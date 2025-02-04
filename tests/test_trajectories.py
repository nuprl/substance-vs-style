from student_trajectories.analysis_utils import (
    remove_students,
    load_graph,
    trim_graph,
    is_any_tag_kind,
    is_known_exception,
    populate_clues,
    load_problem_clues,
    load_problem_answers,
    get_breakout_edge,
    conditional_prob
)
from student_trajectories.student_edge_cases import SUCCESS_NODE_IDS

def test_remove_students():
    g = load_graph(f"student_trajectories/tagging_clues/tagging_graphs_oct9_trimmed/altText.yaml")
    ng = remove_students(g, ["student23"])
    assert len(g.edges)-len(ng.edges) == len(g.get_student_edges()["student23"])
    assert not "student23" in set(ng.get_students())

def test_trim_graph():
    graph = load_graph("student_trajectories/tagging_clues/tagging_graphs_sep27/changeSection.yaml")
    # stuednt 30 has success on attempt 0 but continues until attempt 4
    trimmed_graph = trim_graph(graph, SUCCESS_NODE_IDS["changeSection"])
    assert len(trimmed_graph.edges) <= len(graph.edges)
    student30_edges = graph.get_student_edges()["student30"]
    trimmed_student30_edges = trimmed_graph.get_student_edges().get("student30", [])
    assert len(student30_edges) - len(trimmed_student30_edges) == 3

def test_any_tag_kind():
    assert is_any_tag_kind(["a3","m4"], ["a", "l"])
    assert not is_any_tag_kind([0, "a3"], ["m", "l"])
    assert is_any_tag_kind([0, "a3"], ["0"])

