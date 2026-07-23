"""
project_cards.py

Two things live here, and they're separate for an important reason:

1. render_project_cards_svg() - the VISUAL card grid (icon + one-line
   description per project). Dark, muted background with a subtle
   border, matching the reference dashboard's aesthetic (sparse accent
   color, not a bright white card like the old design).

2. render_link_badge_svg() - small "Preview" / "Code" icon badges.
   These are NOT embedded inside the card grid above, because SVGs
   loaded via markdown image syntax (`![]()`, which becomes `<img
   src="...">`) have all internal interactivity stripped by the browser
   - any <a> links inside such an SVG are inert. The only way to get an
   actually-clickable icon in a GitHub README is markdown's own
   `[![alt](badge.svg)](url)` syntax, where the link lives in the
   markdown, not the image. So each project gets its OWN tiny badge
   file, wrapped in a real markdown link in the template - that's what
   makes them clickable.

Usage:
    from project_cards import render_project_cards_svg, render_link_badge_svg
    svg_markup = render_project_cards_svg(projects, theme_name)
    badge_svg = render_link_badge_svg("preview", theme_name)
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

CARD_WIDTH = 210
CARD_HEIGHT = 130
CARD_GAP = 16
CARDS_PER_ROW = 4
ICON_RADIUS = 20

CARD_BG = "16161c"  # dark, muted - close to a typical dark page background
CARD_BORDER = "2a2a33"  # subtle, barely-lighter-than-bg border
DESC_COLOR = "9a9aa5"  # muted gray for description text, per the reference's hierarchy

BADGE_WIDTH = 96
BADGE_HEIGHT = 30


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _wrap_label(name: str, max_chars: int = 18) -> list[str]:
    """Wrap a project name onto up to 2 lines, breaking at the nearest space."""
    if len(name) <= max_chars:
        return [name]
    break_at = name.rfind(" ", 0, max_chars + 1)
    if break_at == -1:
        break_at = name.find(" ", max_chars)
    if break_at != -1:
        return [name[:break_at], name[break_at + 1 :]]
    return [name[:max_chars], name[max_chars:]]


def _wrap_description(text: str, max_chars: int = 30) -> list[str]:
    """Wrap a description onto up to 3 lines, breaking on spaces."""
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
    return lines[:3]


def _project_icon(cx: float, cy: float, initial: str, accent: str) -> str:
    """
    A simple circular icon badge with the project's first letter -
    consistent with the initials-avatar pattern used elsewhere in this
    project (hero_card.py), rather than trying to guess a "real" icon
    per project with no actual icon data to draw from.
    """
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{ICON_RADIUS}" fill="{accent}" fill-opacity="0.15" '
        f'stroke="{accent}" stroke-width="1.5"/>'
        f'<text x="{cx}" y="{cy + 6}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="18" font-weight="700" fill="{accent}" text-anchor="middle">{_esc(initial)}</text>'
    )


def _card(x: int, y: int, project: dict, accent: str) -> str:
    name = project["name"]
    description = project.get("description", "")
    name_lines = _wrap_label(name)
    desc_lines = _wrap_description(description)

    icon_cy = 34
    name_y = icon_cy + ICON_RADIUS + 20
    desc_start_y = name_y + len(name_lines) * 18 + 6

    name_elements = "".join(
        f'<text x="{CARD_WIDTH / 2}" y="{name_y + i * 18}" '
        f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="14" '
        f'font-weight="700" fill="white" text-anchor="middle">{_esc(line)}</text>'
        for i, line in enumerate(name_lines)
    )
    desc_elements = "".join(
        f'<text x="{CARD_WIDTH / 2}" y="{desc_start_y + i * 15}" '
        f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" '
        f'fill="#{DESC_COLOR}" text-anchor="middle">{_esc(line)}</text>'
        for i, line in enumerate(desc_lines)
    )

    return f"""
  <g transform="translate({x},{y})">
    <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="10" fill="#{CARD_BG}" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
    {_project_icon(CARD_WIDTH / 2, icon_cy, name[0].upper(), accent)}
    {name_elements}
    {desc_elements}
  </g>"""


def render_project_cards_svg(projects: list[dict], theme_name: str = DEFAULT_THEME) -> str:
    """
    Build an SVG containing one visual card per project (icon + name +
    description - NOT clickable, see module docstring), wrapping into
    rows of CARDS_PER_ROW.
    """
    if not projects:
        projects = [{"name": "More projects coming soon", "description": ""}]

    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"

    rows = [projects[i : i + CARDS_PER_ROW] for i in range(0, len(projects), CARDS_PER_ROW)]
    cols_in_widest_row = max(len(row) for row in rows)

    width = cols_in_widest_row * CARD_WIDTH + (cols_in_widest_row - 1) * CARD_GAP
    height = len(rows) * CARD_HEIGHT + (len(rows) - 1) * CARD_GAP

    cards = []
    for row_i, row in enumerate(rows):
        for col_i, project in enumerate(row):
            x = col_i * (CARD_WIDTH + CARD_GAP)
            y = row_i * (CARD_HEIGHT + CARD_GAP)
            cards.append(_card(x, y, project, accent))

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Projects">
  {''.join(cards)}
</svg>"""


def _eye_icon(cx: float, cy: float, color: str) -> str:
    """Simple eye glyph for the 'preview' badge - drawn as shapes, no icon font needed."""
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="7" ry="4.2" fill="none" stroke="{color}" stroke-width="1.4"/>'
        f'<circle cx="{cx}" cy="{cy}" r="2.1" fill="{color}"/>'
    )


def render_link_badge_svg(
    kind: str, theme_name: str = DEFAULT_THEME, disabled: bool = False
) -> str:
    """
    Build one small badge: kind is "preview" or "code". These are the
    pieces that actually become clickable, once wrapped in a markdown
    link in the template - see module docstring for why this is a
    separate function/file from the card grid.

    `disabled=True` renders a muted, non-link-implying version (used
    for "not hosted yet" - still shown as a badge for visual
    consistency, just dimmed and not wrapped in a link by the template).
    """
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}" if not disabled else "#5a5a66"
    dark = f"#{theme['label_color']}"
    label = "Preview" if kind == "preview" else "Code"

    icon_x = 16
    if kind == "preview":
        icon = _eye_icon(icon_x, BADGE_HEIGHT / 2, accent)
    else:
        icon = (
            f'<text x="{icon_x}" y="{BADGE_HEIGHT / 2 + 4}" font-family="Consolas, Menlo, monospace" '
            f'font-size="12" font-weight="700" fill="{accent}" text-anchor="middle">&lt;/&gt;</text>'
        )

    return f"""<svg width="{BADGE_WIDTH}" height="{BADGE_HEIGHT}" \
viewBox="0 0 {BADGE_WIDTH} {BADGE_HEIGHT}" xmlns="http://www.w3.org/2000/svg" \
role="img" aria-label="{_esc(label)}">
  <rect width="{BADGE_WIDTH}" height="{BADGE_HEIGHT}" rx="6" fill="{dark}" stroke="{accent}" stroke-width="1.2"/>
  {icon}
  <text x="{BADGE_WIDTH / 2 + 10}" y="{BADGE_HEIGHT / 2 + 4}" \
font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" font-weight="600" \
fill="{accent}" text-anchor="middle">{_esc(label)}</text>
</svg>"""
