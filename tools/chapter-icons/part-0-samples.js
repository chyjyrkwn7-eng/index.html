/* Phase 1 samples (build 384.61): six chapters, drawn to the spec in tools/chapter-badges-brief.md - the exemplars phase 2 is held to.
   Each is (c) => markup; palette c = { field, lite, body, shade, ink }; 96 x 96 box, paths only, no ids, no filters. */

/* Chapter 10 - an open door: the frame, the bright opening, the leaf swung back into the room with its two panels and its knob. */
CHAPTER_ICON["Chapter 10: Means of Egress"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M16 8H80V90H16Z" fill="${c.body}" ${K}/>
<path d="M25 16H71V90H25Z" fill="${c.lite}" ${K}/>
<path d="M25 90L71 90L71 80L56 76Z" fill="${c.body}" opacity=".55"/>
<path d="M25 16L57 26V79L25 90Z" fill="${c.shade}" ${K}/>
<path d="M30 23L52 29.6V46L30 48Z" fill="${c.body}" ${k}/>
<path d="M30 56L52 54.4V71.5L30 82Z" fill="${c.body}" ${k}/>
<path d="M52.5 61.5a2.7 2.7 0 1 0 .1 0Z" fill="${c.lite}" ${k}/>`;
};

/* Chapter 9 - a pendant sprinkler head with the water it throws: pipe, fitting, frame, glass bulb, deflector, drops. */
CHAPTER_ICON["Chapter 9: Fire Protection and Life Safety Systems"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  const drop = (x, y, s) => `<path d="M${x} ${y - 7.5 * s}C${x + 2 * s} ${y - 3.5 * s} ${x + 5.2 * s} ${y - 1 * s} ${x + 5.2 * s} ${y + 2.6 * s}A${5.2 * s} ${5.2 * s} 0 0 1 ${x - 5.2 * s} ${y + 2.6 * s}C${x - 5.2 * s} ${y - 1 * s} ${x - 2 * s} ${y - 3.5 * s} ${x} ${y - 7.5 * s}Z" fill="${c.lite}" stroke="${c.ink}" stroke-width="${(1.7 * Math.max(s, .8)).toFixed(2)}"/>`;
  return `
<path d="M42 5H54V22H42Z" fill="${c.body}" ${K}/>
<path d="M42 11H54M42 16H54" fill="none" ${k}/>
<path d="M36 22H60L62 25V30L60 33H36L34 30V25Z" fill="${c.body}" ${K}/>
<path d="M39.5 24.5V30.5" fill="none" stroke="${c.lite}" stroke-width="2.4"/>
<path d="M40 33L45.5 55M56 33L50.5 55" fill="none" stroke="${c.ink}" stroke-width="7.6"/>
<path d="M40 33L45.5 55M56 33L50.5 55" fill="none" stroke="${c.body}" stroke-width="4.4"/>
<path d="M48 36C51.6 36 53.2 40 53.2 44.2S51.6 52 48 52S42.8 48.4 42.8 44.2S44.4 36 48 36Z" fill="${c.lite}" ${k}/>
<path d="M26 62C26 58.6 36 56.4 48 56.4S70 58.6 70 62C70 65.2 60 67 48 67S26 65.2 26 62Z" fill="${c.body}" ${K}/>
<path d="M48 51.5a4.6 4.6 0 1 0 .1 0Z" fill="${c.shade}" ${k}/>
${drop(17, 70, .66)}${drop(31, 79, .84)}${drop(48, 83, 1.02)}${drop(65, 79, .84)}${drop(79, 70, .66)}`;
};

/* Chapter 57 - a drop with a flame in it: flammable and combustible LIQUIDS. The flame is a window onto the enamel. */
CHAPTER_ICON["Chapter 57: Flammable and Combustible Liquids"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.6"`;
  return `
<path d="M48 6C48 6 20 37 20 60A28 28 0 0 0 76 60C76 37 48 6 48 6Z" fill="${c.body}" ${K}/>
<path d="M48 6C48 6 76 37 76 60A28 28 0 0 1 44 87.6C62 82 68 64 63 46C59.5 31 51 15 48 6Z" fill="${c.shade}"/>
<path d="M29.5 58C29.5 49 34 41 40 33" fill="none" stroke="${c.lite}" stroke-width="3.4"/>
<path d="M48 36C52.4 45 63 51 63 65A15 15 0 0 1 33 65C33 58 37 53.6 40.5 48.6C42 52.6 43.6 54 46 54.6C44.4 48 45.8 42 48 36Z" fill="${c.field}" stroke="${c.ink}" stroke-width="2.2"/>
<path d="M48 55C51.4 59.4 55.6 61.6 55.6 67A7.6 7.6 0 0 1 40.4 67C40.4 63.6 43.2 61.6 44.4 58.6C45.4 60.6 46.6 61.4 48 61.6Z" fill="${c.lite}"/>`;
};

