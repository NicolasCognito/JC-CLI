"""In-memory world state manager."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_WORLD: Optional[dict[str, Any]] = None


def load_from_file(path: str | Path) -> None:
    """Load initial world state from a JSON file."""
    global _WORLD
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        _WORLD = json.load(f)


def get_world() -> dict[str, Any]:
    """Return the current world dictionary (empty if unset)."""
    return _WORLD if _WORLD is not None else {}


def update_world(world: dict[str, Any]) -> None:
    """Replace the in-memory world state."""
    global _WORLD
    _WORLD = world


def dump_world(path: str | Path) -> None:
    """Write the current world snapshot to *path*."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(get_world(), f, indent=2)
