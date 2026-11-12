#!/usr/bin/env python3
"""Is every pill, button, chip, tag, badge, round icon button, disc and segmented item centred - BY ITS INK? (build 384)

Madison: "ensure the still here is also centered cause I can tell it's slightly off. You need to do a full check on the
entire app to ensure there's nothing else like this whatsoever. I've been asking you to fix this off centering problem over
and over and over ... we need a permanent fix so you don't allow it to happen again."

A box can be centred while what is drawn in it is not: a font's capitals sit high in their line box, letter-spacing after
the last letter pushes a spaced word left, an icon's drawing does not fill its viewBox evenly, an icon beside a word adds
its own air to one side. So this measures INK, never boxes. It walks every screen in both classes (Police Academy and Fire
Code) - Get Started, Welcome, sign in and the sign-up steps, Home and its class list, Choose your mode, the units in every
mode, a test (question, answer, Pause card), results, Review, Test history, flash cards, Profile, Stats, Customize, the
rank ladder, the badge case, Friends, the Leaderboard's boards, the Calendar, Settings and every page, the classes and
enrolling, the chat's three tabs, the Virtual Room's screens, the save-code and sign-out sheets, What's New, Add to Home
Screen, every banner, the update / Home Screen notices, a toast, the tips - scrolled top to bottom (6 steps at most), and
on each finds every element that draws a shape (its own fill / rim / glass, or a pseudo-element's) with something inside it.
For each it screenshots the page as drawn, then with the content's words made transparent (-webkit-text-fill-color only,
so nothing drawn in currentColor changes), then with all its content hidden; the differences are the words' ink and the
icons' ink. Edges are placed to a fraction of a device pixel (half-coverage crossing). The words are measured from their
top to their BASELINE (read off the pixels: where the stems end), so a descender (g, p, y) does not count, as a typesetter
centres capitals. Then: the ink's gap to the shape's left vs right edge, and top vs bottom.

FAILS on anything off by more than 0.5 CSS px (1 px for a shape over 120px wide), and prints which element, its words, the
screen, class and size, and by how much (+ is right / low). Not measured, on purpose:
  - content laid out from an edge (a list row: tile at its left, chevron at its right; two lines set from the left in a
    card) - it is not meant to be centred; its up-down still is when it is one line (not a row with a picture in it);
  - a card or bar that holds its own button (the button is measured), a track of several controls (each control is);
  - the tab bar's tabs up-down (their words share one line by design; icons differ in height) - across they are asked,
    the lit one against the slider's pill;
  - pictures (a character, a flare, a planet, an emblem - many colours or an image): their visible box stands in for
    their ink (a character is drawn off-symmetric on purpose and placed per character); Home's and Welcome's orbit
    planets are left out; the badge case's drawn latches too;
  - anything that will not hold still (re-read twice, then listed under "Moving");
  - OWNED (the OWNED list in check-centering.js): elements another piece of work owns - listed under "owned by other
    work", failed only with --strict (build 384: the Fire Code code pictures' tag pills). Empty it when that lands.
CHROMIUM, NOT THE APP: with only an emulated pixel ratio, Chromium rounds where it draws a line of words and an <svg> to
a whole CSS pixel (up to half a pixel off) where a phone rounds to a device pixel. So each size runs in a Chromium launched
at that device's own scale (--force-device-scale-factor), which rounds as the phone does (build 384 notes: the test page).
Every size is measured at 3x: an iPad draws at 2x and a laptop at 1-2x, but the layout is the same in CSS pixels and a
coarser screen only adds its own rounding (half a CSS pixel at 2x) to what is measured.
Fonts: Chromium here draws Inter where the iPhone draws SF; the cures (text-box trim, padding moved, icons moved by their
own geometry) do not depend on the font, but a residue under a pixel can differ on a phone.

  python3 tools/check-centering.py --quick            iPhone 17 Pro Max (440x956), both classes: run after any UI change
  python3 tools/check-centering.py --jobs 3           + iPhone SE (375x667), iPad Pro 11" (834x1194), laptop 1536x864
  options: --against REV|FILE   measure another build (git rev or file): build 384's start (claude/b384) FAILS
           --only REGEX         screens whose name matches (home, units/game, settings/sound, signup/class ...)
           --class academy|ifc  --sizes REGEX   --jobs N (default 2: each size and class is its own browser)
           --shots DIR          a crop of each failing element (drawn | content hidden, shape blue, ink red); -v all
           --json FILE          every measurement     --strict   fail on OWNED elements too
The measuring half runs in the page: tools/check-centering.js."""
import base64, io, json, math, os, re, subprocess, sys, time
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright

def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
QUICK = "--quick" in sys.argv
ONLY = re.compile(arg("--only")) if arg("--only") else None
CLASSES = (arg("--class") or "academy,ifc").split(",")
SHOTS = arg("--shots")
VERBOSE = "-v" in sys.argv
JOBS = int(arg("--jobs", "2"))
AGAINST = None
if arg("--against"):
    a = arg("--against")
    AGAINST = open(a, encoding="utf-8").read() if os.path.isfile(a) else subprocess.check_output(["git", "-C", ROOT, "show", a + ":index.html"]).decode("utf-8")
ENGINE = open(os.path.join(HERE, "check-centering.js"), encoding="utf-8").read()

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_IPAD = "Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
# name, w, h, dpr, safe-area insets, installed (Home Screen app), touch, UA
DEVICES = [("iPhone 17 Pro Max", 440, 956, 3, (62, 0, 34, 0), True, True, UA),
           ("iPhone SE", 375, 667, 3, (20, 0, 0, 0), True, True, UA),
           # an iPad draws at 2x and a laptop at 1-2x, but every size is measured at 3x: the layout is the same in CSS
           # pixels, and a coarser screen only adds its own rounding (half a CSS pixel at 2x) to what is measured
           ("iPad Pro 11", 834, 1194, 3, (24, 0, 20, 0), True, True, UA_IPAD),
           ("laptop", 1536, 864, 3, (0, 0, 0, 0), False, False, None)]
if arg("--sizes"): DEVICES = [d for d in DEVICES if re.search(arg("--sizes"), d[0], re.I)]
elif QUICK: DEVICES = DEVICES[:1]

