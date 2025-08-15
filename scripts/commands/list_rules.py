NAME = "list"

#!/usr/bin/env python3
"""
List Rules Command
Lists all rules in the rule map and shows which ones are currently active.

Usage: rules
"""
import json
import sys


def main():
    world = json.load(sys.stdin)
    
    # Get the rule map
    rule_map = world.get("rule_map", {})
    
    if not rule_map:
        print("No rules found in the rule map", file=sys.stderr)
        json.dump(world, sys.stdout)
        sys.exit(0)
    
    # Get rules in power (or all rules if not specified)
    rules_in_power = world.get("rules_in_power", list(rule_map.keys()))
    
    print("Rules:", file=sys.stderr)
    print("-" * 40, file=sys.stderr)
    print(f"{'Rule ID':<20} {'Status':<10} {'Script'}", file=sys.stderr)
    print("-" * 40, file=sys.stderr)
    
    for rule_id, script_name in rule_map.items():
        status = "ACTIVE" if rule_id in rules_in_power else "EXCLUDED"
        print(f"{rule_id:<20} {status:<10} {script_name}", file=sys.stderr)

    print("-" * 40, file=sys.stderr)
    json.dump(world, sys.stdout)
    sys.exit(0)

if __name__ == "__main__":
    main()