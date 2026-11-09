#!/usr/bin/env python3
"""check-tours.py - do the app's tooltips still point at things that exist?

The fourth question, after "is anything broken" (the sweep), "did it land
where I meant it to" (check-positions) and "does the app still DO the right
thing" (check-behaviour). This one is narrower and it exists because of a
specific, silent failure mode:

    renderStep() does `if(!el){ advance(); return; }`

A tour step whose target selector no longer matches anything is SKIPPED, in
silence. Nothing throws, nothing logs, the tour still runs and still looks
fine - it is just shorter than it was written to be. That is how the Profile
tour lost its calendar step: the row was rebuilt as .profile-classline and
the step went on pointing at .cal-profile-row, which is a Settings class.
Four steps were declared, three were ever shown, and the only way to notice
was to count them.

So this counts them. For every tour in the app it walks the real thing on a
real screen and asserts:

  - every step declared in the source actually renders (no silent skips);
  - each tooltip lands fully inside the viewport;
  - the tour ends rather than looping.

It also asserts that every `startSimpleTour` call site in index.html is
covered by a scenario below, on the same principle as SCREENS in
sweep-layout.py: a green run is only worth what it looked at, and a tour
added without a scenario here is a tour nothing checks.

Run on both reference devices, since a tooltip that fits a 440px phone can
still be pushed off a 834px iPad (and the other way round).

    python3 tools/check-tours.py
    python3 tools/check-tours.py --only profile
"""

import functools
import http.server
import json
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = __file__.rsplit("/tools/", 1)[0]
INDEX = ROOT + "/index.html"

DEVICES = [("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11\"", 834, 1194)]

# A CALM HOME for the two tips that wait for one (r18). The seed is a high-level account, so a character unlock is owed and
# boot raises its spotlight (.rs-spot, ~7s up) on a timer of its own - before or after this setup runs depending on how loaded
# the machine is. Overriding homeUnlocksOwed only stopped the NEXT ask; a spotlight already up held the tip back past the
# 8-9s wait and the gate read "0 of 1 steps rendered" (found alone on a quiet machine, 3 of 3). The app is right to wait for
# a spotlight; the fixture owes nothing: the owed unlocks are marked shown (as check-fixes does) and any spotlight is cleared.
CALM_HOME = ("try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){} "
             "try{ homeUnlocksOwed = () => false; }catch(e){} "
             "document.querySelectorAll('.rs-spot, .daily-alert').forEach(n => n.remove()); ")

