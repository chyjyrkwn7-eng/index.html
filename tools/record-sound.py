#!/usr/bin/env python3
"""MP4s of the app WITH ITS OWN SOUND (build 327, after build 325's b325h).

  python3 tools/record-sound.py SCENARIO OUT.mp4 [--device phone|ipad] [--fps 30] [--against FILE]
  python3 tools/record-sound.py --list

Madison: "I just want videos for the sounds this time around." Every clip is
an H.264 video with an AAC-LC 48 kHz stereo track holding the sound the app
itself made - not a soundtrack laid over it afterwards.

HOW (the b325h method, rebuilt here because the review-pack recorder that
first did it was never in the repo):

  - THE SOUND IS THE APP'S OWN ENGINE, RUN ON THE VIDEO'S CLOCK. An init
    script replaces AudioContext with a subclass of OfflineAudioContext
    whose currentTime is the page's performance.now(). NovaSound builds
    every node exactly as it would on a phone - the designs, the limiter,
    the buses, the duck under a cutscene, voice stealing, the Home ambience
    with its fades - each scheduled at the page-clock moment it asked for.
    When the last frame is shot the context is rendered once, the audio
    from the first frame on is cut out and muxed under the video.
  - AN OFFLINE CONTEXT HAS NOT STARTED, so "now" is made explicit, for
    nodes made on the recording context only: start()/stop() with no time
    or a past time mean the page clock; param.value = v becomes
    setValueAtTime(v, now); cancelScheduledValues(t) + setValueAtTime(.value,
    t) (the hold-then-fade in kill() and stopAmbience()) becomes
    cancelAndHoldAtTime(t); disconnect() is a no-op (the engine only ever
    disconnects voices that are already silent). NovaSound.render, the
    ambience pre-render and check-sound use real OfflineAudioContexts and
    are not touched.
  - THE PAGE'S CLOCK IS REPLACED WHEN RECORDING STARTS, not before: Date,
    performance.now, timers, requestAnimationFrame and smooth scrolls read
    a clock this script advances exactly 1/fps per frame, and every CSS /
    Web animation and transition is paused and seeked to it (the clock of
    tools/record-hundo.py). It CONTINUES from the real performance.now(), so
    nothing stamped before it (NovaSound's cooldowns and its "a generic tap
    gives way" rule compare performance.now stamps) is ever in the future:
    build 325's trap was a clock installed mid-run moving performance.now()
    BACK by 1.5s, after which the engine refused 8 of 8 taps.
  - Sound is turned ON for the clip (it is the default since build 327) and
    a real click wakes the context, as a first tap does on a phone.
  - Every play is logged beside the MP4 (OUT.sound.json): id, page time,
    and whether the engine played it.

Scenarios drive the real app: a drill of Identity Crimes answered by real
clicks for the results screens and the test, the Rank tab's climb, the badge
case cutscene, a rank-up, Supernova (Home and its cutscene)."""
import base64, functools, http.server, io, json, os, re, socket, subprocess, sys, threading, wave
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"
DEVICES = {"phone": (440, 956, 3), "ipad": (834, 1194, 2)}
SR = 48000


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SRC = arg("--against") or os.path.join(ROOT, "index.html")
FPS = int(arg("--fps", "30"))
DEV = arg("--device", "phone")

FIRESTORE_STUB = """
  window.__stub = function(){
    if(!window.__osr0) window.__osr0 = onSnapshotResilient;
    fbDb = { collection: function(){ return { doc: function(){ return {
      set: function(){ return Promise.resolve(); },
      get: function(){ return Promise.resolve({ exists: false }); },
      update: function(){ return Promise.resolve(); },
      delete: function(){ return Promise.resolve(); }
    }; } }; } };
    onSnapshotResilient = function(ref, onNext){
      setTimeout(function(){ onNext({ forEach: function(){} }); }, 20);
      return function(){};
    };
  };
"""
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
BODY = INSET_RE.sub(lambda m: "0px", open(SRC, encoding="utf-8").read()) \
    .replace("let fbDb = null;", "let fbDb = null;" + FIRESTORE_STUB, 1)
# check-vroom's fake Firestore (localStorage-backed, live listeners): the
# scenarios that need a class (the leaderboard, a lobby, the chat) switch to it.
FAKE_FS = re.search(r'FAKE_FIRESTORE = """(.*?)"""', open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read(), re.S).group(1)
USE_FAKE = r"""() => {
  fbDb = window.__fakeDb; if(window.__osr0) onSnapshotResilient = window.__osr0;
  syncCode = 'MADI-0001'; store.publicId = 'pub-madison'; store.leaderboardOptIn = true; saveStore();
}"""
# A class on the board: rows the way buildLeaderboardRow() writes them.
CLASS_ROWS = r"""() => {
  const wk = weekKeyNow(), now = Date.now(), all = {};
  [['Devonte','ghost',41,5,88400,6200],['Sauce','wizard',47,7,121000,9400],['Odin','alien',44,6,101500,7100],
   ['Brandon','bear',33,3,52000,4100],['Aranda','tempest',29,2,38800,3300],['Hughesha','solar',38,4,70100,5600],
   ['Cap','ninja',35,3,61200,2100],['Tsale','lunar',26,1,30500,2900],['Z','frost',40,5,79900,4800],
   ['Vishal','ghost',24,1,25300,1500],['Rogelio','wizard',22,0,19900,1200],['Napoleon','alien',37,4,66800,3900]]
  .forEach(([n, av, lv, b, xp, wp], i) => { all['pub-' + n.toLowerCase()] = { firstName: n, avatarChar: av, accent: 'ink',
     correct: Math.round(xp / 11), level: lv, badges: b, mystery: 0, hundos: b * 9 + i, rankFloor: 0, xp, tests: 40 + i * 3,
     week: wk, weekPoints: wp, lastModified: now - i * 60000, seenAt: now - i * 90000 }; });
  localStorage.setItem('fakefs::leaderboard', JSON.stringify(all));
}"""
_b = re.search(r'const APP_BUILD = "([^"]+)"', BODY)
BUILD = _b.group(1) if _b else ""

ACCOUNT = json.dumps({
    "firstName": "Madison", "avatarChar": "ninja", "onboardingComplete": True, "leaderboardOptIn": True,
    "lastModified": 1700000000000, "seenProfileTour": True, "tourRev": 99, "rankMapFx244": True,
    "lifetime": {"points": 14820, "answered": 5400, "correct": 4980, "drillPlays": 64, "examPlays": 22,
                 "perfectTests": 30, "currentStreak": 0, "longestStreak": 57},
    "unlocksShown": {"chars": [], "banners": ["hundos100"],
                     "fx": ["fireworks", "blackhole", "underwater", "worldtree", "bubbles", "ufo"]},
    "theme": {"mode": "dark", "accent": "ink", "layout": "modern", "swipeAdvance": True, "autoAdvance": False,
              "reduceMotion": False, "muteBanners": False, "soundOn": True, "soundVolume": .8, "vibrate": False,
              "soundOn327": True}})

