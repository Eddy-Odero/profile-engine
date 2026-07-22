"""
svg_terminal.py  — Fixed-size terminal with CSS typewriter reveal.

Uses SVG transform with center-origin scaling to prevent clipping.
Content is scaled from its center point, not from (0,0).

No SMIL — all CSS @keyframes for GitHub README compatibility.
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

# ── Fixed terminal frame ──────────────────────────────────────────────
TERM_WIDTH = 820
TERM_HEIGHT = 380
TITLE_BAR_HEIGHT = 32
PADDING = 16

MAX_CONTENT_HEIGHT = TERM_HEIGHT - TITLE_BAR_HEIGHT - PADDING - 5  # 327

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
MIN_SCALE = 0.35

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
  .line      {{ opacity: 0; animation: print-line 0.08s ease-out forwards; }}
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
    Build a fixed-size 820x380 SVG terminal with typewriter reveal.
    Uses center-origin scaling to prevent clipping.
    """
    theme = get_theme(theme_name)
    bg = f"#{theme['label_color']}"
    accent = f"#{theme['color']}"

    avatar_lines = avatar_ascii.split("\n")
    boot_lines = boot_sequence.split("\n")
    status_line = f"$ status: {status}"
    stat_rows = _build_stat_rows(stats)

    # ── Layout ────────────────────────────────────────────────────────
    width = TERM_WIDTH
    height = TERM_HEIGHT
    top_y = TITLE_BAR_HEIGHT + PADDING + FONT_SIZE  # = 61

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

    # Cap content height, scale taller column if needed
    natural_content_h = max(avatar_natural_h, right_natural_h)
    content_height = min(natural_content_h, MAX_CONTENT_HEIGHT)

    avatar_scale = 1.0
    right_scale = 1.0

    if avatar_natural_h > MAX_CONTENT_HEIGHT:
        avatar_scale = MAX_CONTENT_HEIGHT / avatar_natural_h
    if right_natural_h > MAX_CONTENT_HEIGHT:
        right_scale = MAX_CONTENT_HEIGHT / right_natural_h

    avatar_scale = max(avatar_scale, MIN_SCALE)
    right_scale = max(right_scale, MIN_SCALE)

    scaled_avatar_h = avatar_natural_h * avatar_scale
    scaled_right_h = right_natural_h * right_scale

    # ── Centering ─────────────────────────────────────────────────────
    avatar_y_offset = (content_height - scaled_avatar_h) / 2
    right_y_offset = (content_height - scaled_right_h) / 2

    # ── Build avatar column ───────────────────────────────────────────
    # Center-origin scaling: translate to center, scale, translate back
    avatar_cx = avatar_natural_w / 2  # center of content (natural coords)
    avatar_cy = avatar_natural_h / 2

    # Where the center should be in absolute space:
    avatar_center_x = left_col_x + left_col_w / 2
    avatar_center_y = top_y + avatar_y_offset + scaled_avatar_h / 2 - FONT_SIZE * avatar_scale / 2

    # Simpler: position the group so the visual center aligns
    # The content spans from y=FONT_SIZE to y=avatar_natural_h+FONT_SIZE in natural coords
    # We want the middle of this span to be at top_y + avatar_y_offset + scaled_avatar_h/2
    avatar_base_x = left_col_x + (left_col_w - avatar_natural_w * avatar_scale) / 2
    avatar_base_y = top_y + avatar_y_offset

    # Use center-origin transform:
    # translate(base_x + cx*scale, base_y + cy*scale) scale(s) translate(-cx, -cy)
    # But actually simpler: just position the group at the right place
    # and let the content be at natural coords. The scale shrinks toward (0,0).
    # To shrink toward center: translate(cx, cy) scale(s) translate(-cx, -cy)
    # Then position the result.

    # Actually the cleanest: content is at natural coords with origin at top-left
    # We want to scale it from its center. So:
    # 1. Move origin to center of content: translate(-cx, -cy)
    # 2. Scale: scale(s)
    # 3. Move back to where center should be: translate(target_x, target_y)

    avatar_target_cx = left_col_x + left_col_w / 2
    avatar_target_cy = top_y + avatar_y_offset + scaled_avatar_h / 2

    avatar_transform = (
        f'translate({avatar_target_cx:.1f} {avatar_target_cy:.1f}) '
        f'scale({avatar_scale:.4f}) '
        f'translate({-avatar_cx:.1f} {-avatar_cy:.1f})'
    )

    avatar_elements = []
    y = FONT_SIZE
    for i, line in enumerate(avatar_lines):
        avatar_elements.append(
            f'<text class="line line-{i}" x="0" y="{y:.1f}" filter="url(#glow)" '
            f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" '
            f'fill="{accent}" xml:space="preserve">{_esc(line)}</text>'
        )
        y += LINE_HEIGHT

    # ── Build right column ────────────────────────────────────────────
    right_cx = right_col_w / 2  # approximate center (dot leaders vary slightly)
    right_cy = right_natural_h / 2

    right_target_cx = right_col_x + right_col_w / 2
    right_target_cy = top_y + right_y_offset + scaled_right_h / 2

    right_transform = (
        f'translate({right_target_cx:.1f} {right_target_cy:.1f}) '
        f'scale({right_scale:.4f}) '
        f'translate({-right_cx:.1f} {-right_cy:.1f})'
    )

    line_idx = len(avatar_lines)
    right_elements = []
    y = FONT_SIZE

    right_elements.append(
        f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE}" fill="{accent}" fill-opacity="0.4" xml:space="preserve">'
        f'{"-" * RIGHT_COL_CHARS}</text>'
    )
    y += LINE_HEIGHT
    line_idx += 1

    for key, value in stat_rows:
        k, dots, v = _dotted_row(key, value)
        right_elements.append(
            f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" xml:space="preserve">'
            f'<tspan fill="{accent}" font-weight="700">{_esc(k)}</tspan>'
            f'<tspan fill="{accent}" fill-opacity="0.35">{dots}</tspan>'
            f'<tspan fill="white" fill-opacity="0.9">{_esc(v)}</tspan></text>'
        )
        y += LINE_HEIGHT
        line_idx += 1

    y += LINE_HEIGHT
    line_idx += 1

    for line in boot_lines:
        right_elements.append(
            f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" fill="{accent}" fill-opacity="0.55" xml:space="preserve">'
            f"{_esc(line)}</text>"
        )
        y += LINE_HEIGHT
        line_idx += 1

    y += LINE_HEIGHT
    line_idx += 1

    right_elements.append(
        f'<text class="line line-{line_idx}" x="0" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE}" fill="{accent}" xml:space="preserve">{_esc(status_line)}</text>'
    )
    line_idx += 1

    # Cursor (positioned relative to status line in natural coords)
    cursor_x = CHAR_WIDTH * len(status_line)
    cursor_y = y - FONT_SIZE + 2
    cursor = (
        f'<rect class="cursor" x="{cursor_x:.1f}" y="{cursor_y:.1f}" '
        f'width="{CHAR_WIDTH:.1f}" height="{FONT_SIZE + 2:.1f}" '
        f'fill="{accent}"/>'
    )

    total_lines = line_idx

    # ── Assemble SVG ────────────────────────────────────────────────────
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
  </defs>
  <rect width="{width}" height="{height}" rx="10" fill="{bg}"/>
  {_title_bar(width, accent, username)}
  <g clip-path="url(#bodyClip)">
    <g class="glitch">
      <!-- Avatar column with center-origin scaling -->
      <g transform="{avatar_transform}">
        {''.join(avatar_elements)}
      </g>
      <!-- Right column with center-origin scaling -->
      <g transform="{right_transform}">
        {''.join(right_elements)}
        {cursor}
      </g>
    </g>
    {_scan_band(width, accent)}
    {_scanline_texture(width, height)}
  </g>
</svg>"""
