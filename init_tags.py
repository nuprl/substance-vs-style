import yaml
import sys
import pandas as pd
import re

def strip_newlines(data):
    if isinstance(data, dict):
        return {key: strip_newlines(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [strip_newlines(item) for item in data]
    elif isinstance(data, str):
        return re.sub(r'\n+', ' ', data).strip()  # Replace newlines with space
    return data

problems_yaml = sys.argv[1]
with open(problems_yaml, "r") as fp:
    problems = yaml.safe_load(fp)

targets = sys.argv[2]
targets = set(pd.read_csv(targets)["problem"])

outfile = sys.argv[3]

out = {}
for p, data in problems.items():
    if p in targets:
        data = {k:v for k,v in data.items()
                if k in ["tests","signature","working_description"]}
        data = {**data, "tags":""}
        out[p] = data
        
out = strip_newlines(out)
with open(outfile, "w") as fp:
    yaml.dump(out, fp)