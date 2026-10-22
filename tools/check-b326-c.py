#!/usr/bin/env python3
"""Build 326, package C - the extra XP spent level by level, a rank-up for
every rank crossed, the Supernova crack.

Madison's words, each held by checks that FAIL on build 325
(/tmp/claude-0/wbase325/index.html) and pass here:

  python3 tools/check-b326-c.py
  python3 tools/check-b326-c.py --against /tmp/claude-0/wbase325/index.html
  B326C_ONLY=A,B python3 tools/check-b326-c.py

  A. "The 'saved up' xp thing is not the move. The extra xp would just stay
     where it was but I [would] subtract from the extra and it would do it
     level after level, until it goes to your new current level."
     The climb on Profile: no "Saved XP" anywhere; the number under the bar
     starts as the extra it was (the XP into the wall level, past what the
     level asks) and only ever counts DOWN; each level it pays for comes off
     it ("-N XP", N that level's cost) while the bar fills the next level;
     at every step's end xpForLevel(level) + the number IS the total; it
     ends on the new current level (levelStateFor's) with the remainder.
     Both reference devices, plus the numbers on a grid of accounts.
  B. "you could technically rank up twice from one test ... they would go to
     main menu after the one rank up stuff is done, the character would
     vibrate or move again, and it would just do another cutscene."
     A real 100% that crosses Gold AND Platinum: two journeys, each its own
     cutscene in order (Silver->Gold, then Gold->Platinum), each its own
     reward card; Home between them, locked, the Profile tab calling again,
     Gold's flare lit and Platinum's still dark; the first climb stops at
     Platinum's level with the rest still extra, the second spends it; no
     rank skipped or shown twice; a reload between the two plays only the
     second; a three-rank jump plays three. An existing account owes nothing
     new; an older record (no `q`) reads as before.
  C. "I don't really like the supernova crack how it is ... there was a point
     where the supernova main menu crack animation was cool, it looked like
     there was a large large crack and you could see the stuff from the
     crack being sucked into the rings rotation". Home's Supernova planet:
     light leaves the crack and is drawn into the rings' turn (motes that
     start on the crack and end on a ring, moving with its spin), on both
     reference devices and every theme; a wide glowing seam; nothing under
     Reduce motion; transform/opacity only. The cutscene's detonation: the
     planet fractures - cracks run out from the impact with light through
     them - before the scar settles.

Exits non-zero on any failure.
"""
import importlib.util
import json
import os
import sys
import time

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
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:700]) if detail else ""))
    if not ok:
        FAILURES.append(name)


STANDALONE = """(() => { try{ Object.defineProperty(navigator, 'standalone', { get: () => true, configurable: true }); }catch(e){}
  const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q) ? { matches: true, media: q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} } : mm(q); })();"""


def boot(br, w, h, init="", seed=None):
    return cb.booted(br, w, h, seed=seed or cb.USED_ACCOUNT, init=STANDALONE + init, touch=True)


# --------------------------------------------------------------------------
# A. the climb
CLIMB = """async (a) => {
  const out = { errs: [] };
  try{
  const U = topicsIn(QUESTIONS);
  store.unitPerfects = {}; U.slice(0, a.badges).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
  store.rankFloor = 0; store.levelFloor = 0; store.levelWallRule = 325; store.lifetime.points = a.points; store.rankUpShown = 9;
  /* as the journey does: the XP counted as seen, so Profile's own knock does not run */
  try{ localStorage.setItem(PF_XP_SEEN_KEY, String(Math.round(levelStateFor(store).total))); }catch(e){}
  saveStore(); showProfile(); await new Promise(r => setTimeout(r, 900));
  const st = document.querySelector('.pf-standing');
  const from = levelStateOf(store.lifetime.points, a.badges - 1, 0, 0), to = levelStateFor(store);
  out.from = { level: from.level, into: Math.round(from.into), span: Math.round(from.span), stopped: from.stopped };
  out.to = { level: to.level, into: Math.round(to.into), span: Math.round(to.span), stopped: to.stopped, total: to.total };
  rankUpStandingAt(st, from);
  const xf = st.querySelector('.pf-xpbar .xpbar-fill'); xf.style.transition = 'none'; setBarFill(xf, Number(xf.dataset.target) || 0);
  const num = s => Number(String(s || '').replace(/[^0-9]/g, ''));
  out.before = { have: num((st.querySelector('.xpnums-have') || {}).textContent), need: num((st.querySelector('.xpnums-need') || {}).textContent),
                 level: (st.querySelector('.pf-level') || {}).textContent };
  const sc = {}, samples = [];
  let done = false;
  rankUpStandingClimb(st, from, to, null, sc).then(() => { done = true; });
  const T0 = performance.now();
  out.chips = []; out.saved = false; out.pool = false;
  await new Promise(res => { const tick = () => {
    const s = document.querySelector('.pf-standing');
    const f = s.querySelector('.pf-xpbar .xpbar-fill');
    samples.push({ t: Math.round(performance.now() - T0), lv: num((s.querySelector('.pf-level') || {}).textContent),
      have: num((s.querySelector('.xpnums-have') || {}).textContent), need: num((s.querySelector('.xpnums-need') || {}).textContent),
      fill: f ? parseFloat(getComputedStyle(f).getPropertyValue('--fill')) : null, extra: !!s.querySelector('.pf-xp-extra'),
      ex: num((s.querySelector('.pf-xp-extra-n') || {}).textContent) });
    if(/saved/i.test(s.textContent)) out.saved = true;
    if(s.querySelector('.ru-pool')) out.pool = true;
    s.querySelectorAll('.ru-spend-chip, .ru-pool-chip').forEach(c => { if(!c.dataset.seen){ c.dataset.seen = 1; out.chips.push(c.textContent); } });
    if(!done && performance.now() - T0 < 40000) requestAnimationFrame(tick); else res(); };
    requestAnimationFrame(tick); });
  out.n = samples.length;
  out.samples = samples;
  out.rec = sc.climb || null;
  out.spans = []; for(let L = from.level; L < to.level; L++) out.spans.push(xpForLevel(L + 1) - xpForLevel(L));
  out.xpFor = {}; for(let L = from.level; L <= to.level + 1; L++) out.xpFor[L] = xpForLevel(L);
  const f = st.querySelector('.pf-xpbar .xpbar-fill');
  out.endFill = f ? parseFloat(getComputedStyle(f).getPropertyValue('--fill')) : null;
  out.after = { have: num((st.querySelector('.xpnums-have') || {}).textContent), level: (st.querySelector('.pf-level') || {}).textContent };
  }catch(e){ out.errs.push(String(e && e.stack || e)); }
  return out;
}"""


