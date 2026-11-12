#!/usr/bin/env python3
"""Build 384.61, chapter badges PHASE 1: the framework every Fire Code chapter's icon is drawn into.
Madison: "Badges are gonna be designed based on what the chapter is about / the title (mostly the title). For example Means of
Egress could be a door in the open position? Make them cool."
Played in Chromium, in the Fire Code class and in the academy, and read off the page:
 (1) A RESOLVER FOR EVERY CHAPTER: CHAPTER_ICON / chapterIconFor exist; all 58 units (the list in tools/chapter-icons/units.json, in the
     app's teaching order) draw earned, as the empty slot and as a grey token, vector and struck, without throwing - an icon or the
     fallback, never nothing; and a unit with no entry (a chapter added later) draws the fallback;
 (2) THE SAMPLES USE THE ICON PATH: every unit that has an icon draws it - its struck token differs from the same token with the icon's
     painting switched off, in the middle of the plate and nowhere near the rim; its vector token carries a .badge-chapter-icon group; its grey
     (not yet found) token draws NO icon (the picture is the reward) and is pixel-identical with the icon taken out; the face has no
     channels (one open plate);
 (3) THE SPEC, FOR EVERY ICON THAT EXISTS: at most 14 paths, only the allowed attributes, no id / filter / gradient / transform / url(),
     every colour one of the palette's, every path inside the 96 x 96 box, a figure at least a few units thick and wide enough
     to read at 26px, and no two icons alike (their 48px silhouettes' overlap under 0.85);
 (4) NOTHING ELSE MOVED: the academy's units (every one) and Fire Code's chapters with no icon draw byte-for-byte what origin/main
     draws - vector earned / empty / grey with ids normalised, and the struck earned and grey tokens;
 (5) ONE PAGE, ALL 58: every chapter earned on one page has unique ids, every url(#..) resolves, no icon group carries an id;
 (6) the part files and index.html are in step (tools/merge-chapter-icons.py --check) and the brief is there;
 (7) no page errors in either class.
Run:  python3 tools/check-b384-chapterbadges.py   (--against OLD/index.html must FAIL; --base FILE is the build compared in (4),
default origin/main's)"""
import json, os, sys, subprocess, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
against = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
saved = sys.argv[:]
sys.argv = [saved[0]] + (["--index", against] if against else [])
spec = importlib.util.spec_from_file_location("rcb", os.path.join(HERE, "render-chapter-badges.py"))
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
sys.argv = saved
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def base_body():
    if "--base" in sys.argv: return open(sys.argv[sys.argv.index("--base") + 1], encoding="utf-8").read()
    return subprocess.run(["git", "-C", ROOT, "show", "origin/main:index.html"], capture_output=True, check=True).stdout.decode("utf-8")
UNITS = [u[0] for u in json.load(open(os.path.join(HERE, "chapter-icons", "units.json"), encoding="utf-8"))]
HASH = "const H = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };"
SNAP = """async (skip) => { %s const out = {}; const norm = s => s.replace(/bdg\\d+/g, 'bdgN');
  for(const u of unitsInTeachingOrder()){ if(skip.indexOf(u) >= 0) continue;
    const e = badgeStrikeEntry(u, false, 96, false, 0), g = badgeStrikeEntry(u, true, 96, false, 0);
    out[u] = [H(norm(buildUnitBadgeSVG(u, true, { vector: true, dirt: 0 }).outerHTML)), H(norm(buildUnitBadgeSVG(u, false).outerHTML)),
              H(norm(buildUnitBadgeSVG(u, 'grey', { vector: true }).outerHTML)), e ? H(e.url) : null, g ? H(g.url) : null]; }
  return out; }""" % HASH
PROBE = r"""async () => {
  const us = unitsInTeachingOrder(), r = { cls: window.NOVA_CLASS, units: us, hasApi: typeof CHAPTER_ICON === 'object' && typeof chapterIconFor === 'function', icon: [], bad: [] };
  for(const u of us){
    try{
      const a = buildUnitBadgeSVG(u, true), b = buildUnitBadgeSVG(u, false), c = buildUnitBadgeSVG(u, 'grey'), d = buildUnitBadgeSVG(u, true, { vector: true });
      const e = badgeStrikeEntry(u, false, 64, false, 0), g = badgeStrikeEntry(u, true, 64, false, 0);
      if(!a.getAttribute('viewBox') || !b.getAttribute('viewBox') || !c.getAttribute('viewBox') || !d.getAttribute('viewBox') || !e || !e.url || !g || !g.url) r.bad.push([u, 'empty']);
    }catch(x){ r.bad.push([u, String(x).slice(0, 100)]); }
    if(r.hasApi && chapterIconFor(u)) r.icon.push(u);
  }
  return r; }"""
