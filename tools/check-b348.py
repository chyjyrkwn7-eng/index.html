"""Build 348: the Leaderboard builds a screenful and finishes the list on the frames after (so a board switch is not one
long task); the daily question button starts on a touch that lands and lifts on it even if no click comes; its Submit
answer pill stands higher.   Run:  python3 tools/check-b348.py"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL); pg.evaluate("()=>{ showRankings(); }"); pg.wait_for_timeout(2500)
    full = pg.evaluate("()=>document.querySelectorAll('.rank-rows .rank-row').length")
    chk("the board ends up with every row (%d)" % full, full >= 42, full)
    now = pg.evaluate("""()=>{ [...document.querySelectorAll('.profiletabs .iconbtn')].find(b=>b.textContent.trim()==='Hundos').click(); return document.querySelectorAll('.rank-rows .rank-row').length; }""")
    chk("right after a switch only a screenful is built (%d of %d)" % (now, full), 6 <= now <= 22, now)
    pg.wait_for_timeout(1500)
    later = pg.evaluate("()=>document.querySelectorAll('.rank-rows .rank-row').length")
    chk("and the rest follows on the next frames (%d)" % later, later >= 42, later)
    r = pg.evaluate("""()=>{ [...document.querySelectorAll('.profiletabs .iconbtn')].find(b=>b.textContent.trim()==='Overall').click(); document.querySelector('.rank-me-btn').click(); return { rows: document.querySelectorAll('.rank-rows .rank-row').length, me: !!document.querySelector('.rank-rows [data-me="1"]') }; }""")
    chk("Find me finishes the list first and finds your row", r["rows"] >= 42 and r["me"], r)
    # the daily question: a touch with no click
    pg.evaluate("()=>{ store.dailyQuestionDate=''; showHome(); }"); pg.wait_for_timeout(1800)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    moved = pg.evaluate("""async ()=>{ const f=document.querySelector('.daily-question-fab'); const b=f.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const ev=(t,dx)=>new PointerEvent(t,{bubbles:true,pointerType:'touch',pointerId:7,clientX:x+dx,clientY:y,isPrimary:true});
      f.dispatchEvent(ev('pointerdown',0)); f.dispatchEvent(ev('pointerup',30)); await new Promise(r=>setTimeout(r,250)); return !!document.querySelector('.qpanel'); }""")
    chk("a touch that slides off by 30px does not start the question", not moved, moved)
    started = pg.evaluate("""async ()=>{ const f=document.querySelector('.daily-question-fab'); const b=f.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const ev=(t,dx)=>new PointerEvent(t,{bubbles:true,pointerType:'touch',pointerId:8,clientX:x+dx,clientY:y,isPrimary:true});
      f.dispatchEvent(ev('pointerdown',0)); f.dispatchEvent(ev('pointerup',2)); await new Promise(r=>setTimeout(r,400)); return !!document.querySelector('.qpanel'); }""")
    chk("a touch that lands and lifts on it starts the question even when no click arrives", started, started)
    pg.wait_for_timeout(1200)
    s = pg.evaluate("""()=>{ const b=document.getElementById('dailyq-submitbtn'); if(!b) return null; const r=b.getBoundingClientRect(); return { gap: innerHeight - r.bottom, vh: innerHeight }; }""")
    chk("the daily question's Submit answer stands 32px or more off the bottom (%s)" % (s,), s and s["gap"] >= 32, s)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
