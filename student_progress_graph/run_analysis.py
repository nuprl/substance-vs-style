import json
import argparse
'''
Analyzing common patterns in graphs
Hypotheses:
1. edges between two nodes are the same diffs (including self-loops) 
2. a diff either adds a clue, deletes a clue, does nothing (trivial rephrase) or does both
3.  a cycle forms when the student does not add a necessary clue or deketes one in favor of another clue,
but both are needed
4. a long path indicates trivial rewrites and/or missing clues
5. the most efficient paths progressively add clues
6. adding clues at the start or end of a prompt is significant

Experiments to prove these
1. td-idf clustering: cluster edge diffs. See that they correspond to number of unique edges
'''
def main(*args):
    pass

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph-json")
    args = parser.parse_args()
    main(args)