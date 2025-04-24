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
1+ – an error occurred (raw error from script execution)
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
            raise RuntimeError(f"Failed to read rule script at {path}")
    return registry

RULES = _discover_rules()

def _load_world() -> dict:
    try:
        return json.loads(WORLD_FILE.read_text())
    except Exception as e:
        # Let it fail: Don't catch and handle here
        raise RuntimeError(f"Failed to load world data: {e}")

def _save_world(world: dict):
    try:
        WORLD_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORLD_FILE.write_text(json.dumps(world, indent=2))
    except Exception as e:
        # Let it fail: Don't catch and handle here
        raise RuntimeError(f"Failed to save world data: {e}")

def _run_rule(rid: str, path: str, world: dict) -> tuple[dict, bool]:
    # Pass the world data as input to the rule script
    # Allow exceptions to propagate up - don't catch them
    proc = subprocess.run(
        [sys.executable, path],
        input=json.dumps(world).encode(),
        capture_output=True,
        check=True  # Will raise an exception on non-zero exit codes
    )
    
    # Parse the output - any JSON errors will raise exceptions naturally
    new_world = json.loads(proc.stdout)
    
    if proc.returncode == 0:
        return new_world, True
    if proc.returncode == 9:
        return new_world, False
    
    # Any other return code should not be reached due to check=True above
    # Let the subprocess.CalledProcessError propagate

def main():
    if not RULES:
        # Don't just exit quietly - make it clear there are no rules
        raise RuntimeError("No rules found. Check the RULES_DIR path.")

    world = _load_world()
    active = world.get("rules_in_power")
    
    # If no rules_in_power specified, use all discovered rules
    if active is None:
        active = list(RULES.keys())
    
    changed = False

    for rid in active:
        path = RULES.get(rid)
        if not path:
            # Don't silently skip - make it clear the rule is missing
            raise RuntimeError(f"Rule '{rid}' specified in rules_in_power but script not found")
        
        world, did = _run_rule(rid, path, world)
        changed |= did

    _save_world(world)
    sys.exit(0 if changed else 9)

if __name__ == "__main__":
    main()