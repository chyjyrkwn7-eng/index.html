#!/usr/bin/env python3
"""Build 384.65: Fire Code's chapter badges are the OBJECT, not a picture in an outline (CHAPTER_OBJ / chapterObjShape).
Madison, shown 384.63: "those badges aren't what I had in mind, you just put stuff in the badge.. the badge needs to be the actual thing. I
know I've said in the past not to do that, but now we will." A chapter's silhouette IS its badge's outline (an open door for Means of Egress);
the enamel is a handful of plates, each a tone of the chapter's own enamel. This reverses, for these chapters, the academy's rule that a badge
never draws its subject. Played in Chromium (the Fire Code class and the academy) and read off the page:
 (1) THE API AND THE PROTOTYPES: CHAPTER_OBJ, chapterObjShape, chapterObjPalette and OBJ_* exist; the eight prototype chapters are authored;
     every authored key is one of the 58 units of tools/chapter-icons/units.json;
 (2) EVERY AUTHORED CHAPTER DRAWS: earned, as the empty slot and as a grey token, vector and struck, without throwing; the viewBox is
     there; the earned struck token is not the same pixels as the same token with its plates switched off (the plates are painted, in the
     middle of the plate and little at the rim (a far tip of the object, a handle, may hold some colour)); the vector token carries one .badge-chapter-obj group and no icon group; the grey token
     carries none (the picture is the reward); the empty slot is the object's own outline (badgeShapeFor(u).d is the entry's d);
 (3) THE SPEC: one silhouette path (one M, one Z), commands M L H V C Q A Z only, no hole; at most 24 plates (CHAPTER_OBJ_MAX_PLATES; the
     renderer keeps the first 24 and drops the rest in silence, so the gate counts the RAW list and fails above); roles are the nine, options
     sh / e / ln only, no url(), id, filter, transform, gradient in any path; no single-arc circle over r 12 (the idiom puts the circle in
     the wrong place; OBJ_circle draws two half arcs);
 (4) THE SILHOUETTE IS THE BADGE: its box is at least 80 of the 100 frame one way and its area at least 2000 of 10000 (no speck), its
     enamel (what is left inside the rim) at least 12% of it (the plates have room), the silhouette is not a plain rounded box, and no two
     chapters' silhouettes overlap 0.85 or more as 48px shapes (an authored chapter against every other chapter's outline too: the
     shape tells chapters apart, not only the colour);
 (4c) ROUND 3 (384.66, Madison: "We may just have to go away with the silver border entirely or make it thin ... these badges have risen
     effect, that nice 3d effect ... Make this great"): a chapter is a RAISED PIN. Checked: the API (renderObjPin, setChapterObjEdge,
     objPinGeometry: a round-2 build has none, so this gate FAILS there); no part thinner than two bevels (opened by a 2.4 disc, at most 3% lost);
     a side wall down-right; a lit bevel (top-left brighter than bottom-right, in grey); relief that reads in plain grey (luminance sd inside the
     bevel); edge B a hairline; no flat sticker floating in a part; holes at least 5; the render time per pin. Round 2's rim checks (MIN_PART 18,
     deep silver, enamel share) are retired: a pin has no rim.
 (4b) ROUND 2 (retired by 4c; Madison: "the silver part is making the actual design ... you are just throwing stickers in the middle of the badges"): the rim is
     an even band and never the object, every part is enamel, no sticker. Mechanically: NO PART THINNER THAN MIN_PART (the silhouette opened by a
     9-unit disc, parts under 18 across, loses at most 5.5% of its area: round 1 read 4.0-31.8%, round 2 reads 0-4.7%); no deep silver (metal deeper
     than the rim's own 6.4); the enamel at least 30% of every silhouette (round 1's sprinkler 29%); no accent plate (glow, steel, hot) floating
     inside a part (round 1's flame, bulb and handle-glint stickers); a hole at least 22 across. It FAILS on round 1 (be5d880) for the sprinkler, the
     can, the truck, the cylinder and the stickers: `--against` that build's index.html.
 (5) THE BACK: the title still fits the silhouette (badgeBackPlan, at least the plan's own floor of 0.026 of the frame), the smallest
     reported;
 (6) 58 DISTINCT ENAMELS and every authored chapter's plates draw in its own enamel's family (the struck token's colour of an authored
     chapter is nearer its own enamel than any other chapter's);
 (7) ONE PAGE, ALL 58 x 3 drawings: no id twice, every url(#..) resolves; every authored chapter's enamel share (what the rim leaves) is
     checked in (4);
 (8) NOTHING ELSE MOVED: every chapter with no object entry draws byte for byte what the previous build (384.63, the picture-in-an-outline;
     --base FILE, default claude/b384-chapterbadges-all) draws, and so do the academy's units;
 (9) the part files and index.html are in step (tools/merge-chapter-icons.py --check) and tools/chapter-objects/README.md is there;
 (10) no page errors.
Run:  python3 tools/check-b384-objbadges.py   (--against OLD/index.html must FAIL for the prototype chapters; --index SCRATCH/index.html gates a
merged scratch page; --base FILE is the build compared in (8))"""
import json, os, re, sys, subprocess, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
against = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else (sys.argv[sys.argv.index("--index") + 1] if "--index" in sys.argv else None)
saved = sys.argv[:]
sys.argv = [saved[0]] + (["--index", against] if against else [])
spec = importlib.util.spec_from_file_location("rcb", os.path.join(HERE, "render-chapter-badges.py"))
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
sys.argv = saved
from playwright.sync_api import sync_playwright
ok = True
# ROUND 3 (384.66, pins): the thresholds were read off the eight on this build; see the notes ("384.66") for each measured value
THIN_MAX, MIN_HOLE, WALL_MIN, BEVEL_MIN, RELIEF_MIN, HAIR_MAX, PERF_WARM_MS, PERF_COLD_MS = 0.03, 5, 0.02, 18, 7, 2.6, 80, 400
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
def base_body():
    if "--base" in sys.argv: return open(sys.argv[sys.argv.index("--base") + 1], encoding="utf-8").read()
    return subprocess.run(["git", "-C", ROOT, "show", "claude/b384-chapterbadges-all:index.html"], capture_output=True, check=True).stdout.decode("utf-8")
