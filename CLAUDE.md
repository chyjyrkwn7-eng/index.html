# Nova — working notes

Study app for Class 26E, used by ~40 classmates. **26E is a police academy
class**, which is worth knowing before writing any copy for it: "While you
study" was rejected as a Settings header for not reading official enough, and
became "Studying & tests". The tone the app wants is plain and unfussy, not
chatty.

Most of this is distilled from a handoff written across the sessions that built
the app, plus what was learned working directly in the repo. Where the two
disagreed, the repo won and the difference is called out.

---

## Repo and deployment

- `index.html` — the app itself. Markup, one `<style>` block, all logic.
- `launch/` — iOS startup images, referenced by path from `index.html`.
  **Deploys with it.** See **iOS install-time metadata**.
- `version.json` — update-check sidecar. See **Shipping a change**.
- `tools/check-js.py` — syntax check for the inline scripts. See **Verifying**.
- `tools/gen-startup-images.py` — regenerates the iOS launch images. See the
  iOS section. `--check` fails if the block in `index.html` is stale.
- `tools/gen-app-icon.py` — draws the app icon and writes it into all three
  places it lives. `--check` fails if they drift. See **The app icon**.
- `tools/sim-safe-area.py` — bakes real safe-area insets into a copy for
  local testing. See **Verifying**.
- `tools/sweep-layout.py` — every main screen on every supported form
  factor. See **Every device, every way in**. Exits non-zero on a failure.
- `tools/check-positions.py` — the companion to it: not "is anything
  broken" but "did what I just positioned land where I meant it to", on
  every device. See **Every device, every way in**.
- `tools/shoot-flow.py` — screenshots every onboarding screen, Home and
  Settings by *clicking through* from a fresh install on seven devices,
  rather than mounting screens. Use it for anything Madison will look at.
- `tools/record-cutscenes.py` — the animations, **as animations**: GIFs of
  the badge unlock, the badge queue, all seven rank cutscenes, the
  Supernova cutscene, the Void cutscene, and a real full-unit 100% run from the last question
  through to both cutscenes it triggers. A still of a cutscene is a still
  of one arbitrary frame; picking that frame by hand is how a 20-second
  cutscene gets reported as "nothing happens". See **Recording an
  animation**.
- `tools/shoot-results.py` — the three screens `shoot-flow.py` cannot
  reach, because each needs a real run behind it: an end-of-test
  results screen, the Virtual Room results screen, and the race line
  with several people on nearly the same question. It runs a drill for
  real, answers every question correctly, then swaps in a finished
  four-person room. **That "needs run state" is also why none of them
  was in `SCREENS`, and therefore why five things were wrong on the
  Virtual Room results screen at once with every gate green.**
- `tools/shoot-flares.py` — the two Secret Flare screens a walk cannot
  reach (the glint hiding inside a live question, and the banner that
  only exists for five seconds after it is tapped), plus a contact
  sheet of all sixteen characters at tile size AND at the 34px a
  rankings row actually uses. The Customise screen is NOT here — it is
  reachable by clicking, so it belongs in `shoot-flow.py`, which is
  where it now is. It also measures whether the flare banner is sitting
  on a control, because it is the only banner in the app that lands on
  a question rather than on an empty screen.
- `tools/check-fixes.py` — the third question, after "is anything
  broken" (the sweep) and "did it land where I meant it to"
  (check-positions): **is this specific fix actually in effect here**,
  on every device, both orientations, installed and in a browser. Written
  after a batch of device-reported bugs were each verified on one iPad,
  which is not the bar. Exits non-zero and names the device. Extend it
  when a fix is worth holding to across the matrix; delete a check when
  the thing it guards is gone. Takes `--only <substring>` like the sweep,
  because 63 runs of a page that waits on a splash is a long time to wait
  to find out one device is wrong.
- `tools/check-sync.py` — the question none of the three layout tools can
  answer: **does this build still keep people's accounts?** The sync code
  surviving, recovery landing somewhere that isn't Welcome, a rankings row
  being retired when its code is abandoned, and Find me naming the right
  reason. Device-independent, so it runs once rather than 63 times. Every
  check in it was written against a build where it failed; `--against
  old-index.html` re-runs it there, which is the only thing that makes a
  green run mean anything. See **Accounts and the sync code**.
- `tools/check-friends.py` — the friends gate, and the only one that
  asks **is the online dot telling the truth, and does it lead
  anywhere?** Device-independent, so it runs once. Sections 10 and 11
  were written against build 166 and fail there; `--against` is what
  makes a green run mean anything. See **Friends**.
- `tools/check-tours.py` — **do the tooltips still point at things that
  exist?** `renderStep()` does `if(!el){ advance(); return; }`, so a tour
  step whose selector no longer matches anything is skipped IN SILENCE:
  the tour still runs, still looks fine, and is simply shorter than it
  was written to be. That is how the Profile tour lost its calendar step
  for months. This walks every tour on both reference devices and
  asserts the number of steps that render equals the number the source
  declares, and that no tooltip leaves the viewport. It also fails if a
  `startSimpleTour` call site has no scenario in it, on the same
  principle as `SCREENS`. Takes `--only`.
- `tools/check-behaviour.py` — **does the app still DO the right
  thing**, as opposed to still look right: the splash centred from its
  first visible frame, a thumb swipe changing the top tab, a back link
  landing somewhere that is not blank, a badge earned by every route to
  mastery and only then, and a queue of badges playing back to back on the
  main menu. Every check in it was written against a build where it
  failed; `--against old-index.html` runs it there.
- `tools/check-unlocks.py` — **the four EARNED characters and the
  Secret Flares that gate one of them.** Four counters (`dailyCorrectStreak`,
  `unitHundoStreak`, `practiceTestPassed`, the flares) have to move at
  the right moment and stop at the wrong one, and none of the other
  gates can see any of it: a streak that silently never increments looks
  exactly like a streak nobody has earned yet, and the first person to
  notice would be somebody who answered ten daily questions in a row for
  nothing. It also asserts the flare's glint overlaps **no answer
  choice**, on the reasoning that a stray tap on a decoration is a shrug
  while a stray tap that eats an answer is a wrong answer somebody did
  not give. Device-independent, so it runs once. Written against build
  132 and fails there 13 ways; `--against` proves it. It also sweeps
  EVERY placement the glint can pick on the narrowest phone in the
  matrix, which is how the 44px box landing on the words "Question 1"
  across a third of its range was found — one sample on one device is
  not a check.
- `tools/check-vroom.py` — **two devices, for real.** Everything else
  in `tools/` drives one page; a Virtual Room's whole job is two devices
  agreeing, and the things reported about it (ready-up not reaching the
  other device, the host seeing the test first, the lobby list going
  empty) are invisible to a one-page harness. Two tabs in ONE context,
  so they share an origin and therefore `localStorage` and its `storage`
  event; the fake Firestore keeps the room document there and pushes
  snapshots on write, with `--latency` to dial up a bad connection.
  Three rules it was taught the hard way and that must not be undone:
  **never `element.click()` or `?.click()`** — both bypass hit-testing
  and the second makes a missing element a silent pass, which is what
  took this gate to a 25% false-failure rate; **wait for the lobby, do
  not sleep at it** — every fixed `wait_for_timeout` around a join was
  a coin flip; and **the harness must echo back the build it serves**
  in `version.json`, or `--against` an older copy trips the forced
  update and reloads the page out from under the run.
  A fourth, learned later and the cause of a run-in-three failure rate
  that looked like everything except what it was: **every tab needs its
  own `publicId` in the fixture.** `publicIdOf()` mints one on demand
  and `saveStore()`s it — into `localStorage`, which every tab in one
  context SHARES. Whichever tab minted first wrote its id to disk, a
  tab booting after read the same id and became the same account, and
  its join came back "this account is already in the lobby" and did
  nothing. Two devices are two accounts; the fixture has to say so.
  **And every section closes its own tabs**, because the fake wakes
  every listener in the context on every write — eight live tabs was
  enough to stop a fresh join landing inside 25 seconds, and the
  symptom was whichever heavy section happened to run last.
- `tools/firestore-admin.py` — `list`, `find <username>` and
  `purge --yes` against the live Firestore over the plain REST API, no
  SDK. `find` is the "someone lost their code" lookup, and it needs a
  service-account key in `NOVA_ADMIN_KEY` (or `NOVA_ADMIN_KEY_FILE`) to
  return an actual code: the rules are open for reading ONE document but
  refuse to list `progress`, which is where the codes are. Anonymous, it
  says so and falls back to rankings rows. **It is a tool and not a
  screen on purpose** — see **Accounts and the sync code**.
- GitHub Pages serves `main`. No build step, no bundler, no `npm install`.
- Develop on `claude/repo-update-jquqz4`; merge to `main` to deploy.
- **THIS IS THE REPO THE CLASS USES.** It is served at
  `https://chyjyrkwn7-eng.github.io/index.html/`, which is the link ~40
  classmates already have and are studying from. The repo is
  confusingly *named* `index.html` - that is the repository's name, not
  a path - and the Pages URL follows from it.
  **A merge to `main` here is a deploy to real people**, within about a
  minute. There is no separate test repo any more: the build repo this
  was developed in (`Nova-Test`) was retired once everything moved
  across, so there is nowhere to try a change first. Verify before
  merging, not after - the gates in **Verifying** are the whole safety
  net now.

**DO NOT MERGE TO `main` UNTIL MADISON HAS SEEN THE SCREENSHOTS AND SAID
GO.** This supersedes the merge-on-green instruction below, and it is the
current one. Asked for directly — *"Add a hold till I see the screenshots"*
— once it became clear what a merge here actually does: this repo has been
the live repo since build 97, so `main` is ~40 classmates' phones about a
minute later, not a staging URL. The sequence is: finish the change, run
the gates in **Verifying**, send both reference screenshots, and then
**wait**. A green matrix is permission to ask, not permission to ship.

**The superseded instruction, and why it existed**, because the failure
mode it was written for is real and has not gone away: a whole session's
work once sat on the branch while she opened the app and found nothing had
changed, and a branch that is 11 commits ahead looks exactly like one that
is up to date from the Home Screen. So the hold costs something, and the
price of it is stated plainly every time: **whenever work is finished but
NOT on `main`, say so in the same message as the screenshots** — name the
build and say it is waiting on her go. Never let her discover it by
opening the app. That sentence was load-bearing under the old instruction
and it is load-bearing under this one, for opposite reasons.

**A hold is not a reason to stop working.** Keep going down the list,
keep committing and pushing to the branch, keep the gates green. What
waits is the merge, and only the merge.

**Single file is the deployment model, not accretion.** Even Firebase loads via
plain `<script src=...compat.js>` rather than an ES module, precisely so no
bundler is needed. Introducing a build pipeline is a bigger decision than it
looks — it changes how ~40 people's browsers load the app.

**OUTSTANDING, AND NOT A DEFECT: the Firestore admin key is not set
up.** `tools/firestore-admin.py find` cannot return a sync code without
one — see **Accounts and the sync code**. Everything testable about it
passes; only "does Google accept a real key" is unverified. Nobody is
waiting on it and nothing is broken; it is the backstop for a classmate
who loses their code with nothing saved. Madison asked to be reminded
rather than pushed.

There **is** a web app manifest, embedded as a base64 `data:` URI on a
`<link rel="manifest">`. Grepping for `manifest.json` finds nothing and it is
easy to conclude there is none. Decode it to edit; never hand-patch the base64.

---

## Hard rules

- **Every change is verified across the whole device matrix before it
  ships** — every device, both orientations, installed *and* in a browser.
  `python3 tools/sweep-layout.py`. See **Every device, every way in**.
- **Never rename `STORE_KEY` (`"class26e.drill.v1"`) or `"class26e.synccode"`.**
  Either orphans real saved progress on ~40 devices. This includes not
  "fixing" `class26e` to `nova` to match the rebrand — the rename was cosmetic
  and deliberate. Same for the Firebase project id and the IndexedDB name.
- **Never call Firestore `.onSnapshot()` directly** — always
  `onSnapshotResilient()`, which backs off and resubscribes. Direct calls
  reintroduce a shipped bug class where listeners went silently stale.
- **Applying data that arrived from the cloud uses `persistLocally()`, not
  `saveStore()`.** `saveStore()` pushes back up and two synced devices
  ping-pong forever.
- **Any new persisted field on `store` needs an explicit default in
  `applyLoadedData()`** — defaulted so *existing* users don't see it as new
  (e.g. a `seenXTour` flag defaults to already-seen for anyone past
  onboarding).
- **Don't reorder or rename questions' `topic`/`src`.** Question identity is a
  hash of those fields (`KEYS` via `hashOf()`), so changing them scrambles a
  real person's answer history for that question.

---

## iOS install-time metadata — the thing that cost a whole session

iOS reads three things **once**, when the app is added to the Home Screen, and
never again: **the icon, the app name, and the launch status bar colour.** No
reload, no cache clear, and no amount of JavaScript can change them afterwards.
Only removing the icon and re-adding it can.

This is why a flat grey strip at the top of the screen survived several
correct-looking fixes aimed at page layers (`background-attachment`, a
`position:fixed ::before`, a matching gradient on `html`). The status bar never
consults any of them. It was `theme-color`, read at launch.

Consequences worth keeping in mind:

- **Two places declare `theme-color` and they must stay in step:** the
  `<meta id="themecolor">` tag and `theme_color` inside the base64 manifest.
  iOS 16.4+ reads the manifest for an installed app and can prefer it, so a
  stale value there reinstates the bug on exactly the devices the meta fix
  appeared to solve it for. Both are `#271E23`.
- **`background_color` in the manifest does NOT colour the iOS launch
  screen.** This file used to say it was "the launch backdrop"; that is
  wrong, and believing it cost two failed attempts at the white flash. iOS
  ignores it entirely for a home-screen app and paints the launch screen
  **white** unless given an `apple-touch-startup-image` matching the device
  exactly. `background_color` still matters to Android/Chrome, which is why
  it stays `#12161B`.
- **The white flash on launch is that white launch screen**, not anything
  the page does. It cannot be fixed from CSS, because it happens before the
  page exists. The cure is a flat `#0A0A0A` startup image per device per
  orientation, generated by `tools/gen-startup-images.py` into `launch/` and
  a marked block in `<head>`, so the launch screen and `#splashscreen` are
  the same colour and the handover is invisible.
- **Verified end to end, and worth re-running rather than re-reasoning:**
  serve the repo over HTTP, pull every `apple-touch-startup-image` href,
  and check each one returns 200 as `image/png` and is a single flat
  `#0A0A0A`. Current state: 43 link tags, 42 unique files, all clean; the
  iPhone 17 Pro Max's exact 1320×2868 (440×956 at 3x) has both a matching
  file and a matching media query; and the media-less catch-all is the same
  1320×2868 image, so a device iOS fails to match by media query still gets
  black rather than white. That, plus `html{background:#0A0A0A}` inside the
  first ~300 bytes and `#splashscreen` at the same colour, is the whole
  chain — there is no remaining step between the icon being tapped and the
  app's own first paint that can be white.
- **They must be REAL FILES in `launch/`, not `data:` URIs.** The first
  version shipped 42 correct link tags carrying correct PNGs as data URIs
  and the flash did not move. It was not a coverage gap — an iPhone 17 Pro
  Max is 440×956 at 3x, which the existing 16 Pro Max entry matched exactly.
  The links were right and the images were right, so what was left was the
  delivery: iOS needs these images *before* the page it found them in has
  loaded, and every documented implementation references a fetchable path.
  **This is why `index.html` is no longer the whole app.** `launch/` has to
  be deployed with it; if it is missing, the links 404 and iOS falls back to
  white *silently*. `--check` verifies every referenced file is on disk.
- iOS matches on exact pixel dimensions and falls back to white on any
  mismatch, so **a new device needs a new entry in `DEVICES`** — but there
  is also a media-less catch-all entry, last in the block, which is the only
  thing that can cover a device whose size is not known in advance. Both
  orientations use the *portrait* `device-width`/`device-height`, differing
  only by `orientation:` — that is the convention iOS expects, not a bug.
- Startup images are almost certainly read at install time like the icon
  and the app name, so an existing install may need a re-add to pick them
  up. That is what `frameId` is for.
- The status bar colour is computed at runtime from the app's own tokens
  (`syncStatusBarColor()` → `--statusbar-mix2/3` alongside `--bg-glow-r1/r2`),
  cached to `class26e.statusbar.v1`, and replayed before first paint by a
  synchronous inline script in `<head>`. That script must stay synchronous and
  stay in `<head>` — anything deferred loses the race with first paint.
- `getComputedStyle` returns a `color-mix()` result as CSS Color 4
  (`color(srgb 0.15 0.12 0.14)`, 0–1 floats), **not** `rgb(18, 22, 27)`.
  Parsing it with 0–255 assumptions rounds every channel to 0 — a black status
  bar. Both serializations are handled; don't "simplify" that.

---

## The app icon

Drawn by `tools/gen-app-icon.py`, never edited by hand.

**The icon lives in three places and they must never drift apart:** the
`apple-touch-icon` link (the Home Screen app), `<link rel="icon">` (the
browser tab favicon), and the `icons` array inside the base64 manifest
(Android, desktop installs). The script writes all three in one go, and
**`--check` fails if any of them disagree** — that check exists because they
*did* drift: an earlier pass updated the apple-touch-icon and the manifest
and left the favicon still serving the old artwork, so every Safari and
Chrome tab went on showing the icon that had just been replaced, with nothing
anywhere to say so. Run `--check` after touching anything icon-shaped.

- **Full-bleed opaque square. No rounded corners, no transparency.** iOS
  applies its own mask; anything rounded here gets rounded twice. The icon
  this replaced had corners baked in and transparent gaps behind them —
  visible as white notches the moment it was composited on anything light.
- **One idea, legible at 60pt.** The V from NOVA and nothing else. The old
  icon was an illustration — sphere, starburst, orbiting moon, a small N —
  none of which survives the size it is actually used at.
- **The grey is calibrated against a real iOS icon, not chosen from a
  palette.** `GREY_TOP`/`GREY_BOTTOM` are `#323232` → `#141414`. They came
  from photographing Claude's icon next to Nova's on the same Home Screen and
  sampling both tiles down their edges, clear of the glyphs. Claude's reads
  `#2E2E2E` at the top falling to `#171718`, **dead neutral** (R=G=B at every
  point) on a gentle 23-level slope.

  Nova's was wrong in three separate, measurable ways at once: 16 levels too
  light at the top, a slope half again as steep (35 levels), and a consistent
  **+2 blue tint** that made the grey read cool next to Claude's neutral. Two
  levels of blue is invisible in isolation and obvious side by side, which is
  exactly why guessing at "systemGray5" does not work.

  The method is the reusable part: render the icon at the screenshot's tile
  size, sample the same fractions down the same columns, and compare. The
  local render reproduced the screenshot's values exactly, which is what
  makes the comparison trustworthy. Current match: **within 2 levels at every
  point, zero tint.**
- **No overhead highlight on the background.** There used to be a soft
  elliptical pool, and measured against Claude it was adding ~18 levels at
  the top and almost nothing at the bottom — precisely the "too light, too
  steep" above. iOS's dark icons do not have one: the plain top-to-bottom
  gradient *is* the lighting. The glyph's own banded shading carries the
  dimensionality.
- **A lit surface, not a flat fill** — but far less lighting than instinct
  suggests. A hairline along the top edge, and for the smooth variants a
  tight contact shadow and a soft specular on the glyph. The first pass used
  roughly four times the light and read as a gradient wallpaper; the second
  still measured 16 levels too bright against a real iOS icon.
- The V keeps Nova's own ramp (`#FFD37A` → `#F5804D` → `#C23B7A`, the
  wordmark's stops). **The ramp is mapped across the glyph's bounding box and
  weighted towards vertical.** Across the whole canvas, and on an even
  diagonal, a V only ever covers the middle of the ramp — it came out
  uniformly salmon with the gold and magenta both off the edges of the shape.
- **The shipped V is pixel art**, for the game-ish personality the app's
  points/stars/tiers earn. **The sprite is generated from one rule**
  (`build_v_sprite`), not typed out and not traced from the curve — three
  attempts, and only the third looked designed:
  - *Quantising the smooth polygon* gave steps of uneven length, two cells
    here and three there. That is what a low-resolution **render** looks
    like; sprite work has rhythm — the same step, the same run, all the way
    down.
  - *Typing the grid by hand* fixed the rhythm but put the taper off-centre
    by one cell, and the apex came out looking like a drip.
  - *Generating it* guarantees both: one cell across every two rows, and
    every row symmetric about the centre column by construction. There is an
    assertion's worth of truth in `all(line == line[::-1])`.
- **Band the ramp, don't gradient it.** A continuous gradient across the
  cells is the other thing that stops pixel art reading as pixel art; the
  palette is reduced to six steps and the bands are meant to be obvious.
- **Shade by each row's runs, not by each cell's neighbours.** Testing "is
  anything above/below me" lights or darkens nearly every cell on a
  staircase — every step has both — and the glyph came out speckled, busier
  than the version it was replacing. A run has exactly one left edge and one
  right edge, so lighting one and shading the other gives a single light
  direction and leaves the middle of each arm flat.
- **No drop shadow on the pixel glyph.** A one-cell offset drops a dark
  block into every notch of the staircase — correct for a shadow, ruinous to
  look at, because it breaks each arm into a string of beads.
- **A pixel glyph is drawn at the final size, never supersampled and
  reduced.** Reducing is exactly what softens edges, and soft edges are the
  one thing pixel art cannot have. A useful consequence, measured rather than
  assumed: it is *crisper than the smooth V at small sizes* — at 16px the
  smooth one is mush and the pixel one still reads.
- **The cell size is a whole number of pixels and the sprite is centred on
  whole pixels.** Deriving each cell's bounds by rounding instead let them
  come out 6px and 7px wide in the same icon, so the grid was visibly uneven
  — the clearest tell that it was not real sprite work. A little empty margin
  is a fair price for every cell being square.
- Below about 1px per cell the rounding can collapse a cell to negative
  width and `ImageDraw` raises. Boxes are clamped to a single pixel; the
  pixel look is long gone at that size, but it has to render, not crash.

`--preview DIR` renders every variant plus a `_masked` version approximating
what iOS will actually show, so the corners can be looked at rather than
guessed at. The alternatives all still build: `brand` (the smooth V),
`white`, `noir`, `pixel-noir` and `pixel-white`. Switching is one command and
a rebuild. The sprite's own proportions are `V_COLS`, `V_THICK` and
`V_ROWS_PER_STEP` — 3-thick arms read too thin to hold together across the
steps, which is why it is 4.

**The icon is install-time metadata.** Changing it does nothing on a device
that already has the app until that icon is removed and re-added — which is
what `frameId` and the re-add notice exist for. See **Going live**.

---

## Launching: the first frame

Three separate things had to be right before the launch stopped flashing and
sitting crooked. They fail independently, so a fix for one looks like it did
nothing.

- **The white flash was not in the page at all** — see the iOS section above.
  It was the launch screen iOS paints before the page exists, white for want
  of an `apple-touch-startup-image`. Two plausible in-page explanations were
  found, fixed, verified in Chromium, shipped, and changed nothing on the
  device, because a symptom that appears before first paint cannot be caused
  by anything after it. **If a launch symptom survives a fix that measurably
  works, the cause is outside the document; stop editing CSS.**
- The two in-page fixes are still there and still correct, just not the
  cure: `color-scheme: dark` and `html{background:#0A0A0A}` in the first
  `<style>`, both inside the first ~300 bytes, closing the window before any
  rule colours the canvas (nothing else does for ~280 more lines). Keep them
  early — a comment block or a parser-blocking script ahead of them loses
  the race. Testable: truncate the document, force a paint, sample the pixel.
- **Pick the viewport unit deliberately; all three were wrong once.** `dvh` is
  dynamic and grows as the viewport settles, so centred content drifts down.
  `svh` is static but is the screen *minus* overlaid insets, so it comes up
  short by exactly the home-indicator height and leaves a strip of app
  background below the splash. `lvh` is static *and* full-height — that is the
  one. `100vh` is declared first purely as a fallback.
- **Chromium cannot reproduce any of this.** `svh`, `lvh`, `dvh` and `vh` all
  return the same number here and `env(safe-area-inset-*)` is always `0`. To
  test a layout that only misbehaves once the insets are real, serve a copy
  with the `env()` calls text-substituted for real values — see
  `tools/sim-safe-area.py`. It caught a genuine bottom-edge seam that measured
  zero without it.

---

## Every device, every way in

**This is the bar for every change, and it is not negotiable.** Nothing ships
— no fix, no tweak, no audit — until it has been checked across the whole
matrix: every common device, **both orientations**, and **both ways of
running the app**.

```
python3 tools/sweep-layout.py        # the whole matrix, before calling anything done
python3 tools/sweep-layout.py --quick   # one per family, while iterating
```

**Added to the Home Screen and opened in a browser are two different apps.**
An installed app gets the whole display and real safe-area insets — notch,
status bar, home indicator. A browser tab gets a shorter viewport, with
Safari's or Chrome's own bars taking the top and bottom, and essentially no
insets. The same CSS lands differently in each. Checking one is not checking
the other.

The matrix covers iPhones (SE through Pro Max), iPads (mini, 10.2", Air,
Pro 11", Pro 12.9", Pro 13"), Android phones and tablets, and laptops from
a Dell Latitude up through a MacBook Pro 16" and a 1440p display — each
portrait and landscape, each installed and in a browser. Desktops are
browser-only. 21 devices, 70 combinations.

**A GATE'S FIXTURE IS AN EXISTING, UP-TO-DATE ACCOUNT, so it has to
carry `tourRev`.** Without it the one-time tour re-arm fires inside the
gate, puts a tooltip over the screen being measured, and fails a check
that has nothing to do with tours — which is how `check-behaviour`'s
tab-swipe test went red on a build whose swiping was fine. A false
failure caused by a real mechanism, and the argument for every fixture
setting the flag explicitly rather than relying on a default.

**The seed is a USED account, and that is deliberate.** With empty stats
Profile, Rewards, the Leaderboard, the calendar, the review list and test
history all render their *empty* states, so half the app was being checked
as "nothing here yet". The seed carries real points, a streak, nine test
results and three weeks of study log so those screens lay out the content
people actually see. It also carries `onboardingComplete`, without which
the tab bar never appears anywhere (see below).

It reports horizontal page scroll, anything painting outside the viewport,
the primary button colliding with or hidden behind the tab bar, the tab bar
off-screen, controls colliding with the notch or home indicator, and uncaught
JS errors.

**The below-the-fold check used to sit inside the tab-bar branch**, so it
only ran on screens whose tab bar was visible — which is every screen except
onboarding, the exact place a primary button is most likely to fall off the
bottom. It is its own branch now. It also asks the right question: not "is
the button below the fold" (a long screen that scrolls to its button is
working as intended) but "is it below the fold **and** the page cannot
scroll to it", which is the only version of this that is actually a defect.

**It must cover every screen it can mount, not a handful.** It began with 6
of the app's 44 and reported `62/62 clean` while a regression had left
*every onboarding screen* — Welcome, the intro, username entry, character
select — bunched at the top with dead space below. None of them was in the
list. It now runs 25: everything that can be mounted cold.

**`showX()` names overlays as well as screens, so the count is not the
gap it looks like.** There are 45 `showX()` functions and 25 of them are
in `SCREENS`. The other 20 are excluded on purpose and fall into three
groups, checked rather than assumed: **overlays and banners**, which have
no screen of their own (`showToast`, `showNoticeBar`, `showUpdateBanner`,
`showFrameNotice`, `showDailyAlert`, `showTierUpBanner`,
`showPointsFlyEffect`, `showSafariFallback`, `showContextualInfo`,
`showDailyQuestionLockedPopup`, `showPracticeTestConfirm`,
`showCountdown`, `showVroomReadyFlourish`,
`showVirtualRoomFinaleReveal`, `showTierUpStyleBadgeNote`); **screens
needing run state**
(`showBankProblems`, `showAnswerReview`, `showTestHistoryDetail`,
`showVirtualRoomLobby`, `showVirtualRoomResults`); and one that renders
nothing on its own (`showGeneratingProfile`). **Anything else new belongs
in `SCREENS`** — a green sweep is only worth what it looked at, and the
way to check is to diff the app's `^function show` list against `SCREENS`
rather than to trust this paragraph.

**A GATE THAT NAMES A LABEL GOES STALE, AND THEN IT FAILS THE APP FOR
BEING RIGHT.** Three separate checks did this inside two days:
`check-behaviour` asserted the Profile tabs read `["Profile", "Stats",
"Badges", "Ladder"]`, its swipe test asserted the second leaderboard
board is literally `"Badges"`, and `shoot-flow.py` saved that board's
screenshot under the name `badges`. All three went red or wrong the
moment the labels changed — which they did, on request. A check that
encodes a DECISION has to be re-read whenever the decision changes;
better, it should not encode one at all. All three now read the labels
off the page and assert the SHAPE (four tabs in this order, exactly one
step not two, whatever they are called). Keep doing that: the thing
worth asserting is almost never the string.

**A FIXTURE ENCODES A DECISION JUST AS A LABEL DOES, and this trap has
now bitten four times.** After the tab labels, the board name and the
badge threshold, it was `check_ranks`: its seed was *"level 23 (12,400
XP) and 4 badges reaches Veteran"*, its boundary cases called
`rankOfStats(20, 4, 0)`, and a rankings row was built with
`decorateAvatar(a, 34, 6, 0)` and asserted to read **"Gold"**. All three
were true of one curve and one threshold table, and all three went red
the moment the ladder was rescaled — seven failures, none of them a bug.
The section is about "hold Veteran, with Vanguard next" and "a row shows
the rank those numbers earn", so it now **boots once to read
`TIER_UNLOCKS` and `levelProgress()` off the page, builds the seed from
what it finds, and asserts against `RANK_DISPLAY_NAME`**. The rule is
the same one as before, one axis over: assert the SHAPE, and let the app
supply the numbers. If a check has to know a threshold, it should ask.

**A CHECK THAT CANNOT FAIL IS WORSE THAN NO CHECK, because it reads as
coverage.** Two of `check-vroom`'s new results-screen assertions passed
against the broken build on their first draft. "Review your answers
opens a real list" passed because the harness run had missed questions
in it, and that path always built a list — the bug only ever existed on
the CLEAN run, so the fixture now answers every question correctly.
"The race line is down" passed because hiding it on the FIRST render
always worked; what did not was every render after, the hide sitting
past an early return, so the check now puts the bar back and pokes the
document to force another snapshot. **Run every new check against the
build it was written for (`--against`) and make sure it fails.** Green
on both builds means it is measuring nothing.