# Each scenario arms one tour and drives the app to the screen that runs it.
# `flag` is the store field the screen checks; `setup` is evaluated in the
# page to reach that screen. `source` is the line the declared step count is
# read from, so the two can never drift apart by hand.
SCENARIOS = [
    # The one tour with no store flag at all: it is gated by
    # `pendingMainMenuTour`, a module-level variable set when onboarding
    # finishes, so there is nothing to seed and it has to be called by hand
    # from Home. (Seeding a "seenMainMenuTour" does nothing - no such field
    # exists, which is worth knowing before anyone adds one.)
    {"key": "mainmenu", "flag": None, "source": "startMainMenuTour",
     "setup": "showHome(); startMainMenuTour()",
     "note": "the bottom bar, the daily question, the flares"},
    # Build 321: an existing account's meeting with Nova - the main menu's
    # tips (in their returning words) and then what is new on Home and
    # Profile. Gated by store.novaMet; called by hand here, as above.
    {"key": "novareturn", "flag": None, "source": "startNovaReturnTour",
     "setup": "showHome(); startNovaReturnTour()",
     "note": "the main menu's tips, then the planet, Profile, the calendar"},
    # Build 384: the class button's tip, once, on its own, for an account from before the button (maybeClassButtonTip waits
    # 3s for Home to settle, then a few calm beats).
    {"key": "classtip", "flag": "seenClassTip", "source": "maybeClassButtonTip",
     # calm Home first (no unlock cards owed, no banner up), as an account with nothing else to say would be
     "setup": CALM_HOME + "showHome(); maybeClassButtonTip()",
     "wait": 8000, "min": 1,
     "note": "the class button, on Home"},
    # Build 384 round 4: Start Studying's tip, the last of a sign-up's tips - after the sign-up's Add to Home Screen sheet
    # (scheduleStudyTip waits for it, for the +100 XP and for a calm Home). Standalone here: nothing owed, so it comes at once.
    {"key": "studytip", "flag": None, "source": "scheduleStudyTip",
     "setup": CALM_HOME + "try{ localStorage.removeItem('class26e.a2hs'); }catch(e){} showHome(); scheduleStudyTip()",
     "wait": 9000, "min": 1,
     "note": "Start Studying, on Home"},
    {"key": "modeselect", "flag": "seenModeSelectTour", "source": "showModeSelect",
     "setup": "showModeSelect()", "note": "Drill / Quiz / Review / Virtual Room"},  # MOVED IN 327 (b327k)
    {"key": "unitselect", "flag": "seenUnitSelectTour", "source": "showSetup",
     "setup": "cfg.mode='drill'; showSetup()", "note": "unit cards, the count, Start"},
    {"key": "vroomunits", "flag": "seenUnitSelectTour", "source": "showVirtualRoomSetup",
     "setup": "showVirtualRoomSetup()", "note": "same steps, reached a different way"},
    {"key": "settings", "flag": "seenSettingsTour", "source": "showAppearance",
     "setup": "showAppearance()", "note": "one step per section"},
    {"key": "profile", "flag": "seenProfileTour", "source": "showProfile",
     "setup": "showProfile('profile')", "note": "Customize, rank, next rank, badge case, Friends, Stats, Settings"},
    # Build 289: the same three tips on their own, for everybody who had
    # already seen the Profile tour - armed by the tourRev 3 re-arm, which
    # is what the setup does by hand.
    {"key": "profiletips", "flag": None, "source": "PROFILE_TIPS_289",
     "setup": "store.seenProfileTour = true; store.profileTips289 = true; showProfile('profile')",
     "note": "Customize, rank box, badge box"},
    # Build 319 (h): the Leaderboard is its own screen again (the Class
    # tab builder g made was sent back), so its tour is showRankings' again.
    {"key": "rankings", "flag": "seenRewardsTour", "source": "showRankings",
     "setup": "showRankings()", "note": "the three boards, search, Find me"},
    # build 279: the one-time "hold a unit" tip, on the first unit tapped.
    # Gated by a localStorage key, not a store flag, so the setup clears it
    # and taps the first card itself.
    {"key": "unithold", "flag": None, "source": "showUnitHoldTip",
     "setup": "localStorage.removeItem('class26e.unithold.tip'); cfg.mode='drill'; showSetup(); setTimeout(()=>{ const r=document.querySelector('.pick:not(.pick-tba)'); if(r) r.click(); }, 400)",
     "note": "two steps on the tapped unit card"},
    # summarize() runs at the end of a test and needs a finished run behind
    # it, which no cold mount can produce. Declared here so the coverage
    # check below still sees it, and skipped in the walk.
    {"key": "firstresults", "flag": "seenFirstResultsTour", "source": "summarize",
     "setup": None, "note": "end of the first test - needs a real run"},
]

SEED = {
    "onboardingComplete": True, "firstName": "Madison", "avatarChar": "ninja",
    "points": 12400, "tourRev": 99, "rankMapFx244": True,
    "lifetime": {"points": 12400, "answered": 2100, "correct": 1840, "drillPlays": 40,
                 "examPlays": 9, "gamePlays": 6, "perfectTests": 51,
                 "longestStreak": 44, "currentStreak": 12},
    "unitPerfects": {"Professionalism and Ethics": 35, "TCOLE Rules": 35,
                     "Penal Code": 35, "Racial Profiling": 22},
}