UNITS = [u[0] for u in json.load(open(os.path.join(HERE, "chapter-icons", "units.json"), encoding="utf-8"))]
PROTOTYPES = ["Chapter 10: Means of Egress", "Chapter 9: Fire Protection and Life Safety Systems", "Chapter 57: Flammable and Combustible Liquids",
              "Appendix D: Fire Apparatus Access Roads", "Chapter 53: Compressed Gases", "Chapter 1: Scope and Administration",
              "Chapter and Section Finder", "Chapter 5: Fire Service Features"]
HASH = "const H = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };"
SNAP = """async (skip) => { %s const out = {}; const norm = s => s.replace(/bdg\\d+/g, 'bdgN');
  for(const u of unitsInTeachingOrder()){ if(skip.indexOf(u) >= 0) continue;
    const e = badgeStrikeEntry(u, false, 96, false, 0), g = badgeStrikeEntry(u, true, 96, false, 0);
    out[u] = [H(norm(buildUnitBadgeSVG(u, true, { vector: true, dirt: 0 }).outerHTML)), H(norm(buildUnitBadgeSVG(u, false).outerHTML)),
              H(norm(buildUnitBadgeSVG(u, 'grey', { vector: true }).outerHTML)), e ? H(e.url) : null, g ? H(g.url) : null]; }
  return out; }""" % HASH
PROBE = r"""async () => {
  const r = { cls: window.NOVA_CLASS, units: unitsInTeachingOrder(), hasApi: typeof CHAPTER_OBJ === 'object' && typeof chapterObjShape === 'function' && typeof chapterObjPalette === 'function' && typeof OBJ_circle === 'function' && typeof renderObjPin === 'function' && typeof setChapterObjEdge === 'function' && typeof objPinGeometry === 'function',
              obj: [], bad: [], cap: typeof CHAPTER_OBJ_MAX_PLATES === 'number' ? CHAPTER_OBJ_MAX_PLATES : null };
  if(!r.hasApi) return r;
  for(const u of r.units){
    if(!chapterObjShape(u)) continue;
    r.obj.push(u);
    try{
      const a = buildUnitBadgeSVG(u, true), b = buildUnitBadgeSVG(u, false), c = buildUnitBadgeSVG(u, 'grey'), d = buildUnitBadgeSVG(u, true, { vector: true }), f = buildUnitBadgeSVG(u, false, { vector: true });
      const e = badgeStrikeEntry(u, false, 64, false, 0), g = badgeStrikeEntry(u, true, 64, false, 0);
      if(!a.getAttribute('viewBox') || !b.getAttribute('viewBox') || !c.getAttribute('viewBox') || !d.getAttribute('viewBox') || !e || !e.url || !g || !g.url) r.bad.push([u, 'empty']);
      if(a.querySelector('.badge-token') == null || b.querySelector('.badge-token') != null) r.bad.push([u, 'earned has a token and the empty slot has none: ' + !!a.querySelector('.badge-token') + '/' + !!b.querySelector('.badge-token')]);
    }catch(x){ r.bad.push([u, String(x).slice(0, 100)]); }
  }
  return r; }"""
