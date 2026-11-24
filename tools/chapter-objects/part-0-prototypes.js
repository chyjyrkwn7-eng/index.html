/* Fire Code chapter objects - PROTOTYPES, round 3 (build 384.66): eight chapters drawn as RAISED PINS. Madison, of round 2: "the badges
   don't look good ... We may just have to go away with the silver border entirely or make it thin ... you can see how these badges have
   risen effect, that nice 3d effect ... Make this great." Each entry is the pin's silhouette and its parts; a part carries a colour and its
   relief: raised or recessed (z, bev), domed (dome), cut into facets (gem, gw) or a V-groove (cut, with ln). Identity is the silhouette and
   the sculpture, never a sticker; every pin has to read in plain grey too. See tools/chapter-objects/README.md. */

/* ---- Chapter 10: Means of Egress - an open door under a lit EXIT sign (384.79, redrawn: Madison, "the door is open but the frame is
   weird ... something is off", and of the sign, "have it say EXIT with a glow or highlight look"). It was: the leaf's HINGE edge was its
   tallest edge (so it read as swinging away and toward at once), the leaf hung off the frame's outer edge rather than its jamb, and the frame
   was a slab with a hole. Now: a steel frame with even jambs and head (6 each) round a clean dark opening with daylight on its floor; the
   leaf hinged on the LEFT jamb's inner edge and swung open toward you, so its FREE edge - nearer you - is the taller one (the hinge edge is
   exactly the opening's height); its thickness on the free edge, the knob near it, the hinges on the hinge edge. The EXIT sign sits on the
   head, centred over the opening: a steel housing, a dark face, the diffuser's green glow inside it, and the four letters raised and lit -
   the one place a front carries words (at 44px and 26px they become a glowing green bar, as a real sign does at a distance). ---- */
{
  const lerp = (a, b, t) => a + (b - a) * t;
  /* u: 0 at the free edge (x 12), 1 at the hinge (x 50, the left jamb's inner edge); v: 0 top, 1 bottom */
  const leaf = (u, v) => [lerp(12, 50, u), lerp(lerp(12, 20, u), lerp(99, 94, u), v)];
  const quad = (u0, u1, v0, v1, r) => OBJ_poly([leaf(u0, v0), leaf(u1, v0), leaf(u1, v1), leaf(u0, v1)], r);
  const yTop = x => lerp(12, 20, (x - 12) / 38);
  /* E X I T: strokes 1.5 wide, 6.2 tall, centred on the sign (x 67) */
  const L = 55.75, T = 4.15, B = 10.35, M = 7.25, sw = 4.2, xw = 4.8, g = 2.9;
  const xE = L, xX = xE + sw + g, xI = xX + xw + g, xT = xI + g;
  const exit = "M" + (xE + sw) + " " + T + "H" + xE + "V" + B + "H" + (xE + sw) + "M" + xE + " " + M + "H" + (xE + sw * .85) +
               "M" + xX + " " + T + "L" + (xX + xw) + " " + B + "M" + (xX + xw) + " " + T + "L" + xX + " " + B +
               "M" + xI + " " + T + "V" + B +
               "M" + xT + " " + T + "H" + (xT + xw) + "M" + (xT + xw / 2) + " " + T + "V" + B;
  CHAPTER_OBJ["Chapter 10: Means of Egress"] = {
    col: "#2F9A5A",   /* a green door in a hollow-metal steel frame */
    d: OBJ_poly([[12, 12], [44, yTop(44)], [44, 14], [47, 14], [47, 0], [87, 0], [87, 14], [90, 14], [90, 94], [50, 94], [12, 99]],
      [2.5, 0, .5, .5, 2.5, 2.5, .5, 1.5, 1.5, 0, 2.5]),
    plates: [
      ["steel", OBJ_rrect(44, 14, 46, 80, [1.5, 1.5, 0, 0]), { z: .5, bev: .6 }],                    /* the frame: jambs and head, 6 each */
      ["ink", OBJ_rrect(49, 20, 35, 74, [1, 1, 0, 0]), { z: -2.3, bev: .8 }],                          /* the opening, a clean dark recess (on under the leaf: 384.90) */
      ["glow", OBJ_poly([[49, 94], [49, 83.2], [84, 76], [84, 94]], [0, 1, 1, 0]), { z: -2.3, bev: .8, col: "#BFE6CB" }],   /* daylight on its floor */
      ["steel", OBJ_rrect(47, 0, 40, 14.5, 2.5), { z: .5, bev: .5 }],                                /* the sign's housing, on the head */
      ["ink", OBJ_rrect(49.5, 2.2, 35, 10.1, 1.6), { z: -.6, bev: .4, col: "#0E2A1A" }],             /* its dark face */
      ["glow", OBJ_rrect(51, 3.3, 32, 7.9, 1.4), { z: .25, bev: .6, col: "#2C9A5C" }],               /* the diffuser's glow */
      ["glow", exit, { ln: 1.5, z: .8, bev: .35, col: "#D9FFE6" }],                                  /* E X I T, raised and lit */
      ["body", OBJ_poly([leaf(0, 0), leaf(1, 0), leaf(1, 1), leaf(0, 1)], [1.5, .5, .5, 1.5]), { z: 1.6, bev: 1.2 }],   /* the leaf, swung toward you */
      ["deep", quad(0, .07, 0, 1, .6), { z: 1.6, bev: .5 }],                                          /* its thickness, on the free edge */
      ["lite", quad(.2, .84, .07, .45, 1.5), { z: .8, bev: .8 }],                                     /* its upper panel */
      ["lite", quad(.2, .84, .55, .93, 1.5), { z: .8, bev: .8 }],                                     /* its lower panel */
      ["brass", OBJ_circle(leaf(.13, .52)[0], leaf(.13, .52)[1], 3), { dome: 2 }],                   /* the knob, near the free edge */
      ["brass", quad(.93, 1, .12, .2, .5), { z: .6, bev: .4 }],                                       /* the hinges, on the hinge edge */
      ["brass", quad(.93, 1, .8, .88, .5), { z: .6, bev: .4 }],
    ],
  };
}

