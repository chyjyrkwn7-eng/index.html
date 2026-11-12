# Fire Code chapter badges: the badge IS the object (build 384.65)

Owner, shown 384.63 (a picture inside a generic outline): "those badges aren't what I had in mind, you just put stuff in the badge.. the
badge needs to be the actual thing. I know I've said in the past not to do that, but now we will." Original brief: "Badges are gonna be
designed based on what the chapter is about / the title (mostly the title). For example Means of Egress could be a door in the open
position? Make them cool."

Shown the first eight objects (round 1): "Some potential. It's hard to tell what some of them are ... I feel like you are just throwing
stickers in the middle of the badges. Look at the magnifying glass, it's probably the best one, because the majority of it still has that
nice badge look, and the silver border is perfectly even and looks good. But the sprinkler: you are using the silver part to make the
actual design." That is round 2's brief, and it is the first two rules below.

So for Fire Code's 58 chapters the badge's **silhouette is the object**: Means of Egress is cut to the outline of an open door. This
deliberately reverses the older rule ("a badge that draws its subject was rejected twice") for these chapters only; the academy's badges
are untouched. A chapter with no entry here still draws its 384.63 picture-in-an-outline, so the app never breaks mid-migration.

## 0. The five rules (the gate holds the mechanical ones)

1. **The silver rim is a perfectly even border, all the way round the silhouette (and round every hole), and it is NEVER the object.**
   Round 1's pipe, arms and deflector, a can's spout and handle, were drawn by the rim: that is the failure. The magnifier is the benchmark
   (fat ring, fat handle, an even rim, a lens of enamel).
2. **Every part of the object must be wide enough to hold its own rim AND its own enamel: MIN_PART.** Measured from the renderer
   (`BADGE_GEOM`): the rim eats **6.4 units inside the outline** (4.4 silver + a 2.0 dark edge before the enamel starts) and shows 4.5 of
   metal and 6.5 of keyline outside it. A part W wide therefore shows W - 12.8 of enamel, and under about 16 none at all (the renderer drops
   enamel under 3 wide). **MIN_PART = 18 across is the floor the gate fails on; aim for 22 or more (about 3.4 x the 6.4 rim: 9+ of
   enamel). Gaps between parts: at least 20** (two keylines meet under 13); **holes: at least 22 across** (the rim lines the hole's edge
   too). Exaggerate and simplify: chunky, cartoon-bold, like the magnifier. Drop any detail thinner than this rather than letting the rim
   swallow it. (A small junction, like a short neck between two big parts, may be thinner than 18: the gate allows 5.5% of the
   silhouette's area under the floor, which is what rounded corners and pointed tips cost.)
3. **No stickers: identity comes from the SILHOUETTE** (what the outline says), never from a small picture laid in the middle. Interior
   plates are only colour-blocking / shading of the object's own parts (leaf vs frame, lid vs body, a stripe along a truck), never a symbol
   (a flame on a can, a pocket badge on a helmet, a lit rectangle for a doorway). If a flame is needed the object must BE flame-shaped or the
   flame is dropped. Mechanically the gate fails an accent plate (`glow`, `steel`, `hot`) that floats inside a part instead of reaching the
   object's edge (a spout's cap, a stripe, a tip); whether a block is a sticker is finally a judgement: look at the sheet.
4. **Identifiable in two seconds with no label, at 96px and at 26px.** If the silhouette alone does not say the object, change the object or
   the view; do not add detail.
5. **Colour stays the chapter's own family** plus `glow` / `hot` for light and flame; `steel` reads as silver and tempts the rim-as-design
   failure: use it for nothing round 2 needs.

## 1. The recipe, in plain words

The badge keeps the app's whole badge language and changes one thing: where the outline comes from, and what colours the enamel.

- the **outline is the object's silhouette** (one closed rounded path in the 100 x 100 frame every outline uses, plus optional holes);
- a dark **keyline** outside it and a polished silver **rim** following it, exactly as on every other badge; the enamel is lit from the
  top-left, domed, with a clear coat; nothing is added to the rim code;
- the enamel is not one colour but a small set of flat **plates**, each a tone of the chapter's own enamel, each with a thin dark edge,
  optionally casting a soft shadow down-right;
- the **empty slot** is cut to the object's own outline (lit from the top-left), so an empty slot still tells you the shape;
- a **grey** (seen, not yet found) token is the plain silhouette in grey with no plates;
- the **back** (title, and FIRE CODE where it fits) is laid out on the silhouette like on any outline;
- nothing is a filter, a gradient on a line, or an id: the struck token reads the plates off a colour map the renderer paints, the vector
  token (the no-canvas fallback, tests) draws the same plates as SVG paths; both go through `buildUnitBadgeSVG`, so the case, Profile >
  Badges, the unit card, the cutscene's coin, the badge pill, the results row and the badge in your hand all show it.

