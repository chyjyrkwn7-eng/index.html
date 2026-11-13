/* Fire Code chapter objects - part 1 (build 384.66 format, round 3 pins): chapters 2, 3, 4, 6, 7, 8, 11, 12, 20 and 21, each drawn as a
   RAISED PIN of its object. The silhouette is the object; raised, recessed, domed, faceted and grooved parts carry the rest; every pin has
   to read in plain grey. See tools/chapter-objects/README.md. Every helper here is block-scoped, so nothing leaks into the other part files. */

/* ---- Chapter 2: Definitions - an open dictionary: two domed pages curling up from a grooved gutter, the lines of text cut into them, the
   page block's edge below them, the cover showing round the outside, a red ribbon marker hanging out of the bottom. ---- */
{
  const Q = (a, c, b, n) => { const o = []; for(let i = 0; i <= n; i++){ const t = i / n, u = 1 - t; o.push([u * u * a[0] + 2 * u * t * c[0] + t * t * b[0], u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]]); } return o; };
  const mir = p => [100 - p[0], p[1]], N = 10;
  const topL = Q([8, 21], [27, 9], [50, 25], N);     /* the left page's top edge, outer corner to gutter */
  const botL = Q([8, 72], [27, 63], [50, 77], N);    /* the left page's face ends here ... */
  const edgL = Q([8, 79], [27, 70], [50, 84], N);    /* ... and its block of pages here */
  const covL = Q([4, 84], [27, 76], [50, 90], N);    /* the cover's lower edge */
  const covR = covL.map(mir);                         /* outer (96, 84) to the middle */
  const yAt = (pts, x) => { for(let i = 0; i < pts.length - 1; i++){ const a = pts[i], b = pts[i + 1]; if((a[0] - x) * (b[0] - x) <= 0){ const t = (x - a[0]) / ((b[0] - a[0]) || 1); return a[1] + (b[1] - a[1]) * t; } } return pts[pts.length - 1][1]; };
  const RB0 = 57, RB1 = 64;                           /* the ribbon, on the right-hand page */
  const pts = [], rs = [];
  const add = (list, r) => list.forEach(p => { pts.push(p); rs.push(r); });
  add([[50, 25]], 1.5);
  add(topL.map(mir).reverse().slice(1, -1), 4);
  add([[92, 21]], 1.5); add([[96, 24]], 1.5);
  add([[96, 84]], 2);
  add(covR.slice(1).filter(p => p[0] > RB1 + .5), 4);
  add([[RB1, yAt(covR, RB1)]], 1); add([[RB1, 97]], 1); add([[(RB0 + RB1) / 2, 94]], 1); add([[RB0, 97]], 1); add([[RB0, yAt(covR, RB0)]], 1);
  add(covR.filter(p => p[0] < RB0 - .5 && p[0] > 50.5), 4);
  add([[50, 90]], 2);
  add(covL.slice().reverse().slice(1, -1), 4);
  add([[4, 84]], 2); add([[4, 24]], 1.5); add([[8, 21]], 1.5);
  add(topL.slice(1, -1), 4);
  const page = (top, bot) => OBJ_poly(top.concat(bot.slice().reverse()), top.map(() => 3).concat(bot.map(() => 3)).map((r, i, a) => (i === 0 || i === top.length - 1 || i === top.length || i === a.length - 1) ? 1.2 : r));
  const lines = (side) => { let s = ""; for(let k = 1; k <= 4; k++){ const a = [13, 21 + 9 * k + 2], c = [28, 10 + 9 * k + 1.5], b = [45, 25 + 9 * k]; const P = side ? [a, c, b].map(mir) : [a, c, b];
      s += "M" + P[0][0] + " " + P[0][1] + "Q" + P[1][0] + " " + P[1][1] + " " + P[2][0] + " " + P[2][1]; } return s; };
  const stack = (dy) => { const P = [[9, 74 + dy], [27, 65 + dy], [49, 79 + dy]], M = P.map(mir); return "M" + P[0].join(" ") + "Q" + P[1].join(" ") + " " + P[2].join(" ") + "M" + M[0].join(" ") + "Q" + M[1].join(" ") + " " + M[2].join(" "); };
  CHAPTER_OBJ["Chapter 2: Definitions"] = {
    d: OBJ_poly(pts, rs),
    base: "field",                                                                                        /* the cover */
    plates: [
      ["cream", page(topL, edgL), { z: .9, bev: .8 }],                                                   /* the left block of pages */
      ["cream", page(topL.map(mir), edgL.map(mir)), { z: .9, bev: .8 }],                                 /* the right */
      ["glow", page(topL, botL), { dome: 1.6 }],                                                         /* the left page, curling up */
      ["glow", page(topL.map(mir), botL.map(mir)), { dome: 1.6 }],                                       /* the right page */
      ["lite", lines(0) + lines(1), { ln: 1.5, cut: .55, paint: 0 }],                                    /* the lines of text */
      ["cream", stack(1.8) + stack(3.8), { ln: 1, cut: .45, paint: 0 }],                                 /* the edges of the pages */
      ["shade", "M50 26V82", { ln: 2.2, cut: 1.2, paint: 0 }],                                           /* the gutter */
      ["red", OBJ_poly([[RB0, yAt(edgL.map(mir), RB0) - 1], [RB1, yAt(edgL.map(mir), RB1) - 1], [RB1, 97], [(RB0 + RB1) / 2, 94], [RB0, 97]], [1, 1, 1, 1, 1]), { z: .5, bev: .6 }],   /* the ribbon */
    ],
  };
}

