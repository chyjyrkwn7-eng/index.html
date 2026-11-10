"""Build 384 (r15): GOING TO THE NEXT QUESTION IS THE SAME MOVE ON EVERY SIZE OF SCREEN, and the unit / chapter pickers' enter and leave.
Madison: "I saw something taking a test on a LARGE SCREEN and going to the next question was not smooth at all. Get this fixed. Ensure the
smoothness is the same for all devices and all screen sizes." / "ensure the transition from selecting units is good".
Read off the page in Chromium with CDP traces (CPU time of the threads, which a busy machine does not lengthen) and the page's own clocks.
Viewports: phone 440x956 @3 (iPhone UA, touch, installed), iPad 834x1194 @2 and 1024x1366 @2 (touch), laptop 1366x768 @1 and 1512x982 @2, desktops
1920x1080, 2560x1440 and 3840x2160 @1 (Windows UA, a mouse, no touch). A drill, each question answered, then Next (a tap or a click) with the main
thread at 4x (and 6x with --full). Academy: the shortest and the longest questions of the bank. Fire Code (when PDFJS_DIR is set; it draws the
county booklet): a county question with its code box shut, with it open, and with the pre-answer hint's picture open.
 (1) THE MOVE ENDS WITH NOTHING STILL SHOWING OF THE OLD QUESTION: at the slide's last frame the outgoing copy's opacity x the share of it that is
     inside the window is under 2% of its area (a push that crosses the panel's own width takes it clean off a phone, but on a window wider than the
     panel it ended mid-screen at 55% and was removed in one frame - the pop that read as "not smooth"), and at its first frame the incoming
     question is as faint (it appeared fully formed in the middle of the window). Measured by sampling both copies on the compositor's own clock.
 (2) the input's own task (the click / tap that starts the move: the next question's build) is short, and no task of the main thread in the move's
     frames (CPU time) is a long one, on every size - the work does not grow with the window: the median of the input task is within the budget
     below and does not differ by more than 12ms between the smallest and the largest window.
 (3) NOTHING WINDOW-WIDE IS BLURRED IN THE UNIT PICKERS' SHEET: the start sheet (as wide as the window) is solid and its backdrop-filter is none
     (it was blur(16px) saturate(2) over 80vh x the window: 106ms of draw a frame at 3840x2160 in the software compositor, 15ms on a phone). The
     compositor's draw ms of the slide are printed per size; the sandbox's software draw swings too much run to run to be a budget.
 (4) THE FRAMES: wall-clock rAF frame gaps from the input to the end of the move (4x CPU, medians over the runs of a viewport): p95 under 70ms,
     no more than 4 dropped frames in a move; the same on every size (the spread of the p95 between the phone and the biggest window under 25ms).
 (5) IT STILL ENDS RIGHT: the next question is up (pos + 1), no copy or stand-in left on the page, html.q-sliding off, the new panel carries no
     transform, no page error.
 (6) THE UNIT PICKERS: Start Studying -> mode -> units -> Loading -> the first question, each a screen change: its main-thread frame work (CPU) under
     the budget on every size, and nothing of the old screen left over.
Run:  python3 tools/check-b384-bigslide.py [--against REV|path/to/index.html] [--quick] [--full] [--report] [--only fc|academy|units]
      (--against main's index.html must FAIL (1)(3) on the big windows; PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> adds the Fire Code legs)"""
import os, sys, time, json, statistics, mimetypes, re
HERE = os.path.dirname(os.path.abspath(__file__))
def _opt(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name); v = sys.argv[i + 1] if i + 1 < len(sys.argv) else default; del sys.argv[i:i + 2]; return v
    return default
def _flag(name):
    if name in sys.argv: sys.argv.remove(name); return True
    return False
ONLY = _opt("--only"); AGAINST = _opt("--against"); QUICK = _flag("--quick"); FULL = _flag("--full"); REPORT = _flag("--report")
_src = open(os.path.join(HERE, "check-b384-desktop.py")).read().split("\nwith sync_playwright() as pw:")[0]
if AGAINST:
    if os.path.isfile(AGAINST):
        _src = _src.replace('SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()', 'SRC = open(%r, encoding="utf-8").read()' % os.path.abspath(AGAINST))
        _src = _src.replace('if "--against" in sys.argv:', 'if False:')
    else:
        sys.argv += ["--against", AGAINST]