USES = r"""async (u) => {
  const W = 128, px = e => { const cv = document.createElement('canvas'); cv.width = cv.height = W; const x = cv.getContext('2d'); return e; };
  const grab = (grey) => { const c = renderBadgeStrike(u, grey, W, 1, 0); return c.getContext('2d').getImageData(0, 0, W, W).data; };
  const withIcon = grab(false), greyIcon = grab(true);
  /* the same token with only the icon's painting switched off (the face - no channels - stays), so the difference is the icon alone */
  const paint = chapterIconPaintStrike; chapterIconPaintStrike = () => {};
  let without, greyWithout; try{ without = grab(false); greyWithout = grab(true); } finally { chapterIconPaintStrike = paint; }
  /* the middle of the plate vs the rim: pixels within 20% of the centre are the plate, those beyond 42% are rim and wall */
  let mid = 0, midN = 0, rim = 0, rimN = 0, greyDiff = 0;
  for(let y = 0; y < W; y++) for(let x = 0; x < W; x++){
    const i = (y * W + x) * 4, dx = (x - W / 2) / W, dy = (y - W / 2) / W, rr = Math.sqrt(dx * dx + dy * dy);
    const dd = Math.abs(withIcon[i] - without[i]) + Math.abs(withIcon[i + 1] - without[i + 1]) + Math.abs(withIcon[i + 2] - without[i + 2]);
    if(rr < .2){ mid += dd; midN++; } else if(rr > .42 && withIcon[i + 3] > 0){ rim += dd; rimN++; }
    greyDiff += Math.abs(greyIcon[i] - greyWithout[i]) + Math.abs(greyIcon[i + 1] - greyWithout[i + 1]) + Math.abs(greyIcon[i + 2] - greyWithout[i + 2]) + Math.abs(greyIcon[i + 3] - greyWithout[i + 3]);
  }
  const face = badgeFaceShapeFor(u), vec = buildUnitBadgeSVG(u, true, { vector: true, dirt: 0 });
  return { mid: mid / midN, rim: rim / Math.max(1, rimN), greyDiff, noCuts: face.cuts.length === 0 && face.icon === true, orig: badgeShapeFor(u).cuts.length,
           vecIcon: vec.querySelectorAll('.badge-chapter-icon').length, vecPaths: vec.querySelectorAll('.badge-chapter-icon path').length,
           raster: !!buildUnitBadgeSVG(u, true).querySelector('image.badge-raster'), greyHasIcon: !!buildUnitBadgeSVG(u, 'grey', { vector: true }).querySelector('.badge-chapter-icon') }; }"""
