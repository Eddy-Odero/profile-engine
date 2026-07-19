"""
badges.py  (Phase 8)

Turns stat values into shields.io "static badge" markdown images, colored
with whichever theme is active. This is the actual color/visual-styling
layer - everything else in the project (avatar ASCII, CRT effects, boot
sequence) is plain text and can't have color in a GitHub-rendered README.

Shields.io static badge URL shape:
    https://img.shields.io/badge/<LABEL>-<MESSAGE>-<COLOR>?style=...&labelColor=...

Both LABEL and MESSAGE need shields.io's own escaping (literal '-' and '_'
have special meaning in that path segment) before normal URL-encoding.
"""

from __future__ import annotations

from urllib.parse import quote

from themes import DEFAULT_THEME, get_theme


def _escape_segment(text: str) -> str:
    """
    Shields.io reserves '-' and '_' as separators within a badge path
    segment, so a literal '-' must become '--' and '_' must become '__'
    before the segment is placed between the URL's own '-' separators.
    Spaces become '_' (shields.io renders that back as a space).
    """
    text = str(text)
    text = text.replace("-", "--").replace("_", "__")
    text = text.replace(" ", "_")
    return quote(text, safe="_")


def badge_markdown(label: str, message: str, theme_name: str = DEFAULT_THEME) -> str:
    """Build one markdown image badge string for `label: message`, theme-colored."""
    theme = get_theme(theme_name)
    url = (
        f"https://img.shields.io/badge/{_escape_segment(label)}-{_escape_segment(message)}"
        f"-{theme['color']}"
        f"?style={theme['style']}&labelColor={theme['label_color']}"
    )
    alt = f"{label}: {message}"
    return f"![{alt}]({url})"


def build_stat_badges(stats: dict, theme_name: str = DEFAULT_THEME) -> list[str]:
    """
    Build the curated row of badges shown near the top of the README.
    `stats` is expected to be (a subset of) the render context - only the
    keys used below need to be present.
    """
    badges = [
        badge_markdown("Repos", stats.get("repo_count", "?"), theme_name),
        badge_markdown("Stars", stats.get("stars", "?"), theme_name),
        badge_markdown("Followers", stats.get("followers", "?"), theme_name),
    ]

    solved = stats.get("solved")
    if solved:
        badges.append(badge_markdown("LC Solved", solved.get("total", "?"), theme_name))

    rating = stats.get("rating")
    if rating is not None:
        badges.append(badge_markdown("LC Rating", rating, theme_name))

    return badges
