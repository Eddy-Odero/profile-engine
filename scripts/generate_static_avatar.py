"""
generate_static_avatar.py

Generates assets/ascii/hacker.txt: a photo-style (not flat-block) ASCII
portrait of a hooded figure, in the same density-gradient style as real
photo-to-ASCII art - lots of midtone character variation, not just a
handful of solid fill characters.

Why a synthetic image instead of a real photo: this sandbox's network
can't fetch arbitrary photos (locked to package repositories only), and
more importantly, a hand-built synthetic image gives full control over
the one thing that actually matters for this style - dramatic
directional lighting. A flat, evenly-lit real photo is exactly what made
the original photo-avatar pipeline look noisy/muddy; a source image with
a bright hood, a properly dark (not just "somewhat dim") face void, and
a black background reuses that SAME pipeline (avatar.py's resize/
grayscale/contrast/edge functions, completely unchanged) and gets a much
better result, because the input finally has the tonal range the
technique needs.

This is a one-time generator, not part of the build pipeline - run it
by hand when the art needs re-tuning, then commit the resulting
assets/ascii/hacker.txt like any other asset:

    python scripts/generate_static_avatar.py
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import avatar
from utils import ASSETS_DIR

CANVAS_W, CANVAS_H = 700, 620
ASCII_COLS = 64
OUTPUT_FILE = ASSETS_DIR / "ascii" / "hacker.txt"


def build_synthetic_source() -> Image.Image:
    """
    Build a grayscale image of a hooded figure lit from the front-upper
    area (like a monitor's glow), with a dark face void and a pure black
    background - deliberately mimicking dramatic studio/monitor lighting
    rather than flat ambient light.
    """
    yy, xx = np.mgrid[0:CANVAS_H, 0:CANVAS_W]

    light_x, light_y = CANVAS_W * 0.5, CANVAS_H * 0.30
    dist = np.sqrt((xx - light_x) ** 2 + (yy - light_y) ** 2)
    max_dist = np.sqrt(CANVAS_W**2 + CANVAS_H**2) / 2
    brightness = np.clip(1 - (dist / max_dist) * 0.95, 0, 1) ** 1.1 * 255

    mask_img = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    d = ImageDraw.Draw(mask_img)
    d.polygon(
        [
            (CANVAS_W * 0.50, CANVAS_H * 0.04),
            (CANVAS_W * 0.22, CANVAS_H * 0.20),
            (CANVAS_W * 0.12, CANVAS_H * 0.38),
            (CANVAS_W * 0.08, CANVAS_H * 0.55),
            (CANVAS_W * 0.00, CANVAS_H * 0.68),
            (CANVAS_W * 0.00, CANVAS_H * 1.00),
            (CANVAS_W * 1.00, CANVAS_H * 1.00),
            (CANVAS_W * 1.00, CANVAS_H * 0.68),
            (CANVAS_W * 0.92, CANVAS_H * 0.55),
            (CANVAS_W * 0.88, CANVAS_H * 0.38),
            (CANVAS_W * 0.78, CANVAS_H * 0.20),
        ],
        fill=255,
    )
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
    mask = np.array(mask_img, dtype=np.float64) / 255.0

    lit = brightness * mask

    face_mask_img = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    fd = ImageDraw.Draw(face_mask_img)
    fd.ellipse(
        [CANVAS_W * 0.33, CANVAS_H * 0.24, CANVAS_W * 0.67, CANVAS_H * 0.52], fill=255
    )
    face_mask_img = face_mask_img.filter(ImageFilter.GaussianBlur(8))
    face = np.array(face_mask_img, dtype=np.float64) / 255.0
    lit = lit * (1 - face * 0.88)

    result = np.clip(lit, 0, 255).astype(np.uint8)
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