SEED_LS = ("try{['class26e.freshstart','1','class26e.frame.ok','go-live-1','class26e.intro.seen','9',"
           "'class26e.unithold.tip','1','class26e.penal55124.seen','1','class26e.penal124256.seen','1',"
           "'class26e.penal256578.seen','1','class26e.weekrecap.v1','9999-12-31','class26e.soundon.327','1']"
           ".reduce((a,v,i,l)=>{ if(i%%2===0) localStorage.setItem(v,l[i+1]); return a; },0);"
           "localStorage.setItem('class26e.drill.v1', %s);}catch(e){}") % json.dumps(ACCOUNT)

# A brand-new install: none of the account, none of "seen" - only the keys
# that would otherwise put a one-off notice over the walk.
SEED_FRESH = ("try{['class26e.freshstart','1','class26e.frame.ok','go-live-1','class26e.weekrecap.v1','9999-12-31',"
              "'class26e.penal55124.seen','1','class26e.penal124256.seen','1','class26e.penal256578.seen','1']"
              ".forEach((v,i,l)=>{ if(i%2===0) localStorage.setItem(v,l[i+1]); });}catch(e){}")
FRESH_SETUP = r"""() => {
  document.getElementById('splashscreen')?.remove();
  try{ __stub(); fbDb = window.__fakeDb; if(window.__osr0) onSnapshotResilient = window.__osr0; }catch(e){}
}"""

# ---------------------------------------------------------------- the audio
REC_AUDIO = r"""
(() => {
  const OAC = window.OfflineAudioContext;
  if(!OAC) return;
  const REC = window.__rec = { nodes: new WeakSet(), params: new WeakSet(), held: new WeakMap(), ctx: null, budget: %BUDGET%, done: false, plays: [] };
  const now = () => performance.now() / 1000;
  const track = n => {
    if(!n || typeof n !== 'object') return n;
    REC.nodes.add(n);
    for(const k in n){ try{ const v = n[k]; if(v instanceof AudioParam) REC.params.add(v); }catch(e){} }
    return n;
  };
  class RecCtx extends OAC {
    constructor(){
      super({ numberOfChannels: 2, length: Math.round((now() + REC.budget) * 48000), sampleRate: 48000 });
      REC.ctx = this; REC.createdAt = now();
    }
    get currentTime(){ return now(); }
    get state(){ return REC.done ? 'closed' : 'running'; }
    resume(){ return Promise.resolve(); }
    suspend(){ return Promise.resolve(); }
    close(){ return Promise.resolve(); }
  }
  ['createGain','createOscillator','createBiquadFilter','createStereoPanner','createDelay','createConvolver',
   'createDynamicsCompressor','createBufferSource','createChannelMerger','createChannelSplitter','createWaveShaper',
   'createConstantSource','createPanner','createIIRFilter'].forEach(m => {
    const f = BaseAudioContext.prototype[m];
    if(f) RecCtx.prototype[m] = function(...a){ return track(f.apply(this, a)); };
  });
  const pv = Object.getOwnPropertyDescriptor(AudioParam.prototype, 'value');
  Object.defineProperty(AudioParam.prototype, 'value', { configurable: true, enumerable: true,
    get(){ return pv.get.call(this); },
    set(v){ if(REC.params.has(this)){ try{ this.setValueAtTime(v, now()); }catch(e){} } else pv.set.call(this, v); } });
  const csv = AudioParam.prototype.cancelScheduledValues, svt = AudioParam.prototype.setValueAtTime;
  AudioParam.prototype.cancelScheduledValues = function(t){
    if(REC.params.has(this)){ try{ this.cancelAndHoldAtTime(t); }catch(e){ csv.call(this, t); } REC.held.set(this, t); return this; }
    return csv.call(this, t);
  };
  AudioParam.prototype.setValueAtTime = function(v, t){
    if(REC.params.has(this) && REC.held.get(this) === t){ REC.held.delete(this); return this; }
    return svt.call(this, v, t);
  };
  const fixStart = proto => {
    const st = proto.start, sp = proto.stop;
    proto.start = function(when, ...rest){ if(REC.nodes.has(this)) when = Math.max(when || 0, now()); return st.call(this, when, ...rest); };
    proto.stop = function(when){ if(REC.nodes.has(this)) when = Math.max(when || 0, now()); return sp.call(this, when); };
  };
  fixStart(AudioScheduledSourceNode.prototype);
  if(Object.prototype.hasOwnProperty.call(AudioBufferSourceNode.prototype, 'start')) fixStart(AudioBufferSourceNode.prototype);
  const dc = AudioNode.prototype.disconnect;
  AudioNode.prototype.disconnect = function(...a){ if(REC.nodes.has(this)) return; return dc.apply(this, a); };
  try{ Object.defineProperty(window, 'AudioContext', { value: RecCtx, configurable: true, writable: true }); }catch(e){ window.AudioContext = RecCtx; }
  try{ Object.defineProperty(window, 'webkitAudioContext', { value: RecCtx, configurable: true, writable: true }); }catch(e){}
  REC.render = async (t0, t1) => {
    if(!REC.ctx) return { n: 0, none: true };
    REC.done = true;
    const buf = await OAC.prototype.startRendering.call(REC.ctx);
    const a = Math.max(0, Math.round(t0 * 48000)), b = Math.min(buf.length, Math.round(t1 * 48000)), n = Math.max(0, b - a);
    const L = buf.getChannelData(0), R = buf.getChannelData(1), out = new Int16Array(n * 2);
    let peak = 0;
    for(let i = 0; i < n; i++){
      const l = L[a + i], r = R[a + i]; peak = Math.max(peak, Math.abs(l), Math.abs(r));
      out[2 * i] = Math.max(-32767, Math.min(32767, Math.round(l * 32767)));
      out[2 * i + 1] = Math.max(-32767, Math.min(32767, Math.round(r * 32767)));
    }
    REC.pcm = new Uint8Array(out.buffer);
    return { n, peak, bytes: REC.pcm.length, from: a, len: buf.length };
  };
  REC.chunk = (i, size) => {
    const s = REC.pcm.subarray(i * size, (i + 1) * size);
    let bin = '';
    for(let k = 0; k < s.length; k += 32768) bin += String.fromCharCode.apply(null, s.subarray(k, k + 32768));
    return btoa(bin);
  };
})();
"""

