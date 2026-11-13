#!/usr/bin/env python3
"""Build 384.98: the rank-up cutscene that sent the app to a white screen and the splash.

  python3 tools/check-b384-rankup2.py [--against FILE|REV] [--only A,B,C]

Madison (he/him), on his installed iPhone, on the live build (384.92-384.94): "The rank up cutscene, my app would show a white
screen, do the splash, and then go to main menu in the middle of a cutscene for the rank (the very beginning) and then I'd have
to do it again." A white screen followed by the splash is a fresh launch with no "Pushing update" screen in front of it: iOS
ended the page's web process. The cutscene's first frame was the heaviest moment of the journey - the road map stayed laid out
and drawn under the dark while two planet systems and the cutscene's depth layers were built over it in one task.

  A. THE FORCED UPDATE WAITS FOR EVERY SCENE (a newer build advertised with force on; the reload itself is recorded, not made).
     (1) Through a whole real rank-up journey, every frame on which a scene is up (the journey, its veil and curtain, the cutscene,
     a reward card, a badge scene, Nova's words after it) the update is held, it does not go while any of them is up, and it goes within a few seconds
     of the last one ending (asked again, not left to the next poll). (2) The badge case scene on Home (the scene a left test is
     owed) holds it the same way - 384.94 held only the scenes its list named, and the badge case was not one. (3) A scene that
     begins in the second "Pushing update" is up holds it too: the reload is asked again at the moment it would go.
  B. THE CUTSCENE'S OPENING IS LIGHT. (1) The road map draws nothing under the cutscene: in the composited layer tree read at
     the cutscene's first frames and a few seconds in, no layer of the map (#stage) paints. (2) It is back, unchanged, before the
     cutscene lifts: at the frame the overlay starts its exit the map is drawn, at the scroll and page height it had when the
     hand-off's veil went up, and the journey goes on to Home with nothing owed. (3) The depth layers are the size of what
     they paint: each of the nebula and the rays, drawn alone in white on black at a scale that fits it on the screen, paints out
     to at least 80% of its half-box from the centre (a box several times its glow is a layer several times what it needs, made
     in that first frame). (4) Supernova's cutscene builds two planet systems, not three, and marks the same parts to reveal.
  C. A RELAUNCH INSIDE THE CUTSCENE IS HARMLESS. The page is crashed (CDP) a moment into the cutscene's opening and launched
     again in the same storage. (1) It boots to Home with no page error and nothing of the journey left on the page, the rank is
     still owed, and the page's end log says it ended inside the rank-up cutscene. (2) Played again, the journey plays the
     cutscene once, in full (the hand-off's dark is there), lands on Home and owes nothing; nothing plays a second time. (3) Ended
     inside the cutscene a second time in a row, the next launch plays it as the short still scene (no hand-off, no whirl), once,
     and owes nothing after.

Fails on 384.94 (origin/main) in A2, A3, B1, B3, B4, C1 and C3.
"""
import io, json, os, re, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b384_rankjourney_lib import *  # noqa: E402,F401


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


ONLY = set((arg("--only") or "A,B,C").split(","))
AGAINST = arg("--against")
if AGAINST and not os.path.exists(AGAINST):
    tmp = os.path.join(tempfile.mkdtemp(), "index.html")
    open(tmp, "wb").write(subprocess.check_output(["git", "show", "%s:index.html" % AGAINST], cwd=ROOT))
    AGAINST = tmp
SELF = Served(AGAINST)
FAILS = []
_BUF = None


def ck(name, ok, info=None):
    line = ("  PASS  " if ok else "  FAIL  ") + name + ("" if ok or info is None else "  -> " + str(info)[:700])
    if _BUF is not None:
        _BUF.append((line, ok, name))
        return
    print(line, flush=True)
    if not ok:
        FAILS.append(name)


