### Build 327 (b327b) - one line a kind in the XP box, "Answer streak" with 324's line, the extra that goes down, fish in the water, a softer soap film

Madison: *"Let's talk about the xp box, the descriptions under some of the
stuff is bad, it looks cluttered. The hundo one has an unnecessary
description. That would probably only need to be there or there's multiple
units you got a hundo on? Answers in a row is terrible, it was better how it
was before. The title "answers in a row" could be answer streak or
something. The whole xp box needs to be simplified so it's simple to use and
understand."* *"The xp bar with the extra, not sure what's up with the -xp
stuff in the bar.. it could literally just be the xp that's the extra it
goes down as you level up.. fix that."* *"The underwater fish are still bad,
why are they clearly visible? They don't look like they are in the water..
the water needs to look even better. Bubbles looks good but could be
slightly better. Touch all the hundo effects up."* Branch b327b. Gate:
`tools/check-b327-b.py` (A lines, B the extra, C the fish; `--only A,B,C`),
21 failures on build 326, none here.

> **Supersedes** b326a's "the streak line in words" (`runStreakSub` said
> "Reached 10 twice and 25"), b325's "every line says how it was worked out"
> (a sub-line under every XP line with its arithmetic), and b326c's "-N XP
> lifts off the number" (`rankUpSpendChip`, `.ru-spend-chip`).

- **THE XP BOX: ONE LINE A KIND, A SUB-LINE ONLY WHERE IT SAYS SOMETHING
  (`computeRunXp`).** What each line reads now:

  | line | sub-line |
  |---|---|
  | Correct answers | `47 × 10 XP` |
  | Hundo | none |
  | Hundos ×N | the units, `Identity Crimes · TCOLE Rules` - only when 2+ |
  | Answer streak | `10 ×2 · 25 in a row` (build 324's form) |
  | Speed | `3.5s a question` |
  | Long test | `150+ questions` |
  | Personal bests / Best time / Best score | which ones (unchanged) |
  | Several units ×1.2 | `3 whole units` |

  Gone: "A whole unit, every answer right: 100 XP", "(0:42 in all)", "on
  average", "+100 for every 50 questions", "+20% of the 955 above, for 3
  whole units". **The values did not change** - every line pays what it
  paid on 326, and the total is the lines' sum (check-b327-b A, check-results
  3). The keys did not change either: the Virtual Room's steps still match
  `/^streak/` by KEY (line ~112000), not by label.
  - **"It was better how it was before" means build 324, not 325.** 325
    ("10 in a row ×2 +50 · 25 in a row +50") was the one she called worse in
    326; 326's sentence is the one she calls terrible now. 324's
    `tierKeys.map(t => t + (n > 1 ? " ×" + n : "")).join(" · ") + " in a
    row"` is back verbatim in `runStreakSub`. Title "Answer streak".
  - **The hundo line names the units** from `hundoUnits` (new, optional, on
    `computeRunXp`'s argument): `multiUnitStarsEarned.perfected`, passed by
    `summarize()`. A single-unit hundo has no list, and needs none.
  - The Customize hundo-effect mock card's line reads "Answer streak" too.
- **THE EXTRA GOES DOWN (`rankUpStandingClimb`, `buildXpExtra`).** For the
  rank-up climb on Profile the line under the bar is ONE number, the XP
  past the part of the level the bar holds - `40,266 extra XP` - and it
  only ever counts down: each level's fill comes out of it as the bar
  fills (`extra = into(level) - fill * span(level)`, clamped never to rise,
  so rounding cannot tick it back up). No "-N XP" lifts off anything
  (`rankUpSpendChip` deleted; `RU_SPEND_CHIP_MS` is left, unused), and the
  phone's "to Level N" beside it is hidden while it climbs (the level
  number above is already counting). When the climb lands, the ordinary
  `x / y XP` comes back. Every number the climb records
  (`scene.climb.steps`: `have`, `sum = xpForLevel + have`) is as before;
  each step also records `extra`. The same two spans (`.xpnums-have` /
  `.xpnums-need`) carry it, so colour and type are the bar's; the line is
  `.xpnums.is-extra`, and `.is-spent` at 0.
