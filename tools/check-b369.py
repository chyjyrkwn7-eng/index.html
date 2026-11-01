"""Build 369: the Drag test runs on the Leaderboard (animated rows under the bar) and a release during it does not leave the screen; the page carries html.tab-held
while the tab bar is held (the looks that pause animations use it).
Run:  python3 tools/check-b369.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
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
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const el=document.getElementById('bottomtab-home'); const b=el.getBoundingClientRect(); const x=b.left+b.width/2,y=b.top+b.height/2;
      const mk=(t,xx)=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:95,isPrimary:true,clientX:xx,clientY:y});
      const nav=document.querySelector('.bottomtabs-navrow'); const out={};
      el.dispatchEvent(mk('pointerdown',x)); await wait(50); out.heldDown=document.documentElement.classList.contains('tab-held');
      nav.dispatchEvent(mk('pointerup',x)); await wait(1500); out.heldAfter=document.documentElement.classList.contains('tab-held'); return out; }""")
    chk("the page carries tab-held while the bar is held, and not after (%s)" % (r,), r["heldDown"] and not r["heldAfter"], r)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
    d = pg.evaluate("""async()=>{ window.__dragTick=40; const p=runDragTest(); await new Promise(r=>setTimeout(r,200));
      const onBoard=!!document.querySelector('.screen-rankings');
      // a drag from Home to Calendar and a release over Calendar, mid test
      const wait=ms=>new Promise(r=>setTimeout(r,ms)); const a=document.getElementById('bottomtab-home'), c=document.getElementById('bottomtab-calendar'); const ra=a.getBoundingClientRect(), rc=c.getBoundingClientRect(); const y=ra.top+ra.height/2, x0=ra.left+ra.width/2, x1=rc.left+rc.width/2; const nav=document.querySelector('.bottomtabs-navrow');
      const mk=(t,xx)=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:96,isPrimary:true,clientX:xx,clientY:y});
      await wait(300); a.dispatchEvent(mk('pointerdown',x0)); await wait(40); for(let i=1;i<=12;i++){ nav.dispatchEvent(mk('pointermove',x0+(x1-x0)*i/12)); await wait(12); } nav.dispatchEvent(mk('pointerup',x1)); await wait(600);
      const still=!!document.querySelector('.screen-rankings'); await p; return { onBoard, still }; }""")
    chk("the Drag test opens the Leaderboard and a release over another tab does not leave it (%s)" % (d,), d["onBoard"] and d["still"], d)
    br.close()
sys.exit(0 if g["ok"] else 1)
