import datasets
from pathlib import Path
import spacy
import json
import argparse
import re

# TAGS is a dictionary that maps a word's variations to the corresponding tagging category's variations.
# The Key is a word's base form, and the value is a list of dictionaries. Each dictionary has two keys: "variant" is the variation of this base word, and "category" is the variation of the category that this base word should be tagged as.
# For each word in a prompt, if we find this word in one of the variations of a base word, we tag it with the corresponding category's variation.
# eg. If we see the word "phrases" in a prompt, we tag it with "$strings:phrases$" because "phrases" is a variation of the base word "phrase", and should be tagged as "strings", the correct variation of the category "string".
#See charlie_sysnonyms.csv
TAGS = {
    # "string": ["string","word","phrase","set of characters","character"],
    "string":[{"variant":"string","category":"string"},{"variant":"strings","category":"strings"}],
    "word":[{"variant":"word","category":"string"},{"variant":"words","category":"strings"}],
    "phrase":[{"variant":"phrase","category":"string"},{"variant":"phrases","category":"strings"}],
    "set of characters":[{"variant":"set of characters","category":"string"},{"variant":"sets of characters","category":"strings"}],
    "character":[{"variant":"character","category":"string"},{"variant":"characters","category":"strings"}],

    # "list":["brackets","set of brackets","set","list","array","array list"],
    "brackets":[{"variant":"brackets","category":"list"},{"variant":"brackets","category":"lists"}],
    "set of brackets":[{"variant":"set of brackets","category":"list"},{"variant":"sets of brackets","category":"lists"}],
    "set":[{"variant":"set","category":"list"},{"variant":"sets","category":"lists"}],
    "list":[{"variant":"list","category":"list"},{"variant":"lists","category":"lists"}],
    "array":[{"variant":"array","category":"list"},{"variant":"arrays","category":"lists"}],
    "array list":[{"variant":"array list","category":"list"},{"variant":"array lists","category":"lists"}],

    # "dictionary":["map","dictionary"],
    "map":[{"variant":"map","category":"dictionary"},{"variant":"maps","category":"dictionaries"}],
    "dictionary":[{"variant":"dictionary","category":"dictionary"},{"variant":"dictionaries","category":"dictionaries"}],

    # "integer": ["integer","whole number","int"],
    "integer":[{"variant":"integer","category":"integer"},{"variant":"integers","category":"integers"}],
    "whole number":[{"variant":"whole number","category":"integer"},{"variant":"whole numbers","category":"integers"}],
    "int":[{"variant":"int","category":"integer"},{"variant":"ints","category":"integers"}],

    # "return":["output","return","print","produce","display"],
    "output":[{"variant":"output","category":"return"},{"variant":"outputs","category":"returns"}, {"variant":"outputted","category":"returned"}, {"variant":"outputting","category":"returning"}],
    "return":[{"variant":"return","category":"return"},{"variant":"returns","category":"returns"}, {"variant":"returned","category":"returned"}, {"variant":"returning","category":"returning"}],
    "print":[{"variant":"print","category":"return"},{"variant":"prints","category":"returns"}, {"variant":"printed","category":"returned"}, {"variant":"printing","category":"returning"}],
    "produce":[{"variant":"produce","category":"return"},{"variant":"produces","category":"returns"}, {"variant":"produced","category":"returned"}, {"variant":"producing","category":"returning"}],
    "display":[{"variant":"display","category":"return"},{"variant":"displays","category":"returns"}, {"variant":"displayed","category":"returned"}, {"variant":"displaying","category":"returning"}],

    # "parameter": ["parameter","argument","value provided","input"],
    "parameter":[{"variant":"parameter","category":"parameter"},{"variant":"parameters","category":"arguments"}],
    "argument":[{"variant":"argument","category":"parameter"},{"variant":"arguments","category":"arguments"}],
    "value provided":[{"variant":"value provided","category":"parameter"},{"variant":"values provided","category":"arguments"}],
    "input":[{"variant":"input","category":"parameter"},{"variant":"inputs","category":"arguments"}],

    # "take": ["take","bring in","accept","get"],
    "take":[{"variant":"take","category":"take"},{"variant":"takes","category":"takes"}],
    "bring in":[{"variant":"bring in","category":"take"},{"variant":"brings in","category":"takes"}],
    "accept":[{"variant":"accept","category":"take"},{"variant":"accepts","category":"takes"}],
    "get":[{"variant":"get","category":"take"},{"variant":"gets","category":"takes"}],

    # "provide":["provide","enter","input"],
    "provide":[{"variant":"provide","category":"provide"},{"variant":"provides","category":"provides"}, {"variant":"provided","category":"provided"}],
    "enter":[{"variant":"enter","category":"provide"},{"variant":"enters","category":"provides"}, {"variant":"entered","category":"provided"}],
    "input":[{"variant":"input","category":"provide"},{"variant":"inputs","category":"provides"}, {"variant":"inputted","category":"provided"}],

    # "concatenate": ["combine","splice","concatenate","add"],
    "combine":[{"variant":"combine","category":"concatenate"},{"variant":"combines","category":"concatenates"}, {"variant":"combined","category":"concatenated"}, {"variant":"combining","category":"concatenating"}],
    "splice":[{"variant":"splice","category":"concatenate"},{"variant":"splices","category":"concatenates"}, {"variant":"spliced","category":"concatenated"}, {"variant":"splicing","category":"concatenating"}],
    "concatenate":[{"variant":"concatenate","category":"concatenate"},{"variant":"concatenates","category":"concatenates"}, {"variant":"concatenated","category":"concatenated"}, {"variant":"concatenating","category":"concatenating"}],
    "add":[{"variant":"add","category":"concatenate"},{"variant":"adds","category":"concatenates"}, {"variant":"added","category":"concatenated"}, {"variant":"adding","category":"concatenating"}],

    # "insert": ["insert","attach","append"],
    "insert":[{"variant":"insert","category":"insert"},{"variant":"inserts","category":"inserts"}, {"variant":"inserted","category":"inserted"}, {"variant":"inserting","category":"inserting"}],
    "attach":[{"variant":"attach","category":"insert"},{"variant":"attaches","category":"inserts"}, {"variant":"attached","category":"inserted"}, {"variant":"attaching","category":"inserting"}],
    "append":[{"variant":"append","category":"insert"},{"variant":"appends","category":"inserts"}, {"variant":"appended","category":"inserted"}, {"variant":"appending","category":"inserting"}],

    # "loop through": ["go through","run through","iterate through","loop through","run a for loop through","look through","execute a for loop with"],
    "go through":[{"variant":"go through","category":"loop through"},{"variant":"goes through","category":"loops through"}],
    "run through":[{"variant":"run through","category":"loop through"},{"variant":"runs through","category":"loops through"}],
    "iterate through":[{"variant":"iterate through","category":"loop through"},{"variant":"iterates through","category":"loops through"}],
    "loop through":[{"variant":"loop through","category":"loop through"},{"variant":"loops through","category":"loops through"}],
    "run a for loop through":[{"variant":"run a for loop through","category":"loop through"},{"variant":"runs a for loop through","category":"loops through"}],
    "look through":[{"variant":"look through","category":"loop through"},{"variant":"looks through","category":"loops through"}],
    "execute a for loop with":[{"variant":"execute a for loop with","category":"loop through"},{"variant":"executes a for loop with","category":"loops through"}],

    # "skip": ["skip","avoid","neglect","ignore","remove"],
    "skip":[{"variant":"skip","category":"skip"},{"variant":"skips","category":"skips"}, {"variant":"skipped","category":"skipped"}, {"variant":"skipping","category":"skipping"}],
    "avoid":[{"variant":"avoid","category":"skip"},{"variant":"avoids","category":"skips"}, {"variant":"avoided","category":"skipped"}, {"variant":"avoiding","category":"skipping"}],
    "neglect":[{"variant":"neglect","category":"skip"},{"variant":"neglects","category":"skips"}, {"variant":"neglected","category":"skipped"}, {"variant":"neglecting","category":"skipping"}],
    "ignore":[{"variant":"ignore","category":"skip"},{"variant":"ignores","category":"skips"}, {"variant":"ignored","category":"skipped"}, {"variant":"ignoring","category":"skipping"}],
    "remove":[{"variant":"remove","category":"skip"},{"variant":"removes","category":"skips"}, {"variant":"removed","category":"skipped"}, {"variant":"removing","category":"skipping"}],

    # "typecast": ["convert","change","type cast","cast","typecast"],
    "convert":[{"variant":"convert","category":"typecast"},{"variant":"converts","category":"typecasts"}, {"variant":"converted","category":"typecasted"}, {"variant":"converting","category":"typecasting"}],
    "change":[{"variant":"change","category":"typecast"},{"variant":"changes","category":"typecasts"}, {"variant":"changed","category":"typecasted"}, {"variant":"changing","category":"typecasting"}],
    "type cast":[{"variant":"type cast","category":"typecast"},{"variant":"type casts","category":"typecasts"}, {"variant":"type casted","category":"typecasted"}, {"variant":"type casting","category":"typecasting"}],
    "cast":[{"variant":"cast","category":"typecast"},{"variant":"casts","category":"typecasts"}, {"variant":"casted","category":"typecasted"}, {"variant":"casting","category":"typecasting"}],
    "typecast":[{"variant":"typecast","category":"typecast"},{"variant":"typecasts","category":"typecasts"}, {"variant":"typecasted","category":"typecasted"}, {"variant":"typecasting","category":"typecasting"}],

    # "key": ["key","item","entry","attribute","part","element","variable"],
    "key":[{"variant":"key","category":"key"},{"variant":"keys","category":"keys"}],
    "item":[{"variant":"item","category":"key"},{"variant":"items","category":"keys"}],
    "entry":[{"variant":"entry","category":"key"},{"variant":"entries","category":"keys"}],
    "attribute":[{"variant":"attribute","category":"key"},{"variant":"attributes","category":"keys"}],
    "part":[{"variant":"part","category":"key"},{"variant":"parts","category":"keys"}],
    "element":[{"variant":"element","category":"key"},{"variant":"elements","category":"keys"}],
    "variable":[{"variant":"variable","category":"key"},{"variant":"variables","category":"keys"}],
}


