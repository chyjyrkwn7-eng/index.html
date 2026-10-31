"""Build 364: a tap 200-600ms after another waits a build's own cost (50-120ms) for its screen, not the spam hold (280ms); taps under
200ms apart still collapse (check-b356).
Run:  python3 tools/check-b364.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const bar=document.getElementById('bottomtabs'); const out=[];
      const tap=async(d)=>{ const el=document.getElementById('bottomtab-'+d); const b=el.getBoundingClientRect(); const x=b.left+b.width/2,y=b.top+b.height/2;
        const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:81,isPrimary:true,clientX:x,clientY:y});
        const b0=bar._navBuilds||0; el.dispatchEvent(mk('pointerdown')); await wait(30); el.dispatchEvent(mk('pointerup')); const t0=performance.now(); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
        let ms=-1; while(performance.now()-t0<900){ if((bar._navBuilds||0)>b0){ ms=Math.round(performance.now()-t0); break; } await wait(2); } return ms; };
      await tap('rewards'); await wait(1800);
      // pairs of taps 280ms apart: the second one's build
      for(const [a,b] of [['profile','home'],['calendar','rewards'],['home','profile']]){ await tap(a); await wait(250); out.push([b, await tap(b)]); await wait(1800); }
      return out; }""")
    print(r)
    chk("a tap 280ms after another builds its screen within 130ms (%s)" % (r,), all(0 <= x[1] <= 130 for x in r), r)
    br.close()
sys.exit(0 if g["ok"] else 1)
