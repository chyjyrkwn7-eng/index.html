#!/usr/bin/env python3
"""Build 384, round 8 (r8-eyes): Forge, Lunar, Solar and Tempest each get an eye of their OWN.

  "Inferno eyes are cool. Oracle eyes are cool. Frost eyes are cool. The other 4 look the same though, why does inferno eyes look
   different by the way? I thought you'd fix that."

  r7 drew all of Forge, Lunar, Solar, Tempest and Inferno with one helper (glareEye); the four used it at nearly the same size, so
  they read as one eye in four colours, and Inferno read apart only because it was the same eye wider, steeper, heavier and glowing
  on a black face. Now Inferno keeps glareEye (byte for byte), and the four draw their own: Forge a square-cut furnace slit lit from
  below under a filled brow ridge, with soot under it; Lunar a level dark lens in a shadowed socket with a pale glowing iris; Solar
  a sharp white-gold sliver with a hot rim under wedge brows; Tempest a lightning-cut lid and one brow cocked. Read off the drawn SVG
  of each character in BOTH classes. Shapes, not labels: the eye opening is found by what it is (the first solid filled shape in the
  eye group - a glow, a socket or a soot shadow is a fill that fades, and is skipped), not by class.

  A. OWN CONSTRUCTION: the four's left eyes differ from each other and from Inferno's in how they are built (the element tags and path
     commands in drawing order, and the opening's own shape scaled to its box - r7's five were one recipe at five sizes, overlap
     ~.9 and more, so a different size is not a different eye: at most .85) AND in silhouette (the opening and the solid parts on it - lid, rim, not a fading glow - sampled on a
     grid over a fixed window centred on the opening: intersection over union at most .80 for every pair of the four, and of each
     of them with Inferno, Oracle and Frost; cd34de2's four were .91-.98 to each other).
  B. THE SQUINT TEST: each of the seven rulers as a 26px rankings coin, greyscale, 3x: the eye band (the brows down to under the
     eyes) normalised for brightness and contrast, compared pairwise - every pair of the seven differs by at least the margin
     (1 - correlation >= .30). The 26px eye "ink" of each of the four (pixel change with the eye group hidden) is at least 80% of
     Frost's, so they read at that size.
  C. STILL MEAN: every eye opening's height/width at most .40 and no rounder than cd34de2's for that character (both eyes); nothing
     stroked reaches past the opening (no lash, liner flick or ray), nothing small and filled sits outside it (no sparkle), no
     catch-light (a light speck off the iris centre); each brow's nose end is no higher than its temple end (never a worried brow).
  D. SAME PLACE, ROUGHLY THE SAME FOOTPRINT, ATTACHED: the opening's centre within .4 of cd34de2's, its width within 25%; every eye
     part inside the face and clear of the brow (sampled), and every part touching the opening's box (nothing floats).
  E. NOTHING ELSE MOVED: Inferno, Oracle and Frost byte for byte cd34de2's; every other character byte for byte; the four are cd34de2's
     with their eye group and brows taken out (crown, hair, robe, backdrop, neck, mouth, closed eyes); and the four did change.
  F. no page error in either class.

  python3 tools/check-b384-r8-eyes.py [--against OLD/index.html]    (A, B, C's "no rounder" and "the four changed" FAIL on cd34de2;
                                                                       D and E are pinned to it and FAIL on a tampered build)
  python3 tools/check-b384-r8-eyes.py --dump --against cd34de2.html  (writes check-b384-r8-eyes.prev.json)
"""
import json, os, sys, io, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageOps
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)

FOUR = ["forge", "lunar", "solar", "tempest"]
PINNED = ["inferno", "oracle", "frost"]
SEVEN = FOUR + PINNED
# cd34de2's brows on Forge, Lunar and Solar were bare strokes (Tempest's and Frost's sit in a cx-brow group)
BROW_RE = r"^M1[45](\.\d+)? 1[56](\.\d+)? L1[78](\.\d+)? 1[67](\.\d+)? M2[45]"

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4r8eyes01", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT_IFC = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
INIT_ACA = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S

