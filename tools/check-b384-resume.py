#!/usr/bin/env python3
"""384.27: COMING BACK TO THE APP - Home's planet system (the hero sphere, its flare bubbles and the loops that move them).

Madison (iPhone, installed): "When leaving the app and coming back, the planet system lags badly still."

What the page does on the way back is measured here, by SHAPE, on the page itself (nothing typed as a label, no wall-clock
threshold that a busy machine could break): the page is hidden, left for 3s, shown again (pagehide persisted / visibilitychange /
pageshow / focus, the CPU slowed 4x by CDP; --freeze also freezes the page with Page.setWebLifecycleState for the 3s, which Chromium
pays for with a stall of its own - a 2.5s frame on a page the app has no hand in - so it is not the default), and for the next ~6s every animation that is restarted, every big image decoded and every
frame is read. Chromium cannot say what iOS does with a page as it returns (it drops graphics memory, decodes again, starts
accelerated animations again); what it CAN say is what the page itself asks for, and how much of it lands in the same frame:

 (1) ONE HERD, NOT ONE FRAME: the most animations the page restarts in any single frame after the return (a paused loop played, a
     running loop's currentTime written, an animation cancelled or made) is at most a quarter of the animations on the page.
     (origin/main plays all 41 of Home's loops in one frame.)
 (2) ...and it is not done again: after the first 1.5s, running loops are not written to again except for a tenth of them at most.
     (origin/main writes currentTime on 39 of 41 loops, 2.5s after every return, each already within 2ms of where it was put.)
 (3) THE SHEETS COME BACK ONE AT A TIME: with sheets the app had let go on the way out waiting to be decoded again (eight, ~0.55MP each,
     as a phone that has been on the Leaderboard has up to 14), no 400ms window holds more than two big image decodes (>= 0.3MP) the
     page starts, and none starts before the page has had 1.5s of frames. (origin/main starts all of them 1.2s after the return.)
 (4) NOTHING MOVES RELATIVE TO ANYTHING ELSE: every loop's pose, minus the reference loop's, is what it was when the page was hidden
     (within one 24fps step, 45ms, and half a frame of this run's settled frames) - letting them go in turns must not put one loop ahead of another - and every loop that was running
     is running again within 2.5s of the return.
 (5) A HIDE WHILE THE LOOPS ARE STILL BEING LET GO loses none of them: hidden again two frames after a return, shown again, every
     loop is running within 2.5s (the ones still waiting their turn are kept for the next return).
 (6) THE PHONE SAYS HOW IT WENT: the return's line in the resume log (class26e.resumelog, which "Send tab timings" carries) ends with the
     frames drawn in the 3s after it, the worst gap between two and how many were over 50ms (" fr<n>/w<ms>/s<n>"). (None on origin/main.)
 (7) NOT WORSE THAN A SETTLED HOME: against the same Home measured settled in the same run at the same CPU slowdown, the 2s after the
     return has no more than twice the frames over 50ms the settled 2s had (plus 8: the sandbox is shared and these are wall-clock
     numbers) and its longest task is under three times the settled one plus 250ms. Read off the page, printed either way.
 (8) REDUCE MOTION: with it on the planet system has no loops, and a return starts none and throws nothing.
 (9) no page error.
 (10) THE PAINT-MODE WATCH KEEPS CLEAR OF A RETURN: loopsWatchTick (frames counted for 1.5s; two slow counts in a row switch the loops to their fallback for the build) does not start inside 9s of a return,
     while it does start on the settled Home in the same run. (origin/main: it starts.)

Phone = iPhone 17 Pro Max installed 440x956 at 3x, tablet = iPad Pro 11" 834x1194 at 2x; both classes (the academy's Home and Fire
Code's), both of which have the planet system, with all seven bubbles on their moving sheets before the page is put away.

  python3 tools/check-b384-resume.py [--quick] [--only academy|ifc|phone|tablet|rm] [--against REV|DIR|index.html] [--cpu 4]

On origin/main (384.26) it fails (1), (2), (3), (6), (10); (4), (5), (7), (8), (9) pass there (they hold the new behaviour to what it must keep)."""
import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
args = sys.argv[1:]
def arg(n, d=None):
    return args[args.index(n) + 1] if n in args else d
