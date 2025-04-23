# engine/server/command_processing.py
"""Coordinator-side sequence stamping and broadcast (framed)"""

import json
import time
import os
from typing import Dict, Any

from engine.core import netcodec

# ---------------------------------------------------------------------------#


def process_command(server: Dict, command: Dict) -> None:
    """Assign a global sequence number and distribute."""
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

        username = command.get("username", "unknown")
        text = command.get("text", "")
        print(f"[{seq}] {username}: {text}")


def send_history(server: Dict, client_socket) -> None:
    """Push the full backlog to a newly connected client (single framed msg)."""
    try:
        if not os.path.exists(server["history_path"]):
            return

        with open(server["history_path"], "r") as fh:
            history = json.load(fh)

        if not history:
            print("No history to send.")
            return

        print(f"Sending {len(history)} commands of history to new client.")
        packet = {
            "type": "history_batch",
            "commands": history,
        }
        client_socket.sendall(netcodec.encode(packet))
    except Exception as exc:
        print(f"History send failed: {exc}")


# ---------------------------------------------------------------------------#
# Internal helpers                                                           #
# ---------------------------------------------------------------------------#


def _broadcast(server: Dict, ordered_command: Dict) -> None:
    """Frame + send the message to every connected client."""
    blob = netcodec.encode(ordered_command)
    dead = []

    for sock in server["clients"]:
        try:
            sock.sendall(blob)
        except Exception:
            dead.append(sock)

    for sock in dead:
        if sock in server["clients"]:
            server["clients"].remove(sock)
        try:
            sock.close()
        except Exception:
            pass


def _append_to_history(server: Dict, ordered_command: Dict) -> None:
    try:
        if os.path.exists(server["history_path"]):
            with open(server["history_path"], "r") as fh:
                history = json.load(fh)
        else:
            history = []

        history.append(ordered_command)
        with open(server["history_path"], "w") as fh:
            json.dump(history, fh, indent=2)
    except Exception as exc:
        print(f"Failed to write history: {exc}")
