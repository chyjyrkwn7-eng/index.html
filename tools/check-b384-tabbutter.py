"""Build 384 r15: THE BOTTOM TAB, LIKE BUTTER, THE SAME ON EVERY DEVICE.
Madison, on his 384.11 recording (iPhone 17 Pro Max, Home / Profile / Leaderboard / Settings hopped for 20s): "Bottom tab is starting to feel
really really good. I need this to be a smidge smoother. Like butter ... Ensure this smoothness is the same for ALL devices and all screen
sizes, because I've seen how laggy it is on computers."
What his recording says (read frame by frame, ffmpeg): the glass glides at 60 over Profile, the Leaderboard and Settings; every stretch of
dropped frames has Home in it (Home idles at ~40fps, 31% of its frames late; a glide into or out of it drops 4-7 of its ~20). The screen
change itself is one clean frame (build 302's decision: no entrance movement; not touched).
Read off the page in Chromium, academy, 44 classmates from a fake cloud. Chromium here is NOT an iPhone's WebKit or a Windows GPU: frame
times are printed as INFO (p50 / p95 / max of the page's own frame clock over each tab change, and the software compositor's draw time per
frame, which stands in for a GPU's), and what is ASSERTED is thread-CPU of the page's main thread (stable on a busy sandbox) and shapes.
Devices: a phone (440x956 at 3x, a finger, installed), an iPad (834x1194 at 2x, a finger), and a mouse on 1366x768, 1512x982 at 2x, 1920x1080,
2560x1440, 3840x2160 (4K at 1x) and 1920x1080 at 2x (4K at 200%). Taps: all 12 ordered pairs of the academy's four tabs. CPU throttle 1x,
and 4x for the phone and the 1366x768 laptop (a weak machine); budgets are in 1x-equivalent milliseconds (the measured time divided by the throttle).
(1) A TAP HOLDS THE HEAVY ART STILL UNDER THE GLASS (phone, iPad; all 12 pairs): from a frame after the press until the glass has landed, nothing
    in Home's hero, Profile's card and goals or the board's rows (SLIDE_HOLD_SEL, read from the source) is running - on the screen it leaves, and
    (a short grace after the build) on the screen it brings in - and once the glass has landed Home's hero is running again. His recording: the
    glass dropped frames only where Home's ~30 loops ran under it.
(2) NO STYLE PASS PER LOOP: no script function forces more than 8 style recalcs that restyled something (UpdateLayoutTree attributed to it by its stack) or 8 layouts that took 50us or more in one
    tab change, on every device and throttle. (Home's loop clock set each of its ~75 loops after reading the last one's timing: 75 style passes a
    tab change; the board's rows the same on every row coming into view.)
(3) BUDGETS, 1x-equivalent ms of main-thread CPU, per class (a finger: phone, iPad; a mouse: every computer):
    a. no task from the press to a second after it is over BUDGET_WORST (the build and the first frame are the biggest pieces);
    b. no input handler (pointerdown, pointerup, click, touch and mouse twins) over BUDGET_INPUT - the press is the lens's first frame;
    c. the tab change's whole main-thread CPU (median of the 12 pairs) under BUDGET_TOTAL.
(4) NOTHING SCALES WITH THE SCREEN'S AREA: the median whole-hop main-thread CPU on 3840x2160 (and on 1920x1080 at 2x) is at most 1.6x the 1366x768's.
(5) the page's own frame clock saw a frame, every hop; no page errors.
(6) THE IDLE STAND-IN WAITS FOR THE FINGER AND THE GLASS (phone, iPad: Safari has no requestIdleCallback, the page's own runs the warm-ups 700ms
    after the last touchSTART - a finger that stays down on the bar (a slide, a long press) is still there then): a job asked for while a finger is
    down on a tab does not run until it lifts, and then only with the lens down, the bar not held and no settle window open.
Run:  python3 tools/check-b384-tabbutter.py [--quick] [--only phone,1366x768x1] [--checks 1,6] [--against REV|path/to/index.html]
      (--against origin/main's file must FAIL (1) and (2) on every device they run on; (1) on the finger's, (2) everywhere.)"""
