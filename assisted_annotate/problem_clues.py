import argparse
import datasets
from pathlib import Path
from prl_ml.yaml import save_yaml

DATASET_NAME = "wellesley-easel/StudentEval"


def download_studenteval_success_prompts(yaml_path: Path):
    prompts = datasets.load_dataset(DATASET_NAME, split="test")
    prompts = prompts.filter(lambda item: item["is_success"])
    # Group prompts by problem
    grouped_prompts = {}
    for item in prompts:
        problem_name = item["problem"]
        if problem_name not in grouped_prompts:
            grouped_prompts[problem_name] = []
        prompt = item["prompt"].strip()
        grouped_prompts[problem_name].append(f"```\n{prompt}\n```")
    
    # Format each problem group
    formatted_prompts = []
    for problem_name, prompts_list in grouped_prompts.items():
        formatted_prompts.append({
            "problem_name": problem_name,
            "prompts": "\n\n".join(prompts_list)
        })
    
    save_yaml(yaml_path, formatted_prompts)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download StudentEval success prompts")
    download_parser.add_argument("YAML_PATH", type=Path, help="Path to save the YAML file")

    args = parser.parse_args()

    match args.command:
        case "download":
            download_studenteval_success_prompts(args.YAML_PATH)
        case _:
            raise ValueError(f"Invalid command: {args.command}")

if __name__ == "__main__":
    main()
