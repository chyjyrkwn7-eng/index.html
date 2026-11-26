#!/usr/bin/env python3
"""384.154: Profile finished in its first frame, no colour read in a tab change, the next tab seen while swiping, a badge opened
without drawing in the lift.

Madison: "When clicking the profile tab, some of the stuff doesn't load immediately, like the badge icon, the new up for customize." /
"if I'm swiping between tabs, the screen I'm swiping too should be seen as I'm attempting the swipe" / "Clicking a badge to see it, it
still isn't smooth. Make this perfect." / "The bottom tab is laggy still".

Installed iPhone 17 Pro Max (440x956, 2x), real touches (CDP), the academy fixture with badges earned; read off the page:
 (A) FIRST FRAME: in the first painted frame after the Profile tab is tapped, the Customize row's picture and the badge case's art are
     visible (opacity 1) and the badge case's count already reads what it reads 2s later (nothing counts up or fades in);
 (B) NO COLOUR READ: tapping Home / Profile / Home / Profile again, each with a new passing class on <html> (as the glass, a pop-up's
     lock or a slide puts on), forces no colour probe (cssColorHexNow is not run) - the strip's colour comes from the cache;
 (C) PEEK: a finger dragged 150px left on Profile's Profile tab shows the Stats tab beside it (visible, its left edge within 4px of the
     Profile tab's left edge plus one screen width - each tab keeps its own side margins - both moved by the finger), a drag back and release returns to Profile with Stats hidden and unstyled, and
     a long drag selects Stats;
 (D) A SMOOTH OPEN: with the badge case open 8s (its warm-up done), opening an earned badge draws no pin or back for >= 30ms during
     the lift (the first 900ms), and no idle warm-up job runs while it is open;
 (E) no page errors.
Run:  TMPDIR=/dev/shm python3 tools/check-b384-b154.py [--against OLD/index.html]      Must FAIL (A), (B), (C) and (D) on 384.153.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "check-b384-sliders.py")
src = open(SRC, encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
src = src.replace('    pg.route("**/index.html"',
    '    _bld = (re.search(r\'const APP_BUILD = "([^"]+)"\', b) or [None, ""])[1]\n'
    '    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=\'{"build":"%s","force":true}\' % _bld))\n'
    '    pg.route("**/index.html"', 1)
G = {"__file__": SRC, "__name__": "b154", "re": re}
exec(src, G)
from playwright.sync_api import sync_playwright

ok = True; fails = 0
def chk(name, cond, info=""):
    global ok, fails
    ok = ok and bool(cond); fails += 0 if cond else 1
    print(("PASS " if cond else "FAIL ") + name + ("  " + str(info)[:300] if info else ""), flush=True)

FIRST = """()=>new Promise(res => { const read = () => { const st = document.getElementById('stage'); const p = st && st.querySelector('.screen-profile');
    if(!p) return null; const op = el => { if(!el) return null; let o = 1; for(let n = el; n && n !== document.body; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity); return Math.round(o * 100) / 100; };
    const num = p.querySelector('.pf-case-num');
    return { cz: op(p.querySelector('.pfr-cz-next > .trk-thumb, .pfr-cz-next, .pfr-cz-tile')), bc: op(p.querySelector('.pfr-bc > :first-child')), num: num ? num.textContent : null }; };
  const mo = new MutationObserver(() => { const r = read(); if(r){ mo.disconnect(); requestAnimationFrame(() => res(read())); } });
  mo.observe(document.getElementById('stage'), { childList: true });
  document.getElementById('bottomtab-profile').click(); })"""
LATE = """()=>{ const num = document.querySelector('#stage .screen-profile .pf-case-num'); return num ? num.textContent : null; }"""
WRAPHEX = """()=>{ window.__hex = 0; const f = window.cssColorHexNow; if(typeof f === 'function' && !f.__w){ window.cssColorHexNow = function(){ window.__hex++; return f.apply(this, arguments); }; window.cssColorHexNow.__w = 1; } }"""
WRAPDRAW = """()=>{ window.__draws = []; window.__idle = 0; ['renderObjPin','renderObjPinBack','renderBadgeStrike','renderBadgeBack','badgeEdgeURL'].forEach(n => { const f = window[n]; if(typeof f !== 'function' || f.__w) return;
  window[n] = function(){ const t = performance.now(); try{ return f.apply(this, arguments); } finally { window.__draws.push([n, t, performance.now() - t, document.body.classList.contains('binspect-open')]); } }; window[n].__w = 1; }); }"""

def touch(cdp, kind, x, y): G["touch"](cdp, kind, x, y)

with sync_playwright() as pw:
    srv, G["URL"] = G["g"]["serve"]()
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, cdp, errs = G["open_page"](br)
    pg.evaluate("()=>{ try{ homeUnlocksOwed = () => false; }catch(e){} document.getElementById('bottomtab-home').click(); }"); pg.wait_for_timeout(1500)
    # (A)
    first = pg.evaluate(FIRST); pg.wait_for_timeout(2000); late = pg.evaluate(LATE)
    chk("(A) FIRST FRAME: Customize picture opacity %s, badge case art %s, count %r then %r" % (first and first["cz"], first and first["bc"], first and first["num"], late),
        first and first["cz"] == 1 and first["bc"] == 1 and first["num"] == late and late)
    # (B)
    pg.evaluate(WRAPHEX)
    # a passing class on the page before each tab (as the bar's glass, a pop-up's lock or a slide put on): never a colour of its own
    for i, t in enumerate(("home", "profile", "home", "profile")):
        pg.evaluate("(i)=>{ document.documentElement.classList.add('gate-pass-' + i); }", i)
        pg.evaluate("(t)=>document.getElementById('bottomtab-'+t).click()", t); pg.wait_for_timeout(1200)
    n = pg.evaluate("()=>window.__hex")
    chk("(B) NO COLOUR READ: %d colour probes over Home/Profile/Home/Profile after the first visit" % n, n == 0)
    # (C)
    pg.evaluate("()=>{ window.scrollTo(0, 0); }"); pg.wait_for_timeout(300)
    R = """()=>{ const a = document.querySelector('#stage .profile-identity-tab'), b = document.querySelector('#stage .profile-stats-tab');
      const r = e => { const q = e.getBoundingClientRect(); return [q.left, q.right, q.width, !e.hidden && q.width > 0, e.getAttribute('style') || '']; }; return { a: r(a), b: r(b),
      active: (document.querySelector('#stage .profiletabs .active') || {}).textContent }; }"""
    y = 600
    g0 = pg.evaluate(R)
    touch(cdp, "touchStart", 330, y); pg.wait_for_timeout(30)
    for i in range(1, 13): touch(cdp, "touchMove", 330 - 150 * i / 12, y); pg.wait_for_timeout(16)
    pg.wait_for_timeout(80); g1 = pg.evaluate(R)
    vw = pg.evaluate("()=>innerWidth")
    beside = g1["b"][3] and abs((g1["b"][0] - g1["a"][0]) - vw) <= 3 and abs((g1["a"][0] - g0["a"][0]) + 150) <= 6
    chk("(C) PEEK: 150px left, Profile at %.0f..%.0f, Stats shown %s at %.0f (one screen along: %d)" % (g1["a"][0], g1["a"][1], g1["b"][3], g1["b"][0], vw), beside)
    for i in range(1, 9): touch(cdp, "touchMove", 180 + 150 * i / 8, y); pg.wait_for_timeout(16)
    for _ in range(8): touch(cdp, "touchMove", 330, y); pg.wait_for_timeout(16)
    touch(cdp, "touchEnd", 330, y); pg.wait_for_timeout(700); g2 = pg.evaluate(R)
    chk("(C) PEEK: dragged back and let go, still on %r, Stats hidden %s, unstyled %s" % (g2["active"], not g2["b"][3], not g2["b"][4]),
        g2["active"] == "Profile" and not g2["b"][3] and not g2["b"][4])
    touch(cdp, "touchStart", 380, y); pg.wait_for_timeout(30)
    for i in range(1, 15): touch(cdp, "touchMove", 380 - 300 * i / 14, y); pg.wait_for_timeout(16)
    touch(cdp, "touchEnd", 80, y); pg.wait_for_timeout(800); g3 = pg.evaluate(R)
    chk("(C) PEEK: a long drag selected %r, Stats shown at %.0f, unstyled %s" % (g3["active"], g3["b"][0], not g3["b"][4]),
        g3["active"] == "Stats" and g3["b"][3] and abs(g3["b"][0] - g0["a"][0]) <= 2 and not g3["b"][4])
    # (D)
    pg.evaluate("()=>{ showProfile('profile'); }"); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{ const b = document.querySelector('#stage .pfr-bc, #stage .pf-case-count'); b && b.click(); }"); pg.wait_for_timeout(8000)
    pg.evaluate(WRAPDRAW)
    t1 = pg.evaluate("()=>{ const t = [...document.querySelectorAll('#stage .badge-tile.is-earned')][0]; const t0 = performance.now(); t && t.click(); return t0; }")
    pg.wait_for_timeout(2600)
    draws = pg.evaluate("()=>window.__draws")
    lift = [d for d in draws if t1 <= d[1] <= t1 + 900 and d[2] >= 30]
    small = [d for d in draws if d[3] and d[0] in ("renderBadgeStrike",) and d[2] < 30 and d[1] - t1 < 900]
    chk("(D) A SMOOTH OPEN: draws >= 30ms in the lift %s; idle jobs run while open %d" % ([(d[0], round(d[1] - t1), round(d[2])) for d in lift][:4], len(small)),
        not lift and not small)
    chk("(E) no page errors", not errs, errs[:2])
    ctx.close(); br.close()
print("\nALL PASS" if ok else "\n%d FAILED" % fails)
sys.exit(0 if ok else 1)
