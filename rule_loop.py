#!/usr/bin/env python3
"""
Improved Rule loop - Applies rules in order after player commands
Each rule checks its own conditions internally
Now with better exit code handling:
- 0: Rule applied changes
- 1: Rule ran with no changes needed
- 9: Rule determined it wasn't applicable (skipped)
"""
import json
import sys
import subprocess
import os

# Directory where rule scripts are stored
RULE_SCRIPTS_DIR = os.path.join("scripts", "rules")

def load_world():
    """Load the current world state"""
    with open("data/world.json", "r") as f:
        return json.load(f)

def save_world(world):
    """Save the updated world state"""
    with open("data/world.json", "w") as f:
        json.dump(world, f, indent=2)

def execute_rule(rule_id, script_name, world):
    """Execute a single rule script as a subprocess"""
    script_path = os.path.join(RULE_SCRIPTS_DIR, script_name)
    
    # Ensure the script path exists
    if not os.path.exists(script_path):
        print(f"Error: Rule script not found at {script_path}")
        return world, False
    
    # Pass the world as a stringified JSON to avoid file race conditions
    world_json = json.dumps(world)
    
    try:
        # Execute the rule script with the world state as stdin
        result = subprocess.run(
            [sys.executable, script_path],
            input=world_json.encode(),
            capture_output=True,
            check=False  # Don't raise exception on non-zero exit codes
        )
        
        # Parse the updated world from stdout
        updated_world = json.loads(result.stdout.decode())
        
        # Add this rule to the applied rules list
        if "applied_rules" not in updated_world:
            updated_world["applied_rules"] = []
        
        # Check exit code to determine what happened
        if result.returncode == 0:
            # Rule applied changes
            updated_world["applied_rules"].append(rule_id)
            print(f"Rule {rule_id} applied changes")
            return updated_world, True
        elif result.returncode == 9:
            # Rule determined it wasn't applicable
            # Don't log anything - this reduces noise
            return updated_world, False
        else:
            # Rule ran but with errors (exit code 1) or other exit code
            print(f"Rule {rule_id} exited with unexpected code: {result.returncode}")
            return updated_world, False
            
    except subprocess.CalledProcessError as e:
        print(f"Rule {rule_id} failed with code {e.returncode}")
        print(f"Error: {e.stderr.decode()}")
        return world, False
    except json.JSONDecodeError as e:
        print(f"Rule {rule_id} returned invalid JSON: {e}")
        print(f"Output: {result.stdout.decode()}")
        return world, False

def main():
    """Main rule loop execution"""
    changes_made = False
    
    # Load the current world state
    world = load_world()
    
    # Reset applied rules list at the start of each rule loop cycle
    world["applied_rules"] = []
    
    # Get rule map from world
    rule_map = world.get("rule_map", {})
    
    # Execute all rules in the rule map
    for rule_id, script_name in rule_map.items():
        updated_world, rule_changed = execute_rule(rule_id, script_name, world)
        
        # Update our world state with the rule's changes
        world = updated_world
        
        # Track if any rule made changes
        if rule_changed:
            changes_made = True
    
    # Save the final world state back to disk
    save_world(world)
    
    if changes_made:
        print("Rule loop completed. Changes were made.")
        return 0
    else:
        print("Rule loop completed. No changes needed.")
        return 9

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)