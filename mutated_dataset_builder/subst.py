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

# Key is the input format of the replacement word. Values are what we wish the replacement words could look like.
# This is much faster than spacy
WORDS_V = {
    "word":["word","words"],
    "phrase":["phrase","phrases"],
    "string":["string","strings"],
    "character":["character","characters"],
    "set of characters":["set of characters","sets of characters"],
    "brackets":["brackets"],
    "set of brackets":["set of brackets","sets of brackets"],
    "set":["set","sets"],
    "list":["list","lists"],
    "array":["array","arrays"],
    "array list":["array list","array lists"],
    "map":["map","maps"],
    "dictionary":["dictionary","dictionaries"],
    "integer":["integer","integers"],
    "whole number":["whole number","whole numbers"],
    "int":["int","ints"],
    "output":["output","outputs","outputted","outputting"],
    "return":["return","returns","returned","returning"],
    "print":["print","prints","printed","printing"],
    "produce":["produce","produces","produced","producing"],
    "display":["display","displays","displayed","displaying"],
    "parameter":["parameter","parameters"],
    "argument":["argument","arguments"],
    "value provided":["value provided","values provided"],
    "input":["input","inputs","inputted"],
    "take":["take","takes"],
    "bring in":["bring in","brings in"],
    "accept":["accept","accepts"],
    "get":["get","gets"],
    "provide":["provide","provides","provided"],
    "enter":["enter","enters","entered"],
    "combine":["combine","combines","combined","combining"],
    "splice":["splice","splices","spliced","splicing"],
    "concatenate":["concatenate","concatenates","concatenated","concatenating"],
    "add":["add","adds","added","adding"],
    "insert":["insert","inserts","inserted","inserting"],
    "attach":["attach","attaches","attached","attaching"],
    "append":["append","appends","appended","appending"],
    "go through":["go through","goes through"],
    "run through":["run through","runs through"],
    "iterate through":["iterate through","iterates through"],
    "loop through":["loop through","loops through"],
    "run a for loop through":["run a for loop through","runs a for loop through"],
    "look through":["look through","looks through"],
    "execute a for loop with":["execute a for loop with","executes a for loop with"],
    "skip":["skip","skips","skipped","skipping"],
    "avoid":["avoid","avoids","avoided","avoiding"],
    "neglect":["neglect","neglects","neglected","neglecting"],
    "ignore":["ignore","ignores","ignored","ignoring"],
    "remove":["remove","removes","removed","removing"],
    "convert":["convert","converts","converted","converting"],
    "change":["change","changes","changed","changing"],
    "typecast":["typecast","typecasts","typecasted","typecasting"],
    "type cast":["type cast","type casts","type casted","type casting"],
    "cast":["cast","casts","casted","casting"],
    "key":["key","keys"],
    "item":["item","items"],
    "entry":["entry","entries"],
    "attribute":["attribute","attributes"],
    "part":["part","parts"],
    "element":["element","elements"],
    "variable":["variable","variables"],
}

# Same pairs exist in WORDS_V. Separating them to gaurd against wrong --category input.
CATEGORIES_V = {
    "string": ["string", "strings"],
    "list": ["list", "lists"],
    "dictionary": ["dictionary", "dictionaries"],
    "integer": ["integer", "integers"],
    "return": ["return", "returns", "returned", "returning"],
    "parameter": ["parameter", "parameters"],
    "take": ["take", "takes"],
    "provide": ["provide", "provides", "provided"],
    "concatenate": ["concatenate", "concatenates", "concatenated", "concatenating"],
    "insert": ["insert", "inserts", "inserted", "inserting"],
    "loop through": ["loop through", "loops through"],
    "skip": ["skip", "skips", "skipped", "skipping"],
    "typecast": ["typecast", "typecasts", "typecasted", "typecasting"],
    "key": ["key", "keys"]
}


def get_word_variation(word: str, category: str):
    word_variations = WORDS_V[word]
    replace = ""
    for key, value in TAGS.items():
        if isinstance(value, list):
            if category.lower() in value and key in word_variations:
                replace = key
                break
        elif isinstance(value, str):
            if value == category.lower() and key in word_variations:
                replace = key
                break
    #if original category:original is capitalized, capitalize the replacement
    if category.istitle():
        replace=replace.capitalize()
    if replace == "":
        raise ValueError(f"Could not find a word variation for '{word}' in category '{category}'")
    return replace

def substitute_prompt(prompt: str, category: str, value: str):
    # Check if the category exists in TYPES
    if category not in CATEGORIES_V:
        raise ValueError(f"Category '{category}' not found in TYPES.")
    #get all the possible categories by doing TYPES[category]
    category_variations = CATEGORIES_V[category]

    # Regex pattern to match $CATEGORY:ORIGINAL$
    # pattern = re.compile(r"\$(\w+):([\w\s]+)\$")
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
    results = [ ]
    for item in original_dataset:
        prompt = item['prompt']
        substituted_prompt, changed, original= substitute_prompt(prompt, category, value)
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