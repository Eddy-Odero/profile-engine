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

## Revision - Accessibility/readability redesign ✅ DONE

Feedback after the SVG terminal landed: the whole README had drifted into
a "hacker terminal" aesthetic that's a specific style choice, not
necessarily one that reads well to someone like an HR reviewer skimming
quickly for name, role, and project names. Four concrete changes:

1. **Real continuous animation on the terminal**, not just per-build
   text randomization: `svg_terminal.py` now has a static scanline
   texture, a scan-glow band that continuously sweeps top-to-bottom
   (`<animate>` on a gradient rect, 4s loop), and a periodic glitch
   jitter on the whole body text (`<animateTransform>`, brief jumps twice
   per 6s loop). All genuine SMIL animation, playing continuously in a
   browser - not something that only changes when the workflow reruns.
2. **Name and tagline pulled out of the terminal entirely** and put at
   the very top of the README as a plain `#` heading + subtitle - no
   terminal styling, no monospace, just normal markdown text any screen
   reader or quick skim can parse instantly. The terminal (avatar/boot/
   status) now sits further down, explicitly framed as "flavor" via a
   `<sub>` note, not the first thing anyone has to parse.
3. **`project_cards.py`** - a real card layout for projects: light
   background (not dark terminal), rounded corners, a theme-colored
   accent bar, drop shadow, wraps into a grid if there are more projects
   than fit in one row. Replaces the old `$ projects` plain-text block.
