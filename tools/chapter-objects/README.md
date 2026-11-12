# Fire Code chapter badges: each badge is a raised PIN of the chapter's object (build 384.66, round 3)

How we got here, in the owner's words:
- 384.63 put a picture inside a generic outline: "those badges aren't what I had in mind, you just put stuff in the badge.. the badge needs
  to be the actual thing. I know I've said in the past not to do that, but now we will." (The silhouette IS the object. This reverses,
  for Fire Code's 58 chapters only, the older rule that a badge never draws its subject; the academy's badges are untouched.)
- Round 1 (be5d880): "I feel like you are just throwing stickers in the middle of the badges ... you are using the silver part to make the
  actual design." Round 2 (4273698) made every part enamel inside an even silver rim.
- Round 2: "the badges don't look good ... We can keep the back of the badges the same look and everything. But the front and side/edges
  I think we are gonna have to update for the ifc. We may just have to go away with the silver border entirely or make it thin. I sent some
  examples, the mostly grey ones I'm showing because you can see how these badges have risen effect, that nice 3d effect. And then the other
  you can see that it's 3d, color ... Make it super nice though. Make this great." (His references: the Kanto gym badges 3D-printed in grey -
  a drop, a heart split by a crease, a gem with chamfered facets, a button with a raised disc, a flower of domed petals, a leaf with cut
  veins - and the same as coloured enamel pins.)

So a chapter drawn as its object is now a **raised pin**: no silver rim, a sculpted face, a visible side wall, a contact shadow. The back
(the struck back with the engraved title) is unchanged. A chapter with no entry here still draws its 384.63 picture-in-an-outline.

## 0. The rules

1. **The badge is the object, as a raised 3D pin.** No rim. Edge A (the default): a fine darker line of the object's own colour where the
   face turns down into its wall. Edge B (Madison to choose): a hairline of polished metal, `OBJ_PIN.hair` = 1.8 units of 100. Switch with
   `setChapterObjEdge("A" | "B")`.
2. **Identity is the silhouette plus the sculpture** (raised and recessed parts, domes, facets, grooves), never a flat picture printed on the
   face. A raised, domed, faceted or cut part is sculpture; a FLAT painted plate floating inside a part is a sticker and the gate fails it.
3. **It must read in plain grey.** Render every pin with no colour (the relief sheet, the 3D-printed reference): if it does not read as the
   object, the sculpture is not doing its job. The gate measures it (the face's luminance varies inside the bevel).
4. **Colour: each part its natural colour, saturated**, the chapter's own enamel the dominant one (58 distinct): `field`/`body`/`shade`/
   `deep`/`lite`/`ink` are the chapter's family; `brass`, `red`, `water`, `glass`, `rubber`, `cream`, `wood`, `steel`, `hot`, `glow` are natural
   colours, the same on every chapter. The token's mean hue stays within 60 degrees of the chapter's enamel (gated).
5. **MIN_PART (re-measured for pins): a part at least 5 across** (two bevels of 2.4: narrower and it is all slope, no top); aim for 8+ where
   it must read at the case's 44px. **Holes at least 5 across** (the wall and shadow show inside a hole; 8+ to see through at 44px). Gaps:
   at least 4 (the side wall is 3 deep down-right). The gate fails a silhouette that loses more than 3% of its area to a 2.4 disc opening.
6. **Recognisable in two seconds, no label, at 96px, at the case's 44px and at 26px.** The sheet shows all four.

## 1. The recipe, in plain words (index.html: objPinGeometry, renderObjPin, buildObjPinSVG)

- A **height map** at `OBJ_PIN.geoW` (320) across the badge's frame, once per chapter: the silhouette rises from the case by a rounded
  **bevel** (`bevel` 2.4 units wide, a quarter-sine) to a top (`top` 1.7) with a gentle dome (`domeK` .9 over `domeR` 18 units in); each part
  adds its relief, read off **its own distance field**: `z` raises or recesses it with its own bevel `bev`, `dome` domes it (by its inner
  radius), `gem` cuts it into **planar facets** (a linear ramp over `gw` from its edge - a straight edge gives a true plane, a corner a crease),
  `cut` sinks a **V-groove** (usually a line: `ln`).
- **Normals** from the height map; one light, top-left as everywhere in the app: Lambert (ambient `amb` .3) plus a restrained specular
  (`spec` .32, `specP` 52) and a faint sheen; each pixel's colour from the parts' colour map (`chapterObjColourMap`), in linear light.
- The **side wall**: the pin's thickness (`wall` 3 units deep, along `wallDir` - down-right), each point the colour of the face above it,
  darker (`wallK` .6 at the top to .32 at the foot). A **contact shadow** under it (offset `shadow`, softened `shadowBlur`, `shadowA` .55).
- **Edge A**: the outer `outline` .55 units of the face darkened to `outlineK` .5 of its colour. **Edge B**: the outer `hair` 1.8 units in
  polished metal (brighter specular).
- Supersampled (3x under 180px, else 2x), cached per badge, size and state in the strike cache with the same draft-then-finish path the
  struck tokens use. No SVG filter anywhere. The empty slot is the recess cut to the object's own outline (a narrow clearance, `slotGap`
  2.2, since a pin has no rim to clear). The grey (seen, not found) token is the pin rendered in plain grey. With no canvas, the parts are
  drawn flat with a darker wall and a fine edge. The coin's edge slices for a pin are its own outline in its own colour.

## 2. What you write (one block per chapter, in your own part file)

