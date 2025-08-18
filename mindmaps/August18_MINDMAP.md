# August 18 – JC‑CLI Engine Mindmap (File vs Memory Modes)

This document maps the new execution modes, data‑flows, components, and supporting tooling added today. It’s a living “how it fits together” guide for designers and engine devs.

## 1) Execution Modes
- File mode (default):
  - World state lives in `data/world.json`.
  - Orchestrator executes the command process, then `rule_loop.py` (both as fresh Python processes).
  - Rules read world from `stdin`, write world to `stdout`; rule loop persists final `world.json`.
  - View reads `world.json` directly (fast/commit triggers supported).
- Memory mode (opt‑in via `config.WORLD_MODE="memory"` or env `JC_WORLD_MODE=memory`):
  - World state is held in sequencer memory only.
  - Command + rules run without touching disk.
  - View fetches world from a small socket server inside the sequencer (no file reads), and typically triggers on `cursor.seq`.

## 2) High‑Level Dataflows
- File mode:
  1) Server broadcasts an ordered command.
  2) Client appends to `commands.log`; sequencer sees change.
  3) Sequencer runs `engine/orchestrator.py <command-text> <user>`.
  4) Orchestrator: ensure `world.json` exists → run command → run `rule_loop.py` → persist `world.json`.
  5) View re-renders on `world.json` (fast) or `cursor.seq` (commit).

- Memory mode:
  1) Server broadcasts an ordered command.
  2) Client appends to `commands.log`; sequencer sees change.
  3) Sequencer sends a job to the persistent `command_worker` with in‑memory world + the command source.
  4) Sequencer then sends a job to the persistent `rule_worker` with the post‑command world + all rule sources.
  5) Sequencer updates in‑memory world; view fetches it via local socket and re‑renders on `cursor.seq`.

## 3) Components and Responsibilities

### Sequencer (`engine/sequencer.py`)
- Common:
  - Watches `data/commands.log`; advances `data/cursor.seq` per processed entry.
  - Runs exactly‑once in strict `seq` order.
- Memory mode extras:
  - Maintains `self.memory_world` across commands.
  - Starts a tiny TCP server (host `JC_MEM_VIEW_HOST` default `127.0.0.1`, port `JC_MEM_VIEW_PORT`) to serve world JSON to the view.
  - Discovers and caches all command sources (`scripts/commands/*.py`) and rule sources (`scripts/rules/*.py`) at startup.
  - Spawns and reuses:
    - `command_worker.py` — runs commands in‑process.
    - `rule_worker.py` — runs rules in‑process.
  - Updates in‑memory world from worker responses (no file I/O during command/rule execution).

### Orchestrator (`engine/orchestrator.py`)
- File mode: authoritative path.
  - Discovers commands from `scripts/commands/**` (by `NAME = "..."`).
  - Runs the command script process, then runs `rule_loop.py`.
  - Prints all stdout/stderr and returns 0 only if command succeeds and rule loop returns 0 or 9.
- Memory mode: legacy support remains (memshim, `WORLD_FINAL:`) but the sequencer prefers `command_worker` + `rule_worker`. In practice, memory mode orchestration is handled by the workers.

### Rule Loop (`engine/rule_loop.py`)
- File mode: authoritative path.
  - Discovers rules at startup (by `NAME = "..."`).
  - Runs only rules listed in `world['rules_in_power']` if present; otherwise all discovered rules.
  - Feeds `world` to each rule on stdin; collects stdout; persists final `world.json`.
- Memory mode: the sequencer now uses the persistent `rule_worker.py` instead of spawning `rule_loop.py`.
  - `rule_loop.py` also supports `JC_RULE_PACK` (in‑memory rule sources) if used standalone.

### View Manager (`engine/view.py`)
- Discovers game views from `scripts/views/**` (by `NAME = "..."`).
- Modes:
  - `commit` (recommended): triggers on `cursor.seq` bumps; re-renders final, post‑rules world.
  - `fast`: triggers on `world.json` writes (file mode only).
- Memory mode integration:
  - CLI flags `--mem-host/--mem-port` switch `_load_world()` to fetch via socket instead of `world.json`.
  - Thin client (`engine/thin_client.py`) passes these flags when memory mode is enabled via env or config.

### Thin Client (`engine/thin_client.py`)
- On startup:
  - Connects to server; launches sequencer.
  - Creates and monitors `data/command_queue.txt` for ad‑hoc commands (from CLI or view).
  - In memory mode, selects a deterministic view port if not provided and injects it into the view.

## 4) New Workers (Memory Mode)

### Command Worker (`engine/command_worker.py`)
- Persistent Python process that executes command sources in‑process.
- Input: one JSON per line:
  - `{ "type":"run", "cmd":"raise", "argv":["4"], "world":{...}, "source":"<python>", "username":"alice" }`
