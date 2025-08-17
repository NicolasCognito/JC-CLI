# Repository Guidelines

## Project Structure & Module Organization
- engine/: Infrastructure realm (core, client, server). Deterministic networking, sequencing, snapshots.
- scripts/: Logic realm. Place game code here only.
  - scripts/commands/: One file per player command.
  - scripts/rules/: Automatic effects run after commands.
  - scripts/views/: Session UI renderers.
- app/: Entry scripts
  - app/thin_server.py, app/thin_client.py
  - app/orchestrator.py, app/rule_loop.py, app/sequencer.py, app/view.py
- `jc-cli.py`: Interactive shell for sessions.
- templates/: Seed worlds (e.g., `templates/default/initial_world.json`).
- var/sessions, var/clients: Runtime data and local client workspaces.
- docs/: Deep-dive guides for designers and rule authors.

## Build, Test, and Development Commands
- Install deps: `pip install watchdog` (Python ≥3.6).
- Start shell: `python jc-cli.py` (then run interactive commands).
- Quick flow: `start-session my_s default` → `join-session my_s me`.
- Run server/client directly (advanced): `python app/thin_server.py`, `python app/thin_client.py --session <name> --user <me>`.

## Coding Style & Naming Conventions
- Python style: 4‑space indent, PEP 8, `snake_case` for functions/variables, `CAPS` for constants.
- Commands: `scripts/commands/<name>.py` must start with `NAME = "<command>"` as the first non‑comment line.
- Rules: `scripts/rules/<id>.py` must start with `NAME = "<rule_id>"`; read world from stdin, write to stdout, exit 0 (changed) or 9 (no change).
- Determinism: No network, time, or randomness in the logic realm. Let failures surface—avoid defensive wrappers that mask errors.

## Testing Guidelines
- No formal test suite. Prefer fast smoke tests:
  - Create session, issue commands, verify world diffs in `var/sessions/<session>/data/world.json`.
  - Use `scripts/commands/list_rules.py` and related examples to validate discovery.
- Keep rules atomic; verify exit codes (0/9) and repeated stability on replays.
- See `docs/jccli-rules-guide.md` for correct rule I/O patterns.

## Commit & Pull Request Guidelines
- Commits: Imperative subject line (≤72 chars). Consider Conventional Commits (e.g., `feat(engine): ...`, `fix(rules): ...`).
- PRs: Clear summary, rationale, and scope; link issues; include before/after terminal output or world.json diffs when relevant.
- Requirements: Touch only one concern per PR; update docs/templates when behavior or file formats change; add a minimal example in `scripts/` when introducing new patterns.

## Security & Configuration Tips
- Only the engine reads/writes files and handles networking. Logic realm must operate via stdin/stdout and world mutations.
- Avoid nondeterministic sources; if unavoidable, pass explicit parameters via commands, not hidden globals.