## 2. What you write (one block per chapter, in your own part file)

`tools/chapter-objects/part-N.js` holds only blocks of this shape (a `{ ... }` block per chapter keeps your helper `const`s private):

```js
{
  CHAPTER_OBJ["Chapter 10: Means of Egress"] = {
    d: OBJ_poly([[12, 16], [42, 4], [42, 8], [94, 8], [94, 94], [74, 94], [74, 28], [42, 28], [42, 96], [12, 84]], [4, 3, 2, 5, 5, 4, 3, 3, 3, 4]),   // the silhouette
    holes: [ OBJ_rrect(30, 30, 24, 24, 4) ],   // optional: closed paths cut out of it (any way round); at least 22 across
    c: [50, 50],       // optional: the point the badge is scaled about (default: the middle of the silhouette's box)
    base: "field",     // optional: the colour of the silhouette under the plates (default field = the enamel)
    plates: [          // painted in order over the base; at most 24
      ["deep", OBJ_rrect(42, 8, 52, 20, 2), { e: 0 }],         // [role, path, options?]
      ["body", leafPath, { sh: 1, e: 1.6 }],                   // sh: casts a soft shadow down-right on what is under it
      ["deep", "M54 14V34M66 14V34", { ln: 2 }],               // ln: w - the path is a stroked line, width w, round caps, in the role's colour
    ],
  };
}
```

The key is the unit's **exact title** (`tools/chapter-icons/units.json`; em dash and all). Merge, render, gate:

```
python3 tools/merge-chapter-icons.py --out /tmp/<you>/index.html          # your part files merged into a scratch page (index.html untouched)
python3 tools/render-chapter-badges.py /tmp/<you>/sheet.png --index /tmp/<you>/index.html --only 10,9 --cols 2 --px 200
python3 tools/check-b384-objbadges.py --index /tmp/<you>/index.html        # the gate on the scratch page
python3 tools/merge-chapter-icons.py                                       # (integration only) write index.html
```
`--only` takes chapter numbers or title prefixes ("Appendix D"). The sheet shows earned and empty at 96px and 26px (`--px 200` for a big
look) on the real dark card. The merge refuses a key that is not one of the 58, a key drawn twice, a path the measurer cannot walk, and a
file with code the page cannot run; it measures every silhouette under node and writes the boxes into index.html.

### Holes
`holes: [path, ...]`: a handle's loop, a window, a ring's middle. Draw each any way round (the loader winds it opposite to the outline
and lays it in as a dense polyline); the rim lines its edge exactly as evenly as the outline's (4.5 of metal and the keyline inside the
hole), so the see-through part is the hole shrunk by about 13 each way: **a hole under ~22 across plugs**, and one barely bigger shows
as a dark slot. Plates are clipped to the silhouette, holes excluded. Try it before you rely on it: the first doorway drawn as a hole
read as a letter O.

### Roles (the colour of a plate)
| role | what it is | use it for |
|---|---|---|
| `field` | the chapter's enamel itself | the base |
| `body` | the enamel lifted | the object's main lit plate |
| `shade` | the enamel darkened | the turned-away side (right / bottom), panels |
| `deep` | much darker | frames, undersides, bases, a dark gap |
| `lite` | much lighter | highlights, glass, a panel catching the light |
| `ink` | nearly black in the chapter's hue | dark openings |
| `glow` | warm white (the same on every chapter) | light |
| `steel` | cool silver | (avoid: it reads as the rim) |
| `hot` | amber (the same on every chapter) | a stripe, a cap, a flame's warmth where it is part of the edge |

The ladder is moved up for a dark enamel (onyx) and its top is lower for a pale one, so every role stays distinguishable on every enamel;
look at your chapter on its own enamel. Use only these nine, by name; no hex colours, no opacity, no gradients.