4. **`quote_card.py`** - a light card with a genuine sequential
   typewriter reveal: each line types out in turn (via per-line
   clip-path width `<animate>`s sharing one clock, offset so line 2
   doesn't start until line 1 finishes), holds fully visible, then the
   whole card resets and loops. Replaces the old static blockquote.

**A real bug caught during this work:** the initial scanline `<pattern>`
used `width="100%"`, which isn't well-defined inside an SVG `<pattern>`
and made `cairosvg` fail outright with "The SVG size is undefined."
Fixed by switching to explicit pixel dimensions (`width="4" height="3"`).
Also caught and fixed: the quote card and the `quote` context value were
independently calling `random_line("quotes.txt")`, so the image could
show a *different* quote than any other part of the README referencing
`{{ quote }}` - fixed by computing the quote once and reusing it.

**Testing method and its limits:** `cairosvg` (used only for my own
visual checks, not a project dependency) doesn't execute SMIL - it only
renders whatever the *initial* keyframe state is, which for these
animations is mostly "not yet visible" (clip width 0, scan band off-
screen). To actually verify layout, I rendered "debug" copies with the
`<animate>` tags stripped and clip widths forced open, confirming text
wrapping, spacing, and card layout are all correct. Separately confirmed
the real animated files parse and render without errors at their true
initial state. **None of this has been seen playing as an actual
animation in a real browser yet** - only reasoned through the keyframe
math and checked static snapshots. Worth watching the real GitHub-hosted
version after the next push to confirm the scan sweep, glitch jitter, and
typewriter reveal all look right in motion, not just correct on paper.

---

## Revision - Rebuild frequency + hero card

**Schedule change:** rebuild frequency reduced from every 6 hours to
once daily (`cron: "0 6 * * *"`). Rationale: even hosted live-rendering
services (github-readme-stats, capsule-render, etc.) have downtime,
which is exactly the failure mode this project's static-pre-render
architecture avoids - but that architecture still makes real API calls
on every run, so fewer runs means less exposure to rate limits
regardless of `GITHUB_TOKEN` authentication status.

**`hero_card.py`** - a gradient banner card for the "who am I" section:
initials avatar badge (not the real photo - see the module's own
docstring for why), name, role, and location with a small pin icon.
Placed above the existing plain-text `# {{ username }}` heading, not
replacing it - the plain heading stays for accessibility/screen readers/
quick-scan purposes, the hero card is additional visual polish layered
on top, not a replacement for the readable text version.

**Real bug confirmed, not yet fixed:** the avatar fallback ("avatar
unavailable") has now been confirmed to trigger on an actual GitHub
Actions run against the real repo, not just in this sandbox. Root cause
not yet identified - most likely candidate is the live workflow file not
having the `GITHUB_TOKEN` env var under the "Generate README" step
(added in Phase 4 here, but the live repo may be running an older copy
of the workflow file that predates it), which would make `avatar.py`'s
GitHub API calls unauthenticated and vulnerable to rate limiting from
GitHub Actions' shared runner IP pool. Needs the actual Actions log line
(`[avatar] fetch/render failed, using fallback: ...`) to confirm.

---

## Bug fixed: the real cause of the persistent "avatar unavailable"

**Root cause found** (from the actual Actions log line, finally):
`Unknown effects level: ''`.

The workflow passes `CRT_LEVEL: ${{ inputs.crt_level }}` and
`THEME: ${{ inputs.theme }}`, which only have real values on a manual
`workflow_dispatch` run. On every scheduled or push-triggered run - i.e.
the normal case - GitHub Actions sets those env vars to an **empty
string**, not unset. `os.environ.get("CRT_LEVEL", "subtle")` only
supplies its default when the key is missing entirely; a present-but-
empty value passes straight through as `""`. That empty string reached
`effects.apply_crt_effects()`, which correctly didn't recognize `""` as
a valid level and raised - and since that call happens inside
`build_avatar_ascii()`'s try/except, the error surfaced as an avatar
failure, even though the avatar fetch itself was never the problem.

This explains everything reported earlier: it looked identical to a
network/rate-limit failure (same fallback message, same code path) but
had a completely different cause, and it hit on *every* scheduled run
regardless of GitHub API status.

**Fixed two ways:**
1. `build.py`: `os.environ.get("CRT_LEVEL", "subtle")` -> 
   `os.environ.get("CRT_LEVEL") or "subtle"` (same for `THEME`) - `or`
   treats empty string the same as missing, `.get()`'s default doesn't.
2. `effects.apply_crt_effects()`: now treats a falsy `level` as "use the
   default" rather than raising, as defense in depth - a real typo like
   `"subtel"` still raises loudly, only emptiness is forgiven.

**Verified:** reproduced the exact bug by explicitly setting
`CRT_LEVEL="" THEME=""` (matching what GitHub Actions actually sets on
non-dispatch runs) and confirmed the error is gone and both resolve to
their correct defaults (`subtle` / `cyberpunk`). Also confirmed real
manual-dispatch values (`CRT_LEVEL=heavy THEME=matrix`) still flow
through correctly - the fix doesn't break the feature it was protecting.

**Lesson for next time:** `themes.get_theme()` was already immune to
this exact bug, since dict `.get(name, default)` treats an empty string
as simply "not a valid key" and falls through correctly - the bug was
specific to `os.environ.get(key, default)`'s different semantics
(missing vs. falsy), not the theme-lookup pattern in general.

---

## Revision - Neofetch-style two-column terminal layout

Prompted by looking at a reference profile (Andrew6rant/Andrew6rant) for
inspiration. Investigated the actual source and found it's **not** a
photo-to-ASCII avatar at all - it's a `neofetch`-style info panel:
`user@host` header, then dotted key/value rows (`OS: ..... Windows`,
`Languages.Programming: ..... Java, Python`) next to a small logo.
Same static-pre-render architecture as this project (Python script +
GitHub Actions + committed SVG), different visual content.

Decision made: keep the existing photo-to-ASCII avatar as-is (it's a
deliberate feature, not a mistake), but adopt the neofetch two-column
*layout* around it - ASCII avatar unchanged on the left, a dotted
key/value stats panel on the right, in the same visual language as the
reference without copying its content.

**`svg_terminal.py` rewritten** with:
- Two-column layout: avatar column width computed from the actual ASCII
  content, right column fixed at 44 characters for consistent dot-leader
  alignment regardless of stat value lengths
- `_dotted_row()` - given a key/value pair, computes how many `.`
  characters are needed to align at the column width, minimum 3 dots
- Right column now shows: Role, Location, Repos, Stars, Followers,
  Languages, LC Solved, LC Rating - as accent-colored bold keys, dimmed
  dot leaders, and light-colored values - then the boot log (dimmed),
  then the status line + blinking cursor
- Both columns vertically centered against whichever is taller, so a
  short fallback avatar and a short stats panel don't look lopsided
- All the existing continuous animation kept exactly as before per
  explicit request: scan-glow sweep, periodic glitch jitter, scanline
  texture, blinking cursor - none of that changed, only the layout
  and content of what's inside it

**Verified:** stress-tested the new layout with synthetic avatar/stats
data (valid XML confirmed via `ET.fromstring`, not just eyeballed),
then pixel-scanned the rendered PNG to confirm content actually
occupies both the left and right column regions with no overlap.
Re-ran `build.py` end to end and confirmed the real generated
`terminal.svg` is valid XML and renders with correctly-separated
columns (left content ending ~848-1096px, right column consistently
at ~916-1584px across many rows).

**Not yet done:** the plain-text `$ github --stats` / `$ leetcode --stats`
code blocks elsewhere in the README are now partially redundant with the
new stats panel inside the terminal SVG (though they still carry detail
the compact panel doesn't show - pinned repos, recent activity, recent
submissions). Left them in place rather than removing, to avoid losing
that detail without discussing it first. Styling those sections better,
plus the tech-stack chips, was explicitly flagged as a next step, not
done in this pass.

---

## Revision - Static hacker-in-hoodie ASCII art

Request: photo-to-ASCII conversion inherently looks noisy (established
earlier), so switch the default avatar to a hand-crafted, high-contrast
static piece instead - keep the photo pipeline available, don't remove it.

**`assets/ascii/hacker.txt`** - a 40-char-wide, 22-row hooded silhouette
facing a bordered terminal screen. Built with a `centered_core()`
construction helper (not hand-typed spacing) that asserts every row's
padding splits evenly left/right - this caught and fixed a real
asymmetry in the first draft (eyes were off-center: 3-char margin one
side, 5 the other, from manual space-counting). Every row's length is
asserted equal before writing the file, so misalignment is caught at
construction time rather than only visible after rendering.

**`build.py`**: new `AVATAR_MODE` env var, defaulting to `"static"`
(loads the file above, no CRT text-noise applied - kept clean on
purpose). `AVATAR_MODE=photo` runs the original Phase 2 pipeline
unchanged - verified both paths work correctly, the photo pipeline
isn't deprecated, just not the default.

**Verified:** confirmed the generated `terminal.svg` is valid XML and
actually contains the new art (not silently falling back). Confirmed
`AVATAR_MODE=photo` still triggers `avatar.py`'s real fetch logic
(falls back the same way it always has in this sandbox, for the same
network-restriction reasons as every previous test - not a new issue).
Symmetry was verified at construction time via assertions, which is a
stronger guarantee than eyeballing a rendered image - every row's
left/right padding is mathematically equal, not just visually close.

---

## Revision - Pivoted to photo-style density-gradient art

Reference image provided (a hooded figure rendered as real dense-ramp
ASCII, not flat blocks) showed the flat-block design above wasn't what
was wanted - it needed the genuine photo-to-ASCII *texture* (rich
midtone character variation), just depicting a hacker/hoodie subject
rather than a real personal photo.

**Key realization:** this sandbox can't fetch arbitrary photos (network
locked to package repos only), but that turned out not to matter -
`scripts/generate_static_avatar.py` builds a *synthetic* source image
with dramatic directional lighting (bright hood/shoulders, genuinely
dark face void, pure black background) using PIL, then runs it through
the **existing, unmodified** `avatar.py` pipeline functions
(`resize_for_terminal`, `to_grayscale`, `enhance_contrast`,
`blend_edges`, `pixels_to_ascii`). This validates something suspected
earlier: the photo-to-ASCII pipeline was never actually the problem -
flat, evenly-lit real photos (like a typical selfie/avatar) are what
produced noisy-looking output, because they lack the directional
lighting the technique needs. Feed it an image with real contrast and
shadow depth, and it produces exactly the rich, textured look the
reference showed.

**Verified quantitatively, not just eyeballed:** the resulting art uses
69 of the 70 possible characters in `avatar.ASCII_RAMP` - i.e. nearly
the full density range, not just a handful of flat fill characters,
which is what actually produces that photographic-gradient look rather
than a flat silhouette.

**Old block-style art preserved** at `assets/ascii/hacker_blocks.txt`
(not deleted) in case it's wanted again. `assets/ascii/hacker.txt` is
now the photo-style version and remains `build.py`'s default via the
same `AVATAR_MODE=static` path from the previous revision - no build.py
changes were needed, only the asset content changed.

**Reproducible, not a one-off:** the generation logic lives in
`scripts/generate_static_avatar.py` (run by hand, not part of the build
pipeline) rather than being a throwaway script, so the lighting/
proportions can be re-tuned later without hand-editing a 22-row
character grid again.

---

## Revision - Fixed after direct side-by-side comparison with the reference

The first synthetic attempt, compared directly against the reference
image, had three concrete problems, not just "needs polish":

1. **Blurred mask edges** produced a fuzzy, undefined silhouette
   boundary instead of a crisp one - fixed by removing the Gaussian
   blur on the silhouette mask entirely (hard cutoff = sharp edge in
   the final ASCII).
2. **Generic rounded-blob polygon** didn't read as "hoodie" - fixed
   with a deliberately-drawn shape: a pointed hood with two flaps
   hanging past the neckline (the actual visual feature that makes a
   silhouette read as a hood, not just a rounded shape), sitting above
   a separate wider shoulder/chest polygon.
3. **Smooth radial brightness gradient** produced smooth arcs of
   repeated characters ("banding") instead of real texture - fixed by
   adding actual per-pixel Gaussian random noise (`numpy.random.
   default_rng(seed).normal(...)`) on top of the base lighting, which
   is what actually produces the scattered, varied density mix real
   photo grain has.

**Self-assessed honestly, not just declared fixed:** re-inspected the
new ASCII output directly as a character grid (reading it as text,
which can be verified precisely) and confirmed the hood-flap shape,
face void, and shoulder block are all now structurally present and
distinct - not just "looks better." Character diversity re-checked:
still ~69/70 ramp characters used, now from genuine grain rather than
smooth gradient bands. Flagged explicitly to the person building this
that full visual grading against the reference is ultimately their
call, not something fully self-verifiable from this environment -
asked for their direct read on whether this iteration is closer rather
than re-asserting success.

---

## Revision - Switched svg_terminal.py from SMIL to CSS @keyframes

User-authored rewrite of `svg_terminal.py`, adopted after review rather
than accepted blind. Three real changes:

1. **SMIL (`<animate>`/`<animateTransform>`) replaced with CSS
   `@keyframes`** - a more robust long-term choice; SMIL has a spottier
   browser-support history (previously flagged as a risk in this
   project). Scan sweep, glitch jitter, and cursor blink all reimplemented
   as CSS animations.
2. **Fixed 820x380 frame** instead of dynamically-sized-to-content -
   keeps the embedded image a consistent size in the README regardless
   of how long the avatar art or stats happen to be, using
   `transform="scale()"` on the avatar/stats column groups to fit.
3. **Genuine typewriter reveal** - each line gets a staggered
   `animation-delay` (0.06s apart) so content visibly "prints" in
   sequence, satisfying the original "print the ASCII in real time" ask
   properly for the first time.

**Bug found in review, fixed before adopting:** the column-fit scaling
only checked height overflow, never width. Verified concretely: a
120x20-char (wide-but-short) art piece would render at ~900px inside a
~322px-wide column - our actual art happened to avoid this by
coincidence (its height-driven scale-down incidentally also fixed its
width), but it wasn't guaranteed for other aspect ratios. Fixed by
adding `_fit_scale()`, which takes the min of height-based and
width-based scale factors instead of height alone.

**Graceful-degradation gap found and fixed:** the typewriter effect
worked by giving every line a static `opacity: 0` CSS rule, revealed via
animation. If CSS animation didn't execute for any reason, there was no
fallback - unlike the old SMIL version (which only animated the scan/
glitch/cursor on top of always-visible text), a non-animating renderer
would see an almost entirely blank terminal. Fixed by removing the
static `opacity: 0` rule and using `animation-fill-mode: both` instead,
so the "start invisible" behavior comes entirely from the animation
itself - if animation doesn't run, there's no separate rule holding
opacity at 0, and SVG's own default (fully opaque) takes over.

**Verified concretely, not just reasoned about:** used `cairosvg` (which
doesn't execute CSS animations at all) as a real proxy for the "no
animation" failure mode. Before the fix: 0.27% of pixels showed any
content (~blank). After the fix: 5.9%, and critically, IDENTICAL to a
version with the entire `<style>` block surgically removed (proving the
fallback genuinely matches "no CSS at all", not just "improved somewhat").
Cross-checked against the old SMIL module rendered with the exact same
avatar/stats content: 6.89% visible - close enough (small gap is just
the fixed-frame's different margin proportions, not a content
regression) to confirm the fallback now matches previous known-good
behavior instead of the near-total blankness found before this fix.

Old SMIL version preserved at `scripts/svg_terminal_smil_backup.py` for
reference/rollback, not deleted.

---

## Revision - Avatar art rotation pool

Request: support multiple avatar art pieces that rotate randomly per
build, same pattern as quotes.txt/statuses.txt/boot.txt.

**`assets/ascii/avatars/`** - a new folder, globbed (not hardcoded) by
`utils.random_ascii_art()`. Any `.txt` file dropped in here is
automatically eligible next build - no code changes needed to add one.
Naming doesn't matter (`avatar_01.txt`, `my_cool_art.txt`, whatever);
the folder is the only thing that matters.

Seeded with two entries: `avatar_01.txt` (the photo-style hooded-figure
art from the previous revision) and `avatar_02.txt` (a user-uploaded
ASCII art, trimmed of surrounding blank padding lines before saving).

**`build.py`**: `build_avatar_ascii()`'s static-mode branch now calls
`random_ascii_art()` instead of reading one fixed path.

**Verified:** ran the build 4 times in a row and confirmed the
generated `terminal.svg`'s size alternated between two distinct values
matching the two source files (not stuck on one). Sampled the picker
directly 10 times and confirmed a genuinely random mix of both files,
not a fixed alternating pattern. Validated both files individually
render as well-formed XML through the actual `svg_terminal.py` renderer
before considering this done.

---

## Revision - Layout restructure + 3 more rotation-pool avatars

**Layout changes, all per direct request:**
- Terminal moved to the very first section of the README (previously
  the hero card + name heading came first)
- Removed the hero card image and the plain `# {{ username }}` /
  `### {{ tagline }}` heading entirely - both were duplicating identity
  info already shown inside the terminal itself (title bar + status
  line). `hero_card.py` is kept as a file, just no longer called from
  `build_context()` - same "don't delete, just stop using" pattern as
  the photo-avatar pipeline.
- Caption below the terminal reworded from a meta-description ("Live-ish
  terminal flair...") to read like an in-universe live session log
  instead: `~ live session · {username}@github · re-renders every
  build ~`.

**Rotation pool grown from 2 to 5 avatars** - three more user-uploaded
pieces added as `avatar_03.txt`, `avatar_04.txt`, `avatar_05.txt` (each
trimmed of surrounding blank padding first, same as `avatar_02.txt`).
Every file validated individually: rendered through the real
`svg_terminal.render_terminal_svg()` and checked with `ET.fromstring()`
for well-formed XML before being considered added, not just dropped in
and assumed to work.

**Not yet done:** tech stack section is still plain backtick-wrapped
text (`` `Go` `JavaScript` ``) - flagged as the next thing to design,
matching the card-based visual language used for projects/quotes.

---

## Revision - Custom tech-stack chips (not shields.io)

Explicit request: match shields.io's compact size/layout logic, but
design a genuinely distinct shape rather than reusing shields.io itself
- "everyone on GitHub" already uses those rounded pills, and the whole
point of this project is a from-scratch, recognizably-ours pipeline.

**`tech_pills.py`** - each tech renders as a small IC-chip-style badge:
a rectangular (not pill-rounded) body, small pin ticks protruding from
the left/right edges like a real integrated circuit's legs, and a
notch-dot in the top-left corner (evoking the orientation notch real
chips have). Auto-width per label, wraps into additional rows past
`MAX_ROW_WIDTH` (same grid-wrap approach as `project_cards.py`).

Replaced the old plain backtick list (`` `Go` `JavaScript` ``) in the
template with this rendered image.

**Verified:** validated as well-formed XML across all 5 themes, then
checked via pixel-sampling (not just eyeballing) that content actually
spans the expected width with the expected fill ratio for 6 chips with
gaps between them, and that natural height matched a single un-wrapped
row for the current (short) tech list.

---

## Revision - Removed avatar_01, updated stack, added Tools section

- `avatar_01.txt` removed from the rotation pool per request - now only
  the 4 user-uploaded pieces (`avatar_02`-`avatar_05`) rotate. Content
  not lost: it's the same art already sitting at `assets/ascii/hacker.txt`
  from the earlier photo-style-generator revision, just no longer in
  the active pool.
- `STACK` updated: removed Python, added TypeScript, PHP, Node.js, C++,
  HTML, CSS (kept Go, JavaScript, SQLite, PostgreSQL, Docker).
- New `TOOLS` list (Git, Figma, Blender, Redis) rendered as its own
  labeled chip row using the same `tech_pills.render_tech_stack_svg()`,
  just a second call with a different list - no new rendering code
  needed, the function already took an arbitrary list.
- Verified: rebuilt, confirmed both `tech_stack.svg` and `tools.svg`
  validate as well-formed XML, and confirmed via the rotation pool
  listing that `avatar_01` is genuinely gone (4 files, not 5).

---

## Revision - Redesigned projects section, with a real technical constraint solved

Request: match the dashboard reference's dark-card aesthetic, icon +
one-line description per project, plus clickable "Preview" and "Code"
icon buttons like an editor's UI.

**Important constraint surfaced and solved:** GitHub renders every
README image via `<img src="...">`, and browsers strip all
interactivity - including internal `<a>` links - from any SVG loaded
that way. This meant the original plan (one combined image with
clickable icons baked in) was impossible; nothing inside an
`<img>`-loaded SVG can ever be clickable, regardless of how it's built.

The fix: split into two pieces.
1. **`render_project_cards_svg()`** - the visual grid (dark `#16161c`
   cards, subtle `#2a2a33` border, an initials-circle icon, name, and a
   word-wrapped one-line description) - not clickable, purely visual.
2. **`render_link_badge_svg()`** - small standalone "Preview"/"Code"
   badges, generated ONCE each (not per-project, since they're visually
   identical - only the href differs). The template wraps each in
   markdown's own `[![alt](badge.svg)](url)` syntax per project - the
   link lives in the MARKDOWN, not the SVG, which is the only way to
   get a real clickable icon in a GitHub README.

**`PROJECTS` restructured** from a flat list of strings to a list of
dicts (`name`, `description`, `repo_url`, `preview_url`). `preview_url`
is `None` for all four projects right now (repo URLs are guessed from
naming convention and need verification) - when `None`, the template
shows a dimmed "not hosted yet" badge instead of a link, exactly as
requested, rather than a broken/dead link.

**Verified:** rebuilt, confirmed the actual rendered `README.md` shows
real clickable `[Code]` links to each repo and correctly falls back to
"not hosted yet" for every project's preview (since no `preview_url` is
set yet). Validated all four generated SVGs (card grid + 3 badge
variants) as well-formed XML.

**Still needed from the person building this:** verify the guessed
`repo_url` values actually match real repo names/casing, and fill in
`preview_url` for anything that's actually hosted somewhere.

---

## Revision - Color variety, semantic icons, button layout fix, full mockup

Four issues raised together, all addressed:

**1. Too much pink / most real terminals are blue or green:**
Added two new themes to `themes.py` - `cyan` (classic light-blue CRT
phosphor) and `ocean` (softer mid-blue). Switched `DEFAULT_THEME` from
`cyberpunk` to `cyan`. 7 themes now available total.

**2. Tech stack was one flat color for every chip:**
`tech_pills.py` now has a `TECH_COLORS` mapping - each language/tool
gets its own loosely brand-inspired color (Go's cyan, TypeScript's
blue, Redis's red, Figma's purple, etc.) instead of one theme accent
repeated for every chip. Unmapped entries still fall back to the theme
accent, so nothing breaks for an unrecognized tech name.

**3. Project cards: same color issue, confusing button arrangement,
letter-initial icons:**
- `project_cards.py` rewritten: each project is now its OWN separate
  SVG card (`render_single_project_card_svg`), not one shared grid
  image - necessary so View/Code buttons can sit directly under the
  correct card.
- Semantic icon glyphs replace letter initials: hand-drawn lightning
  bolt, play button, network/graph nodes, and shopping cart, selected
  per-project via an `icon` key (`PROJECTS` dicts now include one).
  Falls back to a generic `</>` glyph for unrecognized/missing keys.
- "Preview" renamed to "View" per request.
- Layout fixed using an HTML table per project: card image on top,
  then a 2-column row with View (`align="left"`) and Code
  (`align="right"`) directly underneath - tight, unambiguous
  arrangement instead of the previous stacked-text mess.
- Projects are laid out in a table grid (`batch(4)` in the template),
  matching the previous per-row card count.

**4. Full-README composite mockup:**
Built a single composite PNG (`/mnt/user-data/outputs/readme_full_mockup.png`)
combining every actual generated piece from a real build run - terminal,
tech stack, tools, all 4 project cards with their button rows, quote,
and text renders of the stats blocks - stacked in the same order the
real README uses. Not itself part of the codebase (a one-off review
tool built with PIL), but useful for reviewing the whole design at once
rather than piece by piece.

**Verified:** rebuilt end to end, confirmed every generated SVG (4
project cards, 3 badge variants, tech stack, tools, terminal) validates
as well-formed XML. Confirmed each icon glyph renders with genuinely
different pixel complexity (97-119 unique grayscale values in the icon
region, varying by icon type) rather than all being identical/blank.
Sanity-checked the composite mockup for accidental blank sections
(largest gap: 42px, consistent with normal spacing, not a missing
piece).

---

## Revision - System Modules + Fragmented-Data-style project cards

Second design reference provided (sci-fi HUD / "holographic dashboard"
aesthetic). Scope clarified: terminal stays as-is (already close in
color - `cyan` was already the default theme), this reference's other
sections get added alongside it, and Projects (missing from the
reference) gets redesigned to match instead.

**`skill_modules.py`** - new "System Modules" section: a grid of skill
badges with sci-fi HUD corner brackets (4 L-shaped marks per card, like
a targeting/scanner frame), a circular icon badge colored per-skill
(reusing `tech_pills.TECH_COLORS` for consistency), and a proficiency
level (Expert/Advanced/Intermediate). Uses short monograms (Go, JS, TS,
PG...) instead of real logos - deliberate, avoids reproducing trademarked
brand marks, which also mostly don't reduce well to a tiny circle
anyway. New `SKILLS` data in `build.py`: 8 curated (name, level) pairs,
proficiency levels are a starting guess that should be adjusted to
reflect actual comfort level.

**`project_cards.py` extended** (not replaced - same card layout from
the previous revision, extended) with two more elements from the
reference:
- A diagonal corner ribbon showing PUBLIC or VIP, driven by a new
  `visibility` field per project
- A bottom stats row: language dot + name (colored via the same
  `TECH_COLORS` map), a hand-drawn star icon + count, a hand-drawn fork
  icon + count
- `PROJECTS` gained `visibility`, `language`, `stars`, `forks` fields -
  stars/forks are placeholder zeros right now (not live-fetched per-repo
  yet), need real numbers filled in or a future live-fetch feature.
- Card height increased from 130 to 158px to fit the new row without
  cramping the existing description text.

**Verified:** rebuilt end to end, validated all project cards and the
skill modules SVG as well-formed XML. Pixel-checked the new stats-row
region specifically (not just the whole card) to confirm it has real
content variance, not a blank strip. Rebuilt the composite mockup
(`readme_full_mockup_v2.png`) with both new sections included for
holistic review.

---

## Revision - Exact-match color system + Dimensional Stats

Correction from the previous pass: the person building this wanted an
exact replica of the design reference (color, style, every visual
detail), not our own reinterpretation - and clarified System Modules
already covers what Tech Stack was doing, so having both was pure
duplication.

**Colors sampled directly from the reference image**, not estimated -
wrote a band-scanning script (`np.unique` on saturated/bright pixels
per 200px horizontal strip) to extract real hex values:
`header=#14F7FF, activity=#0BFF8E, stats=#FF00FF, modules=#FFB917,
timeline=#FB333D→#FF00A6, ribbon_public=#0BFF9F, ribbon_vip=#FFEA54`.
These live in `themes.HUD_COLORS`, plus a new `hud` theme (now
`DEFAULT_THEME`) using the header cyan + near-black-blue background,
both also sampled directly from the image rather than guessed.

**Tech Stack + Tools sections removed** from `build.py`/the template
(the modules stay as files, per the established "don't delete, stop
using" pattern) - System Modules absorbed their content: `SKILLS` now
covers all 15 former stack+tools entries, not just a curated 8.

**`skill_modules.py`** - corner brackets switched from theme-accent
cyan to the exact reference gold (`HUD_COLORS["modules"]`), matching
the real image instead of my earlier (wrong) assumption that they were
cyan.

**`project_cards.py`** - ribbon colors switched to the exact sampled
green/gold. Caught and fixed a real bug in the same pass: the ribbon
color lookup was double-prefixing `#` (producing invalid `##0BFF9F`)
after `HUD_COLORS` values were changed to already include `#` -
verified fixed with an explicit `assert '##' not in svg` check.

**`dimensional_stats.py`** - new section: 4 magenta stat cards + a
static isometric cube (three shaded polygon faces implying depth/
lighting - true rotating 3D isn't possible for the same embedding-
constraint reason nothing else here is truly animated-on-demand).
Sourced from real data: Contest Rating (LeetCode), Problems Solved
(LeetCode), GitHub Stars. **"Max Streak" from the reference was
substituted with Repos** - this pipeline has no streak-detection logic,
and fabricating a streak number wasn't an option; flagged clearly
rather than silently substituted.

**Real bug caught during this work:** `_stat_card()` called `_esc()`
(which calls `html.escape()`, string-only) directly on stat values that
are sometimes ints (star counts, repo counts) - crashed the build
immediately with `AttributeError: 'int' object has no attribute
'replace'`. Fixed by casting to `str()` first. Caught because the real
build was run end-to-end with real (mock-fallback) data, not just
tested with hand-typed string literals.

**Verified:** full rebuild succeeds end to end. Every generated SVG
(terminal, skill modules, dimensional stats, all 4 project cards)
validated as well-formed XML with an explicit check for the double-hash
bug. Confirmed `tech_stack.svg`/`tools.svg` are no longer generated at
all. Rebuilt the composite mockup (`readme_full_mockup_v3.png`) with
`SEC-X`-style section headers in the sampled cyan, for holistic review.

**Still pending:** Event Log (needs real milestone data, promised but
not yet provided) and Signal Uplink (placeholder links approved, not
yet built).

---

## Revision - Removed pink entirely, added missing grid texture

Direct, repeated feedback: no pink/magenta anywhere, and the previous
revision didn't structurally resemble the reference at all beyond
picking some colors.

**Pink removed decisively:** `HUD_COLORS["stats"]` changed from the
sampled `#FF00FF` to `#2DA8FF` (blue) - overriding my own pixel-sampling
result in favor of explicit, repeated user feedback. The Event Log
timeline gradient (`timeline_end`, previously fading to `#FF00A6` pink)
also changed to solid red, removing the only other pink reference.
Verified with a direct scan of every generated SVG file for `ff00ff`/
`magenta` - none found.

**Grid texture added** (`hud_grid.py`) - a real, previously-missing
piece of structural similarity: a faint repeating grid-line pattern,
present throughout the reference image but absent from every component
built so far (which matched colors but not this texture). Wired into
`skill_modules.py`, `dimensional_stats.py`, and `project_cards.py` as a
full-canvas background layer, with card backgrounds made slightly
translucent (`fill-opacity` 0.9-0.93) so the grid shows through faintly
even under panels - matching how the reference's dark card panels still
show grid lines beneath them.

**Bug caught and fixed during this work:** the grid rect initially used
sharp corners while project cards use rounded corners (`rx="10"`) -
this would have caused the grid's square corners to poke out past the
card's rounded shape, a visible rendering glitch. Fixed by
parameterizing `grid_background()` with an `rx` argument matching the
card's own radius. Verified concretely: sampled all 4 corner pixels of
a rendered card and confirmed full transparency (alpha=0), not a
stray square patch of grid pattern.

**Honest limitation restated:** I cannot get a visual description back
when using the image-viewing tool in this environment - every
"inspection" in this revision was done via direct pixel/array analysis
(hue histograms, corner-alpha checks, row/column content-variance
scans), not by looking at a rendered picture and describing it. This is
a real constraint on how precisely I can self-verify "does this match
the reference," and worth keeping in mind when judging future
iterations from this pipeline.

---

## Revision - Found and fixed the ACTUAL root cause of the pink issue

The real bug, finally found: `build.py` had its own hardcoded fallback -
`THEME = os.environ.get("THEME") or "cyberpunk"` - a literal string,
completely disconnected from `themes.DEFAULT_THEME`. Every previous
revision that changed the default theme (`cyberpunk` → `cyan` → `hud`)
changed the wrong place. `build.py` never imported `themes` at all, so
none of those changes ever reached the actual build - it silently kept
falling back to `"cyberpunk"` regardless. This is why pink kept
reappearing no matter how many times the color values themselves were
fixed upstream: the bug was never in the color values, it was in which
theme actually got selected.

**Fixed:** `build.py` now imports `themes` and falls back to
`themes.DEFAULT_THEME` instead of a hardcoded string. Verified directly
- `build.THEME` now correctly resolves to `"hud"`, and the real
generated `terminal.svg` now contains `#14F7FF`/`#0a0c14` (the correct
HUD cyan/near-black) instead of `#ff2079`/`#0d0221` (the old cyberpunk
pink/purple) - checked by grepping the actual fill colors out of the
real build output, not assumed.

**Grid texture made much more visible**, per direct feedback that it
should read as "grids crossing the whole design" - increased base
opacity from 0.08 to 0.22, and added a second, bolder, wider-spaced
grid layer (every 4th line) for the denser crossing-lines look in the
reference, instead of one faint uniform grid.

**Added a glow/bloom filter** (`hud_grid.glow_filter()`) - the soft
blurred-highlight look around bright elements that gives the reference
its hazy neon quality, as opposed to flat crisp shapes. Applied to
System Modules' corner brackets and Dimensional Stats' big numbers.

**Real PNG previews generated and shared directly in chat** (not just
described) - rendered every current generated SVG to PNG and sent them
as actual files, addressing the direct request to see results without
needing to push to GitHub Actions and wait for a workflow run.

---

## Revision - Section reorder + Signal Uplink built

**Reordered per direct instruction:** Terminal → System Modules →
Projects → Dimensional Stats → Quote → (stats blocks). Neural Activity
will go last once built; Event Log and an exact-match Fragmented Data
rebuild are still pending.

**`signal_uplink.py`** - social/contact pills matching the reference,
using generic hand-drawn icon glyphs (bird/chat shape, network/
connection shape, globe, envelope, controller-ish shape) rather than
the literal trademarked platform logos. Same clickable-badge pattern as
the project View/Code buttons: each pill is its own small image,
clickable only because the template wraps it in a real markdown link.

**Real links wired in**, not placeholders: Twitter, LinkedIn, Dev.to,
email. One caught early: the first LinkedIn URL provided was under a
different person's name ("Emmaculate Jane Akinyi Odhiambo") - flagged
before using it rather than silently linking someone else's profile;
corrected URL provided and used. **Discord has no link** (none
provided) - renders as a dimmed, non-clickable pill rather than a dead
link, same pattern as "not hosted yet" for projects without a preview URL.

**Verified:** rebuilt end to end, confirmed the real rendered
`README.md` produces working `[![label](pill.svg)](url)` markdown links
for all 4 real accounts and correctly omits the link wrapper for
Discord. Validated all 5 pill SVGs as well-formed XML. Rendered pills to
PNG and shared directly for visual confirmation rather than only
describing them.

---

## Revision - Corrected 3 real regressions from my own substitutions

Direct, sharp feedback: several things had drifted back to my own
design choices instead of the agreed exact-match reference, specifically:

1. **Dimensional Stats color reverted to the real sampled magenta
   (`#FF00FF`)**, undoing the earlier blue override. That override was
   meant to fix MY invented pink (the old cyberpunk-theme bug), but it
   incorrectly also overwrote this section's genuine, correctly-sampled
   reference color. Re-verified by sampling the actual crop again,
   specifically excluding the header text this time (which had skewed
   an earlier sample toward cyan) - confirmed unambiguously: dozens of
   individual pixel samples in the `#ff00ff`-`#fe00ff` range.

2. **System Modules background switched to near-black (`#050608`)**,
   full opacity (no translucency) - the previous navy-tinted, partially
   translucent version didn't read as "black" as directly pointed out.

3. **Cube rebuilt as an actual wireframe** (front face + back face +
   connecting edges, outline only) instead of the previous filled/
   shaded isometric block - the filled version was a design choice that
   didn't match the reference's real wireframe style.

**Real emoji icons added** for System Modules, replacing text
monograms - 🐍 Python, 🐳 Docker, 🐘 PostgreSQL, etc. Caught and fixed an
icon collision during this work: PHP and PostgreSQL both got the
elephant emoji initially (both languages really do use elephant
mascots, which made the mistake easy to make) - given PHP a distinct
purple circle instead so the two remain visually distinguishable.

**Discord removed entirely** from Signal Uplink, not shown as a
disabled placeholder - verified directly in the real generated
`README.md` output (`grep` for `pill_discord` returns zero matches).

**Verified:** re-sampled both corrected colors directly from rendered
output (not just source code) - skill-module card background pixel:
`(5,6,8)`, near-black as intended; dimensional-stats dominant vivid
pixel: `(249,0,250)`, matching `#FF00FF` almost exactly.

---

## Revision - Adopted an exact written spec; fixed a real opacity regression

A full detailed written spec was provided (exact colors, exact content,
exact section-by-section behavior) after continued visual mismatches -
switched to using it as the authoritative source instead of pixel-
sampling estimates, which are inherently less reliable than being told
the exact values directly.

**Real regression found and fixed:** the previous revision's "fix" for
transparent card gaps made the CARDS themselves fully opaque - correct
fix was only the full-canvas background (behind everything) needed to
be opaque; the cards themselves were always supposed to stay
translucent/glassy so the grid shows through, per the reference. Fixed:
card fill-opacity dropped to 0.3 in both `skill_modules.py` and
`dimensional_stats.py`, full-canvas background rect kept opaque. Also
switched `dimensional_stats.py`'s card border from a muted gray to the
magenta accent, matching "transparent cards with magenta borders" from
the spec.

**Exact colors adopted directly**, replacing sampled approximations:
background `#07090F`, cyan `#00E7FF`, green `#24FF9A`, magenta
`#FF38F8`, amber `#FFC84D`, red `#FF4D5A` - all now in `themes.HUD_COLORS`.

**`SKILLS` replaced** with the exact 8 from the spec: Python (Expert),
TypeScript (Advanced), Go (Advanced), Rust (Intermediate), Docker
(Expert), Kubernetes (Advanced), PostgreSQL (Advanced), AWS (Advanced) -
added matching brand colors and emoji for the 3 new entries (Rust,
Kubernetes, AWS) to `tech_pills.TECH_COLORS` and `skill_modules.
MONOGRAMS`. Caught a collision while doing this: Rust and C++ would
have both gotten a gear emoji - gave Rust its actual mascot (🦀) instead.

**Verified concretely:** counted unique colors within a card's own
pixel region after the opacity fix (190 for System Modules, up from
what a flat single-color fill would show) - direct evidence the grid
texture is genuinely visible through the card now, not just asserted.

**Honesty note:** no AI image-generation tool is available in this
environment - could not literally "generate" a concept-art PNG from the
detailed prompt provided. Used the prompt's content as an exact
specification for the code instead.

---

## Revision - Fixed the cube (real bug) and grid alignment

**Real bug found: the "centered view" cube fix from the previous
revision was the actual cause of the "looks like an Excel table"
complaint.** Setting `depth_x = 0` (for a "centered, not skewed" cube)
meant every single connecting edge between the front and back face was
perfectly vertical - which is exactly what a flat table/spreadsheet
grid looks like, not a 3D box. A cube needs DIAGONAL connecting edges
to read as 3D at all; centering the cube and giving it depth aren't the
same axis, and the earlier fix conflated them. Restored a modest
diagonal offset (`size*0.22, -size*0.3`) - enough to read as genuine
3D depth while still staying roughly centered rather than heavily
skewed to one side. Verified directly: counted the actual `<line>`
coordinates in the generated SVG - 12 of 16 edges are now genuinely
diagonal (non-vertical), versus 0 before the fix.

**Grid-alignment fix:** `CARD_GAP` (16→20), `CUBE_BOX_HEIGHT` (224→220),
and `gap_between` (30→20) all adjusted to be clean multiples of the
20px grid spacing (matching `CARD_WIDTH`/`CARD_HEIGHT`, which already
were), and the grid's own `spacing=20` is now passed explicitly instead
of relying on the function's default. Every stat card's edges now land
exactly on a grid line intersection instead of floating at an
unaligned sub-grid position.

---

## How to run locally

```bash
pip install -r requirements.txt
python scripts/build.py
```

This regenerates `README.md` at the project root from `README.template.md`
plus the context assembled in `scripts/build.py`.
