"""
leetcode_panel.py

A styled readout panel for LeetCode stats, in the "Top categories"
bar-chart style (label left, value+percentage right-aligned above a
horizontal bar, bar length proportional to percentage) - the same
pattern as a RescueTime/WakaTime-style breakdown. Easy/Medium/Hard
solved counts map naturally onto this: each is a percentage of total
problems solved, so each becomes one bar row. Rating/rank/contests
don't have a natural percentage, so they sit below as a compact
footer strip instead of forced into bars.

Usage:
    from leetcode_panel import render_leetcode_panel_svg
    svg_markup = render_leetcode_panel_svg(leetcode_stats, theme_name)
"""

from __future__ import annotations

import html

from hud_grid import glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME

WIDTH = 820
PAD_X = 28
TITLE_Y = 30
SUBTITLE_Y = 48
ROWS_TOP = 78
ROW_H = 46
BAR_H = 6
BAR_TRACK_COLOR = "2a2438"

BG = "07090F"
TITLE_COLOR = "e8e6f0"
SUBTITLE_COLOR = "6b6478"
LABEL_COLOR = "c9c4d6"
VALUE_COLOR = "8a7fa8"
FOOTER_LABEL = "6b6478"
FOOTER_VALUE = "e8e6f0"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_leetcode_panel_svg(stats: dict, theme_name: str = DEFAULT_THEME) -> str:
    accent = "#FF2279"  # exact rose-pink sampled from the reference screenshot

    solved = stats.get("solved", {}) or {}
    total = solved.get("total", 0) or 0
    categories = [
        ("Easy", solved.get("easy", 0)),
        ("Medium", solved.get("medium", 0)),
        ("Hard", solved.get("hard", 0)),
    ]

    bar_x = PAD_X
    bar_w = WIDTH - PAD_X * 2

    rows_svg = []
    for i, (label, count) in enumerate(categories):
        pct = (count / total * 100) if total else 0
        row_y = ROWS_TOP + i * ROW_H
        fill_w = bar_w * (pct / 100)
        rows_svg.append(f"""
  <text x="{bar_x}" y="{row_y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" \
font-size="13" fill="#{LABEL_COLOR}">{_esc(label)}</text>
  <text x="{bar_x + bar_w}" y="{row_y}" font-family="Consolas, Menlo, monospace" \
font-size="12" fill="#{VALUE_COLOR}" text-anchor="end">{count} ({pct:.0f}%)</text>
  <rect x="{bar_x}" y="{row_y + 10}" width="{bar_w}" height="{BAR_H}" rx="3" fill="#{BAR_TRACK_COLOR}"/>
  <circle cx="{bar_x + 3}" cy="{row_y + 10 + BAR_H/2}" r="3" fill="{accent}" filter="url(#hudglow)"/>
  <rect x="{bar_x}" y="{row_y + 10}" width="{max(fill_w, 6):.1f}" height="{BAR_H}" rx="3" \
fill="{accent}" fill-opacity="0.85"/>""")

    footer_y = ROWS_TOP + len(categories) * ROW_H + 14
    footer_items = [
        ("RATING", str(stats.get("rating") or "unrated")),
        ("GLOBAL RANK", str(stats.get("ranking") if stats.get("ranking") is not None else "N/A")),
        ("TOP %", f"{stats['top_percentage']}%" if stats.get("top_percentage") is not None else "N/A"),
        ("CONTESTS", str(stats.get("contests_attended") or 0)),
    ]
    footer_col_w = (WIDTH - PAD_X * 2) / len(footer_items)
    footer_svg = []
    for i, (label, value) in enumerate(footer_items):
        fx = PAD_X + i * footer_col_w
        footer_svg.append(
            f'<text x="{fx}" y="{footer_y}" font-family="Consolas, Menlo, monospace" '
            f'font-size="9.5" fill="#{FOOTER_LABEL}" letter-spacing="0.5">{_esc(label)}</text>'
        )
        footer_svg.append(
            f'<text x="{fx}" y="{footer_y + 18}" font-family="Consolas, Menlo, monospace" '
            f'font-size="13" font-weight="700" fill="#{FOOTER_VALUE}">{_esc(value)}</text>'
        )

    height = footer_y + 32

    grid_defs, grid_rect = grid_background(WIDTH, height, accent, spacing=20)
    scan_defs, scan_rect = scanline_overlay(WIDTH, height)

    return f"""<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LeetCode stats">
  <defs>{grid_defs}{glow_filter()}{scan_defs}</defs>
  <rect width="{WIDTH}" height="{height}" fill="#{BG}" fill-opacity="0.6"/>
  {grid_rect}
  <text x="{PAD_X}" y="{TITLE_Y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" \
font-size="17" font-weight="700" fill="#{TITLE_COLOR}">Problem Difficulty</text>
  <text x="{PAD_X}" y="{SUBTITLE_Y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" \
font-size="12" fill="#{SUBTITLE_COLOR}">breakdown of {total} solved, all time</text>
  {''.join(rows_svg)}
  <line x1="{PAD_X}" y1="{footer_y - 24}" x2="{WIDTH-PAD_X}" y2="{footer_y - 24}" \
stroke="#{BAR_TRACK_COLOR}" stroke-width="1"/>
  {''.join(footer_svg)}
  {scan_rect}
</svg>"""
