# Fire Code chapter badges: the badge IS the object (build 384.65)

Owner, shown 384.63 (a picture inside a generic outline): "those badges aren't what I had in mind, you just put stuff in the badge.. the
badge needs to be the actual thing. I know I've said in the past not to do that, but now we will." Original brief: "Badges are gonna be
designed based on what the chapter is about / the title (mostly the title). For example Means of Egress could be a door in the open
position? Make them cool."

So for Fire Code's 58 chapters the badge's **silhouette is the object**: Means of Egress is cut to the outline of an open door. This
deliberately reverses the older rule ("a badge that draws its subject was rejected twice") for these chapters only; the academy's badges
are untouched. A chapter with no entry here still draws its 384.63 picture-in-an-outline, so the app never breaks mid-migration.

## 1. The recipe, in plain words

The badge keeps the app's whole badge language and changes one thing: where the outline comes from, and what colours the enamel.

- the **outline is the object's silhouette** (one closed path, rounded corners, in the 100 x 100 frame every outline uses);
- a dark **keyline** outside it and a polished silver **rim** following it (6.4 units wide inside the outline, 4.5 out), exactly as on every
  other badge; the enamel is lit from the top-left, domed, with a clear coat; nothing is added to the rim code;
- the enamel is not one colour but a small set of flat **plates** laid in the face before it is lit: each a tone of the chapter's own
  enamel (its door leaf, its frame...), each with a thin dark edge, optionally a soft shadow cast on what is beneath. Parts of the
  object may be different colours, but the palette stays the chapter's own family plus three non-family colours (light, metal, flame);
- the **empty slot** is cut to the object's own outline (lit from the top-left, as ever), so an empty slot still tells you the shape;
- a **grey** (seen, not yet found) token is the plain silhouette in grey with no plates: the picture is the reward;
- the **back** (title and FIRE CODE) is laid out on the silhouette like on any outline;
- nothing is a filter, a gradient on a line, or an id: the struck token reads the plates off a colour map the renderer paints, the
  vector token (no-canvas fallback, tests) draws the same plates as SVG paths; both go through `buildUnitBadgeSVG`, so the case, the
  Profile tab, the unit card, the cutscene's coin, the badge pill, the results row and the badge in your hand all show it.

## 2. What you write (one block per chapter, in your own part file)

`tools/chapter-objects/part-N.js` holds only blocks of this shape (a `{ ... }` block per chapter keeps your helper `const`s private):

```js
{
  CHAPTER_OBJ["Chapter 10: Means of Egress"] = {
    d: OBJ_poly([[16, 12], [52, 2], [52, 12], [90, 12], [90, 88], [52, 88], [52, 98], [16, 88]], [3, 2, 1, 3, 3, 1, 2, 3]),   // the silhouette
    base: "field",     // optional: the colour of the silhouette under the plates (default field = the enamel; "steel" for a thing of metal)
    c: [50, 50],       // optional: the point the badge is scaled about (default: the middle of the silhouette's box)
    plates: [          // painted in order over the base; at most 24
      ["deep", OBJ_rrect(16, 12, 74, 76, 3), { e: 0 }],        // [role, path, options?]
      ["glow", OBJ_rrect(24, 20, 58, 68, 1)],
      ["body", leafPath, { sh: 1, e: 1.6 }],                   // sh: casts a soft shadow down-right on what is under it
      ["ink",  "M30 40V60", { ln: 3 }],                        // ln: w - the path is a stroked line, width w, round caps, in the role's colour
    ],
  };
}
```

The key is the unit's **exact title** (`tools/chapter-icons/units.json`; em dash and all). Merge, render, gate:

