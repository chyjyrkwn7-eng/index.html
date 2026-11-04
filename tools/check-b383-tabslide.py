"""Build 383: the tab bar's slide on the units screen, and a slide's frames on every screen.
Madison: "Again like I said, the tab sliding/swiping function needs to be fixed and smooth with no delay/lag because it's still not
fixed. While in the unit selection screen and using the bottom tab, you can only tab the bottom tab stuff, ensure you can still slide
your finger across it to swipe/select similar to how you can on the main menu and stuff."
As an iPhone (its user agent, real touches through CDP, 440x956 at 3x), check-b382-slide's harness:
 (1) THE UNITS SCREEN (no tab lit): a finger put down on one tab and slid to another - the glass follows the finger (mid-slide it is
     within 24px of it, and it travels at least half the finger's way), and let go there, that tab is lit and its screen is up.
     Two slides: Home -> Leaderboard and Calendar -> Profile.
 (2) A SLIDE ON EACH MAIN SCREEN, at 4x CPU (traced): from the lit tab across the bar to the far tab and let go - it lands (that tab lit,
     its screen up); from the first move to the release no style pass restyles more than 300 elements (the whole page restyled in a
     slide's first frame - 951 to 1637 elements, the slide-hold class on <html>); and no task runs over 50ms of the app's own work
     (script, style and layout; Chromium's own compositing steps are left out as in check-b382-slide - a phone's WebKit does those
     differently). Home, Profile, the Leaderboard and the Calendar; the better of two tries (timing-sensitive under load).
 (3) STEADY: touches that do not come one per frame (pairs 6ms apart, then a 22ms gap - as a phone's come against Safari's 60Hz frames),
     a slide on the Calendar at 1x: read where the glass is after every frame of the steady middle of the slide - no more than 20% of
     the frames leave it standing still or stepping back (a step under a quarter of the finger's own over that frame).
 (4) NO SCREEN IS BUILT UNDER A SLIDE: a tab's screen build that comes due while a finger is sliding (a tap's screen is built 40ms
     after its press; a finger back down and sliding inside that had it built under the glide) - made exact by clicking the
     Leaderboard tab from the page mid-slide, its screen made to take 300ms - is built only once the finger has let go.
Run:  python3 tools/check-b383-tabslide.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, time, math, statistics, re
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "check-b382-slide.py")).read().split("\nwith sync_playwright() as pw:")[0]
g2 = {"__file__": os.path.join(HERE, "check-b382-slide.py"), "__name__": "b383tabslide"}
exec(SRC, g2)
g = g2["g"]
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    def _patched(ins, _o=OLD):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    g["patched"] = _patched
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

SCREEN_OF = {"bottomtab-home": ".screen-home-actual", "bottomtab-rewards": ".screen-rankings",
             "bottomtab-profile": ".screen-profile:not(.screen-stats)", "bottomtab-calendar": ".screen-calendar-tab"}
SHOW = {"home": "showHome()", "profile": "showProfile()", "rewards": "showRankings()", "calendar": "showCalendarTab()",
        "units": "(cfg.mode='drill', showSetup())"}
# the glass after every frame (a ResizeObserver callback runs after rAF and layout), with the newest finger x the page has
SAMPLER = """()=>{ const H=window.__H; const body=document.querySelector('#bottomtabs-lens .tab-lens-body');
  if(window.__s) window.__s.on=false;
  const S=window.__s={ fr:[], mv:[], on:true };
  addEventListener('pointermove', e=>{ if(S.on) S.mv.push([performance.now(), e.clientX]); }, true);
  const dot=document.createElement('div'); dot.style.cssText='position:fixed;left:0;top:0;height:1px;width:1px;pointer-events:none;opacity:0'; document.body.appendChild(dot);
  let w=1; const ro=new ResizeObserver(()=>{ if(!S.on) return; const r=H.getBoundingClientRect.call(body); const mv=S.mv;
    S.fr.push([performance.now(), r.left+r.width/2, mv.length?mv[mv.length-1][1]:null, mv.length]); });
  ro.observe(dot);
  const f=()=>{ if(!S.on){ ro.disconnect(); dot.remove(); return; } w=w===1?2:1; dot.style.width=w+'px'; requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
STATE = """(sel)=>({ lit: [...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(t=>t.id),
  up: !!document.querySelector('#stage ' + sel), screen: (document.querySelector('#stage > .panel')||{}).className || '' })"""

def touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})

def tabs_of(pg):
    return g2["tabs_of"](pg)

def lit_tab(pg):
    l = pg.evaluate("()=>[...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(t=>t.id)")
    return l[0] if l else None

