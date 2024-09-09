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

def run_problem(ex):
    tests_passed = 0
    tests = ["assert "+ a for a in ex["assertions"].split("assert ") if a != ""]
    assert len(tests) == ex["total_tests"], f'{ex["assertions"]}, {ex["total_tests"]}'
    
    for test in tests:
        prompt = "'''" + "\n".join([ex["prompt"], "\t".join(ex["completion"].split("\n")), test]) + "'''"
        output = subprocess.run(
            ["python", "-c", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if not "error" in output.stderr.decode("utf-8").lower():
            tests_passed += 1
    assert tests_passed <= len(tests)
    return {"is_success": tests_passed == len(tests), "tests_passed": tests_passed}

def main(args):
    ds = datasets.load_from_disk(args.dataset)
    ds = ds.map(lambda x: {"completion_id": x["completion_id"], "temperature": x["temperature"],
                           **x["extras"]}, desc="Flattening")
    print(ds)
    ds = ds.map(lambda x: {**x, **run_problem(x)}, desc="Evaluating", num_proc=cpu_count())
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