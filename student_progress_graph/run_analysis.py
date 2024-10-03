from dataclasses import dataclass
import pandas as pd
from re import L
from .graph_utils import load_graph, Graph, Edge, get_student_subgraph
import json
import argparse
import os
import yaml
import glob
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict
import networkx as nx
from .analysis_data import SUCCESS_CLUES, KNOWN_EXCEPTIONS
import itertools as it
from scipy import stats
from collections import Counter
'''
Analyzing common patterns in graphs
1. for each edge, compute clues
2. check all successful edges end with success_clues, fail edges do not end with success_clues
    - if there's exceptions raised, note these down in analysis_data/KNOWN_EXCEPTIONS. 
        These are edge cases we can talk about in paper
3. checks that cycles/loops correspond to missing clues and trivial rewrites
4. correlate length of loop to success
'''
class ContinuityError(Exception):
    pass


def is_known_exception(e: Edge, problem, key=None, verbose=False) -> bool:
    try:
        if key is None:
            key = e.state
        reason = KNOWN_EXCEPTIONS[problem][key][e.username][e.attempt_id]
        if verbose:
            print(f"Known exception {e.username}, attempt {e.attempt_id}:\n\t{reason}")
        return True
    except KeyError:
        return False

def _compute_next_state(prev_state, changes):
    if prev_state is None:
        prev_state = []
    prev_state = set(prev_state)
    for c in changes:
        if c == 0: #no change
            continue
        elif c[0] == "d": #delete
            # if int(c[1]) in prev_state:
            try:
                prev_state.remove(int(c[1]))
            except KeyError:
                raise ContinuityError("Remove error")
        elif c[0] == "a": #add
            if int(c[1]) not in prev_state:
                prev_state.add(int(c[1]))
            else:
                raise ContinuityError("Add error")
        elif c[0] == "l" or c[0] == "m":
            # check continuity errors
            if int(c[1]) not in prev_state:
                raise ContinuityError("Modifier error")
    return list(prev_state)

def _edge_dict(e: Edge, verbose: bool) -> dict:
    dikt = e.to_dict()
    if not verbose:
        for k in dikt.keys():
            if k.startswith("node_"):
                dikt[k] = dikt[k]["id"]
        dikt = {k:v for k,v in dikt.items() if not (
            k.startswith("completion_") or
            k.startswith("prompt_") or
            k == "diff"
        )}
    return dikt

def check_state_clues(graph: Graph, verbose=True) -> bool:
    """
    Checks that only success states end with success clues,
    otherwise prints exception edge
    """
    for e in graph.edges:
        e_dict = json.dumps({**_edge_dict(e, verbose), "problem_clues": graph.problem_clues}, indent=4)
        if is_known_exception(e, graph.problem):
            continue
        elif e.state == "success" and e.clues != SUCCESS_CLUES[graph.problem]:
            raise ValueError(f"False success: {e_dict}")
        elif e.state == "fail" and e.clues == SUCCESS_CLUES[graph.problem]:
            raise ValueError(f"False fail: {e_dict}")
        elif e.state == "neutral" and e.clues == SUCCESS_CLUES[graph.problem]:
            raise ValueError(f"False neutral, should be success: {e_dict}")
    return True

def check_loops(graph: Graph) -> Dict[str, List[Edge]]:
    """
    For each student subgraph, check that cycles either have
    incomplete clues or trivial diffs
    """
    summary = {}
    for student in graph.get_students():
        subgraph = get_student_subgraph(graph, student)
        G = subgraph.to_networkx()
        cycle = list(nx.simple_cycles(G))
        
        # for each edge in cycle, check that edge_tag is 0
        # or clues are missing
        cycle_summary = []
        cycle_nodes = list(it.chain(*cycle))
        for e in subgraph.edges:
            is_self_loop = (e.node_from.id == e.node_to.id)
            if ([e.node_from.id, e.node_to.id] in cycle or 
                (is_self_loop and [e.node_from.id] in cycle)):
                if is_known_exception(e, graph.problem, key="loop"):
                    continue 
                elif not(e._edge_tags == [0] or e.clues != SUCCESS_CLUES[graph.problem]):
                    raise ValueError(f"Found non-trivial edge in loop: {yaml.dump(e)}")
                else:
                    cycle_summary.append(e)
            elif e.node_from.id in cycle_nodes and e.node_to.id not in cycle_nodes:
                cycle_summary.append(e)
        summary[student] = sorted(cycle_summary, key=lambda x: x.attempt_id)
    return summary
        