SNAP = r"""([SEVEN, FOUR, BROW]) => {
  document.getElementById('splashscreen')?.remove();
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;opacity:0;pointer-events:none';
  document.body.appendChild(host);
  const re = new RegExp(BROW);
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const ser = s => new XMLSerializer().serializeToString(s).split(s.getAttribute('data-cx-uid') || '@@none@@').join('U');
  const mount = id => { const s = drawAvatarCharSVG(id); if(!s) return null; s.setAttribute('width', 340); s.setAttribute('height', 340); host.appendChild(s); return s; };
  const brows = s => [...s.querySelectorAll('.cx-brow path')].concat([...s.querySelectorAll('.cx-head path')].filter(p => !p.closest('.cx-eyes, .cx-brow') && p.getAttribute('stroke') && re.test(p.getAttribute('d') || '')));
  /* defs nothing references any more (after taking parts out) go too - both builds get the same rule */
  const prune = s => { const txt = () => new XMLSerializer().serializeToString(s);
    [...s.querySelectorAll('defs > [id]')].forEach(d => { const id = d.id; d.remove(); if(txt().includes('#' + id + ')') || txt().includes('"#' + id + '"')) s.querySelector('defs').appendChild(d); }); };
  const out = { cls: window.NOVA_CLASS || 'academy', full: {}, noEyes: {}, eyes: {} };
  for(const c of AVATAR_CHARACTERS){
    let s; try{ s = mount(c.id); }catch(e){ out.full[c.id] = 'ERR ' + e.message; continue; }
    if(!s){ out.full[c.id] = out.noEyes[c.id] = 'no drawing (retired)'; continue; }
    out.full[c.id] = hash(ser(s));
    if(FOUR.includes(c.id)){
      s.querySelector('.cx-eyes')?.remove(); brows(s).forEach(b => b.remove());
      s.querySelectorAll('.cx-brow').forEach(g => { if(!g.children.length) g.remove(); });
      prune(s);
      /* an emptied cx-brow wrapper and a bare brow leave the same tree; normalise the order of what is left in the head */
      out.noEyes[c.id] = hash(ser(s).replace(/<g class="cx-brow"\/>/g, ''));
    }
    s.remove();
  }
  const glowy = el => { if(+(el.getAttribute('opacity') ?? 1) < .9) return true;
    const m = /url\(#([^)]+)\)/.exec(el.getAttribute('fill') || ''); if(!m) return false;
    const g = el.ownerSVGElement.querySelector('[id="' + m[1] + '"]'); return !!g && [...g.querySelectorAll('stop')].some(st => +(st.getAttribute('stop-opacity') ?? 1) < .5); };
  const fillOf = el => { const f = el.getAttribute('fill'); return f === null ? '#000' : f; };
  for(const id of SEVEN){
    const s = mount(id), g = s.querySelector('.cx-eyes');
    const head = s.querySelector('.cx-head');
    const face = s.querySelector('.cx-head path[d^="M12.6 15.2"], .cx-head path[d^="M12.8 15.6"], .cx-head path[d^="M12.6 15.6"]');
    const bw = brows(s);
    const E = { brows: bw.map(b => { const d = (b.getAttribute('d') || '').split(/(?=M)/).map(seg => seg.match(/-?\d+(\.\d+)?/g).map(Number)); return d; }), eyes: [] };
    const all = g ? [...g.querySelectorAll('path,circle,ellipse,rect,polygon')] : [];
    for(const side of [-1, 1]){
      const els = all.filter(el => { const b = el.getBBox(); return ((b.x + b.width / 2) - 20) * side > 0; });
      const free = els.filter(el => !el.closest('[clip-path]'));
      const opening = free.find(el => fillOf(el) !== 'none' && !glowy(el));
      if(!opening){ E.eyes.push(null); continue; }
      const ob = opening.getBBox();
      const sig = els.map(el => el.tagName + (el.tagName === 'path' ? ':' + (el.getAttribute('d') || '').replace(/[^A-Za-z]/g, '') : '') + (el.closest('[clip-path]') ? '@clip' : '')).join(' ');
      /* the eye's outline: the opening and every solid part on it (a lid, a rim - not a glow, socket or soot, which fade out), on a
         grid over a fixed 3.6 x 2.2 window centred on the opening, so size and proportion count as well as shape */
      const solid = free.filter(el => !glowy(el));
      const ocx = ob.x + ob.width / 2, ocy = ob.y + ob.height / 2, GX = 72, GY = 44, grid = [];
      for(let j = 0; j < GY; j++) for(let i = 0; i < GX; i++){
        let u = (i + .5) / GX - .5, v = (j + .5) / GY - .5; if(side > 0) u = -u;   /* mirror the right eye onto the left */
        const pt = new DOMPoint(ocx + u * 3.6, ocy + v * 2.2);
        grid.push(solid.some(el => (fillOf(el) !== 'none' && el.isPointInFill(pt)) || (el.getAttribute('stroke') && el.getAttribute('stroke') !== 'none' && el.isPointInStroke(pt))) ? 1 : 0);
      }
      /* sampled points of every free part: inside the face? clear of the brows? */
      let outFace = 0, onBrow = 0, n = 0;
      const parts = free.map(el => { const b = el.getBBox(); const st = el.getAttribute('stroke') && el.getAttribute('stroke') !== 'none';
        const sw = st ? (+el.getAttribute('stroke-width') || 0) : 0;
        for(let px = b.x - sw / 2; px <= b.x + b.width + sw / 2; px += .04) for(let py = b.y - sw / 2; py <= b.y + b.height + sw / 2; py += .04){
          const pt = new DOMPoint(px, py);
          if(!((fillOf(el) !== 'none' && el.isPointInFill(pt)) || (st && el.isPointInStroke(pt)))) continue;
          n++; if(face && !face.isPointInFill(pt)) outFace++;
          if(bw.some(br => br.isPointInStroke(pt) || (fillOf(br) !== 'none' && br.isPointInFill(pt)))) onBrow++;
        }
        const a = n => el.getAttribute(n);
        return { tag: el.tagName, box: [b.x - sw / 2, b.y - sw / 2, b.x + b.width + sw / 2, b.y + b.height + sw / 2], stroked: !!st, filled: fillOf(el) !== 'none',
          glowy: glowy(el), before: free.indexOf(el) < free.indexOf(opening), fill: fillOf(el), stroke: a('stroke') || '', light: 0 }; });
      /* the iris (a clipped disc) and anything light after it */
      const clipped = els.filter(el => el.closest('[clip-path]'));
      const iris = clipped.find(el => el.tagName === 'circle' && +(el.getAttribute('opacity') ?? 1) >= .9);
      const after = iris ? clipped.slice(clipped.indexOf(iris) + 1).map(el => { const b = el.getBBox(); return { fill: fillOf(el), stroke: el.getAttribute('stroke') || '', cx: b.x + b.width / 2, cy: b.y + b.height / 2, w: b.width }; }) : [];
      /* the opening's own shape, whatever its size: a grid over its own box (mirrored for the right eye) */
      const shape = [];
      for(let j = 0; j < 16; j++) for(let i = 0; i < 40; i++){
        let u = (i + .5) / 40; if(side > 0) u = 1 - u;
        shape.push(opening.isPointInFill(new DOMPoint(ob.x + u * ob.width, ob.y + (j + .5) / 16 * ob.height)) ? 1 : 0);
      }
      E.eyes.push({ side, sig, grid, shape, box: [ob.x, ob.y, ob.x + ob.width, ob.y + ob.height], ratio: ob.height / ob.width, centre: [ob.x + ob.width / 2, ob.y + ob.height / 2], W: ob.width,
        parts, outFace, onBrow, samples: n, iris: iris ? { cx: +iris.getAttribute('cx'), cy: +iris.getAttribute('cy'), r: +iris.getAttribute('r') } : null, after });
    }
    out.eyes[id] = E;
    s.remove();
  }
  return out; }"""

