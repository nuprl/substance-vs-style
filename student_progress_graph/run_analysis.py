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
from typing import *
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

def is_known_exception(e: Edge, problem: str, key: str) -> Union[bool, ValueError]:
    """
    Check if this edge/problem is a known exception
    """
    exception_keys = ["cycles","breakout","success","fail","neutral"]
    if key not in exception_keys:
        raise ValueError(f"Received key {key}, expected one of known keys: {exception_keys}")
    try:
        reason = KNOWN_EXCEPTIONS[problem][key][e.username][e.attempt_id]
        return True
    except KeyError:
        return False

def compute_next_clues(
    clues: Union[List[int],None], 
    edits: Union[List[str],None],
) -> Union[ContinuityError, List[int]]:
    """
    Given a set of clues, compute the next set by applying the edits.
    Raises continuity error if the edits cannot be applied
    """
    if clues is None:
        clues = []
    if edits is None:
        raise ContinuityError("No clues found on edge. Please compute clues first.")
        
    prev_clues = set(clues)
    for c in edits:
        if c == 0: #no change
            continue
        elif c[0] == "d": #delete
            # if int(c[1]) in prev_clues:
            try:
                prev_clues.remove(int(c[1]))
            except KeyError:
                raise ContinuityError("Remove error")
        elif c[0] == "a": #add
            if int(c[1]) not in prev_clues:
                prev_clues.add(int(c[1]))
            else:
                raise ContinuityError("Add error")
        elif c[0] == "l" or c[0] == "m":
            # check continuity errors
            if int(c[1]) not in prev_clues:
                raise ContinuityError("Modifier error")
    return list(prev_clues)

def _edge_to_dict(e: Edge, verbose: bool) -> dict:
    """
    Wrapper for concise representation of edge
    """
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

def check_clues(graph: Graph, verbose:bool=True) -> Union[ValueError,bool]:
    """
    Checks that only successful edges end with success clues,
    otherwise raises ValueError.
    """
    for e in graph.edges:
        e_dict = json.dumps({**_edge_to_dict(e, verbose), "problem_clues": graph.problem_clues}, indent=4)
        if is_known_exception(e, graph.problem, key=e.state):
            continue
        elif e.state == "success" and e.clues != SUCCESS_CLUES[graph.problem]:
            raise ValueError(f"False success: {e_dict}")
        elif e.state == "fail" and e.clues == SUCCESS_CLUES[graph.problem]:
            raise ValueError(f"False fail: {e_dict}")
        elif e.state == "neutral" and e.clues == SUCCESS_CLUES[graph.problem]:
            raise ValueError(f"False neutral, should be success: {e_dict}")
    return True

