"""Shared by tools/check-b384-switchfx.py and tools/record-b384-switch.py: drive the REAL class switch (Police Academy <-> Fire Code)
and watch it frame by frame.

Two witnesses, both on the wall clock so they line up:
  * a CDP screencast (the compositor's own frames and timestamps): what a person SEES - each frame's average light, its edges, a
    picture of it;
  * an in-page rAF log, kept across the reload in sessionStorage (the old page logs until it is gone, the new page carries on): what
    the DOM was doing in each of its frames - the cover, the splash, the tab bar's items, whether the planet and greeting were
    built, the status bar's colour.
The owner's situation is seeded (an account in both classes), the page is served as GitHub Pages serves it (max-age, 304) from a
profile on disk so a reload revalidates the 10MB page rather than fetching it again, and Firebase is stood in by an in-memory
Firestore (the CDN is blocked in the sandbox).
"""
import base64, functools, http.server, io, json, os, re, shutil, socket, sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-a2hs.py"), encoding="utf-8").read().split('\nprint("check-b384-a2hs against"')[0]
G = {"__file__": os.path.join(HERE, "check-b384-a2hs.py"), "__name__": "b384sw"}
exec(_src, G)
SRC, SRC_PATH, BUILD, CHROME, ROOT = G["SRC"], G["SRC_PATH"], G["BUILD"], G["CHROME"], G["ROOT"]
FAKE, STANDALONE, UA = G["FAKE"], G["STANDALONE"], G["UA"]

SEEN = ("['class26e.freshstart','class26e.unithold.tip','class26e.getstarted','class26e.frame.ok','class26e.daily.seen','class26e.savecode.card',"
        "'class26e.savecode.asked','class26e.a2hs'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));"
        "localStorage.setItem('class26e.intro.seen','99');")
SEEN_IFC = ("['class26e.ifc.freshstart','class26e.ifc.daily.seen','class26e.ifc.savecode.card','class26e.ifc.savecode.asked','class26e.ifc.getstarted',"
            "'class26e.ifc.a2hs','class26e.ifc.unithold.tip'].forEach(k=>localStorage.setItem(k,'1'));")

def account(name, pub, pts=0, correct=0, **extra):
    d = {"firstName": name, "avatarChar": "ghost", "onboardingComplete": True, "publicId": pub, "leaderboardOptIn": True,
         "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
         "seenMainMenuTour": True, "seenClassTip": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
         "seenRankingsTour": True, "seenAppearanceTour": True, "badgeBandsVersion": 99,
         "lifetime": {"points": pts, "answered": correct + 10, "correct": correct}}
    d.update(extra)
    return d

# the owner's situation: the academy in Silver wearing Void, Fire Code in its own default, an account in both classes
SW = account("Riley Switch", "xph5b57jbp5a", 900, 250, classes=["academy", "ifc"], rankFloor=2, avatarChar="voidwalker",
             theme={"accent": "ranger", "accentAt": 1}, mysteryColorsFound={"red": True, "orange": True, "yellow": True})
SWI = dict(SW); SWI.pop("classes"); SWI.pop("rankFloor"); SWI["mysteryColorsFound"] = {}; SWI["lifetime"] = {"points": 50, "answered": 10, "correct": 5}
SWI["avatarChar"] = "ghost"
CODE = "TEST-SWCH"

def seed_js(reduce=False):
    sw, swi = dict(SW), dict(SWI)
    if reduce:
        sw["theme"] = dict(sw["theme"], reduceMotion=True); swi["theme"] = {"accent": "ink", "accentAt": 0, "reduceMotion": True}
    return (SEEN + SEEN_IFC + "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); "
            "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s'); localStorage.setItem('class26e.ifc.drill.v1', %s);"
            % (json.dumps(json.dumps(sw)), CODE, json.dumps(json.dumps(swi))))

