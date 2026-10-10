#!/usr/bin/env python3
"""Saving a test for later (build 319).

Madison: "Let's add the ability to pause a test and come back somehow ...
when hitting start studying, it would give a popup of the test you left and
saved asking if you want to rejoin or if you want to a new one. If you hit a
new one then the saved one loses its progress and you can't rejoin. You
can't save two or more at the same time ... This function won't be
available for review or virtual room of course."

What this holds the build to:
  1. Pause has three buttons in one column - Resume, Save and exit, Quit
     test - the group still on the screen's middle, and Quit's confirmation
     puts its buttons where Pause's first two are (both reference devices).
  2. Save and exit lands on an ordinary Home: no pop-up there, before or
     after a relaunch, and Home's unlock cards are not held by it.
  3. Start Studying offers the saved test - mode, units, "Question N of M"
     - with Resume test / Start a new test.
  4. Resume puts back the same questions in the same order, the same
     choice order on screen, what was answered, the in-a-row count and the
     clock, and the run finishes EXACTLY like one that was never put away:
     the same XP lines, the same hundo, the same unit counts, the study log
     credited once (an unpaused twin run in its own context is the control).
  5. A count-down clock does not run while the test is saved.
  6. Start a new test asks first; Keep saved test goes back; Delete and
     start new empties the slot and opens mode select.
  7. One slot: saving a second test replaces the first, which can no
     longer be reached.
  8. Not offered in Review / flashcards, the Virtual Room or the daily
     question - and finishing or leaving those leaves a saved test alone.
  9. Across an update: questions that moved are found by their keys; a
     question that is gone, or whose choices changed, drops the save and
     Start Studying says so once.
 10. An interrupted (not saved) run is still offered on Home (build 304),
     and "Not now" keeps it as the saved test.

Written against 8aded7f (build 318), where it fails:
  python3 tools/check-savetest.py
  python3 tools/check-savetest.py --against /path/to/old-index.html
Exits non-zero on any failure.
"""
import functools
import http.server
import io
import os
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
SRC = (sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv
       else os.path.join(ROOT, "index.html"))

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

USED_ACCOUNT = (
    '{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,'
    '"leaderboardOptIn":true,"lastModified":1700000000000,"seenProfileTour":true,"tourRev":99,"rankMapFx244":true,'
    '"seenUnitSelectTour":true,"seenUnitHoldTip":true,'
    '"testHistory":[{"ts":1700000000000,"mode":"exam","label":"Practice test",'
    '"score":92,"total":25,"correct":23,"units":["1"],"answers":[]}],'
    '"lifetime":{"points":14820,"answered":5400,"correct":4980,"drillPlays":64,'
    '"examPlays":22,"gamePlays":9,"perfectTests":141,"currentStreak":23,'
    '"longestStreak":57},'
    '"unlocksShown":{"chars":[],"banners":["hundos100"],"fx":["fireworks","blackhole","underwater","worldtree","bubbles","ufo"]}}')

BODY = INSET_RE.sub(lambda m: "0px", io.open(SRC, encoding="utf-8").read()) \
    .replace("let fbDb = null;", "let fbDb = null;" + FIRESTORE_STUB, 1)
_BUILD_M = re.search(r'const APP_BUILD = "([^"]+)"', BODY)
SERVED_BUILD = _BUILD_M.group(1) if _BUILD_M else ""

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


# Seeded ONCE per context, so a relaunch (reload) keeps what the app saved
# - the point of the whole feature is surviving one.
SEED_ONCE = ("try{ if(!localStorage.getItem('__seeded')){ localStorage.setItem('__seeded','1');"
             "localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
             "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
             "localStorage.setItem('class26e.penal55124.seen','1');"
             "localStorage.setItem('class26e.drill.v1', '%s'); } }catch(e){}" % USED_ACCOUNT)

# Cards that can land over a screen mid-check (a challenge completing, a
# character unlocking) are taken off as they arrive; nothing here is about them.
QUIET = ("setInterval(()=>[...document.body.children].forEach(n=>{ if(n.id!=='resume-offer' && n.id!=='intro-pop' && getComputedStyle(n).position==='fixed' && "
         "/challenge complete|character unlocked|unlocked|new banner/i.test(n.textContent||'') && !n.querySelector('#nextbtn')) n.remove(); }), 40);")


def settle(pg):
    pg.wait_for_timeout(2600)
    pg.evaluate("""()=>{ document.getElementById('splashscreen')?.remove(); __stub();
      document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
      theme.autoAdvance = false;
      if(!document.querySelector('[data-screen="home"]') && !testInProgress) showHome(); }""")
    pg.evaluate("()=>{" + QUIET + "}")


