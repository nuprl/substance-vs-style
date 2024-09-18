import json
from ruamel.yaml import YAML

# Initialize YAML object
yaml = YAML()

# Read the YAML file
with open('outputtry.yaml', 'r') as yaml_file:
    yaml_data = yaml.load(yaml_file)

# Write to JSONL file
with open('jsonltry.jsonl', 'w') as jsonl_file:
    # Ensure each dictionary is written as a separate JSON line
    for entry in yaml_data:
        jsonl_file.write(json.dumps(entry) + '\n')
