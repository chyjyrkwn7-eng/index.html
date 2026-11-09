# The Virtual Room's points results screen (retired in build 384, round 8)

**Removed by:** commit `ca4c46d`, `index.html` only.
**Patch:** [`vr-points-results.patch`](vr-points-results.patch), the same diff.
**Restore:** `git revert ca4c46d`. If that conflicts, use
`git apply -R --3way retired/vr-points-results.patch`.

## What it was

`showVirtualRoomResults()`: a screen headed **Results**, "Ranked by total score."
It had a **Your score** card (Accuracy, the percentage x 100; Time, minus a point a
second; **Total** in "pts", with the note "Every point of accuracy is worth 100. Each
second costs 1."), a separate **Level** card, the room's players as list rows (place,
character, rank, level, "96% - 3:34 - 9386 pts"), a "Review your answers" toggle, the
room's chat at its foot, and Back to lobby / Back to Home.

Also removed: `vroomTopThree()` and `vroomWinnerOf()`, a points-ranked top three that
nothing called, and the screen's CSS (`.vroom-mine*`, `.vroom-result-reveal`).

## Why it went

- **Nobody reached it.** Since build 240 a race ends in the leaderboard cutscene over the
  run's own results; nothing in a real match called this screen. Only gates and
  `tools/shoot-results.py` mounted it - which is how Madison came to see it, in a
  screenshot, and ask "Is this what our leaderboard is now?"
- **Its points contradicted the room's ranking.** The room has been ranked by the XP a run
  earns, then time, since build 213 (`vroomRankedEntries`); this screen ranked by
  accuracy x 100 minus seconds.
- Madison asked for one results screen for every Virtual Room game, matching a drill's,
  with the placings as a podium. That is the run's own results now (see
  `vroomRaceFinalize` and `showVroomTeamResult` in `index.html`).

## What was deliberately left behind

- `vroomTotalScore()`, used by the two one-off history backfills (`seedVroomHistory`,
  `seedVroomTop3`). They read old room documents, some of which carry a points
  `totalScore` from before build 213, and both have already run for every account.
- `participants.<key>.totalScore`, still written (as the run's XP) by
  `finishVirtualRoomTest()`, because older builds and the lobby browser read it.
- `playVroomWinnerCutscene()`, which Tug of War and Battle still play.

## After restoring it

Restore the gates' use of it: `tools/check-vroom.py` section 7, `tools/check-b327r.py`
("the room's results") and `tools/shoot-results.py` were moved to the real finish.
`tools/check-b384-vrplace.py` check 11 asserts it is gone and will go red.