def booted(br, w, h, dpr=1):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr)
    ctx.add_init_script(SEED_ONCE)
    pg = ctx.new_page()
    pg.route("**/index.html", lambda r: r.fulfill(
        status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json*", lambda r: r.fulfill(
        status=200, headers={"content-type": "application/json"},
        body='{"build":"%s","frameId":"","note":""}' % SERVED_BUILD))
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)[:160]))
    pg.goto(URL)
    settle(pg)
    return ctx, pg, errors


def relaunch(pg):
    """iOS throws the app away: the page loads again from nothing."""
    pg.reload()
    settle(pg)


# Page-side helpers, defined on every call (a reload drops them).
H = """
const wait = ms => new Promise(r => setTimeout(r, ms));
const until = async (f, ms) => { const t0 = Date.now(); while(Date.now() - t0 < (ms || 8000)){ try{ if(f()) return true; }catch(e){} await wait(60); } return false; };
const UNIT = 'Identity Crimes';
const unitIdx = () => QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === UNIT && inWholeUnit(QUESTIONS[i]));
const start = async (mode, extra) => {
  cfg.mode = mode; cfg.units = [UNIT]; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'up'; cfg.flashcards = false;
  Object.assign(cfg, extra || {});
  if(mode === 'exam') cfg.examFeedback = false;
  beginRun(freshOrder(unitIdx()), null, (extra && extra.__minutes) || null);
  return until(() => document.querySelector('.qpanel .choice') && runStartTime != null, 9000);
};
const slotEl = s => document.querySelector('.qpanel .choice[data-index="' + s + '"]');
const choiceTexts = () => [...document.querySelectorAll('.qpanel .choice')].map(b => b.textContent.trim());
/* one question: right first time, or wrong once then right (drill) */
const answer = async (miss) => {
  const qi = order[pos], at = pos, right = correctSlot(qi);
  if(miss && runMode === 'drill'){
    const wrong = [...document.querySelectorAll('.qpanel .choice')].map(b => +b.dataset.index).find(s => s !== right);
    slotEl(wrong).click(); await wait(120);
  }
  slotEl(right).click(); await wait(140);
};
const next = async () => {
  const at = pos; advance();
  await until(() => !testInProgress || (pos === at + 1 && document.querySelector('.qpanel .choice')), 6000);
  await wait(80);
};
const snap = () => ({ points: store.lifetime.points || 0, answered: store.lifetime.answered, correct: store.lifetime.correct,
  perfects: (store.unitPerfects || {})[UNIT] || 0, plays: ((store.testStats || {})[UNIT] || {}).plays || 0,
  study: Object.values(store.studyLog || {}).reduce((a, b) => a + (Number(b) || 0), 0),
  hist: (store.testHistory || []).length });
"""


def js(body):
    return "async ()=>{ " + H + " const out = {}; try{ " + body + " }catch(e){ out.threw = String(e && e.stack || e).slice(0, 400); } return out; }"


def ev(pg, body):
    r = pg.evaluate(js(body))
    if r.get("threw"):
        print("     threw:", r["threw"])
    return r


