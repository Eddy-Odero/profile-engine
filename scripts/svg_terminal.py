"""
svg_terminal.py  — Fixed-size terminal with CSS typewriter reveal.

Uses SVG transform="scale()" on <g> elements for proper column scaling,
while preserving the exact positioning and centering of the original.

No SMIL — all CSS @keyframes for GitHub README compatibility. SMIL
(<animate>/<animateTransform>, the previous approach) has a spottier
long-term browser-support history; CSS @keyframes embedded in <style>
is the more robust choice for something meant to keep working for years
in a README.
"""

from __future__ import annotations

import html

from hud_grid import glass_frame_rect, grid_background
from themes import DEFAULT_THEME, get_theme

# ── Fixed terminal frame ──────────────────────────────────────────────
TERM_WIDTH = 820
TERM_HEIGHT = 420
TITLE_BAR_HEIGHT = 32
PADDING = 16

MAX_CONTENT_HEIGHT = TERM_HEIGHT - TITLE_BAR_HEIGHT - PADDING - 5  # 327

LEFT_COL_RATIO = 0.46
RIGHT_COL_RATIO = 0.54
# These now sum to exactly 1.0 - they used to sum to 0.94, leaving ~6%
# of the usable width as dead space between the two columns that
# neither the ASCII art nor the stats column ever used. Left also
# picked up a bit more of the split, giving the avatar more room to
# scale into (it was rendering smaller than it needed to).
COLUMN_GAP = 20

FONT_SIZE = 13
LINE_HEIGHT = 17
CHAR_WIDTH = FONT_SIZE * 0.6
DESCENDER_MARGIN = 5

TRAFFIC_LIGHT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]
SCAN_BAND_HEIGHT = 50
SCAN_LOOP_SECONDS = 4
GLITCH_LOOP_SECONDS = 6

RIGHT_COL_CHARS = 44
MIN_DOTS = 3

# Print speed: seconds per line
PRINT_DELAY_PER_LINE = 0.06


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _title_bar(width: int, accent: str, username: str) -> str:
    dots = "".join(
        f'<circle cx="{20 + i * 20}" cy="{TITLE_BAR_HEIGHT // 2}" r="6" fill="{c}"/>'
        for i, c in enumerate(TRAFFIC_LIGHT_COLORS)
    )
    label = _esc(f"{username}@github:~")
    return (
        dots
        + f'<text x="{width / 2}" y="{TITLE_BAR_HEIGHT // 2 + 4}" '
        f'font-family="Consolas, Menlo, monospace" font-size="12" '
        f'fill="{accent}" fill-opacity="0.7" text-anchor="middle">{label}</text>'
    )


def _css_block(accent: str, total_lines: int) -> str:
    """CSS animations: scan sweep, cursor blink, glitch jitter, line reveal."""
    h = TERM_HEIGHT
    print_duration = max(total_lines * PRINT_DELAY_PER_LINE + 0.5, SCAN_LOOP_SECONDS)

    css = f"""<style>
  @keyframes scan-sweep {{
    0%   {{ transform: translateY(0); }}
    100% {{ transform: translateY({h + SCAN_BAND_HEIGHT}px); }}
  }}
  @keyframes cursor-blink {{
    0%,49% {{ opacity: 1; }}
    50%,100% {{ opacity: 0; }}
  }}
  @keyframes glitch-jitter {{
    0%,30%  {{ transform: translate(0,0); }}
    31%     {{ transform: translate(2px,0); }}
    32%     {{ transform: translate(-2px,0); }}
    33%,65% {{ transform: translate(0,0); }}
    66%     {{ transform: translate(-1px,0); }}
    67%     {{ transform: translate(1px,0); }}
    68%,100%{{ transform: translate(0,0); }}
  }}
  @keyframes print-line {{
    0%   {{ opacity: 0; }}
    100% {{ opacity: 1; }}
  }}
  .scan-band {{ animation: scan-sweep {SCAN_LOOP_SECONDS}s linear infinite; }}
  .cursor    {{ animation: cursor-blink 1s step-end infinite; animation-delay: {print_duration}s; }}
  .glitch    {{ animation: glitch-jitter {GLITCH_LOOP_SECONDS}s linear infinite; }}
  /* animation-fill-mode: both (not a static opacity:0 rule) is what makes
     this degrade safely. "both" means the animation's own first keyframe
     (opacity:0) only applies WHILE the animation is actually running
     (during its delay + duration). If CSS animation doesn't execute at
     all for any reason, there's no separate static rule holding opacity
     at 0 - text falls back to its normal default (fully opaque), so a
     non-animating renderer shows the complete terminal content instead
     of a blank one. */
  .line      {{ animation: print-line 0.08s ease-out both; }}
"""
    for i in range(total_lines):
        delay = i * PRINT_DELAY_PER_LINE
        css += f"  .line-{i} {{ animation-delay: {delay:.3f}s; }}\n"

    css += "</style>"
    return css


