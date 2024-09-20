"""
Creates a subset of a dataset with completions + stderr/stdout columns, s.t.:

- only prompts from students that were initially fails, but eventually success are present
- for each student change, compute diffs from previous prompt
- numbers student attempts

Also, creates a yaml file outlining stdout/stderr clusters for each problem +
creates a yaml file outlining student trajectories for each problem
"""
import argparse
from utils import load
import numpy as np
from datasets import Dataset
import difflib
import re
from functools import partial
from multiprocessing import cpu_count
import yaml
import pandas as pd
from collections import defaultdict
import json

def anonimize_filename(stderr):
    return re.sub("/tmp/.*?\.py", "/tmp/file.py", stderr)

def fmt(std):
    """
    Formats stderr/stdout to anonimize filenames where present
    and remove escape chars
    """
    if std is None or len(std) == 0:
        return std
    else:
        return anonimize_filename(std.encode("utf-8").decode('unicode_escape'))

def extract_error_message(stderr):
    stderr = stderr.strip().split("\n")[-1].split("Error:")[0].strip()
    return f"{stderr}Error"

def get_diff(prev, new):
    # ndiff shows full prompt, unified_diff shows localized change
    diff = difflib.unified_diff(prev.split(),new.split())
    return ''.join(diff)

def number_attempts(ds):
    """
    Key is (problem, username)
    """
    def get_key(x):
        return (x["problem"], x["username"])
    
    # compute total num attempts per key
    df = ds.to_pandas()
    total_num_attempts = len(df.groupby(["problem","username"]))
    df["num_attempts"] = [1]*len(df)
    df = df.groupby(["problem","username"]).agg({"num_attempts": "sum"}).reset_index()
    key_to_num_attempts = {}
    for dikt in df.to_dict("records"):
        key_to_num_attempts[get_key(dikt)] = dikt["num_attempts"]
    ds = ds.map(lambda x: {**x, "num_attempts": key_to_num_attempts[get_key(x)]},
                num_proc=cpu_count(), desc="Counting attempts")
    
    # make attempt_ids per key
    new_ds, counter = None, None
    for i, row in enumerate(ds):
        if i == 0:
            new_ds = [{**row, "attempt_id": 0}]
            counter = 0
            continue
        prev_problem, prev_username = get_key(new_ds[-1])
        if row["problem"] != prev_problem or row["username"] != prev_username:
            # start new counter
            counter = 0
        else:
            # continue counter
            counter += 1
        new_ds.append({**row, "attempt_id": counter})
    
    return Dataset.from_list(new_ds)


def compute_diffs(ds):
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

def compute_clusters(ds):
    # for each problem, see how many stderr and stdouts exist    
    clusters = {problem: {"stderr": set(), "stdout": set(), 
                          "error_message": set(), "prompt": set()} for problem in set(ds["problem"])}
    for item in ds:
        for key in ["stderr","stdout","error_message","prompt"]:
            item_key = item[key]
            if isinstance(item_key, list):
                item_key = tuple(item_key)
            clusters[item["problem"]][key].add(item_key)
            
    # convert to lists for yaml
    for problem_name,problem_data in clusters.items():
        for k,v in problem_data.items():
            list_val = list(v)
            for i,ele in enumerate(list_val):
                if isinstance(ele, tuple):
                    list_val[i] = list(ele)
            clusters[problem_name][k] = list_val

    return clusters

def compute_trajectories(ds):
    # for each problem, collect student trajectory paths  
    trajectories = {problem: {} for problem in set(ds["problem"])}
    
    # populate {problem: {username: {}}}
    for data in ds:
        if not data["username"] in trajectories[data["problem"]].keys():
            trajectories[data["problem"]].update(
                {data["username"]: 
                    {"stderr": [], 
                     "stdout": [], 
                     "diff": [], 
                     "prompt":[], 
                     "edges":[],
                     "attempt_id": []}
                })
            
        for key in ["stderr","stdout","diff","prompt","attempt_id"]:
            trajectories[data["problem"]][data["username"]][key].append(data[key])
    
    # populate edges separately
    for prob, traj in trajectories.items():
        for student, data in traj.items():
            # sanity check order
            order_ids = data["attempt_id"]
            assert order_ids == list(range(max(order_ids)+1)), order_ids
            assert len(order_ids) == len(data["stdout"]) == len(data["stderr"])
            
            nodes = [list(n) for n in zip(data["stdout"], data["stderr"])]
            edges = [list(e) for e in zip(nodes, nodes[1:])]
            trajectories[prob][student]["edges"] = edges

    return trajectories
    
