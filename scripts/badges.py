"""
badges.py  (Phase 8)

Turns stat values into shields.io "static badge" markdown images, colored
with whichever theme is active. This is the actual color/visual-styling
layer - everything else in the project (avatar ASCII, CRT effects, boot
sequence) is plain text and can't have color in a GitHub-rendered README.

Shields.io static badge URL shape:
    https://img.shields.io/badge/<LABEL>-<MESSAGE>-<COLOR>?style=...&labelColor=...

Both LABEL and MESSAGE need shields.io's own escaping (literal '-' and '_'
have special meaning in that path segment) before normal URL-encoding.
"""

from __future__ import annotations

from urllib.parse import quote

from themes import DEFAULT_THEME, get_theme


def _escape_segment(text: str) -> str:
    """
    Shields.io reserves '-' and '_' as separators within a badge path
    segment, so a literal '-' must become '--' and '_' must become '__'
    before the segment is placed between the URL's own '-' separators.
    Spaces become '_' (shields.io renders that back as a space).
    """
    text = str(text)
    text = text.replace("-", "--").replace("_", "__")
    text = text.replace(" ", "_")
    return quote(text, safe="_")


def _darken(hex_color: str, factor: float = 0.55) -> str:
    """
    Shields.io badges render their message-side box at full, flat
    saturation - fine for most themes, but HUD's neon cyan reads as too
    bright/glary at that size and solidity. Scale RGB down instead of
    swapping the whole theme's accent, so every other component that
    reads the same theme.color for glow/line work is unaffected.
    """
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r, g, b = (max(0, int(c * factor)) for c in (r, g, b))
    return f"{r:02x}{g:02x}{b:02x}"


def badge_markdown(label: str, message: str, theme_name: str = DEFAULT_THEME) -> str:
    """Build one markdown image badge string for `label: message`, theme-colored."""
    theme = get_theme(theme_name)
    url = (
        f"https://img.shields.io/badge/{_escape_segment(label)}-{_escape_segment(message)}"
        f"-{_darken(theme['color'])}"
        f"?style={theme['style']}&labelColor={theme['label_color']}"
    )
    alt = f"{label}: {message}"
    return f"![{alt}]({url})"


def build_stat_badges(stats: dict, theme_name: str = DEFAULT_THEME) -> list[str]:
    """
    Build the curated row of badges shown near the top of the README.
    `stats` is expected to be (a subset of) the render context - only the
    keys used below need to be present.
    """
    badges = [
        badge_markdown("Repos", stats.get("repo_count", "?"), theme_name),
        badge_markdown("Stars", stats.get("stars", "?"), theme_name),
        badge_markdown("Followers", stats.get("followers", "?"), theme_name),
    ]

    solved = stats.get("solved")
    if solved:
        badges.append(badge_markdown("LC Solved", solved.get("total", "?"), theme_name))

    rating = stats.get("rating")
    if rating is not None:
        badges.append(badge_markdown("LC Rating", rating, theme_name))

    return badges


# ── Stats strip (replaces the shields.io badge row) ──────────────────────
import html as _html

from themes import HUD_COLORS

STRIP_W = 820
STRIP_H = 104


def _fmt_stat(value) -> str:
    if isinstance(value, (int, float)):
        return f"{value:,.0f}"
    return _html.escape(str(value))


def render_stats_strip_svg(stats: dict, theme_name: str = DEFAULT_THEME, for_light_mode: bool = False) -> str:
    """
    One wide chamfered panel with big gold numbers and small mono labels
    separated by thin dividers - the stats block from the "About" reference,
    fed with live GitHub and LeetCode numbers. Opaque enough in light mode
    to keep its white text readable.
    """
    gold = HUD_COLORS["modules"]
    bg = get_theme(theme_name)["label_color"]
    opacity = 0.96 if for_light_mode else 0.6
    solved = (stats.get("solved") or {}).get("total", "?")
    items = [
        (stats.get("repo_count", "?"), "REPOS"),
        (stats.get("stars", "?"), "STARS"),
        (stats.get("followers", "?"), "FOLLOWERS"),
        (solved, "LEETCODE SOLVED"),
    ]
    c = 14
    pts = [(c, 0), (STRIP_W - c, 0), (STRIP_W, c), (STRIP_W, STRIP_H - c), (STRIP_W - c, STRIP_H),
           (c, STRIP_H), (0, STRIP_H - c), (0, c)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    col_w = STRIP_W / len(items)
    cells = []
    for i, (value, label) in enumerate(items):
        cx = i * col_w + 36
        if i:
            cells.append(
                f'<line x1="{i * col_w:.1f}" y1="22" x2="{i * col_w:.1f}" y2="{STRIP_H - 22}" '
                f'stroke="white" stroke-opacity="0.12"/>'
            )
        cells.append(
            f'<text x="{cx:.1f}" y="60" font-family="Arial, Helvetica, sans-serif" font-size="40" '
            f'font-weight="800" fill="{gold}">{_fmt_stat(value)}</text>'
            f'<text x="{cx:.1f}" y="82" font-family="Consolas, Menlo, monospace" font-size="10" '
            f'fill="#9a9aa5" letter-spacing="1.5">{label}</text>'
        )
    return f"""<svg width="{STRIP_W}" height="{STRIP_H}" viewBox="0 0 {STRIP_W} {STRIP_H}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Profile stats">
  <polygon points="{poly}" fill="#{bg}" fill-opacity="{opacity}" stroke="white" stroke-opacity="0.14"/>
  <path d="M1 {c + 8} V{c} L{c} 1 H{c + 8} M{STRIP_W - c - 8} {STRIP_H - 1} H{STRIP_W - c} L{STRIP_W - 1} {STRIP_H - c} \
V{STRIP_H - c - 8}" fill="none" stroke="{gold}" stroke-width="1.6"/>
  {''.join(cells)}
</svg>"""
