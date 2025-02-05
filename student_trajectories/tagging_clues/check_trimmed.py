"""
Verify that trimmed graphs are correct
"""
from tqdm import tqdm
import yaml
import sys
from pathlib import Path
from student_trajectories.graph_utils import load_graph
from student_trajectories.student_edge_cases import SUCCESS_NODE_IDS
"""
Compare trimmed and original graphs to make sure no edges were accidentally left out.
If a third arg is passed, then the script will add any left over edges from original->trimmed
and save to that dir.
"""
original = sys.argv[1]
trimmed = sys.argv[2]
if len(sys.argv) == 4:
    trimmed_new = sys.argv[3]
else:
    trimmed_new = None
print("trimmed_new: ", trimmed_new)

PROBLEMS = ['add_int', 'add_up', 'altText', 'assessVowels', 'changeSection', 'check_prime', 
            'combine', 'convert', 'create_list', 'fib', 'findHorizontals', 'find_multiples',
            'generateCardDeck', 'getSeason', 'increaseScore', 'laugh', 'pattern', 'percentWin',
            'planets_mass', 'print_time', 'readingIceCream', 'remove_odd', 'reverseWords',
            'set_chars', 'sortBySuccessRate', 'sort_physicists', 'sortedBooks', 'student_grades',
            'subtract_add', 'times_with', 'topScores', 'total_bill', 'translate']

for p in tqdm(PROBLEMS, disable=True):
    original_graph = load_graph(f"{original}/{p}.yaml")
    trimmed_graph = load_graph(f"{trimmed}/{p}.yaml")
    student_attempts = trimmed_graph.get_student_edges()
    for e in original_graph.edges:
        try:
            edge_list = student_attempts[e.username]
        except:
            if trimmed_new:
                # insert missing student
                assert original_graph.nodes == trimmed_graph.nodes
                # insert start tags
                start_tags = original_graph.student_start_node_tags[e.username]
                trimmed_graph.student_start_node_tags[e.username] = start_tags
                # insert edges
                edges = original_graph.get_student_edges()[e.username]
                trimmed_graph.edges += edges
                student_attempts = trimmed_graph.get_student_edges()
            else:
                print(f"Not found {e.username} in {p}")
                continue
        # if there are missing edges, check the max attempt is a successs node
        # these are correctly trimmed-- the student reached succ node and then kept playing
        if e.attempt_id not in [i.attempt_id for i in student_attempts[e.username]]:
            max_id = max(student_attempts[e.username], key=lambda x: x.attempt_id).node_to.id
            assert max_id == SUCCESS_NODE_IDS[p], (p, e.username,max_id, "succ node:", SUCCESS_NODE_IDS[p])

        # save augmented graph if needed
        if trimmed_new:
            with open(f"{trimmed_new}/{p}.yaml","w") as fp:
                yaml.dump(trimmed_graph, fp)