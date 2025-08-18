"""
Memory-mode shim that intercepts reads/writes to data/world.json so child
processes (command scripts and rule loop) can operate with zero disk I/O.

Enabled when JC_WORLD_MODE=memory is present in the environment of the
Python process. The in-memory world is provided via JC_MEM_WORLD_IN (JSON).

On process exit, if the target file was written, prints a single line:
    WORLD_OUTPUT: <json>
to stdout so the parent can capture the updated world.
"""
import os, io, sys, json, atexit
import builtins

if os.environ.get("JC_WORLD_MODE") == "memory":
    TARGET = os.path.abspath(os.path.join(os.getcwd(), "data", "world.json"))
    INITIAL = os.environ.get("JC_MEM_WORLD_IN", "{}")
    _orig_open = builtins.open
    _last_written: str | None = None

    class _MemFile:
        def __init__(self, mode: str, initial: str = "", binary: bool = False):
            self.mode = mode
            self.binary = binary
            if "a" in mode:
                # start with initial contents for append
                self._buf = io.StringIO(initial) if not binary else io.BytesIO(initial.encode("utf-8"))
                self._buf.seek(0, io.SEEK_END)
            elif "w" in mode or "+" in mode:
                self._buf = io.StringIO("") if not binary else io.BytesIO()
            else:  # read-only
                self._buf = io.StringIO(initial) if not binary else io.BytesIO(initial.encode("utf-8"))
            self.closed = False

        def write(self, data):
            return self._buf.write(data)

        def read(self, *args, **kwargs):
            return self._buf.read(*args, **kwargs)

        def readline(self, *args, **kwargs):
            return self._buf.readline(*args, **kwargs)

        def seek(self, *args, **kwargs):
            return self._buf.seek(*args, **kwargs)

        def flush(self):
            # no-op for memory buffer
            pass

        def close(self):
            global _last_written
            if self.closed:
                return
            self.closed = True
            if ("w" in self.mode) or ("a" in self.mode) or ("+" in self.mode):
                try:
                    val = self._buf.getvalue()
                    if self.binary and isinstance(val, (bytes, bytearray)):
                        val = val.decode("utf-8", errors="replace")
                    _last_written = str(val)
                except Exception:
                    _last_written = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()
            return False

    def _open_hook(file, mode="r", *args, **kwargs):
        path = os.path.abspath(file)
        binary = "b" in mode
        if path == TARGET:
            # Serve from memory
            return _MemFile(mode, INITIAL, binary)
        return _orig_open(file, mode, *args, **kwargs)

    builtins.open = _open_hook  # type: ignore

    @atexit.register
    def _dump_last():
        if _last_written is not None:
            try:
                # Validate and normalize to single-line JSON to simplify parsing
                obj = json.loads(_last_written)
                compact = json.dumps(obj, separators=(",", ":"))
                sys.stdout.write(f"WORLD_OUTPUT: {compact}\n")
                sys.stdout.flush()
            except Exception:
                pass