# ---------------------------------------------------------------------------
def check_pause_menu(br):
    print("\n1. the pause menu: Resume, Save and exit, Quit test")
    for (w, h, dev) in ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")):
        ctx, pg, errors = booted(br, w, h)
        r = ev(pg, """
          await start('drill'); await answer(false); await next();
          pauseRun(); await wait(700);
          const bs = [...document.querySelectorAll('.pausepanel .actions button')];
          out.labels = bs.map(b => b.textContent.trim());
          const rs = bs.map(b => b.getBoundingClientRect());
          const st = document.querySelector('.pause-stack').getBoundingClientRect();
          out.stacked = rs.every((r, i) => i === 0 || r.top >= rs[i - 1].bottom - 1);
          out.sameWidth = rs.every(r => Math.abs(r.width - rs[0].width) < 1);
          out.centred = rs.every(r => Math.abs(r.left + r.width / 2 - innerWidth / 2) < 2);
          out.off = Math.round(Math.abs(st.top + st.height / 2 - innerHeight / 2));
          out.inView = rs.every(r => r.top >= 0 && r.bottom <= innerHeight);
          const at = () => [...document.querySelectorAll('.pausepanel .actions button')].map(b => { const q = b.getBoundingClientRect(); return [+q.left.toFixed(1), +q.top.toFixed(1), +q.width.toFixed(1)]; });
          const before = at();
          document.getElementById('pause-quit').click(); await wait(700);
          const conf = at();
          out.confTitle = (document.querySelector('.pausepanel .qnum') || {}).textContent;
          out.confText = (document.querySelector('.pausepanel .qtext') || {}).textContent;
          out.confLabels = [...document.querySelectorAll('.pausepanel .actions button')].map(b => b.textContent.trim());
          out.confSame = conf.length === 2 && conf.every((p, i) => p.every((v, j) => Math.abs(v - before[i][j]) < 0.6));
          out.conf = conf; out.before = before;
          /* Keep going puts Pause back with its three */
          document.querySelector('.pausepanel .actions button').click(); await wait(600);
          out.backLabels = [...document.querySelectorAll('.pausepanel .actions button')].map(b => b.textContent.trim());
          document.getElementById('pause-quit').click(); await wait(500);
          document.getElementById('quit-confirm').click(); await wait(900);
          out.quitHome = !!document.querySelector('[data-screen="home"]');
          out.quitSlot = localStorage.getItem('class26e.runsession.v1');
        """)
        check("%s: Pause reads Resume / Save and exit / Quit test, in that order" % dev,
              r.get("labels") == ["Resume", "Save and exit", "Quit test"], r.get("labels"))
        check("%s: one column, one width, centred, the group on the screen's middle (<= 8px), all on screen" % dev,
              r.get("stacked") and r.get("sameWidth") and r.get("centred") and r.get("off", 99) <= 8 and r.get("inView"),
              {k: r.get(k) for k in ("stacked", "sameWidth", "centred", "off", "inView")})
        check("%s: Quit asks first, says progress will be lost, and its buttons sit where Pause's first two are" % dev,
              "?" in str(r.get("confTitle")) and "lost" in str(r.get("confText")).lower() and r.get("confSame") is True,
              (r.get("confTitle"), r.get("confText"), r.get("confLabels"), r.get("before"), r.get("conf")))
        check("%s: Keep going returns to the three buttons" % dev,
              r.get("backLabels") == ["Resume", "Save and exit", "Quit test"], r.get("backLabels"))
        check("%s: Quit test leaves to Home with nothing saved" % dev,
              r.get("quitHome") is True and r.get("quitSlot") is None, (r.get("quitHome"), r.get("quitSlot")))
        check("%s: no page errors" % dev, not errors, errors[:3])
        ctx.close()


