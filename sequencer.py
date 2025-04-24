#!/usr/bin/env python3
"""
Event-based Sequencer – append-only log + cursor
Processes commands in strict sequence, exactly once.
"""

import os, sys, json, time, argparse, shlex, subprocess, threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from . import config

# ---------------------------------------------------------------------------#
# Helper: read/write cursor                                                  #
# ---------------------------------------------------------------------------#

def _read_cursor(path: str) -> int:
    try:
        with open(path, "r") as fh:
            return int(fh.read().strip() or 0)
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0

def _write_cursor(path: str, seq: int) -> None:
    with open(path, "w") as fh:
        fh.write(str(seq))

# ---------------------------------------------------------------------------#
# Watchdog handler                                                           #
# ---------------------------------------------------------------------------#

class _LogEventHandler(FileSystemEventHandler):
    def __init__(self, sequencer):
        self.sequencer = sequencer
    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.sequencer.log_file:
            threading.Thread(target=self.sequencer.process_new).start()

# ---------------------------------------------------------------------------#
# Sequencer                                                                  #
# ---------------------------------------------------------------------------#

class Sequencer:
    def __init__(self, client_dir: str | None = None):
        self.client_dir = client_dir or os.getcwd()
        self.data_dir   = os.path.join(self.client_dir, "data")
        self.log_file   = os.path.join(self.data_dir, config.COMMANDS_LOG_FILE)
        self.cursor_file= os.path.join(self.data_dir, config.CURSOR_FILE)
        self.orchestrator = os.path.join(os.path.dirname(__file__), "orchestrator.py")

        for p in (self.data_dir,):
            os.makedirs(p, exist_ok=True)
        open(self.log_file, "a").close()   # ensure exists

        self.cursor = _read_cursor(self.cursor_file)
        self.lock   = threading.Lock()

        self.observer = Observer()
        self.observer.schedule(_LogEventHandler(self), self.data_dir, recursive=False)

        print(f"Sequencer ready – watching {self.log_file}")

    # ------------------------------------------------------------------ #

    def start(self):
        self.process_new()   # catch up first
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("Stopping sequencer.")
        self.observer.stop()
        self.observer.join()

    # ------------------------------------------------------------------ #

    def process_new(self):
        if not self.lock.acquire(blocking=False):
            return
        try:
            next_seq = self.cursor + 1
            with open(self.log_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        cmd = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"!!! ERROR: Invalid JSON in command log: {line}")
                        # Continue processing, don't block on invalid JSON
                        continue
                        
                    # skip already-handled
                    if cmd.get("seq") != next_seq:
                        continue

                    # Execute command and ALWAYS advance cursor, even on failure
                    self._execute(cmd)
                    self.cursor = next_seq
                    _write_cursor(self.cursor_file, self.cursor)
                    next_seq += 1
        finally:
            self.lock.release()

    # ------------------------------------------------------------------ #

    def _execute(self, cmd):
        seq = cmd["seq"]
        text = cmd["command"]["text"]
        user = cmd["command"]["username"]

        parts = shlex.split(text)
        cmd_name, cmd_args = (parts[0], parts[1:]) if parts else ("", [])

        print(f"[Command:{seq}] Processing '{cmd_name}' from {user}")
        if cmd_args:
            print(f"[Command:{seq}] Args: {cmd_args}")

        # Execute without check=True, since we want to continue even if command fails
        # Capture output to show it in raw form
        result = subprocess.run(
            [sys.executable, self.orchestrator, text, user],
            cwd=self.client_dir,
            capture_output=True,
            text=True
        )
        
        # Show raw output, not sanitized error messages
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        if result.returncode != 0:
            print(f"!!! COMMAND FAILED: '{cmd_name}' (code {result.returncode})")
        
        # Note: We don't return anything because sequencer will continue regardless

# ---------------------------------------------------------------------------#

def main():
    parser = argparse.ArgumentParser(description="JC-CLI Sequencer (append-only)")
    parser.add_argument("--dir", help="Client directory to use", default=None)
    args = parser.parse_args()

    Sequencer(client_dir=args.dir).start()

if __name__ == "__main__":
    main()