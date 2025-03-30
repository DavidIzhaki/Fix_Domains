import os
import re
import json
import argparse

def parse_pddl(pddl_text):
    counters_map = {}
    conditions = []
    max_value = 48  # fallback

    # Max value
    max_pattern = re.compile(r'\(=\s+\(max_int\)\s+(\d+)\)')
    max_match = max_pattern.search(pddl_text)
    if max_match:
        max_value = int(max_match.group(1))

    # Value
    value_pattern = re.compile(r'\(=\s+\(value\s+(c\d+)\)\s+(\d+)\)')
    for match in value_pattern.finditer(pddl_text):
        name = match.group(1)
        val = int(match.group(2))
        counters_map[name] = { "name": name, "value": val }

    # Rate value
    rate_pattern = re.compile(r'\(=\s+\(rate_value\s+(c\d+)\)\s+(\d+)\)')
    for match in rate_pattern.finditer(pddl_text):
        name = match.group(1)
        rate_val = int(match.group(2))
        if name not in counters_map:
            counters_map[name] = { "name": name }
        counters_map[name]["rate_value"] = rate_val

    # Conditions (like: (<= (+ (value c0) 1) (value c1)))
    cond_pattern = re.compile(r'\((<=|>=|=|<|>)\s+\(\+\s+\(value\s+(c\d+)\)\s+1\)\s+\(value\s+(c\d+)\)\)')
    for match in cond_pattern.finditer(pddl_text):
        op = match.group(1)
        left = match.group(2)
        right = match.group(3)
        conditions.append({
            "left": { "terms": [[1, left]], "constant": 1 },
            "operator": op,
            "right": { "terms": [[1, right]], "constant": 0 }
        })

    # Convert counters_map to list
    counters = list(counters_map.values())

    return {
        "state": {
            "counters": counters
        },
        "problem": {
            "goal": {
                "conditions": conditions
            },
            "max_value": max_value
        }
    }

def convert_file(input_filepath, output_filepath):
    with open(input_filepath, 'r') as infile:
        content = infile.read()
    parsed = parse_pddl(content)
    with open(output_filepath, 'w') as outfile:
        json.dump(parsed, outfile, indent=4)
    print(f"Converted {input_filepath} to {output_filepath}")

def convert_directory(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for filename in os.listdir(input_dir):
        if filename.endswith(".pddl"):
            input_filepath = os.path.join(input_dir, filename)
            base, _ = os.path.splitext(filename)
            output_filepath = os.path.join(output_dir, base + ".json")
            convert_file(input_filepath, output_filepath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert fo_counter PDDL to structured JSON")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    convert_directory(args.input_dir, args.output_dir)
