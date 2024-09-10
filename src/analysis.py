"""
Takes a dataset with an "all_completions" split and computes metrics over it
"""
import os
import numpy as np
from datasets import load_dataset, load_from_disk
import argparse
from multiprocessing import cpu_count

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


def pass_k_per_field(ds, field, n, k=1, extras={}):
    ds = ds.to_pandas()[[field, "is_success", *list(extras.keys())]]
    ds = ds.groupby(field).agg({"is_success": "sum", field: "first", **extras})
    ds[f"pass@{k}"] = ds["is_success"].apply(lambda x: estimator(n,x, k))
    return ds

def load(dataset, split):
    if os.path.exists(dataset):
        return load_from_disk(dataset)[split]
    else:
        return load_dataset(dataset, split=split)
    
def main(args):
    n_tasks = 953
    ds = load(args.dataset, split=args.split).select(range(n_tasks*20))
    print(ds)
    pass_k_per_prompt = pass_k_per_field(ds, "__index_level_0__", n=20, k=1, extras={"problem":"first"})
    print(pass_k_per_prompt)
    pass_k_per_problem = pass_k_per_prompt.groupby("problem").agg({"pass@1":"mean"})
    
    print(pass_k_per_problem["pass@1"].mean())
    
    ds = ds.map(lambda x: {**x, "group": _get_group(x)}, num_proc=cpu_count()-1)
    results_df = ds.to_pandas().groupby(["problem", "prompt", "group"]).agg(
        c=("is_success", np.sum), n=("is_success", "count")
    )
    print(results_df)
    results_df.reset_index(inplace=True)
    results_df["pass1"] = results_df.apply(
        lambda row: estimator(row["n"], row["c"], 1), axis=1
    )
    # # Calculate mean pass@1 for each group
    results_df = results_df.groupby(["group"]).agg(pass1=("pass1", np.mean))
    print(results_df)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("--split", default="all_completions")
    args = parser.parse_args()
    main(args)