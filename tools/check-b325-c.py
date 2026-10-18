#!/usr/bin/env python3
"""Build 325, stream C - levels, XP, the rank-up journey, Supernova.

Madison's list, item by item, each held by checks that FAIL on build 324
(/tmp/claude-0/wbase325/index.html) and pass here:

  python3 tools/check-b325-c.py
  python3 tools/check-b325-c.py --against /path/to/324/index.html

  A. THE LEVEL WALL IS THE NEXT RANK'S LEVEL ("for platinum it says reach
     level 50, that should be your max level"), for every badge count and
     rank floor; and NOBODY'S SHOWN LEVEL OR RANK DROPS for it: a sample
     of build-324 states (a grid, plus the live board's published XP,
     badges and levels of Oct 18 - numbers only, no names, no codes) loads
     at exactly the level 324 showed, once, idempotently, through merges
     both ways and a reload; a reset and a new account start under the new
     rule. The copy that explains it says the new rule.
  B. Profile's XP bar is at its value from the first frame (no glide).
  C. While a rank-up waits, the Profile tab makes its "something new"
     gesture - grows, rings and shakes - once a call, every few seconds,
     and on a refused tap; never under Reduce motion.
  D. (moved in 326 - see check-b326-c.py A) the climb spends the extra
     where it stands, no pool; a climb that stops at the next wall ends
     with its bar full.
  E. The results XP card: plain lines with their sums, a Bonuses heading,
     and "base + bonuses = total" under the total, which adds up.
  F. No black rings: every secret flare plus Supernova is the orange tier.
  G. The ring streak runs on Home at random times too, and on a tap.
  H. Supernova's mark is a crack: no crater blob at the impact, a glow
     inside the fissures, no smoke.
  I. In a rank cutscene the secret flares orbit at the bubbles' pace.
  J. Opened from the road map, the cutscene's new flare is lit from the
     hand-off's first frame (the copy fades into the same lit flare).

Exits non-zero on any failure.
"""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
from playwright.sync_api import sync_playwright

PHONE = ("iPhone 17 Pro Max", 440, 956)
TABLET = ("iPad Pro 11\"", 834, 1194)
FAILURES = []
if "--against" in sys.argv:
    print("against: %s" % cb.SRC)


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:600]) if detail else ""))
    if not ok:
        FAILURES.append(name)


STANDALONE = """(() => { try{ Object.defineProperty(navigator, 'standalone', { get: () => true, configurable: true }); }catch(e){}
  const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q) ? { matches: true, media: q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} } : mm(q); })();"""


def boot(br, w, h, init=""):
    return cb.booted(br, w, h, seed=cb.USED_ACCOUNT, init=STANDALONE + init, touch=True)


# The live board on Oct 18 (read-only, public rankings rows): XP, badges and
# the level each row published - which build 324 computed with its wall and
# that account's own floor. Numbers only.
BOARD_OCT18 = [
    [300, 0, 2], [177645, 2, 63], [7770, 0, 18], [100, 0, 1], [46655, 0, 40], [26275, 0, 31], [19045, 0, 28],
    [53950, 0, 43], [9785, 0, 20], [42860, 0, 39], [100, 0, 1], [69745, 6, 48], [37635, 0, 36], [29485, 0, 33],
    [100, 0, 1], [138206, 2, 59], [26615, 0, 31], [22350, 0, 29], [5650, 0, 14], [63190, 5, 46], [83395, 1, 51],
    [42075, 0, 38], [11065, 0, 22], [1005, 0, 4], [8440, 0, 19], [2350, 0, 7], [58070, 1, 45], [15470, 0, 26],
    [11885, 0, 23], [60175, 0, 45], [7795, 0, 18], [26530, 0, 31], [23720, 0, 30], [100, 0, 1], [9445, 0, 20],
    [42020, 2, 38], [106905, 3, 55], [22152, 0, 29], [104554, 2, 55]]


