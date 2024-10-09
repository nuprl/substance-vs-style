import glob
import argparse
import os
from .analysis_data import SUCCESS_NODE_IDS, SUCCESS_CLUES
from .graph_utils import load_graph
from tqdm import tqdm

def main(args):
    graphs = []
    for graph_yaml in tqdm(glob.glob(f"{args.graph_dir}/*.yaml")):
        # discard any that we have not verified yet
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if graph_name not in SUCCESS_CLUES.keys():
            continue
        graph = load_graph(graph_yaml)
        success_node_id = SUCCESS_NODE_IDS[graph.problem]
        for i,e in enumerate(graph.edges):
            if e.node_to.id == success_node_id and e.state == "fail":
                print(f"False fail {graph.problem}, {e.node_from.id}->{e.node_to.id}, {e.username}")
            elif e.state == "success" and e.node_to.id != success_node_id:
                print(f"False success {graph.problem}, {e.node_from.id}->{e.node_to.id}, {e.username}")
            elif e.state == "neutral" and (e.node_to.id == success_node_id or e.node_from.id == success_node_id):
                print(f"False neutral {graph.problem}, {e.node_from.id}->{e.node_to.id}, {e.username}")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_dir")
    args = parser.parse_args()
    main(args)