def show_info(ds, clusters, trajectories):
    """
    Print/Check some info for debug
    """
    # check attempt_id computed correctly
    df = ds.to_pandas()
    num_attempts = df.groupby(["problem", "username"]).agg({
        "num_attempts":"first"
        }).reset_index().rename(columns={"num_attempts":"attempt_id"})
    max_attempt_ids = df.groupby(["problem", "username"]).agg({
        "attempt_id": (lambda x: max(x) + 1)
        }).reset_index()
    assert num_attempts.equals(max_attempt_ids), f"{num_attempts} != {max_attempt_ids}"
    
    # last attempt should always have attempt_id = max
    last_attempt_ds = ds.filter(lambda x: x["last_attempt"] and x["attempt_id"]+1 == x["num_attempts"], num_proc=cpu_count())
    assert len(last_attempt_ds) == len(df[df["last_attempt"]])
    
    # count clusters
    data = []
    for k,v in clusters.items():
        data.append({"problem":k, "stdout": len(v["stdout"]),
                     "stderr": len(v["stderr"]),
                     "error_msg": len(v["error_message"]),
                     "prompts": len(v["prompt"])})
    
    df_counts = pd.DataFrame(data)
    print("[INFO] Clusters of stdout/stderr for each problem:\n", df_counts)
    
    # print some trajectories data
    #   - for each problem, how many students
    #   - for each problem, len list of trajectories
    problem_data = []
    for problem, traj in trajectories.items():
        problem_data.append({
            "problem":problem,
            "num_students": len(traj),
            "len_trajectories": [len(v["stdout"]) for v in traj.values()]
        })
    print("\n[INFO] Student trajectory info for each problem:\n", pd.DataFrame(problem_data))
    
    # check that there is 1 end node for each problem
    problem_to_end_nodes = {}
    for item in ds:
        if item["last_attempt"]:
            node = ("\n".join(item["stdout"]), "\n".join(item["stderr"]))
            if item["problem"] not in problem_to_end_nodes.keys():
                problem_to_end_nodes[item["problem"]] = set()
            problem_to_end_nodes[item["problem"]].add(node)
    end_node_counts = {k:len(v) for k,v in problem_to_end_nodes.items()}
    print("\n[INFO] How many end nodes for each problem:")
    print(json.dumps(end_node_counts, indent=4, sort_keys=True))
    
    # inspect entries with multiple end nodes
    multi_end_nodes_info = []
    for k,v in problem_to_end_nodes.items():
        if len(v) > 1:
            tests = list(set(df[df["problem"] == k]["assertions"].to_list()))
            prints = list(set(df[df["problem"] == k]["prints"].to_list()))
            assert len(tests) == 1
            assert len(prints) == 1
            multi_end_nodes_info.append({
                "problem": k,
                "node": list(v),
                # "tests": tests,
                # "prints": prints
            })
    with open("/tmp/multi_end_nodes.yaml","w") as fp:
        yaml.dump(multi_end_nodes_info, fp, default_style="|")
    
def main(args):
    ds = load(args.dataset, args.split)
    ds = number_attempts(ds)
    print(ds)
    
    # problems where first_attempt = Fail and last_attempt = Success
    #   - ignore entried where the first attempt was also last (no progression)
    ds = ds.filter(lambda x: not (x["first_attempt"] and x["last_attempt"]), 
                   num_proc=cpu_count(), desc="Filtering out non-progressions")
    successful = ds.filter(lambda x: x["last_attempt"] and x["is_success"], 
                    num_proc=cpu_count(), desc="Filter by successful last")
    candidates = set(list(zip(successful["problem"], successful["username"])))
    ds = ds.filter(lambda x: (x["problem"], x["username"]) in candidates, 
                   num_proc=cpu_count(), desc="Filter candidates")
    print("Post filter:\n", ds)
    
    # sanity: sort by attempt_number
    ds = ds.sort(["problem","username","attempt_id"])
    
    # add diffs, normalize stderr/stdout
    ds = compute_diffs(ds)
    ds = ds.map(lambda x: {
        **x, 
        "stderr": [fmt(item) for item in x["stderr"]],
        "stdout":  [fmt(item) for item in x["stdout"]],
        "error_message": [extract_error_message(fmt(item)) for item in x["stderr"]]
    }, num_proc = cpu_count())
    ds.save_to_disk(args.outdataset)
    
    # compute clusters(nodes) for each problem
    clusters = compute_clusters(ds)
    with open(args.clusters_yaml, "w") as fp:
        yaml.dump(clusters, fp)
    
    # compute trajectories(edges) for each problem
    trajectories = compute_trajectories(ds)
    with open(args.trajectories_yaml, "w") as fp:
        yaml.dump(trajectories, fp)
        
    """
    Print/Check some info for debug
    """
    # show_info(ds, clusters,trajectories)
    

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outdataset")
    parser.add_argument("clusters_yaml")
    parser.add_argument("trajectories_yaml")
    parser.add_argument("--split", type=str, default=None)
    args = parser.parse_args()
    main(args)
