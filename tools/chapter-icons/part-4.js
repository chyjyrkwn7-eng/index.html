/* Phase 2, part 4 (build 384.61): Chapters 54, 55, 56, 58, 59, 60, 61, 62, 63, 64. Drawn to tools/chapter-badges-brief.md.
   Palette c = { field, lite, body, shade, ink }; 96 x 96 box, paths only, no ids, no filters. */

/* Chapter 54 - Corrosive Materials: a dropper over a metal slab, its drop already eaten a crater into it. */
CHAPTER_ICON["Chapter 54: Corrosive Materials"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M8 67H88V91H8Z" fill="${c.body}" ${K}/>
<path d="M9.2 82H86.8V89.8H9.2Z" fill="${c.shade}"/>
<path d="M26 67C26 72 30.5 73 32.5 71C33.5 79 40 85 48 85S62.5 79 63.5 71C65.5 73 70 72 70 67Z" fill="${c.field}"/>
<path d="M26 67C26 72 30.5 73 32.5 71C33.5 79 40 85 48 85S62.5 79 63.5 71C65.5 73 70 72 70 67" fill="none" ${k}/>
<path d="M15 77.5a3 3 0 1 0 .1 0ZM79.5 75a3.4 3.4 0 1 0 .1 0Z" fill="${c.field}" ${k}/>
<path d="M38 22C35 12 40 5 48 5S61 12 58 22Z" fill="${c.body}" ${K}/>
<path d="M48 5C56 5 61 12 58 22H51.5C54 14 52.5 8.5 48 5Z" fill="${c.shade}"/>
<path d="M42 19C40.6 14.6 42 11 44.6 8.6" fill="none" stroke="${c.lite}" stroke-width="2.6"/>
<path d="M33 22H63V29H33Z" fill="${c.shade}" ${K}/>
<path d="M40 29H56V42L51.5 51H44.5L40 42Z" fill="${c.lite}" ${K}/>
<path d="M43.5 37H52.5V42L50 47.5H46L43.5 42Z" fill="${c.field}" ${k}/>
<path d="M48 52.5C50 55.6 53.4 57.6 53.4 61.4A5.4 5.4 0 0 1 42.6 61.4C42.6 57.6 46 55.6 48 52.5Z" fill="${c.field}" ${k}/>
<path d="M30 60.5a3.4 3.4 0 1 0 .1 0ZM70 58a4 4 0 1 0 .1 0Z" fill="${c.lite}" ${k}/>`;
};

/* Chapter 55 - Cryogenic Fluids: a snowflake, six chunky arms with a branch pair and a crystal tip on each, a hex hub with the enamel in it. */
CHAPTER_ICON["Chapter 55: Cryogenic Fluids"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`;
  const f = (v) => +v.toFixed(1), d2r = Math.PI / 180;
  let ink = "", lit = "", shd = "", tips = "";
  for (let i = 0; i < 6; i++) {
    const a = (i * 60 - 90) * d2r, dx = Math.cos(a), dy = Math.sin(a), bucket = (dx + dy > .3) ? "s" : "l";
    let seg = `M48 48L${f(48 + dx * 38)} ${f(48 + dy * 38)}`;
    for (const s of [-1, 1]) {
      const b = (i * 60 - 90 + s * 55) * d2r, bx = 48 + dx * 25, by = 48 + dy * 25;
      seg += `M${f(bx)} ${f(by)}L${f(bx + Math.cos(b) * 14)} ${f(by + Math.sin(b) * 14)}`;
    }
    ink += seg; if (bucket === "s") shd += seg; else lit += seg;
    const px = -dy, py = dx, cx = 48 + dx * 38, cy = 48 + dy * 38;
    tips += `M${f(cx - dx * 5)} ${f(cy - dy * 5)}L${f(cx + px * 4.8)} ${f(cy + py * 4.8)}L${f(cx + dx * 6.4)} ${f(cy + dy * 6.4)}L${f(cx - px * 4.8)} ${f(cy - py * 4.8)}Z`;
  }
  const hex = (r) => "M" + [0, 1, 2, 3, 4, 5].map(i => `${f(48 + r * Math.cos((i * 60 - 90) * d2r))} ${f(48 + r * Math.sin((i * 60 - 90) * d2r))}`).join("L") + "Z";
  return `
<path d="${ink}" fill="none" stroke="${c.ink}" stroke-width="9.4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="${lit}" fill="none" stroke="${c.body}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="${shd}" fill="none" stroke="${c.shade}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="${tips}" fill="${c.lite}" ${K}/>
<path d="${hex(13)}" fill="${c.body}" ${K} stroke-linejoin="round"/>
<path d="${hex(6.4)}" fill="${c.field}" stroke="${c.ink}" stroke-width="1.6" stroke-linejoin="round"/>`;
};

