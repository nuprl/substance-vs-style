import glob
import pandas as pd
import argparse
import os
import glob
import pandas as pd
from .analysis_utils import (
    load_graph, 
    remove_out_of_token_errors, 
    load_problem_clues, 
    populate_clues, 
    conditional_prob, 
    check_cycles, 
    get_breakout_edge, 
    display_pearsonr_results
)
from .graph import Graph
from typing import List
import contextlib
from .student_edge_cases import OUT_OF_TOKENS_ERROR, IMPLICIT_CLUES, SUCCESS_CLUES

def load_graphs_from_dir(graph_dir: str, problem_clues_yaml:str) -> List[Graph]:
    """
    Given a dir with graph.yamls and a problem_clues.yaml, load all graphs
    """
    graphs = []
    for graph_yaml in glob.glob(f"{graph_dir}/*.yaml"):
        # discard any that we have not verified yet
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if not graph_name in SUCCESS_CLUES.keys():
            print(f"Skipping {graph_name}")
            continue
        graph = load_graph(graph_yaml)
        graph = remove_out_of_token_errors(graph) # removes 13 OOT errors, so 303-13 = 290
        graph.problem_clues = load_problem_clues(problem_clues_yaml, graph.problem)
        graph = populate_clues(graph)
        graphs.append(graph)
    return graphs

def load_terminal_edge_data(graphs: List[Graph]) -> List[dict]:
    """
    Given a list of graphs, collect details for each final edge
    """
    terminal_edge_data = []
    for graph in graphs:
        success_clues = list(SUCCESS_CLUES[graph.problem])
        for student,edge_list in graph.get_student_edges().items():
            e = max(edge_list, key=lambda x: x.attempt_id)
            assert e.state in ["success","fail"]
            is_success = e.state == "success"
            # add any implicit clues
            if graph.problem in IMPLICIT_CLUES.keys() and \
                e.username in IMPLICIT_CLUES[graph.problem]:
                e.clues += IMPLICIT_CLUES[graph.problem][e.username]
            has_all_clues = set(e.clues) == set(success_clues)

            terminal_edge_data.append({
                "problem": graph.problem,
                "success_clues": success_clues,
                "username": e.username,
                "state": e.state,
                "clues": e.clues,
                "has_final_rewrite": all([str(t)[0] in ["l","m","0"] for t in e._edge_tags]),
                "has_final_trivial": all([t == 0 for t in e._edge_tags]),
                "has_final_l": all([str(t)[0]  == "l" for t in e._edge_tags]),
                "has_final_m": all([str(t)[0]  == "m" for t in e._edge_tags]),
                "has_all_clues": has_all_clues,
                "has_leq_half_clues": (len(set(e.clues)) / len(set(success_clues))) <= 0.5,
                "is_missing_clues": not has_all_clues,
                "is_success": is_success,
                "is_fail": not is_success,
            })
    return terminal_edge_data

