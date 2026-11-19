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

from hud_grid import glow_filter
from themes import DEFAULT_THEME, HUD_COLORS

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


GOLD = HUD_COLORS["modules"]
GREEN = "#24FF9A"
BTN_W = 168
BTN_H = 46
CUT = 9


def _cut_box(w: float, h: float, c: float) -> str:
    pts = [(c, 0), (w - 0.5, 0), (w - 0.5, h - c), (w - c, h - 0.5), (0.5, h - 0.5), (0.5, c)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def render_link_pill_svg(
    label: str,
    icon_key: str,
    theme_name: str = DEFAULT_THEME,
    disabled: bool = False,
    primary: bool = False,
) -> str:
    """
    One contact button in the hero's button style: notched corners
    (top-left and bottom-right cut), a filled gold primary button and
    outlined dark secondary buttons. Both are opaque, so they read the
    same on GitHub's light and dark pages. `disabled=True` renders a
    muted version for a platform with no URL yet.
    """
    if disabled:
        fill, stroke, ink = "#07090F", f"#{PILL_BORDER_INACTIVE}", f"#{PILL_BORDER_INACTIVE}"
    elif primary:
        fill, stroke, ink = GOLD, GOLD, "#07090F"
    else:
        fill, stroke, ink = "#0b0f18", "#ffffff", "#ffffff"
    stroke_op = 1 if (primary or disabled) else 0.28

    icon_fn = _ICONS.get(icon_key, _icon_website)
    icon_svg = icon_fn(28, BTN_H / 2, ink if (primary or disabled) else GOLD)

    return f"""<svg width="{BTN_W}" height="{BTN_H}" viewBox="0 0 {BTN_W} {BTN_H}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(label)}">
  <polygon points="{_cut_box(BTN_W - 8, BTN_H, CUT)}" fill="{fill}" stroke="{stroke}" stroke-opacity="{stroke_op}" \
stroke-width="1.2"/>
  {icon_svg}
  <text x="50" y="{BTN_H / 2 + 5}" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="700" \
fill="{ink}" letter-spacing="0.8">{_esc(label.upper())}</text>
</svg>"""


def render_cta_button_svg(label: str, primary: bool = False, width: int = 170) -> str:
    """Hero call-to-action button as its own image so the template can wrap it in a real link."""
    w, h = width, 46
    fill, stroke, ink, op = (GOLD, GOLD, "#07090F", 1) if primary else ("#0b0f18", "#ffffff", "#ffffff", 0.28)
    arrow = (f'<path d="M{w - 38} {h / 2} H{w - 24} M{w - 29} {h / 2 - 5} L{w - 24} {h / 2} L{w - 29} {h / 2 + 5}" '
             f'fill="none" stroke="{ink}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(label)}">
  <polygon points="{_cut_box(w - 8, h, CUT)}" fill="{fill}" stroke="{stroke}" stroke-opacity="{op}" stroke-width="1.2"/>
  <text x="22" y="{h / 2 + 5}" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="700" fill="{ink}" letter-spacing="0.8">{_esc(label.upper())}</text>
  {arrow}
</svg>"""


def render_signal_heading_svg(for_light_mode: bool = False) -> str:
    """Hero-style heading, left-aligned like every other section: corner-marked tag, two-tone title, paragraph."""
    ink = "#10131a" if for_light_mode else "#ffffff"
    muted = "#4b5563" if for_light_mode else "#9a9aa5"
    tw, th, n = 150, 28, 6
    marks = (
        f'<path d="M0 {n} V0 H{n} M{tw - n} 0 H{tw} V{n} M{tw} {th - n} V{th} H{tw - n} '
        f'M{n} {th} H0 V{th - n}" fill="none" stroke="{GOLD}" stroke-width="1.4"/>'
    )
    return f"""<svg width="820" height="206" viewBox="0 0 820 206" xmlns="http://www.w3.org/2000/svg" \
role="img" aria-label="Signal uplink">
  <defs>{glow_filter()}</defs>
  {marks}
  <text x="{tw / 2}" y="19" font-family="Consolas, Menlo, monospace" font-size="12" fill="{GOLD}" text-anchor="middle" \
letter-spacing="2" filter="url(#hudglow)">SIGNAL UPLINK</text>
  <text x="0" y="84" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="800" \
fill="{ink}" letter-spacing="0.5">LET&#8217;S BUILD</text>
  <text x="0" y="132" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="800" \
fill="{GOLD}" letter-spacing="0.5">SOMETHING BOLD</text>
  <text x="0" y="170" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" fill="{muted}">\
Full-stack builds, clean interfaces, and tools that ship.</text>
  <text x="0" y="190" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" fill="{muted}">\
Pick a channel below and say hello.</text>
</svg>"""


def render_status_bar_svg(for_light_mode: bool = False) -> str:
    """Hero-style footer line: green status on the left, a fading rule, a hint on the right."""
    ink = "#10131a" if for_light_mode else "#ffffff"
    muted = "#4b5563" if for_light_mode else "#6b7a8c"
    return f"""<svg width="820" height="44" viewBox="0 0 820 44" xmlns="http://www.w3.org/2000/svg" \
role="img" aria-label="Status">
  <defs>
    <linearGradient id="rule" x1="0" x2="1">
      <stop offset="0" stop-color="{muted}" stop-opacity="0.9"/>
      <stop offset="1" stop-color="{muted}" stop-opacity="0.08"/>
    </linearGradient>
  </defs>
  <circle cx="6" cy="22" r="3.5" fill="{GREEN}"/>
  <text x="18" y="26" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{GREEN}">STATUS:</text>
  <text x="72" y="26" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{ink}">OPEN FOR COLLABORATION</text>
  <rect x="250" y="21.5" width="360" height="1" fill="url(#rule)"/>
  <text x="820" y="26" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{muted}" \
text-anchor="end">SCROLL TO EXPLORE</text>
</svg>"""


def render_spacer_svg(width: int, height: int, text: str = "") -> str:
    """Transparent filler image (optionally with a muted note) used to pad a row of images to exactly 820px."""
    note = (f'<text x="14" y="{height / 2 + 4}" font-family="Consolas, Menlo, monospace" font-size="11" '
            f'fill="#6b7a8c" letter-spacing="0.6">{_esc(text)}</text>') if text else ""
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="">{note}</svg>')
