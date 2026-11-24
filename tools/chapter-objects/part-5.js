/* Fire Code chapter objects - PART 5 (build 384.66 round 3 format): ten chapters drawn as RAISED PINS. Each entry is the pin's silhouette
   and its parts; identity is the silhouette and the sculpture (raised, recessed, domed, faceted, grooved), never a sticker. Colours are the
   object's own (Madison: "make the color of stuff relevant, you don't need to keep the old colors"): a black bomb, a blue drop, a red map
   pin, a brown clipboard. See tools/chapter-objects/README.md. */

/* ---- Chapter 64: Pyrophoric Materials - a burning rock (it ignites on contact with air): a faceted dark stone with glowing cracks cut
   into it, and three tongues of flame rising off it, the middle one tallest, a hot core inside. ---- */
{
  /* (art9) a flame's corners rounded (convex 1.8, concave 4), as OBJ_poly rounded them, before it is cut at the stone */
  const RND = p => OBJ_SDF.grow(OBJ_SDF.grow(OBJ_SDF.grow(OBJ_SDF.grow(p, -1.8), 1.8), 4), -4);
  CHAPTER_OBJ["Chapter 64: Pyrophoric Materials"] = {
    d: OBJ_poly([[12, 93], [5, 76], [13, 60], [20, 57.12], [13, 42], [21, 21], [33, 37], [38, 20], [50, 2], [62, 20], [67, 37], [79, 21], [87, 42], [80, 57.12],
                 [87, 60], [95, 76], [88, 93]],
      [5, 5, 4, 1.5, 6, 2, 3, 5, 2.2, 5, 3, 2, 6, 1.5, 4, 5, 5]),
    base: "rubber",
    plates: [
      /* (384.90) the flames flame-orange, not the tent's red: with the outline following the stone's edge the two outlines came to 0.81
         alike, and the same red made them twins (check-b384-objbadges (6)) */
      /* (art9) Madison: "There's a lot of spots all over that just don't look right." The flames' hearts ran on under the stone and a
         part's relief is added to what is under it, so their round feet stood up as bumps along the stone's top. They now stop where
         the stone starts. */
      ["red", OBJ_rrect(0, 0, 100, 62, 0), { col: "#F36A21" }],                                                                                       /* the flames */
      ["hot", OBJ_SDF.shape(OBJ_SDF.minus(RND(OBJ_SDF.poly([[38, 58], [37, 42], [44, 30], [50, 17], [56, 30], [63, 42], [62, 58]])), OBJ_SDF.poly([[5, 76], [13, 60], [30, 53], [50, 57], [70, 53], [87, 60], [95, 76], [88, 93], [12, 93]])), [0, 0, 100, 100]), { z: .6, bev: .9, dome: 1.2 }],   /* the hot inner flame */
      ["glow", OBJ_SDF.shape(OBJ_SDF.minus(RND(OBJ_SDF.poly([[44, 58], [45, 47], [50, 36], [55, 47], [56, 58]])), OBJ_SDF.poly([[5, 76], [13, 60], [30, 53], [50, 57], [70, 53], [87, 60], [95, 76], [88, 93], [12, 93]])), [0, 0, 100, 100]), { z: .5, bev: .7, dome: .8 }],                             /* its white-hot core */
      ["hot", OBJ_SDF.shape(OBJ_SDF.minus(RND(OBJ_SDF.poly([[21, 58], [19, 46], [23, 34], [30, 48], [30, 58]])), OBJ_SDF.poly([[5, 76], [13, 60], [30, 53], [50, 57], [70, 53], [87, 60], [95, 76], [88, 93], [12, 93]])), [0, 0, 100, 100]), { z: .4, bev: .7, dome: .8 }],                             /* the side flames' hearts */
      ["hot", OBJ_SDF.shape(OBJ_SDF.minus(RND(OBJ_SDF.poly([[79, 58], [81, 46], [77, 34], [70, 48], [70, 58]])), OBJ_SDF.poly([[5, 76], [13, 60], [30, 53], [50, 57], [70, 53], [87, 60], [95, 76], [88, 93], [12, 93]])), [0, 0, 100, 100]), { z: .4, bev: .7, dome: .8 }],
      ["rubber", OBJ_poly([[5, 76], [13, 60], [30, 53], [50, 57], [70, 53], [87, 60], [95, 76], [88, 93], [12, 93]], [5, 4, 3, 3, 3, 4, 5, 5, 5]), { z: .8, bev: 1.1, gem: 1.8, gw: 6 }],   /* the stone, faceted */
      ["hot", "M24 66L36 75L31 87M62 64L71 74L83 79M50 70L53 84", { ln: 2.8, cut: .8 }],                                                               /* its glowing cracks */
    ],
  };
}