OWNER = "xph5b57jbp5a"
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',"
        "'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.freshstart'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal55124.seen','1'); localStorage.setItem('class26e.penal124256.seen','1'); localStorage.setItem('class26e.penal256578.seen','1');")
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); """ + SEEN + """ %s })()"""
IFC = ("localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1')); localStorage.setItem('class26e.ifc.synccode','TEST-3843');"
       "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');")
def seed():
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = OWNER; d["firstName"] = "Casey"; d["novaMet"] = 99
    return d

def body_for(ins):
    if AGAINST is None: return g["patched"](ins)
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)

def open_page(br, dev, cls):
    name, w, h, dpr, ins, installed, touch, ua = dev
    kw = {"viewport": {"width": w, "height": h}, "device_scale_factor": dpr, "has_touch": touch}
    if ua: kw.update(is_mobile=True, user_agent=ua)
    ctx = br.new_context(**kw)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = body_for(ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.add_init_script(INIT % (json.dumps(json.dumps(seed())), IFC if cls == "ifc" else ""))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(URL); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; "
                "try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} "
                "document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    pg.evaluate(ENGINE)
    VIEW.update(w=w, h=h, dpr=dpr)
    cdp = ctx.new_cdp_session(pg)
    cdp.send("Animation.enable")
    return ctx, pg, cdp, errs

VIEW = {"x": 0, "y": 0}
def grab(cdp, box):
    """A screenshot of box = (x0, y0, x1, y1) in device pixels of the viewport. The clip is in page coordinates (the
    viewport's own place on the page), at the device's scale, on whole device pixels."""
    d = VIEW["dpr"]; x0, y0, x1, y1 = box
    r = cdp.send("Page.captureScreenshot", {"format": "png", "optimizeForSpeed": True,
                 "clip": {"x": VIEW["x"] + x0 / d, "y": VIEW["y"] + y0 / d, "width": (x1 - x0) / d, "height": (y1 - y0) / d, "scale": VIEW.get("cscale", d)}})
    a = np.asarray(Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")).astype(np.int16)
    return a[:y1 - y0, :x1 - x0]

def diffmap(a, b):
    return np.abs(a - b).max(axis=2)

def bbox(d, thr):
    m = d >= thr
    if not m.any(): return None
    rows = np.where(m.any(axis=1))[0]; cols = np.where(m.any(axis=0))[0]
    return cols[0], rows[0], cols[-1] + 1, rows[-1] + 1

def edge(profile, i, inward):
    """Where an edge really is, to a fraction of a device pixel: profile is the strongest change along each column (or
    row), i the first pixel past the threshold, inward the direction into the ink. The edge is where the change crosses
    half of the ink's own strength (the strongest within 3 pixels inward), interpolated between two pixels - an
    antialiased edge's half-covered pixel shows half the change."""
    n = len(profile)
    near = profile[i:i + 3] if inward > 0 else profile[max(0, i - 2):i + 1]
    full = float(near.max()) if near.size else float(profile[i])
    if full <= 0: return float(i if inward > 0 else i + 1)
    half = full / 2
    j = i
    # walk outward while still above half, then interpolate between the last pixel above and the first below
    while 0 <= j - inward < n and profile[j - inward] >= half: j -= inward
    a = float(profile[j]); b = float(profile[j - inward]) if 0 <= j - inward < n else 0.0
    frac = 0.0 if a == b else (a - half) / (a - b)   # 0: the edge is at j's outer side; 1: one pixel further out
    frac = min(1.0, max(0.0, frac))
    # pixel j spans [j, j+1]; with full coverage the edge would be at its outer side, with half at its middle
    return (j - frac + .5) if inward > 0 else (j + 1 + frac - .5)

def measure_cand(c, A1, A2, B, C, dpr, org):
    S = c["S"]; ox, oy = org
    x0, y0 = max(ox, int(math.floor(S["l"] * dpr))), max(oy, int(math.floor(S["t"] * dpr)))
    x1, y1 = min(ox + A1.shape[1], int(math.ceil(S["r"] * dpr))), min(oy + A1.shape[0], int(math.ceil(S["b"] * dpr)))
    if x1 - x0 < 4 or y1 - y0 < 4: return None
    sl = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
    # anything that moved between the first and the last screenshot (an animation that is not a CSS one) makes the
    # element unmeasurable this time: it is tried again, and reported if it never holds still
    noise = diffmap(A1[sl], A2[sl]) > 10
    if noise.sum() > max(6, .002 * noise.size): return {"unstable": round(float(noise.mean()), 4)}
    dall = diffmap(A1[sl], C[sl]); dall[noise] = 0
    if os.environ.get("CZ_DUMP") and os.environ["CZ_DUMP"] in c["name"]:
        np.savez(os.environ.get("CZ_DUMP_TO", "/tmp/cz-dump.npz"), A=A1[sl], C=C[sl], x0=x0, y0=y0, S=json.dumps(c["S"]), lines=json.dumps(c["lines"]))
    vals = dall[dall > 10]
    if vals.size < 6 and not c["art"]: return {"empty": True}
    def box_of(d):
        v = d[d > 10]
        if v.size < 4: return None
        # ink is any pixel changed by more than a third of the strongest change (the 5th strongest: one stray pixel
        # cannot set it) - a glass shape's own shimmer, a few levels, stays under it; an edge's half-covered pixels fall
        # the same way on both sides, and edge() then places each edge to a fraction of a pixel
        top = float(np.partition(v, -min(5, v.size))[-min(5, v.size)])
        thr = max(18, .35 * top)
        bb = bbox(d, thr)
        if not bb: return None
        cm, rm = d.max(axis=0).astype(float), d.max(axis=1).astype(float)
        L, T = edge(cm, bb[0], 1), edge(rm, bb[1], 1)
        Rr, Bb = edge(cm, bb[2] - 1, -1), edge(rm, bb[3] - 1, -1)
        return [(x0 + L) / dpr, (y0 + T) / dpr, (x0 + Rr) / dpr, (y0 + Bb) / dpr, thr]
    def baseline_of(d, thr, dom):
        """The words' baseline read off the pixels. Stems stand on it, so it is where columns of ink end: of the rows
        near the layout's own baseline (within 1.5px above it and 1px below - a descender ends further down, a 4's or
        a 7's crossbar further up), the lowest one several columns end on; failing that, the row most columns end on.
        None when nothing is shared widely enough to trust."""
        m = d >= thr
        cols = np.where(m.any(axis=0))[0]
        if cols.size < 3: return None
        bottoms = np.array([np.where(m[:, x])[0][-1] + 1 for x in cols])
        lo, hi = (dom - 1.5) * dpr - y0, (dom + 1.0) * dpr - y0
        need = max(2, int(.08 * cols.size))
        pick = None
        for r in sorted(set(bottoms.tolist()), reverse=True):
            if not (lo <= r <= hi): continue
            if ((bottoms >= r - 1) & (bottoms <= r)).sum() >= need: pick = r; break
        if pick is None:
            # (the layout's baseline can be pixels off - a trimmed line reports its trimmed box - so the row most
            # columns end on is taken instead)
            vals, counts = np.unique(bottoms, return_counts=True)
            best = max(((v, counts[(vals >= v) & (vals <= v + 1)].sum()) for v in vals), key=lambda t: t[1])
            if best[1] < max(3, .3 * cols.size): return None
            pick = best[0] + 1
        # each of those columns' bottom edge, to a fraction of a pixel, and their middle value
        ys = [edge(d[:, x].astype(float), int(bb) - 1, -1) for x, bb in zip(cols, bottoms) if pick - 1 <= bb <= pick]
        return (y0 + float(np.median(ys))) / dpr
    ink_all = box_of(dall)
    # the shape itself must be the same with its content hidden: if much of it changed outside the content (the
    # whole bar slid in or out between the screenshots), this reading is not a reading - it is tried again
    if ink_all:
        ix0, iy0 = int(ink_all[0] * dpr) - x0, int(ink_all[1] * dpr) - y0
        ix1, iy1 = int(math.ceil(ink_all[2] * dpr)) - x0, int(math.ceil(ink_all[3] * dpr)) - y0
        outside = dall > 24; outside[max(0, iy0 - 2):iy1 + 2, max(0, ix0 - 2):ix1 + 2] = False
        if outside.mean() > .05: return {"unstable": round(float(outside.mean()), 3)}
    if not ink_all and not c["art"]: return {"empty": True}
    dtext = dall
    if c["mixed"] and B is not None:
        dt = diffmap(A1[sl], B[sl]); dt[noise] = 0; dtext = dt
        di = diffmap(B[sl], C[sl]); di[noise] = 0
        ink_t, ink_i = box_of(dt), box_of(di)
    elif not ink_all:
        ink_t, ink_i = None, None
    elif c["lines"]:
        ink_t, ink_i = ink_all, None
    else:
        ink_t, ink_i = None, ink_all
    parts = []; bases = None
    if ink_t:
        top = ink_t[1]; bot = ink_t[3]
        if c["lines"]:
            # the words stand on their baseline: what hangs below it (g, p, y) is not counted, as a typesetter
            # centres capitals, not descenders. The baseline is read off the pixels; the layout's own is the fallback.
            last = c["lines"][-1]
            base_dom = last["base"]
            base_px = baseline_of(dtext, ink_t[4], base_dom)
            base = base_px if base_px is not None and abs(base_px - base_dom) < 6 else base_dom
            bases = [round(base_dom, 2), None if base_px is None else round(base_px, 2)]
            # a last line without a descender: the ink's own bottom IS its baseline (no guessing); with one, the
            # baseline read off the stems
            if last.get("desc", c.get("desc")): bot = base
            else: base = bot
            # words with a capital and something taller (an i's dot, an ascender) are centred on their capitals - the
            # first line's capital height above its baseline (the lines' spacing from the layout), as text-box trims
            # them and as a typesetter centres them; words without a capital or ascender by their ink's own top
            if c.get("caps"): top = base - (last["base"] - c["lines"][0]["base"]) - c["lines"][0]["cap"]
            elif not c["tall"]: top = min(base - L["cap"] for L in c["lines"][-1:])
        parts.append([ink_t[0], top, ink_t[2], bot])
    if ink_i:
        sx, sy = c.get("snap", [0, 0])
        parts.append([ink_i[0] - sx, ink_i[1] - sy, ink_i[2] - sx, ink_i[3] - sy])
    for a in c["art"]: parts.append([a["l"], a["t"], a["r"], a["b"]])
    if not parts: return {"empty": True}
    L = min(p[0] for p in parts); T = min(p[1] for p in parts); Rr = max(p[2] for p in parts); Bb = max(p[3] for p in parts)
    # the shape is drawn on the device's pixel grid (its edges rounded to device pixels), so it is compared as drawn
    q = lambda v: math.floor(v * dpr + .5) / dpr    # (half a device pixel rounds UP, as the browser snaps it: Python's round() takes 2980.5 to 2980 and read a disc at x 993.5 a third of a pixel off)
    gl, gr, gt, gb = L - q(S["l"]), q(S["r"]) - Rr, T - q(S["t"]), q(S["b"]) - Bb
    if SHOTS:
        c["_crop"] = (A1[sl].astype(np.uint8), C[sl].astype(np.uint8), (x0, y0), [L, T, Rr, Bb])
    return {"dx": round((gl - gr) / 2, 2), "dy": round((gt - gb) / 2, 2), "gaps": [round(gl, 2), round(gr, 2), round(gt, 2), round(gb, 2)],
            "edgeX": bool(max(gl, gr) < .4), "edgeY": bool(max(gt, gb) < .4), "bases": bases}

def save_crop(r, path):
    """The element as drawn (left) and with its content hidden (right), 4x, its shape in blue and its ink in red."""
    from PIL import ImageDraw
    A, C, (x0, y0), ink = r["_crop"]; dpr = VIEW["dpr"]; k = max(1, int(round(8 / dpr)))
    h, w = A.shape[:2]
    im = Image.new("RGB", (w * 2 * k + 6, h * k), (255, 0, 255))
    im.paste(Image.fromarray(A).resize((w * k, h * k), Image.NEAREST), (0, 0))
    im.paste(Image.fromarray(C).resize((w * k, h * k), Image.NEAREST), (w * k + 6, 0))
    d = ImageDraw.Draw(im); S = r["S"]
    f = lambda x, y: ((x * dpr - x0) * k, (y * dpr - y0) * k)
    d.rectangle([f(S["l"], S["t"]), f(S["r"], S["b"])], outline=(60, 140, 255))
    d.rectangle([f(ink[0], ink[1]), f(ink[2], ink[3])], outline=(255, 40, 40))
    cx, cy = f((S["l"] + S["r"]) / 2, (S["t"] + S["b"]) / 2)
    d.line([(cx, 0), (cx, h * k)], fill=(60, 140, 255)); d.line([(0, cy), (w * k, cy)], fill=(60, 140, 255))
    im.save(path)

def tol_for(c):
    # CENTER_TOL_SCALE=.6 asks for .3px (.6 for a wide shape): a tighter look for what a person can see but .5px lets through (384 r4:
    # every Settings icon leaned .38px right and the gate, at .5, passed them all)
    k = float(os.environ.get("CENTER_TOL_SCALE", "1"))
    if c.get("tol"): return k * c["tol"]            # (384.71) a candidate that asks for its own: the mode tiles' arrow discs, 0.3px
    return k * (1.0 if (c["S"]["r"] - c["S"]["l"]) > 120 else 0.5)

def batches(cands):
    out = []
    for c in sorted(cands, key=lambda c: -(c["S"]["r"] - c["S"]["l"]) * (c["S"]["b"] - c["S"]["t"])):
        S = c["S"]; M = 14
        for b in out:
            if all(S["r"] + M < o["S"]["l"] or o["S"]["r"] + M < S["l"] or S["b"] + M < o["S"]["t"] or o["S"]["b"] + M < S["t"] for o in b):
                b.append(c); break
        else: out.append([c])
    return out

def groups(cands, dpr):
    """Candidates in bands of the screen, each band one clip (a small screenshot is far quicker than the screen)."""
    out = []
    for c in sorted(cands, key=lambda c: c["S"]["t"]):
        S = c["S"]
        for gr in out:
            u = gr["u"]; nu = (min(u[0], S["l"]), min(u[1], S["t"]), max(u[2], S["r"]), max(u[3], S["b"]))
            if (nu[3] - nu[1]) <= 260 and (nu[2] - nu[0]) * (nu[3] - nu[1]) <= 1.6 * ((u[2] - u[0]) * (u[3] - u[1]) + (S["r"] - S["l"]) * (S["b"] - S["t"])) + 8000:
                gr["u"] = nu; gr["c"].append(c); break
        else: out.append({"u": (S["l"], S["t"], S["r"], S["b"]), "c": [c]})
    W, H = VIEW["w"] * dpr, VIEW["h"] * dpr
    for gr in out:
        u = gr["u"]
        # whole CSS pixels, so the clip lands on the device's pixel grid exactly
        gr["box"] = (max(0, int(math.floor(u[0])) - 1) * dpr, max(0, int(math.floor(u[1])) - 1) * dpr, min(int(W), (int(math.ceil(u[2])) + 1) * dpr), min(int(H), (int(math.ceil(u[3])) + 1) * dpr))
    return out

SETTLED = """()=>document.getAnimations().filter(a => { try { const t = a.effect && a.effect.getComputedTiming(); return a.playState === 'running' && t && isFinite(t.endTime); } catch (e) { return false; } }).length"""
def measure_step(pg, cdp, dpr, tag, rows, again=False, tries=2):
    # what is still coming in (a screen's entrance, a card rising) is waited for; only what never ends (a pulse, a
    # shimmer) is paused where it is - a layer stopped part way draws its words up to a pixel from where they rest
    for _ in range(12):
        if not pg.evaluate(SETTLED): break
        pg.wait_for_timeout(150)
    cdp.send("Animation.setPlaybackRate", {"playbackRate": 0})
    pg.evaluate("()=>{ __cz.freeze(); document.activeElement && document.activeElement.blur && document.activeElement.blur(); }")
    try:
        cands = pg.evaluate("(a)=>__cz.collect({again:a})", again)
        if not cands: return 0
        vv = pg.evaluate("()=>[visualViewport.pageLeft, visualViewport.pageTop]"); VIEW["x"], VIEW["y"] = vv
        got = []
        for gr in groups(cands, dpr):
            box = gr["box"]; A1 = grab(cdp, box); res = {}
            for b in batches(gr["c"]):
                ids = [c["id"] for c in b]
                B = None
                if any(c["mixed"] for c in b):
                    pg.evaluate("(ids)=>__cz.hide(ids,'t')", ids); B = grab(cdp, box); pg.evaluate("()=>__cz.restore()")
                pg.evaluate("(ids)=>__cz.hide(ids,'a')", ids); C = grab(cdp, box); pg.evaluate("()=>__cz.restore()")
                for c in b: res[c["id"]] = (B, C)
            A2 = grab(cdp, box)
            for c in gr["c"]:
                B, C = res[c["id"]]
                m = measure_cand(c, A1, A2, B, C, dpr, box[:2])
                for attempt in range(2):
                    if not (m and "unstable" in m): break
                    pg.wait_for_timeout(150)
                    a1 = grab(cdp, box); b = None
                    if c["mixed"]:
                        pg.evaluate("(ids)=>__cz.hide(ids,'t')", [c["id"]]); b = grab(cdp, box); pg.evaluate("()=>__cz.restore()")
                    pg.evaluate("(ids)=>__cz.hide(ids,'a')", [c["id"]]); cc = grab(cdp, box); pg.evaluate("()=>__cz.restore()")
                    m = measure_cand(c, a1, grab(cdp, box), b, cc, dpr, box[:2])
                got.append(dict(c, tag=tag, m=m))
        # anything that changed after it was read (a count that arrived, a card that finished coming in) is read again
        changed = set(pg.evaluate("(ids)=>__cz.changed(ids)", [c["id"] for c in cands])) if tries > 0 else set()
        rows.extend(r for r in got if r["id"] not in changed)
        pg.evaluate("(ids)=>__cz.done(ids)", [c["id"] for c in cands if c["id"] not in changed])
        if changed:
            pg.evaluate("()=>{ __cz.thaw(); }"); pg.wait_for_timeout(400); pg.evaluate("()=>{ __cz.freeze(); }")
            return len(cands) - len(changed) + measure_step(pg, cdp, dpr, tag, rows, again, tries - 1)
        return len(cands)
    finally:
        pg.evaluate("()=>__cz.thaw()")
        cdp.send("Animation.setPlaybackRate", {"playbackRate": 1})

SCROLLER = """()=>{ const se=document.scrollingElement; if(se.scrollHeight > innerHeight + 4) return {win:true, max: se.scrollHeight - innerHeight, h: innerHeight};
  let best=null; for(const el of document.querySelectorAll('body *')){ const cs=getComputedStyle(el); if(!/auto|scroll/.test(cs.overflowY)) continue;
    if(el.scrollHeight <= el.clientHeight + 4 || el.clientHeight < 120) continue; const r=el.getBoundingClientRect(); if(r.width < 100 || r.bottom < 0 || r.top > innerHeight) continue;
    if(!best || el.clientHeight*r.width > best.clientHeight*best.getBoundingClientRect().width) best=el; }
  if(!best) return null; best.setAttribute('data-czscroll','1'); return {win:false, max: best.scrollHeight - best.clientHeight, h: best.clientHeight}; }"""
def scroll_to(pg, sc, y):
    if sc["win"]: pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y)
    else: pg.evaluate("(y)=>{ const e=document.querySelector('[data-czscroll]'); if(e) e.scrollTo({top:y, behavior:'instant'}); }", y)