- **THE FISH ARE IN THE WATER, NOT ON IT.** They were drawn over the
  water's blue and over its light: stickers on the sea. Now
  - **the water is laid over them**: every fish swims in `.hfx-uw-life`,
    the body's FIRST child, so the sheen, the two light strips and the rays
    paint over them; a new `.hfx-uw-dapple` strip (soft light patches with
    silt in them, `hfxUwDappleURL`, faded top and bottom) lies across the
    band they swim in, stepped sideways like the light strips; and
    `.hfx-uw-veil` deepens the floor a touch (static, transparent above
    55% so it never greys the cards);
  - **the haze is in the picture**: `hfxFishURL(k, part, far, haze)` lays a
    pale aqua (`#9ADCE8`) over the fish's outline at `HFX_FISH_HAZE.mid`
    (.34) or `.near` (.22). Pale on purpose - the far veil's dark blue
    turns orange and yellow fish brown (b326a). The key gains `-h34`/`-h22`;
    hfxWarm warms the hazed pieces;
  - **further off is fainter, and every fish comes out of the blue**: the
    school peaks at .42 (was .62), the middle fish at .74 and the near
    angelfish at .84 (both were 1, from the screen edge), each fading in
    over the first 22% of its swim and out over the last 24%;
  - the water itself one band deeper (a 5-stop body gradient, the floor
    .6), the box-only fish fainter (.62).
  Transform/opacity only; no filter, no backdrop-filter (still gated by
  check-b326-a 7).
- **BUBBLES: A SOFTER SOAP FILM (`hfxFilmURL`, sprite `film2-<h>`).** The
  film round each glass hero was bands of saturated colour 8-10 units
  wide, which read as a striped ring painted on. Each band is now two
  strokes, a wide soft one (lightness 76, alpha x.7) and a fine bright one
  inside it, ~6 units in all and pushed out to the rim. Nothing else in
  Bubbles moved.
- **Fireworks, the UFO and Confetti were looked at and left.** Frames at
  2.2s/3.6s (Fireworks) and 3.0s/4.6s (UFO) on a phone read clean, and
  each carries gates on its exact timings and edges (b313_fx,
  b317_hundobox, check-b326-a 5/6) that a touch-up would only put at risk.
- **Measured** (440x956, CPU x4, real time from the effect's first frame,
  7s, 3 runs each; load 3-6 on 4 shared cores, so frames are noise -
  compare main-thread task time): Underwater on 326 4.9-5.0s of task time
  (frames 350-404); on 327 4.6-4.9s (frames 308-404). Script 240-330ms
  both. No regression beyond noise. The first draft also pulsed the dapple's
  opacity and drew it 2 tile-widths wider than its drift needs; both cut
  before measuring the numbers above.
- **The dapple is as soft as the light** (`uwdap4`): check_b313_fx reads
  the sharpest alpha step in every light strip in the water (<= 40 a px).
  The first dapple's silt was hard 1-2px dots (129) and its patches too
  narrow (46); the silt is radial specks now and the patches wider (raw
  step 29). check_b313_fx's "brightest near the surface" is asked of the
  two surface strips only - the dapple lies mid-water on purpose.
- **Gates moved** (each marked in place): check-results 3 (the streak line
  is 324's form) and 5 (a streak label says "streak" or "in a row");
  check-b325-c E (no sub-line under every line any more; held: the answers'
  line says how many, no name is arithmetic, no sub restates a sum);
  check-b326-a 2 (324's form, still one line on a phone); check-b326-c A
  (the line starts on the extra, "N extra XP", counts down, no chips); check_b313_fx (the dapple, above).
- **Failing on 326 as well, not touched**: check_b313_fx "in its tail it
  is still on screen, fading - never cut" for Underwater and the UFO
  (`cutFull: rs-pct-sign`, the same on index-326.html), and check-results
  "a two-unit drill on an iPad: the same gap under every card's heading"
  ([23.8, 19.8] on both builds).
- **Open decisions**
  - A climb that ends at the NEXT wall (more extra still to come) lands on
    the wall's ordinary `12,731 / 4,001 XP`, as Profile shows a wall
    everywhere else; it could instead keep `8,730 extra XP`. That would mean
    changing how a wall reads on Profile and the results card too.
  - "Hundos ×2" carries a ×N in its name, like "Several units ×1.2"; the
    sub-line already lists the units, so the ×N could go.
