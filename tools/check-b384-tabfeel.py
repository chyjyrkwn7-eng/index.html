#!/usr/bin/env python3
"""Build 384.102 (tabfeel): THE BOTTOM TAB BAR, TAP AND SLIDE, LAG-FREE AND THE SAME.

Madison (iPhone, installed, 384.94): "the bottom tab still lags, when tapping it's okay but sometimes it's bad or randomly goes or
moves where it shouldn't. Sliding is better but doesn't feel the same, idk if it's missing Haptic Touch on the slide for the one
you choose? ... It needs to feel consistent for both uses ... It needs to be lag free."

As an iPhone (its user agent, real CDP touches, installed, 440x956 at 3x, 4x CPU) with WEBKIT'S ORDER EMULATED - Chromium draws a
frame first after input, Safari runs any timer due before its next frame first; and a touch that starts on a native switch
(<input type=checkbox switch>, the haptic layer every tab carries) belongs to the switch: WebKit's CheckboxInputType dispatches the
click itself inside touchend's default handling (after a drag too) and plays the system haptic by its own rules (read off WebKit's
source, CheckboxInputType.cpp / RenderThemeIOS.h; see the WK block below):
 (T) TAPS, every ordered pair of the four tabs, twice: the glass's landing track is committed (its first frame drawn) BEFORE the new
     screen is built - on WebKit an animation reaches the compositor only at the next frame, so a build run first holds the landing
     back by the whole build and the glass then jumps back to where the finger let go and glides again; the press and the release
     read no layout in the bar's own handlers (each read forces a style pass and layout of the page, before the first frame of the
     glass); and every tap lands: that tab lit, the platter under it, the glass down, its screen up.
 (R) RAPID AND RANDOM: bursts of taps (30-450ms apart) and slides from every tab's screen, some mid-scroll: after each burst the bar
     ends on the last tab chosen, lit, platter under it, glass down, nothing held, its screen up - and the bar's own box (its layout
     position and size, the swell aside) never changes through any of it, nor through scrolls and a rubber band.
 (S) TAP AND SLIDE ARE THE SAME: a slide that lands on another tab gets exactly one haptic, at the release (none on the way: the
     switch it started on must not track the finger), as a tap does; a slide let go where it began gets none; one tab sound for
     each; and the landing - the shrink into the platter after the glass arrives - is the same track for both.
 (D) EVERY SIZE: an iPhone SE, an iPad Pro 11" (touch), a 1366x768 laptop and a 2560x1440 monitor (mouse: no glass, the platter
     steps): the frame that shows the bar's answer comes before the screen is built, and every tap or click lands.
Chromium has no Taptic Engine: (S) holds WebKit's rules for when a switch plays its tick, emulated from WebKit's own code, not the buzz.
Run:  TMPDIR=/dev/shm python3 tools/check-b384-tabfeel.py [--quick] [--only T,R,S,D] [--against OLD/index.html]   (--against must FAIL)"""
import json, os, sys, time, math, random, re, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    def _patched(ins, _o=OLD):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    g["patched"] = _patched
QUICK = "--quick" in sys.argv
ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else {"T", "R", "S", "D"}
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
def info(s): print("INFO " + s, flush=True)

IPH = """(()=>{ const ua='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148';
  Object.defineProperty(Navigator.prototype,'userAgent',{get:()=>ua,configurable:true}); try{ delete Navigator.prototype.vibrate; }catch(e){} })()"""
IPAD = """(()=>{ Object.defineProperty(Navigator.prototype,'maxTouchPoints',{get:()=>5,configurable:true}); try{ delete Navigator.prototype.vibrate; }catch(e){} })()"""
UA_IPAD = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
UA_DESK = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
# the harness's own layout readers (the counted ones below are the page's)
HREAD = "(()=>{ window.__H={ gbcr: Element.prototype.getBoundingClientRect, gcs: window.getComputedStyle }; })()"