MAX_STEPS = 6
def measure_screen(pg, cdp, dpr, tag, rows, scroll=True):
    pg.evaluate("()=>__cz.reset()")
    n = measure_step(pg, cdp, dpr, tag, rows)
    if not scroll: return n
    sc = pg.evaluate(SCROLLER)
    if sc and sc["max"] > 8:
        y = 0; step = max(120, int(sc["h"] * .6))
        steps = 0
        while y < sc["max"] and steps < MAX_STEPS:
            steps += 1
            y = min(sc["max"], y + step); scroll_to(pg, sc, y); pg.wait_for_timeout(260)
            n += measure_step(pg, cdp, dpr, tag + "@" + str(y), rows)
        scroll_to(pg, sc, 0)
    return n

HELPERS = r"""(()=>{ if(window.__czs) return;
  const S = window.__czs = {
    base: null, bodyCls: null,
    mark(){ S.base = new Set([...document.body.children]); S.bodyCls = document.body.className; S.htmlCls = document.documentElement.className; },
    /* what a sheet, card, banner or tour put on the page goes, and the page's classes are put back */
    clear(){
      try{ if(typeof chatDockOpen !== 'undefined' && chatDockOpen) closeChatDock(); }catch(e){}
      document.querySelectorAll('#tour-overlay, #tour-tooltip, #tour-line, #tour-line-dot, .app-banner, .daily-alert, #updatebanner, .intro-popup, #intro-pop, #resume-offer').forEach(n=>n.remove());
      if(S.base) [...document.body.children].forEach(n => { if(!S.base.has(n) && !/^(SCRIPT|STYLE|LINK|TEMPLATE)$/.test(n.tagName) && n.id !== '__statusbar' && !/chatdock/.test(n.id + ' ' + n.className)) n.remove(); });
      if(S.bodyCls !== null){ document.body.className = S.bodyCls; document.documentElement.className = S.htmlCls; }
      document.body.style.overflow = ''; document.documentElement.style.overflow = '';
      window.scrollTo(0, 0);
    },
    unit(){ const t = topicsIn(QUESTIONS); return t[Math.min(6, t.length - 1)]; },
    run(){ const t = S.unit(); cfg.mode = 'drill'; cfg.units = [t]; cfg.source = 'all';
      beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0,3), null, null); },
    tap(sel){ const e = document.querySelector(sel); if(!e) throw new Error('no ' + sel); e.click(); return true; },
    banner(id, kind, msg, act){ const el = buildAppBanner(id, kind, msg, act, ()=>{}, ()=>{}); document.body.appendChild(el); placeTopBanner(el); el.classList.add('show'); el.style.transition = 'none'; }
  };
})()"""

