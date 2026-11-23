#!/usr/bin/env python3
"""Build 384 (claude/b384-cameo): a short video of each character cameo, for Madison. iPhone 17 Pro Max (440x956 at 3x, installed),
CDP screencast at the device's own pixels, H.264 (yuv420p, faststart) at 30fps, plus a JPEG contact sheet of stills.
Each one is forced with the app's own hook (cameoForce) or, for cheer and oops, planned and set off by a real touch on an answer
(cameoAnswered, the path a test takes); the swipe to the next question is a real touch drag.
Run:  python3 tools/record-b384-cameo.py OUTDIR [kind ...]"""
import base64, functools, http.server, json, os, re, shutil, socket, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    import glob as _g; CHROME = (sorted(_g.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "cameo-videos")
ONLY = sys.argv[2:]
os.makedirs(OUT, exist_ok=True)
SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
BUILD = (re.search(r'const APP_BUILD = "([^"]+)"', SRC) or [None, ""])[1]
from playwright.sync_api import sync_playwright
# the page set-up is the gate's (same seeds, the same Firestore stub, the same inset patch)
_g = open(os.path.join(HERE, "check-b384-cameo.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b384-cameo.py"), "__name__": "cameo_rec"}
_argv = sys.argv; sys.argv = [sys.argv[0]]; exec(_g, G); sys.argv = _argv

def record(pg, cdp, steps):
    frames = []
    def on_frame(p):
        frames.append((p["metadata"]["timestamp"], p["data"]))
        try: cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
        except Exception: pass
    cdp.on("Page.screencastFrame", on_frame)
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 1320, "maxHeight": 2868, "everyNthFrame": 1})
    pg.wait_for_timeout(400)
    steps()
    cdp.send("Page.stopScreencast")
    pg.wait_for_timeout(200)
    try: cdp.remove_listener("Page.screencastFrame", on_frame)
    except Exception: pass
    return frames

def to_mp4(frames, path, lead=.0):
    tmp = path + ".frames"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    lines = []
    for i, (t, d) in enumerate(frames):
        fn = os.path.join(tmp, "%05d.jpg" % i)
        open(fn, "wb").write(base64.b64decode(d))
        dur = (frames[i + 1][0] - t) if i + 1 < len(frames) else .5
        lines.append("file '%s'\nduration %.4f" % (fn, max(.001, dur)))
    lines.append("file '%s'" % os.path.join(tmp, "%05d.jpg" % (len(frames) - 1)))
    open(os.path.join(tmp, "list.txt"), "w").write("\n".join(lines) + "\n")
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"),
                    "-vf", "fps=30,scale=1320:2868:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-profile:v", "high", "-level", "5.1", "-movflags", "+faststart", path], check=True)
    shutil.rmtree(tmp, ignore_errors=True)

def tap(cdp, x, y): G["tap_at"](cdp, x, y)
def swipe(cdp): G["touch_drag"](cdp, 440 * .86, 956 * .5, 440 * .12, 956 * .5, 300)
def choice_xy(pg, right=True):
    return pg.evaluate("""(right)=>{ const qi=order[pos]; const k=optionOrder(qi).indexOf(QUESTIONS[qi].answer); const ch=[...document.querySelectorAll('#stage .qpanel .choice')];
      const b=(right ? ch[k] : ch[(k+1)%ch.length]).getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }""", right)
def plan_now(pg, kind, streak=0):
    pg.evaluate("""([k, st])=>{ cameoPlan = { at: pos, kind: k, qi: order[pos], pos: pos, timer: 0, fired: false }; runLiveStreak = st; }""", [kind, streak])