def check_cycles(graph: Graph) -> Union[ValueError,Dict[str, List[Edge]]]:
    """
    For each student subgraph, check that cycle/loops either have
    incomplete clues or trivial edits, or is a known exception.
    If check fails, raises a value error.
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
                if is_known_exception(e, graph.problem, key="cycles"):
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
        prev_clues = student_clues_tracker[e.username][-1][-1]
        try:
            
            next_clues = compute_next_clues(prev_clues, e._edge_tags)
            student_clues_tracker[e.username].append((e.attempt_id, next_clues))
            graph.edges[i].add_clues(next_clues)
            
        except ContinuityError as err:
            print(f"#### CONTINUITY ERROR: {err} #####")
            # print(_edge_to_dict(e, False))
            e_dict = {k:v for k,v in _edge_to_dict(e, False).items() if k in [
                "node_from", "node_to", "username","attempt_id"
            ]}
            print(f"problem: {graph.problem}")
            print(f"edge: {e_dict}")
            print(f"failed to apply edit: {e._edge_tags} on previous clues {prev_clues}\n")
            # raise ContinuityError(err)
            FOUND_ERRORS_STUDENTS.append(e.username)
            continue
    
    if len(FOUND_ERRORS_STUDENTS) > 0:
        print(f"Problem clues: {json.dumps(graph.problem_clues, indent=4)}")
        raise ContinuityError(f"Found continuity errors in students:\n{set(FOUND_ERRORS_STUDENTS)}")
    
    graph.student_clues_tracker = student_clues_tracker
    return graph

def load_problem_clues(filepath:str, problem:str) -> Dict[int, str]:
    """
    From a problem_clues.yaml filepath, load all the clues available
    for tags for problem.
    Returns a dict of {clue_id : clue_description}
    """
    with open(filepath, "r") as fp:
        problem_clues = yaml.safe_load(fp)[problem]["tags"]
    problem_clues_dict = {}
    for tag in problem_clues:
        k,v = list(tag.items())[0]
        problem_clues_dict[k] = v
    return problem_clues_dict

def load_problem_answers(filepath, problem) -> List[str]:
    """
    From a problem_clues.yaml filepath, load all the tests available
    for a problem. Return as a list of strings.
    """
    with open(filepath, "r") as fp:
        problem_answers = []
        for item in yaml.safe_load(fp)[problem]["tests"]:
            if "output" in item.keys():
                problem_answers.append(str(yaml.safe_load(item["output"])))
    return problem_answers

def get_breakout_edge(cycle_edges: List[Edge]) -> Union[None, Edge]:
    """
    Given a list of edges gathered from a cycle with
    nx.simple_cycle, determine if the final edge is a "breakout_edge"
    i.e. the edge that breaks out of the cycle.
    If a breakout edge exists, return the Edge, otherwise return None.
    """
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

def df_cycle_summary(
    cycle_edges: Dict[str, List[Edge]], 
    graph: Graph
) -> pd.DataFrame:
    """
    Turns cycles into a dataframe with columns
    student, cycle_length, is_success
    """
    successful_students = graph.get_successful_students()
    results = []
    for username,edge_list in cycle_edges.items():
        results.append(
            {"student": username,
             "cycle_length": len(edge_list),
             "is_success": username in successful_students}
        )
    df = pd.DataFrame(results)
    return df

def check_breakout_edges(
    breakout_edges: Dict[str, List[Edge]],
    problem: str
) -> Union[ValueError, None]:
    """
    Given a dict of student usernames to breakout edges.
    checks that clues corresponding to breakout edges are non-trivial--
    a student breaks out of a loop only by adding new clues.
    Raises a ValueError if this is not the case.
    """
    for student,bedge in breakout_edges.items():
        if bedge != None:
            added_clues = [str(i)[0] for i in bedge._edge_tags]
            if not ("a" in added_clues or "d" in added_clues) and \
                not is_known_exception(bedge, problem, key="breakout"):
                raise ValueError(f"Breakout edge is trivial: {student}, {_edge_to_dict(bedge, False)}")

def compute_node_clusters(graph: Graph)-> dict:
    """
    For a graph, produce a dict of node ids to
    set of clues associated with the node
    """
    node_to_clues = {}
    for student,clues in graph.get_start_node_states().items():
        start_node = graph.get_start_node_id(student)
        node_to_clues[start_node] = set([tuple(clues)])
        
    for e in graph.edges:
        if e.node_to.id not in node_to_clues.keys():
            node_to_clues[e.node_to.id] = set()
        node_to_clues[e.node_to.id].add(tuple(e.clues))
    
    return {k:list(v) for k,v in node_to_clues.items()}

def get_path_clues(g: Graph) -> dict:
    """
    Given a graph, compute a dict of student usernames
    to student paths, where paths
    are the sorted list of clues the students accumulate with
    each attempt at the problem.
    """
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

def score_nodes_by_tests_passed(g: Graph, problem_answers: List[str], overwrite:bool=True) -> Graph:
    """
    Tags nodes with a score which is (num tests passed = num errors)
    """
    for i,n in enumerate(g.nodes):
        node_id = n.id
        num_correct_print = sum([int(n.stdout[i].rsplit("\n",1)[0] == problem_answers[i])
                                 for i in range(len(problem_answers))])
        num_error = sum([int("error:" in stderr.lower()) for stderr in n.stderr])
        score = num_correct_print - num_error
        g.tag_node(node_id, score, overwrite=overwrite)
    return g

def score_nodes_by_target_dist(
    g: Graph, 
    target_node_id: int, 
    overwrite:bool=True
) -> Union[Graph, ValueError]:
    """
    Tags nodes N with a score which is the length of shortest path from
    node N to target_node_id (usually the success node)
    """
    G = g.to_networkx()
    for n in g.nodes:
        node_id = n.id
        if node_id == target_node_id:
            g.tag_node(node_id, 0, overwrite=overwrite)
        else:
            try:
                shortest_path = nx.shortest_path(G, source=node_id, target=target_node_id)
                shortest_len = len(shortest_path) - 1
            except nx.NetworkXNoPath:
                shortest_len = -1
            g.tag_node(node_id, shortest_len, overwrite=overwrite)
    
    for n in g.nodes:
        if n._node_tags:
            n._node_tags = list(set(n._node_tags))
            
        if not (n._node_tags and len(n._node_tags) == 1):
            raise ValueError("Found node with different shortest path scores. This should not happen.")
    return g

def display_edge_info(graph: Graph):
    """
    For each edge, print some info
    """
    for e in graph.edges:
        # if all([str(t)[0] in ['m','l','0'] for t in e._edge_tags]):
            prev_clue = None
            for attempt_id, clues in  graph.student_clues_tracker[e.username]:
                if attempt_id == (e.attempt_id - 1):
                    prev_clue = clues
                    break
            diff = set(e.clues).difference(prev_clue)
            score_before = e.node_from._node_tags 
            score_after = e.node_to._node_tags 
            if score_after > score_before: #or len(diff) > 0:
                print(f"{e._edge_tags}: {prev_clue} -> {e.clues}= {diff}, {score_before}>{score_after}")

def run_RQ1(graph: Graph, outdir:str):
    os.makedirs(f"{outdir}/RQ1", exist_ok=True)
    ## RQ1: All about Cycles
    
    # check that only successful students reach successful clue set
    check_clues(graph)
    
    # check cycles only have trivial or missing clues
    cycle_summary = check_cycles(graph)
    
    # Print some info about cycles
    print("## Cycle edge info:")
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
            
    # check that breakout edges are significant
    check_breakout_edges(breakout_edges, graph.problem)
    
    # Print some info about success rate with cycles
    print("## Cycle success rate summary:")
    df = df_cycle_summary(cycle_summary, graph)
    print(df)
    
    tot_succ = df[df["is_success"]]
    tot_fail = df[df["is_success"] == False]
    fail_cycle = tot_fail[tot_fail["cycle_length"] > 0]
    succ_cycle = tot_succ[tot_succ["cycle_length"] > 0]
    print(f"Total num fail: {len(tot_fail)}, num has loop: {len(fail_cycle)}, {100 * len(fail_cycle)/len(tot_fail)} %")
    print(f"Total num success: {len(tot_succ)}, num has loop: {len(succ_cycle)}, {100 * len(succ_cycle)/len(tot_succ)} %")
    
    fail_no_cycle = tot_fail[tot_fail["cycle_length"] == 0]
    tot_no_cycle = df[df["cycle_length"] == 0]
    tot_cycle = df[df["cycle_length"] > 0]
    
    # check that students with cycles are more likely to fail
    if len(fail_cycle) > 0:
        # num_fail_no_cycle / tot_no_cycle
        # num_fail_cycle / tot_cycle
        likelihood_fail_no_cycle = len(fail_no_cycle) / len(tot_no_cycle)
        likelihood_fail_cycle = len(fail_cycle) / len(tot_cycle)
        print(f"Likelihood fail with cycle {likelihood_fail_cycle} vs. no cycle {likelihood_fail_no_cycle}")
        assert likelihood_fail_cycle > likelihood_fail_no_cycle, "Found that cycle is not more likely to fail."
    
    # Save analyses for RQ1
    with open(f"{outdir}/RQ1/graph_cycles.yaml","w") as fp:
        yaml.dump({"cycle_summary":cycle_summary, "breakout_edges": breakout_edges}, fp)
    with open(f"{outdir}/RQ1/graph_with_clues.yaml","w") as fp:
        yaml.dump(graph, fp)
    with open(f"{outdir}/RQ1/path_clues.json","w") as fp:
        path_summary = get_path_clues(graph)
        json.dump(path_summary, fp, indent=1)
    # save cycle likelihood data
    df.to_csv(f"{outdir}/RQ1/cycles_and_success_corr.csv")
    # save exceptions
    with open(f"{outdir}/RQ1/exceptions.json", "w") as fp:
        json.dump(KNOWN_EXCEPTIONS[graph.problem], fp, indent=3)
    
def run_RQ2(graph: Graph, outdir:str):
    os.makedirs(f"{outdir}/RQ2", exist_ok=True)
    pass
    
def main(args):
    # load tagged graph and problem info
    os.makedirs(args.outdir, exist_ok=True)
    graph = load_graph(args.graph_yaml)
    assert graph.edges[0]._edge_tags != None, "Must tag graph first!"
    graph.problem_clues = load_problem_clues(args.problem_clues_yaml, graph.problem)
    problem_answers = load_problem_answers(args.problem_clues_yaml, graph.problem)
    
    # augment graph with clue, node info, get success node
    graph = populate_clues(graph)
    graph = score_nodes_by_tests_passed(graph, problem_answers, overwrite=True)
    # graph = score_nodes_by_target_dist(graph, success_node.id, overwrite=True)
    success_node = [n for n in graph.nodes if n._node_tags == len(problem_answers)]
    # check that only one success node exists
    assert len(success_node) == 1, f"Can only be 1 success node: {len(success_node)}"
    success_node = success_node[0]
    print(f"Success node {success_node.id}")
    
    ## RQ1: cycle behavior
    run_RQ1(graph, args.outdir)
    
    ## RQ2: Rewrites
    try:
        display_edge_info(graph)
    except:
        pass
    
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml")
    parser.add_argument("outdir")
    parser.add_argument("problem_clues_yaml")
    args = parser.parse_args()
    main(args)