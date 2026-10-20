### Build 327 (b327d) - one glass again, a tick that draws itself, the next test on its unit, bigger tab icons, the lobby's switch back, Save and exit blue, a quieter sky

Madison, Oct 20: *"The new darker liquid Liquid Glass for the unit selection
screen is cool I guess but now it don't go with the rest of the page, like it
doesn't go with the start bar, the search bar, the chat button? ... the Liquid
Glass feel/interface app wide kinda lost its touch. I'm not in love with it
anymore. It's not cohesive, maybe some reverting/improving is needed."* *"The
unit selection cards, could they be improved by making the checkmark better?
Would it be a cool feature if somehow like a mark on the units for the
upcoming test?"* *"The bottom tab bar, the icons of the 4 things are good but
could they not be slightly bigger and more white?"* *"I don't like the green
outline for being ready in the lobby, it's too much. For the lobby, I prefer
the regular toggle switch with the invite friends button to the left of it.
The toggles description is just confusing?"* *"Save and exit as a green button
is ABSOLUTELY not the move ... Make that a color that makes sense and goes with
it all."* *"the stars in the background ... a smidge smidge less."* Branch
`b327d`. Gate: `tools/check-b327-d.py` (7 sections, `ONLY_FN=check_lobby,...`;
all pass here; against build 326 every section fails except its guards -
"Oct 27 marks nothing", "no sideways scroll", "the bar on screen", "white on
Save and exit at 4.5:1", and the token-equality app-wide check).

- **ONE LIQUID GLASS, AND IT IS THE TAB BAR'S.** Measured on the unit screen
  on 326 there were three recipes side by side: the unit card a near-black
  blue `rgba(13,16,21,.72)` under `blur(16px) saturate(1.2)` (b326f's
  `--surface-1`), the search field `--surface-2`, the chat button a third
  (`rgba(20,25,32,.55)` under an 8px blur that saturated 1.8 and brightened),
  and the tab bar - the one surface she never stopped liking - a grey glass
  `rgba(42,45,53,.8)` under `blur(30px) saturate(1.8)` with a bright 20% top
  rim. The cards were the odd one out, which is what she could not name. So
  the surface TOKENS now carry the bar's material, and everything already on
  the tokens follows (b326f did the work of putting ~60 rules on them):
  `--surface-1` `rgba(36,40,48,.7)` (the bar's neutral grey tint, never
  blue-black), `--surface-2` `rgba(44,48,57,.72)` (one step lighter, raised
  controls), `--surface-blur` `blur(24px) saturate(1.2)` (heavy enough that
  stars and glow come through as colour, not detail; 326's mild saturate and
  no brightness, so its "nothing boosted" rule holds), `--surface-border` `rgba(255,255,255,.13)`,
  `--surface-shadow` the bar's rim: a soft drop, a 3% inner hairline, a 20%
  catch-light along the top and a dark lip along the bottom, and
  `--surface-sheen` the bar's top-lit wash. The 22 rules that wrote out the old
  card shadow by hand and the 18 that wrote the old `.11` hairline now read
  the tokens. Moved onto the tokens as well: the chat button, Pause (which
  "wears the chat button's glass" since build 215), the search field's and
  Find me's shadows, and the start sheet's `.chip`. **The tab bar and its
  lens are untouched** (b325f/j gates); the cards came to the bar, not the
  other way. Overlays (toast, banners, tooltips, sync confirm) keep their own
  recipe on purpose, as in 326. Lighter than 326 and more opaque than 325.
- **CONTRAST WAS THE PRICE, AND IT IS MEASURED.** The first, lighter fill
  (`rgba(44,48,57,.64)` under saturate 1.4) failed check-b326-f 5b on every
  theme: the small `--soft` labels ("Display & motion", "In this room", "3 of
  4 ready", Stats' week switch) at 4.0-4.48:1, and on Sapphire the Stats
  numbers (`.stat-num`, the raw theme colour `#2F6BFF`) at 2.8 against 3:1.
  Three moves, all in place: the fill came down to `.7` of `(36,40,48)`,
  `--soft` went `#8E9BA5` -> `#A0ACB6` app-wide (secondary text a step
  lighter everywhere, which suits the "more white" direction), and
  `.stat-num` is the theme colour 80% with 20% white (same hue - check-b325-e
  compares hues). 5b passes on all eight themes. **Any further lightening of
  the glass has to run 5b.**
- **A DARK-ENOUGH GREY, NOT A DARK CARD.** check-b326-f 5's "page cards
  <= 40 grey" encoded 326's darkness; it reads `<= 60` now with a note. The
  rule that stays: a new box takes a token, never a fresh rgba().
- **The tick draws itself.** `appendPickTick(box)` puts an SVG path
  (`pathLength=1`) in each unit card's circle on both pickers; picked, the
  circle becomes a lit bead (a white radial light over the accent, a 3px
  accent halo) and pops 1.06x on an overshooting curve, and the tick's
  `stroke-dashoffset` runs 1 -> 0 over .3s after a .12s beat. Unpicked runs
  back in .14s. The `"✓"` text stays in the box at `font-size:0` for
  anything that reads it. Reduce motion (app or OS): no transitions. Drag to
  select's `pick-drag-flip` pop is untouched.
- **The next test's units carry a mark - only when the app KNOWS.**
  `nextTestUnits()`: the next test still to sit (`nextTestEntry`, today
  included), its posted topics (`testTopicsFor` - the Calendar's own table,
  `TEST_TOPICS`), and every unit a topic starts with ("Penal Code - slides
  256-578" names Penal Code). A test with nothing posted marks nothing: never
  a guess off the class day's text, which says what is TAUGHT, not tested.
  `appendUnitNextTestTag(row, name)` adds `.pick-nexttest` - a small amber
  "NEXT TEST  Oct 26" (Today / Tomorrow when it is) in the calendar's test
  amber - in its own grid row `next` (an auto row, zero high on every other
  card), on the test setup and the Virtual Room host's picker. A label:
  `pointer-events:none`, so a tap is the card's and a hold still opens the
  details. On Oct 20 that is Penal Code alone; from Oct 27 (the Nov 2 test
  has nothing posted) nothing. **Posting a test's topics in `TEST_TOPICS` is
  all it takes to mark its units.**
- **Tab icons a step bigger and whiter.** The three line icons (Home,
  Leaderboard, Calendar) 1.75rem -> 1.95rem on a phone (28 -> 31px), 2.2rem ->
  2.4rem from 40rem (35 -> 38px); the six-item bar 1.6 -> 1.75rem; tabs you
  are not on `rgba(255,255,255,.94)` (was .84), the one you are on `#fff`.
  The Profile character keeps its own size (build 317). One rule set after
  every older icon rule, scoped with `:not(.bottomtab-icon-avatar)
  :not(.bottomtab-start-icon)`. **The bar does not grow**: the extra size is
  taken back as a -.1rem margin above and below each icon. On the first pass
  the bar grew 3-4px, and on an iPad Pro 11" in landscape (and a 17 Pro Max
  at 85% zoom on its side) the daily "?" bubble - which parks above the bar
  there - landed 27px from its button, where check-fixes holds it to 24. On a
  320px phone the bar is 296px with every tab inside it, Home and the unit
  screen alike.
- **The lobby's switch is back, Invite to its left, one line under it.** 326's
  two-option segment (`.vroom-access-seg`) is gone. `.vroom-roster-tools` is a
  grid: phone `"invite open" "line line"`, tablet `"invite line open"`.
  `.vroom-open-switch` is a `role=switch` button round the app's `.nsw` track
  (so `nswHost` gives it the Liquid Glass lens like every Settings switch),
  named "Open to class". The line is ONE sentence that never changes with the
  state - "On, anyone in 26E can find this room and join." - so it can never
  be read as the opposite of the switch (the 325 complaint was a state printed
  where a name should be; 326's was that each choice had its own sentence).
  Off is the default and needs no sentence. On a 320px phone Invite friends
  is its icon alone (`.vroom-invite-word` hidden; the aria-label stays).
- **No green ring on a ready player.** The card keeps its ordinary edge and
  shadow; `::before` (the old left strip, already transparent) becomes a full
  faint green wash (9% fading to nothing), and the chip says Ready in soft
  green `#8EF0BF` on a 14% green tint with a 1px inner green line and a
  CSS-drawn tick (hidden on a 320px phone, where names were already short).
  In a crowded room the dot stays solid green with a small glow. check-b326-f
  1 was rewritten to the decision ("reads as ready, arrives whole, no ring").
- **Save and exit is the app's blue, deep.** `#2B5AAE`, pressed `#224A8F`,
  lip `rgba(170,205,255,.55)`; same matte recipe, no border, Quit's height.
  White on it 6.6:1. Why blue: green is a right answer and a ready player
  here, so on a pause sheet it read as a verdict; blue is what the app already
  uses for what it keeps for you and is calm about (the XP bar `#3D8BFF`, the
  sync code, the slider fill). Muted so it stays quieter than Resume's white.
  Resume white, Save and exit blue, Quit black. No gate asserted green
  (check-b326-a 4, check-behaviour 321h/320h ask only "opaque, not Quit's
  colour, readable, darker pressed") - all still hold.
- **The sky, a smidge smidge less.** Same trim as 326: `SKY_TILES` 42 -> 38
  dust and 94 -> 86 stars off the END of each seeded run (every star that
  stays is where it was), `SKY_ALPHA` .96 -> .88. Measured on Home at
  440x956@3 with everything else hidden: 430,813 -> 362,657 (84% of 326, 73%
  of 325). check-b326-g 2 now asks 60-92% of 325.
- **Gates moved, each with a note in place:** check-b326-f 1 (ready: chip and
  wash, no ring), 2 (one switch, one name, one unchanging line), 5 (cards
  `<= 60` grey); check-b326-g 2 (60-92%); check-behaviour 266 (the lobby
  switch), 323v (Invite and the switch in the header), 324g (the lobby
  contributes one switch again, a tap turns it on).

Screens for her (before = 326, after = this branch), 440x956 and 834x1194:
`/tmp/claude-0/b327d/before/` and `/tmp/claude-0/b327d/a2/` (unit screen,
Penal Code card), `/tmp/claude-0/b327d/b326/` and `/tmp/claude-0/b327d/a3/`
(lobby, pause), `/tmp/claude-0/b327d/a4/` (Home with the new tab icons).

Open questions:
- **The bar itself is still saturate 1.8 at 80%; the cards 1.2 at 70%.** They
  read as one material in Chromium (whose backdrop blur is not faithful);
  judge it on a phone. If the cards look flatter than the bar, the token is
  the one place to turn it - and 5b has to pass after.
- **`--soft` changed app-wide**, the one change here that reaches screens no
  gate in this package looked at. It only gets lighter, so contrast only
  improves; worth a glance at anything that set a hierarchy against it.
- **The next-test mark matches by name prefix.** A topic posted as anything
  other than the unit's own name ("Arrest" for "Arrest, Search, and Seizure")
  marks nothing. Post topics starting with the unit's name.
- **The Calendar's `--cal-glass` is still its own** (b326 open question) -
  not pointed at the new tokens here; it is the calendar package's screen.

Gates run on this branch (one Chromium at a time): check-b327-d ALL PASS
(fails on 326 as described); check-b326-f ALL PASS (sections 1, 2, 5 moved;
5b contrast on all eight themes); check-b326-g sky PASS; check-b326-a ALL
PASS; check-b325-f and check-b325-j ALL PASS (the lens); check-behaviour
266, 323v, 324g, 321h ALL PASS; check-vroom ALL PASS; check-tours all steps;
check-fixes --only "17 Pro Max" / "iPad Pro 11" / "iPad mini" all verified,
"SE (1st" one failure, the known SE 1st gen 568x260 browser GREY BAR that
326 also fails; sweep-layout --quick 14/14; check-js OK.
