#!/usr/bin/env python3
import os
import re
import json
import argparse

def remove_comments(text):
    """Remove lines starting with ';' (PDDL comments)."""
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith(";"))

def parse_objects(pddl):
    """
    Parse the objects block.
    Captures everything between "(:objects" and "(:init".
    Returns three dictionaries mapping object names to indices.
    """
    objects_match = re.search(r"\(:objects(.*?)\(:init", pddl, re.DOTALL | re.IGNORECASE)
    if not objects_match:
        raise ValueError("No :objects block found.")
    objects_text = objects_match.group(1).strip().rstrip(")")
    lines = objects_text.splitlines()
    aircraft = {}
    persons = {}
    cities = {}
    for line in lines:
        line = line.strip().rstrip(")")
        if not line or '-' not in line:
            continue
        parts = line.split("-")
        names_str = parts[0].strip()
        typ = parts[1].strip().lower()
        names = names_str.split()
        if typ == "aircraft":
            for name in names:
                if name not in aircraft:
                    aircraft[name] = len(aircraft)
        elif typ == "person":
            for name in names:
                if name not in persons:
                    persons[name] = len(persons)
        elif typ == "city":
            for name in names:
                if name not in cities:
                    cities[name] = len(cities)
    return aircraft, persons, cities

def parse_init(pddl, aircraft, persons, cities):
    """
    Parse the init block.
    Captures everything between "(:init" and "(:goal".
    Returns:
      aircraft_info, persons_info, distances, total_fuel_used, total_time.
    """
    init_match = re.search(r"\(:init(.*?)\(:goal", pddl, re.DOTALL | re.IGNORECASE)
    if not init_match:
        raise ValueError("No :init block found.")
    init_text = init_match.group(1).strip()

    aircraft_info = { name: {} for name in aircraft }
    persons_info = { name: {} for name in persons }
    distances = {}

    # Process "located" predicates.
    located_re = re.compile(r"\(located\s+(\S+)\s+(\S+)\)", re.IGNORECASE)
    for match in located_re.finditer(init_text):
        obj, loc = match.groups()
        if obj in aircraft and loc in cities:
            aircraft_info[obj]["location"] = cities[loc]
        elif obj in persons and loc in cities:
            persons_info[obj]["location"] = cities[loc]
    
    def num_re(predicate):
        return re.compile(r"\(=\s*\(" + re.escape(predicate) + r"\s+(\S+)\)\s+(\d+)\)", re.DOTALL | re.IGNORECASE)
    
    # Numeric predicates for aircraft.
    for regex, key in [
        (num_re("capacity"), "capacity"),
        (num_re("fuel"), "fuel"),
        (num_re("slow-burn"), "slow_burn"),
        (num_re("fast-burn"), "fast_burn"),
        (num_re("onboard"), "onboard"),
        (num_re("zoom-limit"), "zoom_limit"),
        (num_re("slow-speed"), "slow_speed"),
        (num_re("fast-speed"), "fast_speed")
    ]:
        for match in regex.finditer(init_text):
            plane, value = match.groups()
            if plane in aircraft_info:
                aircraft_info[plane][key] = int(value)
                
    # Process distances.
    distance_re = re.compile(r"\(=\s*\(distance\s+(\S+)\s+(\S+)\)\s+(\d+)\)", re.DOTALL | re.IGNORECASE)
    for match in distance_re.finditer(init_text):
        city1, city2, dist = match.groups()
        if city1 in cities and city2 in cities:
            i1 = cities[city1]
            i2 = cities[city2]
            key = f"{i1},{i2}"
            distances[key] = int(dist)
    
    # Process total fuel and total time.
    total_fuel_re = re.compile(r"\(=\s*\(total-fuel-used\)\s+(\d+)\)", re.DOTALL | re.IGNORECASE)
    total_time_re = re.compile(r"\(=\s*\(total-time\)\s+(\d+)\)", re.DOTALL | re.IGNORECASE)
    total_fuel_used = int(total_fuel_re.search(init_text).group(1)) if total_fuel_re.search(init_text) else 0
    total_time = float(total_time_re.search(init_text).group(1)) if total_time_re.search(init_text) else 0.0
    
    # Set defaults if missing.
    for plane in aircraft_info:
        if "location" not in aircraft_info[plane]:
            aircraft_info[plane]["location"] = 0
        for key in ["capacity", "fuel", "slow_burn", "fast_burn", "onboard", "zoom_limit", "slow_speed", "fast_speed"]:
            if key not in aircraft_info[plane]:
                aircraft_info[plane][key] = 0
    for p in persons_info:
        if "location" not in persons_info[p]:
            persons_info[p]["location"] = 0
        persons_info[p]["on_airplane"] = -1
    
    return aircraft_info, persons_info, distances, total_fuel_used, total_time

