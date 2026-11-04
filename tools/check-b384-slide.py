"""Build 384: the tab bar slide's last 10-15% (the release), and Home's rank flares that shook.
Madison (383, Fire Code): "The sliding and tapping features look 100x better. I think there's a delay when sliding on home, maybe
slightly sliding on profile ... It's about the same for ifc and police versions ... We need 10-15 percent better." And: "the stuff with
the rank flares, if you can tell, they are shaking very very slightly but just a noticeable amount. Fix that."
His 120fps recordings read frame by frame: let go of a slide and the glass stood frozen where the finger left it for 3-6 frames (10 over
Home), then the tab lit, the screen changed and the glass jumped, in ONE frame - the release's frame was never drawn before the new
screen's build (a 0ms timer, which Safari runs before its next frame). And each rank bubble's emblem shifted 0.1-0.5px at every step of
its sheet (the bubbles themselves float smoothly): Home's hero is drawn at 0.94, and a step was whole device pixels on the SCREEN but not
in the window's own paint, which is what Safari rasterises at the device's scale.
As an iPhone (its user agent, real CDP touches, 440x956 at 3x), check-b382-slide's harness:
 (1) THE RELEASE IS DRAWN BEFORE THE SCREEN IS BUILT. Safari's order is emulated: a timer of 0-4ms set while the release is handled
     runs before the page draws (Chromium itself draws first after input, so without this the previous build passes by luck of the
     scheduler, not by design). Slides Home -> Profile, Profile -> Home and Calendar -> Home at 4x CPU: a frame comes between the
     release and the new screen's build; the release reads no layout (no box, offset or computed style read in its handler: a forced
     style pass and layout of the whole page); the frame after the release comes within 90ms at 4x CPU; and the slide still lands
     (that tab lit, its screen up, the glass gone).
 (3) THE GLASS UNDER THE FINGER. The row was measured before the bar's swell began and, for a finger that rested past the swell
     (160ms) before sliding, never again: the slide mapped the finger through the unswollen bar (the glass 10px left of a finger held
     still at Home's centre, 6px a tab on, 2.4px right of it on the Leaderboard). A finger held still after a slide's first moves has
     the glass within 1px of it on Home (twice), the Leaderboard and the Calendar; and on check-b382-slide's Home slide at 4x CPU the
     glass is never more than 3px behind the finger (8.4-9.3 before - (3) there failed on Home since 382).
 (2) THE FLARES' STEPS ARE WHOLE PIXELS IN THEIR OWN PAINT. On Home (the Fire Code class, his): every rank bubble's sheet window is a
     whole number of device pixels a cell in its own coordinates (its CSS cell x devicePixelRatio), each step of the sheet (left/top)
     a whole number of cells, the window the same box on the screen as the bubble's cell (126 device px at 3x, centred on the bubble),
     and it shows the clock's frame.
Run:  python3 tools/check-b384-slide.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, time, math, statistics, re
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "check-b382-slide.py")).read().split("\nwith sync_playwright() as pw:")[0]
g2 = {"__file__": os.path.join(HERE, "check-b382-slide.py"), "__name__": "b384slide"}
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

# Safari's order: a timer due before the next frame runs before it. Timers of 0-4ms set while a pointerup is being handled are run at
# the end of that handling (the window's bubble listener, after the bar's own), before the page can draw.
WK = r"""(()=>{ const st=window.setTimeout.bind(window), ct=window.clearTimeout.bind(window); let col=null; const recs=new Map();
  window.setTimeout=function(fn,ms){ const a=[].slice.call(arguments,2); if(col && typeof fn==='function' && !(Number(ms)>4)){ const rec={fn,a,dead:false}; col.push(rec);
      const id=st(()=>{ if(!rec.dead){ rec.dead=true; fn.apply(window,a); } },ms); recs.set(id,rec); return id; } return st.apply(window,arguments); };
  window.clearTimeout=function(id){ const r=recs.get(id); if(r) r.dead=true; return ct(id); };
  addEventListener('pointerup',()=>{ col=[]; },true);
  addEventListener('pointerup',()=>{ const l=col||[]; col=null; l.forEach(r=>{ if(!r.dead){ r.dead=true; try{ r.fn.apply(window,r.a); }catch(e){ st(()=>{ throw e; }); } } }); },false);
})()"""
# the frames, the release's handler (its reads), the builds - read in the page
HOOK = r"""()=>{ if(window.__T) window.__T.on=false; const T=window.__T={up:null,upEnd:null,raf:[],build:[],on:true,upReads:null};
  if(!window.__hooked){ window.__hooked=1;
    addEventListener('pointerup',e=>{ const T=window.__T; if(T){ T.up=performance.now(); window.__reads={}; window.__readOn=true; } },true);
    addEventListener('pointerup',e=>{ const T=window.__T; window.__readOn=false; if(T){ T.upEnd=performance.now(); T.upReads=Object.assign({},window.__reads); } },false);
    ['showHome','showProfile','showRankings','openCalendarTab','showCalendarTab','showStatsScreen','showAppearance'].forEach(n=>{ const f=window[n]; if(typeof f!=='function') return;
      window[n]=function(){ const t=performance.now(); try{ return f.apply(this,arguments); } finally{ const T=window.__T; if(T) T.build.push([n,t,performance.now()]); } }; });
  }
  const f=()=>{ if(!T.on) return; T.raf.push(performance.now()); requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
SCREEN_OF = {"home": ".screen-home-actual", "profile": ".screen-profile:not(.screen-stats)", "calendar": ".screen-calendar-tab", "rewards": ".screen-rankings"}
SHOW = {"home": "showHome()", "profile": "showProfile()", "calendar": "showCalendarTab()", "rewards": "showRankings()"}

def touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})

