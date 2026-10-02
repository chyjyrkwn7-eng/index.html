# Retired features

Features taken out of the app on purpose, kept here so each one can be
put back **exactly as it was**. Nothing in this folder is loaded by the
app; GitHub Pages serves it, but nothing links to it.

| Feature | Retired in | Removed by commit | Notes |
|---|---|---|---|
| Game mode | build 283 | `148456e` | [game-mode.md](game-mode.md) |
| Practice Test | build 283 | `ca1e133` | [practice-test.md](practice-test.md) |

Both were taken out on 2026-10-02 because almost nobody used them.
Counted from the live data on the day: Drill had 282 runs from 35
people, Exam 38 runs from 10 people, Game **1** run. The Practice Test
was thought to be something people would not want until the very end of
the course.

## Bringing one back

Each feature was removed in **its own commit that touches only
`index.html`**, so the first route is one command:

```
git revert 148456e      # Game mode
git revert ca1e133      # Practice Test
```

Revert both, in that order, and `index.html` comes back byte for byte to
what it was at `77a1cef` (build 282). Checked before shipping: reverting
the two commits gave an empty `git diff 77a1cef -- index.html`.

If later work has touched the same lines and the revert conflicts, the
same changes are saved here as patches. Apply one in reverse:

```
git apply -R --3way retired/game-mode.patch
git apply -R --3way retired/practice-test.patch
```

`--3way` lets git merge round later edits. Where it still cannot, the
patch is the record of exactly what was there. Each feature's own note
lists what has to be put back by hand.

**After restoring either one:**

- Bump `APP_BUILD` and `version.json` together, as on every deploy.
- Undo the parts of the build 283 gate changes that belong to it. Each
  note lists them.
- `check_b283` in `tools/check-behaviour.py` asserts the feature is
  **gone**, so restoring it turns `check_b283` red. Delete the assertions
  that belong to the restored feature; do not leave the gate red.
- Decide what happens to the rewards that were moved onto Exam. Each note
  says what they were before, and what moving them back would cost
  anybody.

## What was deliberately left behind

These were left in place on purpose, so a restore does not have to
rebuild them:

- **Every `store` field both features wrote**, still defaulted in
  `applyLoadedData()`: `unitGameBeat`, `gameFarthest`, `gameHardcoreMs`,
  `lifetime.gamePlays`, `practiceTestPassed`, `practiceExamPerfect`.
  Dropping a field from `applyLoadedData()` is how a cloud document starts
  losing keys, and old devices may still write them.
- **History entries** with `mode: "game"`. They still read "Game" in test
  history and friend activity.
- **The CSS for the Game screens** (`.speedgrid`, `.lives`,
  `.rs-difflight*`, `.pick-gamedots`, and similar). It is inert, and
  leaving it keeps the restore a pure revert.
- **`practiceTestMinutes`** and the run-clock plumbing behind it. The
  timer and the Virtual Room still read it as `null`.
