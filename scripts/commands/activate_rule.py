NAME = "include"

#!/usr/bin/env python3
"""
Activate Rule Command
Activates a rule by adding it to the rules_in_power list so it will be
applied in the rule loop.

Usage: activate <rule_id>
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
        print("Usage: activate <rule_id>")
        sys.exit(1)
    
    rule_id = sys.argv[1]
    
    # Load the current world state
    world = load_world()
    
    # Check if the rule is already active
    if rule_id in world["rules_in_power"]:
        print(f"Rule '{rule_id}' is already active")
        sys.exit(0)
    
    # Add the rule to rules_in_power
    world["rules_in_power"].append(rule_id)
    
    # Save the updated world state
    save_world(world)
    
    print(f"Rule '{rule_id}' has been activated")
    sys.exit(0)

if __name__ == "__main__":
    main()