# --------------------------------------------------------------------------
def section_wall(br):
    print("\nA. the level wall is the next rank's level, and nobody's level or rank drops for it")
    ctx, pg = boot(br, *PHONE[1:])
    r = pg.evaluate("""(board) => {
      const out = { errs: [] };
      try{
        out.tiers = TIER_ORDER_FULL.map(k => [TIER_UNLOCKS[k].level, TIER_UNLOCKS[k].badges]);
        out.cap = LEVEL_CAP;
        const units = topicsIn(QUESTIONS);
        const perf = n => Object.fromEntries(units.slice(0, n).map(u => [u, badgeThresholdFor(u)]));
        /* build 324's wall, written here so this runs on 324 too */
        const badgeWall324 = b => { const met = TIER_ORDER_FULL.filter(k => b >= TIER_UNLOCKS[k].badges).length, after = TIER_UNLOCKS[TIER_ORDER_FULL[met + 1]];
          return after ? Math.min(LEVEL_CAP, after.level - 1) : LEVEL_CAP; };
        /* 1. the wall for every badge count and rank floor */
        out.walls = [];
        for(let rf = 0; rf <= TIER_ORDER_FULL.length; rf++) for(let b = 0; b <= units.length; b++){
          const s = levelStateOf(xpForLevel(LEVEL_CAP) + 9000, b, 0, rf);
          out.walls.push([rf, b, s.level, s.wall, s.gateKey]);
        }
        /* the level shown never costs a rank the curve's level would hold */
        out.rankLoss = [];
        [5000, 20000, 39395, 66355, 87480, 120000, 160000, 260000].forEach(p => { for(let b = 0; b <= units.length; b++){
          const s = levelStateOf(p, b, 0, 0), a = rankOfStats(s.level, b, 0), c = rankOfStats(levelFromPoints(p), b, 0);
          if(TIER_ORDER_FULL.indexOf(a) < TIER_ORDER_FULL.indexOf(c)) out.rankLoss.push([p, b, s.level, a, c]); } });
        /* 2. build-324 states loaded fresh (no levelWallRule): the grid and the board */
        const docs = [];
        [3000, 9912, 14000, 17933, 22000, 27739, 35000, 44567, 52000, 61965, 80000, 108478, 140000, 200000, 400000].forEach(p =>
          [0, 1, 2, 3, 4, 5, 6, 7, 9, 12, 14].forEach(n => [0, 33].forEach(fl => docs.push({ p, n, fl }))));
        board.forEach(([p, n, lv]) => docs.push({ p, n, row: lv }));
        out.loads = docs.map(d => {
          const doc = { lifetime: { points: d.p }, unitPerfects: perf(d.n), onboardingComplete: true, firstName: 'x' };
          if(d.fl) doc.levelFloor = d.fl;
          if(d.row != null){
            /* the floor that explains the level the row published */
            applyLoadedData(Object.assign({}, doc, { levelWallRule: 325 })); retroHideBadges = null;
            const plain = Math.min(levelFromPoints(d.p), badgeWall324(badgeCountOf(store)));
            if(d.row > plain) doc.levelFloor = d.row;
          }
          applyLoadedData(JSON.parse(JSON.stringify(doc))); retroHideBadges = null; mergeHidePoints = null;
          const lv = levelOf(store), rk = TIER_ORDER_FULL.indexOf(rankOf(store)), flag = store.levelWallRule, floor = store.levelFloor;
          /* the next launch: the same copy again, as saved */
          applyLoadedData(JSON.parse(JSON.stringify(store))); retroHideBadges = null;
          return { p: d.p, n: d.n, fl: doc.levelFloor || 0, row: d.row, badges: badgeCountOf(store), curve: levelFromPoints(d.p),
                   lv, rk, flag, floor, lv2: levelOf(store), rk2: TIER_ORDER_FULL.indexOf(rankOf(store)) };
        });
        /* 3. one shot: XP earned after the update does not lift a
           grandfathered level the way the old rule would have */
        applyLoadedData({ lifetime: { points: xpForLevel(24) + 50 }, unitPerfects: {}, onboardingComplete: true });
        retroHideBadges = null;
        const g0 = levelOf(store);
        store.lifetime.points = xpForLevel(28) + 50;
        applyLoadedData(JSON.parse(JSON.stringify(store))); retroHideBadges = null;
        out.oneShot = { before: g0, after: levelOf(store), floor: store.levelFloor, flag: store.levelWallRule };
        /* 4. two devices: each migrated on its own, then merged both ways */
        const devA = (() => { applyLoadedData({ lifetime: { points: xpForLevel(26) + 10 }, unitPerfects: {}, onboardingComplete: true }); return JSON.parse(JSON.stringify(store)); })();
        const devB = (() => { applyLoadedData({ lifetime: { points: xpForLevel(28) + 10 }, unitPerfects: {}, onboardingComplete: true }); return JSON.parse(JSON.stringify(store)); })();
        const m1 = JSON.parse(JSON.stringify(devA)); mergeSameAccount(m1, devB);
        const m2 = JSON.parse(JSON.stringify(devB)); mergeSameAccount(m2, devA);
        const m3 = JSON.parse(JSON.stringify(m1)); mergeSameAccount(m3, m2);
        const old = JSON.parse(JSON.stringify(devA)); delete old.levelWallRule;
        const m4 = JSON.parse(JSON.stringify(m1)); mergeSameAccount(m4, old);
        out.merge = { a: [devA.levelFloor, devA.levelWallRule], b: [devB.levelFloor, devB.levelWallRule], m1: [m1.levelFloor, m1.levelWallRule],
                      m2: [m2.levelFloor, m2.levelWallRule], m3: [m3.levelFloor, m3.levelWallRule], m4: [m4.levelFloor, m4.levelWallRule] };
        /* 5. a new account and a reset start under the new rule */
        applyLoadedData({ lifetime: { points: 0 }, onboardingComplete: true });
        out.fresh = { flag: store.levelWallRule, floor: store.levelFloor };
        store.lifetime.points = xpForLevel(28); store.unitPerfects = {}; store.levelFloor = 33;
        wipeLocalProgressAndSettings();
        out.reset = { flag: store.levelWallRule, floor: store.levelFloor };
        store.lifetime.points = xpForLevel(28) + 10; store.unitPerfects = {}; retroHideBadges = null;
        out.reset.level = levelOf(store);
        /* 6. the copy */
        applyLoadedData({ lifetime: { points: xpForLevel(26) + 10 }, unitPerfects: {}, onboardingComplete: true, levelWallRule: 325 });
        retroHideBadges = null;
        const ls = levelStateFor(store);
        out.note = (ls.held && ls.saved > 0) ? levelGateNoteText(ls) : null;
        out.noteState = { level: ls.level, wall: ls.wall, gate: ls.gateKey, saved: ls.saved };
      }catch(e){ out.errs.push(String(e && e.stack || e)); }
      return out;
    }""", BOARD_OCT18)
    if r["errs"]:
        check("the wall section ran", False, r["errs"][0][:400])
        ctx.close()
        return
    tiers, CAP = r["tiers"], r["cap"]

    def new_cap(b, rf):
        for i, (lv, bd) in enumerate(tiers):
            if i >= rf and b < bd:
                return min(CAP, lv)
        return CAP

    def old_cap(b):
        met = sum(1 for lv, bd in tiers if b >= bd)
        return min(CAP, tiers[met + 1][0] - 1) if met + 1 < len(tiers) else CAP

    def rank_of(lv, b):
        held = -1
        for i, (tl, tb) in enumerate(tiers):
            if lv >= tl and b >= tb:
                held = i
        return held

    bad = [w for w in r["walls"] if w[2] != new_cap(w[1], w[0]) or w[3] != new_cap(w[1], w[0])]
    check("the cap is the level of the next rank not held, for every badge count 0-16 and rank floor 0-7 (unranked 21, Gold held 50, all held 80)",
          not bad, bad[:5])
    w0 = {(rf, b): lv for rf, b, lv, wall, g in r["walls"]}
    check("...e.g. 0 badges 21, 1 badge 30, 5 badges (Gold) 50, 12 badges 80; holding Silver by its floor with 2 badges, Gold's 40",
          [w0[(0, 0)], w0[(0, 1)], w0[(0, 5)], w0[(0, 12)], w0[(2, 2)]] == [21, 30, 50, 80, 40],
          [w0[(0, 0)], w0[(0, 1)], w0[(0, 5)], w0[(0, 12)], w0[(2, 2)]])
    check("...and the wall never costs a rank the XP's own level would hold", not r["rankLoss"] and not bad, r["rankLoss"][:4])

    loads = r["loads"]
    drops, rdrops, wrong, notflag, reload = [], [], [], [], []
    grandfathered = 0
    for d in loads:
        old_level = min(d["curve"], max(old_cap(d["badges"]), d["fl"]), CAP)
        new_level = min(d["curve"], max(new_cap(d["badges"], 0), d["fl"]), CAP)
        want = max(old_level, new_level)
        if d["lv"] < old_level:
            drops.append(d)
        if d["rk"] < rank_of(old_level, d["badges"]):
            rdrops.append(d)
        if d["lv"] != want:
            wrong.append((d, want))
        if d["flag"] != 325:
            notflag.append(d)
        if d["lv2"] != d["lv"] or d["rk2"] != d["rk"]:
            reload.append(d)
        if d.get("row") is not None and d["lv"] != d["row"]:
            wrong.append((d, "row"))
        if old_level > new_level:
            grandfathered += 1
    n_board = sum(1 for d in loads if d.get("row") is not None)
    check("%d build-324 states (a grid, and the %d rows of the live board) load at exactly the level 324 showed or the new rule's, whichever is higher - none lower, every board row its published level - under the new rule's flag"
          % (len(loads), n_board), not wrong and not drops and not notflag, (wrong or drops or notflag)[:3])
    # (with the flag: on 324 this would pass trivially - it IS 324's rule)
    check("...and no rank below the one 324 showed, with the new rule's flag set on every one", not rdrops and not notflag, (rdrops or notflag)[:3])
    check("...%d of them kept by a grandfather floor; every one carries levelWallRule 325 after the load" % grandfathered,
          grandfathered > 0 and not notflag, notflag[:3])
    check("...and loading the saved copy again changes nothing (idempotent)", not reload and not notflag, reload[:3])
    o = r["oneShot"]
    check("the floor is one shot: XP earned afterwards does not lift a grandfathered level the way the old rule would (24 stays 24 at XP for 28)",
          o["before"] == 24 and o["after"] == 24 and o["flag"] == 325, o)
    m = r["merge"]
    check("two devices that each ran it merge to the higher floor, either way round, flag kept - and a copy from an older build changes nothing",
          m["m1"] == m["m2"] == m["m3"] == m["m4"] == [max(m["a"][0], m["b"][0]), 325] and m["a"][1] == m["b"][1] == 325, m)
    check("a new account and a reset start under the new rule: flag 325, no floor, level capped at 21",
          r["fresh"] == {"flag": 325, "floor": 0} and r["reset"] == {"flag": 325, "floor": 0, "level": 21}, [r["fresh"], r["reset"]])
    note = r["note"] or []
    txt = " ".join(note)
    check("What's New's note says the new rule - your next rank's level - and never that a level 'went from' one to another",
          bool(note) and "next rank" in txt and "went from" not in txt and str(r["noteState"]["wall"]) in txt, [note, r["noteState"]])
    ctx.close()