# WEBKIT, EMULATED (see the docstring). The switch's rules, from WebKit's CheckboxInputType.cpp (main, 2026):
#  - touchstart on the switch: it keeps the touch's id and starts a 200ms "held" timer; when it fires, the switch starts TRACKING
#    the finger from the touch's starting point (startSwitchPointerTracking) - whether or not the finger has moved since;
#  - touchmove (default not prevented) while tracking: the thumb follows the finger; crossing the change position (half the track,
#    or the start +/- 40% of it when the start was in the thumb's end zone) flips it and plays the haptic at once
#    (performSwitchVisuallyOnAnimation(PointerTracking): no user-gesture check);
#  - touchend (default not prevented): dispatchSimulatedClick - the click, dispatched by the switch, for a drag too; in it
#    (willDispatchClick) the switch toggles and plays the haptic (Click: a trusted click in a user gesture) unless the drag already
#    flipped it; RenderThemeIOS::hasSwitchHapticFeedback is true for both triggers.
WK = r"""(()=>{ const st=window.setTimeout.bind(window), ct=window.clearTimeout.bind(window); let col=null; const recs=new Map();
  const W=window.__WK={on:true, ticks:[], clicks:0, dropped:0};
  window.setTimeout=function(fn,ms){ const a=[].slice.call(arguments,2); if(W.on && col && typeof fn==='function' && !(Number(ms)>4)){ const rec={fn,a,dead:false}; col.push(rec);
      const id=st(()=>{ if(!rec.dead){ rec.dead=true; fn.apply(window,a); } },ms); recs.set(id,rec); return id; } return st.apply(window,arguments); };
  window.clearTimeout=function(id){ const r=recs.get(id); if(r) r.dead=true; return ct(id); };
  const flush=()=>{ const l=col||[]; col=null; l.forEach(r=>{ if(!r.dead){ r.dead=true; try{ r.fn.apply(window,r.a); }catch(e){ st(()=>{ throw e; }); } } }); };
  addEventListener('pointerup',()=>{ if(!W.on) return; if(col) flush(); col=[]; },true);
  /* a release whose click never reaches the window (its propagation stopped) still lets its timers go, once its task is over */
  addEventListener('pointerup',()=>{ if(W.on) st(()=>{ if(col) flush(); },0); },false);
  let sw=null, held=0, tr=null, x0=0, swClickAt=-1e9, dropNext=false;
  const isSw=t=>!!(t && t.tagName==='INPUT' && t.type==='checkbox' && t.hasAttribute('switch'));
  const local=(el,x)=>{ const r=window.__H.gbcr.call(el); return { x:x-r.left, w:r.width, h:r.height }; };
  addEventListener('touchstart',e=>{ dropNext=false; if(!W.on) return; const t=e.target; ct(held); tr=null;
    sw=(isSw(t) && e.targetTouches && e.targetTouches.length===1) ? t : null;
    if(sw){ x0=e.targetTouches[0].clientX; const me=sw; held=st(()=>{ if(sw===me){ const L=local(me,x0); tr={ start:L.x, vis:me.checked, changed:false }; } },200); } },true);
  addEventListener('touchmove',e=>{ if(!W.on || !sw || !tr || e.defaultPrevented) return; const t=[...e.changedTouches][0]; if(!t) return;
    const L=local(sw,t.clientX); const thumbLeft=!tr.vis; let cp=L.w/2;
    if(!tr.changed){ const off=L.w*.4, noThumb=L.w-L.h; if(thumbLeft && tr.start>noThumb) cp=tr.start+off; else if(!thumbLeft && tr.start<noThumb) cp=tr.start-off; }
    const leftNow=L.x<cp; if(leftNow!==thumbLeft){ tr.changed=true; tr.vis=!tr.vis; W.ticks.push({t:performance.now(), how:'track'}); } },false);
  addEventListener('touchend',e=>{ if(!W.on) return; const me=sw; sw=null; ct(held);
    if(me && !e.defaultPrevented && me.isConnected){
      const checked=me.checked;
      const noToggle = tr && tr.changed && tr.vis===checked;
      if(!noToggle && !(tr && tr.changed && tr.vis===!checked)) W.ticks.push({t:performance.now(), how:'click'});
      swClickAt=performance.now(); W.clicks++; dropNext=true;
      try{ me.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,composed:true,view:window,detail:1})); }catch(err){}
    }
    tr=null; if(!col) col=[]; flush(); },false);
  addEventListener('touchcancel',()=>{ sw=null; tr=null; ct(held); col=null; },true);
  /* Chromium's own click for a touch the switch already clicked is dropped (WebKit sends none); a mouse's release ends at its click */
  addEventListener('click',e=>{ if(e.isTrusted && dropNext){ dropNext=false; W.dropped++; e.stopImmediatePropagation(); e.preventDefault(); } },true);
  addEventListener('click',()=>{ if(col) flush(); },false);
})()"""

