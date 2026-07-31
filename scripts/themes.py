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
        "label_color": "07090F",  # exact background from spec
        "color": "00E7FF",  # exact cyan from spec
    },
}

# Exact colors specified directly - these supersede the earlier
# pixel-sampled approximations, since exact hex values from the person
# building this are strictly more reliable than estimates from a photo.
HUD_COLORS = {
    "header": "#00E7FF",
    "activity": "#24FF9A",
    "stats": "#FF38F8",
    "modules": "#FFC84D",
    "timeline": "#FF4D5A",
    "timeline_end": "#FF4D5A",
    "ribbon_public": "#24FF9A",
    "ribbon_vip": "#FFC84D",
}

# Switched away from an all-pink default per direct feedback - most
# "digitized terminal" references are blue or green, not magenta/pink.
DEFAULT_THEME = "hud"


def get_theme(name: str) -> dict:
    """Look up a theme by name, falling back to DEFAULT_THEME if unknown."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])
