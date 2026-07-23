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
import badges
import effects
import github
import leetcode
import project_cards
import quote_card
import renderer
import svg_terminal
import tech_pills
from utils import (
    GENERATED_DIR,
    build_boot_sequence,
    ensure_generated_dir,
    random_ascii_art,
    random_line,
)

# --- Static profile info -----------------------------------------------
# This will eventually move to a config file (profile.yml / config.json),
# but for Phase 1 it's kept here as plain constants for clarity.
USERNAME = "Eddy Odero"
GITHUB_USERNAME = "Eddy-Odero"  # swap for the real GitHub handle
LEETCODE_USERNAME = "leetcode"  # swap for the real LeetCode handle
TAGLINE = "Full-stack developer | Go, SQLite, vanilla JS | Kisumu, Kenya"
ROLE = "Full-Stack Developer"  # used by the hero card - kept separate from
LOCATION = "Kisumu, Kenya"  # TAGLINE so the card doesn't have to parse a string
STACK = [
    "Go", "JavaScript", "TypeScript", "PHP", "Node.js", "C++",
    "HTML", "CSS", "SQLite", "PostgreSQL", "Docker",
]
TOOLS = ["Git", "Figma", "Blender", "Redis"]
PROJECTS = [
    {
        "name": "SatGate",
        "description": "Lightning Network-powered CAPTCHA replacement for contact forms.",
        "repo_url": f"https://github.com/{GITHUB_USERNAME}/SatGate",
        "preview_url": None,  # set a real URL once hosted, or leave None
    },
    {
        "name": "EDU-FLIX",
        "description": "Netflix-style streaming platform built with Go and SQLite/Turso.",
        "repo_url": f"https://github.com/{GITHUB_USERNAME}/EDU-FLIX",
        "preview_url": None,
    },
    {
        "name": "lem-in colony visualizer",
        "description": "Ant colony pathfinding simulator with a 3D max-flow visualizer.",
        "repo_url": f"https://github.com/{GITHUB_USERNAME}/lem-in",
        "preview_url": None,
    },
    {
        "name": "Maison POS",
        "description": "Point-of-sale system for retail, built with vanilla JS.",
        "repo_url": f"https://github.com/{GITHUB_USERNAME}/Maison-POS",
        "preview_url": None,
    },
]
# NOTE: repo_url values above are guessed from the naming convention -
# double check they match your actual repo names/casing, and fill in
# preview_url wherever a project is actually hosted somewhere.

# How aggressive the CRT effects are: "subtle" (default), "medium", "heavy".
# Override with CRT_LEVEL=medium in the environment to try other looks
# without touching code.
#
# Using `or` instead of os.environ.get(key, default) matters here: the
# workflow passes CRT_LEVEL/THEME from `${{ inputs.crt_level }}`, which
# only has a real value on manual workflow_dispatch runs. On scheduled/
# push-triggered runs, GitHub Actions sets the env var to an EMPTY
# STRING, not unset - and os.environ.get()'s default only kicks in when
# the key is missing entirely, not when it's present-but-empty. That
# left CRT_LEVEL="" on every non-manual run, which apply_crt_effects()
# correctly rejected as an unknown level, which surfaced (confusingly)
# as the avatar step failing, since that's the function that called it.
CRT_LEVEL = os.environ.get("CRT_LEVEL") or "subtle"

# Which shields.io color palette to use for the stat badges: cyberpunk
# (default), crt, hacker, minimal, matrix. Override with THEME=matrix in
# the environment - see scripts/themes.py for the full palette list.
THEME = os.environ.get("THEME") or "cyberpunk"

# "static" (default) picks a random art file from
# assets/ascii/avatars/*.txt each build - a rotation pool, same pattern
# as quotes.txt/statuses.txt. "photo" uses the Phase 2 pipeline
# (avatar.py): fetches the real GitHub avatar and converts it to ASCII,
# which is inherently noisier - a real photo's soft gradients don't map
# cleanly onto a character ramp. The photo pipeline is untouched and
# fully working; this is a content choice, not a deprecation. Override
# with AVATAR_MODE=photo to switch.
AVATAR_MODE = os.environ.get("AVATAR_MODE") or "static"

