# NLP analysis of StudentEval

## Use of AI assistants

Copilot used in this project.

**IMPORTANT NOTE**: I would not trust the `bigcode_evaluation_harness` studenteval code without modification because
it hardcodes assertions and values of `is_first_x` and `is_last_x` from the original dataset references in `wellesley-easel`. It also
does not keep track of prompt/completions id. I made a hacked-up script for `studenteval.py` that pulls the correct
assertions for a program, but again this does not solve the issue of missing ids and `is_first/last`. I would reccommend using `batched_lm_generation.vllm_base` to generate, then using `batched_lm_generation.hf_format` to compile a dataset that gets passed to
 `src/run_eval.py` for evaluation. This script `run_eval.py` has been tested to match the gold outputs from `bigcode_evaluation_harness` and is more flexible.