# ---------------------------------------------------------------- the clock
CLOCK = r"""() => {
  if(window.__clk) return;
  const C = window.__clk = { t: performance.now(), q: [], id: 9e6, raf: [], seen: new Map() };
  const nraf = window.__nraf = window.requestAnimationFrame.bind(window);
  const d0 = Date.now() - C.t;
  performance.now = () => C.t; Date.now = () => Math.round(d0 + C.t);
  window.setTimeout = (f, ms, ...a) => { const id = C.id++; if(typeof f === 'function') C.q.push({ id, at: C.t + Math.max(0, +ms || 0), f, a }); return id; };
  window.setInterval = (f, ms, ...a) => { const id = C.id++; const p = Math.max(1, +ms || 0); C.q.push({ id, at: C.t + p, f, a, every: p }); return id; };
  window.clearTimeout = window.clearInterval = id => { C.q = C.q.filter(x => x.id !== id); };
  window.requestAnimationFrame = f => { const id = C.id++; C.raf.push({ id, f }); return id; };
  window.cancelAnimationFrame = id => { C.raf = C.raf.filter(x => x.id !== id); };
  const nScrollTo = window.scrollTo.bind(window);
  window.scrollTo = function(a, b){
    if(a && typeof a === 'object' && a.behavior === 'smooth'){
      const y0 = scrollY, y1 = Math.max(0, Math.min(a.top != null ? a.top : y0, document.documentElement.scrollHeight - innerHeight)), t0 = C.t, D = 420;
      const step = () => { const u = Math.min(1, (C.t - t0) / D), e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
        nScrollTo({ top: y0 + (y1 - y0) * e, left: 0, behavior: 'instant' }); if(u < 1) window.requestAnimationFrame(step); };
      window.requestAnimationFrame(step); return;
    }
    return nScrollTo(a, b);
  };
  window.scrollBy = function(a){ if(a && typeof a === 'object') return window.scrollTo(Object.assign({}, a, { top: scrollY + (a.top || 0) })); return nScrollTo(scrollX + arguments[0], scrollY + arguments[1]); };
  const seek = () => {
    for(const an of document.getAnimations()){
      let base = C.seen.get(an);
      if(base === undefined){ base = C.t - (an.currentTime || 0); C.seen.set(an, base); try{ an.pause(); }catch(e){} }
      if(an.playState === 'finished') continue;
      let end = Infinity; try{ end = an.effect.getComputedTiming().endTime; }catch(e){}
      const t = (C.t - base) * (an.playbackRate || 1);
      if(isFinite(end) && t >= end){ try{ an.finish(); }catch(e){} continue; }
      try{ an.currentTime = t; }catch(e){}
    }
  };
  C.advance = async dt => {
    const end = C.t + dt;
    for(let guard = 0; guard < 4000; guard++){
      C.q.sort((x, y) => x.at - y.at);
      const n = C.q[0]; if(!n || n.at > end) break;
      C.t = Math.max(C.t, n.at);
      if(n.every) n.at += n.every; else C.q.shift();
      try{ n.f(...n.a); }catch(e){ console.error(e); }
      await null; seek();
    }
    C.t = end; seek();
    const r = C.raf; C.raf = [];
    r.forEach(x => { try{ x.f(C.t); }catch(e){ console.error(e); } });
    await null; seek();
    await new Promise(res => nraf(() => nraf(res)));
    return C.t;
  };
  seek();
}"""

LOG_PLAYS = r"""() => {
  if(window.__logged) return; window.__logged = true;
  const P = NovaSound.play;
  NovaSound.play = (id, o) => { const r = P(id, o); window.__rec.plays.push({ id, t: +(performance.now() / 1000).toFixed(3), played: !!r, opts: o && typeof o === 'object' ? JSON.parse(JSON.stringify(o)) : null }); return r; };
}"""

SETUP = r"""() => {
  document.getElementById('splashscreen')?.remove(); try{ __stub(); }catch(e){}
  store.onboardingComplete = true; store.firstName = 'Madison'; store.tourRev = 99; store.rankMapFx244 = true;
  store.retroBadgePending = []; store.badgeBandsVersion = 3;
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
   'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour','seenRanksTour','seenBadgesTour'].forEach(k => store[k] = true);
  theme.muteBanners = false; theme.reduceMotion = false; theme.autoAdvance = false; theme.soundOn = true; theme.soundVolume = .8;
  saveTheme(); saveStore();
}"""

SEED_RANK = r"""(k) => {
  const rule = TIER_UNLOCKS[k] || {};
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  store.unitPerfects = {};
  topics.slice(0, rule.badges || 0).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
  let pts = 1000; while(levelProgress(pts).level < (rule.level || 0)) pts += 500;
  store.lifetime = store.lifetime || {}; store.lifetime.points = pts;
  store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, TIER_ORDER_FULL.indexOf(k) + 1);
  saveStore();
}"""

START_DRILL = r"""(unit) => {
  showHome();
  const ix = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && (typeof inWholeUnit !== 'function' || inWholeUnit(i)));
  cfg.mode = 'drill'; cfg.units = [unit]; cfg.source = 'all'; cfg.size = 0; runMode = 'drill';
  beginRun(ix, null);
  return ix.length;
}"""


class Rec:
    """One page, one clip: prep in real time, then frames on the page's clock."""

    def __init__(self, pw, budget, mode="used"):
        w, h, dpr = DEVICES[DEV]
        self.w, self.h = w, h
        self.br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required", "--force-device-scale-factor=%d" % dpr])
        self.ctx = self.br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr)
        self.ctx.add_init_script(FAKE_FS)
        self.ctx.add_init_script(SEED_FRESH if mode == "fresh" else SEED_LS)
        self.ctx.add_init_script(REC_AUDIO.replace("%BUDGET%", str(budget)))
        pg = self.pg = self.ctx.new_page()
        self.errs = []
        pg.on("pageerror", lambda e: self.errs.append(str(e)[:200]))
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"},
                                                          body='{"build":"%s","frameId":"","note":""}' % BUILD))
        pg.goto(URL)
        pg.wait_for_timeout(2600)
        pg.evaluate(FRESH_SETUP if mode == "fresh" else SETUP)
        pg.evaluate(LOG_PLAYS)
        self.cdp = self.ctx.new_cdp_session(pg)
        self.ff = None
        self.times = []
        self.vpath = None

    def js(self, expr, a=None):
        return self.pg.evaluate(expr, a) if a is not None else self.pg.evaluate(expr)

    def wake(self):
        """A real tap somewhere harmless: the first gesture makes the context."""
        self.pg.mouse.click(self.w - 3, self.h // 2)
        self.pg.wait_for_timeout(300)

    # ---- recording
    def start(self, vpath):
        self.js(CLOCK)
        self.vpath = vpath
        self.ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21",
                                    "-preset", "veryfast", "-r", str(FPS), vpath], stdin=subprocess.PIPE)

    def frame(self):
        t = self.pg.evaluate("async () => await __clk.advance(1000 / %d)" % FPS)
        fr = base64.b64decode(self.cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 85})["data"])
        self.ff.stdin.write(fr)
        self.times.append(t)

    def frames(self, n):
        for _ in range(int(n)):
            self.frame()

    def wait(self, sec):
        self.frames(round(sec * FPS))

    def until(self, js, max_sec, then=0.0):
        for _ in range(int(max_sec * FPS)):
            if self.js(js):
                break
            self.frame()
        self.wait(then)

    def center(self, js):
        return self.js("() => { const el = (" + js + "); if(!el) return null; el.scrollIntoView && el.getBoundingClientRect().bottom > innerHeight && el.scrollIntoView({ block: 'center' });"
                       " const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")

    def tap(self, js, max_sec=6):
        for _ in range(int(max_sec * FPS)):
            xy = self.center(js)
            if xy:
                self.pg.mouse.click(xy[0], xy[1])
                return True
            self.frame()
        return False

    def finish(self, out):
        self.ff.stdin.close(); self.ff.wait()
        t0 = self.times[0] / 1000.0 if self.times else 0
        t1 = t0 + len(self.times) / FPS
        meta = self.js("async ([a, b]) => await __rec.render(a, b)", [t0, t1])
        pcm = b""
        if meta.get("bytes"):
            size = 3 * 1024 * 1024
            for i in range((meta["bytes"] + size - 1) // size):
                pcm += base64.b64decode(self.js("([i, s]) => __rec.chunk(i, s)", [i, size]))
        wpath = out + ".wav"
        with wave.open(wpath, "wb") as wv:
            wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
            wv.writeframes(pcm if pcm else b"\0\0\0\0" * int((t1 - t0) * SR))
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", self.vpath, "-i", wpath, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2", "-shortest", "-movflags", "+faststart", out], check=True)
        plays = self.js("() => __rec.plays")
        log = {"from": t0, "to": t1, "frames": len(self.times), "fps": FPS, "peak": meta.get("peak"), "context": not meta.get("none"),
               "plays": [dict(p, at=round(p["t"] - t0, 3)) for p in plays if p["t"] >= t0 - .05], "held_before": [p for p in plays if p["t"] < t0 - .05],
               "errors": self.errs}
        json.dump(log, open(out + ".sound.json", "w"), indent=1)
        os.remove(wpath); os.remove(self.vpath)
        self.br.close()
        return log


