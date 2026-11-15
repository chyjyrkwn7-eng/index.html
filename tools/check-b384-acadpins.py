#!/usr/bin/env python3
"""Build 384.121: the police academy's unit badges are raised pins of what each unit is about (tools/chapter-objects/part-6-academy.js).
Madison: "Speaking of badges, yes, we are going to update the police academy badges as well. Same concept, match what they are talking
about." Only the art changes: every badge id (the unit's title) and every unlock rule stay exactly as they were. Played in Chromium on the
academy class and read off the page:
 (1) EVERY ONE IS A PIN: all 24 academy units are authored in CHAPTER_OBJ (tools/chapter-objects/academy-units.json is the app's own unit
     list) and draw as a raised pin (svg.is-pin) earned, as the empty slot (cut to its own outline) and as the grey token; no SVG filter in
     any drawing; no unit draws a struck outline any more;
 (2) NOTHING ELSE MOVED: the units, their order, every badge's threshold (badgeThresholdFor) and which badges a fixture account has earned
     (unitBadgeEarned) are exactly what the BASE build (default origin/main) says; UNIT_BADGE_SHAPE keeps every key (other code reads it);
 (3) ONE OBJECT A UNIT, DISTINCT: no two of the 24 silhouettes overlap 0.85 or more as 48px shapes (the Fire Code rule,
     check-b384-objbadges (4); with a near colour as well, 0.80 is already a twin there, (6), which --class academy runs);
 (4) READABLE SMALL: at the case's 44 CSS px (2x) every earned pin covers at least 20% of its square (a speck does not; a long thing - a car, a radio, a dove - covers 23-29%) and its grey token shows relief
     (luminance spread inside the pin at least 12 levels: a flat blob has none);
 (5) THE BADGE CASE: Profile > Badges with every academy badge found shows 24 pins, at 440x956 and 834x1194;
 (6) the Fire Code-style checks for the academy: tools/check-b384-objbadges.py --class academy (spec, thin parts, wall, bevel, relief,
     finish, perf, joins, back and its words, no twins, ids) is ALL PASS (skipped with --against);
 (7) no page errors.
Run:  python3 tools/check-b384-acadpins.py            (--against OLD/index.html must FAIL; --base FILE is the build compared in (2))"""
import json, os, sys, subprocess, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
against = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
saved = sys.argv[:]; sys.argv = [saved[0]] + (["--index", against] if against else [])
spec = importlib.util.spec_from_file_location("rcb", os.path.join(HERE, "render-chapter-badges.py"))
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
sys.argv = saved
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
ACAD = json.load(open(os.path.join(HERE, "chapter-objects", "academy-units.json"), encoding="utf-8"))
def base_body():
    if "--base" in sys.argv: return open(sys.argv[sys.argv.index("--base") + 1], encoding="utf-8").read()
    return subprocess.run(["git", "-C", ROOT, "show", "origin/main:index.html"], capture_output=True, check=True).stdout.decode("utf-8")
RULES = r"""() => {
  const us = unitsInTeachingOrder(), saved = JSON.stringify(store.unitPerfects || {});
  /* a fixture account: every other unit with enough perfect runs, the rest with one short */
  us.forEach((u, i) => { store.unitPerfects[u] = i % 2 ? badgeThresholdFor(u) : Math.max(0, badgeThresholdFor(u) - 1); });
  const r = { units: us, thr: us.map(u => badgeThresholdFor(u)), earned: us.map(u => !!unitBadgeEarned(u)),
              shapeKeys: Object.keys(typeof UNIT_BADGE_SHAPE === 'object' ? UNIT_BADGE_SHAPE : {}) };
  store.unitPerfects = JSON.parse(saved); return r; }"""
PINS = r"""() => {
  const out = [];
  for(const u of unitsInTeachingOrder()){
    const r = { u, obj: typeof chapterObjShape === 'function' && !!chapterObjShape(u) };
    try{
      const a = buildUnitBadgeSVG(u, true, { px: 44, dirt: 0 }), b = buildUnitBadgeSVG(u, false, { px: 44 }), c = buildUnitBadgeSVG(u, 'grey', { px: 44 });
      r.pin = [a, b, c].every(s => s.classList.contains('is-pin'));
      r.filter = [a, b, c].some(s => s.querySelector('filter,[filter]'));
      r.slotOwn = r.obj && badgeShapeFor(u).d === chapterObjShape(u).d;
    }catch(e){ r.err = String(e).slice(0, 120); }
    out.push(r);
  }
  return out; }"""
MASKS = r"""() => {
  const N = 48, mask = (u) => { const sh = badgeShapeFor(u), b = badgeBBoxFor(sh.d) || { x: 0, y: 0, w: 100, h: 100 }; const cv = document.createElement('canvas'); cv.width = cv.height = N;
    const x = cv.getContext('2d', { willReadFrequently: true }); const s = (N - 4) / Math.max(b.w, b.h);
    x.translate(N / 2 - s * (b.x + b.w / 2), N / 2 - s * (b.y + b.h / 2)); x.scale(s, s); x.fill(new Path2D(sh.d));
    const d = x.getImageData(0, 0, N, N).data; let bits = ''; for(let i = 3; i < d.length; i += 4) bits += d[i] > 127 ? '1' : '0'; return bits; };
  const o = {}; unitsInTeachingOrder().forEach(u => { o[u] = mask(u); }); return o; }"""
