"""Build 363: the Leaderboard's characters and flares wait ~450ms after the list is first asked for before they start to fill
(the screen lands bare, then fills a row a frame), so the arrival is not held by drawing them; Send tab timings carries the
`ended:` log (how earlier runs ended).
Run:  python3 tools/check-b363.py   (add --against old.html to run on another build)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); showRankings();
      const bare=()=>[...document.querySelectorAll('.rank-rows .rank-row')].filter(x=>{const b=x.getBoundingClientRect(); return b.top<innerHeight-90&&b.bottom>60&&x.dataset.lazyArt}).length;
      const vis=()=>[...document.querySelectorAll('.rank-rows .rank-row')].filter(x=>{const b=x.getBoundingClientRect(); return b.top<innerHeight-90&&b.bottom>60}).length;
      const out={ vis: vis() }; await wait(250); out.bare250 = bare(); await wait(1600); out.bare1850 = bare(); return out; }""")
    chk("at 250ms the rows in view are still bare, and by 1.85s they have their art (%s)" % (r,), r["vis"] >= 6 and r["bare250"] >= r["vis"] - 1 and r["bare1850"] == 0, r)
    pg.evaluate("()=>{ try{ localStorage.setItem('class26e.crashlog', JSON.stringify(['ENDED-visible board 3s-ago b363'])); }catch(e){} }")
    txt = pg.evaluate("()=>tabPerfText()")
    chk("the tab timings carry the ended log (%s)" % (txt[:140],), "ended: ENDED-visible board" in txt, txt)
    # the tab's icon and word do not grow under the glass
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    m = pg.evaluate("""async()=>{ const el=document.getElementById('bottomtab-rewards'); const b=el.getBoundingClientRect(); const x=b.left+b.width/2,y=b.top+b.height/2; const out={max:1};
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:61,isPrimary:true,clientX:x,clientY:y});
      const tabs=[...document.querySelectorAll('.bottomtabs-navrow .bottomtab')].filter(t=>t.offsetWidth); let stop=false;
      const tick=()=>{ tabs.forEach(t=>{ const m=getComputedStyle(t).transform; if(m&&m!=='none'){ const k=parseFloat(m.slice(7)); if(k>out.max) out.max=k; } }); if(!stop) requestAnimationFrame(tick); }; tick();
      el.dispatchEvent(mk('pointerdown')); await new Promise(r=>setTimeout(r,500)); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y})); await new Promise(r=>setTimeout(r,1500)); stop=true; return out; }""")
    chk("no tab is scaled up while the glass is over it (largest scale %s)" % (m["max"],), m["max"] <= 1.001, m)
    br.close()
sys.exit(0 if g["ok"] else 1)
