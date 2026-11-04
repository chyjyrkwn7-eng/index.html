"""Build 383: Review's question list is left from Pause, and every mode's way out lands on Home.
Madison: "In the review mode, there's a button that says back to options. It needs the pause button that follows you as you
scroll down so you can leave whenever instead. Fix this. This is very much needed." / "in drill mode when you quit the test,
it takes you to the main menu/Home Screen which is great. When leaving every other mode it needs to do the same and take you
back to the Home Screen, cause right it just goes back to the unit selection screen so fix that pathway/navigation."
Phone 440x956:
(1) Review's list has no back link; Pause is up, and after scrolling 2,500px down it is still on screen, in the same place;
    the header row says Review;
(2) Pause: a pause screen with Resume and Exit review; Resume puts the same list back where it was scrolled to;
(3) Exit review lands on Home, Pause gone;
(4) the list's Finished lands on Home;
(5) Flashcards' Exit flashcards lands on Home;
(6) the list left another way (a tab) takes its Pause with it;
(7) a Drill's Quit test still lands on Home.
Run:  python3 tools/check-b383-review.py   (--against OLD/index.html must FAIL)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b383r"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
ST = """()=>{ const p=document.getElementById('pausebtn'); const r=p.getBoundingClientRect();
  return { pause: !p.hidden && r.height > 0 && r.bottom > 0 && r.top < innerHeight, top: Math.round(r.top), y: Math.round(scrollY),
    screen: ((document.querySelector('#stage > .panel')||{}).className||''), back: !!document.querySelector('#stage .screen-answerreview .back-link'),
    label: (document.getElementById('testmodelabel')||{}).textContent || '',
    labelShown: (e => !!e && getComputedStyle(e).display !== 'none')(document.getElementById('testmodelabel')),
    home: !!document.querySelector('#stage .screen-home-actual') }; }"""
OPEN = "()=>{ const t=topicsIn(QUESTIONS)[6]; cfg.mode='review'; cfg.units=[t]; cfg.source='all'; showAnswerReview([t], 'all'); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    def tap(sel):
        try: pg.click(sel, timeout=3000)
        except Exception: pass
    pg.evaluate(OPEN); pg.wait_for_timeout(1200)
    a = pg.evaluate(ST)
    ck("(1) the list has no back link, Pause is up, the header row says Review (%s)" % a, not a["back"] and a["pause"] and a["label"] == "Review" and a["labelShown"], a)
    pg.evaluate("()=>window.scrollTo(0, 2500)"); pg.wait_for_timeout(700)
    b = pg.evaluate(ST)
    ck("(1) scrolled %dpx down: Pause still on screen, in the same place (%s -> %s)" % (b["y"], a["top"], b["top"]), b["y"] >= 2000 and b["pause"] and abs(b["top"] - a["top"]) <= 1, b)
    tap("#pausebtn"); pg.wait_for_timeout(900)
    c = pg.evaluate("""()=>({ screen: ((document.querySelector('#stage > .panel')||{}).className||''),
      buttons: [...document.querySelectorAll('#stage .pausepanel button')].map(x=>x.textContent.trim()) })""")
    ck("(2) Pause: a pause screen with Resume and Exit review (%s)" % c["buttons"], "pausepanel" in c["screen"] and "Resume" in c["buttons"] and "Exit review" in c["buttons"], c)
    tap("#resumebtn"); pg.wait_for_timeout(900)
    d = pg.evaluate(ST)
    ck("(2) Resume: the same list, where it was (%s, was %s)" % (d["y"], b["y"]), "screen-answerreview" in d["screen"] and abs(d["y"] - b["y"]) <= 40 and d["pause"], d)
    tap("#pausebtn"); pg.wait_for_timeout(800)
    pg.evaluate("()=>{ const b=[...document.querySelectorAll('#stage .pausepanel button')].find(x=>/Exit review/.test(x.textContent)); if(b) b.click(); }"); pg.wait_for_timeout(1500)
    e = pg.evaluate(ST)
    ck("(3) Exit review lands on Home, Pause gone", e["home"] and not e["pause"], e)
    pg.evaluate(OPEN); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ const b=document.querySelector('#stage .screen-answerreview #nextbtn'); if(b) b.click(); }"); pg.wait_for_timeout(1500)
    f = pg.evaluate(ST)
    ck("(4) the list's Finished lands on Home", f["home"] and not f["pause"], f)
    pg.evaluate("()=>{ const t=topicsIn(QUESTIONS)[6]; showFlashcards([t], 'all'); }"); pg.wait_for_timeout(1200)
    tap("#pausebtn"); pg.wait_for_timeout(800)
    pg.evaluate("()=>{ const b=[...document.querySelectorAll('#stage .pausepanel button')].find(x=>/Exit flashcards/.test(x.textContent)); if(b) b.click(); }"); pg.wait_for_timeout(1500)
    h = pg.evaluate(ST)
    ck("(5) Exit flashcards lands on Home", h["home"] and not h["pause"], h)
    pg.evaluate(OPEN); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ showProfile(); }"); pg.wait_for_timeout(1200)
    i = pg.evaluate(ST)
    ck("(6) the list left another way: its Pause goes with it", "screen-profile" in i["screen"] and not i["pause"], i)
    pg.evaluate("""()=>{ const t=topicsIn(QUESTIONS)[6]; cfg.mode='drill'; cfg.units=[t]; cfg.source='all';
      beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0,5), null, null); }""")
    pg.wait_for_timeout(4500)
    tap("#pausebtn"); pg.wait_for_timeout(800)
    tap("#pause-quit"); pg.wait_for_timeout(800)
    tap("#quit-confirm"); pg.wait_for_timeout(1500)
    j = pg.evaluate(ST)
    ck("(7) a Drill's Quit test still lands on Home", j["home"] and not j["pause"], j)
    ck("no page errors", not errs, errs[:2])
    ctx.close()
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
