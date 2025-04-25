# engine/client/client_network.py

import shutil
import os, json, socket
from typing import Any
import config
from engine.core import netcodec, utils
from engine.client import sequencer_control      # restart helper
from engine.core.utils import clear_client_state

# ---------------------------------------------------------------------------


def connect(client: dict) -> bool:
    try:
        # Reset command log and cursor files before connecting
        commands_path = client["commands_path"]
        cursor_path = os.path.join(client["data_dir"], config.CURSOR_FILE)
        scripts_dir = os.path.join(client["client_dir"], "scripts")
        
        # Clear local state using shared utility
        clear_client_state(commands_path, cursor_path, scripts_dir)

        # Proceed with connection
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
    """Append newline-delimited JSON to commands.log"""
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


HISTORY_PAGE_SIZE = config.HISTORY_PAGE_SIZE


def listen_for_broadcasts(client: dict):
    sock = client["socket"]
    dec = netcodec.NetDecoder()
    client["_history_high"] = None
    client["_next_seq_pull"] = 1

    try:
        while True:
            chunk = sock.recv(config.BUFFER_SIZE)
            if not chunk:
                print("\nDisconnected.")
                break
            for msg in dec.feed(chunk):
                if isinstance(msg, dict):
                    typ = msg.get("type")

                    if typ == "snapshot_zip":
                        _handle_snapshot_zip(client, msg)

                    elif typ == "initial_world":
                        # new: write the initial world into data/world.json
                        dst = os.path.join(client["data_dir"], config.WORLD_FILE)
                        try:
                            with open(dst, "w", encoding="utf-8") as f:
                                json.dump(msg["world"], f, indent=2)
                            print("Initial world received.")
                        except Exception as exc:
                            print("Failed to write initial world:", exc)
                    # ───────── RESET – blank client and re-seed world ───────
                    elif typ == "reset":
                        _handle_reset(client, msg)          # NEW

                    elif typ == "history_meta":
                        client["_history_high"] = msg["highest_seq"]
                        _request_history(client)

                    elif typ == "history_page":
                        for cmd in msg.get("commands", []):
                            process_command(client, cmd)
                            client["_next_seq_pull"] = cmd["seq"] + 1
                        _request_history(client)

                    elif "seq" in msg:
                        process_command(client, msg)

    except Exception as exc:
        print("Listener error:", exc)

# ---------------------------------------------------------------------------#
# RESET helper                                                               #
# ---------------------------------------------------------------------------#

def _handle_reset(client: dict, msg: dict):
    """Clear local history/cursor, restart sequencer, write fresh world."""
    print("\n=== SESSION RESET received — returning to initial state ===")

    # 1) nuke log + cursor
    commands = client["commands_path"]
    cursor   = os.path.join(client["data_dir"], config.CURSOR_FILE)
    scripts  = os.path.join(client["client_dir"], "scripts")
    utils.clear_client_state(commands, cursor, scripts)

    # 2) drop the running sequencer and spin a new one
    sequencer_control.cleanup(client)
    sequencer_control.start_sequencer(client)

    # 3) write new world
    dst = os.path.join(client["data_dir"], config.WORLD_FILE)
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(msg["world"], fh, indent=2)

    # 4) reset history-pull helpers
    client["_history_high"]  = None
    client["_next_seq_pull"] = 1

    # 5) re-emit INITIAL_COMMAND so per-client init runs on the fresh world
    try:
        send_command(client, config.INITIAL_COMMAND)
        print(f"Re-sent INITIAL_COMMAND: {config.INITIAL_COMMAND}")
    except Exception as exc:
        print("Could not send INITIAL_COMMAND after reset:", exc)


def _request_history(client):
    high = client.get("_history_high")
    nextseq = client.get("_next_seq_pull", 1)
    if high is None or nextseq > high:
        return  # done
    packet = {"type": "history_request", "from": nextseq}
    client["socket"].sendall(netcodec.encode(packet))


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