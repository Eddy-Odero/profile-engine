"""
leetcode_panel.py

LeetCode stats, restyled to the "About" reference design: bracket tag
and two-tone heading with a short description on the right; a large
chamfered profile panel on the left (status line, title, three big
numbers, a 2x2 grid of chips, a signature footer); four numbered rows on
the right (icon box with gold corner marks, title, description, index);
and a hatched strip plus a status bar underneath. All text is reworded
for LeetCode and fed from the real stats.

Usage:
    from leetcode_panel import render_leetcode_panel_svg
    svg_markup = render_leetcode_panel_svg(leetcode_stats, theme_name)
"""

from __future__ import annotations

import html

from hud_grid import glow_filter
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

WIDTH = 820
LEFT_W = 400
RX = 420
RW = WIDTH - RX
TOP = 138
ROW_H = 96
ROW_GAP = 10
STRIP_H = 40
BAR_H = 40

GOLD = HUD_COLORS["modules"]
PINK = "#FF2279"  # exact rose-pink sampled from the earlier LeetCode reference
GREEN = "#24FF9A"
MUTED = "#9a9aa5"
DIM = "#6b7a8c"

# Small 20x20 line glyphs (drawn inside a translate).
GLYPHS = {
    "check": '<circle cx="10" cy="10" r="8"/><path d="M6 10.5 L9 13.5 L14.5 7"/>',
    "bars": '<path d="M4 16 V11 M10 16 V7 M16 16 V3"/>',
    "bolt": '<path d="M11.5 2 L5 11 H10 L8.5 18 L15 9 H10 Z"/>',
    "trophy": '<path d="M6 3 H14 V9 a4 4 0 0 1 -8 0 Z M6 5 H3 a3 3 0 0 0 3 4 M14 5 H17 a3 3 0 0 1 -3 4 '
    'M10 13 V16 M7 17 H13"/>',
    "star": '<path d="M10 2.5 L12.2 7.5 L17.5 8 L13.5 11.6 L14.7 17 L10 14.2 L5.3 17 L6.5 11.6 L2.5 8 L7.8 7.5 Z"/>',
    "layers": '<path d="M10 3 L17 7 L10 11 L3 7 Z M3 11 L10 15 L17 11"/>',
    "percent": '<path d="M15 5 L5 15"/><circle cx="6" cy="6" r="2"/><circle cx="14" cy="14" r="2"/>',
    "flag": '<path d="M5 17 V3 M5 4 H15 L13 7.5 L15 11 H5"/>',
}


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _glyph(name: str, x: float, y: float, color: str, size: float = 20, stroke: float = 1.5) -> str:
    scale = size / 20
    return (
        f'<g transform="translate({x},{y}) scale({scale})" fill="none" stroke="{color}" '
        f'stroke-width="{stroke / scale:.2f}" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[name]}</g>'
    )


def _corner_marks(x: float, y: float, w: float, h: float, color: str, n: float = 7) -> str:
    return (
        f'<path d="M{x} {y + n} V{y} H{x + n} M{x + w - n} {y} H{x + w} V{y + n} '
        f'M{x + w} {y + h - n} V{y + h} H{x + w - n} M{x + n} {y + h} H{x} V{y + h - n}" '
        f'fill="none" stroke="{color}" stroke-width="1.6"/>'
    )


def _chamfer(w: float, h: float, c: float) -> str:
    pts = [(c, 0), (w - c, 0), (w, c), (w, h - c), (w - c, h), (c, h), (0, h - c), (0, c)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def _fmt(value, fallback: str = "N/A") -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, (int, float)):
        return f"{value:,.0f}"
    return str(value)


