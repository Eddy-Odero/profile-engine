"""
fragmented_data.py

"Fragmented Data" - distinct from the "Projects" section (see
project_cards.render_project_card_simple_svg), this section shows the
same real project list at a denser, more data-heavy level of detail:
PUBLIC/VIP visibility ribbon, language dot, star count, fork count.
That's exactly what project_cards.render_single_project_card_svg
already builds, so this module is a thin, clearly-named pass-through
rather than a duplicate implementation - the "needs its own rebuild"
gap was that nothing routed this data into a *second*, separately-
labeled section; the card visual itself was already right.

Usage:
    from fragmented_data import render_fragment_card_svg
    svg_markup = render_fragment_card_svg(project, theme_name)
"""

from __future__ import annotations

from project_cards import render_single_project_card_svg
from themes import DEFAULT_THEME


def render_fragment_card_svg(project: dict, theme_name: str = DEFAULT_THEME) -> str:
    return render_single_project_card_svg(project, theme_name)
