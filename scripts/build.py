"""
build.py

Phase 1 entry point.

Responsibilities right now:
    1. Assemble the render context (static/mock data for anything that
       later phases will fetch live: GitHub stats, LeetCode stats, avatar).
    2. Hand that context to renderer.py to produce README.md.

Run from the project root:
    python scripts/build.py

Later phases plug in by REPLACING the mock values below with real calls:
    - avatar.py   -> generates generated/avatar.txt (Phase 2)
    - github.py   -> fetches live repo/star/follower counts (Phase 4)
    - leetcode.py -> fetches live LeetCode stats (Phase 5)
None of those change renderer.py or README.template.md - they only
change what goes into `context`.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys

import avatar
import effects
import github
import leetcode
import renderer
from utils import GENERATED_DIR, build_boot_sequence, ensure_generated_dir, random_line

# --- Static profile info -----------------------------------------------
# This will eventually move to a config file (profile.yml / config.json),
# but for Phase 1 it's kept here as plain constants for clarity.
USERNAME = "Eddy Odero"
GITHUB_USERNAME = "octocat"  # swap for the real GitHub handle
LEETCODE_USERNAME = "leetcode"  # swap for the real LeetCode handle
TAGLINE = "Full-stack developer | Go, SQLite, vanilla JS | Kisumu, Kenya"
STACK = ["Go", "JavaScript", "SQLite", "PostgreSQL", "Docker", "Python"]
PROJECTS = ["SatGate", "EDU-FLIX", "lem-in colony visualizer", "Maison POS"]

# How aggressive the CRT effects are: "subtle" (default), "medium", "heavy".
# Override with CRT_LEVEL=medium in the environment to try other looks
# without touching code.
CRT_LEVEL = os.environ.get("CRT_LEVEL", "subtle")

# Shown if the avatar fetch/render fails for any reason (offline, rate
# limited, bad username) so a build never hard-fails on Phase 2 work.
FALLBACK_AVATAR = "\n".join(
    [
        "      [ avatar unavailable ]",
        "      run: python scripts/avatar.py <github-username>",
    ]
)


def build_avatar_ascii() -> str:
    try:
        ascii_art = avatar.generate_avatar_ascii(GITHUB_USERNAME, cols=60)
        return effects.apply_crt_effects(ascii_art, level=CRT_LEVEL)
    except Exception as exc:  # noqa: BLE001 - build must never hard-fail here
        print(f"[avatar] fetch/render failed, using fallback: {exc}", file=sys.stderr)
        return FALLBACK_AVATAR

# --- Fallback data if the live GitHub fetch fails -----------------------
# Same shape as github.fetch_github_stats() returns, so build_context()
# doesn't need to care which one it got.
MOCK_GITHUB_STATS = {
    "repo_count": 24,
    "stars": 37,
    "followers": 12,
    "top_languages": ["Go", "JavaScript", "Python"],
    "recent_activity": ["pushed to profile-engine"],
    "pinned_repos": ["SatGate", "EDU-FLIX", "lem-in"],
    "contributions": None,
}


def build_github_stats() -> dict:
    try:
        return github.fetch_github_stats(GITHUB_USERNAME)
    except Exception as exc:  # noqa: BLE001 - build must never hard-fail here
        print(f"[github] live fetch failed, using mock stats: {exc}", file=sys.stderr)
        return MOCK_GITHUB_STATS


# --- Fallback data if the live LeetCode fetch fails ----------------------
# Same shape as leetcode.fetch_leetcode_stats() returns.
MOCK_LEETCODE_STATS = {
    "solved": {"total": 120, "easy": 55, "medium": 50, "hard": 15},
    "rating": None,
    "ranking": None,
    "top_percentage": None,
    "contests_attended": None,
    "badges": [],
    "recent_submissions": [],
}


def build_leetcode_stats() -> dict:
    try:
        return leetcode.fetch_leetcode_stats(LEETCODE_USERNAME)
    except Exception as exc:  # noqa: BLE001 - build must never hard-fail here
        print(f"[leetcode] live fetch failed, using mock stats: {exc}", file=sys.stderr)
        return MOCK_LEETCODE_STATS


def build_context() -> dict:
    """Assemble everything the template needs into a single context dict."""
    return {
        "username": USERNAME,
        "tagline": TAGLINE,
        "stack": STACK,
        "projects": PROJECTS,
        "avatar_ascii": build_avatar_ascii(),
        "cursor": effects.random_cursor(),
        "system_message": effects.random_system_message(),
        "quote": random_line("quotes.txt"),
        "status": random_line("statuses.txt"),
        "boot_sequence": build_boot_sequence("boot.txt"),
        "build_time": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        **build_github_stats(),
        **build_leetcode_stats(),
    }


def write_stats_cache(context: dict) -> None:
    """
    Dump the non-template-formatting parts of the context to
    generated/stats.json - useful for debugging and for future phases
    that may want to read the last-known values without re-fetching.
    """
    cache = {
        k: v for k, v in context.items() if k not in ("boot_sequence", "avatar_ascii")
    }
    (GENERATED_DIR / "stats.json").write_text(
        json.dumps(cache, indent=2), encoding="utf-8"
    )


def main() -> None:
    ensure_generated_dir()
    context = build_context()
    rendered = renderer.render(context)
    output_path = renderer.write_readme(rendered)
    write_stats_cache(context)
    print(f"README generated -> {output_path}")


if __name__ == "__main__":
    main()
