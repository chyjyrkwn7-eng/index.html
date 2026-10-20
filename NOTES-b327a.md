### Build 327 (b327a) - every sound in the ambience's language, on by default, a grade that follows the percentage, the XP box heard

Madison, about sound:

- *"The Home Screen on idle is cool, I like it, it works, it sounds nice.
  The swooshing of the random stars on supernova is not it."*
- *"I'm not a fan of the sounds right now, they aren't good enough. The xp
  box is still missing sounds, like when the numbers come in it should be
  cool. The xp bar effect is a bad sound, the xp road map is a bad sound, a
  lot of the sounds seem shared/repetitive. I feel like they just don't go
  with the app."*
- *"Sound effect for your grade, shouldn't the sound effect be synced with
  the percentage and not the amount of questions you got right..?"*
- *"Looking at the badge cutscene the sounds are bad too."*
- *"The idle screen is the only legit one ... The main menu music gives me
  dark Pokemon music vibes and I love it. More of that kinda stuff app
  wide."*
- *"Let's automatically put the sound on as default now. Cause it's cool,
  option will still be in settings though to turn it off."*
- *"I don't really want all the videos of everything or photos. I just want
  videos for the sounds this time around."*

#### One palette, read off the ambience

`amb.home` is untouched: it is the reference. Read note by note, it is **D
harmonic minor**: a D pad (D, A, F, C), a triangle thrum on D, a muted bell
on **Bb** (the dark sixth) at an FM ratio of 3.01 with the dotted echo, and
far twinkles on A, E, **C#** (the leading note) and F at a ratio of 3.5.

The kit gained that language as named parts (in `sndKit`, after `K.arp`).
Every design is now written with them:

