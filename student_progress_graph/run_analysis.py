from collections import defaultdict
import glob
import re
import pandas as pd
from re import L
import json
import argparse
import os
import yaml
import glob
import pandas as pd
import networkx as nx
from .analysis_utils import *
from scipy import stats
from pathlib import Path
from typing import List, Dict, Union, Any, Tuple
import yaml
import contextlib
from .analysis_data import IGNORE_SUCCESS, OUT_OF_TOKENS_ERROR
'''
Analyzing common patterns in graphs

NOTE:

- is IGNORE_SUCCESS necessary in computing likelihood of fail given cycle?
- do we need to exclude exceptional problems from all_problems analysis (model
    misinterprets good prompts for problem specific reasons)
'''
global SUPPRESS_ASSERTS

def clean_graph(graph: Graph, problem_answers: List[str]) -> Graph:
    """
    Trims graph for extra edges after initial success.
    Removes observed cases where student fails but is marked as success due to
    test coverage being low.
    Removes students with out of token errors.
    """
    graph = trim_graph(graph, problem_answers)
    students_to_remove = IGNORE_SUCCESS.get(graph.problem,[]) + \
                        OUT_OF_TOKENS_ERROR.get(graph.problem, [])
    if len(students_to_remove) > 0:
        graph = remove_students(graph, students_to_remove)
        print("Removed students:", students_to_remove)
    return graph

def display_edge_info(graph: Graph):
    """
    For each edge, print some info
    """
    for e in graph.edges:
        # if all([str(t)[0] in ['m','l','0'] for t in e._edge_tags]):
            prev_clue = None
            for item in  graph.student_clues_tracker[e.username]:
                attempt_id, clues = item["attempt_id"], item["clues"]
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
    check_breakout_edges(breakout_edges, graph)
    
    # Print some info about success rate with cycles
    print("## Cycle success rate summary:")
    df = df_cycle_summary(cycle_summary, graph)
    
    def _check_success(item):
        if graph.problem in IGNORE_SUCCESS.keys() and \
            item["student"] in IGNORE_SUCCESS[graph.problem]:
                return False
        else:
            return item["is_success"]
        
    df["is_success"] = df.apply(_check_success,axis=1)
    df["is_failure"] = df.apply(lambda x: not x["is_success"], axis=1)
    print(df)
    
    tot_succ = df[df["is_success"]]
    tot_fail = df[df["is_success"] == False]
    fail_cycle = tot_fail[tot_fail["cycle_length"] > 0]
    succ_cycle = tot_succ[tot_succ["cycle_length"] > 0]

    if len(tot_succ) > 0:
        succ_rate = 100 * len(succ_cycle)/len(tot_succ)
    else:
        succ_rate = 0

    if len(tot_fail) > 0:
        fail_rate = 100 * len(fail_cycle)/len(tot_fail)
    else:
        fail_rate = 0

    print(f"Total num fail: {len(tot_fail)}, num has loop: {len(fail_cycle)}, {fail_rate} %")
    print(f"Total num success: {len(tot_succ)}, num has loop: {len(succ_cycle)}, {succ_rate} %")
    
    
    fail_no_cycle = tot_fail[tot_fail["cycle_length"] == 0]
    tot_no_cycle = df[df["cycle_length"] == 0]
    tot_cycle = df[df["cycle_length"] > 0]

    # Save analyses for RQ1
    with open(f"{outdir}/RQ1/graph_cycles.yaml","w") as fp:
        yaml.dump({"cycle_summary":cycle_summary, "breakout_edges": breakout_edges}, fp)
    with open(f"{outdir}/RQ1/graph_with_clues.yaml","w") as fp:
        yaml.dump(graph, fp)
    with open(f"{outdir}/RQ1/path_clues.json","w") as fp:
        path_summary = get_path_clues(graph)
        json.dump(path_summary, fp, indent=1)
    # save exceptions
    if graph.problem in KNOWN_EXCEPTIONS.keys():
        with open(f"{outdir}/RQ1/exceptions.json", "w") as fp:
            json.dump(KNOWN_EXCEPTIONS[graph.problem], fp, indent=3)
        
    
    if len(fail_cycle) > 0:
        # check that students with cycles are more likely to fail
        
        # num_fail_no_cycle / tot_no_cycle
        # num_fail_cycle / tot_cycle
        likelihood_fail_no_cycle = len(fail_no_cycle) / len(tot_no_cycle)
        likelihood_fail_cycle = len(fail_cycle) / len(tot_cycle)
        likelihood_msg = f"Likelihood fail with cycle {likelihood_fail_cycle} vs. no cycle {likelihood_fail_no_cycle}"
        print(likelihood_msg)
        
        df["has_cycle"] = df.apply(lambda x: int(x["cycle_length"] > 0), axis=1)
        df["not_has_cycle"] = df.apply(lambda x: int(x["cycle_length"] == 0), axis=1)
        print(df)
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob("is_success", "has_cycle", df)
        print(f"P(is_success) | P(has_cycle): {prob_a_given_b}")
        prob_a, prob_b_neg, prob_anb_neg, prob_a_given_b_neg = conditional_prob("is_success", "not_has_cycle", df)
        print(f"P(is_success) | NOT P(has_cycle): {prob_a_given_b_neg}")

        # save cycle likelihood data
        df.to_csv(f"{outdir}/RQ1/cycles_and_success_corr.csv")

        if not SUPPRESS_ASSERTS:
            # assert likelihood_fail_cycle > likelihood_fail_no_cycle, f"Found that cycle is not more likely to fail: {likelihood_msg}."
            assert prob_a_given_b < prob_a_given_b_neg, f"success has cycle {prob_a_given_b}, not has cycle {prob_a_given_b_neg}"
        
    ## other info to display
    try:
        display_edge_info(graph)
    except:
        pass
    
    
