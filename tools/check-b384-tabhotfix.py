#!/usr/bin/env python3
"""Build 384.62 (hot fix): THE PINNED CHROME THAT RIDES WITH THE PAGE (the tab bar in the middle of the screen, the test header leaving the top).

Madison, four screen recordings and a screenshot (iPhone 17 Pro Max, installed): the tab bar and the round back-to-top button ride UP the screen with the page as it is
scrolled ("Choose your chapters", the Profile, the Leaderboard) and are home when the page is at its top; on a test question the pinned header (progress strip, Pause, chat)
leaves the top and the page seems to jump. Everything `position:fixed` goes with the document while it is scrolled. Read from the code and driven here: nothing in the app
moves any of it (no script writes a transform / translate / top / bottom on them, no ancestor has a transform, filter, contain, will-change, overflow or zoom) and in Chromium
every one is the same pixel through every fling, rubber band and wheel, so what they are pinned to - WebKit's layout viewport - was not following the page. barSelfHeal now
FOLLOWS: from the visual viewport's offset / height, the short layout viewport of an installed phone and the bar's own foot against its design, it works out how far the pinned
chrome stands from the screen and takes it up frame by frame (a negative bottom margin on what is pinned to the bottom, a margin on the test header, Pause and the notices).
 (1) HELD    on the Leaderboard (given the length his list has), Drill setup "Choose your units" (academy), "Choose your chapters" (Fire Code), the Profile, and a Drill question (answered
             wrongly so the code card opens): through a fling, both rubber bands and a wheel the bar's foot, Pause and .wrap/#stage are constant while nothing scrolls them, and the page
             never nudges the scroll itself while it is being scrolled;
 (2) FOLLOW  the visual viewport left riding below the layout one by the scroll offset (the state in the recordings, simulated through visualViewport.offsetTop): after each scroll step
             (384.84, ON PURPOSE: once the page is still - 350ms after the scroll, a second look 150ms later agreeing; the wait per step is 900ms, was 260 - and not mid-scroll:
             in a rubber band the in-flight reading moved a bar that had not moved; tools/check-b384-homescroll.py holds that) the bar
             and the back-to-top button are back at the screen's bottom (within 6px); and back at design when it clears. (384.77, on purpose: the test header and Pause are NOT
             moved by this reading any more - on the owner's phone it moved them ~100pt down mid-scroll; the reading is logged instead. check-b384-top383 holds that.)
 (3) RIDING  the pinned chrome made to ride with the page (every fixed element translated by -scrollY, the state itself, seen only by the page's own geometry): the page sees it, takes it up
             on both screens' bottoms (384.77: the question's top is logged, not taken up), and is back at design after;
 (4) SHORT   an installed phone whose real layout viewport (686) is 270pt short of its 956pt screen: found and taken up, undone when whole;
 (5) NEVER   with a text field focused, in a Safari tab (797 of 956), at his 518px page zoom, in a healthy page for 5s: nothing logged or moved;
 (6) LOG     every state change is in window.__barHeal and Report a bug carries it in `edges` after BARHEAL (with the visual viewport's scale).
Run:  python3 tools/check-b384-tabhotfix.py   (--against OLD/index.html must FAIL: main 384.48 fails 2, 3, 4, 6)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
args = sys.argv[1:]
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
_bm = re.search(r'const APP_BUILD = "([^"]+)"', RAW)
if _bm: cb.SERVED_BUILD = _bm.group(1)   # --against: version.json says the page's own build, or the update check reloads it mid-run
def serve_with(top, bottom):
    ins = {"top": "%gpx" % top, "bottom": "%gpx" % bottom, "left": "0px", "right": "0px"}
    cb.BODY = cb.INSET_RE.sub(lambda m: ins[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:420], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
UA_TAB = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');")
VVM = ("window.__vvm = {top: 0, follow: false}; try{ Object.defineProperty(window.visualViewport, 'offsetTop', { get(){ return window.__vvm.follow ? Math.min(500, Math.round(window.scrollY)) : window.__vvm.top; }, configurable: true }); }catch(e){}"
       "window.__scrollTos = 0; const _st = window.scrollTo.bind(window); window.scrollTo = function(){ window.__scrollTos++; return _st.apply(window, arguments); };"
       # RIDING: every fixed element carries -scrollY (a stand-in for WebKit holding the layout viewport behind the page)
       "window.__ride = false; addEventListener('scroll', () => { if(!window.__ride) return; for(const e of document.body.querySelectorAll('*')){ if(getComputedStyle(e).position === 'fixed' && !e.matches('.wrap > .top')) e.style.translate = '0 ' + (-window.scrollY) + 'px'; } }, {passive: true});")
def boot(br, W, H, scr=None, standalone=True, ua=UA, mobile=True, ifc=False):
    kw = dict(viewport={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=mobile, user_agent=ua)
    if scr: kw["screen"] = {"width": scr[0], "height": scr[1]}
    ctx = br.new_context(**kw)
    ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');}catch(e){}" % (SEEN, cb.USED_ACCOUNT))
    if standalone: ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(VVM)
    pg = cb.open_page(ctx); pg.goto(cb.URL); pg.wait_for_timeout(2500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); pg.wait_for_timeout(600)
    if ifc:
        try:
            with pg.expect_navigation(timeout=15000):
                pg.evaluate("()=>{ setEnrolled('ifc', true); localStorage.setItem('class26e.greet.ifc', 'done'); switchClass('ifc'); }")
            pg.wait_for_timeout(2800); pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); pg.wait_for_timeout(600)
        except Exception as e:
            print("  (class switch failed: %s)" % str(e)[:100])
    return ctx, pg
QSTART = """()=>{ const u='Identity Crimes'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false; theme.reduceMotion=true;
  beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u)), null); }"""
def show(pg, name):
    if name == "question":
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
        pg.evaluate(QSTART); pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(1200)
        # answer wrongly so the code card / explanation opens
        pg.evaluate("()=>{ const r = correctSlot(order[pos]); const bad = [...document.querySelectorAll('.qpanel .choice')].find(c => +c.dataset.index !== r); bad.click(); }"); pg.wait_for_timeout(1500)
    else:
        pg.evaluate({"board": "()=>showRankings()", "units": "()=>{ cfg.mode='drill'; showSetup(); }", "profile": "()=>showProfile()"}[name]); pg.wait_for_timeout(2200)
    pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot').forEach(n=>n.remove()); }")
    if name in ("board", "question"):   # the owner's board is a long list and a question with its code card is long; the harness gives them the length his have
        pg.evaluate("()=>{ const d = document.createElement('div'); d.style.cssText = 'height:3000px;pointer-events:none'; (document.querySelector('.wrap') || document.body).appendChild(d); }")
S = """()=>{ const R = s => { const e = document.querySelector(s); if(!e) return null; const r = e.getBoundingClientRect(); if(!r.width) return null; return [Math.round(r.top * 10) / 10, Math.round(r.bottom * 10) / 10]; };
  const t = document.querySelector('.backtotop'); const tr = t && getComputedStyle(t).display !== 'none' && +getComputedStyle(t).opacity > .5 ? t.getBoundingClientRect() : null;
  return { bar: R('.bottomtabs'), pause: R('#pausebtn'), top: R('.wrap.test-pinned > .top') || R('.wrap > .top'), wrap: R('.wrap'), stage: R('#stage'), up: tr ? tr.bottom : null,
           stale: getComputedStyle(document.documentElement).getPropertyValue('--vp-stale').trim(), vtop: getComputedStyle(document.documentElement).getPropertyValue('--vp-top').trim(),
           log: (window.__barHeal || []).slice(), ih: innerHeight, y: scrollY, nudges: window.__scrollTos }; }"""
SAMPLE = """()=>{ window.__s = []; window.__run = true; const f = () => { const b = document.querySelector('.bottomtabs'), p = document.querySelector('#pausebtn');
  window.__s.push([b ? Math.round(b.getBoundingClientRect().bottom * 10) / 10 : null, p ? Math.round(p.getBoundingClientRect().top * 10) / 10 : null]); if(window.__run) requestAnimationFrame(f); }; f(); }"""
def retry(fn, tries=3):
    for i in range(tries):
        try:
            with sync_playwright() as pw:
                br = pw.chromium.launch(executable_path=cb.CHROME)
                try: return fn(br)
                finally:
                    try: br.close()
                    except Exception: pass
        except Exception as e:
            if "closed" in repr(e).lower() or "crashed" in repr(e).lower():
                print("  (retry %d: %s)" % (i + 1, repr(e)[:80]), flush=True); continue
            raise
    raise RuntimeError("page kept crashing")
errs = []
SCREENS = (("the Leaderboard", False, "board"), ("Drill setup, Choose your units (academy)", False, "units"), ("Drill setup, Choose your chapters (Fire Code)", True, "units"),
           ("the Profile", False, "profile"), ("a Drill question answered wrongly (the code card open)", False, "question"))
def screens(br):
    for label, ifc, name in SCREENS:
        serve_with(59, 34)
        ctx, pg = boot(br, 440, 956, ifc=ifc)
        pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
        show(pg, name)
        s0 = pg.evaluate(S)
        has_bar = s0["bar"] is not None
        chk("%s: up, pinned chrome found (bar %s, Pause %s, header %s)" % (label, s0["bar"], s0["pause"], s0["top"]), (s0["bar"] is not None) or (s0["pause"] is not None), s0)
        # (1) HELD
        pg.evaluate(SAMPLE)
        for y in (400, 1200, 2400, 900, 5000, 0, 3000, 200):
            pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(120)
        for dy in (800, -300, 1500, -2500, 600):
            pg.mouse.wheel(0, dy); pg.wait_for_timeout(110)
        pg.evaluate("()=>{ window.__run = false; window.__scrollTos = 0; }"); pg.wait_for_timeout(100)
        sm = pg.evaluate("()=>window.__s")
        bs = [x[0] for x in sm if x[0] is not None]; ps = [x[1] for x in sm if x[1] is not None]
        chk("%s: through a fling, both rubber bands and a wheel the bar's foot and Pause stay put in every frame (%d frames; bar %s..%s, Pause %s..%s)" % (label, len(sm), min(bs) if bs else None, max(bs) if bs else None, min(ps) if ps else None, max(ps) if ps else None),
            len(sm) > 40 and (not bs or max(bs) - min(bs) < 1.0) and (not ps or max(ps) - min(ps) < 1.0), [bs[:3], ps[:3]])
        pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(500)
        s1 = pg.evaluate(S)
        chk("%s: at rest the page, .wrap and #stage are where they were (wrap %s -> %s, stage %s -> %s) and nothing was taken up (%r / %r)" % (label, s0["wrap"], s1["wrap"], s0["stage"], s1["stage"], s1["stale"], s1["vtop"]),
            s1["wrap"] == s0["wrap"] and s1["stage"] == s0["stage"] and not s1["stale"] and not s1["vtop"], [s0, s1])
        # (2) FOLLOW: the visual viewport rides below the layout one by the scroll offset
        pg.evaluate("()=>{ window.__vvm.follow = true; window.__scrollTos = 0; }")
        worst_b = worst_t = 0; seen = []
        for y in (150, 350, 500, 900, 400):
            pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(900)   # (384.84) taken up once the page is still, not mid-scroll
            s = pg.evaluate(S); off = min(500, round(s["y"]))
            if s["bar"] and s0["bar"]: worst_b = max(worst_b, abs((s["bar"][1] - s0["bar"][1]) - off))
            # (384.77) THE TOP IS READ, NOT MOVED: Pause (and the header) stay where they are; on his phone this reading moved them ~100pt down mid-scroll
            if s["pause"] and s0["pause"]: worst_t = max(worst_t, abs(s["pause"][0] - s0["pause"][0]))
            seen.append([off, s["bar"] and round(s["bar"][1] - s0["bar"][1]), s["pause"] and round(s["pause"][0] - s0["pause"][0])])
        chk("%s: with the visual viewport riding below by the scroll offset the bar is carried to the screen's foot, and (384.77) the header/Pause stay where they are (worst error bottom %.1f, top %.1f; [offset, bar moved, Pause moved] %s)" % (label, worst_b, worst_t, seen),
            worst_b <= 6 and worst_t <= 6 and (s0["bar"] is not None or s0["pause"] is not None), seen)
        n = pg.evaluate("()=>window.__scrollTos")
        chk("%s: the page did not nudge the scroll while it was being scrolled (%d calls of its own besides the test's %d)" % (label, max(0, n - 5), 5), n - 5 <= 0, n)
        pg.evaluate("()=>{ window.__vvm.follow = false; window.__vvm.top = 0; }"); pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(900)
        s2 = pg.evaluate(S)
        chk("%s: when the viewport comes right everything is back at design (bar %s vs %s, Pause %s vs %s, margins %r/%r)" % (label, s2["bar"], s0["bar"], s2["pause"], s0["pause"], s2["stale"], s2["vtop"]),
            s2["bar"] == s0["bar"] and s2["pause"] == s0["pause"] and not s2["stale"] and not s2["vtop"], [s0, s2])
        # (3) RIDING: every fixed element carries -scrollY
        pg.evaluate("()=>{ window.__ride = true; }")
        worst_b = worst_t = 0; seen = []
        for y in (300, 450, 200):
            pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(1300)
            s = pg.evaluate(S)
            if s["bar"] and s0["bar"]: worst_b = max(worst_b, abs(s["bar"][1] - s0["bar"][1]))
            # (384.77) the top is not taken up any more (it is logged): Pause carries the simulation's own -scrollY and nothing adds a margin to it
            if s["pause"] and s0["pause"]: worst_t = max(worst_t, abs((s["pause"][0] - s0["pause"][0]) + round(s["y"])))
            seen.append([round(s["y"]), s["bar"] and round(s["bar"][1] - s0["bar"][1]), s["pause"] and round(s["pause"][0] - s0["pause"][0]), s["stale"], s["vtop"]])
        chk("%s: the pinned chrome made to ride with the page is seen and taken up at the bottom; the top is logged and not moved (384.77) (worst error bottom %.1f, top %.1f; [scrollY, bar off, Pause off, margins] %s; %s)" % (label, worst_b, worst_t, seen, s["log"][-1:]),
            worst_b <= 8 and worst_t <= 8 and not s["vtop"] and (s0["bar"] is not None or s0["pause"] is not None), seen)
        pg.evaluate("()=>{ window.__ride = false; document.querySelectorAll('*').forEach(e => { if(e.style && e.style.translate && /^0px -?\\d/.test(e.style.translate)) e.style.translate = ''; }); }")
        pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(1200)
        if name == "profile" or name == "board":
            pg.evaluate("()=>{ const i = document.createElement('input'); i.id = 'probein'; i.style.cssText = 'position:fixed;left:-300px;top:0;font-size:16px'; document.body.appendChild(i); i.focus(); window.__vvm.top = 270; visualViewport.dispatchEvent(new Event('scroll')); }")
            pg.wait_for_timeout(2600); b5 = pg.evaluate(S)
            chk("%s: with a text field focused (the keyboard's own pan) the chrome is left alone (%r / %r)" % (label, b5["stale"], b5["vtop"]), not b5["stale"] and not b5["vtop"], b5)
        ctx.close()
def short_and_never(br):
    serve_with(59, 34)
    ctx, pg = boot(br, 440, 686, (440, 956), mobile=False)
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    show(pg, "board"); pg.wait_for_timeout(4200)
    c = pg.evaluate(S)
    pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(1800); c2 = pg.evaluate(S)
    chk("an installed phone whose layout viewport (686) is 270 short of its 956pt screen: found and taken up (--vp-stale %r; %s)" % (c["stale"], c["log"]),
        abs(float((c["stale"] or "0px").replace("px", "")) - 270) <= 12 and any("short of the screen" in x for x in c["log"]), c)
    chk("...and undone when the viewport is whole again (%r)" % c2["stale"], not c2["stale"], c2)
    ctx.close()
    serve_with(73, 40)
    ctx, pg = boot(br, 518, 1126, (440, 956), mobile=False)
    show(pg, "board"); pg.wait_for_timeout(4200); z = pg.evaluate(S)
    chk("at his 518px page zoom nothing is taken up or logged (%r, %s)" % (z["stale"], z["log"]), not z["stale"] and not z["vtop"] and not z["log"], z)
    ctx.close()
    serve_with(0, 0)
    ctx, pg = boot(br, 440, 797, (440, 956), standalone=False, ua=UA_TAB, mobile=False)
    show(pg, "board"); pg.wait_for_timeout(4200); z = pg.evaluate(S)
    chk("a Safari tab (the page between the bars, 797 of 956) is not taken for a short installed app (%r, %s)" % (z["stale"], z["log"]), not z["stale"] and not z["vtop"] and not z["log"], z)
    ctx.close()
    serve_with(59, 34)
    ctx, pg = boot(br, 440, 956)
    show(pg, "board"); pg.wait_for_timeout(5200)
    for y in (500, 1500, 300, 0): pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(250)
    pg.wait_for_timeout(800); z = pg.evaluate(S)
    chk("a healthy installed page, scrolled and at rest: nothing logged, nothing taken up (%r/%r, %s)" % (z["stale"], z["vtop"], z["log"]), not z["stale"] and not z["vtop"] and not z["log"], z)
    chk("Report a bug carries the log (edges has BARHEAL and the visual viewport's scale)", "BARHEAL" in cb.BODY and "window.__barHeal" in cb.BODY and '" sc "' in cb.BODY)
    ctx.close()
retry(screens)
retry(short_and_never)
chk("no page errors", not errs, errs)
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
