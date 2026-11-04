"""Build 384 (round 2): the Get Started page.
Madison: "The start up screen wasn't showing for me on my laptop but it's been showing for me on iPhone. Ensure it shows up
everywhere when you aren't signed or don't have an account. Ensure the videos through the screen are high quality ... some
seem weird and start at weird spots and skip around like the upload pdf one. ... maybe include an interactive thing with some
example badges and then rank flares but have all the flares lit up in a row ... When you hit let's get started, ensure the
transition to sign up/sign in screen is nice, like maybe the word nova zooms in really fast ... The let's get started button
looks small btw? It should be nice and big hush like the start studying button. The sign in and sign up buttons look small too"
Read off the page:
 route   - Get Started opens for a device with no account - fresh, or with storage an earlier visit left (Get Started seen,
           an unfinished store, just signed out) - on a phone (installed and in a browser), an iPad and two laptops, with no
           loading screen in front; a device with an account (onboarded, or a code mid sign-up) never sees it. A repeat
           visit has the button from the start; a first visit's waits for the end.
 clips   - every clip on the page (each scene's, and the laptop's two beside the title): plays from its start (t<0.5s) as
           it comes on screen, its time rising steadily for 2s with no jump, back at its start when it comes on screen
           again; its natural size at least twice its CSS width on a phone and a laptop; its poster is its first frame
           and its last frame is its first (the loop has no seam).
 show    - the showcase: at least 4 real badges (drawn), and every rank's flare lit, one row, inside the screen (375, 440,
           iPad, laptop), rising in as the row arrives (transform/opacity transitions only; there at once with Reduce motion);
           a tap names it.
 buttons - Let's get started is Home's Start Studying (height, width, font within 2px) on a phone and an iPad, 44px+ and on
           screen on a 375x667 phone, 52px+ in 18px+ words on a laptop; Welcome's two buttons are 52px+ full-width pills on
           every one of them, and Welcome still fits a 375x667 phone without scrolling.
 leave   - Let's get started: NOVA's transform grows (to 4x+) as it fades, then Welcome is up and the page and the word are gone
           (under a second - 1.6s where the page's frames come 150ms+ apart); with Reduce motion there is no zoom, the page
           fades, Welcome comes up.
 errors  - no page errors anywhere above.
Run:  python3 tools/check-b384-getstarted.py [route clips show buttons leave]
      --against OLD/index.html  (the old tree: its landing/ beside it is served - e.g. git archive 91a1d96 index.html landing
      version.json | tar -x -C /tmp/old; then --against /tmp/old/index.html) must FAIL."""
import functools, http.server, io, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if "--against" in sys.argv:
    ROOT = os.path.dirname(os.path.abspath(sys.argv[sys.argv.index("--against") + 1]))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""
DEV = {  # w, h, insets, installed
    "phone": (440, 956, (62, 0, 34, 0), True), "phone-tab": (440, 956, (0, 0, 0, 0), False), "se": (375, 667, (20, 0, 0, 0), True),
    "ipad": (834, 1194, (24, 0, 20, 0), True), "laptop": (1536, 864, (0, 0, 0, 0), False), "dell": (1366, 768, (0, 0, 0, 0), False)}
SEEN = ("freshstart", "intro.seen", "unithold.tip", "daily.seen", "savecode.asked", "savecode.card", "penal55124.seen",
        "penal124256.seen", "penal256578.seen")
ACCOUNT = {"firstName": "Casey", "avatarChar": "ghost", "onboardingComplete": True, "publicId": "pubgate0384", "tourRev": 999,
           "novaMet": 99, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True, "lastModified": 1790500000000,
           "seenMainMenuTour": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
           "seenRankingsTour": True, "seenAppearanceTour": True,
           "lifetime": {"points": 4000, "answered": 300, "correct": 280}}


def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    http.server.ThreadingHTTPServer.handle_error = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port


SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
BUILD = (re.search(r'const APP_BUILD = "([^"]+)"', SRC) or [None, "?"])[1]
def patched(ins):
    v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
    return INSET_RE.sub(lambda m: v[m.group(1)], SRC)

ok = True
ERRS = []
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:420], flush=True)


