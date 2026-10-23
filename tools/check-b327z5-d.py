#!/usr/bin/env python3
"""Build 327z5 (builder D): the calendar in the app's materials, the
leaderboard's first place without its sheen and with a blurb that says
something, the person card's banner fading out, banner subjects clear of the
character's circle, unit cards one size, and no line under the unit tick.

Madison:
  "The calendar tab ... the interface doesn't go with the rest of the app.. fix it."
  "In the leaderboard, remove the reflection effect on the first place person."
  "In leaderboard is says 'ranked by rank' fix that"
  "When clicking someone's profile ... the banner needs to fade better because it's hard cut off"
  "some of the banners don't display properly because their main component is placed
   like right behind the characters circle"
  "Some of the unit selection boxes aren't the same sizes."
  "When selecting a unit, there's a line under the checkmark, fix that."

  A. no .lb-podium-sheen is built; no board's blurb says "ranked by rank".
  B. every calendar card is the app's card (the surface tokens' background,
     border and blur - the same as a probe built from them); the month title
     is not a serif; its kickers are --soft; the arrows are the black pill.
  C. the person card's cover: mask no-repeat, and down the cover's lower half
     the banner fades with no row-to-row step over 9 levels (device pixels).
  D. the focus table moves each subject banner on the Profile cover and the
     person card (a transform on the art), and leaves an unlisted one alone.
  E. every unit card on a screen is the same height (440, 375, 834).
  F. a picked unit's circle has no hard inset lip (blur <= 1 with a y offset)
     and its top light is not repeated (no-repeat).

  python3 tools/check-b327z5-d.py [--against FILE]
"""
import importlib.util, io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright  # noqa: E402
from PIL import Image  # noqa: E402

check, booted, USED, CHROME = cb.check, cb.booted, cb.USED_ACCOUNT, cb.CHROME
CLEAN = "() => document.querySelectorAll('#intro-pop,.nova-talk,#tour-overlay,.tour-tip').forEach(n=>n.remove())"


def sec_a(br):
    ctx, pg = booted(br, 440, 956, seed=USED, touch=True, dpr=2)
    try:
        r = pg.evaluate("""() => {
          const blurbs = (typeof RANKING_BOARDS !== 'undefined' ? RANKING_BOARDS : []).map(b => (b.blurb || '') + ' ' + (b.info || ''));
          const src = [...document.scripts].map(s => s.textContent).join('\\n');
          return { blurbs, built: /className\\s*=\\s*["']lb-podium-sheen/.test(src) || /lb-podium-sheen["']\\s*;?\\s*row\\.insertBefore/.test(src) };
        }""")
        check("A: first place's sheen is no longer built", not r["built"], r["built"])
        bad = [b for b in r["blurbs"] if "ranked by rank" in b.lower()]
        check("A: no board's blurb says 'ranked by rank'", len(r["blurbs"]) >= 3 and not bad, bad or r["blurbs"])
    finally:
        ctx.close()


