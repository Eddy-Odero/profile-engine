"""
skill_modules.py

"System Modules" - restyled to match the services-list design
reference (bracket-style tag label, bold two-tone section heading,
rows with an index number, icon, title + caption, a decorative
expand/collapse "+" mark, and a divider line under each row) while
keeping this project's own HUD palette and real devicon logos - the
new layout/typography language applied on top of the existing colors,
not a palette swap.

Real per-skill logos via devicon (MIT-licensed, individual SVG icons:
https://github.com/devicons/devicon), pulled from the actual npm
package and stored locally in assets/icons/, then embedded INLINE
(their <path>/<g> content copied directly into our own SVG) rather
than referenced by external URL.

That distinction matters: a first version used <image href="https://
...">, but browsers refuse to let an SVG loaded via a plain <img> tag
(which is exactly how GitHub renders a markdown image) make its own
secondary network requests for referenced resources inside it - a
security restriction on "image context" SVGs, not a GitHub-specific
quirk. So external icon references silently don't load, no matter how
correct the URL is. Inlining the actual path data sidesteps that
entirely since there's no second request to make - the whole image is
one self-contained file.

Falls back to a plain 2-letter text glyph only for a skill with no
local icon file, so an unmapped skill degrades gracefully instead of
showing nothing.

Usage:
    from skill_modules import render_skill_modules_svg
    svg_markup = render_skill_modules_svg(
        [("Go", "Advanced"), ("JavaScript", "Expert")], theme_name)
"""

from __future__ import annotations

import html
import re

from hud_grid import glow_filter, grid_background
from tech_pills import TECH_COLORS
from themes import DEFAULT_THEME, HUD_COLORS, get_theme
from utils import ASSETS_DIR

WIDTH = 820
COLS = 2
COL_GAP = 32
COL_WIDTH = (WIDTH - COL_GAP * (COLS - 1)) // COLS
ROW_HEIGHT = 68
ICON_R = 18

TAG_Y = 18
HEADING_Y = 68
SUBTITLE_Y = 94
LIST_TOP = 128
BOTTOM_PAD = 12

MUTED = "6b7a8c"
MUTED_LIGHT = "4b5563"

# Real language/tool logos, stored locally as assets/icons/*.svg (pulled
# from the actual devicon npm package - see module docstring for why
# they're inlined rather than linked).
ICON_FILES: dict[str, str] = {
    "python": "python-original.svg",
    "go": "go-original.svg",
    "javascript": "javascript-original.svg",
    "typescript": "typescript-original.svg",
    "php": "php-original.svg",
    "node.js": "nodejs-original.svg",
    "nodejs": "nodejs-original.svg",
    "c++": "cplusplus-original.svg",
    "html": "html5-original.svg",
    "css": "css3-original.svg",
    "html/css": "html5-original.svg",
    "c": "c-original.svg",
    "sqlite": "sqlite-original.svg",
    "postgresql": "postgresql-original.svg",
    "docker": "docker-original.svg",
    "git": "git-original.svg",
    "figma": "figma-original.svg",
    "blender": "blender-original.svg",
    "redis": "redis-original.svg",
    "rust": "rust-original.svg",
    "kubernetes": "kubernetes-plain.svg",
}

_ICON_INNER_RE = re.compile(r"<svg[^>]*>(.*)</svg>", re.DOTALL)
_icon_cache: dict[str, str] = {}