def single_problem_analysis(graph_yaml: str, outdir:str):
    # load tagged graph and problem info
    graph = load_graph(graph_yaml)
    graph.problem_clues = load_problem_clues(args.problem_clues_yaml, graph.problem)
    problem_answers = load_problem_answers(args.problem_clues_yaml, graph.problem)
    graph = clean_graph(graph, problem_answers)
    
    assert all([e._edge_tags != None for e in graph.edges]), "Must tag graph first!"
    assert graph.problem in SUCCESS_CLUES.keys(),\
        "Please add the successful clues for this problem in SUCCESS_CLUES"
    
    # augment graph with clue, node info, get success node
    graph = populate_clues(graph)
    graph = score_nodes_by_tests_passed(graph, problem_answers, overwrite=True)
    # graph = score_nodes_by_target_dist(graph, success_node.id, overwrite=True)
    success_node = [n for n in graph.nodes if n._node_tags == len(problem_answers)]
    # check that only one success node exists
    assert len(success_node) == 1, f"Can only be 1 success node: {[success_node, problem_answers]}"
    success_node = success_node[0]
    print(f"Success node {success_node.id}")
    
    ## RQ1: cycle behavior
    run_RQ1(graph, outdir)
    

def display_pearsonr_results(df: pd.DataFrame, var_tuples: List[Tuple[str]]) -> str:
    results = ""
    for var_a, var_b in var_tuples:
        corr, pval = stats.pearsonr(df[var_a], df[var_b])
        res = f"{var_a}-{var_b}: pearsonr {corr}, pvalue {pval}"
        results += "\n" + res
    return results
        
