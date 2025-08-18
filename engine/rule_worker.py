#!/usr/bin/env python3
"""
Persistent Rule Worker (memory mode)

Input (one JSON per line):
  {"type":"run","world":{...},"sources":{rid: py_source},"active":[rid,...]}

Runs rules in-process in sequence. Each rule receives the current world on
stdin and must print a JSON world on stdout. Exit codes follow JC-CLI:
  0 = changed, 9 = no change, other = error (treated as no change).

Output (one JSON per line):
  {"ok": true, "exit": 0|9, "world": {...}, "stdout": "...", "stderr": "..."}
"""
import sys, json, io, traceback
from typing import Dict, Tuple


def _run_rule_source(source: str, world: dict) -> Tuple[int, dict, str, str]:
    old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
    out_buf, err_buf = io.StringIO(), io.StringIO()
    # Provide bytes-capable stdin with .buffer
    bin_in = io.BytesIO(json.dumps(world).encode("utf-8"))
    txt_in = io.TextIOWrapper(bin_in, encoding="utf-8")
    sys.stdin, sys.stdout, sys.stderr = txt_in, out_buf, err_buf
    exit_code = 0
    try:
        ns: Dict[str, object] = {"__name__": "__main__", "__file__": "<in-memory-rule>"}
        code = compile(source, "<in-memory-rule>", "exec")
        exec(code, ns, ns)
    except SystemExit as se:
        try:
            exit_code = int(se.code) if se.code is not None else 0
        except Exception:
            exit_code = 1
    except Exception:
        err_buf.write(traceback.format_exc())
        exit_code = 1
    finally:
        # Restore stdio
        try:
            sys.stdin.detach()
        except Exception:
            pass
        sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr

    out = out_buf.getvalue()
    try:
        new_world = json.loads(out or "{}")
    except Exception:
        new_world = world

    return exit_code, new_world, out, err_buf.getvalue()


def main():
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
        world = msg.get("world") or {}
        sources = msg.get("sources") or {}
        active = msg.get("active")
        if not isinstance(active, list) or not active:
            active = list(sources.keys())

        changed = False
        agg_out, agg_err = [], []
        for rid in active:
            src = sources.get(rid)
            if not src:
                agg_err.append(f"Rule '{rid}' not found in sources\n")
                continue
            code, world, out, err = _run_rule_source(src, world)
            if out:
                agg_out.append(out)
            if err:
                agg_err.append(err)
            changed = changed or (code == 0)

        resp = {
            "ok": True,
            "exit": 0 if changed else 9,
            "world": world,
            "stdout": "".join(agg_out),
            "stderr": "".join(agg_err),
        }
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

