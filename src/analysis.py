"""
Takes a dataset with an "all_completions" split and computes metrics over it
"""
import os
import numpy as np
from datasets import load_dataset, load_from_disk
import argparse
from multiprocessing import cpu_count
import pandas as pd
from utils import load, estimator

    
def pass_k_per_field(df, field, k):
    df_field = df.groupby([field,"__index_level_0__"]).agg({
        "is_success": "sum", 
        "completion_id": lambda x: max(x) + 1
        }).reset_index()
    df_field = df_field.rename(columns={"is_success":"c","completion_id":"n", "__index_level_0__":"prompt_id"})
    df_field["pass@1"] = df_field.apply(lambda x: estimator(x["n"], x["c"], k),axis=1)
    return df_field
    
def main(args):
    ds = load(args.dataset, split=args.split)
    print(ds)
    for field in ["problem","username"]:
        df_field = pass_k_per_field(ds.to_pandas(), field, k=1)
        per_field = df_field[[field,'pass@1']].groupby(field).agg({'pass@1':'mean'}).reset_index().sort_values("pass@1")
        print(f"Mean Pass@1 per {field}:\n{per_field}")
        print(f"Mean pass@1:", df_field["pass@1"].mean())
    
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