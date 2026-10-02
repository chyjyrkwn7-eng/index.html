#!/usr/bin/env python3
"""Does the app still DO the right thing? (Not: does it still look right.)

The sweep asks "is anything broken on this device", check-positions asks
"did it land where I meant it to", check-fixes asks "is this fix in effect
here", and check-sync asks "does this build still keep people's accounts".
None of them can see a splash that paints in the corner for 250ms, a swipe
that lands on nothing, a back link that renders an empty screen, or a badge
that is only awarded on some of the ways to earn it.

Every check here was written against a build where it FAILED. Run it with
--against on that build to watch it fail, which is the only thing that
makes a green run mean anything:

  python3 tools/check-behaviour.py
  python3 tools/check-behaviour.py --against /path/to/old-index.html

Chromium has no Firestore here (the CDN is blocked in the sandbox), so fbDb
is stubbed where a check needs it. Exits non-zero on any failure.
"""
import functools
import json
import http.server
import io
import os
import re
import socket
import sys
import threading
import time

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
SRC = (sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv
       else os.path.join(ROOT, "index.html"))

PHONE = ("iPhone 17 Pro Max", 440, 956)
TABLET = ("iPad Pro 11\"", 834, 1194)
DEVICES = [PHONE, TABLET]

FIRESTORE_STUB = """
  window.__stub = function(){
    fbDb = { collection: function(){ return { doc: function(){ return {
      set: function(){ return Promise.resolve(); },
      get: function(){ return Promise.resolve({ exists: false }); },
      update: function(){ return Promise.resolve(); },
      delete: function(){ return Promise.resolve(); }
    }; } }; } };
    onSnapshotResilient = function(ref, onNext){
      setTimeout(function(){ onNext({ forEach: function(){} }); }, 20);
      return function(){};
    };
  };
"""

# A launch where visualViewport reports a box 1.6x too big for the first
# 250ms: content centred inside an oversized box lands low and right, then
# snaps back, which is exactly how this was reported. The recorder samples
# EVERY frame from inside the page - sampling from Playwright missed the
# window on the faster device and reported a pass on a build with the bug.
LAUNCH_LIE = """
(() => {
  const t0 = Date.now();
  const bad = () => Date.now() - t0 < 250;
  const fake = {
    get width(){ return (bad() ? 1.6 : 1) * window.innerWidth; },
    get height(){ return (bad() ? 1.6 : 1) * window.innerHeight; },
    get offsetLeft(){ return 0; }, get offsetTop(){ return 0; },
    get scale(){ return 1; },
    addEventListener(){}, removeEventListener(){},
  };
  Object.defineProperty(window, 'visualViewport', { get: () => fake, configurable: true });
  window.__frames = [];
  (function rec(){
    const g = document.getElementById('splash-group');
    if(g){
      const r = g.getBoundingClientRect();
      window.__frames.push({ o: parseFloat(getComputedStyle(g).opacity),
        cx: r.left + r.width / 2, cy: r.top + r.height / 2,
        vw: window.innerWidth, vh: window.innerHeight });
    }
    if(window.__frames.length < 120) requestAnimationFrame(rec);
  })();
})();
"""

USED_ACCOUNT = (
    '{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,'
    '"leaderboardOptIn":true,"lastModified":1700000000000,"seenProfileTour":true,"tourRev":99,"rankMapFx244":true,'
    '"testHistory":[{"ts":1700000000000,"mode":"exam","label":"Practice test",'
    '"score":92,"total":25,"correct":23,"units":["1"],"answers":[]}],'
    '"lifetime":{"points":14820,"answered":5400,"correct":4980,"drillPlays":64,'
    '"examPlays":22,"gamePlays":9,"perfectTests":141,"currentStreak":23,'
    '"longestStreak":57}}')

BODY = INSET_RE.sub(lambda m: "0px", io.open(SRC, encoding="utf-8").read()) \
    .replace("let fbDb = null;", "let fbDb = null;" + FIRESTORE_STUB, 1)

_sock = socket.socket(); _sock.bind(("127.0.0.1", 0))
PORT = _sock.getsockname()[1]; _sock.close()


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


SERVER = http.server.ThreadingHTTPServer(
    ("127.0.0.1", PORT), functools.partial(_Quiet, directory=ROOT))
threading.Thread(target=SERVER.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

FAILURES = []


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -> " + str(detail)) if detail else ""))
    if not ok:
        FAILURES.append(name)


_BUILD_M = re.search(r'const APP_BUILD = "([^"]+)"', BODY)
SERVED_BUILD = _BUILD_M.group(1) if _BUILD_M else ""


def open_page(ctx):
    pg = ctx.new_page()
    pg.route("**/index.html", lambda r: r.fulfill(
        status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    # THE PAGE'S OWN BUILD, WHATEVER THE REPO'S version.json SAYS. Under
    # --against the page is an older build than the repo, so the update
    # check found a newer version.json, and with "force" set it reloaded
    # the page in the middle of a check - which is how build 234's
    # section 18 died with "execution context destroyed" against 233
    # instead of failing. No check reads version.json off the server
    # (the update checks hand checkForUpdate() one directly), so this
    # changes nothing on the current build.
    pg.route("**/version.json*", lambda r: r.fulfill(
        status=200, headers={"content-type": "application/json"},
        body='{"build":"%s","frameId":"","note":""}' % SERVED_BUILD))
    return pg


def booted(br, w, h, seed=None, init=None, touch=False, dpr=1):
    """A context on Home with the splash gone and Firestore stubbed."""
    ctx = br.new_context(viewport={"width": w, "height": h},
                         has_touch=touch, is_mobile=touch, device_scale_factor=dpr)
    if init:
        ctx.add_init_script(init)
    if seed:
        ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
                            "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % seed)
    pg = open_page(ctx)
    pg.goto(URL)
    pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    return ctx, pg


# --------------------------------------------------------------------------
def check_launch(br):
    print("\n1. the splash is centred from the first frame it is visible")
    for label, w, h in DEVICES:
        ctx = br.new_context(viewport={"width": w, "height": h})
        ctx.add_init_script(LAUNCH_LIE)
        pg = open_page(ctx)
        pg.goto(URL)
        pg.wait_for_timeout(1400)
        frames = pg.evaluate("() => window.__frames || []")
        worst, shown_off = 0, None
        for f in frames:
            off = max(abs(f["cx"] - f["vw"] / 2), abs(f["cy"] - f["vh"] / 2))
            if f["o"] > 0.02:
                worst = max(worst, off)
                if off > 4 and shown_off is None:
                    shown_off = (round(off), round(f["cx"]), round(f["cy"]))
        end = pg.evaluate("""() => {
          const g = document.getElementById('splash-group');
          if(!g) return null;
          const r = g.getBoundingClientRect();
          return { o: parseFloat(getComputedStyle(g).opacity),
                   cx: r.left + r.width/2, cy: r.top + r.height/2,
                   vw: window.innerWidth, vh: window.innerHeight };}""")
        end_off = (max(abs(end["cx"] - end["vw"] / 2), abs(end["cy"] - end["vh"] / 2))
                   if end else 999)
        check("%s never paints off-centre" % label, shown_off is None,
              shown_off or ("worst %dpx" % worst))
        check("%s settles centred and visible" % label,
              end is not None and end["o"] > 0.5 and end_off <= 4,
              "%dpx" % end_off)
        ctx.close()


# --------------------------------------------------------------------------
def _swipe(cdp, x0, y0, dx, dy=0, steps=8):
    """A real touch drag through CDP, not a synthetic DOM event."""
    cdp.send("Input.dispatchTouchEvent",
             {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
    for i in range(1, steps + 1):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [
            {"x": x0 + dx * i / steps, "y": y0 + dy * i / steps}]})
        time.sleep(0.012)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


ACTIVE_TAB = ("()=>{const b=document.querySelector('.panel .navsegment .iconbtn.active');"
              "return b ? b.textContent : null;}")


def check_swipe(br):
    print("\n2. a thumb swipe changes the top tab, anywhere on the screen")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        cdp = ctx.new_cdp_session(pg)
        for screen, show in [("Rankings", "()=>showRankings('week')"),
                             ("Profile", "()=>showProfile()")]:
            pg.evaluate(show)
            pg.wait_for_timeout(500)
            start = pg.evaluate(ACTIVE_TAB)
            # Low on the screen and with vertical drift, because that is
            # where a thumb actually lands: on a tablet the panel ends
            # halfway up, and swipes below it used to hit nothing.
            _swipe(cdp, w * 0.75, h * 0.45, -w * 0.5, 18)
            pg.wait_for_timeout(400)
            moved = pg.evaluate(ACTIVE_TAB)
            _swipe(cdp, w * 0.25, h * 0.45, w * 0.5, -18)
            pg.wait_for_timeout(400)
            back = pg.evaluate(ACTIVE_TAB)
            check("%s / %s swipes both ways" % (label, screen),
                  moved != start and back == start,
                  "%s -> %s -> %s" % (start, moved, back))
        # The listeners live on .wrap, which outlives the screen inside it.
        pg.evaluate("()=>showRankings('week')"); pg.wait_for_timeout(250)
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(250)
        pg.evaluate("()=>showRankings('week')"); pg.wait_for_timeout(400)
        # READ OFF THE SCREEN, never hard-coded. This asserted the
        # literal "Badges" and went red the day the boards became This
        # Week / Level / Hundos - failing the app for a change that was
        # asked for. What the check is actually about is "exactly one
        # step, not two", so it wants the SECOND tab whatever it is
        # called, and it now asks the app which that is.
        tabs = pg.evaluate("()=>[...document.querySelectorAll('.panel .navsegment .iconbtn')]"
                           ".map(b=>b.textContent)")
        _swipe(cdp, w * 0.75, h * 0.45, -w * 0.5, 18)
        pg.wait_for_timeout(400)
        once = pg.evaluate(ACTIVE_TAB)
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(400)
        _swipe(cdp, w * 0.75, h * 0.45, -w * 0.5, 18)
        pg.wait_for_timeout(400)
        still_home = pg.evaluate("()=>!!document.querySelector('.panel.home')")
        check("%s a second visit still steps exactly one tab" % label,
              len(tabs) > 1 and once == tabs[1], "%s of %s" % (once, tabs))
        check("%s leaving detaches the swipe" % label, still_home)
        """AND NOTHING INVISIBLE IS SITTING ON THE SWIPE LINE.
        The three checks above went red on a build where the chat dock's
        closed panel had grown taller than the swipe: it is a real,
        laid-out box, and `.chatdock-panel *{ pointer-events:auto }`
        kept its children hit-testable while the panel itself was
        pointer-events:none. The swipe checks catch that, but only ever
        after the fact and only for the two screens they drive - this
        asks the question directly, at the exact coordinates they use,
        so the next thing parked in that corner is caught by name."""
        pg.evaluate("()=>showRankings('week')"); pg.wait_for_timeout(300)
        at = pg.evaluate("""([x, y])=>{
          const el = document.elementFromPoint(x, y);
          if(!el) return { none:true };
          const dock = el.closest(".chatdock");
          return { tag: el.tagName, cls: String(el.className || "").slice(0, 60),
                   inDock: !!dock,
                   dockOpen: !!(document.getElementById("chatdock")||{classList:{contains:()=>false}})
                     .classList.contains("is-open") };}""", [w * 0.75, h * 0.45])
        check("%s nothing invisible sits on the swipe line" % label,
              not at.get("inDock"), at)
        ctx.close()


# --------------------------------------------------------------------------
VISIBLE = """()=>{
  const p = document.querySelector('#stage .panel');
  if(!p) return { panel:false };
  const vis = [...p.children].filter(c => !c.hidden && c.getBoundingClientRect().height > 0).length;
  return { panel:true, visibleChildren:vis, height:Math.round(p.getBoundingClientRect().height),
           activeTab:(document.querySelector('.panel .navsegment .iconbtn.active')||{}).textContent||null };}"""


def check_navigation(br):
    print("\n3. a back link lands on a screen with something on it")
    ctx, pg = booted(br, TABLET[1], TABLET[2], seed=USED_ACCOUNT)
    for label, show in [("test review -> Back to Profile", "()=>showTestReviewList()"),
                        ("calendar -> Back to Profile", "()=>showCalendar()")]:
        pg.evaluate(show)
        pg.wait_for_timeout(300)
        if not pg.query_selector(".back-link"):
            check(label, False, "no back link on the screen")
            continue
        pg.click(".back-link")
        pg.wait_for_timeout(400)
        st = pg.evaluate(VISIBLE)
        # A blank Profile is a real, shipped shape: the panel is there and
        # holds only its tab strip, ~112px tall, with no tab marked active.
        check(label, st["panel"] and st["visibleChildren"] >= 2
              and st["height"] > 200 and bool(st["activeTab"]), st)
    ctx.close()


# --------------------------------------------------------------------------
EARN_A_BADGE = """(a)=>{
  const { mode, nUnits, offset, flat, vroom } = a;
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const chosen = topics.slice(0, nUnits);
  /* EACH UNIT IS SET RELATIVE TO ITS OWN THRESHOLD. A badge costs what
     its unit is worth now, so two units in one run do not share a
     number - driving both from a literal 34 puts one of them past its
     own threshold before the run even starts, and the check then reports
     a badge that was already held as a badge that failed to arrive.
     `flat` is for the one case that genuinely is about an absolute
     count (a unit sitting at 10, nowhere near anything). */
  store.unitPerfects = {};
  chosen.forEach(t => {
    store.unitPerfects[t] = (flat != null) ? flat
      : Math.max(0, badgeThresholdFor(t) + offset);
  });
  store.pendingBadgeUnlocks = []; store.lifetime.perfectTests = 0;
  if(vroom){ beginVirtualRoomTest(chosen, null, null); }
  else {
    cfg.mode = mode; cfg.source = 'all'; cfg.units = chosen.slice();
    order = [].concat(...chosen.map(t => QUESTIONS.map((q,i) => [q,i])
      .filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i)));
    runTrackable = true; timedOut = false; runMode = mode; runLabel = null;
  }
  attempts = {}; picked = {}; timedOutSet = {};
  order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  summarize();
  return { queue:(store.pendingBadgeUnlocks||[]).slice(),
           banners:[...document.querySelectorAll('.badgebanner')].length,
           thresholds: chosen.map(t => t + ':' + badgeThresholdFor(t)),
           hundos: store.lifetime.perfectTests };}"""


def check_badges(br):
    """A badge is earned by every route to mastery, and only then.

    THE THRESHOLD IS READ OFF THE PAGE, NOT TYPED HERE. This used to
    drive a unit from a literal 34 to 35, and went red the day mastery
    moved to 30 hundos - at 34 the badge is already held, so crossing
    to 35 earns nothing and the check failed the app for being right.
    Same stale-literal trap this file has already hit three times with
    tab labels and board names. What the check is about is "one short,
    then exactly enough", so it asks the app what enough is.

    IT IS PER UNIT NOW, which is the same trap one level down. Reading a
    single BADGE_THRESHOLD off the page was still typing a literal once
    a badge started costing what its unit is worth: a two-unit run drove
    both units from one number, so one of them began the run already
    past its own threshold and the check reported a missing badge that
    was in fact a badge already held. The fixture asks
    badgeThresholdFor() per unit and the cases are written as "one
    short" and "already there" rather than as numbers at all.
    """
    ctx, pg = booted(br, TABLET[1], TABLET[2])
    print("\n4. a badge is earned by every route to mastery, and only then")
    cases = [
        ("drill, one unit, one short",
         {"mode": "drill", "nUnits": 1, "offset": -1, "flat": None, "vroom": False}, 1, 1),
        ("exam, two units, both one short",
         {"mode": "exam", "nUnits": 2, "offset": -1, "flat": None, "vroom": False}, 2, 2),
        # A Game run until build 283 retired Game mode.
        ("drill, one unit at 10, nowhere near",
         {"mode": "drill", "nUnits": 1, "offset": None, "flat": 10, "vroom": False}, 0, 0),
        ("Virtual Room, two units, both one short",
         {"mode": "exam", "nUnits": 2, "offset": -1, "flat": None, "vroom": True}, 2, 2),
        ("a unit already mastered",
         {"mode": "drill", "nUnits": 1, "offset": 0, "flat": None, "vroom": False}, 0, 0),
    ]
    # BUILD 213: a badge is celebrated ON THE RESULTS SCREEN - its row in
    # "Unlocked" and the badge-case cutscene - and no longer queued for a
    # cutscene on Home. So the queue must stay empty and the banner count
    # carries the "earned by every route, and only then" question alone.
    for label, args, want_queue, want_banners in cases:
        r = pg.evaluate(EARN_A_BADGE, args)
        check(label, len(r["queue"]) == 0 and r["banners"] == want_banners,
              "queued %s, %d banner(s), thresholds %s"
              % (r["queue"], r["banners"], r["thresholds"]))
    ctx.close()


DRAIN_POLL = """async ()=>{
  const t0 = performance.now();
  while(performance.now() - t0 < 6000){
    if(!document.getElementById('badge-cutscene') &&
       !(store.pendingBadgeUnlocks||[]).length) break;
    await new Promise(r=>setTimeout(r,50));
  }
  return { overlay:!!document.getElementById('badge-cutscene'),
           queue:(store.pendingBadgeUnlocks||[]).length,
           ms:Math.round(performance.now()-t0) };}"""


# --------------------------------------------------------------------------
def check_cutscene(br):
    print("\n5. queued badges play on the main menu, back to back")
    seed = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,'
            '"lastModified":1700000000000,"seenProfileTour":true,"tourRev":99,"rankMapFx244":true,'
            '"pendingBadgeUnlocks":["Professionalism and Ethics","TCOLE Rules"],'
            '"unitPerfects":{"Professionalism and Ethics":35,"TCOLE Rules":35},'
            '"lifetime":{"points":14820,"correct":880,"perfectTests":141}}')
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=seed)
        pg.evaluate("()=>showHome()")
        pg.wait_for_timeout(1500)
        first = pg.evaluate("""()=>{const o=document.getElementById('badge-cutscene');
          if(!o) return null; const a=o.querySelector('.badge-cutscene-art').getBoundingClientRect();
          return { name:(o.querySelector('.badge-cutscene-name')||{}).textContent,
                   inView: a.top >= 0 && a.bottom <= window.innerHeight,
                   queue:(store.pendingBadgeUnlocks||[]).length };}""")
        check("%s the first badge plays, on screen" % label,
              bool(first) and first["inView"] and first["queue"] == 1, first)
        # READ THE LENGTH OFF THE APP. This had 2600 typed into it, so
        # lengthening the cutscene - a deliberate change - turned the
        # gate red. Same principle as reading labels off the page
        # instead of quoting them: a gate must not carry its own copy
        # of a number the app owns.
        pg.wait_for_timeout(pg.evaluate("()=>BADGE_CUTSCENE_MS") + 150)
        second = pg.evaluate("""()=>{const o=document.getElementById('badge-cutscene');
          return o ? (o.querySelector('.badge-cutscene-name')||{}).textContent : null;}""")
        # NAMES THE UNIT, DOES NOT QUOTE THE WHOLE LINE. This asserted the
        # literal "TCOLE Rules" and went red the moment the cutscene started
        # calling a badge by its name ("TCOLE Rules badge") - the fifth time
        # in this file a check has encoded a copy decision and then failed the
        # app for being right. What matters is that the SECOND queued unit is
        # the one now on screen, so it tests for the unit inside whatever the
        # line says.
        check("%s the second follows it" % label,
              bool(second) and "TCOLE Rules" in second, second)
        # POLL FOR THE DRAIN, DO NOT SAMPLE AT ONE INSTANT. A fixed
        # 3200ms wait here summed to 7300ms, and the second badge's
        # overlay is removed at 7293ms on a phone and 7341ms on an
        # iPad - so this went red on the tablet and green on the phone
        # for a 40ms arithmetic coincidence, not for anything the app
        # did. The budget is still tight enough to fail a queue that
        # stalls or an overlay that sticks, which is the whole point;
        # it just is not measured against the cutscene's own total.
        # The budget is 6000ms against a real ~3200: headroom enough
        # that a rounding difference between two devices cannot decide
        # it, tight enough that it is still a budget. A queue that
        # stalls never drains at all, so no bound rescues that - which
        # is what this is actually here to catch, and ms is reported
        # so the true figure drifting is visible rather than silent.
        after = pg.evaluate(DRAIN_POLL)
        check("%s the queue drains and the overlay goes" % label,
              not after["overlay"] and after["queue"] == 0, after)
        ctx.close()


# --------------------------------------------------------------------------
def check_ranks(br):
    """The Ranks tab, which replaced the Mastery Ladder and Unlocks.

    Written against the build where it did not exist, so every check
    here fails on --against. The one that matters most is the fill: the
    whole point of the rewrite is that a rank part-way earned is
    part-way lit, and a clip-path that never moves off its CSS default
    looks identical to one that works until you measure it.
    """
    print("\n6. ranks: what you are, what you have, what is next")
    # THE FIXTURE IS DERIVED FROM TIER_UNLOCKS, NOT TYPED. It used to say
    # "level 23 (12,400 XP) and 4 badges reaches Veteran", which was true
    # of one curve and one threshold table and went red the day either
    # moved - the same stale-literal trap this file has now hit with tab
    # labels, board names and the badge threshold. What the section is
    # about is "hold Veteran, with Vanguard next", so it asks the app
    # what Veteran costs and seeds exactly that. Boots once to read the
    # numbers, then again with the seed built from them.
    ctx0, pg0 = booted(br, 834, 1194)
    spec = pg0.evaluate("""()=>{
      const V = TIER_UNLOCKS.veteran;
      let xp = 0;
      while(levelProgress(xp).level < V.level) xp += 25;
      const units = [...new Set(QUESTIONS.map(q => q.topic))].slice(0, V.badges);
      return { xp:xp, units:units, thr:BADGE_THRESHOLD,
               level:V.level, badges:V.badges };}""")
    ctx0.close()
    seed = json.dumps({
        "firstName": "Madison", "avatarChar": "ninja", "onboardingComplete": True,
        "lastModified": 1700000000000, "seenProfileTour": True, "tourRev": 99, "rankMapFx244": True,
        "unitPerfects": {u: spec["thr"] for u in spec["units"]},
        "lifetime": {"points": spec["xp"], "correct": 4980, "perfectTests": 141},
    })
    ctx, pg = booted(br, 834, 1194, seed=seed)
    got = pg.evaluate("""()=>({level:levelOf(store), badges:badgeCountOf(store),
                              rank:rankOf(store)})""")
    check("the seed holds the rank its numbers earn",
          got["level"] >= spec["level"] and got["badges"] == spec["badges"] and
          got["rank"] == "veteran", got)

    # Boundary behaviour, cheap and worth having: one short of a rank is
    # the rank below, and both halves have to be met.
    # Derived from the table for the same reason the seed is.
    edges = pg.evaluate("""()=>{
      const V = TIER_UNLOCKS.veteran, T = TIER_UNLOCKS.titan;
      return {
        exact: rankOfStats(V.level, V.badges, 0),
        levelShort: rankOfStats(V.level - 1, V.badges, 0),
        badgeShort: rankOfStats(V.level, V.badges - 1, 0),
        nothing: rankOfStats(1, 0, 0),
        top: rankOfStats(T.level, T.badges, 0),
        topShort: rankOfStats(T.level, T.badges - 1, 0) };}""")
    # The third argument is the old Secret Flare count. It is passed as 0
    # everywhere now and the top rank reaches anyway, which is the whole
    # point of the check: nothing gates on it any more.
    check("a rank needs both halves of its rule, and only those two",
          edges["exact"] == "veteran" and edges["levelShort"] == "ranger" and
          edges["badgeShort"] == "ranger" and edges["nothing"] is None and
          edges["top"] == "titan" and edges["topShort"] == "elite", edges)

    # RANK AND BADGES ARE THEIR OWN BOTTOM TAB NOW (build 219) - "a new
    # bottom tab for rank/badges with Rank default". Profile keeps two
    # tabs. The invariant is the same one this used to hold for four:
    # the swipe order carries the same tabs as the buttons, on both
    # screens, so a thumb swipe never skips one.
    pg.evaluate("()=>showProfile()")
    pg.wait_for_timeout(1200)
    ptabs = pg.evaluate("""()=>({
      rendered: [...document.querySelectorAll('.profiletabs .iconbtn')].map(b=>b.textContent),
      swipe: PROFILE_TABS.slice(), bottom: !!document.querySelector('#bottomtab-ranks')})""")
    check("Profile is two tabs, Profile first, and swipes in the same order",
          len(ptabs["rendered"]) == 2 and ptabs["rendered"][:1] == ["Profile"] and
          len(ptabs["swipe"]) == 2, ptabs)
    # Build 284 took the Progress tab back off the bar: "let's remove the
    # progress tab and put them within profile" - the rank and badge rows
    # on the Profile card open it (check_b284).
    check("the tab bar carries no Progress tab (build 284)", not ptabs["bottom"], ptabs)
    pg.evaluate("()=>showProfile('ranks')")
    pg.wait_for_timeout(1500)
    tabs = pg.evaluate("""()=>({
      screen: !!document.querySelector('.screen-ranks'),
      rendered: [...document.querySelectorAll('.profiletabs .iconbtn')].map(b=>b.textContent),
      active: (document.querySelector('.profiletabs .iconbtn.active')||{}).textContent,
      swipe: RANKS_TABS.slice(),
      tabLit: document.querySelector('#bottomtab-profile').classList.contains('active')})""")
    check("an old link to Profile's rank tab lands on the Ranks screen, Rank showing",
          tabs["screen"] and len(tabs["rendered"]) == 2 and tabs["active"] == tabs["rendered"][0] and
          tabs["swipe"] == ["ranks", "badges"], tabs)
    check("Profile stays lit on the bar while the climb is open from it (build 284)", tabs["tabLit"], tabs)

    # THE ROAD MAP. Build 232 turned it over: Iron at the top, Supernova
    # at the bottom, so the DOM order IS the climbing order now.
    cards = pg.evaluate("""()=>[...document.querySelectorAll('.rankmap-stop')].map(c=>({
      name:c.querySelector('.rankmap-name').textContent,
      state:(c.className.match(/is-(reached|here|next|locked)/g)||[]).join(' '),
      chip:c.querySelector('.rankmap-state').textContent,
      meter:!!c.querySelector('.rankmap-meter'),
      you:!!c.querySelector('.rankmap-you'),
      rewards:c.querySelectorAll('.rankmap-gift').length,
      charGift:!!c.querySelector('.rankmap-gift.is-char')}))""")
    # Build 244 changed the names: Bronze first, Silver second, Iron gone.
    check("seven ranks, named as ranks and not as flares",
          [c["name"] for c in cards] ==
          ["Bronze", "Silver", "Gold", "Platinum", "Sapphire", "Amethyst", "Supernova"],
          [c["name"] for c in cards])
    check("every stop says which of the states it is in",
          [c["chip"] for c in cards] ==
          ["Reached", "Reached", "You are here", "Up next", "Locked", "Locked", "Locked"],
          [c["chip"] for c in cards])
    # Build 255: no avatar on the road map at all ("your avatar being on
    # the current rank road map, remove that"); the stop still says here.
    check("no avatar stands on the road map; the rank you hold still says so",
          [i for i, c in enumerate(cards) if c["you"]] == [] and "here" in cards[2]["state"],
          cards)
    check("only the rank you are climbing to carries a meter",
          [c["meter"] for c in cards] == [False, False, False, True, False, False, False],
          [c["meter"] for c in cards])
    # Theme and flare on every rank; Gold and up hand over a character
    # too, and the top three a banner (a chip again since build 236).
    # Build 235: Gold hands over the Pharaoh, so it is the top FIVE now.
    check("every rank lists what it hands over, top five include the character",
          # Build 236: the top three's banners are chips again, so they count.
          # Build 244: the second rank hands over Lunar, so the rank
          # characters start one rank lower - six of them.
          [c["rewards"] for c in cards] == [2, 3, 3, 3, 4, 4, 4] and
          [c["charGift"] for c in cards] == [False] + [True] * 6,
          [c["rewards"] for c in cards])
    # THE SHAPE, NOT THE COUNT. This asserted `count == 12` and that
    # every character without an `unlock` is free, and it went red the
    # day four FEAT characters were added - which is the app being
    # right, not wrong. Same trap this file has now watched take out
    # four separate checks: a gate that encodes a DECISION fails the
    # moment the decision changes.
    # What is actually true regardless of how many there are: the top
    # four ranks each hand over a character, a rank you have not reached
    # keeps its locked, and a character with neither `unlock` nor `feat`
    # is free to everybody.
    chars = pg.evaluate("""()=>({
      count: AVATAR_CHARACTERS.length,
      gated: AVATAR_CHARACTERS.filter(c=>c.unlock).map(c=>c.unlock),
      lockedGated: AVATAR_CHARACTERS.filter(c=>c.unlock).map(c=>isLockedCharacter(c.id)),
      heldGated: AVATAR_CHARACTERS.filter(c=>c.unlock).map(c=>tierColorUnlocked(c.unlock)),
      /* build 243: a `legacy` character (the Robot) is neither free nor
         earnable - it is kept by whoever held it - so it is not here. */
      lockedFree: AVATAR_CHARACTERS.filter(c=>!c.unlock && !c.feat && !c.legacy)
                    .map(c=>isLockedCharacter(c.id)),
      featLocked: AVATAR_CHARACTERS.filter(c=>c.feat).map(c=>isLockedCharacter(c.id))})""")
    check("six characters gated on the top six ranks (Lunar on the second since build 244)",
          chars["gated"] == ["ranger", "veteran", "vanguard", "adept", "elite", "titan"], chars)
    # The seed holds Gold (so the Pharaoh is its own since build 235) and has done nothing towards any feat, so
    # none of the eight earned characters is reachable and none of the
    # free ones is ever locked.
    check("a rank you have not reached keeps its character locked",
          all(l == (not h) for l, h in zip(chars["lockedGated"], chars["heldGated"]))
          and not all(chars["heldGated"]) and not any(chars["lockedFree"]), chars)
    check("a feat you have not done keeps its character locked",
          bool(chars["featLocked"]) and all(chars["featLocked"]), chars["featLocked"])

    # A locked rank still shows its colour. Four of the seven used to be
    # redrawn in grey, so you could not see what you were heading for.
    hues = pg.evaluate("""()=>[...document.querySelectorAll('.rankmap-stop')].map(c=>
      c.style.getPropertyValue('--rank-color').trim())""")
    check("every rank carries its own colour, reached or not",
          len(set(hues)) == 7 and all(h.startswith("#") for h in hues), hues)

    # ONE STOP PER ROW, and on a tablet the cards alternate sides of the
    # road - which is what makes it a road rather than a list.
    lay = pg.evaluate("""()=>{const cs=[...document.querySelectorAll('.rankmap-stop')];
      const tops=cs.map(c=>Math.round(c.getBoundingClientRect().top));
      const side=c=>{const n=c.querySelector('.rankmap-node').getBoundingClientRect(),
        k=c.querySelector('.rankmap-card').getBoundingClientRect(); return k.left>=n.right-1?'R':'L';};
      return {distinctRows:new Set(tops).size===cs.length, sides:cs.map(side).join('')};}""")
    check("one stop per row, cards alternating sides of the road on a tablet",
          lay["distinctRows"] and "LR" in lay["sides"] and "RL" in lay["sides"], lay)

    # SEVEN DIFFERENT MARKS, not one mark at seven sizes - and not the
    # chevron set that replaced it either ("I'm not a fan of the iron
    # bronze silver icons after all"). Since build 250 they are, bottom to
    # top: a nebula, a protostar, a sun with a world, a binary, a spiral
    # galaxy, a black hole with jets, and the Supernova with a dark heart -
    # and it has to climb (section 34). The check is structural rather than a look: no two
    # ranks produce the same shape signature, and the top one is the most
    # elaborate thing in the set.
    shapes = pg.evaluate("""()=>{
      const out={};
      TIER_ORDER_FULL.forEach(k=>{
        const svg=buildRankEmblemSVG(k);
        const ds=[...svg.querySelectorAll('path')].map(p=>p.getAttribute('d')||'');
        out[k]={n:ds.length, sig:ds.join('|').length};
      });
      return out;}""")
    order = ["rookie", "ranger", "veteran", "vanguard", "adept", "elite", "titan"]
    check("no two ranks draw the same thing",
          len({shapes[k]["sig"] for k in order}) == 7,
          {k: shapes[k]["sig"] for k in order})
    check("the top rank is the busiest mark in the set",
          shapes["titan"]["n"] > max(shapes[k]["n"] for k in order[:6]),
          {k: shapes[k]["n"] for k in order})

    # The Secret Flares are gone: the hunt, the Eclipse colour it
    # unlocked, and the clause it put on the top rank's requirement.
    # "The mystery flares should be scrapped and moved. That means the
    # requirement they have, the theme, the unlock."
    gone = pg.evaluate("""()=>({
      box: !!document.querySelector('.ranks-tab .unlock-row'),
      anyMention: /Secret Flare/i.test(document.querySelector('.ranks-tab').textContent),
      topReq: document.querySelector('.rankmap-req').textContent,
      eclipse: ACCENTS.indexOf('mystery') !== -1
    })""")
    check("no unlock box and nothing on the tab mentions a Secret Flare",
          not gone["box"] and not gone["anyMention"], gone)
    check("the top rank asks for levels and badges and nothing else",
          "Secret" not in gone["topReq"] and "Level" in gone["topReq"], gone["topReq"])
    check("the Eclipse colour is off the list of themes",
          not gone["eclipse"], gone)
    ctx.close()
    ctx2, pg2 = booted(br, 393, 852, seed=seed)
    pg2.evaluate("()=>showProfile('ranks')")
    pg2.wait_for_timeout(1200)
    lay2 = pg2.evaluate("""()=>{const cs=[...document.querySelectorAll('.rankmap-stop')];
      const tops=cs.map(c=>Math.round(c.getBoundingClientRect().top));
      /* Build 235: the road runs up the middle on a phone too, cards
         either side of it, alternating - "make that the same look the
         iPhone gets". Each card clears its node on its own side. */
      const beside=cs.every((c,i)=>{ const cr=c.querySelector('.rankmap-card').getBoundingClientRect(),
                                         nr=c.querySelector('.rankmap-node').getBoundingClientRect();
                                     return c.classList.contains('is-left') ? cr.right <= nr.left + 1 : cr.left >= nr.right - 1; });
      const over=cs.some(c=>c.getBoundingClientRect().right > innerWidth + 1);
      return {distinctRows:new Set(tops).size===cs.length, beside, over};}""")
    check("one stop per row on a phone, the road up the middle with cards either side, nothing off the edge",
          lay2["distinctRows"] and lay2["beside"] and not lay2["over"], lay2)
    ctx2.close()
    ctx, pg = booted(br, 834, 1194, seed=seed)
    pg.evaluate("()=>showProfile('ranks')")
    pg.wait_for_timeout(1200)

    # The rank has to show up where people are listed, or it is a tab
    # nobody else ever sees.
    # The numbers fed in come from the table, and so does the name
    # expected back - (34, 6) was Gold under one threshold table and
    # Silver under the next. What is being checked is that a row shows
    # THE RANK THOSE NUMBERS EARN, which is a different statement from
    # "shows Gold".
    row = pg.evaluate("""()=>{const V=TIER_UNLOCKS.vanguard;
      const a=document.createElement('span');
      a.className='lb-avatar'; a.appendChild(buildAvatarCharSVGSafe('ninja'));
      decorateAvatar(a, V.level, V.badges, 0);
      const un=document.createElement('span'); un.className='lb-avatar';
      decorateAvatar(un, 1, 0, 0);
      return {rank:(a.querySelector('.lb-rankmark')||{}).title,
              want:RANK_DISPLAY_NAME.vanguard,
              level:!!a.querySelector('.vroom-level'),
              unranked:!un.querySelector('.lb-rankmark'),
              unrankedExtras:un.childNodes.length};}""")
    # ---- REVERSED IN BUILD 241 ----
    # This asserted the rank coin was on the character. "The whole 'rank
    # icon on the top of your avatar' thing just needs to go away from the
    # app entirely ... The ranking with the words is enough." So the
    # helper now decorates nothing, for anybody, at any rank.
    check("no rank coin on a character, whatever the rank", not row["rank"], row)
    # The small blue level number beside the character was asked for,
    # built, and then asked against. Two marks on one 42px character is
    # one too many, and a board that ranks on the number is already
    # printing it.
    check("no level number beside the character", not row["level"], row)
    check("somebody below the first rank gets nothing at all",
          row["unranked"] and row["unrankedExtras"] == 0, row)

    # And on the REAL screen, not just through the helper. The three
    # Rankings boards had a second row builder of their own with its own
    # level chip, so when the number came off everywhere it stayed on the
    # screen it is most visible on - and the rank emblem never arrived
    # there at all. Testing the builder alone is what missed it.
    # With no network the board carries exactly the row liveEntries()
    # synthesises for you, which is one row and enough to check.
    pg.evaluate("()=>{ store.leaderboardOptIn = true; syncCode = 'MADI-0001';"
                "      document.getElementById('bottomtab-rewards').click(); }")
    pg.wait_for_timeout(1200)
    board = pg.evaluate("""()=>{
      const rows = [...document.querySelectorAll('.rank-row')];
      const overall = [...document.querySelectorAll('.navsegment .iconbtn')]
        .find(b => /overall/i.test(b.textContent));
      if(overall) overall.click();
      const after = [...document.querySelectorAll('.rank-row')];
      return {rows:rows.length,
              marks:rows.filter(r=>r.querySelector('.lb-rankmark')).length,
              levelChips:document.querySelectorAll('.rank-level').length,
              hasOverall: !!overall,
              statLines: after.map(r => (r.querySelector('.rank-stat')||{}).textContent || ""),
              heads: [...document.querySelectorAll('.rank-row-head .rank-col-head')].map(e => e.textContent.trim()),
              cols: after.filter(r => !r.classList.contains('rank-row-head')).map(r => {
                const c = r.querySelector('.rank-cols');
                return c ? [...c.children].map(x => x.textContent.trim()) : null; })};}""")
    # ---- THIS ENCODED A DECISION, AND THE DECISION REVERSED ----
    # It asserted that every rankings row carries the rank emblem, which
    # was itself a fix: the boards had their own row markup and never
    # called decorateAvatar, so the emblem never arrived there. Asked
    # against now - "remove the rank icon that's showing on the
    # character while looking at character in the leaderboard" - so the
    # emblem is off these rows and stays on the lobby and the results
    # screen, where a character is drawn big enough to carry it.
    # What is worth holding is the half that was never about the emblem:
    # a row carries NO level chip, and the rank is still on the row -
    # in words, on the Overall board, which is where it now lives.
    check("a rankings row carries neither a level chip nor a rank coin",
          board["rows"] >= 1 and board["marks"] == 0
          and board["levelChips"] == 0, board)
    # THE RANK DID NOT SIMPLY VANISH. Overall names it, so somebody's
    # rank is still readable from the board that ranks on it.
    # AND THEN IT MOVED AGAIN, into columns (build 201): "they should be
    # in their own columns, the rank, level, and badges". The rank is a
    # cell now, not a phrase in a stat line, so this asserts the SHAPE -
    # a three-label header and three filled cells on every row - rather
    # than any one label, which is the lesson every other stale check in
    # this file already paid for.
    check("and the Overall board still says the rank, in its own column",
          board["hasOverall"] and len(board["heads"]) == 3
          and len(board["cols"]) >= 1
          and all(c is not None and len(c) == 3 and all(c) for c in board["cols"]),
          {"heads": board["heads"], "cols": board["cols"][:3]})
    ctx.close()
    ctx.close()


def check_review_reach(br):
    """Every question is REACHABLE, not merely present.

    .cal-month-body is overflow:hidden with a max-height, because that
    pair is what animates the slide open. On the calendar the cap was
    never near; on Answer Review one unit is 14,000px of questions
    against a 2,000px cap, so six sevenths of the screen was clipped -
    and a page cannot scroll to what a box has already clipped away.
    Reported as "it's not scrollable, it doesn't let you scroll down to
    look at all the questions and stuff."

    Counting the questions in the DOM would have passed on the broken
    build: all 29 were there, and 24 of them were invisible. So this
    scrolls to the bottom and asks whether the LAST one is on screen.
    """
    print("\n7. the answer review can be scrolled to its last question")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        # One unit, which renders expanded with no toggle at all.
        pg.evaluate("()=>{ showAnswerReview([topicsIn(QUESTIONS)[0]]); }")
        pg.wait_for_timeout(1100)
        box = pg.evaluate("""()=>{
          const b = document.querySelector('.cal-month-body');
          const qs = document.querySelectorAll('.review-question');
          return b ? { n: qs.length, h: Math.round(b.getBoundingClientRect().height),
                       cap: getComputedStyle(b).maxHeight,
                       clip: getComputedStyle(b).overflow } : null;}""")
        # behavior:"instant" deliberately: smooth scrolling is on by
        # default and a 14,000px smooth scroll is still travelling when
        # the next line measures, which reads exactly like a page that
        # will not scroll. A harness must not invent the bug it checks.
        pg.evaluate("()=>window.scrollTo({top: document.documentElement.scrollHeight,"
                    " behavior: 'instant'})")
        pg.wait_for_timeout(450)
        last = pg.evaluate("""()=>{
          const qs = document.querySelectorAll('.review-question');
          const el = qs[qs.length - 1];
          if(!el) return null;
          const r = el.getBoundingClientRect();
          return { on: r.top < innerHeight && r.bottom > 0, top: Math.round(r.top) };}""")
        check("%s the section is not capped" % label,
              bool(box) and box["cap"] == "none", box)
        check("%s the last question can be scrolled to" % label,
              bool(last) and last["on"], last)
        ctx.close()


def _answer(pg):
    """Answer the question on screen correctly, whatever it is."""
    pg.evaluate("""()=>{ const all=[...document.querySelectorAll('.choice')];
      const qi=order[pos], oo=optionOrder(qi);
      all[oo.indexOf(QUESTIONS[qi].answer)].click(); }""")


def check_update_and_cards(br):
    """Two decisions that are invisible until somebody hits them.

    1. A FORCED UPDATE MUST NOT EAT THE RESULTS SCREEN. summarize()
       clears testInProgress and THEN draws the results, so the retry
       fired a tick later landed on the one screen anybody actually
       wants to read - "people aren't able to see test result stats
       because the updates immediately start". Waiting for the test to
       END was never the condition; waiting for them to LEAVE it is.
    2. AN EARNED BADGE IS THE WHOLE STATUS. A full bar reading 35 / 35
       beside an earned badge is the same fact twice, and a bar is an
       instrument for something you are still working towards.

    Both were written against the build they failed on.
    """
    print("\n9. the forced update waits, and a mastered card is just its badge")
    ctx, pg = booted(br, PHONE[1], PHONE[2], seed=USED_ACCOUNT)
    got = pg.evaluate("""()=>{
      const out = {};
      /* THE DECISION CHANGED, SO THIS CHECK HAD TO BE RE-READ. It used
         to assert that every screen but Welcome and Home BLOCKED the
         update - which was the rule, and which behaved as "anybody
         sitting in Settings or on their Profile never updates at all".
         Asked for directly: push it through unless they are in a test,
         on the results, or in a retake. So the shape being asserted is
         now which states are worth protecting, not which screen is
         Home. */
      out.home = forcedUpdateBlocked();
      showAppearance();
      out.settings = forcedUpdateBlocked();
      showProfile();
      out.profile = forcedUpdateBlocked();
      showHome();
      out.backHome = forcedUpdateBlocked();

      /* A question in progress, however you detect it. */
      document.body.classList.add('has-active-question');
      out.inTest = forcedUpdateBlocked();
      document.body.classList.remove('has-active-question');

      /* Reviewing answers, and a retake being set up. */
      const mkScreen = (cls) => { const p = document.createElement('section');
        p.className = 'panel ' + cls; stage.replaceChildren(p); };
      mkScreen('screen-answerreview'); out.review = forcedUpdateBlocked();
      mkScreen('screen-setup');        out.retake = forcedUpdateBlocked();
      mkScreen('screen-profile');
      const spl = document.createElement('div'); spl.id = 'splashscreen';
      document.body.appendChild(spl);
      out.splash = forcedUpdateBlocked();
      spl.remove();
      /* FAST, and the number is the point: asked for "as fast as
         possible at a rate that makes sense". A minute was too slow to
         feel like the update was live. */
      out.polls = (typeof UPDATE_POLL_MS === 'number') && UPDATE_POLL_MS <= 20000;

      /* THE RESULTS SCREEN IS A FEW SECONDS OF GRACE, NOT A BLOCK.
         Waiting for Home alone meant somebody who goes from one test
         straight into another never updated at all. */
      const panel = document.createElement('section');
      panel.className = 'panel'; panel.dataset.screen = 'results';
      stage.replaceChildren(panel);
      resultsShownAt = Date.now();
      out.justFinished = forcedUpdateBlocked();
      resultsShownAt = Date.now() - (UPDATE_REVIEW_MS + 500);
      out.afterReview = forcedUpdateBlocked();
      out.window = UPDATE_REVIEW_MS;

      const all = topicsIn(QUESTIONS);
      store.unitPerfects = store.unitPerfects || {};
      store.unitPerfects[all[0]] = BADGE_THRESHOLD + 7;
      store.unitPerfects[all[1]] = 4;
      const mk = n => { const row = document.createElement('label');
        row.className = 'pick'; appendUnitProgress(row, n); return row; };
      const done = mk(all[0]), going = mk(all[1]);
      out.badge = !!done.querySelector('.pick-badge.earned');
      out.masteredBar = !!done.querySelector('.pick-barrow');
      out.masteredCount = !!done.querySelector('.pick-bar-count');
      out.goingBar = !!going.querySelector('.pick-barrow');
      return out;}""")
    check("a forced update may go while they are on Home",
          got["home"] is False, got["home"])
    check("and in Settings, rather than waiting for them to wander back",
          got["settings"] is False, got)
    check("and on Profile", got["profile"] is False, got)
    check("but never over a question in progress", got["inTest"] is True, got)
    check("nor while they are reviewing answers", got["review"] is True, got)
    check("nor while a retake is being set up", got["retake"] is True, got)
    check("nor on top of a loading screen", got["splash"] is True, got)
    check("and it re-checks at least every twenty seconds",
          got["polls"] is True, got)
    # The results screen is not Home, and neither is anything else.
    check("and it goes the moment they are back on Home",
          got["backHome"] is False, got["backHome"])
    check("a mastered unit keeps its badge", got["badge"] is True, got["badge"])
    check("and drops the bar and the count",
          got["masteredBar"] is False and got["masteredCount"] is False,
          {"bar": got["masteredBar"], "count": got["masteredCount"]})
    # The bar is still there on a unit somebody is still working on -
    # this is not "take the bar off unit cards".
    check("an unmastered one still has its bar", got["goingBar"] is True, got["goingBar"])
    # "give it a few seconds to review the stuff then push it"
    check("the results screen gets its reading time first",
          got["justFinished"] is True, got["justFinished"])
    check("and the update goes once that window is up",
          got["afterReview"] is False, got["afterReview"])
    check("the window is seconds, not minutes",
          3000 <= got["window"] <= 30000, got["window"])

    """WHICH PATH A NEW BUILD TAKES, AND IT IS NOT THE BANNER ANY MORE.
    *"Let's just keep it so that it forces updates on everyone, no more
    update banner, unless it's the safari one."* So a version.json with
    no `force` field at all must still push, and only an explicit
    `"force": false` may ask for the banner back - the flag is inverted
    rather than deleted, so turning the banner on for one release stays
    a one-line change in a sidecar file.
    Driven through the real decision rather than by reading the
    constant: the check hands checkForUpdate() a version.json and looks
    at which of the two things the app then does."""
    paths = pg.evaluate("""async ()=>{
      const out = {};
      const run = async (body) => {
        forcedUpdateInfo = null; forcedUpdateStarted = false; pendingNotice = null;
        document.querySelectorAll('.update-banner, #pushing-update').forEach(n => n.remove());
        try{ localStorage.removeItem('class26e.forced.v1'); }catch(e){}
        try{ localStorage.removeItem('class26e.update.dismissed'); }catch(e){}
        const real = window.fetch;
        window.fetch = () => Promise.resolve({ ok:true, json: () => Promise.resolve(body) });
        lastUpdateCheck = 0;
        await checkForUpdate(true);
        window.fetch = real;
        await new Promise(r => setTimeout(r, 60));
        return { pushed: !!(forcedUpdateStarted || document.getElementById('pushing-update')),
                 banner: !!(pendingNotice && pendingNotice.kind === 'update') };
      };
      showHome();
      const newBuild = APP_BUILD + '-next';
      out.noFlag   = await run({ build:newBuild });
      out.flagTrue = await run({ build:newBuild, force:true });
      out.flagFalse= await run({ build:newBuild, force:false });
      out.sameBuild= await run({ build:APP_BUILD });
      return out;}""")
    check("a new build with no force field is pushed anyway",
          paths["noFlag"]["pushed"] is True and paths["noFlag"]["banner"] is False,
          paths["noFlag"])
    check("and so is an explicit force:true",
          paths["flagTrue"]["pushed"] is True, paths["flagTrue"])
    """The escape hatch, and the one path that reaches the banner on
    purpose. It is also what a device falls back to once the forced
    push has failed its three tries, which is the reason the banner
    code is still here at all."""
    check("only force:false asks for the banner back",
          paths["flagFalse"]["pushed"] is False and paths["flagFalse"]["banner"] is True,
          paths["flagFalse"])
    check("and the same build does neither",
          paths["sameBuild"]["pushed"] is False and paths["sameBuild"]["banner"] is False,
          paths["sameBuild"])
    ctx.close()


def check_slide(br):
    """The next question FADES THROUGH, and nothing else moves after it.

    Reported as "the lag it has when it goes to the next question was
    so bad the screen was like glitching", and it was two defects in
    one function, both invisible to a frame-drop count.

    1. advanceWithSlide() clones the outgoing question and animates the
       clone away, but the clone was still running screen-fade-in - a
       translateY settle - and a running animation beats a transition
       on the SAME property. So the clone ignored the transition: it
       sat there, moved a pixel, and snapped away at the end. .panel
       has a fully transparent background, so the incoming question
       arrived UNDERNEATH it and both were legible at once.
       THE ASSERTION IS ABOUT OPACITY, NOT GEOMETRY. It used to check
       that the two boxes never overlap horizontally, which was the
       right test for a full-width slide and is meaningless now that
       the transition is a fade-through - the two panels sit in almost
       exactly the same place on purpose. What has to stay true is the
       thing the geometry was standing in for: the two questions are
       never READABLE at the same time. A gate has to track the
       decision it guards, or it fails the app for being right.

    2. The cleanup then set incoming.style.animation = "", which does
       not mean "it already ran, leave it" - it un-suppresses the CSS
       rule and an animation suppressed for its whole duration starts
       from frame zero at that moment. The question finished sliding in
       and then jumped 6px down and settled again. So this also asserts
       nothing is animating the panel once the slide is over.

    setTimeout is stubbed for the slide's own cleanup call - matched by
    a RANGE, not the literal 215, because that number is tuned with the
    transition duration and a gate that hardcodes it silently stops
    holding the clone the moment somebody retunes the animation, which
    is exactly when this check matters most. It already went stale once
    when the duration moved to .19s. Everything about the slide itself is the app's own code.
    """
    print("\n8. the next question fades through cleanly, and then stops")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        pg.evaluate("""()=>{ cfg.units=[topicsIn(QUESTIONS)[0]]; cfg.mode='drill';
          cfg.size=12; cfg.source='all';
          const u=topicsIn(QUESTIONS)[0], idx=[];
          QUESTIONS.forEach((q,i)=>{ if(q.topic===u && idx.length<12) idx.push(i); });
          beginRun(idx); }""")
        pg.wait_for_selector(".choice", timeout=20000)
        pg.wait_for_timeout(700)

        # A real slide first, with nothing stubbed, so the app's own
        # cleanup runs and the flag it sets is cleared normally.
        _answer(pg)
        pg.wait_for_timeout(500)
        pg.evaluate("()=>advanceWithSlide()")
        pg.wait_for_timeout(800)
        after = pg.evaluate("""()=>{
          const p=document.querySelector('#stage > .panel');
          if(!p) return null;
          const s=getComputedStyle(p);
          return { clone: !!document.querySelector('body > .panel'),
                   anim: s.animationName, transform: s.transform }; }""")
        check("%s the arriving question does not re-run its mount animation" % label,
              bool(after) and not after["clone"] and after["anim"] == "none"
              and after["transform"] in ("none", "matrix(1, 0, 0, 1, 0, 0)"), after)

        # Then the geometry, which needs the clone held past its own
        # cleanup. THE STUB LEAVES slideTransitionInFlight SET - the
        # flag is cleared in the timeout that was skipped - so this has
        # to be the LAST thing done in this context, or the next
        # advanceWithSlide() returns early and the check that follows
        # measures an ordinary mount and calls it a slide. It did.
        _answer(pg)
        pg.wait_for_timeout(500)
        worst = pg.evaluate("""async ()=>{
          const st=window.setTimeout;
          window.setTimeout=function(fn,ms){ return (ms>=150&&ms<=400) ? 0 : st(fn,ms); };
          advanceWithSlide();
          window.setTimeout=st;
          let worst=0, frames=0, sawOut=false, sawIn=false;
          for(let i=0;i<50;i++){
            await new Promise(r=>requestAnimationFrame(r));
            const c=document.querySelector('body > .panel');
            const n=document.querySelector('#stage > .panel');
            if(!c||!n) break;
            const oc=+getComputedStyle(c).opacity, on=+getComputedStyle(n).opacity;
            if(oc > .9) sawOut = true;
            if(on > .9) sawIn = true;
            worst=Math.max(worst, Math.min(oc,on));
            frames++;
            if(sawIn && oc < .01) break;
          }
          return { worst: +worst.toFixed(2), frames, sawOut, sawIn }; }""")
        check("%s the two questions are never readable at once" % label,
              worst["frames"] > 3 and worst["sawOut"] and worst["sawIn"]
              and worst["worst"] <= 0.15, worst)
        ctx.close()


def check_b218(br):
    """Build 218: what Madison re-asked for off Home, Settings and the boards.

    Every check here was written against build 216, where it fails."""
    print("\n10. build 218: tabs start at the top, Settings, the boards, Home's motion")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    # "If I'm at the bottom of the settings tab and move to another tab,
    # the new tab starts at the bottom and then moves to the top."
    pg.evaluate("()=>{ theme.smoothScroll = true; try{ applyTheme(); }catch(e){} showAppearance(); }")
    pg.wait_for_timeout(700)
    pg.evaluate("()=>window.scrollTo({top: 99999, behavior: 'instant'})")
    pg.wait_for_timeout(300)
    ys = pg.evaluate("""()=>new Promise(res=>{ const ys=[]; document.getElementById('bottomtab-profile').click();
      let n=0; (function f(){ ys.push(Math.round(scrollY)); if(++n<8) requestAnimationFrame(f); else res(ys); })(); })""")
    check("a tab switched to from the bottom of another starts at the top", ys[2] == 0, ys)
    # Settings: two buttons to a row, and the sync code in a card.
    pg.evaluate("()=>{ showAppearance(); }")
    pg.wait_for_timeout(500)
    rows = pg.evaluate("""()=>{ const top=t=>{ const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()===t); return b?Math.round(b.getBoundingClientRect().top):null; };
      return { upd: top('Check for update'), bug: top('Report a bug'), share: top('Share this app'), install: top('Add to Home Screen') }; }""")
    check("Help's two buttons sit side by side", rows["upd"] is not None and rows["upd"] == rows["bug"], rows)
    check("so do Share and Add to Home Screen", rows["share"] is not None and rows["share"] == rows["install"], rows)
    # Find me wears the search field's glass, at its height.
    pg.evaluate("()=>{ showRankings(); }")
    pg.wait_for_timeout(600)
    fm = pg.evaluate("""()=>{ const a=document.querySelector('.rank-search'), b=document.querySelector('.rank-me-btn');
      if(!a||!b) return null; const ca=getComputedStyle(a), cb=getComputedStyle(b);
      return { h:[Math.round(a.getBoundingClientRect().height), Math.round(b.getBoundingClientRect().height)],
               bg:[ca.backgroundColor, cb.backgroundColor], blur:cb.backdropFilter }; }""")
    check("Find me matches the search field beside it",
          bool(fm) and fm["h"][0] == fm["h"][1] and fm["bg"][0] == fm["bg"][1] and "blur" in (fm["blur"] or ""), fm)
    # The person card: no rank coin on the character, and "Correct answers".
    pc = pg.evaluate("""()=>{ openPersonSheet({ pub:'bo-pub', firstName:'Bo', level:40, badges:6, hundos:40, xp:50000, correct:900, avatarChar:'robot' });
      const card=document.querySelector('.person-card'); if(!card) return null;
      const r={ coin: !!card.querySelector('.person-card-art .lb-rankmark'),
                labels: [...card.querySelectorAll('.person-card-cell-label')].map(e=>e.textContent) };
      document.querySelectorAll('.invite-overlay').forEach(e=>e.remove());
      return r; }""")
    check("no rank coin above a classmate's character", bool(pc) and not pc["coin"], pc)
    check("the last box says Correct answers", bool(pc) and "Correct answers" in pc["labels"], pc)
    # Review has sources. (The Game difficulty check that sat here went
    # with Game mode in build 283; check_b283 asserts it is gone.)
    sh = pg.evaluate("""()=>{ cfg.units=[topicsIn(QUESTIONS)[0]];
      cfg.mode='review'; showSetup(); const d=document.querySelector('.drawfrom-sect');
      return { reviewSources: !!(d && !d.hidden) }; }""")
    check("Review can draw from flagged", sh["reviewSources"], sh)
    # Home: nothing animates an SVG filter every frame.
    an = pg.evaluate("()=>{ showHome(); return document.querySelectorAll('.cosmic-hero-svg animate').length; }")
    check("Home's hero animates no SVG filter", an == 0, an)
    ctx.close()


def check_b220(br):
    """Build 220: five flares, five characters, banners, all counted from
    what people had already done. Written against build 219, where every
    one of these fails (none of the names exists)."""
    print("\n11. build 220: flares on levels, the new characters, banners")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{
      const out = {};
      out.order = MYSTERY_ORDER.slice();
      // The windows: red at 35, orange 40-41, yellow before 46, violet by 60.
      store.flareLevels = { orange: 45, yellow: 66 };   // the old schedule's draws
      out.gates = ['red','orange','yellow','violet','white'].map(k => mysteryLevelGate(k));
      // Void's flares are not looked for until Void is held.
      store.mysteryColorsFound = { red:false, orange:false, yellow:false, violet:false, white:false };
      store.flareNextTestAt = 0;
      const lv = levelOf; levelOf = () => 75;
      out.violetBeforeVoid = mysteryGateMet('violet');
      out.redAt75 = mysteryGateMet('red');
      // Catch-up: owed the next one already, so it is held back 3-4 tests.
      const t0 = testsCompletedOf(store);
      store.mysteryColorsFound.red = true; armFlareCatchup();
      out.hold = store.flareNextTestAt - t0;
      out.orangeNow = mysteryGateMet('orange');
      levelOf = lv;
      return out; }""")
    check("five flares, the last two Void's",
          r["order"] == ["red", "orange", "yellow", "violet", "white"], r["order"])
    g = r["gates"]
    check("each flare's level sits in its window, old draws redrawn",
          g[0] == 35 and g[1] in (40, 41) and 42 <= g[2] <= 45 and 55 <= g[3] <= 59 and 68 <= g[4] <= 72, g)
    check("Void's flares wait for Void", not r["violetBeforeVoid"] and r["redAt75"], r)
    check("somebody behind gets the next one three or four tests later, not the next test",
          r["hold"] in (3, 4) and not r["orangeNow"], r)

    c = pg.evaluate("""()=>{
      /* The Champion was retired in 243 - its challenge is the Clown's. */
      const ids = ['clown','umbra','singularity'];
      const out = { drawn: ids.map(id => !!buildAvatarCharSVG(id)),
                    locked: ids.map(id => isLockedCharacter(id)) };
      // Game beats already on the account count straight away.
      const units = topicsIn(QUESTIONS).slice(0, 10);
      const keep = store.unitGameBeat;
      store.unitGameBeat = {};
      units.forEach(u => store.unitGameBeat[u] = { easy:true, average:false, hardcore:false });
      // Build 225 gave the two Game challenges banners, not characters;
      // build 284 removed those banners outright. Neither may exist.
      out.foxAfter = !bannerDef('easy10');
      out.vikingAfter = !bannerDef('average10');
      out.noFox = !AVATAR_CHARACTERS.some(c => c.id === 'fox' || c.id === 'viking');
      store.unitGameBeat = keep;
      // Wins: once per room, only first place, and the fifth queues the Champion.
      store.vrMatches = 0; store.vrWins = 4; store.vrCounted = []; store.pendingCharUnlocks = [];
      recordVroomOutcome('ROOM-1', ['me','bo'], 'me');
      recordVroomOutcome('ROOM-1', ['me','bo'], 'me');
      recordVroomOutcome('ROOM-2', ['bo','me'], 'me');
      recordVroomOutcome('ROOM-3', ['me'], 'me');
      out.vr = [store.vrMatches, store.vrWins, (store.pendingCharUnlocks||[]).slice()];
      out.champ = isLockedCharacter('clown');
      return out; }""")
    check("the new characters draw and start locked",
          all(c["drawn"]) and all(c["locked"]), c)
    check("no Game banner (Lanterns, Great Wave) exists any more, and there is no Fox or Viking (build 284)",
          c["foxAfter"] and c["vikingAfter"] and c["noFox"], c)
    check("a room counts once, a win needs a rival, and the fifth hands over the Clown (the Champion's, before 243)",
          c["vr"][0] == 3 and c["vr"][1] == 5 and c["vr"][2] == ["clown"] and not c["champ"], c["vr"])

    b = pg.evaluate("""()=>{
      const out = {};
      store.fullTestsSeeded = false; store.lifetime.fullTests = 0;
      seedBannerCounters();
      out.seeded = fullTestsOf(); out.plays = testsCompletedOf(store);
      store.lifetime.fullTests = 120; store.practiceExamPerfect = true; store.banner = 'exam100';
      out.earned = BANNERS.filter(x => bannerEarned(x.id)).map(x => x.id);
      showCustomize();
      out.opts = document.querySelectorAll('.banner-opt').length; out.nBanners = BANNERS.length;
      out.selected = (document.querySelector('.banner-opt.selected')||{}).dataset;
      out.selected = out.selected ? out.selected.banner : null;
      out.nListed = BANNERS.filter(x => !x.secret || bannerEarned(x.id)).length;
      // Build 243: a locked tile is its name and a padlock; what it needs
      // is on the pop-up a tap opens, not printed under every tile.
      const locked = document.querySelector('.banner-opt.locked:not([data-banner=""])');
      out.lockedTileNeed = locked ? !!locked.querySelector('.banner-opt-need') : null;
      if(locked) locked.click();
      const card = document.querySelector('.unlock-card-banner');
      out.lockedSays = card ? card.textContent : '';
      document.querySelectorAll('.invite-overlay').forEach(x => x.remove());
      document.querySelector('.banner-opt[data-banner="tests100"]').click();
      out.wear = store.banner;
      showProfile();
      out.cover = (document.querySelector('.profile-cover.has-banner .bnr')||{}).className || null;
      // A room row carries whoever's banner is in the document.
      const items = rsUnlockItems({ colors:[], characters:[], banners:['vr50'], badges:[], flare:'violet' });
      out.items = items.map(i => i.kind + ':' + (i.banner || i.character || i.flare || ''));
      return out; }""")
    check("full tests are seeded from the work already done, never above the runs played",
          b["seeded"] > 0 and b["seeded"] <= b["plays"], b)
    check("banners earned off the counters", "tests100" in b["earned"] and "exam100" in b["earned"]
          and "tests250" not in b["earned"], b["earned"])
    # Build 243 moved a locked banner's requirement onto a tap; build 246
    # puts it back under every tile as well ("The requirement needed for
    # banners need to be under each banner") - the tap still says more.
    check("Customize lists every banner but unfound secrets, plus Default, and a tap says what a locked one needs",
          b["opts"] == b["nListed"] + 1 and b["selected"] == "exam100"
          and b["lockedTileNeed"] is True and len(b["lockedSays"]) > 10, b)
    check("picking one wears it, and it is across the top of Profile",
          b["wear"] == "tests100" and b["cover"] and "bnr-tests100" in b["cover"], b)
    check("a banner and a Void flare's character are announced on the results",
          "banner:vr50" in b["items"] and "flare:violet" in b["items"] and "character:umbra" in b["items"],
          b["items"])
    ctx.close()


def check_b221(br):
    """Builds 221-222: the Virtual Room countdown, race line, leaderboard,
    Tug of War, and the chat. Written against build 220, where each fails."""
    print("\n12. builds 221-222: the room's countdown and leaderboard, Tug, the chat")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{
      const out = {};
      // The countdown: opaque, and the number never fades out.
      showVroomCountdown(Date.now() + 4000, () => {});
      const ov = document.getElementById('vroom-reveal-overlay');
      out.bg = getComputedStyle(ov).backgroundColor;
      out.ring = !!document.getElementById('vroom-reveal-ring');
      const kf = [...document.styleSheets].flatMap(sh => { try{ return [...sh.cssRules]; }catch(e){ return []; } })
        .filter(r => r.type === CSSRule.KEYFRAMES_RULE && r.name === 'vroom-reveal-pulse')[0];
      out.fades = kf ? /opacity/.test(kf.cssText) : null;
      ov.remove();
      // Any ordinary screen takes the race line down.
      raceBarEl.hidden = false; showHome();
      out.raceAfterHome = raceBarEl.hidden;
      // Correct answers and speed are counted last.
      out.stepsTail = VROOM_XP_STEPS.slice(-2).map(x => x.key);
      return out; }""")
    check("the room's countdown is opaque, with a ring, and its number never fades",
          r["bg"] in ("rgb(10, 10, 10)",) and r["ring"] and r["fades"] is False, r)
    check("the race line is gone from Home", r["raceAfterHome"] is True, r)
    check("speed and correct answers are counted last", r["stepsTail"] == ["speed", "correct"], r)

    lb = pg.evaluate("""()=>{
      vroomMyKey = 'me';
      const L = (c, s) => [{key:'correct', value:c}, {key:'speed', value:s}];
      const mk = (k, a, j, lines) => ({ key:k, p:{ name:k, avatarChar:a, joinedAt:j, xpLines:lines }, xp: lines.reduce((t, l) => t + l.value, 0) });
      /* Two CURRENT characters. This was the Robot, which is retired (244)
         and drawn as the Ninja - and since build 246 it glows as the
         Ninja too, so a Ninja beside a "Robot" is one colour twice, which
         is right. The assertion is about two different people. */
      const r = [mk('me','ninja',1,L(50,10)), mk('bo','ghost',2,L(40,90))].sort((a, b) => b.xp - a.xp);
      playVroomRaceCutscene(r);
      const rows = [...document.querySelectorAll('#vroom-race-cut .vrc-row')];
      const out = { colours: rows.map(x => x.style.getPropertyValue('--pl')), dropping: rows.every(x => x.classList.contains('is-dropping')) };
      out.chatAbove = (()=>{ document.body.classList.add('x'); const d = document.querySelector('.chatdock');
        return d ? Number(getComputedStyle(d).zIndex) : null; })();
      document.getElementById('vroom-race-cut').remove();
      return out; }""")
    check("each player's bar is in their own colour, and the rows drop in",
          len(set(lb["colours"])) == 2 and all(lb["colours"]) and lb["dropping"], lb)
    check("the chat is above the leaderboard", lb["chatAbove"] is None or lb["chatAbove"] > 430, lb)

    c = pg.evaluate("""()=>{
      const out = {};
      startChatDock && startChatDock();
      out.inbox = [...document.querySelectorAll('.chatdock-tab')].map(b => b.textContent.replace(/[0-9+]/g, '').trim());
      // The panel: emoji and plus beside the field, and polls vote once each.
      const host = document.createElement('div'); document.body.appendChild(host);
      let written = null;
      const fake = { code: () => 'X', myKey: () => 'me', colorFor: () => null, isVisible: () => true, cap: 999, keep: 999,
                     shouldTrim: () => false, label: 'Test' };
      const realDb = fbDb;
      fbDb = { collection: () => ({ doc: () => ({ update: (p) => { written = p; return Promise.resolve(); }, set: () => Promise.resolve(),
               get: () => Promise.resolve({ exists:false }) }) }) };
      const clean = buildVroomChatPanel(host, fake);
      out.tools = [!!host.querySelector('.vroom-chat-emojibtn'), !!host.querySelector('.vroom-chat-plusbtn')];
      host.querySelector('.vroom-chat-emojibtn').click();
      out.emoji = [...host.querySelectorAll('.vroom-chat-emoji')].map(b => b.textContent);
      fbDb = realDb;
      if(typeof clean === 'function') clean();
      host.remove();
      return out; }""")
    check("the second tab is called Inbox", "Inbox" in c["inbox"], c["inbox"])
    # 10-15, asked for in build 240 ("10-15 emoji"); this used to ask for
    # 30+, from before that request, and went red for being right.
    check("the chat has an emoji tray and a photo/poll button",
          all(c["tools"]) and 10 <= len(c["emoji"]) <= 15, {"tools": c["tools"], "emoji": len(c["emoji"])})
    check("the emoji tray has the one that was asked for", "\U0001F595" in c["emoji"], len(c["emoji"]))

    t = pg.evaluate("""()=>{
      // Tug: odd rooms wait; the pot goes to the winners.
      const src = String(showVirtualRoomLobby);
      return { oddGate: /oddTug/.test(src), perRight: TUG_XP_PER_RIGHT,
               countdown: /showVroomCountdown\\(tugStartAt/.test(String(beginTugMatch)),
               board: /Team leaderboard in/.test(String(showTugResult)) }; }""")
    check("Tug waits for even teams, counts down, pays the winners and shows a team board",
          t["oddGate"] and t["countdown"] and t["board"] and t["perRight"] > 0, t)
    ctx.close()


def check_b223(br):
    """Build 223: Battle, in teams. Written against build 222, where none of it exists."""
    print("\n13. build 223: Battle - two teams, one health bar each, powers, alerts")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{
      const out = {};
      const parts = { me:{name:'Me',avatarChar:'ninja',joinedAt:1}, bo:{name:'Bo',avatarChar:'robot',joinedAt:2},
                      cy:{name:'Cy',avatarChar:'fox',joinedAt:3}, dee:{name:'Dee',avatarChar:'queen',joinedAt:4} };
      const teams = tugTeamsFor(parts);
      out.teams = teams;
      const mk = (log) => ({ startAt: 1000, participants: parts, battle: { teams: teams, log: log, progress:{} } });
      const E = (id, at, from, kind, x) => Object.assign({ id, at, from, kind }, x || {});
      // A hit from either member of a side comes off the OTHER side's one bar.
      let r = battleReplay(mk([E('a',1,'me','hit',{dmg:5}), E('b',2,'cy','hit',{dmg:5}), E('c',3,'bo','hit',{dmg:5})]));
      out.hp = r.hp; out.max = r.max;
      // Order-independent: the same log in any array order is the same fight.
      const log = [E('a',1,'bo','hit',{dmg:5}), E('b',2,'me','shield'), E('c',3,'dee','hit',{dmg:5}), E('d',4,'bo','double'),
                   E('e',5,'bo','hit',{dmg:5}), E('f',6,'cy','heal'), E('g',7,'cy','hit',{dmg:5})];
      out.orderFree = JSON.stringify(battleReplay(mk(log)).hp) === JSON.stringify(battleReplay(mk(log.slice().reverse())).hp);
      out.events = battleReplay(mk(log)).events.map(e => e.kind);
      // A side at zero is down, and nothing after it counts.
      const ko = [];
      for(let i = 0; i < 40; i++) ko.push(E('k' + i, 10 + i, i % 2 ? 'me' : 'cy', 'hit', {dmg:7}));
      ko.push(E('z', 999, 'bo', 'hit', {dmg:5}));
      r = battleReplay(mk(ko));
      out.downed = r.downed; out.afterDown = r.hp[teams.me];
      // At least fifty questions, the same order on every device.
      cfg.units = ['Identity Crimes']; cfg.source = 'all';
      const p1 = battleBuildPool({ startAt: 5, battle: {} }), p2 = battleBuildPool({ startAt: 5, battle: {} });
      out.pool = [p1.length, JSON.stringify(p1) === JSON.stringify(p2), poolNow().length];
      out.picker = /\\["battle", "Battle"\\]/.test(String(showVirtualRoomSetup));
      out.art = buildVroomModeArt('battle').querySelectorAll('path').length;
      // Even teams: the lobby holds an odd room for Battle as it does for Tug.
      out.oddGate = /data\\.game === "battle"\\) && totalN % 2 === 1/.test(String(showVirtualRoomLobby));
      return out; }""")
    t = r["teams"]
    check("teams alternate by join order, two a side", sorted(t.values()) == ["a", "a", "b", "b"] and t["me"] != t["bo"], t)
    check("one health bar per side, sized for the side",
          set(r["max"].values()) == {200} and r["hp"][t["bo"]] == 190 and r["hp"][t["me"]] == 195, r)
    check("the bars are the same whatever order the log arrives in", r["orderFree"], r["events"])
    check("a shield blocks a hit, a double doubles one, a heal heals",
          "blocked" in r["events"] and "double" in r["events"] and "heal" in r["events"], r["events"])
    check("a side at zero is down, and a hit after that does nothing",
          r["downed"] == t["bo"] and r["afterDown"] == 200, r)
    check("a small unit cycles to at least fifty questions, in one shared order",
          r["pool"][0] >= 50 and r["pool"][1] and r["pool"][2] < 50, r["pool"])
    check("Match settings offers Battle, drawn as crossed swords", r["picker"] and r["art"] == 6, r)
    check("an odd room waits for one more before a Battle starts", r["oddGate"], r["oddGate"])

    u = pg.evaluate("""()=>{
      const out = {};
      vroomCode = null; vroomMyKey = 'me'; vroomIsHost = false;
      const parts = { me:{name:'Me',avatarChar:'ninja',joinedAt:1}, bo:{name:'Bo',avatarChar:'robot',joinedAt:2},
                      cy:{name:'Cy',avatarChar:'fox',joinedAt:3}, dee:{name:'Dee',avatarChar:'queen',joinedAt:4} };
      cfg.units = ['Identity Crimes']; cfg.source = 'all';
      const d = { startAt: Date.now() - 1000, participants: parts, battle: { teams: tugTeamsFor(parts), log: [], progress:{}, count: 0 } };
      battlePool = battleBuildPool(d); battleCount = battlePool.length; battlePos = 0; battleShownPos = -1;
      battleHeld = null; battleSeen = null; battleLastData = d; battleFrozenUntil = 0; battleFlippedUntil = 0;
      battleAbsorbLog(d);
      renderBattleScreen(d);
      out.bars = [...document.querySelectorAll('.screen-battle .battle-side')].map(x => x.querySelector('.battle-side-title').textContent);
      out.faces = [...document.querySelectorAll('.screen-battle .battle-side')].map(x => x.querySelectorAll('.battle-av').length);
      out.choices = document.querySelectorAll('.screen-battle .choice').length;
      out.hint = (document.querySelector('.battle-power-hint') || {}).textContent || '';
      // Bo freezes me, Dee flips me: both land, and each is announced by name.
      const now = Date.now();
      d.battle.log = [{ id:'f1', at: now, from:'bo', kind:'freeze', to:'me' }, { id:'f2', at: now, from:'dee', kind:'flip', to:'me' }];
      battleAbsorbLog(d);
      const panel = document.querySelector('.screen-battle');
      out.frozen = panel.classList.contains('is-frozen') && !document.querySelector('.battle-ice').hidden;
      out.flipped = panel.classList.contains('is-flipped') && getComputedStyle(document.querySelector('.battle-flip')).transform !== 'none';
      out.iceUpright = getComputedStyle(document.querySelector('.battle-arena')).transform === 'none';
      out.alerts = [document.querySelector('.battle-alert') ? document.querySelector('.battle-alert').textContent : ''].concat(battleAlertQueue.map(a => a.text));
      document.querySelector('.screen-battle .choice').click();
      out.frozenTap = battlePos;
      battleHeld = 'shield'; battlePaintPower(d);
      out.power = (document.querySelector('.battle-power-btn') || {}).textContent || '';
      detachBattle(); detachBattleEffects();
      // The end: my side won; XP for right answers plus the win.
      d.battle.over = true; d.battle.winner = d.battle.teams.me;
      d.battle.progress = { me:{pos:20,correct:14}, bo:{pos:22,correct:18}, cy:{pos:15,correct:9}, dee:{pos:12,correct:6} };
      showBattleResult(d);
      out.xp = (document.querySelector('.screen-battle-result .tug-xp-num') || {}).textContent || '';
      out.title = (document.querySelector('.screen-battle-result h1') || {}).textContent || '';
      out.cols = document.querySelectorAll('.screen-battle-result .tug-board-col').length;
      return out; }""")
    check("the match screen has two bars, yours first, each with its members",
          u["bars"] == ["Your side", "Their side"] and u["faces"] == [2, 2] and u["choices"] >= 2
          and "question 10" in u["hint"], u)
    check("a freeze locks the answers and a flip turns the question over, with the ice still upright",
          u["frozen"] and u["flipped"] and u["iceUpright"] and u["frozenTap"] == 0, u)
    check("each is announced naming who did it",
          any("Bo froze you" in a for a in u["alerts"]) and any("Dee turned your screen upside down" in a for a in u["alerts"]), u["alerts"])
    check("a held power is a button that says what it does", "Use Shield" in u["power"], u["power"])
    check("the result names the winning side and pays for right answers plus the win",
          u["title"] == "Your side won" and u["xp"] == "+290 XP" and u["cols"] == 2, u)
    ctx.close()


def check_b229(br):
    """Build 229: last week's top three, and shuffles that do not repeat."""
    print("\n14. build 229: last week's podium, answer positions, question order")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{
      const out = { shuffleOn: cfg.shuffle };
      runMode = 'drill';
      const qi = QUESTIONS.findIndex(q => !q.fixedOrder && q.choices.length === 4);
      let prev = null, repeats = 0, bank = 0; const seen = new Set();
      for(let i = 0; i < 30; i++){
        layout = {}; const o = optionOrder(qi); const sl = o.indexOf(QUESTIONS[qi].answer);
        if(sl === prev) repeats++; if(o.every((v, k) => v === k)) bank++; prev = sl; seen.add(sl);
      }
      out.repeats = repeats; out.bank = bank; out.slotsUsed = seen.size;
      localStorage.removeItem('class26e.recentq');
      const unit = QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic === 'Identity Crimes');
      let last = null, overlap = 0;
      for(let i = 0; i < 8; i++){
        const ord = freshOrder(unit); rememberOpeners(ord);
        const first = ord.slice(0, 4);
        if(last) overlap += first.filter(x => last.includes(x)).length;
        last = first;
      }
      out.overlap = overlap;
      const lw = lastWeekKey(), wk = weekKeyNow();
      const E = (pub, n, x) => Object.assign({ pub, firstName: n, avatarChar: 'ninja' }, x);
      const rows = [E('a', 'Bo', { week: wk, weekPoints: 900, prevWeek: lw, prevWeekPoints: 4200 }),
                    E('b', 'Cy', { week: lw, weekPoints: 5100 }),
                    E('c', 'Dee', { week: wk, weekPoints: 300, prevWeek: lw, prevWeekPoints: 2600 }),
                    E('d', 'Eli', { week: wk, weekPoints: 1200 })];
      rows.forEach(e => { e.rawWeekPoints = e.weekPoints; e.weekPoints = weekPointsOfEntry(e); });
      // The numbers path, with any hand-recorded week set aside (build 246
      // pins the week of 21 Sep, which is "last week" until 5 Oct).
      const pinned = Object.assign({}, WEEK_RESULTS_KNOWN);
      Object.keys(WEEK_RESULTS_KNOWN).forEach(k => delete WEEK_RESULTS_KNOWN[k]);
      out.top = lastWeekTop3(rows).map(t => t.name);
      const host = document.createElement('div'); document.body.appendChild(host);
      renderRankingRows(host, rows, RANKING_BOARDS.find(b => b.key === 'week'), {});
      out.podium = host.querySelectorAll('.lw-podium .lw-podium-spot').length;
      // A recorded week wins over the numbers, and says Winner, not a total.
      WEEK_RESULTS_KNOWN[lw] = ['d'];
      out.pinned = lastWeekTop3(rows).map(t => [t.name, t.pts]);
      renderRankingRows(host, rows, RANKING_BOARDS.find(b => b.key === 'week'), {});
      out.pinnedPts = [...host.querySelectorAll('.lw-podium .lw-podium-pts')].map(x => x.textContent);
      Object.keys(WEEK_RESULTS_KNOWN).forEach(k => delete WEEK_RESULTS_KNOWN[k]); Object.assign(WEEK_RESULTS_KNOWN, pinned);
      out.sauce = WEEK_RESULTS_KNOWN['2026-09-21'];
      host.remove();
      return out; }""")
    check("answer positions are shuffled by default", r["shuffleOn"] is True, r)
    check("the right answer never lands where it was last time, or in the book's order",
          r["repeats"] == 0 and r["bank"] == 0 and r["slotsUsed"] == 4, r)
    check("consecutive runs of a small unit open with different questions", r["overlap"] == 0, r)
    check("last week's top three come from last week's numbers, not this week's",
          r["top"] == ["Cy", "Bo", "Dee"] and r["podium"] == 3, r)
    # Build 248: the totals are what each had WHEN THE WEEK CLOSED, not
    # today's. Odin and Napoleon's are exact (synced before the rollover);
    # Sauce's, by instruction in build 257: his current total less this
    # week's 330 - 67,470 ("needs to be whatever his current xp is minus 330").
    sauce = (r.get("sauce") or [{}])[0]
    check("a hand-recorded week (Sauce, OdinSavior, Napoleon; 21 Sep) shows what each had when the week closed",
          r["pinned"] == [["Eli", None]] and r["pinnedPts"] == ["Winner"]
          and [x["pub"] for x in r["sauce"]] == ["ew7hyxpg5j2y", "kdxnp7smgcre", "mbw5qdhcw2pf"]
          and [x.get("pts") for x in r["sauce"][1:]] == [58880, 31500]
          and sauce.get("pts") == 67470, r)
    ctx.close()


def check_b230(br):
    """Build 230: Home without the lag, and loading bars that do not lurch.
    Written against build 229, where both fail."""
    print("\n15. build 230: Home's raster cost, the loading bar on the compositor")
    # The splash, before booted() removes it: its bar must be a compositor
    # animation, not a width a busy main thread has to keep setting.
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script("try{localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % USED_ACCOUNT)
    pg = open_page(ctx); pg.goto(URL); pg.wait_for_timeout(400)
    bar = pg.evaluate("""()=>{ const f = document.getElementById('splash-fill'); if(!f) return null;
      return { anims: f.getAnimations().map(a => a.animationName), w: f.style.width || '' }; }""")
    check("the splash bar fills by a CSS animation, not a width set every frame",
          bool(bar) and "loadbar-fill" in bar["anims"] and not bar["w"], bar)
    ctx.close()
    # Home: 3s of raster work under a 4x throttle, at the phone's own 3x.
    # Here 229 measures ~690ms and 230 ~250ms; on the capture harness at
    # her 518px view it was ~5.9s against ~0.4s. The ceiling is loose on
    # purpose (raster time grows with machine load) and catches the
    # full-blown case; the scale check below is the one that pins the
    # cause, and it fails on 229.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=3, touch=True)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
    cdp = pg.context.new_cdp_session(pg); cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    br.start_tracing(page=pg, categories=["devtools.timeline", "disabled-by-default-devtools.timeline"])
    pg.wait_for_timeout(3000)
    data = json.loads(br.stop_tracing())
    ev = data["traceEvents"] if isinstance(data, dict) else data
    raster = sum(e.get("dur", 0) for e in ev if e.get("name") == "RasterTask") / 1000
    check("Home's animations are not re-rasterised every frame (raster ms in 3s)", raster < 1500, round(raster))
    scaled = pg.evaluate("""()=>document.getAnimations().filter(a => {
        const t = a.effect && a.effect.target; if(!t || !t.closest || !t.closest('.cosmic-hero-wrap')) return false;
        const r = t.getBoundingClientRect(); if(r.width * r.height < 250000) return false;
        return a.effect.getKeyframes().some(k => /scale/.test(k.transform || '')); }).map(a => a.animationName)""")
    check("nothing large on Home animates by scale", scaled == [], scaled)
    ctx.close()


def check_b231(br):
    """Build 231: banners on the person card, tappable friends, no rank coin
    on the Friends list, and every theme three tones. Written against build
    230, where each fails."""
    print("\n16. build 231: the card shows their banner; friends open it; themes stay three-tone")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{
      const out = {};
      bannerEarned = () => true; store.banner = 'tests100';
      out.rowBanner = buildLeaderboardRow().banner;
      openPersonSheet({ pub:'bo', firstName:'Bo', avatarChar:'robot', level:40, badges:6, banner:'tests250' });
      const card = document.querySelector('.person-card');
      out.cover = !!(card && card.classList.contains('has-cover') && card.querySelector('.person-card-cover .bnr'));
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      leaderboardRows = [{ pub:'f1', firstName:'Alex', avatarChar:'dragon', level:40, badges:6, hundos:3, banner:'tests100',
                           seenAt:Date.now(), lastModified:Date.now() }];
      store.friendsOut = ['f1']; store.friendsIn = ['f1'];
      showFriends();
      const row = [...document.querySelectorAll('.friend-row')].find(x => /Alex/.test(x.textContent));
      out.coin = !!(row && row.querySelector('.lb-rankmark'));
      out.tappable = !!(row && row.classList.contains('is-tappable'));
      if(row) row.click();
      out.friendCard = (document.querySelector('.person-card .person-sheet-name') || {}).textContent || null;
      out.friendCover = !!document.querySelector('.person-card.has-cover');
      // a presence repaint must not take the card away
      try{ refreshPresenceViews(); }catch(e){}
      out.survives = !!document.querySelector('.person-card');
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      // three tones: the three stops of every theme are three different hues
      const hue = h => { const n = parseInt(h.slice(1), 16), r = (n >> 16) / 255, g = (n >> 8 & 255) / 255, b = (n & 255) / 255;
        const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if(!d) return null;
        let x = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return (x * 60 + 360) % 360; };
      const gap = (a, b) => { const d = Math.abs(a - b) % 360; return Math.min(d, 360 - d); };
      out.flat = [];
      ['rookie','ranger','veteran','vanguard','adept','elite','titan'].forEach(a => {
        document.documentElement.dataset.accent = a;
        const cs = getComputedStyle(document.documentElement);
        const hs = ['--theme-c1','--theme-c2','--theme-c3'].map(k => hue(cs.getPropertyValue(k).trim()));
        const spread = Math.max(gap(hs[0], hs[1]), gap(hs[1], hs[2]), gap(hs[0], hs[2]));
        if(!(spread >= 12)) out.flat.push([a, Math.round(spread)]);
      });
      return out; }""")
    check("your worn banner is published on your leaderboard row", r["rowBanner"] == "tests100", r)
    check("a classmate's card shows their banner across the top", r["cover"], r)
    check("no rank coin on a friend's character", r["coin"] is False, r)
    check("tapping a friend opens their card, banner and all",
          r["tappable"] and r["friendCard"] == "Alex" and r["friendCover"], r)
    check("the Friends screen repainting does not close an open card", r["survives"], r)
    check("every theme spans more than one hue", r["flat"] == [], r["flat"])
    ctx.close()


def check_b232(br):
    """Build 232: Madison's list of twenty-two. Written against build 231,
    where each of these fails or throws."""
    print("\n17. build 232: characters, banners, the Rank tab turned over, glass bubbles, the badge case, Pause")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{
      const out = {};
      const T = (k, f) => { try{ out[k] = f(); }catch(e){ out[k] = 'THREW ' + e.message; } };
      // Characters
      T('order', () => AVATAR_CHARACTERS.filter(c => c.feat).map(c => c.id));
      T('masked', () => { const d = AVATAR_CHARACTERS.find(c => c.id === 'masked');
        store.unitGameBeat = {}; store.retakenQuestions = 99;
        const before = isLockedCharacter('masked'), msg = characterLockMessage('masked');
        store.retakenQuestions = 100;
        return { feat: d && d.feat, before, msg, after: isLockedCharacter('masked') }; });
      T('poseidon', () => {
        store.weeklyTop3 = 2; store.pendingCharUnlocks = [];
        store.weekRankSeen = { week: '1999-W01', rank: 3 };
        settleWeeklyWin();
        return { top3: store.weeklyTop3, queued: store.pendingCharUnlocks.slice(), locked: isLockedCharacter('poseidon') }; });
      T('spartan', () => {
        store.vrWins = 9; store.vrCounted = []; store.pendingCharUnlocks = [];
        recordVroomOutcome('ROOMX', ['me', 'bo'], 'me');
        return { wins: store.vrWins, queued: store.pendingCharUnlocks.slice(), locked: isLockedCharacter('valkyrie') }; });
      T('rankMsg', () => characterLockMessage('solar'));  // Gold's since 244
      T('flareMsgs', () => { store.mysteryColorsFound = { red:false, orange:false, yellow:false, violet:false, white:false };
        return [characterLockMessage('umbra'), characterLockMessage('singularity')]; });
      // A real retake run through summarize() counts every question in it
      T('retakeRun', () => {
        const U = topicsIn(QUESTIONS)[0];
        const ix = QUESTIONS.map((q,i)=>i).filter(i => (QUESTIONS[i].topic||'').trim() === U).slice(0, 5);
        store.retakenQuestions = 7;
        cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [U];
        // As the Retake button leaves it: beginRun(missed, "Missed questions", null, true)
        // labels the run, and a labelled run is not a trackable one.
        order = ix; runTrackable = false; timedOut = false; runMode = 'drill'; runLabel = 'Missed questions';
        attempts = {}; picked = {}; timedOutSet = {};
        ix.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
        isMissedRetake = true;
        try{ summarize(); } finally { isMissedRetake = false; }
        document.querySelectorAll('.rs-spot').forEach(e => e.remove());
        return store.retakenQuestions; });
      // Banners
      T('banners', () => BANNERS.map(b => [b.id, b.name]));
      // A seventeenth unit, for the length of one read: the number has to
      // follow it, which a written-in "16" cannot.
      // Hall of Fame (badges16) and Thunderhead (hardcore10) were removed
      // in build 284; both must be gone, not merely locked.
      T('gone284', () => ['badges16', 'hardcore10', 'easy10', 'average10'].filter(id => !!bannerDef(id)));
      // Planets: highlight and rim are two different colours
      T('planets', () => {
        const hue = h => { const n = parseInt(h.slice(1), 16), r = (n >> 16) / 255, g = (n >> 8 & 255) / 255, b = (n & 255) / 255;
          const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if(!d) return 0;
          let x = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return (x * 60 + 360) % 360; };
        const gap = (a, b) => { const d = Math.abs(a - b) % 360; return Math.min(d, 360 - d); };
        const res = {};
        // Build 244: Bronze is the rookie key now (it was ranger's), and
        // Silver, the new ranger, is held to the same rule.
        ['rookie','ranger','veteran','adept','titan'].forEach(a => {
          document.documentElement.dataset.accent = a;
          const cs = getComputedStyle(document.documentElement);
          res[a] = Math.round(gap(hue(cs.getPropertyValue('--theme-c1').trim()), hue(cs.getPropertyValue('--theme-c3').trim())));
        });
        document.documentElement.dataset.accent = theme.accent || 'ink';
        return res; });
      // The leaderboard is published the moment the app is put away
      T('publish', () => {
        let flushed = 0; const real = flushLeaderboardRow;
        flushLeaderboardRow = () => { flushed++; };
        const vs = Object.getOwnPropertyDescriptor(Document.prototype, 'visibilityState');
        Object.defineProperty(document, 'visibilityState', { configurable:true, get: () => 'hidden' });
        const had = { db: fbDb, code: syncCode, opt: store.leaderboardOptIn };
        fbDb = fbDb || {}; syncCode = syncCode || 'TEST-CODE'; store.leaderboardOptIn = true;
        document.dispatchEvent(new Event('visibilitychange'));
        delete document.visibilityState;
        fbDb = had.db; syncCode = had.code; store.leaderboardOptIn = had.opt;
        flushLeaderboardRow = real;
        return flushed; });
      return out; }""")
    # Build 243: the Clown and the Astronaut took the Champion's and Blitz's
    # challenges, the K-9 is new, and SWAT is the sunglasses secret.
    # Build 244: the Valkyrie took the Spartan's ten wins, the Hacker the
    # K-9's twenty hours, the Timekeeper is new, and SWAT is its own secret.
    # Build 245: SWAT removed entirely - not in the row at all.
    # Build 262: the Night Owl joined the end of the row. Asserted as the
    # SHAPE now - the known ones in their order, anything new after them,
    # the secrets last - because a list written out in full failed the
    # build for adding a character, which is the one thing this row is for.
    known = ["detective", "masked", "zeus", "poseidon", "clown", "valkyrie", "marksman", "astronaut", "hacker", "timekeeper"]
    secrets = ["voidwalker", "umbra", "singularity"]
    o = r["order"]
    check("the challenge row: the known challenge characters in order, anything newer after them (the Ronin), then the secrets",
          o[:len(known)] == known and o[-len(secrets):] == secrets and "ronin" in o and "knight" not in o and "nightowl" not in o, o)
    # Build 233: the Masked One is back, for retaking missed questions.
    check("the Masked One unlocks at 100 retaken questions and says how far along you are",
          isinstance(r["masked"], dict) and r["masked"]["feat"] == "retake100" and r["masked"]["before"] is True
          and "99 of 100" in r["masked"]["msg"] and r["masked"]["after"] is False, r["masked"])
    check("a third week on the weekly podium hands over Poseidon",
          isinstance(r["poseidon"], dict) and r["poseidon"]["top3"] == 3 and "poseidon" in r["poseidon"]["queued"]
          and r["poseidon"]["locked"] is False, r["poseidon"])
    # Build 289: the Koi (the Valkyrie's id) is seven study days in a row,
    # so a tenth win counts as a win and hands over nothing.
    check("a tenth Virtual Room win is counted and no longer hands over the Koi (build 289)",
          isinstance(r["spartan"], dict) and r["spartan"]["wins"] == 10 and "valkyrie" not in r["spartan"]["queued"], r["spartan"])
    check("a rank character says only which rank unlocks it",
          isinstance(r["rankMsg"], str) and r["rankMsg"].startswith("Unlocks at ") and "rank" in r["rankMsg"]
          and "Level" not in r["rankMsg"] and "badge" not in r["rankMsg"], r["rankMsg"])
    check("Umbra and Singularity keep their requirement hidden until the one before is unlocked",
          isinstance(r["flareMsgs"], list) and "Unlock Void" in r["flareMsgs"][0] and "Unlock Umbra" in r["flareMsgs"][1]
          and "Find" not in "".join(r["flareMsgs"]), r["flareMsgs"])
    # Build 289: a retake is counted as each question is answered (check_b289
    # walks a real one), so the end of the run must add nothing on top.
    check("finishing a retake run adds nothing on top of what was counted as it was answered",
          r["retakeRun"] == 7, r["retakeRun"])
    names = dict(r["banners"]) if isinstance(r["banners"], list) else {}
    check("Northern Lights is the 100-test banner and Sakura the 250",
          names.get("tests100") == "Northern Lights" and names.get("tests250") == "Sakura", names)
    check("Sky Temple and the Supernova banner exist",
          names.get("hundos250") == "Sky Temple" and names.get("titan_rank") == "Supernova", names)
    check("Lanterns, Great Wave, Thunderhead and Hall of Fame are gone (build 284)", r["gone284"] == [], r["gone284"])
    check("the four circled themes put a second colour on the planet",
          isinstance(r["planets"], dict) and all(v >= 35 for v in r["planets"].values()), r["planets"])
    check("putting the app away publishes your leaderboard row there and then", r["publish"] == 1, r["publish"])

    # Screens
    s = pg.evaluate("""()=>{
      const out = {};
      const T = (k, f) => { try{ out[k] = f(); }catch(e){ out[k] = 'THREW ' + e.message; } };
      showProfile('ranks');
      T('ladder', () => [...document.querySelectorAll('.rankmap-stop .rankmap-name')].map(n => n.textContent));
      /* The chip is there at once; its art is drawn after the first
         paint (build 282), so this asks for the chip and the art is
         waited for below. */
      T('novaBanner', () => { const st = [...document.querySelectorAll('.rankmap-stop')].pop();
        return !!(st && st.querySelector('.rankmap-bannerprev, .rankmap-gift.is-banner .rankmap-giftbanner')); });
      T('centred', () => [...document.querySelectorAll('.rankmap-node')].map(n => {
        const svg = n.querySelector('svg.rank-emblem-svg'); const a = n.getBoundingClientRect(), b = svg.getBoundingClientRect();
        return { vb: svg.getAttribute('viewBox'), dx: Math.round(Math.abs((a.left + a.width / 2) - (b.left + b.width / 2))),
                 over: Math.round(Math.max(0, b.width - a.width)) }; }));
      T('hero', () => ({ gauges: document.querySelectorAll('.rankhero .rankhero-gauge').length,
                         bar: !!document.querySelector('.rankhero-fill, .rankhero-track'),
                         chips: !!document.querySelector('.rankhero-chip') }));
      showProfile('badges');
      T('case', () => { const bg = getComputedStyle(document.querySelector('.badges-tab .badge-grid')).backgroundImage;
        const cols = [...bg.matchAll(/rgb\\((\\d+), (\\d+), (\\d+)\\)/g)].map(m => [+m[1], +m[2], +m[3]]);
        return cols.map(c => c[2] - c[0]); });
      cfg.mode = 'drill'; const u = topicsIn(QUESTIONS)[0]; store.unitPerfects[u] = 999; showSetup();
      T('chip', () => !!document.querySelector('.screen-setup .rs-mode.rs-mode-drill'));
      T('glow', () => { const b = document.querySelector('.pick-badge.earned');
        return b ? [b.style.getPropertyValue('--badge-glow').trim().toUpperCase(), String(badgeThemeFor(u).p).toUpperCase()] : null; });
      showCustomize();
      T('fade', () => { const svg = document.querySelector('.avatarchar-option .avatarchar-svg');
        const cs = svg && getComputedStyle(svg); return cs ? (cs.maskImage || cs.webkitMaskImage || '') : null; });
      showAppearance();
      T('sync', () => { const l = document.querySelector('.sync-code-row .sync-code-label'); return l ? getComputedStyle(l).color : null; });
      return out; }""")
    # Build 244: the first rank is Bronze (it was Iron).
    check("the ladder reads Bronze first and Supernova last, the way you scroll",
          isinstance(s["ladder"], list) and s["ladder"][:1] == ["Bronze"] and s["ladder"][-1:] == ["Supernova"], s["ladder"])
    check("Supernova's stop shows its banner among what it hands over", s["novaBanner"] is True, s["novaBanner"])
    # ...and the art fills it once the screen is up (build 282 draws it
    # after the first paint).
    pg.evaluate("()=>showProfile('ranks')")
    try:
        pg.wait_for_function("""()=>{ const st=[...document.querySelectorAll('.rankmap-stop')].pop();
          return !!(st && st.querySelector('.rankmap-bannerprev .bnr, .rankmap-gift.is-banner .bnr')); }""", timeout=6000)
        art = True
    except Exception:
        art = False
    check("and its banner art is drawn into the chip after the first paint", art)
    cen = s["centred"] if isinstance(s["centred"], list) else []
    # Centred on its own drawing. Build 232 also shrank and clipped them;
    # build 234 put the old size back ("the old road map looked so good"),
    # so only the centring is held to here.
    check("every road-map icon is centred in its circle",
          len(cen) == 7 and all(c["vb"] != "0 0 128 128" and c["dx"] <= 1 for c in cen), cen)
    check("the hero shows level and badges as two gauges, not a copy of the Profile card",
          isinstance(s["hero"], dict) and s["hero"]["gauges"] == 2 and not s["hero"]["bar"] and not s["hero"]["chips"], s["hero"])
    check("the badge case lining is not blue", isinstance(s["case"], list) and s["case"] and max(s["case"]) <= 12, s["case"])
    check("unit selection wears the results screen's mode chip", s["chip"] is True, s["chip"])
    check("an earned badge on a unit card glows in its own colour",
          isinstance(s["glow"], list) and s["glow"][0] == s["glow"][1], s["glow"])
    # The Practice Test briefing was checked here until build 283 retired
    # it (retired/practice-test.md); check_b283 asserts it is gone.
    check("a character's shoulders fade out rather than stopping at a hard line (build 233)",
          isinstance(s["fade"], str) and "linear-gradient" in s["fade"] and "transparent" in s["fade"].replace("rgba(0, 0, 0, 0)", "transparent"), s["fade"])
    check("the words 'Sync code' in Settings are blue", s["sync"] == "rgb(111, 194, 255)", s["sync"])

    # Home: a rank not reached is Liquid Glass, not a dark disc
    h = pg.evaluate("""()=>{ showHome(); const b = document.querySelector('.cosmic-icon-badge.cosmic-badge-rank:not(.cosmic-badge-lit):not(.cosmic-badge-noir)');
      if(!b) return null; const cs = getComputedStyle(b);
      return { bg: cs.backgroundColor, blur: cs.backdropFilter || cs.webkitBackdropFilter }; }""")
    glass = False
    if isinstance(h, dict):
        import re as _re
        m = _re.match(r"rgba\((\d+), (\d+), (\d+), ([\d.]+)\)", h["bg"] or "")
        glass = bool(m) and int(m.group(1)) >= 200 and float(m.group(4)) <= .2 and "blur" in (h["blur"] or "")
    check("an orbit bubble for a rank not reached is Liquid Glass again", glass, h)
    ctx.close()

    # Pause holds still when the page scrolls, level with the chat button.
    ctx, pg = booted(br, 390, 664, seed=USED_ACCOUNT)
    p = pg.evaluate("""async ()=>{
      const U = topicsIn(QUESTIONS)[0]; const ix = QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===U);
      cfg.mode='drill'; cfg.units=[U]; cfg.source='all'; runMode='drill'; beginRun(ix, null);
      for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await new Promise(r => setTimeout(r, 150));
      await new Promise(r => setTimeout(r, 900));
      const d = document.createElement('div'); d.style.height = '1500px'; document.querySelector('.qpanel').appendChild(d);
      const at = () => Math.round(document.querySelector('#pausebtn').getBoundingClientRect().top);
      const a = at(); window.scrollTo({ top: 400, behavior: 'instant' }); await new Promise(r => setTimeout(r, 300));
      return { rest: a, scrolled: at(), sy: Math.round(scrollY) }; }""")
    check("Pause stays where it is when a question scrolls, like the chat button",
          p["sy"] > 0 and p["rest"] == p["scrolled"], p)
    ctx.close()


def check_b234(br):
    """Build 234: the road map as it was, flipped; nothing in colour until
    it is yours; the first look after a rank-up; the start sheet made
    simple; Start dim until there is something to start. Written against
    build 233, where each of these fails."""
    print("\n18. build 234: road map, grey rewards, rank-up on the map, the start sheet, Start's colour")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const out = {};
      const T = async (k, f) => { try{ out[k] = await f(); }catch(e){ out[k] = 'THREW ' + e.message; } };
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const u = topicsIn(QUESTIONS); u.slice(0, 6).forEach(n => store.unitPerfects[n] = 999); levelOf = () => 40;
      // Gold held; the map has already shown Gold, so no show.
      store.rankMapSeen = 2;
      showProfile('ranks'); await wait(900);
      // Build 279 draws the map's character previews after first paint,
      // one a frame, so under load they can land after 900ms: wait for
      // the one this reads rather than reading a gap as "no filter".
      for(let i = 0; i < 40 && !document.querySelectorAll('.rankmap-stop')[4]?.querySelector('.rankmap-gift.is-char .rankmap-giftav svg'); i++) await wait(100);
      await T('grey', () => { const st = [...document.querySelectorAll('.rankmap-stop')];
        const f = (el) => el ? getComputedStyle(el).filter : null;
        return { reached: f(st[0].querySelector('.rankmap-dot')), next: f(st[3].querySelector('.rankmap-dot')),
                 lockedChar: f(st[4].querySelector('.rankmap-gift.is-char .rankmap-giftav svg')) }; });
      await T('novaPrev', () => { const st = [...document.querySelectorAll('.rankmap-stop')].pop();
        const b = st && st.querySelector('.rankmap-gift.is-banner .bnr');
        const chip = b && b.closest('.rankmap-gift'), other = st && st.querySelector('.rankmap-gift.is-theme');
        return b ? { h: Math.round(chip.getBoundingClientRect().height), other: Math.round(other.getBoundingClientRect().height),
                     filter: getComputedStyle(b).filter } : null; });
      await T('nodeSize', () => { const n = document.querySelector('.rankmap-node'); const sv = n.querySelector('svg');
        return Math.round(sv.getBoundingClientRect().width) - Math.round(n.getBoundingClientRect().width); });
      // A rank-up the map has not shown yet: Gold, last seen Bronze.
      store.rankMapSeen = 1; saveStore();
      showProfile('ranks'); await wait(300);
      await T('pendingAtFirst', () => { const g = [...document.querySelectorAll('.rankmap-stop')][2];
        return g.classList.contains('is-celebrate-pending'); });
      await wait(5200);
      await T('afterShow', () => ({ pending: document.querySelectorAll('.is-celebrate-pending').length, seen: store.rankMapSeen }));
      // Never opened on this build: set quietly, no show.
      store.rankMapSeen = null; showProfile('ranks'); await wait(300);
      await T('firstEver', () => ({ pending: document.querySelectorAll('.is-celebrate-pending').length, seen: store.rankMapSeen }));
      // Unit selection: Start is not white until a unit is picked.
      cfg.mode = 'drill'; showSetup(); await wait(600);
      await T('startNone', () => document.getElementById('bottomtab-start').classList.contains('is-inert'));
      const c = document.querySelector('.pick input'); c.checked = true; c.dispatchEvent(new Event('change', { bubbles:true })); await wait(200);
      await T('startOne', () => document.getElementById('bottomtab-start').classList.contains('is-inert'));
      // The start sheet.
      document.getElementById('nextbtn').click(); await wait(500);
      await T('sheet', () => {
        const sh = document.querySelector('.unitoptions-modal-sheet');
        const hm = sh.querySelector('.howmany-sect');
        const sl = hm && hm.querySelector('.slider');
        const defaults = [...sh.querySelectorAll('.sheet-summary-tags .sheet-tag')].map(t => t.textContent);
        const res = { defaults, chips: hm ? hm.querySelectorAll('.chip').length : -1, all: !!(hm && hm.querySelector('.slider-allbtn')),
                      caption: (sh.querySelector('.drawfrom-sect .bank-caption') || {}).textContent || '',
                      count: (sh.querySelector('.drawfrom-sect .bank-opt.on .bank-count') || {}).textContent || '',
                      name: (sh.querySelector('.drawfrom-sect .bank-opt.on .bank-name') || {}).textContent || '' };
        cfg.size = 0; if(sl){ sl.value = sl.min; sl.dispatchEvent(new Event('input', { bubbles:true })); }
        res.dragged = cfg.size; { const hn = sh.querySelector('.hundo-note'); res.warn = !hn.hidden && !hn.classList.contains('is-ok'); }
        if(sl){ sl.value = sl.max; sl.dispatchEvent(new Event('input', { bubbles:true })); }
        res.atEnd = cfg.size; { const hn = sh.querySelector('.hundo-note'); /* build 291: the line stays at All, as the quiet .is-ok one */ res.warnAtEnd = !hn.hidden && !hn.classList.contains('is-ok'); }
        const sw = sh.querySelectorAll('.timer-sect .opt input[type=checkbox]');
        res.timerSwitches = sw.length;
        if(sw[0]){ sw[0].checked = true; sw[0].dispatchEvent(new Event('change', { bubbles:true })); }
        res.timerAfter = cfg.timer;
        /* Build 250: Shuffle and Hide answers are their own card; the fold is the timer alone. */
        const mb = sh.querySelector('.more-body'), rows = sh.querySelector('.optionsmodal-body > .sect > .opt-rows');
        res.optsFolded = !!mb && !mb.classList.contains('open') && !mb.querySelector('.opt-rows') && !!rows && rows.querySelectorAll('.opt').length === 2
          && !!mb.querySelector('.timer-sect');
        cfg.timer = 'off';
        return res; });
      document.querySelector('.unitoptions-modal-scrim').click();
      // Themes: Bronze's second colour is not green, Amethyst's not pink.
      await T('themes', () => {
        const hue = h => { const n = parseInt(h.slice(1), 16), r = (n >> 16) / 255, g = (n >> 8 & 255) / 255, b = (n & 255) / 255;
          const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if(!d) return 0;
          let x = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return (x * 60 + 360) % 360; };
        const c3 = a => { document.documentElement.dataset.accent = a; const v = getComputedStyle(document.documentElement).getPropertyValue('--theme-c3').trim(); return Math.round(hue(v)); };
        // Build 244: Bronze is the rookie key now (it was ranger's).
        const res = { bronze: c3('rookie'), amethyst: c3('elite') };
        document.documentElement.dataset.accent = theme.accent || 'ink';
        return res; });
      return out; }""")
    g = r["grey"] if isinstance(r["grey"], dict) else {}
    check("a reward you have not reached is grey on the road map, and one you have is in colour",
          "grayscale" not in str(g.get("reached")) and "grayscale" in str(g.get("next")) and "grayscale" in str(g.get("lockedChar")), g)
    np_ = r["novaPrev"] if isinstance(r["novaPrev"], dict) else {}
    # Build 236: a chip the size of the other rewards, not a wide preview -
    # "I didn't mean to make that extremely large".
    check("Supernova's stop shows its banner as a reward chip like the others, in black and white until it is yours",
          np_.get("h", 99) <= np_.get("other", 0) + 2 and "grayscale" in str(np_.get("filter")), r["novaPrev"])
    # Build 243 reversed this: "the emblems on the road map are popping out
    # of their circles". Drawn a touch over the node and clipped to it.
    check("the road-map emblems sit inside their circles (build 243)",
          isinstance(r["nodeSize"], int) and -2 <= r["nodeSize"] <= 6, r["nodeSize"])
    check("a rank reached since the map last looked starts locked and is earned on screen",
          r["pendingAtFirst"] is True and isinstance(r["afterShow"], dict) and r["afterShow"]["pending"] == 0
          and r["afterShow"]["seen"] == 2, [r["pendingAtFirst"], r["afterShow"]])
    check("an account that never opened this build is not walked through ranks it already had",
          isinstance(r["firstEver"], dict) and r["firstEver"]["pending"] == 0 and r["firstEver"]["seen"] == 2, r["firstEver"])
    check("Start is not white until a unit is picked, and turns white the moment one is",
          r["startNone"] is True and r["startOne"] is False, [r["startNone"], r["startOne"]])
    sh = r["sheet"] if isinstance(r["sheet"], dict) else {}
    check("How many is one slider with an All button, no Everything/Custom chips",
          sh.get("chips") == 0 and sh.get("all") is True, sh)
    check("dragging below the end picks a number and warns; the far right is every question and does not",
          isinstance(sh.get("dragged"), int) and sh.get("dragged", 0) > 0 and sh.get("warn") is True
          and sh.get("atEnd") == 0 and sh.get("warnAtEnd") is False, sh)
    # Build 235: the chips became the Question bank, each row saying what it draws.
    # Build 249: the line under the switch says what the pool is; the
    # switch itself says how big ("the question bank stuff looks super
    # confusing" - the count moved out of the sentence and onto the choice).
    # Build 250: but not on "All questions" - "All questions / 48" beside
    # "All 48" under How many "doesn't even make sense".
    check("the Question bank's All questions carries no second count",
          sh.get("name") == "All questions" and sh.get("count", "") == "", sh)
    # Build 254: a default says nothing - no "All questions", "In order"
    # or "No timer" in the top box on an untouched run.
    check("on an untouched run the top box shows no defaults (All questions, In order, No timer)",
          not any(x in ("All questions", "In order", "No timer") for x in sh.get("defaults", ["?"])), sh.get("defaults"))
    check("the timer is two switches, and the first one sets a time limit",
          sh.get("timerSwitches") == 2 and sh.get("timerAfter") == "down", sh)
    # Build 249: "I need this app to be super simple and that start menu
    # doesn't look simple anymore" - the answer options fold into More options.
    # Build 250: "the shuffle answers and hide answers should not be in
    # that drop down. That drop down just needs to be the timer stuff."
    check("Shuffle and Hide answers are their own card; the fold holds only the timer, shut until opened", sh.get("optsFolded") is True, sh)
    th = r["themes"] if isinstance(r["themes"], dict) else {}
    check("Bronze's second colour is not green and Amethyst's is not pink",
          not (90 <= th.get("bronze", 120) <= 170) and not (290 <= th.get("amethyst", 330) <= 350), th)
    ctx.close()


def check_b235(br):
    """Build 235: the level label under its number; unlocks earned away
    from a results screen played on Home and flown into Profile; the
    Pharaoh handed to everyone already on Gold; the Rank reward strip;
    the Marksman; banners grouped by ladder; the rank banners; Bronze in
    wine; and the characters' states. Written against build 234, where
    each of these fails."""
    print("\n19. build 235: Home unlocks, Rank reward, Pharaoh, Marksman, banner order, character states")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const out = {};
      const T = async (k, f) => { try{ out[k] = await f(); }catch(e){ out[k] = 'THREW ' + e.message; } };
      const wait = ms => new Promise(r => setTimeout(r, ms));
      // The Profile card: "level" under its number, like "badges".
      showProfile('profile'); await wait(700);
      /* Build 282: the level is the Rank tab's ring with its number in
         the middle and "Level" in the box beside it - so: the number is
         centred in its ring, and the label is the box's, not the ring's. */
      await T('plate', () => { const f = document.querySelector('.profile-level-num.statring');
        const v = f.querySelector('.statring-num'); const lab = document.querySelector('.profile-level .rankhero-gaugelab');
        const a = f.getBoundingClientRect(), b = v.getBoundingClientRect();
        const off = Math.round(Math.max(Math.abs((a.left + a.width / 2) - (b.left + b.width / 2)), Math.abs((a.top + a.height / 2) - (b.top + b.height / 2))));
        return lab && lab.getBoundingClientRect().left >= a.right ? off : 'label not beside the ring'; });
      await T('heroLive', () => document.querySelector('.profile-hero-avatar').classList.contains('char-live'));
      // An existing account on Gold, opening this build for the first
      // time, then winning a week off-screen.
      const u = topicsIn(QUESTIONS); u.slice(0, 6).forEach(n => store.unitPerfects[n] = 999); levelOf = () => 40;
      store.weeklyWins = 0; store.pendingCharUnlocks = []; store.unlocksShown = null;
      await T('seed', () => { const s = ensureUnlocksShown(); return { pharaoh: s.chars.indexOf('solar') >= 0, gold: tierColorUnlocked('veteran') }; });
      /* Build 244: Silver's Lunar is new too and would queue first; this
         check is about Gold's own character, so Lunar is marked seen. */
      markUnlocksShown(['lunar'], []);
      store.weeklyWins = 1;
      showHome(); await wait(600);
      await T('notYet', () => !!document.querySelector('.rs-spot'));
      await wait(3400);
      await T('first', () => { const sp = document.querySelector('.rs-spot'); return sp ? sp.textContent : null; });
      document.querySelector('.rs-spot')?.click(); await wait(200);
      await T('flying', () => { const f = document.querySelector('body > .rs-fly'); if(!f) return null;
        const r = f.getBoundingClientRect(); return { y: Math.round(r.top), pos: getComputedStyle(f).position }; });
      await wait(700);
      await T('pulse', () => document.getElementById('bottomtab-profile').classList.contains('avatar-pulse'));
      await wait(1900);
      await T('second', () => { const sp = document.querySelector('.rs-spot'); if(!sp) return null;
        const st = sp.querySelector('.rs-spot-strip.is-rankreward');
        return { text: sp.textContent, strip: st ? st.textContent : null, emblem: !!(st && st.querySelector('svg')) }; });
      document.querySelector('.rs-spot') && document.querySelector('.rs-spot').click(); await wait(1400);
      await T('after', () => ({ spots: document.querySelectorAll('.rs-spot').length, left: pendingHomeUnlocks().chars.length }));
      showHome(); await wait(4200);
      await T('again', () => document.querySelectorAll('.rs-spot').length);
      // The Marksman: its bar in a row (100 until 246, 150 until 259, 200 until 291, 250 now), counted from the streak on record.
      await T('marksman', () => { const had = store.bestTestStreak, N = CHARACTER_FEATS.streak100.need; store.bestTestStreak = N - 1;
        const a = isLockedCharacter('marksman'); store.bestTestStreak = N; const b = isLockedCharacter('marksman');
        store.bestTestStreak = had; return [a, b]; });
      // The ladders sit together, easiest first.
      await T('order', () => BANNERS.map(b => b.id));
      await T('rankArt', () => ['adept_rank', 'elite_rank', 'titan_rank'].map(id => typeof BANNER_ART[id] === 'function' && !!bannerDef(id)));
      // The grade's reaction.
      await T('react', () => [{ isPerfect: true, pct: 100 }, { pct: 93 }, { pct: 75 }, { pct: 40 }].map(gradeReaction));
      // Asleep: a friend who is not on. Live: anybody else.
      store.friendsIn = ['pubsleepy'];
      openPersonSheet({ pub: 'pubsleepy', firstName: 'Sleepy', avatarChar: 'alien', seenAt: 1 }); await wait(300);
      await T('sleepFriend', () => { const a = document.querySelector('.person-card-art');
        return { sleep: a.classList.contains('char-sleep'), zzz: !!a.querySelector('.char-zzz') }; });
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      openPersonSheet({ pub: 'pubstranger', firstName: 'Stranger', avatarChar: 'alien', seenAt: 1 }); await wait(300);
      await T('liveStranger', () => { const a = document.querySelector('.person-card-art');
        return { live: a.classList.contains('char-live'), sleep: a.classList.contains('char-sleep') }; });
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      // Bronze is wine.
      // Build 244: Bronze is the rookie key now (it was ranger's).
      await T('bronze', () => { document.documentElement.dataset.accent = 'rookie';
        const v = getComputedStyle(document.documentElement).getPropertyValue('--theme-c3').trim();
        document.documentElement.dataset.accent = theme.accent || 'ink'; return v; });
      return out; }""")
    check("the level number sits centred in its ring on the Profile card, \"Level\" beside it (build 282)",
          isinstance(r["plate"], int) and r["plate"] <= 2, r["plate"])
    check("your own character is alive on the Profile card", r["heroLive"] is True, r["heroLive"])
    sd = r["seed"] if isinstance(r["seed"], dict) else {}
    check("an account already on Gold is NOT marked as having seen its rank character (Solar since 244)", sd.get("gold") is True and sd.get("pharaoh") is False, r["seed"])
    check("Home waits a beat before an unlock arrives", r["notYet"] is False, r["notYet"])
    check("Zeus, won away from any results screen, plays on Home as a finished challenge",
          isinstance(r["first"], str) and "Zeus" in r["first"] and r["first"].count("Challenge complete") == 1
          and "Character unlocked" in r["first"], r["first"])
    fl = r["flying"] if isinstance(r["flying"], dict) else {}
    check("tapping it away flies it to the Profile tab (fixed, above the screen) and rings the tab",
          fl.get("pos") == "fixed" and 0 < fl.get("y", -1) < 956 and r["pulse"] is True, [r["flying"], r["pulse"]])
    sc = r["second"] if isinstance(r["second"], dict) else {}
    check("Gold's character (Solar since 244) follows as a Rank reward, with Gold's emblem and name in the strip",
          "Solar" in str(sc.get("text")) and "Rank reward" in str(sc.get("strip")) and "Gold" in str(sc.get("strip"))
          and sc.get("emblem") is True, r["second"])
    af = r["after"] if isinstance(r["after"], dict) else {}
    check("each plays once: nothing left afterwards, nothing on the next visit",
          af.get("spots") == 0 and af.get("left") == 0 and r["again"] == 0, [r["after"], r["again"]])
    check("the Marksman unlocks at its bar in a row and not before", r["marksman"] == [True, False], r["marksman"])
    o = r["order"] if isinstance(r["order"], list) else []
    def run(ids):
        at = [o.index(i) if i in o else -99 for i in ids]
        return all(b == a + 1 for a, b in zip(at, at[1:]))
    check("banners of one ladder sit next to each other, easiest first",
          run(["tests100", "tests250", "tests500"])
          and run(["hundos100", "hundos250"]) and run(["adept_rank", "elite_rank", "titan_rank"]), o)
    check("Sapphire and Amethyst have banners of their own beside Supernova's", r["rankArt"] == [True, True, True], r["rankArt"])
    # A lost game was a fifth case until Game mode went (build 283).
    check("the results character reacts to 100 / 90+ / a pass / a miss",
          r["react"] == ["perfect", "great", "pass", "fail"], r["react"])
    check("a friend who is offline is asleep on their card, Zzz and all",
          r["sleepFriend"] == {"sleep": True, "zzz": True}, r["sleepFriend"])
    check("anybody else - a classmate opened from the Leaderboard - is simply alive",
          r["liveStranger"] == {"live": True, "sleep": False}, r["liveStranger"])
    check("Bronze's theme is wine", str(r["bronze"]).lower() == "#6b2140", r["bronze"])
    ctx.close()


def check_b235b(br):
    """Build 235, second list: the road map evenly spaced and two-sided on
    a phone; the Question bank; the summary tags; the timer's label;
    Most missed capped at 15% of each unit; holding a unit card for its
    details. Written against build 234, where each of these fails."""
    print("\n20. build 235: road map pitch, question bank, unit details")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const out = {};
      const T = async (k, f) => { try{ out[k] = await f(); }catch(e){ out[k] = 'THREW ' + e.message; } };
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const u = topicsIn(QUESTIONS); u.slice(0, 6).forEach(n => store.unitPerfects[n] = 999); levelOf = () => 40;
      store.rankMapSeen = 2; showProfile('ranks'); await wait(900);
      await T('pitch', () => { const n = [...document.querySelectorAll('.rankmap-node')].map(e => Math.round(e.getBoundingClientRect().top));
        const d = n.slice(1).map((y, i) => y - n[i]); return { min: Math.min(...d), max: Math.max(...d) }; });
      await T('sides', () => { const c = [...document.querySelectorAll('.rankmap-card')].map(e => e.getBoundingClientRect());
        const mid = innerWidth / 2; return c.map(r => r.right < mid ? 'L' : r.left > mid ? 'R' : 'X').join(''); });
      // Most missed: at most 15% of each unit.
      const unit = u[0], n = unitQuestionCount(unit), now = Date.now();
      QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === unit) store.stats[KEYS[i]] = { n: 3, m: 3, r: [now - 1000, now - 2000] }; });
      /* build 284: Flagged is the one bank besides All, so give it something */
      store.flagged = store.flagged || {}; QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === unit && Object.keys(store.flagged).length < 3) store.flagged[KEYS[i]] = true; });
      await T('cap', () => ({ n, got: recentMissedIndexes().filter(i => (QUESTIONS[i].topic || '').trim() === unit).length, cap: Math.max(1, Math.round(n * .15)) }));
      // A unit WITH a best time, so the check can fail.
      store.testStats[unit] = Object.assign({}, store.testStats[unit] || {}, { label: unit, plays: 5, totalMs: 1e6, bestMs: 250000 });
      cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(600);
      await T('noBest', () => document.querySelectorAll('.pick .pbest').length);
      await T('hint', () => !!document.querySelector('.picks-holdhint'));
      const box = [...document.querySelectorAll('.pick input')].find(x => x.value === unit);
      if(box){ box.checked = true; box.dispatchEvent(new Event('change', { bubbles: true })); } await wait(200);
      document.getElementById('nextbtn')?.click(); await wait(600);
      await T('bank', () => { const rows = [...document.querySelectorAll('.bank-opt')];
        const cap = document.querySelectorAll('.bank-sect .bank-caption');
        return { rows: rows.map(r => r.dataset.value), bare: rows.every(r => !r.querySelector('.bank-desc') && !r.querySelector('.bank-ico')),
                 oneLine: cap.length === 1 && (cap[0].textContent || '').length > 12,
                 label: (document.querySelector('.bank-sect .slab') || {}).textContent }; });
      document.querySelector('.bank-opt[data-value="flagged"]')?.click(); await wait(200);
      await T('bankInfo', () => { const c = document.querySelector('.bank-caption');
        return { info: !!document.querySelector('.bank-info, .bank-infobody'), shown: !!c && !c.hidden, len: c ? (c.textContent || '').trim().length : 0 }; });
      cfg.timer = 'down'; cfg.timerMinutes = 20; document.querySelector('.bank-opt[data-value="flagged"]')?.click(); await wait(200);
      await T('tags', () => { const ts = [...document.querySelectorAll('.sheet-summary .sheet-summary-tags .sheet-tag')];
        const card = (document.querySelector('.unitoptions-modal-sheet .more-toggle') || {}).parentElement;
        return { tags: ts.length, texts: ts.map(t => t.textContent), icons: ts.every(t => !!t.querySelector('svg')),
                 cardGreen: !!card && card.classList.contains('is-set'),
                 green: (() => { const p = ts.find(t => /min limit|Stopwatch|min countdown|Tracking time/.test(t.textContent)); if(!p) return false;
                   const m = (getComputedStyle(p).borderTopColor.match(/[\d.]+/g) || []).map(Number);
                   return p.classList.contains('is-set') && m.length >= 3 && m[1] > m[0] + 80 && m[1] > m[2] + 60; })(),
                 state: (document.querySelector('.more-toggle-state') || {}).textContent || '' }; });
      await T('timerLabel', () => (document.querySelector('.more-toggle') || {}).textContent || '');
      document.querySelector('.unitoptions-modal-scrim')?.click(); await wait(400);
      // Hold a unit card.
      const row = [...document.querySelectorAll('.pick')].find(r => (r.querySelector('input') || {}).value === unit);
      const was = row.querySelector('input').checked;
      if(row) row.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 50, clientY: 50, button: 0 }));
      await wait(600);
      row.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 50, clientY: 50 }));
      row.click(); await wait(600);
      await T('detail', () => { const d = document.querySelector('.unitdetail'); if(!d) return null;
        const r = d.getBoundingClientRect();
        return { stats: [...d.querySelectorAll('.unitdetail-statlab')].map(e => e.textContent),
                 doors: d.querySelectorAll('.unitdetail-door').length, w: Math.round(r.width),
                 unticked: row.querySelector('input').checked === was }; });
      document.querySelector('.unitdetail-door.is-flagged')?.click(); await wait(600);
      await T('list', () => ({ qs: document.querySelectorAll('.unitdetail-list .unitdetail-q').length,
                               flags: document.querySelectorAll('.unitdetail-list .unitdetail-flag').length }));
      /* Build 270: Most missed has no flags; the Flagged list keeps them,
         and check_b270 asserts that with a fixture that has flags. */
      document.querySelector('.unitdetail-back')?.click(); await wait(500);
      document.querySelector('.unitdetail-scrim')?.click(); await wait(700);
      await T('closed', () => !document.querySelector('.unitdetail') && !document.querySelector('.unitdetail-scrim'));
      return out; }""")
    p = r["pitch"] if isinstance(r["pitch"], dict) else {}
    check("every stretch of road on the map is the same length", p.get("max", 99) - p.get("min", 0) <= 2 and p.get("min", 0) > 150, r["pitch"])
    check("on a phone the ranks sit either side of the road, like the iPad", r["sides"] == "LRLRLRL", r["sides"])
    cp = r["cap"] if isinstance(r["cap"], dict) else {}
    # (Most missed's 15% cap was checked here; the bank went in build 284.)
    check("no best time on the unit cards", r["noBest"] == 0, r["noBest"])
    check("the unit screen says a card can be held", r["hint"] is True, r["hint"])
    b = r["bank"] if isinstance(r["bank"], dict) else {}
    # Build 249: one three-way switch and ONE line under it, not three
    # cards each with a paragraph ("the question bank stuff looks super
    # confusing"). Build 250: and that line is SHORT, with no "i" and no
    # paragraph behind it ("the description for most missed is way too
    # much") - 249 had both, and fails this.
    bi = r.get("bankInfo") if isinstance(r.get("bankInfo"), dict) else {}
    # Build 284: two banks - All questions and Flagged; Most missed is gone.
    check("the Question bank: All questions and Flagged, one short line under Flagged - no info dot",
          b.get("rows") == ["all", "flagged"] and b.get("bare") and b.get("oneLine")
          and bi.get("shown") and 0 < bi.get("len", 0) <= 45 and not bi.get("info")
          and b.get("label") == "Question bank", [b, bi])
    t = r["tags"] if isinstance(r["tags"], dict) else {}
    # Build 250: the settings are back in the top box ("still needs to
    # say the settings of the test from that menu, in the top like
    # before just make it better"): one word and one icon per setting,
    # and NO count among them - "All questions" beside "All 48" was the
    # thing that "doesn't even make sense". The Timer bar still says its
    # own state without opening.
    tx = t.get("texts", []) if isinstance(t, dict) else []
    # Build 254: and ONLY what is switched on - "if they are in order,
    # don't show that ... If there's no timer, don't show that either ...
    # And if it's all questions, don't show that."
    check("the top box lists only the settings that are on, each with an icon, and no question count",
          isinstance(t, dict) and t.get("icons") and "20 min countdown" in tx and "Flagged" in tx
          and not any(x in ("All questions", "In order", "No timer") for x in tx)
          and not any(x.startswith("All ") and x[4:].isdigit() for x in tx) and not any(" of " in x for x in tx)
          and "20 min countdown" in t.get("state", ""), t)
    # Build 250/251: "I need this to go green when you change it" - then
    # "that box turning green is kinda weird. Don't do that. I like how
    # the timer thing at the top is green though." The pill, not the card.
    check("a timer that is on turns its pill in the top box green, and not the Timer card",
          isinstance(t, dict) and t.get("green") is True and t.get("cardGreen") is False, t)
    check("the fold is called Timer", str(r["timerLabel"]).startswith("Timer"), r["timerLabel"])
    d = r["detail"] if isinstance(r["detail"], dict) else {}
    check("holding a unit card opens its details without ticking it",
          d.get("unticked") is True and d.get("doors") == 1 and "Completed" in d.get("stats", []) and "Last score" in d.get("stats", [])
          and "Hundos" in d.get("stats", []) and d.get("w", 0) > 300, r["detail"])
    l = r["list"] if isinstance(r["list"], dict) else {}
    # REVISED IN 270: "When looking at your most missed, remove the flag
    # option." Flagging is done from the Flagged list, which keeps it.
    check("Flagged opens inside the card (its only door since build 284)", l.get("qs", 0) >= 1, r["list"])
    check("tapping off it closes it", isinstance(r["detail"], dict) and r["closed"] is True, r["closed"])
    ctx.close()


def check_b236(br):
    """Build 236: rank banners as reward chips; the road blending rank to
    rank with a light at your progress; black shades; carved panels under
    the socle symbols; the unit list's search, flag and resets; Virtual
    Room podiums only from four people, and its stats. Written against
    build 235, where each of these fails."""
    print("\n21. build 236: road map chips and light, art, unit list tools, Virtual Room podium")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const out = {};
      const T = async (k, f) => { try{ out[k] = await f(); }catch(e){ out[k] = 'THREW ' + e.message; } };
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const u = topicsIn(QUESTIONS); u.slice(2, 8).forEach(n => store.unitPerfects[n] = 999); levelOf = () => 40;
      store.rankMapSeen = 2; showProfile('ranks'); await wait(2200);
      await T('chips', () => ({ prev: document.querySelectorAll('.rankmap-bannerprev').length,
                                chips: document.querySelectorAll('.rankmap-gift.is-banner').length }));
      await T('road', () => { const rs = [...document.querySelectorAll('.rankmap-road')];
        return { blended: rs.length > 0 && rs.every(x => !!x.style.getPropertyValue('--from-color')),
                 tip: document.querySelectorAll('.rankmap-roadtip').length }; });
      /* Build 244 removed the Officer outright; an old id is drawn as the
         character that inherited its rank, the Oracle. */
      await T('shades', () => { const sv = buildAvatarCharSVGSafe('officer');
        return ((sv.querySelector('.cx-fig') || {}).getAttribute ? sv.querySelector('.cx-fig').getAttribute('class') : '') || ''; });
      /* build 265/266: Poseidon's id drew Anubis, then the Kraken, neither
         with a carved panel - only Zeus keeps one, and the id is asserted
         to draw the Kraken. */
      await T('panels', () => ['zeus'].map(k => [...buildAvatarCharSVGSafe(k).querySelectorAll('rect')]
        .some(x => /^#(13263A|0C2E30)$/i.test(x.getAttribute('fill') || ''))).concat(
        /cx-k-sheriff/.test((buildAvatarCharSVGSafe('poseidon').querySelector('.cx-fig') || {getAttribute(){return ''}}).getAttribute('class') || '')));
      // The unit list.
      const unit = u[0], now = Date.now();
      let k = 0;
      QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === unit){ k++; store.stats[KEYS[i]] = { n: 3, m: 3, r: [now - 1000, now - 2000] }; if(k <= 3) store.flagged[KEYS[i]] = true; } });
      cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(600);
      const row = [...document.querySelectorAll('.pick')].find(r => (r.querySelector('input') || {}).value === unit);
      if(row) row.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 50, clientY: 50, button: 0 }));
      await wait(600); if(row) row.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 50, clientY: 50 })); await wait(700);
      await T('copy', () => ({ doors: [...document.querySelectorAll('.unitdetail-doorsub')].map(e => e.textContent),
        hundoSub: [...document.querySelectorAll('.unitdetail-stat')].filter(c => /Hundos/.test(c.textContent)).map(c => c.querySelector('.unitdetail-statsub').textContent)[0] }));
      document.querySelector('.unitdetail-door.is-flagged')?.click(); await wait(700);
      await T('list', () => { const d = document.querySelector('.unitdetail');
        const bar = d.querySelector('.unitdetail-head .pick-stars');
        return { listing: d.classList.contains('is-listing'), barHidden: !bar || getComputedStyle(bar).display === 'none',
                 search: !!d.querySelector('.unitdetail-search input'), testFlag: !!d.querySelector('.unitdetail-q .flagbtn .flagbanner'),
                 qs: d.querySelectorAll('.unitdetail-q').length }; });
      await T('search', async () => { const i = document.querySelector('.unitdetail-search input');
        i.value = 'zzzzqqq'; i.dispatchEvent(new Event('input')); await wait(100);
        const none = document.querySelectorAll('.unitdetail-q').length;
        document.querySelector('.unitdetail-searchclear')?.click(); await wait(100);
        return { none, back: document.querySelectorAll('.unitdetail-q').length }; });
      await T('reset', async () => { document.querySelector('.unitdetail-resetbtn')?.click(); await wait(100);
        const warned = !document.querySelector('.unitdetail-confirm').hidden;
        const before = flaggedIndexes().length;
        document.querySelector('.unitdetail-confirmyes')?.click(); await wait(200);
        return { warned, before, after: flaggedIndexes().filter(i => (QUESTIONS[i].topic || '').trim() === unit).length }; });
      document.querySelector('.unitdetail-back')?.click(); await wait(500);
      /* build 284: no Most missed door to clear */
      await T('clearMissed', () => document.querySelectorAll('.unitdetail-door.is-recent').length);
      document.querySelector('.unitdetail-scrim')?.click(); await wait(600);
      // The Virtual Room podium.
      await T('vr', () => {
        store.vrTop3 = 0; store.vrTop3Rooms = []; store.vrCounted = [];
        recordVroomOutcome('R3', ['a', 'me', 'b'], 'me');
        const small = store.vrTop3;
        recordVroomOutcome('R4', ['a', 'b', 'me', 'c'], 'me');
        recordVroomOutcome('R4', ['a', 'b', 'me', 'c'], 'me');
        return { places: [vroomPlaces(2), vroomPlaces(3), vroomPlaces(4), vroomPlaces(8)], small, big: store.vrTop3 }; });
      showProfile('stats'); await wait(700);
      await T('stats', () => [...document.querySelectorAll('.profile-stats-tab .stat-lab')].map(e => e.textContent));
      return out; }""")
    c = r["chips"] if isinstance(r["chips"], dict) else {}
    check("the rank banners are reward chips, not wide previews", c.get("prev") == 0 and c.get("chips") == 3, r["chips"])
    rd = r["road"] if isinstance(r["road"], dict) else {}
    check("the road blends from rank to rank, with a light where you are", rd.get("blended") is True and rd.get("tip") == 1, r["road"])
    check("the Officer is gone: an old Officer is drawn as the Oracle (build 244)", "cx-k-oracle" in str(r["shades"]), r["shades"])
    # REVISED IN 271-273: the Kraken became the Kitsune, the Vampire, then the Sheriff.
    check("Zeus's symbol sits on a dark carved panel, and Poseidon's id draws the Sheriff", r["panels"] == [True, True], r["panels"])
    cp = r["copy"] if isinstance(r["copy"], dict) else {}
    check("the doors say what they open, and Hundos says nothing about the badge",
          cp.get("doors") == ["Tap to see flagged questions"]
          and "badge" not in (cp.get("hundoSub") or "").lower(), r["copy"])
    l = r["list"] if isinstance(r["list"], dict) else {}
    check("the list drops the badge bar, has a search, and the in-test flag",
          l.get("listing") and l.get("barHidden") and l.get("search") and l.get("testFlag") and l.get("qs") == 3, r["list"])
    check("search filters and Clear brings everything back", r["search"] == {"none": 0, "back": 3}, r["search"])
    rs = r["reset"] if isinstance(r["reset"], dict) else {}
    check("unflagging the unit asks first, then does it", rs.get("warned") and rs.get("before", 0) >= 3 and rs.get("after") == 0, r["reset"])
    check("there is no Most missed door to clear (build 284)", r["clearMissed"] == 0, r["clearMissed"])
    v = r["vr"] if isinstance(r["vr"], dict) else {}
    check("a podium only from four people; top three counts once, and never in a room of three",
          v.get("places") == [1, 1, 3, 3] and v.get("small") == 0 and v.get("big") == 1, r["vr"])
    st = r["stats"] if isinstance(r["stats"], list) else []
    check("Stats has a Virtual Room section with first places and top threes",
          "First-place finishes" in st and "Top-3 finishes" in st, st)
    ctx.close()


def check_b237(br):
    """Build 237: the rank on the Profile card is a plate - the emblem, the
    rank's name large, and a bar to the next rank with its percentage.
    Written against build 236, where it was a small pill."""
    print("\n22. build 237: the Profile rank plate")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const u = topicsIn(QUESTIONS); u.slice(2, 8).forEach(n => store.unitPerfects[n] = 999); levelOf = () => 40;
      showProfile('profile'); await wait(2000);
      const p = document.querySelector('.profile-rankplate');
      if(!p) return null;
      const fill = p.querySelector('.profile-rankplate-fill');
      return { word: (p.querySelector('.profile-rankword') || {}).textContent,
               next: (p.querySelector('.profile-rankplate-next') || {}).textContent,
               fill: fill ? Math.round(fill.getBoundingClientRect().width) : -1,
               w: Math.round(p.getBoundingClientRect().width),
               coin: Math.round((p.querySelector('.profile-rankcoin') || { getBoundingClientRect: () => ({ width: 0 }) }).getBoundingClientRect().width),
               button: p.tagName }; }""")
    check("the rank is a plate across the card, not a pill", isinstance(r, dict) and r.get("w", 0) > 300 and r.get("coin", 0) >= 50 and r.get("button") == "BUTTON", r)
    # REVISED IN 267: "the current rank in the profile box has a progress
    # bar, let's remove that" - the plate names the rank and nothing else.
    check("it names the rank, with no bar under it", isinstance(r, dict) and r.get("word") == "Gold"
          and not r.get("next") and r.get("fill", 0) == -1, r)
    ctx.close()


def check_b238(br):
    """Build 238: the unit details' best time says it comes from a hundo,
    so people know how to set one. Written against build 237, where it
    read "100% drill, whole unit" and "Fastest 100%"."""
    print("\n23. build 238: best time says hundo")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{ const u = topicsIn(QUESTIONS)[0];
      const find = (m, l) => (unitDetailStats(u, m).find(x => x.label === l) || {});
      store.testStats[u] = store.testStats[u] || {}; delete store.testStats[u].bestMs;
      const unset = find('drill', 'Best time').sub;
      store.testStats[u].bestMs = 95000; const set = find('drill', 'Best time').sub;
      const exam = unitDetailStats(u, 'exam').map(x => x.label + ' ' + x.sub).join(' | ');
      return { unset, set, exam }; }""")
    # REVISED IN 270: the card is the same four in every mode (best score,
    # last score, completed, hundos), so no mode shows a time any more.
    check("no mode shows a best time any more (Drill included)", isinstance(r, dict)
          and r.get("unset") is None and r.get("set") is None, r)
    # Build 240 took the time off Exam altogether ("Best exam" and "Exam
    # average" instead), so the hundo wording is only asserted where a time
    # is still shown. A decision that changed, not a regression.
    check("Exam shows no time either", isinstance(r, dict) and "Best time" not in str(r.get("exam"))
          and "Fastest" not in str(r.get("exam")), r)
    ctx.close()


def check_b240_units(br):
    """Build 240: every mode's unit details are four squares in the same
    order (Completed, two for the mode, Hundos) with the mode named in the
    header. Game shows the level unlocked and the farthest reached on it,
    and a time only once Hardcore is beaten; Exam shows its best and its
    average.
    Written against build 239, where the order and labels differed per
    mode and Game showed a best time."""
    print("\n26. build 240: unit details, one order per mode")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{ const u = topicsIn(QUESTIONS)[0];
      const labs = m => unitDetailStats(u, m).map(x => x.label);
      const out = { modes: {} };
      // 'game' left this list with Game mode (build 283).
      ['drill','exam','review','vroom'].forEach(m => out.modes[m] = labs(m));
      if(typeof store.unitExam === 'object') delete store.unitExam[u];
      store.testHistory = (store.testHistory || []).filter(h => !(h.mode === 'exam' && h.units && h.units.length === 1 && h.units[0] === u));
      store.testHistory.unshift({ units: [u], pct: 80, mode: 'exam', playedAt: Date.now() - 1e6 });
      store.testHistory.unshift({ units: [u], pct: 60, mode: 'exam', playedAt: Date.now() });
      if(store.unitExam) delete store.unitExam[u];
      out.exam = unitDetailStats(u, 'exam').map(x => x.label + '=' + x.value + ' ' + x.sub);
      return out; }""")
    modes = (r or {}).get("modes", {}) if isinstance(r, dict) else {}
    firsts = {m: (v[0] if v else None) for m, v in modes.items()}
    lasts = {m: (v[-1] if v else None) for m, v in modes.items()}
    # REVISED IN 268: "it says drill at the top, but really some of that
    # stuff shows up across any mode". Four every-mode squares, always the
    # same and in the same order, then only the mode's own ones.
    # REVISED AGAIN IN 270: "Let's make these so it's the same for any mode
    # so it's simple to use" - one card of four, identical in every mode.
    # The shape is asserted (same four everywhere, one of them the last
    # score), not each label.
    first = next(iter(modes.values()), [])
    check("every mode shows the same four squares", modes and len(first) == 4 and all(v == first for v in modes.values()), modes)
    check("and one of them is the last score", any("Last" in x for x in first), first)
    ex = " | ".join(r.get("exam", [])) if isinstance(r, dict) else ""
    check("the best and the last score come from past runs (80% best, 60% last)",
          "=80%" in ex and "Last score=60%" in ex, ex)
    # The header names the mode: open a real card on the Exam unit grid.
    pg.evaluate("()=>{ cfg.mode = 'exam'; cfg.units = []; showSetup(); }")
    pg.wait_for_timeout(700)
    chip = pg.evaluate("""()=>{ const row = document.querySelector('.pick');
      if(!row) return 'no row';
      row.dispatchEvent(new MouseEvent('contextmenu', {bubbles:true, cancelable:true}));
      const c = document.querySelector('.unitdetail-mode'); return c ? c.textContent : 'no chip'; }""")
    # REVISED IN 268/270: the card is the same in every mode, so it names none.
    check("the details card names no mode - it is the same in every mode", chip == "no chip", chip)
    ctx.close()


def check_b239(br):
    """Build 239: presence and chat. Written against build 238, where
    Friends dropped its own presence listener on its own mount, a chat
    with only somebody else present said "Just you so far", and people
    already in a chat were offered a live Invite button."""
    print("\n24. build 239: presence and chat")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const out = {};
      /* A minimal Firestore that counts presence subscriptions. */
      let subs = 0, unsubs = 0;
      const doc = () => ({ onSnapshot(n){ subs++; return () => { unsubs++; }; },
        update(){ return Promise.resolve(); }, set(){ return Promise.resolve(); },
        get(){ return Promise.resolve({ exists:false, data:()=>({}) }); } });
      fbDb = { collection: () => ({ doc, onSnapshot(){ return () => {}; },
        get(){ return Promise.resolve({ forEach(){}, size:0, metadata:{} }); } }) };
      detachPresence();
      showFriends(); await wait(300);
      out.afterFriends = !!presenceUnsub;
      showProfile('profile'); await wait(300);
      out.afterProfile = !!presenceUnsub;
      showHome(); await wait(300);
      out.afterHome = !!presenceUnsub;

      /* The roster says "just you" only when the one person is you. */
      const box = document.createElement('div'); box.id = 'chatdock-roomwho'; document.body.appendChild(box);
      chatMyKey = 'ME-1';
      renderChatRoster({ 'AL-1': { name: 'Alex', joinedAt: 1 } });
      out.otherOnly = box.textContent;
      renderChatRoster({ 'ME-1': { name: 'Me', joinedAt: 1 } });
      out.meOnly = box.textContent;
      box.remove();

      chatRoomCode = 'ROOM-A';

      /* Somebody already in the chat is not offered Invite. */
      chatAllMembers = { 'ME-1': {}, 'BO-1': {} };
      friendPublicIds = () => ['BO-1'];
      openChatInviteSheet(); await wait(200);
      const b = document.querySelector('.invite-sheet .friend-act');
      out.memberButton = b ? { text: b.textContent, disabled: b.disabled } : null;
      document.querySelector('.invite-overlay')?.remove();
      chatRoomCode = null;
      return out; }""")
    check("Friends keeps its presence listener after it mounts", r.get("afterFriends") is True, r)
    check("and Profile keeps it too", r.get("afterProfile") is True, r)
    check("and leaving for Home lets it go", r.get("afterHome") is False, r)
    check("a chat with only somebody else in it does not say 'Just you'",
          "Just you" not in str(r.get("otherOnly")) and "Just you" in str(r.get("meOnly")), r)
    check("a member already in the chat is not offered Invite",
          isinstance(r.get("memberButton"), dict) and r["memberButton"]["disabled"]
          and "In chat" in r["memberButton"]["text"], r)
    ctx.close()


def check_b241(br):
    """Build 241: Madison's second review list. Every check here was run
    against the build-240 page and fails there."""
    print("\n28. build 241: glass bubbles, no rank coin, profile, banner pop-up")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const units = topicsIn(QUESTIONS);
      store.lifetime.points = 260000;
      units.slice(0, 6).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
      ensureUnlocksShown(); markUnlocksShown(announceableHeldCharacters(), BANNERS.filter(x=>bannerEarned(x.id)).map(x=>x.id));
      store.rankMapSeen = 99;
      /* 1. a lit orbit bubble is glass, not a dark coin */
      showHome(); await wait(600);
      const lit = document.querySelector('.cosmic-badge-rank.cosmic-badge-lit');
      out.litBlur = lit ? getComputedStyle(lit).backdropFilter || getComputedStyle(lit).webkitBackdropFilter : null;
      out.lens = lit ? getComputedStyle(lit, '::after').content : null;
      /* 2. no rank coin, anywhere decorateAvatar is asked */
      const a = document.createElement('span'); decorateAvatar(a, 70, 14, 0);
      out.coin = a.childNodes.length;
      /* 3. profile: one level plate, a badges section, a one-colour rank bar */
      showProfile('profile'); await wait(900);
      /* build 282: the plate is the Rank tab's ring, plain */
      out.plates = document.querySelectorAll('.profile-level .statring').length;
      /* Build 243: the badge row is the badges themselves, no meter. */
      out.badgeCells = document.querySelectorAll('.profile-badgesect .badge-meter-seg').length;
      out.badgeEarned = document.querySelectorAll('.profile-badgesect .profile-badgestack-token').length;
      const fill = document.querySelector('.profile-rankplate-fill');
      out.fillBg = fill ? getComputedStyle(fill).backgroundImage : '';
      out.nextColor = RANK_COLOR.vanguard;
      /* 4. a banner pop-up is centred on the screen */
      const d = bannerDef('tests100'); d.have = () => d.need;
      showHome(); scheduleHomeUnlocks(50);
      for(let i = 0; i < 30 && !document.querySelector('.rs-spot.is-up'); i++) await wait(150);
      await wait(1400);
      const sp = document.querySelector('.rs-spot .rs-spot-card');
      const rr = sp ? sp.getBoundingClientRect() : null;
      out.spot = rr ? { x: Math.round(rr.left + rr.width / 2), y: Math.round(rr.top), w: Math.round(rr.width), vw: innerWidth } : null;
      } catch(e){ out.threw = String(e); }
      return out; }""")
    check("a lit orbit bubble is glass with a lens", isinstance(r, dict) and "blur" in str(r.get("litBlur"))
          and r.get("lens") not in (None, "none", "normal"), r)
    check("no rank coin is hung on any character", isinstance(r, dict) and r.get("coin") == 0, r)
    # REVERSED IN 258: "I don't want to see my badge icons there at all."
    # The section stays; the earned badges drawn in it do not.
    check("Profile: one level plate, and badges are their own section, with no badge icons in it",
          isinstance(r, dict) and r.get("plates") == 1 and r.get("badgeCells") == 0 and r.get("badgeEarned") == 0, r)
    def hexrgb(h):
        h = h.lstrip("#"); return "rgb(%d, %d, %d)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    # REVISED IN 267: there is no rank bar on the plate any more.
    check("the rank plate carries no bar at all", isinstance(r, dict) and not r.get("fillBg"), r)
    sp = (r or {}).get("spot") if isinstance(r, dict) else None
    check("a banner pop-up sits in the middle of the screen, on screen",
          bool(sp) and abs(sp["x"] - sp["vw"] / 2) <= 4 and sp["y"] >= 0 and sp["w"] > 250, r)
    ctx.close()


def check_b241b(br):
    """Build 241, second half: the Eclipse character and its one-day
    challenge, a hundo that gets the character's own move, theme names,
    banners that stay still, and Tug of War read from your own end with a
    pull cutscene. Each was run against build 240 and fails there."""
    print("\n29. build 241: Eclipse, theme names, still banners, the tug rope")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      /* 1. Eclipse sits after the Marksman, and is locked to begin with */
      const ids = AVATAR_CHARACTERS.map(c => c.id);
      /* Build 243: Blitz is retired and the Astronaut took its challenge
         ("Astronaut takes Blitz's spot"), so the same rules are asked of it. */
      const wasChar = store.avatarChar; store.avatarChar = 'ninja';
      out.blitzAt = ids.indexOf('astronaut') - ids.indexOf('marksman');
      store.hundoDay = null; store.hundoDayBest = 0;
      out.lockedAtStart = isLockedCharacter('astronaut');
      out.msg = characterLockMessage('astronaut');
      out.astroName = AVATAR_DISPLAY_NAME.astronaut;
      /* 2. N different units in one day (7 until build 259, 5 now - read
         off the app, not written down here), and only different ones */
      const N = CHARACTER_FEATS.hundo7day.need; out.need = N;
      const units = topicsIn(QUESTIONS);
      for(let i = 0; i < N - 1; i++) noteHundoDay(units[i]);
      noteHundoDay(units[0]); noteHundoDay(units[1]);
      out.sixDistinct = hundoDayCount();
      out.lockedAtSix = isLockedCharacter('astronaut');
      /* a new day starts the list again but keeps the best day */
      store.hundoDay.day = '2000-01-01';
      noteHundoDay(units[N]);
      out.newDay = { today: store.hundoDay.units.length, best: store.hundoDayBest, locked: isLockedCharacter('astronaut') };
      for(let i = 0; i < N; i++) noteHundoDay(units[i]);
      out.lockedAtSeven = isLockedCharacter('astronaut');
      /* it survives a round trip through the cloud loader */
      const saved = JSON.parse(JSON.stringify(store));
      applyLoadedData(saved);
      out.afterLoad = store.hundoDayBest;
      /* 3. the drawing (Blitz since build 242): a racer, not a flare -
         a visor with a sunset in it, and no black body */
      store.avatarChar = wasChar;
      /* An old Blitz id still draws as the character that took its place. */
      const svg = buildAvatarCharSVG('blitz');
      out.corona = (svg.querySelector('.cx-fig').getAttribute('class') || '').indexOf('cx-k-' + (AVATAR_CHARACTERS.find(c => c.id === 'astronaut') || {}).kind) >= 0 ? 7 : 0;
      out.parts = ['cx-head', 'cx-eyes'].filter(c => svg.querySelector('.' + c)).length * 2;
      /* 4. theme swatches carry their names (Profile > Customize) */
      showCustomize(); await wait(500);
      const names = [...document.querySelectorAll('.swatch-cell .swatch-name')].map(e => e.textContent);
      out.names = names;
      out.swatches = document.querySelectorAll('.swatch-cell').length;
      /* 5. only the hardest banners animate */
      out.stillCommon = buildBannerArt('tests100').classList.contains('is-still');
      out.stillTop = buildBannerArt('level80').classList.contains('is-still');
      /* 6. Tug of War from your own end */
      const d = { startAt: 1, participants: { A: { name: 'Ann', avatarChar: 'robot' }, B: { name: 'Bo', avatarChar: 'ninja' } },
                  tug: { count: 20, over: false, finalPos: 0, teams: { A: 'a', B: 'b' }, progress: { A: { pos: 3, correct: 3, pull: 3.6 }, B: { pos: 1, correct: 1 } } } };
      const was = vroomMyKey;
      vroomMyKey = 'A'; const va = tugView(d);
      vroomMyKey = 'B'; const vb = tugView(d);
      out.view = { a: [va.lead, va.pct < 50], b: [vb.lead, vb.pct > 50], oldPull: tugPullOf(d.tug.progress.B) };
      const wrap = buildTugRope(d);
      out.ends = { us: (wrap.querySelector('.tug-team-us .tug-team-fig') || {}).title, them: (wrap.querySelector('.tug-team-them .tug-team-fig') || {}).title,
                   lines: wrap.querySelectorAll('.tug-winline').length, state: (wrap.querySelector('.tug-state') || {}).textContent };
      /* 7. the pull cutscene: says who, hands over, skips when muted */
      d.tug.over = true; d.tug.winner = 'b'; d.tug.finalPos = -5;
      let handed = 0;
      theme.muteBanners = false; theme.reduceMotion = false;
      playTugPullCutscene(d, () => { handed++; });
      await wait(400);
      const cut = document.getElementById('vroom-cutscene');
      out.cut = cut ? { cls: cut.className, line: (cut.querySelector('.tug-cut-line') || {}).textContent } : null;
      await wait(3800);
      out.cutHanded = handed; out.cutGone = !document.getElementById('vroom-cutscene');
      theme.muteBanners = true; let muted = 0;
      playTugPullCutscene(d, () => { muted++; });
      out.muted = muted; theme.muteBanners = false;
      vroomMyKey = was;
      } catch(e){ out.threw = String(e); }
      return out; }""")
    # The astronaut id draws the Cyborg since 271; the name is read off the page.
    check("the astronaut id (Blitz's challenge since 243) sits right after the Marksman, locked, with its challenge and progress",
          isinstance(r, dict) and r.get("blitzAt") == 1 and r.get("lockedAtStart") is True
          and r.get("msg") == "Get a hundo in %d different units in one day (0 of %d) to unlock %s." % (r.get("need"), r.get("need"), r.get("astroName")), r)
    check("only different units count, and one short is not enough",
          r.get("sixDistinct") == r.get("need", 0) - 1 and r.get("lockedAtSix") is True, r)
    check("a new day starts again but keeps the best day",
          r.get("newDay") == {"today": 1, "best": r.get("need", 0) - 1, "locked": True}, r)
    check("the full count in one day unlocks it, and the best day survives a reload",
          r.get("lockedAtSeven") is False and (r.get("afterLoad") or 0) >= r.get("need", 99), r)
    check("an old Blitz id draws as whatever the astronaut id draws, on the parts every character has",
          r.get("corona") == 7 and r.get("parts") == 4, r)
    check("every theme swatch has its name under it, Default first",
          r.get("swatches", 0) >= 7 and len(r.get("names") or []) == r.get("swatches") and (r.get("names") or [""])[0] == "Default", r)
    check("a common banner stays still and level 80 moves",
          r.get("stillCommon") is True and r.get("stillTop") is False, r)
    check("the rope is read from your own end on both devices",
          r.get("view", {}).get("a") == ["us", True] and r.get("view", {}).get("b") == ["them", True], r)
    check("a device that publishes no pull still counts its right answers",
          r.get("view", {}).get("oldPull") == 1, r)
    # Drawn as Bo, who is on side b: Bo holds the left end.
    check("your team holds the left end and theirs the right, whatever side you are",
          r.get("ends", {}).get("us") == "Bo" and r.get("ends", {}).get("them") == "Ann", r)
    check("and there is a line to drag it past at each end",
          r.get("ends", {}).get("lines") == 2, r)
    check("the pull cutscene says which side took it",
          bool(r.get("cut")) and "tug-cut" in r["cut"]["cls"] and r["cut"]["line"] in ("They pulled it over", "Your side pulled it over"), r)
    check("and hands over to the result, once, and clears itself",
          r.get("cutHanded") == 1 and r.get("cutGone") is True, r)
    check("muteBanners skips it and still hands over", r.get("muted") == 1, r)
    ctx.close()


def check_b242(br):
    """Build 242: Madison's list after 241. Every check here was run
    against the build-241 page and fails there."""
    print("\n30. build 242: badges, the case, pop-ups, characters, Customize, the account move")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const units = topicsIn(QUESTIONS);
      store.lifetime.points = 260000;
      units.slice(0, 6).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
      store.unitPerfects[units[7]] = 2;
      ensureUnlocksShown(); markUnlocksShown(announceableHeldCharacters(), BANNERS.filter(x=>bannerEarned(x.id)).map(x=>x.id));
      store.rankMapSeen = 99;
      /* 1. what friends are doing is one colour */
      const a1 = document.createElement('span'); a1.className = 'friend-activity-line'; a1.dataset.activity = 'drill';
      const a2 = document.createElement('span'); a2.className = 'friend-activity-line'; a2.dataset.activity = 'lobby';
      document.body.append(a1, a2);
      out.actColours = [getComputedStyle(a1).color, getComputedStyle(a2).color];
      a1.remove(); a2.remove();
      /* 2. the two friend-code boxes are the same object */
      showFriends(); await wait(300);
      const bx = sel => { const e = document.querySelector(sel), c = getComputedStyle(e), r = e.getBoundingClientRect();
        return [Math.round(r.width), Math.round(r.height), c.backgroundColor, c.borderRadius, c.fontSize]; };
      out.codeBoxes = [bx('.friend-mycode'), bx('.friend-add-input')];
      out.codeBoxBg = getComputedStyle(document.querySelector('.friend-mycode')).backgroundColor;
      /* 3. Profile: a meter and the closest badge, not the whole set */
      showProfile('profile'); await wait(900);
      out.profile = { strip: document.querySelectorAll('.profile-badgesect .badge-strip-cell').length,
        segs: document.querySelectorAll('.profile-badgesect .badge-meter-seg').length,
        stack: document.querySelectorAll('.profile-badgesect .profile-badgestack-token').length };
      /* 4. the rank box: a full-width bar, the next rank as a chip, what is left */
      const bar = document.querySelector('.profile-rankplate-bar'), col = document.querySelector('.profile-rankplate-text');
      out.rankBox = { bar: !!bar,
        chip: !!document.querySelector('.profile-rankplate-next .profile-rankplate-nextmark svg'),
        need: !!document.querySelector('.profile-rankplate-need'),
        label: (document.querySelector('.profile-rankplate-next') || {}).textContent || '' };
      /* 5. the Badges tab: a meter at the top, and a case with a lid and clasps */
      showProfile('badges'); await wait(900);
      out.badgesTab = { strip: document.querySelectorAll('.badges-head .badge-strip-cell').length,
        segs: document.querySelectorAll('.badges-head .badge-meter-seg').length,
        /* build 282: the medal is the Rank tab's gold ring; the count is
           still struck into the middle of it */
        medal: (document.querySelector('.badges-head .statring .statring-num') || {}).textContent || '',
        lid: !!document.querySelector('.badge-case .badge-case-lid .badge-case-plate'),
        clasps: document.querySelectorAll('.badge-case .badge-case-front span').length,
        earned: String(badgesEarnedList().length) };
      /* 6. an earned badge: no printed grain, and a shadow in its slot */
      const bsvg = buildUnitBadgeSVG(units[0], true);
      out.badgeArt = { hatch: bsvg.querySelectorAll('pattern').length,
        shadow: !![...bsvg.querySelectorAll('path')].find(p => p.getAttribute('fill') === 'rgba(0,0,0,.42)') };
      /* 7. every pop-up the same size, a challenge banner with its strip, and visible with Reduce motion */
      showHome(); await wait(300);
      theme.reduceMotion = true; applyTheme();
      const card = js => { document.querySelectorAll('.rs-spot').forEach(e => e.remove()); playUnlockSpotlight(js, 1, 1, () => {});
        const c = document.querySelector('.rs-spot-card'); return c; };
      let c = card(bannerUnlockItem('tests100')); await wait(700);
      out.spotBanner = { w: Math.round(c.getBoundingClientRect().width), strip: !!document.querySelector('.rs-spot .rs-spot-strip'),
        opacity: getComputedStyle(c).opacity };
      c = card(characterUnlockItem('marksman')); await wait(700);
      out.spotChar = { w: Math.round(c.getBoundingClientRect().width), opacity: getComputedStyle(c).opacity };
      c = card(characterUnlockItem('solar')); await wait(700);  // Gold's since 244
      const strip = document.querySelector('.rs-spot-strip.is-rankreward');
      out.rankStripOnScreen = strip ? Math.round(strip.getBoundingClientRect().left) < innerWidth && Math.round(strip.getBoundingClientRect().right) > 0 : false;
      document.querySelectorAll('.rs-spot').forEach(e => e.remove());
      theme.reduceMotion = false; applyTheme();
      /* 8. the character fades out at the bottom wherever it is drawn */
      const holder = document.createElement('span'); holder.className = 'rank-avatar';
      holder.appendChild(buildAvatarCharSVG('ninja')); document.body.appendChild(holder);
      const m = getComputedStyle(holder.querySelector('svg'));
      out.fade = (m.maskImage || m.webkitMaskImage || 'none');
      holder.remove();
      /* 9. the Queen and the Dragon are the Wizard now */
      const saved = JSON.parse(JSON.stringify(store)); saved.avatarChar = 'queen';
      applyLoadedData(saved); out.queenBecomes = store.avatarChar;
      out.dragonDrawnAs = buildAvatarCharSVG('dragon').querySelector('.cx-k-wizard') ? 'wizard' : 'other';
      showWelcomeCharacterPrompt(); await wait(500);
      out.starters = [...document.querySelectorAll('.charselect-panel .avatarchar-option')].filter(o => o.offsetParent).length;
      out.starterCols = getComputedStyle(document.querySelector('.charselect-panel .avatarchar-grid')).gridTemplateColumns.split(' ').length;
      /* 10. Customize: colours before banners, and big enough to sit beside them */
      store.onboardingComplete = true;
      showCustomize(); await wait(600);
      const sw = document.querySelector('.screen-customize .swatches'), bg = document.querySelector('.screen-customize .banner-grid');
      out.custom = { order: sw && bg ? !!(sw.compareDocumentPosition(bg) & Node.DOCUMENT_POSITION_FOLLOWING) : null,
        swatch: Math.round(document.querySelector('.screen-customize .swatch').getBoundingClientRect().width) };
      } catch(e){ out.threw = String(e) + ' ' + (e.stack || '').split('\\n')[1]; }
      return out; }""")
    check("what friends are doing is one colour, whatever they are doing",
          isinstance(r, dict) and len(set(r.get("actColours") or [1, 2])) == 1, r)
    cb = r.get("codeBoxes") or [[0], [1]]
    # REVERSED IN 243: "the text box needs to look like the other text
    # boxes ... the one for copy just needs to be better, maybe because
    # it's in the weird similar bubble thing and shouldn't be". The code
    # is text now, not a pill, and the field is the app's ordinary one,
    # wider than the code.
    check("your code is plain text and the field you type in is an ordinary, wider text box",
          r.get("codeBoxBg") in ("rgba(0, 0, 0, 0)", "transparent") and cb[1][0] > cb[0][0], [cb, r.get("codeBoxBg")])
    p = r.get("profile") or {}
    # REVERSED IN 243: "the profile box, still not a fan of the badge
    # thing. There doesn't need to be a progress bar like that." A count
    # and the badges you hold, and no meter.
    # AND AGAIN IN 258: no badge icons on the card at all.
    check("Profile shows the count with no meter, no set and no badge icons",
          p.get("strip") == 0 and p.get("segs") == 0 and p.get("stack") == 0, p)
    rb = r.get("rankBox") or {}
    # REVERSED IN 243: "the profile box got worse somehow ... it was so
    # good before" - back to the 241 plate: one bar and "Gold · 35%".
    # REVISED IN 267: the bar came off the plate ("no need for that").
    check("the rank plate carries no bar, no chip and no to-do line",
          not rb.get("bar") and not rb.get("chip") and not rb.get("need") and rb.get("label", "") == "", rb)
    bt = r.get("badgesTab") or {}
    # REVERSED IN 243: the meter was "terrible, all I wanted was a better
    # way to show it than the 0/16" - a medal with the number in it.
    # The number is the app's own earned count, not a literal: it was "6"
    # until the 279 bands made the same fixture worth 7 badges.
    # AND IN 282: the medal became the Rank tab's ring, number inside.
    check("the Badges tab heads with its count in a ring, no meter, and sits in a case with a lid and two clasps",
          bt.get("strip") == 0 and bt.get("segs") == 0 and bt.get("medal") == bt.get("earned") and bt.get("medal") not in ("", "0") and bt.get("lid") and bt.get("clasps") == 2, bt)
    ba = r.get("badgeArt") or {}
    check("an earned badge has no printed grain and throws a shadow into its slot",
          ba.get("hatch") == 0 and ba.get("shadow") is True, ba)
    sb, sc = r.get("spotBanner") or {}, r.get("spotChar") or {}
    check("a banner pop-up is the same size as a character's and carries its challenge strip",
          sb.get("w") and sb.get("w") == sc.get("w") and sb.get("strip") is True, [sb, sc])
    check("with Reduce motion on, a pop-up is still visible, rank strip and all",
          sb.get("opacity") == "1" and sc.get("opacity") == "1" and r.get("rankStripOnScreen") is True, r)
    check("a character fades out at the bottom wherever it is drawn", "gradient" in str(r.get("fade")), r.get("fade"))
    check("the Queen becomes the Wizard, and a Dragon anywhere is drawn as one",
          r.get("queenBecomes") == "wizard" and r.get("dragonDrawnAs") == "wizard", r)
    # 243: "go ahead and remove the samurai character as well. Let's make
    # it only 5 starter characters."
    check("sign-up offers five starters, three across",
          r.get("starters") == 5 and r.get("starterCols") == 3, [r.get("starters"), r.get("starterCols")])
    cu = r.get("custom") or {}
    check("Customize puts the colours before the banners, at a size that holds up beside them",
          cu.get("order") is True and cu.get("swatch", 0) >= 56, cu)
    ctx.close()

    # 11. the account move
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const docs = {
        'ABCD-EFGH__moved': { to: 'JKLM-NPQR', at: 1 },
        'JKLM-NPQR': Object.assign(JSON.parse(JSON.stringify(store)), { firstName: 'Cap', publicId: 'pubcap000001', lastModified: 5 })
      };
      const writes = [];
      const ref = id => ({ id,
        get(){ return Promise.resolve({ exists: !!docs[id], data: () => docs[id], ref: ref(id) }); },
        set(d, o){ writes.push([id, d]); docs[id] = Object.assign({}, (o && o.merge) ? docs[id] : {}, d); return Promise.resolve(); },
        update(){ return Promise.resolve(); }, delete(){ return Promise.resolve(); },
        onSnapshot(){ return () => {}; } });
      fbDb = { collection: () => ({ doc: ref, onSnapshot(){ return () => {}; },
               get(){ return Promise.resolve({ forEach(){}, size: 0, metadata: {} }); } }) };
      const retired = [];
      const realRetire = retireLeaderboardEntry;
      retireLeaderboardEntry = pub => { retired.push(pub); };
      store.publicId = 'pubdup000001'; store.firstName = 'Capitaan';
      syncCode = 'ABCD-EFGH'; accountMoveChecked = '';
      checkAccountMove('ABCD-EFGH'); await wait(300);
      out.code = syncCode; out.name = store.firstName; out.pub = store.publicId;
      out.retired = retired; out.done = !!(docs['ABCD-EFGH__moved'] || {}).done;
      /* a note already followed is not followed again, and a code with no note is left alone */
      syncCode = 'ZZZZ-2222'; accountMoveChecked = ''; checkAccountMove('ZZZZ-2222'); await wait(200);
      out.noNote = syncCode;
      retireLeaderboardEntry = realRetire;
      } catch(e){ out.threw = String(e); }
      return out; }""")
    check("a device on a moved account is signed into the real one, cloud copy and all",
          r.get("code") == "JKLM-NPQR" and r.get("name") == "Cap" and r.get("pub") == "pubcap000001", r)
    check("the duplicate's rankings row is retired and the note is marked done",
          (r.get("retired") or [None])[0] == "pubdup000001" and "pubcap000001" not in (r.get("retired") or [])
          and r.get("done") is True, r)
    check("a code with no note is left exactly where it is", r.get("noNote") == "ZZZZ-2222", r)
    ctx.close()


def check_b243(br):
    """Build 243: Madison's list after 242. Written against the build-242
    page and every check fails there."""
    print("\n31. build 243: five starters, new rank characters, secrets, unlock cards, banner ladders")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const def = id => AVATAR_CHARACTERS.find(c => c.id === id) || {};
      /* 1. the table */
      out.starters = AVATAR_CHARACTERS.filter(c => !c.unlock && !c.feat && !c.retired && !c.legacy).map(c => c.id);
      out.ranks = TIER_ORDER_FULL.map(k => (AVATAR_CHARACTERS.find(c => c.unlock === k) || {}).id || null);
      /* build 244: the Hacker took the K-9's hours, the Timekeeper is new,
         the Valkyrie took the Spartan's wins, and SWAT is its own secret. */
      out.feats = { clown: def('clown').feat, astronaut: def('astronaut').feat, hacker: def('hacker').feat, timekeeper: def('timekeeper').feat,
                    valkyrie: def('valkyrie').feat, swatRetired: def('swat').retired === true };
      out.retiredTo = ['samurai', 'champion', 'blitz', 'pharaoh', 'officer', 'spartan', 'k9', 'paladin', 'sentinel', 'pirate', 'scholar', 'wolf', 'swat'].map(id => (buildAvatarCharSVG(id).querySelector('.cx-fig').getAttribute('class') || '').replace('cx-fig cx-k-', ''));
      out.names = ['lunar', 'solar', 'tempest', 'frost', 'oracle', 'inferno', 'hacker', 'timekeeper', 'valkyrie'].map(id => AVATAR_DISPLAY_NAME[id]);
      /* 2. kept from before */
      const saved = JSON.parse(JSON.stringify(store)); delete saved.legacyChars;
      const realT = tierColorUnlocked;
      window.tierColorUnlocked = k => ['rookie', 'ranger', 'veteran', 'vanguard', 'adept'].indexOf(k) >= 0;
      applyLoadedData(saved);
      out.kept = store.legacyChars.slice().sort();
      /* Build 244: nobody can have the Robot, whatever they held. */
      out.robotHeld = store.legacyChars.indexOf('robot') >= 0;
      window.tierColorUnlocked = realT;
      store.legacyChars = [];
      out.robotNew = (buildAvatarCharSVG('robot').querySelector('.cx-fig').getAttribute('class') || '').indexOf('cx-k-ninja') >= 0;
      /* 3. Customize: groups, five across, names on one line */
      store.onboardingComplete = true;
      showCustomize(); await wait(700);
      out.groups = [...document.querySelectorAll('.screen-customize .avatarchar-group-title')]
        .filter(h => h.nextElementSibling && h.nextElementSibling.classList.contains('avatarchar-grid'))
        .map(h => h.firstChild && h.firstChild.textContent);
      const grid = document.querySelector('.screen-customize .avatarchar-grid');
      out.cols = getComputedStyle(grid).gridTemplateColumns.split(' ').length;
      out.twoLine = [...document.querySelectorAll('.screen-customize .avatarchar-name')].filter(n => n.getBoundingClientRect().height > 18).map(n => n.textContent);
      out.robotShown = !!document.querySelector('.screen-customize .avatarchar-option[aria-label="Robot"]');
      out.tileNeeds = [...document.querySelectorAll('.screen-customize .banner-opt-need')].map(e => e.textContent);
      out.defaultTile = (document.querySelector('.screen-customize .banner-opt.is-none .banner-opt-name') || {}).textContent;
      out.shadesTile = !!document.querySelector('.screen-customize .banner-opt[data-banner="shades"]');
      /* 4. the swatches preview what they are */
      const dot = n => { const d = document.querySelectorAll('.screen-customize .swatch .dot')[ACCENTS.indexOf(n)]; return d ? getComputedStyle(d).backgroundImage : ''; };
      out.defaultDot = dot('ink'); out.goldDot = dot('veteran');
      /* 5. a locked thing opens a card with a bar */
      const lockedBanner = document.querySelector('.screen-customize .banner-opt.locked[data-banner="tests100"]');
      lockedBanner.click(); await wait(400);
      out.bannerCard = { card: !!document.querySelector('.unlock-card'), bar: !!document.querySelector('.unlock-card .unlock-card-bar'),
        fill: getComputedStyle(document.querySelector('.unlock-card .unlock-card-fill') || document.body).backgroundImage,
        count: (document.querySelector('.unlock-card-count') || {}).textContent || '' };
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      [...document.querySelectorAll('.screen-customize .swatch.locked')].pop().click(); await wait(400);
      out.themeCard = { desc: (document.querySelector('.unlock-card-desc') || {}).textContent || '',
        note: (document.querySelector('.unlock-card-note') || {}).textContent || '' };
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      /* 6. the default banner is the theme, for somebody else too */
      const art = buildWornBannerArt('', 'adept');
      out.defaultBanner = { cls: art.className, accent: art.dataset.accent };
      openPersonSheet({ pub: 'pubzz0000001', firstName: 'Zed', avatarChar: 'ninja', level: 3, badges: 0, accent: 'elite', banner: '' }); await wait(300);
      const pc = document.querySelector('.person-card-cover .bnr');
      out.personCover = pc ? pc.className + '|' + (pc.dataset.accent || '') : '';
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      /* 7. the SWAT hunt is over (build 245, "remove the swat one
         entirely"): even an account whose turn has come never gets the
         item, a saved SWAT loads as the Ninja, and no banner is left. */
      store.shadesFound = false; store.shadesAt = testsCompletedOf(store) + 1;
      order = QUESTIONS.map((q, i) => i).slice(0, 12); mysteryAppearsAtPos = -1;
      const seen = []; for(let i = 0; i < 3; i++){ maybeStartShadesForRun(); seen.push(shadesAppearsAtPos); }
      out.swatNeverPlaced = seen.every(p => p === -1);
      const savedChar = store.avatarChar;
      applyLoadedData(Object.assign(JSON.parse(JSON.stringify(store)), { avatarChar: 'swat' }));
      out.swatLoadsAs = store.avatarChar; store.avatarChar = savedChar;
      out.bannerAfter = !bannerDef('shades') && !bannerEarned('shades');
      store.shadesAt = null;
      /* 8. banner ladders */
      const still = id => buildBannerArt(id).classList.contains('is-still');
      /* the Game ladder (easy10/average10/hardcore10) was removed in build 284 */
      out.ladders = { first: ['tests100', 'hundos100', 'adept_rank'].map(still),
        rest: ['tests250', 'tests500', 'hundos250', 'elite_rank', 'titan_rank'].map(still) };
      /* build 244: Hall of Fame is a ring of the badges round a medal, drawn
         twice (behind and in front of it) - so count the distinct badges. */
      /* Hall of Fame (badges16) was removed in build 284 */
      out.bannerNames = ['level80', 'study50', 'correct5000'].map(id => (bannerDef(id) || {}).name);
      /* build 244: the two new banners count what they say, from what is already kept. */
      const wasLife = store.lifetime.correct, wasLog = store.studyLog;
      store.lifetime.correct = 4999; const c1 = bannerEarned('correct5000');
      store.lifetime.correct = 5000; const c2 = bannerEarned('correct5000');
      /* 35 hours since build 289 (was 50) */
      store.studyLog = { '2026-01-01': 34.9 * 3600000 }; const s1 = bannerEarned('study50');
      store.studyLog = { '2026-01-01': 20 * 3600000, '2026-01-02': 15 * 3600000 }; const s2 = bannerEarned('study50');
      store.lifetime.correct = wasLife; store.studyLog = wasLog;
      out.newBanners = [c1, c2, s1, s2];
      /* 9. the road map keeps its emblems inside the ring */
      showProfile('ranks'); await wait(900);
      const em = document.querySelector('.rankmap-node > svg.rank-emblem-svg');
      out.mapClip = em ? getComputedStyle(em).clipPath : '';
      /* 10. the friend field is the app's ordinary one, the width of the card */
      showFriends(); await wait(300);
      const f = document.querySelector('.friend-add-input'), row = document.querySelector('.friend-add-row');
      out.fieldShare = f && row ? Math.round(f.getBoundingClientRect().width / row.getBoundingClientRect().width * 100) : 0;
      } catch(e){ out.threw = String(e) + ' ' + (e.stack || '').split('\\n')[1]; }
      return out; }""")
    check("five starters: Ninja, Ghost, Wizard, Bear, Alien",
          isinstance(r, dict) and r.get("starters") == ["ninja", "ghost", "wizard", "grizzly", "alien"], r)
    # Build 244 moved these on: six rank characters from the second rank
    # up, the Scholar/Wolf/Pirate challenges and SWAT as its own secret.
    check("a new character on each rank from the second up, in rank order",
          r.get("ranks") == [None, "lunar", "solar", "tempest", "frost", "oracle", "inferno"], r.get("ranks"))
    check("the Clown is five wins, the Astronaut hundos in a day, the Hacker time studied, the Timekeeper days studied, the Valkyrie the Virtual Room, and SWAT is retired (build 245)",
          r.get("feats") == {"clown": "vrwins5", "astronaut": "hundo7day", "hacker": "study20h", "timekeeper": "days30",
                             "valkyrie": "studyrun7", "swatRetired": True}, r.get("feats"))
    # Kinds, not ids: Blitz goes to the astronaut id, which draws the Phantom since 278.
    check("every retired character is drawn as what replaced it",
          r.get("retiredTo") == ["ninja", "clown", "starblade", "solar", "oracle", "koi", "hacker", "solar", "tempest", "koi", "hacker", "timekeeper", "ninja"], r.get("retiredTo"))
    # build 265/267: the Valkyrie's id drew the Viper, then the Koi (and the characters retired into it).
    check("the new ones are named", r.get("names") == ["Lunar", "Solar", "Tempest", "Frost", "Oracle", "Inferno", "Hacker", "Timekeeper", "Koi"], r.get("names"))
    check("whoever held the Clown under the old ranks keeps it, and nobody at all has the Robot (build 244) - an old Robot is drawn as the Ninja",
          r.get("kept") == ["clown"] and r.get("robotHeld") is False and r.get("robotNew") is True, r)
    check("Customize groups the characters, secrets on their own, and no Robot for somebody who never held it",
          r.get("groups") == ["Starters", "Rank rewards", "Challenge rewards", "Secrets"] and r.get("robotShown") is False, r.get("groups"))
    check("five across on a phone, and every name on one line",
          r.get("cols") == 5 and r.get("twoLine") == [], [r.get("cols"), r.get("twoLine")])
    # Build 246: every tile carries its requirement (was the default's line only).
    check("every banner tile says what it takes, and the secret one is not listed until found",
          (r.get("tileNeeds") or [None])[0] == "Matches your theme" and len(r.get("tileNeeds") or []) > 10
          and r.get("defaultTile") == "Default" and r.get("shadesTile") is False, r)
    check("the Default circle is the default theme and the Gold circle is gold",
          # Build 244 made Gold yellower: #F5C21B, not #E9B43A.
          "255, 211, 122" in (r.get("defaultDot") or "") and "245, 194, 27" in (r.get("goldDot") or ""), [r.get("defaultDot"), r.get("goldDot")])
    bc = r.get("bannerCard") or {}
    check("a locked banner opens a card with a progress bar and a count, not 0/1 text on the tile",
          bc.get("card") and bc.get("bar") and " of 100" in bc.get("count", ""), bc)
    # build 279: "change the locked progress bar and make that the green
    # color like how the unlock ones got" - a locked card's bar is the
    # held card's green (#2FBF71 at its deepest stop), not the old blue.
    check("a locked card's progress bar is the same green as a held one's",
          "47, 191, 113" in bc.get("fill", "") and "61, 139, 255" not in bc.get("fill", ""), bc.get("fill"))
    tc = r.get("themeCard") or {}
    check("a locked theme says the rank it needs and the rank you hold",
          tc.get("desc", "").startswith("Reach ") and ("right now" in tc.get("note", "") or "rank yet" in tc.get("note", "")), tc)
    check("the default banner is somebody's own theme, on their person card too",
          (r.get("defaultBanner") or {}).get("accent") == "adept" and "bnr-theme" in (r.get("defaultBanner") or {}).get("cls", "")
          and r.get("personCover", "").endswith("|elite"), r)
    # Build 245: SWAT removed entirely - the character, the item and the hunt.
    check("the SWAT item is never placed in a test, even when an account's turn has come (build 245)",
          r.get("swatNeverPlaced") is True, r.get("swatNeverPlaced"))
    check("a saved SWAT loads as the Ninja, and there is no Undercover banner",
          r.get("swatLoadsAs") == "ninja" and r.get("bannerAfter") is True, [r.get("swatLoadsAs"), r.get("bannerAfter")])
    lad = r.get("ladders") or {}
    # Build 246: the rank ladder is the exception - all three rank banners
    # move ("All 3 of the rank banners ... Ensure all 3 of them are
    # animated"), so its first rung, Sapphire (the 4th entry), moves too.
    check("the first banner of every ladder is still, bar the rank banners, and every one above it moves",
          lad.get("first") == [True, True, False] and lad.get("rest") == [False] * 5, lad)
    check("the redone and new banners are named", r.get("bannerNames") == ["Ascension", "Midnight Oil", "Star Trails"], r.get("bannerNames"))
    check("Star Trails at 5,000 right answers and Midnight Oil at 50 hours studied (build 244)",
          r.get("newBanners") == [False, True, False, True], r.get("newBanners"))
    check("the road map cuts each emblem to the inside of its ring", "circle" in (r.get("mapClip") or ""), r.get("mapClip"))
    check("the friend field runs most of the card", (r.get("fieldShare") or 0) >= 60, r.get("fieldShare"))
    ctx.close()


def check_b244(br):
    """Build 244: Bronze first, Silver second, a yellow Gold; new emblems for
    the first three that move like the rest; emblems centred in their
    circles. Written against the build-243 page, where every check fails."""
    print("\n32. build 244: Bronze/Silver/Gold, living emblems, centred in their circles")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const K = TIER_ORDER_FULL.slice();
      out.names = K.map(k => RANK_DISPLAY_NAME[k]);
      out.themes = K.map(k => ACCENT_DISPLAY_NAME[k]);
      const rgb = h => { const n = parseInt(String(h).slice(1), 16); return [n >> 16, n >> 8 & 255, n & 255]; };
      const hue = h => { const [r, g, b] = rgb(h).map(v => v / 255), mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
        if(!d) return 0; let x = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return (x * 60 + 360) % 360; };
      out.goldHue = Math.round(hue(RANK_COLOR.veteran));
      /* seven flares, none of them black and no two alike */
      const fl = K.map(k => rgb(flareColorOf(k)));
      out.flareMinLum = Math.min(...fl.map(c => Math.round(.2126 * c[0] + .7152 * c[1] + .0722 * c[2])));
      let md = 999; fl.forEach((a, i) => fl.forEach((b, j) => { if(j > i) md = Math.min(md, Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])); }));
      out.flareMinDist = Math.round(md);
      /* alive where you look at one, still where there are forty */
      const host = document.createElement('div'); host.className = 'rk-live'; host.style.cssText = 'position:fixed;left:0;top:0;width:60px';
      K.forEach(k => { const e = buildRankEmblemSVG(k); e.style.cssText = 'width:60px;height:60px;display:block'; host.appendChild(e); });
      const col = document.createElement('span'); col.className = 'rank-col-emblem'; col.appendChild(buildRankEmblemSVG('rookie'));
      document.body.append(host, col); await wait(200);
      const running = el => el.getAnimations({ subtree: true }).filter(a => /^rk-/.test(a.animationName)).length;
      out.alive = [...host.children].map(running);
      out.still = running(col);
      document.documentElement.dataset.reduceMotion = 'true'; await wait(100);
      out.reduced = running(host);
      delete document.documentElement.dataset.reduceMotion; host.remove(); col.remove();
      /* centred: the drawn ink's box against the circle, in Home's bubbles and the Profile coin */
      const ink = {};
      for(const k of K){
        const svg = buildRankEmblemSVG(k); svg.setAttribute('width', '256'); svg.setAttribute('height', '256');
        svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        const img = new Image(); await new Promise(r => { img.onload = r; img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(svg)); });
        const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d');
        x.fillStyle = '#000'; x.fillRect(0, 0, 256, 256); x.drawImage(img, 0, 0);
        const d = x.getImageData(0, 0, 256, 256).data; let x0 = 256, y0 = 256, x1 = -1, y1 = -1;
        for(let y = 0; y < 256; y++) for(let xx = 0; xx < 256; xx++){ const i = (y * 256 + xx) * 4;
          if(Math.max(d[i], d[i + 1], d[i + 2]) > 30){ x0 = Math.min(x0, xx); x1 = Math.max(x1, xx); y0 = Math.min(y0, y); y1 = Math.max(y1, y); } }
        ink[k] = [(x0 + x1) / 4, (y0 + y1) / 4];
      }
      const off = (circ, svg, k) => { const r = svg.getBoundingClientRect(), c = circ.getBoundingClientRect(), vb = svg.viewBox.baseVal;
        const sc = Math.min(r.width / vb.width, r.height / vb.height);
        const x = r.left + (r.width - vb.width * sc) / 2 + (ink[k][0] - vb.x) * sc, y = r.top + (r.height - vb.height * sc) / 2 + (ink[k][1] - vb.y) * sc;
        return Math.round(Math.hypot(x - (c.left + c.width / 2), y - (c.top + c.height / 2)) * 10) / 10; };
      showHome(); await wait(900); document.getAnimations().forEach(a => a.pause());
      out.home = [...document.querySelectorAll('.cosmic-icon-badge.cosmic-badge-rank')].map((b, i) => off(b, b.querySelector('svg'), K[i]));
      store.lifetime.points = Math.max(store.lifetime.points || 0, 0);
      /* build 268: an unranked plate draws no emblem at all, so the coin is
         measured on an account that holds a rank */
      const rk0 = rankOf; rankOf = () => 'ranger';
      showProfile('profile'); await wait(900); document.getAnimations().forEach(a => a.pause());
      const coin = document.querySelector('.profile-rankplate .profile-rankcoin'), held = 'ranger';
      out.coin = coin && coin.querySelector('svg') ? { fitted: coin.querySelector('svg').classList.contains('is-fitted'), off: off(coin, coin.querySelector('svg'), held) } : null;
      rankOf = rk0;
      showProfile('profile'); await wait(500);
      const cu = document.querySelector('.profile-rankplate .profile-rankcoin');
      out.unrankedEmpty = !rankOf(store) ? (!!cu && !cu.querySelector('svg') && !document.querySelector('.profile-rankplate-wm svg')) : true;
      } catch(e){ out.threw = String(e) + ' ' + (e.stack || '').split('\\n')[1]; }
      return out; }""")
    check("the ladder is Bronze, Silver, Gold, Platinum, Sapphire, Amethyst, Supernova - ranks and themes alike",
          r.get("names") == ["Bronze", "Silver", "Gold", "Platinum", "Sapphire", "Amethyst", "Supernova"] and r.get("themes") == r.get("names"), r)
    check("Gold is a yellow gold, not an ochre (hue 45 or more)", isinstance(r.get("goldHue"), int) and r["goldHue"] >= 45, r.get("goldHue"))
    check("seven flares on Home, none of them black and no two alike",
          r.get("flareMinLum", 0) >= 90 and r.get("flareMinDist", 0) >= 60, [r.get("flareMinLum"), r.get("flareMinDist")])
    alive = r.get("alive") or []
    check("every emblem moves where you look at it, and the Supernova moves most",
          len(alive) == 7 and min(alive) >= 3 and alive[-1] == max(alive), alive)
    check("the leaderboard column's emblem holds still, and Reduce motion stops every one",
          r.get("still") == 0 and r.get("reduced") == 0, [r.get("still"), r.get("reduced")])
    home = r.get("home") or []
    # This one also passes on 243 - by their boxes the old emblems were
    # centred too. It is here to HOLD the centring (the optical offsets in
    # RANK_EMBLEM_FIT move the moon and the comet up to 1.5px off their
    # boxes on purpose, and no further), not to show the change.
    check("every Home bubble's emblem is centred in it (within 1.5px)", len(home) == 7 and max(home) <= 1.5, home)
    coin = r.get("coin") or {}
    check("the Profile plate's coin is cut to fit and centred (within 1px)", coin.get("fitted") is True and coin.get("off", 9) <= 1, coin)
    check("an unranked plate shows no rank's emblem, in the coin or behind it (268)", r.get("unrankedEmpty") is True, r.get("unrankedEmpty"))
    ctx.close()


# --------------------------------------------------------------------------
# The questions on slides 1-87 of "TEXAS PENAL CODE for 736 updated
# 8-14-26" (Madison's "slides 0-85" - the deck has none past slide 79), by
# the bank's own `src`. Typed here on purpose: this is the reference the
# app's PENAL_TEST_SRCS is checked AGAINST, not read back from it.
PENAL_SLIDES_SRCS = sorted([
    147, 60, 135, 6, 62, 139, 285, 57, 265, 32, 151, 77, 174, 210, 51, 172,
    219, 259, 313, 44, 274, 191, 153, 7, 33, 53, 182, 303, 15, 218, 214, 84,
    75, 289, 302, 314, 196, 40, 178, 80, 69, 185, 101, 130, 249, 213, 24,
    121, 200, 262, 344, 128, 159, 61, 95, 183])

PENAL_CARD = ".picks .pick:has(.pname:text-is('Penal Code'))"

# Where a run stands: its pool as srcs, and whether it is all one unit.
PENAL_RUN = """()=>{ const o = (typeof order !== 'undefined' && Array.isArray(order)) ? order : [];
  return { n: o.length, srcs: o.map(i => Number(QUESTIONS[i].src)).sort((a, b) => a - b),
           allPenal: o.every(i => (QUESTIONS[i].topic || '').trim() === 'Penal Code'),
           unitTotal: QUESTIONS.filter(q => (q.topic || '').trim() === 'Penal Code').length }; }"""
# Stops the LOADING TEST count so it cannot open a question over whatever
# the check does next.
PENAL_HALT = """()=>{ try{ clearInterval(countdownHandle); }catch(e){}
  document.getElementById('teststart-overlay')?.remove();
  try{ clearInterval(vroomRevealHandle); }catch(e){}
  document.getElementById('vroom-reveal-overlay')?.remove(); }"""
PENAL_STATE = """()=>{ const row = [...document.querySelectorAll('.picks .pick')]
    .find(r => (r.querySelector('.pname') || {}).textContent === 'Penal Code');
  const pop = document.getElementById('unitver');
  return { pop: !!pop, opts: pop ? [...pop.querySelectorAll('.unitver-opt')].map(b => b.textContent) : [],
           popText: pop ? pop.textContent : '',
           checked: !!(row && row.querySelector('input').checked),
           cardText: row ? row.textContent : null,
           units: cfg.units.slice(), versions: JSON.stringify(cfg.versions || null) }; }"""


def check_penal_versions(br):
    """The Penal Code has two versions: the whole unit, and the questions on
    slides 0-85 of the instructor's PowerPoint. Selecting it asks which,
    EVERY time; nothing is remembered, and the card (which says the second
    version exists) does not change when one is chosen.
    The run draws only the chosen version, Re-run repeats it without asking,
    Select all takes the whole unit without asking, and a perfect run of the
    short version is not a hundo. A Virtual Room carries the choice on its
    own document, so no player's last Drill can leak into a room.
    Written against build 245, where there is no pop-up and every check
    about one fails. Five pass there too, and are meant to: the card not
    changing, deselect, XP, the whole unit and Select all are what must
    STAY as they were, so they hold the old behaviour rather than show
    the new one."""
    print("\n33. the Penal Code asks which version, every time")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    setup = ("()=>{ store.seenUnitSelectTour = true; cfg.mode = 'drill'; cfg.source = 'all'; cfg.size = 0;"
             " cfg.units = []; cfg.versions = {}; showSetup(); }")
    pg.evaluate(setup)
    pg.wait_for_timeout(700)
    card = pg.locator(PENAL_CARD + " .pname")
    before = pg.evaluate(PENAL_STATE)

    def tap():
        # centred first, so the fixed tab bar is never over it
        card.evaluate("e => e.scrollIntoView({block:'center', behavior:'instant'})")
        # A beat before the tap, the way a finger arrives (build 282). With
        # a compositor animation running on the tab bar (its sheen), a
        # click in the SAME instant as the scroll was hit-tested against
        # where the card had been - under the bar - and Playwright then
        # re-scrolled the card to the bottom edge to find a clear spot,
        # leaving it behind the bar. A real mouse click at the card's
        # centre lands on the card either way; this is the harness racing
        # itself, which is the one thing a harness must not do.
        pg.wait_for_timeout(150)
        card.click()
        pg.wait_for_timeout(450)
        return pg.evaluate(PENAL_STATE)

    def choose(which):
        """which: 'short' (the one naming slides) or 'whole'."""
        pg.evaluate("""(w)=>{ const b = [...document.querySelectorAll('#unitver .unitver-opt')]
          .find(x => /0\\u201385|0-85/.test(x.textContent) === (w === 'short')); if(b) b.click(); }""", which)
        pg.wait_for_timeout(450)
        return pg.evaluate(PENAL_STATE)

    # 1. the pop-up and what it says
    s1 = tap()
    check("selecting the Penal Code opens a pop-up, and holds the tick until it is answered",
          s1["pop"] and not s1["checked"] and s1["units"] == [], s1)
    opts = s1["opts"]
    nums = pg.evaluate("""()=>({ whole: QUESTIONS.filter(q => (q.topic||'').trim() === 'Penal Code').length })""")
    short = [o for o in opts if ("0–85" in o or "0-85" in o)]
    whole = [o for o in opts if o not in short]
    check("two choices: the whole unit, and the one from slides 0-85 of the PowerPoint",
          len(opts) == 2 and len(short) == 1 and "PowerPoint" in short[0] and "Penal Code" in whole[0]
          and ("%d questions" % len(PENAL_SLIDES_SRCS)) in short[0]
          and ("%d questions" % nums["whole"]) in whole[0], opts)
    check("nothing on it says 'test version'", s1["pop"] and "test version" not in s1["popText"].lower(), s1["popText"])
    # Build 250: the short version's hundo warning lives here and only here.
    check("the short choice says on the pop-up that it earns no hundo, and the whole unit does not",
          "hundo" in short[0].lower() and "hundo" not in whole[0].lower(), opts)
    s2 = choose("short")
    check("choosing slides 0-85 selects the card on that version",
          not s2["pop"] and s2["checked"] and s2["units"] == ["Penal Code"]
          and s2["versions"] == '{"Penal Code":"test"}', s2)
    check("the card does not change when a version is chosen",
          s2["cardText"] == before["cardText"], [before["cardText"], s2["cardText"]])
    pill = pg.evaluate("""()=>{ const c = [...document.querySelectorAll('.picks .pick')]
      .find(r => (r.querySelector('.pname')||{}).textContent === 'Penal Code');
      const t = c && c.querySelector('.pick-version'); if(!t) return null;
      const b = t.getBoundingClientRect();
      const hit = document.elementFromPoint(b.left + b.width/2, b.top + b.height/2);
      return { text: t.textContent, passesTap: !!hit && c.contains(hit) && !t.contains(hit),
        hit: hit ? (hit.id || String(hit.className && hit.className.baseVal !== undefined ? hit.className.baseVal : hit.className)).slice(0, 60) : null,
        y: Math.round(b.top), vh: innerHeight, sy: Math.round(scrollY) }; }""")
    check("the card says it carries the slides 0-85 version, and a tap on that line is a tap on the card",
          bool(pill) and "0–85" in pill["text"] and pill["passesTap"], pill)
    # 2. deselect never asks; the next select asks again
    s3 = tap()
    check("tapping it again deselects it, with no pop-up",
          not s3["pop"] and not s3["checked"] and s3["units"] == [] and s3["versions"] == "{}", s3)
    s4 = tap()
    check("and selecting it again asks again (every time, never remembered)", s4["pop"] and not s4["checked"], s4)
    choose("short")
    # 3. the sheet and the run
    sheet = pg.evaluate("""async ()=>{ document.getElementById('nextbtn').click();
      const line = document.querySelector('.sheet-summary-line'), note = document.querySelector('.hundo-note');
      const out = { line: line ? line.textContent : '', start: document.getElementById('nextbtn').textContent,
               note: note && !note.hidden ? note.textContent : '' };
      /* Build 254: cut down further (How many under the max), still no note -
         the short version can never earn a hundo, and its pop-up said so */
      const sl = document.querySelector('.unitoptions-modal-sheet .howmany-sect .slider');
      if(sl){ sl.value = sl.min; sl.dispatchEvent(new Event('input', { bubbles: true })); }
      await new Promise(r => setTimeout(r, 150));
      out.noteCut = note && !note.hidden ? note.textContent : '';
      out.cut = cfg.size;
      if(sl){ sl.value = sl.max; sl.dispatchEvent(new Event('input', { bubbles: true })); }
      return out; }""")
    n56 = "%d questions" % len(PENAL_SLIDES_SRCS)
    check("the start sheet and the Start button count the slides 0-85 questions",
          n56 in sheet["line"] and n56 in sheet["start"], sheet)
    # Build 250: the version pop-up is where the short version says it
    # earns no hundo ("put the warning ... only at the pop up for which
    # version"); the sheet's note is for cutting it down further.
    check("the start sheet does not repeat the version pop-up's hundo warning",
          sheet["note"] == "", sheet["note"])
    check("and cutting the short version down further (fewer questions, Most missed, Flagged) raises no warning either",
          sheet.get("cut", 0) > 0 and sheet.get("noteCut") == "", sheet)
    pg.evaluate("()=>document.querySelector('.sheet-begin-btn').click()")
    pg.wait_for_timeout(200)
    run = pg.evaluate(PENAL_RUN)
    pg.evaluate(PENAL_HALT)
    check("the run is exactly the %d questions on slides 0-85" % len(PENAL_SLIDES_SRCS),
          run["allPenal"] and run["srcs"] == PENAL_SLIDES_SRCS, "%d questions" % run["n"])
    # 4. a perfect run of it earns XP and no hundo
    hundo = pg.evaluate("""()=>{ const u = 'Penal Code';
      const before = { hundos: unitPerfectCount(u), perfect: store.lifetime.perfectTests || 0, xp: store.lifetime.points || 0 };
      attempts = {}; picked = {}; timedOutSet = {}; timedOut = false; runStartTime = Date.now() - 90000;
      order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
      summarize();
      return { before, after: { hundos: unitPerfectCount(u), perfect: store.lifetime.perfectTests || 0, xp: store.lifetime.points || 0 },
               rows: [...document.querySelectorAll('.badgeprogress-name')].map(e => e.textContent) }; }""")
    check("a perfect slides 0-85 run is not a Penal Code hundo, and shows no badge progress for it",
          hundo["after"]["hundos"] == hundo["before"]["hundos"] and hundo["after"]["perfect"] == hundo["before"]["perfect"]
          and not any("Penal Code" in r for r in hundo["rows"]), hundo)
    check("it still earns XP", hundo["after"]["xp"] > hundo["before"]["xp"], hundo)
    # 5. Re-run repeats the version, without asking
    rr = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      let b = null;
      for(let i = 0; i < 60 && !b; i++){ b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Re-run'); if(!b) await wait(150); }
      if(!b) return { found: false };
      b.click(); await wait(250);
      return { found: true, pop: !!document.getElementById('unitver') }; }""")
    run2 = pg.evaluate(PENAL_RUN)
    pg.evaluate(PENAL_HALT)
    check("Re-run repeats slides 0-85, and does not ask",
          rr.get("found") and not rr.get("pop") and run2["srcs"] == PENAL_SLIDES_SRCS, [rr, run2["n"]])
    # 6. the whole unit
    pg.evaluate(setup)
    pg.wait_for_timeout(600)
    tap()
    sw = choose("whole")
    pg.evaluate("()=>{ document.getElementById('nextbtn').click(); document.querySelector('.sheet-begin-btn').click(); }")
    pg.wait_for_timeout(200)
    run3 = pg.evaluate(PENAL_RUN)
    pg.evaluate(PENAL_HALT)
    check("choosing the whole unit runs every Penal Code question",
          sw["checked"] and sw["versions"] == "{}" and run3["allPenal"] and run3["n"] == run3["unitTotal"],
          "%d of %d" % (run3["n"], run3["unitTotal"]))
    # 7. dismissing picks nothing, however it is dismissed
    pg.evaluate(setup)
    pg.wait_for_timeout(600)
    tap()
    pg.evaluate("()=>{ const c = document.querySelector('#unitver .unitver-cancel'); if(c) c.click(); }")
    pg.wait_for_timeout(450)
    d1 = pg.evaluate(PENAL_STATE)
    s5 = tap()
    pg.mouse.click(6, 6)   # the scrim, outside the card
    pg.wait_for_timeout(450)
    d2 = pg.evaluate(PENAL_STATE)
    check("Cancel, or a tap outside, leaves it unselected",
          s5["pop"] and not d1["pop"] and not d1["checked"] and d1["units"] == []
          and not d2["pop"] and not d2["checked"] and d2["units"] == [], [d1, d2])
    # 8. Select all
    pg.evaluate("()=>document.querySelector('.selall-btn').click()")
    pg.wait_for_timeout(450)
    sa = pg.evaluate(PENAL_STATE)
    sa_pool = pg.evaluate("()=>poolNow().filter(i => (QUESTIONS[i].topic||'').trim() === 'Penal Code').length")
    check("Select all takes the whole Penal Code, with no pop-up",
          not sa["pop"] and sa["checked"] and "Penal Code" not in sa["versions"] and sa_pool == nums["whole"],
          [sa["pop"], sa["versions"], sa_pool])
    # 8b. in a mix, the note names the short unit and the others still count
    pg.evaluate(setup)
    pg.wait_for_timeout(600)
    tap()
    choose("short")
    pg.locator(".picks .pick:has(.pname:text-is('Identity Crimes')) .pname").click()
    pg.wait_for_timeout(300)
    mix = pg.evaluate("""()=>{ document.getElementById('nextbtn').click();
      const note = document.querySelector('.hundo-note'), line = document.querySelector('.sheet-summary-line');
      const out = { note: note && !note.hidden ? note.textContent : '', line: line ? line.textContent : '',
        want: QUESTIONS.filter(q => (q.topic||'').trim() === 'Identity Crimes').length };
      document.querySelector('.unitoptions-modal-scrim')?.click(); return out; }""")
    # REVISED IN 291: the line is always there now (it holds the slider
    # still), so the rule is that it never claims the short version counts.
    check("with another unit, the sheet's line never says the short version counts",
          "Every question" not in mix["note"] and "won't count" not in mix["note"]
          and ("%d questions" % (len(PENAL_SLIDES_SRCS) + mix["want"])) in mix["line"], mix)
    # 9. Review mode shows the version chosen
    pg.evaluate("()=>{ cfg.mode = 'review'; cfg.units = []; cfg.versions = {}; showSetup(); }")
    pg.wait_for_timeout(600)
    tap()
    choose("short")
    rv = pg.evaluate("""()=>{ document.getElementById('nextbtn').click(); document.querySelector('.sheet-begin-btn').click();
      return document.querySelectorAll('.review-question').length; }""")
    check("Review of slides 0-85 lists those questions only", rv == len(PENAL_SLIDES_SRCS), rv)
    # 10. the Virtual Room: the host's pick goes on the room, and only the room decides
    pg.evaluate("()=>{ window.__room = null; createVirtualRoomLobby = function(){ window.__room = [...arguments]; }; showVirtualRoomSetup(); }")
    pg.wait_for_timeout(700)
    v1 = tap()
    choose("short")
    room = pg.evaluate("""()=>{ document.getElementById('nextbtn').click();
      const line = document.querySelector('.sheet-summary-line');
      const txt = line ? line.textContent : '';
      /* build 266: a room has no game until one is picked */
      document.querySelector('.vroom-host-mode[data-mode="race"]')?.click();
      document.querySelector('.sheet-begin-btn').click();
      return { line: txt, args: window.__room ? JSON.parse(JSON.stringify(window.__room)) : null }; }""")
    args = room.get("args") or []
    check("the Virtual Room's picker asks too, and the room is created with the version on it",
          v1["pop"] and n56 in room["line"] and len(args) >= 4 and args[0] == ["Penal Code"]
          and args[3] == {"Penal Code": "test"}, [v1["pop"], room])
    vr = pg.evaluate("""()=>{ const out = {}; const srcs = () => order.map(i => Number(QUESTIONS[i].src)).sort((a, b) => a - b);
      const stop = () => { try{ clearInterval(vroomRevealHandle); }catch(e){} document.getElementById('vroom-reveal-overlay')?.remove(); };
      cfg.versions = { 'Penal Code': 'test' };           /* this player's last Drill */
      beginVirtualRoomTest(['Penal Code'], 10, Date.now() + 60000, null);
      out.wholeRoom = order.length; stop();
      cfg.versions = {};
      beginVirtualRoomTest(['Penal Code'], 10, Date.now() + 60000, null, { 'Penal Code': 'test' });
      out.shortRoom = srcs(); stop();
      try{
        cfg.versions = {};
        beginTugMatch({ units: ['Penal Code'], versions: { 'Penal Code': 'test' }, startAt: Date.now() + 60000, count: 0 });
        out.tug = tugPool.map(i => Number(QUESTIONS[i].src)).sort((a, b) => a - b);
      }catch(e){ out.tugErr = String(e); }
      inVirtualRoom = false; testInProgress = false; window.forceHideBottomTabs = false;
      return out; }""")
    whole_n = nums["whole"]
    check("a room runs what the ROOM says: the whole unit despite a player's last pick, and slides 0-85 when it is set",
          vr.get("wholeRoom") == whole_n and vr.get("shortRoom") == PENAL_SLIDES_SRCS,
          [vr.get("wholeRoom"), len(vr.get("shortRoom") or [])])
    check("Tug of War draws from the room's version too", vr.get("tug") == PENAL_SLIDES_SRCS,
          vr.get("tugErr") or len(vr.get("tug") or []))
    ctx.close()


def check_b245_ladder(br):
    """Build 245: the ladder CLIMBS. "I want to feel like it's in order from
    best to worst just by looking at it." Measured on the 244 set, it did
    not: at bubble size Bronze's nebula was among the heaviest marks,
    Amethyst's galaxy the faintest, and Gold's sun outshone Platinum and
    Sapphire. The drawings were re-dealt by weight and each rank presented
    one step up, and this holds it: every emblem, fitted into its Home
    bubble exactly as the app fits it and rendered at 44px on black, has
    MORE light and MORE ink than the rank below it - both, at every step.
    Written against build 244 (the page before this), where both fail."""
    print("\n34. build 245: the ladder climbs at bubble size")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = { light: [], ink: [] }; try{
      const N = 44;
      for(const k of TIER_ORDER_FULL){
        const svg = fitRankEmblem(buildRankEmblemSVG(k), k);
        svg.setAttribute('width', N); svg.setAttribute('height', N); svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        const img = new Image(); await new Promise(r => { img.onload = r; img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(svg)); });
        const c = document.createElement('canvas'); c.width = c.height = N; const x = c.getContext('2d');
        x.fillStyle = '#000'; x.fillRect(0, 0, N, N); x.drawImage(img, 0, 0);
        const d = x.getImageData(0, 0, N, N).data; let lit = 0, ink = 0;
        for(let i = 0; i < d.length; i += 4){ const m = Math.max(d[i], d[i + 1], d[i + 2]); lit += m; if(m > 40) ink++; }
        out.light.push(Math.round(lit / (N * N * 255) * 1000) / 10);
        out.ink.push(Math.round(ink / (N * N) * 1000) / 10);
      }
      } catch(e){ out.threw = String(e); }
      return out; }""")
    up = lambda xs: len(xs) == 7 and all(b > a for a, b in zip(xs, xs[1:]))
    check("at bubble size each rank gives off more light than the one below it, Bronze to Supernova",
          up(r.get("light") or []), [r.get("light"), r.get("threw")])
    check("and covers more of its bubble than the one below it",
          up(r.get("ink") or []), r.get("ink"))
    ctx.close()


def check_b240_activity(br):
    """Build 240: what each friend is doing - main menu, a Drill, an Exam,
    Game mode, a Virtual Room lobby or match - on the Friends lists and the
    invite sheets, shared through the presence document and written only
    when it changes. Written against build 239, which had none of it."""
    print("\n27. build 240: what each friend is doing")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; try{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      /* What this device says it is doing. */
      showHome(); await wait(200); out.home = currentActivity();
      const u = topicsIn(QUESTIONS)[0];
      cfg.mode = 'exam'; cfg.units = [u]; cfg.source = 'all';
      beginRun(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === u), null);
      await wait(3600); out.exam = currentActivity();
      testInProgress = false; inVirtualRoom = false;
      const lob = document.createElement('section'); lob.className = 'panel screen-vroom-lobby';
      stage.replaceChildren(lob); out.lobby = currentActivity();
      inVirtualRoom = true; testInProgress = true; out.match = currentActivity();
      inVirtualRoom = false; testInProgress = false;
      /* It is written when it changes, not on every screen change. */
      const writes = [];
      const realFb = fbDb;
      fbDb = { collection: () => ({ doc: () => ({ set: (d) => { writes.push(JSON.stringify(d.a || null)); return Promise.resolve(); } }) }) };
      store.leaderboardOptIn = true; syncCode = syncCode || 'SYNC-TEST'; store.publicId = store.publicId || 'me000000001';
      activityShared = ''; activityLastWrite = 0;
      showHome(); await wait(100); shareActivity();
      showHome(); await wait(100); shareActivity();
      out.writesSame = writes.length;
      fbDb = realFb;
      /* A friend's, as the lists show it. */
      const pub = 'fr000000001';
      store.friendsIn = [pub];
      leaderboardRows = [{ pub, firstName: 'Bo', avatarChar: 'ninja', level: 5, badges: 0, seenAt: Date.now() }];
      presenceMap = { [pub]: Date.now() }; presenceActivity = { [pub]: 'lobby' };
      out.long = friendActivityText(pub, true);
      out.short = friendActivityText(pub, false);
      presenceMap = { [pub]: Date.now() - 60 * 60 * 1000 }; leaderboardRows[0].seenAt = 0;
      out.offline = friendActivityText(pub, true);
      presenceMap = { [pub]: Date.now() }; leaderboardRows[0].seenAt = Date.now();
      showFriends(); await wait(300);
      presenceActivity = { [pub]: 'drill' }; paintActivityLabels();
      const lab = document.querySelector('.screen-friends .friend-activity');
      out.friendsScreen = lab ? lab.textContent : '';
      presenceActivity = { [pub]: 'match' }; paintActivityLabels();
      out.repainted = lab ? lab.textContent : '';
    } catch(e){ out.threw = String(e); } return out; }""")
    check("this device says main menu on Home", r.get("home") == "menu", r)
    check("an Exam in progress says Exam", r.get("exam") == "exam", r)
    check("a Virtual Room lobby and match are told apart",
          r.get("lobby") == "lobby" and r.get("match") == "match", r)
    check("it is written once when it changes, not on every screen change", r.get("writesSame") == 1, r)
    check("a friend in a lobby reads that way, long and short",
          r.get("long") == "In a Virtual Room lobby" and r.get("short") == "In a lobby", r)
    check("and says nothing once they are offline", r.get("offline") == "", r)
    check("Profile > Friends shows it and repaints it in place",
          r.get("friendsScreen") == "In a Drill" and r.get("repainted") == "In a match", r)
    ctx.close()


def check_b240(br):
    """Build 240: Friends and Group chats, counts per tab, dead invites,
    the friends moment, the room's chat on the results, a pinned Pause and
    a centred reveal. Written against build 239, which had one chat tab."""
    print("\n25. build 240: friends and group chats, and the test screen")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const out = {};
      try{
      /* A Firestore that answers, holds nothing, and never pushes. */
      const docs = {};
      const doc = id => ({
        onSnapshot(){ return () => {}; },
        get(){ return Promise.resolve({ exists: !!docs[id], data: () => docs[id] || {} }); },
        set(d){ docs[id] = d; return Promise.resolve(); },
        update(){ return Promise.resolve(); } });
      fbDb = { collection: () => ({ doc, onSnapshot(){ return () => {}; },
                 get(){ return Promise.resolve({ forEach(){}, size:0, metadata:{} }); } }),
               runTransaction(fn){ return Promise.resolve().then(() => fn({
                 get: ref => ref.get(), set: (ref, d) => ref.set(d), update: () => {} })); } };
      const me = publicIdOf();
      store.friendsIn = ['bo00000000001'];
      leaderboardRows = [{ pub:'bo00000000001', firstName:'Bo', avatarChar:'robot', level:5, badges:1, seenAt: Date.now() }];
      /* 1. one friend chat per pair, the same id from both sides */
      out.symmetric = typeof friendChatCode === 'function'
        && friendChatCode('bo00000000001') === ('DM-' + [me, 'bo00000000001'].sort().join('-')).toUpperCase();
      /* 2. the dock has Friends, Groups and Inbox, each able to count */
      showHome(); await wait(600);
      document.getElementById('chatdock-btn').click(); await wait(300);
      out.tabs = [...document.querySelectorAll('.chatdock-tab')].map(b => b.dataset.tab);
      out.friendRow = !!document.querySelector('.chatdock-chatrow.is-friend');
      /* 3. a friend chat has no Invite and no Leave, and can be muted */
      document.querySelector('.chatdock-chatrow.is-friend .chatdock-chatrow-open').click(); await wait(400);
      const minis = [...document.querySelectorAll('.chatdock-mini')].map(b => b.textContent);
      out.friendHead = { invite: minis.indexOf('Invite') >= 0, leave: minis.indexOf('Leave') >= 0,
                         mute: !!document.querySelector('.chatdock-roomhead .chat-mute-btn'),
                         created: !!docs[friendChatCode('bo00000000001')] };
      closeChatRoom();
      /* 4. counts per tab: one unread friend chat, one unread group */
      const t0 = Date.now();
      inboxMsgs = {
        'bo00000000001~m': { type:'msgping', code: friendChatCode('bo00000000001'), pub:'bo00000000001', firstName:'Bo', text:'hi', at: t0 },
        'cy~m': { type:'msgping', code:'GRP-AAAA', pub:'cy', firstName:'Cy', text:'yo', at: t0 } };
      syncChatDockDot();
      const txt = id => { const e = document.getElementById(id); return e && !e.hidden ? e.textContent : '0'; };
      out.counts = { friends: txt('chatdock-friendscount'), groups: txt('chatdock-groupscount'),
                     dot: (document.getElementById('chatdock-dot') || {}).textContent };
      /* 5. a dead invite says the chat is gone */
      let said = '';
      const realToast = window.showToast; window.showToast = m => { said = m; };
      const ok = await joinChatRoom('GONE-0000');
      window.showToast = realToast;
      out.dead = { ok, said, gone: lastJoinGone };
      /* 6. becoming friends is a moment */
      localStorage.removeItem('class26e.friendmoment');
      closeChatDock(); await wait(200);
      celebrateNewFriend('bo00000000001'); await wait(400);
      out.moment = (document.querySelector('.friend-moment-title') || {}).textContent || '';
      document.querySelector('.friend-moment')?.remove();
      /* 7. the room's chat can be lifted over the results */
      const host = document.createElement('section'); host.className = 'panel';
      const chat = document.createElement('div'); chat.className = 'vroom-chat'; chat.textContent = 'room chat';
      host.appendChild(chat); stage.replaceChildren(host);
      mountRoomChatFab(); await wait(100);
      out.fab = !!document.getElementById('roomchat-fab');
      openRoomChatSheet(); await wait(100);
      out.lifted = !!document.querySelector('#roomchat-sheet .vroom-chat');
      closeRoomChatSheet();
      out.returned = chat.parentNode === host;
      } catch(e){ out.threw = String(e); }
      return out; }""")
    check("one friend chat per pair, the same id from both sides", r.get("symmetric") is True, r)
    check("the dock has Friends, Groups and Inbox tabs",
          r.get("tabs") == ["friends", "groups", "notifs"], r.get("tabs"))
    check("a friend is listed on the Friends tab without being invited", r.get("friendRow") is True, r)
    fh = r.get("friendHead") or {}
    check("a friend chat has no Invite and no Leave, and can be muted",
          fh.get("invite") is False and fh.get("leave") is False and fh.get("mute") is True, fh)
    check("opening it creates the friend chat", fh.get("created") is True, fh)
    cn = r.get("counts") or {}
    check("each tab counts its own unread chats and the button adds them up",
          cn.get("friends") == "1" and cn.get("groups") == "1" and cn.get("dot") in ("2", "3"), cn)
    dd = r.get("dead") or {}
    check("a dead invite says plainly that the chat is gone",
          dd.get("ok") is False and "doesn't exist" in (dd.get("said") or "") and dd.get("gone") is True, dd)
    check("becoming friends is a moment, not a toast", "now friends" in (r.get("moment") or ""), r.get("moment"))
    check("the room's chat has a button on the results and lifts into a sheet",
          r.get("fab") is True and r.get("lifted") is True and r.get("returned") is True, r)
    ctx.close()

    # The test screen: Pause pinned and full-size; the reveal centred.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    t = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const U = topicsIn(QUESTIONS)[0];
      const ix = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === U);
      cfg.mode = 'drill'; cfg.units = [U]; cfg.source = 'all'; runMode = 'drill';
      try{ beginRun(ix, null); }catch(e){ return { threw: String(e) }; }
      for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(150);
      await wait(900);
      const p = document.getElementById('pausebtn');
      const pr = p.getBoundingClientRect();
      const out = { pos: getComputedStyle(p).position, h: Math.round(pr.height) };
      revealed = false; cfg.recall = true; render(); await wait(400);
      const b = document.getElementById('revealbtn');
      const panel = b ? b.closest('.panel') : null;
      if(b && panel){
        const br = b.getBoundingClientRect(), pn = panel.getBoundingClientRect();
        out.offCentre = Math.round(Math.abs((br.left + br.width / 2) - (pn.left + pn.width / 2)));
        out.w = Math.round(br.width);
        const st = panel.querySelector('.status');
        out.statusShown = !!(st && !st.hidden && st.getBoundingClientRect().height > 0);
      }
      return out; }""")
    check("Pause is pinned like the chat button and 44px tall on a phone",
          t.get("pos") == "fixed" and (t.get("h") or 0) >= 44, t)
    check("Show answer choices is centred, wide, and has no status line on top of it",
          t.get("offCentre") is not None and t["offCentre"] <= 3 and (t.get("w") or 0) >= 280
          and t.get("statusShown") is False, t)
    ctx.close()


def check_audit_a(br):
    """Pre-launch audit (auditor A). Each of these was written against
    build 245 as it stood and fails there."""
    print("\nA. pre-launch audit: keys typed into a chat, the flare pop-up, the rankings search")

    # Typing into the chat must never drive the run behind it. The
    # document-level shortcuts (1-9 answer, Enter = Next / Start
    # Studying, Space resumes a pause) fired for keys typed INTO the chat
    # box, so "2" in a message answered question two and Enter on Home
    # started a study session under the dock.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const U = topicsIn(QUESTIONS)[0]; const ix = QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===U);
      cfg.mode='drill'; cfg.units=[U]; cfg.source='all'; runMode='drill'; beginRun(ix, null);
      for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(150);
      await wait(900);
      document.getElementById('chatdock-btn').click(); await wait(600);
      [...document.querySelectorAll('.chatdock-tab')].find(t => /Groups/.test(t.textContent))?.click(); await wait(500);
      [...document.querySelectorAll('.chatdock button')].find(b => /Start a group/i.test(b.textContent))?.click();
      for(let i = 0; i < 30 && !document.querySelector('.chatdock .vroom-chat-input'); i++) await wait(150);
      const inp = document.querySelector('.chatdock .vroom-chat-input');
      if(inp) inp.focus();
      return { input: !!inp, pos: pos, locked: document.querySelector('.qpanel').innerText.replace(/\\s+/g, ' ').slice(0, 400) };
    }""")
    if r["input"]:
        pg.keyboard.type("2 4")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(900)
    after = pg.evaluate("""()=>({ pos: pos,
      locked: document.querySelector('.qpanel').innerText.replace(/\\s+/g, ' ').slice(0, 400),
      q: !!document.querySelector('.qpanel .choice') })""")
    check("a chat box can be reached mid-run", r["input"], r)
    check("typing digits and Enter into the chat answers nothing and moves nothing",
          r["input"] and after["q"] and after["pos"] == r["pos"] and after["locked"] == r["locked"],
          {"before": r, "after": after})
    ctx.close()

    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      showHome(); await wait(700);
      document.getElementById('chatdock-btn').click(); await wait(600);
      [...document.querySelectorAll('.chatdock-tab')].find(t => /Groups/.test(t.textContent))?.click(); await wait(500);
      [...document.querySelectorAll('.chatdock button')].find(b => /Start a group/i.test(b.textContent))?.click();
      for(let i = 0; i < 30 && !document.querySelector('.chatdock .vroom-chat-input'); i++) await wait(150);
      const inp = document.querySelector('.chatdock .vroom-chat-input');
      if(inp) inp.focus();
      return { input: !!inp };
    }""")
    if r["input"]:
        pg.keyboard.type("hi")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(1200)
    home = pg.evaluate("()=>!!document.querySelector('#stage [data-screen=\"home\"]')")
    check("Enter in the chat on Home sends the message and does not start studying",
          r["input"] and home, {"input": r["input"], "stillHome": home})
    ctx.close()

    # A flare's pop-up lives on <body>; tapping a tab straight after it
    # used to carry it (and its pointer line) over the next screen.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      showHome(); await wait(900);
      const b = document.querySelector('#stage .cosmic-icon-badge.cosmic-badge-tappable');
      b.dispatchEvent(new MouseEvent('click', { bubbles: true })); await wait(300);
      const shown = !!document.getElementById('contextual-info-popup');
      document.getElementById('bottomtab-profile').click(); await wait(250);
      return { shown, onProfile: !!document.querySelector('.screen-profile'),
        left: ['contextual-info-popup','contextual-info-line','contextual-info-line-dot'].filter(id => document.getElementById(id)) };
    }""")
    check("a flare's pop-up goes with Home when a tab is tapped", r["shown"] and r["onProfile"] and not r["left"], r)
    ctx.close()

    # The rankings search says what it is on the reference phone and on
    # an SE: no 2.5rem icon gap (there is no icon) and no room held for
    # a clear button that is not there.
    for w, h in ((440, 956), (375, 667)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{
          showRankings('week'); await new Promise(r => setTimeout(r, 900));
          const i = document.querySelector('.rank-search'); const cs = getComputedStyle(i);
          const c = document.createElement('canvas').getContext('2d'); c.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
          const room = i.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
          return { need: Math.ceil(c.measureText(i.placeholder).width), room: Math.floor(room) };
        }""")
        check("the rankings search placeholder is not cut off at %dpx" % w, r["need"] <= r["room"], r)
        ctx.close()

    # A tapped badge in the case's bottom row answered OVER the tab bar:
    # the pop-up reserved a guessed 84px for a bar that is taller than
    # that. Put the last row where 84px would have said "it fits below"
    # and the real bar says it does not, and tap it.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      showRanksScreen('badges'); await wait(1200);
      /* The gate serves every safe-area inset as 0; lift the bar by an
         iPhone's 34px home indicator the way env() does on the device. */
      const st = document.createElement('style'); st.textContent = '.bottomtabs{ bottom:calc(.6rem + 34px) !important; }';
      document.head.appendChild(st); await wait(300);
      const bar = document.querySelector('.bottomtabs').getBoundingClientRect();
      const tiles = [...document.querySelectorAll('#stage .badge-tile')]; const t = tiles[tiles.length - 1];
      window.scrollBy({ top: t.getBoundingClientRect().bottom - (bar.top - 73), behavior: 'instant' }); await wait(300);
      const tr = t.getBoundingClientRect();
      t.click(); await wait(700);
      /* Build 281 answers a badge tap with the unlock card rather than
         the info bubble this was written for; the card still has to land
         clear of the bar, whichever badge was tapped. */
      const p = document.querySelector('.unlock-card-badge') || document.getElementById('contextual-info-popup');
      const pr = p ? p.getBoundingClientRect() : null;
      return { tile: [Math.round(tr.top), Math.round(tr.bottom)], barTop: Math.round(bar.top),
        popup: pr ? [Math.round(pr.top), Math.round(pr.bottom)] : null };
    }""")
    check("what a badge near the bottom opens never covers the tab bar",
          r["popup"] is not None and r["popup"][1] <= r["barTop"], r)
    ctx.close()

    # ---- round two ----
    # R1: Home's rank bubbles scale with the planet. On a 320x568 phone
    # they were 44px on a 139px planet: stacked on each other and run
    # down past the hero onto the greeting. The reference phone keeps
    # its exact size.
    sizes = {}
    for w, h in ((320, 568), (440, 956)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        sizes[w] = pg.evaluate("""async ()=>{
          showHome(); await new Promise(r => setTimeout(r, 1200));
          const wrap = document.querySelector('.panel.home .cosmic-hero-wrap').getBoundingClientRect();
          const b = [...document.querySelectorAll('.panel.home .cosmic-hero-wrap .cosmic-icon-badge.cosmic-badge-rank')].map(e => {
            const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, s: r.width, bottom: r.bottom }; });
          let overlaps = 0;
          b.forEach((p, i) => b.forEach((q, j) => { if(j > i && Math.hypot(p.x - q.x, p.y - q.y) < (p.s + q.s) / 2 - 1) overlaps++; }));
          return { n: b.length, size: Math.round(b[0].s * 10) / 10, overlaps,
            spill: Math.round(Math.max(...b.map(p => p.bottom)) - wrap.bottom),
            /* measured inside the hero, which carries a scale() of its own */
            ref: (() => { const d = document.createElement('div'); d.style.cssText = 'position:absolute;left:0;top:0;width:2.9rem;height:1px';
              document.querySelector('.panel.home .cosmic-hero-wrap').appendChild(d);
              const v = d.getBoundingClientRect().width; d.remove(); return Math.round(v * 10) / 10; })() };
        }""")
        ctx.close()
    s = sizes[320]
    check("on a 320x568 phone the rank bubbles neither overlap nor spill below the planet",
          s["n"] == 7 and s["overlaps"] == 0 and s["spill"] <= 0, s)
    p = sizes[440]
    check("on the 17 Pro Max they are still exactly 2.9rem", abs(p["size"] - p["ref"]) < 0.6, p)

    # R7: the secret-flare dots are ~44px to tap without looking any
    # different: a point 15px off a dot's centre is still the dot.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      showHome(); await new Promise(r => setTimeout(r, 1200));
      document.querySelectorAll('.app-banner').forEach(e => e.remove());
      const dots = [...document.querySelectorAll('.panel.home .cosmic-orbit-dot.cosmic-badge-tappable')];
      const hits = dots.map(d => { const r = d.getBoundingClientRect(); const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        return [[15, 0], [-15, 0], [0, 15], [0, -15]].some(([dx, dy]) => document.elementFromPoint(cx + dx, cy + dy) === d); });
      const paint = dots.map(d => getComputedStyle(d).stroke);
      return { n: dots.length, hits: hits.filter(Boolean).length, paint };
    }""")
    check("the secret-flare dots take a tap 15px from their centre", r["n"] == 5 and r["hits"] == 5, r)
    check("and paint nothing new doing it", all(("0, 0, 0, 0" in x) or x in ("none", "transparent") for x in r["paint"]), r["paint"])
    ctx.close()

    # R3: a brand-new account finishes onboarding and does not get the
    # "New in this update" card on top; and the card no longer talks
    # about a "chat lobby".
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      localStorage.removeItem('class26e.intro.seen');
      store.onboardingComplete = false; store.tourRev = 0; pendingMainMenuTour = true; showHome();
      for(let i = 0; i < 60; i++){ await wait(350); const n = document.getElementById('tour-next'); if(n) n.click(); else if(i > 8) break; }
      for(let i = 0; i < 12 && !document.getElementById('intro-pop'); i++) await wait(500);
      const shown = !!document.getElementById('intro-pop');
      document.getElementById('intro-pop')?.remove();
      showIntroPopup(); await wait(200);
      const text = document.getElementById('intro-pop')?.innerText || '';
      document.getElementById('intro-pop')?.remove();
      return { onboarded: store.onboardingComplete, shown, lobby: /chat lobby/i.test(text) };
    }""")
    check("a brand-new account is not shown 'New in this update' after onboarding", r["onboarded"] and not r["shown"], r)
    check("the chat card no longer says 'chat lobby'", not r["lobby"], r)
    ctx.close()

    # R4: the back-to-top button never sits on the last control at the
    # foot of a long screen.
    for w, h in ((440, 956), (375, 667)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const T = 'button, a[href], [role="button"], input, select, textarea, label, .is-tappable';
          const out = {};
          for(const [k, fn] of [['stats', () => showProfile('stats')], ['calendar', () => showCalendar()], ['review', () => showTestReviewList()],
                                ['profile', () => showProfile('profile')], ['settings', () => showAppearance()], ['leaderboard', () => showRankings('week')]]){
            fn(); await wait(900);
            window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' }); await wait(500);
            const btn = document.getElementById('backtotop'); const b = btn.getBoundingClientRect();
            const shown = btn.classList.contains('show');
            const under = shown ? [...document.querySelectorAll('#stage ' + T.split(', ').join(', #stage '))].filter(e => {
              const r = e.getBoundingClientRect(); return r.width && r.left < b.right && r.right > b.left && r.top < b.bottom && r.bottom > b.top; })
              .map(e => e.textContent.trim().slice(0, 20)) : [];
            out[k] = under;
          }
          return out;
        }""")
        bad = {k: v for k, v in r.items() if v}
        check("at %dpx the back-to-top button sits on no control at the foot of a long screen" % w, not bad, bad or r)
        ctx.close()

    # R5: a group chat's controls share the member-count line on an SE,
    # so the conversation gets the height back.
    # A touch context, because a phone's coarse pointer is what gives the
    # app's buttons their full size - and that size is what wrapped.
    ctx, pg = booted(br, 375, 667, seed=USED_ACCOUNT, touch=True)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      showHome(); await wait(700);
      document.getElementById('chatdock-btn').click(); await wait(600);
      [...document.querySelectorAll('.chatdock-tab')].find(t => /Groups/.test(t.textContent))?.click(); await wait(500);
      [...document.querySelectorAll('.chatdock button')].find(b => /Start a group/i.test(b.textContent))?.click();
      for(let i = 0; i < 30 && !document.getElementById('chatdock-roomcount'); i++) await wait(150);
      await wait(400);
      /* The stub has no live roster, so the line the snapshot would write. */
      const cnt = document.getElementById('chatdock-roomcount');
      if(cnt && !cnt.textContent.trim()) cnt.textContent = '3 members \u00b7 2 here now';
      await wait(100);
      const c = cnt?.getBoundingClientRect();
      const t = document.querySelector('.chatdock-roomtools')?.getBoundingClientRect();
      const b = [...document.querySelectorAll('.chatdock-roomtools button')].map(x => Math.round(x.getBoundingClientRect().height));
      return c && t ? { countTop: Math.round(c.top), countBottom: Math.round(c.bottom), toolsTop: Math.round(t.top), heights: b } : null;
    }""")
    check("on an SE a group chat's mute/Invite/Leave sit on the member-count line, still 44px to tap",
          r is not None and r["toolsTop"] < r["countBottom"] and min(r["heights"][1:]) >= 44, r)
    ctx.close()


# --------------------------------------------------------------------------
# Build 245, Madison's polish list. Every section below was written against
# the build before it (the base this list was applied to) and fails there.
CONSTITUTION = "US and Texas Constitution and Rights"
PENAL = "Penal Code"


def check_b245_modes(br):
    """35. "The review option on the mode selection screen should not be at
    the bottom on the iPhone, it'll need to be the 3rd one listed, under
    exam instead." Read by each card's own mode icon, not by its words, so
    a renamed card cannot turn this red; on a tablet's two-across wrap
    Review has to share a row with Virtual Room, under Drill and Exam
    (it was Game until Game mode was retired in build 283)."""
    print("\n35. build 245: Review is third on the mode screen, on every device")
    for label, w, h in DEVICES + [("iPhone SE", 320, 568)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ store.seenModeSelectTour = true; showModeSelect();
          await new Promise(r => setTimeout(r, 500));
          return [...document.querySelectorAll('.modeselect .modecard')].map(c => {
            const ic = c.querySelector('.modeicon'); const b = c.getBoundingClientRect();
            return { kind: ic ? [...ic.classList].find(k => k.startsWith('modeicon-')).slice(9) : null,
                     top: Math.round(b.top), left: Math.round(b.left) }; }); }""")
        kinds = [c["kind"] for c in r]
        check("%s: Drill, Exam, then Review" % label, kinds[:3] == ["drill", "exam", "review"], kinds)
        check("%s: every mode still offered" % label,
              sorted(kinds) == sorted(["drill", "exam", "review", "vroom"]), kinds)
        if w >= 640 and len(r) == 4:
            check("%s: the grid reads Drill Exam / Review Virtual Room" % label,
                  r[0]["top"] == r[1]["top"] and r[2]["top"] == r[3]["top"] > r[0]["top"]
                  and r[2]["left"] < r[3]["left"], r)
        ctx.close()


# A clock the page believes, so the schedule can be read on any date.
AT_CLOCK = """(()=>{ const Real = Date; window.__realDate = Real;
  window.__at = ms => { window.Date = class extends Real {
      constructor(...a){ if(a.length) super(...a); else super(ms); }
      static now(){ return ms; } }; };
  window.__clockBack = () => { window.Date = Real; }; })();"""


def check_b245_daily_schedule(br):
    """36. "Make all the daily questions about the US constitution till
    Monday. After next Monday make it penal code ones for a week, after
    that randomize it for any of them up until and including penal code."
    Read through the app's own clock-driven entry point with a faked
    clock, so this is the question the class would actually be given on
    each date - the 5pm reset included."""
    print("\n36. build 245: the daily question follows the schedule, by date")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=AT_CLOCK)
    r = pg.evaluate("""()=>{ const out = { days: [] };
      const at = (y, m, d, hh, mm) => new __realDate(y, m - 1, d, hh, mm || 0).getTime();
      const pick = ms => { __at(ms); try { return { key: dailyPeriodKey(), qi: dailyQuestionIndexForToday() }; } finally { __clockBack(); } };
      for(let i = 0; i < 44; i++){
        const day = new __realDate(2026, 8, 30 + i);
        const p = pick(at(day.getFullYear(), day.getMonth() + 1, day.getDate(), 18));
        out.days.push({ key: p.key, qi: p.qi, topic: (QUESTIONS[p.qi].topic || '').trim() });
      }
      out.again = pick(at(2026, 10, 7, 20)).qi === pick(at(2026, 10, 8, 9)).qi;
      out.before5 = (QUESTIONS[pick(at(2026, 10, 5, 16, 59)).qi].topic || '').trim();
      out.after5 = (QUESTIONS[pick(at(2026, 10, 5, 17, 0)).qi].topic || '').trim();
      out.order = topicsIn(QUESTIONS);
      return out; }""")
    days = r["days"]
    cons = [d for d in days if d["key"] <= "2026-10-04"]
    pen = [d for d in days if "2026-10-05" <= d["key"] <= "2026-10-11"]
    mix = [d for d in days if d["key"] >= "2026-10-12"]
    allowed = r["order"][:r["order"].index(PENAL) + 1] if PENAL in r["order"] else []
    check("up to Sunday 4 October, every daily question is %s" % CONSTITUTION,
          len(cons) == 5 and all(d["topic"] == CONSTITUTION for d in cons), [d["topic"] for d in cons])
    check("Monday 5 to Sunday 11 October, every one is %s" % PENAL,
          len(pen) == 7 and all(d["topic"] == PENAL for d in pen), [d["topic"] for d in pen])
    check("from Monday 12 October, only units up to and including %s" % PENAL,
          len(mix) > 20 and all(d["topic"] in allowed for d in mix), sorted(set(d["topic"] for d in mix)))
    check("and every one of those units comes up within a month",
          set(d["topic"] for d in mix[:30]) == set(allowed),
          sorted(set(allowed) - set(d["topic"] for d in mix[:30])))
    check("the switch happens at the 5pm reset, not at midnight",
          r["before5"] == CONSTITUTION and r["after5"] == PENAL, [r["before5"], r["after5"]])
    check("one question per period, the same all period long", r["again"])
    check("no question repeats inside the Constitution days or the Penal Code week",
          len(set(d["qi"] for d in cons)) == len(cons) and len(set(d["qi"] for d in pen)) == len(pen))
    ctx.close()


def check_b245_slogan(br):
    """37. "Calling this 'the study game'" (245) and then "where it says
    'the study game' under nova, I feel like that cramps that all up ...
    either remove it or incorporate it somehow in the sentence" (268).
    It is part of the tagline now: no line of its own between NOVA and
    the tagline, the phrase leads the sentence, and Start Studying does
    not move for it - the button is measured with the new tagline and
    again with the old one put back."""
    print("\n37. build 268: 'the study game' is in the tagline, not a line of its own")
    sizes = [(440, 956), (834, 1194), (375, 667), (375, 812), (393, 852), (360, 800),
             (1024, 1366), (1728, 987), (1512, 722), (1194, 834), (956, 440)]
    for w, h in sizes:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ showHome(); await new Promise(r => setTimeout(r, 1500));
          const R = e => { const b = e.getBoundingClientRect(); return { t: b.top, b: b.bottom, h: b.height }; };
          const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
          const btn = () => R(document.getElementById('nextbtn'));
          const settle = async () => { let a = btn(); for(let i = 0; i < 30; i++){ await frame(); const b = btn(); if(Math.abs(b.t - a.t) < .05) return b; a = b; } return a; };
          await settle();
          const wrap = document.querySelector('.hometitle-wrap');
          const tag = document.querySelector('.hometagline');
          const lines = [...wrap.children].map(e => e.className);
          const own = [...document.querySelectorAll('.panel.home *')].filter(e => e !== tag && e.children.length === 0 && /^\\s*the study game\\s*$/i.test(e.textContent || '')).length;
          const out = { lines, own, text: tag.textContent, with: await settle(),
                        shown: getComputedStyle(tag).display !== 'none' && tag.getBoundingClientRect().height > 0 };
          tag.textContent = 'Master the material, one question at a time.';
          out.without = await settle();
          return out; }""")
        tag = "%dx%d" % (w, h)
        check("%s: no separate slogan line under NOVA" % tag, r["own"] == 0 and len(r["lines"]) == 2, r["lines"])
        # REVISED IN 278: "The study game. One question at a time." came
        # back as bad - she preferred "Master the material, one question at
        # a time" with the game worked in. Asserted by shape: the sentence
        # she liked still leads, and a game word is in it. (Start Studying
        # not moving, below, is what keeps it to one line on a phone.)
        check("%s: the tagline leads with 'master the material' and works a game word in" % tag,
              re.search(r"^master the material", r["text"], re.I) and re.search(r"\b(game|play|level|quest)", r["text"], re.I), r["text"])
        check("%s: Start Studying does not move for it" % tag,
              abs(r["with"]["t"] - r["without"]["t"]) < 0.6,
              [round(r["with"]["t"], 1), round(r["without"]["t"], 1)])
        ctx.close()


def check_b245_bugreport(br):
    """38. "The report a bug screen is broken, the text box is all weird"
    - it was a 999px-radius pill with a search-icon gutter and no gap to
    Send - and "the description ... talks about not sharing a code, remove
    that part". The write is read back from a Firestore stand-in: the
    document firestore-admin's `bugs` prints (name, build, viewport, UA,
    text) with nothing of the sync code in it, an empty report writes
    nothing and says so, an over-long one is capped, a failed one keeps
    the text, and a sent one says it was sent on the screen itself."""
    print("\n38. build 245: Report a bug - the field, the words, the write")
    code = "try{localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}"
    for label, w, h in DEVICES + [("iPhone SE", 320, 568)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=code)
        r = pg.evaluate("""async ()=>{ showBugReport(); await new Promise(r => setTimeout(r, 500));
          const box = document.querySelector('.screen-bugreport textarea');
          const cs = getComputedStyle(box), b = box.getBoundingClientRect();
          const send = [...document.querySelectorAll('.screen-bugreport button')].find(x => /send/i.test(x.textContent));
          const sb = send ? send.getBoundingClientRect() : null;
          return { fs: parseFloat(cs.fontSize), radius: parseFloat(cs.borderTopLeftRadius), h: b.height,
                   pl: parseFloat(cs.paddingLeft), pr: parseFloat(cs.paddingRight),
                   right: b.right, vw: innerWidth, hs: document.documentElement.scrollWidth - innerWidth,
                   gap: sb ? sb.top - b.bottom : null,
                   text: document.querySelector('.screen-bugreport').innerText }; }""")
        check("%s: the field is 16px or larger (no iOS zoom)" % label, r["fs"] >= 16, r["fs"])
        check("%s: it is a text box, not a pill" % label,
              r["radius"] <= 24 and r["radius"] < r["h"] / 4, [r["radius"], r["h"]])
        check("%s: with even padding (no search-icon gutter)" % label, abs(r["pl"] - r["pr"]) <= 2, [r["pl"], r["pr"]])
        check("%s: inside the screen" % label, r["hs"] <= 0 and r["right"] <= r["vw"], [r["hs"], r["right"]])
        check("%s: and clear of the Send button" % label, r["gap"] is not None and r["gap"] >= 8, r["gap"])
        check("%s: the words say where it goes and nothing about codes" % label,
              "whoever maintains Nova" in r["text"] and not re.search(r"\bcode\b|sync", r["text"], re.I),
              r["text"][:240])
        ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=code)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      store.publicId = 'pub-me01';
      window.__wrote = [];
      fbDb = { collection: n => ({ doc: i => ({
        set: v => { window.__wrote.push({ coll: n, id: i, data: v }); return Promise.resolve(); },
        get: () => Promise.resolve({ exists: false }), update: () => Promise.resolve(),
        delete: () => Promise.resolve() }) }) };
      showBugReport(); await wait(400);
      const box = document.querySelector('.screen-bugreport textarea');
      const send = () => [...document.querySelectorAll('.screen-bugreport button')].find(x => /send|try again/i.test(x.textContent));
      const out = {};
      send().click(); await wait(300);
      const bugs = () => window.__wrote.filter(w => String(w.id).startsWith('bug-') || (w.data && w.data.kind === 'bug'));
      out.emptyWrote = bugs().length;
      out.emptySays = document.querySelector('.screen-bugreport').innerText;
      box.value = 'The lobby jumps around when I open it. ' + 'y'.repeat(1400);
      box.dispatchEvent(new Event('input'));
      send().click(); await wait(600);
      out.wrote = bugs();
      const scr = document.querySelector('.screen-bugreport');
      out.after = scr ? scr.innerText : '';
      return out; }""")
    check("an empty report writes nothing", r["emptyWrote"] == 0, r["emptyWrote"])
    check("and says what to do, on the screen", re.search(r"write what went wrong", r["emptySays"], re.I) is not None)
    w = r["wrote"][0] if r["wrote"] else {}
    d = w.get("data") or {}
    check("a report writes one document to `vrooms` with a bug- id",
          len(r["wrote"]) == 1 and w.get("coll") == "vrooms" and str(w.get("id", "")).startswith("bug-"),
          [x.get("id") for x in r["wrote"]])
    check("carrying everything firestore-admin's `bugs` prints",
          d.get("name") == "Madison" and bool(d.get("build")) and bool(re.match(r"^\d+x\d+$", d.get("viewport") or ""))
          and bool(d.get("ua")) and (d.get("text") or "").startswith("The lobby jumps")
          and isinstance(d.get("at"), (int, float)) and d.get("kind") == "bug",
          {k: str(v)[:30] for k, v in d.items()})
    check("capped at 1,200 characters", 0 < len(d.get("text") or "") <= 1200, len(d.get("text") or ""))
    check("identified by the anonymous id, never the sync code",
          d.get("from") == "pub-me01" and "WXYZ-7777" not in json.dumps(d))
    check("and a sent report says so on the screen",
          re.search(r"report sent", r["after"], re.I) is not None, r["after"][:120])
    r2 = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      fbDb = { collection: n => ({ doc: i => ({ set: v => Promise.reject(new Error('offline')) }) }) };
      showBugReport(); await wait(300);
      const box = document.querySelector('.screen-bugreport textarea');
      box.value = 'It broke.'; box.dispatchEvent(new Event('input'));
      [...document.querySelectorAll('.screen-bugreport button')].find(x => /send/i.test(x.textContent)).click();
      await wait(400);
      const b = [...document.querySelectorAll('.screen-bugreport button')].find(x => /send|try again/i.test(x.textContent));
      return { text: document.querySelector('.screen-bugreport').innerText, enabled: !!b && !b.disabled,
               kept: box.value }; }""")
    check("a failed send says so, keeps the text and can be tried again",
          re.search(r"couldn.t send", r2["text"], re.I) is not None and r2["enabled"] and r2["kept"] == "It broke.",
          r2["text"][-160:])
    ctx.close()


# Samples every frame of the daily announcement from inside the page.
DAILY_SAMPLER = """async (opts)=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  store.dailyQuestionDate = ''; saveStore();
  localStorage.setItem('class26e.daily.seen', '2000-01-01');
  if(opts.reduce){ theme.reduceMotion = true; applyTheme(); }
  const frames = []; const t0 = performance.now(); let stop = false;
  const rot = el => { if(!el) return null; const m = getComputedStyle(el).transform;
    if(!m || m === 'none') return 0; const v = m.match(/matrix\\(([^)]+)\\)/); if(!v) return null;
    const p = v[1].split(',').map(Number); return Math.round(Math.atan2(p[1], p[0]) * 180 / Math.PI); };
  (function tick(){ if(stop) return;
    const f = document.querySelector('.daily-question-fab'), a = document.getElementById('dailyalert');
    const orb = document.querySelector('.daily-orb-core');
    const ar = a ? a.getBoundingClientRect() : null;
    frames.push({ t: performance.now() - t0,
      charging: !!(f && f.classList.contains('is-charging')),
      arcL: rot(document.querySelector('.dq-charge-l .dq-charge-arc')),
      orb: orb ? (b => [b.left + b.width / 2, b.top + b.height / 2])(orb.getBoundingClientRect()) : null,
      op: a ? parseFloat(getComputedStyle(a).opacity) : 0,
      a: ar ? [ar.left, ar.top, ar.right, ar.bottom] : null });
    requestAnimationFrame(tick); })();
  showHome();
  await wait(opts.ms);
  stop = true;
  const fb = document.querySelector('.daily-question-fab').getBoundingClientRect();
  const cb = document.getElementById('chatdock-btn');
  const ch = cb ? cb.getBoundingClientRect() : null;
  return { frames, fab: [fb.left + fb.width / 2, fb.top + fb.height / 2],
           chat: ch ? [ch.left, ch.top, ch.right, ch.bottom] : null, vw: innerWidth }; }"""


def check_b245_daily_announce(br):
    """39. "Make the banner actually come from the daily question thing so
    you can tell and make the daily question do a better 'pulse/recharge'
    effect. The effect will happen which will last 2-3 seconds, and then
    the banner/toast thing follows" - and "it disappears too soon" and "is
    kinda not centered". Every frame is sampled in the page: the ring has
    to close before the banner shows, the banner has to arrive by way of
    something that leaves the button, settle centred clear of the chat
    button, and still be up six seconds later. With Reduce motion there
    is no sequence, just the banner. The button answers a real tap
    mid-charge."""
    print("\n39. build 245: the daily question recharges, then the banner comes out of it")
    for label, w, h in DEVICES + [("iPhone SE 2", 375, 667)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate(DAILY_SAMPLER, {"ms": 12600, "reduce": False})
        fr = r["frames"]
        charge = next((f["t"] for f in fr if f["charging"]), None)
        closed = next((f["t"] for f in fr if f["arcL"] is not None and abs(f["arcL"]) >= 170), None)
        shown = next((f["t"] for f in fr if f["op"] > 0.5), None)
        orbs = [f for f in fr if f["orb"]]
        check("%s: the button starts charging as Home appears" % label, charge is not None and charge < 1000, charge)
        check("%s: the ring closes round it (a full turn)" % label, closed is not None, closed)
        # 2-3.5s until build 268 asked for "another 2-3 seconds" on the ring
        check("%s: the banner follows the recharge, 4.5-6s in" % label,
              shown is not None and closed is not None and shown >= closed and 4500 <= shown <= 6000,
              [closed, shown])
        dist0 = None
        if orbs:
            first = orbs[0]["orb"]
            dist0 = max(abs(first[0] - r["fab"][0]), abs(first[1] - r["fab"][1]))
        check("%s: and it leaves FROM the button" % label,
              bool(orbs) and dist0 <= 30 and closed is not None and orbs[0]["t"] >= closed,
              [dist0, orbs[0]["t"] if orbs else None])
        settled = [f for f in fr if f["op"] > 0.99 and f["a"] and f["t"] > (shown or 0) + 700]
        if settled:
            a = settled[0]["a"]
            if orbs:
                check("%s: the orb lands on the banner's own icon" % label,
                      a[0] <= orbs[-1]["orb"][0] <= a[0] + 60 and a[1] <= orbs[-1]["orb"][1] <= a[3],
                      [orbs[-1]["orb"], a])
            centre = (a[0] + a[2]) / 2 - r["vw"] / 2
            check("%s: the banner settles centred on the screen" % label, abs(centre) <= 2, round(centre, 1))
            ch = r["chat"]
            clear = ch is None or a[2] <= ch[0] - 4 or a[3] <= ch[1] or a[1] >= ch[3]
            check("%s: clear of the chat button" % label, clear, [a, ch])
        else:
            check("%s: the banner settles" % label, False)
        stays = [f for f in fr if f["op"] > 0.9 and shown is not None and f["t"] >= shown + 6000]
        check("%s: and is still up six seconds later" % label, bool(stays), round(fr[-1]["t"] - (shown or 0)))
        ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate(DAILY_SAMPLER, {"ms": 1500, "reduce": True})
    fr = r["frames"]
    shown = next((f["t"] for f in fr if f["op"] > 0.5), None)
    check("Reduce motion: no recharge, no orb", not any(f["charging"] or f["orb"] for f in fr))
    check("Reduce motion: just the banner, at once", shown is not None and shown < 800, shown)
    ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate("()=>{ store.dailyQuestionDate=''; saveStore(); localStorage.setItem('class26e.daily.seen','2000-01-01'); showHome(); }")
    pg.wait_for_timeout(1100)
    b = pg.evaluate("""()=>{ const f=document.querySelector('.daily-question-fab'); const r=f.getBoundingClientRect();
      return {x:r.left+r.width/2, y:r.top+r.height/2, charging:f.classList.contains('is-charging')}; }""")
    pg.mouse.click(b["x"], b["y"])
    pg.wait_for_timeout(7300)
    q = pg.evaluate("""()=>({ daily: !!document.querySelector('.qnum-daily'), orb: !!document.querySelector('.daily-orb'),
                              banner: !!document.getElementById('dailyalert') })""")
    check("a real tap on the button mid-charge opens the question", b["charging"] and q["daily"], [b, q])
    check("and nothing of the sequence is left over the question", not q["orb"] and not q["banner"], q)
    ctx.close()


def check_b245_start_pill(br):
    """40. The unit screen's Start: "an awkward shape ... could be a little
    bit wider ... a smidge bigger ... that same 3d look feel to it that
    the other buttons kinda have". Wider than tall, the same shape lit or
    not, the primary buttons' layered shadow when lit, inside the bar and
    off the other tabs on a 320px phone. In Review its label says review."""
    print("\n40. build 245: the unit screen's Start pill")
    for label, w, h in DEVICES + [("iPhone SE", 320, 568), ("iPhone SE 2", 375, 667)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
          store.seenUnitSelectTour = true; cfg.mode = 'drill'; cfg.units = []; cfg.versions = {}; showSetup(); await wait(700);
          document.querySelectorAll('#tour-overlay,#tour-tooltip').forEach(e => e.remove());
          const st = document.getElementById('bottomtab-start');
          const R = e => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
          const off = R(st);
          const cb = [...document.querySelectorAll('.picks .pick')].find(p => !/Penal/.test(p.textContent) && !p.classList.contains('locked')).querySelector('input');
          cb.click(); await wait(500);
          const on = R(st), cs = getComputedStyle(st);
          const bar = R(document.querySelector('.bottomtabs'));
          const tabs = [...document.querySelectorAll('.bottomtabs-navrow .bottomtab')].map(R);
          return { off, on, bar, tabs, vw: innerWidth, inert: st.classList.contains('is-inert'),
                   shadow: cs.boxShadow, img: cs.backgroundImage }; }""")
        on, off = r["on"], r["off"]
        wd, ht = on[2] - on[0], on[3] - on[1]
        check("%s: Start is wider than it is tall" % label, wd > ht, [round(wd), round(ht)])
        check("%s: and the same shape lit or not" % label,
              abs((off[2] - off[0]) - wd) < 1 and abs((off[3] - off[1]) - ht) < 1, [off, on])
        layers = len(re.findall(r"rgba?\(", r["shadow"]))
        check("%s: lit, it has the primary buttons' depth (highlight, lip, layered shadow)" % label,
              not r["inert"] and r["shadow"].count("inset") >= 2 and layers >= 5 and "gradient" in r["img"],
              r["shadow"][:120])
        check("%s: inside the bar and the screen" % label,
              r["bar"][0] >= 0 and r["bar"][2] <= r["vw"] and on[0] >= r["bar"][0] and on[2] <= r["bar"][2],
              [r["bar"], on])
        check("%s: and off every other tab" % label, all(t[2] <= on[0] + 0.5 for t in r["tabs"]), [r["tabs"][-1], on])
        ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    lab = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      store.seenUnitSelectTour = true; cfg.mode = 'review'; cfg.units = []; cfg.versions = {}; showSetup(); await wait(600);
      document.querySelectorAll('#tour-overlay,#tour-tooltip').forEach(e => e.remove());
      const cb = [...document.querySelectorAll('.picks .pick')].find(p => !/Penal/.test(p.textContent)).querySelector('input');
      cb.click(); await wait(400);
      return document.getElementById('bottomtab-start').getAttribute('aria-label') || ''; }""")
    check("in Review mode Start says review, not drill", lab.lower().startswith("start review"), lab)
    ctx.close()


def check_b245_daily_header(br):
    """41. On the daily question the top row is the screen label - a one-
    question run has no counter or Pause above it - and "US and Texas
    Constitution and Rights - Daily question, question 1 of 1" ran under
    the chat button. No line of it may reach the button, on any device;
    and in an ordinary test (Pause up, the button beside it) the label is
    not squeezed for a button that is not in its row."""
    print("\n41. build 245: the daily question's header clears the chat button")
    for label, w, h in DEVICES + [("iPhone SE", 320, 568)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
          store.dailyQuestionDate = ''; startDailyQuestion();
          for(let i = 0; i < 60 && !document.querySelector('.choice'); i++) await wait(150);
          await wait(700);
          const c = document.getElementById('count'); const rg = document.createRange(); rg.selectNodeContents(c);
          const lines = [...rg.getClientRects()].map(b => [b.left, b.top, b.right, b.bottom]);
          const k = document.getElementById('chatdock-btn').getBoundingClientRect();
          return { lines, chat: [k.left, k.top, k.right, k.bottom] }; }""")
        ch = r["chat"]
        hit = [l for l in r["lines"] if l[2] > ch[0] - 2 and l[0] < ch[2] and l[3] > ch[1] and l[1] < ch[3]]
        check("%s: no line of the daily header runs under the chat button" % label,
              bool(r["lines"]) and not hit, hit or r["lines"])
        ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    p = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      const U = topicsIn(QUESTIONS)[0]; const ix = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === U);
      cfg.mode = 'drill'; cfg.units = [U]; cfg.source = 'all'; beginRun(ix, null);
      for(let i = 0; i < 60 && !document.querySelector('.choice'); i++) await wait(150);
      await wait(700);
      return parseFloat(getComputedStyle(document.getElementById('count')).paddingRight); }""")
    check("in an ordinary test (Pause up) the label keeps its full width", p < 20, p)
    ctx.close()


def check_b246(br):
    """Build 246. (1) A selected character glows round it, not in a square:
    the drawing carries the shoulders-fade mask, and CSS applies an
    element's filter before its mask, so a drop-shadow on the drawing was
    cut to the mask's rectangle. The glow has to be on the button. Checked
    as the rule itself: pixel tests at the box edge could not separate
    the square from the steep edge of a round glow.
    (2) The Marksman is 150 in a row and the Hacker 25 hours; anybody under
    the new bar who is wearing one goes back to a free character, and a
    queued announcement of one is dropped. Written against build 245,
    where the corners light up and the old numbers still unlock."""
    print("\n42-43. build 246: the character glow, the raised bars, the Ranks tab, Umbra/Singularity, rank banners, banner requirements")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    g = pg.evaluate("""async ()=>{ store.legacyChars = AVATAR_CHARACTERS.map(c => c.id); store.avatarChar = 'zeus';
      showCustomize(); await new Promise(r => setTimeout(r, 1500));
      const o = document.querySelector('.avatarchar-option.selected'); const svg = o && o.querySelector('.avatarchar-svg');
      const cs = svg ? getComputedStyle(svg) : null;
      return { masked: !!cs && ((cs.maskImage || cs.webkitMaskImage || 'none') !== 'none'),
               drawingGlow: !!cs && /drop-shadow/.test(cs.filter),
               buttonGlow: !!o && /drop-shadow/.test(getComputedStyle(o).filter) }; }""")
    # The cause, checked directly: CSS applies an element's filter before
    # its mask, so a glow on the masked drawing is cut to the mask's
    # rectangle. Pixel tests at the box edge could not tell the two apart
    # reliably (the round glow is steep there too); this can.
    check("a selected character's glow is not on the masked drawing (which cuts it square), but on its button",
          g["masked"] and not g["drawingGlow"] and g["buttonGlow"], g)
    r = pg.evaluate("""()=>{ const H = 3600000, out = {}; store.legacyChars = [];
      const set = (st, h) => { store.bestTestStreak = st; /* build 267: one test */ store.studyLog = { '2026-09-01': h * H }; };
      const N = CHARACTER_FEATS.streak100.need;
      set(N - 1, 24.9); out.under = [isLockedCharacter('marksman'), isLockedCharacter('hacker')];
      set(N, 25); out.at = [isLockedCharacter('marksman'), isLockedCharacter('hacker')];
      const d = JSON.parse(JSON.stringify(store)); d.avatarChar = 'hacker'; d.studyLog = { '2026-09-01': 22 * H };
      d.bestTestStreak = 120; d.pendingCharUnlocks = ['marksman', 'clown'];
      applyLoadedData(d); out.revoked = [store.avatarChar, store.pendingCharUnlocks.slice()];
      const e = JSON.parse(JSON.stringify(store)); e.avatarChar = 'marksman'; e.bestTestStreak = N + 10;
      e.studyLog = { '2026-09-01': 30 * H }; e.pendingCharUnlocks = ['hacker'];
      applyLoadedData(e); out.kept = [store.avatarChar, store.pendingCharUnlocks.slice()];
      return out; }""")
    check("the Marksman needs its bar in a row and the Hacker 25 hours", r["under"] == [True, True] and r["at"] == [False, False], r)
    check("under the new bar, the character comes off whoever is wearing it and its announcement is dropped",
          r["revoked"][0] not in ("hacker", "marksman") and r["revoked"][1] == ["clown"], r["revoked"])
    check("at or over it, nothing is taken", r["kept"] == ["marksman", ["hacker"]], r["kept"])
    # 43. Madison's list after 245, on a real Home.
    t = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      store.legacyChars = []; store.avatarChar = 'ninja';
      for(const id of ['bottomtab-rewards', 'bottomtab-profile', 'bottomtab-settings']){
        showHome(); await wait(600);
        const before = document.querySelector('#stage > *');
        document.getElementById(id).click(); await wait(700);
        const now = document.querySelector('#stage > *');
        out[id] = !!now && now !== before && !now.classList.contains('screen-home-actual');
      }
      /* build 284: no Progress tab - the Profile card's rank row opens it */
      out.ranksScreen = (showProfile(), await wait(700), (document.querySelector('.profile-rankplate') || document.querySelector('[class*=rankplate]') || {click(){}}).click(), await wait(900),
                         !!document.querySelector('.screen-ranks'));
      out.hiddenArt = ['umbra', 'singularity'].map(id => !!characterDetail(id).hideArt);
      out.animated = ['adept_rank', 'elite_rank', 'titan_rank'].map(id => !buildBannerArt(id).classList.contains('is-still'));
      showCustomize(); await wait(900);
      out.needs = BANNERS.filter(b => !b.secret).map(b => { const o = document.querySelector('.banner-opt[data-banner="' + b.id + '"] .banner-opt-need');
        return !!o && o.textContent === b.label; });
      return out; }""")
    check("every tab on the bar opens its screen when TAPPED, and the Profile card's rank row opens the climb",
          all(t[k] for k in ("bottomtab-rewards", "bottomtab-profile", "bottomtab-settings")) and t["ranksScreen"], t)
    check("Umbra and Singularity are drawn in their pop-ups, not blacked out", t["hiddenArt"] == [False, False], t["hiddenArt"])
    check("all three rank banners animate", t["animated"] == [True, True, True], t["animated"])
    check("every banner in Customize says what it takes, under it", len(t["needs"]) > 10 and all(t["needs"]), t["needs"])
    # 44. Build 247: the Rank screen says what its rings are for, and
    # Advanced settings opens into view instead of under the tab bar.
    k = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      store.rankMapFx244 = true; store.rankMapSeen = 99;
      showRanksScreen(); await wait(900);
      const head = document.querySelector('.rankhero-gaugehead');
      out.head = head ? head.textContent : null;
      out.nextPill = !!document.querySelector('.rankhero .rankhero-nextrank');
      out.targets = [...document.querySelectorAll('.rankhero-gaugetarget')].map(x => x.textContent);
      showAppearance(); await wait(900);
      const tg = document.querySelector('.adv-toggle');
      tg.scrollIntoView({ block: 'end', behavior: 'instant' }); scrollBy(0, 40); await wait(300);
      tg.click(); await wait(1700);
      const body = tg.nextElementSibling.getBoundingClientRect(), bar = document.getElementById('bottomtabs').getBoundingClientRect();
      out.adv = { bodyBottom: Math.round(body.bottom), barTop: Math.round(bar.top), toggleTop: Math.round(tg.getBoundingClientRect().top) };
      return out; }""")
    check("the Rank screen's rings are headed with the rank they are for", bool(k["head"]) and k["head"].startswith("To reach "), k)
    check("a requirement already met says Met, not Done", "Done" not in k["targets"], k["targets"])
    # Build 248: "the next rank thing is redundant and shows it twice".
    check("the next rank is named once in the hero - by the rings' head, with no Next pill as well",
          not k["nextPill"], k)
    check("opening Advanced settings brings it clear of the tab bar, toggle still on screen",
          k["adv"]["bodyBottom"] <= k["adv"]["barTop"] and k["adv"]["toggleTop"] >= 0, k["adv"])
    ctx.close()


def check_b248_weekly(br):
    """Build 248: the week works week to week. "Ensure this works properly
    week to week." Settling a finish used to trust the rank a phone last
    SAW, and the live board for the week of 21 Sep shows what that does:
    Odin's phone last looked with Odin first, before Sauce passed him, and
    Cap's saw Cap third before Napoleon did - both would have settled a
    finish that never happened. Now it is read from the final standings,
    only from rows the server sent. Also held here: a row published in a
    new week before any XP still carries last week's total, and the
    podium reads it. Written against build 247, where the settlement
    checks fail."""
    print("\n47. build 248: week to week - the final standings settle the week, not a stale sighting")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{ const out = {}; try{
      const lw = lastWeekKey(), now = weekKeyNow();
      const d = new Date(lw + 'T12:00:00'); d.setDate(d.getDate() - 7);
      const older = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
      store.publicId = 'me000000001'; store.leaderboardOptIn = true;
      /* Today's "last week" may be a hand-recorded one; the simulated
         weeks below are not, so it is set aside and put back after. */
      const pinnedSaved = WEEK_RESULTS_KNOWN[lw]; delete WEEK_RESULTS_KNOWN[lw];
      const setRows = (fromServer, rows) => { leaderboardRows = rows; if(typeof leaderboardRowsFromServer !== 'undefined') leaderboardRowsFromServer = fromServer; };
      const mineLastWeek = pts => { store.weekKey = now; store.weekPoints = 10; store.prevWeekKey = lw; store.prevWeekPoints = pts; };
      const row = (pub, pts, rolled) => rolled ? { pub, firstName: pub, avatarChar: 'ninja', week: now, rawWeekPoints: 5, weekPoints: 5, prevWeek: lw, prevWeekPoints: pts }
                                               : { pub, firstName: pub, avatarChar: 'ninja', week: lw, rawWeekPoints: pts, weekPoints: 0 };
      const reset = () => { store.weeklyWins = 0; store.weeklyTop3 = 0; store.pendingCharUnlocks = []; };
      /* 1. Seen first on Sunday afternoon; passed that night. */
      reset(); mineLastWeek(58880); store.weekRankSeen = { week: lw, rank: 1 };
      setRows(true, [row('sauce', 58950, true), row('nap', 31500, false)]);
      settleWeeklyWin();
      out.overtaken = { wins: store.weeklyWins, top3: store.weeklyTop3, cleared: store.weekRankSeen === null };
      /* 2. Seen third, finished fourth. */
      reset(); mineLastWeek(30535); store.weekRankSeen = { week: lw, rank: 3 };
      setRows(true, [row('a', 58950, true), row('b', 58880, false), row('c', 31500, true)]);
      settleWeeklyWin();
      out.fourth = { top3: store.weeklyTop3 };
      /* 3. Only a cached board: wait, then settle when the server's arrives. */
      reset(); mineLastWeek(900); store.weekRankSeen = { week: lw, rank: 2 };
      setRows(false, [row('a', 100, true)]);
      out.waited = settleWeeklyWin() === false && !!store.weekRankSeen;
      setRows(true, [row('a', 100, true)]);
      out.thenWon = settleWeeklyWinQueued() === true && store.weeklyWins === 1 && store.weekRankSeen === null;
      /* 4. A hand-recorded week settles by its recorded order. */
      reset(); WEEK_RESULTS_KNOWN[lw] = [{ pub: 'x', pts: 5 }, { pub: 'me000000001', pts: 4 }];
      mineLastWeek(999999); store.weekRankSeen = { week: lw, rank: 1 };
      setRows(true, [row('x', 5, true)]);
      settleWeeklyWin(); delete WEEK_RESULTS_KNOWN[lw];
      out.pinned = { wins: store.weeklyWins, top3: store.weeklyTop3 };
      /* 5. Opening the app in a new week, before any XP, still publishes last week. */
      store.weekKey = lw; store.weekPoints = 4321; store.prevWeekKey = older; store.prevWeekPoints = 7;
      const pub = buildLeaderboardRow();
      out.published = { week: pub.week === now, weekPoints: pub.weekPoints, prevWeek: pub.prevWeek === lw, prevWeekPoints: pub.prevWeekPoints };
      /* 6. The podium reads rolled and unrolled rows alike, and drops a row two weeks stale. */
      const stale = { pub: 'old', firstName: 'old', avatarChar: 'ninja', week: older, rawWeekPoints: 99999, weekPoints: 0 };
      out.podium = lastWeekTop3([row('a', 300, true), row('b', 500, false), row('c', 100, true), stale]).map(t => [t.name, t.pts]);
      if(pinnedSaved) WEEK_RESULTS_KNOWN[lw] = pinnedSaved;
    } catch(e){ out.threw = String(e); } return out; }""")
    check("a phone that saw itself first but was passed later does NOT settle a win",
          r.get("overtaken", {}).get("wins") == 0 and r["overtaken"].get("top3") == 1 and r["overtaken"].get("cleared"), r)
    check("a phone that saw itself third but finished fourth settles no top-three", r.get("fourth", {}).get("top3") == 0, r)
    check("with only a cached board it waits, and settles the real result once the server's arrives",
          r.get("waited") and r.get("thenWon"), r)
    check("a hand-recorded week settles by its recorded order", r.get("pinned") == {"wins": 0, "top3": 1}, r)
    check("a row published in a new week before any XP still carries last week's total",
          r.get("published") == {"week": True, "weekPoints": 0, "prevWeek": True, "prevWeekPoints": 4321}, r)
    check("last week's podium reads rolled and unrolled rows, and ignores a row two weeks stale",
          r.get("podium") == [["b", 500], ["a", 300], ["c", 100]], r)
    ctx.close()


def check_b250(br):
    """Build 250. (1) "Some of them are animated some aren't, ensure the
    rank ladder makes all of them animated." Every emblem on the road map
    had layers with an animation on them, so a check for animations passed
    on the build she was describing - and on the screen Silver's moved
    about 2 and Gold's about 4 against 7 to 11 for the rest (the mean
    per-channel change between frames over 2.4s, on a 440x956 phone at
    2x): their motion was on their faintest lines, or a twelve-tongued
    corona turning onto itself. So this measures what is SEEN, and the
    reward chips' flares, which were not animated at all, are included.
    (2) The set was re-dealt so it reads as one story, and the final
    three are their own tier - Gold the sun with a world going round it,
    Sapphire a spiral galaxy, Amethyst a black hole with jets, Supernova
    a blast with a jagged dark heart (not a round one: that read as the
    black hole grown up) - and the three banners follow their emblems.
    Written against build 247 (the animation) and 249 (the drawings),
    where every one of these fails."""
    print("\n48-49. build 250: every emblem on the road map moves; the ladder's drawings and banners")
    from PIL import Image, ImageChops, ImageStat
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=2)
    pg.evaluate("()=>{ store.rankMapFx244 = true; store.rankMapSeen = 99; showRanksScreen(); }")
    pg.wait_for_timeout(1500)
    moved = []
    nodes = pg.locator(".rankmap-node")
    for i in range(nodes.count()):
        el = nodes.nth(i)
        el.scroll_into_view_if_needed()
        pg.wait_for_timeout(250)
        frames = []
        for _ in range(6):
            frames.append(Image.open(io.BytesIO(el.screenshot())).convert("RGB"))
            pg.wait_for_timeout(400)
        moved.append(round(max(sum(ImageStat.Stat(ImageChops.difference(frames[0], f)).mean) for f in frames[1:]), 1))
    check("every rank on the road map visibly moves - none is still beside its neighbours",
          len(moved) == 7 and min(moved) >= 4.5, moved)
    chips = pg.evaluate("""()=>[...document.querySelectorAll('.rankmap-giftav svg.rank-emblem-svg')].map(s => s.getAnimations({ subtree: true }).length)""")
    # Build 253: the reward chips' flares hold still again - 26px of
    # motion nobody can see, at 10-20 animations a chip, on a screen that
    # was running out of graphics memory on a phone.
    check("the tiny flares in the reward chips hold still", len(chips) >= 7 and all(n == 0 for n in chips), chips)
    d = pg.evaluate("""()=>{ const out = {};
      const g = buildRankEmblemSVG('veteran');
      out.orbit = !!g.querySelector('.rk-orbit') && !!g.querySelector('.rk-orbit-front');
      const a = buildRankEmblemSVG('adept');
      out.galaxy = !!a.querySelector('.rk-spin') && a.querySelectorAll('.rk-turn').length >= 1;
      const e = buildRankEmblemSVG('elite');
      out.hole = [...e.querySelectorAll('path')].some(p => p.getAttribute('fill') === '#030208') && !!e.querySelector('.rk-flare');
      const t = buildRankEmblemSVG('titan');
      const dark = [...t.querySelectorAll('path')].filter(p => p.getAttribute('fill') === '#000000');
      /* dark, but not a disc: an 8-point star is 8 curves, a circle 2-4 arcs */
      out.darkStar = dark.length > 0 && dark.every(p => (p.getAttribute('d') || '').split(/[MLQAZ]/i).length > 7);
      const html = id => buildBannerArt(id).innerHTML;
      out.sapphireBanner = /bn-spin/.test(html('adept_rank')) && /#3D74E8/i.test(html('adept_rank'));
      out.amethystBanner = /#030208/.test(html('elite_rank')) && /#A855F7/i.test(html('elite_rank')) && !/#3D74E8/i.test(html('elite_rank'));
      out.supernovaBanner = /fill="#000000"/.test(html('titan_rank'));
      return out; }""")
    check("Gold is a sun with a world going round it, in front and behind", d["orbit"], d)
    check("Sapphire is a galaxy that turns, with the final three's crown", d["galaxy"], d)
    check("Amethyst is a black hole with jets", d["hole"], d)
    check("Supernova's dark heart is a jagged star, not a round hole", d["darkStar"], d)
    check("the banners follow: Sapphire's the galaxy, Amethyst's the black hole, Supernova's the dark heart",
          d["sapphireBanner"] and d["amethystBanner"] and d["supernovaBanner"], d)
    # Build 252: "the main menu is broken. The planet and stuff isn't even
    # there." Home's hero must survive a rank drawing that throws (the
    # build-250 speed-up was taken back out, and each emblem is built
    # inside a try), and must be whole after coming back from the unit
    # screen.
    hero = pg.evaluate("""async ()=>{ const e0 = window.buildRankEmblemSVG;
      cfg.mode = 'drill'; showSetup(); await new Promise(r => setTimeout(r, 400));
      showHome(); await new Promise(r => setTimeout(r, 500));
      const back = { hero: !!document.querySelector('#stage .cosmic-hero-wrap'), ems: document.querySelectorAll('#stage .cosmic-rank-emblem').length };
      window.buildRankEmblemSVG = function(){ throw new Error('boom'); };
      let threw = null;
      try { showSetup(); await new Promise(r => setTimeout(r, 300)); showHome(); await new Promise(r => setTimeout(r, 500)); } catch(e){ threw = String(e); }
      window.buildRankEmblemSVG = e0;
      const broken = { hero: !!document.querySelector('#stage .cosmic-hero-wrap'), threw };
      showHome(); await new Promise(r => setTimeout(r, 300));
      return { back, broken }; }""")
    check("back on Home from the unit screen, the planet and all seven rank bubbles are there",
          hero["back"]["hero"] and hero["back"]["ems"] == 7, hero)
    check("and a rank drawing that fails cannot take the planet down with it",
          hero["broken"]["hero"] and not hero["broken"]["threw"], hero)
    # Build 253: "stuff is disappearing on every screen randomly." The
    # Ranks tab was running 446 animations over 557 layers (271 of them in
    # three banners, mostly scrolled out of sight) - more than a phone's
    # graphics memory holds. Only what is on screen moves now.
    load = pg.evaluate("""async ()=>{ showRanksScreen(); await new Promise(r => setTimeout(r, 1500));
      const ranks = document.getAnimations().length;
      showHome(); await new Promise(r => setTimeout(r, 1200));
      return { ranks, home: document.getAnimations().length }; }""")
    check("the Ranks tab runs a budget of animations, not hundreds (only what is on screen moves)",
          load["ranks"] <= 120 and load["home"] <= 160, load)
    # Build 256: "the glow looks to be cut off on the edges" - an earned
    # badge's light pool was still a third strong where its box ended.
    # Measured as the brightness step across the box edge (255: 8).
    ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=3)
    pg.evaluate("""async ()=>{ window.unitBadgeEarned = () => true; showProfile('badges');
      await new Promise(r => setTimeout(r, 1500));
      document.querySelector('.badge-tile.is-earned .badge-tile-art').scrollIntoView({ block: 'center', behavior: 'instant' }); }""")
    pg.wait_for_timeout(800)
    from PIL import Image as _Im
    bx = pg.evaluate("()=>{ const b = document.querySelector('.badge-tile.is-earned .badge-tile-art').getBoundingClientRect(); return [b.left, b.top, b.width, b.height]; }")
    im = _Im.open(io.BytesIO(pg.screenshot())).convert("L")
    x, y, w, h = [v * 3 for v in bx]
    px = lambda a, b: im.getpixel((int(a), int(b)))
    steps = []
    for f in (0.3, 0.5, 0.7):
        steps += [abs(px(x + w * f, y + h - 2) - px(x + w * f, y + h + 2)),
                  abs(px(x + 2, y + h * f) - px(x - 2, y + h * f)),
                  abs(px(x + w - 2, y + h * f) - px(x + w + 2, y + h * f))]
    check("an earned badge's glow fades out before its box ends - no hard edge", max(steps) <= 3, steps)
    ctx.close()


def check_b258(br):
    """Build 258, Madison's profile-card list. (1) "It says I'm 50 percent
    done but that's not even accurate, that percentage needs to be
    precise": past Silver's level with Bronze's one badge read 50% flat
    and stayed there. It is now now-over-target with the XP into the
    level and the closest unit's hundos counted, to one decimal. (2) No
    badge icons on the card. (3) One accent - the rank's - for the level,
    the XP bar and the ring, not the blue level and the theme's purple.
    (4) Midnight Oil visibly moves. (5) A banner's pop-up art spans the
    card instead of sitting 20px left of it. (6) Void's cloak joins its
    hood. (7) The Valkyrie is ten top-three finishes, the Astronaut five
    hundos in a day. Written against build 257, where each one fails."""
    print("\n47. build 258: the profile card, Midnight Oil, the banner pop-up, Void, two challenges")
    from PIL import Image, ImageChops, ImageStat
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=2)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      let p = 0; while(levelProgress(p).level < 30) p += 500; store.lifetime.points = p + 900;
      const us = topicsIn(QUESTIONS); us.forEach(u => store.unitPerfects[u] = 0);
      store.unitPerfects[us[0]] = badgeThresholdFor(us[0]); store.unitPerfects[us[3]] = 11;
      store.rankMapSeen = 99; store.rankMapFx244 = true;
      showProfile('profile'); await wait(1400);
      const thr = badgeThresholdFor(us[3]);
      /* build 266: the slower requirement, over the step from the rank held. */
      { const H = TIER_UNLOCKS[rankOf(store)] || {}, nk = TIER_ORDER_FULL[TIER_ORDER_FULL.indexOf(rankOf(store)) + 1], N = TIER_UNLOCKS[nk] || {};
        const b0 = Math.min(H.badges || 0, N.badges || 0);
        const bdg = 1 >= (N.badges || 0) ? 1 : (1 + 11 / thr - b0) / ((N.badges || 0) - b0);
        const lvl = levelOf(store) >= (N.level || 0) ? 1 : 0;
        out.lvlMet = lvl === 1; out.expect = Math.min(lvl === 1 ? 1 : 0.999, bdg); }
      out.rank = rankOf(store); out.level = levelOf(store);
      /* build 267: the plate lost its bar and label; the exact figure is
         still the one the Rank tab and the unlock cards read. */
      out.label = RANK_DISPLAY_NAME[rankStepProgress().next] + ' · ' + rankStepPctLabel(rankStepProgress().pct);
      out.plateBar = !!document.querySelector('.profile-rankplate-bar, .profile-rankplate-next');
      const sect = document.querySelector('.profile-badgesect');
      /* the ring is the count's own drawing (282); badge ART is anything else */
      out.badgeSvgs = sect ? sect.querySelectorAll('svg:not(.rankhero-ring)').length : -1;
      out.badgeText = sect ? sect.textContent : '';
      out.badgeMedal = sect ? sect.querySelectorAll('.statring').length : -1;
      const fill = document.querySelector('.profile-hero .profile-xpbar .xpbar-fill');
      out.fillBg = fill ? getComputedStyle(fill).backgroundImage : '';
      /* build 282: the level is the Rank tab's blue ring; its colour is the stroke */
      const lv = document.querySelector('.profile-hero .profile-level-num.statring .rankhero-ringtrack');
      out.levelBg = lv ? getComputedStyle(lv).stroke : '';
      out.coverMark = document.querySelectorAll('.profile-cover .profile-cover-mark').length;
      const cov = document.querySelector('.profile-cover:not(.has-banner)');
      out.coverHasTheme = !!cov && /color-mix|rgb/.test(getComputedStyle(cov).backgroundImage) && !cov.style.getPropertyValue('--card-accent');
      const av = document.querySelector('.profile-hero-avatar');
      out.ring = av ? getComputedStyle(av).boxShadow : '';
      const hex = RANK_COLOR[out.rank]; const n = parseInt(hex.slice(1), 16);
      out.rankRgb = 'rgb(' + (n >> 16) + ', ' + ((n >> 8) & 255) + ', ' + (n & 255) + ')';
      /* 5. the banner pop-up */
      showCustomize(); await wait(500);
      showUnlockDetail(bannerDetail('study50')); await wait(700);
      const sh = document.querySelector('.unlock-card'), art = document.querySelector('.unlock-card-art');
      const a = sh.getBoundingClientRect(), b = art.getBoundingClientRect();
      out.popup = [Math.round(b.left - a.left), Math.round(a.right - b.right)];
      document.querySelector('.invite-overlay').remove();
      /* 6. Void */
      const v = buildAvatarCharSVG('voidwalker'); document.body.appendChild(v);
      /* REVISED IN 278: the head is the hood path now, not an ellipse */
      const body = v.querySelector('.cx-body path'), head = v.querySelector('.cx-head path');
      const bb = body.getBBox(), hb = head.getBBox();
      out.void = { bodyTop: bb.y, headBottom: hb.y + hb.height, bodyW: bb.width };
      v.remove();
      /* 7. the two challenges */
      const f = CHARACTER_FEATS;
      /* build 289: the Koi is seven study days in a row */
      const wasLog = store.studyLog;
      store.studyLog = { '2026-03-01': 9, '2026-03-02': 9, '2026-03-03': 9, '2026-03-04': 9, '2026-03-05': 9, '2026-03-06': 9 };
      const six = f.studyrun7.done();
      store.studyLog['2026-03-07'] = 9; const seven = f.studyrun7.done();
      store.studyLog = wasLog; store.vrTop3 = 10; store.vrWins = 10; const vrNo = f.studyrun7.done() === (bestStudyRun() >= 7);
      out.valk = [six, seven, vrNo];
      out.astro = f.hundo7day.need;
      out.marks = f.streak100.need;
      /* 9. hold something you already have: the same card, marked held */
      store.avatarChar = 'ghost'; showCustomize(); await wait(700);
      const nj = [...document.querySelectorAll('.screen-customize .avatarchar-option')].find(b => b.title === 'Ninja');
      nj.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 5, clientY: 5, pointerId: 1 }));
      await wait(650);
      const held = document.querySelector('.unlock-card.is-unlocked');
      nj.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 1 })); nj.click();
      out.hold = { card: !!held, tick: !!(held && held.querySelector('.unlock-card-lock.is-held')),
        text: held ? held.innerText : '', stillGhost: store.avatarChar === 'ghost' };
      document.querySelectorAll('.invite-overlay').forEach(x => x.remove());
      nj.click(); out.hold.tapPicks = store.avatarChar === 'ninja';
      /* 8. the Ronin (263; the Knight and the Night Owl were both asked
         against): pass a test of 400 or more questions */
      const ow = AVATAR_CHARACTERS.find(c => c.id === 'ronin');
      const wasBig = store.bigTest450Passed, wasOld = store.bigTestPassed; store.bigTest450Passed = false;
      /* a pass under the old 400 rule does not hand it over (build 264) */
      store.bigTestPassed = true; const oldRuleLocked = isLockedCharacter('ronin');
      const owlLocked = isLockedCharacter('ronin');
      store.bigTest450Passed = true; const owlHeld = !isLockedCharacter('ronin');
      store.bigTest450Passed = wasBig; store.bigTestPassed = wasOld;
      const os = buildAvatarCharSVG('ronin');
      out.owl = { feat: ow && ow.feat, name: AVATAR_DISPLAY_NAME.ronin, locked: owlLocked, held: owlHeld,
        label: CHARACTER_FEATS.bigtest400.label, size: RONIN_TEST_SIZE, oldRuleLocked,
        parts: ['cx-body', 'cx-head', 'cx-eyes', 'cx-eyes-closed', 'cx-fx-roninscarf'].every(c => !!os.querySelector('.' + c)),
        knightGone: !AVATAR_CHARACTERS.some(c => c.id === 'knight' || c.id === 'nightowl'), knightDrawsAs: RETIRED_CHARACTER_TO.knight, owlDrawsAs: RETIRED_CHARACTER_TO.nightowl };
      /* 10. leaving for an update lets go of the page first */
      showHome(); await wait(400);
      releasePageForReload(); await wait(50);
      out.release = { shown: [...document.body.children].filter(e => getComputedStyle(e).display !== 'none').map(e => e.id),
        stage: stage.children.length, running: document.getAnimations().filter(a => a.playState === 'running' && !(a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest('#pushing-update'))).length };
      document.documentElement.classList.remove('is-reloading'); const pu = document.getElementById('pushing-update'); if(pu) pu.remove();
      } catch(e){ out.threw = String(e); }
      return out; }""")
    import re as _re
    def _blue(c):
        n = [int(float(x)) for x in _re.findall(r"[0-9.]+", c or "")[:3]]
        return len(n) == 3 and n[2] >= 200 and n[2] - max(n[0], n[1]) >= 50
    m = _re.search(r"([0-9]+(?:\.[0-9])?)%", r.get("label", ""))
    got = float(m.group(1)) if m else -1
    check("the rank percentage is exact, to one decimal, not the step-based 50%",
          m is not None and abs(got - int(r["expect"] * 1000) / 10) < 0.11 and got != 50, r)
    # build 266: "it looks like I'm really close except I'm still two
    # badges away" - a level already met must not hold the bar up.
    check("a met level does not prop the bar up while badges are short (266)",
          r.get("lvlMet") is True and got < 60, r)
    # REVISED IN 262: "I don't like how it says what I'm closest to" - the
    # medal and a count, no unit and no hundos.
    # AND IN 282: the medal is the Rank tab's gold ring with the count in it.
    check("no badge icons on the Profile card - the count in its ring, not the closest unit",
          r.get("badgeSvgs") == 0 and r.get("badgeMedal") == 1 and "hundo" not in r.get("badgeText", "")
          and "of 16" in r.get("badgeText", ""), r)
    # REVERSED IN 259: "No no no, the profile change is bad there. I don't
    # like the bronze all the way through." The level is blue again and
    # the default cover is the theme, with no rank on it.
    check("the level and XP bar are blue again, and the cover carries no rank",
          # REVISED IN 270: the level number is the blue coin (#3D8BFF at its
          # deepest stop), not the older #3F7FD0 - blue is what is asserted.
          # REVISED IN 282: the level is the Rank tab's ring, so blue is
          # asserted as blue (blue channel well clear of red and green)
          # rather than as one stop of a coin that is gone.
          "61, 139, 255" in r.get("fillBg", "") and _blue(r.get("levelBg", ""))
          and r.get("coverMark") == 0 and r.get("coverHasTheme") is True, r)
    check("the banner's art spans the pop-up, edge to edge", all(abs(x) <= 2 for x in r.get("popup", [99, 99])), r.get("popup"))
    vd = r.get("void") or {}
    # REVISED IN 275: "the void is worse then when we first came up with
    # him" - Void is build 215's drawing again, slim bust and all, so the
    # cloak this checked for is gone on purpose. check_b275 holds the
    # original. Here: the body still meets the bottom of the hood.
    check("Void's body meets the bottom of its hood",
          vd.get("bodyTop", 99) <= vd.get("headBottom", 0) + .5, vd)
    check("the Koi is seven study days in a row, and Virtual Room results have nothing to do with it (build 289)", r.get("valk") == [False, True, True], r.get("valk"))
    check("the Astronaut is five hundos in a day", r.get("astro") == 5, r.get("astro"))
    # REVISED IN 291: "Make the marksman challenge 250 not 200."
    check("the Marksman is 250 in a row (build 291)", r.get("marks") == 250, r.get("marks"))
    h = r.get("hold") or {}
    check("holding something you have opens its card, held: a tick, 'Unlocked', and it is not picked by the hold",
          h.get("card") and h.get("tick") and "Unlocked" in h.get("text", "") and "day one" in h.get("text", "")
          and h.get("stillGhost") and h.get("tapPicks"), h)
    ow = r.get("owl") or {}
    check("the Knight and the Night Owl are gone; the Ronin is passing a 450-question test, and an old 400 pass does not count",
          ow.get("feat") == "bigtest400" and ow.get("name") == "Ronin" and ow.get("owlDrawsAs") == "ninja" and ow.get("locked") is True and ow.get("held") is True
          and "450" in ow.get("label", "") and ow.get("size") == 450 and ow.get("oldRuleLocked") is True and ow.get("parts") is True and ow.get("knightGone") is True and ow.get("knightDrawsAs") == "ninja", ow)
    rl = r.get("release") or {}
    check("before an update reloads, only the Pushing update bar is left and nothing else is animating",
          rl.get("shown") == ["pushing-update"] and rl.get("stage") == 0 and rl.get("running") == 0, rl)
    # 4. Midnight Oil, measured the way section 45 measures the ladder
    pg.evaluate("""()=>{ document.querySelectorAll('.invite-overlay').forEach(x => x.remove());
      const w = document.createElement('div'); w.id = 'bn258';
      w.style.cssText = 'position:fixed;left:20px;top:200px;width:400px;height:150px;z-index:99999;overflow:hidden';
      const b = buildBannerArt('study50'); b.style.cssText = 'position:absolute;inset:0'; w.appendChild(b); document.body.appendChild(w); }""")
    pg.wait_for_timeout(700)
    el = pg.locator("#bn258"); fr = []
    for _ in range(8):
        fr.append(Image.open(io.BytesIO(el.screenshot())).convert("RGB")); pg.wait_for_timeout(350)
    mv = round(max(sum(ImageStat.Stat(ImageChops.difference(fr[0], f)).mean) for f in fr[1:]), 1)
    check("Midnight Oil visibly moves (it measured about 3.6-4; now 8-12)", mv >= 6, mv)
    ctx.close()


B245_POLISH = ["modes", "daily_schedule", "slogan", "bugreport", "daily_announce", "start_pill", "daily_header"]


def check_b266(br):
    """Build 266, Madison's list. (1) Review's chip on the unit screen is
    green, not Drill's red. (2) Tapping the character you already have on
    opens its card, and nothing on that card can be text-selected by the
    hold. (3) The Virtual Room front door is two cards, Private and
    Public. (4) A new room starts with NO game and cannot start until one
    is picked. (5) The Open-to-the-class switch is a switch-shaped track
    inside a 44px target, not a 51x44 lozenge. (6) A lobby character's
    glow comes off a wrapper, never the masked svg - the square. (7)
    Sapphire carries a black dot, Amethyst has no flattened disc. (8) The
    redrawn characters: Hacker at a laptop, Viper with a tongue, the
    Kraken on Poseidon's id, the Singularity hooded. Written against 265,
    where each one fails."""
    print("\n48. build 266: review tint, tap-to-card, the Virtual Room door, an empty room, the switch, the glow, the emblems, the characters")
    import re as _re
    vr = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-vroom.py")).read()
    fake = _re.search(r'FAKE_FIRESTORE = """(.*?)"""', vr, _re.S).group(1)
    # The harness stubs onSnapshotResilient; the lobby needs the real one
    # listening to the fake, so it is kept aside before the stub lands.
    keep = "window.addEventListener('DOMContentLoaded', function(){ try{ window.__osr = onSnapshotResilient; }catch(e){} });"
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=fake + "\n" + keep)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      document.documentElement.classList.remove('is-reloading'); const pu = document.getElementById('pushing-update'); if(pu) pu.remove();
      /* 1 */
      cfg.mode = 'review'; showSetup(); await wait(400);
      const chip = document.querySelector('.setup-modechip .rs-mode');
      out.chip = chip ? chip.className : '';
      /* 2 */
      showCustomize(); await wait(500);
      const sel = document.querySelector('.screen-customize .avatarchar-option.selected');
      if(sel){ sel.click(); await wait(500); }
      const card = document.querySelector('.invite-sheet.unlock-card');
      out.tapCard = !!card;
      out.cardSelect = card ? getComputedStyle(card).userSelect || getComputedStyle(card).webkitUserSelect : '';
      document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
      /* 3 */
      try{ __useFake(); if(window.__osr) onSnapshotResilient = window.__osr; }catch(e){}
      showVirtualRoomChoice(); await wait(300);
      out.cards = [...document.querySelectorAll('.vrc-modecard')].map(c => ({ mode: c.classList.contains('modecard'), icon: !!c.querySelector('.modeicon'),
        title: (c.querySelector('.modecardtitle') || {}).textContent || '', desc: (c.querySelector('.modecarddesc') || {}).textContent || '' }));
      /* 4 */
      document.querySelector('.vrc-card-host').click();
      for(let i = 0; i < 30 && !document.querySelector('.vroom-test-summary'); i++) await wait(150);
      await wait(600);
      out.summary = (document.querySelector('.vroom-test-summary') || {}).textContent || '';
      out.note = (document.querySelector('.vroom-autostart-note, .vroom-autostart') || {}).textContent || '';
      out.game = null;
      try{ const d = await fbDb.collection('vrooms').doc(vroomCode).get(); out.game = d.data().game; out.hasGameKey = 'game' in d.data(); }catch(e){ out.gameErr = String(e); }
      /* 5 */
      const sw = document.querySelector('.vroom-open-toggle');
      if(sw){ const b = sw.getBoundingClientRect(), tr = getComputedStyle(sw, '::before');
        out.sw = { h: Math.round(b.height), w: Math.round(b.width), trackH: parseFloat(tr.height), trackBg: getComputedStyle(sw).backgroundColor }; }
      /* 6 */
      const av = document.querySelector('.vroom-avatar');
      if(av){ const w = av.querySelector(':scope > .rank-avatar'), sv = av.querySelector('svg');
        out.glow = { wrapFilter: w ? getComputedStyle(w).filter : '', svgFilter: getComputedStyle(sv).filter, svgMask: getComputedStyle(sv).maskImage || getComputedStyle(sv).webkitMaskImage }; }
      /* 7 */
      /* build 267: the dot became a dark heart fading into the core, with dust spinning in */
      out.sapphireDot = [...buildRankEmblemSVG('adept').querySelectorAll('path')].some(p => p.getAttribute('fill') === '#000000');
      out.amethystFlat = /scale\\(1 \\.19\\)/.test(buildRankEmblemSVG('elite').innerHTML);
      out.amethystHole = [...buildRankEmblemSVG('elite').querySelectorAll('path')].some(p => p.getAttribute('fill') === '#030208');
      /* 8 */
      const cls = id => ((buildAvatarCharSVG(id).querySelector('.cx-fig') || {getAttribute(){return ''}}).getAttribute('class') || '');
      const has = (id, sel) => !!buildAvatarCharSVG(id).querySelector(sel);
      out.kraken = { kind: cls('poseidon'), name: AVATAR_DISPLAY_NAME.poseidon };
      out.hacker = { rain: has('hacker', '.cx-fx-hk3rain'), laptop: buildAvatarCharSVG('hacker').innerHTML.indexOf('M18 30.8 L16.5 32.3') >= 0 };
      /* build 267: the Valkyrie's id is the Koi's fishbowl, the Singularity a space cat */
      out.viper = { tongue: has('valkyrie', '.cx-fx-koiswim'), name: AVATAR_DISPLAY_NAME.valkyrie };
      out.sing = { swirl: has('singularity', '.cx-fx-sghair'), eyes: buildAvatarCharSVG('singularity').querySelectorAll('.cx-eyes > *').length };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("Review's chip on the unit screen is Review's, not Drill's", "rs-mode-review" in r.get("chip", ""), r)
    check("tapping the character you already have on opens its card", r.get("tapCard") is True, r)
    check("and nothing on that card can be selected by the hold", r.get("cardSelect") == "none", r)
    # build 287: the two ways in are mode cards, and Host does not call itself private
    cs = r.get("cards", [])
    check("the Virtual Room door is two mode cards, each with a mode icon: host and join",
          len(cs) == 2 and all(x["mode"] and x["icon"] for x in cs), cs)
    check("and Host says it starts invite only and can be opened, not that it is private",
          len(cs) == 2 and "invite only" in cs[0]["desc"].lower() and "open" in cs[0]["desc"].lower(), cs)
    check("a new room starts with no game chosen", r.get("hasGameKey") is True and r.get("game") is None, r)
    check("and the lobby says so instead of saying Race",
          "No game chosen yet" in r.get("summary", "") and "Race" not in r.get("summary", ""), r)
    sw = r.get("sw") or {}
    check("the Open-to-the-class switch is a track inside a 44px target, not a lozenge",
          sw.get("h") == 44 and 28 <= (sw.get("trackH") or 0) <= 36 and (sw.get("w") or 0) / max(1, sw.get("trackH") or 1) >= 1.5
          and sw.get("trackBg") in ("rgba(0, 0, 0, 0)", "transparent"), sw)
    g = r.get("glow") or {}
    check("a lobby character's glow comes off the wrapper, never the masked drawing",
          "drop-shadow" in g.get("wrapFilter", "") and "drop-shadow" not in g.get("svgFilter", ""), g)
    check("Sapphire has a black dot at its heart", r.get("sapphireDot") is True, r)
    check("Amethyst is a black hole with no flattened planet disc", r.get("amethystHole") is True and r.get("amethystFlat") is False, r)
    # REVISED IN 271-273: the Kraken became the Kitsune, the Vampire, then the Sheriff.
    check("Poseidon's id draws the Sheriff, and says so", "cx-k-sheriff" in r["kraken"]["kind"] and r["kraken"]["name"] == "Sheriff", r["kraken"])
    check("the Hacker sits at a laptop with code raining behind", r["hacker"]["rain"] and r["hacker"]["laptop"], r["hacker"])
    # REVISED IN 267: "That snake character is bad, try something else" and
    # "the singularity, idek what that is".
    check("the Valkyrie's id is the Koi, a fish swimming laps in a pink bowl", r["viper"]["tongue"] and r["viper"]["name"] == "Koi", r["viper"])
    # REVISED IN 271: "The singularity is a cat. That needs to be changed
    # immediately" - a hooded figure caught in an accretion disk.
    check("the Singularity has its rising hair and its eyes", r["sing"]["swirl"] and r["sing"]["eyes"] >= 2, r["sing"])
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b267(br):
    """Build 267, Madison's list. (1) The middle ring's dot orbits faster
    than the outer ones. (2) The Virtual Room cards' icons sit on coloured
    tiles. (3) Sapphire's dark heart has dust spinning in it, faster than
    the arms; Supernova throws dark shards. (4) The Marksman is a
    single-test streak: a lifetime streak of 500 does not unlock it.
    (5) Every XP bar is the unlock card's bar. (6) The Profile rank plate
    has no bar, and the level is not boxed in. (7) The start sheet closes
    on a swipe down from its middle, not only its handle. (8) A toast
    shown while the start sheet is open sits above it. Written against
    266, where each one fails."""
    print("\n49. build 267: orbit, icons, the dark heart, the Marksman, the XP bar, the plate, the sheet, the toast")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      document.documentElement.classList.remove('is-reloading'); const pu = document.getElementById('pushing-update'); if(pu) pu.remove();
      showHome(); await wait(900);
      const dur = el => el ? parseFloat(getComputedStyle(el).animationDuration.split(',').pop()) : 0;
      out.orbit = { outer: dur(document.querySelector('.cosmic-hero-orbitlayer:not(.cosmic-hero-orbitlayer-inner)')),
                    inner: dur(document.querySelector('.cosmic-hero-orbitlayer-inner')),
                    innerDots: document.querySelectorAll('.cosmic-hero-orbitlayer-inner .cosmic-orbit-dot').length };
      showVirtualRoomChoice(); await wait(300);
      out.icons = [...document.querySelectorAll('.vrc-modecard .modeicon')].map(i => { const q = i.querySelector('.modeiconpath'); const k = q ? getComputedStyle(q).stroke : ''; return !!k && k !== 'none' && k !== 'rgb(0, 0, 0)' && k !== 'rgb(255, 255, 255)'; })
      out.iconsOld = [...document.querySelectorAll('.vrc-card-icon')].map(i => getComputedStyle(i).backgroundImage.indexOf('gradient') >= 0
        && [...i.querySelectorAll('[fill]')].some(e => /^#(?!fff\\b|ffffff\\b)/i.test(e.getAttribute('fill'))));
      const a = buildRankEmblemSVG('adept');
      out.dust = !!a.querySelector('.rk-spin.rk-fast') && [...a.querySelectorAll('.rk-spin.rk-fast path')].some(p => /^#0[0-9A-F]{5}$/i.test(p.getAttribute('fill') || ''));
      out.shards = !!buildRankEmblemSVG('titan').querySelector('.rk-spin.rk-fast');
      const keep = [store.bestTestStreak, store.lifetime.longestStreak];
      store.bestTestStreak = 0; store.lifetime.longestStreak = 500; out.lifetimeLocked = isLockedCharacter('marksman');
      store.bestTestStreak = CHARACTER_FEATS.streak100.need; out.testUnlocked = !isLockedCharacter('marksman');
      store.bestTestStreak = keep[0] || 0; store.lifetime.longestStreak = keep[1];
      out.defaulted = (() => { const d = JSON.parse(JSON.stringify(store)); delete d.bestTestStreak; applyLoadedData(d); return store.bestTestStreak; })();
      showProfile('profile'); await wait(1400);
      const f = document.querySelector('.profile-xpbar .xpbar-fill'), tr = document.querySelector('.profile-xpbar');
      out.xp = { bg: getComputedStyle(f).backgroundImage, tr: getComputedStyle(f).transitionDuration, h: Math.round(tr.getBoundingClientRect().height),
                 /* build 282: ::after is the pump's wash now (opacity
                    only); a SHEEN is a travelling gradient across it */
                 sheen: (()=>{ const a = getComputedStyle(f, '::after');
                   return a.content === 'none' || a.content === 'normal' ? 'none'
                     : (/gradient/.test(a.backgroundImage) || a.animationName === 'xp-sheen') ? 'sheen' : 'none'; })() };
      out.plate = { bar: !!document.querySelector('.profile-rankplate .profile-rankplate-bar, .profile-rankplate .profile-rankplate-next') };
      const lv = document.querySelector('.profile-level-num');
      out.level = { bg: getComputedStyle(lv).backgroundColor, border: getComputedStyle(lv).borderTopWidth,
                    round: Math.abs(lv.getBoundingClientRect().width - lv.getBoundingClientRect().height) < 1 && parseFloat(getComputedStyle(lv).borderTopLeftRadius) >= lv.getBoundingClientRect().width / 2 - 1 };
      cfg.mode = 'drill'; cfg.units = [topicsIn(QUESTIONS)[0]]; showSetup(); await wait(600);
      document.getElementById('nextbtn').click(); await wait(500);
      showToast('test toast'); await wait(300);
      const t = document.querySelector('.toast'), m = document.getElementById('unitoptions-modal');
      out.toastZ = t ? parseInt(getComputedStyle(t).zIndex) : -1; out.sheetZ = m ? parseInt(getComputedStyle(m).zIndex) : -1;
      const sh = document.querySelector('.unitoptions-modal-sheet').getBoundingClientRect();
      out.sheetMid = [Math.round(innerWidth / 2), Math.round(sh.top + Math.min(160, sh.height / 2))];
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    x, y = (r.get("sheetMid") or [220, 500])
    cdp = ctx.new_cdp_session(pg)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for i in range(1, 14):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y + i * 14}]})
        pg.wait_for_timeout(16)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(600)
    closed = pg.evaluate("()=>{ const m = document.getElementById('unitoptions-modal'); return !!m && m.hidden; }")
    o = r.get("orbit") or {}
    check("the middle ring's dot turns faster than the outer ring", o.get("innerDots", 0) >= 1 and 0 < o.get("inner", 0) < o.get("outer", 0), o)
    check("both Virtual Room card icons are mode icons, in colour (build 287)", r.get("icons") == [True, True], r.get("icons"))
    check("Sapphire's dark heart has dark dust spinning faster than its arms", r.get("dust") is True, r)
    check("Supernova throws dark shards of its own", r.get("shards") is True, r)
    check("a lifetime streak does not unlock the Marksman; one test's does",
          r.get("lifetimeLocked") is True and r.get("testUnlocked") is True and r.get("defaulted") == 0, r)
    xp = r.get("xp") or {}
    check("the XP bar is the unlock card's bar in blue: its .9s glide, no sheen",
          "61, 139, 255" in xp.get("bg", "") and xp.get("tr", "").startswith("0.9") and xp.get("h", 99) <= 12
          and xp.get("sheen") in ("none", "normal"), xp)
    check("the Profile rank plate has no bar", (r.get("plate") or {}).get("bar") is False, r.get("plate"))
    lv = r.get("level") or {}
    # 267 took the level out of its box; 270 put it in the rank plate's
    # coin ("the level number could kind of get that same look"), which is
    # a round lit well, not the square plate 267 removed.
    check("the level is not in a square box", lv.get("bg") in ("rgba(0, 0, 0, 0)", "transparent") or lv.get("radius", "").endswith("%") or lv.get("round"), lv)
    check("a toast sits above an open start sheet", r.get("toastZ", -1) > r.get("sheetZ", 0) > 0, [r.get("toastZ"), r.get("sheetZ")])
    check("the start sheet closes on a swipe down from its middle", closed is True, closed)
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b268(br):
    """Build 268, Madison's list. (1) The answer-streak pop sits on the
    screen's centre line, not in the middle of the gap beside it. (2) A
    cutscene hands straight to the pop-up after it: the screen never comes
    back up between the two. (3) The unit screen's bar is Home's width on a
    phone and its icons have room. (4) The road map's light rides the line
    exactly while it fills. Written against 267, where each one fails."""
    print("\n50. build 268: streak pop centred, cutscene into pop-up, unit bar spacing, road map light")
    # 1. The streak pop's placement was checked here until build 284 took
    # the pop out of the test altogether (check_b284 asserts it is gone).
    # 2. flare scene -> its pop-up, sampled every frame: how much of the
    # screen is covered by the scene, the bridge it leaves or the pop-up's dim
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ showHome(); await new Promise(r => setTimeout(r, 600));
      theme.muteBanners = false;
      const cover = () => { let c = 0;
        document.querySelectorAll('.fl-scene, .scene-bridge').forEach(e => { c = Math.max(c, parseFloat(getComputedStyle(e).opacity) || 0); });
        const sp = document.querySelector('.rs-spot'); if(sp){ const m = getComputedStyle(sp).backgroundColor.match(/rgba?\\(([^)]+)\\)/);
          const a = m ? m[1].split(',').map(Number) : []; c = Math.max(c, (a.length > 3 ? a[3] : 1) / .72); }
        return c; };
      const frames = []; let stop = false, spotAt = null; const t0 = performance.now();
      (function tick(){ if(stop) return; frames.push([performance.now() - t0, cover(), !!document.querySelector('.rs-spot')]); requestAnimationFrame(tick); })();
      const color = VOID_FLARES[0];
      await new Promise(done => playFlareFoundScene(color, false, () => setTimeout(() => {
        spotAt = performance.now() - t0;
        playUnlockSpotlight({ kind: 'banner', kicker: 'Test', name: 'Test', sub: '', color: '#6FC2FF', art: () => document.createElement('div') }, 1, 1, () => {});
        done(); }, 320)));
      await new Promise(r => setTimeout(r, 1500)); stop = true;
      const peak = frames.find(f => f[1] > .95);
      const after = frames.filter(f => peak && f[0] > peak[0] && f[0] <= spotAt + 1200);
      const low = after.reduce((m, f) => Math.min(m, f[1]), 1);
      return { low: Math.round(low * 100) / 100, spotAt: Math.round(spotAt), n: after.length }; }""")
    check("a flare scene hands to its pop-up without the screen coming back up in between",
          r["n"] > 10 and r["low"] >= 0.9, r)
    ctx.close()
    # 3. the unit screen's bar on a phone
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
      const meas = () => { const bar = document.querySelector('.bottomtabs');
        const ic = [...bar.querySelectorAll('.bottomtabs-navrow .bottomtab-icon')].filter(e => e.getBoundingClientRect().width > 0).map(e => e.getBoundingClientRect());
        return { w: Math.round(bar.getBoundingClientRect().width), gap: Math.min.apply(null, ic.slice(1).map((r, i) => r.left - ic[i].right)) }; };
      showHome(); await w(600); const home = meas();
      store.seenUnitSelectTour = true; cfg.mode = 'drill'; cfg.units = []; showSetup(); await w(900);
      const st = document.getElementById('bottomtab-start');
      return { home, setup: meas(), fits: st.scrollWidth <= st.clientWidth }; }""")
    check("17 Pro Max: the unit screen's bar is as wide as Home's", abs(r["setup"]["w"] - r["home"]["w"]) <= 1, r)
    check("and its icons are at least 30px apart", r["setup"]["gap"] >= 30, r)
    check("and Start still fits its pill", r["fits"], r)
    ctx.close()
    # 4. the road map's light
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      levelOf = () => 40; badgeCountOf = () => 4;
      showProfile('ranks'); await wait(3500); showHome(); await wait(300);
      const frames = []; let stop = false;
      (function tick(){ if(stop) return;
        const d = document.querySelector('.rankmap-roadtip-dot') || document.querySelector('.rankmap-roadtip');
        const st = d && d.closest('.rankmap-stop'); const f = st && st.querySelector('.rankmap-roadfill');
        if(d && f){ const a = d.getBoundingClientRect(), b = f.getBoundingClientRect(); frames.push(Math.abs((a.top + a.height / 2) - b.bottom)); }
        requestAnimationFrame(tick); })();
      showProfile('ranks'); await wait(2800); stop = true;
      return { n: frames.length, worst: Math.round(Math.max.apply(null, frames.concat([0])) * 10) / 10 }; }""")
    check("the road map's light rides the end of the line while it fills (within 1.5px every frame)",
          r["n"] > 20 and r["worst"] <= 1.5, r)
    ctx.close()


def check_b269(br):
    """Build 269: "when looking at the unlockable characters and you hold it
    down or whatever to see the details ... ensure the character is doing
    its animated move there ... same for banners, themes". Every
    character's card is live (running animations under the card's art),
    an animated banner runs on its card, and a theme's swatch both swirls
    and carries the gloss sweep the Customize swatches have. Written
    against 268, where every character card was frozen."""
    print("\n51. build 269: unlock cards are alive - characters, banners, themes")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
      const live = root => root ? root.getAnimations({subtree:true}).filter(a => a.playState === 'running') : [];
      const open = async o => { document.querySelectorAll('.invite-overlay').forEach(e => e.remove()); showUnlockDetail(o); await w(300);
        return document.querySelector('.unlock-card .unlock-card-art'); };
      const frozen = [];
      for(const c of AVATAR_CHARACTERS){ const a = await open(characterDetail(c.id)); if(!live(a).length) frozen.push(c.id); }
      const held = await open(Object.assign(characterDetail(AVATAR_CHARACTERS[0].id), { unlocked: true }));
      const heldLive = live(held).length;
      const bn = await open(bannerDetail(BANNER_ANIMATED[0])); const bannerLive = live(bn).length;
      const th = await open(themeDetail('titan')); const names = live(th).map(a => a.animationName);
      return { n: AVATAR_CHARACTERS.length, frozen, heldLive, bannerLive, theme: names }; }""")
    check("every character moves on its unlock card (%d characters)" % r["n"], not r["frozen"], r["frozen"])
    check("and on the card of one you already hold", r["heldLive"] > 0, r["heldLive"])
    check("an animated banner runs on its card", r["bannerLive"] > 0, r["bannerLive"])
    check("a theme's swatch swirls and carries the gloss sweep",
          "legend-swirl" in r["theme"] and "swatch-sheen" in r["theme"], r["theme"])
    ctx.close()


def check_b270(br):
    """Build 270, Madison's list. (1) The unit details card is the same
    four numbers in every mode, one of them the last score. (2) Most
    missed has no flag on its questions and does not mention how much is
    tracked; both lists end in a Back button; a list's choices are
    read-only (locked) and its "Missed N times" chip is the door's
    colour. (3) Back from a list puts the card back to its own size.
    (4) Every back link's chevron and word share a centre line. (5) No
    unit badge's drawing leaves its viewBox (Multiculturalism's top was
    cut off). (6) The Profile rank plate has no white flash. Written
    against 269, where each of these fails."""
    print("\n52a. build 270: unit details, the two lists, back links, badges, the rank plate")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      const wait = ms => new Promise(r => setTimeout(r, ms));
      try {
      const u = topicsIn(QUESTIONS), unit = u[0], now = Date.now();
      out.labels = ['drill', 'exam', 'review'].map(m => unitDetailStats(unit, m).map(s => s.label));
      let k = 0;
      QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === unit){ k++; store.stats[KEYS[i]] = { n: 3, m: 3, r: [now - 1000, now - 2000] }; if(k <= 3) store.flagged[KEYS[i]] = true; } });
      cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(600);
      const row = [...document.querySelectorAll('.pick')].find(r => (r.querySelector('input') || {}).value === unit);
      row.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 50, clientY: 50, button: 0 }));
      await wait(600); row.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 50, clientY: 50 })); await wait(900);
      const card = () => document.querySelector('.unitdetail');
      out.h0 = Math.round(card().getBoundingClientRect().height);
      /* build 284: Flagged is the only list, so it carries the list checks */
      document.querySelector('.unitdetail-door.is-flagged').click(); await wait(900);
      const c = card();
      out.missed = { flags: c.querySelectorAll('.unitdetail-q .unitdetail-flag').length,
        note: (c.querySelector('.unitdetail-listnote') || {}).textContent || '',
        bottomBack: !!c.querySelector('.unitdetail-back.is-bottom'),
        choices: c.querySelectorAll('.unitdetail-q .choice').length,
        unlocked: [...c.querySelectorAll('.unitdetail-q .choice')].filter(b => !b.classList.contains('locked')).length };
      /* and pressing one does not press it: the Liquid Glass dip is off */
      { const ch0 = c.querySelector('.unitdetail-q .choice'); const rb = ch0.getBoundingClientRect();
        ch0.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: rb.left + 5, clientY: rb.top + 5, button: 0 }));
        out.missed.pressed = ch0.style.transform || '';
        ch0.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: rb.left + 5, clientY: rb.top + 5 })); }
      out.recentDoor = document.querySelectorAll('.unitdetail-door.is-recent').length;
      c.querySelector('.unitdetail-back').click(); await wait(900);
      /* Settle rather than trust the 900ms: under a loaded full run the
         card was read mid-transition (786 against 419) on a build where
         it ends at 419. Wait for the height to hold still, up to 3s. */
      { let last = -1, still = 0; for(let i = 0; i < 60 && still < 4; i++){ const hh = Math.round(card().getBoundingClientRect().height); still = hh === last ? still + 1 : 0; last = hh; await wait(50); } }
      out.h1 = Math.round(card().getBoundingClientRect().height);
      document.querySelector('.unitdetail-door.is-flagged').click(); await wait(900);
      out.flagged = { flags: card().querySelectorAll('.unitdetail-q .unitdetail-flag').length, bottomBack: !!card().querySelector('.unitdetail-back.is-bottom') };
      /* back links */
      const bl = buildBackLink('Back', () => {}); bl.style.cssText = 'position:fixed;left:10px;top:10px'; document.body.appendChild(bl);
      const ch = bl.querySelector('.back-chevron'), wd = bl.querySelector('.back-word');
      if(ch && wd){ const a = ch.getBoundingClientRect(), b = wd.getBoundingClientRect(); out.backOff = Math.abs((a.top + a.bottom) / 2 - (b.top + b.bottom) / 2); }
      else out.backOff = 99;
      bl.remove();
      /* every badge inside its own box */
      const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:200px;height:200px'; document.body.appendChild(host);
      out.clipped = [];
      for(const n of u){ host.replaceChildren(); const sv = buildUnitBadgeSVG(n, true); if(!sv) continue; sv.style.cssText = 'width:200px;height:200px'; host.appendChild(sv);
        /* on screen, so every transform is applied: each drawn path's box
           against the svg's own box */
        const box = sv.getBoundingClientRect();
        const out1 = [...sv.querySelectorAll('path')].filter(p => !p.closest('defs, clipPath, mask, [clip-path]')).some(p => { const b = p.getBoundingClientRect();
          return b.width && (b.left < box.left - .5 || b.top < box.top - .5 || b.right > box.right + .5 || b.bottom > box.bottom + .5); });
        if(out1) out.clipped.push(n); }
      host.remove();
      /* the rank plate */
      document.querySelectorAll('.unitdetail-scrim, .unitdetail').forEach(e => e.remove());
      showProfile('profile'); await wait(900);
      const plate = document.querySelector('.profile-rankplate');
      out.plateAfter = plate ? getComputedStyle(plate, '::after').content : 'missing';
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    L = r.get("labels") or []
    check("the unit card is the same four numbers in every mode, the last score among them",
          len(L) == 3 and L[0] == L[1] == L[2] and len(L[0]) == 4 and any("ast" in x for x in L[0]), L)
    m = r.get("missed") or {}
    check("there is no Most missed list (build 284), and the Flagged list shows its questions", r.get("recentDoor") == 0 and m.get("choices", 0) > 0, m)
    check("both lists end in a Back button", m.get("bottomBack") and (r.get("flagged") or {}).get("bottomBack"), (m, r.get("flagged")))
    check("Flagged keeps its flags", (r.get("flagged") or {}).get("flags", 0) > 0, r.get("flagged"))
    check("a list's answer choices are read-only, and do not press like buttons", m.get("unlocked") == 0 and not m.get("pressed"), m)
    check("Back from a list puts the card back to its own size", abs((r.get("h1") or 0) - (r.get("h0") or -99)) <= 4, (r.get("h0"), r.get("h1")))
    check("a back link's chevron and word share a centre line", r.get("backOff", 99) <= 1, r.get("backOff"))
    check("no unit badge's drawing leaves its box", r.get("clipped") == [], r.get("clipped"))
    check("the Profile rank plate has no white flash", r.get("plateAfter") in ("none", "normal"), r.get("plateAfter"))
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b271(br):
    """Build 271, the characters. (1) Every character stands in a scene of
    its own - a backdrop outside the figure, faded by a MASK (never a
    filter), unscaled when the figure is enlarged, moving only under
    char-live. (2) The Singularity is no longer a cat: it is the third of
    Void's hooded family, caught in an accretion disk, a flare on its
    brow. (3) Poseidon's id is the Kitsune, with tails; the astronaut id
    the Cyborg, with a cyber-eye - and both say so by name. (4) The Koi
    has two fish. (5) The Alien's eyes slant hard and a brow cuts them.
    (6) Void is lit down one side by flare light, like its family.
    Written against 270, where none of it held."""
    print("\n52. build 271: a scene behind every character; the Singularity, Kitsune, Cyborg, Koi, Alien and Void")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const active = AVATAR_CHARACTERS.filter(c => !c.retired).map(c => c.id);
      out.n = active.length;
      out.noScene = []; out.badScene = [];
      for(const id of active){
        const sv = buildAvatarCharSVG(id), bg = sv.querySelector('.cx-bg');
        if(!bg){ out.noScene.push(id); continue; }
        const m = bg.getAttribute('mask') || '';
        if(bg.parentNode !== sv || bg.closest('.cx-fig') || !/^url\\(#/.test(m) || sv.querySelector('filter')) out.badScene.push(id);
      }
      /* two characters' scenes should not be the same picture */
      const sig = id => { const bg = buildAvatarCharSVG(id).querySelector('.cx-bg'); return bg ? [...bg.querySelectorAll('[class*="cx-fx-bg"]')].map(g => g.getAttribute('class')).join('|') : ''; };
      out.sameScene = sig('detective') === sig('frost') || sig('ronin') === sig('solar');
      /* motion only when live */
      const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:120px;height:120px';
      host.appendChild(buildAvatarCharSVG('frost')); document.body.appendChild(host);
      const fall = () => getComputedStyle(host.querySelector('.cx-fx-bgfall')).animationName;
      out.stillFall = fall(); host.classList.add('char-live'); out.liveFall = fall(); host.remove();
      /* the Singularity */
      const sg = buildAvatarCharSVG('singularity');
      out.sing = { cat: !!sg.querySelector('[class*="cx-fx-cat"]'), disk: !!sg.querySelector('.cx-fx-sghair'),
                   star: !!sg.querySelector('.cx-fx-sgstar'), eyes: sg.querySelectorAll('.cx-eyes > *').length };
      /* Kitsune and Cyborg */
      const kind = id => (buildAvatarCharSVG(id).querySelector('.cx-fig').getAttribute('class') || '').replace('cx-fig cx-k-', '');
      out.pos = { kind: kind('poseidon'), name: AVATAR_DISPLAY_NAME.poseidon };
      out.ast = { kind: kind('astronaut'), name: AVATAR_DISPLAY_NAME.astronaut };
      /* the Koi's fish */
      const swim = buildAvatarCharSVG('valkyrie').querySelector('.cx-fx-koiswim');
      out.koiFish = swim ? swim.querySelectorAll(':scope > g').length : 0;
      /* the Alien's eyes */
      const al = buildAvatarCharSVG('alien');
      out.alienRot = [...al.querySelectorAll('.cx-eyes ellipse')].map(e => Math.abs(parseFloat(((e.getAttribute('transform') || '').match(/rotate\\(([-\\d.]+)/) || [0, 0])[1])));
      /* Void's flare rim */
      out.voidRimAny = [...buildAvatarCharSVG('voidwalker').querySelectorAll('path')].some(p => p.getAttribute('fill') === 'none' && /^#[0-9A-F]{6}$/i.test(p.getAttribute('stroke') || ''));
      /* an enlarged character's scene is not enlarged with it */
      const vw = buildAvatarCharSVG('voidwalker');
      out.voidBgUnscaled = !!vw.querySelector(':scope > .cx-bg') && !vw.querySelector('g[transform] .cx-bg');
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("every character (%s) stands in a scene of its own" % r.get("n"), not r.get("noScene") and r.get("n", 0) >= 20, r.get("noScene"))
    check("the scene sits behind the figure, faded by a mask, with no SVG filter anywhere", not r.get("badScene"), r.get("badScene"))
    check("two characters' scenes are not the same picture", r.get("sameScene") is False, r.get("sameScene"))
    check("the scene only moves when the character is live",
          r.get("stillFall") == "none" and r.get("liveFall") not in (None, "", "none"), (r.get("stillFall"), r.get("liveFall")))
    s = r.get("sing") or {}
    check("the Singularity is not a cat: a figure with its rising hair, a flare on its head, eyes",
          s.get("cat") is False and s.get("disk") and s.get("star") and s.get("eyes", 0) >= 2, s)
    p, a = r.get("pos") or {}, r.get("ast") or {}
    # REVISED IN 272: the Kitsune and the Cyborg each lasted one build;
    # check_b272 holds what replaced them. Here only that the old drawings
    # are gone and the ids are renamed.
    check("Poseidon's id is no longer the Kraken, and is not named for it",
          p.get("kind") not in ("kraken", "") and p.get("name") not in ("Kraken", "", None), p)
    # REVISED IN 279: every replacement since 271 was turned down, the last
    # with "please hurry so I can get this live" - the id draws the live
    # Astronaut again until one is picked. What still holds: it draws something.
    check("the astronaut id draws a real character and is named for it",
          a.get("kind") not in ("", None) and a.get("name") not in ("", None), a)
    # REVISED IN 272: "Not a fan of the bowl head one having two large fish
    # like that" - check_b272 holds the three small ones. Here: more than one.
    check("the Koi has more than one fish in its bowl", (r.get("koiFish") or 0) >= 2, r.get("koiFish"))
    check("the Alien's eyes slant hard (20 degrees or more)", len(r.get("alienRot") or []) == 2 and min(r.get("alienRot")) >= 20, r.get("alienRot"))
    # REVISED IN 275: the orange rim came off with the return to build 215's Void.
    check("Void keeps a rim of light down one side", r.get("voidRimAny") is True, r.get("voidRimAny"))
    check("an enlarged character's scene stays at its own size", r.get("voidBgUnscaled") is True, r.get("voidBgUnscaled"))
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b272(br):
    """Build 272. (1) THE STARTERS' HEADS ARE THE SET'S SIZE - "I've said
    this 20 times": measured on screen, every starter's head is no wider
    than 23 units of the 34-unit frame and no more than 12% over the
    median of the earned characters' heads. (2) Poseidon's id is the
    Vampire and the astronaut id the Plague Doctor, each named for it.
    (3) The Singularity is its own shape, not a third hood: one eye.
    (4) The Koi's bowl has three small fish, not two big ones. (5) The
    Marksman's ghillie is strips - dozens of them - with a painted face
    and the rifle across it. Written against 271, where none of it held."""
    print("\n53. build 272: starter head size; Vampire, Plague Doctor, the one-eyed Singularity, three koi, the ghillie")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px'; document.body.appendChild(host);
      const headW = id => { host.replaceChildren(); const sv = buildAvatarCharSVG(id); sv.style.cssText = 'width:340px;height:340px;display:block'; host.appendChild(sv);
        const h = sv.querySelector('.cx-head'); return h ? +(h.getBoundingClientRect().width / 10).toFixed(1) : 99; };
      const starters = ['ninja', 'ghost', 'wizard', 'grizzly', 'alien'];
      out.starters = Object.fromEntries(starters.map(id => [id, headW(id)]));
      const earned = ['zeus', 'hacker', 'umbra', 'lunar', 'solar', 'tempest', 'frost', 'oracle', 'timekeeper', 'singularity'].map(headW).sort((a, b) => a - b);
      out.median = earned[Math.floor(earned.length / 2)];
      host.remove();
      const kind = id => (buildAvatarCharSVG(id).querySelector('.cx-fig').getAttribute('class') || '').replace('cx-fig cx-k-', '');
      const vp = buildAvatarCharSVG('poseidon'), pd = buildAvatarCharSVG('astronaut');
      out.vamp = { kind: kind('poseidon'), name: AVATAR_DISPLAY_NAME.poseidon,
        fangs: [...vp.querySelectorAll('.cx-mouth path')].filter(p => (p.getAttribute('fill') || '').toUpperCase() === '#FFFFFF').length };
      out.plague = { kind: kind('astronaut'), name: AVATAR_DISPLAY_NAME.astronaut,
        lenses: [...pd.querySelectorAll('.cx-eyes circle')].filter(c => /url\\(#/.test(c.getAttribute('fill') || '')).length };
      const sg = buildAvatarCharSVG('singularity'), um = buildAvatarCharSVG('umbra');
      out.sing = { pupils: [...sg.querySelectorAll('.cx-eyes circle')].filter(c => c.getAttribute('fill') === '#000000').length,
        shards: sg.querySelectorAll('.cx-fx-sgstar path').length, umbraEyes: um.querySelectorAll('.cx-eyes path').length };
      const swim = buildAvatarCharSVG('valkyrie').querySelector('.cx-fx-koiswim');
      out.koi = swim ? [...swim.querySelectorAll(':scope > g')].map(g => +(((g.getAttribute('transform') || '').match(/scale\\(([\\d.]+)\\)/) || [0, 1])[1])) : [];
      const mk = buildAvatarCharSVG('marksman');
      out.mark = { strips: mk.querySelectorAll('.cx-head path').length, paint: !!mk.querySelector('.cx-head g[clip-path]'), rifle: !!mk.querySelector('.cx-fx-mkrifle') };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    st, med = r.get("starters") or {}, r.get("median") or 0
    check("every starter's head is the set's size (<= 23 units, <= 12%% over the earned median of %s)" % med,
          st and all(w <= 23 and w <= med * 1.12 for w in st.values()), st)
    v, p = r.get("vamp") or {}, r.get("plague") or {}
    # REVISED IN 273: "I don't like Dracula, the big nose thing, or
    # singularity. Change them." check_b273 holds what replaced them; here
    # only that the Kitsune and the Cyborg have not come back.
    check("Poseidon's id is not the Kitsune", v.get("kind") not in ("kitsune", "kraken", ""), v)
    check("the astronaut id is not the Cyborg", p.get("kind") not in ("cyborg", ""), p)
    k = r.get("koi") or []
    check("the Koi's bowl has three small fish, not two big ones", len(k) == 3 and all(x <= .7 for x in k), k)
    m = r.get("mark") or {}
    check("the Marksman's ghillie is dozens of strips, with a painted face and the rifle across it",
          m.get("strips", 0) >= 40 and m.get("paint") and m.get("rifle"), m)
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b273(br):
    """Build 273: "I don't like Dracula, the big nose thing, or
    singularity. Change them. Unique." (1) Poseidon's id is the Sheriff:
    the hat, the bandana, the star. (2) The astronaut id is the Viking:
    horns, helmet, beard. Both named for it. (3) The Singularity has no
    hood and no single eye: hair streaming up, a mask, one line of light
    for eyes, and a flare on the brow. (4) None of the rejected drawings
    (Kraken, Kitsune, Vampire, Cyborg, Plague Doctor, the cat) can be
    reached by any id. Written against 272, where none of it held."""
    print("\n54. build 273: the Sheriff, the Viking, the Singularity's rising hair")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const kind = id => (buildAvatarCharSVG(id).querySelector('.cx-fig').getAttribute('class') || '').replace('cx-fig cx-k-', '');
      const sh = buildAvatarCharSVG('poseidon'), vk = buildAvatarCharSVG('astronaut'), sg = buildAvatarCharSVG('singularity');
      out.sheriff = { kind: kind('poseidon'), name: AVATAR_DISPLAY_NAME.poseidon, star: !!sh.querySelector('.cx-fx-shstar') };
      out.viking = { kind: kind('astronaut'), name: AVATAR_DISPLAY_NAME.astronaut, horns: sh && vk.querySelectorAll('.cx-fx-vkhorns path').length };
      out.sing = { hair: sg.querySelectorAll('.cx-fx-sghair path').length, visor: !!sg.querySelector('.cx-fx-sgvisor'),
        flare: !!sg.querySelector('.cx-fx-sgstar'), pupils: [...sg.querySelectorAll('.cx-eyes circle')].filter(c => c.getAttribute('fill') === '#000000').length };
      const gone = ['kraken', 'kitsune', 'vampire', 'cyborg', 'plaguedoc'];
      out.reachable = AVATAR_CHARACTERS.map(c => kind(c.id)).filter(k => gone.indexOf(k) >= 0);
      out.cat = !!sg.querySelector('[class*="cx-fx-cat"]');
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    a, b, s = r.get("sheriff") or {}, r.get("viking") or {}, r.get("sing") or {}
    check("Poseidon's id is the Sheriff, star on the chest, and is named for it",
          a.get("kind") == "sheriff" and a.get("star") and a.get("name") == "Sheriff", a)
    # REVISED IN 274: "The Viking is a pass, try something else" -
    # check_b274 holds the Bounty Hunter. Here: the Plague Doctor is gone.
    check("the astronaut id is no longer the Plague Doctor", b.get("kind") not in ("plaguedoc", ""), b)
    check("the Singularity: hair streaming up, a line of light for eyes, a flare on the brow - no single black eye",
          s.get("hair", 0) >= 5 and s.get("visor") and s.get("flare") and s.get("pupils") == 0, s)
    check("no id can reach a rejected drawing, and there is no cat", r.get("reachable") == [] and r.get("cat") is False, r.get("reachable"))
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b274(br):
    """Build 274: "Sheriff is perfect. Could singularity be better? I
    don't like the white thing behind it ... The Viking is a pass, try
    something else." (1) The astronaut id is the Bounty Hunter: a helmet
    with a T-shaped visor and a rangefinder, named for it. (2) The
    Singularity has no ring behind it any more - its scene is a nebula
    with motes rising - and its hair is long locks, two layers of them,
    not a crown of spikes. (3) The Sheriff is untouched. Written against
    273, where none of it held."""
    print("\n55. build 274: the Bounty Hunter; the Singularity without its ring")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const kind = id => (buildAvatarCharSVG(id).querySelector('.cx-fig').getAttribute('class') || '').replace('cx-fig cx-k-', '');
      const bh = buildAvatarCharSVG('astronaut'), sg = buildAvatarCharSVG('singularity');
      out.bounty = { kind: kind('astronaut'), name: AVATAR_DISPLAY_NAME.astronaut, visor: !!bh.querySelector('.cx-fx-bhglow'), finder: !!bh.querySelector('.cx-fx-bhlight') };
      out.sing = { ring: !!sg.querySelector('.cx-bg [class*="disk"], .cx-fx-sgdisk'), rising: !!sg.querySelector('.cx-bg .cx-fx-bgrise'),
                   locks: sg.querySelectorAll('.cx-fx-sghair path').length };
      out.sheriff = { kind: kind('poseidon'), name: AVATAR_DISPLAY_NAME.poseidon };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    b, s = r.get("bounty") or {}, r.get("sing") or {}
    # REVISED IN 277: "I don't like the bounty hunter either" - the Ace
    # took the astronaut id (check_b277). What still holds is that the
    # Viking this replaced stays gone.
    check("the astronaut id is no longer the Viking", b.get("kind") != "viking" and b.get("name") != "Viking", b)
    check("the Singularity has no ring behind it, and motes rising in its scene", s.get("ring") is False and s.get("rising") is True, s)
    check("and its hair is two layers of long locks (10 or more), not a crown of spikes", s.get("locks", 0) >= 10, s)
    check("the Sheriff is untouched", r.get("sheriff") == {"kind": "sheriff", "name": "Sheriff"}, r.get("sheriff"))
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b275(br):
    """Build 275. (1) The Hacker's code rain fades into a circle like
    every other scene: it sits under the backdrop's radial mask, and
    there is no rectangular clip on it. (2) Void is build 215's drawing
    again - the slim bust (its top edge at y=29 and 28.2 wide), drawn at
    1:1 (no AVATAR_ART_SCALE), no orange rim, no nebula in its face or
    its scene, its halo open. (3) The Marksman's face tapers to the chin
    and has the hood's shadow across the brow. Written against 274,
    where none of it held."""
    print("\n56. build 275: the Hacker's round scene, Void restored, the Marksman refined")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const hk = buildAvatarCharSVG('hacker'), rain = hk.querySelector('.cx-fx-hk3rain');
      const holder = rain && rain.parentNode;
      out.hacker = { masked: !!(holder && /url\\(#/.test(holder.getAttribute('mask') || '')), clipped: !!(holder && holder.getAttribute('clip-path')) };
      const v = buildAvatarCharSVG('voidwalker');
      const body = v.querySelector('.cx-body path');
      const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px'; document.body.appendChild(host);
      v.style.cssText = 'width:340px;height:340px;display:block'; host.appendChild(v);
      const b = body.getBoundingClientRect();
      out.void = { bodyD: body.getAttribute('d'), scaled: typeof AVATAR_ART_SCALE.voidwalker === 'number',
        top: +(b.top / 10 + 3).toFixed(1),
        orange: [...v.querySelectorAll('path')].some(p => (p.getAttribute('stroke') || '').toUpperCase() === '#F97316'),
        nebula: !!v.querySelector('[fill*="-vneb"], .cx-bg [class*="bgneb"]'),
        halo: !!v.querySelector('circle[fill^="url(#halo-"]') };
      host.remove();
      const mk = buildAvatarCharSVG('marksman');
      out.mark = { shadow: !!mk.querySelector('rect[fill*="-mks"]'), taper: [...mk.querySelectorAll('.cx-head path')].some(p => /28\\.2 20 28\\.4/.test(p.getAttribute('d') || '')) };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    h, v, m = r.get("hacker") or {}, r.get("void") or {}, r.get("mark") or {}
    check("the Hacker's rain fades into a circle like every scene, with no rectangular clip", h.get("masked") and not h.get("clipped"), h)
    # REVISED IN 278: "voids problem is that the head doesn't connect to
    # the body" - the shoulders now rise to meet the hood, so 215's exact
    # bust path is gone on purpose (check_b278 holds the join). What still
    # holds from 275: drawn at 1:1, no art scale.
    check("Void is drawn at 1:1, with no art scale", v.get("scaled") is False, v)
    check("with its halo open, and no orange rim or nebula on it", v.get("halo") and not v.get("orange") and not v.get("nebula"), v)
    check("the Marksman's face tapers to the chin, with the hood's shadow on the brow", m.get("shadow") and m.get("taper"), m)
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b276(br):
    """Build 276. The fifth flare (Event Horizon, the one that hands over
    the Singularity) is the Singularity's own colour: it is the colour
    the Singularity is drawn in and the colour its selected glow uses, it
    is a real blue rather than a near-white, and it stays well apart in
    hue from the fourth (Umbra's violet). On Home, a found fifth dot
    paints in it. Asserted against the character rather than a hex, so a
    later redraw of the Singularity moves the gate with it. Written
    against 275, where the flare was #E6F7FF and matched nothing."""
    print("\n57. build 276: the fifth flare is the Singularity's colour")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const hsl = hex => { const n = parseInt(hex.slice(1), 16), R = (n>>16&255)/255, G = (n>>8&255)/255, B = (n&255)/255;
        const mx = Math.max(R,G,B), mn = Math.min(R,G,B), d = mx - mn, l = (mx+mn)/2;
        let h = 0; if(d){ h = mx===R ? ((G-B)/d)%6 : mx===G ? (B-R)/d+2 : (R-G)/d+4; h = (h*60+360)%360; }
        const sat = d ? d/(1-Math.abs(2*l-1)) : 0; return { h, s: sat, l }; };
      const fifth = MYSTERY_COLOR[MYSTERY_ORDER[4]], fourth = MYSTERY_COLOR[MYSTERY_ORDER[3]];
      const sg = buildAvatarCharSVG(FLARE_CHARACTER[MYSTERY_ORDER[4]]);
      const used = new Set([...sg.querySelectorAll('[fill],[stroke],stop')].flatMap(e => [e.getAttribute('fill'), e.getAttribute('stroke'), e.getAttribute('stop-color')])
        .filter(c => c && c[0] === '#').map(c => c.toUpperCase()));
      const a = hsl(fifth), b = hsl(fourth); let dh = Math.abs(a.h - b.h); if(dh > 180) dh = 360 - dh;
      out.flare = { fifth, fourth, inDrawing: used.has(fifth.toUpperCase()), glow: AVATAR_GLOW[FLARE_CHARACTER[MYSTERY_ORDER[4]]],
        hue: Math.round(a.h), sat: +a.s.toFixed(2), light: +a.l.toFixed(2), apart: Math.round(dh) };
      store.mysteryColorsFound = {}; MYSTERY_ORDER.forEach(k => store.mysteryColorsFound[k] = true);
      showHome(); await new Promise(res => setTimeout(res, 400));
      const dots = [...document.querySelectorAll('.cosmic-orbit-dot')];
      out.dot = { n: dots.length, fills: dots.map(x => (x.getAttribute('fill') || '').toUpperCase()) };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    f, d = r.get("flare") or {}, r.get("dot") or {}
    check("the fifth flare is a colour the Singularity is drawn in, and its glow", f.get("inDrawing") and f.get("glow") == f.get("fifth"), f)
    check("it is a real blue, not a near-white", 180 <= (f.get("hue") or 0) <= 230 and (f.get("sat") or 0) >= .6 and (f.get("light") or 1) <= .85, f)
    check("and stays well apart from the fourth flare's violet", (f.get("apart") or 0) >= 40, f)
    check("a found fifth dot on Home paints in it", d.get("n") == 5 and (f.get("fifth") or "?").upper() in (d.get("fills") or []), d)
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b277(br):
    """Build 277. "I don't like the bounty hunter either, change bounty
    hunter to something else. and void just doesn't look good.. make void
    better, I really like the face with the 3 flares, and the black ...
    Can you incorporate the 4th flare in umbra and the 5th in
    singularity? Singularity character doesn't look like singularity
    anymore, change the name. Maybe horizon like you named the flare."
    (1) The astronaut id is the Ace - goggles holding the sky, a scarf
    that streams - and named for it; no Bounty Hunter anywhere. (2) Void
    keeps its black and its three flares (in the flares' own colours)
    but its face is now a window distinct from the hood, with the three
    joined by a line. (3) Umbra wears the fourth flare's colour and the
    Singularity id the fifth's, each as a real flare (a disc with a
    white core), not just a tint. (4) That id is called Horizon, and no
    character is called Singularity. Written against 276."""
    print("\n58. build 277: the Ace; a better Void; the flares worn; Horizon")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const kind = id => (buildAvatarCharSVG(id).querySelector('.cx-fig').getAttribute('class') || '').replace('cx-fig cx-k-', '');
      const ace = buildAvatarCharSVG('astronaut');
      out.ace = { kind: kind('astronaut'), name: AVATAR_DISPLAY_NAME.astronaut,
        goggles: !!ace.querySelector('[fill*="-acesky"]'), scarf: !!ace.querySelector('.cx-fx-acescarf path'),
        bounty: Object.values(AVATAR_DISPLAY_NAME).includes('Bounty Hunter') };
      const v = buildAvatarCharSVG('voidwalker');
      const fills = el => [...el.querySelectorAll('[fill]')].map(e => (e.getAttribute('fill') || '').toUpperCase());
      const vf = fills(v.querySelector('.cx-fx-flares'));
      out.void = { flares: VOID_FLARES.every(k => vf.includes(MYSTERY_COLOR[k].toUpperCase())),
        window: !!v.querySelector('.cx-head [fill^="url(#vface-"]'), line: !!v.querySelector('.cx-fx-flares path[stroke-dasharray]'),
        orbs: v.querySelectorAll('.cx-fx-flares circle[fill="#FFF"], .cx-fx-flares circle[fill="#FFFFFF"]').length };
      const worn = (id, key) => { const svg = buildAvatarCharSVG(id), col = MYSTERY_COLOR[key].toUpperCase();
        const discs = [...svg.querySelectorAll('.cx-fig circle')].filter(c => (c.getAttribute('fill') || '').toUpperCase() === col);
        return discs.some(d => [...d.parentNode.querySelectorAll('circle')].some(c => /^#FFF(FFF)?$/i.test(c.getAttribute('fill') || ''))); };
      out.worn = { umbra: worn('umbra', MYSTERY_ORDER[3]), fifth: worn(FLARE_CHARACTER[MYSTERY_ORDER[4]], MYSTERY_ORDER[4]) };
      out.names = { fifth: AVATAR_DISPLAY_NAME[FLARE_CHARACTER[MYSTERY_ORDER[4]]], flare: MYSTERY_NAME[MYSTERY_ORDER[4]],
        anySing: Object.values(AVATAR_DISPLAY_NAME).includes('Singularity') };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    a, v, w, n = r.get("ace") or {}, r.get("void") or {}, r.get("worn") or {}, r.get("names") or {}
    # REVISED IN 278: "Nope, not ace" - the Phantom took the astronaut id
    # (check_b278). What still holds: no Bounty Hunter anywhere.
    check("the Bounty Hunter stays gone", a.get("kind") != "bounty" and not a.get("bounty"), a)
    check("Void keeps its three flares in the flares' own colours", v.get("flares") and v.get("orbs") == 3, v)
    check("and its face is a window of its own, the three joined by a line", v.get("window") and v.get("line"), v)
    check("Umbra wears the fourth flare, the fifth flare's character wears the fifth", w.get("umbra") and w.get("fifth"), w)
    check("the fifth flare's character is named for the flare, and nobody is called Singularity",
          bool(n.get("fifth")) and n.get("fifth") in (n.get("flare") or "") and not n.get("anySing"), n)
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b279_merge(br):
    """Build 279. "Delete the two lower level accounts, and make it so
    those two lower accounts, next time he uses them, his higher level
    account will be used instead ... take his progress from the lower
    level accounts and apply it to the main account ... Give lake an
    extra level as well." and "If anyone unlocks anything because of
    this, do it after their next test." A merge note moves the device AND
    folds its progress into the account it joins, plus a bonus level;
    what that unlocks waits for the next finished test. Written against
    build 278, where the device takes the target whole and every number
    here is the target's alone."""
    print("\n52. build 279: a duplicate account merged into the real one")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const U = 'Identity Crimes';
      const key0 = Object.keys(store.stats || {})[0];
      /* the account being joined: its own name and id, 10 of 15 hundos */
      const main = Object.assign(JSON.parse(JSON.stringify(store)), {
        firstName: 'Main', publicId: 'pubmain00001', lastModified: 5, mergeHold: null,
        unitPerfects: { [U]: 10 }, testHistory: [{ label: 'old', playedAt: 1000, pct: 50, units: [U], mode: 'drill' }],
        studyLog: { '2026-09-30': 60000 }, vrWins: 2 });
      main.lifetime = Object.assign({}, main.lifetime, { points: xpForLevel(20) + 100, correct: 900, answered: 1000 });
      main.stats = { [key0]: { n: 4, m: 1, r: [10] } };
      /* this device, the duplicate: 6 more hundos, its own history */
      store.firstName = 'Dup'; store.publicId = 'pubdup000002';
      store.unitPerfects = { [U]: 6 };
      store.lifetime = Object.assign({}, store.lifetime, { points: 2000, correct: 170, answered: 190 });
      store.stats = { [key0]: { n: 3, m: 2, r: [20, 30] } };
      store.testHistory = [{ label: 'new', playedAt: 2000, pct: 100, units: [U], mode: 'drill' }];
      store.studyLog = { '2026-09-30': 30000, '2026-10-01': 45000 };
      store.vrWins = 1;
      const docs = {
        'ABCD-EFGH__merge': { to: 'JKLM-NPQR', at: 1, bonusLevels: 1,
                              extra: { points: 500, correct: 40, week: weekKeyNow(), weekPoints: 100 } },
        'JKLM-NPQR': main };
      const writes = [];
      const ref = id => ({ id,
        get(){ return Promise.resolve({ exists: !!docs[id], data: () => docs[id], ref: ref(id) }); },
        set(d, o){ writes.push(id); docs[id] = Object.assign({}, (o && o.merge) ? docs[id] : {}, d); return Promise.resolve(); },
        update(){ return Promise.resolve(); }, delete(){ return Promise.resolve(); },
        onSnapshot(){ return () => {}; } });
      fbDb = { collection: () => ({ doc: ref, onSnapshot(){ return () => {}; },
               get(){ return Promise.resolve({ forEach(){}, size: 0, metadata: {} }); } }) };
      const realRetire = retireLeaderboardEntry; const retired = [];
      retireLeaderboardEntry = pub => { retired.push(pub); };
      syncCode = 'ABCD-EFGH'; accountMoveChecked = '';
      checkAccountMove('ABCD-EFGH'); await wait(600);
      retireLeaderboardEntry = realRetire;
      const base = xpForLevel(20) + 100 + 2000 + 500;
      out.code = syncCode; out.name = store.firstName; out.pub = store.publicId; out.retired = retired;
      out.level = levelOf(store); out.levelNoBonus = levelFromPoints(base);
      out.correct = store.lifetime.correct; out.hundos = store.unitPerfects[U];
      out.stat = store.stats[key0]; out.hist = store.testHistory.map(h => h.label);
      out.day = store.studyLog['2026-09-30']; out.vrWins = store.vrWins;
      out.held = !!store.mergeHold; out.homeQuiet = pendingHomeUnlocks().chars.length + pendingHomeUnlocks().banners.length;
      out.badgeNow = unitBadgeEarned(U);
      out.done = !!(docs['ABCD-EFGH__merge'] || {}).done;
      await wait(1500); out.pushed = writes.indexOf('JKLM-NPQR') >= 0;
      /* the next finished test, any test at all, plays what the merge brought */
      const idx = t => QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
      const xp0 = store.lifetime.points;
      cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = ['Victims of Crime'];
      order = idx('Victims of Crime').slice(0, 5);
      runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
      attempts = {}; picked = {}; timedOutSet = {};
      order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
      summarize(); await wait(400);
      out.celebrated = [...document.querySelectorAll('#stage .rs-unlock-badge .unlockbanner-name')].map(e => e.textContent);
      out.runXp = store.lifetime.points - xp0;
      out.heldAfter = !!store.mergeHold;
      } catch(e){ out.threw = String(e); }
      return out; }""")
    check("the duplicate's device lands on the real account, name and id",
          r.get("code") == "JKLM-NPQR" and r.get("name") == "Main" and r.get("pub") == "pubmain00001"
          and (r.get("retired") or [None])[0] == "pubdup000002" and r.get("done") is True, r)
    check("its XP, right answers and hundos are added to the real account's",
          r.get("correct") == 900 + 170 + 40 and r.get("hundos") == 16, r)
    check("so are its question stats, history and study time",
          (r.get("stat") or {}).get("n") == 7 and (r.get("stat") or {}).get("m") == 3
          and r.get("hist") == ["new", "old"] and r.get("day") == 90000 and r.get("vrWins") == 3, r)
    check("and the gift is one whole level on top of the merged total",
          r.get("level") == (r.get("levelNoBonus") or 0) + 1, [r.get("level"), r.get("levelNoBonus")])
    check("the merged account goes straight to the cloud", r.get("pushed") is True, r)
    check("what it unlocks waits: nothing announces on Home in the meantime",
          r.get("held") is True and r.get("homeQuiet") == 0 and r.get("badgeNow") is True, r)
    check("and the next test of any sort plays it, the merged badge included",
          any("Identity Crimes" in (n or "") for n in (r.get("celebrated") or [])) and r.get("heldAfter") is False, r)
    check("with no mastery bonus for a badge the merge earned", 0 < (r.get("runXp") or 0) < 1000, r.get("runXp"))
    # THE MERGE NOTE HAS ITS OWN NAME. An old build follows any `__moved`
    # note by taking the target whole; a merge parked there would throw
    # the duplicate's progress away on a phone that had not updated.
    import re as _re
    src = open(SRC, encoding="utf-8").read()
    check("a merge note is never a `__moved` note, which old builds would follow without merging",
          '"__merge"' in src and not _re.search(r"merge:\s*true[^;]*__moved", src), "__merge" in src)
    ctx.close()


def check_b278(br):
    """Build 278. "Nope, not ace, something cooler, something mysterious
    and unique. I feel like voids problem is that the head doesn't
    connect to the body? ... I like the flares of horizon and umbra,
    ensure they look like that on void." (1) The astronaut id is the
    Phantom - a top hat, a mask with a monocle, a calling card - named
    for it, and nobody is called Ace. (2) Void's hood and body are one
    figure: they share one ramp laid in user space (so there is no band
    where one box's darkest meets the other's lightest), and the hood's
    bottom runs past the top of the shoulders. (3) Void's three flares
    are drawn exactly as Umbra's and Horizon's are - the same parts in
    the same order, a rimmed disc and a white core - in the three hunt
    colours. Written against 277, where none of it held."""
    print("\n59. build 278: the Phantom; Void joined to its body; one flare drawing for all three")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try {
      const kind = id => (buildAvatarCharSVG(id).querySelector('.cx-fig').getAttribute('class') || '').replace('cx-fig cx-k-', '');
      const ph = buildAvatarCharSVG('astronaut');
      out.ph = { kind: kind('astronaut'), name: AVATAR_DISPLAY_NAME.astronaut, card: !!ph.querySelector('.cx-fx-phcard rect'),
        monocle: !!ph.querySelector('.cx-fx-phsheen'), ace: Object.values(AVATAR_DISPLAY_NAME).includes('Ace') };
      const v = buildAvatarCharSVG('voidwalker'); document.body.appendChild(v);
      const body = v.querySelector('.cx-body path'), hood = v.querySelector('.cx-head path');
      const gradOf = el => { const m = /url\(#([^)]+)\)/.exec(el.getAttribute('fill') || ''); return m && v.querySelector('#' + CSS.escape(m[1])); };
      const g = gradOf(body);
      out.join = { same: body.getAttribute('fill') === hood.getAttribute('fill'), user: !!g && g.getAttribute('gradientUnits') === 'userSpaceOnUse',
        overlap: +(hood.getBBox().y + hood.getBBox().height - body.getBBox().y).toFixed(2) };
      v.remove();
      /* the shape of one worn flare: the circles its group draws, as (has stroke, is white) */
      const sig = (svg, col) => { const disc = [...svg.querySelectorAll('.cx-fig circle')].find(c => (c.getAttribute('fill') || '').toUpperCase() === col.toUpperCase());
        if(!disc) return null; const cs = [...disc.parentNode.children].filter(e => e.tagName === 'circle');
        const i = cs.indexOf(disc); return [cs[i - 1], cs[i], cs[i + 1]].map(c => c ? [/^url/.test(c.getAttribute('fill') || ''), !!c.getAttribute('stroke'), /^#FFF(FFF)?$/i.test(c.getAttribute('fill') || '')].join('') : 'none').join('|'); };
      out.sig = { umbra: sig(buildAvatarCharSVG('umbra'), MYSTERY_COLOR[MYSTERY_ORDER[3]]),
        fifth: sig(buildAvatarCharSVG(FLARE_CHARACTER[MYSTERY_ORDER[4]]), MYSTERY_COLOR[MYSTERY_ORDER[4]]),
        void: VOID_FLARES.map(k => sig(buildAvatarCharSVG('voidwalker'), MYSTERY_COLOR[k])) };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    p, j, sg = r.get("ph") or {}, r.get("join") or {}, r.get("sig") or {}
    # REVISED IN 279: the Phantom was turned down ("I don't like the
    # phantom, that one is weird") and so was every round after it, until
    # a hooded space assassin: "Star blade is cool". Still no Ace.
    # The name changed once already ("the name is kinda lame"), so the
    # shape is asserted, not the string: the hooded assassin drawing, and
    # a name that is neither of the two turned down.
    check("the astronaut id is the hooded space assassin, named; no Phantom, no Ace",
          p.get("kind") == "starblade" and p.get("name") not in ("", None, "Phantom", "Ace", "Starblade")
          and not p.get("ace"), p)
    check("Void's hood and body share one ramp laid in user space", j.get("same") and j.get("user"), j)
    check("and the hood runs down past the top of the shoulders", (j.get("overlap") or 0) >= 2, j)
    check("Void's three flares are drawn exactly as Umbra's and Horizon's",
          sg.get("umbra") and sg.get("umbra") == sg.get("fifth") and all(x == sg.get("umbra") for x in (sg.get("void") or [None])), sg)
    check("no exception", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b280_rankmap_still(br):
    """Build 280. "The animation where it moves the screen down for you to
    the progress, only do that when the progression changes (even if it's
    slightly)." Build 279 glided the road map down to your stop and back
    on EVERY opening of the Rank tab. Now: opened with nothing changed,
    the map does not move; opened after the stretch you are on has grown
    by a hair (a thousandth of it), it travels down and runs the climb.
    Written against build 279, where the first half fails (it glances
    every time) and the second fails on the 0.4% threshold."""
    print("\n53. build 280: the Rank tab only travels to your progress when it changed")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      /* held badges put the account part-way along a stretch of road
         (the seed has none, and an unranked account has no stretch) */
      const u = topicsIn(QUESTIONS); u.slice(0, 3).forEach(n => store.unitPerfects[n] = 999);
      store.rankMapFx244 = true; store.rankMapSeen = 99; store.rankMapProg = null;
      const open = async () => { showHome(); await wait(300); window.scrollTo({ top: 0, behavior: 'instant' });
        showProfile('ranks'); let max = 0; for(let i = 0; i < 45; i++){ await wait(100); max = Math.max(max, window.scrollY); } return max; };
      /* first look: no record, so the climb plays and the spot is recorded */
      await open(); await wait(3500);
      out.recorded = store.rankMapProg ? store.rankMapProg.p : null;
      /* unchanged: still */
      out.stillMax = await open();
      out.stillClimb = !!document.querySelector('.rankmap-roadfill[data-progress-to]');
      /* grown by a thousandth of the stretch */
      if(store.rankMapProg) store.rankMapProg.p = Math.max(0, store.rankMapProg.p - 0.001);
      out.grownMax = await open();
      out.grownClimb = !!document.querySelector('.rankmap-roadfill[data-progress-to]');
      }catch(e){ out.threw = String(e); }
      return out; }""")
    check("opened with nothing changed, the Rank tab does not travel",
          r.get("recorded") is not None and 0 < r["recorded"] < 1 and r.get("stillMax", 99) < 2 and not r.get("stillClimb"), r)
    check("opened after the climb grew by a thousandth, it travels to it and runs the climb",
          r.get("grownClimb") is True and r.get("grownMax", 0) > 40, r)
    ctx.close()


def check_b281_badge_card(br):
    """Build 281. "The pop ups when clicking the badges ... they stay there
    till I click off the tab ... make it similar to the character unlock
    or banner unlock now, you click it, and opens up the progress screen
    similarly with the green bar." A badge tile opens the unlock card -
    kind badge, the badge drawn, the green bar, hundos of what it needs -
    and no info bubble. Written against build 280, where the tap raised
    showContextualInfo's bubble and no card."""
    print("\n54. build 281: a badge opens the unlock card")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const u = topicsIn(QUESTIONS)[0]; store.unitPerfects[u] = 1;
      showProfile('badges'); await wait(1200);
      const tile = [...document.querySelectorAll('.badge-tile')].find(t => t.querySelector('.badge-tile-name').textContent === u);
      tile.click(); await wait(1400);
      const c = document.querySelector('.unlock-card');
      out.card = !!c; out.kind = c ? c.className : '';
      out.art = !!(c && c.querySelector('.unlock-card-art svg'));
      out.fill = c ? getComputedStyle(c.querySelector('.unlock-card-fill')).backgroundImage : '';
      out.count = c ? (c.querySelector('.unlock-card-count') || {}).textContent || '' : '';
      out.need = String(badgeThresholdFor(u));
      out.bubble = !!document.getElementById('contextual-info-popup');
      }catch(e){ out.threw = String(e); }
      return out; }""")
    check("a badge opens the unlock card, not the info bubble",
          r.get("card") is True and "unlock-card-badge" in r.get("kind", "") and r.get("art") is True and r.get("bubble") is False, r)
    check("the card's bar is the green one and counts hundos of what the badge needs",
          "47, 191, 113" in r.get("fill", "") and r.get("count", "").endswith(" of " + r.get("need", "?")), r)
    ctx.close()


def check_b282(br):
    """Build 282. "The rank box where it says what rank you are in the rank
    tab. Those boxes that show your level and badge count is really really
    nice. I want the badge tab at the top to use that same circle idea and
    color ... slightly bigger ... on your profile tab, in the top box, make
    those circles the same, not the glowy ones. Those ones don't need the
    progress circles though ... ensure the bottom tab lag is fixed ...
    Ensure the result screen stuff and animations are lag free."
    Held as SHAPE: the rings are the Rank tab's (its own --ring colours,
    read off the Rank tab rather than typed here), the Badges tab's is
    bigger and carries an arc, the Profile's carry none and nothing on
    them moves; the bar's bubble has no blur of its own and its sheen, the
    XP pump and every results-card landing move only transform and
    opacity; a results card has no backdrop blur; and toTop() at the top
    of the page asks nothing of layout. Written against build 281."""
    print("\n55. build 282: the Rank tab's rings elsewhere, and nothing that repaints per frame")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try{
      const ringOf = el => el ? getComputedStyle(el).getPropertyValue('--ring').trim() : null;
      showRanksScreen('ranks'); await wait(1400);
      const rg = document.querySelector('.rankhero-gauge:not(.is-badges)'), rb = document.querySelector('.rankhero-gauge.is-badges');
      out.rankLevelRing = ringOf(rg); out.rankBadgeRing = ringOf(rb);
      const rf = document.querySelector('.rankhero .rankhero-ringface');
      out.rankFaceW = rf ? Math.round(rf.getBoundingClientRect().width) : 0;
      /* three badges held, so the arc has somewhere real to stand */
      topicsIn(QUESTIONS).slice(0, 3).forEach(u => store.unitPerfects[u] = 999);
      showProfile('badges'); await wait(1600);
      const hb = document.querySelector('.badges-head .rankhero-gauge.is-badges');
      const hf = hb && hb.querySelector('.rankhero-ringface');
      const arc = hf && hf.querySelector('.rankhero-ringarc');
      out.headRing = ringOf(hb); out.headFaceW = hf ? Math.round(hf.getBoundingClientRect().width) : 0;
      out.headArc = arc ? parseFloat(getComputedStyle(arc).strokeDashoffset) : null;
      out.headWant = Math.round((1 - badgesEarnedList().length / topicsIn(QUESTIONS).length) * 1000) / 10;
      out.headMedal = document.querySelectorAll('.badges-head .badges-medal').length;
      showProfile(); await wait(1600);
      const lv = document.querySelector('.profile-level.rankhero-gauge'), bd = document.querySelector('.profile-badgesect.rankhero-gauge');
      out.profLevelRing = ringOf(lv); out.profBadgeRing = ringOf(bd);
      const rings = [...document.querySelectorAll('.profile-level .rankhero-ringface, .profile-badgesect .rankhero-ringface')];
      out.profRings = rings.length;
      out.profArcs = rings.reduce((n, f) => n + f.querySelectorAll('.rankhero-ringarc').length, 0);
      out.profRingAnims = rings.reduce((n, f) => n + f.getAnimations({ subtree:true }).length, 0)
        + (document.querySelector('.profile-level-num') ? document.querySelector('.profile-level-num').getAnimations().length : 0);
      /* every HTML-element animation running on Profile: transform/opacity only */
      const paintProps = [];
      document.getAnimations().forEach(a => { const t = a.effect && a.effect.target; if(!t || a.playState !== 'running') return;
        if(t instanceof SVGElement) return;
        a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => {
          if(['offset','easing','composite','computedOffset','transform','opacity','translate','rotate','scale'].includes(p)) return;
          paintProps.push((a.animationName || a.transitionProperty || '?') + ':' + p); })); });
      out.profPaint = [...new Set(paintProps)];
      /* the keyframes behind the bar's sheen, the XP pump and the results reveal */
      const kf = {};
      const walk = rules => { for(const rule of rules){
        if(rule.type === CSSRule.KEYFRAMES_RULE){ const props = new Set();
          for(const k of rule.cssRules) for(let i = 0; i < k.style.length; i++) props.add(k.style[i]);
          kf[rule.name] = [...props]; }
        else if(rule.cssRules) walk(rule.cssRules); } };
      for(const sh of document.styleSheets){ try{ walk(sh.cssRules); }catch(e){} }
      out.kf = {};
      ['glass-sheen','xp-pump','rs-bang','rs-slam','rs-impact','rs-charge','rs-trackpop'].forEach(n => out.kf[n] = kf[n] || null);
      const slider = document.getElementById('bottomtabs-slider');
      out.sliderBlur = slider ? getComputedStyle(slider).backdropFilter : 'missing';
      const scr = document.createElement('div'); scr.className = 'rs-screen';
      const card = document.createElement('div'); card.className = 'rs-card'; scr.appendChild(card); document.body.appendChild(scr);
      out.cardBlur = getComputedStyle(card).backdropFilter; scr.remove();
      /* toTop() at the top asks nothing of layout */
      window.scrollTo({ top:0, behavior:'instant' }); await wait(200);
      const real = window.scrollTo; let calls = 0;
      window.scrollTo = function(){ calls++; return real.apply(this, arguments); };
      toTop(); toTop(true);
      out.toTopAtTop = calls;
      window.scrollTo = real;
      }catch(e){ out.threw = String(e); }
      return out; }""")
    check("the Badges tab's ring is the Rank tab's badge ring, bigger, in its box, with no medal",
          r.get("headRing") and r.get("headRing") == r.get("rankBadgeRing") and r.get("headFaceW", 0) > r.get("rankFaceW", 0) > 0
          and r.get("headMedal") == 0, r)
    check("and its arc stands at the share of the badges held",
          r.get("headArc") is not None and abs(r["headArc"] - r["headWant"]) < 1.5, (r.get("headArc"), r.get("headWant")))
    check("the Profile card's two rings take the Rank tab's level and badge colours",
          r.get("profRings") == 2 and r.get("profLevelRing") == r.get("rankLevelRing") and r.get("profBadgeRing") == r.get("rankBadgeRing")
          and r.get("rankLevelRing") != r.get("rankBadgeRing"), r)
    check("with no progress arc and nothing on them moving",
          r.get("profArcs") == 0 and r.get("profRingAnims") == 0, (r.get("profArcs"), r.get("profRingAnims")))
    check("nothing running on Profile repaints per frame (transform and opacity only)",
          r.get("profPaint") == [], r.get("profPaint"))
    kf = r.get("kf") or {}
    cheap = {"transform", "opacity", "translate", "rotate", "scale"}
    check("the bar's sheen, the XP pump and every results landing move transform and opacity only",
          all(kf.get(n) and set(kf[n]) <= cheap for n in kf), kf)
    check("the tab bar's bubble has no blur of its own, and a results card no backdrop blur",
          r.get("sliderBlur") == "none" and r.get("cardBlur") == "none", (r.get("sliderBlur"), r.get("cardBlur")))
    check("toTop() at the top of the page does not scroll, so lays nothing out",
          r.get("toTopAtTop") == 0, r.get("toTopAtTop"))
    ctx.close()


def check_b283(br):
    """Build 283: Game mode and the Practice Test are retired, and their
    rewards move onto Exam. (1) The mode screen offers no Game card and
    an Exam card goes straight to unit selection - no Standard / Practice
    choice. (2) Neither screen's builder is left in the page, and a saved
    Game mode comes back as Drill. (3) [Lanterns, Great Wave and
    Thunderhead moved onto Exam here; build 284 removed them, so that part
    is gone from this gate.] (4) Phoenix is
    a perfect Exam of 100 or more questions, through summarize(), and 99
    is not enough. Written against 282, where every one of these fails."""
    print("\n56. build 283: Game mode and the Practice Test retired, their rewards on Exam")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      const wait = ms => new Promise(r => setTimeout(r, ms));
      try {
      store.seenModeSelectTour = true; showModeSelect(); await wait(400);
      out.kinds = [...document.querySelectorAll('.modeselect .modecard')].map(c => c.dataset.mode);
      const ex = document.querySelector('.modecard[data-mode="exam"]');
      if(ex){ ex.click(); await wait(700); }
      out.examLands = !!document.querySelector('.screen-setup') && cfg.mode === 'exam';
      out.gone = ['showExamOptions', 'showPracticeTestConfirm', 'gameOver', 'recordGameBeatIfEligible']
        .filter(n => typeof window[n] === 'function');
      store.opts = Object.assign({}, store.opts || {}, { mode: 'game' }); applySaved();
      out.savedGame = cfg.mode;
      cfg.mode = 'drill';
      const U = topicsIn(QUESTIONS);
      /* Lanterns, Great Wave and Thunderhead moved onto Exam here in 283
         and were removed outright in 284 (check_b284); Phoenix stays. */
      out.labels = ['exam100'].map(id => bannerDef(id).label);
      // Phoenix: a real perfect Exam through summarize().
      const units = []; let n = 0;
      for(const u of U){ units.push(u); n += unitQuestionCount(u); if(n >= 100) break; }
      const all = [].concat(...units.map(t => QUESTIONS.map((q, i) => [q, i]).filter(([q]) => (q.topic || '').trim() === t).map(([, i]) => i)));
      const run = ord => {
        cfg.mode = 'exam'; cfg.source = 'all'; cfg.units = units.slice();
        order = ord; runTrackable = true; timedOut = false; runMode = 'exam'; runLabel = null; isMissedRetake = false;
        attempts = {}; picked = {}; timedOutSet = {};
        order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
        summarize(); document.querySelectorAll('.rs-spot').forEach(e => e.remove());
        return store.practiceExamPerfect === true; };
      store.practiceExamPerfect = false; store.unitExam = {};
      out.n = all.length;
      out.phoenix99 = run(all.slice(0, 99));
      out.phoenix = run(all);
      out.acedAfter = units.filter(u => (unitExamOf(u) || {}).best === 100).length;
      out.nUnits = units.length;
      } catch(e){ out.threw = String(e && e.stack || e); }
      try{ testInProgress = false; showHome(); }catch(e){}
      return out; }""")
    check("no exception", not r.get("threw"), r.get("threw"))
    kinds = r.get("kinds") or []
    check("the mode screen offers no Game card, and still offers the other four",
          "game" not in kinds and sorted(kinds) == sorted(["drill", "exam", "review", "vroom"]), kinds)
    check("the Exam card goes straight to unit selection, with no Practice Test choice first",
          r.get("examLands") is True, r.get("examLands"))
    check("the Game and Practice Test screens are gone from the page", r.get("gone") == [], r.get("gone"))
    check("a saved Game mode comes back as Drill", r.get("savedGame") == "drill", r.get("savedGame"))
    labs = r.get("labels") or []
    # Build 289: Phoenix is seven units aced in a row; a perfect long Exam
    # no longer sets the old flag (anybody holding it keeps the banner).
    check("Phoenix asks for units aced in a row, not an Exam or the Practice Exam (build 289)",
          len(labs) == 1 and not any(re.search(r"game|practice|exam", l, re.I) for l in labs) and all("in a row" in l for l in labs), labs)
    check("a perfect Exam of 100 or more questions no longer sets the old Phoenix flag",
          r.get("phoenix99") is False and r.get("phoenix") is False and r.get("n", 0) >= 100, r.get("n"))
    check("and it records every unit it covered as an Exam ace",
          r.get("acedAfter") == r.get("nUnits") and r.get("nUnits", 0) > 0, (r.get("acedAfter"), r.get("nUnits")))
    ctx.close()


def check_b284(br):
    """Build 284, Madison's list after 283. (1) Settings has no Smooth
    scrolling or Keep screen awake switch; scrolling is smooth whatever an
    older build saved, and nothing asks for a wake lock. (2) No Progress
    tab: four tabs on the bar, and the Profile card's rank and badge rows
    open the climb and the case, with a way back to Profile. (3) The rank
    box has no "N to go until X" line and the badge box no "Closest" line.
    (4) No answer-streak pop during a test. (5) Lanterns, Great Wave,
    Thunderhead and Hall of Fame are gone, and somebody wearing one is
    back on the default. (6) No Most missed: two banks, one door, no
    reset in Settings, and a saved Most missed bank loads as All. Written
    against 283, where each one fails."""
    print("\n57. build 284: Settings switches, no Progress tab, simpler rank boxes, no streak pop, four banners gone")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT,
                     init="window.__wake = 0; try{ Object.defineProperty(navigator, 'wakeLock', { value: { request: () => { window.__wake++; return Promise.resolve({ release(){} }); } }, configurable: true }); }catch(e){}")
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      try {
      /* 1. Settings */
      store.theme = Object.assign({}, store.theme || {}, { smoothScroll: false, keepAwake: true });
      loadTheme(); applyTheme(); await wait(200);
      out.scroll = document.documentElement.style.scrollBehavior;
      out.wake = window.__wake;
      showAppearance(); await wait(800);
      out.rows = [...document.querySelectorAll('.otext')].map(e => (e.firstChild && e.firstChild.textContent || '').trim());
      /* 2. the bar and the Profile card */
      out.tabs = [...document.querySelectorAll('#bottomtabs .bottomtab:not(.bottomtab-start)')].map(t => t.dataset.dest);
      showProfile(); await wait(900);
      const plate = document.querySelector('.profile-rankplate');
      if(plate) plate.click(); await wait(900);
      out.rankOpens = !!document.querySelector('.screen-ranks') && !!(document.querySelector('.rankstabs .iconbtn.active') || {}).textContent;
      out.profileLit = !!document.querySelector('#bottomtab-profile.active');
      out.noteLine = !!document.querySelector('.rankhero-next');
      const back = document.querySelector('.screen-ranks .back-link');
      if(back) back.click(); await wait(900);
      out.backToProfile = !!document.querySelector('.screen-profile');
      const badgeRow = document.querySelector('.screen-profile .profile-badgesect');
      if(badgeRow) badgeRow.click(); await wait(1200);
      out.badgesOpen = !!document.querySelector('.screen-ranks .badges-tab:not([hidden])');
      out.closest = !!document.querySelector('.badge-next');
      /* 4. a run of right answers in a Drill */
      const U = topicsIn(QUESTIONS)[0];
      cfg.mode = 'drill'; runMode = 'drill'; runLabel = null; isMissedRetake = false;
      let pops = 0; const mo = new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => { if(n.classList && n.classList.contains('streak-pop')) pops++; })));
      mo.observe(document.body, { childList: true, subtree: true });
      theme.muteBanners = false; runLiveStreak = 0;
      for(let i = 0; i < 30; i++) runStreakLive(true);
      await wait(300); mo.disconnect();
      out.pops = pops + document.querySelectorAll('.streak-pop').length;
      runLiveStreak = 0;
      /* 6. no Most missed: the bank, the unit door, the Settings reset, a saved bank */
      showAppearance(); await wait(700);
      out.resetMissed = [...document.querySelectorAll('button')].some(b => /missed-question history/i.test(b.textContent || ''));
      store.opts = Object.assign({}, store.opts || {}, { source: 'recent', mode: 'drill' }); applySaved();
      out.savedBank = cfg.source;
      const unit = topicsIn(QUESTIONS)[0];
      cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(700);
      const box = [...document.querySelectorAll('.pick input')].find(x => x.value === unit);
      if(box){ box.checked = true; box.dispatchEvent(new Event('change', { bubbles: true })); } await wait(200);
      document.getElementById('nextbtn')?.click(); await wait(600);
      out.banks = [...document.querySelectorAll('.bank-opt')].map(r => r.dataset.value);
      document.querySelector('.unitoptions-modal-scrim')?.click(); await wait(400);
      const row = [...document.querySelectorAll('.pick')].find(r => (r.querySelector('input') || {}).value === unit);
      if(row){ row.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 50, clientY: 50, button: 0 }));
        await wait(600); row.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 50, clientY: 50 })); await wait(800); }
      out.doors = [...document.querySelectorAll('.unitdetail-door')].map(d => [...d.classList].find(c => c.startsWith('is-') && c !== 'is-empty'));
      document.querySelectorAll('.unitdetail-scrim, .unitdetail').forEach(e => e.remove());
      /* 5. the banners */
      out.gone = ['easy10', 'average10', 'hardcore10', 'badges16'].filter(id => !!bannerDef(id));
      store.banner = 'badges16'; out.worn = wornBanner();
      store.banner = '';
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("no exception", not r.get("threw"), r.get("threw"))
    rows = r.get("rows") or []
    check("Settings has no Smooth scrolling or Keep screen awake switch",
          len(rows) > 3 and not any(x in ("Smooth scrolling", "Keep screen awake") for x in rows), rows)
    check("scrolling is smooth even where an older build saved it off", r.get("scroll") == "smooth", r.get("scroll"))
    check("nothing asks for a wake lock, even where an older build saved it on", r.get("wake") == 0, r.get("wake"))
    check("four tabs on the bar and none of them Progress",
          r.get("tabs") == ["home", "profile", "rewards", "settings"], r.get("tabs"))
    check("the Profile card's rank row opens the climb, with Profile lit on the bar",
          r.get("rankOpens") is True and r.get("profileLit") is True, (r.get("rankOpens"), r.get("profileLit")))
    check("and its back link goes to Profile", r.get("backToProfile") is True, r.get("backToProfile"))
    check("the badge row opens the badge case", r.get("badgesOpen") is True, r.get("badgesOpen"))
    check("the rank box has no 'N to go until X' line, the badge box no 'Closest' line",
          r.get("noteLine") is False and r.get("closest") is False, (r.get("noteLine"), r.get("closest")))
    check("thirty right answers in a row put up no streak pop during the test", r.get("pops") == 0, r.get("pops"))
    check("Lanterns, Great Wave, Thunderhead and Hall of Fame are gone", r.get("gone") == [], r.get("gone"))
    check("somebody wearing one of them is back on the default banner", r.get("worn") == "", r.get("worn"))
    check("the Question bank is All questions and Flagged - no Most missed", r.get("banks") == ["all", "flagged"], r.get("banks"))
    check("a unit's details have one door, Flagged", r.get("doors") == ["is-flagged"], r.get("doors"))
    check("a saved Most missed bank comes back as every question", r.get("savedBank") == "all", r.get("savedBank"))
    check("Settings has no 'Reset missed-question history'", r.get("resetMissed") is False, r.get("resetMissed"))
    ctx.close()
    # (7) "the amethyst animation spins a little fast ... the supernova
    # animation could be a little cooler, needs to be coolest one."
    # Measured on a live Rank hero emblem: Amethyst's whirl takes longer
    # than 3s a turn, and Supernova goes off - its core, flares, light,
    # cross-flare and blast shell on ONE clock with no offset (a single
    # detonation, not five things breathing), its star turning faster
    # than once a minute.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    m = pg.evaluate("""()=>{ const host = document.createElement('div'); host.className = 'rankhero-art';
      host.style.cssText = 'position:fixed;left:0;top:0;width:200px;height:200px'; document.body.appendChild(host);
      const look = k => { const s = buildRankEmblemSVG(k); host.replaceChildren(s); s.classList.remove('rk-idle');
        return [...s.querySelectorAll('.rk-a')].map(g => { const c = getComputedStyle(g);
          return { cls: g.getAttribute('class'), name: c.animationName, dur: parseFloat(c.animationDuration), delay: parseFloat(c.animationDelay) }; }); };
      const e = look('elite'), t = look('titan');
      const whirl = e.find(a => /rk-spin rk-quick/.test(a.cls));
      const boom = t.filter(a => /^rk-nova-/.test(a.name));
      const star = t.find(a => /rk-turn rk-slow/.test(a.cls));
      return { whirl: whirl && whirl.dur, boom: boom.map(a => [a.name, a.dur, a.delay]), star: star && star.dur }; }""")
    check("Amethyst's whirl is slower than it was (more than 3s a turn)", (m.get("whirl") or 0) >= 5, m.get("whirl"))
    names = sorted({b[0] for b in m.get("boom") or []})
    check("Supernova detonates: core, flares, light, cross-flare and blast shell on one clock, together",
          names == ["rk-nova-core", "rk-nova-flare", "rk-nova-halo", "rk-nova-shock", "rk-nova-x"]
          and len({(b[1], b[2]) for b in m["boom"]}) == 1, m.get("boom"))
    check("and its star turns faster than once a minute", 0 < (m.get("star") or 0) < 60, m.get("star"))
    ctx.close()


def check_b285(br):
    """Build 285. (1) The Question bank's two choices fill its bar - the
    grid was a fixed three columns and left an empty third beside All and
    Flagged. (2) Unit details' lone Flagged button spans the whole row,
    bigger, with its title centred. Written against 284, where both fail."""
    print("\n58. build 285: the bank switch fills its bar, the Flagged button is full width and centred")
    for w, h, label in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
          document.documentElement.classList.remove('is-reloading'); document.getElementById('pushing-update')?.remove();
          store.seenUnitSelectTour = true; cfg.mode = 'drill'; const unit = topicsIn(QUESTIONS)[0]; cfg.units = [unit];
          showSetup(); await wait(700);
          document.getElementById('nextbtn')?.click(); await wait(800);
          const l = document.querySelector('.unitoptions-modal-sheet .bank-opts'), lr = l.getBoundingClientRect();
          const os = [...l.querySelectorAll('.bank-opt')].map(o => o.getBoundingClientRect());
          out.bank = { inner: Math.round(lr.width), used: Math.round(os[os.length - 1].right - os[0].left), n: os.length };
          document.querySelector('.unitoptions-modal-scrim')?.click(); await wait(500);
          const row = [...document.querySelectorAll('.pick')].find(r => (r.querySelector('input') || {}).value === unit);
          row.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 50, clientY: 50, button: 0 }));
          await wait(600); row.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 50, clientY: 50 })); await wait(900);
          const d = document.querySelector('.unitdetail-door'), p = d.parentElement.getBoundingClientRect(), dr = d.getBoundingClientRect();
          const t = d.querySelector('.unitdetail-doortitle').getBoundingClientRect(), c = d.querySelector('.unitdetail-doorcount').getBoundingClientRect();
          out.door = { w: Math.round(dr.width), row: Math.round(p.width), h: Math.round(dr.height),
                       off: Math.round(Math.abs(((t.left + c.right) / 2) - (dr.left + dr.width / 2))) };
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        b, d = r.get("bank") or {}, r.get("door") or {}
        check("%s: All and Flagged fill the Question bank bar" % label,
              b.get("n") == 2 and b.get("inner", 0) - b.get("used", 0) <= 12, r.get("bank") or r.get("threw"))
        check("%s: the Flagged button spans its row, is taller, and its title is centred" % label,
              d.get("w") == d.get("row") and d.get("h", 0) >= 56 and d.get("off", 99) <= 3, r.get("door") or r.get("threw"))
        ctx.close()


def check_b287_rooms(br):
    """Build 287. An open room in a match is still listed, said to be in
    a match, and a room's state is said either way; a room everybody has
    left is not. Written against 286, which dropped any room not waiting."""
    print("\n59. build 287: open rooms in a match are listed, and say so")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{ const now = Date.now(); const out = {};
      try{
        const doc = (id, r) => ({ id, data: () => r });
        const here = { a: { name: 'A', seen: now - 5000 }, b: { name: 'B', seen: now - 5000 } };
        const rooms = openRoomsFrom([
          doc('LOBBY1', { open: true, status: 'waiting', createdAt: now - 60000, participants: here }),
          doc('MATCH1', { open: true, status: 'starting', createdAt: now - 3600000, participants: here }),
          doc('GONE01', { open: true, status: 'waiting', createdAt: now - 3600000, participants: { c: { name: 'C', seen: now - 3600000 } } }),
          doc('SHUT01', { open: false, status: 'waiting', createdAt: now - 60000, participants: here }) ]);
        out.rooms = rooms.map(x => [x.code, x.inMatch, x.count]);
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    rooms = {c: (m, n) for c, m, n in (r.get("rooms") or [])}
    check("a room in a match is listed, marked in a match, with its head count",
          rooms.get("MATCH1") == (True, 2), str(r))
    check("a lobby is listed as a lobby; a room everybody left, or a closed one, is not",
          rooms.get("LOBBY1") == (False, 2) and "GONE01" not in rooms and "SHUT01" not in rooms, str(r))
    ctx.close()


def check_b288(br):
    """Build 288. (1) The length slider glides and counts one question at a
    time on a small unit. (2) The swipe hint points forward, and swipe to
    advance is switched on once for everyone. (3) The lag fixes are in
    place: the halo is a drawn-once canvas clipped at the screen, the orbit
    emblems hold still, the badge cutscene has no full-screen blur, and a
    second Home visit reuses the glow it already drew. Written against
    287, where every one of these fails."""
    print("\n60. build 288: slider, swipe hint, swipe on, and the lag fixes")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        document.documentElement.classList.remove('is-reloading'); document.getElementById('pushing-update')?.remove();
        store.seenUnitSelectTour = true; store.seenUnitOptionsTour = true;
        /* (2) swipe on, once */
        try{ localStorage.removeItem('class26e.swipeon.288'); }catch(e){}
        theme.swipeAdvance = false; if(store.theme) store.theme.swipeAdvance = false; loadTheme();
        out.swipeOnce = theme.swipeAdvance;
        theme.swipeAdvance = false; if(store.theme) store.theme.swipeAdvance = false; loadTheme();
        out.swipeStaysOff = theme.swipeAdvance === false;
        theme.swipeAdvance = true;
        /* (3) Home */
        showHome(); await wait(1500);
        const glow = document.querySelector('.homeglow-hero');
        out.halo = glow ? glow.tagName : null;
        const wrap = document.querySelector('.wrap'); out.clip = wrap ? getComputedStyle(wrap).overflowX : null;
        out.orbitAnims = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && t.closest && t.closest('.cosmic-icon-badge .rank-emblem-svg'); }).length;
        const bc = document.createElement('div'); bc.className = 'badge-cutscene'; document.body.appendChild(bc);
        out.badgeBlur = getComputedStyle(bc).backdropFilter || getComputedStyle(bc).webkitBackdropFilter || 'none'; bc.remove();
        showProfile(); await wait(500); showHome(); await wait(600);
        out.glowReused = !!document.querySelector('.cosmic-hero-glowbox > canvas');
        /* (1) the slider on a small unit */
        cfg.mode = 'drill'; const unit = topicsIn(QUESTIONS).find(u => u.indexOf('Identity') >= 0); cfg.units = [unit]; cfg.size = 0;
        showSetup(); await wait(700);
        document.getElementById('nextbtn')?.click(); await wait(900);
        const sl = document.querySelector('.howmany-sect input.slider'), val = document.querySelector('.howmany-sect .sliderval');
        out.step = sl.getAttribute('step') || sl.step;
        sl.value = '7.4'; sl.dispatchEvent(new Event('input', { bubbles: true })); await wait(50);
        out.mid = { thumb: Number(sl.value), shown: val.textContent, size: cfg.size };
        sl.dispatchEvent(new Event('change', { bubbles: true })); await wait(50);
        out.after = Number(sl.value);
        /* (2) the hint's chevrons */
        document.querySelector('.unitoptions-modal-scrim')?.click(); await wait(300);
        const qs = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit);
        beginRun(qs); const t0 = performance.now();
        while(!document.querySelector('.choice') && performance.now() - t0 < 8000) await wait(100);
        const chev = document.querySelector('.swipehint .swipechev');
        out.chev = chev ? chev.getAttribute('d') : null;
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("the length slider glides (step 'any') and counts one question at a time on a 12-question unit",
          r.get("step") == "any" and (r.get("mid") or {}).get("size") == 7 and "7 of" in str((r.get("mid") or {}).get("shown")), str(r.get("mid") or r.get("threw")))
    check("and the thumb stays under the finger mid-drag, then settles on the count",
          abs((r.get("mid") or {}).get("thumb", 0) - 7.4) < 0.01 and r.get("after") == 7, str([r.get("mid"), r.get("after")]))
    check("the swipe hint points forward, the way the next question arrives",
          str(r.get("chev") or "").startswith("M9 5l6 7"), str(r.get("chev")))
    check("swipe to advance is switched on once, and turning it off afterwards sticks",
          r.get("swipeOnce") is True and r.get("swipeStaysOff") is True, str([r.get("swipeOnce"), r.get("swipeStaysOff")]))
    check("Home's halo is a canvas drawn once, clipped at the screen",
          r.get("halo") == "CANVAS" and r.get("clip") == "clip", str([r.get("halo"), r.get("clip")]))
    check("the orbit's emblems hold still and the badge cutscene has no full-screen blur",
          r.get("orbitAnims") == 0 and r.get("badgeBlur") == "none", str([r.get("orbitAnims"), r.get("badgeBlur")]))
    check("a second Home visit reuses the sphere glow it already drew", r.get("glowReused") is True, str(r.get("glowReused")))
    ctx.close()


def check_b289(br):
    """Build 289. (1) The rewards count what they say: a Drill question got
    wrong and answered again is a retake, counted as it happens; the
    one-time seed fills the retake count and the best runs from what is on
    record and never lowers anything; the Detective keeps its best run; the
    Koi is seven study days in a row; Koi Pond a hundo in every unit;
    Phoenix seven units aced in a row; Midnight Oil 35 hours; Neon City 25
    matches. (2) Bars fill with a transform. (3) Last week's top 3 are
    congratulated once. (4) The Profile rank box is one of three, and the
    three tips are armed by tourRev. Written against 288, where all of it
    fails."""
    print("\n61. build 289: rewards, smooth bars, last week's top 3, the rank box")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        document.documentElement.classList.remove('is-reloading'); document.getElementById('pushing-update')?.remove();
        const b = id => (BANNERS.find(x => x.id === id) || {});
        out.needs = ['study50', 'vr50', 'exam100', 'tests500'].map(id => b(id).need);
        out.units = topicsIn(QUESTIONS).length;
        out.koiFeat = (AVATAR_CHARACTERS.find(c => c.id === 'valkyrie') || {}).feat;
        /* Koi: a run of seven, not seven days */
        store.studyLog = { '2026-09-01': 9, '2026-09-02': 9, '2026-09-03': 9, '2026-09-05': 9, '2026-09-06': 9, '2026-09-07': 9 };
        out.koiSix = isLockedCharacter('valkyrie');
        store.studyLog['2026-09-04'] = 9; store.studyLog['2026-09-08'] = 9;
        out.koiSeven = !isLockedCharacter('valkyrie');
        /* Phoenix keeps the best run */
        store.practiceExamPerfect = false; store.unitHundoStreak = 0; store.unitHundoStreakBest = 6; out.ph6 = bannerEarned('exam100');
        store.unitHundoStreakBest = 7; out.ph7 = bannerEarned('exam100');
        /* Detective keeps the best run */
        store.dailyCorrectStreak = 0; store.dailyCorrectBest = 10; out.det = !isLockedCharacter('detective');
        /* the seed never lowers, and fills */
        store.challengeSeed289 = false; store.retakenQuestions = 500; store.lifetime.drillPlays = 4; store.lifetime.examPlays = 0;
        store.stats[KEYS[0]] = { n: 9, m: 7, r: [] };
        seedChallenges289(); out.seedKeeps = store.retakenQuestions;
        store.challengeSeed289 = false; store.retakenQuestions = 0; seedChallenges289(); out.seedFills = store.retakenQuestions;
        /* a real drill: wrong twice then right is one retake; right first time is none */
        store.retakenQuestions = 0; store.seenUnitSelectTour = true;
        cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = ['Identity Crimes'];
        const qs = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === 'Identity Crimes').slice(0, 2);
        beginRun(qs, null, null, false); await wait(3600);
        let qi = order[pos], right = correctSlot(qi), wrong = right === 0 ? 1 : 0;
        choose(wrong); await wait(50); choose(wrong); await wait(50); choose(right); await wait(80);
        out.afterMiss = store.retakenQuestions;
        advance(); await wait(900);
        qi = order[pos]; right = correctSlot(qi); choose(right); await wait(80);
        out.afterClean = store.retakenQuestions;
        testInProgress = false; showHome(); await wait(300);
        /* a "Retake missed questions" run counts every question, first try or not */
        store.retakenQuestions = 0;
        beginRun(qs, 'Missed questions', null, true); await wait(900);
        for(let k = 0; k < qs.length; k++){ const q = order[pos]; choose(correctSlot(q)); await wait(80); if(k < qs.length - 1){ advance(); await wait(900); } }
        out.retakeRun = store.retakenQuestions;
        testInProgress = false; isMissedRetake = false; showHome(); await wait(300);
        /* (2) the unlock card's bar */
        showUnlockDetail(bannerDetail('vr50')); await wait(900);
        const f = document.querySelector('.unlock-card-fill');
        out.bar = f ? { sbar: f.classList.contains('sbar'), prop: getComputedStyle(f).transitionProperty, t: getComputedStyle(f).transform !== 'none' } : null;
        out.note = (document.querySelector('.unlock-card') || {}).innerText || '';
        document.querySelectorAll('.invite-overlay').forEach(x => x.remove());
        showUnlockDetail(bannerDetail('tests100')); await wait(300);
        out.fullNote = /full-length/i.test((document.querySelector('.unlock-card') || {}).innerText || '');
        document.querySelectorAll('.invite-overlay').forEach(x => x.remove());
        /* (3) last week's top 3, once */
        store.seenRewardsTour = true; try{ localStorage.removeItem('class26e.weekcongrats.v1'); }catch(e){}
        const lw = lastWeekKey();
        /* A hand-recorded week (WEEK_RESULTS_KNOWN) names its three by id. */
        const ids = (WEEK_RESULTS_KNOWN[lw] || []).map(k => k.pub || k).concat(['p1', 'p2', 'p3']);
        leaderboardRows = [ { pub: ids[0], firstName: 'Ada', avatarChar: 'ninja', week: lw, weekPoints: 900 },
          { pub: ids[1], firstName: 'Bo', avatarChar: 'ghost', week: lw, weekPoints: 800 },
          { pub: ids[2], firstName: 'Cy', avatarChar: 'alien', week: lw, weekPoints: 700 },
          { pub: store.publicId, firstName: store.firstName, avatarChar: 'ninja', week: lw, weekPoints: 10 } ];
        leaderboardRowsFromServer = true;
        showRankings('overall'); await wait(1600);
        const card = document.querySelector('.week-congrats');
        out.congrats = card ? card.querySelectorAll('.lw-podium-spot').length : 0;
        document.querySelectorAll('.invite-overlay').forEach(x => x.remove());
        showHome(); await wait(300); showRankings('week'); await wait(1600);
        out.congratsAgain = !!document.querySelector('.week-congrats');
        showHome(); await wait(300);
        /* (4) the rank box and the tips */
        store.tourRev = 2; store.seenProfileTour = true; store.profileTips289 = false;
        out.tourRev = TOUR_REV;
        if(typeof PROFILE_TIPS_289 !== 'undefined'){
          if(store.onboardingComplete && store.tourRev < TOUR_REV){ store.profileTips289 = true; store.tourRev = TOUR_REV; }
        }
        showProfile('profile'); await wait(900);
        const tip = document.getElementById('tour-text');
        out.tip = tip ? tip.textContent : '';
        document.querySelectorAll('#tour-overlay, #tour-tooltip, #tour-line, #tour-line-dot').forEach(x => x.remove());
        const rb = document.querySelector('.profile-hero .profile-rankplate'), lb = document.querySelector('.profile-hero .profile-level.statbox');
        if(rb && lb){
          const a = getComputedStyle(rb), c = getComputedStyle(lb);
          out.box = { bg: a.backgroundColor === c.backgroundColor && a.backgroundImage === 'none', radius: a.borderTopLeftRadius === c.borderTopLeftRadius,
            width: Math.abs(rb.getBoundingClientRect().width - lb.getBoundingClientRect().width) < 1, shadow: a.boxShadow === 'none',
            wm: !document.querySelector('.profile-hero .profile-rankplate-wm') || getComputedStyle(document.querySelector('.profile-hero .profile-rankplate-wm')).display === 'none' };
        }
        const eb = document.querySelector('.profile-hero .profile-edit-btn');
        out.edit = eb ? parseFloat(getComputedStyle(eb).fontSize) : 0;
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    # REVISED IN 294: Koi Pond is a hundo on the Penal Code (was every
    # unit, then one unit on ten days in 293).
    check("the reworked banners: Midnight Oil 35 hours, Neon City 25 matches, Phoenix 7 units in a row, Koi Pond one Penal Code hundo",
          r.get("needs") == [35, 25, 7, 1], r)
    check("the Koi is seven study days IN A ROW (six, or seven with a gap, is not enough)",
          r.get("koiFeat") == "studyrun7" and r.get("koiSix") is True and r.get("koiSeven") is True, r)
    check("Phoenix and the Detective keep their best run, so a later slip takes nothing back",
          r.get("ph6") is False and r.get("ph7") is True and r.get("det") is True, r)
    check("the one-time retake seed fills from misses on record and never lowers a count",
          r.get("seedKeeps") == 500 and r.get("seedFills", 0) >= 7, r)
    check("a Drill question got wrong and answered again is one retake, counted at once; a clean one is none",
          r.get("afterMiss") == 1 and r.get("afterClean") == 1, r)
    check("every question answered in a Retake missed questions run counts, as it is answered",
          r.get("retakeRun") == 2, r.get("retakeRun"))
    check("bars fill with a transform, not width", isinstance(r.get("bar"), dict) and r["bar"]["sbar"] and r["bar"]["prop"] == "transform" and r["bar"]["t"], r.get("bar"))
    check("the full-tests banners say they count full-length tests", r.get("fullNote") is True, r.get("note"))
    check("last week's top 3 are congratulated on the first Leaderboard visit, and only once",
          r.get("congrats") == 3 and r.get("congratsAgain") is False, r)
    check("tourRev 3 arms the three Profile tips, starting with Customize",
          r.get("tourRev") == 3 and "Customize" in str(r.get("tip")), r.get("tip"))
    check("the rank box is one of three: same box, radius, width, no glow, no watermark",
          isinstance(r.get("box"), dict) and all(r["box"].values()), r.get("box"))
    check("Customize is a little bigger", r.get("edit", 0) > 13, r.get("edit"))
    ctx.close()


def check_b290(br):
    """Build 290: "When selecting a character, the glow has a delay when
    triggering." (1) The pick lights in the same tap - class on, store set -
    with saving and the header redraw held back until after the glow. (2)
    The glow is a short ease-out, the pool on its own layer. (3) No
    :has(.selected) on the character cells (it re-checked the page's styles
    on every pick). (4) Customize pauses the banner tiles and theme
    swatches it cannot see. Written against 289, where all four fail."""
    print("\n62. build 290: the character glow lights on the tap")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        document.getElementById('pushing-update')?.remove();
        showCustomize(); await wait(900);
        const o = [...document.querySelectorAll('.screen-customize .avatarchar-option:not(.locked):not(.selected)')][0];
        let saves = 0; const realSave = window.saveStore; window.saveStore = function(){ saves++; return realSave.apply(this, arguments); };
        o.click();
        out.sync = { selected: o.classList.contains('selected'), cell: o.parentElement.classList.contains('is-selected'), savedYet: saves };
        await wait(500); out.savedLater = saves > 0; window.saveStore = realSave;
        const cs = getComputedStyle(o), pool = getComputedStyle(o, '::before');
        const dur = (prop, list) => { const ps = list.transitionProperty.split(',').map(x => x.trim()), ds = list.transitionDuration.split(',').map(x => parseFloat(x)); const i = ps.indexOf(prop); return i < 0 ? null : ds[i]; };
        out.glow = { k: dur('--char-glow-k', cs), pool: dur('opacity', pool), poolLayer: pool.willChange };
        let hasRule = false;
        [...document.styleSheets].forEach(sh => { try{ [...sh.cssRules].forEach(r => { if(r.selectorText && /avatarchar-cell:has\(/.test(r.selectorText)) hasRule = true; }); }catch(e){} });
        out.hasRule = hasRule;
        const sw = document.querySelector('.screen-customize .swatch'), bo = document.querySelector('.screen-customize .banner-opt');
        out.offscreen = { swatch: !!(sw && sw.classList.contains('is-offscreen')), banner: !!(bo && bo.classList.contains('is-offscreen')) };
        const dot = sw && sw.querySelector('.dot'); out.dotPaused = dot ? getComputedStyle(dot).animationPlayState : null;
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    s = r.get("sync") or {}
    check("a pick lights in the same tap, and saving waits until after the glow",
          s.get("selected") is True and s.get("cell") is True and s.get("savedYet") == 0 and r.get("savedLater") is True, r)
    g = r.get("glow") or {}
    check("the glow comes up in a short ease-out, the pool on its own layer",
          g.get("k") is not None and g["k"] <= 0.25 and g.get("pool") is not None and g["pool"] <= 0.3 and "opacity" in str(g.get("poolLayer")), g)
    check("no :has(.selected) on the character cells", r.get("hasRule") is False, r.get("hasRule"))
    check("Customize pauses the swatches and banner tiles it cannot see",
          (r.get("offscreen") or {}) == {"swatch": True, "banner": True} and r.get("dotPaused") in ("paused", None), r)
    ctx.close()


def check_b291(br):
    """Build 291. (1) Unlocks in one sitting: cloud data landing after
    Home is up gets its card on the same visit, and anything newly earned
    while a card is up joins the same queue. (2) The Marksman is 250 in a
    row. (3) The Hive: 500 questions in a day (300 in 291), counted per answer. (4)
    Sliders follow a touch from anywhere on the track, and the hundo line
    is always there while a run can be cut, so the slider never moves
    mid-drag. (5) The options say "answer choices", carry a one-line
    description, and the timers are "Countdown timer" / "Track my time".
    (6) Loading is half a second shorter. (7) The flag is bigger and up in
    the corner. (8) Pause names the units, under Paused, in the middle.
    Written against 290, where every one of these fails."""
    print("\n63. build 291: one sitting, Hive, sliders, start sheet, flag, pause")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        document.documentElement.classList.remove('is-reloading'); document.getElementById('pushing-update')?.remove();
        store.seenUnitSelectTour = true; store.seenUnitOptionsTour = true;
        /* (2)(3) the feats */
        out.marks = CHARACTER_FEATS.streak100 && CHARACTER_FEATS.streak100.need;
        out.hive = { def: AVATAR_CHARACTERS.some(c => c.id === 'hive'), feat: (CHARACTER_FEATS.busyday300 || {}).need,
                     svg: (() => { try{ const s = buildAvatarCharSVG('hive'); return !!(s && s.querySelector('.cx-fx-hivebees')); }catch(e){ return false; } })() };
        const keep = [store.dayAnswered, store.dayAnsweredBest];
        store.dayAnswered = null; store.dayAnsweredBest = 0;
        out.hiveLocked0 = isLockedCharacter('hive');
        const qi = QUESTIONS.findIndex(q => (q.topic || '').indexOf('Identity') >= 0);
        try{ recordResult(qi, true); recordResult(qi, false); }catch(e){ out.recordThrew = String(e); }
        out.dayCount = typeof busiestDay === 'function' ? busiestDay() : null;
        const HN = CHARACTER_FEATS.busyday300.need; store.dayAnswered = null; store.dayAnsweredBest = HN - 1; out.hiveLocked299 = isLockedCharacter('hive');
        store.dayAnsweredBest = HN; out.hiveOpen300 = !isLockedCharacter('hive');
        out.defaulted = (() => { const d = JSON.parse(JSON.stringify(store)); delete d.dayAnsweredBest; delete d.dayAnswered; applyLoadedData(d);
          return [store.dayAnsweredBest, store.dayAnswered]; })();
        store.dayAnswered = keep[0]; store.dayAnsweredBest = 0;
        /* (1) one sitting. A clean slate, then Home. */
        const kStreak = store.bestTestStreak;
        store.bestTestStreak = 0;
        const p0 = pendingHomeUnlocks(); markUnlocksShown(p0.chars, p0.banners);
        showHome(); await wait(3200);
        out.spotsAtStart = document.querySelectorAll('.rs-spot').length;
        /* the cloud copy lands: a character earned elsewhere */
        store.bestTestStreak = CHARACTER_FEATS.streak100.need;
        persistLocally();
        let t0 = performance.now();
        while(!document.querySelector('.rs-spot') && performance.now() - t0 < 4000) await wait(100);
        const s1 = document.querySelector('.rs-spot');
        out.first = s1 ? s1.textContent.slice(0, 160) : null;
        /* earned while the first card is up */
        store.dayAnsweredBest = CHARACTER_FEATS.busyday300.need;
        await wait(800);
        s1 && s1.click();
        t0 = performance.now(); let s2 = null;
        while(performance.now() - t0 < 4000){ await wait(100); s2 = document.querySelector('.rs-spot'); if(s2 && s2 !== s1 && s2.isConnected && !/Marksman/.test(s2.textContent)) break; s2 = null; }
        out.second = s2 ? s2.textContent.slice(0, 160) : null;
        out.stillHome = !!stage.querySelector('[data-screen="home"]');
        s2 && s2.click(); await wait(1600);
        store.bestTestStreak = kStreak; store.dayAnsweredBest = keep[1] || 0;
        /* (4)(5) the start sheet */
        cfg.mode = 'drill'; const unit = topicsIn(QUESTIONS).find(u => u.indexOf('Identity') >= 0); cfg.units = [unit]; cfg.size = 0;
        showSetup(); await wait(700);
        document.getElementById('nextbtn')?.click(); await wait(900);
        const sl = document.querySelector('.howmany-sect input.slider');
        const note = document.querySelector('.unitoptions-modal-sheet .hundo-note');
        const box = el => { const b = el.getBoundingClientRect(); return [Math.round(b.top), Math.round(b.height)]; };
        out.noteAll = note ? { hidden: note.hidden, text: note.textContent, h: box(note)[1] } : null;
        const slTop0 = box(sl)[0];
        const r0 = sl.getBoundingClientRect(), y = r0.top + r0.height / 2;
        const touch = (type, x) => { const t = new Touch({ identifier: 1, target: sl, clientX: x, clientY: y });
          sl.dispatchEvent(new TouchEvent(type, { touches: type === 'touchend' ? [] : [t], changedTouches: [t], targetTouches: type === 'touchend' ? [] : [t], bubbles: true, cancelable: true })); };
        const x0 = r0.left + r0.width * .35;
        out.sizeBefore = cfg.size;
        touch('touchstart', x0); await wait(16);
        touch('touchmove', x0 + 12); await wait(16);
        out.midDrag = { size: cfg.size, top: box(sl)[0] };
        touch('touchmove', x0 + 30); await wait(16);
        touch('touchend', x0 + 30); await wait(200);
        out.sizeAfter = cfg.size; out.slTop = [slTop0, box(sl)[0]];
        out.notePartial = note ? { hidden: note.hidden, text: note.textContent, h: box(note)[1] } : null;
        /* every other slider on the sheet takes a touch the same way */
        out.sliders = [...document.querySelectorAll('input[type=range]')].length;
        const labs = [...document.querySelectorAll('.unitoptions-modal-sheet .otitle, .unitoptions-modal-sheet .olabel, .unitoptions-modal-sheet label')].map(e => e.textContent.trim()).join(' | ');
        out.labels = labs;
        out.hints = [...document.querySelectorAll('.unitoptions-modal-sheet .ohint')].filter(h => h.offsetParent && h.textContent.trim()).map(h => h.textContent.trim());
        out.sheetText = (document.querySelector('.unitoptions-modal-sheet') || {}).textContent || '';
        document.querySelector('.unitoptions-modal-scrim')?.click(); await wait(300);
        /* (6) loading, (7) flag, (8) pause */
        cfg.units = [unit]; cfg.size = 0;
        const qs = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit);
        beginRun(qs); t0 = performance.now();
        while(!document.querySelector('.choice') && performance.now() - t0 < 8000) await wait(25);
        out.loadMs = Math.round(performance.now() - t0);
        await wait(700);
        const fb = document.querySelector('.qnumrow > .flagbtn'), qn = document.querySelector('.qnumrow .qnum'), qt = document.querySelector('.qtext');
        const card = fb && fb.closest('.panel');
        if(fb){ const b = fb.getBoundingClientRect(), n = qn.getBoundingClientRect(), t = qt.getBoundingClientRect(), c = card.getBoundingClientRect();
          out.flag = { w: Math.round(b.width), icon: Math.round(fb.querySelector('.flagicon').getBoundingClientRect().width),
                       centreAboveLine: Math.round((b.top + b.bottom) / 2 - (n.top + n.bottom) / 2), aboveQuestion: Math.round(t.top - b.bottom),
                       rightGap: Math.round(c.right - b.right) }; }
        pauseRun(); await wait(500);
        const units = document.querySelector('.pause-units'), where = document.querySelector('.pause-where'), pp = document.querySelector('.pausepanel');
        out.pause = { units: units ? units.textContent : null, where: where ? where.textContent : null,
                      size: units ? parseFloat(getComputedStyle(units).fontSize) : 0,
                      centreOff: pp ? Math.round((pp.getBoundingClientRect().top + pp.getBoundingClientRect().bottom) / 2 - innerHeight / 2) : null,
                      unitsTop: units ? Math.round(units.getBoundingClientRect().top) : null,
                      scope: (() => { const s = document.querySelector('.test-scopelabel'); return s ? getComputedStyle(s).visibility : 'none'; })() };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    if r.get("threw"):
        print("   threw:", r["threw"][:400])
    check("the Marksman is 250 in a row in one test", r.get("marks") == 250, r.get("marks"))
    hv = r.get("hive") or {}
    check("the Hive exists, is drawn with its bees, and asks for 500 questions in a day (build 292)",
          hv.get("def") and hv.get("svg") and hv.get("feat") == 500, hv)
    check("every answer counts toward the day, right or wrong, and the Hive opens at its number, not one short",
          r.get("dayCount") == 2 and r.get("hiveLocked0") and r.get("hiveLocked299") and r.get("hiveOpen300"),
          [r.get("dayCount"), r.get("hiveLocked0"), r.get("hiveLocked299"), r.get("hiveOpen300"), r.get("recordThrew")])
    check("an account from an older build gets the day counters defaulted", r.get("defaulted") == [0, None], r.get("defaulted"))
    check("a character that arrives with the cloud copy plays on the same Home visit",
          r.get("spotsAtStart") == 0 and "Marksman" in str(r.get("first")), [r.get("spotsAtStart"), r.get("first")])
    check("and one earned while that card is up plays straight after it, still on Home",
          "Hive" in str(r.get("second")) and "500 questions" in str(r.get("second")) and r.get("stillHome"), [r.get("second"), r.get("stillHome")])
    na, npart = r.get("noteAll") or {}, r.get("notePartial") or {}
    check("on All, the hundo line is already there (says the whole unit counts)",
          na and not na.get("hidden") and "counts as a hundo" in na.get("text", ""), na)
    check("a touch on the track away from the thumb moves the count, first time, from All",
          r.get("sizeBefore") == 0 and 0 < (r.get("sizeAfter") or 0) < 12, [r.get("sizeBefore"), (r.get("midDrag") or {}).get("size"), r.get("sizeAfter")])
    st = r.get("slTop") or [0, 1]
    check("the slider does not move while it is dragged below All, and the line keeps its height",
          st[0] == st[1] == (r.get("midDrag") or {}).get("top") and npart.get("h") == na.get("h") and "won't count" in npart.get("text", ""),
          [st, (r.get("midDrag") or {}).get("top"), na.get("h"), npart.get("h")])
    txt = r.get("sheetText") or ""
    check("the options say 'answer choices', and the timers say what they do",
          all(s in txt for s in ["Shuffle answer choices", "Hide answer choices", "Countdown timer", "Track my time"])
          and "Stopwatch" not in txt, txt[:300])
    check("each of those four carries a one-line description",
          len([h for h in r.get("hints", []) if len(h) < 80]) >= 4, r.get("hints"))
    check("the loading screen is about half a second shorter (2.5s)",
          2300 <= (r.get("loadMs") or 0) <= 2850, r.get("loadMs"))
    fl = r.get("flag") or {}
    check("the test's flag is bigger (44px+ button, 26px+ icon), up above the question line, right in the corner",
          fl.get("w", 0) >= 44 and fl.get("icon", 0) >= 26 and fl.get("centreAboveLine", 0) < -3 and fl.get("aboveQuestion", -1) >= 0 and fl.get("rightGap", 99) <= 16, fl)
    pz = r.get("pause") or {}
    check("Pause names the unit and the question, in bigger type, lowered from the top",
          "Identity" in str(pz.get("units")) and "Question 1 of" in str(pz.get("where")) and pz.get("size", 0) >= 19
          and (pz.get("unitsTop") or 0) > 250, pz)
    check("and the pause panel sits in the middle of the screen, the header's small line out of the way",
          abs(pz.get("centreOff") or 999) <= 80 and pz.get("scope") in ("hidden", "none"), pz)
    ctx.close()


def check_b294(br):
    """Build 294: "that koi pond challenge is too confusing and weird.
    Simple and unique, change it." Koi Pond is a hundo on the Penal Code:
    one line, the target does not follow the number of units, the short
    version never counts, and a whole-unit Penal Code hundo earns it.
    Written against 293, where it fails."""
    print("\n64. build 294: Koi Pond is a hundo on the Penal Code")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try{
        document.getElementById('pushing-update')?.remove();
        const b = BANNERS.find(x => x.id === 'tests500');
        out.label = b.label; out.need = b.need;
        out.note = typeof b.note === 'function' ? b.note() : b.note;
        out.needWithMoreUnits = (() => { try{ QUESTIONS.push({ topic: 'A New Unit', src: 'x' }); return BANNERS.find(x => x.id === 'tests500').need; } finally { QUESTIONS.pop(); } })();
        store.unitPerfects = {};
        const P = 'Penal Code';
        out.none = bannerEarned('tests500');
        /* the short version: not the whole unit, so no hundo */
        cfg.units = [P]; cfg.source = 'all'; cfg.versions = { [P]: 'test' }; runLabel = P;
        order = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === P).slice(0, 56);
        recordUnitPerfectIfEligible(100); out.short = bannerEarned('tests500');
        /* another unit's hundo does nothing */
        store.unitPerfects['Identity Crimes'] = 3; out.other = bannerEarned('tests500');
        /* the whole unit */
        cfg.versions = {}; order = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === P);
        out.total = order.length;
        recordUnitPerfectIfEligible(100); out.whole = bannerEarned('tests500');
        const d = bannerDetail('tests500'); out.detail = d && (d.need || d.label || '') + ' ' + (d.note || '');
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    if r.get("threw"):
        print("   threw:", r["threw"][:400])
    check("Koi Pond says one simple thing: a hundo on the Penal Code",
          r.get("label") == "Get a hundo on the Penal Code" and r.get("need") == 1, [r.get("label"), r.get("need")])
    check("the note gives the real question count and says the short version does not count",
          ("All %s questions" % r.get("total")) in str(r.get("note")) and "short version" in str(r.get("note")), r.get("note"))
    check("adding a unit to the app does not move the target", r.get("needWithMoreUnits") == 1, r.get("needWithMoreUnits"))
    check("nothing, the short version, or another unit's hundo does not earn it",
          r.get("none") is False and r.get("short") is False and r.get("other") is False, [r.get("none"), r.get("short"), r.get("other")])
    check("a whole Penal Code hundo earns it", r.get("whole") is True, r.get("whole"))
    ctx.close()


def main():
    # ONLY_B245=slogan,modes runs just those build 245 polish sections.
    only = os.environ.get("ONLY_B245")
    if only:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME)
            try:
                for name in only.split(","):
                    globals()["check_b245_" + name](br)
            finally:
                br.close()
        SERVER.shutdown()
        print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES),
                                         len(FAILURES)))
        return 1 if FAILURES else 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        try:
            check_launch(br)
            check_swipe(br)
            check_navigation(br)
            check_badges(br)
            check_cutscene(br)
            check_ranks(br)
            check_review_reach(br)
            check_slide(br)
            check_update_and_cards(br)
            check_b218(br)
            check_b220(br)
            check_b221(br)
            check_b223(br)
            check_b229(br)
            check_b230(br)
            check_b231(br)
            check_b232(br)
            check_b234(br)
            check_b235(br)
            check_b235b(br)
            check_b236(br)
            check_b237(br)
            check_b238(br)
            check_b239(br)
            check_b240(br)
            check_b240_units(br)
            check_b240_activity(br)
            check_b241(br)
            check_b241b(br)
            check_b242(br)
            check_b243(br)
            check_b244(br)
            check_b245_ladder(br)
            check_penal_versions(br)
            check_audit_a(br)
            for name in B245_POLISH:
                globals()["check_b245_" + name](br)
            check_b246(br)
            check_b248_weekly(br)
            check_b250(br)
            check_b258(br)
            check_b266(br)
            check_b267(br)
            check_b268(br)
            check_b269(br)
            check_b270(br)
            check_b271(br)
            check_b272(br)
            check_b273(br)
            check_b274(br)
            check_b275(br)
            check_b276(br)
            check_b277(br)
            check_b278(br)
            check_b279_merge(br)
            check_b280_rankmap_still(br)
            check_b281_badge_card(br)
            check_b282(br)
            check_b283(br)
            check_b284(br)
            check_b285(br)
            check_b287_rooms(br)
            check_b288(br)
            check_b289(br)
            check_b290(br)
            check_b291(br)
            check_b294(br)
        finally:
            br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))"
          % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES),
             len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
