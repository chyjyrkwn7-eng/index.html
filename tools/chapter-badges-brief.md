# Fire Code chapter badges - design brief and phase 2 spec (build 384.61)

Owner request: "Big change. Badges are gonna be designed based on what the chapter is about / the title (mostly the title). For
example Means of Egress could be a door in the open position? Make them cool." This is for the Fire Code class only. The
academy's sixteen (now more) badges are untouched; the gate proves it byte for byte. Madison asked for this, so it overrides the
academy's old rule that a badge never draws its subject (and the Fire Code round-2 note "please don't make badges that look like
real things"): the newer instruction wins, in these 58 chapters only.

Phase 1 (this build) is the framework, six sample icons and the look to approve. Phase 2 draws the other 52.

## 1. What was found (read before drawing)

- **Colour is already solved, and better than asked.** `BADGE_FAMILY` (21 named colours) is no longer what Fire Code uses. Since
  badges round 2 every chapter has an enamel of its own (`IFC_BADGE_THEME`, 58 distinct, none within CIEDE2000 11 of another).
  So "every chapter a distinct colour family" is already true and nothing is grouped. The enamel is the plate colour; the icon's
  colours are derived from it (section 4), so a chapter's icon is always in its own colour family.
- **Outlines are already 58 distinct silhouettes** (`IFC_BADGE_SHAPE`), and each chapter's BACK (its title + FIRE CODE) is laid out
  on that outline. That is why short titles hold the narrow outlines and long titles the roomy ones.
- **The outline is now the main limit on how big an icon can be.** The icon sits on the one open plate inside the metal rim; the
  biggest square that fits the plate (section 3) ranges from 54 units (quarter dome) down to 4 (the C-ring) of a 100-unit
  frame. Under ~30 an icon is a speck on a phone: bolt 20, dart 19, tau 17, maltese 23, four-point star 23, kite 26, peaks 26, bilobe 26,
  chevron 27, cross 27, fan 27, bardia 27, hourglass 22, C-ring 4. Roomy: quarter dome, gonfalon, disc, coin, pennon, slope, keystone,
  castle, shield, tag, bucket, notched square, cinquefoil (all over 44).
