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

from hud_grid import glass_frame_rect, glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

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
    bg = get_theme(theme_name)["label_color"]

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

    bg_defs, bg_rect = grid_background(width, height, accent, spacing=20, rx=16)
    scan_defs, scan_rect = scanline_overlay(width, height)
    glass_defs, glass_overlay = glass_frame_rect(width, height, accent, rx=16, pattern_id="neuralglass")

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

    # A shark chasing a few small fish across the grid - one animated
    # focal point instead of more HUD chrome. Three laps alternate
    # direction: left-to-right, then right-to-left on a mirrored wave,
    # then a diagonal bottom-to-top pass.
    #
    # Each lap is its OWN <animateMotion>, chained to the next via
    # begin="prevId.end" instead of one concatenated path with assumed
    # equal-thirds timing. That equal-thirds assumption was the actual
    # bug behind "changes direction before reaching the edge": a single
    # animateMotion paces itself by constant speed over the path's real
    # arc length, and lap 3 (a short diagonal) is geometrically much
    # shorter than laps 1/2 (wide S-curves) - so it was eating time that
    # rightfully belonged to lap 2, cutting lap 2 off early. Chaining
    # separate per-lap animations means each one always plays its own
    # path fully, in its own dur, regardless of how the other laps'
    # lengths compare.
    lap_duration = 6
    n_laps = 3
    rocket_duration = lap_duration * n_laps
    SHARK_COLOR = "#8C93A6"  # grey, like the original shark emoji - not the green accent

    lap_1 = (
        f"M {grid_x0 - 24:.1f},{grid_y0 + grid_h * 0.55:.1f} "
        f"Q {grid_x0 + grid_w * 0.25:.1f},{grid_y0 - 14:.1f} "
        f"{grid_x0 + grid_w * 0.5:.1f},{grid_y0 + grid_h * 0.5:.1f} "
        f"Q {grid_x0 + grid_w * 0.75:.1f},{grid_y0 + grid_h + 16:.1f} "
        f"{grid_x0 + grid_w + 24:.1f},{grid_y0 + grid_h * 0.45:.1f} "
    )
    lap_2 = (  # right-to-left, mirrored wave (dips the opposite way)
        f"M {grid_x0 + grid_w + 24:.1f},{grid_y0 + grid_h * 0.4:.1f} "
        f"Q {grid_x0 + grid_w * 0.75:.1f},{grid_y0 + grid_h + 18:.1f} "
        f"{grid_x0 + grid_w * 0.5:.1f},{grid_y0 + grid_h * 0.5:.1f} "
        f"Q {grid_x0 + grid_w * 0.25:.1f},{grid_y0 - 16:.1f} "
        f"{grid_x0 - 24:.1f},{grid_y0 + grid_h * 0.6:.1f} "
    )
    lap_3 = (  # diagonal, bottom-left to top-right
        f"M {grid_x0 + grid_w * 0.1:.1f},{grid_y0 + grid_h + 20:.1f} "
        f"Q {grid_x0 + grid_w * 0.5:.1f},{grid_y0 + grid_h * 0.3:.1f} "
        f"{grid_x0 + grid_w * 0.9:.1f},{grid_y0 - 20:.1f} "
    )
    laps = [lap_1, lap_2, lap_3]

    def _chained_motion(entity_id: str, initial_lead: float) -> str:
        """3 chained animateMotion elements for one entity - each lap
        begins exactly when the previous one ends, so every lap always
        gets its full, equal time slice."""
        parts = []
        for i, lap_path in enumerate(laps):
            this_id = f"{entity_id}_lap{i}"
            prev_id = f"{entity_id}_lap{(i - 1) % n_laps}"
            begin = f"{-initial_lead:.2f}s;{prev_id}.end" if i == 0 else f"{prev_id}.end"
            parts.append(
                f'<animateMotion id="{this_id}" path="{lap_path}" dur="{lap_duration}s" '
                f'begin="{begin}" fill="freeze"/>'
            )
        return "".join(parts)

    # One fade pulse per lap: invisible during the jump between laps,
    # visible while actually flying.
    fade_values = []
    fade_keytimes = []
    edge = 0.02  # fraction of one lap spent fading in/out
    for lap in range(n_laps):
        start = lap / n_laps
        end = (lap + 1) / n_laps
        fade_values += ["0", "1", "1", "0"]
        fade_keytimes += [
            f"{start:.4f}", f"{start + edge:.4f}", f"{end - edge:.4f}", f"{end:.4f}"
        ]
    fade_values_str = ";".join(fade_values)
    fade_keytimes_str = ";".join(fade_keytimes)
    fade_anim = (
        f'<animate attributeName="opacity" values="{fade_values_str}" '
        'keyTimes="{keytimes}" dur="{d}s" begin="{b}s" repeatCount="indefinite"/>'
    )

    # Direction-facing fix: laps 1 and 3 move left-to-right, lap 2 moves
    # right-to-left, but nothing was flipping to match - moving right
    # while still facing left (or vice versa) reads as swimming
    # backwards. `calcMode="discrete"` steps between values instead of
    # smoothly interpolating, so the flip happens as an instant mirror
    # at each lap boundary (while the element is invisible anyway, mid-
    # fade), not a gradual squish through zero.
    def _direction_flip_anim(begin: float, faces_right_by_default: bool) -> str:
        right_lap, left_lap = ("1,1", "-1,1") if faces_right_by_default else ("-1,1", "1,1")
        values = f"{right_lap};{left_lap};{right_lap};{right_lap}"
        return (
            f'<animateTransform attributeName="transform" type="scale" '
            f'values="{values}" keyTimes="0;{1/n_laps:.4f};{2/n_laps:.4f};1" '
            f'calcMode="discrete" dur="{rocket_duration}s" begin="{begin}s" repeatCount="indefinite"/>'
        )

    def _shark_svg(color: str) -> str:
        """
        A drawn shark modeled on the reference image: two-tone body
        (darker slate-grey top, lighter grey belly), a curved dorsal
        fin, a forked tail, a pectoral fin, a small eye, and a few teeth
        at the mouth - a separate lower-jaw piece still rotates open/
        closed on its own fast independent loop. Drawn nose-right by
        default (see faces_right_by_default above).
        """
        belly = "#C7CBD1"  # lighter grey, like the reference's underside
        dark = "#454B57"  # darker slate for the top-body outline/shade
        return f"""
    <g stroke="{dark}" stroke-width="0.6">
      <path fill="{color}" d="M -18,1 Q -18,-6 -7,-6.5 L 6,-5.5 Q 13,-5 16,0 \
Q 13,4.5 6,6 L -7,6.5 Q -18,7 -18,1 Z"/>
      <path fill="{belly}" fill-opacity="0.85" d="M -15,3 Q -6,6.5 5,5.8 \
Q 11,5.2 15,2 Q 10,5 3,4.8 Q -8,4.6 -15,3 Z"/>
      <path fill="{color}" d="M -3,-5.5 Q 0,-13 3,-5" />
      <path fill="{color}" d="M -16,0.5 L -25,-7 L -21,-1 L -26,5 L -17,2 Z"/>
      <path fill="{color}" d="M -3,5.5 L -7,12 L 1,6.5 Z"/>
      <circle cx="10.5" cy="-1.8" r="1.1" fill="#1a1a1f"/>
    </g>
    <g fill="#e9eaee" stroke="{dark}" stroke-width="0.4">
      <path d="M 12,-2 L 14,0.5 L 10.5,0.8 Z"/>
      <path d="M 13,1.5 L 15,3 L 11,2.8 Z"/>
    </g>
    <g fill="{color}" stroke="{dark}" stroke-width="0.6">
      <path d="M 16,0 L 9,1.5 L 14,4.5 Z">
        <animateTransform attributeName="transform" type="rotate" values="0 16 0;28 16 0;0 16 0" \
dur="0.7s" repeatCount="indefinite"/>
      </path>
    </g>"""

    # A few small fish swimming ahead of the shark, not a fading comet
    # trail - negative `begin` puts an element FURTHER ALONG the path at
    # any given moment (its clock started earlier), which is exactly
    # "ahead of / fleeing from" the shark at begin=0. Bigger negative
    # offset = further out in front of the pack.
    fish = []
    fish_offsets = [0.35, 0.75, 1.2]
    for i, lead in enumerate(fish_offsets):
        fish_id = f"fish{i}"
        fish.append(f"""
  <g opacity="0">
    {_chained_motion(fish_id, lead)}
    {fade_anim.format(keytimes=fade_keytimes_str, d=rocket_duration, b=-lead)}
    <g>
      {_direction_flip_anim(-lead, faces_right_by_default=False)}
      <text font-size="11" text-anchor="middle" dominant-baseline="middle">🐟</text>
    </g>
  </g>""")

    rocket = f"""
  <g opacity="0">
    {_chained_motion("shark", 0)}
    {fade_anim.format(keytimes=fade_keytimes_str, d=rocket_duration, b=0)}
    <g>
      {_direction_flip_anim(0, faces_right_by_default=True)}
      {_shark_svg(SHARK_COLOR)}
    </g>
  </g>"""

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Neural activity">
  <defs>{bg_defs}{glow_filter()}{scan_defs}{glass_defs}</defs>
  <rect width="{width}" height="{height}" rx="16" fill="#{bg}" fill-opacity="0.6"/>
  {bg_rect}
  {number_block}
  {live_chip}
  {active_text}
  <g>{''.join(cells)}</g>
  {''.join(fish)}
  {rocket}
  {streak_badges}
  {scan_rect}
  {glass_overlay}
</svg>"""
