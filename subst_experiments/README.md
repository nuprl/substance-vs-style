# Substitution Experiments

1. Upload the YAML file with the tagged data to the Hugging Face Hub.
   We will eventually have a "final" YAML file. But, some preliminary ones
   are already on the Hub with the split name filename.commithash. Example:

   https://huggingface.co/datasets/nuprl-staging/studenteval_tagged_prompts/viewer/default/two.of.each.firstlast.firsthalf.475cc88


2. Use the substitution script to build a variation of a subset of StudentEval:

   Run bash script bin/prepare_subst.sh on the validated dataset to get various splits of substituted data base on target word and replacement value. 
   `./bin/prepare_subst.sh CATEGORY ORIGINAL`
   The first argument is the category, the second argument is the replacement value.

   eg. `./bin/prepare_subst.sh "return" "output"`
   replaces all occurrance of words tagged with category 'return' with the correct word variation of 'output'.(i.e. returns-outputs, returning-outputting.)

3. Run generations on Discovery:

   ```bash
   source ...
   module load cuda/12.1
   ./bin/prepare_subst.sh CATEGORY ORIGINAL
   ```
      
   eg. `./bin/run_generation.sh "return" "output"`
   This will create a dir splitname_return_output, with a sub dir completions_jsons storing all the json.gz files.

4. Convert generations to MultiPL-E format:
   cd into generation_experiments/splitname_return_output

   ```bash
   python3 -m prl_ml.batched_lm_generation.multiple_format completions_jsons multiple --tests-field assertions --language py
   ````

5. Run MultiPL-E execution script to test the generations:

   ```bash
   sbatch /work/arjunguha-research-group/arjun/jobs/exec_multipl-e.sbatch multiple 
   ```

6. Compute the original and updated Pass@1 of the substituted prompts.
   Run this from the generation_experiments dir. 
   ```bash
   python3 pass_1.py generations_two.of.each.firstlast.firsthalf.475cc88_return_output/multiple
   ```
   