# --------------------------------------------------------------------------
def section_profile_bar(br):
    print("\nB. Profile's XP bar is where it stands from the first frame - no fill from empty on opening")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        r = pg.evaluate("""async () => {
          store.lifetime.points = xpForLevel(14) + Math.round((xpForLevel(15) - xpForLevel(14)) * .6); store.unitPerfects = {}; store.levelFloor = 0; store.rankFloor = 0;
          showHome(); await new Promise(r => setTimeout(r, 300));
          const seen = [];
          let first = null, moved = [];
          /* the bar's value the moment it is put in the page, before any
             frame - and every transition it ever runs (a transform
             transition can finish on the compositor while the page is
             still busy building, so sampling alone can miss the glide) */
          const mo = new MutationObserver(() => { const f = document.querySelector('.screen-profile .pf-standing .pf-xpbar .xpbar-fill');
            if(f && first == null){ first = Math.round(new DOMMatrix(getComputedStyle(f).transform).m41 * 10) / 10; } });
          showProfile();
          { const f = document.querySelector('.screen-profile .pf-standing .pf-xpbar .xpbar-fill');
            if(f) first = Math.round(new DOMMatrix(getComputedStyle(f).transform).m41 * 10) / 10; }
          const t0 = performance.now();
          const take = () => { const f = document.querySelector('.screen-profile .pf-standing .pf-xpbar .xpbar-fill');
            if(f){ const m = new DOMMatrix(getComputedStyle(f).transform); seen.push([Math.round(performance.now() - t0), Math.round(m.m41 * 10) / 10]);
              f.getAnimations().forEach(a => { if(a.transitionProperty || a.animationName) moved.push(a.transitionProperty || a.animationName); }); } };
          const iv = setInterval(take, 40);
          await new Promise(res => { const tick = () => { take();
            if(performance.now() - t0 < 1600) requestAnimationFrame(tick); else res(); };
            requestAnimationFrame(tick); });
          clearInterval(iv);
          const f = document.querySelector('.screen-profile .pf-standing .pf-xpbar .xpbar-fill');
          return { seen, first, moved: [...new Set(moved)].filter(x => /transform/.test(x)), target: f && f.dataset.target };
        }""")
        xs = [s[1] for s in r["seen"]]
        check("%s: opening Profile, the bar's fill does not move in any frame for 1.6s (at %s%%)" % (label, r["target"]),
              len(xs) >= 3 and r["seen"][-1][0] >= 1200 and max(xs) - min(xs) < 0.6 and r["first"] is not None and abs(r["first"] - xs[-1]) < 0.6 and not r["moved"],
              [r["first"], r["moved"], len(xs), r["seen"][:2], r["seen"][-1:]])
        ctx.close()


