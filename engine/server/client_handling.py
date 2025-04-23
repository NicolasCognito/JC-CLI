# engine/server/client_handling.py
"""Per‑client loop that now also replies to history page requests."""

import socket, json
from engine.core import config, netcodec
from engine.server import command_processing


def handle_client(server, sock: socket.socket, addr):
    decoder = netcodec.NetDecoder()

    # push snapshot & meta immediately
    command_processing.send_snapshot(server, sock)
    command_processing.send_history_meta(server, sock)

    try:
        while True:
            chunk = sock.recv(config.BUFFER_SIZE)
            if not chunk:
                break
            for msg in decoder.feed(chunk):
                # history page request from client
                if isinstance(msg, dict) and msg.get("type") == "history_request":
                    frm = int(msg.get("from", 1))
                    command_processing.send_history_page(server, sock, frm)
                    continue
                # otherwise treat as player command
                try:
                    command_processing.process_command(server, msg)
                except Exception as exc:
                    print(f"Error processing from {addr}: {exc}")
    except Exception as exc:
        print(f"Socket error with {addr}: {exc}")
    finally:
        if sock in server["clients"]:
            server["clients"].remove(sock)
        sock.close()
        print("Connection closed:", addr)