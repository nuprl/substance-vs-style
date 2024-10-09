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
import datasets
from tqdm import tqdm

def main(args):
    graphs = []
    for graph_yaml in tqdm(glob.glob(f"{args.graph_dir}/*.yaml")):
        # discard any that we have not verified yet
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if graph_name not in SUCCESS_CLUES.keys():
            continue
        graph = load_graph(graph_yaml)
        # recompute state on edges
        # 1. score nodes
        problem_answers = load_problem_answers(args.problem_clues_yaml, graph.problem)
        graph = score_nodes_by_tests_passed(graph, problem_answers, overwrite=True)
        success_node = [n for n in graph.nodes if n._node_tags == len(problem_answers)]
        if len(success_node) != 1:
            print(graph_name, len(success_node))
            print([n._node_tags for n in graph.nodes])
            continue
        success_node = success_node[0]

        for i,e in enumerate(graph.edges):
            if e.node_to.id == success_node.id:
                if e.state != "success":
                    print(f"False fail {graph.problem}, {e.node_from.id}->{e.node_to.id}, {e.username}")
                elif e.state == "success" and e.node_to.id != success_node.id:
                    print(f"False success {graph.problem}, {e.node_from.id}->{e.node_to.id}, {e.username}")
                elif e.state == "neutral" and (e.node_to.id == success_node.id or e.node_from.id == success_node.id):
                    print(f"False neutral {graph.problem}, {e.node_from.id}->{e.node_to.id}, {e.username}")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_dir")
    parser.add_argument("problem_clues_yaml")
    args = parser.parse_args()
    main(args)