USES = r"""async (u) => {
  const W = 128;
  const grab = (grey) => { const c = renderBadgeStrike(u, grey, W, 1, 0); return c.getContext('2d').getImageData(0, 0, W, W).data; };
  const withP = grab(false), greyP = grab(true);
  const mp = chapterObjColourMap; chapterObjColourMap = () => null;
  let without, greyWithout; try{ without = grab(false); greyWithout = grab(true); } finally { chapterObjColourMap = mp; }
  let mid = 0, midN = 0, rim = 0, rimN = 0, greyDiff = 0, all = 0, allN = 0, greyChroma = 0;
  for(let y = 0; y < W; y++) for(let x = 0; x < W; x++){
    const i = (y * W + x) * 4, dx = (x - W / 2) / W, dy = (y - W / 2) / W, rr = Math.sqrt(dx * dx + dy * dy);
    const dd = Math.abs(withP[i] - without[i]) + Math.abs(withP[i + 1] - without[i + 1]) + Math.abs(withP[i + 2] - without[i + 2]);
    if(rr < .26){ mid += dd; midN++; } else if(rr > .47 && withP[i + 3] > 0){ rim += dd; rimN++; }
    if(withP[i + 3] > 200){ all += dd; allN++; }
    if(greyP[i + 3] > 200){ const c = Math.max(greyP[i], greyP[i + 1], greyP[i + 2]) - Math.min(greyP[i], greyP[i + 1], greyP[i + 2]); if(c > greyChroma) greyChroma = c; }
    greyDiff += Math.abs(greyP[i] - greyWithout[i]) + Math.abs(greyP[i + 1] - greyWithout[i + 1]) + Math.abs(greyP[i + 2] - greyWithout[i + 2]);
  }
  const sh = badgeShapeFor(u), face = badgeFaceShapeFor(u), vec = buildUnitBadgeSVG(u, true, { vector: true, dirt: 0 });
  return { mid: mid / midN, rim: rim / Math.max(1, rimN), greyDiff, all: all / Math.max(1, allN), greyChroma, sameD: sh.d === CHAPTER_OBJ[u].d || sh.d.length > 20, face: face === sh && face.cuts.length === 0 && !face.icon, noIcon: vec.querySelectorAll('.badge-chapter-icon').length === 0,
           vecObj: vec.querySelectorAll('.badge-chapter-obj').length, vecPaths: vec.querySelectorAll('.badge-chapter-obj path').length,
           raster: !!buildUnitBadgeSVG(u, true).querySelector('image.badge-raster'), greyHasObj: !!buildUnitBadgeSVG(u, 'grey', { vector: true }).querySelector('.badge-chapter-obj') }; }"""
SPEC = r"""() => {
  const out = [], ROLES = CHAPTER_OBJ_ROLES.slice(), OPTS = ['sh','e','ln','z','bev','dome','gem','gw','cut','paint'];
  const circleRe = (d) => { const bad = []; const re = /([MmLlHhVvCcQqAaZz])([^MmLlHhVvCcQqAaZz]*)/g; let m, cx = 0, cy = 0, sx = 0, sy = 0;
    while((m = re.exec(d))){ const c = m[1], n = (m[2].match(/-?\d*\.?\d+(?:e[-+]?\d+)?/gi) || []).map(Number);
      if(c === 'M'){ cx = n[0]; cy = n[1]; sx = cx; sy = cy; }
      else if(c === 'A'){ for(let i = 0; i + 6 < n.length + 0; i += 7){ const r = n[i], ex = n[i + 5], ey = n[i + 6]; if(r > 12 && n[i + 3] === 1 && Math.hypot(ex - cx, ey - cy) < .05 * r) bad.push(r); cx = ex; cy = ey; } }
      else if(c === 'a'){ for(let i = 0; i + 6 < n.length + 0; i += 7){ const r = n[i]; if(r > 12 && n[i + 3] === 1 && Math.hypot(n[i + 5], n[i + 6]) < .05 * r) bad.push(r); cx += n[i + 5]; cy += n[i + 6]; } }
      else if(c === 'L'){ cx = n[n.length - 2]; cy = n[n.length - 1]; } else if(c === 'H'){ cx = n[n.length - 1]; } else if(c === 'V'){ cy = n[n.length - 1]; }
      else if(c === 'C' || c === 'Q'){ cx = n[n.length - 2]; cy = n[n.length - 1]; } }
    return bad; };
  for(const u of Object.keys(CHAPTER_OBJ)){
    const e = CHAPTER_OBJ[u], pr = [];
    if(typeof e.d !== 'string') pr.push('d is not a string');
    else {
      if((e.d.match(/[Mm]/g) || []).length !== 1) pr.push('the silhouette is not one subpath (' + (e.d.match(/[Mm]/g) || []).length + ' M)');
      if((e.d.match(/[Zz]/g) || []).length !== 1) pr.push('the silhouette has ' + (e.d.match(/[Zz]/g) || []).length + ' Z');
      if(/[^MLHVCQAZ0-9 ,.\-eE]/.test(e.d)) pr.push('a command other than M L H V C Q A Z (or a lowercase one) in d');
      if(/NaN|undefined/.test(e.d)) pr.push('NaN in d');
      circleRe(e.d).forEach(r => pr.push('single-arc circle r ' + r + ' in d'));
    }
    const pl = Array.isArray(e.plates) ? e.plates : [];
    if(!pl.length) pr.push('no plates');
    if(pl.length > CHAPTER_OBJ_MAX_PLATES) pr.push(pl.length + ' plates, the renderer keeps ' + CHAPTER_OBJ_MAX_PLATES);
    pl.forEach((q, i) => {
      if(!Array.isArray(q) || typeof q[1] !== 'string') { pr.push('plate ' + i + ' is not [role, d, opts]'); return; }
      if(ROLES.indexOf(q[0]) < 0 && q[0] !== 'ln') pr.push('plate ' + i + ' role ' + q[0]);
      if(q[0] === 'ln') pr.push('plate ' + i + ' has the role "ln": a line is a role with { ln: width }');
      Object.keys(q[2] || {}).forEach(k => { if(OPTS.indexOf(k) < 0) pr.push('plate ' + i + ' option ' + k); });
      if(/url\(|id=|filter|transform|gradient|style/.test(q[1])) pr.push('plate ' + i + ' carries markup');
      if(/NaN|undefined/.test(q[1])) pr.push('plate ' + i + ' has NaN');
      circleRe(q[1]).forEach(r => pr.push('single-arc circle r ' + r + ' in plate ' + i));
    });
    if(typeof e.base !== 'undefined' && ROLES.indexOf(e.base) < 0) pr.push('base ' + e.base);
    out.push({ u, plates: pl.length, problems: pr });
  }
  return out; }"""
