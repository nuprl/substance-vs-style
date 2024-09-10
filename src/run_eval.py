"""
Run studenteval completions from a dataset with columns

- prompt
- temperature
- top_p
- max_tokens
- completion
- completion_id
- extras
    - __index_level_0__
    - assertions
    - completion
    - entrypoint
    - first_attempt
    - is_first_failure
    - is_first_success
    - is_last_failure
    - is_last_success
    - is_success
    - last_attempt
    - prints
    - problem
    - prompt
    - submitted_text
    - tests_passed
    - total_tests
    - username
"""
import datasets
import argparse
import subprocess
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from tqdm import tqdm
import tempfile
EXECUTION_TIMEOUT = 15

def generate_splits(ds):
    # save main as csv
    ds.to_csv("/tmp/studenteval_completions.csv")
    filtered_data = {}
    for item in ds:
        idx = item["__index_level_0__"]
        if idx in filtered_data.keys():
            if not filtered_data[idx]["is_success"] and item["is_success"]:
                filtered_data[idx] = item
        else:
            filtered_data[idx] = item
    # save filtered csv
    pd.DataFrame.from_records(filtered_data).to_csv("/tmp/studenteval_filtered.csv")
    return datasets.load_dataset("csv", data_files={
        "test": "/tmp/studenteval_filtered.csv",
        "all_completions": "/tmp/studenteval_completions.csv"
    })
    
def run_problem(ex):
    tests_passed = 0
    tests = ["assert "+ a for a in ex["assertions"].split("assert ") if a != ""]
    assert len(tests) == ex["total_tests"]
    
    for idx,test in enumerate(tests):
        prompt = ex["prompt"].strip() + "\n    " + ex["completion"] + test
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", prefix=f'{ex["_id"]}_{idx}_') as f:
        # with open(f"/tmp/{prefix}.py", "w") as f:
            f.write(prompt)
            f.flush()
            try:
                result = subprocess.run(
                    ["python3", f.name],
                    timeout=EXECUTION_TIMEOUT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                exit_code = 1
        
        if exit_code == 0:
            tests_passed += 1
    assert tests_passed <= len(tests)
    return {**ex, "is_success": tests_passed == len(tests), "tests_passed": tests_passed}

def main(args):
    ds = datasets.load_from_disk(args.dataset).select(range(1000))
    ds = ds.map(lambda x,i: {**x["extras"], "completion": x["completion"],
                           "completion_id": x["completion_id"], "temperature": x["temperature"], "_id": i}, desc="Flattening", with_indices=True)
    print(ds)
    with ThreadPoolExecutor(max_workers=cpu_count() - 1) as executor:
        res = list(tqdm(executor.map(run_problem, ds), total=len(ds)))
        ds = datasets.Dataset.from_list(res)
        
    ds = ds.remove_columns(["extras","_id"])
    print(ds)
    # create splits
    ds = generate_splits(ds)
    print(ds)
    ds.save_to_disk(args.outdataset)
    # num success
    print(ds.to_pandas()["is_success"].mean())
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outdataset")
    args = parser.parse_args()
    main(args)