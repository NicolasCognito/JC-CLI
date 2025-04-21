# engine/core/utils.py
"""Utility functions for file operations and process management"""

import os
import sys
import platform
import subprocess
import shutil
import json
from . import config # Use relative import within the package

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
            # Original template content
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
        # Create destination if it doesn't exist
        os.makedirs(dst, exist_ok=True)

        # Copy contents
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)

            if os.path.isdir(src_item):
                # Recursive copy for directories
                copy_directory(src_item, dst_item)
            else:
                # Copy files
                shutil.copy2(src_item, dst_item)

        return True
    except Exception as e:
        print(f"Error copying directory: {e}")
        return False

def launch_in_new_terminal(cmd, title=None):
    """Launch a command in a new terminal window based on OS"""
    system = platform.system()
    cwd = os.getcwd() # Get current working directory to ensure scripts run from the correct context

    try:
        if system == "Windows":
            # Fixed Windows title handling
            if title:
                # Using the Start command directly which handles titles properly
                subprocess.Popen(
                    f'start "{title}" powershell -NoExit -Command "cd \'{cwd}\'; {cmd}"',
                    shell=True
                )
            else:
                # No title specified
                subprocess.Popen(
                    f'start powershell -NoExit -Command "cd \'{cwd}\'; {cmd}"',
                    shell=True
                )

        elif system == "Darwin":  # macOS
            # Original AppleScript approach
            apple_cmd = f'cd \\"{cwd}\\"; {cmd}' # Command needs escaping for AppleScript string
            window_title_arg = f' with title "{title}"' if title else ""
            osa_script = f'tell app "Terminal" to do script "{apple_cmd}"{window_title_arg}'
            subprocess.Popen(["osascript", "-e", osa_script])

        elif system == "Linux":
            # Try common terminals, adapting original logic
            try:
                # gnome-terminal
                term_cmd = ["gnome-terminal"]
                if title: term_cmd.extend([f"--title={title}"])
                term_cmd.extend(["--", "bash", "-c", f'cd "{cwd}" && {cmd}; exec bash'])
                subprocess.Popen(term_cmd)
            except FileNotFoundError:
                try:
                    # xterm fallback
                    term_cmd = ["xterm"]
                    if title: term_cmd.extend(["-T", title])
                    term_cmd.extend(["-e", f'bash -c \'cd "{cwd}" && {cmd}; exec bash\'']) # Ensure inner command is quoted for -e
                    subprocess.Popen(term_cmd)
                except FileNotFoundError:
                     print(f"Could not find gnome-terminal or xterm. Please run manually.")
                     print(f"Command: cd \"{cwd}\" && {cmd}")
                     return False
        else:
            print(f"Unsupported OS: {system}")
            print(f"Please run this command manually in directory '{cwd}': {cmd}")
            return False

        return True

    except Exception as e:
        print(f"Error launching terminal: {e}")
        print(f"Please run this command manually in directory '{cwd}': {cmd}")
        return False