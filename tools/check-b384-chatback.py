"""Build 384: Friends opened from the chat goes back to where you were - a test above all.
Madison: "Chat button while in a test takes you back to main menu. What I mean is, if I am in a test and I hit like manage friends
or something, when I leave that, it goes back to the main menu instead? Fix that."
iPhone 17 Pro Max (440x956), the chat opened on its Friends tab, Manage friends tapped, then Friends' Back:
(1) in a Mock test with its clock: on Friends the test is held (paused, the clock not moving), Friends has no tab bar (the test has
    none - Back is the way out) and none of the test's strip; Back is the test again on the same question with its answers in the
    same order, no longer paused, the clock moving, Pause and the progress dots shown, the chat open on Friends; the time away is not counted (the clock reads what it read when Friends opened, give or take the chat being open before and the moment after Back - 3s);
(2) Review's list, scrolled down: Back is the same list at the same scroll, its Pause there, its run alive (Pause pauses it);
(3) flash cards, on the third card with its answer showing: Back is the same deck on the same card, answer side up;
(4) the unit screen with two units ticked: Back is the unit screen with those two still ticked;
(5) Home: Back is Home with the chat on Friends (as before);
(6) no page errors.
Run:  python3 tools/check-b384-chatback.py   (--against OLD/index.html must FAIL)"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384cb"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
CLEAN = "document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner').forEach(e=>e.remove());"
def manage_friends(pg):
    pg.evaluate("()=>{ %s chatDockTab = 'friends'; openChatDock(); }" % CLEAN); pg.wait_for_timeout(900)
    ok = pg.evaluate("()=>{ const b=document.querySelector('.chatdock-panel .chatdock-friendsbar-btn'); if(!b) return false; b.click(); return true; }")
    pg.wait_for_timeout(1100)
    return ok
def back(pg):
    pg.evaluate("()=>document.querySelector('#stage .screen-friends .back-link')?.click()"); pg.wait_for_timeout(1300)
TABS = "()=>{ const t=document.querySelector('.bottomtabs'); if(!t) return false; const r=t.getBoundingClientRect(), c=getComputedStyle(t); return r.height > 0 && c.display !== 'none' && c.visibility !== 'hidden' && +c.opacity > .1 && r.top < innerHeight; }"
CLOCK = "()=>{ const t=typeof tmainEl !== 'undefined' ? tmainEl : null; return t && !timerlineEl.hidden ? t.textContent.trim() : null; }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    # (1) a Mock test with its clock
    pg.evaluate("""()=>{ const t=topicsIn(QUESTIONS)[3]; cfg.mode='exam'; runMode='exam'; cfg.units=[t]; cfg.source='all'; cfg.timer='down'; cfg.timerMinutes=10;
      beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0,6), null, null); }""")
    for _ in range(60):
        if pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(2200)
    pg.evaluate("()=>{ document.querySelector('.qpanel .choice')?.click(); }"); pg.wait_for_timeout(500)
    pg.evaluate("()=>{ const n=document.querySelector('#nextbtn, .qpanel .next'); n && !n.hidden && n.click(); }"); pg.wait_for_timeout(1400)
    before = pg.evaluate("()=>({ pos, q: (document.querySelector('.qpanel .qtext')||{}).textContent || '', clock: (" + CLOCK + ")(), paused, ch: [...document.querySelectorAll('.qpanel .choice')].map(c=>c.textContent.trim()) })")
    opened = manage_friends(pg)
    ck("(1) in a test, the chat's Manage friends opens Friends", opened and pg.evaluate("()=>!!document.querySelector('#stage .screen-friends')"), opened)
    c1 = pg.evaluate(CLOCK); pg.wait_for_timeout(3200); c2 = pg.evaluate(CLOCK)
    held = pg.evaluate("()=>({ paused, test: testInProgress, tabs: (" + TABS + ")(), strip: !meterEl.hidden || !timerlineEl.hidden })")
    ck("(1) on Friends the test is held - paused, its clock still (%s -> %s)" % (c1, c2), held["paused"] and held["test"] and c1 == c2, held)
    ck("(1) and Friends has no tab bar over a test (Back is the way out), and none of the test's strip (its dots, its clock)", not held["tabs"] and not held["strip"], held)
    back(pg)
    after = pg.evaluate("()=>({ pos, q: (document.querySelector('.qpanel .qtext')||{}).textContent || '', clock: (" + CLOCK + ")(), paused, test: testInProgress, choices: document.querySelectorAll('.qpanel .choice').length, ch: [...document.querySelectorAll('.qpanel .choice')].map(c=>c.textContent.trim()), meter: !meterEl.hidden, pause: !pauseBtn.hidden, chat: chatDockOpen, tab: chatDockTab, home: !!document.querySelector('#stage .screen-home-actual') })")
    pg.wait_for_timeout(2300); later = pg.evaluate(CLOCK)
    ck("(1) Back is the test on the same question (%s, '%s...'), not Home" % (after["pos"], after["q"][:30]),
       not after["home"] and after["test"] and after["choices"] >= 2 and after["pos"] == before["pos"] and after["q"] == before["q"], [before, after])
    ck("(1) its answers in the same order (%s)" % " | ".join(after["ch"]), after["ch"] == before["ch"] and len(after["ch"]) >= 2, [before["ch"], after["ch"]])
    ck("(1) resumed: not paused, Pause shown, its progress dots back, the clock moving again (%s -> %s)" % (after["clock"], later), not after["paused"] and after["pause"] and after["meter"] and after["clock"] != later, after)
    def secs(t):
        m = re.findall(r"(\d+):(\d\d)", t or ""); return int(m[0][0]) * 60 + int(m[0][1]) if m else None
    ck("(1) the time on Friends is not counted (the clock %s when Friends opened, %s back)" % (before["clock"], after["clock"]),
       secs(before["clock"]) is not None and secs(after["clock"]) is not None and abs(secs(after["clock"]) - secs(before["clock"])) <= 3, [before["clock"], after["clock"]])
    ck("(1) and the chat is open again on Friends, where you left it", after["chat"] and after["tab"] == "friends", after)
    pg.evaluate("()=>{ try{ closeChatDock(); }catch(e){} testInProgress=false; paused=false; stopTimer(); stopQuestionTimer(); showHome(); }"); pg.wait_for_timeout(900)
    # (2) Review's list, scrolled
    pg.evaluate("()=>{ showAnswerReview([topicsIn(QUESTIONS)[3]], 'all'); }"); pg.wait_for_timeout(1400)
    pg.evaluate("()=>window.scrollTo(0, 900)"); pg.wait_for_timeout(500)
    y0 = pg.evaluate("()=>Math.round(scrollY)")
    manage_friends(pg); back(pg)
    r = pg.evaluate("()=>({ list: !!document.querySelector('#stage .screen-answerreview'), y: Math.round(scrollY), run: !!answerReviewRun, pause: !pauseBtn.hidden, chat: chatDockOpen })")
    ck("(2) Review's list: Back is the same list at the same scroll (%s / %s), its Pause there and alive" % (r["y"], y0),
       r["list"] and abs(r["y"] - y0) <= 4 and r["run"] and r["pause"], r)
    pg.evaluate("()=>{ try{ closeChatDock(); }catch(e){} pauseRun(); }"); pg.wait_for_timeout(700)
    ck("(2) and its Pause still pauses it", pg.evaluate("()=>!!document.querySelector('.pausepanel.is-arpause')"))
    pg.evaluate("()=>{ answerReviewLeave(); showHome(); }"); pg.wait_for_timeout(700)
    # (3) flash cards, third card, answer side
    pg.evaluate("()=>{ showFlashcards([topicsIn(QUESTIONS)[3]], 'all'); }"); pg.wait_for_timeout(1300)
    pg.evaluate("()=>{ fc.pos = 2; renderFlashcard(2); }"); pg.wait_for_timeout(700)
    pg.evaluate("()=>document.querySelector('.fc-card')?.click()"); pg.wait_for_timeout(800)
    f0 = pg.evaluate("()=>({ pos: fc.pos, q: (document.querySelector('.fc-card .fc-front')||{}).textContent || '', flipped: document.querySelector('.fc-card').classList.contains('is-flipped') })")
    manage_friends(pg); back(pg)
    f1 = pg.evaluate("()=>({ fc: !!fc, pos: fc && fc.pos, q: (document.querySelector('.fc-card .fc-front')||{}).textContent || '', flipped: !!document.querySelector('.fc-card.is-flipped'), pause: !pauseBtn.hidden })")
    ck("(3) flash cards: Back is the same deck on the same card (%s), answer side up" % f1.get("pos"),
       f0["flipped"] and f1["fc"] and f1["pos"] == f0["pos"] and f1["q"] == f0["q"] and f1["flipped"] and f1["pause"], [f0, f1])
    pg.evaluate("()=>{ try{ closeChatDock(); }catch(e){} fcLeave(); showHome(); }"); pg.wait_for_timeout(700)
    # (4) the unit screen with two ticked
    pg.evaluate("()=>{ cfg.mode='drill'; cfg.units=[]; showSetup(); }"); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ const c=[...document.querySelectorAll('.picks > label.pick')]; [1,3].forEach(i=>c[i] && c[i].querySelector('input').click()); }"); pg.wait_for_timeout(600)
    u0 = pg.evaluate("()=>[...document.querySelectorAll('.picks > label.pick.pick-checked')].map(l=>l.textContent.trim().slice(0,20))")
    manage_friends(pg); back(pg)
    u1 = pg.evaluate("()=>({ setup: !!document.querySelector('#stage .picks'), picked: [...document.querySelectorAll('.picks > label.pick.pick-checked')].map(l=>l.textContent.trim().slice(0,20)) })")
    ck("(4) the unit screen: Back is the unit screen with the same two ticked (%s)" % u1["picked"], u1["setup"] and len(u0) == 2 and u1["picked"] == u0, [u0, u1])
    pg.evaluate("()=>{ try{ closeChatDock(); }catch(e){} showHome(); }"); pg.wait_for_timeout(900)
    # (5) Home, as before
    manage_friends(pg); back(pg)
    h = pg.evaluate("()=>({ home: !!document.querySelector('#stage .screen-home-actual'), chat: chatDockOpen, tab: chatDockTab })")
    ck("(5) Home: Back is Home with the chat on Friends (as before)", h["home"] and h["chat"] and h["tab"] == "friends", h)
    ck("(6) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
