#!/usr/bin/env python3
"""The whole sign-up as a new person sees it, WITH THE APP'S OWN SOUND - from the moment the link is opened to Home.

  python3 tools/record-signup.py OUT.mp4 [--device phone|laptop] [--fps 30]

Madison (383): "I'm gonna need a video of the sign up process. A video from a phone, and laptop ... The video will start from
the second you click the link as if you never have all the way to the point of hitting home."

tools/record-sound.py's nova-new starts on Welcome, after the page has loaded with the splash taken away. This one starts the
recording BEFORE the page loads: record-sound's page clock is an init script here (installed before the app's first line runs),
so the boot, the splash and its fade, the first-visit page (Welcome to NOVA, scrolled through), and everything after run on the
video's clock, frame by frame. The sound is record-sound's: the app's own engine on an offline context on that clock, muxed
under the video (silent until the first tap, as on a phone).
  phone  - an iPhone 17 Pro Max Safari tab (440x838 under Safari's bars, iPhone Safari's user agent, touch), a link opened there
  laptop - a 1440x820 browser window
The walk: the splash -> Welcome to NOVA, scrolled to its end -> Let's get started -> Welcome -> I'm new here -> New to Nova? ->
I'm new, continue -> Select your classes (Police Academy) -> Continue -> GENERATING PROFILE -> Nova (your name, your partner, the
save-your-code card) -> the main menu's tips -> Home. The cloud is check-vroom's in-memory Firestore (the CDN is blocked here);
the name typed is a made-up one. A log of every sound played is written beside the MP4 (OUT.sound.json)."""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
DEVICE = sys.argv[sys.argv.index("--device") + 1] if "--device" in sys.argv else "phone"
OUT = os.path.abspath(sys.argv[1])
# record-sound's machinery (its devices, sound, clock, Rec, Nova's walk), set up for this device
sys.argv = [os.path.join(HERE, "record-sound.py"), "nova-new", OUT, "--device", "phone-safari" if DEVICE == "phone" else "laptop"] + \
           (["--mode", "safari"] if DEVICE == "phone" else []) + (["--fps", sys.argv[sys.argv.index("--fps") + 1]] if "--fps" in sys.argv else [])
src = open(os.path.join(HERE, "record-sound.py"), encoding="utf-8").read()
G = {"__file__": os.path.join(HERE, "record-sound.py"), "__name__": "record_signup"}
exec(src.split("\nSCENARIOS = {")[0], G)
# frames at 2x on the phone, 1.5x on the laptop: sharp, and quick enough to shoot a five-minute walk
G["DEVICES"]["phone-safari"] = (440, 838, 2)
G["DEVICES"]["laptop"] = (1440, 820, 1.5)
NAME = "Alex Rivera"
# the page is served from the repo (record-sound starts this after its scenario table)
import socket, http.server, functools, threading
_s = socket.socket(); _s.bind(("127.0.0.1", 0)); _port = _s.getsockname()[1]; _s.close()
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
_srv = http.server.ThreadingHTTPServer(("127.0.0.1", _port), functools.partial(_Q, directory=G["ROOT"]))
threading.Thread(target=_srv.serve_forever, daemon=True).start()
G["URL"] = "http://127.0.0.1:%d/index.html" % _port

exec(r'''
class LinkRec(Rec):
    """Rec, but the clock is in before the page's first script and the frames start as the page is opened."""
    def __init__(self, pw, budget):
        w, h, dpr = DEVICES[DEV]
        self.w, self.h = w, h
        self.br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required", "--force-device-scale-factor=%s" % dpr])
        extra = {"user_agent": IPHONE_SAFARI_UA, "is_mobile": True, "has_touch": True} if MODE == "safari" else {}
        self.ctx = self.br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, **extra)
        self.ctx.add_init_script(FAKE_FS)
        self.ctx.add_init_script(SEED_FRESH)
        self.ctx.add_init_script(REC_AUDIO.replace("%BUDGET%", str(budget)))
        self.ctx.add_init_script("(" + CLOCK + ")();")
        pg = self.pg = self.ctx.new_page()
        self.errs = []
        pg.on("pageerror", lambda e: self.errs.append(str(e)[:200]))
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"},
                                                          body='{"build":"%s","frameId":"","note":""}' % BUILD))
        pg.route("**/firebasejs/**", lambda r: r.abort())
        self.cdp = self.ctx.new_cdp_session(pg)
        self.ff = None; self.times = []; self.vpath = None

    def open_link(self, vpath):
        self.vpath = vpath
        self.ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                                    "-preset", "veryfast", "-r", str(FPS), vpath], stdin=subprocess.PIPE)
        self.pg.goto(URL, wait_until="commit")
        for _ in range(200):
            if self.pg.evaluate("() => !!window.__clk && !!document.body"): break
            self.pg.wait_for_timeout(20)
''', G)
Rec, LinkRec = G["Rec"], G["LinkRec"]

def scroll_gs(r):
    """Welcome to NOVA, read as a person would: a stop on each section, an eased glide between them, to the end."""
    n = r.js("() => { const s = document.querySelector('.gs-scroll'); return s ? Math.ceil((s.scrollHeight - s.clientHeight) / (s.clientHeight * .8)) : 0; }") or 0
    for _ in range(int(n) + 1):
        r.js("() => { const s = document.querySelector('.gs-scroll'); window.__gs = { y0: s.scrollTop, y1: Math.min(s.scrollHeight - s.clientHeight, s.scrollTop + s.clientHeight * .8), k: 0 }; }")
        for k in range(1, 25):
            r.js("(k) => { const s = document.querySelector('.gs-scroll'), g = window.__gs, u = k / 24, e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; s.scrollTop = g.y0 + (g.y1 - g.y0) * e; }", k)
            r.frame()
        r.wait(1.7)

