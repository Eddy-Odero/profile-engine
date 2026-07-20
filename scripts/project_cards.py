"""
project_cards.py

Renders the project list as a row (or grid, if there are more than fit
on one row) of clean, light-background cards - not terminal-styled.

This is a deliberate style break from svg_terminal.py: someone skimming
a profile (a recruiter, an HR reviewer, a non-technical collaborator)
shouldn't have to parse `$ projects` terminal syntax to find out what
someone has built. A card with a project name in plain, legible type
reads the same way to everyone, technical or not.

Usage:
    from project_cards import render_project_cards_svg
    svg_markup = render_project_cards_svg(["SatGate", "EDU-FLIX"], theme_name)
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

CARD_WIDTH = 190
CARD_HEIGHT = 100
CARD_GAP = 16
ACCENT_BAR_HEIGHT = 6
CARDS_PER_ROW = 4
CARD_BG = "f8f9fa"  # light, neutral - readable regardless of the theme's dark accent color
CARD_TEXT = "212529"  # near-black, for legibility on the light card background


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _wrap_label(name: str, max_chars: int = 16) -> list[str]:
    """
    Wrap a project name onto up to 2 lines if it's long, breaking at the
    space closest to (but not past) max_chars so long multi-word names
    ("lem-in colony visualizer") split sensibly rather than only ever
    checking the first space in the string.
    """
    if len(name) <= max_chars:
        return [name]

    break_at = name.rfind(" ", 0, max_chars + 1)
    if break_at == -1:
        break_at = name.find(" ", max_chars)  # no space before the limit - use the first one after it instead
    if break_at != -1:
        return [name[:break_at], name[break_at + 1 :]]

    return [name[:max_chars], name[max_chars:]]


def _card(x: int, y: int, name: str, accent: str, index: int) -> str:
    lines = _wrap_label(name)
    label_y = CARD_HEIGHT / 2 + (10 if len(lines) == 1 else 0)

    text_elements = []
    for i, line in enumerate(lines):
        text_elements.append(
            f'<text x="{CARD_WIDTH / 2}" y="{label_y + i * 20}" '
            f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="15" '
            f'font-weight="600" fill="#{CARD_TEXT}" text-anchor="middle">'
            f"{_esc(line)}</text>"
        )

    return f"""
  <g transform="translate({x},{y})" filter="url(#cardShadow)">
    <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="12" fill="#{CARD_BG}"/>
    <rect width="{CARD_WIDTH}" height="{ACCENT_BAR_HEIGHT}" rx="3" fill="{accent}"/>
    <rect y="{ACCENT_BAR_HEIGHT}" width="{CARD_WIDTH}" height="{ACCENT_BAR_HEIGHT}" fill="{accent}"/>
    <circle cx="24" cy="{CARD_HEIGHT - 24}" r="10" fill="{accent}" fill-opacity="0.15"/>
    <text x="24" y="{CARD_HEIGHT - 20}" font-size="12" text-anchor="middle" fill="{accent}">#{index + 1}</text>
    {''.join(text_elements)}
  </g>"""


def render_project_cards_svg(projects: list[str], theme_name: str = DEFAULT_THEME) -> str:
    """
    Build an SVG containing one card per project, wrapping into rows of
    CARDS_PER_ROW. Returns a full <svg>...</svg> string.
    """
    if not projects:
        projects = ["More projects coming soon"]

    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"

    rows = [projects[i : i + CARDS_PER_ROW] for i in range(0, len(projects), CARDS_PER_ROW)]
    cols_in_widest_row = max(len(row) for row in rows)

    width = cols_in_widest_row * CARD_WIDTH + (cols_in_widest_row - 1) * CARD_GAP
    height = len(rows) * CARD_HEIGHT + (len(rows) - 1) * CARD_GAP

    cards = []
    index = 0
    for row_i, row in enumerate(rows):
        for col_i, project in enumerate(row):
            x = col_i * (CARD_WIDTH + CARD_GAP)
            y = row_i * (CARD_HEIGHT + CARD_GAP)
            cards.append(_card(x, y, project, accent, index))
            index += 1

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Projects">
  <defs>
    <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15"/>
    </filter>
  </defs>
  {''.join(cards)}
</svg>"""
