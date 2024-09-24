"""
Given a clusters.yaml and a trajectories.yaml, plots the progresss graph
for each problem
"""
from re import M
from tqdm import tqdm
from typing import Union
import argparse
import yaml
import sys
import networkx as nx
import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from collections import defaultdict
import itertools
import json
import gravis
import random
import numpy as np
np.random.seed(42)
random.seed(42)

START_NODE_COLOR = "grey"
STD_NODE_COLOR = "blue"
END_NODE_CORR_COLOR = "green"
END_NODE_INC_COLOR = "red"

COLORS = [
    '#d83034', # red
    '#f9e858', # yellow
    '#008dff', # med blue
    '#4ecb8d', # green
    '#c701ff', # purple
    '#ffcd8e', # light orange
    '#003a7d', # dark blue
    '#Ff73b6', # pink
    '#ff7f50', # coral
    '#7fff00', # chartreuse
    '#8a2be2', # blue violet
    '#ffd700', # gold
    '#ff4500', # orange red
    '#00ced1', # dark turquoise
    '#ff1493', # deep pink
    '#9400d3', # dark violet
]
HTML_HEADER="""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>"""

def assign_cluster_ids(clusters: list)-> dict:
    legend = {}
    for i,d in enumerate(clusters):
        if isinstance(d, list):
            d = "\n".join(d)
        legend[d] = i
    return legend

def get_node_from_labels(graph, target_labels: dict):
    for node, data in graph.nodes(data=True):
        if all([data.get(k) == v for k,v in target_labels.items()]):
            return node
    raise ValueError(f"Node not found:\n{target_labels}")

def custom_plt_legend(student_colors:dict):
    custom_lines, labels = [],[]
    for username,color in student_colors.items():
        custom_lines.append(Line2D([0], [0], color=color, lw=4))
        labels.append(username)
    return custom_lines, labels

def problem_graph(G, clusters, trajectories) -> Union[nx.DiGraph, dict]:
    stderr = clusters["stderr"]
    stdout = clusters["stdout"]
    # for reproducibility
    stdout.sort()
    stderr.sort()
    stderr_to_id_dict = assign_cluster_ids(stderr)
    stdout_to_id_dict = assign_cluster_ids(stdout)
    diffs = []
    seen = set()
    for v in trajectories.values():
        for d in v["diff"][1:]: # ignore first trivial None diff
            if d not in seen:
                diffs.append(d)
                seen.add(d)        
        
    diff_to_id_dict = assign_cluster_ids(diffs)
    stderr_to_id = (lambda x: stderr_to_id_dict["\n".join(x)])
    stdout_to_id = (lambda x: stdout_to_id_dict["\n".join(x)])
    
    legend = {"nodes": defaultdict(lambda _: {}), 
              "edges": defaultdict(lambda _ : {}), 
              "student_color": defaultdict(lambda _ : {})}
    
    # build set of nodes based on represented stdout/stderr pairs
    std_out_err_clusters = []
    seen = set()
    for _, student_data in trajectories.items():
        for i,(node_from, node_to) in enumerate(student_data["edges"]):
            # edges are:
            #   node_from: (stdout, stderr)
            #   node_to: (stdout, stderr)
            if str(node_from) not in seen:
                std_out_err_clusters.append(node_from)
                seen.add(str(node_from))
            if str(node_to) not in seen:
                std_out_err_clusters.append(node_to)
                seen.add(str(node_to))
    
    for i,(stdout,stderr) in enumerate(std_out_err_clusters):
        # add node with ids as label
        stderr_id = stderr_to_id(stderr)
        stdout_id = stdout_to_id(stdout)
        stderr_text = "\n".join(stderr)
        if stderr_text.strip() == "":
            stderr_text = "_no_stderr_"
        stdout_text = "\n".join([s for s in stdout if s.strip() != "[]"])
        if stdout_text.strip() == "":
            stdout_text = "_no_stdout_"
        G.add_node(i, 
                   stderr_id=stderr_id, 
                   stdout_id=stdout_id, 
                   hover=f"stdout:\n{stdout_text}\nstderr:\n{stderr_text}",
                   color=STD_NODE_COLOR,)
        legend["nodes"][i] = {
            "stderr": stderr, 
            "stdout": stdout,
            "stderr_id": stderr_id,
            "stdout_id": stdout_id}
    
    start_nodes, end_nodes_succ, end_nodes_fail = [],[], []
    for j,(student_name, student_data) in enumerate(trajectories.items()):
        # student has unique color
        # add edges with arrows, diff ids as label
        color = COLORS[j]
        legend["student_color"][student_name] = color
        for i,(node_from_std, node_to_std) in enumerate(student_data["edges"]):
            node_from = get_node_from_labels(
                G, 
                {"stdout_id":stdout_to_id(node_from_std[0]),
                "stderr_id":stderr_to_id(node_from_std[1])}
            )
            node_to = get_node_from_labels(
                G, 
                {"stdout_id":stdout_to_id(node_to_std[0]),
                "stderr_id":stderr_to_id(node_to_std[1])}
            )
            # diff computed from next node, so diff[0] is always None (first attempt)
            diff = student_data["diff"][i+1]
            edge_label = diff_to_id_dict[diff]
            G.add_edge(
                node_from, 
                node_to, 
                diff=edge_label, 
                color=color,
                arrow_color=color,
                username=student_name,
                hover=f"username:{student_name}\nedge: ({node_from}->{node_to})\ndiff:" + 
                        f"\n{diff}\n\nFROM completion:\n{student_data['prompt'][i]}"+
                        f"    {student_data['completion'][i]}" + 
                        f"\n\nTO completion:\n{student_data['prompt'][i+1]}"+
                        f"    {student_data['completion'][i+1]}")
            legend["edges"][edge_label] = diff
            
            if i == len(student_data["edges"]) - 1:
                if student_data["is_success"][-1]:
                    end_nodes_succ.append(node_to)
                else:
                    end_nodes_fail.append(node_to)
            if i == 0:
                start_nodes.append(node_from)
                
    # color start nodes and end nodes
    all_nodes = G.nodes()
    for node in all_nodes:
        if node in start_nodes:
            G.nodes[node]['color'] = START_NODE_COLOR
        if node in end_nodes_fail:
            G.nodes[node]['color'] = END_NODE_INC_COLOR
        if node in end_nodes_succ:
            G.nodes[node]['color'] = END_NODE_CORR_COLOR
            
    return G, legend