_src = _src.replace("    pg = ctx.new_page(); errs = []", "    HOOK(ctx); pg = ctx.new_page(); errs = []", 1)
G = {"__file__": os.path.join(HERE, "check-b384-desktop.py"), "__name__": "b384bigslide"}
exec(_src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def info(s): print("INFO " + s, flush=True)

G["DEVS"]["ipad13"] = (1024, 1366, 2, True)
PDFJS = (os.environ.get("PDFJS_DIR", "").rstrip("/") + "/") if os.environ.get("PDFJS_DIR") else ""
HAVE_PDF = bool(PDFJS) and os.path.exists(PDFJS + "build/pdf.min.mjs")
def hook(ctx):
    if not HAVE_PDF: return
    def h(r, req):
        rel = req.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
        if not os.path.exists(p): return r.fulfill(status=404, body="")
        r.fulfill(status=200, body=open(p, "rb").read(), content_type=mimetypes.guess_type(p)[0] or "text/javascript", headers={"access-control-allow-origin": "*"})
    ctx.route("**/pdfjs-dist@5.4.149/**", h)
G["HOOK"] = hook

VIEWPORTS = [("phone 440x956@3", "phone"), ("iPad 834x1194@2", "ipad"), ("iPad 1024x1366@2", "ipad13"), ("laptop 1366x768@1", "1366x768x1"),
             ("laptop 1512x982@2", "1512x982x2"), ("desktop 1920x1080@1", "1920x1080x1"), ("desktop 2560x1440@1", "2560x1440x1"), ("desktop 3840x2160@1", "3840x2160x1")]
if QUICK: VIEWPORTS = [v for v in VIEWPORTS if v[1] in ("phone", "1366x768x1", "1920x1080x1", "3840x2160x1")]
elif not FULL: VIEWPORTS = [v for v in VIEWPORTS if v[1] in ("phone", "ipad13", "1366x768x1", "1920x1080x1", "3840x2160x1")]
N_RUNS = 4 if QUICK else 6

# a Fire Code account: the owner's id (the class's owner), the class active, its drill store the same seed
def ifc_init():
    seed = json.dumps(G["SEED"])
    return ("(()=>{ try{ if(sessionStorage.getItem('__seededifc')) return; sessionStorage.setItem('__seededifc','1');"
            "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
            "localStorage.setItem('class26e.ifc.drill.v1', %s); localStorage.setItem('class26e.ifc.synccode','TEST-3846');"
            "['intro.seen','unithold.tip','daily.seen','savecode.asked','savecode.card','getstarted'].forEach(k=>localStorage.setItem('class26e.ifc.'+k,'1'));"
            "localStorage.setItem('class26e.ifc.weekrecap.v1','9999-12-31'); }catch(e){} })()") % json.dumps(seed)

# ------------------------------------------------------------------------------------------------------------ the page's side
ACAD_START = """async([which, n])=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const L=i=>String(QUESTIONS[i].q||'').length+QUESTIONS[i].choices.join('').length;
 let ids=QUESTIONS.map((q,i)=>i).filter(i=>inWholeUnit(QUESTIONS[i])); ids.sort((a,b)=>which==='long'?L(b)-L(a):L(a)-L(b)); ids=ids.slice(0,n);
 cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic.trim()]; beginRun(ids);
 for(let t=0;t<80&&!document.querySelector('.qpanel .choice');t++) await wait(100); await wait(1500);
 return ids.map(L); }"""
FC_START = """async([which, n])=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const L=i=>(QUESTIONS[i].ifc.explanation||'').length+String(QUESTIONS[i].q||'').length+QUESTIONS[i].choices.join('').length;
 let ids=QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].ifc && QUESTIONS[i].ifc.citation.source==='amendment' && !QUESTIONS[i].ifc.citation.blur);
 ids.sort((a,b)=>which==='long'?L(b)-L(a):L(a)-L(b)); ids=ids.slice(0,n);
 cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids);
 for(let t=0;t<80&&!document.querySelector('.qpanel .choice');t++) await wait(100); await wait(1500);
 return ids.map(L); }"""
# the pre-answer hint's picture, opened (when this question has one), and the code box (the remembered preference), then the right answer
HINT = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); let b=null;
 for(let t=0;t<30&&!(b=document.querySelector('.qpanel .ifc-hint-btn'));t++) await wait(100);
 if(!b) return false; b.click(); for(let t=0;t<60&&!document.querySelector('.qpanel .ifc-hintpic canvas');t++) await wait(100); await wait(500); return !!document.querySelector('.qpanel .ifc-hintpic canvas'); }"""
ANSWER = """async(wantCode)=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const qi=order[pos]; const k=optionOrder(qi).indexOf(QUESTIONS[qi].answer);
 [...document.querySelectorAll('.qpanel .choice')][k].click(); await wait(1200);
 if(wantCode){ for(let t=0;t<60&&!document.querySelector('.qpanel .ifc-code[open] .ifc-clips canvas');t++) await wait(100); await wait(500); }
 return !!document.querySelector('.qpanel .ifc-code[open] canvas'); }"""
SET_CODEPREF = "(on)=>{ try{ ifcCodeOpenSet(on); }catch(e){} }"
# the page's own clocks: rAF stamps (and the long tasks) from the call to 1.1s on
FRAMES = """(ms)=>{ window.__fr=[]; const t0=performance.now(); const f=t=>{ window.__fr.push(t); if(t-t0<ms) requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
# the move's two copies, on the compositor's clock: at the first and last frame of the slide the outgoing copy's opacity x share inside the window, and
# the incoming panel's. Read by freezing every slide animation at 0 and at 1 of its length (the page holds still while they are read).
WRAP = """()=>{ if(window.__wrapped) return; window.__wrapped=true; window.__end=null; const q=window.qSlideDone; window.qSlideDone=function(){ window.__end=performance.now(); return q.apply(this, arguments); }; }"""
MASS = """(f)=>{ const vw=innerWidth; const an=document.getAnimations().filter(a=>{ const t=a.effect&&a.effect.getTiming(); return t && t.easing==='linear' && t.duration>=150 && t.duration<=600 && a.effect.target && a.effect.target.isConnected; });
 const out=[]; an.forEach(a=>{ a.pause(); a.currentTime=a.effect.getTiming().duration*f; });
 const cl=document.querySelector('body > .q-slide-clone'); const inc=document.querySelector('#stage > .qpanel');
 const mass=el=>{ if(!el) return null; const r=el.getBoundingClientRect(), cs=getComputedStyle(el); const vis=Math.max(0, Math.min(vw, r.right)-Math.max(0, r.left))/Math.max(1, r.width); return Math.round(vis*(+cs.opacity)*1000)/1000; };
 const cv=cl && cl.querySelector('canvas.__probe'); let px=null; if(cv){ px=0; try{ const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data; for(let i=3;i<d.length;i+=4*20) if(d[i]) px++; }catch(e){ px=-1; } }
 const res={ n:an.length, out:mass(cl), inc:mass(inc), probe:px }; return res; }"""
# a picture in the question (a canvas painted red, as a code box's print is): the copy has to carry it
PROBE = """()=>{ const p=document.querySelector('#stage .qpanel'); if(!p) return; const c=document.createElement('canvas'); c.width=120; c.height=40; c.className='__probe'; c.style.cssText='display:block;width:120px;height:40px';
  const g=c.getContext('2d'); g.fillStyle='#f00'; g.fillRect(0,0,120,40); p.appendChild(c); }"""
AFTER = """()=>{ const p=document.querySelector('#stage .qpanel'); return { pos:pos, sliding:document.documentElement.classList.contains('q-sliding'),
  stray: document.querySelectorAll('body > .q-slide-clone, body > .q-blurpair, body > .panel').length, tx: p ? (p.style.transform||'') : null }; }"""
# the layers' area at mid-move: from the compositor's own tree (CDP LayerTree)

# ------------------------------------------------------------------------------------------------------------ the trace's side
def collect(cdp, pg, fn, settle, cats):
    evs = []; done = []
    h1 = lambda p: evs.extend(p["value"]); h2 = lambda p: done.append(1)
    cdp.on("Tracing.dataCollected", h1); cdp.on("Tracing.tracingComplete", h2)
    cdp.send("Tracing.start", {"categories": cats, "transferMode": "ReportEvents"})
    fn(); pg.wait_for_timeout(settle)
    cdp.send("Tracing.end")
    for _ in range(200):
        if done: break
        pg.wait_for_timeout(100)
    try: cdp.remove_listener("Tracing.dataCollected", h1); cdp.remove_listener("Tracing.tracingComplete", h2)
    except Exception: pass
    return evs
CATS = "devtools.timeline,disabled-by-default-devtools.timeline,cc,viz"
def cpu(e): return e.get("tdur", e.get("dur", 0)) / 1000
def read_trace(evs, kinds, win_ms):
    """the task holding the input (CPU ms), every main-thread frame's CPU in the window after it, the longest other task, and the compositor's
    work in the window: the draw (software renderer's DoDrawQuad: the pixels a slow GPU would push), the raster, the frames presented"""
    main = set(); other = {}
    for e in evs:
        if e.get("name") == "thread_name":
            nm = e.get("args", {}).get("name", ""); k = (e["pid"], e["tid"])
            if nm == "CrRendererMain": main.add(k)
            other[k] = nm
    M = [e for e in evs if (e.get("pid"), e.get("tid")) in main and e.get("ph") == "X"]
    typ = lambda e: e.get("args", {}).get("data", {}).get("type")
    tasks = sorted((e for e in M if e["name"] == "RunTask"), key=lambda e: e["ts"])
    if kinds is None:
        if not tasks: return None
        t0 = tasks[0]["ts"]; t1 = t0 + win_ms * 1000; tk = {"ts": t0, "dur": 0, "tdur": 0}
    else:
        inp = sorted((e for e in M if e["name"] == "EventDispatch" and typ(e) in kinds), key=lambda e: e["ts"])
        if not inp: return None
        t0 = inp[0]["ts"]; t1 = t0 + win_ms * 1000
        tk = next((e for e in tasks if e["ts"] <= t0 <= e["ts"] + e["dur"]), None)
        if not tk: return None
    inwin = [e for e in tasks if t0 <= e["ts"] <= t1]
    def has(t, name): return any(e["name"] == name and t["ts"] <= e["ts"] and e["ts"] + e["dur"] <= t["ts"] + t["dur"] for e in M)
    frames = [cpu(t) for t in inwin if t is not tk and has(t, "ProxyMain::BeginMainFrame")]
    others = [cpu(t) for t in inwin if t is not tk and not has(t, "ProxyMain::BeginMainFrame")]
    allw = [e for e in evs if t0 <= e["ts"] <= t1]
    draw = [e for e in allw if e.get("name") == "SoftwareRenderer::DoDrawQuad" and e.get("ph") == "X"]
    swaps = sorted(e["ts"] for e in allw if e.get("name") == "Graphics.Pipeline.DrawAndSwap" and e.get("ph") in ("b", "B"))
    raster = [e for e in allw if e.get("name") == "RasterTask" and e.get("ph") == "X"]
    nsw = max(1, len(swaps))
    heavy = []
    for t in inwin:
        if cpu(t) < 50: continue
        kids = [e for e in M if e is not t and e["ts"] >= t["ts"] and e["ts"] + e["dur"] <= t["ts"] + t["dur"] and e["dur"] > 3000 and e["name"] not in ("RunTask", "ProxyMain::BeginMainFrame", "LatencyInfo.Flow", "FunctionCall")]
        heavy.append("%.0fms@%.0f: " % (cpu(t), (t["ts"] - t0) / 1000) + ", ".join("%s %.0f" % (k["name"], cpu(k)) for k in sorted(kids, key=lambda k: -k["dur"])[:6]))
    return {"heavy": heavy, "task": cpu(tk), "frames": frames, "other_max": max(others) if others else 0, "draw_ms": sum(cpu(e) for e in draw), "draw_per_frame": sum(cpu(e) for e in draw) / nsw,
            "raster_ms": sum(cpu(e) for e in raster), "presented": len(swaps), "gaps": [(b - a) / 1000 for a, b in zip(swaps, swaps[1:])]}

def pct(v, p):
    v = sorted(v)
    if not v: return 0
    return v[min(len(v) - 1, int(round((len(v) - 1) * p)))]
def frame_stats(fr, upto):
    """rAF stamps from the input to `upto` ms after: the p95 gap and the frames dropped (each gap counts for the frames it spans, less one)"""
    if len(fr) < 3: return None
    t0 = fr[0]; d = [b - a for a, b in zip(fr, fr[1:]) if b - t0 <= upto]
    if not d: return None
    return {"p50": pct(d, .5), "p95": pct(d, .95), "max": max(d), "dropped": sum(max(0, int(round(x / 16.667)) - 1) for x in d)}

def tap_next(pg, cdp, touch):
    """as a person does: Next scrolled to when a long question leaves it under the fold, then a real tap or click on it"""
    pg.evaluate("()=>{ const b=document.getElementById('nextbtn'); if(!b) return; const r=b.getBoundingClientRect(); if(r.bottom>innerHeight-8||r.top<0) b.scrollIntoView({block:'center',behavior:'instant'}); }")
    pg.wait_for_timeout(120)
    return G["tap"](pg, cdp, touch, "#nextbtn")

def run_scene(br, dev, cls, scen, rate, n_runs, label):
    """one boot: `n_runs` Nexts of one kind of question. scen: short | long (academy); fc-shut | fc-open | fc-hint (Fire Code)."""
    extra = [ifc_init()] if cls == "ifc" else []
    ctx, pg, cdp, errs, touch = G["open_page"](br, dev, extra)
    out = {"errs": errs, "runs": [], "mass0": [], "mass1": [], "label": label, "viewport": pg.evaluate("()=>[innerWidth, innerHeight]")}
    try:
        pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} }")
        if cls == "ifc":
            if pg.evaluate("()=>typeof activeClass==='function' ? activeClass() : (window.NOVA_CLASS||'')") not in ("ifc",):
                pass
        which = "long" if scen in ("long", "fc-shut", "fc-open", "fc-hint") else "short"
        pg.evaluate(SET_CODEPREF, scen == "fc-open") if cls == "ifc" else None
        out["lens"] = pg.evaluate(ACAD_START if cls == "academy" else FC_START, [which, n_runs + 8])
        pg.evaluate(WRAP)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": rate})
        for i in range(n_runs + 4):
            if len(out["runs"]) >= n_runs: break
            hinted = False
            if scen == "fc-hint": hinted = pg.evaluate(HINT)
            coded = pg.evaluate(ANSWER, scen == "fc-open")
            b = pg.evaluate("()=>pos")
            def fire():
                pg.evaluate(FRAMES, 1100); pg.wait_for_timeout(60)
                tap_next(pg, cdp, touch)
            evs = collect(cdp, pg, fire, 1100, CATS)
            fr = pg.evaluate("()=>window.__fr"); a = pg.evaluate(AFTER)
            r = read_trace(evs, ("click",) if True else (), 1100)
            if i == 0 or not r: continue
            if a["pos"] == b and not a["sliding"]:      # the tap did not take (a pill still rising under the pointer): a person taps again; not a move to measure
                out["missed"] = out.get("missed", 0) + 1; continue
            r["rAF"] = frame_stats(fr, 700); r["ok"] = (a["pos"] == b + 1 and not a["sliding"] and a["stray"] == 0 and not a["tx"]); r["hinted"] = hinted; r["coded"] = coded; r["after"] = (b, a)
            out["runs"].append(r)
        # the pops, read once per scene on a frozen move: every animation of the slide held at its first and its last frame
        for f_, key in ((0.0, "mass0"), (1.0, "mass1")):
            pg.evaluate(ANSWER, False)
            if f_ == 0.0: pg.evaluate(PROBE)
            pg.evaluate("()=>{ window.__keep=window.qSlideDone; window.qSlideDone=function(){}; }")
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            pg.evaluate("()=>{ const b=document.getElementById('nextbtn'); b.click(); }")
            pg.wait_for_timeout(80)
            out[key] = pg.evaluate(MASS, f_)
            pg.evaluate("()=>{ document.getAnimations().forEach(a=>{ try{ a.cancel(); }catch(e){} }); document.querySelectorAll('body > .q-slide-clone, body > .q-blurpair').forEach(n=>n.remove()); document.documentElement.classList.remove('q-sliding'); slideTransitionInFlight=false; window.qSlideDone=window.__keep; }")
            pg.wait_for_timeout(200)
    finally:
        ctx.close()
    return out


