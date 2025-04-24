# engine/server/command_processing.py

import json, os, time, base64
from typing import Dict, Any
from . import config
from engine.core import netcodec

# -------------------------------------------------------------------- #
# Command flow


def process_command(server: Dict, command: Dict):
    """Assign global order and broadcast."""
    with server["lock"]:
        server["sequence_number"] += 1
        seq = server["sequence_number"]

        ordered = {
            "seq": seq,
            "timestamp": time.time(),
            "command": command,
        }

        _broadcast(server, ordered)
        _append_to_history(server, ordered)

        print(f"[{seq}] {command.get('username','?')}: {command.get('text','')}")


# -------------------------------------------------------------------- #
# Snapshot & history helpers


def send_snapshot(server: Dict, sock):
    """Streams client zip, then sends the session’s initial world."""
    import base64
    zip_path = os.path.join(server["session_dir"], config.SNAPSHOT_DIR, config.CLIENT_ZIP_NAME)
    try:
        # 1) send the client code snapshot ZIP
        with open(zip_path, "rb") as fh:
            blob = base64.b64encode(fh.read()).decode("ascii")
        packet = {"type": "snapshot_zip", "name": config.CLIENT_ZIP_NAME, "b64": blob}
        sock.sendall(netcodec.encode(packet))
    except Exception as exc:
        print("Snapshot send failed:", exc)

    # 2) send the initial world JSON
    world_path = os.path.join(server["session_dir"], config.INITIAL_WORLD_FILE)
    try:
        with open(world_path, "r", encoding="utf-8") as f:
            world = json.load(f)
        init_pkt = {
            "type": "initial_world",
            "world": world
        }
        sock.sendall(netcodec.encode(init_pkt))
    except Exception as exc:
        print("Initial world send failed:", exc)


# -------------------------------------------------------------------- #
# NEW: paged history


def send_history_meta(server: Dict, sock):
    """Send highest sequence number so client knows how many pages to pull."""
    meta = {"type": "history_meta", "highest_seq": server["sequence_number"], "page_size": config.HISTORY_PAGE_SIZE}
    sock.sendall(netcodec.encode(meta))


def send_history_page(server: Dict, sock, from_seq: int):
    """Send a page beginning at *from_seq* inclusive."""
    page_size = config.HISTORY_PAGE_SIZE
    try:
        with open(server["history_path"], "r") as fh:
            history = json.load(fh)
    except Exception:
        history = []

    page = [cmd for cmd in history if cmd.get("seq", 0) >= from_seq][:page_size]
    packet = {"type": "history_page", "commands": page}
    sock.sendall(netcodec.encode(packet))


# -------------------------------------------------------------------- #
# Internal helpers


def _broadcast(server: Dict, ordered: Dict):
    blob = netcodec.encode(ordered)
    dead = []
    for c in server["clients"]:
        try:
            c.sendall(blob)
        except Exception:
            dead.append(c)
    for c in dead:
        server["clients"].remove(c)
        try:
            c.close()
        except Exception:
            pass


def _append_to_history(server: Dict, ordered: Dict):
    try:
        if os.path.exists(server["history_path"]):
            with open(server["history_path"], "r") as fh:
                hist = json.load(fh)
        else:
            hist = []
        hist.append(ordered)
        with open(server["history_path"], "w") as fh:
            json.dump(hist, fh, indent=2)
    except Exception as exc:
        print("History write failed:", exc)