/* ---- Chapter 65: Pyroxylin (Cellulose Nitrate) Plastics - a reel of nitrate film: the reel with its five round windows (real holes), the
   raised hub and spindle, the rim; the film strip running off the bottom with its perforations pressed in. ---- */
{
  const C = [40, 42], R = 37, Y0 = 59, Y1 = 79, f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const xj = C[0] + Math.sqrt(R * R - (Y0 - C[1]) * (Y0 - C[1]));          /* where the strip's top edge meets the reel */
  const a0 = Math.atan2(Y0 - C[1], xj - C[0]), a1 = Math.PI / 2, am = (a0 + a1 - 2 * Math.PI) / 2;   /* the long way round, over the top */
  const mid = [C[0] + R * Math.cos(am), C[1] + R * Math.sin(am)];
  /* (384.79) six small windows near the rim, not five big ones round the hub: the back's title had no room between them */
  const holes = []; for(let k = 0; k < 6; k++){ const t = -Math.PI / 2 + k * 2 * Math.PI / 6; holes.push(OBJ_circle(C[0] + 26.5 * Math.cos(t), C[1] + 26.5 * Math.sin(t), 4.2)); }
  let perf = ""; for(const x of [76, 85]) for(const y of [61.5, 71.5]) perf += OBJ_rrect(x, y, 5.5, 5.5, 1.2);
  CHAPTER_OBJ["Chapter 65: Pyroxylin (Cellulose Nitrate) Plastics"] = {
    d: "M" + f([C[0], Y1]) + OBJ_chain([[C[0], Y1], [96, Y1], [96, Y0], [xj, Y0]], [0, 2, 2, 0]) + "A" + R + " " + R + " 0 0 0 " + f(mid) + "A" + R + " " + R + " 0 0 0 " + f([C[0], Y1]) + "Z",
    holes,
    base: "steel",
    plates: [
      /* (art9) the film strip leaves the reel from under its rim: drawn on under the reel, its top edge and end showed through the reel's face as a step */
      ["wood", OBJ_SDF.shape(OBJ_SDF.minus(OBJ_SDF.box(40, Y0, 56, Y1 - Y0, 2), OBJ_SDF.circle(C[0], C[1], R)), [0, 0, 100, 100]), { dome: .6 }],   /* the film strip */
      ["rubber", perf, { z: -.9, bev: .5 }],                                                         /* its perforations */
      ["steel", OBJ_circle(C[0], C[1], R), { dome: .4 }],                                          /* the reel */
      ["steel", OBJ_circle(C[0], C[1], R - 5.5), { z: -.7, bev: .9 }],                             /* its face, inside the rim */
      ["brass", OBJ_circle(C[0], C[1], 9.5), { z: 1.1, bev: .9, dome: .8 }],                        /* the hub */
      ["rubber", OBJ_circle(C[0], C[1], 4), { dome: 1.3 }],                                         /* the spindle */
    ],
  };
}

