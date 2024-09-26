'''
Show that edges between same nodes correspond to similar diffs.
Method:
- cluster diffs by tsne
- show clusters correspond to edges
'''
import json
import networkx as nx
from .graph import Graph
from typing import List, Union
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer
import re

MODEL_NAME = "bigcode/starencoder"
MODEL = AutoModel.from_pretrained(MODEL_NAME)
TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
TOKENIZER.pad_token_id = TOKENIZER.eos_token_id
MODEL.eval()

@torch.no_grad
def get_word_embedding(word: List[str]) -> torch.Tensor:
    """
    Must batch to get homogenous size, but this may cause problems in TSNE
    """
    inp = TOKENIZER(word, return_tensors="pt", padding=True)
    output = MODEL(**inp)
    return output.last_hidden_state

def format_diff(diff):
    diff = diff.replace("---","").replace("+++","")
    return re.sub(r"\@\@.*?\@\@", r" ", diff).strip()

# def get_diff_clusters(graph: Graph) -> List[str]:
#     diffs = []
#     for edge in graph.edges:
#         diffs.append(format_diff(edge.diff))
#     return diffs

# def get_edge_degree(graph: Graph) -> dict:
#     """
#     Return a dict showing the number of dupicate edges
#     between two nodes
#     """
#     edge_to_degree = {}
#     for i,edge in enumerate(graph.edges):
#         key = f"({edge.node_from.id}, {edge.node_to.id})"
#         if key not in edge_to_degree.keys():
#             edge_to_degree[key] = {"count":1, "diff": [format_diff(edge.diff)], "id":i}
#         else:
#             edge_to_degree[key]["count"] += 1
#             edge_to_degree[key]["diff"].append(format_diff(edge.diff))
#     return edge_to_degree
            
def plot_clusters(graph: Graph) -> plt.Figure:
    '''
    Tsne plot of diffs
    '''
    edge_to_diffs = {}
    diffs, edges = [],[]
    for i,edge in enumerate(graph.edges):
        key = f"({edge.node_from.id}, {edge.node_to.id})"
        diffs.append(format_diff(edge.diff))
        edges.append(key)
        if key in edge_to_diffs.keys():
            edge_to_diffs[key].append({"text":format_diff(edge.diff), "diff_id":i})
        else:
            edge_to_diffs[key] = [{"text":format_diff(edge.diff), "diff_id":i}]
            
    labels = list(range(len(diffs)))
    tokens = get_word_embedding(diffs)
    # tokens = []
    # for d in diffs:
    #     tokens.append(get_word_embedding(d))

    tokens = tokens.reshape(tokens.shape[0], -1)
    # reduce dimensions to main components due to padding
    # pca = PCA(n_components=3)
    # tokens = pca.fit_transform(tokens)
    # print(tokens.shape)
    
    # tsne_model = TSNE(perplexity=20, n_components=3, init='pca', n_iter=3500, random_state=23)
    # new_values = tsne_model.fit_transform(tokens)

    # plt.figure(figsize=(16, 16)) 
    # x = []
    # y = []
    # for value in new_values:
    #     x.append(value[0])
    #     y.append(value[1])
        
    # for i in range(len(x)):
    #     plt.scatter(x[i],y[i])
    #     plt.annotate(labels[i],
    #                  xy=(x[i], y[i]),
    #                  xytext=(5, 2),
    #                  textcoords='offset points',
    #                  ha='right',
    #                  va='bottom')
    normalized_tensors = torch.nn.functional.normalize(tokens, p=2, dim=1)

    # Compute the cosine similarity matrix
    similarity_matrix = torch.mm(normalized_tensors, normalized_tensors.t())
    torch.save(similarity_matrix, "sim_mat.pt")

    plt.imshow(similarity_matrix.numpy(), cmap='coolwarm', interpolation='nearest')
    plt.colorbar()
    plt.xticks(ticks=np.arange(similarity_matrix.shape[1]), labels=labels)
    plt.yticks(ticks=np.arange(similarity_matrix.shape[0]), labels=labels)

    return plt.gcf(), edge_to_diffs

def cluster_diffs(graph: Graph, filepath: str):
    print(len(graph.edges))
    fig, legend = plot_clusters(graph)
    plt.savefig(filepath)
    
    # diff_ids = {i:d for i,d in enumerate(diff_clusters)}
    # legend = {"edges": edge_legend, "diffs": diff_ids}
    legend_file = filepath.rsplit(".", 1)[0] + ".legend.json"
    with open(legend_file, "w") as fp:
        json.dump(legend, fp, indent=4)

