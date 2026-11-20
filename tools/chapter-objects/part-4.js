/* Fire Code chapter objects - PART 4 (build 384.66 round 3 format): ten hazardous-materials chapters drawn as RAISED PINS. Each is the
   chapter's object; identity is its silhouette and its sculpture (raised, recessed, domed, faceted and grooved parts), never a sticker. Colours are each part's natural colour (Madison: "make the color of stuff relevant"), the chapter enamel only where it is natural too.
   See tools/chapter-objects/README.md. Helpers here are prefixed P4_ so they never meet another part file's. */

/* sample points along an ellipse from angle a0 to a1 (degrees, y down), each with corner radius r (0 = a dense curve) */
const P4_arc = (cx, cy, rx, ry, a0, a1, n) => {
  const out = [];
  for(let i = 0; i <= n; i++){ const t = (a0 + (a1 - a0) * i / n) * Math.PI / 180; out.push([cx + rx * Math.cos(t), cy + ry * Math.sin(t)]); }
  return out;
};
/* a ribbon round a centreline (an open stroke of varying width) as its two sides and a round cap at the end: the points run up the
   left side (left of travel), round the tip and back down the right side, so a clockwise outline can take them in order */
const P4_ribbon = (c, w) => {
  const L = [], R = [], n = c.length;
  for(let i = 0; i < n; i++){
    const a = c[Math.max(0, i - 1)], b = c[Math.min(n - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
    const nx = dy / l, ny = -dx / l, h = w[i] / 2;
    L.push([c[i][0] + nx * h, c[i][1] + ny * h]); R.push([c[i][0] - nx * h, c[i][1] - ny * h]);
  }
  const e = c[n - 1], p = c[n - 2], dx = e[0] - p[0], dy = e[1] - p[1], l = Math.hypot(dx, dy), ux = dx / l, uy = dy / l, h = w[n - 1] / 2;
  const cap = []; for(let k = 1; k < 8; k++){ const t = Math.PI * k / 8, nx = uy, ny = -ux; cap.push([e[0] + (nx * Math.cos(t) + ux * Math.sin(t)) * h, e[1] + (ny * Math.cos(t) + uy * Math.sin(t)) * h]); }
  return L.concat(cap).concat(R.reverse());
};
/* the part of the segment a-b inside a convex polygon (Cyrus-Beck), or null */
const P4_clip = (a, b, poly) => {
  let t0 = 0, t1 = 1; const dx = b[0] - a[0], dy = b[1] - a[1], n = poly.length;
  let s = 0; for(let i = 0; i < n; i++){ const p = poly[i], q = poly[(i + 1) % n]; s += p[0] * q[1] - q[0] * p[1]; }
  for(let i = 0; i < n; i++){
    const p = poly[i], q = poly[(i + 1) % n], ex = q[0] - p[0], ey = q[1] - p[1];
    const nx = s > 0 ? -ey : ey, ny = s > 0 ? ex : -ex;          /* inward normal */
    const num = nx * (a[0] - p[0]) + ny * (a[1] - p[1]), den = nx * dx + ny * dy;
    if(Math.abs(den) < 1e-9){ if(num < 0) return null; continue; }
    const t = -num / den; if(den > 0) t0 = Math.max(t0, t); else t1 = Math.min(t1, t);
    if(t0 > t1) return null;
  }
  return [[a[0] + dx * t0, a[1] + dy * t0], [a[0] + dx * t1, a[1] + dy * t1]];
};
/* a polyline resampled every ~step units (corners kept), so a ribbon round it bends smoothly */
const P4_resample = (c, step) => {
  const out = [c[0]];
  for(let i = 1; i < c.length; i++){ const a = c[i - 1], b = c[i], l = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.round(l / step));
    for(let k = 1; k <= n; k++) out.push([a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n]); }
  return out;
};
const P4_f = p => (Math.round(p[0] * 100) / 100) + " " + (Math.round(p[1] * 100) / 100);
const P4_lines = segs => segs.filter(Boolean).map(s => "M" + P4_f(s[0]) + "L" + P4_f(s[1])).join("");

/* ---- Chapter 51: Aerosols - an aerosol spray can: the domed shoulder with its rolled seam, the actuator and nozzle, and the mist fanning
   out of it as part of the silhouette, with raised droplets in it. The can itself is short and wide beside 53's tall cylinder. ---- */
{
  const sL = P4_arc(33, 34, 21, 13, 180, 250.5, 6), sR = P4_arc(33, 34, 21, 13, 289.5, 360, 6);
  const lobe = (A, B, k) => { const out = [], dx = B[0] - A[0], dy = B[1] - A[1], l = Math.hypot(dx, dy), nx = dy / l, ny = -dx / l;
    for(let i = 1; i < 8; i++){ const t = i / 8, s = Math.sin(Math.PI * t) * k; out.push([A[0] + dx * t + nx * s, A[1] + dy * t + ny * s]); } return out; };
  const T0 = [80, 3.5], T1 = [91, 8.5], T2 = [93, 19], T3 = [83, 27];
  const plume = [[47, 10]].concat([T0]).concat(lobe(T0, T1, 4.6)).concat([T1]).concat(lobe(T1, T2, 4.6)).concat([T2]).concat(lobe(T2, T3, 4.6)).concat([T3]).concat([[47, 16.5]]);
  const pts = [[12, 95]].concat(sL).concat([[26, 21.7], [26, 10]]).concat(plume).concat([[40, 16.5], [40, 21.7]]).concat(sR).concat([[54, 95]]);
  const rs = pts.map(() => 0), at = p => pts.indexOf(p);
  [[pts[0], 6], [sL[0], 1], [pts[at(T0) - 2], 3], [plume[0], .6], [T0, 2], [T1, 1.2], [T2, 1.2], [T3, 2], [plume[plume.length - 1], .6],
   [pts[at(T3) + 2], 1], [pts[at(T3) + 3], 1], [sR[sR.length - 1], 1], [pts[pts.length - 1], 6]].forEach(q => { rs[at(q[0])] = q[1]; });
  rs[at(T0) - 3] = 1;                                                                  /* the actuator's foot on the shoulder */
  const shoulder = OBJ_poly([[12, 36]].concat(sL).concat(P4_arc(33, 34, 21, 13, 250.5, 289.5, 4)).concat(sR).concat([[54, 36]]), 0);
  CHAPTER_OBJ["Chapter 51: Aerosols"] = {
    d: OBJ_poly(pts, rs),
    plates: [
      ["field", OBJ_rrect(12, 34, 42, 61, [0, 0, 6, 6]), { dome: 1.6 }],                         /* the can */
      ["body", shoulder, { dome: 1.2 }],                                                          /* its domed shoulder */
      ["steel", OBJ_rrect(12, 32, 42, 5, 2.5), { z: .8, bev: .8 }],                              /* the rolled seam */
      ["steel", OBJ_rrect(12, 88, 42, 7, [0, 0, 6, 6]), { z: .5, bev: .6 }],                     /* the bottom bead */
      ["cream", OBJ_rrect(18, 44, 30, 38, 4), { z: -.8, bev: .9 }],                              /* the label panel pressed in */
      ["cream", OBJ_poly([[26, 21.7], [26, 10], [47, 10], [47, 16.5], [40, 16.5], [40, 21.7]], [0, 3, .6, .6, 1, 0]), { z: .6, bev: .6 }],   /* the actuator and nozzle */
      ["glow", OBJ_poly(plume, 1.5), { z: -.3, bev: .8 }],                                       /* the mist */
      ["lite", OBJ_circle(62, 13.5, 2.7), { dome: 1.2 }],                                        /* its droplets */
      ["lite", OBJ_circle(72, 9.5, 2.7), { dome: 1.2 }],
      ["lite", OBJ_circle(73, 19, 2.7), { dome: 1.2 }],
      ["lite", OBJ_circle(84.5, 11, 3), { dome: 1.3 }],
      ["lite", OBJ_circle(84, 20.5, 3), { dome: 1.3 }],
    ],
  };
}

/* ---- Chapter 54: Corrosive Materials - a chemical jug: the screw cap with its knurling, the neck, the moulded handle with a real hole
   through it, the ribbed body with its panel pressed in, and the acid it is leaking. (384.133 badgeart, Madison: "The leak is coming out
   of the lid, the green leak." The round-9 drop hung from under the cap, so the cap looked like what was leaking.) The cap is now clean
   and sealed; the acid seeps from a split low in the jug's side, runs down it and spreads into a glossy green puddle round the jug's
   foot - the puddle is part of the silhouette, so it reads at 44px as a leaking container. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const PX = 31, PY = 94, PRX = 27, PRY = 5;                                   /* the puddle */
  const t0 = Math.acos((57 - PX) / PRX) * 180 / Math.PI, t1 = 360 - Math.acos((20 - PX) / PRX) * 180 / Math.PI;
  const arc = P4_arc(PX, PY, PRX, PRY, t0, t1, 16), aEnd = arc[arc.length - 1];
  const jug = [[aEnd[0], aEnd[1]], [20, 36], [26, 26], [33, 22], [33, 13], [31, 13], [31, 4], [51, 4], [51, 13], [49, 13], [49, 20], [55, 14], [73, 13], [80, 20], [80, 96]];
  const jr = [0, 10, 6, 2, 1, 1, 2.5, 2.5, 1, 1, 2, 3, 6, 4, 6];
  const run = S.union([S.cone(31, 72, 31.3, 90, 1.2, 2.4), S.ellipse(31.5, 92.2, 4.6, 2.6)], 1.6);
  CHAPTER_OBJ["Chapter 54: Corrosive Materials"] = {
    base: "cream",
    d: OBJ_poly(jug.concat(arc.slice(0, -1)), jr.concat(arc.slice(0, -1).map(() => 0))),
    holes: [OBJ_rrect(57, 21, 14, 17, 5)],
    plates: [
      ["water", OBJ_poly(arc.concat([[20, aEnd[1]], [20, 96], [arc[0][0], 96]]), arc.map(() => 0).concat([0, 6, 0])), { z: .2, bev: .6, dome: .5, col: "#86C232" }],   /* the puddle */
      ["cream", OBJ_rrect(52, 12, 28, 30, [7, 6, 2, 2]), { dome: .9 }],                            /* the handle */
      ["glow", OBJ_rrect(26, 47, 48, 40, 5), { z: -.8, bev: .9 }],                               /* the panel pressed in */
      ["field", "M21 43H79M21 91H79", { ln: 1.6, cut: .8, paint: 0 }],                            /* the moulded ribs */
      ["cream", OBJ_rrect(33, 12, 16, 12, 1), { z: .3 }],                                         /* the neck */
      ["red", OBJ_rrect(31, 4, 20, 9.5, 2.5), { z: .6, bev: .6 }],                               /* the cap */
      ["deep", "M35 6.5V11M39 6.5V11M43 6.5V11M47 6.5V11", { ln: 1.3, cut: .6, paint: 0 }],       /* its knurling */
      ["glow", "M29.6 62.4L32.4 64.6L30.4 66.8L32.4 68.4", { ln: 1.3, cut: .9, paint: 0 }],           /* the split it seeps from */
      ["water", S.shape(run, BB), { z: .6, bev: .6, dome: 1.1, col: "#86C232" }],                 /* the acid running down */
    ],
  };
}

