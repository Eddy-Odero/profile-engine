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

**Real bug hit and fixed:** the initial `enhance_contrast()` used a fixed
1.35x multiplier applied to the RGB image before grayscale conversion.
That only helps if the source photo already spans close to the full
brightness range. A soft/low-contrast source image (reported: a sunset +
tree silhouette avatar) only used a **60-194** luminance band out of
0-255 after resize+grayscale - narrow enough that most of the 70-char
ASCII ramp never got used, so the portrait read as a blurry wall of
similar-looking texture instead of a recognizable shape.

Fixed by switching to `ImageOps.autocontrast()` (histogram stretch,
applied to the grayscale image, with a 1% cutoff so a stray extreme
pixel can't dominate the stretch) before a much milder 1.15x boost on
top, and reordering the pipeline so grayscale conversion happens before
the contrast step (previously contrast ran on RGB first). Verified with
a synthetic reproduction of the reported issue - confirmed the luminance
range goes from 60-194 to the full 0-255 after the fix, and the
tree/silhouette shape becomes clearly distinguishable in the ASCII output
that was previously flat and hard to read.

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

## Phase 4 - GitHub integration ✅ DONE

- [x] Repo count, followers (`github.fetch_profile`)
- [x] Total stars, top languages, aggregated across all non-fork repos (`github.aggregate_repo_stats`)
- [x] Recent public activity, turned into readable lines (`github.fetch_recent_activity`)
- [x] Pinned repos + contribution count via GraphQL (`github.fetch_graphql_extras`) - requires `GITHUB_TOKEN`
- [x] Graceful 3-tier degradation: full GraphQL stats → REST-only approximation (pinned = top-starred repos, contributions = N/A) → mock stats if REST itself fails
- [x] Wired into `build.py` (`build_github_stats()`, same defensive pattern as `build_avatar_ascii()`)
- [x] Template updated: stats block now shows contributions/languages/pinned, plus a new `$ github --activity` block

**Deliverable met:** live profile statistics, with the same "never hard-fail
the build" philosophy as Phase 2.

**Note on testing:** this sandbox's IP is rate-limited by GitHub's REST API
(0/60 remaining, shared across sandbox sessions), so live end-to-end calls
couldn't be exercised here. Instead, `github.py`'s logic (pagination,
fork-exclusion, star/language aggregation, GraphQL response parsing, and
both fallback tiers) was verified with mocked `requests.get`/`requests.post`
responses covering realistic repo/event/GraphQL payloads - all paths
(with-token, without-token) produced correct output. The mock-stats
fallback path was verified via a full `build.py` run.

## Phase 5 - LeetCode integration ✅ DONE

- [x] Solved counts by difficulty (total/easy/medium/hard) via LeetCode's GraphQL endpoint
- [x] Contest rating, global ranking, top percentage, contests attended
- [x] Badges
- [x] Recent accepted submissions
- [x] "No contest history" handled as a normal state (`rating`/`ranking`/etc. = `None`), not an error
- [x] Wired into `build.py` (`build_leetcode_stats()`, same defensive pattern as Phases 2 & 4)
- [x] Template: new `$ leetcode --stats` block, plus a conditional `$ leetcode --recent`
      block that only appears when there's submission history to show

**Deliverable met:** competitive programming dashboard, degrading gracefully
same as the GitHub integration.

**Note on testing:** `leetcode.com` isn't on this sandbox's network
allowlist, so live calls aren't reachable here (confirmed: the real
`build.py` run got a 403 from the sandbox's egress proxy and fell back to
mock data cleanly, exactly as intended). `leetcode.py`'s parsing logic was
verified with mocked GraphQL responses covering three cases: a user with
contest history, a user with none (ratings/ranking all `None`, not an
error), and a nonexistent username (raises `ValueError`, caught by
`build.py`'s fallback). This endpoint is unofficial (LeetCode has no public
REST API) - it's the same one leetcode.com's own frontend uses, and the
approach every open-source "LeetCode stats card" project relies on, but
it's not a documented/stable contract, so keep an eye out if LeetCode ever
changes its schema.

## Phase 6 - Renderer ✅ DONE

Template rendering and placeholder replacement were effectively finished as
a side effect of Phases 1-5 (`scripts/renderer.py`, `README.template.md`).
This pass hardened the error handling specifically:

- [x] Template syntax errors now raise `RuntimeError` with the line number
      and a plain-English description, instead of a raw Jinja traceback
- [x] Missing context keys (e.g. someone adds `{{ new_field }}` to the
      template without updating `build_context()`) now raise `RuntimeError`
      pointing at exactly which key is missing and where to fix it
- [x] Verified both error paths deliberately (missing key, broken `{% for %}`)
      and confirmed the normal build path still works unchanged afterward

**Deliverable met:** complete, robust README generation - a bad template
edit now fails with a message that says what's wrong and where, not a
50-line Jinja stack trace.

## Phase 7 - Automation ✅ DONE

- [x] `permissions: contents: write` - required or the push step 403s
      (this was the actual bug reported and fixed mid-project)
- [x] `concurrency` group with `cancel-in-progress: true` - prevents a
      scheduled run and a push-triggered run from racing to commit/push
      at the same time
- [x] pip dependency caching (`cache: pip` in `setup-python`) - faster runs
- [x] `workflow_dispatch` now accepts a `crt_level` choice input (subtle/
      medium/heavy) for manually trying a different look without editing code
