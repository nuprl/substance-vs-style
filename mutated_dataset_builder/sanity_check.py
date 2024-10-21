
import re
from main import TAGS
from subst import WORDS_V, CATEGORIES_V
import json
from ruamel.yaml import YAML
import json
import argparse

#Category, possible substitution words, in their original form
subst_to_run = {
    "string": ["word","phrase","string","character","set of characters"],
    "list":["brackets","set of brackets","set","list","array list","array"],
    "dictionary":["map","dictionary"],
    "integer": ["integer","whole number","int"],
    "return": ["return","output","print","produce","display"],
    "parameter": ["parameter","argument","value provided","input"],
    "take": ["take","bring in","accept","get","input"],
    "provide": ["provide","enter","input"],
    "concatenate": ["concatenate","combine","splice","add"],
    "insert": ["insert","add","append","attach"],
    "loop through": ["go through","run through","iterate through","loop through","run a for loop through","look through","execute a for loop with"],
    "skip": ["skip","avoid","neglect","ignore","remove"],
    "typecast": ["typecast","type cast","cast","convert","change"],
    "key": ["key","item","entry","attribute","part","element","variable"],
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


def check_pair_exist(category: str,word: str):
    category_variations = CATEGORIES_V[category]
    word_variations = WORDS_V[word]
    for category_variation in category_variations:
        # print("replace category_variation",category_variation,"with",get_word_variation(word,category_variation))
        assert get_word_variation(word,category_variation)!=None
        for word_variation in word_variations:
            #skip special case of input
            if word_variation == 'inputted' and category_variation in ['parameter','parameters','take','takes']:
                continue
            if word_variation not in TAGS:
                raise ValueError(f"Could not find the word {word_variation} in TAGS.")
            possible_tags = TAGS[word_variation] if isinstance(TAGS[word_variation], list) else [TAGS[word_variation]]
            # print("Possible tags: ", possible_tags)
            exist = False
            for tag in possible_tags:
                if tag in category_variations:
                    exist = True
            if exist == False:
                raise ValueError(f"Could not find the pair ({word_variation}, {category_variation}) in TAGS.")

def check_tagged_category(prompt):
    # Regex pattern to match $CATEGORY:ORIGINAL$
    pattern = re.compile(r"\$([\w\s]+):([\w\s]+)\$")
    for match in pattern.finditer(prompt):
        # Extract CATEGORY
        category = match.group(1)
        original = match.group(2)
        found = False
        for super_category, categories in CATEGORIES_V.items():
            if category.lower() in categories:
                found = True
        if found == False:
            raise ValueError(f"Category '{category}' not found in CATEGORIES_V.")
        
    return


def main_with_args(tagged_dataset: str):
    for category, words in subst_to_run.items():
        for word in words:
            check_pair_exist(category,word)
    print("All subsitution pairs exist.")
    yaml = YAML()
    with open(tagged_dataset, 'r') as yaml_file:
        yaml_data = yaml.load(yaml_file)

    for item in yaml_data:
        prompt = item["prompt"]
        check_tagged_category(prompt)
    print("All tagged categories are valid.")
    print("All word variation pairs exist.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tagged_dataset", type=str, default="/mnt/ssd/aryawu/studenteval_nlp/for_edits/two_of_each_firstlast_all.yaml")
    args = parser.parse_args()
    main_with_args(args.tagged_dataset)

if __name__ == "__main__":
    main()