SMALL = r"""async () => {
  /* the case's 44 CSS px at the page's ratio: the earned pin's coverage of its square, the grey token's luminance spread */
  const out = [];
  for(const u of unitsInTeachingOrder()){
    const W = Math.round(44 * devicePixelRatio);
    const read = grey => { const c = renderBadgeStrike(u, grey, W, 1, 0); return c.getContext('2d').getImageData(0, 0, W, W).data; };
    const e = read(false), g = read(true);
    let cov = 0, s1 = 0, s2 = 0, n = 0;
    for(let i = 0; i < W * W; i++){ if(e[i * 4 + 3] > 200) cov++; if(g[i * 4 + 3] > 250){ const L = .2126 * g[i * 4] + .7152 * g[i * 4 + 1] + .0722 * g[i * 4 + 2]; s1 += L; s2 += L * L; n++; } }
    const m = n ? s1 / n : 0;
    out.push({ u, cov: cov / (W * W), sd: n ? Math.sqrt(Math.max(0, s2 / n - m * m)) : 0 });
  }
  return out; }"""
def iou(a, b):
    i = sum(1 for x, y in zip(a, b) if x == "1" and y == "1"); u = sum(1 for x, y in zip(a, b) if x == "1" or y == "1")
    return i / max(1, u)
srv, port = R.serve()
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
    ctx, pg, errs = R.open_page(br, port, R.SEED, 440, 956, 2, "academy")
    pg.set_default_timeout(180000)
    pins = pg.evaluate(PINS)
    rules = pg.evaluate(RULES)
    chk("(1) the page is the academy and its units are the %d of academy-units.json" % len(ACAD), sorted(rules["units"]) == sorted(ACAD), [u for u in rules["units"] if u not in ACAD][:3])
    nopin = [p["u"][:28] for p in pins if not (p.get("obj") and p.get("pin") and p.get("slotOwn"))]
    chk("(1) EVERY ONE IS A PIN: all %d units draw as a raised pin earned, as the empty slot (its own outline) and grey: %s" % (len(pins), nopin[:4] or "all"), len(pins) == 24 and not nopin, nopin[:8])
    flt = [p["u"][:28] for p in pins if p.get("filter") or p.get("err")]
    chk("(1) no SVG filter (and no error) in any drawing: %s" % (flt[:3] or "none"), not flt, [(p["u"][:20], p.get("err")) for p in pins if p.get("filter") or p.get("err")][:4])
    masks = pg.evaluate(MASKS)
    us = list(masks.keys()); worst = (0, "", "")
    for i in range(len(us)):
        for j in range(i + 1, len(us)):
            v = iou(masks[us[i]], masks[us[j]])
            if v > worst[0]: worst = (round(v, 3), us[i][:24], us[j][:24])
    chk("(3) ONE OBJECT A UNIT: no two of the 24 silhouettes overlap 0.85 or more as 48px shapes: the most alike pair %s" % (worst,), worst[0] < .85, worst)
    sm = pg.evaluate(SMALL)
    low = [(r["u"][:24], round(r["cov"], 2), round(r["sd"], 1)) for r in sm if r["cov"] < .20 or r["sd"] < 12]
    chk("(4) READABLE SMALL: at 44 CSS px every pin covers 20%%+ of its square and its grey token's relief spreads 12+ levels: least coverage %s, least relief %s" % (
        min([(round(r["cov"], 2), r["u"][:20]) for r in sm]), min([(round(r["sd"], 1), r["u"][:20]) for r in sm])), not low, low[:6])
    errs_all += errs; ctx.close()
    for (w, h, dsf) in ((440, 956, 3), (834, 1194, 2)):
        ctx, pg, errs = R.open_page(br, port, R.SEED, w, h, dsf, "academy")
        pg.set_default_timeout(180000)
        pg.evaluate("()=>{ unitsInTeachingOrder().forEach(u => { store.unitPerfects[u] = Math.max(store.unitPerfects[u] || 0, badgeThresholdFor(u)); }); showRanksScreen('badges'); }")
        pg.wait_for_timeout(3500)
        n = pg.evaluate("()=>({ pins: document.querySelectorAll('#stage svg.badge-art.is-pin.is-earned').length, struck: document.querySelectorAll('#stage svg.badge-art.is-earned:not(.is-pin)').length })")
        chk("(5) THE BADGE CASE at %dx%d with every academy badge found: %d pins, %d struck badges" % (w, h, n["pins"], n["struck"]), n["pins"] >= 24 and n["struck"] == 0, n)
        errs_all += errs; ctx.close()
    ctx, pg, errs = R.open_page(br, port, R.SEED, 440, 956, 2, "academy", base_body())
    base = pg.evaluate(RULES)
    ctx.close()
    br.close()
chk("(2) NOTHING ELSE MOVED: the units and their order are the base build's", rules["units"] == base["units"], [rules["units"][:3], base["units"][:3]])
chk("(2) every badge's threshold is the base build's (%s)" % rules["thr"], rules["thr"] == base["thr"], list(zip(rules["units"], rules["thr"], base["thr"]))[:5])
chk("(2) a fixture account has earned exactly the badges it had on the base build (%d of %d)" % (sum(rules["earned"]), len(rules["earned"])), rules["earned"] == base["earned"], [rules["earned"], base["earned"]])
chk("(2) UNIT_BADGE_SHAPE keeps every key the base build has", all(k in rules["shapeKeys"] for k in base["shapeKeys"]), [k for k in base["shapeKeys"] if k not in rules["shapeKeys"]][:4])
if not against:
    r = subprocess.run([sys.executable, os.path.join(HERE, "check-b384-objbadges.py"), "--class", "academy"], capture_output=True, text=True)
    fails = [l[:200] for l in r.stdout.splitlines() if l.startswith("FAIL")]
    chk("(6) tools/check-b384-objbadges.py --class academy: %s" % ("ALL PASS" if r.returncode == 0 else "%d fail(s)" % len(fails)), r.returncode == 0, fails[:5] or r.stderr[-400:])
chk("(7) no page errors", not errs_all, errs_all[:3])
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