/* ---- Chapter 3: General Requirements - a portable fire extinguisher, redrawn (384.93 r9: Madison, "General requirements" - it read as a
   stack of grey levers on a red box, the hose hanging loose): the red cylinder with its domed shoulder, the white instruction label, the
   brass collar and the chrome valve head, the black squeeze lever over the black carry handle, the pressure gauge, and the black hose
   looping from the valve down the side to its horn, clipped to the body (the loop is a real hole). Built as one filleted union (OBJ_SDF). ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const body = S.union([S.box(31, 34, 36, 62, 5), S.ellipse(49, 37, 18, 12)], 0);
  const neck = S.box(44, 19, 10, 10, 1.5), valve = S.box(38, 13, 22, 8, 2.5);
  const lever = S.capsule(53, 10.6, 77, 5.6, 2.5), handle = S.capsule(55, 17.6, 79, 19, 2.5);
  const gauge = S.circle(32.5, 15.5, 5.4), gstem = S.box(33, 14, 7, 3, 1);
  const hose = S.tube([40, 21], [15, 22], [19, 62], () => 2.9, 22), horn = S.cone(19.4, 60, 21.6, 80, 3.2, 4.8), clip = S.box(21, 71, 12, 6, 1.5);
  const all = S.union([body, neck, valve, lever, handle, gauge, gstem, hose, horn, clip], 1.2), sil = S.trace(all, BB);
  CHAPTER_OBJ["Chapter 3: General Requirements"] = {
    d: sil.d, holes: sil.holes, base: "red",
    plates: [
      ["red", S.shape(body, BB), { dome: 1.7 }],                                                          /* the cylinder */
      ["cream", OBJ_rrect(33, 54, 32, 23, 2), { z: .5, bev: .6, col: "#F4F1EA" }],                         /* its label */
      ["cream", "M37 61H61M37 66H61M37 71H54", { ln: 1.5, cut: .6, paint: 0 }],                           /* its lines of instructions */
      ["deep", OBJ_rrect(31, 90, 36, 6, [0, 0, 5, 5]), { z: .3, bev: .5 }],                               /* the foot ring */
      ["rubber", S.shape(S.union([hose, horn], .6), BB), { dome: .9 }],                                    /* the hose and its horn */
      ["steel", S.shape(clip, BB), { z: .5, bev: .5 }],                                                    /* the clip */
      ["brass", S.shape(neck, BB), { z: .4, bev: .5 }],                                                    /* the collar */
      ["steel", S.shape(S.union([valve, gstem], .8), BB), { dome: .9 }],                                   /* the valve head */
      ["rubber", S.shape(handle, BB), { dome: .8 }],                                                      /* the carry handle */
      ["rubber", S.shape(lever, BB), { dome: .8 }],                                                       /* the squeeze lever */
      ["steel", S.shape(gauge, BB), { dome: .7 }],                                                        /* the gauge */
      ["cream", OBJ_circle(32.5, 15.5, 3.4), { z: -.4, bev: .4, col: "#F4F1EA" }],                        /* its face */
      ["red", "M32.5 15.5L35 13", { ln: 1, z: .3, bev: .3 }],                                             /* its needle */
    ],
  };
}

