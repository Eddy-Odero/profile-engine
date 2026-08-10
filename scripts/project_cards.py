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

from hud_grid import grid_background
from tech_pills import TECH_COLORS
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

CARD_WIDTH = 210
CARD_HEIGHT = 158  # +28 from the original 130 to fit the new stats row
ICON_RADIUS = 20

CARD_BG = "07090F"  # exact background from spec (was "16161c", an approximation)
CARD_BORDER = "2a2a33"  # subtle, barely-lighter-than-bg border
DESC_COLOR = "9a9aa5"  # muted gray for description text, per the reference's hierarchy
STAT_COLOR = "7d7d88"

RIBBON_COLORS = {"public": HUD_COLORS["ribbon_public"], "vip": HUD_COLORS["ribbon_vip"]}

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


def _ribbon(visibility: str, width: int = CARD_WIDTH) -> str:
    """A small diagonal corner ribbon showing PUBLIC/VIP, top-right of the card."""
    if not visibility:
        return ""
    color = RIBBON_COLORS.get(visibility.lower(), RIBBON_COLORS["public"])
    label = visibility.upper()
    # A small parallelogram tucked into the top-right corner, angled like a ribbon/flag
    return f"""
  <g>
    <polygon points="{width-70},14 {width-8},14 {width-8},30 {width-58},30" fill="{color}"/>
    <text x="{width-39}" y="26" font-family="Consolas, Menlo, monospace" font-size="9" \
font-weight="700" fill="#0a0a0d" text-anchor="middle">{_esc(label)}</text>
  </g>"""


def _star_icon(x: float, y: float, color: str) -> str:
    """A tiny 5-point star glyph for the stars stat."""
    import math
    pts = []
    for i in range(10):
        r = 5 if i % 2 == 0 else 2.2
        angle = math.pi / 2 + i * math.pi / 5
        pts.append(f"{x + r*math.cos(angle):.1f},{y - r*math.sin(angle):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{color}"/>'


def _fork_icon(x: float, y: float, color: str) -> str:
    """A tiny fork/branch glyph (two prongs merging into one line) for the forks stat."""
    return (
        f'<g stroke="{color}" stroke-width="1.3" fill="none">'
        f'<circle cx="{x}" cy="{y-4}" r="1.8" fill="{color}" stroke="none"/>'
        f'<circle cx="{x+6}" cy="{y-4}" r="1.8" fill="{color}" stroke="none"/>'
        f'<circle cx="{x+3}" cy="{y+4}" r="1.8" fill="{color}" stroke="none"/>'
        f'<path d="M{x} {y-4} V{y-1} Q{x} {y+1} {x+3} {y+1} V{y+4} '
        f'M{x+6} {y-4} V{y-1} Q{x+6} {y+1} {x+3} {y+1}"/>'
        f"</g>"
    )


def _stats_row(y: float, language: str, stars: int, forks: int, accent: str, width: int = CARD_WIDTH) -> str:
    """Language dot + name, star count, fork count - one row along the card bottom."""
    lang_hex = TECH_COLORS.get((language or "").lower())
    lang_color = f"#{lang_hex}" if lang_hex else accent

    parts = []
    lx = 16
    if language:
        parts.append(f'<circle cx="{lx}" cy="{y-3}" r="4" fill="{lang_color}"/>')
        parts.append(
            f'<text x="{lx+10}" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
            f'font-size="10" fill="#{STAT_COLOR}">{_esc(language)}</text>'
        )

    star_x = width - 62
    parts.append(_star_icon(star_x, y - 3, f"#{STAT_COLOR}"))
    parts.append(
        f'<text x="{star_x+9}" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="10" fill="#{STAT_COLOR}">{stars}</text>'
    )

    fork_x = width - 28
    parts.append(_fork_icon(fork_x, y - 3, f"#{STAT_COLOR}"))
    parts.append(
        f'<text x="{fork_x+11}" y="{y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
        f'font-size="10" fill="#{STAT_COLOR}">{forks}</text>'
    )

    return "".join(parts)


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

    grid_defs, grid_rect = grid_background(CARD_WIDTH, CARD_HEIGHT, accent, spacing=16, rx=10)

    return f"""<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(name)}">
  <defs>{grid_defs}</defs>
  {grid_rect}
  <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="10" fill="#{theme['label_color']}" fill-opacity="0.93" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
  {_ribbon(project.get("visibility", ""))}
  {_project_icon(CARD_WIDTH / 2, icon_cy, icon_key, accent)}
  {name_elements}
  {desc_elements}
  <line x1="14" y1="{CARD_HEIGHT - 26}" x2="{CARD_WIDTH - 14}" y2="{CARD_HEIGHT - 26}" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
  {_stats_row(CARD_HEIGHT - 10, project.get("language", ""), project.get("stars", 0), \
project.get("forks", 0), accent)}
</svg>"""


def render_project_card_simple_svg(project: dict, theme_name: str = DEFAULT_THEME) -> str:
    """
    The PLAIN project card used for the "Projects" section: icon, name,
    description - no PUBLIC/VIP ribbon, no language/star/fork stats
    row. Those live one level down, on the "Fragmented Data" section's
    cards (see fragmented_data.py, which reuses
    render_single_project_card_svg above) - the two sections show the
    same real project list but at different levels of detail, which is
    what actually distinguishes them visually, per the reference.

    This card is taller in the description area (no stats row eating
    into it) since the View/Code badges are rendered as separate images
    by the template, directly underneath.
    """
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"

    name = project.get("name", "")
    description = project.get("description", "")
    icon_key = project.get("icon", "")

    name_lines = _wrap_label(name)
    desc_lines = _wrap_description(description, max_chars=32)

    icon_cy = 34
    name_y = icon_cy + ICON_RADIUS + 20
    desc_start_y = name_y + len(name_lines) * 18 + 6
    card_height = desc_start_y + len(desc_lines) * 15 + 18

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

    grid_defs, grid_rect = grid_background(CARD_WIDTH, card_height, accent, spacing=16, rx=10)

    return f"""<svg width="{CARD_WIDTH}" height="{card_height}" viewBox="0 0 {CARD_WIDTH} {card_height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(name)}">
  <defs>{grid_defs}</defs>
  {grid_rect}
  <rect width="{CARD_WIDTH}" height="{card_height}" rx="10" fill="#{theme['label_color']}" fill-opacity="0.93" \
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
    # Orange - distinct from every other accent already in use (cyan,
    # green, gold, red, rose-pink, grey), and purple didn't land either.
    accent = "#FF8A3D" if not disabled else "#5a5a66"
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