/* ---- Chapter 55: Cryogenic Fluids - a dewar: the round, squat steel tank with its lugs and frosted band, the neck and stopper, and the
   cold vapour billowing out of the neck as part of the silhouette. ---- */
{
  const CY = 66, sL = P4_arc(50, CY, 30, 24, 180, 250.5, 7), sR = P4_arc(50, CY, 30, 24, 289.5, 360, 7), NY = CY - 22.6;
  /* the vapour: a cloud of four puffs on a short stem, as one outline - the boundary of their union, walked round its centre (it is
     star-shaped about it), from the stem's left foot clockwise to its right foot */
  /* the vapour: three wavy wisps rising off the stopper, as part of the outline (each a ribbon round a wavy centreline, upright at its
     foot so it stands square on the stopper; the same phase, so the gaps between them stay even) */
  const LT = 28, wisp = (x, top) => { const c = []; for(let k = 0; k <= 12; k++){ const t = k / 12; c.push([x + 3 * (1 - Math.cos(3 * Math.PI * t)) / 2, LT - (LT - top) * t]); }
    return P4_ribbon(c, c.map((p, k) => 5.8 - .6 * k / 12)); };
  const W1 = wisp(39.5, 9), W2 = wisp(49, 3.5), W3 = wisp(58.5, 9);
  const cloud = W1.concat(W2).concat(W3);
  const pts = [[20, 96], [20, CY + 16], [11, CY + 16], [11, CY + 2], [20, CY + 2]].concat(sL.slice(1, -1)).concat([[40, NY], [40, LT + 8], [34, LT + 8], [34, LT]])
    .concat(cloud).concat([[66, LT], [66, LT + 8], [60, LT + 8], [60, NY]]).concat(sR.slice(1, -1)).concat([[80, CY + 2], [89, CY + 2], [89, CY + 16], [80, CY + 16], [80, 96]]);
  const rs = pts.map(() => 0);
  [[0, 8], [1, 1], [2, 3], [3, 3], [4, 1]].forEach(q => { rs[q[0]] = q[1]; });
  const n = pts.length; [[n - 1, 8], [n - 2, 1], [n - 3, 3], [n - 4, 3], [n - 5, 1]].forEach(q => { rs[q[0]] = q[1]; });
  const iL = 5 + sL.length - 2; [[iL, 1], [iL + 1, 1], [iL + 2, 1.5], [iL + 3, 2]].forEach(q => { rs[q[0]] = q[1]; });
  const iR = iL + 4 + cloud.length - 1; [[iR, 1], [iR + 1, 2], [iR + 2, 1.5], [iR + 3, 1], [iR + 4, 1]].forEach(q => { rs[q[0]] = q[1]; });
  const tank = OBJ_poly([[20, 96], [20, CY]].concat(sL.slice(1)).concat(P4_arc(50, CY, 30, 24, 250.5, 289.5, 3).slice(1, -1)).concat(sR.slice(0, -1)).concat([[80, CY], [80, 96]]),
    [8, 0].concat(sL.slice(1).map(() => 0)).concat([0, 0]).concat(sR.slice(0, -1).map(() => 0)).concat([0, 8]));
  CHAPTER_OBJ["Chapter 55: Cryogenic Fluids"] = {
    base: "steel",
    d: OBJ_poly(pts, rs),
    plates: [
      ["steel", tank, { dome: 2 }],                                                               /* the insulated steel tank */
      ["glass", OBJ_rrect(20, CY + 4, 60, 9, 0), { z: .6, bev: .7 }],                            /* its frosted band */
      ["steel", "M21 " + (CY + 21) + "H79", { ln: 1.6, cut: .8, paint: 0 }],                      /* a groove */
      ["rubber", OBJ_rrect(11, CY + 2, 12, 14, 3), { dome: .9 }],                                  /* the lugs */
      ["rubber", OBJ_rrect(77, CY + 2, 12, 14, 3), { dome: .9 }],
      ["steel", OBJ_rrect(40, LT + 7, 20, NY - LT - 5, 1), { z: .4, bev: .5 }],                  /* the neck */
      ["rubber", OBJ_rrect(34, LT, 32, 8, 2), { gem: 1, gw: 2 }],                                    /* the stopper */
      ["glow", OBJ_poly(W1, 0), { dome: 1.2 }],                                                     /* the vapour */
      ["glow", OBJ_poly(W2, 0), { dome: 1.2 }],
      ["glow", OBJ_poly(W3, 0), { dome: 1.2 }],
    ],
  };
}