def shared_steps(src, name):
    """Steps in a `const NAME = [ ... ];` list of tour steps."""
    m = re.search(r"const %s = \[" % re.escape(name), src)
    if not m:
        return 0
    i = m.end() - 1
    depth, j = 0, i
    while j < len(src):
        if src[j] == "[":
            depth += 1
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return len(re.findall(r"\btarget\s*:", src[i:j]))


def declared_steps(src):
    """How many steps each tour's source actually declares.

    Counts `target:` inside the array literal handed to startSimpleTour,
    matching brackets rather than guessing, so a step carrying a nested
    object or an array cannot throw the count off.
    """
    out = {}
    for m in re.finditer(r"startSimpleTour\(\s*\[", src):
        i = m.end() - 1
        depth, j = 0, i
        while j < len(src):
            if src[j] == "[":
                depth += 1
            elif src[j] == "]":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = src[i:j]
        # which function is this call inside?
        fn = None
        for f in re.finditer(r"^function ([A-Za-z0-9_]+)\(", src[:m.start()], re.M):
            fn = f.group(1)
        out.setdefault(fn, 0)
        out[fn] += len(re.findall(r"\btarget\s*:", block))
        # Build 289: a tour may spread a shared step list into itself
        # (`...PROFILE_TIPS_289`) - those steps render too, so count them.
        for sp in re.findall(r"\.\.\.([A-Z0-9_]+)", block):
            out[fn] += shared_steps(src, sp)
    # Build 289: the three Profile tips are a shared constant, handed to
    # startSimpleTour on their own for anybody re-armed by tourRev 3.
    out["PROFILE_TIPS_289"] = shared_steps(src, "PROFILE_TIPS_289")
    # startMainMenuTour builds `steps` as a variable and passes it by name;
    # since build 321 the steps are mainMenuTourSteps(), which the meeting
    # with Nova (startNovaReturnTour) also uses, followed by the new tips.
    m = re.search(r"function mainMenuTourSteps\([^)]*\)\{(.*?)\n\}", src, re.S) \
        or re.search(r"function startMainMenuTour\(\)\{(.*?)\n\}", src, re.S)
    if m:
        # Build 327z15: the centred welcome step has no target but renders.
        out["startMainMenuTour"] = len(re.findall(r"\b(?:target|center)\s*:", m.group(1)))
        if "function startNovaReturnTour(" in src:
            # build 325: the meeting's tips are the new ones alone ("all the
            # walk through stuff on the main menu can be removed, only the
            # ones with the 'new' at the beginning") - so the main menu's
            # count only when the function still asks for them
            body = re.search(r"function startNovaReturnTour\([^)]*\)\{(.*?)\n\}", src, re.S)
            mm = out["startMainMenuTour"] if body and "mainMenuTourSteps" in body.group(1) else 0
            out["startNovaReturnTour"] = mm + shared_steps(src, "NOVA_NEW_TIPS_321")
    out.pop("mainMenuTourSteps", None)
    return out


def serve(src_path):
    so = socket.socket(); so.bind(("127.0.0.1", 0))
    port = so.getsockname()[1]; so.close()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)

    class Quiet(handler.func if hasattr(handler, "func") else http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port),
        functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def walk_tour(pg):
    """Click through a running tour, one step at a time."""
    steps = []
    for _ in range(16):
        st = pg.evaluate("""()=>{
          const tt=document.getElementById('tour-tooltip');
          if(!tt) return null;
          const r=tt.getBoundingClientRect();
          return { text:(document.getElementById('tour-text')||{}).textContent||'',
                   onScreen: r.top>=-1 && r.bottom<=innerHeight+1
                             && r.left>=-1 && r.right<=innerWidth+1 };}""")
        if not st:
            break
        steps.append(st)
        pg.evaluate("()=>document.getElementById('tour-next')?.click()")
        pg.wait_for_timeout(650)
    return steps


