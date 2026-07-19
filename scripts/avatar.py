"""
avatar.py  (Phase 2)

Pipeline: GitHub avatar -> resize -> grayscale -> contrast enhancement
          -> edge detection -> unicode conversion -> ASCII portrait

CRT effects (scanlines, noise, glitches, cursor blink, corruption) are
intentionally NOT applied here - that's effects.py / Phase 3. This
module's only job is to turn a photo into a clean, high-detail ASCII
portrait. build.py composes the two later.

Usage:
    from avatar import generate_avatar_ascii
    ascii_art = generate_avatar_ascii("EddyOdero", cols=70)
"""

from __future__ import annotations

import io

import numpy as np
import requests
from PIL import Image, ImageEnhance, ImageFilter

from utils import GENERATED_DIR, github_headers

GITHUB_API = "https://api.github.com/users/{username}"

# Dense-to-sparse brightness ramp (dark chars = bright pixels, since
# terminals are usually light-text-on-dark-background). ~70 levels
# gives noticeably smoother gradients than the classic 10-char ramp.
ASCII_RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

# Terminal characters are taller than they are wide. Without correcting
# for this, ASCII art comes out vertically stretched. ~0.5-0.55 is the
# standard fudge factor for monospace fonts.
CHAR_ASPECT_CORRECTION = 0.5


def fetch_avatar_bytes(username: str, size: int = 460) -> bytes:
    """
    Resolve a GitHub username to its avatar image bytes.

    Uses the GitHub API (not github.com/user.png) so we get a stable,
    direct CDN URL back rather than depending on a redirect.
    """
    headers = github_headers()

    api_resp = requests.get(
        GITHUB_API.format(username=username), headers=headers, timeout=10
    )
    api_resp.raise_for_status()
    avatar_url = api_resp.json()["avatar_url"]

    img_resp = requests.get(f"{avatar_url}&size={size}", headers=headers, timeout=10)
    img_resp.raise_for_status()
    return img_resp.content


def load_image(data: bytes) -> Image.Image:
    """Load raw image bytes into a Pillow Image, normalized to RGB."""
    return Image.open(io.BytesIO(data)).convert("RGB")


def resize_for_terminal(image: Image.Image, cols: int) -> Image.Image:
    """Resize to `cols` wide, correcting for monospace character aspect ratio."""
    width, height = image.size
    rows = max(1, int(cols * (height / width) * CHAR_ASPECT_CORRECTION))
    return image.resize((cols, rows), Image.LANCZOS)


def enhance_contrast(image: Image.Image, factor: float = 1.35) -> Image.Image:
    """Boost contrast so mid-tones spread out and detail doesn't wash out."""
    return ImageEnhance.Contrast(image).enhance(factor)


def to_grayscale(image: Image.Image) -> Image.Image:
    return image.convert("L")


def blend_edges(gray_image: Image.Image, edge_strength: float = 0.45) -> Image.Image:
    """
    Detect edges and subtract them from the grayscale image so outlines
    (hair, glasses, jawlines) render darker/denser than flat regions of
    similar brightness. Returns a new grayscale image.
    """
    edges = gray_image.filter(ImageFilter.FIND_EDGES)

    gray_arr = np.asarray(gray_image, dtype=np.int16)
    edge_arr = np.asarray(edges, dtype=np.int16)

    combined = gray_arr - (edge_arr * edge_strength).astype(np.int16)
    combined = np.clip(combined, 0, 255).astype(np.uint8)

    return Image.fromarray(combined, mode="L")


def pixels_to_ascii(image: Image.Image, ramp: str = ASCII_RAMP) -> str:
    """Map each pixel's brightness to a character in `ramp` and join into rows."""
    arr = np.asarray(image, dtype=np.float32)
    # Normalize 0-255 -> 0-(len(ramp)-1)
    indices = (arr / 255 * (len(ramp) - 1)).astype(np.uint8)

    rows = []
    for row in indices:
        rows.append("".join(ramp[i] for i in row))
    return "\n".join(rows)


def generate_avatar_ascii(
    username: str,
    cols: int = 70,
    write_to_disk: bool = True,
) -> str:
    """
    Full Phase 2 pipeline: username -> ASCII portrait string.

    If `write_to_disk` is True, also saves the result to
    generated/avatar.txt so it can be inspected/reused without
    re-hitting the GitHub API.
    """
    raw = fetch_avatar_bytes(username)
    image = load_image(raw)
    image = resize_for_terminal(image, cols)
    image = enhance_contrast(image)
    gray = to_grayscale(image)
    gray = blend_edges(gray)
    ascii_art = pixels_to_ascii(gray)

    if write_to_disk:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        (GENERATED_DIR / "avatar.txt").write_text(ascii_art, encoding="utf-8")

    return ascii_art


if __name__ == "__main__":
    import sys

    name = sys.argv[1] if len(sys.argv) > 1 else "octocat"
    print(generate_avatar_ascii(name))