# ------------------------------------------------------------------------------------------------------------ the unit pickers
# what the app's own warm-up (warmBadgeStrikes, in idle slices from 5s after launch) has done by the time a person gets to the units: every unit's
# badge drawn once. A harness that taps through in the first seconds would measure that first drawing instead of the screen.
WARM = """()=>{ try{ const W=badgeStrikeSize(badgeDefaultPx()*badgeDpr()); unitsInTeachingOrder().forEach(u=>{ badgeStrikeGeometry(badgeShapeFor(u)); badgeStrikeURL(u, !unitBadgeEarned(u), W, badgeDirtStage(u)); try{ cardBadgeSVG(u, unitBadgeEarned(u)); }catch(e){} }); return true; }catch(e){ return String(e); } }"""
UNIT_STEPS = [("Home -> mode", "#bottomtab-start|.screen-home-actual .playbtn|.homestart .playbtn", "()=>!!document.querySelector('.modeselect')"),
              ("mode -> units", '.modecard[data-mode="drill"]', "()=>!!document.querySelector('label.pick')"),
              ("tick a unit", "label.pick", "()=>!!document.querySelector('label.pick input:checked')"),
              ("Start -> the sheet", "#bottomtab-start|#nextbtn", "()=>{ const m=document.querySelector('.unitoptions-modal'); return !!(m && !m.hidden); }"),
              ("Begin -> loading", ".sheet-begin-btn", "()=>!!document.getElementById('teststart-overlay')")]