def nova_walk(r, read=1.7, max_sec=480):
    """Nova at his own pace (record-sound's nova_talk) - his name question, the partner, and the save-your-code card."""
    t_end = len(r.times) + max_sec * G["FPS"]
    last = None
    while len(r.times) < t_end:
        if r.js("() => !!document.getElementById('savecode-card')"):
            r.wait(3.2)
            r.tap("document.querySelector('#savecode-card .savecode-ack')"); r.wait(.8)
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
                r.tap("document.querySelector('#nova-intro .nt-ask-input')"); r.wait(.4)
                for ch in NAME:
                    r.pg.keyboard.type(ch); r.wait(.11)
                r.wait(.7)
                r.tap("document.querySelector('#nova-intro .nt-ask-name .nt-ask-go')"); r.wait(1.2)
                r.until("!document.querySelector('#nova-intro .nt-ask-name')", 8)
            elif st.get("char"):
                r.tap("document.querySelectorAll('#nova-intro .nt-ask-char .avatarchar-option')[2]"); r.wait(.9)
                r.tap("document.querySelectorAll('#nova-intro .nt-ask-char .avatarchar-option')[0]"); r.wait(1.0)
                r.tap("document.querySelector('#nova-intro .nt-ask-char .nt-ask-go')"); r.wait(1.0)
            last = None
            continue
        if st["i"] != last:
            last = st["i"]; r.wait(read); continue
        if st["i"] >= st["c"] - 1:
            r.tap("document.querySelector('#nova-intro .nt-go')"); r.wait(.8); last = None
        else:
            r.tap("document.querySelector('#nova-intro .nt-bubble')"); r.wait(.25)

SCREEN = "() => (document.querySelector('#stage [data-screen]') || {}).dataset ? document.querySelector('#stage [data-screen]').dataset.screen : null"
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    r = LinkRec(pw, 720)
    r.open_link(OUT + ".video.mp4")
    marks = []
    def mark(what): marks.append((what, round(len(r.times) / G["FPS"], 2))); print("  %6.1fs  %s" % (len(r.times) / G["FPS"], what), flush=True)
    mark("link opened")
    r.until("!document.getElementById('splashscreen') && !!document.querySelector('#stage [data-screen]')", 25, then=.3)
    mark("splash gone: " + str(r.js(SCREEN)))
    # the cloud stand-in, once the app is up (record-sound's fresh setup, without taking the splash away)
    r.js("() => { try{ __stub(); fbDb = window.__fakeDb; if(window.__osr0) onSnapshotResilient = window.__osr0; }catch(e){} }")
    r.pg.evaluate(G["LOG_PLAYS"])
    if r.js(SCREEN) == "getstarted":
        r.wait(2.6)
        scroll_gs(r)
        r.until("(() => { const b = document.querySelector('.gs-go'); return !!b && b.getBoundingClientRect().height > 0 && getComputedStyle(b).opacity > .9; })()", 8, then=1.0)
        mark("Let's get started")
        r.tap("document.querySelector('.gs-go')"); r.wait(.4)
    r.until("!!document.querySelector('#stage [data-screen=\"welcome\"]')", 10, then=2.8)
    mark("Welcome")
    r.tap("document.querySelector('.cosmic-welcome-btn.welcome-new')"); r.wait(.4)
    r.until("!!document.querySelector('#stage .signupcheck-panel')", 8, then=2.8)
    mark("New to Nova?")
    r.tap("document.querySelector('.signupcheck-panel .signupcheck-go')"); r.wait(.4)
    r.until("!!document.querySelector('#stage .classselect-panel')", 8, then=2.0)
    mark("Select your classes")
    r.tap("document.querySelector('.classselect-panel .class-card.is-academy')"); r.wait(1.1)
    r.tap("document.querySelector('.classselect-panel #nextbtn')"); r.wait(.4)
    mark("GENERATING PROFILE")
    r.until("!document.getElementById('genprofile-overlay') && !!document.getElementById('nova-intro')", 40, then=.4)
    mark("Nova")
    nova_walk(r)
    mark("tips")
    G["tour_through"](r)
    r.until("!!document.querySelector('#stage [data-screen=\"home\"]') && !document.getElementById('tour-next')", 10)
    mark("Home")
    r.wait(4)
    state = r.js("() => ({ screen: (document.querySelector('#stage [data-screen]') || {dataset:{}}).dataset.screen, name: store.firstName, char: store.avatarChar, onb: store.onboardingComplete, code: !!syncCode })")
    log = r.finish(OUT)
played = [p for p in log["plays"] if p["played"]]
log["marks"] = marks; log["end"] = state
json.dump(log, open(OUT + ".sound.json", "w"), indent=1)
print("%s: %d frames (%.1fs), %d sounds played, %d refused, peak %.3f, end %s%s" % (
    OUT, log["frames"], log["frames"] / G["FPS"], len(played), len(log["plays"]) - len(played), log["peak"] or 0, state,
    (", errors: " + "; ".join(log["errors"][:3])) if log["errors"] else ""))
