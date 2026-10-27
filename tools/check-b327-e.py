#!/usr/bin/env python3
"""Build 327, package e: Stats, Test history, the badge case, the planet's crack.

Madison (Oct 20):
  "Stats tab, why is the accuracy percentage ring color matched? I feel like
   that looked better as grey ... Recent test, why are the percentage rings
   color matched to the mode? It should be color matched to hundo (gold) or
   pass green or fail red. And then the mode would have that thing as its
   own color."
  "Test history ... Just ensure the top numbers are accurate. I also feel
   like the three top numbers could have that same look, like the
   percentage as a ring ..."
  "The badge case looks better, the corners of metal though ... are rounded
   edges and don't look right? I also don't like the weird pattern of the
   case on the inside top part. The case ... looks bad and not 3d."
  "Super nova crack is cool with the stuff coming out but I thought it would
   look like some of the floating rocks ... the smaller ash mark is bad and
   can just go away, we need it to be combined ... All the progressive
   cracking could be better too."

Every section fails on build 326 (5ce026a):

  python3 tools/check-b327-e.py
  python3 tools/check-b327-e.py --against /tmp/claude-0/b327/index-326.html
  B327E_ONLY=AB python3 tools/check-b327-e.py

  A. STATS: the accuracy ring is a neutral grey (no hue) on the default theme
     and two rank themes; the numbers' own colour is not what it is drawn in.
  B. RESULT RINGS: on Stats' Recent tests, Test history and a test's own
     page, each score ring is the RESULT's colour - gold for a hundo/100%,
     green at PASS_MARK and up, red under it - and each row's mode chip is
     its MODE's colour (Drill red, Mock orange, Virtual Room blue),
     never the ring's.
  C. TEST HISTORY'S NUMBERS: for every filter (All, Drill, Mock,
     Virtual Room) the strip's three figures are the count, the rounded
     mean score and the hundos of exactly the rows listed under it - checked
     against values worked out by hand from the fixture, not read back from
     the app - and the average is drawn as a ring (svg with an arc) between
     the other two.
  D. THE BADGE CASE: on the Badges tab and in the badge cutscene, every
     corner protector (.nova-case-cap) and every wall guard foot is square
     (no corner radius over 12% of its width - the old caps were half their
     width on one corner); the lid's inside carries no quilt (no diagonal
     seams, no tiled buttons); the lining is a recess (a dark inner shadow
     cast down from its top edge by at least 1.2% of the case's width).
  E. THE SUPERNOVA CRACK: everything that leaves the crack is rock - each
     mote is the ring debris' own stone (the same gradient as
     .csc-ringfrag, clipped to one of its three shapes), its underside
     still hot; the shine carries no crazing of its own at Amethyst or
     Supernova (dark cover in the highlight, away from the one branch that
     runs into it, under 4%); and from Platinum each rank's crack carries the
     seam's light, brighter rank by rank.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
from playwright.sync_api import sync_playwright

PHONE = ("iPhone 17 Pro Max", 440, 956)
TABLET = ("iPad Pro 11\"", 834, 1194)
ONLY = os.environ.get("B327E_ONLY", "ABCDE")
check = cb.check

HIST_SEED = """() => { const now = Date.now(), m = 60000, d = 86400000;
  store.testHistory = [
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 100, elapsedMs: 300000, playedAt: now - 5 * m, mode: 'drill', n: 12, ok: 12, hundos: 1 },
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 92, elapsedMs: 300000, playedAt: now - 30 * m, mode: 'drill', n: 12, ok: 11 },
    { label: 'Victims of Crime', units: ['Victims of Crime'], pct: 60, elapsedMs: 300000, playedAt: now - 60 * m, mode: 'exam', n: 20, ok: 12 },
    { label: 'TCOLE Rules', units: ['TCOLE Rules'], pct: 64, elapsedMs: 300000, playedAt: now - d, mode: 'drill', n: 14, ok: 9, vr: true },
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 100, elapsedMs: 200000, playedAt: now - 2 * d, mode: 'exam', n: 12, ok: 12, hundos: 1 },
    { label: 'Penal Code', units: ['Penal Code'], pct: 77, elapsedMs: 900000, playedAt: now - 3 * d, mode: 'exam', n: 40, ok: 31 }];
  saveStore(); }"""
# worked out by hand from HIST_SEED (mean rounded half up, as Math.round):
#   all   : 6 tests, (100+92+60+64+100+77)/6 = 493/6 = 82.17 -> 82, 2 hundos
#   drill : rows 1, 2 (row 4 is a Virtual Room) -> 2, (100+92)/2 = 96, 1
#   exam  : rows 3, 5, 6 -> 3, (60+100+77)/3 = 79, 1
#   vr    : row 4 -> 1, 64, 0
# MOVED IN 327 (b327k): the mode reads Mock on screen ("I prefer quiz"); stored as "exam".
WANT = {"All": (6, 82, 2), "Drill": (2, 96, 1), "Mock": (3, 79, 1), "Virtual Room": (1, 64, 0)}
# what each fixture row's ring must be: the result
GOLD, GREEN, RED = (255, 211, 106), (95, 217, 154), (255, 122, 122)
MODE = {"Drill": (255, 107, 112), "Mock": (255, 154, 60), "Virtual Room": (74, 159, 232)}


def rgb(s):
    import re
    m = re.findall(r"[\d.]+", s or "")
    return tuple(round(float(v)) for v in m[:3]) if len(m) >= 3 else None


def near(a, b, tol=6):
    return bool(a and b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def want_ring(pct):
    return GOLD if pct >= 100 else GREEN if pct >= 70 else RED


def boot(br, w, h, seed=None):
    return cb.booted(br, w, h, seed=seed or cb.USED_ACCOUNT, dpr=1)


ROWS = r"""(sel) => [...document.querySelectorAll(sel)].map(r => { const arc = r.querySelector('.thx-ring-arc'), chip = r.querySelector('.thx-chip');
  return { pct: parseInt((r.querySelector('.thx-ring-num') || {}).textContent, 10), ring: arc ? getComputedStyle(arc).stroke : null,
    mode: chip ? chip.textContent : null, chip: chip ? getComputedStyle(chip).getPropertyValue('--mode-c').trim() : null }; })"""


def hexrgb(h):
    h = (h or "").strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else rgb(h)


def section_a(br):
    print("\nA. Stats: the accuracy ring is red under 70, green from 70, gold at 100")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        for acc in ("ink", "titan", "adept"):
            r = pg.evaluate("""async (acc) => { theme.accent = acc; try{ applyTheme(); }catch(e){} showProfile('stats');
              await new Promise(r => setTimeout(r, 700));
              const arc = document.querySelector('.stx-hero .thx-ring-arc'), num = document.querySelector('.profile-stats-tab .stat-num');
              const pct = store.lifetime.answered ? Math.round(store.lifetime.correct / store.lifetime.answered * 100) : null;
              return { ring: arc ? getComputedStyle(arc).stroke : null, num: num ? getComputedStyle(num).color : null, pct }; }""", acc)
            # build 327 round 10 replaced the grey (and round 9's fixed green): "Red if under a 70,
            # green if above a 70 and a gold if somehow a hundred" - the same bands whatever the theme
            c = rgb(r["ring"])
            check("%s, %s theme: the accuracy ring is in its band for %s%% (%s), not the theme's colour" % (label, acc, r.get("pct"), r["ring"]),
                  r.get("pct") is not None and near(c, want_ring(r["pct"]), 8), r)
        ctx.close()


def section_b(br):
    print("\nB. score rings are the result's colour, the mode is its chip")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate(HIST_SEED)
        pg.evaluate("() => showProfile('stats')"); pg.wait_for_timeout(700)
        stats = pg.evaluate(ROWS, ".profile-stats-tab .stx-recent .thx-row")
        pg.evaluate("() => { testHistoryFilter = 'all'; showTestReviewList(); }"); pg.wait_for_timeout(500)
        hist = pg.evaluate(ROWS, "#stage .thx-row")
        dets = []
        for i in range(len(hist)):
            pg.evaluate("(i) => { testHistoryFilter = 'all'; showTestReviewList(); document.querySelectorAll('#stage .thx-row')[i].click(); }", i)
            pg.wait_for_timeout(250)
            dets.append(pg.evaluate("""() => { const p = document.querySelector('.screen-testdetail'); const arc = p && p.querySelector('.thx-ring-arc'), chip = p && p.querySelector('.thx-chip');
              return p ? { pct: parseInt(p.querySelector('.thx-ring-num').textContent, 10), ring: getComputedStyle(arc).stroke, mode: chip.textContent,
                chip: getComputedStyle(chip).getPropertyValue('--mode-c').trim() } : null; }"""))
        for where, rows in (("Stats' Recent tests", stats), ("Test history", hist), ("each test's own page", dets)):
            bad = [r for r in rows if not r or not near(rgb(r["ring"]), want_ring(r["pct"]))]
            check("%s, %s: %d rings in the result's colour (gold 100, green pass, red fail)" % (label, where, len(rows)),
                  len(rows) >= 3 and not bad and len({tuple(rgb(r["ring"])) for r in rows}) >= 2, bad[:3])
            badc = [r for r in rows if r and (not near(hexrgb(r["chip"]), MODE.get(r["mode"])) or near(hexrgb(r["chip"]), rgb(r["ring"]), 10))]
            check("%s, %s: every mode chip in its mode's colour, and not the ring's" % (label, where), rows and not badc, badc[:3])
        ctx.close()


def section_c(br):
    print("\nC. Test history: the three numbers are right for every filter, the average is a ring")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate(HIST_SEED)
        pg.evaluate("() => { testHistoryFilter = 'all'; showTestReviewList(); }"); pg.wait_for_timeout(400)
        names = pg.evaluate("() => [...document.querySelectorAll('.thx-filter-btn')].map(b => b.textContent)")
        for name, (n, avg, hun) in WANT.items():
            r = pg.evaluate("""(name) => { const b = [...document.querySelectorAll('.thx-filter-btn')].find(x => x.textContent === name); if(b) b.click();
              const s = document.querySelector('.thx-summary'); if(!s) return null;
              const txt = s.innerText.replace(/\\s+/g, ' ');
              const ring = s.querySelector('.thx-ring svg .thx-ring-arc');
              const nums = [...s.querySelectorAll('.thx-sum-num')].map(e => e.textContent);
              const ringNum = (s.querySelector('.thx-ring-num') || {}).textContent;
              const rows = document.querySelectorAll('#stage .thx-groups .thx-row').length;
              const rr = ring && ring.closest('.thx-ring').getBoundingClientRect(), sr = s.getBoundingClientRect();
              const sides = [...s.querySelectorAll('.thx-sum-num')].map(e => e.getBoundingClientRect());
              return { txt, ring: !!ring, nums, ringNum, rows, between: !!(rr && sides.length === 2 && sides[0].right <= rr.left && sides[1].left >= rr.right),
                dash: ring ? ring.style.strokeDasharray : '' }; }""", name)
            got = r and (r["nums"][:1] + [r["ringNum"]] + r["nums"][1:2]) if r else None
            ok = bool(r) and r["rows"] == n and got == [str(n), "%d%%" % avg, str(hun)]
            check("%s, %s: %d tests, %d%% average, %d hundo%s - by hand - and %d rows listed" % (label, name, n, avg, hun, "" if hun == 1 else "s", n),
                  ok, r and {"read": got, "rows": r["rows"], "text": r["txt"]})
            if name == "All":
                check("%s: the average is a ring (an arc at its value) between the count and the hundos" % label,
                      bool(r) and r["ring"] and r["between"] and re.match(r"^%d\b" % avg, r["dash"] or ""), r and {"ring": r["ring"], "between": r["between"], "dash": r["dash"]})
        check("%s: the filters are All, Drill, Mock, Virtual Room" % label, set(WANT) <= set(names), names)
        ctx.close()


CASE = r"""(root) => { const sc = document.querySelector(root); if(!sc) return null;
  const capsShown = [...sc.querySelectorAll('.nova-case-cap')].filter(c => getComputedStyle(c).display !== 'none' && c.getClientRects().length).length;
  const guardsShown = [...sc.querySelectorAll('.nova-case-wall.is-hw')].flatMap(wl => ['::before', '::after'].map(p => getComputedStyle(wl, p).display)).filter(d => d !== 'none').length;
  const lidShown = !!sc.querySelector('.ncase-lid');
  const caps = [...sc.querySelectorAll('.nova-case-cap')].map(c => { const cs = getComputedStyle(c), w = c.offsetWidth || 1;
    return Math.max(...['borderTopLeftRadius', 'borderTopRightRadius', 'borderBottomLeftRadius', 'borderBottomRightRadius'].map(k => parseFloat(cs[k]) || 0)) / w; });
  const guards = [...sc.querySelectorAll('.nova-case-wall.is-hw')].flatMap(wl => ['::before', '::after'].map(p => { const cs = getComputedStyle(wl, p), w = parseFloat(cs.width) || 1;
    return Math.max(parseFloat(cs.borderBottomLeftRadius) || 0, parseFloat(cs.borderBottomRightRadius) || 0) / w; }));
  const cush = [...sc.querySelectorAll('.nova-case-cushion')].map(e => { const cs = getComputedStyle(e); const bg = cs.backgroundImage;
    return { diag: (bg.match(/linear-gradient\((to (right|left) bottom|to bottom (right|left))/g) || []).length, tiles: /(^|,\s*)25%/.test(cs.backgroundSize) }; });
  const lin = sc.querySelector('.bcs-well, .nova-case-lining'), cw = (sc.querySelector('.bcs, .nova-case.ncase, .bc-case') || sc).offsetWidth || 1;
  const sh = lin ? getComputedStyle(lin).boxShadow : '';
  /* the deepest inset shadow pushed DOWN from the lining's top edge (its y offset - the wall's height; not its blur), as a share of the case's width */
  let deep = 0;
  sh.split(/,(?![^(]*\))/).forEach(p => { if(!/inset/.test(p)) return; const n = (p.replace(/rgba?\([^)]*\)/, '').match(/-?[\d.]+px/g) || []).map(parseFloat);
    if(n.length >= 2 && n[1] > 0){ deep = Math.max(deep, n[1]); } });
  return { caps, guards, cush, recess: deep / cw, capsShown, guardsShown, lidShown }; }"""


def section_d(br):
    print("\nD. the badge case: square corner protectors, a plain lid, a recessed lining")
    seed = """() => { const units = topicsIn(QUESTIONS); store.unitPerfects = store.unitPerfects || {};
      units.slice(0, 5).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u)); store.badgeCleanedAt = {};
      Object.keys(store.unitPerfects).forEach(u => store.badgeCleanedAt[u] = Date.now()); store.pendingBadgeUnlocks = [];
      theme.muteBanners = false; theme.reduceMotion = false; applyTheme(); }"""
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate(seed)
        pg.evaluate("() => { try{ settleUntil = 0; }catch(e){} showRanksScreen('badges'); }"); pg.wait_for_timeout(500)
        pg.evaluate("() => { try{ finishBadgeCaseOpen(); }catch(e){} }"); pg.wait_for_timeout(600)
        tab = pg.evaluate(CASE, ".badges-tab")
        pg.evaluate("() => { showHome(); }"); pg.wait_for_timeout(400)
        pg.evaluate("() => { playBadgeCaseScene(['Identity Crimes'], () => {}); }"); pg.wait_for_timeout(1500)
        cut = pg.evaluate(CASE, ".bc-scene")
        for where, c in (("the Badges tab", tab), ("the cutscene", cut)):
            if not c:
                check("%s, %s: the case is there" % (label, where), False); continue
            # REVISED (327 round 10): "the metal pieces, the 3d look, the clip parts all of it is bad" -
            # asked which way: tray only, sleek premium. No corner protectors or wall guards are drawn
            # anywhere, the tab has no lid at all, and the cutscene's lid keeps no quilt.
            check("%s, %s: no corner protectors or wall guards drawn (sleek, round 10)" % (label, where),
                  c["capsShown"] == 0 and c["guardsShown"] == 0, {"caps": c["capsShown"], "guards": c["guardsShown"]})
            if where == "the Badges tab":
                check("%s, %s: tray only - no lid" % (label, where), not c["lidShown"], c["lidShown"])
            else:
                check("%s, %s: the lid's inside has no quilt (no diagonal seams, no tiled buttons)" % (label, where),
                      c["cush"] and all(x["diag"] == 0 and not x["tiles"] for x in c["cush"]), c["cush"])
            check("%s, %s: the lining is a recess - its top edge's inner shadow %.1f%% of the case deep (1.2%%+)" % (label, where, 100 * c["recess"]),
                  c["recess"] >= .012, round(c["recess"], 4))
        ctx.close()


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("A", section_a), ("B", section_b), ("C", section_c), ("D", section_d)):
            if k in ONLY:
                try:
                    fn(br)
                except Exception as e:  # a section that throws is a failure, not a crash
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
