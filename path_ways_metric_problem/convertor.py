import os
import re
import json

def extract_objects(pddl_str):
    simples = []
    complexes = []
    # Locate the objects block between "(:objects" and the next closing parenthesis.
    m = re.search(r"\(:objects(.*?)\)", pddl_str, re.DOTALL)
    if m:
        objects_block = m.group(1).strip()
        # Split the block into lines
        lines = re.split(r"\s*\n\s*", objects_block)
        # Process each line individually.
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Expect lines like: "SP1 - simple" or "Raf1 - simple"
            match = re.match(r"^(\S+)\s*-\s*(simple|complex)$", line)
            if match:
                name = match.group(1)
                typ = match.group(2)
                if typ == "simple":
                    simples.append({
                        "name": name,
                        "chosen": False,
                        "possible": True,
                        "available": 0
                    })
                else:  # complex
                    complexes.append({
                        "name": name,
                        "available": 0
                    })
            else:
                # If a line doesn't match, log it (you may adjust this behavior as needed)
                print("Line didn't match objects pattern:", line)
    else:
        print("No objects block found in PDDL.")
    return simples, complexes



def extract_available(pddl_str, simples, complexes):
    # Match both forms: (available SP1 0) and (= (available SP1) 0)
    re_avail = re.compile(r"\(available\s+([^\s\)]+)\s+(\d+)\)")
    re_eq_avail = re.compile(r"\(=\s+\(available\s+([^\s\)]+)\)\s+(\d+)\)")
    for regex in (re_avail, re_eq_avail):
        for match in regex.finditer(pddl_str):
            name = match.group(1)
            available = int(match.group(2))
            updated = False
            for obj in simples:
                if obj["name"] == name:
                    obj["available"] = available
                    updated = True
                    break
            if not updated:
                for obj in complexes:
                    if obj["name"] == name:
                        obj["available"] = available
                        break

def extract_goal_conditions(pddl_str):
    goal_conditions = []
    # This regex matches a goal like:
    # (>= (+ (available pRbp1p2-AP2) (available pCAF-p300)) 4)
    re_goal = re.compile(
        r"\(>=\s+\(\+\s+\(available\s+([^\s\)]+)\)\s+\(available\s+([^\s\)]+)\)\)\s+(\d+)\)"
    )
    for match in re_goal.finditer(pddl_str):
        mol1 = match.group(1)
        mol2 = match.group(2)
        amount = int(match.group(3))
        goal_conditions.append({
            "molecule_1_name": mol1,
            "molecule_2_name": mol2,
            "amount_condition": amount
        })
    return goal_conditions

def extract_association_reactions(pddl_str):
    reactions = []
    re_assoc = re.compile(r"\(association-reaction\s+([^\s\)]+)\s+([^\s\)]+)\s+([^\s\)]+)\)")
    for match in re_assoc.finditer(pddl_str):
        m1, m2, m3 = match.groups()
        re_need1 = re.compile(rf"\(= \(need-for-association\s+{re.escape(m1)}\s+{re.escape(m2)}\s+{re.escape(m3)}\)\s+(\d+)\)")
        re_need2 = re.compile(rf"\(= \(need-for-association\s+{re.escape(m2)}\s+{re.escape(m1)}\s+{re.escape(m3)}\)\s+(\d+)\)")
        re_prod = re.compile(rf"\(= \(prod-by-association\s+{re.escape(m1)}\s+{re.escape(m2)}\s+{re.escape(m3)}\)\s+(\d+)\)")
        need1 = int(re_need1.search(pddl_str).group(1)) if re_need1.search(pddl_str) else 0
        need2 = int(re_need2.search(pddl_str).group(1)) if re_need2.search(pddl_str) else 0
        prod = int(re_prod.search(pddl_str).group(1)) if re_prod.search(pddl_str) else 0
        reactions.append({
            "molecule_1_name": m1,
            "need_molecule_1": need1,
            "molecule_2_name": m2,
            "need_molecule_2": need2,
            "molecule_3_name": m3,
            "prod": prod
        })
    return reactions