def run():
    global URL
    srv, URL = g["serve"]()
    rows = []; errs_all = []; skipped = []
    with sync_playwright() as pw:
        for dev in DEVICES:
            # THE DEVICE'S OWN PIXEL RATIO, FOR REAL. With only the emulated ratio, Chromium lays out and rounds at CSS
            # pixels: a line of words and an <svg> are drawn at their box rounded to a whole CSS pixel (up to half a
            # pixel off) where a phone rounds to a device pixel (a third). Launched at the device's own scale, it
            # rounds as the phone does (measured on a test page: build 384's notes).
            br = pw.chromium.launch(executable_path=g["CHROME"], args=["--force-device-scale-factor=%s" % dev[3]])
            VIEW["cscale"] = 1   # (the capture is in device pixels already)
            for cls in CLASSES:
                ctx, pg, cdp, errs = open_page(br, dev, cls)
                pg.evaluate(HELPERS)
                pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(2200); pg.evaluate("()=>__czs.mark()")
                for sc in SCREENS:
                    name = sc["name"]
                    if ONLY and not ONLY.search(name): continue
                    if sc.get("cls") and sc["cls"] != cls: continue
                    if sc.get("touch") is not None and sc["touch"] != dev[6]: continue
                    t0 = time.time()
                    try:
                        pg.evaluate("()=>{" + sc["js"] + "}"); pg.wait_for_timeout(sc.get("wait", 1300))
                        if sc.get("ready") and not pg.evaluate("()=>!!(" + sc["ready"] + ")"):
                            raise Exception("not on screen: " + sc["ready"])
                    except Exception as e:
                        skipped.append("%s|%s|%s: %s" % (dev[0], cls, name, str(e).splitlines()[0][:140]))
                        if VERBOSE: print("  (could not open %s)" % skipped[-1], flush=True)
                        try: pg.evaluate("()=>__czs.clear()")
                        except Exception: pass
                        continue
                    tag = "%s|%s|%s" % (dev[0], cls, name)
                    n = measure_screen(pg, cdp, dev[3], tag, rows, sc.get("scroll", True))
                    if VERBOSE: print("  %-50s %3d measured %.1fs" % (tag, n, time.time() - t0), flush=True)
                    try:
                        if sc.get("after"): pg.evaluate("()=>{" + sc["after"] + "}")
                        if sc.get("clear", True): pg.evaluate("()=>__czs.clear()")
                    except Exception: pass
                errs_all += ["%s %s: %s" % (dev[0], cls, e) for e in errs]
                ctx.close()
            br.close()
    srv.shutdown()
    return rows, errs_all, skipped

