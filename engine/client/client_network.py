# engine/client/client_network.py
"""Client-side networking helpers with length-prefixed framing"""

import socket
from typing import Any
from engine.core import config
from engine.core import netcodec

# Public API -----------------------------------------------------------------


def connect(client: dict) -> bool:
    """Open the TCP connection to the coordinator."""
    try:
        host, port = client["server_host"], client["server_port"]
        print(f"Connecting to server at {host}:{port} …")
        client["socket"].connect((host, port))
        # Create a decoder for this socket
        client["_decoder"] = netcodec.NetDecoder()
        return True
    except (ConnectionError, OSError) as exc:
        print(f"Connection error: {exc}")
        return False


def disconnect(client: dict) -> None:
    """Close the TCP socket."""
    try:
        client["socket"].close()
    except Exception:
        pass


def send_command(client: dict, command_text: str) -> bool:
    """Send a *player* command to the coordinator."""
    try:
        payload = {
            "username": client["username"],
            "text": command_text,
        }
        client["socket"].sendall(netcodec.encode(payload))
        return True
    except (socket.error, OSError) as exc:
        print(f"Network error while sending: {exc}")
        return False


# ---------------------------------------------------------------------------#
# Receiving / processing broadcasts                                          #
# ---------------------------------------------------------------------------#


def process_command(client: dict, ordered_command: Any) -> None:
    """Append the command to file and show it in the local console."""
    try:
        _append_command_to_file(client, ordered_command)

        seq = ordered_command["seq"]
        username = ordered_command["command"]["username"]
        cmd_text = ordered_command["command"]["text"]

        prefix = "You" if username == client["username"] else username
        print(f"[{seq}] {prefix}: {cmd_text}")
    except Exception as exc:
        print(f"Error processing command: {exc}")


def listen_for_broadcasts(client: dict) -> None:
    """Background loop that decodes framed messages from the server."""
    sock = client["socket"]
    decoder: netcodec.NetDecoder = client["_decoder"]

    try:
        while True:
            chunk = sock.recv(config.BUFFER_SIZE)
            if not chunk:
                print("\nDisconnected from server.")
                break

            for message in decoder.feed(chunk):
                # History batch or single command
                if isinstance(message, dict) and message.get("type") == "history_batch":
                    cmds = message.get("commands", [])
                    print(f"Received history batch of {len(cmds)} commands.")
                    for cmd in cmds:
                        process_command(client, cmd)
                else:
                    process_command(client, message)
    except (socket.error, OSError) as exc:
        print(f"\nNetwork error: {exc}")
    except Exception as exc:
        print(f"Listener failure: {exc}")


# ---------------------------------------------------------------------------#
# Internal helpers                                                           #
# ---------------------------------------------------------------------------#


def _append_command_to_file(client: dict, ordered_command: Any) -> None:
    """Local persistence helper (append mode will be swapped in Issue 2)."""
    import json, os

    path = client["commands_path"]
    try:
        # Read → mutate → write (will change in the next issue)
        if os.path.exists(path):
            with open(path, "r") as fh:
                data = json.load(fh)
        else:
            data = []

        data.append(ordered_command)
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
    except Exception as exc:
        print(f"Error saving command to file: {exc}")