/* ---- Chapter 66: Unstable (Reactive) Materials - a round bomb: the domed sphere, the faceted steel cap, the fuse and its spark.
   (art10) Madison circled the spark: a gold star stuck over the fuse's end with a white disc. A lit fuse is a cord that burns at its
   tip and throws sparks: the fuse is a twisted cord now, bending a little as a cord does, its tip a glowing ember, and from the ember a
   starburst - a white-hot flash and nine thin rays of different lengths in warm yellow, all one piece with the outline. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const C = [41, 60], R = 34, s = Math.SQRT1_2, u = [s, -s], n = [s, s], W = 9.5, CAP = 45;
  const P = (t, w) => [C[0] + t * u[0] + w * n[0], C[1] + t * u[1] + w * n[1]], f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const a = Math.sqrt(R * R - W * W);
  /* the fuse: a cord on a gentle curve from the cap's end to its burning tip */
  const F0 = P(CAP - .6, 0), F1 = P(51.5, 2.4), T = P(57.6, -.6);
  const bz = t => [(1 - t) * (1 - t) * F0[0] + 2 * (1 - t) * t * F1[0] + t * t * T[0], (1 - t) * (1 - t) * F0[1] + 2 * (1 - t) * t * F1[1] + t * t * T[1]];
  const fuse = S.tube(F0, F1, T, t => 2.55 - .35 * t, 22);
  /* the burst: a flash at the tip and nine rays, their angles from the fuse's own direction and their lengths uneven */
  const dT = [T[0] - bz(.94)[0], T[1] - bz(.94)[1]], dl = Math.hypot(dT[0], dT[1]), a0 = Math.atan2(dT[1] / dl, dT[0] / dl);
  const FC = [T[0] + dT[0] / dl * 1.4, T[1] + dT[1] / dl * 1.4];
  const RAYS = [[-135, 6], [-108, 10.5], [-81, 7], [-54, 12.5], [-27, 8], [0, 13], [27, 7.5], [54, 11.5], [81, 6.5], [108, 10], [135, 6]];   /* evenly round (a narrow V between two rays at their roots read as a notch) */
  const rays = RAYS.map(([g, L]) => { const t = a0 + g * Math.PI / 180, e = [FC[0] + Math.cos(t) * (2.4 + L), FC[1] + Math.sin(t) * (2.4 + L)]; return S.cone(FC[0], FC[1], e[0], e[1], 1, .26); });
  /* the flash: a four-pointed glint (a twinkle), its points square to the fuse and across it */
  const glint = S.union([0, 90, 180, 270].map(g => { const t = a0 + (g + 45) * Math.PI / 180, L = g % 180 ? 6.4 : 7.8; return S.cone(FC[0], FC[1], FC[0] + Math.cos(t) * L, FC[1] + Math.sin(t) * L, 1.45, .2); }).concat([S.circle(FC[0], FC[1], 1.7)]), .7);
  const flash = S.circle(FC[0], FC[1], 2.2), burst = S.union([glint].concat(rays), .35);
  const body = "M" + f(P(a, W)) + "A" + R + " " + R + " 0 0 1 " + f(P(-R, 0)) + "A" + R + " " + R + " 0 0 1 " + f(P(a, -W));
  const capF = S.poly([P(a - 5, -W), P(CAP, -W), P(CAP, W), P(a - 5, W)]);
  const all = S.union([S.circle(C[0], C[1], R), S.grow(S.grow(capF, -1), 1), S.union([fuse, burst], .8)], .9);
  /* the cord's twist: short grooves across it, slanted, every 1.7 along it */
  const e0 = [(T[0] - F0[0]), (T[1] - F0[1])], el = Math.hypot(e0[0], e0[1]), ex = e0[0] / el, ey = e0[1] / el;
  const twist = (x, y) => { const sx = (x - F0[0]) * ex + (y - F0[1]) * ey, sw = (x - F0[0]) * -ey + (y - F0[1]) * ex, ph = ((sx + .75 * sw) % 1.9 + 1.9) % 1.9; return Math.abs(ph - .95) - .38; };
  CHAPTER_OBJ["Chapter 66: Unstable (Reactive) Materials"] = {
    d: S.shape(all, BB),
    base: "rubber",
    plates: [
      ["rubber", OBJ_circle(C[0], C[1], R), { dome: 4 }],                                                   /* the sphere */
      /* (art9) Madison: "There's a lot of spots all over that just don't look right." The cap ran 5 on over the sphere and took its
         curve as an arc across it (a part's relief is added to what is under it). It now stands out of the sphere from its edge. */
      ["brass", S.shape(S.minus(S.inter(all, S.grow(capF, .6)), S.circle(C[0], C[1], R)), BB), { z: .5, bev: .7, gem: .9, gw: 2.2 }],   /* the cap */
      ["brass", "M" + f(P(a + 3.5, -W)) + "L" + f(P(a + 3.5, W)), { ln: 1.4, cut: .7, paint: 0 }],         /* its seam */
      ["cream", S.shape(S.minus(S.inter(all, S.grow(fuse, .6)), S.union([capF, glint], 0)), BB), { dome: .9, col: "#E3D3B0" }],   /* the fuse, a round cord from the cap's end to the flash */
      ["cream", S.loops(S.inter(S.minus(fuse, S.union([capF, glint], 0)), twist), BB).map(S.pathOf).join(""), { col: "#B9A27A" }],   /* its twist: the strands, slanting round it */
      ["hot", S.shape(S.minus(S.inter(fuse, S.circle(T[0], T[1], 3.3)), glint), BB), { col: "#FF6A1C" }],   /* its tip, an ember */
      ["glow", S.loops(S.minus(S.inter(all, S.grow(burst, .5)), S.union([fuse, glint], 0)), BB).map(S.pathOf).join(""), { z: .5, bev: .8, col: "#FFD23A" }],   /* the sparks, */
      ["glow", S.loops(S.minus(S.inter(all, S.grow(burst, .5)), S.union([fuse, S.circle(FC[0], FC[1], 8.5)], 0)), BB).map(S.pathOf).join(""), { col: "#FF9A26" }],   /* cooling to orange as they fly */
      ["glow", S.shape(glint, BB), { z: .7, bev: .7, dome: .5, col: "#FFF8E0" }],                            /* the white-hot glint at the tip */
    ],
  };
}

/* ---- Chapter 67: Water-Reactive Solids and Liquids - a drop of water struck through by a raised, faceted spark: water meeting the thing
   it sets off. ---- */
{
  const C = [50, 62], R = 32, T = [50, 3], d = Math.hypot(T[0] - C[0], T[1] - C[1]), ph = Math.acos(R / d);
  const Rt = [C[0] + R * Math.sin(ph), C[1] - R * Math.cos(ph)], Lt = [C[0] - R * Math.sin(ph), C[1] - R * Math.cos(ph)], f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const sil = "M" + f(Rt) + "A" + R + " " + R + " 0 0 1 " + f([C[0], C[1] + R]) + "A" + R + " " + R + " 0 0 1 " + f(Lt) + OBJ_chain([Lt, T, Rt], [0, 3.5, 0]) + "Z";
  const BOLT = [[54, 26], [67, 26], [57.5, 49], [69, 49], [39.5, 89], [49, 60], [40, 60]].map(([x, y]) => [+(50 + (x - 54.5) * .86).toFixed(2), +(58.5 + (y - 58) * .86).toFixed(2)]);
  CHAPTER_OBJ["Chapter 67: Water-Reactive Solids and Liquids"] = {
    d: sil,
    base: "water",
    plates: [
      ["water", sil, { dome: 2.4 }],                                                                          /* the drop */
      /* (art10) Madison circled the bolt: crude and flat - a thin upper stroke, a wide step, a long thin spike. A classic bolt now: an
         upper bar of one width slanting down to a level step, the lower bar leaving the step at the same width and tapering to a
         sharp point; sharp outer corners, its edges chamfered in planes (gold catching the light along them), centred in the drop */
      ["brass", OBJ_poly(BOLT, [.6, .6, .9, .6, .3, .9, .6]), { z: 1.1, bev: .7, gem: 1, gw: 2.3 }],   /* the bolt */
    ],
  };
}

