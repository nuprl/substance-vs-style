# Analyzing common patterns in graphs

## Hypotheses:
0. self-loops are trivial information, no significant code change [X]
1. edges between two nodes are the same diffs (including self-loops) [FAIL]
    - different changes lead to same outcome
    - maybe these edges are all missing something?
2. a diff either adds a clue, deletes a clue, does nothing (trivial rephrase) or does both [X]

3. a cycle forms when the student does not add a necessary clue or deletes one in favor of another clue,but both are needed
4. a long path indicates trivial rewrites and/or missing clues
5. the most efficient paths progressively add clues
6. adding clues at the start or end of a prompt is significant

## Methodolody:

for each problem
1. create a set of clues required to solve
2. annotate each edge with clues added or missing
3. annotate start nodes with clues present


## Talking points

- student prompt either add, delete or modify a clue
    - this and sampling determines state transition
    - if a clue is missing, you will not get correct answer (even with resampling) [TODO]
        - check if any 0 edges leading to success are missing clues
- students loop when missing a detail, engage in trivial re-writes [TODO]
    shorten loop by providing hint that missing detail
    - students are more likely to give up when they perceive loops, vs a linear path
- rewrites do not help
    - plot distinct success trace, fail trace
    
- adding clues to start vs end
