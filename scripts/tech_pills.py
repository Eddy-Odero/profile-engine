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


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _chip_width(label: str) -> float:
    return len(label) * CHAR_WIDTH + CHIP_PADDING_X * 2


def _pins(x: float, y: float, width: float, accent: str) -> str:
    """Small tick marks on the left and right edges, like IC chip legs."""
    mid_y = y + CHIP_HEIGHT / 2
    return (
        f'<line x1="{x - PIN_LENGTH}" y1="{mid_y:.1f}" x2="{x}" y2="{mid_y:.1f}" '
        f'stroke="{accent}" stroke-width="{PIN_WIDTH}"/>'
        f'<line x1="{x + width}" y1="{mid_y:.1f}" x2="{x + width + PIN_LENGTH}" y2="{mid_y:.1f}" '
        f'stroke="{accent}" stroke-width="{PIN_WIDTH}"/>'
    )


def _chip(x: float, y: float, label: str, accent: str, dark: str) -> str:
    width = _chip_width(label)
    text_x = x + width / 2
    text_y = y + CHIP_HEIGHT / 2 + FONT_SIZE * 0.35

    return f"""
  <g>
    {_pins(x, y, width, accent)}
    <rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{CHIP_HEIGHT}" rx="3" \
fill="{dark}" stroke="{accent}" stroke-width="1.3"/>
    <circle cx="{x + NOTCH_RADIUS + 3:.1f}" cy="{y + NOTCH_RADIUS + 3:.1f}" r="{NOTCH_RADIUS}" \
fill="{accent}" fill-opacity="0.55"/>
    <text x="{text_x:.1f}" y="{text_y:.1f}" font-family="Consolas, Menlo, monospace" \
font-size="{FONT_SIZE}" font-weight="700" fill="{accent}" text-anchor="middle">{_esc(label)}</text>
  </g>"""


def render_tech_stack_svg(stack: list[str], theme_name: str = DEFAULT_THEME) -> str:
    """Build an SVG of chip-styled badges, one per tech, wrapping to new rows as needed."""
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"
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
            chips.append(_chip(x, y, tech, accent, dark))
            x += _chip_width(tech) + PIN_LENGTH * 2 + CHIP_GAP
        y += CHIP_HEIGHT + ROW_GAP

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tech stack">
  {''.join(chips)}
</svg>"""
