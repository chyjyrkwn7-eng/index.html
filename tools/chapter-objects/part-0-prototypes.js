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

/* ---- Chapter 9: Fire Protection and Life Safety Systems - a pendant sprinkler head (Madison chose the sprinkler): the brass nipple with its
   threads, the faceted hex body, the frame narrowing to the boss with the red glass bulb in its windows, and the round deflector seen a
   little from above - its lit top face, its toothed rim. With no rim to swallow them, the thin parts are the sprinkler again. (A disc, not
   a flat bar: the back's title is laid out on the silhouette and the disc gives it room; a thick bar read as a comb.) ---- */
{
  const CX = 50, CY = 76, RX = 45, RY = 18, pts = [], rs = [];
  const ell = (t, k) => [CX + RX * k * Math.cos(t), CY + RY * k * Math.sin(t)];
  /* the top of the disc, from where the frame meets it round to the right */
  for(let d = 284; d <= 360; d += 19) { pts.push(ell(d * Math.PI / 180, 1)); rs.push(3); }
  /* its lower rim, toothed */
  for(let d = 9; d <= 171; d += 9){ pts.push(ell(d * Math.PI / 180, (d / 9) % 2 ? .9 : 1)); rs.push(.8); }
  for(let d = 180; d <= 256; d += 19) { pts.push(ell(d * Math.PI / 180, 1)); rs.push(3); }
  CHAPTER_OBJ["Chapter 9: Fire Protection and Life Safety Systems"] = {
    d: OBJ_poly([[41, 3], [59, 3], [59, 15], [68, 15], [73, 22.5], [68, 30], [65, 30], [59, 59.5]].concat(pts).concat([[41, 59.5], [35, 30], [32, 30], [27, 22.5], [32, 15], [41, 15]]),
      [1.5, 1.5, 1, 1, 1.5, 1, 1, 2].concat(rs).concat([2, 1, 1, 1.5, 1, 1])),
    base: "brass", col: "#C9972F",   /* (384.67) natural colours: a brass head, polished metal all over, its red glass bulb */
    plates: [
      ["brass", OBJ_rrect(41, 3, 18, 12, 1.5), { z: .4 }],                                     /* the nipple */
      ["brass", "M41 6.5H59M41 10H59M41 13.5H59", { ln: 1.4, cut: .8, paint: 0 }],             /* its threads */
      ["brass", OBJ_poly([[32, 15], [68, 15], [73, 22.5], [68, 30], [32, 30], [27, 22.5]], 1), { gem: 1.4, gw: 3 }],   /* the hex body */
      ["body", "M41 16V29M59 16V29", { ln: 1.4, cut: .7, paint: 0 }],                            /* its flats */
      ["brass", OBJ_poly([[35, 30], [65, 30], [59, 62], [41, 62]], 1), { z: .5 }],              /* the frame */
      ["ink", OBJ_poly([[39, 33], [45.5, 33], [45.5, 57], [42.5, 57]], 1), { z: -1.7, bev: .6 }],   /* its two windows */
      ["ink", OBJ_poly([[61, 33], [54.5, 33], [54.5, 57], [57.5, 57]], 1), { z: -1.7, bev: .6 }],
      ["red", OBJ_ellipse(50, 45, 4.4, 12), { dome: 2.6 }],                                     /* the glass bulb */
      ["brass", OBJ_ellipse(CX, CY - 2, RX - 5, RY - 5), { z: .6, bev: 1, dome: .6 }],          /* the deflector's top face */
      ["brass", OBJ_rrect(43, 54, 14, 9, 2), { dome: 1.4 }],                                    /* the boss on it */
    ],
  };
}

