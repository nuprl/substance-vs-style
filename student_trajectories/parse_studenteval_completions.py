import argparse
import json
import gzip
import re
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import datasets
import os
STUDENTEVAL = datasets.load_dataset("wellesley-easel/StudentEval",token=os.environ.get("HF_TOKEN",None))["test"]

def parse_generated(model:str, generated: str, prompt: str) -> str:
    """
    Parse the generated code from first completion, remove the prompt
    """
    # gpt often uses md format for coding
    if "gpt4o-mini" in model.as_posix():
        assert "```python" in generated
        generated = re.search(r"```python([\S\s]+?)```", generated).group(1)
        func_sig = prompt.split('"""')[0].strip()
        generated = re.sub(r'{func}\s+\"\"\"[\s\S]+\"\"\"'.format(func=re.escape(func_sig)),"", generated).strip()

    # remove prompt
    generated = generated.replace(prompt.strip(),'')
    return generated.strip()

def parse_print_stmt(assertions: str) -> str:
    """
    Turn assertions into prints
    """
    prints = ""
    for assert_stmt in assertions.split("assert"):
        if len(assert_stmt.strip()) > 0:
            assert "==" in assert_stmt
            prints += f"print({assert_stmt.split('==')[0].strip()})\n"
    return prints

def get_username(problem: str, index: str) -> str:
    """
    Given a problem and index, fetch the username from the original Studenteval
    """
    df = STUDENTEVAL.to_pandas()
    df = df.loc[df["__index_level_0__"] == index]
    assert len(df) == 1
    df = df.to_dict(orient="records")[0]
    assert df["problem"] == problem
    return df["username"]

def get_attempt_order(username:str, problem:str, idx:str) -> dict:
    """
    Given an entry with username, problem, __index_level_0__ find
    the corresponding field last attempt/first attempt in original
    wellesley/studenteval. return:
    {last_attempt: T/F, first_attempt: T/F}
    """
    df = STUDENTEVAL.to_pandas()
    df = df.loc[df["__index_level_0__"] == idx]
    assert len(df) == 1
    df = df.to_dict(orient="records")[0]
    assert df["username"] == username
    assert df["problem"] == problem
    return {"last_attempt": df["last_attempt"], "first_attempt": df["first_attempt"]}


def main(model:Path, output:Path):
    """
    Completions structure:
    { 'prompt': '', 'temperature': 0.0, 'completions': [''], 'top_p': 0.0, 'max_tokens'0,
    'extras': {
        '__index_level_0__':0,
        'problem': '',
        'entrypoint': '',
        'assertions': '',
        'username': '',
        'submitted_text': '',
        'prompt': ''
    }}
    """
    completions = []
    # load completions
    for item in tqdm(model.glob("*.json.gz"), desc="Parsing studenteval items"):
        with gzip.open(item, "r") as fp:
            comp = json.load(fp)
            extras = comp.pop("extras")
            if extras.get("tests",None):
                extras["assertions"] = extras["tests"]
            extras["assertions"] = extras["assertions"].strip()
            extras["total_tests"] = extras["assertions"].count("assert ")
            comp = {**comp, **extras}

            if not comp.get("username",None):
                comp["username"] = get_username(comp["problem"], comp["__index_level_0__"])
            attempt_dict = get_attempt_order(comp["username"],comp["problem"], comp["__index_level_0__"])
            generated = parse_generated(model, comp.pop("completions")[0]["text"], comp["prompt"])
            comp["prints"] = parse_print_stmt(comp["assertions"])
            completions.append({**comp, **attempt_dict, "completion":generated})

    pd.DataFrame(completions).to_csv(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=["gpt4o-mini","llama3p1_8b_base", "llama3p1_70b_base"])
    parser.add_argument("output", type=Path)
    RESULT_DIR="/work/arjunguha-research-group/projects/prompt_trajectories/causal_intervention/{model}/studenteval/completions_jsons/"
    args = parser.parse_args()
    main(Path(RESULT_DIR.format(model=args.model)), args.output)