CAL = """() => {
  const probe = document.createElement('div');
  probe.style.cssText = 'position:fixed;left:0;top:0;width:10px;height:10px;background:var(--surface-sheen), var(--surface-1);border:1px solid var(--surface-border);backdrop-filter:var(--surface-blur);-webkit-backdrop-filter:var(--surface-blur)';
  document.body.appendChild(probe);
  const P = getComputedStyle(probe), want = { bg: P.backgroundImage, bc: P.borderTopColor, bf: P.backdropFilter || P.webkitBackdropFilter };
  probe.remove();
  const cards = [...document.querySelectorAll('#stage .cal-today-card, #stage .cal-nexttest-card, #stage .cal-big-card, #stage .cal-course-card, #stage .cal-daycard')]
    .filter(c => c.offsetParent !== null);
  const off = cards.map(c => { const s = getComputedStyle(c); return { c: c.className.split(' ')[0], ok: s.backgroundImage === want.bg && s.borderTopColor === want.bc && (s.backdropFilter || s.webkitBackdropFilter) === want.bf, bg: s.backgroundImage.slice(0, 70), bc: s.borderTopColor }; }).filter(x => !x.ok);
  const m = document.querySelector('#stage .cal-grid-month');
  const kick = [...document.querySelectorAll('#stage .cal-card-head .slab')].filter(k => k.offsetParent !== null);
  const soft = getComputedStyle(document.documentElement).getPropertyValue('--soft').trim();
  const t = document.createElement('i'); t.style.color = soft; document.body.appendChild(t); const softC = getComputedStyle(t).color; t.remove();
  const arr = document.querySelector('#stage .cal-grid-arrow');
  return { n: cards.length, off, serif: m ? /serif|georgia|times/i.test(getComputedStyle(m).fontFamily) && !/sans-serif/i.test(getComputedStyle(m).fontFamily) : null,
    kick: kick.length, kickOff: kick.filter(k => getComputedStyle(k).color !== softC).map(k => getComputedStyle(k).color),
    arrow: arr ? getComputedStyle(arr).backgroundColor : null };
}"""


