"""
utils.py

Small shared helpers used by every stage of the rendering pipeline
(build.py, renderer.py, and later avatar.py / github.py / leetcode.py).

Kept dependency-free (stdlib only) so it can be imported anywhere
without worrying about install order.
"""

from __future__ import annotations

import random
from pathlib import Path

# Project root = one level up from this file's directory (scripts/ -> profile-engine/)
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
GENERATED_DIR = ROOT_DIR / "generated"


def read_lines(filename: str) -> list[str]:
    """
    Read a text asset file (e.g. 'quotes.txt') from assets/ and return
    a list of non-empty, stripped lines.
    """
    path = ASSETS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Asset file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]

    return [line for line in lines if line]


def random_line(filename: str) -> str:
    """Return a single random non-empty line from an assets file."""
    lines = read_lines(filename)
    if not lines:
        return ""
    return random.choice(lines)


def build_boot_sequence(filename: str = "boot.txt") -> str:
    """
    Return the full boot sequence as a single multi-line string,
    ready to drop into a markdown code block.
    """
    lines = read_lines(filename)
    return "\n".join(lines)


def ensure_generated_dir() -> None:
    """Make sure generated/ exists before anything tries to write to it."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