# --------------------------------------------------------------------------
RU_HOME = """async () => {
  const U = topicsIn(QUESTIONS), t = 'Identity Crimes';
  store.unitPerfects = {}; U.filter(x => x !== t).slice(0, 5).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
  store.rankFloor = 0; store.levelFloor = 0; store.lifetime.points = xpForLevel(45) + 500;
  store.rankMapFx244 = true; store.rankMapSeen = 1; store.rankUpShown = 2; store.rankUpFrom = null;
  store.pendingBadgeUnlocks = []; store.retroBadgePending = []; store.mergeHold = null;
  try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
  saveStore(); showHome();
}"""


def section_nudge(br):
    print("\nC. while a rank-up waits, the Profile tab makes its call: it grows, rings and shakes, once a call")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate(RU_HOME)
        r = pg.evaluate("""async () => {
          const tab = document.getElementById('bottomtab-profile'), T0 = performance.now(), calls = [];
          let maxScale = 1, maxRot = 0, was = false;
          await new Promise(res => { const tick = () => {
            const on = tab.classList.contains('ru-nudge');
            if(on && !was) calls.push(Math.round(performance.now() - T0));
            was = on;
            const m = new DOMMatrix(getComputedStyle(tab).transform);
            const sc = Math.hypot(m.a, m.b), rot = Math.abs(Math.atan2(m.b, m.a) * 180 / Math.PI);
            if(sc > maxScale) maxScale = sc; if(rot > maxRot) maxRot = rot;
            if(performance.now() - T0 < 12500) requestAnimationFrame(tick); else res(); };
            requestAnimationFrame(tick); });
          const lock = document.body.classList.contains('rankup-lock');
          /* a refused tap calls once more, at once */
          const n0 = Number(tab.dataset.ruNudges) || 0;
          document.getElementById('bottomtab-rewards').click();
          await new Promise(r => setTimeout(r, 120));
          const refused = (Number(tab.dataset.ruNudges) || 0) - n0, label = getComputedStyle(tab.querySelector('.bottomtab-label')).color;
          return { lock, calls, maxScale: Math.round(maxScale * 100) / 100, maxRot: Math.round(maxRot * 10) / 10, refused, label };
        }""")
        gaps = [b - a for a, b in zip(r["calls"], r["calls"][1:])]
        check("%s: Home locks and the tab's gesture plays - it grows past 1.1x and turns (shakes)" % label,
              r["lock"] and r["maxScale"] >= 1.1 and r["maxRot"] >= 2, r)
        check("%s: ...again every few seconds while it waits (2+ calls in 12s, 4s+ apart - a call, not a loop), and on a refused tap" % label,
              len(r["calls"]) >= 2 and all(g >= 4000 for g in gaps) and r["refused"] >= 1, [r["calls"], gaps, r["refused"]])
        ctx.close()
    # Reduce motion: nothing moves
    ctx, pg = boot(br, *PHONE[1:])
    pg.evaluate("()=>{ theme.reduceMotion = true; applyTheme && applyTheme(); }")
    pg.evaluate(RU_HOME)
    r = pg.evaluate("""async () => {
      const tab = document.getElementById('bottomtab-profile'), T0 = performance.now(); let maxScale = 1;
      await new Promise(res => { const tick = () => { const m = new DOMMatrix(getComputedStyle(tab).transform); maxScale = Math.max(maxScale, Math.hypot(m.a, m.b));
        if(performance.now() - T0 < 4000) requestAnimationFrame(tick); else res(); }; requestAnimationFrame(tick); });
      return { lock: document.body.classList.contains('rankup-lock'), maxScale, nudges: Number(tab.dataset.ruNudges) || 0 };
    }""")
    check("Reduce motion: the tab is called but nothing on it moves", r["lock"] and r["maxScale"] < 1.01 and r["nudges"] >= 1, r)
    ctx.close()