def terminal_edge_analysis(graphs: List[Graph], outdir: str):
    """
    Collect all students' final edges and analyse patterns. Save
    analysis data to outdir
    """
    terminal_edge_data = load_terminal_edge_data(graphs)
    terminal_edge_df = pd.DataFrame(terminal_edge_data)
    terminal_edge_df.to_csv(f"{outdir}/terminal_edge.csv")
    succ_edge_df = terminal_edge_df[terminal_edge_df["state"] == "success"]
    succ_edge_df.to_csv(f"{outdir}/successful_terminal_edges.csv")

    print("############ TERMINAL EDGE DATA ############")

    print("--- stats")
    print("num students:", len(set(terminal_edge_df["username"])))
    print("num problems:", len(set(terminal_edge_df["problem"])))
    print("num students & prob:", len(terminal_edge_df.groupby(["username","problem"])))
    print("num succ students & prob:", terminal_edge_df.groupby(["username","problem"]).agg({"is_success": "all"})["is_success"].sum())
    
    print(f"(succ & has_all_clues) / tot_succ: {succ_edge_df['has_all_clues'].sum()} / {len(succ_edge_df)} = {succ_edge_df['has_all_clues'].mean():.2f}")

    print("---- Out of all terminal edges:")
    for var_a, var_b in [("is_success","has_all_clues"), ("is_success","is_missing_clues")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, terminal_edge_df)
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    print("---- How many out of has all clues terminal edges are successful?")
    all_clues_succ = succ_edge_df['has_all_clues'].sum()
    num_all_clues = terminal_edge_df['has_all_clues'].sum()
    print(f"(succ & has_all_clues) / has_all_clues: {all_clues_succ}/{num_all_clues} = {all_clues_succ/num_all_clues:.2f}")

    print("---- How many rewrite kinds out of successful terminal edges?")
    for var in ["has_final_trivial","has_final_rewrite","has_final_l","has_final_m"]:
        nom = succ_edge_df[var]
        print(f"{var} out of succ_edges: {nom.sum()}/{len(succ_edge_df)} = {nom.mean():.2f}")
    
    # P(had_final_m|has_final_rewrite)
    for var_a, var_b in [("has_final_m","has_final_rewrite")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, succ_edge_df)
        print(f"P( {var_a} & succ | {var_b} & succ) = {prob_a_given_b:.3f}")

    print("---- Out of all SUCC final rewrite edges, how many contain m?")
    final_m = (succ_edge_df['has_final_m'] & succ_edge_df['has_final_rewrite']).sum()
    final_rewrite = succ_edge_df['has_final_rewrite'].sum()
    print(f"Num(contain m & succ / have rewrite & succ): {final_m}/{final_rewrite} = {final_m/final_rewrite:.2f}")

    print("---- Out of terminal edges with <= 0.5 clues, how many are successful with final rewrite?")
    # probability that final rewrite fixes a prompt with little clues
    # out of prompts with little clues, p(is_success | has_final_rewrite)
    leq_half_clues = terminal_edge_df[ terminal_edge_df["has_leq_half_clues"]]
    for var_a, var_b in [("is_success","has_final_rewrite")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, leq_half_clues)
        print(f"out of all final edges with little clues: P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")
    
    a = len(leq_half_clues[leq_half_clues["is_success"] & leq_half_clues["has_final_rewrite"]])
    b = leq_half_clues["has_final_rewrite"].sum()
    print(f"Num( succ & final_rewrite/ has final rewrite) in had_leq_half_clues: {a}/{b}={a/b:.2f}")

