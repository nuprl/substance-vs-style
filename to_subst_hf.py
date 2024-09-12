import sys
from utils import load
import pandas as pd
from datasets import DatasetDict, Dataset
import re

df_subst = pd.read_csv(sys.argv[1])
outds = sys.argv[2]

def apply_subst(prompt):
    matches = re.search(r"\$\$.*?\:(.*?)\$\$", prompt)
    while matches:
        for group in matches.groups():
            prompt = re.sub(fr"\$\$.*?\:{group}\$\$", str(group), prompt, count=1)
        matches = re.search(r"\$\$.*?\:(.*?)\$\$", prompt)
    if "$$" in prompt:
        raise ValueError(f"Delim found {prompt}")
    return prompt

ds = Dataset.from_pandas(df_subst)
old_ds = ds
ds = ds.map(lambda x: {**x, "prompt":apply_subst(x["prompt"])})

ds = DatasetDict({
    "test": ds
})
ds.save_to_disk(outds)