/* ---- Chapter 56: Explosives and Fireworks - a firework rocket: the faceted nose cone, the paper body with its spiral wraps, the fins,
   and the guide stick. Symmetric. ---- */
{
  /* (384.79) a fifth wider about its axis (X): its back's title was 8.9 CSS px in your hand, under the 9.2 every back is held to */
  const X = x => 50 + (x - 50) * 1.2;
  const half = [[50, 2], [X(54.5), 6.5], [X(58.5), 11.5], [X(61.5), 17], [X(63.3), 22], [X(64), 26], [X(64), 47], [X(78), 67], [X(78), 80], [X(64), 73], [X(64), 77], [53, 77], [53, 97]];
  const hr = [2, 0, 0, 0, 0, 1, 1, 3, 3.5, 1, 2, 1, 2.5];
  const left = half.slice(1).reverse().map(p => [100 - p[0], p[1]]), lr = hr.slice(1).reverse();
  const cone = OBJ_poly([[50, 2], [54.5, 6.5], [58.5, 11.5], [61.5, 17], [63.3, 22], [64, 26.5], [36, 26.5], [36.7, 22], [38.5, 17], [41.5, 11.5], [45.5, 6.5]].map(p => [X(p[0]), p[1]]), [2, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]);
  const wrap = k => OBJ_poly([[X(36), 34 + k], [X(64), 42 + k], [X(64), 48 + k], [X(36), 40 + k]], .8);
  CHAPTER_OBJ["Chapter 56: Explosives and Fireworks"] = {
    base: "red",
    d: OBJ_poly(half.concat(left), hr.concat(lr)),
    plates: [
      ["red", OBJ_rrect(X(36), 26, X(64) - X(36), 51, [0, 0, 2, 2]), { dome: 1.6 }],            /* the body */
      ["cream", wrap(0), { z: .5, bev: .6 }],                                                       /* its spiral wraps */
      ["cream", wrap(14), { z: .5, bev: .6 }],
      ["cream", wrap(28), { z: .5, bev: .6 }],
      ["brass", cone, { gem: 1.6, gw: 6 }],                                                          /* the nose cone, faceted */
      ["brass", OBJ_rrect(X(35), 24.5, X(65) - X(35), 4, 1.5), { z: .5, bev: .5 }],                 /* its rim */
      ["brass", OBJ_poly([[X(64), 47], [X(78), 67], [X(78), 80], [X(64), 73]], [0, 3, 3.5, 0]), { z: .3, bev: .8 }],   /* the fins */
      ["brass", OBJ_poly([[X(36), 47], [X(22), 67], [X(22), 80], [X(36), 73]], [0, 3, 3.5, 0]), { z: .3, bev: .8 }],
      ["wood", OBJ_rrect(47, 74, 6, 23, [0, 0, 2.5, 2.5]), { dome: .7 }],                          /* the stick */
    ],
  };
}

