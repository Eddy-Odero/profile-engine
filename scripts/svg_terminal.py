"""
svg_terminal.py  (real colored terminal visual)

Everything else in this project - the ASCII avatar, CRT text-noise
effects, the boot sequence - is plain text, and GitHub renders code-block
text as flat monospace with no color. Shields.io badges (Phase 8) added
some color, but only for stat pills, not the terminal window itself.

This module renders the avatar + boot sequence + status line as an
actual SVG image: dark window chrome, theme-colored monospace text, a
soft glow filter, and a real blinking cursor using SVG's native <animate>
(SMIL). Since the README embeds this as a same-repo relative path, GitHub
serves it as a raw file rather than routing it through its script-
stripping image proxy (that proxy is for external URLs) - so the
animation actually plays in a browser, unlike anything else in this repo.

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
  </defs>
  <rect width="{width}" height="{height}" rx="10" fill="{bg}"/>
  {_title_bar(width, accent, username)}
  {''.join(text_elements)}
  {cursor}
</svg>"""