# ---------------------------------------------------------------- scenarios
def prep_answer(r, wrong=(), stop_before=1):
    """Answer the running drill in real time (not recorded): a question in
    `wrong` gets one wrong pick first. Stops `stop_before` questions short."""
    pg = r.pg
    pg.wait_for_selector(".qpanel .choice", timeout=25000)
    n = r.js("() => order.length")
    for k in range(n - stop_before):
        answer_one(r, k in wrong, real=True)


SETTLED = "(() => !document.querySelector('.qpanel .choice') || (pos !== %d && document.querySelectorAll('.qpanel').length === 1))()"


def answer_one(r, wrong_first, real=False):
    def tap_choice(right):
        js = "(() => { const s = correctSlot(order[pos]); const oo = optionOrder(order[pos]); const k = %s; return document.querySelector('.qpanel .choice[data-index=\"' + k + '\"]'); })()" % \
             ("s" if right else "(s + 1) % oo.length")
        if real:
            xy = r.center(js)
            r.pg.mouse.click(xy[0], xy[1]); r.pg.wait_for_timeout(500)
        else:
            r.tap(js); r.wait(.6)
    p = r.js("() => pos")
    if wrong_first:
        tap_choice(False)
    tap_choice(True)
    if real:
        for _ in range(30):
            if r.js("() => { const b = document.getElementById('nextbtn'); return !!b && !b.hidden && b.getBoundingClientRect().height > 0 && +getComputedStyle(b).opacity > .98 && !b.getAnimations().some(a => a.playState === 'running' || a.playState === 'paused' && a.currentTime < (a.effect.getComputedTiming().endTime || 0)); }"):
                break
            r.pg.wait_for_timeout(100)
        r.pg.wait_for_timeout(300)
        xy = r.center("document.getElementById('nextbtn')")
        if xy: r.pg.mouse.click(xy[0], xy[1])
        # THE SLIDE HAS TWO QUESTIONS MOUNTED AT ONCE: wait for the new one
        # alone, or the next click lands on the outgoing copy and is lost
        for _ in range(60):
            r.pg.wait_for_timeout(100)
            if r.js(SETTLED % p):
                break
        r.pg.wait_for_timeout(250)
    else:
        r.until("(() => { const b = document.getElementById('nextbtn'); return !!b && !b.hidden && b.getBoundingClientRect().height > 0 && +getComputedStyle(b).opacity > .98 && !b.getAnimations().some(a => a.playState === 'running' || a.playState === 'paused' && a.currentTime < (a.effect.getComputedTiming().endTime || 0)); })()", 3, then=.2)
        r.tap("document.getElementById('nextbtn')")
        r.until(SETTLED % p, 5, then=.35)


RESULTS_DONE = "(() => { const a = document.querySelector('.rs-actions'); return !!a && +getComputedStyle(a).opacity > .9 && !document.querySelector('.rs-spot, .bc-scene, .sf-scene'); })()"


def results(miss, extra=None, tail=2.5, max_sec=70):
    def body(r, out):
        if extra:
            r.js(extra)
        r.wake()
        n = r.js(START_DRILL, "Identity Crimes")
        last = n - 1
        wrong = set(range(miss))
        if last in wrong:
            wrong.discard(last); wrong.add(0)
        prep_answer(r, wrong=wrong, stop_before=1)
        r.pg.wait_for_timeout(400)
        r.start(out)
        r.wait(.4)
        answer_one(r, False)
        r.until(RESULTS_DONE, max_sec, then=tail)
    return body


def home_idle(r, out):
    r.js("() => showHome()")
    r.wake()
    r.pg.wait_for_timeout(3500)
    r.start(out)
    r.wait(20)


def roadmap(r, out):
    # A REAL CLIMB (build 327): the rank held is Gold and long since shown
    # (rankUpShown, rankMapSeen), and the stretch to Platinum has grown since
    # the last look - two units most of the way to their badges and a few
    # levels more. The old fixture replayed a rank reached on the map's
    # first look, a path today's rank-up journey has replaced.
    r.js(SEED_RANK, "veteran")
    r.js("""() => { const held = TIER_ORDER_FULL.indexOf(rankOf(store));
      const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean).filter(t => !(store.unitPerfects[t] >= badgeThresholdFor(t)));
      topics.slice(0, 2).forEach(t => { store.unitPerfects[t] = Math.max(1, badgeThresholdFor(t) - 1); });
      let pts = store.lifetime.points; while(levelProgress(pts).level < 46) pts += 400; store.lifetime.points = pts;
      store.rankUpShown = held + 1; store.rankMapSeen = held; store.rankMapFx244 = true;
      store.rankMapProg = { i: held, p: .04 };
      try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
      saveStore(); showHome(); }""")
    r.wake()
    r.pg.wait_for_timeout(2500)
    r.start(out)
    r.wait(.6)
    r.js("() => showRanksScreen('ranks')")
    r.wait(16)


