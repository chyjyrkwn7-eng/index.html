/* Phase 2, part 2 (build 384.61): chapters 22-33, drawn to the spec in tools/chapter-badges-brief.md.
   Each is (c) => markup; palette c = { field, lite, body, shade, ink }; 96 x 96 box, paths only, no ids, no filters.
   Light is top-left: body/lite on the left and top, shade on the right and bottom, ink for the keyline. */

/* Chapter 22 - a sack of grain tied at the neck, a stencilled ear of wheat on its belly, a puff of dust rising off its mouth. */
CHAPTER_ICON["Chapter 22: Combustible Dust-Producing Operations"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const circ = (x, y, r) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  const puff = circ(66, 20, 11) + circ(80, 28, 9) + circ(55, 28, 8) + circ(68, 34, 8.5);
  const grain = (x, y, d) => `M${x} ${y}q${d * 7} -1 ${d * 9} -9q${-d * 8} 0 ${-d * 9} 9Z`;
  return `
<path d="M24 46C14 54 10 66 11 78C11 86 18 91 28 91H58C68 91 75 86 75 78C76 66 72 54 62 46Z" fill="${c.body}" ${K}/>
<path d="M62 46C72 54 76 66 75 78C75 86 68 91 58 91H46C56 86 60 70 56 46Z" fill="${c.shade}"/>
<path d="M30 46L28 34Q36 29 43 35Q49 27 59 31L58 46Z" fill="${c.body}" ${K}/>
<path d="M27 42H60" fill="none" stroke="${c.ink}" stroke-width="6.4"/>
<path d="M27 42H60" fill="none" stroke="${c.lite}" stroke-width="3"/>
<path d="M18 62C16 68 16 74 18 80" fill="none" stroke="${c.lite}" stroke-width="3.2"/>
<path d="M43 82V57" fill="none" stroke="${c.field}" stroke-width="2.6"/>
<path d="${grain(43, 78, 1)}${grain(43, 78, -1)}${grain(43, 70, 1)}${grain(43, 70, -1)}${grain(43, 62, 1)}${grain(43, 62, -1)}M43 57q-4 -5 0 -10q4 5 0 10Z" fill="${c.field}"/>
<path d="${puff}" fill="${c.ink}" stroke="${c.ink}" stroke-width="4.8"/>
<path d="${puff}" fill="${c.lite}"/>
<path d="M60 22Q64 16 71 17" fill="none" stroke="${c.body}" stroke-width="2.4"/>
<path d="${circ(87, 46, 3)}${circ(78, 55, 2.6)}${circ(90, 60, 2.2)}" fill="${c.lite}" ${k}/>`;
};

