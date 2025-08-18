#!/usr/bin/env python3
"""
Game-agnostic Rule Loop

• Recursively scans scripts/rules/** for Python files whose first line is
      NAME = "rule_id"
  and builds {rule_id: script_path}.

• World['rules_in_power'] (optional list) controls which rules actually run;
  if the list is missing, *all* discovered rules are executed.

Exit codes
----------
0  – at least one rule modified the world
9  – no changes
1+ – an error occurred
"""

import json, sys, subprocess, pathlib, re

CWD           = pathlib.Path.cwd()
RULES_DIR     = CWD / "scripts" / "rules"
WORLD_FILE    = CWD / "data" / "world.json"
NAME_PATTERN  = re.compile(r'NAME\s*=\s*["\'](.+?)["\']')

def _discover_rules(folder: pathlib.Path = RULES_DIR) -> dict[str, str]:
    registry: dict[str, str] = {}
    for path in folder.rglob("*.py"):
        try:
            with path.open() as fh:
                for line in fh:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    m = NAME_PATTERN.match(s)
                    if m:
                        registry[m.group(1)] = str(path)
                    break
        except OSError:
            print(f"!!! ERROR: Cannot read rule script at {path}")
    return registry

RULES = _discover_rules()

def _load_world() -> dict:
    try:
        return json.loads(WORLD_FILE.read_text())
    except Exception as e:
        # Show raw error but use empty world to allow continuation
        print(f"!!! ERROR: Failed to load world data: {e}")
        return {}

def _save_world(world: dict):
    try:
        WORLD_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORLD_FILE.write_text(json.dumps(world, indent=2))
    except Exception as e:
        print(f"!!! ERROR: Failed to save world data: {e}")
        # Don't handle the error - let caller see the raw failure

def _run_rule(rid: str, path: str, world: dict) -> tuple[dict, bool]:
    print(f"Running rule: {rid} => {path}")
    try:
        # Pass the world data as input to the rule script
        # Show raw output for maximum transparency
        proc = subprocess.run(
            [sys.executable, path],
            input=json.dumps(world).encode(),
            capture_output=True
        )
        
        # Show any stderr output - errors should be visible
        if proc.stderr:
            sys.stderr.write(proc.stderr.decode('utf-8', errors='replace'))
        
        # Try to parse output, but show raw error if it fails
        try:
            new_world = json.loads(proc.stdout or b"{}")
        except json.JSONDecodeError as e:
            print(f"!!! ERROR: Rule {rid} returned invalid JSON: {e}")
            print(f"Raw output: {proc.stdout[:200]}...")  # First 200 chars of output
            return world, False  # Return original world unchanged
    except Exception as e:
        print(f"!!! ERROR: Rule {rid} failed to execute: {e}")
        return world, False
    
    if proc.returncode == 0:
        return new_world, True
    if proc.returncode == 9:
        return new_world, False
    
    print(f"!!! ERROR: Rule {rid} exited with code {proc.returncode}")
    return new_world, False

def main():
    if not RULES:
        print("!!! WARNING: No rules found.")
        sys.exit(9)  # No changes

    world = _load_world()
    active = world.get("rules_in_power")
    
    # If no rules_in_power specified, run all discovered rules
    if active is None:
        active = list(RULES.keys())
    
    changed = False

    for rid in active:
        path = RULES.get(rid)
        if not path:
            print(f"!!! ERROR: Rule '{rid}' specified in rules_in_power but script not found")
            continue  # Continue with other rules
        
        world, did = _run_rule(rid, path, world)
        changed |= did

    _save_world(world)
    sys.exit(0 if changed else 9)

if __name__ == "__main__":
    main()