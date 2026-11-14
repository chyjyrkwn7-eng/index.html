/* Police academy unit badges as RAISED PINS (build 384.121). Madison: "Speaking of badges, yes, we are going to update the police academy
   badges as well. Same concept, match what they are talking about." Each of the academy's 24 units is the one object its unit is about,
   drawn exactly as the Fire Code chapters are (tools/chapter-objects/README.md: the silhouette is the object, sculpture not stickers, natural
   colours, parts at least 5 across, every piece joins). The unit's badge id (its title) and its unlock rule are untouched; only the art.
   Local helpers live inside this one block so nothing leaks into the page. */
{
  const S = OBJ_SDF, BB = [0, 0, 100, 100];
  const sh = f => S.shape(f, BB);                                  /* one loop: the largest */
  const all = f => S.loops(f, BB).map(S.pathOf).join("");          /* every loop (README rule 8d) */
  const g = (f, r) => S.grow(f, r == null ? .3 : r);
  const rot = (pts, a, cx, cy) => { const c = Math.cos(a * Math.PI / 180), s = Math.sin(a * Math.PI / 180);
    return pts.map(([x, y]) => [cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c]); };
  const rbox = (cx, cy, w, h, a, r) => S.grow(S.poly(rot([[cx - w / 2 + r, cy - h / 2 + r], [cx + w / 2 - r, cy - h / 2 + r], [cx + w / 2 - r, cy + h / 2 - r], [cx - w / 2 + r, cy + h / 2 - r]], a, cx, cy)), r);
  const lineP = (pts) => "M" + pts.map(p => p[0].toFixed(2) + " " + p[1].toFixed(2)).join("L");
  const ring = (cx, cy, ro, ri) => S.minus(S.circle(cx, cy, ro), S.circle(cx, cy, ri));
  const arcPts = (cx, cy, rx, ry, a0, a1, n) => { const o = []; for(let i = 0; i <= n; i++){ const a = (a0 + (a1 - a0) * i / n) * Math.PI / 180; o.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); } return o; };
  const half = (f, yMin, yMax) => S.inter(f, S.box(-10, yMin, 120, yMax - yMin, 0));

  /* ---- Professionalism and Ethics - the scales: a brass balance, its post on a stepped base, the beam, and two pans hung level (an
     officer's conduct weighed, impartial). ---- */
  {
    const post = S.box(45, 16, 10, 62, 3), base = S.union([S.box(16, 78, 68, 19, 5), S.box(32, 72, 36, 9, 3)], 1);
    const beam = S.box(8, 19, 84, 7, 3.5), knob = S.circle(50, 12, 7);
    const hang = S.union([S.capsule(13, 23, 6, 54, 2.6), S.capsule(13, 23, 30, 54, 2.6), S.capsule(87, 23, 70, 54, 2.6), S.capsule(87, 23, 94, 54, 2.6)]);
    const pans = S.union([half(S.ellipse(18, 54, 17, 14), 53, 80), half(S.ellipse(82, 54, 17, 14), 53, 80)]);
    const sil = S.union([post, base, beam, knob, hang, pans], 1.2);
    CHAPTER_OBJ["Professionalism and Ethics"] = {
      d: sh(sil), base: "brass",
      plates: [
        ["brass", all(g(hang)), { dome: .6 }],                                                      /* the hangers */
        ["brass", all(g(pans)), { dome: 1.6 }],                                                     /* the pans */
        ["brass", "M4 56H32M68 56H96", { ln: 1.2, cut: .6, paint: 0 }],                              /* their rims */
        ["brass", sh(g(post)), { z: .5, bev: .8, dome: .6 }],                                       /* the post */
        ["brass", sh(g(beam)), { z: .8, bev: .8, dome: .5 }],                                       /* the beam */
        ["brass", sh(g(knob)), { z: 1, bev: .8, dome: 1.2 }],                                       /* its finial */
        ["wood", sh(g(base)), { z: .4, bev: .8, dome: .4, col: "#5A3620" }],                        /* the base */
        ["wood", "M22 82H78", { ln: 1.4, cut: .7, paint: 0 }],
      ],
    };
  }

  /* ---- Professional Policing - the patrol cap: the navy crown, the black band, the gloss peak, the gold cap badge on its front. ---- */
  {
    const crown = S.union([S.ellipse(50, 30, 47, 17), S.box(15, 30, 70, 26, 2)], 6);
    const band = S.box(15, 52, 70, 14, 2), peak = half(S.ellipse(50, 64, 38, 15), 64, 90);
    const sil = S.union([crown, band, peak], 1.5);
    const badge = S.poly([[50, 25], [60, 30], [58, 43], [50, 49], [42, 43], [40, 30]]);
    CHAPTER_OBJ["Professional Policing"] = {
      d: sh(sil), col: "#22305A", base: "field",
      plates: [
        ["field", sh(g(crown)), { dome: 2 }],                                                       /* the crown */
        ["field", "M8 34Q50 48 92 34", { ln: 1.4, cut: .8, paint: 0 }],                              /* its welt */
        ["rubber", sh(g(band)), { z: .4, bev: .7, dome: .3, col: "#15171B" }],                     /* the band */
        ["brass", "M18 59H82", { ln: 2.4, z: .3, bev: .5 }],                                        /* the gold chin cord */
        ["rubber", sh(g(peak)), { z: .6, bev: .8, dome: 1, col: "#111316" }],                      /* the peak */
        ["brass", sh(S.grow(badge, 2)), { z: 1.2, bev: .7, gem: .8, gw: 3 }],                       /* the cap badge */
        ["brass", OBJ_circle(50, 37, 4.6), { z: .4, bev: .5, dome: .6, col: "#F0C75A" }],
      ],
    };
  }

  /* ---- Fitness, Wellness, and Stress Management - a kettlebell: the round bell, its flat foot, the arched handle and the hole a hand
     goes through. ---- */
  {
    const bell = S.circle(50, 62, 34), foot = S.box(30, 88, 40, 9, 3);
    const arch = S.union([S.capsule(22, 46, 20, 18, 8), S.capsule(78, 46, 80, 18, 8), S.capsule(26, 10, 74, 10, 8)], 10);
    const hole = S.minus(S.box(30, 18.5, 40, 26, 8), S.grow(bell, 2.5));
    const t = S.trace(S.minus(S.union([bell, foot, arch], 4), hole), BB);
    CHAPTER_OBJ["Fitness, Wellness, and Stress Management"] = {
      d: t.d, holes: t.holes, col: "#2F6FD6", base: "field",
      plates: [
        ["field", all(S.minus(S.minus(g(arch), S.grow(bell, -1)), hole)), { dome: 1.4, col: "#285FB8" }],   /* the handle */
        ["field", sh(S.union([g(bell), g(foot)], 3)), { dome: 2.4 }],                              /* the bell */
        ["field", OBJ_circle(50, 63, 25), { ln: 1.4, cut: .7, paint: 0 }],                          /* its cast seam */
        ["rubber", sh(g(foot)), { z: .2, bev: .6, col: "#2E3238" }],                                /* its foot */
      ],
    };
  }

  /* ---- TCOLE Rules - the Texas peace officer's star in its ring: the licence every rule is about. A five-point silver star whose points
     stand past a brass ring, the gaps between the arms open. ---- */
  {
    const star = (ro, ri) => { const p = []; for(let i = 0; i < 10; i++){ const a = (-90 + i * 36) * Math.PI / 180, r = i % 2 ? ri : ro; p.push([50 + r * Math.cos(a), 52 + r * Math.sin(a)]); } return p; };
    const st = S.grow(S.poly(star(45, 18)), 2), rg = ring(50, 52, 38, 29);
    const t = S.trace(S.union([st, rg], 1), BB);
    CHAPTER_OBJ["TCOLE Rules"] = {
      d: t.d, holes: t.holes, col: "#C9CFD6", base: "steel",
      plates: [
        ["brass", all(g(rg)), { dome: 1.2 }],                                                       /* the ring */
        ["field", all(ring(50, 52, 36, 31)), { z: -.3, bev: .5, col: "#1F3B7A" }],                  /* its enamel band */
        ["steel", sh(g(st)), { z: 1, bev: .9, gem: 1.8, gw: 5 }],                                   /* the star, faceted */
        ["brass", OBJ_circle(50, 52, 9), { z: .6, bev: .7, dome: 1 }],                              /* the boss at its heart */
      ],
    };
  }

  /* ---- Multiculturalism and Human Relations - a desk globe: the blue world with its raised green land, the brass meridian round it,
     the stem and the foot. ---- */
  {
    const ball = S.circle(48, 42, 31), mer = S.inter(ring(48, 42, 39, 34), S.box(48, -10, 60, 120, 0));
    const stem = S.box(44, 76, 8, 12, 2), foot = S.ellipse(48, 91, 24, 6.5);
    const sil = S.union([ball, mer, stem, foot, S.capsule(48, 3, 48, 7, 3.4)], 1.5);
    const land = S.union([S.poly([[30, 22], [44, 17], [50, 26], [44, 36], [47, 46], [40, 52], [32, 42], [26, 34]]), S.poly([[54, 46], [66, 42], [70, 52], [62, 66], [55, 60]]),
                          S.poly([[56, 20], [68, 18], [74, 28], [64, 32]])]);
    CHAPTER_OBJ["Multiculturalism and Human Relations"] = {
      d: sh(sil), col: "#2C7FD0", base: "brass",
      plates: [
        ["field", sh(g(ball)), { dome: 2.6 }],                                                      /* the world */
        ["field", all(S.grow(land, 1.6)), { z: .6, bev: .9, dome: .6, col: "#3E9B4F" }],           /* its land */
        ["brass", all(g(mer)), { z: .6, bev: .8, dome: .6 }],                                       /* the meridian */
        ["brass", sh(g(S.union([stem, foot], 1))), { z: .3, bev: .8, dome: .6, col: "#B8862F" }], /* the stem and foot */
      ],
    };
  }

  /* ---- Racial Profiling - the traffic stop: a black-and-white patrol car from the side, its light bar red and blue, the windows, the
     white doors, two wheels. ---- */
  {
    const body = S.box(4, 46, 92, 26, 8), cab = S.grow(S.poly([[28, 46], [36, 30], [64, 30], [74, 46]]), 3), bar = S.box(39, 21, 22, 8, 3);
    const w1 = S.circle(25, 72, 12), w2 = S.circle(75, 72, 12);
    const sil = S.union([body, cab, bar, w1, w2], 1.5);
    CHAPTER_OBJ["Racial Profiling"] = {
      d: sh(sil), col: "#1E2126", base: "field",
      plates: [
        ["field", sh(g(S.union([body, cab], 1.5))), { dome: 1 }],                                   /* the body */
        ["cream", sh(S.inter(S.box(26, 44, 48, 26, 2), S.union([body, cab], 1.5))), { z: .3, bev: .6, col: "#F2F3F5" }],   /* the white doors */
        ["glass", all(S.union([S.grow(S.poly([[33, 44], [39, 33], [49, 33], [49, 44]]), 1), S.grow(S.poly([[52, 44], [52, 33], [62, 33], [69, 44]]), 1)])), { z: -.6, bev: .6, col: "#2C3E50" }],   /* the windows */
        ["field", "M50 47V68", { ln: 1.2, cut: .7, paint: 0 }],                                       /* the door seam */
        ["red", sh(g(S.box(39, 21, 11, 8, 3))), { z: .6, bev: .6, dome: .8, col: "#E3342F" }],     /* the light bar */
        ["water", sh(g(S.box(50, 21, 11, 8, 3))), { z: .6, bev: .6, dome: .8, col: "#2D6FE0" }],
        ["rubber", all(g(S.union([w1, w2]))), { z: .5, bev: .9, dome: .8 }],                        /* the wheels */
        ["steel", OBJ_circle(25, 72, 5.5) + OBJ_circle(75, 72, 5.5), { z: .9, bev: .6, dome: .8 }],
        ["glow", OBJ_rrect(88, 52, 6, 6, 2), { z: .4, bev: .5, dome: .5, col: "#FFF4C2" }],         /* the headlamp */
      ],
    };
  }

  /* ---- US and Texas Constitution and Rights - the parchment: a scroll unrolled between its two rolls, its lines, the quill across it. ---- */
  {
    const sheet = S.box(18, 14, 56, 72, 1), r1 = S.capsule(13, 13, 79, 13, 7.5), r2 = S.capsule(13, 87, 79, 87, 7.5);
    const quill = S.tube([60, 82], [72, 46], [94, 8], t => 2.8 + 6.5 * Math.sin(Math.PI * Math.min(1, Math.max(0, (t - .12) / .88))) * (t > .12 ? 1 : 0), 24);
    const sil = S.union([sheet, r1, r2, quill], 1.2);
    let lines = ""; for(let y = 28; y <= 72; y += 7) lines += "M26 " + y + "H" + (y > 60 ? 50 : 62);
    CHAPTER_OBJ["US and Texas Constitution and Rights"] = {
      d: sh(sil), col: "#E8D3A2", base: "field",
      plates: [
        ["field", sh(g(sheet)), { dome: .6 }],                                                      /* the sheet */
        ["field", lines, { ln: 1.8, cut: .6, paint: 0 }],                                            /* its lines */
        ["field", all(g(S.union([r1, r2]))), { z: .6, bev: .9, dome: 1.6, col: "#D2B57A" }],      /* the rolls */
        ["cream", sh(S.minus(g(quill), S.union([r1, r2]))), { z: 1, bev: .7, dome: .8, col: "#F7F5EF" }],   /* the quill */
        ["cream", lineP([[63, 76], [74, 44], [91, 13]]), { ln: 1, cut: .5, paint: 0 }],              /* its shaft */
        ["red", OBJ_circle(30, 76, 6.5), { z: .9, bev: .7, dome: 1, col: "#B3282D" }],              /* the seal */
      ],
    };
  }

  /* ---- Penal Code - the judge's gavel on its sound block: the dark wooden head with its brass bands, the handle, the block. ---- */
  {
    const a = -15, head = rbox(24, 38, 30, 60, a, 7), handle = S.capsule(30, 37, 93, 20, 5.2), block = S.union([S.ellipse(55, 73, 42, 10), S.box(13, 73, 84, 16, 3), S.ellipse(55, 89, 42, 9)], 1);
    const sil = S.union([head, handle, block], 1.2);
    const off = d => [24 - d * Math.sin(a * Math.PI / 180), 38 + d * Math.cos(a * Math.PI / 180)];
    const bandA = S.inter(S.grow(head, .3), rbox(off(-19)[0], off(-19)[1], 40, 6, a, 1)), bandB = S.inter(S.grow(head, .3), rbox(off(19)[0], off(19)[1], 40, 6, a, 1));
    CHAPTER_OBJ["Penal Code"] = {
      d: sh(sil), col: "#6B3A1E", base: "field",
      plates: [
        ["wood", sh(g(block)), { dome: .6, col: "#A8703C" }],                                       /* the sound block */
        ["wood", "M14 76Q55 92 96 76", { ln: 1.2, cut: .6, paint: 0 }],
        ["field", sh(S.minus(g(handle), head)), { z: .6, bev: .8, dome: .8 }],                      /* the handle */
        ["field", sh(g(head)), { z: 1, bev: 1, dome: 1.6 }],                                         /* the head */
        ["brass", all(S.union([bandA, bandB])), { z: 1.3, bev: .5, dome: .5 }],                     /* its brass bands */
      ],
    };
  }

  /* ---- Code of Criminal Procedure and Bill of Rights - the law book: a thick bound volume, its cover with raised gold bands, the page
     block down its side, the ribbon marker. ---- */
  {
    const cover = S.grow(S.poly([[16, 12], [64, 8], [64, 88], [16, 92]]), 3), pages = S.grow(S.poly([[64, 8], [83, 14], [83, 84], [64, 88]]), 2);
    const ribbon = S.poly([[70, 84], [77, 85], [77, 98], [73.5, 95], [70, 98]]);
    const sil = S.union([cover, pages, ribbon], 1);
    CHAPTER_OBJ["Code of Criminal Procedure and Bill of Rights"] = {
      d: sh(sil), col: "#8A2430", base: "field",
      plates: [
        ["cream", sh(g(pages)), { dome: .4, col: "#EFE6D2" }],                                      /* the pages */
        ["cream", "M69 18V84M73.5 19V83M78 20V82", { ln: 1, cut: .5, paint: 0 }],
        ["red", sh(g(ribbon)), { z: .3, bev: .5, col: "#B3282D" }],                                 /* the ribbon */
        ["field", sh(g(cover)), { dome: 1.4 }],                                                     /* the cover */
        ["brass", sh(S.grow(S.poly([[22, 24], [58, 21], [58, 27], [22, 30]]), 1)), { z: .8, bev: .5, dome: .4 }],   /* its gold bands */
        ["brass", sh(S.grow(S.poly([[22, 70], [58, 68], [58, 74], [22, 76]]), 1)), { z: .8, bev: .5, dome: .4 }],
        ["field", sh(S.grow(S.poly([[26, 38], [54, 36], [54, 60], [26, 62]]), 2)), { z: .5, bev: .7, col: "#701C26" }],   /* the title panel */
        ["brass", OBJ_circle(40, 49, 5.5), { z: 1, bev: .6, dome: .8 }],
      ],
    };
  }

  /* ---- Arrest, Search, and Seizure - rigid handcuffs: two steel cuffs joined by the rigid black grip bar, its steel swivel caps. ---- */
  {
    const c1 = ring(25, 64, 23, 12), c2 = ring(75, 64, 23, 12);
    const bar = S.box(14, 20, 72, 22, 7), cap1 = S.box(8, 22, 14, 18, 4), cap2 = S.box(78, 22, 14, 18, 4);
    const t = S.trace(S.union([c1, c2, bar, cap1, cap2], 1.5), BB);
    CHAPTER_OBJ["Arrest, Search, and Seizure"] = {
      d: t.d, holes: t.holes, col: "#2A2D33", base: "field",
      plates: [
        ["steel", all(S.minus(g(S.union([c1, c2])), bar)), { dome: 1.6 }],                         /* the cuffs */
        ["steel", lineP(arcPts(25, 64, 17.5, 17.5, -40, 220, 30)) + lineP(arcPts(75, 64, 17.5, 17.5, -40, 220, 30)), { ln: 1, cut: .5, paint: 0 }],   /* their ratchet line */
        ["field", sh(g(bar)), { z: .6, bev: .9, dome: 1 }],                                          /* the grip bar */
        ["field", "M30 26V36M38 26V36M46 26V36M54 26V36M62 26V36M70 26V36", { ln: 1.4, cut: .7, paint: 0 }],   /* its grip */
        ["steel", all(g(S.union([cap1, cap2]))), { z: .9, bev: .7, dome: .8 }],                       /* the swivel caps */
      ],
    };
  }

  /* ---- Victims of Crime - care: a red heart with a plaster across it, its pad and holes. ---- */
  {
    const heart = S.union([S.circle(30, 32, 23), S.circle(70, 32, 23), S.poly([[9, 40], [91, 40], [50, 96]])], 6);
    const plaster = rbox(50, 50, 90, 21, -28, 6);
    const sil = S.union([heart, plaster], 1);
    CHAPTER_OBJ["Victims of Crime"] = {
      d: sh(sil), col: "#D8343F", base: "field",
      plates: [
        ["field", sh(g(heart)), { dome: 2.6 }],                                                     /* the heart */
        ["cream", sh(g(plaster)), { z: .7, bev: .8, dome: .5, col: "#E9C9A0" }],                   /* the plaster */
        ["cream", sh(rbox(50, 50, 22, 14, -28, 3)), { z: 1, bev: .6, dome: .4, col: "#F6E7D2" }],   /* its pad */
        ["cream", OBJ_circle(27, 61, 1.6) + OBJ_circle(23, 54, 1.6) + OBJ_circle(77, 46, 1.6) + OBJ_circle(73, 39, 1.6), { z: -.5, bev: .3, col: "#C9A47A" }],
      ],
    };
  }

  /* ---- Missing and Exploited Children - a teddy bear: round ears, the head with its muzzle, the body and its tummy, the paws. ---- */
  {
    const head = S.circle(50, 31, 21), ears = S.union([S.circle(31, 15, 9), S.circle(69, 15, 9)]), body = S.ellipse(50, 67, 23, 24);
    const arms = S.union([S.capsule(30, 55, 15, 70, 8), S.capsule(70, 55, 85, 70, 8)]), legs = S.union([S.circle(32, 87, 10), S.circle(68, 87, 10)]);
    const sil = S.union([head, ears, body, arms, legs], 3);
    CHAPTER_OBJ["Missing and Exploited Children"] = {
      d: sh(sil), col: "#A86A38", base: "field",
      plates: [
        ["field", all(g(S.union([body, arms, legs], 3))), { dome: 1.6 }],                           /* the body, arms and legs */
        ["field", all(g(ears)), { dome: 1 }],                                                       /* the ears */
        ["cream", all(S.union([S.circle(31, 15, 4.6), S.circle(69, 15, 4.6)])), { z: -.5, bev: .5, col: "#E2B98A" }],   /* their insides */
        ["field", sh(g(head)), { z: .6, bev: 1, dome: 2 }],                                         /* the head */
        ["cream", OBJ_ellipse(50, 39, 10, 7.5), { z: .5, bev: .7, dome: .9, col: "#E2B98A" }],     /* the muzzle */
        ["rubber", OBJ_ellipse(50, 35.5, 4, 3), { z: .6, bev: .4, dome: .6 }],                      /* the nose */
        ["rubber", OBJ_circle(41, 26, 2.8) + OBJ_circle(59, 26, 2.8), { z: .4, bev: .4, dome: .6 }],   /* the eyes */
        ["cream", OBJ_ellipse(50, 70, 11, 12), { z: .4, bev: .7, dome: .6, col: "#E2B98A" }],      /* the tummy */
        ["cream", OBJ_circle(32, 88, 5) + OBJ_circle(68, 88, 5), { z: .3, bev: .5, dome: .4, col: "#E2B98A" }],   /* the foot pads */
      ],
    };
  }

  /* ---- Identity Crimes - a fingerprint: the oval pad of a print, its whorl of ridges. ---- */
  {
    const T = 25, E0 = S.ellipse(50, 51, 32, 46), pad = (x, y) => { const p = rot([[x, y]], -T, 50, 51)[0]; return E0(p[0], p[1]); };   /* a thumbprint, leaning */
    let ridges = "";
    for(let k = 0; k < 6; k++){ const rx = 7 + k * 5, ry = 10 + k * 6.2, cy = 50 + k * .6;
      ridges += lineP(rot(arcPts(50, cy, rx, ry, 200 + (k % 2) * 14, 520 - (k % 3) * 18, 36), T, 50, 51)); }
    ridges += lineP(rot(arcPts(50, 50, 2.5, 4.5, 0, 340, 14), T, 50, 51));
    CHAPTER_OBJ["Identity Crimes"] = {
      d: sh(pad), col: "#6F8FD0", base: "field",
      plates: [
        ["field", sh(g(pad)), { dome: 1.6 }],                                                       /* the pad */
        ["deep", ridges, { ln: 2.8, z: .7, bev: .6 }],                                               /* its ridges, raised and inked */
      ],
    };
  }

  /* ---- Sexual Assault and Family Violence - the home: a house with its purple roof (the colour of family-violence awareness), the
     chimney, the door, and a raised heart on its front. ---- */
  {
    const roof = S.grow(S.poly([[50, 8], [92, 46], [8, 46]]), 3), walls = S.box(16, 42, 68, 52, 3), chim = S.box(66, 12, 11, 24, 2);
    const sil = S.union([roof, walls, chim], 1.2);
    const heart = S.union([S.circle(43, 58, 7), S.circle(57, 58, 7), S.poly([[36.5, 61], [63.5, 61], [50, 76]])], 2);
    CHAPTER_OBJ["Sexual Assault and Family Violence"] = {
      d: sh(sil), col: "#7B4BB0", base: "field",
      plates: [
        ["cream", sh(g(walls)), { dome: .6, col: "#EFE7DA" }],                                      /* the walls */
        ["field", sh(S.minus(g(chim), roof)), { z: .3, bev: .6, col: "#5E3A8A" }],                 /* the chimney */
        ["field", sh(g(roof)), { z: .8, bev: .9, dome: 1.2 }],                                      /* the roof */
        ["field", "M18 40L50 12L82 40", { ln: 1.2, cut: .6, paint: 0 }],
        ["field", sh(heart), { z: 1, bev: .8, dome: 1.2, col: "#9A5FD0" }],                         /* the heart */
        ["wood", OBJ_rrect(42, 79, 16, 15, [3, 3, 0, 0]), { z: -.4, bev: .5, col: "#6E4A2E" }],     /* the door */
      ],
    };
  }

  /* ---- Verbal Communication - the conversation: two speech bubbles, the blue one in front with its three dots, the white one behind. ---- */
  {
    const b1 = S.union([S.box(4, 18, 62, 44, 14), S.poly([[14, 56], [28, 58], [10, 76]])], 2);
    const b2 = S.union([S.box(42, 40, 54, 40, 14), S.poly([[86, 74], [74, 78], [92, 94]])], 2);
    const sil = S.union([b1, b2], 1);
    CHAPTER_OBJ["Verbal Communication"] = {
      d: sh(sil), col: "#2E7AD6", base: "field",
      plates: [
        ["cream", sh(S.minus(g(b2), S.grow(b1, 1.2))), { dome: 1, col: "#EEF1F4" }],                /* the white bubble, behind */
        ["field", sh(g(b1)), { z: 1, bev: 1, dome: 1.6 }],                                           /* the blue bubble */
        ["cream", OBJ_circle(22, 40, 4.4) + OBJ_circle(35, 40, 4.4) + OBJ_circle(48, 40, 4.4), { z: .6, bev: .5, dome: .9, col: "#F4F7FB" }],   /* its dots */
      ],
    };
  }

  /* ---- Civil Process and Liability - the papers served: a manila envelope, its flap closed with a red wax seal. ---- */
  {
    const env = rbox(50, 52, 86, 60, 10, 4);
    const P = rot([[7, 22], [93, 22], [50, 58]], 10, 50, 52);
    const seal = S.circle(P[2][0], P[2][1], 10);
    const sil = S.union([env, seal], 1);
    CHAPTER_OBJ["Civil Process and Liability"] = {
      d: sh(sil), col: "#D8B472", base: "field",
      plates: [
        ["field", sh(g(env)), { dome: .8 }],                                                        /* the envelope */
        ["field", sh(S.inter(S.grow(S.poly(P), 1.5), env)), { z: .6, bev: .8, dome: .4, col: "#CBA35E" }],   /* its flap */
        ["red", sh(g(seal)), { z: 1.2, bev: .8, dome: 1.2, col: "#B3282D" }],                       /* the seal */
        ["red", OBJ_circle(P[2][0], P[2][1], 5.6), { ln: 1.2, cut: .6, paint: 0 }],
      ],
    };
  }

  /* ---- Consular Notification - the foreign national's passport: a navy booklet, its gold globe emblem raised on the cover, the gold
     band where its name would be, the spine's fold. ---- */
  {
    const A = -22, bk = rbox(50, 50, 58, 80, A, 5), R = (x, y) => rot([[x, y]], A, 50, 50)[0];
    const c = R(50, 42), band = rbox(R(50, 72)[0], R(50, 72)[1], 32, 6, A, 2.5);
    const glob = rx => lineP(arcPts(0, 0, rx, 13, -90, 270, 40).map(([x, y]) => R(50 + x, 42 + y)));
    CHAPTER_OBJ["Consular Notification"] = {
      d: sh(bk), col: "#1F2F5C", base: "field",
      plates: [
        ["field", sh(g(bk)), { dome: 1 }],                                                          /* the cover */
        ["field", lineP([R(26, 10), R(26, 90)]), { ln: 1.4, cut: .7, paint: 0 }],                   /* the spine's fold */
        ["brass", OBJ_circle(c[0], c[1], 13), { ln: 3, z: .9, bev: .5 }],                          /* the globe */
        ["brass", glob(6) + lineP([R(37, 42), R(63, 42)]) + lineP([R(39.5, 35), R(60.5, 35)]) + lineP([R(39.5, 49), R(60.5, 49)]), { ln: 2, z: .9, bev: .4 }],   /* its meridians and parallels */
        ["brass", sh(band), { z: .7, bev: .5, dome: .3 }],                                          /* the gold band */
      ],
    };
  }

  /* ---- Crisis Intervention Training - the life ring thrown to someone in crisis: orange and white quarters, its grab line. ---- */
  {
    const lr = ring(50, 50, 46, 17);
    const t = S.trace(lr, BB);
    const quarter = (a0) => S.inter(lr, S.poly([[50, 50], [50 + 70 * Math.cos(a0 * Math.PI / 180), 50 + 70 * Math.sin(a0 * Math.PI / 180)], [50 + 70 * Math.cos((a0 + 45) * Math.PI / 180), 50 + 70 * Math.sin((a0 + 45) * Math.PI / 180)], [50 + 70 * Math.cos((a0 + 90) * Math.PI / 180), 50 + 70 * Math.sin((a0 + 90) * Math.PI / 180)]]));
    CHAPTER_OBJ["Crisis Intervention Training"] = {
      d: t.d, holes: t.holes, col: "#F05A22", base: "field",
      plates: [
        ["field", all(g(lr)), { dome: 2.4 }],                                                        /* the ring */
        ["cream", all(S.union([quarter(-22.5), quarter(157.5)])), { z: .05, bev: .3, dome: 0, col: "#F4F5F6" }],   /* its white quarters */
        ["cream", lineP(arcPts(50, 50, 31.5, 31.5, 0, 360, 72)), { ln: 2.6, z: .5, bev: .5, col: "#D8C9A8" }],   /* the grab line */
      ],
    };
  }

  /* ---- De-Escalation - calm: a white dove in flight with an olive sprig. ---- */
  {
    const body = S.union([S.cone(30, 52, 74, 62, 13, 7), S.circle(24, 44, 10)], 5);
    const wing = S.grow(S.poly([[38, 50], [52, 18], [74, 6], [70, 28], [62, 50]]), 4);
    const tail = S.grow(S.poly([[70, 58], [94, 52], [94, 74], [72, 68]]), 2.5);
    const beak = S.grow(S.poly([[11, 46], [17, 41], [17, 50]]), 1);
    const sprig = S.union([S.capsule(13, 49, 8, 66, 2.6), S.ellipse(5, 60, 5, 3.4), S.ellipse(14, 64, 5, 3.4), S.ellipse(8, 70, 4.4, 3)], 1);
    const sil = S.union([body, wing, tail, beak, sprig], 1.2);
    CHAPTER_OBJ["De-Escalation"] = {
      d: sh(sil), col: "#EEF1F5", base: "field",
      plates: [
        ["field", sh(S.minus(g(tail), body)), { dome: .8, col: "#DCE2EA" }],                        /* the tail */
        ["field", "M74 60L93 56M74 64L93 64M74 68L93 71", { ln: 1, cut: .5, paint: 0 }],
        ["field", sh(g(body)), { dome: 1.8 }],                                                      /* the body */
        ["field", sh(S.minus(g(wing), S.grow(body, -2))), { z: .8, bev: .9, dome: 1 }],             /* the wing */
        ["field", "M50 26L64 46M58 18L68 40M66 12L70 30", { ln: 1.1, cut: .6, paint: 0 }],          /* its feathers */
        ["hot", sh(g(beak)), { z: .3, bev: .4, col: "#F2A23A" }],                                  /* the beak */
        ["rubber", OBJ_circle(23, 42, 2.4), { z: .4, bev: .3, dome: .5 }],                          /* the eye */
        ["field", all(g(S.minus(sprig, beak))), { z: .4, bev: .5, dome: .5, col: "#6E9A3A" }],     /* the olive sprig */
      ],
    };
  }

  /* ---- Health and Safety Code - controlled substances: a capsule, half red and half white, its seam. ---- */
  {
    const cap = S.capsule(24, 78, 76, 22, 19);
    const ax = [0.6802, -0.7330];
    const side = (x, y) => -((x - 50) * ax[0] + (y - 50) * ax[1]);
    CHAPTER_OBJ["Health and Safety Code"] = {
      d: sh(cap), col: "#D8343F", base: "field",
      plates: [
        ["cream", sh(S.inter(g(cap), side)), { dome: 2.4, col: "#F4F5F7" }],                       /* the white half */
        ["field", sh(S.inter(g(cap), (x, y) => -side(x, y))), { dome: 2.4 }],                      /* the red half */
        ["field", lineP([[50 - 19 * .733, 50 - 19 * .6802], [50 + 19 * .733, 50 + 19 * .6802]]), { ln: 1.6, cut: .9, paint: 0 }],   /* the seam */
      ],
    };
  }

  /* ---- Interacting with Deaf or Hard-of-Hearing - the ear, and the hearing aid that sits behind it. ---- */
  {
    const ear = S.union([S.ellipse(46, 40, 28, 34), S.circle(44, 78, 13)], 10);
    const aid = S.tube([72, 22], [92, 40], [76, 70], () => 6, 20);
    const sil = S.union([ear, aid], 1.5);
    CHAPTER_OBJ["Interacting with Deaf or Hard-of-Hearing"] = {
      d: sh(sil), col: "#E2A47E", base: "field",
      plates: [
        ["cream", sh(S.minus(g(aid), ear)), { dome: 1.2, col: "#C9CED6" }],                         /* the hearing aid */
        ["field", sh(g(ear)), { dome: 1.6 }],                                                       /* the ear */
        ["field", lineP(arcPts(46, 40, 20, 26, 160, 400, 40)), { ln: 2.2, cut: 1.2, paint: 0 }],    /* the rim of the helix */
        ["field", sh(S.union([S.ellipse(46, 50, 10, 14), S.circle(40, 60, 6)], 3)), { z: -1.2, bev: 1, col: "#C98763" }],   /* the bowl */
        ["field", sh(S.circle(44, 80, 7)), { z: .3, bev: .8, dome: .6, col: "#E9B08C" }],          /* the lobe */
      ],
    };
  }

  /* ---- Radio Communications, Alerts, and TCIC-TLETS - the handheld radio: its antenna, the channel knob, the screen, the speaker grille,
     the push-to-talk key. ---- */
  {
    const body = S.box(28, 30, 44, 66, 8), ant = S.capsule(39, 32, 39, 4, 4.2), knob = S.box(54, 18, 13, 14, 3), ptt = S.box(22, 44, 8, 20, 3);
    const sil = S.union([body, ant, knob, ptt], 1.2);
    let grille = ""; for(let y = 66; y <= 88; y += 5) grille += "M37 " + y + "H63";
    CHAPTER_OBJ["Radio Communications, Alerts, and TCIC-TLETS"] = {
      d: sh(sil), col: "#3B4049", base: "field",
      plates: [
        ["rubber", sh(S.minus(g(ant), body)), { dome: .8 }],                                         /* the antenna */
        ["steel", sh(S.minus(g(knob), body)), { z: .2, bev: .6, dome: .6 }],                         /* the channel knob */
        ["steel", "M57 19V30M61 19V30M65 19V30", { ln: 1, cut: .5, paint: 0 }],
        ["field", sh(g(body)), { dome: 1.2 }],                                                      /* the body */
        ["rubber", sh(S.minus(g(ptt), body)), { z: .3, bev: .5, col: "#3A3E45" }],                  /* the talk key */
        ["glass", OBJ_rrect(36, 38, 28, 18, 3), { z: -.5, bev: .5, col: "#7FC3A4" }],               /* the screen */
        ["field", grille, { ln: 2.2, cut: 1, paint: 0 }],                                            /* the speaker grille */
        ["red", OBJ_rrect(47, 25, 6, 5, 1.5), { z: 1, bev: .4, dome: .5, col: "#E3342F" }],        /* the alert key */
      ],
    };
  }

  /* ---- Traumatic Brain Injury - the brain, from the side: its folds, the cerebellum under the back, the stem. ---- */
  {
    const cer = S.union([S.ellipse(48, 42, 44, 33), S.circle(30, 54, 18)], 6), cbl = S.ellipse(70, 72, 16, 11), stem = S.capsule(56, 70, 60, 94, 6);
    const sil = S.union([cer, cbl, stem], 2);
    const folds = "M14 40Q22 26 34 30Q38 18 52 20Q62 12 72 22Q84 22 86 36M20 56Q30 46 40 52Q46 40 58 44Q66 34 78 42M34 68Q44 60 54 64Q62 56 72 58M50 30Q52 38 46 44M66 28Q64 36 70 40M30 40Q34 46 30 50";
    CHAPTER_OBJ["Traumatic Brain Injury"] = {
      d: sh(sil), col: "#E59AB0", base: "field",
      plates: [
        ["field", sh(S.minus(g(stem), cer)), { dome: .8, col: "#C26A86" }],                          /* the stem */
        ["field", sh(S.minus(g(cbl), cer)), { z: .2, bev: .6, dome: 1, col: "#C97A92" }],            /* the cerebellum */
        ["field", "M60 72Q70 66 82 72M58 78Q70 74 82 78", { ln: 1.2, cut: .7, paint: 0 }],
        ["field", sh(g(cer)), { z: .4, bev: .9, dome: 2.4 }],                                       /* the cerebrum */
        ["field", folds, { ln: 2, cut: 1.1, paint: 0 }],                                             /* its folds */
      ],
    };
  }

  /* ---- Phonetic Alphabet and Military Time - the field watch: olive straps, the steel case and crown, the dark dial with its four
     markers and hands (no numerals). ---- */
  {
    const c = S.circle(50, 50, 29), s1 = S.box(35, 2, 30, 30, 4), s2 = S.box(35, 68, 30, 30, 4), crown = S.box(76, 45, 9, 10, 2.5);
    const sil = S.union([c, s1, s2, crown], 1.5);
    CHAPTER_OBJ["Phonetic Alphabet and Military Time"] = {
      d: sh(sil), col: "#62723A", base: "field",
      plates: [
        ["field", all(S.minus(g(S.union([s1, s2])), c)), { dome: .6 }],                             /* the straps */
        ["field", "M41 8H59M41 14H59M41 86H59M41 92H59", { ln: 1.4, cut: .7, paint: 0 }],
        ["steel", sh(S.minus(g(crown), c)), { z: .3, bev: .6, dome: .6 }],                           /* the crown */
        ["steel", sh(g(c)), { z: .6, bev: .9, dome: 1.2 }],                                         /* the case */
        ["rubber", OBJ_circle(50, 50, 22), { z: -.4, bev: .6, col: "#1D2125" }],                    /* the dial */
        ["cream", OBJ_rrect(48, 30, 4, 7, 1.5) + OBJ_rrect(48, 63, 4, 7, 1.5) + OBJ_rrect(30, 48, 7, 4, 1.5) + OBJ_rrect(63, 48, 7, 4, 1.5), { z: .3, bev: .3, col: "#E8E2C9" }],   /* the markers */
        ["cream", "M50 50L50 34M50 50L61 56", { ln: 2.6, z: .6, bev: .4, col: "#F4F1E4" }],         /* the hands */
        ["red", OBJ_circle(50, 50, 2.8), { z: .9, bev: .3, dome: .4, col: "#E3342F" }],
      ],
    };
  }
}
