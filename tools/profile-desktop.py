#!/usr/bin/env python3
"""profile-desktop.py - WHERE A COMPUTER'S MAIN THREAD GOES, per interaction (a recorder, not a gate).
Build 384.20: Madison, "the app feels laggy on a computer". Opens the app as check-b384-desktop does (44 fake classmates, academy; a phone is
440x956 at 3x with a finger, a window is a desktop browser at the size named, with a mouse), traces one interaction with CDP and prints for it:
the page's frame clock (p50 / p95 / max / frames over 25ms), the main thread's CPU in 1x-equivalent ms (thread time, so it does not move with a
busy sandbox the way a frame time does) by kind of work, the longest tasks and what the longest is made of, which script function forced each
style pass and layout (with the line in index.html, read straight off the trace), and with --self the SELF time by trace event and with --calls
the script functions that took the most.

  python3 tools/profile-desktop.py DEVICE SCENARIOS [--thr N] [--against FILE] [--self] [--calls] [--nf 8] [--ncalls 12] [--ms N] [--idlems N]
  DEVICE     phone | ipad | WxHxDPR (1366x768x1, 1512x982x2, 1920x1080x1, 1920x1080x2 ...)
  SCENARIOS  comma list of: tabs (six hops of the bar), lbscroll (the Leaderboard scrolled down), czscroll (Customize > Banner, then
             Character, scrolled), startsheet (the Start sheet opened), hover (a mouse moved over the board), lbidle (the Leaderboard
             sitting open for --ms), idle:TAB (a screen sitting open for --idlems), warm (waits, up to --ms, for the Leaderboard's
             flip-book sheets to be recorded and saved - minutes on a cold profile; later scenarios then measure a settled page)
  --thr N    CPU throttle (the figures are divided back to 1x)

What it found on 384.19 (1366x768, this sandbox; docs/notes-archive.md, "384.20"): a tab change forces no function more than 4 style passes (the
60+ of place / hswFits / backToTopRoom were fixed in 384.19), and what a computer pays for is the FIRST visit of each screen with art - the
flip-book sheets of the characters and flares are recorded then (nothing is saved yet): 59-77% of the main thread for minutes, frames at half rate.
"""
import os, sys, re, time, json, statistics, collections
HERE = os.path.dirname(os.path.abspath(__file__))
_args = sys.argv[:]
def opt(n, d=None): return _args[_args.index(n) + 1] if n in _args else d
AG = opt("--against")
THR = float(opt("--thr", 1))
_src = open(os.path.join(HERE, "check-b384-desktop.py")).read().split("\nwith sync_playwright() as pw:")[0]
_src = _src.replace('if "--against" in sys.argv:', 'if False:')
sys.argv = [sys.argv[0]]
G = {"__file__": os.path.join(HERE, "check-b384-desktop.py"), "__name__": "profile_desktop"}
exec(_src, G)
if AG:
    G["SRC"] = open(AG, encoding="utf-8").read()
    G["BUILD"] = (re.search(r'const APP_BUILD = "([^"]+)"', G["SRC"]) or [None, ""])[1]
from playwright.sync_api import sync_playwright
DEV, SCEN = _args[1], _args[2]
PROFILE = opt("--profile")   # 384.30: a persistent browser profile, so the saved flip-book sheets (Cache Storage) are there next run: a WARM page
class _Persist:
    """a stand-in for a Browser whose new_context() is a persistent context on one directory, on one port (Cache Storage is per origin)"""
    def __init__(self, pw, exe, d): self.pw, self.exe, self.d, self.ctx = pw, exe, d, None
    def new_context(self, **kw):
        self.ctx = self.pw.chromium.launch_persistent_context(self.d, executable_path=self.exe, **kw)
        for p in list(self.ctx.pages): p.close()
        return self.ctx
    def close(self):
        try: self.ctx.close()
        except Exception: pass
if PROFILE:
    import functools, http.server, threading
    _port = int(opt("--port", 8765))
    class _Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    _srv = http.server.ThreadingHTTPServer(("127.0.0.1", _port), functools.partial(_Q, directory=G["ROOT"]))
    threading.Thread(target=_srv.serve_forever, daemon=True).start()
    G["URL"] = "http://127.0.0.1:%d/index.html" % _port