/* ---- Chapter 80: Referenced Standards - a stack of four bound volumes, spines out: each a rounded spine with gold bands at its ends and
   a label panel pressed into its middle. ---- */
{
  const B = [[20, 76, 26, 42], [8, 84, 42, 59], [14, 92, 59, 76], [5, 89, 76, 94]];   /* x0, x1, y0, y1, top to bottom */
  /* (384.68) the largest, bottom volume in a bookbinder's green (col below), not brown: brown made the stack the armchair's twin */
  const tone = ["red", "water", "wood", "field"];
  const pts = [[B[0][0], B[0][2]], [B[0][1], B[0][2]]];
  for(let i = 0; i < 3; i++){ pts.push([B[i][1], B[i][3]]); pts.push([B[i + 1][1], B[i + 1][2]]); }
  pts.push([B[3][1], B[3][3]]); pts.push([B[3][0], B[3][3]]);
  for(let i = 3; i > 0; i--){ pts.push([B[i][0], B[i][2]]); pts.push([B[i - 1][0], B[i - 1][3]]); }
  const plates = [];
  B.forEach((b, i) => {
    const [x0, x1, y0, y1] = b, h = y1 - y0, m = (x0 + x1) / 2;
    plates.push([tone[i], OBJ_rrect(x0, y0, x1 - x0, h, 2.5), { z: .2, bev: .8, dome: 1.1 }]);
    plates.push(["brass", "M" + (x0 + 5.5) + " " + (y0 + 1.5) + "V" + (y1 - 1.5) + "M" + (x0 + 10) + " " + (y0 + 1.5) + "V" + (y1 - 1.5) +
                          "M" + (x1 - 5.5) + " " + (y0 + 1.5) + "V" + (y1 - 1.5) + "M" + (x1 - 10) + " " + (y0 + 1.5) + "V" + (y1 - 1.5), { ln: 2, z: .5, bev: .4 }]);
    plates.push(["cream", OBJ_rrect(m - 11, y0 + h / 2 - 3.5, 22, 7, 1.5), { z: -.5, bev: .5 }]);
  });
  CHAPTER_OBJ["Chapter 80: Referenced Standards"] = {
    d: OBJ_poly(pts, pts.map(() => 2.5)),
    base: "field", col: "#2E6B45",
    plates,
  };
}

/* ---- Appendix B: Fire-Flow Requirements for Buildings - a fire hose nozzle, side on, its spray part of the pin: the hose, the knurled
   brass coupling, the tapered barrel with its bale handle (a real hole), the tip, and the spray fanning out to a scalloped edge, its
   streams grooved into it. ---- */
{
  const O = [38, 50], deg = Math.PI / 180, at = (a, r) => [O[0] + r * Math.cos(a * deg), O[1] + r * Math.sin(a * deg)];
  const A = 50, RV = 50, RT = 57,   /* (384.79) A 33 -> 46: a wider spray, room for the back's title and its FIRE CODE line (9.2 CSS px in your hand); (384.133) 46 -> 50, its title at the academy's smallest */ top = (x) => 39 + 4 * (x - 26) / 20, bot = (x) => 61 - 4 * (x - 26) / 20;
  const edge = [at(-A, RV)], er = [2];
  for(let k = 0; k < 5; k++){ const c = -A + (k + .5) * (2 * A / 5); edge.push(at(c - 3.6, RT), at(c + 3.6, RT)); er.push(4, 4); if(k < 4){ edge.push(at(c + 6.6, RV)); er.push(2.5); } }
  edge.push(at(A, RV)); er.push(2);
  const pts = [[3, 42], [15, 42], [15, 35], [26, 35], [26, top(26)], [28, top(28)], [28, 26], [46, 26], [46, 40], [51, 40]].concat(edge)
    .concat([[51, 60], [46, 60], [46, bot(46)], [26, bot(26)], [26, 65], [15, 65], [15, 58], [3, 58]]);
  const rs = [4, 1, 1, 1, 0, 1, 2, 2, 1, 1].concat(er).concat([1, 1, 1, 0, 1, 1, 1, 4]);
  let knurl = ""; for(let x = 18; x <= 23; x += 2.5) knurl += "M" + x + " 36.5V63.5";
  let streams = ""; for(let k = 1; k < 5; k++){ const a = -A + k * (2 * A / 5); streams += "M" + at(a, 22).map(v => v.toFixed(2)).join(" ") + "L" + at(a, RV - 3).map(v => v.toFixed(2)).join(" "); }
  CHAPTER_OBJ["Appendix B: Fire-Flow Requirements for Buildings"] = {
    d: OBJ_poly(pts, rs),
    holes: [OBJ_rrect(33, 31, 8, top(33) - 31 - .8, 2)],
    base: "steel",
    plates: [
      /* (art9) Madison: "There's a lot of spots all over that just don't look right." Each part ran a unit or two on under the next
         (the hose under the coupling, the barrel and the spray under the tip, the bale handle over the barrel), and a part's relief is
         added to what is under it, so each join showed a ridge through the part in front. Every part now ends where the next begins. */
      ["water", OBJ_poly([[51.8, 40], [52, 40]].concat(edge).concat([[52, 60], [51.8, 60]]), [0, 1].concat(er).concat([1, 0])), { dome: 1.8 }],   /* the spray */
      ["water", streams, { ln: 1.6, cut: .9, paint: 0 }],                                           /* its streams */
      ["red", OBJ_rrect(3, 42, 12, 16, [4, 0, 0, 4]), { dome: 1.1 }],                               /* the hose */
      ["brass", OBJ_rrect(15, 35, 11, 30, 1), { z: .6, bev: .6 }],                                  /* the coupling */
      ["brass", knurl, { ln: 1.2, cut: .7, paint: 0 }],                                             /* its knurling */
      ["steel", OBJ_poly([[26, top(26)], [45, top(45)], [45, bot(45)], [26, bot(26)]], [0, 0, 0, 0]), { dome: 1.4 }],   /* the barrel */
      ["rubber", OBJ_poly([[28, top(28)], [28, 26], [46, 26], [46, top(46)]], [0, 2, 2, 0]), { z: .5, bev: .6 }],   /* the bale handle */
      ["steel", OBJ_rrect(45, 40, 7, 20, 1.5), { z: .5, bev: .5, gem: .6, gw: 1.6 }],               /* the tip */
    ],
  };
}

