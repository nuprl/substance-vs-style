# Note on naming

A 'trimmed' graph refers to a graph where students reach success early, but keep messing around. The
edges after the initial success have been trimmed.

# Problem graphs

*NOTE*: please read this whole document :).

We can visualize student progress on each StudentEval problem as a graph where:

- **nodes** correspond to the set of unique `(stdout, stderr)` pairs observed in
    the Codex2 generated functions for that problem. 
    The intuition behind this is:
        - we can look at what each prompt got right/wrong by looking at the generated function
        - we can look at what the generated function got right/wrong by looking at the `(stdout, stderr)` output
    Thus, by the transitive property, we can group and classify student prompts by 
    looking at outputs. Importantly, there is a finite, **limited**
    set of outputs, which makes our lives easier. Within the set of nodes, 
    only one node is the **success node** which all successful students terminate in.

- **edges** correspond to an edit that a student made in order to progress from node `u` to
    node `v`.

- **paths**. Each student that attempts a problem draws path through the graph. For example,
    here is a (simplified) representation of edge1 and edge2 in `student38`'s path in `add_up`.
    Pay attention to the fields `attempt_id`, `total_attempts`, `completion_from`, `completion_to`, 
    `node_from`, `node_to`, `prompt_from`, `prompt_to`, `diff`

```yaml
- !Edge
  node_from: !Node
    id: 6
    stdout:
    - '[''hello5'', ''aaa5'', ''bbb5'', ''ccc5'', 6, 9]

        '
    - '[9, 57, 9, ''51'', ''41'']

        '
    - ''
    stderr:
    - ''
    - ''
    - 'TypeError: can only concatenate list (not "int") to list'
  node_to: !Node
    id: 1
    stdout:
    - '[''hello5'', ''aaa5'', ''bbb5'', ''ccc5'', 6, 9]

        '
    - '[9, 57, 9, ''51'', ''41'']

        '
    - '[''hello5'', ''aaa5'', ''bbb5'', [''list''], 6, 9]

        '
    stderr:
    - ''
    - ''
    - ''
  username: student38
  prompt_from: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. Return\
    \ the new lst. \n    \"\"\"\n    "
  prompt_to: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. Else,\
    \ return position. Return the new lst. \n    \"\"\"\n    "
  completion_from: "new_lst = []\n    for i in lst:\n        if type(i) == str:\n\
    \            new_lst.append(i + str(num))\n        else:\n            new_lst.append(i\
    \ + num)\n    return new_lst\n\nprint(add_int([1, 2, 3], 4))\nprint(add_int([\"\
    a\", \"b\", \"c\"], 4))\nprint"
  completion_to: "new_lst = []\n    for i in lst:\n        if type(i) == str:\n  \
    \          new_lst.append(i + str(num))\n        elif type(i) == int:\n      \
    \      new_lst.append(i + num)\n        else:\n            new_lst.append(i)\n\
    \    return new_lst\n\nprint(add_int(['a', 'b',"
  diff: "--- \n+++ \n@@ -22,6 +22,9 @@\n num to integer.+Else,+return+position. Return\
    \ the new"
  attempt_id: 1
  total_attempts: 4
  state: neutral
  _edge_tags: null
- !Edge
  node_from: !Node
    id: 1
    stdout:
    - '[''hello5'', ''aaa5'', ''bbb5'', ''ccc5'', 6, 9]

        '
    - '[9, 57, 9, ''51'', ''41'']

        '
    - '[''hello5'', ''aaa5'', ''bbb5'', [''list''], 6, 9]

        '
    stderr:
    - ''
    - ''
    - ''
  node_to: !Node
    id: 4
    stdout:
    - '[''hello5'', ''aaa5'', ''bbb5'', ''ccc5'', 6, 9]

        '
    - '[9, 57, 9, ''51'', ''41'']

        '
    - '[''hello5'', ''aaa5'', ''bbb5'', [''list'', 5], 6, 9]

        '
    stderr:
    - ''
    - ''
    - ''
  username: student38
  prompt_from: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. Else,\
    \ return position. Return the new lst. \n    \"\"\"\n    "
  prompt_to: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. If\
    \ position in lst is list, add list to lst. Return the new lst. \n    \"\"\"\n\
    \    "
  completion_from: "new_lst = []\n    for i in lst:\n        if type(i) == str:\n\
    \            new_lst.append(i + str(num))\n        elif type(i) == int:\n    \
    \        new_lst.append(i + num)\n        else:\n            new_lst.append(i)\n\
    \    return new_lst\n\nprint(add_int(['a', 'b',"
  completion_to: "new_lst = []\n    for item in lst:\n        if type(item) == str:\n\
    \            new_lst.append(item + str(num))\n        elif type(item) == int:\n\
    \            new_lst.append(item + num)\n        elif type(item) == list:\n  \
    \          new_lst.append(item + [num])\n    return new_lst\n"
  diff: "--- \n+++ \n@@ -22,9 +22,16 @@\n num to integer.-Else,-return-position.+If+position+in+lst+is+list,+add+list+to+lst.\
    \ Return the new"
  attempt_id: 2
  total_attempts: 4
  state: neutral
  _edge_tags: null
```
This is much more pleasantly visualized as a figure, but for tagging this format should be sufficient.

