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
        ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
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
        ("game, one unit at 10, nowhere near",
         {"mode": "game", "nUnits": 1, "offset": None, "flat": 10, "vroom": False}, 0, 0),
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
    check("the tab bar carries a Ranks tab", ptabs["bottom"], ptabs)
    pg.evaluate("()=>showProfile('ranks')")
    pg.wait_for_timeout(1500)
    tabs = pg.evaluate("""()=>({
      screen: !!document.querySelector('.screen-ranks'),
      rendered: [...document.querySelectorAll('.profiletabs .iconbtn')].map(b=>b.textContent),
      active: (document.querySelector('.profiletabs .iconbtn.active')||{}).textContent,
      swipe: RANKS_TABS.slice(),
      tabLit: document.querySelector('#bottomtab-ranks').classList.contains('active')})""")
    check("an old link to Profile's rank tab lands on the Ranks screen, Rank showing",
          tabs["screen"] and len(tabs["rendered"]) == 2 and tabs["active"] == tabs["rendered"][0] and
          tabs["swipe"] == ["ranks", "badges"], tabs)
    check("the Ranks tab in the bar is lit on its own screen", tabs["tabLit"], tabs)

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
    check("your character stands on the rank you hold, and only there",
          [i for i, c in enumerate(cards) if c["you"]] == [2] and "here" in cards[2]["state"],
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
    # bronze silver icons after all"). Since build 245 they are, bottom to
    # top: a nebula, a protostar, a comet, a binary, a galaxy, a ring
    # nebula and the Supernova burst (re-dealt so the ladder climbs - see
    # section 34). The check is structural rather than a look: no two
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
    # The Game difficulty is on the sheet, not in a dropdown; Review has sources.
    sh = pg.evaluate("""()=>{ cfg.mode='game'; cfg.units=[topicsIn(QUESTIONS)[0]]; showSetup();
      const g=document.querySelector('.speedgrid'); const inDrop=!!(g && g.closest('.more-body'));
      cfg.mode='review'; showSetup(); const d=document.querySelector('.drawfrom-sect');
      return { speed: !!g, inDropdown: inDrop, reviewSources: !!(d && !d.hidden) }; }""")
    check("the Game difficulty is not hidden in the options dropdown", sh["speed"] and not sh["inDropdown"], sh)
    check("Review can draw from flagged and most missed", sh["reviewSources"], sh)
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
      // Build 225: the two Game challenges hand over banners, not characters.
      out.foxAfter = !bannerEarned('easy10');
      out.vikingAfter = !bannerEarned('average10');
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
    check("Game beats already on the account earn the Easy banner, not the Average one - and there is no Fox or Viking",
          not c["foxAfter"] and c["vikingAfter"] and c["noFox"], c)
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
    check("a hand-recorded week (Sauce, OdinSavior, Napoleon; 21 Sep) replaces numbers that cannot be trusted, and shows no made-up total",
          r["pinned"] == [["Eli", None]] and r["pinnedPts"] == ["Winner"] and r["sauce"] == ["ew7hyxpg5j2y", "kdxnp7smgcre", "mbw5qdhcw2pf"], r)
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
      openPersonSheet({ pub:'bo', firstName:'Bo', avatarChar:'robot', level:40, badges:6, banner:'average10' });
      const card = document.querySelector('.person-card');
      out.cover = !!(card && card.classList.contains('has-cover') && card.querySelector('.person-card-cover .bnr'));
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      leaderboardRows = [{ pub:'f1', firstName:'Alex', avatarChar:'dragon', level:40, badges:6, hundos:3, banner:'easy10',
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
      T('starfall', () => { const b = bannerDef('badges16');
        QUESTIONS.push(Object.assign({}, QUESTIONS[0], { topic: 'A Unit Added Later' }));
        try{ return { label: b.label, need: b.need, units: topicsIn(QUESTIONS).length }; }
        finally{ QUESTIONS.pop(); } });
      T('hardcore', () => { store.unitGameBeat = {}; topicsIn(QUESTIONS).slice(0, 10).forEach(t => store.unitGameBeat[t] = { easy:true, average:true, hardcore:true });
        return bannerEarned('hardcore10'); });
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
    check("the challenge row: Detective, the Masked One, the two gods, the Clown, the Valkyrie, the Marksman, the Astronaut, the Hacker, the Timekeeper, then the secrets",
          r["order"] == ["detective", "masked", "zeus", "poseidon", "clown", "valkyrie", "marksman", "astronaut", "hacker", "timekeeper", "voidwalker", "umbra", "singularity"], r["order"])
    # Build 233: the Masked One is back, for retaking missed questions.
    check("the Masked One unlocks at 100 retaken questions and says how far along you are",
          isinstance(r["masked"], dict) and r["masked"]["feat"] == "retake100" and r["masked"]["before"] is True
          and "99 of 100" in r["masked"]["msg"] and r["masked"]["after"] is False, r["masked"])
    check("a third week on the weekly podium hands over Poseidon",
          isinstance(r["poseidon"], dict) and r["poseidon"]["top3"] == 3 and "poseidon" in r["poseidon"]["queued"]
          and r["poseidon"]["locked"] is False, r["poseidon"])
    check("a tenth Virtual Room win hands over the Valkyrie (the Spartan's before 244)",
          isinstance(r["spartan"], dict) and r["spartan"]["wins"] == 10 and "valkyrie" in r["spartan"]["queued"]
          and r["spartan"]["locked"] is False, r["spartan"])
    check("a rank character says only which rank unlocks it",
          isinstance(r["rankMsg"], str) and r["rankMsg"].startswith("Unlocks at ") and "rank" in r["rankMsg"]
          and "Level" not in r["rankMsg"] and "badge" not in r["rankMsg"], r["rankMsg"])
    check("Umbra and Singularity keep their requirement hidden until the one before is unlocked",
          isinstance(r["flareMsgs"], list) and "Unlock Void" in r["flareMsgs"][0] and "Unlock Umbra" in r["flareMsgs"][1]
          and "Find" not in "".join(r["flareMsgs"]), r["flareMsgs"])
    check("a finished retake of five missed questions counts five towards the Masked One",
          r["retakeRun"] == 12, r["retakeRun"])
    names = dict(r["banners"]) if isinstance(r["banners"], list) else {}
    check("Northern Lights is the 100-test banner and Sakura the 250",
          names.get("tests100") == "Northern Lights" and names.get("tests250") == "Sakura", names)
    check("Thunderhead, Sky Temple and the Supernova banner exist",
          names.get("hardcore10") == "Thunderhead" and names.get("hundos250") == "Sky Temple"
          and names.get("titan_rank") == "Supernova", names)
    check("Hardcore on ten units hands over the Thunderhead banner", r["hardcore"] is True, r["hardcore"])
    sf = r["starfall"] if isinstance(r["starfall"], dict) else {}
    check("Starfall's count is the units that exist, not a written-in sixteen",
          sf.get("need") == sf.get("units") and ("all %s badges" % sf.get("units")) in str(sf.get("label")), sf)
    check("the four circled themes put a second colour on the planet",
          isinstance(r["planets"], dict) and all(v >= 35 for v in r["planets"].values()), r["planets"])
    check("putting the app away publishes your leaderboard row there and then", r["publish"] == 1, r["publish"])

    # Screens
    s = pg.evaluate("""()=>{
      const out = {};
      const T = (k, f) => { try{ out[k] = f(); }catch(e){ out[k] = 'THREW ' + e.message; } };
      showProfile('ranks');
      T('ladder', () => [...document.querySelectorAll('.rankmap-stop .rankmap-name')].map(n => n.textContent));
      T('novaBanner', () => { const st = [...document.querySelectorAll('.rankmap-stop')].pop();
        return !!(st && st.querySelector('.rankmap-bannerprev .bnr, .rankmap-gift.is-banner .bnr')); });
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
      showPracticeTestConfirm();
      T('brief', () => ({ stats: document.querySelectorAll('.pt-stats .pt-stat').length, rules: document.querySelectorAll('.pt-rules .pt-rule').length,
                          record: !!document.querySelector('.pt-record') }));
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
    check("the Practice Test screen is a briefing: three numbers, four rules, your record",
          isinstance(s["brief"], dict) and s["brief"]["stats"] == 3 and s["brief"]["rules"] == 4 and s["brief"]["record"], s["brief"])
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
        const res = { chips: hm ? hm.querySelectorAll('.chip').length : -1, all: !!(hm && hm.querySelector('.slider-allbtn')),
                      caption: (sh.querySelector('.drawfrom-sect .bank-opt.on .bank-desc') || {}).textContent || '' };
        cfg.size = 0; if(sl){ sl.value = sl.min; sl.dispatchEvent(new Event('input', { bubbles:true })); }
        res.dragged = cfg.size; res.warn = !sh.querySelector('.hundo-note').hidden;
        if(sl){ sl.value = sl.max; sl.dispatchEvent(new Event('input', { bubbles:true })); }
        res.atEnd = cfg.size; res.warnAtEnd = !sh.querySelector('.hundo-note').hidden;
        const sw = sh.querySelectorAll('.timer-sect .opt input[type=checkbox]');
        res.timerSwitches = sw.length;
        if(sw[0]){ sw[0].checked = true; sw[0].dispatchEvent(new Event('change', { bubbles:true })); }
        res.timerAfter = cfg.timer;
        const tiles = [...sh.querySelectorAll('.opt-tile')].map(t => Math.round(t.getBoundingClientRect().top));
        res.tilesSideBySide = tiles.length === 2 && tiles[0] === tiles[1];
        cfg.timer = 'off';
        return res; });
      document.querySelector('.unitoptions-modal-scrim').click();
      showPracticeTestConfirm(); await wait(300);
      await T('phoenix', () => /Phoenix/i.test(document.getElementById('stage').textContent));
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
    check("the Question bank choice says what the pool is and how big", "in" in sh.get("caption", "") and any(ch.isdigit() for ch in sh.get("caption", "")), sh.get("caption"))
    check("the timer is two switches, and the first one sets a time limit",
          sh.get("timerSwitches") == 2 and sh.get("timerAfter") == "down", sh)
    check("the two answer options sit side by side", sh.get("tilesSideBySide") is True, sh)
    check("the Practice Test screen does not mention the Phoenix banner", r["phoenix"] is False, r["phoenix"])
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
      await T('plate', () => { const v = document.querySelector('.profile-level-num .profile-level-value');
        const w = document.querySelector('.profile-level-num .profile-level-word');
        return Math.round(w.getBoundingClientRect().top - v.getBoundingClientRect().bottom); });
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
      // The Marksman: 150 in a row (100 until build 246), counted from the streak on record.
      await T('marksman', () => { const had = store.lifetime.longestStreak; store.lifetime.longestStreak = 149;
        const a = isLockedCharacter('marksman'); store.lifetime.longestStreak = 150; const b = isLockedCharacter('marksman');
        store.lifetime.longestStreak = had; return [a, b]; });
      // The ladders sit together, easiest first.
      await T('order', () => BANNERS.map(b => b.id));
      await T('rankArt', () => ['adept_rank', 'elite_rank', 'titan_rank'].map(id => typeof BANNER_ART[id] === 'function' && !!bannerDef(id)));
      // The grade's reaction.
      await T('react', () => [{ isPerfect: true, pct: 100 }, { pct: 93 }, { pct: 75 }, { pct: 40 }, { gameLost: 3, pct: 90 }].map(gradeReaction));
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
    check("\"level\" sits under its number on the Profile card, the way \"badges\" does",
          isinstance(r["plate"], int) and r["plate"] >= -2, r["plate"])
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
    check("the Marksman unlocks at 150 in a row and not before", r["marksman"] == [True, False], r["marksman"])
    o = r["order"] if isinstance(r["order"], list) else []
    def run(ids):
        at = [o.index(i) if i in o else -99 for i in ids]
        return all(b == a + 1 for a, b in zip(at, at[1:]))
    check("banners of one ladder sit next to each other, easiest first",
          run(["easy10", "average10", "hardcore10"]) and run(["tests100", "tests250", "tests500"])
          and run(["hundos100", "hundos250"]) and run(["adept_rank", "elite_rank", "titan_rank"]), o)
    check("Sapphire and Amethyst have banners of their own beside Supernova's", r["rankArt"] == [True, True, True], r["rankArt"])
    check("the results character reacts to 100 / 90+ / a pass / a miss (and a lost game)",
          r["react"] == ["perfect", "great", "pass", "fail", "fail"], r["react"])
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
        return { rows: rows.map(r => r.dataset.value), descs: rows.every(r => (r.querySelector('.bank-desc').textContent || '').length > 12),
                 info: !!document.querySelector('.bank-opt[data-value="recent"] .bank-info'),
                 label: (document.querySelector('.bank-sect .slab') || {}).textContent }; });
      document.querySelector('.bank-opt[data-value="recent"]')?.click(); await wait(200);
      cfg.timer = 'down'; cfg.timerMinutes = 20; document.querySelector('.bank-opt[data-value="recent"]')?.click(); await wait(200);
      await T('tags', () => [...document.querySelectorAll('.sheet-summary-tags .sheet-tag')].map(t => t.textContent));
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
      document.querySelector('.unitdetail-door.is-recent')?.click(); await wait(600);
      await T('list', () => ({ qs: document.querySelectorAll('.unitdetail-list .unitdetail-q').length,
                               flags: document.querySelectorAll('.unitdetail-list .unitdetail-flag').length }));
      document.querySelector('.unitdetail-list .unitdetail-flag')?.click();
      await T('flagged', () => flaggedIndexes().length);
      document.querySelector('.unitdetail-back')?.click(); await wait(500);
      document.querySelector('.unitdetail-scrim')?.click(); await wait(700);
      await T('closed', () => !document.querySelector('.unitdetail') && !document.querySelector('.unitdetail-scrim'));
      return out; }""")
    p = r["pitch"] if isinstance(r["pitch"], dict) else {}
    check("every stretch of road on the map is the same length", p.get("max", 99) - p.get("min", 0) <= 2 and p.get("min", 0) > 150, r["pitch"])
    check("on a phone the ranks sit either side of the road, like the iPad", r["sides"] == "LRLRLRL", r["sides"])
    cp = r["cap"] if isinstance(r["cap"], dict) else {}
    check("Most missed keeps at most 15% of a unit", cp.get("got") == cp.get("cap") and cp.get("got", 99) < cp.get("n", 0), r["cap"])
    check("no best time on the unit cards", r["noBest"] == 0, r["noBest"])
    check("the unit screen says a card can be held", r["hint"] is True, r["hint"])
    b = r["bank"] if isinstance(r["bank"], dict) else {}
    check("the Question bank: three rows that each say what they draw, and an info dot on Most missed",
          b.get("rows") == ["all", "recent", "flagged"] and b.get("descs") and b.get("info") and b.get("label") == "Question bank", b)
    t = r["tags"] if isinstance(r["tags"], list) else []
    check("the top box says the bank and the timer without opening anything",
          "Most missed" in t and "20 min limit" in t, t)
    check("the timer row says what is in it", "Time limit" in str(r["timerLabel"]) and "stopwatch" in str(r["timerLabel"]).lower(), r["timerLabel"])
    d = r["detail"] if isinstance(r["detail"], dict) else {}
    check("holding a unit card opens its details without ticking it",
          d.get("unticked") is True and d.get("doors") == 2 and "Completed" in d.get("stats", []) and "Best time" in d.get("stats", [])
          and "Hundos" in d.get("stats", []) and d.get("w", 0) > 300, r["detail"])
    l = r["list"] if isinstance(r["list"], dict) else {}
    check("Most missed opens inside the card, each question with its flag", l.get("qs", 0) >= 1 and l.get("qs") == l.get("flags"), r["list"])
    check("a question can be flagged from there", isinstance(r["flagged"], int) and r["flagged"] >= 1, r["flagged"])
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
      await T('panels', () => ['zeus', 'poseidon'].map(k => [...buildAvatarCharSVGSafe(k).querySelectorAll('rect')]
        .some(x => /^#(13263A|0C2E30)$/i.test(x.getAttribute('fill') || ''))));
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
      document.querySelector('.unitdetail-door.is-recent')?.click(); await wait(700);
      await T('clearMissed', async () => { const before = recentMissedIndexes().filter(i => (QUESTIONS[i].topic || '').trim() === unit).length;
        document.querySelector('.unitdetail-resetbtn')?.click(); await wait(100);
        document.querySelector('.unitdetail-confirmyes')?.click(); await wait(200);
        return { before, after: recentMissedIndexes().filter(i => (QUESTIONS[i].topic || '').trim() === unit).length }; });
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
    check("Zeus and Poseidon's symbols sit on a dark carved panel", r["panels"] == [True, True], r["panels"])
    cp = r["copy"] if isinstance(r["copy"], dict) else {}
    check("the doors say what they open, and Hundos says nothing about the badge",
          cp.get("doors") == ["Tap to see flagged questions", "Tap to see most missed"]
          and "badge" not in (cp.get("hundoSub") or "").lower(), r["copy"])
    l = r["list"] if isinstance(r["list"], dict) else {}
    check("the list drops the badge bar, has a search, and the in-test flag",
          l.get("listing") and l.get("barHidden") and l.get("search") and l.get("testFlag") and l.get("qs") == 3, r["list"])
    check("search filters and Clear brings everything back", r["search"] == {"none": 0, "back": 3}, r["search"])
    rs = r["reset"] if isinstance(r["reset"], dict) else {}
    check("unflagging the unit asks first, then does it", rs.get("warned") and rs.get("before", 0) >= 3 and rs.get("after") == 0, r["reset"])
    cm = r["clearMissed"] if isinstance(r["clearMissed"], dict) else {}
    check("clearing a unit's most missed empties it", cm.get("before", 0) > 0 and cm.get("after") == 0, r["clearMissed"])
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
    check("it names the rank and how far to the next one", isinstance(r, dict) and r.get("word") == "Gold"
          and "Platinum" in str(r.get("next")) and "%" in str(r.get("next")) and r.get("fill", 0) > 0, r)
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
    check("Drill's best time says a hundo sets it, set or not", isinstance(r, dict)
          and "hundo" in str(r.get("unset")) and "hundo" in str(r.get("set")), r)
    # Build 240 took the time off Exam altogether ("Best exam" and "Exam
    # average" instead), so the hundo wording is only asserted where a time
    # is still shown. A decision that changed, not a regression.
    check("Exam no longer shows a time at all", isinstance(r, dict) and "Best exam" in str(r.get("exam"))
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
      ['drill','exam','game','review','vroom'].forEach(m => out.modes[m] = labs(m));
      store.gameBeat = store.gameBeat || {};
      const saveBeat = JSON.stringify(gameBeat(u));
      store.gameFarthest[u] = { easy: 7 };
      out.gameEasy = unitDetailStats(u, 'game').map(x => x.label + '=' + x.value);
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
    check("every mode has four squares", modes and all(len(v) == 4 for v in modes.values()), modes)
    check("every mode starts with Completed and ends with Hundos",
          modes and all(f == "Completed" for f in firsts.values()) and all(l == "Hundos" for l in lasts.values()), modes)
    check("Game shows no best time unless Hardcore is beaten",
          modes.get("game") and not any("time" in x.lower() for x in modes["game"]), modes.get("game"))
    ge = " | ".join(r.get("gameEasy", [])) if isinstance(r, dict) else ""
    check("Game shows the level unlocked and how far you got on it",
          "Level unlocked=" in ge and "Farthest on " in ge and "7 / " in ge, ge)
    ex = " | ".join(r.get("exam", [])) if isinstance(r, dict) else ""
    check("Exam shows its best and its average from past exams",
          "Best exam=80%" in ex and "Exam average=70%" in ex, ex)
    # The header names the mode: open a real card on the Exam unit grid.
    pg.evaluate("()=>{ cfg.mode = 'exam'; cfg.units = []; showSetup(); }")
    pg.wait_for_timeout(700)
    chip = pg.evaluate("""()=>{ const row = document.querySelector('.pick');
      if(!row) return 'no row';
      row.dispatchEvent(new MouseEvent('contextmenu', {bubbles:true, cancelable:true}));
      const c = document.querySelector('.unitdetail-mode'); return c ? c.textContent : 'no chip'; }""")
    check("the details card names the mode it is for", chip == "Exam", chip)
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
      out.plates = document.querySelectorAll('.profile-statplate').length;
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
    check("Profile: one level plate, and badges are their own section of every unit",
          isinstance(r, dict) and r.get("plates") == 1 and r.get("badgeCells") == 0 and r.get("badgeEarned") == 6, r)
    def hexrgb(h):
        h = h.lstrip("#"); return "rgb(%d, %d, %d)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    check("the rank bar is the rank's own colour, not a blend into the next",
          isinstance(r, dict) and r.get("fillBg") and hexrgb(r.get("nextColor", "#000000")) not in r.get("fillBg", ""), r)
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
      /* 2. seven different units in one day, and only different ones */
      const units = topicsIn(QUESTIONS);
      for(let i = 0; i < 6; i++) noteHundoDay(units[i]);
      noteHundoDay(units[0]); noteHundoDay(units[1]);
      out.sixDistinct = hundoDayCount();
      out.lockedAtSix = isLockedCharacter('astronaut');
      /* a new day starts the list again but keeps the best day */
      store.hundoDay.day = '2000-01-01';
      noteHundoDay(units[6]);
      out.newDay = { today: store.hundoDay.units.length, best: store.hundoDayBest, locked: isLockedCharacter('astronaut') };
      for(let i = 0; i < 7; i++) noteHundoDay(units[i]);
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
      out.corona = (svg.querySelector('.cx-fig').getAttribute('class') || '').indexOf('cx-k-astronaut') >= 0 ? 7 : 0;
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
    check("the Astronaut (Blitz's challenge since 243) sits right after the Marksman, locked, with its challenge and progress",
          isinstance(r, dict) and r.get("blitzAt") == 1 and r.get("lockedAtStart") is True
          and r.get("msg") == "Get a hundo in 7 different units in one day (0 of 7) to unlock Astronaut.", r)
    check("only different units count, and six is not seven",
          r.get("sixDistinct") == 6 and r.get("lockedAtSix") is True, r)
    check("a new day starts again but keeps the best day",
          r.get("newDay") == {"today": 1, "best": 6, "locked": True}, r)
    check("seven in one day unlocks it, and the best day survives a reload",
          r.get("lockedAtSeven") is False and r.get("afterLoad") == 7, r)
    check("an old Blitz id draws as the Astronaut, on the parts every character has",
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
        medal: (document.querySelector('.badges-head .badges-medal-num') || {}).textContent || '',
        lid: !!document.querySelector('.badge-case .badge-case-lid .badge-case-plate'),
        clasps: document.querySelectorAll('.badge-case .badge-case-front span').length };
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
    check("Profile shows the count and the six badges held, with no meter and not the whole set",
          p.get("strip") == 0 and p.get("segs") == 0 and p.get("stack") == 6, p)
    rb = r.get("rankBox") or {}
    # REVERSED IN 243: "the profile box got worse somehow ... it was so
    # good before" - back to the 241 plate: one bar and "Gold · 35%".
    check("the rank plate is the 241 one: a bar and the next rank's name and share, no chip",
          rb.get("bar") and not rb.get("chip") and not rb.get("need") and "%" in rb.get("label", ""), rb)
    bt = r.get("badgesTab") or {}
    # REVERSED IN 243: the meter was "terrible, all I wanted was a better
    # way to show it than the 0/16" - a medal with the number in it.
    check("the Badges tab heads with a medal, no meter, and sits in a case with a lid and two clasps",
          bt.get("strip") == 0 and bt.get("segs") == 0 and bt.get("medal") == "6" and bt.get("lid") and bt.get("clasps") == 2, bt)
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
      out.ladders = { first: ['easy10', 'tests100', 'hundos100', 'adept_rank'].map(still),
        rest: ['average10', 'hardcore10', 'tests250', 'tests500', 'hundos250', 'elite_rank', 'titan_rank'].map(still) };
      /* build 244: Hall of Fame is a ring of the badges round a medal, drawn
         twice (behind and in front of it) - so count the distinct badges. */
      out.hallBadges = new Set([...buildBannerArt('badges16').querySelectorAll('[data-u]')].map(e => e.dataset.u)).size;
      out.bannerNames = ['badges16', 'level80', 'study50', 'correct5000'].map(id => (bannerDef(id) || {}).name);
      /* build 244: the two new banners count what they say, from what is already kept. */
      const wasLife = store.lifetime.correct, wasLog = store.studyLog;
      store.lifetime.correct = 4999; const c1 = bannerEarned('correct5000');
      store.lifetime.correct = 5000; const c2 = bannerEarned('correct5000');
      store.studyLog = { '2026-01-01': 49.9 * 3600000 }; const s1 = bannerEarned('study50');
      store.studyLog = { '2026-01-01': 30 * 3600000, '2026-01-02': 20 * 3600000 }; const s2 = bannerEarned('study50');
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
    check("the Clown is five wins, the Astronaut seven hundos, the Hacker time studied, the Timekeeper days studied, the Valkyrie ten wins, and SWAT is retired (build 245)",
          r.get("feats") == {"clown": "vrwins5", "astronaut": "hundo7day", "hacker": "study20h", "timekeeper": "days30",
                             "valkyrie": "vrwins10", "swatRetired": True}, r.get("feats"))
    check("every retired character is drawn as what replaced it",
          r.get("retiredTo") == ["ninja", "clown", "astronaut", "solar", "oracle", "valkyrie", "hacker", "solar", "tempest", "valkyrie", "hacker", "timekeeper", "ninja"], r.get("retiredTo"))
    check("the new ones are named", r.get("names") == ["Lunar", "Solar", "Tempest", "Frost", "Oracle", "Inferno", "Hacker", "Timekeeper", "Valkyrie"], r.get("names"))
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
          lad.get("first") == [True, True, True, False] and lad.get("rest") == [False] * 7, lad)
    check("the all-badges banner is the sixteen badges", r.get("hallBadges") == 16, r.get("hallBadges"))
    check("the redone and new banners are named", r.get("bannerNames") == ["Hall of Fame", "Ascension", "Midnight Oil", "Star Trails"], r.get("bannerNames"))
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
      showProfile('profile'); await wait(900); document.getAnimations().forEach(a => a.pause());
      const coin = document.querySelector('.profile-rankplate .profile-rankcoin'), held = rankOf(store) || rankStepProgress().next;
      out.coin = coin ? { fitted: coin.querySelector('svg').classList.contains('is-fitted'), off: off(coin, coin.querySelector('svg'), held) } : null;
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
      return { text: t.textContent, passesTap: !!hit && c.contains(hit) && !t.contains(hit) }; }""")
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
    sheet = pg.evaluate("""()=>{ document.getElementById('nextbtn').click();
      const line = document.querySelector('.sheet-summary-line'), note = document.querySelector('.hundo-note');
      return { line: line ? line.textContent : '', start: document.getElementById('nextbtn').textContent,
               note: note && !note.hidden ? note.textContent : '' }; }""")
    n56 = "%d questions" % len(PENAL_SLIDES_SRCS)
    check("the start sheet and the Start button count the slides 0-85 questions",
          n56 in sheet["line"] and n56 in sheet["start"], sheet)
    check("the start sheet says it won't count toward a hundo, in its existing words",
          sheet["note"] == "Not the whole unit, so this run won't count toward a hundo.", sheet["note"])
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
    check("with another unit, the note names the Penal Code's slides and says the others still count",
          "Penal Code (slides 0\u201385)" in mix["note"] and "other units still can" in mix["note"]
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
      t.click(); await wait(500);
      const p = document.getElementById('contextual-info-popup');
      const pr = p ? p.getBoundingClientRect() : null;
      return { tile: [Math.round(tr.top), Math.round(tr.bottom)], barTop: Math.round(bar.top),
        popup: pr ? [Math.round(pr.top), Math.round(pr.bottom)] : null };
    }""")
    check("a badge pop-up near the bottom never covers the tab bar",
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
    Review has to share a row with Game, under Drill and Exam."""
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
              sorted(kinds) == sorted(["drill", "exam", "review", "game", "vroom"]), kinds)
        if w >= 640 and len(r) == 5:
            check("%s: the grid reads Drill Exam / Review Game / Virtual Room" % label,
                  r[0]["top"] == r[1]["top"] and r[2]["top"] == r[3]["top"] > r[0]["top"]
                  and r[2]["left"] < r[3]["left"] and r[4]["top"] > r[2]["top"], r)
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
    """37. "On the main menu of the app, could put another slogan somewhere
    maybe, calling this 'the study game'". It is there, between NOVA and
    the tagline - and Start Studying does not move by a pixel for it: the
    button is measured with the slogan in place and again with the slogan
    and its lift taken out, which is the page as it was before. The short
    viewport tiers drop it, like the tagline one tier further down."""
    print("\n37. build 245: THE STUDY GAME on Home, and Start Studying unmoved")
    sizes = [(440, 956), (834, 1194), (375, 667), (375, 812), (393, 852), (360, 800),
             (1024, 1366), (1728, 987), (1512, 722), (1194, 834), (956, 440)]
    for w, h in sizes:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ showHome(); await new Promise(r => setTimeout(r, 1500));
          const R = e => { const b = e.getBoundingClientRect(); return { t: b.top, b: b.bottom, l: b.left, r: b.right, h: b.height }; };
          const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
          const btn = () => R(document.getElementById('nextbtn'));
          const settle = async () => { let a = btn(); for(let i = 0; i < 30; i++){ await frame(); const b = btn(); if(Math.abs(b.t - a.t) < .05) return b; a = b; } return a; };
          await settle();
          const s = [...document.querySelectorAll('.panel.home *')].find(e => /study game/i.test(e.textContent || '') && e.children.length === 0);
          const shown = !!s && getComputedStyle(s).display !== 'none' && s.getBoundingClientRect().height > 0;
          const out = { shown, with: await settle(), tag: R(document.querySelector('.hometagline')) };
          if(s){ out.s = R(s); out.title = R(document.querySelector('.hometitle'));
                 out.greet = R(document.querySelector('.homegreeting')); }
          const panel = document.querySelector('.panel.home');
          if(s){ s.remove(); panel.style.setProperty('--slogan-lift', '0px'); }
          out.without = await settle(); out.tag0 = R(document.querySelector('.hometagline'));
          return out; }""")
        tag = "%dx%d" % (w, h)
        short = h <= 800 and w >= 544 or h <= 608
        if not short:
            check("%s: the slogan is on Home" % tag, r["shown"])
        if r.get("shown"):
            check("%s: it sits between NOVA and the tagline, touching neither" % tag,
                  r["title"]["b"] <= r["s"]["t"] + 0.5 and r["s"]["b"] <= r["tag"]["t"] + 0.5,
                  [r["title"], r["s"], r["tag"]])
            check("%s: and the greeting still clears NOVA" % tag, r["greet"]["b"] <= r["title"]["t"] + 0.5)
        check("%s: Start Studying does not move for it" % tag,
              abs(r["with"]["t"] - r["without"]["t"]) < 0.6 and abs(r["tag"]["b"] - r["tag0"]["b"]) < 0.6,
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
        r = pg.evaluate(DAILY_SAMPLER, {"ms": 9800, "reduce": False})
        fr = r["frames"]
        charge = next((f["t"] for f in fr if f["charging"]), None)
        closed = next((f["t"] for f in fr if f["arcL"] is not None and abs(f["arcL"]) >= 170), None)
        shown = next((f["t"] for f in fr if f["op"] > 0.5), None)
        orbs = [f for f in fr if f["orb"]]
        check("%s: the button starts charging as Home appears" % label, charge is not None and charge < 1000, charge)
        check("%s: the ring closes round it (a full turn)" % label, closed is not None, closed)
        check("%s: the banner follows the recharge, 2-3.5s in" % label,
              shown is not None and closed is not None and shown >= closed and 2000 <= shown <= 3500,
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
    pg.wait_for_timeout(4800)
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
      const set = (st, h) => { store.lifetime.longestStreak = st; store.studyLog = { '2026-09-01': h * H }; };
      set(149, 24.9); out.under = [isLockedCharacter('marksman'), isLockedCharacter('hacker')];
      set(150, 25); out.at = [isLockedCharacter('marksman'), isLockedCharacter('hacker')];
      const d = JSON.parse(JSON.stringify(store)); d.avatarChar = 'hacker'; d.studyLog = { '2026-09-01': 22 * H };
      d.lifetime.longestStreak = 120; d.pendingCharUnlocks = ['marksman', 'clown'];
      applyLoadedData(d); out.revoked = [store.avatarChar, store.pendingCharUnlocks.slice()];
      const e = JSON.parse(JSON.stringify(store)); e.avatarChar = 'marksman'; e.lifetime.longestStreak = 160;
      e.studyLog = { '2026-09-01': 30 * H }; e.pendingCharUnlocks = ['hacker'];
      applyLoadedData(e); out.kept = [store.avatarChar, store.pendingCharUnlocks.slice()];
      return out; }""")
    check("the Marksman needs 150 in a row and the Hacker 25 hours", r["under"] == [True, True] and r["at"] == [False, False], r)
    check("under the new bar, the character comes off whoever is wearing it and its announcement is dropped",
          r["revoked"][0] not in ("hacker", "marksman") and r["revoked"][1] == ["clown"], r["revoked"])
    check("at or over it, nothing is taken", r["kept"] == ["marksman", ["hacker"]], r["kept"])
    # 43. Madison's list after 245, on a real Home.
    t = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      store.legacyChars = []; store.avatarChar = 'ninja';
      for(const id of ['bottomtab-ranks', 'bottomtab-rewards', 'bottomtab-profile', 'bottomtab-settings']){
        showHome(); await wait(600);
        const before = document.querySelector('#stage > *');
        document.getElementById(id).click(); await wait(700);
        const now = document.querySelector('#stage > *');
        out[id] = !!now && now !== before && !now.classList.contains('screen-home-actual');
      }
      out.ranksScreen = (showHome(), await wait(500), document.getElementById('bottomtab-ranks').click(), await wait(700),
                         !!document.querySelector('.screen-ranks'));
      out.hiddenArt = ['umbra', 'singularity'].map(id => !!characterDetail(id).hideArt);
      out.animated = ['adept_rank', 'elite_rank', 'titan_rank'].map(id => !buildBannerArt(id).classList.contains('is-still'));
      showCustomize(); await wait(900);
      out.needs = BANNERS.filter(b => !b.secret).map(b => { const o = document.querySelector('.banner-opt[data-banner="' + b.id + '"] .banner-opt-need');
        return !!o && o.textContent === b.label; });
      return out; }""")
    check("every tab on the bar opens its screen when TAPPED, Ranks included",
          all(t[k] for k in ("bottomtab-ranks", "bottomtab-rewards", "bottomtab-profile", "bottomtab-settings")) and t["ranksScreen"], t)
    check("Umbra and Singularity are drawn in their pop-ups, not blacked out", t["hiddenArt"] == [False, False], t["hiddenArt"])
    check("all three rank banners animate", t["animated"] == [True, True, True], t["animated"])
    check("every banner in Customize says what it takes, under it", len(t["needs"]) > 10 and all(t["needs"]), t["needs"])
    ctx.close()


B245_POLISH = ["modes", "daily_schedule", "slogan", "bugreport", "daily_announce", "start_pill", "daily_header"]


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
        finally:
            br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))"
          % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES),
             len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
