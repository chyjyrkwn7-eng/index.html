/* Phase 2, part 1 (build 384.61): chapters 1, 3, 4, 5, 6, 7, 8, 11, 12, 21. Each is (c) => markup, drawn to tools/chapter-badges-brief.md.
   Palette c = { field, lite, body, shade, ink }; 96 x 96 box, flat <path> plates only, no ids, no filters. */

/* Chapter 1 - a rubber hand stamp with its mark struck under it: SCOPE AND ADMINISTRATION is approvals and permits. */
CHAPTER_ICON["Chapter 1: Scope and Administration"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`;
  return `
<path d="M48 4C62 4 68 13 66 23C65 29 60 33 58 38H38C36 33 31 29 30 23C28 13 34 4 48 4Z" fill="${c.body}" ${K}/>
<path d="M49 6C62 8 64 18 63 24C62 29 58 32 56 36H50C56 28 57 15 49 6Z" fill="${c.shade}"/>
<path d="M37 11C35 16 35 21 37 25" fill="none" stroke="${c.lite}" stroke-width="3.4"/>
<path d="M40 38H56V50H40Z" fill="${c.shade}" ${K}/>
<path d="M12 49H84Q88 49 88 53V69H8V53Q8 49 12 49Z" fill="${c.body}" ${K}/>
<path d="M62 50.2H84Q86.8 50.2 86.8 53V67.8H62Z" fill="${c.shade}"/>
<path d="M14 54.5H44" fill="none" stroke="${c.lite}" stroke-width="3.2"/>
<path d="M13 69H83V76Q83 78 81 78H15Q13 78 13 76Z" fill="${c.shade}" ${K}/>
<path d="M10 83H86V91H10Z" fill="${c.body}" ${K}/>
<path d="M28 84.5V89.5M48 84.5V89.5M66 84.5V89.5" fill="none" stroke="${c.shade}" stroke-width="2"/>`;
};

/* Chapter 3 - a clipboard with three ticked lines, tilted: GENERAL REQUIREMENTS is the checklist everything else is held to.
   Tilted so that its silhouette is not the Egress door's (an upright rectangle each). */
CHAPTER_ICON["Chapter 3: General Requirements"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const rot = (d) => { const a = 9 * Math.PI / 180, cs = Math.cos(a), sn = Math.sin(a); return d.replace(/(-?\d*\.?\d+)[ ,](-?\d*\.?\d+)/g, (m, x, y) => { x = +x - 48; y = +y - 48; return (48 + x * cs - y * sn).toFixed(1) + " " + (48 + x * sn + y * cs).toFixed(1); }); };
  const row = (y) => `<path d="${rot(`M26 ${y}L31 ${y + 5}L40 ${y - 6}`)}" fill="none" stroke="${c.ink}" stroke-width="3.8" stroke-linejoin="round" stroke-linecap="round"/><path d="${rot(`M48 ${y}L68 ${y}`)}" fill="none" stroke="${c.shade}" stroke-width="3.8" stroke-linecap="round"/>`;
  return `
<path d="${rot("M18 16Q18 14 20 14L76 14Q78 14 78 16L78 84Q78 86 76 86L20 86Q18 86 18 84Z")}" fill="${c.body}" ${K}/>
<path d="${rot("M62 15.2L76 15.2Q76.8 15.2 76.8 16L76.8 84Q76.8 84.8 76 84.8L62 84.8Z")}" fill="${c.shade}" opacity=".6"/>
<path d="${rot("M24 24L72 24L72 80L24 80Z")}" fill="${c.lite}" ${k}/>
${row(40)}${row(55)}${row(70)}
<path d="${rot("M33 8L63 8Q65 8 65 10L65 20Q65 22 63 22L33 22Q31 22 31 20L31 10Q31 8 33 8Z")}" fill="${c.shade}" ${K}/>
<path d="${rot("M48 14L48.01 14")}" fill="none" stroke="${c.lite}" stroke-width="4.6" stroke-linecap="round"/>`;
};

/* Chapter 4 - a floor plan sheet: walls with doorways, a dotted route out through them and the arrow at the exit. The PLAN, not the emergency. */
CHAPTER_ICON["Chapter 4: Emergency Planning and Preparedness"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`;
  const dots = (pts, step) => { let o = "", [px, py] = pts[0]; o += `M${px} ${py}h.01`; for (let i = 1; i < pts.length; i++) { const [x, y] = pts[i], L = Math.hypot(x - px, y - py), n = Math.round(L / step); for (let j = 1; j <= n; j++) o += `M${(px + (x - px) * j / n).toFixed(1)} ${(py + (y - py) * j / n).toFixed(1)}h.01`; px = x; py = y; } return o; };
  return `
<path d="M8 10H58V44H90V88H8Z" fill="${c.lite}" stroke="${c.ink}" stroke-width="2.4" stroke-linejoin="round"/>
<path d="M9.2 44H30M44 44H58M62 45.2V60" fill="none" stroke="${c.shade}" stroke-width="4.6"/>
<path d="${dots([[20, 27], [37, 27], [37, 68], [66, 68]], 8)}" fill="none" stroke="${c.ink}" stroke-width="5.2" stroke-linecap="round"/>
<path d="M64 55L89 68L64 81Z" fill="${c.ink}" stroke="${c.ink}" stroke-width="3" stroke-linejoin="round"/>`;
};

