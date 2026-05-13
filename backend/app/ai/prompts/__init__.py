"""Prompt loader — caches text files in memory."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Return the contents of ``<name>.txt`` from the prompts directory."""
    if not name.endswith(".txt"):
        name = f"{name}.txt"
    path = _PROMPTS_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
