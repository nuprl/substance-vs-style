'''
Some utility and modifier functions for data that goes into plots
'''
import re
from typing import Union
import difflib
import yaml
from .graph import graph_constructor, edge_constructor, node_constructor, Graph

def anonimize_filename(stderr: str)->str:
    return re.sub("/tmp/.*?\.py", "/tmp/file.py", stderr)

def extract_error_message(stderr: str)->str:
    if stderr == "":
        return stderr
    stderr_splits = stderr.strip().split("\n")[-1].split("Error:")
    return stderr_splits[0] + "Error:" + stderr_splits[-1]

def get_diff(prev:str, new:str) -> str:
    # ndiff shows full prompt, unified_diff shows localized change
    diff = difflib.unified_diff(prev.split(),new.split())
    return ''.join(diff)

def load_graph(filepath:str) -> Graph:
    yaml.SafeLoader.add_constructor('!Graph', graph_constructor)
    yaml.SafeLoader.add_constructor('!Edge', edge_constructor)
    yaml.SafeLoader.add_constructor('!Node', node_constructor)
    
    with open(filepath, "r") as fp:
        graph = yaml.safe_load(fp)
    return graph