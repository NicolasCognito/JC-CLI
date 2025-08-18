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

    mode = os.environ.get("JC_WORLD_MODE", "file")
    if mode != "memory":
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
    if mode == "memory":
        # Inject shim and in-memory world for child
        env = os.environ.copy()
        env["PLAYER"] = username
        env["JC_WORLD_MODE"] = "memory"
        # Prepend memshim to PYTHONPATH so sitecustomize is importable
        shim_dir = str((pathlib.Path(__file__).parent / "memshim").resolve())
        env["PYTHONPATH"] = shim_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        # Resolve command path and run
        cmd_path = COMMANDS.get(cmd)
        if not cmd_path:
            print(f"ERROR! Unknown command: {cmd}")
            command_success = False
            world_after_cmd = env.get("JC_MEM_WORLD_IN", "{}")
        else:
            cmd_result = subprocess.run([sys.executable, cmd_path, *argv],
                                        env=env, capture_output=True, text=True)
            # Show command output
            if cmd_result.stdout:
                sys.stdout.write(cmd_result.stdout)
            if cmd_result.stderr:
                sys.stderr.write(cmd_result.stderr)
            command_success = (cmd_result.returncode == 0)

            # Extract world after command from marker; fallback to input if absent
            world_after_cmd = env.get("JC_MEM_WORLD_IN", "{}")
            for line in (cmd_result.stdout or "").splitlines()[::-1]:
                if line.startswith("WORLD_OUTPUT:"):
                    world_after_cmd = line.split(":", 1)[1].strip()
                    break

        # Run rule loop with shim as well
        env["JC_MEM_WORLD_IN"] = world_after_cmd
        rule_result = subprocess.run([sys.executable, RULE_LOOP_PY],
                                     env=env, capture_output=True, text=True)
    else:
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
    
    # In memory mode, emit a final world marker for the sequencer
    if mode == "memory":
        final_world = world_after_cmd  # default to post-command world
        for line in (rule_result.stdout or "").splitlines()[::-1]:
            if line.startswith("WORLD_OUTPUT:"):
                final_world = line.split(":", 1)[1].strip()
                break
        print(f"WORLD_FINAL: {final_world}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
