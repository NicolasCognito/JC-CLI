# --- view.py (View Manager) ---
#!/usr/bin/env python3
"""
JC-CLI View Manager (refactored)

Launches and coordinates game‑specific view modules.  Two modes:
  • fast   – redraw on every write to world.json (legacy)
  • commit – redraw only after cursor.seq is bumped (command + rules finished)

The view script is discovered by NAME metadata inside scripts/views/*.py.
A running manager can switch views with the local command:
    view <view_id>

Game commands are queued for thin_client via --cmd-queue file.
"""
import argparse, importlib.util, json, os, sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Engine configuration
from . import config

# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

def _discover_views(folder: Path):
    registry: dict[str, Path] = {}
    for path in folder.rglob("*.py"):
        try:
            with path.open() as fh:
                for line in fh:
                    s = line.strip()
                    if s.startswith("NAME"):
                        name = s.split("=", 1)[1].strip().strip("\"'")
                        registry[name] = path
                        break
        except OSError:
            pass
    return registry

def _load_view(name: str, registry: dict[str, Path]):
    path = registry.get(name)
    if not path:
        raise ValueError(f"View '{name}' not found. Available: {', '.join(registry)}")
    spec = importlib.util.spec_from_file_location(f"jccli.view.{name}", path)
    mod  = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    return mod

# ---------------------------------------------------------------------------
# Filesystem trigger handler
# ---------------------------------------------------------------------------
class _TriggerHandler(FileSystemEventHandler):
    def __init__(self, manager):
        self.manager = manager
    def on_modified(self, event):
        if event.is_directory:
            return
        if os.path.abspath(event.src_path) == str(self.manager.trigger_file):
            self.manager.render_once()

# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------
class ViewManager:
    def __init__(self, client_dir: str, username: str, view_id: str, mode: str, cmd_queue: str):
        self.client_dir = Path(client_dir).resolve()
        self.username   = username
        self.cmd_queue  = Path(cmd_queue)
        self.data_dir   = self.client_dir / "data"

        # Discover views
        views_dir = self.client_dir / "scripts" / "views"
        self.registry = _discover_views(views_dir)
        if not self.registry:
            print("No view scripts discovered.", file=sys.stderr)
            sys.exit(1)
        self.active_view_id = view_id if view_id in self.registry else next(iter(self.registry))
        self.active_view    = _load_view(self.active_view_id, self.registry)

        # Choose trigger file
        self.mode = mode
        if mode == "commit":
            self.trigger_file = self.data_dir / config.CURSOR_FILE
        else:
            self.trigger_file = self.data_dir / config.WORLD_FILE
        self.trigger_file.touch(exist_ok=True)

        # Observer setup
        self.observer = Observer()
        self.observer.schedule(_TriggerHandler(self), str(self.data_dir), recursive=False)

    # ---------------- world helpers ----------------
    def _load_world(self):
        world_path = self.data_dir / config.WORLD_FILE
        try:
            with world_path.open() as fh:
                return json.load(fh)
        except Exception:
            return {}

    # ---------------- rendering --------------------
    def render_once(self):
        world = self._load_world()
        ctx   = {"username": self.username}
        # clear terminal for readability
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            self.active_view.render(world, ctx)  # type: ignore[attr-defined]
        except Exception as e:
            print(f"[view-error] {e}")

    # ---------------- input handling ---------------
    def _queue_command(self, line: str):
        try:
            with self.cmd_queue.open("a") as fh:
                fh.write(line + "\n")
        except Exception as e:
            print(f"Error queueing command: {e}")

    def _switch_view(self, vid: str):
        if vid not in self.registry:
            print(f"No such view '{vid}'. Available: {', '.join(self.registry)}")
            return
        self.active_view_id = vid
        self.active_view = _load_view(vid, self.registry)
        print(f"Switched to view '{vid}'.")
        self.render_once()

    def handle_input(self, line: str):
        line = line.strip()
        if not line:
            return
        if line.lower().startswith("view "):
            self._switch_view(line.split(maxsplit=1)[1].strip())
            return
        # delegate to current view
        if hasattr(self.active_view, "handle_input"):
            consumed = bool(self.active_view.handle_input(line, {"username": self.username}))  # type: ignore[attr-defined]
            if consumed:
                return
        # default: push to game server
        self._queue_command(line)

    # ---------------- run loop ---------------------
    def start(self):
        self.render_once()
        self.observer.start()
        try:
            while True:
                try:
                    #line = input("✎ ")
                    line = input("> ")
                except EOFError:
                    break
                self.handle_input(line)
        except KeyboardInterrupt:
            pass
        finally:
            self.observer.stop()
            self.observer.join()

# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="JC-CLI View Manager")
    p.add_argument("--dir", required=True, help="Client directory")
    p.add_argument("--username", required=True)
    p.add_argument("--cmd-queue", required=True)
    p.add_argument("--view", default="default", help="View ID to start with")
    p.add_argument("--mode", choices=("fast", "commit"), default="commit",
                   help="fast=watch world.json, commit=watch cursor.seq")
    return p.parse_args()


def main():
    args = _parse_args()
    ViewManager(args.dir, args.username, args.view, args.mode, args.cmd_queue).start()

if __name__ == "__main__":
    main()