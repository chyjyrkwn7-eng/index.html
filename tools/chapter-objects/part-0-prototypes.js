/* Fire Code chapter objects - PROTOTYPES, round 2 (build 384.65): eight chapters that prove the recipe across very different kinds of thing.
   Round 1 (be5d880) put its identity in bare silver (a pipe, arms, a spout drawn by the rim) and in small stickers (a flame, a pocket
   badge, a lit rectangle). Madison: "I feel like you are just throwing stickers in the middle of the badges ... the silver part is making
   the actual design." So now: the rim is an even band all round and never the design; EVERY part of an object is at least MIN_PART (20)
   wide so it holds its own rim and its own enamel; identity is the silhouette; interior plates only colour-block the object's own parts.
   See tools/chapter-objects/README.md. */

/* ---- Chapter 10: Means of Egress - an open door in its frame. The leaf is swung toward you (its free edge the nearest and the tallest thing);
   the frame is a lintel and a post, and the doorway between the leaf and the post is open to the case behind (a notch, 28 wide). The
   rim is even all round; every part (leaf, lintel, post) holds its own enamel. A real HOLE for the doorway was tried (the renderer
   supports holes now) and read as a letter O and a mail slot, so it is a notch. ---- */
{
  const lerp = (a, b, t) => a + (b - a) * t;
  /* a point on the leaf: u 0 at the hinge to 1 at the free edge, v 0 at the top to 1 at the bottom (perspective: the free edge is taller) */
  const leaf = (u, v) => [lerp(12, 42, u), lerp(lerp(16, 4, u), lerp(84, 96, u), v)];
  const quad = (u0, u1, v0, v1, r) => OBJ_poly([leaf(u0, v0), leaf(u1, v0), leaf(u1, v1), leaf(u0, v1)], r);
  CHAPTER_OBJ["Chapter 10: Means of Egress"] = {
    d: OBJ_poly([[12, 16], [42, 4], [42, 8], [94, 8], [94, 94], [74, 94], [74, 28], [42, 28], [42, 96], [12, 84]], [4, 3, 2, 5, 5, 4, 3, 3, 3, 4]),
    plates: [
      ["deep", OBJ_rrect(42, 8, 52, 20, 2), { e: 0 }],                                   /* the lintel */
      ["deep", OBJ_rrect(74, 8, 20, 86, 2), { e: 0 }],                                   /* the post */
      ["body", OBJ_poly([leaf(0, 0), leaf(1, 0), leaf(1, 1), leaf(0, 1)], 2), { sh: 1, e: 1.6 }],   /* the leaf */
      ["shade", quad(.8, 1, 0, 1, 1), { e: 0 }],                                           /* its thick edge */
      ["lite", quad(.1, .66, .1, .46, 2), { e: 1.3 }],                                   /* its upper panel */
      ["lite", quad(.1, .66, .54, .9, 2), { e: 1.3 }],                                   /* its lower panel */
    ],
  };
}

