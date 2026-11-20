"""
neural_activity.py

"Neural Activity" - the LAST section in the final layout. A big number
top-left (total contributions), a "LIVE" status chip, streak badges,
and a neon cyberpunk city skyline built from the same weekly data:
each week becomes one building, height + lit-window count scaled to
that week's activity, varied rooflines (spire/dome/angled-cut/flat) for
visual variety, gradient-lit facades, a water reflection beneath the
street line, plus a couple of planes crossing the sky and cars driving
the street.

Windows are deliberately GREEN (not the reference photo's warm yellow)
- they represent real commit activity, so they stay tied to the same
green used for "activity" everywhere else on the page rather than
matching a reference image's color choice.

Usage:
    from neural_activity import render_neural_activity_svg
    svg_markup = render_neural_activity_svg(weeks, total, current_streak, longest_streak, active_days, theme_name)

`weeks` is a list of 52-ish columns, each a list of 7 ints (0-4
intensity levels, Sun-Sat), oldest column first - same shape GitHub's
own contribution graph uses. Each column's 7 levels are summed (0-28)
to get that week's "activity score", which drives building height,
lit-window count, and roof style.
"""

from __future__ import annotations

import hashlib
import html

from hud_grid import glass_frame_rect, glow_filter, scanline_overlay
from themes import DEFAULT_THEME, HUD_COLORS, get_theme

PANEL_PAD_X = 24
PANEL_PAD_TOP = 138  # room for the number/chip row + the centered streak badge row
CITY_HEIGHT = 150
REFLECTION_HEIGHT = 60
PANEL_PAD_BOTTOM = 20

NEON_GROUPS = ["cyan", "pink", "green"]
NEON_HEX = {"cyan": "#00E7FF", "pink": "#FF2279", "green": "#24FF9A"}
NEON_DARK = {"cyan": "#0a2230", "pink": "#2a0a1c", "green": "#0a2418"}

# Windows are always green (commit activity), regardless of a
# building's own neon accent color.
WINDOW_LIT = "#3CFFB0"
WINDOW_LIT_DIM = "#1FAE78"
WINDOW_DARK = "#0d1a16"

SKY_TOP = "#0d0508"
SKY_MID = "#20101f"
SKY_HORIZON = "#3d1830"
HORIZON_GLOW = "#ff7a3d"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a: str, b: str, t: float) -> str:
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))


NEON = {
    "gold": "#FFC84D", "orange": "#FF8A3D", "green": "#24FF9A",
    "cyan": "#26E6FF", "purple": "#B565FF", "blue": "#4C8DFF",
}
_N = 8            # lots per side
_A = 44           # half tile width (px)
_CX, _CY0 = 410, 118
_FW = 0.64        # building footprint (fraction of a lot)


def _P(x: float, y: float, z: float = 0.0):
    return _CX + (x - y) * _A, _CY0 + (x + y) * _A / 2 - z


def _pts(*p) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in p)