/* Chapter 5 - a fire helmet in profile: the high comb over the crown, the dome with its front badge, the short peak and the long swept tail. */
CHAPTER_ICON["Chapter 5: Fire Service Features"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.6"`, k = `stroke="${c.ink}" stroke-width="1.8"`;
  return `
<path d="M4 63C14 73 38 77 58 77C76 78 88 82 92 90C70 92 42 91 24 86C10 82 4 74 4 63Z" fill="${c.shade}" ${K}/>
<path d="M13 70C9 38 27 23 48 23C70 23 85 40 85 74C70 80 30 78 13 70Z" fill="${c.body}" ${K}/>
<path d="M58 25C75 28 84 46 85 74C80 76 76 78 70 79C76 56 72 38 58 25Z" fill="${c.shade}"/>
<path d="M18 42C26 6 68 3 82 44L72 47C63 26 44 24 30 47Z" fill="${c.lite}" ${K}/>
<path d="M27 49H53V62C53 68 47 71 40 74C33 71 27 68 27 62Z" fill="${c.field}" ${k}/>
<path d="M15 56C16 50 18 46 21 42" fill="none" stroke="${c.lite}" stroke-width="3.2"/>`;
};

/* Chapter 6 - a ventilation fan in its square duct: the casing, the round throat, four curved blades and the hub. BUILDING SERVICES, of which air is the commonest. */
CHAPTER_ICON["Chapter 6: Building Services and Systems"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const rot = (d, deg) => { const a = deg * Math.PI / 180, cs = Math.cos(a), sn = Math.sin(a); return d.replace(/(-?\d*\.?\d+)[ ,](-?\d*\.?\d+)/g, (m, x, y) => { x = +x - 48; y = +y - 48; return (48 + x * cs - y * sn).toFixed(1) + " " + (48 + x * sn + y * cs).toFixed(1); }); };
  const blade = "M45 44C35 34 36 18 50 14C62 12 64 26 54 44Z";
  const bl = [0, 90, 180, 270].map(a => `<path d="${rot(blade, a)}" fill="${c.body}" ${k}/>`).join("");
  return `
<path d="M12 6H84Q90 6 90 12V84Q90 90 84 90H12Q6 90 6 84V12Q6 6 12 6Z" fill="${c.body}" ${K}/>
<path d="M48 14a34 34 0 1 0 .01 0Z" fill="${c.shade}" ${K}/>
${bl}
<path d="M48 40a8 8 0 1 0 .01 0Z" fill="${c.lite}" ${K}/>
<path d="M16 15h.01M80 15h.01M16 81h.01M80 81h.01" fill="none" stroke="${c.lite}" stroke-width="4.4" stroke-linecap="round"/>`;
};

/* Chapter 7 - a brick wall with the flame held at one side of it and the smoke that gets over the top: fire and smoke PROTECTION. */
CHAPTER_ICON["Chapter 7: Fire and Smoke Protection Features"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M42 32H90V90H42Z" fill="${c.body}" ${K}/>
<path d="M74 33.2H88.8V88.8H74Z" fill="${c.shade}"/>
<path d="M43 47H89M43 62H89M43 77H89M60 32V47M76 32V47M52 47V62M68 47V62M84 47V62M60 62V77M76 62V77M52 77V90M68 77V90M84 77V90" fill="none" ${k}/>
<path d="M22 90C8 90 6 72 15 60C17 66 21 68 23 66C21 52 28 40 34 31C40 46 44 58 41 74C40 84 34 90 22 90Z" fill="${c.lite}" ${K}/>
<path d="M23 90C15 90 14 80 19 74C21 77 24 78 25 76C27 70 29 66 31 62C34 70 34 80 30 86C28 89 26 90 23 90Z" fill="${c.field}" ${k}/>
<path d="M44 26C36 26 33 19 38 14C38 8 46 6 50 9C54 4 63 5 65 11C71 9 78 13 76 19C82 20 83 26 77 26Z" fill="${c.shade}" ${K}/>
<path d="M42 14C44 11 47 11 49 12" fill="none" stroke="${c.lite}" stroke-width="2.8"/>`;
};

/* Chapter 8 - an armchair: FURNISHINGS, the thing the finish and the fabric go on. Tall back, rolled arms, loose seat cushion, short legs. */
CHAPTER_ICON["Chapter 8: Interior Finish, Decorative Materials and Furnishings"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`;
  return `
<path d="M24 8H72Q80 8 80 16V58H16V16Q16 8 24 8Z" fill="${c.body}" ${K}/>
<path d="M62 9.2H72Q78.8 9.2 78.8 16V57H62Z" fill="${c.shade}"/>
<path d="M24 16C22 22 22 30 24 36" fill="none" stroke="${c.lite}" stroke-width="3.2"/>
<path d="M12 40H24V76H6V46Q6 40 12 40Z" fill="${c.shade}" ${K}/>
<path d="M84 40H72V76H90V46Q90 40 84 40Z" fill="${c.shade}" ${K}/>
<path d="M12 41.5C9 44 8 48 8 52" fill="none" stroke="${c.lite}" stroke-width="2.4"/>
<path d="M24 52H72V74H24Z" fill="${c.lite}" ${K}/>
<path d="M6 74H90V82Q90 84 88 84H8Q6 84 6 82Z" fill="${c.body}" ${K}/>
<path d="M13 84V90M83 84V90" fill="none" stroke="${c.ink}" stroke-width="6.4" stroke-linecap="round"/>`;
};

