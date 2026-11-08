#!/usr/bin/env python3
"""Build 384, round 6 (r6-eyes): the four crowned rulers get eyes of their own, in Frost's spirit.

  "The 5 rank up characters, see I'm not sure what to do, it looks cool on oracle but the rest looks repetitive. Frost keeps the shape and
   makes a slight change which I really like.. what if they did that? But don't change oracle or frost?"

  Forge, Lunar, Solar, Tempest and Oracle all wore one eye: a translucent glowing oval in the character's colour with a white almond inside
  it and nothing in the almond - a hollow ring; only the colour changed. Frost kept the almond and put an iris in it. Read off the drawn
  SVG of each character (drawAvatarCharSVG), in BOTH classes (the academy and Fire Code share these five):

  A. THE RING IS GONE from Forge, Lunar, Solar and Tempest: each eye has an iris (a coloured disc centred in the almond) and no
     translucent glow ellipse round the almond.
  B. FOUR DIFFERENT EYES: the eye's STRUCTURE (glow or not, the iris's colour family, and where its marks sit - below the eye, off the
     outer corner, inside the iris) differs between every two of Forge, Lunar, Solar, Tempest and Frost; so does its fine signature
     (every shape, its place and colour), and the four irises are four colours, none of them Frost's blue.
  C. THE SAME EYE SHAPE, PLACE AND SIZE: the white almond of each of the four is where and the size it was on 130a41c (the eyes the
     faces are known by), and every mark stays inside the face, clear of the brow.
  D. ORACLE AND FROST ARE BYTE FOR BYTE 130a41c's (check-b384-r6-eyes.prev.json), in both classes.
  E. NOTHING ELSE MOVED: every other character in both classes is byte for byte 130a41c's, and the four are 130a41c's too once their
     eye group is taken out (the crowns, hair, robes, backdrops and necks are untouched).
  F. no page error in either class.

  python3 tools/check-b384-r6-eyes.py [--against OLD/index.html]     (A and B FAIL on 130a41c; D and E are pinned to it, and FAIL
                                                                        on a build that touches Frost, Oracle or anyone else)
  python3 tools/check-b384-r6-eyes.py --dump --against 130a41c.html  (writes check-b384-r6-eyes.prev.json)
"""
import json, os, sys, colorsys
# SUPERSEDED IN 384 r7 (check-b384-r7-eyes.py): "Not a fan of gold and platinum eyes they look girly and not mean. Inferno needs to match
# probably.." The four's r6 eyes (round iris, outline, rays / crescent / spark / flick) and the 130a41c pins this checks are gone on
# purpose; r7 pins Oracle and Frost (and everyone else) to 6057892 instead. Still runs --against an r6 build.
if "--against" not in sys.argv and "--dump" not in sys.argv:
    print("SKIP superseded by check-b384-r7-eyes.py (the rulers' glare replaced the r6 eyes)"); sys.exit(0)
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

FOUR = ["forge", "lunar", "solar", "tempest"]
EYES = FOUR + ["frost", "oracle"]
# C. the white almond of each of the four on 130a41c: [cx of the left eye, cy, rx, ry]
ALMOND = {"forge": [16.8, 17.7, 1, .52], "lunar": [16.8, 17.7, 1.02, .5], "solar": [16.8, 17.8, 1.05, .55], "tempest": [16.8, 18, 1.08, .52]}

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4r6eyes01", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT_IFC = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
INIT_ACA = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S

SNAP = r"""(EYES) => {
  document.getElementById('splashscreen')?.remove();
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;opacity:0;pointer-events:none';
  document.body.appendChild(host);
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const ser = s => new XMLSerializer().serializeToString(s).split(s.getAttribute('data-cx-uid') || '@@none@@').join('U');
  const mount = id => { const s = drawAvatarCharSVG(id); if(!s) return null; s.setAttribute('width', 340); s.setAttribute('height', 340); host.appendChild(s); return s; };
  const out = { cls: window.NOVA_CLASS || 'academy', full: {}, noEyes: {}, eyes: {} };
  for(const c of AVATAR_CHARACTERS){
    let s; try{ s = mount(c.id); }catch(e){ out.full[c.id] = 'ERR ' + e.message; continue; }
    if(!s){ out.full[c.id] = out.noEyes[c.id] = 'no drawing (retired)'; continue; }
    out.full[c.id] = hash(ser(s));
    const e = s.querySelector('.cx-eyes'); if(e) e.remove(); out.noEyes[c.id] = hash(ser(s));
    s.remove();
  }
  /* the eye group of each ruler, shape by shape: tag, the geometry it was drawn with, its box, fill, stroke, opacity */
  for(const id of EYES){
    const s = mount(id), g = s.querySelector('.cx-eyes');
    const brow = [...s.querySelectorAll('.cx-head path')].filter(p => !p.closest('.cx-eyes') && p.getAttribute('stroke') && /^M1[45](\.\d+)? 15\.\d/.test(p.getAttribute('d') || '')).map(p => { const b = p.getBBox(); return b.y + b.height + (+p.getAttribute('stroke-width') || 0) / 2; });
    const face = s.querySelector('.cx-head path[d^="M12.6 15.2"], .cx-head path[d^="M12.8 15.6"]');
    const fb = face ? face.getBBox() : null;
    out.eyes[id] = { browBottom: brow.length ? Math.max(...brow) : null, face: fb ? [fb.x, fb.y, fb.x + fb.width, fb.y + fb.height] : null,
      els: g ? [...g.querySelectorAll('path,circle,ellipse,rect')].map(el => { const b = el.getBBox(); const a = n => el.getAttribute(n);
        return { tag: el.tagName, cx: +a('cx') || null, cy: +a('cy') || null, r: +a('r') || null, rx: +a('rx') || null, ry: +a('ry') || null,
          box: [b.x, b.y, b.x + b.width, b.y + b.height], fill: a('fill') || '', stroke: a('stroke') || '', sw: +a('stroke-width') || 0, op: a('opacity') === null ? 1 : +a('opacity') }; }) : [] };
    s.remove();
  }
  return out; }"""

