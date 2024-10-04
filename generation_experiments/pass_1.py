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


def gunzip_json(path: Path) -> Optional[dict]:
    """
    Reads a .json.gz file, but produces None if any error occurs.
    """
    try:
        with gzip.open(path, "rt") as f:
            return json.load(f)
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

import re
def check_changed(data):
    submitted_text = data['submitted_text']
    prompt = data['prompt']
    match = re.search(r'"""\s*(.*?)\s*"""', prompt, re.DOTALL)
    if match:
        content = match.group(1)
        return content != submitted_text
    else:
        raise ValueError("No content found between triple quotes.")

def for_file(path):
    data = gunzip_json(path)
    if data is None:
        return None

    changed = check_changed(data)
        
    n = len(data["results"])
    c = len([True for r in data["results"] if r["status"]
            == "OK" and r["exit_code"] == 0])
    __index_level_0__ = data["__index_level_0__"]
    return {
        "__index_level_0__":__index_level_0__,
        "changed":changed,
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
    parser.add_argument(
        "dirs", type=str,  help="Directories with results. ", nargs="+")
    args = parser.parse_args()
    
    orig_results = [for_file(p) for p in itertools.chain(
            Path(args.orig_dir).glob("*.results.json"), Path(args.orig_dir).glob("*.results.json.gz"))]
    orig_results = [r for r in orig_results if r is not None]
    
    if not args.suppress_header:
        print("Dataset,Original_Pass@1,Updated_Pass@1,Original_Pass@1_Changed,Updated_Pass@1_Changed,NumProblems_Changed,Delta_Pass@1_Changed")
    for d in args.dirs:
        name = d.split("/")[-2] if d.split("/")[-1] != "" else d.split("/")[-3]
        results = [for_file(p) for p in itertools.chain(
            Path(d).glob("*.results.json"), Path(d).glob("*.results.json.gz"))]
        results = {r["__index_level_0__"]: r for r in results if r is not None}
        results = list(results.values())
        indices = [r["__index_level_0__"] for r in results]
        filtered_orig_results = [r for r in orig_results if r["__index_level_0__"] in indices]
        num_problems = len(results)
        assert len(filtered_orig_results) == num_problems
        pass_1_original = np.mean([r["pass@1"] for r in filtered_orig_results])
        pass_1_updated = np.mean([r["pass@1"] for r in results])

        changed_results = {r["__index_level_0__"]:r for r in results if r["changed"]}
        changed_results = list(changed_results.values())
        changed_indices = [r["__index_level_0__"] for r in changed_results]
        filtered_orig_results_changed = [r for r in orig_results if r["__index_level_0__"] in changed_indices]
        num_problems_changed = len(changed_results)
        assert len(filtered_orig_results_changed) == num_problems_changed
        pass_1_original_changed = np.mean([r["pass@1"] for r in filtered_orig_results_changed])
        pass_1_updated_changed = np.mean([r["pass@1"] for r in changed_results])
        delta_changed = pass_1_updated_changed - pass_1_original_changed
        print(
            f"{name},{pass_1_original:.4f},{pass_1_updated:.4f},{num_problems},{pass_1_original_changed:.4f},{pass_1_updated_changed:.4f},{num_problems_changed},{delta_changed:.4f}")

if __name__ == "__main__":
    main()
