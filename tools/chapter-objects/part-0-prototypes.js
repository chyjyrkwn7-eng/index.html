/* Fire Code chapter objects - PROTOTYPES (build 384.65): eight chapters that prove the recipe across very different kinds of thing.
   Each entry is the chapter's silhouette (the badge's outline) and the plates inlaid in it. See tools/chapter-objects/README.md. */

/* ---- Chapter 10: Means of Egress - an open door. The leaf is swung toward you, so its free edge is the nearest and the tallest
   thing: it stands out past the top and the bottom of the frame. The doorway beside it is the lit rectangle, bright with the way out. ---- */
{
  const lerp = (a, b, t) => a + (b - a) * t;
  /* a point on the leaf: u 0 at the hinge to 1 at the free edge, v 0 at the top to 1 at the bottom (perspective: the free edge is taller) */
  const leaf = (u, v) => [lerp(16, 52, u), lerp(lerp(12, 2, u), lerp(88, 98, u), v)];
  const quad = (u0, u1, v0, v1, r) => OBJ_poly([leaf(u0, v0), leaf(u1, v0), leaf(u1, v1), leaf(u0, v1)], r);
  CHAPTER_OBJ["Chapter 10: Means of Egress"] = {
    d: OBJ_poly([[16, 12], [52, 2], [52, 12], [90, 12], [90, 88], [52, 88], [52, 98], [16, 88]], [3, 2, 1, 3, 3, 1, 2, 3]),
    plates: [
      ["deep", OBJ_rrect(16, 12, 74, 76, 3), { e: 0 }],                                   /* the frame */
      ["glow", OBJ_rrect(24, 20, 58, 68, 1), { e: 1.4 }],                                    /* the way out, lit */
      ["body", OBJ_poly([leaf(0, 0), leaf(1, 0), leaf(1, 1), leaf(0, 1)], 2), { sh: 1, e: 1.6 }],   /* the leaf */
      ["shade", quad(.86, 1, 0, 1, 1), { e: 0 }],                                          /* its thick edge */
      ["lite", quad(.16, .72, .1, .45, 2), { e: 1.3 }],                                 /* upper panel */
      ["lite", quad(.16, .72, .55, .9, 2), { e: 1.3 }],                                 /* lower panel */
      ["hot", OBJ_circle(leaf(.8, .5)[0], leaf(.8, .5)[1], 3.2), { e: 1.2 }],             /* the handle */
    ],
  };
}

/* ---- Chapter 9: Fire Protection and Life Safety Systems - a pendant sprinkler on its pipe, spraying (a device; Madison chose the sprinkler
   over an extinguisher or an alarm bell): the supply pipe across the top, the nipple and hex body hanging from it, the frame with its two
   arms round the red glass bulb, the wide flat deflector, and the cone of water it throws, which is where the chapter's blue lives. The
   pipe, nipple, arms and deflector are too thin to hold enamel: bare metal. A sprinkler's arms alone are thin (no enamel, a blob under
   the rim), so the frame is drawn solid and the arms and the bulb are plates in it; the pipe across the top is what stops the whole
   from reading as a chess piece. ---- */
{
  const dots = (y, x0, x1, step) => { let d = ""; for(let x = x0; x <= x1; x += step) d += "M" + x + " " + y + "h.01"; return d; };
  CHAPTER_OBJ["Chapter 9: Fire Protection and Life Safety Systems"] = {
    base: "steel",
    d: "M50 4" + OBJ_chain([[50, 4], [92, 4], [92, 18], [58, 18], [58, 22], [68, 26], [68, 38], [64, 42], [70, 60], [90, 62], [90, 70], [68, 72], [82, 94], [18, 94], [32, 72], [10, 70], [10, 62], [30, 60], [36, 42], [32, 38], [32, 26], [42, 22], [42, 18], [8, 18], [8, 4], [50, 4]],
      [0, 5, 5, 2, 2, 3, 3, 3, 3, 5, 5, 3, 8, 8, 3, 5, 5, 3, 3, 3, 3, 2, 2, 5, 5, 0]) + "Z",
    plates: [
      ["body", OBJ_rrect(32, 26, 36, 12, 3), { e: 1.4 }],                                    /* the hex body, lit */
      ["deep", OBJ_poly([[36, 42], [64, 42], [70, 60], [30, 60]], 1), { e: 0 }],             /* the dark between the arms */
      ["steel", OBJ_poly([[36, 42], [42, 42], [38, 60], [30, 60]], 1), { e: 1 }],            /* the frame arms */
      ["steel", OBJ_poly([[64, 42], [58, 42], [62, 60], [70, 60]], 1), { e: 1 }],
      ["hot", OBJ_ellipse(50, 51, 7, 11), { sh: 1, e: 1.4 }],                                /* the glass bulb, red with its liquid */
      ["lite", OBJ_ellipse(47.5, 47, 2, 4), { e: 0 }],                                       /* its glint */
      ["body", OBJ_poly([[32, 72], [68, 72], [82, 94], [18, 94]], 2), { e: 0 }],             /* the cone of spray */
      ["lite", dots(79, 38, 62, 6), { ln: 4 }],                                              /* its drops */
      ["lite", dots(86, 30, 70, 6), { ln: 3.6 }],
    ],
  };
}

