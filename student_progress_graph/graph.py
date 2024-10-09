from typing import List, Literal, Union, Any
from pathlib import Path
from networkx.readwrite.json_graph import adjacency
import yaml
import networkx as nx
from dataclasses import dataclass
from collections import defaultdict

State = Literal['success','fail','neutral',
                '_dummy_']

class Node(yaml.YAMLObject):
    """
    Represents a possible completion output (stderr/stdout)
    """
    yaml_tag = u'!Node'
    
    def __init__(self, id: int, stdout: List[str], stderr: List[str], 
                _node_tags: Union[None, List[str]] = None):
        self.id = id
        self.stdout = stdout
        self.stderr = stderr
        self._node_tags = _node_tags
    
    def __repr__(self):
        return "%s(id=%r, stdout=%r, stderr=%r, _node_tags=%r)" % (
        self.__class__.__name__,self.id, self.stdout, self.stderr, self._node_tags)
        
    def __eq__(self, other):
        return (self.id == other.id and self.stdout == other.stdout
                and self.stderr == other.stderr)
        
    def __hash__(self):
        stdout = "\n".join(self.stdout)
        stderr = "\n".join(self.stderr)
        return hash(str(self.id) + stdout + "\n" + stderr)
    
    @classmethod
    def from_dict(cls, node:dict) -> "Node":
        return cls(**node)
    
    @classmethod
    def dummy_node(cls) -> "Node":
        return cls(-1, ["_stdout_"],["_stderr_"])

@dataclass  
class Edge(yaml.YAMLObject):
    """
    Represents a student edit
    """
    yaml_tag = u'!Edge'
    node_from: Node
    node_to: Node
    username: str
    prompt_from: str
    prompt_to: str
    completion_from: str
    completion_to: str
    diff: str
    attempt_id: int
    total_attempts: int
    state: State
    _edge_tags: Union[None, List[str]] = None
    clues: Union[None, List[int]] = None

    def __hash__(self):
        return hash("\n".join(str(getattr(self, k)) for k in [
            "node_from","node_to","username","prompt_from","prompt_to","completion_from",
            "completion_to", "attempt_id","total_attempts"
        ]))
    
    def __repr__(self):
        # return f"%r" % self.state
        return """%s(_edge_tags=%r,node_from=%r,node_to=%r,username=%r,
prompt_from=%r,prompt_to=%r,completion_from=%r,completion_to=%r,diff=%r,
attempt_id=%r,total_attempts=%r,state=%r, clues=%r""" % (self.__class__.__name__,
        self._edge_tags, self.node_from, self.node_to, self.username,
        self.prompt_from, self.prompt_to, self.completion_from,self.completion_to, 
        self.diff, self.attempt_id, self.total_attempts, self.state, self.clues)
        
    def to_dict(self) -> dict:
        dikt = {}
        for k,v in self.__dict__.items():
            if isinstance(v, Node):
                dikt[k] = v.__dict__
            else:
                dikt[k] = v
        return dikt
    
    def add_clues(self, clues: List[int]):
        self.clues = list(clues)
    
    @classmethod
    def from_dict(cls, edge:dict) -> "Edge":
        edge["node_from"] = Node(**edge["node_from"])
        edge["node_to"] = Node(**edge["node_to"])
        return cls(**edge)
    
    @classmethod
    def dummy_edge(cls) -> "Edge":
        return cls(
            node_from = Node.dummy_node(),
            node_to = Node.dummy_node(),
            completion_from= "_completion_from_",
            completion_to="_compeltion_to_",
            prompt_from="_prompt_from_",
            prompt_to="_prompt_to_",
            attempt_id=-1,
            diff="_diff_",
            total_attempts=-1,
            username="_username_",
            state="_dummy_"
        )
    
