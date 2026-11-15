/* Phase 2, part 3 (build 384.61): chapters 34, 35, 36, 37, 38, 39, 40, 50, 51, 53. Drawn to tools/chapter-badges-brief.md;
   each is (c) => markup, palette c = { field, lite, body, shade, ink }, 96 x 96 box, paths only, no ids, no filters. */

/* Chapter 34 - a tyre seen face on: the lugged tread ring, the sidewall with its inner groove and a catch-light, the wheel and its five bolts. */
CHAPTER_ICON["Chapter 34: Tire Rebuilding and Tire Storage"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const N = 16, R = 44.6, r = 40, f = (n) => n.toFixed(1);
  const pt = (rad, a) => f(48 + rad * Math.cos(a)) + " " + f(48 + rad * Math.sin(a));
  let tread = "M" + pt(r, 0);
  for (let i = 0; i < N; i++) {
    const a0 = i * 2 * Math.PI / N, w = 2 * Math.PI / N;
    tread += "L" + pt(r, a0 + w * .06) + "L" + pt(R, a0 + w * .12) + "A" + R + " " + R + " 0 0 1 " + pt(R, a0 + w * .88) + "L" + pt(r, a0 + w * .94) + "A" + r + " " + r + " 0 0 1 " + pt(r, a0 + w);
  }
  tread += "Z";
  const O = (x, y, r) => `M${(x - r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x + r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x - r).toFixed(1)} ${y.toFixed(1)}Z`;
  const ring = (rad) => O(48, 48, rad);
  let bolts = "";
  for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + i * 2 * Math.PI / 5; const x = 48 + 10.5 * Math.cos(a), y = 48 + 10.5 * Math.sin(a); bolts += O(x, y, 2.4); }
  const arc = (rad, a0, a1) => `M${pt(rad, a0)}A${rad} ${rad} 0 0 1 ${pt(rad, a1)}`;
  return `
<path d="${tread}" fill="${c.ink}" ${K}/>
<path d="${ring(35)}" fill="${c.shade}" ${K}/>
<path d="${ring(29)}" fill="none" stroke="${c.ink}" stroke-width="2"/>
<path d="${arc(32, Math.PI * 1.08, Math.PI * 1.55)}" fill="none" stroke="${c.lite}" stroke-width="3.4" stroke-linecap="round"/>
<path d="${ring(20)}" fill="${c.body}" ${K}/>
<path d="${ring(14)}" fill="${c.lite}" ${k}/>
<path d="${ring(5)}" fill="${c.body}" ${k}/>
<path d="${bolts}" fill="${c.ink}"/>`;
};