# Shown if the avatar fetch/render fails for any reason (offline, rate
# limited, bad username) so a build never hard-fails on Phase 2 work.
FALLBACK_AVATAR = "\n".join(
    [
        "      [ avatar unavailable ]",
        "      run: python scripts/avatar.py <github-username>",
    ]
)


def build_avatar_ascii() -> str:
    if AVATAR_MODE == "static":
        try:
            return random_ascii_art()
        except Exception as exc:  # noqa: BLE001 - build must never hard-fail here
            print(f"[avatar] static art load failed, using fallback: {exc}", file=sys.stderr)
            return FALLBACK_AVATAR

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


def _write_svg(markup: str, filename: str) -> str:
    """Write SVG markup to generated/<filename> and return the template-relative path."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    (GENERATED_DIR / filename).write_text(markup, encoding="utf-8")
    return f"generated/{filename}"


def build_terminal_svg(
    avatar_ascii: str, boot_sequence: str, system_message: str, status: str, stats: dict
) -> str:
    """
    Render the terminal window SVG and save it to generated/terminal.svg.
    Returns the path as the template should reference it (relative to
    the repo root, since that's where README.md lives).
    """
    boot_text = f"{boot_sequence}\n{system_message}"
    svg_markup = svg_terminal.render_terminal_svg(
        avatar_ascii=avatar_ascii,
        boot_sequence=boot_text,
        status=status,
        username=USERNAME,
        stats={**stats, "role": ROLE, "location": LOCATION},
        theme_name=THEME,
    )
    return _write_svg(svg_markup, "terminal.svg")


def build_context() -> dict:
    """Assemble everything the template needs into a single context dict."""
    github_stats = build_github_stats()
    leetcode_stats = build_leetcode_stats()
    combined_stats = {**github_stats, **leetcode_stats}

    avatar_ascii = build_avatar_ascii()
    system_message = effects.random_system_message()
    status = random_line("statuses.txt")
    boot_sequence = build_boot_sequence("boot.txt")
    quote = random_line("quotes.txt")

    return {
        "username": USERNAME,
        "tagline": TAGLINE,
        "stack": STACK,
        "avatar_ascii": avatar_ascii,
        "cursor": effects.random_cursor(),
        "system_message": system_message,
        "quote": quote,
        "status": status,
        "boot_sequence": boot_sequence,
        "terminal_svg_path": build_terminal_svg(
            avatar_ascii, boot_sequence, system_message, status, combined_stats
        ),
        "project_cards_svg_path": _write_svg(
            project_cards.render_project_cards_svg(PROJECTS, THEME), "project_cards.svg"
        ),
        "badge_preview_path": _write_svg(
            project_cards.render_link_badge_svg("preview", THEME), "badge_preview.svg"
        ),
        "badge_code_path": _write_svg(
            project_cards.render_link_badge_svg("code", THEME), "badge_code.svg"
        ),
        "badge_disabled_path": _write_svg(
            project_cards.render_link_badge_svg("preview", THEME, disabled=True), "badge_disabled.svg"
        ),
        "projects": PROJECTS,
        "tech_stack_svg_path": _write_svg(
            tech_pills.render_tech_stack_svg(STACK, THEME), "tech_stack.svg"
        ),
        "tools_svg_path": _write_svg(
            tech_pills.render_tech_stack_svg(TOOLS, THEME), "tools.svg"
        ),
        "quote_svg_path": _write_svg(quote_card.render_quote_svg(quote, THEME), "quote.svg"),
        "build_time": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "stat_badges": badges.build_stat_badges(combined_stats, THEME),
        "theme": THEME,
        **combined_stats,
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