- `K.dm(i, root)` - degree i of D harmonic minor (D E F G A Bb C#).
- `K.chime` - the ambience's bell: FM 3.01, a falling index, reverb and
  echo.
- `K.twinkle` - the ambience's far twinkle: FM 3.5, long echo.
- `K.lead` - the "dark Pokemon" voice: a **soft pulse wave** (`o.duty` on
  `K.tone`, `sndPulse()`: a handheld's square with its upper harmonics
  rolled off), a lowpass, and a vibrato that comes in late (`vib[3]`, the
  delay).
- `K.chip` - a chip arpeggio: one pulse voice stepping through a chord
  every 30-45ms, the way a handheld plays a chord.
- `K.bass` (a triangle), `K.pad` (the ambience's detuned saw pad) and
  `K.hush` (its filtered air).

The grammar:

- Good news resolves UP: to A, to D, or through **Bb and C to a bright D
  major**. That is the heroic minor turn, used for 90+, level up, streaks
  of 50, the winner and the podium.
- Bad news falls a half step: Bb to A on a wrong answer; a C# that never
  resolves on the error knock.
- Movement is air, not a swoosh.

#### What changed, by id

Every design was rewritten except these:

- the five character reactions (`react.*`), which are voices;
- the physical sounds: `badge.rub`, `badge.squeak`, `rank.crack`, `vr.tug`;
- the roar inside `rank.whirl`.

Even those were retuned where they carried notes (`rank.whirl` gained a D
minor arpeggio quickening with the spin).

**The ones she named:**

- **`res.xp.fill`** (the XP bar): it was a continuous glide rising an
  octave. It is now a chip arpeggio of D minor climbing the octaves for the
  length of the fill, quickening and brightening as it charges.
- **`rank.road.fill`** (the road map): it was the same kind of glide. It
  is now a stair - one step of D harmonic minor in pulse and a faint bell
  per stair, the steps easing out with the light, landing on a bell on the
  high D.
- **`rank.road.scroll`**: it was a ratchet of wooden detents. It is now
  air drifting the way you travel, with one low bell.
- **The badge cutscene:**
  - `cs.badge` - the dark pad, then an "obtained" fanfare in pulse (D, F,
    A, C#, then the high D held) over a bell chord, and twinkles on the
    glint.
  - `bc.rise` - a triangle climbing D to A under the air.
  - `badge.case.open` - the latches tick on F and D, the lid groans as a
    low triangle, and the glint is two twinkles.
  - `badge.slide` - a thin pulse slide, A up to D.
  - `badge.drop` - its ring is a bell on D.
- **The results screen:**
  - **The grade by band:**
    - `res.grade.fail` - a slow pulse falling F, E, D over the dark pad.
    - `res.grade.pass` - D, E, F, A.
    - `res.grade.great` - chip chords Bb, C, D major with the lead up to
      F#.
    - `res.grade.perfect` - a held breath, a thrum, D major in bells, and
      a fanfare A, D, F#, A.
  - `res.levelup`: three quick A's, then Bb, C, and a held D major - a
    handheld level-up.
  - `res.xp.pop`, `res.xp.overflow` (it ends on C# to D), and the found
    rows: the badge is a bell figure A, D, F; the flare is twinkles on Bb
    and C# (the augmented second); the character is C major to D major.

**New:**

- `res.xp.line` - a note per line of how the XP was earned, a step higher
  each line (`opts.i`).
- `res.xp.total` - the coin: A up to D with vibrato over a D minor bell
  chord.
- `res.xp.count` existed but was never played. It is now the tick of the
  total counting up, climbing two octaves of D minor with `opts.k`.

**Removed:** `home.supernova.ring` (see below).

**Loudness:** every id's `vol` was recalibrated so its loudest 50ms
matches build 326's for the same id. The old balance had been tuned by
ear on a device, so it was kept. That was done with a scratch script that
renders both builds; the numbers are in the catalogue. Two were
deliberately trimmed below the old one:

- `res.xp.fill` to 0.45: the old glide was a loud sustained tone, which is
  most of why it was bad;
- `rank.whirl`.

`check-sound` 7: no pair above .90. The closest is `res.xp.knock` /
`ui.error` at .87; the median pair is .16.

**Distinct by construction:** each id has its own figure, and the gate
renders every id and fails on two identical renders. Where an idea
repeats, it is deliberate and stated in the desc:

- the C#-to-D "arrival" in `ui.notice`, `test.star`, `res.xp.overflow`;
- the heroic turn in the four celebrations.

**Note for anyone redesigning a sound:** the streak tiers are at **10, 25,
50**, not 3, 5, 10. The old `test.streak.*` descs said 3/5/10 and were
stale; they are corrected.

#### The Supernova "random stars"

That was `home.supernova.ring`. The Supernova ring's comet streaks round
Home:

- on a tap of the planet;
- on the planet's pulse;
- at random every 12-38s (build 325).

Each streak played a stereo-circling noise whoosh. It now plays nothing
and the id is gone. The comet itself is unchanged, and a tap on the
planet still rings `home.planet`. `rank.supernova` (the detonation) also
lost its 28 random high glitter pings for a slow D major chord in bells,
so nothing on Supernova scatters random noise any more.

#### The grade follows the percentage

The landing was already chosen by `run.pct`. The count was not:
`res.bar.tick` fired once per RIGHT ANSWER with `frac = good / total`. So
a 12-question run ticked 9 times and a 40-question run 30 times for the
same 75%, at different pitches.

- Now `sndGradeTick(from, to)` is called where the shown percentage
  changes in `paintCount`, and plays one tick per `SND_GRADE_STEP` (4)
  percent passed, pitched by that percentage. The same percentage sounds
  alike at any length.
- `gradeSoundFor(pct)` is the one place the landing is chosen: 100 is
  perfect, 90+ great, the pass mark and up pass, below that fail.
- **A tick per frame at most**: on a slow device a frame can pass several
  steps and plays one. That is the frame rate, never the question count.

#### The XP box heard

Each are one-line hooks:

- `sndXpLine(el)` on every XP line as it lands. Not on the "Bonuses"
  kicker or the "No XP" line.
- `sndXpCount(k)` in `countUp`'s frame: a `res.xp.count` each time the
  number moves (its 40ms cooldown makes ~22 ticks over the 900ms count),
  and `res.xp.total` on the count's last frame. That is outside the
  "changed" test, or a count whose last frame repeats the figure would
  never ring.

#### The Rank tab's own climb has sound

`runRankMapCelebration` (opening Rank with progress since the last look)
was silent. It now plays:

- `rank.road.fill` with the climb (3.2s, the CSS's own `.is-climbing`
  transition);
- `rank.road.fill` (2.6s) and `rank.unlock.pop` for each rank reached on
  the road.

The rank-up journey on Profile already had both.

#### Sound on by default

- `theme.soundOn` defaults **true**. Vibration stays off.
- **An account saved with the old default is switched on ONCE.** It is
  recorded in two places:
  - on the account, as `theme.soundOn327`. It is synced, so turning sound
    off on one phone is not undone by another phone's first launch on 327.
  - on the device, as `class26e.soundon.327`. An older build's `saveTheme`
    drops the field, and the device marker stops that from causing a
    second switch-on here.
- The switch-on happens only when an account's theme exists and has
  neither mark. A device that boots with no theme yet (a sign-in) waits
  for the cloud copy and switches that on.
- The behaviour-toggle rule is followed: a default, a line in `loadTheme`
  (`theme.soundOn327 = store.theme.soundOn327 === true`) and a field in
  `saveTheme`. A new account's theme starts with `soundOn327: true`.
- **iOS:** nothing changed in the engine and nothing needed to. With sound
  on, no `AudioContext` exists until the first touchend/click/keydown
  (`onGesture`). Every play before that returns null quietly, and the Home
  ambience starts on that first tap (`afterResume`). `check-b327-a` 1
  asserts no context before the first gesture with sound on.
- **check-sound section 1 was re-read, not deleted.** It now asserts on by
  default; the one-time switch-on; off sticks across a reload and on a
  device without the marker; and non-booleans are ignored. Sections 2 and
  3 test "free while off" after turning it off.

#### Recording with sound: `tools/record-sound.py`

```
python3 tools/record-sound.py SCENARIO OUT.mp4 [--device phone|ipad] [--fps 30] [--against FILE]
python3 tools/record-sound.py --list
```

This rebuilds the b325h recorder, whose pack folder was never in the repo.

- The output is H.264 plus AAC-LC 48 kHz stereo, with `OUT.sound.json`
  beside it listing every play (id, seconds into the clip, whether the
  engine played it).
- **The audio:** an init script swaps `AudioContext` for an
  `OfflineAudioContext` subclass whose `currentTime` is `performance.now()`.
  It also applies the b325h "now is explicit" fixes, but only to nodes
  made on that context:
  - `start()` and `stop()` with no time, or a past time, mean now;
  - `.value =` becomes `setValueAtTime(v, now)`;
  - cancel-then-hold becomes `cancelAndHoldAtTime`;
  - `disconnect` is a no-op.
  At the end the context is rendered once, cut from the first frame, and
  muxed.
- **The picture:** `tools/record-hundo.py`'s page clock (timers, rAF,
  smooth scroll and every animation seeked to it), installed when
  recording starts. **It continues from the real `performance.now()`.**
  build 325's trap was a clock that moved time BACK, after which
  NovaSound's cooldown refused every tap. This one never does, so no gate
  on plays is needed.
- **Scenarios:** `home-idle`, `results-hundo`, `results-pass` (83%),
  `results-fail` (50%), `results-levelup`, `roadmap-climb`,
  `badge-cutscene`, `rankup-cutscene`, `supernova`, `test`.
  - The results scenarios run a REAL Identity Crimes drill answered by
    real clicks. The first 11 questions are answered in real time and not
    recorded; the clip starts at the last answer.
- **Cost:** at dpr 3 a frame costs ~0.5s here, so a 20s clip is ~5
  minutes. Run one at a time.
- **Harness fixture:** a Supernova Home needs `store.supernovaAchieved`,
  its reward cards marked shown, and `homeUnlockPlaying` FALSE.
  `homeUnlockPlaying` holds the ring's streak (`ringDrawHeld`), so
  record-cutscenes' habit of setting it true silences the very thing being
  recorded.

#### Gates

- **`tools/check-b327-a.py`** (`--against`). It fails on build 326 in 12
  checks, and passes on this build. It covers:
  - on by default, the one-time switch-on, and off sticking;
  - no context before a gesture;
  - two REAL results screens at 75% (9/12 and 30/40) landing alike and
    ticking on 4% steps, never once per answer;
  - 50% landing differently;
  - the XP box's line notes, the count ticks climbing, and the coin last;
  - the palette in the kit;
  - no two ids rendering the same;
  - the Supernova comet streaking with no sound, and its id gone.
- **`tools/check-sound.py`:** ALL PASS. Section 1 was re-read to on by
  default. REQUIRED drops `home.supernova.ring` and adds `res.xp.line`,
  `res.xp.count` and `res.xp.total`.

#### Rules learned

- **A sound she likes is a spec.** Read it note by note (key, timbres,
  space) before designing anything near it. "More of that kinda stuff"
  meant the ambience's key, bell and echo, not more ambience.
- **A sound tied to a count is tied to the wrong thing when the count
  means a percentage.** Tick on the number the screen is showing.
- **Loudness is a decision that was already made.** When redesigning,
  match the old id's loudest 50ms rather than re-balancing by guesswork.
- **A sustained tone that follows a long fill is the loudest thing on the
  screen for its whole length.** Notes with gaps between them carry a fill
  without filling the room.
