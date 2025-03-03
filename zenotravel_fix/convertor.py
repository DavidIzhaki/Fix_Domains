import os
import glob
import re
import json
import argparse

def extract_pddl_state(pddl_text):
    state = {}
    
    # --- Extract Number of Cities ---
    city_pattern = re.compile(r'\bcity(\d+)\b')
    # Extract all numeric city identifiers and count unique ones
    cities_found = {int(num) for num in city_pattern.findall(pddl_text)}
    state["num_cities"] = len(cities_found)
    
    # --- Patterns for Airplane Attributes ---
    slow_burn_pattern = re.compile(r'\(= \(slow-burn (\w+)\)\s+(\d+)\)')
    fast_burn_pattern = re.compile(r'\(= \(fast-burn (\w+)\)\s+(\d+)\)')
    slow_speed_pattern = re.compile(r'\(= \(slow-speed (\w+)\)\s+(\d+)\)')
    fast_speed_pattern = re.compile(r'\(= \(fast-speed (\w+)\)\s+(\d+)\)')
    capacity_pattern = re.compile(r'\(= \(capacity (\w+)\)\s+(\d+)\)')
    fuel_pattern = re.compile(r'\(= \(fuel (\w+)\)\s+(\d+)\)')
    zoom_limit_pattern = re.compile(r'\(= \(zoom-limit (\w+)\)\s+(\d+)\)')
    
    # --- Dedicated Patterns for Locations ---
    airplane_pattern = re.compile(r'\(located (plane\d+)\s+(city\d+)\)')
    
    def plane_index(name):
        m = re.search(r'plane(\d+)', name)
        return int(m.group(1)) if m else None
    
    # --- Extract Airplane Attribute Dictionaries ---
    slow_burns = {m.group(1): int(m.group(2)) for m in slow_burn_pattern.finditer(pddl_text)}
    fast_burns = {m.group(1): int(m.group(2)) for m in fast_burn_pattern.finditer(pddl_text)}
    slow_speeds = {m.group(1): int(m.group(2)) for m in slow_speed_pattern.finditer(pddl_text)}
    fast_speeds = {m.group(1): int(m.group(2)) for m in fast_speed_pattern.finditer(pddl_text)}
    capacities = {m.group(1): int(m.group(2)) for m in capacity_pattern.finditer(pddl_text)}
    fuels = {m.group(1): int(m.group(2)) for m in fuel_pattern.finditer(pddl_text)}
    zoom_limits = {m.group(1): int(m.group(2)) for m in zoom_limit_pattern.finditer(pddl_text)}
    
    # --- Extract Initial State `(:init ...)` Section ---
    init_match = re.search(r'\(:init(.*?)\)\s*(?:\(:goal|\(:metric|\Z)', pddl_text, re.DOTALL)
    if not init_match:
        raise ValueError("ERROR: Could not find a properly formatted (:init ...) section in PDDL!")
    init_section = init_match.group(1)
    goal_match = re.search(r'\(:goal\s*\(and(.*)\)\s*\)', pddl_text, re.DOTALL)
    if goal_match:
        goal_section = goal_match.group(1)
    else:
        print("ERROR: Could not find (:goal ...) section in PDDL!")
        exit(1)
    
    # --- Extract Airplane Locations ---
    airplane_locations = {}
    for m in airplane_pattern.finditer(init_section):
        plane_name = m.group(1)  # e.g., "plane1"
        loc = m.group(2)         # e.g., "city0"
        m_city = re.search(r'city(\d+)', loc)
        if m_city:
            airplane_locations[plane_name] = int(m_city.group(1))
    
    # --- Extract Persons ---
    person_pattern = re.compile(r'\(located\s+(person\d+)\s+(city\d+)\)')
    persons_dict = {}
    for m in person_pattern.finditer(init_section):
        person_name = m.group(1)  # e.g., "person1"
        city_str = m.group(2)     # e.g., "city4"
        person_idx = int(person_name.replace("person", ""))
        city_idx = int(city_str.replace("city", ""))
        persons_dict[person_idx] = city_idx
    
        # --- Combine Airplane Attributes into a vector ---
    airplanes_list = []
    # Get all unique plane names from the attribute dictionaries.
    plane_names = set(slow_burns.keys()) | set(fast_burns.keys()) | set(slow_speeds.keys()) | set(fast_speeds.keys()) | set(capacities.keys()) | set(fuels.keys()) | set(zoom_limits.keys())
    # Sort plane names by their index to ensure order.
    for plane in sorted(plane_names, key=lambda p: plane_index(p)):
        idx = plane_index(plane)
        if idx is None:
            continue
        # Adjust the index so that planes start at 0.
        idx = idx - 1  
        s_burn = slow_burns.get(plane, 0)
        s_speed = slow_speeds.get(plane, 0)
        f_burn = fast_burns.get(plane, 0)
        f_speed = fast_speeds.get(plane, 0)
        cap = capacities.get(plane, 0)
        fuel_val = fuels.get(plane, 0)
        z_limit = zoom_limits.get(plane, 0)
        loc_index = airplane_locations.get(plane, 0)  # default to 0 if not found
        # Build the airplane as a dict matching our new Airplane struct.
        
        airplanes_list.append({
            "index": idx,
            "slow_burn": s_burn,
            "slow_speed": s_speed,
            "fast_burn": f_burn,
            "fast_speed": f_speed,
            "capacity": cap,
            "fuel": fuel_val,
            "location": loc_index,
            "zoom_limit": z_limit,
            "onboard": 0  # default onboard count
        })

    
    state["airplanes"] = airplanes_list
    
    # --- Convert Persons Dictionary into a Vector ---
    persons_list = []
    for person_idx in sorted(persons_dict.keys()):
        persons_list.append({
            "loc": persons_dict[person_idx],
            "on_airpane": -1  # -1 indicates the person is on the ground
        })
    state["persons"] = persons_list
    
    # --- Extract Distances ---
    distances = {}
    distance_pattern = re.compile(r'\(= \(distance (\w+)\s+(\w+)\)\s+(\d+)\)')
    for m in distance_pattern.finditer(pddl_text):
        city1 = m.group(1)  # e.g., "city0"
        city2 = m.group(2)  # e.g., "city1"
        dist = int(m.group(3))
        m1 = re.search(r'city(\d+)', city1)
        m2 = re.search(r'city(\d+)', city2)
        if m1 and m2:
            key = f"{int(m1.group(1))}-{int(m2.group(1))}"
            distances[key] = dist
    state["distances"] = distances

    # --- Extract Global Metrics ---
    total_fuel_pattern = re.compile(r'\(= \(total-fuel-used\)\s+(\d+)\)')
    total_time_pattern = re.compile(r'\(= \(total-time\)\s+([\d\.]+)\)')
    fuel_match = total_fuel_pattern.search(pddl_text)
    time_match = total_time_pattern.search(pddl_text)
    state["total_fuel_used"] = int(fuel_match.group(1)) if fuel_match else 0
    state["total_time"] = float(time_match.group(1)) if time_match else 0.0

    # --- Extract Goal Conditions for Airplanes and Persons ---
    goal_airplane_pattern = re.compile(r'\(located\s+(plane\d+)\s+(city\d+)\)', re.IGNORECASE)
    goal_person_pattern = re.compile(r'\(located\s+(person\d+)\s+(city\d+)\)', re.IGNORECASE)

    goal_airplanes = {}
    for match in goal_airplane_pattern.finditer(goal_section):
        plane_idx = int(re.search(r'\d+', match.group(1)).group())
        city_idx = int(re.search(r'\d+', match.group(2)).group())
        goal_airplanes[plane_idx] = city_idx

    goal_persons = {}
    for match in goal_person_pattern.finditer(goal_section):
        person_idx = int(re.search(r'\d+', match.group(1)).group())
        city_idx = int(re.search(r'\d+', match.group(2)).group())
        goal_persons[person_idx] = city_idx

    # --- Extract the Metric ---
    metric_match = re.search(r'\(:metric\s+(minimize)\s+(\(.*\))\)', pddl_text, re.DOTALL)
    if metric_match:
        metric_type = metric_match.group(1)
        metric_expression = metric_match.group(2).strip()
        metric = {"type": metric_type, "expression": metric_expression}
    else:
        metric = None

    # --- Build the goal output (if you want to keep goal in the JSON) ---
    state["goal"] = {
        "airplanes": goal_airplanes,
        "persons": goal_persons,
        "metric": metric
    }

    return state

def custom_dumps(obj, indent=1, level=0):
    """Custom JSON dumping that prints the 'airplanes' field in compact form."""
    space = " " * (indent * level)
    if isinstance(obj, dict):
        items = []
        for key, value in obj.items():
            if key == "airplanes":
                compact = json.dumps(value, separators=(',', ':'))
                items.append(f'{space}"{key}": {compact}')
            else:
                items.append(f'{space}"{key}": {custom_dumps(value, indent, level+1)}')
        inner = ",\n".join(items)
        return "{\n" + inner + "\n" + space + "}"
    elif isinstance(obj, list):
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
        with open(json_path, 'w') as f:
            json.dump(state, f, indent=1)
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
