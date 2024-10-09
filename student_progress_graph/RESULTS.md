# Results overview

# Data selection

Select problems by following filters:
1. at least 1 success
2. at least 5 students to establish pattern
3. filter out single attempts (interested in edits)

## 1. How clues lead to success

**Method**

    - for each graph, we check that successful students have all the clues for the problem

**Experiment**

    - out of all successful students, how many have all clues?

**Result**

    This shows that success depends on substance

```python
Has all clues 99 / 147 = 0.67
P( is_success | has_all_clues) = 0.45
P( is_success | not_has_all_clues) =  0.07
```

## 2. Cycles

**Method**

    - for each graph, we check that cycle edges are trivial edits
    or student is missing clues

**Experiment**

    - out of all the cyles, how many fit this criteria?

**Result**

    Shows loops are due to students missing a clue

Show that students have a higher likelihood of giving up with cycles

`P(success | not cycle) vs P(success | cycle)`

```python
Num cycles with only trivial edits 192 / 314 = 0.61
Num cycles with missing clues 307 / 314 = 0.98
P( is_success | has_cycle) = 0.33
P( is_success | not_has_cycle) = 0.62
is_success-cycle_num_edges: pearsonr -0.2322847155032073, pvalue 3.22e-05
```

## 3. How to breakout of cycles

Show that students with cycles that are successful have breakout edges, failing
students do not. 'Breakout edges' are edges with substantial edits, i.e. 'a' and 'd'
that occur after the student has been stuck in a cycle of trivial edits for a while.
Intuitively, they represent the student finally understanding that they are missing a
clue.

How many out of successful students with loops have breakout edges? How many don't?

This shows students defeat loops by realizing the missing clue. Providing
feedback of loops via visualization may thus help students succeed in prompting.

```python
P( is_success | has_breakout_edge) = 0.52
P( is_success | not_has_breakout_edge) = 0.45
```


## 4. Form does not matter too much (all about rewrites)

Rewrites do not help model, but help student debug what is wrong with model.

Question: how often does a rewrite lead directly to success node?
`P(success | rewrite)` vs `P(success | no rewrites)`
Answer: not very often.

```python
P(is_success & has_final_rewrite): 0.15
```

how often is a rewrite followed by a substantial edit? And how often
does a rewrite->substatial edit lead to success?

`P(success | rewrite->substatial)`

```python
has final rewrite 109 / 314 = 0.35
P( is_success | rewrite->subst) =  0.55
P( is_success | not_rewrite->subst) = 0.44
```


## RQ5: Memorization+ Instruction Following affects model and student interaction

**TODO**: i have some intuition about this, no results yet.

Here is where we discuss exceptions like `check_prime`, `find_multiples`.

Instruction following:
    - follow student too closely
Memorization:
    - not follow student at all

