#!/usr/bin/env python3
"""Build 327: Nova's recap gets a slide for a level that changed.

Madison: "Nova walk through, when he talks about how you are doing, add a
slide or something for the guys levels who changed. Mention that because
some people could be confused."

  o1. an existing account whose level went down on this update (live was
      313c, no level wall): right after the recap card, a slide of its own -
      the level it had struck, the level it has now, its XP "all of it
      kept", and the badges that lift it - and his two lines say from what
      to what, why, and that no XP was lost. The slide fits the stage on
      both reference devices and an SE; the recap card comes back after it.
  o2. an account whose level did not change: no such slide, nothing said.

  python3 tools/check-b327-o.py [--against FILE] [--shots DIR]

Fails on 651229b (no slide).
"""
import importlib.util, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

check, booted, USED_ACCOUNT = cb.check, cb.booted, cb.USED_ACCOUNT
SHOTS = None
if "--shots" in sys.argv:
    SHOTS = sys.argv[sys.argv.index("--shots") + 1]; os.makedirs(SHOTS, exist_ok=True)

SETUP = """(a) => { const U = topicsIn(QUESTIONS); store.unitPerfects = {}; U.slice(0, a[0]).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
  store.levelFloor = 0; store.rankFloor = 0; store.levelWallRule = 325; store.lifetime.points = xpForLevel(a[1]) + 10;
  store.rankUpShown = TIER_ORDER_FULL.length; saveStore();
  return { level: levelOf(store), was: legacyLevelOfPoints(store.lifetime.points), xp: store.lifetime.points }; }"""

# Walk his talk; at each line note what is on the stage.
WALK = r"""async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  showHome(); playNovaIntro(() => {}, { existing: true });
  for(let i = 0; i < 80 && !document.getElementById('nova-intro'); i++) await wait(100);
  const el = document.getElementById('nova-intro'); const nv = el.__nova;
  for(let i = 0; i < 60 && nv.index < 0; i++) await wait(100);
  const out = [];
  for(let g = 0; g < 60 && el.isConnected; g++){
    while(nv.typing){ nv.advance(); await wait(40); }
    await wait(900);
    const st = el.querySelector('.nt-stage');
    const lc = st.querySelector('.nt-prop:not(.is-prepped):not(.is-out) .nt-lc');
    const rc = st.querySelector('.nt-prop:not(.is-prepped):not(.is-out) .nt-rc');
    const one = { i: nv.index, text: el.querySelector('.nt-text').textContent, lc: null, rc: !!rc };
    if(lc){
      const r = lc.getBoundingClientRect(), s = st.getBoundingClientRect();
      const n = [...lc.querySelectorAll('.nt-lc-n')].map(x => x.textContent);
      one.lc = { was: n[0], now: n[1], struck: getComputedStyle(lc.querySelector('.is-was .nt-lc-n')).textDecorationLine,
        xp: (lc.querySelector('.nt-lc-xp') || {}).textContent || '', unlock: (lc.querySelector('.nt-lc-unlock') || {}).textContent || '',
        emblem: !!lc.querySelector('.nt-lc-unlock svg'), shown: getComputedStyle(lc).opacity,
        inView: r.top >= s.top - 1 && r.bottom <= s.bottom + 1 && r.left >= -1 && r.right <= innerWidth + 1 };
    }
    out.push(one);
    const go = el.querySelector('.nt-go');
    if(go && getComputedStyle(go).display !== 'none') break;
    nv.advance(); await wait(80);
  }
  return out;
}"""


def run(br, w, h, dev, badges, lvl, shot=None):
    ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
    st = pg.evaluate(SETUP, [badges, lvl])
    if shot:
        pg.evaluate("() => { window.__shotAt = null; }")
    steps = pg.evaluate(WALK) if not shot else None
    if shot:
        # walk again, stopping on the slide to photograph it
        pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          showHome(); playNovaIntro(() => {}, { existing: true });
          for(let i = 0; i < 80 && !document.getElementById('nova-intro'); i++) await wait(100);
          const el = document.getElementById('nova-intro'), nv = el.__nova;
          for(let i = 0; i < 60 && nv.index < 0; i++) await wait(100);
          for(let g = 0; g < 60; g++){ while(nv.typing){ nv.advance(); await wait(40); }
            if(/went from/.test(el.querySelector('.nt-text').textContent)) break; nv.advance(); await wait(80); }
          await wait(1200); }""")
        pg.screenshot(path=os.path.join(SHOTS, shot + "-1.png"))
        pg.evaluate("""async () => { const el = document.getElementById('nova-intro'); el.__nova.advance(); await new Promise(r => setTimeout(r, 80));
          while(el.__nova.typing){ el.__nova.advance(); await new Promise(r => setTimeout(r, 40)); } await new Promise(r => setTimeout(r, 1200)); }""")
        pg.screenshot(path=os.path.join(SHOTS, shot + "-2.png"))
    ctx.close()
    return st, steps


def o1(br):
    print("\no1. a level that changed gets its own slide, straight after the recap")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11"), (375, 667, "SE 2/3")):
        st, steps = run(br, w, h, dev, 1, 45)
        texts = [s["text"] for s in steps]
        ri = next((i for i, s in enumerate(steps) if s["rc"]), -1)
        li = next((i for i, s in enumerate(steps) if s["lc"]), -1)
        lc = steps[li]["lc"] if li >= 0 else None
        check("%s: level %d before, %d now - the account is one whose level changed" % (dev, st["was"], st["level"]), st["was"] > st["level"], st)
        check("%s: the slide comes straight after the recap card" % dev, ri >= 0 and li == ri + 1, {"recap": ri, "slide": li})
        check("%s: it shows the old level struck, the new one, the XP all kept, and the badges for the next rank with its emblem" % dev,
              lc and lc["was"] == str(st["was"]) and lc["now"] == str(st["level"]) and "line-through" in lc["struck"]
              and "{:,} XP".format(st["xp"]) in lc["xp"] and "kept" in lc["xp"] and re.search(r"Find \d+ more badges? to reach \w+", lc["unlock"]) and lc["emblem"] and float(lc["shown"]) > .9,
              lc)
        check("%s: ...and it fits the stage" % dev, lc and lc["inView"], lc)
        said = " ".join(texts[li:li + 2]) if li >= 0 else ""
        check("%s: he says from what to what, why, and that no XP was lost" % dev,
              ("went from %d to %d" % (st["was"], st["level"])) in said and "one rank at a time" in said and "lose any XP" in said and "paid for" in said,
              said[:300])
        nxt = steps[li + 2] if li >= 0 and li + 2 < len(steps) else {}
        check("%s: after it, the recap card is back for what you've found" % dev, nxt.get("rc") and not nxt.get("lc") and "found" in nxt.get("text", ""), nxt)


def o2(br):
    print("\no2. a level that did not change: no slide")
    st, steps = run(br, 440, 956, "17 Pro Max", 3, 12)
    check("level %d before and now: no level-change slide, nothing said about it" % st["level"],
          st["was"] == st["level"] and not any(s["lc"] for s in steps) and not any("went from" in s["text"] for s in steps),
          [s["text"][:60] for s in steps])


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            for fn in (o1, o2):
                try:
                    fn(br)
                except Exception as e:
                    check("%s ran to the end" % fn.__name__, False, str(e)[:200])
            if SHOTS:
                for (w, h, n) in ((440, 956, "iphone-17-pro-max"), (834, 1194, "ipad-pro-11")):
                    run(br, w, h, n, 1, 45, shot=n + "-level-change")
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
