import glob
import argparse
import os
from .analysis_utils import load_graph, trim_graph
from .analysis_data import SUCCESS_NODE_IDS
import yaml
from tqdm import tqdm

def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    for graph_yaml in tqdm(glob.glob(f"{args.graph_dir}/*.yaml")):
        # only do tagged graphs
        graph_name = os.path.basename(graph_yaml).replace(".yaml","")
        if graph_name not in SUCCESS_CLUES.keys():
            print(f"Skipping {graph_name}")
            continue
        graph = load_graph(graph_yaml)
        graph = trim_graph(graph, SUCCESS_NODE_IDS[graph.problem])
        with open(f"{args.outdir}/{graph.problem}.yaml", "w") as fp:
            yaml.dump(graph, fp)

        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_dir")
    parser.add_argument("outdir")
    args = parser.parse_args()
    main(args)