/* ---- Chapter 57: Flammable and Combustible Liquids - a safety can (a hazardous-material container). The handle hump on the left,
   the angled spout on the right, a flame on its face. The spout and the handle are thin enough to be the bare metal. ---- */
{
  /* a flame: a bold teardrop leaning left with a curl, centred on (cx, cy), h tall */
  const flame = (cx, cy, h) => {
    const k = h / 40, X = x => (cx + x * k).toFixed(2), Y = y => (cy + y * k).toFixed(2);
    return "M" + X(2) + " " + Y(-20) + "C" + X(4) + " " + Y(-10) + " " + X(15) + " " + Y(-6) + " " + X(15) + " " + Y(6) +
      "C" + X(15) + " " + Y(14) + " " + X(8) + " " + Y(20) + " " + X(0) + " " + Y(20) +
      "C" + X(-9) + " " + Y(20) + " " + X(-15) + " " + Y(14) + " " + X(-15) + " " + Y(5) +
      "C" + X(-15) + " " + Y(-2) + " " + X(-10) + " " + Y(-6) + " " + X(-8) + " " + Y(-12) +
      "C" + X(-4) + " " + Y(-8) + " " + X(-2) + " " + Y(-5) + " " + X(-2) + " " + Y(-1) + "C" + X(-1) + " " + Y(-8) + " " + X(0) + " " + Y(-14) + " " + X(2) + " " + Y(-20) + "Z";
  };
  CHAPTER_OBJ["Chapter 57: Flammable and Combustible Liquids"] = {
    d: "M40 92" + OBJ_chain([[40, 92], [10, 92], [10, 40], [20, 14], [44, 12], [50, 40], [60, 40], [81, 11], [92, 21], [73, 40], [84, 40], [84, 92], [40, 92]], [0, 9, 6, 5, 5, 3, 2, 4, 4, 2, 5, 9, 0]) + "Z",
    plates: [
      ["body", OBJ_rrect(10, 40, 74, 52, [0, 0, 9, 9]), { e: 0 }],                            /* the can */
      ["ink", OBJ_poly([[26, 20], [40, 19], [43, 36], [24, 37]], 2), { e: 0 }],                /* the handle's hollow */
      ["deep", "M12 58H82", { ln: 2.2 }],                                                    /* a rib across the can */
      ["shade", OBJ_rrect(66, 48, 18, 44, 2), { e: 0 }],                                      /* its turned-away side */
      ["glow", flame(46, 66, 38), { sh: 1, e: 1.5 }],                                         /* the flame */
      ["hot", flame(46, 71, 20), { e: 0 }],                                                   /* its core */
    ],
  };
}

