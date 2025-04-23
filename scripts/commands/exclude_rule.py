NAME = "exclude"

#!/usr/bin/env python3
"""
Exclude Rule Command
Excludes a rule from being applied in the rule loop by removing it from the
rules_in_power list.

Usage: exclude <rule_id>
"""
import json
import sys

def load_world():
    """Load the current world state"""
    with open("data/world.json", "r") as f:
        return json.load(f)

def save_world(world):
    """Save the updated world state"""
    with open("data/world.json", "w") as f:
        json.dump(world, f, indent=2)

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: exclude <rule_id>")
        sys.exit(1)
    
    rule_id = sys.argv[1]
    
    # Load the current world state
    world = load_world()
    
    # Get the rule map
    rule_map = world.get("rule_map", {})
    
    # Check if the rule exists
    if rule_id not in rule_map:
        print(f"Error: Rule '{rule_id}' not found in rule map")
        sys.exit(1)
    
    # Initialize rules_in_power if it doesn't exist
    if "rules_in_power" not in world:
        world["rules_in_power"] = list(rule_map.keys())
    
    # Check if the rule is already excluded
    if rule_id not in world["rules_in_power"]:
        print(f"Rule '{rule_id}' is already excluded")
        sys.exit(0)
    
    # Remove the rule from rules_in_power
    world["rules_in_power"].remove(rule_id)
    
    # Save the updated world state
    save_world(world)
    
    print(f"Rule '{rule_id}' has been excluded")
    sys.exit(0)

if __name__ == "__main__":
    main()