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
from .analysis_data import IGNORE_SUCCESS, OUT_OF_TOKENS_ERROR, IGNORE_FAIL

def display_pearsonr_results(df: pd.DataFrame, var_tuples: List[Tuple[str]]) -> str:
    results = ""
    for var_a, var_b in var_tuples:
        corr, pval = stats.pearsonr(df[var_a], df[var_b])
        res = f"{var_a}-{var_b}: pearsonr {corr:.3f}, pvalue {pval:.3f}"
        results += "\n" + res
    return results

def all_problems_analysis(graph_dir: str, outdir:str, problem_clues_yaml: str):
    graphs = []
    prob_to_graph = {}
    for graph_yaml in glob.glob(f"{graph_dir}/*.yaml"):
        # discard any that we have not verified yet
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if not graph_name in SUCCESS_CLUES.keys():
            print(f"Skipping {graph_name}")
            continue
        graph = load_graph(graph_yaml)
        # recompute state on edges
        graph.problem_clues = load_problem_clues(problem_clues_yaml, graph.problem)
        problem_answers = load_problem_answers(problem_clues_yaml, graph.problem)
        graph = populate_clues(graph)
        prob_to_graph[graph.problem] = graph
        graphs.append(graph)
    
    print(f"--- Running for problems {[g.problem for g in graphs]}")
    
    # run_RQ2(graphs, f"{outdir}/RQ2", prob_to_graph) 

    run_RQ3(graphs, f"{outdir}/RQ3", prob_to_graph)

def run_RQ3(graphs: List[Graph], outdir:str, prob_to_graph: dict[str, Graph]):
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
    final_edge_data = []
    for graph in graphs:
        for e in graph.edges:
            if e.state in ["success","fail"]:
                final_edge_data.append({
                    "problem": graph.problem,
                    "success_clues": list(SUCCESS_CLUES[graph.problem]),
                    "state": e.state,
                    "clues": e.clues,
                    "is_success": e.state == "success",
                    "is_fail": e.state == "fail",
                })

    edge_df = pd.DataFrame(final_edge_data)
    edge_df["has_all_clues"] = edge_df["success_clues"] == edge_df["clues"]
    edge_df["not_has_all_clues"] = edge_df["success_clues"] != edge_df["clues"]
    print(edge_df)
    succ_edge_df = edge_df[edge_df["state"] == "success"]
    print(f"Has all clues {succ_edge_df['has_all_clues'].sum()} / {len(succ_edge_df)} = {succ_edge_df['has_all_clues'].sum()/len(succ_edge_df):.2f}")

    for var_a, var_b in [("is_success","has_all_clues"), ("is_success","not_has_all_clues"), ("is_fail","has_all_clues"),
                        ("is_fail", "not_has_all_clues")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, edge_df)
        print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")

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

            cycles_data.append({
                "username": student,
                "is_success": (student in succ_students),
                "cycle_num_edges": len(cycle_edge_list),
                "has_cycle": len(cycle_edge_list) > 0,
                "not_has_cycle": len(cycle_edge_list) == 0,
                "cycle_clues": [e.clues for e in cycle_edge_list],
                "cycle_edits": [e._edge_tags for e in cycle_edge_list],
                "has_breakout_edge": bool(breakout_edge is not None),
            })
    df_cycles = pd.DataFrame(cycles_data)
    print(df_cycles.value_counts("is_success"))
    df_cycles["has_only_trivial_edits"] = df_cycles["cycle_edits"].apply(lambda x: all([is_tag_kind(edit, [0,"m","l"]) for edit in x]))
    df_cycles["has_substantial_edits"] = df_cycles["has_only_trivial_edits"].apply(lambda x: not x)
    df_cycles["has_missing_clues"] = df_cycles["cycle_clues"].apply(lambda x: all([clue != SUCCESS_CLUES[graph.problem] for clue in x]))
    df_cycles["not_has_missing_clues"] = df_cycles["has_missing_clues"].apply(lambda x: not x)
    df_cycles["not_has_breakout_edge"] = df_cycles["has_breakout_edge"].apply(lambda x: not x)
    print(df_cycles)

    num_trivial_cycles = df_cycles['has_only_trivial_edits'].sum()
    num_missing_clues_cycles = df_cycles['has_missing_clues'].sum()
    print(f"Num cycles with only trivial edits {num_trivial_cycles} / {len(df_cycles)} = {num_trivial_cycles / len(df_cycles):.2f}")
    print(f"Num cycles with missing clues {num_missing_clues_cycles} / {len(df_cycles)} = {num_missing_clues_cycles / len(df_cycles):.2f}")

    for var_a, var_b in [("is_success","has_cycle"), ("is_success","not_has_cycle"), ("is_success","has_breakout_edge"),
                        ("is_success", "not_has_breakout_edge"), ]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, df_cycles)
        print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")

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
                "has_final_rewrite": is_tag_kind(last_edge._edge_tags, ["m","l",0]),
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
        if is_tag_kind(a._edge_tags, ["l","m",0]) and is_tag_kind(b._edge_tags, ["a","d"]) \
            and a.attempt_id == b.attempt_id-1:
            count += 1
    return count


def run_RQ2(graphs: List[Graph], outdir:str, prob_to_graph: dict[str, Graph]):
    os.makedirs(outdir, exist_ok=True)
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