/* Chapter 23 - a fuel pump: the display window, the body on its base, the hose looped out of the side to the nozzle in its holster. */
CHAPTER_ICON["Chapter 23: Motor Fuel-Dispensing Facilities and Repair Garages"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M12 84H64V91H12Z" fill="${c.shade}" ${K}/>
<path d="M18 14Q18 8 24 8H52Q58 8 58 14V84H18Z" fill="${c.body}" ${K}/>
<path d="M46 8H52Q58 8 58 14V84H46Z" fill="${c.shade}"/>
<path d="M18 14Q18 8 24 8H52Q58 8 58 14V84H18Z" fill="none" ${K}/>
<path d="M24 16H52V34H24Z" fill="${c.lite}" ${K}/>
<path d="M29 22H40M29 28H47" fill="none" stroke="${c.shade}" stroke-width="2.6"/>
<path d="M24 42H52V58H24Z" fill="${c.shade}" ${k}/>
<path d="M30 63H46V78H30Z" fill="${c.lite}" ${k}/>
<path d="M58 40H72Q82 40 82 50V62" fill="none" stroke="${c.ink}" stroke-width="8.4"/>
<path d="M58 40H72Q82 40 82 50V62" fill="none" stroke="${c.lite}" stroke-width="4.6"/>
<path d="M74 60H90V70L86 74V86H78V74L74 70Z" fill="${c.body}" ${K}/>
<path d="M86 74V86H82V74Z" fill="${c.shade}"/>
<path d="M77 63H87" fill="none" stroke="${c.lite}" stroke-width="2.4"/>`;
};

/* Chapter 24 - a spray gun, nose to the left, its paint cup on top and its trigger under the barrel, throwing a speckled fan of paint. */
CHAPTER_ICON["Chapter 24: Flammable Finishes"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const circ = (x, y, r) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  return `
<path d="M33 41L10 17Q-1 41 10 65Z" fill="${c.lite}" ${K}/>
<path d="${circ(14, 41, 2.6)}${circ(21, 30, 2.4)}${circ(21, 52, 2.4)}${circ(10, 29, 2)}${circ(10, 53, 2)}${circ(27, 41, 2.2)}" fill="${c.shade}"/>
<path d="M60 8H84V15H60Z" fill="${c.body}" ${K}/>
<path d="M62 15H82L77 36H67Z" fill="${c.lite}" ${K}/>
<path d="M72 15H82L77 36H72Z" fill="${c.shade}"/>
<path d="M33 33H40V49H33Z" fill="${c.shade}" ${K}/>
<path d="M40 31H78Q90 31 90 41V47Q90 52 85 52H40Z" fill="${c.body}" ${K}/>
<path d="M66 31H78Q90 31 90 41V47Q90 52 85 52H66Z" fill="${c.shade}"/>
<path d="M45 37H62" fill="none" stroke="${c.lite}" stroke-width="2.6"/>
<path d="M68 52H85L91 84Q92 90 86 90H80Q75 90 74 85Z" fill="${c.body}" ${K}/>
<path d="M80 52H85L91 84Q92 90 86 90H80Q82 80 80 52Z" fill="${c.shade}"/>
<path d="M60 52Q54 63 62 70" fill="none" stroke="${c.ink}" stroke-width="6.6"/>
<path d="M60 52Q54 63 62 70" fill="none" stroke="${c.lite}" stroke-width="3"/>`;
};

/* Chapter 25 - an apple with its stem and leaf: fruit ripening. The leaf is the shade plate so it parts from the fruit. */
CHAPTER_ICON["Chapter 25: Fruit and Crop Ripening"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.6"`;
  return `
<path d="M48 30C38 22 16 24 14 50C12 72 30 90 41 88Q48 85 55 88C66 90 84 72 82 50C80 24 58 22 48 30Z" fill="${c.body}" ${K}/>
<path d="M82 50C84 72 66 90 55 88Q50 86 48 86C62 80 70 66 68 48C67 38 60 31 52 28C66 24 80 30 82 50Z" fill="${c.shade}"/>
<path d="M22 46C23 38 28 33 35 31" fill="none" stroke="${c.lite}" stroke-width="4"/>
<path d="M48 30C47 22 48 14 52 8" fill="none" stroke="${c.ink}" stroke-width="7"/>
<path d="M48 30C47 22 48 14 52 8" fill="none" stroke="${c.shade}" stroke-width="3.2"/>
<path d="M54 22C58 10 72 6 84 12C80 24 68 28 54 22Z" fill="${c.lite}" ${K}/>
<path d="M54 22C64 16 72 14 79 14" fill="none" stroke="${c.shade}" stroke-width="1.8"/>`;
};