def section_spend(br):
    print("\nA. the extra stays where it is and is spent level by level, down to the new current level")
    cases = [(PHONE, {"badges": 5, "points": None, "lv": 53, "plus": 700}), (TABLET, {"badges": 5, "points": None, "lv": 47, "plus": 300})]
    for (label, w, h), fx in cases:
        ctx, pg = boot(br, w, h)
        pts = pg.evaluate("(a) => xpForLevel(a.lv) + a.plus", fx)
        r = pg.evaluate(CLIMB, {"badges": fx["badges"], "points": pts})
        if r.get("errs"):
            check("%s: the climb ran" % label, False, r["errs"])
            ctx.close()
            continue
        fr, to, s = r["from"], r["to"], r["samples"]
        tot = to["total"]
        check("%s: no 'Saved XP' and no pool anywhere while it climbs (%d frames)" % (label, r["n"]),
              not r["saved"] and not r["pool"] and r["n"] >= 30, [r["saved"], r["pool"], r["n"]])
        # MOVED IN 327: "not sure what's up with the -xp stuff in the bar..
        # it could literally just be the xp that's the extra it goes down as
        # you level up." The line is the extra itself ("N extra XP": the XP
        # past the level the bar is full at), not "into / span"; it counts
        # down while the levels fill, and no "-N XP" comes off it.
        # MOVED IN 327 (round 6): "it should show the next level like normal
        # and so on but as the next level's bar goes up the extra xp would go
        # down to match it". The line is the ordinary "x / y XP" (here the full
        # wall level, span / span) AND, on the right, "N extra XP".
        # MOVED IN 327 round 7: "WHEN YOU HAVE EXTRA XP going into ranking up, the number
        # on the left will obviously be higher, but at the cutscene it would do the level
        # up effect/sound then go to the next level, THE NUMBER on the left would go into
        # the level?" No "N extra XP": the ordinary "x / y XP" with x past y, and x goes
        # into each new level. check-b327u B holds the climb in full.
        check("%s: it starts on the ordinary line with the extra IN the number - %s / %s XP at a full Level %s" % (label, fr["into"], fr["span"], fr["level"]),
              fr["stopped"] and s and s[0]["have"] == fr["into"] and s[0]["lv"] == fr["level"] and fr["into"] > fr["span"],
              [s[:2], fr])
        check("%s: no 'N extra XP' at any frame" % label, not any(x["extra"] for x in s), [x for x in s if x["extra"]][:2])
        lvs = []
        for x in s:
            if not lvs or lvs[-1] != x["lv"]:
                lvs.append(x["lv"])
        check("%s: level after level, one at a time, %s to %s" % (label, fr["level"], to["level"]),
              lvs == list(range(fr["level"], to["level"] + 1)), lvs)
        rec = r.get("rec") or {}
        steps = rec.get("steps") or []
        check("%s: each level's own cost comes off it (327: no '-N XP' shown - the extra going down is the telling)" % label,
              [st["cost"] for st in steps] == r["spans"] and len(r["chips"]) == 0,
              [[st["cost"] for st in steps], r["spans"], r["chips"]])
        check("%s: nothing lost - at every step xpForLevel(level) + the number is the total (%d)" % (label, tot),
              steps and all(st["sum"] == tot for st in steps) and all(int(r["xpFor"][str(st["level"])]) + st["have"] == tot for st in steps),
              [(st["level"], st["have"], st["sum"]) for st in steps][:6])
        # the bar fills each level: right after each level change it is near empty, and it rises
        fills_ok, bad = True, []
        for st in steps:
            L = st["level"]
            seg = [x["fill"] for x in s if x["lv"] == L and x["fill"] is not None]
            want = 100 * min(1, st["have"] / max(1, st["span"]))
            # near empty as the level opens, rising while the frames watch, and set where its numbers say at the step's end
            if len(seg) < 2 or min(seg[:2]) > 20 or max(seg) < min(want, min(seg[:2]) + 8) - 1 or abs((st.get("fill") or 0) - want) > 1.5:
                fills_ok = False; bad.append((L, seg[:3], max(seg) if seg else None, st.get("fill"), round(want, 1)))
        check("%s: and the bar fills each new level from empty as the extra goes in" % label, fills_ok, bad[:4])
        check("%s: it ends on the new current level (%s) with what is left (%s / %s XP)%s" % (label, to["level"], to["into"], to["span"], ", the bar full at the next wall" if to["stopped"] else ""),
              r["after"]["level"] == "Level %d" % to["level"] and r["after"]["have"] == to["into"] and (not to["stopped"] or r["endFill"] == 100),
              [r["after"], to, r["endFill"]])
        ctx.close()
    # the numbers on a grid: every journey's start and end, conserved, never lower
    ctx, pg = boot(br, 440, 956)
    g = pg.evaluate("""() => { const out = [];
      const U = topicsIn(QUESTIONS);
      for(const [b0, b1] of [[0, 1], [0, 3], [2, 3], [2, 5], [4, 5], [4, 7], [6, 9], [4, 9], [8, 12], [11, 14]])
      for(const lv of [21, 25, 30, 34, 40, 45, 50, 55, 60, 66, 72, 80]){
        store.unitPerfects = {}; U.slice(0, b1).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
        store.rankFloor = 0; store.levelFloor = 0; store.levelWallRule = 325;
        store.lifetime.points = xpForLevel(lv) + 137;
        const pts = store.lifetime.points;
        const shownIdx = TIER_ORDER_FULL.indexOf(rankOfStats(levelStateOf(pts, b0, 0, 0).level, b0, 0));
        store.rankUpShown = shownIdx + 1; store.rankUpFrom = { r: shownIdx, b: b0, p: pts };
        const held = TIER_ORDER_FULL.indexOf(rankOf(store));
        if(held <= shownIdx) continue;
        const real = levelStateFor(store);
        let prevEnd = null, n = 0, bad = null;
        while(rankUpOwed() && n < 9){
          const o = rankUpOwed(); const step = typeof rankUpStepOf === 'function' ? rankUpStepOf(o) : o;
          const N = rankUpSceneNumbers(step);
          const end = N.end || real;
          const sum = st => xpForLevel(st.level) + Math.round(st.into);
          /* (level 80 is the cap: its numbers are the top band's, not a level's) */
          if(end.level < LEVEL_CAP && (sum(N.cap) !== Math.round(real.total) || sum(end) !== Math.round(real.total))) bad = bad || ['sum', n, sum(N.cap), sum(end), real.total];
          if(end.level < N.cap.level) bad = bad || ['down', n, N.cap.level, end.level];
          if(prevEnd != null && N.cap.level !== prevEnd) bad = bad || ['gap', n, prevEnd, N.cap.level];
          prevEnd = end.level; n++;
          rankUpMarkShown(step.toIdx);
        }
        out.push({ b0, b1, lv, steps: n, crossed: held - shownIdx, last: prevEnd, real: real.level, bad });
      }
      return out; }""")
    multi = [x for x in g if x["crossed"] > 1]
    check("the numbers, on %d rank-ups (%d crossing more than one rank): one journey per rank crossed, each starting where the last ended, the XP the same total at both ends of every one, never lower, the last on the real level" % (len(g), len(multi)),
          g and multi and all(x["steps"] == x["crossed"] and x["last"] == x["real"] and not x["bad"] for x in g),
          [x for x in g if x["steps"] != x["crossed"] or x["last"] != x["real"] or x["bad"]][:5])
    ctx.close()


