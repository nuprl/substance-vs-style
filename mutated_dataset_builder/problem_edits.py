from pathlib import Path
from functools import partial
from multiprocessing import cpu_count
import json
from datasets import load_dataset, load_from_disk, DatasetDict
from typing import Optional
import re
import argparse
import os
from utils import load

def exclude_processed(pattern):
    return fr"(?<!\$\$[^$]){pattern}(?![^$]*\$\$)"

def append_to_end(prompt, sent):
    prompt = prompt.rsplit("\n    \"\"\"", 1)
    return prompt[0] + sent + "\n    \"\"\""

def subtract_add_edit1(prompt):
    prompt = re.sub("list of integers", "$$list of integers:list of integers as strings$$", prompt)
    prompt = re.sub("list of numbers", "$$list of numbers:list of integers as strings$$", prompt)
    return append_to_end(prompt, "Use 1-indexing.")

def add_up_edit1(prompt):
    """
    Replace list or array with "list of lists" or "array of arrays"
    """
    if any(t in prompt for t in ["internal","inner","within"]):
        return prompt
    
    prompt = prompt.replace("brackets", "list")
    prompt = prompt.replace("arrangement", "list")
    prompt = prompt.replace("sequence", "list")
    
    for arr in ["list", "array"]:
        for num in ["int","str","float","number", "item"]:
            prompt = re.sub(exclude_processed(f" {arr} of {num}"), f"$$ {arr} of {num}: {arr} of {arr}s of {num}$$", prompt, count=1)
            prompt = re.sub(exclude_processed(f" {arr} and "), f"$$ {arr} and : {arr} of {arr}s and $$", prompt, count=1)
            prompt = re.sub(exclude_processed(f" {arr} *?\."), f"$$ {arr}.: {arr} of {arr}.$$", prompt, count=1)
            prompt = re.sub(exclude_processed(f" {arr} *?,"), f"$$ {arr},: {arr} of {arr},$$", prompt, count=1)
            prompt = re.sub(exclude_processed(f" {arr} *?\n"), f"$$ {arr}: {arr} of {arr}s$$\n", prompt, count=1)
    return prompt

def add_up_edit2(prompt):
    """
    Replace integer/number with integer and float
    """
    if "float" in prompt:
        if not "integer" in prompt:
            prompt = prompt.replace(exclude_processed("float"), "$$float:integer and float$$")
        return prompt

    prompt = re.sub("integer", "$$integer:integer and float$$", prompt)
    prompt = re.sub("number", "$$number:integer and float$$", prompt)
    return prompt

def convert_edit1(prompt):
    prompt = prompt.replace("comma","string break")
    prompt = append_to_end(prompt, " Capitalize all strings in output.")
    return prompt

SUBST_TEMPLATE = {
    "add_up": [
        add_up_edit1,
        add_up_edit2
    ],
    "subtract_add": [
        subtract_add_edit1
    ],
    "convert":[
        convert_edit1
    ]
}

def apply_subst(item: dict, subst : Optional[dict]):
    if subst:
        all_subst = subst[item["problem"]]
        for subst_fn in all_subst:
            item["prompt"] = subst_fn(item["prompt"])
    return item

def main(args):
    ds = load(args.dataset, args.split)
    ds = ds.filter(lambda x: (x["first_attempt"] or x["last_attempt"]) and not x["is_success"], num_proc=cpu_count()-1)
    subst = args.subst
    if isinstance(subst, str) and os.path.exists(Path(subst)):
        with open(subst, "r") as fp:
            subst = json.load(fp)
    ds = ds.filter(lambda x: x["problem"] in subst.keys(), num_proc=cpu_count()-1)
    ds = ds.map(lambda x: apply_subst(x, subst=subst), num_proc=cpu_count()-1)
    ds = DatasetDict({
        args.split : ds
    })
    print(ds)
    ds.save_to_disk(args.outdir)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("outdir")
    parser.add_argument("--split", default="test")
    parser.add_argument("--subst", help="path to json file describing substitutions", default=SUBST_TEMPLATE)
    args = parser.parse_args()
    main(args)