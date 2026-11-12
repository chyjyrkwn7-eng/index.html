#!/usr/bin/env python3
"""Build 384.84: HOME STAYS PUT UNDER A SWIPE; THE PINNED CHROME IS NOT MOVED BY A RUBBER BAND.

Madison's 384.82 recording of Home (iPhone 17 Pro Max, installed, the rubber band back): at each swipe the content stretched a long way
and snapped back to the same place every time (a rubber band, not a scroll: Home fits), but the tab bar, the daily "?" and the class
bubble went DOWN, off the foot of the screen, and came back as the stretch let go; and as a big stretch let go the planet system was
missing for a few frames. The bar's move was barSelfHeal (384.62): in a rubber band iOS reports the visual viewport past the layout one
(offsetTop > 0) while its compositor keeps the pinned chrome where it belongs, so the follower read the stretch as a displacement and
took it up (a negative bottom margin by the stretch), and on its first take-up it also sent a synthetic resize, which rewrites the
hero's own style (repositionTopNotices) mid-bounce. 384.84: the follower changes nothing while a finger is down, while the page or the
visual viewport is moving, for 900ms after the finger lifts, or while the page stands past an end; a displacement still there at rest
is taken up as before.

 (1) FITS     Home's document is no taller than the window (scrollHeight <= innerHeight + 1) on every device of the sweep matrix
              (tools/sweep-layout.py's DEVICES: installed, in a browser and Safari's bars over the page; portrait and landscape; his
              85% zoom is the "@85%" entry). Passes on 384.82 too: Home did not scroll there either; the travel is the stretch.
 (2) STILL    on Home, Profile, the Leaderboard, the Calendar, Settings and a question (440x956 installed, and 518x1126 at his zoom on
              Home): a touch goes down, the visual viewport stretches past the layout one (offsetTop 0 -> 240 -> 0, what iOS reports in a
              rubber band) while the page scrolls where it can, the finger lifts and the stretch snaps back; in every frame the tab bar,
              the daily "?", the class bubble, the chat button, the top strip, Pause / the test header and the version label are where
              they were at rest (within 1px), the page sends no resize of its own, the hero's style is not written, and nothing is left
              taken up. FAILS on 384.82 (the bar and the corner buttons carried down by the stretch, a resize sent).
 (3) PLANETS  Home's planet system (the hero, its orbit and sphere) is the same node, displayed, visible and not faded in every frame of
              (2), after programmatic scrolls past both ends and a wheel. (Not reproducible as a failure in Chromium: the frames where
              his phone drew no planets are WebKit's raster, not a page state; the app-side triggers mid-bounce are (2)'s resize and
              hero-style checks.)
 (4) AT REST  the follower still works where it was written for: a visual viewport left 200px past the layout one with the page still
              (the 384.62 state) is taken up within 1.5s and undone when it clears.
Run:  python3 tools/check-b384-homescroll.py [--quick] [--against OLD/index.html]"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
spec2 = importlib.util.spec_from_file_location("sw", os.path.join(HERE, "sweep-layout.py")); sw = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(sw)
args = sys.argv[1:]
QUICK = "--quick" in args
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
_bm = re.search(r'const APP_BUILD = "([^"]+)"', RAW)
if _bm: cb.SERVED_BUILD = _bm.group(1)
def serve_with(t, r, b, l):
    ins = {"top": "%gpx" % t, "right": "%gpx" % r, "bottom": "%gpx" % b, "left": "%gpx" % l}
    cb.BODY = cb.INSET_RE.sub(lambda m: ins[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');")
UNOWE = "()=>{ try{ const u=pendingHomeUnlocks(); markUnlocksShown(u.chars,u.banners,u.fx); }catch(e){} try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('.rs-spot,.intro-pop,#intro-pop,.unlock-card').forEach(n=>n.remove()); document.body.classList.remove('cutscene-focus'); }"
errs = []

# ---------------------------------------------------------------- (1) FITS
def matrix(br):
    devices = [d for d in sw.DEVICES if d[0] in sw.QUICK or "@85%" in d[0] or "Pro Max" in d[0]] if QUICK else sw.DEVICES
    combos = list(sw.combinations(devices)); bad = []; worst = {}
    # his own phone with the opaque status bar (the ?sbs=default icon): the page starts under the bar, so no top inset and 59pt less height
    combos += [("iPhone 17 Pro Max, opaque status bar", "portrait", "home screen", 440, 897, (0, 0, 34, 0), (0, 0, 34, 0), "ios-phone", (440, 956)),
               ("iPhone 17 Pro Max @85% zoom, opaque status bar", "portrait", "home screen", 518, 1056, (0, 0, 40, 0), (0, 0, 40, 0), "ios-phone", (440, 956))]
    for label, orientation, mode, vw, vh, insets, audit, platform, scr in combos:
        serve_with(*insets)
        touch = platform != "desktop"
        ctx = br.new_context(viewport={"width": vw, "height": vh}, screen={"width": scr[0], "height": scr[1]},
                             user_agent=sw.ua_for(label, platform, vw, vh), has_touch=touch, is_mobile=touch)
        ctx.add_init_script(sw.SEED); ctx.add_init_script("try{%s}catch(e){}" % SEEN)
        if platform == "ios-tablet": ctx.add_init_script(sw.TOUCH_POINTS)
        if mode == "home screen": ctx.add_init_script(sw.STANDALONE)
        pg = cb.open_page(ctx)
        try:
            pg.goto(cb.URL); pg.wait_for_timeout(2400)
            pg.evaluate("()=>document.getElementById('splashscreen')?.remove()"); pg.evaluate(UNOWE)
            pg.evaluate("()=>{ showHome(); scrollTo(0,0); }"); pg.wait_for_timeout(1300)
            r = pg.evaluate("()=>{ const se=document.scrollingElement; return [se.scrollHeight, innerHeight, !!document.querySelector('.cosmic-hero-wrap')]; }")
        except Exception as e:
            r = [None, None, str(e)[:80]]
        tag = "%s, %s, %s (%dx%d)" % (label, orientation, mode, vw, vh)
        over = (r[0] - r[1]) if r[0] is not None else None
        worst[tag] = over
        if over is None or over > 1 or r[2] is not True: bad.append([tag, r])
        ctx.close()
    for b in bad: print("   over:", b[0], b[1], flush=True)
    chk("FITS: Home's document is no taller than the window on all %d combinations of the matrix (installed / browser / bars over, both orientations, his 85%% zoom); over the window: %s"
        % (len(combos), sorted(set(v for v in worst.values() if v is not None))), not bad, bad[:8])

# ---------------------------------------------------------------- (2)-(4)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
VVM = "window.__vvm = {top: 0}; try{ Object.defineProperty(window.visualViewport, 'offsetTop', { get(){ return window.__vvm.top; }, configurable: true }); }catch(e){}"
CHROME_SEL = ["#bottomtabs", ".daily-question-fab", ".class-bubble-wrap", "#chatdock-btn", "#top-edge", "#pausebtn", ".wrap.test-pinned > .top", ".homeversion", ".backtotop"]
GESTURE = """async (args)=>{
  const SEL = %s, scrollable = args.scrollable;
  const raf2 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const rects = () => { const o = {}; for(const s of SEL){ const e = document.querySelector(s); if(!e) continue; const cs = getComputedStyle(e);
      if(cs.display === 'none' || cs.visibility !== 'visible') continue; const r = e.getBoundingClientRect(); if(!r.width || !r.height) continue;
      o[s] = [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; } return o; };   /* centres: the back-to-top button scales as it comes in */
  const hero0 = document.querySelector('.cosmic-hero-wrap');
  const heroOk = () => { if(!hero0) return null; const h = document.querySelector('.cosmic-hero-wrap'); if(h !== hero0 || !h.isConnected) return 'replaced';
      let e = h; while(e && e !== document.body){ const cs = getComputedStyle(e); if(cs.display === 'none') return 'display:none on ' + e.className; if(cs.visibility !== 'visible') return 'hidden on ' + e.className; if(+cs.opacity < .9) return 'opacity ' + cs.opacity + ' on ' + e.className; e = e.parentElement; }
      const r = h.getBoundingClientRect(); if(r.height < 100) return 'height ' + r.height;
      for(const s of ['.cosmic-hero-orbitlayer', '.cosmic-sphere, .cosmic-hero-sphere, .cosmic-hero-core']){ const x = h.querySelector(s); if(!x) continue; const cs = getComputedStyle(x); if(cs.display === 'none' || cs.visibility !== 'visible') return s + ' hidden'; }
      return 'ok'; };
  let resizes = 0; const onR = () => resizes++; addEventListener('resize', onR);
  let heroWrites = 0; const mo = new MutationObserver(l => { heroWrites += l.length; }); if(hero0) mo.observe(hero0, { attributes: true, attributeFilter: ['style', 'class'] });
  const base = rects(); const frames = []; const hero = [];
  const t = document.documentElement;
  const touch = (type) => { try{ const p = new Touch({ identifier: 7, target: t, clientX: 200, clientY: 500 }); t.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: false, touches: type === 'touchend' ? [] : [p], changedTouches: [p] })); }catch(e){ t.dispatchEvent(new Event(type, { bubbles: true })); } };
  touch('touchstart');
  const up = [0, 15, 40, 70, 100, 130, 160, 190, 215, 235, 240, 240, 240, 236, 230];
  const down = [210, 170, 125, 85, 55, 30, 14, 5, 1, 0, 0, 0];
  let i = 0;
  for(const v of up){ window.__vvm.top = v; if(scrollable) window.scrollTo({ top: 60 * (++i), behavior: 'instant' }); visualViewport.dispatchEvent(new Event('scroll')); window.dispatchEvent(new Event('scroll'));
    await raf2(); await wait(30); frames.push(rects()); hero.push(heroOk()); }
  touch('touchend');
  for(const v of down){ window.__vvm.top = v; if(scrollable) window.scrollTo({ top: 60 * (++i), behavior: 'instant' }); visualViewport.dispatchEvent(new Event('scroll')); window.dispatchEvent(new Event('scroll'));
    await raf2(); await wait(30); frames.push(rects()); hero.push(heroOk()); }
  await wait(1400); frames.push(rects()); hero.push(heroOk());
  removeEventListener('resize', onR); mo.disconnect();
  let worst = 0, where = '';
  for(const f of frames) for(const s in base){ if(!f[s]) { if(s !== '.backtotop'){ worst = Math.max(worst, 999); where = s + ' gone'; } continue; }
    for(let k = 0; k < 2; k++){ const d = Math.abs(f[s][k] - base[s][k]); if(d > worst){ worst = d; where = s + ' ' + JSON.stringify(base[s]) + ' -> ' + JSON.stringify(f[s]); } } }
  const cs = getComputedStyle(document.documentElement);
  return { base, worst, where, resizes, heroWrites, hero, stale: cs.getPropertyValue('--vp-stale').trim(), log: (window.__barHeal || []).slice(-3) };
}""" % (repr(CHROME_SEL),)
QSTART = """()=>{ const u='Identity Crimes'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false; theme.reduceMotion=true;
  beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u)), null); }"""
def boot(br, W, H, scr=(440, 956)):
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": scr[0], "height": scr[1]}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=UA)
    ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');}catch(e){}" % (SEEN, cb.USED_ACCOUNT))
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(VVM)
    pg = cb.open_page(ctx); pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    pg.goto(cb.URL); pg.wait_for_timeout(2500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()"); pg.evaluate(UNOWE); pg.wait_for_timeout(400)
    return ctx, pg
SCREENS = [("Home", "()=>showHome()", False), ("the Profile", "()=>showProfile()", True), ("the Leaderboard", "()=>showRankings()", True),
           ("the Calendar", "()=>showCalendarTab()", True), ("Settings", "()=>showAppearance()", True), ("a question", None, True)]
def gestures(br):
    cases = [(440, 956, (59, 0, 34, 0), s) for s in SCREENS] + [(518, 1126, (73, 0, 40, 0), SCREENS[0]), (440, 897, (0, 0, 34, 0), SCREENS[0]), (518, 1056, (0, 0, 40, 0), SCREENS[0])]
    for W, H, ins, (label, call, scrollable) in cases:
        serve_with(*ins)
        ctx, pg = boot(br, W, H)
        if call: pg.evaluate(call)
        else:
            pg.evaluate("()=>showHome()"); pg.wait_for_timeout(400); pg.evaluate(QSTART); pg.wait_for_selector(".qpanel .choice", timeout=25000)
        pg.wait_for_timeout(1800); pg.evaluate(UNOWE)
        if scrollable:   # the owner's lists are long; the harness gives every scrollable screen the length to scroll through the gesture
            pg.evaluate("()=>{ const d = document.createElement('div'); d.style.cssText = 'height:2400px;pointer-events:none'; (document.querySelector('.wrap') || document.body).appendChild(d); }")
        pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(1500)
        g = pg.evaluate(GESTURE, {"scrollable": scrollable})
        tag = "%s (%dx%d installed)" % (label, W, H)
        chk("STILL %s: through a touch, a stretch of 240px past the layout viewport and its snap-back, the pinned chrome (%s) stays where it was in every frame (worst %dpx: %s)"
            % (tag, ", ".join(g["base"].keys()), g["worst"], g["where"] or "-"), g["worst"] <= 1 and len(g["base"]) >= 2, g["log"])
        chk("STILL %s: the page sent no resize of its own during the gesture (%d) and nothing is left taken up (--vp-stale %r)" % (tag, g["resizes"], g["stale"]),
            g["resizes"] == 0 and not g["stale"], g["log"])
        if label == "Home":
            bad = [h for h in g["hero"] if h != "ok"]
            chk("PLANETS %s: the planet system is the same node, displayed, visible and not faded in all %d frames of the gesture (%s)" % (tag, len(g["hero"]), bad[:3] or "all ok"),
                g["hero"] and not bad, g["hero"])
            chk("PLANETS %s: the hero's own style was not written during the gesture (%d writes)" % (tag, g["heroWrites"]), g["heroWrites"] == 0, g["heroWrites"])
            for y in (400, -120, 2000, 0):
                pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(150)
            for dy in (900, -900, 600, -600): pg.mouse.wheel(0, dy); pg.wait_for_timeout(120)
            pg.wait_for_timeout(500)
            h = pg.evaluate("""()=>{ const h = document.querySelector('.cosmic-hero-wrap'); if(!h) return 'missing'; let e = h; while(e && e !== document.body){ const cs = getComputedStyle(e);
                if(cs.display === 'none' || cs.visibility !== 'visible' || +cs.opacity < .9) return 'hidden at ' + e.className; e = e.parentElement; } const r = h.getBoundingClientRect();
                return [Math.round(r.top), Math.round(r.height), scrollY]; }""")
            chk("PLANETS %s: after scrolls past both ends and a wheel the planet system is there and visible, and Home is back at its top (%s)" % (tag, h),
                isinstance(h, list) and h[1] > 100 and h[2] == 0, h)
        ctx.close()
def at_rest(br):
    serve_with(59, 0, 34, 0)
    ctx, pg = boot(br, 440, 956)
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(2500); pg.evaluate(UNOWE)
    b0 = pg.evaluate("()=>document.querySelector('#bottomtabs').getBoundingClientRect().bottom")
    pg.evaluate("()=>{ window.__vvm.top = 200; visualViewport.dispatchEvent(new Event('scroll')); }"); pg.wait_for_timeout(1500)
    a = pg.evaluate("()=>[getComputedStyle(document.documentElement).getPropertyValue('--vp-stale').trim(), document.querySelector('#bottomtabs').getBoundingClientRect().bottom]")
    pg.evaluate("()=>{ window.__vvm.top = 0; visualViewport.dispatchEvent(new Event('scroll')); }"); pg.wait_for_timeout(1500)
    c = pg.evaluate("()=>[getComputedStyle(document.documentElement).getPropertyValue('--vp-stale').trim(), document.querySelector('#bottomtabs').getBoundingClientRect().bottom]")
    chk("AT REST: a visual viewport left 200px past the layout one with the page still is taken up (--vp-stale %r, the bar %s -> %s) and undone when it clears (%r, %s)" % (a[0], b0, a[1], c[0], c[1]),
        a[0] == "200px" and abs(a[1] - b0 - 200) <= 2 and not c[0] and abs(c[1] - b0) <= 1, [b0, a, c])
    ctx.close()
def run(fn):
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try: fn(br)
        finally:
            try: br.close()
            except Exception: pass
if "--matrix" not in args:
    run(gestures)
    run(at_rest)
if "--gestures" not in args:
    run(matrix)
chk("no page errors", not errs, errs[:4])
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
