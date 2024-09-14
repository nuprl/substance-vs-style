import json
import re
from ruamel.yaml import YAML

def str_presenter(dumper, data):
    if '\n' in data:
        style = '|'  # Use literal block style for multi-line strings
    elif re.search(r'[:#\[\]\{\},&\*]', data):
        style = '|'  # Use literal block style if special characters are present
    else:
        style = ''   # Use plain style (unquoted) for other strings
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style=style)

yaml = YAML()
yaml.representer.add_representer(str, str_presenter)
yaml.default_flow_style = False
yaml.allow_unicode = True

with open('tagged_prompts.jsonl', 'r') as jsonl_file, open('outputtry.yaml', 'w') as yaml_file:
    for line in jsonl_file:
        data = json.loads(line)
        yaml.dump(data, yaml_file)
