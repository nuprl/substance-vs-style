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
from .analysis_data import OUT_OF_TOKENS_ERROR, IMPLICIT_CLUES

def all_problems_analysis(graph_dir: str, outdir:str, problem_clues_yaml: str):
    graphs = []
    for graph_yaml in glob.glob(f"{graph_dir}/*.yaml"):
        # discard any that we have not verified yet
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if not graph_name in SUCCESS_CLUES.keys():
            print(f"Skipping {graph_name}")
            continue
        graph = load_graph(graph_yaml)
        graph = remove_out_of_token_errors(graph)
        graph.problem_clues = load_problem_clues(problem_clues_yaml, graph.problem)
        graph = populate_clues(graph)
        graphs.append(graph)
    
    print(f"--- Running for problems {[g.problem for g in graphs]}")
    run_RQ2(graphs, args.outdir)

def run_RQ2(graphs: List[Graph], outdir:str):
    os.makedirs(outdir, exist_ok=True)

    """
    1. Success clues

    Method
        - for each graph, we check that successful students have all clues
    Experiment
        - out of all successful edges, how many have all clues?
    Result
        This shows that success depends on substance
    """
    terminal_edge_data = []
    for graph in graphs:
        success_clues = list(SUCCESS_CLUES[graph.problem])
        for e in graph.edges:
            if e.state in ["success","fail"]:
                is_success = e.state == "success"
                if graph.problem in IMPLICIT_CLUES.keys() and \
                    e.username in IMPLICIT_CLUES[graph.problem]:
                    e.clues += IMPLICIT_CLUES[graph.problem][e.username]
                has_all_clues = e.clues == success_clues

                terminal_edge_data.append({
                    "problem": graph.problem,
                    "success_clues": success_clues,
                    "state": e.state,
                    "clues": e.clues,
                    "has_all_clues": has_all_clues,
                    "is_missing_clues": not has_all_clues,
                    "is_success": is_success,
                    "is_fail": not is_success,
                })

    edge_df = pd.DataFrame(terminal_edge_data)
    # print(edge_df)
    succ_edge_df = edge_df[edge_df["state"] == "success"]
    print(f"has_all_clues/ num_succ: {succ_edge_df['has_all_clues'].sum()} / {len(succ_edge_df)} = {succ_edge_df['has_all_clues'].sum()/len(succ_edge_df):.2f}")

    for var_a, var_b in [("is_success","has_all_clues"), ("is_success","is_missing_clues"), ("is_fail","has_all_clues"),
                        ("is_fail", "is_missing_clues")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, edge_df)
        # print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    """
    2. Cycles

    Method
        - for each graph, we check that cycle edges are trivial edits
        or student is missing clues
    Experiment
        - out of all the cyles, how many fit this? [lower bound]
    Result
        Shows loops are due to missing something

    Show that students have a higher likelihood of giving up with cycles

    `P(success | not cycle) vs P(success | cycle)`
    """
    # dataframe [problem, cycle_num_edges, cycle_edits]
    cycles_data = []
    for graph in graphs:
        succ_students = graph.get_successful_students()
        cycle_summary = check_cycles(graph, suppress_check=True)
        for student, cycle_edge_list in cycle_summary.items():
            # check if has breakout edge
            breakout_edge = get_breakout_edge(cycle_edge_list)
            if breakout_edge:
                cycle_edge_list.pop()

            has_only_trivial_edits = all([not is_any_tag_kind(e._edge_tags, ["a","d"]) for e in cycle_edge_list])
            cycle_clues = [e.clues for e in cycle_edge_list]
            has_missing_clues = all([clue != SUCCESS_CLUES[graph.problem] for clue in cycle_clues])
            cycles_data.append({
                "username": student,
                "is_success": (student in succ_students),
                "cycle_num_edges": len(cycle_edge_list),
                "has_cycle": len(cycle_edge_list) > 0,
                "not_has_cycle": len(cycle_edge_list) == 0,
                "cycle_clues": cycle_clues,
                "cycle_edits": [e._edge_tags for e in cycle_edge_list],
                "has_breakout_edge": bool(breakout_edge is not None),
                "not_has_breakout_edge": bool(breakout_edge is None),
                "has_only_trivial_edits": has_only_trivial_edits,
                "has_substantial_edits": not has_only_trivial_edits,
                "has_missing_clues": has_missing_clues,
                "not_has_missing_clues": not has_missing_clues,
            })
    df_cycles = pd.DataFrame(cycles_data)
    print(df_cycles.value_counts("is_success"))

    num_trivial_cycles = df_cycles['has_only_trivial_edits'].sum()
    num_missing_clues_cycles = df_cycles['has_missing_clues'].sum()
    print(f"Num cycles with only trivial edits {num_trivial_cycles} / {len(df_cycles)} = {num_trivial_cycles / len(df_cycles):.2f}")
    print(f"Num cycles with missing clues {num_missing_clues_cycles} / {len(df_cycles)} = {num_missing_clues_cycles / len(df_cycles):.2f}")

    for var_a, var_b in [("is_success","has_cycle"), ("is_success","not_has_cycle"), ("is_success","has_breakout_edge"),
                        ("is_success", "not_has_breakout_edge"), ]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, df_cycles)
        # print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    corr = display_pearsonr_results(df_cycles, [("is_success","cycle_num_edges")])
    print(corr)

    """
    3. Rewrites

    Rewrites do not help model, but help student debug what is wrong with model.

    Plot: how often does a rewrite lead directly to success node?
    `P(success | rewrite)` vs `P(success | no rewrites)`
    Answer: not very often.

    how often is a rewrite followed by a substantial edit? And how often
    is a rewrite+substatial edit lead to success?

    `P(success | rewrite->substatial)`
    """
    path_data = []
    for graph in graphs:
        for student, edge_list in graph.get_student_edges().items():
            last_edge = edge_list[-1]
            path_data.append({
                "student": student,
                "problem": graph.problem,
                "edge_list": edge_list,
                "last_edge": last_edge,
                "has_final_rewrite": is_any_tag_kind(last_edge._edge_tags, ["m","l",0]),
                "is_success": last_edge.state == "success",
                "num_rewrite->subst": num_rewrite_to_subst(edge_list)
            })
    path_df = pd.DataFrame(path_data)
    path_df["not_has_final_rewrite"] =  path_df["has_final_rewrite"].apply(lambda x: not x)

    num_last_edge_is_rewrite = path_df["has_final_rewrite"].sum()
    print(f"P(is_success & has_final_rewrite): {(path_df['is_success']& path_df['has_final_rewrite']).mean():.2f}")
    print(f"has final rewrite {num_last_edge_is_rewrite} / {len(path_df)} = {path_df['has_final_rewrite'].mean():.2f}")
    print(f"not has final rewrite {path_df['not_has_final_rewrite'].sum()} / {len(path_df)} = {path_df['not_has_final_rewrite'].mean():.2f}")

    path_df["rewrite->subst"] = path_df["num_rewrite->subst"].apply(lambda x: x>0)
    path_df["not_rewrite->subst"] = path_df["rewrite->subst"].apply(lambda x: not x)

    for var_a, var_b in [("is_success","rewrite->subst"), ("is_success","not_rewrite->subst")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, path_df)
        print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")

    corr = display_pearsonr_results(path_df, [("is_success","num_rewrite->subst")])
    print(corr)

def num_rewrite_to_subst(edge_list: List[Edge]) -> int:
    count = 0
    for a,b in zip(edge_list, edge_list[1:]):
        if is_any_tag_kind(a._edge_tags, ["l","m",0]) and is_any_tag_kind(b._edge_tags, ["a","d"]) \
            and a.attempt_id == b.attempt_id-1:
            count += 1
    return count


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    logfile = f"{args.outdir}/analysis.log"
    
    with open(logfile, 'w') as log_fp:
        with contextlib.redirect_stdout(log_fp), contextlib.redirect_stderr(log_fp):
            print("# Analyzing all problems that have been reviewed")
            all_problems_analysis(args.graph_dir, args.outdir, args.problem_clues_yaml)
            
    # print logfile at end
    with open(logfile, 'r') as log_fp:
        log_contents = log_fp.read()
        print(log_contents)
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_dir")
    parser.add_argument("outdir")
    parser.add_argument("problem_clues_yaml")
    parser.add_argument("--suppress-asserts","-q", action="store_true")
    args = parser.parse_args()
    SUPPRESS_ASSERTS = args.suppress_asserts
    main(args)