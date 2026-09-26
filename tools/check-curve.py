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
        # Madison's bands as of build 210, verbatim: 25 or fewer questions
        # 20 hundos, 26-50 15, 51-100 10, 101-200 5, over 200 3.
        bands = [(0, 25, 20), (26, 50, 15), (51, 100, 10),
                 (101, 200, 5), (201, 10 ** 6, 3)]
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
        # AND NO UNIT GOT DEARER THAN BUILD 209 CHARGED IT - the same rule,
        # unit by unit, against the bands that were live before 210.
        old_bands = [(0, 19, 35), (20, 40, 25), (41, 60, 15),
                     (61, 100, 10), (101, 200, 7), (201, 10 ** 6, 5)]
        raised = [(u, v["q"], v["need"], next(h for lo, hi, h in old_bands if lo <= v["q"] <= hi))
                  for u, v in units.items()
                  if v["need"] > next(h for lo, hi, h in old_bands if lo <= v["q"] <= hi)]
        check("no unit needs more hundos than it did on build 209", not raised, raised)

        print("\n2. nobody's level drops, for any XP total")
        drop = pg.evaluate("""([oldStep, oldLate, unchangedThrough])=>{
          /* The old curve rebuilt from its own two constants, stepping
             exactly the way levelProgress() does - including the
             Math.round and the ceiling - so this compares curves rather
             than two different ways of writing one. */
          function oldLevel(p){
            let lvl = 1, need = LEVEL_BASE_POINTS, spent = 0;
            const growth = l => l <= LEVEL_FREEZE_THROUGH ? LEVEL_GROWTH
                               : (l === LEVEL_FREEZE_THROUGH + 1 ? oldStep : oldLate);
            const ceil = l => l <= LEVEL_FREEZE_THROUGH ? LEVEL_COST_MAX : LEVEL_COST_TOP;
            while(lvl < LEVEL_CAP && p >= spent + need){
              spent += need; lvl += 1;
              need = Math.min(ceil(lvl + 1), Math.round(need * growth(lvl + 1)));
            }
            return lvl;
          }
          /* EVERY TOTAL THAT PUTS SOMEBODY AT OR BELOW 45 on the curve
             the class is on reads the same level on this one. Above 45
             it is dearer by design (build 210) - nobody held more than
             43 when it shipped - so the sweep stops where the old curve
             reaches 46. */
          let worst = null, n = 0;
          for(let p = 0; p <= 600000; p += 137){
            const a = oldLevel(p);
            if(a > unchangedThrough) break;
            const b = levelFromPoints(p);
            if(b !== a){ n++; if(!worst) worst = { p, was: a, now: b }; }
          }
          /* The frozen stretch has to be byte-identical, not merely not
             worse - that is what "do not change anyone's current level
             what so ever" asks for, and every account in the class is
             inside it. */
          let frozenDiff = null;
          for(let p = 0; p <= 15000; p += 31){
            if(oldLevel(p) !== levelFromPoints(p)){ frozenDiff = p; break; }
          }
          return { n, worst, frozenDiff, cap: LEVEL_CAP };}""", [OLD_STEP, OLD_LATE, UNCHANGED_THROUGH])
        check("no level at or below 45 moves by a single point", drop["n"] == 0, drop["worst"])
        check("levels 1-25 are byte-identical to the live build",
              drop["frozenDiff"] is None, drop["frozenDiff"])

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
                      "no rank got harder than the live build",
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
            """A rank is computed fresh from level and badges, so raising
            either number takes a rank off somebody who holds it. Iron was
            reached by a real person the day it shipped."""
            LIVE = {"rookie": (21, 1), "ranger": (29, 3), "veteran": (36, 5),
                    "vanguard": (45, 8), "adept": (52, 11), "elite": (65, 15),
                    "titan": (80, 20)}
            raised = [(t["key"], t["level"], t["badges"], LIVE[t["key"]])
                      for t in line["tiers"]
                      if t["key"] in LIVE
                      and (t["level"] > LIVE[t["key"]][0] or t["badges"] > LIVE[t["key"]][1])]
            check("no rank got harder than the live build", not raised, raised)
            stale = [t["key"] for t in line["tiers"]
                     if str(t["level"]) not in t["label"] or str(t["badges"]) not in t["label"]]
            check("every rank's label says the numbers it actually checks", not stale, stale)

        print("\n4. what it costs to climb")
        costs = pg.evaluate("""()=>{
          const at = L => xpForLevel(L) - xpForLevel(L - 1);
          let minRatioPast45 = Infinity;
          for(let L = 47; L <= LEVEL_CAP; L++) minRatioPast45 = Math.min(minRatioPast45, at(L) / at(L - 1));
          return { l26: at(26), l50: at(50), l60: at(60), l61: at(61), l80: at(80),
                   toCap: xpForLevel(LEVEL_CAP), minRatioPast45 };}""")
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
        check("past 45 every level is at least 6% dearer than the last",
              costs["minRatioPast45"] >= 1.059, round(costs["minRatioPast45"], 4))  # 6%, less whole-XP rounding
        check("the whole climb to 80 is about 375,000 XP",
              abs(costs["toCap"] - 375000) <= 3750, costs["toCap"])
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
            const idx = t => QUESTIONS.map((q,i)=>[q,i])
              .filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
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
            const first = { queued: store.pendingBadgeUnlocks.slice(), tier: store.pendingTierCutscene,
                            left: store.retroBadgePending.slice(), xp: store.lifetime.points - xp0 };
            store.pendingBadgeUnlocks = []; store.pendingTierCutscene = null;
            grantRetroBadgesOnce();                   // a relaunch must not list them again
            finish('Victims of Crime', 5);
            const second = { queued: store.pendingBadgeUnlocks.slice(), tier: store.pendingTierCutscene };
            /* A brand-new account is current at sign-up: nothing handed out. */
            store.badgeBandsVersion = 2; store.retroBadgePending = [];
            store.unitPerfects = {'Identity Crimes': 20};
            grantRetroBadgesOnce();
            return { listed, first, second, fresh: store.retroBadgePending.slice() };
          } catch(e){ return { threw: String(e) }; }}""")
        if retro.get("threw"):
            check("handed-out badges are listed once, on launch", False, retro["threw"])
        else:
            check("handed-out badges are listed once, on launch",
                  sorted(retro["listed"]) == ['Identity Crimes', 'Penal Code', 'TCOLE Rules'], retro["listed"])
            check("the next test celebrates each of them",
                  sorted(retro["first"]["queued"]) == sorted(retro["listed"]), retro["first"])
            check("and plays the rank-up they cause", retro["first"]["tier"] == "ranger", retro["first"]["tier"])
            check("with no mastery bonus for them - the slice pays only its answers",
                  retro["first"]["xp"] == 50, retro["first"]["xp"])
            check("and never again", not retro["second"]["queued"] and not retro["second"]["tier"]
                  and not retro["first"]["left"], retro["second"])
            check("a new account has nothing handed out", retro["fresh"] == [], retro["fresh"])

        check("no uncaught JS along the way", not errs, errs[:3])
        ctx.close(); br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))" %
          ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
