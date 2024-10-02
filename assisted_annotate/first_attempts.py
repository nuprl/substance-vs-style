from pathlib import Path
import yaml
import re
from tqdm.auto import tqdm
import prl_ml.yaml
import argparse

class IgnoreUnknownTagLoader(yaml.SafeLoader):
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
    



def extract(graph_path: Path, first_attempts_path: Path):
    graph = load_graph_yaml(graph_path)
    edges = graph["edges"]
    first_edges = [ edge for edge in edges if edge["attempt_id"] == 1]
    results = { }
    for e in first_edges:
        results[e["username"]] = {
            "prompt": e["prompt_from"],
            "tags": [ 0 ]
        }
    prl_ml.yaml.save_yaml(first_attempts_path, results)



def patchback(graph_path: Path, first_attempts_path: Path):
    # Load the original graph
    graph = load_graph_yaml(graph_path)
    edges = graph["edges"]

    # Load the first attempts data
    first_attempts = prl_ml.yaml.load_yaml(first_attempts_path)

    # Add student_start_node_tags at the end of the graph
    graph["student_start_node_tags"] = {
        username: data["tags"]
        for username, data in first_attempts.items()
    }

    # Save the updated graph
    with graph_path.open('w') as f:
        yaml.dump(graph, f, default_flow_style=False)



def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    extract_parser = subparsers.add_parser('extract')
    extract_parser.add_argument("--graph", type=Path, required=True)
    extract_parser.add_argument("--first-attempts", type=Path, required=True)
    patchback_parser = subparsers.add_parser('patchback')
    patchback_parser.add_argument("--graph", type=Path, required=True)
    patchback_parser.add_argument("--first-attempts", type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'extract':
        extract(args.graph, args.first_attempts)
    elif args.command == 'patchback':
        patchback(args.graph, args.first_attempts)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()

