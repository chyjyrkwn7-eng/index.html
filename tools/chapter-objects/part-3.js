/* Fire Code chapter objects - PART 3 (round 3 format, build 384.66): chapters 32-40 and 50 as RAISED PINS. Each pin is its object: the
   silhouette plus sculpted relief (raised, recessed, domed, faceted, grooved parts), never a picture printed on a face. See
   tools/chapter-objects/README.md and part-0-prototypes.js. Local helpers live inside this one block so nothing leaks into the page. */
{
  /* geometry helpers (part 3's own): points on an ellipse arc, a quadratic's points, a polygon from runs of [points, radius] */
  const D2R = Math.PI / 180;
  const P3arc = (cx, cy, rx, ry, a0, a1, step) => { const out = [], n = Math.max(2, Math.ceil(Math.abs(a1 - a0) / (step || 4)));
    for(let i = 0; i <= n; i++){ const a = (a0 + (a1 - a0) * i / n) * D2R; out.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); } return out; };
  const P3q = (p0, c, p1, n) => { const out = []; for(let i = 0; i <= n; i++){ const t = i / n, u = 1 - t;
    out.push([u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1]]); } return out; };
  /* runs: [[points, r], ...] - every point of a run gets radius r (0 = a sampled curve, left as is); a run of one point is a corner */
  const P3poly = runs => { const pts = [], rs = []; runs.forEach(([p, r]) => p.forEach(q => { pts.push(q); rs.push(r); })); return OBJ_poly(pts, rs); };
  const P3f = p => OBJ_N(p[0]) + " " + OBJ_N(p[1]);
  /* (384.133 badgeart) a sampled line as runs of points, broken wherever skip(p) holds: a groove cut into one part stops at the edge of a
     part laid over it (a stave under a hoop, a strand under the over-wrap) rather than being cut through it */
  const P3runs = (pts, skip) => { let s = "", on = false; pts.forEach(p => { if(skip(p)){ on = false; return; } s += (on ? "L" : "M") + P3f(p); on = true; }); return s; };

  /* ---- Chapter 32: High-Piled Combustible Storage - a selective pallet rack, loaded, seen a little from the right. (384.133 badgeart:
     Madison, "This isn't high piled storage, that's just a stack of boxes. Those orange and blue or orange and green metal racks are high
     piled storage more often than not.") (384.133 art3, Madison: "This high piled storage is bad, it's hard to tell what that even is."
     Drawn straight on, the rack was a flat blue square with tan blocks in it.) Now the rack in 3/4: the front frame - three blue
     uprights with their punched slots, two bays, orange step beams on two levels with their connectors - and the rack going BACK, up
     and to the right: the right end frame seen from the side, its back upright and the cross-bracing zig-zagging between the two posts;
     the back uprights showing over the top. On the floor and on each pair of beams a wooden pallet with two kraft cartons on it, their
     tops seen going back into the rack; the dark inside of the rack behind and between them. ---- */
  {
    const S = OBJ_SDF, BB = [0, 0, 100, 100];
    const D = [14, -9], DL = [7.8, -5];                                 /* the rack's depth, and a load's (as drawn: up and right) */
    const UP = [[2, 8], [38, 44], [74, 80]], BAYS = [[8, 38], [44, 74]];
    const TOP = 7, FLOOR = 96, BTOP = 1, BFLOOR = FLOOR + D[1];
    const BEAMS = [[66, 71], [37, 42]];                                   /* the beams: y0, y1 (lower, upper) */
    const LV = [[FLOOR, 75], [66, 46.5], [37, 19]];                      /* each level: the pallet's foot, the cartons' top */
    const PH = 4.5;
    const sideFrame = S.poly([[80, TOP + 4], [80 + D[0], TOP + 4 + D[1]], [80 + D[0], BFLOOR], [80, FLOOR]]);
    const backPost = ([x0, x1]) => S.box(x0 + D[0], BTOP, x1 - x0, BFLOOR - BTOP, 0);
    const inside = S.box(8, 17, 66, FLOOR - 17, 0);
    const parts = [inside, sideFrame, backPost(UP[2]), backPost(UP[0]), backPost(UP[1])];
    UP.forEach(([x0, x1]) => parts.push(S.box(x0, TOP, x1 - x0, FLOOR - TOP, 0)));
    /* (384.136 art4) Madison: "you can see all the missing pieces like behind it, on top, behind the boxes ... If the boxes weren't there,
       it should look complete." Every frame is a frame now, not only the right one: each front upright is tied to its back upright by a
       strut across the top (the right end frame's own top strut, repeated on the left and middle frames), and each bay has its back
       beams at both levels, behind the loads, so with the cartons taken off the rack still stands as a whole rack. */
    const strut = ([x0, x1]) => [[x0, TOP + 3], [x0 + D[0], TOP + 3 + D[1]], [x1 + D[0], TOP + 3 + D[1]], [x1 + D[0], TOP + 7.5 + D[1]], [x1, TOP + 7.5], [x0, TOP + 7.5]];
    UP.forEach(u => parts.push(S.poly(strut(u))));
    const loads = [];
    BAYS.forEach(([x0, x1]) => LV.forEach(([foot, topY]) => {
      const bx0 = x0 + 2.2, bx1 = x1 - 2.2, by1 = foot - PH;
      const topFace = [[bx0, topY], [bx0 + DL[0], topY + DL[1]], [bx1 + DL[0], topY + DL[1]], [bx1, topY]];
      loads.push({ pal: [x0 + 1, by1, x1 - x0 - 2, PH], box: [bx0, topY, bx1 - bx0, by1 - topY], topFace });
      parts.push(S.poly(topFace));
    }));
    const sil = S.trace(S.grow(S.grow(S.union(parts, 0), -1), 1), BB);
    const f = (x, y) => (+x).toFixed(2) + " " + (+y).toFixed(2);
    const polyD = p => "M" + p.map(q => f(q[0], q[1])).join("L") + "Z";
    const plates = [];
    /* the dark inside of the rack */
    plates.push(["ink", OBJ_rrect(8, 16, 66, FLOOR - 16, 0) + polyD([[44 + D[0] * .5, BTOP + 4], [80 + D[0], BTOP + 4], [80 + D[0], BFLOOR], [44, FLOOR]]), { z: -.9, bev: .6, col: "#151B24" }]);
    /* the back beams of each bay at both levels, behind the loads (their connectors on the back uprights) */
    /* what stands in front of the rack's insides: every load (pallet, cartons, their tops) and the front uprights - a part behind them is
       cut where they cover it, so its relief never shows through them */
    const front = S.union(loads.flatMap(l => [S.box(l.pal[0], l.pal[1], l.pal[2], l.pal[3], 0), S.box(l.box[0], l.box[1], l.box[2], l.box[3], 0), S.poly(l.topFace)])
      .concat(UP.map(([x0, x1]) => S.box(x0, TOP, x1 - x0, FLOOR - TOP, 0)))
      .concat(BAYS.flatMap(([x0, x1]) => BEAMS.map(([y0, y1]) => S.box(x0 - 1.6, y0 - 1.6, x1 - x0 + 3.2, y1 - y0 + 3.2, 0)))), 0);
    const behind = g => S.loops(S.minus(g, S.grow(front, .3)), BB).map(S.pathOf).join("");   /* every piece that shows, each its own loop */
    const bbF = []; BAYS.forEach(([x0, x1]) => BEAMS.forEach(([y0, y1]) => { const a = x0 + D[0], b = Math.min(x1 + D[0], 79.4);   /* (behind the right end frame it is not drawn) */
      bbF.push(S.box(a, y0 + D[1], b - a, y1 - y0, .5)); }));
    plates.push(["hot", behind(S.union(bbF, 0)), { z: -.45, bev: .4, col: "#B85E14" }]);
    /* the top struts tying each front upright to its back upright (the left and middle frames; the right one is drawn with its frame below) */
    plates.push(["field", UP.slice(0, 2).map(u => "M" + u.map(() => "").join("") + strut(u).map(q => f(q[0], q[1])).join("L") + "Z").join(""), { z: .3, bev: .4, col: "#2B64A6" }]);
    /* the left and middle frames are frames too: their floor ties and the bracing between front and back uprights, behind the loads */
    const sideF = [];
    UP.slice(0, 2).forEach(([x0, x1]) => {
      const pts = [[x1 + .5, TOP + 6]]; { let y = TOP + 6, fr = true; while(y + 10 <= FLOOR - 4){ y += 10; pts.push(fr ? [x1 + D[0] - .5, y + D[1]] : [x1 + .5, y]); fr = !fr; } }
      for(let i = 1; i < pts.length; i++) sideF.push(S.capsule(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], 1));
      sideF.push(S.poly([[x1, FLOOR - 7], [x1 + D[0], FLOOR - 7 + D[1]], [x1 + D[0], FLOOR - 2.5 + D[1]], [x1, FLOOR - 2.5]]));
    });
    plates.push(["field", behind(S.union(sideF, 0)), { z: -.35, bev: .4, col: "#245A96" }]);
    /* the back uprights (seen over the top, and the right one beside the end frame), over the ends of the bracing and the back beams */
    plates.push(["field", UP.map(([x0, x1]) => OBJ_rrect(x0 + D[0], BTOP, x1 - x0, BFLOOR - BTOP, .8)).join(""), { z: -.3, bev: .5, col: "#245A96" }]);
    /* the right end frame, seen from the side: its two posts and the bracing between them */
    let brace = "M" + f(80.5, TOP + 6); { let y = TOP + 6, front = true; while(y + 10 <= FLOOR - 4){ y += 10; brace += "L" + f(front ? 80 + D[0] - .5 : 80.5, front ? y + D[1] * 1 : y); front = !front; } }
    plates.push(["field", polyD([[80, TOP + 3], [80 + D[0], TOP + 3 + D[1]], [80 + D[0], TOP + 7.5 + D[1]], [80, TOP + 7.5]]) + polyD([[80, FLOOR - 7], [80 + D[0], FLOOR - 7 + D[1]], [80 + D[0], FLOOR - 2.5 + D[1]], [80, FLOOR - 2.5]]), { z: .3, bev: .4, col: "#2B64A6" }]);
    plates.push(["field", brace, { ln: 2.2, z: .4, bev: .5, col: "#3A7BC4" }]);
    /* the loads: pallets and cartons, their tops going back into the rack */
    let pals = "", pfork = "", cart = "", tops = "", seam = "", tape = "";
    loads.forEach(({ pal, box, topFace }) => {
      pals += OBJ_rrect(pal[0], pal[1], pal[2], pal[3], .5);
      const fw = pal[2] * .24; pfork += OBJ_rrect(pal[0] + pal[2] * .13, pal[1] + 2, fw, pal[3] - 2, [.5, .5, 0, 0]) + OBJ_rrect(pal[0] + pal[2] * .87 - fw, pal[1] + 2, fw, pal[3] - 2, [.5, .5, 0, 0]);
      cart += OBJ_rrect(box[0], box[1], box[2], box[3], 0);
      tops += polyD(topFace);
      const xm = box[0] + box[2] / 2;
      seam += "M" + f(xm, box[1] + .8) + "V" + (box[1] + box[3] - .6).toFixed(2);
      tape += "M" + f(box[0] + box[2] * .25, box[1]) + "V" + (box[1] + box[3] * .38).toFixed(2) + "M" + f(box[0] + box[2] * .75, box[1]) + "V" + (box[1] + box[3] * .38).toFixed(2);
    });
    plates.push(["cardboard", tops, { z: .5, bev: .5, col: "#D9AC72" }]);
    plates.push(["cardboard", cart, { z: .7, bev: .6, col: "#B47E45" }]);
    plates.push(["cardboard", seam, { ln: 1.2, cut: .7, paint: 0 }]);
    plates.push(["cardboard", tape, { ln: 2, z: .2, bev: .3, col: "#8C5A2B" }]);
    plates.push(["wood", pals, { z: .5, bev: .45 }]);
    plates.push(["ink", pfork, { z: -.6, bev: .35, col: "#2A1D12" }]);
    /* the front uprights, the punched slots up them, the orange beams and their connectors in front of everything */
    plates.push(["field", UP.map(([x0, x1]) => OBJ_rrect(x0, TOP, x1 - x0, FLOOR - TOP, 1)).join(""), { z: 1, bev: .7, dome: .5 }]);
    const onBeam = p => BEAMS.some(([y0, y1]) => p[1] > y0 - 2.4 && p[1] < y1 + 2.4);
    let slots = ""; UP.forEach(([x0, x1]) => { const xm = (x0 + x1) / 2, ys = []; for(let y = TOP + 3; y <= FLOOR - 3; y += .5) ys.push([xm, y]); slots += P3runs(ys, onBeam); });
    plates.push(["field", slots, { ln: 1.3, cut: .6, paint: 0 }]);
    let beams = "", conn = "";
    BAYS.forEach(([x0, x1]) => BEAMS.forEach(([y0, y1]) => { beams += OBJ_rrect(x0, y0, x1 - x0, y1 - y0, .6);
      conn += OBJ_rrect(x0 - 1.6, y0 - 1.6, 3.6, y1 - y0 + 3.2, .8) + OBJ_rrect(x1 - 2, y0 - 1.6, 3.6, y1 - y0 + 3.2, .8); }));
    plates.push(["hot", beams, { z: 1.3, bev: .6, dome: .4, col: "#F07A1A" }]);
    plates.push(["hot", conn, { z: 1.5, bev: .45, col: "#C95F12" }]);
    CHAPTER_OBJ["Chapter 32: High-Piled Combustible Storage"] = {
      d: sil.d, holes: sil.holes,
      col: "#2F6FB8", base: "field",
      plates,
    };
  }

  /* ---- Chapter 33: Fire Safety During Construction and Demolition - a hard hat, side on, facing left. (384.133 badgeart, Madison: "I
     don't like the hat at all. Make this better." The round-9 hat was a yellow bell, front on, with a short brim: a bowler.) Now a real
     cap-style hard hat: the high domed shell with its raised crown ridge and the two ribs running front to back, the bill at the front
     reaching out and down, the full brim round the back, the suspension's headband showing under the brim. NAVY, by Madison's standing
     rule for this class: "If there is going to be any hard hats ... they will be navy blue" (r6; every hard hat, helmet and cap the
     agency's people wear is navy). (384.133 art3, Madison: "The navy hard hat is cool, however the randomly placed star is not it.
     There's gotta be something better.") The star is gone; the shell carries a silver REFLECTIVE BAND all the way round it, low on the
     crown above the brim, as fire-service and fire-marshal hard hats do. On a hat drawn side on, a front shield or cross would sit on the
     very edge of the shell (seen edge on) and read off-centre again; the band is centred by its nature, runs front to back on the shell's
     own curve (a little bowed, as a ring round the dome is from a hair below), and stays a bright line at the case's 44px and at 26px. ---- */
  {
    const S = OBJ_SDF, BB = [0, 0, 100, 100];
    const CX = 55, CY = 76, RX = 38, RY = 42;                                         /* the shell: the top of an ellipse */
    const shell = S.inter(S.ellipse(CX, CY, RX, RY), S.box(0, 0, 100, CY + 1, 0));
    const brimPts = [[2, 85], [7, 78], [17, 74.5], [90, 73.5], [96, 75], [97.5, 78.5], [94, 81], [86, 81.5], [24, 82.5], [11, 87], [5, 88]];
    const brim = S.poly(brimPts);
    const band = S.box(32, 79, 44, 7, 2.5);                                            /* the suspension's headband */
    const all = S.union([shell, brim, band], 1.6);
    const ell = (kx, ky, a0, a1) => { const o = []; for(let i = 0; i <= 24; i++){ const t = (a0 + (a1 - a0) * i / 24) * Math.PI / 180; o.push([CX + RX * kx * Math.cos(t), CY + RY * ky * Math.sin(t)]); }
      return "M" + o.map(p => p[0].toFixed(2) + " " + p[1].toFixed(2)).join("L"); };
    /* the reflective band: between two lines round the shell, each bowed up a little in the middle, cut to the shell's face */
    /* (384.136 art4) Madison: "White stripe looks bad, looks weird, like you can tell it's not there." It was a flat white bar whose edges
       bowed UP in the middle (a ring seen from below) on a hat drawn from a little above, unshaded on a domed shell. Now it is a ring
       round the dome as this view shows one: both edges SAG a little in the middle (the near side of the ring, seen from above), it runs
       out to the shell's edge front and back, and it is silver (the tape's grey, not white) with the shell's own doming, so it darkens
       as it turns away at the sides like the navy round it. */
    /* the band's width falls off toward front and back as it turns away round the shell (foreshortened), its middle line sags */
    const edge = (side) => { const o = []; for(let i = 0; i <= 40; i++){ const x = 12 + 86 * i / 40, t = Math.min(1, Math.abs((x - CX) / RX)), c = Math.sqrt(Math.max(0, 1 - t * t));
      const mid = 63.8 + 3.2 * c, w = 6 * (.45 + .55 * c); o.push([x, mid + side * w / 2]); } return o; };
    const bandPoly = edge(-1).concat(edge(1).reverse());
    const refl = S.inter(S.poly(bandPoly), S.inter(S.grow(shell, -.7), S.box(0, 0, 100, 72.6, 0)));
    CHAPTER_OBJ["Chapter 33: Fire Safety During Construction and Demolition"] = {
      d: S.shape(all, BB),
      col: "#24407A", base: "field",
      plates: [
        ["rubber", S.shape(band, BB), { z: -.5, bev: .6, col: "#161B27" }],                              /* the headband */
        ["field", S.shape(S.inter(shell, S.box(0, 0, 100, 74, 0)), BB), { dome: 2.6 }],                 /* the shell */
        ["field", ell(.86, .9, 214, 326), { ln: 6, z: .9, bev: 1.3 }],                                   /* the crown ridge */
        ["field", ell(.92, .64, 216, 324), { ln: 2.6, z: .6, bev: .8 }],                                 /* the side rib, front to back */
        ["field", S.shape(brim, BB), { z: .5, bev: .8, dome: .5 }],                                      /* the brim and the bill */
        ["shade", "M7 86.4Q13 83.4 24 82H86", { ln: 2.2, z: .2, bev: .5 }],                             /* the brim's underside */
        ["cream", S.shape(refl, BB), { z: .3, bev: .35, dome: 2.6, col: "#A9B3BF" }],                         /* the reflective band round the shell */
      ],
    };
  }

  /* ---- Chapter 34: Tire Rebuilding and Tire Storage - a stack of three tyres, seen from the side and a little above. (384.133 art3,
     Madison, of badgeart's stack: "I want the tires of course, but it's got to look better, this just doesn't look legit." Its tyres were
     pill-shaped bands with half-round ends, and the tread was slanted slash marks with one line through each tyre.) Each tyre is now a
     real tyre on its side: a short cylinder whose front edges are arcs (it is seen from a little above), its sidewalls rounding over at
     the shoulders top and bottom, and between them the flat tread band. The tread is a block pattern on that band - a groove round the
     middle and the cross grooves between the blocks, staggered above and below it - laid round the tyre, so the blocks close up toward
     the sides as the tyre turns away; every groove stays inside its own tread band. Each tyre sits on the one under it: the lower one
     darkens where the upper one's shoulder meets it (the contact shadow), and the outline steps in between them. The top tyre shows its
     upper sidewall as an ellipse with a raised rim line and the bead, and its hole in perspective: the far inside wall of the tyre seen
     through it, dark below. Staggered a little as tyres stacked by hand are (check-b384-badgetwins: Chapter 50 turned on its side). ---- */
  {
    const S = OBJ_SDF, BB = [0, 0, 100, 100];
    const E = 7, H = 24, A = 37.5, SH = 4.2;                                  /* the arcs' depth, a tyre's height, half-width, shoulder */
    const T = [[48, 62], [53, 38], [48.5, 14]];                            /* each tyre: centre x, its top's centre y (bottom, middle, top) */
    const tyre = ([cx, y]) => S.union([S.ellipse(cx, y, A - 2.6, E), S.box(cx - A, y + 3.2, 2 * A, H - 6.4, 3.6), S.ellipse(cx, y + H, A - 2.6, E)], 3.2);
    const tyres = T.map(tyre);
    const all = S.union(tyres, .5);
    const lp = f => S.loops(f, BB).map(S.pathOf).join("");
    /* the tread band of a tyre: between the arcs SH below its top and SH above its bottom, a hair in from its sides */
    const band = ([cx, y]) => S.inter(S.minus(S.union([S.ellipse(cx, y + H - SH, A - 1.4, E), S.box(cx - A + 1.4, y + SH, 2 * (A - 1.4), H - 2 * SH, 0)], 0),
      S.ellipse(cx, y + SH, A - 1.4, E)), S.box(0, y + SH - .01, 100, 100, 0));
    const f = (x, y) => x.toFixed(2) + " " + y.toFixed(2);
    let tread = "", ring = "";
    const shadows = [];
    T.forEach(([cx, y], k) => {
      const ra = A - 1.4, yA = y + SH, yB = y + H - SH, ym = (yA + yB) / 2;
      const arcY = (y0, s) => y0 + E * Math.sqrt(Math.max(0, 1 - s * s));      /* the front arc at x = cx + ra * s */
      /* the groove round the middle */
      let p = ""; for(let i = 0; i <= 40; i++){ const s = -.9 + 1.8 * i / 40; p += (i ? "L" : "M") + f(cx + ra * s, arcY(ym, s)); } ring += p;
      /* the cross grooves: blocks above the ring and below it, staggered by half a block, closing up toward the sides */
      const step = 15 * Math.PI / 180;
      for(let j = -6; j <= 6; j++){
        [[-.5, yA + .9, ym - 1.5], [0, ym + 1.5, yB - .9]].forEach(([off, y0, y1]) => {
          const th = (j + off) * step; if(Math.abs(th) > 1.1) return;
          const s0 = Math.sin(th), s1 = Math.sin(th + .07);                      /* a slight slant, as a block tread has */
          tread += "M" + f(cx + ra * s0, arcY(y0, s0)) + "L" + f(cx + ra * s1, arcY(y1, s1));
        });
      }
      /* the contact shadow on this tyre where the one above sits on it */
      if(k < 2) shadows.push(S.inter(S.minus(S.grow(tyres[k + 1], 2.4), tyres[k + 1]), tyres[k]));
    });
    const [tx, ty] = T[2], RX = A - 2.6, HX = RX * .5, HY = E * .5;
    CHAPTER_OBJ["Chapter 34: Tire Rebuilding and Tire Storage"] = {
      d: S.shape(all, BB),
      base: "rubber", col: "#34373C",
      plates: [
        ["rubber", S.shape(tyres[0], BB), { dome: .9 }],                                                        /* the bottom tyre */
        ["rubber", lp(band(T[0])), { z: .3, bev: .5, col: "#2C2F34" }],                                          /* its tread band */
        ["ink", lp(shadows[0]), { z: -.25, bev: .6, col: "#111316" }],                                           /* where the middle one sits on it */
        ["rubber", S.shape(tyres[1], BB), { dome: .9 }],                                                        /* the middle tyre */
        ["rubber", lp(band(T[1])), { z: .3, bev: .5, col: "#2C2F34" }],
        ["ink", lp(shadows[1]), { z: -.25, bev: .6, col: "#111316" }],                                           /* where the top one sits on it */
        ["rubber", S.shape(tyres[2], BB), { dome: .9 }],                                                        /* the top tyre */
        ["rubber", lp(band(T[2])), { z: .3, bev: .5, col: "#2C2F34" }],
        ["ink", tread, { ln: 1.6, z: -.7, bev: .35, col: "#16181B" }],                                          /* the cross grooves, each in its own band */
        ["ink", ring, { ln: 1.6, z: -.7, bev: .35, col: "#16181B" }],                                           /* the groove round each */
        ["field", OBJ_ellipse(tx, ty, RX, E), { z: .45, bev: .9, dome: .8, col: "#454950" }],                   /* the top tyre's upper sidewall */
        ["field", OBJ_ellipse(tx, ty, RX * .8, E * .85), { ln: 1, cut: .45, paint: 0 }],                         /* its rim line */
        ["field", OBJ_ellipse(tx, ty, HX + 3.4, HY + 1.6), { z: .2, bev: .5, dome: .3, col: "#3A3E44" }],         /* the bead */
        ["ink", OBJ_ellipse(tx, ty, HX, HY), { z: -1.6, bev: .6, col: "#121417" }],                              /* the hole */
        ["rubber", lp(S.minus(S.ellipse(tx, ty, HX, HY), S.ellipse(tx, ty + 2.4, HX + .6, HY))), { z: -1.1, bev: .4, col: "#3B3F45" }],   /* the far inside wall, through it */
      ],
    };
  }

  /* ---- Chapter 35: Welding and Other Hot Work - an oxy-fuel welding torch alight, redrawn (384.93 r9: the welding helmet, front on, read
     as a face): the black grip with its grooves, the two valve knobs at its back (red for the fuel, green for the oxygen), the brass head,
     the steel tip and its nozzle, and the flame - the hot blue cone inside the orange. (384.133 badgeart: laid at a shallower angle and
     the grip made thicker - at 45 degrees and 9.8 thick the silhouette was 1996 of 10000, under the 2000 floor, and its back had no
     band wide enough for the title, which came out at 5px in your hand.) ---- */
  {
    const S = OBJ_SDF, BB = [0, 0, 100, 100];
    const a = -18 * Math.PI / 180, u = [Math.cos(a), Math.sin(a)], n = [-u[1], u[0]];
    const P = (p, t, w) => [p[0] + u[0] * t + n[0] * (w || 0), p[1] + u[1] * t + n[1] * (w || 0)];
    const G0 = [13, 63], G1 = P(G0, 31), H1 = P(G1, 14), T1 = P(H1, 11), N1 = P(T1, 6.5), FC = P(N1, 9), FT = P(N1, 33);
    const grip = S.capsule(G0[0], G0[1], G1[0], G1[1], 17), head = S.capsule(G1[0], G1[1], H1[0], H1[1], 8.6);
    const tip = S.capsule(H1[0], H1[1], T1[0], T1[1], 4.2), noz = S.cone(T1[0], T1[1], N1[0], N1[1], 4.2, 5.8);
    const K1 = P(G0, -1.5, -13), K2 = P(G0, -1.5, 13), knobR = S.circle(K1[0], K1[1], 7.8), knobG = S.circle(K2[0], K2[1], 7.8);
    const flame = S.union([S.circle(FC[0], FC[1], 9.6), S.cone(FC[0], FC[1], FT[0], FT[1], 9.6, .9)], 0);
    const heart = S.union([S.circle(P(FC, -.5)[0], P(FC, -.5)[1], 4.6), S.cone(P(FC, -.5)[0], P(FC, -.5)[1], P(FC, 13)[0], P(FC, 13)[1], 4.6, .7)], 0);
    const blue = S.cone(P(N1, .4)[0], P(N1, .4)[1], P(N1, 5.2)[0], P(N1, 5.2)[1], 2.6, 2.9);
    const all = S.union([grip, head, tip, noz, knobR, knobG, flame], 1.4);
    const f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
    let grooves = ""; [9, 16, 23, 30].forEach(t => { grooves += "M" + f(P(G0, t, -11)) + "L" + f(P(G0, t, 11)); });
    CHAPTER_OBJ["Chapter 35: Welding and Other Hot Work"] = {
      d: S.shape(all, BB),
      base: "rubber",
      plates: [
        ["hot", S.shape(flame, BB), { dome: 1.4, col: "#FF8A2A" }],                                       /* the flame */
        ["glow", S.shape(heart, BB), { z: .5, bev: .6, dome: .8, col: "#FFE08A" }],                       /* its yellow heart */
        ["water", S.shape(blue, BB), { z: .8, bev: .5, dome: .6, col: "#5FB6FF" }],                       /* the hot blue cone at the nozzle */
        ["steel", S.shape(tip, BB), { dome: .8 }],                                                         /* the tip */
        ["brass", S.shape(noz, BB), { dome: .8 }],                                                         /* its nozzle */
        ["brass", S.shape(head, BB), { dome: 1.2 }],                                                       /* the head */
        ["rubber", S.shape(grip, BB), { dome: 1.4 }],                                                      /* the grip */
        ["rubber", grooves, { ln: 1.6, cut: .9, paint: 0 }],                                               /* its grooves */
        ["red", S.shape(knobR, BB), { dome: 1.5, col: "#D8352C" }],                                        /* the fuel valve */
        ["red", S.shape(knobG, BB), { dome: 1.5, col: "#2E9B4F" }],                                        /* the oxygen valve */
      ],
    };
  }

  /* ---- Chapter 36: Marinas - a galvanised anchor: the ring with a real hole, the wooden stock across the shank, the curved arms
     thickening into a heavy crown, and their faceted flukes. Drawn as its right half and mirrored, so it is symmetric by construction;
     the crown and the stock are broad enough to carry the back's title. ---- */
  {
    /* the shank's half-width; the arms' outer circle and inner ellipse (a heavy crown, slim tips); the angle where the arms end */
    const W = 6, Co = [50, 50], Ro = 43, Ci = [50, 46], Rx = 32, Ry = 18, A = 12;
    const on = (c, r, a) => [c[0] + r * Math.cos(a * D2R), c[1] + r * Math.sin(a * D2R)];
    const yj = Ci[1] + Ry * Math.sqrt(1 - (W / Rx) * (W / Rx)), aj = Math.acos(W / Rx) / D2R;   /* the inner arc meets the shank */
    const yr = 13 + Math.sqrt(121 - W * W), ar = Math.atan2(yr - 13, W) / D2R;     /* the ring meets the shank */
    const e0 = [Ci[0] + Rx * Math.cos(A * D2R), Ci[1] + Ry * Math.sin(A * D2R)], e1 = on(Co, Ro, A), v = [e1[0] - e0[0], e1[1] - e0[1]], m = [(e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2];
    const vl = Math.hypot(v[0], v[1]), vn = [v[0] / vl, v[1] / vl], up = (() => { const t = [vn[1], -vn[0] - 1], l = Math.hypot(t[0], t[1]); return [t[0] / l, t[1] / l]; })();
    const back = [-up[0], -up[1]];
    const bIn = [e0[0] - .6 * v[0] + 4 * back[0], e0[1] - .6 * v[1] + 4 * back[1]], bOut = [e1[0] + .45 * v[0] + 4 * back[0], e1[1] + .45 * v[1] + 4 * back[1]];
    const tip = [m[0] + 17 * up[0], m[1] + 17 * up[1]];
    /* the right half, top centre to bottom centre: [point, corner radius] */
    const half = [].concat(
      P3arc(50, 13, 11, 11, 270, 360 + ar, 8).map(p => [p, 0]),
      [[[50 + W, 25], 1], [[77, 25], 4.5], [[77, 36], 4.5], [[50 + W, 36], 1], [[50 + W, yj], 2]],
      P3arc(Ci[0], Ci[1], Rx, Ry, aj, A, 5).slice(1, -1).map(p => [p, 0]),
      [[e0, 0], [bIn, 1], [tip, 1.3], [bOut, 1], [e1, 0]],
      P3arc(Co[0], Co[1], Ro, Ro, A, 90, 5).slice(1).map(p => [p, 0]));
    const mir = half.slice(1, -1).reverse().map(([p, r]) => [[100 - p[0], p[1]], r]);
    const all = half.concat(mir);
    const d = OBJ_poly(all.map(q => q[0]), all.map(q => q[1]));
    const arm = P3poly([[P3arc(Co[0], Co[1], Ro, Ro, A, 180 - A, 5), 0], [P3arc(Ci[0], Ci[1], Rx, Ry, 180 - A, A, 5), 0]]);
    const fluke = k => { const f = q => (k > 0 ? q : [100 - q[0], q[1]]); return OBJ_poly([e0, bIn, tip, bOut, e1].map(f), [0, 1, 1.3, 1, 0]); };
    CHAPTER_OBJ["Chapter 36: Marinas"] = {
      d,
      base: "steel",
      holes: [OBJ_circle(50, 13, 5)],
      plates: [
        ["steel", OBJ_rrect(50 - W, 20, 2 * W, 50, 2), { dome: 1.2 }],                                /* the shank */
        ["steel", arm, { dome: 1.8 }],                                                                 /* the arms and the crown */
        ["steel", fluke(1), { gem: 1.4, gw: 3.4 }],                                                   /* the flukes */
        ["steel", fluke(-1), { gem: 1.4, gw: 3.4 }],
        ["wood", OBJ_rrect(23, 25, 54, 11, 4.5), { z: .9, bev: .9, dome: .7 }],                      /* the stock */
        ["wood", "M38 26V35M62 26V35", { ln: 1.4, cut: .7, paint: 0 }],                                /* its seams */
        ["steel", OBJ_circle(50, 13, 11), { dome: 1.4 }],                                              /* the ring */
      ],
    };
  }

  /* ---- Chapter 37: Combustible Fibers - a ball of yarn: the wound ball cut with its strands, the over-wrap band crossing it, and the
     loose end trailing away along the bottom. ---- */
  {
    const C = [45, 46], R = 40, hw = 3.6;
    const line = P3q([60, 80], [78, 99], [96, 84], 18);                                 /* the loose end's centre line */
    const nrm = i => { const a = line[Math.max(0, i - 1)], b = line[Math.min(line.length - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy); return [-dy / l, dx / l]; };
    const side = s => line.map((p, i) => { const n = nrm(i); return [p[0] + s * hw * n[0], p[1] + s * hw * n[1]]; });
    const out = side(1), inn = side(-1);   /* out: the lower edge; inn: the upper */
    const ang = p => Math.atan2(p[1] - C[1], p[0] - C[0]) / D2R;
    const outside = p => Math.hypot(p[0] - C[0], p[1] - C[1]) > R;
    const io = out.findIndex(outside), ii = inn.findIndex(outside);
    const aOut = ang(out[io]), aIn = ang(inn[ii]);
    const end = line[line.length - 1], en = nrm(line.length - 1);
    const cap = []; for(let k = 1; k < 8; k++){ const t = Math.PI * k / 8, dx = line[line.length - 1][0] - line[line.length - 2][0], dy = line[line.length - 1][1] - line[line.length - 2][1], l = Math.hypot(dx, dy);
      cap.push([end[0] + hw * (Math.cos(t) * en[0] + Math.sin(t) * dx / l), end[1] + hw * (Math.cos(t) * en[1] + Math.sin(t) * dy / l)]); }
    /* round the ball the long way from one edge of the loose end to the other, out along that edge, round its cap, back along the first */
    const A = aOut > aIn ? { p: out, i: io, a: aOut, o: 1 } : { p: inn, i: ii, a: aIn, o: -1 }, B = A.p === out ? { p: inn, i: ii, a: aIn } : { p: out, i: io, a: aOut };
    const d = P3poly([[P3arc(C[0], C[1], R, R, A.a, B.a + 360, 4), 0], [B.p.slice(B.i + 1), 0], [A.o > 0 ? cap.slice().reverse() : cap, 0], [A.p.slice(A.i + 1).reverse(), 0]]);
    /* the strands: chords across the ball at 35 degrees, bowed like lines on a sphere */
    const strands = (a, offs, bow, skip) => { let s = ""; const u = [Math.cos(a * D2R), Math.sin(a * D2R)], v = [-u[1], u[0]];
      offs.forEach(o => { const h = Math.sqrt(Math.max(0, (R - 3) * (R - 3) - o * o)), m = [C[0] + v[0] * o, C[1] + v[1] * o];
        const p0 = [m[0] - u[0] * h, m[1] - u[1] * h], p1 = [m[0] + u[0] * h, m[1] + u[1] * h], c = [m[0] + v[0] * bow * (1 - Math.abs(o) / R), m[1] + v[1] * bow * (1 - Math.abs(o) / R)];
        s += skip ? P3runs(P3q(p0, c, p1, 40), skip) : "M" + P3f(p0) + "Q" + P3f(c) + " " + P3f(p1); }); return s; };
    const underBand = p => { const a = 125 * D2R; return Math.abs(-(p[0] - C[0]) * Math.sin(a) + (p[1] - C[1]) * Math.cos(a)) < 9 + 1.3; };
    const band = (() => { const a = 125 * D2R, u = [Math.cos(a), Math.sin(a)], v = [-u[1], u[0]], h = R + 2, w = 9;
      return OBJ_poly([[C[0] - u[0] * h - v[0] * w, C[1] - u[1] * h - v[1] * w], [C[0] + u[0] * h - v[0] * w, C[1] + u[1] * h - v[1] * w],
        [C[0] + u[0] * h + v[0] * w, C[1] + u[1] * h + v[1] * w], [C[0] - u[0] * h + v[0] * w, C[1] - u[1] * h + v[1] * w]], 2); })();
    CHAPTER_OBJ["Chapter 37: Combustible Fibers"] = {
      d,
      plates: [
        ["body", OBJ_circle(C[0], C[1], R), { dome: 2.4 }],                                          /* the ball */
        ["body", strands(35, [-30, -21, -12, -3, 6, 15, 24, 32], 5, underBand), { ln: 2, cut: 1.3, paint: 0 }],   /* its wound strands, stopping at the band */
        ["lite", band, { z: .9, bev: 1, dome: .8 }],                                                 /* the over-wrap band */
        ["lite", strands(125, [-5, 0, 5], 3), { ln: 1.5, cut: 1, paint: 0 }],                      /* its strands */
        /* (384.79) the loose end comes OUT of the ball: it starts well inside the ball (on its wound surface), in the ball's own colour and
           at the silhouette's own thickness, and runs off it - it was the darker shade and began at the ball's edge, so it read as a
           separate piece ("the piece coming off looks disconnected") */
        ["body", "M" + P3f([50, 66]) + "Q" + P3f([55, 76]) + " " + P3f(line[0]) + "L" + line.map(P3f).join("L"), { ln: hw * 2, z: .45, bev: 1.1 }],
        ["body", "M" + P3f(line[4]) + "l2.6 -3.4M" + P3f(line[8]) + "l2.6 -3.4M" + P3f(line[12]) + "l3.2 -1.2", { ln: 1, cut: .6, paint: 0 }],   /* its ply twist */
      ],
    };
  }

  /* ---- Chapter 38: Higher Education Laboratories - an Erlenmeyer flask: the rolled lip, the neck, the conical body, the liquid in it
     pressed in behind the glass, the graduation marks cut into the wall. ---- */
  {
    CHAPTER_OBJ["Chapter 38: Higher Education Laboratories"] = {
      base: "glass",
      d: OBJ_poly([[38, 4], [62, 4], [62, 11], [59, 12], [59, 36], [90, 87], [86, 94], [14, 94], [10, 87], [41, 36], [41, 12], [38, 11]],
        [2.5, 2.5, 1.5, 1, 3, 5, 4, 4, 5, 3, 1, 1.5]),
      plates: [
        ["glass", OBJ_rrect(38, 4, 24, 7.5, 2.5), { z: .5, dome: .8 }],                                /* the lip */
        ["glass", OBJ_poly([[59, 12], [59, 36], [90, 87], [86, 94], [14, 94], [10, 87], [41, 36], [41, 12]], [1, 3, 5, 4, 4, 5, 3, 1]), { dome: 1.6 }],   /* the glass */
        ["body", OBJ_poly([[27.5, 64], [72.5, 64], [85, 86], [82, 90.5], [18, 90.5], [15, 86]], [1.5, 1.5, 3, 3, 3, 3]), { z: -.7, bev: .7, dome: .9 }],   /* the liquid */
        ["glass", "M38 44H46M35.5 50H45M33 56H46", { ln: 1.5, cut: .8, paint: 0 }],                 /* the graduations */
      ],
    };
  }

  /* ---- Chapter 39: Processing and Extraction Facilities - a still: the stainless extraction column with its domed cap and copper tray
     rings, the copper vapour line arching over and down into the domed receiving tank beside it, both on a green-painted skid; the
     space under the vapour line a real opening. The broad tank and the skid give the back's title room. ---- */
  {
    const cap = P3arc(23, 20, 13, 14, 180, 314.4, 6);
    const ang = x => Math.acos((x - 65) / 29) / D2R;
    const d = P3poly([[cap, 0], [[[82, 10]], 7], [P3arc(65, 60, 29, 14, 360 - ang(82), 360, 6), 0], [[[94, 86]], 1], [[[96, 86]], 1.5], [[[96, 95]], 2], [[[4, 95]], 2],
      [[[4, 86]], 1.5], [[[10, 86]], 1]]);
    const hole = P3poly([[[[36, 17]], 1.5], [[[75, 17]], 1], [P3arc(65, 60, 29, 14, 360 - ang(75), 180, 6), 0]]);
    CHAPTER_OBJ["Chapter 39: Processing and Extraction Facilities"] = {
      d,
      base: "steel",
      holes: [hole],
      plates: [
        ["steel", OBJ_rrect(10, 18, 26, 68, 0), { dome: 1.4 }],                                       /* the column */
        ["steel", "M10 20A13 14 0 0 1 36 20Z", { dome: 1.8 }],                                         /* its cap */
        ["brass", OBJ_rrect(9, 31, 28, 5, 1), { z: .8, bev: .6 }],                                     /* its tray rings */
        ["brass", OBJ_rrect(9, 49, 28, 5, 1), { z: .8, bev: .6 }],
        ["brass", OBJ_rrect(9, 67, 28, 5, 1), { z: .8, bev: .6 }],
        ["brass", OBJ_poly([[30, 10], [82, 10], [82, 48], [75, 48], [75, 17], [30, 17]], [0, 7, 0, 0, 1, 0]), { dome: .9 }],   /* the vapour line */
        ["brass", OBJ_rrect(53, 8, 5, 11, 1.2), { z: .7, bev: .5 }],                                   /* its flanges */
        ["brass", OBJ_rrect(73, 27, 11, 5, 1.2), { z: .7, bev: .5 }],
        ["steel", "M36 60A29 14 0 0 1 94 60V86H36Z", { z: .2, bev: 1, dome: 1.8 }],                     /* the receiving tank, domed */
        ["brass", OBJ_rrect(36, 66, 58, 5, 0), { z: .6, bev: .5 }],                                     /* its band */
        ["brass", OBJ_circle(65, 78, 3.4), { dome: 1.2 }],                                              /* its drain valve */
        ["deep", OBJ_rrect(4, 86, 92, 9, 2), { z: .5, bev: .6, dome: .6 }],                             /* the skid */
        ["steel", OBJ_circle(9.5, 90.5, 2.5), { dome: 1 }],                                             /* its bolts */
        ["steel", OBJ_circle(50, 90.5, 2.5), { dome: 1 }],
        ["steel", OBJ_circle(90.5, 90.5, 2.5), { dome: 1 }],
      ],
    };
  }

  /* ---- Chapter 40: Storage of Distilled Spirits and Wines - a wine cask lying on its rack, as in a cellar: the oak staves bulging
     between the iron hoops, the bung on top, the brass tap in its head, the two chocks and the plank under it. (Upright, a barrel's outline was
     too close to a jug's or a board's; lying on a rack with its tap it is nothing else.) ---- */
  {
    const L = 16, Rt = 90, M = 53, top = x => { const t = (x - L) / (Rt - L); return 22 - 28 * t * (1 - t); }, bot = x => 88 - top(x);
    const span = (x0, x1, n) => { const o = []; for(let i = 0; i <= n; i++){ const x = x0 + (x1 - x0) * i / n; o.push(x); } return o; };
    const topRun = span(L, Rt, 18).map(x => [x, top(x)]);
    const botRun = (x0, x1) => span(x0, x1, Math.max(2, Math.round(Math.abs(x1 - x0) / 4))).map(x => [x, bot(x)]);
    /* the rack: two chocks under the cask (x 22-40 and 66-84) on one plank (y 86-94); the space between them is a real opening */
    const d = P3poly([[topRun, 0], [P3arc(Rt, 44, 4, 22, -90, 90, 10).slice(1), 0],
      [botRun(Rt, 84).slice(1), 0], [[[84, 86]], 1], [[[92, 86]], 1.5], [[[92, 94]], 2], [[[14, 94]], 2], [[[14, 86]], 1.5], [[[22, 86]], 1], [botRun(22, L).slice(0, -1), 0],
      [P3arc(L, 44, 4, 22, 90, 155.8, 6), 0],
      [[[10, 53]], 1], [[[10, 61]], 1.5], [[[4, 61]], 1.5], [[[4, 45]], 1], [[[6, 45]], 1], [[[6, 36]], 2], [[[11, 36]], 2], [[[11, 45]], 1],
      [P3arc(L, 44, 4, 22, 177.4, 270, 10).slice(0, -1), 0]]);
    const hole = P3poly([[botRun(40, 66), 1], [[[66, 86]], 1.5], [[[40, 86]], 1.5]]);
    const cask = P3poly([[topRun, 0], [P3arc(Rt, 44, 4, 22, -90, 90, 10).slice(1, -1), 0], [botRun(Rt, L), 0], [P3arc(L, 44, 4, 22, 90, 270, 10).slice(1, -1), 0]]);
    const hoop = x => OBJ_poly([[x, top(x) - 1], [x + 5, top(x + 5) - 1], [x + 5, bot(x + 5)], [x, bot(x)]], 0);
    const underHoop = p => [21, 31, 70, 80].some(x => p[0] > x - .9 && p[0] < x + 5.9);
    let staves = ""; [-.62, -.22, .22, .62].forEach(f => { staves += P3runs(P3q([L + 1, 44 + f * 22], [M, 44 + f * 36], [Rt - 1, 44 + f * 22], 60), underHoop); });   /* (384.133) stopping at each hoop */
    CHAPTER_OBJ["Chapter 40: Storage of Distilled Spirits and Wines"] = {
      d,
      holes: [hole],
      base: "wood",
      plates: [
        ["wood", OBJ_rrect(14, 86, 78, 8, 2), { z: .2, bev: .6 }],                                       /* the rack's plank */
        ["wood", "M30 87V93M53 87V93M76 87V93", { ln: 1.4, cut: .7, paint: 0 }],
        ["wood", OBJ_rrect(22, 58, 18, 28, 0), { z: -.3, bev: .6 }],                                     /* the chocks */
        ["wood", OBJ_rrect(66, 58, 18, 28, 0), { z: -.3, bev: .6 }],
        ["wood", cask, { z: .3, bev: 1, dome: 2.2 }],                                                   /* the cask */
        ["wood", staves, { ln: 1.6, cut: .9, paint: 0 }],                                               /* its staves */
        ["rubber", hoop(21), { z: .7, bev: .5, dome: .4 }],                                              /* the iron hoops */
        ["rubber", hoop(31), { z: .7, bev: .5, dome: .4 }],
        ["rubber", hoop(70), { z: .7, bev: .5, dome: .4 }],
        ["rubber", hoop(80), { z: .7, bev: .5, dome: .4 }],
        ["cream", OBJ_circle(M, 19.5, 4), { dome: 1.6 }],                                                /* the bung */
        ["brass", OBJ_poly([[14, 45], [14, 53], [10, 53], [10, 61], [4, 61], [4, 45]], [0, 0, 1, 1.5, 1.5, 1]), { dome: 1 }],   /* the tap */
        ["brass", OBJ_rrect(6, 36, 5, 10, [2, 2, 0, 0]), { z: .4, gem: .8, gw: 1.6 }],                   /* its handle */
      ],
    };
  }

  /* ---- Chapter 50: Hazardous Materials—General Provisions - the NFPA 704 hazard diamond: four raised, faceted quadrants (health
     blue, flammability red, instability yellow, special white) in a black-framed diamond. No numbers: the colours and the facets carry it. ---- */
  {
    const q = (cx, cy) => OBJ_poly([[cx, cy - 18], [cx + 18, cy], [cx, cy + 18], [cx - 18, cy]], 2.5);
    CHAPTER_OBJ["Chapter 50: Hazardous Materials—General Provisions"] = {
      d: OBJ_poly([[50, 2], [98, 50], [50, 98], [2, 50]], 6),
      base: "rubber",
      plates: [
        ["rubber", OBJ_poly([[50, 2], [98, 50], [50, 98], [2, 50]], 6), { dome: .8 }],                   /* the frame */
        ["red", q(50, 27), { z: 1, bev: .8, gem: 1.4, gw: 5 }],                                         /* flammability */
        ["field", q(73, 50), { z: 1, bev: .8, gem: 1.4, gw: 5 }],                                       /* instability */
        ["glow", q(50, 73), { z: 1, bev: .8, gem: 1.4, gw: 5 }],                                       /* special */
        ["water", q(27, 50), { z: 1, bev: .8, gem: 1.4, gw: 5 }],                                       /* health */
      ],
    };
  }
}
