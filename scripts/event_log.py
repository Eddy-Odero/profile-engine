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

from hud_grid import glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS

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


def render_event_log_svg(events: list[dict], theme_name: str = DEFAULT_THEME) -> str:
    accent = HUD_COLORS["timeline"]

    # Pre-measure each entry's height so nodes land exactly on their
    # entry's vertical center regardless of how many description lines wrap.
    entry_heights = []
    for event in events:
        desc_lines = _wrap(event.get("description", ""))
        h = DATE_H + TITLE_H + len(desc_lines) * DESC_LINE_H + ROW_GAP
        entry_heights.append((h, desc_lines))

    height = PAD_TOP + sum(h for h, _ in entry_heights) + PAD_BOTTOM
    timeline_top = PAD_TOP + 6
    timeline_bottom = height - PAD_BOTTOM

    parts = []
    y = PAD_TOP
    for event, (h, desc_lines) in zip(events, entry_heights):
        node_y = y + 8
        text_x = NODE_X + 26

        parts.append(
            f'<circle cx="{NODE_X}" cy="{node_y}" r="5" fill="{accent}" filter="url(#hudglow)"/>'
            f'<circle cx="{NODE_X}" cy="{node_y}" r="8" fill="none" stroke="{accent}" '
            f'stroke-width="1" stroke-opacity="0.4"/>'
        )
        parts.append(
            f'<text x="{text_x}" y="{node_y + 4}" font-family="Consolas, Menlo, monospace" '
            f'font-size="11" fill="#{DATE_COLOR}">{_esc(event.get("date", ""))}</text>'
        )
        title_y = node_y + DATE_H
        parts.append(
            f'<text x="{text_x}" y="{title_y}" font-family="Consolas, Menlo, monospace" '
            f'font-size="15" font-weight="700" fill="#{TITLE_COLOR}">{_esc(event.get("title", ""))}</text>'
        )
        desc_y0 = title_y + 20
        for i, line in enumerate(desc_lines):
            parts.append(
                f'<text x="{text_x}" y="{desc_y0 + i*DESC_LINE_H}" '
                f'font-family="Consolas, Menlo, monospace" font-size="11" '
                f'fill="#{DESC_COLOR}">{_esc(line)}</text>'
            )
        y += h

    timeline_line = (
        f'<line x1="{NODE_X}" y1="{timeline_top}" x2="{NODE_X}" y2="{timeline_bottom}" '
        f'stroke="{accent}" stroke-width="1.5" stroke-opacity="0.5"/>'
    )

    bg_defs, bg_rect = grid_background(WIDTH, height, accent, spacing=20)
    scan_defs, scan_rect = scanline_overlay(WIDTH, height)

    return f"""<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Event log">
  <defs>{bg_defs}{glow_filter()}{scan_defs}</defs>
  <rect width="{WIDTH}" height="{height}" fill="#{BG}" fill-opacity="0.6"/>
  {bg_rect}
  {timeline_line}
  {''.join(parts)}
  {scan_rect}
</svg>"""
