#!/usr/bin/env python3
"""Build 384 r17 check: the launch handover - the splash covers the whole screen from its first frame and its word never moves.

Madison, a screen recording of opening the installed app on his iPhone 17 Pro Max after an iOS update: "the splash screen glitches
sometimes and it's not smooth. This is vital." Frame by frame (20fps): the startup image, then the page's FIRST frame - the splash 62pt
short (a strip of the app's own glow and stars showing under it) with NOVA and the bar at the middle of that short box - then, one frame
later, the box whole and the word 62pt higher; and for the rest of the splash the word 88pt above the screen's middle.

Chromium cannot reproduce an iOS launch, so this models the part of it the page can be held to: a viewport that STARTS shorter than the
final one (short by the bottom inset, the top inset, or both; the width unchanged) and grows to its final size a moment after the splash
is first in the page, with the screen (screen.width/height) fixed - which is what an installed iOS app's screen is - in an installed
app (navigator.standalone) and in a browser tab, at 100% and at his 85% page zoom (518 css px wide on a 440pt screen), phone and iPad,
portrait and landscape. Every animation frame from the start of the document is recorded from inside the page, and a screencast of what
was really painted is read pixel by pixel. For every frame:

  1. COVER   the splash's box covers the whole FINAL viewport (not the viewport of that moment), in every frame it exists - so no
             strip of anything else shows round it however short the first frame's viewport is;
  2. STILL   once the word is visible (opacity over .02) it is at the same place in every frame (it must not move after its first
             painted frame), and that place is the middle of the screen (the installed app: of the whole screen; a tab: of the viewport);
  3. DARK    the page's own background colour is the splash's #0A0A0A in every frame, <html>'s inline background is still there while
             the splash is up (a browser tab: it is what Safari's bands show), and no painted frame is lighter than the splash's own
             dark (a light flash would be one whole-screen frame; the word is a few percent of the screen);
  4. QUIET   nothing writes the viewport meta, and nothing but the head's own replay writes theme-color, while the splash is up in an
             installed app (a rewritten viewport is a resized one);
  5. FIRST   the splash's markup is in the document BEFORE the 2.9MB stylesheet, so a first paint does not wait for the stylesheet.

Not reproducible here, and said so: what the web view paints before the page's first frame (it is outside the page), iOS's real
safe areas and its real viewport timing. The model is the invariants, which hold whatever the timing is.

  python3 tools/check-b384-launchframe.py [--quick] [--against OLD/index.html]   (must FAIL on the build before)
"""
import argparse, io, json, os, re, shutil, socket, sys, tempfile, threading, functools, http.server, base64
from PIL import Image
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true")
ap.add_argument("--against", default=None)
ap.add_argument("--only", default="")
args = ap.parse_args()

STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){},
       addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""

# every animation frame from the first one the document has, from inside the page; and every write to the two meta tags
RECORDER = """
(() => {
  window.__rec = []; window.__metaWrites = []; const t0 = performance.now();
  try{
    const sa = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(n, v){
      try{ if(this.id === 'viewportmeta' && n === 'content') window.__metaWrites.push(['viewport', performance.now() - t0, String(v)]); }catch(e){}
      return sa.call(this, n, v);
    };
    const d = Object.getOwnPropertyDescriptor(HTMLMetaElement.prototype, 'content');
    if(d && d.set) Object.defineProperty(HTMLMetaElement.prototype, 'content', { configurable: true, get: d.get, set: function(v){
      try{ if(this.id === 'themecolor') window.__metaWrites.push(['theme', performance.now() - t0, String(v)]); }catch(e){}
      return d.set.call(this, v);
    }});
  }catch(e){}
  /* sampled on every animation frame AND on a 10ms timer: a launch's main thread is blocked for seconds by the page's own parse and
     script, and a timer's turn between two of its tasks is the state a frame would paint - an animation frame alone would see none of it */
  function sample(){
    const de = document.documentElement, sp = document.getElementById('splashscreen'), g = document.getElementById('splash-group');
    const f = { t: performance.now() - t0, wall: Date.now(), iw: innerWidth, ih: innerHeight, hbg: de ? de.style.backgroundColor : null,
                hcs: de ? getComputedStyle(de).backgroundColor : null, sp: null, g: null, op: 0, hide: false };
    if(sp){ const r = sp.getBoundingClientRect(); f.sp = [r.left, r.top, r.right, r.bottom]; f.hide = sp.classList.contains('splash-hide'); }
    if(g){ const r = g.getBoundingClientRect(); f.g = [(r.left + r.right) / 2, (r.top + r.bottom) / 2, r.width, r.height]; { const cs = getComputedStyle(g); f.op = cs.visibility === 'hidden' ? 0 : parseFloat(cs.opacity); } }
    window.__rec.push(f);
  }
  try{
    const ca = DOMTokenList.prototype.add;
    DOMTokenList.prototype.add = function(){ try{ if(!window.__hideAt && [].indexOf.call(arguments, 'splash-hide') >= 0){ window.__hideAt = performance.now() - t0; window.__hideWall = Date.now(); } }catch(e){} return ca.apply(this, arguments); };
  }catch(e){}
  if(window.parent !== window){
    /* inside the host's <iframe>: the moment the splash's group is in the page (a microtask after the parser's task that made it, before any
       layout of its own) is the page's first frame - sample it at the short size, then let the host grow the viewport */
    new MutationObserver((ms, o) => { if(document.getElementById('splash-group')){ o.disconnect(); sample(); try{ window.parent.__grow(); }catch(e){} } })
      .observe(document, { childList: true, subtree: true });
  }
  (function rec(){ sample(); if(window.__rec.length < 900) requestAnimationFrame(rec); })();
  const iv = setInterval(() => { sample(); if(window.__rec.length >= 900) clearInterval(iv); }, 10);
})();
"""

