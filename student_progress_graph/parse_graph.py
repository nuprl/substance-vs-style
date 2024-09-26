"""
Parses data into a Graph for each problem
"""
import argparse
from utils import load
from datasets import Dataset, disable_caching
from datasets.utils.logging import disable_progress_bar
from multiprocessing import cpu_count
from .graph_utils import anonimize_filename, get_diff, extract_error_message, load_graph
from .graph import Graph, Node, Edge, find_node, compute_state
from typing import List
from tqdm import tqdm
import os
import yaml


def number_attempts(ds: Dataset) -> Dataset:
    """
    Numbers student attempts in the dataset
    """
    def get_key(x):
        return (x["problem"], x["username"])
    
    # compute total num attempts per key
    df = ds.to_pandas()
    df["num_attempts"] = [1]*len(df)
    df = df.groupby(["problem","username"]).agg({"num_attempts": "sum"}).reset_index()
    # populate dataset with num_attempts column
    key_to_num_attempts = {}
    for dikt in df.to_dict("records"):
        key_to_num_attempts[get_key(dikt)] = dikt["num_attempts"]
    ds = ds.map(lambda x: {**x, "num_attempts": key_to_num_attempts[get_key(x)]},
                num_proc=cpu_count(), desc="Counting attempts")
    
    # make attempt_ids per key
    new_ds = [{**ds[0], "attempt_id": 0}]
    counter = 0
    for i, row in enumerate(ds.select(range(1, len(ds)))):
        prev_problem, prev_username = get_key(new_ds[-1])
        if row["problem"] != prev_problem or row["username"] != prev_username:
            # start new counter
            counter = 0
        else:
            # continue counter
            counter += 1
        new_ds.append({**row, "attempt_id": counter})
    
    return Dataset.from_list(new_ds)

def compute_diffs(ds: Dataset) -> Dataset:
    """
    Compute diffs from a students previous prompt.
    First prompt is None
    """
    new_ds = []
    for i,row in enumerate(ds):
        if row["attempt_id"] == 0:
            new_ds.append({**row, "diff": None})
        else:
            prev = ds[i-1]
            # sanity check
            assert (prev["attempt_id"] == row["attempt_id"]-1 and 
                    prev["username"] == row["username"] and
                    prev["problem"] == row["problem"])
            new_ds.append({**row, "diff": get_diff(prev["prompt"], row["prompt"])})
    return Dataset.from_list(new_ds)

def parse_edges(ds: Dataset, nodes: List[Node]) -> List[Edge]:
    # collect student edges
    edges = []
    
    for i,item in enumerate(ds):
        if item["attempt_id"] == 0:
            continue
        
        edge = Edge(
            node_from=find_node(ds[i-1]["stdout"], ds[i-1]["stderr"], nodes),
            node_to=find_node(item["stdout"], item["stderr"], nodes),
            username=item["username"],
            prompt_from=ds[i-1]["prompt"],
            prompt_to=item["prompt"],
            completion_from=ds[i-1]["completion"],
            completion_to=item["completion"],
            diff= item["diff"],
            attempt_id=item["attempt_id"],
            total_attempts=item["num_attempts"],
            state=compute_state(item["is_success"], item["last_attempt"])
        )
        
        edges.append(edge)
        
    return edges
    
def parse_nodes(ds: Dataset) -> List[Node]:
    # for a problem, collect set of stdout/stderr
    nodes = set()
    for item in ds:
        nodes.add(Node(id=-1, stderr=item["stderr"], stdout=item["stdout"]))
    # assign node ids
    nodes = [Node(i, stderr=n.stderr, stdout=n.stdout) for i,n in enumerate(nodes)]
    return nodes

def parse_graph(ds: Dataset, problem:str) -> Graph:
    nodes = parse_nodes(ds)
    edges = parse_edges(ds, nodes)
    return Graph(nodes=nodes, edges=edges, problem=problem)

def main(args):
    disable_caching()
    disable_progress_bar()
    os.makedirs(args.outputdir, exist_ok=True)
    
    ds = load(args.dataset, args.split)
    if not "stderr" in ds.column_names:
        raise ValueError("Please run evaluate to get stderr/stdout first")
    
    ds = number_attempts(ds)
    if args.cluster_by_error_msg:
        ds = ds.map(lambda x: {**x, "stderr": list(map(extract_error_message,x["stderr"]))},
            desc="Extracting error msg", num_proc=cpu_count())
    else:
        ds = ds.map(lambda x: {**x, "stderr": list(map(anonimize_filename,x["stderr"]))},
            desc="Normalizing stderr", num_proc=cpu_count())
        
    # sort by attempt_number
    ds = ds.sort(["problem","username","attempt_id"])
    
    # add diffs
    ds = compute_diffs(ds)
    
    # parse into graphs for each problem
    for problem in tqdm(set(ds["problem"]), desc="Parsing problem"):
        problem_ds = ds.filter(lambda x: x["problem"] == problem, num_proc=cpu_count())
        problem_graph = parse_graph(problem_ds, problem)
        
        with open(f"{args.outputdir}/{problem}.yaml", "w") as fp:
            # yaml.Dumper.ignore_aliases = lambda *args : True
            yaml.dump(problem_graph, fp, default_style="|")
        
        # sanity check
        new_problem = load_graph(f"{args.outputdir}/{problem}.yaml")
        
        assert new_problem == problem_graph
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outputdir")
    parser.add_argument("--cluster-by-error-msg", action="store_true")
    parser.add_argument("--split", type=str, default=None)
    args = parser.parse_args()
    main(args)
