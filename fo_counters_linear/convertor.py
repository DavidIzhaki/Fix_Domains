import os
import re
import json
import argparse

def parse_pddl(pddl_text):
    result = {"Counters": {}, "Goal": {}}
    
    # Extract counter values from the init section.
    # Matches lines like: (= (value c0) 19)
    value_pattern = re.compile(r'\(=\s+\(value\s+(c\d+)\)\s+(\d+)\)')
    for match in value_pattern.finditer(pddl_text):
        counter_name = match.group(1)  # e.g., "c0"
        value = int(match.group(2))
        # Use the number part as key and store in a dictionary.
        result["Counters"][counter_name[1:]] = {"value": value}
    
    # Extract rate_value from the init section.
    # Matches lines like: (= (rate_value c0) 0)
    rate_pattern = re.compile(r'\(=\s+\(rate_value\s+(c\d+)\)\s+(\d+)\)')
    for match in rate_pattern.finditer(pddl_text):
        counter_name = match.group(1)  # e.g., "c0"
        rate_value = int(match.group(2))
        # If the counter hasn't been seen yet, create its dictionary.
        if counter_name[1:] not in result["Counters"]:
            result["Counters"][counter_name[1:]] = {}
        result["Counters"][counter_name[1:]]["rate_value"] = rate_value

    # Extract goal conditions.
    # This regex finds conditions of the form:
    # (<= (+ (value cX) 1) (value cY)) or (>= (+ (value cX) 1) (value cY))
    cond_pattern = re.compile(r'\((<=|>=)\s+\(\+\s+\(value\s+(c\d+)\)\s+1\)\s+\(value\s+(c\d+)\)\)')
    cond_index = 1
    for match in cond_pattern.finditer(pddl_text):
        op = match.group(1)
        left_counter = match.group(2)
        right_counter = match.group(3)
        # Format condition as "cX+1 {op} cY"
        condition_str = f"{left_counter}+1 {op} {right_counter}"
        result["Goal"][f"condition{cond_index}"] = condition_str
        cond_index += 1

    return result

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
    # Process only .pddl files.
    for filename in os.listdir(input_dir):
        if filename.endswith(".pddl"):
            input_filepath = os.path.join(input_dir, filename)
            base, _ = os.path.splitext(filename)
            output_filepath = os.path.join(output_dir, base + ".json")
            convert_file(input_filepath, output_filepath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert fo_counters PDDL files (with rate_value) to JSON (Linear Domain)")
    parser.add_argument("--input_dir", help="Directory containing the PDDL files", required=True)
    parser.add_argument("--output_dir", help="Directory to store the JSON files", required=True)
    args = parser.parse_args()
    
    convert_directory(args.input_dir, args.output_dir)