def generate_legend_html(legend_dict):
    legend_items = []
    
    for student, color in legend_dict.items():
        # color = COLORS_TO_HEX[color]
        legend_items.append(f'<div style="display: flex; align-items: center; margin-bottom: 5px;">'
                            f'<div style="width: 20px; height: 10px; background-color: {color}; margin-right: 5px;"></div>'
                            f'<span>{student}</span></div>')
    
    legend_html = '<div style="font-family: Arial, sans-serif;">' + ''.join(legend_items) + '</div>'
    return legend_html

def draw_multidigraph(G, legend, save_to):
    """
    # https://networkx.org/documentation/stable/auto_examples/drawing/plot_multigraphs.html
    Length of connectionstyle must be at least that of a maximum number of edges
    between pair of nodes. This number is maximum one-sided connections
    for directed graph and maximum total connections for undirected graph.
    """
    ax,fig = plt.gca(), plt.gcf()
    # Works with arc3 and angle3 connectionstyles
    if len(G.out_degree()) == 0:
        # a known bug
        max_num_edge_per_node = 3
    else:
        max_num_edge_per_node = max([d for n,d in G.out_degree()])
    connectionstyle = [f"arc3,rad={r}" for r in itertools.accumulate([0.15] * max_num_edge_per_node)]
    # connectionstyle = [f"angle3,angleA={r}" for r in itertools.accumulate([30] * 4)]
    edge_colors, edgelist = [],[]
    for edge, color in nx.get_edge_attributes(G, 'color').items():
        edge_colors.append(color)
        edgelist.append(edge)
        
    node_colors, nodelist = [],[]
    for node, color in nx.get_node_attributes(G, 'color').items():
        node_colors.append(color)
        nodelist.append(node)
    
    pos = nx.shell_layout(G)
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=nodelist, node_color=node_colors)
    nx.draw_networkx_labels(G, pos, ax=ax)
    nx.draw_networkx_edges(
        G, pos, edge_color=edge_colors, edgelist=edgelist, connectionstyle=connectionstyle, ax=ax
    )

    labels = {
        tuple(edge): attrs['diff']
        for *edge, attrs in G.edges(keys=True, data=True)
    }
    
    nx.draw_networkx_edge_labels(
        G,
        pos,
        labels,
        connectionstyle=connectionstyle,
        label_pos=0.3,
        font_color="blue",
        bbox={"alpha": 0},
        ax=ax,
    )
    gravis_fmt = gravis.convert.networkx_to_gjgf(G)
    fig = gravis.d3(data=gravis_fmt,edge_curvature=0.4,
            node_hover_tooltip=True,
            edge_hover_tooltip=True,
            graph_height=700, zoom_factor=2.5,
            # show_menu=True
            )
    
    html_legend_students = generate_legend_html(legend["student_color"])
    html_legend_nodes =  generate_legend_html({"NODE is_last_success": "green", 
                                               "NODE is_last_failure": "red", 
                                               "NODE starting": "grey"})
    html_legend = "\n".join([html_legend_students, html_legend_nodes])
    with open(save_to.replace(".pdf", ".html"), "w") as fp:
        fp.write(fig.to_html().replace(HTML_HEADER, HTML_HEADER + "\n" + html_legend))
    plt.legend(*custom_plt_legend(legend["student_color"]))
    plt.tight_layout()
    plt.savefig(save_to)
    return fig
    
def to_yaml_fmt(legend):
    legend = {k: dict(v) for k, v in legend.items()}
    for k, v in legend["edges"].items():
        if v is None:
            legend["edges"][k] = ""
        else:
            legend["edges"][k] = v.replace(" \n","\n")

    return legend

def main(args):
    with open(args.clusters_yaml,"r") as fp:
        clusters = yaml.safe_load(fp)
    with open(args.trajectories_yaml,"r") as fp:
        trajectories = yaml.safe_load(fp)
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    
    for problem in tqdm(clusters.keys(), desc="Plotting problem"):
        if args.problems and not problem in args.problems:
            continue
        graph = nx.MultiDiGraph()
        graph, legend = problem_graph(graph, clusters[problem], trajectories[problem])
        with open(f"{args.outdir}/{problem}_legend.yaml", "w") as fp:
            yaml_legend = to_yaml_fmt(legend)
            yaml.dump(yaml_legend, fp, default_style="|")
        with open(f"{args.outdir}/{problem}_graph.json", "w") as fp:
            json.dump(nx.readwrite.json_graph.adjacency_data(graph), fp, indent=4)
        
        draw_multidigraph(graph, legend, f"{args.outdir}/{problem}.pdf")
        # clear
        graph.clear()
        plt.clf()
        
        
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("clusters_yaml")
    parser.add_argument("trajectories_yaml")
    parser.add_argument("outdir")
    parser.add_argument("--problems",nargs="+", default=None)
    args = parser.parse_args()
    main(args)