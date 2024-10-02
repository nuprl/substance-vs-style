#!/bin/bash

set -x
set -e

CATEGORY=$1
TARGET=$2
SPLIT=$3

python3 mutated_dataset_builder/subst.py \
    --output_path "subst_experiments/experiment_${SPLIT}_${CATEGORY// /_}_${TARGET// /_}.jsonl" \
    --category "$CATEGORY" \
    --value "$TARGET" \
    --original_dataset nuprl-staging/studenteval_tagged_prompts \
    --split $SPLIT