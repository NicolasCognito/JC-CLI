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
            pass
    return registry

RULES = _discover_rules()

def _load_world() -> dict:
    return json.loads(WORLD_FILE.read_text())

def _save_world(world: dict):
    WORLD_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORLD_FILE.write_text(json.dumps(world, indent=2))

def _run_rule(rid: str, path: str, world: dict) -> tuple[dict, bool]:
    try:
        proc = subprocess.run(
            [sys.executable, path],
            input=json.dumps(world).encode(),
            capture_output=True
        )
        new_world = json.loads(proc.stdout or b"{}")
    except Exception as e:
        print(f"Rule {rid} error: {e}")
        return world, False

    if proc.returncode == 0:
        return new_world, True
    if proc.returncode == 9:
        return new_world, False

    print(f"Rule {rid} exited with {proc.returncode}")
    return new_world, False

def main():
    if not RULES:
        print("No rules found.")
        sys.exit(9)

    world  = _load_world()
    active = world.get("rules_in_power") or list(RULES.keys())
    changed = False

    for rid in active:
        path = RULES.get(rid)
        if not path:
            print(f"Skipping missing rule: {rid}")
            continue
        world, did = _run_rule(rid, path, world)
        changed |= did

    _save_world(world)
    sys.exit(0 if changed else 9)

if __name__ == "__main__":
    main()
