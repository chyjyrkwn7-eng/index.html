"""Build 368: a slide across the tab bar's own space (the pill and the margin round it, which is the bare page as far as the touch target goes) is not a swipe of the
screen: on the Leaderboard it changed board with the board switch's "ding", on Profile it changed the top tab. A swipe on the screen itself still does.
Run:  python3 tools/check-b368.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
SW = """async(y, dx)=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const x=220;
  const mk=(type,xx)=>{ const t=new Touch({identifier:7,target:document.body,clientX:xx,clientY:y}); return new TouchEvent(type,{bubbles:true,cancelable:true,touches:type==='touchend'?[]:[t],targetTouches:type==='touchend'?[]:[t],changedTouches:[t]}); };
  document.body.dispatchEvent(mk('touchstart',x)); await wait(20); document.body.dispatchEvent(mk('touchmove',x+dx/2)); await wait(20); document.body.dispatchEvent(mk('touchmove',x+dx)); await wait(20); document.body.dispatchEvent(mk('touchend',x+dx)); await wait(300);
  return rankingsBoardKey; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL); pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(1500)
    bar = pg.evaluate("()=>{ const r=document.getElementById('bottomtabs').getBoundingClientRect(); return { top:r.top, bottom:r.bottom, h:innerHeight }; }")
    yMargin = min(bar["bottom"] + 6, bar["h"] - 1)
    k1 = pg.evaluate(SW, [yMargin, -140])
    chk("a slide that starts just below the bar (y %d) does not change the board (%s)" % (yMargin, k1), k1 == "overall", [bar, k1])
    k2 = pg.evaluate(SW, [bar["top"] - 8, -140])
    chk("nor one that starts just above the bar's top (%s)" % (k2,), k2 == "overall", k2)
    k3 = pg.evaluate(SW, [bar["top"] - 160, -140])
    chk("a swipe on the screen itself still changes it (%s)" % (k3,), k3 == "hundos", k3)
    br.close()
sys.exit(0 if g["ok"] else 1)