def check_save_resume_parity(br):
    print("\n2-5. save, relaunch, Start Studying, resume, finish - exactly like a run never put away")
    PLAN = "const MISS = [2, 7];"   # question positions answered wrong first (drill)
    # The control: the same unit, the same answers, the same pause in the
    # middle (the clock is stopped for it either way), never put away.
    ctx, pg, errors = booted(br, 440, 956)
    ctl = ev(pg, PLAN + """
      const before = snap();
      await start('drill');
      for(let k = 0; k < 5; k++){ await answer(MISS.includes(pos)); await next(); }
      await wait(2500);
      pauseRun(); await wait(400); resumeRun(); await wait(100);
      while(testInProgress){ await answer(MISS.includes(pos)); await next(); }
      await until(() => lastRunXpLines && lastRunXpLines.length, 5000);
      const after = snap();
      out.lines = lastRunXpLines.map(l => [l.key, l.value]);
      out.xp = lastRunXpEarned;
      out.delta = Object.fromEntries(Object.keys(after).map(k => [k, after[k] - before[k]]));
      out.pct = store.testHistory[0] && store.testHistory[0].pct;
      out.elapsed = store.testHistory[0] && store.testHistory[0].elapsedMs;
    """)
    ctx.close()
    # The same run, saved part-way and finished after a relaunch.
    ctx, pg, errors = booted(br, 440, 956)
    a = ev(pg, PLAN + """
      const before = snap(); localStorage.setItem('__before', JSON.stringify(before));
      await start('drill');
      for(let k = 0; k < 5; k++){ await answer(MISS.includes(pos)); await next(); }
      await wait(2500);
      /* the question on screen answered (and a miss on it) before saving */
      await answer(MISS.includes(pos));
      out.pos = pos; out.q = order[pos]; out.order = order.slice(); out.texts = choiceTexts();
      out.cleared = cleared; out.streak = runLiveStreak;
      out.elapsed = Date.now() - runStartTime;
      out.ticks = meterTicks ? meterTicks.slice(0, pos).map(t => t.className) : null;
      pauseRun(); await wait(500);
      const sb = document.getElementById('pause-save');
      out.hasSave = !!sb;
      if(sb){ sb.click(); await wait(1200); }
      out.home = !!document.querySelector('[data-screen="home"]');
      out.testInProgress = testInProgress;
      const raw = localStorage.getItem('class26e.runsession.v1');
      out.saved = raw ? JSON.parse(raw).saved === true : false;
      await wait(2600);
      out.offerOnHome = !!document.getElementById('resume-offer');
      out.studyAtSave = snap().study - before.study;
    """)
    check("Pause has Save and exit on a Drill", a.get("hasSave") is True, a.get("hasSave"))
    check("Save and exit lands on Home, out of the test, with the test saved",
          a.get("home") is True and a.get("testInProgress") is False and a.get("saved") is True,
          {k: a.get(k) for k in ("home", "testInProgress", "saved")})
    check("Home after Save and exit is ordinary: no pop-up", a.get("offerOnHome") is False, a.get("offerOnHome"))
    relaunch(pg)
    pg.wait_for_timeout(3200)
    b = ev(pg, """
      out.home = !!document.querySelector('[data-screen="home"]');
      out.offerOnHome = !!document.getElementById('resume-offer');
      out.unlocksHeld = typeof homeUnlockBlocked === 'function' ? homeUnlockBlocked() : null;
      document.querySelector('[data-screen="home"] #nextbtn').click(); await wait(600);
      const o = document.getElementById('resume-offer');
      out.offer = o ? o.textContent : null;
      out.offerBtns = o ? [...o.querySelectorAll('button')].map(b => b.textContent.trim()) : null;
      out.modeSelect = !!document.querySelector('.panel.modeselect');
    """)
    check("after a relaunch, Home is ordinary: no pop-up on its own", b.get("home") is True and b.get("offerOnHome") is False,
          (b.get("home"), b.get("offerOnHome")))
    check("a saved test does not hold Home's unlock cards", b.get("unlocksHeld") is False, b.get("unlocksHeld"))
    want_q = "Question %d of %d" % (a.get("pos", -9) + 1, len(a.get("order") or []))
    check("Start Studying offers the saved test: mode, unit, '%s'" % want_q,
          bool(b.get("offer")) and "Drill" in b["offer"] and "Identity Crimes" in b["offer"] and want_q in b["offer"]
          and not b.get("modeSelect"), b.get("offer"))
    check("its buttons are Resume test / Start a new test", b.get("offerBtns") == ["Resume test", "Start a new test"], b.get("offerBtns"))
    c = ev(pg, PLAN + """
      document.getElementById('resume-go').click();
      await until(() => document.querySelector('.qpanel .choice'), 4000); await wait(400);
      out.pos = pos; out.q = order[pos]; out.order = order.slice(); out.texts = choiceTexts();
      out.cleared = cleared; out.streak = runLiveStreak;
      out.elapsed = Date.now() - runStartTime;
      out.ticks = meterTicks ? meterTicks.slice(0, pos).map(t => t.className) : null;
      out.saveAfterResume = (() => { const r = localStorage.getItem('class26e.runsession.v1'); return r ? JSON.parse(r).saved : null; })();
      await next();
      while(testInProgress){ await answer(MISS.includes(pos)); await next(); }
      await until(() => lastRunXpLines && lastRunXpLines.length, 5000);
      const before = JSON.parse(localStorage.getItem('__before'));
      const after = snap();
      out.lines = lastRunXpLines.map(l => [l.key, l.value]);
      out.xp = lastRunXpEarned;
      out.delta = Object.fromEntries(Object.keys(after).map(k => [k, after[k] - before[k]]));
      out.pct = store.testHistory[0] && store.testHistory[0].pct;
      out.runElapsed = store.testHistory[0] && store.testHistory[0].elapsedMs;
      out.slotAfter = localStorage.getItem('class26e.runsession.v1');
      /* and Start Studying now goes straight to the modes */
      showHome(); await wait(500);
      document.querySelector('[data-screen="home"] #nextbtn').click(); await wait(600);
      out.straightToModes = !!document.querySelector('.panel.modeselect') && !document.getElementById('resume-offer');
    """)
    check("resume puts back the same questions in the same order, on the same question",
          c.get("order") == a.get("order") and c.get("pos") == a.get("pos") and c.get("q") == a.get("q"),
          (a.get("pos"), c.get("pos")))
    check("the same choice order on screen", c.get("texts") == a.get("texts"), (a.get("texts"), c.get("texts")))
    check("what was answered is still answered, the meter painted the same, the in-a-row count kept",
          c.get("cleared") == a.get("cleared") and c.get("ticks") == a.get("ticks") and c.get("streak") == a.get("streak"),
          {k: (a.get(k), c.get(k)) for k in ("cleared", "streak", "ticks")})
    check("the clock picks up where it stopped (the time closed does not count)",
          abs((c.get("elapsed") or 0) - (a.get("elapsed") or 0)) < 1500, (a.get("elapsed"), c.get("elapsed")))
    check("once resumed it is a live run again (the slot is no longer 'saved')", c.get("saveAfterResume") is False, c.get("saveAfterResume"))
    check("the XP card is line for line the unpaused run's", c.get("lines") == ctl.get("lines") and c.get("xp") == ctl.get("xp"),
          (ctl.get("lines"), c.get("lines")))
    dk = ("points", "answered", "correct", "perfects", "plays", "hist")
    check("the account moved exactly as the unpaused run moved it (XP, answers, hundos, plays, history)",
          all((c.get("delta") or {}).get(k) == (ctl.get("delta") or {}).get(k) for k in dk) and c.get("pct") == ctl.get("pct"),
          {k: ((ctl.get("delta") or {}).get(k), (c.get("delta") or {}).get(k)) for k in dk})
    study_c, study_ctl, run_el = (c.get("delta") or {}).get("study", 0), (ctl.get("delta") or {}).get("study", 0), c.get("runElapsed") or 0
    check("the study log is credited once for the whole run, not twice for the first part",
          a.get("studyAtSave", 0) > 2000 and abs(study_c - run_el) < 1500,
          {"atSave": a.get("studyAtSave"), "total": study_c, "runElapsed": run_el, "control": study_ctl})
    check("finished, the slot is empty and Start Studying goes straight to the modes",
          c.get("slotAfter") is None and c.get("straightToModes") is True, (c.get("slotAfter"), c.get("straightToModes")))
    check("no page errors", not errors, errors[:3])
    ctx.close()

    # Hundo eligibility: a clean full-unit run, saved half-way, still earns
    # its hundo exactly as the clean run does.
    res = []
    for paused in (False, True):
        ctx, pg, errors = booted(br, 440, 956)
        r = ev(pg, """
          const before = snap(); localStorage.setItem('__before', JSON.stringify(before));
          await start('drill');
          for(let k = 0; k < 6; k++){ await answer(false); await next(); }
          if(%s){
            pauseRun(); await wait(400); document.getElementById('pause-save').click(); await wait(800);
          }
        """ % ("true" if paused else "false"))
        if paused:
            relaunch(pg)
            ev(pg, """document.querySelector('[data-screen="home"] #nextbtn').click(); await wait(600);
                      document.getElementById('resume-go').click(); await until(() => document.querySelector('.qpanel .choice'), 4000); await wait(300);""")
        r = ev(pg, """
          while(testInProgress){ await answer(false); await next(); }
          await until(() => lastRunXpLines && lastRunXpLines.length, 5000);
          const before = JSON.parse(localStorage.getItem('__before')); const after = snap();
          out.lines = lastRunXpLines.map(l => [l.key, l.value]);
          out.perfects = after.perfects - before.perfects;
        """)
        res.append(r)
        ctx.close()
    check("a clean run saved half-way still earns its hundo, and its XP card matches the clean run's",
          res[0].get("perfects") == 1 and res[1].get("perfects") == 1 and res[0].get("lines") == res[1].get("lines"),
          (res[0].get("perfects"), res[1].get("perfects"), res[0].get("lines"), res[1].get("lines")))


