# engine/client/client_network.py
"""Client‑side networking helpers – append‑only commands.log"""

import os, json, socket
from typing import Any
from engine.core import config, netcodec

# ---------------------------------------------------------------------------


def connect(client: dict) -> bool:
    try:
        host, port = client["server_host"], client["server_port"]
        print(f"Connecting to server at {host}:{port} …")
        client["socket"].connect((host, port))
        client["_decoder"] = netcodec.NetDecoder()
        return True
    except (ConnectionError, OSError) as exc:
        print(f"Connection error: {exc}")
        return False


def disconnect(client: dict) -> None:
    try:
        client["socket"].close()
    except Exception:
        pass


def send_command(client: dict, command_text: str) -> bool:
    try:
        payload = {"username": client["username"], "text": command_text}
        client["socket"].sendall(netcodec.encode(payload))
        return True
    except (socket.error, OSError) as exc:
        print(f"Network error while sending: {exc}")
        return False

# ---------------------------------------------------------------------------
# Receiving                                                                 
# ---------------------------------------------------------------------------

def _append_command(client: dict, ordered: Any) -> None:
    """Append newline‑delimited JSON to commands.log"""
    path = client["commands_path"]
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ordered, separators=(",", ":")) + "\n")
    except Exception as exc:
        print(f"Error storing command locally: {exc}")


def process_command(client: dict, ordered_command: dict) -> None:
    """Append the command and show it."""
    try:
        _append_command(client, ordered_command)

        seq   = ordered_command["seq"]
        user  = ordered_command["command"]["username"]
        text  = ordered_command["command"]["text"]
        who   = "You" if user == client["username"] else user
        print(f"[{seq}] {who}: {text}")
    except Exception as exc:
        print(f"Command processing error: {exc}")

# ---------------------------------------------------------------------------#

def listen_for_broadcasts(client: dict) -> None:
    """Background thread – decodes frames and routes by packet *type*."""
    sock     = client["socket"]
    decoder  = netcodec.NetDecoder()

    try:
        while True:
            chunk = sock.recv(config.BUFFER_SIZE)
            if not chunk:
                print("\nDisconnected from server.")
                break

            for msg in decoder.feed(chunk):
                # --- packet routing ------------------------------------
                if isinstance(msg, dict):
                    ptype = msg.get("type")
                    if ptype == "snapshot_zip":
                        _handle_snapshot_zip(client, msg)
                    elif ptype == "history_batch":
                        for cmd in msg.get("commands", []):
                            process_command(client, cmd)
                    # ignore any other control packet types for now
                    elif "seq" in msg:        # genuine ordered command
                        process_command(client, msg)
                    else:
                        # Unknown packet; keep decoder alive, just log once
                        print("Received non-command packet, ignored:", msg.keys())
                # If somehow a non-dict arrives we drop it silently
    except (socket.error, OSError) as exc:
        print(f"\nNetwork error: {exc}")
    except Exception as exc:
        print(f"Listener failure: {exc}")


def _handle_snapshot_zip(client: dict, msg: dict):
    import base64, zipfile, io, os, shutil, sys
    try:
        data   = base64.b64decode(msg["b64"])
        buffer = io.BytesIO(data)
        with zipfile.ZipFile(buffer, "r") as zf:
            zf.extractall(client["client_dir"])
        print("Snapshot received & unpacked.")
    except Exception as exc:
        print(f"Snapshot unpack error: {exc}")