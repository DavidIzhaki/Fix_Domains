import re
import json
import os
import sys

def convert_location(loc_str):
    """Converts a location string:
       - If it starts with 'depot', returns -1.
       - If it starts with 'market', returns (market number - 1).
       Otherwise, returns the original string.
    """
    if loc_str.startswith("depot"):
        return -1
    elif loc_str.startswith("market"):
        m = re.search(r'\d+', loc_str)
        if m:
            return int(m.group(0)) - 1
    return loc_str

def parse_objects(pddl_text):
    """Parses the objects section to build a dictionary mapping types to list of names."""
    objects_by_type = {}
    m = re.search(r'\(:objects(.*?)\)', pddl_text, re.DOTALL)
    if m:
        objects_section = m.group(1)
        for line in objects_section.splitlines():
            line = line.strip()
            if not line:
                continue
            if '-' in line:
                parts = line.split('-')
                names = parts[0].strip().split()
                type_name = parts[1].strip()
                objects_by_type.setdefault(type_name, []).extend(names)
    return objects_by_type

def parse_truck_locations(init_section):
    """Parses all (loc truck depot) statements and returns a dict mapping truck name to its location."""
    truck_locations = {}
    loc_pattern = re.compile(r'\(loc\s+(\S+)\s+(\S+)\)', re.IGNORECASE)
    for truck, loc in loc_pattern.findall(init_section):
        truck_locations[truck] = convert_location(loc)
    return truck_locations

def parse_market_items(init_section):
    """Parses price and on-sale info for markets.
       Returns a dictionary mapping market name to its items.
       Each item is stored as: { goods_id: { "price": price, "on_sale": on_sale } }
    """
    market_items = {}
    price_pattern = re.compile(r'\(=\s+\(price\s+(\S+)\s+(\S+)\)\s+([\d\.]+)\)', re.IGNORECASE)
    for good, market, price in price_pattern.findall(init_section):
        price = float(price)
        if market not in market_items:
            market_items[market] = {}
        m_good = re.search(r'\d+', good)
        if m_good:
            good_id = m_good.group(0)  # keep as string
            market_items[market].setdefault(good_id, {})["price"] = price

    on_sale_pattern = re.compile(r'\(=\s+\(on-sale\s+(\S+)\s+(\S+)\)\s+(\d+)\)', re.IGNORECASE)
    for good, market, on_sale in on_sale_pattern.findall(init_section):
        on_sale = int(on_sale)
        if market not in market_items:
            market_items[market] = {}
        m_good = re.search(r'\d+', good)
        if m_good:
            good_id = m_good.group(0)
            entry = market_items[market].setdefault(good_id, {})
            entry["on_sale"] = on_sale
            # If on_sale is 0 and price isn't set, set price to 0.
            if on_sale == 0 and "price" not in entry:
                entry["price"] = 0
    return market_items

def parse_pddl(pddl_text):
    # Remove comment lines (those starting with ";;")
    pddl_text = re.sub(r";;.*", "", pddl_text)

    # Initialize the output structure.
    output = {
        "state": {
            "trucks": [],
            "markets": [],
            "items_bought": {},  # from (bought ...) statements
            "total_cost": 0
        },
        "problem": {
            "distances": {},    # from (drive-cost ...) statements; keys as strings "(from,to)"
            "goal": {
                "goal_requests": {}  # mapping goods id -> requested amount
            }
        }
    }

    # ----- Extract the INIT section -----
    init_split = re.split(r'\(:goal', pddl_text, flags=re.DOTALL)
    if len(init_split) < 2:
        print("Could not find a (:goal section. Check the PDDL file format.")
        init_section = ""
    else:
        init_section = init_split[0]
        # Remove the (:init header.
        init_section = re.sub(r'^\s*\(:init', '', init_section, count=1).strip()

    # ----- Parse objects section for trucks and markets -----
    objects_by_type = parse_objects(pddl_text)

    # ----- Parse trucks -----
    truck_locations = parse_truck_locations(init_section)
    state_trucks = []
    for truck in objects_by_type.get("truck", []):
        # Default truck location to -1 if not found
        loc = truck_locations.get(truck, -1)
        state_trucks.append({"name": truck, "location": loc})
    output["state"]["trucks"] = state_trucks

    # ----- Parse markets -----
    market_items = parse_market_items(init_section)
    state_markets = []
    for market in objects_by_type.get("market", []):
        state_markets.append({
            "location": str(convert_location(market)),
            "items": market_items.get(market, {})
        })
    output["state"]["markets"] = state_markets

    # ----- Parse distances -----
    # Instead of a nested dict, we now create a flat dict where each key is a string "({from},{to})"
    drive_cost_pattern = re.compile(r'\(=\s+\(drive-cost\s+(\S+)\s+(\S+)\)\s+([\d\.]+)\)', re.IGNORECASE)
    distances = {}
    for from_loc, to_loc, cost in drive_cost_pattern.findall(init_section):
        cost = float(cost)
        conv_from = str(convert_location(from_loc))
        conv_to = str(convert_location(to_loc))
        key = f"({conv_from},{conv_to})"
        distances[key] = cost
    output["problem"]["distances"] = distances

    # ----- Parse bought statements -----
    bought_pattern = re.compile(r'\(=\s+\(bought\s+(\S+)\)\s+(\d+)\)', re.IGNORECASE)
    items_bought = {}
    for good, number in bought_pattern.findall(init_section):
        m_good = re.search(r'\d+', good)
        if m_good:
            good_id = m_good.group(0)
            items_bought[good_id] = int(number)
    output["state"]["items_bought"] = items_bought

    # ----- Parse total-cost -----
    total_cost_pattern = re.compile(r'\(=\s+\(total-cost\)\s+(\d+)\)', re.IGNORECASE)
    m_total = total_cost_pattern.search(init_section)
    if m_total:
        output["state"]["total_cost"] = int(m_total.group(1))

    # ----- Parse request statements for goal_requests -----
    request_pattern = re.compile(r'\(=\s+\(request\s+(\S+)\)\s+(\d+)\)', re.IGNORECASE)
    goal_requests = {}
    for good, req in request_pattern.findall(init_section):
        m_good = re.search(r'\d+', good)
        if m_good:
            good_id = m_good.group(0)
            goal_requests[good_id] = int(req)
    output["problem"]["goal"]["goal_requests"] = goal_requests

    return output

def convert_pddl_directory_to_json(input_directory, output_directory):
    os.makedirs(output_directory, exist_ok=True)
    
    for filename in os.listdir(input_directory):
        if filename.endswith(".pddl"):
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r') as f:
                pddl_text = f.read()
            json_data = parse_pddl(pddl_text)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_directory, output_filename)
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=4)
            print(f"Converted {filename} -> {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pddl_to_json.py <input_directory> <output_directory>")
    else:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        convert_pddl_directory_to_json(input_dir, output_dir)
