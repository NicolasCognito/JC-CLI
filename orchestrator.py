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
1+ – an error occurred (script crashed or failed directly)
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
        # No graceful message here - crash immediately with descriptive error
        raise RuntimeError(f"Unknown command: {cmd}")
    if not os.path.exists(script):
        # No graceful message here - crash immediately with descriptive error
        raise RuntimeError(f"Script not found: {script}")
    
    print(f"→ {cmd} ► {script} {argv}")
    # Execute directly with check=True to raise CalledProcessError on failure
    # This will provide a traceback with the actual failure reason
    subprocess.run([sys.executable, script, *argv], check=True)
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

    # Let errors propagate naturally - no try/except blocks
    # The "Let It Fail" philosophy means we should see Python's full
    # traceback and error state rather than a clean error message
    _execute_command(cmd, argv)
    
    # Run rule loop without capturing output - let errors show directly
    subprocess.run([sys.executable, RULE_LOOP_PY], check=True)
    sys.exit(0)

if __name__ == "__main__":
    main()