/* ---- Chapter 9: Fire Protection and Life Safety Systems - a sprinkler head going off, redrawn (384.93 r9: Madison, "Chapter 9, update" -
   with its deflector a broad disc seen from above, the brass head read as a goblet or a lamp): the brass head upright - the threaded
   nipple, the hex body, the two frame arms holding the red glass bulb, the boss and the toothed deflector seen edge on - hanging from
   the red sprinkler main across the top, with the water it throws: five jets fanning out of the deflector, widening as they go. ---- */
{
  /* (384.133 badgeart) the main is a big pipe now, 25 across, and the head under it is the same drawing drawn 0.86 as tall: on the main's
     broad run the back has a band wide enough for the chapter's title and its class line (the old 10-unit main left the title 8.2px in
     your hand, under the 9.2 every back is held to, and no room for FIRE CODE). */
  const S = OBJ_SDF, BB = [0, 0, 100, 100], ALL = f => S.loops(f, BB).map(S.pathOf).join("");
  const K = .86, Y = y => 27 + (y - 14) * K, Hh = h => h * K;
  const pipe = S.box(2, 1.5, 96, 25.5, 8), tee = S.box(34, 0, 32, 29, 3.5);
  const nipple = S.box(42, Y(14), 16, Hh(5) + .6, 1), hex = S.poly([[34, Y(18)], [66, Y(18)], [70, Y(23)], [66, Y(28)], [34, Y(28)], [30, Y(23)]]);
  const arms = S.union([S.capsule(35.5, Y(27), 43.5, Y(46), 3), S.capsule(64.5, Y(27), 56.5, Y(46), 3)], 0);
  const boss = S.box(42, Y(43), 16, Hh(6), 2), defl = S.box(24, Y(48), 52, Hh(6) + .4, 2);
  const J = [[32, 53, 7, 76], [41, 53, 25, 88], [50, 53, 50, 94], [59, 53, 75, 88], [68, 53, 93, 76]].map(([a, b, c, d]) => [a, Y(b), c, Math.min(97, Y(d))]);
  const jets = S.union(J.map(([a, b, c, d]) => S.cone(a, b, c, d, 1.9, 3.9)), 2);
  const bulb = S.ellipse(50, Y(36.5), 3.4, Hh(8)), head = S.union([nipple, hex, arms, bulb, boss, defl], 1.2);
  const sil = S.trace(S.union([pipe, tee, head, jets], 1.5), BB);
  let teeth = ""; [30, 38, 46, 54, 62, 70].forEach(x => { teeth += "M" + x + " " + Y(49).toFixed(2) + "V" + Y(53).toFixed(2); });
  CHAPTER_OBJ["Chapter 9: Fire Protection and Life Safety Systems"] = {
    d: sil.d, holes: sil.holes,
    base: "brass", col: "#C9972F",
    plates: [
      ["red", S.shape(pipe, BB), { dome: 1.6 }],                                                          /* the sprinkler main */
      ["red", "M9 6H31M69 6H91M9 22.5H31M69 22.5H91", { ln: 1.2, cut: .5, paint: 0 }],                                      /* its seams */
      ["red", S.shape(tee, BB), { z: .6, bev: .6, dome: .6, col: "#B52A22" }],                             /* its tee */
      /* (art9) Madison: "There's a lot of spots all over that just don't look right ... we want perfection." Every part used to be
         drawn whole and the one painted over it covered only its colour: its relief still showed through - the five jets' round tops
         as bumps along the deflector, the frame's capsule ends as blobs on the hex and the boss, the bulb's foot on the boss. Each
         part now stops where the part in front of it starts (a crease where they meet). */
      ["water", ALL(S.minus(jets, defl)), { dome: 1.4 }],                                         /* the jets, from under the deflector */
      ["brass", S.shape(S.minus(nipple, hex), BB), { z: .4 }],                                            /* the nipple */
      ["brass", S.shape(hex, BB), { gem: 1.4, gw: 3 }],                                                   /* the hex body */
      ["brass", ALL(S.minus(arms, S.union([hex, boss], 0))), { dome: 1 }],                                /* the frame */
      ["red", S.shape(S.minus(bulb, boss), BB), { dome: 2.2 }],                                           /* the glass bulb */
      ["brass", S.shape(S.minus(boss, defl), BB), { dome: 1 }],                                           /* the boss */
      ["brass", S.shape(defl, BB), { z: .6, bev: .6 }],                                                   /* the deflector */
      ["brass", teeth, { ln: 1.3, cut: .7, paint: 0 }],                                                   /* its teeth */
    ],
  };
}

