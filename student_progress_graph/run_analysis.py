import pandas as pd
from re import L
from .graph_utils import load_graph, Graph
import json
import argparse
import os
import yaml
import glob
'''
Analyzing common patterns in graphs
Hypotheses:
0. self loops are trivial edits
1. edges between two nodes are the same diffs
2. a diff either adds a clue, deletes a clue, does nothing (trivial rephrase) or does both
3.  a cycle forms when the student does not add a necessary clue or deketes one in favor of another clue,
but both are needed
4. a long path indicates trivial rewrites and/or missing clues
5. the most efficient paths progressively add clues
6. adding clues at the start or end of a prompt is significant
'''
def inspect_multi_edges(graph:Graph)->dict:
    """
    Write diffs into a format easy to analyse
    """
    edge_to_diffs = {}
    for edge in graph.edges:
        key = f"({edge.node_from.id}, {edge.node_to.id})"
        if not key in edge_to_diffs.keys():
            edge_to_diffs[key] = [edge.diff.replace(" \n", "\n")]
        else:
            edge_to_diffs[key].append(edge.diff.replace(" \n", "\n"))
    return {k:v for k,v in edge_to_diffs.items() if len(v) > 1}

def _compute_next_state(prev_state, changes):
    if prev_state is None:
        prev_state = []
    prev_state = set(prev_state)
    for c in changes:
        if c == 0: #no change
            continue
        elif c[0] == "d": #delete
            # if int(c[1]) in prev_state:
            prev_state.remove(int(c[1]))
        elif c[0] == "a": #add
            prev_state.add(int(c[1]))
    return list(prev_state)

def progress_summary(graph: Graph)->dict:
    """
    Will produce following summary:
    student1:
        [
            {
                "attempt_id":0,
                "node_id_from-node_id_to":_,
                "clues":_,
                "state":_,
            },
            ...
            {
                "attempt_id":n,
                "node_id_from-node_id_to":_,
                "clues":_,
                "state":_,
            },
        ]
    """
    student_to_attempt_tags = {}
    for e in graph.edges:
        if e.attempt_id == 1:
            student_to_attempt_tags[e.username] = [{
                "attempt_id": 0,
                "node_id_from-node_id_to": (None, e.node_from.id),
                "clues": graph.get_start_node_states()[e.username],
                "_edge_tag": None,
                "state": "start"
            }]
        student_to_attempt_tags[e.username].append({
                "attempt_id": e.attempt_id,
                "node_id_from-node_id_to": (e.node_from.id, e.node_to.id),
                "clues": None,
                "_edge_tag": e._edge_tags,
                "state": e.state
            })
        
    # compute intermediate node sets
    for student, attempts in student_to_attempt_tags.items():
        sorted_attempts = sorted(attempts, key=lambda x: x["attempt_id"])
        clues_tracker = []
        for attempt in sorted_attempts:
            if attempt["attempt_id"] == 0:
                clues_tracker.append(attempt)
            else:
                prev_state = clues_tracker[-1]["clues"]
                changes = attempt["_edge_tag"]
                attempt["clues"] = _compute_next_state(prev_state, changes)
                clues_tracker.append(attempt)
        student_to_attempt_tags[student] = clues_tracker
    return student_to_attempt_tags

def get_clusters(problem_summary):
    """
    For each edge, collect the state reached (diff clusters)
    
    (u,v):
        [
            {
                "_edge_tag": []
                "state": _
            }
        ]
    """
    edge_to_state = {}
    for student,attempts in problem_summary.items():
        for dikt in attempts:
            edge = str(dikt["node_id_from-node_id_to"])
            state = dikt["state"]
            change = str(dikt["_edge_tag"])
            if edge not in edge_to_state.keys():
                edge_to_state[edge] = [{"_edge_tag":change,"state":state}]
            else:
                edge_to_state[edge].append({"_edge_tag":change,"state":state})
    
    return edge_to_state

def get_paths(problem_summary):
    """
    For each student, collect path
    
    student0: [
        {
            "attempt_id":_,
            "curr_node":_,
            "_edge_tag":_,
            "clue_set":_,
            
        }
    ]
    """
    student_to_trace = {}
    for student,attempts in problem_summary.items():
        if student not in student_to_trace.keys():
            student_to_trace[student] = []
        attempts = sorted(attempts, key= lambda x: x["attempt_id"])
        for dikt in attempts:
            student_to_trace[student].append({"attempt_id": dikt["attempt_id"],
                                            "curr_node": dikt["node_id_from-node_id_to"][1],
                                              "_edge_tag": dikt["_edge_tag"], 
                                              "clue_set": dikt["clues"],
                                              "state": dikt["state"]})
    return student_to_trace

def filter_graphs(graphs):
    MIN_NUM_NODES = 5
    MIN_NUM_STUDENTS = 5
    # AVG_PATH_LEN = 3
    filtered = []
    for g in graphs:
        path_lens = {e.username: e.total_attempts for e in g.edges}
        if (len(g.nodes) >= MIN_NUM_NODES and
            len(path_lens.keys()) >= MIN_NUM_STUDENTS
            #and sum(path_lens.values()) / len(path_lens) >= AVG_PATH_LEN
        ):
            filtered.append(g)
    return filtered
    

def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    graphs = []
    assert os.path.exists(args.graph_yaml_dir)
    for graph_yaml in glob.glob(f"{args.graph_yaml_dir}/*.yaml"):
        graph = load_graph(graph_yaml)
        if args.debug_problems and not graph.problem in args.debug_problems:
            continue
        graphs.append(graph)
    
    if args.task == "inspect_multi_edges":
        problem = {}
        for g in graphs:
            problem[g.problem] = inspect_multi_edges(g)
        with open(f"{args.outdir}/inspect_multi_edges.yaml","w") as fp:
            yaml.dump(problem, fp, default_style="|")
    elif args.task == "progress_summary":
        problem = {}
        for g in graphs:
            prob_summary = progress_summary(g)
            clusters = get_clusters(prob_summary)
            paths =get_paths(prob_summary)
            problem[g.problem] = {"student_path":prob_summary, "edge_to_tags": clusters, 
                                  "student_path_condensed": paths}
        with open(f"{args.outdir}/progress_summary.json","w") as fp:
            json.dump(problem, fp, indent=3)
    elif args.task == "filter_graphs":
        graph_subset = filter_graphs(graphs)
        tot_nodes, tot_edges = 0,0
        for g in graph_subset:
            tot_nodes += len(g.get_students())
            tot_edges += len(g.edges)
            print(f"{len(g.nodes)},", f"{len(g.edges)},", g.problem)
        
        print(tot_nodes, tot_edges, len(graph_subset))
    else:
        raise NotImplementedError()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml_dir")
    parser.add_argument("outdir")
    parser.add_argument("task", choices=["all", "inspect_multi_edges", "progress_summary", "filter_graphs"])
    parser.add_argument("--debug-problems", nargs="+", default=None)
    args = parser.parse_args()
    main(args)