# NLP analysis of StudentEval

## Workflow

1. We first apply a tagging process to every prompt in the first/last success/failure subsets of StudentEval.
   For example, given a prompt `"Outputs if the number input is even"`, the tagged prompt becomes
   `"$Returns:prints$ if the number $parameter:input$ is even"`. This process is semi-automated.

   a. `mutated_dataset_builder/main.py` rule-based script that creates a preliminary tagged dataset
      [nuprl-staging/studenteval_tagged_prompts](https://huggingface.co/datasets/nuprl-staging/studenteval_tagged_prompts).
   b. We transform this dataset to the file [FILL], which we manually edit.
   c. We map these edits back to a new split of the tagged dataset

2. [FILL]


## Use of AI assistants

Copilot used in this project.

**IMPORTANT NOTE**: I would not trust the `bigcode_evaluation_harness` studenteval code without modification because
it hardcodes assertions and values of `is_first_x` and `is_last_x` from the original dataset references in `wellesley-easel`. It also
does not keep track of prompt/completions id. I made a hacked-up script for `studenteval.py` that pulls the correct
assertions for a program, but again this does not solve the issue of missing ids and `is_first/last`. I would reccommend using `batched_lm_generation.vllm_base` to generate, then using `batched_lm_generation.hf_format` to compile a dataset that gets passed to
 `src/run_eval.py` for evaluation. This script `run_eval.py` has been tested to match the gold outputs from `bigcode_evaluation_harness` and is more flexible.

