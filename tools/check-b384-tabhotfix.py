#!/usr/bin/env python3
"""Build 384.62 (hot fix): THE TAB BAR IN THE MIDDLE OF THE SCREEN.

Madison: a Leaderboard scrolled part way, the glass tab bar drawn over rows #9 / #10 (~270pt too high) and the round back-to-top button above its right end the same;
and a screen recording of "Choose your chapters" (Fire Code's unit list, Drill): the pill with Start rides up the screen as the list is scrolled and comes back when it stops.
Top-pinned controls stay in the same frames. Read from the code and driven here: nothing in the app moves the bar (no script writes a transform, translate, top or bottom
on it or on back-to-top), both are position:fixed; bottom:--tabs-bottom, and in Chromium the bar's foot is the same pixel through every fling and rubber band - so the
layout viewport's bottom edge was not where the screen's is (WebKit's; not reproducible here). What the page can do is watch the bar (barSelfHeal) and put it back.
 (1) HELD   on the Leaderboard (academy), Drill setup "Choose your units" (academy) and "Choose your chapters" (Fire Code), scrolled by a fling, a rubber band at both ends and a
            mouse wheel: the bar's foot is its designed place in every animation frame (the page never moves it), and the page does not nudge the scroll while it is scrolling;
 (2) PAN    a visual viewport left 270px below the layout one (the keyboard's pan kept) with the page at rest: found, the scroll nudged, then the bar and the back-to-top button
            are taken down by exactly that (934 -> 1204: the 270px) and the margin is undone when the viewport comes right;
 (3) SHORT  an installed phone whose real layout viewport (686) is 270pt short of its 956pt screen: found and taken up, undone when whole;
 (4) NEVER  with a text field focused, in a Safari tab (797 of 956), at his 518px page zoom, in a healthy page for 5s: nothing is touched;
 (5) LOG    every step is in window.__barHeal and Report a bug carries it in `edges` after BARHEAL (with the visual viewport's scale), so the next one names its cause.
Run:  python3 tools/check-b384-tabhotfix.py   (--against OLD/index.html must FAIL: main 384.48 fails 2, 3, 5)"""
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
VVM = ("window.__vvm = {top: 0}; try{ Object.defineProperty(window.visualViewport, 'offsetTop', { get(){ return window.__vvm.top; }, configurable: true }); }catch(e){}"
       "window.__scrollTos = 0; const _st = window.scrollTo.bind(window); window.scrollTo = function(){ window.__scrollTos++; return _st.apply(window, arguments); };")
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
def show(pg, name):
    pg.evaluate({"board": "()=>showRankings()", "units": "()=>{ cfg.mode='drill'; showSetup(); }"}[name]); pg.wait_for_timeout(2200)
    pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot').forEach(n=>n.remove()); }")
    if name == "board":   # the owner's board is a long list; the harness's seed has few rows, so the page is given the length his has
        pg.evaluate("()=>{ const d = document.createElement('div'); d.style.cssText = 'height:3000px;pointer-events:none'; (document.querySelector('.wrap') || document.body).appendChild(d); }")
BAR = """()=>{ const b = document.querySelector('.bottomtabs'); if(!b) return null; const r = b.getBoundingClientRect(); const t = document.querySelector('.backtotop'); const tr = t && getComputedStyle(t).display !== 'none' ? t.getBoundingClientRect() : null;
  return { bottom: r.bottom, stale: getComputedStyle(document.documentElement).getPropertyValue('--vp-stale').trim(), cls: document.documentElement.classList.contains('vp-stale'), up: tr ? tr.bottom : null,
           log: (window.__barHeal || []).slice(), ih: innerHeight, docH: document.documentElement.scrollHeight, y: scrollY, nudges: window.__scrollTos, startTab: document.querySelector('.bottomtabs').classList.contains('has-start-tab') }; }"""
