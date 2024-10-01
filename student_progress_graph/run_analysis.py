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
'''
Analyzing common patterns in graphs
1. for each edge, compute clues
2. check all successful edges end with success_clues, fail edges do not end with success_clues
    - if there's exceptions raised, note these down in analysis_data/KNOWN_EXCEPTIONS. 
        These are edge cases we can talk about in paper
3. checks that cycles/loops correspond to missing clues and trivial rewrites
4. correlate length of loop to success
5. find the "breakout edge" if student broke out of cycle
'''

def is_known_exception(e: Edge, problem, verbose=False) -> bool:
    try:
        reason = KNOWN_EXCEPTIONS[problem][e.state][e.username][str(e.attempt_id)]
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
            prev_state.remove(int(c[1]))
        elif c[0] == "a": #add
            prev_state.add(int(c[1]))
    return list(prev_state)

def check_state_clues(graph: Graph) -> bool:
    """
    Checks that only success states end with success clues,
    otherwise prints exception edge
    """
    for e in graph.edges:
        e_dict = json.dumps({**e.to_dict(), "problem_clues": graph.problem_clues}, indent=4)
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
                if is_known_exception(e, graph.problem):
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
    student_clues_tracker = {student: [start_state] for student,start_state 
                             in graph.get_start_node_states().items()}
    for i,e in enumerate(graph.edges):
        prev_state = student_clues_tracker[e.username][-1]
        next_state = _compute_next_state(prev_state, e._edge_tags)
        student_clues_tracker[e.username].append(
            next_state
        )
        graph.edges[i].clues = next_state
    
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

def display_breakout_edge(cycle_edges: List[Edge]):
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
        return yaml.dump({k:getattr(last_edge, k) for k in ["attempt_id", "diff"]})

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

def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    graph = load_graph(args.graph_yaml)
    graph.problem_clues = load_problem_clues(args.problem_clues_yaml, graph.problem)
    graph = populate_clues(graph)
    check_state_clues(graph)
    cycle_summary = check_loops(graph)
    for k,edges in cycle_summary.items():
        # last edge is breakout edge
        e_list = [[e.node_from.id, e.node_to.id, e.clues, e._edge_tags] 
                  for e in edges]
        print(f"{k}:{e_list}")
        breakout_edge = display_breakout_edge(edges)
        if breakout_edge:
            print(f"breakoutedge {k}")
            
    df = likelihood_fail_given_loop(cycle_summary, graph)
    print(df)
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml")
    parser.add_argument("outdir")
    parser.add_argument("problem_clues_yaml")
    args = parser.parse_args()
    main(args)