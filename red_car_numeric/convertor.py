import os
import re
import sys
import json

def remove_comments(text):
    """Remove lines starting with ';'."""
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith(";"))

def extract_section(content, start_marker, end_marker):
    """
    Extracts a section from content starting with start_marker and ending at end_marker.
    If end_marker is not found, returns content from start_marker to the end.
    """
    start = content.find(start_marker)
    if start == -1:
        raise ValueError(f"Section '{start_marker}' not found.")
    end = content.find(end_marker, start)
    if end == -1:
        return content[start:]
    return content[start:end]

def extract_objects_section(content):
    """Extracts the objects section (everything between '(:objects' and the next ')')."""
    return extract_section(content, "(:objects", ")")

def extract_init_section(content):
    """Extracts the init section (everything between '(:init' and '(:goal')."""
    return extract_section(content, "(:init", "(:goal")

def parse_vehicle_declarations(objects_text):
    """
    Parses the objects section (which should now contain only vehicles) and builds a dictionary.
    Assumes the objects section is of the form:
       red-car blue-car purple-car - horizontalCar
       green-car orange-car ... - verticalCar
       ...
    Returns a dictionary mapping vehicle names to their type (in lowercase).
    This version filters out any token that starts with '('.
    """
    # Remove newlines and extra spaces.
    text = " ".join(objects_text.split())
    # Split by '-' to separate names from type.
    decls = text.split(" - ")
    vehicles = {}
    if len(decls) >= 2:
        # Process the first declaration group:
        names = [token for token in decls[0].split() if not token.startswith("(")]
        typ = decls[1].split()[0]
        for name in names:
            vehicles[name] = typ.lower()
        # Process subsequent groups (if any).
        for i in range(1, len(decls) - 1):
            names = [token for token in decls[i].split() if not token.startswith("(")]
            typ = decls[i+1].split()[0]
            for name in names:
                vehicles[name] = typ.lower()
    return vehicles

def parse_numeric_assignment(init_text, var, vehicle):
    """
    Parses the init section to extract the numeric assignment for variable var (x or y)
    for a given vehicle.
    For example, finds a line like: (= (x red-car) 3)
    Returns the numeric value as an integer, or 0 if not found.
    """
    pattern = r'\(=\s*\(' + var + r'\s+' + re.escape(vehicle) + r'\)\s+(\d+)\)'
    m = re.search(pattern, init_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 0

def parse_grid_boundaries(init_text):
    """
    Parses grid boundaries from the init section.
    Expects lines like:
      (= (min_x) 0)
      (= (max_x) 6)
      (= (min_y) 0)
      (= (max_y) 6)
    Returns a tuple (min_x, max_x, min_y, max_y) as integers.
    Defaults to (0,6,0,6) if not found.
    """
    def parse_boundary(var):
        pattern = r'\(=\s*\(' + var + r'\)\s+(\d+)\)'
        m = re.search(pattern, init_text, re.IGNORECASE)
        return int(m.group(1)) if m else None
    min_x = parse_boundary("min_x") or 0
    max_x = parse_boundary("max_x") or 6
    min_y = parse_boundary("min_y") or 0
    max_y = parse_boundary("max_y") or 6
    return min_x, max_x, min_y, max_y

def build_state_json(content):
    """
    Builds a JSON state from a numeric PDDL file.
    The state contains:
      - grid: { row_size, col_size, cells: {} }
      - horizontalcars, verticalcars, horizontaltrucks, verticaltrucks:
         lists of vehicle objects (each with keys: name, x, y).
    """
    content_clean = remove_comments(content)
    objects_sec = extract_objects_section(content_clean)
    init_sec = extract_init_section(content_clean)
    
    vehicles = parse_vehicle_declarations(objects_sec)
    
    # Build vehicle lists partitioned by type.
    horizontalcars = []
    verticalcars = []
    horizontaltrucks = []
    verticaltrucks = []
    
    for name, typ in vehicles.items():
        x_val = parse_numeric_assignment(init_sec, "x", name)
        y_val = parse_numeric_assignment(init_sec, "y", name)
        veh_obj = {"name": name, "x": x_val, "y": y_val}
        if typ == "horizontalcar":
            horizontalcars.append(veh_obj)
        elif typ == "verticalcar":
            verticalcars.append(veh_obj)
        elif typ == "horizontaltruck":
            horizontaltrucks.append(veh_obj)
        elif typ == "verticaltruck":
            verticaltrucks.append(veh_obj)
    
    # Parse grid boundaries to compute grid size.
    min_x, max_x, min_y, max_y = parse_grid_boundaries(init_sec)
    col_size = max_x  # assume max_x is already the number of columns
    row_size = max_y  # assume max_y is the number of rows
    
    state = {
        "grid": {
            "row_size": row_size,
            "col_size": col_size,
            "cells": {}  # This can be filled later if needed.
        },
        "horizontalcars": horizontalcars,
        "verticalcars": verticalcars,
        "horizontaltrucks": horizontaltrucks,
        "verticaltrucks": verticaltrucks
    }
    return {"state": state}

def convert_file(input_filepath, output_filepath):
    with open(input_filepath, 'r') as infile:
        content = infile.read()
    state_json = build_state_json(content)
    with open(output_filepath, 'w') as outfile:
        json.dump(state_json, outfile, indent=4)
    print(f"Converted {input_filepath} -> {output_filepath}")

def main(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for filename in os.listdir(input_dir):
        if filename.endswith('.pddl'):
            input_filepath = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_filepath = os.path.join(output_dir, output_filename)
            try:
                convert_file(input_filepath, output_filepath)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python batch_convert_numeric_to_json.py <input_dir> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
