# The display test (retired in build 384.105)

**Removed by:** commit `b6c0b68`, `index.html` only.
**Patch:** [`display-test.patch`](display-test.patch), the same diff.
**Restore:** `git revert b6c0b68`. If that conflicts, use
`git apply -R --3way retired/display-test.patch`. See [README.md](README.md)
for what to do afterwards.

## What it was

A diagnostic, never a feature: a small black panel of switches for finding
what made the top of every screen look soft and grey on the owner's iPhone
after the iOS 26 update (docs/notes-archive.md, "384 r17" to "384.85").

- **How it opened.** `?diag` in the address, or Settings > Advanced >
  Troubleshooting > "Show the display test panel" (that row was the whole
  Troubleshooting section), which set `class26e.displaytest` and reloaded.
- **Suspect switches** (`diag-*` styles, live): no backdrop blur, no glow or
  stars, no masks, no filters, no will-change, no blur on the top buttons,
  header not pinned, chat dock off, no animations, tab bar off, every fixed
  layer off, the top strip off. **Run auto test** stepped through them, 5s
  each, for a screen recording (384 r12).
- **Trials** (`dx-*` styles and elements): strips of several sizes at the top
  edge, keeping the top edge still, the colour tags changed live, how the page
  scrolls, content lower; "Keep what is on for the next launch"
  (`class26e.dxboot`); a readout of measurements to copy; a second icon with
  another status bar style (`?sbs=default|black`, read by a head script).
- **Flags the head script read before the first paint**, each turning on a
  class on `<html>`:

  | Key (`class26e.`) | Value | Class | What it did |
  |---|---|---|---|
  | `topguard` | `"0"` | (no `top-edge-on`) | no top strip at all (384 r20) |
  | `topedgeold` | `"1"` | `top-edge-old` | the old 8px `#top-guard`, a new one per colour, the tags rewritten (384.27 A/B) |
  | `topedgepe` | `"none"` | `top-edge-none` | the strip ignores touch (it has since 384.80 anyway) |
  | `topmatch` | `"1"` | `top-match` | A: the strip in the colour the wash makes (`topWashLift`) (384.77) |
  | `topdeep` | `"1"` | `top-deep` | B: `#top-deep`, a flat backdrop under the wash, behind the content (384.77) |
  | `top383` | `"1"` | `top-383` | C: no strip, the tags rewritten as 383 did (384.77) |
  | `topclip` | `"1"` | `top-clip` | the strip 11px with `background-clip:text` (384.80) |

## Why it went

Madison: "Remove the 'show the display test panel' stuff from settings by the
way." The blur is the system's own (none of the 13 auto-test steps moved it,
384.9) and he has decided it is not fixable and is not to be chased further.

## What 384.105 does that a restore has to undo

- **The flags are deleted at every launch**, in the first head script, before
  the class redirect, in both classes' copies (`class26e.X` and
  `class26e.ifc.X`): the seven above, `displaytest`, `dxboot`, and three from
  earlier rounds that nothing reads any more (`ojappoff` and `sbdefault` from
  the reverted 384.85, `topclear` from 384.54). The revert takes that block out
  with the rest; without it, a restored panel's switches would be wiped at the
  next launch.
- `displaytest` came out of the sign-out keep list and the class redirect's
  shared list (`keepRe`, `SHARED`). The revert puts it back.
- `PAGE_LOCK_SKIP` lost `top-deep` and `top-guard`.

## The gates

- `check-b384-displaytest.py`, `check-b384-autotest.py` and
  `check-b384-topguard.py` held the panel, the auto test and the old 8px strip.
  They are in [`display-test/`](display-test/) as they were in 384.95; move them
  back to `tools/` to run them (they load `tools/check-behaviour.py` from their
  own folder).
- Changed on purpose in 384.105 and to be changed back: `check-b384-topedge.py`
  (5), `check-b384-top383.py` (6) and `check-b384-bouncefix.py` (10), which held
  the switches; each now asserts the flag is deleted and changes nothing.
- `tools/check-b384-nodiag.py` asserts the panel is gone; delete it.

## What was deliberately left behind

- `#top-safe{display:none !important}` and the `top-safe` lines in
  `topStripsSky()` / `syncTopGuard()`: 384.80's, not the test's (the element
  has not been in the markup since then).
- The installed app's still top edge itself (`#top-edge`, `html.top-edge-on`,
  `syncTopGuard`, the theme-color "dance"): that is the shipped default, not a
  test setting.
