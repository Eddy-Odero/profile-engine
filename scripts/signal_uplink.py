"""
signal_uplink.py

"Signal Uplink" - a row of social/contact pills, matching the reference
design. Same clickability constraint as project_cards.py's View/Code
badges: SVGs loaded via markdown image syntax have all internal links
stripped, so each pill is its own small standalone image, wrapped in a
real markdown link by the template - that's what makes it clickable.

Icons are generic hand-drawn glyphs (bird/chat shape, network/connection
shape, globe, envelope, controller-ish shape) rather than the literal
trademarked platform logos.

Usage:
    from signal_uplink import render_link_pill_svg
    svg_markup = render_link_pill_svg("Twitter", "twitter", theme_name)
"""

from __future__ import annotations

import html

from hud_grid import glow_filter, grid_background
from themes import DEFAULT_THEME, get_theme

PILL_WIDTH = 150
PILL_HEIGHT = 44
PILL_BG = "07090F"  # exact background from spec (was "0a0c14", a near-miss approximation)
PILL_BORDER_INACTIVE = "2a3040"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _icon_twitter(cx: float, cy: float, color: str) -> str:
    return (
        f'<path transform="translate({cx-8},{cy-6})" d="M0 10 Q2 2 8 1 Q7 0 9 0 '
        f'Q11 2 10 4 Q15 3 16 0 Q15 5 12 6 Q13 12 6 13 Q2 13 0 10 Z" '
        f'fill="none" stroke="{color}" stroke-width="1.3"/>'
    )


def _icon_linkedin(cx: float, cy: float, color: str) -> str:
    return (
        f'<g transform="translate({cx-8},{cy-8})" fill="{color}">'
        f'<circle cx="2.5" cy="2.5" r="2.2"/>'
        f'<rect x="0.7" y="6" width="3.6" height="10" />'
        f'<path d="M8 6 H11.5 V8 C12.3 6.5 14 6 15.5 7 C17 8 17 10 17 12 V16 H13.5 V12.5 '
        f'C13.5 11 13 10.3 11.8 10.3 C10.6 10.3 10 11 10 12.5 V16 H8 Z"/>'
        f"</g>"
    )


def _icon_website(cx: float, cy: float, color: str) -> str:
    return (
        f'<g transform="translate({cx},{cy})" fill="none" stroke="{color}" stroke-width="1.3">'
        f'<circle cx="0" cy="0" r="8"/>'
        f'<ellipse cx="0" cy="0" rx="3.5" ry="8"/>'
        f'<line x1="-8" y1="0" x2="8" y2="0"/>'
        f"</g>"
    )


def _icon_email(cx: float, cy: float, color: str) -> str:
    return (
        f'<g transform="translate({cx-9},{cy-6})" fill="none" stroke="{color}" stroke-width="1.3">'
        f'<rect x="0" y="0" width="18" height="12" rx="1"/>'
        f'<path d="M0 1 L9 8 L18 1"/>'
        f"</g>"
    )


def _icon_discord(cx: float, cy: float, color: str) -> str:
    return (
        f'<g transform="translate({cx-9},{cy-6})" fill="none" stroke="{color}" stroke-width="1.3">'
        f'<rect x="0" y="2" width="18" height="9" rx="4"/>'
        f'<circle cx="5" cy="6.5" r="1.2" fill="{color}" stroke="none"/>'
        f'<circle cx="13" cy="6.5" r="1.2" fill="{color}" stroke="none"/>'
        f"</g>"
    )


_ICONS = {
    "twitter": _icon_twitter,
    "linkedin": _icon_linkedin,
    "website": _icon_website,
    "email": _icon_email,
    "discord": _icon_discord,
}


def render_link_pill_svg(
    label: str, icon_key: str, theme_name: str = DEFAULT_THEME, disabled: bool = False
) -> str:
    """
    Build one signal-uplink pill: icon + label. `disabled=True` renders
    a muted, non-link-implying version (used when there's no real URL
    for this platform yet, e.g. Discord with no invite link provided).
    """
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}" if not disabled else f"#{PILL_BORDER_INACTIVE}"
    border = accent if not disabled else f"#{PILL_BORDER_INACTIVE}"

    icon_fn = _ICONS.get(icon_key, _icon_website)
    icon_cx = 26
    icon_svg = icon_fn(icon_cx, PILL_HEIGHT / 2, accent)

    grid_defs, grid_rect = grid_background(PILL_WIDTH, PILL_HEIGHT, accent, spacing=10, rx=22)
    glow_defs = glow_filter() if not disabled else ""
    text_filter = ' filter="url(#hudglow)"' if not disabled else ""

    return f"""<svg width="{PILL_WIDTH}" height="{PILL_HEIGHT}" \
viewBox="0 0 {PILL_WIDTH} {PILL_HEIGHT}" xmlns="http://www.w3.org/2000/svg" \
role="img" aria-label="{_esc(label)}">
  <defs>{grid_defs}{glow_defs}</defs>
  <rect width="{PILL_WIDTH}" height="{PILL_HEIGHT}" rx="22" fill="#{theme['label_color']}" \
stroke="{border}" stroke-width="1.3"/>
  {grid_rect}
  {icon_svg}
  <text x="{icon_cx + 20}" y="{PILL_HEIGHT / 2 + 5}" font-family="Consolas, Menlo, monospace" \
font-size="13" font-weight="600" fill="{accent}"{text_filter}>{_esc(label)}</text>
</svg>"""