/* ---- Chapter 57: Flammable and Combustible Liquids - a gas can in classic jerry-can red: the carry handle with a real hole, the panel
   pressed into its side with the embossed X, and the spout. (384.133 badgeart, Madison: "The gas can, the black part needs to connect
   well to the actual canister. Make that great." The black spout stood on the can's top edge with nothing under it, so it floated.) The
   spout now screws onto a NECK: a raised red boss moulded into the can's shoulder, the black threaded collar seated on it, square to the
   spout, with its grip ridges, and the spout running out of the collar to its amber cap. The silhouette is one filleted union, so the
   neck grows out of the can's top. ---- */
/* (art10) Madison circled where the collar met the can: a notched, stepped corner. The spout leant out of a square boss on the flat
   top, so the collar's corner hung over the can's edge on one side and the outline stepped round it. Now the can's top-right corner
   is a SHOULDER sloped square to the spout (as a plastic fuel can's is), and everything stands square on it along one axis: the red
   threaded neck moulded out of the shoulder (filleted into it both sides), the black collar screwed down onto it - a raised ring at
   its foot and its grip ridges above - with a thin shadow on the neck under the ring, then the spout and the amber cap with its ring.
   Each part starts where the one under it stops (nothing drawn under another to show through). */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const th = 55 * Math.PI / 180, u = [Math.cos(th), -Math.sin(th)], n = [-u[1], u[0]];   /* the spout's axis (up and right) and across it */
  const M = [77, 36.5];                                                          /* the neck's foot, on the shoulder */
  const tt = (x, y) => (x - M[0]) * u[0] + (y - M[1]) * u[1], ww = (x, y) => (x - M[0]) * n[0] + (y - M[1]) * n[1];
  const Q = (t, w) => [M[0] + u[0] * t + n[0] * w, M[1] + u[1] * t + n[1] * w];
  const quad = (t0, t1, w) => [Q(t0, -w), Q(t1, -w), Q(t1, w), Q(t0, w)];
  const slab = (t0, t1, w) => (x, y) => Math.max(t0 - tt(x, y), tt(x, y) - t1, Math.abs(ww(x, y)) - w);
  const T1 = 4.6, T2 = 6.3, T3 = 11.6, T4 = 21.2, T5 = 27;                   /* neck | ring | grip | spout | cap */
  const body = S.grow(S.grow(S.inter(S.box(5, 31, 80, 63, 5.5), tt), -1.5), 1.5);   /* the can, its top-right corner a shoulder square to the spout */
  const handle = S.box(10, 10, 39, 24, 4);
  const neck = S.poly(quad(-3, T1, 5.4)), ring = S.poly([Q(T1, -6), Q(T1 + .8, -7.3), Q(T2 - .5, -7.3), Q(T2, -6.8), Q(T2, 6.8), Q(T2 - .5, 7.3), Q(T1 + .8, 7.3), Q(T1, 6)]);   /* chamfered onto the neck below and into the collar above (a square step read as a notch) */
  const spout = S.poly(quad(T3 - .5, T4 + .5, 5)), cap = S.poly(quad(T4, T5, 7));
  const grip = S.poly([Q(T2, -6.8), Q(T3 - 1.4, -6.8), Q(T3 + .2, -5), Q(T3 + .2, 5), Q(T3 - 1.4, 6.8), Q(T2, 6.8)]);   /* the collar's top chamfered into the spout (a square step read as a notch) */
  const can = S.union([body, handle], 1.6);
  const solid = S.union([S.union([can, neck], 1.8), S.grow(S.grow(S.union([ring, grip, spout, cap], .7), -.9), .9)], .7);
  const all = S.minus(solid, S.box(17, 16, 25, 9, 3.5)), sil = S.trace(all, BB);
  const part = (t0, t1, w) => S.shape(S.inter(all, slab(t0, t1, w)), BB);
  const f = p => p[0].toFixed(2) + " " + p[1].toFixed(2), line = (t, w) => "M" + f(Q(t, -w)) + "L" + f(Q(t, w));
  const ridges = [-4.8, -1.6, 1.6, 4.8].map(w => "M" + f(Q(T2 + .9, w)) + "L" + f(Q(T3 - .9, w))).join("");
  CHAPTER_OBJ["Chapter 57: Flammable and Combustible Liquids"] = {
    d: sil.d, holes: sil.holes,
    base: "red",
    plates: [
      ["red", S.shape(body, BB)],                                                               /* the can */
      ["red", OBJ_rrect(12, 40, 64, 46, 4), { z: -.9, bev: 1 }],                                /* the panel pressed into its side */
      ["red", "M18 46L70 80M70 46L18 80", { ln: 6, z: 1.4, bev: 1.4 }],                         /* the embossed X */
      ["red", OBJ_rrect(10, 10, 39, 24, 4), { z: .3, bev: .8 }],                                /* the handle */
      ["red", part(0, T1, 9), { z: .45, bev: .8, dome: .4 }],                                   /* the threaded neck, moulded out of the shoulder */
      ["red", line(1.5, 4.6) + line(2.9, 4.8), { ln: .8, cut: .5, paint: 0 }],                /* its threads */
      ["ink", OBJ_poly(quad(T1 - 1.1, T1, 6), 0), { col: "#4A100E" }],                       /* the collar's shadow on it */
      ["rubber", part(T1, T4 + 1, 9.5)],                                                          /* (the black under the collar and spout, to their fillets' last corner) */
      ["rubber", part(T1, T2, 9), { z: .95, bev: .5, dome: .3 }],                               /* the collar's ring, seated on the neck */
      ["rubber", part(T2, T3, 9), { z: .75, bev: .6, dome: .5 }],                               /* the collar */
      ["rubber", ridges, { ln: 1.1, cut: .55, paint: 0 }],                                       /* its grip ridges */
      ["rubber", part(T3, T4, 9), { z: .35, dome: .8 }],                                         /* the spout */
      ["hot", part(T4, 40, 9), { dome: 1.3 }],                                                    /* the cap */
      ["hot", line(T4 + 1.6, 6.1), { ln: .8, cut: .45, paint: 0 }],                              /* its ring */
    ],
  };
}