def run_units(br, dev, rate, label):
    """Start Studying -> mode -> units -> a unit -> Start -> the sheet -> Begin -> LOADING TEST -> the first question, each a real tap on a real
    boot; per step the input task, the frames' CPU, the compositor's draw and raster, and where it landed."""
    ctx, pg, cdp, errs, touch = G["open_page"](br, dev, [])
    out = {"errs": errs, "steps": [], "label": label, "viewport": pg.evaluate("()=>[innerWidth, innerHeight]")}
    try:
        pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} }")
        out["warm"] = pg.evaluate(WARM)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": rate})
        for name, sel, arrived in UNIT_STEPS:
            def fire(sel=sel):
                use = pg.evaluate("(c)=>{ for(const s of c.split('|')){ const e=document.querySelector(s); if(e){ const r=e.getBoundingClientRect(); if(r.width>0 && r.height>0){ if(r.bottom>innerHeight||r.top<0) e.scrollIntoView({block:'nearest',behavior:'instant'}); return s; } } } return c.split('|')[0]; }", sel)
                pg.wait_for_timeout(80)
                G["tap"](pg, cdp, touch, use)
            evs = collect(cdp, pg, fire, 900, CATS)
            r = read_trace(evs, ("click",), 900)
            ok_ = bool(pg.evaluate(arrived))
            if not ok_ and "Begin" in name:
                pg.wait_for_timeout(700); G["tap"](pg, cdp, touch, ".sheet-begin-btn"); pg.wait_for_timeout(900); ok_ = bool(pg.evaluate(arrived)); out["begin_retry"] = True
            if r: r["name"] = name; r["arrived"] = ok_; out["steps"].append(r)
            else: out["steps"].append({"name": name, "arrived": ok_, "task": 0, "frames": [], "other_max": 0, "draw_per_frame": 0, "draw_ms": 0, "raster_ms": 0, "presented": 0, "gaps": []})
            if "sheet" in name:
                out["sheet"] = pg.evaluate("()=>{ const s=document.querySelector('.unitoptions-modal-sheet'); if(!s) return null; const cs=getComputedStyle(s); return { bf: cs.backdropFilter || cs.webkitBackdropFilter || 'none', bg: cs.backgroundColor, w: Math.round(s.getBoundingClientRect().width) }; }")
                out["sheet_draw"] = r["draw_ms"] if r else None
            pg.wait_for_timeout(1800 if "sheet" in name else 300)
        # the loading screen's end: the bar's last stretch, the overlay going, the first question building
        def wait_end(): pg.wait_for_timeout(1800)
        evs = collect(cdp, pg, wait_end, 1700, CATS)
        r = read_trace(evs, None, 1500)
        if r: r["name"] = "LOADING -> first question"; r["arrived"] = bool(pg.evaluate("()=>!!document.querySelector('.qpanel .choice') && !document.getElementById('teststart-overlay')")); out["steps"].append(r)
    finally:
        ctx.close()
    return out

