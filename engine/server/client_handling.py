# engine/server/client_handling.py
"""Per‑client loop that now also replies to history page requests."""

import socket, json
import config
from engine.core import netcodec
from engine.server import command_processing


def handle_client(server, sock: socket.socket, addr):
    decoder = netcodec.NetDecoder()
    client_username = None  # We'll store the username here when we first get it

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
                    # Store username from first command received
                    if client_username is None and isinstance(msg, dict) and "username" in msg:
                        client_username = msg["username"]
                    
                    command_processing.process_command(server, msg)
                except Exception as exc:
                    print(f"Error processing from {addr}: {exc}")
    except Exception as exc:
        print(f"Socket error with {addr}: {exc}")
    finally:
        # Remove the socket from server clients list
        if sock in server["clients"]:
            server["clients"].remove(sock)
        sock.close()
        print("Connection closed:", addr)
        
        # Broadcast disconnect message if we know the username
        if client_username:
            disconnect_msg = {
                "username": "client_username", 
                "text": config.DISCONNECT_COMMAND
            }
            command_processing.process_command(server, disconnect_msg)