**A GATE THAT SAMPLES AN ANIMATION AT ONE INSTANT IS A COIN FLIP, and
it fails the build that happened to be 40ms slower.** `check-behaviour`
section 5 waited 1500 + 2600 + 3200 = 7300ms and then asked once
whether the badge queue had drained. Measured, the second cutscene's
overlay is removed at **7293ms on a phone and 7341ms on an iPad** — the
same 2600 + 780 per badge the app has always used — so the phone passed
and the tablet failed on a build whose only changes were a toast offset,
a constant and a level curve. There was nothing wrong with the app, and
nothing wrong with the previous build either; the sum simply landed
inside the app's own total. **Poll for the condition with a stated
budget, and report the figure it actually took.** The rewrite polls to
6000ms against a real ~3180 and prints `ms`, so a genuine slowdown is
visible long before it is red. That is not softening the check: a queue
that stalls never drains at all, so it still fails outright — verified
by pulling the recursion out of the cutscene's own cleanup and watching
both devices go red. Same trap as the stale label, one axis over: what
is worth asserting is the SHAPE (it drains, within a budget), never the
arithmetic.

**And a harness must not invent the bug it is checking for.** The first
version of the answer-review scroll check reported that the page would
not scroll, because it called `window.scrollTo` and measured 450ms
later — and smooth scrolling is on by default, so a 14,000px scroll was
still travelling. `behavior:"instant"` is deliberate there.

**The sweep is an AUDIT, not a look.** It answers "is anything broken on
this device" — overflow, collisions, insets, JS errors. It does not answer
"did the thing I just positioned land where I meant it to", and a green
sweep says nothing about that. Both questions need asking on the whole
matrix. Asked properly the second time round, after a session whose
screenshots had only ever been taken at 440×956 and 834×1194, it found
three real defects a 66/66 sweep had sailed past: Start Studying 70–75px
off-centre on an iPad Pro 12.9"/13" (the fix for it was inside a phone
media query), the Welcome hint 20px below the fold on an SE 2nd/3rd gen,
and "What This Actually Is" overflowing its viewport on *every* short
device in the matrix — which in turn put its Continue button 184px away
from where every other onboarding screen puts it, while measuring 0px
apart on a Pro Max. `tools/check-positions.py` is that check: measure the specific decisions, on every device, and flag the
outliers rather than eyeballing two.

### Why this matrix and not a smaller one

Every bug below was invisible at 390×844 in a desktop browser, which is where
"looks fine" usually comes from:

- **A `padding` shorthand on `.wrap` under 32rem wiped out all four
  `env(safe-area-inset-*)` longhands** — so *every phone* lost its insets. On
  a notched iPhone the screen title sat at y=20 under a 59px status bar,
  behind the clock. **Never set `padding` shorthand on `.wrap`; use
  longhands**, or the insets go silently.
- **Do NOT add `env(safe-area-inset-bottom)` to the space reserved for the
  tab bar.** An earlier pass did, reasoning that the bar grows by the inset
  so the reservation must too. Measured, that is double-counting: the bar's
  whole footprint on an iPhone 15 is its offset (`0.6rem`) plus its 101px
  height — under 7rem *with* the home indicator already inside it — so the
  flat `7.5rem` covers it, and the addition opened a second gap of the same
  size under the button.
- **`min-height:calc(100dvh - Nrem)` must subtract only the EXTRA the insets
  add, not the insets themselves** — `var(--pad-inset-top)` /
  `var(--pad-inset-bottom)`, which are `max(0px, inset - baseline)`.
  Subtracting the raw insets double-counts the baseline the rem figure
  already contains: it took **~93px off every panel** on a notched iPhone
  and left every screen in the app bunched at the top with dead space under
  it. Each formula must collapse back to its original value at zero insets —
  that property is what makes a change here safe to reason about.
- The laptop collision: Home did not fit a 768px laptop screen (~640px of
  page in Chrome) and hid the primary action behind the tab bar.
- The tab bar was a fixed 344px wide, off both edges of a 320px phone; the
  Rewards tab switcher overflowed sideways below 384px.

**A `document`-LEVEL `preventDefault` EATS EVERY NATIVE DRAG IN THE
APP.** Moving the swipe listeners to `document` (build 111) fixed the
dead strip at the top of a question and silently broke both sliders:
the touchmove handler calls `preventDefault()` once a drag looks
horizontal, and on every other screen that cancelled the native drag of
`<input type=range>`. Reported as *"the length and countdown adjustable
thing does not seem to be working with my finger."*
**The control experiment is what proved it**: a bare range input in the
same browser follows a synthetic touch drag to its maximum, so the
harness was fine and the app was eating the gesture. Run that before
blaming the harness.
`swipeGestureAllowed()` now guards both `touchstart` and `touchmove`:
a question with its `.choices` must be on screen, and the touch must
not have started on `input, textarea, select, [contenteditable]` —
anything that owns its own drag.
Sliders also carry **`touch-action:none`** (a control whose job is to
consume the drag on both axes, and which can never be the thing you
scroll by) and a **28px thumb in a 44px track**; the browser default
was ~12px in 24px, well under the 44px minimum this file sets, which
is most of why it "barely works with the cursor" either.

**A RANGE INPUT'S `max` MUST LAND ON ITS STEP LATTICE, or the last
stretch of track is dead.** Steps are measured from `min`, so with 894
questions, min 5 and step 5 the highest reachable stop is 890 — but
`max` was 894, so the thumb stopped short of the end and four
questions' worth of track had nothing on it. *"If I scroll all the way
to the right it should be max questions ... there shouldn't be
available space there, it needs to matchup perfectly."* `topStopFor()`
sets `max` to the top lattice stop and `effectiveFrom()` turns that
stop into the real pool size, so the far right is both reachable and
means *all of them*. Verified by dragging: thumb at `max`, display
"894 questions", `cfg.size` 894 of a 894 pool. The countdown slider
(5–90 step 5) is already exact and needed nothing.

**THE SWIPE LISTENS ON `document`, NOT `#stage`, AND THAT MATTERS.**
`#stage` is only the panel, so the strip along the TOP of a question —
the progress dots and the unit line — is outside it, and a swipe
started there reached no listener at all. Measured on both reference
devices: question text, a choice, the Next button and empty panel
space all advanced; the top bar did not. Reported as the swipe working
on the button but "not by swiping on the screen". `SWIPE_SURFACE` is
`document`; every guard still applies, and the one that matters is
that a question with its `.choices` must be on screen, so it cannot
fire anywhere else in the app. `body.has-active-question .wrap` carries
`touch-action:pan-y` for the same reason the panel does.

**THE MODE ICON AT THE TOP OF UNIT SELECTION IS PER-MODE COLOURED, and
the fix has to sit below the modern-layout block.** `[data-layout=
"modern"] .modedisplay-top .modeiconpath{stroke:var(--accent)}` paints
it in `--accent`, which on the default theme is `--ink` — so Drill and
Exam came out near-white while Game was magenta, because Game is the
one mode whose per-mode rule sets `fill` rather than `stroke` and so
was never overridden. Measured before: drill and exam both
`rgb(231,237,241)`, game `rgb(194,59,122)`.
**The first attempt put the override 4,400 lines higher at one class
MORE specificity and still lost** — the modern rule is an attribute
plus two classes, the same 0,3,0, and later in the file. Same trap as
`.panel` padding: an override of anything in the modern-layout block
needs the `[data-layout="modern"]` prefix AND has to come after it.
Now drill `--theme-c1`, exam `--theme-c2`, game `--theme-c3`, vroom
`#4A9FE8` — the same colours the Mode Select cards use.

**`button{touch-action:manipulation}` IS WHY SWIPE-TO-ADVANCE DID NOT
WORK ON A PHONE, and why it always passed in Chromium.** `body` is
`touch-action:pan-y`, which hands the HORIZONTAL axis to the app so the
swipe can claim it — but every answer choice is a `<button>`, and the
global button rule resets them to `manipulation`, giving both axes back
to the browser. The choices fill most of the question screen, so a real
thumb swipe almost always starts on one: iOS took the gesture before
`touchmove` could `preventDefault`, and the page moved instead of the
question. **Chromium honours a JS `preventDefault` far more readily
than iOS**, so the harness advanced the question every time while the
device did nothing — three fixes were shipped at this symptom before
the cause was found. `touch-action` is DECLARATIVE: it settles who owns
the axis before the first `touchmove` fires instead of racing for it.
The question panel, its buttons and `#nextbtn` are `pan-y` while
`body.has-active-question` is set.

**THE FIRESTORE RULES DENY WRITES TO `leaderboard`, AND THE APP
SWALLOWS IT.** Tested directly over the REST API: `progress` write
**200**, `vrooms` write **200**, `leaderboard` write **403**. Reads and
lists are allowed, which is why the board renders and is simply empty.
`pushToCloud()` ends its `.set()` in `.catch(() => {})`, so every
rejected write is silent — the collection held 0 documents while
everyone's own progress synced perfectly. **No change to `index.html`
can fix this**; the rules have to be edited in the Firebase console.
Before debugging an empty board again, run the write test rather than
reading the client code.

**THE RESULTS SCREEN IS THREE MATCHED CARDS AND A MATCHED BUTTON
ROW.** It used to go card, card, loose paragraph, two mismatched
pills. The review block was the only one of the three without a
surface, and its hierarchy was inverted — heading in `.qnum` (small,
grey, the label style) over body in `.qtext` (the QUESTION text style,
large and bold). `.results-review` joins `.points-breakdown` /
`.results-level` in the shared surface rules, with the title bold and
the body soft. `.actions.actions-results` makes both buttons equal
width; they measured 176 vs 137 before.
**Verify this screen on a REAL finished run.** `shoot-results.py`
builds it its own way and showed no change at all while the DOM from
an actual drill already had the card and the matched row.

**NO TEXT FIELD MAY COMPUTE TO UNDER 16px.** iOS Safari zooms the whole
page in when it focuses one that does, and does not reliably zoom back
out — the page is left magnified with no way to pinch out of it.
Reported from a device against the username screen. Measured, EVERY
text field in the app was `.95rem` (15.2px) and the chat input `.85rem`
(13.6px); a rule setting onboarding fields to `1.1rem` exists but does
not reach that screen. They are `max(16px, 1rem)` now, with a
low-specificity net over every typed `input`/`textarea`/`select` so a
field added later inherits the floor without anyone having to know the
rule. **Chromium never does this**, so the number is the only thing that
can catch a regression — `check-fixes.py` measures it on every device in
the matrix.

**Short-viewport tiers must be short AND wide** — `(max-height:Nrem) and
(min-width:34rem)`. Height-only was the first instinct, on the reasoning that
the problem is purely vertical, and it was wrong: it also fires on a phone
held *upright*. An iPhone SE is 667px tall and was fitting comfortably, and
the tier shrank its hero from 295px to 227px and its title with it, for no
reason. The `34rem` floor keeps the tiers to what they were written for —
laptop windows and phones on their side. Home has three: 50rem, 36rem, 26rem.

**A full-bleed bar pinned to the bottom edge is supposed to reach the edge.**
It clears the home indicator with *padding*, not by stopping short — so
inset checks measure the CONTENT box, never the border box. `.floatbtn` does
need `padding-left`/`padding-right` insets though: full-bleed puts its label
under the notch on a phone held sideways.

**A TOAST HAS TO CLEAR THE BAR *PLUS ITS OWN HEIGHT*, AND THAT NUMBER IS
MEASURED, NOT DERIVED.** `body.has-bottomtabs .toast` sat at
`calc(6rem + env(safe-area-inset-bottom))`, which is less than the bar's
own footprint: measured on an iPad Pro 11" the toast's bottom edge was at
1078 against a bar starting at 1063 — a 15px overlap — and on a 17 Pro
Max it cleared by 5px, which is touching, not clearing. Reported as
*"the select units to start pop up hides under the bottom tab"*. The
obvious fix is `7.5rem`, the figure this file already uses for the bar's
whole footprint, and it is wrong for the same reason 6rem was: the toast
is anchored by its *bottom*, so it has its own height to get out of the
way as well. `8rem` was tried and still overlapped the iPad by **3px**.
`9.5rem` is what actually measures clean — 27px of gap on a 17 Pro Max,
21px on an iPad Pro 11". **Deliberately without the safe-area inset**:
the bar's height already contains it, and adding it again is exactly the
double-count recorded above for the tab bar's own reservation.

**Clear the home indicator by MOVING a fixed element, not by padding it.**
`.bottomtabs` used `padding-bottom:max(.4rem, env(...))`, which grew the pill
downward by the whole inset — 34px of empty glass under the icons on an
iPhone, leaving them sitting high in a bar that looked wrong. An iPad's 20px
inset made the same mistake less obvious, which is why that one "looked
perfect" by comparison. `bottom:calc(.6rem + env(...))` keeps the pill the
shape it was designed to be on every device, and the total space it occupies
is unchanged. The offset itself is how low the bar sits — it was `1.1rem`
until it was reported as sitting too high; at `0.6rem` the pill clears the
home indicator's inset by 10px on both an iPhone and an iPad. Only ever
lower it toward the edge, never past it: the `7.5rem` reservation above
assumes the bar's whole footprint still fits inside it.

**A laptop is not a tall tablet either, and gating the enlargement on
height alone missed them all.** The `(min-width:40rem) and
(min-height:60rem)` block that scales Home's sphere and type up for a
tablet needs 960px of height — which an iPad in portrait clears and a
laptop browser window does not. A MacBook Pro 14" leaves 852px once
Chrome's chrome is gone, so it was falling all the way through to the
*phone* sizing: measured, a 368px sphere and a 15.2px tagline centred in a
1512px viewport. The fix is a second condition, `(min-width:64rem) and
(min-height:46rem)`: width is the safe way in, because the thing the
height gate protects is a short iPad in landscape, and those are 834px
tall at 40–52rem *wide*. Requiring 64rem of width excludes every one of
them and takes in every laptop.

**A tablet is not a big phone.** The hero sphere carries these screens and it
is the one element that can absorb a tablet's height — but **size it in `vh`,
not a flat `rem` cap.** `min(36rem, 56vh)` fits an 834×1194 iPad beautifully
and pushed Start Studying behind the tab bar on a 768×1024 one and on every
iPad in landscape. `min(36rem, 48vh)` serves both. The same applies to the
margins around it: fixed `rem` gaps that look right at 1194 are what tip a
1024-tall iPad over, so they are `min(2.4rem, 3vh)` and so on.

**The sign-up picker is FOUR across, and that is a different screen
from the one the six-column rule was written for.** Six was right while
it showed all twelve characters — two even rows. The locked four came
off it (they are hidden at sign-up now), and eight items in six columns
is a row of six and a ragged row of two, reported as uneven. Four is two
even rows again. **The room that frees went into the rows, not into the
characters**: `max-width` stays at `3.7rem` on a phone and `6rem` from
tablet up, because both numbers were arrived at from device reports —
`7rem` came back as "absolutely massive" and the phone size was signed
off as it stands. The grid is a flex child of an `align-items:center`
panel, so it sizes to its own content and that `max-width` is what
decides how wide it sits; raising it is safe for overflow (fit-content
clamps to the panel, which is why a 320px phone already renders 54.6px
tracks against a 59.2px ceiling) but it is a LOOK change, not a bug fix,
so it wants asking about rather than assuming.

**A GRID'S COLUMN COUNT IS A HEIGHT DECISION.** The character picker was
four across, which is two even rows of eight. Adding the four rank
characters made it twelve — three rows — and that added ~75px to a
screen that already scrolls on a small phone. Measured, it pushed the
level card's own top ABOVE the viewport on an SE 2nd/3rd gen and an
Android phone: content that cannot be scrolled up to. Six across is two
even rows again and the panel came back to 833px, shorter than the 864
it was before the characters existed. Six on a tablet too — eight
columns with twelve items is a row of eight and a ragged row of four,
which reads as a mistake. The grid still spans the swatches' full width,
which is what "as wide as the colors below it" actually asked for.

**`.panel.home` is `align-items:center`, so a flex child sizes to its own
content.** The fourth "What This Actually Is" card has the shortest text and
came out visibly narrower than the other three on an iPad; on a phone all
four wrap to full width, so it never showed there. Anything meant to be a
full-width row in that column needs `width:100%` explicitly.

**Welcome's layout is auto margins at every width now, not just on a
phone.** The tablets kept `justify-content:center`, which floated the
whole five-item column in the middle of a 1194px iPad with slack both
above the sphere and under the hint — "the stuff underneath the planet
system needs to be moved down or spaced out". `flex-start` plus
`margin-top:auto` on the hero and on the actions block puts the leftover
height where it reads as layout and lands the actions on the panel floor
on every device.

**Welcome also carries its own `--panel-reserve`, because it has no
bottom furniture.** It has no tab bar and no floating button, so the
shared `4rem` of `.wrap` bottom padding is reserved for things that are
not there — and that alone was holding the hint 82px off the bottom edge
everywhere. `body.on-welcome` (toggled in `syncVisibility()`, the same
self-clearing hook as `has-bottomtabs`) drops it to `2.25rem`, which
brings the hint to ~50px and 62px on a device with a home indicator.
**All three values move together**: `--panel-reserve` is `.wrap`'s top
padding plus its bottom padding, and `--pad-inset-bottom` is whatever the
inset adds *over that new bottom baseline*. Change one and the panels
mis-size — this is the same arithmetic that once cost every panel ~93px.

**Two `auto` margins centre an item in the leftover space.** That is the
right tool when a button should sit *between* the content and the bottom of
the panel rather than tucked under the content or jammed at the floor.

**A bottom margin on the last item is a self-cancelling gap, and it is the
only way to say "centre it when there is no room, floor it when there is".**
CSS has no `margin-top: max(2.5rem, auto)`. But a margin on the LAST CARD
is absorbed by the button's `margin-top:auto` wherever slack exists (a 13
mini has 113px of it — nothing moves) and, where there is none, grows the
panel past its `min-height` and carries the button down into the reserve
below it instead. On an SE 2nd/3rd gen that turned 3px above / 87px below
into 45/45 while every roomier device stayed byte-identical. It costs **34px**
of scroll on the SE (27px before the intro cards' gaps were raised; three
gaps at +2.4px each is the whole difference) — and measured rather than
assumed, **that scroll is slack below the button, not the button**: on an
SE 2nd/3rd gen Continue's bottom edge sits at 629 in a 667px viewport, 38px
above the fold and visible without scrolling anything. So the trade is
cheaper than it reads. Guard it with a `min-height` so it does not land on
a device that is already overflowing badly.

**A screen that overflows its viewport cannot honour a shared button
position, so making it fit IS the fix.** "What This Actually Is" is the
one onboarding screen with enough content to overflow, and wherever it
did, its Continue landed after the content instead of on the panel floor.
Two height tiers bring it back inside: `(max-height:52rem)` — height-only
on purpose, because here the upright phone *is* the case the rule exists
for — and a narrower `(max-width:32rem) and (max-height:44rem)` that also
trims the panel's side padding, since every pixel of column width is text
that does not have to wrap and a wrapped line costs ~17px four times over.
The body type stays at `.8rem` throughout: it was raised from that size
once already on an explicit report that it was too small to read, and
buying 20px back by undoing that is a bad trade.
An iPhone SE **1st gen** (320×568) still scrolls this screen and is not
expected to stop — four cards of real text do not fit a 4-inch display,
and hiding a card would be worse than a scroll.

**Every onboarding Continue button sits on its panel's content floor, and
that is the point.** Two separate attempts to give "What This Actually Is"
a position of its own (auto on both sides, then auto plus a fixed
`2.25rem`) both came back as *"slightly higher than the other continue
buttons"* — 29px on a phone, 120px on an iPad. There is nothing to tune
here: the answer is the shared floor, plus the same `padding-bottom:1.5rem`
every other `.panel.home` screen uses, or the floors themselves differ.

**The gap BETWEEN the intro cards has to beat the padding INSIDE them, or the
four of them read as one slab.** Reported as "awkward sized gaps" on an iPad,
and it was: measured, each card carried 35px of padding and only 27px of
margin below it, so the air inside each box outweighed the air separating
them. Phones never showed it — there they were 15/15 — which is why it
survived several passes. Each tier sets both numbers together
(tablet `margin-bottom:2.4rem` / `padding:1.8rem 2rem`, and so on down), and
the table in **Where things currently land** records the pair per device so
the relationship can be checked rather than eyeballed. The last card's margin
is cancelled by the shared-floor rule above, so raising it costs nothing at
the bottom of the panel.

**An auto margin only ever moves the things ABOVE it.** All the free space
in a column ends up above the last child no matter how many auto margins
divide it, so where the *other* children land is the only thing the split
decides. Welcome's phone layout wants the buttons low and the sphere where
it is, so the hero and the actions block take the two autos and the title
takes a fixed `1.6rem`. A third auto on the title instead divided the space
evenly and opened a 100px hole under the sphere — which measured correct and
looked like a gap in the screen. Fixed gaps are spacing; auto gaps are
leftovers.

**An `auto` margin in the main axis beats `justify-content` outright.** Free
space is handed to auto margins first and `justify-content` only ever sees
what is left, which is nothing. So `justify-content:center` plus
`margin-bottom:auto` on the last child is not "centred, a bit lower" — it is
the whole group jammed against the top. Home's phone rule
(`.panel.home.screen-home-actual .playbtn{margin-bottom:auto}`) has to be
explicitly reset to `0` inside the tablet block for exactly this reason.

**A `position:fixed` control holds no space, so the layout has to reserve
it by hand.** Home's daily-question circle and its version label are both
fixed off the bottom edge; Home's primary button was centred between the
tagline and the **tab bar**, which starts 54px *below* where the circle
starts. Measured, the two collided outright: Start Studying overlapped the
"?" by 8×44px on an SE 2nd/3rd gen and 8×9px on a 13 mini, and cleared it
by **one pixel** on a 14/15/16. Every phone was within a rounding error of
the same bug and the ones that looked fine were lucky, not right. The fix
reserves the row rather than nudging the circle —
`[data-layout="modern"] .panel.home.screen-home-actual{padding-bottom:5rem}`
on `(max-width:32rem)` — so the two auto margins go on centring the button
exactly as asked, just between the tagline and the furniture genuinely
below it. Padding is inside the border box, so the panel's `min-height` is
untouched and nothing that fit before starts scrolling. A tablet needs
none of this: its circle and label sit in the corners beside the centred
tab pill, 118px clear of the button.

**Where Home already overflows, padding below the button cannot move it** —
the button is at the end of the content, not on the panel floor, so the
height has to come from something real. The hero is the only element with
300px to spare, and `(max-width:32rem) and (min-height:36rem) and
(max-height:48rem)` trims it to `min(23rem, 34vh)`. Short AND **narrow**,
which is the opposite gate from the laptop tiers (short and *wide*) and
must not catch their devices. Both ends matter: without the `48rem`
ceiling a 13 mini at 812px loses a hero it has the room for, and without
the `36rem` floor this four-class selector reaches down and *undoes* the
`max-height:36rem` tier — an SE 1st gen's hero went from 148px back up to
210px on the first pass. The band that actually needed it, swept across
every phone height from 540 to 980px, is 736–800: a 14/15/16 in a
**browser tab** is 393×742 once Safari's chrome is gone, and that is where
the button landed level with the circle with 3px of horizontal gap between
them.

**`tools/check-fixes.py` now measures that row, and `check-positions.py`
measures the button against it** rather than against the tab bar — the
"centred" number that hid the collision was correct arithmetic about the
wrong floor. `check-fixes.py` takes `--only` like the sweep does.

**The same rule used deliberately is how four screens share one button
position.** `::before{content:"";margin-top:auto}` on the panel plus
`margin-top:auto` on the button gives two auto margins with the content
between them: the group floats mid-screen and the button lands on the panel
floor — the *same* floor on every screen using it, whatever its content
height. That is what puts Continue in one spot across username, character
select, Pick your class, the code screens and "You're all set", which
centring each screen separately cannot do (it left a 125px spread on an
iPad).

**"What This Actually Is" is on that rule too now, and the exception that
kept it off was a measurement with a shelf life.** It had the button half
(`margin-top:auto`) but not the `::before` spacer, on the reasoning that
four full-height cards plus a title left no spare height to float into —
correct when it was written. The cards then lost height in the gap fix
(padding down to `1.8rem` so the gap between them could beat the padding
inside them), and with only one auto margin the whole screen sat at the
top: **280px of dead space above Continue on an iPad Pro 11", 452px on a
12.9"**, reported as the one screen that stood out. With both autos it
floats like its neighbours (280 → 159, 452 → 245) and **Continue does not
move by a pixel** on any device, which is the property to check after
touching any of these screens. Where a screen genuinely has no slack —
every phone, the shortest laptops — an auto margin distributes nothing, so
adding one cannot strand anything. **The lesson is the shelf life, not the
rule**: an exception justified by a measurement needs re-measuring
whenever the thing it measured changes.

**`justify-content:space-between` spreads the leftover height into EVERY
gap, including ones that belong together.** Welcome's two buttons are styled
11px apart and measured 41px apart on an iPhone because each of the five gaps
in that column got an equal share. Grouping the pair (and the line explaining
them) into `.cosmic-welcome-actions`, one flex child, is the fix — the free space then lands *between*
blocks rather than inside one. Welcome is now plain `justify-content:center`
on a phone as well; space-between made the remaining three gaps ~50px each,
which read as three holes rather than a filled screen.

**Anything appended to `<body>` must clear itself on navigation.**
`.daily-alert` is `position:fixed`, so it cannot live inside `#stage` —
`#stage` animates, and a transform on an ancestor re-parents a fixed
element's containing block, which is the documented cause of the daily
button's own old positioning glitch. So it goes on `<body>` and takes a
one-shot `MutationObserver` on `#stage` that removes it on the next screen
change. It also has to be created *after* its own screen mounts: announcing
from inside `showHome()` before `stage.replaceChildren()` had the mount
immediately remove it, which a `setTimeout(…, 0)` fixes.

**A control hidden with `[hidden]` stops holding the layout up.** Three
onboarding screens gate Continue until something is chosen, and
`display:none` takes its `margin-top:auto` with it — so on a tablet the
panel's `::before` spacer was left as the only auto margin and swallowed
every spare pixel, sinking the whole screen to the bottom. Reported as
"all the stuff got pushed to the bottom" on Pick your class, Enter a
username and Choose a character, with "You're all set" (button never
hidden) looking right beside them. `visibility:hidden` is the tool: the
box and its auto margin stay, it is still out of the accessibility tree
so nothing announces a button that does nothing, and the layout does not
jump when the button arrives.

**Nothing may sit on top of a loading screen — and z-index alone does not
enforce it.** `#genprofile-overlay` was `z-index:200`, tied with
`.bottomtabs`, so the tab bar painted alongside a full-screen loading
state and stayed tappable *through* it; tapping Settings there started
the Settings tour on top of "GENERATING PROFILE". The overlay is 400 now
(above the tour overlay at 205 and its tooltip at 210), and
`startSimpleTour()` refuses to start while `#genprofile-overlay` or
`#splashscreen` exists. It **waits** rather than abandoning, because
every caller sets its own `seenXTour` flag to true *before* calling, so a
tour dropped there is one that person never sees; it gives up only if the
screen it was called for has been replaced, or after
`TOUR_OVERLAY_WAIT_MS`.

**A screen mount blurs a still-focused text field, and that
`MutationObserver` on `#stage` is load-bearing.** Focusing a field on iOS
scrolls the page to keep it above the keyboard; replacing that field's
screen while it still has focus dismisses the keyboard **without ever
undoing the scroll**, so the page is left pushed up — and because most of
this app's chrome is `position:fixed`, everything reads as shifted with
nothing to put it back. That was "the character screen comes up
off-centre and stays that way". The observer blurs the field and returns
to the top, and it is **deliberately conditional**: ordinary navigation
must not have its scroll position reset out from under it, so it only
fires in the one situation that causes the problem. Chromium has no soft
keyboard and no visual viewport offset to leave behind, so this cannot be
reproduced or regression-tested locally — don't "simplify" it because
nothing appears to depend on it.

**Dead code that appends to `<body>` is worse than dead.** `showTourSendoff()`
— the old "You're all set" popup — had not been called in a long time (the
send-off is the last step of `startMainMenuTour()` now), but it attached its
overlay to `<body>` rather than `#stage`, so nothing cleared it on a screen
change. Anything that called it, including a harness mounting every screen by
name, left it stuck over whatever came next. Deleted.

**A fixed element's offset from the bottom must carry the safe-area
inset if the thing it clears does.** `.homeversion`'s `6.2rem` offset did
not, while the tab bar's own height does — so the version label sat at
727..753 against a bar starting at 733, hidden behind it on precisely the
notched devices where anyone goes looking for a version number. It carries
the inset now. It also reads `v6.0` on a phone and `Version 6.0` from
tablet up, as **two spans picked by CSS** rather than a string chosen once
at render: the right answer changes when a device is rotated, and a
JS-chosen string does not.

**The sync code field is centred, mono and narrow, and all four parts
matter.** Reported as the x's not lining up with the box. A code is a
fixed-length string of characters, not prose, so it is
`text-align:center` + `var(--mono)` + `letter-spacing:.14em` inside an
`11rem` wrap — the narrow wrap is what makes centring read as deliberate
rather than as text stranded in a wide field, and the mono face is what
stops the characters drifting relative to each other. Widening the field
undoes the fix even with the centring left in.

**Tap targets: 44px minimum, and check them.** A sweep of every button
found the Settings controls running at 12.5–13.1px text in 40px boxes while
the primary button was 16.8px in 48px — `.cal-profile-btn`, `.more-toggle`,
`.restart` (22px tall) and `.daily-question-fab` (41.6px) were all under it.
Secondary does not mean small. Where a text link has to stay a text link,
give it padding and pull the padding back out with a negative margin, so the
target grows without disturbing the layout.

**A phone-only refinement needs a height floor as well as a width ceiling.**
Widening Home's column and opening up its text block is affordable at 852px
and pushes Start Studying behind the tab bar at 667px. `(max-width:32rem)`
alone is not "phones like mine", it is *every* phone, including an SE and
every phone in a browser tab. Pair it with `(min-height:46rem)`.

**`[data-layout="modern"] .panel{padding:1.5rem 1.25rem}` sits ~900 lines
below the phone rules and wins on source order.** Any phone override of
panel padding needs the `[data-layout="modern"]` prefix or it silently does
nothing — the same trap as `.opt .box`, `.next`'s box-shadow and
`.bottomtab-label`. The symptom is subtle: everything else in the block
applies and only the padding is ignored.

