"""
fragmented_data.py

"Fragmented Data" - same card content/layout as the original project
card (icon centered above the title, centered description, bottom
stats row - reused as-is from project_cards.py), with two differences:
the card is a wide rectangle instead of a portrait rect, and its
top-right + bottom-left corners are chamfered (cut at 45 degrees)
instead of plain rounded corners.

The ribbon is the standard, unmodified _ribbon() shape from
project_cards.py - a normal compact parallelogram flag, not a custom
diagonal shape. It's wrapped in the card's own chamfer clip-path, so
the same cut that trims the card's corner also trims whatever part of
the ribbon sits past it. Kept simple on purpose after a detour into
custom-shaped ribbons that stopped looking like a ribbon at all.

Usage:
    from fragmented_data import render_fragment_card_svg
    svg_markup = render_fragment_card_svg(project, theme_name)
"""

from __future__ import annotations

from hud_grid import glass_frame_polygon, glow_filter, grid_background
from project_cards import (
    DESC_COLOR,
    ICON_RADIUS,
    _esc,
    _project_icon,
    RIBBON_COLORS,
    _stats_row,
    _wrap_description,
    _wrap_label,
)
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

WIDTH = 380
HEIGHT = 214
CHAMFER = 20  # size of the cut corner, top-right and bottom-left
PAD = 10
THUMB_H = 150
HEADING_WIDTH = 820
HEADING_HEIGHT = 132
GOLD = HUD_COLORS["modules"]


def _chamfered_points(width: float, height: float, cut: float) -> str:
    points = [
        (0, 0),
        (width - cut, 0),
        (width, cut),
        (width, height),
        (cut, height),
        (0, height - cut),
    ]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def render_fragment_heading_svg(theme_name: str = DEFAULT_THEME, for_light_mode: bool = False) -> str:
    """
    Section heading in the "Selected Work" reference style: bracket tag,
    bold two-tone title on the left, short description on the right.
    """
    ink = "#10131a" if for_light_mode else "#ffffff"
    muted = "#4b5563" if for_light_mode else "#9a9aa5"
    return f"""<svg width="{HEADING_WIDTH}" height="{HEADING_HEIGHT}" viewBox="0 0 {HEADING_WIDTH} {HEADING_HEIGHT}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Selected work">
  <defs>{glow_filter()}</defs>
  <text x="0" y="18" font-family="Consolas, Menlo, monospace" font-size="12" font-weight="700" \
fill="{GOLD}" letter-spacing="3" filter="url(#hudglow)">[ SELECTED WORK ]</text>
  <text x="0" y="64" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="800" \
fill="{ink}" letter-spacing="0.5">CRAFTED DIGITAL</text>
  <text x="0" y="106" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="800" \
fill="{GOLD}" letter-spacing="0.5">EXPERIENCES</text>
  <text x="{HEADING_WIDTH}" y="74" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" \
fill="{muted}" text-anchor="end">A curated collection of projects shaped with</text>
  <text x="{HEADING_WIDTH}" y="94" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" \
fill="{muted}" text-anchor="end">strong structure, clean code, and futuristic design.</text>
</svg>"""


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "\u2026"


_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def _project_image_uri(project: dict, box_w: int, box_h: int) -> str | None:
    """
    Look for a screenshot at assets/projects/<slug>.(png|jpg|webp), where
    slug is project["image"] if set, else the repo name from repo_url,
    else the project name (lowercased, spaces -> dashes). It's
    cover-cropped to the thumbnail box at 2x and embedded as a base64
    JPEG data URI - an SVG shown via <img> can't load external files, so
    the pixels have to live inside the SVG itself. Returns None when no
    image exists, and the card falls back to the icon panel.
    """
    import base64
    import io
    import re

    from utils import ASSETS_DIR

    slug = project.get("image") or ""
    if not slug:
        repo = (project.get("repo_url") or "").rstrip("/").split("/")[-1]
        slug = repo or project.get("name", "")
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    folder = ASSETS_DIR / "projects"
    path = next((folder / f"{slug}{e}" for e in _IMAGE_EXTS if (folder / f"{slug}{e}").exists()), None)
    if path is None:
        return None
    try:
        from PIL import Image, ImageOps

        img = Image.open(path).convert("RGB")
        img = ImageOps.fit(img, (box_w * 2, box_h * 2), method=Image.LANCZOS, centering=(0.5, 0.0))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=82, optimize=True)
    except Exception:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


