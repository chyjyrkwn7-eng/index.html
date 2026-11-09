#!/usr/bin/env python3
"""An MP4 of the top switcher (r8): real touches (CDP Input.dispatchTouchEvent) on an iPhone 17 Pro Max (440x956 at 2x),
Profile / Stats / Settings: taps between the three, a drag of the glass, and a swipe across the content. A dot (drawn onto the
frames afterwards) shows the finger.
AT AN EIGHTH OF THE PAGE'S SPEED (--speed, default 0.12), THEN BACK. Drawn live at 2x the sandbox manages ~20 frames a second, so while it records, every
clock the page has runs that much slower: its animations (CDP Animation.setPlaybackRate) and its timers, performance.now, Date.now and
requestAnimationFrame's time (patched in the page) - and the touches are paced as much slower too. Real compositor frames
(Page.startScreencast) are then placed on the page's own time and resampled to a steady 60fps: well over 60 real frames a second of app
time. (The browser's virtual time was tried first: code in the app that waits on performance.now spins forever under a paused
clock, and the recorder hung.)

  python3 tools/record-toptabs.py OUT.mp4 [--stills DIR] [--against FILE] [--ipad]

--stills DIR  also writes the frames at rest, mid-lens and settled for the first tap (DIR/rest.png, DIR/mid*.png, DIR/settled.png)
Needs ffmpeg (/usr/bin/ffmpeg, or imageio_ffmpeg's)."""
import base64, io, json, os, re, shutil, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
a = sys.argv[1:]
def opt(name, default=None):
    if name in a:
        i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
    return default
STILLS = opt("--stills"); AG = opt("--against")
IPAD = "--ipad" in a
if IPAD: a.remove("--ipad")
OUT = os.path.abspath(a[0])
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else __import__("imageio_ffmpeg").get_ffmpeg_exe()
W, H, DPR, INS = (834, 1194, 2, (24, 0, 20, 0)) if IPAD else (440, 956, 2, (62, 0, 34, 0))
UA = ("Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1" if IPAD else
      "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1")
html = open(AG, encoding="utf-8").read() if AG else open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
def body():
    v = {"top": f"{INS[0]}px", "right": f"{INS[1]}px", "bottom": f"{INS[2]}px", "left": f"{INS[3]}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], html)
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted']"
        ".forEach(k=>localStorage.setItem(k,'1')); localStorage.setItem('class26e.frame.ok','go-live-1');"
        "['55124','124256','256578'].forEach(k=>localStorage.setItem('class26e.penal'+k+'.seen','1'));")
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "xph5b57jbp5a"; d["firstName"] = "Casey"; d["novaMet"] = 99
INIT = "(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); %s })()" % (json.dumps(json.dumps(d)), SEEN)
K = float(opt("--speed", "0.12"))   # the page's speed while it records (a stall in the sandbox's frames is real time: slower hides it)
SLOW = """(K)=>{ const pn=performance.now.bind(performance), t0=pn(); performance.now=()=>t0+(pn()-t0)*K;
  const dn=Date.now, d0=dn(); Date.now=()=>d0+(dn()-d0)*K;
  const st=window.setTimeout, si=window.setInterval; window.setTimeout=(f,ms,...a)=>st(f,(+ms||0)/K,...a); window.setInterval=(f,ms,...a)=>si(f,(+ms||0)/K,...a);
  const raf=window.requestAnimationFrame.bind(window); window.requestAnimationFrame=cb=>raf(t=>cb(t0+(t-t0)*K)); }"""