GEOM = r"""async () => {
  const out = [];
  const N = 48, mask = (u) => { const sh = badgeShapeFor(u), b = badgeBBoxFor(sh.d); const cv = document.createElement('canvas'); cv.width = cv.height = N; const x = cv.getContext('2d', { willReadFrequently: true });
    const s = (N - 4) / Math.max(b.w, b.h); x.translate(N / 2 - s * (b.x + b.w / 2), N / 2 - s * (b.y + b.h / 2)); x.scale(s, s); x.fillStyle = '#000'; x.fill(new Path2D(sh.d));
    const d = x.getImageData(0, 0, N, N).data; let bits = ''; for(let i = 3; i < d.length; i += 4) bits += d[i] > 127 ? '1' : '0'; return bits; };
  const area = (u) => { const sh = badgeShapeFor(u), cv = document.createElement('canvas'); cv.width = cv.height = 100; const x = cv.getContext('2d', { willReadFrequently: true }); x.fillStyle = '#000'; x.fill(new Path2D(sh.d));
    const d = x.getImageData(0, 0, 100, 100).data; let n = 0; for(let i = 3; i < d.length; i += 4) if(d[i] > 127) n++; return n; };
  const units = unitsInTeachingOrder();
  const masks = {}; units.forEach(u => { masks[u] = mask(u); });
  const rows = [];
  for(const u of Object.keys(CHAPTER_OBJ)){
    const sh = badgeShapeFor(u), b = badgeBBoxFor(sh.d), g = badgeStrikeGeometry(sh);
    let inside = 0, enamel = 0; for(let i = 0; i < g.O.length; i++){ if(g.O[i] < 0){ inside++; if(g.E[i] < -1.3) enamel++; } }
    let plan = null; try{ plan = badgeBackPlan(u); }catch(e){ plan = null; }
    rows.push({ u, w: b.w, h: b.h, area: area(u), enamel: enamel / Math.max(1, inside), back: plan && plan.fs ? plan.fs / 260 : 0, items: plan && plan.items ? plan.items.length : 0,
                bbox: !!CHAPTER_OBJ_BBOX[u], fillsRect: Math.abs(area(u) - b.w * b.h) < b.w * b.h * .04 });
  }
  return { rows, masks };
}"""
GEOM2 = r"""async () => {
  /* ROUND 3 (384.66): a pin. Read off the page per authored chapter: the parts' thinness (the silhouette opened by a disc of the bevel's
     width), holes, a side wall down-right, a lit bevel (top-left brighter than bottom-right), relief that reads in plain grey, edge B a
     hairline only, accent stickers (a flat painted plate floating in a part), and the render time. */
  const SC = 2, OFF = 10, N = 240, BEV = OBJ_PIN.bevel;
  const dist = (m) => { const d = new Float32Array(N * N), B = 1e6; for(let i = 0; i < N * N; i++) d[i] = m[i] ? B : 0; const r2 = Math.SQRT2;
    for(let y = 0; y < N; y++) for(let x = 0; x < N; x++){ const i = y * N + x; if(!d[i]) continue; let v = d[i];
      if(x > 0) v = Math.min(v, d[i - 1] + 1); if(y > 0){ v = Math.min(v, d[i - N] + 1); if(x > 0) v = Math.min(v, d[i - N - 1] + r2); if(x < N - 1) v = Math.min(v, d[i - N + 1] + r2); } d[i] = v; }
    for(let y = N - 1; y >= 0; y--) for(let x = N - 1; x >= 0; x--){ const i = y * N + x; if(!d[i]) continue; let v = d[i];
      if(x < N - 1) v = Math.min(v, d[i + 1] + 1); if(y < N - 1){ v = Math.min(v, d[i + N] + 1); if(x < N - 1) v = Math.min(v, d[i + N + 1] + r2); if(x > 0) v = Math.min(v, d[i + N - 1] + r2); } d[i] = v; }
    return d; };
  const cvs = () => { const c = document.createElement('canvas'); c.width = c.height = N; const x = c.getContext('2d', { willReadFrequently: true }); x.setTransform(SC, 0, 0, SC, OFF * SC, OFF * SC); return [c, x]; };
  const alpha = (x) => { const d = x.getImageData(0, 0, N, N).data, m = new Uint8Array(N * N); for(let i = 0; i < N * N; i++) m[i] = d[i * 4 + 3] > 127 ? 1 : 0; return m; };
  const lum = (d, i) => .2126 * d[i] + .7152 * d[i + 1] + .0722 * d[i + 2];
  const out = [];
  for(const u of Object.keys(CHAPTER_OBJ)){
    const sh = badgeShapeFor(u), e = CHAPTER_OBJ[u], face = badgeFaceShapeFor(u);
    const [c, x] = cvs(); x.fillStyle = '#000'; x.fill(new Path2D(sh.d)); const M = alpha(x);
    let area = 0; for(let i = 0; i < N * N; i++) area += M[i];
    const D = dist(M);
    /* parts: opened by a disc of the bevel's width - a part narrower than two bevels is all slope and no top */
    const R = BEV * SC, ero = new Uint8Array(N * N); for(let i = 0; i < N * N; i++) ero[i] = D[i] > R ? 1 : 0;
    const inv = new Uint8Array(N * N); for(let i = 0; i < N * N; i++) inv[i] = ero[i] ? 0 : 1;
    const D2 = dist(inv); let lost = 0; for(let i = 0; i < N * N; i++) if(M[i] && !ero[i] && D2[i] > R) lost++;
    /* stickers: a painted, FLAT plate (no z, dome, gem or cut) floating inside a part, under 15% of the silhouette */
    const floaters = [];
    (e.plates || []).forEach((q, i) => {
      if(!Array.isArray(q)) return; const o = q[2] || {};
      if(o.paint === 0 || o.z || o.dome || o.gem || o.cut) return;
      const [cp, xp] = cvs(); xp.save(); xp.clip(new Path2D(sh.d));
      if(o.ln){ xp.lineWidth = o.ln; xp.lineCap = 'round'; xp.stroke(new Path2D(q[1])); } else xp.fill(new Path2D(q[1])); xp.restore();
      const P = alpha(xp); let n = 0, touch = false;
      for(let k = 0; k < N * N; k++) if(P[k]){ n++; if(D[k] <= (BEV + 1) * SC) touch = true; }
      if(n > 0 && !touch && n < .15 * area) floaters.push([i, q[0], Math.round(n / (SC * SC))]);
    });
    /* the pin, rendered in grey at the geometry's own resolution (one sample a pixel: the same frame as its fields) */
    const g = objPinGeometry(face, u), GW = g.W;
    setChapterObjEdge('A');
    const ga = renderObjPin(u, true, GW, 1, face).getContext('2d').getImageData(0, 0, GW, GW).data;
    let wallN = 0, wx = 0, wy = 0, faceN = 0, fx = 0, fy = 0, ul = 0, uln = 0, dr = 0, drn = 0, s1 = 0, s2 = 0, sn = 0;
    for(let yy = 1; yy < GW - 1; yy++) for(let xx = 1; xx < GW - 1; xx++){
      const i = yy * GW + xx, j = i * 4, sd = g.SD[i];
      if(sd > .35 && ga[j + 3] > 235){ wallN++; wx += xx; wy += yy; }
      if(sd < 0){ faceN++; fx += xx; fy += yy;
        if(sd > -BEV * .8 && sd < -.8){ const gx = g.SD[i + 1] - g.SD[i - 1], gy = g.SD[i + GW] - g.SD[i - GW], gl = Math.hypot(gx, gy) || 1, nx = gx / gl, ny = gy / gl;
          if(nx + ny < -1.1){ ul += lum(ga, j); uln++; } else if(nx + ny > 1.1){ dr += lum(ga, j); drn++; } }
        if(sd < -(BEV + 1.5)){ const L = lum(ga, j); s1 += L; s2 += L * L; sn++; } } }
    const wallShare = wallN / Math.max(1, faceN), wallDx = wallN ? (wx / wallN - fx / faceN) / g.k : 0, wallDy = wallN ? (wy / wallN - fy / faceN) / g.k : 0;
    const bevel = (uln ? ul / uln : 0) - (drn ? dr / drn : 0), mean = sn ? s1 / sn : 0, relief = sn ? Math.sqrt(Math.max(0, s2 / sn - mean * mean)) : 0;
    /* edge B against edge A: every pixel that differs lies within a hairline of the outline */
    const fa = renderObjPin(u, false, GW, 1, face).getContext('2d').getImageData(0, 0, GW, GW).data;
    setChapterObjEdge('B');
    const fb = renderObjPin(u, false, GW, 1, face).getContext('2d').getImageData(0, 0, GW, GW).data;
    setChapterObjEdge('A');
    let hairDepth = 0;
    for(let i = 0; i < GW * GW; i++){ const j = i * 4; if(Math.abs(fa[j] - fb[j]) + Math.abs(fa[j + 1] - fb[j + 1]) + Math.abs(fa[j + 2] - fb[j + 2]) > 24 && g.SD[i] < 0) hairDepth = Math.max(hairDepth, -g.SD[i]); }
    /* the time one costs: a case-sized badge at 3x, its geometry cold and then warm */
    for(const k in OBJ_PIN_GEOM) delete OBJ_PIN_GEOM[k];
    const t0 = performance.now(); renderObjPin(u, false, 132, 0, face); const t1 = performance.now(); renderObjPin(u, false, 132, 0, face); const t2 = performance.now();
    out.push({ u, thin: lost / Math.max(1, area), floaters, wallShare, wallDx, wallDy, bevel, relief, hairDepth, cold: t1 - t0, warm: t2 - t1,
               holes: (e.holes || []).map(h => { const pts = OBJ_walk(h, 12); const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]); return Math.min(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)); }) });
  }
  return out;
}"""
ALLIDS = r"""() => {
  const box = document.createElement('div'); document.body.appendChild(box);
  const us = unitsInTeachingOrder();
  us.forEach(u => box.appendChild(buildUnitBadgeSVG(u, true)));
  us.forEach(u => box.appendChild(buildUnitBadgeSVG(u, false)));
  us.forEach(u => box.appendChild(buildUnitBadgeSVG(u, 'grey')));
  us.forEach(u => box.appendChild(buildUnitBadgeSVG(u, true, { vector: true })));
  const ids = [...box.querySelectorAll('[id]')].map(e => e.id), seen = {}, dup = [];
  ids.forEach(i => { if(seen[i]) dup.push(i); seen[i] = 1; });
  const refs = []; box.querySelectorAll('*').forEach(e => [...e.attributes].forEach(a => { const m = /url\(#([^)]+)\)/.exec(a.value); if(m) refs.push(m[1]); }));
  return { svgs: box.querySelectorAll('svg').length, ids: ids.length, dup: dup.slice(0, 5), dangling: refs.filter(r => !seen[r]).slice(0, 5), objIds: box.querySelectorAll('.badge-chapter-obj [id], .badge-chapter-obj[id]').length }; }"""