import os, sys, re, time, json, statistics, collections
HERE = os.path.dirname(os.path.abspath(__file__))
_args = sys.argv[:]
def _opt(name, default=None):
    return _args[_args.index(name) + 1] if name in _args else default
QUICK = "--quick" in _args
ONLY = set(_opt("--only", "").split(",")) - {""}
CHECKS = set(_opt("--checks", "").split(",")) - {""}          # e.g. --checks 1,6 (the finger's checks alone, no traced hops)
TRACED = not CHECKS or bool(CHECKS & {"2", "3", "4"})
AG = _opt("--against")
# the desktop harness' prelude (open_page, tap, SRC, CHROME); --against is a git rev there, a path here
_src = open(os.path.join(HERE, "check-b384-desktop.py")).read().split("\nwith sync_playwright() as pw:")[0]
_src = _src.replace('if "--against" in sys.argv:', 'if False:')
sys.argv = [sys.argv[0]]
G = {"__file__": os.path.join(HERE, "check-b384-desktop.py"), "__name__": "b384tabbutter"}
exec(_src, G)
if AG:
    if os.path.isfile(AG): G["SRC"] = open(AG, encoding="utf-8").read()
    else:
        import subprocess
        G["SRC"] = subprocess.check_output(["git", "-C", os.path.dirname(HERE), "show", AG + ":index.html"]).decode("utf-8")
    G["BUILD"] = (re.search(r'const APP_BUILD = "([^"]+)"', G["SRC"]) or [None, ""])[1]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def info(s): print("INFO " + s, flush=True)

TABS = ["home", "profile", "rewards", "calendar"]
PAIRS = [(a, b) for a in TABS for b in TABS if a != b]
QUICK_PAIRS = [("home", "profile"), ("profile", "home"), ("home", "rewards"), ("rewards", "calendar")]
# (device, throttle list); a finger on the first two, a mouse on the rest
DEVICES = [("phone", (1, 4)), ("ipad", (1,)), ("1366x768x1", (1, 4)), ("1512x982x2", (1,)), ("1920x1080x1", (1,)),
           ("2560x1440x1", (1,)), ("3840x2160x1", (1,)), ("1920x1080x2", (1,))]
if QUICK: DEVICES = [("phone", (1,)), ("1366x768x1", (1,)), ("1920x1080x2", (1,))]
if ONLY: DEVICES = [d for d in DEVICES if d[0] in ONLY]
FINGER = ("phone", "ipad")
# 1x-equivalent ms of main-thread CPU, per class
BUDGET = {"finger": {"worst": 140, "input": 20, "total": 600}, "mouse": {"worst": 140, "input": 14, "total": 600}}
AREA_RATIO = 1.6
# the heavy art a tap holds, read from the source (the same selector a slide holds)
HOLD_SEL = (re.search(r'const SLIDE_HOLD_SEL = "([^"]+)"', G["SRC"]) or [None, ""])[1]
SCREEN = {"home": ".screen-home-actual", "profile": ".screen-profile", "rewards": ".screen-rankings", "calendar": ".screen-calendar-tab"}

# ---- the trace -----------------------------------------------------------------------------------------------------------------------------
CATS = "devtools.timeline,disabled-by-default-devtools.timeline,disabled-by-default-devtools.timeline.stack,v8.execute,cc,viz"
def trace_run(pg, cdp, fn, tail_ms):
    evs, done = [], []
    cdp.on("Tracing.dataCollected", lambda p: evs.extend(p["value"]))
    cdp.on("Tracing.tracingComplete", lambda p: done.append(1))
    cdp.send("Tracing.start", {"categories": CATS, "transferMode": "ReportEvents"})
    fn()
    pg.wait_for_timeout(tail_ms)
    cdp.send("Tracing.end")
    for _ in range(400):
        if done: break
        pg.wait_for_timeout(100)
    cdp.remove_listener("Tracing.dataCollected", cdp._listeners["Tracing.dataCollected"][-1]) if False else None
    return evs