# THE RECORDER: the bar's Web Animations (when each is made and when its first frame is drawn: `ready`), every frame, the bar's
# layout box each frame, the touches' events, the screens' builds, the tab sounds, and the layout read inside the bar's own handlers
REC = r"""()=>{ if(window.__rec) return; const R=window.__rec={anims:[],frames:[],builds:[],ev:[],bar:[],sounds:[],reads:{},readsUp:{},on:true};
  const oa=Element.prototype.animate;
  Element.prototype.animate=function(k,o){ const a=oa.apply(this,arguments);
    try{ if(this.closest && this.closest('#bottomtabs')){ const f0=Array.isArray(k)?k[0]:null;
      const kind=f0&&('transform' in f0)?'tf':f0&&('opacity' in f0)?'op':f0&&('scale' in f0)?'sc':'x';
      const last=Array.isArray(k)?k[k.length-1]:null;
      const r={cls:String(this.className&&this.className.baseVal!==undefined?this.className.baseVal:this.className||this.id), kind, t:performance.now(), ready:null, dur:(o&&o.duration)||0, n:Array.isArray(k)?k.length:0, end:last&&last.transform||null};
      R.anims.push(r); if(R.anims.length>6000) R.anims.splice(0,2000);
      a.ready.then(()=>{ r.ready=performance.now(); },()=>{ r.cancel=performance.now(); }); } }catch(e){}
    return a; };
  const bar=document.getElementById('bottomtabs');
  const fr=()=>{ const t=performance.now(); R.frames.push(t); if(R.frames.length>30000) R.frames.splice(0,10000);
    if(R.on && bar && !bar.hidden){ const L=bar.offsetLeft, T=bar.offsetTop, Wd=bar.offsetWidth, Hh=bar.offsetHeight; const p=R.bar[R.bar.length-1];
      if(!p || p[1]!==L || p[2]!==T || p[3]!==Wd || p[4]!==Hh) R.bar.push([t,L,T,Wd,Hh,document.documentElement.classList.contains('vp-stale')?1:0, bar.hidden?1:0]); }
    requestAnimationFrame(fr); }; requestAnimationFrame(fr);
  ['pointerdown','pointerup','touchstart','touchend','click'].forEach(n=>{
    addEventListener(n,e=>{ R.ev.push([n,'c',performance.now()]); },true); addEventListener(n,()=>{ R.ev.push([n,'b',performance.now()]); },false); });
  const ps=window.playSound; window.playSound=function(id){ if(id==='ui.tab.bottom') R.sounds.push(performance.now()); return ps.apply(this,arguments); };
  ['showHome','showProfile','showRankings','openCalendarTab','showCalendarTab','showStatsScreen','showAppearance'].forEach(n=>{ const f=window[n]; if(typeof f!=='function'||f.__w) return;
    const w=function(){ const t=performance.now(); try{ return f.apply(this,arguments); } finally{ R.builds.push([n,t,performance.now()]); } }; w.__w=1; window[n]=w; });
  /* layout read by the page between the bar's own capture and bubble listeners (the press: pointerdown; the release: pointerup..click) */
  let on=null; const cnt=n=>{ if(on){ on[n]=(on[n]||0)+1; } };
  [['getBoundingClientRect',Element.prototype],['getClientRects',Element.prototype]].forEach(([n,p])=>{ const f=p[n]; p[n]=function(){ cnt(n); return f.apply(this,arguments); }; });
  const gcs=window.getComputedStyle; window.getComputedStyle=function(){ cnt('getComputedStyle'); return gcs.apply(window,arguments); };
  ['offsetWidth','offsetHeight','offsetLeft','offsetTop'].forEach(n=>{ const d=Object.getOwnPropertyDescriptor(HTMLElement.prototype,n); if(!d||!d.get) return;
    Object.defineProperty(HTMLElement.prototype,n,{configurable:true,get(){ cnt(n); return d.get.call(this); }}); });
  const nav=document.querySelector('#bottomtabs .bottomtabs-navrow');
  nav.addEventListener('pointerdown',()=>{ on=R.reads={}; },true); nav.addEventListener('pointerdown',()=>{ on=null; },false);
  nav.addEventListener('pointerup',()=>{ on=R.readsUp={}; },true); nav.addEventListener('pointerup',()=>{ on=null; },false);
  /* the bar's frame-rate box is read with the uncounted readers */
  R.H=1;
}"""
# the page's own fallback: a frame not drawn within this long after a release is a frame held back (Low Power Mode, a page in the
# background, here a machine at load 30+), and the screen is built anyway - an order the gate cannot hold against the page
HELD = 400
SEL = {"bottomtab-home": "home", "bottomtab-profile": "profile", "bottomtab-rewards": "rewards", "bottomtab-calendar": "calendar", "bottomtab-settings": "settings"}
STATE = """()=>{ const bar=document.getElementById('bottomtabs'); const H=window.__H; const act=[...bar.querySelectorAll('.bottomtab.active')].map(t=>t.id);
  const sl=bar.querySelector('.bottomtabs-slider'), lens=document.getElementById('bottomtabs-lens');
  const sr=H.gbcr.call(sl); const under=[...bar.querySelectorAll('.bottomtab')].filter(t=>!t.hidden&&H.gbcr.call(t).width).map(t=>{ const r=H.gbcr.call(t); return [t.id, Math.abs((r.left+r.width/2)-(sr.left+sr.width/2))]; }).sort((a,b)=>a[1]-b[1]);
  const st=document.getElementById('stage');
  const scr=st.querySelector('.screen-home-actual')?'home':st.querySelector('.screen-calendar-tab')?'calendar':st.querySelector('.screen-rankings')?'rewards':st.querySelector('.screen-profile .profile-settings-tab:not([hidden])')?'settings':st.querySelector('.screen-profile')?'profile':'other';
  return { active:act, platter: under[0]?under[0][0]:null, off: under[0]?Math.round(under[0][1]*10)/10:null, platterOp: +H.gcs.call(window,sl).opacity,
    lensUp: lens.classList.contains('is-up'), lensOp: +H.gcs.call(window,lens).opacity, held: document.documentElement.classList.contains('tab-held'), screen: scr,
    pend: !!bar._navPend, stale: document.documentElement.classList.contains('vp-stale'), y: Math.round(scrollY) }; }"""

