"""
project_cards.py

Three things live here:

1. render_single_project_card_svg() - ONE project's visual card (icon +
   name + description). Renders one project at a time now, not a
   combined grid - the template arranges cards into an HTML table grid
   itself, because each card needs its own View/Code button row
   directly underneath it (see point 2), which only works if each
   card is its own separate image.

2. render_link_badge_svg() - small "View" / "Code" icon badges. These
   are NOT embedded inside the card SVG, because SVGs loaded via
   markdown image syntax (`![]()`, which becomes `<img src="...">`)
   have all internal interactivity stripped by the browser - any <a>
   links inside such an SVG are inert. The only way to get an actually-
   clickable icon in a GitHub README is markdown's own
   `[![alt](badge.svg)](url)` syntax, where the link lives in the
   markdown, not the image.

3. A small set of hand-drawn semantic icon glyphs (lightning bolt, play
   button, network/graph nodes, shopping cart, and a generic default) -
   picked per-project via an "icon" key, since there's no real per-
   project logo artwork to draw from. Falls back to a generic icon if
   a project doesn't specify one or specifies an unknown key.

Usage:
    from project_cards import render_single_project_card_svg, render_link_badge_svg
    card_svg = render_single_project_card_svg(project, theme_name)
    badge_svg = render_link_badge_svg("view", theme_name)
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

CARD_WIDTH = 210
CARD_HEIGHT = 130
ICON_RADIUS = 20

CARD_BG = "16161c"  # dark, muted - close to a typical dark page background
CARD_BORDER = "2a2a33"  # subtle, barely-lighter-than-bg border
DESC_COLOR = "9a9aa5"  # muted gray for description text, per the reference's hierarchy

BADGE_WIDTH = 88
BADGE_HEIGHT = 30


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _wrap_label(name: str, max_chars: int = 18) -> list[str]:
    if len(name) <= max_chars:
        return [name]
    break_at = name.rfind(" ", 0, max_chars + 1)
    if break_at == -1:
        break_at = name.find(" ", max_chars)
    if break_at != -1:
        return [name[:break_at], name[break_at + 1 :]]
    return [name[:max_chars], name[max_chars:]]


def _wrap_description(text: str, max_chars: int = 30) -> list[str]:
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


def _icon_lightning(cx: float, cy: float, color: str) -> str:
    return (
        f'<path transform="translate({cx - 6},{cy - 9})" '
        f'd="M7 0 L1 10 L5.5 10 L4 18 L11 8 L6.5 8 Z" fill="{color}"/>'
    )


def _icon_play(cx: float, cy: float, color: str) -> str:
    return f'<path transform="translate({cx - 6},{cy - 7})" d="M0 0 L14 7 L0 14 Z" fill="{color}"/>'


def _icon_network(cx: float, cy: float, color: str) -> str:
    pts = [(cx - 9, cy + 6), (cx, cy - 8), (cx + 9, cy + 6)]
    lines = "".join(
        f'<line x1="{cx}" y1="{cy-2}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="1.4"/>'
        for x, y in pts
    )
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}"/>' for x, y in pts)
    return lines + dots + f'<circle cx="{cx}" cy="{cy - 2}" r="3" fill="{color}"/>'


def _icon_cart(cx: float, cy: float, color: str) -> str:
    return (
        f'<g transform="translate({cx - 9},{cy - 7})" fill="none" stroke="{color}" stroke-width="1.5">'
        f'<path d="M0 0 H3 L5.5 11 H15 L17 3 H4.5"/>'
        f'<circle cx="7" cy="15" r="1.6" fill="{color}"/>'
        f'<circle cx="13.5" cy="15" r="1.6" fill="{color}"/>'
        f"</g>"
    )


def _icon_default(cx: float, cy: float, color: str) -> str:
    return (
        f'<text x="{cx}" y="{cy + 5}" font-family="Consolas, Menlo, monospace" font-size="16" '
        f'font-weight="700" fill="{color}" text-anchor="middle">&lt;/&gt;</text>'
    )


_ICON_FUNCS = {
    "lightning": _icon_lightning,
    "play": _icon_play,
    "network": _icon_network,
    "cart": _icon_cart,
}


def _project_icon(cx: float, cy: float, icon_key: str, accent: str) -> str:
    glyph_fn = _ICON_FUNCS.get(icon_key, _icon_default)
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{ICON_RADIUS}" fill="{accent}" fill-opacity="0.13" '
        f'stroke="{accent}" stroke-width="1.5"/>'
        f"{glyph_fn(cx, cy, accent)}"
    )


def render_single_project_card_svg(project: dict, theme_name: str = DEFAULT_THEME) -> str:
    """Build the SVG for one project's visual card (icon + name + description)."""
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"

    name = project.get("name", "")
    description = project.get("description", "")
    icon_key = project.get("icon", "")

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

    return f"""<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(name)}">
  <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="10" fill="#{CARD_BG}" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
  {_project_icon(CARD_WIDTH / 2, icon_cy, icon_key, accent)}
  {name_elements}
  {desc_elements}
</svg>"""


def _eye_icon(cx: float, cy: float, color: str) -> str:
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="7" ry="4.2" fill="none" stroke="{color}" stroke-width="1.4"/>'
        f'<circle cx="{cx}" cy="{cy}" r="2.1" fill="{color}"/>'
    )


def render_link_badge_svg(
    kind: str, theme_name: str = DEFAULT_THEME, disabled: bool = False
) -> str:
    """
    Build one small badge: kind is "view" or "code". These are the
    pieces that actually become clickable, once wrapped in a markdown
    link in the template.

    `disabled=True` renders a muted, non-link-implying version (used
    for "not hosted yet").
    """
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}" if not disabled else "#5a5a66"
    dark = f"#{theme['label_color']}"
    label = "View" if kind == "view" else "Code"

    icon_x = 16
    if kind == "view":
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
  <text x="{BADGE_WIDTH / 2 + 9}" y="{BADGE_HEIGHT / 2 + 4}" \
font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" font-weight="600" \
fill="{accent}" text-anchor="middle">{_esc(label)}</text>
</svg>"""
