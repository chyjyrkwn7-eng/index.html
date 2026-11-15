/* Phase 2, part 5 (build 384.61): ten chapters drawn to the spec in tools/chapter-badges-brief.md.
   Each is (c) => markup; palette c = { field, lite, body, shade, ink }; 96 x 96 box, paths only, no ids, no filters.
   Pattern used throughout: fill the whole figure first, lay the shade plate over it, then draw the keyline again as an outline-only path
   (so a shade plate never eats half the keyline), then the highlight and small details last. */

/* Chapter 65 - a film reel (cellulose nitrate was film stock): five-hole reel on a hub with a loop of film running off it. */
CHAPTER_ICON["Chapter 65: Pyroxylin (Cellulose Nitrate) Plastics"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const cx = 40, cy = 41, R = 36, rad = (a) => a * Math.PI / 180;
  const pt = (r, a) => [(cx + r * Math.cos(rad(a))).toFixed(1), (cy + r * Math.sin(rad(a))).toFixed(1)];
  const circ = (x, y, r) => `M${(x - r).toFixed(1)} ${y.toFixed(1)}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  let holes = "";
  for (let i = 0; i < 5; i++) { const a = -90 + 72 * i, p = pt(20.8, a); holes += circ(+p[0], +p[1], 7.8); }
  const p1 = pt(R, -40), p2 = pt(R, 150);
  const arc = (r, a, b, w, col) => { const s = pt(r, a), e = pt(r, b); return `<path d="M${s[0]} ${s[1]}A${r} ${r} 0 0 1 ${e[0]} ${e[1]}" fill="none" stroke="${col}" stroke-width="${w}"/>`; };
  /* the film: a strip drawn level then turned 14 degrees about its root, with four sprocket holes along it */
  const t = rad(8), co = Math.cos(t), si = Math.sin(t);
  const tr = (x, y) => [(46 + (x - 46) * co - (y - 76) * si).toFixed(1), (76 + (x - 46) * si + (y - 76) * co).toFixed(1)].join(" ");
  const quad = (x0, y0, x1, y1) => "M" + [tr(x0, y0), tr(x1, y0), tr(x1, y1), tr(x0, y1)].join("L") + "Z";
  const strip = quad(46, 66, 90, 86);
  const perf = [66, 74.6, 83.2].map(x => quad(x, 68.6, x + 4.4, 73.2) + quad(x, 78.8, x + 4.4, 83.4)).join("");
  return `
<path d="${strip}" fill="${c.shade}" ${K}/>
<path d="${perf}" fill="${c.lite}"/>
<path d="${circ(cx, cy, R)}" fill="${c.body}"/>
<path d="M${p1[0]} ${p1[1]}A${R} ${R} 0 0 1 ${p2[0]} ${p2[1]}A${R * 1.3} ${R * 1.3} 0 0 0 ${p1[0]} ${p1[1]}Z" fill="${c.shade}"/>
<path d="${circ(cx, cy, R)}" fill="none" ${K}/>
${arc(R - 4.6, 200, 255, 3.2, c.lite)}
<path d="${holes}" fill="${c.field}" ${k}/>
<path d="${circ(cx, cy, 8)}" fill="${c.lite}" ${K}/>
<path d="${circ(cx, cy, 2.8)}" fill="${c.ink}"/>`;
};

/* Chapter 66 - UNSTABLE (REACTIVE) materials: a stoppered vial being shaken, tipped over with the motion marks either side.
   A vial rather than a bomb on purpose: Chapter 56 owns the firework. The liquid is a window onto the enamel. */
CHAPTER_ICON["Chapter 66: Unstable (Reactive) Materials"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const a = -24 * Math.PI / 180, co = Math.cos(a), si = Math.sin(a);
  /* the vial is drawn upright with absolute M L C pairs only, then every pair is turned about (48,50) */
  const R = (d) => d.replace(/(-?[\d.]+) (-?[\d.]+)/g, (m, x, y) => [(48 + (x - 48) * co - (y - 50) * si).toFixed(1), (50 + (x - 48) * si + (y - 50) * co).toFixed(1)].join(" "));
  const bub = (x, y, r) => { const q = R(`${x} ${y}`).split(" "); return `M${(q[0] - r).toFixed(1)} ${q[1]}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`; };
  const zig = (x, dir) => `M${x} 28L${x + 7 * dir} 37L${x - 1 * dir} 45L${x + 7 * dir} 53L${x - 1 * dir} 61L${x + 6 * dir} 69`;
  return `
<path d="${R("M37 29L37 70C37 88 59 88 59 70L59 29Z")}" fill="${c.body}" ${K}/>
<path d="${R("M52 31L59 31L59 70C59 74 57.5 78 54.3 81.3C54.5 74 53.6 66 52 58Z")}" fill="${c.shade}"/>
<path d="${R("M37 51C42 46 45 46 48 50C52 54 55 54 59 49L59 70C59 88 37 88 37 70Z")}" fill="${c.field}" ${k}/>
<path d="${R("M33 22L63 22L63 31L33 31Z")}" fill="${c.shade}" ${K}/>
<path d="${R("M35 7L61 7L61 22L35 22Z")}" fill="${c.lite}" ${K}/>
<path d="${R("M40 12L40 19")}" fill="none" stroke="${c.body}" stroke-width="3"/>
<path d="${R("M41.5 33L41.5 45")}" fill="none" stroke="${c.lite}" stroke-width="3.2"/>
<path d="${bub(43, 69, 3)}${bub(52, 61, 2.4)}" fill="${c.lite}"/>
<path d="${zig(13, -1)}" fill="none" stroke="${c.ink}" stroke-width="6.4"/>
<path d="${zig(13, -1)}" fill="none" stroke="${c.lite}" stroke-width="3.2"/>
<path d="${zig(83, 1)}" fill="none" stroke="${c.ink}" stroke-width="6.4"/>
<path d="${zig(83, 1)}" fill="none" stroke="${c.lite}" stroke-width="3.2"/>`;
};

/* Chapter 67 - WATER-reactive solids and liquids: a tap with a single drop falling from the spout. The tap leads and is big;
   the drop is small and sits below it, so it cannot be read as Chapter 57's drop. */
CHAPTER_ICON["Chapter 67: Water-Reactive Solids and Liquids"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const spout = "M18 34H57C71 34 80 43 80 57V63H60V59C60 55 58 53 54 53H18Z";
  return `
<path d="M8 27H19V62H8Z" fill="${c.shade}" ${K}/>
<path d="M26 24H44V36H26Z" fill="${c.shade}" ${K}/>
<path d="${spout}" fill="${c.body}"/>
<path d="M18 46H54C58 46 60 48 60 54V63H80V57C80 53 79.4 49.6 78 46.5C74 38 66 34 57 34H18Z" fill="${c.shade}"/>
<path d="${spout}" fill="none" ${K}/>
<path d="M22 39.6H53C58 39.6 62 41 66 44" fill="none" stroke="${c.lite}" stroke-width="3.2"/>
<path d="M56 62H84V71H56Z" fill="${c.body}" ${K}/>
<path d="M59.6 66.5H68" fill="none" stroke="${c.lite}" stroke-width="2.4"/>
<path d="M12 14H58C61 14 63 16 63 19S61 24 58 24H12C9 24 7 22 7 19S9 14 12 14Z" fill="${c.body}" ${K}/>
<path d="M13 18.2H42" fill="none" stroke="${c.lite}" stroke-width="2.6"/>
<path d="M70 75C70 75 63.8 81.5 63.8 85A6.2 6.2 0 0 0 76.2 85C76.2 81.5 70 75 70 75Z" fill="${c.lite}" stroke="${c.ink}" stroke-width="1.8"/>`;
};

/* Chapter 80 - REFERENCED standards: a stack of three books, spines out, with a ribbon marker hanging down the front.
   (Chapter 2 is the open dictionary; this is closed and stacked, and it is the stack that reads at 26px.) */
CHAPTER_ICON["Chapter 80: Referenced Standards"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const rr = (x, y, w, h, r) => `M${x + r} ${y}H${x + w - r}Q${x + w} ${y} ${x + w} ${y + r}V${y + h - r}Q${x + w} ${y + h} ${x + w - r} ${y + h}H${x + r}Q${x} ${y + h} ${x} ${y + h - r}V${y + r}Q${x} ${y} ${x + r} ${y}Z`;
  return `
<path d="${rr(6, 63, 82, 26, 4)}" fill="${c.body}" ${K}/>
<path d="M66 60V91L70.4 86L74.8 91V60Z" fill="${c.field}" stroke="${c.ink}" stroke-width="2" stroke-linejoin="round"/>
<path d="${rr(16, 37, 76, 26, 4)}" fill="${c.shade}" ${K}/>
<path d="${rr(10, 11, 66, 26, 4)}" fill="${c.body}" ${K}/>
<path d="M10 83H84M14 31H72" fill="none" stroke="${c.shade}" stroke-width="4.4"/>
<path d="M12 67.8H80M15 16.4H70" fill="none" stroke="${c.lite}" stroke-width="2.4"/>
<path d="M21 42.4H86" fill="none" stroke="${c.body}" stroke-width="2.4"/>
<path d="M17 63V89M77 63V89M26 37V63M82 37V63M21 11V37M65 11V37" fill="none" ${k}/>
<path d="${rr(34, 72, 28, 10, 2)}" fill="${c.lite}" ${k}/>
<path d="${rr(42, 46, 26, 10, 2)}" fill="${c.body}" ${k}/>
<path d="${rr(30, 20, 26, 9, 2)}" fill="${c.field}" ${k}/>`;
};

/* Appendix B - FIRE-FLOW requirements: a pressure gauge, bezel, dial with ticks and a danger band, the needle, a threaded stem. */
CHAPTER_ICON["Appendix B: Fire-Flow Requirements for Buildings"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const cx = 48, cy = 43, R = 38, rad = (a) => a * Math.PI / 180;
  const pt = (r, a) => [(cx + r * Math.cos(rad(a))).toFixed(1), (cy + r * Math.sin(rad(a))).toFixed(1)];
  const circ = (r) => `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  let ticks = "";
  for (let i = 0; i <= 8; i++) { const a = 135 + 33.75 * i, s = pt(i % 4 === 0 ? 20 : 23, a), e = pt(27, a); ticks += `M${s[0]} ${s[1]}L${e[0]} ${e[1]}`; }
  const z1 = pt(21.5, 33.75 * 5 + 135 - 6), z2 = pt(21.5, 405);
  const s1 = pt(R, -45), s2 = pt(R, 140), h1 = pt(R - 4.2, 195), h2 = pt(R - 4.2, 250);
  const nt = pt(25, -50), nb1 = pt(4.4, 40), nb2 = pt(4.4, -140), nta = pt(8, 130);
  return `
<path d="M40 76H56V89H40Z" fill="${c.shade}" ${K}/>
<path d="M36 85H60V92H36Z" fill="${c.body}" ${K}/>
<path d="${circ(R)}" fill="${c.body}"/>
<path d="M${s1[0]} ${s1[1]}A${R} ${R} 0 0 1 ${s2[0]} ${s2[1]}A${R * 1.3} ${R * 1.3} 0 0 0 ${s1[0]} ${s1[1]}Z" fill="${c.shade}"/>
<path d="${circ(R)}" fill="none" ${K}/>
<path d="M${h1[0]} ${h1[1]}A${R - 4.2} ${R - 4.2} 0 0 1 ${h2[0]} ${h2[1]}" fill="none" stroke="${c.lite}" stroke-width="3"/>
<path d="${circ(29.5)}" fill="${c.lite}" ${k}/>
<path d="M${z1[0]} ${z1[1]}A21.5 21.5 0 0 1 ${z2[0]} ${z2[1]}" fill="none" stroke="${c.field}" stroke-width="4.4"/>
<path d="${ticks}" fill="none" stroke="${c.ink}" stroke-width="2.4"/>
<path d="M${nt[0]} ${nt[1]}L${nb1[0]} ${nb1[1]}L${nta[0]} ${nta[1]}L${nb2[0]} ${nb2[1]}Z" fill="${c.ink}" stroke="${c.ink}" stroke-width="1.6"/>
<path d="${circ(5.2)}" fill="${c.body}" ${k}/>`;
};