/* Chapter 56 - Explosives and Fireworks: a stick rocket climbing to the upper right, a burst of sparks at its nose. The art is
   drawn upright and turned in the function. */
CHAPTER_ICON["Chapter 56: Explosives and Fireworks"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const a = 38 * Math.PI / 180, cs = Math.cos(a), sn = Math.sin(a), PX = 46, PY = 52, S = 1.2;
  const P = (x, y) => `${+(PX + (x * cs - y * sn) * S).toFixed(1)} ${+(PY + (x * sn + y * cs) * S).toFixed(1)}`;
  const R = (d) => d.replace(/(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)/g, (m, x, y) => P(+x, +y));
  let rays = "", cores = "";
  for (const [deg, len] of [[0, 17], [-40, 12], [40, 12], [-80, 17], [80, 17], [-120, 12], [120, 12]]) {
    const t = deg * Math.PI / 180, ux = Math.sin(t), uy = -Math.cos(t);
    const seg = `M${R(`${+(ux * 7).toFixed(1)} ${+(-31 + uy * 7).toFixed(1)}`)}L${R(`${+(ux * len).toFixed(1)} ${+(-31 + uy * len).toFixed(1)}`)}`;
    rays += seg; if (len > 10) cores += seg;
  }
  return `
<path d="${rays}" fill="none" stroke="${c.ink}" stroke-width="7" stroke-linecap="round"/>
<path d="${rays}" fill="none" stroke="${c.body}" stroke-width="3.6" stroke-linecap="round"/>
<path d="${cores}" fill="none" stroke="${c.lite}" stroke-width="3.6" stroke-linecap="round"/>
<path d="${R("M-2.4 22L-2.4 40L2.4 40L2.4 22Z")}" fill="${c.shade}" ${k}/>
<path d="${R("M-7 11L-15 25L-15 29L-7 25Z")}" fill="${c.body}" ${K}/>
<path d="${R("M7 11L15 25L15 29L7 25Z")}" fill="${c.shade}" ${K}/>
<path d="${R("M-7.5 23L-7.5 0C-7.5 -8 -3.5 -14 0 -20C3.5 -14 7.5 -8 7.5 0L7.5 23Z")}" fill="${c.body}" ${K}/>
<path d="${R("M2.5 -15C5.5 -10 7.5 -6 7.5 0L7.5 23L2.5 23Z")}" fill="${c.shade}"/>
<path d="${R("M-4 -4L-4 18")}" fill="none" stroke="${c.lite}" stroke-width="2.4"/>
<path d="${R("M-7.5 4L7.5 4L7.5 11L-7.5 11Z")}" fill="${c.field}" ${k}/>
<path d="${R("M-5 23L5 23L4 28L-4 28Z")}" fill="${c.shade}" ${k}/>`;
};

/* Chapter 58 - Flammable Gases and Flammable Cryogenic Fluids: a gas burner, a crown of flame tongues standing on its head. */
CHAPTER_ICON["Chapter 58: Flammable Gases and Flammable Cryogenic Fluids"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const f = (v) => +v.toFixed(1);
  const tongue = (x, y, h, w, l) => `M${f(x - w / 2)} ${y}C${f(x - w / 2)} ${f(y - h * .42)} ${f(x + l * .4 - w * .1)} ${f(y - h * .6)} ${f(x + l)} ${f(y - h)}C${f(x + l * .6 + w * .5)} ${f(y - h * .6)} ${f(x + w / 2)} ${f(y - h * .38)} ${f(x + w / 2)} ${y}Z`;
  const spec = [[21, 62, 20, 15, -3], [75, 62, 20, 15, 3], [30, 57, 30, 16, -2], [66, 57, 30, 16, 2], [48, 55, 40, 18, 0]];
  let out = "", inner = "";
  for (const [x, y, h, w, l] of spec) {
    out += `\n<path d="${tongue(x, y, h, w, l)}" fill="${c.body}" ${K}/>`;
    inner += tongue(x, y + 1, h * .55, w * .5, l * .5);
  }
  return out + `
<path d="${inner}" fill="${c.lite}"/>
<path d="M41 74H55V86H41Z" fill="${c.shade}" ${K}/>
<path d="M31 84H65L67 91H29Z" fill="${c.body}" ${K}/>
<path d="M14 60V71C14 78 28 82 48 82S82 78 82 71V60Z" fill="${c.body}" ${K}/>
<path d="M82 60V71C82 78 68 82 48 82C62 78 66 70 66 60Z" fill="${c.shade}"/>
<path d="M14 60C14 54 28 51 48 51S82 54 82 60C82 66 68 69 48 69S14 66 14 60Z" fill="${c.lite}" ${K}/>
<path d="M32 60C32 58 38 57 48 57S64 58 64 60C64 62 58 63 48 63S32 62 32 60Z" fill="${c.field}" ${k}/>`;
};