/* ---- Appendix C: Fire Hydrant Locations and Distribution - a map pin standing on its spot, a hydrant raised in its window: the location,
   and what is there. (art10) Madison circled the foot: the pin's point was stuck into the middle of a wide, flat black disc. The pin
   now STANDS on a small round base plate seen in perspective - its top an ellipse, its edge a band below it - with the point touching
   the middle of the top and a soft contact shadow round it; the base stops where the pin starts (nothing under the pin to show through
   it), so the pin reads as a marker standing on the map. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const C = [50, 34], R = 31, T = [50, 87.2], d = T[1] - C[1], ph = Math.acos(R / d), f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const Rt = [C[0] + R * Math.sin(ph), C[1] + R * Math.cos(ph)], Lt = [C[0] - R * Math.sin(ph), C[1] + R * Math.cos(ph)];
  const pin = "M" + f(Lt) + "A" + R + " " + R + " 0 0 1 " + f([C[0], C[1] - R]) + "A" + R + " " + R + " 0 0 1 " + f(Rt) + OBJ_chain([Rt, T, Lt], [0, 2.2, 0]) + "Z";
  const pinF = S.poly(OBJ_walk(pin));
  const BX = 17, BY = 4.6, BT = 3.2;                                           /* the base: its top's half-axes, and its thickness */
  const top = S.ellipse(50, T[1], BX, BY), base = S.union([top, S.ellipse(50, T[1] + BT, BX, BY), S.box(50 - BX, T[1], 2 * BX, BT, 0)], 0);
  const all = S.union([pinF, base], 1.2);
  CHAPTER_OBJ["Appendix C: Fire Hydrant Locations and Distribution"] = {
    d: S.shape(all, BB),
    base: "rubber",
    plates: [
      ["rubber", S.shape(S.minus(S.minus(all, top), pinF), BB), { z: -.2, bev: .9, col: "#3F454D" }],       /* the base's edge */
      ["rubber", S.shape(S.minus(top, pinF), BB), { z: .25, bev: .8, dome: .3, col: "#7D8792" }],          /* its top */
      ["rubber", S.shape(S.minus(S.inter(S.ellipse(54.6, T[1] + .55, 8.6, 2.2), S.grow(top, -.8)), pinF), BB), { z: -.12, bev: 1.3, col: "#5C656F" }],   /* the pin's shadow on it, falling down and right */
      ["red", pin, { dome: 2.2 }],                                                                  /* the pin */
      ["cream", OBJ_circle(C[0], C[1] + 1, 21), { z: -1.1, bev: 1 }],                                  /* its window */
      ["red", OBJ_poly([[46, 17], [54, 17], [55.5, 21], [59, 23], [61, 28], [58, 28], [58, 32], [66, 32], [66, 41], [58, 41], [58, 47], [61, 47], [61, 52],
                         [39, 52], [39, 47], [42, 47], [42, 41], [34, 41], [34, 32], [42, 32], [42, 28], [39, 28], [41, 23], [44.5, 21]],
                        [1.5, 1.5, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1]), { z: 1.6, bev: .8, dome: .6 }],   /* the hydrant, raised */
    ],
  };
}