def storage(kind):
    """localStorage for each kind of device, set before the app's first script"""
    s = "localStorage.setItem('class26e.frame.ok','go-live-1');"
    if kind == "fresh": return s
    if kind == "seen":      # an earlier visit tapped through Get Started and left (no account)
        return s + "localStorage.setItem('class26e.getstarted','1');" + "".join("localStorage.setItem('class26e.%s','1');" % k for k in SEEN[:3])
    if kind == "leftover":  # an earlier visit left its (unfinished, nameless) saved copy behind, and the seen mark
        return s + "localStorage.setItem('class26e.getstarted','1');localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(
            {"onboardingComplete": False, "lifetime": {"points": 0}, "theme": {"accent": "ink"}}))
    if kind == "signedout":  # Settings > Account > Sign out, then the reload: the head script's wipe has run
        return s + "localStorage.setItem('class26e.signedout', String(Date.now() - 5000));localStorage.setItem('class26e.hadaccount','1');"
    if kind == "account":
        return s + "".join("localStorage.setItem('class26e.%s','1');" % k for k in SEEN) + \
            "localStorage.setItem('class26e.getstarted','1');localStorage.setItem('class26e.synccode','GATE-0384');" \
            "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(ACCOUNT))
    if kind == "account-nomark":  # an onboarded account on a device that never set the seen mark
        return s + "".join("localStorage.setItem('class26e.%s','1');" % k for k in SEEN) + \
            "localStorage.setItem('class26e.synccode','GATE-0385');localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(ACCOUNT))
    if kind == "midsignup":  # a code, sign-up not finished: Welcome offers the account back
        return s + "localStorage.setItem('class26e.synccode','GATE-0386');localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(
            {"onboardingComplete": False, "firstName": "Casey"}))
    raise ValueError(kind)


