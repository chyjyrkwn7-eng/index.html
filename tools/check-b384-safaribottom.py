#!/usr/bin/env python3
"""Build 384 (round 18): Safari in a tab - no hard edge at the top or the bottom of the page, and a calm tab bar.

Madison, with two screenshots (Get Started and Welcome in a Safari tab, iPhone 17 Pro Max, iOS 26): "The bottom of the screen
while in safari, it's still not properly displaying. The bottom tab is a little laggy." / "PLEASE FIX SAFARI". In both the page
stops at a hard horizontal line a little above Safari's floating toolbar (the Get Started phone mock-up is sliced there, Welcome's
glow ends in it) and below it, behind the toolbar, is one flat colour; at the top there is the same line where the page starts
under the status bar.

What the page can see of Safari 26 (measured off his frames and off share/edge-test.html in 382): fixed layers stop at its bars;
the root element's own background is what shows behind them (a flat colour wherever the root has no image: --band). So the page
cannot paint UNDER the bars, but it can make the line vanish: every row of the page's own edge must be the root's flat colour
(or the content must dissolve into it), so that wherever Safari stops the page, what it shows beyond is the same colour.

MODEL (Chromium cannot reproduce Safari's bars; this is the repo's own model - check-b384-browsers' "tab" and the sweep's
CHROME_H - plus Safari's rule above): the page runs in the viewport BETWEEN the bars (top = status bar, bottom = floating
toolbar, no insets); the screenshot is put on a full-screen canvas whose strips behind the bars are the root's flat computed
background colour. Per device and screen:
  seam    - top: the first rows of the page against the strip above them; bottom: the last rows against the strip below. In
            every 8px-wide column (median of its rows, so a star is not a seam) the step is at most SEAM_MAX levels, and no
            column of the page's last 4 rows is a hard-lit slice of content (Get Started's mock-up).
  scroll  - Get Started scrolled to its end: its last content ends clear of the bottom (nothing is hidden by the toolbar).
  bar     - the tab bar (Home) does not move when the toolbar collapses (the viewport grows by the toolbar's height): its
            distance from the viewport's bottom is the same, and no handler writes layout per scroll event (counted).
Run:  python3 tools/check-b384-safaribottom.py [seam scroll bar] [--root DIR] [--shots DIR]
      --root /tmp/old (a tree with the build before: git archive af5725d index.html version.json share launch | tar -x -C /tmp/old) must FAIL."""
import functools, http.server, io, json, os, re, socket, sys, threading, time
from playwright.sync_api import sync_playwright
from PIL import Image

args = sys.argv[1:]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = None
if "--root" in args:
    i = args.index("--root"); ROOT = os.path.abspath(args[i + 1]); del args[i:i + 2]
if "--shots" in args:
    i = args.index("--shots"); SHOTS = os.path.abspath(args[i + 1]); del args[i:i + 2]; os.makedirs(SHOTS, exist_ok=True)
ONLY = None
if "--only" in args:
    i = args.index("--only"); ONLY = args[i + 1]; del args[i:i + 2]
want = args or ["seam", "scroll", "noscroll", "govern", "bar"]
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SEAM_MAX = 3.0   # levels (0-255 luminance) between the page's edge and what Safari shows beyond it
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 "
      "Safari/604.1")
UA_IPAD = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15")
TOUCH_POINTS = "Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5,configurable:true});"
SEED = json.dumps({"firstName": "Casey", "avatarChar": "ninja", "onboardingComplete": True, "leaderboardOptIn": True,
    "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
    "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "seenHomeTour": True,
    "seenSettingsTour": True, "seenRewardsTour": True, "seenLadderTour": True, "novaMet": 99, "publicId": "pubtest00384",
    "lifetime": {"points": 12400, "answered": 5400, "correct": 4980, "drillPlays": 64, "examPlays": 22, "gamePlays": 9,
                 "perfectTests": 141, "currentStreak": 23, "longestStreak": 57}})
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked',"
        "'class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.a2hs','1790500000000'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1');")