ph = {"top": 62, "bottom": 34}      # an iPhone 17 Pro Max's insets, in points
UA_PHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_PAD = "Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
# name, screen (points, as the device reports it), page scale (css px per point: 1 at 100%, 518/440 at his 85%), ua, insets (top, bottom)
DEV = [
    ("iPhone 17 Pro Max 100%", (440, 956), 1.0, UA_PHONE, (62, 34)),
    ("iPhone 17 Pro Max 85% page zoom", (440, 956), 518 / 440, UA_PHONE, (62, 34)),
    ("iPhone SE (3rd gen)", (375, 667), 1.0, UA_PHONE, (20, 0)),
    ("iPhone 16e", (390, 844), 1.0, UA_PHONE, (47, 34)),
    ("iPad Pro 11in portrait", (834, 1194), 1.0, UA_PAD, (24, 20)),
    ("iPad Pro 11in landscape", (1194, 834), 1.0, UA_PAD, (24, 20)),
]
SHORT = [("short by the bottom inset", "b"), ("short by the top inset", "t"), ("short by both insets", "tb"), ("not short (control)", "")]
QUICK = {("iPhone 17 Pro Max 100%", True), ("iPhone 17 Pro Max 85% page zoom", True), ("iPhone 17 Pro Max 100%", False), ("iPad Pro 11in landscape", True)}

seed = None
with open(os.path.join(HERE, "record-cutscenes.py")) as fh:
    src = fh.read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
seed = dict(rc["SEED"]); seed["seenClassTip"] = True

ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:420], flush=True)

SRC = args.against or os.path.join(ROOT, "index.html")
TMP = tempfile.mkdtemp(prefix="launchframe-")
for d in ("launch", "share", "ifc"):
    if os.path.isdir(os.path.join(ROOT, d)):
        os.symlink(os.path.join(ROOT, d), os.path.join(TMP, d))
RAW = io.open(SRC, encoding="utf-8").read()
def page_for(insets):
    t, b = insets
    name = "i_%d_%d.html" % (t, b)
    if not os.path.exists(os.path.join(TMP, name)):
        v = {"top": "%dpx" % t, "right": "0px", "bottom": "%dpx" % b, "left": "0px"}
        io.open(os.path.join(TMP, name), "w", encoding="utf-8").write(INSET_RE.sub(lambda m: v[m.group(1)], RAW))
    return name

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=TMP))
threading.Thread(target=srv.serve_forever, daemon=True).start()