- [x] `git pull --rebase` before push - reduces (but doesn't eliminate)
      push-conflict risk if something else touched `main` mid-run
- [x] Commit step now stages `generated/` too, not just `README.md`, so
      `stats.json` stays in sync with what's actually in the README
- [x] `GITHUB_TOKEN` passed through to the build step (added in Phase 4)
      so `github.py`'s GraphQL calls get real pinned-repos/contributions data

**Deliverable met:** zero manual maintenance, once `GITHUB_USERNAME` and
`LEETCODE_USERNAME` in `build.py` are set to your real handles and the repo's
Settings → Actions → General → Workflow permissions is set to "Read and
write" (see the earlier fix for the exact 403 this project hit).

**Not done / known gaps:** the `git pull --rebase` step reduces race risk
but two truly simultaneous runs could still conflict since `generated/`
changes every build - the `concurrency` group is the real fix for that and
should cover it in practice. Not yet tested against a real repo's Actions
tab (only validated the YAML parses and the build step behaves correctly
locally).

**Real bug hit and fixed:** the first live run committed fine but then
`git pull --rebase` failed with "You have unstaged changes" - caused by
`scripts/__pycache__/*.pyc` having been committed to the repo before a
`.gitignore` existed, so every build left those tracked files modified but
unstaged. Fixed two ways: added `.gitignore` (`__pycache__/`, `*.pyc`, etc.)
to stop tracking them going forward, and changed the commit step to
`git add -A` as a safety net so no stray tracked-file change can ever block
the rebase again. One-time manual cleanup still needed on the actual repo
(the already-tracked pycache files won't untrack themselves just because
`.gitignore` now exists) - see the note sent alongside this update.

## Phase 8 - Customization ✅ DONE (badges), plugin system not started

- [x] 5 themes: Cyberpunk, CRT, Hacker, Minimal, Matrix (`scripts/themes.py`)
- [x] Each theme is a shields.io color palette (badge color, label color, badge style)
- [x] `scripts/badges.py` builds a themed badge row (repos, stars, followers,
      LeetCode solved, LeetCode rating) as markdown image links
- [x] Wired into `build.py` via `THEME` env var (default `cyberpunk`), same
      pattern as `CRT_LEVEL`; unknown theme name falls back cleanly
- [x] Workflow's `workflow_dispatch` now has a `theme` choice input too, so
      you can preview any theme from the Actions tab without editing code
- [x] Footer now records which theme rendered the current README

**Why badges, not colored ASCII/SVG:** this directly answers the earlier
"why does it look plain" question. GitHub renders code-block text as flat
monospace - no color, no matter what characters go inside it. Shields.io
badges are markdown *images*, which GitHub renders with full color, so
they're the only piece of this README that will actually look colorful
and "themed" rather than just differently-textured plain text. The ASCII
avatar and CRT effects stay monospace/textual by design (that's Phase 2/3's
job) - badges are the visual-styling layer on top.

**Not built:** a real plugin system (arbitrary user-defined themes/rendering
modules) - out of scope for now, flagged as a stretch goal in the original
spec, not a Phase 8 requirement. Also not built: an SVG-rendered colored
terminal image (the "Live SVG terminal" stretch goal) - that would be the
next step if actual colored terminal visuals (not just badges) are wanted
later.

**Verified:** ran the build across all 5 themes via `THEME=<name>` and
confirmed each produces correctly-colored, correctly-styled badge URLs;
confirmed an unknown theme name falls back to the default instead of
crashing.

---

## Stretch Goal - Live SVG Terminal ✅ DONE

This is the actual answer to "why does it look plain, not styled." Every
other piece of this project (ASCII avatar, CRT text-noise, boot sequence,
even the Phase 8 badges) is either flat monospace text or a static colored
pill. None of it is a real dark terminal window with glowing colored text.

- [x] `scripts/svg_terminal.py` renders the avatar + boot sequence + status
      line as an actual SVG image: rounded dark window, macOS-style traffic-
      light dots, theme-colored monospace text, a soft glow filter
      (`feGaussianBlur` + `feMerge`), and a **real blinking cursor** using
      SVG's native `<animate>` (SMIL) - not simulated by changing content
      between builds like the old text-only cursor, an actual animation
      that plays continuously in the browser
- [x] Written to `generated/terminal.svg` each build, referenced from
      `README.md` via a relative path - GitHub serves same-repo relative
      image paths as raw files, not through its script-stripping proxy
      (that's only for external URLs), so the SMIL animation survives
- [x] Uses the same `THEME` palette as the Phase 8 badges, so the whole
      README stays visually consistent under one theme choice
- [x] `README.template.md`'s old plain-text avatar/boot code blocks
      replaced with a single `![...](generated/terminal.svg)` embed

**Verified:** rendered the SVG to PNG locally (via `cairosvg`, a
dev-only tool used just for this visual check - **not** a project
dependency, `svg_terminal.py` only builds markup strings) and inspected
it directly across multiple themes and both a small fallback-text case
and a realistic 60-column avatar. Confirmed layout, spacing, and text
don't clip or overlap in either case.

**Honest caveats:**
- SMIL (`<animate>`) is what makes the cursor blink for real. It's been
  deprecated-then-undeprecated in browser engines before and Chrome has
  floated removing it again in the past - if it ever actually gets pulled,
  the cursor would just render as a solid non-blinking block, not break
  anything.
- This hasn't been seen rendered in an actual GitHub-hosted README yet -
  only locally via `cairosvg`, which is a different SVG renderer than
  what browsers use. Worth checking your real GitHub profile page after
  the next push to confirm it looks right there specifically.
- No dark/light-mode awareness - GitHub READMEs can be viewed in either,
  and this SVG always renders with its own fixed background regardless
  of the visitor's GitHub theme. That's normal for embedded images (badges
  have the same limitation) but worth knowing.

---

## How to run locally

```bash
pip install -r requirements.txt
python scripts/build.py
```

This regenerates `README.md` at the project root from `README.template.md`
plus the context assembled in `scripts/build.py`.
