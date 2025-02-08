import yaml
import sys
import pandas as pd
import re
"""
Script for creating a template for recording problem clues.
See problem_tags.yaml, which is a filled example of the template.

"""
def strip_newlines(data):
    if isinstance(data, dict):
        return {key: strip_newlines(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [strip_newlines(item) for item in data]
    elif isinstance(data, str):
        return re.sub(r'\n+', ' ', data).strip()  # Replace newlines with space
    return data

if __name__ == "__main__":
    problems_yaml = sys.argv[1] #problems.yaml
    targets = sys.argv[2] #target_problems.csv
    outfile = sys.argv[3] # problem_tags.yaml

    with open(problems_yaml, "r") as fp:
        problems = yaml.safe_load(fp)
    targets = set(pd.read_csv(targets)["problem"])

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