# --------------------------------------------------------------------------
# B. a rank-up for every rank crossed
# From Home: wait for the lock, tap the Profile tab, and record the journey
# until it hands back; again while anything is owed. Cutscenes are stood in
# for unless a.real (the real ones are check_b320d_rankup's and C's).
QUEUE_WALK = """async (a) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const out = { journeys: [], homes: [], threw: null };
  try{
  const realTier = window.playTierCutscene, realSn = window.playSupernovaCutscene;
  if(!a.real){
    const fake = (key, opts) => { const j = out.journeys[out.journeys.length - 1]; if(j) j.cuts.push({ key, from: opts && opts.from });
      const ov = document.createElement('div'); ov.id = 'supernova-cutscene'; ov.className = 'tier-cutscene'; document.body.appendChild(ov);
      setTimeout(() => { ov.remove(); openSceneBridge(RANK_COLOR[key], { plain: true }); opts && opts.onDone && opts.onDone(); }, a.cutMs || 300); return {}; };
    window.playTierCutscene = fake; window.playSupernovaCutscene = o => fake('titan', o);
  } else {
    window.playTierCutscene = (k, o) => { const j = out.journeys[out.journeys.length - 1]; if(j) j.cuts.push({ key: k, from: o && o.from }); return realTier(k, o); };
    window.playSupernovaCutscene = o => { const j = out.journeys[out.journeys.length - 1]; if(j) j.cuts.push({ key: 'titan', from: o && o.from }); return realSn(o); };
  }
  if(!document.querySelector('[data-screen="home"]')) showHome();
  const tab = document.getElementById('bottomtab-profile');
  const flare = k => { const b = document.querySelector('.panel.home .cosmic-icon-badge[data-rank-tier="' + k + '"]'); return b ? b.classList.contains('cosmic-badge-lit') : null; };
  const total0 = Number(store.lifetime.points);
  for(let n = 0; n < (a.max || 4); n++){
    /* Home: locked, the tab calling */
    let nudges0 = Number(tab.dataset.ruNudges) || 0, sawNudge = false;
    for(let i = 0; i < 160 && !document.body.classList.contains('rankup-lock'); i++){
      const sp = document.querySelector('.rs-spot.is-up'); if(sp) sp.click();
      await wait(100);
    }
    const t1 = performance.now();
    while(performance.now() - t1 < 2600){ if(tab.classList.contains('ru-nudge')) sawNudge = true; await wait(40); }
    const owed = rankUpOwed();
    const home = { lock: document.body.classList.contains('rankup-lock'), call: tab.classList.contains('ru-call'),
      nudges: (Number(tab.dataset.ruNudges) || 0) - nudges0, sawNudge, onHome: !!document.querySelector('[data-screen="home"]'),
      owed, shown: store.rankUpShown, lit: {}, screen: (stage.firstElementChild || {}).className || null, tabColor: tab.style.getPropertyValue('--ru-color') || null,
      tabBar: !!document.querySelector('.bottomtabs') && getComputedStyle(document.querySelector('.bottomtabs')).visibility !== 'hidden' };
    TIER_ORDER_FULL.forEach(k => home.lit[k] = flare(k));
    out.homes.push(home);
    if(!owed) break;
    if(a.reloadAt === n){ out.reloadHere = true; break; }
    /* a double tap on the tab can only start one */
    const j = { cuts: [], cards: [], lvls: [], phases: [], scenes: 0, from: null, to: null, rank0: null };
    out.journeys.push(j);
    tab.click();
    if(a.doubleTap){ tab.click(); try{ armRankUpProfileScene('profile'); }catch(e){} }
    let seenScene = null, lastLv = null;
    for(let i = 0; i < 3000; i++){
      const s = rankUpScene;
      if(s && s !== seenScene){ seenScene = s; j.scenes++; j.from = s.from; j.to = s.to; j.more = !!s.more; }
      if(s && j.phases[j.phases.length - 1] !== s.phase) j.phases.push(s.phase);
      if(s && s.phase === 'profile' && !j.rank0){ j.rank0 = (document.querySelector('.pf-standing .pf-rankname') || {}).textContent;
        j.level0 = (document.querySelector('.pf-standing .pf-level') || {}).textContent; }
      const sp = document.querySelector('.rs-spot.is-up');
      if(sp && !sp.dataset.t){ sp.dataset.t = 1; j.cards.push({ name: (sp.querySelector('.rs-spot-name') || {}).textContent, foot: (sp.querySelector('.rs-spot-foot') || {}).textContent });
        setTimeout(() => sp.click(), a.cardMs || 500); }
      const up = document.querySelector('.rankmap-stop.ru-nextpop');
      if(up && !j.upnext) j.upnext = (up.querySelector('.rankmap-name') || {}).textContent;
      const lv = document.querySelector('.screen-profile .pf-standing .pf-level');
      if(s && (s.phase === 'return' || s.phase === 'home') && lv && lv.textContent !== lastLv){ lastLv = lv.textContent; j.lvls.push(lastLv); }
      if(s && (s.phase === 'return' || s.phase === 'home') && lv){ j.rankEnd = (document.querySelector('.screen-profile .pf-standing .pf-rankname') || {}).textContent; j.levelEnd = lv.textContent; }
      if(s && s.climb && !j.climb) j.climb = s.climb;
      if(seenScene && !s){ break; }
      await wait(40);
    }
    j.onHomeAfter = !!document.querySelector('[data-screen="home"]');
    j.screenAfter = (stage.firstElementChild || {}).className || null;
    j.onProfileAfter = !!document.querySelector('.screen-profile');
    j.shownAfter = store.rankUpShown;
    j.blocker = !!document.querySelector('.ru-blocker');
    j.points = Number(store.lifetime.points);
    if(j.onProfileAfter && !rankUpOwed()){ break; }
  }
  out.final = { shown: store.rankUpShown, held: TIER_ORDER_FULL.indexOf(rankOf(store)) + 1, owed: rankUpOwed(), points: Number(store.lifetime.points), total0,
    level: levelOf(store), rec: store.rankUpFrom, prog: localStorage.getItem('class26e.rankup.prog') };
  window.playTierCutscene = realTier; window.playSupernovaCutscene = realSn;
  if(!a.reloadAt && a.reloadAt !== 0){
    showHome(); await wait(2600);
    out.homeEnd = { lock: document.body.classList.contains('rankup-lock'), lit: {} };
    TIER_ORDER_FULL.forEach(k => out.homeEnd.lit[k] = flare(k));
    showProfile(); await wait(1200);
    out.again = !!rankUpScene;
  }
  }catch(e){ out.threw = String(e && e.stack || e); }
  return out; }"""