### Helpers (defined in index.html; available to every part file)
`OBJ_poly(points, r)` a polygon, every corner rounded by a quadratic through the vertex (r a number or one per vertex; 0 keeps a corner);
`OBJ_rrect(x, y, w, h, r)` a rounded rectangle (r a number or [tl, tr, br, bl]); `OBJ_circle(cx, cy, r)` and `OBJ_ellipse(cx, cy, rx, ry)`
(two half arcs); `OBJ_chain(points, r)` an open run of rounded corners, "L .. Q .." (start the path with "M" + the first point, join runs with
arcs: `"M20 78" + OBJ_chain([...]) + "A13 13 0 0 1 60 78" + OBJ_chain([...]) + "Z"`); `OBJ_walk(d)` a path's points. Arithmetic and local helper
functions are fine (the magnifier's geometry, the gas can's spout and the hydrant's arcs are computed); keep the strings to the commands below.

## 3. More pitfalls (each one cost a drawing)

1. **One silhouette path**: exactly one `M` and one `Z` in `d`, commands `M L H V C Q A Z` only (absolute). Overlapping subpaths are NOT a union
   (the rim is stroked along every subpath, and each interior edge would carve a groove): trace the union outline by hand with `OBJ_poly` /
   `OBJ_chain`. A see-through is `holes`, not a second subpath in `d`.
2. **The rim rounds every convex corner** (about 11 across) and closes gaps: steps under ~10 melt into a bump (a stepped skyscraper became a
   baby bottle, twice); a notch under ~20 wide closes up. Put the identity in the big silhouette features (a spout, an overhang, a hump, a flare).
3. **Smooth tapers read as pawns and flasks.** A stack of widening parts (a sprinkler's stub, body, frame, deflector) reads as a chess piece,
   a bell or a flask however it is coloured; a silhouette needs a feature no other object has.
4. **Round corners** on every vertex (radius at least 2); the rim rounds anything you leave sharp. Circles are two half arcs: a one-arc circle
   puts the circle in the wrong place (the gate fails one over r 12); `OBJ_circle` is always right.
5. **No gradients and no line gradients** (a gradient on a line has a zero-width box and paints black: this app has been bitten three times):
   plates are flat; light comes from the renderer. Stack two flat plates for a shine. A plate path may not carry `url(`, an id, a filter or a
   transform: the gate greps for all of it.
6. **At most 24 plates** (the renderer drops the rest in silence, so the gate counts the raw list). A plate whose role is not one of the nine
   is dropped silently: the gate fails it. Repeats (rungs, ribs) are one plate: a `ln` path of many subpaths.
7. **A plate outside the silhouette is clipped; one over the rim is hidden by it.** The colour you see is only inside the rim (6.4 in): draw a
   part's plate to its full outline and let the rim cover its edge.
8. **Light from the top-left**: highlights up and left, shade down and right; a raised plate gets `{ sh: 1 }`.
9. **No text, numbers, letters or people**, no trademark or brand mark. Official, not cute.
10. **The back must still hold the title**: the gate reads the back's plan off the app (the floor is 0.026 of the frame; FIRE CODE drops off
    a back that has no room for it, as designed). Long names (Appendix H, Chapter 28) want a roomy silhouette.
11. **Distinct from every other chapter's shape at 48px** (overlap under 0.85): two upright rounded boxes are the same badge whatever is inside.

## 4. Checklist (every chapter, before hand-off)

1. The key is the exact unit title; the merge accepts it.
2. One `d` (one M, one Z, M L H V C Q A Z only), rounded corners, the box 80+ of 100 one way, area 2000+, not a plain box.
3. Every part at least 18 across (aim 22+), every gap at least 20, every hole at least 22; the gate's MIN_PART and enamel checks are green.
4. The rim is the border and nothing else: no part of the object is bare silver.
5. No stickers: every plate colour-blocks one of the object's own parts; no `glow` / `steel` / `hot` plate floating inside a part.
6. Plates: at most 24, roles from the nine, options `sh` / `e` / `ln` only, no markup in any path, no single-arc circle over r 12.
7. Identifiable in two seconds with no label at 96px AND at 26px: look at the sheet and say what it is aloud.
8. Reads on its own enamel (dark and pale ones especially) and stays in its chapter's colour family.
9. Different from every other chapter's silhouette (look at the whole sheet, not only your twelve).
10. Light top-left; raised plates cast a shadow; no gradient, no opacity, no hex.
11. No letters, numbers, text, people, trademarks.
12. `python3 tools/check-b384-objbadges.py --index /tmp/<you>/index.html` is green (the merge-in-step check is skipped on a scratch page).

## 5. The eight prototypes (tools/chapter-objects/part-0-prototypes.js, round 2)

Means of Egress (an open door: a leaf swung toward you beside a lintel-and-post frame, the doorway an open notch), Chapter 9 (a sprinkler
spraying: pipe stub, hex body, flat deflector, three bold drops that are part of the outline; the weakest, still), Chapter 57 (a gas can: the
handle hump, the long angled spout and its cap), Appendix D (a ladder truck: low cab, tall body, one fat ladder bar, two big wheels; the
widest and lowest), Chapter 53 (a gas cylinder: a fat valve, a domed shoulder; the tallest and narrowest), Chapter 1 (a rubber hand stamp),
Chapter and Section Finder (a magnifying glass: the benchmark), Chapter 5 (a fire hydrant: Madison's own suggestion, after a helmet read as a
hat; Appendix C, Fire Hydrant Locations, will need a different object). Copy the nearest one.
