"""The study flow, end to end - the pre-launch audit's gate (build 245).

  python3 tools/check-studyflow.py                 # this build
  python3 tools/check-studyflow.py --against OLD   # must FAIL on the build before

Every check here was written against a build where it failed:

  1. A unit's details card can always be closed. Each open left an observer
     on #stage that, on the next screen change, cleared the GLOBAL "a card
     is open" flag - the one the NEXT card had set - so the new card and its
     scrim stayed on screen for good, and a tap on the scrim did nothing.
     (Open a unit's details twice, leave the screen with the second up.)
  2. The daily question books the XP its card prints (DAILY_XP). It said
     "+200 XP" and booked 100.
  3. A rank reached on the daily question is told on Home, in order: no
     "Character unlocked" / "Theme unlocked" pills stacked over the
     question; the rank character is left for Home's queue.
  4. Review mode's sheet counts the bank it will list (Most missed, not the
     whole unit).
  5. The Supernova results say "Main menu" like every other run.
  6. The grade's "12 of 12 / right on the first try" is never squeezed into
     a one-word column beside a 100% on a small phone.
  7. The last row to land on the results is not under the back-to-top
     button in the corner.
  8. The unit-select tour does not promise a flat 35 hundos a badge.
  9. Something a run tips over WHILE it is being answered - the 5,000th
     right answer, 100 in a row, the 20th hour - is announced on that
     run's results. summarize() took its before-snapshots after those
     counters had already moved, so they fell through to Home's queue.
 10. A run that ends on its time limit pays XP for what was answered ("scores
     whatever you finished"), and still no hundo and no history entry.
 11. A challenge character's pop-up says "Challenge complete" once (the
     strip) and says what was unlocked under it, not the strip again.
 12. A wrong daily question marks the answer you picked, as well as the
     right one.
 13. The start sheet's close button is a 44px target and still draws the
     same 2.1rem circle; the "How Most missed works" dot reaches 44px too
     (it already did - held here so it cannot regress).
"""
import functools, http.server, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
HTML = open(AGAINST or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', HTML).group(1)

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

SEED = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,"tourRev":99,'
        '"rankMapFx244":true,"rankMapSeen":99,"badgeBandsVersion":2,"retroBadgePending":[],'
        '"seenFirstResultsTour":true,"seenModeSelectTour":true,"seenUnitSelectTour":true,'
        '"seenMainMenuTour":true,"seenProfileTour":true,"seenSettingsTour":true,'
        '"lifetime":{"points":6400,"answered":800,"correct":700}}')
errors = []

def page(br, w=440, h=956):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True)
    ctx.add_init_script(FAKE)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
                        "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.daily.seen','x');"
                        "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}" % repr(SEED))
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.route("**/index.html", lambda r, q=None: r.fulfill(status=200, content_type="text/html", body=HTML))
    pg.route("**/version.json*", lambda r, q=None: r.fulfill(status=200, content_type="application/json",
             body='{"build":"%s","frameId":""}' % BUILD))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2300)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ __useFake(); }catch(e){} "
                "ensureUnlocksShown(); store.unlocksShown.chars=announceableHeldCharacters(); "
                "store.unlocksShown.banners=BANNERS.filter(b=>bannerEarned(b.id)).map(b=>b.id); saveStore(); showHome(); }")
    pg.wait_for_timeout(400)
    return ctx, pg

# Answers the question on screen right (or wrong) through the real buttons.
ANSWER = """(bad)=>{ const rv=document.querySelector('.recall-reveal button'); if(rv) rv.click();
  const r=correctSlot(order[pos]); const cs=[...document.querySelectorAll('.qpanel .choice')];
  const t = bad ? cs.find(c=>+c.dataset.index!==r) : cs.find(c=>+c.dataset.index===r); if(t) t.click(); return !!t; }"""
RUN_UNIT = """async ([unit, perfect])=>{ const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  cfg.mode='drill'; cfg.source='all'; cfg.units=[unit]; cfg.size=0; cfg.recall=false;
  beginRun(QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit));
  for(let k=0;k<400;k++){
    for(let t=0;t<80 && !document.querySelector('.qpanel .choice') && !document.querySelector('.rs-screen');t++) await sleep(100);
    if(document.querySelector('.rs-screen')) return true;
    const p=pos, r=correctSlot(order[pos]); const cs=[...document.querySelectorAll('.qpanel .choice')];
    if(!perfect && p===1){ cs.find(c=>+c.dataset.index!==r).click(); await sleep(150); }
    [...document.querySelectorAll('.qpanel .choice')].find(c=>+c.dataset.index===r).click(); await sleep(150);
    const b=document.getElementById('nextbtn'); if(b && !b.hidden) b.click();
    for(let t=0;t<50 && pos===p && !document.querySelector('.rs-screen');t++) await sleep(60);
  } return false; }"""