/* ---- Appendix D: Fire Apparatus Access Roads - a fire engine, side on, facing left: the cab with its windscreen and light bar, the
   chrome ladder along the roof, the lockers, the red stripe, two big wheels. The widest, lowest pin. ---- */
{
  let rungs = ""; for(let x = 28; x <= 92; x += 8) rungs += "M" + x + " 25V31";
  CHAPTER_OBJ["Appendix D: Fire Apparatus Access Roads"] = {
    col: "#C8302B",   /* (384.67) natural colours: a red engine, a white stripe, an amber light bar */
    d: "M14 74" + OBJ_chain([[14, 74], [6, 74], [6, 58], [12, 46], [13, 41], [27, 41], [28, 46], [31, 46], [31, 33], [22, 33], [22, 23], [96, 23], [96, 74], [88, 74]], [0, 3, 4, 3, 1.5, 1.5, 1, 1, 1, 2, 2, 2, 3, 0]) +
       "A12 12 0 0 1 64 74" + OBJ_chain([[64, 74], [38, 74]], 0) + "A12 12 0 0 1 14 74Z",
    plates: [
      ["steel", OBJ_rrect(22, 23, 74, 10, 2), { z: .8, bev: .6 }],                              /* the ladder */
      ["steel", rungs, { ln: 1.4, cut: .8, paint: 0 }],                                         /* its rungs */
      /* (art9) the stripe stops at the wheel wells: run on under them, its edges showed through the wells and tyres as steps */
      ["cream", OBJ_SDF.loops(OBJ_SDF.minus(OBJ_SDF.box(6, 58, 90, 6, 0), OBJ_SDF.union([OBJ_SDF.circle(26, 74, 13.8), OBJ_SDF.circle(76, 74, 13.8)], 0)), [0, 0, 100, 100]).map(OBJ_SDF.pathOf).join(""), { z: .4, bev: .5 }],   /* the stripe */
      ["glass", OBJ_poly([[8, 56], [13, 47], [27, 47], [27, 56]], 1.5), { z: -.8, bev: .6 }],   /* the windscreen */
      ["hot", OBJ_rrect(13, 41, 14, 5, 2), { dome: 1.4 }],                                       /* the light bar */
      ["body", OBJ_rrect(35, 37, 18, 18, 1.5), { z: .7, bev: .6 }],                              /* the lockers */
      ["body", OBJ_rrect(56, 37, 18, 18, 1.5), { z: .7, bev: .6 }],
      ["body", OBJ_rrect(77, 37, 16, 18, 1.5), { z: .7, bev: .6 }],
      ["ink", OBJ_circle(26, 74, 13.8), { z: -.5, bev: .5 }],                                    /* the wheel wells (384.90) */
      ["ink", OBJ_circle(76, 74, 13.8), { z: -.5, bev: .5 }],
      ["rubber", OBJ_circle(26, 74, 12), { z: .9, bev: 1.2 }],                                   /* the wheels */
      ["rubber", OBJ_circle(76, 74, 12), { z: .9, bev: 1.2 }],
      ["steel", OBJ_circle(26, 74, 5.5), { dome: 1.6 }],                                         /* their hubs */
      ["steel", OBJ_circle(76, 74, 5.5), { dome: 1.6 }],
    ],
  };
}