def run(init, label):
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
        r = pg.evaluate(SNAP, EYES)
        ctx.close(); br.close()
    srv.shutdown()
    r["errs"] = errs
    return r

ACA = run(INIT_ACA, "academy")
IFC = run(INIT_IFC, "ifc")
PREVF = os.path.join(HERE, "check-b384-r6-eyes.prev.json")
if "--dump" in sys.argv:
    json.dump({k: {"full": R["full"], "noEyes": R["noEyes"]} for k, R in (("academy", ACA), ("ifc", IFC))}, open(PREVF, "w"), indent=0, sort_keys=True)
    print("dumped", PREVF); sys.exit(0)

def rgb(h):
    h = (h or "").strip()
    if not (h.startswith("#") and len(h) in (4, 7)): return None
    if len(h) == 4: h = "#" + "".join(c * 2 for c in h[1:])
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
def hls(h):
    c = rgb(h); return colorsys.rgb_to_hls(*c) if c else None
def whiteish(h):
    c = hls(h); return bool(c) and c[1] >= .88
def family(h):
    c = hls(h)
    if not c: return "none"
    H, L, Sa = c[0] * 360, c[1], c[2]
    if Sa < .3: return "silver"
    return "h%d" % int(H)

def anatomy(E):
    """Split the LEFT eye's shapes into almond, glow, iris, pupil and marks; marks are named by where they sit."""
    els = [e for e in E["els"] if (e["box"][0] + e["box"][2]) / 2 < 20]
    alm = [e for e in els if e["tag"] == "ellipse" and whiteish(e["fill"]) and .85 <= (e["rx"] or 0) <= 1.25 and e["op"] >= .9]
    if not alm: return {"almond": None, "glow": False, "iris": None, "marks": [], "els": els}
    a = alm[-1]; ax, ay, rx, ry = a["cx"], a["cy"], a["rx"], a["ry"]
    glow = [e for e in els if e["tag"] == "ellipse" and e is not a and abs(e["cx"] - ax) < .05 and abs(e["cy"] - ay) < .05 and (e["rx"] or 0) > rx * 1.3 and e["op"] < 1]
    disc = [e for e in els if e["tag"] == "circle" and abs(e["cx"] - ax) < .12 and abs(e["cy"] - ay) < .12 and els.index(e) > els.index(a)]
    iris = [e for e in disc if .3 <= e["r"] <= .6 and not whiteish(e["fill"]) and hls(e["fill"])]
    pupil = [e for e in disc if e["r"] < .3]
    skip = set(map(id, [a] + glow + iris + pupil))
    marks = []
    for e in els:
        if id(e) in skip: continue
        x0, y0, x1, y1 = e["box"]; mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        zone = ("in-iris" if iris and abs(mx - ax) < iris[0]["r"] and abs(my - ay) < iris[0]["r"] else
                "outer" if mx < ax - rx * .8 else "inner" if mx > ax + rx * .8 else "below" if my > ay else "above")
        kind = "stroke" if (e["fill"] in ("", "none") and e["stroke"]) else "fill"
        marks.append((zone, e["tag"], kind))
    return {"almond": [ax, ay, rx, ry], "glow": bool(glow), "iris": iris[0]["fill"] if iris else None, "pupil": bool(pupil), "marks": sorted(set(marks)), "els": els}

