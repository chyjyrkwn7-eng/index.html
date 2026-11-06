#!/usr/bin/env python3
"""Records the clips on the Get Started page (landing/*.mp4, and landing/*.jpg - each clip's FIRST frame, its poster).

  python3 tools/record-landing.py [academy|hundo|rank|customize ...]
  (the Fire Code clips, test and ifc, are tools/record-landing-ifc.py - they need the owner's book and pdf.js)

BUILD 384 (round 2): "Ensure the videos through the screen are high quality cause they didn't look like it. Ensure the videos
are good to go cause some seem weird and start at weird spots and skip around like the upload pdf one."
What was wrong with the 330 clips, and what this does instead:
  * SIZE: a 360x780 page at 1.5x, scaled to 540px and encoded at crf 29 (80-260 kb/s) - shown 255px wide on a 3x phone, that
    is 765 pixels drawn from 540, starved. Now a 390x845 page (the clip frame's 9:19.5) at 2x: 780x1690, x264 crf ~20, High
    profile, yuv420p, faststart, no audio - each file kept under ~3 MB.
  * TIMING: the screencast only sends a frame when something changed, and the old encoder gave each frame its gap to the next
    CAPPED AT ONE SECOND, so every still moment over a second was cut short - the clip jumped. Now the frames are put on a
    true 30 fps clock (each held until the next one arrives), so a pause is as long as it was.
  * START: each clip starts at its own beginning (the first thing the scene shows, not a mid-way moment), and its last half
    second dissolves into its first frame so the loop has no seam.
  * POSTER: the still is the clip's first frame (it was a mid-clip moment for hundo and rank, so the clip jumped back when it
    started playing).
  * No real classmate or owner name: the account is a fixture ("Alex").
A clip may speed up a stretch (SPEED: (from_s, to_s, factor)) - uniformly, so it plays faster, never skips."""
import base64, functools, http.server, io, json, os, socket, subprocess, sys, threading, time
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get("LANDING_OUT", os.path.join(ROOT, "landing"))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
W, H, DSF = 390, 845, 2          # the page's CSS size and pixel ratio: clips are 780x1690
FPS = 30
CRF = int(os.environ.get("LANDING_CRF", "20"))
MAX_BYTES = 3 * 1024 * 1024
FADE = .5                         # the last half second dissolves into the first frame

SEED = {
    "onboardingComplete": True, "firstName": "Alex", "avatarChar": "ninja", "publicId": "pubfixture0384",
    "tourRev": 999, "rankMapFx244": True, "novaMet": 99, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
    "seenMainMenuTour": True, "seenClassTip": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
    "seenRankingsTour": True, "seenAppearanceTour": True,
    # sound off: a clip is silent, and the results' count runs to the sound's clock, which slow motion cannot slow
    "theme": {"soundOn": False, "soundOn327": True, "vibrate": False},
    "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "gamePlays": 8,
                 "perfectTests": 64, "longestStreak": 44, "currentStreak": 12},
    "unitPerfects": {"Professionalism and Ethics": 35, "TCOLE Rules": 35, "Penal Code": 35, "Racial Profiling": 35,
                     "Victims of Crime": 35, "Identity Crimes": 34},
}
SEEN_KEYS = ("freshstart", "intro.seen", "unithold.tip", "daily.seen", "savecode.asked", "savecode.card", "getstarted",
             "penal55124.seen", "penal124256.seen", "penal256578.seen")


def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    http.server.ThreadingHTTPServer.handle_error = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def init_script(seed, extra=""):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1');"
    s += "".join("localStorage.setItem('class26e.%s','1');" % k for k in SEEN_KEYS)
    s += "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(seed))
    s += "localStorage.setItem('class26e.synccode','FIXT-0384');"
    return s + extra + " })()"


