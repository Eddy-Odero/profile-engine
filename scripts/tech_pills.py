"""
tech_pills.py

Tech stack, rendered as small IC-chip-style badges - shields.io's size
and layout logic (compact, auto-width, single-row-first then wrap), but
a deliberately different SHAPE language. shields.io badges are fully
rounded pills; every profile README that uses them looks the same. This
draws each tech as a small rectangular chip with pin ticks on the left/
right edges and a notch at the top-left corner, like a real integrated
circuit component - it reads as "ours" at a glance rather than "another
shields.io row", while staying just as compact and scannable.

Each chip is colored per-language/tool (loosely inspired by each
language's own brand/ecosystem color - Go's cyan, TypeScript's blue,
Redis's red, etc.) rather than one flat theme accent repeated for every
chip - a single color for the whole row read as monochrome/flat; this
reads as a real, varied tech stack instead. Unknown entries fall back
to the active theme's accent color.

Usage:
    from tech_pills import render_tech_stack_svg
    svg_markup = render_tech_stack_svg(["Go", "JavaScript", "Docker"], theme_name)
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

FONT_SIZE = 12
CHAR_WIDTH = FONT_SIZE * 0.62
CHIP_HEIGHT = 26
CHIP_PADDING_X = 12
CHIP_GAP = 10
ROW_GAP = 12
PIN_LENGTH = 5
PIN_WIDTH = 2
NOTCH_RADIUS = 3
MAX_ROW_WIDTH = 760  # wrap to a new row past this, same idea as project_cards' grid

# Loosely brand-inspired per-tech colors, not exact trademarked hex
# values - close enough to read as "that language's color" at a glance
# without claiming to reproduce anyone's official brand guidelines.
TECH_COLORS: dict[str, str] = {
    "go": "00ADD8",
    "javascript": "F7DF1E",
    "typescript": "3178C6",
    "php": "8892BF",
    "node.js": "68A063",
    "nodejs": "68A063",
    "c++": "00599C",
    "html": "E34C26",
    "css": "2965F1",
    "sqlite": "4C8BBE",
    "postgresql": "336791",
    "docker": "2496ED",
    "python": "3776AB",
    "git": "F05032",
    "figma": "A259FF",
    "blender": "F5792A",
    "redis": "DC382D",
}


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _chip_width(label: str) -> float:
    return len(label) * CHAR_WIDTH + CHIP_PADDING_X * 2


def _chip_color(label: str, fallback: str) -> str:
    """Look up this tech's color by name (case-insensitive); fall back to the theme accent."""
    hex_color = TECH_COLORS.get(label.lower())
    return f"#{hex_color}" if hex_color else fallback


def _pins(x: float, y: float, width: float, color: str) -> str:
    """Small tick marks on the left and right edges, like IC chip legs."""
    mid_y = y + CHIP_HEIGHT / 2
    return (
        f'<line x1="{x - PIN_LENGTH}" y1="{mid_y:.1f}" x2="{x}" y2="{mid_y:.1f}" '
        f'stroke="{color}" stroke-width="{PIN_WIDTH}"/>'
        f'<line x1="{x + width}" y1="{mid_y:.1f}" x2="{x + width + PIN_LENGTH}" y2="{mid_y:.1f}" '
        f'stroke="{color}" stroke-width="{PIN_WIDTH}"/>'
    )


def _chip(x: float, y: float, label: str, color: str, dark: str) -> str:
    width = _chip_width(label)
    text_x = x + width / 2
    text_y = y + CHIP_HEIGHT / 2 + FONT_SIZE * 0.35

    return f"""
  <g>
    {_pins(x, y, width, color)}
    <rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{CHIP_HEIGHT}" rx="3" \
fill="{dark}" stroke="{color}" stroke-width="1.3"/>
    <circle cx="{x + NOTCH_RADIUS + 3:.1f}" cy="{y + NOTCH_RADIUS + 3:.1f}" r="{NOTCH_RADIUS}" \
fill="{color}" fill-opacity="0.55"/>
    <text x="{text_x:.1f}" y="{text_y:.1f}" font-family="Consolas, Menlo, monospace" \
font-size="{FONT_SIZE}" font-weight="700" fill="{color}" text-anchor="middle">{_esc(label)}</text>
  </g>"""


def render_tech_stack_svg(stack: list[str], theme_name: str = DEFAULT_THEME) -> str:
    """Build an SVG of chip-styled badges, one per tech, wrapping to new rows as needed."""
    theme = get_theme(theme_name)
    fallback_accent = f"#{theme['color']}"
    dark = f"#{theme['label_color']}"

    if not stack:
        stack = ["more coming soon"]

    rows: list[list[str]] = [[]]
    row_widths = [0.0]
    for tech in stack:
        w = _chip_width(tech) + PIN_LENGTH * 2
        projected = row_widths[-1] + (CHIP_GAP if rows[-1] else 0) + w
        if projected > MAX_ROW_WIDTH and rows[-1]:
            rows.append([])
            row_widths.append(0.0)
        rows[-1].append(tech)
        row_widths[-1] = row_widths[-1] + (CHIP_GAP if len(rows[-1]) > 1 else 0) + w

    width = int(max(row_widths)) + PIN_LENGTH * 2
    height = int(len(rows) * CHIP_HEIGHT + (len(rows) - 1) * ROW_GAP)

    chips = []
    y = 0.0
    for row in rows:
        x = float(PIN_LENGTH)
        for tech in row:
            chips.append(_chip(x, y, tech, _chip_color(tech, fallback_accent), dark))
            x += _chip_width(tech) + PIN_LENGTH * 2 + CHIP_GAP
        y += CHIP_HEIGHT + ROW_GAP

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tech stack">
  {''.join(chips)}
</svg>"""
