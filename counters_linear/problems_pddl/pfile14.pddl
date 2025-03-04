import os
import re
import json
import argparse

def extract_goal_block(text):
    """
    Extracts the goal block from the text starting at "(:goal" and returns the substring
    containing the balanced parentheses.
    """
    idx = text.find("(:goal")
    if idx == -1:
        return None
    paren_count = 0
    start = idx
    end = None
    for i, char in enumerate(text[idx:], start=idx):
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
            if paren_count == 0:
                end = i + 1
                break
    if end is None:
        raise Exception("Unbalanced parentheses in goal block")
    return text[start:end]

def parse_pddl(pddl_text):
    result = {"Counters": {}, "Goal": {}}
    
    # Extract counters from the init section.
    # Matches lines like: (= (value c0) 19)
    init_pattern = re.compile(r'\(=\s+\(value\s+(c\d+)\)\s+(\d+)\)')
    for match in init_pattern.finditer(pddl_text):
        counter_name = match.group(1)  # e.g., "c0"
        value = int(match.group(2))
        key = counter_name[1:]  # using just the number part as key
        result["Counters"][key] = value

    # Extract the goal block using the helper.
    goal_block_str = extract_goal_block(pddl_text)
    if not goal_block_str:
        print("No goal block found in the PDDL file.")
    else:
        # Remove the outer "(:goal" and the corresponding closing parenthesis.
        inner = goal_block_str[len("(:goal"):].strip()
        # Remove outer parentheses if present.
        if inner.startswith('(') and inner.endswith(')'):
            inner = inner[1:-1].strip()
        # Now, the inner string should start with "and". Remove it.
        if inner.startswith("and"):
            inner = inner[len("and"):].strip()
        # At this point, 'inner' should contain the conditions.
        # Use regex to capture conditions of the form: (<= <expr_left> <expr_right>)
        condition_matches = re.findall(r'\(<=\s*(\(.+?\))\s*(\(.+?\))\s*\)', inner, re.DOTALL)
        if not condition_matches:
            print("No conditions found in the goal block.")
        else:
            for index, (left_expr, right_expr) in enumerate(condition_matches, start=1):
                try:
                    left_counter, left_offset = parse_linear_expr(left_expr)
                    right_counter, right_offset = parse_linear_expr(right_expr)
                except Exception as e:
                    raise Exception(f"Error parsing condition {index}: {e}")
                
                left_formatted = (
                    left_counter if left_offset == 0 
                    else (f"{left_counter} + {left_offset}" if left_offset > 0 else f"{left_counter} - {-left_offset}")
                )
                right_formatted = (
                    right_counter if right_offset == 0 
                    else (f"{right_counter} + {right_offset}" if right_offset > 0 else f"{right_counter} - {-right_offset}")
                )
                result["Goal"][f"condition{index}"] = f"{left_formatted} <= {right_formatted}"
    return result

def parse_linear_expr(expr_str):
    """
    Parses a linear expression.
    Supported forms:
      - Simple counter: (value cX)
      - Addition: (+ (value cX) constant)
      - Subtraction: (- (value cX) constant)
      - Multiplication by 1: (* (value cX) 1) or (* 1 (value cX))
    Returns a tuple (counter, constant_offset).
    """
    expr_str = expr_str.strip()
    
    # Multiplication by 1: (* (value cX) 1)
    m = re.match(r'^\(\*\s+\(value\s+(c\d+)\)\s+1\)$', expr_str)
    if m:
        return m.group(1), 0
    # Multiplication by 1: (* 1 \(value cX\))
    m = re.match(r'^\(\*\s+1\s+\(value\s+(c\d+)\)\)$', expr_str)
    if m:
        return m.group(1), 0
    
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
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    for filename in os.listdir(input_dir):
        if filename.endswith(".pddl"):
            input_filepath = os.path.join(input_dir, filename)
            base, _ = os.path.splitext(filename)
            output_filepath = os.path.join(output_dir, base + ".json")
            convert_file(input_filepath, output_filepath)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDDL files to JSON format for linear expressions")
    parser.add_argument("--input_dir", required=True, help="Directory containing the PDDL files")
    parser.add_argument("--output_dir", required=True, help="Directory to store the JSON files")
    args = parser.parse_args()
    
    convert_directory(args.input_dir, args.output_dir)
