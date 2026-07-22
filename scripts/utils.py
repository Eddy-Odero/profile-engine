"""
utils.py

Small shared helpers used by every stage of the rendering pipeline
(build.py, renderer.py, and later avatar.py / github.py / leetcode.py).

Kept dependency-free (stdlib only) so it can be imported anywhere
without worrying about install order.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

# Project root = one level up from this file's directory (scripts/ -> profile-engine/)
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
GENERATED_DIR = ROOT_DIR / "generated"


def github_headers() -> dict:
    """
    Shared auth headers for any GitHub REST or GraphQL call.

    Unauthenticated REST calls are capped at 60/hour per IP (easy to hit
    in CI, and GraphQL requires auth even for public data). If
    GITHUB_TOKEN is set - GitHub Actions provides one automatically as
    secrets.GITHUB_TOKEN - use it for a 5000/hour limit and GraphQL access.
    """
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "profile-engine"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


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


def random_ascii_art(subdir: str = "ascii/avatars") -> str:
    """
    Pick a random .txt file from an assets subdirectory (default:
    assets/ascii/avatars/) and return its content.

    This is the rotation-pool pattern: any .txt file dropped into that
    folder is automatically eligible next time this runs - no code
    changes needed to add a new avatar art piece. Naming doesn't matter
    (avatar_01.txt, my_cool_art.txt, whatever) since the folder is
    globbed, not hardcoded.
    """
    pool_dir = ASSETS_DIR / subdir
    candidates = sorted(pool_dir.glob("*.txt"))
    if not candidates:
        raise FileNotFoundError(f"No .txt files found in {pool_dir}")

    chosen = random.choice(candidates)
    return chosen.read_text(encoding="utf-8").rstrip("\n")


def ensure_generated_dir() -> None:
    """Make sure generated/ exists before anything tries to write to it."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
