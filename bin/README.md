To systematically run substitution and generation experiments on discovery with the bin scripts:

## Step 1: Substitution
To perform the substitution, run `./bin/subst_all.sh` to generate all the jsonl files of substituted prompt and save them in directory subst_experiments.

## Step 2: Generation
To run generation for all the jsonl files, run `./bin/run_all.sh`, which will run the bash script run_generation.sh on each individual substitution file `experiment_${SPLIT}_${CATEGORY// /_}_${TARGET// /_}.jsonl`. 
You can change the model used to generate by modifying the MODEL in run_generation.sh. 
A directory named `generations_${SPLIT}_${CATEGORY}_${TARGET}` that has the generated results will be saved into generation_experiments directory.

## Step 3: Evaluate
To evaluate the result, we convert the generation into MultiPLE format to execute the generated code and save outputs.
run `./bin/eval_all.sh`

## Step 4: Compute Pass 1
Compute the original and updated Pass@1 of the substituted prompts.

To get the original Pass@1, we need to run generations for the original unmodified studenteval dataset. Run `./bin/run_generation_full.sh`. Modify the MODEL and the EXPERIMENT_DIR.

Then run `./bin/pass_1.sh EXPERIMENT_DIR` with the EXPERIMENT_DIR being where the generations of the original studenteval are stored.

This will print out the pass 1 for all subsitution experiments.