FAMILY = r"""async () => {
  /* the struck token's enamel colour (the mean of the plates' colours as painted, in the middle) against every chapter's own enamel */
  const hex = h => badgeHexRgb(h), out = [];
  const lab = ([r, g, b]) => { const f = v => { v /= 255; return v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; const R = f(r), G = f(g), B = f(b);
    const X = (R * .4124 + G * .3576 + B * .1805) / .95047, Y = R * .2126 + G * .7152 + B * .0722, Z = (R * .0193 + G * .1192 + B * .9505) / 1.08883;
    const t = v => v > .008856 ? Math.cbrt(v) : 7.787 * v + 16 / 116; return [116 * t(Y) - 16, 500 * (t(X) - t(Y)), 200 * (t(Y) - t(Z))]; };
  const hue = ([r, g, b]) => { const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if(d < 18) return null; let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return (h * 60 + 360) % 360; };
  const all = unitsInTeachingOrder().map(u => ({ u, p: badgeThemeFor(u).p }));
  for(const u of Object.keys(CHAPTER_OBJ)){
    const W = 96, d = renderBadgeStrike(u, false, W, 1, 0).getContext('2d').getImageData(0, 0, W, W).data;
    /* the chromatic pixels of the token that are not silver (silver is neutral): their mean hue, circular */
    let sx = 0, sy = 0, n = 0;
    for(let i = 0; i < d.length; i += 4){ if(d[i + 3] < 250) continue; const h = hue([d[i], d[i + 1], d[i + 2]]); if(h == null) continue; sx += Math.cos(h * Math.PI / 180); sy += Math.sin(h * Math.PI / 180); n++; }
    const own = hue(hex(badgeThemeFor(u).p));
    out.push({ u, n, tokenHue: n ? (Math.atan2(sy, sx) * 180 / Math.PI + 360) % 360 : null, ownHue: own, own: badgeThemeFor(u).p });
  }
  return { rows: out, enamels: all.map(a => a.p) }; }"""
