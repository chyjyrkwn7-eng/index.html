#!/usr/bin/env python3
"""The badge thresholds, the level curve, and the ranks they gate.

Three things that are only correct together. A threshold band, the XP a
level costs and a rank's requirement are all separately plausible
numbers; what makes them right is the relationship between them, and
nothing else in this repo can see that relationship. A sweep asks "is
anything broken on this device", check-behaviour asks "does the app do
the right thing" - neither can tell you that the top rank asks for 20
badges in an app with 16 units, which is what build 189 shipped.

Every check here was written against build 189 and fails there:

    python3 tools/check-curve.py --against /path/to/189/index.html

The two that matter most are the two that cannot be argued with:

  NOBODY'S LEVEL DROPS. Evaluated for every XP total from 0 to 600,000,
  the new curve must never return a lower level than the old one. That
  is the whole of "do not change anyone's current level", and it is
  checkable without touching a single live account.

  THE TOP RANK IS REACHABLE. Its badge count must be one the question
  bank can actually produce, and the level it asks for must be one the
  badge line actually reaches.

Device-independent - none of this is layout - so it runs once.
Exits non-zero on any failure.
"""
import argparse
import functools
import http.server
import io
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("--against", help="run the same checks against another index.html")
A = ap.parse_args()
SERVE = ROOT
if A.against:
    other = A.against if os.path.isabs(A.against) else os.path.join(ROOT, A.against)
    SERVE = tempfile.mkdtemp(prefix="curve-")
    shutil.copy(other, os.path.join(SERVE, "index.html"))
    if os.path.exists(os.path.join(ROOT, "version.json")):
        shutil.copy(os.path.join(ROOT, "version.json"), SERVE)
    print("against: %s" % other)

_s = socket.socket(); _s.bind(("127.0.0.1", 0))
PORT = _s.getsockname()[1]; _s.close()


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


SERVER = http.server.ThreadingHTTPServer(
    ("127.0.0.1", PORT), functools.partial(_Quiet, directory=SERVE))
threading.Thread(target=SERVER.serve_forever, daemon=True).start()

FAILURES = []


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -> " + str(detail)) if detail else ""))
    if not ok:
        FAILURES.append(name)


