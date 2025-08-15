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


def main():
    if len(sys.argv) < 2:
        print("Usage: exclude <rule_id>", file=sys.stderr)
        sys.exit(1)

    rule_id = sys.argv[1]
    world = json.load(sys.stdin)

    if rule_id not in world["rules_in_power"]:
        print(f"Rule '{rule_id}' is already excluded", file=sys.stderr)
    else:
        world["rules_in_power"].remove(rule_id)
        print(f"Rule '{rule_id}' has been excluded", file=sys.stderr)

    json.dump(world, sys.stdout)
    sys.exit(0)

if __name__ == "__main__":
    main()