def luma_frac(png_b64, floor=60):
    im = Image.open(io.BytesIO(base64.b64decode(png_b64))).convert("L")
    im = im.resize((max(1, im.width // 4), max(1, im.height // 4)))
    px = list(im.get_flattened_data()) if hasattr(im, 'get_flattened_data') else list(im.getdata()); n = len(px)
    return sum(1 for v in px if v > floor) / float(n), max(px)

def run_case(br, dev, installed, short, late=False):
    name, (sw, sh), r, ua, (it, ib) = dev
    portrait = sw < sh or (name.endswith("portrait"))
    # the final viewport, in css px: the whole screen at the page's scale
    fw, fh = round(sw * r), round(sh * r)
    dy = (ib if "b" in short else 0) + (it if "t" in short else 0)
    h0 = fh - round(dy * r)
    # The page runs in an <iframe> that the host page grows from h0 to fh in the very frame the splash's group first exists (or 110ms
    # later: `late`). A real viewport resize, applied by the engine at the next frame like iOS's, and landing at the same point of the
    # page's own life on every run - which a resize sent from outside, over a loaded machine, cannot promise.
    host = "host_%d.html" % (abs(hash((name, installed, short, late))) % 10**8)
    io.open(os.path.join(TMP, host), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<body style="margin:0;background:#0A0A0A;overflow:hidden"><iframe id="f" src="%s" style="border:0;display:block;width:%dpx;height:%dpx"></iframe>'
        '<script>(function(){ var f = document.getElementById("f"); window.__grow = function(){'
        ' if(%d) setTimeout(function(){ f.style.height = "%dpx"; }, 110); else f.style.height = "%dpx"; }; })();</script>'
        % (page_for((it, ib)), fw, h0, 1 if late else 0, fh, fh))
    ctx = br.new_context(viewport={"width": fw, "height": fh}, screen={"width": sw, "height": sh}, device_scale_factor=3 * (1 / r),
                         is_mobile=True, has_touch=True, user_agent=ua)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    if os.environ.get("LF_DEBUG"): pg.on("framenavigated", lambda f: print("  nav", f.url[-30:], flush=True)); pg.on("console", lambda m: print("  console", m.text[:100], flush=True))
    if installed: ctx.add_init_script(STANDALONE)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.a2hs','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
                        "localStorage.setItem('class26e.intro.seen','99');localStorage.setItem('class26e.statusbar.v1','#271E23');localStorage.setItem('class26e.drill.v1',%s)}catch(e){}" % json.dumps(json.dumps(seed)))
    ctx.add_init_script(RECORDER)
    pg.route("**/version.json", lambda rt, q: rt.abort())
    cdp = ctx.new_cdp_session(pg); shots = []
    cdp.on("Page.screencastFrame", lambda e: (shots.append((e["metadata"].get("timestamp", 0), e["data"])), cdp.send("Page.screencastFrameAck", {"sessionId": e["sessionId"]})))
    cdp.send("Page.startScreencast", {"format": "png", "everyNthFrame": 1})
    pg.goto("http://127.0.0.1:%d/%s" % (PORT, host), wait_until="commit")
    fr = None
    for _ in range(600):
        kids = [x for x in pg.frames if x != pg.main_frame]
        if kids:
            fr = kids[0]
            try:
                if fr.evaluate("()=>!!document.getElementById('splash-group')"): break
            except Exception: pass
        pg.wait_for_timeout(15)
    if fr is None:
        chk("%s: the page loaded in its frame" % name, False); ctx.close(); return
    # the order of the document is read now, while the splash is still in it
    order = fr.evaluate("""()=>{ const sp = document.getElementById('splashscreen'); if(!sp) return null;
      const m = [...document.querySelectorAll('style')].find(s => s.textContent.indexOf('--ink:#121A20') >= 0);
      return m ? !!(sp.compareDocumentPosition(m) & Node.DOCUMENT_POSITION_FOLLOWING) : null; }""")
    pg.wait_for_timeout(900)
    # the splash's own life: what is read below is everything up to the moment it starts to fade (then Home is on show, lighter by design)
    for _ in range(120):
        try:
            if fr.evaluate("()=>{ const s = document.getElementById('splashscreen'); return !s || s.classList.contains('splash-hide'); }"): break
        except Exception: break
        pg.wait_for_timeout(40)
    try: cdp.send("Page.stopScreencast")
    except Exception: pass
    rec = fr.evaluate("()=>window.__rec"); writes = fr.evaluate("()=>window.__metaWrites"); hide_at = fr.evaluate("()=>window.__hideAt || null"); hide_wall0 = fr.evaluate("()=>window.__hideWall || null")
    if os.environ.get("LF_DEBUG"): print("DEBUG", fr.url[-30:], len(rec), [(round(f["t"]), bool(f["sp"]), f["hide"], round(f["op"], 2), f["ih"]) for f in rec[:3] + rec[-4:]], flush=True)
    ctx.close()
    tag = "%s, %s, %s%s" % (name, "installed" if installed else "browser tab", ("starts " + short_name(short)) if short else "no transient", ", grows late" if late else "")
    rec.sort(key=lambda f: f["t"])
    live = [f for f in rec if f["sp"] and not f["hide"]]
    chk("%s: the splash was recorded (%d frames)" % (tag, len(live)), len(live) >= 4, len(rec))
    if len(live) < 4: return
    # 1. COVER
    bad = [(round(f["t"]), [round(v) for v in f["sp"]], f["ih"]) for f in live if not (f["sp"][0] <= 0.5 and f["sp"][1] <= 0.5 and f["sp"][2] >= fw - 0.5 and f["sp"][3] >= fh - 0.5)]
    first = live[0]
    chk("%s: the splash covers the whole final viewport %dx%d in every frame (first frame: its box %s in a viewport %d tall)" %
        (tag, fw, fh, [round(v) for v in first["sp"]], first["ih"]), not bad, bad[:3])
    # 2. STILL
    vis = [f for f in rec if f["g"] and f["op"] > 0.02 and not f["hide"]]
    chk("%s: the word is shown (%d frames)" % (tag, len(vis)), len(vis) >= 2, len(rec))
    if len(vis) >= 2:
        ys = [f["g"][1] for f in vis]; xs = [f["g"][0] for f in vis]
        chk("%s: the word does not move after its first painted frame (y %.1f..%.1f, x %.1f..%.1f)" % (tag, min(ys), max(ys), min(xs), max(xs)),
            max(ys) - min(ys) <= 1.0 and max(xs) - min(xs) <= 1.0, [round(y) for y in ys][:12])
        mid = fh / 2.0
        chk("%s: ... and rests at the middle of the %s (%.1f from it)" % (tag, "screen" if installed else "viewport", ys[-1] - mid),
            abs(ys[-1] - mid) <= 3 and abs(xs[-1] - fw / 2.0) <= 3, (ys[-1], mid))
    # 3. DARK
    flat = [f for f in live if f["hcs"] != "rgb(10, 10, 10)"]
    chk("%s: <html>'s own background is the splash's #0A0A0A in every frame" % tag, not flat, [(round(f["t"]), f["hcs"]) for f in flat[:3]])
    cleared = [f for f in live if f["hbg"] not in ("rgb(10, 10, 10)", "#0a0a0a", "#0A0A0A")]
    chk("%s: ... and its inline background is still there while the splash is up" % tag, not cleared, [(round(f["t"]), f["hbg"]) for f in cleared[:3]])
    worst = (0, 0); light = None
    hide_wall = (hide_wall0 or next((f["wall"] for f in rec if f["hide"]), 1e18)) / 1000.0
    shots = [d for (ts, d) in shots if ts <= hide_wall - 0.08]       # what was painted before the splash began to fade
    lead = 0                                            # the frames before the page's first paint are the blank page it replaced
    while lead < len(shots) and luma_frac(shots[lead])[0] > 0.9: lead += 1
    for i, d in enumerate(shots[lead:lead + 60]):
        frac, mx = luma_frac(d)
        if frac > worst[0]: worst = (frac, mx)
        if frac > 0.10 and light is None: light = (i, round(frac, 2))
    chk("%s: no painted frame is lighter than the splash's dark (%d frames read; the most light: %.1f%% of the screen)" % (tag, min(60, len(shots) - lead), worst[0] * 100),
        light is None and len(shots) - lead >= 3, light)
    # 4. QUIET
    vw = [w for w in writes if w[0] == "viewport"]
    chk("%s: nothing writes the viewport meta while the splash is up" % tag, not vw, vw[:3])
    if installed:
        tw = [w for w in writes if w[0] == "theme" and first["t"] < w[1] < (hide_at or 1e12)]
        chk("%s: nothing rewrites theme-color while the splash is up" % tag, not tw, tw[:3])
    # 5. FIRST
    chk("%s: the splash's markup comes before the stylesheet in the document" % tag, order is True, order)
    chk("%s: no page errors" % tag, not errs, errs[:2])

def short_name(code):
    return {"b": "short by the bottom inset", "t": "short by the top inset", "tb": "short by both insets"}.get(code, code)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    for dev in DEV:
        for installed in (True, False):
            if args.only and args.only.lower() not in dev[0].lower(): continue
            if args.quick and (dev[0], installed) not in QUICK: continue
            if not installed and dev[4][1] == 0 and "SE" in dev[0]: continue
            for label, code in SHORT:
                if args.quick and code not in ("b", "tb"): continue
                for late in ((False, True) if installed and code else (False,)):
                    try:
                        run_case(br, dev, installed, code, late)
                    except Exception as e:
                        chk("%s %s %s: ran" % (dev[0], installed, code), False, repr(e))
    br.close()
srv.shutdown()
shutil.rmtree(TMP, ignore_errors=True)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
