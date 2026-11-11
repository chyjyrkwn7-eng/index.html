"""Build 384.32, lag on a computer. Madison: the app lags on a laptop / a big monitor (Chrome, Safari, Edge). tools/profile-desktop.py found where the
main thread goes: not a settled screen (Home 7%, a saved Leaderboard 25%, a question 5% of it; every running animation transform / opacity and in or
near the window) but the FLIP-BOOK RECORDERS, which draw every character and flare a frame at a time into a saved sheet (a data: SVG document loaded
per frame, a style pass per frame, a canvas draw). A fresh profile (every update that changes a drawing, every cleared cache) spent 29% (Home) to 66%
(Leaderboard) of the main thread on them for a minute or more, with a frame in four late - and 80% with the page told it is HIDDEN, because only one
of the two recorders' waits looked at document.hidden.
Shapes and counts, no frame times (the machine is shared). Academy, 44 fake classmates, a fresh browser profile (nothing saved: every recorder has
work), a window at the size named with a mouse. Every recorded frame is one `img.src = "data:image/svg+xml..."` and one canvas drawImage, so they are
counted where they are made; the main thread's time is read off a trace (thread time) and the recorder's own part of it from the trace's events.
(1) THE COUNTER MEASURES SOMETHING: on the cold Leaderboard, visible, at least 20 frames are recorded in 8s.
(2) NOTHING IS RECORDED FOR A PAGE NOBODY CAN SEE: hidden (the page's own flag), no more than 3 frames in 4s (one in flight) and no more than 300ms of
    main-thread work (a hidden tab is not a CPU bill); the Home recorders likewise.
(3) ...AND IT GOES ON WHEN THE PAGE IS BACK: on the Leaderboard, at least 10 frames in the 5s after (Home's seven sheets are done in 12s without a governor).
(4) A RECORDER TAKES A SHARE OF A COMPUTER'S MAIN THREAD, NOT ALL OF IT: on the cold Leaderboard and the cold Home the recorders sleep after every batch
    for at least 60% of the time they and their sleep take (the page's own count, recStats), and their own events (the SVG documents made for the
    frames, the requests, the canvas draws, read off a trace) are no more than 20% of the main thread.
(5) THE SETTLED SCREEN'S SHAPE (guards, hold on every build): running animations on Home, the Leaderboard and Profile are in or near the window (a
    handful far, none detached), and the backdrop filters cover less than a window. (What they animate is INFO: a loop in the painted mode steps left / top.)
(6) A PHONE IS UNCHANGED: REC_DUTY is 1 and the device is not a computer there.
(7) no page errors.
Run:  python3 tools/check-b384-desktoplag.py [--against FILE|REV] [--full] [--only 1,2,...]
      (--against the 384.29 index.html must FAIL (2) and (4))"""
import os, re, subprocess, sys, time, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from b384_desktoplag_lib import SHAPE_JS, thread_cpu, recorder_cost
_args = sys.argv[:]
def opt(n, d=None): return _args[_args.index(n) + 1] if n in _args else d
AG = opt("--against")
FULL = "--full" in _args
ONLY = set(opt("--only", "").split(",")) - {""} or None
def want(n): return ONLY is None or str(n) in ONLY
_src = open(os.path.join(HERE, "check-b384-desktop.py")).read().split("\nwith sync_playwright() as pw:")[0]
_src = _src.replace('if "--against" in sys.argv:', 'if False:')
sys.argv = [sys.argv[0]]
G = {"__file__": os.path.join(HERE, "check-b384-desktop.py"), "__name__": "check_desktoplag"}
exec(_src, G)
if AG:
    if os.path.exists(AG): G["SRC"] = open(AG, encoding="utf-8").read()
    else: G["SRC"] = subprocess.check_output(["git", "-C", ROOT, "show", AG + ":index.html"]).decode("utf-8")
    G["BUILD"] = (re.search(r'const APP_BUILD = "([^"]+)"', G["SRC"]) or [None, ""])[1]
