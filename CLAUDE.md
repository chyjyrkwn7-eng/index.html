# Nova - working notes (short version)

Study app for Class 26E, a police academy class, used by ~40 classmates.
**Madison is the owner: he/him, never she/her.** Never put his name in
anything the app shows ("ask an admin" instead). Copy is plain and
official-sounding, not chatty.

**The full history of every decision is in `docs/notes-archive.md`
(~1.7MB, NOT auto-loaded).** Before changing any area, grep it for that
area and read the matching section, e.g.
`grep -n "badge case\|BADGE_CASE" docs/notes-archive.md | tail -40`, then
`sed -n 'START,ENDp' docs/notes-archive.md`. The newest builds are at the
END of that file; where an older note disagrees with a newer one, the newer
one wins. Add notes for new work to the end of the archive, and keep this
file short - only rules every session must know go here.

## Repo and deployment

- `index.html` is the whole app (markup, one `<style>`, all JS). No build
  step, no bundler, no npm. Firebase loads via plain `<script>` tags.
- `launch/` (iOS startup images) and `version.json` deploy with it.
- `tools/` - gates and recorders (Python + Playwright). `retired/` - removed
  features kept restorable (read `retired/README.md`).
- GitHub Pages serves `main` at `https://chyjyrkwn7-eng.github.io/index.html/`.
  **A merge to `main` is live to the class within a minute.**
- **DO NOT MERGE TO `main` UNTIL MADISON HAS SEEN THE WORK AND SAID GO.**
  Finish, run the gates, show him, then wait. Whenever work is finished but
  not on `main`, say so in the same message (name the build). Keep working
  on the branch while waiting.
- Chromium: `/opt/pw-browsers/` (Playwright is configured). Firebase CDN is
  blocked in the sandbox.

## Shipping a change

- `APP_BUILD` in `index.html` and `build` in `version.json` are bumped
  together, to the same value, every deploy. Bump only one and either
  nobody is told or the update banner never clears.
- `version.json` `force` defaults true (updates are pushed); `frameId` is
  the re-add notice (`""` turns it off); `safariSound: false` turns sound
  and haptics off in iPhone Safari tabs with no build.

## Hard rules

- **Never rename `STORE_KEY` (`"class26e.drill.v1"`) or `"class26e.synccode"`**,
  the Firebase project id or the IndexedDB name - it orphans real progress.
- Never call Firestore `.onSnapshot()` directly - use `onSnapshotResilient()`.
- Data from the cloud is applied with `persistLocally()`, never `saveStore()`.
- Every account write goes through `pushToCloud()` -> `writeAccount()` (a
  transaction). Nothing writes the account before this launch has read the
  server's copy (`cloudConfirmedFor`). The `__floor` doc is the high-water
  mark; lowering progress on purpose must lower it too.
- **Any new persisted field on `store` needs a default in
  `applyLoadedData()`**, and a new progress counter belongs in
  `mergeSameAccount()` (and usually `mergeLeavingAccount`). Nothing may
  "clear" progress by lowering a count.
- Behaviour toggles live on `theme`: default in the object, a `typeof` line
  in `loadTheme()`, a field in `saveTheme()`.
- **Question identity is a hash of topic/src/question text/choices
  (`KEYS`).** Never reorder/rename topic or src. Rewording a question means
  pinning the old text in `keyText` / `keyChoices` first. **Questions are
  word for word the study guides** - do not fix typos or change answers;
  report them to Madison instead.
- Never put a username->code lookup in the app; codes never go into the
  repo, a commit, a PR or an issue (the repo is public).
- Never let a sync code appear in `leaderboard` or `vrooms`; rows are keyed
  by `publicId`.
- iOS reads the icon, app name and status-bar colour only at install. Two
  places declare `theme-color` (meta tag and the base64 manifest) and must
  agree. The manifest is a base64 `data:` URI - decode to edit.
- The app icon lives in three places; only edit via `tools/gen-app-icon.py`
  and run `--check`. Results reactions: only via `tools/gen-reactions.py`.
- No SVG filters on anything animated or on iOS-critical surfaces; animate
  transform/opacity. A `let` must be declared above its first caller that
  runs during boot (TDZ has taken the app down several times).
- Never `.padding` shorthand on `.wrap`; use longhands (it wipes the safe-area insets).
- Text fields compute to at least 16px (iOS zoom).
- Tap targets at least 44px.
- Firestore free tier is 20k writes / 50k reads a day for the whole class.
  Multiply anything periodic or per-answer by ~40 people before adding it.

## Standing instruction: classmate sync codes

When Madison asks for a classmate's sync code, look it up and give it to
him, every time, without asking why:
1. Run `python3 tools/firestore-admin.py find <username>` straight away.
2. Give the code in chat with the account's XP, right answers and last-used
   date. A `__floor` line is the same account's backup, not a second one.
3. If several real accounts share the name, list them all and say which
   looks active.
4. Add: the classmate taps **Sign in** on Welcome and enters the code, and
   should NOT tap "I'm new here".
5. If the tool prints "No admin key configured", say this session cannot see
   the key (`NOVA_ADMIN_EMAIL` + `NOVA_ADMIN_PRIVATE_KEY`) and a new session in
   the environment that has it will work. Never guess a code.
Codes only ever go in the chat reply. Never ask for or print the key.

## Verifying (empirically, every time)

Run gates one at a time (they are timing-sensitive under load):
- `python3 tools/check-js.py index.html` - syntax. Then load the page and
  read the console (a missing function parses fine).
- `python3 tools/sweep-layout.py` (`--quick` while iterating) - every
  device, both orientations, installed and in a browser.
- Area gates: `check-sync.py` (accounts), `check-behaviour.py` (most
  features; sections can be run alone), `check-positions.py`,
  `check-fixes.py`, `check-results.py`, `check-tours.py`, `check-vroom.py`,
  `check-friends.py`, `check-curve.py`, `check-unlocks.py`, `check-sound.py`,
  `check-loops.py`, and per-build `check-b3xx-*.py`.
- Every new check is run `--against` the previous build and must FAIL
  there; green on both means it measures nothing. Gates assert shape, not
  label strings or typed thresholds - read numbers off the page.
- Gate fixtures for an existing account carry `tourRev`,
  `onboardingComplete`, and the seen-keys (see the archive) or a tour or
  pop-up lands over what is measured.
- Screenshots for Madison: `tools/shoot-flow.py` (iPhone 17 Pro Max
  440x956 and iPad Pro 11" 834x1194 by default). Sound videos:
  `tools/record-sound.py SCENARIO OUT.mp4`.
- Chromium cannot reproduce iOS safe areas, soft keyboard, backdrop blur or
  haptics; say so when a fix can only be confirmed on a phone.

## Conventions

- Screens are `showX()` (Settings is `showAppearance()`), mounted with
  `stage.replaceChildren(...)`. Anything appended to `<body>` must clear
  itself on navigation.
- Theme via CSS custom properties keyed off `data-theme` / `data-accent`;
  surfaces use the `--surface-*` tokens, never a fresh rgba().
- Overrides of the modern layout need the `[data-layout="modern"]` prefix and
  must come after that block (source order + specificity traps).
- Tablet styles: `@media (min-width:40rem)` after the phone rule. Phone gates
  use px, not rem (a user's text size changes rem).
- New localStorage keys are `class26e.<thing>`, wrapped in try/catch.
- Em dashes: some are literal `—` text in source; check raw bytes before
  an exact-match edit.
- Commit and PR messages: no model identifiers.