# --------------------------------------------------------------------------
def section_pool(br):
    # MOVED IN 326: "The 'saved up' xp thing is not the move. The extra xp
    # would just stay where it was but I [would] subtract from the extra and it
    # would do it level after level". No pool any more: the number under the
    # bar starts on the extra and counts down level by level. The full check
    # is tools/check-b326-c.py A; this keeps the one thing build 325 added that
    # still stands - a climb that stops at the next wall ends with the bar full.
    print("\nD. (moved in 326) the climb spends the extra where it stands; a climb that stops at the next wall ends with the bar full")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        r = pg.evaluate("""async () => {
          const out = {};
          const U = topicsIn(QUESTIONS);
          store.unitPerfects = {}; U.slice(0, 5).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
          store.rankFloor = 0; store.levelFloor = 0; store.lifetime.points = xpForLevel(53) + 700; store.rankUpShown = 3;
          try{ localStorage.setItem(PF_XP_SEEN_KEY, String(store.lifetime.points)); }catch(e){}
          saveStore(); showProfile(); await new Promise(r => setTimeout(r, 900));
          const st = document.querySelector('.pf-standing');
          const from = levelStateOf(store.lifetime.points, 4, 0, 0), to = levelStateFor(store);
          out.to = [to.level, to.banked, to.stopped];
          rankUpStandingAt(st, from);
          let done = false, pool = false, first = null;
          rankUpStandingClimb(st, from, to, null, {}).then(() => { done = true; });
          const T0 = performance.now();
          await new Promise(res => { const tick = () => {
            if(document.querySelector('.pf-standing .ru-pool')) pool = true;
            if(first == null) first = Number(((document.querySelector('.pf-standing .xpnums-have') || {}).textContent || '').replace(/[^0-9]/g, ''));
            if(!done && performance.now() - T0 < 40000) requestAnimationFrame(tick); else res(); };
            requestAnimationFrame(tick); });
          out.pool = pool; out.first = first; out.extra = Math.round(from.into);
          const f = st.querySelector('.pf-xpbar .xpbar-fill');
          out.endFill = f ? getComputedStyle(f).getPropertyValue('--fill').trim() : null;
          return out;
        }""")
        check("%s: no Saved XP pool; the number starts on the extra where it was (%s)" % (label, r.get("extra")),
              not r.get("pool") and r.get("first") == r.get("extra"), r)
        check("%s: a climb that stops at the next wall ends with the bar full, not empty" % label,
              r["to"][2] and r.get("endFill") == "100%", [r["to"], r.get("endFill")])
        ctx.close()


