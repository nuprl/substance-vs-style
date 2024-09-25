'''
Show tat edges between same nodes correspond to similar diffs.
Method:
- cluster diffs by tf-idf
- show clusters correspond to edges
'''
import networkx as nx

def get_diff_clusters(graph: nx.MultiDiGraph):
    edge_to_diffs = {}
    for edge, data in nx.get_edge_attributes(graph, "diff")