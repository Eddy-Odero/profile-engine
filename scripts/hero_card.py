"""
hero_card.py

The visual-heavy "who am I" section: a gradient banner card with an
initials avatar badge, name, role, and location - the kind of polished
header the top profile READMEs use, instead of a plain markdown heading.

Deliberately does NOT try to embed the real GitHub avatar photo here.
SVG <image> tags CAN reference external URLs, and it's tempting to point
one at the live avatars.githubusercontent.com URL for a real photo - but
GitHub sanitizes SVGs it renders and it's not confirmed whether external
image references survive that sanitization. Rather than ship something
that might silently fail, this uses an initials badge: guaranteed to
render, zero external dependency, and it's a well-established design
pattern on its own (Gravatar, Slack, and plenty of other products use
initials avatars as the default/fallback).

Usage:
    from hero_card import render_hero_svg
    svg_markup = render_hero_svg(name="Eddy Odero", role="Full-Stack Developer",
                                  location="Kisumu, Kenya", theme_name="cyberpunk")
"""

from __future__ import annotations

import html

from themes import DEFAULT_THEME, get_theme

WIDTH = 760
HEIGHT = 180
BADGE_RADIUS = 56
BADGE_CX = 110
BADGE_CY = HEIGHT / 2
TEXT_X = 210


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _initials(name: str) -> str:
    """First letter of up to the first two words of the name, uppercased."""
    words = [w for w in name.replace("-", " ").split() if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _location_pin(x: float, y: float, color: str) -> str:
    """A small map-pin icon, drawn as plain SVG paths (no external icon font)."""
    return (
        f'<g transform="translate({x},{y}) scale(0.055)" fill="{color}">'
        '<path d="M12 0C7.6 0 4 3.6 4 8c0 6 8 16 8 16s8-10 8-16c0-4.4-3.6-8-8-8z '
        'M12 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/></g>'
    )


def render_hero_svg(
    name: str,
    role: str,
    location: str,
    theme_name: str = DEFAULT_THEME,
) -> str:
    """Build the SVG markup for the hero/about banner."""
    theme = get_theme(theme_name)
    accent = f"#{theme['color']}"
    dark = f"#{theme['label_color']}"
    initials = _initials(name)

    return f"""<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" \
xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(name)}, {_esc(role)}, {_esc(location)}">
  <defs>
    <linearGradient id="heroGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{dark}"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0.55"/>
    </linearGradient>
    <radialGradient id="dotFade" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="white" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="white" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="url(#heroGrad)"/>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="url(#dotFade)"/>

  <circle cx="{BADGE_CX}" cy="{BADGE_CY}" r="{BADGE_RADIUS}" fill="{dark}" fill-opacity="0.35" stroke="{accent}" stroke-width="2.5"/>
  <text x="{BADGE_CX}" y="{BADGE_CY + 12}" font-family="Segoe UI, Helvetica, Arial, sans-serif" \
font-size="34" font-weight="700" fill="white" text-anchor="middle">{_esc(initials)}</text>

  <text x="{TEXT_X}" y="{HEIGHT / 2 - 22}" font-family="Segoe UI, Helvetica, Arial, sans-serif" \
font-size="30" font-weight="700" fill="white">{_esc(name)}</text>
  <text x="{TEXT_X}" y="{HEIGHT / 2 + 10}" font-family="Segoe UI, Helvetica, Arial, sans-serif" \
font-size="17" fill="{accent}">{_esc(role)}</text>

  {_location_pin(TEXT_X, HEIGHT / 2 + 24, "white")}
  <text x="{TEXT_X + 20}" y="{HEIGHT / 2 + 42}" font-family="Segoe UI, Helvetica, Arial, sans-serif" \
font-size="14" fill="white" fill-opacity="0.8">{_esc(location)}</text>
</svg>"""
