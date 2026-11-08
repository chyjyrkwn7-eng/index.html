#!/usr/bin/env python3
"""Build 384, round 7 (r7-eyes): the crowned rulers' eyes made MEAN, and Inferno brought into the same family.

  "Not a fan of gold and platinum eyes they look girly and not mean. Inferno needs to match probably.."

  r6 gave Forge, Lunar, Solar and Tempest an almond with a round full iris, a fine outline and a small decoration each (rays, a
  crescent catch-light, a spark, a liner-like flick); Inferno kept big white angular slits, another family. Now Forge, Lunar, Solar,
  Tempest and Inferno share one hard eye (glareEye in drawAvatarCharSVG), each with its own colours, pupil and glow. Read off the
  drawn SVG of each character in BOTH classes (the academy and Fire Code share them). Shapes, not labels: the eye's parts are found
  by what they are (the light shape the iris sits in, a coloured disc, the dark filled lid over it), never by class name.

  A. ONE FAMILY: each of the five has, in each eye, a light eye shape, an iris disc inside it with a pupil on it, and a dark filled
     upper lid drawn over its top edge; nothing - no ray, spark or flick - reaches out past the eye, and no catch-light.
  B. MEAN, measured: (1) the eye shape is narrow - height over width at most .40 and below 6057892's for that character; (2) it
     slants down towards the nose - its inner corner sits below its outer corner by at least 8% of its width and its highest point
     is on the outer half; (3) the lid is heavy and hard - at least .2 thick at the nose end and half again as thick there as at
     the temple end; (4) the lid cuts the iris - the iris's top is above the eye shape's upper edge (a glare, not a stare);
     (5) the brows angle down towards the nose (slope at least .25, steeper than 6057892's) in the brows' own stroke (colour, width,
     caps as before); (6) Inferno, who has no brow, is the meanest: the steepest slant and the heaviest lid of the five.
  C. EACH HIS OWN: iris colour family, pupil (slit / dot / bolt, dark or hot) and glow (halo / under-lid / none) differ between every
     two of the five and Frost, and each of the five has a pupil; the five iris colours are five colours, none of them Frost's blue.
  D. SAME PLACE, ROUGHLY THE SAME FOOTPRINT: each eye shape's centre within .4 of where 6057892 had it, its width within 25%; every eye
     shape inside the face and below the brow.
  E. NOTHING ELSE MOVED: Oracle and Frost byte for byte 6057892's; every other character byte for byte; the five are 6057892's once
     their eye group and brow are taken out; and the five's eyes did change.
  F. READS AT 26px: on a 26px rankings coin at 3x, each of the five's eyes carries at least 80% of the ink Frost's do (the eye Madison
     likes, unchanged) - ink being every pixel's change when the eye group is hidden, summed.
  G. no page error in either class.

  python3 tools/check-b384-r7-eyes.py [--against OLD/index.html]    (A, B, C and "the five changed" FAIL on 6057892; D, E and F are
                                                                       pinned to it and FAIL on a tampered build)
  python3 tools/check-b384-r7-eyes.py --dump --against 6057892.html  (writes check-b384-r7-eyes.prev.json)
"""
import json, os, sys, colorsys, io, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)

FIVE = ["forge", "lunar", "solar", "tempest", "inferno"]
BROWED = ["forge", "lunar", "solar", "tempest"]
EYES = FIVE + ["frost", "oracle"]
BROW_RE = r"^M1[45](\.\d+)? 1[56](\.\d+)? L1[78](\.\d+)? 1[67](\.\d+)? M2[45]"

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4r7eyes01", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT_IFC = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
INIT_ACA = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S