/* ---- Chapter 9: Fire Protection and Life Safety Systems - a sprinkler head spraying (Madison chose the sprinkler): the pipe stub, the hex
   body, the wide flat deflector, and three bold drops of water falling from it, which are part of the outline (the notches between them
   are what say "spray"). Every part is wide enough to hold enamel; nothing is a sticker. ---- */
{
  CHAPTER_OBJ["Chapter 9: Fire Protection and Life Safety Systems"] = {
    d: OBJ_poly([[37, 4], [63, 4], [63, 18], [74, 20], [74, 38], [94, 40], [94, 74], [86, 87], [80, 95], [74, 87], [66, 76], [65, 62], [64, 76], [56, 87], [50, 95], [44, 87], [36, 76], [35, 62], [34, 76], [26, 87], [20, 95], [14, 87], [6, 74], [6, 40], [26, 38], [26, 20], [37, 18]],
      [3, 3, 3, 3, 3, 4, 8, 6, 4, 6, 6, 1, 6, 6, 4, 6, 6, 1, 6, 6, 4, 6, 8, 4, 3, 3, 3]),
    plates: [
      ["deep", OBJ_rrect(37, 4, 26, 16, 3), { e: 0 }],                                       /* the stub */
      ["body", OBJ_rrect(26, 20, 48, 18, 0), { e: 0 }],                                      /* the hex body, in its faces */
      ["shade", OBJ_rrect(26, 20, 14, 18, 0), { e: 0 }],
      ["deep", OBJ_rrect(6, 38, 88, 22, 6), { sh: 1, e: 0 }],                                /* the deflector */
      ["lite", OBJ_rrect(10, 42, 80, 7, 3), { e: 0 }],
      ["body", OBJ_poly([[6, 60], [94, 60], [94, 96], [6, 96]], 0), { e: 0 }],              /* the water */
      ["lite", OBJ_poly([[6, 60], [94, 60], [94, 70], [6, 70]], 0), { e: 0 }],
      ["shade", OBJ_poly([[6, 84], [94, 84], [94, 96], [6, 96]], 0), { e: 0 }],
    ],
  };
}

/* ---- Chapter 57: Flammable and Combustible Liquids - a gas can (a hazardous-material container). The silhouette is the whole point: the
   round handle hump on the left, the long angled spout with its wider cap on the right, a valley between them. No flame sticker. ---- */
{
  const hump = []; for(let k = 0; k <= 8; k++){ const t = (180 + 180 * k / 8) * Math.PI / 180; hump.push([24 + 18 * Math.cos(t), 40 + 22 * Math.sin(t)]); }
  /* the spout: an axis from its base on the can's top to its cap, a tube 22 wide and a cap 28 wide */
  const A = [66, 42], B = [88, 14], ux = (B[0] - A[0]), uy = (B[1] - A[1]), L = Math.hypot(ux, uy), dx = ux / L, dy = uy / L, nx = -dy, ny = dx;
  const at = (t, w) => [A[0] + dx * t + nx * w, A[1] + dy * t + ny * w];
  const bl = at(0, -11), br = at(0, 11), tl = at(L - 8, -11), tr = at(L - 8, 11), cl = at(L - 8, -14), cr = at(L - 8, 14), ct = at(L + 2, -14), cu = at(L + 2, 14);
  CHAPTER_OBJ["Chapter 57: Flammable and Combustible Liquids"] = {
    d: OBJ_poly([[6, 92], [6, 40]].concat(hump.slice(1, 8)).concat([[42, 40], [bl[0] - 2, 40], bl, tl, cl, ct, cu, cr, tr, [br[0] + 4, 40], [94, 44], [94, 92]]),
      [9, 4].concat(hump.slice(1, 8).map(() => 2), [3, 3, 3, 2, 2, 2, 4, 4, 2, 2, 3, 4, 4, 9])),
    plates: [
      ["body", OBJ_rrect(6, 40, 88, 52, [0, 0, 9, 9]), { e: 0 }],                            /* the can */
      ["shade", OBJ_rrect(6, 68, 88, 24, [0, 0, 9, 9]), { e: 0 }],                           /* its lower band */
      ["lite", OBJ_rrect(6, 44, 88, 9, 0), { e: 0 }],                                       /* the light along its shoulder */
      ["deep", OBJ_poly([[6, 40]].concat(hump.slice(1, 8)).concat([[42, 40], [42, 44], [6, 44]]), 1), { e: 0 }],   /* the handle hump */
      ["deep", OBJ_poly([bl, tl, tr, br], 1), { e: 0 }],                                    /* the spout */
      ["hot", OBJ_poly([cl, ct, cu, cr], 2), { e: 0 }],                                     /* its cap */
    ],
  };
}

