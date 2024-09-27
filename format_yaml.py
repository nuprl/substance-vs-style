import sys
import yaml
from student_progress_graph.graph_utils import load_graph

yaml_file = sys.argv[1]
output_file = sys.argv[2]

graph = load_graph(yaml_file)

yaml_output = yaml.dump(graph, default_flow_style=False, sort_keys=False)
print(yaml_output)
with open(output_file, "w") as fp:
    fp.write(yaml_output)