# JC‑CLI PROTOTYPE ARCHITECTURE — CONCEPTUAL BLUEPRINT

## Purpose and Scope

JC‑CLI (JSON-Controller-CLI) is a network‑first, deterministic command‑line shell intended for the first week of game experimentation. The objective is to validate that a designer‑typed command can traverse a network, drive rule logic, mutate shared world data, and render identically on every client—with **zero infrastructure ceremony**. Once the proto‑alpha play‑test ends, the engine is archived and replaced. This blueprint states *what* the framework must do and *where* responsibilities live, while leaving concrete implementation details open to the developer.

## Core Principle: Two Realms, Two Files

JC‑CLI draws an inviolable line between infrastructure and logic.

- **Infrastructure Realm** (Python engine) owns networking, command ordering, persistence, and rendering. It may only *append* to the command list and *read* the world.
- **Logic Realm** (Lua scripts or disciplined Python) owns every state mutation. It may only *read* the command list and *write* the world. It is isolated from sockets, clocks and operating‑system APIs.

Communication passes exclusively through two files that live side by side in the repository. One file contains the mutable world; the other contains a chronological list of **player** commands. Automatic effects created by rules are executed locally after each player command and are **not** added to the list. This inverse‑permission model is the architectural safety belt; any deviation breaks determinism.

## Recommended Folder Layout (Rationale in italics)

```
project_root/
├─ engine.py          # Entry point that wires input, network, scheduler, and view
├─ engine/            # Infrastructure realm. *Keeps all non‑game code in one box.*
├─ scripts/           # Logic realm. *Physically separate from engine to prevent imports.*
│   ├─ commands/      # One file per player command keyword
│   └─ recipes/       # Reusable rule capsules (card abilities, timers…)
├─ data/              # Persistent surface between realms. *Everything transparent, git‑diffable.*
│   ├─ world.<ext>    # Mutable world snapshot (format up to the team)
│   └─ commands.<ext> # Ordered list of player commands only
└─ templates/         # Optional seed worlds for quick restarts
```

Developers are free to choose file extensions, data schemas, or language versions—but *physical separation* mirrors the logical boundary, making accidental cross‑talk impossible.

## Absolute Minimalism Doctrine

> *“Every component must defend its existence.”*

1. **No validation layer** – Commands are trusted inputs. If a malformed command breaks the game, the break becomes observable data rather than a swallowed error. This maximises transparency and accelerates debugging.
2. **No hidden abstraction** – There is no ORM, no service locator, no private protocol translation. Raw data structures are stored exactly as they appear on disk, so designers can open them in a text editor and understand the state instantly.
3. **No alternative modes** – The engine is always networked. Even single‑player spins up a local coordinator so the path from key‑press to world mutation is identical everywhere.
4. **No extra features without purpose** – Sound, UI widgets, and asset pipelines belong in later stages; adding them here only obscures the rule experiment.

Radical minimalism makes JC‑CLI cheap to build, trivial to reason about, and safe to delete.

## Always‑Network Execution Model

JC‑CLI never operates offline. A coordinator process stamps commands with a monotonically increasing sequence number and broadcasts them. The coordinator is intentionally ignorant of rules and state; it is a packet shuffler only.

## High‑Level Command Flow

1. **Input** Client captures raw text and sends it to the coordinator.
2. **Ordering** Coordinator assigns global order and broadcasts.
3. **Distribution** Each client appends the record to the command list and enqueues it.
4. **Execution** When a record reaches the head of the queue, the engine invokes the matching logic script by name.
5. **World Mutation** The script mutates the world data directly and may call recipe scripts.
6. **Rule Pass** Immediately after the player command resolves, each client runs a pure rule loop that applies automatic effects locally.
7. **Render** Engine signals the view; view opens the world file and prints.

Because every client starts from the same seed and processes the identical player list with identical rule code, convergence is guaranteed.

## Automatic Effects and Purity Restrictions

Rule code must remain pure: no wall‑time reads and no non‑deterministic sources except a random generator seeded from deterministic inputs (such as the current player index). This ensures that automatic effects, though unlisted, produce identical world deltas on every machine.

## View Discipline

Views are read‑only. Player view redacts secrets; admin view reveals all; summary view prints high‑level markers. Views can be swapped or rewritten freely without risking determinism.

## Replay and Archiving

A replay consists of the initial world snapshot, the ordered player command list, and the exact rule scripts used during the session. Replaying in a clean environment must reproduce the final world byte‑for‑byte. Archived replays serve as living test cases and design documents.

## Decommissioning Checklist

1. Freeze at least three significant sessions (world, command list, rule scripts).
2. Tag the repository and archive the prototype.
3. Carry only the design insights and replay bundles into the production engine.

## Summary

JC‑CLI embodies *boundary clarity* and *radical minimalism*: one realm orders commands, the other mutates state; one file logs players, one file stores the world. Nothing more. Keep these constraints and recommendations intact—especially the folder boundary, the no‑validation stance, and the network‑only pipeline—and any developer can re‑implement the engine confidently while custom‑tailoring the low‑level details.
