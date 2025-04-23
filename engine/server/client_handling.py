# engine/server/client_handling.py
"""Per-client receive loop with framed decoding"""

import socket
from engine.core import config, netcodec
from engine.server import command_processing

# ---------------------------------------------------------------------------#


def handle_client(server: dict, client_socket: socket.socket, addr) -> None:
    """Receive player commands from one client and pass them to the processor."""
    decoder = netcodec.NetDecoder()

    try:
        while True:
            chunk = client_socket.recv(config.BUFFER_SIZE)
            if not chunk:
                break

            for message in decoder.feed(chunk):
                try:
                    command_processing.process_command(server, message)
                except Exception as exc:
                    print(f"Error processing command from {addr}: {exc}")
    except (socket.error, OSError) as exc:
        print(f"Socket error with {addr}: {exc}")
    finally:
        if client_socket in server["clients"]:
            server["clients"].remove(client_socket)
        client_socket.close()
        print(f"Connection closed: {addr}")