/* ---- Chapter 58: Flammable Gases and Flammable Cryogenic Fluids - a flip-top lighter, open: the case, the lid standing up on its hinge,
   the chimney with its two windows cut right through, and the flame. ---- */
{
  const flame = [[30, 30], [27, 24.5], [25.5, 18], [27, 11], [31.5, 5.5], [37.5, 1.5], [36.5, 6], [41, 9], [45.5, 13.5], [47.5, 19.5], [46, 25.5], [42, 30]];
  const fr = [1, 3, 4, 4, 3, 1.4, 1.6, 3, 4, 4, 3, 1];
  const pts = [[16, 97], [16, 54], [20, 54], [20, 30]].concat(flame).concat([[52, 30], [52, 54], [58, 54], [58, 16], [76, 16], [76, 56], [68, 56], [68, 97]]);
  const rs = [6, 2, 1, 2].concat(fr).concat([2, 1, 1, 5, 5, 2, 1, 6]);
  const inner = OBJ_poly([[32, 30], [30.5, 25], [31, 19], [34.5, 13], [37.5, 9.5], [39, 14], [42.5, 18], [43, 24], [40, 30]], [1, 3, 3, 2.5, 1.2, 2.5, 3, 3, 1]);
  CHAPTER_OBJ["Chapter 58: Flammable Gases and Flammable Cryogenic Fluids"] = {
    base: "brass",
    d: OBJ_poly(pts, rs),
    holes: [OBJ_rrect(26, 36, 7, 12, 2.5), OBJ_rrect(39, 36, 7, 12, 2.5)],
    plates: [
      ["brass", OBJ_rrect(16, 54, 52, 43, [2, 0, 6, 6]), { dome: 1.5 }],                          /* the case */
      ["brass", "M17 61H67", { ln: 1.5, cut: .7, paint: 0 }],                                      /* its seam */
      ["brass", OBJ_rrect(58, 16, 18, 40, [5, 5, 2, 2]), { dome: 1 }],                               /* the lid, standing open */
      ["steel", OBJ_rrect(20, 30, 32, 25, 1.5), { z: .5, bev: .6 }],                               /* the chimney */
      ["steel", OBJ_rrect(57, 49, 10, 9, 2.5), { dome: 1 }],                                        /* the hinge */
      ["red", OBJ_poly(flame.concat([[42, 31], [30, 31]]), fr.concat([0, 0])), { dome: 1.5 }],     /* the flame */
      ["hot", inner, { dome: 1.1 }],                                                                /* its hot heart */
      ["glow", OBJ_ellipse(36.5, 25, 3, 4.5), { dome: .8 }],
    ],
  };
}