SPEC = r"""() => {
  const out = [], sets = [], NS = 'http://www.w3.org/2000/svg';
  const holder = document.createElementNS(NS, 'svg'); holder.setAttribute('viewBox', '0 0 96 96'); holder.style.cssText = 'position:absolute;left:-999px;width:96px;height:96px'; document.body.appendChild(holder);
  for(const u of unitsInTeachingOrder()){
    if(!chapterIconFor(u)) continue;
    const pal = chapterIconPalette(u), allowed = new Set(['field', 'lite', 'body', 'shade', 'ink'].map(k => pal[k]));
    const mk = chapterIconMarkup(u), ops = chapterIconOps(mk), problems = [];
    const tagCount = (mk.match(/<[a-zA-Z]+/g) || []).length, pathCount = (mk.match(/<path\b/g) || []).length;
    if(!ops.length) problems.push('no paths');
    if(pathCount > CHAPTER_ICON_MAX_PATHS) problems.push('more than ' + CHAPTER_ICON_MAX_PATHS + ' paths (' + pathCount + ')');
    if(tagCount !== pathCount) problems.push('an element that is not a <path>');
    if(/\bid=|filter|Gradient|url\(|transform=|<defs|<style|<image|<text|<use/i.test(mk)) problems.push('an id, filter, gradient, url(), transform, defs, style, image, text or use');
    const attrs = new Set(); (mk.match(/\s([a-z-]+)="/g) || []).forEach(a => attrs.add(a.replace(/[\s="]/g, '')));
    attrs.forEach(a => { if(CHAPTER_ICON_ATTRS.indexOf(a) < 0) problems.push('attribute ' + a); });
    ops.forEach((o, i) => { ['fill', 'stroke'].forEach(k => { if(o[k] && o[k] !== 'none' && !allowed.has(o[k])) problems.push('path ' + i + ' ' + k + ' ' + o[k] + ' is not a palette colour'); }); });
    /* inside the box: every path's own box, in an svg of the 96 box */
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    ops.forEach((o, i) => { const p = document.createElementNS(NS, 'path'); p.setAttribute('d', o.d); holder.appendChild(p); const b = p.getBBox(); holder.removeChild(p);
      const sw = (+o['stroke-width'] || 0) / 2; x0 = Math.min(x0, b.x - sw); y0 = Math.min(y0, b.y - sw); x1 = Math.max(x1, b.x + b.width + sw); y1 = Math.max(y1, b.y + b.height + sw); });
    if(ops.length && (x0 < 2 || y0 < 2 || x1 > 94 || y1 > 94)) problems.push('outside the box: ' + [x0, y0, x1, y1].map(v => +v.toFixed(1)).join(','));
    if(ops.length && (x1 - x0 < 40 || y1 - y0 < 40) ) problems.push('too small to read at 26px: ' + (x1 - x0).toFixed(0) + ' x ' + (y1 - y0).toFixed(0));
    /* a 48px silhouette of its filled plates and strokes */
    const cv = document.createElement('canvas'); cv.width = cv.height = 48; const g = cv.getContext('2d'); g.scale(.5, .5);
    ops.forEach(o => { const p = new Path2D(o.d); if(o.fill && o.fill !== 'none'){ g.fillStyle = '#000'; g.fill(p, o['fill-rule'] === 'evenodd' ? 'evenodd' : 'nonzero'); } if(o.stroke && o.stroke !== 'none'){ g.strokeStyle = '#000'; g.lineWidth = +o['stroke-width'] || 1; g.lineJoin = 'round'; g.lineCap = 'round'; g.stroke(p); } });
    const d = g.getImageData(0, 0, 48, 48).data, m = new Uint8Array(48 * 48); let area = 0; for(let i = 0; i < 48 * 48; i++){ m[i] = d[i * 4 + 3] > 127 ? 1 : 0; area += m[i]; }
    if(area < 48 * 48 * .12) problems.push('a figure under 12% of its box');
    sets.push([u, m]); out.push({ u, problems, paths: ops.length, box: [x0, y0, x1, y1].map(v => +v.toFixed(0)) });
  }
  holder.remove();
  let worst = [0, '', ''];
  for(let i = 0; i < sets.length; i++) for(let j = i + 1; j < sets.length; j++){ let a = 0, b = 0; const A = sets[i][1], B = sets[j][1]; for(let k = 0; k < A.length; k++){ if(A[k] && B[k]) a++; if(A[k] || B[k]) b++; } const v = b ? a / b : 0; if(v > worst[0]) worst = [+v.toFixed(3), sets[i][0], sets[j][0]]; }
  return { icons: out, worst }; }"""
ALLIDS = r"""async () => {
  const us = unitsInTeachingOrder(), box = document.createElement('div'); document.body.appendChild(box);
  us.forEach(u => box.appendChild(buildUnitBadgeSVG(u, true)));
  us.forEach(u => box.appendChild(buildUnitBadgeSVG(u, 'grey')));
  us.forEach(u => box.appendChild(buildUnitBadgeSVG(u, true, { vector: true })));
  const ids = [...box.querySelectorAll('[id]')].map(e => e.id), seen = {}, dup = [];
  ids.forEach(i => { if(seen[i]) dup.push(i); seen[i] = 1; });
  const refs = []; box.querySelectorAll('*').forEach(e => [...e.attributes].forEach(a => { const m = /url\(#([^)]+)\)/.exec(a.value); if(m) refs.push(m[1]); }));
  const dangling = refs.filter(r => !seen[r]);
  return { svgs: box.querySelectorAll('svg').length, ids: ids.length, dup: dup.slice(0, 5), dangling: dangling.slice(0, 5), iconIds: box.querySelectorAll('.badge-chapter-icon [id], .badge-chapter-icon[id]').length }; }"""
def load(br, body=None, cls="ifc"):
    return R.open_page(br, port, R.SEED, 440, 956, 2, cls, body)
