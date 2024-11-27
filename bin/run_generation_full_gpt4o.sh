#!/bin/bash
#SBATCH --nodes=1
#SBATCH --mem=64G
#SBATCH --export=All
#SBATCH --cpus-per-task=4
#SBATCH --time=24:00:00
#SBATCH --job-name=arya

set -x
set -e

EXPERIMENT_REPO="/work/arjunguha-research-group/zi.wu/studenteval_nlp"
MODEL="gpt-4o-mini"

DATASET_STR="hub:wellesley-easel/StudentEval:split=test"
EXPERIMENT_DIR="${EXPERIMENT_REPO}/generation_experiments/gpt4o-mini/studenteval"

mkdir -p $EXPERIMENT_DIR
    
echo "Generating..."

python3 -m prl_ml.batched_lm_generation.gpt4o_chatcoder \
    --model-name $MODEL \
    --dataset $DATASET_STR \
    --output-dir $EXPERIMENT_DIR/completions_jsons \
    --temperature 0.2 \
    --completion-limit 20 \
    --batch-size 40 \
    --max-tokens 1024 \
    --extra-columns __index_level_0__,problem,entrypoint,assertions,username,submitted_text,prompt


echo "Formating..."
python3 -m prl_ml.batched_lm_generation.completion_extraction $EXPERIMENT_DIR/completions_jsons $EXPERIMENT_DIR/extracted_jsons

echo "Executing..."
sbatch python3 -m prl_ml.batched_lm_generation.execute_python --experiment-dir $EXPERIMENT_DIR/extracted_jsons

echo "Done."