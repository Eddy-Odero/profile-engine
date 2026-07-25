"""
dimensional_stats.py

"Dimensional Stats" - 4 blue-accented stat cards plus a small
isometric cube graphic, matching the reference design.

The reference's cube appears to imply rotation/3D. A truly rotating 3D
object isn't possible here for the same reason nothing else in this
project can be truly interactive: this renders as a static image
embedded via markdown, and GitHub strips all animation/interactivity
from SVGs loaded that way (same constraint documented in
project_cards.py). This draws a flat ISOMETRIC illusion instead - three
visible faces of a cube with different shading to imply depth, which is
the standard static-art technique for suggesting 3D without needing
actual 3D rendering or animation.

Usage:
    from dimensional_stats import render_dimensional_stats_svg
    svg_markup = render_dimensional_stats_svg(stats, cube_label_lines, theme_name)
"""

from __future__ import annotations

import html

from hud_grid import grid_background
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

CARD_WIDTH = 280
CARD_HEIGHT = 100
CARD_GAP = 16
CARD_BG = "0c0a14"
CARD_BORDER = "241c33"
LABEL_COLOR = "8a7fa8"

CUBE_SIZE = 90
CUBE_BOX_WIDTH = 220
CUBE_BOX_HEIGHT = 224


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _stat_card(x: float, y: float, label: str, value, accent: str) -> str:
    value = str(value)
    bar_width = min(len(value) * 14 + 20, CARD_WIDTH - 40)
    return f"""
  <g transform="translate({x},{y})">
    <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" fill="#{CARD_BG}" fill-opacity="0.9" stroke="#{CARD_BORDER}" stroke-width="1"/>
    <rect x="0" y="0" width="4" height="{CARD_HEIGHT}" fill="{accent}"/>
    <text x="20" y="28" font-family="Consolas, Menlo, monospace" font-size="10" \
fill="#{LABEL_COLOR}" letter-spacing="1">{_esc(label.upper())}</text>
    <text x="20" y="64" font-family="Consolas, Menlo, monospace" font-size="30" \
font-weight="700" fill="{accent}">{_esc(value)}</text>
    <line x1="20" y1="80" x2="{20 + bar_width}" y2="80" stroke="{accent}" stroke-width="2"/>
  </g>"""


def _isometric_cube(cx: float, cy: float, size: float, accent: str, label_lines: list[str]) -> str:
    """
    Three visible faces (top, left, right) of a cube in isometric
    projection, each a different opacity of the same accent color to
    imply depth/lighting - the standard flat-art trick for a "3D" look.
    """
    h = size * 0.55  # vertical squash for the isometric angle

    top = [
        (cx, cy - h), (cx + size / 2, cy - h / 2),
        (cx, cy), (cx - size / 2, cy - h / 2),
    ]
    left = [
        (cx - size / 2, cy - h / 2), (cx, cy),
        (cx, cy + h), (cx - size / 2, cy + h / 2),
    ]
    right = [
        (cx + size / 2, cy - h / 2), (cx, cy),
        (cx, cy + h), (cx + size / 2, cy + h / 2),
    ]

    def poly(pts, opacity):
        pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        return (
            f'<polygon points="{pts_str}" fill="{accent}" fill-opacity="{opacity}" '
            f'stroke="{accent}" stroke-width="1"/>'
        )

    label_svg = "".join(
        f'<text x="{cx:.1f}" y="{cy + h/2 - 8 + i*13:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="10" fill="white" text-anchor="middle">{_esc(line)}</text>'
        for i, line in enumerate(label_lines)
    )

    return f"""
  <g>
    {poly(top, 0.35)}
    {poly(left, 0.20)}
    {poly(right, 0.12)}
    {label_svg}
  </g>"""


def render_dimensional_stats_svg(
    stats: list[tuple[str, str]],
    cube_label_lines: list[str],
    theme_name: str = DEFAULT_THEME,
) -> str:
    """
    Build the SVG: an isometric cube on the left, a 2x2 grid of stat
    cards on the right. `stats` is a list of up to 4 (label, value)
    tuples. `cube_label_lines` are 1-3 short lines of text shown inside
    the cube (matching the reference's small in-cube stat readout).
    """
    accent = HUD_COLORS["stats"]

    cube_area_w = CUBE_BOX_WIDTH
    stats_cols = 2
    stats_rows = (len(stats) + 1) // 2
    stats_area_w = stats_cols * CARD_WIDTH + (stats_cols - 1) * CARD_GAP
    stats_area_h = stats_rows * CARD_HEIGHT + (stats_rows - 1) * CARD_GAP

    gap_between = 30
    width = cube_area_w + gap_between + stats_area_w
    height = max(CUBE_BOX_HEIGHT, stats_area_h)

    cube_cx = cube_area_w / 2
    cube_cy = height / 2
    cube_svg = _isometric_cube(cube_cx, cube_cy, CUBE_SIZE, accent, cube_label_lines)

    cards = []
    stats_x0 = cube_area_w + gap_between
    y_offset = (height - stats_area_h) / 2
    for i, (label, value) in enumerate(stats[:4]):
        col = i % 2
        row = i // 2
        x = stats_x0 + col * (CARD_WIDTH + CARD_GAP)
        y = y_offset + row * (CARD_HEIGHT + CARD_GAP)
        cards.append(_stat_card(x, y, label, value, accent))

    grid_defs, grid_rect = grid_background(width, height, accent)

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dimensional stats">
  <defs>{grid_defs}</defs>
  {grid_rect}
  {cube_svg}
  {''.join(cards)}
</svg>"""