SAMPLE = """()=>{ window.__s = []; window.__run = true; const f = () => { const b = document.querySelector('.bottomtabs'); if(b) window.__s.push(Math.round(b.getBoundingClientRect().bottom * 10) / 10); if(window.__run) requestAnimationFrame(f); }; f(); }"""
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
def screens(br):
    for label, ifc, name in (("the Leaderboard", False, "board"), ("Drill setup, Choose your units (academy)", False, "units"), ("Drill setup, Choose your chapters (Fire Code)", True, "units")):
        serve_with(59, 34)
        ctx, pg = boot(br, 440, 956, ifc=ifc)
        pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
        show(pg, name)
        b0 = pg.evaluate(BAR)
        chk("%s: the bar is up, long enough to scroll (doc %s, has Start: %s)" % (label, b0 and b0["docH"], b0 and b0["startTab"]), b0 and b0["bottom"] > b0["ih"] - 60, b0)
        # (1) HELD: a fling, both rubber bands, a wheel - every frame
        pg.evaluate(SAMPLE)
        for y in (400, 1200, 2400, 900, 5000, 0, 3000, 200):
            pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(120)
        for dy in (800, -300, 1500, -2500, 600):
            pg.mouse.wheel(0, dy); pg.wait_for_timeout(110)
        pg.evaluate("()=>{ window.__run = false; }"); pg.wait_for_timeout(100)
        s = pg.evaluate("()=>window.__s")
        pg.evaluate("()=>{ window.__scrollTos = 0; }")
        chk("%s: through a fling, a rubber band at both ends and a wheel the bar's foot is its designed place in every frame (%d frames, %s..%s, designed %s)" % (label, len(s), min(s), max(s), round(b0["bottom"], 1)),
            len(s) > 40 and max(s) - min(s) < 1.0 and abs(s[0] - b0["bottom"]) < 1.0, [min(s), max(s), b0["bottom"]])
        # transient noise from the visual viewport while the page is scrolling is not acted on
        pg.evaluate("()=>{ window.__scrollTos = 0; }")
        for i in range(10):
            pg.evaluate("(i)=>{ window.__vvm.top = 270; visualViewport.dispatchEvent(new Event('scroll')); window.scrollTo({top:300 + i * 60, behavior:'instant'}); }", i); pg.wait_for_timeout(60)
            pg.evaluate("()=>{ window.__vvm.top = 0; visualViewport.dispatchEvent(new Event('scroll')); }"); pg.wait_for_timeout(50)
        n1 = pg.evaluate("()=>window.__scrollTos"); pg.wait_for_timeout(400)
        b1 = pg.evaluate(BAR)
        chk("%s: a visual viewport that flickers 270px for a few frames while the page scrolls is not acted on (own scroll calls %s of the 10 the test made; margin %r)" % (label, b1["nudges"] - 10, b1["stale"]),
            not b1["cls"] and not any("nudged" in x or "margin" in x for x in b1["log"]), b1)
        # (2) PAN, at rest
        pg.evaluate("()=>window.scrollTo({top:700, behavior:'instant'})"); pg.wait_for_timeout(900)
        b2 = pg.evaluate(BAR)
        pg.evaluate("()=>{ window.__vvm.top = 270; visualViewport.dispatchEvent(new Event('scroll')); }"); pg.wait_for_timeout(3600)
        b3 = pg.evaluate(BAR)
        chk("%s: a visual viewport left 270px below the layout one, page at rest: the scroll is nudged, then the bar is taken down 270 (%s -> %s; --vp-stale %s; %s)" % (label, round(b2["bottom"]), round(b3["bottom"]), b3["stale"], b3["log"][-2:]),
            b3["cls"] and abs((b3["bottom"] - b2["bottom"]) - 270) <= 10 and any("nudged" in x for x in b3["log"]), b3)
        if b2["up"] and b3["up"]: chk("%s: the back-to-top button goes with it (%s -> %s)" % (label, round(b2["up"]), round(b3["up"])), abs((b3["up"] - b2["up"]) - 270) <= 10, [b2, b3])
        pg.evaluate("()=>{ window.__vvm.top = 0; visualViewport.dispatchEvent(new Event('scroll')); }"); pg.wait_for_timeout(1900)
        b4 = pg.evaluate(BAR)
        chk("%s: the viewport comes right: the bar is back (%s vs %s), the margin gone (%r)" % (label, round(b4["bottom"]), round(b2["bottom"]), b4["stale"]), not b4["cls"] and abs(b4["bottom"] - b2["bottom"]) < 1.5, b4)
        pg.evaluate("()=>{ const i = document.createElement('input'); i.id = 'probein'; i.style.cssText = 'position:fixed;left:-300px;top:0;font-size:16px'; document.body.appendChild(i); i.focus(); window.__vvm.top = 270; visualViewport.dispatchEvent(new Event('scroll')); }")
        pg.wait_for_timeout(3000); b5 = pg.evaluate(BAR)
        chk("%s: with a text field focused the bar is left alone (%r)" % (label, b5["stale"]), not b5["cls"] and abs(b5["bottom"] - b2["bottom"]) < 1.5, b5)
        ctx.close()
def short_and_never(br):
    # (3) a real short layout viewport in an installed phone app
    serve_with(59, 34)
    ctx, pg = boot(br, 440, 686, (440, 956), mobile=False)
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    show(pg, "board"); pg.wait_for_timeout(4200)
    c = pg.evaluate(BAR)
    pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(1800); c2 = pg.evaluate(BAR)
    chk("an installed phone whose layout viewport (686) is 270 short of its 956pt screen: found and taken up (--vp-stale %s; %s)" % (c and c["stale"], c and c["log"]),
        c and c["cls"] and abs(float(c["stale"].replace("px", "")) - 270) <= 12 and any("short of the screen" in x for x in c["log"]), c)
    chk("...and undone when the viewport is whole again (%r)" % (c2 and c2["stale"]), c2 and not c2["cls"] and c2["bottom"] > c2["ih"] - 60, c2)
    ctx.close()
    # (4) never: his page zoom, a Safari tab, a healthy page
    serve_with(73, 40)
    ctx, pg = boot(br, 518, 1126, (440, 956), mobile=False)
    show(pg, "board"); pg.wait_for_timeout(4200); z = pg.evaluate(BAR)
    chk("at his 518px page zoom nothing is taken up (%r)" % (z and z["stale"]), z and not z["cls"] and not z["log"], z)
    ctx.close()
    serve_with(0, 0)
    ctx, pg = boot(br, 440, 797, (440, 956), standalone=False, ua=UA_TAB, mobile=False)
    show(pg, "board"); pg.wait_for_timeout(4200); z = pg.evaluate(BAR)
    chk("a Safari tab (the page between the bars, 797 of 956) is not taken for a short installed app (%r)" % (z and z["stale"]), z and not z["cls"] and not z["log"], z)
    ctx.close()
    serve_with(59, 34)
    ctx, pg = boot(br, 440, 956)
    show(pg, "board"); pg.wait_for_timeout(5200); z = pg.evaluate(BAR)
    chk("a healthy installed page for 5s: nothing logged, nothing taken up (%r, %s)" % (z and z["stale"], z and z["log"]), z and not z["cls"] and not z["log"], z)
    # (5) the log reaches Report a bug
    src_has = "BARHEAL" in cb.BODY and "window.__barHeal" in cb.BODY
    chk("Report a bug carries the log (edges has BARHEAL and the visual viewport's scale)", src_has and '" sc "' in cb.BODY)
    ctx.close()
retry(screens)
retry(short_and_never)
chk("no page errors", not errs, errs)
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