def analyse(evs, thr):
    names = {}
    for e in evs:
        if e.get("name") == "thread_name": names[(e["pid"], e["tid"])] = e["args"]["name"]
    th = lambda e: names.get((e.get("pid"), e.get("tid")))
    main = [e for e in evs if th(e) == "CrRendererMain" and e.get("ph") == "X"]
    cpu = lambda e: e.get("tdur", e["dur"]) / 1000.0 / thr
    ty = lambda e: (e.get("args", {}).get("data", {}) or {}).get("type")
    downs = [e["ts"] for e in main if e["name"] == "EventDispatch" and ty(e) in ("pointerdown", "mousedown", "touchstart")]
    if not downs: return None
    t0 = min(downs); t1 = t0 + 1_100_000
    tasks = [e for e in main if e["name"] == "RunTask" and t0 - 2000 <= e["ts"] <= t1]
    inputs = [(ty(e), cpu(e)) for e in main if e["name"] == "EventDispatch" and t0 - 2000 <= e["ts"] <= t1
              and ty(e) in ("pointerdown", "pointerup", "click", "touchstart", "touchend", "mousedown", "mouseup")]
    # style / layout recalcs attributed to the script function that forced them
    forced = collections.Counter()
    for e in main:
        if e["name"] in ("UpdateLayoutTree", "Layout") and t0 - 2000 <= e["ts"] <= t1:
            a = e.get("args", {})
            st = (a.get("beginData", {}) or {}).get("stackTrace") or a.get("stackTrace") or []
            fn = next((f.get("functionName") for f in st if f.get("functionName")), None)
            # a pass that did something: restyled an element, or took measurable time (a read with nothing dirty is a marker, not a pass)
            real = (e["name"] == "UpdateLayoutTree" and (a.get("elementCount") or 0) > 0) or (e["name"] == "Layout" and e.get("tdur", 0) >= 50)
            if fn and real: forced[(e["name"], fn)] += 1
    viz = [e.get("tdur", e["dur"]) / 1000.0 for e in evs if th(e) == "VizCompositorThread" and e.get("ph") == "X" and e.get("name") == "Display::DrawAndSwap" and t0 <= e["ts"] <= t1]
    return {"worst": max([cpu(e) for e in tasks] or [0]), "total": sum(cpu(e) for e in tasks),
            "inputMax": max([c for _, c in inputs] or [0]), "inputs": inputs, "forced": forced,
            "viz": statistics.median(viz) / thr if viz else 0, "draws": len(viz)}