/* ---- Appendix D: Fire Apparatus Access Roads - a ladder truck (a vehicle), side on, facing left: the ladder rack runs the whole roof
   and reaches out over the cab, two big wheels. The widest, lowest silhouette in the set. ---- */
{
  let rungs = ""; for(let x = 16; x <= 90; x += 6) rungs += "M" + x + " 25.5V34.5";
  CHAPTER_OBJ["Appendix D: Fire Apparatus Access Roads"] = {
    d: "M10 71" + OBJ_chain([[10, 71], [6, 71], [6, 60], [14, 48], [38, 48], [38, 38], [10, 38], [10, 22], [94, 22], [94, 71], [86, 71]], [0, 4, 4, 5, 2, 2, 3, 3, 3, 3, 0]) +
       "A12 12 0 0 1 62 71" + OBJ_chain([[62, 71], [38, 71]], 0) + "A12 12 0 0 1 14 71" + OBJ_chain([[14, 71], [10, 71]], 0) + "Z",
    plates: [
      ["deep", OBJ_rrect(38, 38, 56, 33, 2), { e: 0 }],                                     /* the body */
      ["steel", OBJ_rrect(10, 22, 84, 16, 3), { e: 0 }],                                    /* the ladder rack */
      ["deep", rungs, { ln: 1.6 }],                                                          /* the ladder's rungs */
      ["shade", OBJ_rrect(42, 44, 14, 22, 2), { e: 1.2 }],                                   /* the locker doors */
      ["shade", OBJ_rrect(59, 44, 14, 22, 2), { e: 1.2 }],
      ["shade", OBJ_rrect(76, 44, 14, 22, 2), { e: 1.2 }],
      ["hot", OBJ_rrect(38, 58, 56, 4, 0), { e: 0 }],                                        /* the stripe */
      ["glow", OBJ_poly([[10, 62], [17, 52], [34, 52], [34, 62]], 2), { e: 1.4 }],           /* the cab's windows */
      ["steel", OBJ_circle(26, 71, 6.5), { e: 1.2 }],                                        /* the hubs */
      ["steel", OBJ_circle(74, 71, 6.5), { e: 1.2 }],
    ],
  };
}

/* ---- Chapter 53: Compressed Gases - a gas cylinder (a hazardous-material container; the tall, narrow silhouette): the valve with its
   handwheel across the top, the collar, the domed shoulder, the long body with a band round it. ---- */
{
  CHAPTER_OBJ["Chapter 53: Compressed Gases"] = {
    d: "M50 4" + OBJ_chain([[50, 4], [72, 4], [72, 15], [58, 15], [58, 26], [66, 28], [74, 42], [74, 92], [26, 92], [26, 42], [34, 28], [42, 26], [42, 15], [28, 15], [28, 4], [50, 4]],
      [0, 5, 5, 2, 2, 2, 14, 9, 9, 14, 2, 2, 2, 5, 5, 0]) + "Z",
    plates: [
      ["body", OBJ_rrect(26, 30, 48, 62, [18, 18, 9, 9]), { e: 0 }],                         /* the cylinder */
      ["shade", "M26 44C26 28 42 28 50 28C58 28 74 28 74 44Z", { e: 1.2 }],                    /* the domed shoulder */
      ["lite", OBJ_rrect(32, 40, 7, 40, 3), { e: 0 }],                                       /* the light down its left */
      ["shade", OBJ_rrect(64, 40, 10, 48, 3), { e: 0 }],                                     /* the turning away on its right */
      ["glow", OBJ_rrect(26, 50, 48, 14, 1), { e: 1.4 }],                                    /* the label band */
      ["deep", OBJ_rrect(26, 82, 48, 10, [0, 0, 9, 9]), { e: 0 }],                           /* the foot ring */
    ],
  };
}

