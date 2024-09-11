import datasets
from pathlib import Path
import spacy
import json
import argparse
import re
#string, list, dictionary, integer, return, input, concatenate
#and maybe also:loop, skip, typecast, key

# For each KEY:VALUE pair, when we see the word KEY in the prompt, we tag it
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
    "characters": "strings",
    "character": "string",
    #list:
    "brackets": "list",
    "set of brackets": "list",
    "set": "list",
    "list": "list",
    "lists": "lists",
    "array": "list",
    "sequence": "list",
    #dictionary:
    "map": "dictionary",
    "maps": "dictionaries",
    "dictionary": "dictionary",
    "dictionaries": "dictionaries",
    #"array": "dictionary",#array tagged list already
    #"arrays": "dictionaries",
    #integer:
    "integer": "integer",
    "integers": "integers",
    "whole number": "integer",
    "int": "integer",
    #return
    "output": "return",
    "outputs": "returns",
    "outputed": "returned",
    "outputing": "returning",
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
    #input
    "parameter": "input",
    "parameters": "inputs",
    "input": "input",
    "inputs": "inputs",
    "inputed": "input",
    "inputted": "input",
    "argument": "input",
    "arguments": "inputs",
    "take": "input",
    "takes": "inputs",
    "provided": "input",
    "enter": "input",
    "enters": "inputs",
    "entered": "input",
    "brings in": "input",
    "given": "input",
    "passed": "input",
    "accept": "input",
    "gets": "inputs",
    "receives": "inputs",
    #concatenate
    "add": "concatenate",
    "adds": "concatenates",
    "added": "concatenated",
    "adding": "concatenating",
    "insert": "concatenate",
    "inserts": "concatenates",
    "inserted": "concatenated",
    "inserting": "concatenating",
    "combine": "concatenate",
    "combines": "concatenates",
    "combined": "concatenated",
    "combining": "concatenating",
    "splice": "concatenate",
    "splices": "concatenates",
    "spliced": "concatenated",
    "splicing": "concatenating",
    "attach": "concatenate",
    "attaches": "concatenates",
    "attached": "concatenated",
    "attaching": "concatenating",
    "concatenate": "concatenate",
    "concatenates": "concatenates",
    "concatenated": "concatenated",
    "concatenating": "concatenating",
    "append": "concatenate",
    "appends": "concatenates",
    "appended": "concatenated",
    "appending": "concatenating",
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
    "looks through": "loops through",
    "executes a for loop": "loops",
    "loop over": "loop through",
    "loops over": "loops through",
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
    "turn": "typecast",
    "turns": "typecasts",
    "turned": "typecasted",
    "turning": "typecasting",
    "type cast": "typecast",
    "typecast": "typecast",
    "typecasts": "typecasts",
    "typecasted": "typecasted",
    "typecasting": "typecasting",
    "treat": "typecast",
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
    # "parameter": "key",
    # "parameters": "keys",
    "variable": "key",
    "variables": "keys",
}

def extract_parts(prompt: str):
    match = re.search(r'(.*?\"\"\"\s*)(.*?)(\s*\"\"\".*)', prompt, re.DOTALL)
    if match:
        before = match.group(1)  # Includes the triple quotes and spaces/newlines after the first triple quotes
        docstring = match.group(2)  # The content inside the triple quotes
        after = match.group(3)  # Includes the spaces/newlines before and the triple quotes after the content
        return before, docstring, after
    else:
        return None, None, None

    
def tag_prompt(nlp: spacy.Language, prompt: str) -> str:
    """
    Given a prompt such as

    This function prints the word "Hello".

    This function will return the following string:

    This function $$returns:prints$$ the $$string:word$$ "Hello".
    (the form $CATEGORY:ORIGINAL$)

    Thus, all possible words that we may substitute are tagged with their category.

    This is *not* a dataset that we can feed to the model. But, we can edit the
    dataset manually to address cases where the rules go wrong. After inspection,
    we can apply substitutions.
    """
    #prompt might look like this def add_up(arr):"""takes a list of strings, integers, and floats and returns the sum of all the integers and floats."""
    #search for """ in prompt
    #Get the text between the first and second """
    before,docstring,after = extract_parts(prompt)
    doc = nlp(docstring)
    new_prompt = []
    for token in doc:
        # lemma = token.lemma_
        if token.text in TAGS:
            new_prompt.append(f"${TAGS[token.text]}:{token.text}$")
        elif token.text.lower() in TAGS:
            tag = TAGS[token.text.lower()]
            uppercasetag = tag[0].upper() + tag[1:]
            new_prompt.append(f"${uppercasetag}:{token.text}$")
        else:
            new_prompt.append(token.text)
    modified_prompt = " ".join(new_prompt)
    modified_prompt = re.sub(r'\s+([.,!?])', r'\1', modified_prompt)  # Remove spaces before punctuation
    return f"{before}{modified_prompt}{after}"

# original_dataset = datasets.load_dataset('wellesley-easel/StudentEval', split="only_subsets")
# prompt0 = original_dataset[10]['prompt']
# prompt0m = tag_prompt(spacy.load("en_core_web_trf"), prompt0)
# print(prompt0)
# print(prompt0m)

# """
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
# """