/* Appendix D - FIRE APPARATUS access roads: a fire engine in side view, nose to the left: cab with its windows and roof lights,
   the body with its compartment doors, the ladder racked along the top, two wheels. */
CHAPTER_ICON["Appendix D: Fire Apparatus Access Roads"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const circ = (x, y, r) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  let rungs = ""; for (let x = 42; x < 90; x += 6) rungs += `M${x} ${(33 - (x - 36) * 9 / 56 + 0.6).toFixed(1)}V${(40 - (x - 36) * 9 / 56 - 0.6).toFixed(1)}`;
  return `
<path d="M38 38H92V68H38Z" fill="${c.body}" ${K}/>
<path d="M6 69V50L15 31H38V69Z" fill="${c.body}" ${K}/>
<path d="M6 62H92V69H6Z" fill="${c.shade}" ${K}/>
<path d="M11 48L17.4 35H24V48ZM27.4 35H35V48H27.4Z" fill="${c.field}" ${k}/>
<path d="M43 44H57V58H43ZM60.4 44H74.4V58H60.4ZM78 44H88V58H78Z" fill="${c.shade}" ${k}/>
<path d="M17 24.6H33V31H17Z" fill="${c.lite}" ${K}/>
<path d="M36 33L92 24V31L36 40Z" fill="${c.lite}" ${K}/>
<path d="${rungs}" fill="none" ${k}/>
<path d="M44.6 47.2H54.6M63 47.2H72" fill="none" stroke="${c.body}" stroke-width="2.2"/>
<path d="${circ(24, 70, 10.4)}" fill="${c.shade}" ${K}/>
<path d="${circ(72, 70, 10.4)}" fill="${c.shade}" ${K}/>
<path d="${circ(24, 70, 4.6)}" fill="${c.lite}" ${k}/>
<path d="${circ(72, 70, 4.6)}" fill="${c.lite}" ${k}/>`;
};

