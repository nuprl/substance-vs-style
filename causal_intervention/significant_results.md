# Results for LLama 8B

Results are from mixed-effects binary logistic regression models, including random effects for prompt ID and problem. The random effects structure for problem contains both random slopes and intercepts; due to issues with convergence, the random effects for prompt ID contain only random intercepts. 

The outcome variable for our data is a proportion. In GLMR models, the number of observations upon which the proportion is based can be included as a weight argument. These results are based on 200 samples, so all models were fit with a weight of 200.

All comparisons use the original, unmodified prompt as the baseline condition.

## Type categories

String: 
	- Character has a significant negative effect
	- Phrase has a significnat negative effect
	- Set of characters has a significant negative effect
	- Word has a significant negative effect
	- The largest magnitude effect is set of characters

Integer:
	- Marginal negative effect of whole number

List:
	- Brackets has a significant negative effect
	- Set has a significant negative effect
	- Set of brackets has a significant negative effect
	- The largest magnitude effect is set

Dictionary:
	- No significant effects

Key:
	- Attribute has a significant negative effect
	- Entry has a significant negative effect
	- Item has a significant negative effect
	- Part has a significant negative effect
	- Variable has a significant negative effect
	- The strongest magnitude effect is attribute

## Control flow categories

Take:
	- No significant effects

Parameter:
	- No significant effects

Provide:
	- No significant effects

Return:
	- Display has a significant negative effect
	- Print has a significant negative effect
	- The strongest magnitude effect is print

Loop:
	- Execute a for loop with has a significant negative effect
	- Go through has a significant negative effect
	- Run a for loop through has a significant negative effect
	- The strongest magnitude effect is execute a for loop with

## Operation categories

Concatenate:
	- Splice has a significant negative effect

Insert:
	- No significant effects

Skip:
	- Remove has a significant negative effect
	- Avoid has a significant negative effect
	- The strongest magnitude effect is remove

Typecast:
	- Cast has a significant negative effect