class Graph(yaml.YAMLObject):
    """
    Represents a Problem
    """
    yaml_tag = u'!Graph'
    SUCCESS_NODE_COLOR = "green"
    BASE_NODE_COLOR="grey"
    
    def __init__(self, problem:str, nodes: List[Node],edges: List[Edge], **kwargs):
        self.problem=problem
        self.nodes=nodes
        self.edges=edges
        
        self.student_start_node_tags = kwargs.pop("student_start_node_tags", {})
        self.problem_clues = kwargs.pop("problem_clues", {})

        self.COLORS = [
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
            '#00bfff', # deep sky blue
        ]
        self.student_colors = {}

        # this is initialized after tagging
        self.student_clues_tracker = {}
    
    def __repr__(self):
        return "%s(problem=%r, nodes=%r, edges=%r)" % (
        self.__class__.__name__, self.problem, self.nodes, self.edges)
        
    def __eq__(self, other):
        return (self.nodes == other.nodes and
                self.edges == other.edges and
                self.problem == other.problem)
        
    def to_networkx(self) -> nx.MultiDiGraph:
        G = nx.MultiDiGraph(label=self.problem)
        
        # add nodes
        for node in self.nodes:
            stdout_text = "\n".join(node.stdout)
            stderr_text = "\n".join(node.stderr)
            if node._node_tags:
                tags = f"tags:{node._node_tags}\n"
            else:
                tags = ""
            G.add_node(node.id, 
                       stderr=node.stderr,
                       stdout=node.stdout,
                       color=self.BASE_NODE_COLOR,
                       label_with_tags=f"{node.id}:{tags.replace('tags:','')}",
                       tags=tags,
                       hover=f"{tags}stdout:\n{stdout_text}\nstderr:\n{stderr_text}")
        
        # add edges
        success_nodes = []
        for edge in self.edges:
            if edge.state == "success":
                success_nodes.append(edge.node_to.id)
            
            if edge._edge_tags:
                tags = str(edge._edge_tags)
            else:
                tags = ""
            hover_text = (f"username:{edge.username}\nedge: ({edge.node_from.id}->{edge.node_to.id})\n" +
                        f"state:{edge.state}\n" +
                        f"attempt_num:{edge.attempt_id}/{edge.total_attempts}\n"+
                        f"diff:\n{edge.diff}\n\n"+
                        f"FROM completion:\n{edge.prompt_from}\n    {edge.completion_from}\n\n"+
                        f"TO completion:\n{edge.prompt_to}\n    {edge.completion_to}")
            
            if edge.username in self.student_colors.keys():
                color = self.student_colors[edge.username]
            else:
                color = self.COLORS.pop()
                self.student_colors[edge.username] = color
                
            G.add_edge(
                edge.node_from.id, edge.node_to.id,
                prompt_from=edge.prompt_from, prompt_to=edge.prompt_to,
                completion_from=edge.completion_from, completion_to=edge.completion_to,
                total_attempts=edge.total_attempts, attempt_id=edge.attempt_id,
                diff=edge.diff, username=edge.username, state=edge.state,
                hover = hover_text,
                tags= tags,
                color= color
            )
        
        # color success nodes in green
        for i,node in enumerate(G.nodes()):
            if node in success_nodes:
                G.nodes[i]["color"] = self.SUCCESS_NODE_COLOR

        return G

    def get_legend(self):
        return self.student_colors
    
    def get_start_node_states(self):
        return self.student_start_node_tags
    
    def get_students(self):
        return sorted(list(set([e.username for e in self.edges])))
    
    def get_start_node_id(self, username: str):
        for e in self.edges:
            if e.username == username and e.attempt_id == 1:
                return e.node_from.id
        raise ValueError(f"Start node not found {username}, {self.problem}")
    
    def get_student_edges(self) -> dict[str, List[Edge]]:
        student_to_edges = defaultdict(list)
        for e in self.edges:
            student_to_edges[e.username].append(e)
        student_to_edges = {k: sorted(v, key=lambda x: x.attempt_id) for k,v in student_to_edges.items()}
        return student_to_edges

    def adjacency(self):
        adjacency = {n.id:[] for n in self.nodes}
        for e in self.edges:
            adjacency[e.node_from.id].append(e.node_to.id)
        return adjacency
    
    def get_successful_students(self):
        successful = []
        for e in self.edges:
            if e.state == "success":
                successful.append(e.username)
        return successful
    
    @classmethod
    def from_dict(cls, graph: dict) -> "Graph":
        nodes = [Node.from_dict(n) for n in graph["nodes"]]
        edges = [Edge.from_dict(e) for e in graph["edges"]]
        return cls(
            problem= graph["problem"],
            nodes=nodes,
            edges=edges,
            student_start_node_tags=graph["student_start_node_tags"]
        )
    
    def tag_node(self, node_id: int, tag: Any, overwrite:bool=False):  
        
        def _add_tag(node, t):
            if overwrite:
                n._node_tags = tag
            elif node._node_tags == None:
               node._node_tags = [t]
            else:
                node._node_tags.append(t)    
                
        for n in self.nodes:
            if n.id == node_id:
                _add_tag(n, tag)
                
        for e in self.edges:
            if e.node_from.id == node_id:
                _add_tag(e.node_from, tag)
            if e.node_to.id == node_id:
                _add_tag(e.node_to, tag)
              
def compute_state(is_success:bool, last_attempt: bool) -> State:
    if is_success:
        return "success"
    else:
        if last_attempt:
            return "fail"
        else:
            return "neutral"

def find_node(stdout: List[str], stderr: List[str], nodes: List[Node]) -> Union[Node, None]:
    for node in nodes:
        if node.stderr == stderr and node.stdout == stdout:
            return node
    return None