INIT = ("(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s);"
        " localStorage.setItem('class26e.synccode','TEST-0384'); %s })()") % (json.dumps(SEED), SEEN)
CLEAR = ("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click());"
         " document.querySelectorAll('.rs-spot,.unlock-card,.intro-pop').forEach(n=>n.remove()); document.body.classList.remove('cutscene-focus'); }")

# name, screen pt (w, h), status bar pt, toolbar pt (what Safari keeps outside the page), iPad?
DEVICES = [
    ("iPhone 17 Pro Max", (440, 956), 62, 97, False),
    ("iPhone 16", (393, 852), 59, 97, False),
    ("iPhone SE", (375, 667), 20, 72, False),
    ("iPad Pro 11", (834, 1194), 74, 0, True),
]
if ONLY: DEVICES = [d for d in DEVICES if ONLY.lower() in d[0].lower()] or DEVICES
SCREENS = [("Welcome", "showWelcome()"), ("Home", "showHome()"), ("Get Started", "showGetStarted()")]

ok = True
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else ("-> " + str(info)[:500]))

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    http.server.ThreadingHTTPServer.handle_error = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port
srv, URL = serve()

def lum(p): return .2126 * p[0] + .7152 * p[1] + .0722 * p[2]
def parse_rgb(s):
    m = re.findall(r"[\d.]+", s)
    return tuple(float(x) for x in m[:3])

def open_page(br, dev, extra_h=0, lvh=0):
    name, (sw, sh), top, bot, ipad = dev
    vh = sh - top - bot + extra_h
    ctx = br.new_context(viewport={"width": sw, "height": vh}, screen={"width": sw, "height": sh}, user_agent=UA_IPAD if ipad else UA,
                         has_touch=True, is_mobile=True, device_scale_factor=2)
    ctx.add_init_script(INIT)
    if ipad: ctx.add_init_script(TOUCH_POINTS)
    pg = ctx.new_page()
    if lvh:   # Chromium's lvh is its dvh; Safari's is taller by what its toolbar gives up when it minimises (~47pt measured at 383)
        src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read().replace("100lvh", "calc(100dvh + %dpx)" % lvh)
        pg.route("**/index.html", lambda route, request, b=src: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.errs = []; pg.on("pageerror", lambda e: pg.errs.append(str(e)[:160]))
    pg.goto(URL); pg.wait_for_timeout(2500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.add_style_tag(content=".intro-pop, .rs-spot, .unlock-card{ display:none !important; }")   # a pop-up's dim is not the page being measured
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} }")
    return ctx, pg, vh

def screen_on(pg, call):
    pg.evaluate("()=>{ %s; }" % call); pg.wait_for_timeout(1500)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(150)
    pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(500)

STRIP_JS = """(y)=>{ const root = document.documentElement; let e = document.elementFromPoint(innerWidth / 2, y < 0 ? innerHeight + y : y);
  const clear = c => { const m = c.match(/rgba?\\(([^)]*)\\)/); if(!m) return true; const p = m[1].split(','); return p.length > 3 && parseFloat(p[3]) < .95; };
  /* Safari 26 tints a bar from a SOLID FIXED element at that edge (337), else from the root's own colour */
  while(e && e !== root){ const s = getComputedStyle(e);
    if(s.position === 'fixed' && !clear(s.backgroundColor) && e.getBoundingClientRect().width >= innerWidth - 1) return s.backgroundColor;
    e = e.parentElement; }
  return getComputedStyle(root).backgroundColor; }"""
def strips(pg):
    return parse_rgb(pg.evaluate(STRIP_JS, 1)), parse_rgb(pg.evaluate(STRIP_JS, -2))

