"""
The graphs that we read are multigraphs. This code changes their representation into graphs with two different types of
nodes as follows.

1. Existing nodes become "model" nodes labelled with their node ID (from the existing node) and prefixed with "m".
2. Existing edges become "user" nodes. The label on these nodes is the username from the edge and a unique ID prefixed with "u".
3. We create two new edges for every existing edge:
   - One goes from the "model" node for the "from" node to the "user" node.
   - One goes from the "user" node to the "model" node for the "to" node.

We also add a special "start" node (TODO).
"""
from pathlib import Path
import yaml
import re
from tqdm.auto import tqdm
from collections import defaultdict
from typing import TypedDict, List, Set, NamedTuple, Tuple, Optional
import subprocess
import argparse


class IgnoreUnknownTagLoader(yaml.SafeLoader):
    """
    Ignores the custom constructors in the YAML file
    """
    def ignore_unknown(self, suffix, node):
        if isinstance(node, yaml.MappingNode):
            return self.construct_mapping(node)
        elif isinstance(node, yaml.SequenceNode):
            return self.construct_sequence(node)
        else:
            return self.construct_scalar(node)

IgnoreUnknownTagLoader.add_multi_constructor('', IgnoreUnknownTagLoader.ignore_unknown)

def load_graph_yaml(path: Path):
    with path.open() as f:
        return yaml.load(f, Loader=IgnoreUnknownTagLoader)

# There is more in a node, but this is all we need.
class Node(TypedDict):
    id: int
    state: str


# There is more in an edge, but this is all we need.
class Edge(TypedDict):
    node_from: Node
    node_to: Node
    username: str
    _edge_tags: list[str]
    state: str

class ModelNode(NamedTuple):
    id: str
    state: str

class UserNode(NamedTuple):
    username: str
    id: str
    state: str

class UserEdge(NamedTuple):
    from_node_id: str
    to_node_id: str
    text: str


def create_model_node(node: Node, edge: Edge) -> ModelNode:
    if edge["node_to"]["id"] == node["id"]:
        return ModelNode(f"m{node['id']}", edge["state"])
    else:
        return ModelNode(f"m{node['id']}", "")

def create_model_nodes(edges: List[Edge]) -> Set[ModelNode]:
    from_node_ids = {edge["node_from"]["id"] for edge in edges}
    to_node_ids = {edge["node_to"]["id"] for edge in edges}
    all_node_ids = from_node_ids.union(to_node_ids)
    node_states = defaultdict(lambda: "")
    
    for edge in edges:
        node_states[edge["node_to"]["id"]] = edge["state"]

    model_nodes = set(ModelNode(f"m{node_id}", node_states[node_id]) for node_id in all_node_ids)
    return model_nodes

def create_user_nodes_and_edges(edges: List[Edge]) -> Tuple[List[UserNode], List[UserEdge]]:
    user_nodes = []
    user_edges = []
    for user_node_num, edge in enumerate(edges):
        from_node_num = edge["node_from"]["id"]
        to_node_num = edge["node_to"]["id"]
        user_node_id = f"u{user_node_num}"
        user_node = UserNode(edge["username"].replace("student", "s"), user_node_id, edge["state"])
        user_nodes.append(user_node)
        label = ",".join([f"{tag}" for tag in edge["_edge_tags"]]) if edge["_edge_tags"] else "0"
        if label == "0":
            label = ""
        user_edges.append(UserEdge(f"m{from_node_num}", user_node_id, ""))
        user_edges.append(UserEdge(user_node_id, f"m{to_node_num}", label))
    return user_nodes, user_edges

# For each user, we find the model node that is the first to transition to it.
# Specifically, if a model node has an edge out for a user and no edge in for
# that user, then that model node is the first to transition to it.
def get_first_model_node_for_user(user_nodes: List[UserNode], user_edges: List[UserEdge], model_nodes: Set[ModelNode]) -> List[Tuple[str, ModelNode]]:
    first_model_nodes = []
    for model_node in model_nodes:
        # Find all the node IDs that transition to this model node
        from_user_node_ids = [edge.from_node_id for edge in user_edges if edge.to_node_id == model_node.id]
        # Find all the node IDs that transition from this model node
        to_user_node_ids = [edge.to_node_id for edge in user_edges if edge.from_node_id == model_node.id]


        from_users = {user_node.username for user_node in user_nodes if user_node.id in from_user_node_ids}
        to_users = {user_node.username for user_node in user_nodes if user_node.id in to_user_node_ids}
        # This is the first model node for the difference
        delta = list(set(to_users) - set(from_users))
        for user in delta:
            first_model_nodes.append((user, model_node))
    return first_model_nodes
        
def read_start_node_tags(graph: dict) -> dict[str, str]:
    start_node_tags = graph["student_start_node_tags"]
    results = { }
    for student, tags in start_node_tags.items():
        user = student.replace("student", "s")
        if not tags:
            tags = [0]
        label = ",".join([f"a{tag}" for tag in tags])
        if label == "a0":
            label = ""
        results[user] = label
    return results

def main_with_args(graph_yaml_path: Path, dot_output_path: Path, render: bool):
    graph = load_graph_yaml(graph_yaml_path)
    existing_edges: List[Edge] = graph["edges"]
    start_node_tags = read_start_node_tags(graph)
    model_nodes = create_model_nodes(existing_edges)

    user_nodes, user_edges = create_user_nodes_and_edges(existing_edges)
    first_model_nodes = get_first_model_node_for_user(user_nodes, user_edges, model_nodes)
    for (user, first_model_node) in first_model_nodes:
        n = UserNode(user, f"u_{user}", "initial")
        user_nodes.append(n)   
        user_edges.append(UserEdge(n.id, first_model_node.id, start_node_tags.get(user, "")))


    with dot_output_path.open("w") as f:
        f.write("digraph G {\n")
        for model_node in model_nodes:
            if model_node.state == "success":   
                shape = "doublecircle"
                more_style = 'color = "green", style = "filled",'
            elif model_node.state == "initial":
                shape = "circle"
                more_style = 'shape = "circle", style = "dashed",'
            else:
                shape = "circle"
                more_style = ""
            f.write(f"  {model_node.id} [shape={shape}, {more_style} label=\"{model_node.id}\"];\n")
        # Label the user nodes with their username
        for user_node in user_nodes:
            if user_node.state == "fail":
                more_style = 'color = "red", style = "filled",'
            elif user_node.state == "initial":
                more_style = 'style = "dashed",'
            elif user_node.state == "success":
                more_style = 'color = "green", style = "filled",'
            else:
                more_style = ""
            f.write(f"  {user_node.id} [shape=diamond, {more_style} label=\"{user_node.username}\"];\n")
        for user_edge in user_edges:
            f.write(f"  {user_edge.from_node_id} -> {user_edge.to_node_id} [label=\"{user_edge.text}\"];\n")
        f.write("}\n")


    pdf_output_path = dot_output_path.with_suffix(".pdf")
    if render:
        subprocess.run(["dot", "-Tpdf", dot_output_path, "-o", pdf_output_path])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml", type=Path)
    parser.add_argument("--dot-output", type=Path)
    
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()

    if args.dot_output is None:
        args.dot_output = args.graph_yaml.with_suffix(".dot")
    main_with_args(args.graph_yaml, args.dot_output, args.render)  

if __name__ == "__main__":
    main()