/* ---- Chapter 4: Emergency Planning and Preparedness - a megaphone, recoloured (384.93 r9: an orange horn with two white bands read
   as a traffic cone on its side): a white horn with a red rim at its mouth and a red collar where it meets the black rear housing, the
   dark opening with its grille rings, the black pistol grip with its grooves. ---- */
{
  const E = (cx, cy, rx, ry, a0, a1, n) => { const o = []; for(let i = 0; i <= n; i++){ const t = (a0 + (a1 - a0) * i / n) * Math.PI / 180; o.push([cx + rx * Math.cos(t), cy + ry * Math.sin(t)]); } return o; };
  const mouth = E(84, 46, 9, 31, -90, 90, 12);
  const cone = (x) => 10 + (x - 22) * (21 / 62);      /* the horn's half height at x: from the housing's own 10, no step (384.90) */
  const band = (x0, x1) => OBJ_poly([[x0, 46 - cone(x0)], [x1, 46 - cone(x1)], [x1, 46 + cone(x1)], [x0, 46 + cone(x0)]], 1);
  const pts = [[6, 36], [22, 36]].concat(mouth).concat([[48, 46 + cone(48)], [45, 89], [33, 89], [35, 46 + cone(35)], [22, 56], [6, 56]]);
  const rs = [4, .5].concat(mouth.map((p, i) => (i === 0 || i === mouth.length - 1) ? 1.5 : 4)).concat([1, 2.5, 2.5, 1, .5, 4]);
  CHAPTER_OBJ["Chapter 4: Emergency Planning and Preparedness"] = {
    d: OBJ_poly(pts, rs),
    col: "#F3F1EA", base: "field",
    plates: [
      ["field", OBJ_poly([[22, 36], [84, 15], [84, 77], [22, 56]], [.5, 1, 1, .5]), { dome: 2 }],       /* the white horn */
      ["red", band(22, 28), { z: .6, bev: .6 }],                                                            /* its collar */
      ["red", OBJ_ellipse(84, 46, 9, 31), { z: .8, bev: .7, dome: .6 }],                                    /* the red rim of its mouth */
      ["rubber", OBJ_ellipse(85, 46, 5, 26), { z: -1.8, bev: .9 }],                                         /* its opening */
      ["rubber", OBJ_ellipse(85, 46, 2.6, 15), { ln: 1.2, cut: .6, paint: 0 }],                             /* the grille */
      ["rubber", OBJ_rrect(6, 36, 16.6, 20, [4, .5, .5, 4]), { dome: 1.4 }],                                 /* the rear housing */
      ["rubber", OBJ_poly([[35, 57], [48, 61], [45, 89], [33, 89]], [1, 1, 2.5, 2.5]), { dome: 1 }],         /* the grip */
      ["rubber", "M36 70H45.5M35.6 76H45M35.2 82H44.5", { ln: 1.3, cut: .7, paint: 0 }],
    ],
  };
}

