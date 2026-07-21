"""
generate_static_avatar.py

Generates assets/ascii/hacker.txt: a photo-style (not flat-block) ASCII
portrait of a hooded figure, in the same density-gradient style as real
photo-to-ASCII art - lots of fine-grained character variation, not a
smooth gradient blob.

Why a synthetic image instead of a real photo: this sandbox's network
can't fetch arbitrary photos (locked to package repositories only), and
more importantly, a hand-built synthetic image gives full control over
the things that actually matter for this style:
    1. A deliberately-drawn, recognizable hoodie silhouette (pointed
       hood, hood flaps hanging past the shoulder line) with SHARP,
       unblurred mask edges - a soft/blurred silhouette boundary reads
       as a fuzzy blob, not a defined shape.
    2. Real per-pixel grain (numpy random noise), not a smooth
       brightness gradient - smooth gradients produce smooth arcs of
       repeated characters ("banding"), which look nothing like a real
       photo's texture. Fine grain is what produces the varied,
       scattered density mix real photo-to-ASCII art has.
    3. A distinctly darker, smoother face void, separated from the
       grainy hood texture around it.

This reuses avatar.py's pipeline functions completely unchanged
(resize/grayscale/contrast/edge-blend) - the earlier "photo-ASCII looks
noisy" problem was never the pipeline's fault, it was that a flat,
evenly-lit real photo doesn't have the tonal range or grain this
technique needs. A properly-lit, properly-textured source image does.

This is a one-time generator, not part of the build pipeline - run it
by hand when the art needs re-tuning, then commit the resulting
assets/ascii/hacker.txt like any other asset:

    python scripts/generate_static_avatar.py
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

import avatar
from utils import ASSETS_DIR

CANVAS_W, CANVAS_H = 800, 900
ASCII_COLS = 64
GRAIN_SEED = 7
OUTPUT_FILE = ASSETS_DIR / "ascii" / "hacker.txt"


def _hood_and_shoulders_mask() -> np.ndarray:
    """
    A deliberately-drawn hoodie silhouette: pointed hood with two flaps
    that hang down past the neckline (the shape that actually reads as
    "hood" rather than a generic rounded blob), plus a wide shoulder/
    chest block below. No blur - sharp edges are what make the final
    silhouette read as a defined shape instead of a soft gradient.
    """
    mask_img = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    d = ImageDraw.Draw(mask_img)

    W, H = CANVAS_W, CANVAS_H
    d.polygon(
        [
            (W * 0.50, H * 0.03),
            (W * 0.30, H * 0.10),
            (W * 0.20, H * 0.22),
            (W * 0.16, H * 0.38),
            (W * 0.18, H * 0.50),  # left hood flap tip
            (W * 0.26, H * 0.42),
            (W * 0.30, H * 0.30),
            (W * 0.70, H * 0.30),
            (W * 0.74, H * 0.42),
            (W * 0.82, H * 0.50),  # right hood flap tip
            (W * 0.84, H * 0.38),
            (W * 0.80, H * 0.22),
            (W * 0.70, H * 0.10),
        ],
        fill=255,
    )
    d.polygon(
        [
            (W * 0.28, H * 0.42),
            (W * 0.72, H * 0.42),
            (W * 0.92, H * 0.62),
            (W * 0.98, H * 1.00),
            (W * 0.02, H * 1.00),
            (W * 0.08, H * 0.62),
        ],
        fill=255,
    )
    return np.array(mask_img, dtype=np.float64) / 255.0


def build_synthetic_source() -> Image.Image:
    """Build the full lit + grained + masked grayscale source image."""
    rng = np.random.default_rng(GRAIN_SEED)
    W, H = CANVAS_W, CANVAS_H

    mask = _hood_and_shoulders_mask()

    yy, xx = np.mgrid[0:H, 0:W]
    light_x, light_y = W * 0.5, H * 0.25
    dist = np.sqrt((xx - light_x) ** 2 + (yy - light_y) ** 2)
    max_dist = np.sqrt(W**2 + H**2) / 2
    base_brightness = np.clip(1 - (dist / max_dist) * 0.6, 0.15, 1) * 210

    grain = rng.normal(loc=0, scale=55, size=(H, W))
    textured = base_brightness + grain

    face_mask_img = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face_mask_img)
    fd.ellipse([W * 0.34, H * 0.14, W * 0.66, H * 0.40], fill=255)
    face = np.array(face_mask_img, dtype=np.float64) / 255.0
    textured = textured * (1 - face * 0.85)

    result = np.clip(textured, 0, 255) * mask  # hard cutoff = sharp silhouette edge
    result = np.clip(result, 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="L").convert("RGB")


def main() -> None:
    source = build_synthetic_source()

    image = avatar.resize_for_terminal(source, cols=ASCII_COLS)
    gray = avatar.to_grayscale(image)
    gray = avatar.enhance_contrast(gray)
    gray = avatar.blend_edges(gray)
    ascii_art = avatar.pixels_to_ascii(gray)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(ascii_art, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} ({len(ascii_art)} chars)")


if __name__ == "__main__":
    main()