def case(fn, *a, tries=4):
    """one self-contained case (its own browser), run again from the start when the sandbox's chromium drops a tab on its own
    (a case that crashes the page on purpose catches that itself)"""
    global _BUF
    last = None
    for _ in range(tries):
        _BUF = []
        try:
            fn(*a)
            buf, _BUF = _BUF, None
            for line, ok, name in buf:
                print(line, flush=True)
                if not ok:
                    FAILS.append(name)
            return
        except Exception as e:
            last = e
            _BUF = None
            print("  (case %s stopped: %s - again)" % (fn.__name__, str(e)[:160]), flush=True)
            while LAUNCHED:
                try:
                    LAUNCHED.pop()[0].close()
                except Exception:
                    pass
            if not re.search(r"crash|closed|Target|Timeout|timeout", str(e)):
                raise
    raise last


LAUNCHED = []


def launch(pw):
    """a browser with a mark of its own on its command line, so its renderer can be found and ended like iOS ends a page"""
    mark = "--nova-rankup2-%d-%d" % (os.getpid(), len(LAUNCHED) + int(time.time() * 1000) % 100000)
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--disable-dev-shm-usage", mark])
    LAUNCHED.append((br, mark))
    return br


def kill_renderers(br):
    """SIGKILL every renderer of this browser (and only this one), as jetsam ends a WebContent process: no pagehide, no unload"""
    import signal
    mark = next((m for b, m in LAUNCHED if b is br), None)
    procs = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            st = open("/proc/%s/stat" % d).read()
            ppid = int(st[st.rindex(")") + 2:].split()[1])
            cmd = open("/proc/%s/cmdline" % d, "rb").read().replace(b"\0", b" ").decode("utf-8", "replace")
            procs[int(d)] = (ppid, cmd)
        except Exception:
            pass
    root = [p for p, (pp, c) in procs.items() if mark and mark in c and "--type=" not in c]
    if not root:
        return 0
    tree, grew = {root[0]}, True
    while grew:
        grew = False
        for p, (pp, c) in procs.items():
            if pp in tree and p not in tree:
                tree.add(p); grew = True
    n = 0
    for p in tree:
        c = procs[p][1]
        if "--type=renderer" in c and "--extension-process" not in c:
            try:
                os.kill(p, signal.SIGKILL); n += 1
            except Exception:
                pass
    return n


class Ctx:
    """a context seeded ONCE (it survives a relaunch: a new page in the same storage), installed, with version.json answering
    the served build, or a newer one with force on once `newer` is set"""
    def __init__(self, br, served, cls="academy", w=440, h=956, dpr=1):
        self.served, self.newer = served, False
        self.ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True)
        self.ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
        self.ctx.add_init_script(init_js(cls).replace("sessionStorage.getItem('__seeded')", "localStorage.getItem('__rk2seeded')")
                                 .replace("sessionStorage.setItem('__seeded','1')", "localStorage.setItem('__rk2seeded','1')"))
        self.ctx.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=served.body))
        self.ctx.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"},
                       body='{"build":"%s","frameId":"","force":%s}' % ("2099-12-31-999" if self.newer else served.build, "true" if self.newer else "false")))
        self.errs = []

    def open(self):
        pg = self.ctx.new_page()
        pg.on("pageerror", lambda e: self.errs.append(str(e)[:300]))
        pg.goto("http://127.0.0.1:%d/index.html" % self.served.port, timeout=180000)
        pg.wait_for_timeout(3500)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ __stub(); }catch(e){} theme.reduceMotion = false; theme.muteBanners = false; applyTheme(); }")
        return pg


DONE = r"""() => !rankUpScene && !rankUpOwed() && !document.body.classList.contains('rankup-lock') && !document.querySelector('.rs-spot, #supernova-cutscene, .ru-veil, .ru-curtain.is-on')"""


def journey(pg, timeout=480, until=None, tick=None):
    """real time, as a person: tap the Profile tab when Home calls, reward cards tapped once they have been up 2.6s; returns
    the seconds taken, or None if it did not end (until(pg, st) true stops it early and returns -1)"""
    t0 = time.time(); tapped = False; over = None
    while time.time() - t0 < timeout:
        pg.wait_for_timeout(150)
        st = pg.evaluate(PROBE)
        if st["lock"] and not st["sc"] and not tapped:
            pg.wait_for_timeout(1200)
            pg.evaluate("()=>{ document.getElementById('bottomtab-profile').click(); }")
            tapped = True
        pg.evaluate(PERSON)
        if tick:
            tick(pg, st)
        if until and until(pg, st):
            return -1
        if tapped and pg.evaluate(DONE):
            over = over or time.time()
            if time.time() - over > 3:
                return round(time.time() - t0, 1)
        else:
            over = None
    return None


