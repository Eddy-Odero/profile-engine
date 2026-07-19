# Project Status - GitHub Profile Engine

## Phase 1 - Project setup ✅ DONE

- [x] Folder structure (`assets/`, `scripts/`, `generated/`, `.github/workflows/`)
- [x] Template engine (Jinja2, `scripts/renderer.py`)
- [x] README generator (`scripts/build.py`)
- [x] Random quote / status / boot-sequence data (`assets/*.txt`)
- [x] Verified end-to-end: `python scripts/build.py` produces a working `README.md`

**Deliverable met:** Automatically generated README, from static/mock data.

## Phase 2 - Avatar rendering engine (not started)

Stub at `scripts/avatar.py`. Pipeline: download → resize → grayscale →
contrast → edge detection → unicode conversion → CRT effects.

## Phase 3 - Effects engine (not started)

Stub at `scripts/effects.py`. Scanlines, noise, glitches, corruption, cursor blink.

## Phase 4 - GitHub integration (not started)

Stub at `scripts/github.py`. Will replace `MOCK_GITHUB_STATS` in `build.py`.

## Phase 5 - LeetCode integration (not started)

Stub at `scripts/leetcode.py`.

## Phase 6 - Renderer (mostly done as part of Phase 1)

`scripts/renderer.py` already handles template + placeholder rendering.
Will need small additions once avatar/effects output is added to the context.

## Phase 7 - Automation (skeleton only)

`.github/workflows/profile.yml` runs `build.py` on push and every 6 hours,
then commits the regenerated `README.md`. Not yet tested in a real repo.

## Phase 8 - Customization (not started)

Themes (Cyberpunk, CRT, Hacker, Minimal, Matrix) - no plugin system yet.

---

## How to run locally

```bash
pip install -r requirements.txt
python scripts/build.py
```

This regenerates `README.md` at the project root from `README.template.md`
plus the context assembled in `scripts/build.py`.
