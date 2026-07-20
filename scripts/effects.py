"""
effects.py  (Phase 3)

CRT-style effects applied on top of already-rendered terminal text
(mainly the ASCII avatar from avatar.py, but these work on any block
of terminal-ish text).

Design rule: every function here is (text: str, **params) -> str, so
they can be freely composed/chained in any order from build.py without
touching renderer.py or the template. Effects are randomized (no fixed
seed) so the profile looks slightly different on every render, per the
spec's "effects change every render" requirement - but kept SUBTLE by
default so the portrait/text stays readable rather than becoming noise.
"""

from __future__ import annotations

import random

from utils import random_line

# Rough dark -> light groupings pulled from avatar.ASCII_RAMP. Used to
# nudge a character one step darker/lighter without needing to know its
# exact ramp index - keeps scanline/brightness effects generic enough
# to run on non-avatar text too (unrecognized characters are left alone).
_DARK_TO_LIGHT = list(" .:-=+*#%@$")

_NOISE_CHARS = ".:'`,^~"
_CORRUPTION_CHARS = "▓▒░×#?§¤"
_CURSOR_FRAMES = ["█", "_", " "]


def _nudge_char(ch: str, steps: int) -> str:
    """Shift a character `steps` positions along the dark<->light scale."""
    if ch not in _DARK_TO_LIGHT:
        return ch
    idx = _DARK_TO_LIGHT.index(ch)
    new_idx = max(0, min(len(_DARK_TO_LIGHT) - 1, idx + steps))
    return _DARK_TO_LIGHT[new_idx]


def apply_scanlines(text: str, interval: int = 2, steps: int = 1) -> str:
    """
    Dim every `interval`-th line slightly, simulating a CRT scanline
    passing over that row. Leaves blank lines and markdown fences alone.
    """
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        if i % interval == 0 and line.strip():
            out.append("".join(_nudge_char(ch, steps) for ch in line))
        else:
            out.append(line)
    return "\n".join(out)


def apply_noise(text: str, density: float = 0.015) -> str:
    """Randomly replace a small fraction of non-space characters with static."""
    out_chars = []
    for ch in text:
        if ch not in ("\n", " ") and random.random() < density:
            out_chars.append(random.choice(_NOISE_CHARS))
        else:
            out_chars.append(ch)
    return "".join(out_chars)


def apply_glitch(text: str, max_glitches: int = 2, glitch_len: tuple[int, int] = (3, 8)) -> str:
    """
    Corrupt a couple of short random spans with block-glitch characters,
    simulating a dropped signal / bad frame.
    """
    lines = text.split("\n")
    candidate_idxs = [i for i, l in enumerate(lines) if len(l.strip()) > glitch_len[1]]
    if not candidate_idxs:
        return text

    for _ in range(random.randint(0, max_glitches)):
        i = random.choice(candidate_idxs)
        line = lines[i]
        span = random.randint(*glitch_len)
        start = random.randint(0, max(0, len(line) - span))
        corrupted = "".join(random.choice(_CORRUPTION_CHARS) for _ in range(span))
        lines[i] = line[:start] + corrupted + line[start + span :]

    return "\n".join(lines)


def apply_brightness_shift(text: str, max_steps: int = 1) -> str:
    """Globally nudge every character darker or lighter by a small random amount."""
    steps = random.randint(-max_steps, max_steps)
    if steps == 0:
        return text
    return "".join(_nudge_char(ch, steps) if ch != "\n" else ch for ch in text)


def apply_corruption(text: str, density: float = 0.006) -> str:
    """Sparsely swap characters for glitchy corruption glyphs (heavier than noise)."""
    out_chars = []
    for ch in text:
        if ch not in ("\n", " ") and random.random() < density:
            out_chars.append(random.choice(_CORRUPTION_CHARS))
        else:
            out_chars.append(ch)
    return "".join(out_chars)


def random_cursor() -> str:
    """A blinking-cursor character. Changes each render (real animation isn't
    possible in a static README, but this simulates it across periodic builds)."""
    return random.choice(_CURSOR_FRAMES)


def random_system_message() -> str:
    """A random glitchy system-log line, for injecting into the terminal output."""
    return random_line("glitches.txt")


def apply_crt_effects(text: str, level: str = "subtle") -> str:
    """
    Compose the effects above into one pipeline. `level` controls how
    aggressive the corruption gets:
        subtle  - barely noticeable, portrait stays clearly readable (default)
        medium  - visibly glitchy but still recognizable
        heavy   - deliberately trashed, for a "signal lost" look

    An empty/falsy `level` (e.g. an env var that's set-but-blank rather
    than truly unset - the exact bug that hit build.py's CRT_LEVEL/THEME
    reads) is treated as "use the default", not as an error. A real typo
    like "subtel" still raises, since that's worth catching loudly.
    """
    level = level or "subtle"

    params = {
        "subtle": dict(noise=0.006, corruption=0.001, glitches=1, steps=0, scan_interval=4),
        "medium": dict(noise=0.02, corruption=0.008, glitches=2, steps=1, scan_interval=3),
        "heavy": dict(noise=0.06, corruption=0.025, glitches=4, steps=2, scan_interval=2),
    }.get(level, None)

    if params is None:
        raise ValueError(f"Unknown effects level: {level!r}")

    text = apply_scanlines(text, interval=params["scan_interval"], steps=max(1, params["steps"]))
    if params["steps"] > 0:
        text = apply_brightness_shift(text, max_steps=params["steps"])
    text = apply_noise(text, density=params["noise"])
    text = apply_corruption(text, density=params["corruption"])
    text = apply_glitch(text, max_glitches=params["glitches"])
    return text
