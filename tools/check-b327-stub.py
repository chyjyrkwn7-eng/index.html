#!/usr/bin/env python3
"""Build 327: nothing of the next stretch leaves a circle before its moment.

Madison's screenshot (Oct 21): Gold reached but not yet celebrated on the
road map, its circle still saying Locked, and a short bar of gold already
coming out under it - the 9px stub that joins the climbing line to the rank
above. It was drawn the moment the map was built. It is held dark now
(`.rankmap-roadstub.is-held`) until its line moves: the climb after the
celebration, or the ordinary fill.

  python3 tools/check-b327-stub.py
  python3 tools/check-b327-stub.py --against OLD_INDEX.html   (fails on 7259f20)
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

SEED = """() => { document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
  const units = topicsIn(QUESTIONS); store.unitPerfects = store.unitPerfects || {};
  units.slice(0, 5).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
  store.lifetime.points = xpForLevel(46) + 500; store.levelFloor = 0; store.levelWallRule = 325;
  store.rankMapSeen = TIER_ORDER_FULL.indexOf('ranger'); store.rankMapFx244 = true; store.rankUpShown = null;
  showRanksScreen('ranks'); }"""
READ = """() => [...document.querySelectorAll('.rankmap-roadstub')].map(e => ({ op: +getComputedStyle(e).opacity,
  pending: !!document.querySelector('.rankmap-stop.is-celebrate-pending') }))"""

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=cb.CHROME)
    for label, w, h in (cb.PHONE, cb.TABLET):
        ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT)
        pg.evaluate(SEED)
        seen = []
        for _ in range(12):
            pg.wait_for_timeout(250)
            seen += pg.evaluate(READ)
        early = [s for s in seen if s["pending"]]
        cb.check("%s: while Gold waits to be celebrated, no stub of the next stretch shows" % label,
                 bool(early) and all(s["op"] < .05 for s in early), early[:3])
        late = None
        for _ in range(60):
            pg.wait_for_timeout(500)
            r = pg.evaluate(READ)
            if r and not r[0]["pending"] and r[0]["op"] > .95: late = r; break
        cb.check("%s: and it comes on with the climb after the celebration" % label, bool(late), late)
        ctx.close()
    br.close()

fails = [f for f in getattr(cb, "FAILURES", [])]
print("ALL PASS" if not fails else "FAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