def _scanline_texture(width: int, height: int) -> str:
    return f"""
  <defs>
    <pattern id="scanlines" width="4" height="3" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="black" fill-opacity="0.15"/>
    </pattern>
  </defs>
  <rect x="0" y="{TITLE_BAR_HEIGHT}" width="{width}" height="{height - TITLE_BAR_HEIGHT}" fill="url(#scanlines)"/>"""


def _scan_band(width: int, accent: str) -> str:
    return f"""
  <defs>
    <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{accent}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect class="scan-band" x="0" y="{-SCAN_BAND_HEIGHT}" width="{width}" height="{SCAN_BAND_HEIGHT}" fill="url(#scanGrad)"/>"""


# Brightness ramp used by avatar.py (index = pixel brightness), plus a few
# block characters from the alternate hacker_blocks art.
_RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
_BLOCKS = {"\u2588": 1.0, "\u2593": 0.8, "\u2592": 0.55, "\u2591": 0.3, "\u2584": 0.6, "\u2580": 0.6}
HALFTONE_BUCKETS = 6


def _char_brightness(ch: str) -> float | None:
    if ch in _BLOCKS:
        return _BLOCKS[ch]
    idx = _RAMP.find(ch)
    if idx < 0:
        return None
    return idx / (len(_RAMP) - 1)


def _halftone_rows(avatar_lines: list[str], accent: str) -> list[str] | None:
    """
    Turn the ASCII portrait into a halftone dot matrix (the "Design Beyond
    the Product" hero look): every character cell becomes two stacked dots
    whose area follows that character's brightness, so bright areas get big
    dots and dark areas get none. Dots are drawn as zero-length round-capped
    path segments, grouped by size, which keeps the file small.

    Returns one <g> per source row (so the typewriter reveal still works),
    or None if the art isn't made of ramp characters (e.g. the "avatar
    unavailable" fallback text), in which case the caller draws plain text.
    """
    chars = [c for line in avatar_lines for c in line if not c.isspace()]
    if not chars:
        return None
    known = sum(1 for c in chars if _char_brightness(c) is not None)
    if known / len(chars) < 0.9:
        return None

    cw, ch = CHAR_WIDTH, LINE_HEIGHT
    max_r = cw * 0.52
    rows = []
    for i, line in enumerate(avatar_lines):
        buckets: dict[int, list[str]] = {}
        for j, c in enumerate(line):
            b = _char_brightness(c)
            if b is None or b < 0.07:
                continue
            level = min(HALFTONE_BUCKETS, max(1, round(b**0.8 * HALFTONE_BUCKETS)))
            x = (j + 0.5) * cw
            for frac in (0.25, 0.75):
                y = i * ch + frac * ch
                buckets.setdefault(level, []).append(f"M{x:.1f} {y:.1f}h0")
        paths = "".join(
            f'<path d="{"".join(segs)}" stroke="{accent}" stroke-width="{2 * max_r * (lvl / HALFTONE_BUCKETS) ** 0.5:.2f}" '
            f'stroke-linecap="round" fill="none" stroke-opacity="{0.55 + 0.45 * lvl / HALFTONE_BUCKETS:.2f}"/>'
            for lvl, segs in sorted(buckets.items())
        )
        rows.append(f'<g class="line line-{i}">{paths}</g>')
    return rows


def _dotted_row(key: str, value: str, total_chars: int = RIGHT_COL_CHARS) -> tuple[str, str, str]:
    value = str(value)
    used = len(key) + len(value) + 2
    dots = max(MIN_DOTS, total_chars - used)
    return key, "." * dots, value