/* ---- Appendix H: HMMP and HMIS Instructions - a clipboard with its pencil: the board, the steel clip with its hole, the sheet, three
   checklist rows (a box pressed in, a raised tick, the line's grooves), and the pencil laid across its corner, standing out past the
   board's edge (the shape a plain board does not have). (384.133 badgeart, Madison: "The other pencil looked better, the edges of it
   just needed to be better cause it wasn't 100 percent good to go." The pencil is the one from before round 9 again - the polished brass
   pencil with its red eraser - and its edges are made clean: every part of it meets the next on the same line with no corner rounded
   where it butts on a neighbour (the body's rounded ends left specks of the board at the ferrule and the cone), the eraser's end follows
   the outline's own corner, the ferrule is crimped twice, the body carries two facet lines like a hexagonal pencil, and the sharpened wood
   runs in straight to the graphite.) ---- */
{
  /* (art10) Madison circled the whole pencil: "make these better". A real pencil now, slimmer (a pencil is a long thin thing): a
     hexagonal barrel showing three flat faces (lit, middle, shaded yellow - the middle face as wide as both sides together, as a hexagon
     seen flat-on is); the sharpened wood cone with the SCALLOPED edge where the paint meets the wood (the cone cuts each flat face in a
     curve, so the paint runs up to a point in the middle of every face); the graphite point; the metal ferrule with its crimped ridges
     near both ends; and a pink eraser with a rounded end. It stands point up beside the board, clear of it below (its eraser runs past
     the board's foot) and with the board's own edge rising between them, so it reads as a pencil standing there, not a strip of the
     board. */
  const X0 = 10, X1 = 72, Y0 = 27, Y1 = 96, f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const HW = 4.1, E = [X1 + HW, 98.6], TP = [X1 + HW, 1], L = Math.hypot(TP[0] - E[0], TP[1] - E[1]), u = [(TP[0] - E[0]) / L, (TP[1] - E[1]) / L], n = [u[1], -u[0]];   /* it stands on its eraser, point up: w > 0 is its left (lit) side */
  const Q = (t, w) => [E[0] + u[0] * t + n[0] * w, E[1] + u[1] * t + n[1] * w];
  const ER = 2.7, RUB = 5.6, FER = 15.2, CONE = L - 17.5, AP = L, PT = L - .5, GR = L - 6.2;   /* eraser | ferrule | barrel | cone | graphite */
  const rows = [48, 63, 78], plates = [
    ["wood", OBJ_poly([[X0, Y0], [X1, Y0], [X1, Y1], [X0, Y1]], [4, 4, 0, 4]), { z: .35, bev: 1, dome: .6 }],                    /* the board (its edges rise: the pencil stands clear of it) */
    ["cream", OBJ_rrect(X0 + 6, Y0 + 10, X1 - X0 - 12, 53, 2), { z: .5, bev: .6 }],                    /* the sheet */
    /* (art9) Madison: "There's a lot of spots all over that just don't look right." The clip took the board's edge and the sheet's
       top as steps across it (a part's relief is added to what is under it); it now lies flat over both (lvl). */
    ["steel", OBJ_poly([[20, 38], [20, 28], [26, 16], [56, 16], [62, 28], [62, 38]], [2, 2, 3, 3, 2, 2]), { z: 1.1, bev: .8, dome: .6, lvl: "clip" }],   /* the clip */
  ];
  /* (384.136 art6) the three rows' boxes, ticks and lines are one plate each (the same parts, the same options): a badge holds at
     most CHAPTER_OBJ_MAX_PLATES (24) and the pencil's contour was the 25th, dropped without a word */
  /* (art6 round 4) Madison: "the check marks are messed up and don't look right all the way through". A tick that crossed its box's
     edge showed the box's rim through it. Each tick now sits wholly inside its (larger) box: nothing crosses anything. */
  plates.push(["steel", rows.map(y => OBJ_rrect(19, y - 6.5, 13, 13, 2.5)).join(""), { z: -.7, bev: .5 }]);
  /* (art7) Madison: "inside the box they have an outline, outside the box the outline is gone" - each tick is a dark outline under its blue,
     the same the whole way along, wherever it lies */
  const tickD = rows.map(y => "M22 " + (y + .2) + "L24.8 " + (y + 3.2) + "L29.4 " + (y - 3.4)).join("");
  plates.push(["ink", tickD, { ln: 4.1, z: 1.0, bev: .5, col: "#16324F" }]);
  plates.push(["water", tickD, { ln: 2.5, z: 1.25, bev: .6 }]);   /* the ticks */
  plates.push(["cream", rows.map(y => "M36 " + (y - 2.5) + "H" + (y > 70 ? 52 : 58) + "M36 " + (y + 3) + "H" + (y > 70 ? 46 : 52)).join(""), { ln: 2.2, cut: .7, paint: 0 }]);
  /* THE PENCIL. The cone's half-width at t, and where the paint stops across face w (the scallop: highest in each face's middle) */
  const wAt = t => HW * (AP - t) / (AP - CONE), H2 = HW / 2, SB = 2.6;
  const FACES = [[HW, H2], [H2, -H2], [-H2, -HW]];
  const scal = (w0, w1, w) => { const c = (w0 + w1) / 2, h = Math.abs(w1 - w0) / 2; return CONE + SB * (1 - ((w - c) / h) ** 2); };
  const N = 10, arc = (w0, w1) => { const o = []; for(let i = 0; i <= N; i++){ const w = w0 + (w1 - w0) * i / N; o.push(Q(scal(w0, w1, w), w)); } return o; };
  const FCOL = ["#F7D262", "#E7B532", "#BE8A22"], WCOL = ["#E6C08E", "#D4A56C", "#B5844F"];
  /* ONE relief for barrel, cone and point, cut into planar facets (gem: the ramp from each side is a hexagon's side face, half the
     half-width wide, so the creases fall on the faces' own edges and run on up the cone to the point); the faces' tones on it */
  plates.push(["cardboard", OBJ_poly([Q(FER, HW), Q(CONE, HW), Q(PT, wAt(PT)), Q(PT, -wAt(PT)), Q(CONE, -HW), Q(FER, -HW)], [0, 0, .2, .2, 0, 0]), { lvl: "pencil", z: .9, bev: .3, gem: .8, gw: H2, col: FCOL[1] }]);
  /* the barrel's faces, each from the ferrule to its scallop */
  FACES.forEach(([w0, w1], k) => plates.push(["cardboard", OBJ_poly([Q(FER, w0)].concat(arc(w0, w1)).concat([Q(FER, w1)]), 0), { col: FCOL[k] }]));
  /* the sharpened wood, each face's tone, from its scallop up to the graphite (the outer two keep their outer edge on the cone's own line) */
  const gw = w => w * wAt(GR) / HW;
  FACES.forEach(([w0, w1], k) => plates.push(["cardboard", OBJ_poly([Q(CONE, w0), Q(GR, gw(w0)), Q(GR, gw(w1)), Q(CONE, w1)].concat(arc(w0, w1).reverse().slice(1, -1)), 0), { col: WCOL[k] }]));
  plates.push(["rubber", OBJ_poly([Q(GR, -wAt(GR)), Q(PT, -wAt(PT)), Q(PT, wAt(PT)), Q(GR, wAt(GR))], [0, .2, .2, 0]), { col: "#3A3D42" }]);   /* the graphite */
  plates.push(["cream", OBJ_poly([Q(RUB, -HW), Q(FER, -HW), Q(FER, HW), Q(RUB, HW)], 0), { lvl: "pencil", z: 1.2, bev: .45, dome: .5, col: "#BCC3CC" }]);   /* the ferrule, brushed aluminium */
  plates.push(["cream", [RUB + 1.3, RUB + 2.4, FER - 2.4, FER - 1.3].map(t => "M" + f(Q(t, -HW + .5)) + "L" + f(Q(t, HW - .5))).join(""), { lvl: "pencil", ln: .7, cut: .6, paint: 0 }]);   /* its crimped ridges */
  plates.push(["red", OBJ_poly([Q(0, -HW), Q(RUB, -HW), Q(RUB, HW), Q(0, HW)], [ER, 0, 0, ER]), { lvl: "pencil", z: 1.1, bev: .8, dome: 1, col: "#EC6F82" }]);   /* its eraser, rounded */
  plates.push(["rubber", "M" + f([X1, Y0 + 1]) + "V" + (Y1 - .5), { ln: 1, cut: .5, paint: 0 }]);   /* the line where it stands beside the board */
  CHAPTER_OBJ["Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions"] = {
    /* (384.136 art6) THE PENCIL STANDS AGAINST THE BOARD. Madison, a sixth time: "The pencil is still messed up". Every round that patched
       the place where it crossed the board's edge left something there; lying wholly on the board made the outline a plain board (a
       twin of Chapter 10's door). It now stands upright against the board's right side - a straight joint, no crossing - rising past the
       board's top beside the clip, and its sharpened end makes the outline's notch. */
    d: "M" + f([X0 + 4, Y0]) + OBJ_chain([[X0 + 4, Y0], [20, Y0], [26, 16], [56, 16], [62, Y0], [X1, Y0], Q(CONE, HW), Q(PT, wAt(PT)), Q(PT, -wAt(PT)), Q(CONE, -HW), Q(0, -HW), Q(0, HW), [X1, Y1], [X0, Y1], [X0, Y0], [X0 + 4, Y0]],
      [0, 1, 3, 3, 1, 1, 0, .3, .3, 0, ER, ER, 0, 4, 4, 0]) + "Z",
    holes: [OBJ_rrect(33, 21, 16, 6, 2.5)],
    base: "wood",
    plates,
  };
}

