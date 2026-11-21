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
      /* (384.90) the flames flame-orange, not the tent's red: with the outline following the stone's edge the two outlines came to 0.81
         alike, and the same red made them twins (check-b384-objbadges (6)) */
      ["red", OBJ_rrect(0, 0, 100, 62, 0), { col: "#F36A21" }],                                                                                       /* the flames */
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
   board's edge (the shape a plain board does not have). (384.133 badgeart, Madison: "The other pencil looked better, the edges of it
   just needed to be better cause it wasn't 100 percent good to go." The pencil is the one from before round 9 again - the polished brass
   pencil with its red eraser - and its edges are made clean: every part of it meets the next on the same line with no corner rounded
   where it butts on a neighbour (the body's rounded ends left specks of the board at the ferrule and the cone), the eraser's end follows
   the outline's own corner, the ferrule is crimped twice, the body carries two facet lines like a hexagonal pencil, and the sharpened wood
   runs in straight to the graphite.) ---- */
{
  const X0 = 10, X1 = 72, Y0 = 27, Y1 = 97, f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const E = [76.8, 1], TP = [76.8, 97], L = Math.hypot(TP[0] - E[0], TP[1] - E[1]), u = [(TP[0] - E[0]) / L, (TP[1] - E[1]) / L], n = [-u[1], u[0]], HW = 4.8;
  const Q = (t, w) => [E[0] + u[0] * t + n[0] * w, E[1] + u[1] * t + n[1] * w];
  const atX = (w, x) => (x - E[0] - n[0] * w) / u[0];          /* where the pencil's side w crosses the board's edge x */
  const tl = atX(HW, X1), tr = atX(-HW, X1), CONE = L - 13.5, ER = 2.4;
  const rows = [48, 63, 78], plates = [
    ["wood", OBJ_rrect(X0, Y0, X1 - X0, Y1 - Y0, 4), { dome: .6 }],                                   /* the board */
    ["cream", OBJ_rrect(X0 + 6, Y0 + 10, X1 - X0 - 12, 54, 2), { z: .5, bev: .6 }],                    /* the sheet */
    ["steel", OBJ_poly([[20, 38], [20, 28], [26, 16], [56, 16], [62, 28], [62, 38]], [2, 2, 3, 3, 2, 2]), { z: 1.1, bev: .8, dome: .6 }],   /* the clip */
  ];
  /* (384.136 art6) the three rows' boxes, ticks and lines are one plate each (the same parts, the same options): a badge holds at
     most CHAPTER_OBJ_MAX_PLATES (24) and the pencil's contour was the 25th, dropped without a word */
  /* (art6 round 4) Madison: "the check marks are messed up and don't look right all the way through". A tick that crossed its box's
     edge showed the box's rim through it. Each tick now sits wholly inside its (larger) box: nothing crosses anything. */
  plates.push(["steel", rows.map(y => OBJ_rrect(19, y - 6.5, 13, 13, 2.5)).join(""), { z: -.7, bev: .5 }]);
  plates.push(["water", rows.map(y => "M22 " + (y + .2) + "L24.8 " + (y + 3.2) + "L29.4 " + (y - 3.4)).join(""), { ln: 2.6, z: 1.1, bev: .6 }]);   /* the ticks, inside the boxes */
  plates.push(["cream", rows.map(y => "M36 " + (y - 2.5) + "H" + (y > 70 ? 52 : 58) + "M36 " + (y + 3) + "H" + (y > 70 ? 46 : 52)).join(""), { ln: 2.2, cut: .7, paint: 0 }]);
  /* (384.133 art3, Madison circled the pencil's lower end, where the body meets the sharpened wood and the graphite: the body's facet
     lines ran on past it and the cone and the tip did not line up.) One straight pencil now, every piece on the same axis and butting
     on the next at one line across it: the eraser 0-6.8, the ferrule 6.8-11.2, the body 11.2 to the cone, the cone to the graphite and
     the graphite to the point. The body is a hexagonal pencil's three faces - three flat strips side by side (each lit as one plane, so
     the facets are its own edges, not lines cut along it), all three ending exactly where the cone starts. The cone and the graphite are
     ONE taper: both sides run straight from the body's corners to a single point, the graphite is just the last stretch of it. */
  /* (art6 round 4) Madison: "The pencil looks messed up". It is drawn now as a plain hexagonal pencil seen square on, nothing borrowed
     from the versions that hung off the board: no side band, no grooves - three flat faces (lit, middle, shaded) from the ferrule to the
     cone, the sharpened wood in the same three tones to the graphite, a crimped ferrule and the eraser. It runs the board's full height. */
  const AP = L, PT = L - .5, GR = L - 4.2, wAt = t => HW * (AP - t) / (AP - CONE), H3 = HW / 3;
  const penOut = [Q(0, HW), Q(CONE, HW), Q(PT, wAt(PT)), Q(PT, -wAt(PT)), Q(CONE, -HW), Q(0, -HW)];
  const face = (w0, w1, t0, t1, col, role, o) => plates.push([role, OBJ_poly([Q(t0, w0), Q(t1, w0), Q(t1, w1), Q(t0, w1)], 0), Object.assign({ lvl: "pencil", z: 1.3, bev: .3 }, o, { col })]);
  face(HW, H3, 11.2, CONE, "#F0C75A", "cardboard"); face(H3, -H3, 11.2, CONE, "#DDAA36", "cardboard"); face(-H3, -HW, 11.2, CONE, "#B5832A", "cardboard");
  const cone = (wa, wb, col) => plates.push(["cardboard", OBJ_poly([Q(CONE, wa), Q(GR, wa * wAt(GR) / HW), Q(GR, wb * wAt(GR) / HW), Q(CONE, wb)], 0), { lvl: "pencil", z: 1.3, bev: .3, col }]);
  cone(HW, H3, "#E6C08E"); cone(H3, -H3, "#D4A56C"); cone(-H3, -HW, "#B5844F");
  plates.push(["rubber", OBJ_poly([Q(GR, -wAt(GR)), Q(PT, -wAt(PT)), Q(PT, wAt(PT)), Q(GR, wAt(GR))], [0, .2, .2, 0]), { lvl: "pencil", z: 1.3, bev: .35, col: "#3A3D42" }]);   /* the graphite */
  plates.push(["steel", OBJ_poly([Q(6.8, -HW), Q(11.2, -HW), Q(11.2, HW), Q(6.8, HW)], 0), { lvl: "pencil", z: 1.45, bev: .5, dome: .9 }]);   /* the ferrule */
  plates.push(["steel", "M" + f(Q(8.4, -HW + .6)) + "L" + f(Q(8.4, HW - .6)) + "M" + f(Q(9.7, -HW + .6)) + "L" + f(Q(9.7, HW - .6)), { lvl: "pencil", ln: .7, cut: .45, paint: 0 }]);   /* its crimps */
  plates.push(["red", OBJ_poly([Q(0, -HW), Q(6.8, -HW), Q(6.8, HW), Q(0, HW)], [ER, 0, 0, ER]), { lvl: "pencil", z: 1.3, bev: .7, dome: .9 }]);   /* its eraser */
  plates.push(["rubber", "M" + f([X1, Y0]) + "V" + Y1, { ln: .9, cut: .4, paint: 0 }]);   /* the line where it stands against the board */
  CHAPTER_OBJ["Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions"] = {
    /* (384.136 art6) THE PENCIL STANDS AGAINST THE BOARD. Madison, a sixth time: "The pencil is still messed up". Every round that patched
       the place where it crossed the board's edge left something there; lying wholly on the board made the outline a plain board (a
       twin of Chapter 10's door). It now stands upright against the board's right side - a straight joint, no crossing - rising past the
       board's top beside the clip, and its sharpened end makes the outline's notch. */
    d: "M" + f([X0 + 4, Y0]) + OBJ_chain([[X0 + 4, Y0], [20, Y0], [26, 16], [56, 16], [62, Y0], [X1, Y0], Q(0, HW), Q(0, -HW), Q(CONE, -HW), Q(PT, -wAt(PT)), Q(PT, wAt(PT)), Q(CONE, HW), [X1, Y1], [X0, Y1], [X0, Y0], [X0 + 4, Y0]],
      [0, 1, 3, 3, 1, 1, ER, ER, 0, .3, .3, 0, 4, 4, 4, 0]) + "Z",
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
      ["glow", S.shape(yel, BB), { dome: .6, col: "#F2C230" }],                                       /* the yellow tag behind */
      ["glow", "M" + rot([67, 66]).map(v => v.toFixed(2)).join(" ") + "L" + rot([67, 90]).map(v => v.toFixed(2)).join(" ") + "M" + rot([70, 63]).map(v => v.toFixed(2)).join(" ") + "L" + rot([70, 90]).map(v => v.toFixed(2)).join(" "), { ln: .9, cut: .45, paint: 0 }],   /* its grid, where it shows */
      ["red", S.shape(red, BB), { z: .6, bev: .8, dome: .6 }],                                       /* the red tag */
      ["red", grid, { ln: .8, cut: .45, paint: 0 }],                                                  /* its day and month grids */
      ["red", "M39 60H53M39 67H53M39 74H53", { ln: .9, cut: .45, paint: 0 }],                         /* the lines to fill in */
      ["ink", "M33.5 41.5H58.5M37 46H55", { ln: 2, z: .3, bev: .3, col: "#231A1A" }],                 /* the heading */
      ["ink", "M32.5 80.5H59.5M35.5 87H56.5", { ln: 3.6, z: .4, bev: .35, col: "#1D1616" }],          /* EQUIPMENT IMPAIRED */
      ["cream", OBJ_circle(G[0], G[1], 7.2), { z: .3, bev: .5, dome: .4, col: "#D8C08E" }],            /* the reinforcing patch */
      ["steel", OBJ_circle(G[0], G[1], 4.5), { z: .6, bev: .5, dome: .8 }],                           /* the eyelet */
      ["steel", S.shape(S.grow(wire, -.01), BB), { z: .4, bev: .7, dome: 1.2 }],                      /* the wire loop */
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