def sec_b(br):
    for (w, h, dev) in ((440, 956, "iPhone 17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED, touch=True, dpr=2)
        try:
            pg.evaluate(CLEAN)
            pg.evaluate("() => (typeof showCalendarTab === 'function' ? showCalendarTab : showCalendar)()")
            pg.wait_for_timeout(900)
            r = pg.evaluate(CAL)
            check("B (%s): every calendar card is the app's card" % dev, r["n"] >= 4 and not r["off"], r)
            check("B (%s): the month title is not a serif" % dev, r["serif"] is False, r["serif"])
            check("B (%s): the cards' kickers are the app's soft grey" % dev, r["kick"] >= 3 and not r["kickOff"], r["kickOff"])
            check("B (%s): the month arrows are the black pill" % dev, r["arrow"] == "rgb(10, 10, 12)", r["arrow"])
        finally:
            ctx.close()


def person(pg, bid):
    pg.evaluate("""(b) => { document.querySelector('.invite-overlay')?.remove(); openPersonSheet({ pub:'zz1', name:'Ana', avatarChar:'ninja', banner:b, level:30, badges:3, xp:20000, hundos:9, correct:900, weekPoints:100, accent:'ink' }); }""", bid)
    pg.wait_for_timeout(1300)


def sec_c(br):
    ctx, pg = booted(br, 440, 956, seed=USED, touch=True, dpr=2)
    try:
        pg.evaluate(CLEAN)
        pg.evaluate("() => document.documentElement.setAttribute('data-reduce-motion','true')")
        worst = 0
        for bid in ("exam100", "hundos250", "study50"):
            person(pg, bid)
            r = pg.evaluate("""() => { const c = document.querySelector('.person-card-cover'); const b = c.getBoundingClientRect(), s = getComputedStyle(c);
               return { x: b.left, y: b.top, w: b.width, h: b.height, rep: s.maskRepeat || s.webkitMaskRepeat }; }""")
            check("C (%s): the cover's fade never repeats" % bid, "no-repeat" in (r["rep"] or ""), r["rep"])
            # the cover with the portrait hidden, to read the banner's fade alone
            pg.evaluate("() => { const a = document.querySelector('.person-card-art'); if(a) a.style.visibility = 'hidden'; }")
            im = Image.open(io.BytesIO(pg.screenshot(clip={"x": r["x"] + 4, "y": r["y"], "width": r["w"] - 8, "height": r["h"] + 6}))).convert("L")
            W, H = im.size
            px = im.load()
            rows = [sum(px[x, y] for x in range(W)) / W for y in range(H)]
            lo = int(H * .45)
            step = max(abs(rows[y + 1] - rows[y]) for y in range(lo, H - 1))
            worst = max(worst, step)
            check("C (%s): the banner fades out with no hard step (max %.1f levels a row)" % (bid, step), step <= 9, round(step, 1))
    finally:
        ctx.close()


FOCUS = """(b) => { const c = document.querySelector('.profile-cover > .bnr'); return c ? getComputedStyle(c).transform : null; }"""


def sec_d(br):
    ctx, pg = booted(br, 440, 956, seed=USED, touch=True, dpr=1)
    try:
        pg.evaluate(CLEAN)
        pg.evaluate("() => { window.bannerEarned = () => true; }")
        for bid, moved in (("flare_umbra", True), ("flare_void", True), ("titan_rank", True), ("level80", True), ("tests250", False)):
            pg.evaluate("(b) => { store.banner = b; showProfile(); }", bid)
            pg.wait_for_timeout(600)
            t = pg.evaluate(FOCUS, bid)
            person(pg, bid)
            t2 = pg.evaluate("() => { const c = document.querySelector('.person-card-cover > .bnr'); return c ? getComputedStyle(c).transform : null; }")
            pg.evaluate("() => document.querySelector('.invite-overlay')?.remove()")
            ok = (t not in (None, "none") and t2 not in (None, "none")) if moved else (t in ("none",) and t2 in ("none",))
            check("D: %s %s on the Profile cover and the person card" % (bid, "is moved clear of the circle" if moved else "is left as drawn"), ok, (t, t2))
    finally:
        ctx.close()


def sec_e(br):
    for (w, h, dev) in ((440, 956, "iPhone 17 Pro Max"), (375, 667, "iPhone SE"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED, touch=True, dpr=2)
        try:
            pg.evaluate(CLEAN)
            pg.evaluate("() => { cfg.mode = 'drill'; showSetup(); }")
            pg.wait_for_timeout(1300)
            hs = pg.evaluate("() => [...document.querySelectorAll('.picks > label.pick')].map(p => Math.round(p.getBoundingClientRect().height * 2) / 2)")
            check("E (%s): every unit card is the same height" % dev, len(hs) >= 8 and max(hs) - min(hs) <= 1, sorted(set(hs)))
        finally:
            ctx.close()


def sec_f(br):
    ctx, pg = booted(br, 440, 956, seed=USED, touch=True, dpr=3)
    try:
        pg.evaluate(CLEAN)
        pg.evaluate("() => { cfg.mode = 'drill'; showSetup(); }")
        pg.wait_for_timeout(1200)
        b = pg.evaluate("() => { const l = document.querySelector('.picks > label.pick'); l.scrollIntoView({block:'center'}); const r = l.querySelector('.box').getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2}; }")
        pg.wait_for_timeout(300)
        pg.touchscreen.tap(b["x"], b["y"])
        pg.wait_for_timeout(900)
        r = pg.evaluate("""() => { const x = document.querySelector('.picks > label.pick > .box'); const s = getComputedStyle(x);
          const ins = (s.boxShadow.match(/[^,(]*(\\([^)]*\\))?[^,]*/g) || []).join('|');
          const parts = s.boxShadow.split(/,(?![^(]*\\))/).map(p => p.trim()).filter(p => /inset/.test(p)).map(p => (p.replace(/(rgba?|color)\\([^)]*\\)/g, '').match(/-?[\\d.]+px/g) || []).map(parseFloat));
          return { checked: x.parentElement.querySelector('input').checked, rep: s.backgroundRepeat, parts }; }""")
        hard = [p for p in r["parts"] if len(p) >= 3 and abs(p[1]) > 0 and p[2] <= 1]
        check("F: the picked circle has no hard inset lip under the tick", r["checked"] and not hard, r)
        check("F: the circle's top light is not repeated under its border", r["checked"] and r["rep"].startswith("no-repeat"), r["rep"])
    finally:
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        try:
            for f in (sec_a, sec_b, sec_c, sec_d, sec_e, sec_f):
                f(br)
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