def check_timer(br):
    print("\n5. a count-down clock does not run while the test is saved")
    ctx, pg, errors = booted(br, 440, 956)
    a = ev(pg, """
      await start('exam', { timer: 'down', timerMinutes: 10 });
      for(let k = 0; k < 3; k++){ slotEl(correctSlot(order[pos])).click(); await wait(120); await next(); }
      await wait(1500);
      out.left = timerDeadline - Date.now();
      pauseRun(); await wait(300);
      out.hasSave = !!document.getElementById('pause-save');
      document.getElementById('pause-save')?.click(); await wait(700);
    """)
    pg.wait_for_timeout(4000)
    relaunch(pg)
    b = ev(pg, """
      document.querySelector('[data-screen="home"] #nextbtn').click(); await wait(600);
      const o = document.getElementById('resume-offer'); out.offer = o ? o.textContent : null;
      document.getElementById('resume-go')?.click(); await until(() => document.querySelector('.qpanel .choice'), 4000); await wait(200);
      out.left = timerDeadline ? timerDeadline - Date.now() : null; out.mode = runMode; out.pos = pos;
    """)
    check("an Exam offers Save and exit too", a.get("hasSave") is True, a.get("hasSave"))
    check("the pop-up says it is an Exam and how much time is left", bool(b.get("offer")) and "Exam" in b["offer"] and "left on the timer" in b["offer"], b.get("offer"))
    check("resumed, the time left is what it was at the pause (within 1.5s), not minus the ~8s it sat saved",
          b.get("left") is not None and abs(b["left"] - a.get("left", 0)) < 1500 and b.get("pos") == 3,
          (a.get("left"), b.get("left"), b.get("pos")))
    check("no page errors", not errors, errors[:3])
    ctx.close()