By analyzing the paths in each graph problem, we draw conclusions on student behaviors. For example,
we see that in certain problems students are more likely to get stuck in cycles.

The graph representation allows us to ask questions like:

- how do students break out of loops?
- does rewriting with more/less detail (condensing) help?
- how does a student debug their prompt?

However, in order to answer these questions and talk generally about student strategies without pulling
up specific prompts, we need to further group student edits. This means tagging each edge (or enough edges, until
we have sufficient proof for our hypotheses [see hypotheses section]).

## Strategy for tagging edges

You will be using the above yaml format to add edge tags in the empty `_edge_tags` field.

What are the tags? Tags are problem specific `clues` that the model needs to receive in order to solve
a problem. You can see some clues I started drafting in `problem_clues.yaml`. For example, `add_int`:

```yaml
add_int:
  signature: 'def add_int(lst, num):'
  tags:
    # do nothing to list, can have list of lists
  - 1: edge case of list in list
  # this is the variable num
  - 2: concatenate num to strings
  - 3: add num to integers
  - 4: return list
tests:
  - input: '[''hello'', ''aaa'', ''bbb'', ''ccc'', 1, 4], 5'
    output: '[''hello5'', ''aaa5'', ''bbb5'', ''ccc5'', 6, 9]'
  - input: '[8, 56, 8, ''5'', ''4''], 1'
    output: '[9, 57, 9, ''51'', ''41'']'
  - input: '[''hello'', ''aaa'', ''bbb'', [''list''], 1, 4], 5'
    output: '[''hello5'', ''aaa5'', ''bbb5'', [''list''], 6, 9]'
working_description: Given a list lst of strings and integers and integer num, concatenates
    num to the end of strings in lst and adds it to integers in lst.
```

I made these clues by looking at test cases and the working description of the function. As I was
tagging, I also updated clues to reflect patterns I noticed. Here is how I tagged the student38 
edges above.

