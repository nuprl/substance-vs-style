"""
Takes a dataset with an "all_completions" split and computes metrics over it
"""
import os
import numpy as np
from datasets import load_dataset, load_from_disk
import argparse
from multiprocessing import cpu_count
import pandas as pd

# from bigcode studenteval
def _get_group(item):
    """
    These boolean flags are mutually exclusive in the dataset. We turn them into a
    a string for easy grouping with Pandas.
    """
    if item["is_first_success"]:
        return "First Success"
    if item["is_last_success"]:
        return "Last Success"
    if item["is_first_failure"]:
        return "First Failure"
    if item["is_last_failure"]:
        return "Last Failure"
    return None

# from Multipl-E
def estimator(n: int, c: int, k: int) -> float:
    """
    Calculates 1 - comb(n - c, k) / comb(n, k).
    """
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

def load(dataset, split):
    if os.path.exists(dataset):
        return load_from_disk(dataset)[split]
    else:
        return load_dataset(dataset, split=split)
    
def main(args):
    ds = load(args.dataset, split=args.split)
    pass_k_per_problem = ds.to_pandas().groupby("problem").agg({"is_success": "sum", "completion_id": lambda x: max(x) + 1})
    pass_k_per_problem = pass_k_per_problem.rename(columns={"is_success":"c","completion_id":"n"}).reset_index()
    pass_k_per_problem["pass@1"] = pass_k_per_problem.apply(lambda x: estimator(x["n"], x["c"], 1),axis=1)
    pass_k_per_problem = pass_k_per_problem[["problem","pass@1"]]
    print("Pass@1 per problem:\n",pass_k_per_problem)
    print("Mean:", pass_k_per_problem["pass@1"].mean())

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("--split", default="all_completions")
    args = parser.parse_args()
    main(args)
    
"""
PYTESTS
"""

# Replicated bigcode eval to ensure same results
def test_against_bigcode():
    ds = load("llama3.1_8b_base_studenteval", split="test")
    ds = ds.map(lambda x: {**x, 
                           "success": x["is_success"],
                           "program": x["prompt"].strip()+"\n    "+x["completion"]+"\n\n"+x["assertions"]}, num_proc=cpu_count()-1)
    df = ds.to_pandas()
    bigcode_df = pd.read_csv("tests/bigcode_eval_results_llama3.1_8b_base_sep11.csv")
    merged = pd.merge(df, bigcode_df, on="program")
    num_eq = merged[merged["success_y"] == merged["success_x"]]
    assert len(num_eq) == len(merged)