/* Appendix H - the HMMP and HMIS instructions: a three-ring binder, the plan, with a four-part hazard diamond on its cover
   (no letters or numbers: four plain diamonds in the four tones). */
CHAPTER_ICON["Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const rr = (x, y, w, h, r) => `M${x + r} ${y}H${x + w - r}Q${x + w} ${y} ${x + w} ${y + r}V${y + h - r}Q${x + w} ${y + h} ${x + w - r} ${y + h}H${x + r}Q${x} ${y + h} ${x} ${y + h - r}V${y + r}Q${x} ${y} ${x + r} ${y}Z`;
  const dia = (x, y, h) => `M${x} ${y - h}L${x + h} ${y}L${x} ${y + h}L${x - h} ${y}Z`;
  const dx = 61, dy = 40, h = 10.4;
  const rings = "M17 22H44M17 48H44M17 74H44";
  return `
<path d="${rr(26, 6, 58, 84, 5)}" fill="${c.body}"/>
<path d="M72 6H79Q84 6 84 11V85Q84 90 79 90H62C70 78 73 40 72 6Z" fill="${c.shade}"/>
<path d="${rr(26, 6, 58, 84, 5)}" fill="none" ${K}/>
<path d="M26 11Q26 6 31 6H37V90H31Q26 90 26 85Z" fill="${c.shade}" ${K}/>
<path d="${rings}" fill="none" stroke="${c.ink}" stroke-width="8"/>
<path d="${rings}" fill="none" stroke="${c.lite}" stroke-width="4"/>
<path d="${dia(dx, dy - h, h)}" fill="${c.lite}" ${k}/>
<path d="${dia(dx - h, dy, h)}" fill="${c.field}" ${k}/>
<path d="${dia(dx + h, dy, h)}" fill="${c.shade}" ${k}/>
<path d="${dia(dx, dy + h, h)}" fill="${c.body}" ${k}/>
<path d="${dia(dx, dy, h * 2)}" fill="none" ${K}/>
<path d="${rr(52, 71, 26, 10, 2.5)}" fill="${c.lite}" ${k}/>`;
};