/* ---- Chapter 6: Building Services and Systems - an elevator: the frame with its two steel doors set into the doorway and the seam
   between them, the brass sill, over the doors the floor lantern with its lit up and down arrows, beside them the call station and its two buttons. ---- */
{
  CHAPTER_OBJ["Chapter 6: Building Services and Systems"] = {
    /* (384.68) the lantern and its arrows larger: at 26px the arrows are what says "elevator" (it read as a framed box) */
    d: OBJ_poly([[14, 19], [26, 19], [26, 1], [66, 1], [66, 19], [78, 19], [78, 44], [94, 44], [94, 74], [78, 74], [78, 95], [14, 95]], [4, 1, 4, 4, 1, 4, 1, 4, 4, 1, 3, 3]),
    base: "brass",
    plates: [
      ["brass", OBJ_rrect(14, 19, 64, 76, [4, 4, 3, 3]), { dome: .8 }],                                        /* the frame */
      ["steel", OBJ_rrect(21, 27, 50, 68, [2, 2, 0, 0]), { z: -1.1, bev: .8 }],                                /* the doorway */
      ["steel", OBJ_rrect(22.5, 28.5, 22.5, 66.5, 1), { z: .4, bev: .6, dome: .6 }],                           /* the doors */
      ["steel", OBJ_rrect(47, 28.5, 22.5, 66.5, 1), { z: .4, bev: .6, dome: .6 }],
      ["rubber", "M46 29V90", { ln: 3, cut: 1 }],                                                           /* the gap where they meet */
      ["steel", OBJ_rrect(19, 91, 54, 4, 1), { z: .5, bev: .5 }],                                              /* the sill */
      ["rubber", OBJ_rrect(26, 1, 40, 20, [4, 4, 0, 0]), { z: .3 }],                                             /* the floor lantern */
      ["rubber", OBJ_rrect(29, 3.5, 34, 15, 2), { z: -.7, bev: .6 }],
      ["glow", OBJ_poly([[31.5, 16], [38.5, 6], [45.5, 16]], 1.2), { gem: 1.2, gw: 2 }],                       /* up */
      ["glow", OBJ_poly([[46.5, 6], [60.5, 6], [53.5, 16]], 1.2), { gem: 1.2, gw: 2 }],                        /* down */
      ["brass", OBJ_rrect(76, 44, 18, 30, [0, 4, 4, 0]), { z: .3 }],                                            /* the call station */
      ["rubber", OBJ_rrect(81, 48, 9, 22, 4.5), { z: -.6, bev: .6 }],
      ["glow", OBJ_circle(85.5, 53.5, 2.8), { dome: 1.2 }],                                                    /* its two buttons */
      ["glow", OBJ_circle(85.5, 64.5, 2.8), { dome: 1.2 }],
    ],
  };
}

/* ---- Chapter 7: Fire and Smoke Protection Features - a fire wall: a section of brickwork in stretcher bond, the courses toothed at both
   ends and the top course stepped where the wall is still going up, every brick raised out of the mortar. ---- */
{
  const Y = [5, 23, 41, 59, 77, 95];
  const even = [[4, 30], [32.5, 58.5], [61, 88]], odd = [[12, 25], [27.5, 53.5], [56, 82], [84.5, 96]];
  const tones = ["red", "red", "field", "red", "red", "red", "shade", "red", "red", "field", "red", "red", "red", "field", "red", "red", "shade"];
  const bricks = []; let n = 0;
  for(let r = 0; r < 5; r++) (r % 2 ? odd : r ? even : even.slice(0, 2)).forEach(b => {
    const x0 = b[0] + (b[0] <= 12 ? 0 : 1.25), x1 = b[1] - (b[1] >= 88 || (!r && b[1] > 58) ? 0 : 1.25), y0 = Y[r] + (r ? 1.25 : 0), y1 = Y[r + 1] - (r < 4 ? 1.25 : 0);
    bricks.push([tones[n++ % tones.length], OBJ_rrect(x0, y0, x1 - x0, y1 - y0, 1.6), { z: 1, bev: .8, dome: .5 }]);
  });
  CHAPTER_OBJ["Chapter 7: Fire and Smoke Protection Features"] = {
    d: OBJ_poly([[4, 5], [58.5, 5], [58.5, 23], [96, 23], [96, 41], [88, 41], [88, 59], [96, 59], [96, 77], [88, 77], [88, 95], [4, 95], [4, 77], [12, 77], [12, 59], [4, 59], [4, 41], [12, 41], [12, 23], [4, 23]],
      [2, 2, 1, 2, 2, 1, 1, 2, 2, 1, 2, 2, 1, 2, 2, 1, 1, 2, 2, 1]),
    base: "cream",                                                                                         /* the mortar */
    plates: bricks,
  };
}