def load_cycles_data(graphs: List[str]) -> List[dict]:
    """
    For each graph, extract a summary of cycles
    """
    # dataframe [problem, cycle_num_edges, cycle_edits]
    cycles_data = []
    for graph in graphs:
        succ_students = graph.get_successful_students()
        cycle_summary = check_cycles(graph, suppress_check=True)

        for student in graph.get_students():
            if student in cycle_summary.keys():
                cycles = cycle_summary[student]
                assert len(cycles) == 1, (student, graph.problem)
                for cycle_edge_list in cycles:
                    # get breakout edge
                    last_edge = get_breakout_edge(graph, student, cycle_edge_list)

                    has_only_rewrite_edits = all([all([str(t)[0] in ["0","m","l"] for t in e._edge_tags]) 
                                                for e in cycle_edge_list])
                    has_only_trivial_edits = all([all([str(t)[0] in ["0"] for t in e._edge_tags]) 
                                                for e in cycle_edge_list])
                    cycle_clues = [set(e.clues) for e in cycle_edge_list]
                    num_edits_with_missing_clues = sum([clue != set(SUCCESS_CLUES[graph.problem]) for clue in cycle_clues])
                    num_trivial = sum([set(e._edge_tags) == set([0]) for e in cycle_edge_list])
                    num_rewrite = sum([all([str(t)[0] in ['l','m','0'] for t in e._edge_tags]) for e in cycle_edge_list])
                    has_missing_clues = all([clue != set(SUCCESS_CLUES[graph.problem]) for clue in cycle_clues])
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
                        "not_has_cycle": len(cycle_edge_list) == 0,
                        "cycle_num_edits_with_missing_clues": num_edits_with_missing_clues,
                        "cycle_num_rewrite_edits":num_rewrite,
                        "cycle_num_trivial_edits": num_trivial,
                        "cycle_clues": cycle_clues,
                        "cycle_edits": [e._edge_tags for e in cycle_edge_list],
                        "has_breakout_edge": bool(last_edge),
                        "breakout_edge_tags": [] if not last_edge else last_edge._edge_tags,
                        "has_0_breakout_edge": has_0_breakout_edge,
                        "has_m_breakout_edge": has_m_breakout_edge,
                        "has_a_breakout_edge": has_a_breakout_edge,
                        "has_l_breakout_edge": has_l_breakout_edge,
                        "has_d_breakout_edge": has_d_breakout_edge,
                        "cycle_has_only_trivial_edits": has_only_trivial_edits,
                        "cycle_has_only_rewrite_edits": has_only_rewrite_edits,
                        "has_substantial_edits": not has_only_rewrite_edits,
                        "has_missing_clues": has_missing_clues,
                        "not_has_missing_clues": not has_missing_clues,
                    })
            else:
                cycles_data.append({
                    "problem": graph.problem,"username":student,"cycle_list":[],"is_success": (student in succ_students),
                    "cycle_num_edges": 0,"has_cycle": False,"has_long_cycle": False,"not_has_cycle": True,
                    "cycle_num_edits_with_missing_clues": 0,"cycle_num_rewrite_edits":0,"cycle_num_trivial_edits":0,
                    "cycle_clues": [],"cycle_edits": [],"has_breakout_edge": False,"breakout_edge_tags": [],
                    "has_0_breakout_edge": False,"has_m_breakout_edge": False,"has_a_breakout_edge": False,
                    "has_l_breakout_edge": False,"has_d_breakout_edge": False,"cycle_has_only_trivial_edits": False,
                    "cycle_has_only_rewrite_edits": False,"has_substantial_edits": False,"has_missing_clues": False,
                    "not_has_missing_clues": False,
                })
    return cycles_data

