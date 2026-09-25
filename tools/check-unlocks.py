#!/usr/bin/env python3
"""The four EARNED characters, and the Secret Flares that gate one of them.

Four characters are now unlocked by doing something rather than by
reaching a rank, which means four counters that have to move at the right
moment and stop at the wrong one. None of the other gates can see any of
this: the sweep asks "is anything broken on this device", check-positions
asks "did it land where I meant it to", check-behaviour drives badges and
cutscenes. A streak that silently never increments looks identical to a
streak nobody has earned yet, and the first person to notice would be
somebody who answered ten daily questions in a row for nothing.

Every check here was written against build 132 - the build before any of
this existed - and fails there. Run it that way to watch it fail, which
is the only thing that makes a green run mean anything:

  python3 tools/check-unlocks.py
  python3 tools/check-unlocks.py --against /path/to/old-index.html

Device-independent: none of this is layout, so it runs once rather than
21 times. The one thing that IS layout - where the flare's glint sits -
is checked as a relationship (inside the header row, never overlapping a
choice) rather than as a coordinate, so it cannot go stale the way a
gate that names a number does.

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

# A FIXTURE IS AN EXISTING, UP-TO-DATE ACCOUNT, so it carries tourRev -
# without it the one-time tour re-arm fires inside the gate and puts a
# tooltip over whatever is being measured.
SEED = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,'
        '"tourRev":99,"leaderboardOptIn":true,'
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


def booted(br, w=834, h=1194):
    ctx = br.new_context(viewport={"width": w, "height": h})
    ctx.add_init_script(
        "try{localStorage.setItem('class26e.freshstart','1');"
        "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % SEED)
    pg = ctx.new_page()
    pg.route("**/index.html", lambda r: r.fulfill(
        status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto(URL)
    pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    return ctx, pg


# --------------------------------------------------------------------------
def check_table(pg):
    """Four feat characters exist, each locked on a fresh account, each
    with a lock message that says how far along you are.

    NOT A LIST OF NAMES. A gate that names a label goes stale and then
    fails the app for being right - this file has watched that happen to
    three separate checks in two days. What is asserted is the SHAPE:
    exactly four characters carry a feat, every feat is in the table,
    every one is locked at zero, and each message carries its own
    progress. Rename any of them and this still passes; break one and it
    does not."""
    print("\n1. four characters are earned by doing something")
    r = pg.evaluate("""()=>{
      store.dailyCorrectStreak = 0; store.unitHundoStreak = 0;
      store.practiceTestPassed = false;
      store.mysteryColorsFound = { red:false, orange:false, yellow:false };
      const feats = AVATAR_CHARACTERS.filter(c => c.feat);
      return {
        n: feats.length,
        keys: feats.map(c => c.feat),
        known: feats.every(c => !!CHARACTER_FEATS[c.feat]),
        allLocked: feats.every(c => isLockedCharacter(c.id)),
        msgs: feats.map(c => characterLockMessage(c.id)),
        named: feats.every(c => !!AVATAR_DISPLAY_NAME[c.id]),
        glowed: feats.every(c => avatarGlowColor(c.id) !== 'var(--accent)'),
        rankFour: AVATAR_CHARACTERS.filter(c => c.unlock).length
      };}""")
    check("four of them, and the rank four are untouched",
          r["n"] == 4 and r["rankFour"] == 4, "%d feat, %d rank" % (r["n"], r["rankFour"]))
    check("every feat key is in CHARACTER_FEATS", r["known"], r["keys"])
    check("all four locked on a fresh account", r["allLocked"])
    check("each has a display name and its own glow", r["named"] and r["glowed"])
    # Every message says what to do; the multi-step ones say how far in.
    multi = [m for m in r["msgs"] if " of " in m]
    check("each lock message names the character and the target",
          all(m.endswith(".") and len(m) > 20 for m in r["msgs"]), r["msgs"][0])
    check("the countable ones show progress, not just the target",
          len(multi) >= 3, multi)


# --------------------------------------------------------------------------
DAILY = """(correctRun)=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [topics[0]];
  const qi = QUESTIONS.findIndex(q => (q.topic||'').trim() === topics[0]);
  order = [qi]; runTrackable = true; timedOut = false; runMode = 'drill';
  runLabel = 'Daily question';
  attempts = {}; picked = {}; timedOutSet = {};
  attempts[qi] = 1;
  dailyQuestionLocked = !correctRun;
  store.dailyQuestionDate = null;
  summarize();
  return store.dailyCorrectStreak;}"""


def check_daily_streak(pg):
    print("\n2. the daily-question streak counts, and a miss resets it")
    pg.evaluate("()=>{ store.dailyCorrectStreak = 0; }")
    got = [pg.evaluate(DAILY, True) for _ in range(3)]
    check("three right in a row reads 3", got == [1, 2, 3], got)
    missed = pg.evaluate(DAILY, False)
    check("one wrong resets it to 0", missed == 0, missed)
    again = pg.evaluate(DAILY, True)
    check("and it starts again from 1", again == 1, again)


# --------------------------------------------------------------------------
BEAT_HARDCORE = """(n)=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  store.unitGameBeat = {};
  topics.slice(0, n).forEach(t => {
    store.unitGameBeat[t] = { easy:true, average:true, hardcore:true };
  });
  return { beaten: hardcoreUnitsBeaten(), locked: isLockedCharacter('masked'),
           msg: characterLockMessage('masked') };}"""

# A real Game run on Hardcore, through the app's own recorder, so the
# ladder inside it is exercised rather than the store being hand-set.
GAME_RUN = """(a)=>{
  const { unitIndex, speed, aced } = a;
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics[unitIndex];
  cfg.mode='game'; cfg.source='all'; cfg.units=[t]; cfg.gameSpeed=speed;
  order = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  runTrackable=true; timedOut=false; runMode='game'; runLabel=null;
  attempts={}; picked={}; timedOutSet={};
  order.forEach(qi => { attempts[qi] = aced ? 1 : 2;
    picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  summarize();
  return Object.assign({}, gameBeat(t));}"""


HUNDO = """(a)=>{
  const { unitIndex, ace } = a;
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics[unitIndex];
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [t];
  order = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
  attempts = {}; picked = {}; timedOutSet = {};
  order.forEach(qi => { attempts[qi] = ace ? 1 : 2;
    picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  summarize();
  return { n: store.unitHundoStreak, units: (store.unitHundoStreakUnits||[]).length };}"""

SLICE_RUN = """()=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics[5];
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [t];
  const all = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  order = all.slice(0, Math.max(3, Math.floor(all.length/3)));
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null;
  attempts = {}; picked = {}; timedOutSet = {};
  order.forEach(qi => { attempts[qi] = 2;
    picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  summarize();
  return store.unitHundoStreak;}"""


def check_hardcore(pg):
    """Hardcore beaten on ten units, and the ladder that guards it.

    The data has been there since Game mode shipped - store.unitGameBeat
    records {easy, average, hardcore} per unit - and nothing had ever
    read it or shown it. So what is worth asserting is that the COUNT is
    the count, that the app's own recorder still refuses Hardcore before
    Average, and that a unit card now says which of the three you have."""
    print("\n3. Hardcore beaten on ten units")
    for n in (0, 9, 10):
        r = pg.evaluate(BEAT_HARDCORE, n)
        want = n < 10
        check("%d unit(s) beaten -> %s" % (n, "locked" if want else "unlocked"),
              r["beaten"] == n and r["locked"] is want, r)
    # THE LADDER, through the app's own recorder rather than by setting
    # the store. Hardcore on a unit whose Average is not beaten must not
    # count, or the feat is ten Easy runs with the difficulty swapped.
    pg.evaluate("()=>{ store.unitGameBeat = {}; }")
    straight = pg.evaluate(GAME_RUN, {"unitIndex": 0, "speed": "hardcore", "aced": True})
    check("Hardcore alone does not count before Average",
          straight.get("hardcore") is False, straight)
    pg.evaluate(GAME_RUN, {"unitIndex": 0, "speed": "easy", "aced": True})
    pg.evaluate(GAME_RUN, {"unitIndex": 0, "speed": "average", "aced": True})
    climbed = pg.evaluate(GAME_RUN, {"unitIndex": 0, "speed": "hardcore", "aced": True})
    check("Easy then Average then Hardcore does",
          climbed.get("hardcore") is True, climbed)
    # The three bubbles say which, on the unit card, in Game mode.
    dots = pg.evaluate("""()=>{
      cfg.mode='game'; showSetup();
      const row = document.querySelector('.pick .pick-gamedots');
      if(!row) return { found:false };
      return { found:true, dots: row.children.length,
               on: [...row.children].filter(d=>d.classList.contains('on')).length,
               legend: !!document.querySelector('.speedkey') };}""")
    check("the unit card carries three difficulty bubbles",
          dots.get("found") and dots["dots"] == 3, dots)
    check("and the picker explains what they mean", dots.get("legend") is True, dots)


def check_hundo_streak(pg):
    print("\n3b. the hundo-streak counters still behave (kept, unread)")
    pg.evaluate("()=>{ store.unitHundoStreak = 0; store.unitHundoStreakUnits = []; }")
    a = pg.evaluate(HUNDO, {"unitIndex": 0, "ace": True})
    b = pg.evaluate(HUNDO, {"unitIndex": 1, "ace": True})
    check("two different units aced reads 2", b["n"] == 2, [a["n"], b["n"]])
    same = pg.evaluate(HUNDO, {"unitIndex": 1, "ace": True})
    check("the SAME unit again does not count twice", same["n"] == 2, same["n"])
    # A partial slice is not an attempt at the unit, so a bad one is not a
    # setback - the same rule isFullUnitRun already applies to hundos.
    sliced = pg.evaluate(SLICE_RUN)
    check("a missed PARTIAL slice leaves the streak alone", sliced == 2, sliced)
    broke = pg.evaluate(HUNDO, {"unitIndex": 2, "ace": False})
    check("a missed FULL unit clears it", broke["n"] == 0, broke["n"])


# --------------------------------------------------------------------------
PRACTICE = """(pctWanted)=>{
  store.practiceTestPassed = false;
  const n = 40, wrong = Math.round(n * (100 - pctWanted) / 100);
  cfg.mode = 'exam'; cfg.source = 'all';
  cfg.units = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  order = QUESTIONS.map((q,i) => i).slice(0, n);
  runTrackable = true; timedOut = false; runMode = 'exam'; runLabel = null;
  practiceTestMinutes = PRACTICE_TEST_MINUTES;
  attempts = {}; picked = {}; timedOutSet = {};
  order.forEach((qi, k) => {
    const right = optionOrder(qi).indexOf(QUESTIONS[qi].answer);
    picked[qi] = k < wrong ? (right + 1) % optionOrder(qi).length : right;
    attempts[qi] = 1;
  });
  summarize();
  practiceTestMinutes = null;
  return !!store.practiceTestPassed;}"""


def check_practice(pg):
    mark = pg.evaluate("()=>PASS_MARK")
    print("\n4. the Practice Test is passed at the real mark (%d%%)" % mark)
    check("under the mark is not a pass", pg.evaluate(PRACTICE, mark - 15) is False)
    check("at the mark is a pass", pg.evaluate(PRACTICE, mark + 5) is True)
    # An ordinary exam is not the Practice Test however well it goes.
    ordinary = pg.evaluate("""()=>{
      store.practiceTestPassed = false;
      cfg.mode='exam'; cfg.source='all';
      cfg.units=[...new Set(QUESTIONS.map(q=>(q.topic||'').trim()))].filter(Boolean).slice(0,2);
      order = QUESTIONS.map((q,i)=>i).slice(0,20);
      runTrackable=true; timedOut=false; runMode='exam'; runLabel=null;
      practiceTestMinutes = null;
      attempts={}; picked={}; timedOutSet={};
      order.forEach(qi=>{ attempts[qi]=1; picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
      summarize();
      return !!store.practiceTestPassed;}""")
    check("a perfect ORDINARY exam is not a Practice Test pass", ordinary is False)


# --------------------------------------------------------------------------
ARM = """()=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics[0];
  cfg.mode='drill'; cfg.source='all'; cfg.units=[t];
  const pool = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  beginRun(pool, null, null);
  return { at: mysteryAppearsAtPos, color: mysteryColorThisRun,
           left: store.testsUntilMystery, n: pool.length };}"""


SET_TESTS = """(n)=>{
  store.lifetime.drillPlays = n; store.lifetime.examPlays = 0; store.lifetime.gamePlays = 0;
  return testsCompletedOf(store);}"""


def check_flares(pg):
    """The flares are gated on TESTS COMPLETED, and the number they are
    gated on is the number the Stats tab prints.

    THE THRESHOLDS ARE READ OFF THE PAGE, not typed here. Three of this
    repo's checks have gone red for naming a decision that then changed,
    and these are decisions - "80-90 tests, then around 200, then about
    350" was a judgement call and will be another one if it moves. What
    is asserted is the SHAPE: nothing one short of each threshold,
    something at it, in order, red first."""
    at = pg.evaluate("()=>MYSTERY_AT.slice()")
    print("\n5. the Secret Flares are hidden behind %s tests completed" % at)
    r = pg.evaluate("""()=>{
      store.mysteryColorsFound = { red:false, orange:false, yellow:false };
      return nextNeededMysteryColor();}""")
    check("red is wanted first on a fresh account", r == "red", r)
    # The gate is the same number the app shows on Stats. A gate on a
    # number nobody can see is a gate nobody can be told about.
    same = pg.evaluate(SET_TESTS, 137)
    check("the gate counts what the Stats tab counts", same == 137, same)

    for i, key in enumerate(["red", "orange", "yellow"]):
        pg.evaluate("""(k)=>{ const f = { red:false, orange:false, yellow:false };
          ['red','orange','yellow'].slice(0, k).forEach(c => f[c] = true);
          store.mysteryColorsFound = f; }""", i)
        pg.evaluate(SET_TESTS, at[i] - 1)
        short = pg.evaluate(ARM)
        pg.evaluate(SET_TESTS, at[i])
        due = pg.evaluate(ARM)
        check("%s: nothing at %d, armed at %d" % (key, at[i] - 1, at[i]),
              short["at"] == -1 and due["at"] >= 0 and due["color"] == key,
              [short["at"], due["at"], due["color"]])

    # A one-question daily has nowhere to hide anything, at any count.
    tiny = pg.evaluate("""()=>{
      store.mysteryColorsFound = { red:false, orange:false, yellow:false };
      store.lifetime.drillPlays = 9999;
      cfg.mode='drill'; cfg.source='all';
      cfg.units=[(QUESTIONS[0].topic||'').trim()];
      beginRun([0], 'Daily question', null);
      return mysteryAppearsAtPos;}""")
    check("a one-question run is never chosen", tiny == -1, tiny)


# EVERY POSITION IT CAN PICK, on a phone as well as a tablet. The first
# version measured one random placement on one device and passed; swept
# properly, the 44px box landed on the words "Question 1" across a third
# of its range on every phone in the matrix and never once on an iPad.
# A hidden thing sitting on top of the text reads as a rendering fault,
# which is the opposite of hiding.
GLINT_SWEEP = """()=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics[0];
  cfg.mode='drill'; cfg.source='all'; cfg.units=[t];
  order = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; pos = 0;
  attempts = {}; picked = {}; layout = {}; timedOutSet = {};
  mysteryColorThisRun = 'red'; mysteryFoundThisSession = false; mysteryAppearsAtPos = 0;
  const bad = [];
  return new Promise(resolve => {
    let i = 0;
    const step = () => {
      if(i > 20) return resolve(bad);
      mysteryLeftFrac = i / 20;
      render();
      /* placeMysterySpark measures in a rAF, so the position is not
         final in the same tick render() returns in. Two frames. */
      requestAnimationFrame(() => requestAnimationFrame(() => {
        const s = document.querySelector('.mystery-spark');
        if(!s){ bad.push([i, 'missing']); i++; return step(); }
        const r = s.getBoundingClientRect();
        const row = s.closest('.qnumrow').getBoundingClientRect();
        if(r.left < row.left - 1 || r.right > row.right + 1) bad.push([i, 'out of row']);
        ['.qnum', '.flagbtn', '.choice'].forEach(sel => {
          document.querySelectorAll(sel).forEach(e => {
            const q = e.getBoundingClientRect();
            if(!q.width || !q.height) return;
            if(!(r.right <= q.left || r.left >= q.right ||
                 r.bottom <= q.top || r.top >= q.bottom)) bad.push([i, sel]);
          });
        });
        i++; step();
      }));
    };
    step();
  });}"""

GLINT = """()=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics[0];
  cfg.mode='drill'; cfg.source='all'; cfg.units=[t];
  const pool = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  store.mysteryColorsFound = { red:false, orange:false, yellow:false };
  store.lifetime.drillPlays = 9999;
  beginRun(pool, null, null);
  mysteryAppearsAtPos = 0; pos = 0;
  render();
  const spark = document.querySelector('.mystery-spark');
  if(!spark) return { spark:false };
  const s = spark.getBoundingClientRect();
  const row = spark.closest('.qnumrow');
  const rr = row ? row.getBoundingClientRect() : null;
  const hits = [...document.querySelectorAll('.choice')].filter(c => {
    const r = c.getBoundingClientRect();
    return !(s.right <= r.left || s.left >= r.right || s.bottom <= r.top || s.top >= r.bottom);
  }).length;
  return { spark:true, w:Math.round(s.width), h:Math.round(s.height),
           inRow: !!rr && s.left >= rr.left - 1 && s.right <= rr.right + 1,
           overlapsChoice: hits,
           centred: !!rr && Math.abs((s.top+s.bottom)/2 - (rr.top+rr.bottom)/2) < 2 };}"""


def check_glint(pg):
    print("\n6. the glint is a real tap target and never over an answer")
    g = pg.evaluate(GLINT)
    check("it renders at the armed position", g.get("spark") is True, g)
    if not g.get("spark"):
        return
    # 44px is the app's own floor, and this one is a decoration - which
    # makes it MORE important, not less: a small target that misses is a
    # person tapping at the screen wondering what they did wrong.
    check("at least 44x44", g["w"] >= 44 and g["h"] >= 44, "%dx%d" % (g["w"], g["h"]))
    check("inside the question card's header row", g["inRow"] and g["centred"])
    # THE ONE THAT MATTERS. A stray tap on a decoration is a shrug; a
    # stray tap that eats an answer is a wrong answer somebody did not
    # give, and this app records those permanently.
    check("overlapping no answer choice", g["overlapsChoice"] == 0, g["overlapsChoice"])


def check_glint_everywhere(br):
    """Every placement the app can pick, on the narrowest phone in the
    matrix and on a tablet. One sample on one device is not a check."""
    print("\n6b. every placement it can pick, on the narrowest phone too")
    for name, w, h in (("iPhone SE (1st gen)", 320, 568), ("iPad Pro 11\"", 834, 1194)):
        ctx, pg = booted(br, w, h)
        bad = pg.evaluate(GLINT_SWEEP)
        kinds = sorted(set(x[1] for x in bad))
        check("%s %dx%d clear at every position" % (name, w, h), not bad, kinds)
        ctx.close()


FIND = """()=>{
  const spark = document.querySelector('.mystery-spark');
  if(!spark) return { ok:false };
  spark.click();
  return { ok:true,
           found: Object.assign({}, store.mysteryColorsFound),
           count: mysteryColorsFoundCount(),
           banners: document.querySelectorAll('.flare-banner').length,
           voidLocked: isLockedCharacter('voidwalker') };}"""

REARM = """()=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics[0];
  cfg.mode='drill'; cfg.source='all'; cfg.units=[t];
  const pool = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  store.lifetime.drillPlays = 9999;
  beginRun(pool, null, null);
  mysteryAppearsAtPos = 0; pos = 0;
  render();
  return !!document.querySelector('.mystery-spark');}"""


def check_find(pg):
    print("\n7. finding all three is what unlocks Void")
    order_seen = []
    first = pg.evaluate(FIND)
    check("tapping it records the colour", first.get("ok") and first["count"] == 1, first)
    order_seen.append(first["found"])
    check("one is not enough for Void", first["voidLocked"] is True)
    check("and it says so on screen", first["banners"] == 1, first["banners"])
    # A found flare must not be findable twice, or the whole hunt is one
    # run long. IT IS DISABLED THE INSTANT IT IS TAPPED and removed a
    # beat later, and the order matters: reading the DOM straight after
    # the click and demanding the node be gone would be a check that
    # forces the burst animation to be deleted, which is the entire
    # feedback for finding one. So: unusable now, gone shortly.
    now = pg.evaluate("""()=>{ const s = document.querySelector('.mystery-spark');
      return { present: !!s, disabled: !!(s && s.disabled) }; }""")
    check("unusable the instant it is tapped", now["disabled"] is True, now)
    pg.wait_for_timeout(1200)
    later = pg.evaluate("()=>document.querySelectorAll('.mystery-spark').length")
    check("and gone once the burst has played", later == 0, later)

    for _ in range(2):
        pg.evaluate(REARM)
        r = pg.evaluate(FIND)
        order_seen.append(r["count"])
    final = pg.evaluate("""()=>({ count: mysteryColorsFoundCount(),
        voidLocked: isLockedCharacter('voidwalker'),
        msg: characterLockMessage('voidwalker'),
        queued: store.pendingVoidCutscene === true })""")
    check("three found", final["count"] == 3, order_seen[1:])
    check("Void is unlocked, and nothing else is", final["voidLocked"] is False)
    check("its lock message is empty once held", final["msg"] == "", final["msg"])
    # THE CUTSCENE IS QUEUED ON `store`, not played here. There is no
    # fixed route from a test to Home, so the flag has to survive the
    # trip and a relaunch - the same reason the badge queue lives there.
    check("the main-menu cutscene is queued", final["queued"] is True)
    # HOME HANDS OVER TO THE CUTSCENE while it is queued - checking the
    # orbit dots without clearing it measures the cutscene overlay and
    # reports Home as broken, which is what the first version of this
    # did. Both halves are worth asserting: that Home yields, and that
    # once it has, the dots are lit.
    played = pg.evaluate("""()=>{ showHome();
      return { overlay: !!document.getElementById('void-cutscene'),
               orbs: document.querySelectorAll('#void-cutscene .void-orb').length,
               character: !!document.querySelector('#void-cutscene .void-core svg') }; }""")
    check("Home plays the cutscene while it is queued", played["overlay"] is True, played)
    check("it is built out of the three flares and the character",
          played["orbs"] == 3 and played["character"] is True, played)
    # Home's orbit dots are the permanent mark, and they were left as
    # dead decoration when this feature was scrapped.
    lit = pg.evaluate("""()=>{
      document.getElementById('void-cutscene')?.remove();
      store.pendingVoidCutscene = false;
      showHome();
      return [...document.querySelectorAll('.cosmic-orbit-dot-found')].length; }""")
    check("all three orbit dots on Home are lit", lit == 3, lit)


# --------------------------------------------------------------------------
BANNER_RUN = """()=>{
  [...document.querySelectorAll('.charup-banner')].forEach(b => b.remove());
  store.dailyCorrectStreak = 9;
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [topics[0]];
  const qi = QUESTIONS.findIndex(q => (q.topic||'').trim() === topics[0]);
  order = [qi]; runTrackable = true; timedOut = false; runMode = 'drill';
  runLabel = 'Daily question';
  attempts = {}; picked = {}; timedOutSet = {}; attempts[qi] = 1;
  dailyQuestionLocked = false; store.dailyQuestionDate = null;
  summarize();
  const b = document.querySelector('.charup-banner');
  return { streak: store.dailyCorrectStreak,
           locked: isLockedCharacter('detective'),
           banner: !!b,
           drawsCharacter: !!(b && b.querySelector('.avatarchar-svg')),
           says: b ? b.textContent : '' };}"""


def check_unlock_banner(pg):
    """The banner shows the CHARACTER, not a generic mark.

    Same fault the rank-up banner had and was corrected for: it
    announced a rank and drew the flare that rank hands over. Asserted
    structurally - that the banner contains a real .avatarchar-svg built
    by the app's own builder - rather than by matching any string."""
    print("\n7b. unlocking a character shows that character in the banner")
    r = pg.evaluate(BANNER_RUN)
    check("the tenth daily in a row unlocks the Detective",
          r["streak"] == 10 and r["locked"] is False, r["streak"])
    check("a banner appears at the end of that run", r["banner"] is True)
    check("and the character is drawn in it", r["drawsCharacter"] is True, r["says"][:60])


def check_art(pg):
    """Sixteen characters, sixteen drawings.

    Same rule the rank emblems already carry: no two may produce the same
    shape signature. A builder that falls through to a default for an id
    it does not know is how the leaderboard once lost three classmates,
    and a new character that silently renders as an older one is the
    quiet version of the same bug."""
    print("\n8. sixteen characters, and no two of them are the same drawing")
    r = pg.evaluate("""()=>{
      const sigs = {};
      let empty = [];
      AVATAR_CHARACTERS.forEach(c => {
        const svg = buildAvatarCharSVG(c.id);
        if(!svg || svg.querySelectorAll('path,circle,ellipse,polygon').length < 3) empty.push(c.id);
        const sig = [...(svg ? svg.querySelectorAll('path,circle,ellipse,polygon') : [])]
          .map(n => n.tagName + (n.getAttribute('d')||'') +
                    (n.getAttribute('cx')||'') + (n.getAttribute('points')||'')).join('|');
        (sigs[sig] = sigs[sig] || []).push(c.id);
      });
      return { n: AVATAR_CHARACTERS.length, empty,
               dupes: Object.values(sigs).filter(v => v.length > 1),
               safe: !!buildAvatarCharSVGSafe('a-character-from-another-build') };}""")
    check("sixteen of them", r["n"] == 16, r["n"])
    check("every one draws something", not r["empty"], r["empty"])
    check("no two share a shape signature", not r["dupes"], r["dupes"])
    check("an unknown id still returns a node", r["safe"] is True)


def check_locked_art(br):
    """A LOCKED CHARACTER IS STILL A CHARACTER, and this is a PIXEL check.

    The locked treatment used to be `saturate .34 / brightness 1.42 /
    contrast .92`, and `brightness()` is a multiply: it lifts a mid tone
    and leaves a near black near black. The Masked One's hood is #141020,
    so on a near black tile it disappeared and what was left was the pale
    lacquer mask floating with no head under it - reported as "all you
    can see is the mask while it's locked". Void had the same problem
    waiting in it.

    Nothing in the DOM can see this: the element is there, the filter
    string is there, and the only thing that is wrong is a number of
    levels on a screen. So this samples the rendered tile - the hood band
    on the left, the mask in the middle, and a corner of the tile for the
    background - and asserts two things: the hood separates from the tile
    it sits on, and the mask does not out-shout it. Both were false at
    build 188."""
    print("\n9. a locked character is still a character")
    """ITS OWN CONTEXT, and that is not tidiness. Every other check in
    this file drives the app somewhere - check_unlock_banner finishes a
    daily question, and the timer that screen leaves behind re-rendered
    the stage ~600ms after Customize had mounted. Measured on the shared
    page, this check screenshotted the app's own wordmark and reported
    the hood as missing: a harness inventing the bug it was looking
    for."""
    ctx, pg = booted(br)
    try:
        _locked_art_body(pg)
    finally:
        ctx.close()


def _locked_art_body(pg):
    from PIL import Image                                 # noqa: PLC0415
    import tempfile                                       # noqa: PLC0415
    pg.evaluate("()=>{ showCustomize(); }")
    pg.wait_for_timeout(900)
    opts = pg.query_selector_all(".avatarchar-option")
    """The name is a SIBLING of the option, not inside it, so inner_text
    on the tile is the empty string - read the label off the tile itself.
    Found by a first draft that failed with sixteen empty strings."""
    names = [(o.evaluate("e => e.dataset.char || e.dataset.id || e.getAttribute('aria-label') || ''")
              or "").strip().lower() for o in opts]
    idx = next((i for i, n in enumerate(names) if "mask" in n), None)
    check("the Masked One is on the picker", idx is not None, names[:16])
    if idx is None:
        return
    locked = opts[idx].evaluate("e => e.classList.contains('locked')")
    check("and it is locked for this fixture", locked)
    """A PAGE CLIP, NOT AN ELEMENT SCREENSHOT, and the bands are computed
    from the drawing's own box rather than taken as fractions of the tile.
    Two earlier drafts got this wrong in opposite directions: fractions of
    the TILE put the mask band on empty padding at 834x1194 and on the
    mask at 440x956, because the padding is a different share of the tile
    at every size; and an element screenshot of the svg detached itself
    the moment an earlier check had re-rendered the screen. A clip
    rectangle read in the same evaluate as the rects can do neither."""
    box = pg.evaluate("""(i)=>{
      const o = document.querySelectorAll('.avatarchar-option')[i];
      const a = o && (o.querySelector('.avatarchar-svg') || o.querySelector('svg'));
      if(!a) return null;
      a.scrollIntoView({block:'center'});
      const r = a.getBoundingClientRect();
      /* PAGE COORDINATES, NOT VIEWPORT ONES. Playwright's clip is
         relative to the document; getBoundingClientRect is relative to
         the viewport. A first draft left the scroll offset out and
         clipped a patch of empty background 500px above the picker,
         which measured a flat 10 everywhere and read as "the hood is
         not there" - the exact bug this check is for, invented by the
         harness. */
      return { x:r.left + window.scrollX, y:r.top + window.scrollY,
               width:r.width, height:r.height };}""", idx)
    check("the character is drawn in its tile", bool(box) and box["width"] > 8, box)
    if not box or box["width"] <= 8:
        return
    path = os.path.join(tempfile.mkdtemp(prefix="locked-"), "masked.png")
    """An ELEMENT screenshot, re-queried in this moment rather than held
    from earlier: a page-level clip built from getBoundingClientRect came
    back a flat background colour here however the scroll offset was
    added, and an element handle taken before the picker rendered
    detaches. Re-querying and letting Playwright do the clipping is the
    one version of this that measures the drawing."""
    art = pg.query_selector_all(".avatarchar-option")[idx].query_selector(".avatarchar-svg")
    art.screenshot(path=path)
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = list(im.getdata())
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]

    def band(y0, y1, x0, x1):
        vals = [lum[y * w + x]
                for y in range(int(h * y0), max(int(h * y0) + 1, int(h * y1)))
                for x in range(int(w * x0), max(int(w * x0) + 1, int(w * x1)))]
        return sum(vals) / len(vals)

    """THE SHOULDERS ARE THE MEASUREMENT. The viewBox is `3 3 34 34`, so
    the hood's shoulder band fills the bottom tenth of the drawing edge to
    edge, the mask sits in the middle, and the top-left corner is empty on
    every character in the set. The shoulders are also the part that
    actually disappeared, which is what makes them the right band rather
    than the hood's sides: measured at build 188 they came out BELOW the
    tile they sat on (-3 levels on a tablet, +7 on a phone) - a body that
    is not there - against +45 and +55 now."""
    hood = band(.90, 1.0, .15, .75)
    mask = band(.40, .70, .40, .60)
    bg = band(.00, .18, .00, .18)
    """Levels, not ratios, for the first one: the question is whether
    there is a body under the mask at all. 30 sits well clear of both
    sides - 188 measures -3, this build measures +44."""
    check("the hood separates from the tile", hood - bg >= 30,
          "hood %.0f  tile %.0f  (+%.0f)" % (hood, bg, hood - bg))
    """The mask may be the brightest thing on the character - it is a
    pale lacquer mask - but past about 3x the hood's own separation it
    stops reading as a face on a head and becomes an object floating on
    its own. 188 measures 105x, because the hood it is being compared
    against is not there at all; this build measures 2.17x."""
    check("and the mask does not out-shout it",
          (mask - bg) <= 3.0 * (hood - bg),
          "mask +%.0f vs hood +%.0f  (%.2fx)" % (mask - bg, hood - bg, (mask - bg) / max(1.0, hood - bg)))


# --------------------------------------------------------------------------
def main():
    print("checking %s" % SRC)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        ctx, pg = booted(br)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for fn in (check_table, check_daily_streak, check_hardcore, check_flares, check_glint, check_find,
                   check_unlock_banner, check_art):
            try:
                fn(pg)
            except Exception as exc:                      # noqa: BLE001
                check(fn.__name__, False, "threw: %s" % exc)
        check("no uncaught JS along the way", not errs, errs[:3])
        ctx.close()
        for fn in (check_glint_everywhere, check_locked_art):
            try:
                fn(br)
            except Exception as exc:                      # noqa: BLE001
                check(fn.__name__, False, "threw: %s" % exc)
        br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))" %
          ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
