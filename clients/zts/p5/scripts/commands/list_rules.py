#!/usr/bin/env python3
"""
List Rules Command
Lists all rules in the rule map and shows which ones are currently active.

Usage: rules
"""
import json
import sys

def load_world():
    """Load the current world state"""
    with open("data/world.json", "r") as f:
        return json.load(f)

def main():
    # Load the current world state
    world = load_world()
    
    # Get the rule map
    rule_map = world.get("rule_map", {})
    
    if not rule_map:
        print("No rules found in the rule map")
        sys.exit(0)
    
    # Get rules in power (or all rules if not specified)
    rules_in_power = world.get("rules_in_power", list(rule_map.keys()))
    
    print("Rules:")
    print("-" * 40)
    print(f"{'Rule ID':<20} {'Status':<10} {'Script'}")
    print("-" * 40)
    
    for rule_id, script_name in rule_map.items():
        status = "ACTIVE" if rule_id in rules_in_power else "EXCLUDED"
        print(f"{rule_id:<20} {status:<10} {script_name}")
    
    print("-" * 40)
    sys.exit(0)

if __name__ == "__main__":
    main()