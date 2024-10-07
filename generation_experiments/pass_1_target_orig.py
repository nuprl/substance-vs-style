import numpy as np
from pathlib import Path
import itertools
import argparse
import datasets
from pathlib import Path
import json
import gzip
from typing import Optional
import sys

subst_to_run = {
    "string": ["word","phrase","string","character","set of characters"],
    "list":["brackets","set of brackets","set","list","array list","array"],
    "dictionary":["map","dictionary"],
    "integer": ["integer","whole number","int"],
    "return": ["return","output","print","produce","display"],
    "parameter": ["parameter","argument","value provided","input"],
    "take": ["take","bring in","accept","get","input"],
    "provide": ["provide","enter","input"],
    "concatenate": ["concatenate","combine","splice","add"],
    "insert": ["insert","add","append","attach"],
    "loop through": ["go through","run through","iterate through","loop through","run a for loop through","look through","execute a for loop with"],
    "skip": ["skip","avoid","neglect","ignore","remove"],
    "typecast": ["typecast","type cast","cast","convert","change"],
    "key": ["key","item","entry","attribute","part","element","variable"],
}

WORDS_V = {
    "word":["word","words"],
    "phrase":["phrase","phrases"],
    "string":["string","strings"],
    "character":["character","characters"],
    "set of characters":["set of characters","sets of characters"],
    "brackets":["brackets"],
    "set of brackets":["set of brackets","sets of brackets"],
    "set":["set","sets"],
    "list":["list","lists"],
    "array":["array","arrays"],
    "array list":["array list","array lists"],
    "map":["map","maps"],
    "dictionary":["dictionary","dictionaries"],
    "integer":["integer","integers"],
    "whole number":["whole number","whole numbers"],
    "int":["int","ints"],
    "output":["output","outputs","outputted","outputting"],
    "return":["return","returns","returned","returning"],
    "print":["print","prints","printed","printing"],
    "produce":["produce","produces","produced","producing"],
    "display":["display","displays","displayed","displaying"],
    "parameter":["parameter","parameters"],
    "argument":["argument","arguments"],
    "value provided":["value provided","values provided"],
    "input":["input","inputs","inputted"],
    "take":["take","takes"],
    "bring in":["bring in","brings in"],
    "accept":["accept","accepts"],
    "get":["get","gets"],
    "provide":["provide","provides","provided"],
    "enter":["enter","enters","entered"],
    "combine":["combine","combines","combined","combining"],
    "splice":["splice","splices","spliced","splicing"],
    "concatenate":["concatenate","concatenates","concatenated","concatenating"],
    "add":["add","adds","added","adding"],
    "insert":["insert","inserts","inserted","inserting"],
    "attach":["attach","attaches","attached","attaching"],
    "append":["append","appends","appended","appending"],
    "go through":["go through","goes through"],
    "run through":["run through","runs through"],
    "iterate through":["iterate through","iterates through"],
    "loop through":["loop through","loops through"],
    "run a for loop through":["run a for loop through","runs a for loop through"],
    "look through":["look through","looks through"],
    "execute a for loop with":["execute a for loop with","executes a for loop with"],
    "skip":["skip","skips","skipped","skipping"],
    "avoid":["avoid","avoids","avoided","avoiding"],
    "neglect":["neglect","neglects","neglected","neglecting"],
    "ignore":["ignore","ignores","ignored","ignoring"],
    "remove":["remove","removes","removed","removing"],
    "convert":["convert","converts","converted","converting"],
    "change":["change","changes","changed","changing"],
    "typecast":["typecast","typecasts","typecasted","typecasting"],
    "type cast":["type cast","type casts","type casted","type casting"],
    "cast":["cast","casts","casted","casting"],
    "key":["key","keys"],
    "item":["item","items"],
    "entry":["entry","entries"],
    "attribute":["attribute","attributes"],
    "part":["part","parts"],
    "element":["element","elements"],
    "variable":["variable","variables"],
}

# Same pairs exist in WORDS_V. Separating them to gaurd against wrong --category input.
CATEGORIES_V = {
    "string": ["string", "strings"],
    "list": ["list", "lists"],
    "dictionary": ["dictionary", "dictionaries"],
    "integer": ["integer", "integers"],
    "return": ["return", "returns", "returned", "returning"],
    "parameter": ["parameter", "parameters"],
    "take": ["take", "takes"],
    "provide": ["provide", "provides", "provided"],
    "concatenate": ["concatenate", "concatenates", "concatenated", "concatenating"],
    "insert": ["insert", "inserts", "inserted", "inserting"],
    "loop through": ["loop through", "loops through"],
    "skip": ["skip", "skips", "skipped", "skipping"],
    "typecast": ["typecast", "typecasts", "typecasted", "typecasting"],
    "key": ["key", "keys"]
}


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