def check_discard_and_one_slot(br):
    print("\n6-7. Start a new test asks first; one saved test at a time")
    ctx, pg, errors = booted(br, 440, 956)
    r = ev(pg, """
      const save = async (mode, n) => { await start(mode); for(let k = 0; k < n; k++){ await answer(false); await next(); }
        pauseRun(); await wait(300); document.getElementById('pause-save').click(); await wait(700); return order.slice(); };
      const tapStart = async () => { document.querySelector('[data-screen="home"] #nextbtn').click(); await wait(600); };
      const A = await save('drill', 2);
      await tapStart();
      document.getElementById('resume-new').click(); await wait(400);
      const card = document.querySelector('#resume-offer .resume-card');
      out.confirm = card ? card.textContent : null;
      out.confirmBtns = card ? [...card.querySelectorAll('button')].map(b => b.textContent.trim()) : null;
      out.stillSaved = !!localStorage.getItem('class26e.runsession.v1');
      document.getElementById('resume-keep').click(); await wait(300);
      out.backToOffer = !!document.getElementById('resume-go');
      /* a tap outside closes it and changes nothing */
      const wrap = document.getElementById('resume-offer');
      wrap.dispatchEvent(new MouseEvent('click', { bubbles: true })); await wait(400);
      out.closedOutside = !document.getElementById('resume-offer') && !!localStorage.getItem('class26e.runsession.v1');
      /* one slot: a test started after Start a new test replaces it */
      await tapStart();
      document.getElementById('resume-new').click(); await wait(300);
      document.getElementById('resume-delete').click(); await wait(600);
      out.deleted = localStorage.getItem('class26e.runsession.v1') === null;
      out.modeSelect = !!document.querySelector('.panel.modeselect');
      showHome(); await wait(400);
      const B = await save('exam', 4);
      await tapStart();
      const o = document.getElementById('resume-offer'); out.offerB = o ? o.textContent : null;
      out.keys = Object.keys(localStorage).filter(k => /runsession|savedtest/.test(k));
      document.getElementById('resume-go').click(); await until(() => document.querySelector('.qpanel .choice'), 4000);
      out.resumedB = JSON.stringify(order) === JSON.stringify(B) && runMode === 'exam' && pos === 4;
      out.notA = JSON.stringify(order) !== JSON.stringify(A) || runMode !== 'drill';
    """)
    check("Start a new test asks first, saying the saved test will be deleted",
          r.get("confirm") and "deleted" in r["confirm"] and r.get("stillSaved") is True, (r.get("confirm"), r.get("confirmBtns")))
    check("Keep saved test goes back to the offer; a tap outside closes it and keeps the test",
          r.get("backToOffer") is True and r.get("closedOutside") is True, (r.get("backToOffer"), r.get("closedOutside")))
    check("Delete and start new empties the slot and opens the modes",
          r.get("deleted") is True and r.get("modeSelect") is True, (r.get("deleted"), r.get("modeSelect")))
    check("one slot: the second saved test is the one offered and resumed; the first is gone",
          bool(r.get("offerB")) and "Exam" in r["offerB"] and "Question 5 of" in r["offerB"] and r.get("resumedB") is True
          and r.get("notA") is True and r.get("keys") == ["class26e.runsession.v1"],
          (r.get("offerB"), r.get("resumedB"), r.get("keys")))
    check("no page errors", not errors, errors[:3])
    ctx.close()


