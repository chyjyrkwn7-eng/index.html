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

  /* ---- Chapter 32: High-Piled Combustible Storage - a selective pallet rack, loaded. (384.133 badgeart, Madison: "This isn't high piled
     storage, that's just a stack of boxes. Those orange and blue or orange and green metal racks are high piled storage more often than
     not." His photo: a warehouse aisle of racks with blue-green uprights and orange beams, pallets of cartons on every level.) Two bays,
     three levels: the blue end frames with their zig-zag bracing and the punched slots up their posts, the plain upright between the
     bays, the orange step beams with their end connectors, and on the floor and on each pair of beams a wooden pallet of kraft cartons.
     The space between each load and the beam over it is open (a real see-through), so it reads as a rack, not a pile; the loads fill
     their bays side to side, so the back has a band wide enough for the title. ---- */
  {
    const S = OBJ_SDF, BB = [0, 0, 100, 100];
    const UP = [[3, 16], [46.5, 53.5], [84, 97]];                       /* the uprights: two end frames, the post between the bays */
    const BAYS = [[16, 46.5], [53.5, 84]];
    const TOP = 3, FLOOR = 97;
    const BEAMS = [[62, 67], [28, 33]];                              /* beam levels: top, bottom (y) */
    const LV = [[FLOOR, 77.5], [62, 43], [28, TOP]];                       /* each level: the pallet's foot, the cartons' top */
    const PH = 5.5;                                                      /* a pallet's height */
    const parts = [];
    UP.forEach(([x0, x1]) => parts.push(S.box(x0, TOP, x1 - x0, FLOOR - TOP, 0)));
    BAYS.forEach(([x0, x1]) => BEAMS.forEach(([y0, y1]) => parts.push(S.box(x0 - 1, y0, x1 - x0 + 2, y1 - y0, 0))));
    const loads = [];
    BAYS.forEach(([x0, x1]) => LV.forEach(([foot, topY]) => {
      const pal = [x0, foot - PH, x1 - x0, PH];
      const cw = (x1 - x0) / 2, c1 = [x0, topY, cw, foot - PH - topY], c2 = [x0 + cw, topY, cw, foot - PH - topY];
      loads.push({ pal, c1, c2 });
      parts.push(S.box(pal[0], pal[1], pal[2], pal[3], 0));
      parts.push(S.box(c1[0], c1[1], 2 * cw, c1[3], 0));
    }));
    const sil = S.trace(S.grow(S.grow(S.union(parts, 0), -1.2), 1.2), BB);   /* every outer corner rounded, the inner ones left square */
    const plates = [];
    /* the uprights */
    const frame = ([x0, x1]) => OBJ_rrect(x0, TOP, x1 - x0, FLOOR - TOP, 1.2);
    plates.push(["field", UP.map(frame).join(""), { dome: .5 }]);
    /* the end frames: two posts and the bracing zig-zagging between them, the post between the bays plain */
    let brace = "", slots = "";
    [UP[0], UP[2]].forEach(([x0, x1]) => {
      const a = x0 + 2.6, b = x1 - 2.6; let y = TOP + 4, left = true; brace += "M" + a + " " + y;
      while(y + 9 <= FLOOR - 3){ y += 9; brace += "L" + (left ? b : a) + " " + y; left = !left; }
      slots += "M" + (x0 + 1.3) + " " + (TOP + 3) + "V" + (FLOOR - 3) + "M" + (x1 - 1.3) + " " + (TOP + 3) + "V" + (FLOOR - 3);
    });
    plates.push(["field", brace, { ln: 2, z: .7, bev: .6, col: "#4E8FD8" }]);
    plates.push(["field", slots, { ln: 1, cut: .5, paint: 0 }]);
    let punch = ""; for(let y = TOP + 4; y < FLOOR - 3; y += 4.5) punch += "M50 " + y.toFixed(1) + "V" + (y + 2).toFixed(1);
    plates.push(["field", punch, { ln: 1.4, cut: .6, paint: 0 }]);
    /* the beams, orange, and their connectors on the uprights */
    let beams = "", conn = "";
    BAYS.forEach(([x0, x1]) => BEAMS.forEach(([y0, y1]) => { beams += OBJ_rrect(x0 - 1, y0, x1 - x0 + 2, y1 - y0, .8);
      conn += OBJ_rrect(x0 - 1.5, y0 - 1.5, 3.4, y1 - y0 + 3, .8) + OBJ_rrect(x1 - 1.9, y0 - 1.5, 3.4, y1 - y0 + 3, .8); }));
    plates.push(["hot", beams, { z: .9, bev: .7, dome: .4, col: "#F07A1A" }]);
    plates.push(["hot", conn, { z: 1.1, bev: .5, col: "#C95F12" }]);
    /* the loads: pallets and cartons */
    let pals = "", pfork = "", cart = "", seam = "", tape = "";
    loads.forEach(({ pal, c1, c2 }) => {
      pals += OBJ_rrect(pal[0], pal[1], pal[2], pal[3], .6);
      const fw = pal[2] * .26; pfork += OBJ_rrect(pal[0] + pal[2] * .12, pal[1] + 2.6, fw, pal[3] - 2.6, [.6, .6, 0, 0]) + OBJ_rrect(pal[0] + pal[2] * .88 - fw, pal[1] + 2.6, fw, pal[3] - 2.6, [.6, .6, 0, 0]);
      const x0 = c1[0], x1 = c2[0] + c2[2], xm = (c1[0] + c1[2] + c2[0]) / 2;
      cart += OBJ_rrect(x0 + .9, c1[1], x1 - x0 - 1.8, c1[3], [1.2, 1.2, 0, 0]);
      seam += "M" + xm.toFixed(2) + " " + (c1[1] + .6) + "V" + (c1[1] + c1[3] - .3).toFixed(2);
      [c1, c2].forEach(c => { tape += "M" + (c[0] + c[2] / 2).toFixed(2) + " " + (c[1] + .2) + "V" + (c[1] + c[3] * .42).toFixed(2); });
    });
    plates.push(["wood", pals, { z: .5, bev: .5 }]);
    plates.push(["ink", pfork, { z: -.6, bev: .4, col: "#2A1D12" }]);
    plates.push(["cardboard", cart, { z: .8, bev: .8, col: "#B5814A" }]);
    plates.push(["cardboard", seam, { ln: 1.3, cut: .8, paint: 0 }]);
    plates.push(["cardboard", tape, { ln: 2, z: .25, bev: .3, col: "#8C5A2B" }]);
    CHAPTER_OBJ["Chapter 32: High-Piled Combustible Storage"] = {
      d: sil.d, holes: sil.holes,
      col: "#2F6FB8", base: "field",
      plates,
    };
  }

  /* ---- Chapter 33: Fire Safety During Construction and Demolition - a hard hat, side on, facing left. (384.133 badgeart, Madison: "I
     don't like the hat at all. Make this better." The round-9 hat was a yellow bell, front on, with a short brim: a bowler.) Now a real
     cap-style hard hat: the high domed shell with its raised crown ridge and the two ribs running front to back, the bill at the front
     reaching out and down, the full brim round the back, the suspension's headband showing under the brim, and a small gold star decal.
     NAVY, by Madison's standing rule for this class: "If there is going to be any hard hats ... they will be navy blue" (r6; every hard
     hat, helmet and cap the agency's people wear is navy). ---- */
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
    const star = (cx, cy, R) => OBJ_poly([...Array(10)].map((_, i) => { const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? R * .45 : R; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; }), .5);
    CHAPTER_OBJ["Chapter 33: Fire Safety During Construction and Demolition"] = {
      d: S.shape(all, BB),
      col: "#24407A", base: "field",
      plates: [
        ["rubber", S.shape(band, BB), { z: -.5, bev: .6, col: "#161B27" }],                              /* the headband */
        ["field", S.shape(S.inter(shell, S.box(0, 0, 100, 74, 0)), BB), { dome: 2.6 }],                 /* the shell */
        ["field", ell(.86, .9, 212, 328), { ln: 6, z: .9, bev: 1.3 }],                                   /* the crown ridge */
        ["field", ell(.92, .64, 197, 343), { ln: 2.6, z: .6, bev: .8 }],                                 /* the side rib, front to back */
        ["field", S.shape(brim, BB), { z: .5, bev: .8, dome: .5 }],                                      /* the brim and the bill */
        ["shade", "M7 86.4Q13 83.4 24 82H86", { ln: 2.2, z: .2, bev: .5 }],                             /* the brim's underside */
        ["brass", star(43, 59, 5.6), { z: .5, bev: .4, col: "#E2B640" }],                              /* the gold star decal */
      ],
    };
  }

  /* ---- Chapter 34: Tire Rebuilding and Tire Storage - a stack of three tyres seen from the side, the top one's sidewall and its hole seen
     from above. (384.133 badgeart, Madison: "The lines on the tires are messed up and come off the tires." The round-9 tread grooves ran
     the full width of a square block, over the tyres' rounded shoulders, across the seams between them and up into the top tyre's
     sidewall.) Each tyre is now its own rounded band - a tyre's shoulder is round, so its ends are half-round - and its tread is cut only
     inside its own band: two rows of slanted blocks either side of a centre groove, every groove clipped to the band's flat tread, clear
     of its shoulders, its neighbours and the sidewall above. The three are staggered as tyres are when they are stacked by hand (the
     straight-sided stack was 0.89-0.96 alike, by outline, to Chapter 50's diamond turned on its side). ---- */
  {
    const S = OBJ_SDF, BB = [0, 0, 100, 100];
    const T = [[9, 85, 74, 96], [15, 93, 52, 74], [6, 84, 30, 52]];            /* each tyre: x0, x1, y0, y1 (bottom, middle, top) */
    const R = 10.5;
    const bands = T.map(([x0, x1, y0, y1]) => S.box(x0, y0, x1 - x0, y1 - y0, R));
    const tc = T[2], TX = (tc[0] + tc[1]) / 2, TY = tc[2], TRX = (tc[1] - tc[0]) / 2 - 1, TRY = 9;
    const top = S.ellipse(TX, TY, TRX, TRY);
    const all = S.union(bands.concat([top]), .6);
    /* a segment clipped to the box [x0, x1] x [y0, y1] (Liang-Barsky) */
    const clip = (a, b, x0, x1, y0, y1) => { let t0 = 0, t1 = 1; const dx = b[0] - a[0], dy = b[1] - a[1];
      for(const [p, q] of [[-dx, a[0] - x0], [dx, x1 - a[0]], [-dy, a[1] - y0], [dy, y1 - a[1]]]){
        if(p === 0){ if(q < 0) return null; continue; } const r = q / p; if(p < 0){ if(r > t1) return null; if(r > t0) t0 = r; } else { if(r < t0) return null; if(r < t1) t1 = r; } }
      return t1 - t0 > .08 ? [[a[0] + dx * t0, a[1] + dy * t0], [a[0] + dx * t1, a[1] + dy * t1]] : null; };
    const seg = q => q ? "M" + q[0][0].toFixed(2) + " " + q[0][1].toFixed(2) + "L" + q[1][0].toFixed(2) + " " + q[1][1].toFixed(2) : "";
    let tread = "", grooves = "";
    T.forEach(([x0, x1, y0, y1], k) => {
      const fx0 = x0 + R + .5, fx1 = x1 - R - .5;                               /* the flat of the tread, clear of the round shoulders */
      const yA = k === 2 ? TY + TRY + 2.2 : y0 + 3.2, yB = y1 - 3.2, ym = (yA + yB) / 2;
      if(k !== 2) grooves += "M" + fx0.toFixed(2) + " " + ym.toFixed(2) + "H" + fx1.toFixed(2);
      for(let x = fx0 - 6; x <= fx1 + 6; x += 6.4){
        if(k === 2){ tread += seg(clip([x, yB], [x + 3.2, yA], fx0, fx1, yA, yB)); continue; }
        tread += seg(clip([x, ym - 1.4], [x + 2.6, yA], fx0, fx1, yA, ym - 1.4));
        tread += seg(clip([x + 2.6, yB], [x, ym + 1.4], fx0, fx1, ym + 1.4, yB));
      }
    });
    CHAPTER_OBJ["Chapter 34: Tire Rebuilding and Tire Storage"] = {
      d: S.shape(all, BB),
      base: "rubber", col: "#34373C",
      plates: [
        ["rubber", S.shape(bands[0], BB), { dome: 1.1 }],                                               /* the bottom tyre */
        ["rubber", S.shape(bands[1], BB), { dome: 1.1 }],                                               /* the middle one, on it */
        ["rubber", S.shape(bands[2], BB), { dome: 1.1 }],                                               /* the top one */
        ["rubber", tread, { ln: 1.5, cut: .8, paint: 0 }],                                              /* the tread blocks, each in its own band */
        ["rubber", grooves, { ln: 1.3, cut: .7, paint: 0 }],                                            /* the centre grooves */
        ["field", OBJ_ellipse(TX, TY, TRX, TRY), { z: .4, bev: .8, dome: .7, col: "#4A4E55" }],          /* the top tyre's sidewall */
        ["steel", OBJ_ellipse(TX, TY, TRX * .56, TRY * .52), { z: .2, bev: .5, dome: .3, col: "#5A5F68" }],   /* its bead */
        ["ink", OBJ_ellipse(TX, TY, TRX * .47, TRY * .4), { z: -1.8, bev: .8, col: "#16181B" }],        /* the hole in the middle */
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
