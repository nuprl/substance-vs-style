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

def build_CATEGORY_V(TAGS):
    CATEGORY_V = {}
    for word,variations in TAGS.items():
        if word == "input" or word == "add":
            continue
        category = variations[0]['category']
        if category not in CATEGORY_V:
            CATEGORY_V[category] = []
        for variation in variations:
            if variation['category'] not in CATEGORY_V[category]:
                CATEGORY_V[category].append(variation['category'])
    print(CATEGORY_V)
    return CATEGORY_V


def get_word_variation(word: str, category: str):
    replace = ""
    for base_word, variations in TAGS.items():
        if base_word == word:
            for variation in variations:
                # print("variation",variation)
                if variation['category'] == category.lower():
                    replace=variation['variant']
                    break
            if replace:
                break
                
    #if original category:original is capitalized, capitalize the replacement
    if category.istitle():
        replace=replace.capitalize()
    if replace == "":
        raise ValueError(f"Could not find a word variation for '{word}' in category '{category}'")
    return replace

def substitute_prompt(CATEGORY_V,prompt: str, category: str, value: str):
    if category not in CATEGORY_V.keys():
        raise ValueError(f"Category '{category}' not found in the given categories.")
    #get all the possible categories by doing TYPES[category]
    category_variations = CATEGORY_V[category]

    # Regex pattern to match $CATEGORY:ORIGINAL$
    pattern = re.compile(r"\$([\w\s]+):([\w\s]+)\$")
    
    changed = False
    changed_original = None
    # Iterate over all matches in the example string
    for match in pattern.finditer(prompt):
        # Extract CATEGORY
        category = match.group(1)
        original = match.group(2)
        if category.lower() in category_variations:
            #find out what variation of the value we need.
            actual_value = get_word_variation(value, category)
            # Replace the match with the new value
            prompt = prompt.replace(match.group(0), actual_value)
            changed_original = original
            changed = True
        else:#use the original for every tagged token that is not in the given category class.
            prompt = prompt.replace(match.group(0), original)
    return prompt, changed, changed_original

def main_with_args(original_dataset: str, split:str, output_path: Path,category: str, value: str):
    original_dataset = datasets.load_dataset(original_dataset, split=split)
    CATEGORY_V = build_CATEGORY_V(TAGS)
    results = [ ]
    for item in original_dataset:
        prompt = item['prompt']
        substituted_prompt, changed, original= substitute_prompt(CATEGORY_V,prompt, category, value)
        item['prompt'] = substituted_prompt
        item["original"] = original
        if changed:
            results.append(item)
        # else: #Filter out prompts that do not have any tokens from the given category class–they are identical to the original.
        #     print(f"Prompt {item[__index_level_0__]} did not contain any tokens from category {category}. Skipping.")

    with output_path.open("w") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")
    print(f"Saved {len(results)} items to {output_path}")
    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_dataset", type=str, default="nuprl-staging/studenteval_tagged_prompts")
    parser.add_argument("--split", type=str,required=True)
    parser.add_argument("--output_path", type=Path, default=Path("subst_prompts_insert_append.jsonl"))
    parser.add_argument("--category", type=str, default="insert")
    parser.add_argument("--value", type=str, default="append")
    args = parser.parse_args()
    main_with_args(args.original_dataset,args.split, args.output_path, args.category, args.value)

if __name__ == "__main__":
    main()