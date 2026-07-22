"""
svg_terminal.py  — Fixed-size terminal with CSS animations for GitHub README compatibility.

Replaces SMIL (<animate>, <animateTransform>) with CSS @keyframes inside the SVG <style> tag.
GitHub's SVG sanitizer strips scripts and sometimes SMIL, but typically preserves CSS.

The terminal is a fixed 820×380px frame. Both ASCII avatar and text stats are
independently scaled to fit their allocated column boxes. Content never overflows
and the frame size is constant regardless of input.
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

# ── Fixed terminal frame ──────────────────────────────────────────────
TERM_WIDTH = 820
TERM_HEIGHT = 380
TITLE_BAR_HEIGHT = 32
PADDING = 16

# Column widths as ratios of the body area (width minus padding/gap)
LEFT_COL_RATIO = 0.42
RIGHT_COL_RATIO = 0.52
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

# Minimum scale so text stays readable even for huge ASCII art
MIN_SCALE = 0.35


def _esc(text: str) -> str:
    """Escape text for safe placement inside SVG <text> content."""
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


def _css_block(accent: str) -> str:
    """CSS animations inside the SVG. GitHub typically preserves these."""
    h = TERM_HEIGHT
    return f"""<style>
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
  .scan-band {{ animation: scan-sweep {SCAN_LOOP_SECONDS}s linear infinite; }}
  .cursor    {{ animation: cursor-blink 1s step-end infinite; }}
  .glitch    {{ animation: glitch-jitter {GLITCH_LOOP_SECONDS}s linear infinite; }}
</style>"""


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


def render_terminal_svg(
    avatar_ascii: str,
    boot_sequence: str,
    status: str,
    username: str,
    stats: dict,
    theme_name: str = DEFAULT_THEME,
) -> str:
    """
    Build a fixed-size 820×380 SVG terminal.

    Avatar and stats are independently scaled to fit their column boxes.
    Uses CSS animations for GitHub README compatibility.
    """
    theme = get_theme(theme_name)
    bg = f"#{theme['label_color']}"
    accent = f"#{theme['color']}"

    avatar_lines = avatar_ascii.split("\n")
    boot_lines = boot_sequence.split("\n")
    status_line = f"$ status: {status}"
    stat_rows = _build_stat_rows(stats)

    # ── Layout geometry ───────────────────────────────────────────────
    width = TERM_WIDTH
    height = TERM_HEIGHT
    body_top = TITLE_BAR_HEIGHT + PADDING
    body_height = height - TITLE_BAR_HEIGHT - PADDING - DESCENDER_MARGIN

    usable_width = width - 2 * PADDING - COLUMN_GAP
    left_col_w = int(usable_width * LEFT_COL_RATIO)
    right_col_w = int(usable_width * RIGHT_COL_RATIO)
    left_col_x = PADDING
    right_col_x = width - PADDING - right_col_w

    # ── Scale avatar to fit left column box ───────────────────────────
    avatar_cols = max((len(line) for line in avatar_lines), default=40)
    avatar_rows = len(avatar_lines)
    avatar_natural_w = avatar_cols * CHAR_WIDTH
    avatar_natural_h = avatar_rows * LINE_HEIGHT

    scale_x = left_col_w / avatar_natural_w if avatar_natural_w > 0 else 1
    scale_y = body_height / avatar_natural_h if avatar_natural_h > 0 else 1
    avatar_scale = max(min(scale_x, scale_y), MIN_SCALE)

    scaled_avatar_w = avatar_natural_w * avatar_scale
    scaled_avatar_h = avatar_natural_h * avatar_scale

    avatar_offset_x = left_col_x + (left_col_w - scaled_avatar_w) / 2
    avatar_offset_y = body_top + (body_height - scaled_avatar_h) / 2

    avatar_elements = []
    for i, line in enumerate(avatar_lines):
        y = avatar_offset_y + (i + 1) * LINE_HEIGHT * avatar_scale
        avatar_elements.append(
            f'<text x="{avatar_offset_x:.1f}" y="{y:.1f}" filter="url(#glow)" '
            f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE * avatar_scale:.1f}" '
            f'fill="{accent}" xml:space="preserve">{_esc(line)}</text>'
        )

    # ── Scale right column to fit right column box ────────────────────
    right_row_count = 1 + len(stat_rows) + 1 + len(boot_lines) + 1 + 1
    right_natural_h = right_row_count * LINE_HEIGHT
    right_scale = max(body_height / right_natural_h, MIN_SCALE) if right_natural_h > 0 else 1

    scaled_right_h = right_natural_h * right_scale
    right_offset_y = body_top + (body_height - scaled_right_h) / 2

    right_elements = []
    y = right_offset_y

    # Separator
    right_elements.append(
        f'<text x="{right_col_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE * right_scale:.1f}" fill="{accent}" fill-opacity="0.4" xml:space="preserve">'
        f'{"-" * RIGHT_COL_CHARS}</text>'
    )
    y += LINE_HEIGHT * right_scale

    # Stat rows
    for key, value in stat_rows:
        k, dots, v = _dotted_row(key, value)
        right_elements.append(
            f'<text x="{right_col_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE * right_scale:.1f}" xml:space="preserve">'
            f'<tspan fill="{accent}" font-weight="700">{_esc(k)}</tspan>'
            f'<tspan fill="{accent}" fill-opacity="0.35">{dots}</tspan>'
            f'<tspan fill="white" fill-opacity="0.9">{_esc(v)}</tspan></text>'
        )
        y += LINE_HEIGHT * right_scale

    y += LINE_HEIGHT * right_scale  # spacer

    for line in boot_lines:
        right_elements.append(
            f'<text x="{right_col_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE * right_scale:.1f}" fill="{accent}" fill-opacity="0.55" xml:space="preserve">'
            f"{_esc(line)}</text>"
        )
        y += LINE_HEIGHT * right_scale

    y += LINE_HEIGHT * right_scale  # spacer

    right_elements.append(
        f'<text x="{right_col_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE * right_scale:.1f}" fill="{accent}" xml:space="preserve">{_esc(status_line)}</text>'
    )
    status_baseline_y = y

    # Cursor
    cursor_x = right_col_x + CHAR_WIDTH * right_scale * len(status_line)
    cursor_y = status_baseline_y - FONT_SIZE * right_scale + 2
    cursor = (
        f'<rect class="cursor" x="{cursor_x:.1f}" y="{cursor_y:.1f}" '
        f'width="{CHAR_WIDTH * right_scale:.1f}" height="{FONT_SIZE * right_scale + 2:.1f}" '
        f'fill="{accent}"/>'
    )

    # ── Assemble SVG ────────────────────────────────────────────────────
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(username)} terminal">
  {_css_block(accent)}
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
  </defs>
  <rect width="{width}" height="{height}" rx="10" fill="{bg}"/>
  {_title_bar(width, accent, username)}
  <g clip-path="url(#bodyClip)">
    <g class="glitch">
      {''.join(avatar_elements)}
      {''.join(right_elements)}
      {cursor}
    </g>
    {_scan_band(width, accent)}
    {_scanline_texture(width, height)}
  </g>
</svg>"""