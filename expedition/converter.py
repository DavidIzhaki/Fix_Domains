#!/usr/bin/env python3
import re
import json
import os
import argparse

def parse_sleds(pddl_text):
    """Extract sled properties including hardcoded starting location and initial supplies."""
    sleds = {}
    # Initialize sleds with default values for location and supplies
    capacity_matches = re.finditer(r'\(=\s*\(sled_capacity\s+(s\d+)\)\s*(\d+)\)', pddl_text)
    supplies_matches = re.finditer(r'\(=\s*\(sled_supplies\s+(s\d+)\)\s*(\d+)\)', pddl_text)

    for match in capacity_matches:
        sled_id, _ = match.groups()
        sleds[sled_id] = {
            'location': "waypoint0",  # Hardcode starting location
            'supplies': 0  # Default supplies in case it's not specified
        }

    for match in supplies_matches:
        sled_id, supplies = match.groups()
        if sled_id in sleds:
            sleds[sled_id]['supplies'] = int(supplies)

    return sleds

def parse_capacities(pddl_text):
    """Extract sled capacity separately."""
    capacities = {}
    capacity_matches = re.finditer(r'\(=\s*\(sled_capacity\s+(s\d+)\)\s*(\d+)\)', pddl_text)
    for match in capacity_matches:
        sled_id, capacity = match.groups()
        capacities[sled_id] = int(capacity)
    return capacities

def parse_waypoints(pddl_text):
    """Extract waypoint supplies and connections."""
    waypoints = {}
    supplies_matches = re.finditer(r'\(=\s*\(waypoint_supplies\s+(wa\d+)\)\s*(\d+)\)', pddl_text)
    connections_matches = re.finditer(r'\(is_next\s+(wa\d+)\s+(wa\d+)\)', pddl_text)

    for match in supplies_matches:
        waypoint_id, supplies = match.groups()
        waypoints["waypoint" + waypoint_id[2:]] = int(supplies)

    connections = {}
    for match in connections_matches:
        from_wp, to_wp = match.groups()
        if from_wp not in connections:
            connections["waypoint" + from_wp[2:]] = []
        connections["waypoint" + from_wp[2:]].append("waypoint" + to_wp[2:])

    return waypoints, connections

def parse_goals(pddl_text):
    """Extract goal conditions."""
    goal_locations = {}
    goal_location_matches = re.finditer(r'\(at\s+(s\d+)\s+(wa\d+)\)', pddl_text)

    for match in goal_location_matches:
        sled_id, location = match.groups()
        goal_locations[sled_id] = "waypoint" + location[2:]

    return goal_locations

def convert_pddl_to_json(pddl_text):
    """Convert expedition PDDL problem instance to JSON format"""
    sleds = parse_sleds(pddl_text)
    capacities = parse_capacities(pddl_text)
    waypoints, connections = parse_waypoints(pddl_text)
    goal_locations = parse_goals(pddl_text)

    json_data = {
        "state": {
            "sleds": sleds,
            "waypoint_supplies": waypoints
        },
        "problem": {
            "goal_locations": goal_locations,
            "waypoint_connections": connections,
            "sled_capacity": capacities
        }
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
            output_filename = f"{filename[:-5]}.json"
            output_path = os.path.join(args.output_dir, output_filename)

            with open(input_path, 'r') as f:
                pddl_text = f.read()

            json_data = convert_pddl_to_json(pddl_text)

            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=4)

            print(f"Converted {filename} to {output_filename}")

if __name__ == '__main__':
    main()
