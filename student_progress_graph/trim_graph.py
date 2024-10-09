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
from tqdm import tqdm

def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    for graph_yaml in tqdm(glob.glob(f"{args.graph_dir}/*.yaml")):
        # only do tagged graphs
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if graph_name not in SUCCESS_CLUES.keys():
            print(f"Skipping {graph_name}")
            continue
        graph = load_graph(graph_yaml)
        graph.problem_clues = load_problem_clues(args.problem_clues_yaml, graph.problem)
        problem_answers = load_problem_answers(args.problem_clues_yaml, graph.problem)
        graph = trim_graph(graph, problem_answers)
        with open(f"{args.outdir}/{graph.problem}.yaml", "w") as fp:
            yaml.dump(graph, fp)

        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_dir")
    parser.add_argument("outdir")
    parser.add_argument("problem_clues_yaml")
    args = parser.parse_args()
    main(args)