def boot(br, url, w=440, h=956, dpr=3, kind="iphone", insets=(62, 0, 34, 0), installed=True):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0402"; d["firstName"] = "Casey"; d["novaMet"] = 99
    touch = kind in ("iphone", "ipad")
    kw = dict(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=touch, is_mobile=touch)
    if kind == "ipad": kw["user_agent"] = UA_IPAD
    if kind == "desk": kw["user_agent"] = UA_DESK
    ctx = br.new_context(**kw)
    ctx.add_init_script(HREAD); ctx.add_init_script(WK)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    if kind == "iphone": ctx.add_init_script(IPH)
    if kind == "ipad": ctx.add_init_script(IPAD)
    pg = ctx.new_page(); body = g["patched"](insets)
    bm = re.search(r'const APP_BUILD = "([^"]+)"', body)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda route, request, b=(bm.group(1) if bm else ""): route.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % b))
    pg.add_init_script("""(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
     localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0402');
     ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
     localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); localStorage.setItem('class26e.a2hs','1790500000000'); localStorage.setItem('class26e.intro.seen','9'); })()""" % json.dumps(json.dumps(d)))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('.rs-spot,.intro-pop,#intro-pop,.unlock-card').forEach(n=>n.remove()); }")
    pg.evaluate(REC)
    cdp = ctx.new_cdp_session(pg)
    # every tab's screen once (first builds are not what is measured), back to Home, the haptic layer in
    # (the bar changes shape between screens on a wide screen - the Start pill joins it on Home - so a tab is found where it is now)
    for tid in ("bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar", "bottomtab-settings", "bottomtab-home"):
        T = tabs(pg)
        if tid in T: click_tab(pg, cdp, kind, T[tid]); pg.wait_for_timeout(1400); settle(pg)
    pg.wait_for_timeout(1500)
    return ctx, pg, cdp, errs

def tabs(pg):
    return pg.evaluate("""()=>Object.fromEntries([...document.querySelectorAll('#bottomtabs .bottomtab')].filter(t=>!t.hidden && window.__H.gbcr.call(t).width).map(t=>{ const r=window.__H.gbcr.call(t); return [t.id,[r.left+r.width/2, r.top+r.height/2, r.width]]; }))""")
def touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if typ == "touchEnd" else [{"x": x, "y": y}]})
def tap(cdp, x, y, hold=0.07):
    touch(cdp, "touchStart", x, y); time.sleep(hold); touch(cdp, "touchEnd")
def mouse_click(pg, x, y, hold=0.07):
    pg.mouse.move(x, y); pg.mouse.down(); time.sleep(hold); pg.mouse.up()
def click_tab(pg, cdp, kind, t, hold=0.07):
    if kind == "desk": mouse_click(pg, t[0], t[1], hold)
    else: tap(cdp, t[0], t[1], hold)
def slide(cdp, x0, x1, y, dur=0.45, rest=0.25, back=False):
    touch(cdp, "touchStart", x0, y)
    if rest: time.sleep(rest)
    n = max(8, int(dur / 0.016))
    for k in range(1, n + 1):
        u = k / n; s = (0.5 - 0.5 * math.cos(u * math.pi * (2 if back else 1)))
        touch(cdp, "touchMove", x0 + (x1 - x0) * s, y); time.sleep(dur / n)
    time.sleep(0.03); touch(cdp, "touchEnd")
def now(pg): return pg.evaluate("()=>performance.now()")
def settle(pg, most=25.0):
    """wait (on a busy shared machine, as long as it takes) until the bar is at rest: glass down, nothing held, no screen waiting"""
    t = time.time()
    while time.time() - t < most:
        st = pg.evaluate("()=>{ const b=document.getElementById('bottomtabs'), l=document.getElementById('bottomtabs-lens'); if(!b || !l) return true; return l.classList.contains('is-up') || document.documentElement.classList.contains('tab-held') || !!b._navPend || b.classList.contains('lens-up'); }")
        if not st: break
        time.sleep(0.25)
    pg.wait_for_timeout(350)
def rec(pg): return pg.evaluate("()=>{ const R=window.__rec; return {anims:R.anims, frames:R.frames.slice(-3000), builds:R.builds, ev:R.ev.slice(-400), bar:R.bar, sounds:R.sounds, reads:R.reads, readsUp:R.readsUp, ticks:window.__WK.ticks}; }")

def one_action(r, t0):
    """what the last touch did, from t0: press, release, the lift and landing tracks, the build, the frames"""
    ev = [e for e in r["ev"] if e[2] >= t0]
    down = next((e[2] for e in ev if e[0] == "pointerdown" and e[1] == "c"), None)
    up = next((e[2] for e in ev if e[0] == "pointerup" and e[1] == "c"), None)
    an = [a for a in r["anims"] if a["t"] >= t0 and a["kind"] == "tf" and "tab-lens" in a["cls"]]
    lift = next((a for a in an if down is not None and a["t"] >= down and (up is None or a["t"] < up)), None)
    land = next((a for a in an if up is not None and a["t"] >= up), None)
    build = next((b for b in r["builds"] if up is not None and b[1] >= up), None)
    fu = next((f for f in r["frames"] if up is not None and f > up), None)
    fd = next((f for f in r["frames"] if down is not None and f > down), None)
    fr = [f for f in r["frames"] if down is not None and down <= f <= down + 1200]
    gaps = [round(b - a) for a, b in zip(fr, fr[1:])]
    return dict(down=down, up=up, lift=lift, land=land, build=build, fu=fu, fd=fd, gaps=gaps)

