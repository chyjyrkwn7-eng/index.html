"""Build 384: the back button and the chat button meet in the middle.
Madison, on Choose your mode: "The chat button should be slightly relocated so it's brought down a little, so it lines up with the
new back button, cause it seems out of place now? Or maybe they could both kinda meet each other in the middle so the change isn't
noticeable but still improved? ... move the back button slightly up and the chat button slightly down?"
Installed on an iPhone 17 Pro Max (440x956, its 62px top inset) and an iPad Pro 11" (834x1194), the chat button read once it has
come to rest:
(1) on pushed screens - the modes, Settings' pages, Customize, Friends, Badges, Contributors - the round back button's middle and
    the chat button's middle are on one line (within 1px);
(2) they met in the middle: the back button is higher than it was and the chat button lower (each moved, neither the whole way);
(3) on Home and a tab screen (the Leaderboard) the chat button is where it always was: its top is the inset plus .75rem;
(4) no page errors.
Run:  python3 tools/check-b384-navmeet.py   (--against OLD/index.html must FAIL)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "b384nm"}
exec(src, g)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
PUSHED = [("modes", "showModeSelect()"), ("sound", "showAppearance({page:'sound'})"), ("customize", "showCustomize()"), ("friends", "showFriends()"),
          ("badges", "showRanksScreen('badges')"), ("credits", "showCredits()")]
TABS = [("home", "showHome()"), ("leaderboard", "showRankings()")]
SETTLE = """async ()=>{ const c=document.getElementById('chatdock-btn'); let last=null, same=0;
  for(let i=0;i<60;i++){ await new Promise(r=>setTimeout(r,100)); const t=c.getBoundingClientRect().top; if(last!==null && Math.abs(t-last)<.05 && t>0) { if(++same>=4) break; } else same=0; last=t; }
  const R=e=>{ if(!e) return null; const r=e.getBoundingClientRect(); return { cy: r.top + r.height/2, top: r.top }; };
  const back=document.querySelector('#stage .settings-nav-back, #stage .ios-nav-back');
  const rem=parseFloat(getComputedStyle(document.documentElement).fontSize);
  return { chat: R(c), back: R(back), rem }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    srv, url = g["serve"]()
    errs = []
    for (W, H, INS, dev) in ((440, 956, (62, 0, 34, 0), "17 Pro Max"), (834, 1194, (24, 0, 20, 0), "iPad Pro 11")):
        g["new_page"].w, g["new_page"].h = W, H
        ctx, pg = g["new_page"](br, INS, True, True)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url); pg.wait_for_timeout(3500)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner').forEach(e=>e.remove()); }")
        # a seeded account can open on an unlock cutscene, which parks the chat button off the top (body.cutscene-focus): let it end
        for _ in range(40):
            if not pg.evaluate("()=>document.body.classList.contains('cutscene-focus') || document.body.classList.contains('cutscene-return')"): break
            pg.evaluate("()=>{ document.querySelectorAll('.unlock-card .next, .rs-spot .next, .cutscene-skip, .ru-skip').forEach(b=>{ try{ b.click(); }catch(e){} }); }")
            pg.wait_for_timeout(500)
        off, moved = [], []
        for name, js in PUSHED:
            pg.evaluate("()=>{ %s; window.scrollTo(0,0); }" % js); pg.wait_for_timeout(600)
            r = pg.evaluate(SETTLE)
            if not (r["chat"] and r["back"]) or abs(r["chat"]["cy"] - r["back"]["cy"]) > 1: off.append((name, r))
            moved.append((name, r))
        chk("(1) %s: the back button and the chat button on one line on %d pushed screens (%s)" % (dev, len(PUSHED), [(n, round(r["chat"]["cy"], 1) if r["chat"] else None, round(r["back"]["cy"], 1) if r["back"] else None) for n, r in moved]),
            not off, off[:2])
        tabs = []
        for name, js in TABS:
            pg.evaluate("()=>{ %s; window.scrollTo(0,0); }" % js); pg.wait_for_timeout(600)
            tabs.append((name, pg.evaluate(SETTLE)))
        home_top = tabs[0][1]["chat"]["top"]; rem = tabs[0][1]["rem"]
        restTop = INS[0] + .75 * rem
        chk("(3) %s: Home and the Leaderboard keep the chat button where it was (tops %s, the inset + .75rem = %s)" % (dev, [round(t[1]["chat"]["top"], 1) for t in tabs], restTop),
            all(abs(t[1]["chat"]["top"] - restTop) <= 1 for t in tabs), tabs)
        # (2) met in the middle: the chat button on a pushed screen is lower than at rest, and the back button's middle is above where
        # a resting chat button's middle is plus the old gap - i.e. each moved part of the way
        r0 = moved[0][1]
        chatRest = restTop + (tabs[0][1]["chat"]["cy"] - tabs[0][1]["chat"]["top"])
        chk("(2) %s: they met in the middle - the chat button came down (%.1f -> %.1f) and the back button is up, level with it" % (dev, chatRest, r0["chat"]["cy"]),
            r0["chat"]["cy"] > chatRest + 2 and abs(r0["back"]["cy"] - r0["chat"]["cy"]) <= 1, [chatRest, r0])
        ctx.close()
    chk("(4) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
