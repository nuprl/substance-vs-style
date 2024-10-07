"""

This script calculates pass@k. It receives a list of directories as its
argument, and calculates the mean pass@k for the set of problems in each
directory. It checks that all results in a directory were generated at the same
temperature. It calculates pass@1 for temperature 0.2 and both pass@10 and
pass@100 for temperature 0.8.

The output has the following columns:

- Dataset: the name of a directory
- Pass@k: the value of k
- Estimate: the mean pass@k for the problems in the directory
- NumProblems: the number of problems in the directory
- MinCompletions: the minimum number of completions for any problem in the 
  directory
- MaxCompletions: the maximum number of completions for any problem in the
  directory
"""
import numpy as np
from pathlib import Path
import itertools
import argparse

from pathlib import Path
import json
import gzip
from typing import Optional
import sys
from datasets import load_dataset

# def get_all_firstlast_indices():
#     ds = load_dataset("wellesley-easel/StudentEval",split="only_subsets")
#     first_last_indices=[]
#     for data in ds:
#         if data["first_attempt"]==True or data["last_attempt"]==True:
#             first_last_indices.append(data["__index_level_0__"])
#     assert len(first_last_indices)==953
#     return first_last_indices

def get_subset_indices():
    ds = load_dataset("wellesley-easel/StudentEval",split="only_subsets")
    first_last_indices=[]
    first_success_indices=[]
    first_failure_indices=[]
    last_success_indices=[]
    last_failure_indices=[]
    for data in ds:
        if data["first_attempt"]==True or data["last_attempt"]==True:
            first_last_indices.append(data["__index_level_0__"])
        if data["is_first_success"]==True:
            first_success_indices.append(data["__index_level_0__"])
        elif data["is_first_failure"]==True:
            first_failure_indices.append(data["__index_level_0__"])
        elif data["is_last_success"]==True:
            last_success_indices.append(data["__index_level_0__"])
        elif data["is_last_failure"]==True:
            last_failure_indices.append(data["__index_level_0__"])
            
    assert len(first_success_indices)+len(first_failure_indices)+len(last_success_indices)+len(last_failure_indices)==len(first_last_indices)
    return first_last_indices,first_success_indices,first_failure_indices,last_success_indices,last_failure_indices

def gunzip_json(path: Path) -> Optional[dict]:
    """
    Reads a .json.gz file, but produces None if any error occurs.
    """
    try:
        with gzip.open(path, "rt") as f:
            data = json.load(f)
            return data
    except Exception as e:
        return None


def gzip_json(path: Path, data: dict) -> None:
    with gzip.open(path, "wt") as f:
        json.dump(data, f)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

    

def estimator(n: int, c: int, k: int) -> float:
    """
    Calculates 1 - comb(n - c, k) / comb(n, k).
    """
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


def for_file_orig(path):
    data = gunzip_json(path)
    if data is None:
        return None
    n = len(data["results"])
    c = len([True for r in data["results"] if r["status"]
            == "OK" and r["exit_code"] == 0])
    __index_level_0__ = data["__index_level_0__"]
    return {
        "__index_level_0__":__index_level_0__,
        "pass@1": estimator(n, c, 1),
        "pass@10": estimator(n, c, 10),
        "pass@100": estimator(n, c, 100),
        "n": n,
        "c": c,
        "temperature": data["temperature"] if "temperature" in data else 0.2
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suppress-header",
                        action="store_true", help="Suppress the header")
    parser.add_argument("-k", type=int, default=1, help="The value of k")
    parser.add_argument(
        "--orig_dir", type=str,  help="Directory with full results of orig studenteval", default="generations_studenteval/multiple")
    args = parser.parse_args()
    name = args.orig_dir
    orig_results = [for_file_orig(p) for p in itertools.chain(
            Path(args.orig_dir).glob("*.results.json"), Path(args.orig_dir).glob("*.results.json.gz"))]
    first_last_indices,first_success_indices,first_failure_indices,last_success_indices,last_failure_indices = get_subset_indices()
    orig_results_firstlast = [r for r in orig_results if r["__index_level_0__"] in first_last_indices]
    num_problems = len(orig_results_firstlast)
    orig_results_first_success=[r for r in orig_results if r["__index_level_0__"] in first_success_indices]
    orig_results_first_failure=[r for r in orig_results if r["__index_level_0__"] in first_failure_indices]
    orig_results_last_success=[r for r in orig_results if r["__index_level_0__"] in last_success_indices]
    orig_results_last_failure=[r for r in orig_results if r["__index_level_0__"] in last_failure_indices]
    
    
    if not args.suppress_header:
        print("Dataset,Original_Pass@1,NumProblems,first_failure,last_failure,first_success,last_success")
    pass_1_original_firstlast = np.mean([r["pass@1"] for r in orig_results_firstlast])
    pass_1_original_first_failure = np.mean([r["pass@1"] for r in orig_results_first_failure])
    pass_1_original_last_failure = np.mean([r["pass@1"] for r in orig_results_last_failure])
    pass_1_original_first_success = np.mean([r["pass@1"] for r in orig_results_first_success])
    pass_1_original_last_success = np.mean([r["pass@1"] for r in orig_results_last_success])
       
    print(
        f"{name},{pass_1_original_firstlast:.4f},{num_problems},{pass_1_original_first_failure:.4f},{pass_1_original_last_failure:.4f},{pass_1_original_first_success:.4f},{pass_1_original_last_success:.4f}")

if __name__ == "__main__":
    main()