frames = []
with sync_playwright() as pw:
    # the screencast is drawn at the device's own scale only when the browser itself runs at it (check-centering's lesson)
    br = pw.chromium.launch(executable_path=g["CHROME"], args=["--force-device-scale-factor=%d" % DPR])
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=DPR, has_touch=True, is_mobile=True, user_agent=UA)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); b = body()
    srv, url = g["serve"]()
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', b); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.add_init_script(INIT); pg.add_init_script(g["STATUS_BAR"].replace("__H__", str(INS[0])))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; playUnlockSpotlight=(it,n,of,r)=>{ try{ r && r(); }catch(e){} }; }catch(e){} store.novaMet=99;"
                "document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .unlock-card').forEach(n=>n.remove()); showProfile('stats'); }")
    pg.wait_for_timeout(1800)
    marks = {}
    SEL = "#stage .screen-profile > .navsegment.profiletabs > .iconbtn"
    c = pg.evaluate("(s)=>[...document.querySelectorAll(s)].map(b=>{const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]})", SEL)
    cdp = ctx.new_cdp_session(pg)
    shots = []
    def on_frame(p):
        shots.append((p["metadata"]["timestamp"], base64.b64decode(p["data"])))
        try: cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
        except Exception: pass
    cdp.on("Page.screencastFrame", on_frame)
    plan = []          # (app ms, type, x, y)
    def at(ms, typ, x=None, y=None): plan.append((ms, typ, x, y))
    t = 600.0
    def tap(i):
        global t
        at(t, "touchStart", *c[i]); at(t + 70, "touchEnd"); t += 70 + 900
    def drag(i, j, ms=650, steps=30):
        global t
        (x0, y0), (x1, y1) = c[i], c[j]
        at(t, "touchStart", x0, y0); t += 100
        for k in range(1, steps + 1):
            u = k / steps; e = u * u * (3 - 2 * u)
            at(t + ms * k / steps, "touchMove", x0 + (x1 - x0) * e, y0)
        t += ms + 60; at(t, "touchEnd"); t += 900
    def swipe(y, dx, ms=240, steps=12):
        global t
        x0 = W / 2 - dx / 2
        at(t, "touchStart", x0, y)
        for k in range(1, steps + 1): at(t + ms * k / steps, "touchMove", x0 + dx * k / steps, y + k * .4)
        t += ms + 17; at(t, "touchEnd"); t += 1000
    tap(0); tap(2); tap(1); drag(1, 0); swipe(c[0][1] + 360, -240)
    END = t
    marks["tap1"] = 600.0
    cdp.send("Animation.enable")
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "everyNthFrame": 1})
    pg.wait_for_timeout(300)
    pg.evaluate(SLOW, K); cdp.send("Animation.setPlaybackRate", {"playbackRate": K})
    T0 = time.time(); TS0 = None
    fingers = []       # (app ms, (x, y) or None)
    for (ms, typ, x, y) in plan:
        while (time.time() - T0) * 1000 * K < ms: pg.wait_for_timeout(4)
        cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})
        fingers.append(((time.time() - T0) * 1000 * K, None if typ == "touchEnd" else (x, y)))
    while (time.time() - T0) * 1000 * K < END: pg.wait_for_timeout(20)
    cdp.send("Page.stopScreencast"); pg.wait_for_timeout(300)
    cdp.send("Animation.setPlaybackRate", {"playbackRate": 1})
    # screencast timestamps are seconds on the wall clock; T0 on the same clock is the first frame after the slow-down
    tw0 = T0
    print("  %d frames captured; first at %+.3fs from the slow-down" % (len(shots), (shots[0][0] - tw0) if shots else 0))
    frames = [((ts - tw0) * K, data) for ts, data in shots if ts >= tw0]
    print("page errors:", errs)
    srv.shutdown()
if len(frames) < 10: sys.exit("too few frames (%d)" % len(frames))
frames.sort(key=lambda f: f[0])
def finger_at(sec):
    f = None
    for ms, p in fingers:
        if ms / 1000 <= sec: f = p
        else: break
    return f
tmp = tempfile.mkdtemp(prefix="toptabs-", dir=os.path.dirname(OUT))
n = int(END / 1000 * 60)
j = 0; picked = []
for k in range(n):
    tt = k / 60
    while j + 1 < len(frames) and frames[j + 1][0] <= tt: j += 1
    data = frames[j][1]; fp = finger_at(tt); picked.append(j)
    if fp:
        from PIL import ImageDraw
        im = Image.open(io.BytesIO(data)).convert("RGBA"); sc = im.width / W
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
        fx, fy = fp[0] * sc, fp[1] * sc; R = 17 * sc
        dr.ellipse([fx - R, fy - R, fx + R, fy + R], fill=(255, 255, 255, 70), outline=(255, 255, 255, 140), width=max(1, int(1.5 * sc)))
        bio = io.BytesIO(); Image.alpha_composite(im, ov).convert("RGB").save(bio, "JPEG", quality=92); data = bio.getvalue()
    open(os.path.join(tmp, "%05d.jpg" % k), "wb").write(data)
subprocess.run([FF, "-v", "error", "-y", "-framerate", "60", "-i", os.path.join(tmp, "%05d.jpg"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", OUT], check=True)
if STILLS:
    # the first tap: every captured frame from 50ms before the touch to 700ms after it, named by app ms from the touch
    os.makedirs(STILLS, exist_ok=True)
    t1 = marks["tap1"] / 1000
    for tt, data in frames:
        if t1 - .05 <= tt <= t1 + .7: open(os.path.join(STILLS, "t%+05d.jpg" % round((tt - t1) * 1000)), "wb").write(data)
shutil.rmtree(tmp)
print("wrote", OUT, "%d real frames over %.2fs of app time (%.0f a second of app time)" % (len(frames), END / 1000, len(frames) / (END / 1000)))
