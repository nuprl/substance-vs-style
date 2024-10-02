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


def main_with_args(graph_path: Path, annotations_path: Path):
    graph = load_graph_yaml(graph_path)
    annotations = load_annotations(annotations_path)
    print(len(graph["edges"]))
    print(len(annotations))
    for graph_item, annotation in zip(graph["edges"], annotations):
        graph_item["_edge_tags"] = annotation
    prl_ml.yaml.save_yaml(graph_path, graph)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    args = parser.parse_args()
    main_with_args(args.graph, args.annotations)

if __name__ == "__main__":
    main()