/* ---- Chapter 53: Compressed Gases - an industrial gas cylinder: straight sides, a rounded shoulder, the brass collar ring and the steel
   valve-protection cap open at the front on the brass valve, a cream label band, a dark foot ring. The tallest, narrowest pin. (It read as a
   bottle with a tapered neck and a soap pump with a side outlet: both dropped. Chapter 61's squat propane tank is another chapter's.) ---- */
{
  const arc = (cx, cy, rx, ry, a0, a1, n) => { const o = []; for(let k = 0; k <= n; k++){ const t = (a0 + (a1 - a0) * k / n) * Math.PI / 180; o.push([cx + rx * Math.cos(t), cy + ry * Math.sin(t)]); } return o; };
  const right = arc(57, 33, 12, 14, 270, 360, 6), left = arc(43, 33, 12, 14, 180, 270, 6);
  const pts = [[38, 15], [38, 8], [42, 3], [58, 3], [62, 8], [62, 15], [58, 15], [58, 19]].concat(right.slice(1)).concat([[69, 92], [31, 92]]).concat(left).concat([[42, 19], [42, 15]]);
  const rs = [1, 3, 3, 3, 3, 1, 1, 1].concat(right.slice(1).map(() => 0)).concat([4, 4]).concat(left.map(() => 0)).concat([1, 1]);
  CHAPTER_OBJ["Chapter 53: Compressed Gases"] = {
    col: "#3F8A3C",   /* (384.67) natural colours: a green industrial cylinder */
    d: OBJ_poly(pts, rs),
    plates: [
      ["steel", OBJ_rrect(38, 3, 24, 12, [4, 4, 1, 1]), { dome: .8 }],                          /* the valve-protection cap */
      ["ink", OBJ_rrect(43, 5.5, 14, 7.5, 2), { z: -1.3, bev: .6 }],                           /* its open front */
      ["brass", OBJ_circle(50, 9.3, 2.6), { dome: 1.2 }],                                       /* the valve inside it */
      ["brass", OBJ_rrect(42, 15, 16, 5, 1), { z: .4, bev: .5 }],                               /* the collar ring */
      ["body", OBJ_rrect(31, 19, 38, 73, [12, 12, 4, 4]), { dome: 1.6 }],                        /* the cylinder */
      ["shade", OBJ_rrect(31, 19, 38, 18, [12, 12, 0, 0])],                                     /* the shoulder, its own colour */
      ["body", "M32 38H68M32 42H68", { ln: 1.4, cut: .8, paint: 0 }],                            /* the shoulder grooves */
      ["cream", OBJ_rrect(31, 52, 38, 14, 0), { z: .5, bev: .6 }],                               /* the label band */
      ["deep", OBJ_rrect(31, 84, 38, 8, [0, 0, 4, 4]), { z: .4, bev: .6 }],                       /* the foot ring */
    ],
  };
}

