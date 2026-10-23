# Build 327z5 (builder D) - the calendar in the app's materials, first place without its sheen, a person card that fades, banners clear of the circle, one unit card size, no line under the tick

Branch `b327z5-d` off 619542a. Gate: `tools/check-b327z5-d.py` (A-F,
`--against`); all pass here, 23 fail on 619542a.

- **The calendar's cards are the app's card.** "The interface doesn't go with
  the rest of the app." Today, Next test, the day card, Final Exams and The
  course take the surface tokens (`--surface-sheen`, `--surface-1`,
  `--surface-border`, `--surface-shadow`, `--surface-blur`, 14px corners) -
  the Stats / Profile card - instead of build 327's per-card colour washes and
  tinted rims. Kickers are `--soft` like every card's; the month title is the
  app's sans (heavy), not the serif; the month arrows and Go to today are the
  black 3D pill (Quit's recipe); the class-day cells a faint lifted tile with
  no outline (326g's rule kept); the Next test count a stat tile. Layout,
  content, dot colours and their meanings are unchanged. One CSS block,
  "THE CALENDAR IN THE APP'S MATERIALS (build 327z5)", at the end of the main
  stylesheet. **This reverses round 10's "each card edged and washed in its
  own colour"** - the colour now lives only in the dots and numbers.
- **No sheen over first place.** `.lb-podium-sheen` and the element are gone;
  the metal ring, crown and medal stay. check-behaviour's top-three check now
  asserts no sheen.
- **Overall's blurb**: "Ordered by rank. Within a rank, whoever is closest to
  the next one is ahead." (was "Ranked by rank. ..."). This Week and Hundos
  read fine.
- **The person card's banner fades** over a 7.6rem strip (was 6.2) on the
  Profile cover's eased curve, `mask-repeat:no-repeat` (the default repeat
  could tile the opaque top under the strip); the portrait moves up the same
  1.4rem so nothing under it moves.
- **`BANNER_FOCUS` / `applyBannerFocus(art, id)`** (beside
  `buildWornBannerArt`): [zoom, x, y] per banner, applied only on the Profile
  cover and the person card (`.bnr.has-focus`, a transform on the art inside
  its clipped box), so a subject drawn in the middle is not under the
  character's circle. Listed: level80, adept_rank, titan_rank, flare_void,
  flare_umbra, flare_horizon, flare_genesis, zenith. Chosen by rendering every
  banner at 1440x540 and searching zoom/offset for the least banner detail
  left under the circle on both covers and both reference devices. Still
  partly behind the circle and left alone (the subject fills the middle, any
  shift loses more than it gains): exam100, astral, elite_rank. A new banner
  whose subject is in the middle wants a row.
- **Every unit card is one height** (`equalizePickHeights(list)`, both unit
  pickers): every `label.pick` takes the tallest card's height, re-measured on
  a width change and when fonts load; the card's 1fr row takes the extra so
  the count and bar stay on the floor. The Starred box and "More units coming"
  keep their own. The cost is air on short names (a row is as tall as the
  Penal Code card: 201px on a Pro Max, 241px on an SE 1st gen).
- **No line under the tick.** The picked circle's shade was `inset 0 -1px 1px`
  - a hard grey arc right under the tick (b327y's hairline in the one circle it
  missed); now a soft fall-off, and its top light is `no-repeat` over the
  border box.
- Gates: check-b327z5-d ALL PASS; check-js OK; check-b326-g fails two Home
  rows (button-to-tab-bar on a 14/15/16 and an iPad) - the same on 619542a
  (the round-7 tab bar), not this package; its class-day-outline rows fail on
  619542a and pass here.