THREE_SEED = """() => {
  /* Bronze shown and held; one badge before; then seven badges and Platinum's
     level - Silver, Gold and Platinum crossed at once */
  const U = topicsIn(QUESTIONS);
  store.unitPerfects = {}; U.slice(0, 7).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
  store.rankFloor = 0; store.levelFloor = 0; store.levelWallRule = 325;
  const p0 = xpForLevel(21) + 4000;
  store.lifetime.points = xpForLevel(55) + 900;
  store.rankMapFx244 = true; store.rankMapSeen = 0; store.rankMapProg = { i: 0, p: .3 };
  store.rankUpShown = 1; store.rankUpFrom = { r: 0, b: 1, p: p0, d: .2 };
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour'].forEach(k => store[k] = true);
  store.lateHundos = 999; store.retroBadgePending = []; store.mergeHold = null; store.savedCodeSaved = true; store.pendingTierCutscene = null;
  theme.muteBanners = false; theme.reduceMotion = false; applyTheme && applyTheme();
  try{ seedBannerCounters(); seedChallenges289(); }catch(e){}
  const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx);
  store.pendingBadgeUnlocks = []; saveStore();
  try{ localStorage.removeItem('class26e.rankup.prog'); }catch(e){}
  showHome();
  return { owed: rankUpOwed(), level: levelOf(store), held: rankOf(store) };
}"""


