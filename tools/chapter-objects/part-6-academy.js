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
  /* (art11) an exact outline: f traced and made a polygon again, so its distance is true off its corners too; then a convex corner
     rounded by r (opening) and a concave one by rc (closing) */
  const exact = f => S.poly(S.simp(S.loops(f, BB)[0], .02));
  const round = (f, r, rc) => { let o = r ? S.grow(exact(S.grow(f, -r)), r) : f; if(rc) o = S.grow(exact(S.grow(o, rc)), -rc); return o; };
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

  /* ---- Arrest, Search, and Seizure - a pair of hinged handcuffs, laid as Madison's reference photo lies (ASP hinged cuffs: "There's no
     way you think these look alike. Redo the connection part ... ensure it's that good"). (art12) The pair lies on a diagonal, one cuff
     up and right, the other down and left, turned half round from each other about the hinge between them. Each cuff: the black
     lock case, long across the pair's axis, with its keyhole, four rivets and the yellow double-lock tab on the side toward its ring;
     the black double bar running from the case round the cuff's outer side to the round pivot at the far end; the polished single bow
     swinging from that pivot round the other side and back into the case, its ratchet teeth along its outer edge where it enters. The
     CONNECTION is the photo's: two flat steel hinge links side by side, each pinned into one case and the other, a dark gap between
     them, a joint across each at the middle. ---- */
  {
    const H = [50, 50], TH = -42 * D, U = [Math.cos(TH), Math.sin(TH)], V = [-Math.sin(TH), Math.cos(TH)], K = 1.2;   /* K: the local frame's scale */
    /* local frame: u along the pair's axis toward the upper cuff, v across it; the lower cuff is the upper one turned half round */
    const toA = (u, v) => [H[0] + K * (U[0] * u + V[0] * v), H[1] + K * (U[1] * u + V[1] * v)], toB = (u, v) => toA(-u, -v);
    const loc = (x, y) => { const dx = (x - H[0]) / K, dy = (y - H[1]) / K; return [dx * U[0] + dy * U[1], dx * V[0] + dy * V[1]]; };
    const WA = f => (x, y) => { const q = loc(x, y); return K * f(q[0], q[1]); }, WB = f => (x, y) => { const q = loc(x, y); return K * f(-q[0], -q[1]); };
    const pair = f => S.union([WA(f), WB(f)], 0);
    const pts2 = ps => ps.map(p => toA(...p)).concat([]), ptsB = ps => ps.map(p => toB(...p));
    /* one cuff, in the local frame */
    const CU = 12, CW = 13, CL = 27, caseL = S.box(CU - CW / 2, -CL / 2, CW, CL, 3.2);
    const RC = [28.5, 1.5], RO = 17.2, RI = 11.4, RB = 16.6, MR = (RO + RI) / 2, PA = -16;
    const sectorL = (a0, a1, r0, r1) => S.inter(ring(RC[0], RC[1], r1, r0), wedge(RC, a0, a1, 40));
    const barL = S.minus(sectorL(PA, 182, RI, RO), caseL);              /* the double bar: from the case round the outer side to the pivot */
    const PVL = polar(RC, MR, PA), pivotL = S.circle(PVL[0], PVL[1], 3.7);
    const bowL = S.minus(S.minus(sectorL(176, 360 + PA + 4, RI, RB), caseL), pivotL);   /* the single bow: from the pivot round the other side into the case */
    /* the hinge: two links side by side along the axis, pinned into each case */
    const LV = 5.4, LW = 4.6, LU = 9.2;
    const linkL = v => S.box(-LU, v - LW / 2, 2 * LU, LW, 1.7);
    const linksW = S.union([linkL(-LV), linkL(LV)].map(f => WA(f)), 0);     /* (the links are their own turned copies: symmetric already) */
    const gapW = WA(S.box(-LU + 3.3, -LV + LW / 2, 2 * (LU - 3.3), 2 * LV - LW, .6));
    const cases = pair(caseL), bars = pair(barL), bows = pair(bowL), pivots = pair(pivotL);
    /* (the space between the two links is a deep dark recess, the ground in shadow between them: a hole there split the pin's back,
       which carries the title, into pieces too small for it) */
    const sil = S.union([S.union([cases, bars, bows, pivots], .8), linksW, gapW], .5);
    const t = S.trace(sil, BB);
    const linkV = S.minus(linksW, cases), gapV = S.minus(S.minus(gapW, linksW), cases);
    /* the case's face, its keyhole, rivets, the double-lock tab */
    const faceL = S.box(CU - CW / 2 + 2.2, -CL / 2 + 2.2, CW - 4.4, CL - 4.4, 2);
    const KH = [CU + .5, -5.2], keyL = [[KH[0] - 1.9, KH[1]], [KH[0] - .3, KH[1] - 1.1], [KH[0] + 4.6, KH[1] - 1.6], [KH[0] + 4.6, KH[1] + 1.6], [KH[0] - .3, KH[1] + 1.1]];
    const keyholes = OBJ_circle(...toA(KH[0] - 1.2, KH[1]), 1.9 * K) + OBJ_poly(pts2(keyL.slice(1)), .5) + OBJ_circle(...toB(KH[0] - 1.2, KH[1]), 1.9 * K) + OBJ_poly(ptsB(keyL.slice(1)), .5);
    const rvL = [[CU - 3.6, -CL / 2 + 3.4], [CU + 3.6, -CL / 2 + 3.4], [CU - 3.6, CL / 2 - 3.4], [CU + 3.6, CL / 2 - 3.4]];
    const rivets = rvL.map(p => OBJ_circle(...toA(...p), 1.05 * K)).join("") + rvL.map(p => OBJ_circle(...toB(...p), 1.05 * K)).join("");
    const pinL = [[-LU + 1.9, -LV], [-LU + 1.9, LV], [LU - 1.9, -LV], [LU - 1.9, LV]];
    const pins = pinL.map(p => OBJ_circle(...toA(...p), 1.35 * K)).join("");
    const tabL = S.box(CU - 2.3, CL / 2 - 2.1, 4.6, 2.4, 1.1);            /* the yellow tab, on the case's edge toward its ring, between its rivets */
    /* the ratchet teeth: across the bow's outer edge, over the stretch that enters the case */
    let teeth = ""; for(let a = 186; a <= 246; a += 5){ const pa = polar(RC, RB - 2.6, a), pb = polar(RC, RB + .4, a);
      teeth += keep([toA(...pa), toA(...pb)], q => WA(bowL)(...q) < -.35) + keep([toB(...pa), toB(...pb)], q => WB(bowL)(...q) < -.35); }
    /* the double bar's seam along its middle */
    const seamL = []; for(let i = 0; i <= 40; i++){ const a = PA + 12 + (150 - PA - 12) * i / 40; seamL.push(polar(RC, MR, a)); }
    const onBarA = q => WA(S.minus(barL, S.grow(pivotL, .8)))(...q) < -.6, onBarB = q => WB(S.minus(barL, S.grow(pivotL, .8)))(...q) < -.6;
    const seams = keep(seamL.map(p => toA(...p)), onBarA) + keep(seamL.map(p => toB(...p)), onBarB);
    /* the joint across each link, at its middle */
    const joints = [-LV, LV].map(v => lineP([toA(0, v - LW / 2 + .9), toA(0, v + LW / 2 - .9)])).join("");
    const pv = [toA(...PVL), toB(...PVL)];   /* (world points: OBJ_ radii above are local x K) */
    CHAPTER_OBJ["Arrest, Search, and Seizure"] = {
      d: t.d, holes: t.holes, col: "#2A2D33", base: "rubber", backRot: -42,   /* the back's words run along the pair (badgeBackPlanAt) */
      plates: [
        ["rubber", all(g(S.minus(S.union([bars, cases], 0), pivots), .2)), { z: .45, bev: .8, dome: 1.2, col: "#2A2D33" }],      /* the black double bars and their cases */
        ["rubber", all(pair(faceL)), { z: .3, bev: .7, gem: .4, gw: 1.4, col: "#33373F" }],                                       /* each case's raised face */
        ["rubber", keyholes, { z: -.55, bev: .35, col: "#0C0D10" }],                                                              /* the keyholes */
        ["hot", all(pair(tabL)), { z: .35, bev: .4, dome: .5, col: "#F2C12E" }],                                                 /* the double-lock tabs */
        ["cream", all(g(bows, .2)), { z: .4, bev: .5, dome: 1, col: "#CDD4DB" }],                                                /* the polished single bows */
        ["cream", all(pair(S.inter(bowL, ring(RC[0], RC[1], (RI + RB) / 2 + 2, (RI + RB) / 2 + .4)))), { dome: .05, col: "#7B8590" }],   /* the dark band of the floor in the polished steel */
        ["cream", teeth, { ln: .9, cut: .6, col: "#9AA3AD" }],                                                                   /* their ratchet teeth */
        ["rubber", seams, { ln: .7, cut: .35, paint: 0 }],                                                                       /* the double bars' seams */
        ["cream", all(g(pivots, .2)), { z: .65, bev: .5, dome: 1.2, col: "#C4CBD3" }],                                           /* the round pivot pins */
        ["steel", all(g(linkV, .2)), { z: .45, bev: .6, dome: 1.1, col: "#B4BDC6" }],                                            /* the two hinge links */
        ["rubber", all(g(gapV, .1)), { z: -.3, bev: .4, col: "#121418" }],                                                        /* the gap between them */
        ["steel", joints, { ln: .8, cut: .45, paint: 0 }],                                                                       /* the joint across each link */
        ["steel", rivets + pins + pv.map(p => OBJ_circle(p[0], p[1], 1.6 * K)).join(""), { z: .3, bev: .3, dome: .6, col: "#D3D9DF" }],   /* rivets, hinge pins, the pivots' heads */
      ],
    };
  }

  /* ---- US and Texas Constitution and Rights - the parchment unrolled between its two rolls (their ends show the rolled sheet), the
     preamble's flourish of a heading and its lines in brown ink; the red wax seal on its ribbons; in front, a cut-glass inkwell and the
     white quill standing in it. (art10, Madison circled the seal and the quill's foot: the seal was a disc with a ring on two flat
     straps, and the quill stood IN FRONT of a flat brass lid.) Now the seal is a pool of red wax with a melted, uneven edge, a star
     pressed into it inside a ring, glossy; its two ribbon tails hang from under it over the bottom roll, each turning over once (the
     ribbon's back shows darker below the turn) and cut in a V. The inkwell has a round mouth: a brass rim seen from a little above,
     the ink dark inside it, and the quill's bare shaft goes down INTO it - the rim's front lip runs across in front of the shaft. The
     quill: a narrow vane and a broad one either side of the central rachis, barbs sweeping toward the tip, two splits in the broad
     vane. ---- */
  {
    const RL = 9, RR = 67, sheet = S.box(12.5, 14, 51, 72, 0);
    const roll = y => S.union([S.box(RL, y - 7, RR - RL, 14, 0), S.ellipse(RL, y, 3.6, 7), S.ellipse(RR, y, 3.6, 7)], 0);
    const rolls = S.union([roll(14), roll(86)], 0);
    const bottle = S.poly([[66, 76], [70.5, 71.5], [91.5, 71.5], [96, 76], [96, 93], [92, 96.5], [70, 96.5], [66, 93]]);
    /* the inkwell's round mouth: a brass rim (its top and its front face), the ink inside */
    const MC = [81, 65.2], neck = S.box(74.2, 65.2, 13.6, 7.5, 1.2);
    const rimO = S.ellipse(MC[0], MC[1], 8.2, 2.9), rimIn = S.ellipse(MC[0], MC[1], 5.7, 1.75);
    const rimAll = S.minus(S.union([rimO, S.box(MC[0] - 8.2, MC[1], 16.4, 1.9, 0), S.ellipse(MC[0], MC[1] + 1.9, 8.2, 2.9)], 0), rimIn);
    /* (art11) the rim is ONE clean ring, nothing cut out of it (the quill crossing its back left it looking broken open): the quill leans
       back, away from us, so the back of the rim is in front of it; the quill shows above the rim, and again inside the mouth, its bare
       shaft going down into the ink */
    const mouthAll = S.union([rimAll, rimO, neck, bottle], 0);
    /* the quill: from inside the mouth up to its tip */
    const A = [82, 67.5], B = [95.5, 5], L = Math.hypot(B[0] - A[0], B[1] - A[1]), w = [(B[0] - A[0]) / L, (B[1] - A[1]) / L], n = [w[1], -w[0]];
    const Qq = frame(A, w, n);                                  /* Q(along the shaft, across: + toward the scroll) */
    const t0 = .3, prof = t => { const s = (t - t0) / (1 - t0); return s <= 0 ? 0 : Math.pow(Math.sin(Math.PI * Math.min(1, s * .9 + .06)), .62); };
    const wl = t => 9.6 * prof(t), wr = t => 4.2 * prof(t), vpts = [];
    for(let i = 0; i <= 24; i++){ const t = t0 + (1 - t0) * i / 24; vpts.push(Qq(L * t, wl(t) + .01)); }
    for(let i = 24; i >= 0; i--){ const t = t0 + (1 - t0) * i / 24; vpts.push(Qq(L * t, -wr(t) - .01)); }
    const vane = S.grow(S.poly(vpts), .8), shaft = S.cone(...Qq(-2, 0), ...Qq(L * .99, 0), 1.75, .8);
    /* (art12) Madison: "where it's supposed to be inside of the ink thing isn't happening". The quill goes down INTO the mouth: it is in
       front of the rim's back half and of the ink, and behind the rim's front half, its front face, the neck and the bottle; where it is
       inside the mouth it is wet with ink */
    const front = S.union([S.inter(S.minus(rimO, rimIn), (x, y) => MC[1] + .15 - y), S.minus(rimAll, rimO), neck, bottle], 0);
    const quill = S.union([vane, shaft], 1), quillV = S.minus(quill, front), quillWet = S.inter(quillV, S.grow(rimIn, .2));
    let barbs = ""; for(let k = 0; k < 15; k++){ const t = t0 + .06 + k * .042; barbs += lineP([Qq(L * t, 1.7), Qq(L * (t + .05), wl(t + .05) * .84)]); }
    for(let k = 0; k < 9; k++){ const t = t0 + .1 + k * .06; if(wr(t + .04) > 2.4) barbs += lineP([Qq(L * t, -1.5), Qq(L * (t + .04), -wr(t + .04) * .8)]); }
    const splits = lineP([Qq(L * .5, 1.6), Qq(L * .56, wl(.56) + 1)]) + lineP([Qq(L * .74, 1.6), Qq(L * .8, wl(.8) + 1)]);
    /* the seal: a pool of wax with a melted edge, a star pressed in a ring; its two tails hang from under it, turning over once */
    const SC = [24.5, 71.5], sealPts = []; for(let i = 0; i < 72; i++){ const a = i / 72 * 2 * Math.PI, r = 7.1 + .5 * Math.sin(5 * a + .4) + .32 * Math.sin(9 * a + 1.3) + .2 * Math.sin(14 * a + 2); sealPts.push([SC[0] + r * Math.cos(a), SC[1] + r * Math.sin(a)]); }
    const seal = S.poly(sealPts);
    /* (art11) Madison: "Doesn't look like a legit ribbon" - the tails were boxy, pinched at a waist, with ragged ends. Now each tail is a
       satin ribbon hanging from under the seal along a gentle curve, a little narrower where it turns and flaring toward its end, cut in
       a clean swallowtail. */
    /* (art11b) each tail ends in a real swallowtail: the V is cut INTO the end, two points either side of it. The right tail turns over
       once, partway down: it narrows smoothly to the twist and widens again, and below it the ribbon's back shows, a deeper red. */
    const tail = (P0, C, P1, twist) => { const bz = t => [(1 - t) * (1 - t) * P0[0] + 2 * (1 - t) * t * C[0] + t * t * P1[0], (1 - t) * (1 - t) * P0[1] + 2 * (1 - t) * t * C[1] + t * t * P1[1]];
      const W = t => (5.4 + 2.3 * Math.pow(t, 1.8)) * (twist ? 1 - .6 * Math.exp(-Math.pow((t - twist) / .085, 2)) : 1 - .1 * Math.sin(Math.PI * Math.min(1, t / .8))), N = 40, L = [], R = [], mid = [];
      for(let i = 0; i <= N; i++){ const t = i / N, p = bz(t), q = bz(Math.min(1, t + .01)), o = bz(Math.max(0, t - .01)), dx = q[0] - o[0], dy = q[1] - o[1], l = Math.hypot(dx, dy), n = [-dy / l, dx / l], h = W(t) / 2;
        L.push([p[0] + n[0] * h, p[1] + n[1] * h]); R.push([p[0] - n[0] * h, p[1] - n[1] * h]); mid.push([p, n, h]); }
      const e = mid[N], fw = [e[1][1], -e[1][0]], notch = [e[0][0] - fw[0] * 3.8, e[0][1] - fw[1] * 3.8];   /* fw: forward along the tail; the notch goes back into it */
      const f = round(S.poly(L.concat([notch], R.slice().reverse())), .35);
      const k0 = twist ? Math.round(twist * N) : N;
      const back = S.inter(f, S.poly(mid.slice(k0).map(([p, n, h]) => [p[0] + n[0] * (h + 2), p[1] + n[1] * (h + 2)]).concat(mid.slice(k0).reverse().map(([p, n, h]) => [p[0] - n[0] * (h + 2), p[1] - n[1] * (h + 2)])).concat([[e[0][0] + fw[0] * 3, e[0][1] + fw[1] * 3]])));
      return { all: f, back }; };
    /* (art12) Madison: "it's supposed to look like it's resting on top of it, so why does the bottom make it look like it's built into
       it?" The tails end ON the bottom roll (they ran off its edge onto the pin's ground, a step below the paper), and the sheet and the
       rolls are no longer cut where the ribbon lies: the ribbon sits on them, over the roll's curve, with its shadow on the paper */
    const tL = tail([22, 74], [20.6, 83], [16.2, 90.6], 0), tR = tail([27.5, 74.5], [29.4, 83], [33.4, 90.6], .5);
    const tails = S.union([tL.all, tR.all], 0), ribbonAll = S.union([tails, S.grow(seal, 0)], 0), shift0 = (f, dx, dy) => (x, y) => f(x - dx, y - dy);
    const pts5 = []; for(let i = 0; i < 10; i++){ const a = -90 + i * 36, r = i % 2 ? 1.45 : 3.5; pts5.push(polar(SC, r, a)); }
    const sil = S.union([sheet, rolls, bottle, neck, rimAll, rimO, quill, tails, seal], 1);
    let lines = ""; for(let y = 38; y <= 70; y += 6.4) lines += "M" + (y > 60 ? 35 : 19) + " " + F(y) + "H" + (y > 60 ? 50 : 58);   /* (art11) the lines beside the seal start right of it */
    const spiral = (cx, cy) => { const p = []; for(let i = 0; i <= 30; i++){ const t = i / 30 * 3.2 * Math.PI, r = .2 + .8 * i / 30; p.push([cx + 2.6 * r * Math.cos(t), cy + 5.6 * r * Math.sin(t)]); } return lineP(p); };
    CHAPTER_OBJ["US and Texas Constitution and Rights"] = {
      d: sh(sil), col: "#E9D5A6", base: "field",
      plates: [
        ["field", sh(g(sheet)), { dome: .5 }],                                                                           /* the sheet */
        ["ink", lineP(Array.from({ length: 41 }, (_, i) => [19 + i, 26 - 2.4 * Math.sin(i / 40 * 5.5 * Math.PI) * (1 - i / 80)])), { ln: 2.2, z: .3, bev: .4, col: "#5A3A1E" }],   /* the heading's flourish */
        ["ink", lines, { ln: 1.1, cut: .3, col: "#8A6A44" }],                            /* its lines */
        ["field", all(g(rolls)), { z: .7, bev: .9, dome: 1.7, col: "#D9BD84" }],                                        /* the rolls */
        ["field", all(S.minus(S.inter(S.union([sheet, rolls], 0), S.grow(shift0(ribbonAll, .5, .9), .9)), ribbonAll)), { col: "#B99A60" }],   /* the ribbon's shadow on the paper */
        ["field", sh(S.ellipse(RL, 14, 3.3, 6.6)) + sh(S.ellipse(RL, 86, 3.3, 6.6)), { z: .85, bev: .4, col: "#C3A267" }],   /* their ends */
        ["field", spiral(RL, 14) + spiral(RL, 86), { ln: .8, cut: .4, paint: 0 }],                                       /* the rolled sheet */
        ["red", sh(g(S.minus(tL.all, seal), .2)), { z: .35, bev: .7, dome: .5, col: "#B3242B" }],                      /* the seal's ribbon tails, each its own band */
        ["red", sh(g(S.minus(S.minus(tR.all, seal), tL.all), .2)), { z: .35, bev: .7, dome: .5, col: "#B3242B" }],
        ["red", all(S.minus(tR.back, tL.all)), { col: "#9A1E25" }],                                                      /* past its twist, the ribbon's back (colour only) */
        ["red", sh(g(seal)), { z: .9, bev: .8, dome: 1.3, col: "#C42A30" }],                                            /* the wax seal */
        ["red", OBJ_circle(SC[0], SC[1], 5), { ln: .8, cut: .4, paint: 0 }],                                             /* its ring */
        ["red", OBJ_poly(pts5, .3), { z: -.35, bev: .3, col: "#A8222A" }],                                              /* its star, pressed in */
        ["glass", sh(g(bottle)), { z: .9, bev: .6, dome: .4, col: "#2F4E6E" }],                                         /* the cut-glass inkwell */
        ["glass", sh(S.poly([[91, 78], [96, 76], [96, 93], [91, 95]])), { col: "#1F364F" }],                            /* its facets: right */
        ["glass", sh(S.poly([[66, 76], [70.5, 71.5], [91.5, 71.5], [96, 76], [91, 78], [71, 78]])), { col: "#5D86AE" }],   /* its shoulder */
        ["glass", sh(g(S.minus(neck, rimAll))), { z: .9, bev: .4, dome: .6, col: "#3C6188" }],                         /* its neck */
        ["rubber", all(S.minus(rimIn, quillV)), { z: .6, bev: .3, col: "#101418" }],                                   /* the ink in it */
        ["brass", all(g(S.minus(S.minus(rimO, rimIn), quillV), .15)), { z: 1.1, bev: .4, dome: .5 }],          /* the mouth's rim: its top, a whole ring (the quill crosses its back half) */
        ["cream", all(g(quillV)), { z: 1.2, bev: .7, dome: 1, col: "#F4F2EA" }],                                       /* the quill, down into the mouth */
        ["cream", all(quillWet), { col: "#59606B" }],                                                                    /* where it is in the ink, wet */
        ["cream", barbs + splits, { ln: .6, cut: .35, paint: 0 }],                                                       /* its barbs and splits */
        ["cream", keep([Qq(L * .26, 0), Qq(L * .97, 0)], q => quillV(...q) < -.4), { ln: 1.15, z: .3, bev: .3, col: "#FFFFFF" }],   /* its rachis */
        ["brass", sh(g(S.minus(rimAll, rimO), .2)), { z: .9, bev: .35, dome: .3, col: "#B88A2E" }],                    /* its round front face */
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

  /* ---- Missing and Exploited Children - a plush teddy bear, sitting. (art10, Madison circled the whole bear and its ears: where each
     ear met the head there were arc seams and a notch, and the bear read lumpy - every part was laid whole over the one behind it, so
     each edge showed through the part in front as a ridge.) Now every part is cut where the part in front of it begins, so nothing
     shows through anything: the head and its ears are ONE soft shape (the ears grow out of it, no line where they meet), each inner ear
     a soft lighter oval set into its ear; the domed muzzle, the button nose and eyes, the stitched mouth; the round body with its
     stitched-on tummy patch; the arms and the legs in front of the body, meeting it in a soft crease, their paw and foot pads; the
     blue bow tie at the neck, in front of everything there. ---- */
  {
    const HC = [50, 29.5], HR = 17.6, EA = 46, ED = 17.8, ER = 8.3;
    const earC = [-1, 1].map(k => [HC[0] + k * ED * Math.sin(EA * D), HC[1] - ED * Math.cos(EA * D)]);
    const headU = S.union([S.circle(HC[0], HC[1], HR)].concat(earC.map(c => S.circle(c[0], c[1], ER))), 3.4);
    const body = S.union([S.ellipse(50, 61.5, 16.5, 15.5), S.ellipse(50, 71, 19.5, 15.5)], 6);
    const armC = [[36.2, 54.2, 23.4, 69.6], [63.8, 54.2, 76.6, 69.6]], arms = S.union(armC.map(a => S.cone(a[0], a[1], a[2], a[3], 6.6, 7.4)), 0);
    const legC = [[32.6, 86.4], [67.4, 86.4]], legs = S.union(legC.map(c => S.ellipse(c[0], c[1], 12, 10.4)), 0);
    const BW = [50, 48.6], bow = S.union([S.grow(S.poly([[50, 48.6], [38.6, 42.6], [38.6, 54.6]]), 2.1), S.grow(S.poly([[50, 48.6], [61.4, 42.6], [61.4, 54.6]]), 2.1), S.circle(50, 48.6, 4.3)], .8);
    const sil = S.union([S.union([body, arms, legs], 3), headU, bow], 1.4);   /* the crevices between arm, leg and body filled softly (no notch) */
    /* each part stops where the parts in front of it begin */
    const headP = S.minus(headU, bow), armsP = S.minus(arms, S.union([headU, bow], 0)), legsP = S.minus(legs, arms);
    const bodyP = S.minus(body, S.union([headU, bow, arms, legs], 0));
    const innerEar = earC.map((c, i) => { const k = i ? 1 : -1, o = [c[0] + k * 1.1 * Math.sin(EA * D), c[1] - 1.1 * Math.cos(EA * D)]; return rell(o[0], o[1], 4.6, 4, 90 - k * EA); });
    let stitch = ""; for(let k = 0; k < 22; k++){ const a0 = k * 360 / 22, a1 = a0 + 9; stitch += lineP(ellP(ax, 50, 69.5, 11.9, 12.9, a0, a1, 3)); }
    CHAPTER_OBJ["Missing and Exploited Children"] = {
      d: sh(sil), col: "#B87A40", base: "field",
      plates: [
        ["field", sh(g(bodyP)), { dome: 2.4 }],                                                                                       /* the body */
        ["cream", OBJ_ellipse(50, 69.5, 10.6, 11.6), { z: .2, bev: 1.4, dome: .5, col: "#E3C190" }],                                 /* the tummy patch */
        ["field", stitch, { ln: .75, cut: .35, paint: 0 }],                                                                            /* stitched on */
        ["field", all(g(legsP)), { dome: 2.3 }],                                                                                       /* the legs */
        ["cream", legC.map(c => OBJ_ellipse(c[0], c[1] + 1.2, 7.2, 6.3)).join(""), { z: .25, bev: 1, dome: .7, col: "#E3C190" }],    /* the foot pads */
        ["field", all(g(armsP)), { dome: 2.1 }],                                                                                       /* the arms */
        ["cream", OBJ_ellipse(22.6, 70.8, 4.5, 4.1) + OBJ_ellipse(77.4, 70.8, 4.5, 4.1), { z: .25, bev: .8, dome: .5, col: "#E3C190" }],   /* the paw pads */
        ["field", sh(g(headP)), { dome: 2.7 }],                                                                                        /* the head and its ears, one shape */
        ["cream", all(S.union(innerEar, 0)), { z: -.35, bev: 1.5, dome: .3, col: "#D9AB74" }],                                       /* the inner ears */
        ["cream", OBJ_ellipse(50, 37.2, 9.2, 7), { z: .5, bev: 1.3, dome: 1.3, col: "#E8CA9A" }],                                    /* the muzzle */
        ["rubber", "M50 36.4V39.8M45.6 40.3Q50 43.6 54.4 40.3", { ln: .9, cut: .45, paint: 0 }],                                      /* its stitched mouth */
        ["rubber", OBJ_ellipse(50, 34, 4.1, 2.9), { z: .6, bev: .5, dome: 1, col: "#2B2220" }],                                       /* the nose */
        ["rubber", OBJ_circle(42.6, 25.6, 2.6) + OBJ_circle(57.4, 25.6, 2.6), { z: .5, bev: .5, dome: .9, col: "#221B19" }],          /* the button eyes */
        ["water", sh(g(bow)), { z: .45, bev: .6, dome: 1.1, col: "#3B78C4" }],                                                  /* the bow tie */
        ["water", "M45.4 46.2L40.6 44.6M45.4 51L40.6 52.6M54.6 46.2L59.4 44.6M54.6 51L59.4 52.6", { ln: .8, cut: .4, paint: 0 }],       /* its folds */
        ["water", OBJ_circle(50, 48.6, 3.9), { z: .45, bev: .5, dome: .7, col: "#4A88D4" }],                                          /* its knot */
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
    /* (384.137) each tail is cut ACROSS ITS OWN LENGTH with its V centred on it. The cut was a level line (y 97) and two upright V's,
       but the tails run down at ~45 degrees, so each tail's round end stood out past the V as a step on its outer side (the "messed
       up parts" at the tail ends). tailEnd(end, from): < 0 on the ribbon's side of a V whose point is D in from the end, across width W. */
    const D = 5.5, W = 13;
    const tailEnd = (end, from) => { const ul = Math.hypot(end[0] - from[0], end[1] - from[1]), u = [(end[0] - from[0]) / ul, (end[1] - from[1]) / ul];
      const E = [end[0] - u[0] * 3, end[1] - u[1] * 3];
      return (x, y) => { const along = (x - E[0]) * u[0] + (y - E[1]) * u[1], across = Math.abs((x - E[0]) * -u[1] + (y - E[1]) * u[0]);
        return along + D - D * Math.min(across, W) / W; }; };
    const endL = tailEnd(LT, X1), endR = tailEnd(RT, X2);
    const notch = (x, y) => -Math.max(endL(x, y), endR(x, y));   /* < 0 where the tails are cut away */
    const cut = f => S.inter(S.inter(f, endL), endR);
    const t = S.trace(S.union([cut(back), cut(front)], 0), BB);
    /* the woven edges: E either side of the centre line; the strand behind loses its edges where the front strand lies over it */
    const E = 8, edges = (from, to, off, hide) => { let d = "", run = [];
      for(let i = from; i < to; i++){ const a = cl[Math.max(0, i - 1)], b = cl[Math.min(cl.length - 1, i + 1)], l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
        const p = [cl[i][0] - (b[1] - a[1]) / l * off, cl[i][1] + (b[0] - a[0]) / l * off];
        if((hide && hide(...p) < .6) || notch(...p) < .8){ if(run.length > 1) d += lineP(run); run = []; } else run.push(p); }
      if(run.length > 1) d += lineP(run); return d; };
    /* (art10) THE CROSSING IS ONE BAND FOLDED OVER THE OTHER. Madison circled it: the strand on top read as a flat box laid over the
       other, with straight seams and steps where it began and ended (round 3 raised it as a plate, cut square at both ends). Now
       nothing is raised: the ribbon is one smooth band all round, and the strand going down to the right tail passes over the other
       only by what a satin ribbon shows - its two edges press down onto the strand under it (a soft V where they meet), and that
       strand is shaded along them, deepest at the edge and on the side away from the light; the over strand's woven edges run on
       unbroken through the fold, the under strand's stop at it. */
    const frontTail = S.cone(...X2, ...RT, R, R + 2.4), ovS = cut(frontTail), unS = cut(S.cone(...LT, ...X1, R + 2.4, R));
    const shift = (f, dx, dy) => (x, y) => f(x - dx, y - dy);
    const ou = [(RT[0] - X2[0]), (RT[1] - X2[1])], ol = Math.hypot(...ou), on = [-ou[1] / ol, ou[0] / ol];
    const oEdge = k => { const o = []; for(let i = 0; i <= 60; i++){ const t = i / 60, r = (R + 2.4 * t) - .15; o.push([X2[0] + ou[0] * t + on[0] * r * k, X2[1] + ou[1] * t + on[1] * r * k]); } return o; };
    const onUnder = p => unS(...p) < -.25;
    const hx = (a, b, k) => "#" + [0, 1, 2].map(i => { const v = Math.round(parseInt(a.substr(1 + 2 * i, 2), 16) * (1 - k) + parseInt(b.substr(1 + 2 * i, 2), 16) * k); return (v < 16 ? "0" : "") + v.toString(16); }).join("").toUpperCase();
    /* the middle of the crossing */
    const lu = [X1[0] - LT[0], X1[1] - LT[1]], den = ou[0] * lu[1] - ou[1] * lu[0], tt = ((LT[0] - X2[0]) * lu[1] - (LT[1] - X2[1]) * lu[0]) / den;
    const XC = [X2[0] + ou[0] * tt, X2[1] + ou[1] * tt];
    /* (art11b) the shade is on the strand that goes under, at both its ends, darkest right at the over strand's edge (no shift) */
    const backC = cut(back), frontC = cut(front), tuck = w => S.minus(S.inter(S.inter(backC, S.circle(XC[0], XC[1], 24)), S.grow(frontC, w)), frontC);
    const SHADE = [0, 1, 2, 3, 4].map(k => ["field", all(tuck(2.8 - k * .6)), { col: hx("#8746AD", "#4E2270", (k + 1) / 5.4) }]);
    /* (art11) Madison: "It doesn't make sense where it crosses." art10's lift was one plate with a 7-unit bevel and grooves along the
       over strand's edges (a double edge, light bands across it). (art11b) The over strand is not touched at all now - its shading runs
       on along its own length through the crossing (art11's lift, eight plates round the crossing, still showed as a lighter band
       where the other strand ran under it). Instead the strand going under DIPS as it reaches it: ten thin plates on the under strand,
       each cut by a circle round the crossing a little wider than the last and stopping exactly at the over strand's edges, so they
       add to one crisp step down at those edges and a gentle ramp back up away from them. */
    const DIP = Array.from({ length: 10 }, (_, k) => ["field", all(S.minus(S.inter(backC, S.circle(XC[0], XC[1], 13 + k * 1.1)), frontC)), { z: -.065, bev: 1.3, paint: 0 }]);
    CHAPTER_OBJ["Sexual Assault and Family Violence"] = {
      d: t.d, holes: t.holes, col: "#7A3E9E", base: "field",
      plates: [
        ["field", all(g(S.union([cut(back), cut(front)], 0))), { col: "#8746AD" }],                                   /* the ribbon: a satin band, its edges rounded, its face level (art11b: a dome over the whole ribbon peaked where the strands cross - the band across the over strand) */
        ...SHADE,                                                                                                                       /* the under strand's shade where it tucks under */
        ...DIP,                                                                                                                         /* the under strand dips under it */
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
        ["cream", hand(-150, 11.5, 1.9) + hand(-30, 17, 1.5), { lvl: "hands", z: .7, bev: .4, dome: .3, col: "#EFEBD2" }],   /* the hands */
        ["red", lineP([polar(C, -5, 200), polar(C, 17.5, 20)]), { lvl: "hands", ln: 1.1, z: .95, bev: .3, col: "#D8352C" }],             /* the seconds hand */
        ["brass", OBJ_circle(C[0], C[1], 2.4), { lvl: "hands", z: 1.15, bev: .4, dome: .6 }],
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
        ["field", sh(g(S.minus(fbX, fb))), { lvl: "blue", z: .3, bev: .5, col: "#1F5DAE" }],                                                        /* the blue bubble's side */
        ["field", sh(g(fb)), { lvl: "blue", z: .9, bev: .9, dome: 1.8, sh: 1 }],                                                     /* the blue bubble */
        ["cream", OBJ_circle(20, 53, 4.6) + OBJ_circle(33, 53, 4.6) + OBJ_circle(46, 53, 4.6), { lvl: "blue", z: 1.6, bev: .6, dome: 1, col: "#F4F7FA" }],   /* its dots */
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
    const beam = S.union([S.capsule(15, 23.5, 86, 23.5, 2.6), S.circle(15, 23.5, 3.6), S.circle(86, 23.5, 3.6)], .8), boss = S.circle(colX, 23.5, 5.4), fin = S.union([S.circle(colX, 13.5, 4.4), S.cone(colX, 13.5, colX, 3, 2.6, .9), S.cone(colX, 14, colX, 22, 2.6, 3.2)], .8);   /* (round 3) the finial stands on the boss: one silhouette (it was a separate loop, taken as a hole) */
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
        ["wood", sh(g(t1.top)) + sh(g(t2.top)), { z: .2, bev: .5, dome: .9, col: "#9C6639" }],                               /* the plinth's tops */
        ["wood", sh(g(t1.front)) + sh(g(t2.front)), { z: .2, bev: .5, dome: 1.4, col: "#7A4B2A" }],                          /* its fronts */
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

  /* ---- Fitness, Wellness, and Stress Management - a running shoe from the side, toe to the right, long and low with the toe sprung
     up: the treaded rubber outsole; the white foam midsole, thick under the heel and thinning to the toe, an orange piping along its top;
     the blue mesh upper with its vents; the darker heel counter and toe bumper (stitched); the eyestay with six eyelets and white laces
     crossing over the instep; the padded tongue standing up with its pull tab; the dark lining showing at the ankle opening above the
     padded collar; the orange heel pull loop. (384.136 round 3, Madison: "The shoe is bad, make the shoe better" - round 2's was a tall
     slab with a flat sole.) ---- */
  {
    const outline = [[11, 83], [7, 73], [6, 61], [8.5, 50], [12.5, 45.5], [19, 46.5], [27, 48.5], [33, 46], [36.5, 39.5], [39.5, 33], [45, 32.5], [48.5, 36.5],
                     [56, 42], [65, 47.3], [74, 51.8], [83, 56], [90, 60], [95.5, 65.5], [97.5, 71], [95.5, 76.5], [88, 81], [74, 84], [50, 85.4], [26, 85.4], [16, 84.6]];
    const rad = [4, 6, 6, 4, 3, 4, 4, 3, 3, 2.5, 2.5, 3, 5, 5, 5, 5, 4, 4, 3, 4, 6, 6, 5, 5, 4];
    const shoe = S.poly(outline);
    const mid = x => 68 + 6.2 * Math.sin(Math.min(1, Math.max(0, (x - 6) / 64)) * Math.PI / 2) - Math.max(0, x - 82) * .18;
    const obot = x => 81.6 - Math.max(0, x - 76) * .26 - Math.max(0, 16 - x) * .12;
    const loop = S.capsule(10.6, 46.5, 8.6, 39.5, 2.7);
    const sil = S.union([shoe, loop], 1.2);
    const upper = S.inter(S.grow(shoe, .01), (x, y) => y - mid(x));
    const sole = S.inter(S.inter(S.grow(shoe, .01), (x, y) => mid(x) - y), (x, y) => y - obot(x));
    const outsole = S.inter(S.grow(shoe, .01), (x, y) => obot(x) - y);
    const counter = S.inter(upper, S.ellipse(3, 64, 22, 23));
    const bumper = S.inter(upper, S.ellipse(101, 71, 17.5, 12.5));
    const edgeTop = (x0, x1, off, w) => { const p = []; for(let i = 0; i <= 20; i++){ const x = x0 + (x1 - x0) * i / 20; p.push([x, topAt(x) + off]); } for(let i = 20; i >= 0; i--){ const x = x0 + (x1 - x0) * i / 20; p.push([x, topAt(x) + off + w]); } return S.poly(p); };
    function topAt(x){ for(let i = 9; i < 17; i++){ const a = outline[i], b = outline[i + 1]; if(x >= a[0] && x <= b[0]) return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]); } return x < 45 ? 33 : 60; }
    const eyestay = S.inter(upper, edgeTop(47, 88, 0, 7.6));
    const tongue = S.inter(S.grow(shoe, .01), S.poly([[35, 47], [37.2, 38.5], [40.2, 32.4], [45.6, 32], [49, 36.6], [47.5, 43.5]]));
    const lining = S.inter(S.grow(shoe, .01), S.poly([[11, 44], [19, 45.6], [27.5, 47.6], [34, 45.2], [36.5, 40], [37.5, 44.5], [34, 49.8], [27, 51.6], [19, 50], [12.5, 49]]));
    const eyes = [0, 1, 2, 3, 4, 5].map(k => { const x = 51 + k * 6.3; return [x, topAt(x) + 4.6]; });
    let laces = ""; eyes.forEach((p, k) => { laces += lineP([[p[0] - .3, p[1] - .3], [p[0] + 3.4, p[1] - 4.4 + .6]]); });
    const wave = lineP(Array.from({ length: 23 }, (_, i) => { const x = 10 + i * 3.8; return [x, (mid(x) + obot(x)) / 2 + 1.2 * Math.sin(i * .9)]; }));
    let tread = ""; for(let x = 17; x < 90; x += 5) tread += "M" + F(x) + " " + F(obot(x) + 1.2) + "V" + F(Math.min(85.4, obot(x) + 4.2));
    let vents = ""; for(let r = 0; r < 3; r++) for(let k = 0; k < 7; k++){ const x = 54 + k * 4.4 + (r % 2) * 2.2, y = 58 + r * 3.8 + (x - 54) * .2;
      const ok = q => eyestay(...q) > 1 && bumper(...q) > 1 && q[1] < mid(q[0]) - 2.4 && shoe(...q) < -2; if(ok([x, y]) && ok([x + 1.6, y])) vents += "M" + F(x) + " " + F(y) + "H" + F(x + 1.6); }
    CHAPTER_OBJ["Fitness, Wellness, and Stress Management"] = {
      d: sh(sil), col: "#2F63D9", base: "field",
      plates: [
        ["field", sh(g(upper)), { dome: 1.3 }],                                                                                 /* the mesh upper */
        ["rubber", sh(g(lining)), { z: -.6, bev: .8, col: "#1A2238" }],                                                         /* the lining at the ankle */
        ["field", lineP([[12.5, 48.8], [19.5, 50.6], [27, 52.2], [33.8, 49.8]]), { ln: 3.2, z: .45, bev: .6, dome: .4, col: "#3A70E4" }],   /* the padded collar */
        ["field", sh(g(tongue)), { z: .3, bev: .8, dome: .7, col: "#3B72E6" }],                                                 /* the tongue */
        ["field", sh(g(counter)) + sh(g(bumper)), { z: .4, bev: .7, dome: .55, col: "#1F4AA6" }],                                /* the heel counter and toe bumper */
        ["field", keep(ellP(ax, 3, 64, 19.8, 20.8, -60, 18, 24), q => counter(...q) < -1 && q[1] < mid(q[0]) - 1.4) + keep(ellP(ax, 101, 71, 15.2, 10.4, 186, 262, 16), q => bumper(...q) < -1 && q[1] < mid(q[0]) - 1.4) + vents + wave + tread, { ln: 1, cut: .45, paint: 0 }],   /* their stitching, the mesh's vents, the midsole's wave, the tread (one plate: the shoe is the first badge opened, so it is kept cheap) */
        ["field", sh(g(eyestay)), { z: .45, bev: .5, dome: .4, col: "#1B3F8E" }],                                               /* the eyestay */
        ["steel", eyes.map(p => OBJ_circle(p[0], p[1], 1.6)).join(""), { z: .75, bev: .3, dome: .5 }],                          /* its eyelets */
        ["cream", laces, { ln: 2.4, z: 1, bev: .4, dome: .3, col: "#F5F7FA", sh: 1 }],                                           /* the laces */
        ["cream", sh(g(sole)), { z: .35, bev: .6, dome: .7, col: "#F2F3F5" }],                                                  /* the midsole */
        ["hot", lineP(Array.from({ length: 25 }, (_, i) => { const x = 8.5 + i * 3.6; return [x, mid(x) + .2]; })), { ln: 1.6, z: .5, bev: .4, col: "#FF7A1F" }],   /* the orange piping */
        ["rubber", sh(g(outsole)), { z: .35, bev: .5, dome: .3, col: "#2A2D33" }],                                              /* the outsole */
        ["hot", sh(g(loop)) + OBJ_rrect(41.6, 31.9, 3.4, 2.6, 1.2), { z: .4, bev: .5, dome: .6, col: "#FF7A1F" }],                /* the heel pull loop, the tongue's tab */
      ],
    };
  }

  /* ---- Health and Safety Code (the controlled substances it governs) - a prescription bottle seen from a little above: the white
     child-resistant cap (its top face with its raised ring, its ridged side), the amber body - darker at its foot and towards its
     edges, a long highlight down its lit side, so it reads as a round, translucent bottle - the paper label wrapped round it, its
     coloured band and its lines of print following the curve; two capsules lying on the ground in front of it, each in its two halves
     (the cap half a little wider over the body half), the nearer one in front of the other, both shading the bottle where they lie
     against it. (art10: Madison circled the whole bottle and its capsules - "And these...".) ---- */
  {
    const CX = 42, RX = 21.5, KY = .27;
    const cyl = (y0, y1, rx) => S.union([S.box(CX - rx, y0, 2 * rx, y1 - y0, 0), S.ellipse(CX, y0, rx, rx * KY), S.ellipse(CX, y1, rx, rx * KY)], 0);
    /* (art11) the cap is one clean cylinder a little wider than the bottle, its ridges even, a plain lip round its foot, and its sides
       run straight down to that lip: no neck band under it and no fillet where it steps in to the bottle (that fillet was the bulge
       Madison circled on its right) */
    const RC = RX + .3, capF = cyl(10, 26, RC), capTop = S.ellipse(CX, 10, RC, RC * KY), body = cyl(26, 86, RX);
    const below = y => S.minus(S.box(0, y, 100, 100, 0), S.ellipse(CX, y, RX + .01, RX * KY));                          /* the bottle from the front arc at y down */
    const capBelow = y => S.minus(S.box(0, y, 100, 100, 0), S.ellipse(CX, y, RC + .01, RC * KY));
    const capLip = S.inter(capF, capBelow(23.2));
    const label = S.minus(S.inter(body, S.minus(below(44), below(74))), S.ellipse(CX, 44, RX + 1, RX * KY));
    /* a capsule A -> B in its two halves: the cap half (from A, a little wider) over the body half */
    const capsule = (A, B, r) => { const L = Math.hypot(B[0] - A[0], B[1] - A[1]), u = [(B[0] - A[0]) / L, (B[1] - A[1]) / L], M = [A[0] + u[0] * L * .54, A[1] + u[1] * L * .54];
      const along = (x, y) => (x - M[0]) * u[0] + (y - M[1]) * u[1];
      const whole = S.capsule(...A, ...B, r), capH = S.inter(whole, (x, y) => along(x, y)), bodyH = S.inter(whole, (x, y) => -along(x, y));   /* (art11) one radius: a wider cap half stepped the outline */
      const all_ = whole;
      const seam = [[M[0] - u[1] * (r - .6) + u[0] * .3, M[1] + u[0] * (r - .6) + u[1] * .3], [M[0] + u[1] * (r - .6) + u[0] * .3, M[1] - u[0] * (r - .6) + u[1] * .3]];
      /* (art12) its round: a lit band along its upper side and a shaded one along its lower side (colour only), so it reads as a
         cylinder lying down, not a slab */
      const n = u[1] > 0 ? [u[1], -u[0]] : [-u[1], u[0]], side = (x, y) => (x - A[0]) * n[0] + (y - A[1]) * n[1];
      const lit = S.inter(S.grow(whole, -.7), (x, y) => Math.max(r * .18 - side(x, y), side(x, y) - r * .62));
      const dark = S.inter(S.grow(whole, -.5), (x, y) => side(x, y) + r * .42);
      return { all: all_, capH, bodyH, seam, lit, dark }; };
    const p1 = capsule([62.5, 89], [84.5, 81.2], 5.4), p2 = capsule([93.6, 94.4], [71.5, 96.2], 4.5);
    const pills = S.union([p1.all, p2.all], 0);
    const shift0 = (f, dx, dy) => (x, y) => f(x - dx, y - dy);
    /* (art12) the capsules lie on their own soft shadow: the pin's edge runs round the shadow, not round each capsule, so a capsule's
       lower side is its own round, not the pin's bevel under it (that read as a second bottom) */
    const ground = S.minus(S.union([S.grow(shift0(pills, .4, 1.1), 1.2), S.grow(pills, .8)], 1), S.union([capF, body], 0));
    const sil = S.union([S.union([capF, body], 0), pills, ground], .6);
    const bodyP = S.minus(body, pills);
    let ridges = ""; for(let k = -8; k <= 8; k++){ const t = k / 9.6 * Math.PI / 2, x = CX + RC * Math.sin(t), y = RC * KY * Math.cos(t); ridges += "M" + F(x) + " " + F(10 + y + 1.6) + "V" + F(23.2 + y - 1); }
    /* print on the label: lines set from one left margin, following the cylinder (the front arcs of its ellipse) */
    const arcL = (y, t0, t1) => lineP(ellP(ax, CX, y, RX, RX * KY, t0, t1, 18));
    const print = arcL(56.5, 152, 48) + arcL(61, 152, 66) + arcL(65.5, 152, 84) + arcL(70, 152, 104);
    /* the amber's shading: bands down its sides, darkest at the right (away from the light), a highlight down its left */
    const strip = (x0, x1) => S.inter(bodyP, S.box(x0, 0, x1 - x0, 100, 0));
    const shift = (f, dx, dy) => (x, y) => f(x - dx, y - dy);
        /* (art11) each half is grown across the seam only (into its other half), never past the capsule's own outline: a half grown past
       it stood out as a hook at the seam */
    const pShade = [["field", all(S.minus(S.inter(bodyP, S.grow(shift(pills, -.3, -.4), 1.4)), pills)), { col: "#A65A19" }]];
    const capShade = S.minus(S.inter(bodyP, shift(capF, .3, 1.8)), capF);                                               /* the cap's shade on the bottle, just under its lip */
    CHAPTER_OBJ["Health and Safety Code"] = {
      d: sh(sil), col: "#3A3A43", base: "field",   /* (art13) the base under it all is the capsules' shadow colour: no lighter halo where a capsule meets it */
      plates: [
        ["rubber", all(g(ground)), { col: "#3A3A43" }],                                              /* the capsules' shadow on the ground */
        ["field", sh(g(bodyP)), { dome: 1.8, col: "#D9822B" }],                                                                          /* the amber bottle */
        ["field", all(strip(CX + RX * .55, 100)), { col: "#D07C29" }],                                                  /* its shading round the side */
        ["field", all(strip(CX + RX * .72, 100)), { col: "#C47124" }],
        ["field", all(strip(CX + RX * .86, 100)), { col: "#B4661F" }],
        ["field", all(strip(CX - RX * .6, CX - RX * .43)), { col: "#E8994C" }],                                         /* its highlight */
        ["field", all(S.inter(bodyP, below(81))), { col: "#B5641B" }],                                                   /* its foot, darker */
        ["field", keep(ellP(ax, CX, 85.2, RX - 1.6, (RX - 1.6) * KY, 8, 172, 24), q => S.grow(pills, .6)(...q) > 0), { ln: .8, cut: .4, paint: 0 }],
        ...pShade,                                                                                                       /* the capsules' shade on it */
        ["cream", sh(g(S.minus(label, pills))), { z: .3, bev: .5, dome: .6, col: "#F4F1E8" }],                         /* the label */
        ["cream", all(S.inter(S.minus(label, pills), S.box(CX + RX * .62, 0, 40, 100, 0))), { col: "#E7E3D8" }],        /* round the side */
        ["red", sh(S.inter(S.grow(label, .3), S.minus(S.box(0, 0, 100, 100, 0), below(49.5)))), { z: .3, bev: .3, dome: .6, col: "#2F6FB8" }],    /* its band */
        ["ink", print, { ln: 1.25, cut: .3, col: "#8F949B" }],                                                          /* its print */
        ["field", all(capShade), { col: "#9E5517" }],                                                                    /* the cap's shade on it */
        ["cream", sh(g(capF)), { z: .8, bev: .6, dome: 1.2, col: "#F2F3F4" }],                                          /* the cap: one cylinder, its sides straight down to its lip */
        ["cream", ridges, { ln: 1, cut: .6, paint: 0 }],                                                               /* its ridges */
        ["cream", sh(capLip), { col: "#E1E4E8" }],                                                                       /* its lip (colour only: no groove to dent its edge) */
        ["cream", sh(S.inter(g(capTop), capF)), { z: .95, bev: .5, dome: .4, col: "#FBFBFC" }],                                        /* its top */
        ["cream", lineP(ellP(ax, CX, 10, RX - 3.5, (RX - 3.5) * KY, 0, 360, 40)), { ln: 1.4, z: .3, bev: .4, col: "#ECEDEF" }],   /* its raised ring */
        ["cream", all(S.minus(S.inter(g(p1.bodyH, .2), S.grow(p1.all, .3)), p2.all)), { z: .6, bev: .9, dome: 2.8, col: "#F3F3F1" }],                      /* the capsules: the far one's body half, */
        ["red", all(S.minus(S.inter(g(p1.capH, .2), S.grow(p1.all, .3)), p2.all)), { z: .6, bev: .9, dome: 2.8, col: "#D2342E" }],   /* the far one's cap half, */
        ["red", all(S.inter(g(p2.capH, .2), S.grow(p2.all, .3))), { z: .85, bev: .9, dome: 2.8, col: "#D2342E" }],                      /* the near one's cap half, */
        ["cream", all(S.inter(g(p2.bodyH, .2), S.grow(p2.all, .3))), { z: .85, bev: .9, dome: 2.8, col: "#F3F3F1" }],                                       /* the near one's body half: each its own dome, so the near one lies over the far one */
        ["red", keep(p1.seam, q => p2.all(...q) > .3) + lineP(p2.seam), { ln: .7, cut: .3, paint: 0 }],                            /* where the halves meet */
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
        ["field", sh(g(nearW)), { z: .35, bev: 1.8, dome: 1.8, col: "#F8F9F6" }],                                    /* the near wing */
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
        ["brass", OBJ_poly([[49.2, 57], [43.2, 53.2], [42.2, 54.8], [48.6, 59.4]], .9) + OBJ_poly([[50.8, 57], [56.8, 53.2], [57.8, 54.8], [51.4, 59.4]], .9), { lvl: "clasp", z: 1.3, bev: .4, dome: .5 }],   /* the clasp's prongs, spread */
        ["brass", OBJ_circle(50, 58, 3.3), { lvl: "clasp", z: 1.6, bev: .4, dome: .6 }],                                          /* its washer */
        ["brass", OBJ_circle(50, 58, 1.3), { lvl: "clasp", z: 1.1, bev: .3, col: "#8A6A2A" }],               /* the brass clasp */
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
        ["brass", sh(g(S.grow(S.poly(star(41, 16.5)), 1.2))), { lvl: "star", z: 1, bev: .6, gem: 2.4, gw: 9, sh: 1 }],                  /* the star, faceted */
        ["brass", ridges, { lvl: "star", ln: .7, cut: .35, paint: 0 }],
        ["brass", all(g(balls)), { lvl: "star", z: 1.1, bev: .5, dome: 1.4 }],                                                             /* the balls on its points */
        ["field", OBJ_circle(C[0], C[1], 9.5), { lvl: "star", z: 1.6, bev: .6, dome: .5, col: "#1F3A78" }],                              /* the centre */
        ["brass", OBJ_poly(star(7.5, 3.1), .4), { lvl: "star", z: 2.1, bev: .4, gem: .5, gw: 1.6 }],                                       /* its star */
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
        ["brass", shield, { lvl: "shield", z: 1.1, bev: .6, dome: .7, sh: 1 }],                                                           /* the cap shield */
        ["field", OBJ_circle(50, 34.5, 5.2), { lvl: "shield", z: 1.6, bev: .4, dome: .4, col: "#24345F" }],                               /* its enamel centre */
        ["brass", OBJ_poly([0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => polar([50, 34.8], i % 2 ? 1.6 : 3.8, -90 + i * 36)), .3), { lvl: "shield", z: 2, bev: .3, gem: .4, gw: 1 }],
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

  /* ---- Victims of Crime - a mended heart: a plump red heart with a crack across it, and an adhesive bandage laid over the crack,
     corner to corner. (art12) Madison, of the umbrella over a heart: "Just change this one entirely, make it something else and make it
     great." Harm and healing in one picture: the split shows on both sides of the bandage and the bandage holds it closed. The heart
     is one dome; the crack is a jagged groove cut into it; the bandage is a cream strip with rounded ends, its gauze pad a paler raised
     square, a row of vent holes on each wing. ---- */
  {
    const AX = 50, HK = 2.72, HY = 43;
    const heart = round(S.poly(Array.from({ length: 200 }, (_, i) => { const t = 2 * Math.PI * i / 200;
      return [AX + 16 * Math.pow(Math.sin(t), 3) * HK, HY - (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) * HK]; })), 3.2, 3.2);
    /* the bandage: along A (rising to the right), centred a little above the heart's middle */
    const BC = [51.5, 47], A = -36 * Math.PI / 180, ca = Math.cos(A), sa = Math.sin(A);
    const rot = (u, v) => [BC[0] + u * ca - v * sa, BC[1] + u * sa + v * ca];
    const BL = 23.5, BW = 8.2, PL = 8.2, PW = 5.9;
    const band = S.capsule(...rot(-BL + BW, 0), ...rot(BL - BW, 0), BW);
    const pad = round(S.poly([rot(-PL, -PW), rot(PL, -PW), rot(PL, PW), rot(-PL, PW)]), 0, 1.4);
    const holes = [-18.2, -14.2, 14.2, 18.2].flatMap(u => [-3.2, 0, 3.2].map(v => OBJ_circle(...rot(u, v), .62))).join("");
    /* the crack: a jagged line across the heart, square to the bandage, its two ends showing either side of it */
    const ck = [[-25, 1.5], [-19, -2.2], [-13, 1.8], [-8, -1.6], [-3, 1.2], [3, -1.4], [8, 1.6], [13, -1.8], [19, 1.4], [24, -1]]
      .map(([v, u]) => rot(u, v));
    const crackLine = S.union(ck.slice(1).map((q, i) => S.capsule(...ck[i], ...q, .95)), 0);
    const crackV = S.minus(S.inter(crackLine, S.grow(heart, -2.4)), S.grow(band, .5));
    const sil = S.union([heart, band], .6);
    CHAPTER_OBJ["Victims of Crime"] = {
      d: sh(sil), col: "#C92E2A", base: "field",
      plates: [
        ["red", sh(g(heart)), { z: .5, bev: .8, dome: 2.8, col: "#D8352C" }],                                     /* the heart */
        ["red", all(crackV), { z: -.55, bev: .35, col: "#7E1714" }],                                                /* the crack, cut into it, either side of the bandage */
        ["cream", sh(g(band)), { z: .9, bev: .6, dome: 1.1, col: "#E8C39A" }],                                      /* the bandage */
        ["cream", holes, { z: -.3, bev: .15, col: "#B98D60" }],                                                     /* its vent holes */
        ["cream", sh(g(pad, .15)), { z: .45, bev: .45, dome: .7, col: "#F7EBDA" }],                               /* the gauze pad */
      ],
    };
  }

  /* ---- Identity Crimes - an identity card and a fingerprint: the card (its blue header band, the gold contact chip with its pads,
     the photo window pressed in, the lines of its details), and over its corner a fingerprint seal - a raised navy token in a
     polished steel rim, chamfered, the print raised on it, its ridges ending short of the rim. (art10, Madison circled the print: it read as crude rings. The ridges are
     now a real LOOP print: traced along the flow of a fingerprint's ridge field - a core where the ridges turn back on themselves and
     a delta below it, the classic model of a print - laid evenly apart, so they run, end and part as a print's do. The card stops where the seal begins and is shaded softly round it.) ---- */
  {
    const a = -9, CC = [42, 46], card = rbox(CC[0], CC[1], 76, 50, a, 5);
    const Q = frame(CC, [Math.cos(a * D), Math.sin(a * D)], [-Math.sin(a * D), Math.cos(a * D)]);
    const band = S.inter(card, S.poly([Q(-50, -30), Q(50, -30), Q(50, -15), Q(-50, -15)]));
    const chip = S.grow(S.poly([Q(-30, -8), Q(-17, -8), Q(-17, 3), Q(-30, 3)]), 1.6);
    const photo = S.grow(S.poly([Q(-31, 8.5), Q(-15, 8.5), Q(-15, 20), Q(-31, 20)]), 1);
    const TC = [72.5, 64.5], TR = 17.6, TF = 14.2, token = S.circle(TC[0], TC[1], TR);
    const sil = S.union([card, token], 1.2), cardP = S.minus(card, token);
    /* the print: evenly spaced streamlines of the Sherlock-Monro orientation field (a core and a delta), traced at merge time */
    /* evenly spaced streamlines of a loop-print orientation field (Sherlock-Monro), in a disc of radius RR */
    function fingerprint(opt){
      const RR = opt.R, SP = opt.sp, core = opt.core, delta = opt.delta, th0 = opt.th0 || 0;
      const dir = (x, y) => { const a = .5 * (Math.atan2(y - core[1], x - core[0]) - Math.atan2(y - delta[1], x - delta[0])) + th0; return [Math.cos(a), Math.sin(a)]; };
      const lines = [], pts = [];   /* pts: every accepted point, for the spacing test (a grid) */
      const G = new Map(), cell = SP, key = (x, y) => Math.floor(x / cell) + "," + Math.floor(y / cell);
      const near = (x, y, d, self) => { const cx = Math.floor(x / cell), cy = Math.floor(y / cell); let m = Infinity;
        for(let i = -1; i <= 1; i++) for(let j = -1; j <= 1; j++){ const a = G.get((cx + i) + "," + (cy + j)); if(!a) continue; for(const p of a){ if(p[2] === self) continue; const q = Math.hypot(p[0] - x, p[1] - y); if(q < m) m = q; } } return m; };
      const add = (p, id) => { const k = key(p[0], p[1]); if(!G.has(k)) G.set(k, []); G.get(k).push([p[0], p[1], id]); };
      const st = .22;
      const trace = (s, id, stopK) => {
        const half = sg => { const o = []; let x = s[0], y = s[1], d = dir(x, y); d = [d[0] * sg, d[1] * sg];
          for(let n = 0; n < 900; n++){
            let e = dir(x, y); if(e[0] * d[0] + e[1] * d[1] < 0) e = [-e[0], -e[1]];
            const mx = x + e[0] * st / 2, my = y + e[1] * st / 2; let f = dir(mx, my); if(f[0] * e[0] + f[1] * e[1] < 0) f = [-f[0], -f[1]];
            const nx = x + f[0] * st, ny = y + f[1] * st;
            if(Math.hypot(nx, ny) > RR) break;
            if(Math.hypot(nx - core[0], ny - core[1]) < SP * .55 || Math.hypot(nx - delta[0], ny - delta[1]) < SP * .45) break;
            if(near(nx, ny, SP * stopK, id) < SP * stopK) break;
            /* do not run back into its own earlier points (a closed loop) */
            if(o.length > 30){ let hit = false; for(let i = 0; i < o.length - 30; i += 2) if(Math.hypot(o[i][0] - nx, o[i][1] - ny) < SP * stopK){ hit = true; break; } if(hit) break; }
            d = f; x = nx; y = ny; o.push([x, y]);
          }
          return o; };
        const a = half(1), b = half(-1);
        return b.reverse().concat([s], a);
      };
      const tryseed = (s, stopK) => {
        if(Math.hypot(...s) > RR - .3) return;
        if(near(s[0], s[1], SP, -1) < SP * .98) return;
        const id = lines.length, l = trace(s, id, stopK);
        if(l.length < (opt.minLen || 10)) return;
        l.forEach(p => add(p, id)); lines.push(l);
      };
      /* seeds: first along a line across the ridges, then everywhere (gap filling) */
      (opt.seeds || []).forEach(s => tryseed(s, .78));
      for(let pass = 0; pass < 2; pass++) for(let y = -RR; y <= RR; y += SP * .5) for(let x = -RR; x <= RR; x += SP * .5) tryseed([x + .13, y + .07], .72);
      return lines;
    }
    const seeds = []; for(let v = -12.8; v <= 12.8; v += 1.9) seeds.push([9, v]);
    const raw = fingerprint({ R: 12.9, sp: 1.9, core: [0, -2], delta: [-10, 8], th0: -.4, seeds });
    const toT = ([x, y]) => [TC[0] - y, TC[1] + x];                       /* turned a quarter: the loop opens downward */
    const ridges = raw.map(l => lineP(S.simp(l.map(toT), .03))).join("");
    const shift = (f, dx, dy) => (x, y) => f(x - dx, y - dy);
    const shade = [0, 1, 2, 3, 4].map(k => { const f = 1 - k / 5; return ["field", all(S.minus(S.inter(cardP, S.grow(shift(token, .9 * f, 1.3 * f), .3 + 2.6 * f)), token)), { col: ["#C3D5E8", "#B6CADF", "#A9BFD6", "#9CB3CC", "#8EA6C1"][k] }]; });
    let lines = ""; [[-8, 18], [-2, 22], [4, 14], [10, 20]].forEach(([y, l]) => { lines += keep([Q(-10, y), Q(-10 + l, y)], p => cardP(...p) < -.8); });
    CHAPTER_OBJ["Identity Crimes"] = {
      d: sh(sil), col: "#CFE0F0", base: "field",
      plates: [
        ["field", sh(g(cardP)), { dome: .6 }],                                                                               /* the card */
        ["field", sh(g(band)), { z: .3, bev: .5, dome: .4, col: "#2C5D9E" }],                                               /* its header band */
        ["ink", lineP([Q(-30, -22.5), Q(4, -22.5)]), { ln: 2.6, z: .2, bev: .3, col: "#DCE8F4" }],                           /* its title */
        ["brass", sh(chip), { z: .4, bev: .4, gem: .5, gw: 1.6 }],                                                           /* the chip */
        ["brass", lineP([Q(-23.5, -8.5), Q(-23.5, 3.5)]) + lineP([Q(-30.5, -2.5), Q(-16.5, -2.5)]), { ln: .9, cut: .45, paint: 0 }],
        ["field", sh(photo), { z: -.6, bev: .5, col: "#A8C0D8" }],                                                          /* the photo window */
        ["ink", lines, { ln: 1.6, cut: .3, col: "#7E93A8" }],                                                                /* the details */
        ...shade,                                                                                                            /* the seal's soft shade on the card */
        ["steel", sh(g(token)), { z: .7, bev: .6, gem: 1.1, gw: 2.2, dome: .5, col: "#B9C3CE" }],                            /* the seal: its polished rim, chamfered */
        ["field", OBJ_circle(TC[0], TC[1], TF), { z: -.45, bev: .7, dome: .7, col: "#223B66" }],                             /* its navy face, set in */
        ["water", ridges, { ln: .95, z: .3, bev: .28, col: "#98C4EE" }],                                                   /* the print */
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
    const hollow = S.minus(S.inter(rimIn, S.ellipse(64, 37, 16.5, 30)), S.ellipse(54, 82, 10, 12));
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
    const ticket = S.minus(tk, cover);
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

  /* ---- Radio Communications, Alerts, and TCIC-TLETS - the officer's handheld radio seen from the front and a little above. (art11,
     Madison: "The older radio looked better, it just needed to be nicer, maybe with a cooler blueish LED screen.") Back to the older
     radio's shape (a0da788): the slim case with the top of it showing, the stubby ribbed antenna, the channel and volume knobs, the
     push-to-talk bar on the left side - no belt clip, no lanyard eye. Polished: the case's front edge chamfered crisp; each knob in a
     steel collar, knurled round its side, its top lighter with a pointer; the orange emergency button between antenna and knobs; the
     screen a backlit blue LCD set in a dark bezel - brightest at its middle, a cyan glow round its edge - with signal bars and a
     two-digit channel in dark segments; the speaker's horizontal slots pressed in. ---- */
  {
    const x0 = 30, x1 = 74, y0 = 30, y1 = 95, d = 3.4;
    const body = S.box(x0, y0, x1 - x0, y1 - y0, 6.5), topF = S.inter(S.box(x0, y0 - d, x1 - x0, 12, 6.5), S.box(0, 0, 100, y0 + 4, 0));
    const AX = 38, ant = S.union([S.cone(AX, 27, AX, 9.5, 3.4, 2.8), S.circle(AX, 9.3, 2.9)], .6), antC = S.union([S.box(AX - 4.3, y0 - 5.2, 8.6, 3.4, 1.2), S.ellipse(AX, y0 - 5.2, 4.3, 1.5)], 0);
    const knob = (cx, r, h) => { const yt = y0 - 2.4 - h; return { yt, side: S.box(cx - r, yt, 2 * r, h, 1), top: S.ellipse(cx, yt, r, r * .38),
      all: S.union([S.box(cx - r, yt, 2 * r, h + 1, 1), S.ellipse(cx, yt, r, r * .38)], 0), col: S.union([S.box(cx - r - .9, y0 - 3.4, 2 * r + 1.8, 2.6, 1), S.ellipse(cx, y0 - 3.4, r + .9, (r + .9) * .38)], 0) }; };
    const k1 = knob(53.5, 4.6, 10), k2 = knob(65.5, 4.1, 6.6);
    const ptt = S.box(25, 44, 7, 22, 2.5);
    const btn = S.box(42.4, y0 - 4.6, 6, 4.4, 1.8);
    const sil = S.union([body, topF, ant, antC, k1.all, k2.all, k1.col, k2.col, ptt, btn], 1);
    /* the screen: a dark bezel, the backlit glass in it, its glow */
    const BZ = [x0 + 5, y0 + 6, x1 - x0 - 10, 17], SC = [BZ[0] + 2, BZ[1] + 2, BZ[2] - 4, BZ[3] - 4];
    const scr = S.box(...SC, 1.6);
    let bars = ""; [1.8, 2.9, 4, 5.1].forEach((h, i) => { const x = SC[0] + 3.3 + i * 2.1; bars += "M" + F(x) + " " + F(SC[1] + SC[3] - 2.6) + "V" + F(SC[1] + SC[3] - 2.6 - h); });
    const seg = (x, y, on) => { const w = 3.4, h = 3.5, S7 = { a: [[0, 0], [w, 0]], b: [[w, 0], [w, h]], c: [[w, h], [w, 2 * h]], d: [[0, 2 * h], [w, 2 * h]], e: [[0, h], [0, 2 * h]], f: [[0, 0], [0, h]], g: [[0, h], [w, h]] };
      return on.split("").map(k => { const [p, q] = S7[k], s0 = .55, dx = q[0] - p[0], dy = q[1] - p[1], l = Math.hypot(dx, dy); return lineP([[x + p[0] + dx / l * s0, y + p[1] + dy / l * s0], [x + q[0] - dx / l * s0, y + q[1] - dy / l * s0]]); }).join(""); };
    const digits = seg(SC[0] + SC[2] - 11.6, SC[1] + 1.9, "bc") + seg(SC[0] + SC[2] - 6, SC[1] + 1.9, "abged");
    /* the speaker: horizontal slots pressed into a recessed panel */
    const SP = [x0 + 6, 55, x1 - x0 - 12, 33];
    let slots = ""; for(let k = 0; k < 6; k++) slots += OBJ_rrect(SP[0] + 3.2, SP[1] + 3.6 + k * 4.6, SP[2] - 6.4, 2.3, 1.1);
    let ribs = ""; for(let y = 12; y < 22; y += 2.6) ribs += "M" + F(AX - 2.6) + " " + F(y) + "H" + F(AX + 2.6);
    const kr = (k, cx, r) => { let s = ""; for(let i = -4; i <= 4; i++){ const x = cx + r * Math.sin(i / 4.6 * Math.PI / 2), dx = (x - cx) / r; s += "M" + F(x) + " " + F(k.yt + r * .38 * Math.sqrt(Math.max(0, 1 - dx * dx)) + .9) + "V" + F(y0 - 4.6); } return s; };
    const pttR = [49, 53, 57, 61].map(y => "M27 " + y + "H30.4").join("");
    CHAPTER_OBJ["Radio Communications, Alerts, and TCIC-TLETS"] = {
      d: sh(sil), col: "#33373F", base: "field",
      plates: [
        ["rubber", sh(g(S.minus(ant, antC))), { dome: 1.3, col: "#24272C" }],                                                /* the antenna */
        ["rubber", sh(g(ptt)), { z: .2, bev: .6, dome: .8, col: "#26292E" }],                                                /* the push-to-talk bar */
        ["field", sh(g(body)), { z: .45, bev: .6, gem: .5, gw: 1.6, dome: 1 }],                                             /* the case: its front, its edge chamfered */
        ["field", sh(g(topF)), { z: .55, bev: .5, dome: .4, col: "#4A4F58" }],                                               /* its top */
        ["steel", sh(g(k1.col)) + sh(g(k2.col)) + sh(g(antC)), { z: .35, bev: .4, dome: .5, col: "#8A939E" }],                             /* the knobs' collars, the antenna's */
        ["rubber", sh(g(S.minus(k1.all, k1.col))) + sh(g(S.minus(k2.all, k2.col))), { z: .3, bev: .5, dome: .9, col: "#2A2D33" }],   /* the knobs */
        ["rubber", sh(g(k1.top)) + sh(g(k2.top)), { z: .45, bev: .4, dome: .35, col: "#555B65" }],                             /* their tops */
        ["rubber", kr(k1, 53.5, 4.6) + kr(k2, 65.5, 4.1) + ribs + pttR + "M53.5 " + F(k1.yt - .9) + "V" + F(k1.yt + .9) + "M65.5 " + F(k2.yt - .8) + "V" + F(k2.yt + .8), { ln: .8, cut: .42, paint: 0 }],   /* knurling, the antenna's ribs, the bar's ridges, the knobs' pointers: grooves, one plate */
        ["hot", sh(g(btn)), { z: .55, bev: .45, dome: .9, col: "#F27B1B" }],                                                 /* the emergency button */
        ["rubber", OBJ_rrect(...BZ, 3), { z: -.15, bev: .5, dome: .2, col: "#17191D" }],                                     /* the screen's bezel */
        ["glass", sh(g(scr)), { z: -.25, bev: .45, dome: .25, col: "#3FB6FF" }],                                             /* the backlit screen */
        ...["#4DBDFF", "#5CC4FF", "#6BCBFF", "#7AD2FF", "#88D8FF"].map((c, k) => ["glass", OBJ_rrect(SC[0] + 1.2 + k * 1.15, SC[1] + .9 + k * .75, SC[2] - 2.4 - k * 2.3, SC[3] - 1.8 - k * 1.5, 1.6 - k * .15), { dome: .06, col: c }]),   /* its glow, brightest at the middle (small steps; together a faint curve of the glass) */
        ["field", all(S.minus(S.box(BZ[0] + .6, BZ[1] + .6, BZ[2] - 1.2, BZ[3] - 1.2, 2.4), S.grow(scr, .25))), { dome: .05, col: "#1E5A86" }],   /* the glow's spill on the bezel */
        ["ink", bars + digits, { ln: 1.1, z: .1, bev: .25, col: "#06304F" }],                                                /* its readout: signal bars, the channel */
        ["rubber", OBJ_rrect(...SP, 4), { z: -.35, bev: .6, dome: .3, col: "#2A2D33" }],                                    /* the speaker */
        ["rubber", slots, { z: -.5, bev: .4, col: "#111316" }],                                                              /* its slots */
      ],
    };
  }
}