def main(argv):
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1].lower()

    src = open(INDEX, encoding="utf-8").read()
    declared = declared_steps(src)

    # Coverage: every startSimpleTour call site needs a scenario.
    sites = set(declared) - {None}
    covered = {s["source"] for s in SCENARIOS}
    missing = sorted(sites - covered)
    failures = []
    if missing:
        failures.append("tours with no scenario in this file: %s" % ", ".join(missing))
        print("MISSING SCENARIO for: %s" % ", ".join(missing))

    srv, port = serve(INDEX)
    checked = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for dev, w, h in DEVICES:
            print("\n%s  %dx%d" % (dev, w, h))
            for sc in SCENARIOS:
                if only and only not in sc["key"]:
                    continue
                want = declared.get(sc["source"], 0)
                if sc["setup"] is None:
                    print("  %-12s  skipped (%s), %d step(s) declared"
                          % (sc["key"], sc["note"], want))
                    continue
                seed = dict(SEED)
                if sc["flag"]:
                    seed[sc["flag"]] = False
                for other in SCENARIOS:
                    if other["flag"] and other["flag"] != sc["flag"]:
                        seed[other["flag"]] = True
                ctx = br.new_context(viewport={"width": w, "height": h})
                pg = ctx.new_page()
                pg.add_init_script(
                    "Object.defineProperty(navigator,'standalone',{get:()=>true});")
                pg.add_init_script(
                    "try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.drill.v1',%s)}catch(e){}"
                    % json.dumps(json.dumps(seed)))
                pg.goto("http://127.0.0.1:%d/index.html" % port)
                pg.wait_for_timeout(2000)
                pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
                # (384 full check) the steps the app hands over, counted at the call - a tour whose steps depend on the
                # account, the layout or the device (spread in, or one of two) is measured against what it really asked for
                pg.evaluate("()=>{ window.__tourAsked = null; const o = startSimpleTour; window.startSimpleTour = startSimpleTour ="
                            " function(steps){ if(window.__tourAsked === null) window.__tourAsked = (steps || []).length; return o.apply(this, arguments); }; }")
                pg.evaluate("()=>{%s}" % sc["setup"])
                pg.wait_for_timeout(sc.get("wait", 1500))
                if sc.get("min"):
                    # (r18) a tip that waits for a calm Home starts when Home is calm, not at a fixed second: the seed's owed
                    # character unlock plays for ~5-7s first (homeUnlockPlaying - state, not a node, so nothing to clear) and
                    # the app is right to wait for it. Allowed up to 25s more; a tip that never starts still reads 0 of 1.
                    try: pg.wait_for_selector("#tour-tooltip", timeout=25000)
                    except Exception: pass
                asked = pg.evaluate("()=>window.__tourAsked")
                if isinstance(asked, int) and asked > 0:
                    want = asked
                want = max(want, sc.get("min", 0))   # a tour that must show something fails if it never starts
                got = walk_tour(pg)
                ctx.close()
                checked += 1
                off = [i + 1 for i, s in enumerate(got) if not s["onScreen"]]
                bad = []
                if len(got) != want:
                    bad.append("%d of %d steps rendered - a target matched nothing"
                               % (len(got), want))
                if off:
                    bad.append("tooltip off-screen at step(s) %s"
                               % ", ".join(map(str, off)))
                if bad:
                    for b in bad:
                        failures.append("%s / %s: %s" % (dev, sc["key"], b))
                    print("  %-12s  FAIL  %s" % (sc["key"], "; ".join(bad)))
                else:
                    print("  %-12s  ok    %d/%d steps, all on screen"
                          % (sc["key"], len(got), want))
        br.close()
    srv.shutdown()

    print("\n%d tour run(s) checked across %d device(s)" % (checked, len(DEVICES)))
    if failures:
        print("\nFAILURES")
        for f in failures:
            print("  * %s" % f)
        return 1
    print("every declared step renders, and no tooltip leaves the viewport")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