CARD_W = 400
COL_GAP = 20
CARD_H = 280
CARD_PAD = 14
ROW_GAP = 14
CARD_THUMB_H = 196


def _card_subtitle(project: dict) -> str:
    """URL-style subtitle like the reference ('nivora.studio'): live host, else repo path, else 'Private'."""
    from urllib.parse import urlparse

    if (project.get("visibility") or "").lower() == "private":
        return "Private repository"
    url = project.get("preview_url") or project.get("repo_url") or ""
    parsed = urlparse(url)
    return (parsed.netloc + parsed.path).rstrip("/") or project.get("language", "")


def render_fragment_card_svg(
    project: dict, theme_name: str = DEFAULT_THEME, for_light_mode: bool = False, index: int | None = None,
    col: int = 0,
) -> str:
    """
    Portfolio tile, matching the "Selected Work" reference: a dark rounded
    card holding a large rounded thumbnail (a real screenshot from
    assets/projects/ if present, else an icon on a soft gradient), then an
    uppercase title, a muted URL-style subtitle and a diagonal arrow. No
    buttons: the whole tile is a link in the README. Opaque, so the same
    file works on GitHub's light and dark pages.

    The SVG is CARD_W + COL_GAP/2 wide and the card sits at the left edge
    (col 0) or right edge (col 1), so two tiles side by side add up to
    exactly 820px, the same width as every section heading above.
    """
    accent = HUD_COLORS["modules"]
    name = project.get("name", "")
    icon_key = project.get("icon", "")
    svg_w = CARD_W + COL_GAP // 2
    cx0 = 0 if col == 0 else COL_GAP // 2
    tw = CARD_W - 2 * CARD_PAD
    tx, ty = cx0 + CARD_PAD, CARD_PAD
    title_y = ty + CARD_THUMB_H + 32
    sub_y = title_y + 20
    image_uri = _project_image_uri(project, tw, CARD_THUMB_H)

    if image_uri:
        thumb = (
            f'<image x="{tx}" y="{ty}" width="{tw}" height="{CARD_THUMB_H}" href="{image_uri}" '
            f'preserveAspectRatio="xMidYMin slice"/>'
        )
    else:
        thumb = (
            f'<rect x="{tx}" y="{ty}" width="{tw}" height="{CARD_THUMB_H}" fill="url(#tilebg)"/>'
            f"{_project_icon(tx + tw / 2, ty + CARD_THUMB_H / 2, icon_key, accent)}"
        )

    return f"""<svg width="{svg_w}" height="{CARD_H + ROW_GAP}" viewBox="0 0 {svg_w} {CARD_H + ROW_GAP}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(name)}">
  <defs>
    <clipPath id="tclip"><rect x="{tx}" y="{ty}" width="{tw}" height="{CARD_THUMB_H}" rx="10"/></clipPath>
    <radialGradient id="tilebg" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#1c170b"/>
      <stop offset="100%" stop-color="#111116"/>
    </radialGradient>
  </defs>
  <rect x="{cx0 + 0.5}" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="14" fill="#0b0b0e" \
stroke="white" stroke-opacity="0.09"/>
  <g clip-path="url(#tclip)">{thumb}</g>
  <text x="{tx + 4}" y="{title_y}" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="800" \
fill="white" letter-spacing="0.6">{_esc(name.upper())}</text>
  <text x="{tx + 4}" y="{sub_y}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="12" \
fill="#9a9aa5" letter-spacing="0.3">{_esc(_card_subtitle(project).upper())}</text>
  <path d="M{tx + tw - 22} {title_y + 10} L{tx + tw - 8} {title_y - 4} M{tx + tw - 19} {title_y - 4} \
L{tx + tw - 8} {title_y - 4} L{tx + tw - 8} {title_y + 7}" fill="none" stroke="white" stroke-width="1.6" \
stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""