/* Chapter 35 - a welder's mask: the shell, the dark lens with its glint, the side pivots, and the spark flying off the work. */
CHAPTER_ICON["Chapter 35: Welding and Other Hot Work"] = (c) => {
  const O = (x, y, r) => `M${(x - r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x + r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x - r).toFixed(1)} ${y.toFixed(1)}Z`;
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M10 48C10 24 24 12 44 12S78 24 78 48V68C78 80 70 88 58 88H30C18 88 10 80 10 68Z" fill="${c.body}" ${K}/>
<path d="M78 48C78 24 64 12 44 12C66 20 62 50 66 88H58C70 88 78 80 78 68Z" fill="${c.shade}"/>
<path d="M18 40C20 26 30 19 42 18" fill="none" stroke="${c.lite}" stroke-width="3.4" stroke-linecap="round"/>
<path d="M20 38H68C71 38 72 40 72 43V57C72 61 70 64 66 64H24C21 64 20 61 20 58Z" fill="${c.ink}" ${K}/>
<path d="M28 59L40 43H49L37 59Z" fill="${c.field}"/>
<path d="M52 59L61 47H64L55 59Z" fill="${c.field}"/>
<path d="${O(10, 50, 4.4)}" fill="${c.lite}" ${k}/>
<path d="M26 74H62" fill="none" stroke="${c.shade}" stroke-width="2.4" stroke-linecap="round"/>
<path d="M81 7L85 14L92 18L85 22L81 29L77 22L70 18L77 14Z" fill="${c.lite}" stroke="${c.ink}" stroke-width="1.8" stroke-linejoin="round"/>`;
};

/* Chapter 36 - an anchor: ring, stock, shank, the curved arms ending in flukes. Marinas; the one object that says the water. */
CHAPTER_ICON["Chapter 36: Marinas"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`;
  return `
<path d="M15 56C15 74 29 83 48 83S81 74 81 56" fill="none" stroke="${c.ink}" stroke-width="19.4" stroke-linecap="round"/>
<path d="M15 56C15 74 29 83 48 83S81 74 81 56" fill="none" stroke="${c.body}" stroke-width="14.6" stroke-linecap="round"/>
<path d="M48 83C66 83 81 74 81 56" fill="none" stroke="${c.shade}" stroke-width="14.6" stroke-linecap="round"/>
<path d="M13 36L28 58H4Z" fill="${c.body}" stroke="${c.ink}" stroke-width="2.4" stroke-linejoin="round"/>
<path d="M83 36L92 58H68Z" fill="${c.shade}" stroke="${c.ink}" stroke-width="2.4" stroke-linejoin="round"/>
<path d="M38 24H58V80H38Z" fill="${c.body}" ${K}/>
<path d="M48 24H58V80H48Z" fill="${c.shade}"/>
<path d="M38 24H58V80H38Z" fill="none" ${K}/>
<path d="M20 29C20 26 22 24 25 24H71C74 24 76 26 76 29S74 36 71 36H25C22 36 20 32 20 29Z" fill="${c.body}" ${K}/>
<path d="M48 24H71C74 24 76 26 76 29S74 36 71 36H48Z" fill="${c.shade}"/>
<path d="M48 5C56 5 61 9 61 15S56 24 48 24S35 21 35 15S40 5 48 5ZM48 10C44 10 41 12 41 15S44 20 48 20S55 18 55 15S52 10 48 10Z" fill="${c.lite}" fill-rule="evenodd" ${K}/>
<path d="M8 47L5 55" fill="none" stroke="${c.lite}" stroke-width="2.4" stroke-linecap="round"/>`;
};

