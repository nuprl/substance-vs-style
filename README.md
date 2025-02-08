# NLP analysis of StudentEval

## Substitution Experiment Workflow

1. We first apply a tagging process to every prompt in the first/last success/failure subsets of StudentEval.
   For example, given a prompt `"Outputs if the number input is even"`, the tagged prompt becomes
   `"$Returns:prints$ if the number $parameter:input$ is even"`. This process is semi-automated.

   a. `mutated_dataset_builder/main.py` rule-based script that creates a preliminary tagged dataset
      [nuprl-staging/studenteval_tagged_prompts](https://huggingface.co/datasets/nuprl-staging/studenteval_tagged_prompts).
   b. We transform this dataset to the file [tagged_prompts_for_edits](https://github.com/franlucc/studenteval_nlp/blob/main/tagged_prompts_for_edits.yaml) by running json_to_yaml.py. We manually edit this file.
   c. We map these edits back to a new split of the tagged dataset

2. We then run bash script bin/prepare_subst.sh on the validated dataset to get various splits of substituted data base on target word and replacement value. Create a directory subst_experiments where the dataset will be stored in jsonl format.
   `./bin/prepare_subst.sh CATEGORY ORIGINAL`
   The first argument is the category, the second argument is the replacement value

   eg. `./bin/prepare_subst.sh "return" "output"`
   replaces all occurrance of words tagged with category 'return' with the correct word variation of 'output'.(i.e. returns-outputs, returning-outputting.)
   
   eg. `./bin/prepare_subst.sh "loop through" "go through"`

3. We run generation script bin/run_generation.sh on the substitued datasets. Create a directory generation_experiments to store the generated model results.
   eg. `./bin/run_generation.sh "return" "output"`
   This will create a dir return_output, with a sub dir completions_jsons storing all the json.gz files.

## Student Trajectories Experiment Workflow

TODO

## Use of AI assistants

Copilot used in this project.
