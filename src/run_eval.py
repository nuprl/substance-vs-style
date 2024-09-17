"""
Heavily inspired by bigcode_evaluation_harness.
Evaluate studenteval completions from a dataset with the following columns.
This dataset can be generated using batched_lm_generation.vllm_base.

- prompt
- temperature
- top_p
- max_tokens
- completion
- completion_id
- extras
    - __index_level_0__
    - assertions
    - first_attempt
    - last_attempt
    - prints
    - problem
    - total_tests
    - prompt
    - username
    
1. Flattens dataset to remove `extras` field
2. runs every completion and records `is_success, is_first_success, is_first_failure, is_last success, is_last_failure, tests_passed`
3. Creates a dataset with 2 splits:
    test - for each problem, stores the first completion (simulates 1 completion)
    all_completions - the eval results of all completions (for computing pass@k)
"""
import os
import datasets
import argparse
import subprocess
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from tqdm import tqdm
import tempfile
from utils import load
EXECUTION_TIMEOUT = 15

def generate_splits(ds):
    # save main as csv
    df = ds.to_pandas()
    df.to_csv("/tmp/studenteval_completions.csv")
    # drop all completions but 0
    if "completion_id" in df.columns:
        filtered_df = df[df["completion_id"] == 0]
        # save filtered csv
        filtered_df.to_csv("/tmp/studenteval_filtered.csv")
    
    if not os.path.exists("/tmp/studenteval_filtered.csv"):
        data_files = {"test": "/tmp/studenteval_completions.csv"}
    else:
        data_files={
            "test": "/tmp/studenteval_filtered.csv",
            "all_completions": "/tmp/studenteval_completions.csv"
        }
        
    ds = datasets.load_dataset("csv", data_files=data_files)
        
    if os.path.exists("/tmp/studenteval_filtered.csv"):
        os.remove("/tmp/studenteval_filtered.csv")
    if os.path.exists("/tmp/studenteval_completions.csv"):
        os.remove("/tmp/studenteval_completions.csv")
        
    return ds
    
def run_problem(ex):
    tests_passed = 0
    tests = ["assert "+ a for a in ex["assertions"].split("assert ") if a != ""]
    assert len(tests) == ex["total_tests"]
    
    for idx,test in enumerate(tests):
        assert ex["prompt"] not in ex["completion"]
        prompt = ex["prompt"].strip() + "\n    " + ex["completion"] + "\n"+ test
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", prefix=f"{ex['_id']}_{idx}") as f:
            f.write(prompt)
            f.flush()
            stderr= None
            try:
                result = subprocess.run(
                    ["python3", f.name],
                    timeout=EXECUTION_TIMEOUT,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                )
                exit_code = result.returncode
                stderr = result.stderr
                if stderr is not None:
                    stderr = stderr.decode("utf-8")
            except subprocess.TimeoutExpired:
                exit_code = 1
        
        if exit_code == 0:
            tests_passed += 1
            
        prompt = ex["prompt"].strip() + "\n    " + ex["completion"] + "\n"+ ex["prints"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", prefix=f"{ex['_id']}_{idx}_prints") as f:
            f.write(prompt)
            f.flush()
            stdout= None
            try:
                result = subprocess.run(
                    ["python3", f.name],
                    timeout=EXECUTION_TIMEOUT,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                )
                stdout = result.stdout
                if stdout is not None:
                    stdout = stdout.decode("utf-8")
            except subprocess.TimeoutExpired:
                pass
        
    assert tests_passed <= ex["total_tests"]
    is_success = bool(tests_passed == ex["total_tests"])
    return {**ex, "is_success": is_success, "tests_passed": tests_passed,
            "stderr":stderr,"stdout":stdout,
            "is_first_failure": ex["first_attempt"] and not is_success, 
            "is_first_success": ex["first_attempt"] and is_success, 
            "is_last_failure": ex["last_attempt"] and not is_success,
            "is_last_success": ex["last_attempt"] and is_success,}

def flatten(x, i):
    extras = x.pop("extras", None)
    if extras:
        x = {**extras, **x}
    return {**x, "_id": i}
    
def main(args):
    datasets.disable_caching()
    ds = load(args.dataset, args.split)
    ds = ds.map(flatten, desc="Flattening", with_indices=True)

    with ThreadPoolExecutor(max_workers=cpu_count() - 1) as executor:
        res = list(tqdm(executor.map(run_problem, ds), total=len(ds)))
        ds = datasets.Dataset.from_list(res)
        
    ds = ds.remove_columns(["_id"])
    # create splits
    ds = generate_splits(ds)
    ds.save_to_disk(args.outdataset)
    print(ds)
    # num success
    print("Test split success rate:", ds["test"].to_pandas()["is_success"].mean())
    print("All completions success rate:", ds["all_completions"].to_pandas()["is_success"].mean())
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outdataset")
    parser.add_argument("--split", type=str, default=None)
    args = parser.parse_args()
    main(args)
    
    
"""
PYTESTS
"""

def test_run_problem():
    ex = {
        "assertions": '''assert generateCardDeck(['S', 'H', 'D'], ['1', '2', 'A']) == ['D1', 'D2', 'DA', 'H1', 'H2', 'HA',  'S1', 'S2', 'SA']
assert generateCardDeck(['H', 'D'], ['6', 'Q', 'J', '2']) == ['D2', 'D6', 'DJ', 'DQ', 'H2','H6', 'HJ', 'HQ']
assert generateCardDeck(['H'], ['2']) == ['H2']''',
        "total_tests":3,
        "first_attempt":True,
        "last_attempt":True,
        "_id":1521,
        "completion":'''# Create a list of suits
    suits = ['H', 'D', 'C', 'S']

    # Create a list of values
    vals = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    # Create a list of cards
    cards = []

    # Create a nested loop to combine suits and values
    for suit in suits:
        for val in vals:
            cards.append(suit + val)

    # Print the list of cards''',
        "prompt":'''def generateCardDeck(suits, vals):
    """
    The program, generateCardDeck(suits, vals):, defines Card as the input data, Card == ['H'], ['2'], and creates an output that combines both [] of information.
    """''',
    }
    res = run_problem(ex)
    assert res["is_success"] == False