CATS = "devtools.timeline,disabled-by-default-devtools.timeline,disabled-by-default-devtools.timeline.stack,v8.execute,cc,viz,blink"

def trace_run(pg, cdp, fn, tail_ms=300):
    evs, done = [], []
    h1 = lambda p: evs.extend(p["value"]); h2 = lambda p: done.append(1)
    cdp.on("Tracing.dataCollected", h1); cdp.on("Tracing.tracingComplete", h2)
    cdp.send("Tracing.start", {"categories": CATS, "transferMode": "ReportEvents"})
    fn(); pg.wait_for_timeout(tail_ms)
    cdp.send("Tracing.end")
    for _ in range(600):
        if done: break
        pg.wait_for_timeout(100)
    try: cdp.remove_listener("Tracing.dataCollected", h1); cdp.remove_listener("Tracing.tracingComplete", h2)
    except Exception: pass
    return evs

LIVE = """()=>{ const A = document.getAnimations(); const run = A.filter(a => a.playState === 'running');
  return { anims: A.length, running: run.length, els: document.getElementsByTagName('*').length }; }"""
def live_counts(pg, cdp):
    """running animations, elements, and the compositor's layer count (read off one layerTreeDidChange)"""
    r = pg.evaluate(LIVE); box = []
    h = lambda p: box.append(len(p.get("layers") or []))
    try:
        cdp.on("LayerTree.layerTreeDidChange", h); cdp.send("LayerTree.enable"); pg.wait_for_timeout(700)
        cdp.send("LayerTree.disable"); cdp.remove_listener("LayerTree.layerTreeDidChange", h)
    except Exception: pass
    r["layers"] = max(box) if box else -1
    return r
