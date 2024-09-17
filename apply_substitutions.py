import sys
from utils import load
import pandas as pd
from datasets import DatasetDict, Dataset
import re
from pathlib import Path
import yaml

SUBST_PATTERN = (r"\$(.*?)\:.*?\$", r"\${group}\:.*?\$")

def read_data(data: Path):
    if data.endswith(".csv"):
        return pd.read_csv(data)
    elif data.endswith(".yaml"):
        with open(data, "r") as fp:
            data_str = fp.read()
        problems = ["problem: "+ex for ex in data_str.split("problem: ") if len(ex) > 0]
        new_data = []
        for ex in problems:
            new_data.append(yaml.safe_load(ex))
        return pd.DataFrame(new_data)
    else:
        raise NotImplementedError(f"Format not supported {data}")        

def apply_subst(prompt, subst_pattern = SUBST_PATTERN, delim = "$"):
    matches = re.search(subst_pattern[0], prompt)
    while matches:
        for group in matches.groups():
            prompt = re.sub(subst_pattern[1].format(group=group), str(group), prompt, count=1)
        matches = re.search(subst_pattern[0], prompt)
    if delim in prompt:
        raise ValueError(f"Delim found {prompt}")
    return prompt

df_subst = read_data(sys.argv[1])
print(df_subst)
outds = sys.argv[2]
ds = Dataset.from_pandas(df_subst).map(lambda x: {**x, "prompt":apply_subst(x["prompt"])})
print(ds[0])
ds = DatasetDict({
    "test": ds
})
ds.save_to_disk(outds)