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
    '"longestStreak":57},'
    # An up-to-date account has had its unlock pop-ups: the record the
    # app would seed for it, with the hundo effects (build 313) marked
    # shown too, so no section is met by their Home pop-ups.
    '"unlocksShown":{"chars":[],"banners":["hundos100"],"fx":["fireworks","blackhole","underwater","worldtree","bubbles","ufo"]}}')

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
        ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');"
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
    # Build 299 took the Rank/Badges switcher off: "when clicking rank, or
    # badges, there's a tab at the top for both as well, remove that".
    check("an old link to Profile's rank tab lands on the Rank screen, with no switcher on it",
          tabs["screen"] and len(tabs["rendered"]) == 0 and tabs["swipe"] == ["ranks", "badges"], tabs)
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
    # Build 314: the top card shows the next rank's challenges, so no road
    # map card carries a meter any more - "Up next" keeps its chip.
    check("no road map card carries a meter (the top card has the challenges)",
          [c["meter"] for c in cards] == [False] * 7, [c["meter"] for c in cards])
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

      /* THE RESULTS SCREEN IS A BLOCK, HOWEVER LONG IT IS UP (build 298).
         It was a few seconds of grace and then the update went - which is
         "an update push at the end of a test", reported as something that
         must never happen. Re-read with the decision. */
      const panel = document.createElement('section');
      panel.className = 'panel rs-screen'; panel.dataset.screen = 'results';
      stage.replaceChildren(panel);
      resultsShownAt = Date.now();
      out.justFinished = forcedUpdateBlocked();
      resultsShownAt = Date.now() - 10 * 60 * 1000;
      out.afterReview = forcedUpdateBlocked();
      /* every Virtual Room screen, and the test's own leaderboard */
      out.vroom = ['vroom-results-panel', 'vroom-finale-panel rs-screen', 'screen-vroom-lobby', 'screen-vroom-choice',
                   'screen-rooms', 'screen-tug', 'screen-tug-result', 'screen-battle-result', 'qpanel', 'pausepanel']
        .filter(c => { mkScreen(c); return !forcedUpdateBlocked(); });
      mkScreen('screen-rankings'); out.rankings = forcedUpdateBlocked();

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
    # "UPDATES can not happen during a test, in the result screen, test
    # leaderboard, virtual room lobby or anything like that" (build 298)
    check("never on the results screen",
          got["justFinished"] is True, got["justFinished"])
    check("not even ten minutes after the results came up",
          got["afterReview"] is True, got["afterReview"])
    check("nor on any Virtual Room screen, a question or Pause",
          got["vroom"] == [], got["vroom"])
    check("but the Leaderboard tab still takes it",
          got["rankings"] is False, got["rankings"])

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
        /* the app's own check may still be out (build 301 lets the
           poll and screen changes really ask); this one is the test */
        try{ updateCheckInFlight = 0; }catch(e){}
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
    """THE POLL HAS TO ACTUALLY ASK, AND SO DOES COMING BACK (build 301).
    "Why aren't the updates pushing when I open the app?" The 15-second
    poll above was real and was asserted - by reading UPDATE_POLL_MS -
    and every one of its calls was turned away by a 15-minute gap that
    every trigger shared. A check that reads a constant cannot see a
    second constant overruling it. So this one counts the requests that
    actually go out: a check made a minute ago must not stop the poll,
    and one made two seconds ago must not stop coming back to the app."""
    asks = pg.evaluate("""async ()=>{
      const out = {};
      const real = window.fetch; let n = 0;
      window.fetch = (u, o) => { if(String(u).indexOf('version.json') >= 0){ n++;
        return Promise.resolve({ ok:true, json: () => Promise.resolve({ build: APP_BUILD }) }); }
        return real(u, o); };
      try{
        document.querySelectorAll('.update-banner, #pushing-update').forEach(x => x.remove());
        await new Promise(r => setTimeout(r, 50));
        try{ updateCheckInFlight = 0; }catch(e){}
        lastUpdateCheck = Date.now() - 60 * 1000; n = 0;
        await checkForUpdate();                       /* what the poll calls */
        await new Promise(r => setTimeout(r, 50));
        out.poll = n;
        lastUpdateCheck = Date.now() - 2000; n = 0;
        document.dispatchEvent(new Event('visibilitychange'));
        await new Promise(r => setTimeout(r, 120));
        out.resume = n;
        lastUpdateCheck = Date.now() - 1000; n = 0;
        await checkForUpdate();                       /* a burst of screen changes */
        await checkForUpdate();
        out.burst = n;
      } finally { window.fetch = real; }
      return out; }""")
    check("the poll asks for real: a check a minute ago does not turn it away",
          asks.get("poll") == 1, asks)
    check("coming back to the app always asks, even seconds after the last check",
          asks.get("resume") == 1, asks)
    check("but a burst of screen changes does not fire a burst of requests",
          asks.get("burst") == 0, asks)
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
    print("\n8. the next question pushes in cleanly, and then stops")
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
          /* BUILD 311: A PUSH. "I see the next question as the old one is
             going away" - so both ARE on screen together now, side by side.
             What must stay true is the thing 296 was guarding: they are
             never drawn over each other. That is geometry again (the
             docstring above said so: the right test for a slide), plus
             that the two really do share the screen for some frames. */
          let overlap=0, frames=0, both=0, sawOut=false, sawIn=false, hScroll=0;
          for(let i=0;i<50;i++){
            await new Promise(r=>requestAnimationFrame(r));
            const c=document.querySelector('body > .panel');
            const n=document.querySelector('#stage > .panel');
            if(!c||!n) break;
            const oc=+getComputedStyle(c).opacity, on=+getComputedStyle(n).opacity;
            const rc=c.getBoundingClientRect(), rn=n.getBoundingClientRect();
            if(oc > .9) sawOut = true;
            if(on > .9) sawIn = true;
            const inView = r => r.right > 4 && r.left < innerWidth - 4;
            if(oc > .15 && on > .15 && inView(rc) && inView(rn)){
              both++;
              overlap = Math.max(overlap, Math.min(rc.right, rn.right) - Math.max(rc.left, rn.left));
            }
            hScroll = Math.max(hScroll, document.documentElement.scrollWidth - document.documentElement.clientWidth);
            frames++;
            if(sawIn && rn.left <= 1 && rn.left >= -1 && Math.abs(rc.right) < 1e6 && rc.right <= 0) break;
          }
          return { overlap: Math.round(overlap), both, frames, sawOut, sawIn, hScroll }; }""")
        check("%s the two questions share the screen side by side, never drawn over each other" % label,
              worst["frames"] > 3 and worst["sawOut"] and worst["sawIn"] and worst["both"] >= 2
              and worst["overlap"] <= 2, worst)
        check("%s and the page never scrolls sideways while the next one pushes in" % label,
              worst["hScroll"] <= 0, worst)
        ctx.close()


def check_b313_qmotion(br):
    """Build 313: the star stops shouting, and the next question visibly
    moves. "The color of the star is kinda harsh ... it kinda catches your
    eye" and "it's hard to tell that the question is literally moving".
    Written against 312, where the star is saturated gold unstarred, the
    outgoing question fades to 40% as it goes, and a drag does nothing
    until the finger lifts."""
    print("\n95. build 313: a quiet star, a solid slide, a question that follows the thumb")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True)
    pg.evaluate("""()=>{ cfg.units=[topicsIn(QUESTIONS)[0]]; cfg.mode='drill'; cfg.size=12; cfg.source='all';
      const u=topicsIn(QUESTIONS)[0], idx=[]; QUESTIONS.forEach((q,i)=>{ if(q.topic===u && idx.length<12) idx.push(i); });
      beginRun(idx); }""")
    pg.wait_for_selector(".choice", timeout=20000)
    pg.wait_for_timeout(700)
    star = pg.evaluate("""()=>{ const l=document.querySelector('.qpanel .flagbtn:not(.on) .starline');
      if(!l) return null; const c=getComputedStyle(l).stroke.match(/[\\d.]+/g).map(Number);
      return { stroke: getComputedStyle(l).stroke, spread: Math.max(c[0],c[1],c[2]) - Math.min(c[0],c[1],c[2]) }; }""")
    check("an unstarred question's star is the soft white of the rest of the chrome, not gold",
          bool(star) and star["spread"] <= 24, star)
    _answer(pg)
    pg.wait_for_timeout(600)
    mid = pg.evaluate("""async ()=>{ advanceWithSlide(); const out=[];
      for(let i=0;i<30;i++){ await new Promise(r=>requestAnimationFrame(r));
        const c=document.querySelector('body > .panel'); if(!c) break;
        const r=c.getBoundingClientRect(); out.push({ op:+getComputedStyle(c).opacity, x:Math.round(r.left) }); }
      return out; }""")
    halfway = [f for f in mid if f["x"] < -150]
    check("the outgoing question is still solid a third of the way off",
          bool(halfway) and halfway[0]["op"] >= .9, (halfway[:2], len(mid)))
    pg.wait_for_timeout(600)
    _answer(pg)
    pg.wait_for_timeout(600)
    drag = pg.evaluate("""async ()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
      const p=document.querySelector('#stage > .panel'); const x0=p.getBoundingClientRect().left;
      const T=(x,y)=>new Touch({identifier:7, target:p, clientX:x, clientY:y});
      const fire=(type,x,y)=>{ const t=T(x,y); p.dispatchEvent(new TouchEvent(type,{bubbles:true,cancelable:true,
        touches: type==='touchend'?[]:[t], targetTouches: type==='touchend'?[]:[t], changedTouches:[t]})); };
      const q0=pos;
      fire('touchstart', 330, 600); await wait(16);
      fire('touchmove', 300, 602); await wait(16); fire('touchmove', 250, 603); await wait(32);
      const during = Math.round(p.getBoundingClientRect().left - x0);
      const pair = document.querySelector('.q-blurpair');
      const pv = pair ? { n: (pair.querySelector('.qnum')||{}).textContent, sharp: +pair.children[1].style.opacity,
        blur: getComputedStyle(pair.children[0]).filter } : null;
      fire('touchmove', 150, 603); await wait(32);
      const pv2 = pair ? +pair.children[1].style.opacity : null;
      fire('touchmove', 250, 603); await wait(16);
      fire('touchmove', 300, 603); await wait(16); fire('touchend', 318, 603); await wait(400);
      const back = { x: Math.round(p.getBoundingClientRect().left - x0), pos: pos === q0 };
      fire('touchstart', 330, 600); await wait(16);
      fire('touchmove', 280, 602); await wait(16); fire('touchmove', 200, 603); await wait(16);
      fire('touchend', 200, 603); await wait(500);
      return { during, back, advanced: pos !== q0, clone: !!document.querySelector('body > .panel'), pv, pv2,
               left: document.querySelectorAll('.q-blurpair').length, want: 'Question ' + (q0 + 2) }; }""")
    check("dragging sideways moves the question with the thumb", drag["during"] <= -60, drag)
    check("let go short of the line, it springs back and stays on the question",
          abs(drag["back"]["x"]) <= 1 and drag["back"]["pos"], drag)
    check("let go past it, the next question comes in", drag["advanced"] and not drag["clone"], drag)
    pv = drag.get("pv") or {}
    # REVISED IN 314: "even at the halfway point it should still be hard
    # to read" - nothing of the sharp copy shows during a drag at all now
    # (it sharpened from the first pixel in 313). Section 99 holds the
    # rest of the new swipe.
    check("mid-drag the next question is already there, out of focus, and stays out of focus",
          pv.get("n") == drag.get("want") and "blur" in (pv.get("blur") or "") and pv.get("sharp", 1) == 0
          and (drag.get("pv2") if drag.get("pv2") is not None else 1) == 0 and drag.get("left") == 0, drag)
    ctx.close()


def check_b313_notice(br):
    """Build 313: the update notice on Home ran under the chat button (its
    own close button hidden beneath it) and over the top flare bubble -
    13px on a 17 Pro Max, 30px on an SE. Now it stops short of the chat
    button and the planet system slides down to clear it, and back when
    it goes. Fails on 312."""
    print("\n98. build 313: the update notice clears the chat button and the planet")
    out = {}
    for (w, h, tag) in [(440, 956, "pro max"), (375, 667, "se")]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        out[tag] = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          try{ markUnlocksShown(AVATAR_CHARACTERS.map(c=>c.id), BANNERS.map(b=>b.id)); }catch(e){}
          store.flareHintsShown = ['umbra','singularity','genesis']; store.hundoFxShown = Object.assign({}, store.hundoFxShown || {}); saveStore();
          showHome(); await wait(900);
          for(let i = 0; i < 12 && document.querySelector('.rs-spot'); i++){ document.querySelector('.rs-spot').click(); await wait(1100); }
          const hero = () => document.querySelector('#stage .cosmic-hero-wrap');
          const top = () => { let t = hero().getBoundingClientRect().top; hero().querySelectorAll('.cosmic-badge').forEach(e => { const r = e.getBoundingClientRect(); if(r.width > 0) t = Math.min(t, r.top); }); return t; };
          const before = top();
          showUpdateBanner('2099-01-01-999'); await wait(1400);
          const bar = document.getElementById('updatebanner').getBoundingClientRect();
          const chat = document.querySelector('.chatdock-btn').getBoundingClientRect();
          const hit = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
          const res = { chatHit: hit(bar, chat), bubbleGap: Math.round(top() - bar.bottom),
            closeVisible: (() => { const c = document.querySelector('#updatebanner .update-banner-close, #updatebanner button[aria-label*="lose"]'); if(!c) return null; const r = c.getBoundingClientRect(); return !hit(r, chat); })() };
          hideBanner(); await wait(900);
          res.back = Math.round(top() - before);
          const greet = document.querySelector('.hometitle-wrap, .homegreet');
          res.greetClear = greet ? Math.round(greet.getBoundingClientRect().top - hero().getBoundingClientRect().bottom) : null;
          return res; }""")
        ctx.close()
    for tag, r in out.items():
        check("%s: the notice does not run under the chat button" % tag, r.get("chatHit") is False and r.get("closeVisible") is not False, r)
        check("%s: and it clears the top flare bubble" % tag, isinstance(r.get("bubbleGap"), int) and r["bubbleGap"] >= 4, r)
        check("%s: the planet goes back when the notice goes" % tag, r.get("back") == 0, r)


def check_b314_nova(br):
    """Build 314: "Could the supernova have a little more black? Like maybe
    black shooting out? In fragmented pieces?" Measured on a live Rank hero
    emblem: at least ten separate black pieces, each moving OUTWARD from the
    centre over the detonation (not spinning in place), fading out at the
    far end, and held mid-flight - away from the core - when motion is off.
    Written against 313, where there are no such pieces."""
    print("\n314n. build 314: the Supernova throws black out in fragments")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    m = pg.evaluate("""()=>{ const host = document.createElement('div'); host.className = 'rankhero-art';
      host.style.cssText = 'position:fixed;left:0;top:0;width:256px;height:256px'; document.body.appendChild(host);
      const s = buildRankEmblemSVG('titan'); host.replaceChildren(s); s.classList.remove('rk-idle');
      const frags = [...s.querySelectorAll('.rk-nova-frag')];
      const hb = host.getBoundingClientRect(), cx = hb.left + hb.width / 2, cy = hb.top + hb.height / 2;
      const at = t => frags.map(g => { g.getAnimations().forEach(a => { a.pause(); a.currentTime = t; });
        const r = g.getBoundingClientRect(); return { d: Math.hypot(r.left + r.width / 2 - cx, r.top + r.height / 2 - cy), o: parseFloat(getComputedStyle(g).opacity) }; });
      const black = frags.every(g => [...g.querySelectorAll('path')].some(p => /^#0[0-9]0/.test(p.getAttribute('fill') || '')));
      const early = at(200), late = at(2200), gone = at(2700);
      frags.forEach(g => g.style.animation = 'none');
      const still = frags.map(g => { const r = g.getBoundingClientRect(); return Math.hypot(r.left + r.width / 2 - cx, r.top + r.height / 2 - cy); });
      return { n: frags.length, black, out: early.map((e, i) => late[i].d - e.d), fade: gone.map(x => x.o), seen: early.map(x => x.o),
               still, size: hb.width }; }""")
    check("Supernova has at least ten black fragments", m["n"] >= 10 and m["black"], {k: m[k] for k in ("n", "black")})
    check("every fragment flies outward over the blast (by more than a sixth of the emblem)",
          m["n"] >= 10 and min(m["out"]) > m["size"] / 6, [round(x) for x in m["out"]])
    check("they are visible as they leave and burnt out by the end of the beat",
          m["n"] >= 10 and min(m["seen"]) > .5 and max(m["fade"]) < .05, {"seen": m["seen"][:4], "fade": m["fade"][:4]})
    check("with motion off they hold mid-flight, clear of the core",
          m["n"] >= 10 and min(m["still"]) > m["size"] * .2, [round(x) for x in m["still"]])
    ctx.close()


def check_b313_shuffle(br):
    """Build 313: "Can we double check that all the questions are being
    shuffled properly ... please please ensure this." Measured, the
    question order was not random: build 229's rule moved every recently
    opened question to the back of the next run, so on every small unit a
    question's place correlated about -0.47 with its place one run before
    (each run close to the last one backwards) and the big units carried
    the same 48 questions at the end of run after run. Now a plain
    shuffle with only the opening questions kept fresh. Also: a Victims
    of Crime question whose import had cut one choice in half and glued
    "All of the Above" onto another. Fails on 312."""
    print("\n97. build 313: question order and answer choices are really shuffled")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{
      const out = { units: [] };
      localStorage.removeItem('class26e.recentq');
      const RUNS = 60;
      topicsIn(QUESTIONS).forEach(u => {
        const ids = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === u.trim());
        if(ids.length < 19) return;
        const runs = [];
        for(let r = 0; r < RUNS; r++){ const o = freshOrder(ids); rememberOpeners(o); runs.push(o); }
        const pos = runs.map(o => { const m = new Map(); o.forEach((qi, i) => m.set(qi, i)); return m; });
        const n = ids.length, mx = (n - 1) / 2;
        const corr = k => { let s = 0, c = 0; for(let r = k; r < RUNS; r++){ let num = 0, d = 0;
          ids.forEach(q => { const a = pos[r].get(q) - mx, b = pos[r - k].get(q) - mx; num += a * b; d += a * a; }); s += num / d; c++; } return s / c; };
        // the opening few never repeat the last run's opening few
        const k = Math.min(4, Math.floor(n / 3)); let reopen = 0;
        for(let r = 1; r < RUNS; r++) reopen += runs[r].slice(0, k).filter(x => runs[r - 1].slice(0, k).includes(x)).length;
        out.units.push({ u: u.slice(0, 24), n, c: [1, 2, 3, 4].map(corr).map(x => +x.toFixed(3)), reopen });
      });
      // answer choices: every question that can move shows several orders,
      // and where the right answer is an ordinary choice it lands in every
      // slot about equally often
      const isRef = (q, k) => CHOICE_REFERS_RE.some(re => re.test(String(q.choices[k])));
      let few = [], slot = [0, 0, 0, 0], freeAns = 0;
      QUESTIONS.forEach((q, qi) => {
        if(q.fixedOrder || (q.choices || []).length !== 4 || q.choices.some((c, k) => isRef(q, k) || /\\b(above|listed|these)\\b/i.test(String(c)))) return;
        const seen = new Set();
        for(let t = 0; t < 20; t++){ layout = {}; runMode = 'drill'; cfg.shuffle = true; const o = optionOrder(qi); seen.add(o.join());
          if(!isRef(q, q.answer)) slot[o.indexOf(q.answer)]++; }
        if(!isRef(q, q.answer)) freeAns++;
        const movable = q.choices.filter((c, k) => !isRef(q, k)).length;
        if(movable >= 3 && seen.size < 3) few.push(q.topic.trim().slice(0, 12) + ' ' + q.src);
      });
      // 6 Oct: a question whose choices point at each other ("All of the
      // above", "Both A & B", "A, B, and C") shows the study guide's exact
      // order in every mode, shuffle on or off, and no choice is rewritten
      out.letters = []; out.frozenN = 0;
      const ptr = q => (q.choices || []).some((c, k) => isRef(q, k) || /\\b(above|listed|these)\\b/i.test(String(c)));
      QUESTIONS.forEach((q, qi) => {
        if(!ptr(q)) return; out.frozenN++;
        const guide = q.choices.map((c, k) => k).join();
        const orders = [];
        for(let t = 0; t < 8; t++){
          layout = {}; runMode = 'exam'; orders.push(optionOrder(qi).join());
          layout = {}; runMode = 'drill'; cfg.shuffle = true; orders.push(optionOrder(qi).join());
          layout = {}; runMode = 'drill'; cfg.shuffle = false; orders.push(optionOrder(qi).join());
          orders.push(shuffledChoiceOrder(qi, false).join());
        }
        const rev = q.choices.map((c, k) => k).reverse();
        const rewritten = typeof choiceShown === 'function' && q.choices.some((c, k) => choiceShown(qi, k, rev) !== String(c));
        if(orders.some(o => o !== guide) || rewritten) out.letters.push(q.topic.trim().slice(0, 12) + ' ' + q.src + (rewritten ? ' (text rewritten)' : ' (moved)'));
      });
      out.hasShown = typeof choiceShown === 'function';
      const tot = slot.reduce((a, b) => a + b, 0);
      out.slotPct = slot.map(x => +(100 * x / tot).toFixed(1)); out.few = few.slice(0, 8); out.fewN = few.length; out.freeAns = freeAns;
      // the import damage
      const v = QUESTIONS.findIndex(q => (q.topic || '').trim() === 'Victims of Crime' && q.src === 5);
      out.victim = v >= 0 ? QUESTIONS[v].choices.slice() : null;
      out.victimKeep = v >= 0 && KEYS[v] === 'Victims of Crime|5|' + hashOf(String(QUESTIONS[v].q) + '\\u0001' + [
        'Assure victims that their reactions are natural and understandable.',
        'Recognize \\u201cfrozen fright\\u201d or the victim\\'s complete dissociation between them and the',
        'event.',
        'Victims may \\u201cdeny or minimize\\u201d the impact of the assault or crime they\\'ve been subjected to. All of the Above'].join('\\u0001'));
      // a choice cut off mid-sentence ("...between them and the") with
      // its last word left over as the next choice ("event.")
      out.dupes = QUESTIONS.map((q, i) => i).filter(i => { const c = (QUESTIONS[i].choices || []).map(x => String(x).trim().toLowerCase()); return new Set(c).size !== c.length; })
        .map(i => QUESTIONS[i].topic.trim().slice(0, 12) + ' ' + QUESTIONS[i].src);
      // "writ of" alone was a wrong answer cut off in the guide (US and Texas 23)
      out.damaged = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].choices || []).some(c => /\\b(of|the|and|to)$/i.test(String(c).trim()) && String(c).trim().split(/\\s+/).length <= 3)).map(i => QUESTIONS[i].topic.trim().slice(0, 12) + ' ' + QUESTIONS[i].src)
        .concat(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].choices || []).some((c, k, all) => {
        const t = String(c).trim(), prev = k ? String(all[k - 1]).trim() : '';
        return (/.\\s(all|none) of the above\\s*\\.?$/i.test(t) && !/^(all|none|any)/i.test(t))
          || (/\\b(the|and|of|or|a|an|to|between)$/i.test(prev) && /^[a-z]/.test(t)); }))
        .map(i => QUESTIONS[i].topic.trim().slice(0, 12) + ' ' + QUESTIONS[i].src));
      return out; }""")
    bad = [u for u in r["units"] if any(abs(c) > (0.15 if u["n"] >= 30 else 0.3) for c in u["c"])]
    check("a question's place in one run has nothing to do with its place 1-4 runs earlier, on every unit",
          r["units"] and not bad, bad or [(u["u"], u["c"]) for u in r["units"]][:6])
    check("the opening questions never repeat the last run's opening questions",
          r["units"] and all(u["reopen"] == 0 for u in r["units"]), [(u["u"], u["reopen"]) for u in r["units"] if u["reopen"]])
    check("every four-choice question that can move comes up in several orders", r["fewN"] == 0, r["few"])
    check("every question with All of the above / Both A & B / A, B, and C keeps the study guide's exact order in every mode, shuffled or not, text never rewritten",
          r["frozenN"] > 100 and r["letters"] == [], [r["frozenN"]] + r["letters"][:6])
    check("an ordinary right answer lands in A, B, C and D about equally (20-30% each)",
          r["freeAns"] > 500 and all(20 <= x <= 30 for x in r["slotPct"]), r["slotPct"])
    # REVISED 6 Oct: "these test questions are supposed to be exactly like
    # the study guides" - the bank keeps the guide's wording, damage and
    # all, so the four choice repairs (US/TX 23, Fitness 11, Victims of
    # Crime 5, Penal 346) were undone. What is asserted now is the rule:
    # no question shows choices other than the ones it was stored under.
    check("the Victims of Crime question reads exactly as the study guide has it, identity unchanged",
          r["victimKeep"] is True and r["victim"] and r["victim"][2] == "event.", r["victim"])
    kc = pg.evaluate("()=>QUESTIONS.map((q, i) => i).filter(i => Array.isArray(QUESTIONS[i].keyChoices) && QUESTIONS[i].keyChoices.join('|') !== QUESTIONS[i].choices.join('|')).map(i => QUESTIONS[i].topic.trim().slice(0, 12) + ' ' + QUESTIONS[i].src)")
    check("no question's choices are reworded from the study guide (no keyChoices that differ)", kc == [], kc)
    ctx.close()


def check_b313_sheet2(br):
    """Build 313, the start sheet's last round: the hundo chip centred over
    the slider and saying what it costs, no "random order" in the shuffle
    line, a Max button on the time limit that works like All, and the two
    question-bank halves centred by eye. Fails on 312."""
    print("\n96. build 313: start sheet - centred hundo chip, Max on the time limit, no shuffle filler")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const out={};
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      cfg.mode='drill'; cfg.units=[]; cfg.size=0; showSetup(); await wait(700);
      document.querySelector('.picks .pick .pname').click(); await wait(300);
      document.getElementById('nextbtn')?.click(); await wait(1000);
      const sheet=document.querySelector('#unitoptions-modal');
      out.shuffle=[...sheet.querySelectorAll('*')].filter(e=>e.childElementCount===0).map(e=>e.textContent).find(t=>/answer choices\./.test(t) && /huffle/.test(t)) || '';
      const sl=sheet.querySelector('.howmany-sect input.slider');
      sl.value=Math.floor(Number(sl.max)/2); sl.dispatchEvent(new Event('input',{bubbles:true})); sl.dispatchEvent(new Event('change',{bubbles:true})); await wait(500);
      const chip=sheet.querySelector('.hundo-chip'); const c=chip.getBoundingClientRect(), w=sl.parentElement.getBoundingClientRect();
      out.chip={ off: Math.round((c.left+c.right)/2-(w.left+w.right)/2), text: chip.innerText };
      chip.click(); await wait(300); out.why=(sheet.querySelector('.hundo-why')||{}).textContent||'';
      { const w=sheet.querySelector('.hundo-why'); const bg = el => { const c=getComputedStyle(el); return c.backgroundImage + ' | ' + c.backgroundColor + ' | ' + c.borderTopColor; };
        out.reds = w ? [bg(chip), bg(w)] : null; }
      document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})); await wait(100);
      const inp=[...sheet.querySelectorAll('input[type=checkbox]')].find(x=>{ let e=x; for(let k=0;k<4&&e;k++){ e=e.parentElement; if(e && /Time limit/.test(e.textContent) && !/Stopwatch/.test(e.textContent)) return true; } return false; });
      inp && inp.click(); await wait(500);
      const mb=sheet.querySelector('.minutes-sect .slider-maxbtn');
      out.max0 = mb ? { on: mb.classList.contains('on'), text: mb.textContent } : null;
      if(mb){ mb.click(); await wait(500); out.max1 = { on: mb.classList.contains('on'), mins: cfg.timerMinutes,
        val: (sheet.querySelector('.minutes-sect input.slider')||{}).value }; }
      const ms=sheet.querySelector('.minutes-sect input.slider');
      const mid = b => { const r=b.getBoundingClientRect(), t=document.createRange(); t.selectNodeContents(b); const tr=[...t.getClientRects()].pop();
        return tr ? Math.round((tr.left+tr.right)/2 - (r.left+r.right)/2) : 99; };
      out.centre = [];
      if(ms && mb){ ms.value=30; ms.dispatchEvent(new Event('input',{bubbles:true})); await wait(80); out.max2 = { on: mb.classList.contains('on'), lit: mb.classList.contains('just-ready') }; await wait(1200);
        out.centre.push(mid(mb)); const ab=sheet.querySelector('.howmany-sect .slider-allbtn'); out.centre.push(mid(ab)); ab.click(); await wait(600); out.centre.push(mid(ab)); }
      return out; }""")
    ctx.close()
    check("the shuffle line says what it does and nothing about question order",
          r["shuffle"] and "random order" not in r["shuffle"], r["shuffle"])
    check("the No hundo chip is centred over the slider", abs(r["chip"]["off"]) <= 1, r["chip"])
    check("and says No hundo, and its note names the hundo total and the badge count",
          "hundo" in r["chip"]["text"].lower() and "hundo total" in r["why"] and "badge" in r["why"]
          and "\u201cHow many\u201d" in r["why"] and "\u201cAll\u201d" in r["why"], [r["chip"], r["why"]])
    # [Max unticked, All unticked, All ticked]. Ticked, the tick and the
    # word are centred as a pair, so the word alone sits half a tick right.
    ce = r.get("centre") or [9, 9, 99]
    check("the word sits in the middle of Max and All when there is no tick",
          abs(ce[0]) <= 1 and abs(ce[1]) <= 1 and 2 <= ce[2] <= 9, ce)
    # "it looks like a different red": the note is the chip's tint and border
    rd = r.get("reds") or ["", ""]
    check("the No hundo note is the same red as its chip, tint and border",
          "rgba(255, 107, 91, 0.12)" in rd[1] and rd[0].split(" | ")[2] == rd[1].split(" | ")[2], rd)
    m0, m1, m2 = r.get("max0") or {}, r.get("max1") or {}, r.get("max2") or {}
    check("the time limit has a Max button, lit while the limit is below the top",
          m0.get("text", "").strip().lower() == "max" and m0.get("on") is False, m0)
    check("Max takes the limit to the top and goes quiet; dragging back lights it up again",
          m1.get("on") is True and m1.get("mins") == 90 and m2.get("on") is False and m2.get("lit") is True, [m1, m2])


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
      // The windows are FLARE_WINDOWS (build 302: 20 / 34-36 / 47-49 / 59-61 / 70-72).
      store.flareLevels = { orange: 45, yellow: 66 };   // the old schedule's draws
      out.gates = ['red','orange','yellow','violet','white'].map(k => mysteryLevelGate(k));
      out.windows = ['red','orange','yellow','violet','white'].map(k => FLARE_WINDOWS[k]);
      out.oldOutside = !(45 >= FLARE_WINDOWS.orange[0] && 45 <= FLARE_WINDOWS.orange[1]) && !(66 >= FLARE_WINDOWS.yellow[0] && 66 <= FLARE_WINDOWS.yellow[1]);
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
    # build 313: a sixth, the planet's own, appended after the five
    check("five flares, the last two Void's (and the planet's own after them)",
          r["order"][:5] == ["red", "orange", "yellow", "violet", "white"], r["order"])
    g = r["gates"]
    # The windows are read off the page: they moved in build 302 (red 20,
    # orange ~35, yellow ~48, Umbra ~60, Horizon 70-72) and a gate that
    # names the numbers fails the app for being right. What is asserted is
    # the shape - every draw inside its own window, the old draws redrawn,
    # and the windows climbing in order. Section 71 holds the numbers.
    w = r["windows"]
    check("each flare's level sits in its window, old draws redrawn",
          all(w[i][0] <= g[i] <= w[i][1] for i in range(5)) and r["oldOutside"]
          and all(w[i][1] < w[i + 1][0] for i in range(4)), (g, w))
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
      showCustomize('banner');
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
      /* a question that is meant to shuffle: since build 298 one whose
         choices point at each other ("A, B, and C") keeps its order */
      const held = i => typeof choicesReferToEachOther === 'function' ? choicesReferToEachOther(i) : !!QUESTIONS[i].fixedOrder;
      const qi = QUESTIONS.findIndex((q, i) => !held(i) && q.choices.length === 4);
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
    secrets = ["voidwalker", "umbra", "singularity", "genesis"]  # Genesis: build 313
    # Build 304: Zenith, the ultimate, is a feat too and comes after the
    # secrets - "it will be the last character on the list".
    # Build 312: three ultimates, Zenith still last - Astral, Celestial, Zenith.
    o = r["order"]
    ULT = ["astral", "celestial", "zenith"]
    ult = o[-3:] == ULT
    o = [x for x in o if x not in ULT]
    check("the challenge row: the known challenge characters in order, anything newer after them (the Ronin), then the secrets, then the three ultimates with Zenith last",
          ult and o[:len(known)] == known and o[-len(secrets):] == secrets and "ronin" in o and "knight" not in o and "nightowl" not in o, r["order"])
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
      showCustomize('character');
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
                      star: (() => { const r = sh.querySelector('.drawfrom-sect .bank-starred'); if(!r) return null;
                        return { text: (r.querySelector('.otext') || {}).firstChild ? r.querySelector('.otext').firstChild.textContent : '',
                                 hint: (r.querySelector('.ohint') || {}).textContent || '', on: r.querySelector('input').checked }; })() };
        cfg.size = 0; if(sl){ sl.value = sl.min; sl.dispatchEvent(new Event('input', { bubbles:true })); }
        /* build 311: the warning is the "No hundo" chip in the How many row */
        res.dragged = cfg.size; { const hn = sh.querySelector('.hundo-chip'); res.warn = !!hn && !hn.hidden; }
        if(sl){ sl.value = sl.max; sl.dispatchEvent(new Event('input', { bubbles:true })); }
        res.atEnd = cfg.size; { const hn = sh.querySelector('.hundo-chip'); res.warnAtEnd = !!hn && !hn.hidden; }
        const sw = sh.querySelectorAll('.timer-sect .opt input[type=checkbox]');
        res.timerSwitches = sw.length;
        /* the Countdown switch by name (build 310 put the Stopwatch first) */
        const cd = [...sh.querySelectorAll('.timer-sect .opt')].find(r => /Countdown|Time limit/.test(r.textContent));
        const cdIn = cd && cd.querySelector('input[type=checkbox]');
        if(cdIn){ cdIn.checked = true; cdIn.dispatchEvent(new Event('change', { bubbles:true })); }
        res.timerAfter = cfg.timer;
        /* Build 250: Shuffle and Hide answers are their own card; the fold is the timer alone. */
        const mb = sh.querySelector('.more-body'), rows = sh.querySelector('.optionsmodal-body > .sect > .opt-rows');
        res.optsFolded = !!mb && !mb.querySelector('.opt-rows') && !!rows && rows.querySelectorAll('.opt:not([hidden])').length === 2
          && !!mb.querySelector('.timer-sect');
        /* build 309: the Timer card is not a dropdown - open from the start, no button to fold it */
        res.timerOpen = !!mb && mb.classList.contains('open') && !document.querySelector('.unitoptions-modal-sheet button.more-toggle');
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
    # REVISED IN 311: the box carries what it draws ("The whole unit"),
    # still never a number - the rule from 250 is the number.
    # REVISED IN 313: "it says the whole unit but what if you have
    # multiple units?" - the choice is "Your unit" / "Your units", and with
    # several it says how many UNITS (never how many questions).
    # REVISED AGAIN IN 313: "should it say all questions from selected
    # unit? Starred questions from selected unit?" - the name says which
    # questions and the line says where from; still never a question count.
    # REVISED IN 314: "Maybe all questions should be default and the
    # starred thing should be a button?" - All questions is simply the
    # default with no control of its own; the bank is ONE switch,
    # "Starred questions only", off, saying how many are starred (or that
    # none are) and never the unit's question count.
    st = sh.get("star") or {}
    check("the bank is one switch, Starred questions only, off by default, saying what is starred - no question count",
          st.get("text") == "Starred questions only" and st.get("on") is False
          and re.search(r"starred in |No starred questions in ", st.get("hint", ""))
          and not re.search(r"\d+ question", st.get("hint", "")), sh)
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
    # REVISED IN 309: "Don't put the timer options in a drop down anymore,
    # remove the drop down for that." The timer card is open from the
    # start, with no toggle to fold it; the switches are still in it alone.
    check("Shuffle and Hide answers are their own card; the timer has its own card, open, no dropdown",
          sh.get("optsFolded") is True and sh.get("timerOpen") is True, sh)
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
      /* the fixture has no badge, so no rank and an empty bubble - give
         it Bronze (one badge, level 21+) so there is an emblem to centre */
      { const u0 = topicsIn(QUESTIONS)[0]; store.unitPerfects[u0] = badgeThresholdFor(u0);
        store.lifetime.points = Math.max(store.lifetime.points, xpForLevel(25)); }
      showProfile('profile'); await wait(700);
      /* Build 315: the level ring is gone (build 282 put the number in
         it). Build 316: the rank is one line under the name again - the
         emblem, the rank, the level, the XP - so: the emblem sits on that
         line, centred on the rank's name, with the name after it. */
      await T('plate', () => { const e = document.querySelector('.pf-standing .pf-emb');
        const v = e && e.querySelector('svg'); const nm = document.querySelector('.pf-standing .pf-rankname');
        const lab = document.querySelector('.pf-standing .pf-level');
        if(!e || !v || !nm) return 'no emblem or no rank name on the line';
        const a = e.getBoundingClientRect(), b = nm.getBoundingClientRect();
        const off = Math.round(Math.abs((a.top + a.height / 2) - (b.top + b.height / 2)));
        return b.left >= a.right && lab && lab.getBoundingClientRect().left >= b.right ? off : 'not emblem, rank, level in that order'; });
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
      /* Build 308: a rank's reward comes ahead of a challenge's, so it
         follows the rank-up straight away. */
      await T('first', () => { const sp = document.querySelector('.rs-spot'); if(!sp) return null;
        const st = sp.querySelector('.rs-spot-strip.is-rankreward');
        return { text: sp.textContent, strip: st ? st.textContent : null, emblem: !!(st && st.querySelector('svg')) }; });
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
      /* Build 313: this account has 141 hundos and no record of the hundo
         effects being announced, so it is owed the first two (Fireworks
         and the World Tree, read off HUNDO_FX rather than named here) as
         well - they follow in the same sitting, each up long enough to
         count as seen and then tapped away. */
      out.fx = []; out.fxOwed = HUNDO_FX.filter(d => d.need > 0 && d.need <= hundosOf(store)).map(d => d.name);
      for(let k = 0; k < 6; k++){
        const sp = document.querySelector('.rs-spot.rs-spot-fx');
        if(!sp){ await wait(400); continue; }
        out.fx.push((sp.querySelector('.rs-spot-name') || {}).textContent);
        await wait(1500); sp.click(); await wait(1400);
      }
      await T('after', () => ({ spots: document.querySelectorAll('.rs-spot').length, left: pendingHomeUnlocks().chars.length + pendingHomeUnlocks().fx.length }));
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
        /* A flip-book (build 308) is alive too - a small character plays
           its recorded loop rather than the live svg. */
        return { live: a.classList.contains('char-live') || a.classList.contains('char-flip'), sleep: a.classList.contains('char-sleep') }; });
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      // Bronze is wine.
      // Build 244: Bronze is the rookie key now (it was ranger's).
      await T('bronze', () => { document.documentElement.dataset.accent = 'rookie';
        const v = getComputedStyle(document.documentElement).getPropertyValue('--theme-c3').trim();
        document.documentElement.dataset.accent = theme.accent || 'ink'; return v; });
      return out; }""")
    check("the held rank's emblem sits on the rank line, centred on its name, then the level (build 316; a bubble in 315, the level ring before it)",
          isinstance(r["plate"], int) and r["plate"] <= 2, r["plate"])
    check("your own character is alive on the Profile card", r["heroLive"] is True, r["heroLive"])
    sd = r["seed"] if isinstance(r["seed"], dict) else {}
    check("an account already on Gold is NOT marked as having seen its rank character (Solar since 244)", sd.get("gold") is True and sd.get("pharaoh") is False, r["seed"])
    check("Home waits a beat before an unlock arrives", r["notYet"] is False, r["notYet"])
    # BUILD 308: a rank's reward plays ahead of a challenge's (it follows
    # the rank-up), so Gold's Solar is first and Zeus second. The
    # assertions about each card are unchanged; only their order moved.
    fc = r["first"] if isinstance(r["first"], dict) else {}
    check("Gold's character (Solar since 244) plays first on Home as a Rank reward, with Gold's emblem and name in the strip",
          "Solar" in str(fc.get("text")) and "Rank reward" in str(fc.get("strip")) and "Gold" in str(fc.get("strip"))
          and fc.get("emblem") is True, r["first"])
    fl = r["flying"] if isinstance(r["flying"], dict) else {}
    check("tapping it away flies it to the Profile tab (fixed, above the screen) and rings the tab",
          fl.get("pos") == "fixed" and 0 < fl.get("y", -1) < 956 and r["pulse"] is True, [r["flying"], r["pulse"]])
    sc = r["second"] if isinstance(r["second"], dict) else {}
    st = str(sc.get("text"))
    check("Zeus, won away from any results screen, follows as a finished challenge",
          "Zeus" in st and st.count("Challenge complete") == 1 and "Character unlocked" in st, r["second"])
    check("the hundo effects this account already qualifies for follow in the same sitting (build 313)",
          len(r.get("fxOwed") or []) == 2 and r.get("fx") == r.get("fxOwed"), [r.get("fx"), r.get("fxOwed")])
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
      /* REVISED IN 314: one switch, not two boxes - see check_b314_bank */
      await T('bank', () => { const rows = [...document.querySelectorAll('.bank-sect .opt')];
        return { rows: rows.length, bare: rows.every(r => !r.querySelector('.bank-desc') && !r.querySelector('.bank-ico')),
                 oneLine: rows.every(r => ((r.querySelector('.ohint') || {}).textContent || '').trim().length > 2),
                 label: (document.querySelector('.bank-sect .slab') || {}).textContent }; });
      await T('bankInfo', () => { const fc = document.querySelector('.bank-starred .ohint');
        return { info: !!document.querySelector('.bank-info, .bank-infobody'), shown: !!fc, len: fc ? (fc.textContent || '').trim().length : 0 }; });
      cfg.timer = 'down'; cfg.timerMinutes = 20; document.querySelector('.bank-starred')?.click(); await wait(200);
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
    # REVISED IN 309: the line names your selection ("could it be more
    # specific to clarify that is for the ones you have selected?"), so it
    # is allowed 60 characters, still one short line.
    # REVISED IN 311: the words moved INTO the boxes and the line under
    # the switch went - "should it just be in those boxes?"
    # REVISED IN 314: "There's gotta be a better way to do the starred
    # question and all questions thing" - one switch row under "Questions",
    # its one short line saying how many are starred.
    check("Questions: one Starred switch with one short line under it - no info dot",
          b.get("rows") == 1 and b.get("bare") and b.get("oneLine")
          and bi.get("shown") and 0 < bi.get("len", 0) <= 60 and not bi.get("info")
          and b.get("label") == "Questions", [b, bi])
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
          isinstance(t, dict) and t.get("icons") and ("20 min countdown" in tx or "20 min limit" in tx) and ("Flagged" in tx or "Starred" in tx)
          and not any(x in ("All questions", "In order", "No timer") for x in tx)
          and not any(x.startswith("All ") and x[4:].isdigit() for x in tx) and not any(" of " in x for x in tx), t)
    # (The Timer bar's own "20 min countdown" state went with the dropdown
    # in build 309 - the switch beside it says so.)
    # Build 250/251: "I need this to go green when you change it" - then
    # "that box turning green is kinda weird. Don't do that. I like how
    # the timer thing at the top is green though." The pill, not the card.
    check("a timer that is on turns its pill in the top box green, and not the Timer card",
          isinstance(t, dict) and t.get("green") is True and t.get("cardGreen") is False, t)
    # build 310 renamed it "Stopwatch & timer": the shape is that it names the timers
    check("the fold is named for the timers", "timer" in str(r["timerLabel"]).lower(), r["timerLabel"])
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
                 search: !!d.querySelector('.unitdetail-search input'), testFlag: !!d.querySelector('.unitdetail-q .flagbtn .flagbanner, .unitdetail-q .flagbtn.qflag .starfill'),
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
          # Build 303 made the flag a star; the door's shape is what counts.
          cp.get("doors") in (["Tap to see flagged questions"], ["Tap to see starred questions"])
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
      /* Build 315: the plate became the standing block - the rank, large,
         in its lit flare bubble, in a box. Build 316: "the new xp stuff is
         in its own box and it shouldn't be so it feels more of your
         profile" - the rank is the mockup's one line under the name again
         and the box is gone; still one button across the card. */
      const p = document.querySelector('.pf-standing');
      if(!p) return null;
      const cs = getComputedStyle(p);
      return { word: (p.querySelector('.pf-rankname') || {}).textContent,
               rankBar: !!p.querySelector('.profile-rankplate-fill, .profile-rankplate-next, .pf-bar'),
               xpBar: !!p.querySelector('.pf-xpbar .xpbar-fill'),
               w: Math.round(p.getBoundingClientRect().width),
               emb: !!p.querySelector('.pf-idline .pf-emb svg'), bubble: !!p.querySelector('.flare-solo'),
               boxed: cs.backgroundImage !== 'none' || !/rgba\\(0, 0, 0, 0\\)|transparent/.test(cs.backgroundColor) || parseFloat(cs.borderTopWidth) > 0,
               button: p.tagName }; }""")
    check("the rank leads the card as one line under the name - its emblem, the rank, the level, the XP - with no box round it, as one button across the card",
          isinstance(r, dict) and r.get("w", 0) > 300 and r.get("emb") and not r.get("bubble") and r.get("boxed") is False and r.get("button") == "BUTTON", r)
    # REVISED IN 267: "the current rank in the profile box has a progress
    # bar, let's remove that". REVISED IN 315: the bar under the rank is
    # the XP bar, asked back ("how do we still get that nice xp stuff");
    # the climb to the next rank is the Next rank card's, never here.
    check("it names the rank; the bar under it is the XP bar, not a bar to the next rank", isinstance(r, dict) and r.get("word") == "Gold"
          and r.get("xpBar") and not r.get("rankBar"), r)
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
    # REVISED IN 309: "In the unit details, go ahead and put the best time
    # you have there." Back as a fifth stat, the same in every mode, and it
    # still says a 100% on the whole unit is what sets one.
    check("the best time is in the details, and says a 100% on the whole unit sets it", isinstance(r, dict)
          and "100% on the whole unit" in str(r.get("unset")) and "100%" in str(r.get("set")), r)
    check("and it is the same card in every mode", isinstance(r, dict) and "Best time" in str(r.get("exam")), r)
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
    # REVISED IN 309: a fifth, Best time, asked for in the details - the
    # same five everywhere is still the shape.
    first = next(iter(modes.values()), [])
    check("every mode shows the same five squares", modes and len(first) == 5 and all(v == first for v in modes.values())
          and any("time" in x.lower() for x in first), modes)
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
      /* build 315: the level is said once, in the standing block */
      out.plates = document.querySelectorAll('.profile-hero .pf-level').length;
      /* Build 243: the badge row is the badges themselves, no meter.
         Build 315: as the badge case strip, every slot, earned or not. */
      out.badgeCells = document.querySelectorAll('.profile-hero .badge-meter-seg').length;
      out.caseCells = document.querySelectorAll('.profile-hero .pf-case .badge-strip-cell').length;
      out.caseEarned = document.querySelectorAll('.profile-hero .pf-case .badge-strip-cell.is-earned').length;
      out.units = units.length;
      const fill = document.querySelector('.pf-standing .pf-bar i, .profile-rankplate-fill');
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
    # REVERSED AGAIN IN 315: Madison picked the Profile mock-up with the
    # badge case as a strip ("the mini badge case is nice"): every slot,
    # the earned ones filled - and still no meter.
    check("Profile: the level said once, and the badges their own block - the case as a strip, no meter",
          isinstance(r, dict) and r.get("plates") == 1 and r.get("badgeCells") == 0
          and r.get("caseCells") == r.get("units") and r.get("caseEarned") == 6, r)
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
      showCustomize('theme'); await wait(500);
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
      out.profile = { strip: document.querySelectorAll('.profile-hero .pf-case .badge-strip-cell').length,
        segs: document.querySelectorAll('.profile-hero .badge-meter-seg').length,
        count: (document.querySelector('.profile-hero .pf-case .pf-case-count') || {}).textContent || '',
        units: topicsIn(QUESTIONS).length };
      /* 4. the rank box: a full-width bar, the next rank as a chip, what is left.
         Build 315: the rank box is the standing block, and the next rank
         and what is left are the Next rank card's - so none of it here. */
      const sb = document.querySelector('.pf-standing') || document.createElement('i');
      out.rankBox = { bar: !!sb.querySelector('.pf-bar, .profile-rankplate-bar'),
        chip: !!sb.querySelector('.pf-goal-emb, .profile-rankplate-nextmark'),
        need: !!sb.querySelector('.pf-task, .profile-rankplate-need'),
        label: (sb.querySelector('.pf-goal-name, .profile-rankplate-next') || {}).textContent || '',
        standing: !!document.querySelector('.pf-standing') };
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
      /* 10. Customize: colours before banners, and big enough to sit beside them.
         Build 315: each is its own page off a summary, so the order is the
         summary's rows, and no grid sits on the summary at all */
      store.onboardingComplete = true;
      showCustomize(); await wait(600);
      out.custom = { rows: [...document.querySelectorAll('.screen-customize .cz-row')].map(r => r.dataset.page),
        grids: document.querySelectorAll('.screen-customize :is(.swatches, .banner-grid, .avatarchar-grid, .hfx-grid)').length };
      showCustomize('theme'); await wait(400);
      out.custom.swatch = Math.round(document.querySelector('.screen-customize .swatch').getBoundingClientRect().width);
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
    # AND BACK IN 315, by choice: the Profile mock-up Madison picked has
    # the badge case as a strip - "the mini badge case is nice". Still no
    # meter, and the count beside it.
    check("Profile shows the count and the badge case as a strip, with no meter",
          p.get("strip") == p.get("units") and p.get("segs") == 0 and re.match(r"^\d+ of \d+", p.get("count", "")), p)
    rb = r.get("rankBox") or {}
    # REVERSED IN 243: "the profile box got worse somehow ... it was so
    # good before" - back to the 241 plate: one bar and "Gold · 35%".
    # REVISED IN 267: the bar came off the plate ("no need for that").
    check("the rank block carries no bar to the next rank, no chip and no to-do line (those are the Next rank card's)",
          rb.get("standing") and not rb.get("bar") and not rb.get("chip") and not rb.get("need") and rb.get("label", "") == "", rb)
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
    # REVISED IN 315: the long page became a summary of four rows, each
    # opening its own page - so no grid is buried under another any more.
    check("Customize is four rows - Character, Banner, Theme color, Hundo effect - with no grid on it, and the swatches hold up on their page",
          cu.get("rows") == ["character", "banner", "theme", "fx"] and cu.get("grids") == 0 and cu.get("swatch", 0) >= 56, cu)
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
      showCustomize('character'); await wait(700);
      out.groups = [...document.querySelectorAll('.screen-customize .avatarchar-group-title')]
        .filter(h => h.nextElementSibling && h.nextElementSibling.classList.contains('avatarchar-grid'))
        .map(h => h.firstChild && h.firstChild.textContent);
      const grid = document.querySelector('.screen-customize .avatarchar-grid');
      out.cols = getComputedStyle(grid).gridTemplateColumns.split(' ').length;
      out.twoLine = [...document.querySelectorAll('.screen-customize .avatarchar-name')].filter(n => n.getBoundingClientRect().height > 18).map(n => n.textContent);
      out.robotShown = !!document.querySelector('.screen-customize .avatarchar-option[aria-label="Robot"]');
      /* build 315: each thing you wear has its own Customize page */
      showCustomize('banner'); await wait(500);
      out.tileNeeds = [...document.querySelectorAll('.screen-customize .banner-opt-need')].map(e => e.textContent);
      out.defaultTile = (document.querySelector('.screen-customize .banner-opt.is-none .banner-opt-name') || {}).textContent;
      out.shadesTile = !!document.querySelector('.screen-customize .banner-opt[data-banner="shades"]');
      /* 4. the swatches preview what they are */
      showCustomize('theme'); await wait(400);
      const dot = n => { const d = document.querySelectorAll('.screen-customize .swatch .dot')[ACCENTS.indexOf(n)]; return d ? getComputedStyle(d).backgroundImage : ''; };
      out.defaultDot = dot('ink'); out.goldDot = dot('veteran');
      /* 5. a locked thing opens a card with a bar */
      showCustomize('banner'); await wait(400);
      const lockedBanner = document.querySelector('.screen-customize .banner-opt.locked[data-banner="tests100"]');
      lockedBanner.click(); await wait(400);
      out.bannerCard = { card: !!document.querySelector('.unlock-card'), bar: !!document.querySelector('.unlock-card .unlock-card-bar'),
        fill: getComputedStyle(document.querySelector('.unlock-card .unlock-card-fill') || document.body).backgroundImage,
        count: (document.querySelector('.unlock-card-count') || {}).textContent || '' };
      document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
      showCustomize('theme'); await wait(400);
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
    # Build 304: the Ultimate group (Zenith) is the last one, after the secrets.
    check("Customize groups the characters, secrets on their own, the Ultimate last, and no Robot for somebody who never held it",
          r.get("groups") == ["Starters", "Rank rewards", "Challenge rewards", "Secrets", "Ultimate"] and r.get("robotShown") is False, r.get("groups"))
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
      /* Build 315: the coin was the standing block's flare bubble. Build
         316: it is the emblem on the rank line, the held rank's own,
         fitted the way every emblem is - held to the same centring */
      const coin = document.querySelector('.pf-standing .pf-emb'), held = 'ranger';
      const csvg = coin && coin.querySelector('svg');
      out.coin = csvg ? { name: (document.querySelector('.pf-standing .pf-rankname') || {}).textContent, want: RANK_DISPLAY_NAME[held], off: off(coin, csvg, held) } : null;
      rankOf = rk0;
      showProfile('profile'); await wait(500);
      out.unrankedEmpty = !rankOf(store) ? (!document.querySelector('.pf-standing .pf-emb') && !document.querySelector('.pf-standing .pf-rankname')
        && /^Level \\d+$/.test((document.querySelector('.pf-standing .pf-level') || {}).textContent || '')) : true;
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
    check("the Profile card's rank line carries the held rank's emblem, centred in its box (within 1.5px, as on Home), and its name",
          coin.get("name") == coin.get("want") and coin.get("off", 9) <= 1.5, coin)
    check("an unranked card names no rank and draws no emblem - just the level (268)", r.get("unrankedEmpty") is True, r.get("unrankedEmpty"))
    ctx.close()


# --------------------------------------------------------------------------
# The questions on slides 55-124 of "TEXAS PENAL CODE for 736 updated
# 8-14-26" (build 313: the next test's slides, replacing slides 0-85), by
# the bank's own `src`. Typed here on purpose: this is the reference the
# app's PENAL_TEST_SRCS is checked AGAINST, not read back from it.
PENAL_SLIDES_SRCS = sorted([
    249, 213, 24, 121, 200, 262, 344, 128, 159, 61, 95, 183, 109, 117, 150,
    158, 250, 304, 65, 70, 97, 178, 319, 236, 318, 346, 22, 209, 3, 204, 253,
    290, 343, 321, 322, 324, 28, 41, 66, 68, 76, 141, 207, 323, 255, 83, 90,
    100, 222, 299, 88, 230, 297, 338, 114,
    348, 349, 350])  # #213, #128 and #183 again - the deck has each on two slides
# The version-only copies, by the src each one repeats.
PENAL_REPEATS = {348: 213, 349: 128, 350: 183}

PENAL_CARD = ".picks .pick:has(.pname:text-is('Penal Code'))"

# Where a run stands: its pool as srcs, and whether it is all one unit.
PENAL_RUN = """()=>{ const o = (typeof order !== 'undefined' && Array.isArray(order)) ? order : [];
  return { n: o.length, srcs: o.map(i => Number(QUESTIONS[i].src)).sort((a, b) => a - b),
           allPenal: o.every(i => (QUESTIONS[i].topic || '').trim() === 'Penal Code'),
           unitTotal: QUESTIONS.filter(q => (q.topic || '').trim() === 'Penal Code' && !q.versionOnly).length }; }"""
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
    slides 55-124 of the instructor's PowerPoint. Selecting it asks which,
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
          .find(x => /55\\u2013124|55-124/.test(x.textContent) === (w === 'short')); if(b) b.click(); }""", which)
        pg.wait_for_timeout(450)
        return pg.evaluate(PENAL_STATE)

    # 1. the pop-up and what it says
    s1 = tap()
    check("selecting the Penal Code opens a pop-up, and holds the tick until it is answered",
          s1["pop"] and not s1["checked"] and s1["units"] == [], s1)
    opts = s1["opts"]
    # The whole unit is the study guide's 340 (build 300): the second #84,
    # flagged versionOnly, belongs to the slides 55-124 version alone.
    nums = pg.evaluate("""()=>({ whole: QUESTIONS.filter(q => (q.topic||'').trim() === 'Penal Code' && !q.versionOnly).length })""")
    short = [o for o in opts if ("55–124" in o or "55-124" in o)]
    whole = [o for o in opts if o not in short]
    check("two choices: the whole unit, and the one from slides 55-124 of the PowerPoint",
          len(opts) == 2 and len(short) == 1 and "PowerPoint" in short[0] and "Penal Code" in whole[0]
          and ("%d questions" % len(PENAL_SLIDES_SRCS)) in short[0]
          and ("%d questions" % nums["whole"]) in whole[0], opts)
    check("nothing on it says 'test version'", s1["pop"] and "test version" not in s1["popText"].lower(), s1["popText"])
    # Build 250: the short version's hundo warning lives here and only here.
    check("the short choice says on the pop-up that it earns no hundo, and the whole unit does not",
          bool(short) and bool(whole) and "hundo" in short[0].lower() and "hundo" not in whole[0].lower(), opts)
    s2 = choose("short")
    check("choosing slides 55-124 selects the card on that version",
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
    check("the card says it carries the slides 55-124 version, and a tap on that line is a tap on the card",
          bool(pill) and "55–124" in pill["text"] and pill["passesTap"], pill)
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
    n_ver = "%d questions" % len(PENAL_SLIDES_SRCS)
    check("the start sheet and the Start button count the slides 55-124 questions",
          n_ver in sheet["line"] and n_ver in sheet["start"], sheet)
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
    check("the run is exactly the %d questions on slides 55-124" % len(PENAL_SLIDES_SRCS),
          run["allPenal"] and run["srcs"] == PENAL_SLIDES_SRCS, "%d questions" % run["n"])
    # 4. a perfect run of it earns XP and no hundo
    hundo = pg.evaluate("""()=>{ const u = 'Penal Code';
      const before = { hundos: unitPerfectCount(u), perfect: store.lifetime.perfectTests || 0, xp: store.lifetime.points || 0 };
      attempts = {}; picked = {}; timedOutSet = {}; timedOut = false; runStartTime = Date.now() - 90000;
      order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
      summarize();
      return { before, after: { hundos: unitPerfectCount(u), perfect: store.lifetime.perfectTests || 0, xp: store.lifetime.points || 0 },
               rows: [...document.querySelectorAll('.badgeprogress-name')].map(e => e.textContent) }; }""")
    check("a perfect slides 55-124 run is not a Penal Code hundo, and shows no badge progress for it",
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
    check("Re-run repeats slides 55-124, and does not ask",
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
    # build 314: Review opens through LOADING REVIEW (~2s)
    rv = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      document.getElementById('nextbtn').click(); document.querySelector('.sheet-begin-btn').click();
      await wait(100); while(document.getElementById('teststart-overlay')) await wait(30); await wait(300);
      return document.querySelectorAll('.review-question').length; }""")
    check("Review of slides 55-124 lists those questions only", rv == len(PENAL_SLIDES_SRCS), rv)
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
          v1["pop"] and n_ver in room["line"] and len(args) >= 4 and args[0] == ["Penal Code"]
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
    check("a room runs what the ROOM says: the whole unit despite a player's last pick, and slides 55-124 when it is set",
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
    # build 313: only the first three show until Void is held (this account
    # has found none), and each is an HTML flare with a 44px tap disc
    check("the secret-flare dots take a tap 15px from their centre", r["n"] == 3 and r["hits"] == 3, r)
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
        # REVISED IN 309: "one level at a time" became "one rank at a time"
        # on request, so rank counts as the game word too.
        check("%s: the tagline leads with 'master the material' and works a game word in" % tag,
              re.search(r"^master the material", r["text"], re.I) and re.search(r"\b(game|play|level|quest|rank)", r["text"], re.I), r["text"])
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
    /* REVISED IN 309: the announcement is the bubble beside the "?" now
       (#daily-lock-tip.is-live), the top banner only its fallback. */
    const f = document.querySelector('.daily-question-fab'), a = document.querySelector('#daily-lock-tip.is-live') || document.getElementById('dailyalert');
    const orb = document.querySelector('.daily-orb-core');
    const ar = a ? a.getBoundingClientRect() : null;
    frames.push({ t: performance.now() - t0,
      charging: !!(f && f.classList.contains('is-charging')),
      arcL: rot(document.querySelector('.dq-charge-l .dq-charge-arc')),
      burst: (b => b ? parseFloat(getComputedStyle(b).opacity) : 0)(document.querySelector('.dq-charge-burst')),
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
           chat: ch ? [ch.left, ch.top, ch.right, ch.bottom] : null, vw: innerWidth, vh: innerHeight }; }"""


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
        # 2-3.5s until build 268 asked for "another 2-3 seconds" on the ring;
        # +0.5s in 309, the ring holding closed before it goes off
        check("%s: the announcement follows the recharge, 4.5-6.5s in" % label,
              shown is not None and closed is not None and shown >= closed and 4500 <= shown <= 6500,
              [closed, shown])
        # REVISED IN 309: "it shouldn't go to the top ... needs to go near
        # the daily question button". No orb flight to a top banner: the
        # bubble opens beside the "?" itself, clear of the chat button,
        # and the ring is seen CLOSED before it goes ("the circle when
        # it's fully charged doesn't complete").
        sealed = next((f["t"] for f in fr if f["arcL"] is not None and abs(f["arcL"]) >= 179), None)
        boom = next((f["t"] for f in fr if f["burst"] > 0.1), None)
        check("%s: the ring is seen whole before it goes off" % label,
              sealed is not None and boom is not None and boom - sealed >= 300, [sealed, boom])
        settled = [f for f in fr if f["op"] > 0.99 and f["a"] and f["t"] > (shown or 0) + 700]
        if settled:
            a = settled[0]["a"]; fx, fy = r["fab"]
            gap = max(a[0] - fx, fx - a[2], a[1] - fy, fy - a[3])
            check("%s: the bubble opens beside the button, not at the top" % label,
                  a[1] > 0.5 * r["vh"] and gap <= 80, [a, r["fab"]])  # from the button's CENTRE: its radius + the 10px gap
            ch = r["chat"]
            clear = ch is None or a[2] <= ch[0] - 4 or a[3] <= ch[1] or a[1] >= ch[3]
            check("%s: clear of the chat button" % label, clear, [a, ch])
        else:
            check("%s: the bubble settles" % label, False)
        stays = [f for f in fr if f["op"] > 0.9 and shown is not None and f["t"] >= shown + 6000]
        check("%s: and is still up six seconds later" % label, bool(stays), round(fr[-1]["t"] - (shown or 0)))
        ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate(DAILY_SAMPLER, {"ms": 1500, "reduce": True})
    fr = r["frames"]
    shown = next((f["t"] for f in fr if f["op"] > 0.5), None)
    check("Reduce motion: no recharge, no orb", not any(f["charging"] or f["orb"] for f in fr))
    check("Reduce motion: just the bubble, at once", shown is not None and shown < 800, shown)
    ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate("()=>{ store.dailyQuestionDate=''; saveStore(); localStorage.setItem('class26e.daily.seen','2000-01-01'); showHome(); }")
    pg.wait_for_timeout(1100)
    b = pg.evaluate("""()=>{ const f=document.querySelector('.daily-question-fab'); const r=f.getBoundingClientRect();
      return {x:r.left+r.width/2, y:r.top+r.height/2, charging:f.classList.contains('is-charging')}; }""")
    pg.mouse.click(b["x"], b["y"])
    pg.wait_for_timeout(7300)
    q = pg.evaluate("""()=>({ daily: !!document.querySelector('.qnum-daily'), orb: !!document.querySelector('.daily-orb'),
                              banner: !!document.getElementById('dailyalert') || !!document.getElementById('daily-lock-tip') })""")
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
          /* 1300, not 500 (build 313): the fill was slowed on request ("a
             tiny bit slowed down") and the lit depth lands when it ends */
          cb.click(); await wait(1300);
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
      /* a unit card - Review's first card is the Flagged questions box (build 297), which has no checkbox */
      const cb = [...document.querySelectorAll('.picks .pick:not(.pick-flagged-all)')].find(p => !/Penal/.test(p.textContent) && p.querySelector('input')).querySelector('input');
      cb.click(); await wait(400);
      return document.getElementById('bottomtab-start').getAttribute('aria-label') || ''; }""")
    check("in Review mode Start says review, not drill", lab.lower().startswith(("start review", "start learning")), lab)
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
      showCustomize('character'); await new Promise(r => setTimeout(r, 1500));
      const o = document.querySelector('.avatarchar-option.selected'); const svg = o && o.querySelector('.avatarchar-svg');
      const cs = svg ? getComputedStyle(svg) : null;
      return { masked: !!cs && ((cs.maskImage || cs.webkitMaskImage || 'none') !== 'none'),
               drawingGlow: !!cs && /drop-shadow/.test(cs.filter),
               buttonGlow: !!o && /drop-shadow/.test(getComputedStyle(o).filter),
               /* build 314: a tile playing its flip-book carries no filter
                  (a drop-shadow re-drawn 24 times a second doubled
                  Customize's frame time); its light is the pool behind it
                  and the selection ring, neither of which is masked */
               flipping: !!o && o.classList.contains('char-flip'),
               poolGlow: !!o && /gradient/.test(getComputedStyle(o, '::before').backgroundImage),
               ring: !!o && getComputedStyle(o, '::after').opacity === '1' }; }""")
    # The cause, checked directly: CSS applies an element's filter before
    # its mask, so a glow on the masked drawing is cut to the mask's
    # rectangle. Pixel tests at the box edge could not tell the two apart
    # reliably (the round glow is steep there too); this can.
    check("a selected character's glow is not on the masked drawing (which cuts it square), but on its button",
          g["masked"] and not g["drawingGlow"]
          and (g["buttonGlow"] or (g.get("flipping") and g.get("poolGlow") and g.get("ring"))), g)
    r = pg.evaluate("""()=>{ const H = 3600000, out = {}; store.legacyChars = [];
      /* Build 314 caps a day of the study log at 6 hours up to the leak
         fix (normalizeStudyLog, run on every load), so 30 hours on one
         day loads as 6 and the Hacker re-locks. The hours go in at 5 a
         day, as somebody would really have studied them. */
      const spread = h => { const o = {}; let left = h, d = 1;
        while(left > 1e-9){ const t = Math.min(5, left); o['2026-09-' + String(d).padStart(2, '0')] = t * H; left -= t; d++; }
        return o; };
      const set = (st, h) => { store.bestTestStreak = st; /* build 267: one test */ store.studyLog = spread(h); };
      const N = CHARACTER_FEATS.streak100.need;
      set(N - 1, 24.9); out.under = [isLockedCharacter('marksman'), isLockedCharacter('hacker')];
      set(N, 25); out.at = [isLockedCharacter('marksman'), isLockedCharacter('hacker')];
      const d = JSON.parse(JSON.stringify(store)); d.avatarChar = 'hacker'; d.studyLog = spread(22);
      d.bestTestStreak = 120; d.pendingCharUnlocks = ['marksman', 'clown'];
      applyLoadedData(d); out.revoked = [store.avatarChar, store.pendingCharUnlocks.slice()];
      const e = JSON.parse(JSON.stringify(store)); e.avatarChar = 'marksman'; e.bestTestStreak = N + 10;
      e.studyLog = spread(30); e.pendingCharUnlocks = ['hacker'];
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
      out.ranksScreen = (showProfile(), await wait(700), (document.querySelector('.pf-standing') || {click(){}}).click(), await wait(900),
                         !!document.querySelector('.screen-ranks'));
      out.hiddenArt = ['umbra', 'singularity'].map(id => !!characterDetail(id).hideArt);
      out.animated = ['adept_rank', 'elite_rank', 'titan_rank'].map(id => !buildBannerArt(id).classList.contains('is-still'));
      showCustomize('banner'); await wait(900);
      out.needs = BANNERS.filter(b => !b.secret).map(b => { const o = document.querySelector('.banner-opt[data-banner="' + b.id + '"] .banner-opt-need');
        return !!o && o.textContent === b.label; });
      return out; }""")
    check("every tab on the bar opens its screen when TAPPED, and the Profile card's rank block opens the climb",
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
    # Build 314: back to "To reach <Rank>" after "<Rank> challenges" was
    # tried and Madison preferred the original.
    check("the Rank screen's rings are headed with the rank they are for", bool(k["head"]) and k["head"].startswith("To reach ")
          and len(k["head"]) > len("To reach "), k)
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
        # CENTRED, not merely "in view" (fixed in 295): scrolled just far
        # enough, a node can stop at the bottom edge under the tab bar,
        # and then this measured the bar - a still bar read as a still
        # emblem, and failed on a day when nothing in the app had changed.
        el.evaluate("e => e.scrollIntoView({ block: 'center', behavior: 'instant' })")
        pg.wait_for_timeout(250)
        frames = []
        # 10 frames over ~4s (was 6 over ~2.4s, fixed in 295): Silver's
        # loop is slow, and centred it measured 4.4-5.7 against a 4.5 bar
        # depending on where in its cycle the window fell.
        for _ in range(10):
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
      /* the heart, not the shards build 314 throws out of it (rk-nova-frag,
         check_b314_nova): eleven black triangles on purpose */
      const dark = [...t.querySelectorAll('path')].filter(p => p.getAttribute('fill') === '#000000' && !p.closest('.rk-nova-frag'));
      /* dark, but not a disc: an 8-point star is 8 curves, a circle 2-4 arcs */
      out.darkStar = dark.length > 0 && dark.every(p => (p.getAttribute('d') || '').split(/[MLQAZ]/i).length > 7);
      const html = id => buildBannerArt(id).innerHTML;
      /* build 304: the turn is a layer on the compositor now (bl-spin) */
      out.sapphireBanner = /b[nl]-spin/.test(html('adept_rank')) && /#3D74E8/i.test(html('adept_rank'));
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
      out.plateBar = !!document.querySelector('.pf-standing .pf-bar, .profile-rankplate-bar, .profile-rankplate-next');
      /* Build 315: the badges are the badge case - its strip IS badge art,
         by choice; what it must not grow back is a ring, or a unit and
         its hundos (those belong to the Next rank card's badge task) */
      const sect = document.querySelector('.pf-case');
      out.badgeSvgs = sect ? sect.querySelectorAll('.badge-strip-cell.is-earned').length : -1;
      out.badgeText = sect ? sect.textContent : '';
      out.badgeMedal = sect ? sect.querySelectorAll('.statring, .rankhero-ring').length : -1;
      const fill = document.querySelector('.profile-hero .profile-xpbar .xpbar-fill');
      out.fillBg = fill ? getComputedStyle(fill).backgroundImage : '';
      /* build 282: the level is the Rank tab's blue ring; its colour is the stroke.
         Build 315: the ring is gone; the level is said in the bar's blue.
         Build 316: the mockup's line - the XP is the blue on it */
      const lv = document.querySelector('.profile-hero .pf-standing .pf-xp-total');
      out.levelBg = lv ? getComputedStyle(lv).color : '';
      out.coverMark = document.querySelectorAll('.profile-cover .profile-cover-mark').length;
      const cov = document.querySelector('.profile-cover:not(.has-banner)');
      out.coverHasTheme = !!cov && /color-mix|rgb/.test(getComputedStyle(cov).backgroundImage) && !cov.style.getPropertyValue('--card-accent');
      const av = document.querySelector('.profile-hero-avatar');
      out.ring = av ? getComputedStyle(av).boxShadow : '';
      const hex = RANK_COLOR[out.rank]; const n = parseInt(hex.slice(1), 16);
      out.rankRgb = 'rgb(' + (n >> 16) + ', ' + ((n >> 8) & 255) + ', ' + (n & 255) + ')';
      /* 5. the banner pop-up */
      showCustomize('banner'); await wait(500);
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
      store.avatarChar = 'ghost'; showCustomize('character'); await wait(700);
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
    # AND IN 315: the count beside the badge case's strip - which is badge
    # art, by choice ("the mini badge case is nice") - with no ring; the
    # closest unit is the Next rank card's badge task, not the case's.
    check("the badge case says its count over the strip of earned badges - no ring, no unit, no hundos",
          r.get("badgeSvgs", 0) >= 1 and r.get("badgeMedal") == 0 and "hundo" not in r.get("badgeText", "")
          and "of 16" in r.get("badgeText", "") and not r.get("plateBar"), r)
    # REVERSED IN 259: "No no no, the profile change is bad there. I don't
    # like the bronze all the way through." The level is blue again and
    # the default cover is the theme, with no rank on it.
    check("the XP and its bar are blue again, and the cover carries no rank",
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
    # REVISED IN 304: "Take ronin challenge to 500 questions not 450." The
    # size is read off the page (RONIN_TEST_SIZE) and the label must say
    # it - the shape, not the number - and it may never fall below 450.
    check("the Knight and the Night Owl are gone; the Ronin is passing a test of RONIN_TEST_SIZE (500) questions, and an old 400 pass does not count",
          ow.get("feat") == "bigtest400" and ow.get("name") == "Ronin" and ow.get("owlDrawsAs") == "ninja" and ow.get("locked") is True and ow.get("held") is True
          and str(ow.get("size")) in ow.get("label", "") and (ow.get("size") or 0) >= 450 and ow.get("oldRuleLocked") is True and ow.get("parts") is True and ow.get("knightGone") is True and ow.get("knightDrawsAs") == "ninja", ow)
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
      showCustomize('character'); await wait(500);
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
      /* build 315: the plate is the standing block, the level a line in it */
      out.plate = { bar: !!document.querySelector('.pf-standing .pf-bar, .profile-rankplate .profile-rankplate-bar, .profile-rankplate .profile-rankplate-next') };
      const lv = document.querySelector('.pf-standing .pf-level');
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
        bottomBack: !!c.querySelector('.unitdetail-back.is-bottom'), backs: c.querySelectorAll('.unitdetail-back').length,
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
      /* build 315: the plate is the standing block */
      const plate = document.querySelector('.pf-standing');
      out.plateAfter = plate ? getComputedStyle(plate, '::after').content : 'missing';
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    L = r.get("labels") or []
    # REVISED IN 309: five, Best time added.
    check("the unit card is the same five numbers in every mode, the last score and best time among them",
          len(L) == 3 and L[0] == L[1] == L[2] and len(L[0]) == 5 and any("ast" in x for x in L[0])
          and any("time" in x.lower() for x in L[0]), L)
    m = r.get("missed") or {}
    check("there is no Most missed list (build 284), and the Flagged list shows its questions", r.get("recentDoor") == 0 and m.get("choices", 0) > 0, m)
    # build 298: "remove the back button at the very bottom since the other back button is already there"
    check("the Flagged list has one Back, at the top, and none at the bottom", not m.get("bottomBack") and not (r.get("flagged") or {}).get("bottomBack") and m.get("backs") == 1, (m, r.get("flagged")))
    check("Flagged keeps its flags", (r.get("flagged") or {}).get("flags", 0) > 0, r.get("flagged"))
    check("a list's answer choices are read-only, and do not press like buttons", m.get("unlocked") == 0 and not m.get("pressed"), m)
    check("Back from a list puts the card back to its own size", abs((r.get("h1") or 0) - (r.get("h0") or -99)) <= 4, (r.get("h0"), r.get("h1")))
    check("a back link's chevron and word share a centre line", r.get("backOff", 99) <= 1, r.get("backOff"))
    check("no unit badge's drawing leaves its box", r.get("clipped") == [], r.get("clipped"))
    check("the Profile rank block has no white flash", r.get("plateAfter") in ("none", "normal"), r.get("plateAfter"))
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
    print("\n_ver. build 275: the Hacker's round scene, Void restored, the Marksman refined")
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
      /* build 313: a flare's colour is its --fc (the fill attribute lost to the stylesheet) */
      out.dot = { n: dots.length, fills: dots.map(x => (getComputedStyle(x).getPropertyValue('--fc') || x.getAttribute('fill') || '').trim().toUpperCase()) };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    f, d = r.get("flare") or {}, r.get("dot") or {}
    check("the fifth flare is a colour the Singularity is drawn in, and its glow", f.get("inDrawing") and f.get("glow") == f.get("fifth"), f)
    check("it is a real blue, not a near-white", 180 <= (f.get("hue") or 0) <= 230 and (f.get("sat") or 0) >= .6 and (f.get("light") or 1) <= .85, f)
    check("and stays well apart from the fourth flare's violet", (f.get("apart") or 0) >= 40, f)
    # build 313: six flares on Home once the fifth is found (the sixth on the planet)
    check("a found fifth dot on Home paints in it", d.get("n") == 6 and (f.get("fifth") or "?").upper() in (d.get("fills") or []), d)
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
    # Build 311 reversed the first half: "when opening the rank tab each
    # time, you should follow the rank road map progress bar to your rank
    # and then back to the top". Opened with nothing changed it now WALKS
    # (travels and comes back) but does not re-run the climb.
    check("opened with nothing changed, the Rank tab walks down to your progress (build 311) without re-running the climb",
          r.get("recorded") is not None and 0 < r["recorded"] < 1 and r.get("stillMax", 0) > 40 and not r.get("stillClimb"), r)
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
      /* Build 315: the two rings are gone - the level and the badges are
         the Next rank card's two tasks now, in the same two colours */
      const tasks = [...document.querySelectorAll('.pf-goal .pf-task')];
      const tcOf = re => { const t = tasks.find(x => re.test((x.querySelector('.pf-task-label') || {}).textContent || ''));
        return t ? t.style.getPropertyValue('--tc').trim() : null; };
      out.profLevelRing = tcOf(/^Reach level/); out.profBadgeRing = tcOf(/^Earn /);
      out.profRings = tasks.length;
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
    # REVISED IN 315: the rings came off the Profile card with the rebuild
    # (311's "progress ring" check went with them); the level and the
    # badges are the Next rank card's two tasks, and they keep the colours.
    up = lambda v: (v or "").strip().upper()
    check("the Next rank card's level and badge tasks take the Rank tab's level and badge colours",
          r.get("profRings") == 2 and up(r.get("profLevelRing")) == up(r.get("rankLevelRing")) and up(r.get("profBadgeRing")) == up(r.get("rankBadgeRing"))
          and r.get("rankLevelRing") and up(r.get("rankLevelRing")) != up(r.get("rankBadgeRing")), r)
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
    print("\n_ver. build 283: Game mode and the Practice Test retired, their rewards on Exam")
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
      /* build 315: the rank row is the standing block */
      const plate = document.querySelector('.pf-standing');
      if(plate) plate.click(); await wait(900);
      out.rankOpens = !!document.querySelector('.screen-ranks .rankmap-stop');
      out.profileLit = !!document.querySelector('#bottomtab-profile.active');
      out.noteLine = !!document.querySelector('.rankhero-next');
      const back = document.querySelector('.screen-ranks .back-link');
      if(back) back.click(); await wait(900);
      out.backToProfile = !!document.querySelector('.screen-profile');
      /* build 315: the badge row is the badge case */
      const badgeRow = document.querySelector('.screen-profile .pf-case');
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
      /* the pops that went up - the last may still be on screen (build 302) */
      out.pops = pops;
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
      /* REVISED IN 314: the bank is one Starred switch (All is the default) */
      out.banks = document.querySelector('.bank-starred') && !document.querySelector('.bank-opt') ? ['all', 'flagged'] : [...document.querySelectorAll('.bank-opt')].map(r => r.dataset.value);
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
    check("the Profile card's rank block opens the climb, with Profile lit on the bar",
          r.get("rankOpens") is True and r.get("profileLit") is True, (r.get("rankOpens"), r.get("profileLit")))
    check("and its back link goes to Profile", r.get("backToProfile") is True, r.get("backToProfile"))
    check("the badge case opens the badge case", r.get("badgesOpen") is True, r.get("badgesOpen"))
    check("the rank box has no 'N to go until X' line, the badge box no 'Closest' line",
          r.get("noteLine") is False and r.get("closest") is False, (r.get("noteLine"), r.get("closest")))
    # REVERSED IN 302: "Bring back the correct answer streak thing you get
    # during tests." Thirty in a row is the pop at 10 and the pop at 25.
    check("thirty right answers in a row put up the streak pop at 10 and at 25", r.get("pops") == 2, r.get("pops"))
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
    check("Supernova detonates: core, flares, light, cross-flare, blast shell and black fragments on one clock, together",
          # build 314: the black fragments are thrown on the same beat
          names == ["rk-nova-core", "rk-nova-flare", "rk-nova-frag", "rk-nova-halo", "rk-nova-shock", "rk-nova-x"]
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
          /* REVISED IN 314: the two-box bar became one switch row, which
             fills the sheet's column like every other card */
          const l = document.querySelector('.unitoptions-modal-sheet .bank-rows'), lr = l.getBoundingClientRect();
          const col = document.querySelector('.unitoptions-modal-sheet .howmany-sect').getBoundingClientRect();
          out.bank = { inner: Math.round(col.width), used: Math.round(lr.width), n: l.querySelectorAll('.opt').length };
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
        check("%s: the Starred switch row fills the sheet's column (build 314)" % label,
              b.get("n") == 1 and b.get("inner", 0) - b.get("used", 0) <= 12, r.get("bank") or r.get("threw"))
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
        store.practiceExamPerfect = false; store.unitHundoStreak = 0; store.unitHundoStreakBest = 9; out.ph6 = bannerEarned('exam100');
        store.unitHundoStreakBest = 10; out.ph7 = bannerEarned('exam100');
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
        /* Build 315: the three blocks are the standing block, the Next
           rank card and the badge case. Build 316: the standing block is
           no box any more (it reads as part of the profile), so the family
           is the two boxes - and the rank line runs the same width */
        const bl = ['.pf-standing', '.pf-goal', '.pf-case'].map(q => document.querySelector('.profile-hero ' + q));
        if(bl.every(Boolean)){
          const cs = bl.map(b => getComputedStyle(b)), rs = bl.map(b => b.getBoundingClientRect());
          out.box = { radius: cs[1].borderTopLeftRadius === cs[2].borderTopLeftRadius,
            width: rs.every(q => Math.abs(q.width - rs[0].width) < 1), shadow: cs.every(c => c.boxShadow === 'none'),
            unboxed: cs[0].backgroundImage === 'none' && parseFloat(cs[0].borderTopWidth) === 0,
            wm: !document.querySelector('.profile-hero .profile-rankplate-wm') };
        }
        const eb = document.querySelector('.profile-hero .profile-edit-btn');
        out.edit = eb ? parseFloat(getComputedStyle(eb).fontSize) : 0;
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    # REVISED IN 295: Koi Pond is five friends (was every unit, then one
    # unit on ten days in 293, then a Penal Code hundo in 294).
    check("the reworked banners: Midnight Oil 35 hours, Neon City 25 matches, Phoenix 10 units in a row (313), Koi Pond 5 friends",
          r.get("needs") == [35, 25, 10, 5], r)
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
    check("the rank line is no box; the next rank and the badge case are one family: same radius, same width, no glow, no watermark",
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
        showCustomize('character'); await wait(900);
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
        /* Since build 315 the swatches and the banners have pages of their
           own, where most of them are on screen. So each page has a tall
           spacer put in above its grid: the first tile must play where it
           can be seen, pause once it is pushed out of view, and play again
           when the spacer goes - the page's own observer doing all three. */
        const pushOut = async (page, sel) => {
          showCustomize(page); await wait(800);
          const panel = document.querySelector('#stage > .screen-customize'), first = document.querySelector('.screen-customize ' + sel);
          if(!panel || !first) return { missing: true };
          const res = { onBefore: !first.classList.contains('is-offscreen') };
          const sp = document.createElement('div'); sp.style.height = '5000px'; panel.insertBefore(sp, panel.firstChild);
          window.scrollTo({ top: 0, behavior: 'instant' }); await wait(500);
          res.offAfter = first.classList.contains('is-offscreen');
          const dot = first.querySelector('.dot'); if(dot) res.dotPaused = getComputedStyle(dot).animationPlayState;
          sp.remove(); await wait(500);
          res.backOn = !first.classList.contains('is-offscreen');
          return res;
        };
        out.swatch = await pushOut('theme', '.swatch');
        out.banner = await pushOut('banner', '.banner-opt');
        out.offscreen = { swatch: !!(out.swatch.onBefore && out.swatch.offAfter && out.swatch.backOn), banner: !!(out.banner.onBefore && out.banner.offAfter && out.banner.backOn) };
        out.dotPaused = out.swatch.dotPaused === undefined ? null : out.swatch.dotPaused;
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    s = r.get("sync") or {}
    check("a pick lights in the same tap, and saving waits until after the glow",
          s.get("selected") is True and s.get("cell") is True and s.get("savedYet") == 0 and r.get("savedLater") is True, r)
    g = r.get("glow") or {}
    check("the glow comes up in a short ease-out, the pool on its own layer",
          g.get("k") is not None and g["k"] <= 0.25 and g.get("pool") is not None and g["pool"] <= 0.3 and "opacity" in str(g.get("poolLayer")), g)
    check("no :has(.selected) on the character cells", r.get("hasRule") is False, r.get("hasRule"))
    check("Customize pauses the swatches and banner tiles it cannot see, and plays the ones it can",
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
        const note = document.querySelector('.unitoptions-modal-sheet .hundo-chip');
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
    # REVISED IN 311: "When you have the max questions on, that notice
    # beneath it does not need to be there." Nothing at All; the warning
    # is a chip in the How many row, so it still moves nothing.
    check("on All, there is no hundo note at all",
          na and na.get("hidden"), na)
    check("a touch on the track away from the thumb moves the count, first time, from All",
          r.get("sizeBefore") == 0 and 0 < (r.get("sizeAfter") or 0) < 12, [r.get("sizeBefore"), (r.get("midDrag") or {}).get("size"), r.get("sizeAfter")])
    st = r.get("slTop") or [0, 1]
    check("the slider does not move while it is dragged below All, and the No hundo chip shows",
          st[0] == st[1] == (r.get("midDrag") or {}).get("top") and not npart.get("hidden") and "hundo" in npart.get("text", "").lower(),
          [st, (r.get("midDrag") or {}).get("top"), na.get("h"), npart.get("h")])
    txt = r.get("sheetText") or ""
    check("the options say 'answer choices', and the timers say what they do",
          all(s in txt for s in ["Shuffle answer choices", "Hide answer choices", "Time limit", "Stopwatch"])
          and "Track my time" not in txt, txt[:300])
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


def check_b295(br):
    """Build 295: "Naw get a hundo on the penal code is not a good one.
    Change it. If someone unlocked, remove that unlock. Remove it so they
    don't get the pop up either." Koi Pond is five friends, picked from a
    list. A Penal Code hundo no longer earns it; anyone shown the 294
    unlock has that record cleared once and stops wearing it; the friend
    count keeps its best so the banner does not flicker locked before the
    rankings load. Written against 294, where it fails."""
    print("\n64. build 295: Koi Pond is five friends; 294's unlock taken back")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const out = {};
      try{
        document.getElementById('pushing-update')?.remove();
        const b = BANNERS.find(x => x.id === 'tests500');
        out.label = b.label; out.need = b.need;
        const ids = n => Array.from({ length: n }, (_, i) => 'pub-test-' + i);
        store.friendsBest = 0; leaderboardRows = [];
        store.unitPerfects = Object.assign({}, store.unitPerfects, { 'Penal Code': 3 });
        store.friendsIn = ids(4); out.four = bannerEarned('tests500');
        store.friendsIn = ids(5); out.five = bannerEarned('tests500');
        store.friendsIn = []; out.kept = bannerEarned('tests500');
        /* 294's unlock, taken back once */
        store.friendsBest = 0;
        store.unlocksShown = { chars: [], banners: ['tests500', 'tests100'] };
        store.banner = 'tests500'; store.koiRevoked295 = false;
        seedChallenges289();
        out.revoked = { shown: store.unlocksShown.banners.slice(), banner: store.banner, flag: store.koiRevoked295 };
        /* build 296: not just once - while it is not held, a "shown"
           record arriving from another device is cleared too */
        store.unlocksShown.banners.push('tests500'); store.koiRevoked295 = true; seedChallenges289();
        out.once = store.unlocksShown.banners.indexOf('tests500') < 0;
        /* and once it IS held, the record of its pop-up stays */
        store.friendsBest = 5; markUnlocksShown([], ['tests500']); seedChallenges289();
        out.heldStays = store.unlocksShown.banners.indexOf('tests500') >= 0;
        out.pending = (pendingHomeUnlocks().banners || []).indexOf('tests500') >= 0;
        const d = JSON.parse(JSON.stringify(store)); delete d.koiRevoked295; delete d.friendsBest;
        applyLoadedData(d); out.defaulted = [store.koiRevoked295, store.friendsBest];
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    if r.get("threw"):
        print("   threw:", r["threw"][:400])
    check("Koi Pond says one simple thing: add 5 friends", r.get("label") == "Add 5 friends" and r.get("need") == 5, [r.get("label"), r.get("need")])
    check("four friends and a Penal Code hundo do not earn it; five do", r.get("four") is False and r.get("five") is True, [r.get("four"), r.get("five")])
    check("it keeps the best count, so it does not flicker locked while the rankings load", r.get("kept") is True, r.get("kept"))
    rv = r.get("revoked") or {}
    check("294's unlock is taken back: no longer recorded as shown, no longer worn",
          rv.get("shown") == ["tests100"] and rv.get("banner") == "" and rv.get("flag") is True, rv)
    check("while Koi Pond is not held, a 'shown' record from any device is cleared, and no pop-up is queued",
          r.get("once") is True and r.get("pending") is False, [r.get("once"), r.get("pending")])
    check("once it is really earned, its pop-up record stays", r.get("heldStays") is True, r.get("heldStays"))
    check("an account from an older build is defaulted unrevoked, with no friends on record",
          r.get("defaulted") == [False, 0], r.get("defaulted"))
    ctx.close()


def check_b297(br):
    """Build 297.
    "When in the test start menu in review, swiping down opens up the
    test": the sheet's swipe-down dismiss went on to open the answer
    review. Now it only closes.
    "Maybe it should be a unit card box kinda but it'd be double wide and
    it'd be at the top", and "do not display the amount of flagged
    questions on a unit card": a Flagged questions box spanning the
    grid, first on Review; the unit cards are untouched.
    "You should be able to see the flagged button similar to how it's
    displayed in a test ... it's the same one app wide": the test's
    round flag on every question in Answer Review and in a unit's
    Flagged list.
    "I'm pretty sure all my flagged questions disappeared": flags merge
    across devices, flag and unflag both stamped.
    "The pause menu ... still not centered": one column of equal-width
    buttons, the group on the screen's own middle.
    Written against 296, where all of it fails."""
    print("\n65. build 297: swipe-down closes, the Flagged box, one flag app wide, flags survive a second device, pause centred")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        document.getElementById('pushing-update')?.remove(); store.seenUnitSelectTour = true; store.seenUnitOptionsTour = true;
        store.flagged = {}; store.unflagged = {};
        const all = topicsIn(QUESTIONS), A = all[0], B = all[2];
        const ofU = u => QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === u);
        const want = ofU(A).slice(0, 2).concat(ofU(B).slice(0, 1));
        want.forEach(i => toggleFlag(i));

        /* 1. the Flagged box: first in the grid, both columns wide */
        cfg.mode = 'review'; cfg.units = []; cfg.source = 'all'; showSetup(); await wait(600);
        const grid = document.querySelector('.screen-setup .picks');
        const box = grid && grid.querySelector('.pick-flagged-all');
        const cards = [...grid.querySelectorAll('.pick:not(.pick-flagged-all):not(.pick-tba)')];
        out.box = box ? { first: grid.firstElementChild === box, text: box.textContent,
          wide: Math.abs(box.getBoundingClientRect().width - grid.getBoundingClientRect().width) < 2 } : null;
        out.cardCounts = cards.map(c => (c.querySelector('.pcount') || {}).textContent).filter(t => /flag/i.test(t || ''));
        out.oldUi = !!document.querySelector('.review-flagged-card, .review-bank');

        /* 2. Start -> the sheet; swipe it down: it closes, nothing opens */
        const pick = cards[0].querySelector('input'); pick.click(); await wait(200);
        const startBtn = [...document.querySelectorAll('button')].find(b => /^Start/.test(b.textContent.trim()) && b.offsetParent);
        startBtn.click(); await wait(400);
        const modal = document.getElementById('unitoptions-modal');
        const sheet = modal.querySelector('.unitoptions-modal-sheet');
        out.sheetOpen = !modal.hidden;
        const mk = (y) => new Touch({ identifier: 7, target: sheet, clientX: 200, clientY: y });
        const fire = (type, y, list) => sheet.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true,
          touches: list ? [mk(y)] : [], targetTouches: list ? [mk(y)] : [], changedTouches: [mk(y)] }));
        sheet.scrollTop = 0;
        fire('touchstart', 300, true);
        for(let y = 310; y <= 520; y += 30) fire('touchmove', y, true);
        fire('touchend', 520, false);
        await wait(700);
        out.afterSwipe = { closed: modal.hidden, screen: document.querySelector('.screen-answerreview') ? 'review' : (document.querySelector('.screen-setup') ? 'setup' : 'other') };
        modal.hidden = true;

        /* 3. the box opens exactly the flagged ones, each with the test's flag, on */
        /* build 314: through LOADING REVIEW first */
        document.querySelector('.pick-flagged-all').click(); await wait(200); while(document.getElementById('teststart-overlay')) await wait(30); await wait(300);
        const qs = [...document.querySelectorAll('.screen-answerreview .review-question')];
        out.list = { n: qs.length, all: want.every(i => qs.some(q => q.querySelector('.review-question-text').textContent === QUESTIONS[i].q)),
                     title: (document.querySelector('.screen-answerreview .ar-head-title') || {}).textContent,
                     flags: qs.map(q => { const f = q.querySelector('.flagbtn.qflag'); return f ? f.classList.contains('on') : null; }) };
        /* unflag one there: it is unflagged, and stays on screen dimmed */
        const first = qs[0], ftext = first.querySelector('.review-question-text').textContent;
        const fi = QUESTIONS.findIndex(x => x.q === ftext);
        first.querySelector('.flagbtn.qflag').click(); await wait(200);
        out.unflagHere = { flagged: isFlagged(fi), dimmed: first.classList.contains('is-unflagged'), still: first.isConnected };
        toggleFlag(fi);

        /* 4. any unit's review: every question has the flag, and a flagged one shows on */
        showAnswerReview([A], 'all', {}); await wait(600);
        const uq = [...document.querySelectorAll('.screen-answerreview .review-question')];
        out.unitReview = { n: uq.length, withFlag: uq.filter(q => q.querySelector('.flagbtn.qflag')).length,
          on: uq.filter(q => (q.querySelector('.flagbtn.qflag') || {classList:{contains:()=>false}}).classList.contains('on')).length };
        /* flag one from here */
        const off = uq.find(q => !q.querySelector('.flagbtn.qflag').classList.contains('on'));
        const offi = QUESTIONS.findIndex(x => x.q === off.querySelector('.review-question-text').textContent);
        off.querySelector('.flagbtn.qflag').click(); await wait(100);
        out.flagFromReview = isFlagged(offi);
        toggleFlag(offi);

        /* 5. flags survive a second device that has none */
        const other = JSON.parse(JSON.stringify(store));
        other.flagged = {}; other.unflagged = {}; other.lastModified = Date.now() + 60000;
        syncSameAccount(other);
        out.keptOnNewerEmpty = want.every(i => isFlagged(i));
        const k = KEYS[want[0]];
        const dev2 = JSON.parse(JSON.stringify(store));
        setFlag(want[0], false);
        mergeSameAccount(store, dev2);
        out.unflagHolds = !isFlagged(want[0]);
        const dev3 = JSON.parse(JSON.stringify(store)); dev3.flagged[k] = Date.now() + 5000; delete dev3.unflagged[k];
        mergeSameAccount(store, dev3);
        out.reflagWins = isFlagged(want[0]);
        const dev4 = { flagged: { [KEYS[want[2]]]: true } }; store.flagged = {}; store.unflagged = {};
        mergeSameAccount(store, dev4);
        out.legacy = isFlagged(want[2]);
        const again = mergeSameAccount(store, JSON.parse(JSON.stringify(store)));
        out.converges = !again.gained && !again.otherHadLess;
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    if r.get("threw"):
        print("   threw:", r["threw"][:400])
    bx = r.get("box") or {}
    check("Review's grid opens with a Flagged questions box, first and full width",
          bx.get("first") is True and bx.get("wide") is True and "3 questions" in bx.get("text", "") and r.get("oldUi") is False, {**bx, "oldUi": r.get("oldUi")})
    check("no unit card says how many are flagged", r.get("cardCounts") == [], r.get("cardCounts"))
    sw = r.get("afterSwipe") or {}
    check("swiping the Review start sheet down closes it and opens nothing",
          r.get("sheetOpen") is True and sw.get("closed") is True and sw.get("screen") == "setup", sw)
    ls = r.get("list") or {}
    check("the box lists exactly the flagged questions, each with the test's flag, on",
          ls.get("n") == 3 and ls.get("all") and (ls.get("title") or "").lower() in ("flagged questions", "starred questions") and ls.get("flags") == [True, True, True], ls)
    uh = r.get("unflagHere") or {}
    check("unflagging there takes the flag off and leaves the question, dimmed",
          uh.get("flagged") is False and uh.get("dimmed") is True and uh.get("still") is True, uh)
    ur = r.get("unitReview") or {}
    check("a unit's Answer Review has the flag on every question, on where flagged",
          ur.get("n", 0) > 0 and ur.get("withFlag") == ur.get("n") and ur.get("on") == 2, ur)
    check("a question can be flagged from Answer Review", r.get("flagFromReview") is True, r.get("flagFromReview"))
    check("flags survive a newer device that has none", r.get("keptOnNewerEmpty") is True, r.get("keptOnNewerEmpty"))
    check("an unflag is not undone by another device's older flag", r.get("unflagHolds") is True, r.get("unflagHolds"))
    check("a flag made after that unflag wins", r.get("reflagWins") is True, r.get("reflagWins"))
    check("a legacy flag (true) still merges in", r.get("legacy") is True, r.get("legacy"))
    check("the flag merge converges", r.get("converges") is True, r.get("converges"))
    ctx.close()

    # the unit-details Flagged list uses the same round flag, and pause is centred - both reference sizes
    for w, h in [(440, 956), (834, 1194)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
            document.getElementById('pushing-update')?.remove();
            cfg.mode = 'drill'; cfg.units = [topicsIn(QUESTIONS)[0]]; cfg.source = 'all';
            beginRun(QUESTIONS.map((q, i) => i).filter(inUnits).slice(0, 10), null);
            for(let k = 0; k < 40 && !document.querySelector('.choice'); k++) await wait(200);
            const tf = document.querySelector('.qnumrow > .flagbtn');
            out.testFlag = tf ? tf.classList.contains('qflag') : null;
            pauseRun(); await wait(800);
            const st = document.querySelector('.pause-stack');
            const s = st && st.getBoundingClientRect();
            const bs = [...document.querySelectorAll('.pausepanel .actions button')].map(b => b.getBoundingClientRect());
            out.pause = s ? { off: Math.round(Math.abs((s.top + s.height / 2) - innerHeight / 2)),
              stacked: bs.length === 2 && bs[1].top > bs[0].bottom - 1,
              sameWidth: bs.length === 2 && Math.abs(bs[0].width - bs[1].width) < 1,
              centred: bs.every(b => Math.abs((b.left + b.width / 2) - innerWidth / 2) < 2) } : null;
            /* the exit confirmation puts its buttons exactly where Pause's were */
            /* UNROUNDED, within half a pixel (build 308). Both screens centre
               their stack, so the buttons land on fractional pixels; a
               0.14px difference rounded 564.49 and 564.63 to two different
               integers and failed a move nobody can see. A real move is
               whole pixels and still fails. */
            const at = () => [...document.querySelectorAll('.pausepanel .actions button')].map(b => { const q = b.getBoundingClientRect(); return [+q.left.toFixed(2), +q.top.toFixed(2), +q.width.toFixed(2)]; });
            const before = at();
            [...document.querySelectorAll('.pausepanel button')].find(b => /Exit/.test(b.textContent)).click(); await wait(800);
            const conf = at();
            out.confirm = { title: (document.querySelector('.pausepanel .qnum') || {}).textContent, before, conf,
              same: before.length === conf.length && before.every((p, i) => p.every((v, j) => Math.abs(v - conf[i][j]) < 0.5)) };
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        if r.get("threw"):
            print("   threw:", r["threw"][:300])
        check("%dx%d: the test's flag is the shared one" % (w, h), r.get("testFlag") is True, r.get("testFlag"))
        pz = r.get("pause") or {}
        check("%dx%d: pause buttons stacked, one width, centred, the group on the screen's middle" % (w, h),
              pz.get("stacked") and pz.get("sameWidth") and pz.get("centred") and pz.get("off", 99) <= 6, pz)
        cf = r.get("confirm") or {}
        check("%dx%d: the exit confirmation's buttons sit exactly where Pause's do" % (w, h),
              cf.get("same") is True and "Exit" in str(cf.get("title")), cf)
        ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      document.getElementById('pushing-update')?.remove(); store.seenUnitSelectTour = true; store.seenUnitHoldTip = true;
      store.flagged = {}; const A = topicsIn(QUESTIONS)[0];
      QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === A).slice(0, 2).forEach(i => toggleFlag(i));
      cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(600);
      const row = [...document.querySelectorAll('.screen-setup .pick')].find(r => r.querySelector('.pname') && r.querySelector('.pname').textContent === A);
      row.scrollIntoView({ block: 'center' }); await wait(300); }""")
    box = pg.evaluate("""()=>{ const A = topicsIn(QUESTIONS)[0];
      const row = [...document.querySelectorAll('.screen-setup .pick')].find(r => r.querySelector('.pname') && r.querySelector('.pname').textContent === A);
      const b = row.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }""")
    pg.mouse.move(*box); pg.mouse.down(); pg.wait_for_timeout(900); pg.mouse.up(); pg.wait_for_timeout(800)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      const d = [...document.querySelectorAll('button')].find(b => /Flagged|[Ss]tarred/.test(b.textContent) && b.offsetParent && b.closest('[class*=unitdetail]'));
      d && d.click(); await wait(700);
      const fl = [...document.querySelectorAll('.unitdetail-q .flagbtn')];
      return { n: fl.length, shared: fl.every(f => f.classList.contains('qflag') && f.classList.contains('on')),
               besideText: fl.every(f => f.parentElement.classList.contains('review-qhead')) }; }""")
    check("a unit's Flagged list uses the same round flag, beside each question",
          r.get("n") == 2 and r.get("shared") and r.get("besideText"), r)
    ctx.close()


def check_b298(br):
    """Build 298.
    "The animations of the rank icons in the flare bubbles isn't happening
    anymore ... ensure there is not lag": each reached rank's motion is
    recorded once and played as a stepped flip-book the compositor runs -
    no repaint and no script per frame. "The flag icon within the small
    yellow circle is not centered", "just the flag icon there without the
    circle", "remove the back button at the very bottom", "the remove all
    flagged questions ... actually looks like a button".
    Written against 297, where all of it fails."""
    print("\n66. build 298: rank emblems move again, compositor-only; flag centred; Flagged box and list polish")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=2)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
            document.getElementById('pushing-update')?.remove();
            store.lifetime.points = 300000; topicsIn(QUESTIONS).forEach(u => store.unitPerfects[u] = 40);
            store.pendingBadgeUnlocks = []; theme.muteBanners = true; showHome();
            const lit = () => document.querySelectorAll('.cosmic-badge-rank.cosmic-badge-lit').length;
            /* 90s, not 30 (build 314): the recorder steps aside for input and
               runs in short slices, so on a loaded test machine it takes
               longer - the property is that every one plays, not how soon */
            for(let i = 0; i < 900 && document.querySelectorAll('.cosmic-rank-anim').length < lit(); i++) await wait(100);
            const wraps = [...document.querySelectorAll('.cosmic-rank-anim')];
            out.lit = lit(); out.playing = wraps.length;
            /* one animation on one image since build 300 (two clocks drifted) */
            out.running = wraps.every(wr => { const im = wr.querySelector('img');
              const a = [...wr.querySelectorAll('*')].flatMap(e => e.getAnimations()); return !!im && a.length === 1 && a.every(x => x.playState === 'running'); });
            out.svgHidden = wraps.every(wr => getComputedStyle(wr.previousElementSibling).visibility === 'hidden');
            out.aligned = wraps.every(wr => { const a = wr.getBoundingClientRect(), b = wr.parentElement.getBoundingClientRect();
              return Math.abs(a.left - b.left) < 1.5 && Math.abs(a.width - b.width) < 3; });
            /* moving changes what is on screen, with no script per frame */
            out.raf = typeof orbitAnimTick === 'function';
            /* the flag in its round button: drawn on the button's centre */
            cfg.mode = 'drill'; const qf = buildQuestionFlag(0); qf.style.cssText = 'position:fixed;left:40px;top:40px'; document.body.appendChild(qf); await wait(50);
            const bb = qf.getBoundingClientRect(); let L = 1e9, T = 1e9, R = -1e9, B = -1e9;
            qf.querySelectorAll('path').forEach(p => { const r = p.getBoundingClientRect(); L = Math.min(L, r.left); T = Math.min(T, r.top); R = Math.max(R, r.right); B = Math.max(B, r.bottom); });
            out.flagOff = [Math.round(((L + R) / 2 - (bb.left + bb.right) / 2) * 10) / 10, Math.round(((T + B) / 2 - (bb.top + bb.bottom) / 2) * 10) / 10];
            qf.remove();
            /* Review's Flagged box: the flag, no circle */
            store.flagged = {}; store.unflagged = {};
            const all = topicsIn(QUESTIONS), A = all[0];
            QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === A && Object.keys(store.flagged).length < 3) toggleFlag(i); });
            cfg.mode = 'review'; cfg.units = []; cfg.source = 'all'; showSetup(); await wait(600);
            const ic = document.querySelector('.pick-flagged-all .pick-flagged-icon');
            const cs = ic && getComputedStyle(ic);
            out.icon = ic ? { bg: cs.backgroundColor, shadow: cs.boxShadow, radius: cs.borderRadius, glyph: !!ic.querySelector('svg') } : null;
            /* a unit's Flagged list: one Back, and a real Unflag button */
            cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(600);
            const row = [...document.querySelectorAll('.pick')].find(r => (r.querySelector('input') || {}).value === A);
            row.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 50, clientY: 50, button: 0 }));
            await wait(600); row.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 50, clientY: 50 })); await wait(900);
            document.querySelector('.unitdetail-door.is-flagged').click(); await wait(900);
            const card = document.querySelector('.unitdetail');
            out.backs = card.querySelectorAll('.unitdetail-back').length;
            out.bottomBack = !!card.querySelector('.unitdetail-back.is-bottom');
            const rb = card.querySelector('.unitdetail-resetbtn'), lst = card.querySelector('.unitdetail-listscroll');
            const rcs = getComputedStyle(rb), rr = rb.getBoundingClientRect(), lr = lst.getBoundingClientRect();
            out.reset = { h: Math.round(rr.height), wideFrac: Math.round(rr.width / (lr.width - 2 * 17.6) * 100) / 100,
              solid: /gradient/.test(rcs.backgroundImage), color: rcs.color, radius: rcs.borderRadius, text: rb.textContent };
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: no error", not r.get("threw"), r.get("threw", ""))
        check(f"{dev}: every reached rank's emblem moves again in its bubble",
              r.get("lit", 0) > 0 and r.get("playing") == r.get("lit") and r.get("running") and r.get("svgHidden") and r.get("aligned"), r)
        check(f"{dev}: and it is played by the compositor - no per-frame script", not r.get("raf"), r.get("raf"))
        fo = r.get("flagOff") or [9, 9]
        check(f"{dev}: the flag is drawn on its round button's centre (within 1px)", abs(fo[0]) <= 1 and abs(fo[1]) <= 1, fo)
        ic = r.get("icon") or {}
        check(f"{dev}: Review's Flagged box shows the flag with no circle round it",
              ic.get("glyph") and ic.get("bg") in ("rgba(0, 0, 0, 0)", "transparent") and ic.get("shadow") == "none", ic)
        check(f"{dev}: a unit's Flagged list has one Back, at the top", r.get("backs") == 1 and not r.get("bottomBack"), (r.get("backs"), r.get("bottomBack")))
        rs = r.get("reset") or {}
        check(f"{dev}: Unflag every question is a real button: full width, solid, 48px+",
              rs.get("h", 0) >= 48 and rs.get("wideFrac", 0) >= .95 and rs.get("solid"), rs)
        ctx.close()
    # "Daily question, the best time thing in the top right needs to go"
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      document.getElementById('pushing-update')?.remove();
      cfg.timer = 'up'; store.dailyQuestionDate = null; showHome(); await wait(700);
      const k = 'Daily question'; Object.keys(store.testStats || {}).forEach(x => { store.testStats[x].bestMs = 4000; });
      document.querySelector('.daily-question-fab').click(); await wait(2500);
      const tl = document.getElementById('timerline') || (typeof timerlineEl !== 'undefined' ? timerlineEl : null);
      const vis = el => !!el && !el.hidden && el.getBoundingClientRect().width > 0;
      return { daily: runLabel, timerShown: vis(timerlineEl), bestShown: vis(tbestEl), bestText: tbestEl.textContent }; }""")
    check("the daily question has no clock and no best time, even with the test timer on",
          r.get("daily") == "Daily question" and not r.get("timerShown") and not r.get("bestShown"), r)
    ctx.close()
    # "ensure even when on shuffle the answer choices aren't mixed" - a choice that points at others
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{ const out = {};
      const find = (t, src) => QUESTIONS.findIndex(q => (q.topic || '').trim() === t && q.src === src);
      cfg.shuffle = true; runMode = 'drill';
      const refers = i => typeof choicesReferToEachOther === 'function' ? choicesReferToEachOther(i) : !!QUESTIONS[i].fixedOrder;
      const order20 = qi => { const seen = new Set(); for(let k = 0; k < 20; k++){ delete layout[qi]; seen.add(optionOrder(qi).join(',')); } return [...seen]; };
      const both = find('Penal Code', 213);              /* "Both A & B" */
      out.both = { text: QUESTIONS[both].choices.join(' | '), orders: order20(both) };
      const above = QUESTIONS.findIndex(q => (q.choices || []).some(c => /^all of the above$/i.test(c)));
      out.above = order20(above);
      const prose = find('Professional Policing', 17);   /* "All elements of the criminal justice system" is a plain answer */
      out.prose = order20(prose).length;
      const plain = QUESTIONS.findIndex(q => (q.choices || []).length === 4 && !refers(QUESTIONS.indexOf(q)));
      out.plain = order20(plain).length;
      runMode = 'exam'; cfg.shuffle = false; out.exam = order20(both);
      out.count = QUESTIONS.filter((q, i) => refers(i)).length;
      /* "the all of the above answer should always be at the bottom" - "Any of the above", "A or B", "All are true" too */
      runMode = 'drill'; cfg.shuffle = true;
      const pointer = /\\b(above|listed)\\b|^all are (true|correct)$/i, letter = /(^|[\\s(])[A-E]\\s*(,\\s*[A-E]\\s*,?\\s*)?(&|and|or|nor)\\s*[A-E](\\b|$)/i;
      /* a choice naming letters ("A or B", "a and b are correct") holds the bank's order exactly */
      out.moved = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].choices || []).some(c => letter.test(c)))
        .filter(i => { for(let k = 0; k < 6; k++){ delete layout[i]; if(optionOrder(i).some((v, j) => v !== j)) return true; } return false; })
        .map(i => QUESTIONS[i].topic + ' ' + QUESTIONS[i].src);
      out.astray = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].choices || []).some(c => pointer.test(c)) && !(QUESTIONS[i].choices || []).some(c => letter.test(c)))
        .filter(i => { for(let k = 0; k < 6; k++){ delete layout[i]; const o = optionOrder(i), ch = QUESTIONS[i].choices;
          const last = o.map(x => pointer.test(ch[x])); const first = last.indexOf(true);
          if(first < 0 || last.slice(first).some(v => !v)) return true; } return false; })
        .map(i => QUESTIONS[i].topic + ' ' + QUESTIONS[i].src);
      /* "always feels like questions are around the same area of a test and answer choices aren't always shuffled well" */
      const pen = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === 'Penal Code');
      const sig = i => (QUESTIONS[i].choices || []).map(c => c.toLowerCase().replace(/[^a-z0-9]/g, '')).sort().join('|');
      let near = 0, twins = 0; const R = 40;
      for(let r = 0; r < R; r++){
        const o = freshOrder(pen);
        for(let k = 1; k < o.length; k++){
          if(Math.abs(QUESTIONS[o[k]].src - QUESTIONS[o[k - 1]].src) <= 3) near++;
          for(let j = Math.max(0, k - 20); j < k; j++) if(sig(o[j]) === sig(o[k])) twins++;
        }
      }
      out.near = near / R; out.twins = twins / R;
      /* build 313: the slides 55-124 version carries three deliberate repeats
         and five questions on one answer set ("which offense is this") */
      const ver = pen.filter(i => inChosenVersion(i, { 'Penal Code': 'test' }));
      let repMin = 1e9, sideBySide = 0;
      for(let r = 0; r < R; r++){
        const o = freshOrder(ver), at = {};
        o.forEach((qi, k) => { const s = sig(qi);
          if(at[s] != null){ if(k - at[s] === 1) sideBySide++;
            const q = QUESTIONS[qi], twin = QUESTIONS[o[at[s]]];
            if(q.repeatOf === twin.src || twin.repeatOf === q.src) repMin = Math.min(repMin, k - at[s]); }
          at[s] = k; });
      }
      out.verRepMin = repMin; out.verSideBySide = sideBySide;
      let stay2 = 0, n4 = 0; const slots = [0, 0, 0, 0];
      pen.forEach(i => { if(refers(i) || QUESTIONS[i].choices.length !== 4) return;
        for(let t = 0; t < 8; t++){ delete layout[i]; const o = optionOrder(i); n4++;
          if(o.filter((v, j) => v === j).length >= 2) stay2++; slots[o.indexOf(QUESTIONS[i].answer)]++; } });
      out.stay2 = stay2 / n4; out.slots = slots.map(x => +(x / n4).toFixed(3));
      return out; }""")
    # BUILD 312 changed the decision this encoded: a question with a
    # pointing choice is no longer frozen whole ("the answer choices still
    # aren't being properly shuffled"). The pointing choice stays where it
    # is and still means the same choices; section 86 proves that across
    # the whole bank. What is asserted here is that shape, on the two
    # questions this section was written about.
    # BUILD 313 moved it again: "Both A & B" no longer pins A and B - all
    # three ordinary choices shuffle and its letters are rewritten to
    # follow them (section 97 proves they name the same two). What stays
    # is the pointing choice in its own place, and real movement.
    # REVISED 6 Oct, by instruction: these questions keep the study
    # guide's EXACT order, shuffled or not - builds 312-313 are undone.
    guide = lambda os: os == ["0,1,2,3"]
    check("a question whose choices name other letters (\"Both A & B\") shows the study guide's exact order, on shuffle and in an exam",
          guide(r["both"]["orders"]) and guide(r["exam"]), r["both"])
    check("one with \"All of the above\" shows the study guide's exact order on shuffle", guide(r["above"]), r["above"])
    check("a plain question, and one whose answer only starts with \"All\", still shuffle", r["plain"] > 1 and r["prose"] > 1, (r["plain"], r["prose"]))
    check("about a hundred questions in the bank are held in order", 90 <= r["count"] <= 130, r["count"])
    # REVISED 6 Oct: exact guide order outranks "always at the bottom" -
    # the one guide question with "All the listed" third keeps it third
    check("on shuffle, an \"of the above\" / \"All the listed\" / \"All are true\" choice stays exactly where the study guide puts it",
          r["astray"] == ["Sexual Assault and Family Violence 41"] or r["astray"] == [], r["astray"])
    check("a shuffled run never puts two questions from the same stretch of the guide side by side, or a repeated question near its twin",
          r["near"] < 0.5 and r["twins"] < 0.5, (r["near"], r["twins"]))
    check("the Penal slides 55-124 version: a repeated question is 15 or more questions from its twin, and no two on one answer set are ever side by side",
          r["verRepMin"] >= 15 and r["verSideBySide"] == 0, (r["verRepMin"], r["verSideBySide"]))
    check("a shuffled question leaves at most one choice where the guide had it, and the answer still lands on every letter about equally",
          r["stay2"] == 0 and all(0.2 <= s <= 0.3 for s in r["slots"]), (r["stay2"], r["slots"]))
    check("and one whose choices name letters (\"A or B\", \"a and b are correct\") never moves (6 Oct: exact study guide order)",
          r["moved"] == [], r["moved"])
    ctx.close()
    # "this one ... said at the top that it's a duplicate.. remove that stuff"
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{ const bad = /quizlet|googled|https?:|duplicate\\)|deleted #|wrong subject|left because|\\(#\\d+\\)|^\\d{1,3}\\.\\s|\\(inserted\\)/i;
      /* "(#10)" is a real citation in a reference line ("PC 42.01 (a) (#10)"); in the question itself it is a note */
      const inText = /\\(#\\d+\\)/;
      const notes = QUESTIONS.map((q, i) => i).filter(i => bad.test(QUESTIONS[i].q) || inText.test(QUESTIONS[i].q) || bad.test((QUESTIONS[i].ref || '').replace(/\\(#\\d+\\)/g, '')) || (QUESTIONS[i].choices || []).some(c => bad.test(c)))
        .map(i => QUESTIONS[i].topic + ' ' + QUESTIONS[i].src);
      const edited = QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].keyText != null);
      const keep = edited.every(i => KEYS[i] === (QUESTIONS[i].topic || '') + '|' + QUESTIONS[i].src + '|' + hashOf(String(QUESTIONS[i].keyText) + '\\u0001' + QUESTIONS[i].choices.join('\\u0001')));
      const boat = QUESTIONS.find(q => (q.topic || '').trim() === 'Penal Code' && q.src === 239);
      return { notes, edited: edited.length, keep, boat: boat && boat.q.slice(0, 40) }; }""")
    check("no question carries an editing note: no \"duplicate\", no Quizlet or Googled source, no links, no stray numbers",
          r["notes"] == [] and r["boat"].startswith("Two friends"), r)
    check("and a question whose wording was cleaned keeps its identity, so nobody's history or flags on it move",
          r["edited"] >= 6 and r["keep"], (r["edited"], r["keep"]))
    # "that circled stuff should [be] the same way all the other questions are where it's sitting under the question"
    tails = pg.evaluate("""()=>{ const cite = /(\\((PC|CCP|FC|CPRC|Sec\\.?|Section|US &|Victims of|Sexual|Civil)[ ,][^?]{0,140}|\\bPC \\d+\\.\\d+[^?]{0,60}\\))\\s*[,;]?\\s*$/;
      return QUESTIONS.map((q, i) => i).filter(i => cite.test(QUESTIONS[i].q)).map(i => QUESTIONS[i].topic + ' ' + QUESTIONS[i].src); }""")
    check("no question ends in its own citation: the source sits in the grey line under it, like every other question",
          tails == [], tails)
    ctx.close()
    # "the flag button in tests is a little too low still ... perfectly in the corner" - on a phone and a tablet alike
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11"), (1024, 1366, "iPad Pro 12.9")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
          document.getElementById('pushing-update')?.remove();
          cfg.mode = 'drill'; cfg.units = ['Penal Code']; cfg.source = 'all';
          beginRun(poolNow().slice(0, 10), null); await wait(4200);
          const f = document.querySelector('.qnumrow > .flagbtn.qflag').getBoundingClientRect();
          const line = document.getElementById('count').getBoundingClientRect();
          const qt = document.querySelector('.qnumrow').nextElementSibling.getBoundingClientRect();
          return { underLine: Math.round(f.top - line.bottom), rightOff: Math.round(f.right - line.right), toQuestion: Math.round(qt.top - f.bottom) }; }""")
        check(f"{dev}: the test's flag sits in the corner under the line - 6-14px below it, flush with its end, clear of the question",
              6 <= r["underLine"] <= 14 and abs(r["rightOff"]) <= 2 and r["toQuestion"] >= 16, r)
        ctx.close()
    # "if it's in that version, it also needs to be in the entire unit ... every single question from the guide"
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""()=>{ const all = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === 'Penal Code');
      /* the WHOLE unit, as a run draws it (build 300: a repeat is the short version's only) */
      cfg.mode = 'drill'; cfg.units = ['Penal Code']; cfg.source = 'all'; cfg.versions = {};
      const pc = poolNow();
      const srcs = pc.map(i => QUESTIONS[i].src);
      const v = all.filter(i => inChosenVersion(i, { 'Penal Code': 'test' }));
      const reps = QUESTIONS.filter(q => q.topic === 'Penal Code' && q.repeatOf != null);
      const twice = {}; [213, 128, 183].forEach(s => { const t = QUESTIONS.find(q => q.topic === 'Penal Code' && q.src === s).q; twice[s] = v.filter(i => QUESTIONS[i].q === t).length; });
      const days = []; for(let d = 0; d < 400; d++){ const k = new Date(2026, 9, 1 + d); days.push(dailyQuestionIndexFor(k.getFullYear() + '-' + String(k.getMonth() + 1).padStart(2, '0') + '-' + String(k.getDate()).padStart(2, '0'))); }
      return { n: pc.length, srcs, size: unitQuestionCount('Penal Code'), version: v.length,
               versionIn: v.every(i => pc.indexOf(i) >= 0 || QUESTIONS[i].repeatOf != null), twice,
               repeatsOnlyHere: reps.every(q => q.versionOnly === true),
               keysUnique: new Set(all.map(i => KEYS[i])).size === all.length,
               repeatLast: QUESTIONS.slice(-reps.length).every(q => q.repeatOf != null),
               dailyRepeat: days.some(i => QUESTIONS[i] && QUESTIONS[i].repeatOf != null) }; }""")
    guide = [n for n in range(1, 347) if n not in (122, 137, 148, 237, 256, 258)]
    # Build 300: "remove it from the entire unit one, the entire unit one
    # should be 340 questions not 341" - a repeat is the short version's only.
    check("the whole Penal Code unit is exactly the study guide's 340 questions - no repeat in it",
          r["n"] == 340 and sorted(r["srcs"]) == guide and not ({347, 348, 349, 350} & set(r["srcs"])) and r["size"] == 340, (r["n"], len(r["srcs"]), r["size"]))
    check("the slides 55-124 version is the deck's 58, #213, #128 and #183 twice each, and every other one is in the whole unit too",
          r["version"] == len(PENAL_SLIDES_SRCS) == 58 and r["twice"] == {"213": 2, "128": 2, "183": 2} and r["versionIn"] and r["repeatsOnlyHere"],
          (r["version"], r["twice"], r["versionIn"], r["repeatsOnlyHere"]))
    check("the repeats have their own identity, sit at the end of the bank (no other question moves), and are never a daily question",
          r["keysUnique"] and r["repeatLast"] and not r["dailyRepeat"], r)
    ctx.close()
    # and no lag: with the flip-book playing, Home paints nothing per frame
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=3)
    pg.evaluate("""()=>{ document.getElementById('pushing-update')?.remove(); store.lifetime.points = 300000; topicsIn(QUESTIONS).forEach(u => store.unitPerfects[u] = 40);
      store.pendingBadgeUnlocks = []; theme.muteBanners = true; showHome(); }""")
    pg.wait_for_function("()=>document.querySelectorAll('.cosmic-rank-anim').length >= document.querySelectorAll('.cosmic-badge-rank.cosmic-badge-lit').length && document.querySelectorAll('.cosmic-rank-anim').length > 0", timeout=60000)
    def paint_ms(on):
        pg.evaluate("""(on)=>{ document.querySelectorAll('.cosmic-rank-anim').forEach(w => w.style.display = on ? '' : 'none');
          document.querySelectorAll('svg.cosmic-rank-emblem').forEach(s => s.classList.toggle('rk-under-anim', on && !!(s.nextElementSibling && s.nextElementSibling.classList.contains('cosmic-rank-anim')))); }""", on)
        pg.wait_for_timeout(500)
        br.start_tracing(page=pg, categories=["devtools.timeline", "disabled-by-default-devtools.timeline"])
        pg.wait_for_timeout(2500)
        data = json.loads(br.stop_tracing()); ev = data["traceEvents"] if isinstance(data, dict) else data
        return sum(e.get("dur", 0) for e in ev if e.get("name") in ("Paint", "RasterTask")) / 1000
    on1, off1, on2, off2 = paint_ms(True), paint_ms(False), paint_ms(True), paint_ms(False)
    check("17 Pro Max: Home with the emblems moving paints no more than with them still (paint+raster over 2.5s, ms)",
          min(on1, on2) <= max(off1, off2) + 40, [round(on1), round(off1), round(on2), round(off2)])
    ctx.close()


def check_b299(br):
    """Build 299. "At the bottom of tests where it says you can press the
    numbers and hit enter ... centered and not offset to left", and "if
    you unlock something ... the customize button in the profile box has a
    dot ... and then within customize put a dot ... over the new thing
    that goes away once you click it". Written against 298, where both fail."""
    print("\n67. build 300: the keyboard hint is centred; a yellow dot for anything new; every flare moves; Rank and Badges stand alone")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
            document.getElementById('pushing-update')?.remove();
            cfg.mode = 'drill'; cfg.units = ['Penal Code']; cfg.source = 'all';
            beginRun(poolNow().slice(0, 5), null); await wait(4200);
            const hint = document.getElementById('hint'), hb = hint.getBoundingClientRect(), cs = getComputedStyle(hint);
            const range = document.createRange(); range.selectNodeContents(hint); const tb = range.getBoundingClientRect();
            out.hint = { align: cs.textAlign, off: Math.round(((tb.left + tb.right) / 2 - (hb.left + hb.right) / 2) * 10) / 10 };
            /* an account updating into 299: nothing is new (and its road map is up to date) */
            store.seenUnlocks = null; testInProgress = false;
            store.rankMapFx244 = true; store.rankMapSeen = TIER_ORDER_FULL.indexOf(rankOf(store));
            showProfile('profile'); await wait(600);
            out.firstDots = document.querySelectorAll('.new-dot').length;
            /* now a character is earned */
            const u = typeof unlockedIdsNow === 'function' ? unlockedIdsNow() : { chars: [] };
            const ch = u.chars.find(id => id !== store.avatarChar);
            if(store.seenUnlocks) store.seenUnlocks.chars = store.seenUnlocks.chars.filter(x => x !== ch);
            showProfile('profile'); await wait(600);
            out.profileDot = !!document.querySelector('.profile-hero .new-dot, .namedisplay-row .new-dot');
            showCustomize('character'); await wait(700);
            const dots = [...document.querySelectorAll('.screen-customize .new-dot')];
            out.custDots = dots.length; out.onChar = dots.length === 1 && dots[0].parentElement.classList.contains('avatarchar-option');
            const opt = document.querySelector('.screen-customize .avatarchar-option.is-new');
            if(opt){ opt.click(); await wait(400); }
            out.after = document.querySelectorAll('.screen-customize .new-dot').length;
            out.saved = !!(store.seenUnlocks && store.seenUnlocks.chars.indexOf(ch) >= 0);
            showProfile('profile'); await wait(600);
            out.profileAfter = !!document.querySelector('.profile-hero .new-dot, .namedisplay-row .new-dot');
            /* the mark travels with the account: a merge keeps both devices' marks */
            const a = { seenUnlocks: { chars: ['x'], banners: [], themes: [], badges: ['p'] } }, b = { seenUnlocks: { chars: ['y'], banners: ['z'], themes: [], badges: ['q'] } };
            mergeSameAccount(a, b); out.merged = a.seenUnlocks.chars.slice().sort().join(',') + '|' + a.seenUnlocks.banners.join(',') + '|' + a.seenUnlocks.badges.slice().sort().join(',');
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: no error", not r.get("threw"), r.get("threw", ""))
        hh = r.get("hint") or {}
        check(f"{dev}: the 'press 1 through 9' hint under a test is centred", hh.get("align") == "center" and abs(hh.get("off", 99)) <= 2, hh)
        check(f"{dev}: an account updating in sees no dots - what it already had is not new", r.get("firstDots") == 0, r.get("firstDots"))
        check(f"{dev}: something newly unlocked puts a dot on Profile's Customize button, and on that one thing in Customize",
              r.get("profileDot") and r.get("custDots") == 1 and r.get("onChar"), (r.get("profileDot"), r.get("custDots"), r.get("onChar")))
        check(f"{dev}: tapping it clears its dot and the Customize button's, and remembers it",
              r.get("after") == 0 and r.get("saved") and not r.get("profileAfter"), (r.get("after"), r.get("saved"), r.get("profileAfter")))
        check(f"{dev}: seen on one device is seen on the other (merged, not replaced)", r.get("merged") == "x,y|z|p,q", r.get("merged"))
        # "Same goes for rank when you rank up, put a dot there or something,
        # and then same goes for badges when you get a new badge."
        r2 = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
            document.querySelectorAll('.unlock-detail, .unlockdetail-overlay, [class*="unlock-detail"]').forEach(n => n.remove());
            const units = topicsIn(QUESTIONS);
            const u0 = units.find(u => !unitBadgeEarned(u)) || units[0];
            store.unitPerfects[u0] = badgeThresholdFor(u0);
            if(typeof retroHideBadges !== 'undefined' && retroHideBadges) retroHideBadges.delete(u0);
            out.unit = u0;
            const held = TIER_ORDER_FULL.indexOf(rankOf(store)); out.held = held;
            store.rankMapFx244 = true; store.rankMapSeen = held;
            /* build 315: the medal is the badge case, the coin the standing block's bubble */
            showProfile('profile'); await wait(600);
            out.badgeDot = !!document.querySelector('.pf-case .new-dot');
            out.rankDotBefore = !!document.querySelector('.pf-standing .new-dot');
            /* each opens on its own - no Rank/Badges switcher (build 299) */
            showRanksScreen('ranks'); await wait(800);
            out.rankScreen = { switcher: document.querySelectorAll('.screen-ranks .navsegment, .screen-ranks .iconbtn').length,
              map: !!document.querySelector('.screen-ranks .rankmap-stop'), badges: !!document.querySelector('.screen-ranks .badges-tab'),
              head: document.getElementById('count') ? document.getElementById('count').textContent : null };
            showRanksScreen('badges'); await wait(900);
            out.badgeScreen = { switcher: document.querySelectorAll('.screen-ranks .navsegment, .screen-ranks .iconbtn').length,
              map: !!document.querySelector('.screen-ranks .rankmap-stop'), badges: !!document.querySelector('.screen-ranks .badges-tab'),
              head: document.getElementById('count') ? document.getElementById('count').textContent : null };
            const tdots = [...document.querySelectorAll('.badges-tab .badge-tile .new-dot')];
            out.tileDots = tdots.length;
            const tile = tdots[0] && tdots[0].closest('.badge-tile');
            out.tileName = tile ? tile.querySelector('.badge-tile-name').textContent : null;
            if(tile){ tile.click(); await wait(500); }
            out.tileAfter = document.querySelectorAll('.badges-tab .badge-tile .new-dot').length;
            out.badgeSaved = store.seenUnlocks.badges.indexOf(u0) >= 0;
            document.querySelectorAll('.unlock-detail, .unlockdetail-overlay, [class*="unlock-detail"]').forEach(n => n.remove());
            showProfile('profile'); await wait(600);
            out.badgeDotAfter = !!document.querySelector('.pf-case .new-dot');
            /* now a rank-up the road map has not shown yet */
            if(held >= 0){
              store.rankMapSeen = held - 1;
              showProfile('profile'); await wait(600);
              /* build 317: Profile now plays the rank-up (check_b317_rankup)
                 and is drawn as it was - so the dot is on the old rank's
                 bubble, or, coming up from no rank, the scene itself is the
                 notice. Either says "something new about your rank". */
              out.rankDot = !!document.querySelector('.pf-standing .new-dot') ||
                (typeof rankUpScene !== 'undefined' && !!rankUpScene && store.rankMapSeen === held - 1);
              showRanksScreen('ranks');
              for(let k = 0; k < 40 && store.rankMapSeen !== held; k++) await wait(250);
              out.rankSeenNow = store.rankMapSeen === held;
              showProfile('profile'); await wait(600);
              out.rankDotAfter = !!document.querySelector('.pf-standing .new-dot');
            }
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: rank/badge dots: no error", not r2.get("threw"), r2.get("threw", ""))
        check(f"{dev}: an up-to-date rank carries no dot", r2.get("rankDotBefore") is False, r2.get("rankDotBefore"))
        rs, bs = r2.get("rankScreen") or {}, r2.get("badgeScreen") or {}
        check(f"{dev}: Rank and Badges each open on their own, with no switcher at the top",
              rs.get("switcher") == 0 and bs.get("switcher") == 0 and rs.get("map") and not rs.get("badges")
              and bs.get("badges") and not bs.get("map") and rs.get("head") == "Rank" and bs.get("head") == "Badges", (rs, bs))
        check(f"{dev}: a new badge puts a dot on Profile's badge case", r2.get("badgeDot"), r2.get("badgeDot"))
        check(f"{dev}: in the case the dot is on that one badge",
              r2.get("tileDots") == 1 and r2.get("tileName") == r2.get("unit"),
              (r2.get("tileDots"), r2.get("tileName"), r2.get("unit")))
        check(f"{dev}: tapping the badge clears its dot and Profile's, and remembers it",
              r2.get("tileAfter") == 0 and r2.get("badgeSaved") and not r2.get("badgeDotAfter"),
              (r2.get("tileAfter"), r2.get("badgeSaved"), r2.get("badgeDotAfter")))
        check(f"{dev}: the fixture holds a rank, so the rank-up case is exercised", (r2.get("held") if r2.get("held") is not None else -1) >= 0, r2.get("held"))
        check(f"{dev}: a rank-up the road map has not shown puts a dot on Profile's rank bubble (or, from 317, plays the rank-up)", r2.get("rankDot"), r2.get("rankDot"))
        check(f"{dev}: opening Rank plays the map, and that clears it",
              r2.get("rankSeenNow") and not r2.get("rankDotAfter"), (r2.get("rankSeenNow"), r2.get("rankDotAfter")))
        # "What if the dot was also on the bottom tab for profile as well",
        # "what about it being yellow?", and "the animations only happen to
        # the flare you have unlocked on the main menu, should still be all
        # the flares".
        r3 = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
            const tab = document.getElementById('bottomtab-profile');
            /* start from nothing new at all, then make one thing new */
            const u = unlockedIdsNow(); store.seenUnlocks = JSON.parse(JSON.stringify(u));
            /* a CURRENT record (309 versions it): without the stamp the v2 re-seed reads it as an old one */
            if(typeof SEEN_VERSION !== 'undefined') store.seenUnlocks.v = SEEN_VERSION;
            store.rankMapFx244 = true; store.rankMapSeen = TIER_ORDER_FULL.indexOf(rankOf(store));
            store.pendingBadgeUnlocks = []; theme.muteBanners = true;
            /* build 314: the dot is worked out once the switch has settled
               (syncProfileTabDotSoon), not in the mount's own task */
            showHome(); await wait(1500);
            out.tabDotNone = tab.classList.contains('has-new');
            const ch = u.chars.find(id => id !== store.avatarChar);
            store.seenUnlocks.chars = store.seenUnlocks.chars.filter(x => x !== ch);
            showHome(); await wait(1500);
            out.tabDot = tab.classList.contains('has-new');
            const dcs = getComputedStyle(tab.querySelector('.bottomtab-icon'), '::after');
            out.tabDotShown = dcs.content !== 'none' && parseFloat(dcs.width) > 6;
            /* the dot is a lit ball now (build 317) - its yellow is in the gradient, not the flat colour */
            out.tabDotColor = (dcs.backgroundImage.match(/rgb\(255, 212, 59\)/) || [dcs.backgroundColor])[0];
            markUnlockSeen('chars', ch); await wait(50);
            out.tabDotAfter = tab.classList.contains('has-new');
            /* the dot inside, same colour */
            store.seenUnlocks.chars = store.seenUnlocks.chars.filter(x => x !== ch);
            showProfile('profile'); await wait(600);
            const d = document.querySelector('.namedisplay-row .new-dot');
            out.dotColor = d ? ((getComputedStyle(d).backgroundImage.match(/rgb\(255, 212, 59\)/) || [getComputedStyle(d).backgroundColor])[0]) : null;
            markUnlockSeen('chars', ch);
            /* every flare moves, locked ones included */
            store.lifetime.points = 0; topicsIn(QUESTIONS).forEach(x => store.unitPerfects[x] = 0);
            showHome();
            const all = () => document.querySelectorAll('.cosmic-badge-rank').length;
            /* 60s, not 40 (build 315): seven sheets recorded from nothing
               on a software-drawn iPad Home take 30-45s here, and the home
               stream's own build missed 40 one run in two. What this
               guards is "the locked ones move too" - on 298 they never
               do, at any budget. */
            for(let k = 0; k < 600 && document.querySelectorAll('.cosmic-rank-anim').length < all(); k++) await wait(100);
            out.flares = all();
            out.locked = document.querySelectorAll('.cosmic-badge-rank:not(.cosmic-badge-lit)').length;
            out.lockedPlaying = document.querySelectorAll('.cosmic-badge-rank:not(.cosmic-badge-lit) .cosmic-rank-anim').length;
            const w = document.querySelector('.cosmic-badge-rank:not(.cosmic-badge-lit) .cosmic-rank-anim');
            out.lockedGrey = w ? /grayscale/.test(w.style.filter) : null;
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: tab/flare checks: no error", not r3.get("threw"), r3.get("threw", ""))
        check(f"{dev}: something new puts a dot on the Profile tab in the bottom bar, and seeing it clears it",
              r3.get("tabDotNone") is False and r3.get("tabDot") and r3.get("tabDotShown") and not r3.get("tabDotAfter"),
              (r3.get("tabDotNone"), r3.get("tabDot"), r3.get("tabDotShown"), r3.get("tabDotAfter")))
        check(f"{dev}: the dot is yellow, the same on the tab and on the card",
              r3.get("dotColor") == "rgb(255, 212, 59)" and r3.get("tabDotColor") == "rgb(255, 212, 59)", (r3.get("dotColor"), r3.get("tabDotColor")))
        check(f"{dev}: every flare on Home moves, the locked ones too (in their grey)",
              (r3.get("locked") or 0) > 0 and r3.get("lockedPlaying") == r3.get("locked") and r3.get("lockedGrey"),
              (r3.get("flares"), r3.get("locked"), r3.get("lockedPlaying"), r3.get("lockedGrey")))
        # "On the leaderboard, where it has the top 3, you should be able to
        # hit each user from the top 3 similar to how you can click any user
        # on the leaderboard."
        r4 = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
            document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
            const lw = lastWeekKey(), wk = weekKeyNow();
            const E = (pub, n, x) => Object.assign({ pub, firstName: n, avatarChar: 'ninja', level: 20, badges: 2 }, x);
            const rows = [E('a', 'Bo', { week: wk, weekPoints: 900, prevWeek: lw, prevWeekPoints: 4200 }),
                          E(store.publicId, 'Me', { week: wk, weekPoints: 10, prevWeek: lw, prevWeekPoints: 3000 }),
                          E('c', 'Dee', { week: wk, weekPoints: 300, prevWeek: lw, prevWeekPoints: 2600 })];
            rows.forEach(e => { e.rawWeekPoints = e.weekPoints; e.weekPoints = weekPointsOfEntry(e); });
            const pinned = Object.assign({}, WEEK_RESULTS_KNOWN);
            Object.keys(WEEK_RESULTS_KNOWN).forEach(k => delete WEEK_RESULTS_KNOWN[k]);
            const host = document.createElement('div'); document.body.appendChild(host);
            renderRankingRows(host, rows, RANKING_BOARDS.find(b => b.key === 'week'), {});
            const spots = [...host.querySelectorAll('.lw-podium .lw-podium-spot')];
            out.spots = spots.length;
            out.tappable = spots.filter(x => x.classList.contains('is-tappable')).map(x => x.querySelector('.lw-podium-name').textContent).sort().join(',');
            const bo = spots.find(x => x.querySelector('.lw-podium-name').textContent === 'Bo');
            if(bo) bo.click(); await wait(300);
            out.card = (document.querySelector('.person-card .person-sheet-name') || {}).textContent || null;
            document.querySelectorAll('.invite-overlay').forEach(e => e.remove());
            /* the congratulations popup's podium stays a picture */
            const pic = buildLastWeekPodium(lastWeekTop3(rows));
            out.picTappable = pic.querySelectorAll('.is-tappable').length;
            Object.keys(WEEK_RESULTS_KNOWN).forEach(k => delete WEEK_RESULTS_KNOWN[k]); Object.assign(WEEK_RESULTS_KNOWN, pinned);
            host.remove();
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: podium: no error", not r4.get("threw"), r4.get("threw", ""))
        # REVISED IN 304: "I should be able to click myself on the
        # leaderboard" - your own spot opens your card too (Go to profile).
        check(f"{dev}: last week's top 3 are tappable like any row - you included (build 304)",
              r4.get("spots") == 3 and r4.get("tappable") == "Bo,Dee,Me", (r4.get("spots"), r4.get("tappable")))
        check(f"{dev}: tapping one opens that person's card", r4.get("card") == "Bo", r4.get("card"))
        check(f"{dev}: the congratulations popup's podium is not tappable (no card over a card)", r4.get("picTappable") == 0, r4.get("picTappable"))
        # "Level at the bottom, badges between the other two."
        order = pg.evaluate("""async ()=>{ showProfile('profile'); await new Promise(r => setTimeout(r, 600));
          const hero = document.querySelector('.profile-hero');
          /* build 315: the mock-up Madison picked - where you stand (rank
             and level), the next rank, the badge case */
          const pick = el => el.matches('.pf-standing') ? 'standing' : el.matches('.pf-goal') ? 'next' : el.matches('.pf-case') ? 'case' : null;
          const tops = [...hero.querySelectorAll('.pf-standing, .pf-goal, .pf-case')].map(el => [pick(el), el.getBoundingClientRect().top]);
          return tops.sort((a, b) => a[1] - b[1]).map(x => x[0]).join(','); }""")
        check(f"{dev}: the Profile card reads where you stand, the next rank, the badge case from the top", order == "standing,next,case", order)
        ctx.close()


def check_b300(br):
    """Build 300. "The bubble flares on home, slight bug or something where
    they are slightly shaking? And not all of them are animating
    properly/smoothly." Three causes, each asserted: two stepped clocks that
    drifted (a wrong frame at every row change), sheet cells that landed on
    half pixels at 3x, and a cache keyed by build so every update
    re-recorded every flare. Written against 299, where it fails."""
    print("\n68. build 300: the Home flares play on one clock, on whole pixels, and are recorded once")
    for (w, h, dev, dpr) in ((440, 956, "17 Pro Max", 3), (834, 1194, "iPad Pro 11", 2)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
            document.getElementById('pushing-update')?.remove();
            store.pendingBadgeUnlocks = []; theme.muteBanners = true; showHome();
            const all = () => document.querySelectorAll('.cosmic-badge-rank').length;
            /* 120s (build 314): recording runs in short slices - see section 66 */
            for(let k = 0; k < 1200 && document.querySelectorAll('.cosmic-rank-anim').length < all(); k++) await wait(100);
            const wraps = [...document.querySelectorAll('.cosmic-rank-anim')];
            out.flares = all(); out.playing = wraps.length;
            const dprNow = window.devicePixelRatio;
            out.per = wraps.map(wr => {
              const imgs = wr.querySelectorAll('img'); const img = imgs[0];
              const anims = [...wr.querySelectorAll('*')].flatMap(e => e.getAnimations());
              const frame = img.parentElement, fw = parseFloat(frame.style.width);
              /* SCREEN pixels: the hero is scaled, so take the ancestors' scale too */
              const badge = wr.parentElement, S = badge.getBoundingClientRect().width / parseFloat(getComputedStyle(badge).width);
              const res = { imgs: imgs.length, anims: anims.length, running: anims.every(a => a.playState === 'running'),
                frameDev: fw * S * dprNow, wrong: 0, offPx: 0 };
              if(anims.length !== 1) return res;
              /* walk the whole loop: at the middle of every frame and just
                 after every frame boundary, the frame on show must be that one */
              const a = anims[0], L = Number(a.effect.getTiming().duration);
              const cols = Math.round(img.offsetWidth / fw), n = a.effect.getKeyframes().length - 1;
              a.pause();
              for(let k = 0; k < n; k++){
                for(const t of [(k + 0.5) * L / n, k * L / n + 0.5]){
                  a.currentTime = t;
                  const m = new DOMMatrix(getComputedStyle(img).transform);
                  const col = Math.round(-m.m41 / fw), row = Math.round(-m.m42 / fw);
                  if(row * cols + col !== k) res.wrong++;
                  for(const v of [m.m41 * S * dprNow, m.m42 * S * dprNow]) if(Math.abs(v - Math.round(v)) > 0.02) res.offPx++;
                }
              }
              a.play();
              res.n = n;
              return res;
            });
            /* recorded once: the cache key is the drawing, not the build */
            /* Rank sheets only (build 308): the character flip-books share
               this cache under /__ch/. */
            const keys = window.caches ? (await (await caches.open('class26e.rk-sheets')).keys()).map(k => new URL(k.url).pathname).filter(p => p.indexOf('/__rk/') === 0) : [];
            out.keys = keys.length; out.buildKeyed = keys.some(k => k.indexOf(encodeURIComponent(APP_BUILD)) >= 0);
            /* The folder is whatever version the page says (ORBIT_ANIM_VER), not a
               literal: build 310 moved it to v5 and a literal "v4" here failed
               the build for being right. */
            out.v3 = keys.filter(k => k.indexOf('/__rk/' + ORBIT_ANIM_VER + '/') === 0).length;
            /* a second Home reuses them: all playing again almost at once */
            showProfile('profile'); await wait(400); showHome();
            const t0 = performance.now();
            for(let k = 0; k < 100 && document.querySelectorAll('.cosmic-rank-anim').length < all(); k++) await wait(50);
            out.againMs = Math.round(performance.now() - t0); out.againPlaying = document.querySelectorAll('.cosmic-rank-anim').length;
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: no error", not r.get("threw"), r.get("threw", ""))
        per = r.get("per") or []
        check(f"{dev}: every flare on Home is playing ({r.get('flares')})",
              r.get("flares", 0) > 0 and r.get("playing") == r.get("flares"), (r.get("flares"), r.get("playing")))
        check(f"{dev}: each is ONE animation on ONE image - no second clock to drift",
              per and all(p["imgs"] == 1 and p["anims"] == 1 and p["running"] for p in per), [(p["imgs"], p["anims"]) for p in per])
        check(f"{dev}: the frame on show is the right one at every moment of the loop, row changes included (no shake)",
              per and all(p.get("anims") == 1 and p.get("wrong") == 0 for p in per), [p.get("wrong") for p in per])
        check(f"{dev}: every frame step lands on whole device pixels (no shimmer)",
              per and all(p.get("anims") == 1 and p.get("offPx") == 0 and isinstance(p.get("frameDev"), (int, float))
                          and abs(p["frameDev"] - round(p["frameDev"])) < 0.02 for p in per),
              [(p.get("offPx"), p.get("frameDev") if not isinstance(p.get("frameDev"), (int, float)) else round(p["frameDev"], 2)) for p in per])
        check(f"{dev}: 30 frames a second (180 over the 6s loop; build 302)", per and all(p.get("n") == 180 for p in per), [p.get("n") for p in per])
        check(f"{dev}: the sheets are cached by drawing, not by build, so an update does not re-record them",
              r.get("keys", 0) > 0 and not r.get("buildKeyed") and r.get("v3") == r.get("keys"), (r.get("keys"), r.get("buildKeyed"), r.get("v3")))
        check(f"{dev}: coming back to Home, every flare is playing again within a second",
              r.get("againPlaying") == r.get("flares") and r.get("againMs", 9999) < 1000, (r.get("againPlaying"), r.get("againMs")))
        ctx.close()

    # "Remove it from the entire unit one, the entire unit one should be 340
    # questions not 341" - the card says so, and a whole-unit run of 340
    # is still a whole unit (its hundo counts); the slides 55-124 version has 58.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        document.getElementById('pushing-update')?.remove();
        cfg.mode = 'drill'; cfg.units = []; cfg.versions = {}; cfg.source = 'all'; showSetup(); await wait(700);
        const row = [...document.querySelectorAll('.pick')].find(x => (x.querySelector('input') || {}).value === 'Penal Code');
        out.card = row ? (row.querySelector('.pcount') || {}).textContent : null;
        cfg.units = ['Penal Code']; cfg.versions = {};
        order = poolNow(); out.whole = order.length; out.full = isFullUnitRun();
        out.covered = unitsFullyCoveredBy(order);
        cfg.versions = { 'Penal Code': 'test' }; out.test = poolNow().length;
        out.testRepeats = poolNow().map(i => QUESTIONS[i].src).filter(s => s >= 347).sort();
        cfg.versions = {};
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("Penal Code: no error", not r.get("threw"), r.get("threw", ""))
    check("Penal Code: the unit card says 340 questions", r.get("card") == "340 questions", r.get("card"))
    check("Penal Code: a whole-unit run is 340 and counts as the full unit (its hundo still lands)",
          r.get("whole") == 340 and r.get("full") is True and r.get("covered") == ["Penal Code"], (r.get("whole"), r.get("full"), r.get("covered")))
    check("Penal Code: the slides 55-124 version has its 58, the three repeats included and the old #84 one not",
          r.get("test") == 58 and r.get("testRepeats") == [348, 349, 350], (r.get("test"), r.get("testRepeats")))
    ctx.close()


def check_b301_chat(br):
    """Build 301: "old chats are showing up as notifications and old chats
    are giving the chat bubble a red dot as if there's an unread chat."

    A message drops a small `msgping` into each member's inbox document,
    and nothing ever took one out again. Madison's inbox on the live
    project held three pings from one group chat, eight days old. They
    count as unread whenever this device has no record of reading that
    chat - the record is per-device localStorage, which a re-add, iOS
    tidying storage, or simply never having opened it HERE all lose -
    and a chat you had left was put straight back on your list by its
    own old ping. So: a ping has a shelf life, reading a chat takes its
    pings out of the mailbox, a chat you left stays left, and an old
    ping never pops a banner. Written against build 300, where every
    one of these fails."""
    print("\n69. build 301: old chat pings stay old")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(r => setTimeout(r, ms));
      const out = {};
      try{
      const docs = {}, updates = [];
      const doc = id => ({
        onSnapshot(){ return () => {}; },
        get(){ return Promise.resolve({ exists: !!docs[id], data: () => docs[id] || {} }); },
        set(d){ docs[id] = d; return Promise.resolve(); },
        update(...a){ updates.push({ id, keys: a.length > 1 ? a.filter((x, i) => i % 2 === 0).map(f => (f.segs || []).join('.')) : Object.keys(a[0] || {}) });
                      return Promise.resolve(); } });
      if(typeof firebase === 'undefined') window.firebase = {
        firestore: { FieldPath: function(){ this.segs = [...arguments]; }, FieldValue: { delete: () => '__del__' } } };
      fbDb = { collection: () => ({ doc, onSnapshot(){ return () => {}; },
                 get(){ return Promise.resolve({ forEach(){}, size:0, metadata:{} }); } }),
               runTransaction(fn){ return Promise.resolve().then(() => fn({
                 get: ref => ref.get(), set: (ref, d) => ref.set(d), update: () => {} })); } };
      theme.muteBanners = false;
      store.friendsIn = ['bo00000000001'];
      leaderboardRows = [{ pub:'bo00000000001', firstName:'Bo', avatarChar:'robot', level:5, badges:1, seenAt: Date.now() }];
      store.chats = [{ code:'GRP-OLD1', name:'Study group', at: Date.now() - 9 * 864e5, with:['cy','od'] }];
      localStorage.removeItem('class26e.chatseen');          /* a device with no read history */
      showHome(); await wait(500);
      const txt = id => { const e = document.getElementById(id); return e && !e.hidden ? e.textContent : '0'; };
      const day = 864e5, now = Date.now();
      /* A. Madison's inbox, as it is: three pings, one chat, eight days old */
      inboxMsgs = {
        'cy~m': { type:'msgping', code:'GRP-OLD1', pub:'cy', firstName:'Cap', text:'So could he make one this week', at: now - 8 * day },
        'od~m': { type:'msgping', code:'GRP-OLD1', pub:'od', firstName:'Odin', text:'T for tolerance', at: now - 8 * day + 3000 },
        'sa~m': { type:'msgping', code:'GRP-OLD1', pub:'sa', firstName:'Sauce', text:'T is for trust', at: now - 8 * day - 8000 } };
      syncChatDockDot();
      out.oldDot = txt('chatdock-dot'); out.oldGroups = txt('chatdock-groupscount');
      /* B. a chat you left stays left, even with its old ping still in the box */
      store.chats.push({ code:'GRP-LEFT', name:'Left group', at: now - day, with:['cy'] });
      inboxMsgs['zz~m'] = { type:'msgping', code:'GRP-LEFT', pub:'zz', firstName:'Zed', text:'bye', at: now - 3600e3 };
      markChatSeen('GRP-LEFT', now - 3600e3);
      leaveChatByCode('GRP-LEFT'); await wait(50);
      syncChatDockDot(); chatUnreadByTab();
      out.leftBack = !!chatEntry('GRP-LEFT');
      document.querySelectorAll('.toast').forEach(t => t.remove());
      /* C. reading a chat takes its pings out of the mailbox */
      store.chats.push({ code:'GRP-NEW1', name:'New group', at: now, with:['cy'] });
      inboxMsgs['cy2~m'] = { type:'msgping', code:'GRP-NEW1', pub:'cy2', firstName:'Cy', text:'hi', at: now - 5 * 60e3 };
      syncChatDockDot();
      out.newDot = txt('chatdock-dot');
      updates.length = 0;
      markChatSeen('GRP-NEW1', Date.now());
      await wait(50); syncChatDockDot();
      out.afterRead = txt('chatdock-dot');
      out.cleared = updates.filter(u => /^inbox-/.test(u.id)).flatMap(u => u.keys);
      /* D. an old ping never pops a banner, a fresh one still does */
      document.querySelectorAll('.vroom-chat-alert').forEach(e => e.remove());
      const keep = inboxMsgs;
      pingPreviewSeen = null; inboxMsgs = {}; previewNewPings();
      inboxMsgs = { 'cy~m': keep['cy~m'], 'od~m': keep['od~m'] }; previewNewPings();
      out.oldBanner = !!document.querySelector('.vroom-chat-alert.is-ping');
      inboxMsgs['fr~m'] = { type:'msgping', code:'GRP-OLD1', pub:'fr', firstName:'Fresh', text:'now', at: Date.now() };
      previewNewPings();
      out.freshBanner = !!document.querySelector('.vroom-chat-alert.is-ping');
      document.querySelectorAll('.vroom-chat-alert').forEach(e => e.remove());
      /* E. a friend chat whose history has expired is still read by opening it */
      const fc = friendChatCode('bo00000000001');
      docs[fc] = { kind:'chat', chatMessages: [], participants: {} };
      /* 23 hours, not 30: since build 313 a ping is a day long, the same as
         the chat's own history, so a 30-hour ping is not unread at all.
         The room is still empty - what is under test is that opening a
         chat with nothing in it reads its ping. */
      inboxMsgs = { 'bo00000000001~m': { type:'msgping', code: fc, pub:'bo00000000001', firstName:'Bo', text:'yo', at: Date.now() - 23 * 3600e3 } };
      syncChatDockDot();
      out.friendBefore = txt('chatdock-friendscount');
      chatDockTab = 'friends'; openChatDock(); await wait(200);
      openFriendChat('bo00000000001'); await wait(400);
      markOpenChatSeen(); await wait(50);
      out.friendAfter = txt('chatdock-friendscount');
      closeChatDock();
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("an eight-day-old ping is not an unread chat, with or without a read record",
          r.get("oldDot") == "0" and r.get("oldGroups") == "0", r)
    check("a chat you left is not put back on your list by its old ping",
          r.get("leftBack") is False, r)
    check("a fresh ping still counts", r.get("newDot") == "1", r)
    check("reading a chat clears it, and takes its ping out of the mailbox",
          r.get("afterRead") == "0" and any("cy2~m" in k for k in (r.get("cleared") or [])), r)
    check("an old ping never pops a message banner", r.get("oldBanner") is False, r)
    check("a fresh one still does", r.get("freshBanner") is True, r)
    check("opening a friend chat whose history has expired still reads it",
          r.get("friendBefore") == "1" and r.get("friendAfter") == "0", r)
    check("and nothing threw", not r.get("threw"), r.get("threw"))
    ctx.close()


def check_b302(br):
    """Build 302: tabs that do not lap, a calendar where every day can be
    picked, a sleeper that still moves, matched rings, the total XP at the
    bottom, Home's bubbles filled on the way back, the road map slower and
    the emblems' new shapes. Written against build 301; every group fails
    there."""
    print("\n70. build 302: no lap on a tab switch, every calendar day, and the rest")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const out = {};
          try{
          document.getElementById('pushing-update')?.remove();
          /* 1. a tab switch from a scrolled page: no movement after mount */
          showAppearance(); await wait(500);
          document.documentElement.style.scrollBehavior = 'smooth';
          window.scrollTo({ top: 600, behavior: 'instant' }); await wait(200);
          out.scrolledFrom = window.scrollY;
          const seen = []; let first = null;
          document.getElementById('bottomtab-profile').click();
          const t0 = performance.now();
          while(performance.now() - t0 < 700){
            await new Promise(r => requestAnimationFrame(r));
            const el = stage.firstElementChild;
            if(el && el.classList.contains('screen-profile') || (el && el.querySelector('.profile-hero'))){
              if(first === null) first = performance.now() - t0;
              seen.push({ y: window.scrollY, tf: getComputedStyle(el).transform });
            }
          }
          out.frames = seen.length;
          out.moved = seen.filter(f => f.tf && f.tf !== 'none').length;
          out.glided = seen.filter(f => f.y > 0 && f.y < out.scrolledFrom).length;
          out.endY = window.scrollY;
          out.ys = seen.map(f => Math.round(f.y)).slice(0, 12);
          /* 2. the calendar: a weekend is a button, today is picked, the two marks differ */
          showCalendar(); await wait(400);
          const cells = [...document.querySelectorAll('.cal-grid .cal-cell[data-date]')];
          const wk = cells.find(c => { const [y, m, d] = c.dataset.date.split('-').map(Number); const dw = new Date(y, m - 1, d).getDay(); return dw === 6 && !c.classList.contains('cal-cell-class'); });
          out.weekendIsButton = !!(wk && wk.tagName === 'BUTTON');
          if(wk){ wk.click(); await wait(100); }
          out.weekendCard = (document.querySelector('.cal-daycard') || {}).textContent || '';
          const cls = [...document.querySelectorAll('.cal-grid .cal-cell.cal-cell-class:not(.cal-cell-today)')][0];
          if(cls){ cls.click(); await wait(100); }
          const today = document.querySelector('.cal-grid .cal-cell-today');
          out.todayMarkedUnpicked = !!(today && !today.classList.contains('cal-cell-sel'));
          if(today){ today.click(); await wait(100); }
          const today2 = document.querySelector('.cal-grid .cal-cell-today');
          out.todayPickable = !!(today2 && today2.classList.contains('cal-cell-sel'));
          out.hint = !!document.querySelector('.cal-grid-hint');
          /* 3. asleep and still moving */
          const av = avatarSpanFor({ avatarChar: 'ninja' }); document.body.appendChild(av);
          setCharState(av, 'live'); await wait(80);
          const liveN = av.getAnimations ? av.getAnimations({ subtree: true }).length : 0;
          setCharState(av, 'sleep'); await wait(80);
          out.sleepLive = av.classList.contains('char-live');
          out.sleepN = av.getAnimations ? av.getAnimations({ subtree: true }).filter(a => !(a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest('.char-zzz'))).length : 0;
          out.liveN = liveN;
          av.remove();
          /* 4. three rings, one size; 5. the total at the bottom.
             Build 316: an unranked line has no emblem to measure, so the
             fixture holds Bronze (one badge, level 25) for this part */
          const keepU0 = topicsIn(QUESTIONS)[0], keepPerf = store.unitPerfects[keepU0], keepPts = store.lifetime.points;
          store.unitPerfects[keepU0] = Math.max(keepPerf || 0, badgeThresholdFor(keepU0));
          store.lifetime.points = Math.max(keepPts || 0, xpForLevel(25));
          showProfile('profile'); await wait(700);
          const wOf = sel => { const e = document.querySelector(sel); return e ? Math.round(e.getBoundingClientRect().width) : null; };
          /* build 315: the rings are gone. Build 316: the rank you hold is
             an emblem on its line, the line's own size - not a ring, and
             not a second big mark beside the next rank's */
          out.rings = [wOf('.pf-standing .pf-emb'), wOf('.pf-goal .pf-goal-emb')];
          const tot = document.querySelector('.pf-standing .pf-xp-total'), bar = document.querySelector('.pf-standing .profile-xpbar');
          out.total = tot ? tot.textContent : '';
          out.totalOnLine = !!(tot && tot.closest('.pf-idline') && bar && (bar.compareDocumentPosition(tot) & Node.DOCUMENT_POSITION_PRECEDING));
          out.barNums = (document.querySelector('.pf-standing .pf-xpnums') || {}).textContent || '';
          if(keepPerf === undefined) delete store.unitPerfects[keepU0]; else store.unitPerfects[keepU0] = keepPerf;
          store.lifetime.points = keepPts;
          const fill = document.querySelector('.profile-xpbar .xpbar-fill');
          out.glide = fill ? getComputedStyle(fill, '::before').animationName : '';
          /* 6. Home's bubbles on the way back */
          showHome(); await wait(9000);
          document.getElementById('bottomtab-profile').click(); await wait(800);
          document.querySelector('.bottomtab').click();
          await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
          await wait(120);
          const bub = [...document.querySelectorAll('.cosmic-badge-rank')];
          out.bubbles = bub.length;
          out.blank = bub.filter(b => { const s = b.querySelector('svg.cosmic-rank-emblem'); const shown = s && getComputedStyle(s).visibility !== 'hidden'; return !shown && !b.querySelector('.cosmic-rank-anim'); }).length;
          /* 7. the shapes and the orbit */
          const sap = buildRankEmblemSVG('adept'), plat = buildRankEmblemSVG('vanguard'), sil = buildRankEmblemSVG('ranger');
          out.sapSym = !!sap.querySelector('.rk-spin.rk-sym2');
          out.platSpiral = !!plat.querySelector('.rk-spin.rk-sym4');
          out.silverSoft = !!sil.querySelector('.rk-twinkle.rk-soft');
          /* build 313: the 4th and 5th only show once Void is held - look with it held */
          const keepF = store.mysteryColorsFound; store.mysteryColorsFound = { red: true, orange: true, yellow: true };
          showHome(); await wait(400);
          out.innerDots = document.querySelectorAll('.cosmic-hero-orbitlayer-inner .cosmic-orbit-dot').length;
          store.mysteryColorsFound = keepF;
          /* 8. the road map is slower */
          showRanksScreen('ranks'); await wait(300);
          const rf = document.querySelector('.rankmap-roadfill');
          out.roadDur = rf ? getComputedStyle(rf).transitionDuration : '';
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: a tab switch moves nothing once the new screen is up - no slide, no glide to the top",
              r.get("frames", 0) > 5 and r.get("moved") == 0 and r.get("glided") == 0 and r.get("endY") == 0, r)
        check(f"{dev}: a weekend can be picked and says there is no class",
              r.get("weekendIsButton") is True and "No class" in (r.get("weekendCard") or ""), [r.get("weekendIsButton"), r.get("weekendCard")])
        check(f"{dev}: today keeps its mark when another day is picked, and can be picked again",
              r.get("todayMarkedUnpicked") is True and r.get("todayPickable") is True and r.get("hint") is True, r)
        check(f"{dev}: a sleeping character is still live and still animating",
              r.get("sleepLive") is True and r.get("sleepN", 0) >= max(3, r.get("liveN", 0) // 2), [r.get("sleepLive"), r.get("liveN"), r.get("sleepN")])
        rings = r.get("rings") or []
        # REVISED IN 316: the held rank is the mockup's small emblem on the
        # rank line ("I prefer how your current level and rank looked"), so
        # it is the line's size and the next rank's emblem is the big one.
        check(f"{dev}: the rank you hold is an emblem the size of its line, the next rank's the big one",
              len(rings) == 2 and None not in rings and 20 <= rings[0] <= 32 and rings[1] >= 2 * rings[0], rings)
        # REVISED IN 315: "we wouldn't need that total xp there because it'd
        # be with all the xp stuff" - the total joined the bar's numbers.
        # REVISED IN 316: back on the rank line, as the mockup had it; the
        # bar's numbers are this level's and what is left to the next.
        check(f"{dev}: the total XP is on the rank line above the bar; under the bar, this level's XP and what is left",
              r.get("totalOnLine") is True and re.match(r"^[0-9,]+ total XP$", r.get("total") or "")
              and re.match(r"^[0-9,]+ / [0-9,]+ XP[0-9,]+ XP to level \d+$", r.get("barNums") or ""), [r.get("total"), r.get("barNums")])
        check(f"{dev}: the XP bar carries its slow light", r.get("glide") == "xp-glide", r.get("glide"))
        check(f"{dev}: back on Home, no flare bubble is empty", r.get("bubbles", 0) >= 7 and r.get("blank") == 0, [r.get("bubbles"), r.get("blank")])
        check(f"{dev}: Sapphire turns on a half-turn loop, Platinum has its spiral, Silver's star glints",
              r.get("sapSym") and r.get("platSpiral") and r.get("silverSoft"), [r.get("sapSym"), r.get("platSpiral"), r.get("silverSoft")])
        check(f"{dev}: three orbit dots on the inner ring", r.get("innerDots") == 3, r.get("innerDots"))
        check(f"{dev}: the road map fills over 2.4s", (r.get("roadDur") or "").startswith("2.4s"), r.get("roadDur"))
        check(f"{dev}: nothing threw", not r.get("threw"), r.get("threw"))
        ctx.close()

def check_b302_flares(br):
    """Build 302: the flare levels move down (20 / ~35 / ~48 / ~60 / 70-72)
    and anybody already past one is handed it at random over about their
    next ten tests, once. Written against build 301; fails there."""
    print("\n71. build 302: new flare levels, and the owed ones spread over ten tests")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => {
      const out = {};
      try{
      out.windows = JSON.stringify(typeof FLARE_WINDOWS !== 'undefined' ? FLARE_WINDOWS : null);
      out.hasFn = typeof applyFlareReschedule === 'function';
      const realLevel = levelOf;
      const tests = testsCompletedOf(store);
      out.tests = tests;
      const trial = (lvl, found, n) => {
        const offs = [];
        for(let i = 0; i < n; i++){
          levelOf = () => lvl;
          store.mysteryColorsFound = Object.assign({}, found);
          store.flareLevels = { red: 35, orange: 40, yellow: 44, violet: 57, white: 69 };
          store.flareSchedRev = 0; store.flareNextTestAt = -99;
          if(out.hasFn) applyFlareReschedule();
          offs.push(store.flareNextTestAt === -99 ? null : store.flareNextTestAt - tests);
        }
        return offs;
      };
      const span = a => a.some(x => x === null) ? null : [Math.min(...a), Math.max(...a), new Set(a).size];
      out.one = span(trial(25, {}, 300));
      out.two = span(trial(45, {}, 300));
      out.three = span(trial(50, {}, 300));
      out.none = trial(10, {}, 5);
      /* once only: a second call leaves the schedule alone */
      levelOf = () => 25; store.mysteryColorsFound = {}; store.flareSchedRev = 0;
      if(out.hasFn) applyFlareReschedule();
      const first = store.flareNextTestAt; store.flareNextTestAt = first + 7;
      if(out.hasFn) applyFlareReschedule();
      out.onceOnly = out.hasFn && store.flareNextTestAt === first + 7;
      /* red at exactly 20, with nothing holding it back */
      store.flareSchedRev = 999; store.flareNextTestAt = 0; store.mysteryColorsFound = {};
      levelOf = () => 19; out.red19 = mysteryGateMet('red');
      levelOf = () => 20; out.red20 = mysteryGateMet('red');
      /* an old drawn level is redrawn into its new window */
      store.flareLevels = { orange: 41 };
      out.orangeRedrawn = mysteryLevelGate('orange');
      levelOf = realLevel;
      /* an existing account loads with the reschedule still to come */
      const doc = JSON.parse(JSON.stringify(store)); delete doc.flareSchedRev;
      applyLoadedData(doc);
      out.loadedRev = store.flareSchedRev;
      }catch(e){ out.err = String(e); }
      return out;
    }""")
    ctx.close()
    check("no error in the flare checks", "err" not in r, r.get("err"))
    # build 313 added the sixth (78-80) after these; the five are unchanged
    check("flare levels are 20 / 34-36 / 47-49 / 59-61 / 70-72",
          (r.get("windows") or "").startswith('{"red":[20,20],"orange":[34,36],"yellow":[47,49],"violet":[59,61],"white":[70,72]'),
          r.get("windows"))
    one, two, three = r.get("one"), r.get("two"), r.get("three")
    check("one flare owed: lands anywhere in the next ten tests",
          bool(one) and one[0] == 0 and 7 <= one[1] <= 9 and one[2] >= 6, one)
    check("two owed: the first within six, so both fit inside ten",
          bool(two) and two[0] == 0 and two[1] <= 5 and two[2] >= 3, two)
    check("three owed: the first within two", bool(three) and three[1] <= 1, three)
    check("nobody owed: the schedule is left alone", r.get("none") == [None] * 5, r.get("none"))
    check("the reschedule happens once per account", r.get("onceOnly") is True)
    check("red is level 20 exactly", r.get("red19") is False and r.get("red20") is True,
          (r.get("red19"), r.get("red20")))
    check("an old drawn orange level is redrawn into 34-36",
          isinstance(r.get("orangeRedrawn"), int) and 34 <= r["orangeRedrawn"] <= 36, r.get("orangeRedrawn"))
    check("an existing account loads with the reschedule pending", r.get("loadedRev") == 0, r.get("loadedRev"))


FLAGNOTE_VIEWPORTS = [
    (320, 568), (375, 667), (375, 812), (393, 852), (440, 956), (518, 1125),
    (744, 1133), (768, 1024), (810, 1080), (820, 1180), (834, 1194),
    (1024, 1366), (1032, 1376), (360, 800), (800, 1280),
    (1366, 768), (1512, 982), (1728, 1117), (1920, 1080), (1440, 900),
    (1280, 800), (2560, 1440)]


def check_b302_flagnote(br):
    """Build 302: the flag's confirmation is a label beside the flag, not
    a yellow bar across the top of the screen. "It looks like a button ...
    being at the very top of the screen isn't the move ... the chat button
    is over it." On every matrix size, upright and on its side: no toast,
    a label on the flag's own line, inside the screen, clear of the flag,
    Pause, the chat button and the top bar, and with no fill of its own
    in a test. Written against build 301; fails there.

    REVISED IN 314: "Star removed/and starred wording when hitting the
    button, we don't need that anymore." The label is gone; what is held
    on every size now is that a tap on the star says NOTHING - no label,
    no toast - and the star itself still turns on. Fails on 313, where
    every size shows "Starred"."""
    print("\n72. build 314: tapping the star shows no words, on every device")
    sizes = []
    for (w, h) in FLAGNOTE_VIEWPORTS:
        sizes.append((w, h))
        if w < h:
            sizes.append((h, w))
    bad = []
    for (w, h) in sizes:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        try:
            pg.evaluate("""async ()=>{ const wt = ms => new Promise(r => setTimeout(r, ms));
              document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
              cfg.mode='drill'; cfg.units=['Identity Crimes']; cfg.versions={}; cfg.source='all'; cfg.size=0;
              showSetup(); await wt(400); document.getElementById('nextbtn').click(); await wt(300);
              document.querySelector('.sheet-begin-btn').click(); }""")
            pg.wait_for_selector(".choice", timeout=25000)
            pg.wait_for_timeout(500)
            r = pg.evaluate("""async ()=>{ const wt = ms => new Promise(r => setTimeout(r, ms));
              const f = document.querySelector('.qflag'); if(!f) return { noFlag: true };
              if(isFlagged(order[pos])){ setFlag(order[pos], false); }
              f.click(); await wt(260);
              const R = e => e && e.getBoundingClientRect();
              const n = document.querySelector('.flag-note'), t = document.getElementById('toast');
              const on = f.classList.contains('on') && isFlagged(order[pos]);
              if(!n) return { noNote: true, on, toast: !!(t && t.textContent && t.classList.contains('show')) };
              const nr = R(n), fr = R(f);
              const hit = (a, b) => !!(a && b && b.width && !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom));
              const cs = getComputedStyle(n);
              return {
                toast: !!(t && t.textContent && t.classList.contains('show')),
                text: n.textContent,
                inView: nr.left >= 0 && nr.right <= innerWidth && nr.top >= 0 && nr.bottom <= innerHeight,
                onLine: Math.abs((nr.top + nr.bottom) / 2 - (fr.top + fr.bottom) / 2) <= 2 || nr.top >= fr.bottom,
                hitsFlag: hit(nr, fr),
                hitsPause: hit(nr, R(document.getElementById('pausebtn'))),
                hitsChat: hit(nr, R(document.querySelector('.chatdock-btn'))),
                hitsTop: hit(nr, R(document.querySelector('.wrap > .top'))),
                filled: cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent'
              }; }""")
        except Exception as e:
            r = {"err": str(e)[:100]}
        ctx.close()
        tag = "%dx%d" % (w, h)
        if r.get("err") or r.get("noFlag"):
            bad.append("%s: %s" % (tag, r)); continue
        if not r.get("noNote"):
            bad.append("%s: a label still says %r" % (tag, r.get("text"))); continue
        if r.get("toast"):
            bad.append("%s: a toast says it instead" % tag)
        if not r.get("on"):
            bad.append("%s: the star did not turn on" % tag)
    check("a tap on the star turns it on and says nothing, on all %d sizes" % len(sizes), not bad, bad[:6])


def check_b303(br):
    """Build 303: the test screen (mode left, count centred, timer under
    the bar and amber while paused, a press then a result, a wrong pick
    that lights and lets go, a 3D Next that rises), feedback with some
    personality, the star, Exam's instant feedback, and Learn with its
    flashcards. Written against build 302; every group fails there."""
    print("\n73. build 303: test screen, star, instant feedback, Learn and flashcards")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const R = e => e && e.getBoundingClientRect();
          const out = {};
          try{
          setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          const start = async (mode, extra) => {
            cfg.mode = mode; cfg.units = ['Identity Crimes']; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'up';
            if(extra) extra();
            showSetup(); await wait(400); document.getElementById('nextbtn').click(); await wait(400);
            document.querySelector('.sheet-begin-btn').click();
            for(let t = 0; t < 80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
            await wait(300);
          };
          await start('drill');
          /* 1. top row: mode on the left, count centred on the screen */
          const ml = document.getElementById('testmodelabel'), qc = document.getElementById('testqcounter');
          out.mode = ml ? ml.textContent : null;
          out.modeLeft = ml ? Math.round(R(ml).left) : null;
          out.countMid = qc ? Math.round((R(qc).left + R(qc).right) / 2 - innerWidth / 2) : null;
          /* 2. the timer under the progress bar, above the line */
          const tl = document.getElementById('timerline'), mt = document.getElementById('meter'), ct = document.getElementById('count');
          out.timerUnderMeter = !!(tl && !tl.hidden && R(tl).top >= R(mt).bottom - 1 && R(tl).bottom <= R(ct).bottom + 1);
          /* 3. a wrong pick: pressed, then red, then let go */
          const qi = order[pos], right = correctSlot(qi), wrongSlot = (right + 1) % 4;
          document.querySelector('.qpanel .choice[data-index="' + wrongSlot + '"]').click();
          out.pressing = !!document.querySelector('.qpanel .choice.is-pressing');
          await wait(250);
          const wb = document.querySelector('.qpanel .choice[data-index="' + wrongSlot + '"]');
          out.wrongFlash = wb.classList.contains('is-wrong-flash');
          const st = document.querySelector('.qpanel > .status');
          out.statusGap = Math.round(R(document.querySelector('.qpanel .choices')).top - R(st).bottom);
          await wait(2700);
          out.wrongLetGo = !document.querySelector('.qpanel .choice[data-index="' + wrongSlot + '"]').classList.contains('is-wrong-flash');
          /* 4. the right pick: a pop, a line that is not the old one, a rising Next */
          document.querySelector('.qpanel .choice[data-index="' + right + '"]').click();
          await wait(200);
          out.rightPop = !!document.querySelector('.qpanel .choice.is-right-pop');
          out.line = (document.querySelector('.qpanel > .status') || {}).textContent || '';
          const nb = document.getElementById('nextbtn');
          out.nextRising = nb.classList.contains('is-rising');
          await wait(1500);
          const nr = R(nb);
          out.nextPill = { w: Math.round(nr.width), vw: innerWidth, gapBottom: Math.round(innerHeight - nr.bottom), radius: getComputedStyle(nb).borderTopLeftRadius };
          /* 5. the star */
          const fb = document.querySelector('.qpanel .qflag');
          out.star = !!(fb && fb.querySelector('.starfill') && !fb.querySelector('.flagpole'));
          if(isFlagged(qi)) setFlag(qi, false);
          fb.click(); await wait(100);
          out.starOn = fb.classList.contains('on') && fb.classList.contains('just-on');
          out.starNote = (document.querySelector('.flag-note') || {}).textContent || '';
          /* 6. paused: the clock stays, in amber */
          document.getElementById('pausebtn').click(); await wait(400);
          out.pausedTimer = !tl.hidden && tl.classList.contains('is-paused') && getComputedStyle(tl.querySelector('.tpaused')).display !== 'none';
          document.getElementById('resumebtn').click(); await wait(300);
          out.resumedTimer = !tl.classList.contains('is-paused');
          /* 7. Exam: the switch is Exam's alone, and with it a pick is judged and locked */
          cfg.mode = 'drill'; showSetup(); await wait(300); document.getElementById('nextbtn').click(); await wait(400);
          const rowText = [...document.querySelectorAll('.unitoptions-modal .opt')].filter(o => !o.hidden && o.offsetParent).map(o => o.textContent);
          out.drillHasFeedback = rowText.some(t => /Instant feedback/.test(t));
          document.getElementById('unitoptions-modal')?.remove();
          await start('exam', () => { cfg.examFeedback = true; });
          const eqi = order[pos], er = correctSlot(eqi), ew = (er + 1) % 4;
          document.querySelector('.qpanel .choice[data-index="' + ew + '"]').click(); await wait(300);
          out.examJudged = !!document.querySelector('.qpanel .choice.is-right') && !!document.querySelector('.qpanel .choice.is-wrong-pick');
          document.querySelector('.qpanel .choice[data-index="' + er + '"]').click(); await wait(200);
          out.examLocked = picked[eqi] === ew;
          out.examMode = document.getElementById('testmodelabel').textContent;
          cfg.examFeedback = false;
          /* 8. Learn, and its flashcards */
          testInProgress = false;
          cfg.mode = 'review'; cfg.flashcards = true; showSetup(); await wait(300); document.getElementById('nextbtn').click(); await wait(400);
          out.sheetTitle = (document.querySelector('.unitoptions-modal-title') || {}).textContent;
          out.beginText = document.querySelector('.sheet-begin-btn').textContent;
          /* build 314: through LOADING FLASHCARDS first */
          document.querySelector('.sheet-begin-btn').click(); await wait(200); while(document.getElementById('teststart-overlay')) await wait(30); await wait(300);
          const card = document.querySelector('.fc-card');
          out.fcCard = !!card;
          out.fcCount = document.getElementById('testqcounter').textContent;
          out.fcMode = document.getElementById('testmodelabel').textContent;
          out.fcTimer = document.getElementById('timerline').hidden;
          out.fcStar = !!(card && card.querySelector('.fc-star .starfill'));
          card.click(); await wait(700);
          out.fcFlipped = card.classList.contains('is-flipped');
          document.getElementById('fcnext').click(); await wait(150);
          document.getElementById('fcnext').click(); await wait(400);
          out.fcGreenAt3 = document.querySelectorAll('#meter .tick.clean').length;
          document.querySelector('.fc-back-btn').click(); await wait(400);
          out.fcGreenBack = document.querySelectorAll('#meter .tick.clean').length;
          document.getElementById('pausebtn').click(); await wait(400);
          out.fcPause = !!document.querySelector('.pausepanel') && /Exit flashcards/.test(document.querySelector('.pausepanel').textContent);
          [...document.querySelectorAll('.pausepanel .next')].find(b => /Exit/.test(b.textContent)).click(); await wait(400);
          out.fcLeft = (typeof fc === 'undefined' || fc === null) && document.getElementById('pausebtn').hidden;
          /* 9. Learn's list, as cards with air between them */
          cfg.flashcards = false; showAnswerReview(['Identity Crimes'], 'all', {}); await wait(400);
          const qs = [...document.querySelectorAll('.screen-answerreview .review-question')];
          out.listTitle = (document.querySelector('.screen-answerreview .ar-head-title') || {}).textContent;
          out.listGap = qs.length > 1 ? Math.round(R(qs[1]).top - R(qs[0]).bottom) : null;
          out.listCard = qs.length ? parseFloat(getComputedStyle(qs[0]).borderTopLeftRadius) : 0;
          /* 10. the words */
          out.modeCard = (document.querySelector ? true : true);
          }catch(e){ out.err = String(e).slice(0, 200); }
          return out;
        }""")
        ctx.close()
        check(dev + ": no error in the 303 run", "err" not in r, r.get("err"))
        check(dev + ": the top row says the mode on the left", r.get("mode") == "Drill" and (r.get("modeLeft") or 999) < 60, (r.get("mode"), r.get("modeLeft")))
        check(dev + ": and the count in the middle of the screen", r.get("countMid") is not None and abs(r["countMid"]) <= 2, r.get("countMid"))
        check(dev + ": the timer sits under the progress bar, above the line", r.get("timerUnderMeter") is True)
        check(dev + ": a pick is pressed before it is answered", r.get("pressing") is True)
        check(dev + ": a wrong pick lights up red", r.get("wrongFlash") is True)
        check(dev + ": and lets go on its own after a couple of seconds", r.get("wrongLetGo") is True)
        check(dev + ": the feedback line has space under it", (r.get("statusGap") or 0) >= 10, r.get("statusGap"))
        check(dev + ": a right pick pops", r.get("rightPop") is True)
        check(dev + ": and says something other than the old fixed line",
              bool(r.get("line")) and r["line"] not in ("Correct, first try.",) and not r["line"].startswith("Correct, after "), r.get("line"))
        np_ = r.get("nextPill") or {}
        check(dev + ": Next rises, as a pill clear of the edges",
              r.get("nextRising") is True and np_.get("w", 9999) < np_.get("vw", 0) - 30 and np_.get("gapBottom", 0) >= 12 and np_.get("radius", "0px") != "0px", np_)
        check(dev + ": the flag is a star, and fills when tapped", r.get("star") is True and r.get("starOn") is True, (r.get("star"), r.get("starOn")))
        # REVISED IN 314: the "Starred" / "Star removed" words are gone.
        check(dev + ": and shows no words beside it (build 314)", r.get("starNote") == "", r.get("starNote"))
        check(dev + ": paused, the timer stays up in its paused colour", r.get("pausedTimer") is True and r.get("resumedTimer") is True)
        check(dev + ": Instant feedback is not offered in Drill", r.get("drillHasFeedback") is False)
        check(dev + ": in Exam with it on, a pick is judged and locked",
              r.get("examJudged") is True and r.get("examLocked") is True and r.get("examMode") == "Exam", (r.get("examJudged"), r.get("examLocked"), r.get("examMode")))
        # Build 305 put the name back to Review; the sheet, the list and the card all say the same thing.
        check(dev + ": the mode is called Review everywhere", r.get("sheetTitle") == "Review" and r.get("listTitle") == "Review", (r.get("sheetTitle"), r.get("listTitle")))
        check(dev + ": with Flashcards on, Begin says so and opens a card", r.get("beginText") == "Start flashcards" and r.get("fcCard") is True, r.get("beginText"))
        check(dev + ": the card has the count in the middle, Review on the left, no timer and a star",
              r.get("fcCount") == "1/12" and r.get("fcMode") == "Review" and r.get("fcTimer") is True and r.get("fcStar") is True,
              (r.get("fcCount"), r.get("fcMode"), r.get("fcTimer"), r.get("fcStar")))
        check(dev + ": a tap flips it", r.get("fcFlipped") is True)
        check(dev + ": the bar goes green as you go and un-greens going back", r.get("fcGreenAt3") == 2 and r.get("fcGreenBack") == 1, (r.get("fcGreenAt3"), r.get("fcGreenBack")))
        check(dev + ": Pause is the way out", r.get("fcPause") is True and r.get("fcLeft") is True, (r.get("fcPause"), r.get("fcLeft")))
        check(dev + ": the list's questions are cards with room between them", (r.get("listGap") or 0) >= 14 and (r.get("listCard") or 0) >= 10, (r.get("listGap"), r.get("listCard")))


def check_b304(br):
    """Build 304: an interrupted test is offered back, Ronin at 500, the
    unlock card's bar fills from its start, the Default banner tile has
    no theme rim, your own leaderboard row opens your card with Go to
    profile, characters move on the boards and in the tab bar, and every
    unlock card has a line saying how. Written against build 303; every
    group fails there."""
    print("\n74. build 304: resume, Ronin 500, unlock cards, your own card, live characters")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        CLEAR = "setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);"
        r = pg.evaluate("""async ()=>{
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const out = {};
          try{
          %s
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'up';
          showSetup(); await wait(400); document.getElementById('nextbtn').click(); await wait(400);
          document.querySelector('.sheet-begin-btn').click();
          for(let t = 0; t < 80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
          await wait(400);
          const pick = s => document.querySelector('.qpanel .choice[data-index="' + s + '"]').click();
          pick(correctSlot(order[pos])); await wait(300); advance(); await wait(600);
          pick(correctSlot(order[pos])); await wait(400);
          out.pos = pos; out.q = order[pos];
          out.saved = !!localStorage.getItem('class26e.runsession.v1');
          }catch(e){ out.err = String(e).slice(0, 200); }
          return out;
        }""" % CLEAR)
        # iOS throws the app away: the page loads again from nothing
        pg.reload()
        pg.wait_for_timeout(2600)
        pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub(); if(!document.querySelector('[data-screen=\"home\"]')) showHome();}")
        pg.wait_for_timeout(2600)
        r2 = pg.evaluate("""async ()=>{
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const out = {};
          try{
          %s
          const offer = document.getElementById('resume-offer');
          out.offer = offer ? offer.textContent : null;
          if(offer){ document.getElementById('resume-go').click(); await wait(900); }
          out.pos = typeof pos === 'number' ? pos : null; out.q = order && order[pos];
          out.inTest = testInProgress === true && !!document.querySelector('.qpanel .choice');
          /* leave it, so nothing below is inside a test */
          if(typeof clearRunSession === 'function') clearRunSession();
          testInProgress = false; showHome(); await wait(600);
          /* Ronin */
          out.ronin = CHARACTER_FEATS.bigtest400.label;
          /* the unlock card's bar, from its start */
          showUnlockDetail(characterDetail('hacker'));
          const fill = document.querySelector('.unlock-card-fill'), bar = document.querySelector('.unlock-card-bar');
          /* what SHOWS of the fill: it is full width and slides in
             (setBarFill), so the visible part is where it overlaps the
             track, and that must start at the track's left edge */
          const shown = () => { const f = fill.getBoundingClientRect(), b = bar.getBoundingClientRect();
            return { w: Math.max(0, Math.min(f.right, b.right) - Math.max(f.left, b.left)), left: Math.round(Math.max(f.left, b.left) - b.left) }; };
          out.barClip = bar ? getComputedStyle(bar).clipPath : null;
          out.barAtOpen = fill && bar ? shown().w : null;
          await wait(1500);
          out.barLater = fill && bar ? shown().w : null;
          out.barLeft = fill && bar ? shown().left : null;
          out.note = (document.querySelector('.unlock-card-note') || {}).textContent || '';
          document.querySelectorAll('.invite-overlay').forEach(n => n.remove());
          /* build 308: a line only where the rule has a catch - "only keep
             the ones that are needed". Which cards carry one: */
          const withNote = [];
          const look = o => { if(!o || !o.id) return; if(o.note || unlockNoteFor(o)) withNote.push(o.kind + ':' + o.id); };
          AVATAR_CHARACTERS.forEach(c => look(characterDetail(c.id)));
          BANNERS.forEach(b => look(bannerDetail(b.id)));
          out.withNote = withNote;
          out.rankNote = themeDetail('veteran').note;
          /* the Default banner tile: no theme colour bleeding as a rim */
          showCustomize('banner'); await wait(700);
          const art = document.querySelector('.banner-opt.is-none .banner-opt-art');
          out.noneBg = art ? getComputedStyle(art).backgroundImage : 'missing';
          /* your own row, your own card */
          if(!store.publicId) store.publicId = 'me-pub-304';
          const chars = AVATAR_CHARACTERS.map(c => c.id), rows = [];
          for(let i = 0; i < 24; i++) rows.push({ pub: 'p' + i, firstName: 'Classmate' + i, avatarChar: chars[(i * 3) %% chars.length], level: 60 - i * 2, badges: Math.max(0, 14 - i), hundos: 80 - i, xp: 90000 - i * 3000, correct: 9000 - i * 300, week: 4000 - i * 120, lastModified: Date.now() });
          rows.splice(3, 0, { pub: store.publicId, firstName: store.firstName, avatarChar: store.avatarChar, level: 57, badges: 12, hundos: 70, xp: 80000, correct: 8000, week: 3900, lastModified: Date.now() });
          leaderboardRows = rows;
          showRankings('level'); await wait(1500);
          const all = [...document.querySelectorAll('.rank-row:not(.rank-row-head)')];
          out.rows = all.length;
          /* char-flip counts (build 308): a row's character plays its
             recorded loop rather than the live svg - that is the lag fix. */
          out.liveRows = all.filter(x => x.querySelector('.rank-avatar-wrap.char-live, .rank-avatar-wrap.char-flip')).length;
          out.offRows = all.filter(x => x.classList.contains('is-offscreen')).length;
          const me = document.querySelector('.rank-row.lb-row-me');
          out.meTappable = !!(me && me.classList.contains('is-tappable'));
          if(me){ me.click(); await wait(700); }
          const card = document.querySelector('.person-card');
          out.cardAct = card ? (card.querySelector('.person-sheet-act') || {}).textContent : null;
          out.cardHint = card ? !!card.querySelector('.person-sheet-hint') : null;
          if(card){ card.querySelector('.person-sheet-act').click(); await wait(700); }
          out.toProfile = !!document.querySelector('.profile-hero') && !document.querySelector('.invite-overlay');
          /* the Customize button is not under the character's glow */
          const cb = document.querySelector('.profile-edit-btn');
          if(cb){ const b = cb.getBoundingClientRect(); const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2); out.customizeOnTop = !!(hit && (hit === cb || cb.contains(hit))); }
          /* the tab bar's character moves */
          store.avatarChar = chars.find(id => { const d = AVATAR_CHARACTERS.find(c => c.id === id); return d && !d.unlock && !d.feat; }) || chars[0];
          syncBottomTabAvatar(); await wait(300);
          /* Live, or a flip-book of its loop (build 308): either is moving. */
          /* A sheet may still be recording on a cold page, so give it a few seconds. */
          const sel = '#bottomtab-profile .bottomtab-icon.char-live svg, #bottomtab-profile .bottomtab-icon.char-flip .char-flip-play';
          for(let k = 0; k < 40 && !document.querySelector(sel); k++) await wait(150);
          out.tabLive = !!document.querySelector(sel);
          }catch(e){ out.err = String(e).slice(0, 200); }
          return out;
        }""" % CLEAR)
        ctx.close()
        check(dev + ": no error in the 304 run", "err" not in r and "err" not in r2, (r.get("err"), r2.get("err")))
        check(dev + ": a run in progress is saved as it goes", r.get("saved") is True)
        check(dev + ": coming back, it asks to continue the interrupted test",
              bool(r2.get("offer")) and "interrupted" in (r2.get("offer") or "").lower(), r2.get("offer"))
        check(dev + ": and Continue picks up on the same question",
              r2.get("inTest") is True and r2.get("pos") == r.get("pos") and r2.get("q") == r.get("q"), (r.get("pos"), r2.get("pos"), r2.get("inTest")))
        check(dev + ": Ronin asks for 500 questions", "500" in (r2.get("ronin") or ""), r2.get("ronin"))
        check(dev + ": the unlock card's bar starts empty at its left end and fills, inside a clipped track",
              r2.get("barAtOpen") is not None and r2["barAtOpen"] < 3 and (r2.get("barLater") or 0) > 3 and r2.get("barLeft") == 0
              and "inset" in (r2.get("barClip") or ""),
              (r2.get("barAtOpen"), r2.get("barLater"), r2.get("barLeft"), r2.get("barClip")))
        wn = set(r2.get("withNote") or [])
        need = {"character:detective", "character:marksman", "character:astronaut", "character:ronin", "character:zeus", "character:poseidon"}
        check(dev + ": the cards whose rule has a catch keep their line", need <= wn, sorted(need - wn))
        check(dev + ": a plain count has no line under its bar (build 308)",
              r2.get("note") == "" and not ({"character:hacker", "character:timekeeper", "banner:correct5000", "banner:study50"} & wn),
              (r2.get("note"), sorted(wn)))
        check(dev + ": a rank card says what the rank takes", "takes level" in (r2.get("rankNote") or ""), r2.get("rankNote"))
        check(dev + ": the Default banner tile has no theme colour behind it", r2.get("noneBg") == "none", r2.get("noneBg"))
        check(dev + ": your own leaderboard row is tappable", r2.get("meTappable") is True)
        check(dev + ": and opens your card with Go to profile, no friend line",
              r2.get("cardAct") == "Go to profile" and r2.get("cardHint") is False and r2.get("toProfile") is True,
              (r2.get("cardAct"), r2.get("cardHint"), r2.get("toProfile")))
        check(dev + ": every character on the board is alive, and rows out of view pause",
              r2.get("rows", 0) > 10 and r2.get("liveRows") == r2.get("rows") and (r2.get("offRows") or 0) > 0,
              (r2.get("rows"), r2.get("liveRows"), r2.get("offRows")))
        check(dev + ": the character in the tab bar is alive", r2.get("tabLive") is True)
        check(dev + ": the Customize button is on top of the character's glow", r2.get("customizeOnTop") is True, r2.get("customizeOnTop"))


def check_b304_polish(br):
    """Build 304, second list: the Profile card takes its banner's
    colours, a stat's explanation opens under the row you tapped, and
    Start says it is ready - a pop when it lights up, a halo and a sweep
    while it stays ready - with the start sheet's Begin raised to match.
    Written against build 303: every check of the change fails there; the
    two that pass are "no error" and the guard that a grey Start stays
    still, which is a property 303 already had and 304 must keep."""
    print("\n75. build 304: banner-tinted Profile card, stat answers in place, Start that says it is ready")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const out = {};
          try{
          setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          /* the card under a banner wears that banner's colours */
          bannerEarned = () => true;
          const tints = [];
          for(const id of ['tests100', 'vr50', 'exam100']){
            store.banner = id; showProfile('profile'); await wait(500);
            const hero = document.querySelector('.profile-hero');
            tints.push({ id, t1: hero.style.getPropertyValue('--hero-t1').trim(), bg: getComputedStyle(hero).backgroundImage });
          }
          out.tints = tints.map(t => ({ id: t.id, t1: t.t1, tinted: /gradient/.test(t.bg) }));
          out.distinct = new Set(tints.map(t => t.t1)).size;
          store.banner = ''; showProfile('profile'); await wait(500);
          out.defaultTinted = /gradient/.test(getComputedStyle(document.querySelector('.profile-hero')).backgroundImage);
          /* a stat's answer opens under the tapped card's row */
          showProfile('stats'); await wait(700);
          const cards = [...document.querySelectorAll('.stat-card')];
          const first = cards[0]; first.scrollIntoView({ block: 'center' }); await wait(200); first.click(); await wait(400);
          const box = document.querySelector('.stat-why');
          out.whyGap = Math.round(box.getBoundingClientRect().top - first.getBoundingClientRect().bottom);
          out.whyInGrid = box.parentElement === first.parentElement;
          out.whyVisible = !box.hidden && box.getBoundingClientRect().bottom <= innerHeight;
          /* Start: a pop as it lights up, then a halo and a sweep */
          store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(800);
          const tab = document.getElementById('bottomtab-start');
          out.inertBefore = tab.classList.contains('is-inert');
          out.inertAnim = getComputedStyle(tab, '::after').animationName;
          [...document.querySelectorAll('.screen-setup .pick')].find(p => /Identity Crimes/.test(p.textContent)).click(); await wait(100);
          out.pop = tab.classList.contains('just-ready');
          out.fill = getComputedStyle(tab, '::before').animationName;
          /* 1300 since 313: the fill is .6s and the pop and sheen follow it */
          await wait(1300);
          out.popGone = !tab.classList.contains('just-ready');
          out.halo = getComputedStyle(tab, '::after').animationName;
          out.sweep = getComputedStyle(tab).animationName;
          tab.click(); await wait(900);
          const b = document.querySelector('.sheet-begin-btn');
          const bs = getComputedStyle(b), bb = getComputedStyle(b, '::before');
          out.begin = { anim: bs.animationName, halo: getComputedStyle(b, '::after').animationName,
                        icon: (bb.webkitMaskImage || bb.maskImage || '').indexOf('svg') >= 0, lip: /inset/.test(bs.boxShadow) && (bs.boxShadow.match(/rgba?\(/g) || []).length >= 4 };
          }catch(e){ out.err = String(e).slice(0, 200); }
          return out;
        }""")
        ctx.close()
        check(dev + ": no error in the 304 polish run", "err" not in r, r.get("err"))
        check(dev + ": the Profile card under a banner is tinted, and differently per banner",
              all(t["tinted"] and t["t1"] for t in r.get("tints", [])) and r.get("distinct") == 3, r.get("tints"))
        check(dev + ": the default banner's card takes the theme's colours", r.get("defaultTinted") is True)
        check(dev + ": a stat's explanation opens directly under the row you tapped",
              r.get("whyInGrid") is True and 0 <= (r.get("whyGap") or -1) <= 20 and r.get("whyVisible") is True,
              (r.get("whyInGrid"), r.get("whyGap"), r.get("whyVisible")))
        check(dev + ": a grey Start does not animate", r.get("inertBefore") is True and r.get("inertAnim") in ("none", ""), r.get("inertAnim"))
        check(dev + ": Start fills from its centre once as it lights up (build 308)",
              r.get("pop") is True and r.get("fill") == "start-fill-in" and r.get("popGone") is True, (r.get("pop"), r.get("fill"), r.get("popGone")))
        check(dev + ": and once ready it does not pulse - no halo, no sweep (build 308)",
              r.get("halo") in ("none", "") and r.get("sweep") in ("none", ""), (r.get("halo"), r.get("sweep")))
        bg = r.get("begin") or {}
        check(dev + ": the sheet's Begin is raised, marked with a play icon, and does not pulse",
              bg.get("icon") and bg.get("lip") and bg.get("halo") in ("none", "") and bg.get("anim") in ("none", ""), bg)


def check_b304_noxpfly(br):
    """Build 304: no XP banner flies into Profile after a run. A drill
    with one miss, its retake, then Main menu - the reported route - and
    Home is watched for the fly. Written against 303, where it flies."""
    print("\n76. build 304: no XP fly into Profile after a run")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
      setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); theme.reduceMotion = true; applyTheme();
      cfg.mode='drill'; cfg.units=['Identity Crimes']; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false;
      beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes')), null); }""")
    def play(miss_first):
        pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(400)
        for i in range(40):
            if pg.evaluate("()=>!!document.querySelector('.rs-rewards')"): break
            p = pg.evaluate("()=>pos")
            pg.evaluate("""(m)=>{ const r=correctSlot(order[pos]); const pick=s=>document.querySelector('.qpanel .choice[data-index="'+s+'"]').click();
              if(m) pick((r+1)%4); pick(r); }""", miss_first and i == 0)
            pg.wait_for_timeout(250)
            pg.evaluate("()=>{ const b=document.getElementById('nextbtn'); if(b && !b.hidden) b.click(); }")
            for _ in range(40):
                pg.wait_for_timeout(100)
                if pg.evaluate("()=>pos") != p or pg.evaluate("()=>!!document.querySelector('.rs-rewards')"): break
        for _ in range(150):
            pg.wait_for_timeout(200)
            if pg.evaluate("()=>!!document.querySelector('.rs-rewards.rs-done')"): break
    play(True)
    pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
      document.querySelector('.rs-continue').click(); await w(900);
      [...document.querySelectorAll('button')].find(b => /Retake missed/.test(b.textContent)).click(); }""")
    play(False)
    r = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
      let flew = false;
      const mo = new MutationObserver(() => { if(document.getElementById('welcomebonus-banner')) flew = true; });
      mo.observe(document.body, { childList: true, subtree: true });
      const mm = [...document.querySelectorAll('.rs-actions button')].find(b => /Main menu/.test(b.textContent));
      const had = !!mm; if(mm) mm.click(); await w(2500); mo.disconnect();
      return { had, flew, home: !!document.querySelector('[data-screen="home"]') }; }""")
    ctx.close()
    check("the retake ends on a results screen with Main menu", r.get("had") is True, r)
    check("Main menu lands on Home with no XP flying into Profile", r.get("home") is True and r.get("flew") is False, r)
    # "Unless it's a daily question": its result is a small box, so its XP still flies.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    d = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
      setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); theme.reduceMotion = true; applyTheme();
      try{ startDailyQuestion(); }catch(e){ return { err: String(e).slice(0, 120) }; }
      for(let t = 0; t < 60 && !document.querySelector('.qpanel .choice'); t++) await w(100);
      const c = document.querySelector('.qpanel .choice[data-index="' + correctSlot(order[pos]) + '"]');
      if(!c) return { noQuestion: true };
      c.click(); const sb=document.getElementById('dailyq-submitbtn'); if(sb && !sb.disabled) sb.click();
      for(let t = 0; t < 60 && !document.getElementById('dailyq-exitbtn'); t++) await w(100);
      let flew = false;
      const mo = new MutationObserver(() => { if(document.getElementById('welcomebonus-banner')) flew = true; });
      mo.observe(document.body, { childList: true, subtree: true });
      const ex = document.getElementById('dailyq-exitbtn'); const had = !!ex; if(ex) ex.click();
      await w(2500); mo.disconnect();
      return { had, flew }; }""")
    ctx.close()
    check("after the daily question, its XP still flies into Profile", d.get("had") is True and d.get("flew") is True, d)


def check_b305_flashcards(br):
    """Build 305: every flashcard's answer side lists the choices with
    the right one marked, and nothing on a card is cut off on the
    smallest phone; the end of a deck is centred under the bar and its
    second button is Main menu, which lands on Home. Written against
    304, where only "All of the above" cards listed choices and the end
    screen sat at the top with Done going back to the setup screen."""
    print("\n77. build 305: flashcard answers list the choices, long cards read; the end of a deck")
    for w, h in ((375, 667), (440, 956), (834, 1194)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          const units = [...new Set(QUESTIONS.map(q => q.topic))];
          showFlashcards(units, 'all', {}); await w(300);
          let bad = 0, clipped = 0, worst = 0, dupLong = 0, noHead = 0, shortFs = 999, longFs = 0; const n = fc.deck.length;
          for(let i = 0; i < n; i++){
            fc.pos = i; renderFlashcard(0);
            const b = document.querySelector('.fc-back');
            const lis = b.querySelectorAll('.fc-choices li'), right = b.querySelectorAll('.fc-choices li.is-answer');
            if(lis.length !== QUESTIONS[fc.deck[i]].choices.length || right.length !== 1) bad++;
            const o = Math.max(...[...document.querySelectorAll('.fc-face')].map(f => f.scrollHeight - f.clientHeight));
            if(o > 1){ clipped++; worst = Math.max(worst, o); }
            const q = QUESTIONS[fc.deck[i]], al = String(q.choices[q.answer]).length, ql = String(q.q).length;
            const head = b.querySelector('.fc-text');
            if(head) dupLong++;
            const fs = parseFloat(getComputedStyle(document.querySelector('.fc-front .fc-text')).fontSize);
            if(ql <= 90) shortFs = Math.min(shortFs, fs); if(ql > 280) longFs = Math.max(longFs, fs);
          }
          fcLeave(); showFlashcards(['Identity Crimes'], 'all', {}); await w(300);
          showFlashcardsDone(); await w(300);
          const p = document.querySelector('.fc-done'), a = document.querySelector('.fc-done-actions');
          const pr = p.getBoundingClientRect();
          const t = document.querySelector('.fc-done-title').getBoundingClientRect(), ar = a.getBoundingClientRect();
          const groupMid = (t.top + ar.bottom) / 2, panelMid = (pr.top + pr.bottom) / 2;
          const labels = [...a.querySelectorAll('button')].map(b => b.textContent.trim());
          const mm = [...a.querySelectorAll('button')].find(b => /Main menu/.test(b.textContent));
          const btnMid = Math.round(ar.left + ar.width / 2 - innerWidth / 2);
          if(mm) mm.click(); await w(900);
          return { n, bad, clipped, worst, dupLong, noHead, shortFs, longFs, labels, btnMid, offCentre: Math.round(groupMid - panelMid), panelH: Math.round(pr.height), vh: innerHeight,
                   home: !!document.querySelector('[data-screen="home"]') }; }""")
        ctx.close()
        dev = "%dx%d" % (w, h)
        check(dev + ": every card's answer side lists its choices, one marked right", r.get("bad") == 0 and r.get("n", 0) > 100, (r.get("n"), r.get("bad")))
        check(dev + ": no card is cut off, on either side", r.get("clipped") == 0, (r.get("clipped"), r.get("worst")))
        check(dev + ": the answer side is the choices alone, no answer printed above them", r.get("dupLong") == 0, r.get("dupLong"))
        check(dev + ": a long question is set smaller than a short one", 0 < r.get("longFs", 0) < r.get("shortFs", 0) * 0.8, (r.get("shortFs"), r.get("longFs")))
        check(dev + ": the end of a deck offers Go again and Main menu", r.get("labels") == ["Go again", "Main menu"], r.get("labels"))
        check(dev + ": its buttons are centred across the screen", r.get("btnMid") is not None and abs(r["btnMid"]) <= 2, r.get("btnMid"))
        check(dev + ": and the group sits in the middle of the space under the bar", r.get("panelH", 0) > r.get("vh", 0) * 0.5 and abs(r.get("offCentre") or 999) <= 40, (r.get("offCentre"), r.get("panelH")))
        check(dev + ": Main menu lands on Home", r.get("home") is True, r)


def check_b305_resultstap(br):
    """Build 305: a tap on the results screen while it is still coming in
    never leaves it. The run's buttons were on the panel from the start at
    opacity 0, so a tap where Main menu would be went Home - "I tapped the
    screen ... while the test results came up ... it send me back to the
    main menu". A tap now finishes the card on screen and brings the NEXT
    one in (not the whole reveal), and Main menu works once it is there.
    Written against 305-pre-fix, where the first check goes Home."""
    print("\n78. build 305: a tap during the results reveal speeds it up, never leaves")
    for w, h in ((440, 956), (834, 1194)):
        dev = "%dx%d" % (w, h)
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        pg.evaluate("""()=>{ setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); theme.reduceMotion = true; applyTheme();
          cfg.mode='drill'; cfg.units=['Identity Crimes']; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false;
          beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes')), null); }""")
        pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(300)
        for i in range(40):
            p = pg.evaluate("()=>pos"); last = pg.evaluate("()=>pos===order.length-1")
            if last: pg.evaluate("()=>{ theme.reduceMotion=false; applyTheme(); }")
            pg.evaluate("""()=>{ const r=correctSlot(order[pos]); document.querySelector('.qpanel .choice[data-index="'+r+'"]').click(); }""")
            pg.wait_for_timeout(150)
            if last: pg.wait_for_timeout(500); break
            pg.evaluate("()=>{ const b=document.getElementById('nextbtn'); if(b && !b.hidden) b.click(); }")
            for _ in range(60):
                pg.wait_for_timeout(30)
                if pg.evaluate("()=>pos") != p: break
        pg.evaluate("()=>document.getElementById('nextbtn').click()")
        pg.wait_for_selector(".rs-rewards", timeout=5000); pg.wait_for_timeout(150)
        where = pg.evaluate("""()=>{ const b=[...document.querySelectorAll('.rs-actions button')].find(x=>/Main menu/.test(x.textContent));
          const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }""")
        pg.touchscreen.tap(where[0], where[1]); pg.wait_for_timeout(900)
        r1 = pg.evaluate("()=>({ home: !!document.querySelector('[data-screen=\"home\"]'), results: !!document.querySelector('.rs-rewards') })")
        check(dev + ": a tap where Main menu will be, before it is there, stays on the results", r1["results"] and not r1["home"], r1)
        # one tap, one card
        landed = "()=>document.querySelectorAll('.rs-rewards .rs-land.rs-in, .rs-rewards .rs-land.rs-in-now').length"
        total = pg.evaluate("()=>document.querySelectorAll('.rs-rewards .rs-land').length")
        before = pg.evaluate(landed)
        pg.touchscreen.tap(w / 2, h * 0.45); pg.wait_for_timeout(60)
        after = pg.evaluate(landed)
        check(dev + ": a tap on the screen brings in the next card, not the rest of them",
              after == before + 1 and after < total, (before, after, total))
        for _ in range(150):
            pg.wait_for_timeout(200)
            if pg.evaluate("()=>!!document.querySelector('.rs-rewards.rs-done')"): break
        # measured again HERE, once the page has stopped moving: the finished reveal scrolls the buttons into view
        # (50-94px on a phone when the machine is busy), so the spot measured
        # before the reveal can be empty page by now - that tap missed, it was
        # not the app ignoring one
        where = pg.evaluate("""async ()=>{ const b=[...document.querySelectorAll('.rs-actions button')].find(x=>/Main menu/.test(x.textContent));
          let last = null, still = 0;
          for(let k = 0; k < 60 && still < 4; k++){ await new Promise(r => setTimeout(r, 100));
            const y = Math.round(b.getBoundingClientRect().top) + '|' + Math.round(scrollY); still = y === last ? still + 1 : 0; last = y; }
          const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }""")
        pg.touchscreen.tap(where[0], where[1]); pg.wait_for_timeout(1200)
        r2 = pg.evaluate("()=>!!document.querySelector('[data-screen=\"home\"]')")
        ctx.close()
        check(dev + ": once it has landed, Main menu goes Home", r2 is True, r2)


def check_b306_marks(br):
    """Build 306: a wrong pick shows a cross the way a right one shows a
    tick, both centred in their row; the count at the top reads like the
    mode name beside it in every mode; flashcards have a white bar and
    room under the star. Written against 305, where a wrong pick had no
    mark, the tick rode high, the count was white mono and the bar green."""
    print("\n79. build 306: tick and cross centred, a grey count, a white flashcard bar")
    for w, h in ((440, 956), (834, 1194)):
        dev = "%dx%d" % (w, h)
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          const mid = b => { const k=b.querySelector('.mark'), br=b.getBoundingClientRect(); const rg=document.createRange(); rg.selectNodeContents(k); const g=rg.getBoundingClientRect();
            return { text:k.textContent, off: Math.round((g.top+g.height/2) - (br.top+br.height/2)), color: getComputedStyle(k).color }; };
          const same = () => { const a=getComputedStyle(document.getElementById('testmodelabel')), b=getComputedStyle(document.getElementById('testqcounter'));
            return a.color===b.color && a.fontSize===b.fontSize && a.fontWeight===b.fontWeight && a.fontFamily===b.fontFamily; };
          cfg.mode='drill'; cfg.units=['Identity Crimes']; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false;
          beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes')), null);
          for(let t=0; t<80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
          await wait(400);
          const right = correctSlot(order[pos]);
          document.querySelector('.qpanel .choice[data-index="'+((right+1)%4)+'"]').click(); await wait(450);
          const wb = document.querySelector('.qpanel .choice.is-wrong-flash'); out.wrong = wb ? mid(wb) : null;
          document.querySelector('.qpanel .choice[data-index="'+right+'"]').click(); await wait(500);
          const rb = document.querySelector('.qpanel .choice.is-right'); out.right = rb ? mid(rb) : null;
          out.drillSame = same();
          out.keyOff = Math.max(...[...document.querySelectorAll('.qpanel .choice')].map(b => { const k=b.querySelector('.key'), br=b.getBoundingClientRect(); const rg=document.createRange(); rg.selectNodeContents(k); const g=rg.getBoundingClientRect(); return Math.abs(Math.round((g.top+g.height/2)-(br.top+br.height/2))); }));
          testInProgress = false;
          cfg.mode='exam'; cfg.timer='on'; cfg.timerMinutes=60;
          beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes')), null);
          for(let t=0; t<80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
          await wait(300); out.examSame = same();
          testInProgress = false;
          const qi = QUESTIONS.findIndex(q=>/clearly define acts constituting racial profiling, strictly/.test(q.choices[q.answer]));
          showFlashcards([QUESTIONS[qi].topic], 'all', {}); const at=fc.deck.indexOf(qi); fc.deck.splice(at,1); fc.deck.splice(3,0,qi); fc.pos=3; renderFlashcard(0); await wait(300);
          out.fcSame = same();
          const tc = document.querySelector('#meter .tick.clean'), tn = document.querySelector('#meter .tick.now');
          out.cleanBg = tc ? getComputedStyle(tc).backgroundColor : null; out.nowBg = tn ? getComputedStyle(tn).backgroundColor : null;
          const s = document.querySelector('.fc-back .fc-star').getBoundingClientRect(), l = document.querySelector('.fc-back .fc-choices li').getBoundingClientRect();
          out.starGap = Math.round(l.top - s.bottom);
          return out; }""")
        ctx.close()
        wr, rt = r.get("wrong") or {}, r.get("right") or {}
        check(dev + ": a wrong pick shows a cross in the wrong colour", wr.get("text") == "\u2715" and wr.get("color") not in ("rgba(0, 0, 0, 0)", "transparent"), wr)
        check(dev + ": the cross sits in the middle of its row", abs(wr.get("off", 99)) <= 2, wr.get("off"))
        check(dev + ": the tick sits in the middle of its row", rt.get("text") == "\u2713" and abs(rt.get("off", 99)) <= 2, rt)
        check(dev + ": every choice's letter sits in the middle of its row", r.get("keyOff") is not None and r["keyOff"] <= 2, r.get("keyOff"))
        check(dev + ": the count reads like the mode name in a drill, an exam and flashcards",
              r.get("drillSame") is True and r.get("examSame") is True and r.get("fcSame") is True, (r.get("drillSame"), r.get("examSame"), r.get("fcSame")))
        def green(c):
            import re
            n = [float(x) for x in re.findall(r"[\d.]+", c or "")]
            return len(n) >= 3 and n[1] > n[0] + 40 and n[1] > n[2] + 20
        # REVISED IN 311: "Maybe we don't make the color green for the progress
        # bar ... white is boring and green kinda makes me think of test and
        # xp." Its own colour now: a violet, neither green nor white nor grey.
        def violet(c):
            import re
            n = [float(x) for x in re.findall(r"[\d.]+", c or "")]
            return len(n) >= 3 and n[2] > n[1] + 40 and n[0] > n[1] + 10
        check(dev + ": the flashcard bar is its own colour - violet, not green or white (build 311)",
              violet(r.get("cleanBg")) and not green(r.get("cleanBg")), (r.get("cleanBg"), r.get("nowBg")))
        check(dev + ": a wordy card's first choice is clear of the star", (r.get("starGap") or 0) >= 8, r.get("starGap"))


def check_b306_fcmotion(br):
    """Build 306: a flashcard only moves on when it is dragged most of the
    way across - a short drag springs back - and the arrow throws it the
    same way; two quick taps on the arrow still move two cards. The flip
    lifts the card. A right answer glows like a wrong one, both faint.
    Written against 305, where a 60px flick moved the deck."""
    print("\n80. build 306: flashcards swipe all the way or spring back; matched faint glows")
    for w, h in ((440, 956), (834, 1194)):
        dev = "%dx%d" % (w, h)
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate("()=>{ document.querySelectorAll('#pushing-update,#intro-pop,.rs-spot').forEach(n=>n.remove()); cfg.mode='review'; cfg.flashcards=true; showFlashcards(['Identity Crimes'],'all',{}); }")
        pg.wait_for_timeout(800)
        b = pg.evaluate("()=>{ const r=document.querySelector('.fc-card').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
        cx, cy = b[0] + b[2] / 2, b[1] + b[3] / 2
        def drag(frac):
            pg.mouse.move(cx + 50, cy); pg.mouse.down()
            for i in range(1, 21):
                pg.mouse.move(cx + 50 - b[2] * frac * i / 20, cy); pg.wait_for_timeout(16)
            pg.mouse.up(); pg.wait_for_timeout(700)
            return pg.evaluate("()=>fc.pos")
        short = drag(0.25)
        full = drag(0.6)
        pg.mouse.click(cx, cy); pg.wait_for_timeout(120)
        lifting = pg.evaluate("()=>document.querySelector('.fc-card').classList.contains('is-flipping')")
        pg.wait_for_timeout(900)
        pg.evaluate("()=>{ document.getElementById('fcnext').click(); }"); pg.wait_for_timeout(120)
        pg.evaluate("()=>{ document.getElementById('fcnext').click(); }"); pg.wait_for_timeout(700)
        twice = pg.evaluate("()=>fc.pos")
        ctx.close()
        check(dev + ": a short drag springs back and stays on the card", short == 0, short)
        check(dev + ": a drag most of the way across moves to the next card", full == 1, full)
        check(dev + ": two quick taps on the arrow move two cards", twice == 3, twice)
        check(dev + ": the flip lifts the card as it turns", lifting is True, lifting)
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    g = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      cfg.mode='drill'; cfg.units=['Identity Crimes']; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false;
      beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes')), null);
      for(let t=0; t<80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
      await wait(400); const r = correctSlot(order[pos]);
      /* sample the picked box's border every frame: build 313 wants the
         colour to arrive over a few hundred ms, not land in one frame */
      const trace = async (sel) => { const seen = []; const t0 = performance.now();
        while(performance.now() - t0 < 900){ const e = document.querySelector(sel); if(e) seen.push(getComputedStyle(e).borderTopColor + ' | ' + getComputedStyle(e.querySelector('.bar')).backgroundColor); await new Promise(r => requestAnimationFrame(r)); }
        return seen; };
      document.querySelector('.qpanel .choice[data-index="'+((r+1)%4)+'"]').click();
      const wt = await trace('.qpanel .choice.is-wrong-flash');
      const wb = document.querySelector('.qpanel .choice.is-wrong-flash');
      const ws = wb ? getComputedStyle(wb).boxShadow : 'missing';
      const wa = wb ? getComputedStyle(wb, '::after').content : 'missing';
      document.querySelector('.qpanel .choice[data-index="'+r+'"]').click();
      const rt = await trace('.qpanel .choice.is-right');
      const rb = document.querySelector('.qpanel .choice.is-right');
      const rs = getComputedStyle(rb).boxShadow, ra = getComputedStyle(rb, '::after').content;
      return { ws, rs, wa, ra, wt, rt }; }""")
    ctx.close()
    # Build 313 reversed build 306's "a faint glow on both": "does not
    # need that glow effect when selecting it, it's too much ... the stuff
    # already green could phase in instead of instantly".
    check("a picked answer has no glow, right or wrong", g["rs"] == "none" and g["ws"] == "none", (g["rs"], g["ws"]))
    check("and no colour sweeps across it", g["ra"] in ("none", "normal") and g["wa"] in ("none", "normal"), (g["ra"], g["wa"]))
    for name, tr in (("right", g["rt"]), ("wrong", g["wt"])):
        borders = list(dict.fromkeys(x.split(" | ")[0] for x in tr))
        bars = list(dict.fromkeys(x.split(" | ")[1] for x in tr))
        check("the %s colour fades in over several frames, not in one (border and edge bar)" % name,
              len(borders) >= 4 and len(bars) >= 4, (borders[:4], bars[:4]))


def check_b308_timer(br):
    """Build 308: the two timer switches are one-or-the-other and both
    always show (Track my time used to vanish whenever Countdown was on,
    and turning one on left the other still showing on); no timer note
    over the unit list; and the sliders take any whole number but pull
    towards fives. Written against 307, where every one of these fails."""
    print("\n81. build 308: timer switches exclusive and always shown; sliders pull to fives")
    for w, h in ((440, 956), (834, 1194)):
        dev = "%dx%d" % (w, h)
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          /* REVISED IN 309: arriving with no units picked is a new test and
             resets the sheet, so the preset rides in with a unit picked -
             the round trip that keeps what you set. */
          cfg.mode='drill'; cfg.units=topicsIn(QUESTIONS).filter(u => !/penal/i.test(u)); cfg.timer='down'; cfg.timerMinutes=20; showSetup(); await wait(400);
          const note = document.querySelector('.screen-setup .info-note');
          const noteTxt = note && !note.hidden ? note.textContent : '';
          const m = document.getElementById('unitoptions-modal'); m.hidden = false;
          m.querySelector('.more-toggle')?.click(); await wait(400);
          /* by name, not position: build 310 put the stopwatch first */
          const allRows = [...m.querySelectorAll('.timer-sect > .opt')];
          const rows = [allRows.find(r => /Countdown|Time limit/.test(r.textContent)), allRows.find(r => /Stopwatch|Track my time/.test(r.textContent))].filter(Boolean);
          const st = () => rows.map(r => (r.hidden || !r.offsetParent ? 'H' : '') + (r.querySelector('input').checked ? 'on' : 'off')).join('/');
          const out = { noteTxt, n: rows.length, start: st() };
          rows[1].querySelector('input').click(); await wait(150); out.watch = st() + ' ' + cfg.timer;
          rows[0].querySelector('input').click(); await wait(150); out.limit = st() + ' ' + cfg.timer;
          const mins = m.querySelector('.minutes-sect input[type=range]');
          out.mins = [69.0, 69.5, 70.4, 71.0].map(v => { mins.value = v; mins.dispatchEvent(new Event('input')); return cfg.timerMinutes; });
          const how = m.querySelector('.howmany-sect input[type=range]');
          out.how = [69.0, 69.5, 70.4].map(v => { how.value = v; how.dispatchEvent(new Event('input')); return cfg.size; });
          return out; }""")
        ctx.close()
        check(dev + ": no timer note over the unit list", not r["noteTxt"], r["noteTxt"])
        check(dev + ": both timer switches show with Countdown on", r["n"] == 2 and r["start"] == "on/off", r["start"])
        check(dev + ": Track my time on turns Countdown off", r["watch"] == "off/on up", r["watch"])
        check(dev + ": Countdown on turns Track my time off", r["limit"] == "on/off down", r["limit"])
        check(dev + ": Minutes reaches 69 and pulls 69.5 and 70.4 to 70", r["mins"] == [69, 70, 70, 71], r["mins"])
        check(dev + ": How many does the same", r["how"] == [69, 70, 70], r["how"])


UNLOCK_ORDER_RUN = """async (a)=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
  const log = [];
  /* Every scene and pop-up answers at once and says what it was. */
  window.playBadgeCaseScene = (units, done) => { log.push('badge'); setTimeout(done, 20); return {}; };
  window.playTierCutscene = (k, o) => { log.push('rank:' + k); setTimeout(() => o && o.onDone && o.onDone(), 20); return {}; };
  window.playSupernovaCutscene = (o) => { log.push('rank:titan'); setTimeout(() => o && o.onDone && o.onDone(), 20); return {}; };
  window.playUnlockSpotlight = (it, n, of, release) => {
    log.push('spot:' + it.kind + (it.kind === 'rankrewards' ? '[' + it.parts.map(p => p.kind).join('+') + ']' : ''));
    setTimeout(release, 20); return { skip(){}, stop(){} }; };
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics.find(x => x === 'Identity Crimes') || topics[0];
  store.unitPerfects = {}; store.unitPerfects[t] = Math.max(0, badgeThresholdFor(t) - 1);
  store.lifetime.points = 30000; store.pendingBadgeUnlocks = [];
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [t];
  order = QUESTIONS.map((q,i) => [q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
  attempts = {}; picked = {}; timedOutSet = {};
  order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  const rankBefore = rankOf(store);
  summarize();
  for(let i = 0; i < 400 && !document.querySelector('.rs-rewards.rs-done'); i++) await wait(100);
  return { log, rankBefore, rankAfter: rankOf(store), rows: document.querySelectorAll('.rs-unlock-row, .rs-unlocked .unlockbanner').length };
}"""


def check_b308_unlocks(br):
    """Build 308: the unlock sequence. The badge's case first (it is what
    tips the rank), then the rank's scene, then ONE card for everything
    the rank handed over; the rank scene turns the flares round a still
    planet and lights the rank's own flare before the flash; the badge
    spins in on its own and is named before the case comes up, and the
    case's lid lifts towards you; pop-ups stay up for a good while; the
    Masked One's red mark stays on the mask; the results character is
    bigger. Written against 306/307, where these fail."""
    print("\n82. build 308: unlock order, rank orbit, badge case, pop-up hold")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate(UNLOCK_ORDER_RUN)
    ctx.close()
    log = r["log"]
    check("a badge that tips a rank: the case plays first", bool(log) and log[0] == "badge", log)
    rk = [i for i, x in enumerate(log) if x.startswith("rank:")]
    check("then the rank's own scene", bool(rk) and rk[0] == 1, log)
    rew = [x for x in log if x.startswith("spot:")]
    check("then one card for the rank's rewards, not one each",
          len(rew) >= 1 and (rew[0].startswith("spot:rankrewards") or len(rew) == 1)
          and not any(x in ("spot:theme",) for x in rew[1:]), log)

    for w, h in ((440, 956), (834, 1194)):
        dev = "%dx%d" % (w, h)
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        sc = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          playTierCutscene('vanguard', { from: 'veteran', onDone(){} });
          await wait(1800);
          const o = document.querySelector('#supernova-cutscene .rank-before .rank-orbit');
          const spin = document.querySelector('#supernova-cutscene .rank-spin');
          const main = document.querySelector('#supernova-cutscene .rank-before .cosmic-hero-main').getBoundingClientRect();
          const slots = [...o.querySelectorAll('.rank-orbit-slot')].map(s => s.getBoundingClientRect());
          const cx = slots.reduce((a, r) => a + r.left + r.width / 2, 0) / slots.length;
          const cy = slots.reduce((a, r) => a + r.top + r.height / 2, 0) / slots.length;
          const off = Math.hypot(cx - (main.left + main.width / 2), cy - (main.top + main.height * 162 / 342)) / main.width;
          const rot1 = getComputedStyle(o).rotate;
          await wait(1800);
          const rot2 = getComputedStyle(o).rotate;
          const lit = document.querySelector('#supernova-cutscene .rank-before .rank-orbit-slot.is-igniting .cosmic-badge-lit');
          const burst = document.getElementById('supernova-cutscene').classList.contains('supernova-burst');
          return { planetStill: getComputedStyle(spin).transform === 'none', rot1, rot2, off: +off.toFixed(3), slots: slots.length, lit: !!lit, burstYet: burst };}""")
        ctx.close()
        check(dev + ": the planet itself does not spin", sc["planetStill"], sc)
        check(dev + ": the seven flares turn round it", sc["slots"] == 7 and sc["rot1"] != sc["rot2"], sc)
        check(dev + ": centred on the planet, not beside it", sc["off"] < 0.03, sc["off"])
        check(dev + ": the rank's flare lights while they turn, before the flash", sc["lit"] and not sc["burstYet"], sc)

        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        bc = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          playBadgeCaseScene(['Identity Crimes'], ()=>{});
          await wait(2600);
          const kase = document.querySelector('.bc-case');
          const intro = document.querySelector('.bc-intro');
          const first = { caseOp: +getComputedStyle(kase).opacity, introIn: intro && intro.classList.contains('is-in'),
                          named: intro ? intro.textContent : '' };
          await wait(5800);
          const m = getComputedStyle(document.querySelector('.bc-lid')).transform;
          const v = (m.match(/matrix3d\\(([^)]*)\\)/) || [, ''])[1].split(',').map(Number);
          return { first, lidSin: v.length > 6 ? v[6] : null, lidOpen: kase.classList.contains('bc-open') };}""")
        ctx.close()
        check(dev + ": the badge comes up alone first, named", bc["first"]["caseOp"] < 0.05 and bc["first"]["introIn"]
              and "Identity Crimes" in bc["first"]["named"], bc["first"])
        check(dev + ": the lid lifts towards you, not down into the case", bc["lidOpen"] and (bc["lidSin"] or 0) > 0.3, bc)

    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    ex = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      const id = (typeof BANNERS !== "undefined" && BANNERS.length) ? BANNERS[BANNERS.length-1].id : null;
      const it = id ? bannerUnlockItem(id) : characterUnlockItem(AVATAR_CHARACTERS[AVATAR_CHARACTERS.length-1].id);
      playUnlockSpotlight(it, 1, 1, ()=>{});
      await wait(7000);
      const still = !!document.querySelector('.rs-spot.is-up');
      document.querySelectorAll('.rs-spot').forEach(n => n.remove());
      const svg = buildAvatarCharSVGFresh('masked');
      const mark = svg.querySelector('.cx-mkmark');
      const clip = mark && mark.getAttribute('clip-path');
      const inside = !!(mark && mark.querySelector('.cx-fx-mk3bolt') && mark.querySelector('.cx-fx-mk2crack'));
      const a = document.createElement('span'); a.className = 'results-level-avatar'; document.body.appendChild(a);
      const px = a.getBoundingClientRect().width; a.remove();
      return { still, clip, inside, px };}""")
    ctx.close()
    check("a pop-up is still up after 7 seconds untouched", ex["still"], ex)
    check("the Masked One's red mark is clipped to the mask", bool(ex["clip"]) and ex["inside"], ex)
    check("the results character's circle is bigger (at least 4.2rem)", ex["px"] >= 4.2 * 16 - 1, ex["px"])


# --------------------------------------------------------------------------
# BUILD 314 (Home, ranks, performance, chat). Every section below was
# written against build 313 and fails there; see each docstring.
# --------------------------------------------------------------------------

def _seed_gold_js():
    """In-page JS that puts the account on Gold (veteran), whatever the
    thresholds are this build: the badges and then the XP for the level."""
    return """(() => { const rule = TIER_UNLOCKS.veteran; const U = topicsIn(QUESTIONS);
      store.unitPerfects = store.unitPerfects || {};
      U.slice(0, rule.badges).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
      U.slice(rule.badges).forEach(u => store.unitPerfects[u] = 0);
      store.lifetime = store.lifetime || {}; let n = 0;
      while(levelOf(store) < rule.level && n++ < 4000) store.lifetime.points = (store.lifetime.points || 0) + 2000;
      return rankOf(store); })()"""


def check_b314h_flares(br):
    """Build 314: "The secret flares you haven't got, you shouldn't be able
    to see their colors" and the found ones' "random shine ... just a tiny
    bit less". On 313 the next flare wore its colour (--fc was its real
    colour on every dot), the Home hint card drew the missing flare in its
    colour, and the glint peaked at full size and full brightness."""
    print("\n95. build 314: an unfound secret flare shows no colour anywhere; the found ones' glint is a touch less")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
      store.mysteryColorsFound = { red: true, orange: false, yellow: false, violet: false, white: false, core: false };
      showHome(); await wait(700);
      const dots = [...document.querySelectorAll('.panel.home .cosmic-flare-dot')];
      out.dots = dots.map(d => ({ k: d.dataset.flare, found: d.classList.contains('is-found'), next: d.classList.contains('is-next'),
        fc: getComputedStyle(d).getPropertyValue('--fc').trim().toUpperCase() }));
      out.real = MYSTERY_COLOR; out.tint = (typeof FLARE_UNFOUND_TINT === 'string') ? FLARE_UNFOUND_TINT.toUpperCase() : null;
      /* the Home hint card for a secret whose flare is still missing */
      store.mysteryColorsFound = { red: true, orange: true, yellow: true, violet: false, white: false, core: false };
      const h = flareHintItem('umbra'); out.hintColor = String(h.color).toUpperCase();
      const box = document.createElement('div'); box.append(h.art()); document.body.append(box);
      out.hintFills = [...box.querySelectorAll('.rs-hint-orb [fill]')].map(c => String(c.getAttribute('fill')).toUpperCase()).filter(f => f[0] === '#');
      out.hintStops = [...box.querySelectorAll('.rs-hint-orb stop')].map(s => String(s.getAttribute('stop-color')).toUpperCase());
      box.remove();
      /* the glint's peak */
      let kf = null;
      for(const sh of document.styleSheets){ let rules; try{ rules = sh.cssRules; }catch(e){ continue; }
        const walk = list => { for(const rr of list){ if(rr.type === CSSRule.KEYFRAMES_RULE && rr.name === 'cof-glint') kf = rr; else if(rr.cssRules) walk(rr.cssRules); } };
        walk(rules); }
      if(kf){ let op = 0, sc = 0; for(const k of kf.cssRules){ op = Math.max(op, parseFloat(k.style.opacity) || 0);
        const m = /scale\\(([0-9.]+)\\)/.exec(k.style.transform || ''); if(m) sc = Math.max(sc, parseFloat(m[1])); } out.glint = { op, sc }; }
      }catch(e){ out.threw = String(e); }
      return out; }""")
    real = {k: v.upper() for k, v in (r.get("real") or {}).items()}
    dots = r.get("dots") or []
    found = [d for d in dots if d["found"]]
    unfound = [d for d in dots if not d["found"]]
    check("a found flare is lit in its own colour", found and all(d["fc"] == real.get(d["k"]) for d in found), found)
    check("no unfound flare on Home carries its colour - not even the next one being hunted",
          unfound and any(d["next"] for d in unfound) and all(d["fc"] != real.get(d["k"]) and d["fc"] == r.get("tint") for d in unfound), unfound)
    check("the Home hint card draws the missing flare without its colour",
          r.get("hintColor") != real.get("violet") and real.get("violet") not in (r.get("hintFills") or []) + (r.get("hintStops") or []),
          {k: r.get(k) for k in ("hintColor", "hintFills", "hintStops")})
    g = r.get("glint") or {}
    check("the found flares' glint is a touch less: peak brightness and size .7-.85 of what 313 had (1)",
          0.7 <= g.get("op", 0) <= 0.85 and 0.7 <= g.get("sc", 0) <= 0.85, g)
    ctx.close()


_RANKMAP_SAMPLE = """async (scen) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const u = topicsIn(QUESTIONS); u.slice(0, 4).forEach(n => store.unitPerfects[n] = 999);
  store.rankMapFx244 = true; store.rankMapSeen = TIER_ORDER_FULL.indexOf(rankOf(store));
  store.rankMapProg = scen === 'climb' ? null : { i: TIER_ORDER_FULL.indexOf(rankOf(store)), p: 1 };
  window.scrollTo(0, 0);
  /* every scroll the show makes, as it makes it */
  const calls = []; const o = window.scrollTo.bind(window);
  window.scrollTo = function(a, b){ calls.push(typeof a === 'object' && a ? 'options:' + a.behavior : 'xy'); return arguments.length > 1 ? o(a, b) : o(a); };
  const frames = []; const t0 = performance.now(); let stop = false;
  const rec = () => {
    const tip = document.querySelector('.rankmap-roadtip-dot');
    const fill = document.querySelector('.rankmap-roadfill.is-tipped');
    if(tip && fill){
      const a = tip.getBoundingClientRect(), b = fill.getBoundingClientRect();
      frames.push({ t: performance.now() - t0, op: parseFloat(getComputedStyle(tip).opacity), dotY: a.top + a.height / 2, fillEnd: b.bottom, fillH: b.height, sy: scrollY });
    }
    if(!stop) requestAnimationFrame(rec);
  };
  showRanksScreen('ranks');
  requestAnimationFrame(rec);
  await wait(scen === 'climb' ? 11000 : 8000);
  stop = true;
  window.scrollTo = o;
  return { frames, calls: [...new Set(calls)] };
}"""


def check_b314h_rankmap(br):
    """Build 314, the road map: "there's circle at the end is already there
    when loading, and when it's done showing the progress, it doesn't go
    back to the top of screen like it should. The gold in that progress bar
    doesn't [look] like the gold [of the name in] current rank". On 313 the
    light was lit on an empty road from the first frame, every step of the
    walk was scrollTo({behavior:"instant"}) on a smooth-scrolling page (an
    engine without "instant" falls back to the page's own smooth glide),
    and Gold's road was the raw #F5C21B rather than the name's lifted gold."""
    print("\n96. build 314: the road's light waits for its line, the walk comes back to the top, Gold's road is the name's gold")
    for scen in ("climb", "walk"):
        ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
        r = pg.evaluate(_RANKMAP_SAMPLE, scen)
        fr = r.get("frames") or []
        h0 = fr[0]["fillH"] if fr else 0
        before = [f for f in fr if f["fillH"] <= h0 + 0.5 and f["t"] < 6000]
        lit_early = [round(f["op"], 2) for f in before if f["op"] > 0.1]
        check("%s: the light is not there while its line has not moved (%d frames before the fill set off)" % (scen, len(before)),
              len(before) >= 3 and not lit_early, lit_early[:8])
        last = fr[-1] if fr else {}
        check("%s: once the fill has run, the light is lit and sits at the end of the line" % scen,
              last and last["op"] > 0.9 and abs(last["dotY"] - last["fillEnd"]) <= 3, last)
        sy = [f["sy"] for f in fr]
        check("%s: the walk went down the road and came back to the very top" % scen,
              sy and max(sy) > 100 and sy[-1] == 0, {"max": max(sy) if sy else None, "end": sy[-1] if sy else None})
        check("%s: every scroll of the walk is a plain jump, never the options form an engine may not know" % scen,
              r.get("calls") and all(c == "xy" for c in r["calls"]), r.get("calls"))
        ctx.close()
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      out.rank = """ + _seed_gold_js() + """;
      store.rankMapFx244 = true; store.rankMapSeen = 99; store.rankMapProg = { i: 2, p: 1 };
      theme.reduceMotion = true;
      showRanksScreen('ranks'); await wait(800);
      const name = document.querySelector('.rankhero-name'); out.nameCol = name ? getComputedStyle(name).color : null;
      out.name = name ? name.textContent : null;
      const isGold = v => /^\s*(#F5C21B|color-mix\(in srgb, #F5C21B 70%, #fff\))\s*$/i.test(v);
      const roads = [...document.querySelectorAll('.rankmap-road')].filter(r => isGold(r.style.getPropertyValue('--rank-color')) || isGold(r.style.getPropertyValue('--from-color')));
      out.roads = roads.length;
      out.roadCols = roads.map(r => { const p = document.createElement('i'); p.style.color = isGold(r.style.getPropertyValue('--rank-color')) ? 'var(--rank-color)' : 'var(--from-color)';
        r.appendChild(p); const c = getComputedStyle(p).color; p.remove(); return c; });
      /* No RAW gold anywhere on the road: every gold in a stretch's
         colours, its blend's end and its light is the lifted one (so a
         colour blended from gold - the partly lit stretch - blends from
         the name's gold too). */
      const raw = /#F5C21B(?! 70%, #fff\))/i, props = ['--rank-color', '--from-color', '--end-color'];
      out.rawLeft = [...document.querySelectorAll('.rankmap-road, .rankmap-roadtip')].flatMap(e => props.map(p => e.style.getPropertyValue(p))).filter(v => raw.test(v));
      /* and a blend made after the fact (the shape build 314's road-colour
         work gives the partly lit stretch) goes through the same lift */
      const probe = document.createElement('span');
      probe.style.setProperty('--end-color', 'color-mix(in srgb, #F5C21B 40%, ' + RANK_COLOR.ranger + ')');
      if(typeof liftRoadColors === 'function') liftRoadColors(probe);
      out.blend = probe.style.getPropertyValue('--end-color');
      theme.reduceMotion = false;
      return out; }""")
    check("Gold's road is exactly the gold of the name under Current rank",
          r.get("rank") == "veteran" and r.get("roads", 0) >= 1 and all(c == r.get("nameCol") for c in r.get("roadCols", [])), r)
    check("no raw gold left anywhere on the road (its light and any blend use the name's gold)",
          not r.get("rawLeft") and "70%, #fff)" in (r.get("blend") or ""), {"raw": r.get("rawLeft"), "blend": r.get("blend")})
    ctx.close()


def check_b314h_tabs(br):
    """Build 314: "There's lag again when clicking tabs ... Sometimes the
    screen does not load." On 313 the screen was built only from an
    animation frame (a held frame and it never came), a tap that moved a
    pixel or two went the drag path and was built inside pointerup before
    the highlight moved, the unit list was re-walked from the whole bank on
    every badge count, and the Profile dot's unlock walk ran in the same
    task as every mount."""
    print("\n97. build 314: tab switches - the screen always comes, the tap answers first, nothing heavy in the switch")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      /* 1. frames held back (iOS Low Power Mode, a busy compositor) */
      const orig = window.requestAnimationFrame; let held = 0;
      window.requestAnimationFrame = cb => { held++; return 0; };
      document.getElementById('bottomtab-settings').click();
      await wait(600);
      out.heldFrames = held;
      out.loadedWithoutFrames = !!document.querySelector('#stage .screen-settings');
      window.requestAnimationFrame = orig;
      await wait(400);
      /* 2. the bank's units are worked out once */
      const t0 = performance.now(); for(let i = 0; i < 200; i++) topicsIn(QUESTIONS); out.topics200 = performance.now() - t0;
      out.topicsSame = JSON.stringify(topicsIn(QUESTIONS)) === JSON.stringify((() => { const n = []; QUESTIONS.forEach(q => { const t = (q.topic || '').trim(); if(t && n.indexOf(t) < 0) n.push(t); }); return n; })());
      const a = topicsIn(QUESTIONS); a.push('x'); out.topicsCopy = topicsIn(QUESTIONS).indexOf('x') < 0;
      /* 3. the dot's walk is not in the mount's task */
      let inMount = 0, seen = 0; const o2 = window.unlockedIdsNow;
      window.unlockedIdsNow = function(){ seen++; if(window.__inMount) inMount++; return o2.apply(this, arguments); };
      new MutationObserver(() => { window.__inMount = true; Promise.resolve().then(() => { window.__inMount = false; }); }).observe(document.getElementById('stage'), { childList: true });
      document.getElementById('bottomtab-profile').click(); await wait(2500);
      out.dotInMount = inMount; out.dotLater = seen;
      out.dotState = document.getElementById('bottomtab-profile').classList.contains('has-new') === (rankIsNew() || customizeNewCount() + badgeNewCount() > 0);
      window.unlockedIdsNow = o2;
      return out; }""")
    check("with animation frames held back, a tab tap still loads its screen", r.get("heldFrames", 0) > 0 and r.get("loadedWithoutFrames") is True, r)
    check("the bank's unit list is worked out once (200 asks under 20ms), the same list, and every caller gets its own copy",
          r.get("topics200", 999) < 20 and r.get("topicsSame") and r.get("topicsCopy"), r)
    check("the Profile tab's dot is not worked out in the task that mounts a screen, but is worked out after, correctly",
          r.get("dotInMount") == 0 and r.get("dotLater", 0) >= 1 and r.get("dotState") is True, r)
    # 4. a real finger: down, a 3px wobble, up. The highlight must move before
    #    the new screen is built (the answer-first path), not after it.
    pg.evaluate("""() => { window.__order = []; const st = document.getElementById('stage');
      new MutationObserver(() => __order.push('mount')).observe(st, { childList: true });
      new MutationObserver(ms => ms.forEach(m => { if(m.target.id === 'bottomtab-rewards' && m.target.classList.contains('active')) __order.push('active'); }))
        .observe(document.getElementById('bottomtabs'), { attributes: true, subtree: true, attributeFilter: ['class'] }); }""")
    box = pg.evaluate("() => { const r = document.getElementById('bottomtab-rewards').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    cdp = ctx.new_cdp_session(pg)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": box[0], "y": box[1]}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": box[0] + 3, "y": box[1] + 1}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(900)
    o = pg.evaluate("() => ({ order: __order.slice(0, 4), screen: !!document.querySelector('#stage .screen-rankings') })")
    check("a tap that wobbles 3px is still a tap: the highlight moves first, then the Leaderboard comes",
          o["screen"] and "active" in o["order"] and "mount" in o["order"] and o["order"].index("active") < o["order"].index("mount"), o)
    # 5. a timing budget, every switch, at 4x CPU
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    pg.evaluate("""() => { window.__tap = 0; window.__mounts = []; window.__frames = [];
      document.addEventListener('pointerdown', () => { __tap = performance.now(); }, true);
      new MutationObserver(() => __mounts.push(performance.now())).observe(document.getElementById('stage'), { childList: true });
      (function f(t){ __frames.push(t); requestAnimationFrame(f); })(0); }""")
    tabs = ["home", "profile", "rewards", "settings"]
    times = []; blank = 0
    # three rounds of the twelve switches (build 315): a median of twelve
    # swung 280-350ms run to run on one build here; of thirty-six it holds
    # within a few ms, and 313 (~390) still fails it.
    for a, b in [(a, b) for _ in range(3) for a in tabs for b in tabs]:
        if a == b:
            continue
        for d in (a, b):
            xy = pg.evaluate("d => { const r = document.querySelector('.bottomtab[data-dest=\"' + d + '\"]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }", d)
            pg.evaluate("() => { __mounts.length = 0; __frames.length = 0; }")
            pg.touchscreen.tap(xy[0], xy[1])
            pg.wait_for_timeout(1100)
        m = pg.evaluate("""() => { const m = __mounts.find(x => x >= __tap); const f = m ? __frames.find(x => x > m) : null;
          const st = document.getElementById('stage'); return { paint: f ? f - __tap : 9999, blank: !st.firstElementChild }; }""")
        times.append(m["paint"]); blank += 1 if m["blank"] else 0
    times.sort()
    med = times[len(times) // 2]
    check("every switch between the four tabs paints its screen, median tap-to-paint under 300ms at 4x CPU (313: ~390 warm)",
          blank == 0 and med < 300 and times[-1] < 2000, {"median": round(med), "worst": round(times[-1]), "blank": blank})
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    ctx.close()


def check_b314h_chat(br):
    """Build 314, the chat sheet: "if I click on that stuff, the background
    behind the chat goes dull or dark" and "swipe down functions are laggy".
    On 313 every touch of the sheet's chrome - a plain tap - put it into
    .is-settling (the near-opaque fill that stands in for the glass while
    it moves) for a third of a second, and the first moves of a drag were
    left passive, so the page could take the gesture."""
    print("\n98. build 314: a tap on the chat sheet leaves its glass alone; a pull down is the sheet's alone and closes it")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True)
    pg.evaluate("() => { openChatDock(); }")
    pg.wait_for_timeout(600)
    info = pg.evaluate("""() => { const p = document.querySelector('.chatdock-panel'); const r = p.getBoundingClientRect();
      window.__cls = []; new MutationObserver(() => __cls.push(p.className)).observe(p, { attributes: true, attributeFilter: ['class'] });
      const g = p.querySelector('.chatdock-grip'); const gr = g ? g.getBoundingClientRect() : r;
      return { bf: getComputedStyle(p).backdropFilter, x: gr.left + gr.width / 2, y: gr.top + gr.height / 2, open: chatDockOpen }; }""")
    cdp = ctx.new_cdp_session(pg)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": info["x"], "y": info["y"]}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(60)
    a = pg.evaluate("() => ({ cls: __cls.slice(), bf: getComputedStyle(document.querySelector('.chatdock-panel')).backdropFilter, open: chatDockOpen })")
    check("a tap on the sheet never turns its glass into the dark moving fill",
          info["open"] and a["open"] and not any(("is-settling" in c or "is-dragging" in c) for c in a["cls"]) and a["bf"] == info["bf"] and a["bf"] != "none", a)
    # a real pull down closes it; every move after the first is claimed
    pg.evaluate("""() => { window.__prevented = 0; window.__moves = 0; document.querySelector('.chatdock-panel').addEventListener('touchmove', e => { __moves++; setTimeout(() => { if(e.defaultPrevented) __prevented++; }, 0); }, { passive: true }); }""")
    _swipe(cdp, info["x"], info["y"], 0, 220, steps=10)
    pg.wait_for_timeout(500)
    b = pg.evaluate("() => ({ open: chatDockOpen, moves: __moves, prevented: __prevented })")
    check("a pull down the sheet closes it, and every move of it was the sheet's (none left to the page)",
          b["open"] is False and b["moves"] >= 8 and b["prevented"] == b["moves"], b)
    ctx.close()


def check_b314h_sheet(br):
    """Build 314, the start sheet's swipe-down: on 313 it wrote the sheet's
    transform from every touchmove and kept its 16px backdrop blur the whole
    way down - re-blurred every frame it moved."""
    print("\n99. build 314: a pulled sheet moves once a frame, without its blur, and closes on a pull")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True)
    pg.evaluate("""() => { const s = document.createElement('div'); s.id = 'tsheet'; s.className = 'unitoptions-modal-sheet';
      s.style.cssText = 'position:fixed;left:0;right:0;bottom:0;height:400px;z-index:999;';
      s.innerHTML = '<p style="height:600px">x</p>'; document.body.appendChild(s);
      window.__closed = 0; attachSheetSwipe(s, () => { __closed++; });
      window.__writes = 0; window.__frames = 0; window.__mid = null;
      new MutationObserver(() => __writes++).observe(s, { attributes: true, attributeFilter: ['style'] });
      (function f(){ __frames++; if(__frames < 400) requestAnimationFrame(f); })(); }""")
    mid = pg.evaluate("""async () => { const s = document.getElementById('tsheet');
      const T = y => new Touch({ identifier: 1, target: s, clientX: 200, clientY: y, pageX: 200, pageY: y });
      const ev = (type, y) => s.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: type === 'touchend' ? [] : [T(y)], targetTouches: type === 'touchend' ? [] : [T(y)], changedTouches: [T(y)] }));
      ev('touchstart', 500); __writes = 0;
      for(let i = 1; i <= 24; i++) ev('touchmove', 500 + i * 6);
      await Promise.resolve();
      const sync = __writes;
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
      const out = { cls: s.className, bf: getComputedStyle(s).backdropFilter, tf: s.style.transform, sync, afterFrame: __writes };
      ev('touchend', 644);
      return out; }""")
    pg.wait_for_timeout(500)
    closed = pg.evaluate("() => __closed")
    check("while pulled, the sheet is .is-dragging with no backdrop blur, moved by translate3d",
          "is-dragging" in mid["cls"] and mid["bf"] == "none" and "translate3d" in mid["tf"], mid)
    check("24 moves in one go are written once, on the next frame - not 24 times as they arrive",
          mid["sync"] <= 1 and mid["afterFrame"] <= 3, mid)
    check("pulled past the line, it closes", closed == 1, closed)
    ctx.close()


_LB_FAKE = """async () => {
  store.publicId = 'me0000000001'; store.leaderboardOptIn = true; syncCode = syncCode || 'SYNC-test';
  const chars = ['zeus','ninja','grizzly','ghost','wizard','alien','detective','marksman'];
  window.__rows = Array.from({ length: 18 }, (_, i) => ({ pub: 'p' + String(i).padStart(11, '0'), firstName: 'Cadet ' + String.fromCharCode(65 + i),
    avatarChar: chars[i % chars.length], level: 60 - i * 2, badges: 14 - Math.floor(i / 2), hundos: 300 - i * 9, correct: 5000 - i * 100,
    week: weekKeyNow(), weekPoints: 4000 - i * 150, lastModified: Date.now() }));
  window.__cbs = [];
  const mk = rows => ({ metadata: { fromCache: false }, size: rows.length, empty: !rows.length, forEach: f => rows.forEach(r => f({ id: r.pub, data: () => Object.assign({}, r) })) });
  window.__push = () => __cbs.forEach(cb => cb(mk(__rows)));
  const real = fbDb;
  onSnapshotResilient = (ref, onNext) => ref.onSnapshot(onNext, () => {});
  fbDb = { collection: n => n !== 'leaderboard' ? real.collection(n) : ({ doc: id => real.collection(n).doc(id),
    get: () => Promise.resolve(mk(__rows)),
    onSnapshot: cb => { __cbs.push(cb); setTimeout(() => cb(mk(__rows)), 30); return () => { window.__cbs = __cbs.filter(c => c !== cb); }; } }) };
  leaderboardRows = [];
}"""

_LB_EXPECT = """(key) => {
  const board = RANKING_BOARDS.find(b => b.key === key);
  const val = e => Number(e && e[board.field]) || 0;
  const mine = { pub: publicIdOf(), firstName: store.firstName || 'Anonymous', avatarChar: store.avatarChar, level: levelOf(store), badges: badgeCountOf(store),
    hundos: hundosOf(store), week: weekKeyNow(), weekPoints: weekPointsOf(store), mystery: mysteryColorsFoundCount() };
  const list = __rows.map(r => Object.assign({}, r, { weekPoints: weekPointsOfEntry(r) })).concat([mine]);
  const sorted = list.slice().sort(board.sort || ((a, b) => (val(b) - val(a)) || String(a.firstName || '').localeCompare(String(b.firstName || ''))));
  const want = sorted.map(e => e.firstName);
  const got = [...document.querySelectorAll('.screen-rankings .rank-rows .rank-row:not(.rank-row-head):not(.rank-row-skel) .rank-name')].map(n => n.textContent);
  return { key, ok: JSON.stringify(want) === JSON.stringify(got), want: want.slice(0, 6), got: got.slice(0, 6), n: got.length, N: want.length };
}"""


def check_b314h_board(br):
    """Build 314, the Leaderboard: the header "sitting on top of the person
    in first place", the characters "still slightly shaking", and "ensure
    all the leaderboard stuff is accurate and stays accurate ... clicking
    through the leaderboard tabs". On 313 the header was pulled 3px into
    the first row and carried the rows' glass (a saturated blurred strip),
    and every character's flip-book window wore the board's .94 scale, so
    its frames landed on 30+ different sub-pixel offsets. The accuracy half
    is a guard: rows change under the board while its tabs are switched,
    the screen is left and re-entered, and every board must match the data
    exactly every time."""
    print("\n100. build 314: the Leaderboard - header clear of first place, characters that hold still, boards that stay true")
    for (dn, w, h) in [("phone", 440, 956), ("tablet", 834, 1194), ("SE", 375, 667)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate(_LB_FAKE)
        pg.evaluate("() => showRankings('overall')")
        pg.wait_for_timeout(900)
        r = pg.evaluate("""() => { const h = document.querySelector('.rank-row-head'); const f = document.querySelector('.rank-rows .rank-row.lb-place-1');
          const hr = h.getBoundingClientRect(), fr = f.getBoundingClientRect(); const cs = getComputedStyle(h);
          const lab = [...h.querySelectorAll('.rank-col-head')].map(e => e.getBoundingClientRect().bottom);
          return { gap: Math.round(fr.top - hr.bottom), labGap: Math.round(fr.top - Math.max(...lab)), bf: cs.backdropFilter, bg: cs.backgroundColor }; }""")
        check("%s: the Rank / Level / Badges header keeps its own line, clear of first place and its glow, with no glass strip" % dn,
              r["gap"] >= 8 and r["labGap"] >= 12 and r["bf"] == "none", r)
        ctx.close()
    # characters that hold still: every flip-book frame on the same pixel grid
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=3, has_touch=True, is_mobile=True)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
                        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % USED_ACCOUNT)
    pg = open_page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.evaluate(_LB_FAKE)
    pg.evaluate("() => showRankings('week')")
    t0 = time.time()
    while time.time() - t0 < 150 and pg.evaluate("() => document.querySelectorAll('.screen-rankings .rank-row .char-flip-play img').length") < 3:
        time.sleep(1)
    r = pg.evaluate("""async () => { const dpr = devicePixelRatio; const imgs = [...document.querySelectorAll('.screen-rankings .rank-row .char-flip-play img')].slice(0, 3);
      const phases = imgs.map(() => new Set()); const al = [];
      for(let f = 0; f < 45; f++){ await new Promise(r => requestAnimationFrame(r));
        imgs.forEach((img, i) => { const r = img.getBoundingClientRect(), p = img.parentElement.getBoundingClientRect();
          const fx = (r.left - p.left) * dpr, fy = (r.top - p.top) * dpr; phases[i].add((fx - Math.round(fx)).toFixed(2) + ',' + (fy - Math.round(fy)).toFixed(2)); }); }
      imgs.forEach(img => { const play = img.parentElement, s = play.parentNode.querySelector('svg.avatarchar-svg').getBoundingClientRect(), r = play.getBoundingClientRect();
        al.push({ dx: Math.abs(r.left + r.width / 2 - s.left - s.width / 2), dy: Math.abs(r.top + r.height / 2 - s.top - s.height / 2), dw: Math.abs(r.width - s.width) }); });
      return { n: imgs.length, phases: phases.map(s => s.size), al }; }""")
    check("every leaderboard character's flip-book steps on whole device pixels (one sub-pixel phase over 45 frames, 313: 30+)",
          r["n"] >= 3 and all(p == 1 for p in r["phases"]), r)
    check("...and still sits exactly over its drawing (centre within .5px, size within 1.5px)",
          all(a["dx"] <= 0.5 and a["dy"] <= 0.5 and a["dw"] <= 1.5 for a in r["al"]), r["al"])
    ctx.close()
    # accuracy, under change
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate(_LB_FAKE)
    pg.evaluate("() => showRankings('week')")
    pg.wait_for_timeout(700)
    keys = pg.evaluate("() => RANKING_BOARDS.map(b => b.key)")
    bad = []
    steps = [
        "() => { __rows[7].weekPoints = 99999; __rows[3].level = 80; __rows[3].badges = 20; __rows[10].hundos = 9999; __push(); }",
        "() => { __rows[0].weekPoints = 1; __rows[15].level = 79; __rows[15].badges = 20; __rows.push({ pub: 'pNEW00000000', firstName: 'Cadet New', avatarChar: 'ghost', level: 70, badges: 18, hundos: 50, correct: 1, week: weekKeyNow(), weekPoints: 50000, lastModified: Date.now() }); __push(); }",
        "() => { __rows.splice(2, 1); __rows[5].hundos = 100000; __push(); }",
    ]
    for si, st in enumerate(steps):
        for k in keys:
            pg.evaluate("k => document.querySelectorAll('.screen-rankings .navsegment .iconbtn')[RANKING_BOARDS.findIndex(b => b.key === k)].click()", k)
            pg.wait_for_timeout(60)
            e = pg.evaluate(_LB_EXPECT, k)
            if not e["ok"]:
                bad.append(("before step %d" % si, e))
        pg.evaluate(st)
        pg.wait_for_timeout(60)
        e = pg.evaluate(_LB_EXPECT, pg.evaluate("() => rankingsBoardKey"))
        if not e["ok"]:
            bad.append(("live after step %d" % si, e))
        if si == 1:
            pg.evaluate("() => showHome()"); pg.wait_for_timeout(300)
            pg.evaluate("() => { __rows[1].weekPoints = 77777; }")
            pg.evaluate("() => showRankings()"); pg.wait_for_timeout(500)
            e = pg.evaluate(_LB_EXPECT, pg.evaluate("() => rankingsBoardKey"))
            if not e["ok"]:
                bad.append(("re-entered", e))
    check("every board matches the data exactly, through live changes, tab switches and a re-entry (%d boards x %d steps)" % (len(keys), len(steps)),
          not bad, bad[:3])
    ctx.close()


def check_b314h_settings_calendar(br):
    """Build 314: Advanced settings "should open more smooth and like it's
    actually expanding open, and when shutting it would actually close shut
    but nicely and smoothly" (313 opened as a fade and closed in one frame),
    and the calendar's today box "still looks shiny ... maybe it shouldn't
    be themed color" (313: the theme's gradient and a glow)."""
    print("\n101. build 314: Advanced settings sweeps open and shut; today in the calendar is calm and neutral")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      showAppearance(); await wait(500);
      const tog = [...document.querySelectorAll('.more-toggle')].find(b => /Advanced settings/.test(b.textContent));
      const body = tog.nextElementSibling, inner = body.querySelector('.more-body-inner');
      const sample = async ms => { const s = []; const t0 = performance.now();
        while(performance.now() - t0 < ms){ await new Promise(r => requestAnimationFrame(r)); s.push({ t: Math.round(performance.now() - t0), h: Math.round(body.getBoundingClientRect().height), clip: getComputedStyle(inner).clipPath }); } return s; };
      tog.click(); out.open = await sample(700);
      tog.click(); out.close = await sample(800);
      out.closedAfter = !body.classList.contains('open');
      /* the calendar, on a coloured theme */
      theme.accent = 'adept'; applyTheme(); showCalendar(); await wait(400);
      const t = document.querySelector('.cal-grid .cal-cell-today'); const c = getComputedStyle(t);
      out.today = { sel: t.classList.contains('cal-cell-sel'), bgImg: c.backgroundImage, shadow: c.boxShadow, border: c.borderTopColor, bg: c.backgroundColor };
      return out; }""")
    op = r["open"]; cl = r["close"]
    mid_open = [s for s in op if s["clip"] not in (op[-1]["clip"], op[0]["clip"])]
    check("opening sweeps the clip open over several frames, at its full height from the first",
          len(mid_open) >= 3 and op[0]["h"] > 40, {"frames": len(op), "between": len(mid_open), "h0": op[0]["h"]})
    held = [s for s in cl if s["h"] > 40 and s["t"] >= 150]
    check("closing is not instant: it keeps its height for 150ms+ while the clip sweeps shut, then gives it back",
          len(held) >= 3 and cl[-1]["h"] < 5 and r["closedAfter"], {"held": len(held), "end": cl[-1]})
    t = r["today"]
    import re as _re
    nums = [int(x) for x in _re.findall(r"\d+", t["border"])[:3]]
    check("today is matte and neutral: no gradient, no glow, a neutral rim (theme set to a colour)",
          t["bgImg"] == "none" and t["shadow"] == "none" and len(nums) == 3 and max(nums) - min(nums) <= 6, t)
    ctx.close()


def check_b314h_host(br):
    """Build 314: "When hosting a room, you click host, it says something
    there but then it opens the lobby so fast ... something about opening a
    lobby is not smooth." On 313 a quick server put the lobby up 120ms after
    the tap, and the lobby cut in and then grew its roster a frame later."""
    print("\n102. build 314: Host a room - the card's words are up long enough to read, the lobby arrives once, softly")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => {
      const wait = ms => new Promise(r => setTimeout(r, ms));
      let docData = null; const subs = []; const real = fbDb;
      onSnapshotResilient = (ref, onNext) => ref.onSnapshot(onNext, () => {});
      const docRef = id => ({ id, set: d => { docData = Object.assign({}, d); setTimeout(() => subs.forEach(cb => cb({ exists: true, id, data: () => docData, metadata: { fromCache: false } })), 40); return new Promise(r => setTimeout(r, 60)); },
        update: () => Promise.resolve(), get: () => Promise.resolve({ exists: !!docData, data: () => docData }), delete: () => Promise.resolve(),
        onSnapshot: cb => { subs.push(cb); if(docData) setTimeout(() => cb({ exists: true, id, data: () => docData, metadata: { fromCache: false } }), 20); return () => {}; }, collection: () => ({ doc: docRef }) });
      fbDb = { collection: n => n === 'vrooms' ? ({ doc: docRef, where: function(){ return this; }, onSnapshot: cb => { setTimeout(() => cb({ forEach(){}, docs: [] }), 20); return () => {}; } }) : real.collection(n) };
      showVirtualRoomChoice(); await wait(500);
      const btn = [...document.querySelectorAll('button')].find(b => /Host a room/.test(b.textContent));
      const t0 = performance.now(); let lobbyAt = null, firstOp = null; const ops = [];
      btn.click();
      while(performance.now() - t0 < 2500){ await new Promise(r => requestAnimationFrame(r));
        const p = document.querySelector('#stage > .screen-vroom-lobby');
        if(p){ if(lobbyAt == null){ lobbyAt = performance.now() - t0; firstOp = parseFloat(getComputedStyle(p).opacity); }
          ops.push(parseFloat(getComputedStyle(p).opacity)); } }
      return { lobbyAt, firstOp, rose: ops.filter(o => o > .05 && o < .95).length, end: ops[ops.length - 1] }; }""")
    check("'Setting up your room...' stays up 800ms+ even when the server answers at once (313: ~120ms)",
          r["lobbyAt"] is not None and r["lobbyAt"] >= 800 and r["lobbyAt"] < 1800, r)
    check("the lobby comes in as one soft rise (it is not simply cut in), and finishes fully shown",
          r["firstOp"] is not None and r["firstOp"] < 0.1 and r["rose"] >= 1 and r["end"] == 1, r)
    ctx.close()


_HOME_POSE = """() => { const p = document.querySelector('.panel.home.screen-home-actual'); if(!p) return null;
  const ang = el => { if(!el) return null; const m = new DOMMatrix(getComputedStyle(el).transform === 'none' ? undefined : getComputedStyle(el).transform); return Math.atan2(m.b, m.a) * 180 / Math.PI; };
  const pts = [...p.querySelectorAll('.cosmic-badge-rank, .cosmic-flare-dot')].map(e => { const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; });
  /* the wall-clock moment the styles describe: an animation's computed
     state is for the document timeline's time, which lags the wall clock
     while the page is busy - so t is read off the timeline, not Date.now() */
  const lag = (document.timeline && typeof document.timeline.currentTime === 'number') ? Math.max(0, performance.now() - document.timeline.currentTime) : 0;
  return { t: Date.now() - lag, outer: ang(p.querySelector('.cosmic-hero-orbitlayer:not(.cosmic-hero-orbitlayer-inner)')), inner: ang(p.querySelector('.cosmic-hero-orbitlayer-inner')),
           pts, node: p.dataset.hid || (p.dataset.hid = String(Math.random())) }; }"""


def check_b314h_home_clock(br):
    """Build 314: "when hitting the main menu or reloading the home button
    or whatever, the plant system like reloads and stuff changes positions".
    On 313 every Home was a new set of CSS loops starting at 0%: the rings
    snapped back to their starting angle and the bubbles jumped, on every
    return and on Main menu from Home itself."""
    print("\n103. build 314: Home's planet system carries on where it was - one clock for every loop")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.wait_for_timeout(1500)
    # 1. rebuilt in place (Main menu while on Home): no jump between the last
    #    frame of the old system and the first of the new
    # The old system is put exactly where the shared clock says (as every
    # Home is put at its mount: the wall clock, read on the document
    # timeline - an animation's time only moves when a frame is made, so a
    # busy task sees the timeline behind the wall clock, and that lag is
    # taken off). Both settings are made in ONE task, where that value is
    # the same whenever it is read, so the rebuilt system must land on the
    # same pose to within a pixel. Comparing against "a frame's motion"
    # was a noisy proxy - a bobbing bubble near the top of its bob barely
    # moves in a frame - and failed a good build on a loaded machine. On
    # dd6cfae every loop starts again at 0%: 60px and more.
    r = pg.evaluate("""async (POSE) => { const pose = eval(POSE); const out = {};
      const EPOCH = Date.UTC(2026, 0, 1);
      const clock = () => Date.now() - EPOCH - Math.max(0, performance.now() - document.timeline.currentTime);
      const onClock = root => { const t = clock(); root.getAnimations({ subtree: true }).forEach(a => { try{ const g = a.effect && a.effect.getTiming();
        if(g && g.iterations === Infinity && Number(g.duration) > 0) a.currentTime = t; }catch(e){} }); };
      onClock(document.querySelector('.panel.home.screen-home-actual'));
      const b = pose();
      showHome();
      const c = pose();
      await new Promise(r => requestAnimationFrame(r)); const d = pose();
      const jump = (x, y) => Math.max(...x.pts.map((p, i) => y.pts[i] ? Math.hypot(p[0] - y.pts[i][0], p[1] - y.pts[i][1]) : 0));
      out.rebuildMove = +jump(b, c).toFixed(2); out.nextFrame = +jump(c, d).toFixed(2); out.n = b.pts.length; out.same = c.pts.length === b.pts.length;
      return out; }""", _HOME_POSE)
    check("Home rebuilt in place at the same moment lands on the same pose - no orbiting piece moves more than a pixel (%d pieces)" % r.get("n", 0),
          r.get("n", 0) >= 7 and r.get("same") and r["rebuildMove"] <= 1.0, r)
    # 2. away and back: each ring is at the angle it would have reached
    a = pg.evaluate(_HOME_POSE)
    pg.evaluate("() => showProfile('profile')")
    pg.wait_for_timeout(2500)
    pg.evaluate("() => document.getElementById('bottomtab-home').click()")
    pg.wait_for_timeout(400)
    b = pg.evaluate(_HOME_POSE)
    el = (b["t"] - a["t"]) / 1000.0
    def want(ang0, period):
        return (ang0 + 360.0 * el / period)
    def diff(x, y):
        d = (x - y) % 360
        return min(d, 360 - d)
    dout = diff(b["outer"], want(a["outer"], 120)) if a.get("outer") is not None else 99
    din = diff(b["inner"], want(a["inner"], 52)) if a.get("inner") is not None else 99
    check("back from another tab, both rings are where they would have turned to (within 1.5 degrees)",
          dout <= 1.5 and din <= 1.5, {"outer": round(dout, 2), "inner": round(din, 2), "elapsed": round(el, 2)})
    # 3. tapping Home while on Home does not rebuild it
    n0 = pg.evaluate("() => document.querySelector('.panel.home').dataset.hid")
    pg.evaluate("() => document.getElementById('bottomtab-home').click()")
    pg.wait_for_timeout(500)
    n1 = pg.evaluate("() => { const p = document.querySelector('.panel.home'); return p && p.dataset.hid; }")
    check("tapping Home while on Home leaves the same system on screen, not a new one", n0 is not None and n0 == n1, (n0, n1))
    # 4. a reload carries on too
    a = pg.evaluate(_HOME_POSE)
    pg.reload(); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.wait_for_timeout(300)
    b = pg.evaluate(_HOME_POSE)
    if b:
        el = (b["t"] - a["t"]) / 1000.0
        dout = diff(b["outer"], a["outer"] + 360.0 * el / 120)
        check("after a reload the outer ring is where it would have turned to (within 1.5 degrees)", dout <= 1.5, {"outer": round(dout, 2), "elapsed": round(el, 2)})
    else:
        check("after a reload Home is up", False, None)
    ctx.close()


def check_b314h_lead2(br):
    """Build 314, second list: the Leaderboard opens on Overall "anytime you
    open leaderboard"; the class card counts the tests left (finals and the
    state test with them); July 8th is the State test and the Last day, with
    a box of its own in both calendar views; Month/List swipes like the
    Leaderboard's boards. On dd6cfae the board reopened on the last one
    viewed, there was no test count, July 8th had no state test and no
    card of its own, and the calendar's switch did not swipe."""
    print("\n104. build 314: Overall by default, tests left, the State test on the last day, a calendar that swipes")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      showRankings('week'); await wait(300); showHome(); await wait(300);
      document.getElementById('bottomtab-rewards').click(); await wait(700);
      const act = document.querySelector('.screen-rankings .navsegment .iconbtn.active');
      out.opened = act ? act.textContent : null; out.key = rankingsBoardKey;
      const sl = document.querySelector('.screen-rankings .navsegment .seg-slider');
      out.sliderOn = !!(sl && act && Math.abs(sl.getBoundingClientRect().left - act.getBoundingClientRect().left) < 2);
      /* the class card */
      showProfile('profile'); await wait(500);
      const pills = [...document.querySelectorAll('.profile-classcard:not(.profile-friendcard) .profile-classcard-count')].map(e => e.textContent);
      out.pills = pills;
      out.testsLeft = typeof testsRemaining === 'function' ? testsRemaining() : null;
      out.exams = typeof isExamDay === 'function' ? CALENDAR_DATA.filter(isExamDay).map(e => e.date) : [];
      const j8 = CALENDAR_DATA.find(e => e.date === '2027-07-08'); out.j8 = j8 ? j8.text : null;
      return out; }""")
    check("the Leaderboard opens on Overall from the tab bar, whichever board was looked at last, and its bubble sits under Overall",
          r.get("key") == "overall" and r.get("opened") == "Overall" and r.get("sliderOn"), r)
    ex = r.get("exams") or []
    check("tests left counts every numbered test, the three level finals and the state test (not PT finals)",
          isinstance(r.get("testsLeft"), int) and "2027-07-08" in ex and "2027-01-19" in ex and "2027-06-10" in ex and "2027-06-21" in ex
          and "2027-01-11" not in ex and "2027-06-09" not in ex and len(ex) >= 16, {"n": len(ex), "testsLeft": r.get("testsLeft")})
    check("the class card shows tests left beside class days left",
          any("class day" in p for p in r.get("pills") or []) and any(p.endswith("test left") or p.endswith("tests left") for p in r.get("pills") or []), r.get("pills"))
    check("July 8th is the State test and says Last day", r.get("j8") and "State Test" in r["j8"] and "Last Day" in r["j8"], r.get("j8"))
    # the last day, both views
    r2 = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      showCalendar(); await wait(400);
      for(let i = 0; i < 20 && !document.querySelector('.cal-cell[data-date="2027-07-08"]'); i++){ const n = document.querySelectorAll('.cal-grid-arrow')[1]; if(!n || n.disabled) break; n.click(); await wait(60); }
      const cell = document.querySelector('.cal-cell[data-date="2027-07-08"]');
      out.cell = cell ? { last: cell.classList.contains('cal-cell-last'), star: getComputedStyle(cell, '::after').content !== 'none', border: getComputedStyle(cell).borderTopColor } : null;
      if(cell){ cell.click(); await wait(200); }
      const card = document.querySelector('.cal-daycard');
      out.card = card ? { cls: card.className, crest: !!card.querySelector('.cal-last-crest svg'), text: card.textContent } : null;
      return out; }""")
    c = r2.get("cell") or {}
    check("the month view's July 8th is the last day, in academy gold with a star", c.get("last") and c.get("star") and "229" in (c.get("border") or ""), c)
    cd = r2.get("card") or {}
    check("tapping it opens the commendation card: a crest, Last day, State test",
          "cal-daycard-last" in (cd.get("cls") or "") and cd.get("crest") and "Last day" in (cd.get("text") or "") and "State test" in (cd.get("text") or ""), cd)
    # swipe between Month and List, with a real finger
    cdp = ctx.new_cdp_session(pg)
    pg.evaluate("() => { window.scrollTo(0, 0); }")
    before = pg.evaluate("() => document.querySelector('.screen-calendar .navsegment .iconbtn.active').textContent")
    _swipe(cdp, 330, 600, -220, 0, steps=8)
    pg.wait_for_timeout(500)
    after = pg.evaluate("() => ({ act: document.querySelector('.screen-calendar .navsegment .iconbtn.active').textContent, list: !document.querySelector('.cal-listview').hidden })")
    _swipe(cdp, 110, 600, 220, 0, steps=8)
    pg.wait_for_timeout(500)
    back = pg.evaluate("() => document.querySelector('.screen-calendar .navsegment .iconbtn.active').textContent")
    check("a swipe left goes Month to List, and right comes back", before == "Month" and after["act"] == "List" and after["list"] and back == "Month",
          (before, after, back))
    # the list view's row for the last day
    r3 = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      document.querySelectorAll('.screen-calendar .navsegment .iconbtn')[1].click(); await wait(200);
      const s = document.querySelector('.cal-listview .searchbox'); s.value = 'State Test'; s.dispatchEvent(new Event('input', { bubbles: true })); await wait(200);
      const row = document.querySelector('.cal-row[data-date="2027-07-08"]');
      return row ? { last: row.classList.contains('cal-row-last'), chips: [...row.querySelectorAll('.cal-row-chip')].map(c => c.textContent) } : null; }""")
    check("the list view's July 8th row is gold-rimmed and says LAST DAY and STATE TEST",
          r3 and r3["last"] and "LAST DAY" in r3["chips"] and "STATE TEST" in r3["chips"], r3)
    # THE DAYS "TESTS LEFT" COUNTS ARE THE DAYS MARKED AS TESTS: the finals
    # and the state test are tests in the count, so they are test days on
    # the grid (the amber dot) and in the list (a chip) as well. On the
    # first pass the count took them in and the calendar did not mark them.
    r4 = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const s = document.querySelector('.cal-listview .searchbox'); s.value = ''; s.dispatchEvent(new Event('input', { bubbles: true })); await wait(250);
      const want = CALENDAR_DATA.filter(isExamDay).map(e => e.date).sort();
      const rows = [...document.querySelectorAll('.cal-listview .cal-row.cal-row-test')];
      out.listMissing = want.filter(d => !rows.some(r => r.dataset.date === d));
      out.listExtra = rows.map(r => r.dataset.date).filter(d => want.indexOf(d) < 0);
      out.unchipped = rows.filter(r => !r.querySelector('.cal-row-chip-test')).map(r => r.dataset.date);
      const fin = document.querySelector('.cal-row[data-date="2027-01-19"]');
      out.finalChips = fin ? [...fin.querySelectorAll('.cal-row-chip')].map(c => c.textContent) : null;
      document.querySelectorAll('.screen-calendar .navsegment .iconbtn')[0].click(); await wait(250);
      for(let i = 0; i < 20 && !document.querySelector('.cal-cell[data-date="2027-01-19"]'); i++){ const b = document.querySelectorAll('.cal-grid-arrow')[0]; if(!b || b.disabled) break; b.click(); await wait(60); }
      const jan = document.querySelector('.cal-cell[data-date="2027-01-19"]');
      out.gridFinal = jan ? !!jan.querySelector('.cal-cell-dot-test') : null;
      return out; }""")
    check("every day 'tests left' counts is marked as a test in the list and on the grid - the finals (FINAL) and the State test too",
          r4 and not r4["listMissing"] and not r4["listExtra"] and not r4["unchipped"] and r4["finalChips"] and "FINAL" in r4["finalChips"] and r4["gridFinal"] is True, r4)
    ctx.close()


_KB_STUB = """(() => { const t = new EventTarget(); let h = null, off = 0;
  const st = { get width(){ return innerWidth; }, get height(){ return h == null ? innerHeight : h; }, get offsetTop(){ return off; },
    get offsetLeft(){ return 0; }, get pageTop(){ return scrollY + off; }, get pageLeft(){ return 0; }, get scale(){ return 1; },
    addEventListener: t.addEventListener.bind(t), removeEventListener: t.removeEventListener.bind(t), dispatchEvent: t.dispatchEvent.bind(t), onresize: null, onscroll: null };
  Object.defineProperty(window, 'visualViewport', { get: () => st, configurable: true });
  window.__kb = (px) => { h = px ? innerHeight - px : null; t.dispatchEvent(new Event('resize')); };
})();"""


def check_b314h_chat2(br):
    """Build 314, chat: the sheet "cuts off" above the keyboard, and an
    offline member's yellow character "looks like one of the rank unlock
    characters". On dd6cfae the sheet stayed pinned to the layout
    viewport's bottom, behind the keyboard, and away members were
    grayscale(1)."""
    print("\n105. build 314: the chat sits flush on the keyboard; an offline member keeps their colours")
    for (dn, w, h, kb) in [("iPhone 17 Pro Max", 440, 956, 336), ('iPad Pro 11"', 834, 1194, 400)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=_KB_STUB)
        pg.evaluate("() => openChatDock()")
        # measured once the sheet / popover has finished arriving
        base = pg.evaluate("""async () => { const p = document.querySelector('.chatdock-panel'); let last = null, same = 0;
          for(let i = 0; i < 60 && (same < 4 || p.getAnimations().some(a => a.playState === 'running')); i++){ await new Promise(r => setTimeout(r, 60)); const r = p.getBoundingClientRect();
            const k = r.top.toFixed(1) + '|' + r.bottom.toFixed(1); same = k === last ? same + 1 : 0; last = k; }
          const r = p.getBoundingClientRect(); return { bottom: r.bottom, top: r.top, pb: getComputedStyle(p).paddingBottom }; }""")
        pg.evaluate("k => __kb(k)", kb)
        pg.evaluate("""async () => { const p = document.querySelector('.chatdock-panel'); let last = null, same = 0;
          for(let i = 0; i < 60 && (same < 4 || p.getAnimations().some(a => a.playState === 'running')); i++){ await new Promise(r => setTimeout(r, 60)); const r = p.getBoundingClientRect();
            const k = r.top.toFixed(1) + '|' + r.bottom.toFixed(1); same = k === last ? same + 1 : 0; last = k; } }""")
        up = pg.evaluate("() => { const p = document.querySelector('.chatdock-panel'); const r = p.getBoundingClientRect(); return { bottom: r.bottom, top: r.top, kbTop: visualViewport.offsetTop + visualViewport.height }; }")
        if "--against" not in sys.argv and os.path.isdir("/tmp/claude-0/b314/home"):
            pg.screenshot(path="/tmp/claude-0/b314/home/chat-keyboard-%s.png" % ("iphone" if w < 600 else "ipad"))
        pg.evaluate("() => __kb(0)")
        pg.evaluate("""async () => { const p = document.querySelector('.chatdock-panel'); let last = null, same = 0;
          for(let i = 0; i < 60 && (same < 4 || p.getAnimations().some(a => a.playState === 'running')); i++){ await new Promise(r => setTimeout(r, 60)); const r = p.getBoundingClientRect();
            const k = r.top.toFixed(1) + '|' + r.bottom.toFixed(1); same = k === last ? same + 1 : 0; last = k; } }""")
        down = pg.evaluate("() => { const p = document.querySelector('.chatdock-panel'); const r = p.getBoundingClientRect(); return { bottom: r.bottom, top: r.top, kb: p.classList.contains('is-kb'), pb: getComputedStyle(p).paddingBottom }; }")
        check("%s: with the keyboard up the chat's bottom sits on the keyboard's top (within 1px) and its top is on screen" % dn,
              abs(up["bottom"] - up["kbTop"]) <= 1 and up["top"] >= 0, {"up": up, "kb": kb})
        check("%s: and with it down again the chat is exactly where it was" % dn,
              abs(down["bottom"] - base["bottom"]) <= 1 and abs(down["top"] - base["top"]) <= 1 and not down["kb"] and down["pb"] == base["pb"], {"base": base, "down": down})
        ctx.close()
    # THE EXACT STATE MADISON SENT (build 314): a room open, the field
    # tapped and focused, the keyboard up. The glass behind the messages
    # must stay the glass - never the dark moving fill, never dimmed -
    # from the tap through the keyboard arriving. On dd6cfae the tap on
    # the field put the sheet in .is-settling.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=_KB_STUB, touch=True)
    pg.evaluate("() => { openChatDock(); enterChatRoom('GTEST1'); }")
    pg.wait_for_timeout(900)
    st = pg.evaluate("""() => { const p = document.querySelector('.chatdock-panel'); const i = p.querySelector('.vroom-chat-input');
      window.__glass = []; const look = () => { const cs = getComputedStyle(p); __glass.push([p.className, cs.backdropFilter, cs.backgroundColor]); };
      new MutationObserver(look).observe(p, { attributes: true, attributeFilter: ['class'] });
      const iv = setInterval(look, 16); setTimeout(() => clearInterval(iv), 2500);
      const r = i ? i.getBoundingClientRect() : null; const cs = getComputedStyle(p);
      /* and a spot of the sheet that is not a control: the room's count line */
      const c = p.querySelector('.chatdock-roomcount'); const cr = c ? c.getBoundingClientRect() : null;
      return { rest: [cs.backdropFilter, cs.backgroundColor], at: r && { x: r.left + r.width / 2, y: r.top + r.height / 2 },
               bare: cr && { x: cr.left + Math.min(30, cr.width / 2), y: cr.top + cr.height / 2 } }; }""")
    if st["at"]:
        cdp = ctx.new_cdp_session(pg)
        for pt in (st["bare"], st["at"]):
            if not pt: continue
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": pt["x"], "y": pt["y"]}]})
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            pg.wait_for_timeout(120)
        pg.evaluate("() => document.querySelector('.chatdock-panel .vroom-chat-input').focus()")
        pg.wait_for_timeout(80)
        pg.evaluate("() => __kb(336)")
        pg.wait_for_timeout(700)
    g = pg.evaluate("() => ({ seen: __glass, focused: document.activeElement && document.activeElement.className, kb: document.querySelector('.chatdock-panel').classList.contains('is-kb') })")
    bad = [x for x in g["seen"] if "is-settling" in x[0] or "is-dragging" in x[0] or x[1] != st["rest"][0] or x[2] != st["rest"][1]]
    check("tapping the field and typing with the keyboard up never dims or flattens the glass behind the chat",
          bool(st["at"]) and bool(st["bare"]) and g["focused"] == "vroom-chat-input" and g["kb"] and len(g["seen"]) > 20 and not bad,
          {"rest": st["rest"], "bad": bad[:3], "n": len(g["seen"]), "focused": g["focused"], "kb": g["kb"]})
    ctx.close()
    # an offline member keeps their hue
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
                        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % USED_ACCOUNT)
    pg = open_page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.evaluate("""() => { const host = document.createElement('div'); host.id = 'awaytest'; host.className = 'chatdock-roomhead';
      host.style.cssText = 'position:fixed;left:20px;top:200px;z-index:9999;display:flex;gap:30px;background:#141a22;padding:20px';
      /* "-here" is the same offline chip with the art's own treatment
         taken off, so the two differ by exactly what offline does to the
         drawing (the status dot and the name are not in the picture) */
      ['paladin', 'alien'].forEach(c => [false, true].forEach(away => {
        const one = document.createElement('span'); one.className = 'chatdock-who is-away'; one.dataset.k = c + (away ? '-away' : '-here');
        const art = document.createElement('span'); art.className = 'chatdock-who-art'; art.appendChild(buildAvatarCharSVGSafe(c));
        if(!away) art.style.cssText = 'filter:none !important; opacity:1 !important;';
        const nm = document.createElement('span'); nm.className = 'chatdock-who-name'; nm.textContent = 'X';
        one.append(art, nm); host.appendChild(one); }));
      document.body.appendChild(host); }""")
    pg.wait_for_timeout(500)
    import colorsys, io as _io, math
    from PIL import Image
    pg.evaluate("() => document.getAnimations().forEach(a => { try{ a.pause(); a.currentTime = 0; }catch(e){} })")
    pg.wait_for_timeout(200)
    def img(sel):
        el = pg.query_selector('#awaytest [data-k="%s"] .chatdock-who-art' % sel)
        return Image.open(_io.BytesIO(el.screenshot())).convert("RGB")
    res = {}
    def pop(im):
        hs = []; ss = []
        for px in im.getdata():
            hh, sv, vv = colorsys.rgb_to_hsv(*(v / 255.0 for v in px))
            if sv >= 0.3 and vv >= 0.25:
                hs.append(hh * 2 * math.pi); ss.append(sv)
        if not hs:
            return None
        x = sum(math.cos(h) for h in hs) / len(hs); y = sum(math.sin(h) for h in hs) / len(hs)
        return {"n": len(hs), "hue": math.degrees(math.atan2(y, x)) % 360, "sat": sum(ss) / len(ss)}
    for c in ("paladin", "alien"):
        a_, b_ = pop(img(c + "-here")), pop(img(c + "-away"))
        if not a_ or not b_:
            res[c] = {"px": 0, "hueShift": None, "satKept": None}; continue
        d = abs(a_["hue"] - b_["hue"]) % 360
        res[c] = {"px": min(a_["n"], b_["n"]), "hueShift": round(min(d, 360 - d), 1), "satKept": round(b_["sat"] / a_["sat"], 2)}
    filt = pg.evaluate("() => [...document.querySelectorAll('#awaytest .is-away, #awaytest .is-away *')].map(e => getComputedStyle(e).filter).filter(f => /grayscale|saturate|sepia/.test(f || ''))")
    ok = all(v["px"] > 50 and v["hueShift"] is not None and v["hueShift"] <= 8 and v["satKept"] >= 0.75 for v in res.values())
    check("an offline member's character keeps its own hue and most of its colour (no grayscale or desaturate)",
          ok and not filt, {"res": res, "filters": filt[:3]})
    ctx.close()


_ROOM_FAKE = """(() => {
  window.__rooms = {}; window.__subs = {}; window.__delay = 1500;
  const snap = (id, fromCache) => ({ exists: !!__rooms[id], id, data: () => __rooms[id] && JSON.parse(JSON.stringify(__rooms[id])), metadata: { fromCache: !!fromCache } });
  const deliver = id => (__subs[id] || []).forEach(cb => cb(snap(id, false)));
  const setPath = (obj, path, v) => { const ks = path.split('.'); let o = obj; for(let i = 0; i < ks.length - 1; i++){ o[ks[i]] = o[ks[i]] || {}; o = o[ks[i]]; } o[ks[ks.length - 1]] = v; };
  window.__docRef = id => ({ id,
    set: d => { __rooms[id] = JSON.parse(JSON.stringify(d)); setTimeout(() => deliver(id), 40); return new Promise(r => setTimeout(r, 60)); },
    update: u => { if(__rooms[id]) Object.keys(u).forEach(k => { const v = u[k]; if(v && v._delete) { const ks = k.split('.'); let o = __rooms[id]; for(let i = 0; i < ks.length - 1; i++) o = o[ks[i]] || {}; delete o[ks[ks.length - 1]]; } else setPath(__rooms[id], k, v); }); setTimeout(() => deliver(id), 40); return Promise.resolve(); },
    get: () => Promise.resolve(snap(id, false)), delete: () => { delete __rooms[id]; return Promise.resolve(); },
    onSnapshot: cb => { (__subs[id] = __subs[id] || []).push(cb); setTimeout(() => cb(snap(id, false)), __delay); return () => { __subs[id] = (__subs[id] || []).filter(c => c !== cb); }; },
    collection: () => ({ doc: __docRef, onSnapshot: cb => { setTimeout(() => cb({ forEach(){}, docs: [], docChanges: () => [] }), 20); return () => {}; }, orderBy(){ return this; }, limit(){ return this; }, where(){ return this; }, get: () => Promise.resolve({ forEach(){}, docs: [] }) }) });
  window.__useRooms = () => { const real = fbDb; onSnapshotResilient = (ref, onNext) => ref.onSnapshot(onNext, () => {});
    fbDb = { collection: n => n === 'vrooms' ? ({ doc: __docRef, where: function(){ return this; }, onSnapshot: cb => { setTimeout(() => cb({ forEach(){}, docs: [] }), 20); return () => {}; } }) : real.collection(n) }; };
})();"""

_LOBBY_WATCH = """() => { window.__rowsSeen = []; let stop = false; window.__stopWatch = () => { stop = true; };
  (function f(){ const p = document.querySelector('#stage > .screen-vroom-lobby'); if(p){ __rowsSeen.push(p.querySelectorAll('.vroom-roster-list .vroom-row').length); } if(!stop) requestAnimationFrame(f); })(); }"""


def check_b314h_lobby(br):
    """Build 314: "sometimes the lobby doesn't load who's in it the second
    I'm [in] the lobby". On dd6cfae the roster was drawn only by the room's
    live listener, so with its first answer 1.5s late the lobby showed an
    empty "In this room" for 1.5s - for the host, a joiner and a rejoin."""
    print("\n106. build 314: the lobby shows who is in it from its first frame, even with the room's first answer 1.5s late")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=_ROOM_FAKE)
    pg.evaluate("() => __useRooms()")
    # host
    pg.evaluate("() => showVirtualRoomChoice()"); pg.wait_for_timeout(500)
    pg.evaluate(_LOBBY_WATCH)
    pg.evaluate("() => [...document.querySelectorAll('button')].find(b => /Host a room/.test(b.textContent)).click()")
    pg.wait_for_timeout(3200)
    host = pg.evaluate("() => { __stopWatch(); return __rowsSeen.slice(); }")
    check("host: the lobby's first frame already has you in it, and the roster is never empty",
          host and host[0] >= 1 and min(host) >= 1, {"frames": len(host), "first": host[:3], "min": min(host) if host else None})
    # joiner: a room with two people in it, read to join
    pg.evaluate("() => { try{ leaveVirtualRoom(); }catch(e){} }"); pg.wait_for_timeout(400)
    pg.evaluate("""() => { __rooms['ROOMJ1'] = { hostCode: 'pHOST0000001', hostName: 'Avery', units: [], versions: {}, game: null, open: true, status: 'waiting', mode: 'exam', createdAt: Date.now(),
        participants: { pHOST0000001: { name: 'Avery', avatarChar: 'zeus', level: 40, badges: 6, joinedAt: Date.now() - 9000, seen: Date.now(), ready: false },
                        pTWO00000002: { name: 'Jordan', avatarChar: 'alien', level: 30, badges: 4, joinedAt: Date.now() - 5000, seen: Date.now(), ready: true } } }; }""")
    for label in ("joiner", "rejoin"):
        pg.evaluate("() => showHome()"); pg.wait_for_timeout(300)
        pg.evaluate(_LOBBY_WATCH)
        pg.evaluate("() => joinVirtualRoomLobby('ROOMJ1')")
        pg.wait_for_timeout(2800)
        seen = pg.evaluate("() => { __stopWatch(); return __rowsSeen.slice(); }")
        check("%s: the lobby's first frame shows all three (the two already there and you), and never fewer" % label,
              seen and seen[0] == 3 and min(seen) == 3, {"frames": len(seen), "first": seen[:3], "min": min(seen) if seen else None})
        pg.evaluate("() => { try{ leaveVirtualRoom(); }catch(e){} try{ delete __rooms['ROOMJ1'].participants[publicIdOf()]; }catch(e){} }"); pg.wait_for_timeout(500)
    ctx.close()


def check_b310(br):
    """Build 310. Each of these was written against build 309 and fails
    there: the streak pop was one colour and 1.9s, the Profile tab went
    dark on Friends/Customize/Calendar/Test review, the top tab switchers
    jumped, a leaderboard snapshot rebuilt every character (the shake),
    leaving the app turned the online dot grey at once and an expired dot
    never went grey on screen, the tiny flares were 7.5 glows, Platinum
    swung, and Silver had no world going round it."""
    print("\n83. build 310: streak colours, Profile tab lit in its sub-screens, sliding top tabs, steady board, online grace, flares, emblems")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      const out = {};
      /* the streak pop: a colour per tier, and still up at 2.6s */
      theme.muteBanners = false;
      const cols = [10, 25, 50, 75, 100, 150, 250, 350].map(n => { showRunStreakBanner(n); const e = document.querySelector('.streak-pop');
        return getComputedStyle(e).getPropertyValue('--sk').trim() + '|' + e.className; });
      out.streakDistinct = new Set(cols.map(c => c.split('|')[0])).size;
      /* different COLOURS, not eight greens: the hues have to span the wheel */
      const hue = hex => { const n = parseInt(hex.replace('#', ''), 16), r = (n >> 16) / 255, g = (n >> 8 & 255) / 255, b = (n & 255) / 255;
        const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if(!d) return 0;
        let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return (h * 60 + 360) % 360; };
      const hs = cols.map(c => hue(c.split('|')[0] || '#000000')).sort((a, b) => a - b);
      let gap = 360 - hs[hs.length - 1] + hs[0]; for(let i = 1; i < hs.length; i++) gap = Math.max(gap, hs[i] - hs[i - 1]);
      out.hueSpan = Math.round(360 - gap);
      out.past50 = cols[3].indexOf('streak-lv4') >= 0 && cols[7].indexOf('streak-lv8') >= 0;
      showRunStreakBanner(25); await wait(2600); out.streakStill = !!document.querySelector('.streak-pop');
      await wait(900); out.streakGone = !document.querySelector('.streak-pop');
      /* the Profile tab stays lit on every screen reached from Profile */
      const lit = () => !!document.querySelector('#bottomtab-profile.active');
      out.lit = {};
      for(const [k, f] of [['friends', () => showFriends()], ['calendar', () => showCalendar && showCalendar()], ['testreview', () => showTestReviewList && showTestReviewList()]]){
        try{ f(); }catch(e){ out.lit[k] = 'threw ' + e.message; continue; }
        await wait(500); out.lit[k] = lit();
      }
      /* the top tabs slide: a slider, and it moves on its own transition */
      showRankings('level'); await wait(700);
      const seg = document.querySelector('.has-seg-slider'), sl = seg && seg.querySelector(':scope > .seg-slider');
      out.slider = !!sl;
      if(sl){
        const x0 = sl.getBoundingClientRect().left;
        const btns = [...seg.children].filter(b => b !== sl && b.tagName === 'BUTTON');
        const target = btns.find(b => !b.classList.contains('active') && !b.classList.contains('is-on'));
        target.click(); await wait(60);
        const mid = sl.getBoundingClientRect().left; await wait(700);
        const end = sl.getBoundingClientRect().left;
        out.slide = { x0: Math.round(x0), mid: Math.round(mid), end: Math.round(end), tr: getComputedStyle(sl).transitionProperty };
      }
      /* a snapshot keeps each character: same node, before and after */
      leaderboardRows = [0, 1, 2, 3].map(i => ({ pub: 'p' + i, firstName: 'N' + i, avatarChar: AVATAR_CHARACTERS[i].id, level: 40 - i, badges: 3, hundos: 9, xp: 9000 - i, correct: 900 - i, week: 100, lastModified: Date.now() }));
      showRankings('level'); await wait(600);
      const rowOf = n => [...document.querySelectorAll('.rank-row')].find(r => (r.querySelector('.rank-name') || {}).textContent === n);
      const before = rowOf('N2') && rowOf('N2').querySelector('.rank-avatar-wrap');
      leaderboardRows = leaderboardRows.map(e => Object.assign({}, e, { correct: e.correct + 1 }));
      const rows = rowOf('N2').parentElement;
      const board = RANKING_BOARDS.find(b => b.key === rankingsBoardKey);
      if(board) renderRankingRows(rows, leaderboardRows, board, {});
      await wait(200);
      const after = rowOf('N2') && rowOf('N2').querySelector('.rank-avatar-wrap');
      out.sameAvatar = !!before && before === after; out.boardFound = !!board;
      out.noRowBanner = !document.querySelector('.lb-row-bnr') && typeof LB_ROW_BANNER !== 'undefined' && LB_ROW_BANNER === '';
      /* online: a heartbeat is green, leaving is green for the grace, then grey */
      const now = Date.now();
      presenceMap = { a: now - 60000, b: -(now - 60000), c: -(now - 3 * 60000), d: 0 };
      out.online = ['a', 'b', 'c', 'd'].map(p => isOnline({ pub: p }));
      out.grace = typeof OFFLINE_GRACE_MS !== 'undefined' ? OFFLINE_GRACE_MS : 0;
      /* the tiny flares are one bubble, all alike */
      showHome(); await wait(900);
      /* build 313: HTML flares, every one the same box (its width as a share
         of the hero) and the same glass body; three until Void is held */
      const dots = [...document.querySelectorAll('.cosmic-hero-wrap .cosmic-orbit-dot')];
      const hw = (document.querySelector('.cosmic-hero-wrap') || { getBoundingClientRect: () => ({ width: 1 }) }).getBoundingClientRect().width;
      /* offsetWidth: the layers turn, and a turned box's bounding rect is bigger */
      const hwo = (document.querySelector('.cosmic-hero-wrap') || { offsetWidth: 1 }).offsetWidth;
      out.dots = dots.length; out.dotR = [...new Set(dots.map(d => (d.offsetWidth / hwo * 360 / 2).toFixed(0)))];
      out.rims = document.querySelectorAll('.cosmic-hero-wrap .cosmic-orbit-dot .cof-body').length;
      out.shade = !!document.querySelector('.cosmic-sphere-shade');
      out.litSmoke = !!document.querySelector('.cosmic-smoke-lit');
      /* emblems: Platinum's pair goes round and nothing swings; Silver has a world */
      const pl = buildRankEmblemSVG('vanguard'), sv = buildRankEmblemSVG('ranger');
      out.plat = ['.rk-bin-a', '.rk-bin-b', '.rk-bin-b-front'].every(c => pl.querySelector(c)) && !pl.querySelector('.rk-swing');
      out.silver = !!sv.querySelector('.rk-orbit') && !!sv.querySelector('.rk-orbit-front');
      /* a theme's page glow has its own triad */
      document.documentElement.dataset.accent = 'rookie';
      const cs = getComputedStyle(document.documentElement);
      out.bg = [cs.getPropertyValue('--bg-c3').trim(), cs.getPropertyValue('--theme-c3').trim()];
      document.documentElement.dataset.accent = 'ink';
      return out; }""")
    ctx.close()
    check("the streak pop has eight different colours, one per tier, across the wheel", r["streakDistinct"] == 8 and r["hueSpan"] >= 180, r)
    check("streaks past 50 get their own tiers (75 is the 4th, 350 the 8th)", r["past50"], r)
    check("the streak pop is still up at 2.6s and gone by 3.5s", r["streakStill"] and r["streakGone"], r)
    check("the Profile tab stays lit on Friends, Calendar and Test review", all(v is True for v in r["lit"].values()), r["lit"])
    sl = r.get("slide") or {}
    check("the leaderboard's top tabs have a sliding indicator", r["slider"], r)
    check("the indicator glides between tabs rather than jumping", bool(sl) and sl["x0"] != sl["end"] and sl["mid"] != sl["end"] and "transform" in sl["tr"], sl)
    check("a leaderboard snapshot keeps each character (no restart, no shake)", r["sameAvatar"] and r["boardFound"], r)
    check("no banners on leaderboard rows until one is picked", r["noRowBanner"], r)
    check("online: heartbeat green, just left green, left 3 min ago grey, 0 grey", r["online"] == [True, True, False, False] and r["grace"] == 120000, r)
    check("the tiny flares are all one size of bubble, each with a rim", r["dots"] == 3 and r["dotR"] == ["5"] and r["rims"] == 3, r)
    check("the big planet is the original: no night-side layer, no pale smoke", not r["shade"] and not r["litSmoke"], r)
    check("Platinum's two stars go round each other and nothing swings", r["plat"], r)
    check("Silver has a world going round it", r["silver"], r)
    check("Bronze's page glow has its own, brighter rim colour", r["bg"][0] and r["bg"][0].upper() != r["bg"][1].upper(), r["bg"])


def check_b310_vroom(br):
    """Build 310, second batch. Written against build 309, where: the
    host's back link said "Leave lobby" and went to the mode menu; a host
    whose create write hung sat on "Setting up your room" for good; Ready
    up came after Invite friends; the game cards were the theme accent;
    Match settings had a bare slider with no All pill and no hundo note;
    the start sheet said "Track my time" under the countdown and its
    toggles sat under "Options"."""
    print("\n84. build 310: Virtual Room back link, a fast host, the lobby order, Match settings, the timer names")
    import re as _re
    vr = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-vroom.py")).read()
    fake = _re.search(r'FAKE_FIRESTORE = """(.*?)"""', vr, _re.S).group(1)
    keep = "window.addEventListener('DOMContentLoaded', function(){ try{ window.__osr = onSnapshotResilient; }catch(e){} });"
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=fake + "\n" + keep)
    r = pg.evaluate("""async ()=>{ const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      try{ __useFake(); if(window.__osr) onSnapshotResilient = window.__osr; }catch(e){}
      /* a create write the server never acknowledges */
      const realColl = fbDb.collection.bind(fbDb);
      fbDb.collection = name => { const c = realColl(name); if(name !== 'vrooms') return c;
        const realDoc = c.doc.bind(c);
        c.doc = id => { const d = realDoc(id); const realSet = d.set.bind(d);
          d.set = (...a) => { realSet(...a); return new Promise(() => {}); }; return d; };
        return c; };
      const t0 = Date.now();
      const ok = await Promise.race([createVirtualRoomLobby([], null), wait(4000).then(() => 'timeout')]);
      out.hostMs = Date.now() - t0; out.hostOk = ok;
      fbDb.collection = realColl;
      await wait(700);
      const lobby = document.querySelector('.screen-vroom-lobby');
      out.inLobby = !!lobby;
      if(lobby){
        const kids = [...lobby.children].map(c => c.className);
        const iRoster = kids.findIndex(c => /vroom-roster/.test(c)), iReady = kids.findIndex(c => /vroom-readyup-btn/.test(c)), iInvite = kids.findIndex(c => /vroom-code-row/.test(c));
        out.order = [iRoster, iReady, iInvite];
        const back = lobby.querySelector('.back-link');
        out.backText = back ? back.textContent.trim() : '';
        /* Match settings: coloured games, the All pill, the hundo note */
        document.querySelector('.vroom-settings-btn').click(); await wait(600);
        document.querySelector('.picks .pick input').click(); await wait(150);
        document.querySelector('.vroom-setup-go').click(); await wait(500);
        const m = document.getElementById('unitoptions-modal');
        out.modeColours = [...m.querySelectorAll('.vroom-host-mode')].map(b => getComputedStyle(b).getPropertyValue('--mc').trim());
        out.allBtn = !!m.querySelector('.slider-allbtn');
        const range = m.querySelector('input[type=range]');
        range.value = 8; range.dispatchEvent(new Event('input')); range.dispatchEvent(new Event('change')); await wait(200);
        const hn = m.querySelector('.hundo-note');
        out.noteCut = hn && !hn.hidden && !hn.classList.contains('is-ok') ? hn.textContent : '';
        const before = Number(range.value);
        m.querySelector('.slider-allbtn').click(); await wait(80);
        out.allMid = Number(range.value); out.allBefore = before; out.allMax = Number(range.max);
        await wait(500);
        out.allEnd = Number(range.value);
        out.noteAll = hn && !hn.hidden && hn.classList.contains('is-ok');
        m.hidden = true;
        /* back out of the lobby: lands on the Virtual Room screen */
        showVirtualRoomLobby(); await wait(400);
        document.querySelector('.screen-vroom-lobby .back-link').click(); await wait(500);
        out.after = !!document.querySelector('.vrc-modecards');
      }
      /* the start sheet: Stopwatch first, by name, and the section names */
      cfg.mode = 'drill'; cfg.units = topicsIn(QUESTIONS).slice(0, 1); showSetup(); await wait(400);
      const sh = document.getElementById('unitoptions-modal'); sh.hidden = false; await wait(200);
      out.timerRows = [...sh.querySelectorAll('.timer-sect > .opt')].map(r => (r.querySelector('.otext') || r).firstChild.textContent.trim());
      out.fold = (sh.querySelector('.more-toggle') || {}).textContent || '';
      out.optLab = (sh.querySelector('.opt-tiles-sect > .slab') || {}).textContent || '';
      out.shuffleHint = ([...sh.querySelectorAll('.opt')].find(r => /Shuffle/.test(r.textContent)) || { textContent: '' }).querySelector?.('.ohint')?.textContent || '';
      return out; }""")
    ctx.close()
    check("a host goes into the lobby within 2s even if the server never answers", r.get("inLobby") and r.get("hostMs", 9999) < 2000, [r.get("hostMs"), r.get("hostOk")])
    check("the lobby's back link says Virtual Room", r.get("backText") == "Virtual Room", r.get("backText"))
    check("and goes back to the Virtual Room screen", r.get("after") is True, r.get("after"))
    o = r.get("order") or [-1, -1, -1]
    check("Ready up sits under the room list and above Invite friends", 0 <= o[0] < o[1] < o[2], o)
    mc = r.get("modeColours") or []
    check("each game in Match settings has its own colour", len(mc) == 3 and all(mc) and len(set(mc)) == 3, mc)
    check("Match settings has the All pill", r.get("allBtn") is True, r)
    check("fewer questions than the units hold says no hundo", "won't count" in (r.get("noteCut") or ""), r.get("noteCut"))
    check("All slides the bar to the end rather than jumping",
          r.get("allBefore", 0) < r.get("allMid", 0) < r.get("allMax", 0) and r.get("allEnd") == r.get("allMax"),
          [r.get("allBefore"), r.get("allMid"), r.get("allEnd"), r.get("allMax")])
    check("at All the note says the hundo counts", r.get("noteAll") is True, r)
    check("the start sheet lists Stopwatch first, then Time limit (renamed in 313)", r.get("timerRows") == ["Stopwatch", "Time limit"], r.get("timerRows"))
    check("the timer card is called Stopwatch & timer", "Stopwatch" in (r.get("fold") or ""), r.get("fold"))
    check("the toggles are 'Answer choice options', not 'Options'", r.get("optLab") == "Answer choice options", r.get("optLab"))
    # Build 313, later the same day: "Dont mention in the shuffle thing
    # about the random question if questions already come shuffled no
    # matter what" - the line is about the choices and nothing else.
    check("the shuffle line is about the answer choices only, not the question order",
          "answer choices" in (r.get("shuffleHint") or "").lower() and "question" not in (r.get("shuffleHint") or "").lower(), r.get("shuffleHint"))


def check_b311_rank(br):
    """Build 311, the Rank tab. Written against build 310, where each
    fails: the light on the road was moved by a calc() mixing a
    percentage with lengths (which WebKit jumps to the end of instead of
    animating), the reward chips were sized to their own words and
    started at different x on a left-hand card, the circles were not
    tappable, the "To reach" word was the raw rank colour, and the
    rings filled in 1.2s."""
    print("\n85. build 311: the Rank tab - pixel-placed light, even chips, rank cards, slower rings")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
      const u = topicsIn(QUESTIONS); u.slice(0, 4).forEach(n => store.unitPerfects[n] = 999);
      store.rankMapFx244 = true; store.rankMapSeen = 99; store.rankMapProg = null;
      showProfile('ranks'); await wait(400);
      const tips = [...document.querySelectorAll('.rankmap-roadtip')];
      out.tips = tips.length;
      out.tipPx = tips.every(t => /^translateY\\(-?[0-9.]+px\\)$/.test(t.style.transform));
      out.ringDur = getComputedStyle(document.querySelector('.rankhero .rankhero-ringarc')).transitionDuration;
      const b = document.querySelector('.rankhero-gaugehead b');
      out.headEm = !!(b && b.querySelector('.rankhero-gaugehead-em svg'));
      out.headCol = b ? getComputedStyle(b).color : '';
      out.rawCol = (() => { const k = TIER_ORDER_FULL[TIER_ORDER_FULL.indexOf(rankOf(store)) + 1]; const d = document.createElement('i'); d.style.color = RANK_COLOR[k]; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })();
      /* every chip in a card the same width and starting at the same x */
      out.chips = [...document.querySelectorAll('.rankmap-stop')].map(st => {
        const r = [...st.querySelectorAll('.rankmap-gift')].map(g => g.getBoundingClientRect());
        return { n: r.length, w: Math.round(Math.max(...r.map(x => x.width)) - Math.min(...r.map(x => x.width))),
                 x: Math.round(Math.max(...r.map(x => x.left)) - Math.min(...r.map(x => x.left))),
                 h: Math.round(Math.max(...r.map(x => x.height)) - Math.min(...r.map(x => x.height))) }; });
      out.note = document.querySelector('.ranks-note').textContent;
      /* tap a reached circle, then a locked one */
      const nodes = [...document.querySelectorAll('.rankmap-node')];
      out.tappable = nodes.every(n => n.getAttribute('role') === 'button');
      nodes[0].click(); await wait(500);
      let c = document.querySelector('.ranklore-card');
      out.reached = c ? { cls: c.className, lore: c.querySelector('.ranklore-text').textContent, reqs: c.querySelectorAll('.ranklore-req').length,
                          gifts: c.querySelectorAll('.rankmap-gift').length } : null;
      document.querySelector('.invite-overlay')?.remove();
      nodes[nodes.length - 1].click(); await wait(500);
      c = document.querySelector('.ranklore-card');
      out.locked = c ? { cls: c.className, lore: c.querySelector('.ranklore-text').textContent,
                         grey: getComputedStyle(c.querySelector('.ranklore-art svg')).filter } : null;
      document.querySelector('.invite-overlay')?.remove();
      }catch(e){ out.threw = String(e); }
      return out; }""")
    check("the road's light is placed in plain pixels, never a calc() with a percentage (WebKit jumps those)",
          r.get("tips", 0) >= 1 and r.get("tipPx") is True, r)
    check("the level and badge rings fill over 2.2s, not 1.2s", r.get("ringDur") == "2.2s", r)
    check("'To reach' names the rank (no emblem since 313), in the lifted colour the map uses rather than the raw one",
          r.get("headEm") is False and r.get("headCol") and r.get("headCol") != r.get("rawCol"), r)
    check("every reward chip on a card is one size and starts at one x",
          r.get("chips") and all(c["n"] >= 2 and c["w"] <= 1 and c["x"] <= 1 and c["h"] <= 1 for c in r["chips"]), r.get("chips"))
    # Build 313: "the climb description is bad, it's talking about specific
    # ranks" - it says ranks unlock rewards and names no rank.
    check("the climb's description says ranks unlock rewards without listing ranks",
          "unlock" in r.get("note", "") and not any(n in r.get("note", "") for n in ("Iron", "Bronze", "Silver", "Gold", "Platinum", "Sapphire", "Amethyst", "Supernova")), r.get("note"))
    check("every rank circle is a button that opens its card", r.get("tappable") is True and r.get("reached") and r.get("locked"), r)
    check("a reached rank's card tells its story, with both requirements and its unlocks",
          r.get("reached") and "is-reached" in r["reached"]["cls"] and len(r["reached"]["lore"]) > 60 and "story" not in r["reached"]["lore"]
          and r["reached"]["reqs"] == 2 and r["reached"]["gifts"] >= 2, r.get("reached"))
    check("a locked rank's card is grey and keeps its story back",
          r.get("locked") and "is-locked" in r["locked"]["cls"] and "read its story" in r["locked"]["lore"] and "grayscale" in r["locked"]["grey"], r.get("locked"))
    ctx.close()


def check_b312_shuffle(br):
    """Build 312, the shuffle: "the answer choices still aren't being
    properly shuffled and neither are the order of questions". Written
    against build 311, where 121 of 895 questions could never move (every
    question with a choice that points at the others was frozen whole),
    flashcards were never shuffled at all, and the same slot could hold
    the answer twice running."""
    print("\n86. build 312: the shuffle - every question can move, the pointing choices stay true, flashcards shuffle")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => { const out = {};
      const ids = qi => (QUESTIONS[qi].choices || []).map((c, k) => k);
      /* every question that is not hand-fixed moves at least once in 60 tries */
      let never = [], fixedMoved = [], checked = 0;
      QUESTIONS.forEach((q, qi) => {
        const n = (q.choices || []).length; if(n < 2) return;
        /* REVISED 6 Oct: the guide's order, exactly, for any question whose
           choices point at each other - not only the hand-fixed two */
        const base = ids(qi).join();
        const frozen = q.fixedOrder || (typeof choicesFrozen === 'function' ? choicesFrozen(qi) : choicesReferToEachOther(qi));
        let moved = false;
        for(let t = 0; t < 60 && !moved; t++) if(shuffledChoiceOrder(qi, false).join() !== base) moved = true;
        if(frozen){ if(moved) fixedMoved.push(qi); return; }
        checked++; if(!moved) never.push(q.src);
      });
      out.checked = checked; out.never = never.slice(0, 8); out.neverN = never.length; out.fixedMoved = fixedMoved.length;
      out.fixedN = QUESTIONS.filter((q, qi) => q.fixedOrder || choicesReferToEachOther(qi)).length;
      /* a choice that points at the others still points at the same set */
      let bad = [], pointing = 0;
      QUESTIONS.forEach((q, qi) => {
        if(!choicesReferToEachOther(qi) || q.fixedOrder) return; pointing++;
        const ch = q.choices, base = pointsUpLast(qi, ids(qi));
        const isLetter = k => CHOICE_REFERS_RE[1].test(String(ch[k]));
        const isRef = k => CHOICE_REFERS_RE.some(re => re.test(String(ch[k])));
        const refSet = (o, k) => { const at = o.indexOf(k);
          /* build 313: the letters are rewritten to follow their choices
             (choiceShown), so read them off the choice AS SHOWN */
          if(isLetter(k)){ const t = []; String(typeof choiceShown === 'function' ? choiceShown(qi, k, o) : ch[k]).replace(CHOICE_LETTER_RE, (m, x) => { t.push(o[x.toUpperCase().charCodeAt(0) - 65]); return m; }); return t.filter(x => x !== undefined && x !== k).sort().join(); }
          return o.slice(0, at).filter(x => !isRef(x)).sort().join(); };
        for(let t = 0; t < 120; t++){
          const o = shuffledChoiceOrder(qi, false);
          for(const k of ch.map((c, i) => i).filter(isRef))
            if(refSet(o, k) !== refSet(base, k) || o.indexOf(k) !== base.indexOf(k)){ bad.push([q.src, ch[k], o.join(''), base.join('')]); t = 999; break; }
        }
      });
      out.pointing = pointing; out.bad = bad.slice(0, 4);
      /* asked again, the answer is not in the same slot as last time */
      const qi0 = QUESTIONS.findIndex(q => !q.fixedOrder && (q.choices || []).length >= 4 && !choicesReferToEachOther(QUESTIONS.indexOf(q)));
      let repeats = 0, prev = null;
      for(let t = 0; t < 40; t++){ const o = shuffledChoiceOrder(qi0, true); const slot = o.indexOf(QUESTIONS[qi0].answer); if(slot === prev) repeats++; prev = slot; }
      out.repeats = repeats;
      /* flashcards come in a fresh order each deck */
      try{ const fu = [topicsIn(QUESTIONS)[1]];
        const a = flashcardDeck(fu, 'all', {}).join(), b = flashcardDeck(fu, 'all', {}).join(), c = flashcardDeck(fu, 'all', {}).join();
        out.fcDiffer = (a !== b) || (b !== c); out.fcLen = a.split(',').length; }catch(e){ out.fcErr = String(e); }
      return out; }""")
    check("every question with no choice pointing at the others can come up in a new choice order",
          r.get("checked", 0) > 700 and r.get("neverN") == 0, {k: r.get(k) for k in ("checked", "neverN", "never")})
    check("the hand-fixed questions and every All of the above / Both A & B question never move (6 Oct: exact study guide order)",
          r.get("fixedN", 0) > 100 and r.get("fixedMoved") == 0, {k: r.get(k) for k in ("fixedN", "fixedMoved")})
    # REVISED 6 Oct: covered by the never-move check above; a frozen
    # question's choices point exactly where the guide's do
    check("a choice that points at the others (all/none of the above, both A and B) keeps pointing at the same choices",
          r.get("pointing", 0) > 50 and all(b[2] == "".join(str(i) for i in range(len(b[2]))) for b in (r.get("bad") or [])), {k: r.get(k) for k in ("pointing", "bad")})
    check("asked again, the answer does not sit in the same slot as it did the time before", r.get("repeats") == 0, r.get("repeats"))
    check("flashcards come in a new order each time", r.get("fcDiffer") is True and r.get("fcLen", 0) > 5, r)
    ctx.close()


def check_b312_results(br):
    """Build 312: "Review test" on a perfect run was asked for ("when getting
    a 100, still provide a review option") and taken back before it shipped
    ("Nvm, if you get a 100, let's not do the review test thing"). A 100%
    run ends on Re-run and Main menu, as build 311 did; the review is only
    for the misses."""
    print("\n87. build 312: a perfect run ends on Re-run and Main menu - no Review test")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.source = 'all'; cfg.size = 0; cfg.versions = {};
      theme.autoAdvance = true;
      beginRun(freshOrder(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic.trim() === 'Identity Crimes')), null);
      for(let i = 0; i < 80 && !document.querySelector('.choice'); i++) await wait(100);
      let last = -1, guard = 0;
      while(testInProgress && guard++ < 240){
        const ch = [...document.querySelectorAll('#stage .choice:not(.locked)')];
        if(pos !== last && ch.length){ last = pos; const slot = correctSlot(order[pos]); ch[slot] && ch[slot].click(); }
        await wait(250);
      }
      for(let i = 0; i < 100 && !document.querySelector('.rs-final button'); i++){ document.querySelector('.rs-screen')?.click(); await wait(200); }
      await wait(600);
      return { btns: [...document.querySelectorAll('.rs-final button')].map(b => b.textContent.trim()) }; }""")
    check("a 100% run's final buttons are Re-run and Main menu, with no Review test", r.get("btns") == ["Re-run", "Main menu"], r.get("btns"))
    ctx.close()
    # "if I get a hundo on a unit that I already have a badge on, you don't
    # need to show the badge stuff there, no point"
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const U = 'Identity Crimes';
      const run = async () => {
        cfg.mode = 'drill'; cfg.units = [U]; cfg.source = 'all'; cfg.size = 0; cfg.versions = {}; theme.autoAdvance = true;
        beginRun(freshOrder(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic.trim() === U)), null);
        for(let i = 0; i < 80 && !document.querySelector('.choice'); i++) await wait(100);
        let last = -1, guard = 0;
        while(testInProgress && guard++ < 240){
          const ch = [...document.querySelectorAll('#stage .choice:not(.locked)')];
          if(pos !== last && ch.length){ last = pos; const slot = correctSlot(order[pos]); ch[slot] && ch[slot].click(); }
          await wait(250);
        }
        for(let i = 0; i < 100 && !document.querySelector('.rs-final button'); i++){ document.querySelector('.rs-screen')?.click(); await wait(200); }
        return document.querySelectorAll('.badgeprogress-wrap').length;
      };
      store.unitPerfects[U] = badgeThresholdFor(U) + 3; saveStore();
      out.held = await run();
      testInProgress = false; showHome(); await wait(600);
      store.unitPerfects[U] = 0; saveStore();
      out.filling = await run();
      return out; }""")
    check("a hundo on a unit whose badge you already hold shows no badge box", r.get("held") == 0, r)
    check("and one still filling up keeps its badge progress box", r.get("filling", 0) >= 1, r)
    ctx.close()


def check_b312_unlocks(br):
    """Build 312: "The Home Screen unlock banner didn't show up for Zeus".
    Build 311 marked a pop-up shown the moment it was BUILT, so one cut
    short before anybody saw it still counted and Home never played it.
    And the three ultimates: Astral (every character), Celestial (every
    banner), Zenith (everything, the other two included)."""
    print("\n88. build 312: an unlock card counts only once seen; three ultimates; Lights Out")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const shown = id => !!(store.unlocksShown && (store.unlocksShown.chars || []).indexOf(id) >= 0);
      store.unlocksShown = store.unlocksShown || { chars: [], banners: [] };
      store.unlocksShown.chars = (store.unlocksShown.chars || []).filter(x => x !== 'zeus' && x !== 'clown');
      /* cut short at 300ms: still owed */
      let h = playUnlockSpotlight({ kind: 'character', character: 'zeus', feat: true, kicker: 'Character unlocked' }, 1, 1, () => {});
      await wait(300); h.stop(); await wait(1300);
      out.cutShort = shown('zeus');
      /* left up: counted once it has been seen */
      h = playUnlockSpotlight({ kind: 'character', character: 'clown', feat: true, kicker: 'Character unlocked' }, 1, 1, () => {});
      await wait(1500); out.seen = shown('clown'); h.stop();
      /* the ultimates, in order, each its own look */
      out.ult = AVATAR_CHARACTERS.filter(c => c.ultimate).map(c => c.id);
      const looks = {}; out.ult.forEach(id => { const sv = buildAvatarCharSVG(id); looks[id] = ['za', 'zb', 'zc'].filter(k => sv.querySelector('[class*="cx-fx-' + k + '"]')); });
      out.looks = looks;
      out.ultBanners = BANNERS.filter(b => b.ultimate).map(b => b.id);
      /* the ladder: everything else held -> Astral and Celestial, and Zenith only once those are too */
      const realLocked = isLockedCharacter, realEarned = bannerEarned, realAccent = isLockedAccent;
      const ultIds = ['astral', 'celestial', 'zenith'];
      window.isLockedCharacter = id => ultIds.indexOf(id) >= 0 ? realLocked(id) : false;
      window.bannerEarned = id => ultIds.indexOf(id) >= 0 ? realEarned(id) : true;
      window.isLockedAccent = () => false;
      /* build 313: Zenith also counts the hundo effects, read off the hundos */
      const hundosWas = store.lifetime.perfectTests; store.lifetime.perfectTests = Math.max(hundosWas || 0, 500);
      out.astral = !isLockedCharacter('astral'); out.celestial = !isLockedCharacter('celestial');
      out.astralBanner = bannerEarned('astral'); out.celestialBanner = bannerEarned('celestial');
      out.zenith = !isLockedCharacter('zenith');
      const up = ultimateProgress(); out.up = up;
      store.lifetime.perfectTests = hundosWas;
      window.isLockedCharacter = realLocked; window.bannerEarned = realEarned; window.isLockedAccent = realAccent;
      /* Lights Out: hundos between 8 PM and midnight, seeded once from
         the history. 21:00 with hundos:1 counts 1; 22:00 with unit scores
         {100, 90} counts 1; 23:00 part of a unit counts 0; 07:00 counts 0. */
      const at = h => { const d = new Date(); d.setHours(h, 10, 0, 0); return d.getTime(); };
      store.testHistory = [
        { label: 'a', units: ['x'], pct: 100, playedAt: at(21), hundos: 1 },
        { label: 'b', units: ['x', 'y'], pct: 95, playedAt: at(22), up: { x: 100, y: 90 } },
        { label: 'c', units: ['x'], pct: 100, playedAt: at(23), part: true },
        { label: 'd', units: ['x'], pct: 100, playedAt: at(7) } ];
      store.lateHundos = 0; store.lateHundosSeed312 = false;
      const b = bannerDef('early10');
      out.early = b ? { need: b.need, have: b.have(), name: b.name, label: b.label } : null;
      store.lateHundos = 3;
      out.earned = bannerEarned('early10');
      return out; }""")
    check("an unlock card cut short before it was seen stays owed, so Home still plays it", r.get("cutShort") is False, r)
    check("an unlock card that stayed up counts as shown", r.get("seen") is True, r)
    check("three ultimates, hardest last: Astral, Celestial, Zenith", r.get("ult") == ["astral", "celestial", "zenith"], r.get("ult"))
    check("each ultimate wears its own look (Astral the plasma, Celestial the stars, Zenith the obsidian)",
          r.get("looks") == {"astral": ["zc"], "celestial": ["zb"], "zenith": ["za"]}, r.get("looks"))
    check("each ultimate has its banner, last in the list", r.get("ultBanners") == ["astral", "celestial", "zenith"], r.get("ultBanners"))
    check("every other character earns Astral and every banner earns Celestial, character and banner alike",
          r.get("astral") and r.get("celestial") and r.get("astralBanner") and r.get("celestialBanner"), r)
    check("Zenith asks for everything, the other two ultimates included", r.get("zenith") is True and r["up"]["have"] == r["up"]["need"], r.get("up"))
    # First Light was "10 tests before 8 in the morning" ("I wouldn't even
    # want to do that challenge"), then a hundo in 10 units. Madison's own
    # idea replaced both: "get a hundo between 8pm and 12pm ... Or 3 hundos".
    check("Lights Out is 3 hundos between 8 PM and midnight, seeded from the evening hundos already in the history",
          r.get("early") and r["early"]["need"] == 3 and r["early"]["have"] == 2 and r["early"]["name"] == "Lights Out"
          and "8 PM" in r["early"]["label"] and r.get("earned") is True, r)
    ctx.close()
    # A real perfect run counts only in the evening: the same whole-unit
    # hundo at 21:30 adds one, at 10:30 adds nothing.
    for hour, want in ((21, 1), (10, 0)):
        ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
        r = pg.evaluate("""async (hour) => { const wait = ms => new Promise(r => setTimeout(r, ms));
          const real = Date.now.bind(Date), d = new Date(); d.setHours(hour, 30, 0, 0);
          const off = d.getTime() - real(); Date.now = () => real() + off;
          store.lateHundosSeed312 = true; store.lateHundos = 0;
          cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.source = 'all'; cfg.size = 0; cfg.versions = {}; theme.autoAdvance = true;
          beginRun(freshOrder(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic.trim() === 'Identity Crimes')), null);
          for(let i = 0; i < 80 && !document.querySelector('.choice'); i++) await wait(100);
          let last = -1, guard = 0;
          while(testInProgress && guard++ < 240){
            const ch = [...document.querySelectorAll('#stage .choice:not(.locked)')];
            if(pos !== last && ch.length){ last = pos; const slot = correctSlot(order[pos]); ch[slot] && ch[slot].click(); }
            await wait(250);
          }
          await wait(600);
          Date.now = real;
          return { late: store.lateHundos, top: (store.testHistory[0] || {}).pct }; }""", hour)
        check("a whole-unit hundo finished at %02d:30 adds %d to Lights Out" % (hour, want),
              r.get("top") == 100 and r.get("late") == want, r)
        ctx.close()


def check_b312_flares(br):
    """Build 312, the secret flares: "This secret flare has a square around
    it"; "the void cutscene ... started hopping up and down ... void should
    have became super faint and slowly started to appear out of the dark,
    potentially starting with the flares being placed in the middle ...
    lasting another 5-10 seconds"; "when you go back to main menu, you get
    a banner pop up that says the you can now unlock umbra". Written
    against build 311, where the flare card carried a drop-shadow filter
    (a lit square on iOS), the figure swapped to the bouncing win reaction
    and breathed up and down, the scene ended at 11.2s, and Home said
    nothing about the hunt that had just opened."""
    print("\n90. build 312: the flare card has no box, Void fades up out of the dark without hopping, Home tells you Umbra is out there")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      /* the flare card: no filter on the art (WebKit paints a filtered box as its rectangle) */
      const h = playUnlockSpotlight({ kind: 'flare', flare: 'yellow', kicker: 'Secret flare found', name: 'Yellow',
        color: MYSTERY_COLOR.yellow, art: () => buildFlareOrb(MYSTERY_COLOR.yellow, 't') }, 1, 1, () => {});
      await wait(1900);
      const art = document.querySelector('.rs-spot .rs-spot-art');
      out.cardFilter = art ? getComputedStyle(art).filter : 'missing';
      h.stop();
      /* the Void scene */
      store.mysteryColorsFound = { red: true, orange: true, yellow: true };
      const sc = playFinalFlareScene('yellow', () => {});
      await wait(9800);
      const ov = document.querySelector('.ff-scene');
      out.hop = !!(ov && ov.querySelector('.char-react-win'));
      const fig = ov && ov.querySelector('.ff-fig');
      out.figFilter = fig ? getComputedStyle(fig).filter : 'missing';
      out.figAnim = fig ? getComputedStyle(fig).animationName : 'missing';
      out.flaresFirst = !!(ov && ov.querySelector('.ff-figflares svg'));
      await wait(6800);
      out.stillUpAt16s = !!document.querySelector('.ff-scene');
      sc && sc.stop && sc.stop();
      /* the Home card */
      ensureUnlocksShown(); markUnlocksShown(announceableHeldCharacters(), BANNERS.filter(b => bannerEarned(b.id)).map(b => b.id));
      store.flareHintsShown = [];
      out.owed = typeof pendingFlareHints === 'function' ? pendingFlareHints() : 'none';
      showHome(); await wait(4200);
      const spot = document.querySelector('.rs-spot');
      out.card = spot ? spot.textContent : '';
      spot && spot.click(); await wait(1200);
      out.shown = (store.flareHintsShown || []).slice();
      showHome(); await wait(4200);
      out.again = !!document.querySelector('.rs-spot');
      store.mysteryColorsFound = { red: true, orange: true, yellow: true, violet: true };
      out.owedNext = typeof pendingFlareHints === 'function' ? pendingFlareHints() : 'none';
      return out; }""")
    check("the secret flare card draws no filter round the orb (the square on iOS)", r.get("cardFilter") == "none", r.get("cardFilter"))
    check("Void never takes the bouncing win reaction in its own scene", r.get("hop") is False, r)
    check("the emerging figure has no filter and no up-and-down animation", r.get("figFilter") == "none" and r.get("figAnim") == "none", r)
    check("its flares light first, alone in the dark", r.get("flaresFirst") is True, r)
    check("the scene runs past 16 seconds (it ended at 11 before)", r.get("stillUpAt16s") is True, r)
    check("holding Void owes the Umbra hint, and Home shows it", r.get("owed") == ["umbra"] and "Umbra is out there" in r.get("card", ""), r)
    check("tapped away, it is recorded and never shown again", r.get("shown") == ["umbra"] and r.get("again") is False, r)
    check("holding Umbra owes the Horizon hint next", r.get("owedNext") == ["singularity"], r)
    ctx.close()


def check_b312_looks(br):
    """Build 312: "ensure all characters blink"; the leaderboard's
    characters "protruding outside the circles"; the tab bubble's "weird
    line" along its bottom; the Next button "0.25 seconds faster"."""
    print("\n89. build 312: everyone blinks, board avatars stay in their circles, the tab bubble, the Next button")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const host = document.createElement('div'); host.className = 'char-live'; host.style.cssText = 'position:fixed;left:0;top:0;width:60px;height:60px';
      document.body.appendChild(host);
      out.noBlink = []; out.ballsStill = null;
      AVATAR_CHARACTERS.filter(c => !c.retired).forEach(c => {
        host.innerHTML = ''; const sv = buildAvatarCharSVG(c.id); host.appendChild(sv);
        const e = sv.querySelector('.cx-eyes');
        if(!e || !/cx-blink/.test(getComputedStyle(e).animationName)) out.noBlink.push(c.id);
      });
      host.remove();
      const still = buildAvatarCharSVG('clown'); document.body.appendChild(still);
      out.ballsStill = getComputedStyle(still.querySelector('.cx-fx-cl3balls')).opacity; still.remove();
      /* Orion's constellation is in the sky, not across his face */
      const orion = buildAvatarCharSVG('astronaut');
      out.orionLines = [...orion.querySelectorAll('.cx-fx-sa3line')].map(l => Math.max(...l.getAttribute('d').match(/[0-9.]+/g).filter((v, i) => i % 2 === 0).map(Number)));
      /* the board's avatars */
      for(let i = 0; i < 6; i++) await fbDb.collection('leaderboard').doc('p' + i).set({ firstName: 'P' + i, avatarChar: ['zeus', 'inferno', 'singularity', 'clown', 'zenith', 'astral'][i], accent: 'ink', level: 40 - i, badges: 3, hundos: 20 - i, xp: 40000 - i * 900, tests: 30, week: weekKeyNow(), weekPoints: 900 - i * 50, lastModified: Date.now(), seenAt: Date.now() });
      showRankings(); await wait(1800);
      out.clip = [...document.querySelectorAll('.rank-row .rank-avatar')].slice(0, 6).map(a => { const s = getComputedStyle(a); return s.overflow + '|' + s.clipPath; });
      /* the tab bubble sits inside the bar, so it has no edge on the bar's own */
      const sl = document.querySelector('.bottomtabs-slider');
      out.pill = sl ? { top: getComputedStyle(sl, '::before').top, bottom: getComputedStyle(sl, '::before').bottom } : null;
      return out; }""")
    check("every character blinks", r.get("noBlink") == [], r.get("noBlink"))
    check("the Clown's juggling balls are hidden in a still drawing (they would stack as one ball)", r.get("ballsStill") == "0", r.get("ballsStill"))
    check("Orion's constellation sits in the sky beside him, clear of his face (x under 11)",
          r.get("orionLines") and all(x < 11 for x in r["orionLines"]), r.get("orionLines"))
    check("each board avatar is clipped to its circle", r.get("clip") and all(c.startswith("hidden") and "circle" in c for c in r["clip"]), r.get("clip"))
    check("the tab bubble is inset from the bar's top and bottom edges", r.get("pill") and r["pill"]["top"] == "5px" and r["pill"]["bottom"] == "5px", r.get("pill"))
    ctx.close()


def check_b313_lead(br):
    """Build 313, the lead's own list: "settings still says auto flag";
    the leaderboard blurbs "shortened"; an unlocked badge "just like the
    challenge is displayed on the non unlocked ones"; Phoenix "the hardest
    unique challenge"; the rank bars "applied to all of them"; the no-hundo
    note "near the button"; and the Leaderboard that "sometimes only
    displays myself" and "opens poorly with a missing piece"."""
    print("\n90. build 313 (lead): Auto-star, short blurbs, badge text, Phoenix 10, rank bars, the no-hundo note, the board that only showed you")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      showAppearance(); await wait(500);
      out.autoStar = [...document.querySelectorAll('#stage *')].some(e => e.childElementCount === 0 && /Auto-star questions you keep missing/.test(e.textContent || ''))
        || /Auto-star questions you keep missing/.test(document.getElementById('stage').textContent);
      out.autoFlag = /Auto-flag/i.test(document.getElementById('stage').textContent);
      out.blurbs = RANKING_BOARDS.map(b => (b.blurb || '').length);
      out.blurbText = RANKING_BOARDS.map(b => b.blurb || '');
      const U = topicsIn(QUESTIONS);
      store.unitPerfects = store.unitPerfects || {}; store.unitPerfects[U[0]] = badgeThresholdFor(U[0]) + 3; store.unitPerfects[U[1]] = 0;
      out.descHeld = badgeDetail(U[0]).desc; out.descNot = badgeDetail(U[1]).desc;
      out.phoenix = typeof PHOENIX_UNIT_RUN === 'number' ? PHOENIX_UNIT_RUN : null;
      /* the rank's colour on a bar that is met, not green */
      showRankLore('rookie'); await wait(900);
      out.fills = [...document.querySelectorAll('.ranklore-reqfill')].map(f => { const c = getComputedStyle(f); return { img: c.backgroundImage.slice(0, 15), glow: c.boxShadow !== 'none', met: f.closest('.ranklore-req').classList.contains('is-met') }; });
      document.querySelector('.invite-overlay')?.remove();
      /* a version label that only writes when it changes */
      showProfile('stats'); await wait(700);
      const st = document.documentElement.style, orig = st.setProperty.bind(st); let writes = 0;
      st.setProperty = (k, v, pr) => { if(k === '--vv-shift') writes++; return orig(k, v, pr); };
      const max = document.documentElement.scrollHeight - innerHeight;
      for(let i = 0; i < 16; i++){ window.scrollTo({ top: (i % 2) ? max : Math.max(0, max - 120), behavior: 'instant' }); await new Promise(r => requestAnimationFrame(r)); }
      delete st.setProperty; out.shiftWrites = writes;
      window.scrollTo({ top: 0, behavior: 'instant' });
      /* the no-hundo note sits by its chip */
      cfg.mode = 'drill'; cfg.units = []; cfg.size = 0; showSetup(); await wait(700);
      document.querySelector('.picks .pick .pname')?.click(); await wait(300);
      [...document.querySelectorAll('button')].find(b => /^start$/i.test(b.textContent.trim()))?.click(); await wait(1000);
      const sl = document.querySelector('#unitoptions-modal .howmany-sect input.slider');
      if(sl){ sl.value = Math.max(1, Math.floor(Number(sl.max) / 2)); sl.dispatchEvent(new Event('input', { bubbles: true })); sl.dispatchEvent(new Event('change', { bubbles: true })); }
      await wait(600);
      const chip = document.querySelector('.hundo-chip'); chip?.click(); await wait(400);
      const why = document.querySelector('.hundo-why');
      out.why = (chip && why && !why.hidden) ? { gap: Math.round(why.getBoundingClientRect().top - chip.getBoundingClientRect().bottom), text: why.textContent.trim() } : null;
      document.querySelector('#unitoptions-modal')?.remove(); document.querySelector('.unitoptions-scrim')?.remove();
      /* Customize goes up before its banner scenes are drawn, and every
         one of them is drawn a moment later */
      showCustomize('banner');
      /* a locked secret banner is veiled - a blurred still under glass,
         never drawn live (veilBanner, build 313) - so it is not one to wait
         for. Counting the four of them is why this failed on every build
         since the veil went in: 19 of 23, however long it waited. */
      const tiles = () => [...document.querySelectorAll('.screen-customize .banner-opt:not(.is-none)')].filter(t => !t.querySelector('.banner-opt-art.is-veiled'));
      out.custNow = { tiles: tiles().length, drawn: tiles().filter(t => t.querySelector('.bnr')).length };
      /* drawn a frame or two at a time, so how long that takes is the
         machine's frame rate: wait for it, up to 8s, rather than a fixed
         1.5s that a loaded 4-core runner does not always make */
      for(let i = 0; i < 32 && tiles().filter(t => t.querySelector('.bnr')).length < tiles().length; i++) await wait(250);
      out.custLater = { tiles: tiles().length, drawn: tiles().filter(t => t.querySelector('.bnr')).length };
      showHome(); await wait(300);
      /* the in-test streak: every tier keeps the last one's extras and adds one */
      theme.muteBanners = false;
      out.streak = [10, 25, 50, 75, 100, 250].map(n => { showRunStreakBanner(n); const e = document.querySelector('.streak-pop');
        return { n, ring: getComputedStyle(e, '::after').content !== 'none', sheen: !!e.querySelector('.streak-sheen'), sparks: e.querySelectorAll('.streak-spark').length,
                 flame: !!e.querySelector('.streak-ico'), flash: !!document.querySelector('.streak-flash') }; });
      document.querySelectorAll('.streak-pop, .streak-flash').forEach(e => e.remove());
      /* ---- the board ---- */
      store.publicId = 'me0000000001'; store.leaderboardOptIn = true; syncCode = syncCode || 'SYNC-test';
      const mk = (rows, cache) => ({ metadata: { fromCache: !!cache }, size: rows.length, empty: !rows.length, forEach: f => rows.forEach(r => f({ id: r.pub, data: () => r })) });
      const me = { pub: 'me0000000001', firstName: 'Me', avatarChar: 'grizzly', level: 3, badges: 0, hundos: 1, week: weekKeyNow(), weekPoints: 10 };
      const class10 = Array.from({ length: 10 }, (_, i) => ({ pub: 'p' + String(i).padStart(11, '0'), firstName: 'P' + i, avatarChar: 'zeus', level: 40 - i, badges: 3, hundos: 20 - i, week: weekKeyNow(), weekPoints: 900 - i * 50 }));
      let cbs = [];
      const real = fbDb, realOSR = onSnapshotResilient;
      /* the harness stub answers every listener with an empty SERVED
         snapshot; this test needs the snapshots it hands over itself */
      onSnapshotResilient = (ref, onNext) => ref.onSnapshot(onNext, () => {});
      fbDb = { collection: n => n !== 'leaderboard' ? real.collection(n) : ({ doc: id => real.collection(n).doc(id),
        get: () => new Promise(() => {}), onSnapshot: cb => { cbs.push(cb); return () => { cbs = cbs.filter(c => c !== cb); }; } }) };
      const real4 = () => document.querySelectorAll('.rank-row:not(.rank-row-skel)').length;
      /* cold: nothing in memory, the cache knows only you */
      leaderboardRows = []; showRankings('week'); await wait(60);
      cbs.forEach(cb => cb(mk([me], true))); await wait(300);
      out.cold = { skel: document.querySelectorAll('.rank-row-skel').length, rows: real4() };
      cbs.forEach(cb => cb(mk(class10.concat([me]), false))); await wait(300);
      out.coldServed = { skel: document.querySelectorAll('.rank-row-skel').length, rows: real4() };
      /* warm: the class is in memory, the cache answers with only you */
      showHome(); await wait(300); cbs = [];
      leaderboardRows = class10.slice(); showRankings('week'); await wait(60);
      out.warmFirst = real4();
      cbs.forEach(cb => cb(mk([me], true))); await wait(300);
      out.warmAfterCache = real4();
      /* the server may still take somebody off */
      cbs.forEach(cb => cb(mk(class10.slice(0, 7).concat([me]), false))); await wait(300);
      out.afterServed = real4();
      fbDb = real; onSnapshotResilient = realOSR; showHome();
      return out; }""")
    check("Settings says Auto-star, and nothing says Auto-flag", r.get("autoStar") is True and r.get("autoFlag") is False, [r.get("autoStar"), r.get("autoFlag")])
    # Build 314 reverses the one-line limit: "Make it all an extra sentence."
    # Each blurb is now at most two short sentences (60 characters or fewer
    # each), Overall no longer says "on the same rank", and Hundos says a
    # hundo is a whole unit at 100% rather than "one hundo per unit".
    import re as _re
    sents = [[x for x in _re.split(r"(?<=[.!?])\s+", t) if x] for t in r.get("blurbText") or []]
    check("each board's blurb is at most two short sentences (60 characters or fewer each)",
          sents and all(1 <= len(ss) <= 2 and all(len(x) <= 60 for x in ss) for ss in sents), r.get("blurbText"))
    check("Overall no longer says 'on the same rank'; Hundos says a hundo is 100% on a whole unit, not 'one hundo per unit'",
          r.get("blurbText") and not any("same rank" in t.lower() for t in r["blurbText"])
          and any("whole unit" in t for t in r["blurbText"]) and not any("one hundo per unit" in t for t in r["blurbText"]), r.get("blurbText"))
    check("an earned badge states its challenge exactly the way a locked one does",
          bool(re.fullmatch(r"Earn \d+ hundos? in this unit\.", r.get("descHeld") or "")) and bool(re.fullmatch(r"Earn \d+ hundos? in this unit\.", r.get("descNot") or "")),
          [r.get("descHeld"), r.get("descNot")])
    check("Phoenix asks for 10 units at 100% in a row", r.get("phoenix") == 10, r.get("phoenix"))
    f = r.get("fills") or []
    check("every requirement bar on a rank is in the rank's colour with its glow - a met one too, never green",
          len(f) == 2 and any(x["met"] for x in f) and all(x["img"].startswith("linear-gradient") and x["glow"] for x in f), f)
    check("scrolling does not rewrite the page's root style on every frame", r.get("shiftWrites") == 0, r.get("shiftWrites"))
    w = r.get("why")
    check("tapping No hundo opens its note right under the chip, saying to slide to All",
          isinstance(w, dict) and 0 <= w["gap"] <= 40 and "All" in w["text"], w)
    cn, cl = r.get("custNow") or {}, r.get("custLater") or {}
    check("Customize opens before drawing its banner scenes, and draws every one of them a moment later",
          cn.get("tiles", 0) > 10 and cn.get("drawn") == 0 and cl.get("drawn") == cl.get("tiles") == cn.get("tiles"), [cn, cl])
    st = {x["n"]: x for x in (r.get("streak") or [])}
    def lvl(n):
        x = st.get(n) or {}
        return (x.get("ring"), x.get("sheen"), x.get("sparks", 0) > 0, x.get("flame"), x.get("flash"))
    check("the streak pop gets more each tier: ring at 25, sweep at 50, sparks at 75, flame at 100, screen flash at 250",
          lvl(10) == (False, False, False, False, False) and lvl(25) == (True, False, False, False, False)
          and lvl(50) == (True, True, False, False, False) and lvl(75) == (True, True, True, False, False)
          and lvl(100) == (True, True, True, True, False) and lvl(250) == (True, True, True, True, True), r.get("streak"))
    c = r.get("cold") or {}
    check("a cold open shows placeholder rows, not you alone in 1st place, while the cache knows only you",
          c.get("skel", 0) >= 5 and c.get("rows") == 0, c)
    cs = r.get("coldServed") or {}
    check("and the class replaces the placeholders the moment the server answers", cs.get("skel") == 0 and cs.get("rows") == 11, cs)
    check("an open with the class in memory paints it in the first frame", r.get("warmFirst", 0) >= 10, r.get("warmFirst"))
    check("a cached answer holding only you does not shrink the board to you", r.get("warmAfterCache", 0) >= 10, r.get("warmAfterCache"))
    check("but the server's answer can still take somebody off", r.get("afterServed") == 8, r.get("afterServed"))
    ctx.close()


def check_b313_chars_centred(br):
    """Build 313: "Leaderboard character display problem (maybe an app wide
    problem idk ...) the characters move positions within their circle and
    aren't properly centered/displayed." The flip-book over a small
    character was laid at the corner of the SCALED drawing at full size:
    on the boards (drawing scaled .94) every one landed 1.5px right and
    down and 7% bigger, so it jumped off centre whenever its loop took
    over. Written against build 312, where it fails on every row."""
    print("\n91. build 313: every board character's flip-book sits exactly on its drawing, centred in its circle")
    chars = ['astral', 'celestial', 'zenith', 'ninja', 'poseidon', 'astronaut', 'ronin', 'zeus']
    import re as _re
    vr = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-vroom.py")).read()
    fake = _re.search(r'FAKE_FIRESTORE = """(.*?)"""', vr, _re.S).group(1)
    keep = "window.addEventListener('DOMContentLoaded', function(){ try{ window.__osr = onSnapshotResilient; }catch(e){} });"
    for label, w, h, dpr in [("iPhone 17 Pro Max", 440, 956, 3), ('iPad Pro 11"', 834, 1194, 2)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr, init=fake + "\n" + keep)
        r = pg.evaluate("""async (chars) => { const wait = ms => new Promise(r => setTimeout(r, ms));
          try{ __useFake(); if(window.__osr) onSnapshotResilient = window.__osr; }catch(e){}
          for(let i = 0; i < chars.length; i++) await fbDb.collection('leaderboard').doc('c' + i).set({ pub: 'c' + i, firstName: chars[i], avatarChar: chars[i], accent: 'ink', level: 40 - i, badges: 3, hundos: 20 - i, xp: 40000 - i * 900, tests: 30, week: weekKeyNow(), weekPoints: 900 - i * 50, lastModified: Date.now(), seenAt: Date.now() });
          showRankings(); const out = { rows: [] };
          for(let t = 0; t < 400; t++){ await wait(250); if(document.querySelectorAll('.rank-row .char-flip-play').length >= 4) break; }
          const read = () => [...document.querySelectorAll('.rank-row .rank-avatar-wrap')].filter(wr => wr.querySelector('.char-flip-play')).map(wr => {
            const c = wr.querySelector('.rank-avatar').getBoundingClientRect(), s = wr.querySelector('svg.avatarchar-svg').getBoundingClientRect(), f = wr.querySelector('.char-flip-play').getBoundingClientRect();
            return { dx: +((f.left + f.width / 2) - (s.left + s.width / 2)).toFixed(2), dy: +((f.top + f.height / 2) - (s.top + s.height / 2)).toFixed(2),
                     size: +(f.width / s.width).toFixed(3), off: +Math.hypot((f.left + f.width / 2) - (c.left + c.width / 2), (f.top + f.height / 2) - (c.top + c.height / 2)).toFixed(2) }; });
          out.rows = read(); await wait(2100); out.later = read(); await wait(2100); out.last = read();
          /* and each plays its OWN loop: Astral, Celestial and Zenith share
             a kind, and a flip-book picked by kind gave all three Zenith's */
          for(let t = 0; t < 480; t++){ const n = ['astral', 'celestial', 'zenith'].filter(c => [...document.querySelectorAll('.rank-row')].some(r => r.dataset.av === c && r.querySelector('.char-flip-play img'))).length; if(n === 3) break; await wait(250); }
          out.sheets = ['astral', 'celestial', 'zenith'].map(c => { const r = [...document.querySelectorAll('.rank-row')].find(r => r.dataset.av === c); const img = r && r.querySelector('.char-flip-play img'); return img ? img.src : null; });
          return out; }""", chars)
        rows = r.get("rows") or []
        worst = max([max(abs(x["dx"]), abs(x["dy"])) for x in rows] or [99])
        size = max([abs(x["size"] - 1) for x in rows] or [99])
        off = max([x["off"] for x in rows] or [99])
        drift = max([abs(a["dx"] - b["dx"]) + abs(a["dy"] - b["dy"]) for seq in (r.get("later") or [], r.get("last") or []) for a, b in zip(rows, seq)] or [0])
        check("%s: flip-books measured on %d rows" % (label, len(rows)), len(rows) >= 4, len(rows))
        check("%s: each flip-book's centre is within 0.6px of its drawing's" % label, worst <= 0.6, "%.2fpx" % worst)
        check("%s: each flip-book is the drawing's size (within 3%%)" % label, size <= 0.03, "%.1f%%" % (size * 100))
        check("%s: each sits within 1px of its circle's centre" % label, off <= 1.0, "%.2fpx" % off)
        check("%s: and stays put across the loop" % label, drift <= 0.1, drift)
        sh = r.get("sheets") or []
        check("%s: Astral, Celestial and Zenith each play their own loop, not one shared one" % label,
              len(sh) == 3 and all(sh) and len(set(sh)) == 3, [bool(x) for x in sh] + [len(set(sh))])
        ctx.close()


def check_b313_no_sweep(br):
    """Build 313: "the suffering effect thing some characters get that
    shoots across their face, let's get rid of that animation entirely."
    It was a band of light (sheen()) run across Orion's visor, Astral's
    helm, Celestial's mask, the Ronin's hat, the Marksman's lens and more.
    Written against build 312, where nine drawings carry one and the
    stylesheet still runs cx-sheen / cx-sheen-idle / avatar-scan."""
    print("\n92. build 313: no sweep of light crosses any character")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => { const out = { swept: [], kf: [] };
      AVATAR_CHARACTERS.forEach(c => { const sv = buildAvatarCharSVG(c.id); if(sv && sv.querySelector('.cx-fx-sheen, .avatarchar-scan, [class*="sheen"], [class*="sweep"]')) out.swept.push(c.id); });
      const bad = /^(cx-sheen|cx-sheen-idle|avatar-scan|cx-hk2-scan|cx-scan)$/;
      for(const sh of document.styleSheets){ let rules; try{ rules = sh.cssRules; }catch(e){ continue; }
        const walk = list => { for(const ru of list){ if(ru.cssRules) walk(ru.cssRules);
          if(ru.type === CSSRule.KEYFRAMES_RULE && bad.test(ru.name)) out.kf.push(ru.name);
          if(ru.style && bad.test((ru.style.animationName || '').split(',')[0].trim())) out.kf.push(ru.selectorText); } };
        walk(rules); }
      return out; }""")
    check("no character drawing carries a sweep", r["swept"] == [], r["swept"])
    check("no sweep keyframes or rules are left in the stylesheet", r["kf"] == [], r["kf"][:6])
    ctx.close()


def check_b313_alive(br):
    """Build 313: "Orions and sheriffs effects are lame"; "ronins animations
    are also non existent"; "Astrals effects are nonexistent ... The
    ultimate characters should be coolest and best in the app ... we need
    them all 3 to be a big cooler/better". Counts the parts that move on a
    live drawing - build 312 had Orion 24, the Sheriff 13, the Ronin 8,
    Astral 15, Celestial 21 and Zenith 26 - and checks each now moves more,
    the three ultimates the most of any earnable character, and that every
    new loop has its period divide the flip-book's 6s."""
    print("\n93. build 313: Orion, the Sheriff, the Ronin and the three ultimates do much more")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const out = { n: {}, odd: [] };
      const host = document.createElement('div'); host.className = 'char-live'; host.style.cssText = 'position:fixed;left:0;top:0;width:120px;height:120px'; document.body.appendChild(host);
      for(const c of AVATAR_CHARACTERS.filter(c => !c.retired)){
        host.innerHTML = ''; const sv = buildAvatarCharSVG(c.id); host.appendChild(sv);
        await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        const anims = sv.getAnimations({ subtree: true });
        out.n[c.id] = new Set(anims.map(a => a.effect.target)).size;
        if(['astronaut', 'poseidon', 'ronin', 'astral', 'celestial', 'zenith'].indexOf(c.id) >= 0)
          anims.filter(a => /^cx-(sa5|sh4|ronin2|zc2|zb2|za2|dt4)-/.test(a.animationName)).forEach(a => { const t = a.effect.getTiming(); const P = Number(t.duration) * (String(t.direction).indexOf('alternate') >= 0 ? 2 : 1);
            const k = 6000 / P; if(P <= 12000 && Math.abs(k - Math.round(k)) > .01) out.odd.push(c.id + ':' + a.animationName + ':' + P); });
      }
      host.remove(); return out; }""")
    n = r["n"]
    before = {"astronaut": 24, "poseidon": 13, "ronin": 8, "astral": 15, "celestial": 21, "zenith": 26}
    for cid, b in before.items():
        need = b + (8 if cid in ("astral", "celestial", "zenith") else 4)
        # Build 314 redrew Celestial and calmed it on request ("a smidge
        # toned down ... could look better"): it moves 27 parts, still more
        # than every earnable character but Orion (asserted below).
        if cid == "celestial":
            need = 25
        check("%s moves at least %d parts (was %d)" % (cid, need, b), n.get(cid, 0) >= need, n.get(cid))
    others = {k: v for k, v in n.items() if k not in ("astral", "celestial", "zenith", "voidwalker", "umbra", "singularity", "astronaut")}
    check("each ultimate moves more parts than every challenge, rank and starter character but Orion",
          all(n.get(u, 0) > max(others.values()) for u in ("astral", "celestial", "zenith")), (max(others.items(), key=lambda kv: kv[1]), {u: n.get(u) for u in ("astral", "celestial", "zenith")}))
    check("every loop added in 313 divides the 6s flip-book", r["odd"] == [], r["odd"][:6])
    ctx.close()


def check_b313_grades(br):
    """Build 313: "Ensure all the test results animations look good, ensure
    they work for the grade. Ensure they are noticeable, the emotions and
    everything." Four real drill runs of Identity Crimes (12 questions):
    all right (100), one wrong (91.7), three wrong (75) and six wrong (50).
    Each must land its own reaction on the results character, with the
    sign round it that every character shows however it is drawn; and on
    every character the drawing's own move must actually run (a per-
    character idle rule must not win over it). Written against build 312,
    which had no sign at all and a head tilt of a pixel or two for three
    of the four grades."""
    print("\n94. build 313: every grade shows on the results character - 100, 90+, a pass and a fail")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = { runs: {}, chars: [] };
      const U = 'Identity Crimes';
      const run = async wrong => {
        cfg.mode = 'drill'; cfg.units = [U]; cfg.source = 'all'; cfg.size = 0; cfg.versions = {}; theme.autoAdvance = true;
        beginRun(freshOrder(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic.trim() === U)), null);
        for(let i = 0; i < 80 && !document.querySelector('.choice'); i++) await wait(100);
        let last = -1, guard = 0, k = 0;
        while(testInProgress && guard++ < 240){
          /* a drill keeps the question until it is answered right, so a
             miss is a wrong pick first and then the right one */
          const ch = [...document.querySelectorAll('#stage .choice')];
          if(ch.length && !document.querySelector('#stage .choice.locked.correct, #stage .choice.is-correct')){
            const slot = correctSlot(order[pos]); let pick = slot;
            if(pos !== last){ last = pos; if(k++ < wrong) pick = (slot + 1) % ch.length; }
            if(ch[pick] && !ch[pick].classList.contains('locked')) ch[pick].click();
          }
          await wait(250);
        }
        for(let i = 0; i < 60 && !document.querySelector('.results-level-avatar[data-reacted]'); i++){ document.querySelector('.rs-screen')?.click(); await wait(200); }
        await wait(1600);
        const av = document.querySelector('.results-level-avatar');
        const res = av ? { cls: [...av.classList].filter(c => /char-react-/.test(c)).sort().join(' '),
          back: av.querySelectorAll(':scope > .char-emote-back').length, front: av.querySelector(':scope > .char-emote-front') ? av.querySelector(':scope > .char-emote-front').className : '',
          anims: [...new Set(av.getAnimations({ subtree: true }).map(a => a.animationName))] } : null;
        testInProgress = false; showHome(); await wait(500);
        return res;
      };
      for(const [band, wrong] of [['perfect', 0], ['great', 1], ['pass', 3], ['fail', 6]]) out.runs[band] = await run(wrong);
      /* every character, every band: its OWN move runs (build 314: each
         character's keyframes are named rx-<id>-..., see
         tools/gen-reactions.py) - and a per-character idle rule must not
         win over it */
      const want = { perfect: 1, great: 1, pass: 1, fail: 1 };
      const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0'; document.body.appendChild(host);
      for(const c of AVATAR_CHARACTERS.filter(c => !c.retired)) for(const band of Object.keys(want)){
        const av = document.createElement('span'); av.className = 'results-level-avatar char-live'; av.appendChild(buildAvatarCharSVG(c.id)); host.appendChild(av);
        if(typeof reactCharacter === 'function') reactCharacter(av, band); else { av.classList.remove('char-live'); av.classList.add('char-react-' + band); }
        await new Promise(r => requestAnimationFrame(r));
        const names = av.getAnimations({ subtree: true }).map(a => a.animationName);
        if(!names.some(n => n.indexOf('rx-' + c.id + '-') === 0)) out.chars.push(c.id + '/' + band);
        av.remove();
      }
      host.remove();
      return out; }""")
    runs = r["runs"]
    for band, sign in [("perfect", "char-emote-perfect"), ("great", "char-emote-great"), ("pass", "char-emote-pass"), ("fail", "char-emote-fail")]:
        x = runs.get(band) or {}
        # build 314: a 100 is the character's own move now, not the
        # Virtual Room win's (char-react-win) on top of a generic hop
        want_cls = "char-react-" + band
        check("a %s run lands %s on the results character" % (band, want_cls), x.get("cls") == want_cls, x)
        check("a %s run shows its sign round the character" % band, sign in (x.get("front") or ""), x.get("front"))
    check("the four grades look four different ways", len({(runs.get(b) or {}).get("front") for b in runs}) == 4, [(runs.get(b) or {}).get("front") for b in runs])
    check("every character's own reaction move runs for every grade", r["chars"] == [], r["chars"][:8])
    ctx.close()


# The characters and Customize stream of build 314.
B314_TRANSPARENT = ("()=>{const st=document.createElement('style'); st.textContent='html,body{background:transparent!important;background-image:none!important}"
                    " html::before,html::after,body::before,body::after{display:none!important} #stage,#bottomtabs,.topbar,header{display:none!important}'; document.head.appendChild(st);}")


def _b314_extent(pg, cid, sil=False):
    """Rasterise one still drawing, figure only (no scenery, no halo), at 10px a
    unit on a transparent page, and return the opaque (alpha>80) pixels as
    (x, y) in the drawing's own units."""
    import io as _io
    from PIL import Image as _Im
    pg.evaluate("""([cid, sil]) => { document.getElementById('b314h')?.remove();
      const host = document.createElement('div'); host.id = 'b314h'; host.style.cssText = 'position:fixed;left:0;top:0;width:540px;height:540px;z-index:99999';
      /* (build 313 drew a silhouette as two stacked svgs in a span) */
      const el = sil ? (typeof charSilhouetteSVG === 'function' ? charSilhouetteSVG(cid) : buildCharSilhouette(cid)) : buildAvatarCharSVGSafe(cid);
      if(el.tagName !== 'svg'){ host.className = 'char-live'; el.style.cssText = 'position:absolute;inset:0;display:block'; }
      (el.tagName === 'svg' ? [el] : [...el.querySelectorAll('svg')]).forEach(s => {
        s.setAttribute('viewBox', '-7 -7 54 54'); s.style.cssText = 'position:absolute;left:0;top:0;width:540px;height:540px;overflow:visible;-webkit-mask-image:none;mask-image:none;filter:none';
        s.querySelectorAll('.cx-bg').forEach(n => n.remove());
        s.querySelectorAll('circle').forEach(n => { if(/url\\(#(aura|halo)-/.test(n.getAttribute('fill') || '')) n.remove(); }); });
      host.appendChild(el); document.body.appendChild(host); }""", [cid, sil])
    png = pg.screenshot(clip={"x": 0, "y": 0, "width": 540, "height": 540}, omit_background=True)
    A = _Im.open(_io.BytesIO(png)).convert("RGBA").getchannel("A").load()
    pts = []
    for y in range(0, 540, 2):
        for x in range(0, 540, 2):
            if A[x, y] > 80:
                pts.append((x / 10 - 7, y / 10 - 7))
    return pts


def check_b314_chars(br):
    """Build 314, the characters and Customize. Every assertion here was
    run against build 313 and fails there:
    - "Some of the characters when looking at them in their rows, edges of
      them look to be cut off": a still drawing never rises above build
      272's top line (y 4.35 of 3..37) or within 4 units of the sides
      (Marksman's rifle runs off on purpose), and every drawing carries the
      edge feather; Umbra and Horizon sit inside a round frame (313: the
      hood and the crown ran into every circle).
    - "remove the colors from their outline when not unlocked": a locked
      secret's silhouette, as drawn in Customize, has no hue in it.
    - "All the characters when looking at them in the customize thing, the
      unlocked ones should be doing their animations": held characters on
      Customize play a running flip-book; locked ones stay still.
    - "My character on the bottom tab is not moving": the tab's character
      moves from the first frame, keeps its loop through a live update,
      and a recording that fails falls back to the live drawing instead
      of leaving it still for good.
    - "The silver rank looks a little blue" / "silver on the leaderboard
      doesn't look good": every Silver colour is neutral and the ranks
      stay apart.
    - "The badges you have not unlocked yet ... grey them out": an
      unearned badge, in the case and on its card, shows its form and no
      unit colour.
    - "it's hard to tell which character is selected": exactly one tile
      wears the ring and the tick, and a picker drawing's own halo is down.
    - "that text box is a smidge cramped": the name row goes while the
      field is open, and the field has room, on a 320px phone too."""
    print("\n95. build 314: characters fit their frames, play everywhere, silhouettes and Silver have no hue, unearned badges are grey")
    import math as _m
    import re as _re
    ctx, pg = booted(br, 700, 700, seed=USED_ACCOUNT, dpr=1)
    pg.evaluate(B314_TRANSPARENT)
    ids = pg.evaluate("()=>AVATAR_CHARACTERS.filter(c => !c.retired).map(c => c.id)")
    high, sides = [], []
    feather = pg.evaluate("""()=>{ const sv = buildAvatarCharSVGSafe('ninja'); document.body.appendChild(sv);
      const m = getComputedStyle(sv).webkitMaskImage || getComputedStyle(sv).maskImage || ''; sv.remove();
      const layers = m.split(/,\\s*(?=linear-gradient)/);
      return { n: layers.length, side: layers.some(l => /to right|90deg/.test(l)), top: /linear-gradient\\((to bottom, |180deg, )?(transparent|rgba\\(0, 0, 0, 0\\)) 0%/.test(m) }; }""")
    for cid in ids:
        pts = _b314_extent(pg, cid)
        if not pts:
            continue
        top = min(p[1] for p in pts)
        upper = [p[0] for p in pts if p[1] < 28]
        if top < 4.15:
            high.append("%s %.1f" % (cid, top))
        if cid != "marksman" and upper and (min(upper) < 3.9 or max(upper) > 36.1):
            sides.append("%s %.1f..%.1f" % (cid, min(upper), max(upper)))
    check("no still character rises above y 4.35 (build 272's line)", high == [], high)
    check("no character runs into the sides of its frame", sides == [], sides)
    check("every drawing feathers out at its top and sides (a second mask layer)", feather["n"] >= 2 and feather["side"] and feather["top"], feather)
    for cid in ("umbra", "singularity"):
        for sil in (False, True):
            pts = _b314_extent(pg, cid, sil)
            out = [p for p in pts if p[1] < 26 and _m.hypot(p[0] - 20, p[1] - 20) > 16.6]
            check("%s%s sits inside a round frame" % ("Horizon" if cid == "singularity" else "Umbra", " (silhouette)" if sil else ""),
                  len(out) == 0, "%d px outside" % len(out))
    # a locked secret's silhouette, drawn on its own over nothing: no pixel
    # of it (outline, flare, the pool behind it) has a hue
    import io as _io
    from PIL import Image as _Im
    for cid in ("voidwalker", "umbra", "singularity", "genesis"):
        pg.evaluate("""cid => { document.getElementById('b314h')?.remove();
          const host = document.createElement('div'); host.id = 'b314h'; host.className = 'char-live'; host.style.cssText = 'position:fixed;left:0;top:0;width:300px;height:300px;z-index:99999';
          host.appendChild(buildCharSilhouette(cid)); document.body.appendChild(host); }""", cid)
        pg.wait_for_timeout(300)
        im = _Im.open(_io.BytesIO(pg.screenshot(clip={"x": 0, "y": 0, "width": 300, "height": 300}, omit_background=True))).convert("RGBA")
        px = [q for q in im.getdata() if q[3] > 40]
        hue = sum(1 for (a, b, c, al) in px if max(a, b, c) - min(a, b, c) > 14)
        check("%s's silhouette gives away no colour (pixels with a hue)" % cid, len(px) > 500 and hue <= len(px) * 0.003, "%d of %d" % (hue, len(px)))
    ctx.close()

    # Customize: held characters play, silhouettes have no hue
    for label, w, h, dpr in [("iPhone 17 Pro Max", 440, 956, 3), ('iPad Pro 11"', 834, 1194, 2)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          store.mysteryColorsFound = { red: true, orange: true, yellow: true };
          showCustomize('character'); await wait(400);
          const opts = [...document.querySelectorAll('.screen-customize .avatarchar-option')];
          const near = o => { const b = o.getBoundingClientRect(); return b.bottom > 0 && b.top < innerHeight; };
          const held = opts.filter(o => !o.classList.contains('locked'));
          out.held = held.length; out.locked = opts.filter(o => o.classList.contains('locked') && !o.classList.contains('is-silhouette')).length;
          out.heldFlip = held.filter(o => o.classList.contains('char-flip') || o.classList.contains('char-live')).length;
          out.lockedMoving = opts.filter(o => o.classList.contains('locked') && !o.classList.contains('is-silhouette') && (o.classList.contains('char-flip') || o.classList.contains('char-live'))).length;
          for(let t = 0; t < 600; t++){ if(held.filter(near).every(o => o.querySelector('.char-flip-play img'))) break; await wait(250); }
          const playing = o => { const img = o.querySelector('.char-flip-play img'); return !!img && img.getAnimations().some(a => a.playState === 'running'); };
          out.nearHeld = held.filter(near).length; out.nearPlaying = held.filter(near).filter(playing).length;
          /* a silhouette scrolled into view plays too */
          const sil = opts.find(o => o.classList.contains('is-silhouette'));
          sil.scrollIntoView({ block: 'center', behavior: 'instant' });
          for(let t = 0; t < 400; t++){ if(sil.querySelector('.char-flip-play img')) break; await wait(250); }
          out.silPlaying = playing(sil);
          const sb = sil.getBoundingClientRect(); out.silBox = [sb.left, sb.top, sb.width, sb.height];
          out.silGlow = getComputedStyle(sil).getPropertyValue('--char-glow').trim();
          return out; }""")
        check("%s: every held character on Customize is set to play" % label, r["held"] > 0 and r["heldFlip"] == r["held"], (r["heldFlip"], r["held"]))
        check("%s: every held character on screen is playing its loop" % label, r["nearHeld"] > 0 and r["nearPlaying"] == r["nearHeld"], (r["nearPlaying"], r["nearHeld"]))
        check("%s: a locked (non-secret) character stays still" % label, r["locked"] > 0 and r["lockedMoving"] == 0, (r["lockedMoving"], r["locked"]))
        check("%s: a locked secret's silhouette plays as well" % label, r["silPlaying"] is True)
        g = r["silGlow"]
        check("%s: and its tile's glow is no colour" % label, bool(_re.match(r"#([0-9A-F]{2})\1\1|#A7AAAF", g, _re.I)) or g.upper() == "#A7AAAF", g)
        ctx.close()

    # which one is selected (build 314: "it's hard to tell which character
    # is selected because some of the characters have the glow effect on
    # them at all times") and the name editor ("a smidge cramped")
    for label, w, h, dpr in [("iPhone 17 Pro Max", 440, 956, 3), ('iPad Pro 11"', 834, 1194, 2), ("iPhone SE 1st gen", 320, 568, 2)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          showCustomize('character'); await wait(600);
          const opts = [...document.querySelectorAll('.screen-customize .avatarchar-option')];
          const ring = o => { const a = getComputedStyle(o, '::after'); return parseFloat(a.opacity) > .9 && parseFloat(a.borderTopWidth) >= 1; };
          const tick = o => { const c = o.querySelector('.avatarchar-check'); return !!c && parseFloat(getComputedStyle(c).opacity) > .9; };
          out.rings = opts.filter(ring).length; out.ticks = opts.filter(tick).length;
          out.selRing = opts.filter(o => o.classList.contains('selected')).every(o => ring(o) && tick(o));
          /* the picker's own drawing has its halo turned down */
          const held = opts.find(o => !o.classList.contains('locked') && !o.classList.contains('selected'));
          const aura = held && [...held.querySelectorAll('svg.avatarchar-svg circle')].find(c => /url\\(#(aura|halo)-/.test(c.getAttribute('fill') || ''));
          out.halo = aura ? parseFloat(aura.getAttribute('opacity') || '1') : null;
          /* the name editor - on the summary page since build 315 */
          showCustomize(); await wait(500);
          document.querySelector('.customize-namerow .profile-edit-btn').click(); await wait(300);
          const row = document.querySelector('.customize-namerow'), inp = document.querySelector('.screen-customize input.searchbox');
          const save = [...document.querySelectorAll('.screen-customize button')].find(b => b.textContent.trim() === 'Save');
          const ir = inp.getBoundingClientRect(), sr = save.getBoundingClientRect(), ics = getComputedStyle(inp);
          out.rowGone = getComputedStyle(row).display === 'none';
          out.padIn = Math.min(parseFloat(ics.paddingLeft), parseFloat(ics.paddingTop));
          out.font = parseFloat(ics.fontSize); out.fieldToBtn = Math.round(sr.top - ir.bottom);
          out.inView = ir.left >= 8 && ir.right <= innerWidth - 8 && sr.right <= innerWidth - 8;
          return out; }""")
        check("%s: exactly one character wears the selection ring and the tick" % label, r["rings"] == 1 and r["ticks"] == 1 and r["selRing"] is True, (r["rings"], r["ticks"], r["selRing"]))
        if label != "iPhone SE 1st gen":
            check("%s: a picker character's own halo is turned down (it read as selected)" % label, r["halo"] is not None and r["halo"] <= .5, r["halo"])
        check("%s: changing your name, the name row goes away while the field is open" % label, r["rowGone"] is True)
        check("%s: the name field has room inside it (>= 14px), 16px+ text, 10px+ to its buttons, clear of the screen edges" % label,
              r["padIn"] >= 14 and r["font"] >= 16 and r["fieldToBtn"] >= 10 and r["inView"], r)
        ctx.close()

    # the tab: moves at once, keeps its loop, falls back when a recording fails
    for fail in (False, True):
        init = None
        if fail:
            init = ("(()=>{ const d = HTMLImageElement.prototype.decode; HTMLImageElement.prototype.decode = function(){"
                    " if(String(this.src).indexOf('data:image/svg+xml') === 0) return Promise.reject(new Error('no')); return d.call(this); }; })();")
        ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=3, init=init)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          const tab = () => document.querySelector('#bottomtab-profile .bottomtab-icon');
          const moving = () => { const t = tab(); if(!t) return false;
            const img = t.querySelector('.char-flip-play img');
            if(img && img.getAnimations().some(a => a.playState === 'running')) return 'flip';
            const sv = t.querySelector('svg.avatarchar-svg');
            if(t.classList.contains('char-live') && sv && sv.getAnimations({ subtree: true }).some(a => a.playState === 'running')) return 'live';
            return false; };
          showHome(); await wait(1000); out.at1s = moving();
          const svg0 = tab().querySelector('svg.avatarchar-svg');
          for(let i = 0; i < 4; i++){ try{ onLiveUpdateApplied(); }catch(e){} updateHeaderTitle(); await wait(100); }
          out.kept = tab().querySelector('svg.avatarchar-svg') === svg0;
          await wait(25000); out.at25s = moving();
          return out; }""")
        tag = "with recording broken" if fail else "normally"
        check("the tab's character is moving a second after Home opens (%s)" % tag, bool(r["at1s"]), r["at1s"])
        check("and is still moving 25s later (%s)" % tag, bool(r["at25s"]), r["at25s"])
        if not fail:
            check("a live update or a save does not throw away the tab's loop", r["kept"] is True)
            check("the tab plays its recorded flip-book once the sheet is made", r["at25s"] == "flip", r["at25s"])
        ctx.close()

    # Silver, and the badges
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const rgb = s => { const m = String(s).match(/#([0-9a-f]{6})/i); if(m) return [0, 2, 4].map(i => parseInt(m[1].slice(i, i + 2), 16));
        const n = String(s).match(/rgba?\\(([^)]+)\\)/); return n ? n[1].split(',').slice(0, 3).map(Number) : null; };
      const spread = s => { const c = rgb(s); return c ? Math.max(...c) - Math.min(...c) : 999; };
      const probe = document.createElement('div'); probe.setAttribute('data-accent', 'ranger'); probe.setAttribute('data-theme', 'dark'); document.body.appendChild(probe);
      const cs = getComputedStyle(probe);
      const vals = { rank: RANK_COLOR.ranger, swatch: ACCENT_SWATCH.ranger };
      ['--theme-c1', '--theme-c2', '--theme-c3', '--bg-c1', '--bg-c2', '--bg-c3', '--rank-accent'].forEach(v => vals[v] = cs.getPropertyValue(v).trim());
      const dot = document.createElement('span'); dot.className = 'dot tier-ranger'; document.body.appendChild(dot);
      vals.dot = (getComputedStyle(dot).backgroundImage.match(/(#[0-9a-f]{6}|rgba?\\([^)]+\\))/gi) || []).join(' ');
      const med = document.createElement('span'); med.className = 'lb-rank-medal lb-rank-2'; document.documentElement.setAttribute('data-theme', 'dark'); document.body.appendChild(med);
      vals.medal = (getComputedStyle(med).backgroundImage.match(/rgba?\\([^)]+\\)/gi) || []).join(' ');
      const row = document.createElement('div'); row.className = 'rank-row rank-podium-2'; document.body.appendChild(row);
      vals.podium = getComputedStyle(row).borderTopColor;
      const em = buildRankEmblemSVG('ranger'); vals.emblem = [...em.querySelectorAll('[fill],[stop-color]')].map(n => n.getAttribute('stop-color') || n.getAttribute('fill')).filter(c => /^#[0-9a-f]{6}$/i.test(c)).join(' ');
      out.silver = {}; Object.keys(vals).forEach(k => { const cols = String(vals[k]).match(/(#[0-9a-f]{6}|rgba?\\([^)]+\\))/gi) || []; out.silver[k] = cols.length ? Math.max(...cols.map(spread)) : 999; });
      const keys = Object.keys(RANK_COLOR); out.close = [];
      keys.forEach((a, i) => keys.slice(i + 1).forEach(b => { const x = rgb(RANK_COLOR[a]), y = rgb(RANK_COLOR[b]); const d = Math.hypot(x[0] - y[0], x[1] - y[1], x[2] - y[2]); if(d < 60) out.close.push(a + '/' + b + ' ' + Math.round(d)); }));
      /* the badges */
      const units = unitsInTeachingOrder(); const u = units.find(x => !unitBadgeEarned(x));
      const unitCols = un => { const t = badgeThemeFor(un); return [t.p, t.s].filter(Boolean).map(c => String(c).toLowerCase()); };
      const leaks = (svg, un) => { const mk = svg.outerHTML.toLowerCase(); return unitCols(un).filter(c => mk.indexOf(c) >= 0 || (c.indexOf('#') === 0 && mk.indexOf(c.slice(1)) >= 0)); };
      showProfile('badges'); await wait(900);
      const tiles = [...document.querySelectorAll('.badge-tile.is-locked')];
      out.lockedTiles = tiles.length;
      out.tileLeaks = tiles.map((t, i) => leaks(t.querySelector('svg'), units.filter(x => !unitBadgeEarned(x))[i] || u)).filter(l => l.length).length;
      out.tileForm = tiles.filter(t => t.querySelectorAll('svg path').length > 12).length;
      out.tileGlowNeutral = tiles.every(t => spread(getComputedStyle(t.querySelector('.badge-tile-art')).getPropertyValue('--badge-glow').trim()) < 10);
      showUnlockDetail(badgeDetail(u)); await wait(400);
      const card = document.querySelector('.unlock-card-badge .unlock-card-art');
      out.cardLeaks = card ? leaks(card.querySelector('svg'), u) : ['missing'];
      out.cardForm = card ? card.querySelectorAll('svg path').length > 12 : false;
      out.cardGlow = card ? spread(getComputedStyle(card).getPropertyValue('--badge-glow').trim()) : 999;
      document.querySelectorAll('.invite-overlay').forEach(n => n.remove());
      /* an earned one keeps its colour */
      const e = units[0]; const was = store.unitPerfects; store.unitPerfects = Object.assign({}, was || {}); store.unitPerfects[e] = 999;
      const sv = buildUnitBadgeSVG(e, unitBadgeEarned(e) ? true : 'grey'); out.earnedColour = leaks(sv, e).length > 0;
      store.unitPerfects = was;
      return out; }""")
    bad = {k: v for k, v in r["silver"].items() if v > 8}
    check("every Silver colour is neutral (no channel more than 8 levels off another)", bad == {}, bad)
    check("the seven rank colours stay apart", r["close"] == [], r["close"])
    check("an unearned badge in the case shows no unit colour", r["lockedTiles"] > 0 and r["tileLeaks"] == 0, (r["tileLeaks"], r["lockedTiles"]))
    check("an unearned badge in the case shows its form, not an empty hole", r["tileForm"] == r["lockedTiles"], (r["tileForm"], r["lockedTiles"]))
    check("an unearned tile's light is no colour", r["tileGlowNeutral"] is True)
    check("an unearned badge's card shows its form and no unit colour", r["cardLeaks"] == [] and r["cardForm"] is True, (r["cardLeaks"], r["cardForm"]))
    check("and its card's light is no colour", r["cardGlow"] < 10, r["cardGlow"])
    check("an earned badge keeps its own colour", r["earnedColour"] is True)
    ctx.close()



def check_b314_reactions(br):
    """Build 314: "The hundo effect to the character is eh ... I was hoping
    for more of a character animation, something the character does so
    it's cooler, all the characters can have somewhat different ones, and
    the reaction is based on the grade." Every live character, every band,
    mounted the way the results screen mounts it (a live drawing in a
    .results-level-avatar) and handed to reactCharacter():
      - its own keyframes run (rx-<id>-..., written by
        tools/gen-reactions.py), for every band;
      - a 100 and a fail are different moves, and all four bands are four
        different moves (what animates where, minus the idle it had
        already);
      - no two characters' 100s are the same move with the name changed;
      - nothing a move shows leaves the drawing's frame (sampled through
        the move) - the drawing's edges clip, and a flame scaled past the
        top came out cut flat on the first draft;
      - the sign round the circle stepped back: no stars, sparkles or rain
        cloud; a pass keeps its tick and a fail its dimming;
      - with Reduce motion on, nothing moves and a 100 and a fail still land
        on two different pictures.
    Written against build 313, where every character ran the same hop, nod
    and slump: no character's own keyframes exist there and every 100 is
    the same move."""
    print("\n96. build 314: every character its own grade reaction - four bands, all different, inside its frame")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=1)
    r = pg.evaluate("""async () => {
      const out = { sig: {}, own: {}, outside: [], front: {}, rm: {}, rmMoving: [] };
      const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:40px;top:40px;z-index:99999'; document.body.appendChild(host);
      const mount = id => { const av = document.createElement('span'); av.className = 'results-level-avatar char-live'; av.appendChild(buildAvatarCharSVGSafe(id)); host.appendChild(av); return av; };
      const cls = t => t && t.getAttribute ? (t.getAttribute('class') || '').split(/\\s+/).filter(x => /^cx-/.test(x) && x !== 'cx-fx').join('.') : '';
      const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
      const shown = (el, svg) => { let o = 1; for(let e = el; e && e !== svg.parentNode; e = e.parentNode) o *= parseFloat(getComputedStyle(e).opacity); return o; };
      const chars = AVATAR_CHARACTERS.filter(c => !c.retired).map(c => c.id);
      for(const id of chars){
        const idle = mount(id); await frame();
        const base = new Set(idle.getAnimations({ subtree: true }).map(a => cls(a.effect.target) + ':' + a.animationName)); idle.remove();
        for(const band of ['perfect', 'great', 'pass', 'fail']){
          const av = mount(id);
          reactCharacter(av, band);
          await frame();
          const svg = av.querySelector('svg');
          const anims = av.getAnimations({ subtree: true }).filter(a => a.effect && svg.contains(a.effect.target));
          out.sig[id + '/' + band] = [...new Set(anims.map(a => cls(a.effect.target) + ':' + a.animationName.split('rx-' + id + '-').join('rx-*-')))].filter(k => !base.has(k)).sort();
          out.own[id + '/' + band] = anims.some(a => a.animationName.indexOf('rx-' + id + '-') === 0);
          const fr = av.querySelector(':scope > .char-emote-front'); out.front[id + '/' + band] = fr ? fr.children.length : 0;
          /* inside the frame: every part this reaction moves, that sits
             inside the frame at rest, stays inside it while it is seen */
          const all = av.getAnimations({ subtree: true });
          const movers = [...new Set(anims.filter(a => /^rx-/.test(a.animationName)).map(a => a.effect.target))];
          const R = svg.getBoundingClientRect(), tol = R.width / 34 * 1.0, LEAF = 'path, circle, ellipse, rect, polygon, polyline, line, text';
          const inside = b => b.left >= R.left - tol && b.right <= R.right + tol && b.top >= R.top - tol && b.bottom <= R.bottom + tol;
          all.forEach(a => { a.pause(); a.currentTime = 0; });
          /* a shape's real outline, through every transform on the way
             (getScreenCTM carries the CSS ones): a box would grow at the
             corners of anything turned and call it out of frame */
          const outline = k => { const m = k.getScreenCTM(); if(!m) return [];
            let ps = [];
            if(typeof k.getTotalLength === 'function' && k.tagName !== 'text'){ const L = k.getTotalLength(); for(let i = 0; i <= 32; i++){ const q = k.getPointAtLength(L * i / 32); ps.push([q.x, q.y]); } }
            else { const b = k.getBBox(); ps = [[b.x, b.y], [b.x + b.width, b.y], [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]]; }
            return ps.map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]); };
          const inPts = k => outline(k).every(([x, y]) => x >= R.left - tol && x <= R.right + tol && y >= R.top - tol && y <= R.bottom + tol);
          const drawn = k => !k.classList.contains('rxpv') && !(getComputedStyle(k).fill === 'none' && getComputedStyle(k).stroke === 'none');
          const LEAFOK = t => (t.matches(LEAF) ? [t] : [...t.querySelectorAll(LEAF)]).filter(drawn).every(inPts);
          const ok = new Set(movers.filter(t => t.classList.contains('cx-rx') || LEAFOK(t)));
          for(const t of [.25, .5, .8, 1.1, 1.4, 1.8, 2.2, 2.8, 3.6]){
            all.forEach(a => { a.currentTime = t * 1000; });
            for(const el of ok){
              /* what it DRAWS: every visible shape in it, each by its own
                 box - not the group's box, which a turn inflates at its
                 corners, and not the invisible disc (.rxpv) a prop turns
                 about. The drawing's edges feather out over 1.6 units, so
                 a shape may reach into that band; past it, it is cut. */
              const leaves = (el.matches(LEAF) ? [el] : [...el.querySelectorAll(LEAF)]).filter(k => drawn(k) && shown(k, svg) > .08);
              const bad = leaves.find(k => !inPts(k));
              if(bad) out.outside.push(id + '/' + band + ' ' + cls(el) + ' @' + t + 's');
            }
          }
          av.remove();
        }
      }
      /* Reduce motion: the final pose, still */
      theme.reduceMotion = true; applyTheme();
      for(const id of chars){
        const pose = {};
        for(const band of ['perfect', 'fail']){
          const av = mount(id); reactCharacter(av, band); await frame();
          const svg = av.querySelector('svg');
          if(av.getAnimations({ subtree: true }).some(a => a.playState === 'running' && svg.contains(a.effect && a.effect.target))) out.rmMoving.push(id + '/' + band);
          pose[band] = [...svg.querySelectorAll('[class*="cx-"]')].map(e => { const c = getComputedStyle(e); return c.transform + '|' + c.opacity; }).join(';');
          av.remove();
        }
        out.rm[id] = pose.perfect !== pose.fail;
      }
      theme.reduceMotion = false; applyTheme();
      host.remove();
      return out; }""")
    chars = sorted({k.split("/")[0] for k in r["own"]})
    bands = ["perfect", "great", "pass", "fail"]
    check("there is a reaction to check for every live character (%d)" % len(chars), len(chars) >= 30, chars)
    check("every character plays its OWN move (keyframes named for it) for every grade",
          all(r["own"].values()), [k for k, v in r["own"].items() if not v][:8])
    check("for every character a 100 and a fail are different moves, and neither is empty",
          all(r["sig"][c + "/perfect"] and r["sig"][c + "/fail"] and r["sig"][c + "/perfect"] != r["sig"][c + "/fail"] for c in chars),
          [c for c in chars if not (r["sig"][c + "/perfect"] and r["sig"][c + "/fail"] and r["sig"][c + "/perfect"] != r["sig"][c + "/fail"])][:8])
    check("for every character the four grades are four different moves",
          all(len({tuple(r["sig"][c + "/" + b]) for b in bands}) == 4 for c in chars),
          [c for c in chars if len({tuple(r["sig"][c + "/" + b]) for b in bands}) != 4][:8])
    perf = {}
    for c in chars:
        perf.setdefault(tuple(r["sig"][c + "/perfect"]), []).append(c)
    check("no two characters' 100s are the same move with the name changed", all(len(v) == 1 for v in perf.values()),
          [v for v in perf.values() if len(v) > 1][:4])
    check("nothing a move shows leaves the drawing's frame, all the way through the move", r["outside"] == [],
          sorted({o.split(" @")[0] for o in r["outside"]})[:40])
    check("the sign round the circle steps back: no stars on a 100, no sparkles on a 90, no rain cloud on a fail; a pass keeps its tick",
          all(r["front"][c + "/perfect"] == 0 and r["front"][c + "/great"] == 0 and r["front"][c + "/pass"] == 1 and r["front"][c + "/fail"] == 1 for c in chars),
          {c: [r["front"][c + "/" + b] for b in bands] for c in chars[:3]})
    check("with Reduce motion on, nothing in the drawing moves", r["rmMoving"] == [], r["rmMoving"][:6])
    check("with Reduce motion on, a 100 and a fail still land on two different pictures", all(r["rm"].values()),
          [c for c, v in r["rm"].items() if not v][:8])
    ctx.close()



B314_LIGHT = ['cx-fx-umaura', 'cx-fx-umaura2', 'cx-fx-wisps', 'cx-fx-umcglow', 'cx-fx-umcglint', 'cx-fx-umrim', 'cx-fx-sgsparks', 'cx-fx-sglight',
              'cx-fx-sgsurgew', 'cx-fx-sgsurgeb', 'cx-fx-sgaurora', 'cx-fx-gnatm', 'cx-fx-gnleak', 'cx-fx-gnerupt', 'cx-fx-gnseam', 'cx-fx-starfield', 'cx-fx-sparkles']
# Orion's head group draws its whole cloak as well; its head is the hood,
# which ends here.
B314_HEAD_FLOOR = {"astronaut": 26}


def _b314_size(pg, cid, head):
    """One still drawing at 10px a unit on a transparent page, scene, halo
    and light left out, nothing else of the page showing. Returns the ink
    box (x, y, w, h in the drawing's units) and the ink area (square units)
    of the head (head=True) or the whole figure."""
    import io as _io
    from PIL import Image as _Im
    pg.evaluate("""([cid, head, light]) => { document.getElementById('b314sz')?.remove();
      const host = document.createElement('div'); host.id = 'b314sz'; host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;z-index:99999';
      const s = buildAvatarCharSVGSafe(cid);
      s.style.cssText = 'width:340px;height:340px;-webkit-mask-image:none;mask-image:none;filter:none';
      host.appendChild(s); document.body.appendChild(host);
      document.querySelectorAll('body > *:not(#b314sz)').forEach(e => { if(e.style) e.style.visibility = 'hidden'; });
      s.querySelectorAll('.cx-bg').forEach(n => n.remove());
      s.querySelectorAll('circle').forEach(n => { if(/url\\(#(aura|halo)-/.test(n.getAttribute('fill') || '')) n.remove(); });
      light.forEach(c => s.querySelectorAll('.' + c).forEach(n => n.remove()));
      if(head){
        s.querySelectorAll('*').forEach(n => n.style && (n.style.visibility = 'hidden'));
        const h = s.querySelector('.cx-head');
        if(h){ h.style.visibility = 'visible'; h.querySelectorAll('*').forEach(n => n.style && (n.style.visibility = 'visible')); }
      } }""", [cid, head, B314_LIGHT])
    png = pg.screenshot(clip={"x": 0, "y": 0, "width": 340, "height": 340}, omit_background=True)
    A = _Im.open(_io.BytesIO(png)).convert("RGBA").getchannel("A").point(lambda v: 255 if v > 110 else 0)
    if head and cid in B314_HEAD_FLOOR:
        A = A.crop((0, 0, 340, int((B314_HEAD_FLOOR[cid] - 3) * 10))).crop((0, 0, 340, 340))
    bb = A.getbbox()
    if not bb:
        return None
    area = sum(1 for v in A.getdata() if v) / 100.0
    return {"x": bb[0] / 10 + 3, "y": bb[1] / 10 + 3, "w": (bb[2] - bb[0]) / 10, "h": (bb[3] - bb[1]) / 10, "area": area}


def check_b314_sizes(br):
    """Build 314: "The masked one character looks bigger than the rest when
    looking at them all. Ensure all the characters are the same size, some
    of the secret flare characters had the problem."
    What reads as a character's size is its head - every one of them is a
    bust whose shoulders run off the bottom of the frame, so the whole
    figure's box is nearly the same for all thirty and says nothing (it is
    checked here too, to a tight tolerance). The head is measured as the
    ink it covers - its silhouette, hats, hoods and hair included, light and
    glow left out - which is what made the Masked One (solid mask, spiked
    hood: 38% over the median at build 313), the Hive (31%), Umbra (20%)
    and Void (16%) read as big. Then, in each place a character is drawn -
    the Customize grid, the sign-up picker, the Profile card and a
    leaderboard row - every character's drawing is the same size in its
    tile, so what holds for the drawing holds there.
    Fails on build 313 for the Masked One, the Hive, Umbra and Void."""
    import statistics as _st
    print("\n97. build 314: every character the same size - the head no more than 15% over the set's median, in every place it is drawn")
    ctx, pg = booted(br, 400, 400, seed=USED_ACCOUNT, dpr=1)
    pg.evaluate(B314_TRANSPARENT)
    ids = pg.evaluate("()=>AVATAR_CHARACTERS.filter(c => !c.retired).map(c => c.id)")
    head = {c: _b314_size(pg, c, True) for c in ids}
    ctx.close()
    med = _st.median(v["area"] for v in head.values())
    over = {c: round(100 * (v["area"] / med - 1)) for c, v in head.items() if v["area"] > med * 1.15}
    check("no character's head covers more than 15%% more than the set's median (%.0f sq units)" % med, not over, over)
    mw, mh = _st.median(v["w"] for v in head.values()), _st.median(v["h"] for v in head.values())
    small = {c: (round(100 * (v["w"] / mw - 1)), round(100 * (v["h"] / mh - 1))) for c, v in head.items() if v["w"] < mw * .85 and v["h"] < mh * .85}
    check("and no character's head is more than 15% narrower AND shorter than the median", not small, small)

    # the same size in every place a character is drawn: every drawing in
    # a context renders at one size, with nothing scaling one character
    import re as _re
    vr = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-vroom.py")).read()
    fake = _re.search(r'FAKE_FIRESTORE = """(.*?)"""', vr, _re.S).group(1)
    keep = "window.addEventListener('DOMContentLoaded', function(){ try{ window.__osr = onSnapshotResilient; }catch(e){} });"
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=1, init=fake + "\n" + keep)
    r = pg.evaluate("""async (ids) => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      /* the drawing's laid-out size, not its box on screen: the picked tile
         grows 4% on purpose and that is not the drawing's size */
      const sz = svg => svg ? +parseFloat(getComputedStyle(svg).width).toFixed(1) : 0;
      const one = (list) => { const v = list.filter(x => x[1] > 0); const s = new Set(v.map(x => x[1])); return { n: v.length, sizes: [...s], who: v }; };
      /* Customize, everything held */
      store.legacyChars = ids.slice(); showCustomize('character'); await wait(900);
      out.customize = one([...document.querySelectorAll('.screen-customize .avatarchar-option')].map(o => [o.dataset.char || '', sz(o.querySelector('svg.avatarchar-svg') || o.querySelector('svg'))]));
      /* the sign-up picker */
      try{ showWelcomeCharacterPrompt(); await wait(700);
        out.signup = one([...document.querySelectorAll('.avatarchar-option')].map(o => [o.dataset.char || '', sz(o.querySelector('svg'))])); }catch(e){ out.signup = { n: 0, err: String(e) }; }
      /* the Profile card, each character in turn */
      const prof = [];
      for(const id of ids){ store.avatarChar = id; showProfile(); await wait(120);
        const sv = document.querySelector('.profile-hero svg.avatarchar-svg, .profile-avatar svg.avatarchar-svg, .profilecard svg.avatarchar-svg') || document.querySelector('#stage svg.avatarchar-svg');
        prof.push([id, sv ? sz(sv) : 0]); }
      out.profile = one(prof);
      /* a leaderboard row, each character on one */
      try{ __useFake(); if(window.__osr) onSnapshotResilient = window.__osr; }catch(e){}
      for(let i = 0; i < ids.length; i++) await fbDb.collection('leaderboard').doc('s' + i).set({ pub: 's' + i, firstName: 'P' + i, avatarChar: ids[i], accent: 'ink', level: 60 - i, badges: 3, hundos: 20, xp: 50000 - i * 900, tests: 30, week: weekKeyNow(), weekPoints: 900 - i * 10, lastModified: Date.now(), seenAt: Date.now() });
      showRankings(); for(let t = 0; t < 60 && document.querySelectorAll('.rank-row .rank-avatar svg').length < ids.length; t++) await wait(200);
      out.board = one([...document.querySelectorAll('.rank-row')].filter(r => r.dataset.av).map(r => [r.dataset.av, sz(r.querySelector('.rank-avatar svg.avatarchar-svg') || r.querySelector('.rank-avatar svg'))]));
      return out; }""", ids)
    for k, label in (("customize", "the Customize grid"), ("signup", "the sign-up picker"), ("profile", "the Profile card"), ("board", "a leaderboard row")):
        v = r.get(k) or {}
        sizes = v.get("sizes") or []
        check("%s: every character's drawing is the same size (%d drawn)" % (label, v.get("n", 0)),
              v.get("n", 0) >= (4 if k == "signup" else 20) and len(sizes) == 1, {"sizes": sizes, "err": v.get("err")})
    ctx.close()

def check_b313_flares(br):
    """Build 313, the secret flares: "None of my secret flares are lit up";
    "when tapping the tiny secret flares, sometimes they and sometimes the
    text box won't show up ... ensure it properly and smoothly follows the
    selected flare"; "there will only be 3 at first, the 4th and 5th flare
    will appear once void is unlocked"; "ensure the flares in the middle are
    moving at a faster pace"; "the umbra missing flare did not change at
    all"; a sixth flare, on the planet, found at level 78-80, handing over
    the last secret character; names, not colours; locked secret characters
    as silhouettes; a banner for each. Written against build 312, where the
    found flares computed white, the tooltip stayed where it was opened,
    all five dots always showed, and none of the rest existed."""
    print("\n91. build 313: secret flares lit, tappable and followed; three then five then six; the sixth flare; names; silhouettes; banners")
    FOUND = lambda *ks: "{" + ",".join('"%s":%s' % (k, "true" if k in ks else "false") for k in ["red", "orange", "yellow", "violet", "white", "core"]) + "}"
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async (F) => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          try{
          document.querySelectorAll('.app-banner, #save-code').forEach(e => e.remove());
          store.unlocksShown = store.unlocksShown || { chars: [], banners: [] };
          const shownNow = () => { try{ ensureUnlocksShown(); markUnlocksShown(announceableHeldCharacters(), BANNERS.filter(b => bannerEarned(b.id)).map(b => b.id)); }catch(e){}
            store.flareHintsShown = ['umbra', 'singularity', 'genesis']; };
          const home = async (found) => { store.mysteryColorsFound = JSON.parse(found); shownNow(); showHome(); await wait(1500);
            document.querySelectorAll('.rs-spot, .app-banner').forEach(e => e.remove()); };
          const hex = c => { const n = parseInt(c.slice(1), 16); return 'rgb(' + (n >> 16) + ', ' + ((n >> 8) & 255) + ', ' + (n & 255) + ')'; };
          /* 1. lit: a found flare paints in its own colour */
          await home(F.void);
          const dots = [...document.querySelectorAll('.panel.home .cosmic-orbit-dot')];
          out.count3 = 0; out.countVoid = dots.length;
          out.lit = dots.filter(d => (store.mysteryColorsFound || {})[d.dataset.flare || ''] || /found/.test(d.getAttribute('class') || '')).map(d => {
            const key = d.dataset.flare || ['red', 'orange', 'yellow'][dots.indexOf(d)];
            const b = d.querySelector('.cof-body'); const cs = getComputedStyle(b || d);
            return { key, ok: (cs.backgroundImage + '|' + cs.fill).indexOf(hex(MYSTERY_COLOR[key] || '#000000')) >= 0 };
          });
          /* the next one wears its colour - Umbra's, once Void is held */
          const vio = document.querySelector('.panel.home [data-flare="violet"]');
          /* build 314: marked, but in plain light - never its colour ("the secret
             flares you haven't got, you shouldn't be able to see their colors") */
          out.nextTinted = !!(vio && vio.classList.contains('is-next') && parseFloat(getComputedStyle(vio.querySelector('.cof-tint')).opacity) > .2
            && getComputedStyle(vio).getPropertyValue('--fc').trim().toUpperCase() !== MYSTERY_COLOR.violet.toUpperCase());
          /* 2. three, then five, then six */
          await home(F.none); out.count3 = document.querySelectorAll('.panel.home .cosmic-orbit-dot').length;
          await home(F.five); out.count6 = document.querySelectorAll('.panel.home .cosmic-orbit-dot').length;
          out.coreOnPlanet = !!document.querySelector('.panel.home .cosmic-core-orbit [data-flare="core"]');
          /* 3. the inner ring is well over twice as quick */
          const dur = el => el ? parseFloat(getComputedStyle(el).animationDuration.split(',').pop()) : 0;
          out.spin = [dur(document.querySelector('.cosmic-hero-orbitlayer:not(.cosmic-hero-orbitlayer-inner)')), dur(document.querySelector('.cosmic-hero-orbitlayer-inner'))];
          /* 4. names, not colours */
          out.names = MYSTERY_ORDER.map(k => MYSTERY_NAME[k]);
          out.order = MYSTERY_ORDER.slice(); out.coreWin = (typeof FLARE_WINDOWS !== 'undefined') ? FLARE_WINDOWS.core : null;
          /* 5. the sixth: next after the fifth, at level 78-80 */
          const realLevel = levelOf;
          store.mysteryColorsFound = JSON.parse(F.five); store.flareNextTestAt = 0;
          out.nextAfterFive = nextNeededMysteryColor();
          levelOf = () => 77; out.gate77 = mysteryGateMet('core');
          levelOf = () => 80; out.gate80 = mysteryGateMet('core');
          levelOf = realLevel;
          out.genesisLockedBefore = isLockedCharacter('genesis');
          store.mysteryColorsFound = JSON.parse(F.all); out.genesisHeld = !isLockedCharacter('genesis');
          out.items = rsUnlockItems({ badges: [], retroBadges: [], colors: [], characters: [], banners: ['flare_genesis'], justBeatSpeed: null, units: [], flare: 'core', flareAll: false, flareCount: 6 })
            .map(i => i.kind + ':' + (i.flare || i.character || i.banner || '') + ':' + (i.name || ''));
          /* 6. silhouettes: with only Void held, the other three are black cut-outs in Customize */
          store.mysteryColorsFound = JSON.parse(F.void); showCustomize('character'); await wait(900);
          const opt = id => [...document.querySelectorAll('.avatarchar-option')].find(o => o.title === (AVATAR_DISPLAY_NAME[id] || id));
          out.sil = ['umbra', 'singularity', 'genesis'].map(id => { const o = opt(id); if(!o) return 'missing';
            const p = o.querySelector('.char-sil-body .cx-head :is(path, circle, ellipse):not([fill="none"])');
            return o.classList.contains('is-silhouette') && p ? getComputedStyle(p).fill : 'not-silhouette'; });
          out.voidShown = (() => { const o = opt('voidwalker'); return !!o && !o.classList.contains('is-silhouette'); })();
          /* build 314: the silhouette is a flip-book on its tile (char-flip),
             or live if its sheet cannot be made */
          out.silLive = !!document.querySelector('.avatarchar-option.is-silhouette:is(.char-flip, .char-live), .avatarchar-option.is-silhouette .char-sil.char-live');
          /* 7. banners: one per secret character, held with it */
          out.banners = ['flare_void', 'flare_umbra', 'flare_horizon', 'flare_genesis'].map(id => !!bannerDef(id) && typeof BANNER_ART[id] === 'function');
          out.bannerHeld = [bannerEarned('flare_void'), bannerEarned('flare_umbra')];
          showCustomize('banner'); await wait(900);   /* the banners' own page since build 315 */
          out.secretLocked = !!document.querySelector('.banner-opt.locked.is-secret[data-banner="flare_umbra"]');
          /* an account already holding Void is handed its banner on Home */
          shownNow(); store.unlocksShown.banners = store.unlocksShown.banners.filter(x => x !== 'flare_void');
          showHome(); await wait(4200);
          const spot = document.querySelector('.rs-spot'); out.homeBanner = spot ? spot.textContent : '';
          }catch(e){ out.err = String(e && e.stack || e); }
          return out; }""", {"none": FOUND(), "void": FOUND("red", "orange", "yellow"),
                            "five": FOUND("red", "orange", "yellow", "violet", "white"),
                            "all": FOUND("red", "orange", "yellow", "violet", "white", "core")})
        check(f"{label}: no exception", "err" not in r, r.get("err"))
        lit = r.get("lit") or []
        check(f"{label}: every found flare on Home is lit in its own colour (they computed white)",
              len(lit) == 3 and all(x["ok"] for x in lit), lit)
        check(f"{label}: the flare being hunted next is marked (once Void is held) - in plain light, not its colour (build 314)", r.get("nextTinted") is True, r.get("nextTinted"))
        check(f"{label}: three flares before Void, five with it, six once the fifth is found",
              (r.get("count3"), r.get("countVoid"), r.get("count6")) == (3, 5, 6), (r.get("count3"), r.get("countVoid"), r.get("count6")))
        check(f"{label}: the sixth flare is on the planet", r.get("coreOnPlanet") is True)
        sp = r.get("spin") or [0, 0]
        check(f"{label}: the inner ring turns at least twice as fast as the outer", sp[1] > 0 and sp[0] >= 2 * sp[1], sp)
        nm = r.get("names") or []
        check(f"{label}: every flare has a name of its own, not a colour",
              len(nm) == 6 and len(set(nm)) == 6 and not any(n.lower() in ("red", "orange", "yellow", "violet", "white") for n in nm), nm)
        check(f"{label}: the sixth flare comes after the fifth, at level 78-80",
              r.get("order", [])[-1:] == ["core"] and r.get("coreWin") == [78, 80] and r.get("nextAfterFive") == "core"
              and r.get("gate77") is False and r.get("gate80") is True, [r.get("order"), r.get("coreWin"), r.get("nextAfterFive"), r.get("gate77"), r.get("gate80")])
        check(f"{label}: it hands over Genesis", r.get("genesisLockedBefore") is True and r.get("genesisHeld") is True)
        check(f"{label}: the results name the flare, then the character, then its banner",
              (r.get("items") or [])[-3:] == ["flare:core:Worldheart", "character:genesis:Genesis", "banner:flare_genesis:Genesis"], r.get("items"))
        check(f"{label}: a locked secret character is a black cut-out in Customize, the held one is not",
              r.get("sil") == ["rgb(5, 6, 10)"] * 3 and r.get("voidShown") is True and r.get("silLive") is True, [r.get("sil"), r.get("voidShown"), r.get("silLive")])
        check(f"{label}: a banner for each secret character, held with it, dark until then",
              r.get("banners") == [True] * 4 and r.get("bannerHeld") == [True, False] and r.get("secretLocked") is True, [r.get("banners"), r.get("bannerHeld"), r.get("secretLocked")])
        check(f"{label}: an account already holding Void is handed its banner on Home",
              "Void" in (r.get("homeBanner") or "") and "Banner" in (r.get("homeBanner") or ""), r.get("homeBanner"))
        ctx.close()

    # Real taps, at each flare's live position, and the tooltip following it.
    # (The sync-code notice sits along the top, where the red flare can be.)
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init="try{localStorage.setItem('class26e.savecode.asked','1');}catch(e){}")
    pg.evaluate("""()=>{ document.querySelectorAll('.app-banner, #save-code').forEach(e => e.remove());
      store.mysteryColorsFound = { red: true, orange: true, yellow: true, violet: true, white: true };
      try{ ensureUnlocksShown(); markUnlocksShown(announceableHeldCharacters(), BANNERS.filter(b => bannerEarned(b.id)).map(b => b.id)); }catch(e){}
      store.flareHintsShown = ['umbra', 'singularity', 'genesis']; showHome(); }""")
    pg.wait_for_timeout(2500)
    pg.evaluate("()=>document.querySelectorAll('.rs-spot').forEach(e => e.remove())")
    keys = ["red", "orange", "yellow", "violet", "white"]
    ok, missed = 0, []
    for i in range(15):
        k = keys[i % 5]
        # Build 313's second pass: a flare under a Liquid Glass bubble is
        # meant to give the tap to the bubble (section 92), so wait until
        # this one is in the clear before tapping it.
        pos = None
        for _ in range(20):
            pos = pg.evaluate("""(k)=>{ const d = document.querySelector('.panel.home [data-flare="' + k + '"]') || [...document.querySelectorAll('.panel.home .cosmic-orbit-dot')][['red','orange','yellow','violet','white'].indexOf(k)];
              if(!d) return null; const r = d.getBoundingClientRect(); const x = r.left + r.width / 2, y = r.top + r.height / 2;
              const top = document.elementFromPoint(x, y); return [x, y, !!(top && top.closest && top.closest('.cosmic-icon-badge'))]; }""", k)
            if not pos or not pos[2]:
                break
            pg.wait_for_timeout(400)
        if not pos:
            missed.append((k, "no dot")); continue
        pg.evaluate("()=>{ document.querySelectorAll('.app-banner, #save-code, .daily-alert, .rs-spot, #contextual-info-popup').forEach(e => e.remove()); }")
        pg.mouse.click(pos[0], pos[1])
        pg.wait_for_timeout(150)
        t = pg.evaluate("()=>{ const p = document.getElementById('contextual-info-popup'); return p ? p.textContent : ''; }")
        nm = pg.evaluate("(k)=>MYSTERY_NAME[k]", k)
        if nm in t:
            ok += 1
        else:
            missed.append((k, t[:40]))
        pg.wait_for_timeout(250)
    check("every real tap on a found flare opens its tooltip, naming the flare", ok == 15, missed)
    pos = pg.evaluate("""()=>{ const d = document.querySelector('.panel.home [data-flare="violet"]') || [...document.querySelectorAll('.panel.home .cosmic-orbit-dot')][3];
      const r = d.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }""")
    pg.mouse.click(pos[0], pos[1])
    f = pg.evaluate("""async ()=>{ const d = document.querySelector('.panel.home [data-flare="violet"]') || [...document.querySelectorAll('.panel.home .cosmic-orbit-dot')][3];
      const out = []; const t0 = performance.now();
      while(performance.now() - t0 < 1200){ await new Promise(r => requestAnimationFrame(r));
        const m = document.getElementById('contextual-info-line-dot'); if(!m) continue;
        const a = d.getBoundingClientRect(), b = m.getBoundingClientRect();
        out.push([Math.hypot(a.left + a.width / 2 - b.left - b.width / 2, a.top + a.height / 2 - b.top - b.height / 2), a.left, a.top]); }
      return out; }""")
    moved = max(abs(f[-1][1] - f[0][1]), abs(f[-1][2] - f[0][2])) if f else 0
    worst = max(x[0] for x in f) if f else 99
    check("the tooltip's marker stays on the flare as it moves (within 2px over 1.2s)", len(f) > 20 and moved > 3 and worst <= 2, ("frames", len(f), "moved", round(moved, 1), "worst", round(worst, 1)))
    ctx.close()

    # The characters and the scenes.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
      const host = document.createElement('div'); host.className = 'char-live'; host.style.cssText = 'position:fixed;left:0;top:0;width:80px;height:80px';
      document.body.appendChild(host);
      const anim = (id, sel) => { host.innerHTML = ''; const s = buildAvatarCharSVG(id); if(!s) return 'nodrawing'; host.appendChild(s);
        const e = s.querySelector(sel); return e ? getComputedStyle(e).animationName : 'missing'; };
      out.genesis = [anim('genesis', '.cx-fx-gnspin'), anim('genesis', '.cx-fx-gnmoonfront'), anim('genesis', '.cx-eyes')];
      out.umbraMoon = [anim('umbra', '.cx-fx-umdark'), anim('umbra', '.cx-fx-umlit')];
      out.horizonSurge = [anim('singularity', '.cx-fx-sgsurgew'), anim('singularity', '.cx-fx-sgsurgeb')];
      host.remove();
      store.mysteryColorsFound = { red: true, orange: true, yellow: true, violet: true, white: true, core: true };
      out.scenes = [];
      for(const c of ['violet', 'white', 'core']){
        const h = playFlareFoundScene(c, false, () => {}); await wait(400);
        const o = document.querySelector('.ff-scene'); out.scenes.push(o ? o.className.split(' ').filter(x => /^xs-(umbra|horizon|genesis)$/.test(x)).join('') : 'none');
        h && h.stop && h.stop(); await wait(100);
      }
      }catch(e){ out.err = String(e && e.stack || e); }
      return out; }""")
    check("no exception in the character and scene checks", "err" not in r, r.get("err"))
    g = r.get("genesis") or []
    check("Genesis is drawn, its moon orbits and passes behind, and it blinks",
          g[:2] == ["cx-gn-spin", "cx-gn-front"] and "cx-blink" in (g[2] if len(g) > 2 else ""), g)
    check("Umbra's moon goes through its phases", r.get("umbraMoon") == ["cx-um-dark", "cx-um-lit"], r.get("umbraMoon"))
    check("Horizon's hair surges white and deep blue", r.get("horizonSurge") == ["cx-sg-surgew", "cx-sg-surgeb"], r.get("horizonSurge"))
    check("Umbra, Horizon and Genesis each have a scene of their own", r.get("scenes") == ["xs-umbra", "xs-horizon", "xs-genesis"], r.get("scenes"))
    ctx.close()


def check_b313_pause(br):
    """Build 313: "When paused, the chat button needs to be put in the right
    not the same spot, that open space on the right looks weird." Pause hides
    itself on its own screen, and the chat button stayed where it had sat
    BESIDE Pause - leaving a Pause-sized hole at the end of the row. It now
    takes Pause's spot: the same line, right-aligned to Pause's right edge.
    Fails on 312, where it is one gap to Pause's left."""
    print("\n313p. paused, the chat button takes Pause's place")
    for label, w, h in (("phone", 440, 956), ("small phone", 375, 667), ("phone sideways", 956, 440), ("iPad", 834, 1194)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        got = pg.evaluate("""async ()=>{
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const U = topicsIn(QUESTIONS)[0]; const ix = QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===U);
          cfg.mode='drill'; cfg.units=[U]; cfg.source='all'; runMode='drill'; beginRun(ix, null);
          for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(150);
          await wait(900);
          const R = e => { const b = e.getBoundingClientRect(); return { l: b.left, r: b.right, cy: b.top + b.height / 2, w: b.width }; };
          const pause = R(document.getElementById('pausebtn'));
          const dockQ = R(document.getElementById('chatdock-btn'));
          document.getElementById('pausebtn').click(); await wait(700);
          const dockP = R(document.getElementById('chatdock-btn'));
          const panel = !!document.querySelector('#stage .pausepanel.is-pause');
          document.getElementById('resumebtn')?.click(); await wait(600);
          const dockR = R(document.getElementById('chatdock-btn'));
          return { pause, dockQ, dockP, dockR, panel, vw: innerWidth }; }""")
        p, q, d, r = got["pause"], got["dockQ"], got["dockP"], got["dockR"]
        check("%s: on a question the chat button sits left of Pause" % label, q["r"] <= p["l"] + 1, got)
        check("%s: paused, it moves to Pause's right edge, on the same line" % label,
              got["panel"] and abs(d["r"] - p["r"]) <= 2 and abs(d["cy"] - p["cy"]) <= 2, {"pause": p, "paused": d})
        check("%s: and back beside Pause on Resume" % label, abs(r["r"] - q["r"]) <= 2 and abs(r["cy"] - q["cy"]) <= 2, {"before": q, "after": r})
        ctx.close()


GLASS_SEEK = """(want)=>{
  /* Turn the inner ring (its animation re-timed by a negative delay) until
     the violet flare's centre is under a bubble (want 'under') or well
     clear of every bubble (want 'clear'), then freeze everything there. */
  const wrap = document.querySelector('.panel.home .cosmic-hero-wrap');
  const inner = wrap.querySelector('.cosmic-hero-orbitlayer-inner');
  const flare = inner.querySelector('[data-flare="violet"]') || inner.querySelectorAll('.cosmic-orbit-dot')[1] || inner.querySelector('.cosmic-orbit-dot');
  const bubbles = [...wrap.querySelectorAll(':scope > .cosmic-icon-badge')];
  const dur = parseFloat(getComputedStyle(inner).animationDuration.split(',').pop()) || 60;
  const at = () => { const f = flare.getBoundingClientRect(); return [f.left + f.width / 2, f.top + f.height / 2]; };
  for(let s = 0; s < dur; s += .1){
    inner.style.animationDelay = '0s, -' + s.toFixed(2) + 's';
    const [fx, fy] = at();
    const near = bubbles.map(b => { const r = b.getBoundingClientRect(); return { b, d: Math.hypot(fx - r.left - r.width / 2, fy - r.top - r.height / 2) - r.width / 2 }; })
      .sort((a, c) => a.d - c.d)[0];
    if((want === 'under' && near.d < -8) || (want === 'clear' && near.d > 34)){
      wrap.querySelectorAll('*').forEach(e => { e.style.animationPlayState = 'paused'; });
      inner.style.animationPlayState = 'paused';
      return { x: fx, y: fy, tier: near.b.dataset.rankTier || '', d: Math.round(near.d) };
    }
  }
  return null; }"""


def check_b313_flares_glass(br):
    """Build 313, second pass: "Ensure those go under the flare bubble when
    passing through, that would look so so sick with the Liquid Glass flare
    bubbles." The first pass put the secret flares ABOVE the rank bubbles;
    they paint below them now and are seen through the glass. A flare under
    a bubble must not take the bubble's tap; a flare in the clear still
    names itself. Written against the first pass (flares on top), where the
    paint-order and the under-a-bubble tap both fail; against 312 the
    flare in the clear says nothing about which flare it is."""
    print("\n93. build 313: the secret flares pass under the Liquid Glass bubbles (centred on their rings); taps stay right")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init="try{localStorage.setItem('class26e.savecode.asked','1');}catch(e){}")
        pg.evaluate("""()=>{ document.querySelectorAll('.app-banner, #save-code').forEach(e => e.remove());
          store.mysteryColorsFound = { red: true, orange: true, yellow: true, violet: true, white: false };
          try{ ensureUnlocksShown(); markUnlocksShown(announceableHeldCharacters(), BANNERS.filter(b => bannerEarned(b.id)).map(b => b.id)); }catch(e){}
          store.flareHintsShown = ['umbra', 'singularity', 'genesis']; showHome(); }""")
        pg.wait_for_timeout(2600)
        pg.evaluate("()=>document.querySelectorAll('.rs-spot, .app-banner, #save-code, .daily-alert').forEach(e => e.remove())")
        under = pg.evaluate(GLASS_SEEK, "under")
        pg.wait_for_timeout(200)
        order = pg.evaluate("""(p)=>{ if(!p) return null; const els = document.elementsFromPoint(p.x, p.y);
          const bi = els.findIndex(e => e.classList && e.classList.contains('cosmic-icon-badge'));
          const fi = els.findIndex(e => (e.classList && e.classList.contains('cosmic-orbit-dot')) || (e.getAttribute && /cosmic-orbit-dot/.test(e.getAttribute('class') || '')));
          return { bubble: bi, flare: fi }; }""", under)
        check(f"{label}: a flare under a bubble paints beneath it (the glass is on top)",
              bool(order) and order["bubble"] >= 0 and order["flare"] >= 0 and order["bubble"] < order["flare"], [under, order])
        if under:
            pg.mouse.click(under["x"], under["y"])
            pg.wait_for_timeout(200)
        t = pg.evaluate("()=>{ const p = document.getElementById('contextual-info-popup'); return p ? p.textContent : ''; }")
        rank = pg.evaluate("(t)=>RANK_DISPLAY_NAME[t] || ''", (under or {}).get("tier", ""))
        check(f"{label}: a tap on a bubble with a flare under it opens the bubble's rank, not the flare",
              bool(rank) and t.startswith(rank + " rank"), [rank, t[:60]])
        pg.evaluate("()=>{ document.getElementById('contextual-info-popup')?.remove(); document.querySelectorAll('.panel.home .cosmic-hero-wrap *').forEach(e => { e.style.animationPlayState = ''; }); }")
        clear = pg.evaluate(GLASS_SEEK, "clear")
        pg.wait_for_timeout(200)
        if clear:
            pg.mouse.click(clear["x"], clear["y"])
            pg.wait_for_timeout(200)
        t2 = pg.evaluate("()=>{ const p = document.getElementById('contextual-info-popup'); return p ? p.textContent : ''; }")
        nm = pg.evaluate("()=>MYSTERY_NAME.violet")
        check(f"{label}: the same flare in the clear still takes the tap and names itself", bool(clear) and nm in t2, [clear, t2[:60]])
        # THE BUBBLES SIT ON THE RINGS, BY THEIR CENTRES - and so a flare on
        # a bubble's ring goes straight under its middle, not past its rim.
        geo = pg.evaluate("""()=>{
          const wrap = document.querySelector('.panel.home .cosmic-hero-wrap');
          wrap.querySelectorAll('*').forEach(e => { e.style.animationPlayState = ''; });
          const bubs = [...wrap.querySelectorAll(':scope > .cosmic-icon-badge')];
          bubs.forEach(b => b.style.animation = 'none');
          const W = wrap.getBoundingClientRect(), u = W.width / 360;
          const cx = W.left + W.width / 2, cy = W.top + W.height * 162 / 342;
          const outer = typeof HOME_OUTER_R === 'number' ? HOME_OUTER_R : 152;
          const ctr = b => { const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
          const off = bubs.map(b => { const [x, y] = ctr(b); const d = Math.hypot(x - cx, y - cy) / u;
            return +Math.min(Math.abs(d - 108), Math.abs(d - outer)) * u; });
          /* one revolution of the inner ring: the closest any inner flare comes to any bubble's centre */
          const inner = wrap.querySelector('.cosmic-hero-orbitlayer-inner');
          const flares = [...inner.querySelectorAll('.cosmic-orbit-dot')];
          const dur = parseFloat(getComputedStyle(inner).animationDuration.split(',').pop()) || 60;
          let best = 1e9;
          for(let t = 0; t < dur; t += dur / 1440){
            inner.style.animationDelay = '0s, -' + t.toFixed(3) + 's';
            flares.forEach(f => { const r = f.getBoundingClientRect(); const fx = r.left + r.width / 2, fy = r.top + r.height / 2;
              bubs.forEach(b => { const [x, y] = ctr(b); best = Math.min(best, Math.hypot(fx - x, fy - y)); }); });
          }
          inner.style.animationDelay = ''; bubs.forEach(b => b.style.animation = '');
          return { off: off.map(v => +v.toFixed(2)), closest: +best.toFixed(2) }; }""")
        check(f"{label}: every bubble's centre is on its ring (within 1.5px)", bool(geo["off"]) and max(geo["off"]) <= 1.5, geo["off"])
        check(f"{label}: a flare passes within 3px of a bubble's centre - through it, not past the rim", geo["closest"] <= 3, geo["closest"])
        # The glass is the glass it was: nothing about a bubble with nothing
        # behind it changed (its fill, blur and rim are 312's).
        g = pg.evaluate("""()=>{ const u = document.querySelector('.panel.home .cosmic-icon-badge.cosmic-badge-rank:not(.cosmic-badge-lit)');
          if(!u) return null; const s = getComputedStyle(u); return [s.backgroundColor, s.backdropFilter || s.webkitBackdropFilter, s.borderTopColor, s.opacity]; }""")
        check(f"{label}: an unreached bubble's glass is unchanged (fill, blur, rim, opacity)",
              g == ["rgba(255, 255, 255, 0.09)", "blur(6px) saturate(1.4)", "rgba(255, 255, 255, 0.24)", "1"], g)
        ctx.close()


FX_RUN = """const wait = ms => new Promise(r => setTimeout(r, ms));
  window.__fxAt = 0;
  if(typeof playHundoFx === 'function'){ const real = playHundoFx; window.playHundoFx = function(a, b){ window.__fxAt = performance.now(); window.__fxId = a; return real(a, b); }; }
  const realCel = celebrate; window.celebrate = function(a, b){ window.__celAt = performance.now(); return realCel(a, b); };
  cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.source = 'all'; cfg.size = 0; cfg.versions = {}; theme.autoAdvance = true;
  beginRun(freshOrder(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic.trim() === 'Identity Crimes')), null);
  for(let i = 0; i < 80 && !document.querySelector('.choice'); i++) await wait(100);
  let last = -1, guard = 0;
  while(testInProgress && guard++ < 240){
    const ch = [...document.querySelectorAll('#stage .choice:not(.locked)')];
    if(pos !== last && ch.length){ last = pos; const slot = correctSlot(order[pos]); ch[slot] && ch[slot].click(); }
    await wait(250);
  }
  for(let i = 0; i < 60 && !window.__fxAt && !window.__celAt; i++) await wait(100);
"""


# When to look: early (it should still be at the box) and late (it should
# have spread). The UFO is the exception by design - it comes down out of
# the dark - so it is checked for LANDING on the box instead.
# Fireworks is the shipped 50 (round 4); the Black Hole and Underwater are
# the earlier builds for that slot, still built and still checked. Fireworks
# is drawn on a canvas, so its start at the box and its spread are read off
# the canvas's own pixels rather than by the screenshot diff below; neither
# of the other two starts from the box by design (the hole darkens the
# whole screen as it opens, the water floods up from the bottom), so each
# has checks of its own instead.
FX_EARLY = {"worldtree": .6, "bubbles": .55}
FX_LATE = {"worldtree": 2.8, "bubbles": 3.4}
FX_ALL = ["fireworks", "blackhole", "underwater", "worldtree", "bubbles", "ufo"]


def fx_spread(pg, fx):
    """Plays `fx` again on the real results box and, at two moments, pauses
    every animation, takes the screen with and without the effect's layers,
    and measures where the difference is: inside the box (grown 48px), and
    far from it (outside the box grown 120px)."""
    from PIL import Image, ImageChops
    ok = pg.evaluate("""(fx) => { const g = document.querySelector('.rs-grade');
      if(!g || typeof playHundoFx !== 'function') return false;
      window.scrollTo({ top: Math.max(0, g.getBoundingClientRect().top + scrollY - innerHeight * .55), behavior: 'instant' });
      window.__h2 = playHundoFx(fx, { box: g, pct: g.querySelector('.rs-pct') }); window.__t2 = performance.now(); return !!window.__h2; }""", fx)
    if not ok:
        return None
    out = {}
    for tag, at in (("early", FX_EARLY[fx]), ("late", FX_LATE[fx])):
        box = pg.evaluate("""async (ms) => { const d = ms - (performance.now() - window.__t2); if(d > 0) await new Promise(r => setTimeout(r, d));
          document.getAnimations().forEach(a => { try{ a.pause(); }catch(e){} });
          const g = document.querySelector('.rs-grade'), r = g.getBoundingClientRect();
          const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
          return [cx - g.offsetWidth / 2, cy - g.offsetHeight / 2, cx + g.offsetWidth / 2, cy + g.offsetHeight / 2]; }""", at * 1000)
        a = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        pg.evaluate("() => document.querySelectorAll('.hfx-layer, .hfx-box, .hfx-pane').forEach(e => e.style.visibility = 'hidden')")
        b = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        pg.evaluate("() => { document.querySelectorAll('.hfx-layer, .hfx-box, .hfx-pane').forEach(e => e.style.visibility = ''); document.getAnimations().forEach(a => { try{ a.play(); }catch(e){} }); }")
        diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 30 else 0)
        px = diff.load(); W, H = diff.size
        n = inside = far = 0
        for y in range(0, H, 2):
            for x in range(0, W, 2):
                if px[x, y]:
                    n += 1
                    if box[0] - 48 <= x <= box[2] + 48 and box[1] - 48 <= y <= box[3] + 48: inside += 1
                    if not (box[0] - 120 <= x <= box[2] + 120 and box[1] - 120 <= y <= box[3] + 120): far += 1
        out[tag] = {"n": n * 4, "inside": round(inside / n, 3) if n else 0, "far": round(far / n, 3) if n else 0, "farN": far * 4}
    pg.evaluate("() => { if(window.__h2 && window.__h2.stop) window.__h2.stop(); }")
    return out


def check_b313_fx(br):
    """Build 313: "Can we introduce 1 new type of unlock? ... the effect you
    get when getting a 100? It's confetti by default? ... The ultimate
    character zenith would need these to be completed as well ... make
    these ones kind of inline so it's the same challenge but harder and
    harder". Then: "Bubbles should be the rarest one", "the first one now
    unlocks at 50 hundos", "make them start from the 100 box and spread
    out", "the first two are ehh maybe try something else", the UFO after
    Bubbles, "the themes matches the box", "it would obviously disappear
    slowly like how it does now", and the pop-ups: the already-qualified
    on Home, the rest on the results screen. Fails on 312, which has none
    of it."""
    print("\n313fx. hundo effects: the ladder, from the box, the box's colours, the slow tail, the pop-ups, Zenith")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    # the ladder as the page has it: the gate asserts its shape, not its names
    LADDER = pg.evaluate("() => HUNDO_FX.map(d => ({ id: d.id, name: d.name, built: typeof HUNDO_FX_BUILD[d.id] === 'function' || d.id === 'confetti' }))")
    IDS, NAMES = [d["id"] for d in LADDER], [d["name"] for d in LADDER]
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const tiles = () => [...document.querySelectorAll('.hfx-opt')].map(b => ({ id: b.dataset.fx, locked: b.classList.contains('locked'),
        sel: b.classList.contains('selected'), need: (b.querySelector('.hfx-opt-need') || {}).textContent, stage: !!b.querySelector('.hfx-stage') }));
      store.lifetime.perfectTests = 0; saveStore(); showCustomize('fx'); await wait(400);
      out.zero = tiles();
      store.lifetime.perfectTests = 120; saveStore(); showCustomize('fx'); await wait(400);
      out.mid = tiles();
      out.heads = [...document.querySelectorAll('.screen-customize .slab')].map(e => e.textContent.trim());
      out.firstLive = !!document.querySelector('.hfx-opt[data-fx="confetti"] .hfx-stage');
      document.querySelector('.hfx-opt[data-fx="confetti"]')?.scrollIntoView({ block: 'center', behavior: 'instant' });
      await wait(2600); out.confettiPieces = document.querySelectorAll('.hfx-opt[data-fx="confetti"] .hfx-stage *').length;
      /* build 314: the tiles are STILL - nothing in any tile is animating
         and no effect's layers are in them, 2.6s after the screen opened */
      out.tileAnims = [...document.querySelectorAll('.hfx-opt')].reduce((n, b) => n + b.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length, 0);
      out.tileFx = document.querySelectorAll('.hfx-opt .hfx-box, .hfx-opt .hfx-layer').length;
      out.posters = document.querySelectorAll('.hfx-opt .hfx-stage.is-poster svg').length;
      /* the tiles are the banners' size and shape */
      const ta = document.querySelector('.hfx-opt .hfx-stage');
      out.tile = ta ? [ta.offsetWidth, ta.offsetHeight] : null;
      /* the banners have a page of their own since build 315 */
      showCustomize('banner'); await wait(400);
      const ba = document.querySelector('.banner-opt .banner-opt-art');
      out.banner = ba ? [ba.offsetWidth, ba.offsetHeight] : null;
      showCustomize('fx'); await wait(400);
      document.querySelector('.hfx-opt[data-fx="worldtree"]')?.click(); await wait(200);
      out.picked = store.hundoFx;
      /* build 314: a first tap only picks it ("if it's not selected and you
         tap it, that's selecting") - no card */
      out.firstTapCard = document.querySelectorAll('.unlock-card').length;
      out.firstTapSel = !!document.querySelector('.hfx-opt[data-fx="worldtree"].selected');
      /* and a tap on the picked one shows it: the card, with the effect playing on a results screen in miniature */
      document.querySelector('.hfx-opt[data-fx="worldtree"]')?.click(); await wait(200);
      out.tapCard = !!document.querySelector('.unlock-card-fx .hfx-mock');
      await wait(1600);
      out.tapLive = document.querySelectorAll('.unlock-card-fx .hfx-mock .hfx-layer, .unlock-card-fx .hfx-mock .hfx-box').length;
      out.tapHeld = !!document.querySelector('.unlock-card-fx.is-unlocked');
      document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); await wait(100);
      document.querySelector('.hfx-opt[data-fx="ufo"]')?.click(); await wait(500);
      out.cardText = (document.querySelector('.unlock-card-fx') || {}).textContent || '';
      out.preview = !!document.querySelector('.unlock-card-fx .unlock-card-preview');
      out.stillPicked = store.hundoFx;
      document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); await wait(100);
      /* round 4: a pick of the retired Black Hole, at 120 hundos - it plays
         Confetti, Confetti's tile is the one selected, and the 50 is held
         and one tap away */
      store.hundoFx = 'blackhole'; saveStore();
      out.oldInUse = hundoFxInUse();
      showCustomize('fx'); await wait(400);
      out.oldSel = [...document.querySelectorAll('.hfx-opt.selected')].map(b => b.dataset.fx);
      const t50 = document.querySelector('.hfx-opt[data-fx="' + HUNDO_FX[1].id + '"]');
      out.old50Held = !!t50 && !t50.classList.contains('locked');
      t50?.click(); await wait(200);
      out.oldRepick = store.hundoFx;
      document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
      store.hundoFx = 'worldtree'; saveStore();   /* as the tap above left it, for the read-back below */
      return out; }""")
    r0 = r
    mid = r.get("mid") or []
    nums = [int(re.sub(r"[^0-9]", "", t["need"] or "") or 0) for t in mid]
    check("Customize has a Hundo effect section", any("hundo effect" in h.lower() for h in r.get("heads") or []), r.get("heads"))
    check("five tiles in HUNDO_FX's order (%s), Confetti first, each a small 100%% box" % ", ".join(NAMES),
          len(IDS) == 5 and IDS[0] == "confetti" and [t["id"] for t in mid] == IDS and all(t["stage"] for t in mid), [t["id"] for t in mid])
    check("every rung on the ladder is a built effect - the 50 is %s" % NAMES[1], all(d["built"] for d in LADDER), LADDER)
    check("four to earn, one ladder of hundos: 50, 100, 200, 350", nums[1:] == [50, 100, 200, 350], [t["need"] for t in mid])
    check("Confetti comes first and is held by everyone", mid and mid[0]["id"] == "confetti" and not mid[0]["locked"] and r.get("firstLive"), {k: r.get(k) for k in ("firstLive",)})
    check("build 314: every tile is a STILL of its effect - nothing animating in any tile, no effect playing in one (\"all those effects and animations seems like a lot, don't do the effects there\")",
          r.get("tileAnims") == 0 and r.get("tileFx") == 0 and r.get("posters") == len(IDS), {k: r.get(k) for k in ("tileAnims", "tileFx", "posters")})
    check("with no hundos only Confetti is held", [t["locked"] for t in r.get("zero") or []] == [False] + [True] * 4, r.get("zero"))
    check("with 120 hundos %s and %s are held, the rest are not" % (NAMES[1], NAMES[2]), [t["locked"] for t in mid] == [False, False, False, True, True], mid)
    tl, bn = r.get("tile") or [0, 1], r.get("banner") or [0, 1]
    check("the effect tiles are the banner tiles' size and shape (round 3: \"slightly too big\")",
          abs(tl[0] - bn[0]) <= 2 and abs(tl[1] - bn[1]) <= 3, {"tile": r.get("tile"), "banner": r.get("banner")})
    check("build 314: tapping a held one that is not picked PICKS it and opens nothing (like a character or a banner)",
          r.get("firstTapCard") == 0 and r.get("firstTapSel") and r.get("picked") == "worldtree", {k: r.get(k) for k in ("firstTapCard", "firstTapSel", "picked")})
    check("tapping the picked one opens its card, held, with the effect playing on a results screen in miniature",
          r.get("tapCard") and r.get("tapLive", 0) >= 1 and r.get("tapHeld"), {k: r.get(k) for k in ("tapCard", "tapLive", "tapHeld")})
    check("tapping a held one picks it; a locked one opens its card (its count) and picks nothing",
          r.get("picked") == "worldtree" and "350" in r.get("cardText", "") and r.get("stillPicked") == "worldtree",
          {k: r.get(k) for k in ("picked", "cardText", "stillPicked")})
    check("build 314: the card has no Preview button (\"The preview button also can be removed\") - the miniature results screen is the preview",
          not r.get("preview") and "Preview" not in r.get("cardText", ""), {k: r.get(k) for k in ("preview",)})
    r = pg.evaluate("""() => { const got = JSON.parse(JSON.stringify(store)); delete got.hundoFx;
      store.hundoFx = 'confetti'; loadStore(); const kept = store.hundoFx;
      applyLoadedData(got); const def = store.hundoFx;
      applyLoadedData(Object.assign(JSON.parse(JSON.stringify(store)), { hundoFx: 'worldtree' })); const cloud = store.hundoFx;
      store.lifetime.perfectTests = 10; store.hundoFx = 'bubbles';
      const fallback = typeof hundoFxInUse === 'function' ? hundoFxInUse() : null;
      return { kept, def, cloud, fallback }; }""")
    check("the pick is saved and read back at boot; a cloud copy without it is Confetti; one with it keeps it",
          r.get("kept") == "worldtree" and r.get("def") == "confetti" and r.get("cloud") == "worldtree", r)
    check("a pick that is not held here falls back to Confetti", r.get("fallback") == "confetti", r)
    ctx.close()
    check("round 4: a saved pick of the retired Black Hole plays Confetti, and Customize shows Confetti picked, not nothing",
          r0.get("oldInUse") == "confetti" and r0.get("oldSel") == ["confetti"], {k: r0.get(k) for k in ("oldInUse", "oldSel")})
    check("and the 50 (%s) is held and a tap picks it" % NAMES[1], r0.get("old50Held") and r0.get("oldRepick") == IDS[1], {k: r0.get(k) for k in ("old50Held", "oldRepick")})

    # --- every effect on a real 100%: it plays, from the box, in the box's
    # new colours, with a slow tail, then is gone and the box is yellow again
    for fx in FX_ALL:
        ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
        r = pg.evaluate("async (fx) => { store.lifetime.perfectTests = 600; if(typeof HUNDO_FX !== 'undefined' && !HUNDO_FX.some(d => d.id === fx)) HUNDO_FX[1].id = fx; store.hundoFx = fx; saveStore(); " + FX_RUN + """
          const out = { id: window.__fxId || null, started: !!window.__fxAt };
          if(!window.__fxAt) return out;
          const since = () => performance.now() - window.__fxAt;
          const until = async ms => { const d = ms - since(); if(d > 0) await wait(d); };
          const opac = el => parseFloat(getComputedStyle(el).opacity);
          const shown = (el, root) => { let o = 1; for(let e = el; e && e !== root.parentElement; e = e.parentElement) o *= opac(e); return o; };
          const g = document.querySelector('.rs-grade');
          /* round 4: where the screen's own cards are, every 200ms through the
             effect - on the page, so the reveal's scroll is not a move */
          const still = [], cards = () => [...document.querySelectorAll('.rs-screen > *')].filter(e => !e.classList.contains('hfx-layer') && e.offsetWidth)
            .map(e => { const q = e.getBoundingClientRect(); return [Math.round(q.left + scrollX), Math.round(q.top + scrollY), Math.round(q.width), Math.round(q.height)].join(','); }).join(' ');
          /* and any script-made animation on them (the Black Hole's pull, the water's sway are those) */
          let scripted = 0;
          const sampler = fx === 'fireworks' ? setInterval(() => { still.push([Math.round(since()), cards()]);
            scripted = Math.max(scripted, [...document.querySelectorAll('.rs-screen > *')].reduce((n, e) => n + e.getAnimations().filter(a => a.constructor === Animation).length, 0)); }, 200) : null;
          /* what the sky canvas has lit: how many pixels, and their extent, in the viewport */
          const lit = () => { const cv = document.querySelector('.hfx-layer.hfx-fireworks canvas.hfx-fw-sky'); if(!cv) return null;
            const x = cv.getContext('2d'), d = x.getImageData(0, 0, cv.width, cv.height).data, cr = cv.getBoundingClientRect(), sx = cr.width / cv.width, sy = cr.height / cv.height;
            let n = 0, x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
            for(let yy = 0; yy < cv.height; yy += 3) for(let xx = 0; xx < cv.width; xx += 3){ if(d[(yy * cv.width + xx) * 4 + 3] > 60){ n++;
              const X = cr.left + xx * sx, Y = cr.top + yy * sy; if(X < x0) x0 = X; if(X > x1) x1 = X; if(Y < y0) y0 = Y; if(Y > y1) y1 = Y; } }
            return { n, x0: Math.round(x0), x1: Math.round(x1), y0: Math.round(y0), y1: Math.round(y1) }; };
          if(fx === 'fireworks'){
            await until(420);
            const gr = g.getBoundingClientRect();
            out.early = lit(); out.boxAt = { l: Math.round(gr.left), r: Math.round(gr.right), t: Math.round(gr.top), b: Math.round(gr.bottom) };
            out.dimEarly = (() => { const d = document.querySelector('.hfx-fw-dim'); return d ? parseFloat(getComputedStyle(d).opacity) : null; })();
          }
          await until(1600);
          const scr = document.querySelector('.hfx-layer.hfx-' + fx), box = document.querySelector('.rs-grade .hfx-box.hfx-' + fx);
          out.screen = scr ? scr.querySelectorAll('*').length : 0;
          out.box = box ? box.querySelectorAll('*').length : 0;
          const fill = () => { const f = document.querySelector('.rs-screen .unit-breakdown-fill.is-gold'); return f ? getComputedStyle(f).backgroundImage : null; };
          out.border = getComputedStyle(g).borderTopColor; out.fill = fill();
          if(fx === 'worldtree'){
            await until(3000);
            out.panes = document.querySelectorAll('.rs-screen > .rs-card > .hfx-pane').length;
            out.sharp = document.querySelectorAll('.hfx-layer.hfx-worldtree .hfx-seg.is-wood').length;
          }
          if(fx === 'underwater'){
            await until(2600);
            const sea = document.querySelector('.hfx-uw-sea'), sr = sea && sea.getBoundingClientRect(), gr = g.getBoundingClientRect();
            out.flooded = !!sr && sr.top <= gr.top && sr.bottom >= gr.bottom;
          }
          if(fx === 'blackhole'){
            const xp = document.querySelector('.rs-screen > .rs-xp');
            await until(2650);
            const cs = getComputedStyle(xp);
            out.pulled = { translate: cs.translate, scale: cs.scale };
            const hole = document.querySelector('.hfx-bh'), hr = hole && hole.getBoundingClientRect(), gr = g.getBoundingClientRect();
            out.atBox = hr ? Math.round(Math.hypot(hr.left - (gr.left + gr.width / 2), hr.top - (gr.top + gr.height / 2))) : null;
            await until(4800);
            const c2 = getComputedStyle(xp);
            out.back = { translate: c2.translate, scale: c2.scale };
          }
          if(fx === 'fireworks'){
            await until(3900);
            const gr = g.getBoundingClientRect();
            out.late = lit(); out.boxLate = { t: Math.round(gr.top) };
            out.dimMid = (d => d ? parseFloat(getComputedStyle(d).opacity) : null)(document.querySelector('.hfx-fw-dim'));
          }
          if(fx === 'ufo'){
            out.beforeBeam = getComputedStyle(g).borderTopColor;
            await until(4700);
            out.border = getComputedStyle(g).borderTopColor; out.fill = fill();
            const b = document.querySelector('.hfx-saucer .hfx-ufo-bob'), br = b && b.getBoundingClientRect(), gr = g.getBoundingClientRect();
            out.landed = br ? { feet: Math.round(br.bottom - gr.top), cx: Math.round(br.left + br.width / 2 - (gr.left + gr.width / 2)) } : null;
          }
          const T = (typeof HUNDO_FX_TOTAL === 'object' && HUNDO_FX_TOTAL[fx]) || 0, tail = (typeof HUNDO_FX_TAIL_AT === 'object' && HUNDO_FX_TAIL_AT[fx]) || 0;
          out.total = T;
          /* build 315: the tail is watched from its start to the moment the
             layer goes, not read once at 45% of it. A single read passed
             the build where four bubbles sat fully shown until the layer
             was cut away at 7s (they were not "fading", so nothing looked
             at them) and failed the build that fixed it, whose bubbles had
             all faded out by 6s - before the one read. What "never cut"
             means is the LAST look before the layer goes: no piece of it
             (a leaf, and some of it in sight) still fully shown. */
          await until(tail);
          /* what of a piece can be SEEN: its box cut down by every ancestor
             that clips (overflow) and by the viewport. The Underwater sea
             drains its water below its own clipped box, so the water's raw
             box is still on the page while none of it shows. */
          const seen = (el, root) => {
            const q = el.getBoundingClientRect();
            let l = Math.max(q.left, 0), t = Math.max(q.top, 0), r = Math.min(q.right, innerWidth), b = Math.min(q.bottom, innerHeight);
            for(let a = el.parentElement; a && l < r && t < b; a = a.parentElement){
              const cs = getComputedStyle(a);
              if(cs.overflowX !== 'visible' || cs.overflowY !== 'visible'){
                const w = a.getBoundingClientRect();
                l = Math.max(l, w.left); t = Math.max(t, w.top); r = Math.min(r, w.right); b = Math.min(b, w.bottom);
              }
              if(a === root) break;
            }
            return l < r && t < b;
          };
          let firstTail = null, lastLive = null;
          while(since() < T + 400){
            const s2 = document.querySelector('.hfx-layer.hfx-' + fx), b2 = document.querySelector('.rs-grade .hfx-box.hfx-' + fx);
            if(!s2 && !b2) break;
            const parts = (s2 ? [...s2.querySelectorAll('*')].map(e => [shown(e, s2), e]) : []).concat(b2 ? [...b2.querySelectorAll('*')].map(e => [shown(e, b2), e]) : []);
            const look = { t: Math.round(since()), layer: !!s2 && opac(s2) > .99,
              fading: parts.filter(p => p[0] > .02 && p[0] < .98).length,
              full: parts.filter(p => p[0] >= .98 && !p[1].children.length && seen(p[1], p[1].closest('.hfx-layer, .hfx-box') || document.body)).map(p => String(p[1].className && p[1].className.baseVal !== undefined ? p[1].className.baseVal : p[1].className).split(' ')[0]) };
            if(!firstTail) firstTail = look;
            lastLive = look;
            await wait(50);
          }
          out.tailLayer = !!firstTail && firstTail.layer;
          out.tailFading = firstTail ? firstTail.fading : 0;
          out.cutAt = lastLive ? lastLive.t : null;
          out.cutFull = lastLive ? lastLive.full : null;
          await until(T + 1300);
          out.after = document.querySelectorAll('.hfx-layer, .hfx-box.is-grade, .hfx-pane').length;
          out.borderAfter = getComputedStyle(g).borderTopColor; out.fillAfter = fill();
          const tn = g.querySelector(':scope > .hfx-tintnum.hfx-keep');
          out.numAfter = tn ? parseFloat(getComputedStyle(tn).opacity) : 0;
          out.screenUp = !!document.querySelector('.rs-screen') && g.isConnected;
          out.tintVars = ['--hfx-b', '--hfx-g1', '--hfx-g2'].map(k => g.style.getPropertyValue(k).trim());
          if(sampler){ clearInterval(sampler); out.still = still; out.cardAnims = scripted; }
          return out; }""", fx)
        yellow = "rgba(242, 211, 138, 0.2)"
        check("%s: a 100%% plays it, on the screen and in the box" % fx, r.get("id") == fx and r.get("screen", 0) > 3 and r.get("box", 0) > 2, r)
        check("%s: the box takes the effect's colours while it plays" % fx, r.get("border") not in (None, yellow), r.get("border"))
        rgb = lambda h: "rgb(%d, %d, %d)" % tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) if h and h.startswith("#") else None
        tv = r.get("tintVars") or [None, None, None]
        check("%s: and KEEPS them once the effect has finished, the results screen still up (round 3: \"it stays yellow\")" % fx,
              r.get("screenUp") and tv[0] and r.get("borderAfter") == rgb(tv[0]) and r.get("numAfter", 0) > .95, {k: r.get(k) for k in ("borderAfter", "numAfter", "screenUp", "tintVars")})
        check("%s: in its tail it is still on screen, fading - never cut (nothing fully shown at the last look before the layer goes)" % fx,
              r.get("tailLayer") and r.get("tailFading", 0) >= 2 and r.get("cutFull") == [], {k: r.get(k) for k in ("tailLayer", "tailFading", "cutAt", "cutFull", "total")})
        check("%s: and once it has faded every piece is gone" % fx, r.get("after") == 0 and r.get("total", 0) > 0, r)
        gold = "rgb(217, 169, 58)"
        check("%s: the box's progress bar takes the effect's colours too, and keeps them after" % fx,
              r.get("fill") and gold not in r["fill"] and tv[2] and r.get("fillAfter") == "linear-gradient(90deg, %s, %s)" % (rgb(tv[2]), rgb(tv[1])), {"during": r.get("fill"), "after": r.get("fillAfter")})
        if fx == "worldtree":
            check("worldtree: the cards become glass - a pane in each card, the tree passing behind them", r.get("panes", 0) >= 2 and r.get("sharp", 0) >= 4, r)
        if fx == "fireworks":
            ea, la, ba = r.get("early") or {}, r.get("late") or {}, r.get("boxAt") or {}
            check("fireworks: it starts AT the 100% box - the first shell is climbing out of its top edge, nothing lit anywhere else",
                  ea.get("n", 0) > 4 and ba and ea["x0"] >= ba["l"] - 12 and ea["x1"] <= ba["r"] + 12 and ea["y1"] <= ba["t"] + 8 and ea["y0"] >= ba["t"] - 260, {"lit": ea, "box": ba})
            check("fireworks: and spreads out - by the finale the sky above the box is lit across most of the screen",
                  la.get("n", 0) > 400 and la["x1"] - la["x0"] >= 440 * .7 and la["y0"] < (r.get("boxLate") or {}).get("t", 0) - 300, {"lit": la, "box": r.get("boxLate")})
            check("fireworks: the screen dims a little behind the sky - and only a little", r.get("dimMid") is not None and .3 <= r["dimMid"] <= .6, r.get("dimMid"))
            st = r.get("still") or []
            later = [c for t, c in st if t >= 400]
            check("fireworks: the screen itself does not move - every card where it was, every 200ms from 0.4s (the grade card has landed) to the end (round 4: \"not a fan of that giddy one\")",
                  len(later) >= 20 and len(set(later)) == 1 and r.get("cardAnims") == 0, {"samples": len(later), "distinct": len(set(later)), "cardAnims": r.get("cardAnims"), "first": later[:1], "odd": [c for c in set(later) if later and c != later[0]][:2]})
        if fx == "underwater":
            check("underwater: the screen floods - the water is over the whole box", r.get("flooded"), r)
        if fx == "blackhole":
            pl, bk = r.get("pulled") or {}, r.get("back") or {}
            sc = [float(v) for v in (pl.get("scale") or "1").split()]
            ty = (pl.get("translate") or "0px 0px").replace("px", "").split()
            check("blackhole: the hole opens at the box", r.get("atBox") is not None and r["atBox"] <= 4, r.get("atBox"))
            check("blackhole: the XP card is pulled in towards it - moved down to the box and squeezed",
                  len(ty) == 2 and float(ty[1]) > 60 and min(sc) < .8, pl)
            check("blackhole: and springs back to exactly where it was", bk.get("scale") in ("none", "1", "1 1") and bk.get("translate") in ("none", "0px", "0px 0px"), bk)
        if fx == "ufo":
            check("ufo: the box does not light up before the beam reaches it", r.get("beforeBeam") == yellow, r.get("beforeBeam"))
            ld = r.get("landed") or {}
            check("ufo: it lands ON the 100% box - its feet on the box's top edge, over its middle",
                  ld and abs(ld.get("feet", 99)) <= 8 and abs(ld.get("cx", 99)) <= 30, ld)
        elif fx in FX_EARLY:
            sp = fx_spread(pg, fx)
            check("%s: it starts AT the 100%% box - its first visible pieces are on the box" % fx, sp and sp["early"]["n"] >= 150 and sp["early"]["inside"] >= .85, sp)
            # an absolute area far from the box, not a share: the box's own
            # new colours are a lot of pixels inside it, and a meteor is thin
            check("%s: and spreads out - later its pieces reach well beyond the box" % fx, sp and sp["late"]["farN"] >= 400, sp)
        ctx.close()

    # --- Confetti, the default, leaves the box gold
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("async () => { store.lifetime.perfectTests = 600; store.hundoFx = 'confetti'; saveStore(); " + FX_RUN + """
      await wait(4200); const g = document.querySelector('.rs-grade'), f = document.querySelector('.rs-screen .unit-breakdown-fill.is-gold');
      return { border: getComputedStyle(g).borderTopColor, fill: f ? getComputedStyle(f).backgroundImage : null, tinted: g.classList.contains('hfx-tinted') }; }""")
    check("Confetti, the default, leaves the box and its bar gold", r.get("border") == "rgba(242, 211, 138, 0.2)" and "rgb(217, 169, 58)" in (r.get("fill") or "") and not r.get("tinted"), r)
    ctx.close()

    # --- the pop-ups. An account with no record of them, at 120 hundos:
    # the first two (Fireworks then World Tree) on Home, once; a live preview inside; gone after.
    acct = json.loads(USED_ACCOUNT)
    del acct["unlocksShown"]
    acct["lifetime"]["perfectTests"] = 120
    ctx, pg = booted(br, 440, 956, seed=json.dumps(acct))
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = { seen: [], live: [], gone: [] };
      showHome();
      for(let i = 0; i < 120; i++){
        const sp = document.querySelector('.rs-spot.is-up');
        if(sp && sp.classList.contains('rs-spot-fx')){
          const name = sp.querySelector('.rs-spot-name').textContent;
          if(out.seen[out.seen.length - 1] !== name){
            out.seen.push(name);
            await wait(3200);
            out.live.push(document.querySelectorAll('.rs-spot-fx .hfx-stage .hfx-box').length);
            out.use = !!out.use || !!sp.querySelector('.rs-spot-use') || /use this effect/i.test(sp.textContent);
            out.need = out.need || (sp.querySelector('.rs-spot-need-text') || {}).textContent;
            sp.click(); await wait(1100);
            out.gone.push(document.querySelectorAll('.rs-spot-fx, .hfx-box, .hfx-layer').length);
            continue;
          }
        } else if(sp) sp.click();
        await wait(250);
      }
      out.shown = (store.unlocksShown || {}).fx || [];
      out.store = JSON.stringify(store);
      return out; }""")
    check("an account already at 120 hundos gets %s then %s on Home - two in a row" % (NAMES[1], NAMES[2]), r.get("seen") == NAMES[1:3], r.get("seen"))
    check("each pop-up plays the effect live in its own 100% box and says what it took",
          r.get("live") and all(n >= 1 for n in r["live"]) and r.get("need") == "Earn 50 hundos", {k: r.get(k) for k in ("live", "need")})
    check("build 314: and has NO \"Use this effect\" button (\"let's remove that\")", r.get("use") is False, {k: r.get(k) for k in ("use",)})
    check("closing a pop-up stops and removes its preview", r.get("gone") and all(n == 0 for n in r["gone"]), r.get("gone"))
    check("both are recorded as shown", r.get("shown") == IDS[1:3], r.get("shown"))
    stored = r.get("store") or "{}"
    ctx.close()
    ctx, pg = booted(br, 440, 956, seed=stored)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); showHome(); let n = 0;
      for(let i = 0; i < 24; i++){ if(document.querySelector('.rs-spot-fx')) n++; const sp = document.querySelector('.rs-spot.is-up'); if(sp) sp.click(); await wait(250); } return n; }""")
    check("and not again on the next launch", r == 0, r)
    ctx.close()
    acct["lifetime"]["perfectTests"] = 0
    ctx, pg = booted(br, 440, 956, seed=json.dumps(acct))
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); showHome(); let n = 0;
      for(let i = 0; i < 24; i++){ if(document.querySelector('.rs-spot-fx')) n++; const sp = document.querySelector('.rs-spot.is-up'); if(sp) sp.click(); await wait(250); } return n; }""")
    check("an account with no hundos gets no hundo effect pop-up", r == 0, r)
    ctx.close()

    # --- crossing 50 in a run: on the results screen, in its slot, and not again on Home
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("async () => { store.lifetime.perfectTests = 49; store.unlocksShown.fx = []; store.hundoFx = 'bubbles'; saveStore(); " + FX_RUN + """
      await wait(400);
      const out = { played: window.__fxId || null, confetti: !!document.querySelector('.stardust-layer') };
      for(let i = 0; i < 80 && !document.querySelector('.rs-spot-fx.is-up'); i++) await wait(250);
      out.popup = (document.querySelector('.rs-spot-fx .rs-spot-name') || {}).textContent || null;
      await wait(1800);
      document.querySelector('.rs-spot')?.click();
      for(let i = 0; i < 60 && !document.querySelector('.rs-unlock-fx.rs-in, .rs-unlock-fx.rs-in-now'); i++) await wait(250);
      const row = document.querySelector('.rs-unlock-fx');
      out.row = row ? row.textContent : null;
      out.slot = !!(row && row.parentElement && row.parentElement.classList.contains('rs-unlock-slot'));
      out.fx = (typeof lastRunResult === 'object' && lastRunResult) ? lastRunResult.fx : null;
      showHome(); let n = 0;
      for(let i = 0; i < 24; i++){ if(document.querySelector('.rs-spot-fx')) n++; await wait(250); }
      out.home = n; out.shown = store.unlocksShown.fx;
      return out; }""")
    check("a picked effect that is not held plays Confetti instead", r.get("confetti") and r.get("played") in ("confetti", None), r)
    check("a run that takes you to 50 hundos announces %s on the results screen - pop-up and a row in its slot" % NAMES[1],
          r.get("popup") == NAMES[1] and r.get("fx") == IDS[1:2] and r.get("row") and NAMES[1] in r["row"] and r.get("slot"), r)
    check("and Home does not announce it again", r.get("home") == 0 and r.get("shown") == IDS[1:2], r)
    ctx.close()

    # --- Zenith counts the effects, the UFO included
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => { const out = {};
      const realLocked = isLockedCharacter, realEarned = bannerEarned, realAccent = isLockedAccent;
      window.isLockedCharacter = id => id === 'zenith' ? realLocked(id) : false;
      window.bannerEarned = id => id === 'zenith' ? realEarned(id) : true;
      window.isLockedAccent = () => false;
      store.lifetime.perfectTests = 300;
      out.mid = ultimateProgress(); out.midZenith = !isLockedCharacter('zenith');
      store.lifetime.perfectTests = 350;
      out.all = ultimateProgress(); out.allZenith = !isLockedCharacter('zenith');
      window.isLockedCharacter = realLocked; window.bannerEarned = realEarned; window.isLockedAccent = realAccent;
      out.label = CHARACTER_FEATS.everything.label;
      return out; }""")
    md, al = r.get("mid") or {}, r.get("all") or {}
    check("Zenith counts the hundo effects: one short at 300 hundos (no UFO yet)",
          md.get("need", 0) - md.get("have", 0) == 1 and "hundo effect" in (md.get("note") or "") and r.get("midZenith") is False, r)
    check("and is held at 350, with everything else", al.get("have") == al.get("need") and r.get("allZenith") is True, r)
    check("Zenith's requirement says so", "hundo effect" in (r.get("label") or ""), r.get("label"))
    ctx.close()



# --------------------------------------------------------------------------
# Build 314: the test and study flow
# --------------------------------------------------------------------------

B314_RUN = """()=>{ cfg.units=[topicsIn(QUESTIONS)[1]]; cfg.mode='drill'; cfg.size=30; cfg.source='all';
  const u=topicsIn(QUESTIONS)[1], idx=[]; QUESTIONS.forEach((q,i)=>{ if(q.topic===u && idx.length<30) idx.push(i); });
  beginRun(idx); }"""

B314_TOUCH = """()=>{
  window.__wait = ms => new Promise(r => setTimeout(r, ms));
  window.__raf = () => new Promise(r => requestAnimationFrame(r));
  window.__ensure = async () => { const n=document.getElementById('nextbtn');
    if(!n || n.hidden){ const all=[...document.querySelectorAll('#stage .choice')]; const qi=order[pos], oo=optionOrder(qi);
      all[oo.indexOf(QUESTIONS[qi].answer)].click(); await __wait(1300); } };
  window.__fire = (type, x, y) => { const p = document.querySelector('#stage > .panel');
    const t = new Touch({ identifier: 9, target: p, clientX: x, clientY: y });
    p.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true,
      touches: type === 'touchend' ? [] : [t], targetTouches: type === 'touchend' ? [] : [t], changedTouches: [t] })); };
  window.__px = () => { const p = document.querySelector('#stage > .panel'); const m = getComputedStyle(p).transform.match(/matrix\\(([^)]+)\\)/);
    return m ? +m[1].split(',')[4] : 0; };
  /* drag from x0 to x1 in n moves, `gap` ms apart, then hold `hold` ms; returns what the preview looked like */
  window.__drag = async (x0, x1, n, gap, hold) => {
    __fire('touchstart', x0, 600); await __raf();
    for(let i = 1; i <= n; i++){ __fire('touchmove', x0 + (x1 - x0) * i / n, 602); if(gap) await __wait(gap); else await __raf(); }
    if(hold) await __wait(hold);
    const pair = document.querySelector('.q-blurpair');
    return pair ? { sharp: +getComputedStyle(pair.children[1]).opacity, soft: +getComputedStyle(pair.children[0]).opacity,
      blur: parseFloat((getComputedStyle(pair.children[0]).filter.match(/blur\\(([\\d.]+)px/) || [0, 0])[1]),
      n: (pair.querySelector('.qnum') || {}).textContent } : null; };
}"""


def check_b314_swipe(br):
    """Build 314: a swipe has a line to cross, and the next question stays
    unreadable until it is crossed. "if I only swipe a little, it [should
    not] move to the next question, it would kinda bounce back ... even at
    the halfway point it should still be hard to read", and Next / auto /
    a full-speed flick "still smooth and that blurry stuff doesn't kinda
    make it look bad". Written against 313, where a 40px swipe advanced,
    the stand-in sharpened from the first pixel and Next arrived through
    a blurred copy; fails there."""
    print("\n99. build 314: the swipe - a line to cross, blurred until it is crossed, clean fast paths")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        pg.evaluate(B314_RUN)
        pg.wait_for_selector(".choice", timeout=20000)
        pg.wait_for_timeout(800)
        pg.evaluate(B314_TOUCH)
        r = pg.evaluate("""async ()=>{ const out = {};
          const push = document.querySelector('#stage > .panel').getBoundingClientRect().width + 28;
          const X0 = innerWidth - 24;
          /* 1. a slow drag to a fifth of the way, let go: back, same question */
          await __ensure(); let q0 = pos;
          await __drag(X0, X0 - push * .2, 8, 40, 120); __fire('touchend', X0 - push * .2, 602); await __wait(120);
          const mid = __px(); await __wait(420);
          out.small = { advanced: pos !== q0, x: Math.round(__px()), midReturn: Math.round(mid), pairs: document.querySelectorAll('.q-blurpair').length };
          /* 2. a quick nudge, 10% of the way in two frames: still a bounce */
          await __drag(X0, X0 - push * .1, 2, 0, 0); __fire('touchend', X0 - push * .1, 602); await __wait(500);
          out.nudge = { advanced: pos !== q0, x: Math.round(__px()) };
          /* 3. held at half way and at three quarters: blurred, nothing sharp */
          out.half = await __drag(X0, X0 - push * .5, 10, 30, 200);
          for(let i = 1; i <= 5; i++){ __fire('touchmove', X0 - push * (.5 + .25 * i / 5), 602); await __wait(30); }
          await __wait(200);
          const pr = document.querySelector('.q-blurpair');
          out.threeq = pr ? { sharp: +getComputedStyle(pr.children[1]).opacity } : null;
          out.want = 'Question ' + (pos + 2);
          /* 4. let go there, slowly: it commits, and the arrival sharpens while it moves */
          const frames = []; let done = false;
          (async () => { while(!done){ await __raf(); const n = document.querySelector('#stage > .panel');
            const m = getComputedStyle(n).transform.match(/matrix\\(([^)]+)\\)/);
            frames.push({ x: m ? +m[1].split(',')[4] : 0, o: +getComputedStyle(n).opacity, q: pos }); } })();
          __fire('touchend', X0 - push * .75, 602);
          await __wait(600); done = true;
          out.commit = { advanced: pos !== q0, left: document.querySelectorAll('.q-blurpair, body > .panel').length };
          const arriving = frames.filter(f => f.q !== q0);
          /* let go at 3/4: sharp by the last fifth of the quarter still to go */
          out.lateSoft = arriving.filter(f => f.x < push * .25 * .2 && f.o < .97).length;
          out.arrivingN = arriving.length;
          /* 5. a full-speed flick a quarter of the way: commits */
          await __ensure(); q0 = pos;
          __fire('touchstart', X0, 600); for(let i = 1; i <= 3; i++){ await __wait(16); __fire('touchmove', X0 - push * .25 * i / 3, 602); }
          __fire('touchend', X0 - push * .25, 602); await __wait(600);
          out.flick = { advanced: pos !== q0 };
          /* 6. Next: a solid push, nothing blurred, nothing re-fading in the copy */
          await __ensure(); await __wait(300);
          const right = document.querySelector('#stage .choice.is-right');
          const want = right ? getComputedStyle(right).borderTopColor : null;
          const nf = []; let nd = false;
          document.getElementById('nextbtn').click();
          const anims = document.getAnimations().filter(a => a.effect && a.effect.target && (a.effect.target.closest('body > .panel') || a.effect.target.matches('#stage > .panel')));
          out.animProps = [...new Set(anims.flatMap(a => a.effect.getKeyframes().flatMap(k => Object.keys(k).filter(x => !['offset','easing','composite','computedOffset'].includes(x)))))].sort();
          out.cssTransitionsInCopy = document.getAnimations().filter(a => a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest('body > .panel') && a.constructor.name !== 'Animation').length;
          for(let i = 0; i < 14; i++){ await __raf(); const c = document.querySelector('body > .panel'), n = document.querySelector('#stage > .panel');
            const cr = c && c.querySelector('.choice.is-right');
            nf.push({ blur: !!document.querySelector('.q-blurpair'), o: n ? +getComputedStyle(n).opacity : 1,
                      copyRight: cr ? getComputedStyle(cr).borderTopColor : null }); }
          out.next = { blurred: nf.filter(f => f.blur).length, minOpacity: Math.min(...nf.map(f => f.o)),
                       copyRightChanged: nf.filter(f => f.copyRight && want && f.copyRight !== want).length, want };
          await __wait(400);
          /* 7. a spring-back caught by a new touch is held where it is, no snap */
          await __ensure(); q0 = pos;
          await __drag(X0, X0 - push * .3, 6, 30, 50); __fire('touchend', X0 - push * .3, 602);
          await __wait(90); const before = __px(); __fire('touchstart', X0, 600); await __raf(); const after = __px();
          __fire('touchend', X0, 600); await __wait(500);
          out.catch = { before: Math.round(before), after: Math.round(after), advanced: pos !== q0, x: Math.round(__px()) };
          return out; }""")
        ctx.close()
        check("%s a slow drag a fifth of the way springs back to the same question" % label,
              not r["small"]["advanced"] and abs(r["small"]["x"]) <= 1 and r["small"]["midReturn"] < -2 and r["small"]["pairs"] == 0, r["small"])
        check("%s a quick short nudge springs back too" % label,
              not r["nudge"]["advanced"] and abs(r["nudge"]["x"]) <= 1, r["nudge"])
        hf, tq = r.get("half") or {}, r.get("threeq") or {}
        check("%s held at halfway the next question is there, heavily blurred, with nothing sharp" % label,
              hf.get("n") == r["want"] and hf.get("sharp") == 0 and hf.get("blur", 0) >= 8 and hf.get("soft", 0) > .9, hf)
        check("%s and at three quarters still nothing sharp" % label, tq.get("sharp") == 0, tq)
        check("%s released past the line it goes, and sharpens while moving - fully sharp before it slows into place" % label,
              r["commit"]["advanced"] and r["commit"]["left"] == 0 and r["arrivingN"] >= 2 and r["lateSoft"] == 0,
              (r["commit"], r["lateSoft"], r["arrivingN"]))
        check("%s a full-speed flick a quarter of the way commits" % label, r["flick"]["advanced"], r["flick"])
        check("%s Next is a solid push: no blurred copy, the new question never below 85%%" % label,
              r["next"]["blurred"] == 0 and r["next"]["minOpacity"] >= .84, r["next"])
        check("%s the moves animate transform and opacity only, and the leaving copy replays nothing" % label,
              r["animProps"] == ["opacity", "transform"] and r["cssTransitionsInCopy"] == 0 and r["next"]["copyRightChanged"] == 0,
              (r["animProps"], r["cssTransitionsInCopy"], r["next"]["copyRightChanged"]))
        c = r["catch"]
        check("%s a spring-back caught by a new touch stays where it was" % label,
              c["before"] < -2 and abs(c["after"] - c["before"]) <= 3 and not c["advanced"] and abs(c["x"]) <= 1, c)


def check_b314_feel(br):
    """Build 314: the answer lands sooner and the Next pill rises later.
    "The incorrect one looks good but that delay is too long, could be cut
    in half, and then the vibration effect could be slightly toned down.
    The correct answer, the delay is too strong as well" and "The next
    question button that comes up is now JUST slightly too quick ... it
    was better before." Measured on 313: the colour was half there 282ms
    after a right tap and 284ms after a wrong one, the nudge was 4px, and
    Next began rising 500ms after the tap (build 311: 849ms). Fails there."""
    print("\n100. build 314: the answer lands in half the time, the nudge is softer, Next rises at 311's pace")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate(B314_RUN)
    pg.wait_for_selector(".choice", timeout=20000)
    pg.wait_for_timeout(900)
    meas = """async (want) => {
      const qi=order[pos], oo=optionOrder(qi), right=oo.indexOf(QUESTIONS[qi].answer);
      const slot = want==='right' ? right : (right+1)%oo.length;
      const btn=()=>document.querySelector('#stage .qpanel .choice[data-index="'+slot+'"]');
      const parse=c=>c.match(/[\\d.]+/g).map(Number);
      const b0=btn(); const neutral=parse(getComputedStyle(b0).borderTopColor);
      const t0=performance.now(); b0.click(); const out=[]; let rise=null;
      for(let i=0;i<75;i++){ await new Promise(r=>requestAnimationFrame(r)); const b=btn(); const n=document.getElementById('nextbtn');
        if(rise===null && n && !n.hidden && +getComputedStyle(n).opacity>.02) rise=performance.now()-t0;
        if(!b) continue; const cs=getComputedStyle(b); out.push({t:performance.now()-t0, c:parse(cs.borderTopColor), tf:cs.transform}); }
      const fin=out[out.length-1].c, d=c=>Math.hypot(c[0]-neutral[0],c[1]-neutral[1],c[2]-neutral[2]), D=d(fin)||1;
      const half=out.find(o=>d(o.c)/D>=.5);
      let dx=0; out.forEach(o=>{ const m=o.tf.match(/matrix\\(([^)]+)\\)/); if(m) dx=Math.max(dx,Math.abs(+m[1].split(',')[4])); });
      return { half: half?Math.round(half.t):null, dx: +dx.toFixed(2), rise: rise===null?null:Math.round(rise) }; }"""
    res = {"wrong": [], "right": []}
    for _ in range(3):
        res["wrong"].append(pg.evaluate(meas, "wrong")); pg.wait_for_timeout(2800)
        res["right"].append(pg.evaluate(meas, "right")); pg.wait_for_timeout(600)
        pg.evaluate("()=>advance()"); pg.wait_for_timeout(700)
    ctx.close()
    med = lambda xs: sorted(xs)[len(xs) // 2]
    wh = med([x["half"] for x in res["wrong"] if x["half"] is not None] or [999])
    rh = med([x["half"] for x in res["right"] if x["half"] is not None] or [999])
    rise = med([x["rise"] for x in res["right"] if x["rise"] is not None] or [0])
    ndx = max(x["dx"] for x in res["wrong"])
    check("a wrong pick's red is half there within 170ms of the tap (313: 284)", wh <= 170, wh)
    check("a right pick's green is half there within 170ms of the tap (313: 282)", rh <= 170, rh)
    check("the wrong nudge is a quarter softer - 3px at most (313: 4)", 1.5 <= ndx <= 3.2, ndx)
    check("Next starts rising 780-920ms after the tap, as in 311 (313: 500)", 780 <= rise <= 920, rise)


def check_b314_study(br):
    """Build 314: Review's Starred questions star is filled only once there
    is something starred, and stays true after a unit's details change it;
    Learn and Flashcards get their own loading screen, half a second
    shorter than a test's. "that star, just fill it in with color ONCE
    someone actually has a flagged question" and "give flashcards or
    regular review a loading screen ... take the loading time down by half
    a second". Fails on 313: no filled star, no loading screen."""
    print("\n101. build 314: the starred box's star, and LOADING REVIEW / LOADING FLASHCARDS")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const out={};
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          store.flagged = {}; cfg.mode='review'; cfg.units=[]; showSetup(); await wait(700);
          const box=()=>document.querySelector('#stage .pick-flagged-all');
          const star=()=>box().querySelector('.starred-card-star');
          out.empty = { filled: star().classList.contains('is-filled'), fill: (star().querySelector('path')||{}).getAttribute && star().querySelector('path').getAttribute('fill') };
          /* starred inside a unit's details: the box catches up when they close */
          const u = topicsIn(QUESTIONS)[1]; const qi = QUESTIONS.findIndex(q => (q.topic||'').trim() === u.trim());
          const row = [...document.querySelectorAll('#stage label.pick')].find(p => p.querySelector('.pname').textContent.trim() === u.trim());
          openUnitDetail(row, u.trim(), 'review'); await wait(500);
          toggleFlag(qi);
          document.querySelector('.unitdetail-scrim, .unitdetail-backdrop') ? document.querySelector('.unitdetail-scrim, .unitdetail-backdrop').click() : null; await wait(600);
          out.after = { filled: star().classList.contains('is-filled'), sub: box().querySelector('.pcount').textContent, empty: box().classList.contains('is-empty') };
          /* the filled star is the in-test gold, not 308's saturated one */
          const st = [...star().querySelectorAll('stop')].map(s => s.getAttribute('stop-color'));
          out.stops = st;
          /* LOADING REVIEW, from the box */
          const t0 = performance.now(); box().click(); await wait(80);
          const tabs = document.querySelector('.bottomtabs');
          out.rv = { label: (document.getElementById('teststart-label')||{}).textContent, tabsHidden: !tabs || tabs.hidden };
          while(document.getElementById('teststart-overlay')) await wait(15);
          out.rv.ms = Math.round(performance.now() - t0);
          out.rv.screen = !!document.querySelector('.screen-answerreview');
          /* LOADING FLASHCARDS, from the sheet */
          cfg.units=[]; showSetup(); await wait(600);
          row && [...document.querySelectorAll('#stage label.pick')][1].click(); await wait(300);
          document.getElementById('nextbtn').click(); await wait(900);
          cfg.flashcards = true;
          const t1 = performance.now(); document.querySelector('.sheet-begin-btn').click(); await wait(80);
          out.fc = { label: (document.getElementById('teststart-label')||{}).textContent };
          while(document.getElementById('teststart-overlay')) await wait(15);
          out.fc.ms = Math.round(performance.now() - t1); out.fc.screen = !!document.querySelector('.fc-screen');
          cfg.flashcards = false;
          /* a test still has its own 2.5s LOADING TEST */
          cfg.mode='drill'; cfg.units=[topicsIn(QUESTIONS)[1]]; cfg.size=0; cfg.source='all';
          const t2 = performance.now(); beginRun(QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'')===topicsIn(QUESTIONS)[1]).slice(0,5)); await wait(80);
          out.test = { label: (document.getElementById('teststart-label')||{}).textContent };
          while(document.getElementById('teststart-overlay')) await wait(15);
          out.test.ms = Math.round(performance.now() - t2);
          return out; }""")
        ctx.close()
        check("%s with nothing starred, the box's star is the white outline" % label,
              r["empty"]["filled"] is False, r["empty"])
        check("%s starred in a unit's details, the box fills its star and counts it when they close" % label,
              r["after"]["filled"] is True and not r["after"]["empty"] and r["after"]["sub"].startswith("1 question"), r["after"])
        check("%s the filled star is the in-test star's soft gold (#E8C770), not 308's #FFD233" % label,
              "#E8C770" in r["stops"] and "#FFD233" not in r["stops"], r["stops"])
        check("%s the Starred box opens through LOADING REVIEW, ~2s, with the tab bar off it" % label,
              r["rv"]["label"] == "LOADING REVIEW" and r["rv"]["tabsHidden"] and 1850 <= r["rv"]["ms"] <= 2350 and r["rv"]["screen"], r["rv"])
        check("%s flashcards open through LOADING FLASHCARDS, ~2s" % label,
              r["fc"]["label"] == "LOADING FLASHCARDS" and 1850 <= r["fc"]["ms"] <= 2350 and r["fc"]["screen"], r["fc"])
        check("%s and a test keeps LOADING TEST at ~2.5s - half a second longer" % label,
              r["test"]["label"] == "LOADING TEST" and r["test"]["ms"] >= 2400 and r["test"]["ms"] - r["fc"]["ms"] >= 250, (r["test"], r["fc"]["ms"]))


def check_b314_sheet(br):
    """Build 314, the start sheet: the question bank is one switch, Start's
    lighting-up is one crisp beat, and Max says so when it is already
    there. "There's gotta be a better way to do the starred question and
    all questions thing ... Maybe all questions should be default and the
    starred thing should be a button?", "the timing of that pulse is bad
    and it's weak" and "if it's already at that, give a small thing that
    says max time set". On 313 the bank was two boxes, the pop was a
    1.06 scale waiting .5s behind a .6s fill, and a tap on Max at 90 did
    nothing. Fails there."""
    print("\n102. build 314: the bank is one Starred switch; Start lights in one beat; Max says it is set")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async ()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const out={};
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; store.flagged = {};
          cfg.mode='drill'; cfg.units=[]; cfg.size=0; cfg.source='all'; cfg.timer='none'; showSetup(); await wait(1000);
          const tab=document.getElementById('bottomtab-start');
          const pick=[...document.querySelectorAll('.screen-setup .pick')].find(p => /Identity Crimes/.test(p.textContent));
          pick.click(); await wait(30);
          /* the beat, read off the animations themselves (wall-clock frame
             sampling is at the mercy of a loaded machine) */
          const an = tab.getAnimations({ subtree: true });
          const fill = an.find(a => a.animationName === 'start-fill-in'), punch = an.find(a => a.animationName === 'start-ready-punch');
          const tm = a => a ? a.effect.getComputedTiming() : null;
          const peak = punch ? Math.max(...punch.effect.getKeyframes().map(k => { const m = String(k.transform || '').match(/scale\\(([\\d.]+)/); return m ? +m[1] : 1; })) : 0;
          out.start = { fillMs: fill ? tm(fill).duration : null, punchDelay: punch ? tm(punch).delay : null,
                        punchMs: punch ? tm(punch).duration : null, peak };
          await wait(1000);
          /* the sheet: no bank boxes, one switch, off */
          tab.click(); await wait(1000);
          const sheet=document.querySelector('#unitoptions-modal');
          const row=sheet.querySelector('.bank-starred');
          out.bank = { boxes: sheet.querySelectorAll('.bank-opt').length, row: !!row,
                       text: row ? row.querySelector('.otext').firstChild.textContent : null,
                       hint: row ? row.querySelector('.ohint').textContent : null,
                       disabled: row ? row.querySelector('input').disabled : null, source: cfg.source };
          /* starred in this unit: the switch takes the run to them, How many follows */
          const u = 'Identity Crimes', ids = QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u);
          [0, 3, 6].forEach(k => toggleFlag(ids[k]));
          document.querySelector('.unitoptions-modal-scrim')?.click(); await wait(600); tab.click(); await wait(1000);
          const sh2 = document.querySelector('#unitoptions-modal'), row2 = sh2 && sh2.querySelector('.bank-starred');
          out.bank2 = {};
          if(row2){
          out.bank2 = { hint: row2.querySelector('.ohint').textContent, disabled: row2.querySelector('input').disabled };
          row2.click(); await wait(400);
          out.bank2.source = cfg.source;
          out.bank2.howMany = (sh2.querySelector('.howmany-sect .sect-headval') || {}).textContent;
          out.bank2.summary = (sh2.querySelector('.sheet-summary-line') || {}).textContent;
          row2.click(); await wait(400); out.bank2.back = cfg.source;
          out.bank2.howManyBack = (sh2.querySelector('.howmany-sect .sect-headval') || {}).textContent;
          }
          /* All at All: the note was dropped with the bank boxes */
          const note=()=>sh2.querySelector('.slider-topnote');
          sh2.querySelector('.howmany-sect .slider-allbtn').click(); await wait(300); out.allNote = !!note();
          /* Max: a tap that changes the value says nothing; at the top it says so */
          const inp=[...sh2.querySelectorAll('input[type=checkbox]')].find(x=>{ let e=x; for(let k=0;k<4&&e;k++){ e=e.parentElement; if(e && /Time limit/.test(e.textContent) && !/Stopwatch/.test(e.textContent)) return true; } return false; });
          inp && inp.click(); await wait(500);
          const mb=sh2.querySelector('.minutes-sect .slider-maxbtn'); mb.click(); await wait(500); out.maxOnChange = !!note();
          await wait(2400); mb.scrollIntoView({block:'center'}); await wait(300); mb.click(); await wait(300);
          const n2=note(); out.max = n2 ? n2.innerText.replace(/\\n/g,' | ') : null;
          if(n2){ n2.style.pointerEvents='auto'; const rr=n2.getBoundingClientRect(); const hit=document.elementFromPoint((rr.left+rr.right)/2,(rr.top+rr.bottom)/2);
            out.maxVisible = !!hit && (hit===n2 || n2.contains(hit)) && rr.left >= 0 && rr.right <= innerWidth; n2.style.pointerEvents=''; }
          await wait(2600); out.maxGone = !note();
          return out; }""")
        ctx.close()
        s0 = r["start"]
        check("%s Start's beat: a .3s fill, the punch from 180ms, to 1.08+ (313: .6s, .5s, 1.06)" % label,
              s0["fillMs"] is not None and s0["fillMs"] <= 320 and s0["punchDelay"] is not None and s0["punchDelay"] <= 220
              and s0["peak"] >= 1.08, s0)
        b0, b2 = r["bank"], r["bank2"]
        check("%s the bank is one switch, Starred questions only - no All / Starred boxes - off by default" % label,
              b0["boxes"] == 0 and b0["row"] and b0["text"] == "Starred questions only" and b0["source"] == "all", b0)
        check("%s with nothing starred it is greyed and says so" % label,
              b0["disabled"] is True and b0["hint"] == "No starred questions in the selected unit yet", b0)
        check("%s with three starred it says so, turns the run to them, and How many follows" % label,
              b2.get("hint") == "3 starred in the selected unit" and b2.get("disabled") is False and b2.get("source") == "flagged"
              and b2.get("howMany") == "All 3" and b2.get("back") == "all" and b2.get("howManyBack") not in ("All 3", None), b2)
        check("%s All at All shows no note (dropped with the bank boxes)" % label, r.get("allNote") is False, r.get("allNote"))
        check("%s a tap on Max that changes the value shows nothing" % label, r.get("maxOnChange") is False, r.get("maxOnChange"))
        check("%s Max at the top says 'Max time set / 90 minutes', in view and not clipped by its card, then goes" % label,
              r.get("max") == "Max time set | 90 minutes" and r.get("maxVisible") is True and r.get("maxGone") is True,
              (r.get("max"), r.get("maxVisible"), r.get("maxGone")))



def _b314_touch(ctx, pg):
    cdp = ctx.new_cdp_session(pg)
    def T(kind, pts):
        cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [{"x": x, "y": y} for x, y in pts]})
    return T


def check_b314_dragselect(br):
    """Build 314: drag across the unit cards to select them. "being able to
    hold and drop on units to select multiple faster, would be pretty
    sick. Let's do it. Ensure it's done right." Real touch input (CDP),
    so the browser's own scrolling takes part: a drag from a card's circle
    selects every card from it to the finger, a drag from a ticked one
    unticks, a sideways-first drag from a card's body selects too, the
    list scrolls itself near the bottom edge - and a vertical swipe still
    scrolls, a hold still opens the details, a tap still ticks one.
    Fails on 313 (dd6cfae), where a drag selects nothing."""
    import time
    print("\n103. build 314: drag to select units, and nothing that worked before stops working")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        T = _b314_touch(ctx, pg)
        pg.evaluate("""async ()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; localStorage.setItem('class26e.unithold.tip','1');
          cfg.mode='drill'; cfg.units=[]; showSetup(); await wait(900); }""")
        st = lambda: pg.evaluate("()=>[...document.querySelectorAll('.picks label.pick')].map(r=>r.querySelector('input').checked?1:0).join('')")
        clear = lambda: pg.evaluate("()=>{ document.querySelectorAll('.picks label.pick input').forEach(c=>{ c.checked=false; c.closest('.pick').classList.remove('pick-checked'); }); }")
        def to(i, y=260):
            pg.evaluate("([i,y])=>{ const r=[...document.querySelectorAll('.picks label.pick')][i]; window.scrollBy({ top: r.getBoundingClientRect().top - y, behavior: 'instant' }); }", [i, y]); time.sleep(0.3)
        def pt(i, part):
            return pg.evaluate("""([i,part])=>{ const r=[...document.querySelectorAll('.picks label.pick')][i];
              const b=(part==='box'?r.querySelector('.box'):r).getBoundingClientRect(); return part==='box'?[b.left+b.width/2,b.top+b.height/2]:[b.left+b.width*.6,b.top+b.height*.5]; }""", [i, part])
        def line(a, b, n): return [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]
        def drag(pts, hold=0):
            T("touchStart", [pts[0]])
            for p in pts[1:]:
                time.sleep(0.016); T("touchMove", [p])
            if hold: time.sleep(hold)
            T("touchEnd", []); time.sleep(0.4)
        r = {}
        clear(); to(0, 200)
        drag(line(pt(0, "box"), pt(3, "body"), 12)); r["select"] = st()
        to(0, 200); drag(line(pt(0, "box"), pt(1, "body"), 8)); r["deselect"] = st()
        clear(); to(6, 160)
        a = pt(7, "body"); side = (a[0] - 40, a[1])
        drag(line(a, side, 4) + line(side, pt(9, "body"), 8)[1:]); r["body"] = st()
        clear(); to(4); y0 = pg.evaluate("()=>scrollY"); a = pt(5, "body")
        drag(line(a, (a[0], a[1] - 240), 12)); time.sleep(0.5)
        r["scroll"] = { "dy": round(pg.evaluate("()=>scrollY") - y0), "st": st() }
        to(4); a = pt(4, "body"); T("touchStart", [a]); time.sleep(0.7)
        r["hold"] = { "open": pg.evaluate("()=>document.querySelectorAll('.unitdetail').length") > 0 }
        T("touchEnd", []); time.sleep(0.4); r["hold"]["st"] = st()
        pg.evaluate("()=>document.querySelector('.unitdetail-scrim')?.click()"); time.sleep(0.7)
        to(4); a = pt(4, "body"); T("touchStart", [a]); time.sleep(0.05); T("touchEnd", []); time.sleep(0.5); r["tap"] = st()
        clear(); pg.evaluate("()=>window.scrollTo({ top: 0, behavior: 'instant' })"); time.sleep(0.3)
        a = pt(0, "box"); y0 = pg.evaluate("()=>scrollY")
        drag(line(a, (a[0], h - 50), 12), hold=1.3)
        r["auto"] = { "dy": round(pg.evaluate("()=>scrollY") - y0), "n": st().count("1") }
        ctx.close()
        n = len(r["select"])
        check("%s a drag from a card's circle to the fourth card ticks those four" % label, r["select"] == "1111" + "0" * (n - 4), r["select"])
        check("%s a drag from a ticked card unticks back to where the finger is" % label, r["deselect"] == "0011" + "0" * (n - 4), r["deselect"])
        check("%s a sideways-first drag from a card's body selects too" % label,
              r["body"] == "0" * 7 + "111" + "0" * (n - 10), r["body"])
        check("%s a vertical swipe on the cards still scrolls and ticks nothing" % label,
              abs(r["scroll"]["dy"]) > 100 and r["scroll"]["st"] == "0" * n, r["scroll"])
        check("%s a hold still opens the unit's details and ticks nothing" % label,
              r["hold"]["open"] and r["hold"]["st"] == "0" * n, r["hold"])
        check("%s a tap still ticks the one card" % label, r["tap"] == "0" * 4 + "1" + "0" * (n - 5), r["tap"])
        check("%s held at the bottom edge the list scrolls itself and keeps selecting" % label,
              r["auto"]["dy"] > 40 and r["auto"]["n"] >= 4, r["auto"])


def check_b314_slider_release(br):
    """Build 314: All and Max light up when the finger LETS GO, at once.
    "just make sure it's a little better so it activates right when I stop
    touching it ... and not that delay thing it has". On 313 the effect
    fired on the first move below the top, under the finger, and its punch
    waited .5s after that. Real touch input (CDP). Fails there."""
    import time
    print("\n104. build 314: All and Max light up on the release, with no delay")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        T = _b314_touch(ctx, pg)
        pg.evaluate("""async ()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
          store.seenUnitSelectTour = true; cfg.mode='drill'; cfg.units=[]; cfg.size=0; showSetup(); await wait(800);
          [...document.querySelectorAll('.picks label.pick')].slice(0,2).forEach(p=>p.click()); await wait(300); document.getElementById('nextbtn').click(); await wait(1000);
          const sheet=document.querySelector('#unitoptions-modal');
          const inp=[...sheet.querySelectorAll('input[type=checkbox]')].find(x=>{ let e=x; for(let k=0;k<4&&e;k++){ e=e.parentElement; if(e && /Time limit/.test(e.textContent) && !/Stopwatch/.test(e.textContent)) return true; } return false; });
          inp && inp.click(); await wait(400); sheet.querySelector('.minutes-sect .slider-maxbtn').click(); await wait(700); }""")
        out = {}
        for name, sel, bsel in [("All", ".howmany-sect input.slider", ".howmany-sect .slider-allbtn"),
                                ("Max", ".minutes-sect input.slider", ".minutes-sect .slider-maxbtn")]:
            g = pg.evaluate("""([sel,bsel])=>{ const s=document.querySelector('#unitoptions-modal '+sel); s.scrollIntoView({block:'center'});
              const r=s.getBoundingClientRect(); const b=document.querySelector('#unitoptions-modal '+bsel);
              /* the first thing the release dispatches is pointerup; read the button just before the app hears it */
              window.__rel={}; document.addEventListener('pointerup', ()=>{ __rel.t=performance.now(); __rel.before={ lit:b.classList.contains('just-ready'), on:b.classList.contains('on') };
                setTimeout(()=>{ const a=b.getAnimations({subtree:true}); const p=a.find(x=>x.animationName==='start-ready-punch');
                  __rel.after={ lit:b.classList.contains('just-ready')||b.classList.contains('ready-pop'), on:b.classList.contains('on'), delay:p?p.effect.getComputedTiming().delay:null }; }, 30); }, { capture:true, once:true });
              return [r.right-12, r.top+r.height/2, r.left, r.width]; }""", [sel, bsel])
            time.sleep(0.4)
            x0, y = g[0], g[1]; x1 = g[2] + g[3] * .5
            T("touchStart", [(x0, y)])
            for k in range(1, 11):
                time.sleep(0.016); T("touchMove", [(x0 + (x1 - x0) * k / 10, y)])
            time.sleep(0.2); T("touchEnd", []); time.sleep(0.5)
            out[name] = pg.evaluate("()=>__rel")
        ctx.close()
        for name in ("All", "Max"):
            o = out.get(name) or {}
            b, a = o.get("before") or {}, o.get("after") or {}
            check("%s %s stays quiet while the finger is still down below the top" % (label, name),
                  b.get("lit") is False and b.get("on") is True, o)
            check("%s %s lights the moment the finger lets go, its punch with no delay" % (label, name),
                  a.get("lit") is True and a.get("on") is False and a.get("delay") == 0, o)


# --------------------------------------------------------------------------
SPOT_PROBE = """async (expr) => { const wait = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('.rs-spot').forEach(s => s.remove());
  const item = (0, eval)('(' + expr + ')');
  const h = playUnlockSpotlight(item, 1, 1, () => {});
  const spot = document.querySelector('.rs-spot'), card = spot.querySelector('.rs-spot-card'), art = spot.querySelector('.rs-spot-art');
  const scaleOf = el => { const t = getComputedStyle(el).transform; if(!t || t === 'none') return [1, 1];
    const m = t.match(/matrix\\(([^)]+)\\)/); if(!m) return [9, 9]; const v = m[1].split(',').map(Number); return [Math.hypot(v[0], v[1]), Math.hypot(v[2], v[3])]; };
  const samples = [];
  const t0 = performance.now();
  for(let i = 0; i < 26; i++){ await wait(70);
    samples.push({ t: Math.round(performance.now() - t0), card: scaleOf(card), art: scaleOf(art), cf: getComputedStyle(card).filter, ao: +getComputedStyle(art).opacity }); }
  await wait(600);
  const cs = getComputedStyle(card), ba = spot.querySelector('.rs-spot-bannerart');
  const out = { samples,
    color: spot.style.getPropertyValue('--spot-color').trim(), color2: spot.style.getPropertyValue('--spot-color2').trim(),
    ground: cs.backgroundColor, cls: spot.className,
    strip: (spot.querySelector('.rs-spot-strip') || {}).className || null,
    artAnims: art.getAnimations().map(a => a.animationName || a.id),
    cardAnims: card.getAnimations().map(a => a.animationName || a.id),
    sheen: ba ? getComputedStyle(ba, '::after').animationName : null,
    spotBefore: getComputedStyle(spot, '::before').animationName,
    use: !!spot.querySelector('.rs-spot-use') || /use this effect/i.test(spot.textContent) };
  h.stop(); return out; }"""


def check_b314_unlocks(br):
    """Build 314: "the void, umbra, horizon and genesis banners are pretty
    mid ... the pop up for void for that banner did not match the banner,
    it probably should have been black toned? I thought all the unlocks
    would match their color theme ... but also different unlocks had a
    similar but different type of pop up? ... it like made the banner do
    an effect when the pop up came up, not a fan of that ... Not sure about
    the unlock stuff within the pops should do that type of effect where
    they start off tiny ... and then getting big"; "the pop up showed the
    button to 'use this effect' let's remove that"; and the UFO, the tree,
    the bubbles. Fails on 313, which has none of it."""
    print("\n314u. unlock pop-ups in their own colours and calm; the flare banners; the UFO's scan and exit; the tree's edges; the bubbles' pops")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    # everything held and already announced, on a screen with no unlock
    # queue of its own, so nothing but the card under test is ever up
    pg.evaluate("""() => { window.isLockedCharacter = id => false; store.lifetime.perfectTests = 600;
      const u = ensureUnlocksShown(); u.banners = BANNERS.map(b => b.id); u.chars = AVATAR_CHARACTERS.map(c => c.id); u.fx = HUNDO_FX.map(d => d.id);
      store.flareHintsShown = ['umbra', 'singularity', 'genesis']; saveStore(); showAppearance(); }""")
    pg.wait_for_timeout(600)
    probe = lambda expr: pg.evaluate(SPOT_PROBE, expr)
    void = probe("bannerUnlockItem('flare_void')")
    koi = probe("bannerUnlockItem('tests500')")
    umbra = probe("bannerUnlockItem('flare_umbra')")
    rankb = probe("bannerUnlockItem('adept_rank')")
    badge = probe("({ kind: 'badge', unit: 'Identity Crimes', kicker: 'Badge earned', name: 'Identity Crimes badge', sub: '', color: '#D8E2EC', art: () => buildUnitBadgeSVG('Identity Crimes', true) })")
    fx = probe("hundoFxUnlockItem('fireworks')")
    char = probe("characterUnlockItem('voidwalker')")
    exp = pg.evaluate("""() => ({ void: bannerTintOf('flare_void'), koi: bannerTintOf('tests500'), umbra: bannerTintOf('flare_umbra'),
      badge: badgeThemeFor('Identity Crimes').p }).valueOf()""")
    lum = lambda c: (lambda v: (.2126 * v[0] + .7152 * v[1] + .0722 * v[2]) / 255)([float(x) for x in re.findall(r"[\d.]+", c)[:3]]) if c else 1
    hexlow = lambda h: (h or "").strip().lower()
    check("the Void banner's pop-up is BLACK-toned - its card's own ground near black (\"it probably should have been black toned\")",
          lum(void.get("ground")) < .03, void.get("ground"))
    check("and every banner's pop-up takes that banner's own colours (not one pale grey for all): Void, Koi Pond, Umbra",
          hexlow(void.get("color")) == hexlow(exp["void"][0]) and hexlow(koi.get("color")) == hexlow(exp["koi"][0]) and hexlow(umbra.get("color")) == hexlow(exp["umbra"][0])
          and hexlow(koi.get("color")) != "#e9eef6", {"void": void.get("color"), "koi": koi.get("color"), "umbra": umbra.get("color"), "expected": exp})
    check("a badge's pop-up is in that badge's enamel colour", hexlow(badge.get("color")) == hexlow(exp["badge"]), {"got": badge.get("color"), "want": exp["badge"]})
    check("the Void character's pop-up is black-toned too, in the same colours as its banner's (the two arrive back to back)",
          lum(char.get("ground")) < .03 and hexlow(char.get("color")) == hexlow(void.get("color")) and hexlow(char.get("color2")) == hexlow(void.get("color2")),
          {k: (char.get(k), void.get(k)) for k in ("ground", "color", "color2")})
    check("each KIND keeps its own shape: a challenge banner the striped strip, a rank banner the rank-reward chevron, a badge none",
          koi.get("strip") == "rs-spot-strip" and "is-rankreward" in (rankb.get("strip") or "") and badge.get("strip") is None,
          {"koi": koi.get("strip"), "rank": rankb.get("strip"), "badge": badge.get("strip")})
    check("a banner's pop-up does nothing TO the banner: no unroll, no sheen across it, no jolt, no flash",
          all(a in ("rs-artpop",) for a in void.get("artAnims") or []) and (void.get("sheen") in (None, "none"))
          and "is-epic" not in (void.get("cls") or "") and not any("jolt" in a for a in void.get("cardAnims") or []),
          {k: void.get(k) for k in ("artAnims", "sheen", "cls", "cardAnims")})
    worst = lambda r, k: max(max(abs(s[k][0] - 1), abs(s[k][1] - 1)) for s in r.get("samples") or [{"card": [9, 9], "art": [9, 9]}])
    check("every pop-up's card and the thing in it arrive at FULL SIZE - no growing from small (sampled every 70ms through the entrance)",
          all(worst(r, "card") < .002 and worst(r, "art") < .002 for r in (void, koi, badge, fx, char)),
          {n: (round(worst(r, "card"), 3), round(worst(r, "art"), 3)) for n, r in (("void", void), ("koi", koi), ("badge", badge), ("fx", fx), ("char", char))})
    check("and they still arrive - the card and the art fade in", all((r.get("samples") or [{}])[-1].get("ao", 0) > .95 for r in (void, koi, badge, fx, char)),
          [round((r.get("samples") or [{}])[-1].get("ao", 0), 2) for r in (void, koi, badge, fx, char)])
    check("no blur or brightness filter on the card's way in", all(s["cf"] in ("none", "") for r in (void, koi, badge) for s in r["samples"]), void["samples"][:3])
    check("a hundo effect's pop-up has no \"Use this effect\" button", fx.get("use") is False, fx.get("use"))
    # the flare banners: Void is black, and its colours on the Profile card follow
    r = pg.evaluate("""async () => { const out = {};
      const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px;z-index:9999';
      const a = buildBannerArt('flare_void'); a.style.cssText = 'position:absolute;inset:0;'; box.appendChild(a); document.body.appendChild(box);
      return true; }""")
    pg.wait_for_timeout(900)
    from PIL import Image
    im = Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": 0, "width": 480, "height": 180}))).convert("L")
    px = list(im.getdata()); dark = sum(1 for v in px if v < 22) / len(px)
    tint = pg.evaluate("() => bannerTintOf('flare_void')")
    sat = (lambda h: (lambda r, g, b: (max(r, g, b) - min(r, g, b)) / max(1, max(r, g, b)))(*[int(h[i:i + 2], 16) for i in (1, 3, 5)]))(tint[0])
    check("the Void banner is black: most of it near-black (%.0f%% under 22/255)" % (dark * 100), dark > .6, round(dark, 3))
    check("and the colours it hands the Profile card are steel, not the old orange glow", sat < .3, tint)
    ctx.close()

    # --- the hundo effect tiles take taps like everything else in Customize
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      store.lifetime.perfectTests = 120; store.hundoFx = 'confetti'; saveStore(); showCustomize('fx'); await wait(500);
      const tile = id => document.querySelector('.hfx-opt[data-fx="' + id + '"]');
      const cards = () => document.querySelectorAll('.unlock-card').length;
      const fw = HUNDO_FX[1].id;
      tile(fw).scrollIntoView({ block: 'center', behavior: 'instant' }); await wait(100);
      tile(fw).click(); await wait(250);
      out.firstPick = store.hundoFx; out.firstCards = cards();
      tile(fw).click(); await wait(500);
      out.secondCards = cards(); out.secondLive = !!document.querySelector('.unlock-card-fx .hfx-mock');
      document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); await wait(100);
      /* a hold on one that is not picked: its card, and the pick stays */
      const t = tile('worldtree'), rc = t.getBoundingClientRect(), x = rc.left + rc.width / 2, y = rc.top + rc.height / 3;
      const ev = (type) => t.dispatchEvent(new PointerEvent(type, { bubbles: true, clientX: x, clientY: y, pointerId: 1, button: 0, isPrimary: true }));
      ev('pointerdown'); await wait(UNIT_HOLD_MS + 200); ev('pointerup'); t.click(); await wait(300);
      out.holdCards = cards(); out.holdPick = store.hundoFx;
      document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); await wait(100);
      tile('ufo').click(); await wait(300);
      out.lockedCard = cards(); out.lockedPick = store.hundoFx;
      return out; }""")
    check("hundo effect tiles: a tap on one that is not picked PICKS it and opens nothing (\"if it's not selected and you tap it, that's selecting\")",
          r.get("firstCards") == 0 and r.get("firstPick") == pg.evaluate("() => HUNDO_FX[1].id"), r)
    check("a tap on the picked one opens its card, the effect playing on its miniature results screen, as before", r.get("secondCards") == 1 and r.get("secondLive"), r)
    check("a hold always opens the card, and picks nothing (\"holding it down always does the details\")", r.get("holdCards") == 1 and r.get("holdPick") == r.get("firstPick"), r)
    check("a locked one opens its card and picks nothing, as a locked character or banner does", r.get("lockedCard") == 1 and r.get("lockedPick") == r.get("firstPick"), r)
    ctx.close()

    # --- a secret flare banner nobody holds: frosted glass, still moving, "Unlock to see"
    for w, h in ((440, 956), (834, 1194)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=1)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          showCustomize('banner'); await wait(400);
          const t = document.querySelector('.banner-opt[data-banner="flare_umbra"]');
          t.scrollIntoView({ block: 'center', behavior: 'instant' }); await wait(1800);
          const art = t.querySelector('.banner-opt-art'), still = art.querySelector('.bnr-veil-still');
          out.veiled = art.classList.contains('is-veiled');
          out.label = ((art.querySelector('.bnr-veil') || {}).textContent || '').trim();
          /* a pre-blurred picture of the banner (40 x 15, softened, scaled up), never the live banner under glass */
          out.still = !!still && still.classList.contains('is-ready') && /^url\("data:image\/png/.test(getComputedStyle(still).backgroundImage);
          out.live = art.querySelectorAll('.bnr').length;
          out.moving = [...art.querySelectorAll('.bnr-veil-still, .bnr-veil-glow')].reduce((n, e) => n + e.getAnimations().filter(a => a.playState === 'running').length, 0);
          out.qmark = getComputedStyle(art, '::after').content;
          const rc = art.getBoundingClientRect(); out.rect = [rc.left, rc.top, rc.width, rc.height];
          /* the tap card */
          t.click(); await wait(700);
          const ca = document.querySelector('.unlock-card-banner .unlock-card-art'), cb = ca && ca.querySelector('.bnr');
          out.cardVeiled = !!ca && ca.classList.contains('is-veiled') && !cb && !!ca.querySelector('.bnr-veil-still') && /unlock to see/i.test(ca.textContent);
          document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
          /* a held one is not veiled */
          window.isLockedCharacter = id => false; showCustomize('banner'); await wait(300);
          const t2 = document.querySelector('.banner-opt[data-banner="flare_umbra"]');
          out.heldVeiled = !!t2 && t2.querySelector('.banner-opt-art').classList.contains('is-veiled');
          return out; }""")
        tag = "%dx%d" % (w, h)
        check("secret flare banner, locked, %s: frosted glass over a blurred picture of it (no live banner under the glass), moving gently, labelled \"Unlock to see\", no \"?\"" % tag,
              r.get("veiled") and r.get("still") and r.get("live") == 0 and r.get("moving", 0) >= 2 and r.get("label", "").lower() == "unlock to see" and r.get("qmark") in ("none", "normal", ""), r)
        check("secret flare banner, locked, %s: the card a tap opens shows it the same way" % tag, r.get("cardVeiled"), r.get("cardVeiled"))
        check("secret flare banner, held, %s: no veil" % tag, r.get("heldVeiled") is False, r.get("heldVeiled"))
        ctx.close()

    # --- reduce motion: the UFO plays nothing and still leaves the box in its colours; a pop-up is there at once
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("async () => { store.lifetime.perfectTests = 600; store.hundoFx = 'ufo'; theme.reduceMotion = true; try{ applyTheme(); }catch(e){} saveStore(); " + FX_RUN + """
      await wait(1500); const g = document.querySelector('.rs-grade');
      const out = { layers: document.querySelectorAll('.hfx-layer, .hfx-box').length, tinted: !!g && g.classList.contains('hfx-tinted') };
      showAppearance(); await wait(200);
      const h = playUnlockSpotlight(bannerUnlockItem('flare_genesis'), 1, 1, () => {}); await wait(150);
      const c = document.querySelector('.rs-spot-card'); out.cardOpacity = c ? parseFloat(getComputedStyle(c).opacity) : 0; h.stop();
      return out; }""")
    check("reduce motion: the UFO plays nothing on a 100%, the box still takes its colours, and a pop-up's card is there at once",
          r.get("layers") == 0 and r.get("tinted") and r.get("cardOpacity", 0) > .99, r)
    ctx.close()

    # --- the UFO: the scan, the lock, the score taken up, the warp, the marks
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("async () => { store.lifetime.perfectTests = 600; store.hundoFx = 'ufo'; saveStore(); " + FX_RUN + """
      const out = {}; if(!window.__fxAt) return out;
      /* timed by the saucer's own animation clock: on a loaded machine the
         page's timers and its animations drift apart by a few hundred ms */
      for(let i = 0; i < 40 && !document.querySelector('.hfx-saucer'); i++) await wait(50);
      const sa = document.querySelector('.hfx-saucer').getAnimations()[0];
      const until = async ms => { for(let i = 0; i < 400 && (sa.currentTime || 0) < ms; i++) await wait(16); };
      const op = el => { if(!el) return -1; let o = 1; for(let e = el; e && e !== document.body; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return o; };
      await until(4650); out.scan = op(document.querySelector('.rs-grade .hfx-ufo-scanbar'));
      await until(5450); out.lock = op(document.querySelector('.rs-grade .hfx-ufo-lock'));
      await until(5820);
      const gs = [...document.querySelectorAll('.hfx-ufo-ghost')], g = document.querySelector('.rs-grade'), gr = g.getBoundingClientRect();
      out.ghosts = gs.length;
      out.ghostUp = gs.map(e => { const r = e.getBoundingClientRect(); return Math.round(r.top + r.height / 2 - gr.top); });
      await until(6120); out.warp = op(document.querySelector('.hfx-ufo-warp'));
      await until(6500); out.marks = op(document.querySelector('.rs-grade .hfx-ufo-marks'));
      const u = document.querySelector('.hfx-saucer'); out.saucerGone = u ? op(u) : 0;
      return out; }""")
    check("UFO: once down, a bar of its light SCANS the 100%%, and brackets lock on round it", r.get("scan", -1) > .5 and r.get("lock", -1) > .5, r)
    check("UFO: on the way out it takes the score up the beam - a copy of the 100%% rising above the box's top edge", r.get("ghosts") == 2 and min(r.get("ghostUp") or [99]) < -10, r)
    check("UFO: and goes in a warp, leaving its landing marks glowing on the box", r.get("warp", -1) > .3 and r.get("marks", -1) > .3 and r.get("saucerGone", 1) < .05, r)
    ctx.close()

    # --- Fireworks: nothing of the show is drawn below the 100% box's top
    # edge. The box is lifted over the sky but its glass is see-through, so
    # the gold willow's drips and the embers read as streaks down behind the
    # number. Read off the canvas's own pixels, every 150ms through the part
    # of the show that hangs low.
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("async () => { store.lifetime.perfectTests = 600; store.hundoFx = 'fireworks'; theme.muteBanners = true; saveStore(); " + FX_RUN + """
      if(!window.__fxAt) return null;
      const out = { below: [], above: [] };
      for(let i = 0; i < 40; i++){
        const t = performance.now() - window.__fxAt; if(t > 6200) break;
        const cv = document.querySelector('.hfx-layer .hfx-fw-sky'), g = document.querySelector('.rs-grade');
        if(cv && g && t > 2600){
          const cr = cv.getBoundingClientRect(), gr = g.getBoundingClientRect(), k = cv.width / cr.width;
          const y0 = Math.ceil((gr.top - cr.top + 1) * k), y1 = Math.floor((gr.bottom - cr.top) * k), x0 = Math.ceil((gr.left - cr.left) * k), x1 = Math.floor((gr.right - cr.left) * k);
          const lit = (ya, yb) => { if(yb <= ya) return 0; const d = cv.getContext('2d').getImageData(x0, ya, x1 - x0, yb - ya).data; let n = 0; for(let j = 3; j < d.length; j += 4) if(d[j] > 8) n++; return n; };
          out.below.push(lit(y0, y1)); out.above.push(lit(Math.max(0, y0 - Math.round(260 * k)), y0 - Math.round(12 * k)));
        }
        await wait(150);
      }
      return out; }""")
    check("Fireworks: nothing of the show is drawn over the 100%% box (willow drips, embers) - the sky stops at its top edge, and is still lit above it",
          r and r["below"] and max(r["below"]) == 0 and max(r["above"]) > 50, r and {"below": max(r["below"] or [0]), "above": max(r["above"] or [0]), "n": len(r["below"])})
    ctx.close()

    # --- the UFO's tile: the saucer is whole inside the tile, not cut by its top edge
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { showCustomize('fx'); await new Promise(r => setTimeout(r, 400));
      const st = document.querySelector('.hfx-opt[data-fx="ufo"] .hfx-stage'), svg = st && st.querySelector('svg');
      if(!svg) return null; const dome = [...svg.querySelectorAll('path')].find(p => /url\\(#[^)]*dome\\)/.test(p.getAttribute('fill') || ''));
      if(!dome) return { dome: false }; const a = st.getBoundingClientRect(), b = dome.getBoundingClientRect();
      return { dome: true, gap: Math.round((b.top - a.top) * 10) / 10 }; }""")
    check("the UFO's Customize tile shows its saucer whole - the dome clear of the tile's top edge", r and r.get("dome") and r.get("gap", 0) >= 4, r)
    ctx.close()

    # --- Bubbles: every glass hero meant to pop does pop
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("async () => { store.lifetime.perfectTests = 600; store.hundoFx = 'bubbles'; saveStore(); " + FX_RUN + """
      if(!window.__fxAt) return null;
      /* each one's own clock: its path has run and it has had its pop */
      for(let i = 0; i < 40 && !document.querySelector('.hfx-gb.is-pop'); i++) await wait(50);
      const heroes = [...document.querySelectorAll('.hfx-gb.is-pop')];
      const op = el => { let o = 1; for(let e = el; e && e !== document.body; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return o; };
      /* watched while they are in the page: each must go out (its pop)
         before the layer is taken away */
      const popped = heroes.map(() => false), seen = heroes.map(() => false), lastO = heroes.map(() => 1);
      for(let i = 0; i < 240 && heroes.some((h, j) => !popped[j] && h.isConnected); i++){
        heroes.forEach((h, j) => { if(!h.isConnected || popped[j]) return; const g = h.querySelector('.hfx-glass'); const o = g ? op(g) : 1;
          lastO[j] = Math.round(o * 100) / 100; if(o > .6) seen[j] = true; else if(o < .05 && seen[j]) popped[j] = true; });
        await wait(40); }
      return { n: heroes.length, popped, seen, last: lastO, at: Math.round(performance.now() - window.__fxAt) }; }""")
    check("Bubbles: the glass bubbles that pop DO pop once their path has run - none left sitting on the cards until the layer is cut",
          r and r.get("n", 0) >= 1 and all(r.get("popped") or [False]), r)
    ctx.close()

    # --- World Tree: the wood meets every card's edge and never crosses into
    # one. Measured in PIXELS: at 5.8s every animation is held, the page is
    # shot with only the tree's wood showing and again with nothing, and the
    # difference is the wood as drawn - clip-paths, rotations and all.
    from PIL import Image, ImageChops
    for w, h, units in ((440, 956, "single"), (834, 1194, "single"), (440, 956, "multi"), (375, 667, "single")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        run = FX_RUN if units == "single" else FX_RUN.replace("cfg.units = ['Identity Crimes']", "cfg.units = ['Identity Crimes', 'Racial Profiling', 'Victims of Crime']") \
            .replace("QUESTIONS[i].topic.trim() === 'Identity Crimes'", "['Identity Crimes', 'Racial Profiling', 'Victims of Crime'].indexOf(QUESTIONS[i].topic.trim()) >= 0")
        # muteBanners: an unrelated unlock (a time-of-day banner) must not
        # cover the screen being measured; the effect does not read it
        r = pg.evaluate("async () => { store.lifetime.perfectTests = 600; store.hundoFx = 'worldtree'; theme.muteBanners = true; saveStore(); " + run + """
          for(let i = 0; i < 300 && !window.__fxAt; i++) await wait(100);
          if(!window.__fxAt) return null; const d = 5800 - (performance.now() - window.__fxAt); if(d > 0) await wait(d);
          document.getAnimations().forEach(a => { try{ a.pause(); }catch(e){} });
          /* and the reveal's scroll held where it is, so the shots and the rects agree */
          window.scrollTo({ top: window.scrollY, behavior: 'instant' }); window.__holdY = window.scrollY;
          window.addEventListener('scroll', () => window.scrollTo({ top: window.__holdY, behavior: 'instant' }));
          await wait(120);
          const layer = document.querySelector('.hfx-layer.hfx-worldtree');
          if(!layer) return { missing: true, fx: window.__fxId, at: Math.round(performance.now() - window.__fxAt), spot: (document.querySelector('.rs-spot') || {}).className || null,
            others: [...document.querySelectorAll('.hfx-layer, .confetti-layer')].map(e => e.className) };
          const cards = [...document.querySelectorAll('.rs-screen > .rs-card')].map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; });
          const gr = document.querySelector('.rs-screen > .rs-grade').getBoundingClientRect();
          const head = document.querySelector('.rs-screen > .rs-head');
          const xp = document.querySelector('.rs-screen > .rs-xp').getBoundingClientRect();
          const crownBase = [...document.querySelectorAll('.hfx-layer.hfx-worldtree .hfx-branch.is-trunk')].map(e => Math.round((e.getBoundingClientRect().bottom - xp.top) * 10) / 10);
          const st = document.createElement('style'); st.id = '__woodonly';
          st.textContent = 'body *{ visibility:hidden !important; } .hfx-seg.is-wood{ visibility:visible !important; }';
          document.head.appendChild(st);
          return { cards, gradeTop: gr.top, headOver: !!head && head.classList.contains('hfx-over'), crownBase, n: document.querySelectorAll('.hfx-layer.hfx-worldtree .hfx-seg.is-wood').length }; }""")
        tag = "%dx%d %s" % (w, h, units)
        if not r or r.get("missing"):
            check("World Tree %s: it plays" % tag, False, r); ctx.close(); continue
        A = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        pg.evaluate("() => { document.getElementById('__woodonly').textContent = 'body *{ visibility:hidden !important; }'; }")
        B = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        m = ImageChops.difference(A, B).convert("L").point(lambda v: 255 if v > 24 else 0)
        px = m.load(); W, H = m.size
        worst = 0; bad = 0
        for c in r["cards"]:
            x0, y0, x1, y1 = [int(round(v)) for v in c]
            for y in range(max(0, y0 + 1), min(H, y1 - 1)):
                for x in range(max(0, x0 + 1), min(W, x1 - 1)):
                    if px[x, y]:
                        bad += 1; worst = max(worst, min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y))
        # the trunk in each gap between two stacked cards: wood on the row
        # touching the upper card and on the row touching the lower one
        gaps = []
        cs = sorted(r["cards"], key=lambda c: c[1])
        for a, b in zip(cs, cs[1:]):
            # the trunk climbs from the 100% box to the XP card: the gaps between those
            if b[1] - a[3] < 4 or b[1] > r["gradeTop"] + 1: continue
            # only a gap that is on the screen can be read off the shot (the
            # reveal's scroll can leave the lowest one under the fold)
            if a[3] < 0 or b[1] >= H - 1: continue
            cx = int((a[0] + a[2]) / 2)
            row = lambda y: sum(1 for x in range(max(0, cx - 60), min(W, cx + 60)) if 0 <= y < H and px[x, y])
            gaps.append([max(row(int(a[3])), row(int(a[3]) + 1)), max(row(int(b[1]) - 1), row(int(b[1])))])
        check("World Tree %s: no wood is drawn inside a card - %d pixel(s), deepest %dpx" % (tag, bad, worst), r["n"] > 3 and worst <= 1, {"pieces": r["n"], "bad": bad, "worst": worst})
        check("World Tree %s: in every gap between cards the trunk reaches both edges (wood pixels on the rows touching each)" % tag,
              gaps and all(g[0] >= 6 and g[1] >= 6 for g in gaps), gaps)
        check("World Tree %s: the crown rises from the XP card's top edge, not from inside it, and the header is over the crown" % tag,
              r["headOver"] and r["crownBase"] and all(-3 <= b <= 2.5 for b in r["crownBase"][:1]), {k: r[k] for k in ("headOver", "crownBase")})
        ctx.close()


def check_b315_customize(br):
    """Build 315: Customize is a summary - your name, then "Your look" in
    the Name's own header bar and four rows (Character, Banner, Theme
    color, Hundo effect) showing what you have on - and each row opens
    that thing's own page under the same bar, with its count. Written
    against build 314's single long page, where every check here fails."""
    print("\n315cz. Customize: a summary of what you wear, a page for each")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async () => { const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
          try{
          /* one character held but never looked at, so exactly one row is "new" */
          const held = AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy && !isLockedCharacter(c.id)).map(c => c.id);
          ensureSeenUnlocks();
          const fresh = held.find(id => id !== store.avatarChar);
          store.seenUnlocks.chars = held.filter(id => id !== fresh);
          store.seenUnlocks.banners = BANNERS.filter(b => bannerEarned(b.id)).map(b => b.id);
          store.seenUnlocks.themes = ACCENTS.filter(a => !isLockedAccent(a));
          store.seenUnlocks.fx = HUNDO_FX.filter(d => hundoFxEarned(d.id)).map(d => d.id);
          out.fresh = fresh;
          /* Profile's own button - it hands showCustomize its click event */
          showProfile('profile'); await wait(500);
          const btn = [...document.querySelectorAll('.profile-edit-btn')].find(b => /custom/i.test(b.textContent));
          if(btn) btn.click(); else showCustomize(new Event('click'));
          await wait(900);
          const panel = () => document.querySelector('#stage > .screen-customize');
          const rows = () => [...document.querySelectorAll('.screen-customize .cz-row')];
          out.back = (document.querySelector('.screen-customize .back-link') || {}).textContent || '';
          out.rows = rows().map(r => r.dataset.page);
          out.grids = document.querySelectorAll('.screen-customize :is(.swatches, .banner-grid, .avatarchar-grid, .hfx-grid)').length;
          const bars = [...document.querySelectorAll('.screen-customize .slab.motion-summary')];
          out.bars = bars.map(b => b.textContent.trim());
          const bg = b => getComputedStyle(b).backgroundImage + '|' + getComputedStyle(b).borderRadius;
          out.sameBar = bars.length === 2 && bg(bars[0]) === bg(bars[1]);
          const box = el => { if(!el) return null; const r = el.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; };
          const pick = k => document.querySelector('.cz-row[data-page="' + k + '"] .cz-pick');
          out.char = { box: box(pick('character')), avatar: !!(pick('character') || document).querySelector('.rank-avatar[data-char="' + store.avatarChar + '"]') };
          out.banner = box(pick('banner'));
          const tdot = pick('theme') && pick('theme').querySelector('.dot');
          out.theme = { box: box(pick('theme')), swirl: !!tdot && document.getAnimations().some(a => a.animationName === 'pf-swirl' && a.effect && a.effect.target === tdot && a.effect.pseudoElement === '::before') };
          const st = pick('fx') && pick('fx').querySelector('.hfx-stage');
          out.fx = { box: box(pick('fx')), id: st ? st.dataset.fx : null, inUse: hundoFxInUse(), pct: st ? (st.querySelector('.hfx-stage-pct') || {}).textContent : null };
          out.values = rows().map(r => (r.querySelector('.cz-value') || {}).textContent);
          out.counts = rows().map(r => (r.querySelector('.cz-count') || {}).textContent);
          out.news = rows().map(r => (r.querySelector('.cz-new') || {}).textContent || '');
          /* each row opens its page, under the bar, and Back comes home */
          const OPT = { character: '.avatarchar-option', banner: '.banner-opt', theme: '.swatch', fx: '.hfx-opt' };
          /* the character page is one grid per group (free, ranks, secrets...),
             so "only its grid" is no grid of any OTHER kind, and at least one of its own */
          const GRID = { character: '.avatarchar-grid', banner: '.banner-grid', theme: '.swatches', fx: '.hfx-grid' };
          out.pages = [];
          for(const k of ['character', 'banner', 'theme', 'fx']){
            const row = document.querySelector('.cz-row[data-page="' + k + '"]');
            const want = row ? (row.querySelector('.cz-count') || {}).textContent : null;
            const label = row ? (row.querySelector('.cz-label') || {}).textContent : null;
            if(row) row.click(); await wait(700);
            const p = panel();
            const opts = [...document.querySelectorAll('.screen-customize ' + OPT[k])];
            const barEl = document.querySelector('.screen-customize .cz-bar');
            out.pages.push({ k, isPage: !!p && p.classList.contains('cz-page-' + k),
              title: barEl ? (barEl.querySelector('.cz-bar-title') || {}).textContent : null, label,
              barCount: barEl ? (barEl.querySelector('.cz-bar-count') || {}).textContent : null, rowCount: want,
              grid: opts.filter(o => !o.classList.contains('locked')).length + ' of ' + opts.length,
              own: document.querySelectorAll('.screen-customize ' + GRID[k]).length,
              others: document.querySelectorAll('.screen-customize :is(' + Object.keys(GRID).filter(g => g !== k).map(g => GRID[g]).join(', ') + ')').length,
              back: (document.querySelector('.screen-customize .back-link') || {}).textContent || '' });
            const bl = document.querySelector('.screen-customize .back-link'); if(bl) bl.click(); await wait(500);
          }
          out.backHome = rows().length;
          /* a new pick shows on its row */
          document.querySelector('.cz-row[data-page="character"]').click(); await wait(700);
          const other = [...document.querySelectorAll('.screen-customize .avatarchar-option:not(.locked):not(.selected)')][0];
          if(other){ other.click(); await wait(400); }
          out.picked = store.avatarChar;
          document.querySelector('.screen-customize .back-link').click(); await wait(500);
          out.pickedRow = (document.querySelector('.cz-row[data-page="character"] .cz-value') || {}).textContent;
          out.pickedName = AVATAR_DISPLAY_NAME[store.avatarChar] || store.avatarChar;
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        check(f"{dev}: Customize: no error", not r.get("threw"), r.get("threw", ""))
        check(f"{dev}: Profile's button opens the summary - four rows in order, no grid on it, Back to Profile",
              r.get("rows") == ["character", "banner", "theme", "fx"] and r.get("grids") == 0 and "Back to Profile" in r.get("back", ""), r)
        # "The title of all those tabs needs a header thing"
        check(f"{dev}: \"Your look\" wears the Name's own header bar",
              [b.lower() for b in r.get("bars") or []] == ["name", "your look"] and r.get("sameBar"), (r.get("bars"), r.get("sameBar")))
        ch, bn, th, fx = r.get("char") or {}, r.get("banner") or {}, r.get("theme") or {}, r.get("fx") or {}
        cb = ch.get("box") or {"w": 0, "h": 0}
        # "The character preview of what you have set is cool but it's small"
        check(f"{dev}: the character row shows the one you wear, at least 56px",
              ch.get("avatar") and min(cb["w"], cb["h"]) >= 56, ch)
        # "give the small banner preview (about the same total size as the
        # other ones) but to the shape of a banner"
        bb = bn or {"w": 0, "h": 1}
        ratio, area = bb["w"] / max(1, bb["h"]), bb["w"] * bb["h"] / max(1, cb["w"] * cb["h"])
        check(f"{dev}: the banner row's preview is banner-shaped (16:6) and about the character's size",
              2.4 <= ratio <= 3.0 and 0.6 <= area <= 1.6, {"banner": bn, "ratio": round(ratio, 2), "area": round(area, 2)})
        check(f"{dev}: the theme row's swatch swirls (the composited swirl), at least 48px",
              th.get("swirl") and min((th.get("box") or {"w": 0, "h": 0}).values()) >= 48, th)
        # "The hundo effect one is tough to represent ... there's gotta be a way"
        check(f"{dev}: the hundo effect row shows the effect in use as its own tile, 100% in it",
              fx.get("id") and fx.get("id") == fx.get("inUse") and fx.get("pct") == "100%", fx)
        check(f"{dev}: only the character row carries a \"new\" pill, for the one character not yet seen",
              (r.get("news") or [None])[0] == "1 new" and all(n == "" for n in (r.get("news") or [])[1:]), r.get("news"))
        pages = r.get("pages") or []
        check(f"{dev}: each row opens its own page, under the bar with its name and count, and only its grid",
              len(pages) == 4 and all(p["isPage"] and p["title"] == p["label"] and p["own"] >= 1 and p["others"] == 0 for p in pages), pages)
        check(f"{dev}: every count is the page's own grid, on the row and on the bar",
              len(pages) == 4 and all(p["rowCount"] == p["barCount"] == p["grid"] for p in pages), [(p["k"], p["rowCount"], p["barCount"], p["grid"]) for p in pages])
        check(f"{dev}: Back to Customize comes back to the summary",
              all("Back to Customize" in p["back"] for p in pages) and r.get("backHome") == 4, (r.get("backHome"), [p["back"] for p in pages]))
        check(f"{dev}: a new pick shows on its row", r.get("pickedRow") == r.get("pickedName") and r.get("picked"), (r.get("picked"), r.get("pickedRow"), r.get("pickedName")))
        ctx.close()


def check_b317_daily(br):
    """Build 317. "When you submit your answer, ensure it's not just
    clicking, let's put a submit answer ... Let's also ensure the buttons on
    the bottom of that screen stay in the same place so they don't feel
    randomly placed", and of the Detective: "you get a banner notification at
    the top for the progression towards the character, we don't need that,
    we'd want the pop up when unlocking it though". Written against build
    316, where a tap answered outright, Exit sat under the result card, and
    a correct answer queued "N of 10 daily questions right in a row"."""
    print("\n317. the daily question: pick, then Submit answer; one button spot; no Detective progress banner")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          const R = e => { if(!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; };
          const out = {};
          store.dailyCorrectStreak = 3; store.dailyQuestionDate = null; saveStore();
          document.querySelectorAll('#pushing-update,#intro-pop').forEach(n => n.remove());
          startDailyQuestion();
          for(let t = 0; t < 80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
          await wait(400);
          const sb0 = document.getElementById('dailyq-submitbtn');
          out.submit0 = sb0 ? { text: sb0.textContent.trim(), disabled: sb0.disabled, rect: R(sb0) } : null;
          const r = correctSlot(order[pos]);
          const wrong = [...document.querySelectorAll('.qpanel .choice')].find(c => +c.dataset.index !== r);
          wrong.click(); await wait(300);
          out.afterTap = { locked: dailyQuestionLocked, outro: !!document.querySelector('.dailyq-outro'),
                           picked: !!document.querySelector('.qpanel .choice.is-picked'),
                           submitLive: !!(document.getElementById('dailyq-submitbtn') && !document.getElementById('dailyq-submitbtn').disabled) };
          [...document.querySelectorAll('.qpanel .choice')].find(c => +c.dataset.index === r).click(); await wait(200);
          const sb1 = document.getElementById('dailyq-submitbtn'); out.submit1 = R(sb1); if(sb1) sb1.click();
          await wait(1500);
          const ex = document.getElementById('dailyq-exitbtn');
          out.exit = ex ? { text: ex.textContent.trim(), rect: R(ex) } : null;
          out.exits = document.querySelectorAll('#dailyq-exitbtn').length;
          out.correct = !!store.dailyQuestionCorrect;
          const o = document.querySelector('.dailyq-outro');
          out.outroClear = !!(o && ex && o.getBoundingClientRect().bottom <= ex.getBoundingClientRect().top);
          out.pending = (typeof pendingDailyProgress === 'undefined') ? null : pendingDailyProgress;
          let seen = '';
          const mo = new MutationObserver(() => { const t = document.body.textContent || ''; const m = t.match(/\\d+ of \\d+ daily questions right in a row|Back to 0 of \\d+/); if(m) seen = m[0]; });
          mo.observe(document.body, { childList: true, subtree: true, characterData: true });
          if(ex) ex.click(); await wait(3500); mo.disconnect();
          out.home = !!document.querySelector('[data-screen="home"]'); out.seen = seen;
          return out; }""")
        ctx.close()
        s0 = r.get("submit0") or {}
        check("%s: the daily question opens with Submit answer, off until a choice is picked" % dev,
              s0.get("text") == "Submit answer" and s0.get("disabled") is True, s0)
        a = r.get("afterTap") or {}
        check("%s: tapping a choice picks it and does not answer" % dev,
              a.get("locked") is False and a.get("outro") is False and a.get("picked") is True and a.get("submitLive") is True, a)
        check("%s: changing your mind before Submit still lets you get it right" % dev, r.get("correct") is True, r.get("correct"))
        ex = r.get("exit") or {}
        check("%s: Exit to main menu takes Submit answer's exact spot, once" % dev,
              ex.get("text") == "Exit to main menu" and ex.get("rect") == s0.get("rect") == r.get("submit1") and r.get("exits") == 1,
              [s0.get("rect"), r.get("submit1"), ex.get("rect"), r.get("exits")])
        check("%s: the result card is not under the button" % dev, r.get("outroClear") is True, r.get("outroClear"))
        check("%s: no Detective progress banner, on the question or on Home" % dev,
              r.get("pending") in (None,) and r.get("seen") == "" and r.get("home") is True,
              [r.get("pending"), r.get("seen"), r.get("home")])


def check_b316_tiles(br):
    """Build 316, round two. "The size of the themed circle in the profile
    box unlocks is perfect ... all three (or 4 because there will be a
    banner one) would need to be the same size in totality ... The banner
    one will obviously be the shape of a banner ... The banner animate there
    too of course." And the badge case: "should the outline of that have a
    flow similar to the rank one does not color matching the rank". Written
    against the first 316 build - flare 2.7rem, character 2.9rem, a square
    banner, a flat case - where every check here fails."""
    print("\n316t. Profile: one size for every unlock, a banner-shaped banner that moves, a case with the card's flow")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async () => { const out = {}; const wait = ms => new Promise(r => setTimeout(r, ms));
          try{
          /* Platinum held at its wall, so the next rank is Sapphire - the
             first one that hands over a banner */
          const units = topicsIn(QUESTIONS).slice().sort((a, b) => badgeThresholdFor(a) - badgeThresholdFor(b));
          store.unitPerfects = {}; units.slice(0, TIER_UNLOCKS.vanguard.badges).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
          store.lifetime.points = xpForLevel(75) + 900; store.rankFloor = 0; store.levelFloor = 0;
          showProfile('profile'); await wait(1500);
          const box = sel => { const e = document.querySelector(sel); if(!e) return null; const b = e.getBoundingClientRect();
            return [Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10, Math.round((b.top + b.height / 2) * 10) / 10]; };
          out.next = (rankChallengesOf() || {}).key;
          out.theme = box('.pf-rw.is-theme .pf-swatch .dot');
          out.flare = box('.pf-rw.is-flare .flare-solo');
          out.char = box('.pf-rw.is-char .pf-rw-char');
          out.banner = box('.pf-rw.is-banner .pf-rw-banner');
          const bn = document.querySelector('.pf-rw.is-banner .bnr');
          out.bnStill = bn ? bn.classList.contains('is-still') : null;
          out.bnAnims = bn ? bn.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length : 0;
          const cs = getComputedStyle(document.querySelector('.pf-case'));
          out.caseBg = cs.backgroundImage;
          const m = cs.borderTopColor.match(/[\\d.]+/g) || [];
          out.caseBorderAlpha = m.length >= 4 ? Number(m[3]) : 1;
          out.caseBorderChan = m.slice(0, 3).map(Number);
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""")
        circ = [r.get(k) for k in ("theme", "flare", "char")]
        check(f"{dev}: the theme, the flare and the character are one size - the theme circle's", None not in circ
              and max(c[0] for c in circ) - min(c[0] for c in circ) <= 0.6 and max(c[1] for c in circ) - min(c[1] for c in circ) <= 0.6, circ)
        b, c0 = r.get("banner"), (r.get("theme") or [0, 0, 0])
        check(f"{dev}: the banner is banner-shaped (8 by 3), no taller than the circles and wider than them, on their line",
              r.get("next") == "adept" and b is not None and 2.4 <= b[0] / max(1, b[1]) <= 2.95 and b[1] < c0[1] and b[0] > c0[0]
              and abs(b[2] - c0[2]) <= 2, [r.get("next"), b, c0])
        check(f"{dev}: and it moves", r.get("bnStill") is False and r.get("bnAnims", 0) > 0, [r.get("bnStill"), r.get("bnAnims")])
        ch = r.get("caseBorderChan") or [255, 255, 255]
        check(f"{dev}: the badge case has the Next rank card's flow - a diagonal light and a tinted edge, not a flat box",
              "gradient" in (r.get("caseBg") or "") and r.get("caseBorderAlpha", 0) >= 0.2
              and not all(abs(x - 1) < 0.01 or abs(x - 255) < 1 for x in ch), [r.get("caseBg", "")[:70], r.get("caseBorderAlpha"), ch])
        check(f"{dev}: nothing threw", not r.get("threw"), r.get("threw"))
        ctx.close()


def check_b317_volume(br):
    """Build 317. "It appears in profile some characters have a nice 3d look
    but some don't, fix that as well." Every surface a character paints with
    its headGrad light gets a shade layer and a light layer straight on top
    of it, the same shape, so each piece reads round rather than flat - and
    it is done with fills, never an SVG filter. Written against build 316,
    where only the characters that drew their own highlight had one."""
    print("\n317. every character's surfaces are lit round, with no filter")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => {
      const out = { chars: 0, lit: 0, bare: [], filtered: [], threw: null };
      try {
        AVATAR_CHARACTERS.filter(c => !c.retired).forEach(c => {
          const s = drawAvatarCharSVG(c.id); if(!s) return;
          out.chars++;
          const uid = s.getAttribute('data-cx-uid');
          const head = [...s.querySelectorAll('path, ellipse, circle, rect, polygon')]
            .filter(n => (n.getAttribute('fill') || '').startsWith('url(#' + uid + '-head') && !n.closest('.cx-bg'));
          let ok = head.length > 0 || ['voidwalker', 'genesis', 'zenith'].includes(c.id);
          head.forEach(n => {
            const a = n.nextElementSibling, b = a && a.nextElementSibling;
            const same = x => x && x.nodeName === n.nodeName && ['d', 'cx', 'cy', 'rx', 'ry', 'r', 'points', 'transform']
              .every(k => x.getAttribute(k) === n.getAttribute(k));
            if(!(same(a) && same(b) && /-vshade\\)$/.test(a.getAttribute('fill')) && /-vgloss\\)$/.test(b.getAttribute('fill')))) ok = false;
          });
          if(ok && head.length) out.lit++;
          if(!ok) out.bare.push(c.id);
          if(s.querySelector('[filter]')) out.filtered.push(c.id);
        });
      } catch(e) { out.threw = String(e); }
      return out;
    }""")
    check("every character with lit surfaces has a shade and a light layer on each of them",
          r["chars"] >= 25 and not r["bare"], [r["chars"], r["lit"], r["bare"]])
    check("the flat ones included: Detective, Sheriff, Hive, Zeus, Timekeeper, Masked One",
          r["lit"] >= 25, r["lit"])
    check("no SVG filter inside any drawing", not r["filtered"], r["filtered"])
    check("nothing threw", not r["threw"], r["threw"])
    ctx.close()


CUTSPIN_RUN = """async (tier) => { const wait = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
  const idx = TIER_ORDER_FULL.indexOf(tier);
  /* Home's own bubble against Home's own planet, for this flare */
  let home = null;
  const hw = document.querySelector('[data-screen="home"] .cosmic-hero-wrap');
  if(hw){
    const b = hw.querySelectorAll('.cosmic-icon-badge')[idx], m = hw.querySelector('.cosmic-hero-main');
    if(b && m) home = b.getBoundingClientRect().width / m.getBoundingClientRect().width;
  }
  playTierCutscene(tier, { from: TIER_ORDER_FULL[idx - 1], onDone(){} });
  const ov = document.getElementById('supernova-cutscene');
  const samples = [];
  const t0 = performance.now();
  const ev = { spinEnd: null, litAt: null, burstAt: null, restT: null };
  const orb0 = ov.querySelector('.rank-before .rank-orbit');
  const bb = ov.querySelector('.rank-before .cosmic-icon-badge[data-rank-tier="' + tier + '"]');
  if(orb0) orb0.addEventListener('transitionend', e => { if(e.target === orb0 && e.propertyName === 'transform' && ev.spinEnd == null){
    ev.spinEnd = performance.now(); ev.restT = getComputedStyle(orb0).transform; } });
  if(bb) new MutationObserver(() => { if(ev.litAt == null && bb.classList.contains('cosmic-badge-lit')) ev.litAt = performance.now(); })
    .observe(bb, { attributes: true, attributeFilter: ['class'] });
  new MutationObserver(() => { if(ev.burstAt == null && ov.classList.contains('supernova-burst')) ev.burstAt = performance.now(); })
    .observe(ov, { attributes: true, attributeFilter: ['class'] });
  /* sampled from inside the page every 90ms until the flash, so a loaded
     machine cannot skip the beat between two Playwright calls */
  while(ov.isConnected && !ov.classList.contains('supernova-burst') && performance.now() - t0 < 20000){
    const orb = ov.querySelector('.rank-before .rank-orbit');
    const slot = ov.querySelector('.rank-before .rank-orbit-slot');
    const wipe = ov.querySelector('.rank-before .rank-litwipe');
    const b = ov.querySelector('.rank-before .cosmic-icon-badge[data-rank-tier="' + tier + '"]:not(.rank-litwipe)');
    const m = ov.querySelector('.rank-before .cosmic-hero-main');
    const cp = wipe ? getComputedStyle(wipe).clipPath : '';
    samples.push({ ign: ov.classList.contains('is-igniting'),
      orbT: orb ? getComputedStyle(orb).transform : null,
      slotT: slot ? getComputedStyle(slot).transform : null,
      wipeR: wipe ? parseFloat((cp.match(/circle\\(([\\d.]+)%/) || [, 'NaN'])[1]) : null,
      lit: !!(b && b.classList.contains('cosmic-badge-lit')),
      ratio: b && m ? b.getBoundingClientRect().width / m.getBoundingClientRect().width : null });
    await wait(90);
  }
  /* a loaded machine can start the transition late: give it time to end */
  for(let k = 0; k < 60 && ev.spinEnd == null && ov.isConnected; k++) await wait(100);
  ov.remove();
  return { home, samples, ev };
}"""


def check_b317_cutspin(br):
    """Build 317. "The planet lights up instantly, all the planets need to
    spin on their axis ring thing in a circle, during this part, that's when
    the unlocked flare rank will start lighting up instantly the middle of
    it, they will spin fast and then when it stops it's fully lit ... the
    unlocked rank flare does look massive within the cutscene ... Needs to
    look like the main menu" - and of the pop-ups after it: "the theme one
    looks like a ball, and it doesn't animate, the character also doesn't
    animate". Asserts the whirl (the carrier's transform turns over the
    unlock beat while each slot turns back), a light that RAMPS from the
    middle (several clip sizes between nothing and full, then the bubble
    itself lit before the flash), the flare at Home's size against the
    planet (within 15%, phone and tablet), and the theme and character
    tiles of the rank-reward card moving. Written against build 317's
    first cut (57212ce), where all of these fail."""
    print("\n317b. the rank-up whirl, the light from the middle, Home-sized flares, live reward cards")
    for label, w, h in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate("()=>{ try{ showHome(); }catch(e){} }")
        pg.wait_for_timeout(900)
        r = pg.evaluate(CUTSPIN_RUN, "vanguard")
        ctx.close()
        sm = [x for x in r["samples"] if x["ign"]]
        turns = {x["orbT"] for x in sm if x["orbT"] and x["orbT"] not in ("none", "matrix(1, 0, 0, 1, 0, 0)")}
        back = {x["slotT"] for x in sm if x["slotT"] and x["slotT"] not in ("none", "matrix(1, 0, 0, 1, 0, 0)")}
        check("%s: every flare whirls round its ring at the unlock beat" % label,
              len(turns) >= 3 and len(back) >= 3, (len(sm), len(turns), len(back)))
        ev = r["ev"]
        check("%s: the whirl ends in whole turns, every bubble back in its own place" % label,
              ev["spinEnd"] is not None and ev["restT"] in ("none", "matrix(1, 0, 0, 1, 0, 0)"), ev)
        radii = [x["wipeR"] for x in sm if x["wipeR"] is not None and x["wipeR"] == x["wipeR"]]
        mid = {round(v) for v in radii if 2 < v < 98}
        check("%s: the new flare lights from its middle outward, not in one step" % label,
              len(mid) >= 2 and radii == sorted(radii), sorted(mid))
        # Fully lit as the whirl stops (its transitionend) - or, on a machine
        # so loaded the whirl started late, by the flash at the latest.
        lit_ok = ev["litAt"] is not None and ev["spinEnd"] is not None and (
            ev["litAt"] >= ev["spinEnd"] - 60
            or (ev["burstAt"] is not None and ev["litAt"] >= ev["burstAt"] - 400))
        check("%s: fully lit only once the whirl is over (or the flash comes)" % label,
              lit_ok and bool(mid), ev)
        ratios = [x["ratio"] for x in sm if x["ratio"]]
        worst = max(ratios, key=lambda v: abs(v - (r["home"] or 1))) if ratios else None
        check("%s: the flare is Home's size against the planet (within 15%%)" % label,
              bool(r["home"]) and worst is not None and abs(worst / r["home"] - 1) <= 0.15,
              (r["home"] and round(r["home"], 4), worst and round(worst, 4)))

    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    cards = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      const r = TIER_ORDER_FULL.find(k => AVATAR_CHARACTERS.some(c => c.unlock === k && !c.feat));
      const ch = AVATAR_CHARACTERS.find(c => c.unlock === r && !c.feat);
      playUnlockSpotlight(rankRewardsItem(r, [themeUnlockItem(r), characterUnlockItem(ch.id)]), 1, 1, ()=>{});
      const out = { theme: 0, charMoves: [], charLive: false };
      const t0 = performance.now();
      while(performance.now() - t0 < 9000){
        const th = document.querySelector('.rs-reward-tile.is-theme .rs-reward-art');
        const ca = document.querySelector('.rs-reward-tile.is-character .rs-reward-art');
        if(th) out.theme = Math.max(out.theme, th.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length);
        if(ca){
          ca.getAnimations({ subtree: true }).filter(a => a.playState === 'running' && a.animationName)
            .forEach(a => { if(out.charMoves.indexOf(a.animationName) < 0) out.charMoves.push(a.animationName); });
          if(/char-(live|flip)/.test(ca.className) && !/char-react/.test(ca.className) && out.charMoves.length) out.charLive = true;
        }
        await wait(150);
      }
      out.rank = r;
      return out; }""")
    ctx.close()
    check("the theme tile is the theme's swatch, swirling and sweeping", cards["theme"] >= 2, cards["theme"])
    check("the character tile celebrates (its winner's move), not just a blink",
          any(n in cards["charMoves"] for n in ("cx-hop-big", "cx-hop-loop")), cards["charMoves"][:10])
    check("and then carries on living", cards["charLive"], cards)

    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    order = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      showHome(); await wait(500);
      window.scheduleHomeUnlocks = () => {}; if(homeUnlockTimer){ clearTimeout(homeUnlockTimer); homeUnlockTimer = null; }
      /* a rank just reached on Home with its reward card still owed, and a
         badge from the same run queued */
      window.pendingHomeUnlocks = () => ({ chars: ['x'], banners: [], hints: [], fx: [] });
      rankJustReachedOnHome = 'vanguard';
      store.pendingBadgeUnlocks = [topicsIn(QUESTIONS)[0]];
      const out = { cardsWait: homeUnlockBlocked() };
      playQueuedBadgeCutscenes(); await wait(400);
      out.badgeFirst = !!document.getElementById('badge-cutscene');
      rankJustReachedOnHome = null;
      window.pendingHomeUnlocks = () => ({ chars: [], banners: [], hints: [], fx: [] });
      await wait(1600);
      out.badgeAfter = !!document.getElementById('badge-cutscene');
      return out; }""")
    ctx.close()
    check("on Home a rank's reward card goes before a badge cutscene from the same run",
          order["cardsWait"] is False and not order["badgeFirst"] and order["badgeAfter"], order)


def check_b317_tabplate(br):
    """Build 317. "They got a smidge smaller so let's ensure they are still a
    nice size AND let's ensure you can see their backgrounds because right
    now their backgrounds are hard to see there and ensure they still get
    animations on the tab." The Profile tab's character sits on a lit disc
    in its own colour, 20% bigger than the other tab icons, without the bar
    growing, and still animates. Written against build 317's first cut,
    where it was a bare 28px drawing on the glass."""
    print("\n317. the Profile tab's character: on its own plate, bigger, bar unchanged, still alive")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          store.avatarChar = 'ronin'; const t = document.querySelector('#bottomtab-profile .bottomtab-icon');
          delete t.dataset.char; syncBottomTabAvatar(); showHome(); await wait(2500);
          const home = document.querySelector('#bottomtab-home .bottomtab-icon').getBoundingClientRect();
          const ic = t.getBoundingClientRect(), cs = getComputedStyle(t);
          const lab = document.querySelector('#bottomtab-profile .bottomtab-label').getBoundingClientRect();
          const homeLab = document.querySelector('#bottomtab-home .bottomtab-label').getBoundingClientRect();
          const anims = document.getAnimations().filter(a => a.effect && a.effect.target && t.contains(a.effect.target) && a.playState === 'running').length;
          return { ratio: ic.width / home.width, bg: cs.backgroundImage, radius: cs.borderTopLeftRadius,
                   glow: t.style.getPropertyValue('--char-glow'), gap: lab.top - ic.bottom,
                   labelsLevel: Math.abs(lab.top - homeLab.top), anims }; }""")
        check(f"{dev}: the character is ~20% bigger than the other tab icons", r["ratio"] >= 1.15, round(r["ratio"], 3))
        check(f"{dev}: on a disc lit in its own colour", "gradient" in r["bg"] and r["radius"] == "50%" and bool(r["glow"]), [r["bg"][:40], r["radius"], r["glow"]])
        check(f"{dev}: the labels stay level - the bar did not grow round it", r["labelsLevel"] <= 1 and r["gap"] >= 0, [r["labelsLevel"], r["gap"]])
        check(f"{dev}: and it still animates in the tab", r["anims"] > 0, r["anims"])
        ctx.close()


def check_b317_rankup(br):
    """Build 317. "When you rank up, the next time you open the Profile tab
    it should be a cool thing. After a second, a black loading screen that
    says 'Loading rank up adjustments' ... Then the rank road map plays ...
    Then the screen automatically switches back to the Profile screen ...
    While this is all going on you can't click anything ... when you do rank
    up, the next time you go to Home, the Profile tab in the bottom tab bar
    starts pulsing/ringing, and you can't use anything else except that -
    if you try to hit Start Studying or another tab, it says something like
    'Your profile needs you'. The buttons on the planet system ... and the
    chat button still work." Written against build 316 (the w316snap copy),
    where Home is never locked, Profile opens straight onto the new rank and
    nothing plays."""
    print("\n317r. a rank-up locks Home to the Profile tab, and Profile plays it: loading, the road map, back to Profile")
    SCENE = "(typeof rankUpScene !== 'undefined' ? rankUpScene : null)"
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        held = pg.evaluate("() => " + _seed_gold_js())
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          const scene = () => %s;
          try{
          /* Gold reached, the map last showed Silver; Gold's character card still owed */
          store.rankFloor = 0; store.rankMapFx244 = true; store.rankMapSeen = 1; store.pendingTierCutscene = null;
          store.savedCodeSaved = true; saveStore();
          document.querySelectorAll('.app-banner, #pushing-update, #intro-pop').forEach(n => n.remove());
          showHome(); await wait(1500);
          /* the reward cards play first; the lock waits for them */
          let cards = 0, lockedUnderCard = false;
          for(let i = 0; i < 90 && !document.body.classList.contains('rankup-lock'); i++){
            const sp = document.querySelector('.rs-spot');
            if(sp){ await wait(1300); if(document.body.classList.contains('rankup-lock')) lockedUnderCard = true; sp.click(); cards++; await wait(300); }
            await wait(200);
          }
          out.cards = cards; out.lockedUnderCard = lockedUnderCard;
          const tab = document.getElementById('bottomtab-profile');
          out.lock = document.body.classList.contains('rankup-lock');
          out.ring = getComputedStyle(tab, '::before').animationName;
          out.ringColor = getComputedStyle(tab).getPropertyValue('--ru-color').trim();
          /* refused: Start Studying, the daily question, Leaderboard, Settings */
          const onHome = () => !!document.querySelector('[data-screen="home"]');
          const alertText = () => (document.getElementById('dailyalert') || {}).textContent || '';
          document.getElementById('dailyalert')?.remove();
          document.getElementById('nextbtn').click(); await wait(400);
          out.start = { home: onHome(), alert: alertText(), mode: !!document.querySelector('.screen-modeselect, .modesel') };
          document.getElementById('dailyalert')?.remove();
          const fab = document.querySelector('.daily-question-fab'); if(fab) fab.click(); await wait(400);
          out.daily = { home: onHome(), alert: alertText(), q: !!document.querySelector('.qpanel') };
          document.getElementById('bottomtab-rewards').click(); await wait(500);
          out.board = { home: onHome(), alert: alertText() };
          document.getElementById('bottomtab-settings').click(); await wait(500);
          out.settings = { home: onHome(), alert: alertText() };
          /* allowed: a flare bubble, the chat, the Home tab */
          const fl = document.querySelector('.panel.home .cosmic-badge-tappable');
          if(fl) fl.click(); await wait(500);
          out.flare = !!document.getElementById('contextual-info-popup');
          document.getElementById('contextual-info-popup')?.remove();
          const cb = document.getElementById('chatdock-btn'); if(cb) cb.click(); await wait(700);
          out.chat = !!document.querySelector('.chatdock.is-open');
          if(out.chat){ cb.click(); await wait(500); }
          document.getElementById('bottomtab-home').click(); await wait(400);
          out.homeTab = { home: onHome(), lock: document.body.classList.contains('rankup-lock') };
          /* Profile: the card as it was, every input already taken */
          const t0 = performance.now();
          tab.click(); await wait(400);
          const pan = document.querySelector('.screen-profile');
          out.p0 = { profile: !!pan, blocker: !!document.querySelector('.ru-blocker'),
            rank: (document.querySelector('.pf-standing .pf-rankname') || {}).textContent || null,
            next: (document.querySelector('.pf-goal .pf-goal-name') || {}).textContent || null,
            unlocked: !document.body.classList.contains('rankup-lock') };
          const g = document.querySelector('.pf-goal');
          if(g){ const b = g.getBoundingClientRect(); const top = document.elementFromPoint(b.left + b.width / 2, b.top + 20);
            out.p0.topIsBlocker = !!(top && top.classList.contains('ru-blocker')); g.click(); }
          await wait(300);
          out.p0.stayed = !!(pan && pan.isConnected);
          /* watch the classes the scene moves through */
          const seenCls = {}; const mo = new MutationObserver(ms => ms.forEach(m => { const c = m.target.className;
            if(typeof c === 'string') ['ru-zoom','ru-shake','ru-ride','is-celebrating','ru-rankup','ru-arrive'].forEach(k => { if(c.indexOf(k) >= 0) seenCls[k] = true; }); }));
          mo.observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] });
          const at = {};
          let tried = false;
          for(let i = 0; i < 260; i++){
            const ov = document.getElementById('teststart-overlay');
            if(ov && !at.loading){ at.loading = Math.round(performance.now() - t0); out.loadText = (ov.textContent || '').trim(); }
            if(document.querySelector('.screen-ranks .rankmap') && !at.map) at.map = Math.round(performance.now() - t0);
            if(at.map && !tried && performance.now() - t0 > at.map + 1500){
              tried = true; const bl = document.querySelector('.screen-ranks .back-link, .screen-ranks a, .screen-ranks button');
              if(bl) bl.click(); window.scrollTo(0, 0); await wait(200);
              out.mapHeld = { ranks: !!document.querySelector('.screen-ranks'), blocker: !!document.querySelector('.ru-blocker') };
            }
            if(at.map && !at.revealed && !document.querySelector('.rankmap-stop.is-celebrate-pending')) at.revealed = Math.round(performance.now() - t0);
            const hk = document.querySelector('.rankhero-kicker.ru-kick');
            if(hk && !at.hero){ at.hero = Math.round(performance.now() - t0); out.heroKick = hk.textContent; out.heroName = (document.querySelector('.rankhero-name') || {}).textContent; }
            if(at.map && document.querySelector('.screen-profile') && !at.back) at.back = Math.round(performance.now() - t0);
            if(at.back && !scene() && !document.querySelector('.ru-blocker')){ at.done = Math.round(performance.now() - t0); break; }
            await wait(100);
          }
          mo.disconnect();
          out.at = at; out.cls = seenCls;
          out.after = { rank: (document.querySelector('.pf-standing .pf-rankname') || {}).textContent || null,
            next: (document.querySelector('.pf-goal .pf-goal-name') || {}).textContent || null,
            seen: store.rankMapSeen, held: TIER_ORDER_FULL.indexOf(rankOf(store)), blocker: !!document.querySelector('.ru-blocker'),
            dot: tab.classList.contains('has-new') && rankIsNew() };
          /* the lock is gone, and it plays once */
          showHome(); await wait(3200);
          out.home2 = { lock: document.body.classList.contains('rankup-lock'), ring: tab.classList.contains('ru-call') };
          document.getElementById('nextbtn').click(); await wait(500);
          out.home2.left = !document.querySelector('[data-screen="home"]');
          showProfile(); await wait(1600);
          out.again = { scene: !!scene(), loading: !!document.getElementById('teststart-overlay'), blocker: !!document.querySelector('.ru-blocker') };
          /* never opened the map (rankMapSeen null): no lock, no scene */
          store.rankMapSeen = null; store.rankMapFx244 = false; saveStore();
          showHome(); await wait(3200);
          out.nullLock = document.body.classList.contains('rankup-lock');
          showProfile(); await wait(1500);
          out.nullScene = !!scene() || !!document.getElementById('teststart-overlay');
          } catch(e){ out.threw = String(e && e.stack || e); }
          return out; }""" % SCENE)
        check(f"{dev}: the fixture holds Gold", held == "veteran", held)
        check(f"{dev}: nothing threw", not r.get("threw"), r.get("threw"))
        check(f"{dev}: Gold's reward card plays first, and Home locks only once it has gone",
              (r.get("cards") or 0) >= 1 and r.get("lockedUnderCard") is False and r.get("lock") is True,
              [r.get("cards"), r.get("lockedUnderCard"), r.get("lock")])
        check(f"{dev}: the Profile tab rings, in Gold", r.get("ring") == "ru-tab-ring" and bool(r.get("ringColor")),
              [r.get("ring"), r.get("ringColor")])
        for k, label in (("start", "Start Studying"), ("daily", "the daily question"), ("board", "Leaderboard"), ("settings", "Settings")):
            v = r.get(k) or {}
            check(f"{dev}: {label} is refused with 'Your profile needs you'",
                  v.get("home") is True and v.get("alert") == "Your profile needs you" and not v.get("mode") and not v.get("q"), v)
        check(f"{dev}: a flare bubble on Home still answers", r.get("flare") is True, r.get("flare"))
        check(f"{dev}: the chat button still opens the chat", r.get("chat") is True, r.get("chat"))
        check(f"{dev}: the Home tab is a no-op and keeps the lock", (r.get("homeTab") or {}) == {"home": True, "lock": True}, r.get("homeTab"))
        p0 = r.get("p0") or {}
        check(f"{dev}: Profile opens as it was - Silver, Next rank Gold - with the lock off and input already blocked",
              p0.get("profile") and p0.get("blocker") and p0.get("rank") == "Silver" and p0.get("next") == "Gold" and p0.get("unlocked"), p0)
        check(f"{dev}: a tap on the card lands on the input layer and goes nowhere",
              p0.get("topIsBlocker") is True and p0.get("stayed") is True, [p0.get("topIsBlocker"), p0.get("stayed")])
        at = r.get("at") or {}
        check(f"{dev}: after a second, LOADING RANK UP ADJUSTMENTS",
              800 <= (at.get("loading") or 0) <= 2500 and r.get("loadText", "").endswith("LOADING RANK UP ADJUSTMENTS"), [at.get("loading"), r.get("loadText")])
        check(f"{dev}: about three seconds later, the road map", 2500 <= (at.get("map") or 0) - (at.get("loading") or 0) <= 4500,
              [at.get("loading"), at.get("map")])
        mh = r.get("mapHeld") or {}
        check(f"{dev}: the road map cannot be left mid-show", mh.get("ranks") is True and mh.get("blocker") is True, mh)
        cls = r.get("cls") or {}
        check(f"{dev}: it zooms in, a light rides into Gold, Gold shakes and its colour comes out",
              all(cls.get(k) for k in ("ru-zoom", "ru-ride", "ru-shake", "is-celebrating")) and bool(at.get("revealed")), [cls, at.get("revealed")])
        check(f"{dev}: the current-rank card turns over to Gold and says Rank up",
              r.get("heroKick") == "Rank up" and r.get("heroName") == "Gold" and cls.get("ru-rankup"), [r.get("heroKick"), r.get("heroName")])
        af = r.get("after") or {}
        check(f"{dev}: then back to Profile, fading into Gold and Platinum's challenges",
              bool(at.get("back")) and bool(at.get("done")) and af.get("rank") == "Gold" and af.get("next") == "Platinum" and cls.get("ru-arrive"),
              [at.get("back"), at.get("done"), af.get("rank"), af.get("next")])
        check(f"{dev}: rankMapSeen ends at the rank held, the input layer is gone, and no dot is left",
              af.get("seen") == af.get("held") == 2 and af.get("blocker") is False and not af.get("dot"), af)
        h2 = r.get("home2") or {}
        check(f"{dev}: Home is unlocked afterwards", h2.get("lock") is False and h2.get("ring") is False and h2.get("left") is True, h2)
        check(f"{dev}: it plays once only", r.get("again") == {"scene": False, "loading": False, "blocker": False}, r.get("again"))
        check(f"{dev}: an account that has never opened the map (rankMapSeen null) is never locked",
              r.get("nullLock") is False and r.get("nullScene") is False, [r.get("nullLock"), r.get("nullScene")])
        ctx.close()
    # Reduce motion, a reload half-way, and the watchdog - on the phone.
    # Seeded ONCE (not on every load, as booted() does), so the reload
    # below comes back to what the app itself saved.
    once = ("try{ if(!localStorage.getItem('__seeded317')){ localStorage.setItem('__seeded317','1');"
            "localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
            "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
            "localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.drill.v1', '%s'); } }catch(e){}" % USED_ACCOUNT)
    ctx, pg = booted(br, 440, 956, init=once)
    pg.evaluate("() => " + _seed_gold_js())
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const scene = () => %s;
      try{
      store.rankFloor = 0; store.rankMapFx244 = true; store.rankMapSeen = 1; store.savedCodeSaved = true;
      const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); saveStore();
      theme.reduceMotion = true; applyTheme && applyTheme();
      const seenCls = {}; const mo = new MutationObserver(ms => ms.forEach(m => { const c = m.target.className;
        if(typeof c === 'string') ['ru-zoom','ru-shake','ru-ride'].forEach(k => { if(c.indexOf(k) >= 0) seenCls[k] = true; }); }));
      mo.observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] });
      showProfile(); const t0 = performance.now(); let loading = false, map = false;
      for(let i = 0; i < 200; i++){
        if(document.getElementById('teststart-overlay')) loading = true;
        if(document.querySelector('.screen-ranks')) map = true;
        if(map && !scene() && !document.querySelector('.ru-blocker')) break;
        await wait(100);
      }
      mo.disconnect();
      out.rm = { ms: Math.round(performance.now() - t0), loading, map, cls: seenCls, seen: store.rankMapSeen,
        profile: !!document.querySelector('.screen-profile'), rank: (document.querySelector('.pf-standing .pf-rankname') || {}).textContent };
      theme.reduceMotion = false; applyTheme && applyTheme();
      /* the watchdog: whatever stalls, the layer comes off */
      store.rankMapSeen = 1; saveStore();
      showProfile(); for(let i = 0; i < 80 && !document.querySelector('.screen-ranks'); i++) await wait(100);
      const s = scene(); if(s) rankUpSceneWatch(s, 200); await wait(900);
      out.dog = { scene: !!scene(), blocker: !!document.querySelector('.ru-blocker'), seen: store.rankMapSeen, profile: !!document.querySelector('.screen-profile') };
      /* half-way, then the app is closed: it plays again, with nothing left stuck */
      store.rankMapSeen = 1; saveStore();
      showProfile(); for(let i = 0; i < 80 && !document.querySelector('.screen-ranks'); i++) await wait(100);
      out.midMap = !!document.querySelector('.screen-ranks') && !!document.querySelector('.ru-blocker');
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""" % SCENE)
    check("reduce motion: nothing threw", not r.get("threw"), r.get("threw"))
    rm = r.get("rm") or {}
    check("reduce motion: loading, the map, back on Profile as Gold - shorter, no zoom, ride or shake",
          rm.get("loading") and rm.get("map") and rm.get("profile") and rm.get("rank") == "Gold" and rm.get("seen") == 2
          and not rm.get("cls") and (rm.get("ms") or 99999) < 11000, rm)
    check("the watchdog ends a stalled scene: the layer comes off, it is marked, Profile is up",
          r.get("dog") == {"scene": False, "blocker": False, "seen": 2, "profile": True}, r.get("dog"))
    check("a reload half-way: the scene was on the map", r.get("midMap") is True, r.get("midMap"))
    pg.reload(); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    rl = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      return { blocker: !!document.querySelector('.ru-blocker'), seen: store.rankMapSeen,
               owed: (typeof rankUpSceneOwed === 'function') ? rankUpSceneOwed() : null }; }""")
    check("after the reload nothing is stuck and the rank-up is still owed (it plays again)",
          rl == {"blocker": False, "seen": 1, "owed": True}, rl)
    ctx.close()


def main():
    # ONLY_B245=slogan,modes runs just those build 245 polish sections.
    # ONLY_FN=check_b308_timer,... runs just those sections.
    fns = os.environ.get("ONLY_FN")
    if fns:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME)
            try:
                for name in fns.split(","):
                    globals()[name](br)
            finally:
                br.close()
        SERVER.shutdown()
        print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
        return 1 if FAILURES else 0
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
            check_b295(br)
            check_b297(br)
            check_b298(br)
            check_b299(br)
            check_b300(br)
            check_b301_chat(br)
            check_b302(br)
            check_b302_flares(br)
            check_b302_flagnote(br)
            check_b303(br)
            check_b304(br)
            check_b304_polish(br)
            check_b304_noxpfly(br)
            check_b305_flashcards(br)
            check_b305_resultstap(br)
            check_b306_marks(br)
            check_b306_fcmotion(br)
            check_b308_timer(br)
            check_b308_unlocks(br)
            check_b310(br)
            check_b310_vroom(br)
            # build 314, the Home / ranks / chat stream (check_b314h_*)
            check_b314h_flares(br)
            check_b314h_rankmap(br)
            check_b314h_tabs(br)
            check_b314h_chat(br)
            check_b314h_sheet(br)
            check_b314h_board(br)
            check_b314h_settings_calendar(br)
            check_b314h_host(br)
            check_b314h_home_clock(br)
            check_b314h_lead2(br)
            check_b314h_chat2(br)
            check_b314h_lobby(br)
            check_b311_rank(br)
            check_b312_shuffle(br)
            check_b312_results(br)
            check_b312_unlocks(br)
            check_b312_looks(br)
            check_b312_flares(br)
            check_b313_lead(br)
            check_b313_qmotion(br)
            check_b313_sheet2(br)
            check_b313_shuffle(br)
            check_b314_nova(br)
            check_b313_notice(br)
            check_b313_chars_centred(br)
            check_b313_no_sweep(br)
            check_b313_alive(br)
            check_b313_grades(br)
            check_b314_chars(br)
            check_b314_reactions(br)
            check_b314_sizes(br)
            check_b313_flares(br)
            check_b313_flares_glass(br)
            check_b313_pause(br)
            check_b313_fx(br)
            check_b314_swipe(br)
            check_b314_feel(br)
            check_b314_study(br)
            check_b314_sheet(br)
            check_b314_dragselect(br)
            check_b314_slider_release(br)
            check_b314_unlocks(br)
            check_b315_customize(br)
            check_b316_tiles(br)
            check_b317_daily(br)
            check_b317_volume(br)
            check_b317_cutspin(br)
            check_b317_tabplate(br)
            check_b317_rankup(br)
        finally:
            br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))"
          % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES),
             len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
