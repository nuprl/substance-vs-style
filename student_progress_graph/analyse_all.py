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
                    "has_final_rewrite": all([str(t)[0] in ["l","m","0"] for t in e._edge_tags]),
                    "has_final_trivial": all([t  == 0 for t in e._edge_tags]),
                    "has_final_l": all([str(t)[0]  == "l" for t in e._edge_tags]),
                    "has_final_m": all([str(t)[0]  == "m" for t in e._edge_tags]),
                    "has_all_clues": has_all_clues,
                    "ratio_clues": (len(e.clues) / len(success_clues)),
                    "has_leq_half_clues": (len(e.clues) / len(success_clues)) <= 0.5,
                    "is_missing_clues": not has_all_clues,
                    "is_success": is_success,
                    "is_fail": not is_success,
                })

    edge_df = pd.DataFrame(terminal_edge_data)
    # print(edge_df)
    succ_edge_df = edge_df[edge_df["state"] == "success"]
    succ_edge_df.to_csv(f"{outdir}/successful_terminal_edges.csv")
    print(f"has_all_clues/ num_succ: {succ_edge_df['has_all_clues'].sum()} / {len(succ_edge_df)} = {succ_edge_df['has_all_clues'].sum()/len(succ_edge_df):.2f}")

    for var_a, var_b in [("is_success","has_all_clues"), ("is_success","is_missing_clues"),
                        #  ("is_missing_clues", "is_success"), ("has_all_clues","is_success"),
                        #  ("is_fail","has_all_clues"),("is_fail", "is_missing_clues"),
                        #  ("has_all_clues","is_fail"),("is_missing_clues","is_fail")
                         ]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, edge_df)
        # print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    print(f"out of has all clues, how many succ:{ (edge_df['has_all_clues'] & edge_df['is_success']).sum() / edge_df['has_all_clues'].sum():.2f}")

    for var in ["has_final_trivial","has_final_rewrite","has_final_l","has_final_m"]:
        has_final_rewrite = succ_edge_df[var]
        print(f"{var} out of succ_edges: {has_final_rewrite.sum()}/{len(succ_edge_df)} = {has_final_rewrite.mean():.2f}")
    
    # P(had_final_m|has_final_rewrite)
    for var_a, var_b in [("has_final_m","has_final_rewrite")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, succ_edge_df)
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.3f}")

    # probability that final rewrite fixes a prompt with little clues
    # out of prompts with little clues, p(is_success | has_final_rewrite)
    little_clues = edge_df[ edge_df["has_leq_half_clues"]]
    for var_a, var_b in [("is_success","has_final_rewrite")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, little_clues)
        print(f"little clues P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

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
            last_edge = get_breakout_edge(cycle_edge_list)
            if last_edge:
                last_edge = cycle_edge_list.pop()

            has_only_rewrite_edits = all([all([str(t)[0] in ["0","m","l"] for t in e._edge_tags]) for e in cycle_edge_list])
            has_only_trivial_edits = all([all([str(t)[0] in ["0"] for t in e._edge_tags]) for e in cycle_edge_list])
            cycle_clues = [e.clues for e in cycle_edge_list]
            has_missing_clues = all([clue != SUCCESS_CLUES[graph.problem] for clue in cycle_clues])
            has_0_breakout_edge = bool(last_edge and any([str(t)[0] in ['0'] for t in last_edge._edge_tags]))
            has_m_breakout_edge = bool(last_edge and all([str(t)[0] in ['m'] for t in last_edge._edge_tags]))
            has_a_breakout_edge = bool(last_edge and any([str(t)[0] in ['a'] for t in last_edge._edge_tags]))
            has_l_breakout_edge = bool(last_edge and any([str(t)[0] in ['l'] for t in last_edge._edge_tags]))
            has_d_breakout_edge = bool(last_edge and any([str(t)[0] in ['d'] for t in last_edge._edge_tags]))
            cycles_data.append({
                "problem": graph.problem,
                "username": student,
                "cycle_list": [(e.node_from.id, e.node_to.id) for e in cycle_edge_list],
                "is_success": (student in succ_students),
                "cycle_num_edges": len(cycle_edge_list),
                "has_cycle": len(cycle_edge_list) > 0,
                "has_long_cycle": len(cycle_edge_list) > 3,
                "has_two_cycle": len(cycle_edge_list) >= 2,
                "not_has_cycle": len(cycle_edge_list) == 0,
                "cycle_clues": cycle_clues,
                "cycle_edits": [e._edge_tags for e in cycle_edge_list],
                "last_edge": bool(last_edge),
                "last_edge_tags": [] if not last_edge else last_edge._edge_tags,
                "has_0_breakout_edge": has_0_breakout_edge,
                "has_m_breakout_edge": has_m_breakout_edge,
                "has_a_breakout_edge": has_a_breakout_edge,
                "has_l_breakout_edge": has_l_breakout_edge,
                "has_d_breakout_edge": has_d_breakout_edge,
                "has_only_trivial_edits": has_only_trivial_edits,
                "has_only_rewrite_edits": has_only_rewrite_edits,
                "has_substantial_edits": not has_only_rewrite_edits,
                "has_missing_clues": has_missing_clues,
                "not_has_missing_clues": not has_missing_clues,
            })
    df_cycles = pd.DataFrame(cycles_data)
    df_cycles.to_csv(f"{outdir}/cycles.csv")
    print(df_cycles.value_counts("is_success"))

    print(f"% has only trivial edits {df_cycles['has_only_trivial_edits'].mean():.2f}, has only rewrite {df_cycles['has_only_rewrite_edits'].mean():.2f}")
    num_trivial_cycles = df_cycles['has_only_trivial_edits'].sum()
    num_missing_clues_cycles = df_cycles['has_missing_clues'].sum()
    # num_has_br_edge = df_cycles["has_breakout_edge"].sum()
    num_has_cycle = df_cycles["has_cycle"].sum()
    # print(f"Num has br: {num_has_br_edge}")
    print(f"Num has cycle: {num_has_cycle}")
    print(f"Num cycles with only trivial edits {num_trivial_cycles} / {len(df_cycles)} = {num_trivial_cycles / len(df_cycles):.2f}")
    print(f"Num cycles with missing clues {num_missing_clues_cycles} / {len(df_cycles)} = {num_missing_clues_cycles / len(df_cycles):.2f}")

    for var_a, var_b in [("is_success","has_cycle"), ("is_success","not_has_cycle"),
                        ("has_only_trivial_edits", "has_only_rewrite_edits"),
                        ("is_success","has_long_cycle"),
                        # ("is_success","has_breakout_edge"),
                        # ("has_breakout_edge","is_success")
                        ]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, df_cycles)
        # print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    print("HAS CYCLES")
    df_has_cycles = df_cycles[df_cycles["has_cycle"]]
    print(len(df_has_cycles))
    succ_cycles = df_cycles[df_cycles["is_success"] & df_cycles["has_cycle"]]
    print(f"has cycle and is succ: {len(succ_cycles)}")
    for v in ["has_0_breakout_edge","has_l_breakout_edge","has_m_breakout_edge","has_a_breakout_edge",
              "has_d_breakout_edge","last_edge"]:
        print(f"How many cycles have {v} edge: {df_has_cycles[v].sum()} / {len(df_has_cycles)} = {(df_has_cycles[v]).mean():.2f}")
        print(f"How many succ cycles have {v} edge: {succ_cycles[v].sum()} / {len(succ_cycles)} = {(succ_cycles[v]).mean():.2f}")
    
    succ_cycles.to_csv(f"{outdir}/succ_cycles_with_edge_out.csv")
    print(f"prob succ {df_has_cycles['is_success'].mean()}")
    for var_a, var_b in [("is_success","last_edge"),
                        #  ("not_has_breakout_edge","is_success"),
                        #  ("is_success", "not_has_breakout_edge"),
                        # ("is_success","has_breakout_edge"),
                        # ("has_breakout_edge","has_two_cycle"),
                        # ("has_two_cycle","has_breakout_edge"),
                        # ("has_breakout_edge","is_success")
                        ]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, df_has_cycles)
        # print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    print(f"how many beats out of cycles {df_has_cycles['last_edge'].sum()}/{len(df_has_cycles)} = {df_has_cycles['last_edge'].mean()}")
    # print(f"has_breakout out of cycles {df_has_cycles['has_breakout_edge'].sum()}/{len(df_has_cycles)} = {df_has_cycles['has_breakout_edge'].mean()}")
    
    # print("SUCC CYCLES")
    # succ_cycles = df_has_cycles[df_has_cycles["is_success"]]
    # for var_a, var_b in [("has_breakout_edge","has_long_cycle"),
    #                      ("has_breakout_edge","is_success")]:
    #     prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, succ_cycles)
    #     # print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")
    #     print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")
    # print(f"has_breakout out of succ cycles {succ_cycles['has_breakout_edge'].sum()}/{len(succ_cycles)} = {succ_cycles['has_breakout_edge'].mean()}")
    # print(f"last_edge out of succ cycles {succ_cycles['last_edge'].sum()}/{len(succ_cycles)} = {succ_cycles['last_edge'].mean()}")
    
    corr = display_pearsonr_results(df_cycles, [("is_success","cycle_num_edges")])
    print(corr)

    # """
    # 3. Rewrites/breakout edges

    # Rewrites do not help model, but help student debug what is wrong with model.

    # Plot: how often does a rewrite lead directly to success node?
    # `P(success | rewrite)` vs `P(success | no rewrites)`
    # Answer: not very often.

    # how often is a rewrite followed by a substantial edit? And how often
    # is a rewrite+substatial edit lead to success?

    # `P(success | rewrite->substatial)`
    # """
    # path_data = []
    # for graph in graphs:
    #     for student, edge_list in graph.get_student_edges().items():
    #         last_edge = edge_list[-1]
    #         has_final_rewrite = all([str(t)[0] in ["l","m","0"] for t in last_edge._edge_tags])
    #         path_data.append({
    #             "student": student,
    #             "problem": graph.problem,
    #             "edge_list": edge_list,
    #             "last_edge": last_edge,
    #             "has_final_rewrite": has_final_rewrite,
    #             "not_has_final_rewrite": not has_final_rewrite,
    #             "is_success": last_edge.state == "success",
    #             "has_rewrite": any([any([str(t)[0] in ["m","l","0"] for t in e._edge_tags] for e in edge_list)]),
    #             "num_rewrite->subst": num_rewrite_to_subst(edge_list)
    #         })
    # path_df = pd.DataFrame(path_data)

    # num_last_edge_is_rewrite = path_df["has_final_rewrite"].sum()
    # print(f"P(is_success & has_final_rewrite): {(path_df['is_success']& path_df['has_final_rewrite']).mean():.2f}")
    # print(f"has final rewrite {num_last_edge_is_rewrite} / {len(path_df)} = {path_df['has_final_rewrite'].mean():.2f}")
    # print(f"not has final rewrite {path_df['not_has_final_rewrite'].sum()} / {len(path_df)} = {path_df['not_has_final_rewrite'].mean():.2f}")

    # path_df["rewrite->subst"] = path_df["num_rewrite->subst"].apply(lambda x: x>0)
    # path_df["not_rewrite->subst"] = path_df["rewrite->subst"].apply(lambda x: not x)

    # """
    # How often is a success edge a rewrite? versus not

    # P(is_success | has_final_rewrite)
    # """
    # for var_a, var_b in [("has_final_rewrite", "is_success"), ("not_has_final_rewrite", "is_success"),
    #                      ("rewrite->subst","is_success"), ("has_rewrite","is_success")]:
    #     prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, path_df)
    #     # print(f"P( {var_a} | {var_b}) = var_a {prob_a:.2f} var_b {prob_b:.2f} a_given_b: {prob_a_given_b:.2f}")
    #     print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    # """
    # Breakout edges and rewrites:
    # - How often is a cycle followed by a substantial edit within 2 steps
    # Does this lead to success?
    # """
    


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