def all_problems_analysis(graph_dir: str, outdir:str):
    graphs = []
    prob_to_graph = {}
    for graph_yaml in glob.glob(f"{graph_dir}/*.yaml"):
        # discard any that we have not verified yet
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if not graph_name in SUCCESS_CLUES.keys():
            continue
        graph = load_graph(graph_yaml)
        problem_answers = load_problem_answers(args.problem_clues_yaml, graph.problem)
        graph = clean_graph(graph, problem_answers)
        graph = populate_clues(graph)
        prob_to_graph[graph.problem] = graph
        graphs.append(graph)
    
    print(f"--- Running for problems {[g.problem for g in graphs]}")
    ## correlate length of path with success
    path_data = []
    
    for graph in graphs:
        student_paths = get_path_clues(graph)
        student_success = graph.get_successful_students()
        
        for name,path in student_paths.items():
            student_start_clues = graph.get_start_node_states()[name]
            path_data.append({
                "problem": graph.problem,
                "username": name,
                "path": path,
                "path_len": len(path),
                "is_success": bool(name in student_success),
                "start_clues": student_start_clues,
                "start_clues_len": len(student_start_clues),
                "total_clues": len(SUCCESS_CLUES[graph.problem])
            })

    print("## Correlation results:")
    
    path_df = pd.DataFrame(path_data)
    print(path_df.corr())
    
    variables = [("path_len", "is_success"), ("start_clues_len","is_success"),
                         ("path_len","start_clues_len")]
    print(display_pearsonr_results(path_df, variables))
        
    # What makes students that start with few clues, successful in the end?
    # versus students that start with many clues, but engage in re-writes
    """
    1. classify for "few start clues" and "lots of start clues" based on
        a threshhold
    2. see how many succeed out of the classes
    """
    print("## Correlation of number of start clues and success")
    THRESHHOLD = 0.4
    print(f"Threshhold for defining 'few' num clues: {THRESHHOLD}")
    path_df["has_few_start_clues"] = path_df["start_clues_len"] / path_df["total_clues"]
    path_df["has_few_start_clues"] = path_df["has_few_start_clues"].apply(lambda x: x <= THRESHHOLD)
    print(path_df.value_counts(["has_few_start_clues"]))
    print(path_df.value_counts(["has_few_start_clues", "is_success"]))
    
    """
    Prelim results:
    - majority of students start with many clues (78%)
    - of those that start with many clues, probability of success is pretty even 50%
    - of those that start with few clues, only a few recah success (20%)
    RQ:
        - why do students with many clues still fail?
        - how do students with few clues succeed?
    """
    path_df = path_df.sort_values(["has_few_start_clues", "is_success"]).reset_index()
    path_df.to_csv(f"{outdir}/path_data.csv")
    
    print("## Rewriting habits")
    # rewriting is how students debug, but not often helps
    # how often does final rewrite lead to success?
    problem_edit_history = {}
    modifier_success_count = 0
    for graph in graphs:
        student_to_edit_history = defaultdict(list)
        for e in graph.edges:
            student_to_edit_history[e.username].append(e._edge_tags)
            if e.state == "success" and is_tag_kind(e._edge_tags, ["l","m","0"]):
                modifier_success_count += 1
        problem_edit_history[graph.problem] = student_to_edit_history
        
    print(f"{modifier_success_count} / {len(path_df)} = {modifier_success_count / len(path_df)}")
    
    # useful for students to debug, not so much for model
    # check how often after after a rewrite a substantial tag occurs
    rewrite_data = []
    for problem,student_edits in problem_edit_history.items():
        succ_students = prob_to_graph[problem].get_successful_students()
        
        for student, edits in student_edits.items():
            count_follows_subst = 0
            count_modifiers = 0
            for (e1, e2) in zip(edits, edits[1:]):
                if is_tag_kind(e1, ["l","m","0"]):
                    count_modifiers += 1
                    if is_tag_kind(e2, ["a"]):
                        count_follows_subst += 1

            final_clue = prob_to_graph[problem].student_clues_tracker[student][-1]["clues"]
            rewrite_data.append({"student":student,
                                 "problem":problem,
                                "edits": edits,
                                "has_all_clues": len(final_clue) == len(SUCCESS_CLUES[problem]),
                                "edits_len": len(edits),
                                "has_modifiers": count_modifiers>0,
                                "no_modifiers": count_modifiers == 0,
                                "count_modifiers": count_modifiers,
                                "has_follows_subst": count_follows_subst > 0,
                                "not_has_follows_subst": count_follows_subst == 0,
                                "count_follows_subst": count_follows_subst,
                                "is_success": student in succ_students})
    
    
    rewrite_df = pd.DataFrame(rewrite_data)
    rewrite_df["frequency_follows_subst"] = rewrite_df["count_follows_subst"] / rewrite_df["count_modifiers"]
    print(display_pearsonr_results(rewrite_df, [("has_modifiers","is_success")]))
    
    # how often has_follow_subst + is_success
    """
    probability of A|B
    A: is_success
    B: has_follows_subst
    
    P(A|B) = P(AnB)/P(B)
    
    Keep in mind this will not be high because we still need 
    all the clues
    
    NOTE: P(A|B) will be higher if we compute SUCCESS over all students?
    think maybe its the same.
    """
    for var_a, var_b in [("is_success","has_modifiers"), ("is_success","has_follows_subst"),
                         ("is_success","no_modifiers"), ("is_success","not_has_follows_subst"),
                         ("is_success","has_all_clues")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, rewrite_df)
        print(f"Probability {var_a} given {var_b}: var_a {prob_a:.2f} var_b {prob_b:.2f} \
                a_given_b: {prob_a_given_b:.2f}")

    # correlation over filtered df
    rewrite_df = rewrite_df[rewrite_df["has_modifiers"]]
    assert not rewrite_df.isna().any().any()
    print(rewrite_df)
    
    print(rewrite_df[["frequency_follows_subst","is_success"]].corr())
    variables = [("frequency_follows_subst","is_success"), ("count_modifiers","is_success")]
    print(display_pearsonr_results(rewrite_df, variables))
    rewrite_df.to_csv("rewrites_data.csv")     
    
def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    logfile = f"{args.outdir}/analysis.log"
    
    with open(logfile, 'w') as log_fp:
        with contextlib.redirect_stdout(log_fp), contextlib.redirect_stderr(log_fp):
            if os.path.isdir(Path(args.graph_yaml_or_dir)):
                print("# Analyzing all problems that have been reviewed")
                all_problems_analysis(args.graph_yaml_or_dir, args.outdir)
            else:
                print(f"# Analyzing single problem {os.path.basename(args.graph_yaml_or_dir)}")
                single_problem_analysis(args.graph_yaml_or_dir, args.outdir)
    
    # print logfile at end
    with open(logfile, 'r') as log_fp:
        log_contents = log_fp.read()
        print(log_contents)
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml_or_dir")
    parser.add_argument("outdir")
    parser.add_argument("problem_clues_yaml")
    parser.add_argument("--suppress-asserts","-q", action="store_true")
    args = parser.parse_args()
    SUPPRESS_ASSERTS = args.suppress_asserts
    main(args)