
import re
from main import TAGS
from subst import WORDS_V, CATEGORIES_V
import json
from ruamel.yaml import YAML
import json
import argparse

#Category, possible substitution words, in their original form
# 15 categories, 63 experiments to run
subst_to_run = {
    #string:
    "string": ["word","phrase","string","character","set of characters"],
    #list:
    "list":["brackets","set of brackets","set","list","array","sequence"],
    #dictionary:
    "dictionary":["map","dictionary"],
    #integer:
    "integer": ["integer","whole number","int"],
    #return
    "return": ["return","output","print","produce","display"],
    #parameter
    "parameter": ["parameter","argument","value provided"],
    #input
    "input": ["input"],
    #take
    "take": ["take","bring in","accept","get","receive"],
    #provide
    "provide": ["provide","enter"],
    #concatenate
    "concatenate": ["concatenate","combine","splice"],
    #insert
    "insert": ["insert","add","append","attach"],
    #loop
    "loop through": ["go through","run through","iterate through","loop through","run a for loop through","look through","execute a for loop with"],
    #skip
    "skip": ["skip","avoid","neglect","ignore","remove"],
    #typecast
    "typecast": ["typecast","convert","change","turn","treat"],
    #key
    "key": ["key","item","entry","attribute","part","element","variable"],
}


def check_pair_exist(category: str,word: str):
    category_variations = CATEGORIES_V[category]
    word_variations = WORDS_V[word]
    for category_variation in category_variations:
        for word_variation in word_variations:
            #TAGS have the format (key=word_variation, value=category_variations)
            if word_variation in TAGS and TAGS[word_variation] in category_variations:
                return True
            else:
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
    yaml = YAML()
    with open(tagged_dataset, 'r') as yaml_file:
        yaml_data = yaml.load(yaml_file)

    for item in yaml_data:
        prompt = item["prompt"]
        check_tagged_category(prompt)
    print("All tagged categories are valid.")

    for category, words in subst_to_run.items():
        for word in words:
            check_pair_exist(category,word)
    print("All subsitution pairs exist.")
    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tagged_dataset", type=str, default="/mnt/ssd/aryawu/studenteval_nlp/for_edits/two_of_each_firstlast_all.yaml")
    args = parser.parse_args()
    main_with_args(args.tagged_dataset)

if __name__ == "__main__":
    main()