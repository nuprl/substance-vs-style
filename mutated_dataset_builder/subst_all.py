"""
Substitution script
python3 subst.py –-category return --value output
This would replace all words in the “return” category with variations of “output”. So returns->outputs and returning->outputting, and so on. 
"""
import datasets
from pathlib import Path
import json
import argparse
import re
from main import TAGS

def substitute_prompt(prompt: str):
    # Regex pattern to match $CATEGORY:ORIGINAL$
    # pattern = re.compile(r"\$(\w+):([\w\s]+)\$")
    pattern = re.compile(r"\$([\w\s]+):([\w\s]+)\$")
    changed = False
    # Iterate over all matches in the example string
    for match in pattern.finditer(prompt):
        # Extract CATEGORY
        category = match.group(1)
        original = match.group(2)
        prompt = prompt.replace(match.group(0), category)
        changed = True
    return prompt, changed

def main_with_args(original_dataset: str, split:str, output_path: Path):
    original_dataset = datasets.load_dataset(original_dataset, split=split)
    results = [ ]
    for item in original_dataset:
        prompt = item['prompt']
        substituted_prompt, changed= substitute_prompt(prompt)
        item['prompt'] = substituted_prompt
        if changed:
            results.append(item)
        else: #Filter out prompts that do not have any tokens from the given category class–they are identical to the original.
            print(item["__index_level_0__"],"did not change")

    with output_path.open("w") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")
    print(f"Saved {len(results)} items to {output_path}")
    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_dataset", type=str, default="nuprl-staging/studenteval_tagged_prompts")
    parser.add_argument("--split", type=str,required=True)
    parser.add_argument("--output_path", type=Path, default=Path("subst_prompts_all_at_one.jsonl"))
    args = parser.parse_args()
    main_with_args(args.original_dataset,args.split, args.output_path)

if __name__ == "__main__":
    main()