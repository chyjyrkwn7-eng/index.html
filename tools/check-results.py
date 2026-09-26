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
  5. Pause stays up on both screens, holds the reveal, and Resume puts
     back the SAME screen and lets it finish.
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
  window.__spots=0; window.__maxSpots=0; window.__actionsDuringSpot=false;
  setInterval(()=>{ const n=document.querySelectorAll('.rs-spot').length; __maxSpots=Math.max(__maxSpots,n);
    if(n){ __spots++; const a=document.querySelector('.rs-actions');
      if(a && getComputedStyle(a).opacity > .5) __actionsDuringSpot=true; } }, 60);
  window.__run=(unit, missN, mode)=>{
    __lands.length=0;
    cfg.mode=mode; cfg.source='all'; cfg.units=[unit]; cfg.size=0;
    order=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit);
    runTrackable=true; timedOut=false; runMode=mode; runLabel=null; isMissedRetake=false;
    practiceTestMinutes=null; inVirtualRoom=false; attempts={}; picked={}; timedOutSet={};
    order.forEach((qi,k)=>{ const oo=optionOrder(qi), right=oo.indexOf(QUESTIONS[qi].answer);
      attempts[qi]=k<missN?2:1; picked[qi]=k<missN?(right+1)%oo.length:right; });
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
    ck("Pause stays up on the results", first["pause"], first)
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
    ck("a missed run ends in Continue to review", cont == "Continue to review", cont)
    pg.evaluate("()=>document.querySelector('#stage .rs-continue') && document.querySelector('#stage .rs-continue').click()")
    pg.wait_for_timeout(400)
    rev = pg.evaluate("""()=>({
      title: (document.getElementById('testscopelabel')||{}).textContent,
      qs: document.querySelectorAll('#stage .rs-q').length,
      btns: [...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent),
      pause: !document.getElementById('pausebtn').hidden })""")
    ck("Continue opens the review, with exactly the missed questions",
       rev["qs"] == 3 and rev["title"] == "Test review", rev)
    ck("and Retake / Main menu under them",
       len(rev["btns"]) == 2 and "Retake" in rev["btns"][0] and rev["btns"][1] == "Main menu", rev)
    ck("Pause is up on the review too", rev["pause"], rev)

    print("2. a perfect run that earns a badge: banners one at a time")
    pg.evaluate("""([u])=>{ store.unitPerfects={}; store.unitPerfects[u]=badgeThresholdFor(u)-1;
      store.pendingBadgeUnlocks=[]; __maxSpots=0; __spots=0; __actionsDuringSpot=false; saveStore(); }""", [UNIT])
    pg.evaluate("([u])=>__run(u,0,'drill')", [UNIT])
    done = wait_done(pg, 60000)
    st = pg.evaluate("()=>({max:__maxSpots, seen:__spots, during:__actionsDuringSpot,"
                     " cont: !!document.querySelector('#stage .rs-continue'),"
                     " btns:[...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent),"
                     " unlocked: document.querySelectorAll('#stage .rs-unlocked .rs-unlock').length})")
    lines2 = [l["t"] for l in pg.evaluate("()=>__lands.slice()") if l["kind"] == "line"]
    ck("the XP lines drop in one at a time (correct answers, hundo, badge)",
       len(lines2) >= 3 and all(b - a > 150 for a, b in zip(lines2, lines2[1:])), lines2)
    ck("the badge came through as a banner", st["seen"] > 0, st)
    ck("never two banners at once", st["max"] == 1, st)
    ck("the buttons waited for the last banner", not st["during"], st)
    ck("a perfect run has nothing to review, so no Continue", done and not st["cont"] and len(st["btns"]) >= 1, st)
    ck("what it unlocked is left on the page", st["unlocked"] >= 1, st)

    print("3. Pause holds the reveal and Resume gives the same screen back")
    pg.evaluate("([u])=>__run(u,3,'drill')", [UNIT]); pg.wait_for_timeout(700)
    pg.evaluate("()=>{ window.__node=document.getElementById('stage').firstElementChild; document.getElementById('pausebtn').click(); }")
    pg.wait_for_timeout(300)
    paused = pg.evaluate("()=>({pausePanel: !!document.querySelector('#stage .pausepanel'),"
                         " landed: window.__node ? window.__node.querySelectorAll('.rs-in, .rs-in-now').length : -1})")
    pg.wait_for_timeout(2500)
    held = pg.evaluate("()=>window.__node ? window.__node.querySelectorAll('.rs-in, .rs-in-now').length : -1")
    ck("Pause shows the pause screen over the results", paused["pausePanel"], paused)
    ck("and nothing lands while it is up", held == paused["landed"] and held > 0, (paused, held))
    pg.evaluate("()=>{ const b=document.getElementById('resumebtn'); b && b.click(); }")
    pg.wait_for_timeout(200)
    same = pg.evaluate("()=>document.getElementById('stage').firstElementChild === window.__node")
    ck("Resume puts back the very same screen", same)
    ck("and the reveal carries on to the end", wait_done(pg))

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

    ck("no page errors", not errors, errors[:3])
    br.close()
srv.shutdown()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
