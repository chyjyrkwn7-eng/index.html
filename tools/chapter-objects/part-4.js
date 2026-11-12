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
   through it, the ribbed body with its panel pressed in, and the acid running down from the cap. ---- */
{
  CHAPTER_OBJ["Chapter 54: Corrosive Materials"] = {
    base: "cream",
    d: OBJ_poly([[20, 96], [20, 36], [26, 26], [33, 22], [33, 13], [31, 13], [31, 4], [51, 4], [51, 13], [49, 13], [49, 20], [55, 14], [73, 13], [80, 20], [80, 96]],
      [8, 10, 6, 2, 1, 1, 2.5, 2.5, 1, 1, 2, 3, 6, 4, 8]),
    holes: [OBJ_rrect(57, 21, 14, 17, 5)],
    plates: [
      ["cream", OBJ_rrect(52, 12, 28, 30, [7, 6, 2, 2]), { dome: .9 }],                            /* the handle */
      ["glow", OBJ_rrect(26, 47, 48, 40, 5), { z: -.8, bev: .9 }],                               /* the panel pressed in */
      ["field", "M21 43H79M21 91H79", { ln: 1.6, cut: .8, paint: 0 }],                            /* the moulded ribs */
      ["cream", OBJ_rrect(33, 12, 16, 12, 1), { z: .3 }],                                         /* the neck */
      ["red", OBJ_rrect(31, 4, 20, 9.5, 2.5), { z: .6, bev: .6 }],                               /* the cap */
      ["deep", "M35 6.5V11M39 6.5V11M43 6.5V11M47 6.5V11", { ln: 1.3, cut: .6, paint: 0 }],       /* its knurling */
      ["water", "M36.5 14V27", { ln: 3.6, z: .6, bev: .9 }],                                      /* the acid running down */
      ["water", OBJ_circle(36.5, 30, 3.4), { dome: 1.4 }],                                        /* its drop */
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
  const half = [[50, 2], [54.5, 6.5], [58.5, 11.5], [61.5, 17], [63.3, 22], [64, 26], [64, 47], [78, 67], [78, 80], [64, 73], [64, 77], [53, 77], [53, 97]];
  const hr = [2, 0, 0, 0, 0, 1, 1, 3, 3.5, 1, 2, 1, 2.5];
  const left = half.slice(1).reverse().map(p => [100 - p[0], p[1]]), lr = hr.slice(1).reverse();
  const cone = OBJ_poly([[50, 2], [54.5, 6.5], [58.5, 11.5], [61.5, 17], [63.3, 22], [64, 26.5], [36, 26.5], [36.7, 22], [38.5, 17], [41.5, 11.5], [45.5, 6.5]], [2, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]);
  const wrap = k => OBJ_poly([[36, 34 + k], [64, 42 + k], [64, 48 + k], [36, 40 + k]], .8);
  CHAPTER_OBJ["Chapter 56: Explosives and Fireworks"] = {
    base: "red",
    d: OBJ_poly(half.concat(left), hr.concat(lr)),
    plates: [
      ["red", OBJ_rrect(36, 26, 28, 51, [0, 0, 2, 2]), { dome: 1.6 }],                          /* the body */
      ["cream", wrap(0), { z: .5, bev: .6 }],                                                       /* its spiral wraps */
      ["cream", wrap(14), { z: .5, bev: .6 }],
      ["cream", wrap(28), { z: .5, bev: .6 }],
      ["brass", cone, { gem: 1.6, gw: 6 }],                                                          /* the nose cone, faceted */
      ["brass", OBJ_rrect(35, 24.5, 30, 4, 1.5), { z: .5, bev: .5 }],                               /* its rim */
      ["brass", OBJ_poly([[64, 47], [78, 67], [78, 80], [64, 73]], [0, 3, 3.5, 0]), { z: .3, bev: .8 }],   /* the fins */
      ["brass", OBJ_poly([[36, 47], [22, 67], [22, 80], [36, 73]], [0, 3, 3.5, 0]), { z: .3, bev: .8 }],
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

/* ---- Chapter 59: Flammable Solids - a matchbox, its drawer pulled out with the match heads in a row, the striker along its side, and one
   match laid across it with its head up. ---- */
{
  const A = [28, 62], B = [62, 16], ux = (B[0] - A[0]), uy = (B[1] - A[1]), L = Math.hypot(ux, uy), dx = ux / L, dy = uy / L, nx = -dy, ny = dx;
  const at = (t, w) => [A[0] + dx * t + nx * w, A[1] + dy * t + ny * w];
  /* where the stick's two sides cross the box's top edge (y 54); the side at w -3 is the left one */
  const cross = w => at((54 - A[1] - ny * w) / dy, w);
  /* the head: an ellipse round t = L + 1.5, 7 along and 5.6 across; it meets the stick's sides at phi = +-147.6 degrees */
  const HC = L + 1.5, ha = 7, hb = 5.6, ph = Math.acos(-Math.sqrt(1 - (3 / hb) * (3 / hb))) * 180 / Math.PI;
  const head = []; for(let k = 0; k <= 16; k++){ const p = (-ph + 2 * ph * k / 16) * Math.PI / 180; head.push(at(HC + ha * Math.cos(p), hb * Math.sin(p))); }
  const pts = [[4, 92], [4, 54], cross(-3)].concat(head).concat([cross(3), [72, 54], [72, 57], [96, 57], [96, 89], [72, 89], [72, 92]]);
  const rs = [3, 3, 1].concat(head.map((p, i) => (i === 0 || i === head.length - 1) ? 1 : 0)).concat([1, 1, 1, 2, 2, 1, 1]);
  const stick = OBJ_poly([at(0, 3), at(L - 3, 3), at(L - 3, -3), at(0, -3)], [3, 0, 0, 3]);
  const headD = OBJ_poly(P4_arc(0, 0, 1, 1, 0, 345, 23).map(q => at(HC + ha * q[0], hb * q[1])), 0);
  let hatch = ""; for(let x = 9; x <= 69; x += 5) hatch += "M" + x + " 84L" + (x - 4) + " 90.5";
  const inMatches = [61.5, 67.5, 73.5, 79.5, 85.5];
  CHAPTER_OBJ["Chapter 59: Flammable Solids"] = {
    base: "water",
    d: OBJ_poly(pts, rs),
    plates: [
      ["water", OBJ_rrect(4, 54, 68, 38, 3), { dome: .8 }],                                         /* the box */
      ["cream", OBJ_rrect(10, 59, 56, 19, 3), { z: .6, bev: .8 }],                                    /* its label, raised */
      ["wood", OBJ_rrect(4, 82, 68, 10, [0, 0, 3, 3]), { z: -.3, bev: .5 }],                         /* the striker */
      ["wood", hatch, { ln: 1.3, cut: .6, paint: 0 }],
      ["cream", OBJ_rrect(72, 57, 24, 32, [0, 2, 2, 0]), { z: .2 }],                                  /* the drawer */
      ["rubber", OBJ_rrect(74.5, 59.5, 19, 27, 1.5), { z: -1.2, bev: .7 }],                            /* its inside */
      ["wood", inMatches.map(y => "M76 " + y + "H86").join(""), { ln: 3, z: .5, bev: .6 }],           /* the matches in it */
      ["red", OBJ_circle(88.5, 61.5, 2.7), { dome: 1.2 }],
      ["red", OBJ_circle(88.5, 67.5, 2.7), { dome: 1.2 }],
      ["red", OBJ_circle(88.5, 73.5, 2.7), { dome: 1.2 }],
      ["red", OBJ_circle(88.5, 79.5, 2.7), { dome: 1.2 }],
      ["red", OBJ_circle(88.5, 85.5, 2.7), { dome: 1.2 }],
      ["wood", stick, { z: 1, bev: .9, dome: .5 }],                                                   /* the match */
      ["red", headD, { z: 1, dome: 1.6 }],                                                            /* its head */
    ],
  };
}

/* ---- Chapter 60: Highly Toxic and Toxic Materials - a coffin-shaped poison bottle: the cork, the lip, the faceted body widest at the
   shoulder, and its raised front panel quilted with grooves (poison was moulded to be known by touch in the dark). ---- */
{
  const body = [[57, 27], [76, 42], [67, 97], [33, 97], [24, 42], [43, 27]];
  const panel = [[50, 36], [64, 45], [58.5, 88], [41.5, 88], [36, 45]];
  const segs = [];
  for(let k = -60; k <= 60; k += 8.5){ segs.push(P4_clip([20 + k, 30], [80 + k, 100], panel)); segs.push(P4_clip([80 - k, 30], [20 - k, 100], panel)); }
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

/* ---- Chapter 61: Liquefied Petroleum Gases - a squat propane (barbecue) tank: the collar on top with the valve in its window, the
   domed tank with its welded seam, and the foot ring with its slots. ---- */
{
  /* the tank's outline: its lower dome (127 -> 180 degrees, from the foot ring up to the side), the upper dome to the collar (180 -> 240),
     over the collar, the upper dome down (300 -> 360), the lower dome back to the foot ring (0 -> 53) */
  const botL = P4_arc(50, 70, 40, 16, 127, 180, 6), top = P4_arc(50, 52, 40, 30, 180, 240, 8);
  const topR = P4_arc(50, 52, 40, 30, 300, 360, 8), bot = P4_arc(50, 70, 40, 16, 0, 53, 6);
  const pts = [[26, 97]].concat(botL).concat(top).concat([[30, 3], [70, 3]]).concat(topR).concat(bot).concat([[74, 97]]);
  const rs = pts.map(() => 0), at = p => pts.indexOf(p);
  [[pts[0], 2.5], [botL[0], 1], [top[top.length - 1], 1], [pts[at(top[top.length - 1]) + 1], 4], [pts[at(top[top.length - 1]) + 2], 4], [topR[0], 1],
   [bot[bot.length - 1], 1], [pts[pts.length - 1], 2.5]].forEach(q => { rs[at(q[0])] = q[1]; });
  const tank = OBJ_poly(top.concat(P4_arc(50, 52, 40, 30, 240, 300, 4).slice(1, -1)).concat(topR).concat(bot).concat(P4_arc(50, 70, 40, 16, 53, 127, 6).slice(1, -1)).concat(botL), 0);
  CHAPTER_OBJ["Chapter 61: Liquefied Petroleum Gases"] = {
    base: "water",
    d: OBJ_poly(pts, rs),
    plates: [
      ["water", tank, { dome: 2 }],                                                                    /* the tank */
      ["water", OBJ_rrect(10, 54, 80, 6, 0), { z: .7, bev: .7 }],                                      /* its welded seam */
      ["steel", OBJ_rrect(26, 84, 48, 13, [0, 0, 2.5, 2.5]), { z: .3 }],                                /* the foot ring */
      ["rubber", OBJ_rrect(33, 88, 10, 5, 2), { z: -1, bev: .5 }],                                        /* its slots */
      ["rubber", OBJ_rrect(57, 88, 10, 5, 2), { z: -1, bev: .5 }],
      ["steel", OBJ_rrect(30, 3, 40, 26, [4, 4, 0, 0]), { z: .5, bev: .8 }],                          /* the collar */
      ["rubber", OBJ_rrect(37, 8.5, 26, 14, 4), { z: -1.7, bev: .7 }],                                   /* its window */
      ["steel", OBJ_rrect(41, 9.5, 18, 5.5, 2.5), { dome: 1 }],                                       /* the valve's handwheel */
      ["brass", OBJ_rrect(45.5, 14.5, 9, 9, 1.5), { gem: 1, gw: 2.2 }],                               /* the valve */
    ],
  };
}

/* ---- Chapter 62: Organic Peroxides - an insulated cooler (peroxides are kept cold): the carry handle standing up with a real hole under
   it, the thick pale lid, the tapered body with its raised panel, the latch, and the grips at each end. ---- */
{
  CHAPTER_OBJ["Chapter 62: Organic Peroxides"] = {
    d: OBJ_poly([[5, 42], [5, 26], [28, 26], [28, 8], [72, 8], [72, 26], [95, 26], [95, 42], [92, 42], [92, 54], [98, 54], [98, 70], [90.4, 70], [89, 94], [11, 94], [9.6, 70], [2, 70], [2, 54], [8, 54], [8, 42]],
      [1, 6, 1, 7, 7, 1, 6, 1, 1, 1, 3, 3, 1, 8, 8, 1, 3, 3, 1, 1]),
    holes: [OBJ_rrect(35, 14.5, 30, 10.5, 4.5)],
    plates: [
      ["field", OBJ_poly([[8, 42], [92, 42], [89, 94], [11, 94]], [0, 0, 8, 8]), { dome: 1 }],        /* the body */
      ["body", OBJ_poly([[16, 50], [84, 50], [82, 86], [18, 86]], 4), { z: .7, bev: .9 }],            /* its raised panel */
      ["shade", OBJ_rrect(28, 8, 44, 20, [7, 7, 0, 0]), { dome: .9 }],                                /* the carry handle */
      ["cream", OBJ_rrect(5, 26, 90, 16, [6, 6, 1, 1]), { dome: 1 }],                                  /* the lid */
      ["cream", OBJ_rrect(14, 29.5, 72, 7.5, 3), { z: .5, bev: .7 }],                                   /* its top */
      ["field", "M6 42.5H94", { ln: 1.6, cut: .8, paint: 0 }],                                         /* the seal line */
      ["shade", OBJ_rrect(2, 54, 9, 16, 3), { dome: .9 }],                                             /* the end grips */
      ["shade", OBJ_rrect(89, 54, 9, 16, 3), { dome: .9 }],
      ["steel", OBJ_rrect(43, 37, 14, 13, 2.5), { dome: 1 }],                                          /* the latch */
    ],
  };
}

/* ---- Chapter 63: Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids - an oxygen mask: the domed cup with its soft rim, its nose clip,
   valve and ports, and the corrugated hose curling away from it to its connector. ---- */
{
  const hose = P4_resample([[50, 62], [50, 68], [51.5, 74], [55.5, 80], [61.5, 85], [69, 88], [77, 89.5], [92, 89.5]], 4.2);
  const hw = hose.map((p, i) => i >= hose.length - 3 ? 13 : 11);
  const tube = P4_ribbon(hose, hw);
  const cup = [[42, 4], [58, 4], [80, 42], [71, 62], [29, 62], [20, 42]], cr = [6, 6, 14, 9, 9, 14];
  const pts = cup.slice(0, 4).concat(tube).concat(cup.slice(4)), rs = cr.slice(0, 4).concat(tube.map((p, i) => (i === 0 || i === tube.length - 1) ? 1 : 0)).concat(cr.slice(4));
  rs[3] = 9;
  let ribs = ""; for(let i = 2; i < hose.length - 3; i++){ const a = hose[i - 1], b = hose[i + 1], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy), nx = dy / l, ny = -dx / l, h = hw[i] / 2 - 1.6;
    ribs += "M" + P4_f([hose[i][0] + nx * h, hose[i][1] + ny * h]) + "L" + P4_f([hose[i][0] - nx * h, hose[i][1] - ny * h]); }
  const end = P4_ribbon(hose.slice(-3), [13, 13, 13]);
  CHAPTER_OBJ["Chapter 63: Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids"] = {
    d: OBJ_poly(pts, rs),
    plates: [
      ["glass", OBJ_poly(P4_ribbon([[50, 55]].concat(hose), [11].concat(hw)), 1), { dome: 1 }],         /* the hose */
      ["glass", ribs, { ln: 1.6, cut: .8, paint: 0 }],                                                   /* its corrugations */
      ["steel", OBJ_poly(end, 1), { z: .5, bev: .6 }],                                                  /* its connector */
      ["shade", OBJ_poly(cup, cr), { z: .5, bev: .8 }],                                                 /* the cup's soft rim */
      ["field", OBJ_poly([[43.5, 8.5], [56.5, 8.5], [75.5, 42], [68, 58], [32, 58], [24.5, 42]], [4, 4, 11, 7, 7, 11]), { dome: 2.4 }],   /* the cup */
      ["steel", OBJ_rrect(43, 11, 14, 4.5, 2.2), { z: .5, bev: .6 }],                                   /* the nose clip */
      ["lite", OBJ_circle(50, 39, 6.2), { z: .6, bev: .7, dome: .9 }],                                  /* the valve */
      ["lite", OBJ_circle(35, 41, 3.2), { dome: 1.1 }],                                                 /* the ports */
      ["lite", OBJ_circle(65, 41, 3.2), { dome: 1.1 }],
    ],
  };
}