/* ---- Appendix D: Fire Apparatus Access Roads - a ladder truck (a vehicle), side on, facing left: the low cab, the tall body with one fat ladder
   bar along its roof, two big wheels. The widest, lowest silhouette in the set. ---- */
{
  CHAPTER_OBJ["Appendix D: Fire Apparatus Access Roads"] = {
    d: "M20 78" + OBJ_chain([[20, 78], [8, 78], [8, 62], [16, 48], [42, 48], [42, 14], [96, 14], [96, 78], [86, 78]], [0, 4, 6, 6, 2, 3, 4, 4, 0]) +
       "A13 13 0 0 1 60 78" + OBJ_chain([[60, 78], [42, 78]], 0) + "A13 13 0 0 1 20 78Z",
    plates: [
      ["deep", OBJ_rrect(42, 34, 54, 44, 2), { e: 0 }],                                     /* the body */
      ["lite", OBJ_rrect(42, 14, 54, 20, 3), { e: 0 }],                                     /* the ladder bar, along its roof */
      ["deep", "M54 14V34M66 14V34M78 14V34M90 14V34", { ln: 2 }],                          /* its rungs */
      ["hot", OBJ_rrect(8, 62, 88, 7, 0), { e: 0 }],                                         /* the stripe, cab to tail */
      ["shade", OBJ_rrect(48, 40, 18, 18, 2), { e: 1.2 }],                                  /* the lockers */
      ["shade", OBJ_rrect(70, 40, 20, 18, 2), { e: 1.2 }],
      ["lite", OBJ_poly([[10, 62], [18, 50], [40, 50], [40, 62]], 2), { e: 1.2 }],          /* the cab's windows */
    ],
  };
}

/* ---- Chapter 53: Compressed Gases - a gas cylinder (a hazardous-material container; the tall, narrow silhouette): a fat valve block, the
   domed shoulder, the long body. Its shoulder and its band are colour blocks of the cylinder. ---- */
{
  CHAPTER_OBJ["Chapter 53: Compressed Gases"] = {
    d: "M50 4" + OBJ_chain([[50, 4], [68, 4], [68, 26], [74, 32], [76, 46], [76, 92], [24, 92], [24, 46], [26, 32], [32, 26], [32, 4], [50, 4]],
      [0, 5, 3, 8, 14, 9, 9, 14, 8, 3, 5, 0]) + "Z",
    plates: [
      ["body", OBJ_rrect(24, 30, 52, 62, [18, 18, 9, 9]), { e: 0 }],                         /* the cylinder */
      ["shade", "M24 50C24 30 38 28 50 28C62 28 76 30 76 50Z", { e: 0 }],                    /* the domed shoulder */
      ["deep", OBJ_rrect(32, 4, 36, 24, 3), { e: 0 }],                                       /* the valve */
      ["lite", OBJ_rrect(24, 56, 52, 16, 0), { e: 0 }],                                      /* the band round it */
      ["shade", OBJ_rrect(24, 80, 52, 12, [0, 0, 9, 9]), { e: 0 }],                          /* its foot */
    ],
  };
}

/* ---- Chapter 1: Scope and Administration - a rubber hand stamp (an idea, drawn as the thing that makes it official): a round handle, a
   neck, a flange, a base with its rubber die. ---- */
{
  CHAPTER_OBJ["Chapter 1: Scope and Administration"] = {
    d: "M33 22A17 17 0 0 1 67 22A17 17 0 0 1 60 36" + OBJ_chain([[60, 36], [60, 50], [80, 52], [80, 70], [94, 72], [94, 94], [6, 94], [6, 72], [20, 70], [20, 52], [40, 50], [40, 36]], [0, 3, 4, 3, 4, 5, 5, 4, 3, 4, 3, 0]) + "A17 17 0 0 1 33 22Z",
    plates: [
      ["body", OBJ_circle(50, 22, 17), { sh: 1, e: 1.5 }],                                    /* the knob */
      ["shade", OBJ_rrect(40, 36, 20, 16, 0), { e: 0 }],                                      /* the neck */
      ["body", OBJ_rrect(20, 50, 60, 22, 3), { sh: 1, e: 1.5 }],                              /* the flange */
      ["deep", OBJ_rrect(6, 70, 88, 24, [2, 2, 6, 6]), { e: 0 }],                              /* the base */
      ["lite", OBJ_rrect(6, 80, 88, 14, [0, 0, 6, 6]), { e: 0 }],                              /* the rubber die */
    ],
  };
}