def page(br, url, dev, kind="fresh", reduce=False):
    w, h, ins, inst = DEV[dev]
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if w < 1000 else 1.25,
                         has_touch=w < 1000, reduced_motion="reduce" if reduce else "no-preference")
    if inst: ctx.add_init_script(STANDALONE)
    ctx.add_init_script("(()=>{ if(sessionStorage.getItem('__gs')) return; sessionStorage.setItem('__gs','1'); try{" + storage(kind) + "}catch(e){} })()")
    pg = ctx.new_page()
    pg.__errs = []
    pg.on("pageerror", lambda e, p=pg: (p.__errs.append(str(e)[:200]), ERRS.append("%s/%s: %s" % (dev, kind, str(e)[:200]))))
    body = patched(ins)
    pg.route("**/index.html", lambda r, q, b=body: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(url)
    return ctx, pg


SCREEN = """()=>{ const sp = document.getElementById('splashscreen');
  const spUp = !!sp && getComputedStyle(sp).display !== 'none' && getComputedStyle(sp).visibility !== 'hidden' && +getComputedStyle(sp).opacity > .05;
  const s = document.querySelector('[data-screen]'); const st = document.querySelector('#stage > *');
  return { screen: document.querySelector('.gs-page') ? 'getstarted' : (document.querySelector('#stage .cosmic-welcome') ? 'welcome'
           : (document.querySelector('#stage .screen-home-actual') ? 'home' : (st ? st.className : 'none'))), splash: spUp,
           ready: !!document.querySelector('.gs-bar.is-ready') }; }"""


def sec_route(br, url):
    print("\nroute: Get Started for every device with no account, never for one with an account")
    for dev in ("phone", "phone-tab", "ipad", "laptop", "dell"):
        for kind in ("fresh", "seen", "leftover", "signedout"):
            ctx, pg = page(br, url, dev, kind)
            pg.wait_for_timeout(1600)
            early = pg.evaluate(SCREEN)
            pg.wait_for_timeout(2200)
            r = pg.evaluate(SCREEN)
            if kind == "signedout":
                # (384) Madison: "Signing out, signing out will just bring them to the welcome screen."
                for _ in range(16):
                    if r["screen"] == "welcome": break
                    pg.wait_for_timeout(500); r = pg.evaluate(SCREEN)
                chk("%s, signed out: Welcome, not Get Started (%s)" % (dev, r["screen"]), r["screen"] == "welcome", [early, r])
                ctx.close(); continue
            chk("%s, %s: Get Started is up 1.6s in with no loading screen in front, and still up after 3.8s (%s)" % (dev, kind, r["screen"]),
                early["screen"] == "getstarted" and not early["splash"] and r["screen"] == "getstarted", [early, r])
            if kind != "fresh":
                chk("%s, %s: a repeat visit has Let's get started from the start" % (dev, kind), r["ready"], r)
            else:
                chk("%s, fresh: a first visit's button waits for the end of the page" % dev, not r["ready"], r)
            ctx.close()
        for kind in ("account", "account-nomark", "midsignup"):
            ctx, pg = page(br, url, dev, kind)
            pg.wait_for_timeout(4200)
            r = pg.evaluate(SCREEN)
            want = "home" if kind.startswith("account") else "welcome"
            chk("%s, %s: never Get Started - %s (%s)" % (dev, kind, want, r["screen"]), r["screen"] == want, r)
            ctx.close()


CLIP = """async ([sel, i])=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const v = document.querySelectorAll(sel)[i]; if(!v) return null;
  const s = document.querySelector('.gs-scroll');
  const into = () => { const r = v.getBoundingClientRect(), sr = s.getBoundingClientRect(); s.scrollTop += (r.top + r.height / 2) - (sr.top + sr.height / 2); };
  const run = async () => {
    into();
    const t0 = performance.now();
    while((v.paused || v.readyState < 3 || v.currentTime <= 0) && performance.now() - t0 < 12000) await wait(25);
    const ts = [];
    /* [the time on the page's clock, the clip's time]: a sample can come late on a busy page, and the clip's time is read
       against the time that really went by */
    for(let k = 0; k < 21; k++){ ts.push([+(performance.now() / 1000).toFixed(3), +v.currentTime.toFixed(3)]); await wait(100); }
    return ts; };
  /* away = the far end of the page from it (a clip beside the title is on screen from the start: it is sent away first) */
  const nearTop = v.getBoundingClientRect().bottom + s.scrollTop < s.clientHeight * 1.5;
  const goAway = async () => { s.scrollTop = nearTop ? s.scrollHeight : 0; await wait(700); };
  if(!v.paused) await goAway();
  const first = await run();
  await goAway();
  const away = { paused: v.paused, t: +v.currentTime.toFixed(3) };
  const again = await run();
  const r = v.getBoundingClientRect();
  return { key: v.dataset.gs, first, again, away, vw: v.videoWidth, vh: v.videoHeight, cssW: Math.round(r.width), dur: v.duration }; }"""
FRAMES = """async ([sel, i])=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const src = document.querySelectorAll(sel)[i]; if(!src) return null;
  const v = document.createElement('video'); v.muted = true; v.preload = 'auto'; v.src = src.currentSrc || src.src; document.body.appendChild(v);
  await new Promise(r => { v.onloadeddata = r; setTimeout(r, 8000); });
  const c = document.createElement('canvas'); c.width = 60; c.height = 130; const g = c.getContext('2d');
  const grab = () => { g.drawImage(v, 0, 0, 60, 130); return g.getImageData(0, 0, 60, 130).data; };
  const seek = t => new Promise(r => { v.onseeked = r; v.currentTime = t; setTimeout(r, 4000); });
  await seek(0); await wait(60); const f0 = grab();
  await seek(Math.max(0, v.duration - 0.02)); await wait(60); const fl = grab();
  const im = new Image(); im.src = src.poster; await new Promise(r => { im.onload = r; im.onerror = r; setTimeout(r, 5000); });
  g.drawImage(im, 0, 0, 60, 130); const fp = g.getImageData(0, 0, 60, 130).data;
  const diff = (a, b) => { let s = 0, n = 0; for(let k = 0; k < a.length; k += 4){ s += Math.abs(a[k]-b[k]) + Math.abs(a[k+1]-b[k+1]) + Math.abs(a[k+2]-b[k+2]); n += 3; } return +(s / n).toFixed(2); };
  v.remove();
  return { poster: diff(f0, fp), seam: diff(f0, fl) }; }"""


def sec_clips(br, url):
    print("\nclips: each from its start, steady, high-res; poster = first frame; the loop has no seam")
    for dev, sel in (("phone", ".gs-scene video"), ("laptop", ".gs-page video")):
        ctx, pg = page(br, url, dev, "fresh")
        pg.wait_for_timeout(3000)
        n = pg.evaluate("(sel)=>document.querySelectorAll(sel).length", sel)
        chk("%s: the page has its clips (%d)" % (dev, n), n >= 5, n)
        for i in range(n):
            r = pg.evaluate(CLIP, [sel, i])
            if not r: chk("%s clip %d" % (dev, i), False, "missing"); continue
            fs, ag = r["first"], r["again"]
            # Never back; never ahead of the time that went by since the first sample (+0.5s: currentTime is the player's
            # "official" position, which a busy page updates late and then all at once - this sandbox runs at a load of ~20
            # on 4 cores - so one step can catch up, but a clip that skips gets ahead of the clock); and on its way (1s+ of
            # clip over the samples). A step of 0 is the player waiting on its decoder, not the clip jumping.
            steps = lambda s: [(b[1] - s[0][1], b[0] - s[0][0], b[1] - a[1]) for a, b in zip(s, s[1:])]
            steady = lambda d: bool(d) and all(st >= 0 and gc <= gw + .5 for gc, gw, st in d) and d[-1][0] > 1.0
            d1, d2 = steps(fs), steps(ag)
            worst = max([gc - gw for gc, gw, _ in d1] or [0])
            chk("%s %s: plays from its start (%.2fs) and its time rises for 2s, never back, no jump (most ahead of the clock %.2fs)" % (
                dev, r["key"], fs[0][1], worst), fs[0][1] < .5 and steady(d1), [x[1] for x in fs])
            chk("%s %s: off screen it stops and goes back to its start; on screen again it starts there (%.2fs)" % (dev, r["key"], ag[0][1]),
                r["away"]["paused"] and r["away"]["t"] < .05 and ag[0][1] < .5 and steady(d2), [r["away"], [x[1] for x in ag]])
            chk("%s %s: its picture is high-res - %dpx wide for %dpx on screen (2x at least)" % (dev, r["key"], r["vw"], r["cssW"]),
                r["vw"] >= 2 * r["cssW"], r)
            if dev == "laptop" or i < 6:
                f = pg.evaluate(FRAMES, [sel, i])
                chk("%s %s: the poster is the clip's first frame (diff %.1f) and its last frame is its first (seam %.1f)" % (
                    dev, r["key"], f and f["poster"], f and f["seam"]), f and f["poster"] < 6 and f["seam"] < 6, f)
        ctx.close()


SHOW = """()=>{ const s = document.querySelector('.gs-show'); if(!s) return null;
  const b = [...s.querySelectorAll('.gs-badges > *')], f = [...s.querySelectorAll('.gs-flares > *')];
  const lit = f.filter(x => x.querySelector('.cosmic-badge-lit svg, .cosmic-badge-lit img'));
  const R = e => e.getBoundingClientRect();
  const tops = f.map(x => Math.round(R(x).top)), all = b.concat(f);
  const tr = e => getComputedStyle(e).transitionProperty.split(',').map(x => x.trim());
  return { badges: b.length, drawn: b.filter(x => x.querySelector('svg.badge-art')).length, flares: f.length, lit: lit.length,
           tiers: (typeof TIER_ORDER_FULL !== 'undefined') ? TIER_ORDER_FULL.length : 7,
           oneRow: tops.length ? Math.max(...tops) - Math.min(...tops) <= 2 : false,
           inside: all.every(x => R(x).left >= 0 && R(x).right <= innerWidth), sideScroll: document.querySelector('.gs-scroll').scrollWidth - innerWidth,
           op: f.map(x => +getComputedStyle(x).opacity), bop: b.map(x => +getComputedStyle(x).opacity),
           trans: [...new Set(all.flatMap(tr))], tap: Math.min(...f.map(x => Math.min(R(x).width, R(x).height))) }; }"""


def sec_show(br, url):
    print("\nshow: real badges and every rank's flare lit in a row, rising in as it arrives")
    for dev in ("se", "phone", "ipad", "laptop"):
        ctx, pg = page(br, url, dev, "fresh")
        pg.wait_for_timeout(4200)
        before = pg.evaluate(SHOW)
        if not before:
            chk("%s: the showcase is on the page" % dev, False, "no .gs-show"); ctx.close(); continue
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'), e=document.querySelector('.gs-flares'); const r=e.getBoundingClientRect(); s.scrollTop += r.top - innerHeight * .45; }")
        # the rows rise in over ~1.7s; a busy page is given up to 8s to finish them
        r = None
        for _ in range(16):
            pg.wait_for_timeout(500)
            r = pg.evaluate(SHOW)
            if min(r["op"]) > .99 and min(r["bop"]) > .99 and r["oneRow"]: break
        chk("%s: %d badges, all drawn by the app's badge art (%d)" % (dev, r["badges"], r["drawn"]), r["badges"] >= 4 and r["drawn"] == r["badges"], r)
        chk("%s: every rank's flare (%d of %d), lit, in one row" % (dev, r["lit"], r["tiers"]), r["flares"] == r["tiers"] and r["lit"] == r["tiers"] and r["oneRow"], r)
        chk("%s: all of it inside the screen, nothing scrolls sideways" % dev, r["inside"] and r["sideScroll"] <= 0, r)
        chk("%s: hidden until its row arrives, then risen in (opacity %s -> %s)" % (dev, min(before["op"]), min(r["op"])),
            max(before["op"]) < .05 and min(r["op"]) > .95 and min(r["bop"]) > .95, [before["op"], r["op"], r["bop"]])
        chk("%s: it moves by transform and opacity only (%s)" % (dev, r["trans"]), set(r["trans"]) <= {"opacity", "transform"}, r["trans"])
        chk("%s: a flare is 36px+ (44px with its touch margin)" % dev, r["tap"] >= 35.5, r["tap"])
        if dev == "phone":
            cap0 = pg.evaluate("()=>document.querySelector('.gs-show-cap').textContent")
            pg.evaluate("()=>document.querySelectorAll('.gs-flares > *')[2].click()"); pg.wait_for_timeout(300)
            cap1 = pg.evaluate("()=>document.querySelector('.gs-show-cap').textContent")
            pg.evaluate("()=>document.querySelectorAll('.gs-badges > *')[1].click()"); pg.wait_for_timeout(300)
            cap2 = pg.evaluate("()=>document.querySelector('.gs-show-cap').textContent")
            chk("phone: a tap on a flare or a badge names it (%r, %r)" % (cap1, cap2), cap1 != cap0 and cap2 != cap1 and len(cap1) > 3 and len(cap2) > 3, [cap0, cap1, cap2])
        ctx.close()
    ctx, pg = page(br, url, "phone", "fresh", reduce=True)
    pg.wait_for_timeout(4200)
    pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'), e=document.querySelector('.gs-flares'); if(!e) return; const r=e.getBoundingClientRect(); s.scrollTop += r.top - innerHeight * .45; }")
    pg.wait_for_timeout(150)
    r = pg.evaluate(SHOW)
    chk("phone, Reduce motion: the badges and flares are simply there", r and min(r["op"]) > .95 and min(r["bop"]) > .95, r)
    ctx.close()


BTN = """(sel)=>{ const b = document.querySelector(sel); if(!b) return null; const r = b.getBoundingClientRect(), cs = getComputedStyle(b);
  return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, fs: parseFloat(cs.fontSize), top: Math.round(r.top), bottom: Math.round(r.bottom),
           left: Math.round(r.left), right: Math.round(r.right), vis: r.width > 0 && cs.display !== 'none' }; }"""


def sec_buttons(br, url):
    print("\nbuttons: Let's get started is Start Studying's size; Welcome's two are big full-width pills")
    home = {}
    for dev in ("phone", "ipad"):
        ctx, pg = page(br, url, dev, "account")
        pg.wait_for_timeout(3800)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"); pg.wait_for_timeout(900)
        home[dev] = pg.evaluate(BTN, ".screen-home-actual > .playbtn")
        ctx.close()
    for dev in ("se", "phone", "ipad", "laptop", "dell"):
        ctx, pg = page(br, url, dev, "seen")
        pg.wait_for_timeout(3800)
        welcome0 = None
        if not pg.evaluate("()=>!!document.querySelector('.gs-go')"):   # (a build that sends this device to Welcome)
            welcome0 = pg.evaluate("()=>document.documentElement.scrollHeight - innerHeight")
            pg.evaluate("()=>showGetStarted()"); pg.wait_for_timeout(900)
        g = pg.evaluate(BTN, ".gs-go") or {"w": 0, "h": 0, "fs": 0, "bottom": 0, "left": 0}
        vh = pg.evaluate("()=>innerHeight")
        if dev in home:
            hm = home[dev]
            chk("%s: Let's get started %sx%s in %spx = Start Studying %sx%s in %spx (2px)" % (dev, g["w"], g["h"], g["fs"], hm["w"], hm["h"], hm["fs"]),
                hm and hm["vis"] and abs(g["w"] - hm["w"]) <= 2 and abs(g["h"] - hm["h"]) <= 2 and abs(g["fs"] - hm["fs"]) <= 2, [g, hm])
        elif dev == "se":
            chk("se: Let's get started is 44px+ (%s) and on screen" % g["h"], g["h"] >= 44 and g["bottom"] <= vh and g["left"] >= 0, g)
        else:
            chk("%s: Let's get started is big - %spx tall in %spx words" % (dev, g["h"], g["fs"]), g["h"] >= 52 and g["fs"] >= 18 and g["bottom"] <= vh, g)
        pg.evaluate("()=>{ showWelcome(); }"); pg.wait_for_timeout(900)
        r = pg.evaluate("""()=>{ const a = document.querySelector('.cosmic-welcome-actions'); if(!a) return null;
          const bs = [...a.querySelectorAll('.cosmic-welcome-btn')].filter(b => b.getBoundingClientRect().width > 0);
          const ar = a.getBoundingClientRect();
          return { n: bs.length, hs: bs.map(b => Math.round(b.getBoundingClientRect().height)), ws: bs.map(b => Math.round(b.getBoundingClientRect().width)),
                   aw: Math.round(ar.width), bottom: Math.max(...bs.map(b => Math.round(b.getBoundingClientRect().bottom))), rad: bs.map(b => getComputedStyle(b).borderTopLeftRadius),
                   labels: bs.map(b => b.textContent.trim()), scroll: document.documentElement.scrollHeight - innerHeight,
                   box: Math.round(document.querySelector('.cosmic-welcome').getBoundingClientRect().bottom) }; }""")
        # full width = the width of Welcome's button column (352px at most, the column's own cap since build 322)
        chk("%s: Welcome's two buttons are 52px+ (%s), full-width pills (%s of %s)" % (dev, r and r["hs"], r and r["ws"], r and r["aw"]),
            r and r["n"] == 2 and min(r["hs"]) >= 52 and min(r["ws"]) >= .9 * min(r["aw"], 352) and all(float(x.rstrip("px") or 0) >= 20 for x in r["rad"]), r)
        # (the installed Pro Max's page scrolls 12px on 91a1d96 too - the .wrap's padding under Welcome with this harness's 34px
        # home-indicator inset, not Welcome: there its box and buttons must be on screen and the 12px must not grow)
        allow = 12 if dev == "phone" else 1
        chk("%s: Welcome fits - its box and buttons on screen, nothing more to scroll (%s, %s)" % (dev, r and r["box"], r and r["scroll"]),
            r and r["bottom"] <= vh and r["box"] <= vh + 1 and r["scroll"] <= allow, r)
        ctx.close()


ZOOM = """async ()=>{
  const out = { samples: [], welcomeAt: null, goneAt: null, anim: null, startTl: null, goneTl: null };
  const t0 = performance.now();
  document.querySelector('.gs-go').click();
  /* the move itself, read off its animation (made in the tap): its keyframes, its length, when it started on the page's
     animation clock - what the compositor plays whatever the page's own thread is doing */
  const w = document.querySelector('.gs-zoom-word'), a = w && w.getAnimations()[0];
  if(a){
    const kf = a.effect.getKeyframes();
    out.anim = { dur: a.effect.getTiming().duration, scales: kf.map(k => +new DOMMatrixReadOnly(k.transform || 'none').a.toFixed(3)),
                 ops: kf.map(k => +k.opacity), props: [...new Set(kf.flatMap(k => Object.keys(k).filter(x => !['offset', 'easing', 'composite', 'computedOffset'].includes(x))))] };
    a.ready.then(() => { out.startTl = a.startTime; });
  }
  return await new Promise(res => {
    const tick = () => {
      const t = performance.now() - t0, w2 = document.querySelector('.gs-zoom-word');
      if(w2){ const m = new DOMMatrixReadOnly(getComputedStyle(w2).transform); out.samples.push([Math.round(t), +m.a.toFixed(3), +(+getComputedStyle(w2).opacity).toFixed(3)]); }
      if(out.welcomeAt === null && document.querySelector('#stage .cosmic-welcome')) out.welcomeAt = Math.round(t);
      if(out.goneAt === null && !document.querySelector('.gs-page') && !document.querySelector('.gs-zoom, .gs-cover')){ out.goneAt = Math.round(t); out.goneTl = document.timeline.currentTime; }
      if(t > 3000 || (out.goneAt !== null && out.welcomeAt !== null)) return res(out);
      requestAnimationFrame(tick); };
    requestAnimationFrame(tick); }); }"""


def sec_leave(br, url):
    print("\nleave: NOVA flies at the viewer, then Welcome")
    for dev in ("phone", "laptop"):
        ctx, pg = page(br, url, dev, "seen")
        pg.wait_for_timeout(3800)
        if not pg.evaluate("()=>!!document.querySelector('.gs-go')"): pg.evaluate("()=>showGetStarted()"); pg.wait_for_timeout(900)   # (a build that sent this device to Welcome)
        r = pg.evaluate(ZOOM)
        an = r["anim"] or {}
        sc = an.get("scales") or []
        chk("%s: Let's get started sets NOVA moving - a transform and opacity move of %sms, scale %s, opacity %s" % (dev, an.get("dur"), sc, an.get("ops")),
            bool(an) and 450 <= (an.get("dur") or 0) <= 750 and set(an.get("props") or []) <= {"transform", "opacity"}
            and sc and sc[0] < 1 and max(sc) >= 4 and all(b >= a for a, b in zip(sc, sc[1:])) and max(an.get("ops") or [0]) >= 1 and an["ops"][-1] == 0, r)
        smp = [s[1] for s in r["samples"]]
        chk("%s: as drawn, the word only ever grows (%d frames read, to %.1fx)" % (dev, len(smp), max(smp or [0])),
            all(b >= a - .01 for a, b in zip(smp, smp[1:])), r["samples"][:30])
        took = (r["goneTl"] - r["startTl"]) if (r["goneTl"] is not None and r["startTl"] is not None) else None
        gaps = [b[0] - a[0] for a, b in zip(r["samples"], r["samples"][1:])]
        # under a second; a page whose frames come 150ms+ apart (this sandbox at a load of 20+ on 4 cores - the frame gaps
        # are printed) is given 1.6s, since the end of the move is only seen on the next frame after it
        slow = bool(gaps) and sorted(gaps)[len(gaps) // 2] >= 150
        chk("%s: then Welcome is up and the page and the word are gone, %sms after the move began (under %s; frames %sms apart)" % (
            dev, took and round(took), "1.6s" if slow else "a second", gaps),
            r["welcomeAt"] is not None and took is not None and took <= (1600 if slow else 1000) and pg.evaluate(SCREEN)["screen"] == "welcome", r)
        ctx.close()
    ctx, pg = page(br, url, "phone", "seen", reduce=True)
    pg.wait_for_timeout(3800)
    if not pg.evaluate("()=>!!document.querySelector('.gs-go')"): pg.evaluate("()=>showGetStarted()"); pg.wait_for_timeout(900)
    r = pg.evaluate(ZOOM)
    chk("phone, Reduce motion: no zoom - the page fades and Welcome comes up (%sms)" % r["goneAt"],
        not r["anim"] and not r["samples"] and r["goneAt"] is not None and r["goneAt"] <= 1200 and pg.evaluate(SCREEN)["screen"] == "welcome", r)
    ctx.close()


SECTIONS = {"route": sec_route, "clips": sec_clips, "show": sec_show, "buttons": sec_buttons, "leave": sec_leave}
if __name__ == "__main__":
    args = [a for i, a in enumerate(sys.argv[1:]) if not a.startswith("--") and (i == 0 or sys.argv[i] != "--against")]
    want = [a for a in args if a in SECTIONS] or list(SECTIONS)
    print("check-b384-getstarted against %s (build %s)" % (ROOT, BUILD))
    srv, url = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for s in want: SECTIONS[s](br, url)
        br.close()
    srv.shutdown()
    chk("no page errors in any of it", not ERRS, ERRS[:4])
    print("\nALL PASS" if ok else "\nFAILED")
    sys.exit(0 if ok else 1)