def section_queue(br):
    print("\nB. a rank-up for every rank crossed, one after another, Home between them")
    NAME = lambda k: {"rookie": "Bronze", "ranger": "Silver", "veteran": "Gold", "vanguard": "Platinum", "adept": "Sapphire"}.get(k, k)
    for (label, w, h) in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate(cb.B319_RU_SEED, {"two": True})
        r = pg.evaluate(cb.B319_RU_RUN, {})
        check("%s: the run owes Gold and Platinum (Silver shown) and plays nothing on the results" % label,
              not r.get("threw") and r.get("owed") == {"fromIdx": 1, "toIdx": 3} and r.get("cut") == 0, [r.get("threw"), r.get("owed"), r.get("cut")])
        wk = pg.evaluate(QUEUE_WALK, {"cutMs": 300, "cardMs": 450})
        js, hs = wk.get("journeys") or [], wk.get("homes") or []
        check("%s: nothing threw" % label, not wk.get("threw"), wk.get("threw"))
        check("%s: TWO journeys, each one cutscene in order - Silver to Gold, then Gold to Platinum" % label,
              [[(c["key"], c["from"]) for c in j["cuts"]] for j in js] == [[("veteran", "ranger")], [("vanguard", "veteran")]]
              and [j["scenes"] for j in js] == [1, 1], [[j["cuts"] for j in js], [j["scenes"] for j in js]])
        check("%s: each journey hands over its own rank's card, one each ('Gold rank', then 'Platinum rank')" % label,
              [[c["name"] for c in j["cards"]] for j in js] == [["Gold rank"], ["Platinum rank"]], [[j["cards"] for j in js]])
        h1 = hs[1] if len(hs) > 1 else {}
        check("%s: after the first, back on Home: locked again, the Profile tab calling again (its gesture), Platinum still owed" % label,
              len(js) >= 1 and js[0].get("onHomeAfter") and h1.get("lock") and h1.get("call") and h1.get("sawNudge") and h1.get("nudges", 0) >= 1
              and h1.get("owed") == {"fromIdx": 2, "toIdx": 3} and not js[0].get("blocker"),
              [js[0].get("onHomeAfter") if js else None, h1])
        check("%s: on that Home, Gold's flare is lit and Platinum's is still dark" % label,
              (h1.get("lit") or {}).get("veteran") is True and (h1.get("lit") or {}).get("vanguard") is False, h1.get("lit"))
        check("%s: the first journey's Profile is Gold at Platinum's level (50), not past it; the second's starts there and climbs on" % label,
              len(js) == 2 and js[0].get("rankEnd") == "Gold" and js[0].get("levelEnd") == "Level 50"
              and js[1].get("rank0") == "Gold" and js[1].get("level0") == "Level 50" and js[1].get("rankEnd") == "Platinum"
              and js[1].get("levelEnd") == "Level %d" % (wk.get("final") or {}).get("level", -1),
              [(j.get("rank0"), j.get("level0"), j.get("rankEnd"), j.get("levelEnd"), j.get("lvls")) for j in js] + [(wk.get("final") or {}).get("level")])
        check("%s: each journey's road map pops the next rank as Up next (Platinum, then Sapphire)" % label,
              [j.get("upnext") for j in js] == ["Platinum", "Sapphire"], [j.get("upnext") for j in js])
        f = wk.get("final") or {}
        check("%s: done: both shown, nothing owed, no record left, XP unchanged by any of it" % label,
              f.get("shown") == f.get("held") == 4 and f.get("owed") is None and f.get("rec") is None and f.get("prog") is None
              and f.get("points") == f.get("total0") and all(j.get("points") == f.get("total0") for j in js), f)
        he = wk.get("homeEnd") or {}
        check("%s: Home free with both flares lit, and nothing plays again" % label,
              he.get("lock") is False and (he.get("lit") or {}).get("veteran") and (he.get("lit") or {}).get("vanguard") and wk.get("again") is False,
              [he, wk.get("again")])
        ctx.close()

    # three ranks at once
    ctx, pg = boot(br, 440, 956)
    s0 = pg.evaluate(THREE_SEED)
    wk = pg.evaluate(QUEUE_WALK, {"cutMs": 250, "cardMs": 400, "max": 5, "doubleTap": True})
    js = wk.get("journeys") or []
    check("three ranks at once (Bronze shown, Platinum held: %s): three journeys - Silver, Gold, Platinum - in order, each from the one before" % s0.get("owed"),
          not wk.get("threw") and [[(c["key"], c["from"]) for c in j["cuts"]] for j in js] == [[("ranger", "rookie")], [("veteran", "ranger")], [("vanguard", "veteran")]],
          [wk.get("threw"), [[(c["key"], c["from"]) for c in j["cuts"]] for j in js]])
    check("three ranks, the tab tapped twice each time (and the scene asked for again): one journey each, never two at once",
          [j.get("scenes") for j in js] == [1, 1, 1], [j.get("scenes") for j in js])
    check("three ranks: one card each, Home and the tab's call between each, ends on the real level with nothing owed",
          [[c["name"] for c in j["cards"]] for j in js] == [["Silver rank"], ["Gold rank"], ["Platinum rank"]]
          and all(h.get("sawNudge") and h.get("lock") for h in (wk.get("homes") or [])[:3])
          and [j.get("levelEnd") for j in js] == ["Level 40", "Level 50", "Level %d" % s0.get("level")] and (wk.get("final") or {}).get("owed") is None,
          [[[c["name"] for c in j["cards"]] for j in js], [j.get("levelEnd") for j in js], [(h.get("sawNudge"), h.get("lock"), h.get("onHome"), h.get("screen")) for h in (wk.get("homes") or [])],
           [(j.get("phases"), j.get("onHomeAfter"), j.get("screenAfter")) for j in js]])
    ctx.close()

    # a reload between the two: only the second plays, from Gold
    once = ("try{ if(!localStorage.getItem('__seeded326')){ localStorage.setItem('__seeded326','1');"
            "localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
            "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
            "localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.drill.v1', '%s'); } }catch(e){}" % cb.USED_ACCOUNT)
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, is_mobile=True)
    ctx.add_init_script(STANDALONE + once)
    pg = cb.open_page(ctx)
    pg.goto(cb.URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.evaluate(cb.B319_RU_SEED, {"two": True})
    pg.evaluate(cb.B319_RU_RUN, {})
    w1 = pg.evaluate(QUEUE_WALK, {"cutMs": 250, "cardMs": 400, "reloadAt": 1})
    mid = pg.evaluate("() => ({ shown: store.rankUpShown, owed: rankUpOwed(), rec: store.rankUpFrom })")
    pg.reload(); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub(); showHome(); }")
    w2 = pg.evaluate(QUEUE_WALK, {"cutMs": 250, "cardMs": 400})
    check("a relaunch between the two: Gold shown and kept, Platinum still owed with where it starts recorded (q)",
          mid.get("shown") == 3 and mid.get("owed") == {"fromIdx": 2, "toIdx": 3} and (mid.get("rec") or {}).get("q") == 1 and (mid.get("rec") or {}).get("r") == 2, mid)
    check("...and after it, Home calls and only Platinum's journey plays (Gold's is not shown again)",
          not w2.get("threw") and [[(c["key"], c["from"]) for c in j["cuts"]] for j in (w2.get("journeys") or [])] == [[("vanguard", "veteran")]]
          and (w2.get("final") or {}).get("shown") == 4, [w2.get("threw"), [j.get("cuts") for j in (w2.get("journeys") or [])], w2.get("final")])
    ctx.close()

    # existing accounts, and an older record
    ctx, pg = boot(br, 440, 956)
    ex = pg.evaluate("""() => {
      const out = {};
      out.fixture = { shown: store.rankUpShown, owed: rankUpOwed() };
      applyLoadedData({ lifetime: { points: 90000 }, unitPerfects: {}, onboardingComplete: true, rankUpShown: 2, rankUpFrom: { r: 1, b: 3, p: 50000 } });
      retroHideBadges = null;
      out.old = store.rankUpFrom;
      applyLoadedData({ lifetime: { points: 90000 }, unitPerfects: {}, onboardingComplete: true, rankUpShown: 2, rankUpFrom: { r: 1, b: 3, p: 50000, q: 1 } });
      retroHideBadges = null;
      out.q = store.rankUpFrom;
      return out; }""")
    check("an existing account (never counted) owes nothing; an older record reads as before (no q); a new one keeps q",
          ex["fixture"]["owed"] is None and ex["old"] == {"r": 1, "b": 3, "p": 50000} and (ex["q"] or {}).get("q") == 1, ex)
    ctx.close()



