### Build 327 (b327e) - rings that say how it went, the strip that follows the filter, a case with square corners and no quilt, rocks out of the crack

Madison: *"Stats tab, why is the accuracy percentage ring color matched? I
feel like that looked better as grey.. I feel like this tab got worse
somehow. Recent test, why are the percentage rings color matched to the
mode? It should be color matched to hundo (gold) or pass green or fail red.
And then the mode would have that thing as its own color."* *"Test history
is good ... Just ensure the top numbers are accurate. I also feel like the
three top numbers could have that same look, like the percentage as a ring
..."* *"The badge case looks better, the corners of metal though ... are
rounded edges and don't look right? I also don't like the weird pattern of
the case on the inside top part. The case with the metal parts and stuff
still doesn't look right or legit, looks bad and not 3d."* *"Super nova
crack is cool with the stuff coming out but I thought it would look like
some of the floating rocks ... the smaller ash mark is bad and can just go
away, we need it to be combined I guess and the crack needs to be better
looking. All the progressive cracking could be better too."* Gate:
`tools/check-b327-e.py` (A-E, `B327E_ONLY=`); every section fails on 326
(5ce026a), 48 failures.

> **Supersedes** b326a's "a test is its mode's colour" for the RING and the
> row's wash (the chip keeps the mode's colour), b326a's accuracy ring in
> `--theme-c2`, b326b's tufted lid (`--case-lid-bg`), b325b's "one corner"
> radii (the cap's big inner curve, `--cap-ri` 4.25 units), 326c's
> light-streak motes, and 320e's "the shine starts to break at Amethyst".

#### Stats and Test history

- **THE RING IS THE RESULT, THE CHIP IS THE MODE (`TEST_RESULT_TONE`,
  `testResultKey(pct, hundos)`, `testResultTone(entry)`).** Gold `#FFD36A`
  for a hundo or a 100%, green `#5FD99A` at `PASS_MARK` and up, red `#FF7A7A`
  under it, grey for no score. The ring, the row's faint wash (`--tone`, as
  before 326) and a test's own page (ring, hero wash, verdict) use it; each
  unit's bar on a test's page is that unit's OWN result. The mode is the
  `.thx-chip` alone, in `TEST_MODE_COLOR`. Rows carry `.is-hundo/.is-pass/
  .is-fail`. `testModeColor` is still there for anything that wants the
  mode's colour.
- **The accuracy ring is grey (`NEUTRAL_RING_TONE` `#B4B8BE`, `.stx-ring
  .is-neutral`).** Accuracy is not a test, so it has no pass/fail colour, and
  it is not the theme's. Every other Stats number keeps `--theme-c2` (b325e).
- **"Got worse somehow", looked at against 324 (21b0661):** the differences
  were Total XP off At a glance (asked for in 325), the ring and rows in
  mode colours (fixed above), and the sections' darker, more opaque glass -
  that is b326f's app-wide surfaces ("one family of surfaces"), the glass
  builder's area, not changed here. **Open: if Stats still reads heavy once
  the rings are right, it is the surfaces.**
- **THE STRIP FOLLOWS THE FILTER (`testHistorySummary(list)`).** The three
  numbers were worked out over every test while the list under them showed
  only the filter picked, so on Drill they still counted Qualifiers. Now
  they are the count, `Math.round` of the mean score of the rows that have
  one, and the summed `testHundosOf` - of exactly the rows listed, repainted
  with them (`paintSummary` in `paint`). The strip also carries
  `data-tests/avg/hundos`.
- **One card: count, ring, hundos.** A 3x2 grid - the two numbers level
  with the ring's middle (1.6rem mono), the three labels on one line under
  them, hairlines either side of the ring (a background, so nothing extra in
  the DOM). The ring is `buildScoreRing(avg, "thx-sum-ring", result tone)`,
  the same ring as every row; hundos in gold. The first day heading has a
  little more room under the filters.

#### The badge case (both cases - all of it is `caseKit` CSS)

