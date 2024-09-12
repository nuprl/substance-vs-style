EXPERIMENT_DIR=$1
MODEL=$2
EVAL_REPO="/home/franlucc/projects/studenteval_nlp"
GENERATION_REPO="/home/franlucc/projects/batched_lm_generation"

mkdir $EXPERIMENT_DIR
EXPERIMENT_DIR="$(pwd)/$EXPERIMENT_DIR"
echo $EXPERIMENT_DIR
source ~/venvs/vllm/bin/activate

cd $EVAL_REPO
echo "Mutating..."
# apply problem substituions
python -m mutated_dataset_builder.problem_edits franlucc/llama3.1_8b_base_studenteval $EXPERIMENT_DIR/raw_substitution_ds --split only_subsets
python to_csv.py $EXPERIMENT_DIR/raw_substitution_ds only_subsets $EXPERIMENT_DIR/raw_substitution_ds.csv
python to_subst_hf.py $EXPERIMENT_DIR/raw_substitution_ds.csv $EXPERIMENT_DIR/substitution_ds
python to_csv.py $EXPERIMENT_DIR/substitution_ds test $EXPERIMENT_DIR/substitution_ds.csv

cd $GENERATION_REPO
export CUDA_VISIBLE_DEVICES="3"
echo "Generating..."
python3 -m batched_lm_generation.vllm_base --model-name $MODEL --dataset $EXPERIMENT_DIR/substitution_ds --dataset-split test \
--output-dir $EXPERIMENT_DIR/completions_jsons --temperature 0.2 --completion-limit 20 --num-gpus 1 --stop '["def", "assert", "print", "class"]' \
--batch-size 10000000 --load-from-disk --extra-columns problem,entrypoint,assertions,prints,username,submitted_text,total_tests,prompt,first_attempt,last_attempt,__index_level_0__

python3 -m batched_lm_generation.hf_format $EXPERIMENT_DIR/completions_jsons $EXPERIMENT_DIR/hf_completions

cd $EVAL_REPO
echo "Evaluating..."
python src/run_eval.py $EXPERIMENT_DIR/hf_completions $EXPERIMENT_DIR/hf_eval
python to_csv.py $EXPERIMENT_DIR/hf_eval test $EXPERIMENT_DIR/hf_eval.csv
python -m src.analysis $EXPERIMENT_DIR/hf_eval >> $EXPERIMENT_DIR/analysis_results.md
cat $EXPERIMENT_DIR/analysis_results.md