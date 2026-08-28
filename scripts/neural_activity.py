"""
neural_activity.py

"Neural Activity" - the LAST section in the final layout. A big number
top-left (total contributions), a "LIVE" status chip, streak badges,
and a neon cyberpunk city skyline built from the same weekly data:
each week becomes one building, height + lit-window count scaled to
that week's activity, varied rooflines (spire/dome/angled-cut/flat) for
visual variety, gradient-lit facades, a water reflection beneath the
street line, plus a couple of planes crossing the sky and cars driving
the street.

Windows are deliberately GREEN (not the reference photo's warm yellow)
- they represent real commit activity, so they stay tied to the same
green used for "activity" everywhere else on the page rather than
matching a reference image's color choice.

Usage:
    from neural_activity import render_neural_activity_svg
    svg_markup = render_neural_activity_svg(weeks, total, current_streak, longest_streak, active_days, theme_name)

`weeks` is a list of 52-ish columns, each a list of 7 ints (0-4
intensity levels, Sun-Sat), oldest column first - same shape GitHub's
own contribution graph uses. Each column's 7 levels are summed (0-28)
to get that week's "activity score", which drives building height,
lit-window count, and roof style.
"""

from __future__ import annotations

import hashlib
import html

from hud_grid import glass_frame_rect, glow_filter, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

PANEL_PAD_X = 24
PANEL_PAD_TOP = 138  # room for the number/chip row + the centered streak badge row
CITY_HEIGHT = 150
REFLECTION_HEIGHT = 60
PANEL_PAD_BOTTOM = 20

NEON_GROUPS = ["cyan", "pink", "green"]
NEON_HEX = {"cyan": "#00E7FF", "pink": "#FF2279", "green": "#24FF9A"}
NEON_DARK = {"cyan": "#0a2230", "pink": "#2a0a1c", "green": "#0a2418"}

# Windows are always green (commit activity), regardless of a
# building's own neon accent color.
WINDOW_LIT = "#3CFFB0"
WINDOW_LIT_DIM = "#1FAE78"
WINDOW_DARK = "#0d1a16"

SKY_TOP = "#0d0508"
SKY_MID = "#20101f"
SKY_HORIZON = "#3d1830"
HORIZON_GLOW = "#ff7a3d"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _roof(x: float, w: float, y: float, style: int, color: str) -> str:
    """A decorative roof accent on top of a building body - varies the
    skyline silhouette instead of every building being a flat-top rect."""
    cx = x + w / 2
    if style == 1:  # thin spire/antenna
        return f'<line x1="{cx:.1f}" y1="{y:.1f}" x2="{cx:.1f}" y2="{y-16:.1f}" stroke="{color}" stroke-width="1.2"/>'
    if style == 2:  # domed cap
        return f'<path d="M {x:.1f},{y:.1f} Q {cx:.1f},{y-10:.1f} {x+w:.1f},{y:.1f} Z" fill="{color}" fill-opacity="0.85"/>'
    if style == 3:  # angled cut - one corner higher than the other
        return f'<path d="M {x:.1f},{y:.1f} L {x:.1f},{y-2:.1f} L {x+w:.1f},{y-9:.1f} L {x+w:.1f},{y:.1f} Z" fill="{color}"/>'
    if style == 4:  # landmark halo-ring tower, like the reference's domed towers
        spire_h = 20
        ring_y = y - spire_h * 0.55
        return (
            f'<line x1="{cx:.1f}" y1="{y:.1f}" x2="{cx:.1f}" y2="{y-spire_h:.1f}" stroke="{color}" stroke-width="1.4"/>'
            f'<ellipse cx="{cx:.1f}" cy="{ring_y:.1f}" rx="{w*0.42:.1f}" ry="2.6" fill="none" '
            f'stroke="{color}" stroke-width="1.3" stroke-opacity="0.9"/>'
        )
    return ""  # flat top, no accent