WATCH = r"""() => {
  if(window.__w) return; const W = window.__w = { cuts: 0, veils: 0, still: 0, spin: 0, exit: null, dark: null, ups: [] };
  new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => {
    if(n.nodeType !== 1) return;
    if(n.id === 'supernova-cutscene'){ W.cuts++; W.ups.push(Math.round(performance.now())); new MutationObserver(() => {
      if(n.classList.contains('rank-still')) W.stillSeen = true;
      if(n.classList.contains('is-cutspin')) W.spinSeen = true;
      if(n.classList.contains('supernova-exit') && !W.exit){ const sr = stage.querySelector('.screen-ranks'); const cs = sr ? getComputedStyle(sr) : null;
        const s0 = sr && sr.querySelector('.rankmap-stop');
        W.exit = { y: scrollY, sh: document.documentElement.scrollHeight, vis: cs ? cs.visibility : null, cv: cs ? (cs.contentVisibility || 'visible') : null,
                   top: s0 ? +s0.getBoundingClientRect().top.toFixed(1) : null }; }
    }).observe(n, { attributes: true, attributeFilter: ['class'] }); }
    if(n.classList && n.classList.contains('ru-veil')){ W.veils++; if(!W.dark){
      const sr = stage.querySelector('.screen-ranks'), s0 = sr && sr.querySelector('.rankmap-stop');
      W.dark = { y: scrollY, sh: document.documentElement.scrollHeight, top: s0 ? +s0.getBoundingClientRect().top.toFixed(1) : null }; } }
  }))).observe(document.body, { childList: true });
}"""

# ---------------------------------------------------------------- A: the forced update waits
UPWATCH = r"""() => {
  if(window.__up) return; const U = window.__up = { fired: [], bad: [], frames: 0, scene: 0, lastScene: 0 };
  const sceneUp = () => !!((typeof rankUpScene !== 'undefined' && rankUpScene) || document.body.classList.contains('ru-journey') ||
    document.querySelector('#supernova-cutscene, .rs-spot, .bc-scene, #badge-cutscene, .sf-scene, .ru-veil, .ru-curtain.is-on, #tour-overlay, .nova-talk'));
  window.applyUpdate = function(){ U.fired.push([Math.round(performance.now()), sceneUp()]); };
  const tick = () => { U.frames++; const up = sceneUp(); if(up){ U.scene++; U.lastScene = performance.now(); }
    let blocked = true; try{ blocked = forcedUpdateBlocked(); }catch(e){}
    if(up && !blocked && U.bad.length < 20) U.bad.push([Math.round(performance.now()), (typeof rankUpScene !== 'undefined' && rankUpScene) ? rankUpScene.phase : null,
      document.querySelector('.bc-scene') ? 'bc-scene' : document.querySelector('.rs-spot') ? 'rs-spot' : document.getElementById('supernova-cutscene') ? 'cutscene' : '']);
    requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
}"""
ARM = "()=>{ try{ lastUpdateCheck = 0; updateCheckInFlight = 0; }catch(e){} checkForUpdate(true); }"


def a_journey(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "ranger", "mode": "owed", "owe": 1, "fresh": True})
    pg.evaluate(UPWATCH)
    pg.evaluate("()=>{ showHome(); }")
    armed = {"v": False}

    def tick(pg, st):
        if st["sc"] and not armed["v"]:
            armed["v"] = True; C.newer = True; pg.evaluate(ARM)
    secs = journey(pg, tick=tick)
    pg.wait_for_timeout(6000)
    U = pg.evaluate("()=>({ fired: __up.fired, bad: __up.bad, frames: __up.frames, scene: __up.scene, last: Math.round(__up.lastScene), now: Math.round(performance.now()), info: !!forcedUpdateInfo })")
    ck("A1 the journey ran to its end (%ss) with a newer build advertised mid-way (known to the page: %s)" % (secs, U["info"]), secs is not None and armed["v"] and U["info"], U)
    ck("A1 on every one of %d frames a scene was up, the forced update was held (frames not held: %s)" % (U["scene"], U["bad"][:4]), U["scene"] > 20 and not U["bad"], U["bad"][:6])
    early = [f for f in U["fired"] if f[1]]
    ck("A1 it did not go while any scene was up (%s), and went after the last one ended, within 6s (%s)" % (early, [round((f[0] - U["last"]) / 1000, 1) for f in U["fired"]]),
       not early and len(U["fired"]) >= 1 and 0 <= U["fired"][0][0] - U["last"] <= 6000, U["fired"])
    ck("A1 no page errors", not C.errs, C.errs[:3])
    br.close()