def expect_state(st, tid):
    want = SEL[tid]
    return (st["active"] == [tid] and st["platter"] == tid and (st["off"] is not None and st["off"] <= 1.0) and not st["lensUp"] and st["lensOp"] < 0.05
            and st["platterOp"] > 0.95 and not st["held"] and st["screen"] == want and not st["pend"] and not st["stale"])

# ------------------------------------------------------------------ (T) taps
def part_T(br, url):
    ctx, pg, cdp, errs = boot(br, url)
    T = tabs(pg); ids = [t for t in ("bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar") if t in T]
    pairs = [(a, b) for a in ids for b in ids if a != b]
    if QUICK: pairs = pairs[:6]
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(600)
    cur = pg.evaluate(STATE)["active"][0]
    res = []
    for rep in range(1 if QUICK else 2):
        for a, b in pairs:
            if cur != a:
                tap(cdp, *T[a][:2]); pg.wait_for_timeout(1700); settle(pg); cur = a
            pg.evaluate("()=>{ window.__rec.reads={}; window.__rec.readsUp={}; }")
            t0 = now(pg); tap(cdp, *T[b][:2]); pg.wait_for_timeout(1800); settle(pg); cur = b
            r = rec(pg); x = one_action(r, t0); st = pg.evaluate(STATE)
            x["reads"] = r["reads"]; x["readsUp"] = r["readsUp"]; x["st"] = st; x["pair"] = (a, b); x["landed"] = expect_state(st, b)
            res.append(x)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    nm = lambda p: "%s>%s" % (p[0].replace("bottomtab-", ""), p[1].replace("bottomtab-", ""))
    # a Web Animation reaches the compositor with the frame drawn after it is made (WebKit: the next rendering update), so the landing
    # is on its way when it was made in the release and a frame came between the release and the build
    order_bad = [(nm(x["pair"]), x["build"][0], round(x["land"]["t"] - x["up"]) if x["land"] else None, round(x["fu"] - x["up"]) if x["fu"] else None,
                  round(x["build"][1] - x["up"])) for x in res
                 if x["build"] and (not x["land"] or not x["fu"] or x["land"]["t"] > x["fu"] or (x["fu"] > x["build"][1] and x["fu"] - x["up"] <= HELD))]
    chk("T1 TAPS: the glass's landing is made in the release and handed to the compositor (a frame drawn) before the new screen is built, on all %d taps at 4x CPU [tap, screen, landing made / frame / build, ms after the release]" % len(res),
        not order_bad, order_bad[:8])
    # (a frame that does not come within HELD ms is a frame held back - the page's own timer then builds the screen anyway, by design)
    frame_bad = [(nm(x["pair"]), round(x["fu"] - x["up"]) if x["fu"] else None, round(x["build"][1] - x["up"])) for x in res if x["build"] and x["fu"] and x["fu"] > x["build"][1] and x["fu"] - x["up"] <= HELD]
    held = [x for x in res if x["build"] and x["fu"] and x["fu"] > x["build"][1] and x["fu"] - x["up"] > HELD]
    if held: info("%d tap(s) had their frame held back past %dms by the machine (built by the page's own fallback timer, by design)" % (len(held), HELD))
    chk("T2 TAPS: the first frame after the release comes before the build, every tap (%d)" % len(res), not frame_bad, frame_bad[:8])
    rd = [(nm(x["pair"]), x["reads"], x["readsUp"]) for x in res if sum(x["reads"].values()) or sum(x["readsUp"].values())]
    chk("T3 TAPS: the bar's own press and release handlers read no layout (no box, offset or computed style: each one is a forced style pass and layout of the page before the glass's first frame)", not rd, rd[:4])
    land_bad = [(nm(x["pair"]), x["st"]) for x in res if not x["landed"]]
    chk("T4 TAPS: every tap lands - that tab lit, the platter under it (1px), the glass down, nothing held, its screen up (%d)" % len(res), not land_bad, land_bad[:4])
    lifts = [round(x["lift"]["ready"] - x["down"]) for x in res if x["lift"] and x["lift"]["ready"]]
    fds = [round(x["fd"] - x["down"]) for x in res if x["fd"]]
    allg = [gg for x in res for gg in x["gaps"]]
    info("press to the lift's first frame at 4x: median %s ms, worst %s (n=%d); press to the next frame median %s; frame gaps in the 1.2s after a press: median %s, p95 %s, worst %s"
         % (statistics.median(lifts) if lifts else None, max(lifts) if lifts else None, len(lifts), statistics.median(fds) if fds else None,
            statistics.median(allg) if allg else None, sorted(allg)[int(len(allg) * .95)] if allg else None, max(allg) if allg else None))
    chk("T5 TAPS: no page error", not errs, errs[:3])
    ctx.close()

