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

from hud_grid import glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

CARD_WIDTH = 280  # multiple of the 20px grid spacing below
CARD_HEIGHT = 100  # multiple of 20
CARD_GAP = 20  # changed from 16 - now a multiple of the grid spacing, so card edges land on grid lines
CARD_BG = "07090F"  # exact background from spec, subtle navy tint
CARD_BORDER = "241c33"
LABEL_COLOR = "8a7fa8"

CUBE_SIZE = 90
CUBE_BOX_WIDTH = 220
CUBE_BOX_HEIGHT = 220  # multiple of 20 (was 224) - keeps the whole canvas height grid-aligned


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


def _shade(hex_color: str, factor: float) -> str:
    """factor > 1 lightens toward white, factor < 1 darkens toward black."""
    r, g, b = _hex_to_rgb(hex_color)
    if factor >= 1:
        blend = min(factor - 1, 1)
        r, g, b = [int(c + (255 - c) * blend) for c in (r, g, b)]
    else:
        r, g, b = [int(c * factor) for c in (r, g, b)]
    return f"#{r:02x}{g:02x}{b:02x}"


def _number_gradient_defs(accent: str, gradient_id: str) -> str:
    """
    A gradient from a darker shade of the accent to a lighter shade -
    the "starts dark, gradually lightens" glow illusion on the big
    numbers, rather than one flat solid color.
    """
    dark = _shade(accent, 0.45)
    light = _shade(accent, 1.7)
    return f"""
    <linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{dark}"/>
      <stop offset="100%" stop-color="{light}"/>
    </linearGradient>"""


def _stat_card(x: float, y: float, label: str, value, accent: str, idx: int) -> str:
    value = str(value)
    bar_width = min(len(value) * 14 + 20, CARD_WIDTH - 40)
    gradient_id = f"numGrad{idx}"
    return f"""
  <defs>{_number_gradient_defs(accent, gradient_id)}</defs>
  <g transform="translate({x},{y})">
    <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" fill="#{CARD_BG}" fill-opacity="0.3" stroke="{accent}" stroke-width="1"/>
    <rect x="0" y="0" width="4" height="{CARD_HEIGHT}" fill="{accent}"/>
    <text x="20" y="28" font-family="Consolas, Menlo, monospace" font-size="10" \
fill="#{LABEL_COLOR}" letter-spacing="1">{_esc(label.upper())}</text>
    <text x="20" y="64" font-family="Consolas, Menlo, monospace" font-size="30" \
font-weight="700" fill="url(#{gradient_id})" filter="url(#hudglow)">{_esc(value)}</text>
    <line x1="20" y1="80" x2="{20 + bar_width}" y2="80" stroke="{accent}" stroke-width="2"/>
  </g>"""


def _isometric_cube(cx: float, cy: float, size: float, accent: str, label_lines: list[str]) -> str:
    """
    A wireframe cube in near-front view: looking almost directly at the
    front face, but with the back face very slightly squeezed toward
    the bottom-right (smaller margin on the right/bottom than on the
    left/top) - a small directional offset is what actually reads as a
    real box being looked at, rather than two perfectly concentric
    squares (which reads as flat/decorative, not dimensional). A
    previous version offset the back face by a LOT toward one corner,
    which read as a skewed side view instead - this keeps the offset
    small.
    """
    front_half = size / 2
    back_half = front_half * 0.74  # back face close in size to front - a shallow, near-front box

    front = [
        (cx - front_half, cy - front_half),  # top-left
        (cx + front_half, cy - front_half),  # top-right
        (cx + front_half, cy + front_half),  # bottom-right
        (cx - front_half, cy + front_half),  # bottom-left
    ]
    # Small offset toward bottom-right - back face margin is tighter on
    # the right/bottom than the left/top, giving the natural-box read.
    offset_x, offset_y = size * 0.09, size * 0.06
    back_cx, back_cy = cx + offset_x, cy + offset_y
    back = [
        (back_cx - back_half, back_cy - back_half),
        (back_cx + back_half, back_cy - back_half),
        (back_cx + back_half, back_cy + back_half),
        (back_cx - back_half, back_cy + back_half),
    ]

    def line(p1, p2, width=1.2):
        return f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="{accent}" stroke-width="{width}"/>'

    edges = []
    for i in range(4):
        edges.append(line(front[i], front[(i + 1) % 4]))  # front face
        edges.append(line(back[i], back[(i + 1) % 4]))    # back face
        edges.append(line(front[i], back[i]))              # diagonal connecting edges

    label_svg = "".join(
        f'<text x="{cx:.1f}" y="{cy - 4 + i*13:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="9" fill="{accent}" text-anchor="middle">{_esc(line_text)}</text>'
        for i, line_text in enumerate(label_lines)
    )

    return f"""
  <g fill="none">
    {''.join(edges)}
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

    gap_between = 20  # multiple of grid spacing, matches CARD_GAP for consistent alignment
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
        cards.append(_stat_card(x, y, label, value, accent, i))

    grid_defs, grid_rect = grid_background(width, height, accent, spacing=20)
    scan_defs, scan_rect = scanline_overlay(width, height)

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dimensional stats">
  <defs>{grid_defs}{glow_filter()}{scan_defs}</defs>
  <rect width="{width}" height="{height}" fill="#07090F" fill-opacity="0.82"/>
  {grid_rect}
  {cube_svg}
  {''.join(cards)}
  {scan_rect}
</svg>"""
