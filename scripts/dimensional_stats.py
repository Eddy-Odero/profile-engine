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

from hud_grid import glow_filter, grid_background
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
font-weight="700" fill="{accent}" filter="url(#hudglow)">{_esc(value)}</text>
    <line x1="20" y1="80" x2="{20 + bar_width}" y2="80" stroke="{accent}" stroke-width="2"/>
  </g>"""


def _isometric_cube(cx: float, cy: float, size: float, accent: str, label_lines: list[str]) -> str:
    """
    A wireframe cube (front face + back face + connecting edges, all
    outline-only, no fill) in isometric projection - matching the
    reference's actual style. An earlier filled/shaded isometric block
    version was tried and didn't match.
    """
    h = size * 0.55  # vertical squash for the isometric angle

    # 8 vertices of the cube in isometric projection: front face (4) + back face (4, offset up-left)
    front = [
        (cx - size / 2, cy - h / 2),  # front-top-left
        (cx + size / 2, cy - h / 2),  # front-top-right
        (cx + size / 2, cy + h),      # front-bottom-right
        (cx - size / 2, cy + h),      # front-bottom-left
    ]
    depth_x, depth_y = size * 0.35, -size * 0.22
    back = [(x + depth_x, y + depth_y) for x, y in front]

    def line(p1, p2, width=1.2):
        return f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="{accent}" stroke-width="{width}"/>'

    edges = []
    for i in range(4):
        edges.append(line(front[i], front[(i + 1) % 4]))  # front face
        edges.append(line(back[i], back[(i + 1) % 4]))    # back face
        edges.append(line(front[i], back[i]))              # connecting edges

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
  <defs>{grid_defs}{glow_filter()}</defs>
  {grid_rect}
  {cube_svg}
  {''.join(cards)}
</svg>"""
