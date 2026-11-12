/* Fire Code chapter objects - PART 5 (build 384.66 round 3 format): ten chapters drawn as RAISED PINS. Each entry is the pin's silhouette
   and its parts; identity is the silhouette and the sculpture (raised, recessed, domed, faceted, grooved), never a sticker. Colours are the
   object's own (Madison: "make the color of stuff relevant, you don't need to keep the old colors"): a black bomb, a blue drop, a red map
   pin, a brown clipboard. See tools/chapter-objects/README.md. */

/* ---- Chapter 64: Pyrophoric Materials - a burning rock (it ignites on contact with air): a faceted dark stone with glowing cracks cut
   into it, and three tongues of flame rising off it, the middle one tallest, a hot core inside. ---- */
{
  CHAPTER_OBJ["Chapter 64: Pyrophoric Materials"] = {
    d: OBJ_poly([[12, 93], [5, 76], [13, 60], [20, 57.12], [13, 42], [21, 21], [33, 37], [38, 20], [50, 2], [62, 20], [67, 37], [79, 21], [87, 42], [80, 57.12],
                 [87, 60], [95, 76], [88, 93]],
      [5, 5, 4, 1.5, 6, 2, 3, 5, 2.2, 5, 3, 2, 6, 1.5, 4, 5, 5]),
    base: "rubber",
    plates: [
      ["red", OBJ_rrect(0, 0, 100, 62, 0)],                                                                                                              /* the flames */
      ["hot", OBJ_poly([[38, 58], [37, 42], [44, 30], [50, 17], [56, 30], [63, 42], [62, 58]], [2, 6, 4, 2, 4, 6, 2]), { z: .6, bev: .9, dome: 1.2 }],   /* the hot inner flame */
      ["glow", OBJ_poly([[44, 58], [45, 47], [50, 36], [55, 47], [56, 58]], [2, 4, 2, 4, 2]), { z: .5, bev: .7, dome: .8 }],                             /* its white-hot core */
      ["hot", OBJ_poly([[21, 58], [19, 46], [23, 34], [30, 48], [30, 58]], [2, 4, 2, 3, 2]), { z: .4, bev: .7, dome: .8 }],                             /* the side flames' hearts */
      ["hot", OBJ_poly([[79, 58], [81, 46], [77, 34], [70, 48], [70, 58]], [2, 4, 2, 3, 2]), { z: .4, bev: .7, dome: .8 }],
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
      ["wood", OBJ_rrect(40, Y0, 56, Y1 - Y0, [0, 2, 2, 0]), { dome: .6 }],                       /* the film strip */
      ["rubber", perf, { z: -.9, bev: .5 }],                                                         /* its perforations */
      ["steel", OBJ_circle(C[0], C[1], R), { dome: .4 }],                                          /* the reel */
      ["steel", OBJ_circle(C[0], C[1], R - 5.5), { z: -.7, bev: .9 }],                             /* its face, inside the rim */
      ["brass", OBJ_circle(C[0], C[1], 9.5), { z: 1.1, bev: .9, dome: .8 }],                        /* the hub */
      ["rubber", OBJ_circle(C[0], C[1], 4), { dome: 1.3 }],                                         /* the spindle */
    ],
  };
}