/* Chapter 59 - Flammable Solids: a lit match, the stick laid across the badge and the flame standing straight up from its head. */
CHAPTER_ICON["Chapter 59: Flammable Solids"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const f = (v) => +v.toFixed(1);
  const T = [15, 86], H = [54, 51], L = Math.hypot(H[0] - T[0], H[1] - T[1]), ux = (H[0] - T[0]) / L, uy = (H[1] - T[1]) / L, nx = -uy, ny = ux, w = 4.6;
  const q = (p, s) => `${f(p[0] + nx * w * s)} ${f(p[1] + ny * w * s)}`;
  const stick = `M${q(T, -1)}L${q(H, -1)}L${q(H, 1)}L${q(T, 1)}Z`;
  const half = `M${f(T[0])} ${f(T[1])}L${f(H[0])} ${f(H[1])}L${q(H, 1)}L${q(T, 1)}Z`;
  const hl = `M${f(T[0] + ux * 10 - nx * 2.2)} ${f(T[1] + uy * 10 - ny * 2.2)}L${f(H[0] - ux * 8 - nx * 2.2)} ${f(H[1] - uy * 8 - ny * 2.2)}`;
  return `
<path d="M57 48C41 46 36 31 46 19C50 14 53 10 51 4C64 11 76 24 72 37C70 44 65 48 57 48Z" fill="${c.field}" ${K}/>
<path d="M57 43C48 42 45 34 50 27C52 24 55 22 54 18C62 23 67 30 65 36C64 40 61 43 57 43Z" fill="${c.body}"/>
<path d="${stick}" fill="${c.lite}" ${K}/>
<path d="${half}" fill="${c.shade}"/>
<path d="${hl}" fill="none" stroke="${c.lite}" stroke-width="1.6"/>
<path d="M57 40C64.5 40 70 45.6 70 52.6C70 60 64.5 65 57 65C49.5 65 44 60 44 52.6C44 45.6 49.5 40 57 40Z" fill="${c.ink}" ${K}/>
<path d="M50 49C51.4 46 54 44.6 57 44.6" fill="none" stroke="${c.lite}" stroke-width="2.6"/>`;
};

/* Chapter 60 - Highly Toxic and Toxic Materials: a skull and crossbones, the standard toxic mark, kept graphic. */
CHAPTER_ICON["Chapter 60: Highly Toxic and Toxic Materials"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const f = (v) => +v.toFixed(1);
  const bone = (x1, y1, x2, y2) => `M${x1} ${y1}L${x2} ${y2}`;
  const b1 = bone(15, 57, 81, 83), b2 = bone(81, 57, 15, 83);
  // each end: two lobes
  const lobe = (x, y, ux, uy) => { const nx = -uy, ny = ux, o = 4.4, r = 4.6; return [[x + nx * o, y + ny * o], [x - nx * o, y - ny * o]].map(([a, b]) => `M${f(a - r)} ${f(b)}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`).join(""); };
  const d1 = Math.hypot(66, 26), u1 = [66 / d1, 26 / d1], u2 = [66 / d1, -26 / d1];
  const knobs = lobe(15, 57, u1[0], u1[1]) + lobe(81, 83, u1[0], u1[1]) + lobe(81, 57, -u2[0], -u2[1]) + lobe(15, 83, -u2[0], -u2[1]);
  return `
<path d="${b1}${b2}" fill="none" stroke="${c.ink}" stroke-width="11.4" stroke-linecap="round"/>
<path d="${knobs}" fill="${c.lite}" ${K}/>
<path d="${b1}${b2}" fill="none" stroke="${c.lite}" stroke-width="6.6" stroke-linecap="round"/>
<path d="M48 6C66 6 77 19 77 33C77 42 72 48 67 52V59C67 62 65 64 62 64H34C31 64 29 62 29 59V52C24 48 19 42 19 33C19 19 30 6 48 6Z" fill="${c.body}" ${K}/>
<path d="M48 6C66 6 77 19 77 33C77 42 72 48 67 52V59C67 62 65 64 62 64H55C58 56 62 50 63 40C64 27 58 14 48 6Z" fill="${c.shade}"/>
<path d="M26 28C28 19 34 13 41 10" fill="none" stroke="${c.lite}" stroke-width="3"/>
<path d="M35 31C41 31 45 35 45 40C45 45 41 48 36 48C31 48 27 45 27 40C27 35 30 31 35 31ZM61 31C66 31 69 35 69 40C69 45 65 48 60 48C55 48 51 45 51 40C51 35 55 31 61 31Z" fill="${c.ink}"/>
<path d="M48 49L43.6 56.6H52.4Z" fill="${c.ink}" stroke="${c.ink}" stroke-width="1.6"/>
<path d="M40 59.5V64M48 59.5V64M56 59.5V64" fill="none" ${k}/>`;
};