def extract_catalyzed_association_reactions(pddl_str):
    reactions = []
    re_cat_assoc = re.compile(r"\(catalyzed-association-reaction\s+([^\s\)]+)\s+([^\s\)]+)\s+([^\s\)]+)\)")
    for match in re_cat_assoc.finditer(pddl_str):
        m1, m2, m3 = match.groups()
        re_need1 = re.compile(rf"\(= \(need-for-catalyzed-association\s+{re.escape(m1)}\s+{re.escape(m2)}\s+{re.escape(m3)}\)\s+(\d+)\)")
        re_need2 = re.compile(rf"\(= \(need-for-catalyzed-association\s+{re.escape(m2)}\s+{re.escape(m1)}\s+{re.escape(m3)}\)\s+(\d+)\)")
        re_prod = re.compile(rf"\(= \(prod-by-catalyzed-association\s+{re.escape(m1)}\s+{re.escape(m2)}\s+{re.escape(m3)}\)\s+(\d+)\)")
        need1 = int(re_need1.search(pddl_str).group(1)) if re_need1.search(pddl_str) else 0
        need2 = int(re_need2.search(pddl_str).group(1)) if re_need2.search(pddl_str) else 0
        prod = int(re_prod.search(pddl_str).group(1)) if re_prod.search(pddl_str) else 0
        reactions.append({
            "molecule_1_name": m1,
            "need_molecule_1": need1,
            "molecule_2_name": m2,
            "need_molecule_2": need2,
            "molecule_3_name": m3,
            "prod": prod
        })
    return reactions

def extract_catalyzed_self_association_reactions(pddl_str):
    reactions = []
    re_cat_self = re.compile(r"\(catalyzed-self-association-reaction\s+([^\s\)]+)\s+([^\s\)]+)\)")
    for match in re_cat_self.finditer(pddl_str):
        m1, m2 = match.groups()
        re_need = re.compile(rf"\(= \(need-for-catalyzed-self-association\s+{re.escape(m1)}\s+{re.escape(m2)}\)\s+(\d+)\)")
        re_prod = re.compile(rf"\(= \(prod-by-catalyzed-self-association\s+{re.escape(m1)}\s+{re.escape(m2)}\)\s+(\d+)\)")
        need = int(re_need.search(pddl_str).group(1)) if re_need.search(pddl_str) else 0
        prod = int(re_prod.search(pddl_str).group(1)) if re_prod.search(pddl_str) else 0
        reactions.append({
            "molecule_1_name": m1,
            "need_molecule_1": need,
            "molecule_2_name": m2,
            "prod": prod
        })
    return reactions

def extract_synthesis_reactions(pddl_str):
    reactions = []
    re_synth = re.compile(r"\(synthesis-reaction\s+([^\s\)]+)\s+([^\s\)]+)\)")
    for match in re_synth.finditer(pddl_str):
        m1, m2 = match.groups()
        re_need = re.compile(rf"\(= \(need-for-synthesis\s+{re.escape(m1)}\s+{re.escape(m2)}\)\s+(\d+)\)")
        re_prod = re.compile(rf"\(= \(prod-by-synthesis\s+{re.escape(m1)}\s+{re.escape(m2)}\)\s+(\d+)\)")
        need = int(re_need.search(pddl_str).group(1)) if re_need.search(pddl_str) else 0
        prod = int(re_prod.search(pddl_str).group(1)) if re_prod.search(pddl_str) else 0
        reactions.append({
            "molecule_1_name": m1,
            "need_molecule_1": need,
            "molecule_2_name": m2,
            "prod": prod
        })
    return reactions

def convert_pddl_to_json(pddl_str):
    simples, complexes = extract_objects(pddl_str)
    extract_available(pddl_str, simples, complexes)
    goal_conditions = extract_goal_conditions(pddl_str)
    
    association_reactions = extract_association_reactions(pddl_str)
    catalyzed_association_reactions = extract_catalyzed_association_reactions(pddl_str)
    catalyzed_self_association_reactions = extract_catalyzed_self_association_reactions(pddl_str)
    synthesis_reactions = extract_synthesis_reactions(pddl_str)
    
    return {
        "state": {
            "simples": simples,
            "complexes": complexes,
            "num_subs": 0
        },
        "problem": {
            "goal": {
                "conditions": goal_conditions
            },
            "association_reactions": association_reactions,
            "catalyzed_association_reactions": catalyzed_association_reactions,
            "catalyzed_self_association_reactions": catalyzed_self_association_reactions,
            "synthesis_reactions": synthesis_reactions
        }
    }

def process_pddl_files(input_dir, output_dir, max_files=20):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    count = 0
    for filename in os.listdir(input_dir):
        if count >= max_files:
            break
        if filename.endswith(".pddl"):
            input_path = os.path.join(input_dir, filename)
            with open(input_path, 'r') as f:
                pddl_str = f.read()
            json_data = convert_pddl_to_json(pddl_str)
            base, _ = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{base}.json")
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=4)
            print(f"Converted {filename} to {output_path}")
            count += 1

if __name__ == "__main__":
    input_directory = "problems_pddl"   # Adjust to your input directory
    output_directory = "problems_json"  # Adjust to your output directory
    process_pddl_files(input_directory, output_directory)
