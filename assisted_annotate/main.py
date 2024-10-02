from pathlib import Path
import prl_ml.yaml as yaml
import openai
from tqdm.auto import tqdm
from typing import List, Dict, TypedDict, Union, Any, Literal
import os
import argparse
import sys

class Message(TypedDict):
    role: Union[Literal["system"], Literal["user"], Literal["assistant"]]
    content: str

Conversation = List[Message]


def subst_prompt_template(prompt_template: Conversation, data: dict) -> Conversation:
    """
    Substitute the keys in the prompt template with the values in the data. This
    is straightforward since the template must be in conversation format, and is
    not a free-form YAML file.
    """
    result = [ ]
    for message in prompt_template:
        new_content = message["content"]
        for key, value in data.items():
            new_content = new_content.replace(f"${key}", str(value))
        result.append({ "role": message["role"], "content": new_content })
    return result

VALID_STATUSES = [ "pending", "rejected", "generated", "modified", "accepted" ]

def main_with_args(yaml_path: Path, prompt_template_yaml_path: Path):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt_template = yaml.load_yaml(prompt_template_yaml_path)
    data = yaml.load_yaml(yaml_path)

    for item in data:
        if item.get("_status", "pending") not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {item.get('_status', 'pending')}")

    count = sum(1 for item in data if item.get("_status", "pending") in [ "pending", "rejected" ])

    with tqdm(total=count) as pbar:
        for item in data:
            current_status = item.get("_status", "pending")
            if current_status in [ "generated", "modified", "accepted" ]:
                continue
            conversation = subst_prompt_template(prompt_template, item)
            response = client.chat.completions.create(model="gpt-4o", messages=conversation)
            item["_response"] = response.choices[0].message.content
            item["_status"] = "generated"
            yaml.save_yaml(yaml_path, data)
            pbar.update(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--prompt-template", required=True, type=Path)
    args = parser.parse_args()
    main_with_args(args.data, args.prompt_template)


if __name__ == "__main__":
    main()
