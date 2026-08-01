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
    width: float, height: float, color: str, spacing: int = 24, opacity: float = 0.09,
    pattern_id: str = "hudgrid", rx: int = 0,
) -> tuple[str, str]:
    """
    Returns (defs_markup, rect_markup) - a grid pattern definition (fine
    lines every `spacing`px, plus a bolder crossing line every 4th cell
    for the denser "grid crossing the whole design" look) and a fill
    rect using it. Caller places `defs_markup` inside <defs> and
    `rect_markup` as the first thing painted (before other content).

    `rx` should match the corner radius of any rounded card this grid
    sits behind - otherwise the grid's sharp square corners poke out
    past a rounded card's rounded corners, which looks like a rendering
    glitch rather than a background texture.
    """
    bold_spacing = spacing * 4
    defs = f"""
    <pattern id="{pattern_id}" width="{spacing}" height="{spacing}" patternUnits="userSpaceOnUse">
      <path d="M {spacing} 0 L 0 0 0 {spacing}" fill="none" stroke="{color}" stroke-width="0.6" opacity="{opacity}"/>
    </pattern>
    <pattern id="{pattern_id}bold" width="{bold_spacing}" height="{bold_spacing}" patternUnits="userSpaceOnUse">
      <path d="M {bold_spacing} 0 L 0 0 0 {bold_spacing}" fill="none" stroke="{color}" stroke-width="1" \
opacity="{min(opacity * 1.8, 0.9)}"/>
    </pattern>"""
    rect = (
        f'<rect width="{width}" height="{height}" rx="{rx}" fill="url(#{pattern_id})"/>'
        f'<rect width="{width}" height="{height}" rx="{rx}" fill="url(#{pattern_id}bold)"/>'
    )
    return defs, rect


def scanline_overlay(
    width: float, height: float, y_offset: float = 0, opacity: float = 0.15
) -> tuple[str, str]:
    """
    The same horizontal scanline texture svg_terminal.py already uses,
    pulled out here so every HUD section can share it - the spec calls
    for this "CRT scanline/noise feel" throughout the design, not just
    on the terminal card, so every section-level SVG should layer this
    on top of its grid background.

    Returns (defs_markup, rect_markup), same calling convention as
    grid_background() - caller places defs_markup inside <defs> and
    rect_markup as a late-painted overlay (after content, so the
    scanlines sit on top).
    """
    defs = f"""
    <pattern id="scanlines" width="4" height="3" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="black" fill-opacity="{opacity}"/>
    </pattern>"""
    rect = f'<rect x="0" y="{y_offset}" width="{width}" height="{height - y_offset}" fill="url(#scanlines)"/>'
    return defs, rect


def glow_filter(filter_id: str = "hudglow", strength: float = 1.4) -> str:
    """
    A soft bloom/glow filter - the hazy, slightly-blurred-highlight look
    around bright text/borders that gives this design its "blurry
    aesthetic", as opposed to crisp flat-color shapes. Apply via
    filter="url(#{filter_id})" on any element that should glow.
    """
    return f"""
    <filter id="{filter_id}" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="{strength}" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>"""
