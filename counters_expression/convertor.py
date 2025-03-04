import os
import re
import json
import argparse

def tokenize(s):
    """Splits the string into tokens (words and parentheses)."""
    tokens = []
    token = ""
    for char in s:
        if char.isspace():
            if token:
                tokens.append(token)
                token = ""
        elif char in '()':
            if token:
                tokens.append(token)
                token = ""
            tokens.append(char)
        else:
            token += char
    if token:
        tokens.append(token)
    return tokens

def parse_tokens(tokens):
    """Recursively parses tokens into an S-expression (nested list)."""
    if not tokens:
        raise Exception("Unexpected EOF while parsing")
    token = tokens.pop(0)
    if token == '(':
        lst = []
        while tokens:
            if tokens[0] == ')':
                tokens.pop(0)  # consume the closing ')'
                return lst
            lst.append(parse_tokens(tokens))
        raise Exception("Missing closing parenthesis in expression")
    elif token == ')':
        raise Exception("Unexpected ')' encountered")
    else:
        return token

def expr_to_infix(expr):
    """
    Recursively converts an S-expression (nested list) into an infix string.
    Special case: (value cX) becomes just "cX".
    """
    if isinstance(expr, list):
        # Special handling for (value cX)
        if len(expr) == 2 and expr[0] == "value":
            return expr[1]
        # For binary operators, assume format: [operator, operand1, operand2]
        if len(expr) == 3:
            left = expr_to_infix(expr[1])
            op = expr[0]
            right = expr_to_infix(expr[2])
            return f"({left} {op} {right})"
        else:
            # For n-ary expressions, join all operands with the operator.
            op = expr[0]
            operands = " ".join(expr_to_infix(e) for e in expr[1:])
            return f"({op} {operands})"
    else:
        return expr

def extract_goal_block(text):
    """
    Extracts the goal block as a substring from the given text.
    It looks for the first occurrence of "(:goal" and then finds the matching closing parenthesis.
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
    result = {"Counters": {}, "Goal": {}, "max_value": None}
    
    # Extract max_value from the init section.
    # Matches lines like: (= (max_int) 24)
    max_pattern = re.compile(r'\(=\s+\(max_int\)\s+(\d+)\)')
    max_match = max_pattern.search(pddl_text)
    if max_match:
        result["max_value"] = int(max_match.group(1))
    else:
        result["max_value"] = 48  # default value if not found

    # Extract counters from the init section.
    # Matches lines like: (= (value c0) 19)
    init_pattern = re.compile(r'\(=\s+\(value\s+(c\d+)\)\s+(\d+)\)')
    for match in init_pattern.finditer(pddl_text):
        counter_name = match.group(1)  # e.g., "c0"
        value = int(match.group(2))
        # Use the counter number as key (or keep "c0" if preferred)
        key = counter_name[1:]
        result["Counters"][key] = value

    # Extract the goal block using the helper.
    goal_block_str = extract_goal_block(pddl_text)
    if goal_block_str is None:
        print("No goal block found in the PDDL file.")
    else:
        # Remove the leading "(:goal" and the trailing ")".
        inner = goal_block_str[len("(:goal"):].strip()
        # Remove the outer parentheses if present.
        if inner[0] == '(' and inner[-1] == ')':
            inner = inner[1:-1].strip()
        # Now, re-add parentheses so that the expression is balanced.
        inner = f"({inner})"
        tokens = tokenize(inner)
        try:
            parsed_goal = parse_tokens(tokens)
        except Exception as e:
            raise Exception(f"Error parsing goal S-expression: {e}")
        
        # If the parsed goal is an "and" block, process each condition.
        if isinstance(parsed_goal, list) and parsed_goal[0] == "and":
            conditions = parsed_goal[1:]
            for index, cond in enumerate(conditions, start=1):
                infix_str = expr_to_infix(cond)
                # Remove outermost parentheses for cleaner output.
                if infix_str.startswith("(") and infix_str.endswith(")"):
                    infix_str = infix_str[1:-1]
                result["Goal"][f"condition{index}"] = infix_str
        else:
            # Otherwise, treat the whole expression as one condition.
            infix_str = expr_to_infix(parsed_goal)
            result["Goal"]["condition1"] = infix_str

    return result

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
    parser = argparse.ArgumentParser(description="Convert PDDL files to JSON format with expression support and max_value")
    parser.add_argument("--input_dir", required=True, help="Directory containing the PDDL files")
    parser.add_argument("--output_dir", required=True, help="Directory to store the JSON files")
    args = parser.parse_args()
    
    convert_directory(args.input_dir, args.output_dir)
