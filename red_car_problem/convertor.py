import os
import re
import json
import sys
from collections import OrderedDict

def remove_comments(text):
    """Remove lines that start with ';'."""
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith(";"))

def parse_grid_from_cubes(content):
    """
    Finds all cube tokens matching 'cube-x<num>-y<num>' in the entire content.
    Computes grid dimensions as:
       col_size = max_x + 1,
       row_size = max_y + 1.
    If no cubes are found, defaults to 6x6.
    """
    cubes = re.findall(r'cube-x(\d+)-y(\d+)', content, re.IGNORECASE)
    if not cubes:
        return 6, 6
    max_x = max(int(x) for x, _ in cubes)
    max_y = max(int(y) for _, y in cubes)
    return max_y + 1, max_x + 1

def extract_section(content, section_start, section_end):
    """
    Extracts a section from content starting with section_start until section_end.
    If section_end is not found, returns content from section_start to the end.
    """
    start = content.find(section_start)
    if start == -1:
        raise ValueError(f"Section '{section_start}' not found.")
    end = content.find(section_end, start)
    if end == -1:
        return content[start:]
    return content[start:end]

def extract_init_section(content):
    """Extracts the init section between '(:init' and '(:goal'."""
    return extract_section(content, "(:init", "(:goal")

def parse_at_predicates(init_text):
    """
    Finds all at predicates of the form:
      (at-car-horizontal <vehicle> cube-x<num>-y<num> ...)
      (at-car-vertical <vehicle> cube-x<num>-y<num> ...)
      (at-truck-horizontal <vehicle> cube-x<num>-y<num> ...)
      (at-truck-vertical <vehicle> cube-x<num>-y<num> ...)
    and extracts the vehicle name and the x, y coordinates from the first cube.
    Returns a list of dictionaries with keys: name, x, y, and type.
    """
    pattern = re.compile(
        r'\((at-car-horizontal|at-car-vertical|at-truck-horizontal|at-truck-vertical)\s+(\S+)\s+(cube-x(\d+)-y(\d+))',
        re.IGNORECASE)
    vehicles = []
    for m in pattern.finditer(init_text):
        veh_type = m.group(1).lower()  # e.g., "at-car-horizontal"
        name = m.group(2)
        x = int(m.group(4))
        y = int(m.group(5))
        vehicles.append({"name": name, "x": x, "y": y, "type": veh_type})
    return vehicles

def partition_vehicles(vehicles):
    """
    Partitions vehicles into four lists by type and removes the temporary "type" field.
    Returns a tuple of lists:
       (horizontalcars, verticalcars, horizontaltrucks, verticaltrucks)
    Each vehicle is stored as an OrderedDict with keys in the order: "x", "y", "name".
    """
    horizontalcars = []
    verticalcars = []
    horizontaltrucks = []
    verticaltrucks = []
    for v in vehicles:
        v_type = v.pop("type")
        entry = OrderedDict([("x", v["x"]), ("y", v["y"]), ("name", v["name"])])
        if v_type == "at-car-horizontal":
            horizontalcars.append(entry)
        elif v_type == "at-car-vertical":
            verticalcars.append(entry)
        elif v_type == "at-truck-horizontal":
            horizontaltrucks.append(entry)
        elif v_type == "at-truck-vertical":
            verticaltrucks.append(entry)
    return horizontalcars, verticalcars, horizontaltrucks, verticaltrucks

def parse_pddl_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    content_clean = remove_comments(content)
    
    # Compute grid dimensions from all cubes in the file.
    row_size, col_size = parse_grid_from_cubes(content_clean)
    
    # Extract the init section.
    init_section = extract_init_section(content_clean)
    
    # Parse the at predicates in the init section.
    vehicles = parse_at_predicates(init_section)
    horizontalcars, verticalcars, horizontaltrucks, verticaltrucks = partition_vehicles(vehicles)
    
    grid = {"row_size": row_size, "col_size": col_size, "cells": {}}
    state = {
        "grid": grid,
        "horizontalcars": horizontalcars,
        "verticalcars": verticalcars,
        "horizontaltrucks": horizontaltrucks,
        "verticaltrucks": verticaltrucks
    }
    return {"state": state}

def main(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    i = 1
    for filename in os.listdir(input_dir):
       
        if filename.endswith('.pddl'):
            filepath = os.path.join(input_dir, filename)
            try:
                result = parse_pddl_file(filepath)
                out_filename =  f"pfile{i}.json"
                out_filepath = os.path.join(output_dir, out_filename)
                with open(out_filepath, 'w') as out_file:
                    json.dump(result, out_file, indent=4)
                print(f"Converted {filename} to {out_filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
            i += 1

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convert_from_cubes.py <input_dir> <output_dir>")
    else:
        main(sys.argv[1], sys.argv[2])