COIN = r"""([id, hide]) => { document.getElementById('splashscreen')?.remove(); document.getElementById('__coin')?.remove();
  const w = document.createElement('div'); w.id = '__coin'; w.style.cssText = 'position:fixed;left:0;top:0;z-index:999999;width:30px;height:30px;background:#101216;display:grid;place-items:center';
  const c = document.createElement('div'); c.style.cssText = 'width:26px;height:26px;border-radius:50%;overflow:hidden;background:#1d2230';
  const s = drawAvatarCharSVG(id); s.setAttribute('width', 26); s.setAttribute('height', 26); c.appendChild(s); w.appendChild(c); document.body.appendChild(w);
  if(hide) s.querySelector('.cx-eyes').setAttribute('visibility', 'hidden');
  /* where the eyes really are in the frame (the drawing's own CSS may scale it): the band runs from the brows to under the eyes */
  const W = w.getBoundingClientRect(), r = s.getBoundingClientRect(), u = r.width / 34, cy = r.top + (17.8 - 3) * u - W.top;
  return [r.left - W.left + (14 - 3) * u, cy - 2.8 * u, r.left - W.left + (26 - 3) * u, cy + 1.8 * u]; }"""

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
        r = pg.evaluate(SNAP, [SEVEN, FOUR, BROW_RE])
        ctx.close()
        r["coin"] = {}; r["band"] = {}
        if coins:
            ctx = br.new_context(viewport={"width": 200, "height": 200}, device_scale_factor=3)
            pg = ctx.new_page()
            if BODY is not None:
                pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
            pg.add_init_script(init)
            pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3000)
            for i in SEVEN:
                ims = []
                for hide in (False, True):
                    bx = pg.evaluate(COIN, [i, hide]); pg.wait_for_timeout(40)
                    ims.append(Image.open(io.BytesIO(pg.locator("#__coin").screenshot())).convert("RGB"))
                d = list(ImageChops.difference(ims[0], ims[1]).getdata())
                r["coin"][i] = round(sum(max(p) for p in d) / 255, 1)
                # the eye band in greyscale: viewBox x 14..26, from the brows (y 15) to under the eyes (y 19.6), at the drawing's real place
                g = ImageOps.grayscale(ims[0])
                box = tuple(int(round(v * 3)) for v in bx)
                r["band"][i] = list(g.crop(box).getdata())
                if "--bands" in sys.argv: g.crop(box).resize(((box[2] - box[0]) * 4, (box[3] - box[1]) * 4), Image.NEAREST).save(sys.argv[sys.argv.index("--bands") + 1] + "/band-" + i + ".png")
            ctx.close()
        br.close()
    srv.shutdown()
    r["errs"] = errs
    return r