def _icon_inner_markup(label: str) -> str | None:
    """
    Read a local devicon SVG file and return just its inner content
    (everything between the outer <svg> tags), cached after first
    read. All of these share a 128x128 viewBox, so the caller can
    apply one consistent scale/translate regardless of which icon it
    is.
    """
    filename = ICON_FILES.get(label.lower())
    if not filename:
        return None
    if filename in _icon_cache:
        return _icon_cache[filename]
    path = ASSETS_DIR / "icons" / filename
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _ICON_INNER_RE.search(raw)
    inner = match.group(1) if match else None
    if inner:
        # Some source icons (e.g. Go) use xlink:href inside a <use>,
        # with xmlns:xlink declared on the SOURCE file's own root <svg>
        # tag - which we don't keep, since we only extract inner
        # content. Plain `href` is the modern SVG2 attribute and needs
        # no namespace declaration at all, so swap to that instead of
        # re-declaring xmlns:xlink on every file that embeds an icon.
        inner = inner.replace("xlink:href", "href")
    _icon_cache[filename] = inner
    return inner


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _skill_color(label: str, fallback: str) -> str:
    hex_color = TECH_COLORS.get(label.lower())
    return f"#{hex_color}" if hex_color else fallback


def _tag_label(text: str, color: str) -> str:
    return (
        f'<text x="0" y="18" font-family="Consolas, Menlo, monospace" font-size="12" font-weight="700" '
        f'fill="{color}" letter-spacing="3" filter="url(#hudglow)">[ {_esc(text.upper())} ]</text>'
    )


# Categories for the accordion list (first one is drawn expanded).
CATEGORIES = [
    ("Languages", "Core languages I reach for daily.", ["Python", "TypeScript", "Go", "Rust", "PHP", "C"]),
    ("Web & Data", "Interfaces and storage.", ["JavaScript", "HTML/CSS", "SQLite"]),
    ("Tooling", "Ship and run it.", ["Docker", "Git"]),
    ("Creative", "3D and visual work.", ["Blender"]),
]

CARD_BG = "07090F"
CARD_BORDER = "1c2a3a"
MUTED = "6b7a8c"
LEFT_W = 290
PX = 320  # right panel x
PW = WIDTH - PX
CARD_W, CARD_H, CGAP = 107, 118, 10
PANEL_PAD = 20
TOP = 150
CUT = 14


def _cat_glyph(i: int, cx: float, cy: float, c: str) -> str:
    g = f'<g transform="translate({cx},{cy})" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    if i == 0:
        g += '<path d="M-4 -6 L-10 0 L-4 6 M4 -6 L10 0 L4 6 M1.5 -8 L-1.5 8"/>'
    elif i == 1:
        g += '<ellipse cx="0" cy="-6" rx="8" ry="3"/><path d="M-8 -6 V6 A8 3 0 0 0 8 6 V-6 M-8 0 A8 3 0 0 0 8 0"/>'
    elif i == 2:
        g += '<circle cx="0" cy="0" r="3.5"/><path d="M0 -9 V-6 M0 6 V9 M-9 0 H-6 M6 0 H9 M-6.4 -6.4 L-4.4 -4.4 M4.4 4.4 L6.4 6.4 M-6.4 6.4 L-4.4 4.4 M4.4 -4.4 L6.4 -6.4"/>'
    else:
        g += '<path d="M0 -9 L9 -4 V5 L0 9 L-9 5 V-4 Z M-9 -4 L0 1 L9 -4 M0 1 V9"/>'
    return g + "</g>"


def _tile(cx: float, cy: float, glyph: str, gold: str) -> str:
    x, y, n, t = cx - 20, cy - 20, 6, 40
    marks = (
        f'<path d="M{x} {y+n} V{y} H{x+n} M{x+t-n} {y} H{x+t} V{y+n} M{x+t} {y+t-n} V{y+t} H{x+t-n} '
        f'M{x+n} {y+t} H{x} V{y+t-n}" fill="none" stroke="{gold}" stroke-width="1.3"/>'
    )
    return f'<rect x="{x+3}" y="{y+3}" width="{t-6}" height="{t-6}" rx="8" fill="#0b0f18" stroke="white" stroke-opacity="0.12"/>{marks}{glyph}'


def _check(x: float, y: float, c: str) -> str:
    return f'<path d="M{x} {y} l3 3 l6 -6.5" fill="none" stroke="{c}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'