BADGE = r"""() => { const u = unitsInTeachingOrder().filter(x => unitQuestionCount(x) > 0)[0]; window.__bcDone = false;
  playBadgeCaseScene([u], () => { window.__bcDone = true; }, [], {}); return u; }"""


def a_badge(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    pg.evaluate("()=>{ store.rankUpShown = 99; saveStore(); showHome(); }")
    pg.wait_for_timeout(2500)
    pg.evaluate(UPWATCH)
    pg.evaluate(BADGE)
    up = False
    for _ in range(40):
        pg.wait_for_timeout(150)
        if pg.evaluate("()=>!!document.querySelector('.bc-scene')"):
            up = True; break
    C.newer = True; pg.evaluate(ARM)
    t0 = time.time(); gone = None
    while time.time() - t0 < 60:
        pg.wait_for_timeout(250)
        if not pg.evaluate("()=>!!document.querySelector('.bc-scene')"):
            gone = time.time(); break
    pg.wait_for_timeout(5000)
    U = pg.evaluate("()=>({ fired: __up.fired, bad: __up.bad, scene: __up.scene, last: Math.round(__up.lastScene), info: !!forcedUpdateInfo })")
    early = [f for f in U["fired"] if f[1]]
    ck("A2 the badge case scene on Home (up %s, over after %ss): the update known (%s) is held on every frame it is up (not held: %s)" % (up, None if gone is None else round(gone - t0, 1), U["info"], U["bad"][:3]),
       up and gone is not None and U["info"] and U["scene"] > 5 and not U["bad"], U)
    ck("A2 ...it does not go during the scene (%s) and goes once it is over (%s)" % (early, U["fired"]), not early and len(U["fired"]) >= 1, U["fired"])
    ck("A2 no page errors", not C.errs, C.errs[:3])
    br.close()


def a_grace(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    pg.evaluate("()=>{ store.rankUpShown = 99; saveStore(); showHome(); }")
    pg.wait_for_timeout(2500)
    pg.evaluate(UPWATCH)
    C.newer = True
    pg.evaluate(ARM)
    cover = False
    for _ in range(60):
        pg.wait_for_timeout(50)
        if pg.evaluate("()=>!!document.getElementById('pushing-update')"):
            cover = True; break
    pg.wait_for_timeout(200)
    pg.evaluate(BADGE)
    t0 = time.time(); gone = None; seen = False
    while time.time() - t0 < 60:
        pg.wait_for_timeout(250)
        b = pg.evaluate("()=>!!document.querySelector('.bc-scene')")
        seen = seen or b
        if seen and not b:
            gone = time.time(); break
    pg.wait_for_timeout(5000)
    U = pg.evaluate("()=>({ fired: __up.fired })")
    early = [f for f in U["fired"] if f[1]]
    ck("A3 a scene that starts while 'Pushing update' is up (cover %s, scene %s): the reload is not made under it (%s) and is made once it is over (%s)" % (cover, seen, early, U["fired"]),
       cover and seen and not early and len(U["fired"]) >= 1, U["fired"])
    ck("A3 no page errors", not C.errs, C.errs[:3])
    br.close()


def section_a(pw):
    case(a_journey, pw)
    case(a_badge, pw)
    case(a_grace, pw)


# ---------------------------------------------------------------- B: the opening is light
INSTAGE = "function(){ const el = this.nodeType === 1 ? this : this.parentElement; return !!(el && el.closest && el.closest('#stage')); }"


def stage_layers(cdp, layers):
    n, area = 0, 0
    for l in layers:
        if not l.get("drawsContent") or not l.get("backendNodeId"):
            continue
        try:
            o = cdp.send("DOM.resolveNode", {"backendNodeId": l["backendNodeId"]})["object"]
            r = cdp.send("Runtime.callFunctionOn", {"objectId": o["objectId"], "functionDeclaration": INSTAGE, "returnByValue": True})
            if r["result"].get("value"):
                n += 1; area += l["width"] * l["height"]
        except Exception:
            pass
    return n, area


def b_map(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "ranger", "mode": "owed", "owe": 1, "fresh": False})
    pg.evaluate(WATCH)
    cdp = C.ctx.new_cdp_session(pg)
    last = {"l": []}
    cdp.on("LayerTree.layerTreeDidChange", lambda ev: last.__setitem__("l", ev.get("layers") or []))
    cdp.send("DOM.enable"); cdp.send("DOM.getDocument", {"depth": 0}); cdp.send("LayerTree.enable")
    pg.evaluate("()=>{ showHome(); }")
    snaps = {}
    cut0 = {"t": None}

    def tick(pg, st):
        if st["cut"] and cut0["t"] is None:
            cut0["t"] = time.time()
        for tag, at in (("first frames", .4), ("3s in", 3.0)):
            if cut0["t"] and tag not in snaps and time.time() - cut0["t"] >= at and st["cut"]:
                pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                snaps[tag] = stage_layers(cdp, list(last["l"]))
    secs = journey(pg, tick=tick)
    W = pg.evaluate("()=>__w")
    for tag in ("first frames", "3s in"):
        s = snaps.get(tag)
        ck("B1 the cutscene's %s: no composited layer of the road map paints under it (%s layers, %s px2)" % (tag, s and s[0], s and round(s[1])), s is not None and s[0] == 0, s)
    e, d = W.get("exit"), W.get("dark")
    ck("B2 the map is back, drawn, as the cutscene starts to lift (%s), where it stood when the dark came down (%s)" % (e, d),
       bool(e and d) and e["vis"] == "visible" and e["cv"] in ("visible", "auto", None) and abs(e["y"] - d["y"]) <= 1 and abs(e["sh"] - d["sh"]) <= 1 and
       e["top"] is not None and d["top"] is not None and abs(e["top"] - d["top"]) <= 1, (e, d))
    ck("B2 ...and the journey goes on to Home with nothing owed (%ss; one cutscene: %d, its hand-off: %d)" % (secs, W["cuts"], W["veils"]),
       secs is not None and W["cuts"] == 1 and W["veils"] == 1 and pg.evaluate("()=>!!document.querySelector('[data-screen=home]') && !rankUpOwed()"), W)
    ck("B no page errors (journey)", not C.errs, C.errs[:3])
    br.close()


ISOLATE = r"""(cls) => {
  /* the layer alone: one made by the page's own rules (.tier-cutscene .rank-x) in an empty cutscene-classed box on black, nothing
     else of a scene over or under it, white light, fully on, unturned, shrunk to fit the screen */
  document.getElementById('__iso')?.remove();
  const host = document.createElement('div'); host.id = '__iso'; host.className = 'tier-cutscene';
  host.style.cssText = 'position:fixed;left:0;top:0;width:100vw;height:100vh;background:#000;z-index:2147483647;overflow:hidden;opacity:1;transition:none';
  const el = document.createElement('div'); el.className = cls; host.appendChild(el); document.body.appendChild(host);
  const w0 = el.offsetWidth, h0 = el.offsetHeight;
  const s = Math.min(.9 * innerWidth / w0, .9 * innerHeight / h0);
  el.style.setProperty('--mood', '#ffffff'); el.style.transition = 'none'; el.style.opacity = '1'; el.style.transform = 'scale(' + s + ')';
  return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => { const b = el.getBoundingClientRect();
    r({ x: b.left, y: b.top, w: b.width, h: b.height, w0, s }); }))); }"""


def painted_reach(png):
    """the farthest any painted pixel (2 levels over black) reaches from the box's centre, as a share of the half-box, the larger
    of the two axes: 1.0 is a box exactly the size of what it paints"""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("L")
    px = im.load()
    W, H = im.size
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    rx = ry = 0.0
    for y in range(0, H):
        for x in range(0, W):
            if px[x, y] >= 2:
                rx = max(rx, abs(x - cx)); ry = max(ry, abs(y - cy))
    return max(rx / (W / 2.0), ry / (H / 2.0))


def b_depth(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    res = {}
    for cls in ("rank-nebula", "rank-rays"):
        box = pg.evaluate(ISOLATE, cls)
        png = pg.screenshot(clip={"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]})
        res[cls] = (round(painted_reach(png), 3), box["w0"])
    pg.evaluate("()=>document.getElementById('__iso')?.remove()")
    for cls in ("rank-nebula", "rank-rays"):
        r = res.get(cls)
        ck("B3 the cutscene's .%s paints out to %s of its half-box (box %spx): the box is at most 1.25x what it paints" % (cls, r and r[0], r and r[1]), r is not None and r[0] >= .8, r)
    ck("B3 no page errors", not C.errs, C.errs[:3])
    br.close()


SN = r"""() => {
  const keyOf = el => el.tagName + ':' + String(el.getAttribute('class') || '').split(/\s+/).filter(c => /^cosmic-/.test(c)).sort().join(' ');
  const real = document.documentElement.dataset.accent;
  const build = sn => { const had = store.supernovaAchieved, sv = window.saveStore;
    try{ store.supernovaAchieved = sn; window.saveStore = () => {}; document.documentElement.dataset.accent = 'titan'; return buildCosmicHero(true, 'titan'); }
    finally{ store.supernovaAchieved = had; window.saveStore = sv; if(real) document.documentElement.dataset.accent = real; else delete document.documentElement.dataset.accent; } };
  /* what the old reading marks: everything a Supernova build has at its top level that a plain one (a third build) has not */
  const plain = new Set([...build(false).children].map(keyOf));
  const want = [...build(true).children].filter(el => !plain.has(keyOf(el)) && !el.classList.contains('cosmic-hero-ringlayer')).map(keyOf).sort();
  let n = 0; const f = window.buildCosmicHero; window.buildCosmicHero = function(){ n++; return f.apply(this, arguments); };
  try{ playSupernovaCutscene({ from: 'elite', onDone: () => {} }); } finally { window.buildCosmicHero = f; }
  const ov = document.getElementById('supernova-cutscene');
  const hero = ov.querySelector('.rank-after .cosmic-hero-wrap');
  const marked = [...hero.children].filter(el => el.dataset.snReveal).map(keyOf).sort();
  ov.remove();
  return { n, marked, want };
}"""


def b_supernova(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    pg.evaluate("()=>{ store.rankUpShown = 99; saveStore(); showHome(); }")
    pg.wait_for_timeout(2500)
    r = pg.evaluate(SN)
    ck("B4 Supernova's cutscene builds %d planet systems (the one you had and the one you get)" % r["n"], r["n"] == 2, r["n"])
    ck("B4 ...and marks the parts to reveal after the blast exactly as the reading of a third, plain build does (%s)" % (r["marked"],), r["marked"] == r["want"], r)
    ck("B4 no page errors", not C.errs, C.errs[:3])
    br.close()


def section_b(pw):
    case(b_map, pw)
    case(b_depth, pw)
    case(b_supernova, pw)


# ---------------------------------------------------------------- C: a relaunch inside the cutscene
def crash_in_cutscene(pg, br):
    """the journey from Home to a moment into the cutscene's opening, then the page's web process is killed (SIGKILL, by PID:
    no pagehide, no unload - what iOS does to a WebContent process that runs out of memory)"""
    hit = {"t": None}

    def until(pg, st):
        if st["cut"] and hit["t"] is None:
            hit["t"] = time.time()
        return hit["t"] is not None and time.time() - hit["t"] > .6
    r = journey(pg, timeout=360, until=until)
    if r != -1:
        return False
    n = kill_renderers(br)
    time.sleep(2.0)
    return n > 0


AFTER = r"""() => { let log = []; try{ log = JSON.parse(localStorage.getItem('class26e.crashlog') || '[]'); }catch(e){}
  return { home: !!document.querySelector('[data-screen=home]'), owed: !!rankUpOwed(),
    left: [...document.querySelectorAll('#supernova-cutscene, .ru-veil, .ru-ghost, .ru-curtain.is-on, .rs-spot, .ru-asleep')].map(e => e.id || e.className.split(' ')[0]),
    cls: [document.documentElement.className.match(/\bru-\S+/g), document.body.className.match(/\bru-\S+/g)], log: log.slice(-2) }; }"""


def c_once(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "ranger", "mode": "owed", "owe": 1, "fresh": False})
    pg.evaluate("()=>{ showHome(); }")
    crashed = crash_in_cutscene(pg, br)
    C.errs.clear()
    pg = C.open()
    pg.wait_for_timeout(1500)
    a = pg.evaluate(AFTER)
    last = a["log"][-1] if a["log"] else ""
    ck("C1 crashed inside the cutscene's opening (%s) and launched again: Home, the rank still owed, nothing of the journey left on the page (%s)" % (crashed, a),
       crashed and a["home"] and a["owed"] and not a["left"] and not any(a["cls"]), a)
    ck("C1 ...and the page's end log says it ended inside the rank-up cutscene (%s)" % last, bool(re.search(r"ENDED-visible \S*ru-(handoff|cutscene)", last)), a["log"])
    pg.evaluate(WATCH)
    secs = journey(pg)
    pg.wait_for_timeout(8000)
    W = pg.evaluate("()=>__w")
    end = pg.evaluate("()=>({ home: !!document.querySelector('[data-screen=home]'), owed: !!rankUpOwed(), cut: !!document.getElementById('supernova-cutscene'), shown: store.rankUpShown })")
    ck("C2 played again: the cutscene plays once (%d), in full (hand-off %d, whirl %s), the journey lands on Home and owes nothing (%s, %ss), and nothing plays after it" % (
        W["cuts"], W["veils"], W.get("spinSeen"), end, secs), secs is not None and W["cuts"] == 1 and W["veils"] == 1 and W.get("spinSeen") and end["home"] and not end["owed"] and not end["cut"], (W, end))
    ck("C1-2 no page errors after the relaunch", not C.errs, C.errs[:3])
    br.close()


def c_twice(pw):
    br = launch(pw)
    C = Ctx(br, SELF)
    pg = C.open()
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "ranger", "mode": "owed", "owe": 1, "fresh": False})
    pg.evaluate("()=>{ showHome(); }")
    ok1 = crash_in_cutscene(pg, br)
    pg = C.open()
    ok2 = crash_in_cutscene(pg, br)
    C.errs.clear()
    pg = C.open()
    pg.evaluate(WATCH)
    secs = journey(pg)
    pg.wait_for_timeout(6000)
    W = pg.evaluate("()=>__w")
    end = pg.evaluate("()=>({ home: !!document.querySelector('[data-screen=home]'), owed: !!rankUpOwed(), cut: !!document.getElementById('supernova-cutscene') })")
    ck("C3 ended inside the cutscene twice in a row (%s, %s): the next launch plays it once (%d) as the still scene (still %s; hand-off %d, whirl %s), lands on Home and owes nothing (%s, %ss)" % (
        ok1, ok2, W["cuts"], W.get("stillSeen"), W["veils"], W.get("spinSeen"), end, secs),
       ok1 and ok2 and secs is not None and W["cuts"] == 1 and W.get("stillSeen") and W["veils"] == 0 and not W.get("spinSeen") and end["home"] and not end["owed"], (W, end))
    ck("C3 no page errors", not C.errs, C.errs[:3])
    br.close()


def section_c(pw):
    case(c_once, pw)
    case(c_twice, pw)


def main():
    print("serving %s (build %s)" % (SELF.src, SELF.build), flush=True)
    with sync_playwright() as pw:
        if "A" in ONLY:
            print("A. the forced update waits for every scene", flush=True); section_a(pw)
        if "B" in ONLY:
            print("B. the cutscene's opening is light", flush=True); section_b(pw)
        if "C" in ONLY:
            print("C. a relaunch inside the cutscene is harmless", flush=True); section_c(pw)
    print("\n%s" % ("ALL PASS" if not FAILS else "%d FAILED:\n  - %s" % (len(FAILS), "\n  - ".join(FAILS))), flush=True)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
