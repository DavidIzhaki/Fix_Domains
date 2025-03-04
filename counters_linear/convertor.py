import os
import re
import json
import argparse

def parse_pddl(pddl_text):
    result = {"Counters": {}, "Goal": {}}
    
    # Extract counters from the init section.
    # Matches lines like: (= (value c0) 19)
    counter_pattern = re.compile(r'\(=\s+\(value\s+(c\d+)\)\s+(\d+)\)')
    for match in counter_pattern.finditer(pddl_text):
        counter_name = match.group(1)  # e.g., "c0"
        value = int(match.group(2))
        # Use the number part as key (e.g. "0" for c0)
        result["Counters"][counter_name[1:]] = value

    # Extract goal conditions.
    # We assume the goal conditions appear somewhere in the file inside a (:goal (and ...)) block.
    # This regex looks for conditions of the form:
    # (<= <expr_left> <expr_right>) or (>= <expr_left> <expr_right>)
    cond_pattern = re.compile(r'\((<=|>=)\s+(\(.*?\))\s+(\(.*?\))\)', re.DOTALL)
    conditions = cond_pattern.findall(pddl_text)
    
    cond_index = 1
    for op, left_expr, right_expr in conditions:
        try:
            left_counter, left_offset = parse_linear_expr(left_expr)
            right_counter, right_offset = parse_linear_expr(right_expr)
        except Exception as e:
            print("Error parsing condition:", op, left_expr, right_expr, e)
            continue
        
        left_str = left_counter if left_offset == 0 else (
            f"{left_counter} + {left_offset}" if left_offset > 0 else f"{left_counter} - {-left_offset}"
        )
        right_str = right_counter if right_offset == 0 else (
            f"{right_counter} + {right_offset}" if right_offset > 0 else f"{right_counter} - {-right_offset}"
        )
        condition_str = f"{left_str} {op} {right_str}"
        result["Goal"][f"condition{cond_index}"] = condition_str
        cond_index += 1

    return result

def parse_linear_expr(expr_str):
    """
    Parses a linear expression and returns a tuple: (counter, constant_offset).
    Supported forms:
      - (value cX)
      - (+ (value cX) constant)
      - (- (value cX) constant)
    """
    expr_str = expr_str.strip()
    # Simple counter: (value cX)
    m = re.match(r'^\(value\s+(c\d+)\)$', expr_str)
    if m:
        return m.group(1), 0
    # Addition: (+ (value cX) constant)
    m = re.match(r'^\(\+\s+\(value\s+(c\d+)\)\s+(-?\d+)\)$', expr_str)
    if m:
        return m.group(1), int(m.group(2))
    # Subtraction: (- (value cX) constant)
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
    parser = argparse.ArgumentParser(description="Convert linear PDDL problems to JSON")
    parser.add_argument("--input_dir", help="Directory containing the PDDL files")
    parser.add_argument("--output_dir", help="Directory to store the JSON files")
    args = parser.parse_args()
    convert_directory(args.input_dir, args.output_dir)