/* ---- Chapter 59: Flammable Solids - a box of safety matches, open, and one match struck. (384.133 badgeart, Madison: "change that,
   that's bad. Make it great." Round 9's open tray with seven heads standing up in a row, the middle one burning, read as a birthday
   cake with candles.) Now the box everyone knows, seen from above at an angle: the blue sleeve with its cream label and a red flame on
   it, the brown striking strip down its side, its end; the drawer pushed half out, full of matches lying in it, their red heads lined
   up at its open end; and one match lifted out of it and struck - its stick, its head and the flame standing off it. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const P = (x, w) => [x + 8 * w, 74 - 26 * w];                             /* a point on the box's top plane: x along it, w across (0 front, 1 back) */
  const DL = 9, SL = 34, SR = 89, H = 10;                                   /* the drawer's front end, the sleeve's two ends, the thickness */
  const dn = ([x, y]) => [x, y + H];
  const f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  const box = S.grow(S.grow(S.poly([dn(P(DL, 0)), P(DL, 0), P(DL, 1), P(SR, 1), dn(P(SR, 1)), dn(P(SR, 0))]), -.9), .9);
  /* the struck match: from inside the drawer up and to the left; its head; the flame off it */
  const M0 = [27, 57], M1 = [14.5, 23], ux = (M1[0] - M0[0]), uy = (M1[1] - M0[1]), ul = Math.hypot(ux, uy), u = [ux / ul, uy / ul];
  const HC = [M1[0] + u[0] * 2, M1[1] + u[1] * 2];
  const stick = S.capsule(M0[0], M0[1], M1[0], M1[1], 2.6), head = S.ellipse(HC[0], HC[1], 4.4, 4.4);
  const flame = S.union([S.circle(HC[0] - 1.4, HC[1] - 6.5, 6.6), S.cone(HC[0] - 1.4, HC[1] - 6.5, HC[0] - 5.5, 2.5, 6.6, 1)], 2.2);
  const all = S.union([box, stick, head, flame], 1.2);
  /* the matches in the drawer, lying along it, heads at its open end */
  let sticks = "", heads = "";
  for(let k = 0; k < 6; k++){ const w = .13 + k * .148, h = P(DL + 4.2, w), e = P(SL, w);
    sticks += "M" + f([h[0] + 2, h[1] + 1.2]) + "L" + f([e[0], e[1] + 1.2]);
    heads += OBJ_ellipse(h[0], h[1] + 1.2, 3.6, 2.6); }
  const quad = (a, b, c, d, r) => OBJ_poly([a, b, c, d], r), FE = P(61.5, .5);
  CHAPTER_OBJ["Chapter 59: Flammable Solids"] = {
    d: S.shape(all, BB),
    col: "#2E6FB8", base: "field",
    plates: [
      ["cardboard", quad(P(DL, 0), P(SL, 0), P(SL, 1), P(DL, 1), .8), { col: "#D8B98C" }],                                   /* the drawer's rim */
      ["wood", quad(P(DL + 1.6, .07), P(SL, .07), P(SL, .94), P(DL + 1.6, .94), .6), { z: -1.2, bev: .6, col: "#6E4B2A" }],   /* inside it */
      ["wood", sticks, { ln: 2.4, z: -.6, bev: .4, col: "#E2C38F" }],                                                         /* the matches lying in it */
      ["red", heads, { z: -.2, bev: .5, dome: .9, col: "#D8352C" }],                                                          /* their heads */
      ["cardboard", quad(P(DL, 0), P(SL, 0), dn(P(SL, 0)), dn(P(DL, 0)), [.8, 0, 0, .8]), { z: .2, bev: .5, col: "#D8B98C" }], /* the drawer's front */
      ["field", quad(P(SL, 0), P(SR, 0), P(SR, 1), P(SL, 1), .8), { dome: .8 }],                                              /* the sleeve's top */
      ["cream", quad(P(SL + 5, .17), P(SR - 5, .17), P(SR - 5, .83), P(SL + 5, .83), 1.6), { z: .5, bev: .6, col: "#F4EEDC" }],   /* its label */
      ["red", S.shape(S.union([S.circle(FE[0], FE[1] + 3, 4.4), S.cone(FE[0], FE[1] + 3, FE[0] + 1.6, FE[1] - 10, 4.4, .7), S.cone(FE[0] - 1.6, FE[1] + 2.4, FE[0] - 4.4, FE[1] - 3.8, 3, .6)], 2.2), BB), { z: .4, bev: .4, dome: .5, col: "#E2412F" }],   /* the flame on it */
      ["leather", quad(P(SL, 0), P(SR, 0), dn(P(SR, 0)), dn(P(SL, 0)), [0, 0, .8, 0]), { z: .2, bev: .5, col: "#6B3F22" }],     /* the striking strip down its side */
      ["leather", "M" + f([SL + 3, 76.5]) + "H" + (SR - 3) + "M" + f([SL + 3, 80]) + "H" + (SR - 3), { ln: 1, cut: .4, paint: 0 }],
      ["shade", quad(P(SR, 0), P(SR, 1), dn(P(SR, 1)), dn(P(SR, 0)), [0, .8, .8, .8]), { z: .1, bev: .5 }],                     /* the sleeve's end */
      ["wood", S.shape(stick, BB), { z: 1, bev: .7, dome: .5, col: "#E2C38F" }],                                               /* the struck match */
      ["hot", S.shape(flame, BB), { z: .8, dome: 1.4, col: "#FF8A2A" }],                                                        /* its flame */
      ["glow", S.shape(S.union([S.circle(HC[0] - 1.2, HC[1] - 5.2, 3.4), S.cone(HC[0] - 1.2, HC[1] - 5.2, HC[0] - 3.6, 9.5, 3.4, .6)], 1.4), BB), { z: 1.3, bev: .6, dome: .8, col: "#FFE9A8" }],   /* its heart */
      ["red", S.shape(head, BB), { z: 1.4, bev: .6, dome: 1.6, col: "#C9302A" }],                                               /* its head, burning */
    ],
  };
}

/* ---- Chapter 60: Highly Toxic and Toxic Materials - a coffin-shaped poison bottle: the cork, the lip, the faceted body widest at the
   shoulder, and its raised front panel quilted with grooves (poison was moulded to be known by touch in the dark). ---- */
{
  const body = [[57, 27], [76, 42], [67, 97], [33, 97], [24, 42], [43, 27]];
  const panel = [[50, 36], [64, 45], [58.5, 88], [41.5, 88], [36, 45]];
  const segs = [];
  /* (384.133 badgeart) the quilting is clipped to the panel drawn 1.6 smaller, so no groove runs off its rounded corners onto the body */
  const pc = panel.reduce((a, p) => [a[0] + p[0] / panel.length, a[1] + p[1] / panel.length], [0, 0]);
  const inset = panel.map(p => { const dx = p[0] - pc[0], dy = p[1] - pc[1], l = Math.hypot(dx, dy); return [p[0] - dx / l * 2.4, p[1] - dy / l * 2.4]; });
  for(let k = -60; k <= 60; k += 8.5){ segs.push(P4_clip([20 + k, 30], [80 + k, 100], inset)); segs.push(P4_clip([80 - k, 30], [20 - k, 100], inset)); }
  CHAPTER_OBJ["Chapter 60: Highly Toxic and Toxic Materials"] = {
    d: OBJ_poly([[43, 2], [57, 2], [57, 12], [61, 12], [61, 19], [57, 19]].concat(body).concat([[43, 19], [39, 19], [39, 12], [43, 12]]),
      [2.5, 2.5, 1, 1.5, 1.5, 1, 3, 5, 5, 5, 5, 3, 1, 1.5, 1.5, 1]),
    plates: [
      ["field", OBJ_poly(body, [3, 5, 5, 5, 5, 3]), { gem: 1.5, gw: 6 }],                            /* the faceted body */
      ["body", OBJ_poly(panel, [2, 3, 3, 3, 3]), { z: .8, bev: .9 }],                                 /* its raised front */
      ["body", P4_lines(segs), { ln: 1.4, cut: .7, paint: 0 }],                                       /* quilted */
      ["field", OBJ_rrect(43, 18, 14, 11, 0), { z: .2 }],                                             /* the neck */
      ["shade", OBJ_rrect(39, 12, 22, 7, 2), { z: .5, bev: .6 }],                                     /* the lip */
      ["wood", OBJ_rrect(43, 2, 14, 11, [2.5, 2.5, 0, 0]), { dome: 1 }],                              /* the cork */
      ["wood", "M44 6H56", { ln: 1.2, cut: .5, paint: 0 }],
    ],
  };
}