# Every rAF frame of the page: what the DOM is, on the wall clock. window.__fx is the log; the old page's goes to sessionStorage as it
# is left (pagehide) and the next page picks it up first.
LOGGER = r"""(()=>{ if(location.protocol !== 'http:') return;
  let log = []; try{ log = JSON.parse(sessionStorage.getItem('__fx') || '[]'); }catch(e){}
  window.__fx = log; const t0 = Date.now();
  const op = e => { if(!e) return null; const c = getComputedStyle(e); return c.display === 'none' || c.visibility === 'hidden' ? 0 : +(+c.opacity).toFixed(3); };
  const flush = () => { try{ sessionStorage.setItem('__fx', JSON.stringify(window.__fx.slice(-1500))); }catch(e){} };
  addEventListener('pagehide', flush);
  // events that do not wait for a frame: a main thread busy with the boot's tail drops rAF frames for most of a lift, and a lift that
  // no frame sampled is still a lift. 'lift' = the splash gets splash-hide; 'fadeend' = its opacity transition ends; 'gone' = it is removed;
  // 'coverend' = the old page's cover finished fading in; 'rise' = body gets class-rise
  const mark = k => { try{ window.__fx.push({ mark: k, t: Date.now() }); }catch(e){} };
  const seen = {};
  new MutationObserver(ms => { for(const m of ms){
    const t = m.target;
    if(m.type === 'attributes' && t && t.id === 'splashscreen' && t.classList.contains('splash-hide') && !seen.lift){ seen.lift = 1; mark('lift'); }
    if(m.type === 'attributes' && t && t === document.body && t.classList.contains('class-rise') && !seen.rise){ seen.rise = 1; mark('rise'); }
    for(const n of m.removedNodes){ if(n && n.id === 'splashscreen' && !seen.gone){ seen.gone = 1; mark('gone'); } }
  } }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  document.addEventListener('transitionend', e => {
    const t = e.target;
    if(t && t.id === 'splashscreen' && e.propertyName === 'opacity' && !seen.fadeend && t.classList.contains('splash-hide')){ seen.fadeend = 1; mark('fadeend'); }
    if(t && t.id === 'class-switch-loader' && e.propertyName === 'opacity' && !seen.coverend){ seen.coverend = 1; mark('coverend'); }
  }, true);
  const tick = () => {
    try{
      const d = document, $ = s => d.querySelector(s);
      const tabs = [...d.querySelectorAll('.bottomtabs .bottomtab')].filter(e => !e.hidden && getComputedStyle(e).display !== 'none');
      const bt = $('.bottomtabs'), home = $('#stage [data-screen="home"]'), sp = d.getElementById('splashscreen');
      const cov = d.getElementById('class-switch-loader') || d.getElementById('class-cover');
      const hero = $('#stage .cosmic-hero-wrap'), greet = $('#stage .hometitle-wrap'), start = $('#nextbtn');
      const tc = d.getElementById('themecolor');
      const g = cov ? cov.querySelector('#csl-group') : (sp ? sp.querySelector('#splash-group') : null);
      const gs = sp ? sp.querySelector('#splash-group') : null;
      const labels = tabs.map(e => (e.querySelector('.bottomtab-label') || e).textContent.trim()).join('|');
      const r = e => { if(!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; };
      window.__fx.push({ t: Date.now(), cls: window.NOVA_CLASS || null, sheet: !!$('.class-bubble-wrap.is-open'), cover: cov ? cov.id : null, coverOp: op(cov),
        splash: sp ? op(sp) : null, sd: sp ? parseFloat(getComputedStyle(sp).transitionDuration) || 0 : null, splashHide: sp ? sp.classList.contains('splash-hide') : null, arrive: d.documentElement.classList.contains('class-arrive'),
        pre: d.documentElement.classList.contains('class-arrive-pre'),
        tabs: tabs.length, tabsOp: bt ? op(bt) : null, tabsBox: bt ? r(bt) : null, tabsHidden: bt ? bt.hidden : null, home: !!home, hero: !!hero, heroBox: r(hero), heroOp: hero ? op(hero) : null,
        greet: !!greet, greetOp: greet ? op(greet) : null, start: !!start, startBox: r(start), stage: !!d.getElementById('stage') && d.getElementById('stage').children.length,
        tc: tc ? tc.content : null, accent: d.documentElement.dataset.accent || 'ink',
        grp: g ? op(g) : null, grpScale: gs ? getComputedStyle(gs).scale : null, labels,
        banner: !!d.getElementById('classback-banner'), greetNova: !!d.getElementById('nova-class-greet') });
    }catch(e){}
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();"""