def _icon(skill: str, cx: float, cy: float, size: float, accent: str) -> str:
    inner = _icon_inner_markup(skill)
    if inner:
        sc = size / 128
        return f'<g transform="translate({cx - size / 2:.1f},{cy - size / 2:.1f}) scale({sc:.4f})">{inner}</g>'
    return (
        f'<text x="{cx}" y="{cy + 5}" font-size="{size * 0.6:.0f}" font-weight="700" fill="{accent}" '
        f'text-anchor="middle">{_esc(skill[:2].upper())}</text>'
    )


def _badge(x: float, y: float, skill: str, level: str, accent: str, gold: str) -> str:
    """Original HUD badge card (corner brackets, icon circle, name, level), resized for the panel."""
    color = _skill_color(skill, accent)
    cx, cy = x + CARD_W / 2, y + 38
    b, ln = 6, 12
    corners = [(x + b, y + b, 1, 1), (x + CARD_W - b, y + b, -1, 1), (x + b, y + CARD_H - b, 1, -1), (x + CARD_W - b, y + CARD_H - b, -1, -1)]
    marks = "".join(
        f'<path d="M{px} {py + dy * ln} L{px} {py} L{px + dx * ln} {py}" fill="none" stroke="{gold}" stroke-width="1.8" filter="url(#hudglow)"/>'
        for px, py, dx, dy in corners
    )
    name = skill.upper()
    return f"""
  <g>
    <rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" fill="#{CARD_BG}" fill-opacity="0.85" stroke="#{CARD_BORDER}"/>
    {marks}
    <circle cx="{cx}" cy="{cy}" r="22" fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-width="2"/>
    {_icon(skill, cx, cy, 22, color)}
    <text x="{cx}" y="{y + 84}" font-family="Consolas, Menlo, monospace" font-size="11" font-weight="700" fill="white" text-anchor="middle" letter-spacing="0.4">{_esc(name)}</text>
    <text x="{cx}" y="{y + 100}" font-family="Consolas, Menlo, monospace" font-size="8.5" fill="#{MUTED}" text-anchor="middle" letter-spacing="1">{_esc(level.upper())}</text>
  </g>"""