/* ---- Chapter 8: Interior Finish, Decorative Materials and Furnishings - a leather armchair, front on: the tall back with its
   channel-stitched cushion, the two rolled arms with their scrolled fronts, the domed seat cushion, dark piping round the cushions and the
   scrolls, the skirt and the dark turned legs. ---- */
{
  CHAPTER_OBJ["Chapter 8: Interior Finish, Decorative Materials and Furnishings"] = {
    d: "M20 36" + OBJ_chain([[20, 36], [20, 8], [80, 8], [80, 36]], [0, 13, 13, 0]) + "A10 10 0 0 1 96 44" +
       OBJ_chain([[96, 44], [96, 84], [88, 84], [87, 94], [81, 94], [80, 84], [20, 84], [19, 94], [13, 94], [12, 84], [4, 84], [4, 44]], [0, 2, 1, 1.5, 1.5, 1, 1, 1.5, 1.5, 1, 2, 0]) + "A10 10 0 0 1 20 36Z",
    base: "leather",                                                                                              /* warm brown leather */
    plates: [
      ["leather", OBJ_rrect(20, 8, 60, 50, [13, 13, 0, 0]), { dome: 1.2 }],                                     /* the back */
      ["leather", OBJ_rrect(27, 14, 46, 38, [10, 10, 3, 3]), { z: .5, bev: .8, dome: 1.2 }],                    /* its cushion */
      ["rubber", OBJ_rrect(27, 14, 46, 38, [10, 10, 3, 3]), { ln: 1.4, z: .3, bev: .4 }],                    /* its piping */
      ["rubber", "M42.5 20V46M57.5 20V46", { ln: 1.3, cut: .8 }],                                            /* its channel stitching */
      ["leather", OBJ_rrect(6, 70, 88, 14, 3), { z: .2 }],                                                      /* the skirt */
      ["rubber", "M8 76H92", { ln: 1.3, cut: .6 }],
      ["leather", OBJ_rrect(22, 52, 56, 19, 5), { z: .6, bev: .8, dome: 1.4 }],                                 /* the seat cushion */
      ["rubber", OBJ_rrect(22, 52, 56, 19, 5), { ln: 1.4, z: .3, bev: .4 }],                                 /* its piping */
      ["leather", OBJ_rrect(4, 34, 20, 50, [10, 10, 2, 2]), { z: .7, bev: .8, dome: 1.6 }],                      /* the arms */
      ["leather", OBJ_rrect(76, 34, 20, 50, [10, 10, 2, 2]), { z: .7, bev: .8, dome: 1.6 }],
      ["leather", OBJ_circle(14, 45, 6.5), { z: .5, bev: .7, dome: .8 }],                                        /* their scrolled fronts */
      ["leather", OBJ_circle(86, 45, 6.5), { z: .5, bev: .7, dome: .8 }],
      ["rubber", OBJ_circle(14, 45, 6.5), { ln: 1.3, z: .3, bev: .4 }],                                       /* their piping */
      ["rubber", OBJ_circle(86, 45, 6.5), { ln: 1.3, z: .3, bev: .4 }],
      ["rubber", OBJ_poly([[12, 84], [20, 84], [19, 94], [13, 94]], [.5, .5, 1.5, 1.5]), { dome: .8 }],      /* the legs */
      ["rubber", OBJ_poly([[80, 84], [88, 84], [87, 94], [81, 94]], [.5, .5, 1.5, 1.5]), { dome: .8 }],
    ],
  };
}

