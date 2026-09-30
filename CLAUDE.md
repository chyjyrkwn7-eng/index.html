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

**THE RANK NAME IS ITS COLOUR: Iron, Bronze, Gold, Platinum, Sapphire,
Amethyst — and Supernova, the one exception, below** (build 225; see
that section for why Silver and Emerald went). That is the thing
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
  way round, not a miss. (Race has no time-limit control either since
  build 245 - it is a fixed 45s per question, see **Build 245** - so
  the control is gone from Match settings for every mode, and an old
  room document's `timeLimit` is simply not read.)
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
  a new period (rolled over since this device last saw Home) plays the
  RECHARGE instead - see **Build 245 - the polish list**; the old
  `is-fresh` five-pulse light-up and its CSS are unused since then;
  `is-done` greys it out. The button is `3.4rem` on a phone and
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
- **"Flares" ≠ badges, and "Secret Flares" are a hunt, not a rank requirement.** Flares are the
  orbiting marks on Home, one per rank — the thing a rank hands over.
  Badges are the sixteen unit awards on Profile. The two are separate
  and the words are not interchangeable in copy. Secret Flares were a
  third thing, a hidden three-colour hunt gating the top rank; they were
  scrapped outright. `store.mysteryColorsFound`, `testsUntilMystery` and
  the `mysteryStars` guard survive as defaulted, unread remnants — see
  **Ranks**. They then came back as a HUNT ONLY, unlocking Void (see
  "THE SECRET FLARES ARE BACK" under **Ranks**), so the version-history
  copy describing the hunt is correct again - re-checked in build 208.
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
0. **RUN THE GATES ONE AT A TIME, and never alongside a sweep.**
   `check-friends`' "a stats push republishes seenAt" assertion is
   reproducibly RED while the machine is busy and green when it is idle,
   and that is not a harness artifact: under load the app's own boot push
   has already landed, and `pushLeaderboardRow()`'s deferral branch tests
   the urgent signature and the elapsed time but — unlike the dedupe
   branch directly above it — **not whether the document key changed**,
   so a push to a NEW publicId is held for up to `ROW_SCORE_PUSH_MS`.
   The row still arrives on the deferred timer, so it is a delay rather
   than a loss, which is why it has never been reported. Worth fixing,
   with a check that names the key change rather than the timing.

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
   `python3 tools/check-results.py` — the end of a run: the rewards reveal,
   the review screen, Pause on both. Required on anything touching
   `summarize()` or the results screens.
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

### The phone batch (build 196)

**A HEIGHT GATE WRITTEN IN `rem` MOVES WITH THE READER'S TEXT SIZE.**
This is the finding behind three reports that had each been "fixed"
several times: Home's planet too small, its wording too close to the
planet, its button too far from the tab bar. Every phone tier on Home
and Welcome was gated `(max-width:32rem) and (min-height:46rem)` — 736px
of height *at a 16px root*. Simulated at a larger root font, which iOS
hands out through its own text-size settings, the tier flips off on a
956px phone and the layout falls through to the base rules, which is
exactly the screen that kept being reported. **Those gates are in px
now** (`512px`, `736px`, `576px`, `768px`, and the tab bar's own
`639px`): a device's size decides which layout it gets, and nobody's
accessibility setting can change that. Convert any new one the same way.

**THE PLANET IS FULL-BLEED ON A PHONE, AND HOME AND WELCOME SHARE ONE
SET OF NUMBERS.** The cap was never what limited it — `min(29rem,52vh)`
is 464px on a 17 Pro Max and the sphere measured 419, because the hero
is `width:100%` inside a column inside `.wrap`'s padding. 3.5rem of
negative side margin is exactly what that column gives away, so the
planet now spans the screen edge to edge on every phone. There is
nothing left to take: wider than the phone is wider than the phone.

**THE SLACK IN HOME'S COLUMN IS SPLIT, NOT STACKED.** The greeting's
`margin-top:auto` was the only auto in the column, so every leftover
pixel went above the text and the text group came to rest on the button:
measured, **153px of empty screen under the planet and 5px between the
tagline and Start Studying**. An auto on the button as well divides it,
and the hero's fixed bottom margin biases the division towards the top —
which is the shape the iPad has and was signed off with (108 under the
planet, 59 above the button). A phone now lands at 105/50 instead of
153/5.

**THE UNIT-SELECTION BAR WAS GIVEN AN EXPLICIT WIDTH, AND THAT IS WHY
TIGHTENING ITS GAPS DID NOTHING.** `(max-width:39.99rem)` set
`width:calc(100vw - 1.5rem)` — 12px of margin per side against Home's
own 32 — so the two bars either side of a tap looked like different
objects. It is `calc(100vw - 2.6rem)` now, 398px inside a 440px phone
against Home's 376: still the wider of the two, which is the
relationship asked for both times, without touching the edges. The
navrow inside is `flex:1 1 auto`, so **the ceiling is what sets this
bar's width** — gaps and padding cannot shrink it.

**THE iOS ZOOM IS NOT A FONT-SIZE PROBLEM ANY MORE, WHATEVER THE
DOCUMENTATION SAYS.** Every text field in the app measures 17px and it
still zooms, reported three times. `resetStuckZoom()` unwinds a scale
Safari is already holding, which is the wrong half: by then the page has
jumped mid-word. The clamp now goes on **at focus** — `maximum-scale=1`
on `focusin`, off two frames after `focusout`, through `focusin`/
`focusout` on `document` because every field in this app is built at
runtime. Between typing and not typing, only the typing is clamped, so
pinch-zoom is never taken away from anybody.

### The Overall board and the person card (build 196)

- **THE TIER ALWAYS WINS.** Overall ranks by rank tier first, then by
  progress towards the next rank: level ÷ next rank's level and badges ÷
  next rank's badges, averaged, **uncapped** — "if someone exceeds the
  requirement they should continue receiving credit". A Gold at 49/15
  therefore sits above a Gold at 54/7, which is the worked example that
  was sent. The percentage is a sorting value and is deliberately not
  printed: a number that goes past 100 needs a paragraph.
- `overallProgressOf(level, badges)` takes the numbers rather than a
  store, like `rankOfStats` beside it, because the board asks it about
  other people from a published document.
- **A board may bring its own `sort`.** Two of the three rank on a single
  published field; Overall cannot be expressed as one.
- **The board is seeded from `leaderboardRows` at mount**, so it paints
  in the frame the tab opens instead of showing "Loading the rankings…"
  while waiting for a round trip it did not need.
- **An empty snapshot never takes the board away.** Firestore delivers
  the cached answer first and a cache that has not been told about the
  collection answers with nothing — which emptied `entries` and left
  `liveEntries()` to synthesise the only row it can, yours. That is
  "sometimes I only see myself until I hit another tab and come back".
  Every other reader in the file already carried this guard.
- **The trend rolls on a clock, not a calendar day.** It shipped
  comparing against midnight's board, so a new install had nothing to
  compare with until tomorrow and, after that, most of an evening's
  movement had already been folded into "yesterday". `LB_TREND_ROLL_MS`
  is 4 hours.
- **No rank emblem on a rankings row, and no glow on a list avatar.**
  Both were added deliberately and both are now off, by request: the
  rank is on the row in words, and a halo per row reads as a smear
  rather than as people. The emblem stays where a character is drawn big
  — the lobby, the results screen, the person card.
- **The person card is centred, not a drawer**, on its own near-black
  surface: rank in its own colour, level under it, then XP / badges
  (n of 16) / hundos / correct (was tests; see build 201). `xp` and `tests` are **new published
  fields** on the leaderboard row — an older document reads 0 and
  self-heals on that person's next push, the same contract every field
  on that row has had.
- **"Already friends" was the one state with nothing to do.** It is
  **Message** now, and `openDirectChatWith()` finds the DM you already
  have with somebody — a chat whose only other member is them, which is
  what `store.chats[].with` is for — or starts one and invites them.

### Smaller things that were each reported (build 196)

- **Keep screen awake moved to Motion & interaction**, and its hint
  stopped describing one moment ("doesn't dim out mid-question") as
  though the setting were about tests.
- **"Share Nova" → "Share & install"**: the section holds two buttons
  and only one of them shares anything.
- **Add to Home Screen carries the accent**; Share and Report a bug stay
  quiet, Reset stays red. Tinted rather than filled, so it cannot
  out-shout the one control on that screen that should be able to stop
  you.
- **The XP bar's quarter ticks came off.** They were asked for once and
  are now read as damage — "obviously bugged". A decoration that reads
  as a defect is worse than no decoration.
- **The friends count and the days-remaining count were riding
  `--theme-c3`**, which lands red on the default theme. Red in this app
  means Reset and a wrong answer. They are the online green and the
  pending amber now, fixed rather than themed, because the meaning is
  fixed.
- **The two Profile plates are `align-items:stretch`.** They carry
  numbers at different type sizes, so sizing each to its own content
  made one visibly shorter than the other.
- **The calendar key gained its amber test-day dot.** The grid drew three
  marks and the key explained two.
- **Exam picks its own length again.** It was folded in beside Game,
  which genuinely has none — and Exam's own card promises "pick your own
  units and length".
- **Game's difficulty was inside a collapsible that Game hid.** The
  Speed slider is the difficulty and it lives in "More options", which
  was hidden for Game on the reasoning that every row inside was
  excluded for Game — every row except the one that only exists for it.
  Both that check and the stray "Options" label now ask **whether
  anything inside would show**, from the sections themselves, rather
  than naming the modes that happened to be true when they were written.
- **Leaving a test lands on Home**, not on mode selection — one answer
  rather than two, since the daily question already did this.
- **The Review mode icon is green.** It was the one mode icon with no
  colour; green because it is the only mode that scores nothing and
  green is already this app's colour for a right answer.
- **The orbit dots answer a tap.** They are what is left of the Secret
  Flares, and three silent dots among seven marks that all say something
  read as broken rather than as scenery.
- **The contextual popup is placed against its real height.** It flipped
  above the target whenever a guessed 90px height plus a 90px floor said
  it would not fit, which on a phone is most of the screen.

### The Virtual Room (build 196)

- **Each choice carries its own description, above its own button.** One
  paragraph at the top covering both and another underneath covering
  neither is what "badly spaced out" was pointing at.
- **Open rooms says what the list is** ("Anyone in 26E can join these")
  and a row says it as a sentence — "2 people waiting · Race on 4 units"
  — rather than three tags joined by dots.
- **The lobby's chat is not a box.** Build 194 gave it a border when it
  stopped being a sheet, which made it a card at the foot of a screen
  made of cards.
- **Invite friends sits under the roster**, which is the list it makes
  longer.
- **The summary names the game with its icon** — a rope for Tug of War, a
  flag for Race — because "Virtual Room" is the one thing everybody in
  the room already knows.
- **The Virtual Room's unit screen gets the floating glass pill**, the
  same object the main menu's bar is, carrying one button.
- **THE QUESTIONS SLIDER'S TOP IS THE TOP OF THE POOL.** It was built
  with a placeholder max of 200 before any units were picked, and a range
  input snaps to a step lattice measured from `min` — so with 5-question
  steps and a pool of 187 the highest reachable stop was 185 and the
  thumb stopped short with empty track past it. Same lattice fix the
  Length slider already carried.
- **Tug of war is longer and scales with the bank.** It scaled per
  question against a fixed seven-minute target, so more questions meant a
  faster clock rather than a longer match, and every real match flattened
  out at the ten-minute cap. Target 10 minutes, cap 20, floor 9s.
  `check-vroom`'s three pacing assertions encoded the old decision and
  were re-read: a floor nothing goes under, a short match that stays
  short, **longer means longer**, and a ceiling.
- **The rope is pulled, not read.** It was drawn beautifully and held
  perfectly still while a marker slid along it, which is a progress bar
  with a texture on it. The whole rope now shifts towards whoever leads
  (damped to a third of the knot's travel), the leading end tightens, and
  a line under it says who leads and by how much. **The shift is applied
  in `refreshTugLive()` as well as in the builder** — that is the
  function that runs when somebody else answers, so without it the rope
  would be dragged exactly once, when the screen was built.

### The themes, the two Virtual Room rows, and two things that looked bad (build 197)

- **A THEME'S THREE STOPS HAVE TO POINT THE SAME WAY, NOT JUST EXIST.**
  Build 196 gave every accent all three `--theme-c1/2/3` stops, which
  fixed *"just looks like one color"* — and it was still reported back
  as *"the unlocked themes could still look better, they still don't
  look as good as the default one."* Looked at properly, all seven
  paired their own colour with the **same warm gold c1** the default
  has: a cool rank had a gold glow fighting a blue accent, and the two
  near-grey ranks had gold fighting nothing at all. The default works
  because its three are NEIGHBOURS swept in one direction — gold 40°,
  orange 20°, magenta 335° — lighter and warmer on one side, deeper and
  towards violet on the other. So the seven are **generated from their
  own rank colour by that same rule**: c1 is 20° away from violet, 11%
  lighter, saturation ×1.05; c3 is 45° towards violet, 13% darker, at
  62% of the saturation.
  **THE RULE IS VALIDATED AGAINST THE DEFAULT rather than trusted.** Fed
  the default's own c2 (`#F5804D`) it returns `#FBCE7F` / `#C63978`
  against the real `#FFD37A` / `#C23B7A` — a few levels on each channel.
  A formula that reproduces the triad everyone already likes is the only
  reason to believe it for seven nobody has seen. Two adjustments, both
  stated in the file rather than hidden: a nearly-grey rank (Iron,
  Silver) has no hue to build from, so **saturation is floored at 34%**
  or the glow comes out as three greys; and c1 is kept out of the acid
  yellow-green band, which is where Gold's "away from violet" would
  otherwise land and which nothing else in this app is.
- **A LOBBY IS WHERE A CHARACTER STANDS OUT, AND A LIST IS NOT** — the
  two halves of one request, pulling opposite ways in the same build.
  *"Remove the glow from behind the friends list character and ensure
  it's removed from the characters on the leaderboard"* and *"while in a
  lobby or after a match, that's where the character will stand out — a
  bit larger, with the glow behind them, with their rank and level
  displayed."* A row in a list of twenty is a smear of colour down the
  screen; a lobby is four or five people you are about to race, each
  with a whole row. So the boards and the friends list lost their halos
  and the two Virtual Room screens gained them, at `3.4rem` on a phone
  and `4rem` from tablet up against the `2.6rem` list size.
- **The glow is scoped to the character's own `svg`, never a bare
  `svg`.** The rank coin is a sibling `<svg>` in the same box, and a
  bare descendant selector lit somebody's rank emblem in their
  character's colour.
- **`.vroom-levelchip` is retired, and that is the same "two marks on
  one avatar" call the boards already made.** The level was a chip stuck
  on the corner opposite the rank coin. It is on a line under the name
  now, beside the rank in the rank's own `RANK_COLOR` — the same line
  the friends list and the invite sheet show, so a classmate reads the
  same everywhere. The CSS rule is **deleted rather than left
  unreachable**: nothing builds one.
- **Both Virtual Room rows open the same person card**, which is the
  rest of *"if you click their profile while in a lobby, or after a test
  in the results screen, or click them on the leaderboard, that same
  centred screen will pop up."* A participant key **is** the `publicId`,
  which is what lets `openPersonSheet` resolve the friend state from a
  room document. Never your own row — there is nothing to do with
  yourself, the same rule the boards follow.
- **So the room document publishes `hundos`, `xp` and `tests` too.** The
  card has four progress figures and a room only carried two of them, so
  two thirds of it would have read as zero for everyone in the lobby.
  Written at create and at join, read with a fallback, so a room made by
  an older build still renders.
- **A 4.5px TALL GRAB HANDLE IS NOT A HANDLE.** *"Changing the size of
  the box on the iPhone is very bad and hard to do."* Measured, the
  thing you are asked to grab was **38×4.5px** — a tenth of the 44px
  minimum this file sets for every other control, on the one control in
  the app whose entire job is to be dragged. Same fix as the Settings
  links in the tap-target sweep: **the target grows and the visible mark
  does not.** The element is full width with `.95rem`/`.55rem` of
  padding and a negative top margin so nothing below it moves, the bar
  is drawn by `::after`, and `touch-action:none` sits on the handle so
  the page's own scroll cannot steal the one gesture that element
  exists for.
- **The recent test rows are cards now, not ruled lines.** *"All those
  tests, or boxes of how they are separated, needs to look better, it
  looks bad."* They were four lines of serif name and mono metadata
  stacked with nothing between them but a hairline, on a screen where
  every other group of things — the calendar card, the friends card, the
  badge tiles — is a surface with an edge. Each is its own recessed card
  on the same recipe the Profile plates use, so it arrives as something
  the screen already does rather than a fifth new look, and the press
  state lands on the card instead of washing the full row width.
- **196 PUT START STUDYING BACK ON THE DAILY-QUESTION CIRCLE, ON THE
  PHONES IT NEVER MEASURED.** `check-fixes` had not been run on 196, and
  it found the exact defect this file already records from before the row
  was reserved: on a 13 mini installed the button was `76..300` against a
  circle at `292..346` — an **8×9px overlap** — and a 360px Android in a
  browser cleared it by 8px against the 12px floor. 196 lowered the
  button onto its floor and paid for it by trimming the button to 200px
  so the two clear each other horizontally, but that trim sat in a
  `min-width:24rem` tier, so **every phone narrower than 384px kept a
  224px button in the circle's band**. Three things came out of fixing
  it:
  - **The two remaining Home gates were still `rem`**, so a 440px phone
    at a 21px root computes 20.95rem and falls out of the ≥24rem branch
    entirely — back to the 224px button and the 4.7rem reservation, which
    is precisely the "the button isn't lowered" report 196 was answering.
    They are `384px`/`512px` now, identical at a 16px root.
  - **A `min-width` ON ITS OWN MOVES NOTHING when the content is wider.**
    Dropping the floor from 14rem to 10.5rem only stopped that floor
    applying; the button is 189px because its LABEL is 145px plus 20.8px
    of padding either side. Measured after that change alone: a 10px gap,
    still under the floor. The padding had to come down with it (to
    `.9rem`, ~176px), and the vertical padding is untouched so the 44px
    tap target does not pay for it.
  - **AND THE TWO PHONES FAILED IN DIFFERENT AXES**, which is why one
    lever could not fix both. A 375px phone clears the circle
    horizontally once the button is trimmed (~16px). A 360px one cannot —
    its centre is 20px further left, so the circle sits 15px closer and
    the trim only buys 9px. What 196 actually spent there was VERTICAL:
    the shared full-bleed hero is square, so going full-bleed made it
    ~21px taller, and on an overflowing panel that came straight out of
    the gap. Measured either side: 195 had 17px (13 mini) and 27px
    (Android); 196 had −9px and 3px. So below 368px the hero gives back
    what the bleed gained (`max-width:min(32rem, 58vh, 94vw)`) and the
    whole column rises — 3px to 26px. **It carries the same
    `min-height:736px` floor as the block it refines**, or a four-class
    selector reaches down and undoes the short-phone hero tiers, and it
    has to sit AFTER that block because the selector is identical and
    source order is the only thing deciding.
- **AND THE CARD BROKE A GATE BY BEING RIGHT, the fifth time this has
  happened.** `check-fixes` asserts the test-review chevron sits at the
  far end of its row, and it measured against `getBoundingClientRect()`
  — the BORDER box — which was the same thing while the row was a
  full-bleed ruled line with no side padding. A card has padding, so
  every row came back 15px out (13.6px of padding plus the 1px border)
  and the check went red for the row being correct. It measures the
  row's **content** edge now, which is what it was always trying to
  say and which survives any padding the row carries. **Proved it can
  still fail before believing the green**: a temporary
  `margin-right:40px` on the chevron reports exactly 40px on every row.
- **AND THE TWO FLAGS THAT CAME WITH IT ARE ACCEPTED, NOT MISSED.**
  `check-positions` now reports Start Studying "off-centre" on an SE
  2nd/3rd gen (50 above / 99 below) and a 360px Android (38 / 95). Both
  are the button sitting well clear of the circle rather than centred
  between the tagline and it, and both are the intended trade:
  - The SE's is not new and is not mine — its short-phone tier trims the
    hero so the button clears the circle, which is the collision fix from
    build 96. It only surfaces as a flag because 196 changed what
    `check-positions` measures the button against (the circle row, not
    the tab bar), and 196 never ran this check.
  - The Android's grew by the 23px the hero gave back. That is the price
    of the fix, on the one device class it applies to: every iPhone in
    the matrix is 375px or wider and is fixed by the button trim alone,
    with its hero untouched.
- **The Rank tab was reported as sitting off-centre on a phone and
  measures centred, so nothing was changed.** Checked on an iPhone 16
  Pro Max, a 14/15/16 and an iPad Pro 11", at a 16px root **and at 21px**
  (the `rem`-gate trap that was the real cause of the Home screen
  report): `heroOffCentre` came back 0–1px every time. Recorded here
  because a guess at a layout that measures right is how a screen that
  was fine stops being fine — it needs her screenshot, or the device's
  own text-size setting, to go on.

### The three that were reported as not fixed, and were not (build 198)

*"you literally did NOT fix the first three, they did not get fixed at
all"* — with a photo of the unit-selection bar. All three were real, and
each had failed for a different reason. **None of them was found by a
gate; all three needed a measurement of the SHIPPED build on the
reference device.**

- **THE TAB BAR WAS SIZED FROM THE VIEWPORT AND HOME'S IS SIZED FROM ITS
  CONTENT, so the two can only agree at one width.** Home's bar is
  shrink-to-fit and stops growing at 376px. `width:calc(100vw - 2.6rem)`
  never stops. Measured across the matrix:

  | device | Home bar | start-tab bar |
  |---|---|---|
  | 375 phone | 351 (12px in) | 333 (21px in) |
  | 393 phone | 369 (12px in) | 351 (21px in) |
  | **440 Pro Max** | **376 (32px in)** | **398 (21px in)** |

  So it was NARROWER than Home on every phone except the one it was
  reported from, where it overtakes Home and sits 11px closer to each
  edge. The number had been tuned on a device where it happened to look
  right. It is `width:min(23.5rem, calc(100vw - 1.5rem))` now — Home's
  own formula — so the two bars are identical on every phone and cannot
  drift again, with `min-width:0` on the nav row paying for the Start
  pill out of the icons rather than out of the margins. Measured after:
  376/376 on a Pro Max, every tab still 44px, no overflow anywhere.
  **`width:auto` with a `max-width` is not the same fix** — shrink-to-fit
  plus `min-width:0` collapses the bar to its own minimum, 266px on every
  phone. The explicit `width` is load-bearing.
- **THE ZOOM FIX WAS THE ZOOM.** *"The typing ZOOM STILL WASNT FIXED, it
  just zooms in and zooms out now."* A previous pass concluded the 16px
  floor "did not stop the zoom" and added a clamp that swapped the
  viewport meta to `maximum-scale=1, user-scalable=no` on focusin and
  swapped it back on focusout. Two viewport rewrites around one tap ARE
  a zoom in and a zoom out.
  Measured before removing it, on every screen the harness can mount:
  **twelve text-entry fields, not one under 16px** — `.searchbox`, the
  field it was last reported against, computes 17px. iOS only zooms to a
  field under 16px, so there was nothing left for a clamp to prevent and
  the only thing it could still do was the thing it was reported for.
  The clamp is deleted; the floor and the conditional `resetStuckZoom()`
  (which does nothing unless `visualViewport.scale > 1.01`) stay.
  **Never re-introduce a viewport swap that runs on every focus.** If it
  is reported again, measure which FIELD was focused and what it
  computes to.
- **AND HOME MOVED THE WORDING THE WRONG WAY.** *"the wording is too high
  and too close to the planet system"* — build 196 gave the greeting and
  the button an auto margin each, which splits the slack evenly. On a 17
  Pro Max that took the gap under the planet from 195's **120px to 69px**:
  51px CLOSER to the planet, the opposite of the request, with the text
  left floating in the middle of the empty half of the screen.
  **The slack is 62px, not 141.** The panel is MIN-HEIGHT driven here, so
  the empty half of the screen is not all distributable — an even split
  of what LOOKS like the free space is not what the autos are dividing.
  The first attempt (a 2.2rem fixed gap above the button) moved the text
  13px and measured 82/59; `.5rem` spends nearly all of it and lands
  110/32, with **the button not moving** — a fixed margin here comes out
  of the auto above it, which is the same arithmetic the build-94 note
  records in the other direction.
- **THE PLANET CANNOT GET BIGGER ON A PHONE WITHOUT CROPPING ITS ORBIT.**
  Asked for ("the planet system is too small") and not done, deliberately.
  The hero is already `calc(100% + 3.5rem)` — 442px on a 440px screen, so
  it spans the full width and the outer ring is already clipped by a
  pixel each side. Measured, the sphere is 31% of the screen's width on a
  phone against 21% on the iPad, so it is proportionally LARGER than the
  tablet that was called perfect; what differs is that the iPad shows the
  whole orbit system with air around it and the phone does not. Growing
  it further only crops more ring. That is a look decision with a real
  cost, so it wants asking about rather than assuming.

### THE REFERENCE PHONE IS NOT 440px WIDE (build 199)

**Read this before touching any phone layout.** Eleven rounds of
phone fixes — Home's planet, its wording, its button, the unit-selection
bar, the typing zoom — were each measured correct at 440×956 and each
reported back as *"not even changed"*. They were not changed, on her
phone. A screenshot from the device finally showed why: the planet
small with its whole orbit visible, `v6.9` in the corner (phones hide
it), a 224px Start button (phones use 200). **That is not the phone
layout at all.**

Measured off her screenshot against elements whose CSS size is known —
the "?" circle, the button, the tab bar, the version label — the device
lays the app out **~518 CSS px wide and ~1125 tall**. A 440pt screen at
518 CSS px is a **page zoom of about 85%** (Safari's aA menu / Page
Zoom), which a Home Screen app inherits. Rendered at 518×1125, the
harness reproduced her screenshot to within a few pixels: the circle's
top at 936 on both.

Every phone gate in the file stopped at `max-width:512px` (or `32rem`,
the same thing at a 16px root). 518 is past all of them, so her phone
got the base styles with none of the phone refinements, and every fix
was applied to a layout it never uses.

- **The phone boundary is now `max-width:639px`** — everything below the
  tablet breakpoint (`min-width:40rem` = 640) is a phone. 19 gates moved
  (9 × `512px`, 10 × `32rem`). Nothing in the matrix sits between 513
  and 639 in portrait except the zoomed phone; the landscape phones that
  do are excluded by the height floors most of these rules carry.
- **The typing zoom had the same cause.** At 85% a 17px field is drawn at
  ~14.5px on the glass, and iOS zooms to anything under 16px ON THE
  GLASS. The CSS floor was right in CSS pixels and wrong where it
  counts — which is why "every field measures 17px" and "it still
  zooms" were both true. `syncFieldFloor()` measures the zoom (short
  side of the layout viewport over short side of the screen, so rotation
  is not mistaken for zoom), and on a zoomed touch device sets
  `html.page-zoomed` and `--field-floor` so every text field lands at
  ~17px on the glass: 20px CSS at 85%, 21px at 80%. At 100%, in
  landscape and on a laptop the class is never set and nothing changes.
- **`iPhone 17 Pro Max @85% zoom` (518×1125) is in `DEVICES` now**, so
  the sweep, check-fixes and check-positions all run it. **A matrix that
  only contains the device's nominal size cannot see the device as its
  owner has it set up**, and that gap cost more rounds than every other
  bug in this file put together.
- **The lesson is not "check 518".** It is that a report of "not
  changed" is DATA: when a fix measures right and is reported as absent,
  the device is not running the layout you measured. Ask for, or
  reconstruct from a screenshot, the CSS viewport the device is actually
  using — before writing a single rule.

### The glow was clipped into a box (build 200)

*"The top of the screenshot doesn't blend (the background and stuff),
it's hard cutoff."* `.panel.home` is `overflow:hidden` — there so the
full-bleed planet cannot scroll the page sideways — and Home's panel
starts just under the status bar, while the planet's glow
(`.homeglow-hero`) reaches ~200px above it. So the glow was cut in a
straight line across the screen at the panel's top: measured, a uniform
+6-level step at y=69 on the reference phone with flat background above.
Clipping x at the panel instead of hiding both axes removed the top edge
and exposed the next one: the panel sits ~20px in from the glass, so the
glow now stopped in two vertical lines down the sides.

- **Home's panel clips nothing** (`overflow:visible`) and the sideways
  clip moved to `.wrap:has(.panel.home.screen-home-actual)`, which spans
  the viewport. The glow now fades out at the screen edges, and there is
  still no horizontal scroll on any device.
- **`clip`, never `hidden`, for a single axis.** `overflow-x:hidden`
  forces `overflow-y` to `auto` and quietly turns the element into a
  scroll container; `clip` does not.
- **How it was found is the reusable part**: sample the mean brightness
  of each row across the middle of a screenshot and flag any step over
  ~1.5 levels. A clipped glow is a uniform step at a box edge; a ring or
  a line of text is a +/- pair. The same scan on columns finds the side
  edges. Welcome was checked the same way and was never clipped — it is
  not built as a `.panel`.
- **`tools/check-edges.py` is that scan, as a gate**, over Home and
  Welcome on every device in `DEVICES`. It took three drafts to be worth
  anything, and each failure is a rule: the first flagged every card
  border in the app (only the planet screens carry a glow); the second
  passed the live build because the old build saw a newer
  `version.json` and was showing "Pushing update…" instead of Home, so
  it now pins `version.json` to the build under test and FAILS any
  screen that did not render a planet; the third flagged the planet's
  own halo, so it scans only the band ABOVE the hero, which is where
  the background meets the status bar. Calibrated on the real edge — one
  row in which a contiguous half of the width steps the same way,
  peaking at ~7 levels. **Proved both ways**: `--against` build 199 it
  fails on the zoomed phone (y=73) and a 440 Pro Max (y=62); on 200 it
  passes all 44 combinations.

### Settings, the person card, Message, and the Overall board (build 201)

- **The side edges were already gone in 200; 201 makes the gate look
  for them.** `check-edges.py` gains `side_edges()`, the same scan
  turned through ninety degrees: a column near either side in which a
  contiguous stretch of the upper screen steps the same way and is not
  undone within `PAIR` px. It needs the same minimum PEAK as the top
  check, because a wide smooth gradient on a laptop bands by ONE level
  for hundreds of pixels; the real cutoff peaked at 7. `--against`
  build 199 it finds x=20 and x=498 on the zoomed phone — the box.
- **Settings' switches are grouped, each with a one-line hint.** The
  hints live in one `HINTS` map inside `regroupSwitches()` in
  `showAppearance()`, keyed by the switch's label, so a relabelled
  switch simply loses its hint rather than getting a wrong one. The
  first header is "Display & motion". The leaderboard switch sits in a
  `.settings-card`; the share/install buttons are
  `.settings-actions` (a real gap between them and the text above).
- **THE PERSON CARD SHOWED ZEROS FOR FIGURES IT HAD NEVER BEEN SENT.**
  `xp` and `tests` were new fields in 196, so every row published before
  that read 0 beside a real level. Two fixes, both needed: a missing
  figure reads "—" (`known(k)`), never 0; and **every launch republishes
  your own row** (`flushLeaderboardRow()` right after the ordinary-launch
  `pullFromCloud()`), so the class heals as people open the app rather
  than only when they next finish a test. "Tests" became **Correct**,
  which every row has always carried. The Virtual Room lobby and results
  pass `correct` through to the card for the same reason.
- **Message opens the chat, now.** `openDirectChatWith()` used to send
  an invite and wait; it now creates the `kind:"chat"` vrooms document
  with both people in `participants`, remembers it, enters it, and
  sends the inbox invite in the background. An existing DM is found
  first and simply opened.
- **Overall is three columns: Rank, Level, Badges**, with a header row
  (`buildOverallHead()`), because one line of prose per row made people
  hard to compare. Fixed column widths are what keep every number under
  its header; the NAME is what flexes and truncates. **At 375px the
  first version squeezed the name to 0px and ran the columns 12px past
  the row** — the widths that fit 518 and 834 do not fit a phone. Under
  `29rem` the gaps, place number, avatar and columns all tighten; under
  `24rem` (SE, mini, 360 Android) the avatar goes on this board only,
  since the Rank column already says what its coin would. Measured at
  320–1512: no overflow, header within 1px, rank name never clipped,
  shortest name column 38px (SE 1st gen) and ≥78px everywhere else.
- **A TREND ARROW IS AN ORDER CHANGE, NOT A PLACE CHANGE.** The old
  arrow compared each person's place number with their place number
  last time, so one newcomer joining at the top gave everybody below
  them ▼1 — *"why would everyone be +1 if no one went down under
  them?"* `lbTrendFor()` now compares the ORDER of the people present in
  BOTH snapshots (`class26e.lbtrend.v2`), so the arrows always sum to
  zero: every place gained is a place somebody lost. Joiners and leavers
  move nobody. Every board runs it, including Overall with its own
  `sort`; the week board skips a comparison across a week boundary.
  `check-trend.py` asserts all of this and **fails on build 200** on the
  newcomer case (`--against`), which is the reported bug exactly.

### The Rank tab at her real width, and the chat sheet's drag (build 202)

- **"The Rank tab is offset to the right on the phone" was real, and
  build 197 measured it at the wrong width.** It was checked at 440 and
  came back centred; her phone lays out at 518 (see build 199), where
  the hero is a ROW, and for somebody with no rank yet the emblem slot
  is deliberately empty — but an empty 8rem box still took its space,
  so every line of the card sat in the right-hand two thirds. At 440 the
  same box was a blank block above "No rank yet". An unranked hero now
  has no art slot at all and centres its text and chips at every width.
  **The lesson is the one 199 already paid for: a report that measures
  fine at 440 has to be re-measured at 518 before it is called fine.**
- **The up-next rank card's meter uses the hero's step, not
  `rankPct()`.** `rankPct()` is the SLOWER of the two requirements, so
  with no badges the Iron card sat at zero at level 15 of 21 — "it
  doesn't show any of my progress". The hero already averaged the two
  for exactly that reason; the card now reads `heroStepPct`, so the one
  climb shows one number in both places. It was already in the rank's
  colour with its glow; empty was the whole problem.
- **The chat sheet's swipe-down lag had three causes, all fixed:**
  the touchmove listener was **passive on a `pan-y` panel**, so iOS
  panned the page under the sheet while the sheet followed the finger
  (it now `preventDefault`s once the drag is armed); resizing **wrote
  localStorage on every touchmove**, a synchronous write inside every
  frame (now once, on release); and the panel **re-blurred the screen
  behind it every frame** it moved — a 22px `backdrop-filter` on a
  moving layer. While dragged, and for 320ms of settle after
  (`.is-settling`), it is a near-opaque fill of the same tone and goes
  back to glass once still. Style writes are coalesced to one per frame.
  Driven with real touch events at 518: one storage write per drag,
  `backdrop-filter:none` during the settle and the blur back after it,
  and a downward drag closes the sheet.
- **"Start a lobby lags / the screen expands" did not reproduce.**
  Recorded frame by frame at 518 with the fake Firestore: one stage
  mount, the ordinary 6px enter slide, no size change over 2.5s, and
  three roster updates. Nothing focuses on mount. Left as reported
  rather than guessed at; it needs a screen recording from the device.

### The launch-night batch (builds 203 and 204)

- **THE CHAT BUTTON WENT MISSING FROM HOME ON LAUNCH.** `syncChatDock()`
  hides the dock while any loading screen is up and only ran on a stage
  change, so a Home mounted under the splash came up with no button.
  Present on build 200 too; it just needed the splash to outlast the
  mount. A body-level observer now re-syncs when the splash, LOADING
  TEST or GENERATING PROFILE leaves (`watchLoadingScreensLeave`).
- **"THE CHAT SHOWS A NUMBER INSTEAD OF THE USERNAME" WAS A ROOM CODE.**
  An unnamed chat-list row showed its code, and a joined chat was saved
  with no name until the listener named it. `joinChatRoom()` names it
  from the document it already read, and a row never shows a code.
- **ANDROID "NEXT DOES NOT APPEAR ON SOME QUESTIONS" DID NOT REPRODUCE**,
  and was not assumed fixed on that basis. Audited: all 894 questions,
  Drill and Exam, three Android sizes, installed and in a browser - the
  correct slot is always tappable and Next is always on screen and
  unobstructed, including through the real tap-and-slide path on the 25
  longest questions. What an emulator lacks is the browser's own bottom
  toolbar (Chrome's bottom address bar, in-app browsers), which can cover
  content at `bottom:0`; a short question never scrolls it away.
  `.floatbtn` now sits at `bottom:var(--vv-lift)`, which
  `liftFloatForAndroidBars()` sets from the visual viewport on Android
  only (never iOS, never while pinch-zoomed). Verified with a faked 56px
  toolbar: lifted exactly 56px on Android, unchanged on iPhone. **If it
  is reported again, get the browser and the question.**
- **THE SAVE-CODE REMINDER IS ONCE PER DEVICE.** Three showings, checked
  on every Home, a count on `store` that a cloud pull could rewind, and
  nothing that ever set `savedCodeSaved` - so it could only end by
  running out. One showing, recorded in `class26e.savecode.asked`, and
  tapping "Save it" ends it. `check-save-code` asserts all three and
  fails on 202.
- **WELCOME SCROLLED SIDEWAYS ON EVERY PHONE** by 6-10px - the planet's
  SVG past the right edge, the same overflow Home was clipped for in 200.
  Found by `check-save-code`, not by the sweep. Clipped the same way.
- **A THEME IS THE BACKGROUND, NOT THE BUTTONS.** The seven rank blocks
  no longer set `--accent`/`--accent-ink` (kept as `--rank-accent`), so
  buttons, selected states, progress ticks and focus rings stay default
  under every theme; only the glow triad changes. This supersedes "a
  rank's theme is declared in three places that must agree" for the
  buttons. The planet gradient reads the triad, not `--accent`, so the
  cutscenes are unaffected.
- **THE PLANET STOPPED ROCKING, AND IS 6% SMALLER ON PHONES.**
  `cosmic-drift` rotated the whole drawing 2.5 degrees and back - on a
  full-bleed planet that re-rasterises every ring each frame and reads
  as a shake. Size is a `transform:scale(.94)` on Home's and Welcome's
  hero wrap under 640px, so the signed-off layout box does not move.
- **OVERALL: EACH COLUMN HAS ITS OWN COLOUR ALL THE WAY DOWN** (level
  blue #5CA8FF, badge gold #F2C14E), header included, with wider gaps.
- **READY UP NEEDS UNITS AND A SECOND PERSON**, and anybody ready when
  that stops being true is written back to not-ready.
- **ADVANCED SETTINGS centres its label**; the chevron is pinned right.
- **CHAT:** opening the dock or its tab marks the open chat read at once
  (`CHAT_CTX.markSeen`); dismissed notifications persist
  (`class26e.notifhandled`, with a time, so a newer invite still shows);
  **a message pings each other member's inbox** in its own slot
  (`<pub>~m`, type `msgping`) so the button counts unread in chats that
  are not open - including mid-test, since the inbox listener is always
  on - without a listener per chat; a chat somebody started with you
  joins your list on its first ping. "All chats" is a real button, list
  rows show faces. The expand button that toggled tall/normal was
  REMOVED in build 224 on request ("stick to the drag to expand
  function"); the grip is the only resize.

### Muting a chat (build 205)

- **A muted chat loses its pop-up and nothing else.** Asked for exactly
  that narrowly: "it just mutes the banner of the chat preview, that's
  all." The message still arrives, still counts on the chat button and
  still bolds its row. One check in `announceChatMessage()` via
  `CTX.isMuted`, so DMs and the Virtual Room chat share it. The bell is
  in the open chat's header in the dock and in the Virtual Room chat's
  own title; a muted row in the list is tagged MUTED.
- **Device-local** (`class26e.chatmuted`), like the read marks - whether
  something may interrupt you is about this screen, not the account.

### Short tests stopped paying like whole units (build 206)

- **A HUNDO NEEDS THE WHOLE UNIT IN `summarize()` TOO.** Badge progress
  already did (`recordUnitPerfectIfEligible` -> `isFullUnitRun`), but
  the `hundosEarned` fallback counted ANY 100% run, so five questions
  aced was a hundo on the Hundos board plus `PERFECT_BONUS`, repeatable
  at will. Measured on real runs, 205 -> 206: 5 of Identity Crimes at
  100% paid 150 XP and a hundo, now 50 XP and none; 5 questions across
  three units paid 180 and a hundo, now 50 and none; the whole
  12-question unit is unchanged at 220 and a hundo.
- **The multi-unit bonus counts units taken WHOLE**, not units ticked.
- **XP stays 10 per correct answer**, which is already "by amount of
  questions". The curve was NOT changed: level 80 is 194,250 XP, about
  15,500 correct answers - ~220 questions every day to reach it by early
  December, and an hour a day lands around level 45-60 by then, which
  is the "something to work towards till about early December" asked
  for. Re-measure with `levelProgress()` before touching it.

### The results screen stays, the countdown cannot stall, a test ignores the theme (build 207)

- **FINISHING A RACE KEEPS THE NORMAL RESULTS SCREEN.** `summarize()`
  builds it; `finishVirtualRoomTest()` then called
  `showVirtualRoomFinaleReveal()`, which REPLACED it with a screen of
  its own ("the result screen comes up and then disappears right after,
  then another screen shows up"). When the stage holds the results
  screen (`dataset.screen === "results"`), the finale is now a section
  ON it (`.vroom-finale-inline`, under the score): the wait, your total,
  and "See everyone's results". Only a finale reached another way (put
  back after the leave confirm) still builds its own screen.
  `check-vroom` section 7 asserts it and fails on 206.
- **BOTH START COUNTDOWNS ARE CLOCK-BASED.** LOADING TEST was nine
  chained 300ms timeouts, so any stall pushed every later step back by
  its own length; the Virtual Room's "Starting in 3" ran on
  `requestAnimationFrame`, which iOS stops handing out while the page is
  scrolled or dragged - which typing in chat does. Both are an interval
  reading elapsed time now. Measured with a forced 1.5s main-thread
  stall: 206 took 4.2s to the first question, 207 takes 3.0s either way.
- **A TEST LOOKS THE SAME UNDER EVERY THEME.** The LOADING TEST bar,
  label and wordmark, the Virtual Room score lines, the results XP total
  and the mode icons read `--theme-c1/2/3` - the glow triad a rank theme
  sets - so they changed colour with the theme. They read the default's
  stops (`#FFD37A #F5804D #C23B7A`) now. Found by diffing every
  element's computed colours across three themes on a live question and
  a results screen: zero differences remain on either.

### The last loose ends before the shop (build 208)

- **"START A LOBBY LAGS" WAS THE ROUND TRIP, WITH NOTHING ON SCREEN.**
  Recorded again at a realistic 800ms latency (the first recording used
  120ms, which is why it looked instant): nothing at all changed for the
  whole write, then the lobby arrived at once. The button now answers on
  the tap - "Starting a lobby...", disabled so two taps cannot make two
  rooms - and comes back if the create fails (`createVirtualRoomLobby`
  returns its promise, resolving false on failure). **Re-record any
  network-bound "lag" report at a real latency before calling it
  unreproducible.**
- **Join on the open-rooms list comes back after a refused join**
  instead of sitting on "Joining..." for good.
- **`pushLeaderboardRow()` never defers a write to a NEW document.**
  The deferral compared only the row's contents, so a changed public id
  with the same numbers waited up to `ROW_SCORE_PUSH_MS` - the
  `check-friends` seenAt flake under load. It now also requires
  `lastRowKey === publicIdOf()`.
- The "Secret Flares are gone" note was stale; they are a hunt again,
  unlocking Void, and the version-history copy is correct.

### The full-app audit (build 209)

Asked for as "go through every screen, setting, transition, chat, every
single type of sequence ... every theme, character, every possible
scenario". What found things, in order of how much each found:

- **A `no-undef` lint pass found the worst of it, and nothing else in
  the toolchain could have.** `check-js` is syntax only; a call to a
  function that does not exist parses fine and throws when reached.
  Three did:
  - **`renderTugWaiting` and `showTugResult` had been deleted in build
    170** along with the join-by-code screen after them - the cut
    started at the wrong comment. From 170 to 208, finishing your
    questions in Tug of War and the end of EVERY match threw. Restored
    from `e5703c3^`. `check-vroom` section 9 only went as far as the
    rope moving, so it now plays the match to the end on both devices
    and asserts both result screens, and it fails on build 208.
  - **`showDailyAlert` called `onNavigate.disconnect()`**, a name that
    only exists inside `showIntroPopup`, so every "Already done for
    today" banner threw on its way out and stayed on `<body>`.
    `clearBannerOnScreenChange()` returns its observer now.

  How to run it (eslint is not in the repo, deliberately - no npm):
  extract the inline scripts as `check-js` does, concatenate them into
  one file (they share one global scope), `npm i eslint@9 globals` in a
  scratch folder, and lint with `no-undef` and browser globals plus
  `firebase`. Zero errors is the bar; re-run it after any large delete.
- **TUG OF WAR DREW EVERY LEAD BACKWARDS.** Side a is on the left and a
  positive position means side a leads, but `tugKnotPct` returned
  `50 + clamped*40`, so the knot and the whole rope slid towards the
  side that was losing. Nobody could have noticed on a single device.
  It is `50 - clamped*32` now, the rope's shift is a quarter of that
  rather than a third (at a third the knot ended past the visible end
  of the rope at a full lead), and `.tug-rope-wrap` is
  `overflow-x:clip` because the shifted rope ran off a phone's edge.
  `check-vroom` asserts the direction, not just the colour.
- **A listener per render is a leak even when it is harmless-looking.**
  Measured with CDP `DOMDebugger.getEventListeners` across 60 screen
  changes: every info icon added a document `click` handler for good
  (four per visit to Settings) and every Rankings visit added a
  `visibilitychange` handler that repainted a board no longer on screen.
  Both remove themselves once their element has left the page. Window
  listeners, intervals, body children and heap were flat.
- **The Tug of War question clock was a `requestAnimationFrame` loop**,
  the same thing build 207 took out of the countdowns because iOS stops
  it while typing. `setInterval` at 100ms now.
- **The Add to Home Screen guide was `z-index:80`**, under the tab bar
  (200) and the chat dock (300), so both stayed tappable through its
  dim and a tab tapped behind it left the card over the next screen.
  350 now, and mounted with `mountSheetOverlay()` so a screen change
  clears it.
- **Compact controls got 44px hit areas** without moving a pixel: an
  invisible centred `::after` on `.profile-edit-btn`, `.infoicon`,
  `.chatdock-close` and `.releasehistory-version-btn`, which measured
  26-32px.
- **Harness finds that were NOT app bugs, so nobody chases them
  again:** "NaNh NaNm" on Stats was the sweep/positions seed writing
  `studyLog` entries as `{seconds, answered}` objects where the app
  writes milliseconds (fixed in both seeds, and `studyTotals` now
  reads `Number(x) || 0`); the Virtual Room "Pick the units" button
  under the tab bar is only reachable from a lobby, where the bar is
  hidden; `#profilebtn` measuring 20px on screen sits in a row at
  opacity 0.
- **Looked at and deliberately left:** Settings takes ~140ms to first
  paint here against 20-60ms elsewhere - sixteen `backdrop-filter`
  surfaces in software rendering, which a phone's GPU does not pay the
  same way. Home's seven floating flare badges each carry a backdrop
  blur over an animated planet; without it the orbit lines show
  through every badge, so the signed-off look wins until a device
  says otherwise.

### Levels past 45 compound at 9% (build 210)

"A lot of people are already in 30s or 40s with few badges ... at level
45 we need up the xp needed from then on to be exponentially greater
level by level at a higher rate."

- **Read the live board before touching the curve** (`firestore-admin.py`
  plus the `xp`/`level`/`badges` fields; names never leave the terminal).
  Four and a half days after the Sep 22 fresh start the top five were at
  levels 43/39/33/32/32 with 3/3/1/0/0 badges, earning 6,000-11,300 XP a
  day. At that pace the old +1.99% tail had 45 -> 80 done inside a
  fortnight.
- **`LEVEL_STEEP_FROM = 45`, `LEVEL_STEEP_GROWTH = 1.0601`**: every level
  from 46 costs 6.01% more than the one before. The rate was settled by
  showing Madison the list three times: 9% all the way (level 80 at 54,655,
  "not even realistic"), then 9% easing to 4.82% past 60 (80 at 25,000 but
  475,304 in all, "a little high still"), then one rate fitted to "about
  375,000 in total". 46 is 2,838 (was 2,730), 60 is 6,425, 80 is 20,644 and
  the cap is 374,976 XP (was 194,229). Levels 1-45 are byte-identical and
  nobody held more than 43, so no level dropped. `check-curve` asserts
  that, the 6% floor and the ~375,000 total, and fails on 209.
- **This deliberately ends "all sixteen badges land on the cap".** The
  badge line (badge work alone, cheapest first) is now
  `21 28 33 38 42 46 49 52 54 56 57 59 60 61 62 64`: the badge is still the
  gate up to Gold (45), but Amethyst (65, 12 badges) and Supernova (71,
  14) now ask for grinding past what their badges pay. That is the
  complaint being answered. `check-curve`'s badge-line checks were
  rewritten to say so rather than deleted.
- **"Two levels at 60 must not take a week" is re-measured in days**:
  about 3.4 days at 6,000 XP a day. In 250-XP drills it reads as ~78, which
  sounds alarming and is not how anyone in this class plays.
- **`preserveLegacyLevel()` is retired to a flag-setter.** It topped any
  account whose `levelPreserved` flag was still unset up to a pre-reset
  flat +5% curve, which is cheaper than the real one above 26. After the
  fresh start there was nothing left for it to protect, and past 45 it
  would have handed out tens of thousands of XP.

### Badges need fewer hundos (build 210)

Madison's bands, verbatim: 25 questions or fewer 20 hundos, 26-50 15,
51-100 10, 101-200 5, over 200 3. Per unit that is 20 for the six units of
12-22 questions, 15 for the six of 28-46, 10 for Missing and Exploited
Children (54) and the Constitution (77), 5 for Arrest, Search and Seizure
(120) and 3 for Penal Code (340). Every unit is at or below what it was.

- **A badge the new bands hand out is celebrated on the NEXT TEST, not
  silently.** First built silent; reversed within the hour: "some people
  may rank up, I want people to see the rank up animation ... no matter
  the next test they take, the badge unlock sequence would initiate for
  that badge, and the rank thing would initiate if applicable."
  `grantRetroBadgesOnce()` (boot, onboarded accounts, once -
  `badgeBandsVersion`) lists the units held under the 210 bands but not
  209's (`LEGACY_BADGE_BANDS_209`) in `store.retroBadgePending`. The next
  finished trackable run hides them (`retroHideBadges`, honoured by
  `unitBadgeEarned` and `badgeCountOf(store)`) while `summarize()` takes
  its before-snapshots - characters, badges, ranks - so the ordinary diffs
  see them arrive: the end-of-test banner, the Home cutscene, the rank
  cutscene, colour and character banners. No MASTERY_BONUS for them.
  Cleared after that run. A new sign-up is marked current
  (`badgeBandsVersion = 2`) so a badge it earns is never replayed.
  `check-curve` section 7 covers the lot, and fails on the commit before.
- **`check-curve` re-encodes the bands and adds "no unit needs more
  hundos than it did on build 209"**. "The badge is the gate" is retired to
  a printed report: cheaper badges plus dearer levels past 45 mean a rank
  now asks for both, and badge work alone reaches level 16 for Iron's 21,
  43 for Gold's 45, 54 for Amethyst's 65 and 57 for Supernova's 71.

### Saying what a run can and cannot earn (build 211)

- **The start sheet warns before a run that cannot earn a hundo**
  (`.hundo-note`, under Length): a shorter Length, or Most missed /
  Flagged in Drill. The rule is the same `isFullUnitRun()` the results
  screen already applied afterwards; now it is said while it can still be
  changed. Hidden in Game (no length) and Review (nothing is scored).
- **The right-hand end of Length always means every question.** On a
  12-question unit the 5-step track's last stop is 10, so tapping Custom
  (which starts at 10) left the thumb hard right, the label on 10 and the
  warning up - "the warning shouldn't be there if the custom amount of
  questions is set to max". `paint()` now treats any size at or past the
  top stop as the whole pool, which a drag to the end already did.
- **Exam honours Length now, and never did.** The slider was on the sheet
  for Exam and the Begin handler only ever trimmed a Drill, so a
  10-question exam quietly ran the whole unit, and the sheet's own count
  said so too. Only Game ignores Length.
- **Results badge rows say "<Unit> badge", and appear only for a unit
  this run earned a hundo in** ("the badge rows will only be for the badge
  progress for the hits you took from that test"). `summarize()` snapshots
  `store.unitPerfects` beside `badgesBefore` and a unit whose count did
  not move gets no row: a slice, a run with a miss, or a timed-out run
  shows none. `check-curve` section 6 asserts both empty cases.
- **A Game win is one box, in the difficulty's colour, with two lines**
  (`.game-beat-box`): "Easy difficulty cleared (Game) - Identity Crimes!"
  and under it "Average difficulty is now unlocked - 30 seconds a
  question, 2 lives" (or "Every difficulty beaten on ..." after Hardcore).
  Asked for as "average difficulty" wording, both "in that nice green
  box, because it's regarding the same thing". With banners muted, the
  unlock line stays as a plain `.game-unlock-note`.

No committed regression suite exists yet. Worth building.

### The end of a run is two screens (build 212)

Asked for in one long message: *"split the test result screens up ... the
first screen should be about xp, levels, badges, (tokens because that will
be introduced later) it will also show your grade, it will show banners for
any of the stuff you unlocked ... There will be a continue button that says
'continue to review' IF you didn't make a one hundred."* `summarize()` still
scores and records the run exactly as before; everything it used to BUILD is
now `showRunRewards(run, hooks)` and `showRunReview(run, hooks)`, handed one
`runResult` object plus the two things only `summarize()` can make (the
run's own button row, `buildFinalActions`, and the first-results tour).

- **Rewards, in order**: the run header (mode chip in the mode picker's own
  colour, the unit or unit chips, time and question count as pills), the XP
  card (lines drop one at a time, a beat, the total counts up, then the
  level bar fills with a charge glow and a pop), then badge progress / the
  Game difficulty box / a personal best land top to bottom, then the grade
  **last** with a slam, a panel shake and the confetti if it earned one.
  Then each unlock (badge, rank, theme, character, Game difficulty) comes
  through as a centre-screen banner **one at a time** (`playUnlockSpotlight`,
  2.8s or a tap), then an "Unlocked" card lands, then the button.
- **The button**: something missed → "Continue to review", only after
  everything above has landed. Nothing missed → the run's own buttons (New
  run / Main menu, or a lone primary Main menu) on the rewards screen
  itself, since there is nothing to review. Virtual Room → no button; the
  finale (wait, total, See everyone's results, and the review toggle) drops
  into `.rs-endslot`, which stays hidden until the reveal is done.
- **Review**: only the missed questions, each a card with your answer
  (exam / Virtual Room) or the number of tries (drill), the correct answer,
  and the reference, then Retake / Main menu. `dataset.screen` is
  `runreview` and it carries `.screen-runreview`, which
  `forcedUpdateBlocked()` treats like Answer Review.
- **The reveal is a `makeRevealSequence()` timeline, and it can be held.**
  Pause stays up on both screens ("leave the pause screen on all the
  screens"); `pauseRun()` sends it to `pauseResults()` when an `.rs-screen`
  is up, which stashes the screen node, pauses the timeline and any banner,
  and Resume puts back the SAME node. Cards settle from `.rs-in` to
  `.rs-in-now` on `animationend` so re-attaching does not replay them.
- **A tap on the rewards screen skips** to the next banner (or the end).
  Reduce motion (`theme.reduceMotion` or the OS setting) builds every card
  already landed and plays no banners - the global
  `[data-reduce-motion] *{animation:none}` would otherwise leave cards stuck
  at opacity 0.
- **XP is blue everywhere**, the level bar's blue (`#7CC8FF` text), so the
  number and the bar it fills read as one thing; `.results-level-gain`
  took the same colour for the daily question and the Virtual Room.
- **The old top-banner route for colours and characters now runs only for
  the daily question**, which has no results screen; every other run
  announces them in the sequence. Void is still left out of both (it has
  its own cutscene).
- **The forced update waits for the reveal**: `screen === "results"` is
  checked ahead of the Pause test (Pause is up there now), blocks while
  `resultsSeq` is running, and `resultsShownAt` is reset when it finishes.
- **Tokens slot into the XP card** as a second total under the XP one,
  landing in the same beat - there is a comment at the spot.
- `tools/check-results.py` is the gate: order of landing (measured with a
  MutationObserver on the landing classes, not read from the source), no
  review on the rewards screen, the button after everything, banners never
  two at once and the buttons after the last, Pause/Resume giving back the
  same node, reduce motion. It fails 21 of its 26 checks against build 211.

### The results screen, second pass, and a lot more XP (build 213)

One long message of changes on top of build 212's two screens.

**XP is now computed in one place, `computeRunXp(r)`**, from plain numbers,
returning the lines the XP card prints. summarize() awards its total, the
Virtual Room publishes its lines, check-results asks it directly. The lines:
- right answers × 10; hundo bonus (×N). (Every number below was raised
  once before shipping - "I want the new xp to be noticeable amount of
  gains" - and these are the raised ones.)
- **answer streaks inside a test** - tiers 10, 25, 50, 75, 100, 150, 250,
  350, then every 50 (`runStreakTiersUpTo`), worth 25/50/100/150/200/275/
  400/525 and +50 per 50 after (`runStreakTierXp`), each run of right answers
  scoring every tier it reached, printed "10 right in a row ×2" when two runs
  reached it (`×N` always means THAT line counted N times, never the whole);
- **speed** off the average time a question, 150 under 5s down to 10 past two
  minutes in steps of 10 (`SPEED_TIERS`), scaled by accuracy and, under ten
  questions, by length - its sub-line carries the total time and the average;
- **new best time / new best score per whole unit**, 100 each (×N). Kept on
  `store.unitBestMs` / `store.unitBestPct` (defaulted in applyLoadedData).
  The first time a unit is sat sets the mark and pays nothing; a best score
  with no mark is seeded from test history (`unitBestPctOf`). A best time
  needs the unit answered without a miss. Per-unit time comes from
  `qTimeMs`, started in openQuestion and shifted by cancelPauseTiming;
- Game: difficulty beaten (100/200/400) and lives left (25/50/100 each), only
  for a game actually beaten;
- a badge, now **1,000** (`MASTERY_BONUS`);
- **multi-unit ×1.1 per whole unit past the first** (four units ×1.3),
  capped ×2, last,
  over everything above it except a badge. The flat per-unit bonus is gone.
- **A retake earns right answers × 10 and nothing else**, gets no streak
  banners, and opens with no loading screen.

**Curve: ~600,000 to level 80** (`LEVEL_STEEP_GROWTH` 1.0835, was 1.0601;
level 80 alone costs ~44,000). Raised past the ~450,000 first asked for,
because the new XP roughly doubles what a run pays - "if you need to adjust
levels past level 45 to be more ... then do it".
Only levels past 45 moved; the top account was level 43 (52,940 XP), so
nobody's level dropped.

**Streak banners during a test** (`showRunStreakBanner`) only in Drill and
Game, which already show right/wrong - in an Exam, Practice test or Virtual
Room a "10 in a row" would give answers away, so there they are counted at
the end only. At the top, just under the header and below where the chat
banner drops in (moved there on request), gone in
under two seconds, warming in colour as the tier climbs.

**Results screen**: no Pause (the chat button takes the corner back); no
time/question pills (time is in the XP card now); the mode chip is filled in
the mode's own colour and a retake keeps its test's chip; a multi-unit run
lists every unit; every card is tinted (XP blue, grade green/red/gold, badges
silver, unlocks violet, a lost game ember); no HUNDO stamp; per-unit bars on
single-unit tests too; the Game box is quieter. The level-up bar filled twice
because transitionend and the fallback timer both ran `wrapOver` - guarded.

**Unlocks land one at a time**: the card lands, then each unlock is a centre
banner and then its row. The Game difficulty banner is three lights (green,
amber, red) with the new one blinking, and it names the unit.

**Badge case cutscene on the results** (`playBadgeCaseScene`), straight
after the badge box lands: a case unlatches and opens on the whole
collection, the new badge spins in and flies to its slot, every badge
glistens. Not queued for Home any more.

**Secret flares**: the second at a random level 45-47 and the third at 65-67,
drawn once per account (`store.flareLevels`, `mysteryLevelGate`); the first
is still 80 tests. A flare keeps coming back every test until tapped. Bigger,
with a halo. No mid-test banner: a found flare is the last unlock on the
results, followed by a small scene (`playFlareFoundScene`) or, for the third,
the Void cutscene - both hand back to the results.

**Banners from a test belong to its results screen**: the rank cutscene on
Home no longer adds a banner after it, and colour/character top banners are
only fired for the daily question.

**Game over is a results screen**: `gameOver()` cuts the run to the questions
reached and calls summarize(); a "Game over" card replaces the grade, the
question that took the last life counts as missed (`gameLostQi`), and no
hundo, best or Game bonus is paid.

**Re-run is back** on every mode but the Virtual Room, and always re-runs the
whole test (from a retake: "Re-run the full test"). The review shows the
answer you gave in every mode - Drill's is the FIRST pick (`firstPick`) - and
no percentage.

**Daily question**: no level bar, no Pause, a full-width exit. Any run's XP
flies to the Profile tab in blue when you next land on Home (`pendingXpFly`).

**Virtual Room (race)**: scored in XP (badge bonus excluded), tie to the
quicker; each participant publishes `xp` and `xpLines`. The results screen
is the ordinary one with "Waiting on other players 3/4" at the top and the
answer review at the foot (no retake). Ten seconds after everyone is in AND
your own results have landed, `playVroomRaceCutscene` runs: a ship's window
on moving stars, every player's bar counting XP category by category, then
rows slide into order and 1st/2nd/3rd glow gold/silver/bronze, then Return to
lobby / Main menu. Tug of War is untouched.
- **The race line comes down when your results go up**, in
  `showVirtualRoomFinaleReveal`, and its listener stops. The waiting card
  says where everyone is now; left up, the line sat under the chat button
  with every marker piled at the finish. check-vroom section 7 asserts it
  on THIS path - the older assertion only covered the standings screen,
  which the build-213 flow no longer reaches, so it was green while the
  line was on screen for every player.
- **The cutscene's contents sit INSIDE the ship's window**: `.vrc` padding
  clears `.vrc-window`'s 5%/3% inset (in `lvh`, since a vertical
  percentage resolves against the width). With 1rem of padding the rows
  and buttons ran across the window frame on a phone.
- **check-vroom's fake Firestore can LOSE a write when both tabs write at
  once.** The fake room is `localStorage` shared by the two tabs, and
  Chromium syncs that between renderers asynchronously, so two updates in
  the same instant can each read the room and the later one writes back a
  copy without the earlier one in it. Seen as the host's record reverting
  to its join-time values (`finished:false`, `xp` = lifetime points) and
  the "all in" checks going red two runs in three. Real Firestore applies
  field-path updates on the server and cannot do this, so the fixture now
  finishes the two tabs one after the other and waits for each finish to
  land. The same mechanism is behind the occasional "both messages
  survive a simultaneous send" failure under load - that check is
  simultaneous on purpose, so it was left alone; if it goes red, re-run it
  on an idle machine before suspecting the chat code.

### The results screen, third pass (build 214)

- **Every way-on button is on the RESULTS, and lands last** - after every
  box, the badge case, each unlock spotlight and a flare scene: "Continue
  to review (N missed)" across the top when anything was missed, Re-run and
  Main menu under it. The REVIEW carries only "Retake missed questions"
  (Drill) and "Back to results" - no Re-run, no Main menu - so missing some
  again is a cycle (results -> review -> retake -> results). Back to results
  redraws the finished screen at once (`showRunRewards(run, hooks,
  {instant:true})`): nothing lands again and no cutscene replays.
  `buildFinalActions({where:"results"|"review", ...})` builds both.
- **A retake shows no score.** Its card says only what is left ("2
  questions still to go over" / "every question you missed, answered
  right"), its XP is right answers only, and it throws no confetti.
- **Header:** "1 unit" with the unit listed under it, like "2 units";
  the list's dots are white.
- **"Streak bonus · 10"**, with "10 right in a row" under it.
- **Badge progress is one box per unit.** Every box still filling shares a
  steel tint; the box of a badge just earned takes that badge's own colour
  (`--bt` from `badgeThemeFor(u).p`), bar included.
- **The hundo box is on the XP card's recipe** (wash .12, border .2) and
  its 100% is a lighter gold with a soft glow, like the XP total. Unit bars
  are each unit's own verdict: gold at 100, green at a pass, red short of
  `PASS_MARK` - a failed single-unit test has a red bar now.
- **No Game box.** The difficulty unlock in Unlocked names the unit(s)
  that unlocked it, and beating Hardcore is its own row. A MULTI-unit game
  won covers every unit it ran in full (`recordGameBeatIfEligible` returns
  the speed and fills `lastGameBeatUnits`); a lost game never counts, even
  for a unit it happened to finish. Game over reads "Beat X on Easy to
  unlock Average" (on Hardcore, "to beat the game").
- **Rank up is the biggest banner**: the rank you held charges, burns down
  to light, flash and shockwaves, and the new emblem forms out of it with
  rays behind; the words land after (`.rs-morph`, `item.from`). The rank
  icon in the Unlocked row is scaled up to match the others - the emblem is
  drawn with room for its glow and read half-size.
- **Personal-best marks are seeded BEFORE the run is recorded.** Seeded
  lazily from the history, the history already held this run, so a first
  100% after the feature was compared with itself and never counted.
- **The Virtual Room score leaves out personal bests** (and badges):
  `lastRunRoomXp` is `computeRunXp` again with no PRs, so the multi-unit
  line is taken over the right base. The cutscene has no "Personal bests"
  step; its "Everything else" step is excluded from its own count (asking
  it for a match threw).
- **Virtual Room end:** no Review button - the review is on the screen in
  two tabs, Missed questions (default) and Entire test. Each player
  publishes `revealDone` when their own results have finished landing,
  cutscenes included. "Preparing leaderboard" (a pill pinned to the
  bottom, visible from anywhere) goes up `VROOM_PREP_AFTER_MS` after
  everyone is in; the cutscene rolls at the later of
  `VROOM_ROLL_AFTER_MS` after everyone is in and
  `VROOM_READ_AFTER_REVEAL_MS` after the last reveal, so somebody still
  watching a badge case holds everyone. A player who never reports is
  waited for `VROOM_REVEAL_WAIT_MS` at most. All times are this device's
  own observations - no two clocks are compared. check-vroom holds it by
  having the guest tab withhold its report.
- Customize: "Earned by doing" is now **"Challenge rewards"**.

### Build 215

- **A badge's moment is its case, at the unlock.** The earned badge has no
  progress box (units still filling keep theirs) and no spotlight; its
  unlock plays `playBadgeCaseScene` for every badge the run earned, then
  the rows land. The case pops up from a speck (`bc-pop`, paced per
  keyframe - one steep curve had it at 70% size inside 50ms, which read
  as appearing).
- **Lag free, measured.** Frame times under a rAF loop during the scene,
  on the results screen: the case alone was clean, and every dropped frame
  was the grade's CONFETTI still falling underneath it. So
  `clearCelebrationsForScene()` runs when a cutscene or spotlight starts,
  and once the dim is opaque `body.bc-covering` hides `#stage` behind it.
  No filter is animated anywhere in the case - glows are gradients that
  change opacity. Measured after: no frame over 34ms in three runs.
- **The third flare is its own bigger scene** (`playFinalFlareScene`): the
  last flare streaks in, all three whirl round the planet, fall in, the
  planet implodes, flash and shockwaves, and Void comes up out of the dark
  in a three-colour ring. It does not announce a character; the next
  unlock item is Void's banner and row. `pendingVoidCutscene` is never set
  now - nothing plays on Home.
- **The Constitution unit** (from the updated 9-15-26 study document):
  Q11 and Q37 carry `fixedOrder` (their choices refer to each other, so
  `optionOrder` never shuffles them); Q61 carries `bankNoteAnswer: 1` -
  the bank's key (0) is still what the test counts, and `buildBankNote()`
  puts a red note wherever the answer is shown: Drill/Game/daily once
  answered, every review (so an Exam shows it at the end), the Answer
  Review list, and Tug of War (held 3.5s so it can be read). The links
  in eleven `ref` fields are gone. **`ref` is not part of `KEYS`** (only
  `q` and `choices` are), which is what made removing them safe for
  everyone's history; a link inside `q` would need stripping at display.
- Harness: check-unlocks' locked-art pixel check scrolls the tile into
  view instantly before its element screenshot - with smooth scrolling on
  it captured mid-glide, shifted by a third of a tile, and failed half
  the runs of an unchanged build.

Also: Pause wears the chat button's glass; Stats drops "Current answer
streak" and calls the other "All-time best answer streak"; Customize groups
characters as Starters / Rank rewards / Earned by doing.

### Build 216 - found by recording every cutscene

Madison asked for every results screen and every cutscene from every
mode, as video, on both reference devices. Recording them all turned up
four real faults that every gate had passed:

- **The race line dropped everybody after an unknown avatar.** It built
  markers with `buildAvatarCharSVG()`, which returns null for an id this
  build does not know, and `appendChild(null)` threw inside the loop - so
  one classmate on an older build's character took everyone after them
  off the line. Same bug class as the leaderboard rows (see the comment
  on `buildAvatarCharSVGSafe`); the race line was the one builder left.
  check-vroom section 12.
- **"Everyone's ready!" drew the lobby's tab bar over itself.**
  `showVroomReadyFlourish` now sets `forceHideBottomTabs` before it
  replaces the stage. check-vroom section 12.
- **"AVERAGE" and "HARDCORE" ran together** under the difficulty lights on
  the Hardcore unlock (10px overlap). The labels hang centred under each
  light, so the gap between lights is all the room they get: 2rem, not
  .9. check-results section 7 measures the gap.
- **A streak pill from the last question rode over "Test results"** for
  the rest of its 1.9s. `showRunRewards` clears `.streak-pop`. The check
  reads it synchronously, because a check that waited for the results to
  land would pass on the broken build too.

**How the recording was done, so it can be done again:** one fresh page
per scenario, state set through the app's own functions, a CDP
screencast for the video, and stills pulled from the video at moments a
MutationObserver stamped (a watched overlay appearing), not at guessed
times. Two recorders at once is the limit on this box: four dropped the
screencast to ~14fps, which reads as the app lagging. Virtual Room
scenarios use scripted opponents writing to the fake Firestore, which is
how a room of eight was recorded with one browser.

### Builds 217-218 - the long list, first two batches

One message from Madison carried roughly sixty items. They are being
done in batches, a build each; these two cover the results screen and
the small fixes across Home, Settings and the boards.

**The rank-up is a cutscene on the results screen now, not a banner and
not a trip to Home.** `playTierCutscene(tier, { from, onDone })` and
`playSupernovaCutscene({ from, onDone })` take an inline mode: they add
a "You ranked up" kicker and a "Silver -> Gold" line (so it reads as YOU
ranking up), clear their own pending flag, and at the end hand to
`rankHomePreview()`, which SETS the new theme (`theme.accent = tier`),
draws the main menu without its buttons in that theme with the new
flare lighting, and fades back to the results. Drawn inside the
cutscene's own overlay over a copy of the app background - the results
panel is never unmounted, because the reveal sequence checks
`panel.isConnected` and would stop half way through the unlocks. With
no `opts` both functions behave exactly as before (Home still plays a
pending one after a muted or reduce-motion run).

- **The rank beside your name on the results changes when the scene
  hands back, not before**: the level block carries your avatar and rank
  (`buildResultsLevelBlock(..., { me, rankBefore })`, `setRank()`).
- **The unlock order is the story**: rank, what the rank handed over
  (theme, character), badges, the game-mode unlock, the flare. A flare's
  scene plays BEFORE its banner.
- **Pacing**: 1.7s before the Unlocked card, ~1.1s between scenes, and
  each banner dims first, arrives out of a point of light, then its
  words - about a second and a half before it is readable, and it holds
  4.4-6.2s. Every banner names what it took (`item.need`); a challenge
  character gets the "Challenge complete" strip (`.rs-spot.is-challenge`).
- **The badge case is ~4s longer**: floats up (1.9s), latches go one at a
  time, the lid cracks with light spilling out, then lifts over 1.9s.
  **The glisten lives inside each badge's SVG, clipped to its outline**
  (`.badge-shine-band` in `buildUnitBadgeSVG`) - it was a `::after` on
  the square slot and swept the whole square.
- **The cutscene stage is 52vw, not 70vw**, because it is scaled 1.65x:
  70vw x 1.65 = 115vw cut the right-hand flare off every phone.
- `celebrate()` is a nova (flash, rings, stardust from the element it is
  given), not confetti. Same signature.
- Drill is **red** (`#FF5A60` icon, `#FF6B70` chip) everywhere; gold read
  as the hundo tint. The streak pill is **green**. The badge progress box
  is **brushed silver** and says `+1 hundo · N more to go`.
- **Long test bonus**: +100 XP per whole 50 questions answered, stacking,
  scaled by accuracy, before the multiplier. The daily question pays
  `DAILY_XP` = 200.
- **Zeus is announced on the next results screen**, not on Home
  (`store.pendingCharUnlocks`, defaulted empty). The daily question's
  Detective gets the centre-screen challenge card (`showChallengeUnlock`).

**Home lagged because two SVG filters were animated with SMIL.** Each
frame re-ran a turbulence + displacement chain on the CPU. Measured at
4x CPU throttle: 43fps with a 50ms worst frame; off, 60fps and 17ms.
`COSMIC_SMIL = false`; the life now comes from `.cosmic-plasma` (two
light pools drifting over the sphere, transform-only) and a breathing
`.homeglow-hero`. **Never animate an SVG filter's input again** - move
something composited instead.

**A new screen starts at the top.** With Smooth scrolling on, every
screen mount's `toTop()` was a smooth scroll from wherever the LAST
screen was left, played over the new one ("the new tab starts at the
bottom and then moves to the top"). `toTop()` jumps when the stage was
swapped in the last 400ms, and a stage swap within 400ms of a `toTop()`
lands any scroll still travelling. check-behaviour section 10.

Smaller ones: the daily question ends in a verdict card at the bottom
(Correct / Not this time, the XP, "come back tomorrow ..."); Settings
puts the sync code back in a card and its button pairs side by side;
`.more-body` opens on a softer curve with its contents fading in and its
clip feathered while it moves; Find me is the search field's glass at
its height; the person card has no rank coin and says "Correct answers";
Class 26E's days-left is a neutral pill; the Game difficulty is first on
the sheet rather than in the options dropdown, with a toast that names
the units not yet at that level; Review draws from Flagged and Most
missed too; the per-difficulty "farthest" is no longer shown anywhere;
the mode chip sits under "Test results", flush with it.

Gates: check-results section 8 and check-behaviour section 10, both
failing on 216. check-unlocks 7b now asserts the challenge card names
the challenge.

### Build 219 - Ranks tab, the road map, Emerald, the Profile cover

**Rank and Badges are their own bottom tab now** (`#bottomtab-ranks`,
`showRanksScreen()`, `RANKS_TABS = ["ranks","badges"]`), and Profile is
two tabs (`PROFILE_TABS = ["profile","stats"]`). `showProfile('ranks')`
and `showProfile('badges')` redirect, so every old link still lands.
The rank tab is a **road map**: stops drawn top-down with the summit
first, the road lit up to where you are, your character standing on the
rank you hold, and each stop listing exactly what it hands over (theme,
flare, and a character on the top four).

**Gold is Emerald** (`vanguard`, `#2ED18A`); Silver was lifted to a
cold blue-white so it no longer reads as Iron. The key is unchanged.
Home's orbit marks are the rank emblems themselves.

**Five tabs made the tablet/landscape bar ~100px wider**, which put
the daily-question circle inside it on every sideways phone and on the
iPad. The tab padding is 1.1rem a side from 40rem and .55rem between
40 and 56rem, and the circle sits at `50% - 22rem`. Rule of thumb from
the measurement: **between 40 and 56rem the bar may be no wider than
the viewport minus ~204px**. check-fixes is the gate.

**Characters fill their tiles to the same height** (`AVATAR_ART_SCALE`,
applied in `buildAvatarCharSVG` around the bottom centre, halo left out).
Measured by rasterising: first row with alpha over 200. **Zeus is a
marble bust on a plinth** - one material, the curved truncation, blank
eyes; a person who is pale was never going to read as a statue. **The
selection glow fades**: the pool is always there at opacity 0, and the
drop-shadows run through a registered `--char-glow-k` because
transitioning `filter` from a transparent shadow passes through black.

**The Profile card has a cover** in the theme's three colours with the
rank emblem as a watermark; the character stands over its edge on a
round plate. `data-banner` on `.profile-cover` is where banners go.

Gates: check-behaviour section 6 rewritten for the road map and the two
screens; check-statsbadges' slot-shade window now skips the case frame,
the tile above's text, and a stale scroll (it measured the earned tile
last, so the locked one's numbers described a page that had moved).

### Build 220 - five flares, five characters, banners

**Every flare is a level now** (`FLARE_WINDOWS`): red at 35, orange
40-41, yellow 42-45, then Void's two - **Umbra** (violet, 55-59) and
**Event Horizon** (white, 68-72) - which only exist for somebody who
holds Void. Levels are drawn once per account into `store.flareLevels`;
a stored draw outside its window (the old 45-47 / 65-67) is redrawn.
**Catch-up**: finding a flare while the next is already owed sets
`store.flareNextTestAt` three or four tests on, so somebody far past
the levels gets them over ~ten tests, not five in a row. `VOID_FLARES`
is the first three: Void, the third-flare scene and the first three
orbit dots are built from it; `mysteryAllFound()` means those three.
`flareCompletedVoidThisSession` is what makes a find "the one that made
Void" - `mysteryAllFound()` is true for every find after it too.

**The flare scene is one function for both hunts**:
`playFinalFlareScene(color, done, { voidFlare })` lays out every found
flare round the centre and raises the character the flare hands over.
The reveal was rebuilt because Void read as a sticker in a ring: big,
rising, a blurred corona behind it, shoulders masked into the dark (the
mask is on the SVG, not the box, or it clips the glow flat), and the
flares circling it.

**Five characters**: Fox (10 units on Easy), Viking (10 on Average),
Champion (first place in a Virtual Room five times), Umbra and
Singularity (the Void flares). The Game two read `store.unitGameBeat`,
so past beats count. **Virtual Room matches and wins are recorded at the
reveal** (`recordVroomOutcome`, once per room code, a win needs a
rival) and **seeded once from Firestore** (`seedVroomHistory`: rooms are
never deleted, so every finished room this account raced in is still
there).

**Banners** (`BANNERS`, `buildBannerArt`, all CSS): Hundred Club,
Aurora, Molten Gold (100/250/500 FULL tests), Flawless (100% on the
Practice Exam), Arena (50 room matches), Checkmate (100 hundos), Full
Case (16 badges), Stratosphere (level cap). Worn across the Profile
cover and behind your row in a lobby (`banner` on the participant
document); picked in Customize; announced on the results like a
character. **A full test** is a run where every unit was taken whole
and a game was won; `lifetime.fullTests` was seeded once from questions
answered over the average unit length, capped at runs played, because
nothing before this told a full run from a shortened one.

Gate: check-behaviour section 11.

### Builds 221-222 - the room's countdown and leaderboard, Tug of War, the chat

**The room's countdown was a strobe.** Each second's number arrived
from opacity 0 at 1.5x, for up to fifteen seconds, over a .97 backdrop
the first question ghosted through - after a separate LOADING TEST
screen. Now: one count (a room skips LOADING TEST), an opaque backdrop,
the number settles in place, and a ring drains round it.
`showVroomCountdown(startAt, done)` is the count on its own (Tug uses it).

**The race line is hidden by `setActiveNav()`**, which every ordinary
screen passes through - it is `position:fixed` on `<body>`, so nothing
else ever removed it ("the race shows on the main menu").

**The leaderboard cutscene**: rows drop in, each player's bar is their
character's glow colour, the board re-sorts (a FLIP) after every step,
and the steps run bonuses first and **speed and correct answers last**,
because those two decide it. A row's drop-in class comes off once it has
played - re-appending a row to reshuffle it restarts any animation on it,
and the rows vanished mid-count. The waiting card sits above the XP box;
"Preparing leaderboard" becomes "Leaderboard in 3, 2, 1"; the chat dock
goes above the cutscene.

**Tug of War**: even teams or it waits; the shared countdown; a visible
pause between questions (the match clock allows for it); **winner takes
all** - every right answer in the room into one pot, split by the winning
side, nothing for the losers, your own back on a draw; and a team
leaderboard ten seconds after the result.

**Chat**: the second tab is **Inbox**; tap outside closes the dock;
toasts go above an open dock (they were under it, so "Chat muted" was
never seen); a message in another chat gets a preview that opens THAT
chat; list rows say Direct or Group; the header opens a members list;
an emoji tray (with the one asked for by name) and a + for a **photo**
(shrunk on the phone to <=900px / ~350KB, stored in its own `vrooms`
document because the room document holds every message and has a 1MB
ceiling) or a **poll** (one vote each, rewritten in place like a
reaction). `chatNameFor()` means "Someone" only when nothing anywhere
knows the name - presence drops quiet people after 150s, so looking
names up in the present set alone was what produced it.

**A sheet built on `.invite-overlay` needs `invite-overlay-show`** added
after it is mounted - the overlay starts at opacity 0. Both new sheets
shipped invisible for one pass without it.

Gate: check-behaviour section 12.

### Build 223 - Battle (two teams)

A third Virtual Room game beside Race and Tug of War. It shipped first as
everyone-for-themselves with a bar per person and was corrected the same
day: *"The battle virtual room mode will be teams. Can't be played in odd
numbers ... there would just be a single health bar for each side."* So:
two sides made the way Tug makes them (`tugTeamsFor`, by join order), the
lobby holds an odd room exactly as it does for Tug (the `oddTug` gate now
covers both), and **one health bar per side**, `BATTLE_HP` (100) per
member so a 3v3 lasts about as long as a 1v1.

**Nobody ever writes a health number.** The room carries `battle.log`, an
append-only list (`arrayUnion`) of what happened - a hit, a shield, a
freeze - each with a unique id, and every device derives both bars by
replaying it sorted by `at` then `id` (`battleReplay()`). Two hits in the
same second cannot overwrite each other, the log gives the same fight in
any arrival order (check-behaviour asserts it), and a device that
reconnects draws exactly what everybody else draws. Once a side is at
zero nothing after it counts.

- Every right answer by anybody on a side comes off the other side's bar:
  5, or 7 on your own streak of three. A shield (per side) blocks the
  next hit on your side, a double (per player) doubles your next hit, a
  heal is +15 to your side capped at its maximum.
- **At least fifty questions**: the unit pool is shuffled from the shared
  `startAt` and reshuffled per lap until there are 50 (`BATTLE_MIN_Q`), so
  a twelve-question unit still has enough to fight with. 20s a question,
  a flat 2s pause after each (the Tug pause bar).
- **Powers from question 10**: every third right answer after it hands
  over one at random (freeze, flip, shield, heal, double); one held at a
  time, a button above the question. Freeze and flip go to the other
  side's best player so far (most right answers). A freeze puts ice over
  the answers for 5s with the clock still running; a flip turns
  `.battle-flip` (question and answers) over for 8s - the ice sits
  OUTSIDE it, so "Frozen" stays upright during a flip.
- **Alerts name who did it** ("Bo froze you", "Cy healed their side").
  Hits are not announced - there are dozens and the bars say it. On the
  first snapshot everything already in the log is marked seen silently,
  so rejoining does not replay a match as banners.
- The host ends it: a side at zero, everybody out of questions, or the
  pace's clock runs out - then more health left wins, equal is a draw.
  The winner cutscene is the team one (the whole winning side), then the
  result: both bars, XP (10 a right answer + 150 for everybody on the
  winning side) and a two-column board of damage dealt with a star on
  the top hitter. A team win counts toward the Champion like a first
  place (`recordVroomOutcome` with you first).

**A cutscene ends itself on ANY change to `#stage`, so nothing may draw
under it.** Snapshots are always in flight when a match ends, and the
first version drew the result on the next one and cut the winner
cutscene off after a frame - Tug had the same guard missing. Both now
skip drawing the result while `#vroom-cutscene` exists; the cutscene hands
over itself.

Gate: check-behaviour section 13.

### Build 224 - clearer glass, no chat expand button

**The shop and tokens are deferred.** The message that specified them
opened with "Ignore the shop for now, we will get to that later, didn't
mean to include the shop stuff" - the spec below that line is for later,
not for now. Nothing about tokens is in the app.

**Glass was fogged because it was blurred too hard.** "The glass doesn't
seem very glass like, it still seems a little like fogged glass." Every
shared recipe came down: `blur(16px) saturate(1.5)` (73 uses) is
`blur(9px) saturate(1.9) brightness(1.06)`, the heavier sheets roughly
halved, and the tab bar's plain-blur base - which is what iOS actually
renders, since Safari ignores the `url(#glassRefraction)` layer - went
from 40px to 16px. The common dark card fill (`rgba(28,33,40,.55)`, 34
uses) is thinner and lit from above (a white-to-dark vertical wash over
`rgba(26,31,38,.4)`), and its rim is a real specular line on top plus a
shadowed lower lip. **Chromium's headless compositor does not render
backdrop blur faithfully**, so a screenshot here shows the fill and rim
change and not the blur - judge the blur on a device.

**Every infinite animation was checked for a seam** (first and last
keyframe compared): the ones that differ are periodic - a rotation, a
tile shifted by whole periods - or fade to nothing at both ends. `tools/check-loops.py`
does that check and fails on a new loop with a seam unless it is added
to its `KNOWN` list with a reason.

### Build 225 - Gold and Platinum, banners as scenes, no Fox or Viking

**The ladder is Iron, Bronze, Gold, Platinum, Sapphire, Amethyst,
Supernova** - four metals rising in value, two stones, one star. This
supersedes every earlier list in this file (the ones naming Silver or
Emerald). Emerald was "not the theme of the other ranks"; Silver "matched
iron". Keys are unchanged: `veteran` displays Gold and keeps the
crescent-and-star emblem that was liked, recoloured gold (`#E9B43A`);
`vanguard` displays Platinum, teal (`#2EC4B6`) as most ranked games have
it so it can never read as Iron, with a new emblem - a binary star, two
lit stars on a broken tilted orbit (never a closed ring: that reads as a
wheel). All three places a rank colour lives (`RANK_COLOR`,
`ACCENT_SWATCH`, the `[data-accent]` triad) were changed together.

**The road map names what a rank hands over.** "Flare on Home" said
where and not what; the chip is now "<Rank> flare" with that emblem in
it.

**The Fox and the Viking are gone; those two challenges give banners.**
"Pretty lame for challenge rewards, make it banner." Neither was ever on
`main`, so no stored avatar points at them. `easy10` (Lanterns) and
`average10` (Great Wave) count `store.unitGameBeat` like everything else,
so past Game wins count.

**Banners are illustrated SVG scenes** (`BANNER_ART`, one function per
id, drawn in 480x180 and sliced to fit): Lanterns, Sakura, Great Wave,
Neon City, Summit, Northern Lights, Starfall, Koi Pond, Earthrise,
Phoenix, easiest to hardest. The CSS-pattern set before them was called
"random wallpapers you found online" - a pattern is what a wallpaper is,
so each is now a subject you can name, layered back to front, with one
or two things moving (`.bn-*` classes; transform/opacity only; the global
reduce-motion rule stops them). No SVG filters; glows are radial
gradients. Randomness is seeded (`bnRand`) so a banner is identical on
every device. Every gradient id carries a per-instance prefix
(`bannerSeq`) - a lobby can show eight of the same banner at once.
**Keep the subject inside the middle band (about y 40-140)**: the same
art is shown as a Customize tile, a Profile cover and a thin lobby row,
and the Phoenix's wings ran off the top of all of them at full size.

### Build 226 - Battle bars side by side, a Ranks icon that reads

**Battle's two health bars sit side by side across a "VS"**, yours on the
left in green and theirs on the right in orange, mirrored so it drains
towards the middle like a fighting game - "the health bars are on top of
each other, make them side by side". The number on each is the health
alone; the bar already says how full it is, and "188 / 200" does not fit
half a 320px phone. Measured with no sideways scroll at 320px, 518px and
834px.

**The Ranks tab icon is rank chevrons on a shield.** The hexagon with a
star in it was asked about ("not sure what icon it is"); chevrons are what
a rank looks like, and more so for a police academy class. The icons live
in `iconPaths` in `setupBottomTabs()`.

### Build 227 - banners as nameplates (REVERTED in 230)

Build 227 rebuilt the banners as Rocket League style nameplates (the name
written on a thin plate: Police Tape, Siren, Glazed and so on), from a
page of references Madison sent as "some banner ideas I like". **It was
undone before it shipped.** Shown a screenshot of the build 225/226
banners - the scene tiles in Customize and the banner as the Profile
cover - she said: *"I was really liking how these banners working and
stuff for the profile this looks great. Don't change what you did
here."* The 225 note on banners-as-scenes stands; the banner code is
byte-identical to 226 again (reverted by reverse-applying the 226->227
diff, gates included).

The lesson is about reading a reference: "some ideas I like" sent after
approving a design is a mood board, not a request to replace it. Ask
before throwing out something that was signed off.

### Build 228 - the Detective's run is a Home banner, not in the daily box

The daily question's result box ("Correct" / "Not this time") says how
you did today and nothing else. The Detective's progress - N of 10 in a
row, or back to 0 - is set aside in `pendingDailyProgress` and shown on
Home as a top banner with the Detective's face, 1.5s after landing (after
the XP has flown to Profile), once, and only if you are still on Home.
`showDailyAlert(msg, { tag, character })` is the passive progress shape:
the announcement's face-and-tag layout without the tap. Muted banners
skip it.

### Build 229 - last week's top three; shuffles that do not repeat

**Last week's top three sit on the This Week board** as a small podium
(second, first, third; gold, silver, bronze). Nothing used to keep last
week: `awardXp` zeroed the week on rollover and the row re-published this
week's key. Now `rollWeek()` is the one rollover (awardXp and
`buildLeaderboardRow` both call it) and it keeps `prevWeekKey` /
`prevWeekPoints` on `store` (defaulted in `applyLoadedData`), published
as `prevWeek` / `prevWeekPoints`. `lastWeekPointsOfEntry()` reads either
a row that has not rolled yet (`week` is last week's) or one that has
(`prevWeek`). **The snapshot handlers zero `weekPoints` for any row not
from this week, so they now keep the published figure in
`rawWeekPoints` first** - without it everybody who had not played yet
this week vanished from last week's podium. A device also caches the top
three it saw each week (`class26e.weektop.v1`) as a second source for
rows that rolled over on an older build.

**Shuffling.** "I always see them in the same spot." Three causes, three
fixes:
- Answer positions were only shuffled in Exam and Game - Drill kept the
  bank's order unless a switch in the start sheet was on, and it was off
  by default. It is on by default now, and turned on once for everybody
  (`class26e.shuffleon`); the switch still works.
- A fair shuffle still puts the right answer back in the same slot a
  quarter of the time. `optionOrder()` remembers the slot per question
  (`class26e.lastslot`) and redraws a shuffle that repeats it or comes
  out in the bank's order.
- Question order was random, which means the same few could open runs
  again and again. `freshOrder()` puts never-opened-with questions first
  and the ones opened with longest ago next; `beginRun` records each
  run's openers (`class26e.recentq`). It is ordered by AGE, not yes/no -
  on a 12-question unit everything is "recent" within three runs.
  `shuffle()` now draws from `crypto.getRandomValues`.
Virtual Room order is untouched: it is `shuffleSeeded` and must be the
same on every device.

Gate: check-behaviour section 14 (fails on 228).

### Build 230 - Home without the lag; theme colours; the iPhone button

**Home's lag was one animation.** Measured with a trace at 4x CPU
throttle (raster time per 4s): ~5.9s with everything on, ~0.34s with
the hero's animations off, and turning them off one at a time put all
of it on `.homeglow.homeglow-hero` - a halo nearly twice the hero's size
breathing by `scale()`. **A scale animation is re-rasterised at every
new scale; opacity never is.** It breathes by opacity now (.24-.36) and
Home runs 60fps with a 16.8ms p95 frame where it was 55fps / 33ms.
Find the next one the same way: disable animations by selector and read
`RasterTask`, rather than guessing from what looks expensive - the
backdrop blur and the SVG filters looked guilty and were not.

**The hero is four layers now** (`buildCosmicHero`): the two warped glows
in `.cosmic-hero-glowbox` (which does the breathing, by opacity), the
sphere in `.cosmic-hero-main` (the only one in the flow - it sets the
size), the pulse ring and core in `.cosmic-hero-animlayer`, and the orbit
dots in `.cosmic-hero-orbitlayer`, which rotates as a whole svg element.
All share the viewBox `0 -12 360 342`, so a coordinate means the same
in each. Anything animated INSIDE an svg repaints that svg, filters
included - that is why nothing moving sits with the turbulence filters.
The id-suffixing pass runs over the wrap, not one svg, for that reason.
The orbit badges also lost their backdrop blur for a darker fill.

**Loading bars run on the compositor.** The splash and Generating
Profile bars were a width set from requestAnimationFrame, which lurches
exactly when the main thread is busiest. They are `scaleX` CSS
animations now (`loadbar-fill`), set inline with `!important` so the
reduce-motion rule cannot leave a loading bar empty. Verified from
screencast frames through a 2s main-thread block: the old bar froze,
the new one keeps filling.

**Theme colours.** The mode icons on unit selection had hard-coded
colours that Iron's accent overrode; fixed at the `.modedisplay-top`
rules. The triads (`--theme-c1/c2/c3`, which draw the planet, the
background glow and every unit card's progress bar) went through two
passes. The first gave every theme a warm end and a cool end like the
default, and Bronze and Gold came out as the default - "These look too
much like the default ... you should be able to have a theme on and tell
which one it is." Now each theme owns one hue family nobody else uses
(the table is in the comment above the rookie rule): steel for Iron,
copper and verdigris green for Bronze, yellow for Gold, teal for
Platinum, blue with no violet for Sapphire, orchid to pink for
Amethyst, red all the way through for Supernova (its swatch went
#FF6B5E -> #FF3B30 with it). The default keeps the only sunset. Glow
strengths did not change. A new theme needs a family not on that list.

**iPhone Home** (`(max-width:639px) and (min-height:736px) and
(min-width:430px)`): Start Studying bigger (62x216 at her 518px zoomed
view, was 57x200), 12px more gap above it, and 10px higher, text rising
with it. 430px floor because a 393px phone's button nearly shares a
column with the daily-question circle.

**Banners are back to the 226 scene tiles** - see the build 227 note.

### Build 231 - banners on the person card; friends open it; three-tone themes

**The person card shows the banner you wear**, across its top in the same
cut as the Profile cover (`.person-card-cover`, the character on a disc
over it). It needed the banner ON THE WIRE: `buildLeaderboardRow()`
publishes `banner: wornBanner()` now (the room document already did),
and the lobby and results rows pass `p.banner` into `openPersonSheet`.
A change of banner is an urgent push like any other field.

**The Friends list opens the same card** - tap the row, and the Accept /
Decline / Remove buttons keep their own jobs (a click whose target is a
button is not a tap on the person). And the rank coin came off the
friend's character: "on the friend list as well remove the rank icon
next to their character". The rank is the coloured word under the name;
the lobby is the one list that still carries the coin.

**Neither Friends auto-redraw may run under an open card.** The screen
rebuilds itself on every presence and board snapshot, and a rebuild is
a screen change, which `mountSheetOverlay` answers by closing the sheet -
so a friend's card closed itself within a second. Both paths now return
early while `.invite-overlay .person-card` exists; the board path leaves
its signature unrecorded so the next snapshot does the skipped rebuild.

**Themes: one family each, three tones each.** "Ensure the planet system
and background and progress bar ... still has multiple tones like the
default has." Build 230's families were one hue lighter and darker; each
now spans neighbouring hues inside its family (table above the rookie
rule). check-behaviour section 16 holds every theme to a spread of at
least 12 degrees across its three stops - the 230 set fails it on Iron,
Gold and Platinum.

### Build 232 - Madison's list of twenty-two

**The leaderboard is published when the app is put away, not 90 seconds
later.** "Some people would play and the leaderboard wouldn't update for
a long time." A score change waited out `ROW_SCORE_PUSH_MS` (90s) and the
save debounce (2.5s) - both `setTimeout`s, and iOS suspends timers the
moment an installed app goes to the background, while `pagehide` does not
fire on an app switch at all. So somebody who finished a test and closed
the app took their row with them until they next opened it.
`publishNow()` flushes both on `visibilitychange` to hidden and a beat
after every run's end (summarize, Tug, Battle).

**Trend arrows compare against yesterday, from an hourly history.** They
vanished and came back because the baseline was the previous render's
snapshot, which rolled forward every four hours: somebody who had not
moved lost their arrow as soon as the baseline caught up with them.
`class26e.lbtrend.v3` keeps a snapshot an hour for 36 hours and compares
against the newest one at least 20 hours old (the oldest, if there is
none yet); the week board refuses a baseline from another week.
`check-trend.py` has the ageing check and fails against 231.

**Characters.** Poseidon (top 3 on the weekly board three times,
`store.weeklyTop3`, counted in `settleWeeklyWin()` and seeded to at least
`weeklyWins`) sits beside Zeus; the Spartan (10 Virtual Room wins) beside
the Champion. The challenge row is one order - Detective, Zeus, Poseidon,
Champion, Spartan, then Void, Umbra and Singularity together. The Masked
One was retired here and brought back in 233 as a retake challenge - see
Build 233. Rank characters say "Unlocks at X rank." and nothing
about levels; Umbra and Singularity say "Unlock Void/Umbra to see how"
until the one before is held.

**Banners.** Hardcore on ten units is the Thunderhead banner (all three
Game challenges are banners now). Northern Lights and Sakura swapped
requirements by swapping ART between the ids - the ids are the
requirement, so nobody lost one they had earned. Sky Temple for 250
hundos, and a Supernova banner (`titan_rank`, `rank:"titan"`) that the
Rank tab's Supernova stop shows among its rewards. Starfall reads "Earn
all N badges" from the units that exist, and `store.starfallKept` holds it
once earned, so a new unit cannot take it away. The art was drawn by a
sub-agent against the existing BANNER_ART helpers; `bn-pour` is in
check-loops' KNOWN list (streaks 14px apart sliding exactly 14px).

**The Rank tab is turned over**: Iron at the top, Supernova at the bottom,
the way you scroll. The road between two stops belongs to the stop BELOW
(the rank you are heading for) and fills downward. **Every emblem in a
circle is fitted**: `fitRankEmblem()` re-cuts the viewBox round the
emblem's own drawn bounds (`RANK_EMBLEM_FIT`, measured from renders, not
guessed) and the svg clips to a circle - Gold and Sapphire sat 7-9 units
right of centre and Supernova filled its whole frame at 118%. Used on the
road map, its reward chips, the hero, and Home's orbit bubbles.

**The rank hero is two gauges**, a ring for level and a ring for badges,
each filling towards the next rank from the one you hold, on a dark plate
lit in the current and next ranks' colours. No bar and no chips: it read
as the Profile card twice.

**Home's orbit bubbles for ranks not reached are Liquid Glass again** -
the pale translucent body, top light and bright rim, with a 6px blur.
The lit ones are unchanged.

**The badge case is black velvet**, not blue: every blue and violet badge
sank into the blue.

**Unit selection**: an earned badge glows in its own colour
(`--badge-glow` from `badgeThemeFor`), the mode reads as the results
screen's `.rs-mode` chip, and the Practice Test screen is a briefing -
three numbers, four rules, your record.

**Pause stays put while a question scrolls.** `.top` is sticky and stuck
at .6rem - under the clock on a notched phone, 63px above where it sat at
rest, while the chat button beside it is fixed. It now sticks at exactly
`.wrap`'s top padding at each phone width, so it never moves.

**"Sync code" is blue** (`#6FC2FF`), fixed - it was `var(--accent)`,
which is white on the default theme.

**Four themes got a real second colour on the planet** - Bronze, Gold,
Sapphire, Supernova, circled as looking solid. The planet body is mostly
c3, so c3 moved round the wheel (verdigris, vermilion, violet, and a
yellow-hot c1 on Supernova), chosen from side-by-side renders; c2, the
rank's colour, is untouched. Section 17 holds c1-to-c3 to 35 degrees on
the four.

**The default banner "Theme" is your theme's own colours** - asked and
confirmed.

check-behaviour section 17 is this build's gate; every check in it fails
on 231.

### Build 233 - the Masked One is back; shoulders fade out

**The Masked One is a retake challenge** (`retake100`: 100 questions
answered through "Retake missed questions", counted in the retake branch
of `summarize()` into `store.retakenQuestions`). Asked for so people
"want to retake the misses" rather than quitting. Build 232's
`retired` flag is no longer on any character; the code that honours it
stays, harmless, for the next one. **Nothing recorded retakes before this
build, so the count starts at zero for everyone** - the one new unlock
that cannot be counted from history. The old rule (Hardcore on ten
units) still unlocks it, so nobody who earned it then loses it.

**Where each new unlock's history comes from**, for the next time this is
asked ("ensure people's progress is still shown"): Spartan counts
`vrWins`, seeded from every finished room in Firestore; Thunderhead counts
`unitGameBeat`; Sky Temple hundos; Starfall badges; Northern Lights and
Sakura `lifetime.fullTests`, seeded once from questions answered; the
Supernova banner reads the rank. Poseidon's `weeklyTop3` is seeded from
`weeklyWins` only - a podium finish that was not a win was never
recorded, so those count from now.

**Free-standing characters fade out at the shoulders.** "Where the bottom
stops could be smoother." A mask on `.avatarchar-option .avatarchar-svg`
and on the unlock card's character fades the bottom fifth to nothing;
round avatars keep their circle, which already made the cut read as
intended. The unlock card also gets a soft pool of the character's colour
where the cut was.

**Reading everyone's progress documents for a report was refused by the
session's permission check** (personal data), even with the admin key
set. It needs Madison's explicit go-ahead before it is attempted again.

### Build 234 - the road map as it was; the start sheet made simple

**The road map is build 231's, flipped.** "The old road map looked so
good, all you needed to do was flip it." Build 232 had also shrunk every
emblem into its ring and clipped it; they are their old size and glow
again (`.rankmap-node > svg` at 118%, overflow visible), and only the
centring stays (`fitRankEmblem(svg, key, true)` recentres the viewBox on
the drawing without rescaling). Home's bubbles and the reward chips keep
the fitted, clipped cut.

**Nothing on the map is in colour until it is yours.** A stop that is not
reached (the Up next one included) shows its theme dot as a faint grey
disc, its flare and character in grey, and the Supernova banner in black
and white - Customize's locked treatment. Supernova's banner is a wide
preview across its card (`.rankmap-bannerprev`), not a chip.

**The first look after a rank-up is shown, not just drawn.**
`store.rankMapSeen` is the last rank the map has shown as reached. Ranks
held past it are drawn still-locked; when the tab is SHOWN (runFill) the
map scrolls to each, the road runs into it, the node pops with a ring,
a "Rank reached" ribbon flies, and the rewards take their colour. It is
marked seen before it starts. `null` (never opened on this build) is
set quietly to the rank held, so nobody is walked through ranks they
already had; a reset sets -1.

**The start sheet** (Drill, Exam, Game, Review share it):
- Questions (was "Draw from: All questions"): the pool, with a line
  saying what it is and how big.
- How many (was Length: Everything / Custom): one slider, always
  showing, an All pill on its right; the far right IS all. The hundo
  warning is a quiet red line under it.
- Shuffle answers / Hide answers: two tiles side by side, on the sheet.
- Timer: the one disclosure left, labelled with what is set. Inside,
  two switches (Time limit + minutes, Stopwatch) instead of Off /
  Stopwatch / Countdown. cfg.timer keeps its three values.
- Every slider in the app has a filled track (`--fill`, kept by
  `paintSliderFill()`) and a white knob.

**Start is not white until a unit is picked.** The float button went grey
(`.is-inert`) but the tab-bar copy of it only mirrored `disabled`, which
is never set (a disabled button swallows the tap that explains itself).
`syncStartInert()` mirrors the state from both unit screens, live.

**Themes:** Bronze's rim is deep petrol (was green, "looks like
diarrhea"), Amethyst's is deep plum under a gold core (was pink). The
Practice Test screen no longer mentions the Phoenix banner.

**check-behaviour now serves the page's own build as version.json.**
Under --against the older page saw the repo's newer build, and with
"force" set it reloaded itself mid-check. Section 18 is this build's gate
and fails on 233.

### Build 235 - unlocks on Home; Rank reward; the Pharaoh; characters alive

**Unlocks earned away from a results screen play on Home**, a beat
(`HOME_UNLOCK_DELAY_MS`, 2.2s) after it settles: Zeus when the week rolls
over, the Champion/Spartan after a Virtual Room, anything a rank hands
over on the daily question, and anything new a rank you already hold now
hands over. It is a DIFF, not a queue: `store.unlocksShown` records what
has been SHOWN (characters and banners), `pendingHomeUnlocks()` is what is
held and not in it. `playUnlockSpotlight()` marks each item as it
appears, wherever it appears, so the results screen and Home can never
announce one thing twice. Tapping a Home unlock flies the art itself
(moved to `<body>`, not cloned, so its gradient ids keep resolving) into
the Profile tab, which rings with `avatar-pulse`.
- `unlocksShown` is `null` until `ensureUnlocksShown()` seeds it from
  what is already held, so an existing account is not paraded through
  weeks-old unlocks. `UNLOCKS_NEW_IN_235` (Pharaoh, Marksman, the two
  new rank banners) and anything in `pendingCharUnlocks` are left out of
  the seed on purpose: that is how everyone already on Gold is handed
  the Pharaoh on their next launch. A reset sets it to empty lists.
- The flare characters (Void, Umbra, Singularity) are never in it; each
  has its own scene.
- It waits for anything that owns the screen (`homeUnlockBlocked()`),
  including queued badge cutscenes, which go first. Muted banners mark
  them shown without playing, like the badge queue.
- `body > .rs-spot-art.rs-fly` needs the `body >`: the later
  `.rs-spot-art.is-character{position:relative}` otherwise wins and drops
  the flying art into the page flow, 1,100px below the screen.

**Rank reward** is the challenge strip's sibling: a character, theme or
banner a RANK hands over carries `rankReward` (the tier key), and the
card gets a chevron strip in the rank's colour, in from the right, with
the rank's emblem and name. `characterUnlockItem()` / `bannerUnlockItem()`
are the one builder per kind, shared by the results screen and Home.

**Banner pop-ups unroll** (`.is-bannerup`): a bright line opens to full
height and a sheen crosses it. The hard ones (`BANNER_EPIC`) land with a
jolt and a flash of their own light.

**Gold hands over the Pharaoh**, so five ranks now give a character
(`[2,2,3,3,3,3,3]` rewards on the road map). **The Marksman** is the new
challenge: 100 in a row without a miss (`streak100`), counted off
`lifetime.longestStreak`, which is retroactive.

**Banners are ordered by ladder** - the three Game ones, the three test
counts, the two hundo counts, then the singles, then the three rank
banners (Sapphire, Amethyst, Supernova). Customize reads that order.

**Characters come alive through CSS on an ANCESTOR class, never by
default** (`setCharState()`): `char-live` (idle - Profile card, the
person card, unlock pop-ups), `char-sleep` (a friend who is offline: on
their card, the friends list and both invite sheets, with a `.char-zzz`
the app adds), `char-react-perfect/great/pass/fail` (your character in
the corner of the results grade card, added when the card LANDS - a
MutationObserver on `rs-in` - because a reaction played while the card is
still invisible is one nobody saw) and `char-react-win` (the Virtual Room
winner, as their block rises). Only friends can be asleep: presence is a
friend's thing, so anyone opened from the Leaderboard is simply live.
Leaderboard rows stay static. The Zzz letters use negative delays so a
list that re-renders every few seconds still shows letters in flight.

**Profile card:** "level" stacks under its number, like "badges".
**Bronze** is wine (`#6B2140` under the bronze).

Section 19 of check-behaviour is this build's gate and fails on 234.

**The road map (same build, second list).** Every stop now has the same
pitch: the stops sit in `.rankmap-stops`, a grid with
`grid-auto-rows:1fr`, so each row is as tall as the tallest card and
every stretch of road is the same length. Reached cards are short and
the top three carry a banner, which is what made the passed part of the
road look bunched. From 24rem up (every phone but an SE 1st gen) the
road runs up the middle with the cards alternating either side, as the
iPad already did, and the gap between stops is longer (`--gap` 2.4rem on
a phone, 3.6rem from 46rem) for more of a climb as you scroll.

**The start sheet's Question bank.** The three chips (All / Most missed
/ Flagged) are three rows now: an icon, what each draws, and how many
that is in the units picked. An empty one says why and how to fill it,
and tapping it explains instead of selecting. Most missed carries an
info dot. `srcSect` keeps its name and `.drawfrom-sect` its class, and
`cfg.source` keeps its values. A bank that empties when a unit is
unticked falls back to every question.
- The top box carries **tags** for every choice that shapes the run:
  the bank, the length, the Game difficulty, the timer, shuffle and
  hidden answers. Nobody has to open the timer to see what it is set to.
- The timer disclosure is labelled "Time limit & stopwatch".
- The Shuffle and Hide answers descriptions say what they do.
- `sliderWithEverything`: a pool with no second stop on the 5-step
  lattice (7 most missed) used to show the knob at the far left beside
  "All 7". It sits full and disabled now.

**Most missed is capped per unit:** at most 15% of a unit's questions
(`mostMissedCapFor()`, rounded, never under one), most misses first,
with the latest miss breaking a tie. The flat cap of 50 is gone.
`unitQuestionCount()` already existed further down the file. A second
definition was added and then removed: a function declared twice
silently takes the later one.

**Hold a unit card for its details** (`attachUnitHold` /
`openUnitDetail`), on the test setup grid and the Virtual Room unit list.
- **The hold:** 420ms with under 8px of movement (more than that is a
  scroll); a right-click also opens it. The click that ends a hold is
  swallowed, so the card is not ticked.
- **The card:** it grows from its own place (left, top, width and height
  transitioned, so text reflows rather than stretches) into a centred
  card with the same head as the grid card (`appendUnitProgress`).
- **The stats:**
  - Completed (any mode, `store.unitRuns`) and Hundos in every mode.
  - Drill adds best time (`testStats[unit].bestMs`, a 100% whole-unit
    drill) and best score.
  - Exam adds best score and the fastest 100% in any mode.
  - Game adds the hardest difficulty beaten and best score.
- **Flagged and Most missed:** two buttons that open a review-style list
  inside the card, with Back. Each question can be flagged or unflagged
  there. An unflagged one stays in the list, dimmed, until Back.
- **Closing:** tap anywhere off the card and it shrinks back to its place.
- **`store.unitRuns`:** null until `unitRunsMap()` seeds it from
  `testStats` (a unit's own plays plus every combined test it was in).
  It then counts in `recordTestPlay()`. A reset sets `{}`.
- The "Best: 4:12" line is gone from the unit cards.

**Merged art.** The two rank banners and the hard-banner events came from
one agent, and the Pharaoh, Marksman, the Officer redraw and every
character's `cx-*` parts and states from another. Both were cut against
build 234 and applied with `patch`, cleanly. The character states'
loops that end somewhere other than where they start are all invisible
at both ends or a whole turn, and are listed in check-loops' KNOWN
list. Robot and Astronaut still scan and twinkle with no class: that was
already so, and it is left alone.

Section 20 of check-behaviour covers this list and fails on 234.

### Build 236 - road map chips and light; unit list tools; Virtual Room podiums

**The road map.**
- **The rank banners are reward chips again**, the same size as the
  theme, flare and character chips: a small strip of the banner stands
  where the others have a dot or icon (`.rankmap-giftbanner`). Build
  234's wide preview was read as far bigger than asked for.
- **The road blends** from the rank above to the rank below
  (`--from-color` to `--rank-color`).
- **The stretch you are on** carries a light at the end of the fill
  (`.rankmap-roadtip`, `top` driven by `--tip`), so it visibly creeps
  towards the next rank. Its ping fades to nothing at both ends and is
  listed in check-loops.

**Art.**
- The Officer's aviators are black glass with a black frame.
- Zeus's bolt and Poseidon's trident sit on a dark carved panel in the
  socle, a unit higher than before. At their old height the tile
  clipped them, and light stone behind a light symbol hid it.

**The unit details list.**
- The doors read "Tap to see flagged questions" / "Tap to see most
  missed", and Hundos no longer mentions the badge.
- In the list the card drops the badge bar (`.is-listing`).
- The sticky header runs edge to edge and fades out, instead of the old
  inset block with hard sides.
- A search with a Clear button filters the list.
- Each question carries the in-test flag, made louder, with its word.
- Unflag every question in the unit / Clear most missed for the unit,
  each behind an inline warning. Clearing most missed empties `r` (the
  30-day miss stamps) for the unit's questions and leaves `n`/`m`,
  hundos and history alone.
- Most missed is recomputed on every render, so a question leaving the
  list is replaced by the next-worst.

**The Virtual Room podium needs four people** (`VROOM_PODIUM_MIN`,
`vroomPlaces(n)`). With fewer:
- The results rank only the winner and give everyone else a dot.
- The race cutscene labels "Winner" instead of 1st / 2nd / 3rd.
- The podium cutscene draws one block.

**Top-three finishes** (`store.vrTop3`) count only in a room of four or
more. They are remembered per room in `vrTop3Rooms`, so a rebuilt
results screen cannot count one twice. `seedVroomTop3()` backfills once
from Firestore (`vrTop3RetroDone`). It is separate from
`seedVroomHistory`, which everyone has already run.

**Profile → Stats** has a Virtual Room section: Matches played,
First-place finishes and Top-3 finishes, each with its explanation.

**The results character** reacts on the XP box's own avatar
(`.results-level-avatar`, live until the grade lands). The one on the
grade card from build 235 is gone: "it's perfect being just on the xp
box".

**Data, outside the app (Madison's request).** Four rankings rows were
named Alfred Lake. The rows for the level-5 account and the two level-1
accounts were deleted from `leaderboard`. The level-20 "- ALFRED LAKE -"
row was left as it was.
- The level-5 account's progress is untouched. Its row comes back the
  next time that device syncs, which is the point: it shows he is
  running two accounts.
- The two level-1 accounts' `progress` documents were deleted later the
  same day, once Madison said so explicitly ("Yes, delete the two level
  1 Alfred lake accounts"); they were found with a masked read (name
  and publicId only). Those two accounts are gone for good.
- The level-5 row DID come back: that device synced at 19:29 UTC on
  28 September. Hidden again as asked ("if he uses it again it'd go
  back to leaderboard so I'd know he's using it"), progress untouched.

Section 21 of check-behaviour is this build's gate and fails on 235.

### Build 237 - the Profile rank plate

"The way the rank shows up in profile ... looks a little lame." The rank
was a pill the size of a tag, smaller than the Customize button beside
it. It is a plate the width of the card now (`.profile-rankplate`, still
the `.profile-ranklineup` button to the Rank tab):
- the emblem at 3.4rem (4rem on a tablet) in a lit ring;
- "RANK" and the rank's name large, in the rank's colour;
- a bar to the next rank, blending this rank's colour into the next's,
  with "Platinum · 47%";
- the emblem huge and faint behind it as a watermark, and one sheen
  across it on arrival.

The percentage comes from `rankStepProgress()`, measured the way the
Rank tab's hero measures it: each of level and badges as a share of the
step between the two ranks, averaged. Unranked shows a dashed plate
aimed at Iron; Supernova says "The top of the ladder" with a full bar.

Section 22 of check-behaviour is this build's gate and fails on 236.

### Build 238 - best time says hundo; a chat message cannot be erased

- **Unit details say how a best time is made.** "Ensure best time in the
  unit details mentions it's the best with a hundo ... so people know
  that's the way to get the best time." Drill's Best time box reads
  "your fastest hundo in Drill", or "get a hundo in Drill to set one"
  before there is one; Exam's box is "Fastest hundo". Nothing about how
  a time is set changed - only a hundo in Drill ever set it.
- **Reactions, poll votes and the host's trim go through a
  transaction.** A send has been an atomic `arrayUnion` for a long time
  and cannot lose anybody's message. These three cannot be an append -
  they change a message in place or drop old ones - so they wrote the
  WHOLE `chatMessages` array back, built from this device's last
  snapshot. Anything sent between that snapshot and the write was
  erased, on the real server too: somebody tapping a reaction while
  somebody else sent wiped the new message off every screen.
  `rewriteChat(transform)` reads the list the server has now inside
  `fbDb.runTransaction`, and Firestore retries it if anything lands in
  between. A transform returns null for "nothing to change". The plain
  update is only a fallback for an SDK without transactions.
  Found because check-vroom's two-senders test came up one message short
  on a heavily loaded machine; that test itself was the fake's own
  cross-tab race, but reading the code behind it found this.
- The fake Firestore in check-vroom has `runTransaction` now (check-
  chatroom lifts it), and **section 5b** puts another person's message
  into the room in the same tick as a reaction tap - deterministic in one
  tab. It fails on 237 (the message is gone) and passes on 238.
- check-friends' "the card is actually visible" POLLS for the fade-in
  (up to 2s) instead of sampling once at 350ms, which read a visible
  card as invisible when the machine was loaded. A sheet that never
  fades in still fails.

Section 23 of check-behaviour is the best-time gate and fails on 237.

### Build 239 - presence that stays on; chat invites and rosters that tell the truth

Found by an agent photographing the chat screens and reading the code
behind what it saw. Each one is a real device behaviour, not a harness
artifact, and section 24 of check-behaviour fails on 238 for every one:
- **Presence was unsubscribed before its first snapshot, every time.**
  `showFriends()` and `showProfile()` call `attachPresence()` BEFORE
  they mount, and `attachPresence()` detached "on the next change to
  `#stage`" - which was the caller's own mount. So the online dots never
  came from the presence document at all, only from each row's
  `seenAt`. Now one observer (`presenceObs`) detaches only when no screen
  in `PRESENCE_SCREENS` (`.screen-friends, .screen-profile`) is left on
  the stage. Friends' repaint (`refreshPresenceViews`) is gated on
  `friendsViewSignature()`, because presence now really does move every
  few seconds and most moves change nothing on screen.
- `onSnapshotResilient` no longer calls `onNext` after its handle has
  been called. The fake Firestore delivered one last snapshot after an
  unsubscribe, which turned the bug above into a rebuild loop in the
  harness; a defensive check costs nothing.
- **Opening a chat stamps you present at once**, not a 45s beat later -
  re-opening one you had left for a while showed you as Away, to
  yourself and everybody else.
- **"Just you so far" only when the one person present IS you.** It said
  it for any single person, including when that person was somebody else.
- Tried and reverted: making an invite disappear only for the room it
  invites you to. Madison's rule is "if I am in a room or chat with them
  their old invite should disappear" - with anyone - and check-chatroom
  holds it. Being in chat A with Bo does therefore hide Bo's invite to
  chat B; that edge case was put to her rather than decided here. The
  invite items do carry `code` now, harmlessly, should she want it.
- **Names are coloured by membership, not by who is awake**
  (`chatColorBasis`). Taken from the present set, somebody whose phone
  slept fell back to a hashed colour that could match somebody present.
- **Nobody already in the chat or the room is offered Invite** - the
  button reads "In chat" / "In room", disabled.

Not changed, noted for later: with four people the chat header wraps
(Invite/Leave onto their own row on a phone, Leave alone on an iPad),
and the iPad panel's default height leaves ~290px of list, so a poll can
need the resize handle.

### Build 240 - Friends and Group chats; a pinned Pause; the reveal

**The chat is two things now, on two tabs, plus the Inbox.** Madison:
"There's a tab for your friends, these are permanent but the chat history
deletes after a day. You can't add people to this section unless you
friend someone ... you can't invite people to them or leave the chat. And
then the other section will be group chats ... the people in the
groupchat can invite people as well."
- **A friend chat is one `vrooms` document per pair of friends**, id
  `friendChatCode(pub)` = `DM-` + the two public ids sorted, upper-cased,
  so both sides find it without an invitation. `kind:"dm"` keeps
  `joinChatRoom()` (which accepts `kind:"chat"` only) from letting anyone
  in by code. `openFriendChat(pub)` creates it or adds your own entry in
  a transaction and never writes the friend's entry (that would reset
  how recently they were here).
- **Friend chat history is 24h** (`FRIEND_CHAT_HISTORY_MS`): CHAT_CTX's
  `staleBefore`, `keepStale` (a getter: 0 for a friend chat, 3 for a
  group) and `shouldTrim` all branch on `isFriendChatCode(chatRoomCode)`.
  In a friend chat anybody opening it trims, because nobody may be
  writing to it to do the author's trim; the transaction makes that
  safe. `trimmedChat` honours a `keepStale` of 0.
- **The Friends tab is every friend, always** (`renderFriendChatList`),
  no start and no delete. A friend chat header has the friend, online or
  away, and the mute bell - no Invite, no Leave.
- **The Groups tab is what the one list used to be** (`groupChatList`,
  `renderGroupChatList`), minus friend chats and minus any old two-person
  room with a current friend (hidden, not deleted). A group header is
  "N members · M here now", mute, Invite, Leave, then EVERY member with
  the away ones dimmed - a member whose phone slept used to vanish.
- `chatDockTab` is `"friends" | "groups" | "notifs"`; `isChatTab()` and
  `chatTabFor(code)` replace every old `=== "chat"`. `enterChatRoom` sets
  the tab from the code; switching to the other chat tab closes the open
  room (closing writes nothing). `openChatDock` rebuilds the list when no
  room is open, because friends change while the dock is shut.
- **Counts are chats, not messages** (`chatUnreadByTab`): each chat tab
  counts its unread chats, the Inbox counts its items, and the button is
  the sum - "the chat button shows correct amount of chats/notifications".
  check-chat's "the dot reads 3" became "1" (three messages, one chat).
- **Pings go to every member**, not only the present ones, and a friend
  chat always pings the friend - otherwise a first message never reached
  somebody who had not opened it.
- **Invites (Madison's new rule):** an invite drops out only when it is
  for the chat or room you are already in (`it.code === chatRoomCode` or
  already in your list; `it.code === vroomCode`). One from somebody you
  are chatting with, for a DIFFERENT chat, stays. This supersedes the
  build-221 wording "if I am in a room or chat with them their old invite
  should disappear", which still holds for the room it was for.
  check-chatroom asserts both halves.
- **Dead invites say so:** a missing chat is "That chat doesn't exist any
  more"; a missing lobby "doesn't exist any more"; a started one "is no
  longer available". `lastJoinGone` lets the Inbox row clear itself.
- **Becoming friends is a moment** (`celebrateNewFriend`): both people,
  a heart, "Say hi" into the friend chat. Fired by `acceptFriendRequest`
  and, on the other side, by a `friendacc` landing in the inbox (only if
  new and under three days old). Once per friend (`class26e.friendmoment`
  in localStorage), and it waits out a question, a tour or the splash.
- **The room's chat on the results and the leaderboard:** a Room chat
  pill (`#roomchat-fab`, measured beside the dock button by
  `placeRoomChatFab`) with the room's unread count (VROOM_CHAT_CTX
  `onUnread`), above the race cutscene (z 445). It LIFTS the one live
  `.vroom-chat` into a sheet and puts it back - a second panel would be a
  second listener and doubled preview banners.

**Pause is position:fixed on a phone too**, 44px tall, `top` at the
safe-area line + .35rem. Sticky worked in Chromium, but a sticky control
in an iOS momentum scroll lags a frame and so does its hit area, and it
was 36px. `.top` keeps a 44px min-height so the question does not jump.

**Show answer choices** is a centred `.recall-reveal` block: one line
("Answer it in your head first, then check the choices") and a
full-width button. The status line is hidden while the choices are, and
the button is no longer focused programmatically (that drew a focus ring
on every question; Enter still reveals).

Section 25 of check-behaviour covers all of it and fails on 239.

### Build 240, second round - Madison's review list before shipping

"It's not a go for midnight. I need to review this stuff first." Nothing
from build 240 is committed until she has. These landed in the same
build number, uncommitted:

- **Unit details are one layout for every mode** (`unitDetailStats`):
  always four squares, Completed / two for the mode / Hundos, with the
  mode named in a chip in the header - "some of the screens aren't in the
  same order ... I can't tell which screenshot it is". Game: "Level
  unlocked" and "Farthest on <level>" (`gameFarthestFor`, X / N), and a
  time ONLY once Hardcore is beaten ("Hardcore best time",
  `store.gameHardcoreMs`, recorded on a Hardcore win in summarize's
  whole-unit loop). Exam: "Best exam" and "Exam average"
  (`store.unitExam`, seeded once from `testHistory` by `unitExamOf`).
  **The seed has to happen BEFORE `recordTestPlay` adds this run to the
  history**, or a first exam is counted twice; summarize seeds each unit
  first for exactly that reason. Review and Virtual Room: Best score and
  Accuracy. check-behaviour 26; section 23's Exam assertion changed with
  the decision.
- **Leave asks first** (`confirmLeaveChat`), for the group header's
  Leave and the list's x alike, in a card INSIDE `#chatdock` so closing
  the dock takes it. **Its z-index has to beat the dock's panel (320)
  and button (370), its siblings** - at 40 it was drawn under the panel
  and a real tap never reached it, while every `.click()` in the gates
  passed. Never `window.confirm()`.
- **One accept answers every invite to that chat.** Being in the chat
  already hid the others, but only while it stayed on your list - leave
  it and three invites came back. The Inbox's Join and the banner's Join
  both mark every invite with that code handled. check-chatroom 8 writes
  the invites into the real mailbox: **a fixture written straight into
  `inboxMsgs` is wiped by the inbox listener's next snapshot**, and the
  first draft passed on 239 for exactly that reason.
- **Photos keep their shape** - "proportionate ... like iMessage". The
  size travels with the message (`w`,`h` from `shrinkChatPhoto`), the
  bubble is drawn at that aspect before the image arrives, capped at
  ~two thirds of the chat's width and 15rem of height, 18px corners, no
  frame. Old photos take their size on load.
- **Typing is one row per person**, stacked, with dots, never "Several
  people are typing". Accuracy: the flag comes down in the same write as
  the message and when the box is emptied; a flag older than that
  person's last message is ignored; and a flag is aged from when THIS
  device saw it change, not by the sender's clock (two phones seconds
  apart made people vanish or linger). The typing box is `flex:0 0 auto`
  or its column squeezes the second row onto the input. check-chatroom 4a.
- **Fifteen emoji**, three rows of five, the middle finger kept (it was
  asked for by name in build 222).
- **The Room chat button was unreachable in a real game.** It was mounted
  by `showVirtualRoomResults()`, which nothing calls any more - a race
  ends in `showVirtualRoomFinaleReveal()` and the cutscene. The finale
  now builds the room's chat panel out of sight (`.roomchat-host`,
  `hidden`) so its listener counts, and mounts the button. The gates
  had only ever mounted that screen by hand, which is why they were
  green; check-vroom 7 now asserts it on a real finish. Found by the
  screenshot pass, not by a gate.
  Also: "seen" needs half the list or 80px on screen, not one pixel (an
  iPad's results put 11px of it in view and marked everything read);
  nothing under the leaderboard cutscene counts as seen; the read mark
  survives the panel being rebuilt (`vroomChatSeen`, VROOM_CHAT_CTX
  `onSeen`/`initialSeen`); opening the sheet calls the panel's own
  `markSeen` (zeroing only the button left the panel's mark behind, so
  the next message brought every read one back); and over the cutscene
  on a phone the pill is an icon, because the label sat on "RACE
  RESULTS".
- **What each friend is doing** - "if someone is in a drill mode test or
  virtual room match or virtual room lobby or at the main menu, you would
  see that on the invite list, and friends list in profile ... easy to
  see but subtle". One code per person in the SAME presence document as
  the online dot (`a` beside `p`), so nothing new is listened to.
  `currentActivity()` reads the app's own state (menu, drill, exam,
  game, review, daily, lobby via `.screen-vroom-lobby`, match, results);
  `shareActivity()` runs on screen changes but WRITES only when the code
  changes, at most once every 8s, only while visible and opted in. Shown
  only for somebody online. Every label is a `.friend-activity` span
  carrying its `data-activity-pub`, so a presence snapshot repaints them
  in place (`paintActivityLabels`) without rebuilding a list under a
  finger. On Profile > Friends, the dock's Friends tab (chip), a friend
  chat's header, and both invite sheets. Presence stays attached while
  the dock or an invite sheet is open. check-behaviour 27.

### Build 241 - Madison's list after reviewing 240

Also uncommitted until she has reviewed it. `check-behaviour` 28 and 29
are the gates; both were run against 239/240 and fail there.

- **The Home flare bubbles are glass again.** A lit rank bubble is the
  rank's colour as a tint behind a `backdrop-filter`, with a lens
  highlight on `::after`; an unreached one is the same glass with the
  emblem greyed (`grayscale + brightness`), not a dark coin.
- **No rank coin on any character, anywhere** - "the ranking with the
  words is enough". `decorateAvatar()` still exists and still takes its
  arguments (every board calls it) but hangs nothing on the avatar.
  check-behaviour 3 and check-vroom 3 assert the ABSENCE.
- **Profile card**: the rank bar is ONE colour, the rank you hold - the
  blend into the next rank lives on the road map only. Badges left the
  level section and are their own row (`.profile-badgesect`, sixteen
  mini tokens from `buildBadgeStrip()`, the same strip heads the Badges
  tab where the silver shine used to be).
- **A banner pop-up in the top-left corner was a CLASS COLLISION.**
  `playUnlockSpotlight` names its card `rs-spot-<kind>`, and a banner's
  kind is `banner` - so the art wrapper's own class `rs-spot-banner`
  also matched the positioning rule for the whole card. The art is
  `rs-spot-bannerart` now. Any new art class inside a spotlight must not
  be `rs-spot-<a kind name>`.
- **Characters never visibly loop.** Every live character breathes and
  sways as PENDULUMS (`alternate`, eased both ends) on lengths that are
  not multiples of each other, offset by each one's blink phase. The
  flare characters layer a second motion through the separate `rotate`
  and `scale` properties so it never restarts the first.
  `check-loops.py` skips `alternate` loops because they cannot jump.
- **A hundo gets the character's own win move** on the results XP box
  (`char-react-perfect` + `char-react-win`); 90+ a hop and a nod, a pass
  a nod, a fail a slump.
- **Secret flare order on the results**: the flare's pop-in first, then
  a 1.8s beat, then the flare scene, then the character card.
- **The rank-up cutscene (`playRankUpScene`) starts from what you HAVE**:
  your current theme's sphere, the new rank's flare unlit; zoom in,
  spin (longer now), flash, and only behind the flash does the scene swap
  to the new rank's colour and light its flare. The flash itself carries
  the new rank's accent. It ends dark - the words fade, the system
  settles with every flare round it - never on a Home screen showing
  through. Found secret flares are drawn in both halves. It starts 3s
  after the results' unlock box lands, from further out (`.is-arrive`).
- **Theme swatches carry their names** (`.swatch-name`, "Default" for
  ink, the rank name for the rest).
- **Only the hardest banners animate** (`BANNER_ANIMATED`); every other
  banner is `is-still`. Level 80 is one of the animated ones.
- **ECLIPSE**, the new challenge character: a new moon in front of a sun
  whose corona is the seven rank colours (read from `RANK_COLOR`, never
  copied), a diamond-ring glint on the rim, calm eyes. Challenge:
  **a hundo in 7 different units in one day** (`hundo7day`), one unit per
  flare. `noteHundoDay()` is called from summarize's WHOLE-UNIT loop at
  100%, so it is the same "whole unit" every hundo needs; it keeps
  today's distinct units (`store.hundoDay`) and the best day
  (`store.hundoDayBest`), both defaulted in `applyLoadedData` and reset.
  Tracked from 241 - nothing before kept the day a unit was aced. The
  corona SWINGS (`cx-live-corona`, ±7deg) rather than spinning: the
  tongues pointing into the chest are drawn short, and a full turn would
  carry the long ones over the collar.
- **TUG OF WAR, rebuilt around the rope**:
  - **Pull, not a count.** A right answer pulls `TUG_PULL_BASE` (.5)
    plus up to `TUG_PULL_SPEED` (1) for the share of the clock left
    after the read-in; a wrong TAP pulls back `TUG_PULL_MISS` (-.25);
    running out of time is 0. Published as `pull` beside `correct`;
    `tugPullOf()` falls back to `correct` for a device on an older build.
    XP still pays on `correct`.
  - **Can't spam**: the choices arrive locked for `TUG_ARM_MS` (1.2s) with
    a bar filling over them, and a wrong tap holds you 3s.
  - **Your side is ALWAYS the left end, green**, whichever team letter
    you have (`tugView()`), so the rope reads the same way on every
    phone. The side scores are gone; the field shows the two teams'
    characters holding the ends, a dashed centre, a win line each side
    where a winning pull puts the flag, and a rope 140% of the field
    that slides as one piece. The side ahead leans back by how far ahead
    (`--lean`). `tugKnotPct` travel is 27% so the lines clear the
    figures. check-vroom 9's direction check now asks for "your end".
  - **The pull cutscene** (`playTugPullCutscene`, ~3.7s, on the shared
    `#vroom-cutscene` layer): strain, haul - the flag goes over the
    winner's line, the losers are dragged forward, the winners do their
    win move - then one line, then the result, then the team board.
    Tap skips, muteBanners hands over at once, reduceMotion shows the
    end state.

### Build 242 - Madison's list after 241

Uncommitted until reviewed, like 240 and 241. `check-behaviour` 30 is the
gate; all fifteen of its checks fail on 241.

- **What friends are doing is one colour.** The per-activity tints came
  off `.friend-activity-line`; the words say what it is.
- **"Add a friend" is the same box as "Your friend code"**: same recess,
  pill, 1.25rem mono, 11rem x 3.125rem. Both prefixes on the input rule,
  or the dark theme's `.searchbox` fill wins.
- **Badges, how many rather than which.** Profile and the head of the
  Badges tab carry `buildBadgeMeter()` - sixteen segments, earned first,
  each in its badge's enamel - and `badgeNextLine()` (the closest unearned
  badge by share of its threshold). The set itself is the case below it.
  `buildBadgeStrip` is no longer used on either.
- **Badges look like struck pins**: polished metal (hard highlight, dark
  mid-band, second catch), flat enamel with ONE lacquer gloss, no hatch
  on either - the grain read as printed stripes - and a two-layer shadow
  cast into the slot, clipped to it.
- **A case, not a tray**: `.badge-case` is a stitched shell with a lid
  (`.badge-case-lid`, the brass plate moved onto it) and two clasps
  (`.badge-case-front`). Its padding is trimmed under 40rem so no unit
  name breaks mid-word at three across (measured at 320-834).
- **The rank box**: rank name with the NEXT rank as a chip on the same
  line (its emblem, name and %), a full-width 8px bar under both, and a
  `tierShortfall` line ("1 more badge to Platinum").
- **Unlock pop-ups**: a banner's card is the shared 22rem, not 24, with a
  14.5rem picture; a challenge banner carries the "Challenge complete"
  strip (`feat: !def.rank`), a rank banner the "Rank reward" one.
  **With Reduce motion on, every pop-up used to be invisible** - the card
  starts at opacity 0 and only its animation raised it. The rank strip
  also stayed parked off to the side. Both have reduce-motion rules now,
  and a probe that diffed every screen's opacity with Reduce motion on
  and off found nothing else of the kind.
- **Characters fade out at the bottom everywhere**: the mask is on
  `.avatarchar-svg` itself, so every circle, row, podium and card gets it.
- **Queen and Dragon are retired** (`retired: true`, kept in the table);
  `RETIRED_CHARACTER_TO` draws them as the Wizard anywhere they still turn
  up (old builds' rows), and `applyLoadedData` swaps the stored value.
  Sign-up shows ONLY the six starters (no `unlock`, no `feat`), three
  across in two even rows.
- **The starters got their props**: the Ninja's katana hilt over the
  shoulder and a steel plate on the band; the Ghost's cold aura, rim and
  a will-o'-wisp; the Wizard's staff and crystal and a starred robe; the
  Bear's ranger hat and neckerchief (its `AVATAR_ART_SCALE` came off - the
  hat reaches the top); the Alien's lit antennae and suit badge; the
  Samurai's kabuto with the gold horns, and his sword came off (behind
  the head it read as a sword through the helmet).
- **Eclipse became Blitz** (id `blitz`, same `hundo7day` challenge): a
  racer - white helmet, stripe, a sunset in the visor, speed lines.
  "Matches the flare characters too much" because of the black body; a
  challenge character must not look like one of the hunt's.
- **Singularity** gained the lensed disc (the far side's image bent over
  the top of the hole and under it), a warm bloom, and matter spiralling
  down the cloak (`cx-fx-infall`).
- **Customize**: theme colours before banners, and on their own tiles
  (the banner's surface) with circles half as big again. Character names
  never break mid-word; below 25rem they are set smaller instead.
- **Virtual Room "Pick the units" has no tab bar** (it only hid when
  editing), and **Home's unlock queue waits while the chat dock is
  open** - both from the whole-app screenshot pass.
- **ACCOUNT MOVES** (`checkAccountMove` / `followAccountMove`, and
  `tools/firestore-admin.py move`): for one person who lost their sign-in
  and made duplicates. The note lives at `progress/<old code>__moved`
  `{ to }`, readable only by whoever holds the old code - NOT on the
  progress document (pushToCloud replaces it whole) and never anywhere
  listable (it carries a code). The app checks it whenever the live
  listener attaches, takes the target account whole (cloud wins),
  setSyncCode retires the duplicate's rankings row, and marks the note
  done. `move --finish --yes` deletes old progress documents ONLY for
  notes marked done: deleting one a device still listens to reads as a
  server-confirmed remote reset and wipes that device.
  Written on 2026-09-29 for Capitaan and Cap Cam -> Cap (same ghost
  character, both created the day before, near-empty). They take effect
  once 242 is live; then run `move --finish` to clear the duplicates.
  **Its `ACCOUNT_MOVE_SUFFIX` / `accountMoveChecked` are declared at the
  top of the script, beside `ROW_LAZY_FIELDS`, and have to stay there.**
  First written next to `checkAccountMove`, below `attachLiveListener`,
  which boot calls from inside the top-level script: the read hit the
  temporal dead zone and took the whole app down on load, wherever
  Firebase loads synchronously (i.e. on real devices). Every other gate
  was green; only check-chat's "did it finish booting" caught it. The
  sixth `let` below its caller in this file.

### Build 243 - Madison's list after 242

Several 242 decisions were reversed here, on review. The notes below say
which; section 30 of check-behaviour was rewritten to the 243 decision
where it had encoded the 242 one, and section 31 is new.

**Sections 11, 17, 18, 19 and 29 encoded the 243 decisions' predecessors
as well** (Blitz, the Pharaoh, the Champion, the badge meter, the road-map
emblem "drawn past the ring", the banner tile's printed requirement), and a
crash in section 11 was hiding the other eight failures behind it. All of
them now ask the 243 question, and each was run `--against` 242 to make
sure it fails there. One of them found a real gap:
**`UNLOCKS_NEW_IN_235` carries the build 243 rank characters and the K-9**,
or an account seeding its shown-list for the first time would mark the
Paladin as already seen and nobody on Gold would ever be handed it.

- **CHARACTERS, RESTRUCTURED.** Five starters (Ninja, Ghost, Wizard,
  Bear, Alien) - the Samurai went the way of the Queen and the Dragon.
  **Rank rewards start over**, one per rank from Gold, each in its rank's
  colour and each busier than the one below: Paladin (gold great helm,
  plume, sheen), Sentinel (platinum android, a scan across the visor),
  Frost (ice king, sapphire crown, snow), Oracle (amethysts orbiting
  her, third eye), Inferno (crowned in fire, lava in the cracks).
  **Challenge rewards are the "random" characters**: Detective, Masked
  One, Zeus, Poseidon, **Clown** (5 Virtual Room wins - the Champion's
  old challenge), Spartan (10 wins, redrawn with a spear and a shield),
  Marksman, **Astronaut** (7 hundos in a day - Blitz's old challenge;
  Madison picked this over a new Blitz design) and the new **K-9**
  (`study20h`, 20 hours studied, read straight off `store.studyLog` - the
  one thing no other challenge counts). **Secrets** is its own Customize
  group: SWAT, Void, Umbra, Singularity.
- **RETIRED, AND WHAT THEY BECOME.** `RETIRED_CHARACTER_TO` maps samurai →
  ninja, champion → clown, blitz → astronaut, pharaoh → paladin (queen
  and dragon → wizard from 242), both when drawing somebody else's row
  and when loading your own store.
- **KEPT FROM BEFORE: `store.legacyChars`.** Robot, Clown, Officer and
  Astronaut used to come with Platinum, Sapphire, Amethyst and Supernova.
  `legacyCharsFromRanks()` computes, once, for an account that has never
  had the field, which of those it held under the old rules (and adds
  whatever it is wearing); `isLockedCharacter` lets those through. The
  Robot is `legacy: true` - nobody new can earn it and it only shows in
  Customize (a "Kept" group) for somebody who holds it. It is computed at
  the END of `applyLoadedData`, because it reads the ranks.
- **THE SWAT AND THE SUNGLASSES.** The Officer keeps its id (so anybody
  wearing it keeps it) and is redrawn as a SWAT officer whose face you
  can barely see; it is `feat: "shades", secret: true`. Each account is
  given a lifetime test number within its next 40 (`store.shadesAt`,
  picked on the first run of this build), and from that run on EVERY
  run long enough to hide a flare hides a pair of aviators in the
  question header - never on the flare's question - until tapped
  (`store.shadesFound`). **Tapping mid-run happens before summarize()
  takes its before-snapshots**, so the diff never sees it: summarize
  pushes the SWAT and the Undercover banner by name when
  `shadesFoundThisRun`, the way the flares are announced. The flares
  already persisted this way (a due flare is offered every run until
  found) - Madison asked for both to.
- **CUSTOMIZE: TAP FOR DETAILS.** Tiles carry a name and nothing else
  (bar Default's "Matches your theme"). A locked character, banner or
  theme opens `showUnlockDetail()`: the thing large, what it is, what it
  takes, and a progress bar - a count under it only where there is a
  count worth reading, never "0/1". A rank reward or theme names the
  rank it needs and the rank you hold. Unlocked tiles are still one tap
  to use. Five across on a phone so no name wraps; `AVATAR_GRID_NAME`
  gives "Masked One" for the grid. Madison asked whether Customize should
  be tabs - it stays one page (she likes it), with the groups as headings.
- **THE THEME CIRCLES.** `.dot.tier-veteran` was white into steel blue, a
  leftover from a silver tier, so "Gold" previewed lavender - it is the
  Gold rank's gold now. Default was a flat grey (`ACCENT_SWATCH.ink`) for
  a gold/coral/magenta theme; it is `.dot.theme-default`, the triad.
- **THE DEFAULT BANNER IS THE THEME, FOR EVERYBODY.** No banner used to
  draw nothing on a lobby row or a person card. `buildWornBannerArt(id,
  accent)` falls back to `buildThemeBannerArt(accent)`, a `.bnr-theme`
  carrying THAT person's `data-accent`, so their triad resolves on your
  device; `[data-accent="ink"]` now declares the default triad for this.
  Virtual Room participants publish `accent`, as leaderboard rows did.
- **PROFILE AND BADGES, REVERSED FROM 242.** The rank plate is the 241
  one again ("the profile box got worse ... it was so good before").
  The badge meter is gone from both places: the Profile card shows the
  count and a small stack of the badges you hold; the Badges tab heads
  with a medal with the number struck in it (gold when complete).
- **FRIEND CODES, REVERSED FROM 242.** The field is the app's ordinary
  glass text field running the width of the card; your code is large
  monospaced text beside Copy, in no box.
- **BANNER LADDERS: FIRST STILL, MIDDLE MOVES, LAST MOVES MOST.**
  `BANNER_ANIMATED` now = the middle and top rung of every ladder (Great
  Wave, Thunderhead; Sakura, Koi Pond; Sky Temple; Amethyst, Supernova)
  plus the hard one-offs and the secret. Redrawn: Great Wave (night,
  moon, spray), Northern Lights (static, lake mirror, cabin), Koi Pond
  (light shafts, petals, a third koi), **Hall of Fame** (was Starfall:
  the sixteen real badge shapes in their enamels under spotlights, a
  sweep of light clipped to them), **Ascension** (was Earthrise: a gold
  gate on the last peak, turning runes, rising motes), and the secret
  **Undercover** (`shades`, `secret: true`, hidden in Customize until
  held). New keyframes: bn-beam, bn-sweep, bn-rune.
- **SMALLER.** Road map emblems are clipped to the inside of their ring
  (`clip-path:circle(46.5%)`) - "popping out". The Home flare bubbles
  screen-blend the rank emblem into the glass so its dark sky drops out,
  plus an inner rim of light.

### Build 244 - Madison's list after 243

Several 243 decisions were reversed on review; the notes say which. The
art came from four parallel drafts merged in; what is recorded here is
what shipped, not every draft.

- **THE LADDER IS BRONZE, SILVER, GOLD NOW.** "The bronze rank should be
  the first rank." Asked, she chose Bronze -> Silver -> Gold over Bronze
  -> Iron. The KEYS did not move (rookie is Bronze, ranger is Silver,
  veteran is Gold) - only RANK_DISPLAY_NAME / ACCENT_DISPLAY_NAME,
  RANK_COLOR, ACCENT_SWATCH, the theme triads and the `.dot.tier-*`
  swatches. Anybody who was Iron is Bronze today, with a bronze theme.
  Everything in this file above that says "Iron" first describes the
  ladder before 244.
- **GOLD IS YELLOW.** "Could be a little more yellow ... as good as the
  platinum." RANK_COLOR.veteran is #F5C21B (hue 46, was 42), swatch
  #FFD43B. Gold keeps its vermilion planet rim: an amber rim made the
  planet one colour, which the build-232 "second colour on the planet"
  check exists to stop.
- **NEW EMBLEMS FOR THE FIRST THREE, AND EVERY EMBLEM MOVES.** "The icon
  for bronze is confusing because it's a planet", and then, of a flame,
  a crescent moon and a sun of curved tongues: **"the first three ranks
  icons still aren't good."** What was wrong with that set was that it
  was three FLAT symbols in front of four LIT objects: Platinum through
  Supernova are each a glowing core in a halo with flares, broken
  orbits and sparkles in the gaps, and the first three had none of
  that vocabulary. They are built from the same parts now, and the
  life of a star runs from the start: Bronze a copper NEBULA with a
  newborn spark in it, Silver a PROTOSTAR (polar jets on a tilted
  accretion disc), Gold a SUN with a corona and a small planet on a
  broken orbit, then Platinum's binary, Sapphire's comet, Amethyst's
  galaxy, Supernova. Two things learned on the way: the nebula's first
  draw was four overlapping lobes with visible rims and read as a bunch
  of orange balls - a cloud needs its lobes nearly coincident with long
  falloff so no circular edge shows anywhere; and three tendrils curling
  the same way turned it into Amethyst's spiral galaxy, so they run in
  unrelated directions. Silver's disc swirl is drawn as a circle and
  then squashed, so it turns like a disc rather than a wheel. Gold's
  planet does NOT travel its orbit: the only way to do that bypasses
  the Reduce motion switch. Each emblem is split into layers moved by
  transform/opacity only (`inLayer()`, `rk-*` keyframes) - on Home, the
  road map, the Profile coin, the Rank hero and the rank-up moments;
  still on the leaderboard and in chips. Reduce motion (app or OS)
  stops all of it. Supernova is still the busiest mark (27 paths
  against 18-19), which check-behaviour asserts.
- **CENTRED BY WEIGHT, NOT BY BOX.** "The icons in the bubbles aren't
  centred." They were already box-centred to half a pixel; what read as
  off-centre was visual weight. RANK_EMBLEM_FIT uses the ink's
  brightness-weighted centre for all seven (Silver's cy sits at 61 because
  its long upper jet pulls the box up).
  check-behaviour section 32 holds Home's bubbles within 1.5px.
- **CHARACTERS.** Officer, K-9, Spartan, Paladin, Sentinel and the Robot
  are retired; RETIRED_CHARACTER_TO sends each to whatever inherited its
  rank or challenge, so nobody lands on a character they do not hold.
  **The Robot is gone for everybody** ("nobody can have the robot") -
  checked against the live rankings first: nobody wore it and nobody had
  reached Platinum. Rank characters start at Silver now, six of them,
  all crowned elemental sovereigns: Lunar, Solar, Tempest, Frost,
  Oracle, and a crimson Inferno. **The Clown's 244 redraw was reverted
  on sight** ("revert the clown immediately") - the drawing is 243's. A
  Wolf, an owl Scholar and a Pirate were drawn for the challenges and
  refused outright ("I hate the wolf scholar and pirate"); they are
  retired ids, and the challenges went to the Valkyrie (10 Virtual Room
  wins), the Hacker (20 hours) and the Timekeeper (30 days studied,
  `days30`, counted off the study log). What she likes is the sovereign
  set, Zeus and Poseidon, the Detective: premium and a little epic, not
  cartoon mascots or animals - brief any new character against that.
- **THE SWAT ITEM.** The sunglasses and the Undercover banner are gone;
  a SWAT shield is hidden in one of everybody's next 50 tests
  (SWAT_HUNT_WINDOW; the store keeps its 243 field names) and hands over
  the SWAT character, found mid-run and announced by name like a flare.
- **BANNERS.** Undercover removed. Hall of Fame is the sixteen real
  badge shapes orbiting a crowned medal in perspective (drawn twice,
  behind and in front, so nothing needs depth sorting). Ascension is a
  stair of light out of the clouds (a summit read as Summit). Two new:
  Midnight Oil (50 hours studied) and Star Trails (5,000 right answers).
  Both are in UNLOCKS_NEW_IN_235 so an account seeding its shown-list is
  still told about them.
- **THE RANK TAB SHOWS THE CLIMB.** First open after any progress: it
  scrolls to the road and runs the fill from where it was last seen
  (store.rankMapProg) to now; each rank reached since (rankMapSeen) pops
  back to back - two rings, a flash, ten sparks - and the climb runs
  after them. `store.rankMapFx244` gives EVERY existing account the full
  walk once (all held ranks re-shown), on purpose. **Gate fixtures carry
  `rankMapFx244:true`** alongside tourRev, or the show runs inside the
  gate and reads every held rank as "Locked". **The show waits for a
  clear screen**: the recording of it caught a Home-queue unlock pop-up
  sitting over the map while the first ranks popped unseen underneath,
  so runRankMapCelebration now holds while any .rs-spot, flight,
  cutscene, tour or loading overlay is up.
- **SMALLER.** All five secret-flare dots sit on Home's large ring from
  the start. The streak pop sits INSIDE the top bar's gap (placeStreakPop
  measures the counter and Chat/Pause) instead of under it, where it
  covered the question; compact on a 320px phone. Every loading screen
  (splash - as a fade-in layer, so its first frame stays #0A0A0A -
  GENERATING PROFILE, LOADING TEST) wears the theme's colours and glow;
  LOADING TEST was forced to default and no longer is. The Badges
  medal is smooth gradients (the conic one aliased), the case is black
  leather and velvet. The unlock pop-up's lock hangs off a wrapper
  outside the clipped art.

### Build 245

- **THE CREST LADDER WAS TRIED AND REVERTED ON SIGHT - THE EMBLEMS ARE
  244'S.** Madison sent Rocket League's competitive ladder and asked for
  the icons to "feel like it's leveling up". A full set was drawn to it:
  every rank a bevelled metal crest in its own colour (Bronze a plain
  round medallion, Silver a hexagon, Gold a triangular crest, Platinum a
  star, Sapphire a cut gem with fins, Amethyst winged, Supernova big
  wings and a crown) with the celestial motif set into each, escalating
  in size and detail. Her answer was **"revert that immediately. Revert
  the icons to the others."** The crests were reverted to 244's set first; what shipped is below. Lessons worth
  keeping: a reference image is a statement about a FEELING (escalation)
  rather than a style to copy - literal metal crests replaced the
  celestial objects she already liked; and a redesign of something she
  has named as liked ("I like the platinum, amethyst and sapphire")
  should keep those pieces untouched and be shown as a proposal first.
- **THEN THE LADDER WAS RE-DEALT, NOT REDRAWN - AND THIS IS WHAT SHIPPED.**
  "How we rearrange and change those icons per rank so it does have a
  more progressive look? ... easy to tell which one is greater than the
  one before" - so the 244 drawings stayed and were MEASURED (light and
  ink at 44px bubble size): the old order was nearly upside down there
  (Bronze's nebula carried the most ink, Gold outshone Platinum and
  Sapphire, the Sapphire comet was the dimmest mark in the set). Four
  mockup rounds with her, each a picture before any code, settled on:
  Bronze a softer nebula (no ball at the bottom - "I see bronze as a
  ball and then I see a ball in the later stages so it's not clicking"),
  Silver the protostar, Gold a fuller comet, Platinum the binary with
  bodies lit from inside AND the crisp flare ("combine the new and old
  platinum"), Sapphire the galaxy in blue, Amethyst a layered RING
  NEBULA (new), Supernova the burst. Each rank draws in its own
  RANK_COLOR; the colours themselves did not change.
  - **Supernova is the plain burst.** A restrained "max rank touch"
    (counter-turning corona, second shockwave, breathing glint) was built
    on request and reverted on sight: "way too much going on ... not the
    route I was thinking". Don't decorate it again unasked.
  - **A smidge of black (`RANK_CONTRAST`, 1).** "Maybe these rank icons
    need a smidge of black in them ... add some contrast" - every emblem
    was light-on-glow and read soft. The darks are each rank's own colour
    taken most of the way down (never grey, never an outline): dust
    lanes, shadowed limbs, a darker hole in the ring nebula, darker
    crimson between Supernova's points, and `sepRing`, a thin soft dark
    band just outside a bright body, over its glow. It is a RING, not a
    disc: a filled disc greyed Supernova's see-through core. She chose
    the subtle strength over 2.6x ("I wanted more black ... Maybe +?");
    the constant is the only difference, so moving it is one line.
  - **Sapphire's galaxy was reshaped to sit between its neighbours**:
    a star-like core with a crisp four-point flare (Platinum's family),
    luminous arms with star specks and a dust lane, a gentle tilt, and a
    round glow envelope so it shares their footprint. The first tilt
    squashed it into an S-line.
  - **Presentation climbs one step a rank** (`RANK_PRESENT`): drawn size
    about the drawing's own optical centre, glow, sparkles 1,2,3,4,5,6,8
    (`RANK_SPARKLE_SPOTS`), broken arc pairs from Platinum up.
    `fitRankEmblem` uses one fixed window (`RANK_FIT_SIDE`) so a bubble
    or coin KEEPS that climb instead of normalising every emblem to the
    same share of its circle - that normalising is what flattened 244.
  - **check-behaviour section 34 asserts light and ink at bubble size
    rise strictly Bronze -> Supernova** (8.5 ... 27.4 light, 16.3 ... 49.2
    ink when written) and fails on 244. Redrawing or recolouring any rank
    has to keep that order.
  - **The rank banners follow the emblems** ("ensure the banners match
    yes"): Sapphire's (`adept_rank`) went from a comet to a blue spiral
    galaxy and Amethyst's (`elite_rank`) from a galaxy to a violet ring
    nebula - only those two `BANNER_ART` entries, no new classes. A rank
    banner that draws a DIFFERENT rank's object is the thing to check
    for whenever the emblem ladder is re-dealt again.
  - Mockups were rendered from the live builder with page-only patches,
    which is what made each round quick and each pick exactly buildable.
- **TEMPEST IS A STORM, FROST IS ICE - AND TEMPEST IS PLATINUM.** "The
  tempest and frost characters look too similar": the same near-white
  face in near-white straight hair under a fan of white points, lit the
  same cold way, identical in greyscale. The first fix (slate skin under
  a big thundercloud, gold bolt) separated them by DARKNESS and came back
  as "way too big and it doesn't look platinum enough" - the cloud mass
  filled the circle and dwarfed the other five, and the gold was
  Solar's. What shipped: the same head size and edge margin as Lunar,
  Solar, Frost and Oracle; every colour from the Platinum teal (hair
  pale teal-white to #34C3B3, platinum-white skin, deep teal robe, teal
  eyes, a white-to-#5EEAD4 bolt, no gold anywhere); and the storm
  carried by SHAPE - one lightning bolt rising from two small crown
  clouds (not Frost's symmetric spike fan), hair blown to one side,
  forked side lightning, cloud shoulder pads. Frost is unchanged. A rank
  character's palette comes from its rank's colour, and a character's
  footprint matches the set - those were the two things the first pass
  broke.
- **THE TAB BAR MUST NOT SHOW THE STRUCTURE BEHIND IT.** "The bottom tab
  in the unit section screen, there's a visible line in the middle of
  it." The unit grid's dark centre gutter and the card tops came
  through a 16px blur over a 55% fill as a line down the middle of the
  bar (and a horizontal one), measured at ~12 levels of contrast; Home
  never showed it because nothing sits under the bar there. 30px of
  blur over an 84% fill takes it to 1-3 levels. What survives sits
  along the bar's top edge: a backdrop blur extends whatever crosses
  the element's boundary, so a stronger blur alone never fully clears
  a line that crosses the edge - the fill has to do the rest.
- **SWAT IS GONE ENTIRELY.** "Remove the swat one entirely as well." The
  character is `retired: true` (kept drawable, like the Robot, so an old
  published document still renders), `RETIRED_CHARACTER_TO.swat` is the
  Ninja, the `shades` feat is deleted, `maybeStartShadesForRun()` returns
  before placing anything, and the results screen no longer announces
  it. `store.shadesFound` / `shadesAt` stay defaulted and unread, per the
  applyLoadedData rule. check-behaviour asserts the removal (never
  placed even when an account's turn has come; a saved SWAT loads as the
  Ninja) rather than the hunt. The loading line "Calling the SWAT team"
  is unrelated copy and stays.
- **PENAL CODE HAS TWO VERSIONS, AND IT ASKS EVERY TIME.** "Our next test
  is only over slides 0-85 of the penal code ... A lot of people have
  asked that I only put the questions that will be on test." Selecting
  the Penal Code card opens a pop-up with two choices: "Penal Code"
  (every Penal Code question) and "Penal Code — Slides 0–85" (only the
  questions from slides 0–85 of the instructor's PowerPoint, 56 of them,
  listed in `PENAL_TEST_SRCS` / `UNIT_TEST_VERSIONS` with the deck
  cited). Decisions, each asked for:
  - **It asks every time and remembers nothing**: "make it ask each
    time. If people want to do it again they'd hit re run." The choice
    lives on the run's `cfg`, never on `store`; Re-run repeats it.
  - **The card advertises it, the choice stays off it.** First "nothing
    else would change"; then, once she had seen it, "ensure the unit box
    mentions it has the 0-85 version or something so people know and
    want to click it" - so the Penal Code card (and the Virtual Room
    host's copy of it) carries a small blue "Slides 0–85 version now included" pill
    in the space the name cell already reserves, and never shows which
    version was picked. The pill is `pointer-events:none`: it overlaps
    the name's cell, and as a hit target it swallowed taps meant for
    the name (the gate's own tap timed out on it). A tap on it is a tap
    on the card, and section 33 checks exactly that. The start sheet names the chosen version,
    because its counts and hundo note would otherwise be wrong.
  - **"Doesn't count toward hundos." in subtle red** under the slides
    choice in the pop-up - the start sheet note's own #FF9A9A at weight
    400, no box - asked for as "have it mention it in a subtle red".
  - **A shortened run is never a best score.** Checked with real perfect
    runs, a slides run earned no hundo/badge/unlock but DID become the
    unit's best score (unit details), because a unit with no whole run
    took its best from any single-unit run - true of short-Length runs
    before this too. Such runs are now written to test history with
    `part: true` and skipped there (a history entry field, not `store`,
    so no default needed; old entries can't be told apart).
  - **Never the words "test version"** in the UI, and the range is her
    "0–85" (the deck's questions sit on slides 2–79, so 0–85 and 1–87
    select the same 56). check-behaviour asserts the SHAPE of the two
    labels, not the strings.
  - **No notes on Q33 or Q218**, although the deck marks them with
    contradictory answers - "I'll let you know later if I need that."
    Do not add a bankNoteAnswer to either without her asking.
  - The slides version is a shortened run, so the existing hundo rules
    already keep it off the badge: XP yes, hundo no. Select all takes
    the whole unit without asking; dismissing the pop-up selects
    nothing; deselecting never asks.
  - **The Virtual Room carries the version on the room** (`versions`),
    set by the host, so every player gets the same questions. A client
    older than 245 ignores the field and would get the whole unit.
  - The pop-up keeps a slide range on one line (a 320px phone broke it
    at the dash).

#### Build 245 - the Virtual Room

- **RACE IS 45 SECONDS A QUESTION, AND THERE IS NO TIME OPTION.** Asked
  for as *"lets not add time options, just make it where each question
  has a 45 second timer, if you don't click in time it's wrong 'you'd
  get a thing where it shows the right answer but counts it as wrong
  for you' and then goes to the next one."* A pill beside "Question N"
  plus a draining bar, in the theme triad, red for the last 10s. It is
  a DEADLINE (`deadline - Date.now()`), not an interval count, so a
  locked phone or a background tab comes back to the right number;
  Pause shifts it exactly as Game mode's clock does. On timeout with
  nothing picked the question is counted wrong (`timedOutSet`, so the
  review says "Ran out of time"), the right answer is revealed for
  2.6s, and it advances through `advance()` - so the race-line push
  happens exactly as for an answer. **An answer PICKED but not yet
  confirmed with Next when the clock runs out stands**, no reveal: "if
  you don't click in time" was read as not choosing. One line to flip
  if Madison wants that counted wrong too.
- **The race's time limit used to leak into Practice Test credit**: it
  went to `beginRun` as `practiceMinutes`, so a race at 70% set
  `practiceTestPassed`. Gone with the limit.
- **The race line is a smidge wider and bigger**, as asked: 339 -> 365px
  on a 440 phone, markers 1.45 -> 1.6rem, stack step 1.7rem so it still
  beats the marker's diameter. From 40rem it starts BELOW the pinned
  Pause and chat buttons, which sat on its finish end on an iPad. Its
  marker colours come from `vroomColorFor()`, the chat's own, so one
  person is one colour on one screen.
- **Countdowns follow the theme**: "Starting in", its ring (all three
  triad colours), the backdrop glow, "Everyone's ready!"'s tick (was a
  fixed green) and "Starting now".
- **"Can't leave back to main menu after a game with multiple
  participants concludes"** - a classmate's bug report, reproduced: the
  race leaderboard scene is `position:fixed; overflow:hidden` and grows
  a row per player, so from ~5 players on a 1440x791 window (and a
  320x568 phone) Return to lobby / Main menu were drawn off the bottom
  with nothing able to scroll to them, the tab bar forced off and Pause
  down. The board scrolls inside the scene now; Leave room stays up
  between "everyone finished" and the leaderboard; leaving there no
  longer lets the finale roll over Home later; and the leaderboard
  rolls anyway once everyone is in if this device's own results never
  report. **A screen with the tab bar forced off must have its own exit
  on screen at every size** - that is the rule this broke.
- **Ready is spent when a match starts** (each device clears its own).
  It used to survive the match, so a Tug/Battle host pressing Back to
  lobby started a rematch instantly and anybody who got back before the
  host was dropped into a race alone.
- **The host names `racers`** (present and ready) at start: teams are
  built from them and the finale counts them, and a racer with no
  heartbeat for `PRESENCE_STALE_MS` counts as finished and ranks last.
  A closed app used to hold everyone on "3/4" forever. Rooms from older
  hosts, with no `racers`, fall back to everybody.
- **Tug of War and Battle have a way out mid-match**: Pause opens a
  "Leave the match?" card (the match itself cannot pause - the rope and
  health are shared).
- `avatarGlowColor()` maps through `RETIRED_CHARACTER_TO`, like the
  drawing does - a retired character drawn as the Ninja was glowing in
  its old colour.
- check-vroom 13-19 are the gates for all of this (`--only-246` runs
  just those), each written against the build it failed on.

#### Build 245 - the polish list

- **THE DAILY BANNER COMES OUT OF THE BUTTON.** *"Make the banner
  actually come from the daily question thing so you can tell and make
  the daily question do a better 'pulse/recharge' effect ... 2-3
  seconds, and then the banner/toast thing follows."* On a new period
  the "?" dims, a theme-coloured ring fills round it (1.6s), bursts,
  and a small glass "?" arcs up to land on the banner's own "?" icon,
  from which the banner unrolls - fully out ~3s after Home appears. One
  table, `DAILY_CHARGE`, drives both the JS and the CSS (as custom
  properties), so the two cannot drift. Transform and opacity only, no
  SVG filter, nothing loops. The button stays tappable the whole way
  through. The live banner stays 8s (was 4.2s, reported as disappearing
  too soon); plain one-line messages keep 4.2s. Reduce motion: the
  banner simply appears.
- **The banner is centred on the screen, which means it clears the chat
  button EQUALLY on both sides** - it was 27px left of centre once the
  chat button arrived in the top-right corner. Only a 320px phone drops
  it below the chat button's row.
- **The daily question's own header keeps a chat-button-wide right
  gutter** whenever the button holds that corner.
- **Modes read Drill, Exam, Review, Game, Virtual Room**, asked for as
  Review "3rd one listed, under exam". The mode-select tour finds cards
  by `data-mode`, not by position - positional selectors are what a
  reorder silently breaks (see check-tours).
- **The unit screen's Start is a horizontal pill** with a play icon,
  the same size lit and unlit; lit, it wears the primary buttons' 3D
  recipe (top highlight, bright inset top edge, dark inset lip,
  three-layer shadow). The bar stays Home's height. Review's reads
  "Start review, N questions".
- **`DAILY_SCHEDULE` decides the daily question's pool by period key**
  (the date whose 5pm starts the period): US and Texas Constitution up
  to 2026-10-04, Penal Code (the whole unit) 10-05 to 10-11, then the
  first eight units in bank order - "up until and including penal
  code". In the mixed phase the UNIT is drawn first, each of the eight
  once every eight days, so the Penal Code's 340 questions do not take
  ~60% of days. Nothing repeats within a pool until it is used up. Still
  one question for the whole class per period.
- **"THE STUDY GAME" sits under the NOVA wordmark and takes no height**:
  the title block lifts by exactly its height, so Start Studying moves
  0px on every device (check-positions identical). Hidden on short
  screens (laptop windows, phones sideways), where the lift would put
  the greeting on the sphere.
- **Report a bug was a search field.** It reused the unit search's
  style - a stadium pill with a gutter for an icon that is not there.
  It is a real text box now (17px, no iOS zoom, grows as you type,
  N/1200), the primary Send button, inline errors, a 15s timeout, and a
  retry that reuses the same `bug-` id so it cannot duplicate. The copy
  says it goes to whoever maintains Nova with first name, version and
  device attached - the sync-code sentence came off, by request. The
  written document is unchanged, so `firestore-admin.py bugs` reads it
  as before.
- check-behaviour 35-41 are the gates for all of this
  (`ONLY_B245=name,...` runs a subset).


#### Build 245 - the bug run

- **A run that ends on its time limit earns XP for what was answered**
  (same rules as a finished run, over the answered questions only) and
  nothing else: no hundo, badge, personal best or test-history entry.
  A timed-out Practice Test is never recorded as passed - `pct` there
  is over the answered questions, so ten at 90% would "pass" 250.
  Virtual Room runs keep their own scoring.
- **A challenge character's pop-up says "Challenge complete" once and
  "Character unlocked" as its kicker** - it said the same thing twice.
- **A wrong daily answer marks the pick** (`.choice.is-wrong-pick`, a
  new class so Tug and Battle's own `.is-wrong` stay untouched).
- **The start sheet's close x is a 44px target that still draws at
  33.6px** - a transparent border with the background clipped inside
  it, pulled back with a negative margin so nothing moves.
- **Left alone**: "Continue to review (N missed)" wraps to two lines on
  a 320px phone; it cannot fit one without a shorter label.
- check-studyflow 10-13 are the gates.
- **Home's rank bubbles scale with the planet on short screens**: the
  hero is a size container and a bubble is `max(1.75rem, min(2.9rem,
  10.7cqw))` - 10.7% is exactly 2.9rem on the 17 Pro Max's 415px hero,
  so the Pro Max and everything larger are untouched, and an SE 1st
  gen's four overlapping bubbles (one spilling onto the greeting) sit
  apart. The orbit dots take a ~44px tap through a transparent stroke.
- **"New in this update" is for existing accounts only**:
  `markIntroSeen()` runs when sign-up completes and when Sync This
  Device succeeds, so the card never follows onboarding.
- **The back-to-top arrow hides over a control** within 260px of a
  page's end, rather than padding every screen (which would make every
  screen that fits exactly start to scroll).
- **A group chat's Invite/Leave are small buttons under 26rem** - the
  touch `.next` rule was outranking `.chatdock-mini` and drawing them
  full size, which ate a third of an SE's chat.

**A gate diff from an agent is a diff of the file the agent STARTED
from, and it has to be checked like one.** The Virtual Room agent's
`tools.diff` was taken against a newer copy of check-behaviour than it
began with, so as well as its one real change it silently reverted two
other agents' sections and the Penal Code check fix - applied, the
gate simply had less in it and still read ALL PASS. Before merging a
tools diff, read its `-` lines: every one should be something that
agent meant to remove. And run `patch` without filtering its output,
because "succeeded ... with fuzz" is the only warning there is.

### Build 246

- **A GLOW AND A MASK ON THE SAME ELEMENT MAKE A SQUARE.** CSS applies an
  element's `filter` BEFORE its `mask`, so the selected character's
  drop-shadow on `.avatarchar-svg` - which carries the shoulders-fade
  mask - was cut to the mask's rectangle: every selected character sat
  in a glowing square, reported from a device as "clicking characters
  gives a square effect, should just be the glow". The drop-shadow is on
  `.avatarchar-option` now, so it is drawn from the already-faded
  drawing and follows the figure. **Anything that glows AND fades has to
  put the two on different elements**, glow on the outside one.
  check-behaviour 42 asserts the rule itself; pixel tests at the box
  edge could not tell the square from the steep edge of a round glow.
- **The Marksman is 150 in a row (was 100) and the Hacker 25 hours
  (was 20)**, with "if anyone has unlocked them take it back if they
  don't meet these." The locks are computed live, so the numbers alone
  re-lock them; `revokeRaisedCharacters()` (end of `applyLoadedData`)
  takes the character off anybody still WEARING it and drops a queued
  announcement of it. It is limited to `RAISED_BAR_CHARACTERS` on
  purpose: a feat read from data that arrives later (a weekly win, a
  Virtual Room scan) could read as locked for a moment at boot and must
  never cost anybody their character. The feat KEYS stay `streak100` /
  `study20h` - they are names, and nothing stored is keyed by them.
  Measured on the live data when it shipped: the Marksman went back from
  five people (best streaks 108-136) and the Hacker from one (23.4h);
  none of them was wearing it.
- **THE RANKS TAB NEVER OPENED ON A TAP.** It was added with a
  destination in `tabDests` only - the drag-to-switch path - and none in
  the tab's click handler, so dragging onto it worked and tapping it,
  which is what everybody does, did nothing. It shipped like that and no
  gate tapped the tabs. **A new tab needs its line in BOTH places**;
  check-behaviour 43 taps every one.
- **Umbra and Singularity are drawn in their pop-ups.** `characterDetail`
  blacked them out (`hideArt`) along with hiding how to earn them; the
  how stays hidden, the character does not.
- **All three rank banners move, and visibly.** Sapphire joined
  `BANNER_ANIMATED`, and the rank banners' turn went from 110s to 30s -
  at 110s a galaxy barely moves between two glances and a ring nebula,
  which looks the same at every angle, not at all. Amethyst's ring and
  shell also breathe (`bn-breathe`, 5s). **Motion that cannot be seen is
  not animation**; measure frames a second apart, as banim.py did.
- **Every banner in Customize shows its requirement under it** (the
  `label` from `BANNERS`), earned or not.
- **Last week's top 3 for the week of 21 September is recorded by hand
  in `WEEK_RESULTS_KNOWN`**: Sauce, OdinSavior, Napoleon (second and
  third named by Madison), "Winner" on the first and no totals. That week's numbers are unrecoverable - most of the class
  updated onto the XP rebuild during it, which re-awarded everybody's
  whole history through `awardXp()`, so those rows carry their all-time
  XP as that week's (`weekPoints === xp`), and anyone who studied since
  rolled over on a build that threw last week away. Sauce's own device
  recorded his win (it is how he has Zeus) and Madison confirmed it. The
  entry stops applying on 5 October, when `lastWeekKey()` moves on and
  the published `prevWeek` fields (kept properly from build 245) take
  over. **A one-off recompute must never go through the weekly counter.**
- **The daily orb launches off the ring's `animationend`, not a timer.**
  The ring is CSS and starts when the button first paints, which on a
  busy device is a few hundred ms after `playDailyRecharge()` runs, so a
  timer counted from the call sent the orb off a ring still closing
  (check-behaviour 39 caught it at 2.2s against a 2.6s close, on the
  reference devices, twice). **A JS step that follows a CSS animation
  waits for the animation**, with the clock kept only as a fallback.
