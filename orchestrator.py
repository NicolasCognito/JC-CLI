#!/usr/bin/env python3
"""
Game-agnostic Orchestrator

• Recursively scans scripts/commands/** for Python files whose first line is
      NAME = "some_command"
  and builds a {command_name: script_path} registry.

• When the player enters a command, the orchestrator looks it up in that
  registry, runs the script in a subprocess, and then invokes rule_loop.py.

Exit codes
----------
0  – command + rule loop succeeded
1+ – an error occurred (details printed to console)
"""
import os, sys, shlex, subprocess, json, re, pathlib

CWD           = pathlib.Path.cwd()
COMMANDS_DIR  = CWD / "scripts" / "commands"
RULE_LOOP_PY  = CWD / "rule_loop.py"
WORLD_FILE    = CWD / "data" / "world.json"
NAME_PATTERN  = re.compile(r'NAME\s*=\s*["\'](.+?)["\']')

def _discover_commands(folder: pathlib.Path = COMMANDS_DIR) -> dict[str, str]:
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

COMMANDS = _discover_commands()

def _ensure_world():
    WORLD_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not WORLD_FILE.exists():
        WORLD_FILE.write_text(json.dumps({"counter": 0}, indent=2))

def _execute_command(cmd: str, argv: list[str]) -> bool:
    script = COMMANDS.get(cmd)
    if not script:
        print(f"Unknown command: {cmd}")
        return False
    if not os.path.exists(script):
        print(f"Script not found: {script}")
        return False
    print(f"→ {cmd} ► {script} {argv}")
    rc = subprocess.run([sys.executable, script, *argv]).returncode
    if rc != 0:
        print(f"Command failed (exit {rc})")
        return False
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <command-text> [username]")
        sys.exit(1)

    _ensure_world()
    raw = sys.argv[1]
    args = shlex.split(raw)
    if not args:
        print("Empty command")
        sys.exit(1)
    cmd, argv = args[0], args[1:]

    if cmd == "exit":
        sys.exit(0)

    if _execute_command(cmd, argv):
        rl = subprocess.run([sys.executable, RULE_LOOP_PY]).returncode
        if rl not in (0, 9):
            print(f"Rule loop failed (exit {rl})")
            sys.exit(1)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()