/* ---- Chapter 11: Construction Requirements for Existing Buildings - a classical building: the pediment with its sunk tympanum, the
   cornice, four fluted columns with their capitals and bases standing out of the shadowed portico, the two steps. ---- */
{
  const cols = [23, 41, 59, 77], parts = [];
  cols.forEach(c => parts.push(["glow", OBJ_rrect(c - 5, 41, 10, 38, 1), { z: 1.5, bev: .6, dome: 1 }]));
  let flutes = ""; cols.forEach(c => { flutes += "M" + (c - 2.4) + " 45V75M" + (c + 2.4) + " 45V75"; });
  cols.forEach(c => parts.push(["glow", OBJ_rrect(c - 6.5, 37, 13, 5.5, 1), { z: 1.7, bev: .5 }]));
  cols.forEach(c => parts.push(["glow", OBJ_rrect(c - 6.5, 78, 13, 4, 1), { z: 1.7, bev: .5 }]));
  CHAPTER_OBJ["Chapter 11: Construction Requirements for Existing Buildings"] = {
    d: OBJ_poly([[50, 3], [96, 28], [96, 37], [86, 37], [86, 82], [91, 82], [91, 88], [96, 88], [96, 94], [4, 94], [4, 88], [9, 88], [9, 82], [14, 82], [14, 37], [4, 37], [4, 28]],
      [3, 2, 1.5, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1.5, 2]),
    base: "cream",
    plates: [
      ["cream", OBJ_poly([[50, 3], [96, 28], [4, 28]], [3, 2, 2]), { z: .3 }],                                 /* the pediment */
      ["steel", OBJ_poly([[50, 11], [81, 26], [19, 26]], [2, 1.5, 1.5]), { z: -1, bev: .7 }],                  /* its tympanum */
      ["cream", OBJ_rrect(4, 27.5, 92, 9.5, 1.5), { z: .6, bev: .6 }],                                          /* the cornice */
      ["lite", "M6 32.5H94", { ln: 1.3, cut: .6, paint: 0 }],
      ["ink", OBJ_rrect(14, 37, 72, 45, 0), { z: -1.5, bev: .8 }],                                              /* the portico, in shadow */
    ].concat(parts).concat([
      ["cream", flutes, { ln: 1.3, cut: .6, paint: 0 }],                                                        /* the flutes */
      ["cream", OBJ_rrect(9, 82, 82, 6, 1), { z: .5, bev: .6 }],                                                 /* the steps */
      ["steel", OBJ_rrect(4, 88, 92, 6, [1, 1, 2, 2]), { z: .2, bev: .6 }],
    ]),
  };
}

/* ---- Chapter 12: Energy Systems - a battery cell lying on its side: the domed casing, the brass positive end with its terminal nub and a
   groove where it meets the casing, an embossed plus by it and an embossed minus at the other end. ---- */
{
  CHAPTER_OBJ["Chapter 12: Energy Systems"] = {
    d: OBJ_poly([[6, 28], [84, 28], [84, 40], [94, 40], [94, 60], [84, 60], [84, 72], [6, 72]], [6, 4, 1, 3, 3, 1, 4, 6]),
    base: "water",
    plates: [
      ["water", OBJ_rrect(6, 28, 64, 44, [6, 0, 0, 6]), { dome: 2.2 }],                                      /* the casing */
      ["brass", OBJ_rrect(70, 28, 14, 44, [0, 4, 4, 0]), { dome: 2.2 }],                                      /* the positive end */
      ["brass", OBJ_rrect(84, 40, 10, 20, [0, 3, 3, 0]), { dome: 1.4 }],                                      /* its nub */
      ["shade", "M70 29V71", { ln: 2, cut: 1, paint: 0 }],                                                    /* the seam */
      ["water", "M50 50H62M56 44V56", { ln: 4, z: 1.2, bev: .9 }],                                             /* the plus */
      ["water", "M14 50H24", { ln: 4, z: 1.2, bev: .9 }],                                                      /* the minus */
    ],
  };
}

