#!/usr/bin/env python3
import os
import re
import json
import argparse

def parse_init(pddl_text):
    """
    Parses the :init section to extract assignments for boats and persons.
    This version uses a combined regex pattern to capture:
      - the attribute (x, y, or d)
      - the object name (e.g., b0 or p0)
      - the numeric value
    """
    boats_data = {}
    persons_data = {}
    # Capture everything between :init and :goal
    init_match = re.search(r'\(:init\s*(.*?)\s*\(:goal', pddl_text, flags=re.DOTALL | re.MULTILINE)
    if init_match:
        init_content = init_match.group(1)
        # Combined pattern to extract assignments like (= (x b0) -7)
        pattern = r'\(=\s*\((x|y|d)\s+([bp]\d+)\)\s+(-?\d+(?:\.\d+)?)\)'
        matches = re.findall(pattern, init_content)
        for attr, name, value in matches:
            if name.startswith('b'):
                if name not in boats_data:
                    boats_data[name] = {}
                boats_data[name][attr] = float(value)
            elif name.startswith('p'):
                if name not in persons_data:
                    persons_data[name] = {}
                persons_data[name][attr] = float(value)
    return boats_data, persons_data

def parse_goal(pddl_text):
    """
    Parses the PDDL text to extract which persons are saved.
    Instead of restricting to a goal block, we simply look for all instances of (saved pX).
    Returns a set of person names.
    """
    saved_set = set(re.findall(r'\(saved\s+(p\d+)\)', pddl_text, flags=re.DOTALL | re.MULTILINE))
    return saved_set

def convert_pddl_to_json(pddl_text):
    """
    Converts the PDDL problem to a JSON structure.
    Boats and persons are derived from the :init assignments.
      - Each boat gets "x", "y" and an "index" parsed from its name.
      - Each person gets "d", "saved": false, and an "index" parsed from its name.
    The goal field lists the indices of persons that are saved.
    """
    boats_data, persons_data = parse_init(pddl_text)
    goal_saved = parse_goal(pddl_text)
    
    boats = []
    for boat in sorted(boats_data.keys(), key=lambda b: int("".join(filter(str.isdigit, b)))):
        index = int("".join(filter(str.isdigit, boat)))
        boat_entry = {
            "x": boats_data.get(boat, {}).get("x", 0.0),
            "y": boats_data.get(boat, {}).get("y", 0.0),
            "index": index
        }
        boats.append(boat_entry)
    
    persons = []
    goal_indices = []
    for person in sorted(persons_data.keys(), key=lambda p: int("".join(filter(str.isdigit, p)))):
        index = int("".join(filter(str.isdigit, person)))
        person_entry = {
            "d": persons_data.get(person, {}).get("d", 0.0),
            "saved": False,  # Everyone starts unsaved.
            "index": index
        }
        persons.append(person_entry)
        if person in goal_saved:
            goal_indices.append(index)
    
    return {
        "boats": boats,
        "persons": persons,
        "goal": {
            "saved_persons": goal_indices
        }
    }

def main(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    files = sorted([f for f in os.listdir(input_dir) if f.endswith('.pddl')])
    if not files:
        print("No PDDL files found in the input directory.")
        return
    
    for file in files:
        input_path = os.path.join(input_dir, file)
        with open(input_path, "r") as infile:
            pddl_text = infile.read()
        
        json_state = convert_pddl_to_json(pddl_text)
        output_filename = file.rsplit(".", 1)[0] + ".json"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "w") as outfile:
            json.dump(json_state, outfile, indent=4)
        print(f"Converted {file} -> {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDDL sailing problems to JSON format without parsing objects.")
    parser.add_argument("--input_dir", required=True, help="Directory containing PDDL problem files.")
    parser.add_argument("--output_dir", required=True, help="Directory to store JSON output files.")
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