from playwright.sync_api import sync_playwright
chk, info = G["chk"], G["info"]
SLEEP_MIN = 0.6     # REC_DUTY .25 sleeps 75% of a batch's time and its sleep; 60% leaves room for the 700ms cap
REC_SHARE_MAX = 0.20   # the recorders' own events as a share of the main thread: 28% on the cold Leaderboard before, 11% after (this machine)
CATS = "devtools.timeline,disabled-by-default-devtools.timeline,disabled-by-default-devtools.timeline.stack,v8.execute,cc,viz,blink"   # as profile-desktop.py: the recorder's own events need blink
# the page's hidden state is the test's to set; every recorded frame is counted where it is made
INSTR = """(()=>{ let hid = false;
  try{ Object.defineProperty(Document.prototype, 'hidden', { get(){ return hid; }, configurable: true });
       Object.defineProperty(Document.prototype, 'visibilityState', { get(){ return hid ? 'hidden' : 'visible'; }, configurable: true }); }catch(e){}
  window.__setHidden = v => { hid = v; document.dispatchEvent(new Event('visibilitychange')); };
  const M = window.__L = { snaps: 0, draws: 0 };
  try{ const d = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
    Object.defineProperty(HTMLImageElement.prototype, 'src', { get(){ return d.get.call(this); }, configurable: true,
      set(v){ if(typeof v === 'string' && v.indexOf('data:image/svg+xml') === 0) M.snaps++; return d.set.call(this, v); } }); }catch(e){}
  try{ const dr = CanvasRenderingContext2D.prototype.drawImage; CanvasRenderingContext2D.prototype.drawImage = function(){ M.draws++; return dr.apply(this, arguments); }; }catch(e){}
})()"""

def trace(pg, cdp, ms):
    evs, done = [], []
    h1 = lambda p: evs.extend(p["value"]); h2 = lambda p: done.append(1)
    cdp.on("Tracing.dataCollected", h1); cdp.on("Tracing.tracingComplete", h2)
    cdp.send("Tracing.start", {"categories": CATS, "transferMode": "ReportEvents"})
    pg.wait_for_timeout(ms)
    cdp.send("Tracing.end")
    for _ in range(600):
        if done: break
        pg.wait_for_timeout(100)
    try: cdp.remove_listener("Tracing.dataCollected", h1); cdp.remove_listener("Tracing.tracingComplete", h2)
    except Exception: pass
    return evs
def snaps(pg): return pg.evaluate("()=>window.__L.snaps")

def cold_screen(br, dev, tab, notes):
    """a fresh context on the cold page: tab opened, the recorders going. Returns (page, cdp, touch, errs)."""
    ctx, pg, cdp, errs, touch = G["open_page"](br, dev, extra=(INSTR,))
    if tab != "home": G["tap"](pg, cdp, touch, "#bottomtab-" + tab)
    pg.mouse.move(5, 5) if not touch else None
    pg.wait_for_timeout(4500)       # the recorders do not start for a screen that has just gone in (REC_VISIT_MS)
    return ctx, pg, cdp, errs, touch