/* Chapter 11 - an older brick house with a claw hammer beside it: CONSTRUCTION REQUIREMENTS FOR EXISTING BUILDINGS. */
CHAPTER_ICON["Chapter 11: Construction Requirements for Existing Buildings"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M71 28H81V88Q81 90 79 90H73Q71 90 71 88Z" fill="${c.body}" ${K}/>
<path d="M76 29.2H79.8V88.8H76Z" fill="${c.shade}"/>
<path d="M92 9H67C61 9 57 14 52 23C58 21 62 23 66 27V29H92Z" fill="${c.lite}" ${K}/>
<path d="M82 10.2H90.8V27.8H82Z" fill="${c.shade}"/>
<path d="M40 36V15H49V42Z" fill="${c.body}" ${K}/>
<path d="M8 48H52V90H8Z" fill="${c.body}" ${K}/>
<path d="M34 49.2H50.8V88.8H34Z" fill="${c.shade}" opacity=".7"/>
<path d="M9 62H51M9 76H51M24 62V76M38 62V76" fill="none" stroke="${c.ink}" stroke-width="1.4"/>
<path d="M4 52L30 22L56 52Z" fill="${c.shade}" ${K}/>
<path d="M23 90V76Q23 69 30 69Q37 69 37 76V90Z" fill="${c.ink}" ${k}/>
<path d="M11 53H21V63H11Z" fill="${c.lite}" ${k}/>
<path d="M39 53H49V63H39Z" fill="${c.lite}" ${k}/>`;
};

/* Chapter 12 - a battery cell with a bolt through it: ENERGY SYSTEMS. The bolt is a window onto the enamel, as the flame is in Chapter 57. */
CHAPTER_ICON["Chapter 12: Energy Systems"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`;
  return `
<path d="M80 34H92V62H80Z" fill="${c.shade}" ${K}/>
<path d="M12 16H76Q82 16 82 22V74Q82 80 76 80H12Q6 80 6 74V22Q6 16 12 16Z" fill="${c.body}" ${K}/>
<path d="M7.2 66H80.8V74Q80.8 78.8 76 78.8H12Q7.2 78.8 7.2 74Z" fill="${c.shade}"/>
<path d="M14 23H66" fill="none" stroke="${c.lite}" stroke-width="3.4"/>
<path d="M54 18L30 50H44L36 78L64 42H49Z" fill="${c.field}" stroke="${c.ink}" stroke-width="2.6" stroke-linejoin="round"/>`;
};

/* Chapter 21 - a shirt on a hanger: DRY CLEANING, the garment that comes back on a hanger. */
CHAPTER_ICON["Chapter 21: Dry Cleaning"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M48 26C48 20 40 18 40 12C40 5 54 4 54 11" fill="none" stroke="${c.ink}" stroke-width="7.6" stroke-linecap="round"/>
<path d="M48 26C48 20 40 18 40 12C40 5 54 4 54 11" fill="none" stroke="${c.lite}" stroke-width="3.4" stroke-linecap="round"/>
<path d="M38 26L22 33L4 56L17 66L26 55V90H70V55L79 66L92 56L74 33L58 26L48 36Z" fill="${c.body}" ${K}/>
<path d="M48 36L58 26L74 33L92 56L79 66L70 55V90H48Z" fill="${c.shade}" opacity=".85"/>
<path d="M38 26L48 40L58 26L48 33Z" fill="${c.lite}" ${K}/>
<path d="M48 42V90" fill="none" ${k}/>
<path d="M11 58L22 40" fill="none" stroke="${c.lite}" stroke-width="3.2"/>`;
};