srv, port = R.serve()
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
    ctx, pg, errs = load(br)
    pr = pg.evaluate(PROBE)
    chk("the page is the Fire Code class and has the chapter-icon registry and resolver (CHAPTER_ICON, chapterIconFor)", pr["cls"] == "ifc" and pr["hasApi"], [pr["cls"], pr["hasApi"]])
    chk("(1) the app's chapter list is the 58 units of tools/chapter-icons/units.json, in teaching order", pr["units"] == UNITS, [len(pr["units"]), [u for u in pr["units"] if u not in UNITS][:3]])
    chk("(1) all %d chapters draw earned, empty, grey, vector and struck without throwing (%s)" % (len(pr["units"]), pr["bad"][:3]), len(pr["units"]) == 58 and not pr["bad"], pr["bad"][:5])
    icon_units = pr["icon"]
    chk("(2) at least six chapters have an icon (%d: the six samples)" % len(icon_units), len(icon_units) >= 6, icon_units)
    fb = [u for u in UNITS if u not in icon_units]
    chk("(1) a chapter with no icon (%d of them) resolves to nothing and draws the fallback; a chapter added later would too" % len(fb), len(fb) == 58 - len(icon_units) and pg.evaluate("()=>typeof chapterIconFor === 'function' ? chapterIconFor('Chapter 99: Not Yet') : 'no resolver'") is None and pg.evaluate("()=>{ const s = buildUnitBadgeSVG('Chapter 99: Not Yet', true, { vector: true }); return !!s.getAttribute('viewBox') && !s.querySelector('.badge-chapter-icon'); }"), fb[:3])
    # (2)
    for u in icon_units:
        r = pg.evaluate(USES, u)
        chk("(2) %s: its struck token draws the icon on the plate (mid change %.0f, rim change %.1f), no channels (%d on the outline), vector group %d (%d paths), a raster token, none on a grey (diff %s)"
            % (u[:30], r["mid"], r["rim"], r["orig"], r["vecIcon"], r["vecPaths"], r["greyDiff"]),
            r["mid"] > 25 and r["rim"] < 3 and r["noCuts"] and r["vecIcon"] == 1 and r["vecPaths"] >= 1 and r["raster"] and not r["greyHasIcon"] and r["greyDiff"] == 0, r)
    # (3)
    sp = pg.evaluate(SPEC) if pr["hasApi"] else {"icons": [], "worst": [0, "", ""]}
    badi = [(i["u"][:24], i["problems"]) for i in sp["icons"] if i["problems"]]
    chk("(3) every icon that exists (%d) meets the spec: %s" % (len(sp["icons"]), badi[:3] or "no problems"), len(sp["icons"]) >= 6 and not badi, badi[:4])
    chk("(3) no two icons alike: the most alike pair's 48px silhouettes overlap %s (%s / %s)" % (sp["worst"][0], sp["worst"][1][:22], sp["worst"][2][:22]), sp["worst"][0] < .85, sp["worst"])
    # (5)
    ai = pg.evaluate(ALLIDS)
    chk("(5) all 58 chapters x 3 drawings on one page (%d svgs, %d ids): no id twice, every url(#) resolves, no icon group has an id" % (ai["svgs"], ai["ids"]),
        ai["svgs"] == 58 * 3 and not ai["dup"] and not ai["dangling"] and ai["iconIds"] == 0, ai)
    here_ifc = pg.evaluate(SNAP, icon_units)
    errs_all += errs; ctx.close()
    ctx, pg, errs = load(br, cls="academy")
    here_ac = pg.evaluate(SNAP, [])
    errs_all += errs; ctx.close()
    # (4) the reference build
    base = base_body()
    ctx, pg, errs = load(br, base)
    there_ifc = pg.evaluate(SNAP, icon_units)
    errs_all += errs; ctx.close()
    ctx, pg, errs = load(br, base, "academy")
    there_ac = pg.evaluate(SNAP, [])
    errs_all += errs; ctx.close()
    br.close()
dif = [u for u in there_ac if here_ac.get(u) != there_ac[u]]
chk("(4) the academy's %d units draw exactly what origin/main draws (vector earned, empty, grey; struck earned, grey; ids normalised): %s" % (len(there_ac), dif[:3] or "all identical"), len(there_ac) >= 16 and not dif, dif[:5])
dif = [u for u in there_ifc if here_ifc.get(u) != there_ifc[u]]
chk("(4) Fire Code's %d chapters with no icon draw exactly what origin/main draws: %s" % (len(there_ifc), dif[:3] or "all identical"), len(there_ifc) == len(fb) and len(fb) > 0 and not dif, dif[:5])
mg = subprocess.run([sys.executable, os.path.join(HERE, "merge-chapter-icons.py"), "--check"], capture_output=True, text=True)
chk("(6) tools/chapter-icons/part-*.js and index.html are in step (%s)" % mg.stdout.strip(), mg.returncode == 0 or bool(against), mg.stdout + mg.stderr)
chk("(6) tools/chapter-badges-brief.md is there and carries the spec and the 58-chapter table", os.path.exists(os.path.join(HERE, "chapter-badges-brief.md")) and all(u in open(os.path.join(HERE, "chapter-badges-brief.md"), encoding="utf-8").read() for u in UNITS), "")
chk("(7) no page errors", not errs_all, errs_all[:3])
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