def _building(
    x: float, w: float, base_y: float, height: float, group: str, activity: int, gradient_id: str, height_frac: float
) -> str:
    """One building: gradient-lit body, a glass highlight streak, a
    roof accent, and a grid of windows lit in proportion to that
    week's activity score (0-28). `height_frac` (0-1, this building's
    height relative to the tallest one) biases which roof styles are
    even eligible - elaborate halo/spire caps only show up on the
    tallest buildings, like landmark towers standing out among plainer
    ones, rather than every building rolling the same dice."""
    y = base_y - height
    accent = NEON_HEX[group]
    win_w, win_h, gap = 4, 5, 2.5
    cols = max(1, int((w - gap) / (win_w + gap)))
    rows = max(1, int((height - gap) / (win_h + gap)))
    lit_fraction = min(1.0, activity / 20)

    roll = int(hashlib.md5(f"roof-{x:.0f}".encode()).hexdigest(), 16) % 10
    if height_frac > 0.75 and roll < 3:
        style = 4  # halo-ring landmark, tallest buildings only
    elif height_frac > 0.55 and roll < 4:
        style = 1  # spire
    elif roll < 2:
        style = 2  # dome
    elif roll < 4:
        style = 3  # angled cut
    else:
        style = 0  # flat
    roof = _roof(x, w, y, style, accent)

    # A thin brighter streak down one edge, like light catching a glass
    # corner - the reference image's buildings all have this.
    highlight = f'<rect x="{x+1.5:.1f}" y="{y:.1f}" width="1.4" height="{height:.1f}" fill="white" fill-opacity="0.22"/>'

    windows = []
    for r in range(rows):
        for c in range(cols):
            wx = x + gap + c * (win_w + gap)
            wy = y + gap + r * (win_h + gap)
            h = int(hashlib.md5(f"{x:.0f}-{r}-{c}".encode()).hexdigest(), 16)
            lit = (h % 100) < lit_fraction * 100
            if lit:
                color_w = WINDOW_LIT if (h // 100) % 2 else WINDOW_LIT_DIM
                windows.append(
                    f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{win_w}" height="{win_h}" '
                    f'fill="{color_w}" fill-opacity="0.95"/>'
                )
            else:
                windows.append(
                    f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{win_w}" height="{win_h}" fill="{WINDOW_DARK}"/>'
                )

    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{height:.1f}" '
        f'fill="url(#{gradient_id})" stroke="{accent}" stroke-width="1" stroke-opacity="0.8"/>'
        + highlight
        + roof
        + "".join(windows)
    )


def _plane_svg(color: str) -> str:
    return (
        f'<g fill="{color}" fill-opacity="0.9" filter="url(#hudglow)">'
        f'<path d="M -10,0 L 8,-3 L -2,0 L 8,3 Z"/>'
        f"</g>"
    )


def _car_svg(color: str) -> str:
    return f"""
    <g>
      <rect x="-9" y="-4" width="18" height="5" rx="1.5" fill="{color}"/>
      <path d="M -5,-4 L -3,-7 L 4,-7 L 6,-4 Z" fill="{color}"/>
      <circle cx="-5" cy="1" r="2" fill="#111"/>
      <circle cx="5" cy="1" r="2" fill="#111"/>
    </g>"""


def _chained_motion(entity_id: str, laps: list[str], lap_duration: float, initial_lead: float) -> str:
    n = len(laps)
    parts = []
    for i, lap_path in enumerate(laps):
        this_id = f"{entity_id}_lap{i}"
        prev_id = f"{entity_id}_lap{(i - 1) % n}"
        begin = f"{-initial_lead:.2f}s;{prev_id}.end" if i == 0 else f"{prev_id}.end"
        parts.append(
            f'<animateMotion id="{this_id}" path="{lap_path}" dur="{lap_duration}s" '
            f'begin="{begin}" fill="freeze"/>'
        )
    return "".join(parts)


def _fade_anim(n_laps: int, total_dur: float, begin: float) -> str:
    edge = 0.03
    values, keytimes = [], []
    for lap in range(n_laps):
        start, end = lap / n_laps, (lap + 1) / n_laps
        values += ["0", "1", "1", "0"]
        keytimes += [f"{start:.4f}", f"{start+edge:.4f}", f"{end-edge:.4f}", f"{end:.4f}"]
    return (
        f'<animate attributeName="opacity" values="{";".join(values)}" '
        f'keyTimes="{";".join(keytimes)}" dur="{total_dur}s" begin="{begin}s" repeatCount="indefinite"/>'
    )


def _direction_flip_anim(n_laps: int, total_dur: float, begin: float, faces_right_by_default: bool) -> str:
    right, left = ("1,1", "-1,1") if faces_right_by_default else ("-1,1", "1,1")
    values = ";".join(right if i % 2 == 0 else left for i in range(n_laps)) + f";{right if n_laps % 2 == 0 else left}"
    keytimes = ";".join(f"{i/n_laps:.4f}" for i in range(n_laps)) + ";1"
    return (
        f'<animateTransform attributeName="transform" type="scale" values="{values}" '
        f'keyTimes="{keytimes}" calcMode="discrete" dur="{total_dur}s" begin="{begin}s" repeatCount="indefinite"/>'
    )