# ---- the page's own frame clock and the glass --------------------------------------------------------------------------------------------
CLOCK = """()=>{ const S=window.__tb={frames:[],on:true}; const f=t=>{ if(!S.on) return; S.frames.push(t); requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
def frame_stats(fr):
    d = [fr[i + 1] - fr[i] for i in range(len(fr) - 1)]
    if len(d) < 3: return None
    s = sorted(d); n = len(s)
    return {"n": n, "p50": round(s[n // 2], 1), "p95": round(s[min(n - 1, int(n * .95))], 1), "max": round(s[-1], 1), "late": sum(1 for x in d if x > 25)}
HOLD = """([sel, dest, hold])=>{ const st=document.getElementById('stage'); const S=window.__hold={ t0:performance.now(), rows:[], mount:null, mountFrame:null, lensSeen:null, lensGone:null, before:null, on:true, fr:0 };
  const heavy=()=>{ let run=0; try{ st.getAnimations({subtree:true}).forEach(a=>{ if(a.playState!=='running') return; const t=a.effect&&a.effect.target; if(t&&t.closest&&t.closest(hold)) run++; }); }catch(e){} return run; };
  S.before=heavy();
  const mo=new MutationObserver(()=>{ if(S.mount===null && st.querySelector(dest)){ S.mount=performance.now()-S.t0; S.mountFrame=S.fr; } }); mo.observe(st,{childList:true});
  /* in FRAMES, not milliseconds: a frame on a shared sandbox can take 300ms, and the hold's own look is two frames after the press and one after the build */
  const tick=()=>{ if(!S.on) return; S.fr++; const t=performance.now()-S.t0; const lensEl=document.getElementById('bottomtabs-lens'); const up=!!(lensEl && lensEl.classList.contains('is-up') && parseFloat(getComputedStyle(lensEl).opacity)>.5);   /* the glass SEEN: it hands over to the platter before its class is taken off */
    if(up && S.lensSeen===null) S.lensSeen=S.fr; if(!up && S.lensSeen!==null && S.lensGone===null) S.lensGone=S.fr;
    if(S.fr%2===0) S.rows.push([S.fr, up?1:0, heavy()]); requestAnimationFrame(tick); };
  requestAnimationFrame(tick); }"""

IDLE_JOB = """()=>{ window.__idle=null; const t0=performance.now(); requestIdleCallback(()=>{ window.__idle={ at: Math.round(performance.now()-t0), up: !!document.querySelector('#bottomtabs-lens.is-up'),
  held: document.documentElement.classList.contains('tab-held'), settle: (typeof settleUntil==='number' && Date.now()<settleUntil) }; }); }"""
def tap(pg, cdp, touch, tab):
    return G["tap"](pg, cdp, touch, "#bottomtab-" + tab)

errs_all = []
SUM = {}
HOLD_OK = collections.defaultdict(list)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    for dev, thrs in DEVICES:
        for thr in thrs:
            label = dev + ("@%dx" % thr if thr > 1 else "")
            ctx, pg, cdp, errs, touch = G["open_page"](br, dev)
            cls = "finger" if dev in FINGER else "mouse"
            if thr > 1: cdp.send("Emulation.setCPUThrottlingRate", {"rate": thr})
            pg.wait_for_timeout(1200)
            pairs = [] if not TRACED else (QUICK_PAIRS if QUICK else PAIRS)
            rows = []
            fr_all = []
            for a, b in pairs:
                tap(pg, cdp, touch, a); pg.wait_for_timeout(1500 + 500 * (thr - 1))
                pg.evaluate(CLOCK)
                evs = trace_run(pg, cdp, lambda: tap(pg, cdp, touch, b), 1100 + 300 * (thr - 1))
                fr = pg.evaluate("()=>{ __tb.on=false; return __tb.frames; }")
                r = analyse(evs, thr)
                if not r:
                    chk("(5) %s %s>%s: the trace saw the tap" % (label, a, b), False); continue
                r["pair"] = (a, b); r["fs"] = frame_stats(fr); rows.append(r); fr_all += fr
                if r["fs"] is None: chk("(5) %s %s>%s: the page drew frames" % (label, a, b), False)
            if rows:
                # (2) no style pass per loop
                worst_forced = collections.Counter()
                for r in rows:
                    for k, v in r["forced"].items(): worst_forced[k] = max(worst_forced[k], v)
                top = worst_forced.most_common(1)
                tmax = top[0][1] if top else 0
                chk("(2) %s: no script function forces more than 8 style recalcs or layouts in a tab change (most: %s)" % (label, top[0] if top else "-"), tmax <= 8, dict(worst_forced.most_common(4)))
                # (3) budgets
                B = BUDGET[cls]
                w = max(r["worst"] for r in rows); i = max(r["inputMax"] for r in rows); tot = statistics.median([r["total"] for r in rows])
                wp = max(rows, key=lambda r: r["worst"])["pair"]; ip = max(rows, key=lambda r: r["inputMax"])["pair"]
                chk("(3a) %s: no main-thread task over %dms (1x-equivalent) in a tab change (worst %.0fms, %s>%s)" % (label, B["worst"], w, wp[0], wp[1]), w <= B["worst"], w)
                chk("(3b) %s: no input handler over %dms (worst %.1fms, %s>%s)" % (label, B["input"], i, ip[0], ip[1]), i <= B["input"], i)
                chk("(3c) %s: a tab change's main-thread CPU, median of %d pairs, under %dms (%.0fms)" % (label, len(rows), B["total"], tot), tot <= B["total"], tot)
                fs = frame_stats(fr_all)
                vz = statistics.median([r["viz"] for r in rows if r["viz"]] or [0])
                info("%s frame clock over %d hops: p50 %s p95 %s max %s ms, %d late (>25ms) | software compositor draw per frame %.1fms (median) | worst task %.0fms, total %.0fms (1x-eq)" % (
                    label, len(rows), fs and fs["p50"], fs and fs["p95"], fs and fs["max"], fs["late"] if fs else -1, vz, w, tot))
                SUM[label] = {"total": tot, "worst": w, "p95": fs and fs["p95"], "viz": vz}
            # (1) the finger's tap holds the heavy art
            if cls == "finger" and thr == 1:
                bad = []; unmeasured = []; nconcl = 0
                for a, b in (QUICK_PAIRS if QUICK else PAIRS):
                    tap(pg, cdp, touch, a); pg.wait_for_timeout(1600)
                    pg.evaluate(HOLD, [SCREEN[b], SCREEN[b], HOLD_SEL])
                    tap(pg, cdp, touch, b); pg.wait_for_timeout(1700)
                    H = pg.evaluate("()=>{ __hold.on=false; return __hold; }")
                    mf = H["mountFrame"]
                    grace = lambda fr: mf is not None and mf <= fr <= mf + 5     # the look is a frame after the build
                    after_press = lambda r: r[1] and r[0] >= (H["lensSeen"] or 0) + 3
                    viol = [r for r in H["rows"] if after_press(r) and r[2] > 0 and not grace(r[0])]
                    held = [r for r in H["rows"] if after_press(r) and not grace(r[0])]
                    if H["lensSeen"] is None: unmeasured.append("%s>%s (no lens)" % (a, b)); continue
                    if viol: bad.append("%s>%s: %d of %d samples under the lens had %d loops running (before the tap: %d)" % (a, b, len(viol), len(held), max(r[2] for r in viol), H["before"]))
                    elif H["before"] > 0 or b == "home": nconcl += 1
                    # given back: once the glass has landed Home's hero (and the rest) is running again
                    if b == "home":
                        pg.wait_for_timeout(500)
                        back = pg.evaluate("([sel,hold])=>{ let n=0; document.getElementById('stage').getAnimations({subtree:true}).forEach(x=>{ if(x.playState!=='running') return; const t=x.effect&&x.effect.target; if(t&&t.closest&&t.closest(hold)) n++; }); return n; }", [SCREEN[b], HOLD_SEL])
                        if back < 5: bad.append("%s>%s: after the glass landed only %d loops of Home's hero are running" % (a, b, back))
                chk("(1) %s: a tap holds the heavy art under the glass and gives it back (%d pairs measured)" % (label, nconcl), not bad and not unmeasured and nconcl >= len(QUICK_PAIRS if QUICK else PAIRS) // 2, bad + unmeasured)
            # (6) the idle stand-in (Safari has no requestIdleCallback) does not run its jobs under a finger or the landing glass
            if cls == "finger" and thr == 1:
                late = []
                for a, b in (QUICK_PAIRS if QUICK else PAIRS)[:3]:
                    tap(pg, cdp, touch, a); pg.wait_for_timeout(1700)
                    c = pg.evaluate("(id)=>{ const r=document.getElementById(id).getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }", "bottomtab-" + b)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c[0], "y": c[1]}]})   # a finger that stays down (a slide's first second)
                    pg.wait_for_timeout(100); pg.evaluate(IDLE_JOB); pg.wait_for_timeout(1300)
                    mid = pg.evaluate("()=>window.__idle")
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                    for _ in range(40):                      # behind whatever else the page has queued, a job can take seconds
                        pg.wait_for_timeout(250)
                        if pg.evaluate("()=>!!window.__idle"): break
                    J = pg.evaluate("()=>window.__idle")
                    if mid: late.append("%s>%s: ran under the finger, %dms after it was asked (bar held %s)" % (a, b, mid["at"], mid["held"]))
                    elif not J: late.append("%s>%s: the job never ran" % (a, b))
                    elif J["up"] or J["held"] or J["settle"]: late.append("%s>%s: ran after the lift with the glass up %s, bar held %s, settling %s" % (a, b, J["up"], J["held"], J["settle"]))
                chk("(6) %s: a warm-up job asked for under a finger waits for the lift and the landing" % label, not late, late)
            errs_all += errs
            ctx.close()
    # (4) area
    base = SUM.get("1366x768x1")
    for big in ("3840x2160x1", "1920x1080x2"):
        if base and big in SUM:
            r = SUM[big]["total"] / max(1, base["total"])
            chk("(4) %s costs the main thread %.2fx what 1366x768 does per tab change (at most %.1fx)" % (big, r, AREA_RATIO), r <= AREA_RATIO, [SUM[big]["total"], base["total"]])
    br.close()
chk("(5) no page errors", not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