def render_skill_modules_svg(
    skills: list[tuple[str, str]], theme_name: str = DEFAULT_THEME, for_light_mode: bool = False
) -> str:
    """
    Tech stack in the "What I Create" layout: tag + two-tone heading, a
    description with a short rule on the right, a left category accordion
    (first category expanded with a 2-column checklist) and a big chamfered
    panel on the right holding the original badge-card grid.
    """
    gold = HUD_COLORS["modules"]
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"
    bg = f"#{CARD_BG}"
    panel_op = 0.96 if for_light_mode else 0.55
    ink = "#10131a" if for_light_mode else "#ffffff"
    muted = "#4b5563" if for_light_mode else "#9a9aa5"
    levels = {n.lower(): lv for n, lv in skills}

    # --- left accordion ---
    parts = []
    y = TOP
    for i, (cat, blurb, items) in enumerate(CATEGORIES):
        if i == 0:
            h = 196
            rows = [items[j:j + 2] for j in range(0, len(items), 2)]
            chk = "".join(
                _check(24 + k * 130, 150 + r * 28, gold)
                + f'<text x="{42 + k * 130}" y="{154 + r * 28}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="12" fill="#c9c9d2">{_esc(t)}</text>'
                for r, row in enumerate(rows[:3]) for k, t in enumerate(row)
            )
            h = 150 + min(len(rows), 3) * 28 + 6
            parts.append(f"""
  <g transform="translate(0,{y})">
    <polygon points="0,{CUT} {CUT},0 {LEFT_W},0 {LEFT_W},{h - CUT} {LEFT_W - CUT},{h} 0,{h}" fill="{bg}" fill-opacity="{0.96 if for_light_mode else 0.7}" stroke="white" stroke-opacity="0.12"/>
    {_tile(44, 38, _cat_glyph(i, 44, 38, gold), gold)}
    <text x="80" y="36" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" fill="{gold}" letter-spacing="0.8">{_esc(cat.upper())}</text>
    <text x="80" y="56" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" fill="#9a9aa5">{_esc(blurb)}</text>
    <path d="M{LEFT_W - 30} 38 H{LEFT_W - 16}" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
    <line x1="20" y1="106" x2="{LEFT_W - 20}" y2="106" stroke="white" stroke-opacity="0.14"/>
    <text x="24" y="128" font-family="Consolas, Menlo, monospace" font-size="9.5" fill="#6b7a8c" letter-spacing="1">{len(items)} MODULES</text>
    {chk}
  </g>""")
            y += h + 14
        else:
            h = 60
            tile_ink = "white"
            parts.append(f"""
  <g transform="translate(0,{y})">
    {_tile(44, 30, _cat_glyph(i, 44, 30, "white"), gold)}
    <text x="80" y="35" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" fill="{ink}" letter-spacing="0.8">{_esc(cat.upper())}</text>
    <path d="M{LEFT_W - 30} 30 H{LEFT_W - 16} M{LEFT_W - 23} 23 V37" stroke="{ink}" stroke-width="1.4" stroke-linecap="round"/>
  </g>""")
            y += h + 14
    left_h = y - 14

    # --- right panel ---
    order = [n for _, _, its in CATEGORIES for n in its]
    order += [n for n, _ in skills if n not in order]
    lookup = {n.lower(): n for n, _ in skills}
    order = [lookup[n.lower()] for n in order if n.lower() in lookup]
    cols = 4
    nrows = -(-len(order) // cols)
    grid_w = cols * CARD_W + (cols - 1) * CGAP
    inner_x = PX + (PW - grid_w) / 2
    panel_h = nrows * CARD_H + (nrows - 1) * CGAP + 2 * PANEL_PAD
    cards = "".join(
        _badge(inner_x + (i % cols) * (CARD_W + CGAP), TOP + PANEL_PAD + (i // cols) * (CARD_H + CGAP), n, levels.get(n.lower(), ""), accent, gold)
        for i, n in enumerate(order)
    )
    pts = f"{PX},{TOP + CUT} {PX + CUT},{TOP} {WIDTH - 0.5},{TOP} {WIDTH - 0.5},{TOP + panel_h - CUT} {WIDTH - CUT},{TOP + panel_h} {PX},{TOP + panel_h}"
    b = 10
    px0, px1, py0, py1 = PX + 8, WIDTH - 8, TOP + 8, TOP + panel_h - 8
    outer = (
        f'<path d="M{px0} {py0 + b} V{py0} H{px0 + b} M{px1 - b} {py0} H{px1} V{py0 + b} '
        f'M{px1} {py1 - b} V{py1} H{px1 - b} M{px0 + b} {py1} H{px0} V{py1 - b}" fill="none" stroke="{gold}" stroke-width="1.4"/>'
    )
    height = max(left_h, panel_h + TOP) + 10
    desc = "".join(
        f'<text x="{WIDTH}" y="{50 + j * 20}" text-anchor="end" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" fill="{muted}">{_esc(t)}</text>'
        for j, t in enumerate(["Languages, frameworks and tools for sharp", "interfaces, solid backends and shipped products."])
    )

    return f"""<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tech stack">
  <defs>{glow_filter()}</defs>
  {_tag_label("System Modules", gold)}
  <text x="0" y="62" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="800" fill="{ink}" letter-spacing="0.5">TOOLS FOR</text>
  <text x="0" y="100" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="800" fill="{gold}" letter-spacing="0.5">BOLD BUILDS</text>
  {desc}
  <text x="{WIDTH - 270}" y="104" font-family="Consolas, Menlo, monospace" font-size="11" fill="{gold}" letter-spacing="1.5">CORE STACK</text>
  <rect x="{WIDTH - 170}" y="100" width="170" height="1" fill="{gold}" fill-opacity="0.3"/>
  {''.join(parts)}
  <polygon points="{pts}" fill="{bg}" fill-opacity="{panel_op}" stroke="white" stroke-opacity="0.12"/>
  {outer}
  {cards}
</svg>"""