/* Chapter 61 - Liquefied Petroleum Gases: a propane tank lying on its two legs, valve guard and hand wheel on top. */
CHAPTER_ICON["Chapter 61: Liquefied Petroleum Gases"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M20 62L16 85H34L30 62Z" fill="${c.shade}" ${K}/>
<path d="M66 62L62 85H80L76 62Z" fill="${c.shade}" ${K}/>
<path d="M10 84H40V90H10ZM56 84H86V90H56Z" fill="${c.body}" ${K}/>
<path d="M37 24C37 20 40 18 44 18H52C56 18 59 20 59 24V34H37Z" fill="${c.body}" ${K}/>
<path d="M52 18C56 18 59 20 59 24V34H52Z" fill="${c.shade}"/>
<path d="M30 30H66V35H30Z" fill="${c.shade}" ${K}/>
<path d="M44 18V12H52V18Z" fill="${c.shade}" ${k}/>
<path d="M36 10.5H60" fill="none" stroke="${c.ink}" stroke-width="5.4" stroke-linecap="round"/>
<path d="M36 10.5H60" fill="none" stroke="${c.lite}" stroke-width="2.6" stroke-linecap="round"/>
<path d="M30 33H66C80 33 88 40 88 50C88 60 80 67 66 67H30C16 67 8 60 8 50C8 40 16 33 30 33Z" fill="${c.body}" ${K}/>
<path d="M88 50C88 60 80 67 66 67H30C16 67 8 60 8 50C8 54 16 61 30 61H66C78 61 85 56 88 50Z" fill="${c.shade}"/>
<path d="M24 41C28 38.6 34 38 41 38.2" fill="none" stroke="${c.lite}" stroke-width="3.4"/>
<path d="M27 33.5V66.5M69 33.5V66.5" fill="none" stroke="${c.ink}" stroke-width="1.8"/>
<path d="M78 50a5 5 0 1 0 .1 0Z" fill="${c.lite}" ${k}/>`;
};

/* Chapter 62 - Organic Peroxides: a molecule of three atoms, one pair held by a double bond (the O-O of a peroxide), no letters. */
CHAPTER_ICON["Chapter 62: Organic Peroxides"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const f = (v) => +v.toFixed(1);
  const A = [23, 29, 13], B = [45, 69, 17], C = [79, 37, 13];
  const unit = (p, q) => { const d = Math.hypot(q[0] - p[0], q[1] - p[1]); return [(q[0] - p[0]) / d, (q[1] - p[1]) / d]; };
  const uab = unit(A, B), ubc = unit(B, C), nab = [-uab[1], uab[0]];
  const dbl = (o) => `M${f(A[0] + nab[0] * o)} ${f(A[1] + nab[1] * o)}L${f(B[0] + nab[0] * o)} ${f(B[1] + nab[1] * o)}`;
  const sph = (p, tone) => {
    const [x, y, r] = p;
    return `<path d="M${f(x - r)} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z" fill="${c.body}" ${K}/>
<path d="M${f(x + r * .78)} ${f(y - r * .62)}A${r} ${r} 0 0 1 ${f(x - r * .45)} ${f(y + r * .9)}A${f(r * 1.05)} ${f(r * 1.05)} 0 0 0 ${f(x + r * .78)} ${f(y - r * .62)}Z" fill="${c.shade}"/>
<path d="M${f(x - r * .62)} ${f(y - r * .1)}C${f(x - r * .62)} ${f(y - r * .48)} ${f(x - r * .4)} ${f(y - r * .66)} ${f(x - r * .08)} ${f(y - r * .7)}" fill="none" stroke="${c.lite}" stroke-width="${r > 14 ? 4 : 3.4}"/>`;
  };
  return `
<path d="${dbl(-4.6)}${dbl(4.6)}" fill="none" stroke="${c.ink}" stroke-width="6.6" stroke-linecap="round"/>
<path d="M${f(B[0])} ${f(B[1])}L${f(C[0])} ${f(C[1])}" fill="none" stroke="${c.ink}" stroke-width="8.6" stroke-linecap="round"/>
<path d="${dbl(-4.6)}${dbl(4.6)}" fill="none" stroke="${c.lite}" stroke-width="3" stroke-linecap="round"/>
<path d="M${f(B[0])} ${f(B[1])}L${f(C[0])} ${f(C[1])}" fill="none" stroke="${c.shade}" stroke-width="5" stroke-linecap="round"/>
${sph(A)}
${sph(C)}
${sph(B)}`;
};

/* Chapter 63 - Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids: the oxidizer mark - a flame standing on a ring. */
CHAPTER_ICON["Chapter 63: Oxidizers, Oxidizing Gases and Oxidizing Cryogenic Fluids"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M48 66C26 66 19 52 26 40C30 33 37 30 35 18C34 13 36 9 40 4C42 14 52 19 62 29C72 38 78 52 69 59C64 64 56 66 48 66Z" fill="${c.body}" ${K}/>
<path d="M48 61C36 61 32 52 36 45C39 40 44 38 43 30C53 35 63 43 61 51C60 57 55 61 48 61Z" fill="${c.lite}"/>
<path d="M48 54.5a19 19 0 1 0 .1 0Z" fill="${c.body}" ${K}/>
<path d="M63.6 62.6A19 19 0 0 1 37.1 89.1A22 22 0 0 0 63.6 62.6Z" fill="${c.shade}"/>
<path d="M48 64.9a8.6 8.6 0 1 0 .1 0Z" fill="${c.field}" ${K}/>
<path d="M33.4 71.5A15 15 0 0 1 43.4 60" fill="none" stroke="${c.lite}" stroke-width="3"/>`;
};

