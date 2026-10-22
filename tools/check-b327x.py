#!/usr/bin/env python3
"""Build 327 round 7 (builder X): the bottom tab bar to Madison's reference,
and the "Installing update" screen.

"the home icon, let's make that a planet with a ring ... Make the calendar
look a little bit better ... pay attention to the bottom tabs size their and
the size of the logos and words (it's perfect) ensure ours is the same
perfectness." - with a screenshot of another app's bar, measured in pt: a
62 tall bar, the platter 4.5 inside it, ~23pt glyphs, an 11pt semibold label
~6.5 under the glyph, glyph and label centred.

"Let's make this 'pushing update' screen like 10 seconds longer and with some
new words going across like initiating sound system stuff."

  A. the Home glyph is a planet (a filled circle) with a ring (an arc) round
     it; the Calendar glyph is a filled page with its body cut out (evenodd)
     and a grid of day dots; the Leaderboard glyph is filled.
  B. on a 17 Pro Max: the bar 62px (+-1), the platter 4-5px inside it, the
     icon box 28px, the label 11px semibold, the label under the icon with no
     more than 3px between their boxes, the content centred in the bar
     (+-2px); on an iPad Pro 11: the same x1.28 (bar 77-82, label 13.5-14.5).
  C. a launch with sessionStorage class26e.updating=1 shows #install-update,
     its line changes at least 6 times, it ends 9.5-12.5s in (the page's own
     clock), then it is gone, Home is up and a tap on the tab bar lands on a
     tab; the flag is consumed.
  D. an ordinary launch shows no install screen.

  python3 tools/check-b327x.py
  python3 tools/check-b327x.py --against /tmp/x/index-61d9620.html
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright  # noqa: E402

check, booted, USED_ACCOUNT, CHROME = cb.check, cb.booted, cb.USED_ACCOUNT, cb.CHROME
CLEAN = "() => document.querySelectorAll('#intro-pop,.nova-talk,#tour-overlay,.tour-tip').forEach(n=>n.remove())"

GLYPHS = """() => { const q = id => document.querySelector('#bottomtab-' + id + ' .bottomtab-icon svg');
  const h = q('home'), c = q('calendar'), r = q('rewards');
  const filled = el => !!el && [...el.querySelectorAll('path,circle,rect')].some(n => { const f = getComputedStyle(n).fill; return f && f !== 'none' && !/rgba\\(0, 0, 0, 0\\)/.test(f); });
  return {
    home: !!h && !!h.querySelector('circle') && filled(h) && [...h.querySelectorAll('path')].some(p => /A/.test(p.getAttribute('d') || '')),
    homeRing: !!h && h.querySelectorAll('path').length,
    cal: !!c && filled(c) && [...c.querySelectorAll('path')].some(p => p.getAttribute('fill-rule') === 'evenodd') && c.querySelectorAll('rect').length >= 9,
    calDots: c ? c.querySelectorAll('rect').length : 0,
    rew: filled(r) };
}"""

SIZES = """() => { const bar = document.getElementById('bottomtabs'), b = bar.getBoundingClientRect();
  const sl = document.getElementById('bottomtabs-slider'), s = sl.getBoundingClientRect(), pb = getComputedStyle(sl, '::before');
  const pt = s.top + parseFloat(pb.top), pbt = s.bottom - parseFloat(pb.bottom);
  const t = document.getElementById('bottomtab-calendar'), i = t.querySelector('.bottomtab-icon').getBoundingClientRect();
  const l = t.querySelector('.bottomtab-label'), lr = l.getBoundingClientRect(), cs = getComputedStyle(l);
  return { barH: b.height, inTop: pt - b.top, inBot: b.bottom - pbt, icon: i.height, font: parseFloat(cs.fontSize), weight: +cs.fontWeight,
    gap: lr.top - i.bottom, topRoom: i.top - b.top, botRoom: b.bottom - lr.bottom };
}"""


def check_bar(br):
    print("\nA/B. the glyphs, and the bar's sizes against the reference")
    for (w, h, dpr, lo, hi, flo, fhi) in [(440, 956, 3, 61, 63, 10.7, 11.3), (834, 1194, 2, 77, 82, 13.5, 14.5)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr)
        pg.evaluate(CLEAN)
        pg.wait_for_timeout(600)
        g = pg.evaluate(GLYPHS)
        check("%dx%d: Home is a planet with a ring (a filled circle and an arc)" % (w, h), g["home"], g)
        check("%dx%d: Calendar is a filled page, its body cut out, with a grid of days" % (w, h), g["cal"], g)
        check("%dx%d: Leaderboard is a filled glyph too" % (w, h), g["rew"], g)
        z = pg.evaluate(SIZES)
        zz = {k: round(v, 1) for k, v in z.items()}
        check("%dx%d: the bar is %d-%dpx tall (the reference: 62pt on a phone)" % (w, h, lo, hi), lo <= z["barH"] <= hi, zz)
        check("%dx%d: the platter sits 4-6.5px inside the bar, top and bottom alike" % (w, h),
              4 <= z["inTop"] <= 6.5 and abs(z["inTop"] - z["inBot"]) <= .6, zz)
        check("%dx%d: the label is %.1f-%.1fpx semibold" % (w, h, flo, fhi), flo <= z["font"] <= fhi and z["weight"] == 600, zz)
        check("%dx%d: the label sits right under the icon (0-3px) and the two are centred in the bar (+-2px)" % (w, h),
              -0.5 <= z["gap"] <= 3 and abs(z["topRoom"] - z["botRoom"]) <= 2, zz)
        if w == 440:
            check("440x956: the icon box is 27-29px (23px of ink)", 27 <= z["icon"] <= 29, zz)
        ctx.close()


def launch(br, w, h, updating):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
                        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % USED_ACCOUNT)
    if updating:
        ctx.add_init_script("try{ if(/^http/.test(location.protocol) && !sessionStorage.getItem('x327.once')){ sessionStorage.setItem('x327.once','1'); sessionStorage.setItem('class26e.updating','1'); } }catch(e){}")
    pg = cb.open_page(ctx)
    pg.goto(cb.URL)
    return ctx, pg


def check_install(br):
    print("\nC. a launch straight after an update: the install screen")
    ctx, pg = launch(br, 440, 956, True)
    up = False
    for _ in range(30):
        pg.wait_for_timeout(100)
        up = pg.evaluate("() => !!document.getElementById('install-update') && !!document.getElementById('splashscreen')")
        if up:
            break
    check("the install screen is up from the first frames, over the splash", up)
    try:
        pg.evaluate("() => window.__stub && __stub()")
    except Exception:
        pass
    pg.wait_for_timeout(5000)
    mid = pg.evaluate("() => { const e = document.getElementById('install-update'); return { up: !!e, z: e ? +getComputedStyle(e).zIndex : 0, flag: sessionStorage.getItem('class26e.updating') }; }")
    check("still up 5s in, above everything (z >= 500), the flag consumed", mid["up"] and mid["z"] >= 500 and mid["flag"] is None, mid)
    for _ in range(40):
        pg.wait_for_timeout(500)
        if pg.evaluate("() => !!(window.__installUpdate && window.__installUpdate.end != null)"):
            break
    pg.wait_for_timeout(1500)
    log = pg.evaluate("() => window.__installUpdate || null")
    end = log and log["end"]
    texts = [x["text"] for x in (log["lines"] if log else [])]
    check("its line changes at least 6 times", len(set(texts)) >= 7, texts)
    check("it lasts 9.5-12.5s on the page's clock", end is not None and 9500 <= end <= 12500, end)
    st = pg.evaluate("""() => { const b = document.getElementById('bottomtab-calendar'); const r = b && b.getBoundingClientRect();
      const hit = r ? document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) : null;
      return { gone: !document.getElementById('install-update'), splash: !document.getElementById('splashscreen'),
        home: !!document.querySelector('#stage .screen-home-actual'), tab: !!(hit && hit.closest && hit.closest('.bottomtab')) }; }""")
    check("then it is gone, Home is up and a tap on the bar lands on a tab", all(st.values()), st)
    pg.reload()
    pg.wait_for_timeout(800)
    again = pg.evaluate("() => !!document.getElementById('install-update')")
    check("a reload after it does not show it again", not again)
    ctx.close()

    print("\nD. an ordinary launch")
    ctx, pg = launch(br, 440, 956, False)
    seen = False
    for _ in range(6):
        pg.wait_for_timeout(500)
        seen = seen or pg.evaluate("() => !!document.getElementById('install-update')")
    check("an ordinary launch shows no install screen", not seen)
    ctx.close()


if __name__ == "__main__":
    only = os.environ.get("ONLY", "")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME)
        if not only or "bar" in only:
            check_bar(br)
        if not only or "install" in only:
            check_install(br)
        br.close()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)
