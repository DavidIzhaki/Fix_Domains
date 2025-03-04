import os
import re
import json
import argparse

def parse_pddl(pddl_text):
    result = {
        "Counters": {},
        "Goal": {}
    }
    
    # Extract counters from the init section.
    # Matches lines like: (= (value c0) 19)
    init_pattern = re.compile(r'\(=\s+\(value\s+(c\d+)\)\s+(\d+)\)')
    for match in init_pattern.finditer(pddl_text):
        counter_name = match.group(1)  # e.g., "c0"
        value = int(match.group(2))
        # Remove the leading "c" if you want just the number key, or keep "c" if preferred.
        key = counter_name[1:]
        result["Counters"][key] = value

    # Extract goal conditions.
    # This regex finds conditions of the form:
    # (<= (+ (value cX) 1) (value cY))
    goal_pattern = re.compile(r'\(<=\s*\(\+\s*\(value\s+(c\d+)\)\s+1\s*\)\s*\(value\s+(c\d+)\)\s*\)')
    matches = goal_pattern.findall(pddl_text)
    
    for index, (left_counter, right_counter) in enumerate(matches, start=1):
        # Format the condition as "cX+1 <= cY"
        condition_str = f"{left_counter}+1 <= {right_counter}"
        result["Goal"][f"condition{index}"] = condition_str

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
    # Process only .pddl files
    for filename in os.listdir(input_dir):
        if filename.endswith(".pddl"):
            input_filepath = os.path.join(input_dir, filename)
            # Use same base name with .json extension
            base, _ = os.path.splitext(filename)
            output_filepath = os.path.join(output_dir, base + ".json")
            convert_file(input_filepath, output_filepath)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDDL files to JSON format")
    parser.add_argument("--input_dir", help="Directory containing the PDDL files")
    parser.add_argument("--output_dir", help="Directory to store the JSON files")
    args = parser.parse_args()
    
    convert_directory(args.input_dir, args.output_dir)