/* Chapter 2 - an open dictionary, a ribbon marking the place: DEFINITIONS, which is a chapter of a book of words, drawn as the book. */
CHAPTER_ICON["Chapter 2: Definitions"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, line = (d) => `<path d="${d}" fill="none" stroke="${c.shade}" stroke-width="2.4"/>`;
  return `
<path d="M48 83C40 76 22 75 6 80V26C22 21 40 22 48 28C56 22 74 21 90 26V80C74 75 56 76 48 83Z" fill="${c.shade}" ${K}/>
<path d="M48 76C40 69.5 24 68.5 11 72V24.5C24 21.5 40 22.5 48 28Z" fill="${c.body}" ${K}/>
<path d="M48 76C56 69.5 72 68.5 85 72V24.5C72 21.5 56 22.5 48 28Z" fill="${c.lite}" ${K}/>
${line("M17 34C24 32.4 31 32.6 41 36")}${line("M17 43C24 41.4 31 41.6 41 45")}${line("M17 52C24 50.4 31 50.6 41 54")}${line("M17 61C22 59.6 28 59.8 34 61.4")}
${line("M55 36C65 32.6 72 32.4 79 34")}${line("M55 45C65 41.6 72 41.4 79 43")}${line("M55 54C65 50.6 72 50.4 79 52")}
<path d="M48 76V90L53 85.4L58 90V74Z" fill="${c.field}" stroke="${c.ink}" stroke-width="2"/>`;
};

/* Appendix C - a fire hydrant: bonnet and top nut, the barrel with its two side outlets and the pumper nozzle, the flared base. */
CHAPTER_ICON["Appendix C: Fire Hydrant Locations and Distribution"] = (c) => {
  const K = `stroke="${c.ink}" stroke-width="2.4"`, k = `stroke="${c.ink}" stroke-width="1.6"`;
  return `
<path d="M41 8H55V14H41Z" fill="${c.body}" ${K}/>
<path d="M30 34C30 22 37 15 48 15S66 22 66 34Z" fill="${c.body}" ${K}/>
<path d="M14 42H31V60H14Z" fill="${c.shade}" ${K}/>
<path d="M65 42H82V60H65Z" fill="${c.shade}" ${K}/>
<path d="M9 40H16V62H9Z" fill="${c.body}" ${K}/>
<path d="M80 40H87V62H80Z" fill="${c.body}" ${K}/>
<path d="M31 34H65V80H31Z" fill="${c.body}" ${K}/>
<path d="M57 34H65V80H57Z" fill="${c.shade}"/>
<path d="M28 33H68V40H28Z" fill="${c.shade}" ${K}/>
<path d="M48 47.5a8.5 8.5 0 1 0 .1 0Z" fill="${c.lite}" ${K}/>
<path d="M48 52a4 4 0 1 0 .1 0Z" fill="${c.shade}" ${k}/>
<path d="M30 74H66L72 83H24Z" fill="${c.shade}" ${K}/>
<path d="M22 83H74V89H22Z" fill="${c.body}" ${K}/>`;
};

/* Chapter 20 - an airliner climbing, seen from above: the left half in shade, the right in light. Points are drawn nose-up
   and turned 42 degrees in the function, which is what a program may do and a path alone may not. */
CHAPTER_ICON["Chapter 20: Aviation Facilities"] = (c) => {
  const a = 42 * Math.PI / 180, cs = Math.cos(a), sn = Math.sin(a), K = .88;
  const P = (x, y) => [(48 + (x * cs - y * sn) * K).toFixed(1), (48 + (x * sn + y * cs) * K).toFixed(1)].join(" ");
  const half = [[0, -43], [2.2, -42], [3.8, -37], [4.4, -28], [4.4, -9], [41, 17], [41, 24], [4.4, 11], [3.6, 28], [17, 38], [17, 42.5], [2.6, 39], [1.6, 43.5]];
  const mir = p => half.map(([x, y]) => [-x, y]);
  const right = "M" + half.map(([x, y]) => P(x, y)).join("L") + "L" + P(0, 44) + "Z";
  const L = mir().reverse();
  const left = "M" + P(0, -43) + "L" + P(0, 44) + "L" + half.slice().reverse().map(([x, y]) => P(-x, y)).join("L") + "Z";
  const whole = "M" + half.map(([x, y]) => P(x, y)).join("L") + "L" + P(0, 44) + "L" + half.slice().reverse().map(([x, y]) => P(-x, y)).join("L") + "Z";
  return `
<path d="${whole}" fill="${c.body}" stroke="${c.ink}" stroke-width="2.6"/>
<path d="${left}" fill="${c.shade}"/>
<path d="M${P(0, -43)}L${P(0, 44)}" fill="none" stroke="${c.ink}" stroke-width="1.4"/>
<path d="M${P(2.2, -37)}L${P(2.8, -24)}" fill="none" stroke="${c.lite}" stroke-width="2.2"/>`;
};
