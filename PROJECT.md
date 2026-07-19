# Project Status - GitHub Profile Engine

## Phase 1 - Project setup ✅ DONE

- [x] Folder structure (`assets/`, `scripts/`, `generated/`, `.github/workflows/`)
- [x] Template engine (Jinja2, `scripts/renderer.py`)
- [x] README generator (`scripts/build.py`)
- [x] Random quote / status / boot-sequence data (`assets/*.txt`)
- [x] Verified end-to-end: `python scripts/build.py` produces a working `README.md`

**Deliverable met:** Automatically generated README, from static/mock data.

## Phase 2 - Avatar rendering engine ✅ DONE

- [x] Download avatar via GitHub API (`avatar.fetch_avatar_bytes`)
- [x] Resize with monospace character-aspect correction
- [x] Grayscale + contrast enhancement
- [x] Edge detection blended into grayscale for outline detail
- [x] Unicode/ASCII conversion (70-level brightness ramp)
- [x] Wired into `build.py` (`avatar_ascii` context var) and the template
- [x] Safe fallback if the fetch fails, so a bad network/rate limit never breaks the build

**Deliverable met:** high-quality ASCII portrait, with graceful degradation.

**Note on testing:** this sandbox's network egress can't reach
`avatars.githubusercontent.com` (not on the allowlist) and hit GitHub's
60/req/hr unauthenticated API rate limit besides. The full pipeline
(resize → grayscale → contrast → edges → ASCII) was verified against a
synthetic locally-generated test image and produces correct, well-structured
output. `fetch_avatar_bytes` itself will work in a normal environment or in
GitHub Actions (especially once `GITHUB_TOKEN` is set, see workflow).

CRT effects (scanlines, glitches, corruption) are deliberately NOT part of
this file - that's Phase 3 (`effects.py`), applied on top of this output.

## Phase 3 - Effects engine ✅ DONE

- [x] Scanlines - dims every Nth line slightly (`apply_scanlines`)
- [x] Screen noise - low-density random character static (`apply_noise`)
- [x] Random glitches - short corrupted spans on random lines (`apply_glitch`)
- [x] Brightness shifts - whole-text darker/lighter nudge (`apply_brightness_shift`)
- [x] Character corruption - sparse glitch glyphs, heavier than noise (`apply_corruption`)
- [x] Cursor blinking - `random_cursor()` alternates `█ / _ / ' '` each render
- [x] Random terminal messages - `random_system_message()` reads `assets/glitches.txt`
- [x] Composed into `apply_crt_effects(text, level="subtle"|"medium"|"heavy")`
- [x] Wired into `build.py`: applied to `avatar_ascii` only (not the fallback message),
      plus `cursor` and `system_message` added to the render context and template

**Deliverable met:** living terminal portrait - same avatar pipeline as Phase 2,
now with subtle randomized CRT noise that's different on every build, tunable
via `CRT_LEVEL` env var (defaults to `subtle` so the portrait stays clearly
readable; `medium`/`heavy` available for a rougher look).

**Verified:** ran `apply_crt_effects` at all three levels against the Phase 2
synthetic test portrait - subtle changes ~5-6% of characters (barely
noticeable, shape fully intact), medium ~8-9%, heavy ~20-25% (visibly
glitchy but still recognizable). Ran the full `build.py` multiple times and
confirmed status/cursor/system-message all vary per render as expected.

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