SNAP = r"""([EYES, FIVE, BROW]) => {
  document.getElementById('splashscreen')?.remove();
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;opacity:0;pointer-events:none';
  document.body.appendChild(host);
  const re = new RegExp(BROW);
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const ser = s => new XMLSerializer().serializeToString(s).split(s.getAttribute('data-cx-uid') || '@@none@@').join('U');
  const mount = id => { const s = drawAvatarCharSVG(id); if(!s) return null; s.setAttribute('width', 340); s.setAttribute('height', 340); host.appendChild(s); return s; };
  const browOf = s => [...s.querySelectorAll('.cx-head path')].find(p => !p.closest('.cx-eyes') && p.getAttribute('stroke') && re.test(p.getAttribute('d') || ''));
  const out = { cls: window.NOVA_CLASS || 'academy', full: {}, noEyes: {}, eyes: {} };
  for(const c of AVATAR_CHARACTERS){
    let s; try{ s = mount(c.id); }catch(e){ out.full[c.id] = 'ERR ' + e.message; continue; }
    if(!s){ out.full[c.id] = out.noEyes[c.id] = 'no drawing (retired)'; continue; }
    out.full[c.id] = hash(ser(s));
    const e = s.querySelector('.cx-eyes');
    if(e){ /* the eye group's own clip paths live in <defs>; they go with it */
      [...e.querySelectorAll('[clip-path]')].forEach(n => { const m = /url\(#([^)]+)\)/.exec(n.getAttribute('clip-path')); const d = m && s.querySelector('defs [id="' + m[1] + '"]');
        if(d && ![...s.querySelectorAll('[clip-path]')].some(o => !e.contains(o) && o.getAttribute('clip-path') === n.getAttribute('clip-path'))) d.remove(); });
      e.remove(); }
    if(FIVE.includes(c.id)){ const b = browOf(s); if(b) b.remove(); }
    out.noEyes[c.id] = hash(ser(s));
    s.remove();
  }
  /* each eye shape, sampled: tag, geometry, box, fill, stroke, opacity, and its outline as points */
  const pts = el => {
    const t = el.tagName, a = n => +el.getAttribute(n), P = [];
    if(t === 'path'){ const L = el.getTotalLength(); for(let i = 0; i <= 240; i++){ const p = el.getPointAtLength(L * i / 240); P.push([p.x, p.y]); } }
    else if(t === 'ellipse' || t === 'circle'){ const rx = t === 'circle' ? a('r') : a('rx'), ry = t === 'circle' ? a('r') : a('ry');
      for(let i = 0; i < 240; i++){ const th = i / 240 * 2 * Math.PI; P.push([a('cx') + rx * Math.cos(th), a('cy') + ry * Math.sin(th)]); } }
    return P; };
  for(const id of EYES){
    const s = mount(id), g = s.querySelector('.cx-eyes');
    const bw = browOf(s);
    let brow = null;
    if(bw){ const d = bw.getAttribute('d').match(/-?\d+(\.\d+)?/g).map(Number); const b = bw.getBBox();
      brow = { d: d.slice(0, 4), bottom: b.y + b.height + (+bw.getAttribute('stroke-width') || 0) / 2,
        style: [bw.getAttribute('stroke'), bw.getAttribute('stroke-width'), bw.getAttribute('stroke-linecap'), bw.getAttribute('fill'), bw.getAttribute('opacity')] }; }
    const face = s.querySelector('.cx-head path[d^="M12.6 15.2"], .cx-head path[d^="M12.8 15.6"], .cx-head path[d^="M12.6 15.6"]');
    const fb = face ? face.getBBox() : null;
    out.eyes[id] = { brow, face: fb ? [fb.x, fb.y, fb.x + fb.width, fb.y + fb.height] : null,
      els: g ? [...g.querySelectorAll('path,circle,ellipse,rect')].map(el => { const b = el.getBBox(); const a = n => el.getAttribute(n);
        return { tag: el.tagName, cx: +a('cx') || null, cy: +a('cy') || null, r: +a('r') || null, rx: +a('rx') || null, ry: +a('ry') || null,
          box: [b.x, b.y, b.x + b.width, b.y + b.height], fill: a('fill') || '', stroke: a('stroke') || '', sw: +a('stroke-width') || 0,
          op: a('opacity') === null ? 1 : +a('opacity'), pts: pts(el) }; }) : [] };
    s.remove();
  }
  return out; }"""

COIN = r"""([id, hide]) => { document.getElementById('splashscreen')?.remove(); document.getElementById('__coin')?.remove();
  const w = document.createElement('div'); w.id = '__coin'; w.style.cssText = 'position:fixed;left:0;top:0;z-index:999999;width:30px;height:30px;background:#101216;display:grid;place-items:center';
  const c = document.createElement('div'); c.style.cssText = 'width:26px;height:26px;border-radius:50%;overflow:hidden;background:#1d2230';
  const s = drawAvatarCharSVG(id); s.setAttribute('width', 26); s.setAttribute('height', 26); c.appendChild(s); w.appendChild(c); document.body.appendChild(w);
  if(hide) s.querySelector('.cx-eyes').setAttribute('visibility', 'hidden'); }"""