/* Chapter 37 - a spool of thread: two flanges, the wound thread (the enamel colour) between them, a loose end curling away. */
CHAPTER_ICON["Chapter 37: Combustible Fibers"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M24 20H72V76H24Z" fill="${c.field}" ${K}/>
<path d="M24 30L40 20M24 42L56 20M24 54L68 22M24 66L72 32M30 76L72 44M46 76L72 58" fill="none" ${k}/>
<path d="M62 20H72V76H62Z" fill="${c.shade}" opacity=".5"/>
<path d="M14 8H82C85 8 86 10 86 12V20H10V12C10 10 11 8 14 8Z" fill="${c.body}" ${K}/>
<path d="M10 76H86V84C86 86 85 88 82 88H14C11 88 10 86 10 84Z" fill="${c.body}" ${K}/>
<path d="M60 8H86V20H60Z" fill="${c.shade}"/>
<path d="M60 76H86V88H60Z" fill="${c.shade}"/>
<path d="M14 8H82C85 8 86 10 86 12V20H10V12C10 10 11 8 14 8Z" fill="none" ${K}/>
<path d="M10 76H86V84C86 86 85 88 82 88H14C11 88 10 86 10 84Z" fill="none" ${K}/>
<path d="M72 46C86 44 92 52 87 60C84 65 77 63 79 57" fill="none" stroke="${c.ink}" stroke-width="6.4" stroke-linecap="round"/>
<path d="M72 46C86 44 92 52 87 60C84 65 77 63 79 57" fill="none" stroke="${c.field}" stroke-width="3" stroke-linecap="round"/>
<path d="M15 13H44" fill="none" stroke="${c.lite}" stroke-width="2.6" stroke-linecap="round"/>
<path d="M15 81H34" fill="none" stroke="${c.lite}" stroke-width="2.6" stroke-linecap="round"/>`;
};

/* Chapter 38 - a conical laboratory flask with its liquid and bubbles rising from the neck. */
CHAPTER_ICON["Chapter 38: Higher Education Laboratories"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const O = (x, y, r) => `M${(x - r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x + r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x - r).toFixed(1)} ${y.toFixed(1)}Z`;
  const dot = O;
  return `
<path d="M38 26H58V46L84 80C88 86 85 90 79 90H17C11 90 8 86 12 80L38 46Z" fill="${c.body}" ${K}/>
<path d="M58 26V46L84 80C88 86 85 90 79 90H52C70 82 66 50 58 46Z" fill="${c.shade}"/>
<path d="M24 66C32 61 38 71 48 66S64 62 72 66L82 80C86 86 83 90 79 90H17C11 90 8 86 12 80Z" fill="${c.field}" ${k}/>
<path d="M24 66C32 61 38 71 48 66S64 62 72 66" fill="none" stroke="${c.lite}" stroke-width="2.4" stroke-linecap="round"/>
<path d="M33 22C33 19 35 17 38 17H58C61 17 63 19 63 22S61 27 58 27H38C35 27 33 25 33 22Z" fill="${c.lite}" ${K}/>
<path d="M42 31V45L22 74" fill="none" stroke="${c.lite}" stroke-width="3" stroke-linecap="round"/>
<path d="${dot(47, 11, 4)}" fill="${c.lite}" ${k}/>
<path d="${dot(58, 8, 3)}" fill="${c.lite}" ${k}/>
<path d="${dot(40, 6.5, 2.4)}" fill="${c.lite}" ${k}/>
<path d="${dot(40, 80, 4)}${dot(54, 83, 3)}${dot(62, 76, 2.4)}" fill="${c.lite}" ${k}/>`;
};

/* Chapter 39 - a plain leaf with a drop falling beside it: processing and extraction, drawn as the plant and what is drawn from it. A generic leaf, not a particular plant. */
CHAPTER_ICON["Chapter 39: Processing and Extraction Facilities"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M16 84L10 90" fill="none" stroke="${c.ink}" stroke-width="7" stroke-linecap="round"/>
<path d="M16 84L10 90" fill="none" stroke="${c.body}" stroke-width="3.4" stroke-linecap="round"/>
<path d="M16 82C8 50 30 16 82 10C86 46 62 80 16 82Z" fill="${c.body}" ${K}/>
<path d="M82 10C86 46 62 80 16 82C50 70 70 48 82 10Z" fill="${c.shade}"/>
<path d="M16 82C8 50 30 16 82 10C86 46 62 80 16 82Z" fill="none" ${K}/>
<path d="M16 82C40 62 62 40 80 14" fill="none" stroke="${c.ink}" stroke-width="2.2" stroke-linecap="round"/>
<path d="M30 68C26 58 28 50 33 44M44 56C42 46 46 38 52 33M58 44C58 36 62 30 67 26" fill="none" stroke="${c.lite}" stroke-width="2.4" stroke-linecap="round"/>
<path d="M73 52C73 52 61 66 61 74A12 12 0 0 0 85 74C85 66 73 52 73 52Z" fill="${c.field}" stroke="${c.ink}" stroke-width="2.4" stroke-linejoin="round"/>
<path d="M67 73C67 69.6 69.6 66 72 62.6" fill="none" stroke="${c.lite}" stroke-width="2.6" stroke-linecap="round"/>`;
};

