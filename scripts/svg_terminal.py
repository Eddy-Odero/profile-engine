"""
svg_terminal.py  (real colored terminal visual - neofetch-style two-column layout)

Everything else in this project - the ASCII avatar, CRT text-noise
effects, the boot sequence - is plain text, and GitHub renders code-block
text as flat monospace with no color. Shields.io badges (Phase 8) added
some color, but only for stat pills, not the terminal window itself.

Layout is deliberately modeled on the classic `neofetch` terminal tool
(and profiles that borrow its look, e.g. Andrew6rant/Andrew6rant): the
ASCII avatar sits on the left, unchanged, and a dotted key/value info
panel sits to its right - role, location, and stats aligned with dot
leaders, the same visual language as neofetch's OS/Shell/Uptime rows.
The boot log and status line move into that same right column, below
the stats.

Real, continuous SVG animation (not per-build text randomization):
a static scanline texture, a scan-glow band that sweeps top-to-bottom
on a loop, an occasional glitch jitter on the whole body, and a real
blinking cursor - all via SVG's native <animate>/<animateTransform>
(SMIL), so they play continuously in a browser. Since the README embeds
this as a same-repo relative path, GitHub serves it as a raw file rather
than routing it through its script-stripping image proxy (that's for
external URLs), so the animation survives.

Usage:
    from svg_terminal import render_terminal_svg
    svg_markup = render_terminal_svg(
        avatar_ascii, boot_sequence, status, username, stats, theme_name)
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

FONT_SIZE = 13
LINE_HEIGHT = 17
CHAR_WIDTH = FONT_SIZE * 0.6
PADDING = 16
TITLE_BAR_HEIGHT = 32
DESCENDER_MARGIN = 5  # room for characters like g/y/j that dip below the baseline
TRAFFIC_LIGHT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]
SCAN_BAND_HEIGHT = 50
SCAN_LOOP_SECONDS = 4
GLITCH_LOOP_SECONDS = 6
COLUMN_GAP = 28
RIGHT_COL_CHARS = 44  # neofetch-style column width, in characters, for dot-leader alignment
MIN_DOTS = 3
MAX_HEIGHT_RATIO = 1.05  # scale taller column if more than 5% taller than the other


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


def _scanline_texture(width: int, height: int) -> str:
    """Static repeating pattern of thin dark lines - the CRT scanline texture."""
    return f"""
  <defs>
    <pattern id="scanlines" width="4" height="3" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="black" fill-opacity="0.15"/>
    </pattern>
  </defs>
  <rect x="0" y="{TITLE_BAR_HEIGHT}" width="{width}" height="{height - TITLE_BAR_HEIGHT}" fill="url(#scanlines)"/>"""


def _scan_band(width: int, height: int, accent: str) -> str:
    """A soft light band that continuously sweeps top-to-bottom, like a CRT beam."""
    return f"""
  <defs>
    <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{accent}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0" y="{-SCAN_BAND_HEIGHT}" width="{width}" height="{SCAN_BAND_HEIGHT}" fill="url(#scanGrad)">
    <animate attributeName="y" values="{-SCAN_BAND_HEIGHT};{height}" dur="{SCAN_LOOP_SECONDS}s" repeatCount="indefinite"/>
  </rect>"""


def _glitch_jitter() -> str:
    """A brief horizontal jump applied to the whole body, twice per loop."""
    return (
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;0 0;2 0;-2 0;0 0;0 0;0 0;0 0;-1 0;1 0;0 0;0 0" '
        'keyTimes="0;0.30;0.31;0.32;0.33;0.34;0.65;0.66;0.67;0.68;0.69;1" '
        f'dur="{GLITCH_LOOP_SECONDS}s" repeatCount="indefinite"/>'
    )


def _dotted_row(key: str, value: str, total_chars: int = RIGHT_COL_CHARS) -> tuple[str, str, str]:
    """Split a key/value pair into (key, dot-leader, value) sized to align at total_chars."""
    value = str(value)
    used = len(key) + len(value) + 2
    dots = max(MIN_DOTS, total_chars - used)
    return key, "." * dots, value


def _build_stat_rows(stats: dict) -> list[tuple[str, str]]:
    """Turn the stats dict into an ordered list of (key, value) pairs for the dotted panel."""
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
    Build the SVG markup for the terminal window: ASCII avatar on the
    left, a neofetch-style dotted key/value panel + boot log + status
    on the right. Returns a full <svg>...</svg> string.
    """
    theme = get_theme(theme_name)
    bg = f"#{theme['label_color']}"
    accent = f"#{theme['color']}"

    avatar_lines = avatar_ascii.split("\n")
    avatar_cols = max((len(line) for line in avatar_lines), default=40)
    avatar_col_width = avatar_cols * CHAR_WIDTH

    boot_lines = boot_sequence.split("\n")
    status_line = f"$ status: {status}"
    stat_rows = _build_stat_rows(stats)

    # Right column row count: separator + stat rows + blank + boot lines + blank + status
    right_row_count = 1 + len(stat_rows) + 1 + len(boot_lines) + 1 + 1
    right_col_width = RIGHT_COL_CHARS * CHAR_WIDTH

    # --- Height balancing: scale the taller column to match the shorter one ---
    natural_avatar_h = len(avatar_lines) * LINE_HEIGHT
    natural_right_h = right_row_count * LINE_HEIGHT

    avatar_scale = 1.0
    right_scale = 1.0

    if natural_avatar_h > natural_right_h * MAX_HEIGHT_RATIO:
        avatar_scale = natural_right_h / natural_avatar_h
        content_height = natural_right_h
    elif natural_right_h > natural_avatar_h * MAX_HEIGHT_RATIO:
        right_scale = natural_avatar_h / natural_right_h
        content_height = natural_avatar_h
    else:
        content_height = max(natural_avatar_h, natural_right_h)

    scaled_avatar_h = natural_avatar_h * avatar_scale
    scaled_right_h = natural_right_h * right_scale

    width = int(PADDING + avatar_col_width + COLUMN_GAP + right_col_width + PADDING)
    height = int(TITLE_BAR_HEIGHT + PADDING + content_height + PADDING + DESCENDER_MARGIN)

    avatar_x = PADDING
    right_x = PADDING + avatar_col_width + COLUMN_GAP
    top_y = TITLE_BAR_HEIGHT + PADDING + FONT_SIZE

    # --- Left column: the ASCII avatar, vertically centered ---
    avatar_y_offset = (content_height - scaled_avatar_h) / 2
    avatar_elements = []
    y = top_y + avatar_y_offset
    for line in avatar_lines:
        avatar_elements.append(
            f'<text x="{avatar_x}" y="{y:.1f}" filter="url(#glow)" '
            f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" '
            f'fill="{accent}" xml:space="preserve">{_esc(line)}</text>'
        )
        y += LINE_HEIGHT

    # Compute transform to scale avatar around its center (if scaling is needed)
    avatar_transform = ""
    if avatar_scale != 1.0:
        avatar_cx = avatar_x + avatar_col_width / 2
        avatar_cy = top_y + avatar_y_offset + scaled_avatar_h / 2
        avatar_transform = (
            f' transform="translate({avatar_cx:.1f}, {avatar_cy:.1f}) '
            f'scale(1, {avatar_scale:.4f}) '
            f'translate({-avatar_cx:.1f}, {-avatar_cy:.1f})"'
        )

    # --- Right column: separator, dotted stats, boot log, status ---
    right_elements = []
    right_y_offset = (content_height - scaled_right_h) / 2
    y = top_y + right_y_offset

    right_elements.append(
        f'<text x="{right_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE}" fill="{accent}" fill-opacity="0.4" xml:space="preserve">'
        f'{"-" * RIGHT_COL_CHARS}</text>'
    )
    y += LINE_HEIGHT

    for key, value in stat_rows:
        k, dots, v = _dotted_row(key, value)
        right_elements.append(
            f'<text x="{right_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" xml:space="preserve">'
            f'<tspan fill="{accent}" font-weight="700">{_esc(k)}</tspan>'
            f'<tspan fill="{accent}" fill-opacity="0.35">{dots}</tspan>'
            f'<tspan fill="white" fill-opacity="0.9">{_esc(v)}</tspan></text>'
        )
        y += LINE_HEIGHT

    y += LINE_HEIGHT  # blank spacer

    for line in boot_lines:
        right_elements.append(
            f'<text x="{right_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" fill="{accent}" fill-opacity="0.55" xml:space="preserve">'
            f"{_esc(line)}</text>"
        )
        y += LINE_HEIGHT

    y += LINE_HEIGHT  # blank spacer

    right_elements.append(
        f'<text x="{right_x}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" '
        f'font-size="{FONT_SIZE}" fill="{accent}" xml:space="preserve">{_esc(status_line)}</text>'
    )
    status_baseline_y = y

    # Compute right-column transform (if scaling is needed)
    right_transform = ""
    if right_scale != 1.0:
        right_cx = right_x + right_col_width / 2
        right_cy = top_y + right_y_offset + scaled_right_h / 2
        right_transform = (
            f' transform="translate({right_cx:.1f}, {right_cy:.1f}) '
            f'scale(1, {right_scale:.4f}) '
            f'translate({-right_cx:.1f}, {-right_cy:.1f})"'
        )

    cursor_x = right_x + CHAR_WIDTH * len(status_line)
    cursor_y = status_baseline_y - FONT_SIZE + 2
    cursor = (
        f'<rect x="{cursor_x:.1f}" y="{cursor_y:.1f}" width="{CHAR_WIDTH:.1f}" '
        f'height="{FONT_SIZE + 2}" fill="{accent}">'
        '<animate attributeName="opacity" values="1;1;0;0" '
        'keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
        "</rect>"
    )

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(username)} terminal">
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
    <g>
      <g{avatar_transform}>
        {''.join(avatar_elements)}
      </g>
      <g{right_transform}>
        {''.join(right_elements)}
      </g>
      {cursor}
      {_glitch_jitter()}
    </g>
    {_scan_band(width, height, accent)}
    {_scanline_texture(width, height)}
  </g>
</svg>"""