# --------------------------------------------------------------------------
def section_xpcard(br):
    print("\nE. the results XP card adds up on its face")
    RUN = """async () => {
      const wait = ms => new Promise(r => setTimeout(r, ms));
      theme.reduceMotion = true; applyTheme && applyTheme(); store.seenFirstResultsTour = true;
      window.playBadgeCaseScene = (u, d) => { setTimeout(d, 30); return {}; };
      const units = ['Identity Crimes', 'Victims of Crime', 'TCOLE Rules'];
      cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = units;
      order = QUESTIONS.map((q,i) => [q,i]).filter(([q]) => units.indexOf((q.topic||'').trim()) >= 0 && inWholeUnit(q)).map(([,i]) => i);
      runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false; practiceTestMinutes = null; inVirtualRoom = false;
      attempts = {}; picked = {}; timedOutSet = {};
      order.forEach((qi, k) => { attempts[qi] = 1; picked[qi] = k % 9 === 4 ? (optionOrder(qi).indexOf(QUESTIONS[qi].answer) + 1) % optionOrder(qi).length : optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
      runStartTime = Date.now() - order.length * 9000; testInProgress = true; pos = order.length - 1;
      summarize();
      for(let i = 0; i < 300 && !document.querySelector('.rs-rewards.rs-done'); i++){ const sp = document.querySelector('.rs-spot.is-up'); if(sp) sp.click(); await wait(100); }
      const x = document.querySelector('#stage .rs-xp');
      const kids = [...x.children].map(e => e.className);
      const lines = [...x.querySelectorAll('.rs-xpline:not(.rs-xpkick)')].map(e => ({ name: (e.querySelector('.rs-xpline-name') || {}).textContent,
        sub: (e.querySelector('.rs-xpline-sub') || {}).textContent || null, val: Number(((e.querySelector('.rs-xpline-val') || {}).textContent || '').replace(/[^0-9]/g, '')) }));
      const kick = x.querySelector('.rs-xpkick');
      const kickAt = kick ? kids.indexOf(kick.className) : -1;
      return { lines, kick: !!kick, kickAt, kids, sum: (x.querySelector('.rs-xpsum') || {}).textContent || null,
               total: Number(((x.querySelector('.rs-xptotal-num') || {}).textContent || '').replace(/[^0-9]/g, '')), xpLines: lastRunResult && lastRunResult.xpLines };
    }"""
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        r = pg.evaluate(RUN)
        lines = r["lines"]
        check("%s: every line says how it was worked out (a sub-line under each), and none is named by its arithmetic ('47 correct x 10')" % label,
              len(lines) >= 4 and all(l["sub"] for l in lines) and not any(any(ch.isdigit() for ch in (l["name"] or "").split("×")[0]) for l in lines),
              lines)
        check("%s: the answers' line comes first, then a Bonuses heading over every other line" % label,
              r["kick"] and r["kickAt"] == 2 and lines and r["xpLines"] and r["xpLines"][0]["key"] == "correct", r["kids"][:5])
        import re as _re
        m = _re.match(r"^([\d,]+) for answers \+ ([\d,]+) in bonuses = ([\d,]+) XP$", r["sum"] or "")
        nums = [int(g.replace(",", "")) for g in m.groups()] if m else None
        check("%s: under the total, 'base + bonuses = total' - and it adds up, to the total shown and to the lines" % label,
              nums is not None and nums[0] + nums[1] == nums[2] == r["total"] == sum(l["val"] for l in lines) and nums[0] == lines[0]["val"],
              [r["sum"], r["total"], [l["val"] for l in lines]])
        ctx.close()


# --------------------------------------------------------------------------
def section_rings(br):
    print("\nF. no black rings: every secret flare and Supernova is the orange tier")
    ctx, pg = boot(br, *PHONE[1:])
    r = pg.evaluate("""async () => {
      store.supernovaAchieved = true; store.mysteryColorsFound = {}; MYSTERY_ORDER.forEach(k => store.mysteryColorsFound[k] = true);
      try{ localStorage.setItem('class26e.ringtier.seen', 'eclipse'); }catch(e){}
      saveStore(); showHome(); await new Promise(r => setTimeout(r, 1500));
      const rings = [...document.querySelectorAll('.panel.home .cosmic-orbit-ring')];
      return { tier: homeRingTier(), eclipse: rings.filter(x => x.classList.contains('cosmic-orbit-ring-eclipse')).length,
               orange: rings.filter(x => x.classList.contains('cosmic-orbit-ring-supernova')).length,
               drawing: !!document.querySelector('.panel.home .cosmic-hero-ringdraw'), seen: localStorage.getItem('class26e.ringtier.seen') };
    }""")
    check("with Supernova and every secret flare: the orange rings, no eclipse/black ring, and a device that last showed black settles on orange without a draw",
          r["tier"] == "supernova" and r["eclipse"] == 0 and r["orange"] >= 2 and not r["drawing"] and r["seen"] == "supernova", r)
    ctx.close()


