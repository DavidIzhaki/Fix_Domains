import os
import re
import json
import argparse

def parse_pddl(pddl_text):
    counters = []
    conditions = []
    max_value = 48  # fallback

    # Extract max_value
    max_pattern = re.compile(r'\(=\s+\(max_int\)\s+(\d+)\)')
    max_match = max_pattern.search(pddl_text)
    if max_match:
        max_value = int(max_match.group(1))

    # Extract counters
    counter_pattern = re.compile(r'\(=\s+\(value\s+(c\d+)\)\s+(\d+)\)')
    for match in counter_pattern.finditer(pddl_text):
        name = match.group(1)
        value = int(match.group(2))
        counters.append({ "name": name, "value": value })

    # Extract conditions in goal
    cond_pattern = re.compile(r'\((<=|>=|=|<|>)\s+(\(.*?\))\s+(\(.*?\))\)', re.DOTALL)
    for op, left_expr, right_expr in cond_pattern.findall(pddl_text):
        # Skip non-value expressions (e.g., involving max_int)
        if not ("(value" in left_expr and "(value" in right_expr):
            continue
        try:
            left_counter, left_offset = parse_linear_expr(left_expr)
            right_counter, right_offset = parse_linear_expr(right_expr)
        except Exception as e:
            print("Error parsing condition:", op, left_expr, right_expr, e)
            continue

        conditions.append({
            "left": {
                "terms": [[1, left_counter]],
                "constant": left_offset
            },
            "operator": op,
            "right": {
                "terms": [[1, right_counter]],
                "constant": right_offset
            }
        })

    return {
        "state": { "counters": counters },
        "problem": {
            "goal": { "conditions": conditions },
            "max_value": max_value
        }
    }

def parse_linear_expr(expr_str):
    expr_str = expr_str.strip()
    m = re.match(r'^\(value\s+(c\d+)\)$', expr_str)
    if m:
        return m.group(1), 0
    m = re.match(r'^\(\+\s+\(value\s+(c\d+)\)\s+(-?\d+)\)$', expr_str)
    if m:
        return m.group(1), int(m.group(2))
    m = re.match(r'^\(-\s+\(value\s+(c\d+)\)\s+(\d+)\)$', expr_str)
    if m:
        return m.group(1), -int(m.group(2))
    raise Exception("Unrecognized linear expression format: " + expr_str)

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
    parser = argparse.ArgumentParser(description="Convert linear PDDL problems to structured JSON")
    parser.add_argument("--input_dir", help="Directory containing the PDDL files", required=True)
    parser.add_argument("--output_dir", help="Directory to store the JSON files", required=True)
    args = parser.parse_args()
    convert_directory(args.input_dir, args.output_dir)