/* ---- Chapter 61: Liquefied Petroleum Gases - a squat propane (barbecue) tank: the guard collar on top with the valve in its window, the
   domed tank with its welded seam, and the foot ring with its slots. (384.133 badgeart, Madison: "those parts just don't look smooth where
   I circled. It doesn't seem to go together.") (384.133 art3, Madison: "Blue tank has the same issue, fix it." The collar still sat on
   the dome like a separate piece, and the curved shoulder strip under it stopped short in square ends, off the tank.) The collar is now
   welded on as a real one is: it is a short steel cylinder standing on the dome, so its foot is a ring round the dome - seen from the
   front that ring is an arc that dips down the dome's face between the two points where the collar meets the dome's outline. The foot
   ring follows that arc and runs out into the dome's outline at both ends; the collar's sides flare down into it; the outline is one
   filleted curve from the dome up the collar. Under the foot ring the dome takes its shadow, and the foot ring at the bottom takes the
   tank's. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const DC = [50, 52], DR = [40, 30];
  const domeY = x => DC[1] - DR[1] * Math.sqrt(Math.max(0, 1 - ((x - DC[0]) / DR[0]) ** 2));
  const topDome = S.inter(S.ellipse(DC[0], DC[1], DR[0], DR[1]), S.box(0, 0, 100, 52.5, 0));
  const tank = S.union([topDome, S.box(10, 52, 80, 18, 0), S.inter(S.ellipse(50, 70, 40, 16), S.box(0, 69.5, 100, 31, 0))], 0);
  const foot = S.box(26, 80, 48, 17, 2.5);
  /* the collar's foot: where a ring round the dome at the collar's width is seen from a little above - an arc from the dome's outline
     at x = 50 -/+ FW, dipping DIP below it in the middle */
  const FW = 21, DIP = 4.6, y0 = domeY(50 - FW);
  const arcY = x => y0 + DIP * Math.max(0, 1 - ((x - 50) / FW) ** 2);
  const arc = (dy, x0, x1) => { const o = []; for(let i = 0; i <= 28; i++){ const x = x0 + (x1 - x0) * i / 28; o.push([x, arcY(x) + dy]); } return o; };
  /* the collar: its top, its sides flaring to the foot, which ends on the dome's outline at both sides and follows the arc between */
  const below = S.poly(arc(1.4, 0, 100).concat([[100, 100], [0, 100]]));
  /* (384.136 art4, Madison circled both ends of the foot ring where it met the dome's outline: it ran out INTO the outline, leaving a
     notch and a stray light line at each side.) The collar's foot and its ring now stop a little inside the dome's face, the ring's ends
     rounded, so the dome's outline runs on unbroken and the collar joins it with the outline's own fillet. */
  const collar = S.minus(S.grow(S.poly([[38.6, 8.6], [61.4, 8.6], [50 + FW - 5.4, y0 + 2], [50 - FW + 5.4, y0 + 2]]), 2.6), below);
  /* the ring thins toward its ends, where the dome's outline comes down close over the collar's foot: its top edge keeps just inside
     the outline, and it ends round under the collar's flare */
  const HR = FW - 2.2, rTop = [], rBot = [];
  for(let i = 0; i <= 40; i++){ const x = 50 - HR + 2 * HR * i / 40, t = Math.max(arcY(x) - 2.8, domeY(x) + 1.5), b = Math.max(arcY(x) + 1.4, t + 1.9);
    rTop.push([x, t]); rBot.push([x, b]); }
  const ring = S.grow(S.grow(S.poly(rTop.concat(rBot.reverse())), -.7), .7);
  const all = S.union([tank, foot, S.union([collar, ring], 1.5)], 2.6);
  const lp = f => S.loops(f, BB).map(S.pathOf).join("");
  const shadowUnder = S.inter(S.minus(S.poly(arc(4.4, 50 - FW + 1, 50 + FW - 1).concat(arc(-1, 50 + FW - 1, 50 - FW + 1))), ring), S.grow(tank, -1.6));
  CHAPTER_OBJ["Chapter 61: Liquefied Petroleum Gases"] = {
    base: "water",
    d: S.shape(all, BB),
    plates: [
      ["steel", OBJ_rrect(26, 80, 48, 17, [0, 0, 2.5, 2.5]), { z: .3 }],                               /* the foot ring */
      ["rubber", OBJ_rrect(33, 88, 10, 5, 2), { z: -1, bev: .5 }],                                        /* its slots */
      ["rubber", OBJ_rrect(57, 88, 10, 5, 2), { z: -1, bev: .5 }],
      ["ink", lp(S.inter(S.minus(S.grow(tank, 2.2), tank), S.box(26, 70, 48, 27, 2.5))), { z: .15, bev: .6, col: "#4B5158" }],   /* the tank's shadow on it */
      ["water", S.shape(tank, BB), { dome: 2 }],                                                        /* the tank */
      ["water", OBJ_rrect(10, 54, 80, 6, 0), { z: .7, bev: .7 }],                                      /* its welded seam */
      /* (384.136 art4) the dome's shadow band under the collar is gone: stopped inside the dome, its square ends read as a slab */
      ["steel", S.shape(S.union([collar, ring], 1.5), BB), { z: .5, bev: .9, dome: .7 }],               /* the collar and its foot: ONE part (art6) */
      /* (384.136 art6) Madison circled the collar's foot: a darker ring with a cut weld line between it and the collar read as two
         pieces stacked on the dome. The foot is the collar's own steel now, flaring out in one soft bevel - no seam between them */
      ["rubber", OBJ_rrect(38, 9, 24, 14, 4), { z: -1.7, bev: .7 }],                                     /* its window */
      ["steel", OBJ_rrect(41.5, 10, 17, 5.5, 2.5), { dome: 1 }],                                      /* the valve's handwheel */
      ["brass", OBJ_rrect(45.5, 15, 9, 8.5, 1.5), { gem: 1, gw: 2.2 }],                               /* the valve */
    ],
  };
}

