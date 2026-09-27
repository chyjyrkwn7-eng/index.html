"""The end of a run is two screens (build 212).

  python3 tools/check-results.py                 # this build
  python3 tools/check-results.py --against OLD   # must FAIL on build 211

"Split the test result screens up": a rewards screen first (XP, level,
badges, the grade, unlock banners one after another) and, only when
something was missed, a review screen behind a "Continue to review"
button. What is held here is the SHAPE of that, not its words:

  1. The rewards screen carries no review - no missed questions, no
     Retake - and says "Test results" where the progress bar was.
  2. It arrives in order: the XP lines one at a time, the total after
     them, the grade after every other card. Measured off the moment
     each card lands, not off the source.
  3. The button is not there until everything has landed, and on a
     missed run it goes to a review screen that has the missed
     questions and the Retake / Main menu pair.
  4. Unlock banners come one at a time, and the buttons wait for the
     last of them.
  5. (build 213) No Pause on either results screen; the review shows the
     answer you gave; the XP lines come from computeRunXp() and follow its
     rules (speed in steps of 5, streak tiers with xN, multi-unit last,
     retake = right answers only, Game bonuses only for a game beaten);
     a lost game still gets a results screen; Re-run is back.
  6. Reduce motion gets everything at once and no banners.

Drives summarize() directly with a real unit's questions, the way
check-behaviour's badge routes do, so it is fast and deterministic.
"""
import functools, http.server, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None

s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

ok = True
def ck(name, cond, detail=""):
    global ok
    print(" ", "PASS" if cond else "FAIL", name, ("-> " + str(detail)) if detail else "")
    if not cond: ok = False

SETUP = """()=>{
  document.getElementById('splashscreen')?.remove(); try{ __useFake(); }catch(e){}
  store.onboardingComplete=true; store.firstName='Madison'; store.tourRev=99;
  store.retroBadgePending=[]; store.badgeBandsVersion=2;
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
   'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
  theme.muteBanners=false; theme.reduceMotion=false; saveStore(); showHome();
  /* Every card's landing, timed. */
  window.__lands=[]; const t0=performance.now();
  new MutationObserver(ms=>ms.forEach(m=>{ const el=m.target;
    if(!(el.classList && (el.classList.contains('rs-in')||el.classList.contains('rs-in-now')))) return;
    if(el.__landed) return; el.__landed=performance.now()-t0;
    const kind = el.classList.contains('rs-xpline')?'line' : el.classList.contains('rs-xptotal')?'total'
      : el.classList.contains('rs-grade')?'grade' : el.classList.contains('rs-actions')?'actions'
      : el.classList.contains('rs-unlocked')?'unlocked' : el.classList.contains('rs-head')?'head'
      : el.classList.contains('rs-xp')?'xp' : el.classList.contains('results-level')?'level' : 'box';
    __lands.push({kind, t:el.__landed}); })).observe(document.body,{subtree:true,attributes:true,attributeFilter:['class']});
  window.__spots=0; window.__maxSpots=0; window.__actionsDuringSpot=false; window.__caseSeen=false;
  setInterval(()=>{ if(document.querySelector('.bc-scene')) __caseSeen=true; }, 80);
  setInterval(()=>{ const n=document.querySelectorAll('.rs-spot').length; __maxSpots=Math.max(__maxSpots,n);
    if(n){ __spots++; const a=document.querySelector('.rs-actions');
      if(a && getComputedStyle(a).opacity > .5) __actionsDuringSpot=true; } }, 60);
  window.__run=(unit, missN, mode, retake)=>{
    __lands.length=0;
    cfg.mode=mode; cfg.source='all'; cfg.units=[unit]; cfg.size=0;
    order=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit);
    if(retake) order=order.slice(0,3);
    runTrackable=!retake; timedOut=false; runMode=mode; runLabel=retake?'Missed questions':null; isMissedRetake=!!retake;
    practiceTestMinutes=null; inVirtualRoom=false; attempts={}; picked={}; timedOutSet={};
    try{ firstPick = {}; }catch(e){}
    order.forEach((qi,k)=>{ const oo=optionOrder(qi), right=oo.indexOf(QUESTIONS[qi].answer);
      attempts[qi]=k<missN?2:1; picked[qi]=k<missN?(right+1)%oo.length:right;
      try{ if(k<missN) firstPick[qi]=(right+1)%oo.length; }catch(e){} });
    runStartTime=Date.now()-42000; testInProgress=true; pos=order.length-1;
    summarize();
  };
}"""
VISIBLE = """(sel)=>{ const e=document.querySelector(sel); if(!e) return false;
  const cs=getComputedStyle(e); return cs.display!=='none' && cs.visibility!=='hidden' && +cs.opacity>.5 && e.getClientRects().length>0; }"""