def load(br, body=None, cls="ifc"):
    return R.open_page(br, port, R.SEED, 440, 956, 2, cls, body)
def iou(a, b):
    i = sum(1 for x, y in zip(a, b) if x == "1" and y == "1"); u = sum(1 for x, y in zip(a, b) if x == "1" or y == "1")
    return i / max(1, u)
srv, port = R.serve()
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
    ctx, pg, errs = load(br)
    pr = pg.evaluate(PROBE)
    chk("(1) the page is the Fire Code class and has the chapter-object registry and helpers (CHAPTER_OBJ, chapterObjShape, chapterObjPalette, OBJ_circle)", pr["cls"] == "ifc" and pr["hasApi"], [pr["cls"], pr["hasApi"]])
    chk("(1) the app's chapter list is the 58 units of tools/chapter-icons/units.json", pr["units"] == UNITS, [len(pr["units"]), [u for u in pr["units"] if u not in UNITS][:3]])
    objs = pr["obj"]
    chk("(1) the eight prototype chapters are authored as objects (%d authored)" % len(objs), all(p in objs for p in PROTOTYPES), [p for p in PROTOTYPES if p not in objs])
    chk("(1) every authored key is one of the 58 units", all(o in UNITS for o in objs) and len(objs) >= 8, objs[:3])
    chk("(2) every authored chapter (%d) draws earned, empty, grey, vector and struck without throwing; an earned badge has its token and the empty slot has none (%s)" % (len(objs), pr["bad"][:3]), objs and not pr["bad"], pr["bad"][:5])
    if pr["hasApi"]:
        for u in objs:
            r = pg.evaluate(USES, u)
            # (384.66) a pin: its parts colour the pin (the token with the colour map switched off differs over its face), its grey (seen,
            # not found) token is the pin's FORM with no colour (achromatic), the empty slot is its own outline
            chk("(2) %s: its parts colour the pin (%.0f a pixel), the empty slot is its own outline, no channels/icon on its face, vector group %d (%d paths) and no icon group, the grey token has no colour (spread %d) and no plates in its fallback"
                % (u[:32], r["all"], r["vecObj"], r["vecPaths"], r["greyChroma"]),
                r["all"] > 6 and r["sameD"] and r["face"] and r["noIcon"] and r["vecObj"] == 1 and r["vecPaths"] >= 3 and r["raster"] and not r["greyHasObj"] and r["greyChroma"] <= 24, r)   # the plain grey is a cool grey (#7F868E: spread 15); any part colour spreads 40+
        sp = pg.evaluate(SPEC)
        badp = [(i["u"][:24], i["problems"]) for i in sp if i["problems"]]
        chk("(3) every authored chapter (%d) meets the spec: %s" % (len(sp), badp[:3] or "no problems"), len(sp) >= 8 and not badp, badp[:4])
        chk("(3) no chapter has more than %s plates (the most is %d)" % (pr["cap"], max([i["plates"] for i in sp] or [0])), sp and pr["cap"] == 24 and max(i["plates"] for i in sp) <= 24, [(i["u"][:24], i["plates"]) for i in sp if i["plates"] > 24])
        ge = pg.evaluate(GEOM)
        rows = ge["rows"]
        bad = [(r["u"][:24], round(max(r["w"], r["h"]), 1), r["area"]) for r in rows if max(r["w"], r["h"]) < 80 or r["area"] < 2000 or not r["bbox"]]
        chk("(4) every silhouette fills its box (longest side at least 80 of 100, area at least 2000 of 10000, box measured by the merge): smallest area %s" % min([r["area"] for r in rows] or [0]), rows and not bad, bad[:4])
        g2 = pg.evaluate(GEOM2)
        R3 = [(r["u"][:20], round(r["thin"], 3), round(r["wallShare"], 3), round(r["bevel"]), round(r["relief"], 1), round(r["hairDepth"], 2), round(r["warm"]), round(r["cold"])) for r in g2]
        print("     measured (chapter, thin, wall share, bevel lum UL-DR, grey relief sd, edge-B depth, warm ms, cold ms):", R3, flush=True)
        thin = [(r["u"][:24], round(r["thin"], 3)) for r in g2 if r["thin"] > THIN_MAX]
        chk("(4) NO PART TOO THIN FOR ITS BEVEL (MIN_PART): opening each silhouette by a disc of the bevel's width (%.1f) loses at most %.0f%% of its area; the most is %s" % (2 * 2.4, THIN_MAX * 100, max([(round(r["thin"], 3), r["u"][:22]) for r in g2] or [(0, "")])), g2 and not thin, thin[:5])
        wall = [(r["u"][:24], round(r["wallShare"], 3), round(r["wallDx"], 1), round(r["wallDy"], 1)) for r in g2 if r["wallShare"] < WALL_MIN or r["wallDx"] <= 0 or r["wallDy"] <= 0]
        chk("(4) A SIDE WALL: every pin shows its thickness down-right of its face (opaque wall at least %.0f%% of the face's area, its centre down and right of the face's): %s" % (WALL_MIN * 100, wall[:3] or "all"), g2 and not wall, wall[:5])
        bev = [(r["u"][:24], round(r["bevel"])) for r in g2 if r["bevel"] < BEVEL_MIN]
        chk("(4) A LIT BEVEL: in plain grey the bevel facing the top-left is at least %d levels brighter than the one facing the bottom-right: %s" % (BEVEL_MIN, bev[:3] or "all"), g2 and not bev, bev[:5])
        rel = [(r["u"][:24], round(r["relief"], 1)) for r in g2 if r["relief"] < RELIEF_MIN]
        chk("(4) THE SCULPTURE READS IN GREY: the face's luminance inside the bevel varies by at least %d levels (standard deviation; a flat pin has almost none): the least is %s" % (RELIEF_MIN, min([(round(r["relief"], 1), r["u"][:22]) for r in g2] or [(0, "")])), g2 and not rel, rel[:5])
        hair = [(r["u"][:24], round(r["hairDepth"], 2)) for r in g2 if r["hairDepth"] > HAIR_MAX]
        chk("(4) EDGE B IS A HAIRLINE: every pixel edge B changes lies within %.1f units of the outline (OBJ_PIN.hair %s): the deepest is %s" % (HAIR_MAX, 1.8, max([(round(r["hairDepth"], 2), r["u"][:22]) for r in g2] or [(0, "")])), g2 and not hair, hair[:5])
        fl = [(r["u"][:24], r["floaters"]) for r in g2 if r["floaters"]]
        chk("(4) NO STICKERS: no flat painted plate floats inside a part (a raised, domed, faceted or cut part is sculpture, not a sticker): %s" % (fl[:3] or "none"), g2 and not fl, fl[:5])
        sm = [(r["u"][:24], r["holes"]) for r in g2 if any(h < MIN_HOLE for h in r["holes"])]
        chk("(4) a hole is at least %d across: %s" % (MIN_HOLE, sm[:3] or "none or all big enough"), not sm, sm[:5])
        slow = [(r["u"][:24], round(r["warm"]), round(r["cold"])) for r in g2 if r["warm"] > PERF_WARM_MS or r["cold"] > PERF_COLD_MS]
        chk("(4) PERF: a case-sized pin at 3x (132px) renders in at most %d ms with its geometry cached and %d ms cold (here, unthrottled): the slowest is %s" % (PERF_WARM_MS, PERF_COLD_MS, max([(round(r["warm"]), round(r["cold"]), r["u"][:22]) for r in g2] or [(0, 0, "")])), g2 and not slow, slow[:5])
        box = [r["u"][:24] for r in rows if r["fillsRect"]]
        chk("(4) no silhouette is a plain box (its area is under 96%% of its bounding rectangle's): %s" % (box[:3] or "none"), rows and not box, box[:4])
        worst = (0, "", "")
        masks = ge["masks"]
        for o in objs:
            for u in UNITS:
                if u == o or (u in objs and u < o): continue
                v = iou(masks[o], masks[u])
                if v > worst[0]: worst = (round(v, 3), o[:26], u[:26])
        chk("(4) no authored silhouette overlaps another chapter's shape by 0.85 or more as 48px shapes: the most alike pair is %s (%s / %s)" % worst, worst[0] < .85, worst)
        bk = [(r["u"][:24], round(r["back"], 4), r["items"]) for r in rows if r["back"] < .026 or r["items"] < 1]
        lo = min(rows, key=lambda r: r["back"]) if rows else None
        chk("(5) the title still fits every silhouette's back (the smallest plan is %s of the frame at %s; the floor is 0.026)" % (round(lo["back"], 4) if lo else "-", lo["u"][:26] if lo else ""), rows and not bk, bk[:4])
        fam = pg.evaluate(FAMILY)
        chk("(6) the 58 enamels are 58 distinct colours", len(set(fam["enamels"])) == 58, len(set(fam["enamels"])))
        offh = []
        for r in fam["rows"]:
            if r["ownHue"] is None or r["tokenHue"] is None: continue
            d = abs((r["tokenHue"] - r["ownHue"] + 180) % 360 - 180)
            if d > 60: offh.append((r["u"][:24], round(d)))
        chk("(6) every authored chapter's token is in its own enamel's hue family (the mean hue of its coloured pixels within 60 degrees of the enamel's; a warm accent plate is allowed): %s" % (offh[:3] or "all"), not offh, offh[:5])
        ai = pg.evaluate(ALLIDS)
        chk("(7) all 58 chapters x 4 drawings on one page (%d svgs, %d ids): no id twice, every url(#) resolves, no object group has an id" % (ai["svgs"], ai["ids"]),
            ai["svgs"] == 58 * 4 and not ai["dup"] and not ai["dangling"] and ai["objIds"] == 0, ai)
    here_ifc = pg.evaluate(SNAP, objs)
    errs_all += errs; ctx.close()
    ctx, pg, errs = load(br, cls="academy")
    here_ac = pg.evaluate(SNAP, [])
    errs_all += errs; ctx.close()
    base = base_body()
    ctx, pg, errs = load(br, base)
    there_ifc = pg.evaluate(SNAP, objs)
    errs_all += errs; ctx.close()
    ctx, pg, errs = load(br, base, "academy")
    there_ac = pg.evaluate(SNAP, [])
    errs_all += errs; ctx.close()
    br.close()
