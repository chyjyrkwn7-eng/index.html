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
   of the lid, the green leak." The round-9 drop hung from under the cap, so the cap looked like what was leaking.) The cap is clean and
   sealed; the acid seeps from a split low in the jug's side.
   (art10) Madison circled the drip and the puddle: the run was a stiff green spike (a straight cone) standing on the puddle, and the
   puddle a flat lens jammed against the jug's foot at the jug's own height. Now the acid RUNS: a rivulet from the split that wanders a
   little as it goes down the jug's side, swells into a bead low down and spreads where it reaches the ground; the puddle is an uneven
   pool on the floor - in front of the jug and out to its left, lower than the jug (the jug stands IN it: its foot drops into the pool
   all along, no seam), with a soft edge, a domed sheen and a few bubbles where the acid lands (it fizzes). The panel and the lower rib
   stop short of the run so it lies on plain plastic. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100], FT = 93;                         /* FT: the jug's foot, on the floor */
  const jug = [[20, FT], [20, 36], [26, 26], [33, 22], [33, 13], [31, 13], [31, 4], [51, 4], [51, 13], [49, 13], [49, 20], [55, 14], [73, 13], [80, 20], [80, FT]];
  const jr = [1, 10, 6, 2, 1, 1, 2.5, 2.5, 1, 1, 2, 3, 6, 4, 1];
  const jugD = OBJ_poly(jug, jr), jugF = S.poly(OBJ_walk(jugD));
  /* the pool on the floor, seen a little from above: a wide flat lobe in front of the jug, one out to its left (reaching back beside
     it) and one running on to the right in front - joined softly, so its edge wanders */
  const pool = S.union([S.ellipse(31, 95.6, 26.5, 4), S.ellipse(11.5, 92.2, 8.4, 3.9), S.ellipse(57, 96.7, 14, 2.8), S.ellipse(78.5, 95.6, 7, 3), S.ellipse(5.8, 97.4, 3.2, 1.9)], 4.5);
  const all = S.union([jugF, pool], 4);
  /* the run: a centreline from the split down the jug's side, its half-width swelling into a bead near the foot, and a foot that
     spreads into the pool */
  const N = 30, segs = [], cl = t => [26.45 + .55 * Math.sin(t * Math.PI * 1.15 + .2), 59.9 + 33.1 * t], rw = t => .85 + .5 * t;
  for(let i = 0; i < N; i++){ const a = cl(i / N), b = cl((i + 1) / N); segs.push(S.cone(a[0], a[1], b[0], b[1], rw(i / N), rw((i + 1) / N))); }
  const bx = cl(.64)[0], bead = S.union([S.cone(bx - .05, 77, bx + .1, 82, .95, 2.35), S.circle(bx + .1, 82, 2.35)], 0);   /* a bead: a long taper above, round below */
  const run = S.inter(S.union([S.union(segs, 0), bead, S.ellipse(26.2, 93, 2.8, 1.5)], 1.1), jugF);   /* it pours into the pool at the jug's foot: the pool is the same acid */
  CHAPTER_OBJ["Chapter 54: Corrosive Materials"] = {
    base: "cream",
    d: S.shape(all, BB),
    holes: [OBJ_rrect(57, 21, 14, 17, 5)],
    plates: [
      ["water", S.shape(S.minus(all, jugF), BB), { z: -1, bev: 1.6, dome: .6, col: "#86C232" }],          /* the pool, on the floor: lower than the jug, its foot dropping into it */
      ["cream", OBJ_rrect(52, 12, 28, 30, [7, 6, 2, 2]), { dome: .9 }],                            /* the handle */
      ["glow", OBJ_rrect(32, 47, 42, 38, 5), { z: -.8, bev: .9 }],                               /* the panel pressed in */
      ["field", "M21 43H79M31 88.5H79", { ln: 1.6, cut: .8, paint: 0 }],                          /* the moulded ribs (the lower one stops short of the run) */
      ["cream", OBJ_rrect(33, 13.5, 16, 10.5, [0, 0, 1, 1]), { z: .3 }],                          /* the neck, from under the cap (art9: its top showed through the cap as a step) */
      ["red", OBJ_rrect(31, 4, 20, 9.5, [2.5, 2.5, 1, 1]), { z: .6, bev: .6 }],                  /* the cap */
      ["deep", "M35 6.5V11M39 6.5V11M43 6.5V11M47 6.5V11", { ln: 1.3, cut: .6, paint: 0 }],       /* its knurling */
      ["ink", "M24.2 59.6Q26.4 58.5 28.7 59.4", { ln: 1, z: -.45, bev: .3, col: "#6E6253" }],          /* the split it seeps from */
      ["water", S.shape(run, BB), { z: .75, bev: 1.4, col: "#86C232" }],                  /* the acid running down */
      ["water", OBJ_circle(33.5, 96.2, 1.35) + OBJ_circle(37.6, 95.1, .95) + OBJ_circle(21.8, 97.4, 1.05), { z: .2, bev: .3, dome: .5, col: "#C6EE7C" }],   /* where it lands, fizzing */
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
  const tank = OBJ_poly([[20, 96], [20, CY]].concat(sL.slice(1)).concat(P4_arc(50, CY, 30, 24, 250.5, 289.5, 12).slice(1, -1)).concat(sR.slice(0, -1)).concat([[80, CY], [80, 96]]),
    [8, 0].concat(sL.slice(1).map(() => 0)).concat(P4_arc(50, CY, 30, 24, 250.5, 289.5, 12).slice(1, -1).map(() => 0)).concat(sR.slice(0, -1).map(() => 0)).concat([0, 8]));
  CHAPTER_OBJ["Chapter 55: Cryogenic Fluids"] = {
    base: "steel",
    d: OBJ_poly(pts, rs),
    plates: [
      ["steel", tank, { dome: 2 }],                                                               /* the insulated steel tank */
      ["glass", OBJ_rrect(20, CY + 4, 60, 9, 0), { z: .6, bev: .7 }],                            /* its frosted band */
      ["steel", "M21 " + (CY + 21) + "H79", { ln: 1.6, cut: .8, paint: 0 }],                      /* a groove */
      ["rubber", OBJ_rrect(11, CY + 2, 12, 14, 3), { dome: .9, lvl: "lug" }],                      /* the lugs (art9: flat over the tank's side and the band, whose edges showed through them) */
      ["rubber", OBJ_rrect(77, CY + 2, 12, 14, 3), { dome: .9, lvl: "lug" }],
      /* (art9) the neck stands on the tank's crown (it ran 2 on over it, so the crown's edge showed through it), and the crown is a
         smooth arc (three straight pieces glinted as beads along it) */
      ["steel", OBJ_SDF.shape(OBJ_SDF.minus(OBJ_SDF.box(40, LT + 7, 20, NY - LT - 5, 0), OBJ_SDF.ellipse(50, CY, 30, 24)), [0, 0, 100, 100]), { z: .4, bev: .5 }],   /* the neck */
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
      ["wood", OBJ_rrect(47, 77, 6, 20, [0, 0, 2.5, 2.5]), { dome: .7 }],                          /* the stick, from the body's foot (art9: run up under it, its top showed through as a tab) */
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
      ["steel", OBJ_rrect(20, 30, 32, 25, 1.5), { z: .5, bev: .6, lvl: "chimney" }],               /* the chimney (art9: flat over the case's top edge, which showed through it as a step) */
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
  /* the struck match: from inside the drawer up and to the left; its head; the flame off it.
     (art10) Madison circled the head: a red disc sat on top of the flame with the flame behind it. A lit match's head is the end of the
     stick, not a disc: it is ONE relief with the stick now (the stick swells smoothly into an oval head along its own axis, painted red
     where the coating starts and charred dark at its top, where it burns), and the flame rises off it and wraps round its top - an
     orange outer flame, a yellow one inside it and a white-yellow core right at the head, each a teardrop with its tip flickering
     over, each stopping at the head (nothing is drawn under the head to show through it). */
  const M0 = [27, 57], M1 = [14.5, 23], ux = (M1[0] - M0[0]), uy = (M1[1] - M0[1]), ul = Math.hypot(ux, uy), u = [ux / ul, uy / ul];
  const HC = [M1[0] + u[0] * 1.4, M1[1] + u[1] * 1.4], hp = (x, y) => (x - HC[0]) * u[0] + (y - HC[1]) * u[1], hq = (x, y) => (x - HC[0]) * -u[1] + (y - HC[1]) * u[0];
  const oval = (c, a, b) => (x, y) => { const px = x - c[0], py = y - c[1], s = (px * u[0] + py * u[1]) / a, t = (px * -u[1] + py * u[0]) / b; return (Math.hypot(s, t) - 1) * Math.min(a, b); };
  const stick = S.capsule(M0[0], M0[1], M1[0], M1[1], 2.3), head = oval(HC, 5.3, 3.4);
  const match = S.union([stick, head], 2.2);                                   /* the stick swells into its head */
  const tear = (c, r, ctl, tip, rt) => S.union([S.circle(c[0], c[1], r), S.tube(c, ctl, tip, t => rt + (r - rt) * Math.pow(1 - t, 1.35), 26)], 0);
  const FB = [HC[0] + u[0] * 2.3, HC[1] + u[1] * 2.3];                        /* the flame's round foot, on the head's upper half */
  const flame = tear(FB, 6.1, [FB[0] - .9, FB[1] - 7.8], [9.4, 1.2], .6);
  const flameMid = tear([FB[0], FB[1] + .3], 4.4, [FB[0] - .6, FB[1] - 5.4], [10.5, 5.6], .45);
  const CT = [HC[0] + u[0] * 4.4, HC[1] + u[1] * 4.4], core = tear(CT, 3.1, [CT[0] - .2, CT[1] - 3.2], [CT[0] - .8, CT[1] - 6.6], .4);   /* right on the head's top */
  const all = S.union([box, S.union([match, flame], .5)], 1.2);
  /* the matches in the drawer, lying along it, heads at its open end */
  /* (art9) Madison: "There's a lot of spots all over that just don't look right." A part's relief is added to what is under it: each
     lying match's stick ran into its head (a pale hook in every red head), on under the sleeve's edge (a row of bumps down it), and the
     struck match lay over them all (its stick rippled where it crossed each one). Each stick now runs from its head to the sleeve's
     edge, and the lying matches stop where the struck one lies across them. */
  const lyS = [], lyH = [];
  for(let k = 0; k < 6; k++){ const w = .13 + k * .148, h = P(DL + 4.2, w), e = P(SL, w);
    lyS.push(S.capsule(h[0] + 2, h[1] + 1.2, e[0] + 2, e[1] + 1.2, 1.2));
    lyH.push(S.ellipse(h[0], h[1] + 1.2, 3.6, 2.6)); }
  const sleeve = S.poly([P(SL, 0), P(SR, 0), P(SR, 1), P(SL, 1)]), over = S.grow(stick, .2);
  const sticks = S.loops(S.minus(S.minus(S.minus(S.union(lyS, 0), S.union(lyH, 0)), sleeve), over), BB).map(S.pathOf).join("");
  const heads = S.loops(S.minus(S.union(lyH, 0), over), BB).map(S.pathOf).join("");
  const quad = (a, b, c, d, r) => OBJ_poly([a, b, c, d], r);
  /* (art10) Madison circled the flame on the label: a clipped notch at its top (a round body, a straight spike and a side tongue
     joined, with a V between them). It is ONE teardrop now - a round foot, sides that sweep in to a single point, the tip flickering
     over in a gentle S - with its hot heart inside, upright and centred on the label. */
  const LC = P((SL + SR) / 2, .5);                                            /* the label's middle */
  const tear0 = (c, r, ctl, tip, rt, n) => S.union([S.circle(c[0], c[1], r), S.tube(c, ctl, tip, t => rt + (r - rt) * Math.pow(1 - t, 1.3), n || 28)], 0);
  const logo = tear0([LC[0] - .2, LC[1] + 3], 3.5, [LC[0] - 2.2, LC[1] - 2.9], [LC[0] + .8, LC[1] - 6.7], .45);
  const logoCore = tear0([LC[0] - .1, LC[1] + 3.8], 1.7, [LC[0] - 1.1, LC[1] + .6], [LC[0] - .2, LC[1] - 2], .35, 16);
  CHAPTER_OBJ["Chapter 59: Flammable Solids"] = {
    d: S.shape(all, BB),
    col: "#2E6FB8", base: "field",
    plates: [
      ["cardboard", quad(P(DL, 0), P(SL, 0), P(SL, 1), P(DL, 1), .8), { col: "#D8B98C" }],                                   /* the drawer's rim */
      ["wood", quad(P(DL + 1.6, .07), P(SL, .07), P(SL, .94), P(DL + 1.6, .94), .6), { z: -1.2, bev: .6, col: "#6E4B2A" }],   /* inside it */
      ["wood", sticks, { z: -.6, bev: .4, col: "#E2C38F" }],                                                                  /* the matches lying in it */
      ["red", heads, { z: -.2, bev: .5, dome: .9, col: "#D8352C" }],                                                          /* their heads */
      ["cardboard", quad(P(DL, 0), P(SL, 0), dn(P(SL, 0)), dn(P(DL, 0)), [.8, 0, 0, .8]), { z: .2, bev: .5, col: "#D8B98C" }], /* the drawer's front */
      ["field", quad(P(SL, 0), P(SR, 0), P(SR, 1), P(SL, 1), .8), { dome: .8 }],                                              /* the sleeve's top */
      ["cream", quad(P(SL + 5, .17), P(SR - 5, .17), P(SR - 5, .83), P(SL + 5, .83), 1.6), { z: .5, bev: .6, col: "#F4EEDC" }],   /* its label */
      ["red", S.shape(logo, BB), { z: .4, bev: .45, dome: .55, col: "#E2412F" }],
      ["hot", S.shape(logoCore, BB), { z: .15, bev: .35, dome: .3, col: "#F7A234" }],         /* its hot heart */   /* the flame printed on it (art10: a clean teardrop, its tip flickering over, centred on the label and lying in its plane) */
      ["leather", quad(P(SL, 0), P(SR, 0), dn(P(SR, 0)), dn(P(SL, 0)), [0, 0, .8, 0]), { z: .2, bev: .5, col: "#6B3F22" }],     /* the striking strip down its side */
      ["leather", "M" + f([SL + 3, 76.5]) + "H" + (SR - 3) + "M" + f([SL + 3, 80]) + "H" + (SR - 3), { ln: 1, cut: .4, paint: 0 }],
      ["shade", quad(P(SR, 0), P(SR, 1), dn(P(SR, 1)), dn(P(SR, 0)), [0, .8, .8, .8]), { z: .1, bev: .5 }],                     /* the sleeve's end */
      ["hot", S.shape(S.inter(all, S.grow(flame, 3)), BB), { col: "#FF8A2A" }],                                                 /* the flame's colour, under the match (so no base shows where they meet) */
      ["wood", S.shape(match, BB), { z: 1, bev: .7, dome: .5, col: "#E2C38F", lvl: "struck" }],                                /* the struck match, one straight stick swelling into its head (lvl: not stepping down over the drawer's rim) */
      ["red", S.shape(S.inter(match, (x, y) => -(hp(x, y) + 4.2 - .1 * hq(x, y) ** 2)), BB), { col: "#C9302A" }],   /* its red coating, from where the head swells */
      ["rubber", S.shape(S.inter(head, (x, y) => -(hp(x, y) - .6 - .07 * hq(x, y) ** 2)), BB), { col: "#3B2620" }],   /* charred where it burns */
      ["hot", S.shape(S.minus(S.inter(all, S.grow(flame, 3)), match), BB), { z: .6, dome: 1.3, col: "#FF8A2A" }],                                            /* its flame, rising off the head */
      ["glow", S.shape(S.minus(flameMid, head), BB), { z: .2, bev: .6, dome: .6, col: "#FFC53D" }],                               /* the yellow inside it */
      ["glow", S.shape(S.minus(core, head), BB), { z: .15, bev: .5, dome: .5, col: "#FFF5D6" }],                                  /* the white-hot core at the head */
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
      ["field", OBJ_rrect(43, 19, 14, 8, 0), { z: .2 }],                                              /* the neck, from the lip to the shoulder (art9: run on under both, their edges showed through it) */
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
/* (art10) Madison circled the collar again (two pictures): its foot was a wide grey skirt flaring over the dome, joined to it in a
   stepped, ragged line. A propane cylinder's collar is a steel CYLINDER standing on the dome, so it is drawn as one now: seen a
   little from above, its rolled top rim is an ellipse (the inside of the collar and the valve's handwheel showing in it), its front
   is a straight band between two parallel elliptic arcs, the curved hand-hold opening is cut through that front (the brass valve body
   and its outlet seen through it), and its foot is the same ellipse laid on the dome - the line where it is welded on, the dome in its
   shadow just under it (a raised steel bead there glinted in broken dashes: it read as ragged again). No skirt: the collar's sides come straight down to the dome and the outline takes them in with a small fillet.
   Every part stops where the part in front of it starts (the dome stops at the weld, the front at the rim). ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const DC = [50, 52], DR = [40, 30];
  const domeY = x => DC[1] - DR[1] * Math.sqrt(Math.max(0, 1 - ((x - DC[0]) / DR[0]) ** 2));
  const topDome = S.inter(S.ellipse(DC[0], DC[1], DR[0], DR[1]), S.box(0, 0, 100, 52.5, 0));
  const tank = S.union([topDome, S.box(10, 52, 80, 18, 0), S.inter(S.ellipse(50, 70, 40, 16), S.box(0, 69.5, 100, 31, 0))], 0);
  /* (art11) the foot ring: Madison, of art10's, "the bottom of the barrel thing looks like a USB" - a dark box with two oval slots. It
     is a short steel cylinder now, seen a little from above like the collar: flared a little toward the ground, its bottom edge the front
     arc of an ellipse (a curve, not a box), the tank's bottom dome sitting down into it (the tank is drawn over its top), a rolled lip
     round its foot, and the tank's shadow on it under the dome. No slots. */
  const FY0 = 80, FY1 = 92.6, FR0 = 20.5, FR1 = 24, FE = 4.2;                 /* its top (inside the tank) and its foot: half-widths and the ellipses' depth */
  const front = (y0, r) => (x, y) => y - (y0 + FE * Math.sqrt(Math.max(0, 1 - ((x - 50) / r) ** 2)));   /* <0 above the front arc of the ellipse at y0 */
  const foot = S.union([S.poly([[50 - FR0, FY0], [50 + FR0, FY0], [50 + FR1, FY1], [50 - FR1, FY1]]), S.ellipse(50, FY1, FR1, FE)], 0);
  const lip = S.inter(foot, (x, y) => -front(FY1 - 2.8, FR1)(x, y));             /* the rolled lip: the foot below the arc 2.8 above its edge */
  const vents = [-11, 0, 11].map(dx => OBJ_circle(50 + dx, FY1 - 4.6 + FE * Math.sqrt(1 - (dx / FR1) ** 2) - 1.2, 1.25)).join("");   /* three small round vents, on the band's curve */
  const CW = 16.5, ER = 3.6, TY = 9.8, Y0 = domeY(50 - CW);                  /* the collar's half-width, its ellipses' depth, the rim's middle, where its sides meet the dome */
  const ell = (cy, k) => (x, y) => { const dx = (x - 50) / CW; return y - (cy + k * ER * Math.sqrt(Math.max(0, 1 - dx * dx))); };   /* <0 above the arc (front k = 1, back k = -1) */
  const within = (x, y) => Math.abs(x - 50) - CW;
  const rimOut = S.ellipse(50, TY, CW, ER), rimIn = S.ellipse(50, TY + .25, CW - 1.9, ER - 1.25);
  const collar = S.union([rimOut, (x, y) => Math.max(within(x, y), TY - y, ell(Y0, 1)(x, y) - 6)], 0);   /* rim and body, run on into the dome */
  const all = S.union([tank, foot, collar], 1.6);
  /* the hand-hold opening: a slot cut through the front, curved as the front is */
  const HW = 11, slot = S.grow(S.grow((x, y) => Math.max(Math.abs(x - 50) - HW + 2.4, -ell(TY + 4.3, 1)(x, y), ell(TY + 12.7, 1)(x, y)), -2.4), 2.4);
  const inSlot = f => S.shape(S.inter(f, S.grow(slot, -.55)), BB);
  CHAPTER_OBJ["Chapter 61: Liquefied Petroleum Gases"] = {
    base: "water",
    d: S.shape(all, BB),
    plates: [
      ["steel", S.shape(S.minus(S.inter(all, S.grow(foot, 1.2)), S.grow(tank, -.5)), BB), { z: .35, bev: .6 }],      /* the foot ring, its band (under the tank's edge and its fillets) */
      ["steel", S.shape(S.inter(all, lip), BB), { z: .6, bev: 1, dome: .3 }],                                /* its rolled lip */
      ["rubber", vents, { z: -.7, bev: .45, col: "#2A2E34" }],                                             /* its vents */
      ["ink", S.loops(S.inter(S.inter(S.minus(S.grow(tank, 2), tank), foot), (x, y) => y - 78), BB).map(S.pathOf).join(""), { z: .2, bev: .6, col: "#5A6068" }],   /* the tank's shadow on it */
      ["water", S.shape(S.minus(S.union([tank, S.inter(S.inter(all, S.grow(tank, 1.5)), (x, y) => y - 30)], 0), (x, y) => Math.max(within(x, y), ell(Y0, 1)(x, y))), BB), { dome: 2 }],   /* the tank, from the collar's weld down (over the foot ring's top, as before) */
      ["water", OBJ_rrect(10, 54, 80, 6, 0), { z: .7, bev: .7 }],                                      /* its welded seam */
      ["steel", S.shape(S.inter(all, (x, y) => Math.max(within(x, y) - 1.4, ell(Y0, 1)(x, y))), BB)],                             /* (the collar's steel, under its parts to the outline's last corner) */
      ["steel", S.shape(S.minus(S.inter(all, (x, y) => Math.max(within(x, y) - 1.4, TY - 1.5 - y, ell(Y0, 1)(x, y))), rimOut), BB), { z: .55, bev: .9 }],   /* the collar's front, a band round a cylinder (its fillets into the dome with it) */
      ["rubber", S.shape(slot, BB), { z: -1.5, bev: .6 }],                                                 /* the hand-hold opening */
      ["brass", inSlot(S.box(42.5, TY + 8.6, 15, 12, 2)), { z: .2, gem: .9, gw: 2.2 }],                    /* through it: the brass valve body */
      ["brass", inSlot(S.box(56.4, TY + 11.6, 6, 4.2, 1.6)), { z: .15, dome: .7 }],                        /* and its outlet */
      ["water", S.shape(S.inter(S.minus((x, y) => Math.max(within(x, y) - 2, ell(Y0 + 1.5, 1)(x, y)), (x, y) => Math.max(within(x, y), ell(Y0, 1)(x, y))), all), BB), { col: "#225C9A" }],   /* the dome in the collar's shadow, along the weld */
      ["steel", S.shape(S.minus(rimOut, rimIn), BB), { z: .9, bev: .6, dome: .5 }],                       /* the rolled rim */
      ["rubber", S.shape(rimIn, BB), { z: -1.3, bev: .5, col: "#2C3036" }],                                /* the inside of the collar */
      ["rubber", OBJ_ellipse(50, TY + .5, 8.6, 1.75), { ln: 1.3, z: .45, bev: .4, col: "#4A5059" }],        /* the valve's handwheel in it: its rim, */
      ["rubber", "M42.4 " + (TY + .5) + "H57.6M50 " + (TY - .9) + "V" + (TY + 1.9), { ln: 1, z: .3, bev: .3, col: "#4A5059" }],   /* its spokes */
      ["rubber", OBJ_ellipse(50, TY + .5, 2.2, .9), { z: .5, bev: .3, dome: .3, col: "#5A616B" }],           /* and its hub */
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
      /* (art9) Madison: "There's a lot of spots all over that just don't look right." The handle ran 2 on under the lid, and the grips
         and the latch lay over the body's and the lid's edges, and a part's relief is added to what is under it: each showed the edge
         under it as a step. The handle now stands on the lid; the grips and the latch lie flat over what they cross (lvl). */
      ["shade", OBJ_rrect(28, 8, 44, 18, [7, 7, 0, 0]), { dome: .9 }],                                /* the carry handle */
      ["cream", OBJ_rrect(5, 26, 90, 16, [6, 6, 1, 1]), { dome: 1, col: "#F4F2EC" }],                   /* the lid */
      ["cream", OBJ_rrect(14, 29.5, 72, 7.5, 3), { z: .5, bev: .7, col: "#F4F2EC" }],                    /* its top */
      ["field", "M6 42.5H94", { ln: 1.6, cut: .8, paint: 0 }],                                         /* the seal line */
      ["shade", OBJ_rrect(2, 54, 9, 16, 3), { dome: .9, lvl: "grip" }],                                /* the end grips */
      ["shade", OBJ_rrect(89, 54, 9, 16, 3), { dome: .9, lvl: "grip" }],
      ["steel", OBJ_rrect(43, 37, 14, 13, 2.5), { dome: 1, lvl: "latch" }],                            /* the latch */
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
  const neck = S.box(36.5, 18, 9, 8, 1);
  const cyl = S.union([body, dome, neck], 5);                                   /* the shoulder rises into the neck in one curve */
  /* (384.136 art4, Madison: the connection "looks better but it's not perfect", circling the ring where it meets the neck and the valve.)
     The ring is seated: a hair wider than the neck (a 1-unit lip each side, not 2), the neck's white running up into it with the
     cylinder's own fillet; the regulator's nut comes down onto the ring's top (no notch between them) and the arm joins the outline with a small fillet, so no brass
     drops down beside the ring and no shadowed wedge runs down the neck's right side. */
  /* (art6 round 4) Madison: "the silver part, it doesn't wrap around, not sure why the sides are white". The white beside the ring was
     the neck's paint, standing up beside and under a ring that only matched it. The collar now sits straight on the shoulder (no neck
     shows): a steel collar wider than the valve, its threads curved as a band round a cylinder seen from a little above, its ends
     faceted as they turn away. */
  const ring = S.box(33.5, 12.5, 15, 9.2, 1.6);                                     /* the neck ring */
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
      ["cream", S.shape(S.minus(S.inter(cyl, S.box(0, 24.4, 100, 17.6, 0)), ring), BB), { z: .2, bev: .5, dome: 1.6, col: "#F2F0EA" }],   /* its white shoulder, under the collar's foot */
      ["field", "M17 42H65", { ln: 1.4, cut: .6, paint: 0 }],                                           /* where the paint changes */
      ["field", "M17 88.5H65", { ln: 1.6, cut: .8, paint: 0 }],                                         /* the foot ring */
      ["brass", S.shape(S.minus(S.inter(all, S.box(0, 0, 61, 12.6, 0)), cyl), BB), { z: .2, bev: .5 }],     /* the valve gear, every fillet in it brass (above the ring only) */
      ["brass", S.shape(S.union([valve, stem], .8), BB), { z: .3, bev: .6, gem: .8, gw: 2.2 }],           /* the valve body and its stem */
      /* (art7) Madison: "the edges aren't silver it's like looking at a soda with a screw top, and the screw top doesn't exist on the sides".
         The collar's foot flares out over the shoulder's top to the outline on both sides (a steel shoulder ring the collar stands in), so
         there is no white beside it, and the outline's silhouette there is steel - its side, turned, is silver */
      ["steel", S.shape(S.inter(all, S.union([S.box(32, 12.4, 18, 10.4, 0), S.inter(S.box(0, 19, 100, 5.6, 0), S.grow(cyl, 1))], 2.4)), BB), { z: .6, bev: .55, gem: .7, gw: 2.4 }],   /* the collar and its foot, a steel band across the shoulder's top from outline to outline */
      ["steel", "M34.6 15.4Q41 17.2 47.4 15.4M34.6 18.2Q41 20 47.4 18.2", { ln: .7, cut: .4, paint: 0 }],                 /* its threads, curved round it */
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