def render_neural_activity_svg(
    weeks: list[list[int]],
    total_contributions: int,
    current_streak: int,
    longest_streak: int,
    active_days: int,
    theme_name: str = DEFAULT_THEME,
    for_light_mode: bool = False,
    end_date=None,
    week_dates: list | None = None,
) -> str:
    """
    Isometric neon commit city. 52 weeks = 52 buildings on an 8x8 board.
    The busiest weeks sit in the middle and rise highest; height AND the
    share of lit windows, glow and neon colour all scale with that week's
    commits. The top weeks get light beams and linking data lines.
    Every building carries data-* attributes for the interactive page.
    """
    import datetime as _dt
    import random

    W, H = 820, 500
    end = end_date or _dt.date.today()
    cols = [list(w[:7]) + [0] * (7 - len(w[:7])) for w in weeks][-52:]
    slot_dates = [[""] * 7 for _ in range(52)]
    if week_dates and len(week_dates) >= 52 and len(weeks) == len(week_dates):
        # Put every real day under its true weekday (Sunday first), so a partial first
        # or last week leaves the missing days empty instead of shifting the others.
        cols = []
        for w_counts, w_dates in zip(weeks[-52:], week_dates[-52:]):
            row, drow = [0] * 7, [""] * 7
            for c, dstr in zip(w_counts, w_dates):
                idx = (_dt.date.fromisoformat(dstr).weekday() + 1) % 7
                row[idx], drow[idx] = c, dstr
            cols.append(row)
            slot_dates[len(cols) - 1] = drow
    cols = [[0] * 7] * (52 - len(cols)) + cols
    tot = [sum(c) for c in cols]
    peak = max(tot) or 1
    low = min(tot)
    order = sorted(range(52), key=lambda k: -tot[k])  # rank -> week index
    rank_of = {k: r for r, k in enumerate(order)}

    # Date order: columns run oldest -> newest along the board's right-hand axis, so the
    # latest week sits in the right-most column; the 12 unused lots at the start are parks.
    lots = [(i, j) for i in range(_N) for j in range(_N)]
    park_lots = lots[:12]
    placed_wk = {wk: lots[12 + wk] for wk in range(52)}

    # Real calendar weeks: GitHub weeks run Sunday to Saturday, and the newest one ends today.
    real = [[_dt.date.fromisoformat(d) for d in w] for w in week_dates][-52:] if week_dates else None
    sunday_now = end - _dt.timedelta(days=(end.weekday() + 1) % 7)

    def _week_span(wk):
        if real and len(real) == 52 and real[wk]:
            return min(real[wk]), max(real[wk])
        start = sunday_now - _dt.timedelta(days=7 * (51 - wk))
        return start, min(start + _dt.timedelta(days=6), end)

    rng = random.Random(5)
    hues_used: set[str] = set()

    # ---------- background: circuit traces + code ----------
    circuit = []
    dirs = {0: (1, -0.5), 1: (-1, -0.5), 2: (1, 0.5), 3: (-1, 0.5)}
    for _ in range(46):
        side = rng.randrange(4)
        u = rng.uniform(0, _N)
        ex, ey = {0: _P(u, 0), 1: _P(0, u), 2: _P(_N, u), 3: _P(u, _N)}[side]
        dx, dy = dirs[side]
        l1 = rng.uniform(14, 70)
        mx, my = ex + dx * l1, ey + dy * l1
        # turn onto the perpendicular iso axis
        pdx, pdy = (dy * 2, dx * 2) if rng.random() < 0.5 else (-dy * 2, -dx * 2)
        pdx, pdy = (1 if pdx > 0 else -1), (0.5 if pdy > 0 else -0.5)
        l2 = rng.uniform(10, 50)
        nx, ny = mx + pdx * l2, my + pdy * l2
        col = rng.choice(["#1c6b80", "#1c6b80", "#7a5a1c"])
        circuit.append(f'<polyline points="{ex:.0f},{ey:.0f} {mx:.0f},{my:.0f} {nx:.0f},{ny:.0f}" fill="none" stroke="{col}" stroke-opacity="0.55"/>')
        circuit.append(f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="2" fill="{rng.choice([NEON["gold"], NEON["cyan"]])}" opacity="0.6"/>')
    snippets = ["const commit = await git.push(branch)", "if (build.ok) deploy(main)", "for (const w of weeks) render(w)",
                "git merge --no-ff feature/ui", "export const ship = () => run()", "await repo.fetch({ depth: 1 })",
                "tests.pass() && release.tag()", "city.grow(commits.count)"]
    code = "".join(
        f'<text x="{x}" y="{y + k * 12}" font-family="Consolas, Menlo, monospace" font-size="8" fill="#7fb7d6" opacity="0.16">{_esc(snippets[(k + off) % len(snippets)])}</text>'
        for x, y, off in ((612, 34, 0), (22, 392, 3)) for k in range(7)
    )

    # ---------- platform ----------
    T = 14
    p0, p1, p2, p3 = _P(0, 0), _P(_N, 0), _P(_N, _N), _P(0, _N)
    gold = NEON["gold"]
    platform = (
        f'<polygon points="{_pts(p3, p2, (p2[0], p2[1] + T), (p3[0], p3[1] + T))}" fill="#070b18"/>'
        f'<polygon points="{_pts(p2, p1, (p1[0], p1[1] + T), (p2[0], p2[1] + T))}" fill="#04060e"/>'
        f'<polygon points="{_pts(p0, p1, p2, p3)}" fill="#0a1226" stroke="{gold}" stroke-width="1.6" filter="url(#glow)"/>'
        f'<polyline points="{_pts((p3[0], p3[1] + T), (p2[0], p2[1] + T), (p1[0], p1[1] + T))}" fill="none" stroke="{gold}" stroke-opacity="0.7"/>'
    )
    roads = []
    for k in range(_N + 1):
        a, b = _P(k, 0), _P(k, _N)
        c, d = _P(0, k), _P(_N, k)
        roads.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#26E6FF" stroke-opacity="0.12"/>')
        roads.append(f'<line x1="{c[0]:.1f}" y1="{c[1]:.1f}" x2="{d[0]:.1f}" y2="{d[1]:.1f}" stroke="#26E6FF" stroke-opacity="0.12"/>')
    for i, j in park_lots:
        a = _P(i + 0.12, j + 0.12); b = _P(i + 0.88, j + 0.12); c = _P(i + 0.88, j + 0.88); d = _P(i + 0.12, j + 0.88)
        roads.append(f'<polygon points="{_pts(a, b, c, d)}" fill="#0d2230" stroke="#26E6FF" stroke-opacity="0.35"/>')
        for tx, ty in ((0.35, 0.4), (0.65, 0.62)):
            sx, sy = _P(i + tx, j + ty)
            roads.append(f'<ellipse cx="{sx:.1f}" cy="{sy - 5:.1f}" rx="4.5" ry="5.5" fill="#24FF9A" fill-opacity="0.28" stroke="#24FF9A" stroke-opacity="0.8"/>'
                         f'<rect x="{sx - 0.6:.1f}" y="{sy - 1:.1f}" width="1.2" height="3" fill="#24FF9A" opacity="0.6"/>')

    # ---------- buildings ----------
    items = []  # (depth, svg)
    tops = {}

    def box(i0, j0, i1, j1, z0, z1, hue, ratio, r, wins=True):
        body = _mix("#0b1220", hue, 0.10 + 0.10 * ratio)
        left = _mix(body, "#ffffff", 0.07)
        right = _mix(body, "#000000", 0.35)
        topc = _mix(body, hue, 0.22)
        g = [
            f'<polygon points="{_pts(_P(i0, j1, z0), _P(i1, j1, z0), _P(i1, j1, z1), _P(i0, j1, z1))}" fill="{left}"/>',
            f'<polygon points="{_pts(_P(i1, j1, z0), _P(i1, j0, z0), _P(i1, j0, z1), _P(i1, j1, z1))}" fill="{right}"/>',
            f'<polygon points="{_pts(_P(i0, j0, z1), _P(i1, j0, z1), _P(i1, j1, z1), _P(i0, j1, z1))}" fill="{topc}"/>',
        ]
        h = z1 - z0
        lit_p = 0.10 + 0.85 * ratio
        faces = (
            (_P(i0, j1, z1), 0.5, (i1 - i0) * _A, left),
            (_P(i1, j1, z1), -0.5, (j1 - j0) * _A, right),
        )
        if wins:
            for fidx, ((ox, oy), slope, fw, facecol) in enumerate(faces):
                unlit = _mix(facecol, "#02040a", 0.55)
                buckets: dict[str, str] = {}
                flick = ""
                ncol = max(1, int((fw - 3) // 7))
                v = 5.0
                while v + 5 <= h - 3:
                    for k in range(ncol):
                        if r.random() < lit_p:
                            roll = r.random()
                            col = (NEON["orange"] if ratio < 0.25 else hue) if roll < 0.7 else (_mix(hue, "#ffffff", 0.55) if roll < 0.85 else NEON["orange"])
                            d = f"M{3 + k * 7} {v:.0f}h4v4.5h-4z"
                            if len(flick) < 40 and r.random() < 0.05:
                                flick += d
                            else:
                                buckets[col] = buckets.get(col, "") + d
                        else:
                            buckets[unlit] = buckets.get(unlit, "") + f"M{3 + k * 7} {v:.0f}h4v4.5h-4z"
                    v += 7
                inner = "".join(f'<path d="{d}" fill="{c}"' + ("" if c == unlit else ' opacity="0.95"') + "/>" for c, d in buckets.items())
                if flick:
                    inner += (f'<path d="{flick}" fill="{hue}"><animate attributeName="opacity" values="1;0.12;1" '
                              f'dur="{r.uniform(1.6, 4):.1f}s" begin="-{r.uniform(0, 3):.1f}s" repeatCount="indefinite"/></path>')
                g.append(f'<g transform="matrix(1,{slope},0,1,{ox:.1f},{oy:.1f})">{inner}</g>')
        g.insert(3, f'<polygon points="{_pts(_P(i0, j1, z0), _P(i1, j1, z0), _P(i1, j1, z1), _P(i0, j1, z1))}" fill="url(#fl_{hue[1:]})"/>')
        g.insert(4, f'<polygon points="{_pts(_P(i1, j1, z0), _P(i1, j0, z0), _P(i1, j0, z1), _P(i1, j1, z1))}" fill="url(#fl_{hue[1:]})" opacity="0.6"/>')
        edge_op = 0.25 + 0.75 * ratio
        fx, fy = _P(i1, j1, z0), _P(i1, j1, z1)
        g.append(
            f'<polyline points="{_pts(_P(i0, j1, z1), _P(i1, j1, z1), _P(i1, j0, z1))}" fill="none" stroke="{hue}" stroke-opacity="{edge_op:.2f}" stroke-width="1.2"{' filter="url(#glow)"' if ratio > 0.45 else ''}/>'
            f'<line x1="{fx[0]:.1f}" y1="{fx[1]:.1f}" x2="{fy[0]:.1f}" y2="{fy[1]:.1f}" stroke="{hue}" stroke-opacity="{edge_op:.2f}" stroke-width="1.2"/>'
        )
        return "".join(g)

    m = (1 - _FW) / 2
    for rank in range(52):
        wk = order[rank]
        c = tot[wk]
        ratio = ((c - low) / (peak - low)) ** 1.4 if peak > low else 0.0
        i, j = placed_wk[wk]
        r = random.Random(rank * 131 + 7)
        if rank == 0:
            hue = NEON["gold"]
        elif rank == 1:
            hue = NEON["orange"]
        elif rank == 2:
            hue = NEON["green"]
        elif ratio > 0.45:
            hue = r.choice([NEON["cyan"], NEON["purple"], NEON["blue"], NEON["green"]])
        elif ratio > 0.15:
            hue = r.choice([NEON["blue"], NEON["cyan"], NEON["purple"]])
        else:
            hue = NEON["blue"]
        hues_used.add(hue)
        h = 12 + ratio * 140
        if rank < 3:
            h = min(185, h * 1.18)
        h = min(h, _P(i + 0.5, j + 0.5)[1] - 24)
        i0, i1, j0, j1 = i + m, i + 1 - m, j + m, j + 1 - m
        parts = []
        gx, gy = _P(i + 0.5, j + 0.5)
        parts.append(f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="40" ry="20" fill="url(#g_{hue[1:]})" opacity="{0.12 + 0.7 * ratio:.2f}"/>')
        if h > 70:  # setback tiers like the reference towers
            hb = h * 0.62
            parts.append(box(i0, j0, i1, j1, 0, hb, hue, ratio, r))
            sh = 0.13
            if rank < 3:
                hm = h * 0.84
                parts.append(box(i0 + sh, j0 + sh, i1 - sh, j1 - sh, hb, hm, hue, ratio, r))
                parts.append(box(i0 + 2 * sh, j0 + 2 * sh, i1 - 2 * sh, j1 - 2 * sh, hm, h, hue, ratio, r))
            else:
                parts.append(box(i0 + sh, j0 + sh, i1 - sh, j1 - sh, hb, h, hue, ratio, r))
        else:
            parts.append(box(i0, j0, i1, j1, 0, h, hue, ratio, r))
        tx, ty = _P((i0 + i1) / 2, (j0 + j1) / 2, h)
        tops[rank] = (tx, ty, hue)
        if ratio > 0.5 and rank >= 3:  # satellite dish
            parts.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx:.1f}" y2="{ty - 5:.1f}" stroke="{hue}" stroke-width="1"/>'
                         f'<ellipse cx="{tx:.1f}" cy="{ty - 7:.1f}" rx="4" ry="2.4" fill="none" stroke="#cfe6ff" stroke-width="1"/>')
        if rank < 3:
            parts.append(f'<circle cx="{tx:.1f}" cy="{ty - 4:.1f}" r="9" fill="url(#g_{hue[1:]})"/><circle cx="{tx:.1f}" cy="{ty - 4:.1f}" r="3.2" fill="#fff" fill-opacity="0.9"/>')
        if rank < 6:
            parts.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx:.1f}" y2="{ty - 12:.1f}" stroke="#9aa4b8"/>'
                         f'<circle cx="{tx:.1f}" cy="{ty - 12:.1f}" r="1.8" fill="#ff3b3b"><animate attributeName="opacity" values="1;0.1;1" dur="1.5s" begin="-{rank * 0.3:.1f}s" repeatCount="indefinite"/></circle>')
        ws, we = _week_span(wk)
        label = f"{ws.strftime('%b')} {ws.day} to {we.strftime('%b')} {we.day}"
        items.append((i + j, f'<g class="bld" tabindex="0" data-week="{label}" data-c="{c}" data-rank="{rank + 1}" '
                             f'data-days="{",".join(str(x) for x in cols[wk])}" data-dates="{",".join(slot_dates[wk])}" data-hue="{hue}">{"".join(parts)}</g>'))
    items.sort(key=lambda t: t[0])
    bld = "".join(s for _, s in items)

    # beams + data lines over the three busiest towers
    fx = []
    for rank in range(5):
        tx, ty, hue = tops[rank]
        w = 7 if rank < 3 else 4
        op = (0.55, 0.45, 0.45, 0.3, 0.3)[rank]
        fx.append(f'<rect x="{tx - w / 2:.1f}" y="0" width="{w}" height="{ty:.1f}" fill="url(#bm_{hue[1:]})" opacity="{op}">'
                  f'<animate attributeName="opacity" values="{op};{min(1, op + 0.4):.2f};{op}" dur="{3 + rank * 0.7:.1f}s" repeatCount="indefinite"/></rect>')
        fx.append(f'<line x1="{tx:.1f}" y1="0" x2="{tx:.1f}" y2="{ty:.1f}" stroke="{hue}" stroke-opacity="0.8" stroke-width="1"/>')
        hues_used.add(hue)
    links = [(0, 2, "feat:"), (1, 3, "merge"), (2, 4, "fix:")]
    crowns = sorted(range(3), key=lambda r: tops[r][0])  # left to right
    for pos, rank in enumerate(crowns):
        tx, ty, hue = tops[rank]
        wk = order[rank]
        ws, we = _week_span(wk)
        lab1 = f"#{rank + 1}  {tot[wk]} COMMITS"
        lab2 = f"{ws.strftime('%b')} {ws.day} to {we.strftime('%b')} {we.day}"
        bw, bh = 104, 30
        bx0 = min(max(8, tx - bw / 2), W - bw - 8)
        by0 = (92, 128, 92)[pos]
        fx.append(
            f'<line x1="{tx:.1f}" y1="{ty - 6:.1f}" x2="{min(max(tx, bx0 + 6), bx0 + bw - 6):.1f}" y2="{by0 + bh:.1f}" stroke="{hue}" stroke-opacity="0.8"/>'
            f'<rect x="{bx0:.1f}" y="{by0:.1f}" width="{bw}" height="{bh}" rx="5" fill="#070b16" fill-opacity="0.92" stroke="{hue}"/>'
            f'<text x="{bx0 + 8:.1f}" y="{by0 + 13:.1f}" font-family="Consolas, Menlo, monospace" font-size="10" font-weight="700" fill="{hue}">{lab1}</text>'
            f'<text x="{bx0 + 8:.1f}" y="{by0 + 25:.1f}" font-family="Consolas, Menlo, monospace" font-size="8.5" fill="#9aa4b8">{lab2}</text>'
        )
    for a, b, lab in links:
        ax, ay, ha = tops[a]
        bx, by, hb = tops[b]
        if abs(ax - bx) > 150:
            continue
        cx, cy = (ax + bx) / 2, min(ay, by) - 24 - abs(ax - bx) * 0.25
        fx.append(f'<path d="M{ax:.1f} {ay:.1f} Q{cx:.1f} {cy:.1f} {bx:.1f} {by:.1f}" fill="none" stroke="{ha}" stroke-width="1.2" stroke-opacity="0.75" stroke-dasharray="4 5">'
                  f'<animate attributeName="stroke-dashoffset" from="0" to="-18" dur="1.4s" repeatCount="indefinite"/></path>')

    for a, b in ((0, 1), (1, 2)):
        ax, ay, _ = tops[a]
        bx, by, _ = tops[b]
        if abs(ax - bx) > 150:
            continue
        for k, wc in enumerate(["#ff4d5a", "#26E6FF", "#24FF9A", "#FFC84D", "#B565FF"]):
            y1, y2 = ay + 34 + k * 3, by + 34 + k * 3
            fx.append(f'<path d="M{ax:.1f} {y1:.1f} C{ax:.1f} {y1 + 12:.1f} {bx:.1f} {y2 + 12:.1f} {bx:.1f} {y2:.1f}" fill="none" stroke="{wc}" stroke-width="1.4" stroke-opacity="0.8"/>')
    dust = "".join(
        f'<circle cx="{rng.uniform(10, W - 10):.0f}" cy="{rng.uniform(10, H - 10):.0f}" r="{rng.choice([0.7, 1, 1.4])}" fill="{rng.choice([NEON["gold"], NEON["cyan"], "#ffffff"])}" opacity="{rng.uniform(0.15, 0.5):.2f}"/>'
        for _ in range(110)
    )
    defs = "".join(
        f'<linearGradient id="fl_{h[1:]}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{h}" stop-opacity="0.34"/><stop offset="0.7" stop-color="{h}" stop-opacity="0.04"/><stop offset="1" stop-color="{h}" stop-opacity="0"/></linearGradient>'
        for h in sorted(hues_used)
    ) + "".join(
        f'<radialGradient id="g_{h[1:]}"><stop offset="0" stop-color="{h}" stop-opacity="0.9"/><stop offset="1" stop-color="{h}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="bm_{h[1:]}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{h}" stop-opacity="0"/><stop offset="1" stop-color="{h}" stop-opacity="0.85"/></linearGradient>'
        for h in sorted(hues_used)
    )

    gold_t = NEON["gold"]
    stats = [("TOTAL", total_contributions), ("STREAK", current_streak), ("LONGEST", longest_streak), ("ACTIVE DAYS", active_days)]
    stat_svg = "".join(
        f'<text x="{32 + k * 100}" y="58" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="800" fill="{gold_t}">{v}</text>'
        f'<text x="{32 + k * 100}" y="76" font-family="Consolas, Menlo, monospace" font-size="10" fill="#c9d4e6" letter-spacing="1.2">{_esc(l)}</text>'
        for k, (l, v) in enumerate(stats)
    )
    CUT = 14
    pts = f"0,{CUT} {CUT},0 {W - 0.5},0 {W - 0.5},{H - CUT} {W - CUT},{H} 0,{H}"
    n = 10
    brk = (f'<path d="M8 {8 + n} V8 H{8 + n} M{W - 8 - n} 8 H{W - 8} V{8 + n} M{W - 8} {H - 8 - n} V{H - 8} H{W - 8 - n} '
           f'M{8 + n} {H - 8} H8 V{H - 8 - n}" fill="none" stroke="{gold_t}" stroke-width="1.4"/>')
    return f"""<svg id="city" width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Contribution city">
  <defs>
    <clipPath id="pclip"><polygon points="{pts}"/></clipPath>
    <radialGradient id="bgrad" cx="50%" cy="62%" r="70%"><stop offset="0" stop-color="#0c1630"/><stop offset="1" stop-color="#03050b"/></radialGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <radialGradient id="floor"><stop offset="0.55" stop-color="#FFC84D" stop-opacity="0.10"/><stop offset="1" stop-color="#FFC84D" stop-opacity="0"/></radialGradient>
    {defs}
  </defs>
  <g clip-path="url(#pclip)">
    <rect width="{W}" height="{H}" fill="url(#bgrad)"/>
    {dust}
    {''.join(circuit)}
    {code}
    <ellipse cx="410" cy="{_CY0 + 4.5 * _A + 6}" rx="390" ry="150" fill="url(#floor)"/>
    {platform}
    {''.join(roads)}
    {bld}
    <g pointer-events="none">{''.join(fx)}</g>
    {stat_svg}
    <g pointer-events="none"><text x="{W - 24}" y="{H - 30}" text-anchor="end" font-family="Consolas, Menlo, monospace" font-size="11" fill="#c9d4e6" letter-spacing="1.5">1 BLOCK = 1 WEEK  ·  NEWEST ON THE RIGHT</text>
    <text x="{W - 24}" y="{H - 16}" text-anchor="end" font-family="Consolas, Menlo, monospace" font-size="9" fill="#6b7a8c" letter-spacing="1.2">TALLER + BRIGHTER = MORE COMMITS</text></g>
  </g>
  <polygon points="{pts}" fill="none" stroke="white" stroke-opacity="0.14"/>
  {brk}
</svg>"""


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Commit City</title>
<style>
:root{--bg:#f3f5f9;--ink:#10131a;--muted:#5b6475;--card:#ffffff;--line:#d9dee8;--gold:#b7860b}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#05070d;--ink:#eef2fa;--muted:#8a94a8;--card:#0b0f18;--line:#1f2736;--gold:#FFC84D}}
:root[data-theme="dark"]{--bg:#05070d;--ink:#eef2fa;--muted:#8a94a8;--card:#0b0f18;--line:#1f2736;--gold:#FFC84D}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Segoe UI",system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 48px}
.tag{font:700 12px Consolas,Menlo,monospace;letter-spacing:.25em;color:var(--gold)}
h1{font:800 34px/1.1 Arial,Helvetica,sans-serif;margin:8px 0 6px;letter-spacing:.5px}
p.lead{margin:0 0 18px;color:var(--muted);max-width:60ch}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.bar button{font:600 12px Consolas,Menlo,monospace;letter-spacing:.08em;background:var(--card);color:var(--ink);border:1px solid var(--line);padding:8px 12px;border-radius:8px;cursor:pointer}
.bar button[aria-pressed="true"]{border-color:var(--gold);color:var(--gold)}
.stage{position:relative;background:#03050b;border:1px solid var(--line);border-radius:12px;overflow:hidden}
.stage svg{display:block;width:100%;height:auto}
.bld{cursor:pointer;transition:filter .15s,opacity .2s;outline:none}
.bld:hover,.bld:focus,.bld.pin{filter:brightness(1.7) drop-shadow(0 0 7px var(--h,#FFC84D))}
.dim .bld:not(.on){opacity:.18}
#tip{position:absolute;pointer-events:none;min-width:200px;background:rgba(8,12,22,.96);color:#eef2fa;border:1px solid #FFC84D;border-radius:10px;padding:12px 14px;font-size:13px;opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s;z-index:5}
#tip.show{opacity:1;transform:none}
#tip .w{font:700 11px Consolas,Menlo,monospace;letter-spacing:.14em;color:#FFC84D}
#tip .n{font:800 30px/1.1 Arial,sans-serif;margin:4px 0 2px}
#tip .r{color:#9aa4b8;font-size:12px;margin-bottom:8px}
#tip .d{display:flex;gap:4px;align-items:flex-end;height:36px}
#tip .d i{flex:1;background:var(--h,#FFC84D);border-radius:2px 2px 0 0;min-height:2px;opacity:.9}
#tip .l{display:flex;gap:4px;font:9px Consolas,monospace;color:#6b7a8c;margin-top:3px}
#tip .l span{flex:1;text-align:center}
small{display:block;margin-top:12px;color:var(--muted)}
</style></head><body><main>
<div class="tag">[ NEURAL ACTIVITY ]</div>
<h1>Commit City</h1>
<p class="lead">Every building is one week of commits. Taller and brighter means more commits, and the busiest weeks sit in the middle. Hover, tap or tab to a building to see its week.</p>
<div class="bar" role="group" aria-label="View">
 <button data-f="all" aria-pressed="true">ALL WEEKS</button>
 <button data-f="top" aria-pressed="false">TOP 10</button>
 <button data-f="quiet" aria-pressed="false">QUIET WEEKS</button>
 <button id="pulse" aria-pressed="true">ANIMATION ON</button>
</div>
<div class="stage" id="stage">__SVG__<div id="tip" role="status"></div></div>
<small>Built from the last 52 weeks of GitHub activity. Re-generated on every profile build.</small>
</main>
<script>
(function(){
var st=document.getElementById('stage'),svg=st.querySelector('svg'),tip=document.getElementById('tip'),pin=null;
var B=[].slice.call(svg.querySelectorAll('.bld'));
var DAYS=['S','M','T','W','T','F','S'];
function fill(b){
  var d=b.dataset.days.split(',').map(Number),ds=(b.dataset.dates||'').split(','),m=Math.max.apply(null,d)||1,hasD=ds.some(Boolean);
  var MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],WD=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  tip.style.setProperty('--h',b.dataset.hue);
  function nm(i){var s=ds[i];if(!s)return '';var t=s.split('-');return WD[i]+' '+MO[+t[1]-1]+' '+(+t[2])}
  tip.innerHTML='<div class="w">'+b.dataset.week.toUpperCase()+'</div><div class="n">'+b.dataset.c+' commits</div><div class="r">Rank #'+b.dataset.rank+' of 52</div><div class="d">'+d.map(function(v,i){return hasD&&!ds[i]?'<i style="height:2px;opacity:.25" title="no data"></i>':'<i style="height:'+Math.max(6,v/m*100)+'%" title="'+(nm(i)?nm(i)+': ':'')+v+'"></i>'}).join('')+'</div><div class="l">'+DAYS.map(function(x){return '<span>'+x+'</span>'}).join('')+'</div>';
}
function place(e,b){
  var r=st.getBoundingClientRect(),x,y;
  if(e&&e.clientX!=null){x=e.clientX-r.left;y=e.clientY-r.top}else{var q=b.getBoundingClientRect();x=q.left-r.left+q.width/2;y=q.top-r.top}
  var w=tip.offsetWidth,h=tip.offsetHeight;
  x=Math.min(Math.max(8,x+16),r.width-w-8);y=Math.min(Math.max(8,y-h-12),r.height-h-8);
  tip.style.left=x+'px';tip.style.top=y+'px';
}
function show(e,b){fill(b);place(e,b);tip.classList.add('show')}
function hide(){if(!pin)tip.classList.remove('show')}
B.forEach(function(b){
  b.style.setProperty('--h',b.dataset.hue);
  b.addEventListener('mouseenter',function(e){show(e,b)});
  b.addEventListener('mousemove',function(e){if(!pin)place(e,b)});
  b.addEventListener('mouseleave',hide);
  b.addEventListener('focus',function(){show(null,b)});
  b.addEventListener('blur',hide);
  b.addEventListener('click',function(e){e.stopPropagation();if(pin)pin.classList.remove('pin');if(pin===b){pin=null;hide();return}pin=b;b.classList.add('pin');show(e,b)});
});
document.addEventListener('click',function(){if(pin){pin.classList.remove('pin');pin=null;tip.classList.remove('show')}});
var bar=document.querySelector('.bar');
bar.addEventListener('click',function(e){
  var t=e.target.closest('button');if(!t)return;
  if(t.id==='pulse'){var on=t.getAttribute('aria-pressed')==='true';on?svg.pauseAnimations():svg.unpauseAnimations();t.setAttribute('aria-pressed',String(!on));t.textContent=on?'ANIMATION OFF':'ANIMATION ON';return}
  [].forEach.call(bar.querySelectorAll('[data-f]'),function(x){x.setAttribute('aria-pressed',String(x===t))});
  var f=t.dataset.f;st.classList.toggle('dim',f!=='all');
  var cs=B.map(function(b){return +b.dataset.c}).sort(function(a,b){return a-b}),q=cs[Math.floor(cs.length*0.25)];
  B.forEach(function(b){var rk=+b.dataset.rank,c=+b.dataset.c;b.classList.toggle('on',f==='top'?rk<=10:f==='quiet'?c<=q:true)});
});
})();
</script></body></html>"""


def render_interactive_html(svg: str, sample: bool = False) -> str:
    """Self-contained page that wraps the city SVG with hover/tap tooltips and view filters."""
    note = ("<small><b>Sample data.</b> The build could not read your GitHub contributions (no token or the call failed), "
            "so this city shows placeholder weeks.</small>") if sample else ""
    return _PAGE.replace("__SVG__", svg).replace("<small>Built from", note + "<small>Built from", 1)


GOLD = HUD_COLORS["modules"]
GREEN = "#24FF9A"


def render_activity_heading_svg(for_light_mode: bool = False) -> str:
    """Hero-style heading above the city: corner-marked tag, two-tone title, no paragraph."""
    ink = "#10131a" if for_light_mode else "#ffffff"
    tw, th, n = 170, 28, 6
    marks = (
        f'<path d="M0 {n} V0 H{n} M{tw - n} 0 H{tw} V{n} M{tw} {th - n} V{th} H{tw - n} M{n} {th} H0 V{th - n}" '
        f'fill="none" stroke="{GOLD}" stroke-width="1.4"/>'
    )
    return f"""<svg width="820" height="100" viewBox="0 0 820 100" xmlns="http://www.w3.org/2000/svg" \
role="img" aria-label="Neural activity">
  <defs>{glow_filter()}</defs>
  {marks}
  <text x="{tw / 2}" y="19" font-family="Consolas, Menlo, monospace" font-size="12" fill="{GOLD}" \
text-anchor="middle" letter-spacing="2" filter="url(#hudglow)">NEURAL ACTIVITY</text>
  <text x="0" y="84" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="800" letter-spacing="0.5">\
<tspan fill="{ink}">COMMIT </tspan><tspan fill="{GOLD}">CITY</tspan></text>
</svg>"""


def render_activity_status_svg(for_light_mode: bool = False) -> str:
    """Hero-style footer line under the city."""
    ink = "#10131a" if for_light_mode else "#ffffff"
    muted = "#4b5563" if for_light_mode else "#6b7a8c"
    return f"""<svg width="820" height="44" viewBox="0 0 820 44" xmlns="http://www.w3.org/2000/svg" \
role="img" aria-label="Status">
  <defs>
    <linearGradient id="rule2" x1="0" x2="1">
      <stop offset="0" stop-color="{muted}" stop-opacity="0.9"/>
      <stop offset="1" stop-color="{muted}" stop-opacity="0.08"/>
    </linearGradient>
  </defs>
  <circle cx="6" cy="22" r="3.5" fill="{GREEN}"/>
  <text x="18" y="26" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{GREEN}">STATUS:</text>
  <text x="72" y="26" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{ink}">LIVE FROM GITHUB</text>
  <text x="820" y="26" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{muted}" \
text-anchor="end">EVERY WEEK IS A BUILDING</text>
  <rect x="200" y="21.5" width="400" height="1" fill="url(#rule2)"/>
</svg>"""
