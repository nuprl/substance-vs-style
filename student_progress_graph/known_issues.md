# Known issues

For problem `exp` and students 39 and 65 `wellesley-easel/StudentEval` test split only has 1 attempt which is
recorded as their last attempt, but no first attempt. Hence this graph is empty (escapes prefiltering).

For problem `readingIceCream` a correct answer can print out either floats eg. 10.0 or 10 integer. Thus,
there are 2 end nodes.