def rankup_journey(r, out):
    # THE RANK-UP AS PEOPLE SEE IT (build 319-327): Silver held and shown,
    # Gold's badges and level reached, Home locks and the Profile tab
    # calls; tapping it plays the journey on Profile and the road map.
    r.js(SEED_RANK, "ranger")
    r.js("""() => { const held = TIER_ORDER_FULL.indexOf(rankOf(store));
      store.rankUpShown = held + 1; store.rankMapSeen = held; store.rankMapFx244 = true; store.rankMapProg = { i: held, p: .6 };
      try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
      saveStore(); showHome();
      /* the badges and level Gold asks for, as a test would hand them over */
      const rule = TIER_UNLOCKS.veteran;
      const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
      store.rankUpFrom = { r: held, b: badgeCountOf(store), p: store.lifetime.points, d: .6 };
      topics.slice(0, rule.badges).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
      let pts = store.lifetime.points; while(levelProgress(pts).level < rule.level + 3) pts += 400; store.lifetime.points = pts;
      saveStore(); showHome(); }""")
    r.wake()
    r.pg.wait_for_timeout(3500)
    r.start(out)
    r.wait(2.2)
    r.tap("document.getElementById('bottomtab-profile')")
    r.wait(4)
    # the rank's reward card: read for a few seconds, then tapped on, as people do
    r.until("!!document.querySelector('.rs-spot')", 60, then=3.5)
    r.tap("document.querySelector('.rs-spot')", 2)
    r.until("!document.body.classList.contains('ru-journey')", 60, then=3)


def badge_cutscene(r, out):
    # the badge really earned (and two before it), so the case's count line is true
    r.js("() => { for(const u of ['Identity Crimes','Racial Profiling','Victims of Crime']) store.unitPerfects[u] = Math.max(store.unitPerfects[u]||0, badgeThresholdFor(u)); showHome(); }")
    r.wake()
    r.pg.wait_for_timeout(2500)
    r.start(out)
    r.wait(.5)
    r.js("() => { theme.muteBanners = false; window.__bcDone = false; playBadgeCaseScene(['Identity Crimes'], () => { window.__bcDone = true; }); }")
    r.until("window.__bcDone", 40, then=1.5)


def rankup(r, out):
    r.js(SEED_RANK, "veteran")
    r.js("() => { homeUnlockPlaying = true; showHome(); }")
    r.wake()
    r.pg.wait_for_timeout(2500)
    r.start(out)
    r.wait(.5)
    r.js("() => { store.pendingTierCutscene = 'veteran'; playTierCutscene('veteran'); }")
    r.wait(30)


def supernova(r, out):
    r.js(SEED_RANK, "titan")
    r.js("() => { store.supernovaAchieved = true; try{ markRingTierSeen('supernova'); }catch(e){} /* an up-to-date account: its Supernova reward cards were shown long ago (owed cards hold the streak back) */ try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){} homeUnlocksOwed = () => false; homeUnlockPlaying = false; saveStore(); showHome(); }")
    r.wake()
    r.pg.wait_for_timeout(3000)
    r.start(out)
    r.wait(1.5)
    # the planet tapped: the Supernova ring's comet streaks (silent since 327)
    r.tap("document.querySelector('.screen-home-actual .cosmic-hero-main') || document.querySelector('.cosmic-hero-wrap')")
    r.wait(3)
    r.js("() => { try{ homeRingStreak(document.querySelector('.cosmic-hero-wrap'), 'random'); }catch(e){} }")
    r.wait(3)
    r.js("() => { store.pendingSupernovaCutscene = true; playSupernovaCutscene(); }")
    r.wait(37)


def test(r, out):
    r.wake()
    r.start(out)
    r.wait(.3)
    r.js(START_DRILL, "Identity Crimes")
    r.until("!!document.querySelector('.qpanel .choice')", 8, then=.6)
    answer_one(r, True)
    for _ in range(11):
        if not r.js("!!document.querySelector('.qpanel .choice')"):
            break
        answer_one(r, False)
    r.wait(1.5)


def streak(r, out):
    """A drill on a long unit, every answer right; before each of eight
    answers the run's live streak is set one short of the next tier (10,
    25, 50 ... 350), so each right answer is a real streak pop and its sound."""
    r.wake()
    r.js("() => { theme.muteBanners = false; theme.autoAdvance = false; }")
    r.js(START_DRILL, "Penal Code")
    r.pg.wait_for_selector(".qpanel .choice", timeout=25000)
    r.pg.wait_for_timeout(600)
    r.start(out)
    r.wait(.6)
    for t in [10, 25, 50, 75, 100, 150, 250, 350]:
        r.js("(n) => { runLiveStreak = n - 1; }", t)
        answer_one(r, False)
        r.wait(2.6)
    r.wait(1.5)


def unlock_banner(r, out):
    """The unlock banner on Home, three times: a challenge character, a banner,
    and a character after a scene's bridge (its chord comes .35s sooner)."""
    r.js("() => { homeUnlockPlaying = true; theme.muteBanners = false; showHome(); }")
    r.wake()
    r.pg.wait_for_timeout(2500)
    r.start(out)
    r.wait(.5)
    for js in ["characterUnlockItem('zeus')", "bannerUnlockItem((BANNERS.find(b => !b.rank && !b.secret) || BANNERS[0]).id)", "characterUnlockItem('detective')"]:
        if "detective" in js:
            r.js("() => { try{ openSceneBridge('#7FC8FF'); }catch(e){} }")
        r.js("() => { window.__spDone = false; playUnlockSpotlight(" + js + ", 1, 1, () => { window.__spDone = true; }); }")
        r.wait(3.2)
        r.tap("document.querySelector('.rs-spot')", 2)
        r.until("window.__spDone || !document.querySelector('.rs-spot')", 6, then=.8)
    r.wait(1)


def flare_scene(fn_js, secs):
    def body(r, out):
        r.js("() => { homeUnlockPlaying = true; showHome(); }")
        r.wake()
        r.pg.wait_for_timeout(2500)
        r.start(out)
        r.wait(.4)
        r.js("() => { window.__sfDone = false; " + fn_js + "(() => { window.__sfDone = true; }); }")
        r.until("window.__sfDone", secs, then=1)
    return body


