#!/usr/bin/env python3
import re
import json
import os
import argparse

def parse_bounds(pddl_text):
    """Extract the x, y, z bounds from the PDDL text"""
    bounds = {}
    patterns = {
        'min_x': r'\(=\s*\(min_x\)\s*(\d+)\)',
        'max_x': r'\(=\s*\(max_x\)\s*(\d+)\)',
        'min_y': r'\(=\s*\(min_y\)\s*(\d+)\)',
        'max_y': r'\(=\s*\(max_y\)\s*(\d+)\)',
        'min_z': r'\(=\s*\(min_z\)\s*(\d+)\)',
        'max_z': r'\(=\s*\(max_z\)\s*(\d+)\)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, pddl_text)
        if match:
            bounds[key] = int(match.group(1))
    
    return bounds

def parse_battery(pddl_text):
    """Extract battery information from the PDDL text"""
    level_match = re.search(r'\(=\s*\(battery-level\)\s*(\d+)\)', pddl_text)
    capacity_match = re.search(r'\(=\s*\(battery-level-full\)\s*(\d+)\)', pddl_text)
    
    return {
        'battery_level': int(level_match.group(1)) if level_match else 0,
        'battery_capacity': int(capacity_match.group(1)) if capacity_match else 0
    }

def parse_locations(pddl_text):
    """Extract locations and their coordinates from the PDDL text"""
    locations = {}
    location_pattern = r'\(=\s*\(xl\s+(x\d+y\d+z\d+)\)\s*(\d+)\).*?' + \
                      r'\(=\s*\(yl\s+\1\)\s*(\d+)\).*?' + \
                      r'\(=\s*\(zl\s+\1\)\s*(\d+)\)'
    
    matches = re.finditer(location_pattern, pddl_text, re.DOTALL)
    
    for idx, match in enumerate(matches):
        loc_name, x, y, z = match.groups()
        locations[str(idx)] = [int(x), int(y), int(z)]
    
    return locations

def convert_pddl_to_json(pddl_text):
    """Convert PDDL problem instance to JSON format"""
    bounds = parse_bounds(pddl_text)
    battery_info = parse_battery(pddl_text)
    locations = parse_locations(pddl_text)
    visited = {str(i): False for i in range(len(locations))}
    
    json_data = {
        **battery_info,
        **bounds,
        'locations': locations,
        'visited': visited
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