def run_device(br, dev):
    tag = dev
    for tab in ("rewards", "home"):
        if not (want(1) or want(2) or want(3) or want(4)): break
        ctx, pg, cdp, errs, touch = cold_screen(br, dev, tab, None)
        name = "%s %s" % (tag, "the Leaderboard" if tab == "rewards" else "Home")
        # ---- visible: what is recorded, what the recorders' governor did, and the main thread's share
        def rs(): return pg.evaluate("()=>typeof recStats === 'undefined' ? null : { batches: recStats.batches, batchMs: recStats.batchMs, sleptMs: recStats.sleptMs }")
        s0 = snaps(pg); g0 = rs()
        evs = trace(pg, cdp, 8000)
        s1 = snaps(pg); g1 = rs(); cpu, ntask = thread_cpu(evs); rec, nload = recorder_cost(evs)
        rate = (s1 - s0) / 8.0
        slept = None
        if g1 and g0 is not None:
            db, dm, dsl = g1["batches"] - g0["batches"], g1["batchMs"] - g0["batchMs"], g1["sleptMs"] - g0["sleptMs"]
            slept = dsl / (dm + dsl) if (dm + dsl) > 0 else 0
        info("%s visible 8s: %d frames recorded (%.1f/s); the recorders' own events %.0fms; main thread %.0fms in %d tasks; slept share %s" % (name, s1 - s0, rate, rec, cpu, ntask, "none (no governor)" if slept is None else "%.2f" % slept))
        if tab == "rewards" and want(1): chk("(1) %s: the counter measures something (frames recorded in 8s >= 20)" % name, s1 - s0 >= 20, s1 - s0)
        if want(4):
            chk("(4) %s: the recorders sleep after each batch (share of their time asleep %s, at least %.2f)" % (name, "none" if slept is None else "%.2f" % slept, SLEEP_MIN), slept is not None and slept >= SLEEP_MIN, slept)
            chk("(4) %s: the recorders' own events take at most %d%% of the main thread (%.0f%%)" % (name, REC_SHARE_MAX * 100, rec / 80.0), rec / 8000.0 <= REC_SHARE_MAX, "%.0fms of 8000" % rec)
        # ---- hidden
        pg.evaluate("()=>__setHidden(true)"); pg.wait_for_timeout(1200)
        h0 = snaps(pg); evs = trace(pg, cdp, 4000); h1 = snaps(pg); hcpu, _ = thread_cpu(evs)
        info("%s hidden 4s: %d frames recorded, main thread %.0fms" % (name, h1 - h0, hcpu))
        if want(2):
            chk("(2) %s: hidden, no more than 3 frames recorded in 4s (%d)" % (name, h1 - h0), h1 - h0 <= 3, h1 - h0)
            # (only the page's flag is set here, so Chromium still draws Home's animations: 14-430ms of that in 4s, run to run; the Leaderboard's
            # recorders are the 3,700ms this is about)
            cap = 300 if tab == "rewards" else 700
            chk("(2) %s: hidden, the main thread does under %dms of work in 4s (%.0fms)" % (name, cap, hcpu), hcpu <= cap, "%.0fms" % hcpu)
        # ---- back
        pg.evaluate("()=>__setHidden(false)"); r0 = snaps(pg); pg.wait_for_timeout(5000); r1 = snaps(pg)
        if want(3) and tab == "rewards": chk("(3) %s: back in view, recording goes on (%d frames in 5s)" % (name, r1 - r0), r1 - r0 >= 10, r1 - r0)
        if want(7): chk("(7) %s: no page errors" % name, not errs, errs[:2])
        ctx.close()

def run_shape(br, dev):
    for tab in ("home", "rewards", "profile"):
        ctx, pg, cdp, errs, touch = G["open_page"](br, dev, extra=(INSTR,))
        if tab != "home": G["tap"](pg, cdp, touch, "#bottomtab-" + tab)
        pg.wait_for_timeout(4000)
        r = pg.evaluate(SHAPE_JS)
        name = "%s %s" % (dev, tab)
        info("%s: running %d of %d (in view %d, near %d, far %d, detached %d); backdrops %d over %.2f of the window; animating %s" % (name, r["running"], r["all"], r["inView"], r["near"], r["far"], r["detached"], r["fx"]["backdrop"], r["fx"]["backdropArea"], dict(r["props"])))
        chk("(5) %s: no more than 4 running animations are far from the window, none detached (%d far, %d detached)" % (name, r["far"], r["detached"]), r["far"] <= 4 and r["detached"] == 0, r["far_names"])
        chk("(5) %s: backdrop filters cover under a window's worth (%.2f)" % (name, r["fx"]["backdropArea"]), r["fx"]["backdropArea"] <= 1.0, r["fx"])
        if want(7): chk("(7) %s: no page errors" % name, not errs, errs[:2])
        ctx.close()

def run_phone(br):
    if not want(6): return
    ctx, pg, cdp, errs, touch = G["open_page"](br, "phone", extra=(INSTR,))
    duty = pg.evaluate("()=>[typeof REC_DUTY === 'number' ? REC_DUTY : null, typeof REC_DESKTOP === 'boolean' ? REC_DESKTOP : null]")
    chk("(6) a phone is not throttled: REC_DUTY is 1 and the device is not a computer (%s)" % duty, duty[0] is None or duty == [1, False], duty)
    ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    devs = ["1440x900x1", "1920x1080x1"] + (["2560x1440x1"] if FULL else [])
    try:
        for dev in devs:
            if want(1) or want(2) or want(3) or want(4) or want(7): run_device(br, dev)
        if want(5):
            run_shape(br, devs[0])
        run_phone(br)
    finally:
        br.close()
print("ALL PASS" if G["ok"] else "FAILURES")
sys.exit(0 if G["ok"] else 1)
