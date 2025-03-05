import os
import re
import json
import sys

def extract_section(content, section_start, section_end_marker):
    """
    Extracts a section from content starting with section_start and ending at section_end_marker.
    If section_end_marker is not found, returns content from section_start to the end.
    """
    start = content.find(section_start)
    if start == -1:
        raise ValueError(f"Section {section_start} not found")
    end = content.find(section_end_marker, start)
    if end == -1:
        return content[start:]
    return content[start:end]

def extract_balanced_section(text, start_marker):
    """
    Extract a section starting at start_marker until the parentheses are balanced.
    Returns the substring including the start_marker.
    """
    start = text.find(start_marker)
    if start == -1:
        raise ValueError(f"Marker {start_marker} not found")
    count = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                return text[start:i+1]
        i += 1
    raise ValueError("Unbalanced parentheses in section starting at " + start_marker)

def safe_int(pattern, text, default=None):
    """Helper to search for a pattern and return an int. Raises error if not found and no default is provided."""
    m = re.search(pattern, text)
    if m:
        return int(m.group(1))
    if default is not None:
        return default
    raise ValueError(f"Pattern not found: {pattern}")

# --- Union-Find helpers ---
def find(parent, x):
    if parent[x] != x:
        parent[x] = find(parent, parent[x])
    return parent[x]

def union(parent, a, b):
    ra = find(parent, a)
    rb = find(parent, b)
    if ra != rb:
        parent[rb] = ra

def parse_pddl_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract objects section
    objects_section = extract_section(content, "(:objects", ")")
    # Find object names that look like b1, b2, etc.
    objects = re.findall(r'\b(b\d+)\b', objects_section)
    if not objects:
        raise ValueError("No objects found in the objects section.")

    # Extract the init section.
    try:
        init_section = extract_section(content, "(:init", "(:goal")
    except ValueError:
        init_section = content[content.find("(:init"):]

    # Extract block coordinates (allowing optional spaces)
    x_coords = {m.group(1): int(m.group(2)) 
                for m in re.finditer(r'\(=\s*\(x\s+(b\d+)\)\s+(\d+)\s*\)', init_section)}
    y_coords = {m.group(1): int(m.group(2)) 
                for m in re.finditer(r'\(=\s*\(y\s+(b\d+)\)\s+(\d+)\s*\)', init_section)}

    # Extract grid boundaries.
    max_x = safe_int(r'\(=\s*\(max_x\)\s+(\d+)\s*\)', init_section)
    min_x = safe_int(r'\(=\s*\(min_x\)\s+(\d+)\s*\)', init_section)
    max_y = safe_int(r'\(=\s*\(max_y\)\s+(\d+)\s*\)', init_section)
    min_y = safe_int(r'\(=\s*\(min_y\)\s+(\d+)\s*\)', init_section)

    # Build initial blocks dictionary with dummy color_group (to be determined)
    blocks = {}
    for obj in objects:
        index = int(obj[1:])  # remove the leading 'b'
        blocks[obj] = {
            "index": index,
            "color_group": None,  # will be updated below
            "x": x_coords.get(obj, 0),
            "y": y_coords.get(obj, 0)
        }

    # Extract the goal section using balanced parentheses extraction.
    try:
        goal_section = extract_balanced_section(content, "(:goal")
    except ValueError as e:
        raise ValueError("Error extracting goal section: " + str(e))

    # Remove negative conditions from the goal section.
    # This regex removes occurrences of (not (<stuff>))
    clean_goal = re.sub(r'\(not\s*\(.*?\)\)', '', goal_section, flags=re.DOTALL)

    # Extract equality conditions for x and y coordinates.
    x_pairs = set()
    for m in re.finditer(r'\(=\s*\(x\s+(b\d+)\)\s+\(x\s+(b\d+)\)\s*\)', clean_goal):
        pair = frozenset([m.group(1), m.group(2)])
        x_pairs.add(pair)
    y_pairs = set()
    for m in re.finditer(r'\(=\s*\(y\s+(b\d+)\)\s+\(y\s+(b\d+)\)\s*\)', clean_goal):
        pair = frozenset([m.group(1), m.group(2)])
        y_pairs.add(pair)
    
    # Only consider pairs that appear in both x and y equality conditions.
    common_pairs = x_pairs.intersection(y_pairs)
    
    # Initialize union-find structure for all objects.
    parent = {obj: obj for obj in objects}
    for pair in common_pairs:
        a, b = list(pair)
        union(parent, a, b)

    # Now assign a unique group id for each connected component.
    rep_to_group = {}
    group_id = 1
    for obj in objects:
        rep = find(parent, obj)
        if rep not in rep_to_group:
            rep_to_group[rep] = group_id
            group_id += 1
        blocks[obj]["color_group"] = rep_to_group[rep]

    # Convert blocks dictionary to a list sorted by block index.
    blocks_list = [blocks[obj] for obj in sorted(blocks, key=lambda x: int(x[1:]))]

    state = {"blocks": blocks_list}
    grid = {"max_x": max_x, "min_x": min_x, "max_y": max_y, "min_y": min_y}
    return {"state": state, "grid": grid}

def main(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.pddl'):
            filepath = os.path.join(input_dir, filename)
            try:
                problem_json = parse_pddl_file(filepath)
                out_filename = os.path.splitext(filename)[0] + ".json"
                out_filepath = os.path.join(output_dir, out_filename)
                with open(out_filepath, 'w') as f:
                    json.dump(problem_json, f, indent=4)
                print(f"Converted {filename} to {out_filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convertor.py <input_dir> <output_dir>")
    else:
        main(sys.argv[1], sys.argv[2])