def drag(r, frm_js, to_js, steps=14):
    """A real pointer drag from one element's middle to another's, a frame
    between each move, so what follows the finger is heard as it moves."""
    a, b = r.center(frm_js), r.center(to_js)
    if not a or not b:
        return False
    r.pg.mouse.move(a[0], a[1]); r.pg.mouse.down(); r.frame()
    for i in range(1, steps + 1):
        f = i / steps
        r.pg.mouse.move(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        r.frame()
    r.pg.mouse.up()
    return True


def btn(text, scope="#stage"):
    return "[...document.querySelectorAll('%s button')].find(b => b.offsetParent && b.textContent.trim().indexOf(%s) === 0)" % (scope, json.dumps(text))


def tabs(r, out):
    """Home, Profile, Leaderboard, Calendar and back with real taps on the
    tab bar, Profile's top tabs (Profile, Stats, Settings), and one drag
    along the bar from Home to Calendar."""
    r.js("() => { homeUnlockPlaying = true; showHome(); }")
    r.wake()
    r.pg.wait_for_timeout(2500)
    r.start(out)
    r.wait(1.2)
    r.tap("document.getElementById('bottomtab-profile')"); r.wait(1.4)
    r.tap("document.querySelector('.profile-stats-tab-btn')"); r.wait(1.1)
    r.tap("document.querySelector('.profile-settings-tab-btn')"); r.wait(1.1)
    r.tap("document.querySelector('.navsegment.profiletabs .iconbtn')"); r.wait(1.1)
    r.tap("document.getElementById('bottomtab-rewards')"); r.wait(1.4)
    r.tap("document.getElementById('bottomtab-calendar')"); r.wait(1.4)
    r.tap("document.getElementById('bottomtab-home')"); r.wait(1.6)
    drag(r, "document.getElementById('bottomtab-home')", "document.getElementById('bottomtab-calendar')", 24)
    r.wait(2)


def leaderboard(r, out):
    """The Leaderboard with a class on it: every board, Find me, a
    classmate's card opened and closed."""
    r.js(CLASS_ROWS); r.js(USE_FAKE)
    r.js("() => { homeUnlockPlaying = true; showHome(); }")
    r.wake()
    r.pg.wait_for_timeout(2500)
    r.start(out)
    r.wait(1)
    r.tap("document.getElementById('bottomtab-rewards')"); r.wait(1.8)
    for i in (0, 2, 1):
        r.tap("document.querySelectorAll('#stage .navsegment .iconbtn')[%d]" % i); r.wait(1.2)
    r.tap("document.querySelector('.rank-me-btn')"); r.wait(2)
    r.tap("[...document.querySelectorAll('.rank-row')].find(e => { const b = e.getBoundingClientRect(); return b.top > 150 && b.bottom < innerHeight - 140 && !e.classList.contains('is-me'); })")
    r.wait(2)
    r.tap("document.querySelector('.person-sheet-close')"); r.wait(1.6)


def lobby(r, out):
    """The Virtual Room: Host a room, Match settings (units ticked, the
    games tried, saved), back in the lobby a classmate joins and readies,
    then Ready up and the countdown."""
    r.js(CLASS_ROWS); r.js(USE_FAKE)
    r.js("() => { showModeSelect(); }")
    r.wake()
    r.pg.wait_for_timeout(1500)
    r.start(out)
    r.wait(1)
    r.tap("document.querySelector('.modecard[data-mode=\"vroom\"]')"); r.wait(1.4)
    r.tap("document.querySelector('.vrc-card-host')")
    r.until("!!document.querySelector('.screen-vroom-lobby')", 8, then=1.6)
    r.tap("document.querySelector('.vroom-settings-btn')"); r.wait(1.4)
    r.tap("document.querySelectorAll('.picks > label.pick')[0]"); r.wait(.5)
    r.tap("document.querySelectorAll('.picks > label.pick')[1]"); r.wait(.8)
    r.tap("document.querySelector('.vroom-setup-go')"); r.wait(1.3)
    for g in ("tug", "battle", "race"):
        r.tap("document.querySelector('.unitoptions-modal:not([hidden]) .vroom-host-mode[data-mode=\"%s\"]')" % g); r.wait(.8)
    r.tap(btn("Save settings", ".unitoptions-modal:not([hidden])"))
    r.until("!!document.querySelector('.screen-vroom-lobby')", 8, then=1.5)
    r.js("() => fbDb.collection('vrooms').doc(vroomCode).update({ 'participants.pub-devonte': { name: 'Devonte', avatarChar: 'ghost', joinedAt: Date.now(), seen: Date.now(), ready: false, finished: false, progress: 0, level: 41, badges: 5 } })")
    r.wait(2)
    r.js("() => fbDb.collection('vrooms').doc(vroomCode).update({ 'participants.pub-devonte.ready': true })")
    r.wait(1.6)
    r.tap("document.querySelector('.vroom-readyup-btn')")
    r.wait(7)


def selections(r, out):
    """Picking things: the mode, units ticked and unticked (and a drag
    select), the start sheet's switches, How many and All, closed; two
    Settings switches; Customize picking a character, a banner, a theme."""
    r.js("() => { theme.shuffle = theme.shuffle; showModeSelect(); }")
    r.wake()
    r.pg.wait_for_timeout(1500)
    r.start(out)
    r.wait(1)
    r.tap("document.querySelector('.modecard[data-mode=\"drill\"]')"); r.wait(1.4)
    P = "document.querySelectorAll('.picks > label.pick')[%d]"
    for i in (0, 1, 2):
        r.tap(P % i); r.wait(.45)
    r.tap(P % 1); r.wait(.7)
    drag(r, P % 3 + ".querySelector('.box')", P % 7 + ".querySelector('.box')", 18)
    r.wait(1)
    r.tap("document.getElementById('bottomtab-start')"); r.wait(1.3)
    S = ".unitoptions-modal:not([hidden])"
    for t in ("Shuffle", "Hide answer", "Stopwatch", "Shuffle"):
        r.tap("[...document.querySelectorAll('%s label.opt')].find(l => l.offsetParent && l.textContent.indexOf(%s) >= 0)" % (S, json.dumps(t))); r.wait(.6)
    rng = "[...document.querySelectorAll('%s input[type=range]')].find(e => e.offsetParent)" % S
    b = r.js("() => { const e = " + rng + "; if(!e) return null; e.scrollIntoView({ block: 'center' }); const q = e.getBoundingClientRect(); return [q.left, q.right, q.top + q.height / 2]; }")
    if b:
        r.wait(.4)
        r.pg.mouse.move(b[1] - 6, b[2]); r.pg.mouse.down(); r.frame()
        for i in range(1, 31):
            r.pg.mouse.move(b[1] - 6 - (b[1] - b[0]) * .6 * i / 30, b[2]); r.frame()
        r.pg.mouse.up(); r.wait(.8)
        r.tap("[...document.querySelectorAll('%s .slider-allbtn')].find(e => e.offsetParent && !e.classList.contains('slider-maxbtn'))" % S); r.wait(1)
    r.tap(btn("Close", S)); r.wait(1.2)
    r.tap("document.getElementById('bottomtab-profile')"); r.wait(1.3)
    r.tap("document.querySelector('.profile-settings-tab-btn')"); r.wait(1.2)
    O = "[...document.querySelectorAll('#stage .profile-settings-tab label.opt')].find(l => l.offsetParent && l.textContent.indexOf(%s) >= 0)"
    for t in ("Swipe to next", "Auto-advance", "Auto-advance", "Swipe to next"):
        r.tap(O % json.dumps(t)); r.wait(.7)
    r.tap("document.querySelector('.navsegment.profiletabs .iconbtn')"); r.wait(1)
    r.tap(btn("Customize")); r.wait(1.3)
    for row, opt in (("character", ".avatarchar-option"), ("banner", ".banner-opt"), ("theme", ".swatch")):
        r.tap("document.querySelector('.cz-row-%s')" % row); r.wait(1.3)
        r.tap("[...document.querySelectorAll('#stage %s')].find(e => e.offsetParent && !e.classList.contains('locked') && !e.classList.contains('selected') && !e.classList.contains('on') && e.getBoundingClientRect().top > 120 && e.getBoundingClientRect().bottom < innerHeight - 120)" % opt)
        r.wait(1.3)
        r.tap("document.querySelector('#stage .back-link')"); r.wait(1.1)
    r.wait(1)


def chat(r, out):
    """The chat dock: opened, its tabs, a group chat started, a message
    typed and sent, a classmate joining and answering, closed."""
    r.js(CLASS_ROWS); r.js(USE_FAKE)
    r.js("() => { homeUnlockPlaying = true; showHome(); }")
    r.wake()
    r.pg.wait_for_timeout(2500)
    r.start(out)
    r.wait(1)
    r.tap("document.querySelector('.chatdock-btn')"); r.wait(1.4)
    for i in (1, 2, 0, 1):
        r.tap("document.querySelectorAll('.chatdock-tab')[%d]" % i); r.wait(.8)
    r.tap(btn("Start a group", ".chatdock"))
    r.until("typeof chatRoomCode === 'string' && !!chatRoomCode && !!document.querySelector('.chatdock .vroom-chat-input')", 6, then=1)
    r.tap("[...document.querySelectorAll('.chatdock .vroom-chat-input')].find(e => e.offsetParent)"); r.wait(.4)
    for ch in "Who's up for a race?":
        r.pg.keyboard.type(ch); r.frame()
    r.wait(.3)
    r.tap(btn("Send", ".chatdock")); r.wait(1.6)
    r.js("""() => { const now = Date.now(); return fbDb.collection('vrooms').doc(chatRoomCode).update({
        'participants.pub-devonte': { name: 'Devonte', avatarChar: 'ghost', joinedAt: now, seen: now },
        chatMessages: firebase.firestore.FieldValue.arrayUnion({ id: 'pub-devonte-' + now, key: 'pub-devonte', name: 'Devonte', text: 'Me! Penal Code?', ts: now }) }); }""")
    r.wait(2.4)
    r.tap("[...document.querySelectorAll('.chatdock .vroom-chat-input')].find(e => e.offsetParent)"); r.wait(.3)
    for ch in "Deal":
        r.pg.keyboard.type(ch); r.frame()
    r.tap(btn("Send", ".chatdock")); r.wait(1.4)
    r.tap("document.querySelector('.chatdock-close')"); r.wait(1.6)


LEVEL_NEAR = """() => {
  /* every badge held, so no rank wall stands in front of the next level
     (a wall turns the level-up into a knock), and ~60 XP to go */
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  store.unitPerfects = store.unitPerfects || {};
  topics.forEach(t => { store.unitPerfects[t] = Math.max(store.unitPerfects[t] || 0, badgeThresholdFor(t)); });
  const lp = levelProgress(store.lifetime.points);
  store.lifetime.points = store.lifetime.points + lp.toNext - 60;
  try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
  store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, TIER_ORDER_FULL.indexOf(rankOf(store)) + 1);
  saveStore(); return levelProgress(store.lifetime.points); }"""

FX_PICK = """() => {
  /* every hundo effect held (350 hundos) and %s picked; their pop-ups were
     shown long ago, so nothing but the effect plays */
  store.lifetime.perfectTests = Math.max(store.lifetime.perfectTests || 0, 360);
  store.hundoFx = "%s";
  store.unlocksShown = store.unlocksShown || {}; store.unlocksShown.fx = HUNDO_FX.map(f => f.id);
  try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
  saveStore(); return hundoFxInUse(); }"""

AT_WALL = """() => {
  /* no badges and far more XP than the first rank's level: the bar is held
     full at the wall, so a run knocks it and the rest overflows */
  store.unitPerfects = {}; store.rankFloor = 0; store.levelFloor = 0; store.levelWallRule = 325;
  store.lifetime.points = xpForLevel(26) + 400;
  try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
  saveStore(); return levelStateFor(store); }"""

NOVA_ADV = """() => { const el = document.getElementById('nova-intro'); if(!el || !el.__nova) return null;
  const n = el.__nova; return { i: n.index, c: n.count, typing: n.typing, sig: !!el.querySelector('.nt-signal:not(.is-found)') }; }"""


def nova_talk(r, read=1.6, max_sec=420):
    """Let him say every line at his own pace, hold it long enough to read,
    then a real tap on his bubble (the Goodbye / Let's go button on the last)."""
    t_end = len(r.times) + max_sec * FPS
    last = None
    while len(r.times) < t_end:
        st = r.js(NOVA_ADV)
        if not st:
            return
        if st["sig"] or st["typing"]:
            r.frame(); continue
        if st["i"] != last:
            last = st["i"]; r.wait(read)
            continue
        if st["i"] >= st["c"] - 1:
            r.tap("document.querySelector('#nova-intro .nt-go')"); r.wait(.8)
            last = None
        else:
            r.tap("document.querySelector('#nova-intro .nt-bubble')"); r.wait(.25)


def tour_through(r, read=1.6, max_steps=14):
    for _ in range(max_steps):
        r.until("!!document.getElementById('tour-next')", 8)
        if not r.js("() => !!document.getElementById('tour-next')"):
            return
        n = r.js("() => (document.getElementById('tour-tooltip') || {}).textContent.length || 80")
        r.wait(min(6, n / 72 + read))
        r.tap("document.getElementById('tour-next')", max_sec=2); r.wait(.5)


def nova_new(r, out):
    """A brand-new install: Welcome, I'm new here, the check,
    the class, a username, a character, all set, GENERATING PROFILE, then
    Nova's introduction and the main-menu tooltips."""
    pg = r.pg
    r.start(out)
    r.wait(1.5)
    r.tap("document.querySelector('.cosmic-welcome-btn.welcome-new')"); r.wait(1.4)
    r.tap("document.querySelector('.signupcheck-panel .signupcheck-go')"); r.wait(1.6)
    r.tap("document.querySelector('.welcomeintro-panel .next.playbtn')"); r.wait(1.4)
    r.tap("document.querySelector('.classselect-panel .modecard')"); r.wait(.8)
    r.tap("document.querySelector('.classselect-panel .next.playbtn')"); r.wait(1.0)
    r.tap("document.querySelector('.onboarding-shortform-panel .searchbox')"); r.wait(.4)
    for ch in "Madison":
        pg.keyboard.type(ch); r.wait(.12)
    r.wait(.8)
    r.tap("document.querySelector('.onboarding-shortform-panel .next.playbtn')"); r.wait(1.2)
    r.until("!!document.querySelector('.charselect-panel .avatarchar-option')", 6)
    r.tap("document.querySelectorAll('.charselect-panel .avatarchar-option')[2]"); r.wait(.8)
    r.tap("document.querySelectorAll('.charselect-panel .avatarchar-option')[0]"); r.wait(1.0)
    r.tap("document.querySelector('.charselect-panel .next.playbtn')"); r.wait(1.4)
    r.tap("document.querySelector('.onboarding-shortform-panel .next.playbtn')"); r.wait(.5)
    r.until("!document.getElementById('genprofile-overlay') && !!document.getElementById('nova-intro')", 30, then=.5)
    nova_talk(r)
    tour_through(r)
    r.wait(2.5)


def nova_existing(r, out):
    """An account from before him (Silver, three badges): Home, the signal,
    his introduction and recap ending in his goodbye, the What's New card,
    then the three returning tips."""
    r.js(SEED_RANK, "ranger")
    r.js("""() => { store.novaMet = 0; try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
      saveStore(); localStorage.setItem('class26e.intro.seen', '4'); }""")
    r.wake()
    r.start(out)
    r.js("() => showHome()")
    r.until("!!document.getElementById('nova-intro')", 15, then=.2)
    nova_talk(r)
    r.until("!!document.querySelector('#intro-pop .next, #intro-pop button')", 10, then=5.5)
    r.tap("Array.from(document.querySelectorAll('#intro-pop button')).find(b => /got it/i.test(b.textContent))"); r.wait(1)
    tour_through(r)
    r.wait(2.5)


SCENARIOS = {
    "home-idle": (home_idle, 60, "Home on its own for 20s: the ambience he loves, untouched"),
    "results-hundo": (results(0), 150, "a real Identity Crimes drill, every answer right: count, grade, XP box, bar, the hundo effect"),
    "hundo-confetti": (results(0, extra=FX_PICK % ("confetti", "confetti"), tail=3), 150, "a real 100%: Confetti"),
    "hundo-fireworks": (results(0, extra=FX_PICK % ("fireworks", "fireworks"), tail=3), 150, "a real 100%: Fireworks"),
    "hundo-underwater": (results(0, extra=FX_PICK % ("underwater", "underwater"), tail=3), 150, "a real 100%: Underwater"),
    "hundo-bubbles": (results(0, extra=FX_PICK % ("bubbles", "bubbles"), tail=3), 150, "a real 100%: Bubbles"),
    "hundo-ufo": (results(0, extra=FX_PICK % ("ufo", "ufo"), tail=3), 170, "a real 100%: UFO"),
    "results-wall": (results(2, extra=AT_WALL), 150, "a pass with the XP bar held full at a wall: the full bar and the extra XP"),
    "results-pass": (results(2), 150, "the same drill with 2 of 12 missed (83%): a pass"),
    "results-fail": (results(6), 150, "6 of 12 missed (50%): under the pass mark"),
    "results-levelup": (results(2, extra=LEVEL_NEAR), 150, "a pass that crosses a level: the level-up jingle on the XP bar"),
    "roadmap-climb": (roadmap, 80, "the Rank tab's road map climbing to where you are"),
    "rankup-journey": (rankup_journey, 160, "a rank-up as people see it: Home locks, Profile, the road map, the cutscene, the reward card, back to Profile"),
    "badge-cutscene": (badge_cutscene, 90, "BADGE FOUND: the badge, the case rising, latches, lid, the drop"),
    "rankup-cutscene": (rankup, 90, "a rank-up cutscene (Gold)"),
    "supernova": (supernova, 120, "Supernova on Home (the comet streaks, now silent) and its cutscene"),
    "streak": (streak, 150, "a Penal Code drill, eight right answers each a streak tier (10, 25, 50, 75, 100, 150, 250, 350): the pop and its sound"),
    "unlock-banner": (unlock_banner, 90, "the unlock banner on Home: a character, a banner, a character after a scene"),
    "flare-void": (flare_scene("playVoidFlareScene", 40), 120, "the secret flare scene that brings Void"),
    "flare-umbra": (flare_scene("playUmbraFlareScene", 40), 120, "the secret flare scene that brings Umbra"),
    "flare-horizon": (flare_scene("playHorizonFlareScene", 40), 120, "the secret flare scene that brings Horizon"),
    "flare-genesis": (flare_scene("playGenesisFlareScene", 40), 120, "the secret flare scene that brings Genesis"),
    "flare-first": (flare_scene("(d => playFirstFlaresScene('orange', d))", 20), 80, "one of the first two secret flares' scenes"),
    "tabs": (tabs, 90, "the tab bar: Home, Profile and its top tabs, Leaderboard, Calendar, and a drag along the bar"),
    "leaderboard": (leaderboard, 90, "the Leaderboard with a class on it: the boards, Find me, a classmate's card"),
    "lobby": (lobby, 120, "a Virtual Room: Host, Match settings, a classmate joining and readying, Ready up, the countdown"),
    "selections": (selections, 150, "the mode, units ticked, untick, drag-select, the start sheet's switches and slider, Settings switches, Customize picks"),
    "chat": (chat, 90, "the chat dock: its tabs, a group chat, a message sent, a classmate answering"),
    "nova-new": (nova_new, 600, "a brand-new install: sign-up, GENERATING PROFILE, Nova's introduction, the main-menu tips", "fresh"),
    "nova-existing": (nova_existing, 600, "an account from before Nova: his signal, introduction and recap, What's New, the returning tips"),
    "test": (test, 120, "a drill from LOADING TEST: a wrong answer, then right answers into the 10-in-a-row streak pop"),
}

if "--list" in sys.argv or len(sys.argv) < 3:
    for k, v in SCENARIOS.items():
        print("  %-16s %s" % (k, v[2]))
    sys.exit(0 if "--list" in sys.argv else 2)

name, out = sys.argv[1], os.path.abspath(sys.argv[2])
if name not in SCENARIOS:
    sys.exit("no scenario " + name)
os.makedirs(os.path.dirname(out), exist_ok=True)
s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
SRV = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
threading.Thread(target=SRV.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

fn, budget = SCENARIOS[name][:2]
mode = SCENARIOS[name][3] if len(SCENARIOS[name]) > 3 else "used"
with sync_playwright() as pw:
    r = Rec(pw, budget, mode)
    fn(r, out + ".video.mp4")
    log = r.finish(out)
SRV.shutdown()
played = [p for p in log["plays"] if p["played"]]
print("%s -> %s: %d frames (%.1fs), %d sounds played, %d refused, peak %.3f%s" % (
    name, out, log["frames"], log["frames"] / FPS, len(played), len(log["plays"]) - len(played), log["peak"] or 0,
    (", errors: " + "; ".join(log["errors"][:3])) if log["errors"] else ""))
