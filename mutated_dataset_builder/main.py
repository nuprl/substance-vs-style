import datasets
from pathlib import Path
import spacy
import json
import argparse
import re

# For each KEY:VALUE pair of TAGS, when we see the word KEY in the prompt, we tag it
# with VALUE using tag_prompt.
#See charlie_sysnonyms.csv
TAGS = {
    #string:
    "word": "string",
    "words": "strings",
    "phrase": "string",
    "phrases": "strings",
    "string": "string",
    "strings": "strings",
    "set of characters": "string",
    "sets of characters": "strings",
    "character": "string",
    "characters": "strings",
    #list:
    "brackets": ["list","lists"],
    "set of brackets": "list",
    "sets of brackets": "lists",
    "set": "list",
    "sets": "lists",
    "list": "list",
    "lists": "lists",
    "array": "list",
    "arrays": "lists",
    "array list": "list",
    "array lists": "lists",
    #dictionary:
    "map": "dictionary",
    "maps": "dictionaries",
    "dictionary": "dictionary",
    "dictionaries": "dictionaries",
    #integer:
    "integer": "integer",
    "integers": "integers",
    "whole number": "integer",
    "whole numbers": "integers",
    "int": "integer",
    "ints": "integers",
    #return
    "output": "return",
    "outputs": "returns",
    "outputted": "returned",
    "outputting": "returning",
    "return": "return",
    "returns": "returns",
    "returned": "returned",
    "returning": "returning",
    "print": "return",
    "prints": "returns", 
    "printed": "returned",
    "printing": "returning",
    "produce": "return",
    "produces": "returns",
    "produced": "returned",
    "producing": "returning",
    "display": "return",
    "displays": "returns",
    "displayed": "returned",
    "displaying": "returning",
    #parameter
    "parameter": "parameter",
    "parameters": "parameters",
    "argument": "parameter",
    "arguments": "parameters",
    "value provided": "parameter",
    "values provided": "parameters",
    "input": ["parameter","take","provide"],
    "inputs": ["parameters","takes","provides"],
    #takes
    "take": "take",
    "takes": "takes",
    "bring in": "take",
    "brings in": "takes",
    "accept": "take",
    "accepts": "takes",
    "get": "take",
    "gets": "takes",
    #provide
    "provide": "provide",
    "provides": "provides",
    "provided": "provided",
    "enter": "provide",
    "enters": "provides",
    "entered": "provided",
    "inputted": "provided",
    #concatenate
    "combine": "concatenate",
    "combines": "concatenates",
    "combined": "concatenated",
    "combining": "concatenating",
    "splice": "concatenate",
    "splices": "concatenates",
    "spliced": "concatenated",
    "splicing": "concatenating",
    "concatenate": "concatenate",
    "concatenates": "concatenates",
    "concatenated": "concatenated",
    "concatenating": "concatenating",
    "add": ["concatenate","insert"],
    "adds": ["concatenates","inserts"],
    "added": ["concatenated","inserted"],
    "adding": ["concatenating","inserting"],
    #insert
    "insert": "insert",
    "inserts": "inserts",
    "inserted": "inserted",
    "inserting": "inserting",
    "attach": "insert",
    "attaches": "inserts",
    "attached": "inserted",
    "attaching": "inserting",
    "append": "insert",
    "appends": "inserts",
    "appended": "inserted",
    "appending": "inserting",
    #loop
    "go through": "loop through",
    "goes through": "loops through",
    "run through": "loop through",
    "runs through": "loops through",
    "iterate through": "loop through",
    "iterates through": "loops through",
    "loop through": "loop through",
    "loops through": "loops through",
    "run a for loop through": "loop through",
    "runs a for loop through": "loops through",
    "look through": "loop through",
    "looks through": "loops through",
    "execute a for loop with": "loop through",
    "executes a for loop with": "loops through",
    #skip
    "skip": "skip",
    "skips": "skips",
    "skipped": "skipped",
    "skipping": "skipping",
    "avoid": "skip",
    "avoids": "skips",
    "avoided": "skipped",
    "avoiding": "skipping",
    "neglect": "skip",
    "neglects": "skips",
    "neglected": "skipped",
    "neglecting": "skipping",
    "ignore": "skip",
    "ignores": "skips",
    "ignored": "skipped",
    "ignoring": "skipping",
    "remove": "skip",
    "removes": "skips",
    "removed": "skipped",
    "removing": "skipping",
    #typecast
    "convert": "typecast",
    "converts": "typecasts",
    "converted": "typecasted",
    "converting": "typecasting",
    "cast": "typecast",
    "casts": "typecasts",
    "casted": "typecasted",
    "casting": "typecasting",
    "change": "typecast",
    "changes": "typecasts",
    "changed": "typecasted",
    "changing": "typecasting",
    "type cast": "typecast",
    "type casts": "typecasts",
    "type casted": "typecasted",
    "type casting": "typecasting",
    "cast": "typecast",
    "casts": "typecasts",
    "casted": "typecasted",
    "casting": "typecasting",
    "typecast": "typecast",
    "typecasts": "typecasts",
    "typecasted": "typecasted",
    "typecasting": "typecasting",
    #key
    "key": "key",
    "keys": "keys",
    "item": "key",
    "items": "keys",
    "entry": "key",
    "entries": "keys",
    "attribute": "key",
    "attributes": "keys",
    "part": "key",
    "parts": "keys",
    "element": "key",
    "elements": "keys",
    "variable": "key",
    "variables": "keys",
}

    
def tag_prompt(nlp: spacy.Language, prompt: str) -> str:
    """
    Given a prompt such as

    This function prints the word "Hello".

    This function will return the following string:

    This function $returns:prints$ the $string:word$ "Hello".
    (the form $CATEGORY:ORIGINAL$)

    Thus, all possible words that we may substitute are tagged with their category.

    This is *not* a dataset that we can feed to the model. But, we can edit the
    dataset manually to address cases where the rules go wrong. After inspection,
    we can apply substitutions.
    """
    doc = nlp(prompt)
    new_prompt = []
    last_end = 0
    i = 0
    
    while i < len(doc):
        if doc[i].idx > last_end:
            new_prompt.append(prompt[last_end:doc[i].idx])

        # Check for five-token phrases
        if i < len(doc) - 4:
            five_token_phrase = f"{doc[i].text} {doc[i+1].text} {doc[i+2].text} {doc[i+3].text} {doc[i+4].text}"
            if five_token_phrase in TAGS:
                new_prompt.append(f"${TAGS[five_token_phrase]}:{five_token_phrase}$")
                last_end = doc[i+4].idx + len(doc[i+4].text)
                i += 5
                continue
        # Check for two-token phrases
        if i < len(doc) - 1:
            two_token_phrase = f"{doc[i].text} {doc[i+1].text}"
            if two_token_phrase in TAGS:
                new_prompt.append(f"${TAGS[two_token_phrase]}:{two_token_phrase}$")
                last_end = doc[i+1].idx + len(doc[i+1].text)
                i += 2
                continue
        
        # Handle single-token categories
        token = doc[i]
        if token.text in TAGS:
            new_prompt.append(f"${TAGS[token.text]}:{token.text}$")
        elif token.text.lower() in TAGS:
            tag = TAGS[token.text.lower()]
            uppercasetag = tag[0].upper() + tag[1:]
            new_prompt.append(f"${uppercasetag}:{token.text}$")
        else:
            new_prompt.append(token.text)
        
        last_end = token.idx + len(token.text)
        i += 1

    if last_end < len(prompt):
        new_prompt.append(prompt[last_end:])
    modified_prompt = "".join(new_prompt)
    return modified_prompt