def cycles_analysis(graphs: List[str], outdir:str):
    """
    Collect all students' cycles and analyse patterns. Save
    analysis data to outdir
    """
    cycles_data = load_cycles_data(graphs)
    df_cycles = pd.DataFrame(cycles_data)
    df_cycles.to_csv(f"{outdir}/data_cycles.csv")
    
    print("\n############ ALL CASES: CYCLES DATA ############")
    print("--- stats")
    print("num students:", len(set(df_cycles["username"])))
    print("num problems:", len(set(df_cycles["problem"])))
    print("num has cycle:", df_cycles["has_cycle"].sum())
    print("len:", len(df_cycles))
    print("num students & prob:", len(df_cycles.groupby(["username","problem"])))
    print("num succ students & prob:", df_cycles.groupby(["username","problem"]).agg({"is_success": "sum"})["is_success"].sum())
    

    print(f'(is_succ & has_cycle / tot) {(df_cycles["is_success"] & df_cycles["has_cycle"]).sum()} / {len(df_cycles)} ='+
          f'{(df_cycles["is_success"] & df_cycles["has_cycle"]).mean():.2f}')
    print("---- For each student/graph pair:")

    for var_a, var_b in [("is_success","has_cycle"), ("is_success","not_has_cycle"),
                        ("is_success","has_long_cycle"),
                        ("is_success","has_breakout_edge"),
                        ("has_breakout_edge","is_success"),
                        ("cycle_has_only_trivial_edits", "cycle_has_only_rewrite_edits")]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, df_cycles)
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")

    print("\n############ STUDENTS WITH CYCLES ############")
    df_has_cycles = df_cycles[df_cycles["has_cycle"]]
    df_has_cycles.to_csv(f"{outdir}/has_cycles.csv")

    print("---- How many trivial cycles are there out of all cycles?")
    num_trivial_cycles = df_has_cycles['cycle_has_only_trivial_edits'].sum()
    print(f"{num_trivial_cycles} / {len(df_has_cycles)} = {df_has_cycles['cycle_has_only_trivial_edits'].mean():.2f}")
    
    print("---- How many missing clues cycles are there out of all cycles?")
    num_missing_clues_cycles = df_has_cycles['has_missing_clues'].sum()
    print(f"{num_missing_clues_cycles} / {len(df_has_cycles)} = {df_has_cycles['has_missing_clues'].mean():.2f}")
    
    print("---- Of all cycles edges, how many have missing clues?")
    num_missing = df_has_cycles['cycle_num_edits_with_missing_clues'].sum()
    num_edits = df_has_cycles["cycle_list"].apply(lambda x: len(x)).sum()
    print(f"Num(missing edges/ cycle edges): {num_missing}/{num_edits}={num_missing/num_edits:.2f}")

    print("---- Of all cycles edges, how many have rewrite edits?")
    num_rewrite = df_has_cycles['cycle_num_rewrite_edits'].sum()
    num_edits = df_has_cycles["cycle_list"].apply(lambda x: len(x)).sum()
    print(f"Num(rewrite edits/ cycle edges): {num_rewrite }/{num_edits}={num_rewrite /num_edits:.2f}")
    
    print("---- Of all cycles edges, how many have trivial edits?")
    num_trivial = df_has_cycles['cycle_num_trivial_edits'].sum()
    num_edits = df_has_cycles["cycle_list"].apply(lambda x: len(x)).sum()
    print(f"Num(trivial edits/ cycle edges): {num_trivial}/{num_edits}={num_trivial/num_edits:.2f}")

    print("---- How many cycles have only REWRITE edits?")
    only_rewrite = df_has_cycles['cycle_has_only_rewrite_edits']
    print(f"{only_rewrite.sum()} / {len(df_has_cycles)} =  {only_rewrite.mean():.2f}")

    print("---- How many cycles have only trivial edits?")
    only_trivial = df_has_cycles['cycle_has_only_trivial_edits']
    print(f"{only_trivial.sum()} / {len(df_has_cycles)} =  {only_trivial.mean():.2f}")

    print("---- Of all students with cycles, what is the probability of success if a breakout edge?")
    for var_a, var_b in [("is_success","has_breakout_edge"),
                        ("is_success","has_a_breakout_edge"),
                        ("is_success","has_m_breakout_edge"),
                        ("is_success","has_l_breakout_edge"),
                        ("is_success","has_d_breakout_edge"),
                        ("is_success","has_0_breakout_edge"),]:
        prob_a, prob_b, prob_anb, prob_a_given_b = conditional_prob(var_a, var_b, df_has_cycles)
        print(f"P( {var_a} | {var_b}) = {prob_a_given_b:.2f}")


    print(f"---- Out of all that have cycles: tot {len(df_has_cycles)}")
    print(f"How many are succ? {df_has_cycles['is_success'].sum()} -> {df_has_cycles['is_success'].mean():.2f}")

    for v in ["has_0_breakout_edge","has_l_breakout_edge","has_m_breakout_edge","has_a_breakout_edge",
              "has_d_breakout_edge","has_breakout_edge"]:
        print(f"{v}: {df_has_cycles[v].sum()} / {len(df_has_cycles)} = {(df_has_cycles[v]).mean():.2f}")
    
    print("\n##### SUCC CYCLES ######")

    succ_cycles = df_has_cycles[df_has_cycles["is_success"]]
    print(f"---- Out of all SUCC cycles: tot {len(succ_cycles)}")
    succ_cycles.to_csv(f"{outdir}/succ_cycles.csv")

    for v in ["has_0_breakout_edge","has_l_breakout_edge","has_m_breakout_edge","has_a_breakout_edge",
              "has_d_breakout_edge","has_breakout_edge"]:
        print(f"{v}: {succ_cycles[v].sum()} / {len(succ_cycles)} = {(succ_cycles[v]).mean():.2f}")
    
    corr = display_pearsonr_results(df_cycles, [("is_success","cycle_num_edges")])
    print(corr)

def all_problems_analysis(graph_dir: str, outdir:str, problem_clues_yaml: str):
    graphs = load_graphs_from_dir(graph_dir, problem_clues_yaml)
    print(f"--- Running for problems {[g.problem for g in graphs]}")
    terminal_edge_analysis(graphs, outdir)
    cycles_analysis(graphs, outdir)

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