def slide(pg, cdp, x0, x1, y, D=0.9):
    pg.evaluate(HOOK); time.sleep(0.1)
    touch(cdp, "touchStart", x0, y); time.sleep(0.12)
    t0 = time.time()
    while True:
        u = min(1, (time.time() - t0) / D)
        touch(cdp, "touchMove", x0 + (x1 - x0) * (0.5 - 0.5 * math.cos(u * math.pi)), y)
        if u >= 1: break
        time.sleep(0.008)
    time.sleep(0.03)
    touch(cdp, "touchEnd")
    pg.wait_for_timeout(1800)
    return pg.evaluate("()=>{ const T=window.__T; T.on=false; return T; }")

def nxt(arr, t):
    for v in arr:
        if v > t: return v
    return None

def page(pw, ifc=False, wk=False):
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=3, has_touch=True, is_mobile=True)
    if wk: ctx.add_init_script(WK)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]())); ctx.add_init_script(g2["IPH"])
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0))
    build = re.search(r'const APP_BUILD = "([^"]+)"', body).group(1)
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": build, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(g["STATUS_BAR"].replace("__H__", "62"))
    d = dict(g2["d"])
    if ifc: d["publicId"] = "xph5b57jbp5a"; d["firstName"] = "Maddog"
    pg.add_init_script(g2["INIT"] % json.dumps(json.dumps(d)))
    if ifc:
        pg.add_init_script("""(()=>{ try{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');
          ['class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.freshstart','class26e.ifc.getstarted','class26e.ifc.savecode.asked','class26e.ifc.savecode.card'].forEach(k=>localStorage.setItem(k,'1')); }catch(e){} })()""")
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(g2["url"]); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} try{ store.novaMet=99; }catch(e){} document.querySelectorAll('#tour-overlay,.rs-spot,.unlock-card,.nova-talk,#nova-intro').forEach(n=>n.remove()); }")
    return br, ctx, pg, errs