```yaml
- !Edge
  node_from: *id004
  node_to: *id002
  username: student38
  prompt_from: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. Return\
    \ the new lst. \n    \"\"\"\n    "
  prompt_to: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. Else,\
    \ return position. Return the new lst. \n    \"\"\"\n    "
  completion_from: "new_lst = []\n    for i in lst:\n        if type(i) == str:\n\
    \            new_lst.append(i + str(num))\n        else:\n            new_lst.append(i\
    \ + num)\n    return new_lst\n\nprint(add_int([1, 2, 3], 4))\nprint(add_int([\"\
    a\", \"b\", \"c\"], 4))\nprint"
  completion_to: "new_lst = []\n    for i in lst:\n        if type(i) == str:\n  \
    \          new_lst.append(i + str(num))\n        elif type(i) == int:\n      \
    \      new_lst.append(i + num)\n        else:\n            new_lst.append(i)\n\
    \    return new_lst\n\nprint(add_int(['a', 'b',"
  diff: "--- \n+++ \n@@ -22,6 +22,9 @@\n num to integer.+Else,+return+position. Return\
    \ the new"
  attempt_id: 1
  total_attempts: 4
  state: neutral
  _edge_tags:
  - a1
- !Edge
  node_from: *id002
  node_to: *id005
  username: student38
  prompt_from: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. Else,\
    \ return position. Return the new lst. \n    \"\"\"\n    "
  prompt_to: "def add_int(lst, num):\n    \"\"\"\n    If position in lst is string,\
    \ append num to string. If position in lst is integer, add num to integer. If\
    \ position in lst is list, add list to lst. Return the new lst. \n    \"\"\"\n\
    \    "
  completion_from: "new_lst = []\n    for i in lst:\n        if type(i) == str:\n\
    \            new_lst.append(i + str(num))\n        elif type(i) == int:\n    \
    \        new_lst.append(i + num)\n        else:\n            new_lst.append(i)\n\
    \    return new_lst\n\nprint(add_int(['a', 'b',"
  completion_to: "new_lst = []\n    for item in lst:\n        if type(item) == str:\n\
    \            new_lst.append(item + str(num))\n        elif type(item) == int:\n\
    \            new_lst.append(item + num)\n        elif type(item) == list:\n  \
    \          new_lst.append(item + [num])\n    return new_lst\n"
  diff: "--- \n+++ \n@@ -22,9 +22,16 @@\n num to integer.-Else,-return-position.+If+position+in+lst+is+list,+add+list+to+lst.\
    \ Return the new"
  attempt_id: 2
  total_attempts: 4
  state: neutral
  _edge_tags:
  - m1
```

As you can see, by looking at `prompt_from, prompt_to` and `diff`, I tagged the first
edge `a1` and the second `m1`. The number corresponds to clues `1: edge case of list in list`.
The prefix letter is a convention I use to indicate the following useful extra information:

- `a`: student *added* this clue from previous node
- `d`: student *deleted* this clue from previous node
- `l`: student rewrote this clue with *less* detail [can be wrong detail]
- `m`: student rewrote this clue with *more* detail [detail can be wrong detail]

There is also a special tag that is common to all problems, tag `0`, which requires
no prefix because it represents a noop:

- `0`: no difference or trivial rewrite (semantically equivalent rewrite, adds no new clues)

## Examples of tagging

I have completed the problem clues and done all the tagging for `tagging_graphs_sep27/add_up.yaml` 
and `tagging_graphs_sep27/add_int.yaml`. Refer to these as examples.

## Tagging nodes

Of course, tagging edges is not sufficient because the first edge in a student path
comes out of the student's **starting node**, which is attempt 0. This first prompt the
student used is their start node, which needs to be tagged with the clues the student starts out with.
For each problem, you only need to tag the start node, so one node per student. At the bottom of
the `add_int.yaml` file for example you can find the following start node tags:

```yaml
student_start_node_tags:
  student19:
  - 3
  - 4
  student36:
  - 2
  - 3
  - 4
  student38:
  - 2
  - 3
  - 4
  student42:
  - 2
  - 3
  - 4
  student54:
  - 3
  - 4
  student77:
  - 2
  - 3
  - 4
  ```

I populated this list by looking at `prompt_from` field of the student's `attempt: 1`.

## A note about clues

You should draft clues for a problem in `problem_clues.yaml` first, then start tagging.
Think of it as the 100-level racket rubric that we use at Northeastern. If a student does something
not covered by the rubric (clues), feel free to update the clues.

## Problems to tag

I have filtered out the most interesting problems to tag. Note: I do not expect
us to tag ALL these edges, simply to tag enough until we have substantial proof for
our hypothesis (see hypotheses section). If we do just 3 each, it's already enough data to
start verifying some things.

