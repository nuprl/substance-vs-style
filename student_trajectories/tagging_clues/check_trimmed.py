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
"""
original = sys.argv[1]
trimmed = sys.argv[2]

PROBLEMS = ['add_int', 'add_up', 'altText', 'assessVowels', 'changeSection', 'check_prime', 
            'combine', 'convert', 'create_list', 'fib', 'findHorizontals', 'find_multiples',
            'generateCardDeck', 'getSeason', 'increaseScore', 'laugh', 'pattern', 'percentWin',
            'planets_mass', 'print_time', 'readingIceCream', 'remove_odd', 'reverseWords',
            'set_chars', 'sortBySuccessRate', 'sort_physicists', 'sortedBooks', 'student_grades',
            'subtract_add', 'times_with', 'topScores', 'total_bill', 'translate']

for p in tqdm(PROBLEMS):
    original_graph = load_graph(f"{original}/{p}.yaml")
    trimmed_graph = load_graph(f"{trimmed}/{p}.yaml")
    student_attempts = trimmed_graph.get_student_edges()
    for e in original_graph.edges:
        try:
            edge_list = student_attempts[e.username]
        except:
            first_edge = sorted(original_graph.get_student_edges()[e.username], key=lambda x: x.attempt_id)[0]
            if first_edge.node_from.id != SUCCESS_NODE_IDS[p]:
                print(f"Not found {e.username} in {p}")
            continue
        # if there are missing edges, check the max attempt is a successs node
        # these are correctly trimmed-- the student reached succ node and then kept playing
        if e.attempt_id not in [i.attempt_id for i in student_attempts[e.username]]:
            max_id = max(student_attempts[e.username], key=lambda x: x.attempt_id).node_to.id
            assert max_id == SUCCESS_NODE_IDS[p], (p, e.username,max_id, "succ node:", SUCCESS_NODE_IDS[p])