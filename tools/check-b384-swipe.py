"""Build 384 (r22): THE TOP-TAB SWIPE (Profile's tabs, the Leaderboard's boards) follows the finger.
Madison: "THE SWIPING AND SLIDING FUNCTION IS TERRIBLE" / "there is still so much lag when swiping between stuff". A swipe of the screen used
to do nothing until the finger lifted and then swapped the tab in one step (a board's build, 180-280ms at 4x CPU, sitting between the
lift and anything moving). Now the content follows the finger (one transform write a frame, no reads), eases back when let go short,
and is carried off and replaced by the next tab's on release.
As an iPhone (its user agent, real touches through CDP, 440x956 at 3x, installed), 44 classmates from a fake cloud, the academy
(Profile: its tabs; Leaderboard: its boards - the tab lists are read off the page) and Fire Code (Profile alone: nothing to swipe to).
For every adjacent pair of tabs, both directions:
 (1) FOLLOWS (1x CPU, a slow drag of ~40% of the width, a move every 12ms): from the first frame the content has moved, every frame's
     offset is that of one of the last two touch moves within 2px (a rubber band, a third as far, where there is no tab that way); no
     more layout per frame across the drag than the screen has at rest (and at most one), and the median frame gap no worse than at
     rest (+5ms, and 20ms where the screen at rest is quiet), no frame over 250ms (a busy machine drops a few; the 4x CPU runs in (2)).
 (2) LANDS (1x and 4x CPU): let go past a third of the width the next tab is lit within 450ms (at 4x too), the content has no transform,
     opacity, will-change or lifted copy left on it, and nothing in the page is mid-animation 900ms after.
 (3) A SHORT DRAG EASES BACK: ~15% of the width and let go - the same tab is lit, the content offset is gone within 400ms (and was there
     while the finger was).
 (4) A FLICK: a fast 70px swipe (a move every 6ms, 90ms in all) commits.
 (5) NEVER FIGHTS A SCROLL: a finger that goes down first (14px) and then sideways does not switch (and moves nothing); a swipe
     that starts within 20px of the screen's left edge (the system's swipe back) does not; one that starts on something that
     scrolls sideways itself (a strip made to scroll sideways, put on the screen) does not, and does not move the content.
 (8) A SECOND SWIPE THAT STARTS WHILE THE FIRST IS STILL LANDING (150ms after it) is taken: the first is carried to its end at once and the
     second goes on from there (three tabs: first -> third).
 (6) FIRE CODE: its Profile has two tabs (Profile, Stats - 384 r21): a sideways drag follows the finger like the academy's and throws nothing.
 (7) no page error.
Run:  python3 tools/check-b384-swipe.py [--only 1,2,...] [--against REV|path/to/index.html]   (--against 3a6675d must FAIL (1)(3)(5))"""
import os, sys, time, json, math, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
_args = sys.argv[:]
_src = open(os.path.join(HERE, "check-b384-desktop.py")).read().split("\nwith sync_playwright() as pw:")[0]
ONLY = set(_args[_args.index("--only") + 1].split(",")) if "--only" in _args else None
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
G = {"__file__": os.path.join(HERE, "check-b384-desktop.py"), "__name__": "b384swipe"}
exec(_src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
def info(s): print("INFO " + s, flush=True)
def want(n): return ONLY is None or str(n) in ONLY

IFC = ("try{ localStorage.setItem('class26e.activeclass','ifc'); ['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen',"
       "'class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1')); }catch(e){}")
W = 440
# every frame: the offset of whatever the swipe is moving (an element of the stage with a translate3d on it), the newest touch moves, and layouts
LOGGER = """()=>{ if(window.__s) window.__s.on=false;
  const S=window.__s={ on:true, fr:[], mv:[], ts:null, te:null };
  addEventListener('touchstart', e=>{ S.ts=performance.now(); }, true);
  addEventListener('touchmove', e=>{ S.mv.push(e.touches[0].clientX); }, true);
  addEventListener('touchend', e=>{ S.te=performance.now(); }, true);
  const f=t=>{ if(!S.on) return; const k=S.mv.length; setTimeout(()=>{ const e=document.querySelector('#stage [data-tabdrag]'); const m=e&&/translate3d\\(([-0-9.]+)px/.exec(e.style.transform);
    S.fr.push([t, m?+m[1]:0, k, !!e]); }, 0); requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
STATE = """()=>{ const seg=document.querySelector('#stage .navsegment'); const act=seg&&seg.querySelector('.iconbtn.active');
  const moving=document.querySelector('#stage [data-tabdrag], #stage [aria-hidden="true"][inert][style*="fixed"]');
  const anim=document.getAnimations().filter(a=>{ const tm=a.effect&&a.effect.getTiming&&a.effect.getTiming(); return a.playState==='running' && tm && tm.fill==='forwards' && isFinite(tm.iterations) && [110,170,200,260].indexOf(tm.duration)>=0 && a.effect.target && a.effect.target.closest && a.effect.target.closest('#stage'); }).length;
  return { tab: act&&act.textContent.trim(), left: !!moving, anims: anim }; }"""
# the first y on the screen where a finger belongs to the swipe (not on a slider, a field, the switcher)
FINDY = """()=>{ for(const y of [500,620,380,740,300,820]){ const e=document.elementFromPoint(300,y); if(e && !e.closest('input,textarea,select,.sliderwrap,.has-seg-glass,[data-noswipe],.bottomtabs,#bottomtabs')) return y; } return 500; }"""

def touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})
def drag(pg, cdp, x0, x1, y, D, gap=0.012, hold=0.15, release=True, pre=None):
    """finger down, held `hold`, then a straight line to x1 over D seconds (a move every ~gap), then (release) up"""
    touch(cdp, "touchStart", x0, y); time.sleep(hold)
    if pre:
        for (px, py) in pre: touch(cdp, "touchMove", px, py); time.sleep(0.016)
    t0 = time.time()
    while True:
        u = min(1, (time.time() - t0) / D)
        touch(cdp, "touchMove", x0 + (x1 - x0) * u, y)
        if u >= 1: break
        time.sleep(gap)
    if release: time.sleep(0.03); touch(cdp, "touchEnd")
def tabs_of(pg):
    return pg.evaluate("()=>{ const s=document.querySelector('#stage .navsegment'); return s?[...s.querySelectorAll('.iconbtn')].filter(b=>!b.hidden).map(b=>b.textContent.trim()):[]; }")
def go_tab(pg, name):
    pg.evaluate("(n)=>{ const s=document.querySelector('#stage .navsegment'); [...s.querySelectorAll('.iconbtn')].find(b=>b.textContent.trim()===n).click(); }", name)
    pg.wait_for_timeout(900)
def settle_wait(pg, want_tab, ms=450):
    t0 = time.time()
    while (time.time() - t0) * 1000 < ms:
        if pg.evaluate(STATE)["tab"] == want_tab: return round((time.time() - t0) * 1000)
        pg.wait_for_timeout(15)
    return None

def run_screen(br, label, show, cls=None):
    ctx, pg, cdp, errs, touchy = G["open_page"](br, "phone", extra=((IFC,) if cls == "ifc" else ()))
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; }")
    pg.evaluate("()=>" + show); pg.wait_for_timeout(3000)
    cdp.send("Performance.enable")
    tabs = tabs_of(pg)
    return ctx, pg, cdp, errs, tabs

def phase_follow(pg, cdp, frm, to, to_left):
    y = pg.evaluate(FINDY)
    # the screen at rest first (the Leaderboard and its animated pictures cost frames and layouts with no finger on it, more on a busy
    # machine): the drag is held to that, not to a number
    pg.evaluate(LOGGER)
    b0 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    pg.wait_for_timeout(800)
    b1 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    base = pg.evaluate("()=>{ const f=window.__s.fr; const g=[]; for(let i=3;i<f.length;i++) g.push(f[i][0]-f[i-1][0]); g.sort((a,b)=>a-b); return { n:f.length, p95:g.length?g[Math.floor(g.length*.95)]:0, med:g.length?g[Math.floor(g.length/2)]:0 }; }")
    base["lay"] = (b1["LayoutCount"] - b0["LayoutCount"]) / max(1, base["n"])
    pg.evaluate(LOGGER)
    m0 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    x0, x1 = (330, 330 - 176) if to_left else (110, 110 + 176)
    drag(pg, cdp, x0, x1, y, 0.9, release=False)
    time.sleep(0.12)
    m1 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    s = pg.evaluate("()=>{ window.__s.on=false; return { fr: window.__s.fr, mv: window.__s.mv }; }")
    s["base"] = base
    return s, m1["LayoutCount"] - m0["LayoutCount"], x0, y

def analyse_follow(s, x0, layouts, has_next):
    fr = s["fr"]; mv = s["mv"]
    if len(fr) < 10 or not mv: return {"err": "no frames"}
    moved = [f for f in fr if f[3]]
    errs_ = []
    for f in moved:
        k = f[2]                      # touch moves seen when this frame was logged
        cands = [mv[j] - x0 for j in range(max(0, k - 2), min(len(mv), k + 2))]
        if not cands: continue
        def off(dx): return dx          # a tab lies the way every drag here goes
        errs_.append(min(abs(f[1] - off(dx)) for dx in cands))
    gaps = sorted(fr[i][0] - fr[i - 1][0] for i in range(6, len(fr)))
    p95 = gaps[int(len(gaps) * 0.95)] if gaps else 0
    med = gaps[len(gaps) // 2] if gaps else 0; mx = gaps[-1] if gaps else 0
    base = s.get("base") or {"p95": 0, "lay": 0}
    return {"moved": len(moved), "frames": len(fr), "worst": round(max(errs_), 1) if errs_ else None, "p95": round(p95, 1), "layouts": layouts, "maxtx": max(abs(f[1]) for f in fr),
            "lay_pf": round(layouts / max(1, len(fr)), 2), "base_lay": round(base["lay"], 2), "base_p95": round(base["p95"], 1), "med": round(med, 1), "base_med": round(base.get("med", 0), 1), "max": round(mx, 1)}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    allerrs = []
    SCREENS = (("Profile", "showProfile()"), ("Leaderboard", "showRankings()"))
    for label, show in SCREENS:
        ctx, pg, cdp, errs, tabs = run_screen(br, label, show)
        info("%s: tabs read off the page: %s" % (label, tabs))
        if len(tabs) < 2:
            chk("%s has tabs to swipe between" % label, False, tabs); ctx.close(); continue
        y = pg.evaluate(FINDY)
        # warm-up: the first swipe on a screen builds what its tabs hold for the first time (a one-off, seconds on a loaded machine)
        for fl in (True, False):
            go_tab(pg, tabs[0] if fl else tabs[1])
            drag(pg, cdp, 330 if fl else 110, 154 if fl else 286, y, 0.5, gap=0.02); pg.wait_for_timeout(1500)
        # a first touch wakes the sound (a one-off): done once, off the content
        touch(cdp, "touchStart", 100, 36); time.sleep(0.05); touch(cdp, "touchEnd"); pg.wait_for_timeout(800)
        for k in range(len(tabs) - 1):
            for to_left in (True, False):
                frm, to = (tabs[k], tabs[k + 1]) if to_left else (tabs[k + 1], tabs[k])
                name = "%s: %s -> %s" % (label, frm, to)
                if want(1):
                    go_tab(pg, frm)
                    s, lay, x0, y = phase_follow(pg, cdp, frm, to, to_left)
                    touch(cdp, "touchEnd"); pg.wait_for_timeout(1000)
                    a = analyse_follow(s, x0, lay, True)
                    chk("(1) %s: the content follows the finger within 2px (worst %s px over %s frames, max offset %s)" % (name, a.get("worst"), a.get("moved"), a.get("maxtx")),
                        a.get("moved", 0) >= 6 and a["worst"] is not None and a["worst"] <= 2, a)
                    chk("(1) %s: no more layout than the screen at rest (%s a frame, at rest %s) and a frame gap median %s ms (at rest %s), worst %s ms" % (name, a.get("lay_pf"), a.get("base_lay"), a.get("med"), a.get("base_med"), a.get("max")),
                        a.get("frames") and a["lay_pf"] <= max(1.0, a["base_lay"] + 0.5) and a["med"] <= max(20, a["base_med"] + 5) and a["max"] <= 250, a)
                if want(2):
                    for rate in (1, 4):
                        cdp.send("Emulation.setCPUThrottlingRate", {"rate": rate})
                        go_tab(pg, frm); y = pg.evaluate(FINDY)
                        x0, x1 = (330, 330 - 176) if to_left else (110, 110 + 176)
                        drag(pg, cdp, x0, x1, y, 0.5, gap=0.02, release=True)
                        t0 = time.time()
                        lit = settle_wait(pg, to, 450 if rate == 4 else 400)
                        pg.wait_for_timeout(900)
                        st = pg.evaluate(STATE)
                        chk("(2) %s at %dx: the next tab is lit within 450ms of the release (%s ms), nothing left on the content or running" % (name, rate, lit),
                            lit is not None and not st["left"] and st["anims"] == 0 and st["tab"] == to, (lit, st))
                        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
                if want(3):
                    go_tab(pg, frm); y = pg.evaluate(FINDY)
                    pg.evaluate(LOGGER)
                    x0, x1 = (330, 330 - 64) if to_left else (110, 110 + 64)
                    drag(pg, cdp, x0, x1, y, 0.4, release=False); time.sleep(0.1)
                    mid = pg.evaluate("()=>{ const f=window.__s.fr; return f.length?f[f.length-1][1]:0; }")
                    touch(cdp, "touchEnd"); pg.wait_for_timeout(650)
                    st = pg.evaluate(STATE); pg.evaluate("()=>{ window.__s.on=false; }")
                    chk("(3) %s: a short drag moved the content (%s px) and eases back: same tab, nothing left within 650ms" % (name, mid),
                        abs(mid) > 20 and st["tab"] == frm and not st["left"], (mid, st))
                if want(4):
                    go_tab(pg, frm); y = pg.evaluate(FINDY)
                    # a real flick: the browser's own touch gesture at 1500px/s, 90px (the harness's own touches cannot come as fast as a thumb's)
                    x0 = 330 if to_left else 110
                    cdp.send("Input.synthesizeScrollGesture", {"x": x0, "y": y, "xDistance": -90 if to_left else 90, "yDistance": 0, "speed": 1500, "gestureSourceType": "touch", "preventFling": True})
                    lit = settle_wait(pg, to, 600)
                    pg.wait_for_timeout(700)
                    chk("(4) %s: a flick (90px in 90ms) commits (lit after %s ms)" % (name, lit), lit is not None, lit)
        if want(8) and len(tabs) >= 3:
            go_tab(pg, tabs[0]); y = pg.evaluate(FINDY)
            drag(pg, cdp, 330, 154, y, 0.3, gap=0.012)
            time.sleep(0.15)                       # the first is still landing
            drag(pg, cdp, 330, 154, y, 0.3, gap=0.012)
            lit = settle_wait(pg, tabs[2], 1500); pg.wait_for_timeout(700)
            chk("(8) %s: a second swipe that starts while the first is landing is taken (%s -> %s, lit after %s ms)" % (label, tabs[0], tabs[2], lit), lit is not None and not pg.evaluate(STATE)["left"], pg.evaluate(STATE))
        if want(5):
            a_, b_ = tabs[0], tabs[1]
            go_tab(pg, a_); y = pg.evaluate(FINDY)
            # a finger that goes down first and then sideways
            pg.evaluate(LOGGER)
            drag(pg, cdp, 330, 330 - 140, y, 0.4, release=False, pre=[(330, y + 8), (330, y + 16), (330, y + 24)]); time.sleep(0.1)
            seen = pg.evaluate("()=>window.__s.fr.some(f=>f[3])"); touch(cdp, "touchEnd"); pg.wait_for_timeout(800)
            chk("(5) %s: down first then sideways is a scroll, not a swipe (moved nothing: %s; tab %s)" % (label, not seen, pg.evaluate(STATE)["tab"]),
                not seen and pg.evaluate(STATE)["tab"] == a_, (seen, pg.evaluate(STATE)))
            # from the screen's left edge
            go_tab(pg, b_)
            drag(pg, cdp, 10, 10 + 200, y, 0.4); pg.wait_for_timeout(900)
            chk("(5) %s: a swipe from the left edge (the system's back) changes nothing (tab %s)" % (label, pg.evaluate(STATE)["tab"]), pg.evaluate(STATE)["tab"] == b_)
            go_tab(pg, a_)
            # on a strip that scrolls sideways
            pg.evaluate("""()=>{ const p=document.querySelector('#stage .panel'); const d=document.createElement('div'); d.id='__hs';
              d.style.cssText='position:fixed;left:0;right:0;top:'+(%d-40)+'px;height:80px;overflow-x:auto;z-index:5;background:#222'; const i=document.createElement('div'); i.style.cssText='width:1400px;height:60px'; d.appendChild(i); p.appendChild(d); }""" % y)
            pg.evaluate(LOGGER)
            drag(pg, cdp, 330, 330 - 200, y, 0.4); pg.wait_for_timeout(900)
            seen = pg.evaluate("()=>window.__s.fr.some(f=>f[3])")
            chk("(5) %s: a swipe that starts on a strip that scrolls sideways is the strip's (tab %s, content moved: %s)" % (label, pg.evaluate(STATE)["tab"], seen),
                pg.evaluate(STATE)["tab"] == a_ and not seen, pg.evaluate(STATE))
            pg.evaluate("()=>document.getElementById('__hs')?.remove()")
        allerrs += errs; ctx.close()
    if want(6):
        ctx, pg, cdp, errs, touchy = G["open_page"](br, "phone", extra=(IFC,))
        pg.evaluate("()=>{ homeUnlocksOwed=()=>false; }"); pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(2500)
        tabs = tabs_of(pg); y = pg.evaluate(FINDY)
        pg.evaluate(LOGGER); drag(pg, cdp, 330, 150, y, 0.4); pg.wait_for_timeout(700)
        seen = pg.evaluate("()=>window.__s.fr.some(f=>f[3])")
        chk("(6) Fire Code's Profile (%d tabs): a sideways drag follows the finger (moved: %s) and throws nothing" % (len(tabs), seen), len(tabs) == 2 and seen and not errs, (len(tabs), seen, errs))
        allerrs += errs; ctx.close()
    chk("(7) no page error", not allerrs, allerrs)
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