import re
#this checks change by directly comparing the prompt before and after the substitution
# def check_changed(data):
#     submitted_text = data['submitted_text'].strip().lstrip()
#     prompt = data['prompt']
#     match = re.search(r'"""\s*(.*?)\s*"""', prompt, re.DOTALL)
#     if match:
#         content = match.group(1).strip().lstrip()
#         return content != submitted_text
#     else:
#         raise ValueError("No content found between triple quotes.")

#if we want to know if a substitution between a specific original word and a specific replacement value happened and changed the prompt
def check_subst_pair(data,all_tagged_prompts,category,target_original,replacement):
    if target_original == replacement:
        return False
    tagged_prompt = [item for item in all_tagged_prompts if item['__index_level_0__'] == data['__index_level_0__']]
    assert len(tagged_prompt)==1
    tagged_prompt = tagged_prompt[0]
    pattern = re.compile(r"\$([\w\s]+):([\w\s]+)\$")
    is_subst_changed = False
    for match in pattern.finditer(tagged_prompt['prompt']):
        # Extract CATEGORY
        this_category = match.group(1)
        this_original = match.group(2)
        if this_category in CATEGORIES_V[category]:
            if this_original in WORDS_V[target_original]:
                # print("found original word tagged in",tagged_prompt['prompt'])
                is_subst_changed = True
    return is_subst_changed  
        

def check_success(data):
    subset = data['subset']
    success = 'success' in subset
    return success
    
    
def for_file(path,all_tagged_prompts,category,target_original,replacement):
    data = gunzip_json(path)
    if data is None:
        return None
    is_subst_changed = check_subst_pair(data,all_tagged_prompts,category,target_original,replacement)
    success = check_success(data)
        
    n = len(data["results"])
    c = len([True for r in data["results"] if r["status"]
            == "OK" and r["exit_code"] == 0])
    __index_level_0__ = data["__index_level_0__"]

    return {
        "__index_level_0__":__index_level_0__,
        "is_subst_changed":is_subst_changed,
        "success":success,
        "pass@1": estimator(n, c, 1),
        "pass@10": estimator(n, c, 10),
        "pass@100": estimator(n, c, 100),
        "n": n,
        "c": c,
        "temperature": data["temperature"] if "temperature" in data else 0.2
    }

    
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
    parser.add_argument(
        "dirs", type=str,  help="Directories with results. ", nargs="+")
    args = parser.parse_args()
    all_tagged_prompts = datasets.load_dataset("nuprl-staging/studenteval_tagged_prompts",split = "all.prompts.full.label.d2c1570")
    
    orig_results = [for_file_orig(p) for p in itertools.chain(
            Path(args.orig_dir).glob("*.results.json"), Path(args.orig_dir).glob("*.results.json.gz"))]
    orig_results = [r for r in orig_results if r is not None]
    
    if not args.suppress_header:
        print("Dataset,Target_Orig_Word,Original_Pass@1,Updated_Pass@1,NumProblems,Delta_Pass@1")
    for d in args.dirs:
        name = d.split("/")[-2] if d.split("/")[-1] != "" else d.split("/")[-3]
        suffix = name.split(".")[-1]
        if "loop_through" in suffix:
            category = "loop through"
            replacement = suffix.split("loop_through_")[-1].replace("_", " ").strip().lstrip()
        else:
            category = suffix.split("_")[1]
            replacement= suffix.split(category,1)[-1].replace("_", " ").strip().lstrip()
        # print(category,replacement)
        all_target_original = subst_to_run[category]
        for target_original in all_target_original:
            results = [for_file(p,all_tagged_prompts,category,target_original,replacement) for p in itertools.chain(
                Path(d).glob("*.results.json"), Path(d).glob("*.results.json.gz"))]
            changed_results = {r["__index_level_0__"]:r for r in results if r["is_subst_changed"] and r["success"]}
            changed_results = list(changed_results.values())
            changed_indices = [r["__index_level_0__"] for r in changed_results]
            filtered_orig_results_changed = [r for r in orig_results if r["__index_level_0__"] in changed_indices]
            num_problems_changed = len(changed_results)
            assert len(filtered_orig_results_changed) == num_problems_changed
            pass_1_original_changed = np.mean([r["pass@1"] for r in filtered_orig_results_changed]) if filtered_orig_results_changed else float('nan')
            pass_1_updated_changed = np.mean([r["pass@1"] for r in changed_results]) if changed_results else float('nan')

            delta_changed = pass_1_updated_changed - pass_1_original_changed
            print(
                f"{name},{target_original},{pass_1_original_changed:.4f},{pass_1_updated_changed:.4f},{num_problems_changed},{delta_changed:.4f}")
            
if __name__ == "__main__":
    main()