```js
{
  CHAPTER_OBJ["Chapter 57: Flammable and Combustible Liquids"] = {
    d: OBJ_poly([...], [...]),                 // the silhouette: ONE closed path, rounded corners
    holes: [OBJ_rrect(20, 16, 25, 9, 3.5)],    // optional see-throughs (any way round), at least 5 across
    base: "field",                             // optional: the colour of the silhouette under the parts
    plates: [                                  // the PARTS, painted and sculpted in order; at most 24
      ["body",   OBJ_rrect(8, 30, 80, 64, 6)],                          // a part: colour only (rises with the silhouette)
      ["field",  OBJ_rrect(15, 40, 66, 46, 4), { z: -.9, bev: 1 }],     // a panel pressed in
      ["body",   "M21 46L75 80M75 46L21 80", { ln: 6, z: 1.4, bev: 1.4 }],   // an embossed X (a raised line)
      ["rubber", spoutPath, { z: .4, dome: .8 }],                       // a domed part in a natural colour
      ["brass",  "M41 8.5H59M41 12.5H59", { ln: 1.6, cut: .9, paint: 0 }],  // V-grooves only (threads)
      ["body",   hexPath, { gem: 1.4, gw: 3.2 }],                       // planar facets (a hex nut, a gem)
    ],
  };
}
```
Options: `z` (units; + raised, - recessed), `bev` (that part's bevel width, default 1.2), `dome` (units), `gem` (units) with `gw` (facet width,
default 3), `cut` (groove depth), `ln` (stroke width: the part is a line), `paint: 0` (relief only), `e` (a dark painted edge, off by default),
`sh` (a painted drop shadow: avoid on pins, the relief casts its own light). Heights are a few units at most: the whole pin is ~2.6 thick.

The loop:
```
python3 tools/merge-chapter-icons.py --out /tmp/<you>/index.html
python3 tools/render-chapter-badges.py /tmp/<you>/sheet.png --index /tmp/<you>/index.html --only 10,9 --cols 2 --px 200
python3 tools/check-b384-objbadges.py --index /tmp/<you>/index.html
```
In the page: `setChapterObjEdge("B")` to see edge B; `renderObjPin(unit, true, 400, 0, badgeFaceShapeFor(unit))` for the plain-grey relief.

### Helpers (index.html)
`OBJ_poly(points, r)` (rounded polygon), `OBJ_rrect(x, y, w, h, r)`, `OBJ_circle`, `OBJ_ellipse` (two half arcs), `OBJ_chain(points, r)` (an open
run of rounded corners, to join with arcs), `OBJ_walk(d)` (a path's points). Arithmetic and local helpers are fine.

## 3. Pitfalls (each one cost a drawing)

1. **One silhouette path** in `d` (one M, one Z, M L H V C Q A Z only); overlapping subpaths are not a union. See-throughs are `holes`.
2. **A smooth stack of widening parts reads as a bottle, a pawn or a flask**; a side outlet on a cylinder read as a soap pump. Give the
   silhouette a feature no other object has (a toothed deflector, an X-embossed can with a spout, side outlets with caps, a ladder on a roof).
3. **Relief, not paint, carries the detail**: a groove, a raised panel, a domed knob read in grey and at 44px; a thin painted line does not.
4. **Keep heights small** (a raised part 0.5-1.8, a dome up to ~3): taller and the slopes go black and the specular hot.
5. **Circles are two half arcs** (`OBJ_circle`); a one-arc circle over r 12 fails the gate.
6. **No gradients, no filters, no opacity, no hex colours, no markup in a path**; at most 24 parts (counted on the raw list).
7. **Round corners** (radius at least 1); light comes from the top-left.
8. **No text, numbers, letters, people, trademarks.** Official, not cute.
9. **The back still holds the title** (the back is unchanged and lays the title out on the silhouette; the gate reads its plan).
10. **Distinct from every other chapter's silhouette** at 48px (overlap under 0.85).

## 4. Checklist (every chapter, before hand-off)

1. Exact unit title; the merge accepts it.
2. One `d`, rounded corners, the box 80+ of 100 one way, area 2000+, not a plain box.
3. Every part at least 5 across (8+ where it must read at 44px); holes at least 5; gaps at least 4.
4. Reads as the object in PLAIN GREY (render it) and in colour, at 96, 44 and 26px, in two seconds with no label.
5. No flat sticker floating in a part; identity from silhouette and sculpture.
6. The chapter's enamel dominant, natural colours for the rest, saturated.
7. Parts: at most 24, known roles and options, no single-arc circle over r 12.
8. Edge A and edge B both look right (`setChapterObjEdge`).
9. `python3 tools/check-b384-objbadges.py --index /tmp/<you>/index.html` is green.

## 5. The eight prototypes (tools/chapter-objects/part-0-prototypes.js, round 3)

Means of Egress (an open door: a raised leaf with raised panels and a brass knob, the frame, the doorway a deep recess), Chapter 9 (a pendant
sprinkler: brass threaded nipple, faceted hex body, the frame with its two windows and the red glass bulb, the toothed deflector), Chapter 57
(a gas can: the carry handle with a real hole, the embossed X, the black spout and amber cap), Appendix D (a fire engine: cab, windscreen, light
bar, chrome ladder with cut rungs, raised lockers, red stripe, rubber wheels with chrome hubs; the widest, lowest pin), Chapter 53 (a gas
cylinder: handwheel, brass valve and collar, domed shoulder, grooves, label band; the tallest, narrowest), Chapter 1 (a rubber hand stamp: domed
knob, grooved neck, faceted flange, base, inked die), Chapter and Section Finder (a magnifying glass: the domed glass set into the ring, brass
collar, grooved handle), Chapter 5 (a fire hydrant: faceted nut, domed bonnet, barrel, side outlets with faceted caps, base flange with bolts).
Copy the nearest one.
