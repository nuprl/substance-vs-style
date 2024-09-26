"""
Given a graph.yaml, can plot a matplotlib graph or interactive
gravis html
"""
from functools import partial
import argparse
import networkx as nx
from typing import Union, List
import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import itertools
import gravis
from .graph_utils import load_graph, Graph

HTML_HEADER="""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>"""

def custom_plt_legend(student_colors:dict) -> Union[List[Line2D], List[str]]:
    custom_lines, labels = [],[]
    for username,color in student_colors.items():
        custom_lines.append(Line2D([0], [0], color=color, lw=4))
        labels.append(username)
    return custom_lines, labels

def generate_legend_html(legend_dict:dict) -> str:
    legend_items = []
    
    for student, color in legend_dict.items():
        # color = COLORS_TO_HEX[color]
        legend_items.append(f'<div style="display: flex; align-items: center; margin-bottom: 5px;">'
                            f'<div style="width: 20px; height: 10px; background-color: {color}; margin-right: 5px;"></div>'
                            f'<span>{student}</span></div>')
    
    legend_html = '<div style="font-family: Arial, sans-serif;">' + ''.join(legend_items) + '</div>'
    return legend_html

def draw_multidigraph(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    # https://networkx.org/documentation/stable/auto_examples/drawing/plot_multigraphs.html
    """
    max_num_edge_per_node = max([d for _,d in G.out_degree()])
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
    nx.draw_networkx_nodes(G, pos, nodelist=nodelist, node_color=node_colors)
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(
        G, pos, ax=None, edge_color=edge_colors, edgelist=edgelist, connectionstyle=connectionstyle
    )
    return G

def matplotlib_plot(graph: Graph, filepath:str):
    """
    Saves a static visualization of graph to pdf file
    """
    G = graph.to_networkx()
    G = draw_multidigraph(G)
    fig, ax = plt.gcf(), plt.gca()
    plt.legend(*custom_plt_legend(graph.get_legend()))
    plt.tight_layout()
    plt.savefig(filepath)
    return fig

def gravis_plot(graph:Graph, filepath:str):
    """
    Saves an insteractive visualization of graph to html file
    """
    G = graph.to_networkx()
    G = draw_multidigraph(G)
    # data selection
    edge_colors = nx.get_edge_attributes(G, "color")
    
    def has_color(u, v, i, color=None, edge_colors={}):
        return edge_colors[(u,v,i)] == color
    
    student_graphs = []
    for student, color in graph.get_legend().items():
        subgraph = nx.subgraph_view(G, filter_edge= partial(has_color, 
                                                     color=color,
                                                     edge_colors=edge_colors))
        subgraph = nx.MultiDiGraph(subgraph, label=student)
        student_graphs.append(
            subgraph
        )
        
    graphs = [G, *student_graphs]
    fig = gravis.d3(data=graphs,edge_curvature=0.4,
            node_hover_tooltip=True,
            edge_hover_tooltip=True,
            graph_height=700, zoom_factor=2.5,
            show_node_label=True,
            show_edge_label=True,
            edge_label_data_source="tags",
            use_links_force= False
            # node_label_data_source="label_with_tags",
            # show_menu=True
            )
    
    def format_node_tags(username, tags, start_node_id):
        if username not in tags.keys():
            return f"{username} : {start_node_id}"
        else:
            tags = tags[username]
            if len(username) == len("student0"):
                username = username+"  "
            return f"{username} : {start_node_id} : {tags}"
            
    color_legend = graph.get_legend()
    start_node_tags = graph.get_start_node_states()
    legend = {format_node_tags(k, start_node_tags, graph.get_start_node_id(k)):v for k,v in color_legend.items()}
    html_legend= generate_legend_html(legend)
    html_legend = f"<span>color, username, start node id, start node tags</span></div>{html_legend}"
    with open(filepath, "w") as fp:
        fp.write(fig.to_html().replace(HTML_HEADER, HTML_HEADER + "\n" + html_legend))

def main(args):
    graph : Graph = load_graph(args.graph_yaml)
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    
    matplotlib_plot(graph, f"{args.outdir}/{graph.problem}.pdf")
    gravis_plot(graph, f"{args.outdir}/{graph.problem}.html")
        
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_yaml")
    parser.add_argument("outdir")
    args = parser.parse_args()
    main(args)