```
python3 tools/merge-chapter-icons.py --out /tmp/<you>/index.html          # your part files merged into a scratch page (index.html untouched)
python3 tools/render-chapter-badges.py /tmp/<you>/sheet.png --index /tmp/<you>/index.html --only 10,9 --cols 2 --px 200
python3 tools/merge-chapter-icons.py                                       # (integration only) write index.html
python3 tools/check-b384-objbadges.py                                      # the gate
```
`--only` takes chapter numbers or title prefixes ("Appendix D"). The sheet shows earned and empty at 96px and 26px (`--px 200` for a big
look) on the real dark card. The merge refuses a key that is not one of the 58, a key drawn twice, a path the measurer cannot walk, and a
file with code the page cannot run; it measures every silhouette under node and writes the boxes into index.html (so the page never
forces a layout to measure a badge).

### Roles (the colour of a plate)
| role | what it is | use it for |
|---|---|---|
| `field` | the chapter's enamel itself | the base; a window onto the colour |
| `body` | the enamel lifted | the object's main lit plate |
| `shade` | the enamel darkened | the turned-away side (right / bottom), panels |
| `deep` | much darker | frames, undersides, bases |
| `lite` | much lighter | highlights, glass, panels catching the light |
| `ink` | nearly black in the chapter's hue | dark openings, hollows, hose |
| `glow` | warm white (the same on every chapter) | light, a window, the lit way out |
| `steel` | cool silver | metal parts, hubs, a ladder |
| `hot` | amber (the same on every chapter) | a flame's warmth, brass, a label band |

The ladder is moved up for a dark enamel (onyx, a deep green) and its top is lower for a pale one, so every role stays distinguishable on
every enamel; look at your chapter on its own enamel, and put it on a dark and a pale one with `--shape`-style what-ifs if in doubt. Use
only these nine, by name; there are no hex colours, no opacity, no gradients.

### Helpers (defined in index.html; available to every part file)
`OBJ_poly(points, r)` a polygon, every corner rounded by a quadratic through the vertex (r a number or one per vertex; 0 keeps a corner);
`OBJ_rrect(x, y, w, h, r)` a rounded rectangle (r a number or [tl, tr, br, bl]); `OBJ_circle(cx, cy, r)` and `OBJ_ellipse(cx, cy, rx, ry)`
(two half arcs); `OBJ_chain(points, r)` an open run of rounded corners, "L .. Q .." (start the path with "M" + the first point, join runs with
arcs: `"M10 72" + OBJ_chain([...]) + "A12 12 0 0 1 62 71" + OBJ_chain([...]) + "Z"`). Arithmetic and local helper functions are fine (the
helmet's and magnifier's geometry is computed); keep the strings to the commands below.

## 3. Rules and pitfalls (each one cost a prototype)