def report(evs, label, thr=1.0, top=6):
    names = {}
    for e in evs:
        if e.get("name") == "thread_name": names[(e["pid"], e["tid"])] = e["args"]["name"]
    th = lambda e: names.get((e.get("pid"), e.get("tid")))
    main = [e for e in evs if th(e) == "CrRendererMain" and e.get("ph") == "X"]
    cpu = lambda e: e.get("tdur", e["dur"]) / 1000.0 / thr
    tasks = [e for e in main if e["name"] == "RunTask"]
    total = sum(cpu(e) for e in tasks)
    byname = collections.Counter(); cnt = collections.Counter()
    for e in main:
        if e["name"] in ("UpdateLayoutTree", "Layout", "PrePaint", "Paint", "Layerize", "UpdateLayer", "IntersectionObserverController::computeIntersections", "ComputeIntersections", "FunctionCall", "EvaluateScript", "HitTest", "EventDispatch", "TimerFire", "FireAnimationFrame", "RunMicrotasks", "Commit", "CompositeLayers", "Decode Image", "ImageDecodeTask", "ParseHTML", "UpdateLayoutTree"):
            byname[e["name"]] += cpu(e); cnt[e["name"]] += 1
    forced = collections.Counter(); fms = collections.Counter()
    for e in main:
        if e["name"] in ("UpdateLayoutTree", "Layout"):
            a = e.get("args", {})
            st = (a.get("beginData", {}) or {}).get("stackTrace") or a.get("stackTrace") or []
            fr = [f for f in st if f.get("functionName")]
            fn = ("%s@%s < %s@%s" % (fr[0]["functionName"], fr[0].get("lineNumber"), fr[1]["functionName"], fr[1].get("lineNumber"))) if len(fr) > 1 else (("%s@%s" % (fr[0]["functionName"], fr[0].get("lineNumber"))) if fr else None)
            real = (e["name"] == "UpdateLayoutTree" and (a.get("elementCount") or 0) > 0) or (e["name"] == "Layout" and e.get("tdur", 0) >= 50)
            if fn and real: forced[(e["name"], fn)] += 1; fms[(e["name"], fn)] += cpu(e)
    if "--self" in _args:
        evsm = sorted([e for e in main if e.get("dur") is not None], key=lambda e: (e["ts"], -e["dur"]))
        selft = collections.Counter(); stack = []
        for e in evsm:
            while stack and stack[-1][1] <= e["ts"]: stack.pop()
            if stack: stack[-1][2] += e["dur"]
            stack.append([e, e["ts"] + e["dur"], 0])
            e["_k"] = stack[-1]
        for e in evsm:
            k = e["_k"]; selft[e["name"]] += max(0, e["dur"] - k[2]) / 1000.0 / thr
        print("   SELF time by event (ms): " + ", ".join("%s %.0f" % (k, v) for k, v in selft.most_common(14)))
    if "--calls" in _args:
        calls = collections.Counter(); ccount = collections.Counter()
        for e in main:
            if e["name"] in ("FunctionCall", "EvaluateScript", "v8.callFunction", "TimerFire", "FireAnimationFrame", "FireIdleCallback", "EventDispatch"):
                d = (e.get("args", {}) or {}).get("data", {}) or {}
                key = e["name"] + ":" + str(d.get("functionName") or d.get("type") or d.get("id") or "") + "@" + str(d.get("lineNumber", ""))
                calls[key] += cpu(e); ccount[key] += 1
        print("   TOP CALLS (cumulative ms, n): " + "; ".join("%s %.0f x%d" % (k, v, ccount[k]) for k, v in calls.most_common(int(opt("--ncalls", 10)))))
    long = sorted(tasks, key=lambda e: -cpu(e))[:top]
    print("== %s: main-thread CPU %.0fms over %d tasks (1x-equiv); " % (label, total, len(tasks)) +
          "style/layout/paint: " + ", ".join("%s %d x %.0fms" % (k, cnt[k], v) for k, v in byname.most_common(6)))
    print("   longest tasks (ms): " + ", ".join("%.0f" % cpu(e) for e in long))
    if forced: print("   forced passes (fn: n, ms): " + "; ".join("%s %s: %d, %.0fms" % (k[0][:6], k[1], v, fms[k]) for k, v in forced.most_common(int(opt("--nf", 6)))))
    # what the longest task is made of: top-level children
    if long:
        t = long[0]; s0, s1 = t["ts"], t["ts"] + t["dur"]
        kids = [e for e in main if e is not t and s0 <= e["ts"] and e["ts"] + e["dur"] <= s1 and e["name"] not in ("RunTask",)]
        agg = collections.Counter()
        for e in kids: agg[e["name"]] += cpu(e)
        print("   longest task made of: " + ", ".join("%s %.0f" % (k, v) for k, v in agg.most_common(6)))
    return total

