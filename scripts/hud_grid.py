"""
hud_grid.py

A subtle grid-line texture pattern, reusable across every HUD-styled
component (skill_modules.py, dimensional_stats.py, project_cards.py).

This was a genuine gap: every prior revision matched colors but never
added the fine grid/graph-paper background texture that's visible
throughout the reference image - a real structural similarity miss,
not just a color miss.

Usage:
    defs, fill_rect = grid_background(width, height, color, pattern_id="grid1")
    svg = f"<svg ...><defs>{defs}</defs>{fill_rect}...rest of content...</svg>"
"""

from __future__ import annotations


def grid_background(
    width: float, height: float, color: str, spacing: int = 24, opacity: float = 0.08,
    pattern_id: str = "hudgrid", rx: int = 0,
) -> tuple[str, str]:
    """
    Returns (defs_markup, rect_markup) - a faint grid pattern definition
    and a fill rect using it. Caller places `defs_markup` inside <defs>
    and `rect_markup` as the first thing painted (before other content).

    `rx` should match the corner radius of any rounded card this grid
    sits behind - otherwise the grid's sharp square corners poke out
    past a rounded card's rounded corners, which looks like a rendering
    glitch rather than a background texture.
    """
    defs = f"""
    <pattern id="{pattern_id}" width="{spacing}" height="{spacing}" patternUnits="userSpaceOnUse">
      <path d="M {spacing} 0 L 0 0 0 {spacing}" fill="none" stroke="{color}" stroke-width="0.5" opacity="{opacity}"/>
    </pattern>"""
    rect = f'<rect width="{width}" height="{height}" rx="{rx}" fill="url(#{pattern_id})"/>'
    return defs, rect
