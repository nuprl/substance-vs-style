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


def edge_tag_to_label(tags):
    if not tags:
        return ""
    l =  ",".join([f"{tag}" for tag in tags])
    if l == "0":
        return ""
    return l


        
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

def get_student_trajectory(student_name: str, start_node_tags: dict[str, str], existing_edges: List[Edge]) -> Tuple[List[UserNode], List[UserEdge]]:
    edges = [edge for edge in existing_edges if edge["username"].replace("student", "s") == student_name]
    edges.sort(key=lambda x: x["attempt_id"])
    first_model_node_id = f"m{edges[0]['node_from']['id']}"
    first_user_node_id = f"u_{student_name}_0"
    
    new_user_nodes =[ UserNode(student_name, first_user_node_id, "initial") ]
    new_user_edges = [ UserEdge(first_user_node_id, first_model_node_id, start_node_tags.get(student_name, "")) ]

    last_model_node_id = first_model_node_id
    for existing_edge in edges:
        next_model_node_id = f"m{existing_edge['node_to']['id']}"
        # We are going to connect the last model node to the next model node and introduce a new user node to do so.
        new_user_node = UserNode(student_name, f"u_{student_name}_{existing_edge['attempt_id']}", existing_edge["state"])
        new_user_nodes.append(new_user_node)
        new_user_edges.append(UserEdge(last_model_node_id, new_user_node.id, ""))
        new_user_edges.append(UserEdge(new_user_node.id, next_model_node_id, edge_tag_to_label(existing_edge["_edge_tags"])))
        last_model_node_id = next_model_node_id

    return new_user_nodes, new_user_edges

def main_with_args(graph_yaml_path: Path, dot_output_path: Path, render: bool):
    graph = load_graph_yaml(graph_yaml_path)
    existing_edges: List[Edge] = graph["edges"]
    start_node_tags = read_start_node_tags(graph)

    model_nodes = create_model_nodes(existing_edges)

    # s0, s1, ...
    student_names: List[str] = list(start_node_tags.keys())
    student_names.sort()

    user_nodes = []
    user_edges = []
    for student_name in student_names:
        new_user_nodes, new_user_edges = get_student_trajectory(student_name, start_node_tags, existing_edges)
        user_nodes.extend(new_user_nodes)
        user_edges.extend(new_user_edges)


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
            f.write(f"  {model_node.id} [shape={shape}, {more_style} label=\"\"];\n")
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