# --------------------------------------------------------------------------
def section_streak(br):
    print("\nG. the ring streak runs on Home at random times too, and on a tap")
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, is_mobile=True)
    ctx.add_init_script(STANDALONE)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.ringtier.seen','supernova');"
                        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % cb.USED_ACCOUNT)
    pg = cb.open_page(ctx)
    pg.clock.install()
    pg.goto(cb.URL)
    pg.clock.run_for(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.evaluate("""()=>{ window.__whys = []; const o = homeRingStreak; homeRingStreak = function(h, why){ const r = o(h, why); if(r) __whys.push(why); return r; };
      store.supernovaAchieved = true;
      /* nothing owed on this Home: a reward card (Supernova hands some
         over) would hold every streak while it plays */
      try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); (u.hints || []).forEach(markFlareHintShown); homeUnlockPlaying = false; }catch(e){}
      store.pendingBadgeUnlocks = []; saveStore(); showHome(); }""")
    pg.clock.run_for(3000)
    pg.evaluate("()=>{ document.querySelectorAll('.rs-spot, .daily-alert, .scene-bridge, #intro-pop').forEach(n => n.remove()); try{ homeUnlockPlaying = false; }catch(e){} }")
    for i in range(10):
        pg.clock.run_for(5000)
    whys = pg.evaluate("()=>__whys.slice()")
    pg.evaluate("()=>{ __whys.length = 0; document.querySelectorAll('.sn-ringglint').forEach(g => g.remove()); if(typeof homeStreakRandTimer !== 'undefined') clearTimeout(homeStreakRandTimer); const s = [...document.querySelectorAll('.panel.home circle')].find(c => c.getAttribute('r') === '52' && /cosmicSphereGrad/.test(c.getAttribute('fill') || '')); window.__sph = !!s; s && s.dispatchEvent(new MouseEvent('click', { bubbles: true })); }")
    pg.clock.run_for(300)
    tap = pg.evaluate("()=>[__whys.slice(), document.querySelectorAll('.sn-ringglint').length, window.__sph]")
    pg.evaluate("()=>{ store.supernovaAchieved = false; __whys.length = 0; saveStore(); showHome(); }")
    for i in range(10):
        pg.clock.run_for(5000)
    below = pg.evaluate("()=>__whys.slice()")
    # one check: the random runs are new (324 has none); the tap and the
    # Supernova-only rule are the existing behaviour it must keep
    check("over 50s on a Supernova Home the streak comes on its own at random moments (why 'random') as well as with the pulse; a tap on the planet still runs it; never below Supernova",
          whys.count("random") >= 1 and "tap" in tap[0] and tap[1] > 0 and not below, [whys, tap, below])
    ctx.close()


# --------------------------------------------------------------------------
def section_scar(br):
    print("\nH. Supernova's mark is a crack with a faint light inside it, not a burn")
    ctx, pg = boot(br, *PHONE[1:])
    r = pg.evaluate("""async () => {
      const art = cosmicScarArt();
      if(!art) return { none: true };
      const N = art.n, g = art.burn.getContext('2d'), d = g.getImageData(0, 0, N, N).data;
      const e = art.ember ? art.ember.getContext('2d').getImageData(0, 0, N, N).data : null;
      const cx = (art.crater[0] / 100) * N, cy = (art.crater[1] / 100) * N, R = .2 * N / 2;
      /* the impact: how much of a disc round it is solid dark */
      let disc = 0, dark = 0;
      for(let y = Math.floor(cy - R); y <= cy + R; y++) for(let x = Math.floor(cx - R); x <= cx + R; x++){
        if((x - cx) ** 2 + (y - cy) ** 2 > R * R) continue; disc++; const k = (y * N + x) * 4; if(d[k + 3] > 170) dark++; }
      /* the light inside the crack: ember pixels away from the impact */
      let glowFar = 0;
      if(e) for(let y = 0; y < N; y++) for(let x = 0; x < N; x++){ const k = (y * N + x) * 4; if(e[k + 3] > 60 && Math.hypot(x - cx, y - cy) > R * 1.5) glowFar++; }
      store.supernovaAchieved = true; saveStore(); showHome(); await new Promise(r => setTimeout(r, 1500));
      return { darkShare: Math.round(dark / disc * 1000) / 1000, glowFar, smoke: document.querySelectorAll('.panel.home .csc-smoke').length,
               scar: !!document.querySelector('.panel.home .cosmic-scar') };
    }""")
    # MOVED IN 326: the arms are 1.9x wider ("a large large crack") and meet
    # at the impact, so more of the disc round it is crack - still no crater
    # (324's was all of it)
    check("no crater at the impact: under two thirds of the disc round it is solid dark (324: all of it; under half before 326's wider arms)",
          not r.get("none") and r["darkShare"] < 0.67, r)
    check("the fissures carry a light inside them along their length (ember pixels away from the impact)", r.get("glowFar", 0) > 150, r)
    check("no smoke rising off it on Home, and the mark is still there", r.get("scar") and r.get("smoke") == 0, r)
    ctx.close()


# --------------------------------------------------------------------------
def section_scene_flares(br):
    print("\nI. in a rank cutscene the secret flares orbit at the bubbles' pace, before and after the whirl")
    ctx, pg = boot(br, *PHONE[1:])
    r = pg.evaluate("""async () => {
      store.mysteryColorsFound = {}; MYSTERY_ORDER.forEach((k, i) => store.mysteryColorsFound[k] = i < 3);
      playTierCutscene('veteran', { from: 'ranger', onDone: () => {} });
      const ang = () => { const ov = document.getElementById('supernova-cutscene'); const h = ov && ov.querySelector('.rank-before .cosmic-hero-wrap');
        const d = h && h.querySelector(':scope > .cosmic-hero-orbitlayer:not(.cosmic-hero-orbitlayer-inner) .cosmic-flare-dot');
        const m = h && h.querySelector('.cosmic-hero-main'); if(!d || !m) return null;
        const a = d.getBoundingClientRect(), b = m.getBoundingClientRect();
        return Math.atan2(a.top + a.height / 2 - (b.top + b.height / 2), a.left + a.width / 2 - (b.left + b.width / 2)) * 180 / Math.PI; };
      const speed = async (ms) => { const a0 = ang(); await new Promise(r => setTimeout(r, ms)); const a1 = ang(); if(a0 == null || a1 == null) return null;
        let d = a1 - a0; while(d > 180) d -= 360; while(d < -180) d += 360; return Math.round(Math.abs(d) / ms * 1000 * 10) / 10; };
      await new Promise(r => setTimeout(r, 3200));
      const before = await speed(2000);
      const ov = document.getElementById('supernova-cutscene');
      for(let i = 0; i < 300 && !(ov.classList.contains('is-cutrest')); i++) await new Promise(r => setTimeout(r, 100));
      await new Promise(r => setTimeout(r, 600));
      const after = await speed(2000);
      const rk = ov.querySelector('.rank-before .rank-orbit');
      return { before, after, bubbles: rk ? parseFloat(getComputedStyle(rk).animationDuration) : null };
    }""")
    check("the outer secret flares turn 8+ degrees a second before the whirl and after it (Home's 3 read as standing still beside the bubbles' 12)",
          (r["before"] or 0) >= 8 and (r["after"] or 0) >= 8, r)
    ctx.close()


# --------------------------------------------------------------------------
def section_handoff(br):
    print("\nJ. from the road map, the flare goes into the planet system as the same lit flare, the same size, in the same place")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate(cb.B319_RU_SEED, {})
        pg.evaluate(cb.B319_RU_RUN, {})
        pg.evaluate("()=>{ showHome(); }")
        for i in range(80):
            if pg.evaluate("()=>document.body.classList.contains('rankup-lock')"):
                break
            pg.evaluate("()=>{ const sp=document.querySelector('.rs-spot.is-up'); if(sp) sp.click(); }")
            pg.wait_for_timeout(150)
        pg.evaluate("""()=>{ window.__hand = null; const orig = rankCutHandoff;
          rankCutHandoff = function(ov, sw, hb, key, ghost){ const r = orig(ov, sw, hb, key, ghost);
            const b = rankTierBadge(hb, key);
            const R = e => { const q = e.getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2, q.width]; };
            const g = R(ghost), bb = b ? R(b) : null;
            window.__hand = { took: r, key, lit: !!(b && b.classList.contains('cosmic-badge-lit')), glow: b ? b.style.getPropertyValue('--tier-glow') : null,
                              inBubble: !!(b && ghost && b.contains(ghost)), want: flareColorOf(key),
                              off: bb ? Math.round(Math.max(Math.abs(g[0] - bb[0]), Math.abs(g[1] - bb[1]), Math.abs(g[2] - bb[2])) * 10) / 10 : null,
                              g: g.map(Math.round), b: bb && bb.map(Math.round) };
            return r; }; }""")
        pg.evaluate("()=>document.getElementById('bottomtab-profile').click()")
        for i in range(1500):
            if pg.evaluate("()=>!!window.__hand"):
                break
            pg.wait_for_timeout(50)
        hnd = pg.evaluate("()=>window.__hand")
        # the size is the iPad's: the draw-back's finished fill (scale .84)
        # outlived getAnimations() and held a 220px copy at 185px, 59px off
        # the 72px bubble (on the iPhone .84 happened to be the right ratio)
        check("%s: the road map's circle lands in the scene's bubble - same centre and size within 2px - and that bubble is already lit in the flare's own colour (not the unlit glass it turned into)" % label,
              bool(hnd) and hnd["took"] and hnd["inBubble"] and hnd["lit"] and hnd["glow"] == hnd["want"] and hnd["off"] is not None and hnd["off"] <= 2, hnd)
        ctx.close()


def main():
    only = os.environ.get("ONLY")
    secs = [section_wall, section_profile_bar, section_nudge, section_pool, section_xpcard, section_rings,
            section_streak, section_scar, section_scene_flares, section_handoff]
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            for fn in secs:
                if only and fn.__name__.replace("section_", "") not in only.split(","):
                    continue
                try:
                    fn(br)
                except Exception as e:
                    check("%s ran" % fn.__name__, False, repr(e)[:400])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
