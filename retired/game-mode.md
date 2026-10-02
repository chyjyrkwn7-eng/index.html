# Game mode (retired in build 283)

**Removed by:** commit `148456e` (the mode), then `5006899` (its banners, build 284). `index.html` only.
**Patch:** [`game-mode.patch`](game-mode.patch), the same diff.
**Restore:** `git revert 148456e`. If that conflicts, use
`git apply -R --3way retired/game-mode.patch`. See [README.md](README.md)
for what to do afterwards.

## What it was

The fourth mode on the mode screen, between Review and Virtual Room:
*"A timer on every question and a limited number of lives. Best for
testing yourself under pressure."*

- **It was locked at first.** It opened once you reached Beginner (10
  perfect Drill runs) on enough units (`GAME_MODE_MIN_BEGINNERS`, via
  `gameModeGloballyUnlocked()`). A locked card answered a tap with a toast
  saying how many units were left.
- **Three difficulties, picked on the start sheet** (`GAME_SPEEDS`,
  stored as `cfg.gameSpeed`):

  | Difficulty | Seconds per question | Lives |
  |---|---|---|
  | Easy | 45 | 3 |
  | Average | 30 | 2 |
  | Hardcore | 15 | 1 |

- **A ladder per unit.** Average stayed locked on a unit until Easy was
  beaten there, and Hardcore until Average was
  (`recordGameBeatIfEligible()`). A unit was beaten by finishing it in
  full without losing every life. Beats went into
  `store.unitGameBeat[unit] = {easy, average, hardcore}`. The furthest
  question reached went into `store.gameFarthest`, and the Hardcore times
  into `store.gameHardcoreMs`.
- **During a run:** a red per-question countdown
  (`startQuestionTimer()`), a hearts row (`updateLives()`), and running
  out of time counted as a miss. Losing the last life ended the run in
  `gameOver()`, which showed a results screen titled "Game over" with a
  "Lost your last life" card.
- **XP:** on top of the usual lines, beating a difficulty paid
  `GAME_BEAT_BONUS` (Easy 100, Average 200, Hardcore 400), plus
  `GAME_LIFE_BONUS` per life left (25, 50 or 100). A lost game paid
  neither.
- **Unit cards in Game mode** carried three difficulty bubbles
  (`.pick-gamedots`) with a key under the picker (`.speedkey`). The
  results screen showed the difficulty lights
  (`buildDifficultyLights()`), and its unlock list announced the next
  difficulty.
- **The mode-screen tour** had a step on the Game card: *"Game adds a
  timer and limited lives - good for testing yourself under pressure."*
- **Copy elsewhere** that named it was reworded: the splash line, the
  welcome intro ("Four ways to study"), the Hundos board blurb, the
  Auto-Advance description, and two Stats explanations.

## What happened to its rewards

**Build 283** moved the three Game banners onto Exam, honouring the old
Game counts. **Build 284 then removed them outright**:
*"The banners we have that relevant to the mode game. Let's just go
ahead and remove those banners entirely actually."* Removed by commit
`5006899` ([`game-banners.patch`](game-banners.patch)).

| Banner | Rule in Game mode (until 283) | 283 (Exam) | Since 284 |
|---|---|---|---|
| Lanterns (`easy10`) | Beat 10 units on Easy in Game mode | Pass an Exam on 10 units | gone |
| Great Wave (`average10`) | Beat 10 units on Average in Game mode | 100% in Exam on 10 units | gone |
| Thunderhead (`hardcore10`) | Beat 10 units on Hardcore in Game mode | 100% in Exam on every unit | gone |

**To bring Game mode back with its banners, revert in this order:**
`git revert 5006899` (the banners and their art return, on 283's Exam
rules), then `git revert 148456e` (Game mode returns, and the banners go
back to their original Game rules). Anybody who wore one of these fell
back to the default banner and would need to pick it again.

- **The `hardcore10` character feat** ("Beat Hardcore on 10 units") was
  removed in 283. No character had used it since the Masked One moved to
  its retake challenge.
- **The Masked One's legacy clause** (`hardcoreUnitsBeaten() >= 10`) was
  kept as it was.

## Gate changes to undo on restore

Build 283 removed or retargeted these checks. Bring back the ones that
apply. The `retired/` patch only covers `index.html`; the gate changes
are in the build 283 commit itself.

- `tools/check-behaviour.py`:
  - `check_b218`: the Game difficulty is on the sheet, not in the
    dropdown.
  - `check_b232`: Thunderhead via Hardcore. The label was reworded to
    "the old Game rule".
  - `check_b235`: `gradeReaction({gameLost: 3})` reacts "fail".
  - `check_b240_units`: the `'game'` details row and its two Game checks.
  - `check_b245_modes`: five cards, read as Drill Exam / Review Game /
    Virtual Room.
  - `check_b267`: the toast-over-sheet check used `cfg.mode = 'game'`.
  - `check_b270`: `'game'` was in the label modes.
  - `check_badges`: the "game, one unit at 10" case.
  - `check_b283`: delete the Game assertions.
- `tools/check-results.py`: the `computeRunXp` Game lines, "a lost game
  still gets a results screen" (`gameOver()`), and the difficulty-lights
  label spacing.
- `tools/check-unlocks.py`: `check_hardcore` had the recorder ladder
  (Hardcore refused before Average) through a real Game run, plus the
  unit-card bubbles and key.
- `tools/check-tours.py`: the mode-select scenario note.