# Every screen, sheet, card and banner, in both classes. "ready" must be true once it is open (or the screen is
# reported as not opened); "clear": False keeps the screen for the next entry (a test's question, then its answer).
CLR = "document.querySelectorAll('.cz-none').forEach(n=>n.remove());"
SCREENS = [
    # Home and what floats on it
    {"name": "home", "js": "showHome();", "wait": 2600, "ready": "document.querySelector('#stage .cosmic-hero, #nextbtn')"},
    {"name": "home/class list", "js": "showHome(); setTimeout(()=>document.querySelector('.class-bubble')?.click(), 600);", "wait": 1700, "ready": "document.querySelector('.class-bubble-wrap.is-open, .class-stack')"},
    {"name": "modes", "js": "showModeSelect();", "ready": "document.querySelector('#stage .modecard')"},
    {"name": "units", "js": "cfg.mode='drill'; cfg.units=[]; showSetup();", "ready": "document.querySelector('#stage .picks')"},
    {"name": "units/exam", "js": "cfg.mode='exam'; cfg.units=[]; showSetup();", "ready": "document.querySelector('#stage .picks')", "cls": "academy"},
    {"name": "units/game", "js": "cfg.mode='game'; cfg.units=[]; showSetup();", "ready": "document.querySelector('#stage .picks')"},
    {"name": "units/review", "js": "cfg.mode='review'; cfg.units=[]; showSetup();", "ready": "document.querySelector('#stage .picks')"},
    {"name": "units/picked", "js": "cfg.mode='drill'; cfg.units=[]; showSetup(); setTimeout(()=>{ const c=document.querySelector('.picks > label.pick input'); c && c.click(); }, 500);", "wait": 1500, "ready": "document.querySelector('#stage .picks')"},
    # a test: the question, an answer, the pause card, the results
    {"name": "test/question", "js": "__czs.run();", "wait": 4200, "ready": "document.body.classList.contains('has-active-question')", "clear": False},
    {"name": "test/answered", "js": "const c=[...document.querySelectorAll('#stage .choice, #stage .choices button, #stage label.choice')].find(e=>e.getBoundingClientRect().height>20); c && c.click();", "wait": 1600, "clear": False},
    {"name": "test/paused", "js": "__czs.tap('#pausebtn');", "wait": 1200, "ready": "document.querySelector('.pause-card, .paused, #paused, .screen-paused, [class*=pause]')", "clear": False},
    {"name": "results", "js": "try{ order.forEach(qi=>{ attempts[qi]=1; }); pos=order.length; summarize(); }catch(e){ throw e; }", "wait": 5200, "ready": "document.querySelector('#stage .rs-grade, #stage [class*=result]')"},
    {"name": "review", "js": "showAnswerReview([__czs.unit()], 'all');", "ready": "document.querySelector('#stage .ar-head, #stage [class*=review]')"},
    {"name": "test history", "js": "showTestReviewList();"},
    {"name": "flash cards", "js": "showFlashcards([__czs.unit()], 'all');", "ready": "document.querySelector('#stage .fc-face, #stage [class*=flash]')"},
    # Profile and what it opens
    {"name": "profile", "js": "showProfile('profile');", "ready": "document.querySelector('#stage .profile-hero')"},
    {"name": "stats", "js": "showProfile('stats');"},
    {"name": "customize", "js": "showCustomize();", "ready": "document.querySelector('#stage .cz-row')"},
    # (384 round 4) the four pages behind it
    {"name": "customize/character", "js": "showCustomize('character');", "wait": 1800, "ready": "document.querySelector('#stage .cz-page-character .avatarchar-option')"},
    {"name": "customize/banner", "js": "showCustomize('banner');", "wait": 1800, "ready": "document.querySelector('#stage .cz-page-banner .banner-opt')"},
    {"name": "customize/theme", "js": "showCustomize('theme');", "wait": 1500, "ready": "document.querySelector('#stage .cz-page-theme .swatch')"},
    {"name": "customize/effect", "js": "showCustomize('fx');", "wait": 1500, "ready": "document.querySelector('#stage .cz-page-fx .hfx-opt')"},
    {"name": "rank ladder", "js": "showRanksScreen('ranks');"},
    {"name": "badge case", "js": "showRanksScreen('badges');"},
    {"name": "friends", "js": "showFriends();"},
    # the Leaderboard, each board
    # (385) Fire Code has a Leaderboard too, with two boards (here without a cloud: the pill switcher, search and Find me are what is measured)
    {"name": "leaderboard", "js": "showRankings();", "ready": "document.querySelector('#stage .screen-rankings, .screen-rankings')"},
    {"name": "leaderboard/board 2", "js": "showRankings(); setTimeout(()=>{ const t=[...document.querySelectorAll('#stage [role=tab], #stage .lb-boardtab, #stage .navsegment button')]; t[1] && t[1].click(); }, 700);", "wait": 2000},
    {"name": "leaderboard/board 3", "js": "showRankings(); setTimeout(()=>{ const t=[...document.querySelectorAll('#stage [role=tab], #stage .lb-boardtab, #stage .navsegment button')]; t[2] && t[2].click(); }, 700);", "wait": 2000, "cls": "academy"},
    {"name": "leaderboard/this week", "js": "showRankings('week');", "wait": 1800, "cls": "academy"},
    {"name": "calendar", "js": "showCalendarTab();"},
    # Settings and every page
    {"name": "settings", "js": "showAppearance();", "ready": "document.querySelector('#stage .settings-card')"},
    {"name": "settings/sound", "js": "showAppearance({page:'sound'});"},
    {"name": "settings/study", "js": "showAppearance({page:'study'});"},
    {"name": "settings/motion", "js": "showAppearance({page:'motion'});"},
    {"name": "settings/sync", "js": "showAppearance({page:'sync'});"},
    {"name": "settings/share", "js": "showAppearance({page:'share'});"},
    {"name": "settings/rankings", "js": "showAppearance({page:'rankings'});"},
    # (385 r17) one switch per class under the master: both on, and the master off (every class greyed, in the off position)
    {"name": "settings/rankings, two classes", "js": "enrolledClasses = () => ['academy','ifc']; showAppearance({page:'rankings'});"},
    {"name": "settings/rankings, two classes, master off", "js": "enrolledClasses = () => ['academy','ifc']; showAppearance({page:'rankings'}); setTimeout(()=>{ document.querySelector('#stage .settings-card input[type=checkbox]').click(); }, 700);", "wait": 1800},
    {"name": "settings/account", "js": "showAppearance({page:'account'});"},
    {"name": "settings/advanced", "js": "showAdvancedSettings();"},
    {"name": "settings/credits", "js": "showCredits();"},
    {"name": "settings/terms", "js": "showSettingsText('terms');"},
    {"name": "settings/whats new list", "js": "showReleaseHistory();"},
    {"name": "settings/feedback", "js": "showBugReport();"},
    # classes
    {"name": "classes", "js": "showClassCatalog();"},
    {"name": "classes/enroll", "js": "showIfcEnroll();"},
    {"name": "classes/enroll confirm", "js": "showClassCatalog(); showClassEnrollConfirm('Fire Code', 'International Fire Code', ()=>{});", "wait": 1500},
    # the chat
    {"name": "chat", "js": "showHome(); chatDockTab='friends'; openChatDock();", "wait": 1500},
    {"name": "chat/groups", "js": "showHome(); chatDockTab='groups'; openChatDock(); setTimeout(()=>document.querySelector('.chatdock-tab[data-tab=groups]')?.click(), 300);", "wait": 1500},
    {"name": "chat/inbox", "js": "showHome(); chatDockTab='notifs'; openChatDock(); setTimeout(()=>document.querySelector('.chatdock-tab[data-tab=notifs]')?.click(), 300);", "wait": 1500},
    # the Virtual Room
    {"name": "virtual room", "js": "cfg.mode='vroom'; showVirtualRoomChoice();"},
    {"name": "virtual room/setup", "js": "cfg.mode='vroom'; showVirtualRoomSetup();"},
    {"name": "virtual room/rooms", "js": "cfg.mode='vroom'; showRoomBrowser();"},
    # sheets, cards, banners, toasts
    {"name": "sheet/save code", "js": "showHome(); showSaveCodeCard({ mode: 'settings' });", "wait": 1600},
    {"name": "sheet/sign out", "js": "showAppearance({page:'account'}); showSignOutConfirm();", "wait": 1500},
    {"name": "sheet/whats new", "js": "showHome(); showIntroPopup();", "wait": 1800},
    {"name": "sheet/add to home screen", "js": "showAppearance({page:'share'}); showHomeScreenSheet({ from: 'settings' });", "wait": 1800},
    {"name": "banner/friend", "js": "showHome(); __czs.banner('friend-request','friend','Alex wants to be friends','View');", "wait": 1500},
    {"name": "banner/save", "js": "showHome(); __czs.banner('save-code','account','Save your sync code','Save it');", "wait": 1500},
    {"name": "banner/join", "js": "showHome(); __czs.banner('lobby-invite','vroom','Alex invited you to a Virtual Room','Join');", "wait": 1500},
    {"name": "banner/accept", "js": "showHome(); __czs.banner('nova-challenge','vroom','Nova challenged you to a match','Accept');", "wait": 1500},
    {"name": "banner/update", "js": "showHome(); showUpdateBanner({build:'x'});", "wait": 1200},
    {"name": "banner/home screen", "js": "showHome(); showAddToHomeNotice();", "wait": 1200},
    {"name": "banner/re-add", "js": "showHome(); showFrameNotice({frameId:'x'});", "wait": 1200},
    {"name": "toast", "js": "showHome(); showToast('Saved', 'good');", "wait": 700},
    {"name": "tips", "js": "showHome(); startSimpleTour(mainMenuTourSteps(false), ()=>{});", "wait": 1500},
    # signed out: Get Started, Welcome, sign-in and the sign-up steps
    {"name": "signup/get started", "js": "store.onboardingComplete=false; showGetStarted();", "wait": 2600, "after": "store.onboardingComplete=true;"},
    {"name": "signup/welcome", "js": "store.onboardingComplete=false; showWelcome();", "wait": 1600, "after": "store.onboardingComplete=true;"},
    {"name": "signup/sign in", "js": "store.onboardingComplete=false; showWelcomeCodeEntry();", "wait": 1400, "after": "store.onboardingComplete=true;"},
    {"name": "signup/new here", "js": "store.onboardingComplete=false; showSignUpCheck();", "wait": 1400, "after": "store.onboardingComplete=true;"},
    {"name": "signup/class", "js": "store.onboardingComplete=false; showClassSelection();", "wait": 1400, "after": "store.onboardingComplete=true;"},
    {"name": "signup/class picked", "js": "store.onboardingComplete=false; showClassSelection(); setTimeout(()=>document.querySelector('.classselect-panel .class-card')?.click(), 500);", "wait": 1500, "after": "store.onboardingComplete=true;"},
]

