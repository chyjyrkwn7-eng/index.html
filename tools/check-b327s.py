#!/usr/bin/env python3
"""Build 327 (b327s): small quality-of-life fixes found walking the app.

Madison: "Can you please check the app for any quality of life fixes? Like
if anything could be better, removed, added, changed? ... Please make
necessary changes."

  s1. every back link, Select all and a banner's close x take a 44px tap
      (they measured 30, 34 and 28px), with nothing on screen moving.
  s2. the progress meter is one row however long the test (a 120-question
      drill drew six rows of blocks over the question; a whole Penal Code
      run ~17), and the block you are on stays readable.
  s3. on a narrow phone an app banner's button goes under its words (beside
      them the message was a ~120px column, six lines); on a 440px phone it
      stays beside them.
  s4. Test history and a test's own page name themselves in the header, and
      the list does not say "Test history" a second time.

  python3 tools/check-b327s.py [--against FILE]

Fails on e83f307.
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

check, booted, USED_ACCOUNT = cb.check, cb.booted, cb.USED_ACCOUNT

TAP = r"""(sel) => { const e = document.querySelector(sel); if(!e) return null;
  const r = e.getBoundingClientRect(); const a = getComputedStyle(e, '::after');
  const has = a.content && a.content !== 'none' && a.position === 'absolute';
  return { w: r.width, h: r.height, aw: has ? parseFloat(a.width) : 0, ah: has ? parseFloat(a.height) : 0 }; }"""


def big(t):
    return t and max(t["h"], t["ah"]) >= 43.5 and max(t["w"], t["aw"]) >= 43.5


def s1(br):
    for (w, h, dev) in ((440, 956, "phone"), (834, 1194, "iPad")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True, dpr=2)
        try:
            pg.evaluate("() => showTestReviewList()"); pg.wait_for_timeout(500)
            before = pg.evaluate("() => { const r = document.querySelector('#stage .back-link').getBoundingClientRect(); return [r.top, r.height]; }")
            t = pg.evaluate(TAP, "#stage .back-link")
            check("s1 %s: a back link takes a 44px tap" % dev, big(t), str(t))
            check("s1 %s: the back link itself is the size it was (nothing moved)" % dev, t and t["h"] < 40, str(t))
            pg.evaluate("() => { cfg.mode = 'drill'; showSetup(); }"); pg.wait_for_timeout(600)
            t = pg.evaluate(TAP, "#stage .selall-btn")
            check("s1 %s: Select all takes a 44px tap" % dev, big(t), str(t))
            pg.evaluate("""() => { const b = buildAppBanner('qa-banner', 'friend', 'Ana sent you a friend request', 'View', () => {}, () => {});
              document.body.appendChild(b); b.classList.add('show'); }""")
            pg.wait_for_timeout(300)
            t = pg.evaluate(TAP, "#qa-banner .app-banner-x")
            check("s1 %s: a banner's close x takes a 44px tap" % dev, big(t), str(t))
        finally:
            ctx.close()


def s2(br):
    return  # RETIRED IN 327g: Madison did not want the one-row meter (long tests became slivers); the meter wraps as it did.
    for (n, w, h, dev) in ((120, 440, 956, "phone"), (340, 440, 956, "phone"), (120, 834, 1194, "iPad")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True, dpr=2)
        try:
            pg.evaluate("""(n) => { cfg.mode = 'drill'; beginRun(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic === 'Penal Code').slice(0, n), null); }""", n)
            r = None
            for _ in range(40):
                pg.wait_for_timeout(250)
                r = pg.evaluate("""() => { const m = document.getElementById('meter'); const t = m ? [...m.querySelectorAll('.tick')] : [];
                  if(!t.length || m.hidden) return null; const tops = new Set(t.map(x => Math.round(x.getBoundingClientRect().top)));
                  const now = m.querySelector('.tick.now'); const mr = m.getBoundingClientRect();
                  return { n: t.length, rows: tops.size, h: mr.height, right: mr.right, vw: innerWidth,
                    nowW: now ? now.getBoundingClientRect().width : 0 }; }""")
                if r and r["n"] >= n:
                    break
            check("s2 %s, %d questions: the meter is one row" % (dev, n), r and r["rows"] == 1 and r["h"] < 14, str(r))
            check("s2 %s, %d questions: it stays on the screen" % (dev, n), r and r["right"] <= r["vw"] + 0.5, str(r))
            check("s2 %s, %d questions: the block you are on is still readable" % (dev, n), r and r["nowW"] >= 5.5, str(r))
        finally:
            ctx.close()


def s3(br):
    for (w, h, dev, under) in ((375, 667, "375px phone", True), (440, 956, "440px phone", False)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True, dpr=2)
        try:
            pg.evaluate("""() => { const b = buildAppBanner('qa-banner', 'friend', 'Ana Martinez sent you a friend request, open Friends to answer it', 'View', () => {}, () => {});
              document.body.appendChild(b); placeTopBanner(b); b.classList.add('show'); }""")
            pg.wait_for_timeout(500)
            r = pg.evaluate("""() => { const b = document.getElementById('qa-banner'); const q = s => b.querySelector(s).getBoundingClientRect();
              const body = q('.app-banner-body'), act = q('.app-banner-act'), x = q('.app-banner-x'), txt = b.querySelector('.app-banner-text');
              const lh = parseFloat(getComputedStyle(txt).lineHeight) || 15;
              return { below: act.top >= body.bottom - 1, xTop: x.top < body.bottom, lines: Math.round(txt.getBoundingClientRect().height / lh),
                bw: body.width, right: b.getBoundingClientRect().right, vw: innerWidth }; }""")
            if under:
                check("s3 %s: the button sits under the words" % dev, r["below"], str(r))
                check("s3 %s: the message is three lines or fewer" % dev, r["lines"] <= 3, str(r))
                check("s3 %s: the close x stays on the top row" % dev, r["xTop"], str(r))
            else:
                check("s3 %s: the button stays beside the words" % dev, not r["below"], str(r))
            check("s3 %s: the banner is on the screen" % dev, r["right"] <= r["vw"] + 0.5, str(r))
        finally:
            ctx.close()


def s4(br):
    for (w, h, dev) in ((440, 956, "phone"), (834, 1194, "iPad")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True, dpr=2)
        try:
            pg.evaluate("() => showTestReviewList()"); pg.wait_for_timeout(500)
            r = pg.evaluate("""() => ({ head: document.getElementById('count').textContent.trim(),
              twice: [...document.querySelectorAll('#stage .slab')].filter(e => /test history/i.test(e.textContent)).length,
              rows: document.querySelectorAll('#stage .thx-row').length })""")
            check("s4 %s: Test history names itself in the header" % dev, r["head"] == "Test history", str(r))
            check("s4 %s: and does not say it a second time" % dev, r["twice"] == 0, str(r))
            if r["rows"]:
                pg.evaluate("() => document.querySelector('#stage .thx-row').click()"); pg.wait_for_timeout(500)
                hd = pg.evaluate("() => document.getElementById('count').textContent.trim()")
                check("s4 %s: a test's own page keeps the header" % dev, hd == "Test history", hd)
            else:
                check("s4 %s: the fixture has tests to open" % dev, False, str(r))
        finally:
            ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            only = os.environ.get("ONLY", "")
            for fn in (s1, s2, s3, s4):
                if only and fn.__name__ not in only.split(","):
                    continue
                try:
                    fn(br)
                except Exception as e:
                    check("%s ran to the end" % fn.__name__, False, str(e)[:200])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
