from collections import defaultdict
from .student_edge_cases import SUCCESS_CLUES, KNOWN_EXCEPTIONS, OUT_OF_TOKENS_ERROR
from .graph_utils import load_graph, Graph, Edge, get_student_subgraph, Node
import itertools as it
from typing import List, Union, Dict, Tuple
import json
import pandas as pd
import yaml
import networkx as nx
from copy import deepcopy
from scipy import stats

class ContinuityError(Exception):
    pass

def remove_out_of_token_errors(graph: Graph) -> Graph:
    """
    Removes students with out of token errors.
    """
    students_to_remove = OUT_OF_TOKENS_ERROR.get(graph.problem, [])
    if len(students_to_remove) > 0:
        graph = remove_students(graph, students_to_remove)
        print("Removed students:", students_to_remove)
    return graph

def remove_students(graph: Graph, students: List[str]) -> Graph:
    """
    Removes students and associated edges/data
    """
    def try_pop(obj, key):
        if obj:
            obj.pop(key)

    new_graph = deepcopy(graph)
    for student in students:
        try_pop(getattr(new_graph,"student_colors"), student)
        try_pop(getattr(new_graph,"student_start_node_tags"), student)
        try_pop(getattr(new_graph,"student_clues_tracker"), student)
    new_graph.edges = [e for e in new_graph.edges if not e.username in set(students)]
    return new_graph

def trim_graph(graph:Graph, success_node_id: int) -> Graph:
    """
    Sometimes,students are successful before their last attempt, but keep
    playing with the model. Prune these extra interactions
    """
    student_edges = graph.get_student_edges()
    edges_to_delete = []
    edges_to_retag = []
    students_to_delete = []
    for student, sorted_attempts in student_edges.items():
        for i, attempt in enumerate(sorted_attempts):
            if i == 0 and attempt.node_from.id == success_node_id:
                # first attempt was correct, delete student
                students_to_delete.append(student)
                break
            elif attempt.node_to.id == success_node_id:
                # first correct attempt
                edges_to_delete += sorted_attempts[i+1:]
                edges_to_retag.append(attempt)
                break

    graph = remove_students(graph, students_to_delete)
    graph.edges = [e for e in graph.edges if e not in set(edges_to_delete)]
    for i,e in enumerate(graph.edges):
        if e in set(edges_to_retag):
            graph.edges[i].state = "success"
    return graph
    
def is_any_tag_kind(edge_tag: List[Union[str, int]], tag_kinds:List[str]) -> bool:
    """
    Checks if an edge tag is any of the tag kinds
    """
    return any([str(t)[0] in tag_kinds for t in edge_tag])

def is_known_exception(e: Edge, problem: str, key: str) -> Union[bool, ValueError]:
    """
    Check if this edge/problem is a known exception
    """
    exception_keys = ["cycles","breakout","success","fail","neutral", "start_node"]
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
    if clues is None or clues == [0]: #no clues placeholder
        clues = []

    if edits is None:
        raise ContinuityError("No clues found on edge. Please compute clues first.")
        
    prev_clues = set(clues)
    for c in edits:
        if c == 0: #no change
            continue
        elif c[0] == "d": 
            #delete clue
            try:
                prev_clues.remove(int(c[1]))
            except KeyError:
                raise ContinuityError("Remove error")
        elif c[0] == "a": 
            #add clue must not be in previous
            if prev_clues == []:
                prev_clues = set([int(c[1])])
            elif int(c[1]) not in prev_clues:
                prev_clues.add(int(c[1]))
            else:
                raise ContinuityError("Add error")
        elif c[0] == "l" or c[0] == "m":
            # modified clue must be in previous
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

