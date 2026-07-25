"""
themes.py  (Phase 8)

Real color in a GitHub README can't come from the ASCII/code-block text
(GitHub renders those as flat monospace, no color) - it has to come from
something GitHub renders specially. Shields.io badges are the simplest,
most reliable way to get that: they're just markdown images, so they
always render correctly, need no hosting/build step of their own, and
GitHub caches them fine.

Each theme is a color palette applied to the stat badges in the README
(repos, stars, followers, LeetCode solved, etc.) - not a different piece
of content, just a different look for the same data.

A full plugin system (arbitrary user-defined themes) is a stretch goal;
this is a fixed set of 5 hand-picked palettes, selected via THEME env var
in build.py, same pattern as CRT_LEVEL.
"""

from __future__ import annotations

# Shields.io accepts hex colors without '#', OR a small set of named
# colors (brightgreen, blue, etc.) - hex works for everything below and
# keeps every theme's exact shade explicit rather than shields.io's
# built-in interpretation of a name.
THEMES: dict[str, dict] = {
    "cyberpunk": {
        "label": "Cyberpunk",
        "style": "for-the-badge",
        "label_color": "0d0221",  # near-black purple
        "color": "ff2079",  # hot pink
    },
    "crt": {
        "label": "CRT",
        "style": "for-the-badge",
        "label_color": "1a1300",  # near-black amber
        "color": "ffb000",  # phosphor amber
    },
    "hacker": {
        "label": "Hacker",
        "style": "flat-square",
        "label_color": "000000",
        "color": "00ff41",  # classic terminal green
    },
    "minimal": {
        "label": "Minimal",
        "style": "flat",
        "label_color": "343a40",
        "color": "adb5bd",  # muted gray
    },
    "matrix": {
        "label": "Matrix",
        "style": "flat-square",
        "label_color": "0d0d0d",
        "color": "008f11",  # deeper green than 'hacker', more muted
    },
    "cyan": {
        "label": "Cyan",
        "style": "flat-square",
        "label_color": "001014",  # near-black teal
        "color": "00e5ff",  # classic light-blue CRT phosphor - the most common
        # "digitized terminal" color alongside green, per direct feedback that
        # most real terminal aesthetics lean blue/green, not pink/purple
    },
    "ocean": {
        "label": "Ocean",
        "style": "for-the-badge",
        "label_color": "071a2b",  # near-black navy
        "color": "3fa9f5",  # softer mid-blue, less neon than 'cyan'
    },
    "hud": {
        "label": "HUD",
        "style": "flat-square",
        "label_color": "0a0c14",  # near-black blue, sampled directly from the reference image
        "color": "14F7FF",  # header/divider cyan, sampled directly from the reference image
        # Other section-specific accents (activity green #0BFF8E, stats
        # magenta #FF00FF, modules gold #FFB917, timeline red #FB333D,
        # ribbon green #0BFF9F / gold #FFEA54) live in the individual
        # section modules that use them (dimensional_stats.py,
        # skill_modules.py, project_cards.py) rather than here, since
        # this design uses a different accent per section, not one
        # color reused everywhere like the other themes.
    },
}

# Exact-match reference design accents - sampled directly from pixel
# data in the provided design image, not estimated. Each section in
# this design has its own accent rather than reusing one theme color.
HUD_COLORS = {
    "header": "#14F7FF",
    "activity": "#0BFF8E",
    "stats": "#FF00FF",
    "modules": "#FFB917",
    "timeline": "#FB333D",
    "timeline_end": "#FF00A6",
    "ribbon_public": "#0BFF9F",
    "ribbon_vip": "#FFEA54",
}

# Switched away from an all-pink default per direct feedback - most
# "digitized terminal" references are blue or green, not magenta/pink.
DEFAULT_THEME = "hud"


def get_theme(name: str) -> dict:
    """Look up a theme by name, falling back to DEFAULT_THEME if unknown."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])