- **A CORNER PROTECTOR, NOT A ROUNDED CAP.** Each cap had a quarter circle
  half its width cut out of its free corner and the case's radius on the
  other: a crescent of metal at every corner, worst at the four by the
  hinge. Now every corner of every cap is `--cap-ri` (.45 units - a hair),
  its two outer edges folded over the case's edge (`--cap-lips`: the dark
  turned-down face and a bright line where the metal turns, `--cap-fold`
  1.35 units), a ridge pressed diagonally from the corner (`--cap-ridge`, lit
  toward the top left), the rivet a little in from the fold. The wall guards'
  feet take the same `--cap-ri` (so check-b325-b D - foot = the cap's inner
  radius - still holds). No clip-path (it would cut off the seat shadow).
- **No quilt (`--case-lid-bg`, 5 layers).** A plain padded cushion: a broad
  dome of light upper-middle, shade in toward the frame and at the foot by
  the hinge, the velvet, the base. The nameplate/label and the two stitch
  rows are unchanged.
- **A SOLID (`--case-recess`, `--case-rim`).** The lining is cut down into
  the tray: its top inner wall in deep shadow (1.6 units down), the sides
  shaded, the bottom wall catching a sliver of light. The tray's and the
  lid's top surfaces carry a lit outer edge and a dark inner one. Shadows
  only, painted once; neutral (check_b232's no blue in the lining).
- **Measured** (4x CPU, the badge scene's first 15s, two runs each, load
  ~9): main-thread task time 14.2 / 15.2s against 326's 19.1 / 16.7s, script
  4.8 / 6.1 against 7.9 / 5.6 - nothing measurably slower; frame counts are
  load noise here (82-185 on one build).

#### The planet's crack

- **EVERYTHING THAT LEAVES THE CRACK IS ROCK (`scarMotePlan`, `.csc-motes >
  i.is-rock.rk0-2`).** The 26 motes were light streaks; they are the ring
  debris' own stone (the `.csc-ringfrag` gradient and its three clip
  shapes, `rk0/1/2`), 1.4-2.4% of the hero like the debris, their underside
  still hot from the crack (one radial layer in the same background - no
  extra element or animation: Home's Supernova still runs 174 animations,
  as on 326). Same three-box flight (turn/out/look), so check-b326-c C's
  paths are unchanged; `csc-mote-look` is now unused. The flakes on the
  scar (`.csc-frag`) and the forming's chips (`.csc-chip`) take the same
  stone.
- **ONE CRACK (`SCAR_SHINE_CRAZE` false).** The crazing on the planet's
  highlight - a web of dark seams, the "smaller ash mark" - is drawn at no
  stage (Amethyst's `shine` is 0, Supernova's `scarShineWound` is skipped).
  The branch that runs up into the highlight (`recC`) stays, as one of the
  crack's own.
- **A FISSURE, NOT A LOG.** `SCAR_CRACK_WIDE` 1.9 -> 1.45 (`SCAR_CRACK_DEEP`
  1.45): the walls and lips read again and Amethyst (.70) to Supernova is
  under twice the width. The seam's spill 6.5 -> 3.4 and halo 2.4 -> 1.8 of
  its width (`scarSeamSVG`): the wide orange haze was the smudge.
- **THE LIGHT GROWS RANK BY RANK.** From Platinum a rank's crack carries the
  same seam (`decorateCrackHero` -> `scarSeam(sc, art, scale)`, the strokes
  narrowed to the stage's width by `(width / SCAR_CRACK_WIDE)^.6`), faint
  and still: opacity .34 / .52 / .72 at Platinum / Sapphire / Amethyst
  (`[data-crack]`), no spill, no breathing. Gold's hairline carries none.
  `crackFormArm` now draws a rank's seam on with its crack (it was
  Supernova only), so a rank-up never shows the new light before the new
  crack.
- Nothing here changes what a stage MEANS (`CRACK_RANK_STAGE`, reaches,
  `heroCrackStage`, the forming's timing).

#### Gates

- `tools/check-b327-e.py` A-E (both reference devices). C works the numbers
  out by hand from its fixture; D reads computed radii and the lining's
  inset shadow's OFFSET (its blur passed on 326 and was dropped from the
  measure); E reads the motes' stone against a live `.csc-ringfrag` and the
  shine's dark cover off the art's own canvas.
- Moved (each marked "MOVED IN 327"): check-b326-a 3 (ring and wash are the
  result, the chip the mode), check-b326-b F (a plain padded lid, still
  stitched).
- **Open decisions:** the history strip's ring takes the average's RESULT
  colour (an 82% average is green) - grey like the accuracy ring is the
  other reading; Stats' heavier surfaces belong to the glass builder.
