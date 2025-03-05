#!/usr/bin/env python3
import re
import json
import os
import argparse
from collections import defaultdict

def parse_pddl(pddl_text):
    """Extract information from PDDL with diagnostic output."""
    bots = []
    items = []
    room_connections = defaultdict(list)
    goal_locations = {}
    cost = 0

    room_mapping = {}
    room_counter = 0

    def get_room_id(room_name):
        nonlocal room_counter
        if room_name not in room_mapping:
            room_mapping[room_name] = room_counter
            room_counter += 1
        return room_mapping[room_name]

    # Extract initial state
    init_section = re.search(r'\(:init(.*?)\(:goal', pddl_text, re.DOTALL)
    if init_section:
        init_text = init_section.group(1)
        
        # Extract bot locations, load limits, and current loads
        for match in re.finditer(r'\(at-bot (bot\d+) (room\w+)\)', init_text):
            bot_id = int(match.group(1)[3:])
            room_id = get_room_id(match.group(2))
            bots.append({
                "location": room_id,
                "load_limit": 4,
                "current_load": 0,
                "index": bot_id - 1,
                "arms": [{"is_free": True, "side": 0}, {"is_free": True, "side": 1}]
            })
        
        # Extract item locations and weights
        for match in re.finditer(r'\(at (item\d+) (room\w+)\)', init_text):
            item_id = int(match.group(1)[4:])
            room_id = get_room_id(match.group(2))
            items.append({
                "location": room_id,
                "weight": 1,
                "in_arm": -1,
                "in_tray": -1,
                "index": item_id - 1
            })
        
        items.sort(key=lambda x: x["index"])

        # Extract room connections
        for match in re.finditer(r'\(door (room\w+) (room\w+)\)', init_text):
            room_from = get_room_id(match.group(1))
            room_to = get_room_id(match.group(2))
            room_connections[room_from].append(room_to)
            room_connections[room_to].append(room_from)


        # Extract goal state
        goal_section = re.search(r'\(:goal\s*\(and(.*?)\)\)', pddl_text, re.DOTALL)
        if goal_section:
            goal_text = goal_section.group(1)
            for match in re.finditer(r'\(at (item\d+) (room\w+)', goal_text):
                item_id = int(match.group(1)[4:])  # item indices start from 1 in your PDDL
                room_name = match.group(2)
                room_id = get_room_id(room_name)
                goal_locations[item_id - 1] = room_id  # Adjust index to start from 0

    return {
        "bots": bots,
        "items": items,
        "room_connections": dict(room_connections),
        "cost": cost,
        "goal_locations": goal_locations
    }


def convert_pddl_to_json(pddl_text):
    """Convert PDDL problem instance to JSON format"""
    return parse_pddl(pddl_text)

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