"""
leetcode_panel.py

A styled readout panel for LeetCode stats, replacing the old plain
```-fenced markdown code block (which rendered in GitHub's default
monospace with no color/grid/glow - a real style mismatch next to
every other HUD section). Uses the same magenta accent as Dimensional
Stats, since LeetCode data is the same "dimension" of stat, just shown
here at a level of detail (Easy/Medium/Hard split, rank, recent solves)
that doesn't fit in the compact Dimensional Stats cards.

Usage:
    from leetcode_panel import render_leetcode_panel_svg
    svg_markup = render_leetcode_panel_svg(leetcode_stats, theme_name)

`leetcode_stats` is the dict already produced by build.py's
build_leetcode_stats(): {"solved": {...}, "rating", "ranking",
"top_percentage", "contests_attended", "badges", "recent_submissions"}.
"""

from __future__ import annotations

import html

from hud_grid import glow_filter, grid_background, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS

WIDTH = 820
PAD_X = 28
PAD_TOP = 26
ROW_H = 24
BG = "07090F"
LABEL_COLOR = "8a7fa8"
VALUE_COLOR = "e8e6f0"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_leetcode_panel_svg(stats: dict, theme_name: str = DEFAULT_THEME) -> str:
    accent = HUD_COLORS["stats"]

    solved = stats.get("solved", {}) or {}
    rows = [
        ("SOLVED", f"{solved.get('total', 0)} (E{solved.get('easy', 0)} / "
                    f"M{solved.get('medium', 0)} / H{solved.get('hard', 0)})"),
        ("RATING", str(stats.get("rating") or "unrated")),
        ("GLOBAL_RANK", str(stats.get("ranking") if stats.get("ranking") is not None else "N/A")),
        ("TOP_PERCENT", f"{stats['top_percentage']}%" if stats.get("top_percentage") is not None else "N/A"),
        ("CONTESTS", str(stats.get("contests_attended") or 0)),
        ("BADGES", ", ".join(stats.get("badges") or []) or "none yet"),
    ]

    recent = (stats.get("recent_submissions") or [])[:3]

    left_col_x = PAD_X
    value_x = PAD_X + 190

    row_elements = []
    for i, (label, value) in enumerate(rows):
        y = PAD_TOP + i * ROW_H
        row_elements.append(
            f'<text x="{left_col_x}" y="{y}" font-family="Consolas, Menlo, monospace" '
            f'font-size="12" fill="#{LABEL_COLOR}" letter-spacing="0.5">{_esc(label)}</text>'
        )
        row_elements.append(
            f'<text x="{value_x}" y="{y}" font-family="Consolas, Menlo, monospace" '
            f'font-size="12" font-weight="700" fill="#{VALUE_COLOR}">{_esc(value)}</text>'
        )

    recent_y0 = PAD_TOP + len(rows) * ROW_H + 12
    recent_elements = []
    if recent:
        recent_elements.append(
            f'<text x="{left_col_x}" y="{recent_y0}" font-family="Consolas, Menlo, monospace" '
            f'font-size="12" fill="{accent}" letter-spacing="1">RECENT_SUBMISSIONS</text>'
        )
        for i, title in enumerate(recent):
            y = recent_y0 + 20 + i * 18
            recent_elements.append(
                f'<text x="{left_col_x}" y="{y}" font-family="Consolas, Menlo, monospace" '
                f'font-size="11" fill="#{VALUE_COLOR}">&gt; {_esc(title)}</text>'
            )

    height = recent_y0 + (20 + len(recent) * 18 if recent else 0) + 20

    grid_defs, grid_rect = grid_background(WIDTH, height, accent, spacing=20)
    scan_defs, scan_rect = scanline_overlay(WIDTH, height)

    return f"""<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LeetCode stats">
  <defs>{grid_defs}{glow_filter()}{scan_defs}</defs>
  <rect width="{WIDTH}" height="{height}" fill="#{BG}"/>
  {grid_rect}
  <rect width="4" height="{height}" fill="{accent}"/>
  {''.join(row_elements)}
  {''.join(recent_elements)}
  {scan_rect}
</svg>"""