/* Appendix I - NONCOMPLIANT CONDITIONS: a warning triangle, a bar and a dot on a bright panel. No letters; the bar and dot are marks. */
CHAPTER_ICON["Appendix I: Fire Protection Systems—Noncompliant Conditions"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.6"`;
  const rp = (pts, r) => {
    const n = pts.length; let d = "";
    for (let i = 0; i < n; i++) {
      const p0 = pts[(i + n - 1) % n], p1 = pts[i], p2 = pts[(i + 1) % n];
      const u = (a, b) => { const dx = a[0] - b[0], dy = a[1] - b[1], l = Math.hypot(dx, dy); return [dx / l, dy / l]; };
      const v1 = u(p0, p1), v2 = u(p2, p1);
      d += (i ? "L" : "M") + (p1[0] + v1[0] * r).toFixed(1) + " " + (p1[1] + v1[1] * r).toFixed(1) + "Q" + p1[0] + " " + p1[1] + " " + (p1[0] + v2[0] * r).toFixed(1) + " " + (p1[1] + v2[1] * r).toFixed(1);
    }
    return d + "Z";
  };
  const T = [[48, 8], [91, 85], [5, 85]], g = [48, 59.3];
  const inner = T.map(p => [g[0] + (p[0] - g[0]) * .68, g[1] + (p[1] - g[1]) * .68]);
  return `
<path d="${rp(T, 8)}" fill="${c.body}"/>
<path d="M8.4 82.6L61.4 32L88.6 82.6Z" fill="${c.shade}"/>
<path d="${rp(T, 8)}" fill="none" ${K}/>
<path d="${rp(inner, 4.5)}" fill="${c.lite}" stroke="${c.ink}" stroke-width="1.8"/>
<path d="M43.2 39.5Q43.2 36.5 48 36.5Q52.8 36.5 52.8 39.5L51.2 62H44.8Z" fill="${c.ink}" stroke="${c.ink}" stroke-width="1.6"/>
<path d="M48 65a4.6 4.6 0 1 0 .1 0Z" fill="${c.ink}"/>`;
};