/* ---- Chapter 1: Scope and Administration - a rubber hand stamp: the domed knob, the grooved neck, the chamfered flange, the base and its
   inked rubber die. ---- */
{
  CHAPTER_OBJ["Chapter 1: Scope and Administration"] = {
    col: "#A0662F",   /* (384.67) natural colours: a wooden stamp, its red inked die */
    d: "M35 20A15 15 0 0 1 65 20A15 15 0 0 1 57.5 33" + OBJ_chain([[57.5, 33], [57.5, 48], [78, 50], [78, 62], [90, 64], [90, 86], [88, 94], [12, 94], [10, 86], [10, 64], [22, 62], [22, 50], [42.5, 48], [42.5, 33]], [0, 0, 3, 0, 3, 2, 2, 2, 2, 3, 0, 3, 0, 0]) + "A15 15 0 0 1 35 20Z",
    plates: [
      /* (art9) Madison: "There's a lot of spots all over that just don't look right." The neck was a box run up into the knob, so the
         knob's round foot showed through the neck's top; and the flange's rounded lower corners against the outline's fillets left a
         dark nick each side where it sits on the base. The neck now stops on the knob's own curve (the knob sits on it), and the
         flange stands square on the base, the outline's inside corners square with it. */
      ["body", OBJ_circle(50, 20, 15), { dome: 3.2 }],                                            /* the knob */
      ["shade", "M42.5 33A15 15 0 0 0 57.5 33V48H42.5Z", { dome: .8 }],                            /* the neck, up to the knob's curve */
      ["shade", "M42 38H58M42 43H58", { ln: 1.6, cut: .8, paint: 0 }],                           /* its grooves */
      ["body", OBJ_rrect(22, 48, 56, 14, [3, 3, 0, 0]), { gem: 1.4, gw: 3 }],                     /* the flange */
      ["deep", OBJ_rrect(10, 62, 80, 24, [3, 3, 0, 0]), { z: .4 }],                              /* the base (384.90: square below, where the die meets it) */
      ["lite", OBJ_rrect(14, 66, 72, 3, 1.5), { z: .3, bev: .4 }],                                /* its lip */
      ["red", OBJ_poly([[10, 86], [90, 86], [88, 94], [12, 94]], [0, 0, 2, 2]), { z: -.4, bev: .5 }],   /* the inked rubber die: the outline's own sides and corners (384.90) */
    ],
  };
}

