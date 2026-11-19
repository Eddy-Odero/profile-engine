"""
quote_card.py

A quote rendered as a typewriter-reveal card - WHITE background with a
vertical pink accent bar on the left, dark text for readability. This
is a deliberate one-off: every other section is dark HUD styling, but
the quote card is meant to read as a distinct "note card" pulled out
of that system, not another dark panel.

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

from themes import DEFAULT_THEME

FONT_SIZE = 16
LINE_HEIGHT = 26
CHAR_WIDTH = FONT_SIZE * 0.62  # approximate for a monospace font
PADDING_X = 30
PADDING_Y = 26
WRAP_CHARS = 46
MAX_LINES = 3
BG = "ffffff"
CARD_BORDER = "e5e5ea"
QUOTE_TEXT_COLOR = "1a1a1f"
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
    """HUD-style quote panel: chamfered dark panel, gold bar, corner tag, big quote mark, typewriter text."""
    gold = "#FFC84D"
    fs, lh, cw = 20, 32, 20 * 0.62
    W, CUT = 820, 16
    lines = textwrap.wrap(quote, width=54)[:3] or [quote]
    top = 84
    H = top + len(lines) * lh + 62
    pts = f"0,{CUT} {CUT},0 {W - 0.5},0 {W - 0.5},{H - CUT} {W - CUT},{H} 0,{H}"

    clips, texts = [], []
    for i, line in enumerate(lines):
        y = top + i * lh
        lw = len(line) * cw + 4
        clips.append(
            f'<clipPath id="reveal{i}"><rect x="0" y="{y - fs}" width="0" height="{lh}">'
            f"{_line_reveal_animate(i, len(lines), lw)}</rect></clipPath>"
        )
        texts.append(
            f'<text x="100" y="{y}" clip-path="url(#reveal{i})" font-family="Consolas, Menlo, monospace" '
            f'font-size="{fs}" fill="#ffffff">{_esc(line)}</text>'
        )
    ly = top + (len(lines) - 1) * lh
    lx = 100 + len(lines[-1]) * cw + 3
    by = H - 26
    n = 8
    brk = (
        f'<path d="M{W - 14 - n} 14 H{W - 14} V{14 + n} M14 {H - 14 - n} V{H - 14} H{14 + n}" '
        f'fill="none" stroke="{gold}" stroke-width="1.3"/>'
    )
    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Quote">
  <defs>
    {''.join(clips)}
    <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="2" height="6" fill="{gold}" fill-opacity="0.55"/>
    </pattern>
  </defs>
  <polygon points="{pts}" fill="#0b0f18" stroke="white" stroke-opacity="0.14"/>
  <rect x="0" y="{CUT}" width="4" height="{H - 2 * CUT}" fill="{gold}"/>
  <text x="36" y="38" font-family="Consolas, Menlo, monospace" font-size="12" font-weight="700" fill="{gold}" letter-spacing="3">[ DAILY SIGNAL ]</text>
  <text x="32" y="132" font-family="Georgia, 'Times New Roman', serif" font-size="96" font-weight="700" fill="{gold}" fill-opacity="0.9">&#8220;</text>
  {''.join(texts)}
  <rect x="{lx:.1f}" y="{ly - fs + 3}" width="2.5" height="{fs + 2}" fill="{gold}">
    <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{HOLD_UNTIL_FRACTION - 0.15:.3f};{HOLD_UNTIL_FRACTION - 0.14:.3f};{HOLD_UNTIL_FRACTION};1" dur="{TOTAL_CYCLE_SECONDS}s" repeatCount="indefinite"/>
  </rect>
  <rect x="100" y="{by}" width="40" height="2" fill="{gold}"/>
  <rect x="146" y="{by}" width="90" height="2" fill="url(#hatch)"/>
  <text x="{W - 32}" y="{by + 5}" text-anchor="end" font-family="Consolas, Menlo, monospace" font-size="10" fill="#6b7a8c" letter-spacing="1.5">NEW QUOTE ON EVERY BUILD</text>
  {brk}
</svg>"""