/* ---- Chapter and Section Finder - a magnifying glass (a lookup, drawn as the tool you look things up with): the fat round lens and the fat
   handle at 45 degrees. The benchmark: the rim even all round, the lens the badge's own enamel. ---- */
{
  const C = [40, 40], R = 36, W = 10, L = 40, s2 = Math.SQRT1_2;
  const dir = [s2, s2], nrm = [s2, -s2], a = Math.sqrt(R * R - W * W);
  const P1 = [C[0] + a * dir[0] + W * nrm[0], C[1] + a * dir[1] + W * nrm[1]], P2 = [C[0] + a * dir[0] - W * nrm[0], C[1] + a * dir[1] - W * nrm[1]];
  const E1 = [P1[0] + L * dir[0], P1[1] + L * dir[1]], E2 = [P2[0] + L * dir[0], P2[1] + L * dir[1]];
  const f = p => p[0].toFixed(2) + " " + p[1].toFixed(2);
  CHAPTER_OBJ["Chapter and Section Finder"] = {
    d: "M" + f(P1) + "A" + R + " " + R + " 0 1 0 " + f(P2) + "L" + f(E2) + "A" + W + " " + W + " 0 0 0 " + f(E1) + "Z",
    plates: [
      ["lite", OBJ_circle(40, 40, 25), { e: 1.6 }],                                           /* the glass */
      ["deep", "M" + f([P1[0] + 4 * dir[0], P1[1] + 4 * dir[1]]) + "L" + f(E1) + "L" + f(E2) + "L" + f([P2[0] + 4 * dir[0], P2[1] + 4 * dir[1]]) + "Z", { e: 0 }],   /* the handle */
    ],
  };
}

/* ---- Chapter 5: Fire Service Features - a fire hydrant (Madison's own suggestion; a helmet read as a hat): the nut on top, the bonnet, the
   barrel, the two fat side outlets, the base flange. (Appendix C, Fire Hydrant Locations, wants a different object now.) ---- */
{
  CHAPTER_OBJ["Chapter 5: Fire Service Features"] = {
    d: OBJ_poly([[38, 4], [62, 4], [62, 22], [76, 24], [76, 46], [72, 48], [94, 50], [94, 76], [80, 78], [82, 94], [18, 94], [20, 78], [6, 76], [6, 50], [28, 48], [24, 46], [24, 24], [38, 22]],
      [4, 4, 3, 7, 4, 2, 5, 5, 3, 5, 5, 3, 5, 5, 2, 4, 7, 3]),
    plates: [
      ["body", OBJ_rrect(24, 22, 52, 56, 3), { e: 0 }],                                      /* the body */
      ["shade", OBJ_poly([[24, 24], [76, 24], [76, 46], [24, 46]], 4), { e: 0 }],           /* the bonnet */
      ["deep", OBJ_rrect(38, 4, 24, 20, 3), { e: 0 }],                                       /* the nut */
      ["lite", OBJ_rrect(32, 48, 10, 30, 3), { e: 0 }],                                      /* the light down its barrel */
      ["deep", OBJ_rrect(6, 50, 12, 26, 3), { e: 0 }],                                       /* the outlet caps */
      ["deep", OBJ_rrect(82, 50, 12, 26, 3), { e: 0 }],
      ["deep", OBJ_rrect(18, 78, 64, 16, 3), { e: 0 }],                                      /* the base flange */
    ],
  };
}
