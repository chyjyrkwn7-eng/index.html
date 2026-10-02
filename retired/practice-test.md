# Practice Test (retired in build 283)

**Removed by:** commit `ca1e133`, `index.html` only.
**Patch:** [`practice-test.patch`](practice-test.patch), the same diff.
**Restore:** `git revert ca1e133`. If that conflicts, use
`git apply -R --3way retired/practice-test.patch`. See
[README.md](README.md) for what to do afterwards.

Retired, not abandoned: the thinking was that people would not want it
until the very end of the course. It is the one feature here most likely
to be asked for again, close to the final exam.

## What it was

Tapping **Exam** on the mode screen did not go straight to unit
selection. It opened `showExamOptions()`, headed "Which exam?", with two
cards:

- **Standard Exam:** *"Pick your own units and length. No feedback until
  the end, no retries."* This led to the normal start sheet, which is
  where the Exam card goes directly now.
- **Practice Test:** *"250 random questions across every unit, 90 minutes
  on the clock - built to feel like the real thing."* This led to
  `showPracticeTestConfirm()`, a briefing screen with:
  - Three numbers: questions (`PRACTICE_TEST_SIZE`, 250), minutes
    (`PRACTICE_TEST_MINUTES`, 90), and the pass mark (`PASS_MARK`, 70%).
  - Four rules: every unit, shuffled; no feedback until the end; against
    the clock (marked as it stands when time runs out); one answer each.
  - "Your record", from `store.practiceExamPerfect`,
    `store.practiceTestPassed` and the `"ALL|exam"` test stats.
  - A **Start Practice Test** button. It set `cfg.mode = "exam"` and every
    unit, and called `beginRun(pool, null, PRACTICE_TEST_MINUTES)`.

The screen's CSS was the `.practice-brief` and `.pt-*` rules. Both
constants, `PRACTICE_TEST_SIZE` and `PRACTICE_TEST_MINUTES`, are still in
the file. So is the `practiceTestMinutes` run variable that a running
Practice Test set, so nothing below the start button needs rebuilding.

**Results:** `summarize()` still sets `store.practiceTestPassed` (a pass)
and `store.practiceExamPerfect` (a perfect, not timed out) when
`practiceTestMinutes != null`. Nothing sets that variable any more, so
both lines lie dormant. A restore brings them back to life without
editing them.

## What happened to its reward

| Banner | Before | Since build 283 |
|---|---|---|
| Phoenix (`exam100`) | Score 100% on the Practice Exam | Score 100% on an Exam of 100 or more questions (`PHOENIX_EXAM_SIZE`) |

It writes the **same flag** (`store.practiceExamPerfect`), so everyone
who already had the Phoenix kept it, and nothing new had to sync. The new
rule needs a real Exam sitting: not timed out, trackable, not a retake,
and not a Virtual Room race.

**On restore:** the old Practice Test line in `summarize()` will set the
flag again by itself. Whether to keep the 100-question rule beside it, or
take it out, is a choice. Keeping both is harmless, because either one
earns the same banner.

`store.practiceTestPassed` is read by nothing. No feat or banner uses it.

## Gate changes to undo on restore

- `tools/check-behaviour.py`:
  - `check_b232`: the briefing had three numbers, four rules and a
    record (`showPracticeTestConfirm()`).
  - `check_b234`: the Practice Test screen did not mention the Phoenix
    banner.
  - `check_b283`: delete the Practice Test assertions (the Exam card going
    straight to unit selection, `showExamOptions` and
    `showPracticeTestConfirm` being gone, and the Phoenix 99/100
    question checks if the rule is reverted).
- `tools/sweep-layout.py`: put `"showExamOptions"` back in `SCREENS`.
- `tools/check-vroom.py` was left alone. Its "a race never marks the
  Practice Test passed" check still holds either way.
