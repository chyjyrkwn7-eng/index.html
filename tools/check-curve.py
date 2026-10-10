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

Build 318 re-fitted the curve to the measured class (1-50 untouched,
everything past 50 cheaper, 217,910 to level 80, 409,117 to 100 - the top
quarter at 100 by May, the middle of the class ~93 by Jul 8);
sections 4 and 4b hold it and fail on 219bfea:

    python3 tools/check-curve.py --against /path/to/219bfea/index.html

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
          /* BUILD 318: 1-50 are build 313's to the point, so every XP total
             short of the new level 51 (79,182; 79,512 on 313) reads the
             same level, one at a time. Past 50 levels only come sooner, and
             nobody shows above 49 (the badge wall), so no shown level moves. */
          for(let p = 0; p <= 79181; p += 1){
            if(oldLevel(p) !== levelFromPoints(p)){ frozenDiff = p; break; }
          }
          return { n, worst, frozenDiff, n313 };}""")
        check("no XP total from 0 to 600,000 (past 313's 598,449 for 80) reads a lower level than on build 313", drop["n"] == 0, drop["worst"])
        check("levels 1-50 are byte-identical (every XP total to 79,181)",
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

        print("\n4. what it costs to climb (build 318: fitted to the class, eased past 60)")
        costs = pg.evaluate("""()=>{
          const at = L => xpForLevel(L) - xpForLevel(L - 1);
          /* The curve to 100, stepped the way levelProgress() steps it but
             without the cap - levels 81-100 are defined now and open when
             LEVEL_CAP goes to 100 in January. */
          const per = [0, 0]; let need = LEVEL_BASE_POINTS;
          for(let lvl = 1; lvl < 100; lvl++){
            per.push(need);
            need = Math.min(levelCostCeiling(lvl + 2), Math.round(need * levelGrowthAt(lvl + 2)));
          }
          const tot = [0, 0]; for(let L = 2; L <= 100; L++) tot.push(tot[L - 1] + per[L]);
          return { l26: at(26), l50: at(50), l60: at(60), l61: at(61), l80: at(80),
                   toCap: xpForLevel(LEVEL_CAP), to21: xpForLevel(21), cap: LEVEL_CAP, per, tot };}""")
        per, tot = costs["per"], costs["tot"]
        print("      level  cost / total:", ", ".join("%d %s/%s" % (L, format(per[L], ","), format(tot[L], ","))
                                                  for L in (60, 61, 70, 80, 90, 100)))
        # Build 313's curve, from its own constants, to 100 (its x1.0835 tail
        # carried on past the cap): what "nobody moves" is measured against.
        old_per = [0, 0]; need = 300
        for lvl in range(1, 100):
            old_per.append(need)
            L = lvl + 2
            g = 1.05 if L <= 25 else 2.0 if L == 26 else 1.0835 if L > 45 else 1.0199
            need = min(9000 if L <= 25 else 150000, int(need * g + 0.5))
        """"If you are level 60 I don't want you to have to play for a
        week straight to earn 2 levels" - in DAYS at the pace the class
        actually earns."""
        two60 = costs["l60"] + costs["l61"]
        check("two levels at 60 is under a week at 6,000 XP a day",
              two60 / 6000.0 < 7, "%.1f days" % (two60 / 6000.0))
        check("level 21 still costs about 10,000 (early levels stay quick)", 8000 <= costs["to21"] <= 10500, costs["to21"])
        check("the cap is still 80 until January", costs["cap"] == 80, costs["cap"])
        # BUILD 318: "I want top 25 percent to reach level 100 by May. I'd
        # want most people at or very close to 100 by July 8th." Measured on
        # the class on Oct 10, that is ~410,000 XP at level 100 - which the
        # 8.35% tail of 46-60 cannot reach (40 levels at level 60's cost
        # alone come to ~495,000), so the easing starts at 50. Nobody SHOWS
        # above 49 (the badge wall), and every level past 50 is cheaper
        # than it was - so no XP total can read lower.
        same = [L for L in range(2, 51) if per[L] != old_per[L]]
        check("levels 1-50 cost exactly what build 313 charges, level by level", not same, same[:5])
        dearer = [L for L in range(51, 81) if per[L] >= old_per[L]]
        check("every level from 51 to 80 is cheaper than build 313 charged", not dearer,
              [(L, per[L], old_per[L]) for L in dearer[:3]])
        WANT = {50: 75181, 60: 116042, 70: 161659, 80: 217910, 90: 294417, 100: 409117}
        check("the totals: level 50 75,181, 60 116,042, 70 161,659, 80 217,910, 90 294,417, 100 409,117",
              all(tot[L] == v for L, v in WANT.items()) and costs["toCap"] == 217910,
              {L: tot[L] for L in WANT})
        # SMOOTH, NO SUDDEN STEPS. The x2 into 26 is build 313's and stays:
        # taking it out means cheaper levels from 26, which lifts most of the
        # class. Past 60 the climb must ease, not repeat the 8.35% tail.
        falls = [L for L in range(3, 101) if per[L] < per[L - 1]]
        check("no level costs less than the one before it (2 to 100)", not falls, falls[:5])
        steps = [(L, round(per[L] / per[L - 1], 4)) for L in range(3, 101) if L != 26 and per[L] > round(per[L - 1] * 1.0835) + 1]
        check("no level is more than 8.35% dearer than the one before, give or take rounding (except the kept x2 into 26)", not steps, steps[:5])
        past50 = max(per[L] / per[L - 1] for L in range(51, 101))
        check("past 50 no level is more than 5% dearer than the one before", past50 <= 1.0501, round(past50, 4))
        check("no level up to 100 costs more than level 80 did on build 313 (44,321)",
              max(per[2:101]) <= 44321, max(per[2:101]))
        check("and a level still costs more the higher you are",
              costs["l80"] > costs["l60"] > costs["l50"] > costs["l26"], costs["l80"])

        print("\n4b. January: LEVEL_CAP = 100 is the whole change")
        """Served as a copy with that one constant changed - the claim in the
        code is that nothing else has to move, so that is what is tested."""
        html = open(os.path.join(SERVE, "index.html"), encoding="utf-8").read()
        jan_html = html.replace("const LEVEL_CAP = 80;", "const LEVEL_CAP = 100;", 1)
        check("the copy has exactly one LEVEL_CAP to change", jan_html != html and html.count("const LEVEL_CAP = ") == 1)
        samples = list(range(0, 217910 + 2000, 97))
        lv80 = pg.evaluate("(ps)=> ps.map(p => levelFromPoints(p))", samples)
        jpg = ctx.new_page()
        jpg.route("**/jan.html", lambda route: route.fulfill(status=200, content_type="text/html", body=jan_html))
        jerrs = []
        jpg.on("pageerror", lambda e: jerrs.append(str(e)))
        jpg.goto("http://127.0.0.1:%d/jan.html" % PORT)
        jpg.wait_for_timeout(2600)
        jan = jpg.evaluate("""(ps)=>{ document.getElementById('splashscreen')?.remove();
          const top = levelProgress(xpForLevel(100) + 5000), below = levelProgress(xpForLevel(100) - 1);
          return { cap: LEVEL_CAP, to100: xpForLevel(100), to80: xpForLevel(80),
                   top: { level: top.level, atCap: top.atCap }, below: below.level,
                   at80: levelProgress(xpForLevel(80) + 1).atCap, lv: ps.map(p => levelFromPoints(p)) }; }""", samples)
        jpg.close()
        check("with the cap at 100: level 100 is 409,117 in all and the cap is there",
              jan["cap"] == 100 and jan["to100"] == 409117 and jan["top"] == {"level": 100, "atCap": True} and jan["below"] == 99,
              {k: jan[k] for k in ("cap", "to100", "top", "below")})
        check("...level 80 is an ordinary level then, and nothing at or below it moves",
              jan["to80"] == 217910 and not jan["at80"]
              and all(a == b for a, b in zip(lv80, jan["lv"]) if a < 80), (jan["to80"], jan["at80"]))
        check("...and the page still runs", not jerrs, jerrs[:2])

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
            const first = { queued: shown(), tier: (()=>{ const o = (typeof rankUpOwed === 'function') ? rankUpOwed() : null; return o ? TIER_ORDER_FULL[o.toIdx] : (store.pendingTierCutscene || null); })(),
                            left: store.retroBadgePending.slice(), xp: store.lifetime.points - xp0 };
            /* build 319: the rank-up is owed on Profile (rankUpOwed) until it is shown there */
            store.pendingBadgeUnlocks = []; store.pendingTierCutscene = null;
            { const o = (typeof rankUpOwed === 'function') ? rankUpOwed() : null; if(o) rankUpMarkShown(o.toIdx); }
            grantRetroBadgesOnce();                   // a relaunch must not list them again
            finish('Victims of Crime', 5);
            const second = { queued: shown(), tier: (()=>{ const o = (typeof rankUpOwed === 'function') ? rankUpOwed() : null; return o ? TIER_ORDER_FULL[o.toIdx] : (store.pendingTierCutscene || null); })() };
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
            check("and owes the rank-up they cause, on Profile (build 319)", retro["first"]["tier"] == "ranger", retro["first"]["tier"])
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

        print("\n8. the level bands: your badges cap your level, the XP is saved (build 314)")
        """ "their max level is at their rank ... someone is level 80 but
        doesn't have a single badge, their level would actually show as the
        max level in bronze." Each rank owns a block of levels and the badges
        you hold cap you at the top of the next block. Every one of these
        fails on build 313, which had no cap: its level was the curve's,
        whatever the badges."""
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
            /* XP keeps counting at a cap, and the bar says so */
            setAcct(xpForLevel(30) + 500, {}, 0);
            const s0 = levelStateFor(store);
            out.atWall = { level: s0.level, stopped: s0.stopped, into: s0.into, span: s0.span, xp: s0.total,
                           saved: s0.saved, curve: s0.curveLevel, opensTo: s0.opensTo, gate: s0.gateKey };
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
              gate: (document.querySelector('#stage .results-level-gate') || {}).textContent || null,
              closest: !!document.querySelector('#stage .results-level-closest, #stage .level-chal') };
            /* the badge arrives: the level jumps to what the XP has earned */
            const U = 'Identity Crimes';
            /* XP for level 33 - past the 29 cap, short of the 39 one a
               single badge moves it to */
            setAcct(xpForLevel(33) + 100, { [U]: badgeThresholdFor(U) - 1 }, 0);
            store.pendingBadgeUnlocks = []; store.pendingTierCutscene = null;
            const lv0 = levelOf(store);
            runOf(U, 0);
            const num = document.querySelector('#stage .results-level-num');
            out.jump = { before: lv0, after: levelOf(store), curve: levelFromPoints(store.lifetime.points),
                         badges: badgeCountOf(store), tag: num ? num.dataset.jump || null : null };
            /* NO GRANDFATHERING (build 314, final): "people go back in
               level (they still have the same xp just loaded at the gate)".
               An account arriving with no floor gets none: its level is the
               band cap its badges allow, and its XP is untouched. Nobody
               loses a RANK, though - checked against build 313's ladder,
               rebuilt here from TIER_UNLOCKS_313 and build 313's curve. */
            const oldLevel = p => {
              let lvl = 1, need = 300, spent = 0;
              const growth = l => l <= 25 ? 1.05 : l === 26 ? 2.0 : l > 45 ? 1.0835 : 1.0199;
              const ceil = l => l <= 25 ? 9000 : 150000;
              while(lvl < 80 && p >= spent + need){ spent += need; lvl += 1;
                need = Math.min(ceil(lvl + 1), Math.round(need * growth(lvl + 1))); }
              return lvl;
            };
            const rank313 = (lv, b) => {
              let k = -1;
              TIER_ORDER_FULL.forEach((key, i) => { const r = TIER_UNLOCKS_313[key];
                if(r && lv >= r.level && b >= r.badges) k = i; });
              return k;
            };
            out.floor = [];
            [5000, 20000, 39395, 66355, 87480, 160000, 600000].forEach(p => [0, 1, 3, 6, 9, 12].forEach(n => {
              applyLoadedData({ lifetime: { points: p }, unitPerfects: perfFor(n), onboardingComplete: true });
              retroHideBadges = null;
              const s = levelStateFor(store);
              out.floor.push({ p, n, badges: badgeCountOf(store), floor: store.levelFloor, curve: levelFromPoints(p),
                               old: oldLevel(p), level: s.level, cap: badgeWallLevel(badgeCountOf(store)),
                               saved: s.saved || 0, xp: store.lifetime.points,
                               rank: TIER_ORDER_FULL.indexOf(rankOf(store)), rank313: rank313(oldLevel(p), badgeCountOf(store)) });
            }));
            /* a floor a merge's bonus GAVE survives the load */
            applyLoadedData({ lifetime: { points: 160000 }, unitPerfects: {}, levelFloor: 33, onboardingComplete: true });
            retroHideBadges = null;
            out.gift = levelOf(store);
            applyLoadedData({ lifetime: { points: 0 }, onboardingComplete: true });
            out.freshFloor = store.levelFloor;
            /* the floor merges by max, both ways, and survives a copy that has none */
            const m1 = { levelFloor: 30, lifetime: {} }; mergeSameAccount(m1, { levelFloor: 40, lifetime: {} });
            const m2 = { levelFloor: 40, lifetime: {} }; mergeSameAccount(m2, { levelFloor: 30, lifetime: {} });
            const m3 = { levelFloor: 40, lifetime: {} }; mergeSameAccount(m3, { lifetime: {} });
            out.merge = [m1.levelFloor, m2.levelFloor, m3.levelFloor];
            /* the rankings row publishes the effective level, and the rank
               is asked about that level */
            setAcct(xpForLevel(45), perfFor(1), 0);
            const row = buildLeaderboardRow();
            out.row = { level: row && row.level, eff: levelOf(store), curve: levelFromPoints(store.lifetime.points),
                        rank: rankOf(store), rankOfCurve: rankOfStats(levelFromPoints(store.lifetime.points), 1, 0) };
            /* a reset starts under the wall like anybody new */
            store.levelFloor = 44; wipeLocalProgressAndSettings(); out.resetFloor = store.levelFloor;
            /* THE PROFILE CARD AT A CAP (build 315): three blocks - where
               you stand (rank, level, the XP bar and its numbers), the next
               rank as tasks, the badge case - each one tap into its screen. */
            const q = sel => (document.querySelector(sel) || {}).textContent || null;
            /* a colour-mix() comes back as color(srgb 0-1 0-1 0-1), not 0-255 - see
               CLAUDE.md's status bar note; both are read as 0-255 */
            const rgb = el => { if(!el) return null; const c = getComputedStyle(el).color; const m = c.match(/[\\d.]+/g);
              if(!m) return null; const v = m.slice(0, 3).map(Number); return /^color\\(/.test(c) ? v.map(x => Math.round(x * 255)) : v; };
            const readProfile = () => {
              const tasks = [...document.querySelectorAll('.pf-goal .pf-task')];
              /* build 317 moved the case above the Next rank card; the 317
                 touch-up put it back at the bottom ("The badge case being
                 at the top is not the move, revert that location at the
                 bottom") */
              const order = ['.pf-standing', '.pf-goal', '.pf-case'].map(sel => document.querySelector('.profile-hero ' + sel));
              return {
                blocks: order.map(n => !!n),
                inOrder: order.every(Boolean) && !!(order[0].compareDocumentPosition(order[1]) & 4) && !!(order[1].compareDocumentPosition(order[2]) & 4),
                nested: document.querySelectorAll('.pf-standing button, .pf-goal button, .pf-case button').length,
                study: /\bStudy\b/.test(q('.pf-goal') || ''),
                level: q('.pf-standing .pf-level'), rank: q('.pf-standing .pf-rankname'),
                nums: q('.pf-standing .pf-xpnums .xpnums'), over: !!document.querySelector('.pf-standing .xpnums.is-over'),
                total: q('.pf-standing .pf-xp-total'), totalUnder: !!document.querySelector('.pf-standing .pf-xpnums .pf-xp-total'),
                totalCol: rgb(document.querySelector('.pf-standing .pf-xp-total')), haveCol: rgb(document.querySelector('.pf-standing .xpnums-have')), needCol: rgb(document.querySelector('.pf-standing .xpnums-need')), banked: !!document.querySelector('.pf-standing .pf-xpbar.is-banked'),
                note: q('.pf-standing .pf-xp-note'), noteWall: !!document.querySelector('.pf-standing .pf-xp-note.is-wall'),
                nextGate: !!document.querySelector('.next-gate'), max: !!document.querySelector('.level-max-tag'),
                goal: q('.pf-goal .pf-goal-name'), sub: q('.pf-goal .pf-goal-sub'), goalText: q('.pf-goal'),
                tasks: tasks.map(t => ({ label: (t.querySelector('.pf-task-label') || {}).textContent, met: t.classList.contains('is-met'),
                  tick: (t.querySelector('.pf-check') || {}).textContent, note: (t.querySelector('.pf-task-note') || {}).textContent || null,
                  val: (t.querySelector('.pf-task-val') || {}).textContent,
                  now: rgb(t.querySelector('.pf-now')), need: rgb(t.querySelector('.pf-need')) })),
                tiles: [...document.querySelectorAll('.pf-goal .pf-rw .pf-rw-lab')].map(n => n.textContent),
                caseCount: q('.pf-case .pf-case-count') };
            };
            setAcct(xpForLevel(31) + 600, perfFor(0), 0);
            showProfile('identity'); await new Promise(r => setTimeout(r, 400));
            out.profile = readProfile();
            /* Madison's screenshot: level 49 at the four-badge wall, Gold
               next. The level task asks for 40 and must not talk about 49,
               or about "your 5th badge". */
            setAcct(xpForLevel(52) + 200, perfFor(4), 0);
            showProfile('identity'); await new Promise(r => setTimeout(r, 400));
            out.profile49 = readProfile();
            /* Every block opens its screen from wherever it is tapped: the
               point is found by hit-testing, so anything laid over a block
               (or a control inside it) would catch the tap instead. */
            const tapAt = async (sel, inner) => {
              showProfile('identity'); await new Promise(r => setTimeout(r, 300));
              const box = document.querySelector('.profile-hero ' + sel);
              const t = box && (box.querySelector(inner) || box);
              if(!t) return { hit: false, screen: null };
              t.scrollIntoView({ block: 'center', behavior: 'instant' });
              const r = t.getBoundingClientRect();
              const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
              const hit = !!(el && el.closest(sel) === box);
              /* the point can land on an SVG, which has no click() - a real
                 bubbling click is what a finger sends anyway */
              if(hit) el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
              await new Promise(r => setTimeout(r, 300));
              return { hit, screen: (document.querySelector('#stage > .panel') || {}).className || null,
                       map: !!document.querySelector('.rankmap-stop'), badges: !!document.querySelector('.badges-tab'),
                       title: (document.getElementById('count') || {}).textContent || null };
            };
            out.taps = { standing: await tapAt('.pf-standing', '.pf-xpbar'), goalTile: await tapAt('.pf-goal', '.pf-rw.is-flare'),
                         goalTask: await tapAt('.pf-goal', '.pf-task .pf-bar'), caseStrip: await tapAt('.pf-case', '.badge-strip-cell:nth-child(9)') };
            document.querySelectorAll('.invite-overlay').forEach(n => n.remove());
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
            def cap_for(b):
                met = sum(1 for lv, bd in w["tiers"] if b >= bd)
                return w["tiers"][met + 1][0] - 1 if met + 1 < len(w["tiers"]) else 80
            want = [cap_for(b) for b in range(len(w["walls"]))]
            got = [lv for b, bc, lv in w["walls"]]
            check("the cap per badge count is the top of the next rank's band",
                  got == want and [bc for b, bc, lv in w["walls"]] == list(range(len(w["walls"]))), list(zip(want, got)))
            check("...which is 29, 39, 39, 49, 49, 59, 59, 69, 69, 79, 79, 79, then 80",
                  got[:15] == [29, 39, 39, 49, 49, 59, 59, 69, 69, 79, 79, 79, 80, 80, 80], got)
            a0 = w["atWall"]
            check("at a cap the level is held and the bar is stopped, the XP past it still counted",
                  a0["level"] == 29 and a0["stopped"] and a0["into"] > a0["span"], a0)
            check("the levels past the cap are counted as saved, and the badge opens the next band",
                  a0["saved"] == a0["curve"] - 29 >= 1 and a0["opensTo"] == 39 and a0["gate"] == "rookie", a0)
            ar = w["afterRun"]
            check("XP keeps counting at a cap; the level does not move",
                  ar["gained"] > 0 and ar["level"] == 29, ar)
            # Build 314: "not a fan of the challenge stuff under the xp there
            # at all. Remove it" - the numbers alone, nothing under them.
            check("the results card shows the overflow, with no challenge lines under it",
                  ar["line"] and " / " in ar["line"] and ar["gate"] is None
                  and not ar.get("closest"), ar)
            j = w["jump"]
            check("earning the badge jumps the level straight to what the XP earned",
                  j["before"] == 29 and j["after"] == j["curve"] and 29 < j["after"] <= 39 and j["badges"] == 1, j)
            check("and the level-up says it was several levels", j["tag"] == str(j["after"] - j["before"]), j)
            fl = w["floor"]
            check("no grandfathering: a loaded account has no floor", all(f["floor"] == 0 for f in fl), fl[:3])
            check("the shown level is the curve's, capped by the badges' band",
                  all(f["level"] == min(f["curve"], f["cap"]) for f in fl), [f for f in fl if f["level"] != min(f["curve"], f["cap"])][:3])
            check("the XP is untouched, and every level past the cap is saved",
                  all(f["xp"] == f["p"] and f["saved"] == max(0, f["curve"] - f["cap"]) for f in fl),
                  [f for f in fl if f["saved"] != max(0, f["curve"] - f["cap"])][:3])
            check("nobody loses a rank they held on build 313", all(f["rank"] >= f["rank313"] for f in fl),
                  [f for f in fl if f["rank"] < f["rank313"]][:3])
            # the band cap is always above the level of the highest rank the
            # badges hold - so the cap alone never costs a rank either
            check("the cap never sits below a rank the badges hold",
                  all(cap_for(b) >= max([lv for lv, bd in w["tiers"] if b >= bd] or [0]) for b in range(17)))
            check("someone at level 80 with no badges shows 29 with 51 saved",
                  any(f["p"] == 600000 and f["n"] == 0 and f["level"] == 29 and f["saved"] == f["curve"] - 29 for f in fl), fl[-6:])
            check("a floor a merge's bonus gave survives the load", w["gift"] == 33, w["gift"])
            check("a brand-new account has no floor", w["freshFloor"] == 0, w["freshFloor"])
            check("a merge takes the higher floor, either way round", w["merge"] == [40, 40, 40], w["merge"])
            r = w["row"]
            check("the rankings row publishes the shown level, not the curve's",
                  r["level"] == r["eff"] == 39 and r["curve"] > 39, r)
            check("the rank is asked about the shown level", r["rank"] == "rookie" == r["rankOfCurve"], r)
            check("a reset clears the floor", w["resetFloor"] == 0, w["resetFloor"])
            pf = w["profile"]
            grey = lambda c: c is not None and max(c) - min(c) <= 14
            blue = lambda c: c is not None and c[2] - c[0] >= 80
            gold = lambda c: c is not None and c[0] - c[2] >= 80
            # Build 315: Madison picked option A - standing, next rank, case.
            # REVISED IN 317: "Would it make more sense if the badge case was
            # put above the rank challenge box thing?" - standing, case, next.
            # REVISED BACK IN THE 317 TOUCH-UP: "The badge case being at the
            # top is not the move, revert that location at the bottom."
            check("Profile's card is three blocks in order: where you stand, the next rank, the badge case - nothing tappable nested in them, no Study button",
                  pf["blocks"] == [True, True, True] and pf["inOrder"] and pf["nested"] == 0 and not pf["study"], pf)
            # "How do we still get that nice xp stuff where it shows how much
            # over you are, how much till the next level ... we wouldn't need
            # that total xp there because it'd be with all the xp stuff"
            # REVISED IN 316: the total is back on the rank line ("Silver ·
            # Level 49 · 85,705 XP"), the mockup that was preferred - and it
            # says what it is: "Where it shows your total xp, I feel like that
            # should say total xp."
            # REVISED IN 317: "The total xp you have earned should be on the
            # bottom right under the xp bar not above it", in a deeper blue;
            # and over at a cap both numbers are the same blue.
            # REVISED IN THE 317 TOUCH-UP: one XP blue for the numbers and
            # the total ("I guess the total xp should be the same?").
            check("Profile at a cap: this level's XP marked over under the bar (both numbers and the total one blue), the total under the bar saying 'total XP', the bar banked, and no Next gate box",
                  pf["nums"] and re.match(r"^[0-9,]+ / [0-9,]+ XP$", pf["nums"]) and pf["over"]
                  and pf["haveCol"] == pf["needCol"] == pf["totalCol"] and blue(pf["needCol"])
                  and re.match(r"^[0-9,]+ total XP$", pf["total"] or "") and pf["totalUnder"] and blue(pf["totalCol"]) and pf["banked"]
                  and not pf["max"] and not pf["nextGate"] and pf["level"] == "Level 29", pf)
            # "I don't like how it means that 5th badge part": no ordinal.
            # REVISED IN 316: no count either - it says this is as high as the
            # rank goes, that the next rank's challenges open more, and that
            # the XP is kept: "this is the max level you can achieve at this
            # rank, complete the challenges to keep leveling up, your xp still
            # goes up and will be given to you when the levels or ranks unlock".
            # REVISED IN 317: not gold - "make it like the wording and color of
            # what's shown under the xp challenge" - and the end reworded:
            # "your earned xp is still here, rank up to unlock the new set of
            # levels", combined with the second sentence.
            # REWRITTEN IN 317 (second pass): "could be worded better and easier
            # to understand ... explains to the user that the overflow xp will
            # be used towards the next levels once unlocked but simple". The
            # SHAPE is held, not the prose: top level, which rank's
            # challenges open more, and that the XP still counts toward them.
            note_shape = lambda n, held, nxt: bool(n) and n.startswith("You've reached the top level " + held + ". ") \
                and ("Finish the " + nxt + " rank challenges to unlock more levels.") in n \
                and "still counts" in n and "toward those levels" in n and "is kept" not in n
            check("...and the plain line under the bar says this is the top level before a first rank, the Bronze rank challenges unlock more levels, and the XP still counts toward them - no number in it",
                  not pf["noteWall"] and note_shape(pf["note"], "before your first rank", "Bronze")
                  and not re.search(r"\d", pf["note"] or ""), pf["note"])
            t = pf["tasks"]
            check("the next rank is Bronze, 1 of 2 done, with what is left listed first",
                  pf["goal"] == "Bronze" and pf["sub"] == "1 of 2 done" and len(t) == 2
                  and t[0]["label"] == "Earn 1 badge" and not t[0]["met"] and t[1]["label"] == "Reach level 21" and t[1]["met"], pf)
            # 315 swapped them on request ("the goal number and moving level
            # number should swap colors"); REVISED IN 316, asked back: "I
            # preferred how the leveling requirement looked too" - your count
            # in the colour, the goal plain, met or not.
            # REVISED IN 317: "Grey on left, gold on right, both gold if met,
            # and if it goes over, just the same gold" - the XP bar's rule.
            # REVISED IN 318: "the number on the left can match actually,
            # don't make it grey" - both numbers in the row's colour, met or
            # not (fails on 219bfea, where the unmet count is grey).
            check("a task's count and its goal are both in its colour, met or not (never a grey count); a met one has a tick",
                  len(t) == 2 and gold(t[0]["now"]) and t[0]["now"] == t[0]["need"] and t[0]["tick"] == ""
                  and blue(t[1]["now"]) and blue(t[1]["need"]) and t[1]["tick"] == "✓", t)
            # REVISED IN 317, round two: "the flare and the theme unlock box
            # thing in profile should swap" - the rank's own flare first.
            # REVISED AGAIN IN THE 317 FIX: "switch the flare and theme spot
            # again, preferred the flare one in the middle" - theme, flare.
            check("what Bronze unlocks is shown as tiles: its theme, then its flare in the middle",
                  pf["tiles"][:2] == ["Theme", "Flare"], pf["tiles"])
            p49 = w["profile49"]
            t49 = p49["tasks"]
            # "talks about you being level 49 but it's asking for level 40"
            check("at level 49 behind the four-badge wall, Gold's level task reads 40 / 40, done, and says nothing about 49",
                  p49["level"] == "Level 49" and p49["goal"] == "Gold" and len(t49) == 2
                  and t49[1]["label"] == "Reach level 40" and t49[1]["met"] and (t49[1]["val"] or "").replace(" ", "") == "40/40"
                  and "49" not in (p49["goalText"] or "")
                  and not re.search(r"\b\d+(st|nd|rd|th)\b", p49["goalText"] or ""), p49)
            # Build 316: "The description in the level unlock challenge when at
            # max ... make that say something more along the lines of there,
            # complete rank challenges or something. Don't specifically mention
            # the badges amount there ... I like how it mentions the 'your saved
            # xp turns into levels' but could that be better?"
            # REVISED IN 317: "could be simpler ... redundant to what's
            # underneath the xp bar ... less wordy".
            # REVISED IN 317, round two: "the description under the level
            # challenge, I'm not in love with it ... could be better" - the bar's
            # note says where the XP goes; this one says what is left for the rank.
            check("...and at the wall the level task says, in one short line, it is done and the badge challenge is left for Gold - no badge count",
                  t49[1]["note"] == "Done. Finish the badge challenge to reach Gold."
                  and not re.search(r"\d", t49[1]["note"] or ""), t49[1]["note"])
            check("...and the line under the bar says this is the top level for Silver and the Gold rank challenges unlock more",
                  note_shape(p49["note"], "for Silver", "Gold"), p49["note"])
            tp = w["taps"]
            check("tapping where you stand opens the climb", tp["standing"]["hit"] and tp["standing"]["map"], tp["standing"])
            # "assuming you click anywhere in that box, it opens up the rank road map"
            check("tapping the next rank anywhere - a reward tile or a task's bar - opens the climb",
                  tp["goalTile"]["hit"] and tp["goalTile"]["map"] and tp["goalTask"]["hit"] and tp["goalTask"]["map"], tp)
            # "ensure if you click anywhere on that, it opens up the larger one"
            check("tapping any badge in the strip opens the badge case",
                  tp["caseStrip"]["hit"] and tp["caseStrip"]["badges"] and not tp["caseStrip"]["map"], tp["caseStrip"])

        print("\n9. firestore-admin.py audits with the page's own numbers")
        import importlib.util
        spec = importlib.util.spec_from_file_location("fadmin", os.path.join(ROOT, "tools", "firestore-admin.py"))
        fa = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(fa)
            page = pg.evaluate("""()=>({ q: Object.fromEntries(topicsIn(QUESTIONS).map(u => [u, unitQuestionCount(u)])),
              need: Object.fromEntries(topicsIn(QUESTIONS).map(u => [u, badgeThresholdFor(u)])),
              ranks: TIER_ORDER_FULL.map(k => [TIER_UNLOCKS[k].level, TIER_UNLOCKS[k].badges]),
              lv: [0, 300, 9912, 14306, 14427, 30000, 61965, 99999, 138431, 197370, 250000].map(p => [p, levelFromPoints(p), legacyLevelOfPoints(p)]),
              caps: Array.from({length: 17}, (_, b) => badgeWallLevel(b)) })""")
            check("its unit sizes and badge bands are the page's",
                  fa.UNIT_QUESTIONS == page["q"] and all(fa.badge_threshold(u) == n for u, n in page["need"].items()),
                  [u for u, n in page["need"].items() if fa.badge_threshold(u) != n])
            check("its ranks are the page's", [list(x) for x in fa.RANKS] == page["ranks"], page["ranks"])
            check("its two curves are the page's",
                  all(fa.level_of(p) == a and fa.legacy_level_of_points(p) == b for p, a, b in page["lv"]), page["lv"])
            check("its band caps are the page's", [fa.badge_wall(b) for b in range(17)] == page["caps"],
                  ([fa.badge_wall(b) for b in range(17)], page["caps"]))
            f = {"lifetime": {"points": 600000}, "unitPerfects": {}}
            check("its effective level holds a no-badge account at 29, with no floor",
                  fa.effective_level(f) == 29, fa.effective_level(f))
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
