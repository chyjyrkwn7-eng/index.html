/* ---- OPTION B for Chapter 63 (NOT merged: the merge reads part-*.js only). 384.93 round 9 shipped option A (the oxidizer's
   flame-over-circle, in part-4.js) and rendered B for Madison; 384.121 redraws B so he can pick: the oxygen mask - a clear green cup
   shaped to the nose and chin with its nose clip, the white elastic strap leaving both sides, and the corrugated tube from its
   foot curling away to its connector. To ship B, replace the Chapter 63 block in part-4.js with this block, then run snap.py and the
   merge. ---- */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const cup = S.grow(S.poly([[44, 14], [62, 46], [26, 46]]), 10);
  const strapL = S.tube([30, 36], [16, 36], [7, 46], () => 3.6, 16), strapR = S.tube([58, 36], [72, 36], [81, 46], () => 3.6, 16);
  const P0 = [44, 60], P1 = [44, 90], P2 = [74, 87];
  const tube = S.tube(P0, P1, P2, () => 6.2, 24);
  const conn = S.box(72, 79, 18, 15, 4);
  const all = S.union([cup, strapL, strapR, tube, conn], 1.5);
  const q = t => [(1 - t) * (1 - t) * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0], (1 - t) * (1 - t) * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]];
  let ribs = "";
  for(let i = 3; i <= 15; i++){ const t = i / 18, a = q(t - .01), b = q(t + .01), dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy), nx = -dy / l, ny = dx / l, p = q(t), h = 4.8;
    ribs += "M" + (p[0] + nx * h).toFixed(2) + " " + (p[1] + ny * h).toFixed(2) + "L" + (p[0] - nx * h).toFixed(2) + " " + (p[1] - ny * h).toFixed(2); }
  const L = (f) => S.loops(f, BB).map(S.pathOf).join("");
  CHAPTER_OBJ["Chapter 63: Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids"] = {
    d: S.shape(all, BB),
    col: "#2FA36B",
    base: "field",
    plates: [
      ["cream", L(S.minus(S.grow(S.union([strapL, strapR]), .3), cup)), { dome: .8, col: "#F3F5F6" }],                               /* the white strap */
      ["glass", S.shape(S.minus(S.grow(tube, .3), cup), BB), { dome: 1.2, col: "#D6E6EC" }],                                         /* the tube */
      ["glass", ribs, { ln: 1.5, cut: .8, paint: 0 }],                                                                  /* its corrugations */
      ["field", S.shape(S.grow(conn, .3), BB), { z: .4, bev: .7, dome: .6, col: "#1F7A4D" }],                           /* the connector */
      ["field", S.shape(S.grow(cup, .3), BB), { dome: 2.8 }],                                                           /* the clear green cup */
      ["deep", L(S.minus(S.grow(cup, .3), S.grow(cup, -3))), { z: .4, bev: .8 }],                                       /* its soft rim */
      ["steel", OBJ_rrect(38, 16, 12, 5, 2.5), { z: .4, bev: .6 }],                                                    /* the nose clip */
    ],
  };
}
