/* Police academy unit badges as RAISED PINS, round 2 (build 384.136). Madison asked for the academy's 24 unit badges to get the same
   upgraded look as the Fire Code chapter pins, "just as great". The first set (384.121: kettlebell, scales, patrol cap ...) was taken back
   out ("I'm not a fan of these new ones"); it is kept in retired/academy-pins/. This set is drawn again from nothing, to the Fire Code
   pins' current standard (tools/chapter-objects/README.md): the silhouette is the object, every part sculpted (raised, domed, faceted,
   grooved), natural colours, objects in 3/4 show every side they turn to us, loose things lie ON what is under them, every piece joins.
   The unit's badge id (its title) and its unlock rule are untouched; only the art. Local helpers live in this one block. */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100], D = Math.PI / 180;
  const sh = f => S.shape(f, BB);                                  /* one loop: the largest */
  const all = f => S.loops(f, BB).map(S.pathOf).join("");          /* every loop (README rule 8d) */
  const g = (f, r) => S.grow(f, r == null ? .3 : r);
  const F = v => String(Math.round(v * 100) / 100), pt = p => F(p[0]) + " " + F(p[1]);
  const lineP = pts => "M" + pts.map(pt).join("L");
  const rotP = (pts, a, cx, cy) => { const c = Math.cos(a * D), s = Math.sin(a * D);
    return pts.map(([x, y]) => [cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c]); };
  /* an ellipse turned by a degrees (rx along that direction) */
  const rell = (cx, cy, rx, ry, a) => { const c = Math.cos(a * D), s = Math.sin(a * D), E = S.ellipse(0, 0, rx, ry);
    return (x, y) => { const dx = x - cx, dy = y - cy; return E(dx * c + dy * s, -dx * s + dy * c); }; };
  const rbox = (cx, cy, w, h, a, r) => S.grow(S.poly(rotP([[cx - w / 2 + r, cy - h / 2 + r], [cx + w / 2 - r, cy - h / 2 + r], [cx + w / 2 - r, cy + h / 2 - r], [cx - w / 2 + r, cy + h / 2 - r]], a, cx, cy)), r);
  /* a frame: o + a*u + b*v */
  const frame = (o, u, v) => (a, b) => [o[0] + u[0] * a + v[0] * b, o[1] + u[1] * a + v[1] * b];
  /* points round an ellipse in a frame Q: Q(ca + ra cos t, cb + rb sin t), t in degrees */
  const ellP = (Q, ca, cb, ra, rb, t0, t1, n) => { const o = []; for(let i = 0; i <= n; i++){ const t = (t0 + (t1 - t0) * i / n) * D; o.push(Q(ca + ra * Math.cos(t), cb + rb * Math.sin(t))); } return o; };
  const ax = frame([0, 0], [1, 0], [0, 1]);
  /* a line kept only where ok(point): a groove stays on the part it is cut into (check-b384-badgeart (1)) */
  const dense = (pts, st) => { const o = [pts[0]]; for(let i = 1; i < pts.length; i++){ const a = pts[i - 1], b = pts[i], n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / (st || .4)));
    for(let k = 1; k <= n; k++) o.push([a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n]); } return o; };
  const keep = (pts, ok) => { let d = "", run = []; dense(pts).forEach(p => { if(ok(p)) run.push(p); else { if(run.length > 1) d += lineP(S.simp(run, .03)); run = []; } }); if(run.length > 1) d += lineP(S.simp(run, .03)); return d; };
  const polar = (C, r, a) => [C[0] + r * Math.cos(a * D), C[1] + r * Math.sin(a * D)];
  const ring = (cx, cy, ro, ri) => S.minus(S.circle(cx, cy, ro), S.circle(cx, cy, ri));
  const wedge = (C, a0, a1, R) => { const p = [C]; for(let i = 0; i <= 12; i++) p.push(polar(C, R, a0 + (a1 - a0) * i / 12)); return S.poly(p); };

  /* ---- Penal Code - the judge's gavel striking its sound block. The block is a round wooden block seen from a little above: its top
     face (a groove turned round it) and its side band (two turned rings). The gavel's head is a turned cylinder whose upper end shows
     its face; its lower end stands ON the block's top and throws its shadow there; a brass band where each striking cap meets the
     barrel; the handle runs out of the head's middle and ends in a turned knob. ---- */
  {
    const a = -33 * D, u = [Math.cos(a), Math.sin(a)], v = [-u[1], u[0]];
    const H = [29.4, 57], Q = frame(H, v, u), K = .37;          /* Q(along the head's axis, along the handle); K: an end face's depth */
    const HL = 20, HR = 10, CR = 8.8, CB = 13.2;                /* half length, barrel radius, cap radius, where the caps start */
    const cyl = (s0, s1, r) => S.union([S.poly([Q(s0, -r), Q(s1, -r), Q(s1, r), Q(s0, r)]), rell(...Q(s0, 0), r, r * K, -33), rell(...Q(s1, 0), r, r * K, -33)], 0);
    const barrel = cyl(-CB, CB, HR), caps = S.union([cyl(-HL, -CB + .5, CR), cyl(CB - .5, HL, CR)], 0), head = S.union([barrel, caps], 0);
    const handle = S.union([S.cone(...Q(0, HR - 1), ...Q(0, 55), 4, 3.3), S.circle(...Q(0, 58.5), 5), S.cone(...Q(0, 53.5), ...Q(0, 57), 3.3, 4.2)], .8);
    const C = [57, 77.5], RX = 38, RY = 9.8, SIDE = 9;
    const top = S.ellipse(C[0], C[1], RX, RY), side = S.union([S.box(C[0] - RX, C[1], 2 * RX, SIDE, 0), S.ellipse(C[0], C[1] + SIDE, RX, RY)], 0);
    const sil = S.union([head, handle, top, side], .8);
    const rim = (s, r) => lineP(ellP(Q, s, 0, r * K, r, -90, 90, 16));   /* the near half of a ring round the head at s */
    const lowArc = (dy) => lineP(ellP(ax, C[0], C[1] + dy, RX, RY, 8, 172, 24));
    CHAPTER_OBJ["Penal Code"] = {
      d: sh(sil), col: "#A96C38", base: "field",
      plates: [
        ["wood", sh(g(side)), { dome: .5, col: "#8A5430" }],                                                       /* the block's side */
        ["wood", lowArc(3) + lowArc(6.2), { ln: .9, cut: .45, paint: 0 }],                                          /* its turned rings */
        ["field", sh(g(top)), { z: .25, bev: .6, dome: .3 }],                                                       /* its top face */
        ["field", lineP(ellP(ax, C[0], C[1], RX - 6, RY - 1.6, 0, 360, 48)), { ln: 1.1, cut: .5, paint: 0 }],      /* the groove turned in it */
        ["wood", sh(g(handle)), { lvl: "gavel", z: .9, bev: .7, dome: 1.4, col: "#6B3C1F", sh: 1 }],                  /* the handle */
        ["wood", lineP([Q(-3.6, 53.5), Q(3.6, 53.5)]), { lvl: "gavel", ln: .8, cut: .45, paint: 0 }],                   /* the bead by the knob */
        ["wood", sh(g(head)), { lvl: "gavel", z: .9, bev: .8, dome: 2.4, col: "#6B3C1F", sh: 1 }],                       /* the head */
        ["wood", sh(rell(...Q(-HL, 0), CR - .2, (CR - .2) * K, -33)), { lvl: "gavel", z: 1.05, bev: .5, col: "#9A6236" }],   /* its upper end's face */
        ["wood", rim(-HL + 2.2, CR) + rim(HL - 2.2, CR), { lvl: "gavel", ln: .8, cut: .4, paint: 0 }],                      /* the caps' turned lines */
        ["brass", rim(-CB + 1.4, HR + .1) + rim(CB - 1.4, HR + .1), { lvl: "gavel", ln: 3, z: 1.2, bev: .5 }],               /* the brass bands */
      ],
    };
  }

  /* ---- Arrest, Search, and Seizure - a pair of chain handcuffs: two steel cuffs, each a ring with its lock housing (keyhole, two
     rivets) and the ratchet teeth of its swinging arm, the pivot rivet; swivels from the housings into a short chain (a link face on,
     one edge on, one face on). ---- */
  {
    const RO = 23.6, RI = 9.8, cuffs = [[24.4, 69, 1], [75.6, 69, -1]].map(([x, y, s]) => {
      const C = [x, y], ang = s > 0 ? -48 : -132, bc = polar(C, 17.6, ang), out = polar(C, 23.4, ang), eye = [50 - s * 6, 39.5];
      return { C, s, ang, bc, out, eye, box: rbox(bc[0], bc[1], 24, 13, ang + 90, 3.6), swivel: S.capsule(out[0], out[1], eye[0], eye[1], 3.4) }; });
    const rings = S.union(cuffs.map(c => ring(c.C[0], c.C[1], RO, RI)), 0);
    const boxes = S.union(cuffs.map(c => c.box), 0), swivels = S.union(cuffs.map(c => c.swivel), 0);
    const linkL = S.ellipse(44.2, 36.5, 6, 4.4), linkR = S.ellipse(55.8, 36.5, 6, 4.4), linkM = S.capsule(46.5, 36.5, 53.5, 36.5, 2.7);
    const chain = S.union([linkL, linkR, linkM], .6);
    /* (the cuffs' openings are pressed deep into the pin, not cut through it: a pin's back carries the unit's title, and two open
       rings left it no room for the title and the class line at 9.2px in the hand) */
    const t = S.trace(S.union([S.union(cuffs.map(c => S.circle(c.C[0], c.C[1], RO)), 0), boxes, swivels, chain], 1.2), BB);
    let teeth = "", pivots = [], rivets = [];
    cuffs.forEach(c => {
      for(let k = 0; k < 12; k++){ const a = c.ang + c.s * (46 + k * 6.5); teeth += lineP([polar(c.C, RO - 4.8, a), polar(c.C, RO + .5, a)]); }
      pivots.push(OBJ_circle(...polar(c.C, (RO + RI) / 2, c.ang - c.s * 64), 2.9));
      const tg = [Math.cos((c.ang + 90) * D), Math.sin((c.ang + 90) * D)];
      rivets.push(OBJ_circle(c.bc[0] + tg[0] * 8, c.bc[1] + tg[1] * 8, 2.5), OBJ_circle(c.bc[0] - tg[0] * 8, c.bc[1] - tg[1] * 8, 2.5));
    });
    const keyhole = S.union(cuffs.map(c => { const k = c.bc; return S.union([S.circle(k[0], k[1] - .7, 2.5), S.capsule(k[0], k[1] - .7, k[0], k[1] + 3.1, 1.3)], .5); }), 0);
    CHAPTER_OBJ["Arrest, Search, and Seizure"] = {
      d: t.d, holes: t.holes, col: "#B9C2CC", base: "steel",
      plates: [
        ["rubber", cuffs.map(c => OBJ_circle(c.C[0], c.C[1], RI + .4)).join(""), { z: -2.6, bev: 1.6, col: "#121418" }],           /* their openings */
        ["steel", all(g(rings)), { dome: 2 }],                                                                                /* the cuffs */
        ["steel", teeth, { ln: 1.1, cut: .55, paint: 0 }],                                                                     /* the ratchet teeth */
        ["steel", cuffs.map(c => lineP(ellP(ax, c.C[0], c.C[1], RO - 5.2, RO - 5.2, c.ang + c.s * 42, c.ang + c.s * 124, 16))).join(""), { ln: .9, cut: .5, paint: 0 }],   /* the swinging arm's edge */
        ["steel", pivots.join(""), { z: .5, bev: .5, dome: .9 }],                                                             /* the pivots */
        ["steel", all(g(chain)), { dome: 1.4 }],                                                                              /* the chain */
        ["rubber", all(S.union([S.ellipse(44.2, 36.5, 3.1, 1.5), S.ellipse(55.8, 36.5, 3.1, 1.5)], 0)), { z: -.8, bev: .5 }],   /* the links' eyes */
        ["steel", all(g(swivels)), { z: .4, bev: .6, dome: 1 }],                                                              /* the swivels */
        ["steel", all(g(boxes)), { z: 1, bev: .7, dome: .6, col: "#A3ADB8", sh: 1 }],                                         /* the lock housings */
        ["rubber", all(keyhole), { z: -.7, bev: .4 }],                                                                       /* the keyholes */
        ["steel", rivets.join(""), { z: 1.2, bev: .4, dome: .8 }],                                                           /* the rivets */
      ],
    };
  }

  /* ---- US and Texas Constitution and Rights - the parchment unrolled between its two rolls (their ends show the rolled sheet), the
     preamble's flourish of a heading and its lines in brown ink, the red wax seal on its ribbons; in front, a cut-glass inkwell with
     its brass collar and the white quill standing in it. ---- */
  {
    const RL = 9, RR = 67, sheet = S.box(12.5, 14, 51, 72, 0);
    const roll = y => S.union([S.box(RL, y - 7, RR - RL, 14, 0), S.ellipse(RL, y, 3.6, 7), S.ellipse(RR, y, 3.6, 7)], 0);
    const rolls = S.union([roll(14), roll(86)], 0);
    const bottle = S.union([S.poly([[66, 75], [70.5, 70.5], [91.5, 70.5], [96, 75], [96, 93], [92, 96.5], [70, 96.5], [66, 93]]), S.box(74.5, 65, 13, 7, 1.5)], 1), collar = S.box(73, 62.5, 16, 4.8, 1.8);
    const A = [80.5, 66], B = [95.5, 5], L = Math.hypot(B[0] - A[0], B[1] - A[1]), w = [(B[0] - A[0]) / L, (B[1] - A[1]) / L], n = [w[1], -w[0]];
    const Qq = frame(A, w, n);                                  /* Q(along the shaft, toward the scroll) */
    const t0 = .3, wl = t => { const s = (t - t0) / (1 - t0); return s <= 0 ? 0 : 9.5 * Math.pow(Math.sin(Math.PI * Math.min(1, s * .92 + .04)), .7); };
    const wr = t => wl(t) * .42, vpts = [];
    for(let i = 0; i <= 20; i++){ const t = t0 + (1 - t0) * i / 20; vpts.push(Qq(L * t, wl(t) + .01)); }
    for(let i = 20; i >= 0; i--){ const t = t0 + (1 - t0) * i / 20; vpts.push(Qq(L * t, -wr(t) - .01)); }
    const vane = S.grow(S.poly(vpts), .8), shaft = S.cone(...Qq(-2, 0), ...Qq(L * .99, 0), 1.9, .9);
    const quill = S.union([vane, S.cone(...Qq(-2, 0), ...Qq(L * t0 + 3, 0), 2.8, 2.4)], 1);
    const sealC = [24, 72];
    const tails = S.union([S.poly([[19.5, 73], [25, 75.5], [20.5, 95], [15.5, 92]]), S.poly([[23.5, 75.5], [29, 73], [33, 92], [28, 95]])], 0);
    const sil = S.union([sheet, rolls, bottle, collar, quill, tails], 1);
    let barbs = ""; for(let k = 0; k < 9; k++){ const t = t0 + .1 + k * .065; barbs += lineP([Qq(L * t, 2.4), Qq(L * (t + .05), wl(t + .05) * .8)]); }
    for(let k = 0; k < 5; k++){ const t = t0 + .14 + k * .11; if(wr(t + .05) > 3.6) barbs += lineP([Qq(L * t, -2.2), Qq(L * (t + .05), -wr(t + .05) * .8)]); }
    let lines = ""; for(let y = 38; y <= 70; y += 6.4) lines += "M19 " + F(y) + "H" + (y > 60 ? 50 : 58);
    const spiral = (cx, cy) => { const p = []; for(let i = 0; i <= 30; i++){ const t = i / 30 * 3.2 * Math.PI, r = .2 + .8 * i / 30; p.push([cx + 2.6 * r * Math.cos(t), cy + 5.6 * r * Math.sin(t)]); } return lineP(p); };
    CHAPTER_OBJ["US and Texas Constitution and Rights"] = {
      d: sh(sil), col: "#E9D5A6", base: "field",
      plates: [
        ["field", sh(g(sheet)), { dome: .5 }],                                                                           /* the sheet */
        ["ink", lineP(Array.from({ length: 41 }, (_, i) => [19 + i, 26 - 2.4 * Math.sin(i / 40 * 5.5 * Math.PI) * (1 - i / 80)])), { ln: 2.2, z: .3, bev: .4, col: "#5A3A1E" }],   /* the heading's flourish */
        ["ink", lines, { ln: 1.1, cut: .3, col: "#8A6A44" }],                                                           /* its lines */
        ["field", all(g(rolls)), { z: .7, bev: .9, dome: 1.7, col: "#D9BD84" }],                                        /* the rolls */
        ["field", sh(S.ellipse(RL, 14, 3.3, 6.6)) + sh(S.ellipse(RL, 86, 3.3, 6.6)), { z: .85, bev: .4, col: "#C3A267" }],   /* their ends */
        ["field", spiral(RL, 14) + spiral(RL, 86), { ln: .8, cut: .4, paint: 0 }],                                       /* the rolled sheet */
        ["red", sh(g(tails)), { z: 1, bev: .5, dome: .4, col: "#9E2028", sh: 1 }],                                           /* the seal's ribbons */
        ["red", OBJ_circle(sealC[0], sealC[1], 6.6), { z: 1.4, bev: .7, dome: 1.1, col: "#C22E33", sh: 1 }],               /* the wax seal */
        ["red", OBJ_circle(sealC[0], sealC[1], 3.6), { ln: 1, cut: .45, paint: 0 }],
        ["glass", sh(g(bottle)), { lvl: "well", z: .9, bev: .6, dome: .4, col: "#2F4E6E", sh: 1 }],                     /* the cut-glass inkwell */
        ["glass", sh(S.poly([[66, 75], [71, 77], [71, 95], [66, 93]])), { lvl: "well", z: .9, bev: .3, col: "#4C7398" }],   /* its facets: left */
        ["glass", sh(S.poly([[91, 77], [96, 75], [96, 93], [91, 95]])), { lvl: "well", z: .9, bev: .3, col: "#1F364F" }],   /* right */
        ["glass", sh(S.poly([[66, 75], [70.5, 70.5], [91.5, 70.5], [96, 75], [91, 77], [71, 77]])), { lvl: "well", z: .9, bev: .3, col: "#5D86AE" }],   /* its shoulder */
        ["brass", sh(g(collar)), { lvl: "well", z: 1.2, bev: .6, dome: .7 }],                                           /* its collar */
        ["cream", sh(g(quill)), { lvl: "well", z: 1.4, bev: .7, dome: 1, col: "#F4F2EA", sh: 1 }],                     /* the quill */
        ["cream", barbs, { lvl: "well", ln: .8, cut: .4, paint: 0 }],                                                   /* its barbs */
        ["cream", sh(shaft), { lvl: "well", z: 1.6, bev: .4, dome: .5, col: "#DCD6C6" }],                                /* its shaft */
      ],
    };
  }

  /* ---- Crisis Intervention Training - the life ring thrown to someone in crisis: the orange and white ring, its grab line running
     round its rim, lashed round the ring at four points, twisted all along. ---- */
  {
    const C = [50, 50], RO = 45, RI = 21, RP = 45.4, RW = 2.2;
    const body = ring(50, 50, RO, RI), rope = ring(50, 50, RP + RW, RP - RW);
    const t = S.trace(S.union([body, rope], 0), BB);
    const orange = S.inter(S.union([0, 90, 180, 270].map(a => wedge(C, a - 25, a + 25, 60)), 0), S.grow(body, .3));
    const wraps = S.union([45, 135, 225, 315].map(a => { const m = polar(C, (RI + RP + RW) / 2 - .3, a); return rbox(m[0], m[1], RP + RW - RI + 1.4, 6.4, a, 2.4); }), 0);
    let twist = ""; for(let a = 0; a < 360; a += 6.5){ if([45, 135, 225, 315].some(w => Math.abs(((a - w + 540) % 360) - 180) < 8)) continue; twist += lineP([polar(C, RP - RW + .4, a), polar(C, RP + RW - .4, a + 3.2)]); }
    let wrapT = ""; [45, 135, 225, 315].forEach(a => { const tg = [Math.cos((a + 90) * D), Math.sin((a + 90) * D)];
      for(let r = RI + 2; r < RP + RW - 1; r += 3.4){ const p = polar(C, r, a); wrapT += lineP([[p[0] - tg[0] * 2.4, p[1] - tg[1] * 2.4], [p[0] + tg[0] * 2.4 + (p[0] - C[0]) / r * 1.6, p[1] + tg[1] * 2.4 + (p[1] - C[1]) / r * 1.6]]); } });
    CHAPTER_OBJ["Crisis Intervention Training"] = {
      d: t.d, holes: t.holes, col: "#F05A28", base: "cream",
      plates: [
        ["cream", all(g(body)), { dome: 3.2, col: "#F3F1EC" }],                                                /* the ring, white */
        ["field", all(orange), { dome: 3.2 }],                                                                 /* its orange quarters */
        ["cream", all(rope), { z: .7, bev: .7, dome: 1, col: "#E2D3AE" }],                                      /* the grab line */
        ["cream", twist, { ln: .9, cut: .5, paint: 0 }],                                                        /* its twist */
        ["cream", all(wraps), { z: 1.3, bev: .8, dome: 1.2, col: "#E8DAB6", sh: 1 }],                          /* the lashings */
        ["cream", wrapT, { ln: .9, cut: .5, paint: 0 }],
      ],
    };
  }

  /* ---- Missing and Exploited Children - a teddy bear, sitting: the round head with its ears (their insides pressed in), the muzzle,
     the button eyes and nose, a blue ribbon bow at its neck, the plush tummy patch stitched on, the arms, the legs out in front with
     their round foot pads. ---- */
  {
    const head = S.circle(50, 29, 19), ears = S.union([S.circle(33, 14.5, 8.6), S.circle(67, 14.5, 8.6)], 0);
    const body = S.ellipse(50, 66, 20.5, 21.5), arms = S.union([S.capsule(33, 55, 20.5, 71, 7.4), S.capsule(67, 55, 79.5, 71, 7.4)], 0);
    const legs = S.union([S.ellipse(32.5, 86, 12, 10.5), S.ellipse(67.5, 86, 12, 10.5)], 0);
    const bow = S.union([S.grow(S.poly([[50, 49], [37.5, 42.5], [37.5, 55.5]]), 2), S.grow(S.poly([[50, 49], [62.5, 42.5], [62.5, 55.5]]), 2), S.circle(50, 49, 4.4)], 0);
    const sil = S.union([head, ears, body, arms, legs, bow], 1.6);
    let seam = ""; for(let k = 0; k < 18; k++){ const a0 = k * 20, a1 = a0 + 11; seam += lineP(ellP(ax, 50, 69, 13.6, 14.4, a0, a1, 3)); }
    CHAPTER_OBJ["Missing and Exploited Children"] = {
      d: sh(sil), col: "#B87A40", base: "field",
      plates: [
        ["field", all(g(S.union([arms, legs], 0))), { dome: 1.6, col: "#A86C36" }],                              /* the arms and legs */
        ["field", sh(g(body)), { z: .4, bev: .8, dome: 2.2 }],                                                   /* the body */
        ["cream", OBJ_ellipse(50, 69, 12, 13), { z: .3, bev: .6, dome: .8, col: "#E1BE8A" }],                    /* the tummy patch */
        ["field", seam, { ln: .8, cut: .4, paint: 0 }],                                                           /* stitched on */
        ["cream", OBJ_ellipse(32.5, 87, 7.2, 6.4) + OBJ_ellipse(67.5, 87, 7.2, 6.4), { z: .5, bev: .6, dome: .8, col: "#E1BE8A" }],   /* the foot pads */
        ["cream", OBJ_ellipse(21, 71.5, 4.6, 4.2) + OBJ_ellipse(79, 71.5, 4.6, 4.2), { z: .4, bev: .5, dome: .6, col: "#E1BE8A" }],   /* the paw pads */
        ["field", all(g(ears)), { dome: 1.4, col: "#A86C36" }],                                                  /* the ears */
        ["cream", OBJ_circle(33.5, 15, 4.6) + OBJ_circle(66.5, 15, 4.6), { z: -.6, bev: .6, col: "#DDB582" }],   /* their insides */
        ["field", sh(g(head)), { z: .7, bev: .9, dome: 2.4 }],                                                   /* the head */
        ["cream", OBJ_ellipse(50, 36.5, 9.6, 7.4), { z: 1.1, bev: .7, dome: .9, col: "#E6C696" }],               /* the muzzle */
        ["rubber", "M50 35V39.5M45.5 40.2Q50 43.6 54.5 40.2", { ln: 1, cut: .45, paint: 0 }],                    /* its mouth */
        ["rubber", OBJ_ellipse(50, 33, 4.4, 3.1), { z: 1.6, bev: .5, dome: .9, col: "#2B2220" }],                /* the nose */
        ["rubber", OBJ_circle(42.4, 25, 2.8) + OBJ_circle(57.6, 25, 2.8), { z: .9, bev: .5, dome: 1, col: "#2B2220" }],   /* the button eyes */
        ["water", sh(g(bow)), { z: 1, bev: .7, dome: 1.1, col: "#3B78C4", sh: 1 }],                              /* the ribbon bow */
        ["water", "M45.4 46.3L40 44.4M45.4 51.7L40 53.6M54.6 46.3L60 44.4M54.6 51.7L60 53.6", { ln: .8, cut: .45, paint: 0 }],    /* its folds */
        ["water", OBJ_circle(50, 49, 3.9), { z: 1.4, bev: .5, dome: .8, col: "#4A88D4" }],                       /* its knot */
      ],
    };
  }

  /* ---- Sexual Assault and Family Violence - the purple awareness ribbon (the colour of the domestic violence awareness ribbon): one
     satin ribbon looped at the top, crossing itself, its two tails cut in a V; the strand running to the right tail lies over the other
     and shades it; the woven edges along every strand. ---- */
  {
    const R = 10.6, Pq = (p0, p1, p2, s) => [(1 - s) * (1 - s) * p0[0] + 2 * (1 - s) * s * p1[0] + s * s * p2[0], (1 - s) * (1 - s) * p0[1] + 2 * (1 - s) * s * p1[1] + s * s * p2[1]];
    /* the ribbon's centre line: left tail end -> crossing -> up round the loop -> crossing -> right tail end */
    const cl = []; const LT = [17.5, 91], X1 = [57.5, 50], TOP = [50, 11.5], X2 = [42.5, 50], RT = [82.5, 91];
    for(let i = 0; i < 30; i++) cl.push(Pq(LT, LT, X1, i / 30));
    for(let i = 0; i < 30; i++) cl.push(Pq(X1, [82, 13], TOP, i / 30));
    for(let i = 0; i < 30; i++) cl.push(Pq(TOP, [18, 13], X2, i / 30));
    for(let i = 0; i <= 30; i++) cl.push(Pq(X2, X2, RT, i / 30));
    const back = S.union([S.cone(...LT, ...X1, R + 2.4, R), S.tube(X1, [82, 13], TOP, () => R, 24)], .5);
    const front = S.union([S.tube(TOP, [18, 13], X2, () => R, 24), S.cone(...X2, ...RT, R, R + 2.4)], .5);
    const notch = S.union([S.poly([[8, 101], [16, 90.5], [24, 101]]), S.poly([[76, 101], [84, 90.5], [92, 101]]), S.box(0, 97, 100, 10, 0)], 0);
    const cut = f => S.minus(f, notch);
    const t = S.trace(S.union([cut(back), cut(front)], 0), BB);
    /* the woven edges: E either side of the centre line; the strand behind loses its edges where the front strand lies over it */
    const E = 8, edges = (from, to, off, hide) => { let d = "", run = [];
      for(let i = from; i < to; i++){ const a = cl[Math.max(0, i - 1)], b = cl[Math.min(cl.length - 1, i + 1)], l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
        const p = [cl[i][0] - (b[1] - a[1]) / l * off, cl[i][1] + (b[0] - a[0]) / l * off];
        if((hide && hide(...p) < .6) || notch(...p) < .8){ if(run.length > 1) d += lineP(run); run = []; } else run.push(p); }
      if(run.length > 1) d += lineP(run); return d; };
    const frontTail = S.cone(...X2, ...RT, R, R + 2.4);
    CHAPTER_OBJ["Sexual Assault and Family Violence"] = {
      d: t.d, holes: t.holes, col: "#7A3E9E", base: "field",
      plates: [
        ["field", all(g(cut(back))), { dome: 1.6 }],                                                                   /* the strand behind */
        ["field", edges(0, 60, E, S.grow(cut(front), .8)) + edges(0, 60, -E, S.grow(cut(front), .8)), { ln: .7, cut: .3, paint: 0 }],             /* its woven edges */
        ["field", sh(g(cut(front))), { z: .35, bev: .8, dome: 1.6, col: "#8646AC", sh: 1 }],                            /* the strand in front */
        ["field", edges(60, cl.length, E) + edges(60, cl.length, -E), { ln: .7, cut: .3, paint: 0 }],
      ],
    };
  }

  /* ---- Phonetic Alphabet and Military Time - an olive field watch: the steel case and polished bezel with its minute track, the black
     dial with lumed hour bars and a 24-hour inner ring of ticks, the hands at ten past ten and the red seconds hand, the knurled crown;
     the olive strap through the lugs, stitched along both edges, its steel buckle, keeper loops and holes. ---- */
  {
    const C = [48, 50], R = 25;
    const strapT = S.box(35, 1.5, 26, 30, 3.5), strapB = S.box(35, 68.5, 26, 30, 3.5);
    const lugs = S.union([S.box(33, 25, 7, 8, 2), S.box(56, 25, 7, 8, 2), S.box(33, 67, 7, 8, 2), S.box(56, 67, 7, 8, 2)], 0);
    const caseF = S.circle(C[0], C[1], R), crown = S.union([S.box(72, 45.5, 7.5, 9, 1.8), S.box(66, 47.5, 8, 5, 1)], .5);
    const buckle = S.box(32.5, 7, 31, 11, 3), buckleIn = S.box(36.5, 10, 23, 5, 1.5);
    const sil = S.union([strapT, strapB, lugs, caseF, crown, buckle], 1.2);
    let track = "", ticks24 = "", bars = "";
    for(let k = 0; k < 60; k++){ if(k % 5) track += lineP([polar(C, R - 3.4, k * 6), polar(C, R - 1.6, k * 6)]); }
    for(let k = 0; k < 24; k++) ticks24 += lineP([polar(C, 8.6, k * 15), polar(C, 10.4, k * 15)]);
    for(let k = 0; k < 12; k++){ if(k % 3) bars += lineP([polar(C, 13.6, k * 30 - 90), polar(C, 17.2, k * 30 - 90)]); }
    const quarters = [0, 90, 180].map(a => OBJ_poly([polar(C, 12.8, a - 3.5), polar(C, 18, a - 6), polar(C, 18, a + 6), polar(C, 12.8, a + 3.5)].map(p => p), .6)).join("") +
      OBJ_poly([polar(C, 12.4, 270), polar(C, 18.2, 262), polar(C, 18.2, 278)], .6);
    const hand = (a, len, w) => OBJ_poly([polar(C, w, a + 90), polar(C, len * .72, a + 90 * w * .9 / (len * .72) / D * D * 57.3 / 57.3 * 0 + 3), polar(C, len, a), polar(C, len * .72, a - 3), polar(C, w, a - 90), polar(C, 3.5, a + 180)], [.8, .5, .4, .5, .8, .8]);
    let stitch = ""; for(const x of [37.3, 58.7]) for(const [y0, y1] of [[3, 6.6], [19.6, 24], [76, 96]]) for(let y = y0; y < y1 - 1; y += 2.8) stitch += "M" + x + " " + F(y) + "V" + F(y + 1.5);
    CHAPTER_OBJ["Phonetic Alphabet and Military Time"] = {
      d: sh(sil), col: "#5E6E3C", base: "field",
      plates: [
        ["field", all(g(S.union([strapT, strapB], 0))), { dome: .8 }],                                                   /* the strap */
        ["field", stitch, { ln: .9, cut: .4, paint: 0 }],                                                                 /* its stitching */
        ["field", OBJ_rrect(35, 78, 26, 5.5, 1.5) + OBJ_rrect(35, 86, 26, 5.5, 1.5), { z: .45, bev: .5, dome: .4, col: "#4E5C31" }],   /* the keepers */
        ["rubber", OBJ_circle(48, 93, 2.2) + OBJ_circle(48, 74.5, 2.2), { z: -.6, bev: .4, col: "#3A4428" }],                          /* the strap's holes */
        ["steel", all(g(S.minus(buckle, buckleIn))), { z: .8, bev: .6, dome: .9, sh: 1 }],                               /* the buckle */
        ["steel", "M48 8.5V16.5", { ln: 2.4, z: 1.1, bev: .5 }],                                                          /* its tongue */
        ["steel", all(g(lugs)), { z: .5, bev: .6, dome: .6 }],                                                            /* the lugs */
        ["steel", sh(g(S.inter(S.union([crown, caseF], 2.5), S.box(64, 40, 30, 20, 0)))), { z: .5, bev: .5, dome: .7 }],                                                            /* the crown */
        ["steel", "M74 46V54M76 46V54M78 46V54", { ln: .7, cut: .4, paint: 0 }],                                           /* its knurl */
        ["steel", OBJ_circle(C[0], C[1], R), { z: .8, bev: .8, dome: 1.2 }],                                       /* the case and bezel */
        ["steel", track, { ln: .8, cut: .4, paint: 0 }],                                                                  /* the minute track */
        ["rubber", OBJ_circle(C[0], C[1], R - 5), { z: -.5, bev: .7, dome: .4, col: "#1F2421" }],                         /* the dial */
        ["rubber", ticks24, { ln: .8, z: .15, bev: .3, col: "#B9B5A0" }],                                                 /* the 24-hour ring */
        ["cream", bars, { ln: 2.1, z: .35, bev: .4, col: "#E9E4C6" }],                                                    /* the lumed hour bars */
        ["cream", quarters, { z: .35, bev: .4, col: "#E9E4C6" }],
        ["cream", hand(-150, 11.5, 1.9) + hand(-30, 17, 1.5), { z: .7, bev: .4, dome: .3, col: "#EFEBD2" }],   /* the hands */
        ["red", lineP([polar(C, -5, 200), polar(C, 17.5, 20)]), { ln: 1.1, z: .95, bev: .3, col: "#D8352C" }],             /* the seconds hand */
        ["brass", OBJ_circle(C[0], C[1], 2.4), { z: 1.1, bev: .4, dome: .6 }],
      ],
    };
  }

  /* ---- Multiculturalism and Human Relations - a desk globe: the ocean-blue world tilted on its axis, its raised continents (the
     Americas, Europe and Africa, Greenland), the equator and two meridians drawn on it; the brass meridian ring round it with a pivot at
     each pole; the turned stem and the round wooden foot seen from a little above. ---- */
  {
    const C = [46, 41], R = 31, tilt = 23, up = [Math.sin(tilt * D), -Math.cos(tilt * D)], rt = [-up[1], up[0]];
    const Q = frame(C, rt, up.map(v => -v));                    /* Q(east, south) in the globe's own (tilted) frame */
    const ball = S.circle(C[0], C[1], R), RM = 36.5, MW = 4.6;
    const N = polar(C, RM, -90 + tilt), So = polar(C, RM, 90 + tilt);
    const merid = S.inter(ring(C[0], C[1], RM + MW / 2, RM - MW / 2), S.poly([N, polar(C, 80, -90 + tilt), polar(C, 80, tilt), polar(C, 80, 90 + tilt), So]));
    const caps = S.union([S.circle(...N, 3.4), S.circle(...So, 3.4)], 0);
    const stemTop = [C[0], C[1] + RM + 1], stem = S.union([S.cone(stemTop[0], stemTop[1] - 2, C[0], 87, 3.2, 2.6), S.circle(C[0], 82, 3.8)], 1);
    const FC = [C[0], 89], FX = 24, FY = 5.6;
    const footTop = S.ellipse(FC[0], FC[1], FX, FY), foot = S.union([footTop, S.box(FC[0] - FX, FC[1], 2 * FX, 4.2, 0), S.ellipse(FC[0], FC[1] + 4.2, FX, FY)], 0);
    const axles = S.union([S.capsule(...polar(C, R - 2, -90 + tilt), ...N, 1.9), S.capsule(...polar(C, R - 2, 90 + tilt), ...So, 1.9)], 0);
    const sil = S.union([ball, merid, caps, axles, stem, foot], 1);
    /* the world in orthographic projection, centred on the Atlantic (40 W) and seen from 15 degrees above the equator */
    const L0 = -40, P0 = 15 * D, proj = (lon, lat) => { const l = (lon - L0) * D, p = lat * D;
      let x = Math.cos(p) * Math.sin(l), y = Math.cos(P0) * Math.sin(p) - Math.sin(P0) * Math.cos(p) * Math.cos(l);
      const c = Math.sin(P0) * Math.sin(p) + Math.cos(P0) * Math.cos(p) * Math.cos(l);
      if(c < 0){ const m = Math.hypot(x, y) || 1; x /= m; y /= m; }
      return Q(x * (R - .6), -y * (R - .6)); };
    const L = pts => S.inter(S.grow(S.poly(pts.map(([lo, la]) => proj(lo, la))), .7), S.circle(C[0], C[1], R - 1.3));
    const land = S.union([
      L([[-165, 64], [-140, 70], [-110, 72], [-90, 70], [-80, 63], [-65, 60], [-56, 52], [-66, 45], [-75, 38], [-81, 31], [-80, 26], [-82, 29], [-90, 30], [-97, 27],
         [-97, 21], [-90, 19], [-87, 21], [-88, 15], [-83, 10], [-79, 8], [-86, 12], [-92, 15], [-105, 20], [-110, 24], [-115, 30], [-118, 34], [-124, 40], [-124, 48], [-132, 56], [-150, 60], [-165, 60]]),   /* North America */
      L([[-79, 9], [-75, 11], [-62, 10], [-50, 1], [-35, -5], [-39, -15], [-48, -25], [-58, -35], [-65, -42], [-68, -53], [-73, -50], [-74, -40], [-71, -30], [-70, -18], [-76, -13], [-81, -5], [-80, 1]]),   /* South America */
      L([[-55, 60], [-44, 60], [-22, 70], [-20, 80], [-60, 82], [-72, 77]]),                                                                     /* Greenland */
      L([[-10, 36], [-9, 43], [-1, 46], [-4, 48], [1, 50], [8, 54], [10, 58], [5, 62], [15, 69], [28, 71], [40, 68], [40, 50], [28, 41], [23, 38], [16, 40], [12, 44], [8, 44], [3, 43], [-5, 36]]),   /* Europe */
      L([[-17, 21], [-16, 12], [-12, 7], [-5, 5], [5, 4], [9, 4], [10, -2], [13, -12], [12, -18], [15, -27], [18, -34], [26, -34], [33, -28], [35, -20], [40, -12], [40, -3], [51, 11],
         [43, 12], [37, 20], [32, 31], [20, 32], [10, 37], [-6, 35], [-10, 30]]),                                                                 /* Africa */
      L([[-24, 64], [-14, 64], [-14, 66.5], [-24, 66.5]]),                                                                                          /* Iceland */
    ], .4);
    const graticule = [[0, 1], [-45, 0], [45, 0]].map(([lo, isLat]) => { const o = []; for(let i = 0; i <= 30; i++){ const tt = -90 + 180 * i / 30; o.push(isLat ? proj(L0 + tt, 0) : proj(L0 + lo, tt * .98)); } return keep(o, p => land(...p) > .7); }).join("");
    CHAPTER_OBJ["Multiculturalism and Human Relations"] = {
      d: sh(sil), col: "#2E7FD3", base: "field",
      plates: [
        ["wood", sh(g(foot)), { dome: .5, col: "#6E4426" }],                                                              /* the foot */
        ["wood", sh(g(footTop)), { z: .3, bev: .5, dome: .3, col: "#8A5833" }],                                           /* its top */
        ["brass", sh(g(stem)), { z: .4, bev: .5, dome: 1 }],                                                              /* the stem */
        ["field", sh(g(ball)), { dome: 3 }],                                                                              /* the world */
        ["field", graticule, { ln: .8, cut: .35, paint: 0 }],                                                            /* the equator and two meridians */
        ["field", all(land), { z: .55, bev: .7, dome: .6, col: "#4E9F48" }],                                              /* its continents */
        ["brass", sh(g(merid)), { z: .9, bev: .6, dome: 1, sh: 1 }],                                                     /* the meridian ring */
        ["brass", lineP(ellP(ax, C[0], C[1], RM, RM, -90 + tilt + 8, 90 + tilt - 8, 40)), { ln: .7, cut: .4, paint: 0 }],
        ["brass", all(g(axles)), { z: .5, bev: .4, dome: .6 }],                                                          /* the axle */
        ["brass", OBJ_circle(...N, 3.4) + OBJ_circle(...So, 3.4), { z: 1.2, bev: .5, dome: 1 }],                       /* the pivots */
      ],
    };
  }

  /* ---- Code of Criminal Procedure and Bill of Rights - the open law book seen from a little above: the two pages curving down into
     the gutter, their lines of print, a section heading; under them the page block's edges along the foot and the outer sides; the
     maroon cover boards round it all; the ribbon marker hanging from the gutter. ---- */
  {
    const yT = s => 27 - 10.5 * (1 - Math.pow(1 - s, 2.4)), yB = s => 82 - 6 * (1 - Math.pow(1 - s, 2.4)), X = s => 50 - 41 * s;
    const pageL = [], n = 24; for(let i = 0; i <= n; i++){ const s = i / n; pageL.push([X(s), yT(s)]); } for(let i = n; i >= 0; i--){ const s = i / n; pageL.push([X(s), yB(s)]); }
    const mir = pts => pts.map(([x, y]) => [100 - x, y]);
    const blockL = []; for(let i = 0; i <= n; i++){ const s = i / n; blockL.push([X(s) - 2.6 * s, yB(s) + 4.6 * Math.pow(s, .6)]); }
    blockL.push([X(1) - 2.6, yT(1) + 2]); blockL.push([X(1), yT(1) + .5]); for(let i = n; i >= 0; i--){ const s = i / n; blockL.push([X(s), yB(s) - .5]); }
    const pL = S.poly(pageL), pR = S.poly(mir(pageL)), bL = S.poly(blockL), bR = S.poly(mir(blockL));
    const pagesAll = S.union([pL, pR, bL, bR], 0);
    const cover = S.grow((x, y) => pagesAll(x, y - 1.8), 2.2);
    const ribbon = S.minus(S.poly([[46.5, 80], [53.5, 80], [54.5, 98], [50, 94.5], [45.5, 98]]), S.box(0, 0, 100, 81, 0));
    const sil = S.union([cover, pagesAll, ribbon], .8);
    let lines = ""; [[0, .13, .86], [1, .13, .86], [2, .13, .86], [3, .13, .7], [5, .13, .86], [6, .13, .86], [7, .13, .86], [8, .13, .5]].forEach(([k, s0, s1]) => {
      const pts = []; for(let i = 0; i <= 12; i++){ const s = s0 + (s1 - s0) * i / 12; pts.push([X(s), yT(s) + 9 + k * 5.6 + (yB(s) - yB(0)) * 0 ]); } lines += lineP(pts); });
    const linesR = lines.replace(/(\d+(?:\.\d+)?) (\d+(?:\.\d+)?)/g, (m, x, y) => F(100 - +x) + " " + y);
    let edgesB = ""; for(const k of [1.3, 2.6, 3.7]) { const pts = []; for(let i = 1; i <= n; i++){ const s = i / n; pts.push([X(s) - 2.6 * s * k / 4.6, yB(s) + k * Math.pow(s, .6)]); } edgesB += lineP(pts) + lineP(mir(pts)); }
    CHAPTER_OBJ["Code of Criminal Procedure and Bill of Rights"] = {
      d: sh(sil), col: "#F1E8D2", base: "field",
      plates: [
        ["red", sh(g(cover)), { dome: .4, col: "#7C1F2B" }],                                                             /* the cover boards */
        ["red", sh(g(ribbon)), { z: .3, bev: .5, dome: .4, col: "#C8A13A" }],                                            /* the ribbon marker */
        ["cream", all(g(S.union([bL, bR], 0))), { z: .4, bev: .5, col: "#DCCFAE" }],                                     /* the page block */
        ["cream", edgesB, { ln: .6, cut: .3, paint: 0 }],                                                                /* its leaves */
        ["field", sh(g(pL)), { z: .7, bev: .6, dome: 1.3 }],                                                             /* the left page */
        ["field", sh(g(pR)), { z: .7, bev: .6, dome: 1.3, col: "#F6EEDB" }],                                             /* the right page */
        ["field", "M50 27.5V81.5", { ln: 1.8, cut: 1.1, paint: 0 }],                                                     /* the gutter */
        ["ink", lines + linesR, { ln: 1.3, cut: .3, col: "#8C8170" }],                                                   /* the print */
        ["red", lineP([[X(.3), yT(.3) + 4.5], [X(.7), yT(.7) + 4.5]]) + lineP([[100 - X(.3), yT(.3) + 4.5], [100 - X(.55), yT(.55) + 4.5]]), { ln: 2.4, z: .2, bev: .3, col: "#7C1F2B" }],   /* the section headings */
      ],
    };
  }

  /* ---- Verbal Communication - two speech bubbles, each a thick moulded slab whose side shows down and to the right: the blue one in
     front with three raised dots, the white one behind it with two raised lines, the front one's shadow on it. ---- */
  {
    const off = [2.6, 3.4], ext = f => { const fs = []; for(let k = 0; k <= 6; k++) fs.push(((t) => (x, y) => f(x - off[0] * t, y - off[1] * t))(k / 6)); return S.union(fs, 0); };
    const fb = S.union([S.box(4, 33, 58, 40, 15), S.grow(S.poly([[13, 66], [9, 86], [30, 69]]), 1.2)], 3);
    const bb = S.union([S.box(36, 8, 58, 40, 15), S.grow(S.poly([[80, 42], [88, 62], [68, 45]]), 1.2)], 3);
    const fbX = ext(fb), bbX = ext(bb);
    const sil = S.union([fbX, bbX], .6);
    CHAPTER_OBJ["Verbal Communication"] = {
      d: sh(sil), col: "#2F7FE0", base: "field",
      plates: [
        ["cream", sh(g(S.minus(bbX, bb))), { col: "#B9C1CA" }],                                                       /* the white bubble's side */
        ["cream", sh(g(bb)), { z: .5, bev: .8, dome: 1.6, col: "#EEF1F4" }],                                           /* the white bubble */
        ["cream", "M50 22H82M50 31H74", { ln: 4, z: .45, bev: .6, col: "#CDD4DC" }],                                     /* its lines */
        ["field", sh(g(S.minus(fbX, fb))), { col: "#1F5DAE" }],                                                        /* the blue bubble's side */
        ["field", sh(g(fb)), { z: .9, bev: .9, dome: 1.8, sh: 1 }],                                                     /* the blue bubble */
        ["cream", OBJ_circle(20, 53, 4.6) + OBJ_circle(33, 53, 4.6) + OBJ_circle(46, 53, 4.6), { z: 1.4, bev: .6, dome: 1, col: "#F4F7FA" }],   /* its dots */
      ],
    };
  }

  /* ---- Professionalism and Ethics - the scales of justice in brass: a fluted column standing on a two-step plinth seen from a little
     above (each step's top and right side show), the pivot boss and finial, the beam, and from each end a pair of chains down to a
     pan whose inside shows. ---- */
  {
    const tier = (x0, x1, yTop, h, d) => ({ front: S.poly([[x0, yTop + d], [x1, yTop + d], [x1, yTop + d + h], [x0, yTop + d + h]]),
      top: S.poly([[x0, yTop + d], [x0 + d * 1.2, yTop], [x1 + d * 1.2, yTop], [x1, yTop + d]]), side: S.poly([[x1, yTop + d], [x1 + d * 1.2, yTop], [x1 + d * 1.2, yTop + h], [x1, yTop + d + h]]),
      hull: S.poly([[x0, yTop + d], [x0 + d * 1.2, yTop], [x1 + d * 1.2, yTop], [x1 + d * 1.2, yTop + h], [x1, yTop + d + h], [x0, yTop + d + h]]) });
    const t1 = tier(15, 80, 80.5, 11.5, 4), t2 = tier(30.5, 66.5, 71.5, 8.5, 3.4);
    const colX = 50.5, col = S.box(colX - 4.2, 24, 8.4, 50, 1.2), cap = S.box(colX - 6.2, 23, 12.4, 4.6, 1.6), cb = S.box(colX - 6.2, 69.5, 12.4, 4.4, 1.4);
    const beam = S.union([S.capsule(15, 23.5, 86, 23.5, 2.6), S.circle(15, 23.5, 3.6), S.circle(86, 23.5, 3.6)], .8), boss = S.circle(colX, 23.5, 5.4), fin = S.union([S.circle(colX, 13, 4.4), S.cone(colX, 13, colX, 3, 2.6, .9)], .8);
    const pan = cx => { const rim = S.ellipse(cx, 57, 11.5, 3.6); return { rim, bowl: S.union([rim, half(S.ellipse(cx, 57, 11.5, 9.5), 57, 80)], 0), inner: S.ellipse(cx, 57, 9.4, 2.3) }; };
    function half(f, y0, y1){ return S.inter(f, S.box(-10, y0, 120, y1 - y0, 0)); }
    const pl = pan(15), pr = pan(86);
    const chains = S.union([S.capsule(15, 23.5, 5.5, 56, 2.5), S.capsule(15, 23.5, 24.5, 56, 2.5), S.capsule(86, 23.5, 76.5, 56, 2.5), S.capsule(86, 23.5, 95.5, 56, 2.5)], 0);
    const base = S.union([t1.hull, t2.hull], 1.5);
    const t = S.trace(S.union([base, col, cap, cb, beam, boss, fin, chains, pl.bowl, pr.bowl], .8), BB);
    let links = ""; [[15, 5.5], [15, 24.5], [86, 76.5], [86, 95.5]].forEach(([x0, x1]) => { for(let k = 1; k < 7; k++){ const tt = k / 7.2, x = x0 + (x1 - x0) * tt, y = 23.5 + 32.5 * tt; links += lineP([[x - 1.8, y - .5], [x + 1.8, y + .5]]); } });
    CHAPTER_OBJ["Professionalism and Ethics"] = {
      d: t.d, holes: t.holes, col: "#D9A63E", base: "brass",
      plates: [
        ["wood", sh(g(t1.top)) + sh(g(t2.top)), { z: .2, bev: .5, dome: .5, col: "#8E5A33" }],                               /* the plinth's tops */
        ["wood", sh(g(t1.front)) + sh(g(t2.front)), { z: .2, bev: .5, dome: .9, col: "#6E4426" }],                           /* its fronts */
        ["wood", sh(g(t1.side)) + sh(g(t2.side)), { z: .2, bev: .5, dome: .5, col: "#4F301B" }],                             /* its sides */
        ["brass", all(g(chains)), { dome: .9 }],                                                                              /* the chains */
        ["brass", links, { ln: .8, cut: .45, paint: 0 }],
        ["brass", all(g(S.union([pl.bowl, pr.bowl], 0))), { z: .3, bev: .7, dome: 1.6 }],                                    /* the pans */
        ["brass", all(S.union([pl.inner, pr.inner], 0)), { z: -.5, bev: .6, col: "#9C7426" }],                               /* their insides */
        ["brass", sh(g(col)), { z: .5, bev: .6, dome: 1.2, sh: 1 }],                                                         /* the column */
        ["brass", "M" + (colX - 2) + " 29.5V67.5M" + colX + " 29.5V67.5M" + (colX + 2) + " 29.5V67.5", { ln: .8, cut: .45, paint: 0 }],    /* its flutes */
        ["brass", sh(g(cb)) + sh(g(cap)), { z: .8, bev: .5, dome: .6 }],                                                     /* its base and capital */
        ["brass", sh(g(beam)), { z: 1, bev: .6, dome: .9 }],                                                                  /* the beam */
        ["brass", sh(g(boss)) + sh(g(fin)), { z: 1.3, bev: .5, dome: 1.1 }],                                                 /* the boss and finial */
      ],
    };
  }

  /* ---- Fitness, Wellness, and Stress Management - a running shoe from the side, toe to the right: the treaded rubber outsole, the
     white foam midsole (thick under the heel, a sculpted wave along it), the blue mesh upper with its vents, the darker heel counter and
     toe cap, the eyestay with its eyelets and the laces crossing over the tongue, the padded collar, the heel pull loop. ---- */
  {
    const outline = [[9, 84], [6, 66], [8, 52], [12, 47.5], [21, 50.5], [30, 48], [35, 40], [40, 35.5], [45.5, 36.5], [53, 43.5], [63, 49.5], [74, 54.5], [84, 58.5], [92, 63], [97, 71], [96, 79], [89, 85], [60, 87], [20, 87]];
    const rad = [4, 6, 4, 2.5, 3, 3, 2, 2, 2, 4, 4, 4, 5, 5, 4, 3, 4, 5, 4];
    const shoe = S.poly(outline);
    const mid = (x) => x < 16 ? 70 : x < 70 ? 70 + (x - 16) * 5 / 54 : 75 + (x - 70) * .2;
    const sole = S.inter(S.grow(shoe, .01), (x, y) => mid(x) - y);
    const outsole = S.inter(S.grow(shoe, .01), (x, y) => 81.5 - y);
    const counter = S.inter(shoe, S.union([S.ellipse(4, 66, 22, 21)], 0));
    const toecap = S.inter(shoe, S.ellipse(100, 74, 19, 13));
    const eyestay = S.inter(shoe, S.minus(S.grow(S.poly([[34, 41], [41, 35.5], [46, 37], [53, 44], [63, 50], [74, 55], [85, 59.5], [84, 66], [72, 62], [61, 57], [51, 51.5], [40, 47]]), .5), S.box(0, 0, 100, 0, 0)));
    const loop = S.capsule(10.5, 47.5, 7.5, 41.5, 2.9);
    const sil = S.union([shoe, loop], 1);
    const eyes = [[42.5, 43.5], [50.5, 48.5], [59.5, 54], [68.5, 58.5], [77.5, 62]];
    let laces = ""; eyes.forEach(p => { laces += lineP([[p[0] - .6, p[1] - .6], [p[0] + 1.6, p[1] - 7.2]]); });
    let tread = ""; for(let x = 14; x < 90; x += 5.5) tread += "M" + F(x) + " " + F(82.8) + "V" + F(87);
    let perf = ""; for(let r = 0; r < 3; r++) for(let k = 0; k < 5; k++){ const x = 50 + k * 6 + r * 3, y = 66 - r * 4.4 + k * 1.2; const ok = q => eyestay(...q) > .9 && toecap(...q) > .9 && counter(...q) > .9 && (q[1] < mid(q[0]) - 1.5); if(ok([x, y]) && ok([x + 2, y])) perf += "M" + F(x) + " " + F(y) + "H" + F(x + 2); }
    CHAPTER_OBJ["Fitness, Wellness, and Stress Management"] = {
      d: sh(sil), col: "#2D63D8", base: "field",
      plates: [
        ["field", sh(g(shoe)), { dome: 1.4 }],                                                                              /* the mesh upper */
        ["field", perf, { ln: 1.3, cut: .5, paint: 0 }],                                                                    /* its vents */
        ["field", sh(g(counter)), { z: .4, bev: .7, dome: .6, col: "#1F4AA6" }],                                            /* the heel counter */
        ["field", sh(g(toecap)), { z: .35, bev: .7, dome: .5, col: "#1F4AA6" }],                                            /* the toe cap */
        ["field", keep(ellP(ax, 4, 66, 19.6, 18.6, -75, 30, 24), q => shoe(...q) < -1.2 && q[1] > 55 && q[1] < mid(q[0]) - 1.2) + keep(ellP(ax, 100, 74, 16.5, 10.5, 180, 260, 16), q => shoe(...q) < -1.2 && q[1] < mid(q[0]) - 1.2), { ln: .8, cut: .4, paint: 0 }],   /* their stitching */
        ["field", sh(g(eyestay)), { z: .45, bev: .5, dome: .5, col: "#1B3F8E" }],                                           /* the eyestay */
        ["steel", eyes.map(p => OBJ_circle(p[0], p[1], 1.9)).join(""), { z: .75, bev: .3, dome: .5 }],                     /* its eyelets */
        ["glow", laces, { ln: 2.6, z: 1, bev: .4, dome: .3, col: "#C3E84A", sh: 1 }],                                       /* the laces */
        ["rubber", sh(g(loop)), { z: .3, bev: .5, dome: .6, col: "#25282E" }],                                              /* the pull loop */
        ["field", lineP([[12.5, 49.5], [21, 52.5], [30, 50]]), { ln: 2.4, z: .55, bev: .5, col: "#2A58BE" }],                /* the padded collar */
        ["cream", sh(g(sole)), { z: .3, bev: .6, dome: .7, col: "#F2F3F5" }],                                              /* the midsole */
        ["cream", lineP([[10, 76], [24, 78.5], [40, 76.5], [58, 79.5], [76, 78], [92, 77.5]]), { ln: .9, cut: .45, paint: 0 }],   /* its wave */
        ["rubber", sh(g(outsole)), { z: .35, bev: .5, dome: .3, col: "#2C2F35" }],                                         /* the outsole */
        ["rubber", tread, { ln: 1.6, cut: .5, paint: 0 }],                                                                  /* its tread */
      ],
    };
  }

  /* ---- Health and Safety Code (the controlled substances it governs) - a prescription bottle seen from a little above: the white
     child-resistant cap (its top face and its ridged side), the amber body, the paper label wrapped round it with its coloured band and
     print; two capsules spilled in front, lying on the ground. ---- */
  {
    const CX = 42, RX = 21.5, KY = .27;
    const cyl = (y0, y1, rx) => S.union([S.box(CX - rx, y0, 2 * rx, y1 - y0, 0), S.ellipse(CX, y0, rx, rx * KY), S.ellipse(CX, y1, rx, rx * KY)], 0);
    const capF = cyl(10, 26, RX + 1.2), capTop = S.ellipse(CX, 10, RX + 1.2, (RX + 1.2) * KY), body = cyl(26, 86, RX), lip = cyl(25, 28.5, RX - 1.2);
    const label = S.inter(body, S.union([S.box(0, 44, 100, 30, 0), S.ellipse(CX, 74, RX + 1, RX * KY)], 0));
    const labelCut = S.minus(label, S.ellipse(CX, 44, RX + 1, RX * KY));
    const pill = (a, b, r) => { const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; return { all: S.capsule(...a, ...b, r), half: S.inter(S.capsule(...a, ...b, r), (x, y) => ((x - m[0]) * (b[0] - a[0]) + (y - m[1]) * (b[1] - a[1])) / Math.hypot(b[0] - a[0], b[1] - a[1])) }; };
    const p1 = pill([62, 87.5], [84, 80], 5.6), p2 = pill([76, 93.5], [96, 95], 4.6);
    const sil = S.union([capF, body, p1.all, p2.all], .8);
    let ridges = ""; for(let k = -8; k <= 8; k++){ const x = CX + (RX + 1.2) * Math.sin(k / 8.6 * Math.PI / 2), y = (RX + 1.2) * KY * Math.cos(k / 8.6 * Math.PI / 2); ridges += "M" + F(x) + " " + F(10 + y + 1.2) + "V" + F(26 + y - .8); }
    const arc = (y, rx) => lineP(ellP(ax, CX, y, rx, rx * KY, 6, 174, 24));
    let print = ""; [[56, .78], [61, .78], [66, .5]].forEach(([y, k]) => { print += lineP(ellP(ax, CX - 2, y, RX * k, RX * KY * .9, 150, 30, 12)); });
    CHAPTER_OBJ["Health and Safety Code"] = {
      d: sh(sil), col: "#D9822B", base: "field",
      plates: [
        ["field", sh(g(body)), { dome: 1.8 }],                                                                            /* the amber bottle */
        ["field", arc(86, RX - 2), { ln: .8, cut: .4, paint: 0 }],
        ["cream", sh(g(labelCut)), { z: .35, bev: .4, dome: .6, col: "#F4F1E8" }],                                       /* the label */
        ["red", sh(S.inter(labelCut, S.union([S.box(0, 0, 100, 49.5, 0), S.ellipse(CX, 49.5, RX + 1, RX * KY)], 0))), { z: .45, bev: .3, dome: .6, col: "#2F6FB8" }],   /* its band */
        ["ink", print, { ln: 1.3, cut: .3, col: "#8F949B" }],                                                            /* its print */
        ["cream", sh(g(lip)), { z: .3, bev: .4, dome: .6, col: "#D7D9DC" }],                                             /* the neck */
        ["cream", sh(g(capF)), { z: .8, bev: .6, dome: 1.2, col: "#F2F3F4", sh: 1 }],                                    /* the cap */
        ["cream", ridges, { ln: .9, cut: .45, paint: 0 }],                                                                /* its ridges */
        ["cream", sh(g(capTop)), { z: .95, bev: .5, dome: .4, col: "#FBFBFC" }],                                         /* its top */
        ["cream", lineP(ellP(ax, CX, 10, RX - 3.5, (RX - 3.5) * KY, 0, 360, 40)), { ln: .9, cut: .45, paint: 0 }],
        ["cream", sh(g(p1.all)) + sh(g(p2.all)), { lvl: "pills", z: .5, bev: .6, dome: 1.3, col: "#F3F3F1", sh: 1 }],   /* the capsules */
        ["red", sh(g(p1.half)) + sh(g(p2.half)), { lvl: "pills", z: .5, bev: .6, dome: 1.3, col: "#D2342E" }],
      ],
    };
  }

  /* ---- De-Escalation - the dove of peace in flight with an olive sprig in its beak: the white body and head, the near wing raised and
     swept back with its long primaries and its rows of coverts, the far wing behind it in shade, the fanned tail, the dark eye, the
     beak; the sprig's leaves and an olive. ---- */
  {
    const body = S.union([rell(55, 61, 25, 12, -14), S.circle(29.5, 50.5, 9.6), S.cone(34, 53, 44, 58, 8.4, 10.5)], 4.5);
    const beak = S.poly([[21, 48], [13.6, 51.6], [21, 54.2]]);
    const tail = S.union([0, 1, 2, 3].map(k => S.cone(73, 64, 96 - k * .8, 51.5 + k * 7.6, 4.4, 4.8)), 1.6);
    const feather = (W, a, l, r0, r1) => S.cone(...W, ...polar(W, l, a), r0, r1);
    const WR = [55, 43];
    const nearW = S.union([rell(55, 50, 15, 8.5, -32)].concat([-62, -51, -40, -29, -18].map((a, k) => feather(WR, a, 40 - k * 2.4, 6, 3.6))), 2.5);
    const FW = [42, 46], farW = S.union([-128, -116, -104, -92].map((a, k) => feather(FW, a, 26 + k * 3, 5, 3.2)), 1.4);
    const SA = [18.5, 53.4], SB = [5.5, 71], sd = [SB[0] - SA[0], SB[1] - SA[1]], sl = Math.hypot(...sd), sa = Math.atan2(sd[1], sd[0]) / D;
    const sprig = S.capsule(...SA, ...SB, 1.5), leafAt = (t, side) => { const b = [SA[0] + sd[0] * t, SA[1] + sd[1] * t], a = sa + side * 48, c = polar(b, 5.4, a); return rell(c[0], c[1], 6.2, 2.4, a); };
    const leaves = S.union([leafAt(.3, 1), leafAt(.48, -1), leafAt(.7, 1), leafAt(.88, -1)], 0);
    const olive = S.circle(...polar(SB, 2.4, sa), 2.8);
    const sil = S.union([body, beak, tail, nearW, farW, sprig, leaves, olive], 1);
    let prim = ""; [-56.5, -45.5, -34.5, -23.5].forEach(a => { prim += lineP([polar(WR, 15, a), polar(WR, 36, a)]); });
    let tailC = ""; for(let k = 0; k < 3; k++){ const tip = [96 - (k + .5) * .8, 51.5 + (k + .5) * 7.6], a = Math.atan2(tip[1] - 64, tip[0] - 73) / D; tailC += lineP([polar([73, 64], 8, a), polar([73, 64], 21, a)]); }
    const cov = [0, 1].map(k => { const o = []; for(let i = 0; i <= 5; i++){ const x = 45 + k * 4.5 + i * 3.7, y = 52.5 - k * 5 - i * 1.9; o.push([x, y], [x + 1.9, y + 2]); } return lineP(o); }).join("");
    const veins = [[.3, 1], [.48, -1], [.7, 1], [.88, -1]].map(([t, side]) => { const b = [SA[0] + sd[0] * t, SA[1] + sd[1] * t], a = sa + side * 48; return lineP([polar(b, 1.5, a), polar(b, 9.5, a)]); }).join("");
    CHAPTER_OBJ["De-Escalation"] = {
      d: sh(sil), col: "#F1F2EE", base: "field",
      plates: [
        ["cream", sh(g(farW)), { dome: 1, col: "#C4CAD3" }],                                                              /* the far wing */
        ["cream", [-122, -110, -98].map(a => lineP([polar(FW, 12, a), polar(FW, 28, a)])).join(""), { ln: .9, cut: .45, paint: 0 }],
        ["field", sh(g(tail)), { dome: 1.1 }],                                                                             /* the tail */
        ["field", tailC, { ln: .9, cut: .45, paint: 0 }],
        ["field", sh(g(body)), { z: .4, bev: .8, dome: 2.4, sh: 1 }],                                                     /* the body and head */
        ["field", sh(g(nearW)), { z: .6, bev: 1, dome: 1.8, col: "#F8F9F6", sh: 1 }],                                    /* the near wing */
        ["field", prim, { ln: 1, cut: .5, paint: 0 }],                                                                     /* its primaries */
        ["field", cov, { ln: .8, cut: .4, paint: 0 }],                                                                     /* its coverts */
        ["field", all(g(S.union([sprig, leaves], .5))), { z: .5, bev: .5, dome: .7, col: "#5E9A3A" }],                    /* the olive sprig */
        ["field", veins, { ln: .7, cut: .35, paint: 0 }],
        ["field", all(g(olive)), { z: .7, bev: .4, dome: .8, col: "#3D6B2A" }],                                           /* an olive */
        ["brass", sh(g(beak)), { z: .6, bev: .4, dome: .5, col: "#E3A23C" }],                                             /* the beak */
        ["rubber", OBJ_circle(27.5, 48, 2.1), { z: .8, bev: .3, dome: .8, col: "#22262B" }],                              /* the eye */
      ],
    };
  }

  /* ---- Civil Process and Liability - papers served: a manila envelope from its back, its flap folded open behind, the papers drawn
     part way out (a sealed court paper in front, a second sheet behind it); the brass clasp through its reinforced eyelet; the side flaps'
     folds. ---- */
  {
    const env = S.box(7, 44, 86, 50, 2.5), flap = S.grow(S.poly([[9.5, 45], [50, 23.5], [90.5, 45]]), 1.5);
    const sh1 = rbox(44, 36, 52, 44, -7, 1.5), sh2 = rbox(58, 32, 50, 46, 6, 1.5);
    const sil = S.union([S.union([env, flap], .8), sh1, sh2], 0);
    const sh1v = S.minus(sh1, env);
    const rl = (cx, cy, a, pts) => rotP(pts, a, cx, cy);
    let print1 = "", print2 = ""; for(let k = 0; k < 4; k++){ print1 += lineP(rl(44, 36, -7, [[24, 22 + k * 5.2], [k === 3 ? 48 : 60, 22 + k * 5.2]])); }
    for(let k = 0; k < 3; k++) print2 += lineP(rl(58, 32, 6, [[68, 15 + k * 5.2], [79, 15 + k * 5.2]]));
    CHAPTER_OBJ["Civil Process and Liability"] = {
      d: sh(sil), col: "#D4AE66", base: "field",
      plates: [
        ["field", sh(g(flap)), { dome: .5, col: "#E3C585" }],                                                                /* the open flap */
        ["field", keep([[12, 44], [50, 25.5], [88, 44]], q => sh1(...q) > .9 && sh2(...q) > .9 && env(...q) > .9), { ln: .9, cut: .45, paint: 0 }],                                   /* its gummed edge */
        ["cream", sh(g(S.minus(sh2, env))), { lvl: "papers", z: .4, bev: .4, dome: .4, col: "#E9ECEF" }],                                   /* the sheet behind */
        ["ink", print2, { lvl: "papers", ln: 1.2, cut: .3, col: "#9AA1A9" }],
        ["cream", sh(g(sh1v)), { lvl: "papers", z: .4, bev: .4, dome: .4, col: "#F8F8F5" }],                            /* the court paper */
        ["ink", print1, { lvl: "papers", ln: 1.2, cut: .3, col: "#8E959D" }],
        ["red", OBJ_circle(...rl(44, 36, -7, [[64, 38]])[0], 4.4), { lvl: "papers", z: .45, bev: .5, dome: .8, col: "#B8242B" }],   /* its seal */
        ["field", sh(g(env)), { z: .9, bev: .8, dome: .9, sh: 1 }],                                                           /* the envelope */
        ["field", "M10 91L40 66M90 91L60 66M9.5 47.5Q50 52 90.5 47.5", { ln: .9, cut: .45, paint: 0 }],                       /* the side flaps' folds */
        ["field", OBJ_circle(50, 58, 6), { z: 1.1, bev: .5, dome: .4, col: "#C29A55" }],                                       /* the reinforced eyelet */
        ["brass", OBJ_circle(50, 58, 3.4) + OBJ_rrect(42, 56.4, 16, 3.2, 1.6), { z: 1.5, bev: .4, dome: .7 }],               /* the brass clasp */
      ],
    };
  }

  /* ---- TCOLE Rules - the Texas peace officer's star in its ring, the licence every rule governs: a five-point brass star, each arm
     cut into two facets along its ridge, a ball on every point; behind it a steel ring with a navy enamel band set with raised beads;
     the centre a navy disc with a small raised star. ---- */
  {
    const C = [50, 51.5], star = (ro, ri, c) => { const p = []; for(let i = 0; i < 10; i++){ const a = -90 + i * 36, r = i % 2 ? ri : ro; p.push(polar(c || C, r, a)); } return p; };
    const balls = S.union([0, 1, 2, 3, 4].map(i => S.circle(...polar(C, 41.5, -90 + i * 72), 5.2)), 0);
    const st = S.union([S.grow(S.poly(star(41, 16.5)), 1.2), balls], 1.6), rg = ring(C[0], C[1], 34, 25);
    const t = S.trace(S.union([st, rg], 1), BB);
    let beads = ""; for(let k = 0; k < 40; k++) beads += OBJ_circle(...polar(C, 29.5, k * 9 + 4.5), 1.05);
    let ridges = ""; for(let i = 0; i < 5; i++) ridges += lineP([polar(C, 12, -90 + i * 72), polar(C, 34, -90 + i * 72)]);
    CHAPTER_OBJ["TCOLE Rules"] = {
      d: t.d, holes: t.holes, col: "#D9A63E", base: "brass",
      plates: [
        ["steel", all(g(rg)), { dome: 1.2 }],                                                                              /* the ring */
        ["field", all(ring(C[0], C[1], 32, 27)), { z: -.4, bev: .5, col: "#1F3A78" }],                                     /* its navy band */
        ["steel", beads, { z: .1, bev: .3, dome: .5 }],                                                                     /* its beads */
        ["brass", sh(g(S.grow(S.poly(star(41, 16.5)), 1.2))), { z: 1, bev: .6, gem: 2.4, gw: 9, sh: 1 }],                  /* the star, faceted */
        ["brass", ridges, { ln: .7, cut: .35, paint: 0 }],
        ["brass", all(g(balls)), { z: 1, bev: .5, dome: 1.4 }],                                                             /* the balls on its points */
        ["field", OBJ_circle(C[0], C[1], 9.5), { z: 1.5, bev: .6, dome: .5, col: "#1F3A78" }],                              /* the centre */
        ["brass", OBJ_poly(star(7.5, 3.1), .4), { z: 2, bev: .4, gem: .5, gw: 1.6 }],                                       /* its star */
      ],
    };
  }

  /* ---- Professional Policing - the patrol cap seen from the front and a little above: the navy crown (its top face with the piping
     round it, the front rising from the band), the black band with its leather chin strap and two gilt buttons, the gloss black peak
     curving out toward us, the gold cap shield on the front. ---- */
  {
    const top = S.ellipse(50, 24, 45, 13.5);
    const front = S.poly([[5, 24], [95, 24], [83, 50], [17, 50]]);
    const band = S.union([S.box(17, 46, 66, 14, 0), S.ellipse(50, 60, 33, 5.5)], 0);
    const peak = S.inter(S.ellipse(50, 58, 39, 24), S.box(0, 58, 100, 30, 0));
    const crown = S.union([top, S.grow(front, 1.5)], 3);
    const sil = S.union([crown, band, peak], 1.5);
    const shield = OBJ_poly([[50, 24.5], [55.5, 27], [60, 26.5], [61, 33], [58.5, 41], [50, 46.5], [41.5, 41], [39, 33], [40, 26.5], [44.5, 27]], [1.2, 1.2, 1.2, 2, 3, 2.5, 3, 2, 1.2, 1.2]);
    const strap = S.union([S.box(17, 51, 66, 5.6, 1.5)], 0);
    CHAPTER_OBJ["Professional Policing"] = {
      d: sh(sil), col: "#24345F", base: "field",
      plates: [
        ["field", sh(g(crown)), { dome: 1.6 }],                                                                           /* the crown */
        ["field", sh(g(top)), { z: .35, bev: 1.2, dome: 1, col: "#2C3E6E" }],                                             /* its top */
        ["field", lineP(ellP(ax, 50, 24, 44.4, 12.9, 0, 360, 60)), { ln: 1, cut: .5, paint: 0 }],                          /* its piping */
        ["rubber", sh(g(band)), { z: .4, bev: .6, dome: .6, col: "#16181C" }],                                            /* the band */
        ["rubber", sh(g(strap)), { z: .65, bev: .4, dome: .4, col: "#26292F" }],                                          /* the chin strap */
        ["brass", OBJ_circle(21.5, 53.8, 3.1) + OBJ_circle(78.5, 53.8, 3.1), { z: 1, bev: .4, dome: .9 }],                 /* its buttons */
        ["rubber", sh(g(peak)), { z: .7, bev: .8, dome: 1.6, col: "#121417", sh: 1 }],                                    /* the peak */
        ["rubber", lineP(ellP(ax, 50, 58, 36, 21, 12, 168, 30)), { ln: .9, cut: .45, paint: 0 }],                          /* its stitched edge */
        ["brass", shield, { z: 1.1, bev: .6, dome: .7, sh: 1 }],                                                           /* the cap shield */
        ["field", OBJ_circle(50, 34.5, 5.2), { z: 1.6, bev: .4, dome: .4, col: "#24345F" }],                               /* its enamel centre */
        ["brass", OBJ_poly([0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => polar([50, 34.8], i % 2 ? 1.6 : 3.8, -90 + i * 36)), .3), { z: 2, bev: .3, gem: .4, gw: 1 }],
      ],
    };
  }

  /* ---- Racial Profiling - the traffic stop: a black-and-white patrol car from the side, front to the left: the black hood, roof and
     trunk, the white doors with a gold star, the glass with its pillar, the red and blue light bar, the push bumper, the spotlight on the
     pillar, the head and tail lamps, the door seams and handles, the wheels with their tyres and steel rims. ---- */
  {
    const outline = [[3, 72], [3, 60], [7, 55], [18, 51.5], [33, 49.5], [41, 34], [47, 32.5], [68, 32.5], [74, 34], [83, 48.5], [95, 51], [97, 58], [97, 72], [93, 76], [6, 76]];
    const rad = [2, 3, 4, 4, 2, 2.5, 3, 3, 2.5, 3, 3, 3, 2, 2, 2];
    const bodyF = S.grow(S.poly(outline), 0);
    const wheels = [24, 77].map(x => ({ x, tyre: S.circle(x, 77, 11.5), rim: S.circle(x, 77, 6.4) }));
    const arches = S.union(wheels.map(w => S.circle(w.x, 77, 13.6)), 0);
    const bar = S.union([S.box(48, 26.5, 20, 7, 2.6), S.box(51, 31, 14, 3, 0)], 0);
    const pushB = S.union([S.box(.5, 55, 5.5, 20, 1.8)], 0);
    const sil = S.union([bodyF, ...wheels.map(w => w.tyre), bar, pushB, S.circle(37, 47, 2.6)], 1);
    const doors = S.minus(S.inter(bodyF, S.box(33.5, 50.5, 41, 30, 0)), arches);
    const glass = S.union([S.grow(S.poly([[36, 49], [43, 36.5], [56, 36.5], [56, 49]]), 1.2), S.grow(S.poly([[59.5, 49], [59.5, 36.5], [70, 36.5], [77.5, 49]]), 1.2)], 0);
    const starP = (c, ro, ri) => OBJ_poly([0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => polar(c, i % 2 ? ri : ro, -90 + i * 36)), .4);
    CHAPTER_OBJ["Racial Profiling"] = {
      d: sh(sil), col: "#1C1F24", base: "field",
      plates: [
        ["field", sh(g(bodyF)), { dome: 1.2 }],                                                                          /* the black body */
        ["cream", sh(g(doors)), { z: .25, bev: .5, dome: .8, col: "#F1F2F4" }],                                           /* the white doors */
        ["glass", all(g(glass)), { z: -.5, bev: .5, dome: .3, col: "#3C5368" }],                                          /* the windows */
        ["field", "M57.8 51.8V75M35 51.8V74M73.2 51.8V65.5", { ln: .9, cut: .5, paint: 0 }],                                    /* the door seams */
        ["steel", "M44 54.5H49M63 54.5H68", { ln: 1.8, z: .4, bev: .3 }],                                                 /* the handles */
        ["brass", starP([46, 64], 5.2, 2.2), { z: .6, bev: .4, gem: .7, gw: 1.6 }],                                       /* the door star */
        ["red", sh(g(S.box(48, 26.5, 10.2, 7, 2.6))), { z: .7, bev: .5, dome: 1, col: "#E2342E" }],                       /* the light bar */
        ["water", sh(g(S.box(57.8, 26.5, 10.2, 7, 2.6))), { z: .7, bev: .5, dome: 1, col: "#2D6FE0" }],
        ["rubber", all(g(pushB)), { z: .6, bev: .5, dome: .6, col: "#2A2D33" }],                                          /* the push bumper */
        ["steel", OBJ_circle(37, 47, 2.6), { z: .8, bev: .4, dome: .8 }],                                                 /* the spotlight */
        ["glow", OBJ_rrect(5.5, 57, 6.5, 4.6, 1.6), { z: .4, bev: .4, dome: .5, col: "#FFF4C8" }],                        /* the headlamp */
        ["red", OBJ_rrect(91, 54.5, 5, 6.5, 1.6), { z: .4, bev: .4, dome: .5, col: "#D8352C" }],                          /* the tail lamp */
        ["rubber", all(S.inter(arches, S.grow(bodyF, .3))), { z: -.6, bev: .6, col: "#0E0F12" }],                         /* the wheel wells */
        ["rubber", all(g(S.union(wheels.map(w => w.tyre), 0))), { z: .6, bev: .9, dome: 1.2, col: "#2A2C31", sh: 1 }],   /* the tyres */
        ["steel", wheels.map(w => OBJ_circle(w.x, 77, 6.4)).join(""), { z: .9, bev: .5, dome: .7 }],                    /* the rims */
        ["steel", wheels.map(w => [0, 72, 144, 216, 288].map(a => lineP([polar([w.x, 77], 2.4, a), polar([w.x, 77], 5.6, a)])).join("")).join(""), { ln: 1, cut: .5, paint: 0 }],
        ["steel", wheels.map(w => OBJ_circle(w.x, 77, 2.2)).join(""), { z: 1.2, bev: .3, dome: .6 }],
      ],
    };
  }

  /* ---- Victims of Crime - shelter: an umbrella held over a heart. The canopy's panels in two blues meeting at the ribs, its scalloped
     edge and rib tips, the finial; the shaft running down behind the red heart to the leather crook handle. ---- */
  {
    const AX = 50, TY = 13, EY = 45, RX = 45, ry = EY - TY;
    const tips = [-1, -.5, 0, .5, 1].map(k => [AX + k * RX, EY]);
    const canopyPts = []; for(let i = 0; i <= 40; i++){ const t = Math.PI * i / 40; canopyPts.push([AX - RX * Math.cos(t), EY - ry * Math.sin(t)]); }
    for(let k = 3; k >= 0; k--){ const a = tips[k + 1], b = tips[k]; for(let i = 1; i < 10; i++){ const s = i / 10; canopyPts.push([a[0] + (b[0] - a[0]) * s, EY - 5.5 * Math.sin(Math.PI * s)]); } }
    const canopy = S.grow(S.poly(canopyPts), .8);
    const rib = dx => { const o = []; for(let i = 0; i <= 20; i++){ const t = Math.PI / 2 * i / 20; o.push([AX + dx * Math.sin(t), EY - ry * Math.cos(t)]); } return o; };
    const panel = (d0, d1) => S.inter(canopy, S.poly(rib(d0).concat(rib(d1).reverse())));
    const panelsA = S.union([panel(-RX - 6, -RX / 2), panel(0, RX / 2)], 0), panelsB = S.union([panel(-RX / 2, 0), panel(RX / 2, RX + 6)], 0);
    const fin = S.union([S.cone(AX, TY + 2, AX, 4.5, 2.8, 2.2), S.circle(AX, 4.6, 3)], .5);
    const shaft = S.capsule(AX, EY - 2, AX, 88, 2.8);
    const hook = S.tube([AX, 82], [AX + 1, 97], [AX - 9, 95.5], () => 3.3, 14), hookEnd = S.circle(AX - 10, 94, 3.4);
    const heart = (() => { const pts = []; for(let i = 0; i <= 60; i++){ const t = 2 * Math.PI * i / 60, x = 16 * Math.pow(Math.sin(t), 3), y = -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)); pts.push([AX + x * 1.02, 66 + y * 1.02]); } return S.poly(pts); })();
    const tipBalls = S.union(tips.map(p => S.circle(p[0], p[1] + .5, 2.6)), 0);
    const sil = S.union([canopy, tipBalls, fin, shaft, hook, hookEnd, heart], .8);
    CHAPTER_OBJ["Victims of Crime"] = {
      d: sh(sil), col: "#2F5FA8", base: "field",
      plates: [
        ["leather", sh(g(S.union([hook, hookEnd, S.capsule(AX, 80, AX, 88, 2.8)], 1.2), .5)), { z: .3, bev: .6, dome: 1.1, col: "#6B3F24" }],                    /* the crook handle */
        ["steel", sh(g(shaft)), { z: .3, bev: .5, dome: .8 }],                                                               /* the shaft */
        ["field", all(g(panelsA)), { dome: 2.2 }],                                                                           /* the canopy */
        ["field", all(g(panelsB)), { dome: 2.2, col: "#3E78C8" }],
        ["field", lineP(rib(-RX / 2).slice(2)) + lineP(rib(0).slice(2)) + lineP(rib(RX / 2).slice(2)), { ln: 1.2, z: .25, bev: .3, col: "#24508F" }],   /* the ribs */
        ["steel", all(g(tipBalls)), { z: .4, bev: .4, dome: .8 }],                                                           /* the rib tips */
        ["steel", sh(g(fin)), { z: .5, bev: .4, dome: .9 }],                                                                  /* the finial */
        ["red", sh(g(heart)), { z: 1, bev: .9, dome: 2.4, col: "#D8352C" }],                                          /* the heart */
      ],
    };
  }

  /* ---- Identity Crimes - an identity card and a fingerprint: the card (its blue header band, the gold contact chip with its pads,
     the photo window pressed in, the lines of its details), and over its corner the fingerprint, its ridges looping round the core. ---- */
  {
    const a = -9, CC = [42, 46], card = rbox(CC[0], CC[1], 76, 50, a, 5);
    const Q = frame(CC, [Math.cos(a * D), Math.sin(a * D)], [-Math.sin(a * D), Math.cos(a * D)]);
    const band = S.inter(card, S.poly([Q(-50, -30), Q(50, -30), Q(50, -15), Q(-50, -15)]));
    const chip = S.grow(S.poly([Q(-30, -8), Q(-17, -8), Q(-17, 3), Q(-30, 3)]), 1.6);
    const photo = S.grow(S.poly([Q(-31, 8.5), Q(-15, 8.5), Q(-15, 20), Q(-31, 20)]), 1);
    const FP = [71, 64], fpA = 18, pad = rell(FP[0], FP[1], 16.5, 21, 90 + fpA);
    const sil = S.union([card, pad], 1.2);
    const P = (x, y) => { const c = Math.cos(fpA * D), s = Math.sin(fpA * D); return [FP[0] + x * c - y * s, FP[1] + x * s + y * c]; };
    /* the ridges: loops round a core a little above the pad's middle, each open at the lower left where the next one runs on; under them
       arches across the foot of the pad; all clipped to inside the pad's bevel */
    const inPad = p => rell(FP[0], FP[1], 16.5, 21, 90 + fpA)(...p) < -2.6;
    const clip = pts => { let d = "", run = []; pts.forEach(p => { if(inPad(p)) run.push(p); else { if(run.length > 1) d += lineP(run); run = []; } }); if(run.length > 1) d += lineP(run); return d; };
    let ridges = ""; for(let k = 0; k < 7; k++){ const rx = 1.6 + k * 1.95, ry = 2.4 + k * 2.45, o = [], a0 = 235 - k * 4, a1 = 235 + 300 + k * 4; for(let i = 0; i <= 40; i++){ const t = (a0 + (a1 - a0) * i / 40) * D; o.push(P(rx * Math.cos(t), -3.5 + ry * Math.sin(t))); } ridges += clip(o); }
    for(let k = 0; k < 3; k++){ const y = 14.5 + k * 2.4, w = 16, o = []; for(let i = 0; i <= 20; i++){ const x = -w + 2 * w * i / 20; o.push(P(x, y - 3 * Math.cos(x / w * Math.PI / 2))); } ridges += clip(o); }
    let lines = ""; [[-8, 18], [-2, 22], [4, 14], [10, 20]].forEach(([y, l]) => { lines += lineP([Q(-10, y), Q(-10 + l, y)]); });
    CHAPTER_OBJ["Identity Crimes"] = {
      d: sh(sil), col: "#CFE0F0", base: "field",
      plates: [
        ["field", sh(g(card)), { dome: .6 }],                                                                                /* the card */
        ["field", sh(g(band)), { z: .3, bev: .5, dome: .4, col: "#2C5D9E" }],                                               /* its header band */
        ["ink", lineP([Q(-30, -22.5), Q(4, -22.5)]), { ln: 2.6, z: .2, bev: .3, col: "#DCE8F4" }],                           /* its title */
        ["brass", sh(chip), { z: .4, bev: .4, gem: .5, gw: 1.6 }],                                                           /* the chip */
        ["brass", lineP([Q(-23.5, -8.5), Q(-23.5, 3.5)]) + lineP([Q(-30.5, -2.5), Q(-16.5, -2.5)]), { ln: .9, cut: .45, paint: 0 }],
        ["field", sh(photo), { z: -.6, bev: .5, col: "#A8C0D8" }],                                                          /* the photo window */
        ["ink", lines, { ln: 1.6, cut: .3, col: "#7E93A8" }],                                                                /* the details */
        ["field", sh(g(pad)), { z: 1, bev: .9, dome: 1.6, col: "#263F6B", sh: 1 }],                                          /* the fingerprint */
        ["water", ridges, { ln: 1.25, z: 1.2, bev: .35, col: "#8CBDEE" }],                                                  /* its ridges */
      ],
    };
  }

  /* ---- Interacting with Deaf or Hard-of-Hearing - an ear with a hearing aid behind it: the rolled rim (helix) running from the front
     over the top and down the back, the hollow inside it, the Y-shaped ridge inside that (antihelix), the deep bowl leading into the ear
     (concha) with the way in, the small flap in front of it (tragus) and the soft lobe; the aid's curved case behind the rim (its
     button), the clear tube over the top into the ear, its tip. ---- */
  {
    const ear = S.union([S.ellipse(61, 36, 21, 30), S.ellipse(54, 80, 10.5, 13), S.poly([[42, 40], [80, 44], [65, 78], [44.5, 76]])], 9);
    const rimIn = S.grow(ear, -6.2);
    const hollow = S.minus(S.inter(rimIn, S.box(0, 0, 100, 72, 0)), S.union([S.box(0, 40, 47, 40, 0)], 0));
    const anti = S.union([S.tube([59, 67], [71, 52], [67, 32], () => 3.6, 14), S.tube([67, 32], [64, 19], [51, 20], () => 3, 12)], 1.5);
    const concha = S.union([S.ellipse(54, 52, 9.5, 11.5), S.ellipse(56, 40, 6, 4)], 3);
    const crus = S.tube([45, 40], [52, 37], [60, 42], () => 2.2, 10);
    const tragus = rell(43.5, 54, 4.4, 6.8, 8);
    const aid = S.tube([69, 5.5], [93, 14], [87, 52], t => 5.6 - 1.4 * t, 22);
    const sil = S.union([ear, aid], 1.5);
    const tubeD = lineP(Array.from({ length: 21 }, (_, i) => { const s = i / 20; return [(1 - s) * (1 - s) * 67 + 2 * (1 - s) * s * 48 + s * s * 51.5, (1 - s) * (1 - s) * 5 + 2 * (1 - s) * s * 6 + s * s * 47]; }));
    CHAPTER_OBJ["Interacting with Deaf or Hard-of-Hearing"] = {
      d: sh(sil), col: "#D9A47D", base: "field",
      plates: [
        ["steel", sh(g(aid)), { z: .3, bev: .7, dome: 1.7, col: "#C6CBD2" }],                                                /* the hearing aid */
        ["steel", OBJ_circle(87.5, 28, 2.7), { z: .7, bev: .4, dome: .6, col: "#9AA3AE" }],                                  /* its button */
        ["field", sh(g(ear)), { z: .6, bev: .9, dome: 1.6 }],                                                                /* the ear and its rim */
        ["field", sh(g(hollow)), { z: -1.4, bev: 2, dome: .2, col: "#BE845F" }],                                             /* the hollow inside the rim */
        ["field", sh(g(anti)), { z: 1.1, bev: 1.6, dome: 1.3, col: "#E4B28C" }],                                             /* the ridge inside */
        ["field", sh(g(concha)), { z: -2, bev: 2.2, dome: .2, col: "#A46A4C" }],                                             /* the bowl */
        ["field", OBJ_ellipse(51, 49, 3.6, 4.2), { z: -.9, bev: 1.1, col: "#7A4836" }],                                      /* the way in */
        ["field", sh(g(tragus)), { z: 1, bev: 1.1, dome: 1, col: "#D9A47D" }],                                               /* the flap */
        ["glass", tubeD, { ln: 2.3, z: 1.1, bev: .4, col: "#DCE6EE", sh: 1 }],                                               /* the clear tube */
        ["steel", OBJ_circle(51.5, 48, 3), { z: 1.2, bev: .4, dome: .8, col: "#E6EAEE" }],                                   /* its tip */
      ],
    };
  }

  /* ---- Consular Notification - a passport seen from the front and a little above, so its page block shows along the top and right:
     the navy cover with the gold globe embossed on it and the chip mark, the cream pages' edges, a travel ticket tucked in at the top. ---- */
  {
    const x0 = 16, x1 = 70, y0 = 22, y1 = 94, d = 5;
    const cover = S.box(x0, y0, x1 - x0, y1 - y0, 4.5);
    const topS = S.poly([[x0 + 3, y0], [x0 + 3 + d, y0 - d * .8], [x1 + d - 1, y0 - d * .8], [x1, y0 + 1]]);
    const rightS = S.poly([[x1 - 1, y0 + 1], [x1 + d - 1, y0 - d * .8], [x1 + d, y1 - 4 - d * .8], [x1, y1 - 3]]);
    const pages = S.union([topS, rightS], 0);
    const tk = rbox(62, 20, 46, 18, 14, 2.5);
    const ticket = S.minus(tk, S.union([cover, S.box(0, y0 - 1, 100, 100, 0)], 0));
    const sil = S.union([cover, pages, tk], 1);
    const G = [43, 47], GR = 12.5;
    const glob = lineP(ellP(ax, G[0], G[1], GR * .45, GR, 0, 360, 30)) + lineP(ellP(ax, G[0], G[1], GR, GR * .35, 180, 360, 20)) + lineP(ellP(ax, G[0], G[1], GR, GR * .35, 0, 180, 20)) + "M" + F(G[0]) + " " + F(G[1] - GR) + "V" + F(G[1] + GR);
    let pageLines = ""; for(let k = 1; k <= 3; k++) pageLines += lineP([[x1 + k * 1.25, y0 + 1 - k * 1], [x1 + k * 1.25, y1 - 4 - k * 1]]) + lineP([[x0 + 4 + k * 1.25, y0 - k * 1], [x1 + k * 1.25 - 1, y0 - k * 1]]);
    CHAPTER_OBJ["Consular Notification"] = {
      d: sh(sil), col: "#1F3768", base: "field",
      plates: [
        ["cream", all(g(ticket)), { z: .2, bev: .4, dome: .4, col: "#EAF1F7" }],                                            /* the ticket */
        ["red", all(S.inter(ticket, S.box(73, 0, 6, 30, 0))), { z: .3, bev: .3, col: "#D8352C" }],                          /* its stripe */
        ["cream", all(g(pages)), { z: .2, bev: .4, col: "#EDE3C8" }],                                                        /* the pages */
        ["cream", pageLines, { ln: .6, cut: .3, paint: 0 }],                                                                 /* their edges */
        ["field", sh(g(cover)), { z: .5, bev: .8, dome: 1.1, sh: 1 }],                                                       /* the cover */
        ["field", "M" + (x0 + 4) + " " + (y0 + 2) + "V" + (y1 - 2), { ln: 1.1, cut: .55, paint: 0 }],                         /* its hinge */
        ["brass", OBJ_circle(G[0], G[1], GR + 1.1), { ln: 2.2, z: .3, bev: .4 }],                                            /* the embossed globe */
        ["brass", glob, { ln: 1.4, z: .3, bev: .35 }],
        ["brass", "M30 70H56M34 75.5H52", { ln: 2.2, z: .3, bev: .35 }],                                                     /* the words under it */
        ["brass", OBJ_rrect(37, 82, 12, 8, 1.6), { z: .35, bev: .35, gem: .3, gw: 1.4 }],                                    /* the chip mark */
        ["field", OBJ_circle(43, 86, 2.2), { z: .6, bev: .3, dome: .3 }],
      ],
    };
  }

  /* ---- Traumatic Brain Injury - the brain from the side, facing left: the cerebrum's folds (wandering grooves round its lobes, the deep
     lateral fissure above the temporal lobe, the central sulcus over the top), the finely ridged cerebellum tucked under its back, the
     brain stem. ---- */
  {
    const cer = S.union([S.ellipse(50, 39, 40, 27), S.ellipse(29, 46, 20, 21), S.ellipse(67, 43, 25, 22), rell(42, 58, 22, 9.5, -10)], 5);
    const cb = rell(70, 65.5, 17.5, 11, 8), stem = S.cone(58, 62, 55, 88, 7.4, 5.6);
    const sil = S.union([cer, cb, stem], 1.6);
    const deep = p => cer(...p) < -3.2;
    const clipD = pts => { let d = "", run = []; pts.forEach(p => { if(deep(p)) run.push(p); else { if(run.length > 2) d += lineP(run); run = []; } }); if(run.length > 2) d += lineP(run); return d; };
    /* the gyri: rounded folds lying in rings round the middle of the cerebrum, each wandering in and out, broken into lengths */
    const worms = [];
    [[.2, 0, 2, .9], [.45, 1.1, 4, .5], [.7, 2.3, 5, .35], [.95, .6, 6, .28], [1.2, 1.7, 7, .26]].forEach(([s, ph, n, gap]) => {
      for(let k = 0; k < n; k++){ const t0 = (k / n) * 2 * Math.PI + ph + gap / 2, t1 = ((k + 1) / n) * 2 * Math.PI + ph - gap / 2, pts = [];
        for(let i = 0; i <= 16; i++){ const t = t0 + (t1 - t0) * i / 16, w = 1 + .07 * Math.sin(5 * t + ph * 3); pts.push([49 + 37 * s * w * Math.cos(t), 40 + 23 * s * w * Math.sin(t)]); }
        for(let i = 0; i < 16; i++) worms.push(S.capsule(...pts[i], ...pts[i + 1], 2.7)); } });
    const gyri = S.minus(S.inter(S.union(worms, 0), S.grow(cer, -1.2)), S.union([S.capsule(17, 55, 37, 52, 1.2), S.capsule(37, 52, 64, 42, 1.2), S.capsule(53, 10, 50.5, 22, 1.1), S.capsule(50.5, 22, 52, 37, 1.1)], 0));
    const fissure = lineP([[17, 55], [26, 55.5], [37, 52], [48, 47.5], [58, 45], [64, 42]]), central = lineP([[53, 13], [50.5, 19], [53, 25], [50, 31], [52, 37]]);
    let folia = ""; for(let k = 0; k < 5; k++){ folia += keep(rotP(ellP(ax, 70, 66 + k * 3.2 - 4.8, 16 - Math.abs(k - 2) * 2.2, 3, 15, 165, 14), 8, 70, 66), q => cer(...q) > 1 && cb(...q) < -.8); }
    CHAPTER_OBJ["Traumatic Brain Injury"] = {
      d: sh(sil), col: "#E3A0A8", base: "field",
      plates: [
        ["field", sh(g(stem)), { dome: 1.4, col: "#D08A92" }],                                                               /* the brain stem */
        ["field", sh(g(cb)), { z: .3, bev: .7, dome: 1.5, col: "#CC858E" }],                                                 /* the cerebellum */
        ["field", folia, { ln: .9, cut: .45, paint: 0 }],
        ["field", sh(g(cer)), { z: .6, bev: 1, dome: 2.6, col: "#D98D97", sh: 1 }],                                          /* the cerebrum */
        ["field", all(g(gyri, .01)), { z: .45, bev: 1.1, dome: 1, col: "#EBAFB6" }],                                         /* its folds */
        ["field", fissure + central, { ln: 2.1, cut: 1.3, col: "#BF7480" }],                                                 /* the fissure and central sulcus */
      ],
    };
  }

  /* ---- Radio Communications, Alerts, and TCIC-TLETS - the officer's handheld radio seen from the front and a little above: the
     ribbed rubber antenna, the channel and volume knobs (their ridged sides and tops), the orange emergency button, the top of the case,
     the display, the speaker grille, the side push-to-talk bar, the rubber edge. ---- */
  {
    const x0 = 30, x1 = 74, y0 = 30, y1 = 95, d = 3.4;
    const body = S.box(x0, y0, x1 - x0, y1 - y0, 6.5), topF = S.inter(S.box(x0, y0 - d, x1 - x0, 12, 6.5), S.box(0, 0, 100, y0 + 4, 0));
    const ant = S.union([S.capsule(38, 8, 38, 30, 3.6), S.cone(38, 22, 38, 30, 3.6, 5)], .5);
    const knob = (cx, r, h) => ({ side: S.box(cx - r, y0 - 2 - h, 2 * r, h, 1), top: S.ellipse(cx, y0 - 2 - h, r, r * .38), all: S.union([S.box(cx - r, y0 - 2 - h, 2 * r, h + 2, 1), S.ellipse(cx, y0 - 2 - h, r, r * .38)], 0) });
    const k1 = knob(53, 4.6, 10), k2 = knob(65, 4.2, 7);
    const ptt = S.box(25, 44, 7, 22, 2.5);
    const sil = S.union([body, topF, ant, k1.all, k2.all, ptt], 1);
    const disp = S.box(x0 + 6, y0 + 7, x1 - x0 - 12, 14, 2.5);
    let grille = ""; for(let y = 59; y <= 86; y += 4.5) grille += "M" + (x0 + 9) + " " + y + "H" + (x1 - 9);
    let rib = ""; for(let y = 12; y < 28; y += 3) rib += "M34.6 " + y + "H41.4";
    const kr = (k, cx, r) => { let s = ""; for(let i = -3; i <= 3; i++){ const x = cx + r * Math.sin(i / 3.6 * Math.PI / 2); const ty = y0 - 2 - (k === 1 ? 10 : 7), dx = (x - cx) / r; s += "M" + F(x) + " " + F(ty + r * .38 * Math.sqrt(Math.max(0, 1 - dx * dx)) + .9) + "V" + F(y0 - 3.9); } return s; };
    CHAPTER_OBJ["Radio Communications, Alerts, and TCIC-TLETS"] = {
      d: sh(sil), col: "#33373F", base: "field",
      plates: [
        ["rubber", sh(g(ant)), { dome: 1.2, col: "#25282D" }],                                                               /* the antenna */
        ["rubber", rib, { ln: 1, cut: .5, paint: 0 }],
        ["rubber", sh(g(k1.all)) + sh(g(k2.all)), { z: .2, bev: .5, dome: .8, col: "#2A2D33" }],                             /* the knobs */
        ["rubber", kr(1, 53, 4.6) + kr(2, 65, 4.2), { ln: .8, cut: .4, paint: 0 }],
        ["rubber", sh(g(k1.top)) + sh(g(k2.top)), { z: .35, bev: .4, dome: .3, col: "#4A4F58" }],                            /* their tops */
        ["rubber", sh(g(ptt)), { z: .2, bev: .6, dome: .8, col: "#25282D" }],                                                /* the push-to-talk bar */
        ["rubber", "M27 49H31M27 53H31M27 57H31M27 61H31", { ln: .9, cut: .4, paint: 0 }],
        ["field", sh(g(body)), { z: .4, bev: .9, dome: 1.2 }],                                                               /* the case */
        ["field", sh(g(topF)), { z: .55, bev: .5, dome: .4, col: "#474C55" }],                                               /* its top */
        ["hot", OBJ_rrect(41, y0 - 3.2, 6, 4.2, 1.6), { z: 1, bev: .4, dome: .7, col: "#F07A1A" }],                         /* the emergency button */
        ["glass", sh(disp), { z: -.4, bev: .6, dome: .3, col: "#8FB3A0" }],                                                  /* the display */
        ["ink", "M41 43H63M41 47.5H55", { ln: 1.6, cut: .3, col: "#4E6B5C" }],
        ["rubber", OBJ_rrect(x0 + 6, 54, x1 - x0 - 12, 35, 4), { z: -.4, bev: .6, col: "#2A2D33" }],                        /* the speaker */
        ["rubber", grille, { ln: 2, cut: .7, paint: 0 }],                                                                    /* its grille */
      ],
    };
  }
}
