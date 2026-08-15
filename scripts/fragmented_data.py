"""
fragmented_data.py

"Fragmented Data" - same card content/layout as the original project
card (icon centered above the title, centered description, bottom
stats row - reused as-is from project_cards.py), with two differences:
the card is a wide rectangle instead of a portrait rect, and its
top-right + bottom-left corners are chamfered (cut at 45 degrees)
instead of plain rounded corners.

The PUBLIC/VIP ribbon uses its own dedicated shape (_covering_ribbon)
sized to fully cover the chamfered top-right corner, so that corner
reads as a clean, sharp edge under solid ribbon color rather than
showing the cut/notch. An earlier version clipped the shared ribbon
shape with the same chamfer, which sliced the ribbon itself and left
a gap - this replaces that with a ribbon deliberately oversized to
cover the whole cut.

Usage:
    from fragmented_data import render_fragment_card_svg
    svg_markup = render_fragment_card_svg(project, theme_name)
"""

from __future__ import annotations

from hud_grid import glass_frame_polygon, grid_background
from project_cards import (
    CARD_BORDER,
    DESC_COLOR,
    ICON_RADIUS,
    RIBBON_COLORS,
    _esc,
    _project_icon,
    _stats_row,
    _wrap_description,
    _wrap_label,
)
from themes import DEFAULT_THEME, get_theme

WIDTH = 380
HEIGHT = 150
CHAMFER = 28  # size of the cut corner, top-right and bottom-left
MARGIN = 36  # extra canvas room so the ribbon flag can poke past the top-right edge


def _chamfered_points(width: float, height: float, cut: float) -> str:
    points = [
        (0, 0),
        (width - cut, 0),
        (width, cut),
        (width, height),
        (cut, height),
        (0, height - cut),
    ]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def _covering_ribbon(visibility: str, width: float, chamfer: float) -> str:
    """
    A PUBLIC/VIP ribbon shaped as a true parallelogram whose inner edge
    sits EXACTLY on the card's own chamfer line (352,0)-(380,28) for a
    380-wide/28-chamfer card - not just near it. That's what makes it
    read as "inline with the slice": the ribbon's edge and the card's
    cut are the same line, not two different diagonals. It then extends
    OUTWARD (away from the card body, past the true corner) by `band`
    so the missing-corner gap is still fully covered, rather than
    trading the gap-coverage fix for the alignment fix.
    """
    if not visibility:
        return ""
    color = RIBBON_COLORS.get(visibility.lower(), RIBBON_COLORS["public"])
    label = visibility.upper()

    # The chamfer's own two endpoints - the ribbon's inner edge.
    ax, ay = width - chamfer, 0.0
    bx, by = width, chamfer

    import math
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length          # unit vector along the chamfer
    nx, ny = dy / length, -dx / length          # unit vector perpendicular, outward

    # Extend past both ends of the chamfer segment too, not just
    # outward from it - the raw chamfer segment is short (a 28px
    # chamfer is ~40px long diagonally), not enough room for
    # horizontal "PUBLIC" text inside a rotated band that short.
    extend = 22
    band = 22
    ax, ay = ax - ux * extend, ay - uy * extend
    bx, by = bx + ux * extend, by + uy * extend
    cx, cy = ax + nx * band, ay + ny * band
    dx2, dy2 = bx + nx * band, by + ny * band

    points = f"{ax:.1f},{ay:.1f} {bx:.1f},{by:.1f} {dx2:.1f},{dy2:.1f} {cx:.1f},{cy:.1f}"
    label_x = (ax + bx + cx + dx2) / 4
    label_y = (ay + by + cy + dy2) / 4 + 3

    return f"""
  <g>
    <polygon points="{points}" fill="{color}"/>
    <text x="{label_x:.1f}" y="{label_y:.1f}" font-family="Consolas, Menlo, monospace" font-size="9" \
font-weight="700" fill="#0a0a0d" text-anchor="middle">{_esc(label)}</text>
  </g>"""


def render_fragment_card_svg(project: dict, theme_name: str = DEFAULT_THEME) -> str:
    """Same card as render_single_project_card_svg, just wide + corner-chamfered."""
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"

    name = project.get("name", "")
    description = project.get("description", "")
    icon_key = project.get("icon", "")

    name_lines = _wrap_label(name)
    desc_lines = _wrap_description(description, max_chars=50)

    icon_cy = 30
    name_y = icon_cy + ICON_RADIUS + 18
    desc_start_y = name_y + len(name_lines) * 18 + 4

    name_elements = "".join(
        f'<text x="{WIDTH / 2}" y="{name_y + i * 18}" '
        f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="14" '
        f'font-weight="700" fill="white" text-anchor="middle">{_esc(line)}</text>'
        for i, line in enumerate(name_lines)
    )
    desc_elements = "".join(
        f'<text x="{WIDTH / 2}" y="{desc_start_y + i * 15}" '
        f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" '
        f'fill="#{DESC_COLOR}" text-anchor="middle">{_esc(line)}</text>'
        for i, line in enumerate(desc_lines)
    )

    outline_pts = _chamfered_points(WIDTH, HEIGHT, CHAMFER)
    grid_defs, grid_rect = grid_background(WIDTH, HEIGHT, accent, spacing=16)
    glass_defs, glass_overlay = glass_frame_polygon(outline_pts, accent, pattern_id="fragglass")

    return f"""<svg width="{WIDTH+MARGIN}" height="{HEIGHT+MARGIN}" viewBox="0 {-MARGIN} {WIDTH+MARGIN} {HEIGHT+MARGIN}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(name)}">
  <defs>
    {grid_defs}
    {glass_defs}
    <clipPath id="cardclip">
      <polygon points="{outline_pts}"/>
    </clipPath>
  </defs>
  <g clip-path="url(#cardclip)">
    {grid_rect}
  </g>
  <polygon points="{outline_pts}" fill="#{theme['label_color']}" fill-opacity="0.65" stroke="#{CARD_BORDER}" stroke-width="1"/>
  {_covering_ribbon(project.get("visibility", ""), WIDTH, CHAMFER)}
  {_project_icon(WIDTH / 2, icon_cy, icon_key, accent)}
  {name_elements}
  {desc_elements}
  <line x1="14" y1="{HEIGHT - 26}" x2="{WIDTH - 14}" y2="{HEIGHT - 26}" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
  {_stats_row(HEIGHT - 10, project.get("language", ""), project.get("stars", 0), \
project.get("forks", 0), accent, width=WIDTH)}
  {glass_overlay}
</svg>"""
