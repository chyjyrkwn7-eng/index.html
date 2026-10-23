#!/usr/bin/env python3
"""Build 327z3: the account banner's glass on the passive top lines, and
Safari's bars tinted from strips made after the splash.

"You see the Liquid Glass here? This is great Liquid Glass and needs to be
implemented more through the app where it can be. Like when clicking the
daily question button and it's not ready, the pop could be bigger, at the
top, and have that same kinda look ... You pushed the update, but the bottom
and top parts of safari are still black."

  A. In a browser tab: no edge strip while the splash owns the frame; once it
     has gone, #edge-tint-top and -bottom exist with a SOLID inline colour,
     12px, at the top and bottom edges, the root background is the top one;
     a theme change makes NEW strip elements (Safari reads a colour when an
     element appears) in the new colour. Installed: no strips.
  B. Tapping the "?" when the daily question is done: a banner at the top on
     the app banner's glass (.app-banner.is-passive), tag DAILY QUESTION, a
     title "Done for today", the time left under it, an icon in a lit disc,
     an x that closes it; no bubble by the button.
  C. Find me's answer, "Your profile needs you" and the Detective's run are
     the same glass, each with its own tag.

  python3 tools/check-b327z3.py [--against FILE] [--shots DIR]
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright  # noqa: E402
check, booted, USED_ACCOUNT, CHROME = cb.check, cb.booted, cb.USED_ACCOUNT, cb.CHROME
SHOTS = None
if "--shots" in sys.argv: SHOTS = sys.argv[sys.argv.index("--shots") + 1]
CLEAN = "() => document.querySelectorAll('#intro-pop,.nova-talk,#tour-overlay,#tour-tooltip,.daily-alert,#daily-lock-tip').forEach(n=>n.remove())"

BANNER = """() => { const a = document.getElementById('dailyalert'); if(!a) return null;
  const r = a.getBoundingClientRect(), q = s => a.querySelector(s), cs = getComputedStyle(a);
  return { glass: a.classList.contains('app-banner') && a.classList.contains('is-passive'),
    tag: (q('.app-banner-tag') || {}).textContent || '', title: (q('.app-banner-title') || {}).textContent || '',
    sub: (q('.app-banner-sub') || {}).textContent || '', icon: !!q('.app-banner-icon'), face: !!q('.app-banner-face svg'), x: !!q('.app-banner-x'),
    blur: cs.backdropFilter || cs.webkitBackdropFilter || '', color: cs.getPropertyValue('--banner-color').trim(),
    top: r.top, h: r.height, w: r.width, vw: innerWidth, tip: !!document.getElementById('daily-lock-tip') }; }"""


def shot(pg, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True); pg.wait_for_timeout(450); pg.screenshot(path=os.path.join(SHOTS, name + ".png"))


def check_safari(br):
    print("\nA. Safari's bars: strips made after the splash")
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % USED_ACCOUNT)
    pg = cb.open_page(ctx); pg.goto(cb.URL); pg.wait_for_timeout(500)
    early = pg.evaluate("() => ({ browser: document.documentElement.classList.contains('is-browser'), splash: !!document.getElementById('splashscreen'), strips: document.querySelectorAll('.edge-tint').length })")
    check("a browser tab is marked is-browser", early["browser"], early)
    check("no edge strip while the splash owns the frame", not early["splash"] or early["strips"] == 0, early)
    for _ in range(80):
        if not pg.evaluate("() => !!document.getElementById('splashscreen')"): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(700)
    S = """() => { const t = document.getElementById('edge-tint-top'), b = document.getElementById('edge-tint-bottom');
      const R = e => e && e.getBoundingClientRect();
      return { top: !!t, bot: !!b, tc: t && t.style.backgroundColor, bc: b && b.style.backgroundColor,
        th: t && R(t).height, ttop: t && R(t).top, bbot: b && innerHeight - R(b).bottom, root: document.documentElement.style.backgroundColor,
        fixed: t && getComputedStyle(t).position, pe: t && getComputedStyle(t).pointerEvents }; }"""
    s1 = pg.evaluate(S)
    check("after the splash both strips exist", s1["top"] and s1["bot"], s1)
    check("the strips carry a solid inline colour", bool(s1["tc"]) and "rgba" not in (s1["tc"] or "") and bool(s1["bc"]), s1)
    check("they are fixed, 12px, at the very top and bottom, and take no taps",
          s1["fixed"] == "fixed" and abs((s1["th"] or 0) - 12) < .5 and s1["ttop"] is not None and abs(s1["ttop"]) < .5 and s1["bbot"] is not None and abs(s1["bbot"]) < .5 and s1["pe"] == "none", s1)
    check("the root background is the top strip's colour", s1["root"] == s1["tc"], s1)
    pg.evaluate("() => { window.__oldTop = document.getElementById('edge-tint-top'); theme.accent = 'elite'; applyTheme(); syncStatusBarColor(); }")
    pg.wait_for_timeout(300)
    s2 = pg.evaluate("() => ({ same: document.getElementById('edge-tint-top') === window.__oldTop, c: (document.getElementById('edge-tint-top') || {style:{}}).style.backgroundColor, n: document.querySelectorAll('.edge-tint').length })")
    check("a theme change makes NEW strips in the new colour, two of them", (not s2["same"]) and s2["c"] != s1["tc"] and s2["n"] == 2, {"before": s1["tc"], "after": s2})
    ctx.close()
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    pg = cb.open_page(ctx); pg.goto(cb.URL); pg.wait_for_timeout(2600)
    pg.evaluate("() => { document.getElementById('splashscreen')?.remove(); try{ syncStatusBarColor(); }catch(e){} }")
    n = pg.evaluate("() => ({ browser: document.documentElement.classList.contains('is-browser'), strips: document.querySelectorAll('.edge-tint').length })")
    check("installed: no strips", not n["browser"] and n["strips"] == 0, n)
    ctx.close()


def check_banners(br):
    for (w, h, dpr, dev) in [(440, 956, 3, "iphone"), (834, 1194, 2, "ipad"), (375, 667, 2, "se")]:
        print("\nB/C. %dx%d" % (w, h))
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr)
        pg.evaluate(CLEAN); pg.wait_for_timeout(500)
        pg.evaluate("async () => { store.dailyQuestionDate = dailyPeriodKey(); showHome(); }")
        pg.wait_for_timeout(700); pg.evaluate(CLEAN)
        pg.evaluate("() => document.querySelector('.daily-question-fab').click()")
        pg.wait_for_timeout(500)
        b = pg.evaluate(BANNER)
        check("%s: the done daily question answers on the glass banner" % dev, bool(b) and b["glass"], b)
        if b:
            check("%s: ... at the top, no bubble by the button" % dev, b["top"] < 140 and not b["tip"], b)
            check("%s: ... tagged DAILY QUESTION, titled Done for today, the time under it" % dev,
                  b["tag"] == "DAILY QUESTION" and b["title"] == "Done for today" and "Next one in" in b["sub"], b)
            check("%s: ... an icon in a lit disc, frosted glass and an x" % dev, b["icon"] and b["x"] and "blur" in b["blur"], b)
            check("%s: ... a size up (at least 64px tall)" % dev, b["h"] >= 64, b)
            check("%s: ... inside the screen" % dev, b["w"] <= b["vw"] - 16, b)
            shot(pg, dev + "-daily-done")
            pg.evaluate("() => document.querySelector('#dailyalert .app-banner-x').click()")
            pg.wait_for_timeout(400)
            check("%s: ... the x closes it" % dev, not pg.evaluate("() => !!document.getElementById('dailyalert')"))
        for name, js, tag in [("find me", "() => { store.leaderboardOptIn = true; syncCode = null; showRankings(); setTimeout(() => document.querySelector('.rank-me-btn')?.click(), 400); }", "RANKINGS"),
                              ("profile needs you", "() => { showHome(); rankUpLockRefused(); }", "RANK UP"),
                              ("detective", "() => showDailyAlert('7 of 10 daily questions right in a row', { tag: 'DETECTIVE', character: 'detective', color: '#C9A46A' })", "DETECTIVE")]:
            pg.evaluate(CLEAN); pg.evaluate(js); pg.wait_for_timeout(900)
            if name == "find me":
                pg.evaluate("() => { if(!document.getElementById('dailyalert')){ const b=document.querySelector('.rank-me-btn'); b&&b.click(); } }"); pg.wait_for_timeout(500)
            c = pg.evaluate(BANNER)
            check("%s: %s is the same glass, tagged %s" % (dev, name, tag), bool(c) and c["glass"] and c["tag"] == tag and c["icon"] and c["x"], c)
            if name == "detective" and c: check("%s: ... the Detective's face in the disc" % dev, c["face"], c)
            if c: shot(pg, dev + "-" + name.replace(" ", "-"))
        ctx.close()


if __name__ == "__main__":
    only = os.environ.get("ONLY", "")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME)
        if not only or "safari" in only:
            check_safari(br)
        if not only or "banner" in only:
            check_banners(br)
        br.close()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)