# HOW A 2x CLIP IS CAPTURED HERE. The screencast sends frames at the page's CSS size (390x845 at any pixel ratio), so the
# page is a 780x1690 mobile view whose own viewport tag says width=390 at initial-scale 2: it lays out as a 390px phone
# (innerWidth 390, the phone's media queries) and draws at twice that, and devicePixelRatio reads 2 so its canvases (badges,
# the code pictures) are drawn at 2x too. At that size a frame takes ~70-110ms to capture here (more under load), so the
# page runs in SLOW MOTION while it is recorded: its clock (setTimeout/setInterval, requestAnimationFrame, performance.now,
# Date.now) and every CSS/Web animation (CDP Animation.setPlaybackRate) run at RATE of real time, together, and each frame's
# time is its capture time x RATE - a smooth 30 fps clip from a slow capture, with nothing in the page out of step.
RATE = float(os.environ.get("LANDING_RATE", ".2"))
TIMEWARP = r"""(()=>{
  const RP = performance.now.bind(performance), RD = Date.now, RST = window.setTimeout.bind(window), RSI = window.setInterval.bind(window);
  let rate = 1, baseReal = RP(), baseVirt = baseReal;
  const dateOff = RD() - RP();
  const v = t => baseVirt + (t - baseReal) * rate;
  window.__timeRate = r => { const now = RP(); baseVirt = v(now); baseReal = now; rate = r; };
  /* line the page clock up with the frame clock once both run at the new rate, 2ms behind it, so a frame's time is never
     earlier than the moment the frame was asked for */
  window.__timeSync = () => new Promise(res => requestAnimationFrame(t => { const d = t - v(RP()) - 2; baseVirt += d; res(d); }));
  performance.now = () => v(RP());
  /* Date.now and new Date() alike (code that mixes them must not see two clocks) */
  const vDate = () => Math.round(v(RP()) + dateOff), RDate = Date;
  window.Date = new Proxy(RDate, {
    construct(t, a, nt){ return Reflect.construct(t, a.length ? a : [vDate()], nt); },
    get(t, p, r){ return p === 'now' ? vDate : Reflect.get(t, p, r); } });
  window.setTimeout = function(fn, ms){ const a = [].slice.call(arguments, 2); return RST(fn, Math.max(0, +ms || 0) / rate, ...a); };
  window.setInterval = function(fn, ms){ const a = [].slice.call(arguments, 2); return RSI(fn, Math.max(1, +ms || 0) / rate, ...a); };
  /* requestAnimationFrame is left alone: its frame time is the animation clock, which Animation.setPlaybackRate already slows
     (wrapping it slowed it twice - a count read "-740,591 XP") */
  addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = 'html{scroll-behavior:auto !important}'; document.head.appendChild(s); });
})()"""
_INDEX = {}


def page_html():
    if "src" not in _INDEX:
        src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        tag = 'content="width=device-width, initial-scale=1, viewport-fit=cover"'
        if tag not in src: raise SystemExit("the viewport tag changed - update record-landing.py")
        _INDEX["src"] = src.replace(tag, 'content="width=%d, initial-scale=%d, minimum-scale=%d, maximum-scale=%d, user-scalable=no, viewport-fit=cover"' % (W, DSF, DSF, DSF))
    return _INDEX["src"]


def new_page(br, port, seed=None, extra="", route=None):
    ctx = br.new_context(viewport={"width": W * DSF, "height": H * DSF}, device_scale_factor=1, is_mobile=True, has_touch=True)
    if route: route(ctx)
    ctx.add_init_script("Object.defineProperty(window,'devicePixelRatio',{get:()=>%d,configurable:true});" % DSF)
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(TIMEWARP)
    ctx.add_init_script(init_script(seed or SEED, extra))
    pg = ctx.new_page()
    body = page_html()
    pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
    pg.goto("http://127.0.0.1:%d/index.html" % port)
    pg.wait_for_timeout(3200)
    # the fixture's rewards are owed to it (a "Challenge complete" card would come up over the clip): marked shown, then a
    # fresh launch
    pg.evaluate("()=>{ try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); saveStore(); }catch(e){} }")
    pg.reload(); pg.wait_for_timeout(3200)
    settle(pg)
    return ctx, pg


def settle(pg):
    """no splash, no tour, no pop-up over what is recorded"""
    pg.evaluate("""()=>{ document.getElementById('splashscreen')?.remove();
      try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
      try{ homeUnlocksOwed = () => false; }catch(e){}
      document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .app-banner, .rs-spot').forEach(n => n.remove());
      document.body.classList.remove('cutscene-focus'); }""")
    pg.wait_for_timeout(300)