def run(init, coins):
    srv, port = rc["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=rc["CHROME"])
        ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        if BODY is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.add_init_script(init)
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
        r = pg.evaluate(SNAP, [EYES, FIVE, BROW_RE])
        ctx.close()
        r["coin"] = {}
        if coins:
            ctx = br.new_context(viewport={"width": 200, "height": 200}, device_scale_factor=3)
            pg = ctx.new_page()
            if BODY is not None:
                pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
            pg.add_init_script(init)
            pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3000)
            for i in FIVE + ["frost"]:
                ims = []
                for hide in (False, True):
                    pg.evaluate(COIN, [i, hide]); pg.wait_for_timeout(40)
                    ims.append(Image.open(io.BytesIO(pg.locator("#__coin").screenshot())).convert("RGB"))
                d = list(ImageChops.difference(ims[0], ims[1]).getdata())
                r["coin"][i] = round(sum(max(p) for p in d) / 255, 1)   # the eyes' "ink": every pixel's change, in whole-pixel units
            ctx.close()
        br.close()
    srv.shutdown()
    r["errs"] = errs
    return r

ACA = run(INIT_ACA, True)
IFC = run(INIT_IFC, False)

def rgb(h):
    h = (h or "").strip()
    if not (h.startswith("#") and len(h) in (4, 7)): return None
    if len(h) == 4: h = "#" + "".join(c * 2 for c in h[1:])
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
def hls(h):
    c = rgb(h); return colorsys.rgb_to_hls(*c) if c else None
def light(h, t=.85):
    c = hls(h); return bool(c) and c[1] >= t
def dark(h):
    c = hls(h); return bool(c) and c[1] < .35
def family(h):
    c = hls(h)
    if not c: return "none"
    return "silver" if c[2] < .3 else "h%d" % int(c[0] * 360)
def filled(e): return e["fill"] not in ("", "none")