# kind, class, character, what happens
SCENES = [
    ("sit", "academy", "grizzly", "the Bear hops onto the ledge with a fish; the swipe to the next question sends it off"),
    ("run", "academy", "zeus", "Zeus crackles in and runs across the bottom, lightning bolt in hand"),
    ("tiptoe", "ifc", "detective", "Fire Code's Inspector swaggers in on tiptoe with a flashlight"),
    ("dangle", "ifc", "hacker", "Fire Code's Dispatcher glitches in and hangs from the ledge; the swipe sends it off"),
    ("peek", "academy", "masked", "the Masked One peeks over the ledge out of a puff of smoke"),
    ("wave", "ifc", "poseidon", "Fire Code's Chief waves his bullhorn"),
    ("sleepy", "academy", "ghost", "the Ghost dozes, floating, its lantern beside; a tap wakes it"),
    ("cheer", "academy", "clown", "the Clown cheers a run of right answers with a balloon; the swipe sends it off"),
    ("oops", "ifc", "marksman", "Fire Code's Hazmat after a wrong pick; the next pick sends it off"),
]
done = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    for kind, cls, char, what in SCENES:
        if ONLY and kind not in ONLY: continue
        ctx, pg, cdp = G["open_page"](br, "phone", cls)
        # worn as if earned (a Fire Code challenge character is locked on this fixture, and a locked one worn is put back to the starter)
        pg.evaluate("(c)=>{ const f=isLockedCharacter; isLockedCharacter=function(id){ return id===c ? false : f.apply(this, arguments); }; store.avatarChar=c; }", char)
        pg.evaluate(G["START"], {"mode": "drill"})
        # a question or two in, as a cameo never comes on the first two
        for _ in range(2):
            pg.evaluate(G["ANSWER"], True); pg.evaluate("()=>advanceWithSlide()"); pg.wait_for_timeout(1100)
        pg.evaluate("(c)=>{ cameoPlan=null; cameoGone(); store.avatarChar=c; }", char)
        # sit and dangle are shown on an answered question (they can be there when you swipe on): answered before the recording starts
        if kind in ("sit", "dangle"): pg.evaluate(G["ANSWER"], True)
        def steps():
            if kind == "sit":
                pg.wait_for_timeout(500)
                print(" ", pg.evaluate("()=>cameoForce('sit', {hold:true})")); pg.wait_for_timeout(4600)
                swipe(cdp); pg.wait_for_timeout(1500)
            elif kind == "run":
                pg.wait_for_timeout(500); print(" ", pg.evaluate("()=>cameoForce('run', {dir:1})")); pg.wait_for_timeout(3300)
            elif kind == "tiptoe":
                pg.wait_for_timeout(500); print(" ", pg.evaluate("()=>cameoForce('tiptoe')")); pg.wait_for_timeout(6200)
            elif kind == "dangle":
                pg.wait_for_timeout(500)
                print(" ", pg.evaluate("()=>cameoForce('dangle', {hold:true})")); pg.wait_for_timeout(4200)
                swipe(cdp); pg.wait_for_timeout(1500)
            elif kind in ("peek", "wave"):
                pg.wait_for_timeout(500); print(" ", pg.evaluate("(k)=>cameoForce(k)", kind)); pg.wait_for_timeout(4300)
            elif kind == "sleepy":
                pg.wait_for_timeout(400); print(" ", pg.evaluate("()=>cameoForce('sleepy', {hold:true})")); pg.wait_for_timeout(5200)
                x, y = choice_xy(pg, True); tap(cdp, x, y); pg.wait_for_timeout(1600)
            elif kind == "cheer":
                plan_now(pg, "cheer", 2); pg.wait_for_timeout(700)
                x, y = choice_xy(pg, True); tap(cdp, x, y); pg.wait_for_timeout(2300)
                print(" ", pg.evaluate("()=>cameoInfo()"))
                swipe(cdp); pg.wait_for_timeout(1500)
            elif kind == "oops":
                plan_now(pg, "oops"); pg.wait_for_timeout(700)
                x, y = choice_xy(pg, False); tap(cdp, x, y); pg.wait_for_timeout(3000)
                print(" ", pg.evaluate("()=>cameoInfo()"))
                x, y = choice_xy(pg, True); tap(cdp, x, y); pg.wait_for_timeout(1400)
        print(kind, cls, char, "-", what)
        frames = record(pg, cdp, steps)
        path = os.path.join(OUT, "cameo-%s%s-v2.mp4" % (kind, "-firecode" if cls == "ifc" else ""))
        to_mp4(frames, path)
        print("  %d frames -> %s (%.1f MB)" % (len(frames), path, os.path.getsize(path) / 1e6))
        done.append(path)
        ctx.close()
    br.close()
errs = [(k, e) for k, e in G["ERRS"] if e]
print("page errors:", errs or "none")
