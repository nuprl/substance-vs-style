# Notes and observations

## Add Up

quick fix: `list of ...` -> `list of lists of ...`

imprecise language (list instead of list of list)- word `recursive` may be needed
- id 11: correct, uses `rows and columns`
- id 33: uses more technical lang and is correct, eg. `if there is no error`
- id 37: too handholdy, results in wrong output because instructions are wrong.
- id 59: prompt is fine, output is still wrong
- id 60: model makes rec call correctly, but interprets number as just `int` and ignores `float`
- id 62-65: model often misses `list of lists` in the prompt

## Subtract Add

quick fix: `list of integers` -> `list of integers as strings`

Casting issues are common

- id 76: `integers` instead of `string of integers`
- id 77: good prompt, but handholdy?
- id 78-79: model interprets `odd` as `even` until student uses `not even` instead of `odd`

Students confuse odd indexing with odd element. Also, students confuse "add first element"

- id 96: confusing instructions lead to strange output

Explicitly referring to `second` and `third` item always leads astray.

Students instruct `store first item in array` -> which errors when list is empty

## Convert

quick fix: `comma` -> `string break`, `capitalize all strings`, split final answer by `,` (string with commas instead of comma separated list)

Errors:
- model hallucinates `alphabet` variable
- cast errors: list of chars versus list of string
- id 140: alhpabet makes output too long, cuts off
- id 139: capitalization errors
- id 130: student prompt ignores the -1
- id 132: student prompt says explicit `comma` instead of string break
- id 144: output `string` instead of `list of strings`

id 134: somehow model interprets `add to end index -1` -> missing accumulator initialization to `[[]]` instead of `[]`
Also, not list of list but list of strings, so initialization should be `['']`

- id145: wrong student interpretation of the problem
- id158: `starting with 0 as A` prompts the model to get rid of -1, which are necessary for next steps
Student 17 progression is interesting. Final answer includes keyword `slice`, which may be helpful for finally getting correct.

- id174: model forgets edge case, adding first element regardless of -1
- id190: model interprets `start a new string` as add a space
- id197: `enclose with brackets` interpreted as string instead of list

## Order strings

No one got this correct. Students did not understand problem

## Add int

- id236: `add input integer to each item` -> model only adds to other integers, but should also append to strings
- id239: model does not use access in python loop, but adds to index; change does not persist. Perhaps because of use of term `input` and `i` in loop?
- id241: prompt does not mention elements that are lists (list in list)

## Check prime

quick fix: add `:str` annotation to func signature

Most errors are forgetting to convert `str` to `int`, or returning str instead of bool, eg. `return "True"`

- id266: model ignores instruction to `type cast to int`, maybe because input argname is `num`

## Remove odd

- id290: prompt forgets about floats


## Quick fixes
RQ: how many of these prompts are fixed by passing examples to the model? This fixes student prompts that forget to mention edge cases.