def anatomy(E):
    """The LEFT eye (outer corner towards -x, the nose towards +x), its parts found by what they are."""
    els = [e for e in E["els"] if (e["box"][0] + e["box"][2]) / 2 < 20]
    sc = [e for e in els if filled(e) and light(e["fill"]) and e["op"] >= .9]
    if not sc: return None
    a = max(sc, key=lambda e: (e["box"][2] - e["box"][0]) * (e["box"][3] - e["box"][1]))
    ai = els.index(a); x0, y0, x1, y1 = a["box"]; W, H = x1 - x0, y1 - y0; mx = (x0 + x1) / 2
    P = a["pts"]
    inner = max(P, key=lambda p: p[0]); outer = min(P, key=lambda p: p[0]); top = min(P, key=lambda p: p[1])
    iris = [e for e in els[ai + 1:] if e["tag"] == "circle" and .28 <= (e["r"] or 0) <= .62 and filled(e) and not light(e["fill"], .88) and x0 < e["cx"] < x1 and y0 - .3 < e["cy"] < y1 + .3]
    iris = iris[0] if iris else None
    pupil = None
    if iris:
        ii = els.index(iris)
        for e in els[ii + 1:]:
            bx = e["box"]; cx_, cy_ = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
            if filled(e) and abs(cx_ - iris["cx"]) < iris["r"] * .4 and abs(cy_ - iris["cy"]) < iris["r"] * .4 and (bx[2] - bx[0]) < iris["r"] * 1.2 and e["fill"] != iris["fill"]:
                pw_, ph_ = bx[2] - bx[0], bx[3] - bx[1]
                if (bx[2] - bx[0]) > iris["r"] * .9 and (bx[3] - bx[1]) > iris["r"] * .9: continue   # a hot core, not a pupil
                kind = "bolt" if e["tag"] == "path" else "slit" if ph_ >= 2.5 * pw_ else "dot"
                pupil = {"kind": kind, "tone": "dark" if dark(e["fill"]) else "hot", "el": e}
                break
    lids = [e for e in els[ai + 1:] if filled(e) and dark(e["fill"]) and e["box"][3] <= y1 - .1 and e["box"][2] > x0 and e["box"][0] < x1 and e["box"][1] < y0 + .05 and e is not (pupil or {}).get("el")]
    lid = max(lids, key=lambda e: e["box"][2] - e["box"][0]) if lids else None
    def thick(e, nose):
        lx0, lx1 = e["box"][0], e["box"][2]; s = (lx1 - lx0) * .2
        ys = [p[1] for p in e["pts"] if (p[0] >= lx1 - s if nose else p[0] <= lx0 + s)]
        return max(ys) - min(ys) if ys else 0
    halo = any(e is not a and els.index(e) < ai and filled(e) and e["op"] < 1 and e["box"][0] < x0 and e["box"][2] > x1 and e["box"][1] < y0 and e["box"][3] > y1 for e in els)
    under = any(e is not a and not filled(e) and e["stroke"] and e["op"] < 1 and (e["box"][1] + e["box"][3]) / 2 > (y0 + y1) / 2 for e in els)
    # the upper edge of the eye shape at the iris's centre line
    up_at = None
    if iris:
        col = [p[1] for p in P if abs(p[0] - iris["cx"]) < .06]
        up_at = min(col) if col else None
    # anything reaching out past the eye, or a light speck on the eye after the iris
    reach = [e["tag"] + " " + str([round(v, 2) for v in e["box"]]) for e in els
             if e["box"][0] - e["sw"] / 2 < x0 - .65 or e["box"][2] + e["sw"] / 2 > x1 + .65 or e["box"][1] - e["sw"] / 2 < y0 - .9 or e["box"][3] + e["sw"] / 2 > y1 + .9]
    speck = []
    if iris:
        for e in els[els.index(iris) + 1:]:
            col = e["fill"] if filled(e) else e["stroke"]
            if light(col, .88): speck.append(e["tag"] + " " + col)
    return {"W": W, "H": H, "ratio": H / W if W else 9, "centre": [mx, (y0 + y1) / 2], "box": [x0, y0, x1, y1],
            "drop": (inner[1] - outer[1]) / W if W else 0, "topOuter": top[0] < mx, "iris": iris["fill"] if iris else None, "irisEl": iris,
            "pupil": pupil, "lid": lid, "lidNose": thick(lid, True) if lid else 0, "lidTemple": thick(lid, False) if lid else 0,
            "cut": (iris is not None and up_at is not None and iris["cy"] - iris["r"] < up_at - .02), "halo": halo, "under": under,
            "reach": reach, "speck": speck}

PREVF = os.path.join(HERE, "check-b384-r7-eyes.prev.json")
def slope(b):
    if not b: return None
    x0, y0, x1, y1 = b["d"]; return (y1 - y0) / abs(x1 - x0) if x1 != x0 else 0
if "--dump" in sys.argv:
    dump = {}
    for k, R in (("academy", ACA), ("ifc", IFC)):
        AN = {i: anatomy(R["eyes"][i]) for i in FIVE}
        dump[k] = {"full": R["full"], "noEyes": R["noEyes"],
                   "eye": {i: {"ratio": AN[i]["ratio"], "centre": AN[i]["centre"], "W": AN[i]["W"]} for i in FIVE if AN[i]},
                   "brow": {i: {"slope": slope(R["eyes"][i]["brow"]), "style": R["eyes"][i]["brow"]["style"]} for i in BROWED if R["eyes"][i]["brow"]}}
    json.dump(dump, open(PREVF, "w"), indent=0, sort_keys=True)
    print("dumped", PREVF); sys.exit(0)
if not os.path.exists(PREVF):
    chk("the 6057892 pin file exists (%s)" % PREVF, False); print("\nFAILURES"); sys.exit(1)
PREV = json.load(open(PREVF))