def _build_stat_rows(stats: dict) -> list[tuple[str, str]]:
    rows = [
        ("Role", stats.get("role", "")),
        ("Location", stats.get("location", "")),
        ("Repos", stats.get("repo_count", "?")),
        ("Stars", stats.get("stars", "?")),
        ("Followers", stats.get("followers", "?")),
    ]
    top_languages = stats.get("top_languages") or []
    if top_languages:
        rows.append(("Languages", ", ".join(top_languages)))

    solved = stats.get("solved")
    if solved:
        rows.append(("LC Solved", solved.get("total", "?")))
    rating = stats.get("rating")
    rows.append(("LC Rating", rating if rating is not None else "unrated"))

    return rows


def _fit_scale(natural_w: float, natural_h: float, max_w: float, max_h: float) -> float:
    """
    Compute the scale factor that makes content fill as much of the
    (max_w, max_h) box as possible while preserving aspect ratio -
    scaling UP for content smaller than the box, not just down for
    content that overflows it.

    Two real bugs lived here before:
    1. `scale` started at 1.0 and only ever got reduced, never
       increased - so naturally-small ASCII art (fewer rows/cols)
       just rendered small in a mostly-empty box instead of filling
       it, which is the "images appear small" symptom.
    2. A `MIN_SCALE = 0.35` floor clamped how far large/tall art could
       shrink - once the actually-needed scale dropped below that
       floor, the floor won instead of the real fit, so oversized art
       overflowed its column and visually overlapped/crowded the next
       one ("large ones get squished").

    Taking min(max_w/natural_w, max_h/natural_h) with no floor or
    starting cap fixes both: it's always exactly the scale that fits
    the content to the box on its tighter axis, in either direction.
    """
    if natural_w <= 0 or natural_h <= 0:
        return 1.0
    return min(max_w / natural_w, max_h / natural_h)