# --------------------------------------------------------------------------
# C. the Supernova crack
SN_HOME = """async (acc) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  store.supernovaAchieved = true; store.rankUpShown = 7; saveStore();
  try{ localStorage.setItem('class26e.ringtier.seen', homeRingTier()); }catch(e){}
  if(acc !== undefined){ theme.accent = acc; applyTheme(); }
  showHome(); await wait(1600);
  document.querySelectorAll('.rs-spot,.daily-alert,#tour-overlay,.update-banner,.toast,#nova-intro').forEach(n => n.remove());
  const hero = document.querySelector('.panel.home .cosmic-hero-wrap');
  const out = { hero: !!hero };
  if(!hero) return out;
  const hr = hero.getBoundingClientRect(), u = hr.width / 360;
  const cx = hr.left + 180 * u, cy = hr.top + (150 + 12) * u * (360 / 360);
  out.u = u;
  const art = cosmicScarArt();
  const seams = [...hero.querySelectorAll('.cosmic-scar .csc-disc > svg.csc-seam')];
  out.seam = seams.length ? { paths: seams.reduce((n, x) => n + x.querySelectorAll('path').length, 0), blend: [...new Set(seams.map(x => getComputedStyle(x).mixBlendMode))].join(),
    layers: seams.flatMap(x => [...x.children].map(g => g.getAttribute('class'))).sort(),
    /* what moves on it is whole svgs' opacity - never a group inside one (a repaint of every path a frame) */
    moving: seams.flatMap(x => x.getAnimations({ subtree: true }).map(a => (a.effect.target === x ? 'svg' : 'inner') + ':' + (a.animationName || ''))) } : null;
  const motes = hero.querySelector(':scope > .csc-motes');
  out.motes = motes ? motes.children.length : 0;
  out.motesAfterScar = !!(motes && motes.previousElementSibling && motes.previousElementSibling.classList.contains('cosmic-scar'));
  out.props = [];
  /* every mote at three points of its own loop, the page's own animations seeked */
  const crack = ((art && art.fronts) || []).filter(f => f.main).flatMap(f => f.pts.map(q => [cx + 52 * u * q[0], cy + 52 * u * q[1]]));
  const ringR = [...hero.querySelectorAll('.cosmic-orbit-ring')].map(r => Number(r.getAttribute('r'))).filter(r => r > 60);
  out.rings = ringR;
  out.paths = [];
  if(motes){
    [...motes.children].forEach(m => {
      const els = [m, m.firstElementChild, m.firstElementChild.firstElementChild];
      const ans = els.flatMap(e => e.getAnimations());
      ans.forEach(a => { try{ (a.effect.getKeyframes() || []).forEach(k => Object.keys(k).forEach(p => { if(!/^(offset|easing|composite|computedOffset)$/.test(p) && out.props.indexOf(p) < 0) out.props.push(p); })); }catch(e){} });
      if(ans.length < 3){ out.paths.push(null); return; }
      const T = ans[0].effect.getComputedTiming().duration;
      const at = f => { ans.forEach(a => { a.pause(); const d = a.effect.getComputedTiming().delay; let ct = d + f * T; while(ct < Math.max(0, d)) ct += T; a.currentTime = ct; });
        const r = els[2].getBoundingClientRect(); const x = r.left + r.width / 2, y = r.top + r.height / 2;
        return { d: Math.hypot(x - cx, y - cy) / u, a: (Math.atan2(x - cx, -(y - cy)) * 180 / Math.PI + 360) % 360, o: +getComputedStyle(els[2]).opacity, x, y }; };
      const p0 = at(.001), p62 = at(.62), p95 = at(.95), pend = at(.999);
      const near = crack.length ? Math.min(...crack.map(c => Math.hypot(c[0] - p0.x, c[1] - p0.y))) / u : 99;
      ans.forEach(a => a.play());
      out.paths.push({ start: Math.round(p0.d), near: Math.round(near * 10) / 10, mid: Math.round(p62.d), end: Math.round(p95.d),
        turn: Math.round(((p95.a - p62.a) + 540) % 360 - 180), o0: p0.o, o95: pend.o });
    });
  }
  return out; }"""


