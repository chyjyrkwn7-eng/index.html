#!/usr/bin/env python3
"""Videos of what a NEW person sees, for the owner to watch on a phone: the Home Screen app on an iPhone 17 Pro Max (440x956),
real touches, the app's own sound, a smooth 30 fps on the video's own clock.

  python3 tools/record-b384-newuser.py SCENARIO OUT.mp4 [--dpr 2] [--silent] [--gap 0.9] [--max-mb 24]
  SCENARIO:
    startup         a fresh install opened from its icon: the splash, the Get Started page read section by section (every clip
                    playing at its own speed, the rank ladder lighting), Let's get started, Welcome
    signup-academy  a fresh install: Get Started, Let's get started, Welcome, I'm new here, New to Nova?, Select your classes
                    (Police Academy), the enroll confirm, GENERATING PROFILE, Nova (your name, your partner, the save-your-code
                    card), the main menu's tips, Home
    signup-ifc      the same into Fire Code: the confirm, Enroll in Fire Code, Choose my IFC PDF (the owner's book:
                    IFC_BOOK=<2021 IFC PDF> PDFJS_DIR=<unpacked pdfjs-dist 5.4.149>), the analysis to Success, Continue, Nova's
                    first half, the move into Fire Code, his second half, the tips, Home
    switch          an account in both classes on the academy's Home: the class button, Fire Code, Fire Code's Home; the class
                    button again, Police Academy, the academy's Home

HOW. record-sound.py's machinery (its offline-audio engine and its page clock), with the clock installed by an INIT script
(record-signup.py's way), so the splash, every screen and every animation run on the video's clock frame by frame whatever the
machine's load. On top of it, here:
  * TOUCH: each tap is a CDP touchStart, two frames, touchEnd at the element's middle (a finger, not a mouse), on a mobile
    viewport with touch, the iPhone's user agent and navigator.standalone (the installed app). A soft ring shows where the
    finger landed - drawn only in the recording (it is not in the app). Typing is key presses (no on-screen keyboard here).
  * THE GET STARTED CLIPS: a <video> plays on the media clock, not the page's, so play()/pause() are taken over and each playing
    clip is SEEKED one frame per video frame (looping as the app asks) - every clip plays at its own 1x in the video.
  * THE RELOADS (a class switch, a Fire Code sign-up): the page is reloaded for real. The old page's sound is rendered as the
    switch starts; the new page's Date continues from the old one's plus --gap seconds (the reload's own time; the old page's
    last frame - the cover - is held that long, as a phone holds it), so the switch's own timing reads true across the reload.
    Each page's sound is laid at its place on the video's timeline.
  * No Firebase (the CDN is blocked in the sandbox): the sign-ups run on check-vroom's in-memory Firestore, the switch on the
    device's own stores. The names typed are made-up ones. Chromium has no safe areas, blur-behind, haptics or soft keyboard:
    insets are 0 (as every recorder here), the rest is what Chromium draws.
A log beside the MP4 (OUT.log.json): the marks (what was on screen when), every sound played, the page errors."""
import base64, io, json, os, re, socket, subprocess, sys, tempfile, threading, time, wave, functools, http.server, mimetypes
HERE = os.path.dirname(os.path.abspath(__file__))


def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


if len(sys.argv) < 3:
    sys.exit(__doc__)
SCEN, OUT = sys.argv[1], os.path.abspath(sys.argv[2])
DPR = int(arg("--dpr", "2"))
SOUND = "--silent" not in sys.argv
GAP = float(arg("--gap", "0.9"))
MAX_MB = float(arg("--max-mb", "24"))
BOOK = os.environ.get("IFC_BOOK", "")
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"