def glide(pg, cdp, x0, x1, y, D, gaps=(0.008,), sample=True):
    """finger down at x0, past the slop, then a half-cosine to x1 over D seconds (moves `gaps` apart, cycled); returns the samples"""
    touch(cdp, "touchStart", x0, y); time.sleep(0.15)
    sgn = 1 if x1 > x0 else -1
    for k in range(1, 5):
        touch(cdp, "touchMove", x0 + sgn * 4 * k, y); time.sleep(0.016)
    xs = x0 + sgn * 16
    time.sleep(0.15)
    if sample: pg.evaluate(SAMPLER)
    t0 = time.time(); i = 0
    while True:
        u = min(1, (time.time() - t0) / D)
        touch(cdp, "touchMove", xs + (x1 - xs) * (0.5 - 0.5 * math.cos(u * math.pi)), y)
        if u >= 1: break
        time.sleep(gaps[i % len(gaps)]); i += 1
    time.sleep(0.05)
    s = pg.evaluate("()=>{ const S=window.__s; if(!S) return null; S.on=false; return {fr:S.fr, mv:S.mv}; }") if sample else None
    return s

def trace_work(evs):
    """From the first pointermove to the pointerup, on the page's main thread: the largest style pass (elements restyled) and, per task,
    the app's own work - top-level script plus style and layout not already inside it (Chromium's Layerize/Commit/Paint left out)."""
    main = set()
    for e in evs:
        if e.get("name") == "thread_name" and e.get("args", {}).get("name") == "CrRendererMain": main.add((e["pid"], e["tid"]))
    M = [e for e in evs if (e.get("pid"), e.get("tid")) in main]
    typ = lambda e: e.get("args", {}).get("data", {}).get("type")
    mv = sorted(e["ts"] for e in M if e.get("name") == "EventDispatch" and typ(e) == "pointermove")
    up = sorted(e["ts"] for e in M if e.get("name") == "EventDispatch" and typ(e) == "pointerup")
    if len(mv) < 6 or not up: return None
    a = mv[0]; b = up[0]
    X = sorted((e for e in M if e.get("ph") == "X" and a <= e["ts"] < b), key=lambda e: (e["ts"], -e["dur"]))
    cpu = lambda e: e.get("tdur", e["dur"]) / 1000
    els = [e.get("args", {}).get("elementCount") or 0 for e in X if e["name"] == "UpdateLayoutTree"]
    worst, worst_at = 0, None
    for tk in (e for e in X if e["name"] == "RunTask"):
        inner = [e for e in X if e is not tk and tk["ts"] <= e["ts"] and e["ts"] + e["dur"] <= tk["ts"] + tk["dur"]]
        w, end = 0, -1
        for e in inner:
            if e["ts"] < end: continue
            if e["name"] in g2["SCRIPT"] or e["name"] in ("UpdateLayoutTree", "Layout"):
                w += cpu(e); end = e["ts"] + e["dur"]
        if w > worst: worst, worst_at = w, round((tk["ts"] - a) / 1000)
    return {"maxEls": max(els) if els else 0, "worstTask": round(worst, 1), "worstAt": worst_at, "moves": len(mv), "spanMs": round((b - a) / 1000)}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=3, has_touch=True, is_mobile=True)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]())); ctx.add_init_script(g2["IPH"])
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0))
    build = re.search(r'const APP_BUILD = "([^"]+)"', body).group(1)
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": build, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(g["STATUS_BAR"].replace("__H__", "62"))
    pg.add_init_script(g2["INIT"] % json.dumps(json.dumps(g2["d"])))
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(g2["url"]); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; }")
    cdp = ctx.new_cdp_session(pg)
    for s in ("showRankings()", "showProfile()", "showCalendarTab()", "showHome()"):
        pg.evaluate("()=>" + s); pg.wait_for_timeout(2500)
    for _ in range(120):
        if pg.evaluate("()=>window.__frames") >= 100: break
        pg.wait_for_timeout(500)
    # a session's first touch wakes the sound (a one-off, not the slide's): done once here, off the bar
    touch(cdp, "touchStart", 220, 300); time.sleep(0.05); touch(cdp, "touchEnd"); pg.wait_for_timeout(1200)

    # ---- (1) the units screen ----
    for frm, to in (("bottomtab-home", "bottomtab-rewards"), ("bottomtab-calendar", "bottomtab-profile")):
        pg.evaluate("()=>" + SHOW["units"]); pg.wait_for_timeout(2500)
        st0 = pg.evaluate(STATE, ".screen-setup")
        tabs = tabs_of(pg); x0, y = tabs[frm]; x1 = tabs[to][0]
        s = glide(pg, cdp, x0, x1, y, 1.2)
        touch(cdp, "touchEnd"); pg.wait_for_timeout(1800)
        st = pg.evaluate(STATE, SCREEN_OF[to])
        fr = [f for f in (s or {}).get("fr", []) if f[2] is not None]
        mid = [abs(f[1] - f[2]) for f in fr[len(fr) // 3: 2 * len(fr) // 3]] if fr else []
        travel = abs(fr[-1][1] - fr[0][1]) if len(fr) > 1 else 0
        ftravel = abs(fr[-1][2] - fr[0][2]) if len(fr) > 1 else 1
        print("  units %s -> %s: before %s | glass-finger mid median %s, glass %.0fpx for the finger's %.0fpx | after %s" % (
            frm, to, st0["lit"], mid and round(statistics.median(mid), 1), travel, ftravel, st), flush=True)
        chk("(1) units screen (no tab lit: %s): the glass follows a finger slid %s -> %s (mid-slide %s px from it, <=24; it went %.0f of the finger's %.0f px)" % (
            st0["lit"] or "none", frm[10:], to[10:], mid and round(statistics.median(mid), 1), travel, ftravel),
            st0["up"] and mid and statistics.median(mid) <= 24 and travel >= ftravel * .5, [st0, mid[:6], travel, ftravel])
        chk("(1) units screen: let go on %s, that tab is lit and its screen is up (%s)" % (to[10:], st), st["lit"] == [to] and st["up"], st)

    # ---- (2) a slide on each main screen, 4x CPU, traced ----
    for name, far in (("home", None), ("profile", None), ("rewards", None), ("calendar", None)):
        best = None
        for attempt in range(2):
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            pg.evaluate("()=>" + SHOW[name]); pg.wait_for_timeout(3500)
            frm = lit_tab(pg)
            tabs = tabs_of(pg)
            order = [k for k, v in sorted(tabs.items(), key=lambda kv: kv[1][0]) if v[0] > 0 and k in SCREEN_OF]
            to = order[-1] if frm != order[-1] else order[0]
            x0, y = tabs[frm]; x1 = tabs[to][0]
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(600)
            evs, done = [], []
            h1 = lambda p: evs.extend(p["value"]); h2 = lambda p: done.append(1)
            cdp.on("Tracing.dataCollected", h1); cdp.on("Tracing.tracingComplete", h2)
            cdp.send("Tracing.start", {"categories": "devtools.timeline,disabled-by-default-devtools.timeline", "transferMode": "ReportEvents"})
            glide(pg, cdp, x0, x1, y, 2.0, sample=False)
            touch(cdp, "touchEnd")
            pg.wait_for_timeout(300)
            cdp.send("Tracing.end")
            for _ in range(200):
                if done: break
                pg.wait_for_timeout(100)
            cdp.remove_listener("Tracing.dataCollected", h1); cdp.remove_listener("Tracing.tracingComplete", h2)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            pg.wait_for_timeout(2000)
            st = pg.evaluate(STATE, SCREEN_OF[to])
            w = trace_work(evs) or {"maxEls": 9999, "worstTask": 999, "worstAt": None}
            m = {"from": frm, "to": to, "st": st, "w": w}
            score = (0 if st["lit"] == [to] and st["up"] else 1, w["worstTask"])
            if best is None or score < best[0]: best = (score, m)
        m = best[1]; w = m["w"]; st = m["st"]
        print("  %s: %s -> %s | %s | after %s" % (name, m["from"], m["to"], w, st), flush=True)
        chk("(2) %s: a slide %s -> %s lands there (lit %s, screen up %s)" % (name, m["from"][10:], m["to"][10:], st["lit"], st["up"]), st["lit"] == [m["to"]] and st["up"], st)
        chk("(2) %s: no style pass during the slide restyles more than 300 elements (largest %s)" % (name, w["maxEls"]), w["maxEls"] <= 300, w)
        chk("(2) %s: no task during the slide runs over 50ms of the app's own work at 4x CPU (worst %sms, %sms into the slide)" % (name, w["worstTask"], w["worstAt"]), w["worstTask"] <= 50, w)

    # ---- (3) steady: touches that do not come one per frame ----
    best = None
    for attempt in range(2):
        pg.evaluate("()=>" + SHOW["calendar"]); pg.wait_for_timeout(2500)
        tabs = tabs_of(pg); x0, y = tabs["bottomtab-calendar"]; x1 = tabs["bottomtab-home"][0]
        s = glide(pg, cdp, x0, x1, y, 1.8, gaps=(0.006, 0.006, 0.022))
        touch(cdp, "touchEnd"); pg.wait_for_timeout(1500)
        fr, mv = s["fr"], s["mv"]
        steps = []
        if len(mv) > 10:
            tA = mv[0][0] + (mv[-1][0] - mv[0][0]) * .3; tB = mv[0][0] + (mv[-1][0] - mv[0][0]) * .7
            for (ta, la, fa, na), (tb, lb, fb, nb) in zip(fr, fr[1:]):
                if ta < tA or tb > tB: continue
                # the finger's own speed about this frame, from the moves around it
                near = [p for p in mv if ta - 60 <= p[0] <= tb + 60]
                if len(near) < 2 or near[-1][0] == near[0][0]: continue
                v = (near[-1][1] - near[0][1]) / (near[-1][0] - near[0][0])
                if abs(v) < .05: continue
                steps.append(round((lb - la) / (v * (tb - ta)), 2))
        still = sum(1 for r in steps if r < .25)
        res = {"frames": len(steps), "still": still, "share": round(still / max(1, len(steps)), 2), "med": steps and statistics.median(steps), "first": steps[:24]}
        if best is None or (res["frames"] >= 15, -res["share"]) > (best["frames"] >= 15, -best["share"]): best = res
    print("  steady: %s" % best, flush=True)
    chk("(3) touches not one per frame: the glass stands still or steps back on %d of %d frames (%d%%, at most 20%%), its median step %s of the finger's" % (
        best["still"], best["frames"], round(100 * best["share"]), best["med"]),
        best["frames"] >= 15 and best["share"] <= .2, best)

    # ---- (4) a screen build that comes due while a finger slides waits for the release ----
    # (a tap's screen is built TAB_SCREEN_AFTER ms after its press; a finger back down and sliding inside that time used to have it built
    # under the glide. Made exact here: the Leaderboard tab is clicked from the page while a slide from Home is going.)
    pg.evaluate("()=>" + SHOW["home"]); pg.wait_for_timeout(3000)
    pg.evaluate("""()=>{ const real=window.showRankings; window.__realSR=real; window.__srAt=[];
      window.showRankings=function(){ window.__srAt.push(performance.now()); const t=performance.now(); while(performance.now()-t<300){} return real.apply(this,arguments); };
      window.__fing={down:[],up:[]}; addEventListener('pointerdown',()=>__fing.down.push(performance.now()),true); addEventListener('pointerup',()=>__fing.up.push(performance.now()),true); }""")
    tabs = tabs_of(pg); xh, y = tabs["bottomtab-home"]; xl = tabs["bottomtab-rewards"][0]
    touch(cdp, "touchStart", xh, y); time.sleep(0.15)
    for k in range(1, 5):
        touch(cdp, "touchMove", xh + 4 * k, y); time.sleep(0.016)
    t0 = time.time(); clicked = None
    while True:
        u = min(1, (time.time() - t0) / 1.4)
        touch(cdp, "touchMove", xh + 16 + (xl - xh - 16) * (0.5 - 0.5 * math.cos(u * math.pi)), y)
        if clicked is None and u > .3:
            clicked = pg.evaluate("()=>{ document.getElementById('bottomtab-rewards').click(); return performance.now(); }")
        if u >= 1: break
        time.sleep(0.008)
    time.sleep(0.4)
    touch(cdp, "touchEnd"); pg.wait_for_timeout(2000)
    r4 = pg.evaluate("()=>({ sr: window.__srAt, f: window.__fing, st: [...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(t=>t.id), up: !!document.querySelector('#stage .screen-rankings') })")
    pg.evaluate("()=>{ window.showRankings=window.__realSR; }")
    ups = r4["f"]["up"]; builds = r4["sr"]
    rel = ups[-1] if ups else None
    print("  build due mid-slide: clicked %s, released %s, built %s | after %s" % (
        clicked and round(clicked), rel and round(rel), [round(b) for b in builds], {"lit": r4["st"], "up": r4["up"]}), flush=True)
    chk("(4) a screen build due while the finger slides waits for the release (built %s ms after the release; clicked %s ms before it)" % (
        [round(b - rel) for b in builds] if rel else builds, rel and clicked and round(rel - clicked)),
        rel is not None and len(builds) >= 1 and all(b >= rel for b in builds) and r4["up"] and r4["st"] == ["bottomtab-rewards"], r4)
    chk("no page errors (%s)" % errs[:3], not errs, errs)
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