/* ---- Chapter 1: Scope and Administration - a rubber hand stamp (an idea, drawn as the thing that makes it official): a round
   handle, a neck, a stepped base with its rubber die. ---- */
{
  CHAPTER_OBJ["Chapter 1: Scope and Administration"] = {
    d: "M33 26A17 17 0 0 1 67 26A17 17 0 0 1 60 40" + OBJ_chain([[60, 40], [60, 52], [80, 52], [80, 66], [92, 66], [92, 92], [8, 92], [8, 66], [20, 66], [20, 52], [40, 52], [40, 40]], [0, 3, 4, 3, 3, 5, 5, 3, 3, 4, 3, 0]) + "A17 17 0 0 1 33 26Z",
    plates: [
      ["body", OBJ_circle(50, 26, 17), { sh: 1, e: 1.5 }],                                    /* the knob */
      ["lite", OBJ_circle(44, 20, 5), { e: 0 }],
      ["shade", OBJ_rrect(40, 40, 20, 14, 0), { e: 0 }],                                      /* the neck */
      ["body", OBJ_rrect(20, 52, 60, 14, 3), { sh: 1, e: 1.5 }],                              /* the plate */
      ["deep", OBJ_rrect(8, 66, 84, 26, [2, 2, 5, 5]), { e: 0 }],                              /* the base */
      ["lite", OBJ_rrect(14, 70, 72, 3, 1), { e: 0 }],
      ["hot", OBJ_rrect(14, 78, 72, 8, 1), { e: 1.2 }],                                      /* the rubber die, inked */
    ],
  };
}

/* ---- Chapter and Section Finder - a magnifying glass (a lookup, drawn as the tool you look things up with): a round lens, a
   collar and a handle at 45 degrees. The lens's rim is the badge's own. ---- */
{
  const C = [40, 40], R = 33, W = 8, L = 40, s2 = Math.SQRT1_2;
  const dir = [s2, s2], nrm = [s2, -s2], a = Math.sqrt(R * R - W * W);
  const P1 = [C[0] + a * dir[0] + W * nrm[0], C[1] + a * dir[1] + W * nrm[1]], P2 = [C[0] + a * dir[0] - W * nrm[0], C[1] + a * dir[1] - W * nrm[1]];
  const E1 = [P1[0] + L * dir[0], P1[1] + L * dir[1]], E2 = [P2[0] + L * dir[0], P2[1] + L * dir[1]];
  const f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  CHAPTER_OBJ["Chapter and Section Finder"] = {
    d: "M" + f(P1) + "A" + R + " " + R + " 0 1 0 " + f(P2) + "L" + f(E2) + "A" + W + " " + W + " 0 0 0 " + f(E1) + "Z",
    plates: [
      ["lite", OBJ_circle(40, 40, 26), { e: 1.6 }],                                           /* the glass */
      ["glow", "M22 40A18 18 0 0 1 40 22", { ln: 3.4 }],                                      /* the light across it */
      ["deep", "M" + f([P1[0] + 6 * dir[0], P1[1] + 6 * dir[1]]) + "L" + f(E1) + "L" + f(E2) + "L" + f([P2[0] + 6 * dir[0], P2[1] + 6 * dir[1]]) + "Z", { e: 1.3 }],   /* the grip */
      ["steel", "M" + f(P1) + "L" + f([P1[0] + 7 * dir[0], P1[1] + 7 * dir[1]]) + "L" + f([P2[0] + 7 * dir[0], P2[1] + 7 * dir[1]]) + "L" + f(P2) + "Z", { e: 1.2 }],   /* the collar */
    ],
  };
}

/* ---- Chapter 5: Fire Service Features - a fire helmet, side on: the high crown with its comb, the long swept-back tail, the front shield. ---- */
{
  CHAPTER_OBJ["Chapter 5: Fire Service Features"] = {
    d: "M10 68Q10 62 18 60L22 48C22 24 40 8 58 8C78 8 82 34 84 56C88 62 95 70 93 80Q92 86 86 83C70 77 40 77 22 75Q10 74 10 68Z",
    plates: [
      ["body", "M20 60L24 46C25 26 40 12 58 12C74 12 80 30 82 52L82 62L20 62Z", { e: 0 }],       /* the crown */
      ["deep", "M10 62L84 58C88 62 94 70 93 80Q92 86 86 83C70 77 40 77 22 75Q10 74 10 62Z", { e: 0 }],   /* the brim */
      ["shade", "M32 20C42 12 58 10 66 16C75 22 79 34 81 50L74 48C72 36 66 26 58 24C50 22 40 26 36 32Z", { e: 0 }],   /* the comb */
      ["lite", "M24 34L46 34L46 54Q35 62 24 54Z", { sh: 1, e: 1.5 }],                           /* the front shield */
      ["hot", OBJ_circle(35, 44, 5), { e: 1.2 }],
    ],
  };
}
