import pandas as pd
from re import L
from .graph_utils import load_graph, Graph
import json
import argparse
import os
import yaml
import glob
'''
Analyzing common patterns in graphs
Hypotheses:
0. self loops are trivial edits
1. edges between two nodes are the same diffs
2. a diff either adds a clue, deletes a clue, does nothing (trivial rephrase) or does both
3.  a cycle forms when the student does not add a necessary clue or deketes one in favor of another clue,
but both are needed
4. a long path indicates trivial rewrites and/or missing clues
5. the most efficient paths progressively add clues
6. adding clues at the start or end of a prompt is significant
'''
def inspect_multi_edges(graph:Graph)->dict:
    """
    Write diffs into a format easy to analyse for point 0,1
    """
    edge_to_diffs = {}
    for edge in graph.edges:
        key = f"({edge.node_from.id}, {edge.node_to.id})"
        if not key in edge_to_diffs.keys():
            edge_to_diffs[key] = [edge.diff.replace(" \n", "\n")]
        else:
            edge_to_diffs[key].append(edge.diff.replace(" \n", "\n"))
    return {k:v for k,v in edge_to_diffs.items() if len(v) > 1}

def progress_summary(graph: Graph)->dict:
    """
    student attempt_0 ... attempt_n
    """
    student_to_attempt_tags = {}
    for e in graph.edges:
        if e.attempt_id == 1:
            student_to_attempt_tags[e.username] = [(0, e.node_from._node_tags, "start")]
        student_to_attempt_tags[e.username].append((e.attempt_id, e._edge_tags, e.state))
    
    return student_to_attempt_tags

def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    graphs = []
    for graph_yaml in glob.glob(f"{args.graph_yaml_dir}/*.yaml"):
        graph = load_graph(graph_yaml)
        if args.debug_problems and not graph.problem in args.debug_problems:
            continue
        graphs.append(graph)
    
    if args.task == "inspect_multi_edges":
        problem = {}
        for g in graphs:
            problem[g.problem] = inspect_multi_edges(g)
        with open(f"{args.outdir}/inspect_multi_edges.yaml","w") as fp:
            yaml.dump(problem, fp, default_style="|")
    elif args.task == "progress_summary":
        problem = {}
        for g in graphs:
            problem[g.problem] = progress_summary(g)
        with open(f"{args.outdir}/progress_summary.yaml","w") as fp:
            yaml.dump(problem, fp)
    else:
        raise NotImplementedError()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml_dir")
    parser.add_argument("outdir")
    parser.add_argument("task", choices=["all", "inspect_multi_edges", "progress_summary"])
    parser.add_argument("--debug-problems", nargs="+", default=None)
    args = parser.parse_args()
    main(args)