def check_not_offered(br):
    print("\n8. not offered in Review, flashcards, the Virtual Room or the daily question - and they leave a save alone")
    ctx, pg, errors = booted(br, 440, 956)
    r = ev(pg, """
      /* a saved test first */
      await start('drill'); for(let k = 0; k < 3; k++){ await answer(false); await next(); }
      pauseRun(); await wait(300); document.getElementById('pause-save').click(); await wait(700);
      const slot = () => localStorage.getItem('class26e.runsession.v1');
      const saved0 = slot();
      /* flashcards (Review) */
      cfg.mode = 'review'; cfg.units = [UNIT]; cfg.source = 'all'; cfg.versions = {};
      showFlashcards([UNIT], 'all', {}); await wait(700);
      pauseRun(); await wait(500);
      out.fcPause = !!document.querySelector('.pausepanel');
      out.fcSave = !!document.getElementById('pause-save');
      showHome(); await wait(400);
      /* Review's answer list has no Pause at all */
      showAnswerReview([UNIT], 'all', {}); await wait(700);
      out.reviewPause = !pauseBtn.hidden;
      showHome(); await wait(400);
      /* a Virtual Room run */
      inVirtualRoom = true; vroomStartAt = null; cfg.mode = 'exam'; cfg.units = [UNIT];
      beginRun(unitIdx().slice(0, 4), null, null);
      await until(() => document.querySelector('.qpanel .choice') && runStartTime != null, 9000);
      pauseRun(); await wait(400);
      out.vrPause = !!document.querySelector('.pausepanel');
      out.vrSave = !!document.getElementById('pause-save');
      out.vrSavable = runSessionSavable();
      document.dispatchEvent(new Event('visibilitychange'));
      out.vrKept = slot() === saved0;
      resumeRun(); await wait(200);
      while(testInProgress){ slotEl(correctSlot(order[pos])).click(); await wait(100); const at = pos; advance(); await until(() => !testInProgress || pos === at + 1, 3000); await wait(60); }
      out.vrFinishKept = slot() === saved0;
      inVirtualRoom = false;
      showHome(); await wait(500);
      out.vrHomeKept = slot() === saved0;
      /* the daily question */
      store.dailyQuestionDate = null;
      startDailyQuestion(); await until(() => document.querySelector('.qpanel .choice'), 4000); await wait(300);
      out.dailyPause = !pauseBtn.hidden;
      out.dailySavable = runSessionSavable();
      confirmExitTest(); await wait(600);
      out.dailyExitKept = slot() === saved0;
      out.stillOffered = !!readRunSession() && readRunSession().saved === true;
    """)
    check("flashcards: Pause has no Save and exit", r.get("fcPause") is True and r.get("fcSave") is False, (r.get("fcPause"), r.get("fcSave")))
    check("Review's answer list has no Pause", r.get("reviewPause") is False, r.get("reviewPause"))
    check("a Virtual Room run: Pause has no Save and exit and it never writes the slot",
          r.get("vrPause") is True and r.get("vrSave") is False and r.get("vrSavable") is False and r.get("vrKept") is True,
          {k: r.get(k) for k in ("vrPause", "vrSave", "vrSavable", "vrKept")})
    check("finishing a Virtual Room run, then Home, leaves the saved test",
          r.get("vrFinishKept") is True and r.get("vrHomeKept") is True, (r.get("vrFinishKept"), r.get("vrHomeKept")))
    check("the daily question has no Pause, cannot be saved, and leaving it leaves the saved test",
          r.get("dailyPause") is False and r.get("dailySavable") is False and r.get("dailyExitKept") is True and r.get("stillOffered") is True,
          {k: r.get(k) for k in ("dailyPause", "dailySavable", "dailyExitKept", "stillOffered")})
    check("no page errors", not errors, errors[:3])
    ctx.close()