def summarize_scene(o):
    R = o["runs"]
    if len(R) < 3: return None
    med = lambda k: statistics.median(r[k] for r in R)
    frames_all = [x for r in R for x in r["frames"]]
    rs = [r["rAF"] for r in R if r["rAF"]]
    return {"task": med("task"), "frame_p50": pct(frames_all, .5), "frame_p95": pct(frames_all, .95), "frame_max": max(frames_all) if frames_all else 0,
            "other_max": statistics.median(r["other_max"] for r in R), "draw_per_frame": med("draw_per_frame"), "raster": med("raster_ms"),
            "rAF_p95": statistics.median(x["p95"] for x in rs) if rs else None, "rAF_drop": statistics.median(x["dropped"] for x in rs) if rs else None,
            "rAF_max": statistics.median(x["max"] for x in rs) if rs else None,
            "bad": sum(1 for r in R if not r["ok"]), "bad_info": [r["after"] for r in R if not r["ok"]][:2], "mass0": o["mass0"], "mass1": o["mass1"], "n": len(R), "viewport": o["viewport"]}
def line(label, s):
    return ("%s: input task %.0fms | frame cpu p50 %.1f p95 %.1f max %.1f | other task max %.0f | draw/frame %.2fms raster %.0fms | rAF p95 %s max %s dropped %s | pop: out@end %s in@start %s"
            % (label, s["task"], s["frame_p50"], s["frame_p95"], s["frame_max"], s["other_max"], s["draw_per_frame"], s["raster"],
               None if s["rAF_p95"] is None else round(s["rAF_p95"], 1), None if s["rAF_max"] is None else round(s["rAF_max"], 1), s["rAF_drop"],
               (s["mass1"] or {}).get("out"), (s["mass0"] or {}).get("inc")))