- **In phase 1 three sample chapters were moved to roomy outlines nobody in Fire Code used** (Chapter 2 dart -> octagon, Chapter 10 bolt
  -> gate, Chapter 20 five-point star -> hex), because a door in a lightning bolt is a door the size of a thumbnail. Only three
  such outlines exist (octagon, hex, gate; the academy's `gate` is shared, which the notes allow). **This is the open decision for
  the owner** - see section 9.
- **Chapters named in the request do not exist as such.** There is no "Fire Alarm and Detection" and no "Automatic Sprinkler
  Systems" chapter: both live in Chapter 9, Fire Protection and Life Safety Systems (sprinkler head drawn; a bell is the alternative).
  "Hazardous Materials / Flammable and Combustible Liquids" are Chapters 50 and 57 (57 drawn: a flame in a drop).
- **On a phone the case is 8 across**, so a badge in it is ~44px and its icon ~20px. At that size the icons read as a blob of the
  right shape (door, book, drop, plane, hydrant) and no more; the badge in your hand (tap one) is the size where the picture is read.
  Design for the 96px sheet and make sure the silhouette still says the thing at 26px.

## 2. The 58 chapters (exact titles, question counts, concept, colour, outline, who draws it)

Concept = one instantly nameable object drawn from the TITLE. Enamel = the chapter's existing colour (unchanged). Outline = the
chapter's existing outline key (the three samples that moved are shown with their new one). "part-N" = which phase 2 file draws it.

| # | Chapter | Qs | Concept | Enamel | Outline | Drawn in | Risk / note |
|---|---------|----|---------|--------|---------|----------|-------------|
| 1 | Chapter 1: Scope and Administration | 88 | a rubber hand stamp (handle, base, a stamped bar under it) | `#007A7C` | crown | part-1 | ABSTRACT (Scope and Administration): the stamp is administration - approvals, permits. |
| 2 | Chapter 2: Definitions | 111 | an open dictionary with a ribbon marker | `#83399B` | octagon | sample | ABSTRACT (Definitions): DONE, sample. |
| 3 | Chapter 3: General Requirements | 74 | a clipboard with three ticked lines | `#00375D` | bowhex | part-1 | ABSTRACT (General Requirements): a checklist is the requirement list. |
| 4 | Chapter 4: Emergency Planning and Preparedness | 40 | a floor plan sheet with a dotted exit route and an arrow | `#E59977` | shield | part-1 | mildly abstract (Emergency Planning): the plan, not the emergency. |
| 5 | Chapter 5: Fire Service Features | 50 | a fire helmet (front shield, brim, crest) | `#DD524F` | maltese | part-1 |  |
| 6 | Chapter 6: Building Services and Systems | 41 | a ventilation fan: a propeller in a square duct | `#DBB3E5` | slipdisc | part-1 | abstract (Building Services and Systems): HVAC is the commonest of them. |
| 7 | Chapter 7: Fire and Smoke Protection Features | 21 | a brick wall with a flame stopped on one side and smoke over it | `#6A0B2C` | gem | part-1 |  |
| 8 | Chapter 8: Interior Finish, Decorative Materials and Furnishings | 34 | an armchair (furnishings), a curtain edge optional | `#83E6F2` | scoopsq | part-1 |  |
| 9 | Chapter 9: Fire Protection and Life Safety Systems | 145 | a pendant sprinkler head with drops | `#2E9BD8` | cinquefoil | sample | DONE, sample. The chapter also holds alarms and detection: a bell/smoke detector is the obvious alternative if the owner prefers it (no chapter is titled Fire Alarm and Detection or Automatic Sprinkler Systems). |
| 10 | Chapter 10: Means of Egress | 132 | an open door (leaf swung into the room, bright opening) | `#00954C` | gate | sample | DONE, sample (the owner's example). |
| 11 | Chapter 11: Construction Requirements for Existing Buildings | 43 | an older brick house (pitched roof, windows) with a hammer | `#5F2100` | wave | part-1 | mildly abstract (Construction Requirements for Existing Buildings). |
| 12 | Chapter 12: Energy Systems | 43 | a battery cell with a lightning bolt on it | `#7E6B35` | bilobe | part-1 |  |
| 13 | Chapter 20: Aviation Facilities | 23 | an airliner climbing, seen from above | `#0073AB` | hex | sample | DONE, sample. |
| 14 | Chapter 21: Dry Cleaning | 17 | a shirt on a hanger | `#006917` | hourglass | part-1 |  |
| 15 | Chapter 22: Combustible Dust-Producing Operations | 15 | a sack of grain with a puff of dust over it | `#B9CB3B` | fan | part-2 |  |
| 16 | Chapter 23: Motor Fuel-Dispensing Facilities and Repair Garages | 46 | a fuel pump with its hose and nozzle | `#003C3D` | disc | part-2 |  |
| 17 | Chapter 24: Flammable Finishes | 21 | a spray gun throwing a cone of paint | `#6A55CF` | kite | part-2 |  |
| 18 | Chapter 25: Fruit and Crop Ripening | 6 | an apple with a leaf | `#ADCA96` | cross | part-2 |  |
| 19 | Chapter 26: Fumigation and Insecticidal Fogging | 13 | a beetle in a puff of fog | `#C8315E` | twinblock | part-2 |  |
| 20 | Chapter 27: Semiconductor Fabrication Facilities | 18 | a microchip: a square with pins on four sides | `#FE7ED3` | ticket | part-2 |  |
| 21 | Chapter 28: Lumber Yards and Agro-Industrial, Solid Biomass and Woodworking Facilities | 17 | a stack of logs, end on | `#473100` | slope | part-2 |  |
| 22 | Chapter 29: Manufacture of Organic Coatings | 10 | a paint can with a drip down its side | `#00A5BD` | bucket | part-2 |  |
| 23 | Chapter 30: Industrial Ovens | 9 | an oven: a box with a window door, a handle and two knobs | `#B54D1B` | slant | part-2 |  |
| 24 | Chapter 31: Tents, Temporary Special Event Structures and Other Membrane Structures | 29 | a tent with a peak and a pennant | `#9A7F00` | coin | part-2 |  |
| 25 | Chapter 32: High-Piled Combustible Storage | 33 | a pallet rack with three boxes on each shelf | `#313800` | burstplate | part-2 |  |
| 26 | Chapter 33: Fire Safety During Construction and Demolition | 24 | a wrecking ball on a chain from a boom | `#8A5A34` | saddle | part-2 |  |
| 27 | Chapter 34: Tire Rebuilding and Tire Storage | 18 | a tyre, face on, with its tread | `#444F58` | dishhex | part-3 |  |
| 28 | Chapter 35: Welding and Other Hot Work | 18 | a welder's mask with a spark | `#FFCDAC` | bitehex | part-3 |  |
| 29 | Chapter 36: Marinas | 6 | an anchor | `#1E54B9` | tau | part-3 |  |
| 30 | Chapter 37: Combustible Fibers | 15 | a spool of thread | `#E296A3` | medal | part-3 |  |
| 31 | Chapter 38: Higher Education Laboratories | 10 | a conical (Erlenmeyer) flask with bubbles | `#9F70AC` | chevron | part-3 |  |
| 32 | Chapter 39: Processing and Extraction Facilities | 11 | a leaf with an extracted drop | `#3FC270` | keystone | part-3 | RISK: this chapter is plant extraction, and the cannabis leaf is the obvious picture - use a plain generic leaf; the tone is official. |
| 33 | Chapter 40: Storage of Distilled Spirits and Wines | 8 | a wooden barrel (staves, two hoops) | `#A8176C` | quarterdome | part-3 |  |
| 34 | Chapter 50: Hazardous Materials—General Provisions | 55 | a diamond placard split into four, no text | `#C9A831` | roundel | part-3 | ABSTRACT (Hazardous Materials - General Provisions): the hazard diamond is the general symbol; no letters or numbers. |
| 35 | Chapter 51: Aerosols | 17 | a spray can with its cap, nozzle and a spray puff | `#4F215D` | slipsq | part-3 |  |
| 36 | Chapter 53: Compressed Gases | 20 | a gas cylinder: valve, collar and body | `#65A63B` | star4 | part-3 |  |
| 37 | Chapter 54: Corrosive Materials | 10 | a dropper bottle whose drop has bitten into a surface | `#A2A7DF` | ribbon | part-4 |  |
| 38 | Chapter 55: Cryogenic Fluids | 16 | a snowflake | `#D5ECF5` | peaks | part-4 |  |
| 39 | Chapter 56: Explosives and Fireworks | 48 | a firework rocket with a spark burst | `#535F00` | gonfalon | part-4 |  |
| 40 | Chapter 57: Flammable and Combustible Liquids | 79 | a drop with a flame in it (the flame a window onto the enamel) | `#F96186` | pennon | sample | DONE, sample. |
| 41 | Chapter 58: Flammable Gases and Flammable Cryogenic Fluids | 14 | a gas burner nozzle with a ring of flame | `#E0703A` | bent | part-4 | close to Chapter 53 (cylinder) and 57 (flame in a drop): keep it a burner, not a tank or a drop. |
| 42 | Chapter 59: Flammable Solids | 18 | a lit match | `#C695FF` | cring | part-4 |  |
| 43 | Chapter 60: Highly Toxic and Toxic Materials | 23 | a skull and crossbones | `#005235` | spire | part-4 | the standard toxic pictogram; keep it graphic, not grisly. |
| 44 | Chapter 61: Liquefied Petroleum Gases | 26 | a horizontal propane tank on legs | `#B7710E` | notchsq | part-4 | close to Chapter 53: horizontal, on legs, with a dome and a gauge. |
| 45 | Chapter 62: Organic Peroxides | 10 | a molecule: three atoms joined by bonds, one pair doubled | `#00A8A0` | hexstar | part-4 | ABSTRACT (Organic Peroxides): the peroxide's O-O bond; no letters. |
| 46 | Chapter 63: Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids | 18 | a circle with a flame above it (the oxidizer pictogram) | `#F2D584` | tag | part-4 |  |
| 47 | Chapter 64: Pyrophoric Materials | 10 | a flame rising from a mound of powder | `#FFCACB` | diamond | part-4 |  |
| 48 | Chapter 65: Pyroxylin (Cellulose Nitrate) Plastics | 9 | a film reel | `#83D0B6` | ziggurat | part-5 | cellulose nitrate was film stock. |
| 49 | Chapter 66: Unstable (Reactive) Materials | 16 | a shaking vial with zigzag motion lines | `#CE52A7` | card | part-5 | ABSTRACT (Unstable (Reactive) Materials): keep it a vial, not a bomb (Chapter 56's neighbour). |
| 50 | Chapter 67: Water-Reactive Solids and Liquids | 13 | a tap with a drop falling from it | `#5A7BE6` | arches | part-5 | close to Chapter 57 (a drop): the tap must lead; the drop is small. |
| 51 | Chapter 80: Referenced Standards | 20 | a stack of three books with a bookmark | `#798900` | drop | part-5 | ABSTRACT (Referenced Standards); not the open book of Chapter 2. |
| 52 | Appendix B: Fire-Flow Requirements for Buildings | 13 | a pressure gauge: a dial, ticks and a needle | `#91C6F7` | bitetri | part-5 |  |
| 53 | Appendix C: Fire Hydrant Locations and Distribution | 11 | a fire hydrant | `#AB242B` | cuttri | sample | DONE, sample. |
| 54 | Appendix D: Fire Apparatus Access Roads | 20 | a fire engine, side view, with its ladder | `#232425` | trefoil | part-5 | the hardest silhouette in the set: keep it to a body, cab, ladder and two wheels. |
| 55 | Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions | 3 | a three-ring binder with a hazard diamond on its cover | `#E89A3D` | castle | part-5 | ABSTRACT (HMMP and HMIS instructions): the binder is the plan. |
| 56 | Appendix I: Fire Protection Systems—Noncompliant Conditions | 9 | a warning triangle with a bar and a dot | `#FF8980` | quatre | part-5 | ABSTRACT (Noncompliant Conditions): a warning sign; no letters. |
| 57 | Exhibit B: Amendments to the International Building Code | 7 | a city high-rise with a grid of windows | `#006278` | lens | part-5 | ABSTRACT (Amendments to the IBC): not Chapter 11's old house. |
| 58 | Chapter and Section Finder | 138 | a magnifying glass | `#D2D4FF` | bardia | part-5 | ABSTRACT (Chapter and Section Finder is a lookup tool, not a chapter): the magnifier is the lookup. |

1,812 questions in all. Abstract titles (Scope and Administration, Definitions, General Requirements, Hazardous Materials -
General Provisions, Organic Peroxides, Unstable Materials, Referenced Standards, Appendix H, Appendix I, Exhibit B, Chapter and
Section Finder) are given a symbol rather than a scene: stamp, dictionary, clipboard, placard, molecule, vial, books, binder, warning
triangle, high-rise, magnifier. None uses a letter, a number or text.

## 3. How an icon sits in the badge (decided, built)

- The badge keeps its outline, its enamel, its metal rim, its slot and its back. **What changes is the face:** a chapter with an
  icon has **no channels** (`badgeFaceShapeFor` returns the outline with `cuts: []`, so the plate is one open field - a channel
  would cut across a picture) and **the icon is inlaid on the plate**.
- **Placement is automatic.** `badgeIconBox` finds the largest square that fits wholly inside the open plate (1.3 units in from its
  edge) and centres the 96-unit icon box on it, scaled so the box side is 1.12 x that square (the art is not the box: it stays inside
  the 84-unit circle). A drawer never positions or scales an icon; a drawer only fills the 96 x 96 box.
- **Lit like the rest.** The author draws flat plates. The renderer then adds, the same for every icon: a soft drop shadow down-right,
  and over the figure a lacquer light at its top-left and a little shade at its bottom-right, clipped to the figure's own pixels
  (canvas `source-atop`, no filter). So 58 icons by different hands get one light. Light is **top-left** everywhere.
- **Struck and vector.** The struck token (what the app shows) paints the icon on its canvas (`chapterIconPaintStrike`); the vector
  token (no-canvas fallback, tests) builds the same markup as SVG (`chapterIconVector`). One source: the markup returned by the icon.
- **Not yet found:** the empty slot is unchanged, and the grey (seen-not-shown) token draws the plate with no channels and **no icon**
  (the shape is a hint, the picture is the reward).
- **No icon yet = exactly the old look.** `chapterIconFor(unit)` returns null, the face is the old shape with its channels. A chapter
  added later still renders. A throwing icon function costs its icon only.
- The icon is not on the back (the back is the title). The 3D inspector, the case, the unlock card and the cutscene's coin all use
  the struck token, so they get the icon with no further work.

## 4. The palette an icon is drawn with (the argument `c`)

`c` is computed from the chapter's own enamel `p` (`chapterIconPalette`). A dark or mid enamel (luminance under .30) carries a LIGHT
figure; a pale one (ivory, frost, the pastels) a DARK figure; the roles run the same way in lightness either way, so the same icon
reads on every enamel:

| role | use | light figure (dark/mid enamel) | dark figure (pale enamel) |
|------|-----|-------------------------------|---------------------------|
| `c.lite` | the highlight: knobs, glints, windows, the brightest plate | enamel tinted 97% to white | enamel shaded 34% to black |
| `c.body` | the main plate of the object | tinted 86% | shaded 58% |
| `c.shade` | the turned-away plate (right/bottom side, inner panels, the far half) | tinted 58% | shaded 78% |
| `c.ink` | the keyline and any dark detail | shaded 78% | shaded 92% |
| `c.field` | the enamel itself: a window or cut-out showing the colour through (the flame in the drop, the ribbon) | `p` | `p` |

Use ONLY these five, by name, as `${c.body}` etc. No hex literals, no `rgb()`, no `none` except `fill="none"` on a stroke-only path,
no opacity under .5 except the one soft shadow-plate pattern in the exemplars. That is what keeps 58 icons one set.

## 5. The spec (every icon)

- A function: `CHAPTER_ICON["<exact unit name>"] = (c) => { ... return `<path .../>...`; };` returning a string of `<path>` elements.
  The key is the unit's exact title (em dash and all; copy it from section 2's table or `tools/chapter-icons/units.json`).
- **Box 96 x 96, centred on (48,48).** Every path, strokes included, inside 2..94 on both axes. Keep the figure inside the 84-unit circle
  about (48,48) where you can (a sprinkler's pipe and drops may reach 6 and 90); the figure should span at least 40 units each way
  and fill about two thirds of the box - an icon that floats small in the box is small on the badge.
- **At most 14 `<path>` elements.** Nothing else: no `<circle>`, `<rect>`, `<g>`, `<defs>`, `<style>`, `<text>`, `<image>`, `<use>`.
  A circle is `M cx-r cy a r r 0 1 0 .01 0Z` (exemplars: the hydrant's nut, the door's knob).
- **Attributes allowed:** `d fill stroke stroke-width stroke-linejoin stroke-linecap opacity fill-rule`. **Forbidden:** `id`, `transform`,
  `filter`, `style`, `class`, any `url(...)`, any gradient, any pattern, any mask or clip (the gate greps for all of it).
  Lines get a flat colour, never a gradient (a gradient on a line has a zero-width box and paints black - this app has been bitten
  three times).
- **Unique ids: there are none.** An icon has no ids, so no two icons (or two badges on one page) can clash.
- **Keyline weight:** `stroke-width="2.4"` ink round-joined round the outer edge of every plate; `1.6` for inner details; nothing
  thinner than 1.4. `stroke-linejoin="round"` and round caps (the renderer's default when omitted, but say it for strokes).
- **Corner rounding:** one rule - round joins on every stroke and radius at least 2 on any corner you draw as a curve; never a mitre.
  No sharp spikes under 20 degrees.
- **Two tones plus a highlight, and a keyline:** `body` and `shade` for plates, `lite` for the highlight, `ink` for the line. Light from
  the top-left: the left and top of an object are `body`/`lite`, its right and bottom `shade`.
- **Legible at 26px:** the figure is judged on the contact sheet's 26px badge (and the 96px one). Smallest feature 4 units (a 1.5px
  feature at 26px does not exist); detail that is lost at 26px must not be what makes it recognisable. The silhouette has to say
  the object by itself; avoid anything that needs the interior (keyline) to be read.
- **Distinct:** no two icons may overlap more than 85% as 48px silhouettes (the gate computes it), and think about the 26px blob: two
  upright rectangles with a dot are the same icon.
- **No letters, numbers or text** (rank of risk: an `A` that is a path is still a letter). No people.
- **Do not reproduce a trademark or a brand mark.** Generic objects only.
- Arithmetic in the function is fine (the airliner turns its points in code; the sprinkler's `drop()` is a helper): JS in the body,
  but the returned string must obey all of the above.

## 6. Do and don't (the six exemplars are in `tools/chapter-icons/part-0-samples.js`)

DO
- Start from the exemplar nearest your object: **door** (a frame, an opening, a shaded leaf with inset panels - perspective by a
  trapezoid), **sprinkler** (a vertical object built from stacked plates plus a spray of small repeated drops via a helper),
  **drop and flame** (one big bold silhouette, a shaded crescent for volume, a `c.field` window, a `c.lite` glint),
  **book** (a symbol for an abstract title; strokes in `c.shade` for text lines), **hydrant** (a symmetric object, plates left and right,
  collars as bars, a bold round boss), **airliner** (a silhouette computed in code, left half `shade`, right half `body`).
- Draw the big shape first (it carries 26px), then the shade plate, then the highlight, then the small details last.
- Make the object's most recognisable feature the biggest thing in the picture.
- Look at your icon on a contact sheet (section 8) on a dark enamel AND a pale one before you stop.

DON'T
- Don't use a figure that is a thin outline only: the plates carry it, the keyline only separates them.
- Don't draw a scene (a door and a room and an exit sign): one object.
- Don't put the object's detail where the box edge is - the plate is smaller than the box at the corners.
- Don't use `c.lite` for large areas on a light figure: `lite` is nearly white and glares; `body` is the big plate.
- Don't put a dark `c.ink` plate on a dark enamel or a lite plate on a pale one expecting contrast: roles flip with the enamel on
  purpose; look at both.
- Don't edit `index.html`, any other part file, `IFC_BADGE_SHAPE` or any enamel. Don't rename a unit.

## 7. Phase 2: the split

Five helpers, one file each, no shared files, so no conflicts. The icons already done (part-0) are not touched. Each helper:
creates `tools/chapter-icons/part-N.js` containing ONLY `CHAPTER_ICON["..."] = ...;` statements for its chapters (a header comment
is fine), nothing else.

| file | chapters (the chapters' own numbers - what `--only` takes; the # column in section 2 is only a row count) | count |
|------|------------------------------------|-------|
| part-1.js | 1, 3, 4, 5, 6, 7, 8, 11, 12, 21 | 10 |
| part-2.js | 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33 | 12 |
| part-3.js | 34, 35, 36, 37, 38, 39, 40, 50, 51, 53 | 10 |
| part-4.js | 54, 55, 56, 58, 59, 60, 61, 62, 63, 64 | 10 |
| part-5.js | 65, 66, 67, 80, Appendix B, Appendix D, Appendix H, Appendix I, Exhibit B, Chapter and Section Finder | 10 |

(The Chapter column in section 2 is the exact key.) A helper may change a concept if its drawing cannot be
made to read - write why in a comment above the icon and in the hand-off, and pick something else nameable from the title.

### Working loop (never touches index.html)

```
python3 tools/merge-chapter-icons.py --out /tmp/<you>/index.html     # the page with every part file merged, index.html untouched
python3 tools/render-chapter-badges.py /tmp/<you>/sheet.png --index /tmp/<you>/index.html --only 1,3,4,5 --cols 4
python3 tools/render-chapter-badges.py /tmp/<you>/big.png   --index /tmp/<you>/index.html --only 1,3 --cols 3 --px 190
```
`--only` takes chapter numbers (or title prefixes: `--only "Appendix B"`). The sheet shows, per chapter, the badge earned and as its
empty slot at 96px and 26px with the title under it. Use `--shape coin` to see an icon on a roomy outline when the outline you were
given is the problem. Chromium is `/opt/pw-browsers`; the Firebase CDN being blocked changes nothing. Under load a page can crash at
start: the tool retries; run it again.

### Checklist (every icon, before hand-off - tick each in the hand-off message)

1. The key is the exact unit title; the merge accepts it (the merge refuses a key that is not one of the 58 and a key drawn twice).
2. `<path>` elements only, at most 14; only the allowed attributes; no id, filter, gradient, `url(`, transform, style.
3. Colours only `${c.field|lite|body|shade|ink}`.
4. Inside the 96 box (2..94), spans at least 40 units each way, fills about two thirds of it.
5. Reads at 26px: look at the sheet's 26px badge and say what it is without the label.
6. Reads on a dark enamel and a pale one (check the two ends of your own chapters; the sheet shows each in its own colour).
7. Distinct from every other icon in the set (look at section 2: the neighbours are named in the notes where two are close).
8. Top-left light: highlights top/left, shade right/bottom.
9. No letters, numbers, text, people, trademarks.
10. `python3 tools/check-b384-chapterbadges.py` is green on a scratch merge (section 8).

### Integration (one person, after the five files land)

```
python3 tools/merge-chapter-icons.py          # writes index.html between the two markers
python3 tools/check-b384-chapterbadges.py     # all 58 icons: spec, distinct, ids, academy and no-icon chapters unchanged
python3 tools/render-chapter-badges.py sheet.png --phone phone.png --ipad ipad.png --earned all
```
Then the gates in `CLAUDE.md` (check-js, load and read the console, check-behaviour badge sections, sweep --quick, check-b384-ifcbadges,
check-b384-badgetwins - see section 9 on why that one needs a decision), and a version bump.

## 8. The tools

- `tools/render-chapter-badges.py OUT.png` - the contact sheet: every Fire Code badge, earned and empty, at 96px and 26px, light on
  dark, title under each, `ICON` / `fallback` per chapter. Also `--phone OUT.png` / `--ipad OUT.png` (Profile > Badges at 440x956 and
  834x1194, with `--earned samples|all|none|10,12`), `--px N` (bigger badges), `--shape KEY` (what-if outline), `--index FILE`.
- `tools/merge-chapter-icons.py` - part files -> index.html (`--check`, `--out FILE`).
- `tools/check-b384-chapterbadges.py` - the gate (fails on origin/main).

## 9. Open decisions for the owner (why phase 1 stops here)

1. **Outlines.** Icons need room, and 17 of the 58 outlines give them under 30 units of a 100 frame. Options:
   (a) keep the 58 distinct outlines as they are and accept small icons on the narrow ones (honest, safest, weakest);
   (b) re-deal the outlines so the chapters whose pictures are busiest get the roomy ones (costs the back titles' size: the roomy outlines
       are on the longest titles on purpose; a re-deal needs the backs re-fitted and `check-b384-ifcbadges` section 3/4 re-run);
   (c) since the icon now tells the chapters apart, let a small family of ~8 roomy outlines (coin, shield, disc, gate, octagon,
       hex, keystone, castle...) be shared, with the colour and the picture as the identity. This is the look the phone/iPad
       screenshots in phase 1 approximate; it **retires the "no two outlines alike" rule** (`check-b384-badgetwins` outlines section)
       for Fire Code, so it must be the owner's call, not a drawing helper's;
   (d) the outline itself is the object (a door-shaped badge), which is the boldest look and a rebuild of the outline and back system.
2. **The Egress door.** The owner's example is on the `gate` outline in phase 1 (it was the bolt). Keep, or give it a different roomy one.
3. **Chapter 9.** Sprinkler (drawn) or fire-alarm bell for Fire Protection and Life Safety Systems.
4. Whether a found badge's icon should also appear on the unit card / results (it already does: every place uses the struck token).

## 10. What phase 2 decided (384.63)
All 58 icons are drawn (part-1 .. part-5). Section 9 point 1 was taken as option (b), re-dealing outlines for room with NO two chapters sharing an outline: 17 chapters changed outline (docs/notes-archive.md, "384.63"), the C-ring and the tau are no longer used, and the octagon is not used because it is the coin to the pixel. The twins gate is loosened for five named gate/hex pairs at the 2px band only. The renderer keeps only the first 14 paths of an icon: the gate counts the raw markup and fails above 14. A one-arc circle (`M x y a r r 0 1 0 .01 0Z`) is right only from the circle's TOP and only for a small r: draw a larger one as two half arcs (the gate fails r over 12).
