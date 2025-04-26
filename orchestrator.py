#!/usr/bin/env python3
"""
Game-agnostic Orchestrator

- Recursively scans scripts/commands/** for Python files whose first line is
      NAME = "some_command"
  and builds a {command_name: script_path} registry.

- When the player enters a command, the orchestrator looks it up in that
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

def _execute_command(cmd: str, argv: list[str], username: str) -> bool:
    script = COMMANDS.get(cmd)
    if not script:
        print(f"ERROR! Unknown command: {cmd}")
        return False
    if not os.path.exists(script):
        print(f"ERROR! Script not found: {script}")
        return False
    
    # Create a copy of the environment and add the player name
    env = os.environ.copy()
    env["PLAYER"] = username
    env["COMMAND"] = cmd
    env["COMMAND_ARGS"] = json.dumps(argv)
    
    #print(f"→ {cmd} ► {script} {argv}")

    print(f"-> {cmd} > {script} {argv}")
    # Run with full output captured and displayed, but don't use check=True
    # so we can still return a boolean success value
    result = subprocess.run([sys.executable, script, *argv], 
                           env=env, capture_output=True, text=True)
    
    # Show both stdout and stderr regardless of success or failure
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    
    # Return success/failure based on exit code
    return result.returncode == 0

def main():
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <command-text> [username]")
        sys.exit(1)

    _ensure_world()
    raw = sys.argv[1]
    
    # Extract username from arguments or use default
    username = sys.argv[2] if len(sys.argv) > 2 else "unknown_player"
    
    args = shlex.split(raw)
    if not args:
        print("Empty command")
        sys.exit(1)
    cmd, argv = args[0], args[1:]

    if cmd == "exit":
        sys.exit(0)

    # Execute the command, capturing the success/failure
    command_success = _execute_command(cmd, argv, username)
    
    # Always run the rule loop, even if the command failed
    rule_result = subprocess.run([sys.executable, RULE_LOOP_PY], 
                               capture_output=True, text=True)
    
    # Show rule loop output
    if rule_result.stdout:
        sys.stdout.write(rule_result.stdout)
    if rule_result.stderr:
        sys.stderr.write(rule_result.stderr)
    
    # Exit with success only if both command and rules succeeded
    # But we've already displayed all error information
    if not command_success:
        print(f"ERROR! Command '{cmd}' failed")
        sys.exit(1)
    elif rule_result.returncode not in (0, 9):
        print(f"ERROR! Rule loop failed with code {rule_result.returncode}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()