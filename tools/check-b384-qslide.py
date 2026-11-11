"""Build 384 (r22): THE NEXT-QUESTION SLIDE, what runs inside it.
Madison: "there is still so much lag when swiping between stuff ... I noticed on Windows computers too, that swiping to the NEXT
QUESTION had a lot of lag". Read off the page at 4x CPU, real input, in Chromium (it is not a Windows GPU or a phone's WebKit: what is
measured is the main thread's work in the frames around the move, which is what a slow machine runs out of first). A laptop is
1366x768 at 1x (Windows' user agent, a real mouse, then the Enter key); a phone is 440x956 at 3x (iPhone UA, installed, real touches:
a tap on Next, then a swipe past the line). A drill on one unit, each question answered, then Next, eight times in a row each way.
For each Next, a trace of the main thread from the input to 700ms after it:
 (1) THE INPUT'S OWN TASK is short: the median task that holds the click / key / touch-end is under 56ms (66ms on a phone) at 4x CPU, times how much
     slower than an idle core the machine is just now (a fixed loop; never below x1: 384.20, the budget failed on one build as the load moved) (the move starts
     in the frame after it, so this is the lag before anything moves; 60-75ms before, the build of the next question plus three
     style passes of the whole page forced by script).
 (2) NO PAGE-WIDE LAYOUT FORCED BY SCRIPT INSIDE THE MOVE: while the slide is under way (input to its end) syncChatDock /
     placeDockBesidePause - which measures Pause with offsetLeft + getComputedStyle after every stage and body mutation, so twice or
     three times inside a Next - run 0 times (counted by wrapping them), and the style/layout passes that script forces from the
     input to the first frame add up to under 24ms at 4x (a question and its panel: one forced pass is the build's own).
 (3) IT STILL ENDS RIGHT: the next question is up (pos + 1) within 900ms, no copy of the old one or stand-in is left on the page,
     html.q-sliding is off, the new panel carries no transform, and the chat button is where it was before the Next (the bar's and
     the dock's sync is only moved to the slide's end, never dropped).
 (4) no page error.
Run:  python3 tools/check-b384-qslide.py [--against REV|path/to/index.html]   (--against 3a6675d must FAIL (1)(2))"""
import os, sys, time, json, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
_args = sys.argv[:]
ONLY_N = int(_args[_args.index("--only") + 1]) if "--only" in _args else None
if "--only" in sys.argv: del sys.argv[sys.argv.index("--only"):sys.argv.index("--only") + 2]
_src = open(os.path.join(HERE, "check-b384-desktop.py")).read().split("\nwith sync_playwright() as pw:")[0]
if "--against" in _args:
    _v = _args[_args.index("--against") + 1]
    if os.path.isfile(_v):
        sys.argv = [sys.argv[0]]
        _src = _src.replace('SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()', 'SRC = open(%r, encoding="utf-8").read()' % os.path.abspath(_v))
        _src = _src.replace('if "--against" in sys.argv:', 'if False:')
    else:
        sys.argv = [sys.argv[0], "--against", _v]
else:
    sys.argv = [sys.argv[0]]
G = {"__file__": os.path.join(HERE, "check-b384-desktop.py"), "__name__": "b384qslide"}
exec(_src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
def info(s): print("INFO " + s, flush=True)

START = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const unit=QUESTIONS[0].topic.trim();
 const idx=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit && inWholeUnit(QUESTIONS[i]));
 cfg.source='all'; cfg.mode='drill'; cfg.units=[unit]; beginRun(idx); for(let t=0;t<80&&!document.querySelector('.qpanel .choice');t++) await wait(100); await wait(1500); }"""
ANSWER = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const qi=order[pos]; const k=optionOrder(qi).indexOf(QUESTIONS[qi].answer);
 [...document.querySelectorAll('.qpanel .choice')][k].click(); await wait(1500); }"""
# counts the dock's measure (and the page-wide sync above it) from the page, with when: window.__dc (ms), and when the slide ended
WRAP = """()=>{ if(window.__wrapped) return; window.__wrapped=true; window.__dc=[]; window.__slideEnd=null;
  const f=window.placeDockBesidePause; window.placeDockBesidePause=function(){ window.__dc.push(performance.now()); return f.apply(this, arguments); };
  const q=window.qSlideDone; window.qSlideDone=function(){ window.__slideEnd=performance.now(); return q.apply(this, arguments); }; }"""
BEFORE = """()=>{ const b=document.getElementById('chatdock-btn'); window.__dc=[]; window.__slideEnd=null;
  return { pos:pos, top:b&&b.style.top, right:b&&b.style.right }; }"""
