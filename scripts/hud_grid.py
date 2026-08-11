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


def glass_frame_rect(
    width: float, height: float, accent: str, rx: int = 16, pattern_id: str = "glass"
) -> tuple[str, str]:
    """
    The "premium glass panel" finish: a border that's a gradient (bright
    where light would catch the top-left edge, fading toward the
    bottom-right) instead of a flat single-color stroke, plus a soft
    diagonal sheen overlay across the upper portion of the panel - the
    two things that actually read as "glassmorphism" rather than just
    "translucent rectangle". Real backdrop-blur isn't reliable in
    GitHub's SVG rendering, so this fakes the same premium-glass cue
    with gradients instead of blur.

    Returns (defs_markup, overlay_markup). `defs_markup` goes in <defs>;
    `overlay_markup` is painted LAST (border needs to sit crisply on
    top of everything, sheen needs to sit above the fill but the text
    still reads through it since it's low-opacity white).
    """
    border_id = f"{pattern_id}Border"
    sheen_id = f"{pattern_id}Sheen"
    defs = f"""
    <linearGradient id="{border_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.65"/>
      <stop offset="45%" stop-color="{accent}" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0.06"/>
    </linearGradient>
    <linearGradient id="{sheen_id}" x1="0%" y1="0%" x2="30%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.10"/>
      <stop offset="55%" stop-color="#ffffff" stop-opacity="0.02"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="{pattern_id}Clip">
      <rect width="{width}" height="{height}" rx="{rx}"/>
    </clipPath>"""
    overlay = (
        f'<rect width="{width}" height="{height}" rx="{rx}" fill="url(#{sheen_id})" '
        f'clip-path="url(#{pattern_id}Clip)"/>'
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="{rx}" '
        f'fill="none" stroke="url(#{border_id})" stroke-width="1.2"/>'
    )
    return defs, overlay


def glass_frame_polygon(points: str, accent: str, pattern_id: str = "glass") -> tuple[str, str]:
    """
    Same premium-glass border+sheen treatment as glass_frame_rect, for
    panels with a non-rectangular outline (the chamfered Fragmented
    Data cards) - takes the same `points` string used for the panel's
    own fill/stroke polygon so the glass edge follows the exact same
    silhouette instead of a plain rectangle poking out past the cut
    corners.
    """
    border_id = f"{pattern_id}Border"
    sheen_id = f"{pattern_id}Sheen"
    defs = f"""
    <linearGradient id="{border_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.65"/>
      <stop offset="45%" stop-color="{accent}" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0.06"/>
    </linearGradient>
    <linearGradient id="{sheen_id}" x1="0%" y1="0%" x2="30%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.10"/>
      <stop offset="55%" stop-color="#ffffff" stop-opacity="0.02"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="{pattern_id}Clip">
      <polygon points="{points}"/>
    </clipPath>"""
    overlay = (
        f'<polygon points="{points}" fill="url(#{sheen_id})" clip-path="url(#{pattern_id}Clip)"/>'
        f'<polygon points="{points}" fill="none" stroke="url(#{border_id})" stroke-width="1.2"/>'
    )
    return defs, overlay


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