/* ---- Chapter 57: Flammable and Combustible Liquids - a gas can in classic jerry-can red: the carry handle with its open loop (a real hole),
   the pressed panel with its embossed X, the black spout with its amber cap. ---- */
{
  const A = [72, 31], B = [89, 9], ux = B[0] - A[0], uy = B[1] - A[1], L = Math.hypot(ux, uy), dx = ux / L, dy = uy / L, nx = -dy, ny = dx;
  const at = (t, w) => [A[0] + dx * t + nx * w, A[1] + dy * t + ny * w];
  const bl = at(0, -6), br = at(0, 6), tl = at(L - 4, -6), tr = at(L - 4, 6), cl = at(L - 4, -8), cr = at(L - 4, 8), ct = at(L + 4, -8), cu = at(L + 4, 8);
  CHAPTER_OBJ["Chapter 57: Flammable and Combustible Liquids"] = {
    d: OBJ_poly([[8, 94], [8, 34], [13, 30], [13, 14], [17, 10], [48, 10], [52, 14], [52, 30], [bl[0], 30], bl, tl, cl, ct, cu, cr, tr, br, [br[0], 30], [84, 31], [88, 36], [88, 94]],
      [6, 3, 2, 4, 2, 2, 4, 2, 2, 1, 1, 1, 2, 2, 1, 1, 1, 2, 3, 4, 6]),
    holes: [OBJ_rrect(20, 16, 25, 9, 3.5)],
    base: "red",
    plates: [
      ["red", OBJ_rrect(8, 30, 80, 64, [0, 0, 6, 6])],                                          /* the can */
      ["red", OBJ_rrect(15, 40, 66, 46, 4), { z: -.9, bev: 1 }],                                /* the panel pressed into its side */
      ["red", "M21 46L75 80M75 46L21 80", { ln: 6, z: 1.4, bev: 1.4 }],                         /* the embossed X */
      ["red", OBJ_rrect(13, 10, 39, 22, 4), { z: .3, bev: .8 }],                                /* the handle */
      ["rubber", OBJ_poly([bl, tl, tr, br], 1), { z: .4, dome: .8 }],                           /* the spout */
      ["hot", OBJ_poly([cl, ct, cu, cr], 1.5), { dome: 1.4 }],                                  /* its cap */
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
      ["cream", OBJ_rrect(6, 58, 90, 6, 0), { z: .4, bev: .5 }],                                /* the stripe */
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
    d: "M35 20A15 15 0 0 1 65 20A15 15 0 0 1 57.5 33" + OBJ_chain([[57.5, 33], [57.5, 48], [78, 50], [78, 62], [90, 64], [90, 86], [88, 94], [12, 94], [10, 86], [10, 64], [22, 62], [22, 50], [42.5, 48], [42.5, 33]], [0, 2, 3, 2, 3, 2, 2, 2, 2, 3, 2, 3, 2, 0]) + "A15 15 0 0 1 35 20Z",
    plates: [
      ["body", OBJ_circle(50, 20, 15), { dome: 3.2 }],                                            /* the knob */
      ["shade", OBJ_rrect(42.5, 32, 15, 17, 0), { dome: .8 }],                                   /* the neck */
      ["shade", "M42 38H58M42 43H58", { ln: 1.6, cut: .8, paint: 0 }],                           /* its grooves */
      ["body", OBJ_rrect(22, 48, 56, 14, 3), { gem: 1.4, gw: 3 }],                               /* the flange */
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
      ["deep", "M" + f(along(6, -W - 1)) + "L" + f(along(L + 2, -W - 1)) + "L" + f(along(L + 2, W + 1)) + "L" + f(along(6, W + 1)) + "Z", { dome: 1 }],   /* the handle */
      ["deep", grip, { ln: 1.4, cut: .7, paint: 0 }],                                              /* its grip */
      ["brass", "M" + f(along(-1, -W - 1)) + "L" + f(along(7, -W - 1)) + "L" + f(along(7, W + 1)) + "L" + f(along(-1, W + 1)) + "Z", { z: .7, bev: .6 }],   /* the collar */
    ],
  };
}

/* ---- Chapter 5: Fire Service Features - a fire hydrant (Madison's own suggestion): the faceted operating nut, the domed bonnet, the barrel,
   the two side outlets with their faceted caps, the base flange and its bolts. ---- */
{
  CHAPTER_OBJ["Chapter 5: Fire Service Features"] = {
    col: "#D23A2E",   /* (384.67) natural colours: a red hydrant */
    d: OBJ_poly([[42, 4], [58, 4], [60, 14], [72, 18], [76, 32], [70, 34], [70, 44], [86, 44], [86, 40], [94, 40], [94, 64], [86, 64], [86, 60], [70, 60], [70, 80], [80, 82], [82, 94], [18, 94], [20, 82], [30, 80], [30, 60], [14, 60], [14, 64], [6, 64], [6, 40], [14, 40], [14, 44], [30, 44], [30, 34], [24, 32], [28, 18], [40, 14]],
      [2, 2, 2, 6, 3, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 3, 6, 2]),
    plates: [
      ["field", OBJ_rrect(30, 32, 40, 50, 2), { dome: 1.6 }],                                    /* the barrel */
      ["field", "M24 32C24 20 36 14 50 14C64 14 76 20 76 32Z", { dome: 2.2 }],                   /* the bonnet */
      ["steel", OBJ_poly([[42, 4], [58, 4], [60, 14], [40, 14]], 1), { gem: 1.4, gw: 2.6 }],     /* the operating nut */
      ["field", OBJ_rrect(14, 44, 16, 16, 1.5), { dome: 1 }],                                    /* the outlets */
      ["field", OBJ_rrect(70, 44, 16, 16, 1.5), { dome: 1 }],
      ["steel", OBJ_rrect(6, 40, 8, 24, 2), { gem: 1.2, gw: 2 }],                                /* their caps */
      ["steel", OBJ_rrect(86, 40, 8, 24, 2), { gem: 1.2, gw: 2 }],
      ["deep", OBJ_rrect(18, 80, 64, 14, 2), { z: .5 }],                                         /* the base flange */
      ["steel", OBJ_circle(26, 87, 2.4), { dome: 1.1 }],                                         /* its bolts */
      ["steel", OBJ_circle(42, 87, 2.4), { dome: 1.1 }],
      ["steel", OBJ_circle(58, 87, 2.4), { dome: 1.1 }],
      ["steel", OBJ_circle(74, 87, 2.4), { dome: 1.1 }],
    ],
  };
}