def main_with_args(original_dataset: str, output_path: Path):
    nlp = spacy.load("en_core_web_trf")
    original_dataset = datasets.load_dataset(original_dataset, split="only_subsets")
    #[ ] Drop columns that seem pointless: prints, tests_passed,  total_tests, completion.  (Some of these are now stale – after substitution, we are going to get different values for these columns)
    columns_to_drop = ['prints', 'tests_passed', 'total_tests', 'completion', 'is_success','first_attempt','last_attempt','is_first_success', 'is_first_failure', 'is_last_success', 'is_last_failure'] 

    results = [ ]
    for item in original_dataset:
        original_prompt = item["prompt"]
        tagged_prompt = tag_prompt(nlp, original_prompt)
        item['prompt'] = tagged_prompt
        #[ ] Single column “subset” with values first_success / first_failure / last_success / last_failure
        subset_value = None
        if item['is_first_success']:
            subset_value = 'first_success' 
        elif item['is_last_success']:
            subset_value = 'last_success'
        elif item['is_first_failure']:
            subset_value = 'first_failure'
        elif item['is_last_failure']:
            subset_value = 'last_failure'
        else:
            raise ValueError("No subset value found")
        item['subset'] = subset_value
        # Drop columns that seem pointless
        for column in columns_to_drop:
            del item[column]
        # Reorder fields so that '__index_level_0__' is first
        reordered_item = {}
        if '__index_level_0__' in item:
            reordered_item['__index_level_0__'] = item['__index_level_0__']

        # Add the rest of the fields, excluding '__index_level_0__'
        reordered_item.update({k: v for k, v in item.items() if k != '__index_level_0__'})

        results.append(reordered_item)

    with output_path.open("w") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")
    print(f"Saved {len(results)} items to {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_dataset", type=str, default="wellesley-easel/StudentEval")
    parser.add_argument("--output_path", type=Path, default=Path("tagged_prompts_middle.jsonl"))
    args = parser.parse_args()
    main_with_args(args.original_dataset, args.output_path)

if __name__ == "__main__":
    main()