def extract_metric_block(pddl):
    """
    Extract the complete metric block, balancing parentheses.
    Returns the full substring starting from "(:metric" up to its matching closing parenthesis.
    If no metric block is found, returns None.
    """
    lower_pddl = pddl.lower()
    start_index = lower_pddl.find("(:metric")
    
    if start_index == -1:
        return None
    count = 0
    end_index = start_index
    for i, char in enumerate(pddl[start_index:], start=start_index):
        if char == '(':
            count += 1
        elif char == ')':
            count -= 1
            if count == 0:
                end_index = i
                break
    return pddl[start_index:end_index+1]

def extract_metric_block(pddl):
    """
    Extract the complete metric block, balancing parentheses.
    Returns the substring from "(:metric" up to its matching closing parenthesis.
    If no metric block is found, returns None.
    """
    lower_pddl = pddl.lower()
    start_index = lower_pddl.find("(:metric")
    if start_index == -1:
        return None
    count = 0
    end_index = start_index
    for i, char in enumerate(pddl[start_index:], start=start_index):
        if char == '(':
            count += 1
        elif char == ')':
            count -= 1
            if count == 0:
                end_index = i
                break
    return pddl[start_index:end_index+1]

def parse_metric(pddl):
    """
    Parse the metric block.
    
    Recognizes three cases:
      1. A * total-time           -> returns { "fuel": 0, "time": A }
      2. A * total-fuel-used      -> returns { "fuel": A, "time": 0 }
      3. A * total-time + B * total-fuel-used  -> returns { "fuel": B, "time": A }
      
    If the metric block uses a keyword without an explicit coefficient, we assume the coefficient is 1.
    If no metric block is present, defaults to { "fuel": 1, "time": 1 }.
    """
    metric_block = extract_metric_block(pddl)
    if not metric_block:
        return {"fuel": 1, "time": 1}

    # Look for terms of the form: (* number (total-time)) and (* number (total-fuel-used))
    time_terms = re.findall(r"\(\*\s*(\d+)\s+\(total-time\)\)", metric_block, re.IGNORECASE)
    fuel_terms = re.findall(r"\(\*\s*(\d+)\s+\(total-fuel-used\)\)", metric_block, re.IGNORECASE)

    # If no numeric term is found but the keyword exists, default coefficient to 1.
    time_coef = int(time_terms[0]) if time_terms else (1 if "total-time" in metric_block.lower() else 0)
    fuel_coef = int(fuel_terms[0]) if fuel_terms else (1 if "total-fuel-used" in metric_block.lower() else 0)

    return {"fuel": fuel_coef, "time": time_coef}





