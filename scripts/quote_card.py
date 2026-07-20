"""
quote_card.py

Renders a quote as a friendly, light-background card (matching
project_cards.py's approachable style, not the dark terminal look) with
a real typewriter reveal animation: each line types out in sequence,
holds fully visible, then the whole card resets and loops - using SVG's
native <animate> (SMIL) via a clip-path width reveal per line, the same
general technique as svg_terminal.py's blinking cursor, just applied
per-line instead of to a single cursor block.

Usage:
    from quote_card import render_quote_svg
    svg_markup = render_quote_svg("Talk is cheap. Show me the code.", theme_name)
"""

from __future__ import annotations

import html
import textwrap

from themes import DEFAULT_THEME, get_theme

FONT_SIZE = 17
LINE_HEIGHT = 26
CHAR_WIDTH = FONT_SIZE * 0.52  # approximate for a proportional sans-serif italic
PADDING_X = 28
PADDING_Y = 24
WRAP_CHARS = 34
MAX_LINES = 3
CARD_BG = "f8f9fa"
QUOTE_TEXT_COLOR = "212529"
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
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"

    lines = textwrap.wrap(quote, width=WRAP_CHARS)[:MAX_LINES]
    if not lines:
        lines = [quote]

    max_line_len = max(len(line) for line in lines)
    text_width = max_line_len * CHAR_WIDTH
    width = int(text_width + PADDING_X * 2 + 20)  # +20 for the decorative quote mark
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
            f'<text x="{PADDING_X + 20}" y="{y}" clip-path="url(#reveal{i})" '
            f'font-family="Georgia, \'Times New Roman\', serif" font-style="italic" '
            f'font-size="{FONT_SIZE}" fill="#{QUOTE_TEXT_COLOR}">{_esc(line)}</text>'
        )

    last_line_y = PADDING_Y + (len(lines) - 1) * LINE_HEIGHT + FONT_SIZE - 4
    last_line_width = len(lines[-1]) * CHAR_WIDTH

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Quote">
  <defs>{''.join(clip_groups)}
  </defs>
  <rect width="{width}" height="{height}" rx="12" fill="#{CARD_BG}"/>
  <rect width="6" height="{height}" rx="3" fill="{accent}"/>
  <text x="{PADDING_X - 12}" y="{PADDING_Y + 14}" font-family="Georgia, serif" \
font-size="42" fill="{accent}" fill-opacity="0.35">&#8220;</text>
  {''.join(text_elements)}
  <rect x="{PADDING_X + 20 + last_line_width:.1f}" y="{last_line_y - FONT_SIZE + 3}" \
width="2.5" height="{FONT_SIZE + 2}" fill="{accent}">
    <animate attributeName="opacity" values="0;0;1;1;0" \
keyTimes="0;{HOLD_UNTIL_FRACTION - 0.15:.3f};{HOLD_UNTIL_FRACTION - 0.14:.3f};{HOLD_UNTIL_FRACTION};1" \
dur="{TOTAL_CYCLE_SECONDS}s" repeatCount="indefinite"/>
  </rect>
</svg>"""