def render_neural_activity_svg(
    weeks: list[list[int]],
    total_contributions: int,
    current_streak: int,
    longest_streak: int,
    active_days: int,
    theme_name: str = DEFAULT_THEME,
) -> str:
    accent = HUD_COLORS["activity"]
    bg = get_theme(theme_name)["label_color"]

    width = max(len(weeks) * 15 + PANEL_PAD_X * 2, 780)
    height = PANEL_PAD_TOP + CITY_HEIGHT + REFLECTION_HEIGHT + PANEL_PAD_BOTTOM

    city_x0 = PANEL_PAD_X
    city_w = width - PANEL_PAD_X * 2
    street_y = PANEL_PAD_TOP + CITY_HEIGHT

    n = max(len(weeks), 1)
    bldg_w = city_w / n

    # One gradient per neon color group - a warm orange base (city
    # lights bleeding up from the street, matching the horizon glow)
    # rising through the dark body tone into the lit neon color at
    # top, so buildings look lit from within with the same warm-to-
    # cool blend the reference has, instead of one flat accent color.
    gradient_defs = []
    for group in NEON_GROUPS:
        gid = f"bldg_{group}"
        gradient_defs.append(f"""
    <linearGradient id="{gid}" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="{HORIZON_GLOW}" stop-opacity="0.55"/>
      <stop offset="22%" stop-color="{NEON_DARK[group]}"/>
      <stop offset="100%" stop-color="{NEON_HEX[group]}" stop-opacity="0.35"/>
    </linearGradient>""")

    buildings = []
    heights = []
    for week in weeks:
        activity = sum(week)
        heights.append(16 + (activity / 28) * (CITY_HEIGHT - 26))
    max_h = max(heights) if heights else 1
    for i, week in enumerate(weeks):
        activity = sum(week)
        bldg_h = heights[i]
        group = NEON_GROUPS[i % len(NEON_GROUPS)]
        x = city_x0 + i * bldg_w
        # Slenderer towers with a visible gap between them (2px margin
        # each side instead of 1) reads closer to the reference's tall,
        # narrow skyscrapers than wide, barely-separated bars.
        buildings.append(
            _building(x + 2, bldg_w - 4, street_y, bldg_h, group, activity, f"bldg_{group}", bldg_h / max_h)
        )
    buildings_markup = "".join(buildings)

    # A dimmer, more distant row of buildings behind the main skyline,
    # for depth - like the reference's fainter background towers. Still
    # derived from the real weekly data (adjacent weeks paired and
    # summed) rather than invented, just rendered coarser and muted.
    distant = []
    pair_w = bldg_w * 2
    for i in range(0, n - 1, 2):
        pair_activity = sum(weeks[i]) + sum(weeks[i + 1])
        d_h = 20 + (pair_activity / 56) * (CITY_HEIGHT - 30)
        dx = city_x0 + i * bldg_w
        distant.append(
            f'<rect x="{dx:.1f}" y="{street_y-d_h:.1f}" width="{pair_w-3:.1f}" height="{d_h:.1f}" '
            f'fill="#241a3a" fill-opacity="0.55"/>'
        )
    distant_markup = "".join(distant)

    scan_defs, scan_rect = scanline_overlay(width, height)
    glass_defs, glass_overlay = glass_frame_rect(width, height, accent, rx=16, pattern_id="neuralglass")

    sky_gradient_id = "neuralSky"
    sky_defs = f"""
    <linearGradient id="{sky_gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{SKY_TOP}"/>
      <stop offset="55%" stop-color="{SKY_MID}"/>
      <stop offset="100%" stop-color="{SKY_HORIZON}"/>
    </linearGradient>"""
    sky_rect = (
        f'<rect x="{city_x0}" y="{PANEL_PAD_TOP}" width="{city_w}" height="{CITY_HEIGHT}" '
        f'fill="url(#{sky_gradient_id})"/>'
    )

    horizon_glow_id = "horizonGlow"
    horizon_defs = f"""
    <linearGradient id="{horizon_glow_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{HORIZON_GLOW}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{HORIZON_GLOW}" stop-opacity="0.28"/>
    </linearGradient>"""
    horizon_glow = (
        f'<rect x="{city_x0}" y="{street_y-40:.1f}" width="{city_w}" height="40" '
        f'fill="url(#{horizon_glow_id})"/>'
    )

    stars = []
    for i in range(32):
        h = int(hashlib.md5(f"star-{i}".encode()).hexdigest(), 16)
        sx = city_x0 + (h % 1000) / 1000 * city_w
        sy = PANEL_PAD_TOP + 6 + (h // 1000 % 1000) / 1000 * (CITY_HEIGHT * 0.5)
        r = 0.6 + (h % 3) * 0.3
        twinkle = ""
        if i % 6 == 0:
            twinkle = f'<animate attributeName="opacity" values="1;0.3;1" dur="{2+(i%3)}s" repeatCount="indefinite"/>'
        stars.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r:.1f}" fill="white">{twinkle}</circle>')

    street_line = (
        f'<line x1="{city_x0}" y1="{street_y:.1f}" x2="{city_x0+city_w}" y2="{street_y:.1f}" '
        f'stroke="#3a2a4a" stroke-width="2"/>'
    )

    # Water reflection: the whole skyline flipped vertically below the
    # street line, faded out with a gradient mask so it reads as a
    # reflection rather than a duplicate city.
    reflect_fade_id = "reflectFade"
    reflect_defs = f"""
    <linearGradient id="{reflect_fade_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="white" stop-opacity="0.65"/>
      <stop offset="100%" stop-color="white" stop-opacity="0"/>
    </linearGradient>
    <mask id="reflectMask">
      <rect x="{city_x0}" y="{street_y}" width="{city_w}" height="{REFLECTION_HEIGHT}" fill="url(#{reflect_fade_id})"/>
    </mask>"""
    reflection = (
        f'<g mask="url(#reflectMask)">'
        f'<g transform="translate(0,{2*street_y:.1f}) scale(1,-1)">{buildings_markup}</g>'
        f"</g>"
    )

    number_block = f"""
  <text x="{PANEL_PAD_X}" y="52" font-family="Consolas, Menlo, monospace" \
font-size="46" font-weight="700" fill="{accent}" filter="url(#hudglow)">{total_contributions}</text>
  <text x="{PANEL_PAD_X}" y="70" font-family="Consolas, Menlo, monospace" font-size="10" \
fill="#8a7fa8" letter-spacing="1">CONTRIBUTIONS_THIS_CYCLE</text>"""

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
    badges_y = 92
    left_cx = width / 2 - badge_gap / 2 - badge_w / 2
    right_cx = width / 2 + badge_gap / 2 + badge_w / 2
    streak_badges = (
        _streak_badge(left_cx, badges_y, "🔥", "CURRENT STREAK", current_streak, badge_w, badge_h)
        + _streak_badge(right_cx, badges_y, "🏆", "LONGEST STREAK", longest_streak, badge_w, badge_h)
    )

    plane_lap_duration = 7
    plane_y1 = PANEL_PAD_TOP + CITY_HEIGHT * 0.2
    plane_y2 = PANEL_PAD_TOP + CITY_HEIGHT * 0.32
    plane_laps = [
        f"M {city_x0-20:.1f},{plane_y1:.1f} L {city_x0+city_w+20:.1f},{plane_y1-8:.1f}",
        f"M {city_x0+city_w+20:.1f},{plane_y2:.1f} L {city_x0-20:.1f},{plane_y2-8:.1f}",
    ]
    plane_total_dur = plane_lap_duration * len(plane_laps)
    planes = []
    for i, lead in enumerate([0, 3.2]):
        pid = f"plane{i}"
        planes.append(f"""
  <g opacity="0">
    {_chained_motion(pid, plane_laps, plane_lap_duration, lead)}
    {_fade_anim(len(plane_laps), plane_total_dur, -lead)}
    <g>
      {_direction_flip_anim(len(plane_laps), plane_total_dur, -lead, True)}
      {_plane_svg("#e8e6f0")}
    </g>
  </g>""")

    car_lap_duration = 5
    car_y = street_y + 8
    car_laps = [
        f"M {city_x0-15:.1f},{car_y:.1f} L {city_x0+city_w+15:.1f},{car_y:.1f}",
        f"M {city_x0+city_w+15:.1f},{car_y+10:.1f} L {city_x0-15:.1f},{car_y+10:.1f}",
    ]
    car_total_dur = car_lap_duration * len(car_laps)
    cars = []
    for i, (lead, color) in enumerate([(0, "#FF2279"), (2.5, "#00E7FF")]):
        cid = f"car{i}"
        cars.append(f"""
  <g opacity="0">
    {_chained_motion(cid, car_laps, car_lap_duration, lead)}
    {_fade_anim(len(car_laps), car_total_dur, -lead)}
    <g>
      {_direction_flip_anim(len(car_laps), car_total_dur, -lead, True)}
      {_car_svg(color)}
    </g>
  </g>""")

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Neural activity">
  <defs>{glow_filter()}{scan_defs}{glass_defs}{sky_defs}{horizon_defs}{''.join(gradient_defs)}{reflect_defs}</defs>
  <rect width="{width}" height="{height}" rx="16" fill="#{bg}" fill-opacity="0.6"/>
  {number_block}
  {live_chip}
  {active_text}
  {streak_badges}
  {sky_rect}
  {''.join(stars)}
  {horizon_glow}
  {distant_markup}
  {buildings_markup}
  {street_line}
  {reflection}
  {''.join(planes)}
  {''.join(cars)}
  {scan_rect}
  {glass_overlay}
</svg>"""
