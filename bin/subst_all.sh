#!/bin/bash

set -x
set -e

EXPERIMENT_REPO="/work/arjunguha-research-group/zi.wu/studenteval_nlp"
cd $EXPERIMENT_REPO

SPLIT='all.prompts.full.label.d2c1570'

# Embedded Python to handle subst_to_run dictionary
subst_to_run=$(python3 - <<EOF
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
import json
print(json.dumps(subst_to_run))
EOF
)

# Parse the Python JSON output back into bash and run commands for each substitution
echo "$subst_to_run" | jq -c 'to_entries[]' | while read -r item; do
    key=$(echo "$item" | jq -r '.key')
    # Extract the values as a single string
    values=$(echo "$item" | jq -r '.value | join(",")')

    # Split the string into an array while preserving spaces
    IFS=',' read -ra value_array <<< "$values"

    for TARGET in "${value_array[@]}"; do
        TARGET=$(echo "$TARGET" | xargs)  # Trim whitespace
        CATEGORY=$key
        ./bin/prepare_subst.sh "${CATEGORY}" "${TARGET}" ${SPLIT}
        echo "Preparing substitution: ${CATEGORY} -> ${TARGET}"
        
    done
done