def search_word_tag(doc,i,last_end,phrase,length,new_prompt):
    found = False
    for word,variations in TAGS.items():
        for variation in variations:
            if phrase == variation['variant']:
                category = variation['category']
                new_prompt.append(f"${category}:{phrase}$")
                last_end = doc[i+length-1].idx + len(doc[i+length-1].text)
                i += length
                found=True
                return found,i,last_end,new_prompt
            elif phrase.lower() == variation['variant']:
                category = variation['category']
                uppercategory = category[0].upper() + category[1:]
                new_prompt.append(f"${uppercategory}:{phrase}$")
                last_end = doc[i+length-1].idx + len(doc[i+length-1].text)
                i += length
                found=True
                return found,i,last_end,new_prompt
    return found,i,last_end,new_prompt


    
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

        if i < len(doc) - 4:
            five_token_phrase = f"{doc[i].text} {doc[i+1].text} {doc[i+2].text} {doc[i+3].text} {doc[i+4].text}"
            found,i,last_end,new_prompt=search_word_tag(doc,i,last_end,five_token_phrase,5,new_prompt)
            if found:
                continue

        # Check for two-token phrases
        if i < len(doc) - 1:
            two_token_phrase = f"{doc[i].text} {doc[i+1].text}"
            found,i,last_end,new_prompt=search_word_tag(doc,i,last_end,two_token_phrase,2,new_prompt)
            if found:
                continue
        
        # Handle single-token categories
        token = doc[i]
        phrase = token.text
        found,i,last_end,new_prompt=search_word_tag(doc,i,last_end,phrase,1,new_prompt)
        
        if not found:
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
    parser.add_argument("--output_path", type=Path, default=Path("tagged_prompts_try.jsonl"))
    args = parser.parse_args()
    main_with_args(args.original_dataset, args.output_path)

if __name__ == "__main__":
    main()