/* ---- Chapter 62: Organic Peroxides - an insulated cooler (peroxides are kept cold), refined (384.93 r9: a teal box with a lid read as a
   toolbox): the carry handle standing up with a real hole under it, the thick white lid, the tapered body with its raised panel and a
   raised white SNOWFLAKE on it (cold storage, at a glance), the latch, and the grips at each end. ---- */
{
  const sf = (cx, cy, R) => { let p = ""; for(let k = 0; k < 3; k++){ const a = k * Math.PI / 3, c = Math.cos(a), s = Math.sin(a);
      p += "M" + (cx - R * c).toFixed(2) + " " + (cy - R * s).toFixed(2) + "L" + (cx + R * c).toFixed(2) + " " + (cy + R * s).toFixed(2); }
    for(let k = 0; k < 6; k++){ const a = k * Math.PI / 3, c = Math.cos(a), s = Math.sin(a), bx = cx + R * .58 * c, by = cy + R * .58 * s;
      [1, -1].forEach(sg => { const b = a + sg * Math.PI / 4; p += "M" + bx.toFixed(2) + " " + by.toFixed(2) + "L" + (bx + R * .36 * Math.cos(b)).toFixed(2) + " " + (by + R * .36 * Math.sin(b)).toFixed(2); }); }
    return p; };
  CHAPTER_OBJ["Chapter 62: Organic Peroxides"] = {
    d: OBJ_poly([[5, 42], [5, 26], [28, 26], [28, 8], [72, 8], [72, 26], [95, 26], [95, 42], [92, 42], [92, 54], [98, 54], [98, 70], [90.4, 70], [89, 94], [11, 94], [9.6, 70], [2, 70], [2, 54], [8, 54], [8, 42]],
      [1, 6, 1, 7, 7, 1, 6, 1, 1, 1, 3, 3, 1, 8, 8, 1, 3, 3, 1, 1]),
    holes: [OBJ_rrect(35, 14.5, 30, 10.5, 4.5)],
    plates: [
      ["field", OBJ_poly([[8, 42], [92, 42], [89, 94], [11, 94]], [0, 0, 8, 8]), { dome: 1 }],        /* the body */
      ["body", OBJ_poly([[16, 50], [84, 50], [82, 86], [18, 86]], 4), { z: .7, bev: .9 }],            /* its raised panel */
      ["cream", sf(50, 68, 13.5), { ln: 2.6, z: .9, bev: .5, col: "#F7F9FA" }],                       /* the snowflake on it */
      ["shade", OBJ_rrect(28, 8, 44, 20, [7, 7, 0, 0]), { dome: .9 }],                                /* the carry handle */
      ["cream", OBJ_rrect(5, 26, 90, 16, [6, 6, 1, 1]), { dome: 1, col: "#F4F2EC" }],                   /* the lid */
      ["cream", OBJ_rrect(14, 29.5, 72, 7.5, 3), { z: .5, bev: .7, col: "#F4F2EC" }],                    /* its top */
      ["field", "M6 42.5H94", { ln: 1.6, cut: .8, paint: 0 }],                                         /* the seal line */
      ["shade", OBJ_rrect(2, 54, 9, 16, 3), { dome: .9 }],                                             /* the end grips */
      ["shade", OBJ_rrect(89, 54, 9, 16, 3), { dome: .9 }],
      ["steel", OBJ_rrect(43, 37, 14, 13, 2.5), { dome: 1 }],                                          /* the latch */
    ],
  };
}