def verdict(r):
    """Which axes are off, beyond the tolerance (0.5px; 1px for a shape over 120px wide)."""
    m = r.get("m")
    if not m or "dx" not in m: return []
    tol = tol_for(r); bad = []
    if r["hIntent"] and not m["edgeX"] and abs(m["dx"] - r.get("opticalDx", 0)) > tol: bad.append("x")   # (384) a round back chevron's centre is 3% left
    if r["vIntent"] and not m["edgeY"] and abs(m["dy"]) > tol: bad.append("y")
    return bad

def describe(r):
    m = r["m"]; parts = []
    if "x" in r["bad"]: dx = m["dx"] - r.get("opticalDx", 0); parts.append("%.2fpx %s" % (abs(dx), "right" if dx > 0 else "left") + (" of iOS's optical centre" if r.get("opticalDx") else ""))
    if "y" in r["bad"]: parts.append("%.2fpx %s" % (abs(m["dy"]), "low" if m["dy"] > 0 else "high"))
    return ", ".join(parts)

def children(combos):
    """Each device and class in its own process, JOBS at a time (they are independent pages)."""
    import tempfile
    base = [a for a in sys.argv[1:]]
    for flag in ("--sizes", "--class", "--json", "--jobs"):
        while flag in base: i = base.index(flag); del base[i:i + 2]
    base = [a for a in base if a not in ("--quick",)]
    pending = list(combos); running = []; rows = []; errs = []; skipped = []; ok = True
    while pending or running:
        while pending and len(running) < JOBS:
            dev, cls = pending.pop(0)
            out = tempfile.mktemp(suffix=".json", prefix="cz-")
            cmd = [sys.executable, os.path.abspath(__file__)] + base + ["--sizes", "^" + re.escape(dev[0]) + "$", "--class", cls, "--json", out, "--child"]
            running.append((subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True), out, dev[0], cls))
        time.sleep(.5)
        for p in running[:]:
            if p[0].poll() is None: continue
            running.remove(p); txt = p[0].stdout.read()
            if VERBOSE: print(txt, end="")
            try:
                d = json.load(open(p[1])); os.remove(p[1])
                rows += d["rows"]; errs += d["errs"]; skipped += d["skipped"]
            except Exception:
                ok = False; print("  %s / %s did not finish:\n%s" % (p[2], p[3], txt[-1500:]))
    return rows, errs, skipped, ok

