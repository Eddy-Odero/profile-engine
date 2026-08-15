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
    A PUBLIC/VIP ribbon sized to fully cover the chamfered top-right
    corner - not just sit near it. The shared project_cards._ribbon()
    geometry was built for a plain rectangular card and stops a few
    pixels short of the true edge, which left a sliver of the cut
    corner uncovered (a visible gap/notch instead of a clean edge).
    This one's right edge runs flush with the card's real corner
    (x=width, y=0 down to y=chamfer+a bit) so the cut is fully hidden
    under solid ribbon color - a sharp edge, not a sliced one.
    """
    if not visibility:
        return ""
    color = RIBBON_COLORS.get(visibility.lower(), RIBBON_COLORS["public"])
    label = visibility.upper()
    top = chamfer + 4
    bottom = chamfer + 18
    return f"""
  <g>
    <polygon points="{width-3*chamfer},0 {width},0 {width},{bottom} {width-2*chamfer+6},{bottom}" fill="{color}"/>
    <text x="{width-chamfer-9}" y="{top+9}" font-family="Consolas, Menlo, monospace" font-size="9" \
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

    return f"""<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" \
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
