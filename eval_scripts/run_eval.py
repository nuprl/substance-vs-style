"""
Heavily inspired by bigcode_evaluation_harness.
Evaluate studenteval completions from a dataset with the following columns.
This dataset can be generated using batched_lm_generation.vllm_base.
[Can also handle a dataset in the original wellesley-easel/StudentEval format]

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
2. runs every completion and records `is_success, is_first_success, is_first_failure, is_last success, 
is_last_failure, tests_passed, stderr, stdout`
3. Creates a dataset with 2 splits:
    test - for each problem, stores the first completion (simulates 1 completion)
    all_completions - the eval results of all completions (for computing pass@k - if all_completions split is passed)
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
import re
from functools import partial
EXECUTION_TIMEOUT = 15

def remove_prints(prompt):
    return re.sub(r"print\(.*?\n","\n", prompt + "\n").strip()

def crop_to_return_stmt(func):
    """
    Need to account for multiple return statements.
    Split by lines. Traverse in reverse until return keyword is found. Return
    all following lines.
    """
    rev_lines = func.split("\n")[::-1]
    for i,line in enumerate(rev_lines):
        if re.search(r"^\s*?return .*?$", line) != None:
            return "\n".join(rev_lines[i:][::-1])
    return func

def remove_columns(ds, columns):
    for col in columns:
        if col in ds.column_names:
            ds = ds.remove_columns(col)
    return ds

def generate_splits(ds):
    if "completion_id" in ds.column_names:
        # filter all completions but compltion 0 (simulates n=1 completions)
        filtered_ds = ds.filter(lambda x: x["completion_id"] == 0, num_proc=cpu_count())
        new_ds = datasets.DatasetDict({
            "test": filtered_ds,
            "all_completions": ds
        })
    else:
        new_ds = datasets.DatasetDict({
            "test": ds
        })

    for split_name in new_ds.keys():
        new_ds[split_name] = remove_columns(new_ds[split_name], ["_id","Unnamed: 0"])
    return new_ds
    
def run_problem(ex: dict) -> dict:
    """
    Runs each assertion for a prompt separately. Collects num tests passed.
    Runs each print statement separately. Collects stdout and stderr
    """
    tests_passed = 0
    tests = ["assert "+ a for a in ex["assertions"].split("assert ") if a != ""]
    assert len(tests) == ex["total_tests"]
    
    for idx,test in enumerate(tests):
        assert ex["prompt"] not in ex["completion"]
        completion = ex["completion"]
        prompt = ex["prompt"].strip() + "\n    " + completion + "\n"+ test
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", prefix=f"{ex['_id']}_{idx}") as f:
            f.write(prompt)
            f.flush()
            try:
                result = subprocess.run(
                    ["python3", f.name],
                    timeout=EXECUTION_TIMEOUT,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                exit_code = 1
        
        if exit_code == 0:
            tests_passed += 1
    
    prints = ["print(" + p for p in ex["prints"].split("print(") if p != ""]
    all_stdouts,all_stderrs = [],[]
    for idx,print_stmt in enumerate(prints):
        # remove in-function prints
        #   - this is to reduce number of print clusters in graph experiment 
        completion = remove_prints(ex["completion"])
        prompt = ex["prompt"].strip() + "\n    " + completion + "\n"+ print_stmt
        
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
                all_stdouts.append(stdout)
                stderr = result.stderr
                if stderr is not None:
                    stderr = stderr.decode("utf-8")
                all_stderrs.append(stderr)
                
            except subprocess.TimeoutExpired:
                pass
            
    
    assert tests_passed <= ex["total_tests"]
    is_success = bool(tests_passed == ex["total_tests"])

    return {**ex, 
            "is_success": is_success, 
            "tests_passed": tests_passed,
            "stderr": all_stderrs,"stdout": all_stdouts,
            "is_first_failure": ex["first_attempt"] and not is_success, 
            "is_first_success": ex["first_attempt"] and is_success, 
            "is_last_failure": ex["last_attempt"] and not is_success,
            "is_last_success": ex["last_attempt"] and is_success,
            }

def flatten(x, i):
    extras = x.pop("extras", None)
    if extras:
        x = {**extras, **x}
    return {**x, "_id": i}

def run_problem_wrapper(ex, problems):
    if problems == None:
        return run_problem(ex)
    else:
        if ex["problem"] in problems:
            return run_problem(ex)
        else:
            return None
        
def main(args):
    from utils import load
    datasets.disable_caching()
    ds = load(args.dataset, args.split)
    ds = ds.map(flatten, desc="Flattening", with_indices=True)

    with ThreadPoolExecutor(max_workers=cpu_count() - 1) as executor:
        res = list(tqdm(executor.map(
                        partial(run_problem_wrapper, problems=args.problem), ds), 
                    total=len(ds)))
        if args.problem:
            res = [r for r in res if r != None]
        ds = datasets.Dataset.from_list(res)
    
    # create splits
    ds = generate_splits(ds)
    ds.save_to_disk(args.outdataset)
    
    # print some info
    print(ds)
    for split_name, split in ds.items():
        print(split_name, split.info)
        # success rate
        print(f"{split_name} split success rate:", split.to_pandas()["is_success"].mean())
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outdataset")
    parser.add_argument("--split", type=str, default=None)
    parser.add_argument("--problem", nargs="+", default=None, help="Only run certain problems. For debugging purposes.")
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
        "prints": '',
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
    
def test_run_problem2():
    ex = {
        'problem': 'remove_odd', 
        'entrypoint': 'remove_odd', 
        'assertions': 'assert remove_odd([4.3, 4, 5, 2, 7]) == [4.3, 4, 2]\nassert remove_odd([1.1, 2.2, 3.3]) == [1.1, 2.2, 3.3]\nassert remove_odd([3, 5, 7]) == []', 
        'prints': 'print(remove_odd([4.3, 4, 5, 2, 7]))\nprint(remove_odd([1.1, 2.2, 3.3]))\nprint(remove_odd([3, 5, 7]))', 
        'username': 'student18', 
        'tests_passed': 0, 
        'total_tests': 3, 
        'prompt': 'def remove_odd(lst):\n    """\n    Create a list. Only add either a even number or a decimal to the list from the lst. Then, return the list.\n    """\n    ', 
        'completion': '''
        new_list = []
        for i in lst:
            if i % 2 == 0 or type(i) == float:
                new_list.append(i)
        return new_list
        
        print(remove_odd([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
        print(remove_odd([1, 2, 3, 4, 5, 6, 7, 8, 9,''', 
        'first_attempt': False,
        'last_attempt': True,
        'is_success': False,
        'is_first_success': False,
        'is_last_success': False,
        'is_first_failure': False,
        'is_last_failure': True,
        '__index_level_0__': 323,
        "_id":0}
    
    res = run_problem(ex)
    assert res["is_success"] == False
    assert res["tests_passed"] == 0
    
def test_remove_prints():
    prompt = '''
    def generate_splits(ds):
    if "completion_id" in ds.column_names:
        # filter all completions but compltion 0 (simulates n=1 completions)
        filtered_ds = ds.filter(lambda x: x["completion_id"] == 0, num_proc=cpu_count())
        new_ds = datasets.DatasetDict({
            "test": filtered_ds,
            "all_completions": ds
        })
        print(f'When {n}', 1, {"hiudhf()"})
    else:
        new_ds = datasets.DatasetDict({
            "test": ds
        })
        print(set('hi'))
    '''
    gold = '''
    def generate_splits(ds):
    if "completion_id" in ds.column_names:
        # filter all completions but compltion 0 (simulates n=1 completions)
        filtered_ds = ds.filter(lambda x: x["completion_id"] == 0, num_proc=cpu_count())
        new_ds = datasets.DatasetDict({
            "test": filtered_ds,
            "all_completions": ds
        })
        
    else:
        new_ds = datasets.DatasetDict({
            "test": ds
        })
    '''.strip()
    output = remove_prints(prompt).strip()
    print(output, gold)
    assert output == gold, output
    prompt = '''
    new_string = ""
    for i in range(len(s)):
        if i % 2 == 0:
            new_string += s[i].upper()
        else:
            new_string += s[i].lower()
    return new_string

print(altText("computers"))
print(altText("T"))
'''
    gold = '''
    new_string = ""
    for i in range(len(s)):
        if i % 2 == 0:
            new_string += s[i].upper()
        else:
            new_string += s[i].lower()
    return new_string
'''.strip()
    output = remove_prints(prompt)
    print(output)
    assert output.strip() == gold, output
    
def test_crop_to_return_stmt():
    func = '''
    def complex_function(x, y):
        if x > y:
            return "x is greater than y"
        elif x < y:
            return "x is less than y"
        else:
            return "x is equal to y"

        for i in range(10):
            if i % 2 == 0:
                return f"{i} is even"
            else:
                return f"{i} is odd"

        while x > 0:
            x -= 1
            if x == 5:
                return "x is now 5"
            elif x == 0:
                return "x is now 0"

        try:
            result = x / y
            return result
        except ZeroDivisionError:
            return "Cannot divide by zero"

        return "End of function"
        
    print("Hello, return world!")
    print(f"The value of x is: {x}")
    print("This is a test message.")
    print("Debugging: variable y =", y)
    print("Processing complete.")
    print("Error: Invalid input detected.")
    print("The result is:", result)
    print("Starting the loop...")
    print("Current iteration:", i)
    '''
    gold = '''
    def complex_function(x, y):
        if x > y:
            return "x is greater than y"
        elif x < y:
            return "x is less than y"
        else:
            return "x is equal to y"

        for i in range(10):
            if i % 2 == 0:
                return f"{i} is even"
            else:
                return f"{i} is odd"

        while x > 0:
            x -= 1
            if x == 5:
                return "x is now 5"
            elif x == 0:
                return "x is now 0"

        try:
            result = x / y
            return result
        except ZeroDivisionError:
            return "Cannot divide by zero"

        return "End of function"
    '''.strip()
    output = crop_to_return_stmt(func).strip()
    print(output)
    assert output == gold, output