if __name__ == "__main__":
    t0 = time.time()
    combos = [(d, c) for d in DEVICES for c in CLASSES]
    complete = True
    if len(combos) > 1 and JOBS > 1 and "--child" not in sys.argv:
        rows, errs, skipped, complete = children(combos)
    else:
        rows, errs, skipped = run()
    if "--child" in sys.argv:
        json.dump({"rows": [{k: v for k, v in r.items() if k != "_crop"} for r in rows], "errs": errs, "skipped": skipped}, open(arg("--json"), "w"), default=str)
        if SHOTS:
            for r in rows:
                if r.get("_crop") and (verdict(r) or VERBOSE):
                    os.makedirs(SHOTS, exist_ok=True)
                    save_crop(r, os.path.join(SHOTS, re.sub(r"[^\w.@-]+", "_", "%s_%s_%s" % (r["tag"], r["name"], r["txt"]))[:150] + ".png"))
        sys.exit(0)
    fails = []; owned = []
    for r in rows:
        r["bad"] = verdict(r)
        if r["bad"] and r.get("owned") and "--strict" not in sys.argv: owned.append(r); continue
        if r["bad"]: fails.append(r)
        if SHOTS and (r["bad"] or VERBOSE) and r.get("_crop"):
            os.makedirs(SHOTS, exist_ok=True)
            save_crop(r, os.path.join(SHOTS, re.sub(r"[^\w.@-]+", "_", "%s_%s_%s" % (r["tag"], r["name"], r["txt"]))[:150] + ".png"))
    measured = [r for r in rows if r.get("m") and "dx" in r["m"]]
    # (384.71) THE MODE TILES' ARROWS ARE MEASURED, and a run that never found them is a failure, not a pass: Choose your mode has four tiles in the academy and three in Fire Code,
    # the Virtual Room's Host / Join two in both - each tile's arrow disc is a candidate of its own (check-centering.js), held to 0.3px
    uncovered = []
    for scr, want in (("modes", {"academy": 4, "ifc": 3}), ("virtual room", {"academy": 2, "ifc": 2})):
        if ONLY and not ONLY.search(scr): continue
        for d in DEVICES:
            for cl in CLASSES:
                got = sum(1 for r in rows if r["name"].startswith("modecard::after") and [r["tag"].split("|")[0], r["tag"].split("|")[1], r["tag"].split("|")[2].split("@")[0]] == [d[0], cl, scr] and r.get("m") and "dx" in r["m"])
                if got < want[cl]: uncovered.append("%s / %s / %s: %d of %d arrows measured" % (d[0], cl, scr, got, want[cl]))
    if uncovered:
        complete = False
        print("\nMODE ARROWS NOT MEASURED:\n  " + "\n  ".join(uncovered))
    print("Centring by the ink: %d elements measured on %d screens (%s; %s)" % (
        len(measured), len({r["tag"].split("@")[0] for r in rows}), ", ".join(d[0] for d in DEVICES), " and ".join(CLASSES)))
    if fails:
        print("\nOFF CENTRE (tolerance 0.5px, 1px for a shape over 120px wide; + is right/low, - is left/high):")
        for r in sorted(fails, key=lambda r: (r["name"], r["tag"])):
            m = r["m"]
            print("  FAIL %-34s %-18s %4.0fx%-3.0f %-28s dx %+.2f dy %+.2f  on %s  [%s]" % (
                r["name"][:34], ("'" + r["txt"][:16] + "'") if r["txt"] else "(icon)", r["S"]["r"] - r["S"]["l"], r["S"]["b"] - r["S"]["t"],
                describe(r), m["dx"], m["dy"], r["tag"].replace("|", " / "), r.get("path", "")[:40]))
    if VERBOSE:
        for r in rows:
            if r in fails: continue
            m = r.get("m") or {}
            print("   ok  %-34s %-18s %s %s" % (r["name"][:34], r["txt"][:18], ("dx %+.2f dy %+.2f" % (m["dx"], m["dy"])) if "dx" in m else m, r["tag"]))
    if owned:
        print("\nOFF CENTRE BUT OWNED BY OTHER WORK (listed, not failed; --strict fails them):")
        for r in sorted(owned, key=lambda r: (r["name"], r["tag"])):
            print("  left %-34s %-18s %-28s on %s - %s" % (r["name"][:34], ("'" + r["txt"][:16] + "'") if r["txt"] else "(icon)", describe(r), r["tag"].replace("|", " / "), r["owned"]))
    moving = [r for r in rows if (r.get("m") or {}).get("unstable") is not None]
    if moving:
        print("\nMoving while measured, so not measured (%d):" % len(moving))
        for r in moving: print("    %-34s %-18s on %s" % (r["name"][:34], r["txt"][:18], r["tag"].replace("|", " / ")))
    if skipped:
        print("\nNot opened (%d):" % len(skipped))
        for k in skipped: print("   ", k)
    if errs: print("\npage errors:", errs[:6])
    if arg("--json"): json.dump([{k: v for k, v in r.items() if k != "_crop"} for r in rows], open(arg("--json"), "w"), default=str)
    print("\n%s - %d off centre, %.0fs" % ("ALL PASS" if not fails and complete else "FAILED", len(fails), time.time() - t0))
    sys.exit(1 if fails or not complete else 0)
