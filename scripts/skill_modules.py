"""
skill_modules.py

"System Modules" - a grid of skill badges styled like a sci-fi HUD
component: a circular icon badge, corner-bracket frame decorations
(like a targeting reticle/scanner UI), the skill name, and a
proficiency level. Modeled directly on a design reference provided.

Doesn't try to reproduce real brand logos (trademark/copyright risk,
and most are complex multi-color marks that don't reduce well to a
tiny circle) - each badge shows the skill's color (reusing
tech_pills.TECH_COLORS for consistency with the tech stack chips
elsewhere) and a short 1-3 letter monogram instead.

Usage:
    from skill_modules import render_skill_modules_svg
    svg_markup = render_skill_modules_svg(
        [("Go", "Advanced"), ("JavaScript", "Expert")], theme_name)
"""

from __future__ import annotations

import html

from hud_grid import glow_filter, grid_background, scanline_overlay
from tech_pills import TECH_COLORS
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

CARD_WIDTH = 170
CARD_HEIGHT = 150
CARD_GAP = 14
CARDS_PER_ROW = 4
BADGE_RADIUS = 26
BRACKET_LEN = 16
BRACKET_INSET = 6

CARD_BG = "07090F"  # exact background from spec, subtle navy tint
CARD_BORDER = "1c2a3a"
MUTED = "6b7a8c"

# Real recognizable emoji per skill - standard Unicode characters, not
# custom trademarked logo art, but immediately recognizable per language/
# tool (the snake for Python, the whale for Docker, etc.)
MONOGRAMS: dict[str, str] = {
    "go": "🐹", "javascript": "🟨", "typescript": "🔷", "php": "🟣",
    "node.js": "💚", "nodejs": "💚", "c++": "⚙️", "html": "🌐", "css": "🎨",
    "html/css": "🌐", "c": "🅲",
    "sqlite": "🗄️", "postgresql": "🐘", "docker": "🐳", "python": "🐍",
    "git": "🔧", "figma": "🎯", "blender": "🧊", "redis": "🔴",
    "rust": "🦀", "kubernetes": "☸️", "aws": "☁️",
}


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _monogram(label: str) -> str:
    return MONOGRAMS.get(label.lower(), label[:2].upper())


def _skill_color(label: str, fallback: str) -> str:
    hex_color = TECH_COLORS.get(label.lower())
    return f"#{hex_color}" if hex_color else fallback


def _corner_brackets(x: float, y: float, accent: str) -> str:
    """Four L-shaped corner marks, like a HUD scanner/targeting frame."""
    corners = [
        (x + BRACKET_INSET, y + BRACKET_INSET, 1, 1),  # top-left
        (x + CARD_WIDTH - BRACKET_INSET, y + BRACKET_INSET, -1, 1),  # top-right
        (x + BRACKET_INSET, y + CARD_HEIGHT - BRACKET_INSET, 1, -1),  # bottom-left
        (x + CARD_WIDTH - BRACKET_INSET, y + CARD_HEIGHT - BRACKET_INSET, -1, -1),  # bottom-right
    ]
    marks = []
    for cx, cy, dx, dy in corners:
        marks.append(
            f'<path d="M{cx} {cy + dy * BRACKET_LEN} L{cx} {cy} L{cx + dx * BRACKET_LEN} {cy}" '
            f'fill="none" stroke="{accent}" stroke-width="2" filter="url(#hudglow)"/>'
        )
    return "".join(marks)


def _badge(x: float, y: float, skill: str, level: str, accent: str, bracket_color: str) -> str:
    color = _skill_color(skill, accent)
    badge_cx = x + CARD_WIDTH / 2
    badge_cy = y + 44

    return f"""
  <g>
    <rect x="{x}" y="{y}" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" fill="#{CARD_BG}" fill-opacity="0.3" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
    {_corner_brackets(x, y, bracket_color)}
    <circle cx="{badge_cx}" cy="{badge_cy}" r="{BADGE_RADIUS}" fill="{color}" fill-opacity="0.12" \
stroke="{color}" stroke-width="2"/>
    <text x="{badge_cx}" y="{badge_cy + 8}" font-size="22" \
text-anchor="middle">{_esc(_monogram(skill))}</text>
    <text x="{badge_cx}" y="{y + 100}" font-family="Consolas, Menlo, monospace" font-size="12" \
font-weight="700" fill="white" text-anchor="middle" letter-spacing="0.5">{_esc(skill.upper())}</text>
    <text x="{badge_cx}" y="{y + 118}" font-family="Consolas, Menlo, monospace" font-size="9" \
fill="#{MUTED}" text-anchor="middle" letter-spacing="1">{_esc(level.upper())}</text>
  </g>"""


def render_skill_modules_svg(
    skills: list[tuple[str, str]], theme_name: str = DEFAULT_THEME
) -> str:
    """
    Build the SVG for the skill modules grid. `skills` is a list of
    (name, proficiency_level) tuples. Wraps into rows of CARDS_PER_ROW.

    Corner brackets use the exact reference gold (#FFB917), sampled
    directly from the design image, rather than the active theme's
    accent - this section's bracket color doesn't change with theme,
    matching the reference exactly.
    """
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"
    bracket_color = HUD_COLORS["modules"]

    if not skills:
        skills = [("more skills coming soon", "")]

    rows = [skills[i : i + CARDS_PER_ROW] for i in range(0, len(skills), CARDS_PER_ROW)]
    cols_in_widest_row = max(len(row) for row in rows)

    width = cols_in_widest_row * CARD_WIDTH + (cols_in_widest_row - 1) * CARD_GAP
    height = len(rows) * CARD_HEIGHT + (len(rows) - 1) * CARD_GAP

    badges = []
    for row_i, row in enumerate(rows):
        for col_i, (skill, level) in enumerate(row):
            x = col_i * (CARD_WIDTH + CARD_GAP)
            y = row_i * (CARD_HEIGHT + CARD_GAP)
            badges.append(_badge(x, y, skill, level, accent, bracket_color))

    grid_defs, grid_rect = grid_background(width, height, accent)
    scan_defs, scan_rect = scanline_overlay(width, height)

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="System modules">
  <defs>{grid_defs}{glow_filter()}{scan_defs}</defs>
  <rect width="{width}" height="{height}" fill="#{CARD_BG}"/>
  {grid_rect}
  {''.join(badges)}
  {scan_rect}
</svg>"""