# ------------------------------------------------------------------ (R) rapid and random
def part_R(br, url):
    ctx, pg, cdp, errs = boot(br, url)
    T = tabs(pg); ids = [t for t in ("bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar") if t in T]
    rnd = random.Random(384102)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(600)
    pg.evaluate("()=>{ window.__rec.bar=[]; }")
    bursts = 6 if QUICK else 18
    bad = []; n_taps = n_slides = 0
    for bi in range(bursts):
        st0 = pg.evaluate(STATE); cur = st0["active"][0] if st0["active"] else "bottomtab-home"
        # some bursts start mid-scroll (a long screen scrolled and still moving)
        if bi % 3 == 1:
            pg.evaluate("()=>{ const d=document.createElement('div'); d.className='__tall'; d.style.cssText='height:2400px;pointer-events:none'; (document.querySelector('#stage .panel')||document.body).appendChild(d); window.scrollTo({top:900, behavior:'smooth'}); }")
            time.sleep(0.12)
        last = cur
        for k in range(rnd.randint(3, 8)):
            if rnd.random() < 0.25:
                frm = last
                to = rnd.choice([t for t in ids if t != frm])
                slide(cdp, T[frm][0], T[to][0], T[frm][1], dur=rnd.uniform(.2, .55), rest=rnd.choice([0, .05, .25]))
                last = to; n_slides += 1
            else:
                to = rnd.choice(ids)
                tap(cdp, T[to][0], T[to][1], hold=rnd.uniform(.03, .12)); last = to; n_taps += 1
            time.sleep(rnd.uniform(.03, .45))
        pg.wait_for_timeout(2600); settle(pg)
        st = pg.evaluate(STATE)
        if not expect_state(st, last): bad.append((bi, last.replace("bottomtab-", ""), st))
        pg.evaluate("()=>{ document.querySelectorAll('.__tall').forEach(n=>n.remove()); }")
    r = rec(pg)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    chk("R1 RAPID: after each of %d bursts (%d taps, %d slides, 30-450ms apart, some mid-scroll) the bar ends on the last tab chosen: lit, platter under it, glass down, nothing held, its screen up" % (bursts, n_taps, n_slides),
        not bad, bad[:3])
    boxes = {tuple(b[1:5]) for b in r["bar"]}
    chk("R2 RAPID: the bar's own box (layout position and size) never changed in any frame through all of it (%d distinct: %s)" % (len(boxes), sorted(boxes)[:4]),
        len(boxes) <= 1 and not any(b[5] for b in r["bar"]), r["bar"][:6])
    # scrolls and a rubber band (the visual viewport carried past the layout one, as iOS reports it in a stretch), a finger on the page
    pg.evaluate("()=>{ window.__rec.bar=[]; }")
    pg.evaluate("()=>{ try{ Object.defineProperty(window.visualViewport,'offsetTop',{ get(){ return window.__vvTop||0; }, configurable:true }); }catch(e){} }")
    for name in ("showProfile", "showRankings"):
        pg.evaluate("()=>%s()" % name); pg.wait_for_timeout(1500)
        pg.evaluate("()=>{ const d=document.createElement('div'); d.className='__tall'; d.style.cssText='height:2400px;pointer-events:none'; (document.querySelector('#stage .panel')||document.body).appendChild(d); }")
        touch(cdp, "touchStart", 220, 400)
        for k, v in enumerate([0, 40, 120, 220, 160, 60, 0, 30, 0]):
            pg.evaluate("(v)=>{ window.__vvTop=v; window.scrollTo({top: v*3, behavior:'instant'}); visualViewport.dispatchEvent(new Event('scroll')); window.dispatchEvent(new Event('scroll')); }", v)
            touch(cdp, "touchMove", 220, 400 - 20 * (k + 1)); time.sleep(0.05)
        touch(cdp, "touchEnd"); pg.wait_for_timeout(1500)
        pg.evaluate("()=>{ document.querySelectorAll('.__tall').forEach(n=>n.remove()); window.__vvTop=0; window.scrollTo(0,0); }")
    r2 = rec(pg)
    boxes2 = {tuple(b[1:5]) for b in r2["bar"]}
    chk("R3 SCROLL: through scrolls and a rubber band with a finger on the page the bar's box never moved (%d distinct) and was never taken up (vp-stale)" % len(boxes2),
        len(boxes2) <= 1 and not any(b[5] for b in r2["bar"]), r2["bar"][:6])
    chk("R4 no page error", not errs, errs[:3])
    ctx.close()

