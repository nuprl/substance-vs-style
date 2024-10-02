#!/bin/bash

set -x
set -e

EXPERIMENT_REPO="/work/arjunguha-research-group/zi.wu/studenteval_nlp"
GENERATION_REPO="/work/arjunguha-research-group/zi.wu/prl_ml"
MODEL="bigcode/starcoder2-15b"
CATEGORY=$1
TARGET=$2
SPLIT=$3
    
DATASET_STR="jsonl:${EXPERIMENT_REPO}/subst_experiments/experiment_${SPLIT}_${CATEGORY// /_}_${TARGET// /_}.jsonl"
EXPERIMENT_DIR="${EXPERIMENT_REPO}/generation_experiments/generations_${SPLIT}_${CATEGORY// /_}_${TARGET// /_}"

mkdir $EXPERIMENT_DIR
    
cd $GENERATION_REPO
export CUDA_VISIBLE_DEVICES="0"
echo "Generating..."

python3 -m prl_ml.batched_lm_generation.vllm_base \
    --model-name $MODEL \
    --dataset $DATASET_STR \
    --output-dir $EXPERIMENT_DIR/completions_jsons \
    --temperature 0.2 \
    --completion-limit 20 \
    --num-gpus 1 \
    --stop '["\ndef", "\nassert", "\nprint", "\nclass"]' \
    --batch-size 1000 \
    --extra-columns __index_level_0__,problem,entrypoint,assertions,username,submitted_text,prompt,subset