with sync_playwright() as pw:
    # ---- (1) the release, Safari's timer order ----
    br, ctx, pg, errs = page(pw, wk=True)
    cdp = ctx.new_cdp_session(pg)
    for s in ("showProfile()", "showCalendarTab()", "showHome()"):
        pg.evaluate("()=>" + s); pg.wait_for_timeout(2000)
    for _ in range(120):
        if pg.evaluate("()=>window.__frames") >= 100: break
        pg.wait_for_timeout(500)
    touch(cdp, "touchStart", 220, 300); time.sleep(0.05); touch(cdp, "touchEnd"); pg.wait_for_timeout(1200)
    for frm, to in (("home", "profile"), ("profile", "home"), ("calendar", "home")):
        best = None
        for attempt in range(2):
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            pg.evaluate("()=>" + SHOW[frm]); pg.wait_for_timeout(3000)
            pg.evaluate("()=>document.querySelectorAll('#tour-overlay,.rs-spot,.unlock-card,.nova-talk,#nova-intro').forEach(n=>n.remove())")
            tabs = g2["tabs_of"](pg)
            x0, y = tabs["bottomtab-" + frm]; x1 = tabs["bottomtab-" + to][0]
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(700)
            T = slide(pg, cdp, x0, x1, y)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            st = pg.evaluate("""(sel)=>({ lit:[...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(t=>t.id), up:!!document.querySelector('#stage ' + sel),
              lens: !!document.querySelector('#bottomtabs-lens.is-up') })""", SCREEN_OF[to])
            b = [x for x in T["build"] if T["up"] and x[1] > T["up"]]
            f1 = nxt(T["raf"], T["up"] or 0)
            m = {"lit": st["lit"], "up": st["up"], "lensUp": st["lens"], "reads": sum((T["upReads"] or {}).values()), "readsBy": T["upReads"],
                 "upToFrame": round(f1 - T["up"], 1) if f1 and T["up"] else None,
                 "build": b[0][0] if b else None, "upToBuild": round(b[0][1] - T["up"], 1) if b else None,
                 "frameFirst": bool(b and f1 and f1 < b[0][1])}
            score = (0 if m["frameFirst"] else 1, m["reads"], m["upToFrame"] or 9999)
            if best is None or score < best[0]: best = (score, m)
        m = best[1]
        print("  %s -> %s: %s" % (frm, to, m), flush=True)
        chk("(1) %s -> %s: the frame after the release is drawn before %s's screen is built (frame %sms, build %sms after the release)" % (frm, to, to, m["upToFrame"], m["upToBuild"]),
            m["frameFirst"] and m["build"], m)
        chk("(1) %s -> %s: the release reads no layout (%s reads: %s)" % (frm, to, m["reads"], m["readsBy"]), m["reads"] == 0, m)
        chk("(1) %s -> %s: the frame after the release comes within 90ms at 4x CPU (%sms)" % (frm, to, m["upToFrame"]), m["upToFrame"] is not None and m["upToFrame"] <= 90, m)
        chk("(1) %s -> %s: it lands - %s lit, its screen up, the glass down (%s)" % (frm, to, to, m), m["lit"] == ["bottomtab-" + to] and m["up"] and not m["lensUp"], m)
    # ---- (3) the glass under the finger (the row read through the swell) ----
    PROBE = r"""()=>{ const H=window.__H; const b=H.getBoundingClientRect.call(document.querySelector('#bottomtabs-lens .tab-lens-body')); return b.left+b.width/2; }"""
    held = []
    for scr, tab, dx in (("home", "bottomtab-home", 16), ("home", "bottomtab-home", 60), ("rewards", "bottomtab-rewards", -16), ("calendar", "bottomtab-calendar", -16)):
        pg.evaluate("()=>" + SHOW[scr]); pg.wait_for_timeout(2500)
        tabs = g2["tabs_of"](pg); x0, y = tabs[tab]
        touch(cdp, "touchStart", x0, y); time.sleep(0.25)
        for k in range(1, 5): touch(cdp, "touchMove", x0 + dx * k / 4, y); time.sleep(0.016)
        pg.wait_for_timeout(450)
        lc = pg.evaluate(PROBE)
        touch(cdp, "touchEnd"); pg.wait_for_timeout(1500)
        held.append((scr, dx, round(lc - (x0 + dx), 2)))
    print("  glass - finger, finger held still after a slide's first moves:", held, flush=True)
    chk("(3) a finger held still mid-slide has the glass on it, everywhere on the bar (within 1px: %s)" % held, all(abs(h[2]) <= 1 for h in held), held)
    # and while it slides: check-b382-slide's Home slide (out to the Leaderboard and back) at 4x, the glass read after every frame - with
    # the finger resting 400ms (not 200) before its first move, so the swell has always finished by then (the case that went wrong)
    class _Rest:
        def __getattr__(self, n): return getattr(time, n)
        def sleep(self, s): time.sleep(0.4 if s == 0.2 else s)
    g2["time"] = _Rest()
    best = None
    for attempt in range(2):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(3000)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(600)
        m = g2["slide"](pg, cdp, "bottomtab-home", "bottomtab-rewards", back=True)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        L = g2["lag"](m)
        if L.get("n", 0) >= 3 and (best is None or L["behindMax"] < best["behindMax"]): best = L
        pg.wait_for_timeout(1500)
    print("  Home slide at 4x, glass against the finger each frame:", best, flush=True)
    chk("(3) sliding on Home the glass is never more than 3px behind the finger (%s at worst; median %s ahead)" % (best and best["behindMax"], best and best["med"]),
        best and best["behindMax"] <= 3, best)
    if errs: chk("(1) no page errors", False, errs[:4])
    br.close()

    # ---- (2) Home's rank flares (the Fire Code class, his) ----
    br, ctx, pg, errs = page(pw, ifc=True)
    pg.evaluate("()=>showHome()")
    t0 = time.time(); n = 0
    while time.time() - t0 < 150:
        pg.wait_for_timeout(2000)
        n = pg.evaluate("()=>document.querySelectorAll('#stage .cosmic-hero-wrap > .cosmic-badge-rank .rk-frame img').length")
        if n >= 4: break
    cls = pg.evaluate("()=>window.NOVA_CLASS")
    geo = pg.evaluate(r"""()=>{ const dpr=devicePixelRatio, out=[];
      document.querySelectorAll('#stage .cosmic-hero-wrap > .cosmic-badge-rank').forEach(b=>{
        const img=b.querySelector(':scope > .cosmic-rank-anim:not(.is-standin) .rk-frame img'); if(!img) return;
        const fr=img.parentElement, cell=parseFloat(fr.style.width), cs=getComputedStyle(img);
        const left=parseFloat(cs.left)||0, top=parseFloat(cs.top)||0;
        const r=fr.getBoundingClientRect(), br=b.getBoundingClientRect();
        /* the bubble's own cell on the screen: its shown width at the sheet's scale, even (startOrbitEmblemAnims) */
        const sc=Math.min(dpr,2); let px=Math.round(br.width*sc); px-=px%2;
        const a=img.getAnimations()[0]; const dur=a?a.effect.getTiming().duration:6000, nfr=180, cols=12;
        const k=Math.round(-left/cell)+cols*Math.round(-top/cell);
        const want=a?Math.floor(((a.currentTime%dur)+dur)%dur/(dur/nfr)):null;
        out.push({ tier:b.dataset.rankTier, cellDev:+(cell*dpr).toFixed(4), stepX:+(-left/cell).toFixed(4), stepY:+(-top/cell).toFixed(4),
          winDev:+(r.width*dpr).toFixed(3), wantDev:px*dpr/sc, dc:+Math.max(Math.abs((r.left+r.width/2)-(br.left+br.width/2)), Math.abs((r.top+r.height/2)-(br.top+br.height/2))).toFixed(3),
          frame:k, clock:want });
      }); return out; }""")
    print("  class %s, %d sheets on Home:" % (cls, len(geo)), flush=True)
    for x in geo: print("    ", x, flush=True)
    frac = lambda v: abs(v - round(v))
    chk("(2) Home (%s) carries its rank flares' sheets (%d)" % (cls, len(geo)), cls == "ifc" and len(geo) >= 3, geo)
    bad = [x for x in geo if frac(x["cellDev"]) > .01 or frac(x["stepX"]) > .001 or frac(x["stepY"]) > .001]
    chk("(2) each flare's sheet steps whole device pixels in its window's own paint (cell x dpr: %s)" % sorted(set(x["cellDev"] for x in geo)), geo and not bad, bad)
    off = [x for x in geo if abs(x["winDev"] - x["wantDev"]) > .5 or x["dc"] > .5]
    chk("(2) each window is the bubble's cell on the screen (%s device px, centred within %s CSS px)" % (sorted(set(x["winDev"] for x in geo)), max([x["dc"] for x in geo] or [0])), geo and not off, off)
    late = [x for x in geo if x["clock"] is None or min(abs(x["frame"] - x["clock"]), 180 - abs(x["frame"] - x["clock"])) > 1]
    chk("(2) each shows the clock's frame (%s)" % [(x["frame"], x["clock"]) for x in geo], geo and not late, late)
    if errs: chk("(2) no page errors", False, errs[:4])
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
