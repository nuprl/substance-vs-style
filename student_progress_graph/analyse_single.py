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
from .analysis_data import OUT_OF_TOKENS_ERROR
'''
Analyzing common patterns in graphs
'''
global SUPPRESS_ASSERTS

def run_RQ1(graph: Graph, outdir:str):
    os.makedirs(f"{outdir}/RQ1", exist_ok=True)
    
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

    # Print some info about success rate with cycles
    print("## Cycle success rate summary:")
    df = df_cycle_summary(cycle_summary, graph)
    
    def _check_success(item):
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

    print(f"Total num fail: {len(tot_fail)}, num fail has loop: {len(fail_cycle)}, {fail_rate} %")
    print(f"Total num success: {len(tot_succ)}, num succ has loop: {len(succ_cycle)}, {succ_rate} %")
    
    fail_no_cycle = tot_fail[tot_fail["cycle_length"] == 0]
    tot_no_cycle = df[df["cycle_length"] == 0]
    tot_cycle = df[df["cycle_length"] > 0]
        
    
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
            assert likelihood_fail_cycle > likelihood_fail_no_cycle, f"Found that cycle is not more likely to fail: {likelihood_msg}."
            assert prob_a_given_b < prob_a_given_b_neg, f"success has cycle {prob_a_given_b}, not has cycle {prob_a_given_b_neg}"

    
    
def single_problem_analysis(graph_yaml: str, outdir:str, problem_clues_yaml:str):
    # load tagged graph and problem info
    graph = load_graph(graph_yaml)
    graph.problem_clues = load_problem_clues(problem_clues_yaml, graph.problem)
    problem_answers = load_problem_answers(problem_clues_yaml, graph.problem)
    graph = remove_out_of_token_errors(graph)
    
    assert all([e._edge_tags != None for e in graph.edges]), "Must tag graph first!"
    assert graph.problem in SUCCESS_CLUES.keys(),\
        "Please add the successful clues for this problem in SUCCESS_CLUES"
    
    # augment graph with clue, node info, get success node
    graph = populate_clues(graph)
        # graph = score_nodes_by_tests_passed(graph, problem_answers, overwrite=True)
        # graph = score_nodes_by_target_dist(graph, success_node.id, overwrite=True)
    success_node = SUCCESS_NODE_IDS[graph.problem]
    print(f"Success node {success_node.id}")
    
    ## RQ1: cycle behavior
    run_RQ1(graph, outdir)


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    logfile = f"{args.outdir}/analysis.log"
    
    with open(logfile, 'w') as log_fp:
        with contextlib.redirect_stdout(log_fp), contextlib.redirect_stderr(log_fp):
            print(f"# Analyzing single problem {os.path.basename(args.graph_yaml)}")
            single_problem_analysis(args.graph_yaml, args.outdir, args.problem_clues_yaml)
    
    # print logfile at end
    with open(logfile, 'r') as log_fp:
        log_contents = log_fp.read()
        print(log_contents)
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml")
    parser.add_argument("outdir")
    parser.add_argument("problem_clues_yaml")
    parser.add_argument("--suppress-asserts","-q", action="store_true")
    args = parser.parse_args()
    SUPPRESS_ASSERTS = args.suppress_asserts
    main(args)