def check_update(br):
    print("\n9. a saved test across an update")
    ctx, pg, errors = booted(br, 440, 956)
    r = ev(pg, """
      const save = async () => { await start('drill'); for(let k = 0; k < 3; k++){ await answer(k === 1); await next(); }
        pauseRun(); await wait(300); document.getElementById('pause-save').click(); await wait(700);
        return JSON.parse(localStorage.getItem('class26e.runsession.v1')); };
      const tapStart = async () => { document.querySelector('[data-screen="home"] #nextbtn').click(); await wait(600); };
      /* (a) the questions were numbered differently by the build that saved
         it: every index 7 higher. Same keys, so it comes back exactly. */
      let s = await save();
      const sh = i => i + 7, shObj = o => Object.fromEntries(Object.entries(o || {}).map(([k, v]) => [sh(+k), v]));
      const moved = Object.assign({}, s, { build: 'an-older-build', order: s.order.map(sh), lastRunPool: s.lastRunPool.map(sh),
        originalTestPool: s.originalTestPool.map(sh), attempts: shObj(s.attempts), picked: shObj(s.picked), firstPick: shObj(s.firstPick),
        layout: shObj(s.layout), timedOutSet: shObj(s.timedOutSet), qTimeMs: shObj(s.qTimeMs), qkeys: shObj(s.qkeys) });
      localStorage.setItem('class26e.runsession.v1', JSON.stringify(moved));
      await tapStart();
      out.movedOffer = !!document.getElementById('resume-go');
      document.getElementById('resume-go')?.click(); await until(() => document.querySelector('.qpanel .choice'), 4000);
      out.movedSame = JSON.stringify(order) === JSON.stringify(s.order) && pos === s.pos && JSON.stringify(attempts) === JSON.stringify(s.attempts);
      showHome(); await wait(400);
      /* (b) a question in it is gone */
      s = await save();
      const gone = Object.assign({}, s, { qkeys: Object.assign({}, s.qkeys, { [s.order[5]]: 'Removed unit|999|deadbeef' }) });
      localStorage.setItem('class26e.runsession.v1', JSON.stringify(gone));
      await tapStart();
      const card = document.querySelector('#resume-offer .resume-card');
      out.goneMsg = card ? card.textContent : null;
      out.goneSlot = localStorage.getItem('class26e.runsession.v1');
      document.getElementById('resume-dropped-ok')?.click(); await wait(500);
      out.goneModes = !!document.querySelector('.panel.modeselect');
      showHome(); await wait(400); await tapStart();
      out.goneOnce = !document.getElementById('resume-offer') && !!document.querySelector('.panel.modeselect');
      showHome(); await wait(400);
      /* (c) a question's choices changed in number: its saved order no longer fits */
      s = await save();
      const qi = s.order[0];
      const lay = Object.assign({}, s.layout, { [qi]: (s.layout[qi] || QUESTIONS[qi].choices.map((c, k) => k)).concat([QUESTIONS[qi].choices.length]) });
      localStorage.setItem('class26e.runsession.v1', JSON.stringify(Object.assign({}, s, { layout: lay })));
      await tapStart();
      out.choicesMsg = !!document.getElementById('resume-dropped-ok');
      document.getElementById('resume-dropped-ok')?.click(); await wait(400);
    """)
    check("questions numbered differently by the build that saved it are found by their keys: the same run comes back",
          r.get("movedOffer") is True and r.get("movedSame") is True, (r.get("movedOffer"), r.get("movedSame")))
    check("a question that is gone drops the save, and Start Studying says so",
          bool(r.get("goneMsg")) and "could not be restored" in r["goneMsg"] and r.get("goneSlot") is None and r.get("goneModes") is True,
          (r.get("goneMsg"), r.get("goneSlot"), r.get("goneModes")))
    check("it says so once", r.get("goneOnce") is True, r.get("goneOnce"))
    check("a question whose choices changed in number drops the save too", r.get("choicesMsg") is True, r.get("choicesMsg"))
    check("no page errors", not errors, errors[:3])
    ctx.close()


def check_interrupted(br):
    print("\n10. a run the app lost is still offered on Home; Not now keeps it as the saved test")
    ctx, pg, errors = booted(br, 440, 956)
    ev(pg, "await start('drill'); for(let k = 0; k < 4; k++){ await answer(false); await next(); } document.dispatchEvent(new Event('visibilitychange'));")
    relaunch(pg)
    pg.wait_for_timeout(3600)
    r = ev(pg, """
      const o = document.getElementById('resume-offer');
      out.offer = o ? o.textContent : null;
      out.btns = o ? [...o.querySelectorAll('button')].map(b => b.textContent.trim()) : null;
      out.heldWhileOffered = homeUnlockBlocked();
      document.getElementById('resume-later')?.click(); await wait(500);
      out.savedNow = (readRunSession() || {}).saved === true;
      out.heldAfter = homeUnlockBlocked();
    """)
    relaunch(pg)
    pg.wait_for_timeout(3600)
    r2 = ev(pg, """
      out.offerAgain = !!document.getElementById('resume-offer');
      document.querySelector('[data-screen="home"] #nextbtn').click(); await wait(600);
      out.atStart = !!document.getElementById('resume-go');
      document.getElementById('resume-go')?.click(); await until(() => document.querySelector('.qpanel .choice'), 4000);
      out.pos = pos;
    """)
    check("Home offers the lost run: Resume test / Not now",
          bool(r.get("offer")) and "interrupted" in r["offer"] and r.get("btns") == ["Resume test", "Not now"], (r.get("offer"), r.get("btns")))
    check("Not now keeps it, as a saved test that no longer holds Home's cards",
          r.get("savedNow") is True and r.get("heldAfter") is False, (r.get("savedNow"), r.get("heldAfter")))
    check("after that it waits for Start Studying, not Home, and resumes where it was",
          r2.get("offerAgain") is False and r2.get("atStart") is True and r2.get("pos") == 4, r2)
    check("no page errors", not errors, errors[:3])
    ctx.close()


SECTIONS = [check_pause_menu, check_save_resume_parity, check_timer, check_discard_and_one_slot,
            check_not_offered, check_update, check_interrupted]


def main():
    only = os.environ.get("ONLY_FN")
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        try:
            for fn in SECTIONS:
                if only and fn.__name__ not in only.split(","):
                    continue
                try:
                    fn(br)
                except Exception as e:  # a section that cannot even run is a failure, not a crash
                    check("%s ran to the end" % fn.__name__, False, str(e)[:300])
        finally:
            br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