def corr(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a) ** .5; vb = sum((y - mb) ** 2 for y in b) ** .5
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (va * vb) if va and vb else 1
def iou(a, b):
    i = sum(1 for x, y in zip(a, b) if x and y); u = sum(1 for x, y in zip(a, b) if x or y); return i / u if u else 1
def lum(h):
    h = (h or "").strip()
    if not (h.startswith("#") and len(h) == 7): return None
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)); return (max(r, g, b) + min(r, g, b)) / 2

ACA = run(INIT_ACA, True)
IFC = run(INIT_IFC, False)

PREVF = os.path.join(HERE, "check-b384-r8-eyes.prev.json")
if "--dump" in sys.argv:
    dump = {}
    for k, R in (("academy", ACA), ("ifc", IFC)):
        dump[k] = {"full": R["full"], "noEyes": R["noEyes"],
                   "eye": {i: [{"ratio": e["ratio"], "centre": e["centre"], "W": e["W"]} if e else None for e in R["eyes"][i]["eyes"]] for i in FOUR}}
    json.dump(dump, open(PREVF, "w"), indent=0, sort_keys=True)
    print("dumped", PREVF); sys.exit(0)
if not os.path.exists(PREVF):
    chk("the cd34de2 pin file exists (%s)" % PREVF, False); print("\nFAILURES"); sys.exit(1)
PREV = json.load(open(PREVF))

