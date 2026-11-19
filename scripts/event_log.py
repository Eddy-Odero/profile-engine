"""
event_log.py

"Event Log" - a red vertical timeline of dated milestones, matching
the reference design: a vertical rule with a filled node per entry,
each entry showing a monospace timestamp, a bold title, and a muted
one-line description underneath.

Usage:
    from event_log import render_event_log_svg
    svg_markup = render_event_log_svg(events, theme_name)

`events` is a list of dicts: {"date": "2026.07.22 -- 14:32 UTC",
"title": "...", "description": "..."} newest-first, matching the
reference's ordering.
"""

from __future__ import annotations

import html

from hud_grid import glass_frame_rect, glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

WIDTH = 820
PAD_X = 40
PAD_TOP = 30
PAD_BOTTOM = 30
NODE_X = 44

ROW_GAP = 18  # extra space between entries, beyond the wrapped text height
DATE_H = 20
TITLE_H = 22
DESC_LINE_H = 16

TITLE_COLOR = "e8e6f0"
DESC_COLOR = "8a8494"
DATE_COLOR = "6b6478"
BG = "07090F"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _wrap(text: str, max_chars: int = 78) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "\u2026"


LEFT_W = 290  # heading column
RX = 320  # accordion column x
RW = WIDTH - RX
ROW_SPACING = 10
GOLD = HUD_COLORS["modules"]


def render_event_log_svg(events: list[dict], theme_name: str = DEFAULT_THEME, for_light_mode: bool = False) -> str:
    """
    Event Log in the two-column FAQ reference layout: bracket tag,
    two-tone heading and description on the left; the numbered accordion
    rows (index, divider, title, description, date, decorative "+") on
    the right. Rows stay dark in light mode (near-opaque) so their white
    text reads; only the heading text flips.
    """
    accent = HUD_COLORS["timeline"]
    bg = get_theme(theme_name)["label_color"]
    row_opacity = 0.96 if for_light_mode else 0.6
    ink = "#10131a" if for_light_mode else "#ffffff"
    muted = "#4b5563" if for_light_mode else "#9a9aa5"

    rows = []
    y = 0
    text_x = 74
    for i, event in enumerate(events):
        title_lines = _wrap(event.get("title", "").upper(), 30)[:2]
        desc_lines = _wrap(event.get("description", ""), 58)[:2]
        if len(_wrap(event.get("description", ""), 58)) > 2:
            desc_lines[-1] = _truncate(desc_lines[-1], 56)
        h = 18 + len(title_lines) * 17 + 4 + len(desc_lines) * 14 + 8 + 14 + 14
        ty = 28
        body = [
            f'<text x="{text_x}" y="{ty + j * 17}" font-family="Arial, Helvetica, sans-serif" font-size="13" '
            f'font-weight="700" fill="white" letter-spacing="0.4">{_esc(line)}</text>'
            for j, line in enumerate(title_lines)
        ]
        dy = ty + (len(title_lines) - 1) * 17 + 18
        body += [
            f'<text x="{text_x}" y="{dy + j * 14}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
            f'font-size="11" fill="#9a9aa5">{_esc(line)}</text>'
            for j, line in enumerate(desc_lines)
        ]
        date_y = dy + (len(desc_lines) - 1) * 14 + 20
        body.append(
            f'<text x="{text_x}" y="{date_y}" font-family="Consolas, Menlo, monospace" font-size="10" '
            f'fill="#6b7a8c" letter-spacing="0.5">{_esc(event.get("date", ""))}</text>'
        )
        parts_y = y
        rows.append(f"""
  <g transform="translate({RX},{parts_y})">
    <rect x="0.5" y="0.5" width="{RW - 1}" height="{h - 1}" rx="10" fill="#{bg}" fill-opacity="{row_opacity}" \
stroke="{accent}" stroke-opacity="0.28"/>
    <text x="22" y="{h / 2 + 5}" font-family="Consolas, Menlo, monospace" font-size="14" font-weight="700" \
fill="{accent}">{i + 1:02d}</text>
    <line x1="56" y1="14" x2="56" y2="{h - 14}" stroke="white" stroke-opacity="0.14"/>
    {''.join(body)}
    <path d="M{RW - 31} {h / 2} L{RW - 17} {h / 2} M{RW - 24} {h / 2 - 7} L{RW - 24} {h / 2 + 7}" \
stroke="white" stroke-width="1.4" stroke-linecap="round"/>
  </g>""")
        y += h + ROW_SPACING

    left_h = 150
    height = max(left_h, y - ROW_SPACING) + 12
    sub = _wrap("Wins, launches and shipped work, newest first.", 34)
    sub_svg = "".join(
        f'<text x="0" y="{138 + j * 18}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" '
        f'fill="{muted}">{_esc(line)}</text>'
        for j, line in enumerate(sub)
    )

    # Decorative call-to-action card, bottom of the left column (the
    # reference's "still have questions?" box, reworded). It's an image,
    # so it isn't clickable - the social links elsewhere carry the links.
    card_h = 96
    cy = height - 12 - card_h
    gold = GOLD
    cta = f"""
  <g transform="translate(0,{cy})">
    <rect x="0.5" y="0.5" width="{LEFT_W - 1}" height="{card_h - 1}" rx="12" fill="#{bg}" fill-opacity="{row_opacity}" \
stroke="white" stroke-opacity="0.12"/>
    <rect x="18" y="20" width="44" height="44" rx="10" fill="none" stroke="white" stroke-opacity="0.35"/>
    <path d="M18 28 V20 H26 M54 20 H62 V28 M62 56 V64 H54 M26 64 H18 V56" fill="none" stroke="{gold}" stroke-width="1.6"/>
    <path d="M30 31 H50 a3 3 0 0 1 3 3 V44 a3 3 0 0 1 -3 3 H40 L34 53 V47 H30 a3 3 0 0 1 -3 -3 V34 a3 3 0 0 1 3 -3 Z" \
fill="none" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>
    <text x="78" y="32" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="700" fill="white" \
letter-spacing="0.4">GOT AN IDEA?</text>
    <text x="78" y="50" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" fill="#9a9aa5">\
Tell me what you are building</text>
    <text x="78" y="73" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="700" fill="{gold}" \
letter-spacing="0.5">SAY HELLO</text>
    <rect x="156" y="61" width="16" height="16" rx="3" fill="none" stroke="{gold}" stroke-width="1.3"/>
    <path d="M160 69 H168 M165 66 L168 69 L165 72" fill="none" stroke="{gold}" stroke-width="1.3" \
stroke-linecap="round" stroke-linejoin="round"/>
  </g>"""

    return f"""<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Event log">
  <defs>{glow_filter()}</defs>
  <text x="0" y="18" font-family="Consolas, Menlo, monospace" font-size="12" font-weight="700" \
fill="{GOLD}" letter-spacing="3" filter="url(#hudglow)">[ EVENT LOG ]</text>
  <text x="0" y="62" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="800" \
fill="{ink}" letter-spacing="0.5">RECENT</text>
  <text x="0" y="100" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="800" \
fill="{GOLD}" letter-spacing="0.5">MILESTONES</text>
  <rect x="0" y="114" width="40" height="2" fill="{GOLD}"/>
  <rect x="40" y="114.5" width="{LEFT_W - 100}" height="1" fill="{GOLD}" fill-opacity="0.25"/>
  {sub_svg}
  {cta}
  {''.join(rows)}
</svg>"""