/* Chapter 64 - Pyrophoric Materials: a pile of powder that has lit itself, a flame (and a lick beside it) rising off its peak.
   The flame is a window onto the enamel, as in Chapter 57. */
CHAPTER_ICON["Chapter 64: Pyrophoric Materials"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M38 66C25 64 25 50 32 43C35 39 35 34 33 29C41 34 47 40 45 49C44 56 44 62 38 66Z" fill="${c.field}" ${K}/>
<path d="M56 68C41 68 35 54 41 41C45 33 52 28 50 17C49 13 51 9 55 4C58 14 66 20 72 29C79 38 77 50 71 58C67 64 62 68 56 68Z" fill="${c.field}" ${K}/>
<path d="M56 63C48 63 45 55 48.5 47C51 42 55.5 39 54.5 31C61 36 67 42 66 50C65 57 61 63 56 63Z" fill="${c.body}"/>
<path d="M6 90C23 88 31 80 38 69C42 62 54 62 58 69C65 80 73 88 90 90Z" fill="${c.body}" ${K}/>
<path d="M58 69C65 80 73 88 90 90L52 90C56 82 59 76 58 69Z" fill="${c.shade}"/>
<path d="M17 85C25 81 31 76 37 68" fill="none" stroke="${c.lite}" stroke-width="2.6"/>
<path d="M14 76a2.6 2.6 0 1 0 .1 0ZM80 74a2.6 2.6 0 1 0 .1 0ZM86 82.5a2.2 2.2 0 1 0 .1 0Z" fill="${c.lite}" ${k}/>
<path d="M50 80a1.8 1.8 0 1 0 .1 0ZM62 84a1.8 1.8 0 1 0 .1 0ZM44 86a1.8 1.8 0 1 0 .1 0Z" fill="${c.ink}"/>`;
};
