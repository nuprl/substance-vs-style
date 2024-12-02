#!/bin/bash
#SBATCH --nodes=1
#SBATCH --mem=64G
#SBATCH --export=All
#SBATCH --cpus-per-task=4
#SBATCH --job-name=arya
#SBATCH --partition=177huntington
#SBATCH --gres=gpu:2

set -x
set -e

EXPERIMENT_REPO="/work/arjunguha-research-group/zi.wu/studenteval_nlp"
GENERATION_REPO="/work/arjunguha-research-group/zi.wu/prl_ml"
MODEL="/work/arjunguha-research-group/arjun/models/llama3p1_70b_base"
CATEGORY=$1
TARGET=$2
SPLIT=$3
    
DATASET_STR="jsonl:${EXPERIMENT_REPO}/subst_experiments/experiment_${SPLIT}_${CATEGORY// /_}.${TARGET// /_}.jsonl"
EXPERIMENT_DIR="${EXPERIMENT_REPO}/generation_experiments/generations_${SPLIT}_${CATEGORY// /_}.${TARGET// /_}"

mkdir -p $EXPERIMENT_DIR
    
cd $GENERATION_REPO
echo "Generating..."

python3 -m prl_ml.batched_lm_generation.vllm_base \
    --model-name $MODEL \
    --dataset $DATASET_STR \
    --output-dir $EXPERIMENT_DIR/completions_jsons \
    --temperature 0.2 \
    --completion-limit 20 \
    --num-gpus 2 \
    --stop '["\ndef", "\nassert", "\nprint", "\nclass"]' \
    --batch-size 100 \
    --extra-columns __index_level_0__,problem,entrypoint,assertions,username,submitted_text,prompt,subset

echo "Done."