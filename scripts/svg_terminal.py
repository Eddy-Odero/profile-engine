"""
svg_terminal.py  (real colored terminal visual)

Everything else in this project - the ASCII avatar, CRT text-noise
effects, the boot sequence - is plain text, and GitHub renders code-block
text as flat monospace with no color. Shields.io badges (Phase 8) added
some color, but only for stat pills, not the terminal window itself.

This module renders the avatar + boot sequence + status line as an
actual SVG image: dark window chrome, theme-colored monospace text, a
soft glow filter, a static scanline texture, a scan-glow band that
sweeps top-to-bottom on a loop, an occasional glitch jitter on the whole
body, and a real blinking cursor - all using SVG's native <animate>/
<animateTransform> (SMIL), so they play continuously in a browser rather
than only changing once per build like the old text-based CRT effects.
Since the README embeds this as a same-repo relative path, GitHub serves
it as a raw file rather than routing it through its script-stripping
image proxy (that proxy is for external URLs), so the animation survives.

Usage:
    from svg_terminal import render_terminal_svg
    svg_markup = render_terminal_svg(avatar_ascii, boot_sequence, status, username, theme_name)
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
    """
    A static repeating pattern of thin dark lines every 3px - the classic
    CRT scanline *texture*, always visible (as opposed to the scan band
    below, which is the moving *sweep*). Uses explicit pixel dimensions
    (not percentages) inside the pattern - percentage sizing inside
    <pattern> isn't well-defined and breaks some SVG renderers.
    """
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
    """
    A brief horizontal jump applied to the whole body-text group, twice
    per loop, simulating an occasional signal glitch. Subtle and
    infrequent by design - most of the loop it sits still at (0,0).
    """
    return (
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;0 0;2 0;-2 0;0 0;0 0;0 0;0 0;-1 0;1 0;0 0;0 0" '
        'keyTimes="0;0.30;0.31;0.32;0.33;0.34;0.65;0.66;0.67;0.68;0.69;1" '
        f'dur="{GLITCH_LOOP_SECONDS}s" repeatCount="indefinite"/>'
    )


def render_terminal_svg(
    avatar_ascii: str,
    boot_sequence: str,
    status: str,
    username: str,
    theme_name: str = DEFAULT_THEME,
) -> str:
    """
    Build the SVG markup for the terminal window. Returns a full <svg>...
    </svg> string ready to write straight to a file.
    """
    theme = get_theme(theme_name)
    bg = f"#{theme['label_color']}"
    accent = f"#{theme['color']}"

    avatar_lines = avatar_ascii.split("\n")
    boot_lines = boot_sequence.split("\n")
    status_line = f"$ status: {status}"
    body_lines = avatar_lines + [""] + boot_lines + ["", status_line]

    cols = max((len(line) for line in body_lines), default=40)
    rows = len(body_lines)

    width = int(cols * CHAR_WIDTH + PADDING * 2)
    height = int(rows * LINE_HEIGHT + PADDING * 2 + TITLE_BAR_HEIGHT + DESCENDER_MARGIN)

    text_elements = []
    baseline_y = TITLE_BAR_HEIGHT + PADDING + FONT_SIZE
    status_baseline_y = baseline_y  # overwritten on the last iteration below
    for i, line in enumerate(body_lines):
        is_avatar = i < len(avatar_lines)
        opacity = 1.0 if is_avatar else 0.85
        text_elements.append(
            f'<text x="{PADDING}" y="{baseline_y}" filter="url(#glow)" '
            f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" '
            f'fill="{accent}" fill-opacity="{opacity}" xml:space="preserve">'
            f"{_esc(line)}</text>"
        )
        if line is status_line:
            status_baseline_y = baseline_y
        baseline_y += LINE_HEIGHT

    cursor_x = PADDING + CHAR_WIDTH * len(status_line)
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
      {''.join(text_elements)}
      {cursor}
      {_glitch_jitter()}
    </g>
    {_scan_band(width, height, accent)}
    {_scanline_texture(width, height)}
  </g>
</svg>"""