# record-sound's machinery: its sound, clock, Firestore stand-ins and the Nova / tips walk
sys.argv = [os.path.join(HERE, "record-sound.py"), "nova-new", OUT, "--device", "phone", "--mode", "installed"]
G = {"__file__": os.path.join(HERE, "record-sound.py"), "__name__": "record_newuser"}
exec(open(os.path.join(HERE, "record-sound.py"), encoding="utf-8").read().split("\nSCENARIOS = {")[0], G)
FPS, SR, FF, CHROME, ROOT = G["FPS"], G["SR"], G["FF"], G["CHROME"], G["ROOT"]
W, H = 440, 956

# ------------------------------------------------------------------ in the page
# play()/pause() only say what the app wants; the clip is seeked a frame at a time (STEP)
MEDIA = r"""(()=>{ window.__nST = window.setTimeout.bind(window);
  const P = HTMLMediaElement.prototype;
  P.play = function(){ this.__vplay = true; return Promise.resolve(); };
  P.pause = function(){ this.__vplay = false; };
})();"""
# the page's Date carries on across a reload: the old page leaves its time (+ the reload's) for the next one
DATE_CARRY = r"""(()=>{ const C = window.__clk; if(!C) return;
  let base = null; try{ base = +sessionStorage.getItem('__vdate') || null; sessionStorage.removeItem('__vdate'); }catch(e){}
  if(base){ const t0 = C.t; Date.now = () => Math.round(base + (C.t - t0)); }
  addEventListener('pagehide', () => { try{ sessionStorage.setItem('__vdate', String(Date.now() + (window.__gapMs || 0))); }catch(e){} });
})();"""
# where a finger lands (the recording only)
RING = r"""addEventListener('DOMContentLoaded', () => {
  const s = document.createElement('style');
  s.textContent = '.__tap{position:fixed;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;border:2px solid rgba(255,255,255,.8);'
    + 'background:rgba(255,255,255,.2);z-index:2147483647;pointer-events:none;animation:__tap .5s ease-out forwards}'
    + '@keyframes __tap{from{transform:scale(.55);opacity:.95}to{transform:scale(1.25);opacity:0}}';
  document.body.appendChild(s);
  addEventListener('pointerdown', e => { const d = document.createElement('div'); d.className = '__tap'; d.style.left = e.clientX + 'px';
    d.style.top = e.clientY + 'px'; document.body.appendChild(d); setTimeout(() => d.remove(), 600); }, true);
});"""
STEP = r"""async (dt) => {
  const t = await __clk.advance(dt);
  const vs = [...document.querySelectorAll('video')].filter(v => v.__vplay && v.readyState >= 1 && isFinite(v.duration) && v.duration > 0);
  if(vs.length){
    await Promise.all(vs.map(v => new Promise(res => {
      let nt = v.currentTime + dt / 1000;
      if(nt >= v.duration - .001) nt = v.loop ? nt % v.duration : v.duration;
      let done = false; const fin = () => { if(done) return; done = true; v.removeEventListener('seeked', fin); res(); };
      v.addEventListener('seeked', fin); window.__nST(fin, 600);
      try{ v.currentTime = nt; }catch(e){ fin(); }
    })));
    await new Promise(r => __nraf(() => __nraf(r)));
  }
  let fake = false;
  if(window.__wantFake && !window.__fk && typeof __stub === 'function' && !document.getElementById('splashscreen')){
    try{ __stub(); fbDb = window.__fakeDb; if(window.__osr0) onSnapshotResilient = window.__osr0; window.__fk = 1; fake = true; }catch(e){}
  }
  return [t, document.documentElement.classList.contains('class-switching'), fake, window.__docId];
}"""
LOGP = G["LOG_PLAYS"].replace("if(window.__logged) return;", "if(window.__logged || typeof NovaSound === 'undefined' || !window.__rec) return;")
assert LOGP != G["LOG_PLAYS"]
SCREEN = "() => { const e = document.querySelector('#stage [data-screen]'); return e ? e.dataset.screen : null; }"


def navish(e):
    s = str(e)
    return any(k in s for k in ("Execution context was destroyed", "navigation", "Navigation", "Target closed", "Cannot find context", "frame was detached"))


