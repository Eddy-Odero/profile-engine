"""
fragmented_data.py

"Fragmented Data" - same card content/layout as the original project
card (icon centered above the title, centered description, bottom
stats row, corner ribbon - all reused as-is from project_cards.py),
with exactly two differences: the card is a wide rectangle instead of
a portrait rect, and its top-right + bottom-left corners are chamfered
(cut at 45 degrees) instead of plain rounded corners.

The ribbon itself is NOT redrawn or repositioned - it's the exact same
_ribbon() polygon from project_cards.py. It's wrapped in a clip-path
using the card's own chamfered outline, so the same diagonal cut that
slices the card's corner also slices the ribbon sitting in it - that's
what turns it into the "opposite parallelogram" look, as a side effect
of one shared clip shape, not a redesigned ribbon.

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
    _esc,
    _project_icon,
    _ribbon,
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
  <g clip-path="url(#cardclip)">
    {_ribbon(project.get("visibility", ""), width=WIDTH)}
  </g>
  {_project_icon(WIDTH / 2, icon_cy, icon_key, accent)}
  {name_elements}
  {desc_elements}
  <line x1="14" y1="{HEIGHT - 26}" x2="{WIDTH - 14}" y2="{HEIGHT - 26}" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
  {_stats_row(HEIGHT - 10, project.get("language", ""), project.get("stars", 0), \
project.get("forks", 0), accent, width=WIDTH)}
  {glass_overlay}
</svg>"""