def populate_clues(graph: Graph) -> Graph:
    """
    Augment graph edges with clue sets
    """
    FOUND_ERRORS_STUDENTS = []
    student_clues_tracker = {student: [(0,start_state)] for student,start_state 
                             in graph.get_start_node_states().items()}
    for i,e in enumerate(graph.edges):
        prev_state = student_clues_tracker[e.username][-1][-1]
        try:
            next_state = _compute_next_state(prev_state, e._edge_tags)
        except ContinuityError as err:
            print(f"#### CONTINUITY ERROR: {err} #####")
            # print(_edge_dict(e, False))
            e_dict = {k:v for k,v in _edge_dict(e, False).items() if k in [
                "node_from", "node_to", "username","attempt_id"
            ]}
            print(f"problem: {graph.problem}")
            print(f"edge: {e_dict}")
            print(f"failed to apply edit: {e._edge_tags} on previous clues {prev_state}\n")
            # raise ContinuityError(err)
            FOUND_ERRORS_STUDENTS.append(e.username)
            continue
        
        student_clues_tracker[e.username].append(
            (e.attempt_id, next_state)
        )
        graph.edges[i].clues = next_state
    
    if len(FOUND_ERRORS_STUDENTS) > 0:
        print(f"Problem clues: {json.dumps(graph.problem_clues, indent=4)}")
        raise ContinuityError(f"Found continuity errors in students:\n{set(FOUND_ERRORS_STUDENTS)}")
    
    graph.student_clues_tracker = student_clues_tracker
    return graph

def load_problem_clues(filepath, problem):
    with open(filepath, "r") as fp:
        problem_clues = yaml.safe_load(fp)[problem]["tags"]
    problem_clues_dict = {}
    for tag in problem_clues:
        k,v = list(tag.items())[0]
        problem_clues_dict[k] = v
    return problem_clues_dict

def load_problem_answers(filepath, problem):
    with open(filepath, "r") as fp:
        problem_answers = []
        for item in yaml.safe_load(fp)[problem]["tests"]:
            if "output" in item.keys():
                problem_answers.append(str(yaml.safe_load(item["output"])))
    return problem_answers

def get_breakout_edge(cycle_edges: List[Edge]):
    if len(cycle_edges) < 2:
        return None
    last_edge = cycle_edges.pop()
    nodes = []
    for e in cycle_edges:
        nodes += [e.node_from.id, e.node_to.id]
    nodes = set(nodes)
    if last_edge.node_to.id in nodes:
        return None
    else:
        return last_edge

def likelihood_fail_given_loop(cycle_summary, graph):
    successful_students = graph.get_successful_students()
    results = []
    for k,edge_list in cycle_summary.items():
        results.append(
            {"student": k,
             "loop_len": len(edge_list),
             "is_success": k in successful_students}
        )
    df = pd.DataFrame(results)
    return df

def check_breakout_edges(breakout_edges, problem):
    """
    Given a dict of student usernames to breakout edges.
    Checks that clues added to breakout are substantial
    """
    for student,bedge in breakout_edges.items():
        if bedge != None:
            added_clues = [str(i)[0] for i in bedge._edge_tags]
            if not ("a" in added_clues or "d" in added_clues) and \
                not is_known_exception(bedge, problem, key="breakout"):
                raise ValueError(f"Breakout edge is trivial: {student}, {_edge_dict(bedge, False)}")

def compute_node_clusters(graph: Graph)-> dict:
    node_to_clues = {}
    for student,clues in graph.get_start_node_states().items():
        start_node = graph.get_start_node_id(student)
        node_to_clues[start_node] = set([tuple(clues)])
        
    for e in graph.edges:
        if e.node_to.id not in node_to_clues.keys():
            node_to_clues[e.node_to.id] = set()
        node_to_clues[e.node_to.id].add(tuple(e.clues))
    
    return {k:list(v) for k,v in node_to_clues.items()}

def get_path_summary(g: Graph) -> dict:
    student_paths = {}
    start_states = g.get_start_node_states()
    for e in g.edges:
        if not e.username in student_paths.keys():
            student_paths[e.username] = [(0,start_states[e.username])]
        student_paths[e.username].append((e.attempt_id, e.clues))
    
    for k,v in student_paths.items():
        path = sorted(v, key=lambda x: x[0])
        student_paths[k] = [i[1] for i in path]
    
    return student_paths

def score_nodes_by_tests_passed(g: Graph, problem_answers) -> Graph:
    for i,n in enumerate(g.nodes):
        node_id = n.id
        num_correct_print = sum([int(n.stdout[i].rsplit("\n",1)[0] == problem_answers[i])
                                 for i in range(len(problem_answers))])
        num_error = sum([int("error:" in stderr.lower()) for stderr in n.stderr])
        score = num_correct_print # - num_error
        g.tag_node(node_id, score)
    return g

