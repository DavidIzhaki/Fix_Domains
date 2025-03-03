import os
import glob
import re
import json
import argparse

def extract_pddl_state(pddl_text):
    state = {}
    
    # --- Extract Number of Cities ---
    city_pattern = re.compile(r'\b(city\d+)\b')
    cities_found = set(city_pattern.findall(pddl_text))
    state["num_cities"] = len(cities_found)
    
    # --- Extract Airplane Attributes ---
    airplanes = {}
    
    # Patterns for attributes in the :init section.
    slow_burn_pattern = re.compile(r'\(= \(slow-burn (\w+)\)\s+(\d+)\)')
    fast_burn_pattern = re.compile(r'\(= \(fast-burn (\w+)\)\s+(\d+)\)')
    slow_speed_pattern = re.compile(r'\(= \(slow-speed (\w+)\)\s+(\d+)\)')
    fast_speed_pattern = re.compile(r'\(= \(fast-speed (\w+)\)\s+(\d+)\)')
    capacity_pattern = re.compile(r'\(= \(capacity (\w+)\)\s+(\d+)\)')
    fuel_pattern = re.compile(r'\(= \(fuel (\w+)\)\s+(\d+)\)')
    zoom_limit_pattern = re.compile(r'\(= \(zoom-limit (\w+)\)\s+(\d+)\)')
    located_pattern = re.compile(r'\(located (\w+)\s+(\w+)\)')
    
    # Helper: extract numeric index from a plane name "planeX"
    def plane_index(name):
        m = re.search(r'plane(\d+)', name)
        return int(m.group(1)) if m else name

    # Build dictionaries keyed by plane name.
    slow_burns = {m.group(1): int(m.group(2)) for m in slow_burn_pattern.finditer(pddl_text)}
    fast_burns = {m.group(1): int(m.group(2)) for m in fast_burn_pattern.finditer(pddl_text)}
    slow_speeds = {m.group(1): int(m.group(2)) for m in slow_speed_pattern.finditer(pddl_text)}
    fast_speeds = {m.group(1): int(m.group(2)) for m in fast_speed_pattern.finditer(pddl_text)}
    capacities = {m.group(1): int(m.group(2)) for m in capacity_pattern.finditer(pddl_text)}
    fuels = {m.group(1): int(m.group(2)) for m in fuel_pattern.finditer(pddl_text)}
    zoom_limits = {m.group(1): int(m.group(2)) for m in zoom_limit_pattern.finditer(pddl_text)}
    
    # Get locations for airplanes.
    locations = {}
    for m in located_pattern.finditer(pddl_text):
        obj = m.group(1)
        loc = m.group(2)
        if obj.startswith("plane"):
            locations[obj] = loc

    # Combine attributes for each airplane.
    for plane in set(list(slow_burns.keys()) + list(fast_burns.keys()) +
                     list(slow_speeds.keys()) + list(fast_speeds.keys()) +
                     list(capacities.keys()) + list(fuels.keys()) + list(zoom_limits.keys())):
        idx = plane_index(plane)
        s_speed = slow_speeds.get(plane, 0)
        f_speed = fast_speeds.get(plane, 0)
        
        # Get location index (e.g., "city0" becomes 0)
        loc = locations.get(plane, None)
        if loc:
            loc_match = re.search(r'city(\d+)', loc)
            loc_index = int(loc_match.group(1)) if loc_match else None
        else:
            loc_index = None

        z_limit = zoom_limits.get(plane, 0)
        airplanes[idx] = [
            [slow_burns.get(plane, 0), s_speed],
            [fast_burns.get(plane, 0), f_speed],
            [capacities.get(plane, 0), fuels.get(plane, 0)],
            [loc_index, z_limit]
        ]
    state["airplanes"] = airplanes

    # --- Extract Distances ---
    distances = {}
    distance_pattern = re.compile(r'\(= \(distance (\w+)\s+(\w+)\)\s+(\d+)\)')
    for m in distance_pattern.finditer(pddl_text):
        city1 = m.group(1)
        city2 = m.group(2)
        dist = int(m.group(3))
        m1 = re.search(r'city(\d+)', city1)
        m2 = re.search(r'city(\d+)', city2)
        if m1 and m2:
            key = (int(m1.group(1)), int(m2.group(1)))
            distances[f"{key[0]}-{key[1]}"] = dist
    state["distances"] = distances

    # --- Extract Global Metrics ---
    total_fuel_pattern = re.compile(r'\(= \(total-fuel-used\)\s+(\d+)\)')
    total_time_pattern = re.compile(r'\(= \(total-time\)\s+([\d\.]+)\)')
    fuel_match = total_fuel_pattern.search(pddl_text)
    time_match = total_time_pattern.search(pddl_text)
    state["total_fuel_used"] = int(fuel_match.group(1)) if fuel_match else 0
    state["total_time"] = float(time_match.group(1)) if time_match else 0.0
    
    return state

def custom_dumps(obj, indent=1, level=0):
    """Custom JSON dumping that prints the 'airplanes' field in compact form."""
    space = " " * (indent * level)
    if isinstance(obj, dict):
        items = []
        for key, value in obj.items():
            if key == "airplanes":
                # Dump airplanes value compactly.
                compact = json.dumps(value, separators=(',', ':'))
                items.append(f'{space}"{key}": {compact}')
            else:
                items.append(f'{space}"{key}": {custom_dumps(value, indent, level+1)}')
        inner = ",\n".join(items)
        return "{\n" + inner + "\n" + space + "}"
    elif isinstance(obj, list):
        # For lists, dump each element recursively.
        items = [custom_dumps(item, indent, level+1) for item in obj]
        inner = ",\n".join(" " * (indent * (level+1)) + item for item in items)
        return "[\n" + inner + "\n" + " " * (indent * level) + "]"
    else:
        return json.dumps(obj)

def convert_all_pddl_to_json(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for file_path in glob.glob(os.path.join(input_dir, "*.pddl")):
        with open(file_path, 'r') as f:
            pddl_text = f.read()
        state = extract_pddl_state(pddl_text)
        base_name = os.path.basename(file_path)
        json_file = os.path.splitext(base_name)[0] + ".json"
        json_path = os.path.join(output_dir, json_file)
        # Use our custom_dumps function
        with open(json_path, 'w') as f:
            f.write(custom_dumps(state, indent=1))
        print(f"Converted {file_path} -> {json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert multiple PDDL problem files to JSON state representation."
    )
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Path to the input directory containing PDDL files.")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="Path to the output directory for JSON files.")
    args = parser.parse_args()
    
    convert_all_pddl_to_json(args.input_dir, args.output_dir)
