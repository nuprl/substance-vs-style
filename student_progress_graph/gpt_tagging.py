
import yaml
import argparse
import os
from graph_utils import load_graph

PROMPT = """
Given
"""

def main(args):
    API_KEY = os.environ["OPENAI_API_KEY"]
    graph = load_graph(args.graph_yaml)
    with open(args.problem_tags_yaml, "r") as fp:
        tags = yaml.safe_load(fp)[graph.problem]
    
    
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml")
    parser.add_argument("problem_tags_yaml")
    parser.add_argument("outdir")
    args = parser.parse_args()
    main(args)