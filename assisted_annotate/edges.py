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
    

def extract_yaml_block(s: str):
    # Find the start and end of the YAML block
    start = s.find('```yaml')
    end = s.find('```', start + 7)  # Start searching after '```yaml'
    
    if start != -1 and end != -1:
        # Extract the content between the delimiters
        yaml_content = s[start + 7:end].strip()
        return yaml_content
    else:
        # Return None or an empty string if no YAML block is found
        return None

def load_annotations(path: Path):
    y = prl_ml.yaml.load_yaml(path)
    results = [ ]
    try:
        for ix, item in enumerate(y):
            content = item["_response"]
            # Extract the code in ```yaml blocks
            content = extract_yaml_block(content)
            assert content is not None
            results.append(prl_ml.yaml.load_yaml_string(content))
    except Exception as e:
        print(f"Error on line {ix + 1}: {e}")
        raise
    return results


def patchback(graph_path: Path, annotations_path: Path):
    graph = load_graph_yaml(graph_path)
    annotations = load_annotations(annotations_path)
    print(len(graph["edges"]))
    print(len(annotations))
    for graph_item, annotation in zip(graph["edges"], annotations):
        graph_item["_edge_tags"] = annotation
    prl_ml.yaml.save_yaml(graph_path, graph)

def extract_edges(graph_path: Path, edges_path: Path):
    graph = load_graph_yaml(graph_path)
    edges = graph["edges"]
    # Extract only the required fields from each edge
    extracted_edges = []
    for edge in edges:
        extracted_edge = {
            "prompt_from": edge.get("prompt_from"),
            "prompt_to": edge.get("prompt_to"),
            "attempt_id": edge.get("attempt_id"),
            "username": edge.get("username")
        }
        extracted_edges.append(extracted_edge)
    
    # Replace the original edges with the extracted ones
    edges = extracted_edges
    prl_ml.yaml.save_yaml(edges_path, edges)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    patchback_parser = subparsers.add_parser('patchback')
    patchback_parser.add_argument("--graph", type=Path, required=True)
    patchback_parser.add_argument("--annotations", type=Path, required=True)
    
    extract_parser = subparsers.add_parser('extract')
    extract_parser.add_argument("--graph", type=Path, required=True)
    extract_parser.add_argument("--annotations", type=Path, required=True)
    
    args = parser.parse_args()
    
    if args.command == 'patchback':
        patchback(args.graph, args.annotations)
    elif args.command == 'extract':
        extract_edges(args.graph, args.annotations)
    else:
        raise ValueError(f"Unknown command: {args.command}")
if __name__ == "__main__":
    main()