def score_nodes_by_target_dist(g: Graph, target_node_id: int) -> Graph:
    """
    NOTE: this is incorrect. Networkx shortest path is not directed
    """
    G = g.to_networkx()
    for n in g.nodes:
        node_id = n.id
        if node_id == target_node_id:
            g.tag_node(node_id, 0)
        else:
            try:
                shortest_path = nx.shortest_path(G, source=node_id, target=target_node_id)
                shortest_len = len(shortest_path) - 1
            except nx.NetworkXNoPath:
                shortest_len = -1
            g.tag_node(node_id, shortest_len)
    
    for n in g.nodes:
        n._node_tags = list(set(n._node_tags))
        assert len(n._node_tags) == 1
    return g

def check_rewrites_impact(graph: Graph):
    """
    For each edge, check if rewrites advance the clues.
    NOTE: does not seem to be a trend
    """
    for e in graph.edges:
        # if all([str(t)[0] in ['m','l','0'] for t in e._edge_tags]):
            prev_clue = None
            for attempt_id, clues in  graph.student_clues_tracker[e.username]:
                if attempt_id == (e.attempt_id - 1):
                    prev_clue = clues
                    break
            diff = set(e.clues).difference(prev_clue)
            score_before = e.node_from._node_tags[0] 
            score_after = e.node_to._node_tags[0] 
            if score_after > score_before: #or len(diff) > 0:
                print(f"{e._edge_tags}: {prev_clue} -> {e.clues}= {diff}, {score_before}>{score_after}")

def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    graph = load_graph(args.graph_yaml)
    graph.problem_clues = load_problem_clues(args.problem_clues_yaml, graph.problem)
    graph = populate_clues(graph)
    problem_answers = load_problem_answers(args.problem_clues_yaml, graph.problem)
    graph = score_nodes_by_tests_passed(graph, problem_answers)
    success_node = [n for n in graph.nodes if n._node_tags[0] == len(problem_answers)]
    # check only one success node
    assert len(success_node) == 1, f"Can only be 1 success node: {len(success_node)}"
    success_node = success_node[0]
    
    # graph.clear_node_tags()
    # graph = score_nodes_by_target_dist(graph, success_node.id)

    ## RQ1: Cycles
    
    # check success clues
    check_state_clues(graph)
    # save graph
    with open(f"{args.outdir}/graph_with_clues.yaml","w") as fp:
        yaml.dump(graph, fp)
    # summary
    with open(f"{args.outdir}/path_summary.json","w") as fp:
        path_summary = get_path_summary(graph)
        json.dump(path_summary, fp, indent=1)
    
    # check cycles have trivial or missing clues
    cycle_summary = check_loops(graph)
    
    breakout_edges = {}
    for student,edges in cycle_summary.items():
        # last edge is breakout edge
        e_list = [[e.node_from.id, e.node_to.id, e.clues, e._edge_tags] 
                  for e in edges]
        print(f"{student}:{e_list}")
        breakout_edge = get_breakout_edge(edges)
        breakout_edges[student] = breakout_edge
        if breakout_edge:
            print(f"breakoutedge {student}")
            
    # save cycle info
    with open(f"{args.outdir}/graph_cycles.yaml","w") as fp:
        yaml.dump({"cycle_summary":cycle_summary, "breakout_edges": breakout_edges}, fp)

    check_breakout_edges(breakout_edges, graph.problem)
    df = likelihood_fail_given_loop(cycle_summary, graph)
    print(df)
    # print(df.corr())
    # corr = stats.pearsonr(df["loop_len"], df["is_success"])
    # print(f"statistic: {corr[0]}, pvalue: {corr[1]}")
    # how many fails have loops, how many success, tot_num
    succ = df[df["is_success"]]
    fail = df[df["is_success"] == False]
    fail_loop = fail[fail["loop_len"] > 0]
    succ_loop = succ[succ["loop_len"] > 0]
    print(f"Num fail: {len(fail)}, num has loop: {len(fail_loop)}, {100 * len(fail_loop)/len(fail)} %")
    print(f"Num success: {len(succ)}, num has loop: {len(succ_loop)}, {100 * len(succ_loop)/len(succ)} %")
    
    if len(fail_loop) > 0:
        ratio_succ_fail = (len(succ_loop)/len(succ)) / (len(fail_loop)/len(fail))
        assert ratio_succ_fail <= 0.54, ratio_succ_fail
        # topScores is highest with 0.5333
    
    # save looping likelihood df
    df.to_csv(f"{args.outdir}/looping_behavior.csv")
    
    # save exceptions
    with open(f"{args.outdir}/exceptions.json", "w") as fp:
        json.dump(KNOWN_EXCEPTIONS[graph.problem], fp, indent=3)
        
    # node_clusters = compute_node_clusters(graph)
    # print(json.dumps(node_clusters))
    
    ## RQ2: Rewrites
    
    print(f"Success node {success_node.id}")
    check_rewrites_impact(graph)
    
    
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml")
    parser.add_argument("outdir")
    parser.add_argument("problem_clues_yaml")
    args = parser.parse_args()
    main(args)