/* Chapter 40 - an upright wooden barrel: bulging staves, two hoops, the lid, the bung. The outline bulges in code so the hoops follow it. */
CHAPTER_ICON["Chapter 40: Storage of Distilled Spirits and Wines"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const O = (x, y, r) => `M${(x - r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x + r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x - r).toFixed(1)} ${y.toFixed(1)}Z`;
  const f = (n) => n.toFixed(1), top = 15, bot = 81, E = 7;
  const hw = (y) => 18 + 17 * Math.sin(Math.PI * (y - top) / (bot - top));
  const edge = (side, y0, y1) => { let s = []; for (let i = 0; i <= 8; i++) { const y = y0 + (y1 - y0) * i / 8; s.push(f(48 + side * hw(y)) + " " + f(y)); } return s; };
  const body = "M" + edge(-1, top, bot).join("L") + "A" + hw(bot) + " " + E + " 0 0 0 " + f(48 + hw(bot)) + " " + bot + "L" + edge(1, bot, top).reverse().reverse().join("L") + "A" + hw(top) + " " + E + " 0 0 0 " + f(48 - hw(top)) + " " + top + "Z";
  const band = (y0, y1) => {
    const lo = [], hi = [];
    for (let i = 0; i <= 12; i++) { const u = -1 + 2 * i / 12; lo.push(u); }
    const side = (yy) => lo.map(u => f(48 + u * hw(yy)) + " " + f(yy + E * (1 - u * u))).join("L");
    return "M" + side(y0) + "L" + lo.slice().reverse().map(u => f(48 + u * hw(y1)) + " " + f(y1 + E * (1 - u * u))).join("L") + "Z";
  };
  const rightHalf = "M48 " + (top + E) + "L" + edge(1, top, bot).join("L") + "A" + hw(bot) + " " + E + " 0 0 1 48 " + (bot + E) + "Z";
  return `
<path d="${body}" fill="${c.body}" ${K}/>
<path d="M48 ${top + E}C62 ${top + E} ${f(48 + hw(top))} ${top + 3} ${f(48 + hw(top))} ${top}C${f(48 + hw(50) + 4)} 40 ${f(48 + hw(50) + 4)} 60 ${f(48 + hw(bot))} ${bot}C72 ${bot + E - 1} 58 ${bot + E} 48 ${bot + E}Z" fill="${c.shade}"/>
<path d="${body}" fill="none" ${K}/>
<path d="M36 28C31 42 31 62 36 78M48 22V89M60 28C65 42 65 62 60 78" fill="none" stroke="${c.shade}" stroke-width="1.8" opacity=".9"/>
<path d="${band(26, 34)}" fill="${c.lite}" ${K}/>
<path d="${band(60, 68)}" fill="${c.lite}" ${K}/>
<path d="M30 ${top}a18 7 0 1 0 36 0a18 7 0 1 0 -36 0Z" fill="${c.lite}" ${K}/>
<path d="M37 ${top - .6}C40 ${top - 4} 46 ${top - 5} 52 ${top - 5}" fill="none" stroke="${c.body}" stroke-width="2" stroke-linecap="round"/>
<path d="${O(48, 49.5, 4.6)}" fill="${c.ink}" ${k}/>`;
};

/* Chapter 50 - the hazard placard: four small diamonds making one large diamond. General provisions, so the general symbol, with no letters or numbers. */
CHAPTER_ICON["Chapter 50: Hazardous Materials—General Provisions"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4" stroke-linejoin="round"`, k = `stroke="${c.ink}" stroke-width="1.6" stroke-linejoin="round"`;
  const dia = (cx, cy, d) => `M${cx} ${cy - d}L${cx + d} ${cy}L${cx} ${cy + d}L${cx - d} ${cy}Z`;
  return `
<path d="${dia(48, 25, 20)}" fill="${c.field}" ${K}/>
<path d="${dia(25, 48, 20)}" fill="${c.shade}" ${K}/>
<path d="${dia(71, 48, 20)}" fill="${c.lite}" ${K}/>
<path d="${dia(48, 71, 20)}" fill="${c.body}" ${K}/>
<path d="${dia(48, 25, 8.5)}" fill="${c.lite}" ${k}/>
<path d="${dia(25, 48, 8.5)}" fill="${c.body}" ${k}/>
<path d="${dia(71, 48, 8.5)}" fill="${c.field}" ${k}/>
<path d="${dia(48, 71, 8.5)}" fill="${c.shade}" ${k}/>
<path d="M41 16L48 10.5L55 16" fill="none" stroke="${c.lite}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`;
};