def render_terminal_svg(
    avatar_ascii: str,
    boot_sequence: str,
    status: str,
    username: str,
    stats: dict,
    theme_name: str = DEFAULT_THEME,
    for_light_mode: bool = False,
) -> str:
    """
    Build a fixed-size 820x380 SVG terminal with typewriter reveal.
    Uses transform="scale()" on <g> for proper scaling while preserving
    the original positioning and centering behavior.
    """
    theme = get_theme(theme_name)
    bg = f"#{theme['label_color']}"
    bg_opacity = 0.96 if for_light_mode else 0.65
    accent = f"#{theme['color']}"

    avatar_lines = avatar_ascii.split("\n")
    boot_lines = boot_sequence.split("\n")
    status_line = f"$ status: {status}"
    stat_rows = _build_stat_rows(stats)

    # ── Layout (matching original exactly) ────────────────────────────
    width = TERM_WIDTH
    height = TERM_HEIGHT
    top_y = TITLE_BAR_HEIGHT + PADDING + FONT_SIZE  # = 61, first baseline

    usable_width = width - 2 * PADDING - COLUMN_GAP
    left_col_w = int(usable_width * LEFT_COL_RATIO)
    right_col_w = int(usable_width * RIGHT_COL_RATIO)
    left_col_x = PADDING
    right_col_x = width - PADDING - right_col_w

    # ── Compute natural heights ───────────────────────────────────────
    avatar_cols = max((len(line) for line in avatar_lines), default=40)
    avatar_rows = len(avatar_lines)
    avatar_natural_w = avatar_cols * CHAR_WIDTH
    avatar_natural_h = avatar_rows * LINE_HEIGHT

    right_row_count = 1 + len(stat_rows) + 1 + len(boot_lines) + 1 + 1
    right_natural_h = right_row_count * LINE_HEIGHT
    right_natural_w = RIGHT_COL_CHARS * CHAR_WIDTH
    # Cap content height, scale taller column if needed
    natural_content_h = max(avatar_natural_h, right_natural_h)
    content_height = min(natural_content_h, MAX_CONTENT_HEIGHT)

    # Scale each column to fit BOTH its column width AND the shared max
    # height - not height alone (see _fit_scale docstring for the bug
    # this fixes).
    avatar_scale = _fit_scale(avatar_natural_w, avatar_natural_h, left_col_w, MAX_CONTENT_HEIGHT)
    right_scale = _fit_scale(right_natural_w, right_natural_h, right_col_w, MAX_CONTENT_HEIGHT)

    # The scale above is driven by the taller axis (there are usually
    # many more lines than the fixed 44-char width would need), which
    # left real horizontal space unused - "a lot of space left on the
    # right frame". Recompute how many characters ACTUALLY fit across
    # the full column width at the final scale, and use that (not the
    # fixed RIGHT_COL_CHARS) for anything that should stretch to fill
    # the row - the dotted fill and the separator line.
    fill_chars = max(RIGHT_COL_CHARS, int(right_col_w / (CHAR_WIDTH * right_scale)))

    scaled_avatar_h = avatar_natural_h * avatar_scale
    scaled_right_h = right_natural_h * right_scale

    # ── Centering (matching original formula) ─────────────────────────
    avatar_y_offset = (content_height - scaled_avatar_h) / 2
    right_y_offset = (content_height - scaled_right_h) / 2

    # ── Build avatar column with transform scaling ────────────────────
    avatar_base_x = left_col_x + (left_col_w - avatar_natural_w * avatar_scale) / 2
    avatar_base_y = top_y + avatar_y_offset - FONT_SIZE * avatar_scale

    halftone = _halftone_rows(avatar_lines, accent)
    avatar_elements = []
    y = FONT_SIZE
    for i, line in enumerate(avatar_lines if halftone is None else []):
        avatar_elements.append(
            f'<text class="line line-{i}" x="0" y="{y:.1f}" filter="url(#glow)" '
            f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" '
            f'fill="{accent}" xml:space="preserve">{_esc(line)}</text>'
        )
        y += LINE_HEIGHT
    if halftone is not None:
        avatar_elements = [f'<g filter="url(#glow)">{"".join(halftone)}</g>']

    # ── Build right column with transform scaling ───────────────────
    right_base_x = right_col_x
    right_base_y = top_y + right_y_offset - FONT_SIZE * right_scale

    line_idx = len(avatar_lines)
    right_elements = []
    y = FONT_SIZE

    right_elements.append(
        f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE}" fill="{accent}" fill-opacity="0.4" xml:space="preserve">'
        f'{"-" * fill_chars}</text>'
    )
    y += LINE_HEIGHT
    line_idx += 1

    stat_value_color = "white"  # back to the original - the dark blue/pink
    # experiments were for the separate stat badges shown after the
    # terminal, not this dotted-row text inside it.
    for key, value in stat_rows:
        k, dots, v = _dotted_row(key, value, total_chars=fill_chars)
        right_elements.append(
            f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" xml:space="preserve">'
            f'<tspan fill="{accent}" font-weight="700">{_esc(k)}</tspan>'
            f'<tspan fill="{accent}" fill-opacity="0.35">{dots}</tspan>'
            f'<tspan fill="{stat_value_color}" fill-opacity="0.9" font-weight="700">{_esc(v)}</tspan></text>'
        )
        y += LINE_HEIGHT
        line_idx += 1

    y += LINE_HEIGHT
    line_idx += 1

    for line in boot_lines:
        if line.startswith("[INFO]"):
            rest = _esc(line[len("[INFO]"):])
            line_markup = (
                f'<tspan fill="#FF4D5A" font-weight="700">[INFO]</tspan>'
                f'<tspan fill="{accent}" fill-opacity="0.55">{rest}</tspan>'
            )
        else:
            line_markup = f'<tspan fill="{accent}" fill-opacity="0.55">{_esc(line)}</tspan>'
        right_elements.append(
            f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" xml:space="preserve">'
            f"{line_markup}</text>"
        )
        y += LINE_HEIGHT
        line_idx += 1

    y += LINE_HEIGHT
    line_idx += 1

    right_elements.append(
        f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE}" xml:space="preserve">'
        f'<tspan fill="{accent}">$ status: </tspan>'
        f'<tspan fill="#FF4D5A" font-weight="700">{_esc(status)}</tspan></text>'
    )
    line_idx += 1

    cursor_x = CHAR_WIDTH * len(status_line)
    cursor_y = y - FONT_SIZE + 2
    cursor = (
        f'<rect class="cursor" x="{cursor_x:.1f}" y="{cursor_y:.1f}" '
        f'width="{CHAR_WIDTH:.1f}" height="{FONT_SIZE + 2:.1f}" '
        f'fill="{accent}"/>'
    )

    total_lines = line_idx
    term_grid_defs, term_grid_rect = grid_background(width, height, accent, spacing=20, rx=10)
    glass_defs, glass_overlay = glass_frame_rect(width, height, accent, rx=10, pattern_id="termglass")

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(username)} terminal">
  {_css_block(accent, total_lines)}
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="0.6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <clipPath id="bodyClip">
      <rect x="0" y="{TITLE_BAR_HEIGHT}" width="{width}" height="{height - TITLE_BAR_HEIGHT}"/>
    </clipPath>
    {term_grid_defs}
    {glass_defs}
  </defs>
  <rect width="{width}" height="{height}" rx="10" fill="{bg}" fill-opacity="{bg_opacity}"/>
  {term_grid_rect}
  {_title_bar(width, accent, username)}
  <g clip-path="url(#bodyClip)">
    <g class="glitch">
      <g transform="translate({avatar_base_x:.1f}, {avatar_base_y:.1f}) scale({avatar_scale:.4f})">
        {''.join(avatar_elements)}
      </g>
      <g transform="translate({right_base_x:.1f}, {right_base_y:.1f}) scale({right_scale:.4f})">
        {''.join(right_elements)}
        {cursor}
      </g>
    </g>
    {_scan_band(width, accent)}
    {_scanline_texture(width, height)}
  </g>
  {glass_overlay}
