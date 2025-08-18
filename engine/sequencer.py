#!/usr/bin/env python3
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

"""
Event-based Sequencer – append-only log + cursor
Processes commands in strict sequence, exactly once.
"""

import os, sys, json, time, argparse, shlex, subprocess, threading, socket, re, pathlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import config

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
        # Optional in-memory pipeline (opt-in via JC_WORLD_MODE=memory or config)
        self.world_mode = os.environ.get("JC_WORLD_MODE", getattr(config, "WORLD_MODE", "file"))
        self.memory_world = None
        if self.world_mode == "memory":
            self.memory_world = self._read_world()
            # Start lightweight world server for view fetch (no disk I/O)
            self._mem_host = os.environ.get("JC_MEM_VIEW_HOST", "127.0.0.1")
            try:
                self._mem_port = int(os.environ.get("JC_MEM_VIEW_PORT", "0"))
            except Exception:
                self._mem_port = 0
            if self._mem_port:
                threading.Thread(target=self._world_server, daemon=True).start()
            # Preload command and rule sources into memory
            self._cmd_sources = self._discover_command_sources()
            self._rule_sources = self._discover_rule_sources()
            self._cmd_worker = None
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
        if self.world_mode == "memory":
            # Ensure worker
            if self._cmd_worker is None or self._cmd_worker.poll() is not None:
                self._cmd_worker = subprocess.Popen(
                    [sys.executable, os.path.join(os.path.dirname(__file__), "command_worker.py")],
                    cwd=self.client_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                )
            # Send job
            job = {
                "type": "run",
                "cmd": cmd_name,
                "argv": cmd_args,
                "world": self.memory_world or {},
                "source": self._cmd_sources.get(cmd_name, ""),
                "username": user,
            }
            try:
                assert self._cmd_worker.stdin is not None
                self._cmd_worker.stdin.write(json.dumps(job) + "\n")
                self._cmd_worker.stdin.flush()
                assert self._cmd_worker.stdout is not None
                resp_line = self._cmd_worker.stdout.readline()
                resp = json.loads(resp_line or "{}")
            except Exception as e:
                print(f"[Worker] communication error: {e}")
                resp = {"ok": False, "stdout": "", "stderr": str(e), "exit": 1, "world": self.memory_world or {}}

            # Show command outputs
            if resp.get("stdout"):
                print(resp.get("stdout"))
            if resp.get("stderr"):
                print(resp.get("stderr"))

            # Run rules via persistent worker
            if not hasattr(self, "_rule_worker") or self._rule_worker is None or self._rule_worker.poll() is not None:
                self._rule_worker = subprocess.Popen(
                    [sys.executable, os.path.join(os.path.dirname(__file__), "rule_worker.py")],
                    cwd=self.client_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                )
            rule_job = {
                "type": "run",
                "world": resp.get("world") or {},
                "sources": self._rule_sources,
                # Let worker decide active if not specified
                "active": (resp.get("world") or {}).get("rules_in_power"),
            }
            try:
                assert self._rule_worker.stdin is not None
                self._rule_worker.stdin.write(json.dumps(rule_job) + "\n")
                self._rule_worker.stdin.flush()
                assert self._rule_worker.stdout is not None
                rule_resp_line = self._rule_worker.stdout.readline()
                rule_resp = json.loads(rule_resp_line or "{}")
            except Exception as e:
                print(f"[RuleWorker] communication error: {e}")
                rule_resp = {"ok": False, "exit": 1, "world": resp.get("world") or {}, "stdout": "", "stderr": str(e)}

            if rule_resp.get("stdout"):
                print(rule_resp.get("stdout"))
            if rule_resp.get("stderr"):
                print(rule_resp.get("stderr"))
            self.memory_world = rule_resp.get("world") or (resp.get("world") or {})
            # fake a result object for uniform logging below
            class _R: pass
            result = _R()
            result.returncode = 0 if resp.get("ok") and rule_resp.get("exit") in (0, 9) else 1
            result.stdout = ""
            result.stderr = ""
        else:
            env = os.environ.copy()
            result = subprocess.run(
                [sys.executable, self.orchestrator, text, user],
                cwd=self.client_dir,
                capture_output=True,
                text=True,
                env=env,
            )
        
        # Show raw output, not sanitized error messages
        if hasattr(result, "stdout") and result.stdout:
            print(result.stdout)
        if hasattr(result, "stderr") and result.stderr:
            print(result.stderr)
            
        if result.returncode != 0:
            print(f"!!! COMMAND FAILED: '{cmd_name}' (code {result.returncode})")
        # In memory mode, world has been updated above from worker responses
        
        # Note: We don't return anything because sequencer will continue regardless

    # ------------------------------------------------------------------ #

    def _world_path(self) -> str:
        return os.path.join(self.data_dir, config.WORLD_FILE)

    def _read_world(self) -> dict:
        try:
            with open(self._world_path(), "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return {}
        except Exception:
            return {}

    def _write_world(self, world: dict) -> None:
        path = self._world_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(world, fh, indent=2)

    # --------- script discovery/helpers (memory mode) ---------
    def _discover_command_sources(self) -> dict:
        base = pathlib.Path(self.client_dir) / "scripts" / "commands"
        name_pat = re.compile(r'^\s*NAME\s*=\s*["\'](.+?)["\']')
        reg: dict[str, str] = {}
        try:
            for path in base.rglob("*.py"):
                try:
                    text = path.read_text(encoding="utf-8")
                    first_non_comment = None
                    for line in text.splitlines():
                        s = line.strip()
                        if not s or s.startswith('#'):
                            continue
                        first_non_comment = s
                        break
                    if not first_non_comment:
                        continue
                    m = name_pat.match(first_non_comment)
                    if m:
                        reg[m.group(1)] = text
                except Exception:
                    continue
        except Exception:
            pass
        return reg

    def _discover_rule_sources(self) -> dict:
        base = pathlib.Path(self.client_dir) / "scripts" / "rules"
        name_pat = re.compile(r'^\s*NAME\s*=\s*["\'](.+?)["\']')
        reg: dict[str, str] = {}
        try:
            for path in base.rglob("*.py"):
                try:
                    text = path.read_text(encoding="utf-8")
                    first_non_comment = None
                    for line in text.splitlines():
                        s = line.strip()
                        if not s or s.startswith('#'):
                            continue
                        first_non_comment = s
                        break
                    if not first_non_comment:
                        continue
                    m = name_pat.match(first_non_comment)
                    if m:
                        reg[m.group(1)] = text
                except Exception:
                    continue
        except Exception:
            pass
        return reg

    def _world_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self._mem_host, self._mem_port))
                s.listen(5)
                while True:
                    conn, _ = s.accept()
                    with conn:
                        try:
                            # read and ignore request; respond with JSON
                            conn.recv(1024)
                        except Exception:
                            pass
                        try:
                            payload = json.dumps(self.memory_world or {})
                        except Exception:
                            payload = "{}"
                        try:
                            conn.sendall(payload.encode("utf-8"))
                        except Exception:
                            pass
        except Exception as e:
            print(f"[Memory] World server error: {e}")

# ---------------------------------------------------------------------------#

def main():
    parser = argparse.ArgumentParser(description="JC-CLI Sequencer (append-only)")
    parser.add_argument("--dir", help="Client directory to use", default=None)
    args = parser.parse_args()

    Sequencer(client_dir=args.dir).start()

if __name__ == "__main__":
    main()
