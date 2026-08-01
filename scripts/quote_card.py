"""
quote_card.py

A quote rendered as a typewriter-reveal card, matching the exact HUD
spec everywhere else: dark #07090F background, cyan monospace text,
grid texture + glow - NOT the light-background Georgia-italic look
this file used to have. That earlier version predated the "exact hex,
not approximations" lock-in and was a real mismatch (a bright card in
an otherwise all-dark HUD design) - fixed here in place.

Uses SVG's native <animate> (SMIL) via a clip-path width reveal per
line: each line types out in sequence, holds fully visible, then the
whole card resets and loops - same general technique as
svg_terminal.py's blinking cursor, applied per-line instead of to a
single cursor block.

Usage:
    from quote_card import render_quote_svg
    svg_markup = render_quote_svg("Talk is cheap. Show me the code.", theme_name)
"""

from __future__ import annotations

import html
import textwrap

from hud_grid import glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS

FONT_SIZE = 16
LINE_HEIGHT = 26
CHAR_WIDTH = FONT_SIZE * 0.62  # approximate for a monospace font
PADDING_X = 30
PADDING_Y = 26
WRAP_CHARS = 46
MAX_LINES = 3
BG = "07090F"
CARD_BORDER = "1c2a3a"
QUOTE_TEXT_COLOR = "e8e6f0"
TOTAL_CYCLE_SECONDS = 7
TYPING_PHASE_FRACTION = 0.6  # first 60% of the cycle is spent sequentially typing
HOLD_UNTIL_FRACTION = 0.92  # then hold fully visible until 92%, then snap-reset


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _line_reveal_animate(index: int, total_lines: int, full_width: float) -> str:
    """
    Build the <animate> for one line's clip-rect width: stays at 0 until
    it's this line's turn, ramps 0 -> full_width during its slice of the
    typing phase, holds at full_width, then snaps back to 0 right before
    the loop restarts (all lines share one <dur>/cycle so they resync).
    """
    start_frac = (index / total_lines) * TYPING_PHASE_FRACTION
    end_frac = ((index + 1) / total_lines) * TYPING_PHASE_FRACTION

    key_times = f"0;{start_frac:.3f};{end_frac:.3f};{HOLD_UNTIL_FRACTION};1"
    values = f"0;0;{full_width:.1f};{full_width:.1f};0"

    return (
        f'<animate attributeName="width" values="{values}" keyTimes="{key_times}" '
        f'dur="{TOTAL_CYCLE_SECONDS}s" repeatCount="indefinite"/>'
    )


def render_quote_svg(quote: str, theme_name: str = DEFAULT_THEME) -> str:
    """Build the SVG markup for the typewriter quote card."""
    accent = HUD_COLORS["header"]

    lines = textwrap.wrap(quote, width=WRAP_CHARS)[:MAX_LINES]
    if not lines:
        lines = [quote]

    max_line_len = max(len(line) for line in lines)
    text_width = max_line_len * CHAR_WIDTH
    width = int(text_width + PADDING_X * 2 + 24)  # +24 for the decorative quote mark
    height = int(len(lines) * LINE_HEIGHT + PADDING_Y * 2)

    clip_groups = []
    for i, line in enumerate(lines):
        line_width = len(line) * CHAR_WIDTH + 4
        y = PADDING_Y + i * LINE_HEIGHT
        clip_id = f"reveal{i}"
        clip_groups.append(
            f"""
    <clipPath id="{clip_id}">
      <rect x="0" y="{y - FONT_SIZE}" width="0" height="{LINE_HEIGHT + 4}">
        {_line_reveal_animate(i, len(lines), line_width)}
      </rect>
    </clipPath>"""
        )

    text_elements = []
    for i, line in enumerate(lines):
        y = PADDING_Y + i * LINE_HEIGHT + FONT_SIZE - 4
        text_elements.append(
            f'<text x="{PADDING_X + 24}" y="{y}" clip-path="url(#reveal{i})" '
            f'font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" fill="#{QUOTE_TEXT_COLOR}">{_esc(line)}</text>'
        )

    last_line_y = PADDING_Y + (len(lines) - 1) * LINE_HEIGHT + FONT_SIZE - 4
    last_line_width = len(lines[-1]) * CHAR_WIDTH

    grid_defs, grid_rect = grid_background(width, height, accent, spacing=20, rx=10)
    scan_defs, scan_rect = scanline_overlay(width, height)

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Quote">
  <defs>{''.join(clip_groups)}{grid_defs}{glow_filter()}{scan_defs}
  </defs>
  <rect width="{width}" height="{height}" rx="10" fill="#{BG}"/>
  {grid_rect}
  <rect width="{width}" height="{height}" rx="10" fill="none" stroke="#{CARD_BORDER}" stroke-width="1"/>
  <rect width="4" height="{height}" fill="{accent}"/>
  <text x="{PADDING_X - 8}" y="{PADDING_Y + 16}" font-family="Consolas, Menlo, monospace" \
font-size="38" fill="{accent}" fill-opacity="0.4" filter="url(#hudglow)">&#8220;</text>
  {''.join(text_elements)}
  <rect x="{PADDING_X + 24 + last_line_width:.1f}" y="{last_line_y - FONT_SIZE + 3}" \
width="2.5" height="{FONT_SIZE + 2}" fill="{accent}" filter="url(#hudglow)">
    <animate attributeName="opacity" values="0;0;1;1;0" \
keyTimes="0;{HOLD_UNTIL_FRACTION - 0.15:.3f};{HOLD_UNTIL_FRACTION - 0.14:.3f};{HOLD_UNTIL_FRACTION};1" \
dur="{TOTAL_CYCLE_SECONDS}s" repeatCount="indefinite"/>
  </rect>
  {scan_rect}
</svg>"""