</svg>"""


# ── Hero layout ("Design Beyond the Product" reference) ──────────────────
HERO_W = 820
HERO_H = 470
HERO_GOLD = "#FFC84D"
HERO_GREEN = "#24FF9A"
HERO_PORTRAIT = (420, 30, 380, 410)  # x, y, w, h box the halftone portrait is fitted into


def _wrap_words(text: str, max_chars: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines


def _hero_frame(w: int, h: int, c: float = 16, notch: float = 7) -> str:
    """Notched HUD outline: cut corners plus small notches on both sides, as in the reference."""
    m = 8
    y1, y2 = h * 0.30, h * 0.72
    pts = [
        (m + c, m), (w - m - c, m), (w - m, m + c),
        (w - m, y1), (w - m - notch, y1 + 12), (w - m - notch, y1 + 36), (w - m, y1 + 48),
        (w - m, y2), (w - m - notch, y2 + 12), (w - m - notch, y2 + 36), (w - m, y2 + 48),
        (w - m, h - m - c), (w - m - c, h - m), (m + c, h - m), (m, h - m - c),
        (m, y2 + 48), (m + notch, y2 + 36), (m + notch, y2 + 12), (m, y2),
        (m, y1 + 48), (m + notch, y1 + 36), (m + notch, y1 + 12), (m, y1),
        (m, m + c),
    ]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def _hero_button(x: float, y: float, w: float, label: str, primary: bool) -> str:
    c, h = 8, 40
    pts = f"{c},0 {w},0 {w},{h - c} {w - c},{h} 0,{h} 0,{c}"
    if primary:
        fill, stroke, ink = HERO_GOLD, HERO_GOLD, "#07090F"
    else:
        fill, stroke, ink = "#0b0f18", "#ffffff", "#ffffff"
    return (
        f'<g transform="translate({x},{y})"><polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
        f'stroke-opacity="{1 if primary else 0.3}" stroke-width="1.2"/>'
        f'<text x="{w / 2}" y="{h / 2 + 4.5}" font-family="Arial, Helvetica, sans-serif" font-size="12" '
        f'font-weight="700" fill="{ink}" text-anchor="middle" letter-spacing="1">{_esc(label)}</text></g>'
    )


def render_hero_svg(
    avatar_ascii: str,
    status: str,
    username: str,
    stats: dict,
    theme_name: str = DEFAULT_THEME,
    for_light_mode: bool = False,
) -> str:
    """
    The README's top section in the "Design Beyond the Product" layout:
    corner-tagged role, big two-tone headline, paragraph and notched
    buttons on the left, the halftone ASCII portrait on the right, a
    notched HUD frame, and a status line along the bottom. The navigation
    bar from the reference is left out. Buttons here are decorative (an
    SVG shown as an image can't hold links); the real links are in the
    Signal Uplink section.
    """
    theme = get_theme(theme_name)
    bg = f"#{theme['label_color']}"
    bg_opacity = 0.96 if for_light_mode else 0.65
    accent = f"#{theme['color']}"
    role = stats.get("role", "Full-Stack Developer")
    location = stats.get("location", "")

    w, h = HERO_W, HERO_H
    lx = 52

    # Portrait: fit the art into its box, bottom-aligned, then fade the edges.
    avatar_lines = avatar_ascii.split("\n")
    halftone = _halftone_rows(avatar_lines, accent)
    px, py, pw, ph = HERO_PORTRAIT
    cols = max((len(l) for l in avatar_lines), default=40)
    nat_w, nat_h = cols * CHAR_WIDTH, len(avatar_lines) * LINE_HEIGHT
    sc = _fit_scale(nat_w, nat_h, pw, ph)
    ax = px + (pw - nat_w * sc) / 2
    ay = py + (ph - nat_h * sc)
    if halftone is None:
        portrait = ""
    else:
        # The portrait is defined once and drawn several times: the base, a
        # magenta and a white ghost that flash apart for a split second, and
        # a horizontal slice that slips sideways - the glitch burst.
        band_y = py + ph * 0.36
        portrait = (
            f'<defs><g id="ptsrc"><g transform="translate({ax:.1f},{ay:.1f}) scale({sc:.4f})" '
            f'filter="url(#glow)">{"".join(halftone)}</g></g>'
            f'<filter id="tintM"><feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 0.15  0 0 0 0 0.55  0 0 0 1 0"/></filter>'
            f'<filter id="tintW"><feColorMatrix type="matrix" values="0 0 0 0 0.85  0 0 0 0 1  0 0 0 0 1  0 0 0 1 0"/></filter>'
            f'<clipPath id="sliceClip"><rect x="{px}" y="{band_y:.0f}" width="{pw}" height="34"/></clipPath></defs>'
            f'<g mask="url(#fade)"><g class="glitch"><use href="#ptsrc"/>'
            f'<use href="#ptsrc" class="ghost-m" filter="url(#tintM)"/>'
            f'<use href="#ptsrc" class="ghost-w" filter="url(#tintW)"/>'
            f'<g clip-path="url(#sliceClip)"><use href="#ptsrc" class="slice"/></g></g></g>'
        )

    para = _wrap_words(
        f"I am a {role.lower()} from {location}. I build fast Go backends, clean interfaces and "
        f"tools that ship, from hackathon sprints to production systems.",
        56,
    )
    para_svg = "".join(
        f'<text x="{lx}" y="{286 + i * 19}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="12.5" fill="#c9c9d3">{_esc(line)}</text>'
        for i, line in enumerate(para)
    )
    btn_y = 286 + len(para) * 19 + 12

    tag_w = len(role) * 8 + 24
    n = 6
    tag = (
        f'<path d="M{lx} {86 + n} V86 H{lx + n} M{lx + tag_w - n} 86 H{lx + tag_w} V{86 + n} '
        f'M{lx + tag_w} {112 - n} V112 H{lx + tag_w - n} M{lx + n} 112 H{lx} V{112 - n}" fill="none" '
        f'stroke="{HERO_GOLD}" stroke-width="1.3"/>'
        f'<text x="{lx + tag_w / 2}" y="103" font-family="Consolas, Menlo, monospace" font-size="11.5" '
        f'fill="{HERO_GOLD}" text-anchor="middle" letter-spacing="1.5">{_esc(role.upper())}</text>'
    )

    hx = 22
    logo = (
        f'<polygon points="{lx + 9},34 {lx + 18},39 {lx + 18},49 {lx + 9},54 {lx},49 {lx},39" fill="none" '
        f'stroke="{HERO_GOLD}" stroke-width="2"/><circle cx="{lx + 9}" cy="44" r="3" fill="{HERO_GOLD}"/>'
        f'<text x="{lx + 28}" y="49" font-family="Consolas, Menlo, monospace" font-size="14" font-weight="700" '
        f'fill="white" letter-spacing="3">{_esc(username.upper())}</text>'
    )

    by = h - 38
    status_bar = (
        f'<circle cx="{lx + 3}" cy="{by}" r="3.5" fill="{HERO_GREEN}"/>'
        f'<text x="{lx + 15}" y="{by + 4}" font-family="Arial, Helvetica, sans-serif" font-size="11.5" '
        f'fill="{HERO_GREEN}">STATUS:</text>'
        f'<text x="{lx + 66}" y="{by + 4}" font-family="Arial, Helvetica, sans-serif" font-size="11.5" '
        f'fill="white">{_esc(status.upper())}</text>'
        f'<rect x="{lx + 66 + len(status) * 8 + 18}" y="{by - 0.5}" width="150" height="1" fill="white" fill-opacity="0.35"/>'
        f'<text x="{w - 52}" y="{by + 4}" font-family="Arial, Helvetica, sans-serif" font-size="11.5" '
        f'fill="#6b7a8c" text-anchor="end">SCROLL TO EXPLORE  &#8964;</text>'
    )

    grid_defs, grid_rect = grid_background(w, h, accent, spacing=20, rx=10)
    n_rows = len(avatar_lines)
    reveal = "".join(f"  .line-{i} {{ animation-delay: {i * 0.05:.2f}s; }}\n" for i in range(n_rows))
    css = f"""<style>
  @keyframes scan-sweep {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY({h + SCAN_BAND_HEIGHT}px); }} }}
  @keyframes print-line {{ 0% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
  .scan-band {{ animation: scan-sweep {SCAN_LOOP_SECONDS}s linear infinite; }}
  .line {{ animation: print-line 0.08s ease-out both; }}
  @keyframes gl-main {{ 0%,86% {{ transform: translate(0,0); }} 87% {{ transform: translate(4px,0); }} 88% {{ transform: translate(-4px,1px); }} 89% {{ transform: translate(3px,-1px); }} 90%,93% {{ transform: translate(0,0); }} 94% {{ transform: translate(-2px,0); }} 95%,100% {{ transform: translate(0,0); }} }}
  @keyframes gl-m {{ 0%,86% {{ opacity: 0; }} 87%,90% {{ opacity: 0.75; transform: translate(-6px,0); }} 91%,93% {{ opacity: 0; }} 94% {{ opacity: 0.6; transform: translate(5px,0); }} 95%,100% {{ opacity: 0; }} }}
  @keyframes gl-w {{ 0%,86% {{ opacity: 0; }} 87%,90% {{ opacity: 0.55; transform: translate(6px,0); }} 91%,100% {{ opacity: 0; }} }}
  @keyframes gl-s {{ 0%,87% {{ opacity: 0; transform: translate(0,0); }} 88% {{ opacity: 1; transform: translate(14px,0); }} 89% {{ opacity: 1; transform: translate(-10px,0); }} 90%,100% {{ opacity: 0; transform: translate(0,0); }} }}
  .glitch {{ animation: gl-main {GLITCH_LOOP_SECONDS}s linear infinite; }}
  .ghost-m {{ animation: gl-m {GLITCH_LOOP_SECONDS}s linear infinite; opacity: 0; }}
  .ghost-w {{ animation: gl-w {GLITCH_LOOP_SECONDS}s linear infinite; opacity: 0; }}
  .slice {{ animation: gl-s {GLITCH_LOOP_SECONDS}s linear infinite; opacity: 0; }}
{reveal}</style>"""

    return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" \
role="img" aria-label="{_esc(username)} profile">
  {css}
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="0.6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <radialGradient id="fadeGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0.55" stop-color="white"/><stop offset="1" stop-color="black"/>
    </radialGradient>
    <mask id="fade" maskUnits="userSpaceOnUse" x="{px}" y="{py}" width="{pw}" height="{ph}">
      <rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="url(#fadeGrad)"/>
    </mask>
    <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{accent}" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="heroClip"><polygon points="{_hero_frame(w, h)}"/></clipPath>
    {grid_defs}
  </defs>
  <rect width="{w}" height="{h}" rx="10" fill="{bg}" fill-opacity="{bg_opacity}"/>
  {grid_rect}
  <polygon points="{_hero_frame(w, h)}" fill="none" stroke="{HERO_GOLD}" stroke-opacity="0.45" stroke-width="1.2"/>
  {logo}
  {tag}
  <text x="{lx}" y="158" font-family="Arial, Helvetica, sans-serif" font-size="44" font-weight="800" \
fill="white" letter-spacing="0.5">BUILD BEYOND</text>
  <text x="{lx}" y="204" font-family="Arial, Helvetica, sans-serif" font-size="44" font-weight="800" \
fill="white" letter-spacing="0.5">THE BASICS</text>
  <text x="{lx}" y="250" font-family="Arial, Helvetica, sans-serif" font-size="44" font-weight="800" \
fill="{HERO_GOLD}" letter-spacing="0.5">SHIP IT</text>
  {para_svg}
  {portrait}
  {status_bar}
  <g clip-path="url(#heroClip)">
    <rect class="scan-band" x="0" y="{-SCAN_BAND_HEIGHT}" width="{w}" height="{SCAN_BAND_HEIGHT}" fill="url(#scanGrad)"/>
  </g>
</svg>"""