def parse_goal(pddl, aircraft, persons, cities):
    """
    Parse the goal block.
    Splits the PDDL at the metric block (if present) and extracts all "located" predicates.
    Returns two lists:
      airplane_goals: list of [aircraft_index, goal_city_index]
      person_goals: list of [person_index, goal_city_index]
    """
    parts = re.split(r"\(:metric", pddl, flags=re.IGNORECASE)
    goal_section = parts[0]
    goal_match = re.search(r"\(:goal\s+\(and(.*)\)\s*\)", goal_section, re.DOTALL | re.IGNORECASE)
    if not goal_match:
        raise ValueError("No :goal block found.")
    goal_text = goal_match.group(1).strip()
    
    airplane_goals = []
    person_goals = []
    located_re = re.compile(r"\(located\s+(\S+)\s+(\S+)\)", re.IGNORECASE)
    for match in located_re.finditer(goal_text):
        obj, loc = match.groups()
        if loc not in cities:
            continue
        if obj in aircraft:
            airplane_goals.append([aircraft[obj], cities[loc]])
        elif obj in persons:
            person_goals.append([persons[obj], cities[loc]])
    return airplane_goals, person_goals

def convert_pddl_to_json(pddl_file_path):
    """
    Converts a PDDL file to a JSON structure matching the Rust state format.
    
    {
      "state": {
         "num_cities": int,
         "airplanes": [ { Airplane properties }, ... ],
         "distances": { "(i,j)": distance, ... },
         "persons": [ { Person properties }, ... ],
         "total_fuel_used": int,
         "total_time": float
      },
      "problem": {
         "goal": {
             "airplanes": [ [aircraft_index, goal_city_index], ... ],
             "persons": [ [person_index, goal_city_index], ... ]
         },
         "minimize": { "fuel": int, "time": int }
      }
    }
    """
    with open(pddl_file_path, "r") as f:
        pddl_raw = f.read()
    pddl = remove_comments(pddl_raw)
    aircraft, persons, cities = parse_objects(pddl)
    aircraft_info, persons_info, distances, total_fuel_used, total_time = parse_init(pddl, aircraft, persons, cities)
    num_cities = len(cities)
    
    # Build airplanes list (ordered by index).
    airplanes_list = [None] * len(aircraft)
    for name, idx in aircraft.items():
        info = aircraft_info[name]
        airplanes_list[idx] = {
            "index": idx,
            "slow_burn": info["slow_burn"],
            "slow_speed": info["slow_speed"],
            "fast_burn": info["fast_burn"],
            "fast_speed": info["fast_speed"],
            "capacity": info["capacity"],
            "fuel": info["fuel"],
            "location": info["location"],
            "zoom_limit": info["zoom_limit"],
            "onboard": info["onboard"]
        }
    
    # Build persons list (ordered by index).
    persons_list = [None] * len(persons)
    for name, idx in persons.items():
        info = persons_info[name]
        persons_list[idx] = {
            "location": info["location"],
            "on_airplane": info["on_airplane"]
        }
    
    airplane_goals, person_goals = parse_goal(pddl, aircraft, persons, cities)
    metric = parse_metric(pddl)
    
    json_data = {
        "state": {
            "num_cities": num_cities,
            "airplanes": airplanes_list,
            "distances": distances,
            "persons": persons_list,
            "total_fuel_used": total_fuel_used,
            "total_time": total_time
        },
        "problem": {
            "goal": {
                "airplanes": airplane_goals,
                "persons": person_goals
            },
            "minimize": {
      "fuel": 0,
      "time": 1
    }
        }
    }
    return json_data

def main(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pddl"):
            pddl_path = os.path.join(input_dir, filename)
            try:
                json_problem = convert_pddl_to_json(pddl_path)
                out_filename = filename.replace(".pddl", ".json")
                out_path = os.path.join(output_dir, out_filename)
                with open(out_path, "w") as out_file:
                    json.dump(json_problem, out_file, indent=2)
                print(f"Converted {pddl_path} -> {out_path}")
            except Exception as e:
                print(f"Error processing {pddl_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert zenotravel PDDL files to JSON format.")
    parser.add_argument("input_dir", help="Directory containing PDDL files.")
    parser.add_argument("output_dir", help="Directory to output JSON files.")
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
