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


def process_command(client: dict, ordered: Any) -> None:
    _append_command(client, ordered)

    seq   = ordered["seq"]
    user  = ordered["command"]["username"]
    text  = ordered["command"]["text"]
    label = "You" if user == client["username"] else user
    print(f"[{seq}] {label}: {text}")


def listen_for_broadcasts(client: dict) -> None:
    sock, dec = client["socket"], client["_decoder"]

    

    try:
        while True:
            chunk = sock.recv(config.BUFFER_SIZE)
            if not chunk:
                print("\nDisconnected from server.")
                break
            for msg in dec.feed(chunk):
                if isinstance(msg, dict) and msg.get("type") == "history_batch":
                    for cmd in msg.get("commands", []):
                        process_command(client, cmd)
                if isinstance(msg, dict) and msg.get("type") == "snapshot_zip":
                    _handle_snapshot_zip(client, msg)
                    continue
                else:
                    process_command(client, msg)
    except (socket.error, OSError) as exc:
        print(f"\nNetwork error: {exc}")

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