_SLOW = {"r": 1.0}
# (384 round 4) THE PACE BETWEEN TAPS. Madison: the clips "cut way too fast" - the animations in them are at real speed (they were
# captured in slow motion and put back on a true clock), but the taps followed each other half a second apart, quicker than any
# person reads and answers. HOLD stretches only the pauses a person would take (before an answer, between questions, on each
# pick); every animation stays at its own speed, so the clips play at 1x in the app (no playbackRate) and move as the app does.
HOLD = float(os.environ.get("LANDING_HOLD", "1.9"))


def wait(pg, ms):
    """wait `ms` of the PAGE's time (slowed while recording)"""
    pg.wait_for_timeout(int(ms / _SLOW["r"]))


class Recorder:
    """CDP screencast frames at the page's full pixel size, the page in slow motion; each frame's time is page time."""
    def __init__(self, page):
        self.pg = page
        self.cdp = page.context.new_cdp_session(page)
        self.frames, self.on = [], False
        self.cdp.on("Page.screencastFrame", self._frame)
        try: self.cdp.send("Animation.enable")
        except Exception: pass
    def _frame(self, ev):
        try: self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception: pass
        if self.on: self.frames.append((ev["metadata"].get("timestamp") or time.time(), base64.b64decode(ev["data"])))
    def slow(self, r):
        self.pg.evaluate("(r)=>window.__timeRate && window.__timeRate(r)", r)
        self.cdp.send("Animation.setPlaybackRate", {"playbackRate": r})
        self.pg.evaluate("()=>window.__timeSync && window.__timeSync()")
        _SLOW["r"] = r
    def start(self, rate=None):
        """rate: slower still for a heavy scene (a cutscene draws far more per frame than a question does)"""
        self.rate = rate or RATE
        self.slow(self.rate)
        self.frames, self.on = [], True
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "everyNthFrame": 1})
    def stop(self):
        self.on = False
        try: self.cdp.send("Page.stopScreencast")
        except Exception: pass
        try: self.slow(1.0)
        except Exception: pass
        # page time: a frame captured t real seconds in is t x rate into the clip
        if not self.frames: return []
        t0 = self.frames[0][0]
        return [(t0 + (t - t0) * self.rate, b) for t, b in self.frames]


def remap(t, speed):
    """clip time for recorded time t (seconds from the start): a stretch (a, b, k) plays k times faster"""
    out, last = 0.0, 0.0
    for a, b, k in sorted(speed or []):
        if t <= a: return out + (t - last)
        out += a - last
        if t <= b: return out + (t - a) / k
        out += (b - a) / k
        last = b
    return out + (t - last)


def clip_frames(frames, speed=None, trim_start=0.0, trim_end=0.0):
    """the clip's frames on a true FPS clock: each captured frame held until the next arrives (a still moment keeps its
    length), an optional uniform speed-up, the last FADE seconds dissolved into the first frame"""
    t0 = frames[0][0]
    times = [remap(t - t0, speed) for t, _ in frames]
    start, end = trim_start, times[-1] - trim_end
    n = int((end - start) * FPS) + 1
    j = 0
    while j + 1 < len(frames) and times[j + 1] <= start: j += 1
    first = Image.open(io.BytesIO(frames[j][1])).convert("RGB")
    size = first.size
    nfade = int(FADE * FPS)
    cur, cur_j = None, -1
    for i in range(n):
        want = start + i / FPS
        while j + 1 < len(frames) and times[j + 1] <= want: j += 1
        if j != cur_j:
            cur = Image.open(io.BytesIO(frames[j][1])).convert("RGB")
            if cur.size != size: cur = cur.resize(size, Image.LANCZOS)
            cur_j = j
        im = cur
        k = i - (n - nfade)
        if k >= 0: im = Image.blend(cur, first, min(1.0, (k + 1) / nfade))
        yield i, n, first, im