DEVS = {
    # name: (w, h, dpr, mobile/touch, standalone, ua)
    "phone": (440, 956, 1, True, True, "iphone"),
    "se": (375, 667, 1, True, True, "iphone"),
    "laptop": (1440, 900, 1, False, False, "desktop"),
}

class Server:
    def __init__(self, src_path=None, no_reload=False):
        src_path = src_path or SRC_PATH
        self.root = ROOT
        if no_reload or src_path != os.path.join(ROOT, "index.html"):
            self.root = tempfile.mkdtemp(prefix="b384sw-root-")
            for n in os.listdir(ROOT):
                if n != "index.html" and not n.startswith("."): os.symlink(os.path.join(ROOT, n), os.path.join(self.root, n))
            txt = open(src_path, encoding="utf-8").read()
            if no_reload:   # a reload that never happens (blocked, or hung on a connection that never answers): the switch's own call is a no-op
                old = "requestAnimationFrame(() => requestAnimationFrame(() => location.reload()))"
                assert old in txt
                txt = txt.replace(old, "requestAnimationFrame(() => requestAnimationFrame(() => { window.__reloadCalls = (window.__reloadCalls || 0) + 1; }))")
            open(os.path.join(self.root, "index.html"), "w", encoding="utf-8").write(txt)
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        class GH(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
            def end_headers(self):
                self.send_header("Cache-Control", "max-age=600"); super().end_headers()
        http.server.ThreadingHTTPServer.handle_error = lambda *a: None
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), functools.partial(GH, directory=self.root))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = "http://127.0.0.1:%d/index.html" % self.port
    def close(self): self.srv.shutdown()

def lum_of(jpeg, size=(36, 80)):
    """average light and edge colours of one frame"""
    from PIL import Image
    import numpy as np
    im = Image.open(io.BytesIO(jpeg)).convert("RGB")
    a = np.asarray(im.resize(size)).astype(float)
    w = a[..., 0] * .2126 + a[..., 1] * .7152 + a[..., 2] * .0722
    edge = np.concatenate([a[:2].reshape(-1, 3), a[-2:].reshape(-1, 3), a[:, :1].reshape(-1, 3), a[:, -1:].reshape(-1, 3)]).mean(axis=0)
    return {"lum": float(w.mean()), "max": float(w.max()), "edge": [float(x) for x in edge], "top": [float(x) for x in a[:2].reshape(-1, 3).mean(axis=0)],
            "bot": [float(x) for x in a[-2:].reshape(-1, 3).mean(axis=0)]}

def ev(pg, js, arg=None, default=None):
    for _ in range(4):
        try: return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "navigation" in str(e).lower() or "Target closed" in str(e):
                pg.wait_for_timeout(300); continue
            raise
    return default