/* Chapter 51 - an aerosol can: domed shoulder, rim, label band, the actuator and the cloud of spray it throws. */
CHAPTER_ICON["Chapter 51: Aerosols"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const O = (x, y, r) => `M${(x - r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x + r).toFixed(1)} ${y.toFixed(1)}A${r} ${r} 0 1 0 ${(x - r).toFixed(1)} ${y.toFixed(1)}Z`;
  const dot = O;
  return `
<path d="M44 36C44 30 49 28 52 28H72C75 28 80 30 80 36V86C80 89 78 90 75 90H49C46 90 44 89 44 86Z" fill="${c.body}" ${K}/>
<path d="M66 29H72C75 29 80 31 80 36V86C80 89 78 90 75 90H66Z" fill="${c.shade}"/>
<path d="M44 52H80V72H44Z" fill="${c.field}" ${K}/>
<path d="M44 58H80" fill="none" stroke="${c.lite}" stroke-width="2.6"/>
<path d="M44 36C44 30 49 28 52 28H72C75 28 80 30 80 36Z" fill="none" ${K}/>
<path d="M52 20H72V28H52Z" fill="${c.shade}" ${K}/>
<path d="M54 10H70V20H54Z" fill="${c.lite}" ${K}/>
<path d="M54 14H44V18H54Z" fill="${c.shade}" ${k}/>
<path d="M49 33V86" fill="none" stroke="${c.lite}" stroke-width="2.8" stroke-linecap="round"/>
<path d="${dot(30, 15, 4.6)}${dot(18, 11, 5.4)}${dot(22, 25, 6.2)}${dot(10, 19, 4.4)}${dot(11, 31, 3.6)}${dot(30, 33, 3.2)}${dot(33, 24, 2.6)}${dot(7, 8, 2.6)}" fill="${c.lite}" stroke="${c.ink}" stroke-width="4.8" stroke-linejoin="round"/>
<path d="${dot(30, 15, 4.6)}${dot(18, 11, 5.4)}${dot(22, 25, 6.2)}${dot(10, 19, 4.4)}${dot(11, 31, 3.6)}${dot(30, 33, 3.2)}${dot(33, 24, 2.6)}${dot(7, 8, 2.6)}" fill="${c.lite}"/>`;
};

/* Chapter 53 - a compressed gas cylinder: domed shoulder, valve with its handwheel and side outlet, the guard collar, the foot ring. */
CHAPTER_ICON["Chapter 53: Compressed Gases"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M24 91V46C24 33 33 28 48 28S72 33 72 46V91Z" fill="${c.body}" ${K}/>
<path d="M60 29.2C68 31.4 72 37 72 46V91H60Z" fill="${c.shade}"/>
<path d="M24 91V46C24 33 33 28 48 28S72 33 72 46V91Z" fill="none" ${K}/>
<path d="M24 52H72V72H24Z" fill="${c.field}" ${K}/>
<path d="M24 58H72" fill="none" stroke="${c.lite}" stroke-width="2.6"/>
<path d="M18 83H78V92H18Z" fill="${c.shade}" ${K}/>
<path d="M38 19H58V30H38Z" fill="${c.shade}" ${K}/>
<path d="M58 20H72V26H58Z" fill="${c.body}" ${K}/>
<path d="M43 12H53V19H43Z" fill="${c.body}" ${K}/>
<path d="M22 4.5H74C77 4.5 78 6.5 78 8.5S77 12.5 74 12.5H22C19 12.5 18 10.5 18 8.5S19 4.5 22 4.5Z" fill="${c.lite}" ${K}/>
<path d="M31 38C29 40 29 43 29 47V76" fill="none" stroke="${c.lite}" stroke-width="3.4" stroke-linecap="round"/>`;
};