**A fix that stops overflow by squashing is not a fix.** The first attempt at
the Rewards switcher let the flex items shrink below their own `nowrap` text:
the page stopped scrolling sideways and the three labels overlapped instead.
**Look at a screenshot, not just the numbers.**

**WRAPPING IS DECIDED ON AN ITEM'S BASE SIZE, NOT ITS SHRUNK SIZE.** A
`flex:1 1 auto` item whose content is wider than the line takes the whole
line to itself and pushes everything after it onto the next one — `min-width:0`
does not save it, because that only lets it shrink once it is already on a
line. The test-review row's chevron was left stranded on a line of its own,
on the one row long enough to wrap, and only on a phone. `flex:1 1 0` is the
fix: a zero base always fits, so the item shares its line and then grows into
whatever is left.

**A `white-space:pre` separator makes a line unwrappable, because its spaces
are the only break opportunities there are.** The test-review meta line is
three `nowrap` bits with " · " between them; protecting those spaces with
`pre` — which looks like the careful thing to do — left a 284px line inside a
240px row on a 320px phone, exactly as wide as the single `nowrap` string it
replaced. Only the bits get `nowrap`; the separators stay default.

**A GATE'S FIXTURE DECIDES WHAT THE GATE CAN SEE, AND SHORT STRINGS SEE
NOTHING.** `showTestReviewList` is in `SCREENS` and the SE 1st gen is in
`DEVICES`, and the sweep still reported 70/70 clean while that screen ran
44–52px past the panel and scrolled the page sideways on it. The seeded test
history has no elapsed times in it, so the meta line the gate measured was
much shorter than the one a real account produces. When a screen's width
depends on its content, the seed has to carry content of a realistic length —
the same lesson as the used-account seed, one level further in.

**Mounting an onboarding screen is not the same as reaching one, and the
difference moves the layout.** `showWelcome()` hides the nav buttons the
bottom tab bar derives its visibility from; every onboarding screen is
reached through it. Calling `showWelcomeIntro()` cold against a seeded
(finished) account skips that, so the bar stays up — which puts a tab bar
into screenshots of screens that never have one (reported twice as "a
massive bug", and it is not one: walked for real, both the create-account
and the sign-in-with-a-code paths report the bar `hidden` with height 0 on
every screen) **and** swaps `--panel-reserve` from 5.5rem to 9rem, which
moves every button on the screen by 3.5rem. Both `sweep-layout.py` and
`check-positions.py` now call `showWelcome()` first for anything in their
`ONBOARDING_SCREENS` set, and `tools/shoot-flow.py` is the
pattern for screenshots: click through from a fresh `localStorage` rather
than mounting anything.

**The bar is also now structurally impossible during onboarding**, not
merely absent: `syncVisibility()` requires `store.onboardingComplete`, the
same flag that decides at boot whether the app shows onboarding at all, so
the two cannot disagree. A harness that seeds a finished account has to
seed that flag too, or the bar will never appear anywhere.

**Diff a new tier against the one that is actually winning, not against
the base.** A laptop tier added at `(min-width:40rem) and
(max-height:44rem)` used values chosen as reductions from the *tablet*
block — but a short-viewport tier was already overriding that block, and
the new values were larger than its. Being later in source they won, and
the two shortest laptops came out bigger instead of tighter: a Dell
Latitude went from 49px above its button to 35 and picked up 23px of
overflow. The computed value is the only thing worth comparing against.

**Chromium cannot see any of this by itself.** It reports every
`env(safe-area-inset-*)` as `0` and has no display-mode emulation, so the
sweep simulates both — insets by substituting real values into the served
copy, standalone by patching `navigator.standalone` and the display-mode
media query. The inset figures and browser-chrome heights in `DEVICES` and
`CHROME_H` are *modelled, not measured from hardware*; correct them there if
a real device disagrees, rather than guessing again.

**Internet Explorer is not supported and cannot be.** The app is built on CSS
custom properties, `color-mix()`, `clamp()`, viewport units and modern DOM
APIs (`replaceChildren`, `IntersectionObserver`), none of which IE has.
Modern Edge is Chromium and is fine. Worth ruling out if someone reports "it
doesn't work", but there is no fix short of a rewrite.

---

## Accounts and the sync code

**The sync code IS the account.** Both Firestore collections are keyed by
it as the document id, there is no sign-in of any kind, and anybody holding
a code can link a device and read or overwrite that person's progress.
Everything below follows from that.

- **A FRIEND CODE IS NOT THE SYNC CODE, AND THAT IS A DECISION, NOT AN
  IMPLEMENTATION DETAIL.** Asked and answered directly: *"The friend
  code, this would need to be a different code then the sync code btw.
  That'd be how it's done."* It has to be, and the reason is the first
  line of this section: the sync code IS the account. There is no
  password behind it, so a friend code that doubled as the sync code
  would mean handing somebody your friend code hands them your progress,
  your rankings row and the ability to overwrite both. A friends feature
  whose whole point is passing a code around cannot be built on the one
  string that must never be passed around.
  So friends gets its own identifier, minted separately, stored
  separately, and safe to hand out - it grants "can send you a request",
  nothing more. Rules that follow from that and should not be quietly
  traded away later: a friend code must never be derivable from the sync
  code (no prefix, no hash of it - a hash is a lookup table when the
  alphabet is 32 characters and the length is 8); losing or rotating a
  friend code must not touch the account; and nothing keyed by friend
  code may ever return the sync code, because the collection is
  world-readable exactly like the others.
- **Never put a username → code lookup in the app.** The collection is
  world-readable, so a lookup shipped in `index.html` is a lookup all ~40
  classmates can run against each other. `tools/firestore-admin.py find`
  exists for the one person with the repo. Handing a code to somebody who
  asks for it is handing over their account — check their level/hundos
  against what they tell you first; usernames are not unique.
- **THE publicId MIGRATION SILENTLY KILLED THAT LOOKUP AND LEFT IT
  LOOKING ALIVE.** `find` printed the leaderboard document id, which WAS
  the sync code while `leaderboard` was keyed by one. Moving the rows to
  `publicId` — the right change, it is what stopped the code being a
  public document id — turned the same line into a twelve-character
  public id presented as something you can sign in with. Wrong format,
  will not link a device, and nothing said so. **A migration that
  changes what a document id MEANS has to be chased into every tool that
  prints one**; there is no gate out here, so it is a read-the-callers
  job.
- **The codes are the document ids of `progress`, and the rules refuse to
  LIST that collection, so there is no anonymous route to one — by
  design.** That refusal is the whole wall between ~40 classmates and
  each other's accounts, and nothing should be added to a listable
  collection to work around it. The supported way back in is a
  **service-account key**, read from `NOVA_ADMIN_KEY` (the JSON) or
  `NOVA_ADMIN_KEY_FILE` (a path). With one, `find` lists `progress`
  masked to `firstName`/`lifetime`/`lastModified` and covers everybody
  retroactively, people hidden from the rankings included; without one it
  says so and falls back to rankings rows rather than pretending.
  **That key is full read/write admin on every classmate's data**, it is
  never in the repo (public, for Pages), and `.gitignore` carries
  patterns for it as a net under that rather than as the plan. The RS256
  signing goes through the `openssl` binary with `cryptography` as a
  fallback, deliberately: this file has always run with no pip install
  and that is worth keeping.
- **Two accounts under one name is now an expected result, not a
  puzzle.** A device that lost its code minted a new one before build
  158, which leaves the same person with an old document holding the
  real progress and a newer, emptier one. `find` prints `lastModified`
  and the lifetime totals for exactly that reason.
- **An onboarded account always has a code, and boot enforces it.** It is
  issued at sign-up, but it lives in `localStorage`, which iOS can evict on
  its own — and a device that has lost it is off the rankings, cannot be
  linked to, and cannot be recovered by anyone. So `store.onboardingComplete
  && !syncCode && !syncOff` issues one. `class26e.syncoff` is the only
  thing that holds that off, and only "Stop syncing this device" sets it —
  a reset deliberately does not, because a reset also clears
  `onboardingComplete` and the sign-up that follows issues its own.
- **The code is mirrored into IndexedDB beside the progress store**, and the
  mirror is written from `persistLocally()`, not only from `setSyncCode()`.
  `setSyncCode()` does not run on an ordinary launch, so mirroring only
  there would have recovered an existing install's progress under a
  brand-new code — the same person, quietly become a different account.
- **Recovery has to finish the job.** `if(!storageHadData)` used to restore
  the store from the mirror and then leave the person on the Welcome screen
  boot had already drawn, because the only screen it knew how to put right
  was Setup. That is the reported *"I hit update, came back, and it was at
  the welcome screen"* — and it is worse than it reads, because creating an
  account from that screen overwrites the progress sitting right behind it.
  Recovery now restores the code, reconnects, and lands on Home.
- **THE TWO MIRROR RECORDS GO MISSING SEPARATELY, and every recovery
  path has to assume it.** They live in the same object store, but one
  of them is every answer this person has ever given and the other is
  nine bytes, so a device under storage pressure really can keep one and
  lose the other. Three shapes, and until build 158 two of them were
  holes:
  - **localStorage gone, both mirror records intact** — the case the
    recovery block was written for, and the one that always worked.
  - **The progress key survived and the code did not.** This is the
    ONLY case the "an onboarded account always has a code" self-heal
    actually fires on, and it used to mint on the spot — which hands the
    same person a second account: their rankings row is orphaned with
    nobody left holding the id to retire it, every other device linked
    under the old code is cut off, and the progress sitting right there
    goes up under an id nobody has ever seen. Some of the dead rows on
    the live board are this. It asks `idbLoadCode()` first now and the
    mint is **deferred, not skipped** — the guarantee still holds, it is
    just satisfied from the mirror first.
  - **The mirror kept the code and lost the store.** This is the shape
    that READS as being signed out: Welcome, no progress, nothing said,
    while the whole account is in the cloud and the key to it is in the
    mirror. Recovery bailed the moment the store record came back null
    and threw the code away with it. It now pulls with that code and
    **adopts it only once a real document has come back** — setting the
    code first is how an empty store gets pushed up under a live account
    and wipes the thing the recovery exists to rescue.
  `check-sync.py` sections 4b and 4c drive all of this for real, and both
  fail on build 157.
- **THE APP ASKS PEOPLE TO SAVE THEIR CODE, ONCE, AND THAT IS THE ONLY
  FIX THAT PREVENTS ANY OF THIS.** Everything else in this section is
  recovery after the fact; `checkSaveCodeReminder()` is the one that
  stops somebody needing it. An amber `account` banner on Home,
  `SAVE_CODE_MAX_PROMPTS` (3) asks, then it stops for good.
  - **The x is not an answer, but the count still goes up.** Same shape
    as the re-add notice, where "Not now" stores nothing and the prompt
    returns next launch — that is the notice whose absence once cost
    somebody their account. Bounded at three because the re-add notice
    ends when a device acknowledges a real one-off event and this one
    would otherwise nag forever.
  - **Counted on SHOW, not on dismiss.** A banner scrolled past,
    ignored, or navigated away from has had its turn; counting only the
    x would let it come back for ever.
  - **A refused clipboard must not mark it saved.** That would silence
    the prompt having achieved exactly nothing, so the failure path
    points at Settings instead.
  - `savedCodePrompts` and `savedCodeSaved` ride on `store`, so copying
    on one device ends it on all of them — the code is the same
    everywhere, so saved once really is saved. They are **the one place
    the `applyLoadedData` "default to already-seen" rule is deliberately
    inverted**: an existing account is exactly who this has to reach.
- **A THIRD BANNER KIND, AND THE THREE MUST STAY TELLABLE APART.**
  `account` is amber `#F5B54D` with a key; `vroom` is blue with a room;
  `friend` is green with a person. Colour AND tag, because one survives
  being read in a hurry and the other survives somebody who cannot tell
  those colours apart. Precedence when several are waiting: Virtual Room
  first (time-sensitive), then friends, then this one — it can wait a
  launch.
- **`.app-banner-act` was 36px for Join and View long before any of this**,
  under the 44px minimum, and a sweep of the app's buttons had missed it
  because it is on a banner rather than a screen. It is 44 now. A
  Virtual Room invite is the most time-pressured button in the app.
- **THE BUILD NUMBER IS ON WELCOME, because that is the one screen that
  could not show it.** Home's label is the VERSION (6.0), which does not
  move between builds, and the build itself only lives in Settings,
  which onboarding cannot reach — so somebody signed out and sitting on
  Welcome had no way to tell whether an update had landed. Reported
  exactly that way. `.welcome-build` is fixed **top**-left, appended to
  `#stage` as a sibling (like `versionTag` on Home) so it holds no space
  and Welcome's auto-margin spacing is untouched, and its selector is in
  `NOTICE_OBSTRUCTIONS` so a banner parks below it.
  **Measured before placing, and the bottom was never an option:**
  Welcome's hint already sits 46px off the bottom edge with the home
  indicator inside that, and 3px clear on an SE 2nd/3rd gen. Above the
  hero there is 85px on a 17 Pro Max and 25px on an SE 1st gen. It
  **overlapped the hero by 4px on both SEs** on the first pass, purely
  because a `<p>` carries a default 1em margin — anything positioned in
  a corner wants `margin:0`.
- **Removing the app destroys the whole storage jar**, so none of the
  three above can help — localStorage and the IndexedDB mirror beside it
  go together. What is left is the launch URL (`#k=CODE`, read by
  `readRecoveryCode()`), and until build 158 `recoveryUrlFor()` was
  **defined, commented and never called**: the only surface it had was
  the re-add notice's Safari hand-off, which builds the same URL inline.
  Settings has **Copy code** and **Copy sign-in link** under the sync
  code now, which is the version somebody needs BEFORE the phone loses
  anything. Section 4d taps both for real and checks the link it hands
  out is one boot will read back.
- **A harness document has to post-date `FRESH_START_CUTOFF`** or
  `pullFromCloud()` reports it as not-found, which is correct behaviour
  and turns a recovery check into a check of the cutoff. Read the
  constant off the app rather than writing a date into the gate.
- **Abandoning a code must take its rankings row with it**, and that lives
  in `setSyncCode()` rather than at each call site, so every path that
  changes a code is covered including any added later. Linking this device
  to another account used to strand the old row on everyone else's board
  with nobody left holding the key to delete it. `retireLeaderboardEntry()`
  deletes **only** the rankings row, never the progress document, which may
  still belong to a device happily syncing under that code — which also
  makes it safe to fire speculatively: unowned, the row goes for good;
  owned, the next push puts it straight back.
- **`exists:false` MEANS TWO DIFFERENT THINGS AND ONLY ONE OF THEM IS A
  RESET.** From the server the document is genuinely gone — a real reset
  on another device. From the CACHE it usually just means this client has
  not been told about it yet, which is what happens while a listener
  re-attaches after a dropped connection and around a fresh sign-up while
  the first push is in flight. Firestore delivers the cached answer first
  and the server's a beat later. Acting on the cached one wipes a live
  account and puts a "reset from another device" notice on top of it —
  reported exactly that way from a device. `handleRemoteReset()` fires
  only when `metadata.fromCache === false`, and only a server-confirmed
  existence arms it. The older `hasSeenExist` guard stays: it covers the
  window before the first write, this covers every reconnect after it,
  and **both are needed**. `check-sync.py` section 6 drives the real
  listener with the five snapshots Firestore actually delivers.
- **Two synced devices are one row by construction**, because the row's
  document id is the shared code. Duplicates on the board are not two
  devices — they are separate sign-ups, each of which minted a code of its
  own, plus the orphans above.
- **Find me has three reasons to fail and naming the wrong one is how this
  was reported**: a device with no code was told to turn on a setting that
  was already on. Not loaded / hidden (`leaderboardOptIn`) / not syncing
  (`!syncCode`) are separate messages. A brand-new account with no data is
  **not** one of them — `liveEntries()` synthesises your row at zero — so
  nothing there may ever say "not in the rankings yet" to somebody who
  simply has not answered a question.
- **THE FIRESTORE RULES ALLOW READING ONE DOCUMENT, NOT LISTING THE
  COLLECTION.** `progress` returns **403 PERMISSION_DENIED** on a list;
  only `leaderboard` and `vrooms` can be enumerated. So nothing can
  delete every progress document — not `firestore-admin.py purge`, not
  anything, without changing the rules first. Worth knowing before
  planning anything that depends on clearing them.
- **A class-wide reset therefore takes two halves, and neither works
  alone.** `FRESH_START` in `index.html` clears each device once on
  launch and lands it on Welcome; `FRESH_START_CUTOFF` makes
  `pullFromCloud()` treat any progress document written before that
  moment as `not-found`, which is what actually kills the old codes,
  since the documents themselves cannot be removed. Purging the cloud on
  its own achieves nothing — `pullFromCloud()` leaves local progress
  untouched on a miss and the next save pushes it all back, so ~40 phones
  would rebuild the board within a day. Clearing devices on its own
  leaves every written-down code working.
- **FRESH_START IS DISARMED (0) AND MUST STAY THAT WAY while the class
  is using the app.** It shipped armed and reached `main`, against this
  file's own "TO DISARM: set FRESH_START back to 0 before this reaches
  `main`". Measured on the live build: a device that had not yet run
  the wipe — a new install, or one whose `localStorage` iOS evicted —
  booted with a seeded, onboarded account and came back
  `onboardingComplete:false`, no name, no sync code, sitting on
  Welcome. Its progress was gone and, per **Accounts and the sync
  code**, creating an account from that screen overwrites what is
  behind it. Arm it only for a deliberate, announced reset, and take
  it back to 0 in the same session.

- **The fresh-start marker lives in `localStorage`, never on `store`.**
  The wipe clears `store`, so a flag there would be erased by the very
  thing it exists to stop and the account would be wiped again on every
  launch, forever. It is also written BEFORE the wipe, so a crash
  half-way through costs one reset rather than a loop. Same shape as
  `tourRev`, and the opposite storage choice for the same reason.
- **REMOVING A HOME SCREEN WEB APP DESTROYS ITS WHOLE STORAGE JAR, AND
  THE RE-ADD NOTICE USED TO TELL PEOPLE TO DO EXACTLY THAT.** Reported
  from a device: somebody followed the notice, re-added, and came back
  to Welcome not signed in. `class26e.synccode` goes and **the
  IndexedDB mirror beside it goes at the same moment** - they are in
  the same jar. The progress document survives in the cloud because it
  is keyed by the code, but the only copy of the code was inside the
  thing they were told to delete, so there is nothing left to sign in
  with.
  **The boot recovery does not cover this and never did.** It reads the
  code back out of IndexedDB IN THE SAME JAR, which is the right answer
  for iOS evicting localStorage under a still-installed app and no
  answer at all for the app being removed. Two different failures that
  look identical from the Welcome screen.
  The notice also said *"Your progress stays."* It could not keep that
  promise, and saying it is what made people comfortable doing the
  destructive thing. **Any copy that tells somebody to remove, reset or
  reinstall has to show them the code in the same breath** - the code
  IS the account, and it lives in exactly one place until it is written
  down.
  `showFrameNotice()` is two steps now: the code, selectable with a Copy
  button and the word "remove" nowhere on that step, gated behind "I've
  saved it"; then the re-add instructions. A device with no `syncCode`
  is never offered the re-add at all, because for that person removing
  the app genuinely would erase everything.
  **`frameId: ""` in version.json is the kill switch** -
  `maybeShowFrameNotice()` bails on a falsy id, version.json is fetched
  live, so emptying it stops the notice on every device at the next
  check with no code change and no update prompt. That is how this was
  stopped the same night it was reported, and it is the thing to reach
  for first whenever a notice turns out to be harmful. **It was back to
  `go-live-1` in build 130**, once re-adding stopped costing anybody
  their account - see the next note. Restoring the id is not bumping it:
  a device that already acknowledged `go-live-1` stays acknowledged and
  is not prompted again.
- **THE FIX IS THE LAUNCH URL, because it is the one thing that crosses
  a destroyed jar.** iOS captures the **full URL, fragment included**, at
  the moment Add to Home Screen is tapped, and launches that exact URL
  forever after. So `safariHandoffTarget()` puts the sync code in the
  fragment of the `x-safari-https:` hand-off, the icon made from that
  page carries it, and the empty jar that re-adding creates signs itself
  straight back in. It is not a cache: the URL is re-read on **every**
  launch, so the jar can be wiped any number of times and the account
  still comes back. That is what "you should never get logged out" asked
  for.
  **The fragment, never the query string.** A fragment is not sent to a
  server and never appears in a Referer, so the code stays out of GitHub
  Pages' logs and away from the Firebase CDN. A standalone app has no
  address bar, and the live document's URL is stripped on adoption
  anyway - only the icon keeps it.
  **A URL MAY NEVER REASSIGN A DEVICE THAT ALREADY HAS A CODE.** Shared,
  stale or mistyped, adopting over the top would take somebody off their
  own account, so adoption is gated on `!syncCode` and on `!syncOff`.
  And it has to run **before** the boot self-heal, which would otherwise
  mint a fresh code first and quietly turn the same person into a second
  account with none of their progress in it.
  A definite `not-found` on an otherwise empty device gives the code
  back, so a dead or retired code does not leave somebody holding one
  and pushing an empty document up under it. Every other reason -
  offline, Firebase blocked - keeps it, because the URL re-offers it next
  launch and giving up on a bad connection is how somebody signs up
  twice.
  **The two-step notice stays regardless.** Somebody who re-adds by hand
  never goes through the hand-off and has nothing in their URL, so the
  code is still shown first and still has to be acknowledged.
  `tools/check-readd.py` wipes localStorage and IndexedDB together - the
  actual event, not an approximation - and asserts the account comes
  back, twice over, and that a URL cannot hijack a device that already
  has one. It fails on build 129 with "re-added app came up on WELCOME".
- **RECOVERING A LOST CODE IS FOUR LAYERS, AND ONLY THE LAST ONE NEEDS
  A KEY.** Asked for in one line — *"I just want the codes to be
  recoverable"* — after an afternoon lost to the admin key, which is
  only the last resort:
  1. *The device cannot lose it on its own* — the IndexedDB mirror and
     the boot self-heal (build 158). This is the one that fixed the
     "randomly signed out" report.
  2. *The app asks you to save it* — `checkSaveCodeReminder()`, three
     prompts then silence (159).
  3. *One tap actually saves it somewhere off the phone* —
     `saveSyncCodeVia()`. **Copy is not save**: a clipboard is
     overwritten by the next thing you copy, and this code has to
     outlive the phone. Share sheet first so it lands in Notes or a
     message to yourself, clipboard only where there is no share sheet.
     It marked `savedCodeSaved` only if the code actually went
     somewhere — a cancelled share and a refused clipboard were both
     "not saved", or the prompt is silenced having achieved nothing.
     **THIS STEP NO LONGER HAPPENS, AND THAT IS WORTH KNOWING RATHER
     THAN DISCOVERING.** The Save code button came off Settings on
     request (the screen was reported as a pile of controls) and it was
     `saveSyncCodeVia()`'s only caller. The banner's "Save it" now
     lands on the sync section instead — also on request, *"it just
     directly takes you to the settings, scrolls down to the sync
     section, and flashes it"* — which is a better teach and marks
     nothing. So **nothing sets `savedCodeSaved` any more**: the
     reminder runs all three of its prompts whether or not anybody
     saved anything, and then stops. `saveSyncCodeVia()` is currently
     uncalled. The fix is another button, which is the thing that was
     asked to be removed, so this is raised rather than patched around.
     **`check-sync` 4d was still driving that button and had been red
     for two builds before anyone looked.** It drives the code row the
     way a person does now: the row exists, it starts hidden, a tap
     reveals the real code and a second tap hides it again, and the
     sentence saying why to keep it is there.
  4. *Somebody looks it up* — `tools/firestore-admin.py find`, which
     needs the service-account key. See the admin-key note below.
  **The banner passes no anchor element to `saveSyncCodeVia`**, because
  `buildAppBanner` removes the banner before calling the action and the
  anchor path awaits two animation frames — which on iOS would step
  outside the user gesture `share()` requires.
- **THE ADMIN KEY GOES IN AS TWO FIELDS, NOT AS THE FILE.** The
  environment-variable box takes one `NAME=value` per line; a
  service-account JSON is ~30 lines starting with `{`, and pasting it
  whole comes back as `couldn't parse "{" — use key=value format`. It
  was then pasted as one line and the box **dropped characters at
  random** — a `K` out of `BEGIN PRIVATE KEY`, and three opening quotes
  — which is not a bad mouse drag (that loses a contiguous chunk) but
  the field mangling a 2300-character paste. So `_load_key()` reads
  `NOVA_ADMIN_EMAIL` and `NOVA_ADMIN_PRIVATE_KEY`, both already single
  lines inside that file, and its JSON failure now names what is
  damaged rather than saying "not valid JSON". **Never ask for the key
  in chat**: it would sit in a transcript forever, it opens all ~40
  accounts, and the container is wiped at session end so it would have
  to be re-pasted every time anyway.
- **A SESSION OLDER THAN THE VARIABLES WILL SWEAR THE KEY IS BROKEN,
  AND IT IS WRONG.** Environment variables are read when a session
  STARTS. One session spent an afternoon reporting "the key does not
  work" — truthfully, about its own stale snapshot — while another,
  started later, was pulling real codes out of `progress` the whole
  time. Before contradicting a session that says the key works, check
  whether this one can even see `NOVA_ADMIN_EMAIL`; if it cannot, it
  has nothing to say on the question. The falsifiable test is the one
  that must be asked for, because "the variable exists" proves nothing
  either: **list the `progress` collection.** Anonymous gets 403
  there, a working key gets 200.
- **Safari and the installed app are separate storage jars on iOS.** The
  re-add notice's `x-safari-https:` hand-off lands in a jar with no
  progress in it, showing Welcome. Signing in with the code is the way
  back; creating an account there is a second profile on the board.

---

## Levels, badges and ranks

The three things the app measures are **XP → level**, **badges**, and
**hundos**, and every screen that shows progress is built on those three.

- **A BADGE COSTS WHAT ITS UNIT IS WORTH (build 190), and there is no
  single threshold any more.** *"Some units are huge and some aren't."*
  `BADGE_THRESHOLD_BANDS`, verbatim as asked: under 20 questions stays
  at 35 hundos, 20-40 is 25, 40-60 is 15, 60-100 is 10, over 100 is 7,
  over 200 is 5. `badgeThresholdFor(unit)` is the only way to ask, and
  `unitQuestionCount()` behind it is built lazily off `QUESTIONS`.
  The reason is arithmetic: a hundo is a WHOLE unit with no misses, so
  its cost already scales with the unit, and multiplying by a constant
  35 scaled it twice — Identity Crimes (12 questions) asked for 420
  perfect answers and Penal Code (340) for 11,900. Measured across the
  real bank the bands turn sixteen wildly different units into sixteen
  roughly equal jobs: every badge but Penal Code's now costs 10,000 to
  13,750 XP of work, against 7,700 to 119,000 before. All sixteen come
  to 367 hundos and 194,950 XP, against 560 and 408,900.
  **A band may go DOWN freely and never up without checking the board.**
  A badge is `hundos >= threshold` computed fresh, so lowering one can
  only add badges and cannot ambush anybody with a cutscene or a
  `MASTERY_BONUS` windfall (`summarize()` diffs either side of its own
  recording calls). Raising one takes a badge off whoever is sitting
  between the two numbers.
  **`badgeThresholdFor` falls back to 35, never to 5**, for a unit the
  bank does not know — an id from another build must not hand somebody a
  badge for nothing.
  **NOTHING MAY PRINT ONE NUMBER ANY MORE.** The badge case's blurb said
  "35 hundos in that unit", which is wrong for twelve of the sixteen and
  would send somebody to Penal Code expecting thirty-five flawless runs
  of 340 questions. Each tile carries its own figure; `check-curve.py`
  asserts the tiles print more than one denominator.
  `BADGE_THRESHOLD` (35) survives as the small-unit band and as what
  `DRILL_STAR_THRESHOLD` is written from.