/* ---- Appendix I: Fire Protection Systems - Noncompliant Conditions - the fire protection impairment tag. (384.133 badgeart, Madison:
   "This isn't a fire protection red tag. I attached one though. They have yellow tags as well that look the same just yellow." His
   photo: the state fire marshal's EQUIPMENT IMPAIRED tag - a tall red card with clipped top corners, a reinforced grommet at the top, the
   printed form: a heading, a grid of day and month boxes down each side, ruled lines to fill in, and EQUIPMENT IMPAIRED in heavy black
   type at the foot.) Now that tag: red, its wire loop through the grommet (a tan reinforcing patch and a steel eyelet with a real hole),
   the heading and the heavy words as raised black print (two bars each: no letters at this size), the day and month grids and the
   ruled lines pressed into the card, and a yellow tag of the same kind hung on the same wire behind it. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const G = [46, 31], th = -14 * Math.PI / 180;
  const rot = ([x, y]) => [G[0] + (x - G[0]) * Math.cos(th) - (y - G[1]) * Math.sin(th), G[1] + (x - G[0]) * Math.sin(th) + (y - G[1]) * Math.cos(th)];
  const TP = [[30.5, 21], [61.5, 21], [70, 29.5], [70, 95], [22, 95], [22, 29.5]];
  const red = S.grow(S.poly(TP), 2), yel = S.grow(S.poly(TP.map(rot)), 2);
  const wire = S.minus(S.union([S.circle(G[0], 11, 9.5), S.cone(G[0], 11, G[0], 29, 9.5, 2.6)], 0), S.union([S.circle(G[0], 11, 4.6), S.cone(G[0], 11, G[0], 18.5, 4.6, .8)], 0));
  const hole = S.circle(G[0], G[1], 2.9);
  const all = S.minus(S.union([red, yel, wire], 1), hole);
  const sil = S.trace(all, BB);
  /* the printed form, pressed into the card */
  let grid = "";
  [[26, 34], [58, 66]].forEach(([x0, x1]) => { grid += "M" + x0 + " 50V88M" + ((x0 + x1) / 2) + " 50V88M" + x1 + " 50V88";
    for(let y = 50; y <= 88; y += 4.75) grid += "M" + x0 + " " + y + "H" + x1; });
  CHAPTER_OBJ["Appendix I: Fire Protection Systems—Noncompliant Conditions"] = {
    d: sil.d, holes: sil.holes,
    col: "#E0352B", base: "red",
    plates: [
      /* (art9) Madison: "There's a lot of spots all over that just don't look right." The yellow tag ran on under the red one and the
         wire lay over both, and a part's relief is added to what is under it: the yellow tag's edge showed through the red one as a
         nick along its foot, the red tag's edge as a step across the wire. The yellow tag now stops at the red one; the wire lies
         flat over everything (lvl). */
      ["glow", S.shape(S.minus(yel, red), BB), { dome: .6, col: "#F2C230" }],                         /* the yellow tag behind */
      ["glow", "M" + rot([67, 66]).map(v => v.toFixed(2)).join(" ") + "L" + rot([67, 90]).map(v => v.toFixed(2)).join(" ") + "M" + rot([70, 63]).map(v => v.toFixed(2)).join(" ") + "L" + rot([70, 90]).map(v => v.toFixed(2)).join(" "), { ln: .9, cut: .45, paint: 0 }],   /* its grid, where it shows */
      ["red", S.shape(red, BB), { z: .6, bev: .8, dome: .6 }],                                       /* the red tag */
      ["red", grid, { ln: .8, cut: .45, paint: 0 }],                                                  /* its day and month grids */
      ["red", "M39 60H53M39 67H53M39 74H53", { ln: .9, cut: .45, paint: 0 }],                         /* the lines to fill in */
      ["ink", "M33.5 41.5H58.5M37 46H55", { ln: 2, z: .3, bev: .3, col: "#231A1A" }],                 /* the heading */
      ["ink", "M32.5 80.5H59.5M35.5 87H56.5", { ln: 3.6, z: .4, bev: .35, col: "#1D1616" }],          /* EQUIPMENT IMPAIRED */
      ["cream", OBJ_circle(G[0], G[1], 7.2), { z: .3, bev: .5, dome: .4, col: "#D8C08E" }],            /* the reinforcing patch */
      ["steel", OBJ_circle(G[0], G[1], 4.5), { z: .6, bev: .5, dome: .8 }],                           /* the eyelet */
      ["steel", S.shape(S.grow(wire, -.01), BB), { z: .4, bev: .7, dome: 1.2, lvl: "wire" }],         /* the wire loop */
    ],
  };
}