/* ---- Chapter and Section Finder - a magnifying glass: the ring, the domed glass set into it, the brass collar, the grooved handle. ---- */
{
  const C = [40, 40], R = 34, W = 7, L = 40, s2 = Math.SQRT1_2;
  const dir = [s2, s2], nrm = [s2, -s2], a = Math.sqrt(R * R - W * W);
  const P1 = [C[0] + a * dir[0] + W * nrm[0], C[1] + a * dir[1] + W * nrm[1]], P2 = [C[0] + a * dir[0] - W * nrm[0], C[1] + a * dir[1] - W * nrm[1]];
  const E1 = [P1[0] + L * dir[0], P1[1] + L * dir[1]], E2 = [P2[0] + L * dir[0], P2[1] + L * dir[1]];
  const f = p => p[0].toFixed(2) + " " + p[1].toFixed(2), along = (t, w) => [C[0] + (R + t) * dir[0] + w * nrm[0], C[1] + (R + t) * dir[1] + w * nrm[1]];
  let grip = ""; for(let t = 14; t <= 34; t += 5) grip += "M" + f(along(t, -W - 1)) + "L" + f(along(t, W + 1));
  CHAPTER_OBJ["Chapter and Section Finder"] = {
    col: "#4A4F58",   /* (384.67) natural colours: a dark handle, a brass collar, glass */
    d: "M" + f(P1) + "A" + R + " " + R + " 0 1 0 " + f(P2) + "L" + f(E2) + "A" + W + " " + W + " 0 0 0 " + f(E1) + "Z",
    plates: [
      ["glass", OBJ_circle(40, 40, 26), { z: -.6, bev: .8, dome: 2.4 }],                          /* the glass, domed, set into the ring */
      ["deep", "M" + f(along(7, -W - 1)) + "L" + f(along(L + 2, -W - 1)) + "L" + f(along(L + 2, W + 1)) + "L" + f(along(7, W + 1)) + "Z", { dome: 1 }],   /* the handle, from the collar (art9: its end showed through the collar) */
      ["deep", grip, { ln: 1.4, cut: .7, paint: 0 }],                                              /* its grip */
      ["brass", "M" + f(along(-1, -W - 1)) + "L" + f(along(7, -W - 1)) + "L" + f(along(7, W + 1)) + "L" + f(along(-1, W + 1)) + "Z", { z: .7, bev: .6 }],   /* the collar */
    ],
  };
}

