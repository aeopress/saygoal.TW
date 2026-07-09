import json

def parse_config(path):
    with open(path) as f:      # raises FileNotFoundError when missing
        return json.load(f)