/* ---- Chapter 66: Unstable (Reactive) Materials - a round bomb: the domed sphere, the faceted steel cap, the fuse and its spark. ---- */
{
  const C = [41, 60], R = 34, s = Math.SQRT1_2, u = [s, -s], n = [s, s], W = 9.5, CAP = 45, FW = 3.2, SR = 11.5, SV = 5.2, ST = 62;
  const P = (t, w) => [C[0] + t * u[0] + w * n[0], C[1] + t * u[1] + w * n[1]], f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const a = Math.sqrt(R * R - W * W), S = P(ST, 0), opp = P(-R, 0);
  const star = [P(ST - SV, -FW)];
  for(let k = 1; k <= 15; k++){ const ang = (135 + 22.5 * k) * Math.PI / 180, r = k % 2 ? SR : SV; star.push([S[0] + r * Math.cos(ang), S[1] + r * Math.sin(ang)]); }
  star.push(P(ST - SV, FW));
  const run = [P(a, -W), P(CAP, -W), P(CAP, -FW)].concat(star).concat([P(CAP, FW), P(CAP, W), P(a, W)]);
  const rr = [0, 1.5, 1].concat(star.map((p, i) => (i === 0 || i === star.length - 1) ? 1 : (i % 2 ? 1.2 : 1))).concat([1, 1.5, 0]);
  CHAPTER_OBJ["Chapter 66: Unstable (Reactive) Materials"] = {
    d: "M" + f(P(a, W)) + "A" + R + " " + R + " 0 0 1 " + f(opp) + "A" + R + " " + R + " 0 0 1 " + f(P(a, -W)) + OBJ_chain(run, rr) + "Z",
    base: "rubber",
    plates: [
      ["rubber", OBJ_circle(C[0], C[1], R), { dome: 4 }],                                                   /* the sphere */
      ["brass", OBJ_poly([P(a - 5, -W), P(CAP, -W), P(CAP, W), P(a - 5, W)], 1.5), { z: .5, bev: .7, gem: .9, gw: 2.2 }],   /* the cap */
      ["brass", "M" + f(P(a - 1, -W)) + "L" + f(P(a - 1, W)), { ln: 1.4, cut: .7, paint: 0 }],             /* its seam */
      ["cream", OBJ_poly([P(CAP - 1, -FW), P(ST - SV + 1, -FW), P(ST - SV + 1, FW), P(CAP - 1, FW)], 1), { dome: .9 }],   /* the fuse */
      ["hot", OBJ_poly(star.slice(1, -1).concat([S]), 1), { z: .5, bev: .7, gem: 1, gw: 2.4 }],             /* the spark */
      ["glow", OBJ_circle(S[0], S[1], 4.2), { dome: 1.2 }],                                                  /* its heart */
    ],
  };
}

/* ---- Chapter 67: Water-Reactive Solids and Liquids - a drop of water struck through by a raised, faceted spark: water meeting the thing
   it sets off. ---- */
{
  const C = [50, 62], R = 32, T = [50, 3], d = Math.hypot(T[0] - C[0], T[1] - C[1]), ph = Math.acos(R / d);
  const Rt = [C[0] + R * Math.sin(ph), C[1] - R * Math.cos(ph)], Lt = [C[0] - R * Math.sin(ph), C[1] - R * Math.cos(ph)], f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const sil = "M" + f(Rt) + "A" + R + " " + R + " 0 0 1 " + f([C[0], C[1] + R]) + "A" + R + " " + R + " 0 0 1 " + f(Lt) + OBJ_chain([Lt, T, Rt], [0, 3.5, 0]) + "Z";
  CHAPTER_OBJ["Chapter 67: Water-Reactive Solids and Liquids"] = {
    d: sil,
    base: "water",
    plates: [
      ["water", sil, { dome: 2.4 }],                                                                          /* the drop */
      ["brass", OBJ_poly([[57, 27], [37, 62], [49, 62], [41, 87], [65, 50], [53, 50], [63, 27]], [1.5, 1.5, 1, 1.5, 1.5, 1, 1.5]), { z: 1.4, bev: .9, gem: .8, gw: 2 }],   /* the spark */
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
  const A = 46, RV = 50, RT = 57,   /* (384.79) A 33 -> 46: a wider spray, room for the back's title and its FIRE CODE line (9.2 CSS px in your hand) */ top = (x) => 39 + 4 * (x - 26) / 20, bot = (x) => 61 - 4 * (x - 26) / 20;
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
      ["water", OBJ_poly([[49, 40], [51, 40]].concat(edge).concat([[51, 60], [49, 60]]), [0, 1].concat(er).concat([1, 0])), { dome: 1.8 }],   /* the spray */
      ["water", streams, { ln: 1.6, cut: .9, paint: 0 }],                                           /* its streams */
      ["red", OBJ_rrect(3, 42, 14, 16, [4, 0, 0, 4]), { dome: 1.1 }],                               /* the hose */
      ["brass", OBJ_rrect(15, 35, 11, 30, 1), { z: .6, bev: .6 }],                                  /* the coupling */
      ["brass", knurl, { ln: 1.2, cut: .7, paint: 0 }],                                             /* its knurling */
      ["steel", OBJ_poly([[26, top(26)], [46, top(46)], [46, bot(46)], [26, bot(26)]], 1), { dome: 1.4 }],   /* the barrel */
      ["rubber", OBJ_poly([[28, top(28) + 1], [28, 26], [46, 26], [46, top(46) + 1]], [0, 2, 2, 0]), { z: .5, bev: .6 }],   /* the bale handle */
      ["steel", OBJ_rrect(45, 40, 7, 20, 1.5), { z: .5, bev: .5, gem: .6, gw: 1.6 }],               /* the tip */
    ],
  };
}

