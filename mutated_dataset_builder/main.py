import datasets
from pathlib import Path
import json
import argparse


def rule_array_to_list(prompt: str) -> str:
    """
    Replace all instances of "array" with a list.

    (This is just a demo.)
    """
    return prompt.replace("array", "list")

def rule_replace_print_with_return(prompt: str) -> str:
    """
    Replace all instances of "print" with "return".
    """
    return prompt.replace("print", "return")

RULES = {
    "array_to_list": rule_array_to_list,
    "replace_print_with_return": rule_replace_print_with_return,
}

def main_with_args(original_dataset: str, output_path: Path):
    original_dataset = datasets.load_dataset(original_dataset, split="only_subsets")
    new_dataset = [ ]
    # also add the original dataset to the new dataset
    for item in original_dataset:
        new_dataset.append({ **item, "rule": "original", "original_prompt": item["prompt"] })

    for rule_name, rule_function in RULES.items():
        for item in original_dataset:

            new_prompt = rule_function(item["prompt"])
            if new_prompt != item["prompt"]:
                new_dataset.append({ **item, "rule": rule_name, "prompt": new_prompt, "original_prompt": item["prompt"] })
    with output_path.open("w") as f:
        for item in new_dataset:
            f.write(json.dumps(item) + "\n")
    print(f"Saved {len(new_dataset)} items to {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_dataset", type=str, default="wellesley-easel/StudentEval")
    parser.add_argument("--output_path", type=Path, default=Path("mutated_dataset.jsonl"))
    args = parser.parse_args()
    main_with_args(args.original_dataset, args.output_path)

if __name__ == "__main__":
    main()