# ------------------------------------------------------------------ (S) tap and slide the same
def part_S(br, url):
    ctx, pg, cdp, errs = boot(br, url)
    T = tabs(pg); ids = [t for t in ("bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar") if t in T]
    has_sw = pg.evaluate("()=>[...document.querySelectorAll('#bottomtabs .bottomtab')].filter(t=>!t.hidden).every(t=>!!t.querySelector(':scope > input.nova-hsw[switch]'))")
    chk("S0 every tab carries its native switch (the haptic layer is on, as on his iPhone)", has_sw)
    pairs = [(a, b) for a in ids for b in ids if a != b]
    if QUICK: pairs = [p for i, p in enumerate(pairs) if i % 2 == 0]
    out = []
    for a, b in pairs:
        st = pg.evaluate(STATE)
        if st["active"] != [a]: tap(cdp, *T[a][:2]); pg.wait_for_timeout(1700); settle(pg)
        # the slide: rests past the switch's 200ms "held" timer, then slides to b and lets go there
        t0 = now(pg); slide(cdp, T[a][0], T[b][0], T[a][1], dur=0.45, rest=0.25); pg.wait_for_timeout(1700); settle(pg)
        r = rec(pg); x = one_action(r, t0); st = pg.evaluate(STATE)
        ticks = [k for k in r["ticks"] if k["t"] >= t0]; snd = [s for s in r["sounds"] if s >= t0]
        out.append(dict(kind="slide", pair=(a, b), ticks=ticks, up=x["up"], snd=snd, land=x["land"], landed=expect_state(st, b), st=st))
        # the tap back to a, and a tap to b again to compare its landing
        tap(cdp, *T[a][:2]); pg.wait_for_timeout(1700); settle(pg)
        t1 = now(pg); tap(cdp, *T[b][:2]); pg.wait_for_timeout(1700); settle(pg)
        r = rec(pg); x = one_action(r, t1); st = pg.evaluate(STATE)
        ticks = [k for k in r["ticks"] if k["t"] >= t1]; snd = [s for s in r["sounds"] if s >= t1]
        out.append(dict(kind="tap", pair=(a, b), ticks=ticks, up=x["up"], snd=snd, land=x["land"], landed=expect_state(st, b), st=st))
    # a slide that goes out and comes back to where it began, let go there: nothing chosen, nothing felt
    back = []
    for a in ids[:2 if QUICK else 4]:
        st = pg.evaluate(STATE)
        if st["active"] != [a]: tap(cdp, *T[a][:2]); pg.wait_for_timeout(1700); settle(pg)
        other = ids[(ids.index(a) + 1) % len(ids)]
        t0 = now(pg); slide(cdp, T[a][0], T[other][0], T[a][1], dur=0.6, rest=0.25, back=True); pg.wait_for_timeout(1500); settle(pg)
        r = rec(pg); st = pg.evaluate(STATE)
        back.append(dict(a=a, ticks=[k for k in r["ticks"] if k["t"] >= t0], snd=[s for s in r["sounds"] if s >= t0], st=st, ok=expect_state(st, a)))
    nm = lambda p: "%s>%s" % (p[0].replace("bottomtab-", ""), p[1].replace("bottomtab-", ""))
    sl = [o for o in out if o["kind"] == "slide"]; tp = [o for o in out if o["kind"] == "tap"]
    one_at_release = lambda o: len(o["ticks"]) == 1 and o["up"] is not None and o["ticks"][0]["t"] >= o["up"] and o["ticks"][0]["how"] == "click"
    bad_sl = [(nm(o["pair"]), [(k["how"], round(k["t"] - o["up"]) if o["up"] else None) for k in o["ticks"]]) for o in sl if not one_at_release(o)]
    chk("S1 SLIDE: a slide that lands on another tab gets exactly one haptic, at the release - none while the finger travels (the switch it started on never tracks the finger) [slide, (how, ms from the release)] (%d slides)" % len(sl),
        not bad_sl, bad_sl[:8])
    bad_tp = [(nm(o["pair"]), [(k["how"], round(k["t"] - o["up"]) if o["up"] else None) for k in o["ticks"]]) for o in tp if not one_at_release(o)]
    chk("S2 TAP: a tap gets exactly one haptic, at the release (%d taps)" % len(tp), not bad_tp, bad_tp[:8])
    bad_back = [(b["a"].replace("bottomtab-", ""), [(k["how"]) for k in b["ticks"]], len(b["snd"]), b["ok"]) for b in back if b["ticks"] or b["snd"] or not b["ok"]]
    chk("S3 SLIDE: let go where it began, nothing is chosen, nothing is felt and nothing is heard (%d)" % len(back), not bad_back, bad_back[:4])
    bad_snd = [(o["kind"], nm(o["pair"]), len(o["snd"])) for o in out if len(o["snd"]) != 1 or (o["up"] and o["snd"][0] < o["up"] - 1)]
    chk("S4 one tab sound for each tap and each slide, at the release (%d)" % len(out), not bad_snd, bad_snd[:6])
    # the landing: the same shrink into the platter (same final transform, same settle after the glass has arrived)
    same = []
    for (a, b) in pairs:
        s = next(o for o in sl if o["pair"] == (a, b)); t = next(o for o in tp if o["pair"] == (a, b))
        if not (s["land"] and t["land"]): same.append((nm((a, b)), "no landing track", bool(s["land"]), bool(t["land"]))); continue
        if s["land"]["end"] != t["land"]["end"]: same.append((nm((a, b)), "ends differ", s["land"]["end"], t["land"]["end"]))
    chk("S5 tap and slide land the same: the glass's landing track ends on the same transform for each pair (%d pairs)" % len(pairs), not same, same[:4])
    lands = [(nm(o["pair"]), o["kind"]) for o in out if not o["landed"]]
    chk("S6 every slide and tap lands (lit, platter, glass down, screen) (%d)" % len(out), not lands, lands[:4])
    tm = pg.evaluate("""()=>{ const nav=document.querySelector('#bottomtabs .bottomtabs-navrow'); const sw=nav.querySelector('.bottomtab.active > .nova-hsw') || nav.querySelector('.nova-hsw');
      const t=new Touch({identifier:91,target:sw,clientX:10,clientY:10}); const e=new TouchEvent('touchmove',{bubbles:true,cancelable:true,touches:[t],targetTouches:[t],changedTouches:[t]});
      window.__WK.on=false; sw.dispatchEvent(e); window.__WK.on=true; return e.defaultPrevented; }""")
    info("a touchmove on a tab's switch has its default prevented (the switch never tracks a finger on the bar): %s" % tm)
    chk("S7 no page error", not errs, errs[:3])
    ctx.close()