ONLY = arg("--only"); QUICK = "--quick" in args; CPU = float(arg("--cpu", 4)); FREEZE = "--freeze" in args
AGAINST = None
if "--against" in args:
    a = arg("--against")
    if os.path.isfile(a): AGAINST = open(a, encoding="utf-8").read()
    elif os.path.isfile(os.path.join(a, "index.html")): AGAINST = open(os.path.join(a, "index.html"), encoding="utf-8").read()
    else: AGAINST = subprocess.check_output(["git", "-C", ROOT, "show", a + ":index.html"]).decode("utf-8")
def body_for(ins):
    if AGAINST is None: return g["patched"](ins)
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
def seed(pid, ifc):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = pid; d["firstName"] = "Casey"; d["novaMet"] = 99
    if ifc: d["classes"] = ["academy", "ifc"]; d["seenClassTip"] = True
    return d
def init_for(ifc):
    S = json.dumps(json.dumps(seed("pubresume0384", ifc)))
    base = ("(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; try{ localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.synccode','TEST-3842');"
            "['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
            "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.penal256578.seen','1');") % S
    if ifc:
        base += ("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
                 "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
                 "localStorage.setItem('class26e.ifc.drill.v1',%s);") % S
    return base + "}catch(e){} })()"
# the page's hidden state is the test's to set (the browser's own is "visible" throughout)
VIS = """(()=>{ let hid=false; try{ Object.defineProperty(Document.prototype,'hidden',{get(){return hid;},configurable:true});
  Object.defineProperty(Document.prototype,'visibilityState',{get(){return hid?'hidden':'visible';},configurable:true}); }catch(e){}
  window.__setHidden=v=>{ hid=v; document.dispatchEvent(new Event('visibilitychange')); }; })()"""
# what the page asks of the animations, the images and the frames. Nothing here reads layout or style; it only counts.
INSTR = """(()=>{
 const M = window.__M = { RT:0, ev:[], fr:[], lt:[], frame:0 };
 const rel = () => performance.now() - M.RT;
 const log = (k, d) => { if(M.RT) M.ev.push({ t: Math.round(rel()), f: M.frame, k, d }); };
 const ra = window.requestAnimationFrame;
 (function f(t){ M.frame++; M.fr.push(t); if(M.fr.length > 4000) M.fr.shift(); ra.call(window, f); })(performance.now());
 try{ new PerformanceObserver(l => l.getEntries().forEach(e => M.lt.push([e.startTime, e.duration]))).observe({ type:'longtask' }); }catch(e){}
 const P = Animation.prototype, ct = Object.getOwnPropertyDescriptor(P, 'currentTime');
 const nm = a => a.animationName || (a.effect && a.effect.target && a.effect.target.className && (a.effect.target.className.baseVal || a.effect.target.className)) || '?';
 Object.defineProperty(P, 'currentTime', { get(){ return ct.get.call(this); }, set(v){ log(this.playState === 'running' ? 'write-running' : 'write-other', nm(this)); return ct.set.call(this, v); }, configurable:true });
 const st = Object.getOwnPropertyDescriptor(P, 'startTime');
 if(st) Object.defineProperty(P, 'startTime', { get(){ return st.get.call(this); }, set(v){ if(this.playState === 'paused') log('resume', nm(this)); else log('write-running', nm(this)); return st.set.call(this, v); }, configurable:true });
 const op = P.play; P.play = function(){ if(this.playState === 'paused') log('resume', nm(this)); return op.apply(this, arguments); };
 const oc = P.cancel; P.cancel = function(){ log('cancel', nm(this)); return oc.apply(this, arguments); };
 const oa = Element.prototype.animate; Element.prototype.animate = function(){ log('animate', this.tagName); return oa.apply(this, arguments); };
 const od = HTMLImageElement.prototype.decode;
 HTMLImageElement.prototype.decode = function(){ const e = { t: Math.round(rel()), f: M.frame, k:'decode', d:0 }; if(M.RT) M.ev.push(e); const im = this; const p = od.apply(this, arguments); p.then(() => { e.d = (im.naturalWidth || 0) * (im.naturalHeight || 0); }, () => {}); return p; };
 M.loops = () => document.getAnimations().filter(a => { try{ const t = a.effect.getTiming(); return t.iterations === Infinity && Number(t.duration) > 0; }catch(e){ return false; } });
 M.poses = () => M.loops().map(a => [nm(a), a.playState, a.currentTime, !!a.pending]);
})()"""
SHEETS = """async (N) => { const out = [];
  for(let i = 0; i < N; i++){
    const c = document.createElement('canvas'); c.width = c.height = 744; const x = c.getContext('2d'); const d = x.createImageData(744, 744);
    for(let j = 0; j < d.data.length; j += 4){ d.data[j] = (Math.random() * 255) | 0; d.data[j+1] = (Math.random() * 255) | 0; d.data[j+2] = (Math.random() * 255) | 0; d.data[j+3] = 255; }
    x.putImageData(d, 0, 0);
    const blob = await new Promise(r => c.toBlob(r, 'image/png'));
    const sp = { url: URL.createObjectURL(blob), px: 62, n: 144, cols: 12, rows: 12, pre: null };
    charPreList.push(sp); out.push(sp.url);
  }
  return out.length; }"""