1. **One silhouette path**: exactly one `M` and one `Z`, commands `M L H V C Q A Z` only (absolute). Overlapping subpaths are NOT a union
   here (the rim is stroked along every subpath, and each interior edge would carve a groove): trace the union outline by hand with
   `OBJ_poly` / `OBJ_chain`. **No holes**: a see-through gap (a handle loop, the space between a ladder's rails) is drawn as a plate
   (`ink` for a dark gap, `lite` for glass), not cut out. A hole would need its winding opposite to the outline's (nonzero fill) and the
   rim code has never been run on one.
2. **The rim eats detail.** The rim is 6.4 inside plus 6.5 of keyline outside, uniform, and its outer edge rounds every convex corner by
   about 11. So: a part of the object narrower than about 16 units has **no enamel**: it comes out as bare silver, which is the right look
   for a handle, an arm, a hose or a ladder rail; a **gap narrower than ~20 units closes up** (the keylines of both sides meet); steps of
   under ~10 units melt into a bump (a stepped skyscraper became a baby bottle). Draw big: the longest side 80+ of 100, the key feature the
   biggest thing, concave notches and big silhouette steps rather than fine corners. The gate holds the box and the enamel share.
3. **Round corners** on every vertex (radius at least 2; a sharp spike under 20 degrees is a defect). The rim rounds anything you leave sharp.
4. **Circles are two half arcs.** A one-arc circle (`M x y a r r 0 1 0 .01 0Z`) puts the circle in the wrong place unless it starts exactly at
   its top, and only for a small r; `OBJ_circle` is always right. The gate fails a single-arc circle over r 12.
5. **No gradients and no line gradients** (a gradient on a line has a zero-width box and paints black: this app has been bitten three times):
   plates are flat; light comes from the renderer (top-left light, a lacquer, a shadow under a raised plate with `sh`). Build a shine by
   stacking two flat plates (a lighter crescent over the body), not a gradient. A path in a plate may not carry `url(`, an id, a filter or a
   transform: the gate greps for all of it.
6. **At most 24 plates.** The renderer keeps the first 24 and drops the rest in silence, so the gate counts the raw list and fails above.
   Repeats (windows, rungs, ribs) are one plate: a `ln` path of many subpaths (`M x y V y2 M x2 y V y2 ...`, or `M x y h.01 M ...` for dots).
7. **Parts of the object may be different colours** (door leaf, frame, light, handle) but the object stays in its chapter's family: mostly
   `body` / `shade` / `deep` / `lite`, with `glow`, `steel`, `hot` for light, metal and flame. The gate checks the token's hue is within 60
   degrees of the enamel's. Fifty-eight chapters, 58 enamels: never reuse another chapter's accent as your main colour.
8. **Light from the top-left**: highlights up and left, shade down and right; a raised plate gets `{ sh: 1 }`.
9. **No text, numbers, letters or people**, no trademark or brand mark: generic objects. Official, not cute: a skull is the toxic pictogram,
   not a cartoon; a leaf is a plain leaf.
10. **The back must still hold the title**: the silhouette has to be wide enough somewhere for the chapter's name (the gate reads the back's
    plan off the app; the long names, Appendix H and Chapter 28, want a roomy silhouette).
11. **Distinct from every other chapter's shape at 48px** (overlap under 0.85): two upright rounded boxes are the same badge whatever is inside.
12. **Legible at 26px**: the silhouette must say the object by itself; the plates are a bonus at that size. Look at the sheet's 26px badge and say
    what it is without the label.

## 4. Checklist (every chapter, before hand-off)

1. The key is the exact unit title; the merge accepts it.
2. One `d`: one M, one Z, M L H V C Q A Z only; rounded corners; no holes; the box 80+ of 100 one way, area 2000+, not a plain box.
3. Plates: at most 24, roles from the nine, options `sh` / `e` / `ln` only, no markup in any path.
4. No single-arc circle over r 12 (use `OBJ_circle`).
5. Reads at 26px as the object: looked at on the sheet, said aloud without the label.
6. Reads on its own enamel, dark and pale; in its chapter's colour family.
7. The silhouette differs from every other chapter's (look at the whole sheet, not only your twelve).
8. Light top-left; raised plates cast a shadow; no gradient, no opacity, no hex.
9. No letters, numbers, text, people, trademarks.
10. `python3 tools/merge-chapter-icons.py --out /tmp/<you>/index.html`, then `python3 tools/check-b384-objbadges.py --index /tmp/<you>/index.html`
    is green (the gate's merge-in-step check is skipped on a scratch page).

## 5. The eight prototypes (tools/chapter-objects/part-0-prototypes.js)

Means of Egress (an open door, the leaf swung toward you, the doorway lit), Chapter 9 (a pendant sprinkler on its supply pipe, spraying: a device, the hardest silhouette
because its real parts are thin; drawn solid with the arms and bulb as plates, the pipe across the top and the spray cone as the bold parts), Chapter 57 (a safety can with a flame on its face: a hazardous-material container), Appendix D (a ladder truck: the wide,
low silhouette), Chapter 53 (a gas cylinder with its valve wheel: the tall, narrow one), Chapter 1 (a rubber hand stamp: an idea drawn as
the thing that makes it official), Chapter and Section Finder (a magnifying glass: a lookup drawn as the tool), Chapter 5 (a fire helmet).
Copy the nearest one.