# ------------------------------------------------------------------ (D) every size
DEVS = [("iPhone SE (2nd/3rd)", 375, 667, 2, "iphone", (20, 0, 0, 0)), ("iPad Pro 11\"", 834, 1194, 2, "ipad", (24, 0, 20, 0)),
        ("laptop 1366x768", 1366, 768, 1, "desk", (0, 0, 0, 0)), ("monitor 2560x1440", 2560, 1440, 1, "desk", (0, 0, 0, 0))]
def part_D(br, url):
    for label, w, h, dpr, kind, ins in DEVS:
        # a timing run on a shared machine is run once more before it is called a failure (the coordinator's rule); the second run counts
        for attempt in range(2):
            res = d_device(br, url, label, w, h, dpr, kind, ins)
            if (not res[0] and not res[1] and not res[2]) or attempt == 1: break
            info("D %s: run again (the first run: %s)" % (label, str(res)[:300]))
        bad_o, bad_l, errs, seq = res
        chk("D %s: the bar's answer is drawn before the screen is built, every %s (%d)" % (label, "click" if kind == "desk" else "tap", len(seq)), not bad_o, bad_o[:5])
        chk("D %s: every %s lands on its tab (lit, platter, glass down, screen)" % (label, "click" if kind == "desk" else "tap"), not bad_l, bad_l[:3])
        chk("D %s: no page error" % label, not errs, errs[:3])

def d_device(br, url, label, w, h, dpr, kind, ins):
    if True:
        ctx, pg, cdp, errs = boot(br, url, w, h, dpr, kind, ins, installed=(kind != "desk"))
        T = tabs(pg); ids = [t for t in ("bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar") if t in T]
        seq = ["bottomtab-profile", "bottomtab-rewards", "bottomtab-home", "bottomtab-calendar", "bottomtab-profile", "bottomtab-home"] if QUICK else \
              ["bottomtab-profile", "bottomtab-rewards", "bottomtab-home", "bottomtab-calendar", "bottomtab-profile", "bottomtab-home", "bottomtab-rewards", "bottomtab-calendar", "bottomtab-home"]
        # (Home's own first seconds after the warm-up - its after-build work and late arrivals - are not what is measured)
        pg.wait_for_timeout(3000); settle(pg)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.wait_for_timeout(600)
        bad_o, bad_l = [], []
        for to in seq:
            if to not in T: continue
            T = tabs(pg)
            t0 = now(pg); click_tab(pg, cdp, kind, T[to]); pg.wait_for_timeout(1800); settle(pg)
            # a press the page never received (no pointerdown reached it: the harness's input lost on a loaded machine) is sent again;
            # a press that reached the page and did not land is the page's failure
            if not pg.evaluate("(t0)=>window.__rec.ev.some(e=>e[0]==='pointerdown' && e[1]==='c' && e[2]>=t0)", t0):
                info("D %s: the press on %s never reached the page; sent again" % (label, to))
                t0 = now(pg); click_tab(pg, cdp, kind, T[to]); pg.wait_for_timeout(1800); settle(pg)
            r = rec(pg); x = one_action(r, t0); st = pg.evaluate(STATE)
            if x["build"] and x["fu"] and x["fu"] > x["build"][1] and x["fu"] - x["up"] <= HELD: bad_o.append((to.replace("bottomtab-", ""), round(x["fu"] - x["up"]), round(x["build"][1] - x["up"])))
            if x["build"] and kind != "desk" and (not x["land"] or not x["fu"] or x["land"]["t"] > x["fu"]): bad_o.append((to.replace("bottomtab-", ""), "no landing made in the release"))
            if not expect_state(st, to): bad_l.append((to.replace("bottomtab-", ""), st))
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        ctx.close()
        return bad_o, bad_l, errs, seq

srv, url = g["serve"]()
try:
    for name, fn in (("T", part_T), ("S", part_S), ("R", part_R), ("D", part_D)):
        if name not in ONLY: continue
        # one browser a part; a part whose page the shared machine kills ("Target crashed", the page closed) is run again, whole
        for attempt in range(3):
            print("== %s%s" % (name, "" if not attempt else " (again: the page was lost to the machine's load)"), flush=True)
            try:
                with sync_playwright() as pw:
                    br = pw.chromium.launch(executable_path=g["CHROME"])
                    try: fn(br, url)
                    finally:
                        try: br.close()
                        except Exception: pass
                break
            except Exception as e:
                m = repr(e).lower()
                if attempt < 2 and ("crash" in m or "closed" in m or "destroyed" in m): continue
                raise
finally:
    srv.shutdown()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
