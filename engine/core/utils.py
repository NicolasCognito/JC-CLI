# engine/core/utils.py
"""Utility functions for file operations and process management"""

import os
import shlex
import sys
import platform
import subprocess
import shutil
import json
import config  # Use relative import within the package

def setup_directories():
    """Ensure required base directories exist and create default template"""
    os.makedirs(config.SESSIONS_DIR, exist_ok=True)
    os.makedirs(config.TEMPLATES_DIR, exist_ok=True)

    # Create default template if it doesn't exist
    default_template_dir = os.path.join(config.TEMPLATES_DIR, config.DEFAULT_TEMPLATE)
    default_template_initial_world_file = os.path.join(default_template_dir, config.INITIAL_WORLD_FILE)

    os.makedirs(default_template_dir, exist_ok=True)

    if not os.path.exists(default_template_initial_world_file):
        # Create a simple default template world
        with open(default_template_initial_world_file, 'w') as f:
            json.dump({
                "counter": 0,
                "rule_map": {
                    "trim_counter": "counter_threshold.py"
                }
            }, f, indent=2)
        print(f"Created default template at {default_template_initial_world_file}")

def copy_directory(src, dst):
    """Copy a directory recursively"""
    if not os.path.exists(src):
        print(f"Warning: Source directory {src} not found")
        return False
    try:
        os.makedirs(dst, exist_ok=True)
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)
            if os.path.isdir(src_item):
                copy_directory(src_item, dst_item)
            else:
                shutil.copy2(src_item, dst_item)
        return True
    except Exception as e:
        print(f"Error copying directory: {e}")
        return False

def launch_in_new_terminal(cmd, title: str | None = None) -> bool:
    """
    Launch `cmd` in a fresh terminal window.
    - On Windows + WezTerm → wezterm start … powershell -NoExit …
    - On plain Windows     → start powershell -NoExit …
    - Anything else        → prints a hint and returns False.
    `cmd` may be a str or a sequence of args.
    """
    system = platform.system()
    cwd = os.getcwd()

    # Normalise `cmd` to a single string for the shell we’ll run inside
    if isinstance(cmd, (list, tuple)):
        # list2cmdline gives Windows-safe quoting
        cmd_str = subprocess.list2cmdline(cmd)
    else:
        cmd_str = cmd

    try:
        if system == "Windows":
            if shutil.which("wezterm") and config.USE_WIZTERM == True:
                # ── WezTerm branch ───────────────────────────────────────────────
                # Build the inner PowerShell command
                inner_parts = [f"cd '{cwd}';"]
                if title:
                    # Change the console title inside the WezTerm tab
                    inner_parts.append(f"$Host.UI.RawUI.WindowTitle='{title}';")
                inner_parts.append(cmd_str)
                inner_cmd = " ".join(inner_parts)

                wez_args = [
                    "wezterm", "start",
                    "--cwd", cwd,          # sets starting directory for the tab
                    "--",                  # everything after this is the program to run
                    "powershell", "-NoExit", "-Command", inner_cmd
                ]
                subprocess.Popen(wez_args)

            else:
                # ── Fallback branch (cmd’s `start`) ─────────────────────────────
                # Windows built-ins like `start` require shell=True
                if title:
                    start_line = (
                        f'start "{title}" powershell -NoExit '
                        f'-Command "cd \'{cwd}\'; {cmd_str}"'
                    )
                else:
                    start_line = (
                        f'start powershell -NoExit '
                        f'-Command "cd \'{cwd}\'; {cmd_str}"'
                    )
                subprocess.Popen(start_line, shell=True)
        else:
            print(f"Unsupported OS: {system}")
            print(f"Run manually in {cwd!r}: {cmd_str}")
            return False

        return True

    except Exception as exc:
        print(f"Error launching terminal: {exc}")
        print(f"Run manually in {cwd!r}: {cmd_str}")
        return False
# ──────────────────────────────────────────────────────────────────────────────

def clear_client_state(commands_path: str, cursor_path: str, scripts_dir: str) -> None:
    """
    Clear the client’s command log, reset the cursor file to zero,
    and wipe & recreate the scripts directory.
    """
    # Clear commands log file
    open(commands_path, "w").close()
    print("Command log file reset")

    # Reset cursor file to 0
    with open(cursor_path, "w") as f:
        f.write("0")
    print("Cursor sequence reset to 0")

    # Clear scripts directory if it exists
    if os.path.exists(scripts_dir):
        print(f"Clearing scripts directory: {scripts_dir}")
        shutil.rmtree(scripts_dir)
    os.makedirs(scripts_dir, exist_ok=True)