# The curve the class is standing on (builds 206-209: a 2.0 step into
# 26, then +1.99% a level), so "no level drops" is measured against what
# people actually hold rather than an assumption. It was build 189's
# 3.1102 / 1.0354 until build 210 steepened the curve past 45.
OLD_STEP, OLD_LATE = 2.0, 1.0199
# Build 210: the highest level anyone held when the steep curve shipped
# was 43, so no level at or below this one may move.
UNCHANGED_THROUGH = 45
OLD_BADGE_THRESHOLD = 35


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        ctx = br.new_context(viewport={"width": 834, "height": 1194})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/index.html" % PORT)
        pg.wait_for_timeout(2600)
        pg.evaluate("()=>{document.getElementById('splashscreen')?.remove();}")

        print("\n1. a badge costs what its unit is worth")
        r = pg.evaluate("""()=>{
          const out = {};
          try {
            topicsIn(QUESTIONS).forEach(u => {
              out[u] = { q: unitQuestionCount(u), need: badgeThresholdFor(u) };
            });
          } catch(e){ return { threw: String(e) }; }
          return { units: out,
                   unknown: (typeof badgeThresholdFor === 'function')
                     ? badgeThresholdFor('a unit from another build') : null };}""")
        if r.get("threw"):
            check("badgeThresholdFor exists", False, r["threw"])
            units = {}
        else:
            units = r["units"]
            check("badgeThresholdFor exists", True)
            check("an unknown unit falls back to 35, never to 5",
                  r["unknown"] == 35, r["unknown"])
        # The LIVE bands, as build 279 set them and build 313 shipped them.
        # Build 314 proposed 3/2/1 and it was rejected outright: "DONT
        # change the badge requirement" - so these are asserted as the
        # numbers on dd6cfae, not as a decision this build may revisit.
        bands = [(0, 25, 15), (26, 50, 12), (51, 100, 8), (101, 200, 4), (201, 10 ** 6, 2)]
        wrong = []
        for u, v in units.items():
            want = next(h for lo, hi, h in bands if lo <= v["q"] <= hi)
            if v["need"] != want:
                wrong.append((u, v["q"], v["need"], want))
        check("every unit sits in the band its size puts it in", not wrong, wrong)
        check("sixteen units", len(units) == 16, len(units))
        """Lowering a threshold can only ADD a badge; raising one takes a
        badge off somebody who holds it, because a badge is computed
        fresh from the hundo count rather than stored. So no band may be
        above the flat 35 the live build charges."""
        above = [(u, v["need"]) for u, v in units.items() if v["need"] > OLD_BADGE_THRESHOLD]
        check("no band asks for more than the 35 the live build charged",
              not above, above)
        # AND NO UNIT GOT DEARER THAN BUILD 279 CHARGED IT - lowering can
        # only add a badge; raising one takes it off whoever holds it.
        old_bands = [(0, 25, 15), (26, 50, 12), (51, 100, 8),
                     (101, 200, 4), (201, 10 ** 6, 2)]
        raised = [(u, v["q"], v["need"], next(h for lo, hi, h in old_bands if lo <= v["q"] <= hi))
                  for u, v in units.items()
                  if v["need"] > next(h for lo, hi, h in old_bands if lo <= v["q"] <= hi)]
        check("no unit needs more hundos than it did on build 279", not raised, raised)
        lowered = [(u, v["q"], v["need"]) for u, v in units.items()
                   if v["need"] < next(h for lo, hi, h in old_bands if lo <= v["q"] <= hi)]
        check("...nor fewer: the badge requirement did not change", not lowered, lowered)
        live = pg.evaluate("""()=>({ bands: JSON.parse(JSON.stringify(BADGE_THRESHOLD_BANDS, (k, v) => v === Infinity ? 'inf' : v)),
          ver: BADGE_BANDS_VERSION })""")
        check("BADGE_THRESHOLD_BANDS is byte-for-byte the live table (dd6cfae)",
              live["bands"] == [{"max": 25, "hundos": 15}, {"max": 50, "hundos": 12}, {"max": 100, "hundos": 8},
                                {"max": 200, "hundos": 4}, {"max": "inf", "hundos": 2}], live["bands"])
        check("no new badge hand-out: BADGE_BANDS_VERSION is still 3", live["ver"] == 3, live["ver"])
        # the per-unit numbers dd6cfae computes, so no unit's badge costs
        # a hundo more or less than live
        LIVE_313 = {"Professionalism and Ethics": 12, "Professional Policing": 15,
                    "Fitness, Wellness, and Stress Management": 12, "TCOLE Rules": 15,
                    "Multiculturalism and Human Relations": 12, "Racial Profiling": 15,
                    "US and Texas Constitution and Rights": 8, "Penal Code": 2,
                    "Code of Criminal Procedure and Bill of Rights": 12, "Arrest, Search, and Seizure": 4,
                    "Victims of Crime": 15, "Missing and Exploited Children": 8, "Identity Crimes": 15,
                    "Sexual Assault and Family Violence": 12, "Verbal Communication": 12,
                    "Civil Process and Liability": 15}
        diff = {u: (v["need"], LIVE_313.get(u)) for u, v in units.items() if v["need"] != LIVE_313.get(u)}
        check("every unit's badge costs exactly what it does on dd6cfae", not diff and len(units) == 16, diff)
        rng = pg.evaluate("()=> typeof badgeRangeText === 'function' ? badgeRangeText() : null")
        check("the copy states the range the bands actually ask", rng == "2 to 15 hundos", rng)

        print("\n2. nobody's level drops, for any XP total")
        drop = pg.evaluate("""()=>{
          /* BUILD 313'S CURVE rebuilt here from its own constants (x2.0
             into 26, +1.99% to 45, +8.35% past it), stepping exactly the
             way levelProgress() does - not the page's legacyLevelOfPoints,
             so this compares the curve with the record rather than with
             itself. Build 314 makes every level CHEAPER, so every XP
             total must read the same level or higher. */
          function oldLevel(p){
            let lvl = 1, need = 300, spent = 0;
            const growth = l => l <= 25 ? 1.05 : l === 26 ? 2.0 : l > 45 ? 1.0835 : 1.0199;
            const ceil = l => l <= 25 ? 9000 : 150000;
            while(lvl < 80 && p >= spent + need){
              spent += need; lvl += 1;
              need = Math.min(ceil(lvl + 1), Math.round(need * growth(lvl + 1)));
            }
            return lvl;
          }
          let worst = null, n = 0, frozenDiff = null, n313 = 0;
          for(let p = 0; p <= 600000; p += 37){
            const a = oldLevel(p), b = levelFromPoints(p);
            if(b < a){ n++; if(!worst) worst = { p, was: a, now: b }; }
            if(typeof legacyLevelOfPoints === 'function' && legacyLevelOfPoints(p) !== a) n313++;
          }
          for(let p = 0; p <= 14306; p += 1){
            if(oldLevel(p) !== levelFromPoints(p)){ frozenDiff = p; break; }
          }
          return { n, worst, frozenDiff, n313 };}""")
        check("no XP total from 0 to 600,000 reads a lower level than on build 313", drop["n"] == 0, drop["worst"])
        check("levels 1-25 are byte-identical (every XP total to 14,306)",
              drop["frozenDiff"] is None, drop["frozenDiff"])
        check("legacyLevelOfPoints is build 313's curve, step for step", drop["n313"] == 0, drop["n313"])

        print("\n3. the badge line, and the ranks read off it")
        line = pg.evaluate("""()=>{
          try{
            if(typeof badgeThresholdFor !== 'function') throw new Error('no badgeThresholdFor');
          /* The fastest honest route: earn the cheapest badges first,
             one flawless full-unit run per hundo. Every extra attempt
             earns MORE XP, so this is the LOWEST level a given badge
             count can arrive at - which is the one that matters when
             asking whether a rank is reachable. */
          const cost = topicsIn(QUESTIONS).map(u => {
            const need = badgeThresholdFor(u);
            return need * (unitQuestionCount(u) * POINTS_PER_QUESTION + PERFECT_BONUS)
                   + MASTERY_BONUS;
          }).sort((a, b) => a - b);
          const cum = []; let s = 0;
          cost.forEach(c => { s += c; cum.push(s); });
          return { cum, levels: cum.map(levelFromPoints),
                   tiers: TIER_ORDER_FULL.map(k => ({
                     key: k, level: TIER_UNLOCKS[k].level,
                     badges: TIER_UNLOCKS[k].badges,
                     label: TIER_UNLOCKS[k].label })),
                   units: topicsIn(QUESTIONS).length, cap: LEVEL_CAP };
          } catch(e){ return { threw: String(e) }; }}""")
        """A gate that THROWS on the build it was written against tells
        you less than one that fails on it - it stops before the checks
        that matter. Everything below degrades to a plain FAIL instead."""
        if line.get("threw"):
            for n in ("the badge line only ever climbs",
                      "no rank asks for more badges than there are units",
                      "every rank's level is inside the cap",
                      "the ranks are 21/30/40/50/60/70/80 with the live badge counts (1/3/5/7/9/12/14)",
                      "every rank's label says the numbers it actually checks"):
                check(n, False, line["threw"])
            line = None
        else:
            print("     badge line:", line["levels"])
            # BUILD 210 REVERSED "EVERY BADGE LANDS ON THE CAP". Levels past
            # 45 now cost more than the badges alone pay for - asked for
            # because people held high levels with few badges - so the
            # badge line tops out well below 80. What still has to hold is
            # the shape: more badges is never a lower level.
            check("the badge line only ever climbs",
                  all(b >= a for a, b in zip(line["levels"], line["levels"][1:])),
                  line["levels"])
            over = [t for t in line["tiers"] if t["badges"] > line["units"]]
            check("no rank asks for more badges than there are units", not over, over)
            # "THE BADGE IS THE GATE" IS RETIRED (build 210). It asserted
            # that earning a rank's badges always already paid for its
            # level. Build 210 made badges cheaper and levels past 45
            # dearer - both asked for, to even out "high levels, few
            # badges" - so a rank now asks for both and neither brings the
            # other. Printed so the gap is visible whenever the curve, the
            # bands or the ranks move, rather than asserted one way.
            for t in line["tiers"]:
                if t["badges"] <= line["units"]:
                    print("     %-8s level %2d / %2d badges  -> badges alone reach level %2d"
                          % (t["key"], t["level"], t["badges"], line["levels"][t["badges"] - 1]))
            beyond = [t for t in line["tiers"] if t["level"] > line["cap"]]
            check("every rank's level is inside the cap", not beyond, beyond)
            # BUILD 314, FINAL (Madison): "Let's make supernova level 80? And
            # then fix the ones before it" - even steps to the cap, with the
            # badge counts exactly as live ("DONT change the badge
            # requirement"). Raising a rank's level could take it off
            # somebody, so section 3b checks every real account keeps the
            # rank it holds today.
            WANT = {"rookie": (21, 1), "ranger": (30, 3), "veteran": (40, 5),
                    "vanguard": (50, 7), "adept": (60, 9), "elite": (70, 12),
                    "titan": (80, 14)}
            got = {t["key"]: (t["level"], t["badges"]) for t in line["tiers"]}
            check("the ranks are 21/30/40/50/60/70/80 with the live badge counts (1/3/5/7/9/12/14)",
                  got == WANT, got)
            stale = [t["key"] for t in line["tiers"]
                     if str(t["level"]) not in t["label"] or str(t["badges"]) not in t["label"]]
            check("every rank's label says the numbers it actually checks", not stale, stale)

        print("\n4. what it costs to climb")
        costs = pg.evaluate("""()=>{
          const at = L => xpForLevel(L) - xpForLevel(L - 1);
          let minRatioPast45 = Infinity;
          for(let L = 47; L <= LEVEL_CAP; L++) minRatioPast45 = Math.min(minRatioPast45, at(L) / at(L - 1));
          /* the growth the curve would keep past the cap - levelGrowthAt
             is what levelProgress steps by, so LEVEL_CAP is only a bound */
          const rates = []; for(let L = 27; L <= 120; L++) rates.push(levelGrowthAt(L));
          return { l26: at(26), l50: at(50), l60: at(60), l61: at(61), l80: at(80),
                   toCap: xpForLevel(LEVEL_CAP), to71: xpForLevel(71), to21: xpForLevel(21), minRatioPast45, rates };}""")
        print("     ", json.dumps(costs))
        """"If you are level 60 I don't want you to have to play for a
        week straight to earn 2 levels." Two levels at 60 against a
        typical 250-XP perfect drill is the number to keep an eye on;
        30 runs is a fortnight, 15 is a few evenings."""
        # "If you are level 60 I don't want you to have to play for a week
        # straight to earn 2 levels" - re-measured in DAYS at the pace the
        # class actually earns, not in 250-XP drills. The steep curve of
        # build 210 made two levels at 60 about 76 small drills, which
        # reads alarming and is about three and a half days for somebody
        # earning 6,000 XP a day (the middle of the top five at launch).
        two60 = costs["l60"] + costs["l61"]
        check("two levels at 60 is under a week at 6,000 XP a day",
              two60 / 6000.0 < 7, "%.1f days" % (two60 / 6000.0))
        # AND THE STEEPENING ITSELF, which is the decision build 210 made,
        # settled by looking at the list: every level past 45 at least 6%
        # dearer than the one below it, and the whole climb to the cap
        # about 375,000 XP - "total xp needed could be about 375,000".
        # BUILD 213 raised both, because the run now pays for speed,
        # streaks, personal bests and a multi-unit multiplier as well:
        # "Let's make the total xp like 450 now?", then "if you need to
        # adjust levels past level 45 to be more and make the xp total
        # more than 450,000 then do it" once the new XP was made bigger.
        # Growth past 45 is 8.35%, about 600,000 in all.
        # BUILD 314, FINAL: the re-fitted curve was NOT shipped - "140000 xp
        # is all that's needed to reach level 80? That doesn't even sound
        # right". The live curve stays exactly as it is, so no level moves.
        same = pg.evaluate("""()=>{ let bad = 0; for(let p = 0; p <= 700000; p += 37){ if(levelFromPoints(p) !== legacyLevelOfPoints(p)) bad++; } return bad; }""")
        check("the XP curve is exactly the live one (every total from 0 to 700,000)", same == 0, same)
        check("level 80 still costs what it does live (598,449)", costs["toCap"] == 598449, costs["toCap"])
        check("level 21 still costs about 10,000 (early levels stay quick)", 8000 <= costs["to21"] <= 10500, costs["to21"])
        check("and a level still costs more the higher you are",
              costs["l80"] > costs["l60"] > costs["l50"] > costs["l26"], costs)

        print("\n5. no screen quotes a threshold that is no longer one number")
        quoted = pg.evaluate("""()=>{
          const tab = buildBadgesTab();
          const blurb = tab.querySelector('.badges-blurb');
          const progs = [...tab.querySelectorAll('.badge-tile-prog')].map(n => n.textContent);
          return { blurb: blurb ? blurb.textContent : null, progs };}""")
        check("the badge case's blurb does not name a single number",
              quoted["blurb"] and "35 hundos" not in quoted["blurb"], quoted["blurb"])
        """Sixteen tiles on a fresh account should print sixteen
        denominators, and they should not all be the same one."""
        denom = set(t.split("/")[-1] for t in quoted["progs"] if "/" in t)
        check("the tiles print more than one denominator", len(denom) > 1, sorted(denom))

        print("\n6. the end-of-test rows say what a run could actually do")
        rows = pg.evaluate("""()=>{
          try{
            const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
            const big = topics.reduce((a,b) => unitQuestionCount(b) > unitQuestionCount(a) ? b : a);
            const small = topics.reduce((a,b) => unitQuestionCount(b) < unitQuestionCount(a) ? b : a);
            /* THE WHOLE UNIT AS THE APP COUNTS IT (build 308): inWholeUnit.
               The Penal Code carries a question that exists only in its
               slides 0-85 version, so "every question tagged Penal Code" is
               341 where the unit is 340 - and a run of 341 is not a full
               unit, so its row never appeared and this failed on every
               build since 298. */
            const idx = t => QUESTIONS.map((q,i)=>[q,i])
              .filter(([q]) => (q.topic||'').trim() === t && inWholeUnit(q)).map(([,i]) => i);
            const run = (units, slice) => {
              store.unitPerfects = {}; store.pendingBadgeUnlocks = [];
              cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = units.slice();
              order = [].concat(...units.map(u => slice ? idx(u).slice(0, 10) : idx(u)));
              runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
              attempts = {}; picked = {}; timedOutSet = {};
              order.forEach(qi => { attempts[qi] = 1;
                picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
              summarize();
              return [...document.querySelectorAll('.badgeprogress-row')]
                .map(r => (r.querySelector('.badgeprogress-line')||{}).textContent);
            };
            /* A whole unit sat, with one question missed: no hundo, so
               since build 211 no row either. */
            const missed = (() => {
              store.unitPerfects = {}; store.pendingBadgeUnlocks = [];
              cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [small];
              order = idx(small);
              runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
              attempts = {}; picked = {}; timedOutSet = {};
              order.forEach((qi, k) => { attempts[qi] = k === 0 ? 2 : 1;
                picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
              summarize();
              return [...document.querySelectorAll('.badgeprogress-row')].length;
            })();
            return { slice: run([big], true), full: run([small], false),
                     two: run([small, big], false), missed, big, small };
          } catch(e){ return { threw: String(e) }; }}""")
        if rows.get("threw"):
            check("the results screen carries a row per unit", False, rows["threw"])
        else:
            """A three-unit run reporting on one unit was the whole
            complaint. The count is the check; the wording is not."""
            check("a two-unit run reports on both", len(rows["two"]) == 2, rows["two"])
            check("a full-unit run counts towards the badge",
                  len(rows["full"]) == 1 and "to go" in (rows["full"][0] or ""), rows["full"])
            """A 10-question slice of a 340-question unit can never earn
            a hundo, so a row quoting "5 to go" after one is telling
            somebody to keep doing a thing that does not work. Caught on
            a screenshot - every number on the screen was correct."""
            # BUILD 211: rows only where this run earned a hundo - "the
            # badge rows will only be for the badge progress for the hits
            # you took from that test". A slice and a run with a miss both
            # show none; the start sheet says beforehand that a slice
            # cannot earn one.
            check("a partial run shows no badge row", len(rows["slice"]) == 0, rows["slice"])
            check("a whole unit with a miss shows no badge row", rows["missed"] == 0, rows["missed"])

        print("\n7. badges the new bands handed out celebrate on the next test")
        retro = pg.evaluate("""()=>{
          try{
            if(typeof grantRetroBadgesOnce !== 'function') throw new Error('no grantRetroBadgesOnce');
            const idx = t => QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
            const finish = (unit, n) => {
              cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit];
              order = idx(unit).slice(0, n);
              runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
              attempts = {}; picked = {}; timedOutSet = {};
              order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
              summarize();
            };
            /* An account as it arrives from build 209: three units that only
               clear the new bands, and a level that already holds Bronze's. */
            store.unitPerfects = {'Identity Crimes': 25, 'Penal Code': 4, 'TCOLE Rules': 21};
            store.lifetime.points = xpForLevel(30) + 50;
            store.pendingBadgeUnlocks = []; store.pendingTierCutscene = null; store.pendingSupernovaCutscene = false;
            store.badgeBandsVersion = 0; store.retroBadgePending = [];
            grantRetroBadgesOnce();
            const listed = store.retroBadgePending.slice();
            const xp0 = store.lifetime.points;
            finish('Victims of Crime', 5);           // any test at all, even a slice
            /* Build 213: the celebration is on the RESULTS SCREEN now, as a
               badge row in its "Unlocked" card, not a queue for Home. */
            const shown = () => [...document.querySelectorAll('#stage .rs-unlock-badge .unlockbanner-name')]
              .map(e => e.textContent.replace(/ badge$/, ''));
            const first = { queued: shown(), tier: store.pendingTierCutscene,
                            left: store.retroBadgePending.slice(), xp: store.lifetime.points - xp0 };
            store.pendingBadgeUnlocks = []; store.pendingTierCutscene = null;
            grantRetroBadgesOnce();                   // a relaunch must not list them again
            finish('Victims of Crime', 5);
            const second = { queued: shown(), tier: store.pendingTierCutscene };
            /* A brand-new account is current at sign-up: nothing handed out. */
            store.badgeBandsVersion = 2; store.retroBadgePending = [];
            store.unitPerfects = {'Identity Crimes': 20};
            grantRetroBadgesOnce();
            const fresh = store.retroBadgePending.slice();
            /* BUILD 279: an account already on 210's bands - which is every
               live account - is owed what 279's lower bands hand it, and
               keeps anything 210 handed it that is still uncelebrated. */
            store.badgeBandsVersion = 2; store.retroBadgePending = ['Victims of Crime'];
            store.unitPerfects = {'TCOLE Rules': 16, 'Penal Code': 2, 'Professionalism and Ethics': 12, 'Identity Crimes': 20};
            grantRetroBadgesOnce();
            const b279 = store.retroBadgePending.slice();
            /* BUILD 314 HANDS NOTHING OUT: the bands did not move, so an
               account already on version 3 - every live account - is not
               re-listed, whatever its hundos. */
            store.badgeBandsVersion = 3; store.retroBadgePending = [];
            store.unitPerfects = {'Identity Crimes': 5, 'Penal Code': 2, 'US and Texas Constitution and Rights': 2, 'Victims of Crime': 15};
            grantRetroBadgesOnce();
            const b314 = store.retroBadgePending.slice();
            return { listed, first, second, fresh, b279, b314 };
          } catch(e){ return { threw: String(e) }; }}""")
        if retro.get("threw"):
            check("handed-out badges are listed once, on launch", False, retro["threw"])
        else:
            check("handed-out badges are listed once, on launch",
                  sorted(retro["listed"]) == ['Identity Crimes', 'Penal Code', 'TCOLE Rules'], retro["listed"])
            check("the next test celebrates each of them",
                  sorted(retro["first"]["queued"]) == sorted(retro["listed"]), retro["first"])
            check("and plays the rank-up they cause", retro["first"]["tier"] == "ranger", retro["first"]["tier"])
            # 50 for its answers plus build 213's speed bonus - and never
            # the 1,000 a badge pays when a run earns one.
            check("with no mastery bonus for them - the slice pays only its answers and speed",
                  50 <= retro["first"]["xp"] < 1000, retro["first"]["xp"])
            check("and never again", not retro["second"]["queued"] and not retro["second"]["tier"]
                  and not retro["first"]["left"], retro["second"])
            check("a new account has nothing handed out", retro["fresh"] == [], retro["fresh"])
            # Identity Crimes already held 20 of 20 under 210: not news.
            check("build 279's lower bands hand out what they newly qualify, and keep what 210 still owed",
                  sorted(retro.get("b279") or []) == ['Penal Code', 'Professionalism and Ethics', 'TCOLE Rules', 'Victims of Crime'],
                  retro.get("b279"))

            check("build 314 hands no badge out to a live account (version 3)",
                  retro.get("b314") == [], retro.get("b314"))

        print("\n8. the badge wall: a rank's level is a gate its badges open (build 314)")
        """ "You can't get past that next rank's level until you hit the
        badges needed." Every one of these fails on build 313, which had
        no wall: its level was the curve's, whatever the badges."""
        w = pg.evaluate("""async ()=>{
          const out = {};
          try{
            const tiers = TIER_ORDER_FULL.map(k => [TIER_UNLOCKS[k].level, TIER_UNLOCKS[k].badges]);
            out.tiers = tiers;
            const setAcct = (pts, perf, floor) => {
              store.lifetime = Object.assign({}, store.lifetime, { points: pts });
              store.unitPerfects = perf || {}; store.levelFloor = floor || 0;
              retroHideBadges = null; mergeHidePoints = null;
            };
            /* a badge count, made of real units at their real thresholds */
            const units = topicsIn(QUESTIONS);
            const perfFor = n => Object.fromEntries(units.slice(0, n).map(u => [u, badgeThresholdFor(u)]));
            out.walls = [];
            for(let b = 0; b <= units.length; b++){
              setAcct(xpForLevel(LEVEL_CAP) + 5000, perfFor(b), 0);
              out.walls.push([b, badgeCountOf(store), levelOf(store)]);
            }
            /* XP keeps counting at a wall, and the bar says so */
            setAcct(xpForLevel(30), {}, 0);
            const s0 = levelStateFor(store);
            out.atWall = { level: s0.level, stopped: s0.stopped, into: s0.into, span: s0.span, xp: s0.total };
            const idx = t => QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t && inWholeUnit(q)).map(([,i]) => i);
            const runOf = (unit, n) => {
              cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit];
              order = n ? idx(unit).slice(0, n) : idx(unit);
              runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
              attempts = {}; picked = {}; timedOutSet = {};
              order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
              summarize();
            };
            store.pendingBadgeUnlocks = []; store.pendingTierCutscene = null;
            const xp0 = store.lifetime.points;
            runOf('Victims of Crime', 6);
            out.afterRun = { gained: store.lifetime.points - xp0, level: levelOf(store),
              line: (document.querySelector('#stage .results-level-line') || {}).textContent || null,
              gate: (document.querySelector('#stage .results-level-gate') || {}).textContent || null };
            /* the badge arrives: the level jumps to what the XP has earned */
            const U = 'Identity Crimes';
            /* XP for level 26 - past the 21 wall, short of the 29 one a
               single badge moves it to */
            setAcct(xpForLevel(26) + 100, { [U]: badgeThresholdFor(U) - 1 }, 0);
            store.pendingBadgeUnlocks = []; store.pendingTierCutscene = null;
            const lv0 = levelOf(store);
            runOf(U, 0);
            const num = document.querySelector('#stage .results-level-num');
            out.jump = { before: lv0, after: levelOf(store), curve: levelFromPoints(store.lifetime.points),
                         badges: badgeCountOf(store), tag: num ? num.dataset.jump || null : null };
            /* THE GRANDFATHER FLOOR IS THE OLD CURVE'S LEVEL (build 314):
               "by leveling us up even more, the discrepancy of badges to
               levels WILL get even more." Build 313's curve rebuilt here
               from its own constants, not the page's helper. */
            const oldLevel = p => {
              let lvl = 1, need = 300, spent = 0;
              const growth = l => l <= 25 ? 1.05 : l === 26 ? 2.0 : l > 45 ? 1.0835 : 1.0199;
              const ceil = l => l <= 25 ? 9000 : 150000;
              while(lvl < 80 && p >= spent + need){ spent += need; lvl += 1;
                need = Math.min(ceil(lvl + 1), Math.round(need * growth(lvl + 1))); }
              return lvl;
            };
            const allBadges = Object.fromEntries(units.map(u => [u, badgeThresholdFor(u)]));
            out.floor = [5000, 20000, 39395, 66355, 87480, 160000].map(p => {
              applyLoadedData({ lifetime: { points: p }, unitPerfects: {}, onboardingComplete: true });
              retroHideBadges = null;
              const held0 = { floor: store.levelFloor, level: levelOf(store) };
              applyLoadedData({ lifetime: { points: p }, unitPerfects: allBadges, onboardingComplete: true });
              retroHideBadges = null;
              return { p, old: oldLevel(p), curve: levelFromPoints(p), floor: held0.floor, held: held0.level,
                       unheld: levelOf(store) };
            });
            applyLoadedData({ lifetime: { points: 0 }, onboardingComplete: true });
            out.freshFloor = store.levelFloor;
            /* the floor merges by max, both ways, and survives a copy that has none */
            const m1 = { levelFloor: 30, lifetime: {} }; mergeSameAccount(m1, { levelFloor: 40, lifetime: {} });
            const m2 = { levelFloor: 40, lifetime: {} }; mergeSameAccount(m2, { levelFloor: 30, lifetime: {} });
            const m3 = { levelFloor: 40, lifetime: {} }; mergeSameAccount(m3, { lifetime: {} });
            out.merge = [m1.levelFloor, m2.levelFloor, m3.levelFloor];
            /* the rankings row publishes the effective level, and the rank
               is asked about that level */
            setAcct(xpForLevel(40), perfFor(1), 0);
            const row = buildLeaderboardRow();
            out.row = { level: row && row.level, eff: levelOf(store), curve: levelFromPoints(store.lifetime.points),
                        rank: rankOf(store), rankOfCurve: rankOfStats(levelFromPoints(store.lifetime.points), 1, 0) };
            /* a reset starts under the wall like anybody new */
            store.levelFloor = 44; wipeLocalProgressAndSettings(); out.resetFloor = store.levelFloor;
            /* the Profile card at a gate: the numbers run past the level,
               and the Next gate section says what opens it */
            setAcct(xpForLevel(22) + 600, perfFor(0), 0);
            showProfile('identity'); await new Promise(r => setTimeout(r, 400));
            const q = sel => (document.querySelector(sel) || {}).textContent || null;
            out.profile = { top: q('.profile-level-sidetop'), gate: q('.next-gate-name'), line: q('.next-gate-line'),
                            chips: [...document.querySelectorAll('.next-gate .gate-chip')].map(e => e.textContent),
                            banked: !!document.querySelector('.profile-xpbar.is-banked') };
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        if w.get("threw"):
            check("the badge wall exists", False, w["threw"][:300])
        else:
            want = []
            for b in range(len(w["walls"])):
                levels = [lv for lv, bd in w["tiers"] if bd > b]
                want.append(min(levels) if levels else 80)
            got = [lv for b, bc, lv in w["walls"]]
            check("the wall per badge count is the first rank asking for more badges",
                  got == want and [bc for b, bc, lv in w["walls"]] == list(range(len(w["walls"]))), list(zip(want, got)))
            check("...which is 21, 30, 30, 40, 40, 50, 50, 60, 60, 70, 70, 70, then the cap",
                  got[:15] == [21, 30, 30, 40, 40, 50, 50, 60, 60, 70, 70, 70, 80, 80, 80], got)
            a0 = w["atWall"]
            check("at a wall the level is held and the bar is stopped, the XP past it still counted",
                  a0["level"] == 21 and a0["stopped"] and a0["into"] > a0["span"], a0)
            ar = w["afterRun"]
            check("XP keeps counting at a wall; the level does not move",
                  ar["gained"] > 0 and ar["level"] == 21, ar)
            check("the results card shows the overflow and the gate",
                  ar["line"] and " / " in ar["line"] and ar["gate"] and "to pass level 21" in ar["gate"], ar)
            j = w["jump"]
            check("earning the badge jumps the level straight to what the XP earned",
                  j["before"] == 21 and j["after"] == j["curve"] and 22 < j["after"] <= 30 and j["badges"] == 1, j)
            check("and the level-up says it was several levels", j["tag"] == str(j["after"] - j["before"]), j)
            fl = w["floor"]
            check("the grandfather floor is the level on the OLD curve, never the new one",
                  all(f["floor"] == f["old"] for f in fl), fl)
            check("nobody's level goes below what they hold now", all(f["held"] >= f["old"] and f["unheld"] >= f["old"] for f in fl), fl)
            # BUILD 314, FINAL: the curve is the live one, so the update moves
            # nobody's level - a held account sits exactly where it is today.
            check("nobody's level changes on the update (floor = curve = shown)",
                  all(f["held"] == f["old"] == f["curve"] for f in fl), fl)
            check("a brand-new account has no floor", w["freshFloor"] == 0, w["freshFloor"])
            check("a merge takes the higher floor, either way round", w["merge"] == [40, 40, 40], w["merge"])
            r = w["row"]
            check("the rankings row publishes the effective level, not the curve's",
                  r["level"] == r["eff"] == 30 and r["curve"] > 30, r)
            check("the rank is asked about the effective level", r["rank"] == "rookie" == r["rankOfCurve"], r)
            check("a reset clears the floor", w["resetFloor"] == 0, w["resetFloor"])
            pf = w["profile"]
            check("Profile at a gate: XP into the level over what it asks, Next gate, what opens it",
                  pf["top"] and re.match(r"^[0-9,]+ / [0-9,]+ XP$", pf["top"]) and pf["gate"] == "Bronze"
                  and pf["line"] == "Earn 1 badge to pass level 21" and pf["banked"]
                  and pf["chips"] == ["Level 21 \u2713", "Badges 0 / 1"], pf)

        print("\n9. firestore-admin.py audits with the page's own numbers")
        import importlib.util
        spec = importlib.util.spec_from_file_location("fadmin", os.path.join(ROOT, "tools", "firestore-admin.py"))
        fa = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(fa)
            page = pg.evaluate("""()=>({ q: Object.fromEntries(topicsIn(QUESTIONS).map(u => [u, unitQuestionCount(u)])),
              need: Object.fromEntries(topicsIn(QUESTIONS).map(u => [u, badgeThresholdFor(u)])),
              ranks: TIER_ORDER_FULL.map(k => [TIER_UNLOCKS[k].level, TIER_UNLOCKS[k].badges]),
              lv: [0, 300, 9912, 14306, 14427, 30000, 61965, 99999, 138431, 197370, 250000].map(p => [p, levelFromPoints(p), legacyLevelOfPoints(p)]) })""")
            check("its unit sizes and badge bands are the page's",
                  fa.UNIT_QUESTIONS == page["q"] and all(fa.badge_threshold(u) == n for u, n in page["need"].items()),
                  [u for u, n in page["need"].items() if fa.badge_threshold(u) != n])
            check("its ranks are the page's", [list(x) for x in fa.RANKS] == page["ranks"], page["ranks"])
            check("its two curves are the page's",
                  all(fa.level_of(p) == a and fa.legacy_level_of_points(p) == b for p, a, b in page["lv"]), page["lv"])
            f = {"lifetime": {"points": 30000}, "unitPerfects": {}, "levelFloor": 0}
            check("its effective level holds a no-badge account at 21", fa.effective_level(f) == 21, fa.effective_level(f))
        except Exception as e:
            check("firestore-admin.py loads and has the badge wall", False, repr(e))

        check("no uncaught JS along the way", not errs, errs[:3])
        ctx.close(); br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))" %
          ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
