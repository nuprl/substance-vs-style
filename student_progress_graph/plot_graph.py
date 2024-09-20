"""
Given a clusters.yaml and a trajectories.yaml, plots the progresss graph
for each problem
"""
from tqdm import tqdm
from typing import Union
import argparse
import yaml
import networkx as nx
import os
import matplotlib.pyplot as plt
from collections import defaultdict
# import itertools
import json

def assign_cluster_ids(clusters: list)-> dict:
    legend = {}
    for i,d in enumerate(clusters):
        if isinstance(d, list):
            d = "\n".join(d)
        legend[d] = i
    return legend

def get_node_from_label(graph, target_label):
    for node, data in graph.nodes(data=True):
        if data.get('label') == target_label:
            return node
    raise ValueError(f"Node not found:\n{target_label}")

def problem_graph(G, clusters, trajectories) -> Union[nx.DiGraph, dict]:
    START_NODE_COLOR = "red"
    END_NODE_COLOR = "green"
    STD_NODE_COLOR = "blue"
    COLORS = [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Yellow-green
    ]
    stderr_to_id_dict = assign_cluster_ids(clusters["stderr"])
    stdout_to_id_dict = assign_cluster_ids(clusters["stdout"])
    diffs = []
    for v in trajectories.values():
        diffs.extend(v["diff"])
    diff_to_id_dict = assign_cluster_ids(diffs)
    
    stderr_to_id = (lambda x: stderr_to_id_dict["\n".join(x)])
    stdout_to_id = (lambda x: stdout_to_id_dict["\n".join(x)])
    
    legend = {"nodes": defaultdict(lambda _: {}), 
              "edges": defaultdict(lambda _ : {}), 
              "student_color": defaultdict(lambda _ : {})}
    
    stdout_err_clusters = []
    seen = set()
    for _, student_data in trajectories.items():
        for i,(node_from, node_to) in enumerate(student_data["edges"]):
            if str(node_from) not in seen:
                stdout_err_clusters.append(node_from)
                seen.add(str(node_from))
            if str(node_to) not in seen:
                stdout_err_clusters.append(node_to)
                seen.add(str(node_to))
    
    for i,(stdout,stderr) in enumerate(stdout_err_clusters):
        # add node with ids as label
        label = (stdout_to_id(stdout), stderr_to_id(stderr))

        G.add_node(i, label=label, color=STD_NODE_COLOR)
        legend["nodes"][i] = {"stderr": stderr, "stdout": stdout,
                              "stderr_id": stderr_to_id(stderr), "stdout_id": stdout_to_id(stdout)}
    
    start_nodes = []
    end_nodes = []
    for student, student_data in trajectories.items():
        # student has unique color
        # add edges with arrows, diff ids as label
        color = COLORS.pop()
        legend["student_color"][student] = color
        for i,(node_from_label, node_to_label) in enumerate(student_data["edges"]):
            node_from_label = (stdout_to_id(node_from_label[0]), stderr_to_id(node_from_label[1]))
            node_to_label = (stdout_to_id(node_to_label[0]), stderr_to_id(node_to_label[1]))
            node_from = get_node_from_label(G, node_from_label)
            node_to = get_node_from_label(G, node_to_label)
            edge_id = diff_to_id_dict[student_data["diff"][i]]
            G.add_edge(node_from, node_to, label=edge_id, color=color)
            legend["edges"][edge_id] = student_data["diff"][i]
            if i == len(student_data["edges"]) - 1:
                end_nodes.append(node_to)
            if i == 0:
                start_nodes.append(node_from)
                
    # color start nodes and end nodes
    all_nodes = G.nodes()
    for node in all_nodes:
        if node in start_nodes:
            G.nodes[node]['color'] = START_NODE_COLOR
        if node in end_nodes:
            G.nodes[node]['color'] = END_NODE_COLOR
            
    # # prune graph
    # isolated_nodes = [node for node in G.nodes() if G.degree(node) == 0]
    # G.remove_nodes_from(isolated_nodes)
    # legend["nodes"] = {k:v for k,v in legend["nodes"].items() if k in G.nodes()}
    return G, legend

def main(args):
    with open(args.clusters_yaml,"r") as fp:
        clusters = yaml.safe_load(fp)
    with open(args.trajectories_yaml,"r") as fp:
        trajectories = yaml.safe_load(fp)
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    
    for problem in tqdm(clusters.keys(), desc="Plotting problem"):
        graph = nx.MultiDiGraph()
        graph, legend = problem_graph(graph, clusters[problem], trajectories[problem])
        with open(f"{args.outdir}/{problem}_legend.yaml", "w") as fp:
            yaml.dump(legend, fp)
        with open(f"{args.outdir}/{problem}_legend.json", "w") as fp:
            json.dump(legend, fp, indent=4)

        pos = nx.spring_layout(graph)
        edge_colors = nx.get_edge_attributes(graph, 'color')
        node_color = nx.get_node_attributes(graph, 'color')
        nx.draw(graph,
                pos=pos, 
                with_labels=True, 
                edgelist=graph.edges(),
                node_color=node_color.values(),
                nodelist=graph.nodes(),
                edge_color=edge_colors.values())
        edge_labels = {(u, v): data['label'] for u, v, data in graph.edges(data=True)}
        nx.draw_networkx_edge_labels(graph, pos=pos, edge_labels=edge_labels)
        plt.savefig(f"{args.outdir}/{problem}.pdf")
        graph.clear()
        plt.clf()
    # TODO: all problems in one doc?
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("clusters_yaml")
    parser.add_argument("trajectories_yaml")
    parser.add_argument("outdir")
    args = parser.parse_args()
    main(args)