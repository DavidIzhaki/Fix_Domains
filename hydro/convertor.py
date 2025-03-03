import re
import json

def extract_time_objects(pddl_string):
    """
    Extracts time objects from the :objects block.
    Looks for a line ending with '- time' and splits the tokens.
    """
    time_objects = []
    objects_match = re.search(r'\(:objects(.*?)\)', pddl_string, re.DOTALL | re.IGNORECASE)
    if objects_match:
        objects_text = objects_match.group(1)
        # Process each line in the objects block
        for line in objects_text.splitlines():
            line = line.strip()
            # Look for the line defining time objects (ends with "- time")
            if line.endswith("- time"):
                # Split the line on " -", taking the tokens before the type
                parts = line.rsplit(" -", 1)
                if parts:
                    tokens = parts[0].strip().split()
                    time_objects.extend(tokens)
    return time_objects

def pddl_to_json(pddl_string):
    flags = re.IGNORECASE

    # 1. Build a mapping from node name (e.g., n7) to its numeric value.
    node_mapping = {}
    for match in re.findall(r'\(=\s+\(value\s+(n\d+)\)\s+(\d+)\)', pddl_string, flags):
        node, value = match
        node_mapping[node] = int(value)
    
    # 2. Extract initial funds, e.g. (= (funds) 1000)
    funds_match = re.search(r'\(=\s+\(funds\)\s+(\d+)\)', pddl_string, flags)
    funds = int(funds_match.group(1)) if funds_match else None

    # 3. Extract stored capacity, e.g. (= (stored_capacity) 3)
    capacity_match = re.search(r'\(=\s+\(stored_capacity\)\s+(\d+)\)', pddl_string, flags)
    capacity = int(capacity_match.group(1)) if capacity_match else None

    # 4. Extract goal funds from the goal section: (>= (funds) 1060)
    goal_match = re.search(r'\(\>=\s+\(funds\)\s+(\d+)\)', pddl_string, flags)
    goal_funds = int(goal_match.group(1)) if goal_match else None

    # 5. Extract the list of time objects and create a mapping from time symbol to sequential index.
    time_objects = extract_time_objects(pddl_string)
    time_index_map = { time_sym: idx for idx, time_sym in enumerate(time_objects) }
    time_end = len(time_objects)  # planning horizon is the number of time points

    # 6. Extract demand predicates: (demand tXXXX nX)
    # Instead of converting tXXXX to an integer, we look up its index.
    demands = {}
    for time_sym, node_sym in re.findall(r'\(demand\s+(t\d+)\s+(n\d+)\)', pddl_string, flags):
        idx = time_index_map.get(time_sym)
        if idx is None:
            continue  # Skip if the time symbol wasn't found in the objects block
        value = node_mapping.get(node_sym)
        if value is not None:
            demands[idx] = value

    return {
        "funds": funds,
        "goal_funds": goal_funds,
        "capacity": capacity,
        "time_end": time_end,
        "demands": demands
    }

def main():
    # Set the path to your PDDL file. Use a raw string to handle Windows paths.
    pddl_file_path = "problems\pfile20.pddl"
    output_json_path = "Problem20.json"
    
    try:
        with open(pddl_file_path, "r", encoding="utf-8") as f:
            pddl_content = f.read()
    except FileNotFoundError:
        print("Error: PDDL file not found. Please check the file path.")
        return

    result = pddl_to_json(pddl_content)
 
    
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    

if __name__ == "__main__":
    main()