/* ---- Appendix C: Fire Hydrant Locations and Distribution - a map pin standing on its spot, a hydrant raised in its window: the location,
   and what is there. ---- */
{
  const C = [50, 34], R = 31, T = [50, 88], d = T[1] - C[1], ph = Math.acos(R / d), E = [50, 87.5], EX = 32, EY = 8.5;
  const Rt = [C[0] + R * Math.sin(ph), C[1] + R * Math.cos(ph)], Lt = [C[0] - R * Math.sin(ph), C[1] + R * Math.cos(ph)], f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  /* where each side of the pin meets the top of the spot (the ellipse) */
  const meet = (P) => { const dx = T[0] - P[0], dy = T[1] - P[1], ox = (P[0] - E[0]) / EX, oy = (P[1] - E[1]) / EY, ax = dx / EX, ay = dy / EY;
    const qa = ax * ax + ay * ay, qb = 2 * (ox * ax + oy * ay), qc = ox * ox + oy * oy - 1, t = (-qb - Math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa); return [P[0] + dx * t, P[1] + dy * t]; };
  const Ir = meet(Rt), Il = meet(Lt);
  const pin = "M" + f(Lt) + "A" + R + " " + R + " 0 0 1 " + f([C[0], C[1] - R]) + "A" + R + " " + R + " 0 0 1 " + f(Rt) + OBJ_chain([Rt, T, Lt], [0, 3, 0]) + "Z";
  CHAPTER_OBJ["Appendix C: Fire Hydrant Locations and Distribution"] = {
    d: "M" + f(Lt) + "A" + R + " " + R + " 0 0 1 " + f([C[0], C[1] - R]) + "A" + R + " " + R + " 0 0 1 " + f(Rt) + "L" + f(Ir) +
       "A" + EX + " " + EY + " 0 0 1 " + f([E[0], E[1] + EY]) + "A" + EX + " " + EY + " 0 0 1 " + f(Il) + "Z",
    base: "rubber",
    plates: [
      ["rubber", OBJ_ellipse(E[0], E[1], EX, EY), { dome: .5 }],                                        /* the spot */
      ["rubber", OBJ_ellipse(E[0], E[1], EX - 6.5, EY - 3), { ln: 1.6, cut: .8, paint: 0 }],             /* its ring */
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
   board's edge (the shape a plain board does not have). ---- */
{
  const X0 = 8, X1 = 80, Y0 = 12, Y1 = 96, f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const E = [91, 33], TP = [64, 93], L = Math.hypot(TP[0] - E[0], TP[1] - E[1]), u = [(TP[0] - E[0]) / L, (TP[1] - E[1]) / L], n = [-u[1], u[0]], HW = 4.8;
  const Q = (t, w) => [E[0] + u[0] * t + n[0] * w, E[1] + u[1] * t + n[1] * w];
  const atX = (w, x) => (x - E[0] - n[0] * w) / u[0];          /* where the pencil's side w crosses the board's edge x */
  const tl = atX(HW, X1), tr = atX(-HW, X1), CONE = L - 11;
  const rows = [36, 55, 74], plates = [
    ["wood", OBJ_rrect(X0, Y0, X1 - X0, Y1 - Y0, 4), { dome: .6 }],                                   /* the board */
    ["cream", OBJ_rrect(X0 + 6, Y0 + 10, X1 - X0 - 12, 68, 2), { z: .5, bev: .6 }],                    /* the sheet */
    ["steel", OBJ_poly([[23, 23], [23, 13], [29, 1], [59, 1], [65, 13], [65, 23]], [2, 2, 3, 3, 2, 2]), { z: 1.1, bev: .8, dome: .6 }],   /* the clip */
  ];
  rows.forEach(y => {
    plates.push(["steel", OBJ_rrect(20, y - 5.5, 11, 11, 2), { z: -.7, bev: .5 }]);
    plates.push(["water", "M22.5 " + (y - .5) + "L25.5 " + (y + 3) + "L32 " + (y - 7), { ln: 3, z: 1.1, bev: .6 }]);
    plates.push(["cream", "M36 " + (y - 2.5) + "H" + (y > 60 ? 54 : 62) + "M36 " + (y + 3) + "H" + (y > 60 ? 48 : 56), { ln: 2.2, cut: .7, paint: 0 }]);
  });
  plates.push(["brass", OBJ_poly([Q(7, -HW), Q(CONE, -HW), Q(CONE, HW), Q(7, HW)], 1), { z: 1.3, bev: .7, dome: .9 }]);   /* the pencil */
  plates.push(["brass", "M" + f(Q(9, 0)) + "L" + f(Q(CONE - 1, 0)), { ln: 1.2, cut: .6, paint: 0 }]);                      /* its facet */
  plates.push(["red", OBJ_poly([Q(0, -HW), Q(7, -HW), Q(7, HW), Q(0, HW)], [2, 0, 0, 2]), { z: 1.3, bev: .7, dome: .9 }]);   /* its eraser */
  plates.push(["steel", OBJ_poly([Q(5.5, -HW), Q(11, -HW), Q(11, HW), Q(5.5, HW)], .5), { z: 1.4, bev: .5, dome: .9 }]);   /* the ferrule */
  plates.push(["cream", OBJ_poly([Q(CONE, -HW), Q(L - 1, -.8), Q(L - 1, .8), Q(CONE, HW)], [0, 1, 1, 0]), { z: 1.3, bev: .7 }]);   /* the sharpened wood */
  plates.push(["rubber", OBJ_poly([Q(L - 4.5, -1.9), Q(L - .5, -.4), Q(L - .5, .4), Q(L - 4.5, 1.9)], .6), { z: 1.4, bev: .4 }]);   /* the lead */
  CHAPTER_OBJ["Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions"] = {
    d: "M" + f([X0 + 4, Y0]) + OBJ_chain([[X0 + 4, Y0], [23, Y0], [29, 1], [59, 1], [65, Y0], [X1, Y0], [X1, Q(tl, HW)[1]], Q(0, HW), Q(0, -HW), [X1, Q(tr, -HW)[1]], [X1, Y1], [X0, Y1], [X0, Y0], [X0 + 4, Y0]],
      [0, 1, 3, 3, 1, 4, 1.5, 2, 2, 1.5, 4, 4, 4, 0]) + "Z",
    holes: [OBJ_rrect(36, 6, 16, 6, 2.5)],
    base: "wood",
    plates,
  };
}

/* ---- Appendix I: Fire Protection Systems - Noncompliant Conditions - an out-of-service hang tag: the cord loop, the brass grommet, the
   raised band, and the raised prohibition ring with its bar. ---- */
{
  const C = [50, 15], R = 13, y = 26, dx = Math.sqrt(R * R - (y - C[1]) * (y - C[1]));
  CHAPTER_OBJ["Appendix I: Fire Protection Systems—Noncompliant Conditions"] = {
    d: "M" + (C[0] - dx).toFixed(2) + " " + y + "A" + R + " " + R + " 0 0 1 " + C[0] + " " + (C[1] - R) + "A" + R + " " + R + " 0 0 1 " + (C[0] + dx).toFixed(2) + " " + y +
       OBJ_chain([[C[0] + dx, y], [66, y], [82, 42], [82, 96], [18, 96], [18, 42], [34, y], [C[0] - dx, y]], [0, 2, 2, 4, 4, 2, 2, 0]) + "Z",
    holes: [OBJ_circle(C[0], C[1], 6.5), OBJ_circle(50, 39, 3.6)],
    base: "cream",
    plates: [
      ["steel", OBJ_circle(C[0], C[1], R), { dome: 1.3 }],                                            /* the cord loop */
      ["steel", "M50 27V33", { ln: 5, dome: .6 }],
      ["brass", OBJ_circle(50, 39, 7), { z: .5, bev: .5, dome: .7 }],                                  /* the grommet */
      ["red", OBJ_poly([[34, 26], [66, 26], [82, 42], [82, 54], [18, 54], [18, 42]], [2, 2, 2, 0, 0, 2]), { z: .4, bev: .6 }],                                       /* the red header */
      ["red", OBJ_circle(50, 77, 12), { ln: 5, z: 1.1, bev: .7 }],                                   /* the prohibition ring */
      ["red", "M41.5 68.5L58.5 85.5", { ln: 5, z: 1.1, bev: .7 }],
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
