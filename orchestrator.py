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
from engine.core import world_state

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

def _execute_command(cmd: str, argv: list[str], username: str, world: dict) -> tuple[dict, bool]:
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

    print(f"-> {cmd} > {script} {argv}")
    proc = subprocess.run(
        [sys.executable, script, *argv],
        input=json.dumps(world),
        env=env,
        capture_output=True,
        text=True,
    )

    if proc.stderr:
        sys.stderr.write(proc.stderr)

    try:
        new_world = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as e:
        print(f"!!! ERROR: Command returned invalid JSON: {e}")
        new_world = world

    return new_world, proc.returncode == 0

def run(command_text: str, username: str) -> bool:
    args = shlex.split(command_text)
    if not args:
        print("Empty command")
        return False
    cmd, argv = args[0], args[1:]
    if cmd == "exit":
        return True

    world = world_state.get_world()
    world, command_success = _execute_command(cmd, argv, username, world)
    world_state.update_world(world)

    rule_proc = subprocess.run(
        [sys.executable, RULE_LOOP_PY],
        input=json.dumps(world_state.get_world()),
        capture_output=True,
        text=True,
    )

    if rule_proc.stderr:
        sys.stderr.write(rule_proc.stderr)

    try:
        new_world = json.loads(rule_proc.stdout or "{}")
    except json.JSONDecodeError as e:
        print(f"!!! ERROR: Rule loop returned invalid JSON: {e}")
        new_world = world_state.get_world()

    world_state.update_world(new_world)

    if not command_success:
        print(f"ERROR! Command '{cmd}' failed")
        return False
    if rule_proc.returncode not in (0, 9):
        print(f"ERROR! Rule loop failed with code {rule_proc.returncode}")
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <command-text> [username]")
        return 1
    raw = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else "unknown_player"
    success = run(raw, username)
    world_state.dump_world(WORLD_FILE)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())