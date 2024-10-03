# How to Navigate

This folder includes the results of auto-tagging prompts with the substitution strings.
This is for data labeling _only_ and does not contain any final projects.

## for_edits/
Contains the final result .yaml files for three different passes on the data:
1) the 96 problem subset for validating (two each from each problem)
2) the remaining problems from the firstlast/successfail subset of prompts _without_ the strings tags
3) the remaining problems from the firstlast/successfail subset of prompts _with_ the strings tags
4) the .yaml comparison script used to create the decision text files to diff the two annotators

## individual_comparisons/
The files used by the two annotators to individually reconclide tags. There is one per annotator for each pass. The first 96 problems were done in two halves. Hence, why there are 5 files per person.

## irr_decisions/
The four main decision passes. Includes the diff and then a DECISION about what tags to keep or discard. 

