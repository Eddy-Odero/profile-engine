"""
section_header.py

The small cyan "SEC-X   TITLE" header graphic that sits above every
section in the reference design: a small filled module-code box
("SEC-1") followed by the uppercase section title, with a thin glowing
divider line trailing off to the right. Plain markdown `###` headers
render in GitHub's default black/white styling and can't carry this
look - GitHub only special-cases colored, styled output for markdown
*images*, same reason project_cards.py's badges and signal_uplink.py's
pills are separate SVGs instead of styled text.

Usage:
    from section_header import render_section_header_svg
    svg_markup = render_section_header_svg(1, "Neural Activity", theme_name)
"""

from __future__ import annotations

import html

from hud_grid import glow_filter
from themes import DEFAULT_THEME, HUD_COLORS

WIDTH = 820  # matches the terminal/card content width used elsewhere
HEIGHT = 34
CODE_BOX_W = 46
CODE_BOX_H = 20
BG = "07090F"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_section_header_svg(
    index: int, title: str, theme_name: str = DEFAULT_THEME, accent: str | None = None
) -> str:
    """
    `index` becomes the "SEC-N" code. `accent` overrides the default
    header cyan for a section whose theme color differs (e.g. Neural
    Activity's header still reads cyan in the reference even though its
    content below is green, so the default is deliberately always
    HUD_COLORS["header"] unless a caller passes something else).
    """
    color = accent or HUD_COLORS["header"]
    code = f"SEC-{index}"
    label_y = HEIGHT / 2 + 5
    box_y = (HEIGHT - CODE_BOX_H) / 2
    title_x = CODE_BOX_W + 14

    return f"""<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(title)}">
  <defs>{glow_filter()}</defs>
  <rect x="0" y="{box_y}" width="{CODE_BOX_W}" height="{CODE_BOX_H}" fill="{color}" fill-opacity="0.15" \
stroke="{color}" stroke-width="1"/>
  <text x="{CODE_BOX_W/2}" y="{label_y}" font-family="Consolas, Menlo, monospace" font-size="10" \
font-weight="700" fill="{color}" text-anchor="middle" letter-spacing="0.5">{_esc(code)}</text>
  <text x="{title_x}" y="{label_y}" font-family="Consolas, Menlo, monospace" font-size="14" \
font-weight="700" fill="{color}" letter-spacing="2" filter="url(#hudglow)">{_esc(title.upper())}</text>
  <line x1="{title_x + len(title)*9.5 + 16}" y1="{HEIGHT/2}" x2="{WIDTH}" y2="{HEIGHT/2}" \
stroke="{color}" stroke-width="1" stroke-opacity="0.5"/>
</svg>"""