/* Exhibit B - AMENDMENTS to the International Building Code: a high-rise between two lower blocks, a stepped crown and a mast,
   rows of windows. A tower, not Chapter 11's old house. */
CHAPTER_ICON["Exhibit B: Amendments to the International Building Code"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  let win = "", wl = "", wr = "";
  for (let r = 0; r < 6; r++) for (let q = 0; q < 3; q++) win += `M${31 + q * 10.4} ${26 + r * 10.8}h6.4v6.4h-6.4Z`;
  for (let r = 0; r < 3; r++) wl += `M13.6 ${52 + r * 12.4}h5.6v6.2h-5.6Z`;
  for (let r = 0; r < 4; r++) wr += `M71.6 ${42 + r * 11.6}h5.6v6.2h-5.6Z`;
  return `
<path d="M10 90V44H30V90Z" fill="${c.shade}" ${K}/>
<path d="M66 90V34H86V90Z" fill="${c.shade}" ${K}/>
<path d="M27 90V16H69V90Z" fill="${c.body}" ${K}/>
<path d="M59 16H69V90H59Z" fill="${c.shade}"/>
<path d="M27 90V16H69V90Z" fill="none" ${K}/>
<path d="M34 16V10H62V16Z" fill="${c.body}" ${K}/>
<path d="M47 10V3.5H49V10Z" fill="${c.lite}" ${k}/>
<path d="${win}" fill="${c.lite}"/>
<path d="${wl}${wr}" fill="${c.body}"/>
<path d="M6 90H92" fill="none" stroke="${c.ink}" stroke-width="2.6"/>`;
};

/* Chapter and Section Finder - the lookup: a magnifying glass, ring and handle, the glass an open window onto the enamel. */
CHAPTER_ICON["Chapter and Section Finder"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const cx = 36, cy = 36, R = 29, rad = (a) => a * Math.PI / 180;
  const pt = (r, a) => [(cx + r * Math.cos(rad(a))).toFixed(1), (cy + r * Math.sin(rad(a))).toFixed(1)];
  const circ = (r) => `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  const u = [Math.SQRT1_2, Math.SQRT1_2], n = [Math.SQRT1_2, -Math.SQRT1_2];
  const q = (d, w) => [(cx + u[0] * d + n[0] * w).toFixed(1), (cy + u[1] * d + n[1] * w).toFixed(1)].join(" ");
  const hw = 7, d0 = 22, d1 = 70;
  const handle = `M${q(d0, -hw)}L${q(d1, -hw)}L${q(d1, hw)}L${q(d0, hw)}Z`;
  const hshade = `M${q(d0, 0)}L${q(d1, 0)}L${q(d1, hw)}L${q(d0, hw)}Z`;
  const grip = `M${q(46, -hw)}L${q(46, hw)}M${q(58, -hw)}L${q(58, hw)}`;
  const s1 = pt(R, -45), s2 = pt(R, 140), h1 = pt(R - 4.6, 195), h2 = pt(R - 4.6, 255), g1 = pt(14.4, 200), g2 = pt(14.4, 250);
  return `
<path d="${handle}" fill="${c.body}" ${K}/>
<path d="${hshade}" fill="${c.shade}"/>
<path d="${handle}" fill="none" ${K}/>
<path d="${grip}" fill="none" ${k}/>
<path d="${circ(R)}" fill="${c.body}"/>
<path d="M${s1[0]} ${s1[1]}A${R} ${R} 0 0 1 ${s2[0]} ${s2[1]}A${R * 1.3} ${R * 1.3} 0 0 0 ${s1[0]} ${s1[1]}Z" fill="${c.shade}"/>
<path d="${circ(R)}" fill="none" ${K}/>
<path d="M${h1[0]} ${h1[1]}A${R - 4.6} ${R - 4.6} 0 0 1 ${h2[0]} ${h2[1]}" fill="none" stroke="${c.lite}" stroke-width="3"/>
<path d="${circ(19.5)}" fill="${c.field}" ${K}/>
<path d="M${g1[0]} ${g1[1]}A14.4 14.4 0 0 1 ${g2[0]} ${g2[1]}" fill="none" stroke="${c.lite}" stroke-width="3.6"/>`;
};
