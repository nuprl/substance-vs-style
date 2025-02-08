from copy import deepcopy
from student_trajectories.graph import Graph,Node,Edge
from student_trajectories.analysis_utils import (
    remove_students,
    load_graph,
    trim_graph,
    is_any_tag_kind,
    populate_clues,
    ContinuityError,
    get_breakout_edge,
    check_cycles
)
import networkx as nx
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


def test_populate_clues():
    nodes = [Node.dummy_node(i).__dict__ for i in range(5)]
    dummy_edge_details = {k: f"_{k}_" for k in ["prompt_from", "prompt_to", "completion_from", "completion_to", "diff"]}
    g = Graph.from_dict({
        "nodes": nodes,
        "edges": [
            {"node_from": nodes[0], "node_to": nodes[1], "_edge_tags": ["m1"], "state": "neutral",
                            "username": "student1", "attempt_id": 0, "total_attempts": 3, **dummy_edge_details},
            {"node_from": nodes[1], "node_to": nodes[3], "_edge_tags": [0], "state": "neutral",
                            "username": "student1", "attempt_id": 1, "total_attempts": 3, **dummy_edge_details},
            {"node_from": nodes[3], "node_to": nodes[4], "_edge_tags": ["a3"], "state": "success",
                            "username": "student1", "attempt_id": 2, "total_attempts": 3, **dummy_edge_details},
            {"node_from": nodes[3], "node_to": nodes[2], "_edge_tags": ["a2"], "state": "fail",
                            "username": "student2", "attempt_id": 0, "total_attempts": 1, **dummy_edge_details},
        ],
        "student_start_node_tags": {"student1": [1,2], "student2": [1]},
        "clues": [1,2,3],
        "problem": "Dummy_problem"
    })
    expected = Graph.from_dict({
        "nodes": nodes,
        "edges": [
            {"node_from": nodes[0], "node_to": nodes[1], "_edge_tags": ["m1"], "state": "neutral", "clues": [1,2],
                            "username": "student1", "attempt_id": 0, "total_attempts": 3, **dummy_edge_details},
            {"node_from": nodes[1], "node_to": nodes[3], "_edge_tags": [0], "state": "neutral", "clues": [1,2],
                            "username": "student1", "attempt_id": 1, "total_attempts": 3, **dummy_edge_details},
            {"node_from": nodes[3], "node_to": nodes[4], "_edge_tags": ["a3"], "state": "success", "clues": [1,2,3],
                            "username": "student1", "attempt_id": 2, "total_attempts": 3, **dummy_edge_details},
            {"node_from": nodes[3], "node_to": nodes[2], "_edge_tags": ["a2"], "state": "fail", "clues": [1, 2],
                            "username": "student2", "attempt_id": 0, "total_attempts": 1, **dummy_edge_details},
        ],
        "student_start_node_tags": {"student1": [1,2], "student2": [1]},
        "clues": [1,2,3],
        "problem": "Dummy_problem"
    })
    new_g = populate_clues(deepcopy(g))
    assert new_g.__dict__["edges"] == expected.__dict__["edges"]
    assert new_g.__dict__["edges"] != g.__dict__["edges"]

    g.student_start_node_tags["student2"] = [1,2]
    try:
        populate_clues(deepcopy(g))
        assert False
    except ContinuityError:
        assert True

def test_get_breakout_edge():
    nodes = [Node.dummy_node(i).__dict__ for i in range(5)]
    dummy_edge_details = {k: f"_{k}_" for k in ["prompt_from", "prompt_to", "completion_from", "completion_to", "diff"]}
    g = Graph.from_dict({
        "nodes": nodes,
        "edges": [
            {"node_from": nodes[0], "node_to": nodes[1], "_edge_tags": ["m1"], "state": "neutral",
                            "username": "student1", "attempt_id": 0, "total_attempts": 4, **dummy_edge_details},
            {"node_from": nodes[1], "node_to": nodes[3], "_edge_tags": [0], "state": "neutral",
                            "username": "student1", "attempt_id": 1, "total_attempts": 4, **dummy_edge_details},
            {"node_from": nodes[3], "node_to": nodes[0], "_edge_tags": ["l1"], "state": "neutral",
                            "username": "student1", "attempt_id": 2, "total_attempts": 4, **dummy_edge_details},
            {"node_from": nodes[0], "node_to": nodes[2], "_edge_tags": ["a2"], "state": "fail",
                            "username": "student1", "attempt_id": 3, "total_attempts": 4, **dummy_edge_details},
        ],
        "student_start_node_tags": {"student1": [1,2]},
        "clues": [1,2,3],
        "problem": "fib" # clues=[1,2,3]
    })
    cycle_summary = check_cycles(g, suppress_check=True)
    b_edge = get_breakout_edge(g, "student1", cycle_summary["student1"][0])
    assert b_edge == Edge.from_dict({"node_from": nodes[0], "node_to": nodes[2], "_edge_tags": ["a2"], "state": "fail",
                            "username": "student1", "attempt_id": 3, "total_attempts": 4, **dummy_edge_details})
    g = Graph.from_dict({
        "nodes": nodes,
        "edges": [
            {"node_from": nodes[0], "node_to": nodes[1], "_edge_tags": ["m1"], "state": "neutral",
                            "username": "student1", "attempt_id": 0, "total_attempts": 4, **dummy_edge_details},
            {"node_from": nodes[1], "node_to": nodes[3], "_edge_tags": [0], "state": "neutral",
                            "username": "student1", "attempt_id": 1, "total_attempts": 4, **dummy_edge_details},
            {"node_from": nodes[3], "node_to": nodes[0], "_edge_tags": ["l1"], "state": "neutral",
                            "username": "student1", "attempt_id": 2, "total_attempts": 4, **dummy_edge_details},
            {"node_from": nodes[0], "node_to": nodes[1], "_edge_tags": ["a2"], "state": "fail",
                            "username": "student1", "attempt_id": 3, "total_attempts": 4, **dummy_edge_details},
        ],
        "student_start_node_tags": {"student1": [1,2]},
        "clues": [1,2,3],
        "problem": "fib"
    })
    cycle_summary = check_cycles(g, suppress_check=True)
    b_edge = get_breakout_edge(g, "student1", cycle_summary["student1"][0])
    assert b_edge == None
    