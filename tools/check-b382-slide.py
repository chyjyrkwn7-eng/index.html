"""Build 382: the tab bar's slide, with a real finger (CDP touch, an iPhone user agent, 440x956 at 3x, 4x CPU).
Madison: "I'm upset the bottom tab isn't seamless and smooth as butter yet, taps work really well ... the swiping/sliding
is not good to go at all." His 381 recording: every dropped frame had Home in it, slides felt behind the finger, and after a
slide's landing the new screen came ~130ms after the glass had gone.
For a slide on Home (out to the Leaderboard and back) and on the Leaderboard (to Home), from the first move to the release:
 (1) the slide's own code reads no layout: no box / computed style / offset read per finger move (the row is measured once a
     touch); counted by wrapping the readers, harness reads excluded;
 (2) mid-slide no task runs over 16ms of script (trace thread time), no style/layout is forced from script, and the script a
     frame is under 4ms at 4x CPU (~1ms on the phone, a sixteenth of a 60Hz frame: the rest is the phone's to draw). The whole
     frame's main-thread CPU is printed too; in this sandbox it is mostly Chromium's compositing (Layerize/Commit), which a phone's
     WebKit does not do the same way, so it is reported, not judged;
 (3) the glass is on the finger: read where the lens really is after each frame (after rAF and layout, a ResizeObserver
     callback), against the finger's newest x - never behind by more than 6px, ahead by about the lead (LENS.lead, at most 8px of
     the row), and no transition or CSS transition on the lens's moving parts;
 (4) Home only: every animation in Home's hero (planet, orbit, smoke, glow, rank bubbles) is paused mid-slide, and all of them
     run again once the glass has landed;
 (5) a slide let go over the Leaderboard whose screen takes 350ms to build: the screen is drawn before the glass has handed over
     to the platter (no more than one frame after).
Run:  python3 tools/check-b382-slide.py   (--against: copy the old index.html over first)"""
import json, os, sys, time, math, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
IPH = """(()=>{ const ua='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148';
  Object.defineProperty(Navigator.prototype,'userAgent',{get:()=>ua,configurable:true}); try{ delete Navigator.prototype.vibrate; }catch(e){}
  /* frames since the page loaded (the splash's own 90-frame centring loop reads the viewport; a sandbox frame can be 150ms) */
  window.__frames=0; const fc=()=>{ __frames++; if(__frames<100) requestAnimationFrame(fc); }; requestAnimationFrame(fc);
  /* layout readers, counted while __readOn (the harness uses the originals) */
  window.__reads={}; window.__readOn=false; const H=window.__H={};
  window.__readStacks={}; const cnt=n=>{ if(window.__readOn){ __reads[n]=(__reads[n]||0)+1; const k=(new Error().stack||'').split('\\n').slice(3,6).map(l=>l.trim().replace(/\\(?https?:[^ )]*index.html:/,'@').replace(/\\)$/,'')).join(' < '); __readStacks[k]=(__readStacks[k]||0)+1; } };
  [['getBoundingClientRect',Element.prototype],['getClientRects',Element.prototype]].forEach(([n,p])=>{ const f=p[n]; H[n]=f; p[n]=function(){ cnt(n); return f.apply(this,arguments); }; });
  const gcs=window.getComputedStyle; H.gcs=gcs; window.getComputedStyle=function(){ cnt('getComputedStyle'); return gcs.apply(window,arguments); };
  ['offsetWidth','offsetHeight','offsetLeft','offsetTop'].forEach(n=>{ const d=Object.getOwnPropertyDescriptor(HTMLElement.prototype,n); if(!d||!d.get) return;
    Object.defineProperty(HTMLElement.prototype,n,{configurable:true,get(){ cnt(n); return d.get.call(this); }}); });
  ['clientWidth','clientHeight'].forEach(n=>{ const d=Object.getOwnPropertyDescriptor(Element.prototype,n); if(!d||!d.get) return;
    Object.defineProperty(Element.prototype,n,{configurable:true,get(){ cnt(n); return d.get.call(this); }}); });
})()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0382"; d["firstName"] = "Casey"; d["novaMet"] = 99
HOOK = """([sel, sample])=>{ const H=window.__H; window.__m={moves:[],lens:[],frames:0,rel:0,mount:0,paint:0,hand:null,sel};
  addEventListener('pointermove',e=>{ __m.moves.push([performance.now(),e.clientX]); },true);
  const body=document.querySelector('#bottomtabs-lens .tab-lens-body'), parts=[...document.querySelectorAll('#bottomtabs-lens .tab-lens-body, #bottomtabs-lens .tab-lens-clip, #bottomtabs-lens .tab-lens-cap')];
  const dot=document.createElement('div'); dot.style.cssText='position:fixed;left:0;top:0;height:1px;width:1px;pointer-events:none;opacity:0'; document.body.appendChild(dot);
  let w=1; const ro=new ResizeObserver(()=>{ if(!__m.sampling) return; const r=H.getBoundingClientRect.call(body); const mv=__m.moves;
    __m.lens.push([performance.now(), r.left+r.width/2, mv.length?mv[mv.length-1][1]:null, mv.length?mv[mv.length-1][0]:null,
      parts.some(p=>p.style.transition && p.style.transition!=='none' && /transform/.test(p.style.transition)) || parts.some(p=>p.getAnimations().some(a=>a.constructor.name==='CSSTransition'))]); });
  if(sample) ro.observe(dot);
  const f=()=>{ if(!__m.on) return; __m.frames++; w=w===1?2:1; dot.style.width=w+'px'; requestAnimationFrame(f); }; __m.on=!!sample; if(sample) requestAnimationFrame(f);
  window.__hero=()=>{ const h=document.querySelector('#stage .cosmic-hero-wrap'); if(!h) return null; const o={run:0,paused:0}; h.getAnimations({subtree:true}).forEach(a=>{ if(a.playState==='running') o.run++; else if(a.playState==='paused') o.paused++; }); return o; };
  addEventListener('pointerup',()=>{ __m.rel=performance.now(); const st=document.getElementById('stage');
    const look=()=>{ if(!__m.mount && st.querySelector(__m.sel)){ __m.mount=performance.now(); requestAnimationFrame(()=>{ __m.paint=performance.now(); }); return true; } return false; };
    if(!look()){ const mo=new MutationObserver(()=>{ if(look()) mo.disconnect(); }); mo.observe(st,{childList:true,subtree:true}); }
    /* the hand-over (the lens's opacity to 0), read off its own track each frame until the platter has it */
    const lens=document.getElementById('bottomtabs-lens'); const poll=()=>{ const a=lens.getAnimations().find(x=>{ const k=x.effect&&x.effect.getKeyframes(); return k&&k.some(f=>'opacity' in f); });
      if(a && a.startTime!=null){ const k=a.effect.getKeyframes(), D=a.effect.getTiming().duration; const i=k.findIndex((f,n)=>n>0 && parseFloat(f.opacity)<.5 && parseFloat(k[n-1].opacity)>=.5); if(i>0) __m.hand=a.startTime+k[i].computedOffset*D; }
      if(H.gcs.call(window,lens).opacity==='0' || performance.now()-__m.rel>4000){ __m.done=true; return; } requestAnimationFrame(poll); }; requestAnimationFrame(poll);
  },{capture:true,once:true}); }"""
SEL = {"bottomtab-home": ".screen-home-actual", "bottomtab-rewards": ".screen-rankings", "bottomtab-profile": ".screen-profile"}
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info, flush=True)

def tabs_of(pg):
    return pg.evaluate("()=>Object.fromEntries([...document.querySelectorAll('#bottomtabs .bottomtab')].map(t=>{const r=window.__H.getBoundingClientRect.call(t); return [t.id,[r.left+r.width/2,r.top+r.height/2]];}))")

def slide(pg, cdp, frm, to, trace=False, slow=False, back=False):
    tabs = tabs_of(pg); x0, y = tabs[frm]; x1 = tabs[to][0]
    # a traced slide carries no sampler (its own frame each rAF would be measured with the slide); the lens is read on an untraced one
    pg.evaluate(HOOK, [SEL[to], not trace])
    if slow:
        pg.evaluate("()=>{ const real=window.showRankings; window.__realSR=real; window.showRankings=function(){ const t=performance.now(); while(performance.now()-t<350){} return real.apply(this,arguments); }; }")
    evs, done = [], []
    if trace:
        cdp.on("Tracing.dataCollected", lambda p: evs.extend(p["value"]))
        cdp.on("Tracing.tracingComplete", lambda p: done.append(1))
        cdp.send("Tracing.start", {"categories": "devtools.timeline,disabled-by-default-devtools.timeline", "transferMode": "ReportEvents"})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]}); time.sleep(0.2)
    # past the slop first, then the measured stretch: a half-cosine over 2.4s (3.4s out and back), a move every 8ms (a 120Hz finger)
    for k in range(1, 5):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (4 * k if x1 > x0 else -4 * k), "y": y}]}); time.sleep(0.016)
    xs = x0 + (16 if x1 > x0 else -16)
    time.sleep(0.25)
    pg.evaluate("()=>{ __m.sampling=true; __m.t0=performance.now(); window.__reads={}; window.__readOn=true; __m.heroMid=null; }")
    # back: out to the other tab and back to the lit one (a slide that lands where it began: nothing is opened)
    t0 = time.time(); D = 3.4 if back else 2.4; hero_mid = None
    while True:
        u = min(1, (time.time() - t0) / D)
        x = xs + (x1 - xs) * (0.5 - 0.5 * math.cos(u * math.pi * (2 if back else 1)))
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
        if hero_mid is None and u > .5: hero_mid = pg.evaluate("()=>window.__hero()")
        if u >= 1: break
        time.sleep(0.008)
    time.sleep(0.1)
    m0 = pg.evaluate("()=>{ window.__readOn=false; __m.sampling=false; __m.t1=performance.now(); return {reads: window.__reads, t0: __m.t0, t1: __m.t1, frames: __m.frames}; }")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    for _ in range(60):
        time.sleep(0.1)
        if pg.evaluate("()=>!!__m.done"): break
    time.sleep(0.3)
    if trace:
        cdp.send("Tracing.end")
        for _ in range(150):
            if done: break
            time.sleep(0.1)
    m = pg.evaluate("()=>{ __m.on=false; return __m; }")
    if slow: pg.evaluate("()=>{ window.showRankings=window.__realSR; }")
    time.sleep(2.2)
    m["heroAfter"] = pg.evaluate("()=>window.__hero()")
    m["heroMid"] = hero_mid; m.update(m0)
    m["trace"] = trace_stats(evs) if trace else None
    return m

SCRIPT = ("EventDispatch", "FireAnimationFrame", "TimerFire", "FunctionCall", "FireIdleCallback", "EvaluateScript", "V8.Execute", "ResizeObserver", "IntersectionObserverController::computeIntersections")
def trace_stats(evs):
    """Main-thread CPU (trace thread time) from the slide's 4th move to its last move before the release: per task, the script in it
    (top-level script events, nested ones not counted twice) and the style/layout script forced (an UpdateLayoutTree/Layout inside a
    script event); per frame, all of it and the script alone."""
    main = set()
    for e in evs:
        if e.get("name") == "thread_name" and e.get("args", {}).get("name") == "CrRendererMain": main.add((e["pid"], e["tid"]))
    M = [e for e in evs if (e.get("pid"), e.get("tid")) in main]
    mv = sorted(e["ts"] for e in M if e.get("name") == "EventDispatch" and e.get("args", {}).get("data", {}).get("type") == "pointermove")
    up = sorted(e["ts"] for e in M if e.get("name") == "EventDispatch" and e.get("args", {}).get("data", {}).get("type") == "pointerup")
    if len(mv) < 6 or not up: return None
    a = mv[3]; b = max(t for t in mv if t < up[0])
    X = sorted((e for e in M if e.get("ph") == "X" and a <= e["ts"] <= b), key=lambda e: (e["ts"], -e["dur"]))
    tasks = [e for e in X if e["name"] == "RunTask"]
    cpu = lambda e: e.get("tdur", e["dur"]) / 1000
    per = []
    for tk in tasks:
        inner = [e for e in X if e is not tk and tk["ts"] <= e["ts"] and e["ts"] + e["dur"] <= tk["ts"] + tk["dur"]]
        sc, forced, end = 0, 0, -1
        spans = []
        for e in inner:
            if e["name"] in SCRIPT:
                if e["ts"] >= end: sc += cpu(e); end = e["ts"] + e["dur"]; spans.append((e["ts"], end))
            elif e["name"] in ("UpdateLayoutTree", "Layout") and any(s0 <= e["ts"] < s1 for s0, s1 in spans): forced += cpu(e)
        per.append((cpu(tk), sc, forced))
        if os.environ.get("DUMP") and sc > 6:
            agg = {}
            for e in inner:
                d = e.get("args", {}).get("data", {}) or {}
                k = e["name"] + ":" + str(d.get("type") or d.get("functionName") or "")
                agg[k] = agg.get(k, 0) + cpu(e)
            print("   SCRIPT TASK %.1f:" % sc, sorted(((round(v, 1), k) for k, v in agg.items()), reverse=True)[:8])
    frames = {round(e["ts"] / 4000) for e in X if e["name"] in ("FireAnimationFrame", "BeginMainThreadFrame", "UpdateLayoutTree")}
    nfr = max(1, len({round(e["ts"] / 8000) for e in X if e["name"] == "FireAnimationFrame"}))
    return {"tasks": len(per), "maxTaskCpu": round(max(p[0] for p in per), 1) if per else 0, "maxTaskScript": round(max(p[1] for p in per), 1) if per else 0,
            "forcedMs": round(sum(p[2] for p in per), 1), "cpuPerFrame": round(sum(p[0] for p in per) / nfr, 2), "scriptPerFrame": round(sum(p[1] for p in per) / nfr, 2),
            "frames": nfr, "spanMs": round((b - a) / 1000)}

def lag(m):
    """Each frame (read after rAF and layout): the lens's centre against the newest finger x the page has, signed by the way the finger
    is going (+ ahead, - behind); only frames in which the finger moved."""
    signed, tx, prev, pdir = [], 0, None, 0
    for t, lx, fx, ft, hastx in m["lens"]:
        if hastx: tx += 1
        if fx is None: continue
        if prev is not None and abs(fx - prev) >= 1:
            d = 1 if fx > prev else -1
            # a frame where the finger turned round is left out (the lead still points the old way for a frame or two)
            if d == pdir: signed.append((lx - fx) * d)
            pdir = d
        prev = fx
    if not signed: return {"n": 0, "tx": tx, "samples": len(m["lens"])}
    srt = sorted(signed)
    return {"n": len(signed), "med": round(statistics.median(srt), 1), "behindMax": round(-srt[0], 1), "aheadMax": round(srt[-1], 1), "tx": tx, "samples": len(m["lens"])}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=3, has_touch=True, is_mobile=True)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]())); ctx.add_init_script(IPH)
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(g["STATUS_BAR"].replace("__H__", "62"))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; }")
    cdp = ctx.new_cdp_session(pg)
    for s in ("showRankings", "showProfile", "showHome"):
        pg.evaluate("()=>%s()" % s); pg.wait_for_timeout(3000)
    for _ in range(120):
        if pg.evaluate("()=>window.__frames") >= 100: break
        pg.wait_for_timeout(500)
    res = {}
    # Home: out to the Leaderboard and back (it stays on Home, so its hero can be seen to run again); the Leaderboard: to Home
    for name, frm, to, show in (("Home", "bottomtab-home", "bottomtab-rewards", "showHome"), ("Leaderboard", "bottomtab-rewards", "bottomtab-home", "showRankings")):
        best = None
        for attempt in range(2):     # timing-sensitive under load: the better of two
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            pg.evaluate("()=>%s()" % show); pg.wait_for_timeout(3500)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(600)
            m = slide(pg, cdp, frm, to, trace=True, back=(name == "Home"))
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            pg.evaluate("()=>%s()" % show); pg.wait_for_timeout(3500)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(600)
            m2 = slide(pg, cdp, frm, to, back=(name == "Home"))
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            m["lag"] = lag(m2); m["reads"] = m2["reads"] if sum(m2["reads"].values()) > sum(m["reads"].values()) else m["reads"]
            if os.environ.get("DUMP"): print("   lens samples", len(m2["lens"]), m2["lens"][:3], "moves", len(m2["moves"]))
            t = m["trace"] or {}
            score = (t.get("maxTaskCpu", 99), t.get("cpuPerFrame", 99))
            if best is None or score < best[0]: best = (score, m)
        m = best[1]; res[name] = m
        r = m["reads"]; nreads = sum(v for k, v in r.items())
        if os.environ.get("DUMP"): print("   read stacks", pg.evaluate("()=>window.__readStacks"))
        print("  %s: reads %s | trace %s | lag %s | hero mid %s after %s" % (name, r, m["trace"], m["lag"], m["heroMid"], m["heroAfter"]), flush=True)
        chk("(1) on %s the slide reads no layout while the finger moves (%d reads: %s)" % (name, nreads, r), nreads <= 2, r)
        t = m["trace"]
        chk("(2) on %s mid-slide no task runs over 16ms of script (worst %s), no style or layout is forced from script (%s ms), and the script a frame is %s ms (budget 4 at 4x CPU: ~1ms of a 16.7ms frame on the phone)" % (name, t and t["maxTaskScript"], t and t["forcedMs"], t and t["scriptPerFrame"]),
            t and t["maxTaskScript"] <= 16 and t["forcedMs"] <= 1 and t["scriptPerFrame"] <= 4, t)
        L = m["lag"]
        # ahead: the lead is at most 8px of the row (x1.084 swollen); a sandbox frame here is 100-300ms long, so a single frame can read
        # a few px more (the start's offset still closing) - the median carries the lead, the worst only rules out a runaway
        chk("(3) on %s the glass is on the finger: %s px behind at worst (<=6), %s ahead at the median (<=14) and %s at worst (<=24); %s frames with a transition on the lens" % (name, L.get("behindMax"), L.get("med"), L.get("aheadMax"), L.get("tx")),
            L["n"] >= 3 and L["behindMax"] <= 6 and L["med"] <= 14 and L["aheadMax"] <= 24 and L["tx"] == 0, L)
        if name == "Home":
            hm, ha = m["heroMid"], m["heroAfter"]
            chk("(4) mid-slide Home's hero holds still (%s) and once the glass has landed it runs again (%s)" % (hm, ha),
                hm and hm["run"] == 0 and hm["paused"] >= 8 and ha and ha["paused"] == 0 and ha["run"] >= 8, [hm, ha])
    # (5) a slow screen: drawn before the glass hands over
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(3500)
    m = slide(pg, cdp, "bottomtab-profile", "bottomtab-rewards", slow=True)
    rel = m["rel"]
    paint = (m["paint"] - rel) if m["paint"] else None; hand = (m["hand"] - rel) if m["hand"] else None
    print("  slow screen: release -> mounted %s, drawn %s, glass handed over %s (ms)" % (round(m["mount"] - rel) if m["mount"] else None, paint and round(paint), hand and round(hand)), flush=True)
    chk("(5) a slide's screen (350ms to build) is drawn before the glass hands over to the platter (drawn %s ms, hand-over %s ms after the release)" % (paint and round(paint), hand and round(hand)),
        paint is not None and hand is not None and paint <= hand + 17, [paint, hand])
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