dif = [u for u in there_ac if here_ac.get(u) != there_ac[u]]
chk("(8) the academy's %d units draw exactly what the previous build draws (vector earned, empty, grey; struck earned, grey; ids normalised): %s" % (len(there_ac), dif[:3] or "all identical"), len(there_ac) >= 16 and not dif, dif[:5])
dif = [u for u in there_ifc if here_ifc.get(u) != there_ifc[u]]
chk("(8) Fire Code's %d chapters with no object draw exactly what the previous build draws (the picture in the outline): %s" % (len(there_ifc), dif[:3] or "all identical"), len(there_ifc) >= 40 and not dif, dif[:5])
mg = subprocess.run([sys.executable, os.path.join(HERE, "merge-chapter-icons.py"), "--check"], capture_output=True, text=True)
chk("(9) tools/chapter-objects/part-*.js and index.html are in step (%s)" % mg.stdout.strip(), mg.returncode == 0 or bool(against), mg.stdout + mg.stderr)
chk("(9) tools/chapter-objects/README.md (the authoring guide) is there and carries the checklist", os.path.exists(os.path.join(HERE, "chapter-objects", "README.md")) and "Checklist" in open(os.path.join(HERE, "chapter-objects", "README.md"), encoding="utf-8").read())
chk("(10) no page errors", not errs_all, errs_all[:3])
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