/* Chapter 26 - a beetle seen from above, wading out of a bank of fog: head, antennae, split wing cases, six legs. */
CHAPTER_ICON["Chapter 26: Fumigation and Insecticidal Fogging"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const circ = (x, y, r) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  const fog = circ(22, 76, 11) + circ(38, 72, 12) + circ(58, 74, 13) + circ(76, 72, 11) + circ(84, 82, 6) + circ(12, 82, 6) + circ(26, 84, 6) + circ(48, 84, 6) + circ(70, 84, 6) + "M12 78V90H84V78Z";
  const leg = (d) => `<path d="${d}" fill="none" stroke="${c.ink}" stroke-width="5.4"/><path d="${d}" fill="none" stroke="${c.body}" stroke-width="2.6"/>`;
  return `
${leg("M36 36L16 28L10 36M35 50L12 50M36 62L18 72")}${leg("M60 36L80 28L86 36M61 50L84 50M60 62L78 72")}
<path d="M40 22C38 12 36 10 33 8M56 22C58 12 60 10 63 8" fill="none" stroke="${c.ink}" stroke-width="2.4"/>
<path d="M48 14C55 14 58 18 58 24H38C38 18 41 14 48 14Z" fill="${c.body}" ${K}/>
<path d="M48 22C61 22 66 38 65 56C64 70 57 80 48 80C39 80 32 70 31 56C30 38 35 22 48 22Z" fill="${c.body}" ${K}/>
<path d="M48 22C61 22 66 38 65 56C64 70 57 80 48 80Z" fill="${c.shade}"/>
<path d="M48 22C61 22 66 38 65 56C64 70 57 80 48 80C39 80 32 70 31 56C30 38 35 22 48 22Z" fill="none" ${K}/>
<path d="M48 25V80" fill="none" stroke="${c.ink}" stroke-width="2"/>
<path d="M37 40C36 46 36 52 37 58" fill="none" stroke="${c.lite}" stroke-width="3.2"/>
<path d="${fog}" fill="${c.ink}" stroke="${c.ink}" stroke-width="4.8"/>
<path d="${fog}" fill="${c.lite}"/>
<path d="M16 72C18 67 23 65 28 66M52 66C56 64 60 65 63 67" fill="none" stroke="${c.shade}" stroke-width="2.4"/>`;
};

/* Chapter 27 - a microchip: the package with a notched corner and the die on it, sixteen pins round four sides. */
CHAPTER_ICON["Chapter 27: Semiconductor Fabrication Facilities"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const xs = [30, 42, 54, 66], pinsV = (y0) => xs.map(x => `M${x - 3} ${y0}h6v13h-6Z`).join("");
  const pinsH = (x0) => xs.map(y => `M${x0} ${y - 3}h13v6h-13Z`).join("");
  return `
<path d="${pinsV(8)}${pinsV(75)}${pinsH(8)}${pinsH(75)}" fill="${c.lite}" ${k}/>
<path d="M24 18H72Q78 18 78 24V72Q78 78 72 78H24Q18 78 18 72V24Q18 18 24 18Z" fill="${c.body}" ${K}/>
<path d="M60 18H72Q78 18 78 24V72Q78 78 72 78H60Z" fill="${c.shade}"/>
<path d="M24 18H72Q78 18 78 24V72Q78 78 72 78H24Q18 78 18 72V24Q18 18 24 18Z" fill="none" ${K}/>
<path d="M32 32H64V64H32Z" fill="${c.shade}" ${K}/>
<path d="M36 36H60V60H36Z" fill="${c.lite}" ${k}/>
<path d="M42 42H54V54H42Z" fill="${c.field}" ${k}/>
<path d="M25.8 25a3.2 3.2 0 1 0 6.4 0a3.2 3.2 0 1 0 -6.4 0Z" fill="${c.ink}"/>`;
};

/* Chapter 28 - a stack of logs seen end on: six round ends in a pyramid, bark ring, pale wood, growth rings. */
CHAPTER_ICON["Chapter 28: Lumber Yards and Agro-Industrial, Solid Biomass and Woodworking Facilities"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const circ = (x, y, r) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  const R = 14.8, D = 2 * R, dy = D * 0.866, cx = 48, base = 90 - R;
  const pts = [];
  [3, 2, 1].forEach((n, row) => { for (let i = 0; i < n; i++) pts.push([cx + (i - (n - 1) / 2) * D, base - row * dy]); });
  const bark = pts.map(([x, y]) => circ(x, y, R)).join("");
  const face = pts.map(([x, y]) => circ(x - 1, y - 1, R - 4.4)).join("");
  const ring = pts.map(([x, y]) => circ(x - 1, y - 1, 5.4)).join("");
  const glint = pts.map(([x, y]) => `M${x - 9} ${y - 3}A9 9 0 0 1 ${x - 3} ${y - 9}`).join("");
  return `
<path d="${bark}" fill="${c.shade}" ${K}/>
<path d="${face}" fill="${c.body}" ${k}/>
<path d="${ring}" fill="none" stroke="${c.shade}" stroke-width="1.8"/>
<path d="${glint}" fill="none" stroke="${c.lite}" stroke-width="2.4"/>`;
};

