#!/usr/bin/env python3
import re
import json
import os
import argparse

def parse_sleds(pddl_text):
    """Extract sled information from PDDL"""
    sled_locations = {}
    sled_supplies = {}
    sled_capacity = {}
    
    # Extract initial locations from init section only
    init_section = re.search(r'\(:init(.*?)\(:goal', pddl_text, re.DOTALL)
    if init_section:
        init_text = init_section.group(1)
        for match in re.finditer(r'\(at\s+s(\d+)\s+wa(\d+)\)', init_text):
            sled_num = str(int(match.group(1)))  # Convert s0 to "0"
            waypoint_id = 0  # Always set to 0 for initial location
            sled_locations[sled_num] = waypoint_id
    
    # Extract supplies and capacity
    for match in re.finditer(r'\(=\s*\(sled_supplies\s+s(\d+)\)\s+(\d+)\)', pddl_text):
        sled_num = str(int(match.group(1)))
        supplies = int(match.group(2))
        sled_supplies[sled_num] = supplies
        
    for match in re.finditer(r'\(=\s*\(sled_capacity\s+s(\d+)\)\s+(\d+)\)', pddl_text):
        sled_num = str(int(match.group(1)))
        capacity = int(match.group(2))
        sled_capacity[sled_num] = capacity
        
    return sled_locations, sled_supplies, sled_capacity

def parse_waypoints(pddl_text):
    """Extract waypoint information from PDDL"""
    waypoint_supplies = {}
    waypoint_connections = {}
    
    # Extract supplies
    for match in re.finditer(r'\(=\s*\(waypoint_supplies\s+wa(\d+)\)\s+(\d+)\)', pddl_text):
        waypoint_id = match.group(1)
        supplies = int(match.group(2))
        waypoint_supplies[waypoint_id] = supplies
    
    # Extract connections
    for match in re.finditer(r'\(is_next\s+wa(\d+)\s+wa(\d+)\)', pddl_text):
        from_id = match.group(1)
        to_id = match.group(2)
        if from_id not in waypoint_connections:
            waypoint_connections[from_id] = []
        waypoint_connections[from_id].append(int(to_id))
    
    return waypoint_supplies, waypoint_connections

def parse_goals(pddl_text):
    """Extract goal locations from PDDL"""
    goal_locations = {}
    for match in re.finditer(r'\(at\s+s(\d+)\s+wa(\d+)\)', pddl_text):
        if '(:goal' in pddl_text[:match.start()]:  # Only match goals after :goal
            sled_id = match.group(1)
            waypoint_id = int(match.group(2))
            goal_locations[sled_id] = waypoint_id
    return goal_locations

def convert_pddl_to_json(pddl_text):
    """Convert PDDL problem instance to JSON format"""
    sled_locations, sled_supplies, sled_capacity = parse_sleds(pddl_text)
    waypoint_supplies, waypoint_connections = parse_waypoints(pddl_text)
    goal_locations = parse_goals(pddl_text)
    
    json_data = {
        "sled_locations": sled_locations,
        "sled_supplies": sled_supplies,
        "sled_capacity": sled_capacity,
        "waypoint_supplies": waypoint_supplies,
        "waypoint_connections": waypoint_connections,
        "goal_locations": goal_locations
    }
    
    return json_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', required=True, help='Input directory containing PDDL files')
    parser.add_argument('--output_dir', required=True, help='Output directory for JSON files')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process all PDDL files in input directory
    for filename in os.listdir(args.input_dir):
        if filename.endswith('.pddl'):
            input_path = os.path.join(args.input_dir, filename)
            output_filename = f"problem{filename[5:-5]}.json"  # Generate output filename like "problem1.json"
            output_path = os.path.join(args.output_dir, output_filename)
            
            with open(input_path, 'r') as f:
                pddl_text = f.read()
            
            json_data = convert_pddl_to_json(pddl_text)
            
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=4)
            
            print(f"Converted {filename} to {output_filename}")

if __name__ == '__main__':
    main()