def encode(frames, name, speed=None, trim_start=0.0, trim_end=0.0, crf=None):
    """H.264 at crf ~20 (stepped up only if the file would pass MAX_BYTES), piped straight into ffmpeg; the poster is the
    clip's first frame"""
    if not frames: raise SystemExit("no frames for " + name)
    os.makedirs(OUT, exist_ok=True)
    mp4 = os.path.join(OUT, name + ".mp4")
    c = crf or CRF
    while True:
        p = None
        for i, n, first, im in clip_frames(frames, speed, trim_start, trim_end):
            if p is None:
                size = im.size
                p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                      "-s", "%dx%d" % size, "-r", str(FPS), "-i", "-",
                                      "-c:v", "libx264", "-preset", "slow", "-crf", str(c), "-pix_fmt", "yuv420p",
                                      "-profile:v", "high", "-level", "4.1", "-g", str(FPS * 2), "-movflags", "+faststart",
                                      "-an", mp4], stdin=subprocess.PIPE)
                poster = first
            p.stdin.write(im.tobytes())
        p.stdin.close(); p.wait()
        if p.returncode: raise SystemExit("ffmpeg failed for " + name)
        if os.path.getsize(mp4) <= MAX_BYTES or c >= 30: break
        c += 2
    poster.save(os.path.join(OUT, name + ".jpg"), quality=80, optimize=True, progressive=True)
    print("  %-10s %4d frames in, %4d out (%.1fs)  %dx%d  crf %d  %6.0f KB  poster %4.0f KB" % (
        name, len(frames), n, n / FPS, size[0], size[1], c, os.path.getsize(mp4) / 1024,
        os.path.getsize(os.path.join(OUT, name + ".jpg")) / 1024), flush=True)
    gaps = sorted(b[0] - a[0] for a, b in zip(frames, frames[1:]))
    if gaps: print("  %-10s capture gaps: median %.0fms, 95%% %.0fms, worst %.0fms" % (
        "", gaps[len(gaps) // 2] * 1000, gaps[int(len(gaps) * .95)] * 1000, gaps[-1] * 1000), flush=True)


# ---------------------------------------------------------------- driving
# Taps are the app's own click on the element (the page is drawn at 2x, so a touch would need its coordinates doubled);
# fixed waits are page time (wait()), polls are real time.
def start_unit_run(pg, unit, idx=None):
    pg.evaluate("""([unit, idx])=>{ cfg.source='all'; cfg.mode='drill'; cfg.units=[unit];
      beginRun(idx || QUESTIONS.map((q,i)=>i).filter(i => (QUESTIONS[i].topic||'').trim() === unit)); }""", [unit, idx])
    pg.wait_for_selector(".qpanel .choice", timeout=25000)
    pg.wait_for_timeout(900)


def answer(pg, right=True, ms=1100):
    ms = int(ms * HOLD)
    pg.evaluate("""(right)=>{ const r = correctSlot(order[pos]);
      const all = [...document.querySelectorAll('.qpanel .choice')];
      const c = right ? all.find(x => x.dataset.index === String(r)) : all.find(x => x.dataset.index !== String(r) && !x.disabled && !x.classList.contains('wrong'));
      c && c.click(); }""", right)
    wait(pg, ms)


def next_q(pg, ms=500):
    ms = int(ms * HOLD)
    p = pg.evaluate("()=>pos")
    pg.evaluate("()=>document.getElementById('nextbtn')?.click()")
    for _ in range(200):
        pg.wait_for_timeout(50)
        if pg.evaluate("()=>pos") != p: break
    wait(pg, ms)


def glide_to(pg, sel, block="center", ms=700):
    """scroll an element into view on the page's own (slowed) clock, eased - not the browser's smooth scroll, which would
    run in real time"""
    return pg.evaluate("""([sel, block, ms])=>new Promise(res => {
      const e = [...document.querySelectorAll(sel)].filter(x => x.isConnected && x.getBoundingClientRect().height > 0).pop(); if(!e) return res(false);
      const se = document.scrollingElement, r = e.getBoundingClientRect(), y0 = se.scrollTop;
      const want = block === 'center' ? y0 + r.top + r.height / 2 - innerHeight / 2 : (block === 'end' ? y0 + r.bottom - innerHeight + 24 : y0 + r.top - 80);
      const y1 = Math.max(0, Math.min(se.scrollHeight - innerHeight, want)), t0 = performance.now();
      const step = () => { const k = Math.min(1, (performance.now() - t0) / ms), q = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        se.scrollTop = y0 + (y1 - y0) * q; if(k < 1) requestAnimationFrame(step); else res(true); };
      requestAnimationFrame(step); })""", [sel, block, ms])


def answer_all(pg, upto=0):
    stop = pg.evaluate("()=>order.length") - upto
    for _ in range(stop):
        p = pg.evaluate("()=>pos")
        pg.evaluate("""()=>{const r=correctSlot(order[pos]); document.querySelector('.choice[data-index="'+r+'"]').click();}""")
        pg.wait_for_timeout(420)
        if not pg.evaluate("()=>!!document.getElementById('nextbtn')"): break
        pg.evaluate("()=>document.getElementById('nextbtn').click()")
        for _ in range(30):
            pg.wait_for_timeout(120)
            if pg.evaluate("()=>pos") != p or not pg.evaluate("()=>document.querySelector('.choice')"): break
        if not pg.evaluate("()=>document.querySelector('.choice')"): break


# ---------------------------------------------------------------- scenes
ACADEMY_QS = [90, 82, 91]     # TCOLE Rules: what TCOLE stands for, continuing-education hours, the proficiency certificates


def scene_academy(pg, rec):
    """Police Academy questions, as they are played: right, a miss then right, right"""
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
    start_unit_run(pg, "TCOLE Rules", ACADEMY_QS)
    rec.start(); wait(pg, int(1000 * HOLD))
    answer(pg, True, 1500); next_q(pg, 700)
    answer(pg, False, 1300); answer(pg, True, 1500); next_q(pg, 700)
    answer(pg, True, 1800)
    return {}


def scene_hundo(pg, rec):
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(400)
    start_unit_run(pg, "Identity Crimes")
    answer_all(pg, upto=1)
    pg.wait_for_timeout(600)
    rec.start(rate=.1); wait(pg, 900)
    answer(pg, True, 1300)
    pg.evaluate("()=>document.getElementById('nextbtn').click()")
    wait(pg, 9800)
    return {}


SEED_RANK = """(k)=>{
  const rule = TIER_UNLOCKS[k] || {};
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  store.unitPerfects = {};
  topics.slice(0, rule.badges || 0).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
  let pts = 1000; while(levelProgress(pts).level < (rule.level || 0)) pts += 500;
  store.lifetime = store.lifetime || {}; store.lifetime.points = pts;
  store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, TIER_ORDER_FULL.indexOf(k) + 1);
  homeUnlockPlaying = true; saveStore(); }"""


def scene_rank(pg, rec):
    """the Silver rank-up, all of it (~29s on its own clock): the wind-up and the long whirl (1-19s) play 2.4x faster, so
    the clip is ~18s and ends on SILVER (the old clip stopped at 15s, mid-whirl, before the rank was ever named)"""
    pg.evaluate(SEED_RANK, "ranger")
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1200)
    rec.start(rate=.08); wait(pg, 500)
    pg.evaluate("(k)=>{store.pendingTierCutscene=k; playTierCutscene(k)}", "ranger")
    wait(pg, int(os.environ.get("RANK_MS", "29500")))
    sp = [tuple(map(float, x.split(":"))) for x in os.environ.get("RANK_SPEED", "1.0:19.0:1.4").split(",") if x]
    return {"speed": sp, "trim_end": float(os.environ.get("RANK_TRIM", "1.8"))}


def scene_customize(pg, rec):
    pg.evaluate("()=>showCustomize('character')"); pg.wait_for_timeout(1500)
    rec.start(); wait(pg, 900)
    for k in (2, 5, 8, 3, 6, 1):
        pg.evaluate("(k)=>{ const o=[...document.querySelectorAll('.screen-customize .avatarchar-option:not(.locked)')]; o[k] && o[k].click(); }", k)
        wait(pg, int(1500 * HOLD))
    return {}


SCENES = {"academy": scene_academy, "hundo": scene_hundo, "rank": scene_rank, "customize": scene_customize}


def main(argv):
    want = [a for a in argv if not a.startswith("-")] or list(SCENES)
    srv, port = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for name in want:
            ctx, pg = new_page(br, port)
            rec = Recorder(pg)
            opts = SCENES[name](pg, rec) or {}
            frames = rec.stop(); ctx.close()
            encode(frames, name, **opts)
        br.close()
    srv.shutdown()


if __name__ == "__main__":
    main(sys.argv[1:])