/* ---- Chapter 20: Aviation Facilities - an airliner from above, nose up: the domed fuselage with its cockpit glazing, the swept wings
   with their flap lines, two engine pods under them, the tailplane and the fin's ridge. ---- */
{
  /* the fuselage 16 wide and the wings deep at the root: the back's title is laid across the wings and the body */
  const F = 8, LE = x => 33 + (x - 50 - F) * (14 / 37);
  const wing = s => OBJ_poly([[50 + s * F, 33], [50 + s * 45, 47], [50 + s * 45, 59], [50 + s * F, 61]], [1, 3, 3, 1]);
  const tail = s => OBJ_poly([[50 + s * F, 77], [50 + s * 26, 87], [50 + s * 26, 94], [50 + s * F, 90]], [1, 2.5, 2.5, 1]);
  const half = s => [[50 + s * F, 33], [50 + s * 22, LE(72)], [50 + s * 22, 31], [50 + s * 30, 31], [50 + s * 30, LE(80)], [50 + s * 45, 47], [50 + s * 45, 59], [50 + s * F, 61],
    [50 + s * F, 77], [50 + s * 26, 87], [50 + s * 26, 94], [50 + s * F, 90], [50 + s * F, 95]];
  const R = [1, 1, 3.5, 3.5, 1, 3, 3, 1, 1, 2.5, 2.5, 1, 3];
  CHAPTER_OBJ["Chapter 20: Aviation Facilities"] = {
    d: "M42 11A8 8 0 0 1 58 11" + OBJ_chain([[58, 11]].concat(half(1)).concat(half(-1).reverse()).concat([[42, 11]]), [0].concat(R).concat(R.slice().reverse()).concat([0])) + "Z",
    base: "steel",
    plates: [
      ["steel", wing(-1), { dome: .8 }],                                                                        /* the wings */
      ["steel", wing(1), { dome: .8 }],
      ["steel", "M39 56.5L9 55M61 56.5L91 55", { ln: 1.2, cut: .55, paint: 0 }],                            /* their flaps */
      ["steel", tail(-1), { dome: .6 }],                                                                        /* the tailplane */
      ["steel", tail(1), { dome: .6 }],
      ["field", OBJ_rrect(20, 31, 8, 17, 3.5), { z: .6, bev: .6, dome: 1 }],                                      /* the engines */
      ["field", OBJ_rrect(72, 31, 8, 17, 3.5), { z: .6, bev: .6, dome: 1 }],
      ["ink", OBJ_rrect(21.5, 32, 5, 3, 1.4), { z: -.5, bev: .4 }],                                            /* their intakes */
      ["ink", OBJ_rrect(73.5, 32, 5, 3, 1.4), { z: -.5, bev: .4 }],
      ["glow", "M42 11A8 8 0 0 1 58 11V91Q58 95 54 95H46Q42 95 42 91Z", { z: .8, bev: 1, dome: 1.8 }],          /* the fuselage */
      ["glass", OBJ_poly([[44.5, 13], [55.5, 13], [54.5, 19], [45.5, 19]], 1.5), { z: -.5, bev: .5, dome: .5 }],   /* the cockpit */
      ["field", "M50 76V93", { ln: 3.2, z: .9, bev: .8 }],                                                         /* the fin */
    ],
  };
}