for key, R in (("academy", ACA), ("ifc", IFC)):
    chk("[%s] the page is that class with no page error (%s)" % (key, R["errs"][:2]), R["cls"] == key and not R["errs"], R["errs"])
    AN = {i: anatomy(R["eyes"][i]) for i in EYES}
    # A
    ring = {i: {"glow": AN[i]["glow"], "iris": AN[i]["iris"]} for i in FOUR if AN[i]["glow"] or not AN[i]["iris"]}
    chk("A. [%s] Forge, Lunar, Solar and Tempest no longer wear the hollow ring: each eye has an iris and no glow ring round it (ring: %s)" % (key, ring or "none"),
        not ring and all(AN[i]["almond"] for i in FOUR), {i: (AN[i]["almond"], AN[i]["glow"], AN[i]["iris"]) for i in FOUR})
    # B
    five = FOUR + ["frost"]
    struct = {i: json.dumps([AN[i]["glow"], family(AN[i]["iris"]), AN[i]["pupil"], AN[i]["marks"]]) for i in five}
    q = lambda v: round(v * 20) / 20
    fine = {i: json.dumps([[e["tag"], [q(v) for v in e["box"]], e["fill"], e["stroke"], q(e["op"])] for e in AN[i]["els"]]) for i in five}
    dup = [(a, b) for n, a in enumerate(five) for b in five[n + 1:] if struct[a] == struct[b] or fine[a] == fine[b]]
    chk("B. [%s] the eye differs between every two of Forge, Lunar, Solar, Tempest and Frost - in structure (glow, iris colour, marks and where they sit) AND in fine signature (every shape, its place and colour) (same: %s)" % (key, dup or "none"),
        not dup, struct)
    hues = {i: hls(AN[i]["iris"]) for i in five}
    def apart(a, b):
        ha, hb = hues[a], hues[b]
        if not ha or not hb: return False
        if (ha[2] < .3) != (hb[2] < .3): return True
        d = abs(ha[0] - hb[0]) * 360; d = min(d, 360 - d); return d >= 12
    close = [(a, b) for n, a in enumerate(five) for b in five[n + 1:] if not apart(a, b)]
    chk("B. [%s] ...the four irises are four colours, none of them Frost's blue (%s; too close: %s)" % (key, {i: AN[i]["iris"] for i in five}, close or "none"), not close, hues)
    nomark = [i for i in FOUR if not AN[i]["marks"]]
    chk("B. [%s] ...and each of the four carries a slight mark of its own beside or in the eye (none: %s)" % (key, nomark or "none"), not nomark, {i: AN[i]["marks"] for i in FOUR})
    # C
    moved = {i: (AN[i]["almond"], ALMOND[i]) for i in FOUR if not AN[i]["almond"] or any(abs(u - v) > .005 for u, v in zip(AN[i]["almond"], ALMOND[i]))}
    chk("C. [%s] each of the four keeps its almond's place and size from 130a41c (moved: %s)" % (key, moved or "none"), not moved, moved)
    out = {}
    for i in FOUR:
        E = R["eyes"][i]; fx = E["face"]; bb = E["browBottom"]
        for e in E["els"]:
            x0, y0, x1, y1 = e["box"]; pad = e["sw"] / 2
            if not fx or x0 - pad < fx[0] or x1 + pad > fx[2] or (bb is not None and y0 - pad < bb):
                out.setdefault(i, []).append([round(v, 2) for v in e["box"]])
    chk("C. [%s] every eye shape stays inside the face and below the brow (out: %s)" % (key, out or "none"), not out, {i: (R["eyes"][i]["face"], R["eyes"][i]["browBottom"]) for i in FOUR})

if not os.path.exists(PREVF):
    chk("the 130a41c pin file exists (%s)" % PREVF, False); print("\nFAILURES"); sys.exit(1)
PREV = json.load(open(PREVF))
for key, R in (("academy", ACA), ("ifc", IFC)):
    P = PREV[key]
    # D
    bad = [i for i in ("oracle", "frost") if R["full"].get(i) != P["full"].get(i)]
    chk("D. [%s] Oracle and Frost are byte for byte what 130a41c drew (changed: %s)" % (key, bad or "none"), not bad, {i: (R["full"].get(i), P["full"].get(i)) for i in ("oracle", "frost")})
    # E
    others = sorted(set(P["full"]) | set(R["full"]))
    moved = [i for i in others if i not in FOUR and R["full"].get(i) != P["full"].get(i)]
    chk("E. [%s] every other character (%d of them) is byte for byte 130a41c's (changed: %s)" % (key, len(others) - len(FOUR), moved or "none"), not moved and len(others) >= 25, moved)
    rest = [i for i in FOUR if R["noEyes"].get(i) != P["noEyes"].get(i)]
    chk("E. [%s] ...and the four are 130a41c's outside their eye group - crown, hair, robe, backdrop, neck (changed: %s)" % (key, rest or "none"), not rest, rest)
    same = [i for i in FOUR if R["full"].get(i) == P["full"].get(i)]
    chk("E. [%s] ...while the four's eyes did change (unchanged: %s)" % (key, same or "none"), not same, same)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
