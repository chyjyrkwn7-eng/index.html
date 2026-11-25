#!/usr/bin/env python3
"""384.153 (swipeback): A SWIPE RIGHT ON A SCREEN WITH A BACK BUTTON GOES BACK; SHORT OF IT, THE SCREEN BOUNCES BACK.

Madison: "we need a swipe back function.. similar to how tests have the swipe forward function. We need the back back on like every
screen I think? All the ones that make sense. It won't be blurry when you half swipe on these though. But it will bounce back if you
didn't swipe like all the way".

On an installed iPhone 17 Pro Max (440x956, 2x), with real touches (CDP), for each screen with a back button (Settings > Sound,
Advanced settings, Choose your mode, Add a class, Ranks, Credits, Friends, Customize), read off the page:
 (1) FOLLOW  a finger down mid-screen and moved 150px right: the screen's panel (and its back button) has moved right with it,
             within 6px of the finger, and nothing on it is blurred (no filter on it or under it);
 (2) BOUNCE  moved 100px (under a third of the width), held still, let go: it comes back - passing a little left of where it
             started (the overshoot, >= 0.5px) - and rests where it was, the same screen, no transform left on it;
 (3) BACK    moved 300px and let go: the screen is the one a TAP on its back button opens (the stage's first panel's class, read
             from a fresh page tapped), and nothing is left moved or clipped (html.tab-sliding gone) once it has landed;
 (4) FLICK   80px in ~50ms and let go: back as well;
and on screens where it must not happen:
 (5) NOT     a drag down on a back screen scrolls and moves nothing sideways; a drag LEFT does nothing; a drag right that starts on
             Settings > Sound's volume slider moves the slider, not the screen; a drag right on Home (no back button) and on a
             drill question (a test: no back button) moves no panel and changes no screen;
 (6) no page errors.
Run:  TMPDIR=/dev/shm python3 tools/check-b384-swipeback.py [--only sound,ranks,...] [--against OLD/index.html]
Must FAIL (1)-(4) on 384.152 (no swipe back)."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "check-b384-sliders.py")
src = open(SRC, encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
src = src.replace('    pg.route("**/index.html"',
    '    _bld = (re.search(r\'const APP_BUILD = "([^"]+)"\', b) or [None, ""])[1]\n'
    '    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=\'{"build":"%s","force":true}\' % _bld))\n'
    '    pg.route("**/index.html"', 1)
G = {"__file__": SRC, "__name__": "swipeback", "re": re}
exec(src, G)
from playwright.sync_api import sync_playwright

ONLY = G["ONLY"]
SCREENS = [
    ("sound", "()=>{ theme.soundOn = true; showAppearance({ page: 'sound' }); }"),
    ("advanced", "()=>{ showAdvancedSettings(); }"),
    ("modes", "()=>{ showModeSelect(); }"),
    ("catalog", "()=>{ showClassCatalog('home'); }"),
    ("ranks", "()=>{ showRanksScreen(); }"),
    ("credits", "()=>{ showCredits(); }"),
    ("friends", "()=>{ showFriends(); }"),
    ("customize", "()=>{ showCustomize(); }"),
]
ok = True; fails = 0
def chk(name, cond, info=""):
    global ok, fails
    ok = ok and bool(cond); fails += 0 if cond else 1
    print(("PASS " if cond else "FAIL ") + name + ("  " + str(info)[:300] if info else ""), flush=True)

PREP = """async (js)=>{ const w = ms => new Promise(r => setTimeout(r, ms));
  try{ homeUnlocksOwed = () => false; }catch(e){}
  document.querySelectorAll('.unlock-card,.rs-spot,.rs-fly,#intro-pop,.app-banner').forEach(n => n.remove());
  window.scrollTo(0, 0); (0, eval)('(' + js + ')')(); await w(1300);
  document.querySelectorAll('.unlock-card,.rs-spot,.rs-fly,#intro-pop,.app-banner,#tour-tooltip,.tour-dim').forEach(n => n.remove());
  await w(200); return true; }"""
SIG = """()=>{ const st = document.getElementById('stage'); const p = st && st.firstElementChild; return p ? (p.className || p.tagName) : ''; }"""
GEO = """()=>{ const st = document.getElementById('stage'); const p = st && st.firstElementChild; if(!p) return null;
  const b = st.querySelector('.back-link, .settings-nav-back'); const r = p.getBoundingClientRect(); const br = b && b.getClientRects().length ? b.getBoundingClientRect() : null;
  const blurred = [p, ...p.querySelectorAll('*')].slice(0, 400).some(e => { const cs = getComputedStyle(e); return (cs.filter && cs.filter !== 'none' && /blur/.test(cs.filter)); });
  return { left: r.left, back: br ? br.left : null, tf: p.style.transform || '', sig: p.className, sliding: document.documentElement.classList.contains('tab-sliding'),
           scrollY: window.scrollY, blurred }; }"""
TAPBACK = """async ()=>{ const b = document.querySelector('#stage .back-link, #stage .settings-nav-back'); if(!b) return null; b.click();
  await new Promise(r => setTimeout(r, 900)); const p = document.getElementById('stage').firstElementChild; return p ? p.className : ''; }"""
# sample the panel's left edge every frame for a while (the bounce)
TRACE = """(ms)=>new Promise(res => { const out = []; const t0 = performance.now();
  const f = () => { const p = document.getElementById('stage').firstElementChild; if(p) out.push(p.getBoundingClientRect().left);
    if(performance.now() - t0 < ms) requestAnimationFrame(f); else res(out); }; requestAnimationFrame(f); })"""

def touch(cdp, kind, x, y):
    G["touch"](cdp, kind, x, y)

def drag(pg, cdp, x0, y0, dx, dy=0, steps=12, dt=16, hold=0, release=True):
    touch(cdp, "touchStart", x0, y0); pg.wait_for_timeout(30)
    for i in range(1, steps + 1):
        touch(cdp, "touchMove", x0 + dx * i / steps, y0 + dy * i / steps); pg.wait_for_timeout(dt)
    if hold:
        for _ in range(max(1, hold // 16)):
            touch(cdp, "touchMove", x0 + dx, y0 + dy); pg.wait_for_timeout(16)
    if release:
        touch(cdp, "touchEnd", x0 + dx, y0 + dy)

def fresh(br, key, js):
    ctx, pg, cdp, errs = G["open_page"](br)
    pg.evaluate(PREP, js)
    return ctx, pg, cdp, errs

def run_screen(br, key, js):
    # where a tap on its back button goes
    ctx, pg, cdp, errs = fresh(br, key, js)
    here = pg.evaluate(SIG); want = pg.evaluate(TAPBACK); ctx.close()
    if want is None:
        chk("%s: has a back button" % key, False, here); return
    # (1) follow + (2) bounce
    ctx, pg, cdp, errs = fresh(br, key, js)
    g0 = pg.evaluate(GEO); y = 520
    drag(pg, cdp, 200, y, 150, release=False); pg.wait_for_timeout(60)
    g1 = pg.evaluate(GEO)
    moved = g1["left"] - g0["left"]; bmoved = (g1["back"] - g0["back"]) if (g1["back"] is not None and g0["back"] is not None) else None
    chk("%s (1) FOLLOW: 150px right, the panel moved %.1f, its back button %s, blurred %s" % (key, moved, bmoved and round(bmoved, 1), g1["blurred"]),
        abs(moved - 150) <= 6 and bmoved is not None and abs(bmoved - 150) <= 6 and not g1["blurred"])
    # back to 100px, held still, let go
    for i in range(1, 7):
        touch(cdp, "touchMove", 350 - 50 * i / 6, y); pg.wait_for_timeout(16)
    for _ in range(10):
        touch(cdp, "touchMove", 300, y); pg.wait_for_timeout(16)
    touch(cdp, "touchEnd", 300, y)
    tr = pg.evaluate(TRACE, 700); pg.wait_for_timeout(200)
    g2 = pg.evaluate(GEO)
    lo = min(tr) - g0["left"] if tr else 0
    chk("%s (2) BOUNCE: 100px and let go, it came back past its rest by %.1fpx and rests at %.1f (was %.1f), same screen %s, transform %r" % (
        key, -lo, g2["left"], g0["left"], g2["sig"] == here, g2["tf"]),
        lo <= -0.5 and abs(g2["left"] - g0["left"]) <= 0.5 and g2["sig"] == here and not g2["tf"] and not g2["sliding"])
    chk("%s (6) no page errors (follow/bounce)" % key, not errs, errs[:2])
    ctx.close()
    # (3) back
    ctx, pg, cdp, errs = fresh(br, key, js)
    drag(pg, cdp, 120, y, 300, steps=16); pg.wait_for_timeout(1300)
    g3 = pg.evaluate(GEO)
    chk("%s (3) BACK: 300px, it is now %r (a tap on back opens %r), moved %r, clipped %s" % (key, g3 and g3["sig"], want, g3 and g3["tf"], g3 and g3["sliding"]),
        g3 and g3["sig"] == want and want != here and not g3["tf"] and not g3["sliding"])
    chk("%s (6) no page errors (back)" % key, not errs, errs[:2])
    ctx.close()
    # (4) flick
    ctx, pg, cdp, errs = fresh(br, key, js)
    drag(pg, cdp, 160, y, 80, steps=4, dt=12); pg.wait_for_timeout(1300)
    g4 = pg.evaluate(GEO)
    chk("%s (4) FLICK: 80px in ~50ms, it is now %r (want %r)" % (key, g4 and g4["sig"], want), g4 and g4["sig"] == want)
    ctx.close()
    # (5) down and left
    ctx, pg, cdp, errs = fresh(br, key, js)
    g0 = pg.evaluate(GEO)
    drag(pg, cdp, 220, 700, 8, -260, steps=14, release=False); pg.wait_for_timeout(40)
    gd = pg.evaluate(GEO); touch(cdp, "touchEnd", 228, 440); pg.wait_for_timeout(600)
    chk("%s (5) NOT: a drag down moved the panel sideways %.1fpx (screen %s)" % (key, gd["left"] - g0["left"], pg.evaluate(SIG) == here),
        abs(gd["left"] - g0["left"]) < 0.5 and pg.evaluate(SIG) == here)
    pg.evaluate("()=>window.scrollTo(0,0)"); pg.wait_for_timeout(200); g0 = pg.evaluate(GEO)
    drag(pg, cdp, 360, 520, -200, release=False); pg.wait_for_timeout(40)
    gl = pg.evaluate(GEO); touch(cdp, "touchEnd", 160, 520); pg.wait_for_timeout(700)
    chk("%s (5) NOT: a drag left moved the panel %.1fpx (screen %s)" % (key, gl["left"] - g0["left"], pg.evaluate(SIG) == here),
        abs(gl["left"] - g0["left"]) < 0.5 and pg.evaluate(SIG) == here)
    ctx.close()

def run_nots(br):
    # the volume slider takes the drag
    ctx, pg, cdp, errs = fresh(br, "sound", SCREENS[0][1])
    sl = pg.evaluate("()=>{ const s = document.querySelector('.settings-volume input[type=range]'); s.value = s.min; s.dispatchEvent(new Event('input',{bubbles:true})); s._nsl && s._nsl.paint();"
                     " const k = s.closest('.nsl').querySelector('.nsl-thumb').getBoundingClientRect(); return [k.left + k.width/2, k.top + k.height/2, +s.value]; }")
    pg.wait_for_timeout(500); g0 = pg.evaluate(GEO); here = pg.evaluate(SIG)
    drag(pg, cdp, sl[0], sl[1], 160, release=False); pg.wait_for_timeout(60)
    g1 = pg.evaluate(GEO); v1 = pg.evaluate("()=>+document.querySelector('.settings-volume input[type=range]').value")
    touch(cdp, "touchEnd", sl[0] + 160, sl[1]); pg.wait_for_timeout(700)
    chk("(5) NOT: a drag right from the volume slider's knob moved the volume %g -> %g and the panel %.1fpx (screen %s)" % (sl[2], v1, g1["left"] - g0["left"], pg.evaluate(SIG) == here),
        v1 > sl[2] and abs(g1["left"] - g0["left"]) < 0.5 and pg.evaluate(SIG) == here)
    ctx.close()
    # Home and a drill question: no back button, nothing moves
    for name, js in (("Home", "()=>{ showHome(); }"),
                     ("a drill question", "()=>{ const u=topicsIn(QUESTIONS)[0]; cfg.mode='drill'; cfg.source='all'; cfg.units=[u]; const pool=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u); beginRun(pool); }")):
        ctx, pg, cdp, errs = fresh(br, name, js)
        if name != "Home": pg.wait_for_timeout(1200)
        here = pg.evaluate(SIG); g0 = pg.evaluate(GEO)
        drag(pg, cdp, 140, 520, 220, release=False); pg.wait_for_timeout(60)
        g1 = pg.evaluate(GEO); touch(cdp, "touchEnd", 360, 520); pg.wait_for_timeout(1300)
        chk("(5) NOT: a drag right on %s (%r) moved the panel %.1fpx and left the screen %r" % (name, here[:40], (g1["left"] - g0["left"]) if g0 and g1 else 0, pg.evaluate(SIG)[:40]),
            g0 and g1 and abs(g1["left"] - g0["left"]) < 0.5 and pg.evaluate(SIG) == here and (name == "Home" or "question" in here or "panel" in here))
        chk("(6) no page errors (%s)" % name, not errs, errs[:2])
        ctx.close()

with sync_playwright() as pw:
    srv, G["URL"] = G["g"]["serve"]()
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    for key, js in SCREENS:
        if ONLY and key not in ONLY: continue
        run_screen(br, key, js)
    if not ONLY or "nots" in ONLY:
        run_nots(br)
    br.close()
print("\nALL PASS" if ok else "\n%d FAILED" % fails)
sys.exit(0 if ok else 1)