def section_crack(br):
    print("\nC. Supernova's crack: a large lit crack, his light drawn out of it into the rings' turn; the cutscene's fracture")
    import json as _json
    acct = _json.loads(cb.USED_ACCOUNT); acct["supernovaAchieved"] = True
    seed_sn = _json.dumps(acct)
    for (label, w, h) in (PHONE, TABLET):
        ctx, pg = boot(br, w, h, seed=seed_sn)
        for acc in (None, "adept", "elite", "ranger"):
            r = pg.evaluate(SN_HOME, acc) if acc else pg.evaluate(SN_HOME)
            tag = "%s, %s theme" % (label, acc or "default")
            if acc is None:
                sm = r.get("seam") or {}
                check("%s: the crack carries its light - a seam of %d+ paths (spill, halo, glow, core) in the scar's disc, screen-blended" % (label, 40),
                      sm.get("paths", 0) >= 40 and sm.get("blend") == "screen" and sm.get("layers") == sorted(["csc-sm-spill", "csc-sm-halo", "csc-sm-glow", "csc-sm-core"]), sm)
                check("%s: the seam breathes as a whole svg (the compositor fades it) - nothing inside one animates on Home" % label,
                      sm.get("moving") and all(m.startswith("svg:") for m in sm.get("moving")), sm.get("moving"))
                ps = [p for p in r.get("paths") or [] if p]
                check("%s: %d motes leave the crack, painted over the planet (after the scar)" % (label, len(ps)),
                      r.get("motes", 0) >= 14 and len(ps) == r.get("motes") and r.get("motesAfterScar"), [r.get("motes"), len(ps), r.get("motesAfterScar")])
                rings = r.get("rings") or [108, 140]
                bad = [p for p in ps if not (p["start"] <= 54 and p["near"] <= 3)]
                check("%s: each starts ON the crack (inside the planet, within 3 units of a point of the crack)" % label, ps and not bad, bad[:4])
                bad = [p for p in ps if not any(abs(p["end"] - R) <= 9 for R in rings) or not any(abs(p["mid"] - R) <= 9 for R in rings)]
                check("%s: ...and is drawn out onto a ring (%s) by the time it is two thirds through" % (label, rings), ps and not bad, bad[:4])
                bad = [p for p in ps if p["turn"] < 15]
                check("%s: ...then runs along it clockwise - the rings' way - faster than the ring turns (15+ degrees in a third of its loop)" % label, ps and not bad, bad[:4])
                bad = [p for p in ps if p["o0"] > .05 or p["o95"] > .05]
                check("%s: ...invisible at both ends of its loop (no pop, no seam)" % label, ps and not bad, bad[:4])
                check("%s: transform and opacity only" % label, set(r.get("props") or []) <= {"transform", "opacity", "rotate", "translate", "scale"} and r.get("props"), r.get("props"))
            # the light reads on every theme: sample the seam's core along the arms
            px = pg.evaluate("""() => { const hero = document.querySelector('.panel.home .cosmic-hero-wrap'); const r = hero.getBoundingClientRect(), u = r.width / 360;
              const art = cosmicScarArt(); const pts = art.fronts.filter(f => f.main && f.kind === 0).flatMap(f => f.pts.filter((q, i) => i % 6 === 3 && q[2] < art.arMax * .7));
              return { pts: pts.map(q => [r.left + 180 * u + 52 * u * q[0], r.top + 162 * u + 52 * u * q[1]]) }; }""")
            shot = pg.screenshot()
            from PIL import Image
            import io as _io
            im = Image.open(_io.BytesIO(shot)).convert("RGB")
            sc = im.width / w
            lum = []
            for (x, y) in px["pts"]:
                best = 0
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        rr, gg, bb = im.getpixel((int(x * sc) + dx, int(y * sc) + dy))
                        best = max(best, .2126 * rr + .7152 * gg + .0722 * bb)
                lum.append(round(best))
            good = sum(1 for v in lum if v >= 175)
            check("%s: the seam is light you can see - bright (175+) on %d of %d points down the arms" % (tag, good, len(lum)),
                  lum and good >= .75 * len(lum), lum)
        # Reduce motion: no motes, nothing moving on the seam
        rm = pg.evaluate("""async () => { theme.reduceMotion = true; applyTheme(); showHome(); await new Promise(r => setTimeout(r, 900));
          const hero = document.querySelector('.panel.home .cosmic-hero-wrap'); const m = hero.querySelector(':scope > .csc-motes');
          const seam = hero.querySelector('.csc-disc');
          const run = el => el ? el.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length : -1;
          const out = { motes: m ? getComputedStyle(m).display : 'absent', seamRunning: run(seam), seam: !!seam };
          theme.reduceMotion = false; applyTheme(); return out; }""")
        check("%s: Reduce motion: the crack and its light stay, the motes are not shown, nothing on the seam moves" % label,
              rm.get("seam") and rm.get("motes") == "none" and rm.get("seamRunning") == 0, rm)
        ctx.close()

    # the cutscene, on the fake clock (check-behaviour's _Stepper320: every timer
    # and animation stepped together - load cannot move a frame): the fracture
    # through the swell, the light drawn on with the crack, the motes leaving as
    # it reaches them, and Home's planet after
    ctx, pg = boot(br, 440, 956)
    pg.evaluate("async () => { store.supernovaAchieved = false; saveStore(); showHome(); }")
    pg.wait_for_timeout(1500)
    cdp = ctx.new_cdp_session(pg); cdp.send("Animation.enable"); cdp.send("Animation.setPlaybackRate", {"playbackRate": 0})
    st = cb._Stepper320(pg)
    st.step(1 / 30)
    pg.evaluate("() => { window.__snEnded = false; store.pendingSupernovaCutscene = true; playSupernovaCutscene({ from: 'elite', onDone(){ window.__snEnded = true; } }); }")
    CLS = "() => { const o = document.getElementById('supernova-cutscene'); return o ? o.className : null; }"
    def until(pred, limit):
        while st.t < limit:
            st.step(1 / 15)
            if pg.evaluate(pred):
                return st.t
        return None
    t_sw = until("() => { const o = document.getElementById('supernova-cutscene'); return !!(o && o.classList.contains('sn-swell')); }", 60)
    DASH = """(sel) => { const o = document.getElementById('supernova-cutscene'); const svg = o && o.querySelector(sel); if(!svg) return null;
      const ps = [...svg.querySelectorAll('.csc-sm-core path')], offs = ps.map(p => parseFloat(getComputedStyle(p).strokeDashoffset));
      const hot = svg.querySelector('.csc-sm-hot');
      return { paths: ps.length, drawn: offs.filter(v => v < .02).length, partial: offs.filter(v => v >= .02 && v < .98).length, undrawn: offs.filter(v => v >= .98).length,
               hot: hot ? +getComputedStyle(hot).opacity : null, cls: svg.getAttribute('class') }; }"""
    fr = None
    if t_sw is not None:
        for _ in range(int(1.05 / (1 / 15))):
            st.step(1 / 15)
        fr = pg.evaluate(DASH, ".sn-fx svg.sn-fracture")
    t_det = until("() => { const o = document.getElementById('supernova-cutscene'); return !!(o && o.classList.contains('sn-detonate')); }", 70)
    t_sc = until("() => { const o = document.getElementById('supernova-cutscene'); return !!(o && o.classList.contains('sn-scarred')); }", 75)
    sm = mo = None
    if t_sc is not None:
        for _ in range(int(1.0 / (1 / 15))):
            st.step(1 / 15)
        sm = pg.evaluate(DASH, ".rank-after svg.csc-seam")
        mo = pg.evaluate("""() => { const o = document.getElementById('supernova-cutscene'); const m = o && o.querySelector('.rank-after .csc-motes');
          const us = m ? [...m.querySelectorAll('u')].map(u => +getComputedStyle(u).opacity) : [];
          return { shown: m ? getComputedStyle(m).display : null, fresh: !!(m && m.classList.contains('is-fresh')), visible: us.filter(v => v > .05).length, n: us.length }; }""")
    t_end = until("() => window.__snEnded === true || !document.getElementById('supernova-cutscene')", 110)
    # (inline - the rank-up journey's way - the scene hands back to the journey, not to Home: Home is next built fresh)
    pg.evaluate("() => { document.querySelectorAll('.rs-spot').forEach(n => n.remove()); showHome(); }")
    for _ in range(30):
        st.step(1 / 15)
    home = pg.evaluate("""() => { const h = document.querySelector('.panel.home .cosmic-hero-wrap'); return h ? { seam: !!h.querySelector('svg.csc-seam'),
      motes: h.querySelectorAll(':scope > .csc-motes > i').length, forming: !!h.querySelector('.is-forming'), sn: !!store.supernovaAchieved } : null; }""")
    fr, sm, mo = fr or {}, sm or {}, mo or {}
    times = {"swell": t_sw, "detonate": t_det, "scarred": t_sc, "end": t_end}
    check("the swell: the planet fractures - a second in, the crack's light is part-drawn across it from the impact (%s drawn, %s running, %s still to come), white-hot, before it goes" % (fr.get("drawn"), fr.get("partial"), fr.get("undrawn")),
          fr.get("paths", 0) >= 20 and fr.get("drawn", 0) > 0 and (fr.get("partial", 0) + fr.get("undrawn", 0)) > 0 and (fr.get("hot") or 0) > .5
          and t_sw is not None and t_det is not None and t_sw < t_det, [fr, times])
    check("after the blast the crack's light is drawn on with the crack, white-hot as it runs (some drawn, some still to come)",
          sm.get("paths", 0) >= 20 and sm.get("drawn", 0) > 0 and (sm.get("partial", 0) + sm.get("undrawn", 0)) > 0 and (sm.get("hot") or 0) > .3, [sm, times])
    check("...and the motes start leaving the crack as it reaches them (shown, fresh, some out, not all yet)",
          mo.get("shown") == "block" and mo.get("fresh") and 0 < mo.get("visible", 0) < mo.get("n", 0), mo)
    check("the scene ends on Home's Supernova planet: the seam settled (not forming) and the motes looping",
          t_end is not None and (home or {}).get("seam") and (home or {}).get("motes", 0) >= 14 and not (home or {}).get("forming"), [times, home])
    ctx.close()


# --------------------------------------------------------------------------
SECTIONS = {"A": section_spend, "B": section_queue, "C": section_crack}


def main():
    only = os.environ.get("B326C_ONLY")
    keys = [k.strip() for k in only.split(",")] if only else list(SECTIONS)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME)
        for k in keys:
            try:
                SECTIONS[k](br)
            except Exception as e:
                check("section %s ran" % k, False, repr(e)[:600])
        br.close()
    print("\n%s" % ("ALL PASS" if not FAILURES else "%d FAILED: %s" % (len(FAILURES), FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