/* Chapter 29 - a paint can with its wire handle, a band of label, and paint (the enamel itself) brimming over the rim and running down. */
CHAPTER_ICON["Chapter 29: Manufacture of Organic Coatings"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M20 38C20 6 76 6 76 38" fill="none" stroke="${c.ink}" stroke-width="6.4"/>
<path d="M20 38C20 6 76 6 76 38" fill="none" stroke="${c.lite}" stroke-width="2.8"/>
<path d="M16 34V78Q16 90 48 90Q80 90 80 78V34Z" fill="${c.body}" ${K}/>
<path d="M64 34H80V78Q80 90 48 90Q58 88 64 80Z" fill="${c.shade}"/>
<path d="M16 34V78Q16 90 48 90Q80 90 80 78V34" fill="none" ${K}/>
<path d="M18 56H78V74H18Z" fill="${c.lite}" ${k}/>
<path d="M26 62H46M26 68H58" fill="none" stroke="${c.shade}" stroke-width="2.4"/>
<path d="M12 33C12 25 28 21 48 21S84 25 84 33S68 42 48 42S12 41 12 33Z" fill="${c.lite}" ${K}/>
<path d="M22 33C22 29 33 26 48 26S74 29 74 33S63 38 48 38S22 37 22 33Z" fill="${c.field}" ${k}/>
<path d="M28 39C27 50 26 62 33 62C40 62 38 50 37 39Z" fill="${c.field}" ${k}/>`;
};

/* Chapter 30 - an oven: control strip with two knobs and a display, a handle across the door, a dark window with glints, two feet. */
CHAPTER_ICON["Chapter 30: Industrial Ovens"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M14 84H24V91H14ZM72 84H82V91H72Z" fill="${c.shade}" ${K}/>
<path d="M6 25Q6 15 16 15H80Q90 15 90 25V84H6Z" fill="${c.body}" ${K}/>
<path d="M70 15H80Q90 15 90 25V84H70Z" fill="${c.shade}"/>
<path d="M6 25Q6 15 16 15H80Q90 15 90 25V84H6Z" fill="none" ${K}/>
<path d="M6 36H90" fill="none" ${k}/>
<path d="M16.6 26a5.4 5.4 0 1 0 10.8 0a5.4 5.4 0 1 0 -10.8 0ZM32.6 26a5.4 5.4 0 1 0 10.8 0a5.4 5.4 0 1 0 -10.8 0Z" fill="${c.lite}" ${k}/>
<path d="M62 22H78V29H62Z" fill="${c.ink}"/>
<path d="M13 43H83V78H13Z" fill="${c.shade}" ${K}/>
<path d="M20 52H76V72H20Z" fill="${c.ink}" ${k}/>
<path d="M26 68L36 55H43L33 68ZM47 68L54 58H58L51 68Z" fill="${c.lite}"/>
<path d="M18 47H78" fill="none" stroke="${c.lite}" stroke-width="3.2"/>`;
};