class NRec:
    def __init__(self, pw, seed_js="", fake=True, route_book=False):
        self.br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required",
                                                                     "--force-device-scale-factor=%d" % DPR])
        self.ctx = self.br.new_context(viewport={"width": W, "height": H}, device_scale_factor=DPR, is_mobile=True, has_touch=True,
                                       user_agent=G["IPHONE_SAFARI_UA"])
        self.ctx.add_init_script(G["STANDALONE_JS"])
        self.ctx.add_init_script(G["FAKE_FS"])
        if seed_js:
            self.ctx.add_init_script("(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); "
                                     + seed_js + " }catch(e){} })()")
        self.ctx.add_init_script("window.__docId = Math.random().toString(36).slice(2); window.__wantFake = %s; window.__gapMs = %d;" % ("true" if fake else "false", int(GAP * 1000)))
        self.ctx.add_init_script(G["REC_AUDIO"].replace("%BUDGET%", "480"))
        self.ctx.add_init_script(MEDIA)
        self.ctx.add_init_script("(" + G["CLOCK"] + ")();")
        self.ctx.add_init_script(DATE_CARRY)
        self.ctx.add_init_script(RING)
        if route_book:
            def h(route, req):
                rel = req.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]
                p = PDFJS + rel
                if not os.path.exists(p): return route.fulfill(status=404, body="")
                ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
                route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
            self.ctx.route("**/pdfjs-dist@5.4.149/**", h)
        pg = self.pg = self.ctx.new_page()
        self.errs = []
        pg.on("pageerror", lambda e: self.errs.append(str(e)[:240]))
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=G["BODY"]))
        pg.route("**/firebasejs/**", lambda r: r.abort())
        self.cdp = self.ctx.new_cdp_session(pg)
        self.times, self.marks, self.pages, self.plays = [], [], [], []
        self.capture = True
        self.ff = None
        self.last_jpg = None
        self.vpath = OUT + ".video.mp4"

    # ---- the clip
    def open(self, url):
        self.ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "14", "-preset", "veryfast", "-r", str(FPS), self.vpath],
                                   stdin=subprocess.PIPE)
        self.pg.goto(url, wait_until="commit")
        self.ready()

    def ready(self):
        """the first document: wait for its clock and body"""
        t0 = time.time()
        while time.time() - t0 < 120:
            try:
                if self.pg.evaluate("() => !!window.__clk && !!document.body"): break
            except Exception:
                pass
            time.sleep(.03)

    def step(self):
        for _ in range(200):
            try:
                return self.pg.evaluate(STEP, 1000 / FPS)
            except Exception as e:
                if not navish(e): raise
                time.sleep(.03)
        raise RuntimeError("the page would not step")

    def frame(self):
        t, switching, fake, doc = self.step()
        if not self.pages or self.pages[-1]["doc"] != doc:
            if self.pages:
                old = self.pages[-1]
                if SOUND and not old["rendered"]: self.mark("!! the sound of the page before was not rendered before it went")
                old["rendered"] = True
                if self.capture and self.last_jpg:
                    for _ in range(int(round(GAP * FPS))):     # the old page's last frame (the cover), held while the page reloads
                        self.ff.stdin.write(self.last_jpg); self.times.append(None)
                self.mark("a new page (the reload held %.1fs)" % GAP)
            self.pages.append({"doc": doc, "frame0": len(self.times), "clk0": t, "clk1": t, "rendered": False})
        pgi = self.pages[-1]
        pgi["clk1"] = t
        try: self.pg.evaluate(LOGP)
        except Exception: pass
        if fake: self.mark("cloud stand-in on")
        if switching and not pgi["rendered"]:
            self.render_audio(pgi, tail=2.0)
        if not self.capture:
            pgi["frame0"] = len(self.times); pgi["clk0"] = t
            return
        jpg = base64.b64decode(self.send("Page.captureScreenshot", {"format": "jpeg", "quality": 90})["data"])
        self.last_jpg = jpg
        self.ff.stdin.write(jpg)
        self.times.append(t)

    def send(self, method, params):
        """CDP on the page; a reload into a new renderer detaches the session, so it is opened again"""
        for k in range(5):
            try:
                return self.cdp.send(method, params)
            except Exception as e:
                m = str(e)
                if k == 4 or not any(w in m for w in ("Not attached", "Target closed", "detached", "Unable to capture")): raise
                time.sleep(.25)
                if "Unable to capture" not in m: self.cdp = self.ctx.new_cdp_session(self.pg)

    def frames(self, n):
        for _ in range(int(n)): self.frame()

    def wait(self, sec):
        self.frames(round(sec * FPS))

    def js(self, expr, a=None):
        for _ in range(40):
            try:
                return self.pg.evaluate(expr, a) if a is not None else self.pg.evaluate(expr)
            except Exception as e:
                if not navish(e): raise
                self.frame()
        raise RuntimeError("js: no page")

    def until(self, cond, max_sec, then=0.0):
        for _ in range(int(max_sec * FPS)):
            if self.js("() => !!(" + cond + ")"): break
            self.frame()
        else:
            self.mark("!! waited %ss for %s" % (max_sec, cond[:90]))
        self.wait(then)

    def mark(self, what):
        self.marks.append((round(len(self.times) / FPS, 2), what))
        print("  %6.1fs  %s" % (len(self.times) / FPS, what), flush=True)

    def center(self, sel_js):
        return self.js("() => { const el = (" + sel_js + "); if(!el) return null; const r0 = el.getBoundingClientRect();"
                       " if(r0.bottom > innerHeight || r0.top < 0) el.scrollIntoView({ block: 'center' });"
                       " const r = el.getBoundingClientRect(); if(!r.width || !r.height) return null; return [r.left + r.width / 2, r.top + r.height / 2]; }")

    def tap(self, sel_js, max_sec=8, hold=2):
        """a finger at the middle of the element once it has stopped moving; then `hold` frames"""
        prev = None
        for _ in range(int(max_sec * FPS)):
            xy = self.center(sel_js)
            if xy and prev and abs(xy[0] - prev[0]) < .5 and abs(xy[1] - prev[1]) < .5:
                # down and up 60ms apart in REAL time: the browser's own gesture detector times a press on the wall clock, and a
                # finger held over two recorded frames on a loaded machine is a long press (no click)
                self.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": xy[0], "y": xy[1], "radiusX": 6, "radiusY": 6, "force": 1}]})
                time.sleep(.06)
                self.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                self.frames(hold)
                return True
            prev = xy
            self.frame()
        self.mark("!! no tap target: " + sel_js[:90])
        return False

    def type(self, text, per=.11):
        for ch in text:
            self.pg.keyboard.type(ch); self.wait(per)

    def glide(self, scroller_js, to_js, sec=.9):
        """an eased scroll of an element scroller to a position, a frame at a time (a finger's drag, without the fling)"""
        y0, y1 = self.js("() => { const s = (" + scroller_js + "); const y1 = (" + to_js + "); return [s.scrollTop, Math.max(0, Math.min(s.scrollHeight - s.clientHeight, y1))]; }")
        n = max(1, int(sec * FPS))
        for k in range(1, n + 1):
            u = k / n; e = 2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2
            self.js("(y) => { const s = (" + scroller_js + "); s.scrollTop = y; }", y0 + (y1 - y0) * e)
            self.frame()

    # ---- the sound of each page, laid on the timeline
    def render_audio(self, pgi, tail=0.0):
        if pgi["rendered"] or pgi["clk0"] is None or not SOUND:
            pgi["rendered"] = True; return
        pgi["rendered"] = True
        try:
            plays = self.pg.evaluate("() => (window.__rec && window.__rec.plays) || []")
            t0, t1 = pgi["clk0"] / 1000.0, pgi["clk1"] / 1000.0 + tail
            meta = self.pg.evaluate("async ([a, b]) => window.__rec ? await __rec.render(a, b) : { none: true }", [t0, t1])
            pcm = b""
            if meta.get("bytes"):
                size = 3 * 1024 * 1024
                for i in range((meta["bytes"] + size - 1) // size):
                    pcm += base64.b64decode(self.pg.evaluate("([i, s]) => __rec.chunk(i, s)", [i, size]))
            pgi["pcm"] = pcm
            pgi["peak"] = meta.get("peak")
            for p in plays:
                if p["t"] >= t0 - .05:
                    self.plays.append(dict(p, at=round(pgi["frame0"] / FPS + p["t"] - t0, 3)))
        except Exception as e:
            print("  (sound of this page lost: %s)" % str(e)[:120], flush=True)

    def finish(self):
        self.render_audio(self.pages[-1])
        self.ff.stdin.close(); self.ff.wait()
        n = len(self.times)
        dur = n / FPS
        import numpy as np
        mix = np.zeros((int(dur * SR) + 1, 2), dtype=np.float64)
        for p in self.pages:
            pcm = p.get("pcm")
            if not pcm: continue
            a = np.frombuffer(pcm, dtype=np.int16).reshape(-1, 2).astype(np.float64)
            o = int(round(p["frame0"] / FPS * SR))
            if o >= len(mix): continue
            k = min(len(a), len(mix) - o)
            mix[o:o + k] += a[:k]
        mix = np.clip(mix, -32767, 32767).astype(np.int16)
        wpath = OUT + ".wav"
        with wave.open(wpath, "wb") as wv:
            wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(mix.tobytes())
        crf = 22
        while True:
            subprocess.run([FF, "-y", "-loglevel", "error", "-i", self.vpath, "-i", wpath, "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
                            "-g", str(FPS * 2), "-c:a", "aac", "-b:a", "160k", "-ar", str(SR), "-ac", "2", "-shortest", "-movflags", "+faststart", OUT],
                           check=True)
            mb = os.path.getsize(OUT) / 1048576
            if mb <= MAX_MB or crf >= 34: break
            crf += 2
        os.remove(wpath); os.remove(self.vpath)
        log = {"frames": n, "seconds": round(dur, 2), "crf": crf, "mb": round(mb, 2), "marks": self.marks, "errors": self.errs,
               "pages": [{k: v for k, v in p.items() if k != "pcm"} for p in self.pages], "plays": self.plays}
        json.dump(log, open(OUT + ".log.json", "w"), indent=1)
        self.br.close()
        print("%s: %.1fs, %d frames, crf %d, %.1f MB, %d sounds, %d page errors%s" % (OUT, dur, n, crf, mb, len([p for p in self.plays if p.get("played")]),
              len(self.errs), (": " + " | ".join(self.errs[:3])) if self.errs else ""), flush=True)
        return log


# ------------------------------------------------------------------ the walks
def gs_read(r, full=True):
    """the Get Started page as a person reads it: a stop on the title, each scene brought to the middle and watched while its
    clip plays, the rank ladder scrolled slowly so its rungs light, the end"""
    S = "document.querySelector('.gs-scroll')"
    r.until("!!document.querySelector('.gs-hero-copy.is-in')", 6, then=2.6 if full else 1.4)
    n = r.js("() => document.querySelectorAll('.gs-scene').length")
    for i in range(n):
        el = "document.querySelectorAll('.gs-scene')[%d]" % i
        r.glide(S, "(() => { const e = %s, s = %s; return s.scrollTop + e.getBoundingClientRect().top + e.offsetHeight / 2 - s.clientHeight / 2; })()" % (el, S), 1.0 if full else .5)
        r.mark("scene: " + str(r.js("() => (%s.querySelector('.gs-title') || {}).textContent" % el)))
        # the badges clip is held to its open case (the pins in it); the others for a few seconds of their clip
        key = r.js("() => (%s.querySelector('video') || {dataset: {}}).dataset.gs" % el)
        r.wait((13.5 if key == "badges" else 5.5) if full else .5)
    # the ladder: its top to the middle, then slowly through it
    r.glide(S, "(() => { const e = document.querySelector('.gs-show'), s = %s; return s.scrollTop + e.getBoundingClientRect().top - s.clientHeight * .25; })()" % S, 1.0 if full else .5)
    r.mark("the rank ladder")
    r.wait(1.0 if full else .2)
    r.glide(S, "(() => { const e = document.querySelector('.gs-show'), s = %s; return s.scrollTop + e.getBoundingClientRect().bottom - s.clientHeight * .7; })()" % S, 4.5 if full else 1.2)
    r.wait(1.6 if full else .3)
    r.glide(S, "%s.scrollHeight" % S, 1.2 if full else .6)
    r.mark("the end")
    r.until("(() => { const b = document.querySelector('.gs-bar.is-ready .gs-go'); return !!b && getComputedStyle(b).opacity > .95; })()", 6, then=1.6 if full else .8)


def nova_walk(r, name, read=1.7, max_sec=480):
    """Nova at his own pace: his lines, the name and the partner questions, the save-your-code card"""
    t_end = len(r.times) + max_sec * FPS
    last = None
    while len(r.times) < t_end:
        if r.js("() => !!document.getElementById('savecode-card')"):
            r.mark("save-your-code card")
            r.wait(3.4)
            r.tap("document.querySelector('#savecode-card .savecode-ack')"); r.wait(.9)
            r.tap("document.querySelector('#savecode-card .savecode-continue')"); r.wait(1.2)
            continue
        st = r.js(G["NOVA_ADV"])
        if not st:
            if r.js("() => !!document.getElementById('savecode-card')"): continue
            return
        if st["sig"] or st["typing"]:
            r.frame(); continue
        if st.get("asking"):
            r.wait(read)
            if st.get("name"):
                r.mark("Nova asks the name")
                r.tap("document.querySelector('#nova-intro .nt-ask-input')"); r.wait(.5)
                r.type(name)
                r.wait(.8)
                r.tap("document.querySelector('#nova-intro .nt-ask-name .nt-ask-go')"); r.wait(1.2)
                r.until("!document.querySelector('#nova-intro .nt-ask-name')", 10)
            elif st.get("char"):
                r.mark("Nova asks the partner")
                r.tap("document.querySelectorAll('#nova-intro .nt-ask-char .avatarchar-option')[2]"); r.wait(1.0)
                r.tap("document.querySelectorAll('#nova-intro .nt-ask-char .avatarchar-option')[0]"); r.wait(1.1)
                r.tap("document.querySelector('#nova-intro .nt-ask-char .nt-ask-go')"); r.wait(1.0)
            last = None
            continue
        if st["i"] != last:
            last = st["i"]; r.wait(read); continue
        if st["i"] >= st["c"] - 1:
            r.tap("document.querySelector('#nova-intro .nt-go')"); r.wait(.9); last = None
        else:
            r.tap("document.querySelector('#nova-intro .nt-bubble')"); r.wait(.3)


def tips(r, read=1.7, max_steps=16):
    seen = []
    for _ in range(max_steps):
        r.until("!!document.getElementById('tour-next')", 8)
        if not r.js("() => !!document.getElementById('tour-next')"):
            return seen
        n = r.js("() => (document.getElementById('tour-tooltip') || {}).textContent.length || 80")
        seen.append(str(r.js("() => (document.getElementById('tour-tooltip') || {}).textContent || ''")))
        r.mark("tip: " + seen[-1][:70])
        r.wait(min(6, n / 70 + read))
        r.tap("document.getElementById('tour-next')", max_sec=3); r.wait(.6)
    return seen


def to_welcome(r, read_all):
    r.until("!document.getElementById('splashscreen') && !!document.querySelector('#stage [data-screen]')", 30, then=.2)
    r.mark("splash gone: %s" % r.js(SCREEN))
    if r.js(SCREEN) == "getstarted":
        gs_read(r, full=read_all)
        r.mark("Let's get started")
        r.tap("document.querySelector('.gs-go')")
    r.until("!!document.querySelector('#stage [data-screen=\"welcome\"]')", 12, then=2.6)
    r.mark("Welcome")


def signup_common(r, cls):
    to_welcome(r, read_all=False)
    r.tap("document.querySelector('.cosmic-welcome-btn.welcome-new')")
    r.until("!!document.querySelector('#stage .signupcheck-panel')", 8, then=2.8)
    r.mark("New to Nova?")
    r.tap("document.querySelector('.signupcheck-panel .signupcheck-go')")
    r.until("!!document.querySelector('#stage .classselect-panel')", 8, then=2.4)
    r.mark("Select your classes")
    r.tap("document.querySelector('.classselect-panel .class-card.is-%s')" % cls); r.wait(1.3)
    r.tap("document.querySelector('.classselect-panel #nextbtn')")
    r.until("(() => { const e = document.querySelector('#classenroll-confirm.show'); return !!e; })()", 6, then=2.6)
    r.mark("the enroll confirm")
    r.tap("document.querySelector('#classenroll-confirm .classenroll-yes')")


def scen_startup(r):
    r.open(URL)
    r.mark("the icon tapped")
    to_welcome(r, read_all=True)
    r.wait(1.5)


def scen_signup_academy(r):
    r.open(URL)
    signup_common(r, "academy")
    r.mark("GENERATING PROFILE")
    r.until("!document.getElementById('genprofile-overlay') && !!document.getElementById('nova-intro')", 40, then=.4)
    r.mark("Nova")
    nova_walk(r, "Alex Rivera")
    r.mark("tips")
    # the last tip of a sign-up (Start Studying) comes after the welcome XP and a quiet beat (scheduleStudyTip)
    if not any("ready to study" in t for t in tips(r)):
        r.until("!!document.getElementById('tour-next')", 40)
        tips(r)
    r.until("!!document.querySelector('#stage [data-screen=\"home\"]') && !document.getElementById('tour-next')", 10)
    r.mark("Home")
    r.wait(5)


def scen_signup_ifc(r):
    if not os.path.isfile(BOOK) or not os.path.exists(PDFJS + "build/pdf.min.mjs"):
        sys.exit("signup-ifc: set IFC_BOOK (the owner's 2021 IFC PDF) and PDFJS_DIR (pdfjs-dist 5.4.149, unpacked)")
    r.open(URL)
    signup_common(r, "ifc")
    r.until("!!document.querySelector('#stage .class-enroll .ce-go')", 8, then=3.2)
    r.mark("Enroll in Fire Code")
    # the book list's long text: a slow look down it to the button
    with r.pg.expect_file_chooser(timeout=60000) as fc:
        r.tap("document.querySelector('#stage .class-enroll .ce-go')")
        r.wait(.3)
    r.wait(.6)
    fc.value.set_files(BOOK)
    r.mark("the book chosen")
    r.until("!!document.querySelector('.ifc-analyze')", 10)
    r.mark("analyzing")
    r.until("!!document.querySelector('.ifc-analyze .ia-go')", 400, then=2.6)
    r.mark("Success: " + str(r.js("() => (document.querySelector('.ifc-analyze') || {}).textContent.replace(/\\s+/g, ' ').slice(0, 160)")))
    r.tap("document.querySelector('.ifc-analyze .ia-go')")
    r.mark("GENERATING PROFILE")
    r.until("!document.getElementById('genprofile-overlay') && !!document.getElementById('nova-intro')", 40, then=.4)
    r.mark("Nova (first half)")
    nova_walk(r, "Jordan Ellis")
    r.mark("into Fire Code")
    r.until("window.NOVA_CLASS === 'ifc' && !document.getElementById('splashscreen') && !!document.getElementById('nova-intro')", 40, then=.4)
    r.mark("Nova (in Fire Code)")
    nova_walk(r, "Jordan Ellis")
    r.mark("tips")
    # the last tip of a sign-up (Start Studying) comes after the welcome XP and a quiet beat (scheduleStudyTip)
    if not any("ready to study" in t for t in tips(r)):
        r.until("!!document.getElementById('tour-next')", 40)
        tips(r)
    r.until("!!document.querySelector('#stage [data-screen=\"home\"]') && !document.getElementById('tour-next')", 10)
    r.mark("Home (%s)" % r.js("() => window.NOVA_CLASS"))
    r.wait(5)


def scen_switch(r):
    r.open(URL)
    r.capture = False          # the launch and anything the launch owes, off camera
    r.until("!document.getElementById('splashscreen') && !!document.querySelector('#stage [data-screen=\"home\"]')", 30, then=3)
    # what this launch owes the account (a secret flare's card, the daily question's banner) is tapped away first, as a person
    # who opened the app a moment ago already has
    for _ in range(12):
        if not r.js("() => !!document.querySelector('.rs-spot, .rs-fly, #nova-intro, .nova-talk, #tour-overlay, .unlock-card')"): break
        r.tap("document.querySelector('.rs-spot, .unlock-card, #tour-next') || document.body"); r.wait(1.5)
    r.js("() => { document.querySelectorAll('.daily-alert, .app-banner').forEach(e => e.remove()); }")
    r.wait(2)
    r.capture = True
    r.mark("Home (%s)" % r.js("() => window.NOVA_CLASS"))
    r.wait(2.5)
    for to in ("ifc", "academy"):
        r.tap("document.querySelector('.class-bubble')"); r.wait(1.6)
        r.mark("the class list")
        r.tap("document.querySelector('.class-stack-item.is-%s')" % to)
        r.mark("switch to " + to)
        r.until("window.NOVA_CLASS === '%s' && !document.getElementById('splashscreen') && !document.getElementById('class-switch-loader') && !!document.querySelector('#stage [data-screen=\"home\"]')" % to, 30)
        r.mark("Home (%s)" % to)
        r.wait(4.5)


SCENS = {"startup": scen_startup, "signup-academy": scen_signup_academy, "signup-ifc": scen_signup_ifc, "switch": scen_switch}
if SCEN not in SCENS:
    sys.exit("no scenario " + SCEN)

_s = socket.socket(); _s.bind(("127.0.0.1", 0)); _port = _s.getsockname()[1]; _s.close()
class _Q(http.server.SimpleHTTPRequestHandler):
    """with byte ranges, as GitHub Pages serves: a clip that cannot be fetched by range cannot be seeked"""
    def log_message(self, *a): pass
    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        a = int(m.group(1)) if m and m.group(1) else 0
        b = int(m.group(2)) if m and m.group(2) else size - 1
        b = min(b, size - 1)
        f = open(path, "rb"); f.seek(a)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", "bytes %d-%d/%d" % (a, b, size))
        self.send_header("Content-Length", str(b - a + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._left = b - a + 1
        return f
    def copyfile(self, src, dst):
        left = getattr(self, "_left", None)
        if left is None: return super().copyfile(src, dst)
        while left > 0:
            buf = src.read(min(65536, left))
            if not buf: break
            dst.write(buf); left -= len(buf)
http.server.ThreadingHTTPServer.handle_error = lambda *a: None
_srv = http.server.ThreadingHTTPServer(("127.0.0.1", _port), functools.partial(_Q, directory=ROOT))
threading.Thread(target=_srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % _port

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    if SCEN == "switch":
        sys.path.insert(0, HERE)
        import b384_switchfx_lib as SL
        rec = NRec(pw, seed_js=SL.seed_js(), fake=False)
    else:
        rec = NRec(pw, fake=True, route_book=(SCEN == "signup-ifc"))
    try:
        SCENS[SCEN](rec)
    finally:
        rec.finish()
_srv.shutdown()