/* ---- Chapter 63: Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids - an oxygen cylinder with its regulator. (384.133 badgeart,
   Madison, of round 9's flame-over-circle: "I don't even know what that is. Change that and make it great." The oxygen mask, option B,
   had not been liked enough either.) Oxygen is the oxidizing gas an inspector meets everywhere - hospitals, welding shops, homes - so
   the chapter is its cylinder: a green steel cylinder with the white shoulder of an oxygen bottle, the brass valve at its neck under its
   handwheel, and the regulator screwed onto the valve with its big round gauge - a chrome bezel, a white dial with its marks and the
   needle. The gauge stands out to the side, so the outline is nothing else's (Chapter 53's plain cylinder with its cap is the closest
   object, and they do not share a shape). (384.133 art3, Madison: "It's gotta be a nice connection from that top piece to the actual
   tank. Make that way better." The valve, its cap and the gauge sat on top of the white shoulder as separate pieces.) Now the cylinder
   has a NECK: the shoulder rises into it in one filleted curve (the white paint runs up it), a steel neck ring with its threads rings
   it, and the brass valve body is seated in that ring - its foot goes down inside it. The handwheel sits on the valve's stem; the valve's
   side outlet carries the regulator's hex nut, and the regulator's arm runs straight into the gauge's case. One outline, every join
   filleted; nothing stands on the shoulder by itself. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const body = S.box(16, 33, 50, 64, 7.5), dome = S.ellipse(41, 34, 25, 13);
  /* (384.136 art6) Madison circled both sides under the neck ring: the neck was 2 narrower than the ring, so a dark notch of background
     showed each side between the ring and the shoulder. The neck is the ring's own width now - the ring is a band round it, flush. */
  const neck = S.box(34.5, 14, 13, 12, 1);
  const cyl = S.union([body, dome, neck], 5);                                   /* the shoulder rises into the neck in one curve */
  /* (384.136 art4, Madison: the connection "looks better but it's not perfect", circling the ring where it meets the neck and the valve.)
     The ring is seated: a hair wider than the neck (a 1-unit lip each side, not 2), the neck's white running up into it with the
     cylinder's own fillet; the regulator's nut comes down onto the ring's top (no notch between them) and the arm joins the outline with a small fillet, so no brass
     drops down beside the ring and no shadowed wedge runs down the neck's right side. */
  const ring = S.box(34.5, 13, 13, 5.5, 1.2);                                     /* the neck ring */
  const valve = S.box(36, 4.5, 10, 10, 1.2), stem = S.box(39, 3, 4, 3, .6), wheel = S.box(32.5, .8, 17, 4.6, 2.3);
  const nut = S.box(46.5, 4.6, 6.5, 8.6, 1), arm = S.box(52, 6.8, 12, 5, 1.5), gauge = S.circle(73, 12.5, 12);
  const all = S.union([S.union([cyl, ring, S.union([valve, stem, wheel], 1)], 1.2), S.union([nut, arm, gauge], 1.6)], 0);   /* (art6) the regulator's nut overhangs the ring with clear space under it: no fillet there (it read as a stray wedge) */
  let ticks = ""; for(let k = 0; k <= 8; k++){ const t = (135 + k * 33.75) * Math.PI / 180;
    ticks += "M" + (73 + 5.7 * Math.cos(t)).toFixed(2) + " " + (12.5 + 5.7 * Math.sin(t)).toFixed(2) + "L" + (73 + 7.4 * Math.cos(t)).toFixed(2) + " " + (12.5 + 7.4 * Math.sin(t)).toFixed(2); }
  CHAPTER_OBJ["Chapter 63: Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids"] = {
    d: S.shape(all, BB),
    col: "#2E8B57", base: "field",
    plates: [
      ["field", S.shape(cyl, BB), { dome: 2 }],                                                          /* the cylinder */
      ["cream", S.shape(S.inter(S.union([cyl, S.inter(all, S.box(30, 15, 17.5, 10, 0))], 0), S.box(0, 0, 100, 42, 0)), BB), { z: .2, bev: .5, dome: 1.6, col: "#F2F0EA" }],   /* its white shoulder, up the neck */
      ["field", "M17 42H65", { ln: 1.4, cut: .6, paint: 0 }],                                           /* where the paint changes */
      ["field", "M17 88.5H65", { ln: 1.6, cut: .8, paint: 0 }],                                         /* the foot ring */
      ["brass", S.shape(S.minus(S.inter(all, S.box(0, 0, 61, 13, 0)), cyl), BB), { z: .2, bev: .5 }],     /* the valve gear, every fillet in it brass (above the ring only) */
      ["brass", S.shape(S.union([valve, stem], .8), BB), { z: .3, bev: .6, gem: .8, gw: 2.2 }],           /* the valve body and its stem */
      ["steel", S.shape(S.inter(all, S.box(33, 12.4, 16, 6.1, 0)), BB), { z: .6, bev: .5, dome: .5 }],   /* (art6) the ring fills the outline's fillets at its corners (a green sliver showed there) */                          /* the neck ring it is seated in */
      ["steel", "M35.5 14.9H46.5M35.5 16.8H46.5", { ln: .7, cut: .4, paint: 0 }],                                 /* its threads */
      ["rubber", OBJ_rrect(32.5, .8, 17, 4.6, 2.3), { z: .4, dome: 1, col: "#2B2E33" }],                 /* the handwheel */
      ["rubber", "M36 1.9V4.4M39.5 1.9V4.4M43 1.9V4.4M46.5 1.9V4.4", { ln: 1, cut: .5, paint: 0 }],
      ["brass", S.shape(S.union([arm, S.inter(gauge, S.box(0, 0, 66, 100, 0))], 1.6), BB), { z: .2, dome: .8 }],   /* the regulator's arm into the gauge's case */
      ["brass", OBJ_rrect(46.5, 4.6, 6.5, 8.6, 1), { z: .5, bev: .5, gem: .9, gw: 1.8 }],                 /* its hex nut on the valve's outlet */
      ["steel", OBJ_circle(73, 12.5, 12), { z: .3, dome: 1.2 }],                                         /* the gauge's chrome bezel */
      ["cream", OBJ_circle(73, 12.5, 8.9), { z: -.2, bev: .5, dome: .3, col: "#F7F6F1" }],                  /* its dial */
      ["ink", ticks, { ln: 1.1, z: .1, bev: .2 }],                                                      /* its marks */
      ["red", "M73 12.5L77.6 7.7", { ln: 1.8, z: .5, bev: .3, col: "#C8302A" }],                             /* its needle */
      ["steel", OBJ_circle(73, 12.5, 2.1), { dome: .8 }],
    ],
  };
}