class Session:
    """one device, one profile on disk, the owner's account in both classes, at rest on Home"""
    def __init__(self, pw, server, dev="phone", reduce_motion=False, extra_init=""):
        self.dev = dev; w, h, dpr, touch, standalone, ua = DEVS[dev]
        self.w, self.h = w, h
        self.prof = tempfile.mkdtemp(prefix="b384sw-prof-")
        kw = dict(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=touch, user_agent=UA[ua])
        if reduce_motion: kw["reduced_motion"] = "reduce"
        self.ctx = pw.chromium.launch_persistent_context(self.prof, executable_path=CHROME, **kw)
        self.ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps({"progress": {CODE: SW, CODE + "__ifc": SWI}}))
        self.ctx.add_init_script(FAKE)
        if standalone: self.ctx.add_init_script(STANDALONE)
        self.ctx.add_init_script("(()=>{ try{ if(location.protocol !== 'http:' || sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + seed_js(reduce_motion) + " }catch(e){} })()")
        self.ctx.add_init_script(LOGGER)
        if extra_init: self.ctx.add_init_script(extra_init)
        self.pg = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        self.errs = []
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)[:200]))
        self.pg.on("console", lambda m: self.errs.append("console: " + m.text[:200]) if m.type == "error" and "Failed to load resource" not in m.text and "net::" not in m.text else None)
        self.cdp = self.ctx.new_cdp_session(self.pg)
        self.frames = []; self.rec = False
        self.cdp.on("Page.screencastFrame", self._frame)
        self.server = server
    def _frame(self, ev):
        try: self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception: pass
        if self.rec: self.frames.append((ev["metadata"].get("timestamp") or time.time(), base64.b64decode(ev["data"]), time.time()))
    def boot(self, settle=5000):
        self.pg.goto(self.server.url); self.pg.wait_for_timeout(settle)
        ev(self.pg, "()=>document.getElementById('splashscreen')?.remove()")
        # a while on Home so Fire Code's questions are in the cache, as on a phone that has been open a while
        self.warmed = None
        t0 = time.time()
        while time.time() - t0 < 40:
            if ev(self.pg, "()=>performance.getEntriesByType('resource').some(e=>/ifc\\/bank\\.js/.test(e.name) && e.responseEnd > 0)"): self.warmed = True; break
            self.pg.wait_for_timeout(250)
        # the reward spotlights and banners a launch owes (the owner's account has a secret flare to announce), tapped away as a person does
        calm = 0
        for _ in range(30):
            if ev(self.pg, "()=>!!document.querySelector('.rs-spot, .rs-fly, #nova-intro, .nova-talk, #tour-overlay')"):
                calm = 0
                try: self.tap(".rs-spot")
                except Exception: pass
                self.pg.wait_for_timeout(900)
            else:
                calm += 1
                if calm >= 3: break
                self.pg.wait_for_timeout(500)
        ev(self.pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner,#classback-banner').forEach(e=>e.remove()); }")
        self.pg.wait_for_timeout(800)
        return self
    def tap(self, sel):
        """a real tap (a touch on a phone, the mouse on a laptop) at the middle of the element, as the app's own checks do; returns when"""
        JS = "(s)=>{ const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"
        c = None
        for _ in range(60):     # still: the same place twice, 120ms apart (the bubble pulses and a list slides in)
            a = ev(self.pg, JS, sel); self.pg.wait_for_timeout(120); b = ev(self.pg, JS, sel)
            if a and b and abs(a[0] - b[0]) < .5 and abs(a[1] - b[1]) < .5: c = b; break
        if not c: raise RuntimeError("no still element " + sel)
        if DEVS[self.dev][3]:
            self.cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c[0], "y": c[1]}]})
            time.sleep(.08)
            t = time.time()      # the tap is the lift of the finger: that is when the app's click runs
            self.cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        else:
            self.cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": c[0], "y": c[1]})
            self.cdp.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": c[0], "y": c[1], "button": "left", "clickCount": 1})
            t = time.time()
            self.cdp.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": c[0], "y": c[1], "button": "left", "clickCount": 1})
        return t
    def throttle(self, cpu=1):
        self.cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu})
    def start_rec(self):
        self.frames = []; self.rec = True
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 70, "everyNthFrame": 1})
    def stop_rec(self):
        self.rec = False
        try: self.cdp.send("Page.stopScreencast")
        except Exception: pass
    def switch(self, to, via="sheet", wait_after=2500, limit=30):
        """tap the class button and the class named; run until the new class's Home is up and quiet. -> dict"""
        pg = self.pg
        ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner,#classback-banner').forEach(e=>e.remove()); sessionStorage.removeItem('__fx'); window.__fx.length = 0; }")
        pg.wait_for_timeout(300)
        self.start_rec()
        t_open = time.time()
        if via == "sheet":
            self.tap(".class-bubble"); pg.wait_for_timeout(900)
            t_tap = self.tap(".class-stack-item.is-" + to)
        elif via in ("settings", "enter"):
            # a programmatic switch from Settings (what a catalog join, a leave, a sign-in or a link run): the screen is Settings, not Home
            ev(pg, "()=>{ showAppearance(); }"); pg.wait_for_timeout(1200)
            t_tap = time.time()
            ev(pg, "(a)=>{ if(a.via==='enter') enterAccountClass('signin'); else switchClass(a.to); }", {"via": via, "to": to})
        else:
            raise ValueError(via)
        t_end = None
        while time.time() - t_tap < limit:
            st = ev(pg, "()=>({ cls: window.NOVA_CLASS, home: !!document.querySelector('#stage [data-screen=\"home\"]'), sp: !!document.getElementById('splashscreen'), cv: !!document.getElementById('class-switch-loader') || !!document.getElementById('class-cover') })")
            if st and st["cls"] == to and st["home"] and not st["sp"] and not st["cv"]:
                t_end = t_end or time.time()
                if time.time() - t_end > wait_after / 1000: break
            pg.wait_for_timeout(100)
        self.stop_rec()
        # the screencast's clock is not the wall clock's: shift it by the least delay between a frame's stamp and its arrival
        off = min(rc - ts for ts, _, rc in self.frames) if self.frames else 0
        frames = [(ts + off, jpg) for ts, jpg, rc in self.frames]
        log = ev(pg, "()=>window.__fx.slice()", default=[]) or []
        return {"t_open": t_open, "t_tap": t_tap, "log": log, "frames": frames, "to": to, "off": off}
    def close(self):
        try: self.ctx.close()
        except Exception: pass
        shutil.rmtree(self.prof, ignore_errors=True)

