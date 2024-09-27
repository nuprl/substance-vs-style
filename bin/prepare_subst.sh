#!/bin/bash

set -x
set -e

CATEGORY=$1
TARGET=$2

python3 mutated_dataset_builder/subst.py \
    --output_path "subst_experiments/experiment_full_${CATEGORY// /_}_${TARGET// /_}.jsonl" \
    --category "$CATEGORY" \
    --value "$TARGET" \
    --original_dataset nuprl-staging/studenteval_tagged_prompts