/* Chapter 31 - an event tent: striped roof to a single peak with a pennant, the door drawn back, guy ropes down to the pegs. */
CHAPTER_ICON["Chapter 31: Tents, Temporary Special Event Structures and Other Membrane Structures"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M48 22V8" fill="none" stroke="${c.ink}" stroke-width="2.4"/>
<path d="M48 8L66 13L48 18Z" fill="${c.lite}" ${k}/>
<path d="M48 20C60 40 78 62 90 80H6C18 62 36 40 48 20Z" fill="${c.body}" ${K}/>
<path d="M48 20C60 40 78 62 90 80H62C60 58 54 38 48 20Z" fill="${c.shade}"/>
<path d="M48 20C36 40 18 62 6 80H26C32 58 42 38 48 20Z" fill="${c.lite}"/>
<path d="M48 20C60 40 78 62 90 80H6C18 62 36 40 48 20Z" fill="none" ${K}/>
<path d="M48 46C54 58 60 70 62 82H34C36 70 42 58 48 46Z" fill="${c.ink}" ${k}/>
<path d="M48 46C42 58 36 70 34 82L44 82C44 68 46 56 48 46Z" fill="${c.body}" ${k}/>
<path d="M6 80H90V88H6Z" fill="${c.shade}" ${K}/>`;
};

/* Chapter 32 - a pallet rack: two uprights, three beams, and three boxes stacked on each shelf up to the top of the bay. */
CHAPTER_ICON["Chapter 32: High-Piled Combustible Storage"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const row = (y) => `M18 ${y}H34V${y + 18}H18ZM37 ${y}H53V${y + 18}H37ZM56 ${y}H72V${y + 18}H56Z`;
  return `
<path d="M10 6H18V90H10ZM78 6H86V90H78Z" fill="${c.shade}" ${K}/>
<path d="M10 34H86V40H10ZM10 62H86V68H10ZM10 84H86V90H10Z" fill="${c.lite}" ${k}/>
<path d="${row(14)}${row(42)}${row(70)}" fill="${c.body}" ${K}/>
<path d="M18 14H34V19H18ZM37 14H53V19H37ZM56 14H72V19H56Z M18 42H34V47H18ZM37 42H53V47H37ZM56 42H72V47H56Z M18 70H34V75H18ZM37 70H53V75H37ZM56 70H72V75H56Z" fill="${c.lite}"/>
<path d="M66 19H72V32H66ZM47 19H53V32H47Z M66 47H72V60H66ZM47 47H53V60H47Z M66 75H72V82H66ZM47 75H53V82H47Z M28 19H34V32H28ZM28 47H34V60H28ZM28 75H34V82H28Z" fill="${c.shade}"/>`;
};

/* Chapter 33 - a wrecking ball swinging in on its chain from the tip of a crane boom, with bricks at its feet: construction and demolition. */
CHAPTER_ICON["Chapter 33: Fire Safety During Construction and Demolition"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const circ = (x, y, r) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  const x0 = 36, y0 = 18, x1 = 54, y1 = 39, n = 3, len = Math.hypot(x1 - x0, y1 - y0), ux = (x1 - x0) / len, uy = (y1 - y0) / len;
  let d = "";
  for (let i = 0; i < n; i++) {
    const t = (i + .5) / n, x = x0 + (x1 - x0) * t, y = y0 + (y1 - y0) * t, L = len / n * .5;
    d += `M${(x - ux * L).toFixed(1)} ${(y - uy * L).toFixed(1)}L${(x + ux * L).toFixed(1)} ${(y + uy * L).toFixed(1)}`;
  }
  return `
<path d="M5 4H44L54 18H5Z" fill="${c.body}" ${K}/>
<path d="M7 12H50L53 17H7Z" fill="${c.shade}"/>
<path d="${circ(36, 17, 5)}" fill="${c.lite}" ${k}/>
<path d="${d}" fill="none" stroke="${c.ink}" stroke-width="9.4"/>
<path d="${d}" fill="none" stroke="${c.lite}" stroke-width="5.4"/>
<path d="${d}" fill="none" stroke="${c.ink}" stroke-width="1.6"/>
<path d="${circ(60, 64, 26)}" fill="${c.shade}" ${K}/>
<path d="${circ(55, 59, 19.5)}" fill="${c.body}"/>
<path d="M40 64C40 54 46 47 55 44" fill="none" stroke="${c.lite}" stroke-width="4.4"/>
<path d="M4 76H22V88H4Z" fill="${c.shade}" ${k}/>
<path d="M9 62H25V71H9Z" fill="${c.body}" ${k}/>`;
};