def analyse(run):
    """per-frame light, on the wall clock, from the tap (ms)"""
    t_tap = run["t_tap"]; out = []
    for ts, jpg in run["frames"]:
        m = lum_of(jpg); m["dt"] = round((ts - t_tap) * 1000); out.append(m)
    return out

def contact_sheet(run, path, step=1, cols=12, tw=150, start_ms=-900, end_ms=None, label=True):
    from PIL import Image, ImageDraw
    t_tap = run["t_tap"]
    fr = [(round((ts - t_tap) * 1000), jpg) for ts, jpg in run["frames"] if round((ts - t_tap) * 1000) >= start_ms and (end_ms is None or (ts - t_tap) * 1000 <= end_ms)]
    fr = fr[::step]
    if not fr: return 0
    im0 = Image.open(io.BytesIO(fr[0][1])); th = int(tw * im0.height / im0.width)
    rows = (len(fr) + cols - 1) // cols
    S = Image.new("RGB", (cols * tw, rows * (th + (12 if label else 0))), (40, 0, 40))
    d = ImageDraw.Draw(S)
    for k, (dt, jpg) in enumerate(fr):
        im = Image.open(io.BytesIO(jpg)).convert("RGB").resize((tw, th))
        x, y = (k % cols) * tw, (k // cols) * (th + (12 if label else 0))
        S.paste(im, (x, y + (12 if label else 0)))
        if label: d.text((x + 2, y), "%d" % dt, fill=(255, 255, 0))
    S.save(path); return len(fr)

def pick_sheet(run, times, path, cols=10, tw=150):
    """the frame nearest each time (ms from the tap), labelled - for reading a transition at the moments that matter"""
    from PIL import Image, ImageDraw
    t_tap = run["t_tap"]; fr = [(round((ts - t_tap) * 1000), jpg) for ts, jpg in run["frames"]]
    if not fr: return 0
    im0 = Image.open(io.BytesIO(fr[0][1])); th = int(tw * im0.height / im0.width)
    rows = (len(times) + cols - 1) // cols
    S = Image.new("RGB", (cols * tw, rows * (th + 12)), (40, 0, 40)); d = ImageDraw.Draw(S)
    for k, t in enumerate(times):
        dt, jpg = min(fr, key=lambda x: abs(x[0] - t))
        im = Image.open(io.BytesIO(jpg)).convert("RGB").resize((tw, th))
        x, y = (k % cols) * tw, (k // cols) * (th + 12)
        S.paste(im, (x, y + 12)); d.text((x + 2, y), "%d(%d)" % (t, dt), fill=(255, 255, 0))
    S.save(path); return len(times)

def timeline(run, keys=("cover", "coverOp", "splash", "arrive", "pre", "tabs", "home", "hero", "greet", "sheet", "cls", "stage", "tc", "banner")):
    """the in-page log's changes, from the tap: (ms, {changed fields})"""
    t_tap = run["t_tap"]; prev = None; out = []
    for e in [x for x in run["log"] if "mark" not in x]:
        cur = {k: (round(e[k], 1) if isinstance(e[k], float) else e[k]) for k in keys}
        if cur != prev:
            out.append((round((e["t"] / 1000 - t_tap) * 1000), {k: v for k, v in cur.items() if prev is None or prev.get(k) != v}))
            prev = cur
    return out
