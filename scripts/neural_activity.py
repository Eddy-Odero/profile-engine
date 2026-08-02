"""
neural_activity.py

"Neural Activity" - the LAST section in the final layout. A green
GitHub-style contribution heatmap, matching the reference design:
a big number top-left (total contributions), a small "LIVE" status
chip, a caption line under the number, and two right-aligned stat
readouts ("Total active" / "Streak") above the grid itself.

Same visual language as every other HUD component (grid texture behind
everything, translucent panel, glow filter on bright elements, exact
HUD_COLORS palette) via hud_grid.py / themes.py.

Usage:
    from neural_activity import render_neural_activity_svg
    svg_markup = render_neural_activity_svg(weeks, total, streak, active_days, theme_name)

`weeks` is a list of 52-ish columns, each a list of 7 ints (0-4 intensity
levels, Sun-Sat), oldest column first - same shape GitHub's own
contribution graph uses, so it can be fed real GraphQL data later
(`github.py`'s `fetch_graphql_extras` already pulls a contribution
count; wiring the actual daily calendar through is the natural next
step once that's wanted).
"""

from __future__ import annotations

import hashlib
import html

from hud_grid import glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS

CELL = 13
CELL_GAP = 3
ROWS = 7

PANEL_PAD_X = 24
PANEL_PAD_TOP = 138  # room for the number/chip row + the centered streak badge row
PANEL_PAD_BOTTOM = 20

BG = "07090F"

# 5 intensity levels (0 = no activity) shading from near-background up
# to the full saturated accent - same "dark to light" gradient logic
# used for the Dimensional Stats numbers, applied here as discrete
# steps instead of a continuous gradient.
LEVEL_OPACITIES = [0.10, 0.32, 0.52, 0.75, 1.0]


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _cell_color(level: int, accent: str) -> tuple[str, float]:
    level = max(0, min(level, len(LEVEL_OPACITIES) - 1))
    return accent, LEVEL_OPACITIES[level]