- The note this replaced, kept for the reasoning: mastery was
  `BADGE_THRESHOLD` (35) hundos, flat. Sixteen units, sixteen badges. `DRILL_STAR_THRESHOLD` is
  *written as that same constant* rather than as another literal, because
  it was a separate 40 for the same idea and a unit could read "Advanced"
  on its own card while still not being starred.
  **It went to 30 for a single build and came straight back to 35** the
  same night (*"make the mastery 35 for each still ... essentially
  revert that change"*). The reasoning for the drop, kept because it
  applies in reverse and explains the reconciler: it was asked *"take the hundo requirement for badges down to 30,
  and ensure it all syncs up ... by the time you reach level 30 you
  should have close to 6 badges."* Lowering it can only ADD badges to an
  existing account, because a badge is `hundos >= BADGE_THRESHOLD`
  computed fresh rather than a stored flag — anyone sitting on 30-34 in a
  unit gained one the day it shipped and nobody lost one. It does not
  ambush them with cutscenes either: `summarize()` detects a new badge by
  diffing the list either side of its own recording call, so a badge
  already held before the run produces no diff.
  **NEVER TYPE THE NUMBER INTO A GATE — AND "READ IT OFF THE PAGE" WAS
  STILL TYPING ONE.** `check-behaviour`'s badge section drove a unit
  from a literal 34 to 35 and went red the day mastery moved; it was
  changed to read `BADGE_THRESHOLD` off the page, which held until a
  badge started costing what its unit is worth. A two-unit run then
  drove BOTH units from that one number, so one of them began the run
  already past its own threshold and the gate reported a badge that was
  already held as a badge that had failed to arrive. It asks
  `badgeThresholdFor()` per unit now and the cases are written as "one
  short" and "already there" rather than as numbers at all. Third time
  this same section has gone stale; the lesson is that a gate must ask
  the app the same question the app asks itself, at the same
  granularity.
- **`levelProgress()` is the one place the level curve lives** — the
  level, how far into it, how far across, and what is left. The bar, the
  number under it and the leaderboard each used to do their own
  arithmetic on the same total. 300 XP at +5% a level, capped at 80. The
  cap came with the curve: 500 at +15% compounded 80 times asks for about
  200 million XP when an aced three-unit test pays under a thousand, so
  the ceiling Madison asked for was unreachable until the curve moved.
  **Check what a curve change does to existing levels before making
  one**, by running BOTH builds' `levelProgress()` over a few thousand
  XP totals and diffing. The first curve change was safe because
  nothing went down; the second (below) lowers levels above 20 and was
  allowed to.
- **THE CURVE STEEPENS AFTER LEVEL 20 AND IS UNTOUCHED BELOW IT.**
  *"Do not let leveling up be too easy ... after level 40 or 50 it
  should [take] multiple tests to even level up. It can [be] easy for
  the first 10-20 levels but needs to be decently hard as it goes on
  ... someone being level 14 without mastering a single unit is kinda
  crazy."* Growth holds at `LEVEL_GROWTH` (1.05) through
  `LEVEL_RAMP_FROM` (20), then climbs by `LEVEL_RAMP_STEP` (0.0008) a
  level to `LEVEL_GROWTH_MAX` (1.075). At ~250 XP for a small perfect
  drill: level 25 ≈ 3.7 tests, 30 ≈ 4.9, 40 ≈ 8.8, 50 ≈ 17.3, 60 ≈
  35.7, 80 ≈ 152. Total to the cap goes 277k → 549k.
  **The growth RATE has to stay near 1 and only creep.** The first
  attempt used +11%/+15%/+19% bands and asked **seventeen million XP**
  for level 80 — the same runaway the note above records for a flat
  +15%. Compounding over 80 levels punishes any real increase.
  **Verified by diffing both builds' own `levelProgress()` over 4,380
  XP totals**: zero level changes at or below 20, nobody gains a
  level, first drop at 15,344 XP (27 → 26), biggest at the cap (78 →
  68). Lowering above 20 was explicitly accepted — *"if peoples levels
  get slightly lowered to fix this based on their current earned so
  then so be it"* — and nothing is reset: the XP total is untouched and
  the level is derived from it.
- **NOBODY'S LEVEL MAY CHANGE, AND THAT IS THE FIRST CONSTRAINT, NOT A
  NICETY.** *"Just to CLEAR! I don't want peoples current level to go
  backwards!!"* and then *"I don't want peoples levels to change at
  all."* A level is DERIVED from XP every time it is shown, so making a
  level dearer silently takes it off anybody who had already reached it
  — there is no grandfathering to fall back on. Two fits in a row got
  this wrong by freezing the early curve at the NEW build's prices
  instead of the ones that produced those levels; both dropped the top
  of the board from 25 to about 10.
  **Levels 1–25 are byte-identical to the live curve** (base 300,
  ×1.05), and that is verified by walking **every XP total from 0 to
  14,306 one at a time** rather than by spot checks. Above that,
  `preserveLegacyLevel()` is a one-shot top-up that holds anyone the new
  curve would demote — insurance for somebody who levels past 25 on the
  old build before they update. **It must stay one-shot**: topping up
  raises the total, the old curve is cheaper, so a second pass reads a
  higher old level and tops up again, walking someone to the cap.
- **THE CLIMB STARTS AT 26, AND THE TWO NUMBERS ARE SOLVED, NOT
  CHOSEN.** *"A lot more xp needed to level up starting at level 25
  going into 26."*
  **RE-SOLVED IN BUILD 190 against the per-unit badge thresholds**,
  which moved the thing the old pair was fitted to: all sixteen badges
  cost 194,950 XP now where the flat threshold cost 408,900. Left alone,
  the curve would have put a player holding every badge in the app at
  level 60. `LEVEL_STEP_UP` is **2.0** (level 26 costs 1,842 against
  level 25's 921) and `LEVEL_LATE_GROWTH` is **1.0199**, compounding to
  5,332 at the cap — solved against the same anchor as before, that
  **all the badges there are lands exactly on the cap**.
  What it costs to climb, in correct answers at 10 XP each: level 26 is
  184, level 50 is 295, level 60 is 360, level 80 is 533. Two levels at
  60 went from 74.8 perfect drills to 28.8 — *"if you are level 60 I
  don't want you to have to play for a week straight to earn 2
  levels."*
  **NOBODY'S LEVEL CAN DROP, AND THAT IS PROVABLE RATHER THAN HOPED.**
  Levels 1-25 are byte-identical and every level above 25 is CHEAPER
  than the build before it, so no XP total can lose a level in either
  direction. `check-curve.py` section 2 asserts exactly that for every
  XP total from 0 to 600,000 against the old curve rebuilt from its own
  two constants — no live account is touched to establish it.
  The numbers this replaced: `LEVEL_STEP_UP` 3.1102 and
  `LEVEL_LATE_GROWTH` 1.0354, fitted so a second badge landed on level
  30 and twenty badges on level 80.
- **THE ATTEMPT RATE IS MEASURED, NOT GUESSED — GETTING IT WRONG COST
  TWO FITS.** Assuming "about two tests per hundo" priced a badge at
  nearly double what one costs, and the ladder came out so expensive
  that the best player in the class would have earned **all twenty
  badges at level 69 and never seen the cap**. The real number is on
  the board: 1,068 correct answers and 44 hundos, and **1068 ÷ 44 =
  24.3, which IS his average unit size** — a hundo is a whole unit with
  zero misses, so that ratio matching the unit size means essentially
  every test he took was a hundo. Reported exactly that way before the
  arithmetic caught it: *"he didn't take 50 tests for one badge."*
  **The leaderboard is the instrument here** — `correct` and `hundos`
  per person, and their ratio is the attempt rate. Re-measure it before
  re-fitting anything; the progress documents cannot be read (403 on a
  list, by design), so this ratio is the only window onto how people
  actually play.
  Fitting at one test per hundo also puts the error on the right side:
  anyone who DOES need extra attempts earns more XP per badge and runs
  slightly ahead on level, which leaves the badge as the thing gating a
  rank.
- **`MASTERY_BONUS` is 2,500 and no back-pay is ever paid.** It was
  36,000 once and that was the mistake — big enough to decide the curve
  on its own, it dragged one badge to level 32 when the target was 25.
  At 2,500 it shows up in the results breakdown without moving the
  ladder, and the curve is fitted WITH it included. Existing totals are
  treated as already containing it, by instruction (*"let's just assume
  he was already given the mastery bonus"*), which is also what keeps it
  from moving a single existing level. A reconciler that back-paid it
  was built and removed for exactly that reason.
- **A RANK SOMEBODY REACHED TODAY IS NOT SOMETHING TO TAKE BACK.**
  *"Alex did rank up today, so ensure that his rank requirements don't
  change, but the others might."* So **Iron stays exactly as the live
  build has it — level 5, 1 badge** — and every rank above it moved.
  It costs the ladder nothing: a badge is 35 hundos, about 14,400 XP,
  which is level 25 anyway, so the level half of that rule never binds
  and the badge is what grants it. The rest are read off the measured
  badge line.
  **THE TOP RANK WAS UNREACHABLE BY ANYONE, AND NOT ON PURPOSE.**
  Supernova asked for 20 badges in an app with 16 units. The note here
  used to say that was deliberate, held for units that do not exist yet;
  that is a rank nobody in the class can ever hold, on a ladder whose
  whole job is to be climbed. Build 190 re-spread the counts over the
  units there actually are: **1, 3, 5, 7, 9, 12, 14** — the same
  growing-gap shape, ending two badges short of every badge there is, so
  the last rank is a climb rather than a completionist's receipt.
  **NO LEVEL THRESHOLD MAY GO UP.** A rank is computed fresh from level
  and badges, so raising either number takes a rank off whoever holds
  it — Iron was reached by a real person the day it shipped. Every level
  is the smaller of what the live build asked and what the new badge
  line measures: **Iron 21/1, Bronze 29/3, Silver 36/5, Gold 45/7,
  Sapphire 52/9, Amethyst 65/12, Supernova 71/14.**
  The measured badge line under the new curve, smallest units first, is
  1 → 21, 3 → 33, 5 → 42, 7 → 50, 9 → 58, 12 → 67, 14 → 73, 16 → 80, so
  the BADGE is the gate at every rank and the level is always already
  there: at 3 badges you are 33 against the 29 asked, at 14 you are 73
  against 71. `check-curve.py` asserts that relationship, that no rank
  asks for more badges than there are units, and that no threshold is
  harder than the live build's.
  **Check the board before changing a threshold.** Every rank needs at
  least one badge and only one person in the class has one, so a
  `firestore-admin.py list` answers "can anybody lose a rank" in thirty
  seconds.
- **The cap is 80.** It went to 100 for one build and came straight back
  out; 100 is held for when the extra units land alongside a rank above
  Supernova. Raising it means re-solving the two anchors, not nudging
  the constants.

### Ranks

**A rank and a flare are two different things, and they used to be one.**
The tiers were named after the flares — Spark, Ember, Comet — so the
Mastery Ladder and the Home screen's orbit were two names for one thing,
and climbing gave you nothing to be *given*. The ranks have their own
names now (`RANK_DISPLAY_NAME`) and the flare is one of the things a rank
**hands over**. Reaching Bronze lights the Ember flare and unlocks the
Ember colour; the rank is not called Ember. Keep that distinction in any
copy you write: `ACCENT_DISPLAY_NAME` is the flare/colour,
`RANK_DISPLAY_NAME` is the rank, and they have separate swatches
(`ACCENT_SWATCH` vs `RANK_COLOR`). **They now carry the same colour
on purpose**, asked for directly: *"ensure the theme colors match the
colors of the rank you are getting (you start off as iron so that's
already the default color)."* `ACCENT_SWATCH` is `RANK_COLOR` lifted a
few levels so it holds up as an accent on a dark screen, not a separate
palette. The names stay apart; the colours deliberately do not. The
older note here said a rank the same colour as its reward has nothing
left to be — that reasoning is superseded, and the stale version of it
survives as a comment above `RANK_COLOR`.

**THE RANK NAME IS ITS COLOUR: Iron, Bronze, Silver, Gold, Sapphire,
Amethyst — and Supernova, the one exception, below.** That is the thing
the reference does that makes it read at a glance, and it took two
passes to see it. The role words — rookie, ranger, veteran, vanguard,
adept, elite, titan — carry no colour, so seven coloured cards were
seven arbitrary colours you had to learn. The **keys are still those
role words** and must stay: `TIER_UNLOCKS`,
`ACCENTS`, `ACCENT_SWATCH` and a theme somebody already has selected are
all keyed by them, so renaming a key is a migration for a cosmetic gain.

- **The thresholds did not move.** `TIER_UNLOCKS` is the same table with
  the same level-and-badges pairs; the keys are the same too, which is
  what kept this a rename rather than a migration — `ACCENTS`,
  `ACCENT_SWATCH` and a theme somebody already has selected are all keyed
  by them. The keys no longer resemble the names at all — **`adept`
  displays as "Sapphire"** — and that is fine: a key is a storage
  identifier, and renaming one to match a display name is a migration
  for a cosmetic gain.
- **`rankOfStats(level, badges, mysteryFound)` is the single definition
  of who holds what**, and it takes the numbers rather than a store, because the
  rankings and the Virtual Room ask it about *other people* from a
  published document. `rankOf(store)` is the wrapper for yourself.
- **The third argument to `rankOfStats` is vestigial, and it is left in
  on purpose.** It was the Secret Flare count, which Supernova used to
  require; the flares are scrapped (see below) and no rule in
  `TIER_UNLOCKS` carries a `mysteryStars` field any more, so the
  `typeof rule.mysteryStars === "number"` guard is simply never true.
  The parameter and the guard stay because the leaderboard and the
  Virtual Room publish a `mystery` field on every document and older
  documents still carry it — a signature change here is a wire-format
  change, for nothing.
- **THE SECRET FLARES ARE BACK — the HUNT ONLY.** They were scrapped by
  explicit request, then asked for again just as explicitly: *"I don't
  like either of those ideas, let's do the secret flares"*, as the
  unlock for the fourth earned character. The entry below this one is
  HISTORY: do not "restore" the scrapped state on the strength of it.
  Three separate things were scrapped together and only one came back.
  - **The hunt came back.** `maybeStartMysteryForRun()` arms at most one
    flare per run and never on a run shorter than `MYSTERY_MIN_RUN` (5)
    — a one-question Daily has nowhere to hide anything. A glint appears
    at one question position, is tapped, and the colour is recorded.
    Nothing else in the app tells you it is coming, which is the point.
  - **HOW HIDDEN IS MEASURED IN TESTS COMPLETED, NOT IN RUNS BETWEEN.**
    `MYSTERY_AT` is `[80, 200, 350]`, asked for by number: *"a person
    should see the first flare when they get to 80-90 tests taken. The
    second one can be around 200, and make the 3rd one at about 350 or
    so."* This replaced a two-run gap and is a better KIND of gate: a
    gap in runs makes the hunt something that happens to everybody at
    the same rate from the day it lands, while a lifetime count makes it
    something that happens to people who have put the work in — which is
    what a secret is for. An account that already has three hundred
    tests behind it gets the first two quickly, which is right: they
    earned them before the feature existed.
    The count is `testsCompletedOf()`, **the same number the Stats tab
    prints**. It was written out longhand there and is a function for
    that reason alone — a gate on a number nobody can see is a gate
    nobody can be told about.
  - **The glint is a glowing ORB, not a sparkle, and it is 1.65rem.**
    The first version was a `.82rem` four-point star and came straight
    back off a screenshot: *"that's way too tiny, make them a bit bigger
    so they are easy to see"*, alongside *"a pretty small tiny glowing
    orb thing"*. `buildFlareOrb()` is one builder used in three places —
    the glint, the banner that announces it, and the cutscene — so the
    thing you tapped and the thing you are shown cannot drift. It
    breathes rather than spinning: a 45° rotation is right for a
    four-point sparkle and meaningless on a circle.
  - **The Eclipse colour did not**, and `titan`'s requirement did not.
    `titan` is plain "Reach level 70 and 14 badges", and
    `rankOfStats`'s third argument stays vestigial. **Re-arming that
    guard would change what the top rank costs for people already
    climbing to it** — luck in front of a rank is the one thing the
    ladder must never ask for. A character is a thing you find; a rank
    is a thing you climb to.
  - **Nothing was migrated, because nothing had to be.**
    `store.mysteryColorsFound` (red/orange/yellow) and
    `testsUntilMystery` stayed defaulted in `applyLoadedData()` through
    the whole scrapped period, which is exactly the property that made
    this a revival rather than a rebuild. `testsUntilMystery: null`
    means "never counted down" and arms on the first eligible run, so
    the feature turns up for everybody rather than waiting two runs to
    exist.
  - **THE GLINT LIVES IN THE QUESTION CARD'S HEADER ROW AND NOWHERE
    NEAR THE CHOICES.** It is a 44px tap target with a ~13px mark inside
    it (the same padding trick the Settings text links use), absolutely
    positioned inside `.qnumrow` at a horizontal fraction picked once
    per RUN — not per render, because `render()` runs again on every
    wrong answer and a glint that jumped each time you missed would read
    as a glitch. A stray tap on a decoration is a shrug; a stray tap
    that eats an answer is a wrong answer somebody did not give, and
    this app records those permanently. `check-unlocks.py` asserts the
    overlap with every `.choice` is zero.
  - **The payoff is the burst, so the node is disabled on tap and
    removed a beat later**, not removed immediately. The banner arrives
    from the top edge and the eye is down in the card, so the half
    second of expanding spark is the whole feedback for finding one.
  - **Home's three orbit dots are the permanent mark and always were.**
    They were left in place as dead decoration when this was scrapped
    and light up in their real colours again with nothing new added to
    that scene. There is no new element and no Secret Flares box — the
    box came off the Rank tab by explicit request and stays off.
    Noticed and liked on a screenshot: *"you made the tiny circles on
    the main menu light up and make them the 'secret glares'"*.
  - **THE THIRD FLARE QUEUES A CUTSCENE FOR THE MAIN MENU.** An earlier
    pass announced "Void unlocked" in a banner at the moment of the find
    and stopped there, reasoning that a cutscene minutes later has no
    connection left to the thing just tapped. Reported straight back:
    *"Not sure why the 'void unlocked' thing is on the main menu, ensure
    there is a cool cut scene involving those tiny secret glares."*
    `playVoidCutscene()` is **made of the three orbit dots**: the same
    three colours start at the same three positions `buildCosmicHero()`
    puts them, come loose, fall together over 1.9s, burst, and collapse
    into the character. That is the right shape for it because those
    three dots going one by one from grey to lit is the ONLY thing a
    person has seen of this feature before now.
    `store.pendingVoidCutscene` is queued on `store` for the same reason
    the badge queue is: there is no fixed route from a test to Home, so
    the flag has to survive the trip and a relaunch.
    **The convergence is a TRANSITION, not a keyframe animation**, and
    deliberately — the global `[data-reduce-motion="true"] *{animation:none}`
    rule strips keyframes, which would have left three orbs sitting
    motionless in a ring for nine seconds. Transitions survive it.
    **The flash lives inside `.void-field`, not on the overlay.** On the
    overlay it is centred on the SCREEN while the orbs are centred on
    the field, and the field sits above centre because the title and
    subtitle below it take real height — so the burst came out offset
    from the thing it was bursting out of, which on a recording read as
    a circle with a flat bottom. Found on the recording, not by reading
    it.
- **The scrapping, for the record**, asked for in one line: *"the
  'mystery flares' should be scrapped."* The requirement came off
  Supernova (`titan` is now plain "Reach level 70 and 14 badges"),
  `"mystery"` came off `ACCENTS` and `ACCENT_DISPLAY_NAME`, the hidden
  star button and its banner are deleted, `maybeStartMysteryForRun()` is
  a no-op, and Home's orbit dots are decorative again. **The `store`
  fields stay defaulted** (`mysteryColorsFound`, `testsUntilMystery`) —
  an account that found one is not worth a migration, and dropping a
  field from `applyLoadedData()` is how a cloud document starts losing
  keys on every round trip. Nothing reads them.
- **SEVEN CELESTIAL BODIES, not seven stars.** Three sets came before
  and each failed the same way. The app's V inside a frame that gained
  wings and horns escalated but had nothing to do with the app. A star
  inside a corona ring with rays coming off it **read as a wheel** —
  which is what a ring plus evenly spaced radial lines always reads as.
  The third was generated from one table (same star, more points, bigger
  radius): *"I dont like how they are all nearly identical just
  different in size."* The fourth put service chevrons on the bottom
  three and was rejected outright: *"I'm not a fan of the iron bronze
  silver icons after all."*
  **The drama has to come from what the object IS.** These are the life
  of a star told as seven things you can name at a glance: Iron a dead
  rock that makes no light of its own, Bronze a ringed world, Silver a
  crescent with a star in its cradle, Gold a sun that finally makes its
  own light, Sapphire a comet, Amethyst a galaxy, and Supernova the app
  going off. Every silhouette is different, every one is legible at
  26px on a rankings row, and the order escalates by kind rather than by
  size. `check-behaviour` asserts it structurally: no two ranks produce
  the same shape signature.
- **A circle reads as a world only if it has a terminator.** `litBody()`
  draws the whole disc in shadow and then the lit side as an offset
  circle clipped back to it. Without that step every one of the bottom
  four is a coloured dot.
- **The ring on Bronze is a tilted ellipse drawn in two passes**, with
  the body between the far side and the near side, and **nothing radial
  anywhere near it** — that is the only thing keeping it a ringed world
  rather than the wheel this set has read as twice before. A single pass
  would redraw the far side over the body and flatten it.
- **The crescent is a real cut, not a shape drawn to look like one**: a
  disc minus an offset disc, one path, two subpaths, `fill-rule:evenodd`.
  The bite then lands in the same place at every size.
- **Sapphire is the only asymmetric emblem in the set, deliberately.**
  Direction is the whole idea of a comet, and a symmetric comet is a
  star with fuzz on it. Its tail is drawn twice — one wide and soft, one
  narrower and brighter inside it — because two separate tails at
  different angles read as two blue shards rather than as one thing
  streaming off a head.
- **The glow is a CIRCLE filled with the falloff gradient, not a burst
  shape filled with it.** A twelve-point burst at a wide waist is a
  bulging rounded square, and filled with a soft gradient that is
  exactly what it looked like — a coloured tile behind the emblem rather
  than light coming off it.
- **Three rules carry over from the burst set, because each was learned
  the hard way.** Nothing is a circle with spokes on it — rings here are
  broken arcs, never closed. An arm's sides are quadratic curves pulled
  in towards the centre, so the tips are sharp and the shape is a light
  source rather than a cog; Gold's corona alternates long and short
  tongues for the same reason. And a sparkle sits in the GAP between two
  arms, never on an arm's axis, where it is only that arm made longer.
  **Lens streaks are always at different lengths** horizontally and
  vertically, because equal ones make a cross and a cross is a plus
  sign, not a flare.
- **Reflecting an angle is `PI - th`, and the offset from straight up is
  not the angle.** Every "mirrored pair" of sparks in two successive
  versions landed both copies on the SAME side, because `[a, PI - a]`
  was being applied to the offset from `UP` rather than to the absolute
  angle. Visible as a star with all its sparks on the right. `pair()`
  does it correctly; use it rather than writing the reflection again.
- **The top rank is called Supernova**, and that is the one place a rank
  is not named after its colour. Asked for by name: *"the very last one
  needs to be called supernova and it needs to be very cool."* Its key
  is still `titan` and its colour is still `#E23B3B`. It shares a name
  with its own flare, which the rule about ranks and rewards would
  normally forbid — here it is the point: the rank IS the app going off.
- **A CUTSCENE'S COLOUR HAS TO REACH BOTH HALVES OF IT, AND FOR A LONG
  TIME IT REACHED NEITHER.** `playTierCutscene()` swapped
  `document.documentElement.dataset.accent` to the tier key, built the
  hero, and swapped it back — and the comment above it said that was
  enough because `buildCosmicHero` reads the accent at build time. It
  does not. `accentToGradientStops()` returns early on `theme.accent`,
  the STORED accent, so for anybody on the default theme (after a reset,
  everybody) it handed back the default three stops and ignored
  `--accent` entirely; and the burst flash and the title's glow are CSS
  reading `var(--theme-c1/c2)`, which resolve long after the swap has
  been undone. All seven rank cutscenes played the same sphere and the
  same flash. The fix is both halves: `buildCosmicHero(true, tierKey)`
  for the JS-built gradient, and **`data-accent` plus `data-theme` on
  the OVERLAY** for the CSS — the accent variables are declared on a
  plain `[data-accent="..."]` attribute selector, so they apply to any
  element's subtree, which is also what lets the rest of the app stay on
  the person's own theme. **Found on a screen recording of four of them
  side by side, not by reading the code**, which asserted the opposite
  in a comment.
- **A cutscene fades in and out over whatever is behind it, so `showHome()`
  clears the stage before handing over.** A rank-up is reached from the
  results screen via Main menu, and without this the 100% card showed
  through both fades and came back for half a second after the rank was
  announced, before Home mounted. Also found on the recording.
- **A locked rank still shows its colour.** The emblem is always drawn in
  the rank's own colour and the card only turns it down; it used to
  redraw in grey with the name in `--soft`, so four of the seven cards
  were the same colourless card and you could not see what you were
  heading towards. `check-behaviour` asserts all seven `--rank-color`
  values are distinct and set.
- **A rank card has a backdrop, in three layers and none of them an
  image**: the rank's own emblem enormous and almost invisible behind
  everything, a diagonal wash of its colour, and a vignette to stop the
  wash reaching the corners. The watermark reuses `buildRankEmblemSVG`
  rather than being a second drawing, so the two can never disagree, and
  it has to be **too big to read as an object** — at 78% it sat inside
  the card as a smaller second emblem below the real one, which is a
  duplicate, not a watermark.
- **The card is a GRID, and that is what lets one piece of markup be two
  layouts.** The name sits BESIDE the emblem on a phone and ABOVE it on
  a tablet, and no `flex-direction` can express that with one DOM order
  — `grid-template-areas` can. On the wide layout the header strip pulls
  back out through the card's own padding to run edge to edge with a
  rule under it, the way the reference's tier name does.
- **The glow comes off the emblem with a CSS `drop-shadow`, not an SVG
  filter.** SVG filters are the one feature that has bitten this app on
  real iOS hardware; `filter:drop-shadow()` on the element is safe and is
  what the hero already animates.
- **The meter belongs to the rank you are climbing to, and nothing
  else.** Every unreached rank carried one, which put a half-full bar on
  Supernova while you were working on Gold — progress towards something
  you are not working towards. A locked rank says what it costs and
  stops there.
- **The emblem is lit or it is not.** It was two stacked copies with the
  lit one clipped from the bottom, so a rank part-way earned was
  part-way lit — asked for, built, and then explicitly asked against
  ("the stuff slowly being filled up with colour is not the move"). A
  rank is something you hold or do not, and a waterline across it says
  neither. **Don't bring it back.**
- **Four states, and each card says which in a word.** Reached / You are
  here / Up next / Locked, as a chip. The colour and the dimming say it
  too, but only to somebody who has already worked out the code, and
  "what you are, what you have, what is to come" was the thing the
  rebuild was asked for. A meter appears only on a rank you have not
  reached; on a reached one it is a bar that is always full, which is
  noise.
- **One full-width row per rank, at every width.** Two short cards per
  row was the phone layout and it was reported as atrocious; the upright
  four-across card that replaced it on a tablet was reported next — seven
  of them wrap four-then-three, so the climb reads left to right and then
  left to right again. A ladder has one reading order. The phone
  arrangement was already the simple one and was already liked (*"I also
  like how you have it shown on the iPhone, you are making it a
  scrollable screen, that's a great idea"*), so a wide screen gets the
  same thing with more room rather than a second design: only sizes
  change at 46rem and 62rem, no grid areas move.
- **The bottom tab is "Leaderboard" and the Profile tab is "Rank".**
  Both were renamed in the end. This note used to say Leaderboard would
  not fit a 320px phone's bar and that renaming the bottom tab was the
  worse option — **measured after the change, the bar is 296px wide
  inside a 320px screen and no label clips**, so that was a guess wearing
  the clothes of a measurement. The Profile tab KEY is still `"ranks"`,
  and `"ladder"` was already an accepted alias, so nothing stored or
  linked had to move. `showRankings()` is still the function name.
- **There is no Secret Flares box on this tab, and there is no hunt
  behind it either.** The box came off first, as the one thing on the
  screen that was not a rank (*"this rank screen needs to be very simple
  to understand ... very clean"*); the feature came off next
  (*"the 'mystery flares' should be scrapped"*). Supernova's requirement
  line is now just its level and badge counts. Don't reintroduce either
  half.

- **Only list rewards that exist.** Each card names three — the flare on
  Home, the theme colour, and the rank's emblem beside your name — and
  the TOP FOUR name a fourth, because those each hand over a character
  as well. The list is what you actually get, not a fixed shape with a
  gap in it; `check-behaviour` asserts `[3,3,3,4,4,4,4]` rather than one
  number for all seven. Padding a short list is worse than a short list.
- **Four characters sit behind the top four ranks**: Robot on Gold,
  Clown on Sapphire, Officer on Amethyst, Astronaut on Supernova —
  ordered by how hard each should be, asked for in exactly that order
  (*"the astronaut needs to be the hardest one to get, the police men
  the second hardest, the robot the easiest, and the clown the 3rd
  hardest"*). This note used to say Officer on Gold and was stale: the
  Officer moved UP because this is a police academy class and it is the
  one character that is what the course is FOR, so the closer to the
  top the more it is worth holding. The Astronaut still ends the ladder,
  because the app is Nova, the top rank is Supernova and the emblems are
  the life of a star. `isLockedCharacter()` and
  `characterLockMessage()` deliberately MIRROR `isLockedAccent()` and
  `accentLockMessage()`: a locked colour and a locked character are the
  same idea, and two answers to "is this unlocked yet" is how one of them
  ends up wrong. A character with no `unlock` is free, so the original
  eight are untouched and an id from another build never locks somebody
  out of their own avatar. Locked ones are SHOWN with a padlock — on the
  CUSTOMISE screen. The onboarding picker hides them, asked for
  directly: *"the locked characters should not be included there"*.
- **FOUR MORE ARE EARNED BY DOING SOMETHING, and they carry `feat`
  rather than `unlock`.** A rank comes to you if you keep studying; a
  feat does not, which is why these are the four with the characters
  worth wanting. `isLockedCharacter()` answers for both kinds, so there
  is still ONE answer to "is this unlocked yet" — the same rule that
  keeps a locked colour and a locked character in step. Easiest to
  hardest, the same order the rank four are listed in:

  | character | `feat` | costs |
  |---|---|---|
  | Detective | `daily10` | 10 daily questions right in a row |
  | The Masked One | `streak10` | a hundo in 10 DIFFERENT units in a row |
  | Zeus | `weektop` | finish a week top of the weekly XP board |
  | Void | `flares` | all three Secret Flares |

  Two of the four were asked for by name and by pairing — *"a detective
  for the daily question would be pretty sweet"*, and the flare one as
  *"entirely dark black character with a flare color thing where it has
  like tiny flares on it that glisten and it looks like it's in space"*.
  Zeus was asked for as **a statue, not a person** (*"let's do zeus but
  make it like a statue, not a person, that could be sick"*), and then
  relaxed further — *"Zeus doesnt necessarily need to look like zeus, it
  just needs to be a Greek statue character ya know"* — so the artwork
  is free to be any classical bust. The daily-question target was
  corrected to ten explicitly.
  **Zeus's feat was corrected too**, and this is the kind of thing worth
  recording because the first version was a reasoned guess that was
  simply wrong. It was `exampass` (pass the Practice Test), chosen on
  the argument that a leaderboard finish depends on who else happens to
  be online while the Practice Test is entirely in your own hands. The
  answer was *"The unlock for the greek statue is wrong too, it's
  supposed to finished the week as the #1 on the weekly xp
  leaderboard"*. It is the only feat in the set you cannot earn alone,
  which is the point of it: the other three are you against the
  material, this one is you against the class.
  `store.practiceTestPassed` is still tracked and still defaulted even
  though no character reads it any more — a Practice Test pass is a real
  fact worth having recorded, and it costs four lines.
  **`CHARACTER_FEATS` carries the check AND the sentence**, so the gate
  and the copy shown to somebody who has not earned it cannot drift —
  the same reason `TIER_UNLOCKS` carries its own label. The message
  shows PROGRESS, not just the target: "0 of 10" and "7 of 10" are
  different pieces of information and the second is the one that makes
  somebody go and finish it.
  **`characterLockMessage()` returns "" for anything not locked.** It
  did not, and would happily hand back "Find all three Secret Flares
  (3 of 3) to unlock Void" to somebody already wearing Void. Every
  caller today asks only when `isLockedCharacter()` is true, which is
  exactly the kind of thing that stays true until it does not.
- **The four counters, and why each defaults to NOT-YET-EARNED.**
  `dailyCorrectStreak`, `unitHundoStreak` (+ `unitHundoStreakUnits`) and
  `practiceTestPassed` are new persisted fields, so they need their
  `applyLoadedData()` defaults — and those defaults are **zero/false**,
  which is the opposite of the `seenXTour` rule and deliberately so. A
  tour flag defaults to already-seen because an existing account must
  not be shown something as new; a feat defaults to zero because an
  existing account genuinely has not done it yet — nothing was tracking
  it to know otherwise. Nobody loses anything they held, because nobody
  held these until this build.
  - **"In a row" on the daily question means consecutive daily
    questions ANSWERED, not consecutive days.** Missing a day does not
    break it — a run of ten that a weekend away can end is a punishment
    for having a life, and this class has plenty of those already.
    Getting one wrong does break it, which is the part that makes it
    worth holding.
  - **"Ten different units" is why `unitHundoStreakUnits` is a LIST and
    not a count.** Acing Identity Crimes — 12 questions, the smallest
    unit in the app — ten times over is ten hundos and one unit, and
    would have been the whole feat in about fifteen minutes. A unit
    already in the streak is not a setback either; it simply does not
    count again.
  - **A partial slice neither extends the streak nor breaks it**, on
    the same `isFullUnitRun()` rule hundos themselves already use. A
    looser rule here would mean a ten-question slice could break a
    streak it was never eligible to extend.
  - **The Practice Test is the one run with a pass mark on it**, so it
    is the one run that can be passed — `practiceTestMinutes != null`
    is the discriminator, not the label (it launches with `runLabel`
    null). `timedOut` is deliberately NOT excluded: running out of time
    on a 90-minute exam and still clearing `PASS_MARK` is passing it,
    which is what the real thing would say.
  - **"FINISHING A WEEK #1" CANNOT BE OBSERVED DIRECTLY, and what is
    recorded instead is stated honestly here rather than pretended
    about.** Nothing on the device is awake at midnight on Sunday and
    the board itself resets, so by Monday last week's standings do not
    exist anywhere to be read. `observeWeeklyRank()` records your
    position the last time you LOOKED during a week; `settleWeeklyWin()`
    counts a win when the week key changes and that last-seen rank was
    1. That is generous at the edges — first on Saturday night, did not
    open the app on Sunday, still counts — and the alternative is a feat
    nobody can ever earn. It is never generous in the direction that
    matters: you have to have actually been first on the real board,
    with the whole class's numbers in it, while you were looking.
    `weekRankSeen` is ONE object rather than two fields, because a rank
    is meaningless without the week it belongs to and two fields is how
    they end up describing different weeks.
    It is hooked in `paint()`, which runs on every snapshot and every
    tab change, so simply having the Leaderboard open keeps it current —
    hooking the weekly board alone would have made the feat depend on
    which tab somebody happens to like.
- **THE UNLOCK BANNER SHOWS THE CHARACTER.** Asked for directly: *"The
  unlock banner when unlocking the characters should show the character
  in the unlock banner by the way."* `showCharacterUnlockBanner()`
  draws it from `buildAvatarCharSVGSafe`, the same builder every other
  screen uses, never from a second copy of the artwork — the exact
  mistake the rank-up banner made once, announcing a rank while drawing
  the flare that rank hands over. No coin behind it: a character brings
  its own halo now, and a disc of somebody else's colour fights it.
  Void is the one exception and gets no banner at the moment of the
  find: it gets the cutscene, and the banner after it.
- **A "BEFORE" SNAPSHOT BELONGS BEFORE EVERY MUTATION IN THE FUNCTION,
  NOT BEFORE MOST OF THEM.** `lockedCharacterSet()` is diffed either
  side of `summarize()` to find newly-earned characters, and the first
  version sat next to `badgesBefore` — forty lines down, and *after* the
  daily-question block that writes `dailyCorrectStreak`. So the tenth
  daily in a row had already unlocked the Detective by the time the set
  was built and the diff found nothing. The tier snapshot below it
  carries its own comment about exactly this trap; it was hit again
  anyway. The gate catches it now.
- **DRAWING A NEW CHARACTER: the value stack is the whole job, and
  Zeus took four passes to prove it.** Pass 1 carved him entirely out
  of one pale marble — face, hair, beard and shoulders from the same
  gradient — and rendered beside the other fifteen he was a featureless
  grey egg. Pass 2 made the hair and beard much DARKER than the face
  and came out *worse*: the dark beard and the dark robe merged into
  one mass that swallowed the cheeks and the thing read as a tiki mask.
  **The wizard is the model**, because his beard reads at 34px and
  Zeus's did not — and not because it is better drawn: it is white on
  purple. What the twelve working characters all do is **a pale face,
  features clearly darker than it, a strongly coloured mass below, and
  one saturated accent**. For a marble statue that means the separation
  between face, beard and hair comes from CUT LINES rather than from
  three different greys (which is also what carving actually looks
  like), the robe is the one dark thing, and the laurel is GOLD. The
  same fix applied to the Detective, whose first pass had the hat, the
  shadow, the skin and the coat all in one brown family: charcoal hat,
  lit face, camel trench.
  **Render all sixteen side by side before believing any of them** —
  at 120px AND at 34px, which is the size a rankings row actually uses.
  Every one of these faults was invisible in the path data and obvious
  the moment the set was rendered together. It is a thirty-second check
  and it is the only reason any of them got fixed.
- **A GRID'S COLUMN COUNT FOLLOWS ITS ITEM COUNT — now three times.**
  Sixteen characters in the Customise grid's six columns is two rows of
  six and a ragged row of four, the exact arrangement already recorded
  here as reading like a mistake. Sixteen divides evenly by four and by
  eight and by nothing in between, so it is **four across on a phone
  and eight from 40rem**. Not eight on a phone: eight columns inside a
  375px content column is a ~41px cell, under the 44px tap-target
  floor. Four rows of four is more scroll on a screen that already
  scrolls, which is the cheaper of the two costs.
- **A person's rank hangs off their character, not beside it.**
  `decorateAvatar()` is the one builder — the three rankings boards, the
  Virtual Room lobby and the Virtual Room results all call it, so a
  classmate looks the same wherever they turn up. It goes top-left on a
  dark coin: Rookie's emblem is grey by design and vanished against a
  dark avatar, and the coin gives every rank the same footprint. In the
  flow it would not fit — a row already carries a place marker, a name
  and a stat line, and a 320px phone has no spare width.
  **There is no level number beside it, and there was.** A small blue
  one sat in the opposite corner, asked for on the Virtual Room lobby
  and then asked against everywhere ("forget the little level thing next
  to the characters, I do like the rank icon though"). A rank already
  says roughly where somebody is, the Level board ranks on the number
  itself so it is already printed on the row, and two marks on one 42px
  character is one too many. Somebody below Rookie gets nothing, which
  is correct: there is no rank to show and a placeholder would say
  otherwise. `check-behaviour` and `check-vroom` both assert its
  absence, so it cannot come back by accident.
  **Two row builders for one idea is how a fix misses the screen it
  matters most on.** The three rankings boards had their *own* row
  markup and never called `decorateAvatar()` — so when the level chip
  was taken off everywhere, it stayed on the boards, which is the place
  anyone actually looks at other people, and the rank emblem never
  arrived there at all. Checking the builder is not checking the screen:
  `check-behaviour` asserts against a real `.rank-row` now, built by the
  app, rather than against `decorateAvatar()` in isolation.

### The race line and the end of a run

- **THE RACE LINE POSITIONS BY THE LEFT EDGE, NOT THE CENTRE, and its
  markers used to have nowhere to go.** Everybody at the same progress
  was drawn at the same coordinate, one on top of the other, and a
  lobby has no size limit — so crowded was the default rather than the
  edge case. Each marker keeps its EXACT horizontal position (that is
  the whole point of a line) and moves VERTICALLY into one of three
  lanes when somebody is already within a marker's width of it. Lanes
  are assigned in progress order so the hunt only has to look at the
  markers immediately behind; the DOM order stays join order, which is
  what keeps each person's colour stable.
- **Lane spacing has to beat the marker's own diameter or they touch.**
  1.28rem against a 1.7rem marker overlapped by 7px, and the hairline
  pointer drawn between them was invisible behind the next marker — so
  the pointer came out rather than being left in as decoration nobody
  can see. 1.62rem against 1.5rem clears them.
- **No labels on the markers.** At this size a label under one lane
  lands on the one below it. The characters ARE the identification —
  a classmate's avatar is the one they carry on the boards — and your
  own marker, the one thing an avatar cannot tell you, gets a white
  ring.
- **`buildResultsLevelBlock()` is the XP-and-level card at the end of
  EVERY mode**, drill, exam, game, daily question and Virtual Room
  alike. It is built from `levelProgress()` like every other bar in the
  app, fills from where the run started to where it ended, and wraps
  into the next level if the run crossed one (fill to 100%, reset with
  the transition off for one committed frame, fill again). `runFill()`
  is called by the caller AFTER the panel is on the stage, for the same
  reason the Profile bar's is: a width set in the same tick as the
  element has nothing to transition from.
- **The Virtual Room reuses that run's numbers rather than recomputing
  them.** A Virtual Room run goes through `summarize()` for all its side
  effects and then has its screen replaced, so the XP is genuinely
  awarded and was simply never shown. `lastRunXpEarned` /
  `lastRunPointsAfter` carry it across, so the two screens cannot
  disagree.
- **The race bar is hidden at the TOP of `renderResults`, before any
  early return.** It used to be the last thing that function did, past
  a `return` that fires on every snapshot once the standings are up —
  so a results screen rebuilt or re-entered with the results already
  out kept the line on screen. While people are still working it stays,
  which is the other half of the same request.
- **Both Virtual Room end screens set `forceHideBottomTabs`**, and they
  have to set it AFTER `setActiveNav()`, which clears the flag on the
  way into every screen. `summarize()` already did this for the ordinary
  results screen; these two were the one place the bar came back inside
  a test.

### Badges

- **Badge detection diffs the real list either side of the recording
  calls** in `summarize()`, rather than trusting any one of them to
  report it. `recordMultiUnitPerfectsIfEligible` does return a
  `newlyStarred` list, but only for multi-unit runs — a single-unit run
  and a Virtual Room race cross the threshold by different paths, and a
  badge that only celebrates on some of them is worse than one that never
  celebrates at all. `tools/check-behaviour.py` runs all four routes.
- **The cutscene queue is on `store`, not passed along.** There is no
  fixed route from a test to Home — Home, Profile and the tab bar are all
  reachable from the results screen — so `store.pendingBadgeUnlocks`
  survives the trip and a relaunch. It **defaults to empty** for an
  existing account, per the `applyLoadedData` rule: somebody who mastered
  four units last month must not be met by four cutscenes on the first
  launch after this ships.
- **`playQueuedBadgeCutscenes()` re-checks its preconditions per badge**,
  not once: it runs for several seconds, and a splash, a generating
  overlay or a tour can appear inside that window. It refuses on any
  screen but Home by testing `dataset.screen`, which is set in exactly two
  places in the file, so every other screen fails by construction.
- **`muteBanners` mutes the cutscene too**, and clears the queue while
  doing it — a muted badge that stayed queued would ambush somebody weeks
  later if they unmuted. `reduceMotion` gets the same words as a static
  note rather than the spin, because the global
  `[data-reduce-motion="true"] *{animation:none}` would otherwise strip
  the keyframes and leave a badge sitting motionless behind a dim.
- **SIXTEEN HAND-BUILT BADGES — generation was the mistake, not the
  settings.** Every version before this one grew the silhouette from a
  hash of the unit name (even angles, jittered radii, a pattern of near
  and far points), and each round came back worse than the last, ending
  at *"the badges look worse and worse by the turn. Let's do this. Start
  fresh with the actual badges themselves and redo them."* A hash can
  make sixteen DIFFERENT polygons; it cannot make sixteen DESIGNED ones,
  and the reference is sixteen designed ones — a ringed heptagon, a
  diamond, a trefoil of spheres, a run of peaks, a keystone. Those were
  drawn, so `BADGE_SHAPE` is drawn too: sixteen hand-authored paths,
  each with its own centre and its own list of channel cuts.
- **The recipe, read off the reference rather than invented.** A dark
  keyline round the outside, and it IS the dominant edge; a broad silver
  band of even width following the silhouette inside it; the colour as
  flat PLATES inset within that band, each with its own thin dark edge;
  and silver CHANNELS between the plates. That is the whole
  construction, and it is what makes the inside of a gym badge read as
  assembled rather than printed. An earlier pass here concluded "black
  is not a material" and led with the silver; looked at properly the
  reference leads with the dark line, which is why that set dissolved
  into the case.
- **The channels are the band showing through, not lines drawn on the
  colour**, so each one is clipped to the PLATE and never to the whole
  token. Unclipped they cut the silver band as well and the badge falls
  to pieces. They are a flat `#9FACBA` rather than a ramp — see the
  zero-width bounding box below.
- **A linear gradient resolves against its path's bounding box, and a
  straight line's box is zero-wide in one axis**, so the ramp
  degenerates and the path paints as its first stop, which is usually
  black. This has now bitten three times in this file: the old badge
  leading, the rank glows, and these channels. Anything that is a line
  gets a flat colour; anything that needs a ramp gets a shape with area.
- **The plate is the silhouette scaled about ITS OWN centre**, which is
  what `c:` in each `BADGE_SHAPE` entry is for —
  `translate(cx cy) scale(.8) translate(-cx -cy)`. Scaling about the
  128-unit frame's centre instead leaves the inset thick on one side and
  thin on the other for every shape not centred in its own box; the
  crescent and the trefoil showed it at a glance.
- **A lobed silhouette must be ONE outline, not stacked circles.** The
  trefoil and the quatrefoil were three and four overlapping discs, and
  stroking that strokes every internal seam: what should be a single
  smooth outline came out with lines running through it. Both are one
  arc path through the computed intersections now.
- **Two subpaths winding opposite ways render HOLLOW** under the default
  nonzero fill. A medal drawn as a body plus a ribbon came out as an
  empty ring; it is a rounded triangle now.
- **Corners are rounded, on the badge AND on its slot.** A hard-cornered
  polygon cut into a lining reads as a vector path, which is what *"the
  empty cut outs look bad and inconsistent and not very smooth"* was
  pointing at. Every vertex in `BADGE_SHAPE` is a `Q` rather than an
  `L`, and the slot is the same path, so the two cannot stop fitting
  each other — it is one outline.
- **No gloss streak, no sparkle, no glass, and no motif.** All four were
  tried across three rounds and each came back: *"too shiny"*, and a
  mark *"stuck on top of them ... a lot of upside down v's"*. The
  channels ARE the interior design; there is nothing laid on the colour.
- **Look at the rendered shape before believing its name.** Hand-drawing
  does not exempt anything from this — the medal rendered hollow, the
  lobed pair rendered seamed, and the inset rendered lopsided, all of
  which were invisible in the path data and obvious the moment sixteen
  were rendered side by side. That render is a thirty-second check and
  it is the only reason any of the three got fixed.
- **`badgeHexRgb` takes `rgb(r,g,b)` as well as `#RRGGBB`, and that is
  load-bearing.** The secondary colour IS a `badgeShade()` result for
  half the sixteen units, so anything that shades it a second time
  parsed `"rgb(..."` as hex, got NaN for all three channels and painted
  the plate BLACK. Both helpers sit above `badgeThemeFor`, and **the
  rank emblems depend on them too** — removing them along with a badge
  rewrite threw a ReferenceError on the whole Ladder tab.
- **The colour NODS at the unit; the shape does not.** `UNIT_BADGE_THEME`
  hand-assigns one of the twenty-one `BADGE_FAMILY` colours per unit —
  gold for Ethics, police blue for Professional Policing, gunmetal for
  Arrest/Search/Seizure, amber for Missing and Exploited Children. That
  is the whole of the relevance, and it is deliberate: a badge that
  *draws* its subject was rejected twice, but a set where the colour
  means nothing at all is what made an earlier set read as sixteen
  arbitrary objects. The reference works the same way — the red gym
  badges are fire and none of them is a picture of a flame.
  **Sixteen DISTINCT families, and that is checkable rather than
  assumed.** A hash into a sixteen-entry table is sixteen independent
  draws from sixteen slots, which lands about six of them on a colour
  another badge already has — reported as "a lot of repeating colours",
  and it was. The families are named rather than evenly spaced round the
  hue wheel: even steps is the obvious answer and it produces four
  greens out of sixteen, because green occupies about a sixth of the
  wheel and reads as one colour whatever the spacing says.
- **THE DRAGON WAS THE ONE THAT DID NOT BELONG TO THE SET, and the
  fault was mostly SIZE.** Reported as *"the worst looking one right
  now"*. Measured against the other fifteen, its head was an 11.6x13.2
  ellipse where every other character's is about 9x9.5 — so it filled
  its tile edge to edge while the rest sat inside theirs, and a head
  that big leaves no room for shoulders, so it read as a face pressed
  against the glass. The second fault was the muzzle: a pale pink
  ellipse laid flat on the front of the face with two round dots in it
  is a pig's snout whatever else is around it. A dragon's snout comes
  FORWARD and DOWN off the skull and is the same colour as the rest of
  it, with a lit top plane, a bridge down the centre, angled nostril
  slits and a jaw beneath.
  Two smaller ones worth keeping: horns swept OUT as well as back, wide
  at the base and with growth rings (nearly-parallel tapered triangles
  read as rabbit ears), and scales along the BROW where a raised edge
  would actually catch light rather than parked on the cheeks, where
  they read as dirt.
- **`UNIT_BADGE_SHAPE` is a pairing, not a lottery**, for that same
  reason: a hash into the shape table doubles some up and skips others,
  which is "they all have the same common" in another form. A unit the
  table does not know falls back to the hash rather than to null — the
  leaderboard once lost three classmates to a builder returning null for
  an id it did not know.
- **No enamel colour may be close to the setting.** Arrest, Search and
  Seizure was gunmetal, for steel, and inside a silver rim it came out
  as a blank piece of metal with no badge in it. It is a much darker
  steel-blue now: the relevance survives, the collision does not. Check
  any new family against the silver before adding it.
- **Never one colour field.** A plate and its channels are two tones,
  never one. A flat disc of a single colour with a mark on it is
  precisely the thing the reference never does.
- **Every badge has a slot, and the slot is drawn whether the badge is
  earned or not.** That is the other half of the reference: each badge
  sits in a recess cut to its own outline, which is why an empty slot
  still tells you the shape of what goes in it and a filled one reads as
  something *placed*. A recess lit from the top-left has its shadow on
  the TOP-LEFT inner edge and its catch-light on the bottom-right, which
  is the opposite of a raised object and the whole reason it reads as a
  hole. Two copies of the outline, offset in opposite directions and
  clipped to it, do that without a filter — filters are the one SVG
  feature that has bitten this app on real iOS hardware.
  The token is scaled to `.945` inside its slot: exactly the size of the
  hole and it looks printed on.
- **The recess is not black.** It is the lining seen in shadow, so a
  desaturated blue-grey in the same family as the metal, with wide
  low-opacity strokes for the lip. A hairline reads as a drawn outline;
  material giving way is soft.
- **An unearned badge is its empty slot.** Not an outline, not a solid
  silhouette on the tray, not an empty setting — all three were tried
  and the second reference photo (a partly-filled case) settled it: you
  read the shape of the hole and nothing else, which is what makes an
  earned one beside it look placed.
- **Gradient ids inside a generated SVG must be unique per instance.**
  Sixteen badges on one screen referencing `url(#badge-grad)` is one
  shared definition and fifteen wrong fills; `badgeSvgSeq` exists for
  that, `rankEmblemSeq` does the same job for the rank emblems, and the
  same applies to every `clipPath` id.
- **Two columns on a narrow phone, three from 27rem, four from 40rem.**
  Three across a 375px screen leaves each name 72px and
  "Professionalism" alone is 89px, so `overflow-wrap:anywhere` was
  breaking it mid-word ("Multiculturalis / m"). `break-word` is the
  right value — it breaks only a word that cannot fit at all — but the
  real fix is the column count, measured per device.
- **A grid of cards needs `minmax(0, 1fr)`, never a bare `1fr`** — the
  same trap `.pick` already documents. The badge grid's tracks sized
  themselves to the longest unbreakable word ("Multiculturalism") and ran
  391px wide inside a 375px phone. **The screenshots did not show it**,
  because the overflow scrolls sideways rather than clipping; the sweep
  did, and only because the Profile tabs were added to `SCREENS`.
- **THERE IS ONE UNIT-CARD BUILDER, `appendUnitProgress(row, name)`,
  AND BOTH SCREENS THAT DRAW UNIT CARDS CALL IT.** The test setup
  screen and the Virtual Room's unit list each had their own markup;
  the Virtual Room's was a checkbox, a name and a question count and
  nothing else, so its units looked like a different app's. *"It should
  look just how the drill mode unit cards look. All modes should have
  that same look."* This is the same mistake the rankings boards made
  with `decorateAvatar()` — the fix goes in the builder, the screen
  that matters never calls it — so the cure is the same: one function,
  both call sites. A new screen that lists units calls it too.
- **EVERY UNIT CARD CARRIES THE SAME INSTRUMENT, A MASTERED ONE
  INCLUDED.** It used to drop both the bar and the count once the
  badge was earned and show a lone badge, which left a hole exactly
  where every other card in the grid has its bar — the one card that
  did not match. *"They should all look the same."* A mastered card
  now reads `35 / 35` on a full bar.
  **This is not a revert of the earlier decision, and the difference
  matters.** What came off before was a card reading "Mastered —
  1,204": a word repeating what the badge already says, beside a
  running count of something nobody is working towards. A capped
  `35 / 35` says the unit is done in the same language every other
  card uses for how far along it is, and it stops counting.
- **LEAVING UNIT SELECTION DROPS THE PICKS, and `cfg` is why this came
back.** *"If I select units and then hit back, if I go back into
another mode or the same mode, the units I selected should not be
marked as selected."* `cfg` is a module-level object, so a selection
survived in memory for the whole session. Build 100 stopped it
persisting across LAUNCHES by dropping the `localStorage` restore in
`applySaved()` — a different thing, which is why the report returned.
`cfg.units = []` now happens at the top of **`showModeSelect()`**, not
on entry to `showSetup()`: `showSetup()` is also how you return after
popping over to Profile or Settings mid-selection
(`returnToSetupAfterTabs`), and losing your picks to a tab round trip
would be its own bug. Backing out goes through mode select; a tab round
trip does not.

**THE "Taking: X, Y" LINE LIVES IN THE START SHEET, and it is the same
element that was supposed to come off the panel.** *"It says what you
are taking under the unit cards in white, REMOVE FOR ALL MODES"* —
build 100 removed `.unit-selection-summary` and left `.aboutTake`
rendering, so it was still there. It was then asked for the other way
round: *"in the start button thing, show which units you have selected
there."* Same line, right place. It is appended to `.sheet-summary`
with `flex:0 0 100%` — that row is a `space-between` flex, so a third
child lands as a narrow third column beside the mode and the count; a
full set of unit names needs its own row and several lines.

**THE UNIT CARD MEASURES ONE THING IN EVERY MODE: the badge, and
  hundos towards `BADGE_THRESHOLD`.** It is not mode-dependent and must not become so
  again. A hundo is a full-unit 100% run and `unitPerfectCount` reads
  `store.unitPerfects`, which Drill, Exam, Game and the Virtual Room
  all write to — so there has only ever been one number for the card to
  report. Game used to show its own star and "0/3 speeds beaten"
  instead, which made the same unit read as two different amounts of
  progress depending on the mode picked one screen earlier. Reported:
  *"it's not based on modes, it just needs the badge icon and the 0/35,
  because the 35 hundos counts from any mode. That goes for any
  mode."* The Game star still exists and is still earned — it is on the
  stats popover via `totalStarsFor("game")` — it is simply not what
  this card is for. The badge leads the row at every width now; the
  text-first order was Game's, and existed only because Game's marker
  was an invisible-until-earned star that still reserved its width.

- **`SCREENS` entries may carry arguments** (`"showProfile('badges')"`).
  Profile is four tabs and a bare `showProfile()` lays out only one of
  them, so three quarters of that screen had no gate at all.

---

## Friends, the Virtual Room and the banners

Everything in this section postdates build 94 and was undocumented until
161.

### publicId

- **A ROW IS KEYED BY `publicId`, NEVER BY THE SYNC CODE.** It used to
  be the code, and the code IS the account — on a collection that is
  world-readable AND listable, because that is how forty phones draw
  the board. So every row published that way was a classmate's account
  key sitting in public. `publicIdOf()` mints a twelve-character
  identifier that means nothing to anybody, and `check-sync` section 7
  asserts the code appears nowhere in `leaderboard` or `vrooms`, as a
  document id or in any field.
- **`migrateLeaderboardKey()` deletes the old row once**, on the
  owner's next launch, guarded by `store.leaderboardKeyMigrated`. It is
  the only thing that can: that device is the last holder of the key to
  a document nobody else can ever address. Checked against the live
  board in build 161 — 7 legacy rows were still there, all belonging to
  people who had not yet launched a build containing it. They clear
  themselves as those devices update; `tools/firestore-admin.py prune`
  exists to force it and was deliberately NOT run, because the app
  resolving it on its own costs nobody a place on the board.
- **The retirement in `setSyncCode()` retires the OLD PUBLIC ID**, not
  the old sync code — linking pulls the other account's store down,
  which brings its publicId with it, so the id this device was
  publishing under is the one left stranded. Retiring by the code would
  delete nothing.

### Friends

- **A FRIEND CODE IS NOT THE SYNC CODE and must never be derivable from
  it.** Different alphabet, different length (`XXX-XXX`), no prefix and
  no hash of one from the other. Losing or rotating a friend code must
  not touch the account, and nothing keyed by a friend code may ever
  return a sync code.
- **The friends graph rides in your OWN leaderboard row**, in short
  fields (`fcode`, `freq`, `facc`, `inv`) because that document is
  fetched by every client on every snapshot and there are forty of
  them. Your row says who you have asked and who you have accepted;
  nobody writes to anybody else's.
- **Friends is its own card on Profile**, not a button in the Class 26E
  box — see **Conventions**.
- **The friends screen leads with people, not admin** — also
  **Conventions**.
- **ONLINE MEANS THE APP IS OPEN, and for a while it meant something
  else.** `isOnline()` read `lastModified` on the board row, which only
  moves when somebody PUSHES — that is, when they answer a question. So
  a classmate sitting on Home for ten minutes read as offline, and
  somebody who answered four minutes ago and then closed the app read
  as online. "Who is online" was really "who answered something
  recently", which is not the question a friends list is for. There is
  a heartbeat now: `sendHeartbeat()` writes `seenAt` and nothing else,
  every `HEARTBEAT_MS` (4 min), started from `showHome()` rather than
  at boot. `isOnline()` takes `max(seenAt, lastModified)` against
  `ONLINE_WINDOW_MS` (5 min), and **the `lastModified` fallback is
  load-bearing**: everybody is on an older build for the first day
  after a ship, and without it the whole class reads offline until each
  phone updates.
- **EVERY GUARD ON THE HEARTBEAT IS A FIRESTORE BILL.** It is the only
  periodic write in the app, and forty phones on a four-minute timer is
  ~14k writes a day against a 20k free-tier ceiling the ordinary pushes
  also draw on. So it fires only while the tab is `visible` (an app
  left open on a desk all day is exactly what would spend the quota),
  only with `leaderboardOptIn` on (there is no row to write to
  otherwise), only with a sync code, and never twice inside its own
  interval. It uses `update()`, never `set()` — a heartbeat must not be
  able to create a half-built row. `check-friends.py` section 10
  measures all five, because a guard that silently stopped working
  would break nothing visible; it would just spend the money.
- **`pushToCloud()` republishes `seenAt`, and it has to.** `set()`
  replaces the whole document, so a stats push landing a second after a
  heartbeat would delete `seenAt` and drop the person offline
  mid-session. It also resets `lastHeartbeatAt`, since pushing IS
  activity.
- **The dot has to be good for something.** An online indicator that
  leads nowhere is a light on a dashboard, so an online friend's row
  carries one extra action — Invite — and an offline friend's does not.
  An invite is live for `LOBBY_INVITE_TTL_MS` (30 min) and lands as a
  banner on their Home, so sending one to somebody who is not in the
  app is a room you then sit in alone until it expires.
  `inviteFriendToNewLobby()` **makes the room itself**: an invite is
  addressed to a ROOM CODE and the Friends screen has none
  (`openInviteFriendsSheet()` is handed one because it is only ever
  opened from inside a lobby), so the invite is sent from inside
  `createVirtualRoomLobby()`'s own `.then()`, where the code first
  exists. Already in a room, it invites into THAT one rather than
  abandoning a lobby full of people for a new one.
- **Two text buttons do not fit one phone row, and the wrap is the
  intended answer.** Measured: a 375px phone leaves ~289px inside the
  panel, and avatar + a 7.5rem text floor + two 5.5rem buttons wants
  ~366. `.friend-row` is `flex-wrap:wrap` with `min-width` on the text
  for exactly this — it wraps rather than squashing, the same as
  Accept/Decline already do. An online row is therefore two lines on a
  phone and one on a tablet. Don't "fix" it by shrinking the text
  floor; that is how "Alex" became "A".
- **`decorateAvatar()` takes the ELEMENT, not a character id.** Handing
  it an id threw and took the whole screen down; `avatarSpanFor(entry)`
  is the builder that gets it right.
- **The live listener must not rebuild the screen under somebody's
  fingers.** `friendsViewSignature()` skips a redraw when nothing
  relevant changed, and the redraw is refused outright while
  `.friend-add-input` is focused or part-typed. Measured on the build
  that got this wrong: the field came back EMPTY with focus lost, 15
  times. It also requires `metadata.fromCache === false` before letting
  an empty snapshot replace the board — the same rule as
  `handleRemoteReset()`, for the same reason.

### The banners

- **ONE BUILDER, THREE LOOKS THAT CANNOT BE CONFUSED.**
  `buildAppBanner()` with `BANNER_KINDS`: `vroom` is blue with a room,
  `friend` is green with a person, `account` is amber with a key. The
  tag AND the colour, because one survives being read in a hurry and
  the other survives somebody who cannot tell those colours apart.
  Asked for directly after two banners read as the same banner twice.
- **Precedence when several are waiting**: Virtual Room first (a lobby
  is filling), then friends, then the account one (it can wait a
  launch). Each checks for the others by id before rendering.
- **They live on `<body>`, never inside `#stage`.** `#stage` animates,
  and a transform on an ancestor re-parents a fixed element's
  containing block. Each takes a one-shot `MutationObserver` on
  `#stage` that removes it on the next screen change.
- **`.daily-alert` carries `pointer-events:none`**, which is right for
  a passive banner and fatal for one with buttons — `.app-banner` sets
  it back to `auto`. The Join button measured perfectly and was
  unpressable for a week because of it, which is also why every check
  on these uses a real hit-tested tap: `element.click()` ignores
  pointer-events entirely and cannot catch this.
- **`attachInviteWatcher()` attaches at BOOT, not on the first visit to
  Home.** It used to attach inside `showHome()`, so the first snapshot
  only began arriving once somebody was already looking at the screen
  the banner appears on — which is why an invite showed up "late": the
  wait was the subscription, not the network.

### The Virtual Room

- **Unit selection is reachable ONLY from inside a lobby.** Match
  settings opens `showVirtualRoomSetup(editRoom)` in edit mode — the
  ordinary unit screen, with the bottom bar offering only that options
  sheet and a back-to-lobby link, and `window.forceHideBottomTabs` set
  while editing.
- **`addEventListener` passes the EVENT as argument one.** Wiring the
  Match settings button as `addEventListener("click",
  showVirtualRoomSetup)` handed it a PointerEvent as `editRoom` and
  broke creating a lobby outright. Never pass a function with optional
  parameters by name.
- **Two game types**: `race` (the original) and `tug` (Tug of War).
  `beginTugMatch()` must call `detachVroomListener()` — the race path
  does, and tug not doing so left the lobby listener live underneath
  the match.
- **The two game buttons are CARDS, not pills, and that was a report.**
  As outline pills the unselected one had no surface of its own and was
  read as missing — "they don't look clickable and the one that isn't
  selected looks like it's not there". Two equal cards now, each with
  its own emblem (`buildVroomModeArt`) and a tick on the chosen one.
  The tug emblem is **a row of slanted strands**, arrived at after
  three failures: a hatched straight band inside an outline reads as a
  striped PILL, a sagging curve with ticks reads as a beaded garland,
  and a plain thick line reads as a cable.

#### Tug of War

**IT IS NOT LOCKSTEP ROUNDS ANY MORE, and the whole engine was
replaced.** It shipped with everybody on the same question, the host
resolving each round, and the rope moving by that round's difference.
Asked for directly: *"it's not turn based, the teams will work through
the questions, and whoever is getting through them faster will start to
pull the rope, so each question you get one chance."*

- **Everybody walks the same bank at their own speed.** The order is
  still `shuffleSeeded(pool, data.startAt)` so nobody gets an easier
  deck, but nobody waits. Each client publishes
  `tug.progress.<myKey> = {pos, correct, done}` as a FIELD write —
  never a whole-object set, or two people finishing in the same second
  overwrite each other and the rope jumps backwards.
- **The rope is `tugTeamScore(a) − tugTeamScore(b)`, and the team score
  is an AVERAGE per person.** A total would let a team of two out-pull
  a team of one by arithmetic rather than by play. A 2v1 room is
  lopsided in ability, which is honest; lopsided by construction is
  not.
- **The question count sets the length, and there is NO time-limit
  control for tug** — `timeSect.hidden` in the sheet's `refresh()`.
  `tugPace(n)` divides `TUG_TARGET_MS` (7 min) by the bank to get the
  OPENING pace, clamped to 7–35s. Ten questions open at 35s and run
  about 5 min, 29 at 14.5s over 6 min, 80 at the floor over 9 min —
  *"if I select 80 questions though, make it so that it does last about
  that long"*, so eighty running LONGER than the target is the right
  way round, not a miss. `vroomTimeLimit` keeps its value underneath,
  so switching back to Race restores it.
- **THE SPEED-UP IS A LATE EVENT, NOT A GRADIENT YOU ARE INSIDE FROM
  QUESTION ONE.** A straight ramp from the first question was the first
  draft and it is not what was asked for: *"based on the time you
  select that's how fast the questions start out and towards the end if
  there's no winner questions speed up."* So the opening pace HOLDS for
  `TUG_HOLD_SHARE` (60%) of the match and only then ramps. The
  tightening is the thing that stops a match that will not settle.
- **`TUG_FLOOR_MS` IS 7s, AND IT IS A FLOOR THE MATCH REACHES, NOT A
  SPEED IT RUNS AT** — *"lowest time will be 7 seconds but that's ONLY
  if it takes that long to decide a winner."* A bank big enough that
  7 min ÷ n falls below it simply opens there and never tightens.
- **`TUG_MAX_MS` caps the match at 10 minutes, because the bank is not
  capped.** "All units" is several hundred questions and at the floor
  that is a twenty-five minute match. Past that point the questions
  stop setting the length and the rope settles it: whoever is ahead at
  ten minutes has won. Eighty questions come in at about nine, so the
  ceiling never touches the case it was written around.
- **THE CLOCK IS A FUNCTION OF ELAPSED MATCH TIME, NOT OF YOUR OWN
  INDEX.** Basing it on how far you have got hands the leader the
  shortest clocks and the straggler the longest, which is a rubber
  band, not a race. `tugQuestionMs(now − startAt, count)`.
- **One chance.** The tap locks every choice, marks it, shows the right
  one if you were wrong, and moves on after a beat. Running out of
  clock is a miss, not a pause.
- **`renderTugScreen` must refuse to redraw while `tugAdvanceTimer` is
  set.** Your own progress write echoes back as a snapshot within a
  frame or two and `tugMyPos` has already moved, so without the guard
  that echo rebuilds the panel instantly and the beat where you are
  told the right answer never happens. Caught by `check-vroom`, which
  found every choice enabled 120ms after a tap.
- **`tugWinGap(count)` scales with the bank** — a fifth of it, floored
  at 3 and capped at 12. The old flat 5 would be crossed inside the
  first minute of an eighty-question match.
- **A DRAW IS A REAL OUTCOME.** The rope used to end only by being
  pulled clear, so there was always a side; it can now also run out of
  questions or out of pace dead centre, and `showTugResult` says
  "Nobody moved it" rather than telling both halves of the room they
  lost.
- **The rope is drawn as a rope and that took a report to get right.**
  A repeating diagonal gradient IS the twist (a `border-radius` clips a
  background, so there is no `overflow:hidden` and therefore nothing to
  clip the knot), an inset highlight and shadow bend it into a
  cylinder, and a loop at each end says somebody is holding it. The tan
  `#7A6247` is deliberately NOT a theme token — a themed rope is a
  coloured bar — and the team tints stay at the two ends, which is what
  says who is pulling. Names and scores sit ABOVE it, not either side:
  side by side they took most of a phone's width and left the rope
  about a third of the screen. Capped at `34rem` from tablet up, or a
  13" iPad renders a metre of bar.
#### The end-of-match cutscene

- **A SCENE, NOT A PORTRAIT.** The first version was one big character
  centred on black with their name under it, and it was read for
  exactly what that is: *"it looks too much like the void character
  unlock"*. A race ends on a **podium** of the top three and a tug ends
  on the **whole winning side**, both of which say something a single
  portrait cannot — who else was close, and that two people won it
  together.
- **On the podium, height IS the placing**, so the DOM order is second,
  first, third: the tallest block has to be in the middle or it is not
  a podium. They rise third → second → first, so the winner lands last
  and the confetti goes with it. The shape follows who was actually
  there — a room of two gets two blocks — rather than always drawing
  three with an empty plinth.
- **The tug scene carries the rope**, drawn with the same twist the
  match itself used, so it is the thing they were pulling rather than a
  generic banner. A draw has no side, so it shows everyone still in.
- **It is skippable, and it honours the same two switches every other
  celebration does.** `muteBanners` skips it outright; `reduceMotion`
  keeps the reveal and drops the wind-up, rather than leaving a screen
  that sits still for five seconds because the global
  `[data-reduce-motion="true"] *{animation:none}` rule stripped the
  keyframes out from under it.
- **Every path calls `done()`** — skipped, muted, finished, or the
  overlay torn off by a screen change. The thing after it is the
  results screen, so a cutscene that can swallow its own callback is a
  match that never ends.
- **IT DROPS ITS `id` AT HANDOVER, NOT AT THE END OF THE FADE.** It
  fades for 400ms before it is removed, and for those 400ms it was
  still what `getElementById` returned — so a second cutscene starting
  in that window found the dying one and believed itself already up,
  and anything asking "is a cutscene up?" got yes after it had handed
  over. Anything querying the live cutscene must scope to
  `#vroom-cutscene`, not the document; a bare document query finds the
  corpse.
- **The hidden reveal must be OUT OF FLOW.** At `opacity:0` it still
  reserved its own ~220px, which pushed the wind-up line and dots well
  above the middle with nothing under them — it read as a screen that
  had failed to load rather than a pause before a reveal.
- **It plays at the moment the match ends, not inside
  `showVirtualRoomResults()`.** That screen is also reached by coming
  back from the lobby, and a cutscene that replays every time you
  glance at the results is one nobody wants twice.
- `check-vroom` section 11 is the gate, and it asserts SHAPE — how many
  figures, and that the blocks run 2/1/3 — never what anybody is
  called.

#### Leaving a room

- **LEAVING HAS TO ACTUALLY LEAVE, and for a long time nothing removed
  a participant from a room document at all.** "Leave lobby" detached a
  listener and walked away; pause → Exit test did not touch the room.
  Both gates in this app wait for EVERYONE with no timeout — the lobby
  before it starts, the finale before it reveals — so one person walking
  out stranded the rest for good. `leaveVirtualRoom()` is the single
  exit every path goes through: it deletes the participant and its tug
  rows, records `lastLeave`, and detaches the listeners FIRST so the
  device's own delete does not come back as a snapshot and get rendered
  against a room it has left.
- **THE HOST IS THE EARLIEST JOINER, COMPUTED, NOT STORED.** There was
  no `host` field on the room at all — only a local `vroomIsHost` flag
  set when you created it — so a host who left produced a room with NO
  host, and the two things only a host does (firing the auto-start,
  deciding a tug match is over) never happened again. The room was
  bricked and looked fine. `vroomHostKeyOf()` derives it from join
  order, the same rule the tug teams already use, so the next person is
  promoted by arithmetic with no handoff write to race against.
  `syncVroomHost(data)` re-derives it on every snapshot. **The key
  tie-break in the sort is load-bearing**: two people whose `joinedAt`
  collides must not both believe they are in charge.
- **The leave banner reads a `lastLeave` FIELD, not a diff of
  successive snapshots.** Snapshots coalesce and arrive out of order,
  so a banner that depends on catching the exact moment between two of
  them is a banner that sometimes does not appear. `vroomLastLeaveSeen`
  keeps it to once per departure and stops somebody who joined later
  being told about a person who left before they arrived.
- **The waiting screen's way out is Pause, and there is deliberately no
  Back to lobby or Back to Home on it** — *"there's no button at the
  bottom to return to lobby/return to main menu when you are waiting
  for people to finish … you'd need to hit pause and then hit leave"*.
  `vroomAwaitingOthers` makes Pause ask a different question there,
  because your own run is over: your score is already banked, so the
  copy says you only lose seeing everyone else's results rather than
  borrowing confirmExitTest's run-losing warning.
- **`check-vroom` section 10 is the gate**, and the assertion the old
  build cannot satisfy is the last one: the host walks out and the
  match still starts.

- **`check-vroom` section 9 is the gate**, and the assertion that
  matters is the one lockstep cannot satisfy: one device gets through
  three questions while the other answers nothing, and the rope moves
  for it. Run it `--against` a copy carrying the old tug engine, not
  just an old `index.html` — the lobby fix landed in the same build, so
  an older file fails section 1 and never reaches section 9.
- **Question order comes from `shuffleSeeded(pool, data.startAt)`**, so
  every client gets the same order from the room's own shared
  timestamp. Never shuffle locally.
- **`.invite-overlay` starts at `opacity:0`** until `invite-overlay-show`
  lands in a rAF. Every measurement of the Match settings sheet passed
  while it was invisible; the screenshot caught it.
- **An invite sheet built from `ids.map(id => rows[id])` must not
  `.filter(Boolean)` silently** — a friend whose board row has not
  loaded vanishes from the list with nothing to say so. Reported as
  "the invite list is still empty".

### The badge cutscene

- **`BADGE_CUTSCENE_MS` is the app's number and the gate reads it off
  the page.** `check-behaviour` hardcoded 2600 and went red on the
  build that lengthened it — a gate failing the app for being right.
- **Never name a local `theme`.** It shadows the app's settings object
  for the whole function body and puts `theme.muteBanners` in its
  temporal dead zone; the cutscene threw a ReferenceError on every
  unlock. `badgeThemeFor()`'s result is `badgeTheme`.

---

## The Leaderboard's boards

`RANKING_BOARDS` is the whole definition of a board — its tab label,
what it ranks on, how a row reads, and its blurb. Three of them: This
Week, Level, Hundos.

- **A FOURTH BOARD WAS BUILT AND TAKEN BACK OUT, and the reasoning is
  worth keeping even though the board is not.** Accuracy — lifetime
  correct over lifetime answered, with a 100-question floor so three
  lucky answers could not top the class — shipped in build 160 and was
  removed in 161 on one line: *"remove the accuracy one, I don't like
  it."* Don't rebuild it without being asked.
  It came with machinery that also went: a board could carry
  `value(entry)` and `eligible(entry)` for a number that is not a
  published field, plus `emptyNote` and `barredNote(entry)` for a board
  with a qualifying bar. All of it was removed rather than left
  unreachable — this file already carries enough dead CSS that "check
  the selector is reachable before assuming your edit was wrong" is a
  documented rule.
- **The real constraint it was trying to solve is still true**, and is
  the note on the Level board: badges, hundos and level are all
  LIFETIME totals, so all three put the same people in the same order
  and none of them ever really moves. This Week is the only one a new
  person can win. Any fourth board worth adding has to move.
- **A new ranked number needs publishing in `pushToCloud()` AND
  synthesising in `liveEntries()`.** The first puts everyone else on
  the board; the second puts YOU on it, drawn from the local store so
  your row is right the instant a test ends rather than 2.5s later when
  the push lands. Leaving it out of `liveEntries()` shows the whole
  class except you.
- **Settings' rankings hint is BUILT FROM `RANKING_BOARDS`, not written
  out.** It read "three ways — level, badges and perfect tests" while
  the boards were This Week, Level and Hundos: the count was right by
  accident and not one of the three names was. It now says the count
  and the names the boards actually have, which is also why removing a
  board needs no copy edit.

---

## Shipping a change

`APP_BUILD` in `index.html` and `build` in `version.json` **must be bumped
together, to the same value**, on every deploy. They are two halves of one
comparison: `version.json` is what the server serves, `APP_BUILD` is baked into
whatever copy is running.

- Bump only `version.json` → everyone gets a banner reloading can never clear.
- Bump only `APP_BUILD` → nobody is ever told there's an update.

`frameId` is the exception: it is deliberately **not** compared against
anything in `index.html`, only against what each device has acknowledged
(`class26e.frame.ok`). Bumping it alone is correct, and is how you re-prompt
everyone after an icon or app-name change. `frameNote` overrides the message.
Ship a **new** deployment (different URL) with `frameId: ""` — that disables
the notice, which is right when every install is fresh and already correct.

**A notice sits at the TOP of the screen, and where exactly is measured.**
It used to sit at the bottom, above the primary button — which meant
`positionNotice()` had to measure its way around four pieces of furniture
(`#nextbtn`, `.homeversion`, `.daily-question-fab`, `.bottomtabs`) that all
live down there and all move at the tablet breakpoint. Per explicit request
it now pins to the top instead, where both screens it can appear on are
empty: `top:calc(env(safe-area-inset-top) + .75rem)` in CSS, and
`positionNotice()` measures the *bottom* edge of whatever the current screen
puts up there (`NOTICE_OBSTRUCTIONS`, now `.wrap > .top`, `.wrap > .count`,
`.back-link`) and parks the banner below the lowest of them. On Welcome and
Home none of those is showing, so the CSS value is what you get. Anything
new added along the TOP of Home or Welcome needs its selector in
`NOTICE_OBSTRUCTIONS` or the banner will sit on top of it.
**Both top banners share that measurement**, via `topNoticeOffset()`.
`.daily-alert` used to skip it entirely — it only ever knew how to park
below the update banner, and assumed nothing else was up there, which was
true while it only appeared on Home. The moment "Find me" started
answering with one on Rankings it landed squarely on the screen title, and
then on the Level/Badges/Hundos switcher. `.panel > .navsegment` is in the
list for that; the update banner never meets one, since it is gated to
Welcome and Home. The entrance
animation is `translateY(-8px)` for the same reason — it drops in from
above now rather than rising from an edge it no longer sits on.

**Neither notice may appear while a tour is running, and not for a few
seconds after one ends.** Reported from a screenshot: the re-add banner was
sitting behind the dim while the main-menu tooltips were being clicked
through. `noticeAllowedHere()` tests for `#tour-overlay` — the full-screen
dim every tour puts up — so one test covers every tour rather than each one
having to opt in. `startSimpleTour`'s own `cleanup()` then calls
`holdNoticesAfterTour()`, which sets a `TOUR_NOTICE_QUIET_MS` (3.5s) window
and schedules the re-check itself. That re-check is not optional: a tour
ending is not a screen change, so nothing else would ever call
`syncNoticeVisibility()` again and a held notice would stay held until the
next navigation.

**Gating to Welcome and Home is structural, not a list.** `dataset.screen`
is set in exactly two places in the whole file (`showWelcome` and
`showHome`), so every other screen fails the test by construction — there is
no list of excluded screens to keep up to date, and a new screen is excluded
by default. Verified by grep, not assumed.

**THE PUSH IS THE DEFAULT, AND THE BANNER IS THE ESCAPE HATCH (build
192).** *"Let's just keep it so that it forces updates on everyone, no
more update banner, unless it's the safari one."* So a newer build is
pushed without asking, and the update banner is gone from the everyday
path.

**"The safari one" is a different thing and is untouched**: that is the
RE-ADD notice — `frameId`, `maybeShowFrameNotice()` and the
`x-safari-https:` hand-off — which asks somebody to re-add the app to
their Home Screen after an icon, name or status-bar change. It has
nothing to do with builds. Don't confuse the two when reading a report
about "the banner".

**THE FLAG IS INVERTED, NOT DELETED.** `force` in **version.json** now
defaults to true and only an explicit `"force": false` asks for the
banner back. Keeping it readable is the entire point of it being a
sidecar: putting the banner back for one release is a one-line change
that needs no code to reach anybody first. `check-behaviour` section 9
drives all four cases — no flag, `true`, `false`, and same build —
through `checkForUpdate()` itself rather than reading the constant.

**THE BANNER CODE STAYS, AND IT IS NOT DEAD.** It is reached two ways:
an explicit `"force": false`, and — the one that matters — once the
forced push has failed `FORCED_UPDATE_TRIES` (3) times on that exact
build. Without that fallback a device that cannot complete a reload is
stranded on an old build with nothing on screen to say so and no way to
be told, until some later build happens to work. **Nobody should ever
see it.** If somebody reports the update banner, that is the signal
that their device has failed three forced reloads — not a cosmetic
complaint.

**This supersedes the note it replaced**, kept for the reasoning: the
push was opt-in per release because pushing without asking was built,
shipped and asked against the same night — *"I want them to have the
interactive to select the update button, it's more fun that way ...
I'll tell you when I need an update pushed through."*

**The original note, kept because the mechanics still apply:** *"Force an update, next time
people finish any test they are on it, push their update ... If they
aren't on a test go ahead and push it for those people. I need the
update to be pushed immediately."* So the app finds a newer build, puts
up a full-screen `.pushing-update` ("Pushing update…", a sweeping bar,
"Your progress is saved.") and reloads itself. No tap. A previous
dismissal is deliberately NOT consulted on this path — it recorded an
answer to "would you like to update", which is no longer the question.

- **A FORCED RELOAD NEEDS A LOOP GUARD, and this is the whole risk of
  the feature.** If `version.json` says one build and the served
  `index.html` still carries the old `APP_BUILD` — Pages mid-deploy, a
  CDN edge behind, an iOS cache that will not let go — then "reload
  until they match" never terminates, on every phone in the class at
  once. Each attempt is counted against the build it was for in
  `class26e.forced.v1`, and after `FORCED_UPDATE_TRIES` (3) the app
  stops pushing and falls back to the old banner, which is tappable and
  cannot loop. It is in `localStorage`, not on `store`: it has to
  survive the very reload it is counting, and it is device state rather
  than progress.
- **THE MID-TEST BAIL HAD TO MOVE OUT OF `checkForUpdate()`, and that
  was a real bug, caught by testing rather than by reading.** It used to
  return before the fetch whenever `testInProgress` was set — a harmless
  deferral while the banner waited for a screen change, and fatal for a
  forced push, because the check never learned a new build existed and
  so never armed anything to fire when the test ended. Measured: held
  mid-test, the push never came. The bail now lives in
  `forcedUpdateBlocked()`, which `startForcedUpdate()` re-tests every
  800ms — so the reload still cannot land on somebody's unsaved run, and
  the moment `summarize()` clears the flag the next tick fires.
  **Verified: 1,739ms after the test ended.**
- **`summarize()` also calls `checkForUpdate(true)` 1.2s in**, and the
  `true` matters: the ordinary 15-minute throttle would routinely
  swallow the one check "right when they finish their next test" depends
  on. The 1.2s is so the results screen paints first — finishing a run
  and being shown a loading bar instead of the score reads as a crash.
- **`forcedUpdateBlocked()` also waits out the splash, the generating
  overlay, a tour and a badge cutscene.** Same rule as everything else
  that may not sit on top of a loading screen, in reverse: the overlay
  is `z-index:500`, above `#genprofile-overlay` at 400, because nothing
  may sit on top of THIS either.
- The bar is an indeterminate sweep, not a percentage, because there is
  no percentage to report — it covers one request for one file. Under
  `reduce-motion` the global `animation:none` would leave it frozen at
  40% and reading as stuck, so that case gets a full static bar instead.

The re-add notice, and the banner the forced push falls back to:

Both are gated to the Welcome and Home screens only, never mid-test:

| | Update banner | Re-add notice |
|---|---|---|
| Who | everyone, incl. browser tabs | installed **and** not Android |
| Trigger | `build` ≠ `APP_BUILD` | `frameId` not acknowledged |
| Action | refetch with `cache:"reload"`, then reload | hand off to Safari |

Details that exist for a reason:

- `applyUpdate()` re-fetches the exact URL with `cache:"reload"` before
  reloading. A plain `location.reload()` may serve the same stale copy; a `?v=`
  cache-buster populates a *separate* cache entry and leaves the URL the Home
  Screen icon launches just as stale.
- **`target="_blank"` does not reach Safari** from a standalone app on current
  iOS — a same-origin link navigates inside the app, which presents as the app
  reloading. Use the `x-safari-https:` scheme. `openInSafari()` watches for the
  app going hidden as proof it worked, and grows a copyable link if nothing
  happened after 1.5s.
- Acknowledgement is tied to the app actually going hidden, **not** to the tap.
  Acknowledging on tap turns a failed hand-off into a permanently silenced
  notice.
- The Android exclusion is written as `!/Android/i` rather than a positive iOS
  test **on purpose**: iPadOS Safari reports a Mac-like user agent, so
  `/iPad|iPhone/` misses the exact device this was written for.
- The check retries while the splash is up (20 × 1.2s). The first-run splash is
  **8 seconds**; a 6-retry budget silently ran out and the check was never
  made. Screen changes also trigger a check, so a lost attempt heals itself.

---

## Going live

**This IS the live repo, as of build 97.** It used to be the other way
round: development happened in a separate `Nova-Test` repo and going
live meant copying the built state across. That copy has happened - the
app, `version.json`, `launch/`, `tools/` and this file all moved here -
and `Nova-Test` was retired, because two repos with one of them stale
is how the wrong one gets edited.

The section below is kept because every rule in it still applies to a
deploy from here; only the copying step is history. What matters now:
**a merge to `main` is live to the class in about a minute**, so the
checks in **Verifying** are the only thing standing between a mistake
and ~40 people.

**And now a second thing stands there: Madison's go.** See **DO NOT MERGE
TO `main` UNTIL MADISON HAS SEEN THE SCREENSHOTS** under **Repo and
deployment**. She asked for it on being told what this paragraph says —
she had been asking when the work could be "pushed from the test URL to
the live class used URL", which is a step that stopped existing at build
97. If a session is still describing this repo as a test repo, it is
reading `Nova-Test`'s retired copy of this file.

**Copy `index.html`, `version.json` AND the `launch/` folder. All three.**
`index.html` and `version.json` are one comparison split across two files;
`launch/` holds the iOS startup images the page references by path, and
without it every iPhone gets a white flash on launch with nothing to say
why. If `version.json` is missing or stale on the live side, the
check `fetch`es it, fails, and swallows the error by design — so nobody is
ever told about an update and nobody is ever prompted to re-add. That failure
is completely silent, which is exactly what makes it worth stating here.
`tools/` and this file are for whoever maintains it and can come too; nothing
at runtime reads them. `launch/`, by contrast, **is** read at runtime — by
iOS, at launch, before the page loads.

**The re-add prompt must fire exactly once, and it is armed.** `frameId` is
`go-live-1`. Everything iOS reads only at install has changed — icon, app
name, status bar colour, and now the launch image — so every existing install
genuinely does need re-adding, once.

- **Do not bump `frameId` again**, before or after going live. Bumping it is
  the *only* thing that re-prompts a device that has already acknowledged.
- Further install-time changes landing before go-live need **no** bump. No
  device on the live origin has acknowledged `go-live-1` yet, so it is still
  pending for all of them however many times the file changes first.
- `localStorage` is per-origin, so acknowledging on the test URL does not
  carry to the live URL, and vice versa. Testing here cannot spend the live
  prompt.

Verified end to end: a device is prompted once and never again after either
"I've done this" or a successful Safari hand-off; "Not now" (the ×) stores
nothing and returns next launch, as intended; a device holding an older
acknowledged `frameId` is prompted exactly once for the new one; Android and
plain browser tabs are never prompted; and an update and a re-add pending
together never stack — the update takes the screen and the re-add is
re-evaluated on the next check.

---

## Conventions

- **Screen functions are `showX()`** — except **Settings, which is
  `showAppearance()`**. A holdover from when it was only about theme. Search
  `showAppearance`, not `showSettings`.
- Screens mount via `stage.replaceChildren(...)`. Welcome and Home tag their
  root with `dataset.screen`, which is how the update notices know where they
  are — self-clearing, since the next screen's mount removes the node.
- **No Done/exit button on a screen the bottom tab bar can already leave.**
  Home, Settings, Profile, Rewards and Leaderboard have none — the tab bar is
  the way out. Two keep theirs for a reason: Answer Review's button says
  "Finished" and goes to the test Setup screen, which no tab reaches, and the
  end-of-test summary force-hides the tab bar (`window.forceHideBottomTabs`),
  so it has no other exit.
- **Tabbed screens (Leaderboard, Profile)** share one pattern: a
  `.navsegment`/`.iconbtn` pill switcher, `hidden`-attribute panels, and a
  `selectXTab(which)` toggler. Match it rather than inventing a new shape.
  Profile's four tabs are **Profile, Badges, Rank, Stats** — Stats was
  moved to the far right on request — driven off one `profileTabDefs`
  list rather than four hand-written copies of the same four lines. `PROFILE_TABS` is the swipe order and has to carry
  the same order as the buttons — a thumb swipe that skips a tab is
  worse than no swipe. `"achievements"`, `"ladder"` and `"unlocks"` are all
  still accepted as tab names, so every name this tab has ever had lands
  on it rather than falling back to Profile.
  **`check-behaviour` USED TO ASSERT THOSE FOUR LABELS IN ORDER, AND IT
  WENT STALE TWICE** — once when they were renamed and again when Stats
  moved to the far right, both of which were asked for. The second time
  it sat red for two builds before anyone looked. A gate that encodes a
  DECISION has to be re-read whenever the decision changes, or it fails
  the app for being right; better, it should not encode one. It asserts
  the INVARIANT now: four tabs, the swipe order matching the buttons,
  Profile first and Stats last — the two positions that are load-bearing
  (a bare `showProfile()` lands on Profile, and Stats carries a class
  keyed to being last).
  It was five for a while, and five labels only ever fitted a 375px phone
  by being tightened for five specifically (`:has(.iconbtn:nth-child(5))`)
  and allowed to step just outside the panel's side padding below 26rem;
  measured, they wanted 299px where a 375px phone's content column offers
  295. Those rules are still there, guarded by that `:has()`, and they
  match nothing at four — which is the point: they are a safety net keyed
  on the tab count, not leftovers from a retired feature.
- **`.searchbox` CARRIES A 2.5rem LEFT GUTTER FOR A MAGNIFIER MOST
  FIELDS DO NOT HAVE, AND `text-align:center` CENTRES ON THE CONTENT
  BOX.** So a centred, iconless field sits (2.5 − .9) / 2 = **.8rem
  (12.8px) right of the middle** — reported on Friends as *"the
  previewed text is offset to the right for some reason"*. It is
  padding, not centring and not tracking: **do not chase it with
  `text-indent`.** `.searchbox-plain` exists for exactly this and every
  other iconless field already carried it; the one that did not was the
  friend-code input. Check the class list before believing a centring
  bug.
- **A LOCKED CHARACTER IS STILL A CHARACTER, AND `brightness()` IS A
  MULTIPLY.** The locked treatment was `saturate(.34) brightness(1.42)
  contrast(.92)`, which lifts a mid tone and leaves a near black near
  black. The Masked One's hood is `#141020`, so on a near-black tile it
  stayed at the tile's own level and what was left on screen was the
  pale lacquer mask with no head under it — *"all you can see is the
  mask while it's locked"*. Void had the same problem waiting in it.
  `contrast(<1)` is the tool, because it pulls BOTH ends towards mid
  grey rather than scaling from black. Measured on the rendered pixels
  rather than reasoned about: the hood went from **3 levels BELOW the
  tile to 44 above**, and the mask from 105× the hood's separation to
  2.17×. `check-unlocks` section 9 asserts both, by clipping the
  drawing's own box and sampling the shoulder band — nothing in the DOM
  can see this.
- **A STAT SAYS WHAT IT COUNTS, AND THE SENTENCE IS WRITTEN OFF THE
  CODE.** Every `.stat-card` is a button and opens ONE panel below both
  grids (`STAT_MEANINGS`) — a panel rather than expanding the card,
  because expanding a card reflows the grid and every other number on
  the screen jumps under the finger that just tapped. The sentences are
  read off what produces each number, not composed from the label,
  which is how help text ends up describing something the app stopped
  doing: the three durations are `store.studyLog`, written by
  `addStudyTime()` from time INSIDE a run, so a screen left open on Home
  is not study time; "Study sessions" is the sum of `testStats[].plays`,
  which is finished tests rather than sittings; and the answer streak
  deliberately ignores the daily question (`recordResult`), so a wrong
  daily cannot end one. **Keep them accurate** — a help text that has
  drifted is worse than none, because it is believed.
  `check-statsbadges.py` asserts every card opens a non-empty panel, so
  a label added later with no entry is caught rather than opening a
  blank box.
- **A GRADIENT NUMBER IS LIT WITH `filter`, NEVER `text-shadow`.** The
  level and badge values are `background-clip:text` with a transparent
  colour; a text-shadow on transparent glyphs paints a coloured slab in
  FRONT of the gradient instead of behind it. `drop-shadow` on the
  element respects the alpha.
- **THE BADGE CASE'S SLOT SHADE HAS TO REACH ZERO BEFORE ITS BOX ENDS.**
  It was one `radial-gradient(ellipse at 50% 42%, … 74%)` with no
  explicit size, so the ellipse was sized farthest-corner and its last
  stop landed a long way past the top edge — the shade was still at a
  quarter strength where the box stopped, and stopping is what a hard
  edge is. Reported as *"the shadow around the unearned badge slots is
  not fully there at the top of each one, it's hard cut off"*. Both
  layers carry an explicit size chosen so the last stop lands ON the
  boundary. Measured: 4.6 levels of one-row step down to 1.1.
- **Anything that fills or animates on a Profile tab has to fire when the
  tab is SHOWN, not when it is built.** `showProfile("stats")` builds
  every panel while another one is visible, so an XP bar that animated on
  build is a bar nobody saw move.
- **Shared classes are genuinely shared** (`.sect`, `.slab`, `.iconbtn`,
  `.panel`). A one-screen fix needs a screen-level ancestor scope; editing the
  bare class changes every screen, usually by accident.
- **A recent-test row says WHICH units, and it looks tappable.** Reported
  as not being able to tell either. `testLabelFor()` cannot answer the
  first — it stores a single-unit run as the bare unit name with no mode
  and a multi-unit one as "3 units — Drill", which names none of them —
  so `recordTestPlay()` now keeps `units` on the history entry and
  `testHistoryUnitLine()` writes the line from it. Entries written before
  that have no `units` and fall back to their label, which is why the
  list can show both spellings for a while; twenty entries is the cap, so
  they age out. The naming rule is a CHARACTER BUDGET
  (`TEST_ROW_NAME_BUDGET`, 40) rather than a count of names, because the
  names are not a fixed length — "Penal Code" is 10 and "Code of Criminal
  Procedure and Bill of Rights" is 44, so "the first three" is one line
  for some runs and five on a 320px phone for others. Always at least one
  name, and **never "+1 more"**: a count of one hides exactly one name and
  saves nothing. The affordance was a `@media (hover:hover)` colour, which
  no phone or tablet has, so there is a chevron and an `:active` tint now.

- **The Profile tab is one card, not two.** The identity block (name,
  character) and the level block (level, badges, XP bar) were two slabs
  and are one now, with a rule between them — *"maybe the top two boxes,
  the one with the level and the other with the name, could be joined"*.
  The consecutive-day streak came off it entirely. The class calendar
  and the recent test review sit BELOW the card as two destination rows:
  they are places to go, not facts about you, and inside the card they
  were the only tappable things in a block of read-only text.
- **ONE COPY BUTTON IN SYNC, NOT TWO.** Settings offered Copy code and
  Copy sign-in link; the second came off as "I don't even know what
  that is and it will confuse people". A sign-in link is a second thing
  to understand for something the code already does, and two names for
  one idea is worse than one name. `recoveryUrlFor()` still builds that
  URL for the re-add notice's Safari hand-off — machinery, not
  something anybody has to read. The save-your-code banner was changed
  in the same breath: a banner still pushing the idea Settings had just
  dropped is the app disagreeing with itself.
- **Settings' sections are named after what is in them.** "App version"
  used to sit on the end of the behaviour toggles, which is how it got
  reported as a weird section — nothing about a build number belongs to
  "how the app moves" or "studying & tests". It is in **"This app"**
  now, with Share this app and Add to Home Screen, and the build line
  leads because "am I on the version with the fix in it" is not
  answerable anywhere else once you are past onboarding.
  "Miscellaneous" is what a section is called when nobody has worked
  out what is in it.
- **FRIENDS IS ITS OWN CARD ON PROFILE**, not a second button inside
  the Class 26E box. Beside View class calendar it made "who you know"
  read as a fact about the course and buried the one place on that
  screen where somebody else can be waiting on you. It is a card rather
  than a row because it can SAY something before you tap it — how many
  friends, how many are online, how many are waiting — and a row that
  only says "Friends" is a button wearing a card's clothes. It borrows
  `.profile-classcard` wholesale, surface, header, serif title and the
  coloured figure in the corner: the first pass gave it a small
  uppercase label beside the class card's serif heading and the two
  read as a mistake an inch apart.
- **The friends screen leads with people, not admin.** It was requests,
  your code, add a friend, your friends, waiting on them — so it opened
  with two cards of code-swapping before it reached anybody. "Your
  friend code" and "Add a friend" were one job split in two and are one
  card now, with your own code under a rule BELOW the input: typing
  somebody else's is what you came for, reading out your own is what
  you do when they are standing next to you. Order is requests (someone
  is waiting) → who you have → the machinery for getting more.
- **Two Send buttons were wrong in the same way and both are fixed.**
  The friends one was a pale primary block with 2px corners against a
  dark pill of an input; the Virtual Room chat one was 36px tall beside
  a 45px field at 13.6px text, in the pale pill, on a screen where
  every other button is the matte black one. `.friend-act` is shaped
  for the Accept/Decline pair in a row of people, which is a different
  job from the one button that completes a field. **Both needed the
  `[data-layout="modern"]` prefix and the chat one needed
  `[data-theme="dark"][data-layout="modern"]` too** — the same
  two-step specificity trap `.friend-act` already carries a note about,
  where a half-applied fix looks right in one measurement and wrong in
  the screenshot.
- **Theming** is CSS custom properties keyed off `data-theme` and `data-accent`
  on `<html>`. Write the rule once, then override with a
  `[data-theme=...]`/`[data-accent=...]` prefixed version. Never a one-off
  hardcoded colour.
- **A theme is THREE colours, not one, because the default is three.**
  Reported as *"the default color has more colors, whereas the theme one
  just looks like one color"* — and it was true: only the default
  declared the `--theme-c1/2/3` triad the ambient glow is built from, so
  every other accent repainted one glow and left the other two on the
  default's values. Every `[data-accent="X"]` block now carries all
  three: the accent itself as `--theme-c2`, with a warmer c1 and a
  cooler c3 either side of it. See **Three things move together when
  the ambient glow changes** — a new accent has to set the triad or it
  will look like one flat colour, however right its swatch is.
- **A SET THEME RECOLOURS THE APP AND DOES NOTHING ELSE.** From Gold
  upward, choosing a theme used to turn the Start button into an animated
  shimmering gradient — the one place where picking a colour changed how
  the app BEHAVED rather than what colour it was. It came off by explicit
  request: *"we dont need the themes to animate or anything any different
  when they are set. They just need to match the default color scheme
  look but with its own main new color."* The swatch CIRCLES in the
  picker still move, and that is not a contradiction: the picker is
  previewing what there is to unlock, which was asked for in the same
  breath. Keep the two apart.
- **THE FLARES ON HOME HAVE THEIR OWN COLOUR TABLE, and they have to.**
  `ACCENT_SWATCH` is also the dot in Settings, and that dot has to keep
  predicting what tapping it does (the three-places rule below). Spark
  and Comet were `#AEB7C2` and `#D8E1EA`, two light greys a few levels
  apart — reported as two flares reading as the same colour. So
  `FLARE_SWATCH` overrides Spark to a near-black and `FLARE_NOIR` marks
  it for the `.cosmic-badge-noir` treatment: a genuinely dark body with
  all the light in the rim and the halo, because mixing 55% of a
  near-black with white only produces another grey, and a black disc
  with no halo reads as a hole in the screen. Everything else falls
  through to its swatch. **Change a flare's colour here, never in
  `ACCENT_SWATCH`.**
- **The orbit's outer radius is 38, not 42, and that is a clipping
  fix.** A badge is positioned by its top-left corner, so an outer-ring
  badge on the right put its own 2.6rem width past the coordinate:
  measured on a 17 Pro Max the Comet flare's box ended 7px outside
  `.cosmic-hero-wrap` and its glow a good deal further — reported as
  the right-hand flare looking cut off. Pulling the outer ring in is
  the fix that does not move the other six; the inner ring is
  untouched, and the top badge keeps its clearance from the notice
  banner above it.
- **A rank's theme is that rank's colour, and it is declared in three
  places that must agree**: `ACCENT_SWATCH` (the dot in Settings),
  `--accent` inside the `[data-accent="X"]` block (the app's accent) and
  `--theme-c2` in the same block (the glow). All three derive from
  `RANK_COLOR`, lifted for legibility on a dark screen. Change one and
  the swatch stops predicting what tapping it does, which is exactly
  what *"align the swatches"* was about.
- **EVERY CHARACTER CARRIES A SOFT PERMANENT HALO, drawn INTO the SVG.**
  Asked for off Void, which had one built in from the start: *"the void
  character looks so good because it has that soft permanent glow right
  behind it, give all the characters that same thing but in a color that
  matches it of course."* It is part of the DRAWING rather than a CSS
  effect on the element, and that is the whole point — it comes along to
  the rankings rows, the Virtual Room lobby, the race line, the bottom
  tab bar and every screenshot, instead of only appearing on the one
  screen somebody remembered to add a class to.
  It reads `AVATAR_GLOW`, the same table the picker's selection glow
  uses, so a character's halo and its selection glow cannot end up two
  different colours — the same reason a rank's three places all derive
  from `RANK_COLOR`. It is a **circle filled with the falloff**, never a
  shape filled with it (the rank emblems' rule: a halo cut to the
  silhouette reads as an outline round it rather than as light behind
  it). Void is skipped, because its own halo is a two-colour falloff
  built from the flare colours it wears and a generic one underneath
  only muddies it.
- **A SELECTED CHARACTER GLOWS IN ITS OWN COLOUR**, from `AVATAR_GLOW`
  via `avatarGlowColor()`, set as `--char-glow` on EVERY option rather
  than only the selected one — a value written in the same moment as
  the class would transition from the previous character's colour.
  Two layers, like every other glow here: a pool behind the artwork on
  `::before` (so it cannot affect layout) and a `filter:drop-shadow` on
  the drawing itself, which is what makes the light come OFF the
  character rather than sit behind a square. Never an SVG filter —
  those are the one thing that has bitten this app on real iOS
  hardware. A locked character gives off nothing: it is a preview, not
  something you hold.
- **Tablet styling is `@media (min-width:40rem)`**, added *after* the phone
  rule as an override — never a rewrite of the base rule.
- **Settings' behaviour toggles are two sections, not one.** "Motion &
  interaction" (smooth scrolling, reduce motion, swipe to advance) and
  **"Studying & tests"** (keep screen awake, auto-advance, mute banners,
  auto-flag) — seven under one header had visibly piled up. The second
  header was "While you study" first and was reported as not reading
  official enough for what this app is; the name in the app is the one
  that counts, and this file said the old one for a while. Both headers
  are `.slab.motion-summary` so they read as a matched pair; the second
  also carries `.section-divider` for the gap above it. A new toggle goes
  into whichever group it belongs to, and into that group's own
  `motionDetails`/`studyDetails` container in `showAppearance()`.
- **Behaviour toggles live on `theme`**, not `store` — `smoothScroll`,
  `swipeAdvance`, `autoAdvance`, `hapticTouch`, `reduceMotion`, `keepAwake`,
  `muteBanners`, `autoFlagMissed` — and each needs three things: a default in
  the `theme` object, a `typeof ... === "boolean"` line in `loadTheme()`, and a
  field in `saveTheme()`. Miss any one and it silently stops persisting.
- **The daily question button has three states and a live timer.**
  `is-ready` is a quiet ring that runs whenever the question is unanswered;
  `is-fresh` is a brighter, deliberately finite light-up (five cycles, ~6s)
  plus a toast, shown when the period has rolled over since this device last
  saw Home; `is-done` greys it out. The button is `3.4rem` on a phone and
  `4.6rem` from tablet up — it was 41.6px once, under the 44px minimum,
  and the tablet size exists because a control sized for a phone reads as
  an afterthought beside an iPad's tab bar.
  Both animations are a `::after` ring and
  a `box-shadow` — never the button's own size, because a tap target that
  changes size under a finger is worse than no animation. The global
  `[data-reduce-motion="true"] *{animation:none}` rule switches both off
  without naming either.
  **The announcement is a top banner (`.daily-alert`), not a toast, and
  that was measured rather than chosen.** A toast lands in the bottom
  corner and Home's bottom corner is full: at the toast's own height the
  message painted *under* the "?" it tells you to tap, and lifted clear of
  the "?" it painted *over* Start Studying — the gap between those two is
  26px, so there is no third option down there. `positionDailyAlert()`
  parks it below the update notice when one is up, and is called from
  three places because the two arrive in either order: the notice is
  fetched asynchronously and routinely lands a second after the alert, so
  positioning once at creation left both at y=74.
  `class26e.daily.seen` holds the last period this DEVICE displayed, and is
  deliberately a `localStorage` key rather than a field on `store`: it is
  viewing history, not progress, so syncing it would announce a reset on a
  second device that already happened on the first. A null value means a
  fresh install and announces nothing — it just records.
  `dailyResetTimer` lives outside `showHome()` so a rebuild replaces it
  instead of stacking, fires at `nextDailyResetMs()`, and checks the button
  is still in the document before doing anything, so navigating away lets it
  expire harmlessly. It updates the button in place rather than re-rendering
  Home under someone.
- **The ring round the Profile tab has two causes now.** The first is the
  welcome bonus: at the end of the main-menu tour `awardWelcomeBonus()`
  adds 100 XP and `showPointsFlyEffect()` flies a banner into
  `#bottomtab-profile` and pulses it — an `avatar-pulse` ring expanding
  0 → 14px while the icon scales to 1.18× and back. The second is a badge
  cutscene finishing, which flies the badge to the same tab and pulses it
  the same way, deliberately: "something new is in there" should be one
  gesture the app makes, not two. Those are the only two things in the
  app that ring a tab, so an unexplained halo in a screenshot is one of
  them and nothing else. **Its removal timeout must match the animation's own
  duration** — it was `500` against a `.8s` animation, left behind when the
  animation was lengthened from `.5s` (to stop it being missed), so the
  class came off at 62% with the icon still at ~1.05 and it snapped back to
  size instead of settling. Measured, the ring had already faded by then,
  so the whole visible cost was that snap; both are 800 now.
- **`autoFlagMissed`** flags a question every *fifth* miss
  (`AUTO_FLAG_MISS_THRESHOLD`), hooked in `recordResult()` — the single place a
  miss is recorded, so every mode gets it without its own copy. Every-fifth,
  not five-or-more: with `>=`, un-flagging a question by hand was undone by the
  very next miss, which makes the manual control useless.
- New `localStorage` keys follow `class26e.<thing>` and are wrapped in
  `try/catch`. Keys added for the update machinery: `class26e.statusbar.v1`,
  `class26e.frame.ok`, `class26e.update.dismissed`, `class26e.daily.seen`,
  and session-scoped `class26e.updating`. None of these live on `store`, so the
  `applyLoadedData()` default rule doesn't apply to them.

---

## Known quirks

- **Two kinds of em dash exist in this file and they are not
  interchangeable.** Most comments use a real `—`. Some contain the literal
  six-character text `—` instead. Inside JS *string literals* a `—`
  escape is correct and renders as a dash at runtime; inside `/* comments */`
  it is inert text. This breaks exact-match edits. **Check raw bytes before
  editing text near a dash** (`sed -n 'N,Np' file | cat -A`). The same trap
  applies to `×` and friends — some are literal escapes in source, some
  are real characters.
- **A lot of the CSS is dead, not hidden features.** `loadTheme()` ignores any
  stored `"light"` mode or `"classic"` layout — both are fully retired — but
  their CSS was never deleted. `[data-theme="party"]` likewise has a whole
  theme's CSS that `applyTheme()` can never reach (it maps party → dark).
  Retired accent names `grinder`, `scholar`, `luminary` still have colour
  definitions. **If you change a colour and nothing happens, check the selector
  is reachable before assuming your edit was wrong.**
  (The light/classic values in `--statusbar-mix2/3` are inert for the same
  reason — kept as harmless defensive defaults.)
- **Haptics are not achievable on iOS, and the obvious workaround has
  already been tried on a real device.** WebKit has never shipped the
  Vibration API, so `navigator.vibrate` is simply absent on iPhone and iPad.
  The known workaround — since iOS 17.4, actuating an
  `<input type="checkbox" switch>` fires the system haptic — was built,
  shipped and tested on an up-to-date iPad. **Detection succeeded** (the
  control genuinely renders as a switch there), but **actuation failed**: a
  script-generated `click()` is not a trusted gesture, and iOS produces the
  haptic only for a real finger landing on the control. Being inside a
  user-gesture call stack is not enough. The whole feature was removed
  afterwards rather than left as a dead toggle. The only route left is
  layering a real, tappable switch over every answer choice and forwarding
  the interaction — judged not worth the regression risk on the most-used
  screen for a nicety, and explicitly declined. Don't quietly retry it; a
  visual shake is the feedback that cannot fail.
- **"Flares" ≠ badges, and "Secret Flares" are gone.** Flares are the
  orbiting marks on Home, one per rank — the thing a rank hands over.
  Badges are the sixteen unit awards on Profile. The two are separate
  and the words are not interchangeable in copy. Secret Flares were a
  third thing, a hidden three-colour hunt gating the top rank; they were
  scrapped outright. `store.mysteryColorsFound`, `testsUntilMystery` and
  the `mysteryStars` guard survive as defaulted, unread remnants — see
  **Ranks**. The version-history copy in `index.html` still advertises
  them, and is deferred rather than correct.
- **A solid-coloured child inside a `backdrop-filter` surface can tear on
  iOS** — reported as glitched lines running through the update banner's
  button. The parent needs `will-change:backdrop-filter` (`.toast` has always
  had it and has never glitched; `.update-banner` did not) and the child needs
  its own compositing layer (`translateZ(0)` + `backface-visibility:hidden` +
  `isolation:isolate`) so it is rasterised once instead of resampled through
  the filter every frame.
- **The `html` background is a *fallback* for the `body::before` glow, so it
  has to be pixel-identical, not just the same gradient.** A gradient's
  percentage stops resolve against the box it paints on, and html's box is the
  full scroll height — so the same declaration arrived stretched and read as a
  seam wherever the fixed layer failed to paint. `background-size:100vw 100lvh`
  plus `no-repeat` pins it to the same box `body::before` occupies. Measured
  difference went from up to 8 levels (5 of them in the bottom 40px on a
  tablet) to exactly 0.
- **Three things move together when the ambient glow changes.** The glow is
  declared twice (the `body::before` stack and the `html` fallback, which
  must stay pixel-identical) and its strength is modelled a third time in
  `--statusbar-mix2/3`, which are the share of glow 1 and glow 2 still in
  play at the very top edge — calibrated at 55% and 50% of their peaks. Dark
  currently runs `--theme-c2` at 13.5% and `--theme-c3` at 14.5% (up from
  10%/11%, which was reported as dull), so the tokens are 7.4%/7.25%. There
  is a third, gold `--theme-c1` glow now as well, deliberately anchored at
  `50% 104%` — along the BOTTOM edge, where it contributes nothing up in the
  status bar strip and therefore needs no token of its own. Add a glow near
  the top and that stops being true. The dimmed `has-active-question`
  variant is a fourth copy of the same numbers (4%/4.7%, tokens
  2.2%/2.35%) and has to be re-scaled with them, or the status bar stays
  tuned to the full glow on the single most-used screen in the app.
  **Scale the tokens with the peaks; do not re-sample in Chromium.** The
  55%/50% share was measured against real hardware. Chromium's own top
  strip runs ~6 levels darker than the model on a phone and ~8 lighter on
  a tablet — the glow radius doubles at `min-width:40rem` and one flat
  token has to serve both — so tuning to either reading walks the
  calibration away from the device it came from.
- **The halo round the hero sphere is `.homeglow.homeglow-hero`, not the
  background.** Its base is a single `var(--accent)` ellipse, and on the
  default accent `--accent` is `var(--ink)` — which is exactly why it read as
  "a faint white glow". The dark override paints it in `--theme-c1`/`--theme-c3`
  instead, so it re-themes with every accent rather than going grey.
- **A PLAYWRIGHT ROUTE HANDLER WITH TWO PARAMETERS IS CALLED WITH
  `(route, request)`.** Every harness here serves a modified copy of
  `index.html` by intercepting the request, and the obvious shorthand
  for that — `pg.route("**/index.html", lambda r, b=body: r.fulfill(
  ..., body=b))` — silently binds the Request object to `b`. `fulfill`
  then raises *inside the handler*, so the route is never resolved, the
  navigation hangs until its timeout, and the only thing in the output
  is `Page.goto: Timeout exceeded`. Nothing points at the handler. Use
  a named one-parameter function, or a one-parameter lambda that closes
  over the body.
- **A PATCH SCRIPT NAMED AFTER A STDLIB MODULE WILL RUN ITSELF.** The
  harnesses here start `import sys; sys.path.insert(0,'.')` so they can
  import a sibling helper out of the scratchpad, which puts every `.py`
  in that directory ahead of the standard library. A staged patch saved
  as `typing.py` was therefore imported — and *executed*, editing
  `index.html` — the moment something downstream did `from typing import
  IO`. It announced itself ("typing indicator applied") and was
  otherwise silent. Name staged patches `patch-<thing>.py`, and never
  `typing.py`, `json.py`, `io.py`, `types.py`, `queue.py` or `copy.py`.
- **Fixed-position elements render oddly in Playwright `fullPage` screenshots.**
  Verify their layout with `getBoundingClientRect()`, not by eyeballing.
- **A `max-height` cap alongside `overflow:hidden` is a CLIP, not a
  cap, and the content past it cannot be scrolled to.** `.cal-month-body`
  had `max-height:2000px` so the open/close slide could animate.
  On the calendar the cap was never near; on Answer Review one unit is
  **14,231px** of questions, so six sevenths of the screen was cut off
  with no way to reach it — reported as *"it's not scrollable, it
  doesn't let you scroll down to look at all the questions"*. Counting
  the questions in the DOM would have said everything was fine: all 29
  were there and 24 of them were invisible. `openCollapsible()` is the
  fix — the cap exists only for the duration of the animation and is
  dropped (`.is-settled`) once the transition ends, with a timeout
  behind it because reduce-motion switches transitions off and
  `transitionend` then never fires. **Use it rather than toggling the
  class by hand**, and never give a scrollable region a pixel cap.
- **Setting `style.animation = ""` does not mean "it already ran, leave it" —
  it RESTARTS the animation from frame zero.** The same `advanceWithSlide()`
  cleanup that removed the clone also cleared the incoming panel's inline
  `animation:none`, which un-suppressed `#stage > *{animation:screen-fade-in
  .3s}` — so the question that had just finished sliding in jumped 6px down
  and settled again over the next 300ms. Measured: slide done at ~200ms,
  second movement starting at 215ms. Every question arrived and then bumped.
  A panel that was slid in was never mounted, so the slide IS its entrance
  and the mount animation stays off; the inline `none` goes away with the
  panel at the next question.

- **PROMOTING THE QUESTION PANEL'S COMPOSITOR LAYER UP FRONT WAS TRIED
  AND REJECTED, and the reason is text.** `will-change:transform` on
  the question panel (scoped to `body.has-active-question`) would
  create its layer at mount rather than mid-gesture, which is a real
  cost on iOS. But promoting an element drops subpixel antialiasing
  for greyscale, and this is the most-read text in the app.
  Pixel-diffed: **3,863 pixels changed on an unanswered iPhone screen,
  13,571 on an iPad**; `contain:paint` on top made it 19,251 by
  clipping what paints outside the panel box. **The control — the same
  build diffed against itself — is 0**, which is what makes those
  numbers trustworthy rather than run-to-run noise. Always run that
  control before believing a pixel diff.
  Measured against it: the slide is **already frame-perfect in
  Chromium — 16.7ms median, zero frames over 24ms at 1x, 4x and 6x CPU
  throttle**. So this bought nothing measurable in exchange for worse
  text. If it is revisited, check on a REAL DEVICE first whether
  promotion actually costs anything there, because this machine cannot
  show it.

- **ON AUTO-ADVANCE, THE BIGGEST PART OF THE WAIT BETWEEN QUESTIONS IS
  NOT THE ANIMATION — it is `scheduleAutoAdvance`'s deliberate beat**,
  and it was 500ms against a 170ms slide. Measured end to end from the
  tap, the question did not begin changing for ~510ms and everything
  settled at 1038ms. Tuning the slide cannot touch that; it is three
  times the slide's own length. It is 300ms now — still a clear beat
  to see whether you got it right, 40% off the wait, 1038ms → 509ms
  end to end. Anyone who wants none of it turns auto-advance off,
  which is the default. **Check this number before tuning the
  animation again**: if a report of "lag" comes from somebody with
  auto-advance ON, the animation is the smaller half of what they are
  feeling.
- **"VERSION 6.0" NEVER CHANGES, SO IT CANNOT ANSWER "ARE YOU RUNNING
  THE FIX?"** An installed home-screen app can sit on a cached copy
  indefinitely and looks identical to an up-to-date one — reported as
  *"the lag is still here, has it not been pushed through yet?"* when
  the fix had been live and Pages-deployed for twenty minutes. The
  What's New screen now prints `VERSION 6.0 · BUILD <APP_BUILD>`, which
  is the one place in the app that can settle that without guessing.
  Ask for it before re-diagnosing a bug that is already fixed.

- **THE NEXT-QUESTION TRANSITION IS A FADE-THROUGH, NOT A SLIDE, and
  that is a deliberate reversal.** Reported after four rounds of
  tuning the slide: *"that motion is not easy on the eyes at all ...
  maybe it needs to fade into the next question."* She was right, and
  the reason is that the panel is nearly IDENTICAL between one
  question and the next — same header, same progress dots, same Pause,
  same Next bar. Sliding the whole thing a full screen width animates
  a great many pixels that did not change and asks the eye to track
  the entire display for what is really a swap of text. **No amount of
  curve or duration tuning fixes an animation that is moving the wrong
  thing** — three builds were spent proving that.
  Now: the outgoing clone fades out over 100ms while drifting
  `SLIDE_DRIFT` (14px) left; the incoming fades in over 150ms after an
  85ms delay while drifting 14px back to 0. The fade carries the
  change and the drift only says which direction it went.
  **`SLIDE_IN_DELAY` is load-bearing**: it holds the incoming half
  until the outgoing one is GONE, which is what makes this a fade
  *through* rather than a cross-fade. Two blocks of body text
  dissolving through each other at 50% opacity is unreadable mush, and
  this screen has already been reported once for showing two questions
  at once. Measured frame by frame, the worst simultaneous opacity is
  **0.00**.
  **`check-behaviour` section 8 asserts opacity, not geometry.** It
  used to check that the two boxes never overlap horizontally — the
  right test for a full-width slide, and meaningless now that both
  panels sit in the same place on purpose. What it guards is the thing
  the geometry stood in for: the two questions are never readable at
  once. A gate has to track the decision it guards.

- **AN EASE-OUT CURVE CAN BE SO AGGRESSIVE THAT THE ANIMATION READS AS
  LAG, and the way to see it is to sample the distance per frame.**
  The next-question slide ran `cubic-bezier(.32,.72,0,1)` over 200ms.
  Sampled frame by frame at 4x CPU throttle it moved 87, 124, 100, 40,
  19, 12, 7, 5, 3, 2 px — 78% of the distance in three frames, then
  EIGHT more (60% of the duration) creeping through the last 22%, with
  a 124px frame followed by a 40px one. A 3x deceleration inside one
  frame is what "it's still slightly noticeable" was pointing at: not
  a dropped frame, a badly distributed one. `easeOutQuad`
  (`cubic-bezier(.25,.46,.45,.94)`) at 170ms gives 73, 72, 64, 53, 43,
  33, 24, 18, 12, 8 — still decelerating, no crawl, and finishes
  slightly sooner than the curve it replaced.
  **Both halves carry the same curve and duration or the two questions
  visibly separate** — the clone's is in its `cssText`, the incoming
  one's is set separately. And the cleanup timeout has to be retuned
  with the duration; `check-behaviour` section 8 stubs it by a RANGE
  rather than the literal, because a gate that hardcodes that number
  stops holding the clone the moment anyone retunes the animation.
- **Two `requestAnimationFrame`s before starting a transition is ~33ms
  of a frozen screen, and the eye times a gesture from the TAP.** The
  slide waited two frames before setting its final transforms, bought
  to stop the animation dropping frames at its start. That symptom was
  real, but its cause was the outgoing clone fighting `screen-fade-in`
  (above); with that fixed the head start buys nothing. Measured, the
  tap did nothing at all for 46.6ms — four frames — of which only 13ms
  was real work. What a transition actually needs is for the starting
  positions to be COMMITTED before the final ones are set, and a
  forced layout read (`void el.offsetWidth`) does that synchronously
  for a fraction of a frame. One per element: only the incoming panel
  was being flushed, never the clone.

- **A RUNNING ANIMATION BEATS A TRANSITION ON THE SAME PROPERTY**, and that
  is what made the next-question slide read as "the screen glitching".
  `advanceWithSlide()` clones the outgoing question and transitions it to
  `translateX(-100%)` while the incoming panel slides in from the right. The
  clone was still running `screen-fade-in` — a `translateY` settle — so the
  animation won and the transition was ignored: measured frame by frame the
  clone went (0,6) → (0,2.4) → (0,0.87) → (0,0.07) over ~100ms and only then
  snapped to -400. The outgoing question never slid; it sat in place and
  wobbled. And **`.panel` has a fully transparent background**
  (`rgba(0,0,0,0)`, measured), so the incoming question slid in *underneath*
  it and both were legible at once. The incoming panel had carried
  `animation="none"` for exactly this reason for a long time; the clone never
  did. **Frame-drop numbers cannot see this** — the "before" build dropped
  frames, the fixed one did not, and both readings were consistent with a
  perfectly smooth animation of the wrong thing. It took capturing real
  frames off the compositor (`Page.startScreencast`) and logging BOTH
  transforms per frame.

- **Adjacent vertical margins collapse to the larger, they don't add.** A gap
  "smaller than the two margins suggest" is collapse, not specificity.
- **Don't copy the corner-positioning formula from `.daily-question-fab` /
  `.homeversion-btn`** (`right:max(calc(50% - Nrem), Yrem)`). It's relative to
  the centred bottom tab bar those sit beside and grows *further* from the
  screen edge as the viewport widens. Use
  `right:max(1.5rem, calc(env(safe-area-inset-right,0px) + 1.2rem))`.

---

## Showing the work

**Every change gets a screenshot at BOTH sizes, sent to Madison, every time
— phone and tablet.** Not one or the other, and not only when a change "looks
layout-related": this app is used on both, and a change that reads fine at
390px can be adrift at 1024px (the Pause button sat 88px from the edge on an
iPad while looking perfectly normal on a phone). Madison's own two are an
**iPhone 17 Pro Max (440×956)** and an **iPad Pro 11" (834×1194)** — those are
the reference devices, and a change that moves them needs saying out loud.

**Use `tools/shoot-flow.py`, do not mount screens.** It clicks through from a
fresh install and fails loudly on a tab bar during
onboarding, a missing tab bar on Home, or a tooltip over a loading screen. It
also draws the status bar, because a screenshot with an unexplained black band
at the top has now been misread twice — once as a tab-bar bug, once as the
update banner "not aligned to the top".

**It shoots the two reference devices by default, and that was asked for**
— *"Send me only screenshots for everything from the iPad Pro and
iPhone"* — because seven devices' worth of a whole walk is more than
anyone reads. The other five are still in `DEVICES` and still correct:
`--all` runs the lot and a substring (`shoot-flow.py ipad-mini`) runs
one. That is a change to what gets SENT, not to what gets CHECKED — the
whole matrix is still the bar, and `sweep-layout.py`,
`check-positions.py` and `check-fixes.py` still run every device.

Fixed-position elements render oddly in Playwright `fullPage` screenshots, so
screenshot the viewport and scroll, and measure with `getBoundingClientRect()`
rather than trusting a tall capture.

### Recording an animation

`tools/record-cutscenes.py`. Four of the things asked about most — the badge
unlock, a rank cutscene, the Supernova cutscene, the flight to the Profile
tab — are only animation, and a screenshot of one is a screenshot of one
arbitrary frame.

- **There is no ffmpeg here, and Playwright's own recorder only emits
  `.webm`**, which is not a safe bet on an iPhone. Frames come off the
  compositor with CDP `Page.startScreencast` — real paint timing, where a
  screenshot loop samples at whatever rate the screenshots happen to
  complete and misses the fast parts — and Pillow writes a GIF, which plays
  anywhere including inside a message.
- **One palette for the whole clip, built from frames sampled ACROSS it.**
  Quantising against frame 0 is quantising a gold burst against a palette
  taken from a near-black Home screen: the payoff comes out grey, which
  reads as the cutscene having no colour rather than as an encoding
  artifact. That is exactly how it was first read here.
- **No dithering.** The noise defeats LZW and roughly doubles the file on a
  screen that is mostly smooth dark gradient.
- **Know the real length before recording.** The Supernova cutscene bursts
  at 9s and finishes at 20s — two and a half times any other tier's 8s. A
  12s capture of it is a recording of the wind-up and nothing else.
- **Drive a run by waiting on the DOM, never on a timer.** `beginRun()` puts
  a ~3s LOADING TEST screen up first, and the slide between questions has
  two questions mounted at once, so a click on a fixed delay lands on the
  outgoing one and registers as a wrong answer — which silently turns a
  100% run into a 92% one and no badge at the end. `answer_all()` waits for
  `.choice`, then for `pos` to actually change.
- **Identity Crimes is the unit to use for a real earn**: 12 questions, the
  smallest in the app, and `recordUnitPerfectIfEligible()` only credits a
  hundo for a run covering the unit IN FULL (`isFullUnitRun()`), so a
  10-question slice of Penal Code earns nothing however perfect it is.

### Where things currently land

Regenerate with `python3 tools/check-positions.py`; these are the numbers to
check a change against, not to trust forever. Measured installed, portrait.

**THE NUMBERS ABOVE WERE WRONG FOR 34 BUILDS, AND THE TOOL PASSED EVERY
TIME.** `check-positions.py` carried `ROOT = "/home/user/Nova-Test"` -
the repo the app was developed in before build 97 and retired at it - so
from the copy onward it served, measured and reported a frozen build 97
while the live app moved on without it. `shoot-flow.py` and
`shoot-results.py` had the identical line, so every screenshot they made
after the move was of that frozen build too. **A gate pointed at the
wrong repository cannot fail**, which is the same trap as a check that
measures nothing, wearing different clothes. All three derive ROOT from
their own location now, as the other ten tools already did. If a tool
ever reports a number that does not move when you change the thing it
measures, check what it is actually serving before you believe it.

**And the vertical gate had gone stale in the same way a label gate
does.** Its "below" figure took the nearest fixed thing under the button
- tab bar, daily-question circle, version label - and the circle counted
whether or not it was anywhere near the button horizontally. That was
safe while the button always sat above the circle, and wrong the moment
the button was narrowed and dropped beside it: the tool called a correct
layout "-10px above the tab bar". It only counts furniture the button
actually shares a column with now. `check-fixes.py` owns the horizontal
question and tests both axes together; this one owns the vertical, so it
has to ask the vertical question about the right things.

| | iPhone SE 2/3 | 13 mini | 14/15/16 | **17 Pro Max** | iPad mini | **iPad Pro 11"** | iPad Pro 12.9" | Dell Latitude | MBP 14" |
|---|---|---|---|---|---|---|---|---|---|
| viewport | 375×667 | 375×812 | 393×852 | **440×956** | 744×1133 | **834×1194** | 1024×1366 | 1366×638 | 1512×852 |
| onboarding Continue, y | 581 | 672 | 712 | **816** | 993 | **1054** | 1227 | 502 | 717 |
| …spread across the 6 screens | 54¹ | 0 | 0 | **0** | 0 | **1** | 1 | 0 | 1 |
| Home: tagline→button / button→furniture | 50/27 | 32/18 | 32/61 | **32/61** | 81/59 | **84/61** | 92/66 | 43/60 | 31/48 |
| Welcome: hint off the bottom edge | 33 | 46 | 46 | **46** | 33 | **33** | 33 | 29 | 29 |
| intro cards: padding in / gap between | 5/6 | 5/6 | 8/11 | **14/15** | 20/24 | **20/24** | 20/24 | 6/8 | 8/11 |
| daily question button | 54px | 54 | 54 | **54** | 74 | **74** | 74 | 74 | 74 |

¹ The one deliberate exception: on an SE the intro screen's four cards fill
the panel exactly, so its Continue is carried ~54px lower by the
self-cancelling last-card margin rather than sitting on the shared floor.
An **SE 1st gen (320×568)** is the one device that does not fit this screen at
all and is not expected to.

Rules those numbers encode, worth keeping: the gap **between** intro cards
always beats the padding **inside** them; **every onboarding Continue lands
on one line per device, and a change anywhere near these screens has to
leave that column alone** — it is the single most load-bearing row in the
table; the Welcome hint clears the bottom edge by ~29px in a browser
window, ~33px on a tablet and ~46px where there is a home indicator inside
that; and Home's button sits a short, roughly constant hop above the
furniture below it rather than centred between that and the tagline — the
daily-question circle on a phone, the tab bar on a tablet, where the circle
and the version label sit on the bar's own centre line in the corners
beside it.

**THE TAGLINE CAME BACK DOWN IN BUILD 131, and the button moved with
it.** Asked for directly: *"the start studying button needs to be way
closer to the bottom tab, and the wording above that button needs to be
lower and closer to the start studying button"*, alongside *"the
iPad/larger tablets have such a perfect layout and the phones need to be
just as great"*. That is the reverse of the build 94 request below, and
the same single auto margin serves both directions - `.hometitle-wrap`
went 1.3rem → .5rem, so the text dropped 13px and tightened to 32px
above the button without the button moving.
The button then moved on its own account: the 5rem row reserved for the
daily-question circle is only needed where the two share a column, which
above 24rem they do not, so `(min-width:24rem)` takes it to 3.25rem and
the button falls 28px. Measured, a 17 Pro Max went from 83px above the
tab bar to **61 - the same figure the iPad Pro 11" has**, which is the
parity that was asked for. The button is capped at 12.5rem on those
phones so it clears the circle by 25px on a 440px screen and 13 on a
393px one; `.panel.home .next` carries `min-width:14rem`, so trimming
its padding moves nothing at all and the cap is the only lever. The hero
grew with it (`min(27rem, 56vh)` and a .45rem column gutter), because on
a phone the hero's max-width never binds - the column does.

**The tagline→button figures went UP in build 94 and the button did not
move**, which is the property that made the change safe: reported as
*"the text above the start studying button is now too close to the
button. Move it slightly back up."* The greeting's `margin-top:auto` is
the only auto margin in that column, so every pixel added to
`.hometitle-wrap`'s bottom margin comes out of that auto — the text
group rises by exactly that much and the button stays put. A 17 Pro Max
went 27→45 above with 18 below unchanged and Continue moving one pixel;
an iPad Pro 11" went 67→84 with 61 below unchanged. An SE 2nd/3rd gen
is deliberately untouched (50/27): it is below the `46rem` height floor,
because a device with no leftover height has nothing for an auto margin
to hand over.

---

## Verifying

Empirically, every time. Reading the code and concluding it's correct has
missed real bugs that a thirty-second check caught.

1. `python3 tools/check-js.py index.html` — extracts every inline script and
   runs `node --check`. It strips HTML comments first, because the Firebase
   comment contains the literal text `<script>` and a naive regex reports a
   phantom syntax error on prose.
2. A targeted Playwright check of the actual change — measure or screenshot it.
   Chromium is at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`.
3. `python3 tools/sweep-layout.py` — the full device matrix. Every device,
   both orientations, installed and in a browser. This is required on every
   change, not just layout ones; a JS error only thrown on one screen shows
   up here too. It exits non-zero on any failure.
4. `python3 tools/check-sync.py` — the account-integrity gate. Required on
   anything touching the sync code, the rankings, reset, or boot; see
   **Accounts and the sync code**.
5. `python3 tools/check-behaviour.py` — the behaviour gate: launch,
   swipe, navigation, badges, cutscene. Required on anything touching
   those; see **Levels, badges and the ladder**.
6. `python3 tools/check-positions.py` — did what you positioned land where
   you meant it to, on all 21 devices. A green sweep does not answer this;
   see **Every device, every way in**.
7. `python3 tools/check-tours.py` — every tooltip still points at
   something. Required on anything that renames a class, moves a control
   between screens, or changes a tour's copy.
7b. `python3 tools/check-save-code.py` — the save-your-code banner and
   the build number on Welcome. Takes `--against`, and fails with 23
   red on build 158.
7c. `python3 tools/check-admin-auth.py` and
   `tools/check-admin-lookup.py` — the Firestore admin lookup. Neither
   needs a key: the first generates a throwaway RSA key and checks the
   pure-Python signer is **byte-identical to openssl**, the second
   drives `find` over Firestore-shaped documents with only the HTTP call
   stubbed. **A harness page must echo back the build it is serving**
   (`version.json`), or `--against` an older `index.html` trips the
   forced update and the run dies mid-test on "execution context was
   destroyed" — the update machinery working correctly, breaking a check
   about something else entirely.
7g. `python3 tools/check-curve.py` — **the badge thresholds, the level
   curve, and the ranks they gate, which are only correct together.**
   Each of those is a separately plausible number on its own; what
   makes them right is the relationship, and nothing else in the repo
   can see it. It asserts that every unit sits in the band its size
   puts it in, that no band asks for more than the flat 35 the live
   build charged, that **no XP total from 0 to 600,000 loses a level**
   against the previous curve, that levels 1-25 are byte-identical,
   that all the badges there are lands on the cap, that no rank asks
   for more badges than there are units, and that the end-of-test rows
   say what a run could actually do. Required on anything touching
   `BADGE_THRESHOLD_BANDS`, the curve constants, `TIER_UNLOCKS`,
   `MASTERY_BONUS` or the question bank's sizes. Fails with 11 red on
   build 189.
7h. `python3 tools/check-statsbadges.py` — the tappable stats, the badge
   case's slot shade and the daily-question announcement. The slot
   check is **pixel-measured**, because "the shadow is hard cut off at
   the top" is not visible in the DOM at all — the element is there,
   the gradient string is there, and the only thing wrong is how many
   levels of shade are left at the boundary. Fails with 13 red on 189.
   **The window matters as much as the measurement**: a first draft
   sampled 10px either side of the art box and reported a 4.9-level
   step on a build whose shade is smooth — the step was the tile
   ABOVE.
7i. `python3 tools/check-profilecard.py` — the Profile card, the Friends
   screen and the calendar's list view, on three devices. Fails with 17
   red on build 188.
7a. `python3 tools/check-unlocks.py` — the earned characters and the
   Secret Flares. Required on anything touching `summarize()`, the
   daily question, hundos, the Practice Test, the character table or
   the flares.
7b. `python3 tools/check-readd.py` — **does re-adding to the Home Screen
   still keep the account?** Wipes localStorage and IndexedDB together,
   which is what removing a Home Screen web app actually does, then
   relaunches from the URL the icon would carry. Required on anything
   touching the sync code, boot, the frame notice or the Safari
   hand-off. `--against <dir>` runs it on another build; it fails on
   129 with "re-added app came up on WELCOME - the account is lost".
   **A relaunch in it goes via `about:blank` first**: a goto to a URL
   differing only by its fragment is a same-document navigation, so
   nothing reloads and the check silently measures the app that was
   already open.
7f. `python3 tools/check-friends.py` — the friends gate: the friend
   code's shape and its separation from the sync code, whose row a
   request is written into, the live listener not rebuilding the screen
   under somebody's fingers, the online heartbeat and its five quota
   guards, and the invite action on an online friend. Required on
   anything touching friends, the board row's short fields, `isOnline`
   or lobby invites. Takes `--against`; sections 10 and 11 fail on 166.
7e. `python3 tools/check-vroom.py` — **two devices in one Virtual
   Room.** Required on anything touching the lobby, the chat, the start
   sequence, the results screen, Match settings or either game type.
   Section 9 is the tug gate; `--against` a copy carrying the OLD tug
   engine, not simply an older `index.html`, since the lobby fix landed
   in the same build and an older file fails section 1 and never
   reaches section 9.

**A `let` DECLARED AFTER ITS CALLER IS A TOP-LEVEL TIME BOMB.**
`firebaseBecameReady()` calls `attachLiveListener()`, whose
`liveUnsubscribe` used to be declared 500 lines further down. Function
declarations hoist; `let` does not, so if `fbDb` were ever ready while
the inline script was still running, that call would throw at the TOP
LEVEL and every `const` after it would stay in its temporal dead zone -
the whole app dead, from a line that looks fine. The only thing
preventing it is `defer` on the two Firebase tags in `<head>`, which is
a guarantee held somewhere else entirely and would be easy to drop by
accident. The declaration moved above its caller. Found by a check that
supplied Firebase synchronously, never by a device - and note that
`check-js` passes on it, which is the same lesson as the item below.

8. **Load the page and read the console before believing `check-js`.**
   These are different questions and only one of them is about syntax. A
   reference to a function that does not exist parses perfectly and then
   throws at the top level, which leaves every `const` after it in its
   temporal dead zone and takes out the rest of the script. That happened
   here: `buildTierIcon` was used in `RELEASE_NOTES` on the strength of a
   `grep -o "^function build[A-Za-z]*Icon"` that had silently truncated
   `buildTierIconSVG` into a name that was never real. `check-js` passed.
   The app did not boot. **Never take an identifier from a truncating
   grep** — `grep -n "^function name("` or nothing.
7. `python3 tools/shoot-flow.py` — screenshots by walking the app, for
   Madison, per **Showing the work**.
7c. `python3 tools/shoot-flares.py` — the glint, the banner and the
   sixteen-character contact sheet. Required on anything touching a
   character's artwork or the flares.
8. `python3 tools/shoot-results.py <outdir>` — the three screens that
   walk cannot reach: a drill result, the Virtual Room result, and a
   crowded race line. Required on anything touching the end of a run;
   see **The race line and the end of a run**. Looking at these found
   three spacing faults that every measurement had passed.

`check-vroom` section 7 and `check-behaviour` section 7 are the gates
for those screens, and both were written against the build they failed
on — `--against` an older `index.html` is the only thing that makes a
green run mean anything.

Serve over HTTP for anything touching `version.json` — `fetch` fails on a
`file://` path, and the update check swallows that silently by design.

The Firebase CDN is blocked in the sandbox, so the splash never self-clears;
remove `#splashscreen` manually, *except* when testing the update check, where
the splash race is the thing under test. Those two console errors are expected
and unrelated to any change.

## The chat (build 191)

- **A MESSAGE WRAPS; IT NEVER SCROLLS SIDEWAYS.** Reported directly. A
  flex column's items do not shrink below their content's minimum width
  unless told to, and an unbroken run of characters — a pasted link, a
  sync code, somebody holding a key down — has no break opportunity at
  all, so the item grew and took the list with it. Measured on build
  190: **481px of horizontal scroll** from one 64-character word. The
  fix is three things together — `min-width:0` on the item,
  `overflow-wrap:anywhere` on the text, and `overflow-x:hidden` on the
  list as the net so no future child can bring it back. `anywhere`
  rather than `break-word` IS right here, unlike on a badge label: a
  chat carries strings that have no word boundaries in them.
- **The panel is resizable and remembers it** (`--chat-h`,
  `class26e.chatheight`). On a phone the grip drags up to grow and down
  to close, which is the gesture nobody has to be taught; on a tablet
  there is a handle along the bottom edge. Both clamp against the
  viewport, because a stored height from a rotated or larger screen
  would otherwise leave the panel off the bottom.
- **THE SHEET GESTURE CLAIMS THE TOUCH ONLY ON MOVEMENT.** The old one
  excluded the two scrollable lists and nothing else, so a touch on a
  tab, the close ×, the sideways-scrolling roster or the text input
  still armed a vertical drag — and it armed on touchstart, so a plain
  tap twitched the panel before doing its job. It now starts only on the
  sheet's own dead chrome (asking whether the target IS a control,
  rather than listing the two that were known about), waits for
  `DRAG_SLOP` before anything moves, and on a close-by-drag leaves the
  offset in place for one frame so the transition continues from where
  the finger let go instead of snapping back first.
- **A MESSAGE'S AGE IS IN DAYS ONCE IT IS NOT TODAY.** "9:41" on a
  message from Tuesday reads as nine minutes ago at a glance, which is
  the one thing it is not. `chatMsgAge()` gives the clock time today,
  "yesterday", then "Nd ago", with the full timestamp in the title.
  `chatDaysAgo()` counts CALENDAR days, not elapsed hours: 23:59 to
  00:01 is one day, not zero.
- **THE HISTORY RESETS DAILY; THE CHAT DOES NOT.** Asked for in those
  words. The room, its code and everybody in it survive — only the
  backlog goes. Done inside the SAME trim the cap already does
  (`staleBefore`/`keepStale`), which is one write by one device, rather
  than as a sweep anybody could start: thirty devices each deciding to
  clear the same document at midnight is thirty writes for one result,
  and a write here is charged again as a read to everyone listening.
  **Never leave it empty** — a room whose whole history is old keeps its
  last few, or it opens as a blank box with nothing to say why.
- **FIVE REACTIONS, AND A REACTION BUMPS ITS MESSAGE TO THE BOTTOM.**
  `CHAT_REACTIONS`: heart, thumbs up, thumbs down, laughing, question.
  Keyed by a short ascii id rather than by the emoji, because the key
  ends up in a Firestore document and a glyph is a multi-byte string a
  future platform can render differently — the id is what the data is
  about.
  **The bump is a `bump` STAMP SORTED ON, not a reorder of the stored
  array.** Two reasons: `ts` stays what it always was, so the age label
  still says "yesterday" for an old message somebody has just reacted
  to; and `trimIfHost` decides who trims from the array's own last
  element, which a reorder would hand to whoever reacted rather than to
  whoever wrote. **Adding a reaction bumps; taking one off does not**,
  or somebody changing their mind drags an old message to the bottom of
  everybody's chat a second time.
  Reactions are the one thing in the chat that genuinely needs the whole
  array — toggling one rewrites a message in place, which `arrayUnion`
  cannot express — so the last snapshot is held rather than re-fetched,
  and a reaction costs one write and no read.
  **THAT MAKES A REACTION LAST-WRITE-WINS, WHICH SENDING DELIBERATELY IS
  NOT.** `send()` was rewritten to `arrayUnion` precisely because a
  read-modify-write let two people typing at once erase each other, and
  this path reintroduces that shape for reactions alone. Two people
  reacting inside the same round trip means one of the two reactions is
  lost. Accepted rather than missed: the messages themselves are still
  safe (nothing here appends), Firestore has no update-one-element-of-an-
  array primitive, and a lost reaction costs a tap where a lost message
  costs the conversation. **If reactions ever get busy enough for this
  to show, the answer is a separate `reactions` map keyed by message id
  — not a transaction**, which would cost a read per reaction on a
  project that is already tight on its quota.
  **The picker is absolute inside the list, not fixed**: the list
  scrolls, and a fixed popover would sit still while the message it
  belongs to slid away underneath it.

**A CLOSED PANEL IS A REAL BOX, AND `pointer-events` IS INHERITED.**
`.chatdock-panel, .chatdock-panel *{ pointer-events:auto }` looked like
belt and braces and was the opposite: the panel being `auto` already
makes its children `auto` and the panel being `none` already makes them
`none`, so the `*` half added nothing when open and broke the closed
state — `auto` on a descendant overrides `none` on an ancestor. On a
tablet the closed panel is a laid-out, invisible box under the chat
button, and the moment it grew (build 191 made it resizable) it reached
y=616 on an iPad Pro while the top-tab swipe runs across y=537. Rankings
and Profile both went "This Week → This Week → This Week".
**The sweep cannot see this. Nothing is out of place.** `check-behaviour`
caught it, which is the whole difference between "does it look right"
and "does it DO the right thing" — and it now asks the question directly
at the swipe's own coordinates (`elementFromPoint`, assert not inside
`.chatdock`), so the next thing parked in that corner is named rather
than inferred from three swipe failures.

### One chat button (build 194)

**THERE IS ONE CHAT BUTTON IN THE APP AND IT MEANS DMs.** Asked for in
those words — *"I don't want there to be two chat buttons, unless the
virtual room chat has like a different looking button and it's displayed
differently? Like maybe the virtual room one isn't a button but it's
displayed at the bottom of the lobby strictly and it says virtual room
chat ... And the button is still just strictly DMs."* So:

- The round dock button in the corner is DMs and notifications, on every
  screen, in a Virtual Room as much as anywhere.
- The Virtual Room's chat has **no control of its own anywhere**. It is a
  named section at the foot of the lobby on every device — the layout a
  tablet already had — with **"VIRTUAL ROOM CHAT"** on it, because a panel
  labelled "Chat" under a corner button that also says chat is the exact
  ambiguity this build is about.
- **The phone sheet and its toggle are DELETED, not hidden.** A fixed
  sheet nothing can open is still a fixed box that can catch a touch,
  which is how the closed dock panel ate the tablet's tab swipe in build
  191. It is also how this nearly shipped broken twice over: the toggle
  left behind `display:none` made `getComputedStyle(toggle).display ===
  "none"` — the test for "are you looking at this" — answer **always**,
  silently ending both the unread count and the preview banner; and the
  sheet's swipe-to-close handler was still bound, so the one path that
  still set `sheetOpen` (the preview banner's own click) armed a drag
  that wrote `transform:translateY()` onto a section sitting in the
  page's flow.

**MOUNTED IS NOT THE SAME AS BEING LOOKED AT.** With no sheet there is no
open event, so `VROOM_CHAT_CTX.isVisible` **measures**: the message list's
box against the viewport. On a phone the lobby is ~1,400px of scroll and
the chat is the last 200 of it, so being in the document says nothing.
`CHAT_CTX.isVisible` answers the same question for the dock — open, on the
chat tab. **There is no fallback any more**, and a host that forgets
defaults to *not* visible: over-announcing is a bug somebody reports in an
hour, never announcing is one nobody can see.

**SCROLLING TO IT IS READING IT.** The count is recomputed on a snapshot,
and a snapshot only arrives when somebody writes — so scrolling down to
the chat left "3" sitting over the three messages being read until the
next person spoke. An `IntersectionObserver` on the list is the only thing
that can see arrival happen. It complements `isVisible` rather than
duplicating it: that one answers "was this seen" for a message landing
now, the observer answers "has it just been scrolled to" for messages that
landed earlier. In the dock the list is inside a `hidden` tab body, which
never intersects, so the same code means the same thing there.

**A COUNT NOBODY CAN SEE IS NOT A COUNT.** The unread pill used to be
drawn inside the toggle, so deleting the toggle left it in a `display:none`
parent — and `check-chat` went on passing, because it only ever asked
whether the `hidden` ATTRIBUTE was off, which it dutifully was. It lives
in the chat's own title row now, beside the name of the chat it belongs
to, and the gate measures a real box in that row. What the gate **cannot**
ask is whether the count is in the viewport: on a phone unread and
on-screen are mutually exclusive by construction, which is what the
preview banner is for.

**A PREVIEW SAYS WHICH CHAT IT CAME FROM.** *"When someone sends
something in there you still get the screen notification, but it would
appear so people know it's the virtual room chat and not a DM."* The room's
banner carries a blue **VIRTUAL ROOM** tag and a blue left bar;
`CTX.alertTag` is null for DMs, so a DM preview reads exactly as it did.
Its own colour rather than the accent, so it says Virtual Room on all seven
themes. **Both banners are in `NOTICE_OBSTRUCTIONS` now**, because two of
them can genuinely be up at once — two chats, two listeners, both live in a
lobby — and two banners at the same CSS offset is one banner nobody can
read.

**A VIRTUAL ROOM NO LONGER COSTS YOU YOUR DMs**, and the gate that said
otherwise was failing the app for being right. `syncChatDock()` used to
force-leave the chat lobby and flip the dock onto notifications on entering
a room, which was correct while the two chats competed for one button. It
also could not stay: that function runs on **every screen change**, so a
chat joined inside a room was left again on the next navigation — a join
write and a leave write per screen. The quota cost is a second listener and
it is **accepted rather than missed**: the room document is the expensive
one by an order of magnitude (thirty devices writing progress per
question), a DM between two people is a handful of writes an evening, and
it is still one chat at a time — opening another detaches the first.

**SIXTEEN CHAT COLOURS, NOT EIGHT, AND HAND-PICKED RATHER THAN SPACED.**
*"These could be large so ensure there's multiple chat user colors."*
Eight wrapped on the ninth person, so in a class-sized room two people
shared a colour and the whole point of colouring a name went with it.
Named rather than evenly spaced round the hue wheel, for the same reason
the badge families are: even steps put four greens in sixteen slots,
because green occupies about a sixth of the wheel and reads as one colour
whatever the spacing says. **The race line indexes the same table**, so
adding to it widens the markers' palette too — which is the right
coupling: a marker and a name are the same person.

### Several chats (build 195)

**TWO VARIABLES THAT SOUND THE SAME, AND THEY ARE NOT.**
`chatRoomCode` / `CHAT_ROOM_KEY` is **which chat is OPEN on this
device** — localStorage, per device, as it always was. `store.chats` is
**which chats you are a MEMBER of** — synced, so your phone and your iPad
show the same list. Everything below follows from keeping those apart.

- **Open, close and leave are three different things**, and for two
  builds there were only two of them: the way out of a chat was Leave,
  which deleted your participation, so "go back and look at the other
  one" meant burning the one you were in.
- **Closing writes NOTHING.** It detaches this device's listener and puts
  the list back. You stay in the participants map with the `joinedAt` you
  arrived with — which is what gives you your colour — so re-opening
  costs no read and no write.
- **Leaving takes the row with it** (`forgetChat`), because a chat you
  left is not one you are a member of, and a row offering a way back into
  it is a lie. `leaveChatByCode()` does the same writes for a chat you
  are not sitting in, straight at the document.
- **ONE LIVE LISTENER, STILL.** A list of five chats is not five
  listeners: opening one attaches, closing or opening another detaches.
  That is a deliberate quota decision, not an oversight — a read is
  charged to every listener on every write.
- **The consequence of that, stated plainly: a message in a chat you do
  not have open produces no banner.** What it produces is an unread row
  the next time the list is looked at, which is what the per-row fetch
  below is for.
- **THE LITERAL 30 IN `applyLoadedData`, NOT `CHAT_LIST_MAX`.** That
  function is reached from the top level during boot and the const is
  declared some ten thousand lines below it — a reference there is the
  TDZ time bomb this file has been taken down by five times, and it
  reports an unrelated name when it goes off. `var` would be *worse*:
  hoisted but undefined, and `slice(0, undefined)` returns an EMPTY
  array, so it would quietly erase somebody's chat list on load.
- **A chat is named after the people in it**, not by its code
  (`nameChatFrom`), with yourself left out — every chat you are in has
  you in it, so your own name carries no information and costs the width
  of the row. The name is learned from the **raw** participants map on a
  snapshot, never the present set: a row called "Ann" must not become
  "Bo" because Ann's phone went to sleep.
- **`rememberChat()` saves only on a change.** It is called from the
  panel's roster render, which runs on every snapshot — saving
  unconditionally would push the whole progress document to Firestore
  on every message anybody sends.
- **One `get()` per row, only when the list is being looked at, and
  throttled** (`refreshChatList`, `CHAT_LIST_REFRESH_MS`).
  `rebuildChatTab()` runs on every screen change whether the dock is open
  or shut, so an unguarded fetch there is thirty reads per navigation per
  device — the surest way to spend a day's quota by lunchtime.
- **Rows are painted in place** (`paintChatRow`), not by rebuilding the
  tab: a rebuild remakes every row, so thirty replies landing one after
  another would rebuild the list thirty times under the finger.
- **Unread is a comparison, not a count.** `class26e.chatseen` holds how
  far you have read per chat — localStorage, never `store`, the same call
  `class26e.daily.seen` makes: synced, it would mark a chat read on your
  iPad because you read it on your phone. Your own last message never
  marks a chat unread, and that is tested **by key, not by name**: two
  people in this class can share a first name.
- **The unread dot goes on the row's flex line, not on the name.** The
  name is `overflow:hidden` with an ellipsis, so a `::after` inside it is
  clipped away by exactly the long names most likely to need it.
- **The delete arms before it fires.** One tap on the × beside a row says
  "Leave?" and a second confirms, with a 3.2s window. Leaving is a write
  nobody can undo — the other people see you go — and a bare × beside a
  row is the easiest thing in the app to hit by accident. It says what it
  is about to do rather than asking in a dialog, which on a panel this
  size would cover the list it is asking about.

No committed regression suite exists yet. Worth building.
