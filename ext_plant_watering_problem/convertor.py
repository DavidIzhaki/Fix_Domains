import os
import re
import json

def parse_goal(goal_block):
    """
    Parses the goal block and returns a dictionary matching the Rust Goal struct:
      {
          "conditions": [ { "plant_index": int, "poured_amount": int }, ... ],
          "total_operator": str
      }
      
    It uses a regex that captures conditions with an operator (like =, >=, etc.).
    For plant goals, we expect a condition of the form:
        (<operator> (poured plantX) <value>)
    For the total condition, we expect:
        (<operator> (total_poured) (total_loaded))
    If the total condition is not found, total_operator defaults to "=".
    """
    conditions = []
    total_operator = "="  # default operator
    
    # Pattern matches operators: =, >=, <=, >, <, !=
    # It expects a condition of the form: (<op> (<predicate> <object>?) <rhs>)
    pattern = re.compile(r"\((=|>=|<=|>|<|!=)\s*\(([^)]+)\)\s+([^)]+)\)")
    matches = pattern.findall(goal_block)
    
    for op, lhs, rhs in matches:
        lhs_parts = lhs.strip().split()
        # If it's a plant goal, e.g., (poured plant1) 4
        if len(lhs_parts) == 2 and lhs_parts[0] == "poured" and lhs_parts[1].startswith("plant"):
            try:
                condition = {
                    "plant_index": int(re.search(r"\d+", lhs_parts[1]).group()),
                    "poured_amount": int(rhs)
                }
                conditions.append(condition)
            except (AttributeError, ValueError):
                # Skip if parsing fails.
                pass
        # Check for total condition: (total_poured) (total_loaded)
        elif lhs.strip() == "total_poured" and rhs.strip() == "total_loaded":
            total_operator = op
        # Other conditions can be ignored for now.
    
    return {"conditions": conditions, "total_operator": total_operator}

def parse_pddl(file_content):
    """
    Parse a PDDL problem file content and return a JSON structure with two top-level keys:
      - "state": Contains tap, robots (as a list), plants (as a list), total_poured, total_loaded.
      - "problem": Contains grid boundaries (max_x, max_y, min_x, min_y) and goal.
    """
    temp = {
        "tap": {"x": None, "y": None, "water_amount": None},
        "robots": {},
        "plants": {},
        "max_x": None,
        "max_y": None,
        "min_x": None,
        "min_y": None,
        "goal": {}
    }
    
    # 1. Extract grid boundaries.
    boundary_patterns = {
        "max_x": r"\(=\s*\(maxx\)\s+(\d+)\)",
        "min_x": r"\(=\s*\(minx\)\s+(\d+)\)",
        "max_y": r"\(=\s*\(maxy\)\s+(\d+)\)",
        "min_y": r"\(=\s*\(miny\)\s+(\d+)\)"
    }
    for key, pattern in boundary_patterns.items():
        m = re.search(pattern, file_content)
        if m:
            temp[key] = int(m.group(1))
    
    # 2. Extract water reserve for the tap.
    m = re.search(r"\(=\s*\(water_reserve\)\s+(\d+)\)", file_content)
    if m:
        water_amount = int(m.group(1))
    else:
        water_amount = 0
    
    # 3. Extract all assignment lines.
    # Expected assignments: (predicate object) value
    assignments = re.findall(r"\(=\s*\((\w+)\s+(\w+)\)\s+(\d+)\)", file_content)
    for predicate, obj, val in assignments:
        value = int(val)
        if predicate == "x":
            if obj.startswith("plant"):
                if obj not in temp["plants"]:
                    index = int(re.search(r"\d+", obj).group())
                    temp["plants"][obj] = {"index": index, "x": None, "y": None, "poured": 0}
                temp["plants"][obj]["x"] = value
            elif obj.startswith("agent"):
                if obj not in temp["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    temp["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                temp["robots"][obj]["x"] = value
            elif obj.startswith("tap"):
                temp["tap"]["x"] = value
        elif predicate == "y":
            if obj.startswith("plant"):
                if obj not in temp["plants"]:
                    index = int(re.search(r"\d+", obj).group())
                    temp["plants"][obj] = {"index": index, "x": None, "y": None, "poured": 0}
                temp["plants"][obj]["y"] = value
            elif obj.startswith("agent"):
                if obj not in temp["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    temp["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                temp["robots"][obj]["y"] = value
            elif obj.startswith("tap"):
                temp["tap"]["y"] = value
        elif predicate == "poured":
            if obj.startswith("plant"):
                if obj not in temp["plants"]:
                    index = int(re.search(r"\d+", obj).group())
                    temp["plants"][obj] = {"index": index, "x": None, "y": None, "poured": 0}
                # poured initially 0 (or you can update if needed)
                temp["plants"][obj]["poured"] = 0
        elif predicate == "carrying":
            if obj.startswith("agent"):
                if obj not in temp["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    temp["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                temp["robots"][obj]["carry"] = value
        elif predicate == "max_carry":
            if obj.startswith("agent"):
                if obj not in temp["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    temp["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                temp["robots"][obj]["max_carry"] = value

    # 4. Extract the goal block.
    goal_start = file_content.find("(:goal")
    if goal_start != -1:
        index = goal_start + len("(:goal")
        counter = 1  # already passed "(:goal"
        goal_str = ""
        while index < len(file_content) and counter > 0:
            char = file_content[index]
            goal_str += char
            if char == "(":
                counter += 1
            elif char == ")":
                counter -= 1
            index += 1
        temp["goal"] = parse_goal(goal_str.strip())
    
    # Set water_amount in tap.
    temp["tap"]["water_amount"] = water_amount

    # 5. Build final JSON structure.
    # Build the state according to the Rust State struct.
    state = {
        "robots": list(temp["robots"].values()),
        "plants": list(temp["plants"].values()),
        "tap": temp["tap"],
        "total_poured": 0,
        "total_loaded": 0
    }
    
    # Build the problem according to ExtPlantWateringProblem.
    problem = {
        "goal": temp["goal"],
        "max_x": temp["max_x"],
        "max_y": temp["max_y"],
        "min_x": temp["min_x"],
        "min_y": temp["min_y"]
    }
    
    return {"state": state, "problem": problem}

def process_directory(input_dir, output_dir):
    """
    Process all PDDL files in input_dir, parse them, and write JSON files to output_dir.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pddl"):
            input_path = os.path.join(input_dir, filename)
            with open(input_path, "r") as infile:
                file_content = infile.read()
            parsed_data = parse_pddl(file_content)
            
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, "w") as outfile:
                json.dump(parsed_data, outfile, indent=4)
            print(f"Converted {filename} to {output_filename}")

def main():
    # Set the input and output directories.
    input_directory = "problems_pddl"  # Folder containing your PDDL files.
    output_directory = "output_json_problems"  # Folder where JSON files will be written.
    process_directory(input_directory, output_directory)

if __name__ == "__main__":
    main()
