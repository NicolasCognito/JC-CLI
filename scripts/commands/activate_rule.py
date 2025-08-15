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


def main():
    if len(sys.argv) < 2:
        print("Usage: include <rule_id>", file=sys.stderr)
        sys.exit(1)

    rule_id = sys.argv[1]

    world = json.load(sys.stdin)

    if rule_id in world["rules_in_power"]:
        print(f"Rule '{rule_id}' is already active", file=sys.stderr)
    else:
        world["rules_in_power"].append(rule_id)
        print(f"Rule '{rule_id}' has been activated", file=sys.stderr)

    json.dump(world, sys.stdout)
    sys.exit(0)

if __name__ == "__main__":
    main()