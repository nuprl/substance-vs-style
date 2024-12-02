#!/bin/bash
#SBATCH --nodes=1
#SBATCH --mem=64G
#SBATCH --export=All
#SBATCH --cpus-per-task=4
#SBATCH --job-name=gpt4o

set -x
set -e

EXPERIMENT_REPO="/work/arjunguha-research-group/zi.wu/studenteval_nlp"
GENERATION_REPO="/work/arjunguha-research-group/zi.wu/prl_ml"
MODEL="gpt-4o-mini"
CATEGORY=$1
TARGET=$2
SPLIT=$3
    
DATASET_STR="jsonl:${EXPERIMENT_REPO}/subst_experiments/experiment_${SPLIT}_${CATEGORY// /_}.${TARGET// /_}.jsonl"
EXPERIMENT_DIR="${EXPERIMENT_REPO}/generation_experiments/gpt4o-mini/generations_${SPLIT}_${CATEGORY// /_}.${TARGET// /_}"

mkdir -p $EXPERIMENT_DIR
    
cd $GENERATION_REPO
echo "Generating..."

python3 -m prl_ml.batched_lm_generation.gpt4o_chatcoder \
    --model-name $MODEL \
    --dataset $DATASET_STR \
    --output-dir $EXPERIMENT_DIR/completions_jsons \
    --temperature 0.2 \
    --completion-limit 20 \
    --batch-size 20 \
    --max-tokens 1024 \
    --extra-columns __index_level_0__,problem,entrypoint,assertions,username,submitted_text,prompt,subset

echo "Done."