/* ---- Chapter 5: Fire Service Features - a fire hydrant, refined (384.93 r9): the faceted operating nut, the domed bonnet and the flange
   ring under it, the barrel with its big pumper cap facing you (the outlet a hydrant is known by), the base flange in the hydrant's own
   red with its bolts. (384.133 badgeart, Madison: "This needs to be fixed. Look at the sides." The side outlets were grey blocks stuck on
   short red stubs with a notch between them, so they read as loose ears.) Each side outlet is now one piece with the barrel: a short
   red nozzle that flares into the barrel with a fillet, a groove where its cap threads on, the cap itself in the hydrant's red - a
   little wider than the nozzle, with its grip ribs - and the steel pentagon nut on the cap's end, as on a real hydrant. ---- */
{
  /* one side outlet, on the right; the left is its mirror */
  const R = [[70, 44], [73, 46.5], [78, 46.5], [78, 44], [87, 44], [87, 48.5], [92, 48.5], [92, 55.5], [87, 55.5], [87, 60], [78, 60], [78, 57.5], [73, 57.5], [70, 60]];
  const Rr = [1, 2, .6, .6, 2.5, .6, 1.2, 1.2, .6, 2.5, .6, .6, 2, 1];
  const L = R.map(([x, y]) => [100 - x, y]).reverse(), Lr = Rr.slice().reverse();
  const top = [[42, 4], [58, 4], [60, 14], [72, 18], [76, 32], [70, 34]], topR = [2, 2, 2, 6, 3, 1];
  const foot = [[70, 80], [80, 82], [82, 94], [18, 94], [20, 82], [30, 80]], footR = [1, 2, 2, 2, 2, 1];
  const ret = [[30, 34], [24, 32], [28, 18], [40, 14]], retR = [1, 3, 6, 2];
  const nozzle = side => { const pts = [[70, 44], [73, 46.5], [78.4, 46.5], [78.4, 57.5], [73, 57.5], [70, 60]].map(([x, y]) => [side > 0 ? x : 100 - x, y]);
    return OBJ_poly(side > 0 ? pts : pts.slice().reverse(), [0, 2, 0, 0, 2, 0]); };
  const cap = side => OBJ_rrect(side > 0 ? 78 : 13, 44, 9, 16, 2.5);
  const nut = side => OBJ_rrect(side > 0 ? 86.5 : 8, 48.5, 5.5, 7, 1.2);
  CHAPTER_OBJ["Chapter 5: Fire Service Features"] = {
    col: "#D23A2E",
    d: OBJ_poly(top.concat(R).concat(foot).concat(L).concat(ret), topR.concat(Rr).concat(footR).concat(Lr).concat(retR)),
    plates: [
      ["field", nozzle(1) + nozzle(-1), { dome: .9 }],                                           /* the side nozzles, filleted into the barrel */
      ["field", OBJ_rrect(30, 32, 40, 50, 2), { dome: 1.6 }],                                    /* the barrel */
      ["field", "M24 32C24 20 36 14 50 14C64 14 76 20 76 32Z", { dome: 2.2 }],                   /* the bonnet */
      ["lite", OBJ_rrect(25, 30, 50, 5, 2), { z: .5, bev: .5 }],                                 /* the flange ring under it */
      ["steel", OBJ_poly([[42, 4], [58, 4], [60, 14], [40, 14]], 1), { gem: 1.4, gw: 2.6 }],     /* the operating nut */
      ["field", "M76.8 47.5V56.5M23.2 47.5V56.5", { ln: 1.4, cut: .7, paint: 0 }],               /* where each cap threads on */
      ["shade", cap(1) + cap(-1), { z: .3, bev: .7, dome: 1 }],                                  /* the outlet caps, the hydrant's red */
      ["shade", "M81.5 46V58M84.5 46V58M18.5 46V58M15.5 46V58", { ln: 1.1, cut: .5, paint: 0 }], /* their grip ribs */
      ["steel", nut(1) + nut(-1), { gem: 1, gw: 1.8 }],                                          /* the nut on each cap */
      ["steel", OBJ_circle(50, 56, 10.5), { z: .7, bev: .7, dome: .6 }],                          /* the pumper cap */
      ["steel", OBJ_poly([[50, 50.5], [55.2, 54.3], [53.2, 60.5], [46.8, 60.5], [44.8, 54.3]], .8), { gem: 1.1, gw: 2 }],   /* its nut */
      ["shade", OBJ_rrect(18, 80, 64, 14, 2), { z: .5 }],                                        /* the base flange */
      ["steel", OBJ_circle(26, 87, 2.4), { dome: 1.1 }],                                         /* its bolts */
      ["steel", OBJ_circle(42, 87, 2.4), { dome: 1.1 }],
      ["steel", OBJ_circle(58, 87, 2.4), { dome: 1.1 }],
      ["steel", OBJ_circle(74, 87, 2.4), { dome: 1.1 }],
    ],
  };
}