def composite(png, vh, top, bot, strip_t, strip_b, scale=2):
    """the page's screenshot on the full screen: the strips behind Safari's bars are the flat colour Safari fills them with"""
    pg = Image.open(io.BytesIO(png)).convert("RGB")
    w = pg.width
    full = Image.new("RGB", (w, pg.height + (top + bot) * scale), tuple(int(round(c)) for c in strip_b))
    full.paste(Image.new("RGB", (w, top * scale), tuple(int(round(c)) for c in strip_t)), (0, 0))
    full.paste(pg, (0, top * scale))
    return full, pg

def column_steps(img, y_in, y_out, rows=2, col=16):
    """per column chunk (median over its rows and pixels) the luminance step between `rows` rows inside the page and the strip row(s) outside"""
    out = []
    for x0 in range(0, img.width - col + 1, col):
        def med(y0, n):
            vals = sorted(lum(img.getpixel((x, y))) for y in range(y0, y0 + n) for x in range(x0, x0 + col, 2))
            return vals[len(vals) // 2]
        out.append(abs(med(y_in, rows) - med(y_out, rows)))
    return out

def seams(pg_shot, strip_t, strip_b, scale=2):
    """-> (worst top seam, worst bottom seam) in levels, between the page's edge rows and the flat strip beyond"""
    h = pg_shot.height
    def edge(y0, n, s):
        res = []
        for x0 in range(0, pg_shot.width - 16 + 1, 16):
            vals = sorted(lum(pg_shot.getpixel((x, y))) for y in range(y0, y0 + n) for x in range(x0, x0 + 16, 2))
            res.append(abs(vals[len(vals) // 2] - s))
        return res
    return max(edge(0, 2 * scale, lum(strip_t))), max(edge(h - 2 * scale, 2 * scale, lum(strip_b)))

def seam(pw):
    br = pw.chromium.launch(executable_path=CHROME)
    for dev in DEVICES:
        name, (sw, sh), top, bot, ipad = dev
        ctx, pg, vh = open_page(br, dev)
        for sname, call in SCREENS:
            if ipad and sname == "Get Started": pass
            screen_on(pg, call)
            strip_t, strip_b = strips(pg)
            png = pg.screenshot()
            full, page = composite(png, vh, top, bot, strip_t, strip_b)
            st, sb = seams(page, strip_t, strip_b)
            tag = "%s, Safari tab (%dx%d, bars %d/%d), %s" % (name, sw, vh, top, bot, sname)
            if SHOTS:
                full.crop((0, 0, full.width, full.height)).save(os.path.join(SHOTS, "%s-%s.png" % (name.replace(" ", "_"), sname.replace(" ", "_"))))
            if top:
                chk(tag + ": no hard edge under the status bar (worst column step %.1f <= %.1f)" % (st, SEAM_MAX), st <= SEAM_MAX, st)
            if bot:
                chk(tag + ": no hard edge over the toolbar (worst column step %.1f <= %.1f)" % (sb, SEAM_MAX), sb <= SEAM_MAX, sb)
        # Get Started is a page that scrolls inside the fixed layer: its content crosses the bottom edge (the phone mock-up was sliced
        # there). Every stop of a slow scroll down it is held to the same rule.
        screen_on(pg, "showGetStarted()")
        worst = (0, 0); worst_t = (0, 0)
        for i in range(1, 11):
            pg.evaluate("(f)=>{ const s = document.querySelector('.gs-scroll'); s.scrollTo({top: (s.scrollHeight - s.clientHeight) * f, behavior:'instant'}); }", i / 10)
            pg.wait_for_timeout(260)
            strip_t, strip_b = strips(pg)
            full, page = composite(pg.screenshot(), vh, top, bot, strip_t, strip_b)
            st, sb = seams(page, strip_t, strip_b)
            if sb > worst[0]: worst = (sb, i)
            if st > worst_t[0]: worst_t = (st, i)
            if SHOTS and i in (4, 6, 8): full.save(os.path.join(SHOTS, "%s-Get_Started-scrolled-%d.png" % (name.replace(" ", "_"), i)))
        tag = "%s, Safari tab (%dx%d), Get Started scrolled through" % (name, sw, vh)
        if bot:
            chk(tag + ": at no stop does content end in a hard edge over the toolbar (worst %.1f at stop %d <= %.1f)" % (worst[0], worst[1], SEAM_MAX), worst[0] <= SEAM_MAX, worst)
        if top:
            chk(tag + ": ...nor under the status bar (worst %.1f at stop %d <= %.1f)" % (worst_t[0], worst_t[1], SEAM_MAX), worst_t[0] <= SEAM_MAX, worst_t)
        real = [x for x in pg.errs if not any(k in x for k in ("firebase", "firestore", "gstatic", "Failed to fetch", "net::"))]
        chk("%s: no page errors" % name, not real, real[:3])
        ctx.close()
    br.close()

def scroll(pw):
    br = pw.chromium.launch(executable_path=CHROME)
    for dev in DEVICES[:3]:
        name, (sw, sh), top, bot, ipad = dev
        ctx, pg, vh = open_page(br, dev)
        screen_on(pg, "showGetStarted()")
        pg.evaluate("()=>{ const s = document.querySelector('.gs-scroll'); s && s.scrollTo({top: s.scrollHeight, behavior:'instant'}); }"); pg.wait_for_timeout(1800)
        r = pg.evaluate("""()=>{ const s = document.querySelector('.gs-scroll'); if(!s) return null;
          const kids = [...s.querySelectorAll('*')].filter(e => e.getBoundingClientRect().height > 0 && getComputedStyle(e).position !== 'absolute');
          const last = kids.reduce((a, e) => e.getBoundingClientRect().bottom > a ? e.getBoundingClientRect().bottom : a, 0);
          return { last: Math.round(last), vh: innerHeight, scrollable: s.scrollHeight > s.clientHeight, atEnd: s.scrollTop + s.clientHeight >= s.scrollHeight - 2 }; }""")
        tag = "%s, Safari tab, Get Started" % name
        chk(tag + ": scrolled to its end, its last content ends inside the page (%s)" % r, r and r["atEnd"] and r["last"] <= r["vh"] + .5, r)
        ctx.close()
    br.close()

def noscroll(pw):
    br = pw.chromium.launch(executable_path=CHROME)
    for dev in DEVICES[:3]:
        name, (sw, sh), top, bot, ipad = dev
        ctx, pg, vh = open_page(br, dev, lvh=47)
        for sname, call in (("Welcome", "showWelcome()"), ("Home", "showHome()")):
            screen_on(pg, call)
            r = pg.evaluate("[document.scrollingElement.scrollHeight, innerHeight]")
            chk("%s, Safari tab (%dx%d, its 100lvh 47px taller than the page's viewport), %s: a screen that fits does not scroll (document %d, viewport %d)" % (name, sw, vh, sname, r[0], r[1]),
                r[0] <= r[1] + 1, r)
        # and a vertical drift of a finger on it scrolls nothing
        pg.evaluate("window.scrollTo(0, 40)"); pg.wait_for_timeout(200)
        chk("%s: ...so there is no document scroll for a touch to start (scrollY %s)" % (name, pg.evaluate("scrollY")), pg.evaluate("scrollY") == 0)
        ctx.close()
    br.close()

BAR = """()=>{ const t = document.querySelector('.bottomtabs'); if(!t) return null; const r = t.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, vh: innerHeight, fromBottom: innerHeight - r.bottom }; }"""
GOVERN = """async (src) => {
  window.__cap = []; const oa = window.addEventListener;
  window.addEventListener = function(t, f, o){ if(t === 'resize') window.__cap.push(f); return oa.apply(this, arguments); };
  let H = 800, W = 400;
  Object.defineProperty(window, 'innerHeight', { get: () => H, configurable: true });
  Object.defineProperty(window, 'innerWidth', { get: () => W, configurable: true });
  (0, eval)(src);
  const calls = []; window.addEventListener('resize', () => calls.push([W, H]));
  const w = window.__cap[window.__cap.length - 1];
  if(!w) return { err: 'the governor did not wrap a listener' };
  const fire = (trusted = true) => w({ isTrusted: trusted });
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const out = {};
  fire(); out.first = calls.length;                          // the first one is answered
  const t0 = performance.now();
  for(let k = 1; k <= 40; k++){ H = 800 + k; fire(); await sleep(16); }   // a toolbar giving up 40px over ~64 frames
  out.burstMs = Math.round(performance.now() - t0); out.during = calls.length - out.first;
  await sleep(250); out.after = calls.length - out.first; out.last = calls[calls.length - 1];
  let n = calls.length; fire(); out.dup = calls.length - n;   // the same size again, nothing new
  n = calls.length; W = 300; fire(); out.width = calls.length - n; out.widthAt = calls[calls.length - 1];
  n = calls.length; H = 500; fire(); out.keyboard = calls.length - n;      // 340px: a keyboard, answered at once
  n = calls.length; H = 505; fire(false); out.synthetic = calls.length - n; // one a test or the page made up
  return out; }"""
def govern(pw):
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r"<script>\s*/\* BUILD 384 \(round 18\): A TOOLBAR COLLAPSING.*?</script>", src, re.S)
    chk("the page carries the resize governor (a toolbar collapsing is not answered frame by frame)", bool(m))
    if not m: return
    js = m.group(0)[len("<script>"):-len("</script>")]
    br = pw.chromium.launch(executable_path=CHROME)
    ctx = br.new_context(viewport={"width": 440, "height": 797}, user_agent=UA, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); pg.set_content("<html><body></body></html>")
    r = pg.evaluate(GOVERN, js)
    chk("governor: it wraps a window resize listener", "err" not in r, r)
    if "err" not in r:
        allowed = int(r["burstMs"] / 120) + 2
        chk("governor: a toolbar giving up 40px in %dms (40 resizes) is answered at most once every 120ms: %d (<= %d)" % (r["burstMs"], r["during"], allowed), r["during"] <= allowed and r["during"] < 20, r)
        chk("governor: ...and the last answer is at the size the viewport ended on (%s)" % (r["last"],), r["last"] == [400, 840] and r["after"] >= r["during"], r)
        chk("governor: the same size again is not answered twice (%d)" % r["dup"], r["dup"] == 0, r)
        chk("governor: a width change is answered at once, at that size (%d, %s)" % (r["width"], r["widthAt"]), r["width"] == 1 and r["widthAt"] == [300, 840], r)
        chk("governor: a 340px height change (a keyboard) is answered at once (%d)" % r["keyboard"], r["keyboard"] == 1, r)
        chk("governor: a resize a test or the page made up (untrusted) is always answered (%d)" % r["synthetic"], r["synthetic"] == 1, r)
    ctx.close(); br.close()

def bar(pw):
    br = pw.chromium.launch(executable_path=CHROME)
    dev = DEVICES[0]; name, (sw, sh), top, bot, ipad = dev
    ctx, pg, vh = open_page(br, dev)
    screen_on(pg, "showHome()")
    pg.wait_for_timeout(500)
    a = pg.evaluate(BAR)
    pg.set_viewport_size({"width": sw, "height": vh + bot - 36}); pg.wait_for_timeout(700)   # the toolbar minimises: the viewport grows
    b = pg.evaluate(BAR)
    chk("%s, Safari tab: when the toolbar collapses the tab bar keeps its distance from the viewport's bottom (%.1f -> %.1f)" % (name, a["fromBottom"], b["fromBottom"]),
        abs(a["fromBottom"] - b["fromBottom"]) <= 1.5, [a, b])
    real = [x for x in pg.errs if not any(k in x for k in ("firebase", "firestore", "gstatic", "Failed to fetch", "net::"))]
    chk("%s: no page errors" % name, not real, real[:3])
    ctx.close(); br.close()

with sync_playwright() as pw:
    for s in want:
        {"seam": seam, "scroll": scroll, "noscroll": noscroll, "govern": govern, "bar": bar}[s](pw)
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