def scenario(br, label, ifc, w, h, dpr, rm=False):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA,
                         reduced_motion="reduce" if rm else "no-preference")
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    ctx.add_init_script(VIS); ctx.add_init_script(INSTR)
    pg = ctx.new_page(); body = body_for((62, 0, 34, 0)) if w < 700 else body_for((24, 0, 20, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.add_init_script(init_for(ifc))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(4000)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }")
        pg.wait_for_timeout(300)
    pg.evaluate("()=>{ try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} }")
    if rm:
        pg.evaluate("()=>{ theme.reduceMotion = true; try{ applyTheme(); }catch(e){} homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
    n = [0, 0]; t0 = time.time()
    # the flares move on their recorded sheets (recorded here, at 1x, while the page is up: a minute or two on a shared machine)
    while not rm and time.time() - t0 < 240:
        pg.wait_for_timeout(3000)
        n = pg.evaluate("()=>[document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank').length, document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank > .cosmic-rank-anim').length]")
        if n[0] and n[1] >= n[0]: break
    pg.wait_for_timeout(3000)
    cdp = ctx.new_cdp_session(pg)
    seeded = pg.evaluate(SHEETS, 8)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": CPU})
    # a settled Home, 2s, at the same slowdown
    pg.evaluate("()=>{ window.__B0 = performance.now(); }"); pg.wait_for_timeout(2200)
    base = pg.evaluate("()=>{ const f = __M.fr.filter(t => t >= __B0 && t <= __B0 + 2000); const d = f.slice(1).map((t, i) => t - f[i]); const lt = __M.lt.filter(x => x[0] >= __B0 && x[0] <= __B0 + 2000).map(x => x[1]);"
                       " const so = d.slice().sort((a, b) => a - b); return { frames: f.length, slow: d.filter(x => x > 50).length, longest: Math.max(0, ...lt), med: so.length ? so[so.length >> 1] : 17 }; }")
    # the loops' paint-mode watch (loopsWatchTick) counts frames for 1.5s when it runs: it must be ABLE to run on this settled Home (or (10) measures nothing)
    watch_settled = pg.evaluate("()=>{ try{ loopsWatch.touchAt = -1e9; loopsWatchTick(); return loopsWatch.busy; }catch(e){ return 'err ' + e; } }")
    pg.wait_for_timeout(1900)
    n_loops = pg.evaluate("()=>__M.loops().length")
    n_anims = pg.evaluate("()=>document.getAnimations().length")
    before = pg.evaluate("()=>__M.poses().filter(p => p[1] === 'running').length")
    # hide, away 3s, back
    def hide():
        pg.evaluate("()=>{ __setHidden(true); window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true})); }")
    def show():
        pg.evaluate("()=>{ window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})); __setHidden(false); window.dispatchEvent(new Event('focus')); }")
    hide(); pg.wait_for_timeout(300)
    P = pg.evaluate("()=>__M.poses()")
    if FREEZE:
        cdp.send("Page.setWebLifecycleState", {"state": "frozen"}); time.sleep(3); cdp.send("Page.setWebLifecycleState", {"state": "active"})
    else:
        pg.wait_for_timeout(3000)
    cdp.send("Performance.enable"); met0 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    pg.evaluate("()=>{ window.__M.RT = performance.now(); }"); show()
    # the poses once every loop that ran is running again (the herd, if there is one, is long done); at most 9s
    t1 = time.time(); Q = None
    while time.time() - t1 < 9:
        pg.wait_for_timeout(300)
        Q = pg.evaluate("()=>__M.poses()")
        # (an animation just played is 'running' but still pending: its time is held until the next frame starts it, so it is read after that)
        if len([q for q in Q if q[1] == 'running']) >= before and not [q for q in Q if q[3]]: break
    pg.wait_for_timeout(max(0, 6500 - int((time.time() - t1) * 1000)))
    met1 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    cost = {k: round(met1.get(k, 0) - met0.get(k, 0), 3) for k in ("ScriptDuration", "RecalcStyleDuration", "LayoutDuration", "TaskDuration", "RecalcStyleCount", "LayoutCount")}
    r = pg.evaluate("()=>{ const M = __M; const fr = M.fr.filter(t => t >= M.RT && t <= M.RT + 2000); const d = fr.slice(1).map((t, i) => t - fr[i]);"
                    " const lt = M.lt.filter(x => x[0] >= M.RT && x[0] <= M.RT + 2000).map(x => x[1]);"
                    " return { ev: M.ev, frames: fr.length, slow: d.filter(x => x > 50).length, longest: Math.max(0, ...lt), log: JSON.parse(localStorage.getItem('class26e.resumelog') || '[]'),"
                    " running: M.poses().filter(p => p[1] === 'running').length, loops: M.loops().length }; }")
    # (5) hidden again two frames after a return, shown again
    hide(); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ window.__M.RT = performance.now(); }")
    # back, and hidden again in the frame after the first loop is let go (the rest still waiting their turn, if they are made to wait)
    pg.evaluate("""()=>new Promise(res => { window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})); __setHidden(false); window.dispatchEvent(new Event('focus'));
      let n = 0; const t = () => { if(__M.ev.some(e => e.k === 'resume') || ++n > 400){ __setHidden(true); window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true})); res(); } else requestAnimationFrame(t); }; t(); })""")
    pg.wait_for_timeout(400); show()
    t1 = time.time(); again = None
    while time.time() - t1 < 9:
        pg.wait_for_timeout(300)
        again = pg.evaluate("()=>({ running: __M.poses().filter(p => p[1] === 'running').length, loops: __M.loops().length })")
        if again["running"] >= before: break
    watch_after = pg.evaluate("()=>{ try{ loopsWatch.touchAt = -1e9; loopsWatchTick(); return loopsWatch.busy; }catch(e){ return 'err ' + e; } }")
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    ctx.close()
    return dict(watch_settled=watch_settled, watch_after=watch_after, cost=cost, label=label, sheets=n, seeded=seeded, base=base, n_loops=n_loops, n_anims=n_anims, before=before, P=P, Q=Q, r=r, again=again, errs=errs)
def judge(s):
    L = s["label"]; r = s["r"]; ev = r["ev"]; na = max(1, s["n_anims"]); rm = "rm" in L
    restarts = [e for e in ev if e["k"] in ("resume", "write-running", "cancel", "animate")]
    per = {}
    for e in restarts: per[e["f"]] = per.get(e["f"], 0) + 1
    worst = max(per.values() or [0])
    allow = max(1, -(-na // 4))
    print("   [%s] the page's own account of the ~6.5s after the return (seconds of main-thread time, counts): %s" % (L, s["cost"]))
    print("   [%s] animations %d (loops %d, running before %d); sheets %s; restarts by frame: %s" % (L, na, s["n_loops"], s["before"], s["sheets"], sorted(per.items())[:12]))
    if rm:
        # (the daily question's ring is a ::after, which the app's [data-reduce-motion] * rule does not reach: it is not the planet system and is left out)
        own = [p for p in s["P"] if p[0] != "daily-ready"]; restarts = [e for e in restarts if e["d"] != "daily-ready"]
        chk("(8) %s: reduce motion: the planet system has no loops (%d), none started on the return (%d), no error" % (L, len(own), len(restarts)),
            not own and not restarts and not s["errs"], [own[:5], restarts[:5], s["errs"]])
        return
    chk("(1) %s: no more than a quarter of the animations (%d of %d) restart in any one frame after the return (most: %d)" % (L, allow, na, worst), worst <= allow, sorted(per.items()))
    late = [e for e in ev if e["k"] == "write-running" and e["t"] > 1500]
    chk("(2) %s: after 1.5s running loops are not written to again (%d writes; allowed %d)" % (L, len(late), max(1, na // 10)), len(late) <= max(1, na // 10), [(e["t"], e["d"]) for e in late[:6]])
    big = sorted(e["t"] for e in ev if e["k"] == "decode" and e["d"] >= 300000)
    herd = max([sum(1 for u in big if t <= u < t + 400) for t in big] or [0])
    chk("(3) %s: the let-go sheets are decoded again in turns (%d big decodes started; most in 400ms: %d; first at %s ms)" % (L, len(big), herd, big[0] if big else None),
        s["seeded"] >= 6 and herd <= 2 and (not big or big[0] >= 1500), [s["seeded"], big])
    # (4) poses relative to the reference loop (the one named cosmic-orbit-spin with the longest period: the first)
    P, Q = s["P"], s["Q"]
    bad = []; dev = 0
    # one 24fps step of the sheets (42ms) plus a frame and a half as THIS run's settled Home draws them (the CPU is slowed 4x and the
    # machine is shared: a loop let go a frame later is a frame behind, which a phone at 60Hz makes 17ms and this makes ~60)
    tol = 45 + 0.5 * s["base"]["med"]
    if len(P) == len(Q) and P:
        ref = next((i for i, p in enumerate(P) if p[0] == "cosmic-orbit-spin"), 0)
        for i, (p, q) in enumerate(zip(P, Q)):
            if p[1] != "paused" or q[1] != "running": continue
            dp = p[2] - P[ref][2]; dq = q[2] - Q[ref][2]
            dev = max(dev, abs(dp - dq))
            if abs(dp - dq) > tol: bad.append((p[0], round(dq - dp)))
    chk("(4) %s: every loop keeps its pose against the reference loop (most off: %dms; allowed %dms) and every one that ran is running again (%d of %d)" % (L, dev, tol, r["running"], s["before"]),
        P and len(P) == len(Q) and not bad and r["running"] >= s["before"], [len(P), len(Q), bad[:8], r["running"], s["before"]])
    chk("(5) %s: hidden again two frames after a return and shown again, all %d loops run (running %d)" % (L, s["again"]["loops"], s["again"]["running"]),
        s["again"]["running"] >= s["before"], s["again"])
    line = (r["log"] or [""])[-1] if r["log"] else ""
    chk("(6) %s: the return's line in the resume log carries the frames of the 3s after it (%r)" % (L, line[-60:]), bool(re.search(r" fr\d+/w\d+/s\d+( q[\d,]+ g[\d,-]+)?$", line)) or any(re.search(r" fr\d+/w\d+/s\d+( q[\d,]+ g[\d,-]+)?$", x) for x in r["log"]), r["log"])
    b = s["base"]
    chk("(7) %s: the 2s after the return: %d frames over 50ms (settled Home %d), longest task %dms (settled %dms)" % (L, r["slow"], b["slow"], r["longest"], b["longest"]),
        r["slow"] <= 2 * b["slow"] + 8 and r["longest"] <= 3 * b["longest"] + 250, [r["slow"], b, r["longest"]])
    chk("(10) %s: the loops' paint-mode watch does not count the frames of a page that is waking up (it can run when settled: %s; started within 2.5s of a return: %s)" % (L, s["watch_settled"], s["watch_after"]),
        # (a device whose Home shows fewer than four loops in view never runs the watch at all - the tablet's: nothing to hold clear of, said so)
        (s["watch_settled"] is False and s["watch_after"] is False) or (s["watch_settled"] is True and s["watch_after"] is False), [s["watch_settled"], s["watch_after"]])
    chk("(9) %s: no page error" % L, not s["errs"], s["errs"][:3])
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    plan = [("phone academy", False, 440, 956, 3), ("phone ifc", True, 440, 956, 3), ("tablet academy", False, 834, 1194, 2), ("tablet ifc", True, 834, 1194, 2), ("phone academy rm", False, 440, 956, 3)]
    if QUICK: plan = [plan[0], plan[4]]
    if ONLY: plan = [plan[4]] if ONLY == "rm" else [p for p in plan if ONLY in p[0].split() and not p[0].endswith("rm")]
    for (label, ifc, w, h, dpr) in plan:
        t = time.time()
        s = scenario(br, label, ifc, w, h, dpr, rm=label.endswith("rm"))
        judge(s); print("   (%s took %ds)" % (label, time.time() - t), flush=True)
    br.close()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