# calls inside the slide: before its end (a finger landing, the move, the build). The one the slide's end owes comes after it, in idle time.
AFTER = """()=>{ const b=document.getElementById('chatdock-btn'); const p=document.querySelector('#stage .qpanel');
  return { pos:pos, top:b&&b.style.top, right:b&&b.style.right, sliding:document.documentElement.classList.contains('q-sliding'),
    stray: document.querySelectorAll('body > .q-slide-clone, body > .q-blurpair, body > .panel').length,
    tx: p ? (p.style.transform||'') : null, calls:window.__dc.filter(t=>window.__slideEnd==null||t<window.__slideEnd).length, total:window.__dc.length }; }"""
CALLS = "()=>window.__dockCalls"

def trace_run(cdp, pg, fn, settle=900):
    evs = []; done = []
    h1 = lambda p: evs.extend(p["value"]); h2 = lambda p: done.append(1)
    cdp.on("Tracing.dataCollected", h1); cdp.on("Tracing.tracingComplete", h2)
    cdp.send("Tracing.start", {"categories": "devtools.timeline,disabled-by-default-devtools.timeline", "transferMode": "ReportEvents"})
    fn(); pg.wait_for_timeout(settle)
    cdp.send("Tracing.end")
    for _ in range(150):
        if done: break
        pg.wait_for_timeout(100)
    try: cdp.remove_listener("Tracing.dataCollected", h1); cdp.remove_listener("Tracing.tracingComplete", h2)
    except Exception: pass
    return evs

def cpu(e): return e.get("tdur", e["dur"]) / 1000     # the thread's own CPU time: a busy machine does not lengthen it
def read_trace(evs, kinds):
    """The task holding the input event (first of `kinds`), the style/layout script forces from it to its first frame, and the longest task
    from 250ms after it on (the slide's end; the slide is 280-392ms)."""
    main = set()
    for e in evs:
        if e.get("name") == "thread_name" and e.get("args", {}).get("name") == "CrRendererMain": main.add((e["pid"], e["tid"]))
    M = [e for e in evs if (e.get("pid"), e.get("tid")) in main and e.get("ph") == "X"]
    typ = lambda e: e.get("args", {}).get("data", {}).get("type")
    inp = sorted((e for e in M if e["name"] == "EventDispatch" and typ(e) in kinds), key=lambda e: e["ts"])
    if not inp: return None
    t0 = inp[0]["ts"]
    tasks = sorted((e for e in M if e["name"] == "RunTask"), key=lambda e: e["ts"])
    tk = next((e for e in tasks if e["ts"] <= t0 <= e["ts"] + e["dur"]), None)
    if not tk: return None
    inner = [e for e in M if tk["ts"] <= e["ts"] and e["ts"] + e["dur"] <= tk["ts"] + tk["dur"] and e["name"] in ("UpdateLayoutTree", "Layout")]
    # forced = style / layout that script asked for: those nested in a script event of the task
    scr = [e for e in M if tk["ts"] <= e["ts"] and e["ts"] + e["dur"] <= tk["ts"] + tk["dur"] and e["name"] in ("FunctionCall", "EventDispatch", "TimerFire")]
    def in_script(e): return any(s["ts"] <= e["ts"] and e["ts"] + e["dur"] <= s["ts"] + s["dur"] and s is not e for s in scr)
    forced_ms = sum(cpu(e) * 1000 for e in inner if in_script(e)) / 1000
    late = [cpu(e) for e in tasks if t0 + 250000 <= e["ts"] <= t0 + 470000]
    early = [cpu(e) for e in tasks if t0 <= e["ts"] <= t0 + 250000 and e["dur"] > 4000 and ((e["ts"] + e["dur"]) > tk["ts"])]
    # the heaviest TASK from the input to 250ms after it: for a click or a key that is its own task; for a swipe it is the build that
    # follows the release by a frame (a timer), the move already under way on the compositor
    return {"task": cpu(tk), "wall": tk["dur"] / 1000, "heavy": round(max(early) if early else 0, 1), "forced": round(forced_ms, 1), "late": round(max(late) if late else 0, 1)}

LIMIT1 = {(False, "click"): 56, (False, "key"): 56, (True, "click"): 66, (True, "swipe"): 52}
# (384.20) THE BUDGETS ARE FOR AN UNLOADED CORE, AND SCALE WITH HOW LOADED THIS ONE IS. The thread's own CPU time for the same task is not constant on a
# shared machine: the sandbox's load swings between 4 and 10 on four cores and the same build's median read 47, 54 and 58 ms for the laptop's click (the
# build before the fix, 3a6675d, read 62-69 beside them; the phone's tap 61-60 against 67-83). So the machine's speed is read first - a fixed loop,
# five times, its second fastest - and the two millisecond budgets below are multiplied by how much slower than SPEED_REF it ran (never less than 1, so a quiet
# machine is held to the budgets as written). What tells the build before the fix from this one does not depend on the load and is unchanged: the dock
# is measured inside the slide 4 times against 0, and script forces 32-34 ms of style and layout against 17.
SPEED = """()=>{ const t = performance.now(); let x = 0; for(let i = 0; i < 3e7; i++) x += i % 7; return [performance.now() - t, x]; }"""
SPEED_REF = 45.0     # ms: that loop on one otherwise idle core of the sandbox this was read on
def machine_scale(pg):
    t = sorted(pg.evaluate(SPEED)[0] for _ in range(5))
    return max(1.0, t[1] / SPEED_REF)
