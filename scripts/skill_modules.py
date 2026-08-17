"""
skill_modules.py

"System Modules" - a grid of skill badges styled like a sci-fi HUD
component: a circular icon badge, corner-bracket frame decorations
(like a targeting reticle/scanner UI), the skill name, and a
proficiency level. Modeled directly on a design reference provided.

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

CARD_WIDTH = 170
CARD_HEIGHT = 150
CARD_GAP = 14
CARDS_PER_ROW = 4
BADGE_RADIUS = 26
BRACKET_LEN = 16
BRACKET_INSET = 6

CARD_BG = "07090F"  # exact background from spec, subtle navy tint
CARD_BORDER = "1c2a3a"
MUTED = "6b7a8c"

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


def _corner_brackets(x: float, y: float, accent: str) -> str:
    """Four L-shaped corner marks, like a HUD scanner/targeting frame."""
    corners = [
        (x + BRACKET_INSET, y + BRACKET_INSET, 1, 1),  # top-left
        (x + CARD_WIDTH - BRACKET_INSET, y + BRACKET_INSET, -1, 1),  # top-right
        (x + BRACKET_INSET, y + CARD_HEIGHT - BRACKET_INSET, 1, -1),  # bottom-left
        (x + CARD_WIDTH - BRACKET_INSET, y + CARD_HEIGHT - BRACKET_INSET, -1, -1),  # bottom-right
    ]
    marks = []
    for cx, cy, dx, dy in corners:
        marks.append(
            f'<path d="M{cx} {cy + dy * BRACKET_LEN} L{cx} {cy} L{cx + dx * BRACKET_LEN} {cy}" '
            f'fill="none" stroke="{accent}" stroke-width="2" filter="url(#hudglow)"/>'
        )
    return "".join(marks)


def _badge(x: float, y: float, skill: str, level: str, accent: str, bracket_color: str) -> str:
    color = _skill_color(skill, accent)
    badge_cx = x + CARD_WIDTH / 2
    badge_cy = y + 44
    icon_inner = _icon_inner_markup(skill)
    icon_size = 26
    if icon_inner:
        # All source icons share a 128x128 viewBox, so one scale factor
        # works for all of them: scale to icon_size, then translate so
        # that scaled icon is centered on (badge_cx, badge_cy).
        scale = icon_size / 128
        tx = badge_cx - icon_size / 2
        ty = badge_cy - icon_size / 2
        icon_markup = f'<g transform="translate({tx:.1f},{ty:.1f}) scale({scale:.4f})">{icon_inner}</g>'
    else:
        # Unmapped skill - fall back to a plain text glyph rather than
        # showing nothing.
        icon_markup = (
            f'<text x="{badge_cx}" y="{badge_cy + 8}" font-size="22" '
            f'text-anchor="middle">{_esc(skill[:2].upper())}</text>'
        )

    return f"""
  <g>
    <rect x="{x}" y="{y}" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" fill="#{CARD_BG}" fill-opacity="0.3" \
stroke="#{CARD_BORDER}" stroke-width="1"/>
    {_corner_brackets(x, y, bracket_color)}
    <circle cx="{badge_cx}" cy="{badge_cy}" r="{BADGE_RADIUS}" fill="{color}" fill-opacity="0.12" \
stroke="{color}" stroke-width="2"/>
    {icon_markup}
    <text x="{badge_cx}" y="{y + 100}" font-family="Consolas, Menlo, monospace" font-size="12" \
font-weight="700" fill="white" text-anchor="middle" letter-spacing="0.5">{_esc(skill.upper())}</text>
    <text x="{badge_cx}" y="{y + 118}" font-family="Consolas, Menlo, monospace" font-size="9" \
fill="#{MUTED}" text-anchor="middle" letter-spacing="1">{_esc(level.upper())}</text>
  </g>"""


def render_skill_modules_svg(
    skills: list[tuple[str, str]], theme_name: str = DEFAULT_THEME
) -> str:
    """
    Build the SVG for the skill modules grid. `skills` is a list of
    (name, proficiency_level) tuples. Wraps into rows of CARDS_PER_ROW.

    Corner brackets use the exact reference gold (#FFB917), sampled
    directly from the design image, rather than the active theme's
    accent - this section's bracket color doesn't change with theme,
    matching the reference exactly.
    """
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"
    bracket_color = HUD_COLORS["modules"]

    if not skills:
        skills = [("more skills coming soon", "")]

    rows = [skills[i : i + CARDS_PER_ROW] for i in range(0, len(skills), CARDS_PER_ROW)]
    cols_in_widest_row = max(len(row) for row in rows)

    width = cols_in_widest_row * CARD_WIDTH + (cols_in_widest_row - 1) * CARD_GAP
    height = len(rows) * CARD_HEIGHT + (len(rows) - 1) * CARD_GAP

    badges = []
    for row_i, row in enumerate(rows):
        for col_i, (skill, level) in enumerate(row):
            x = col_i * (CARD_WIDTH + CARD_GAP)
            y = row_i * (CARD_HEIGHT + CARD_GAP)
            badges.append(_badge(x, y, skill, level, accent, bracket_color))

    grid_defs, grid_rect = grid_background(width, height, accent, spacing=20)

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="System modules">
  <defs>{grid_defs}{glow_filter()}</defs>
  {grid_rect}
  {''.join(badges)}
</svg>"""