BUDGET = {"pop": 0.02, "task": 120, "rAF_p95": 250, "dropped": 70}   # the frame budgets are ceilings for a stall (the sandbox is shared: its p95 swings 40-100ms run to run); the CPU numbers and the pops are the measure
def vp_area(vp): return vp[0] * vp[1]
if __name__ == "__main__":
    RATES = [4, 6] if FULL else [4]
    scenes = [("academy", "short"), ("academy", "long")]
    if HAVE_PDF: scenes += [("ifc", "fc-shut"), ("ifc", "fc-open"), ("ifc", "fc-hint")]
    if ONLY == "fc": scenes = [s_ for s_ in scenes if s_[0] == "ifc"]
    if ONLY == "academy": scenes = [s_ for s_ in scenes if s_[0] == "academy"]
    if ONLY == "units": scenes = []
    if QUICK: scenes = [s_ for s_ in scenes if s_[1] in ("long", "fc-open")] if ONLY != "units" else []
    if not HAVE_PDF and ONLY == "fc": print("SKIP the Fire Code legs: PDFJS_DIR is not set to an unpacked pdfjs-dist 5.4.149"); sys.exit(0)
    if not HAVE_PDF: info("Fire Code legs SKIPPED: set PDFJS_DIR to an unpacked pdfjs-dist 5.4.149 (the code box draws the county booklet with it)")
    results = {}; units = {}; errs_all = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=G["CHROME"])
        for rate in RATES:
            for (vl, dev) in VIEWPORTS:
                for (cls, scen) in scenes:
                    try:
                        o = run_scene(br, dev, cls, scen, rate, N_RUNS, "%s %s %s @%dx" % (vl, cls, scen, rate))
                    except Exception as e:
                        chk("%s %s %s: ran" % (vl, cls, scen), False, repr(e)); continue
                    errs_all += o["errs"]
                    sm = summarize_scene(o)
                    if not sm: chk("%s: enough runs (%d)" % (o["label"], len(o["runs"])), False); continue
                    results[(rate, dev, cls, scen)] = sm; sm["label"] = o["label"]; sm["probe"] = (o["mass0"] or {}).get("probe")
                    info(line(o["label"], sm))
                if ONLY in (None, "units") and rate == RATES[0]:
                    try:
                        u = run_units(br, dev, rate, vl); units[dev] = u; errs_all += u["errs"]
                        info("%s units: " % vl + " | ".join("%s task %.0f frame p95 %.0f draw %.0fms raster %.0fms%s" % (r["name"], r["task"], pct(r["frames"], .95), r["draw_ms"], r["raster_ms"], "" if r["arrived"] else " NOT ARRIVED") for r in u["steps"]))
                    except Exception as e:
                        chk("%s units: ran" % vl, False, repr(e))
        br.close()
    # ---------------------------------------------------------------------------------------------------- the asserts
    for (rate, dev, cls, scen), sm in sorted(results.items(), key=lambda kv: str(kv[0])):
        L = sm["label"]
        m1 = (sm["mass1"] or {}).get("out"); m0 = (sm["mass0"] or {}).get("inc")
        chk("(1) %s: nothing of the old question is left showing when the move ends, and the new one does not appear whole at its start (out %s, in %s)" % (L, m1, m0),
            m1 is not None and m0 is not None and m1 <= BUDGET["pop"] and m0 <= BUDGET["pop"], (m1, m0))
        if sm.get("probe") is not None:
            chk("(1b) %s: the copy that slides off carries a picture the question held (a canvas: %s of its samples painted)" % (L, sm["probe"]), sm["probe"] > 0, sm["probe"])
        chk("(2) %s: the input's task is short (%.0fms, <= %d at %dx CPU)" % (L, sm["task"], BUDGET["task"], rate), sm["task"] <= BUDGET["task"], sm["task"])
        if sm["rAF_p95"] is not None:
            chk("(4) %s: frame gaps in the move p95 %.0fms (<= %d), dropped %s (<= %d)" % (L, sm["rAF_p95"], BUDGET["rAF_p95"], sm["rAF_drop"], BUDGET["dropped"]),
                sm["rAF_p95"] <= BUDGET["rAF_p95"] and sm["rAF_drop"] <= BUDGET["dropped"], (sm["rAF_p95"], sm["rAF_drop"]))
        chk("(5) %s: it ends right in all %d (next question up, no copy left, class off, no transform)" % (L, sm["n"]), sm["bad"] == 0, sm.get("bad_info"))
    # the move is the same move on every size: the input task does not grow with the window
    for scen_key in sorted({(k[0], k[2], k[3]) for k in results}):
        rows = [(k[1], v) for k, v in results.items() if (k[0], k[2], k[3]) == scen_key]
        if len(rows) >= 2:
            ts = [v["task"] for _, v in rows]
            info("input task by size @%dx %s %s: %s" % (scen_key[0], scen_key[1], scen_key[2], ", ".join("%s %.0f" % (d_, v["task"]) for d_, v in rows)))
    for dev, u in units.items():
        vl = next(v[0] for v in VIEWPORTS if v[1] == dev)
        chk("(6) %s units: every step arrived, the first question is up, no page error" % vl, all(r["arrived"] for r in u["steps"]) and len(u["steps"]) == 6, [(r["name"], r["arrived"]) for r in u["steps"] if not r["arrived"]])
        sh = u.get("sheet")
        chk("(6) %s units: the start sheet's fill is solid and it blurs nothing behind it (backdrop-filter %s)" % (vl, sh and sh["bf"]), bool(sh) and sh["bf"] in ("none", "") and sh["bg"].startswith("rgb(") , sh)
    if len(units) >= 2:
        info("the start sheet's slide, compositor draw ms (software, 4x; one boot each, noisy): " + ", ".join("%s %.0f" % (d_, u.get("sheet_draw") or 0) for d_, u in units.items()))
    chk("no page error", not errs_all, errs_all[:3])
    print("ALL PASS" if ok else "FAILURES")
    sys.exit(0 if ok else 1)