def wait_for(pg, js, ms):
    for _ in range(ms // 250):
        try:
            if pg.evaluate(js): return True
        except Exception: pass
        pg.wait_for_timeout(250)
    return False

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    print("1. a unit's details card can always be closed")
    ctx, pg = page(br)
    pg.evaluate("()=>{ cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(600)
    OPEN = "(u)=>{ const r=[...document.querySelectorAll('.pick')].find(p=>p.textContent.includes(u)); r.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true})); }"
    pg.evaluate(OPEN, "Identity Crimes"); pg.wait_for_timeout(600)
    pg.evaluate("()=>document.querySelector('.unitdetail-scrim').click()"); pg.wait_for_timeout(700)
    first = pg.evaluate("()=>document.querySelectorAll('.unitdetail, .unitdetail-scrim').length")
    ck("the first card closes on a tap outside it", first == 0, first)
    pg.evaluate(OPEN, "Victims of Crime"); pg.wait_for_timeout(600)
    ck("a second card opens", pg.evaluate("()=>!!document.querySelector('.unitdetail.is-open')"))
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900)
    left = pg.evaluate("()=>({cards:document.querySelectorAll('.unitdetail').length, scrims:document.querySelectorAll('.unitdetail-scrim').length})")
    ck("leaving the screen takes the second card and its scrim with it", left["cards"] == 0 and left["scrims"] == 0, left)
    pg.evaluate("()=>{ cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(600)
    pg.evaluate(OPEN, "Identity Crimes"); pg.wait_for_timeout(600)
    ck("and a card still opens after that", pg.evaluate("()=>!!document.querySelector('.unitdetail.is-open')"))
    ctx.close()

    print("2. the daily question books what it prints")
    ctx, pg = page(br)
    before = pg.evaluate("()=>{ store.dailyQuestionDate=null; saveStore(); startDailyQuestion(); return store.lifetime.points; }")
    pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(300)
    pg.evaluate(ANSWER, False); pg.wait_for_timeout(1200)
    got = pg.evaluate("(b)=>({booked:store.lifetime.points-b, printed:(document.querySelector('.dailyq-outro-xp')||{}).textContent, daily:DAILY_XP})", before)
    ck("the XP booked is the XP on the card", "+%d XP" % got["booked"] == got["printed"], got)
    ck("and it is DAILY_XP", got["booked"] == got["daily"], got)
    ctx.close()

    print("3. a rank reached on the daily question is told on Home, in order")
    ctx, pg = page(br)
    pg.evaluate("""()=>{ const units=topicsIn(QUESTIONS).slice(0,3); store.unitPerfects={}; units.forEach(u=>store.unitPerfects[u]=badgeThresholdFor(u));
      let p=0; while(levelProgress(p).level<TIER_UNLOCKS.ranger.level) p+=10; store.lifetime.points=p-50; store.points=store.lifetime.points;
      store.dailyQuestionDate=null; saveStore(); startDailyQuestion(); }""")
    pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ window.__maxPills=0; window.__pillIv=setInterval(()=>{ __maxPills=Math.max(__maxPills, document.querySelectorAll('.tierup-banner').length); }, 50); }")
    pg.evaluate(ANSWER, False); pg.wait_for_timeout(2600)
    st = pg.evaluate("()=>({rank:rankOf(store), pills:__maxPills, lunarShown:unlockWasShown('chars','lunar'), pending:store.pendingTierCutscene})")
    ck("the answer reached Silver", st["rank"] == "ranger", st)
    ck("no unlock pills over the daily question for what the rank hands over", st["pills"] == 0, st)
    ck("the rank's character is left for Home, not marked shown", not st["lunarShown"], st)
    pg.evaluate("()=>document.getElementById('dailyq-exitbtn').click()")
    saw_cut = wait_for(pg, "()=>!!document.getElementById('supernova-cutscene')", 6000)
    ck("Exit plays the rank cutscene on Home", saw_cut)
    lunar = wait_for(pg, "()=>{ const s=document.querySelector('.rs-spot.is-rankreward'); return !!(s && /Lunar/.test(s.textContent)) && !document.getElementById('supernova-cutscene'); }", 30000)
    ck("then the rank's character arrives on Home, as a Rank reward", lunar)
    ctx.close()

    print("4. Review counts the bank it will list")
    ctx, pg = page(br)
    pg.evaluate("""()=>{ const ids=QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes'); const now=Date.now();
      ids.slice(2,9).forEach((i,k)=>{ store.stats[KEYS[i]]={n:5,m:k+1,r:Array.from({length:k+1},(_,j)=>now-j*3600e3)}; }); saveStore();
      cfg.mode='review'; showSetup(); }""")
    pg.wait_for_timeout(600)
    pg.evaluate("()=>[...document.querySelectorAll('.pick')].find(p=>p.textContent.includes('Identity Crimes')).click()"); pg.wait_for_timeout(300)
    pg.evaluate("()=>document.getElementById('nextbtn').click()"); pg.wait_for_timeout(400)
    pg.evaluate("()=>[...document.querySelectorAll('.bank-opt')].find(r=>/Most missed/.test(r.textContent)).click()"); pg.wait_for_timeout(300)
    sheet = pg.evaluate("()=>({line:document.querySelector('.sheet-summary-line').textContent, start:document.getElementById('nextbtn').textContent,"
                        " missed:recentMissedIndexes().filter(i=>QUESTIONS[i].topic==='Identity Crimes').length})")
    ck("the sheet counts the most-missed questions, not the unit", sheet["line"].endswith(" %d question%s" % (sheet["missed"], "" if sheet["missed"] == 1 else "s")), sheet)
    pg.evaluate("()=>document.querySelector('.sheet-begin-btn').click()"); pg.wait_for_timeout(800)
    listed = pg.evaluate("()=>document.querySelectorAll('.screen-answerreview .review-question').length")
    ck("and the list it opens is that many", listed == sheet["missed"], (listed, sheet["missed"]))
    ctx.close()

    print("5. the Supernova results say Main menu")
    ctx, pg = page(br)
    pg.evaluate("""()=>{ theme.reduceMotion=true; applyTheme(); const units=topicsIn(QUESTIONS).filter(u=>u!=='Identity Crimes').slice(0,13);
      store.unitPerfects={}; units.forEach(u=>store.unitPerfects[u]=badgeThresholdFor(u)); store.unitPerfects['Identity Crimes']=badgeThresholdFor('Identity Crimes')-1;
      let p=0; while(levelProgress(p).level<TIER_UNLOCKS.titan.level) p+=50; store.lifetime.points=p; store.points=p; saveStore(); }""")
    pg.evaluate(RUN_UNIT, ["Identity Crimes", True])
    wait_for(pg, "()=>!!document.querySelector('.rs-rewards.rs-done')", 30000)
    btns = pg.evaluate("()=>({rank:rankOf(store), btns:[...document.querySelectorAll('.rs-actions button')].map(b=>b.textContent)})")
    ck("the run reached Supernova", btns["rank"] == "titan", btns)
    ck("and its way out is Main menu, as on every run", "Main menu" in btns["btns"] and "Go Home" not in btns["btns"], btns)
    ctx.close()

    print("6. the grade's words have room beside or under a 100%")
    for w, h in ((320, 568), (375, 667), (393, 852)):
        ctx, pg = page(br, w, h)
        pg.evaluate("()=>{ theme.reduceMotion=true; applyTheme(); }")
        pg.evaluate(RUN_UNIT, ["Identity Crimes", True])
        wait_for(pg, "()=>!!document.querySelector('.rs-rewards.rs-done')", 30000)
        g = pg.evaluate("""()=>{ const g=document.querySelector('.rs-grade'); const sd=g.querySelector('.rs-grade-side').getBoundingClientRect();
          const f=g.querySelector('.rs-grade-frac'); const lh=parseFloat(getComputedStyle(f).lineHeight)||20;
          return {pct:g.querySelector('.rs-pct').textContent, side:Math.round(sd.width), fracLines:Math.round(f.getBoundingClientRect().height/lh)}; }""")
        ck("%dpx: '12 of 12' sits on one line in a column at least 100px wide" % w, g["side"] >= 100 and g["fracLines"] == 1, g)
        ctx.close()

    print("7. the last row to land is clear of the back-to-top button")
    ctx, pg = page(br, 320, 568)
    pg.evaluate(RUN_UNIT, ["Identity Crimes", True])
    wait_for(pg, "()=>!!document.querySelector('.rs-rewards.rs-done')", 60000); pg.wait_for_timeout(1500)
    hit = pg.evaluate("""()=>{ const bt=document.getElementById('backtotop'); if(!bt.classList.contains('show')) return {shown:false, hits:[]}; const r=bt.getBoundingClientRect();
      return {shown:true, hits:[...document.querySelectorAll('.rs-actions button')].map(b=>{ const q=b.getBoundingClientRect();
        const ix=Math.min(q.right,r.right)-Math.max(q.left,r.left), iy=Math.min(q.bottom,r.bottom)-Math.max(q.top,r.top);
        return ix>0&&iy>0 ? b.textContent+' '+Math.round(ix)+'x'+Math.round(iy) : null; }).filter(Boolean)}; }""")
    ck("no results button sits under it where the reveal stops", not hit["hits"], hit)
    ctx.close()

    print("8. the unit-select tour does not promise 35 hundos a badge")
    ctx, pg = page(br)
    pg.evaluate("()=>{ store.seenUnitSelectTour=false; saveStore(); cfg.mode='drill'; showSetup(); }")
    wait_for(pg, "()=>!!document.querySelector('#tour-overlay')", 4000); pg.wait_for_timeout(600)
    txt = pg.evaluate("()=>(document.querySelector('.tour-tooltip, #tour-tooltip, .tour-tip')||document.body).innerText")
    ck("the tour's first step is up", "Tap a unit" in txt, txt[:80])
    ck("and names no flat hundo count (badges need 3-20 by unit size)", not re.search(r"\b35 hundos\b", txt), txt[:160])
    ctx.close()

    print("9. an unlock tipped over mid-run is on that run's results")
    ctx, pg = page(br)
    pg.evaluate("()=>{ store.lifetime.correct = 5000 - 5; saveStore(); window.__spotNames=[]; setInterval(()=>{ const s=document.querySelector('.rs-spot'); "
                "if(s){ const n=(s.querySelector('.unlockbanner-name, .rs-spot-name')||s).textContent; if(__spotNames.indexOf(n)<0) __spotNames.push(n); } }, 80); }")
    pg.evaluate(RUN_UNIT, ["Identity Crimes", True])
    wait_for(pg, "()=>!!document.querySelector('.rs-rewards.rs-done')", 60000)
    got = pg.evaluate("()=>({spots:__spotNames, rows:[...document.querySelectorAll('.rs-unlock')].map(e=>e.innerText.replace(/\\n/g,' '))})")
    ck("Star Trails (5,000 right answers) plays on the run that reached it", any("Star Trails" in x for x in got["spots"]), got)
    ck("and sits in its Unlocked card", any("Star Trails" in x for x in got["rows"]), got)
    ctx.close()

    print("10. the clock running out pays for what was answered")
    ctx, pg = page(br)
    p0 = pg.evaluate("()=>{ cfg.mode='drill'; cfg.timer='down'; cfg.timerMinutes=5; cfg.units=['Identity Crimes']; cfg.source='all'; cfg.size=0; "
                     "beginRun(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic==='Identity Crimes')); "
                     "return {pts:store.lifetime.points, hundos:store.lifetime.perfectTests, hist:(store.testHistory||[]).length}; }")
    pg.wait_for_selector(".qpanel .choice", timeout=25000)
    for k in range(4):
        p = pg.evaluate("()=>pos")
        pg.evaluate(ANSWER, False); pg.wait_for_timeout(250)
        pg.evaluate("()=>{ const b=document.getElementById('nextbtn'); if(b && !b.hidden) b.click(); }")
        wait_for(pg, "()=>pos!==%d" % p, 3000)
    pg.evaluate("()=>onTimeUp()")
    wait_for(pg, "()=>!!document.querySelector('.rs-rewards.rs-done')", 30000)
    t = pg.evaluate("(p0)=>({booked:store.lifetime.points-p0.pts, hundos:store.lifetime.perfectTests-p0.hundos, hist:(store.testHistory||[]).length-p0.hist,"
                    " total:(document.querySelector('.rs-xptotal-num')||{}).textContent,"
                    " stamps:[...document.querySelectorAll('.rs-stamp')].map(e=>e.textContent)})", p0)
    ck("four right answers before the clock ran out pay at least 4 x 10 XP", t["booked"] >= 40, t)
    ck("the XP card prints what was booked", (t["total"] or "").replace(",", "") == "+%d" % t["booked"], t)
    ck("and it still says Time's up", any("Time" in x for x in t["stamps"]), t)
    ck("no hundo and no test played for a run cut short", t["hundos"] == 0 and t["hist"] == 0, t)
    ctx.close()

    print("11. a challenge character's pop-up says it once")
    ctx, pg = page(br)
    sp = pg.evaluate("()=>{ playUnlockSpotlight(characterUnlockItem('masked'),1,1,()=>{}); const s=document.querySelector('.rs-spot'); "
                     "return {strip:(s.querySelector('.rs-spot-strip')||{}).textContent, kicker:(s.querySelector('.rs-spot-kicker')||{}).textContent}; }")
    ck("the strip says the challenge was done", sp["strip"] == "Challenge complete", sp)
    ck("and the kicker says what was unlocked, not the strip again",
       bool(sp["kicker"]) and sp["kicker"] != sp["strip"] and "unlocked" in sp["kicker"].lower(), sp)
    ctx.close()

    print("12. a wrong daily question marks what you picked")
    ctx, pg = page(br)
    pg.evaluate("()=>{ store.dailyQuestionDate=null; saveStore(); startDailyQuestion(); }")
    pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(300)
    pick = pg.evaluate("()=>{ const r=correctSlot(order[pos]); const c=[...document.querySelectorAll('.qpanel .choice')].find(c=>+c.dataset.index!==r); c.click(); return +c.dataset.index; }")
    pg.wait_for_timeout(1000)
    d = pg.evaluate("(pick)=>{ const cs=[...document.querySelectorAll('.qpanel .choice')]; const p=cs.find(c=>+c.dataset.index===pick), r=cs.find(c=>+c.dataset.index===correctSlot(order[pos]));"
                    " const bc=e=>getComputedStyle(e).borderTopColor; const plain=cs.find(c=>c!==p && c!==r);"
                    " return {picked:p.className, pickMark:p.querySelector('.mark').textContent, right:r.className, pickBorder:bc(p), plainBorder:bc(plain), rightBorder:bc(r)}; }", pick)
    ck("the right answer is still marked", "is-right" in d["right"], d)
    ck("the one you picked is marked, in a colour of its own",
       d["pickMark"] != "" and d["pickBorder"] != d["plainBorder"] and d["pickBorder"] != d["rightBorder"], d)
    ctx.close()

    print("13. the start sheet's small controls are 44px targets")
    ctx, pg = page(br)
    pg.evaluate("()=>{ cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(500)
    pg.evaluate("()=>[...document.querySelectorAll('.pick')].find(p=>p.textContent.includes('Identity Crimes')).click()"); pg.wait_for_timeout(300)
    pg.evaluate("()=>document.getElementById('nextbtn').click()"); pg.wait_for_timeout(700)
    c = pg.evaluate("()=>{ const b=document.querySelector('.unitoptions-modal-head .next'); const r=b.getBoundingClientRect();"
                    " const reach=(el,d)=>{ const q=el.getBoundingClientRect(), cx=q.left+q.width/2, cy=q.top+q.height/2;"
                    "   return [[cx-d,cy],[cx+d,cy],[cx,cy-d],[cx,cy+d]].every(([x,y])=>{ const e=document.elementFromPoint(x,y); return e===el || el.contains(e); }); };"
                    " const bi=document.querySelector('.bank-info');"
                    " const cs=getComputedStyle(b), bw=parseFloat(cs.borderTopWidth)||0, clear=/rgba\\(.*, 0\\)|transparent/.test(cs.borderTopColor);"
                    " return {w:r.width, h:r.height, drawn:r.width-(clear?2*bw:0), close21:reach(b,21), info:bi?reach(bi,21):null}; }")
    ck("the close button answers 21px from its centre in every direction", c["close21"] and c["w"] >= 43.5 and c["h"] >= 43.5, c)
    ck("and still draws the same 2.1rem (33.6px) circle", abs(c["drawn"] - 33.6) < 1.5, c)
    ck("the 'How Most missed works' dot answers 21px from its centre too", c["info"] is True, c)
    ctx.close()

    ck("no page errors", not errors, errors[:3])
    br.close()
srv.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
