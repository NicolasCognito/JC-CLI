#!/usr/bin/env python3
"""
Persistent Command Worker (memory mode)

Receives JSON lines on stdin:
  {"type":"run","cmd":"raise","argv":["1"],"world":{...},"source":"<py source>","username":"me"}

Executes the command source in-process with a file-open shim so that
reads/writes to data/world.json operate on the provided world dict
and never touch disk. Returns a JSON line on stdout with fields:
  {"ok": true/false, "stdout": "...", "stderr": "...", "exit": 0/1, "world": {...}}
"""
import sys, json, os, io, builtins, traceback
from contextlib import contextmanager


@contextmanager
def _world_open_shim(world_obj: dict, cwd: str):
    target = os.path.abspath(os.path.join(cwd, "data", "world.json"))
    orig_open = builtins.open

    class _MemFile:
        def __init__(self, mode: str, initial: str = "", binary: bool = False):
            self.mode = mode
            self.binary = binary
            self._buf = io.StringIO(initial) if not binary else io.BytesIO(initial.encode("utf-8"))
            if "a" in mode:
                self._buf.seek(0, io.SEEK_END)
            self.closed = False
        def write(self, data):
            return self._buf.write(data)
        def read(self, *a, **k):
            return self._buf.read(*a, **k)
        def readline(self, *a, **k):
            return self._buf.readline(*a, **k)
        def seek(self, *a, **k):
            return self._buf.seek(*a, **k)
        def flush(self):
            pass
        def close(self):
            self.closed = True
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            self.close()

    def _open_hook(path, mode="r", *args, **kwargs):
        p = os.path.abspath(path)
        binary = "b" in mode
        if p == target:
            # Serve from provided world
            if "r" in mode and "+" not in mode:
                data = json.dumps(world_obj)
                return _MemFile(mode, data, binary)
            # For write/append, return a buffer and on close update world_obj
            mf = _MemFile(mode, "", binary)
            orig_close = mf.close
            def _close_and_capture():
                if not mf.closed:
                    try:
                        val = mf._buf.getvalue()
                        if mf.binary and isinstance(val, (bytes, bytearray)):
                            val = val.decode("utf-8", errors="replace")
                        new = json.loads(val or "{}")
                        world_obj.clear()
                        world_obj.update(new)
                    except Exception:
                        pass
                orig_close()
            mf.close = _close_and_capture  # type: ignore
            return mf
        return orig_open(path, mode, *args, **kwargs)

    builtins.open = _open_hook  # type: ignore
    try:
        yield
    finally:
        builtins.open = orig_open  # type: ignore


@contextmanager
def _capture_stdio():
    old_out, old_err = sys.stdout, sys.stderr
    out, err = io.StringIO(), io.StringIO()
    sys.stdout, sys.stderr = out, err
    try:
        yield out, err
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def _run_source(source: str, argv: list[str]):
    ns: dict[str, object] = {
        "__name__": "__main__",
        "__file__": "<in-memory-command>",
    }
    exit_code = 0
    with _capture_stdio() as (out, err):
        old_argv = sys.argv[:]
        try:
            sys.argv = ["<cmd>", *argv]
            code = compile(source, "<in-memory-command>", "exec")
            exec(code, ns, ns)
        except SystemExit as se:
            try:
                exit_code = int(se.code) if se.code is not None else 0
            except Exception:
                exit_code = 1
        except Exception:
            err.write(traceback.format_exc())
            exit_code = 1
        finally:
            sys.argv = old_argv
    return exit_code, out.getvalue(), err.getvalue()


def main():
    cwd = os.getcwd()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        if not isinstance(msg, dict) or msg.get("type") != "run":
            continue
        cmd_src = msg.get("source") or ""
        argv = msg.get("argv") or []
        world = msg.get("world") or {}
        username = msg.get("username") or ""

        os.environ["PLAYER"] = str(username)

        with _world_open_shim(world, cwd):
            code, out, err = _run_source(cmd_src, argv)

        payload = {
            "ok": code == 0,
            "stdout": out,
            "stderr": err,
            "exit": code,
            "world": world,
        }
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