/* ---- Chapter 21: Dry Cleaning - a shirt on a hanger: the hanger's hook over the collar, the two raised collar points, the placket with
   its domed buttons, the chest pocket, the set-in sleeves with their seams and cuffs, the curved shirt tail. ---- */
{
  const C = [[50, 25], [50, 13]];
  for(let a = 190; a <= 400; a += 15){ const t = a * Math.PI / 180; C.push([56 + 6 * Math.cos(t), 13 + 6 * Math.sin(t)]); }
  const side = (k) => C.map((p, i) => { const q = C[Math.max(0, i - 1)], r = C[Math.min(C.length - 1, i + 1)], tx = r[0] - q[0], ty = r[1] - q[1], l = Math.hypot(tx, ty) || 1; return [p[0] - ty / l * k, p[1] + tx / l * k]; });
  const hw = 2.8, Out = side(-hw), In = side(hw);   /* the outside of the curl, its inside */
  const hookOut = Out.slice(1), hookIn = In.slice(1).reverse();
  const pts = [[38, 22], [50 - hw, 22]].concat(hookOut).concat(hookIn).concat([[50 + hw, 22], [62, 22], [82, 28], [96, 47], [88, 56], [78, 47], [78, 90], [70, 94], [30, 94], [22, 90], [22, 47], [12, 56], [4, 47], [18, 28]]);
  const rs = [2, 1].concat(hookOut.map((p, i) => i === hookOut.length - 1 ? 2.5 : 2)).concat(hookIn.map((p, i) => i === 0 ? 2.5 : 2)).concat([1, 2, 3, 2.5, 2.5, 1, 3, 3, 3, 3, 1, 2.5, 2.5, 3]);
  const hook = OBJ_poly([[50 - hw, 26]].concat(hookOut).concat(hookIn).concat([[50 + hw, 26]]), 2);
  CHAPTER_OBJ["Chapter 21: Dry Cleaning"] = {
    d: OBJ_poly(pts, rs),
    plates: [
      ["steel", hook, { dome: 1 }],                                                                             /* the hook */
      ["ink", OBJ_poly([[42, 22], [58, 22], [50, 29]], [1, 1, 1.5]), { z: -1, bev: .7 }],                       /* the neck */
      ["lite", OBJ_poly([[37, 22], [49.5, 29], [43, 39]], [1.5, 1.5, 2]), { z: .8, bev: .6, dome: .5 }],         /* the collar points */
      ["lite", OBJ_poly([[63, 22], [50.5, 29], [57, 39]], [1.5, 1.5, 2]), { z: .8, bev: .6, dome: .5 }],
      ["body", OBJ_rrect(46.5, 31, 7, 63, [1, 1, 0, 0]), { z: .4, bev: .5 }],                                    /* the placket */
      ["cream", OBJ_circle(50, 44, 2.7), { dome: 1.3 }],                                                         /* its buttons */
      ["cream", OBJ_circle(50, 57, 2.7), { dome: 1.3 }],
      ["cream", OBJ_circle(50, 70, 2.7), { dome: 1.3 }],
      ["cream", OBJ_circle(50, 83, 2.7), { dome: 1.3 }],
      ["body", OBJ_rrect(59, 46, 12, 13, [0, 0, 2.5, 2.5]), { z: .5, bev: .5 }],                                 /* the pocket */
      ["field", "M79 30L77 47M21 30L23 47", { ln: 1.3, cut: .6, paint: 0 }],                                     /* the sleeve seams */
      ["body", OBJ_poly([[96, 47], [88, 56], [84.5, 52.5], [92.5, 43.5]], 1), { z: .5, bev: .5 }],               /* the cuffs */
      ["body", OBJ_poly([[4, 47], [12, 56], [15.5, 52.5], [7.5, 43.5]], 1), { z: .5, bev: .5 }],
    ],
  };
}