def render_neural_activity_svg(
    weeks: list[list[int]],
    total_contributions: int,
    current_streak: int,
    longest_streak: int,
    active_days: int,
    theme_name: str = DEFAULT_THEME,
) -> str:
    """
    Build the Neural Activity SVG: big total-contributions number,
    LIVE chip, active-days/current-streak/longest-streak readout, and
    the heatmap grid itself.
    """
    accent = HUD_COLORS["activity"]

    grid_w = len(weeks) * (CELL + CELL_GAP) - CELL_GAP
    grid_h = ROWS * (CELL + CELL_GAP) - CELL_GAP

    width = max(grid_w + PANEL_PAD_X * 2, 640)
    height = PANEL_PAD_TOP + grid_h + PANEL_PAD_BOTTOM

    grid_x0 = (width - grid_w) / 2
    grid_y0 = PANEL_PAD_TOP

    GLYPHS = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    cells = []
    for col, week in enumerate(weeks):
        for row, level in enumerate(week):
            color, opacity = _cell_color(level, accent)
            x = grid_x0 + col * (CELL + CELL_GAP)
            y = grid_y0 + row * (CELL + CELL_GAP)
            glow = ' filter="url(#hudglow)"' if level >= 3 else ""
            cell_svg = (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" fill-opacity="{opacity}"{glow}/>'
            )
            # A small character glyph sits inside each active cell - some
            # tinted a lighter green so they nearly blend into the fill,
            # others black so they pop with real contrast - a deliberate
            # mix, not just decoration. Deterministic per (col,row) so
            # rebuilds don't flicker the pattern around.
            if level > 0:
                h = int(hashlib.md5(f"{col}-{row}".encode()).hexdigest(), 16)
                glyph = GLYPHS[h % len(GLYPHS)]
                glyph_color = "#0a0f0c" if (h // len(GLYPHS)) % 2 == 0 else "#bdf5d8"
                cell_svg += (
                    f'<text x="{x + CELL/2:.1f}" y="{y + CELL/2 + 2.6:.1f}" '
                    f'font-family="Consolas, Menlo, monospace" font-size="{CELL*0.62:.1f}" '
                    f'font-weight="700" fill="{glyph_color}" text-anchor="middle">{glyph}</text>'
                )
            cells.append(cell_svg)

    bg_defs, bg_rect = grid_background(width, height, accent, spacing=20)
    scan_defs, scan_rect = scanline_overlay(width, height)

    # Big number, top-left
    number_block = f"""
  <text x="{PANEL_PAD_X}" y="52" font-family="Consolas, Menlo, monospace" \
font-size="46" font-weight="700" fill="{accent}" filter="url(#hudglow)">{total_contributions}</text>
  <text x="{PANEL_PAD_X}" y="70" font-family="Consolas, Menlo, monospace" font-size="10" \
fill="#8a7fa8" letter-spacing="1">CONTRIBUTIONS_THIS_CYCLE</text>"""

    # LIVE status chip, top-right
    chip_w, chip_h = 60, 20
    chip_x = width - PANEL_PAD_X - chip_w
    chip_y = 20
    live_chip = f"""
  <g>
    <rect x="{chip_x}" y="{chip_y}" width="{chip_w}" height="{chip_h}" rx="3" \
fill="{accent}" fill-opacity="0.12" stroke="{accent}" stroke-width="1"/>
    <circle cx="{chip_x + 12}" cy="{chip_y + chip_h/2}" r="3" fill="{accent}" filter="url(#hudglow)"/>
    <text x="{chip_x + 22}" y="{chip_y + chip_h/2 + 4}" font-family="Consolas, Menlo, monospace" \
font-size="10" font-weight="700" fill="{accent}" letter-spacing="1">LIVE</text>
  </g>"""

    # Active-days readout stays as a small right-aligned caption under
    # the LIVE chip; current/longest streak get their own centered
    # badge pills instead - same visual language as the LIVE chip, but
    # centered and given room to actually read as a highlight rather
    # than a line buried in small text.
    active_text = f"""
  <text x="{width - PANEL_PAD_X}" y="{chip_y + chip_h + 18}" \
font-family="Consolas, Menlo, monospace" font-size="10" fill="#8a7fa8" \
text-anchor="end" letter-spacing="0.5">TOTAL_ACTIVE: {active_days}</text>"""

    def _streak_badge(cx: float, y: float, icon: str, label: str, value: int, w: float, h: float) -> str:
        x = cx - w / 2
        return f"""
  <g>
    <rect x="{x:.1f}" y="{y}" width="{w}" height="{h}" rx="{h/2:.1f}" \
fill="{accent}" fill-opacity="0.10" stroke="{accent}" stroke-width="1"/>
    <text x="{x+16:.1f}" y="{y+h/2+5:.1f}" font-size="14" text-anchor="middle">{icon}</text>
    <text x="{x+30:.1f}" y="{y+h/2-2:.1f}" font-family="Consolas, Menlo, monospace" font-size="8.5" \
fill="#8a7fa8" letter-spacing="0.5">{label}</text>
    <text x="{x+30:.1f}" y="{y+h/2+12:.1f}" font-family="Consolas, Menlo, monospace" font-size="13" \
font-weight="700" fill="{accent}" filter="url(#hudglow)">{value} days</text>
  </g>"""

    badge_w, badge_h, badge_gap = 168, 34, 14
    badges_y = 92  # centered row, below the number/LIVE-chip row, above the grid
    left_cx = width / 2 - badge_gap / 2 - badge_w / 2
    right_cx = width / 2 + badge_gap / 2 + badge_w / 2
    streak_badges = (
        _streak_badge(left_cx, badges_y, "🔥", "CURRENT STREAK", current_streak, badge_w, badge_h)
        + _streak_badge(right_cx, badges_y, "🏆", "LONGEST STREAK", longest_streak, badge_w, badge_h)
    )

    # A small rocket flying across the grid on a gentle wave path, with a
    # fading trail of particles behind it - one fun animated focal point
    # instead of more HUD chrome. It fades in/out right at the canvas
    # edges so the animation loop resets while invisible, avoiding a
    # visible snap-back.
    rocket_duration = 9
    path_d = (
        f"M {grid_x0 - 24:.1f},{grid_y0 + grid_h * 0.55:.1f} "
        f"Q {grid_x0 + grid_w * 0.25:.1f},{grid_y0 - 14:.1f} "
        f"{grid_x0 + grid_w * 0.5:.1f},{grid_y0 + grid_h * 0.5:.1f} "
        f"Q {grid_x0 + grid_w * 0.75:.1f},{grid_y0 + grid_h + 16:.1f} "
        f"{grid_x0 + grid_w + 24:.1f},{grid_y0 + grid_h * 0.45:.1f}"
    )
    fade_anim = (
        '<animate attributeName="opacity" values="0;1;1;0" '
        'keyTimes="0;0.08;0.9;1" dur="{d}s" begin="{b}s" repeatCount="indefinite"/>'
    )
    trail = []
    n_particles = 5
    for i in range(n_particles, 0, -1):
        delay = -(i * 0.18)
        r = max(1, 3.2 - i * 0.4)
        trail.append(f"""
  <circle r="{r:.1f}" fill="{accent}" opacity="0">
    <animateMotion path="{path_d}" dur="{rocket_duration}s" begin="{delay}s" repeatCount="indefinite"/>
    {fade_anim.format(d=rocket_duration, b=delay)}
  </circle>""")

    rocket = f"""
  <text font-size="15" opacity="0" text-anchor="middle" dominant-baseline="middle">🚀
    <animateMotion path="{path_d}" dur="{rocket_duration}s" repeatCount="indefinite"/>
    {fade_anim.format(d=rocket_duration, b=0)}
  </text>"""

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Neural activity">
  <defs>{bg_defs}{glow_filter()}{scan_defs}</defs>
  <rect width="{width}" height="{height}" fill="#{BG}" fill-opacity="0.6"/>
  {bg_rect}
  {number_block}
  {live_chip}
  {active_text}
  <g>{''.join(cells)}</g>
  {''.join(trail)}
  {rocket}
  {streak_badges}
  {scan_rect}
</svg>"""