- Behavior:
  - Temporarily shims `open("data/world.json")` to read/write the provided `world` dict (no disk I/O).
  - Executes the command source with `__main__` semantics and `sys.argv` set to match the CLI.
  - Captures stdout/stderr and SystemExit.
- Output: one JSON per line:
  - `{ "ok": true|false, "exit": 0|1, "stdout": "...", "stderr": "...", "world": { ...updated... } }`

### Rule Worker (`engine/rule_worker.py`)
- Persistent Python process that executes rules in‑process.
- Input: one JSON per line:
  - `{ "type":"run", "world":{...}, "sources": { rid: "<python>" }, "active":[rid,...] }`
- Behavior:
  - For each rule in `active` (or all `sources` if `active` missing):
    - Feeds current world to the rule via stdin (bytes, as in original contract).
    - Executes the rule source with `__main__` semantics.
    - Parses stdout JSON; updates the world; tracks if any rule changed it (exit 0).
- Output: one JSON per line:
  - `{ "ok": true, "exit": 0|9, "stdout": "concat of rules stdout", "stderr": "concat of rules stderr", "world": { ...final... } }`

## 5) Mem‑Shim (`engine/memshim/sitecustomize.py`)
- Activates automatically in child processes when `JC_WORLD_MODE=memory`.
- Intercepts `open("data/world.json")` reads and writes:
  - Reads return `JC_MEM_WORLD_IN` JSON.
  - Writes are captured; on process exit a single marker is printed:
    - `WORLD_OUTPUT: { ...single-line-json... }`.
- The shim normalizes to single-line JSON to avoid truncation.

## 6) Environment Vars & Config
- `config.WORLD_MODE`: "file" (default) or "memory".
- `JC_WORLD_MODE`: overrides mode at runtime; set to `memory` to enable memory pipeline.
- `JC_MEM_WORLD_IN`: the JSON world passed into a child process (used by shim/legacy path).
- `JC_CMD_SRC`: in-memory command Python source (used by orchestrator memory path; workers get the source via stdin JSON).
- `JC_RULE_PACK`: JSON map of rule_id → source (used by rule loop memory path; workers get sources via stdin JSON).
- `JC_MEM_VIEW_HOST`, `JC_MEM_VIEW_PORT`: host/port for view to fetch world from sequencer in memory mode.

## 7) Performance Notes
- Biggest wins achieved by:
  - Eliminating per‑command Python process startup (command worker).
  - Eliminating per‑rule Python process startup (rule worker).
  - Removing repeated disk reads for command/rule scripts in memory mode.
- Remaining costs:
  - JSON encode/decode across worker boundaries.
  - Sequencer still writes `commands.log` and `cursor.seq` (small).
  - On Windows/WSL, avoid running from `/mnt/<drive>` for file mode blasts; prefer ext4 path.

## 8) Known Issues & Mitigations
- File mode stress (Windows 10053) during massive bursts:
  - Cause: burst sends + heavy per‑command process/disk churn can starve the client and close the socket.
  - Mitigation: add tiny throttling in `command_loop()` for file mode (future patch), or pace the source (batch script), or run from ext4.
- View `fast` mode has no effect in memory mode (no `world.json` writes); use `commit`.

## 9) Developer Tips
- Memory mode is designed for performance testing and deterministic behavior without hidden I/O.
- File mode remains the reference path for world editing and simple debugging.
- To validate the pipeline, tail the sequencer console:
  - Command worker responses (stdout/stderr and exit) are printed.
  - Rule worker responses (stdout/stderr and exit) are printed.

## 10) Scripts & Utilities
- `quick_session.bat`: one‑shot server + two clients (alice/bob).
- `quick_blast_session.bat` (new):
  - Starts a session; joins alice; waits for `command_queue.txt` then enqueues 100× `raise 4`; joins bob.
  - Usage: `quick_blast_session.bat [optional-session-name]`.

## 11) How to Run
- File mode (default):
  - `python jc-cli.py start-session my_s default`
  - `python jc-cli.py join-session my_s alice`
- Memory mode:
  - Set env `JC_WORLD_MODE=memory` (or set `config.WORLD_MODE="memory"`).
  - Use the same session/joins; the view will auto‑switch to socket fetch.

## 12) Determinism & Safety
- Logic realm (commands/rules/views) remains pure: no time, network, or nondeterministic sources.
- Workers and shim preserve the stdin/stdout contracts; world mutations remain JSON‑to‑JSON with explicit exits.
- Network/file I/O is isolated to the engine layer.

---
If you need a sequence diagram or timing overlay for any path, we can extend this doc with profiling hooks and charts.

