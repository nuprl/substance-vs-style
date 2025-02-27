#!/bin/bash
set -x
set -e

MODEL_DIR=$1

# Specify the parent directory containing subdirectories
PARENT_DIR="/work/arjunguha-research-group/zi.wu/studenteval_nlp/generation_experiments"
cd "$PARENT_DIR"

# Create an array to hold the directory arguments
DIR_ARGS=()

# Loop through each subdirectory and process paths
for dir in $MODEL_DIR/interventions/generations*/; do
    # Remove trailing slash and construct the path
    trimmed_dir=$(echo "$dir" | sed 's:/$::')
    
    # Construct the final output
    output="${trimmed_dir}/extracted_jsons"
    
    # Append the output to DIR_ARGS array
    DIR_ARGS+=("$output")
done


python3 pass_1.py --orig_dir "$MODEL_DIR/studenteval/extracted_jsons" "${DIR_ARGS[@]}"
