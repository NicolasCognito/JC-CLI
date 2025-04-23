#!/usr/bin/env python3
"""
engine/core/netcodec.py
Length-prefixed JSON framing helpers for JC-CLI networking.
"""

import json
import struct
from typing import Any, List

HEADER_LEN = 4  # 4-byte big-endian unsigned int


def encode(obj: Any) -> bytes:
    """
    Serialize *obj* to JSON and prefix it with a 4-byte length header.

    Returns
    -------
    bytes
        Header + UTF-8 JSON payload.
    """
    payload = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    header = struct.pack(">I", len(payload))
    return header + payload


class NetDecoder:
    """
    Incremental decoder for the same length-prefixed format.

    Usage
    -----
    >>> dec = NetDecoder()
    >>> for msg in dec.feed(sock.recv(4096)):
    ...     handle(msg)
    """

    def __init__(self) -> None:
        self._buf = b""

    def feed(self, data: bytes) -> List[Any]:
        """
        Feed raw bytes from the socket and return all complete JSON
        objects decoded since the previous call.
        """
        self._buf += data
        out: List[Any] = []

        while True:
            if len(self._buf) < HEADER_LEN:
                break

            length = struct.unpack(">I", self._buf[:HEADER_LEN])[0]
            if len(self._buf) < HEADER_LEN + length:
                break

            payload = self._buf[HEADER_LEN : HEADER_LEN + length]
            self._buf = self._buf[HEADER_LEN + length :]

            try:
                out.append(json.loads(payload.decode("utf-8")))
            except json.JSONDecodeError:
                # Skip malformed payloads but keep processing stream
                continue

        return out
