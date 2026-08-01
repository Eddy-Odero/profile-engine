"""
fragmented_data.py

"Fragmented Data" - a real, from-scratch rebuild distinct from the old
project-card look, matching the reference exactly: wide LANDSCAPE
cards (not portrait), with the top-right AND bottom-left corners
chamfered (cut at a diagonal, giving a hexagonal/HUD-panel silhouette
rather than a plain rounded rect), a PUBLIC/VIP ribbon tucked into the
cut top-right notch, icon+name on one line, a 2-line description, and
a bottom stats row (language dot, stars, forks). Cards are meant to
sit close together (small gap) in the template's grid, not spaced far
apart.

This reuses the icon glyph / star / fork primitives from
project_cards.py (those don't depend on card width), but everything
that DOES depend on the card's shape (the outline, the ribbon
position, the stats row) is implemented fresh here rather than
delegating to project_cards.render_single_project_card_svg, since that
function assumes a narrower portrait card.

Usage:
    from fragmented_data import render_fragment_card_svg
    svg_markup = render_fragment_card_svg(project, theme_name)
"""

from __future__ import annotations

import html

from project_cards import _fork_icon, _project_icon, _star_icon
from tech_pills import TECH_COLORS
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

WIDTH = 380
HEIGHT = 140
CHAMFER = 20  # size of the cut corner, top-right and bottom-left

BG = "07090F"
CARD_BORDER = "24384a"
DESC_COLOR = "8f97a8"
STAT_COLOR = "7d7d88"
TITLE_COLOR = "e8e6f0"

RIBBON_COLORS = {"public": HUD_COLORS["ribbon_public"], "vip": HUD_COLORS["ribbon_vip"]}


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _wrap(text: str, max_chars: int = 46) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:2] or [""]


def _chamfered_outline(width: float, height: float, cut: float) -> str:
    """
    The card's own outline: a rectangle with its top-right and
    bottom-left corners sliced off at 45 degrees - an octagon-ish HUD
    panel silhouette rather than a plain (rounded) rectangle.
    """
    points = [
        (0, 0),
        (width - cut, 0),
        (width, cut),
        (width, height),
        (cut, height),
        (0, height - cut),
    ]
    pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return pts_str


def _ribbon(visibility: str) -> str:
    """PUBLIC/VIP ribbon tucked into the chamfered top-right notch."""
    if not visibility:
        return ""
    color = RIBBON_COLORS.get(visibility.lower(), RIBBON_COLORS["public"])
    label = visibility.upper()
    return f"""
  <g>
    <polygon points="{WIDTH-CHAMFER-46},10 {WIDTH-14},10 {WIDTH-14},{CHAMFER-2} {WIDTH-CHAMFER-24},{CHAMFER-2}" fill="{color}"/>
    <text x="{WIDTH-CHAMFER-35}" y="{CHAMFER-9}" font-family="Consolas, Menlo, monospace" font-size="8.5" \
font-weight="700" fill="#0a0a0d" text-anchor="middle">{_esc(label)}</text>
  </g>"""


def _stats_row(y: float, language: str, stars: int, forks: int, accent: str) -> str:
    lang_hex = TECH_COLORS.get((language or "").lower())
    lang_color = f"#{lang_hex}" if lang_hex else accent

    parts = []
    lx = 24
    if language:
        parts.append(f'<circle cx="{lx}" cy="{y-3}" r="4" fill="{lang_color}"/>')
        parts.append(
            f'<text x="{lx+10}" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
            f'font-size="10" fill="#{STAT_COLOR}">{_esc(language)}</text>'
        )

    star_x = WIDTH - 88
    parts.append(_star_icon(star_x, y - 3, f"#{STAT_COLOR}"))
    parts.append(
        f'<text x="{star_x+9}" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="10" fill="#{STAT_COLOR}">{stars}</text>'
    )

    fork_x = WIDTH - 48
    parts.append(_fork_icon(fork_x, y - 3, f"#{STAT_COLOR}"))
    parts.append(
        f'<text x="{fork_x+11}" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="10" fill="#{STAT_COLOR}">{forks}</text>'
    )

    return "".join(parts)


def render_fragment_card_svg(project: dict, theme_name: str = DEFAULT_THEME) -> str:
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"

    name = project.get("name", "")
    description = project.get("description", "")
    icon_key = project.get("icon", "")
    visibility = project.get("visibility", "public")
    language = project.get("language", "")
    stars = project.get("stars", 0)
    forks = project.get("forks", 0)

    icon_cx, icon_cy = 34, 38
    name_x = icon_cx + 30
    desc_lines = _wrap(description)

    outline_pts = _chamfered_outline(WIDTH, HEIGHT, CHAMFER)

    name_svg = (
        f'<text x="{name_x}" y="{icon_cy + 5}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="16" font-weight="700" fill="#{TITLE_COLOR}">{_esc(name)}</text>'
    )

    desc_y0 = icon_cy + 32
    desc_svg = "".join(
        f'<text x="24" y="{desc_y0 + i*17}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="11" fill="#{DESC_COLOR}">{_esc(line)}</text>'
        for i, line in enumerate(desc_lines)
    )

    stats_y = HEIGHT - 20

    return f"""<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(name)}">
  <polygon points="{outline_pts}" fill="#{BG}" fill-opacity="0.94" stroke="#{CARD_BORDER}" stroke-width="1"/>
  {_project_icon(icon_cx, icon_cy, icon_key, accent)}
  {name_svg}
  {desc_svg}
  {_stats_row(stats_y, language, stars, forks, accent)}
  {_ribbon(visibility)}
</svg>"""