def check_cycles(graph: Graph, suppress_check: bool = False) -> Union[ValueError,Dict[str, List[Edge]]]:
    """
    For each student subgraph, check that cycle/loops either have
    incomplete clues or trivial edits, or is a known exception.
    If check fails, raises a value error. Otherwise returns
    cycle summary that includes breakout edges.
    """
    summary = defaultdict(list)
    for student in graph.get_students():
        subgraph = get_student_subgraph(graph, student)
        G = subgraph.to_networkx()
        student_cycles = list(nx.simple_cycles(G))
        if len(student_cycles) == 0:
            continue
        
        # # for each edge in cycle, check that edge_tag is 0
        # # or clues are missing
        for cycle in student_cycles:
            cycle_summary = []
            if len(cycle) == 1:
                # self-loop: get the edges in it
                for e in sorted(subgraph.edges, key=lambda x: x.attempt_id):
                    if (e.node_from.id == e.node_to.id) and e.node_to.id == cycle[0]:
                        cycle_summary.append(e)
                        if not(e._edge_tags == [0] or e.clues != SUCCESS_CLUES[graph.problem]) \
                            and not suppress_check:
                            raise ValueError(f"Found non-trivial edge in loop: {yaml.dump(e)}")
            else:
                cycle_nodes = list(zip(cycle, cycle[1:])) + [(cycle[-1], cycle[0])]
                for e in sorted(subgraph.edges, key=lambda x: x.attempt_id):
                    if (e.node_from.id, e.node_to.id) in cycle_nodes:
                        cycle_summary.append(e)
                        if not(e._edge_tags == [0] or e.clues != SUCCESS_CLUES[graph.problem]) \
                            and not suppress_check:
                            raise ValueError(f"Found non-trivial edge in loop: {yaml.dump(e)}")

        summary[student].append(cycle_summary)
    summary = {k:v for k,v in summary.items() if v not in [[], [[]]]} # hack
    return summary
        
def populate_clues(graph: Graph) -> Graph:
    """
    Augment graph edges with clue sets
    """
    FOUND_ERRORS_STUDENTS = []
    student_clues_tracker = {student: [{"attempt_id":0,"clues":start_state}] for student,start_state 
                             in graph.get_start_node_states().items()}
    for i,e in enumerate(graph.edges):
        prev_clues = student_clues_tracker[e.username][-1]["clues"]
        try:
            
            next_clues = compute_next_clues(prev_clues, e._edge_tags)
            student_clues_tracker[e.username].append({"attempt_id":e.attempt_id, "clues":next_clues})
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
    
    for username in student_clues_tracker.keys():
        student_clues_tracker[username].sort(key=lambda x: x["attempt_id"])

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

    # fix None
    problem_answers = [s.replace("'None'", "None") for s in problem_answers]
    return problem_answers

def get_breakout_edge(graph:Graph, student:str,cycle_edges: List[Edge]) -> Union[None, Edge]:
    """
    Given a list of edges gathered from a cycle with
    nx.simple_cycle, if a breakout_edge that exists cycle exists, return it.
    Otherwise return None.
    """
    cycle_edges = sorted(cycle_edges, key=lambda x: x.attempt_id)
    cycle_nodes = set()
    for e in cycle_edges:
        cycle_nodes.add(e.node_from.id)
        cycle_nodes.add(e.node_to.id)
    subgraph = get_student_subgraph(graph, student)
    for e in subgraph.edges:
        if e.attempt_id > cycle_edges[-1].attempt_id:
            # edge after cycle
            if e.node_to.id not in cycle_nodes:
                return e
    
    return None

def display_pearsonr_results(df: pd.DataFrame, var_tuples: List[Tuple[str]]) -> str:
    results = ""
    for var_a, var_b in var_tuples:
        corr, pval = stats.pearsonr(df[var_a], df[var_b])
        res = f"{var_a}-{var_b}: pearsonr {corr}, pvalue {pval}"
        results += "\n" + res
    return results

def conditional_prob(var_a: str, var_b: str, df: pd.DataFrame) -> Tuple[float]:
    """
    probability of A|B
    
    P(A|B) = P(AnB)/P(B)
    
    """
    prob_a = df[var_a].mean()
    prob_b = df[var_b].mean()
    prob_anb = (df[var_a] & df[var_b]).mean()
    prob_a_given_b = prob_anb / prob_b
    return prob_a, prob_b, prob_anb, prob_a_given_b