CLOCK = """()=>{ const S=window.__fc={frames:[],on:true}; const f=t=>{ if(!S.on) return; S.frames.push(t); requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
def fstats(fr):
    d = [fr[i + 1] - fr[i] for i in range(len(fr) - 1)]
    if len(d) < 3: return "no frames"
    s = sorted(d); n = len(s)
    return "frames %d p50 %.0f p95 %.0f max %.0f late(>25) %d" % (n, s[n // 2], s[min(n - 1, int(n * .95))], s[-1], sum(1 for x in d if x > 25))

def scroll_wheel(pg, W, H, dist, step, touch, cdp):
    if touch:
        # a finger drag, then let go
        x, y = W // 2, int(H * 0.8); n = max(2, dist // step)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(0.03)
        for i in range(1, n + 1):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": max(5, y - i * step)}]}); time.sleep(0.016)
            if y - i * step < 5: break
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    else:
        pg.mouse.move(W // 2, H // 2)
        for i in range(max(2, dist // step)):
            pg.mouse.wheel(0, step); pg.wait_for_timeout(16)

def main():
    with sync_playwright() as pw:
        br = _Persist(pw, G["CHROME"], PROFILE) if PROFILE else pw.chromium.launch(executable_path=G["CHROME"])
        ctx, pg, cdp, errs, touch = G["open_page"](br, DEV)
        vp = pg.evaluate("()=>[innerWidth,innerHeight]"); W, H = vp
        if THR > 1: cdp.send("Emulation.setCPUThrottlingRate", {"rate": THR})
        pg.wait_for_timeout(int(opt("--settle", 1500)))
        tail = 500
        scen = SCEN.split(",") if SCEN != "all" else ["tabs", "lbscroll", "czscroll", "startsheet", "hover"]
        for sc in scen:
            if sc == "tabs":
                pairs = [("home", "profile"), ("profile", "rewards"), ("rewards", "calendar"), ("calendar", "home"), ("home", "rewards"), ("rewards", "home")]
                for a, b in pairs:
                    G["tap"](pg, cdp, touch, "#bottomtab-" + a); pg.wait_for_timeout(1700)
                    pg.evaluate(CLOCK)
                    evs = trace_run(pg, cdp, lambda: G["tap"](pg, cdp, touch, "#bottomtab-" + b), 900)
                    fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                    report(evs, "%s tab %s>%s [%s]" % (DEV, a, b, fstats(fr)), THR)
            elif sc == "lbscroll":
                G["tap"](pg, cdp, touch, "#bottomtab-rewards"); pg.wait_for_timeout(2500)
                pg.evaluate(CLOCK)
                maxy = pg.evaluate("()=>document.scrollingElement.scrollHeight-innerHeight")
                evs = trace_run(pg, cdp, lambda: scroll_wheel(pg, W, H, int(maxy * .9), 60, touch, cdp), 600)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                report(evs, "%s Leaderboard scroll down (%dpx) [%s]" % (DEV, maxy, fstats(fr)), THR)
                pg.evaluate("()=>scrollTo({top:0,behavior:'instant'})"); pg.wait_for_timeout(800)
            elif sc == "czscroll":
                pg.evaluate("()=>{ showCustomize('banner'); }"); pg.wait_for_timeout(3500)
                pg.evaluate(CLOCK)
                maxy = pg.evaluate("()=>document.scrollingElement.scrollHeight-innerHeight")
                evs = trace_run(pg, cdp, lambda: scroll_wheel(pg, W, H, int(maxy * .9), 60, touch, cdp), 600)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                report(evs, "%s Customize>Banner scroll down (%dpx) [%s]" % (DEV, maxy, fstats(fr)), THR)
                pg.evaluate("()=>scrollTo({top:0,behavior:'instant'})"); pg.wait_for_timeout(800)
                pg.evaluate("()=>{ showCustomize('character'); }"); pg.wait_for_timeout(3500)
                pg.evaluate(CLOCK)
                maxy = pg.evaluate("()=>document.scrollingElement.scrollHeight-innerHeight")
                evs = trace_run(pg, cdp, lambda: scroll_wheel(pg, W, H, int(maxy * .9), 60, touch, cdp), 600)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                report(evs, "%s Customize>Character scroll down (%dpx) [%s]" % (DEV, maxy, fstats(fr)), THR)
            elif sc == "startsheet":
                G["tap"](pg, cdp, touch, "#bottomtab-home"); pg.wait_for_timeout(2200)
                pg.evaluate(CLOCK)
                sel = pg.evaluate("()=>{ const b=document.querySelector('.panel.home .playbtn, #bottomtab-start, .bottomtabs .start-tab, [data-start]'); return b ? (b.id ? '#'+b.id : '.playbtn') : null; }")
                evs = trace_run(pg, cdp, lambda: G["tap"](pg, cdp, touch, sel or ".playbtn"), 1500)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                report(evs, "%s Start sheet open (%s) [%s]" % (DEV, sel, fstats(fr)), THR)
            elif sc == "lbidle":
                G["tap"](pg, cdp, touch, "#bottomtab-rewards"); pg.wait_for_timeout(1500)
                pg.evaluate(CLOCK)
                evs = trace_run(pg, cdp, lambda: pg.wait_for_timeout(int(opt("--ms", 15000))), 300)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                report(evs, "%s Leaderboard sitting open %sms [%s]" % (DEV, opt("--ms", 15000), fstats(fr)), THR, top=12)
            elif sc == "warm":
                G["tap"](pg, cdp, touch, "#bottomtab-rewards"); pg.wait_for_timeout(1500)
                t0 = time.time()
                while time.time() - t0 < float(opt("--ms", 120000)) / 1000:
                    st = pg.evaluate("()=>({pending: charRecPending.size, ready: charAnimReady.size, sheets: charAnimSheets.size, waiters: charRecWaiters.size, orb: typeof orbitRecPending!=='undefined'?orbitRecPending.size:-1})")
                    print(int(time.time() - t0), st, flush=True)
                    if st["pending"] == 0 and st["ready"] > 0 and st["sheets"] == st["ready"]: break
                    pg.wait_for_timeout(5000)
            elif sc.startswith("idle"):
                tabn = sc.split(":")[1] if ":" in sc else "rewards"
                G["tap"](pg, cdp, touch, "#bottomtab-" + tabn); pg.wait_for_timeout(2500)
                pg.mouse.move(5, 5)
                pg.evaluate(CLOCK)
                evs = trace_run(pg, cdp, lambda: pg.wait_for_timeout(int(opt("--idlems", 4000))), 300)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                lc = live_counts(pg, cdp)
                report(evs, "%s IDLE on %s %sms [%s] [running %d of %d animations, %d layers, %d elements]" % (DEV, tabn, opt("--idlems", 4000), fstats(fr), lc["running"], lc["anims"], lc["layers"], lc["els"]), THR, top=6)
            elif sc == "question":
                # a Drill question sitting open (Identity Crimes, the unit the recorders use): the screen a person spends most of their time on
                pg.evaluate("""()=>{ cfg.mode='drill'; cfg.units=['Identity Crimes']; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; cfg.recall=false;
                  beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes')), null); }""")
                for _ in range(120):
                    if pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
                    pg.wait_for_timeout(100)
                pg.wait_for_timeout(1500); pg.mouse.move(5, 5)
                pg.evaluate(CLOCK)
                evs = trace_run(pg, cdp, lambda: pg.wait_for_timeout(int(opt("--idlems", 4000))), 300)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                lc = live_counts(pg, cdp)
                report(evs, "%s a question sitting open %sms [%s] [running %d of %d animations, %d layers, %d elements]" % (DEV, opt("--idlems", 4000), fstats(fr), lc["running"], lc["anims"], lc["layers"], lc["els"]), THR, top=6)
            elif sc == "hidden":
                # the page told it is hidden (the browser's own flag is the test's to set), then the main thread's work for --idlems
                pg.evaluate("""()=>{ let hid=false; Object.defineProperty(Document.prototype,'hidden',{get(){return hid;},configurable:true});
                  Object.defineProperty(Document.prototype,'visibilityState',{get(){return hid?'hidden':'visible';},configurable:true});
                  window.__setHidden=v=>{ hid=v; document.dispatchEvent(new Event('visibilitychange')); }; }""")
                G["tap"](pg, cdp, touch, "#bottomtab-" + (opt("--tab", "rewards"))); pg.wait_for_timeout(1500)
                pg.evaluate("()=>__setHidden(true)"); pg.wait_for_timeout(500)
                evs = trace_run(pg, cdp, lambda: pg.wait_for_timeout(int(opt("--idlems", 4000))), 300)
                report(evs, "%s HIDDEN on %s %sms" % (DEV, opt("--tab", "rewards"), opt("--idlems", 4000)), THR, top=6)
                pg.evaluate("()=>__setHidden(false)")
            elif sc == "hover":
                G["tap"](pg, cdp, touch, "#bottomtab-rewards"); pg.wait_for_timeout(2500)
                pg.evaluate(CLOCK)
                def hov():
                    for i in range(14):
                        pg.mouse.move(W * (0.2 + 0.05 * (i % 12)), H * (0.25 + 0.04 * i), steps=4); pg.wait_for_timeout(40)
                evs = trace_run(pg, cdp, hov, 400)
                fr = pg.evaluate("()=>{__fc.on=false; return __fc.frames;}")
                report(evs, "%s hovering over the board [%s]" % (DEV, fstats(fr)), THR)
        print("errors:", errs[:3])
        br.close()
main()