```
| index |   num start nodes to tag    |   num edges  | problem           |
|------:|----------------------------:|-------------:|:------------------|
|     0 |                          11 |           11 | add_int           |
|     1 |                          13 |           57 | add_up            |
|     2 |                          17 |           25 | altText           |
|     3 |                           7 |           16 | assessVowels      |
|     4 |                          21 |           34 | changeSection     |
|     5 |                           6 |           22 | check_prime       |
|     6 |                          10 |           13 | combine           |
|     7 |                          44 |           79 | convert           |
|     8 |                           6 |            8 | create_list       |
|     9 |                          10 |           22 | fib               |
|    10 |                          16 |           14 | findHorizontals   |
|    11 |                          12 |           20 | find_multiples    |
|    12 |                           9 |           64 | generateCardDeck  |
|    13 |                          18 |           42 | getSeason         |
|    14 |                           8 |           13 | increaseScore     |
|    15 |                          36 |           67 | laugh             |
|    16 |                          11 |           14 | pattern           |
|    17 |                          16 |           33 | percentWin        |
|    18 |                          18 |           25 | planets_mass      |
|    19 |                          12 |           16 | print_time        |
|    20 |                          17 |           32 | readingIceCream   |
|    21 |                           7 |           47 | remove_odd        |
|    22 |                           7 |           18 | reverseWords      |
|    23 |                          10 |           18 | set_chars         |
|    24 |                          23 |           30 | sortBySuccessRate |
|    25 |                          12 |           23 | sort_physicists   |
|    26 |                          14 |           24 | sortedBooks       |
|    27 |                          13 |            9 | student_grades    |
|    28 |                          20 |           25 | subtract_add      |
|    29 |                          18 |           28 | times_with        |
|    30 |                           5 |           68 | topScores         |
|    31 |                          10 |           22 | total_bill        |
|    32 |                           9 |           12 | translate         |
```

totals: 33 problems, 314 start nodes, 951 edges

avg num nodes to tag per problem: 23

avg num edges to tag per problem: 56

## Hypotheses/ Claims for paper

0. student prompts either add, delete or modify a clue. These edits and resampling
is what determines state transition.

We can just assert this by doing the tagging.

1. if a clue is missing, student will not get correct answer

We can easily check this. I have some code that computes the final set of clues
for each student given the start clues + the edge tags. We can compare
the final set to whether a student is successful. Of course, sometimes
some clues turn out to not be strictly necessary for success (for example, clue 1 in
`add_int` is optional-- but we see that students that do not include clue 1 either
have to significantly revise their prompt or their path is much longer).

**NOTE** that for some reason, the original `is_success` field in `wellesley-easel/StudentEval`
can be wrong. I've also seen that some student will continue prompting after reaching
a success. I'm running each assertion test independently, plus hand verifying
the functions, so not sure why this is.

Some other exceptions so far:
- topScores student45: student with all clues gets fail because of LLM runs out of tokens
- add_up student24: incomplete clues is successful because they use python try-except (mention error in prompt)
- add_up student65: all clues is fail because model interprets "number" as int
- add_int student38: mislabeled as fail, actually succeeds in earlier attempts

2. students fall into loops/cycles when they are missing a clue or just doing trivial re-writes

There's good proof of this already. This means that we could provide students with a
warning that they've fallen into a loop, and encourage them to think of what's missing.

3. Student are more likely to give up when they engage in loops

We can check if students are **more likely to give up** when they perceive that they are
stuck in a loop and getting nowhere. (Does length of loop correlate with success rate)

4. rewrites do not help very much

This is a suspicion I have. We can see out of all the successful paths
how many have rewrites. I suspect that even if theres many successful paths with 
rewrites, they are generally are longer. Rewriting with more detail I expect
won't have much effect.
    
5. adding text at the start of a prompt vs at the end matters

Another suspicion I have. We can look at tags and the location of the diffs to determine this.
I think adding text onto the start may be more successful than at the end. This is because of
autoregression.