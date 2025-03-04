import os
import re
import json

def parse_goal(goal_block):
    """
    Parses the goal block to extract plant goals and other goal conditions.
    
    Returns a dictionary with:
      - "plant_goals": mapping of plant names (e.g., "plant1") to target poured values.
      - "other_goals": list of additional goal condition strings.
    """
    plant_goals = {}
    other_goals = []
    # Find all conditions of the form: (= ( ... ) ... )
    # This regex captures the inner part of the left-hand side and the right-hand side.
    conditions = re.findall(r"\(=\s*\(([^)]+)\)\s+([^)]+)\)", goal_block)
    for lhs, rhs in conditions:
        parts = lhs.strip().split()
        # Check if it's a plant goal: predicate "poured" and second part starts with "plant"
        if len(parts) == 2 and parts[0] == "poured" and parts[1].startswith("plant"):
            try:
                plant_goals[parts[1]] = int(rhs)
            except ValueError:
                plant_goals[parts[1]] = rhs  # fallback if not numeric
        else:
            # Save the full condition as a string in other_goals.
            condition_str = f"(= ({lhs.strip()}) {rhs.strip()})"
            other_goals.append(condition_str)
    return {"plant_goals": plant_goals, "other_goals": other_goals}

def parse_pddl(file_content):
    """
    Parse a PDDL problem file content and return a JSON structure with:
      - water-amount (from water_reserve)
      - tap (with name, x, and y)
      - robots (with index, x, y, max_carry, carry)
      - plants (with index, x, y, poured)
      - grid boundaries (max_x, min_x, max_y, min_y)
      - goal (structured: plant_goals and other_goals)
    """
    result = {
        "water-amount": None,
        "tap": {"name": None, "x": None, "y": None},
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
            result[key] = int(m.group(1))
    
    # 2. Extract water reserve (water-amount).
    m = re.search(r"\(=\s*\(water_reserve\)\s+(\d+)\)", file_content)
    if m:
        result["water-amount"] = int(m.group(1))
    
    # 3. Use a general regex to capture all assignment lines:
    #    Pattern: (=\s*(<predicate> <object>) <value>)
    assignments = re.findall(r"\(=\s*\((\w+)\s+(\w+)\)\s+(\d+)\)", file_content)
    for predicate, obj, val in assignments:
        value = int(val)
        # Process x and y coordinates
        if predicate == "x":
            if obj.startswith("plant"):
                if obj not in result["plants"]:
                    index = int(re.search(r"\d+", obj).group())
                    result["plants"][obj] = {"index": index, "x": None, "y": None, "poured": None}
                result["plants"][obj]["x"] = value
            elif obj.startswith("agent"):
                if obj not in result["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    result["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                result["robots"][obj]["x"] = value
            elif obj.startswith("tap"):
                result["tap"]["name"] = obj
                result["tap"]["x"] = value
        elif predicate == "y":
            if obj.startswith("plant"):
                if obj not in result["plants"]:
                    index = int(re.search(r"\d+", obj).group())
                    result["plants"][obj] = {"index": index, "x": None, "y": None, "poured": None}
                result["plants"][obj]["y"] = value
            elif obj.startswith("agent"):
                if obj not in result["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    result["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                result["robots"][obj]["y"] = value
            elif obj.startswith("tap"):
                result["tap"]["name"] = obj
                result["tap"]["y"] = value
        # Process poured amounts for plants.
        elif predicate == "poured":
            if obj.startswith("plant"):
                if obj not in result["plants"]:
                    index = int(re.search(r"\d+", obj).group())
                    result["plants"][obj] = {"index": index, "x": None, "y": None, "poured": None}
                result["plants"][obj]["poured"] = value
        # Process carrying and max_carry for agents.
        elif predicate == "carrying":
            if obj.startswith("agent"):
                if obj not in result["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    result["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                result["robots"][obj]["carry"] = value
        elif predicate == "max_carry":
            if obj.startswith("agent"):
                if obj not in result["robots"]:
                    index = int(re.search(r"\d+", obj).group())
                    result["robots"][obj] = {"index": index, "x": None, "y": None, "max_carry": None, "carry": None}
                result["robots"][obj]["max_carry"] = value

    # 4. Extract the goal block using a parenthesis counter.
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
        # Parse the goal block into structured goals.
        result["goal"] = parse_goal(goal_str.strip())
    
    return result

def process_directory(input_dir, output_dir):
    """
    Process all PDDL files in input_dir, parse them, and write JSON files to output_dir.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process all files ending with .pddl
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pddl"):
            input_path = os.path.join(input_dir, filename)
            with open(input_path, "r") as infile:
                file_content = infile.read()
            parsed_data = parse_pddl(file_content)
            
            # Create an output filename with .json extension.
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, "w") as outfile:
                json.dump(parsed_data, outfile, indent=4)
            print(f"Converted {filename} to {output_filename}")

def main():
    # Set the input and output directories.
    input_directory = "problems_pddl"  # Folder containing your 20 PDDL files.
    output_directory = "output_json_problems"  # Folder where JSON files will be written.
    
    process_directory(input_directory, output_directory)

if __name__ == "__main__":
    main()
