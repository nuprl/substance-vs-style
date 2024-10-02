# Substitution Experiments

1. Upload the YAML file with the tagged data to the Hugging Face Hub.
   We will eventually have a "final" YAML file. But, some preliminary ones
   are already on the Hub with the split name filename-commithash. Example:


   https://huggingface.co/datasets/nuprl-staging/studenteval_tagged_prompts/viewer/default/two.of.each.firstlast.firsthalf.475cc88


2. Use the substitution script to build a variation of a subset of StudentEval:

   [FILL] (refers to the appropriate split above)

3. Run generations on Discovery:

   ```bash
   source ...
   module load cuda/12.1
   [FILL] run_generations.sh
   ```

4. Convert generations to MultiPL-E format:

   ```bash
   python3 -m prl_ml.batched_lm_generation.multiple_format completions_json multiple --tests-field assertions
   ````

5. Run MultiPL-E execution script to test the generations:

   ```bash
   sbatch /work/arjunguha-research-group/arjun/jobs/exec_multipl-e.sbatch multiple 
   ```

6. [FILL] Write code