def render_leetcode_panel_svg(stats: dict, theme_name: str = DEFAULT_THEME, for_light_mode: bool = False) -> str:
    bg = get_theme(theme_name)["label_color"]
    panel_opacity = 0.96 if for_light_mode else 0.6
    ink = "#10131a" if for_light_mode else "#ffffff"
    muted_ink = "#4b5563" if for_light_mode else MUTED

    solved = stats.get("solved", {}) or {}
    total = solved.get("total", 0) or 0
    easy = solved.get("easy", 0) or 0
    medium = solved.get("medium", 0) or 0
    hard = solved.get("hard", 0) or 0

    rows_h = 4 * ROW_H + 3 * ROW_GAP
    panel_h = rows_h + ROW_GAP + STRIP_H + ROW_GAP + BAR_H
    height = TOP + panel_h + 12

    # ---- left profile panel -------------------------------------------------
    stat_cols = [(f"{total}+", "SOLVED"), (str(medium), "MEDIUM"), (str(hard), "HARD")]
    col_w = (LEFT_W - 56) / 3
    stat_svg = []
    for i, (value, label) in enumerate(stat_cols):
        sx = 28 + i * col_w
        if i:
            stat_svg.append(
                f'<line x1="{sx - 14}" y1="188" x2="{sx - 14}" y2="236" stroke="white" stroke-opacity="0.12"/>'
            )
        stat_svg.append(
            f'<text x="{sx}" y="222" font-family="Arial, Helvetica, sans-serif" font-size="38" '
            f'font-weight="800" fill="{GOLD}">{_esc(value)}</text>'
            f'<text x="{sx}" y="244" font-family="Consolas, Menlo, monospace" font-size="10" '
            f'fill="{DIM}" letter-spacing="1">{label}</text>'
        )

    chips = [
        ("star", "RATING", _fmt(stats.get("rating"), "UNRATED")),
        ("layers", "RANK", _fmt(stats.get("ranking"))),
        ("percent", "TOP", f"{stats['top_percentage']}%" if stats.get("top_percentage") is not None else "N/A"),
        ("flag", "CONTESTS", _fmt(stats.get("contests_attended") or 0)),
    ]
    chip_w = (LEFT_W - 56 - 10) / 2
    chip_svg = []
    for i, (glyph, label, value) in enumerate(chips):
        cx = 28 + (i % 2) * (chip_w + 10)
        cy = 284 + (i // 2) * 54
        chip_svg.append(
            f'<rect x="{cx}" y="{cy}" width="{chip_w}" height="44" rx="6" fill="white" fill-opacity="0.04" '
            f'stroke="white" stroke-opacity="0.12"/>'
            + _glyph(glyph, cx + 12, cy + 12, "white", 20, 1.3)
            + f'<text x="{cx + 42}" y="{cy + 27}" font-family="Arial, Helvetica, sans-serif" font-size="11" '
            f'fill="white" letter-spacing="0.6">{label}</text>'
            f'<text x="{cx + chip_w - 12}" y="{cy + 27}" font-family="Consolas, Menlo, monospace" font-size="12" '
            f'font-weight="700" fill="{GOLD}" text-anchor="end">{_esc(value)}</text>'
        )

    left = f"""
  <g transform="translate(0,{TOP})">
    <polygon points="{_chamfer(LEFT_W, panel_h, 14)}" fill="#{bg}" fill-opacity="{panel_opacity}" \
stroke="white" stroke-opacity="0.14"/>
    <circle cx="34" cy="34" r="3.5" fill="{GREEN}" filter="url(#hudglow)"/>
    <text x="46" y="38" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="{GREEN}">STATUS:</text>
    <text x="99" y="38" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="white">SOLVING DAILY</text>
    <text x="28" y="82" font-family="Arial, Helvetica, sans-serif" font-size="19" font-weight="700" fill="white" \
letter-spacing="0.5">PROBLEM SOLVER &amp;</text>
    <text x="28" y="108" font-family="Arial, Helvetica, sans-serif" font-size="19" font-weight="700" fill="white" \
letter-spacing="0.5">ALGORITHM THINKER</text>
    <line x1="28" y1="140" x2="{LEFT_W - 28}" y2="140" stroke="white" stroke-opacity="0.12"/>
    <line x1="28" y1="262" x2="{LEFT_W - 28}" y2="262" stroke="white" stroke-opacity="0.12"/>
    {''.join(stat_svg)}
    {''.join(chip_svg)}
    <line x1="28" y1="{panel_h - 104}" x2="{LEFT_W - 28}" y2="{panel_h - 104}" stroke="white" stroke-opacity="0.12"/>
    <text x="28" y="{panel_h - 62}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" \
fill="{MUTED}">One problem at a time, every day.</text>
    <text x="28" y="{panel_h - 34}" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" \
fill="{GOLD}" letter-spacing="0.5">&#8212; EDDY</text>
  </g>"""

    # ---- right numbered rows ------------------------------------------------
    def pct(n: int) -> float:
        return (n / total * 100) if total else 0

    items = [
        ("check", "EASY WARM-UPS", f"{easy} solved, {pct(easy):.0f}% of the total", pct(easy)),
        ("bars", "MEDIUM CLIMBS", f"{medium} solved, {pct(medium):.0f}% of the total", pct(medium)),
        ("bolt", "HARD BOSSES", f"{hard} solved, {pct(hard):.0f}% of the total", pct(hard)),
        (
            "trophy",
            "CONTEST MODE",
            f"{_fmt(stats.get('contests_attended') or 0)} contests entered, rating {_fmt(stats.get('rating'), 'unrated')}",
            None,
        ),
    ]
    row_svg = []
    for i, (glyph, title, desc, bar_pct) in enumerate(items):
        ry = TOP + i * (ROW_H + ROW_GAP)
        bar = ""
        if bar_pct is not None:
            bw = RW - 86 - 24
            bar = (
                f'<rect x="86" y="74" width="{bw}" height="4" rx="2" fill="white" fill-opacity="0.1"/>'
                f'<rect x="86" y="74" width="{max(bw * bar_pct / 100, 4):.1f}" height="4" rx="2" fill="{PINK}"/>'
            )
        row_svg.append(f"""
  <g transform="translate({RX},{ry})">
    <polygon points="{_chamfer(RW, ROW_H, 10)}" fill="#{bg}" fill-opacity="{panel_opacity}" stroke="white" \
stroke-opacity="0.14"/>
    <rect x="20" y="{ROW_H / 2 - 28}" width="56" height="56" rx="10" fill="white" fill-opacity="0.05" \
stroke="white" stroke-opacity="0.12"/>
    {_corner_marks(20, ROW_H / 2 - 28, 56, 56, GOLD)}
    {_glyph(glyph, 38, ROW_H / 2 - 10, GOLD, 20, 1.6)}
    <text x="92" y="32" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" \
fill="white" letter-spacing="0.5">{title}</text>
    <text x="92" y="54" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" \
fill="{MUTED}">{_esc(desc)}</text>
    <text x="{RW - 18}" y="28" font-family="Consolas, Menlo, monospace" font-size="10" fill="{DIM}" \
text-anchor="end">{i + 1:02d}</text>
  </g>""")
        if bar:
            row_svg.append(f'<g transform="translate({RX},{ry})"><g transform="translate(6,0)">{bar}</g></g>')

    strip_y = TOP + rows_h + ROW_GAP
    bar_y = strip_y + STRIP_H + ROW_GAP
    bottom = f"""
  <g transform="translate({RX},{strip_y})">
    <rect width="{RW}" height="{STRIP_H}" rx="4" fill="#{bg}" fill-opacity="{panel_opacity}"/>
    <rect width="{RW}" height="{STRIP_H}" rx="4" fill="url(#hatch)" stroke="white" stroke-opacity="0.08"/>
  </g>
  <g transform="translate({RX},{bar_y})">
    <rect x="0.5" y="0.5" width="{RW - 1}" height="{BAR_H - 1}" fill="#{bg}" fill-opacity="{panel_opacity}" \
stroke="white" stroke-opacity="0.14"/>
    <rect x="{RW / 2 - 92}" y="{BAR_H / 2 - 2}" width="4" height="4" fill="{GOLD}"/>
    <text x="{RW / 2 - 80}" y="{BAR_H / 2 + 4}" font-family="Arial, Helvetica, sans-serif" font-size="12" \
fill="white" letter-spacing="0.8">UPDATED ON EVERY BUILD</text>
  </g>"""

    return f"""<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LeetCode stats">
  <defs>
    {glow_filter()}
    <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="white" stroke-opacity="0.12" stroke-width="1.5"/>
    </pattern>
  </defs>
  <text x="0" y="18" font-family="Consolas, Menlo, monospace" font-size="12" font-weight="700" \
fill="{GOLD}" letter-spacing="3" filter="url(#hudglow)">[ LEETCODE ]</text>
  <text x="0" y="64" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="800" \
fill="{ink}" letter-spacing="0.5">SHARP LOGIC</text>
  <text x="0" y="106" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="800" \
fill="{GOLD}" letter-spacing="0.5">CLEAN CODE</text>
  <text x="{WIDTH}" y="74" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" \
fill="{muted_ink}" text-anchor="end">I solve algorithm problems to keep my thinking</text>
  <text x="{WIDTH}" y="94" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" \
fill="{muted_ink}" text-anchor="end">fast, structured, and ready for real systems.</text>
  {left}
  {''.join(row_svg)}
  {bottom}
</svg>"""