for key, R in (("academy", ACA), ("ifc", IFC)):
    P = PREV[key]
    chk("F. [%s] the page is that class with no page error (%s)" % (key, R["errs"][:2]), R["cls"] == key and not R["errs"], R["errs"])
    EY = {i: R["eyes"][i]["eyes"] for i in SEVEN}
    miss = [i for i in SEVEN if not all(EY[i])]
    chk("F. [%s] every ruler's two eyes each have an opening (missing: %s)" % (key, miss or "none"), not miss, miss)
    if miss: continue
    L = {i: EY[i][0] for i in SEVEN}
    # A
    FIVE = FOUR + ["inferno"]
    same = [(a, b) for n, a in enumerate(FIVE) for b in FIVE[n + 1:] if L[a]["sig"] == L[b]["sig"]]
    SH = {a + "/" + b: round(iou(L[a]["shape"], L[b]["shape"]), 2) for n, a in enumerate(FIVE) for b in FIVE[n + 1:]}
    one = {k: v for k, v in SH.items() if v > .85}
    chk("A. [%s] Forge, Lunar, Solar, Tempest and Inferno are each built differently: their parts and path commands differ, and their openings are not one recipe at different sizes - each opening's shape scaled to its own box overlaps every other's by at most .85 (same parts: %s; one shape: %s)" % (
        key, same or "none", one or "none"), not same and not one, {"shape": SH, "sig": {i: L[i]["sig"][:100] for i in FIVE}})
    pairs = [(a, b) for n, a in enumerate(FOUR) for b in FOUR[n + 1:]] + [(a, b) for a in FOUR for b in PINNED]
    IO = {a + "/" + b: round(iou(L[a]["grid"], L[b]["grid"]), 2) for a, b in pairs}
    print("   (for scale: oracle/frost %.2f, inferno/frost %.2f, inferno/oracle %.2f)" % tuple(iou(L[a]["grid"], L[b]["grid"]) for a, b in (("oracle", "frost"), ("inferno", "frost"), ("inferno", "oracle"))))
    alike = {k: v for k, v in IO.items() if v > .80}
    chk("A. [%s] ...and each has its own silhouette: outline overlap at most .80 (r7's four: .91-.98) for every pair of the four and with Inferno, Oracle, Frost (highest %s; too alike: %s)" % (
        key, max(IO.items(), key=lambda kv: kv[1]), alike or "none"), not alike, IO)
    # C
    for i in FOUR:
        pass
    wide = {}
    for i in FOUR:
        for n, e in enumerate(EY[i]):
            pe = P["eye"][i][n]
            if not (e["ratio"] <= .40 and pe and e["ratio"] <= pe["ratio"] + .005): wide[i + ("L" if n == 0 else "R")] = (round(e["ratio"], 3), pe and round(pe["ratio"], 3))
    chk("C. [%s] every eye of the four is narrow: height/width at most .40 and no rounder than cd34de2's (%s; too round: %s)" % (
        key, {i: [round(e["ratio"], 2) for e in EY[i]] for i in FOUR}, wide or "none"), not wide, wide)
    deco = {}
    for i in FOUR:
        for e in EY[i]:
            x0, y0, x1, y1 = e["box"]
            for p in e["parts"]:
                bx = p["box"]
                side_, up_, down_ = max(x0 - bx[0], bx[2] - x1), y0 - bx[1], bx[3] - y1
                if p["glowy"] and p["before"] and bx[0] <= x0 + .2 and bx[2] >= x1 - .2: continue   # a socket, halo or soot under the whole eye
                # a lash, a liner flick or a ray runs out past a CORNER or off an edge; a lid may sit up to .4 over the top edge
                if side_ > .15 or down_ > .25 or up_ > (.4 if p["filled"] else .25):
                    deco.setdefault(i, []).append("%s %s past the eye (side %.2f, up %.2f, down %.2f)" % (p["tag"], p["fill"] if p["filled"] else "stroke " + p["stroke"], side_, up_, down_))
            if e["iris"]:
                for a in e["after"]:
                    col = a["fill"] if a["fill"] not in ("none", "") else a["stroke"]
                    lt = lum(col)
                    if lt is not None and lt >= .88 and (abs(a["cx"] - e["iris"]["cx"]) > .3 * e["iris"]["r"] or abs(a["cy"] - e["iris"]["cy"]) > .3 * e["iris"]["r"]) and a["w"] < e["iris"]["r"]:
                        deco.setdefault(i, []).append("catch-light %s" % col)
    chk("C. [%s] nothing lash-like or decorative: no stroke past the eye, no small shape outside it, no catch-light (%s)" % (key, deco or "none"), not deco, deco)
    worried = {}
    for i in FOUR:
        for d in R["eyes"][i]["brows"]:
            for seg in d:
                xs, ys = seg[0::2], seg[1::2]
                if len(xs) < 2: continue
                # the end nearer the face's centre line (x 20) against the end further from it
                near = min(range(len(xs)), key=lambda k: abs(xs[k] - 20)); far = max(range(len(xs)), key=lambda k: abs(xs[k] - 20))
                if ys[near] < ys[far] - .05: worried.setdefault(i, []).append(seg)
    chk("C. [%s] every brow of the four is no higher at the nose than at the temple - never a worried brow (worried: %s)" % (key, worried or "none"), not worried, worried)
    # D
    moved = {}
    for i in FOUR:
        for n, e in enumerate(EY[i]):
            pe = P["eye"][i][n]
            if not pe or abs(e["centre"][0] - pe["centre"][0]) > .4 or abs(e["centre"][1] - pe["centre"][1]) > .4 or abs(e["W"] / pe["W"] - 1) > .25:
                moved[i + ("L" if n == 0 else "R")] = ([round(v, 2) for v in e["centre"]], pe and [round(v, 2) for v in pe["centre"]], round(e["W"], 2), pe and round(pe["W"], 2))
    chk("D. [%s] each eye stays where cd34de2 had it (centre within .4) at roughly its size (width within 25%%) (moved: %s)" % (key, moved or "none"), not moved, moved)
    outs = {i: [(e["outFace"], e["onBrow"], e["samples"]) for e in EY[i]] for i in FOUR}
    bad = {i: v for i, v in outs.items() if any(o or b or not n for o, b, n in v)}
    chk("D. [%s] every eye part of the four is inside the face and clear of the brows (points outside / on a brow / sampled: %s)" % (key, bad or outs), not bad, bad)
    floating = {}
    for i in FOUR:
        for e in EY[i]:
            x0, y0, x1, y1 = e["box"]
            for p in e["parts"]:
                bx = p["box"]
                if bx[2] < x0 or bx[0] > x1 or bx[3] < y0 or bx[1] > y1: floating.setdefault(i, []).append(p["tag"])
    chk("D. [%s] nothing floats: every part of each eye touches its opening (floating: %s)" % (key, floating or "none"), not floating, floating)
    # E
    bad = [i for i in PINNED if R["full"].get(i) != P["full"].get(i)]
    chk("E. [%s] Inferno, Oracle and Frost are byte for byte what cd34de2 drew (changed: %s)" % (key, bad or "none"), not bad, bad)
    others = sorted(set(P["full"]) | set(R["full"]))
    mv = [i for i in others if i not in FOUR and R["full"].get(i) != P["full"].get(i)]
    chk("E. [%s] every other character (%d of them) is byte for byte cd34de2's (changed: %s)" % (key, len(others) - len(FOUR), mv or "none"), not mv and len(others) >= 25, mv)
    rest = [i for i in FOUR if R["noEyes"].get(i) != P["noEyes"].get(i)]
    chk("E. [%s] ...and the four are cd34de2's outside their eye group and brows - crown, hair, robe, backdrop, neck, mouth, closed eyes (changed: %s)" % (key, rest or "none"), not rest, rest)
    same = [i for i in FOUR if R["full"].get(i) == P["full"].get(i)]
    chk("E. [%s] ...while the four's eyes did change (unchanged: %s)" % (key, same or "none"), not same, same)

# B (the academy page; E says the drawings are the same in both classes)
BD = ACA["band"]
if all(i in BD for i in SEVEN):
    D = {a + "/" + b: round(1 - corr(BD[a], BD[b]), 3) for n, a in enumerate(SEVEN) for b in SEVEN[n + 1:]}
    near = {k: v for k, v in D.items() if v < .30}
    chk("B. the squint test: greyscale 26px, the eye band of every pair of the seven rulers differs by at least .30 (1 - correlation; closest %s; too alike: %s)" % (
        min(D.items(), key=lambda kv: kv[1]), near or "none"), not near, D)
C = ACA["coin"]; fr = C.get("frost", 0)
faint = {i: C[i] for i in FOUR if C[i] < .8 * fr}
chk("B. on a 26px coin each of the four's eyes carries at least 80%% of the ink Frost's do (pixel change with the eyes hidden, %s; faint: %s)" % (C, faint or "none"), not faint and fr > 3, C)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