for key, R in (("academy", ACA), ("ifc", IFC)):
    P = PREV[key]
    chk("G. [%s] the page is that class with no page error (%s)" % (key, R["errs"][:2]), R["cls"] == key and not R["errs"], R["errs"])
    AN = {i: anatomy(R["eyes"][i]) for i in EYES}
    # A
    miss = {i: [n for n, v in (("eye shape", AN[i]), ("iris", AN[i] and AN[i]["iris"]), ("pupil", AN[i] and AN[i]["pupil"]), ("lid", AN[i] and AN[i]["lid"])) if not v] for i in FIVE}
    miss = {i: v for i, v in miss.items() if v}
    chk("A. [%s] Forge, Lunar, Solar, Tempest and Inferno wear one eye: an eye shape, an iris in it with a pupil, a dark lid over its top (missing: %s)" % (key, miss or "none"), not miss, miss)
    deco = {i: (AN[i]["reach"], AN[i]["speck"]) for i in FIVE if AN[i] and (AN[i]["reach"] or AN[i]["speck"])}
    chk("A. [%s] ...with nothing reaching out past the eye (no rays, spark or flick) and no catch-light (%s)" % (key, deco or "none"), not deco, deco)
    if any(AN[i] is None for i in FIVE): continue   # no eye shape at all: nothing below can be measured (A has failed)
    # B
    wide = {i: (round(AN[i]["ratio"], 3), round(P["eye"][i]["ratio"], 3)) for i in FIVE if not (AN[i]["ratio"] <= .40 and AN[i]["ratio"] < P["eye"][i]["ratio"] - .03)}
    chk("B1. [%s] each eye is narrow: height/width at most .40 and below 6057892's (%s; too round: %s)" % (key, {i: round(AN[i]["ratio"], 3) for i in FIVE}, wide or "none"), not wide, wide)
    flat = {i: (round(AN[i]["drop"], 3), AN[i]["topOuter"]) for i in FIVE if not (AN[i]["drop"] >= .08 and AN[i]["topOuter"])}
    chk("B2. [%s] each eye slants down towards the nose: inner corner below the outer by >= 8%% of its width, highest point on the outer half (%s; flat: %s)" % (key, {i: round(AN[i]["drop"], 3) for i in FIVE}, flat or "none"), not flat, flat)
    soft = {i: (round(AN[i]["lidNose"], 3), round(AN[i]["lidTemple"], 3)) for i in FIVE if not (AN[i]["lidNose"] >= .2 and AN[i]["lidNose"] >= 1.5 * AN[i]["lidTemple"])}
    chk("B3. [%s] each lid is heavy and hard: >= .2 thick at the nose and half again the temple end (%s; soft: %s)" % (key, {i: (round(AN[i]["lidNose"], 2), round(AN[i]["lidTemple"], 2)) for i in FIVE}, soft or "none"), not soft, soft)
    stare = [i for i in FIVE if not AN[i]["cut"]]
    chk("B4. [%s] each lid cuts the top of the iris - a glare, not a stare (uncut: %s)" % (key, stare or "none"), not stare, stare)
    br = {}
    for i in BROWED:
        b = R["eyes"][i]["brow"]; s_ = slope(b); ps = P["brow"][i]["slope"]
        if not b or s_ is None or s_ < .25 or s_ <= ps + .05 or b["style"] != P["brow"][i]["style"]: br[i] = (s_, ps, b and b["style"], P["brow"][i]["style"])
    chk("B5. [%s] the brows angle down towards the nose (slope >= .25, steeper than 6057892's) in their own stroke (%s; not: %s)" % (key, {i: round(slope(R["eyes"][i]["brow"]) or 0, 3) for i in BROWED}, br or "none"), not br, br)
    most = max(FIVE, key=lambda i: AN[i]["drop"]); heavy = max(FIVE, key=lambda i: AN[i]["lidNose"])
    chk("B6. [%s] Inferno, with no brow, is the meanest: the steepest slant and the heaviest lid of the five (steepest: %s, heaviest: %s)" % (key, most, heavy if AN[heavy]["lidNose"] else "no lid"),
        most == "inferno" and heavy == "inferno" and AN["inferno"]["lidNose"] > max(AN[i]["lidNose"] for i in BROWED), {i: (round(AN[i]["drop"], 3), round(AN[i]["lidNose"], 3)) for i in FIVE})
    # C
    six = FIVE + ["frost"]
    def struct(i):
        A_ = AN[i]; pu = A_["pupil"] or {}
        return json.dumps([family(A_["iris"]), pu.get("kind"), pu.get("tone"), "halo" if A_["halo"] else "under" if A_["under"] else "none"])
    ST = {i: struct(i) for i in six if AN[i]}
    dup = [(a, b) for n, a in enumerate(six) for b in six[n + 1:] if a in ST and b in ST and ST[a] == ST[b]]
    nopu = [i for i in FIVE if not AN[i]["pupil"]]
    chk("C. [%s] the eye differs between every two of the five and Frost in iris colour, pupil and glow, and each of the five has a pupil (same: %s; no pupil: %s)" % (key, dup or "none", nopu or "none"),
        not dup and not nopu and len(ST) == 6, ST)
    hues = {i: hls(AN[i]["iris"]) if AN[i] else None for i in six}
    def apart(a, b):
        ha, hb = hues[a], hues[b]
        if not ha or not hb: return False
        if (ha[2] < .3) != (hb[2] < .3): return True
        d = abs(ha[0] - hb[0]) * 360; d = min(d, 360 - d); return d >= 12
    close = [(a, b) for n, a in enumerate(six) for b in six[n + 1:] if not apart(a, b)]
    chk("C. [%s] ...five iris colours, none of them Frost's blue (%s; too close: %s)" % (key, {i: AN[i]["iris"] for i in six}, close or "none"), not close, hues)
    # D
    moved = {i: (AN[i]["centre"], P["eye"][i]["centre"], AN[i]["W"], P["eye"][i]["W"]) for i in FIVE
             if abs(AN[i]["centre"][0] - P["eye"][i]["centre"][0]) > .4 or abs(AN[i]["centre"][1] - P["eye"][i]["centre"][1]) > .4 or abs(AN[i]["W"] / P["eye"][i]["W"] - 1) > .25}
    chk("D. [%s] each eye stays where 6057892 had it (centre within .4) at roughly its size (width within 25%%) (moved: %s)" % (key, moved or "none"), not moved, moved)
    out = {}
    for i in FIVE:
        E = R["eyes"][i]; fx = E["face"]; bb = E["brow"]["bottom"] if E["brow"] else None
        for e in E["els"]:
            x0, y0, x1, y1 = e["box"]; pad = e["sw"] / 2
            if not fx or x0 - pad < fx[0] or x1 + pad > fx[2] or (bb is not None and y0 - pad < bb):
                out.setdefault(i, []).append([round(v, 2) for v in e["box"]])
    chk("D. [%s] every eye shape stays inside the face and below the brow (out: %s)" % (key, out or "none"), not out, {i: (R["eyes"][i]["face"], R["eyes"][i]["brow"]) for i in FIVE})
    # E
    bad = [i for i in ("oracle", "frost") if R["full"].get(i) != P["full"].get(i)]
    chk("E. [%s] Oracle and Frost are byte for byte what 6057892 drew (changed: %s)" % (key, bad or "none"), not bad, bad)
    others = sorted(set(P["full"]) | set(R["full"]))
    mv = [i for i in others if i not in FIVE and R["full"].get(i) != P["full"].get(i)]
    chk("E. [%s] every other character (%d of them) is byte for byte 6057892's (changed: %s)" % (key, len(others) - len(FIVE), mv or "none"), not mv and len(others) >= 25, mv)
    rest = [i for i in FIVE if R["noEyes"].get(i) != P["noEyes"].get(i)]
    chk("E. [%s] ...and the five are 6057892's outside their eye group and brow - crown, hair, robe, backdrop, neck, mouth (changed: %s)" % (key, rest or "none"), not rest, rest)
    same = [i for i in FIVE if R["full"].get(i) == P["full"].get(i)]
    chk("E. [%s] ...while the five's eyes did change (unchanged: %s)" % (key, same or "none"), not same, same)

# F (the academy page; the drawings are the same in both classes, E says so)
C = ACA["coin"]; fr = C.get("frost", 0)
faint = {i: C[i] for i in FIVE if C[i] < .8 * fr}
chk("F. on a 26px coin at 3x each of the five's eyes carries at least 80%% of the ink Frost's do (pixel change with the eyes hidden, %s; faint: %s)" % (C, faint or "none"), not faint and fr > 3, C)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