DONE = "()=>!!document.querySelector('.rs-rewards.rs-done')"

def wait_done(pg, ms=40000):
    for _ in range(ms // 250):
        try:
            if pg.evaluate(DONE): return True
        except Exception: pass
        pg.wait_for_timeout(250)
    return False

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script(FAKE)
    ctx.add_init_script("try{localStorage.setItem('class26e.frame.ok','go-live-1');"
                        "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.daily.seen','x');}catch(e){}")
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    _html = open(AGAINST or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if AGAINST:
        pg.route("**/index.html", lambda r, q=None: r.fulfill(status=200, content_type="text/html", body=_html))
    # version.json always names the build being served, or an older
    # build under --against sees an update waiting and reloads mid-check.
    _bld = re.search(r'const APP_BUILD = "([^"]+)"', _html).group(1)
    pg.route("**/version.json*", lambda r, q=None: r.fulfill(status=200, content_type="application/json",
             body='{"build":"%s","frameId":""}' % _bld))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2500)
    pg.evaluate(SETUP); pg.wait_for_timeout(300)
    UNIT = "Identity Crimes"

    print("1. a run with three missed: the rewards screen")
    pg.evaluate("([u])=>__run(u,3,'drill')", [UNIT]); pg.wait_for_timeout(250)
    first = pg.evaluate("""()=>({
      title: (document.getElementById('testscopelabel')||{}).textContent,
      meterHidden: document.getElementById('meter').hidden,
      pause: !document.getElementById('pausebtn').hidden,
      review: document.querySelectorAll('#stage .review li, #stage .rs-q').length,
      retake: [...document.querySelectorAll('#stage button')].some(b=>/Retake/.test(b.textContent)),
      screen: (document.getElementById('stage').firstElementChild||{dataset:{}}).dataset.screen })""")
    ck("the header says Test results where the progress bar was",
       first["title"] == "Test results" and first["meterHidden"], first)
    ck("no missed questions on the rewards screen", first["review"] == 0, first)
    ck("and no Retake on it either", not first["retake"], first)
    ck("no Pause on the results - the chat button has the corner", not first["pause"], first)
    ck("the button is not there while the reveal is still playing",
       not pg.evaluate(VISIBLE, "#stage .rs-actions, #stage .actions"))
    done = wait_done(pg)
    ck("the reveal finishes", done)
    lands = pg.evaluate("()=>__lands.slice()")
    kinds = [l["kind"] for l in lands]
    t = lambda k: [l["t"] for l in lands if l["kind"] == k]
    lines = t("line")
    ck("the total lands after the lines, with a beat between",
       bool(t("total")) and bool(lines) and t("total")[0] - lines[-1] > 400, (lines, t("total")))
    others = [l["t"] for l in lands if l["kind"] in ("head", "xp", "line", "total", "level", "box")]
    ck("the grade lands after everything above it",
       bool(t("grade")) and bool(others) and t("grade")[0] >= max(others), kinds)
    ck("and the button after the grade",
       bool(t("actions")) and bool(t("grade")) and t("actions")[0] > t("grade")[0], kinds)
    cont = pg.evaluate("()=>{const b=document.querySelector('#stage .rs-continue'); return b? b.textContent: null}")
    ck("a missed run ends in Continue to review, with the count", cont == "Continue to review (3 missed)", cont)
    # BUILD 214: Re-run and Main menu are on the RESULTS, not the review -
    # "At the end of the test, on the result screen, that's where the re
    # run and main button need to be".
    res_btns = pg.evaluate("()=>[...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent)")
    ck("and Re-run and Main menu beside it, on the results",
       res_btns == ["Continue to review (3 missed)", "Re-run", "Main menu"], res_btns)
    pg.evaluate("()=>document.querySelector('#stage .rs-continue') && document.querySelector('#stage .rs-continue').click()")
    pg.wait_for_timeout(400)
    rev = pg.evaluate("""()=>({
      title: (document.getElementById('testscopelabel')||{}).textContent,
      qs: document.querySelectorAll('#stage .rs-q').length,
      yours: document.querySelectorAll('#stage .rs-q .rs-q-yours').length,
      pctInHead: /%/.test((document.querySelector('#stage .rs-review-summary')||{}).textContent||''),
      btns: [...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent),
      pause: !document.getElementById('pausebtn').hidden })""")
    ck("Continue opens the review, with exactly the missed questions",
       rev["qs"] == 3 and rev["title"] == "Test review", rev)
    ck("each one shows the answer you gave, Drill included", rev["yours"] == 3, rev)
    ck("and the count at the top carries no stray percentage", not rev["pctInHead"], rev)
    ck("the review offers the retake and the way back, and nothing else",
       rev["btns"] == ["Retake missed questions (3)", "Back to results"], rev)
    ck("so no Re-run and no Main menu while reviewing",
       not any(b in ("Re-run", "Main menu") for b in rev["btns"]), rev)
    pg.evaluate("()=>[...document.querySelectorAll('#stage .actions button')].find(b=>/Back to results/.test(b.textContent)).click()")
    pg.wait_for_timeout(300)
    back = pg.evaluate("()=>({ done: !!document.querySelector('.rs-rewards.rs-done'),"
      " spots: document.querySelectorAll('.rs-spot, .bc-scene, .fl-scene').length,"
      " btns: [...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent) })")
    ck("Back to results is the finished screen at once, nothing replayed",
       back["done"] and back["spots"] == 0 and back["btns"] == res_btns, back)
    ck("no Pause on the review either", not rev["pause"], rev)

    print("2. a perfect run that earns a badge: banners one at a time")
    pg.evaluate("""([u])=>{ store.unitPerfects={}; store.unitPerfects[u]=badgeThresholdFor(u)-1;
      store.pendingBadgeUnlocks=[]; __maxSpots=0; __spots=0; __actionsDuringSpot=false; saveStore(); }""", [UNIT])
    pg.evaluate("([u])=>__run(u,0,'drill')", [UNIT])
    done = wait_done(pg, 60000)
    st = pg.evaluate("()=>({max:__maxSpots, seen:__spots, during:__actionsDuringSpot, caseSeen:!!window.__caseSeen,"
                     " cont: !!document.querySelector('#stage .rs-continue'),"
                     " btns:[...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent),"
                     " unlocked: document.querySelectorAll('#stage .rs-unlocked .rs-unlock').length})")
    lines2 = [l["t"] for l in pg.evaluate("()=>__lands.slice()") if l["kind"] == "line"]
    ck("the XP lines drop in one at a time (correct answers, hundo, badge)",
       len(lines2) >= 3 and all(b - a > 150 for a, b in zip(lines2, lines2[1:])), lines2)
    # BUILD 215: a badge's moment is its case, at the unlock - "move that
    # cutscene to when it hits the unlock thing" - and no banner besides.
    ck("the badge came through as its case, not a banner", st["caseSeen"] and st["seen"] == 0, st)
    ck("never two banners at once", st["max"] <= 1, st)
    ck("and no progress box for the badge it earned",
       pg.evaluate("()=>document.querySelectorAll('#stage .rs-badges').length") == 0)
    ck("the buttons waited for the last banner", not st["during"], st)
    ck("a perfect run has nothing to review, so no Continue", done and not st["cont"] and len(st["btns"]) >= 1, st)
    ck("what it unlocked is left on the page", st["unlocked"] >= 1, st)
    ck("the badge case cutscene played on the results", st["caseSeen"], st)
    ck("and Re-run is back beside Main menu", "Re-run" in st["btns"] and "Main menu" in st["btns"], st)

    print("3. the XP rules, asked of computeRunXp() directly")
    xr = pg.evaluate("""()=>{ if(typeof computeRunXp !== 'function') return null;
      const L = r => computeRunXp(r).lines.map(l => [l.key, l.label, l.value]);
      const ok = n => Array(n).fill(true);
      return {
        fast: L({good:12, answered:12, elapsedMs:12*3000, okList:ok(12), hundos:1, wholeUnits:1}),
        slow: L({good:12, answered:12, elapsedMs:12*150000, okList:ok(12), hundos:0, wholeUnits:1}),
        streaks: L({good:37, answered:38, elapsedMs:38*20000, okList:ok(12).concat([false], ok(25)), hundos:0, wholeUnits:1}),
        multi: computeRunXp({good:40, answered:40, elapsedMs:40*20000, okList:ok(40), hundos:4, wholeUnits:4}).lines.slice(-1)[0],
        retake: L({retake:true, good:3, answered:3, elapsedMs:5000, okList:ok(3)}),
        gameWon: L({good:12, answered:12, elapsedMs:60000, okList:ok(12), hundos:1, wholeUnits:1, game:{speed:'average', beaten:true, livesLeft:2}}),
        gameLost: L({good:2, answered:3, elapsedMs:30000, okList:[true,true,false], hundos:0, wholeUnits:0, game:{speed:'average', beaten:false, livesLeft:0}}),
        badge: MASTERY_BONUS
      }; }""")
    if not xr:
        ck("computeRunXp exists", False)
    else:
        g = lambda rows, key: [r for r in rows if r[0] == key]
        ck("speed under 5s a question is 150", g(xr["fast"], "speed") and g(xr["fast"], "speed")[0][2] == 150, xr["fast"])
        ck("speed past two minutes a question is 10", g(xr["slow"], "speed") and g(xr["slow"], "speed")[0][2] == 10, xr["slow"])
        ck("every speed bonus is a multiple of 5", all(r[2] % 5 == 0 for rows in (xr["fast"], xr["slow"]) for r in g(rows, "speed")))
        st10 = g(xr["streaks"], "streak10"); st25 = g(xr["streaks"], "streak25")
        ck("two runs past 10 count as 10 in a row x2, and 25 once", st10 and "\u00d72" in st10[0][1] and st25 and "\u00d7" not in st25[0][1], xr["streaks"])
        ck("a multi-unit run ends on its multiplier, x1.3 for four units",
           xr["multi"]["key"] == "multi" and "1.3" in xr["multi"]["label"], xr["multi"])
        ck("a retake earns its right answers and nothing else", [r[0] for r in xr["retake"]] == ["correct"] and xr["retake"][0][2] == 30, xr["retake"])
        ck("a Game won pays its difficulty and its lives", g(xr["gameWon"], "gamebeat") and g(xr["gameWon"], "gamelives"), xr["gameWon"])
        ck("a Game lost pays neither", not g(xr["gameLost"], "gamebeat") and not g(xr["gameLost"], "gamelives"), xr["gameLost"])
        ck("a badge is worth 1,000", xr["badge"] == 1000, xr["badge"])
    print("   a lost game still gets a results screen")
    lost = pg.evaluate("""([u])=>{ if(typeof gameOver !== 'function') return null;
      cfg.mode='game'; cfg.gameSpeed='easy'; cfg.source='all'; cfg.units=[u];
      order=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u);
      runTrackable=true; timedOut=false; runMode='game'; runLabel=null; isMissedRetake=false; practiceTestMinutes=null; inVirtualRoom=false;
      attempts={}; picked={}; timedOutSet={}; try{ gameLostAt=0; }catch(e){}
      order.slice(0,3).forEach((qi,k)=>{ attempts[qi]= k<2 ? 2 : 1; });
      pos=2; livesLeft=0; runStartTime=Date.now()-30000; testInProgress=true;
      gameOver();
      return { title:(document.getElementById('testscopelabel')||{}).textContent,
               over: !!document.querySelector('#stage .rs-grade.is-over'),
               xp: !!document.querySelector('#stage .rs-xp') }; }""", [UNIT])
    ck("out of lives lands on a results screen with XP and a Game over card",
       bool(lost) and lost["over"] and lost["xp"] and lost["title"] == "Game over", lost)
    wait_done(pg)

    print("4. reduce motion: everything at once, no banners")
    pg.evaluate("""([u])=>{ theme.reduceMotion=true; applyTheme && applyTheme();
      store.unitPerfects={}; store.unitPerfects[u]=badgeThresholdFor(u)-1; __maxSpots=0; saveStore(); }""", [UNIT])
    pg.evaluate("([u])=>__run(u,0,'drill')", [UNIT]); pg.wait_for_timeout(200)
    rm = pg.evaluate("""()=>({ done: !!document.querySelector('.rs-rewards.rs-done'),
      hidden: [...document.querySelectorAll('#stage .rs-land')].filter(e=>+getComputedStyle(e).opacity<.5).length,
      spots: document.querySelectorAll('.rs-spot').length })""")
    ck("every card is already down", rm["done"] and rm["hidden"] == 0, rm)
    pg.wait_for_timeout(1500)
    ck("and no banner plays", pg.evaluate("()=>__maxSpots") == 0)
    pg.evaluate("()=>{ theme.reduceMotion=false; applyTheme && applyTheme(); }")

    print("5. build 214: the header, the labels, a retake, the room's score")
    pg.evaluate("([u])=>__run(u,2,'drill')", [UNIT]); wait_done(pg)
    hd = pg.evaluate("()=>({ title:(document.querySelector('#stage .rs-units')||{}).textContent,"
                     " items:[...document.querySelectorAll('#stage .rs-unitlist li')].map(l=>l.textContent) })")
    ck("a one-unit test says 1 unit and lists it", hd["title"] == "1 unit" and hd["items"] == [UNIT], hd)
    lab = pg.evaluate("()=>computeRunXp({good:12, answered:12, elapsedMs:60000, okList:Array(12).fill(true), hundos:0, wholeUnits:1})"
                      ".lines.filter(l=>/^streak/.test(l.key)).map(l=>l.label)")
    ck("a streak line says what kind of bonus it is", lab == ["Streak bonus \u00b7 10"], lab)
    pg.evaluate("([u])=>__run(u,1,'drill',true)", [UNIT]); wait_done(pg)
    rt = pg.evaluate("()=>({ pct: !!document.querySelector('#stage .rs-pct'),"
      " note: (document.querySelector('#stage .rs-retake-line')||{}).textContent,"
      " xp: [...document.querySelectorAll('#stage .rs-xpline-name')].map(e=>e.textContent) })")
    ck("a retake shows no score", not rt["pct"] and bool(rt["note"]), rt)
    ck("and earns its right answers only", len(rt["xp"]) == 1 and "correct" in rt["xp"][0], rt)
    pg.evaluate("([u])=>{ store.unitBestPct = store.unitBestPct || {}; store.unitBestPct[u] = 50; saveStore(); }", [UNIT])
    pg.evaluate("([u])=>__run(u,0,'drill')", [UNIT]); wait_done(pg, 60000)
    rm2 = pg.evaluate("()=>({ mine: (lastRunResult.xpLines||[]).map(l=>l.key),"
                      " room: ((lastRunRoomXp||{}).lines||[]).map(l=>l.key) })")
    ck("a new best score is in YOUR XP", "pbscore" in rm2["mine"], rm2)
    ck("and not in the Virtual Room's score, nor a badge",
       "pbscore" not in rm2["room"] and "pbtime" not in rm2["room"] and "badge" not in rm2["room"], rm2)

    print("6. build 215: the Constitution unit")
    cu = pg.evaluate("""()=>{ const U = 'US and Texas Constitution and Rights';
      const idx = QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===U);
      const bySrc = n => idx.find(i=>QUESTIONS[i].src===n);
      const q61 = bySrc(61), q11 = bySrc(11), q37 = bySrc(37);
      const links = idx.filter(i=>/https?:/.test((QUESTIONS[i].ref||'') + QUESTIONS[i].q + QUESTIONS[i].choices.join(' '))).length;
      const orders = [];
      for(let k = 0; k < 8; k++){ layout = {}; runMode = 'exam'; cfg.shuffle = true;
        orders.push(optionOrder(q11).join('') + '/' + optionOrder(q37).join('')); }
      /* Drill: the note once answered. */
      cfg.mode='drill'; cfg.units=[U]; cfg.source='all'; cfg.shuffle=true; runMode='drill';
      beginRun([q61], null);
      return { q61, links, orders }; }""")
    ck("no links left in the unit", cu["links"] == 0, cu["links"])
    ck("Q11 and Q37 keep their order, even shuffled in an Exam", set(cu["orders"]) == {"0123/0123"}, cu["orders"])
    pg.wait_for_selector(".qpanel .choice", timeout=20000)
    pre = pg.evaluate("()=>!!document.querySelector('.bank-note')")
    pg.evaluate("()=>{const r=correctSlot(order[pos]); [...document.querySelectorAll('.qpanel .choice')].find(c=>+c.dataset.index===r).click();}")
    pg.wait_for_timeout(400)
    note = pg.evaluate("()=>(document.querySelector('.qpanel .bank-note')||{}).textContent || ''")
    ck("Q61's red note is not there before answering", pre is False)
    ck("and says the real answer once answered in Drill",
       "excessive bail" in note and "study bank" in note, note[:120])
    rv = pg.evaluate("""([q])=>{ const run = { mode:'exam', vroom:false, gameLost:0, order:[q], missed:[q], attempts:{}, firstPick:{},
        picked: { [q]: 1 }, timedOutSet:{} };
      layout = {}; runMode='exam'; cfg.shuffle=false;
      const li = buildReviewQuestion(run, q, 0);
      return (li.querySelector('.bank-note')||{}).textContent || ''; }""", [cu["q61"]])
    ck("and in an Exam it is in the review at the end", "excessive bail" in rv, rv[:80])
    pg.evaluate("()=>{ testInProgress=false; try{ showHome(); }catch(e){} }")

    print("7. build 216: found recording every cutscene")
    # Both written against build 215, where both fail.
    # The difficulty lights' labels hang centred under each light, so the
    # gap between lights is all the room two labels get: at .9rem
    # "AVERAGE" and "HARDCORE" overlapped by 10px on the Hardcore unlock.
    gaps = pg.evaluate("""()=>{ const spot=document.createElement('div'); spot.className='rs-spot';
      const art=document.createElement('div'); art.className='rs-spot-art';
      art.appendChild(buildDifficultyLights('hardcore')); spot.appendChild(art); document.body.appendChild(spot);
      const ls=[...art.querySelectorAll('.rs-difflight-label')].map(l=>l.getBoundingClientRect());
      const g = ls.slice(1).map((r,i)=>Math.round(r.left-ls[i].right)); spot.remove(); return g; }""")
    ck("the difficulty labels do not run into each other", len(gaps) == 2 and min(gaps) >= 6, gaps)
    # A streak pill from the last question lives on <body> and rode on
    # over "Test results" when the run ended on a streak.
    pg.evaluate("()=>{ theme.muteBanners=false; showRunStreakBanner(25); }")
    pill_before = pg.evaluate("()=>!!document.querySelector('.streak-pop')")
    # Read at once: the pill times itself out after 1.9s, so a check that
    # waited for the results to finish landing could not fail.
    pill_after = pg.evaluate("([u])=>{ __run(u,0,'drill'); return !!document.querySelector('.streak-pop'); }", [UNIT])
    wait_done(pg)
    ck("a streak pill does not ride over the results", pill_before and not pill_after,
       {"before": pill_before, "after": pill_after})
    pg.evaluate("()=>{ testInProgress=false; try{ showHome(); }catch(e){} }")

    ck("no page errors", not errors, errors[:3])
    br.close()
srv.shutdown()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