def run_dev(br, dev, how, n=8):
    ctx, pg, cdp, errs, touch = G["open_page"](br, dev)
    scale = machine_scale(pg)
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; }")
    pg.evaluate(START); pg.evaluate(WRAP)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    res = []
    for i in range(n + 1):
        pg.evaluate(ANSWER)
        b = pg.evaluate(BEFORE)
        def fire():
            if how == "key": pg.keyboard.press("Enter")
            elif how == "swipe":
                cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 400, "y": 500}]}); time.sleep(0.15)
                t0 = time.time()
                while True:
                    u = min(1, (time.time() - t0) / 0.3)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 400 - 340 * u, "y": 500}]})
                    if u >= 1: break
                    time.sleep(0.01)
                cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            else: G["tap"](pg, cdp, touch, "#nextbtn")
        evs = trace_run(cdp, pg, fire)
        a = pg.evaluate(AFTER)
        kinds = ("touchend",) if how == "swipe" else ("keydown",) if how == "key" else ("click",)
        r = read_trace(evs, kinds)
        if i == 0 or not r: continue      # the first is a warm-up
        r.update(calls=a["calls"], ok=(a["pos"] == b["pos"] + 1 and not a["sliding"] and a["stray"] == 0 and not a["tx"] and a["top"] == b["top"] and a["right"] == b["right"]), after=a, before=b)
        res.append(r)
    ctx.close()
    return res, errs, scale

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    allerrs = []
    for k_, (label, dev, how) in enumerate([("laptop, a click on Next", "1366x768x1", "click"), ("laptop, the Enter key", "1366x768x1", "key"),
                            ("phone, a tap on Next", "phone", "click"), ("phone, a swipe past the line", "phone", "swipe")]):
        if ONLY_N is not None and k_ != ONLY_N: continue
        res, errs, scale = run_dev(br, dev, how); allerrs += errs
        if len(res) < 5: chk(label + ": enough runs read (%d)" % len(res), False); continue
        med = lambda k: round(statistics.median(r[k] for r in res), 1)
        info("%s: input task median %s ms (max %s), forced style/layout median %s ms, slide's late tasks max %s ms, dock measures inside the slide %s"
             % (label, med("task"), max(round(r["task"], 1) for r in res), med("forced"), max(r["late"] for r in res), [r["calls"] for r in res]))
        info("%s: every sample (ms of the main thread's own CPU, sorted): task %s, heaviest after the input %s, forced style/layout %s" % (label, sorted(round(r["task"]) for r in res), sorted(round(r["heavy"]) for r in res), sorted(round(r["forced"]) for r in res)))
        # the swipe's input task is the release (touchend); its build is a frame later in a timer, so for it (1) reads the release alone
        key1 = "heavy" if how == "swipe" else "task"
        lim1 = LIMIT1[(dev == "phone", how)] * scale
        info("%s: this machine ran the speed loop %.2fx slower than the reference, so the budgets are x%.2f (task %.0f ms, forced style/layout 24 -> %.0f ms)" % (label, scale, scale, lim1, 24 * scale))
        chk("(1) %s: the %s is short (median %s ms, budget %.0f)" % (label, "release's build (the heaviest task after it)" if how == "swipe" else "input's task", med(key1), lim1), med(key1) <= lim1, [round(r[key1]) for r in res])
        if how != "swipe":
            chk("(2) %s: no dock measure inside the slide (%s)" % (label, [r["calls"] for r in res]), max(r["calls"] for r in res) <= 1 and statistics.median(r["calls"] for r in res) == 0,
                [r["calls"] for r in res])
            chk("(2) %s: forced style/layout under 24ms x%.2f (median %s)" % (label, scale, med("forced")), med("forced") <= 24 * scale, [r["forced"] for r in res])
        else:
            chk("(2) %s: no dock measure inside the slide (%s)" % (label, [r["calls"] for r in res]), statistics.median(r["calls"] for r in res) == 0, [r["calls"] for r in res])
        bad = [r for r in res if not r["ok"]]
        chk("(3) %s: it ends right in all %d (next question up, nothing left, the chat button where it was)" % (label, len(res)), not bad, [(r["before"], r["after"]) for r in bad][:2])
    chk("(4) no page error", not allerrs, allerrs)
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
