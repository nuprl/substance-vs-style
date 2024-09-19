"""
Creates a subset of a dataset with completions + stderr/stdout columns, s.t.:

- only prompts from students that were initially fails, but eventually success are present
- for each student change, compute diffs from previous prompt
- numbers student attempts

Also, creates a yaml file outlining stdout/stderr clusters for each problem.
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

def number_attempts(ds):
    df = ds.to_pandas()
    total_num_attempts = len(df.groupby(["problem","username"]))
    df["num_attempts"] = [1]*len(df)
    df["attempt_num_min"] = list(range(len(df)))
    df_new = df.groupby(["problem","username"]).agg({"num_attempts": "sum", "attempt_num_min": "first"}).reset_index()
    df = df[[c for c in df.columns if not c in ["num_attempts","attempt_num_min"]]]
    df = df.merge(df_new, on=["username","problem"])
    df["attempt_id"] = df["attempt_num_min"].apply(lambda x: int((total_num_attempts * x) / max(df["attempt_num_min"])))
    df["attempt_num"] = list(range(len(df)))
    df["attempt_num"] = df["attempt_num"] - df["attempt_num_min"]
    return Dataset.from_pandas(df[[c for c in df.columns if c != ["attempt_num_min"]]])

def get_diff(prev, new):
    diff = difflib.unified_diff(prev.split(),new.split())
    return '\n'.join(diff)

def compute_diffs(ds):
    ds = number_attempts(ds)
    new_ds = []
    for i,row in enumerate(ds):
        if row["attempt_num"] == 0:
            new_ds.append({**row, "diff": None})
        else:
            prev = ds[i-1]
            # sanity check
            assert (prev["attempt_num"] == row["attempt_num"]-1 and 
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
            clusters[item["problem"]][key].add(tuple(item[key]))
            
    return clusters
    
    
def main(args):
    ds = load(args.dataset, args.split)
    print(ds)
    
    # problems where first_attempt = Fail and last_attempt = Success
    df = ds.to_pandas()
    df = df[df["first_attempt"] != df["is_success"]]
    succ_problems = df.groupby(["problem","username"]).agg({"is_success": "any"}).reset_index()
    
    def successful_students(x):
        candidates = succ_problems[succ_problems["is_success"]]
        candidates = list(zip(candidates["username"].to_list(), candidates["problem"].to_list()))
        return (x["username"], x["problem"]) in candidates
    
    ds = ds.filter(successful_students)
    print("Post filter:\n", ds)
    
    # add diffs, normalize stderr/stdout
    ds = compute_diffs(ds)
    ds = ds.map(lambda x: {
        **x, 
        "stderr": [fmt(item) for item in x["stderr"]],
        "stdout":  [fmt(item) for item in x["stdout"]],
        "error_message": [extract_error_message(fmt(item)) for item in x["stderr"]]
    }, num_proc = cpu_count())
    
    ds.save_to_disk(args.outdataset)
    
    df = ds.to_pandas()
    num_attempts = len(df.groupby(["problem","username"]))
    print(df, num_attempts, max(df["attempt_id"]))
    
    clusters = compute_clusters(ds)
    with open(args.clusters_yaml, "w") as fp:
        yaml.dump(clusters, fp)
    # count clusters
    data = []
    for k,v in clusters.items():
        data.append({"problem":k, "stdout": len(v["stdout"]),
                     "stderr": len(v["stderr"]),
                     "error_msg": len(v["error_message"]),
                     "prompts": len(v["prompt"])})
    
    df_counts = pd.DataFrame(data)
    print(df_counts)
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outdataset")
    parser.add_argument("clusters_yaml")
    parser.add_argument("--split", type=str, default=None)
    args = parser.parse_args()
    main(args)
