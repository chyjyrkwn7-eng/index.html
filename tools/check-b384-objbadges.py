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
  const r = { cls: window.NOVA_CLASS, units: unitsInTeachingOrder(), hasApi: typeof CHAPTER_OBJ === 'object' && typeof chapterObjShape === 'function' && typeof chapterObjPalette === 'function' && typeof OBJ_circle === 'function',
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
  let mid = 0, midN = 0, rim = 0, rimN = 0, greyDiff = 0;
  for(let y = 0; y < W; y++) for(let x = 0; x < W; x++){
    const i = (y * W + x) * 4, dx = (x - W / 2) / W, dy = (y - W / 2) / W, rr = Math.sqrt(dx * dx + dy * dy);
    const dd = Math.abs(withP[i] - without[i]) + Math.abs(withP[i + 1] - without[i + 1]) + Math.abs(withP[i + 2] - without[i + 2]);
    if(rr < .26){ mid += dd; midN++; } else if(rr > .47 && withP[i + 3] > 0){ rim += dd; rimN++; }
    greyDiff += Math.abs(greyP[i] - greyWithout[i]) + Math.abs(greyP[i + 1] - greyWithout[i + 1]) + Math.abs(greyP[i + 2] - greyWithout[i + 2]);
  }
  const sh = badgeShapeFor(u), face = badgeFaceShapeFor(u), vec = buildUnitBadgeSVG(u, true, { vector: true, dirt: 0 });
  return { mid: mid / midN, rim: rim / Math.max(1, rimN), greyDiff, sameD: sh.d === CHAPTER_OBJ[u].d || sh.d.length > 20, face: face === sh && face.cuts.length === 0 && !face.icon, noIcon: vec.querySelectorAll('.badge-chapter-icon').length === 0,
           vecObj: vec.querySelectorAll('.badge-chapter-obj').length, vecPaths: vec.querySelectorAll('.badge-chapter-obj path').length,
           raster: !!buildUnitBadgeSVG(u, true).querySelector('image.badge-raster'), greyHasObj: !!buildUnitBadgeSVG(u, 'grey', { vector: true }).querySelector('.badge-chapter-obj') }; }"""
SPEC = r"""() => {
  const out = [], ROLES = ['field','lite','body','shade','deep','ink','glow','steel','hot'], OPTS = ['sh','e','ln'];
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
            chk("(2) %s: plates are painted on the struck token (middle %.0f, rim %.1f), the empty slot is its own outline, no channels/icon on its face, vector group %d (%d paths) and no icon group, none on a grey (diff %s)"
                % (u[:32], r["mid"], r["rim"], r["vecObj"], r["vecPaths"], r["greyDiff"]),
                r["mid"] > 18 and r["rim"] < 6 and r["sameD"] and r["face"] and r["noIcon"] and r["vecObj"] == 1 and r["vecPaths"] >= 3 and r["raster"] and not r["greyHasObj"] and r["greyDiff"] == 0, r)
        sp = pg.evaluate(SPEC)
        badp = [(i["u"][:24], i["problems"]) for i in sp if i["problems"]]
        chk("(3) every authored chapter (%d) meets the spec: %s" % (len(sp), badp[:3] or "no problems"), len(sp) >= 8 and not badp, badp[:4])
        chk("(3) no chapter has more than %s plates (the most is %d)" % (pr["cap"], max([i["plates"] for i in sp] or [0])), sp and pr["cap"] == 24 and max(i["plates"] for i in sp) <= 24, [(i["u"][:24], i["plates"]) for i in sp if i["plates"] > 24])
        ge = pg.evaluate(GEOM)
        rows = ge["rows"]
        bad = [(r["u"][:24], round(max(r["w"], r["h"]), 1), r["area"]) for r in rows if max(r["w"], r["h"]) < 80 or r["area"] < 2000 or not r["bbox"]]
        chk("(4) every silhouette fills its box (longest side at least 80 of 100, area at least 2000 of 10000, box measured by the merge): smallest area %s" % min([r["area"] for r in rows] or [0]), rows and not bad, bad[:4])
        thin = [(r["u"][:24], round(r["enamel"], 3)) for r in rows if r["enamel"] < .12]
        chk("(4) every silhouette leaves its plates room: the smallest enamel share (what is left inside the rim) is %s, at least .12" % (min(r["enamel"] for r in rows) if rows else "-"), rows and not thin, thin[:4])
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
        bk = [(r["u"][:24], round(r["back"], 4), r["items"]) for r in rows if r["back"] < .026 or r["items"] < 2]
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