/* ---- Exhibit B: Amendments to the International Building Code - a skyscraper: three setbacks and a spire, each tier a lit front and a
   shaded side, the windows pressed in as columns, the floors grooved across. ---- */
{
  const T = [[39, 61, 16, 32], [30, 70, 32, 54], [21, 79, 54, 96]];   /* x0, x1, y0, y1 */
  const plates = [["steel", OBJ_rrect(47, 2, 6, 16, [3, 3, 0, 0]), { dome: 1 }]];   /* the spire */
  let floors = "";
  T.forEach(([x0, x1, y0, y1]) => {
    const sx = Math.round(x0 + (x1 - x0) * .62);
    plates.push(["lite", OBJ_rrect(x0, y0, sx - x0, y1 - y0, 0), { z: .3, bev: .5 }]);
    plates.push(["shade", OBJ_rrect(sx, y0, x1 - sx, y1 - y0, 0)]);
    let wf = "", ws = "";
    for(let x = x0 + 4; x + 5 <= sx - 3; x += 9) wf += OBJ_rrect(x, y0 + 4, 5, y1 - y0 - 7, 1);
    for(let x = sx + 4; x + 5 <= x1 - 3; x += 9) ws += OBJ_rrect(x, y0 + 4, 5, y1 - y0 - 7, 1);
    plates.push(["glass", wf, { z: -.7, bev: .5 }]);
    if(ws) plates.push(["ink", ws, { z: -.7, bev: .5 }]);
    for(let y = y0 + 11; y < y1 - 4; y += 8) floors += "M" + x0 + " " + y + "H" + x1;
  });
  plates.push(["field", floors, { ln: 1.2, cut: .6, paint: 0 }]);
  CHAPTER_OBJ["Exhibit B: Amendments to the International Building Code"] = {
    d: OBJ_poly([[47, 2], [53, 2], [53, 16], [61, 16], [61, 32], [70, 32], [70, 54], [79, 54], [79, 96], [21, 96], [21, 54], [30, 54], [30, 32], [39, 32], [39, 16], [47, 16]],
      [3, 3, 1, 1.5, 1, 1.5, 1, 1.5, 2, 2, 1.5, 1, 1.5, 1, 1.5, 1]),
    plates,
  };
}
