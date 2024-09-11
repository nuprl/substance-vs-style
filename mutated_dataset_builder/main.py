import datasets
from pathlib import Path
import spacy
import json
import argparse

# For each KEY:VALUE pair, when we see the word VALUE in the prompt, we tag it
# with KEY using tag_prompt.
TAGS = {
    "print": "return",
    "prints": "returns",

}

def tag_prompt(nlp: spacy.Language, prompt: str) -> str:
    """
    Given a prompt such as

    This function prints the word "Hello".

    This function will return the following string:

    This function $$returns:prints$$ the $$string:word$$ "Hello".

    Thus, all possible words that we may substitute are tagged with their category.

    This is *not* a dataset that we can feed to the model. But, we can edit the
    dataset manually to address cases where the rules go wrong. After inspection,
    we can apply substitutions.
    """
    doc = nlp(prompt)
    new_prompt = []
    for token in doc:
        lemma = token.lemma_
        if token.text in TAGS:
            new_prompt.append(f"${TAGS[token.text]}:{token.text}")
        else:
            new_prompt.append(token.text)
    return "".join(new_prompt)

def main_with_args(original_dataset: str, output_path: Path):
    nlp = spacy.load("en_core_web_trf")
    original_dataset = datasets.load_dataset(original_dataset, split="only_subsets")
    results = [ ]
    for item in original_dataset:
        original_prompt = item["prompt"]
        tagged_prompt = tag_prompt(nlp, original_prompt)
        results.append({ **item, "prompt": tagged_prompt })
    with output_path.open("w") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")
    print(f"Saved {len(results)} items to {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_dataset", type=str, default="wellesley-easel/StudentEval")
    parser.add_argument("--output_path", type=Path, default=Path("tagged_prompts.jsonl"))
    args = parser.parse_args()
    main_with_args(args.original_dataset, args.output_path)

if __name__ == "__main__":
    main()