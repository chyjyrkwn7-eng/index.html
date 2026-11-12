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

  /* ---- Chapter 32: High-Piled Combustible Storage - kraft cartons stacked three, two, one on a wooden pallet: every carton a raised block
     with its tape strip, the pallet's deck and its three blocks with the fork openings between them. ---- */
  {
    const boxes = [[6, 56, 29.33], [35.33, 56, 29.34], [64.67, 56, 29.33], [20.67, 31, 29.33], [50, 31, 29.33], [35.33, 6, 29.34]];
    const plates = [];
    boxes.forEach(([x, y, w]) => plates.push(["brass", OBJ_rrect(x + .6, y + .6, w - 1.2, 23.8, 1.6), { z: .8, bev: .9 }]));
    boxes.forEach(([x, y, w]) => plates.push(["cream", OBJ_rrect(x + w / 2 - 3, y + .6, 6, 11, [0, 0, 1.5, 1.5]), { z: 1.2, bev: .5 }]));
    plates.push(["wood", OBJ_rrect(3, 81, 94, 7, 2), { z: .5, bev: .7 }]);
    plates.push(["wood", "M18 82V87M33 82V87M50 82V87M67 82V87M82 82V87", { ln: 1.4, cut: .7, paint: 0 }]);
    [[3, 12], [43, 14], [85, 12]].forEach(([x, w]) => plates.push(["wood", OBJ_rrect(x, 88, w, 8, [0, 0, 2, 2]), { z: .2, bev: .6 }]));
    CHAPTER_OBJ["Chapter 32: High-Piled Combustible Storage"] = {
      d: OBJ_poly([[35.33, 6], [64.67, 6], [64.67, 31], [79.33, 31], [79.33, 56], [94, 56], [94, 81], [97, 81], [97, 96], [85, 96], [85, 88], [57, 88], [57, 96],
        [43, 96], [43, 88], [15, 88], [15, 96], [3, 96], [3, 81], [6, 81], [6, 56], [20.67, 56], [20.67, 31], [35.33, 31]],
        [2, 2, 1, 2, 1, 2, 1, 1.5, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2, 1.5, 1, 2, 1, 2, 1]),
      base: "deep",
      plates,
    };
  }

  /* ---- Chapter 33: Fire Safety During Construction and Demolition - a safety-orange hard hat, front on: the domed shell with its raised
     centre ridge and two side ribs, the brim curving down at the front. (No base colour of its own: the parts are what colour it.) ---- */
  {
    const brim = "M7 68H93Q97 68 97 72Q97 76 93 77Q50 89 7 77Q3 76 3 72Q3 68 7 68Z";
    CHAPTER_OBJ["Chapter 33: Fire Safety During Construction and Demolition"] = {
      d: "M7 68H13A37 52 0 0 1 87 68" + brim.slice(brim.indexOf("H93")),
      plates: [
        ["hot", "M13 68A37 52 0 0 1 87 68Z", { dome: 2.8 }],                                      /* the shell */
        ["hot", "M50 21V65", { ln: 11, z: 1, bev: 1.6 }],                                          /* the centre ridge */
        ["hot", "M30 27Q20 44 20 66M70 27Q80 44 80 66", { ln: 2, cut: 1.1, paint: 0 }],           /* the side ribs */
        ["hot", brim, { z: .5, bev: .8, dome: .5 }],                                              /* the brim */
      ],
    };
  }

  /* ---- Chapter 34: Tire Rebuilding and Tire Storage - a tyre: the deep rubber tread blocks round its edge, the domed slate-grey
     sidewall with its ring, the steel wheel set into it, the hub and five lug nuts. ---- */
  {
    const runs = [], Ro = 47, Ri = 42;
    for(let i = 0; i < 24; i++){ const a = -90 + i * 15, p = (r, t) => [50 + r * Math.cos(t * D2R), 50 + r * Math.sin(t * D2R)];
      runs.push([[p(Ro, a - 4.2)], 1.2], [[p(Ro, a + 4.2)], 1.2], [[p(Ri, a + 4.2)], .8], [[p(Ri, a + 10.8)], .8]); }
    const plates = [
      ["rubber", OBJ_circle(50, 50, 42.5), { z: .1 }],                                                /* the tread's floor */
      ["field", OBJ_circle(50, 50, 39), { dome: 1.6 }],                                              /* the sidewall */
      ["field", OBJ_circle(50, 50, 32), { ln: 1.4, cut: .7, paint: 0 }],                              /* its ring */
      ["steel", OBJ_circle(50, 50, 23), { z: -.7, bev: 1.2 }],                                        /* the wheel, set in */
      ["steel", OBJ_circle(50, 50, 18.5), { ln: 1.4, cut: .7, paint: 0 }],                            /* its rim */
      ["steel", OBJ_circle(50, 50, 8.5), { dome: 2.2 }],                                               /* the hub */
    ];
    for(let i = 0; i < 5; i++){ const a = (-90 + i * 72) * D2R; plates.push(["steel", OBJ_circle(50 + 14 * Math.cos(a), 50 + 14 * Math.sin(a), 2.8), { dome: 1.2 }]); }
    CHAPTER_OBJ["Chapter 34: Tire Rebuilding and Tire Storage"] = { d: P3poly(runs), base: "rubber", plates };
  }

  /* ---- Chapter 35: Welding and Other Hot Work - a red welding helmet, front on: the shell narrowing to a faceted chin, the raised black
     lens holder with its dark lens pressed in, the headgear knobs at either side. ---- */
  {
    const knob = (cx, a0, a1) => P3arc(cx, 47, 6.5, 6.5, a0, a1, 8);
    const d = P3poly([[P3arc(50, 36, 30.5, 31, 180, 360, 6), 0], [knob(85.5, -140.3, 140.3), 0], [[[80.5, 62]], 5], [[[62, 93]], 4], [[[38, 93]], 4],
      [[[19.5, 62]], 5], [knob(14.5, 39.7, 320.3), 0]]);
    CHAPTER_OBJ["Chapter 35: Welding and Other Hot Work"] = {
      d,
      base: "red",
      plates: [
        ["red", OBJ_poly([[19.5, 58], [80.5, 58], [62, 93], [38, 93]], [0, 0, 4, 4]), { gem: 1.4, gw: 9 }],   /* the chin, faceted */
        ["rubber", OBJ_rrect(27, 27, 46, 25, 3.5), { z: 1, bev: .9 }],                                     /* the lens holder */
        ["ink", OBJ_rrect(32, 32, 36, 15, 1.5), { z: -1.1, bev: .6 }],                                    /* the lens */
        ["red", "M50 10V24", { ln: 6, z: .6, bev: 1 }],                                                 /* the crown ridge */
        ["rubber", OBJ_circle(85.5, 47, 6.5), { dome: 1.6 }],                                               /* the headgear knobs */
        ["rubber", OBJ_circle(14.5, 47, 6.5), { dome: 1.6 }],
        ["steel", OBJ_circle(85.5, 47, 2.6), { dome: .9 }],
        ["steel", OBJ_circle(14.5, 47, 2.6), { dome: .9 }],
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
    const strands = (a, offs, bow) => { let s = ""; const u = [Math.cos(a * D2R), Math.sin(a * D2R)], v = [-u[1], u[0]];
      offs.forEach(o => { const h = Math.sqrt(Math.max(0, (R - 3) * (R - 3) - o * o)), m = [C[0] + v[0] * o, C[1] + v[1] * o];
        const p0 = [m[0] - u[0] * h, m[1] - u[1] * h], p1 = [m[0] + u[0] * h, m[1] + u[1] * h], c = [m[0] + v[0] * bow * (1 - Math.abs(o) / R), m[1] + v[1] * bow * (1 - Math.abs(o) / R)];
        s += "M" + P3f(p0) + "Q" + P3f(c) + " " + P3f(p1); }); return s; };
    const band = (() => { const a = 125 * D2R, u = [Math.cos(a), Math.sin(a)], v = [-u[1], u[0]], h = R + 2, w = 9;
      return OBJ_poly([[C[0] - u[0] * h - v[0] * w, C[1] - u[1] * h - v[1] * w], [C[0] + u[0] * h - v[0] * w, C[1] + u[1] * h - v[1] * w],
        [C[0] + u[0] * h + v[0] * w, C[1] + u[1] * h + v[1] * w], [C[0] - u[0] * h + v[0] * w, C[1] - u[1] * h + v[1] * w]], 2); })();
    CHAPTER_OBJ["Chapter 37: Combustible Fibers"] = {
      d,
      plates: [
        ["body", OBJ_circle(C[0], C[1], R), { dome: 2.4 }],                                          /* the ball */
        ["body", strands(35, [-30, -21, -12, -3, 6, 15, 24, 32], 5), { ln: 2, cut: 1.3, paint: 0 }],   /* its wound strands */
        ["lite", band, { z: .9, bev: 1, dome: .8 }],                                                 /* the over-wrap band */
        ["lite", strands(125, [-5, 0, 5], 3), { ln: 1.5, cut: 1, paint: 0 }],                      /* its strands */
        ["shade", "M" + line.slice(2).map(P3f).join("L"), { ln: hw * 2, z: .3, bev: 1 }],           /* the loose end */
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
        ["deep", OBJ_rrect(4, 86, 92, 9, 2), { z: .5, bev: .6 }],                                       /* the skid */
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
    let staves = ""; [-.62, -.22, .22, .62].forEach(f => { staves += "M" + (L + 1) + " " + OBJ_N(44 + f * 22) + "Q" + M + " " + OBJ_N(44 + f * 36) + " " + (Rt - 1) + " " + OBJ_N(44 + f * 22); });
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
