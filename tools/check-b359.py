"""Build 359 (also: taps ~0.7s apart are not a "run" and get no extra wait): a tapped tab's screen is built as soon as the finger lifts (30ms after the glass starts), not 120ms later: the
glass is a compositor animation and carries on under the build, so the wait only delayed the page.
Run:  python3 tools/check-b359.py   (add --against old.html to run on another build)"""
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
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const out=[];
      for(const d of ['calendar','profile','home','calendar']){ const el=document.getElementById('bottomtab-'+d); const r=el.getBoundingClientRect(); const x=r.left+r.width/2,y=r.top+r.height/2;
        const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:42,isPrimary:true,clientX:x,clientY:y});
        const b0=document.getElementById('bottomtabs')._navBuilds||0;
        el.dispatchEvent(mk('pointerdown')); await wait(30); el.dispatchEvent(mk("pointerup")); const t0=performance.now(); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
        let ms=-1; while(performance.now()-t0<1500){ if((document.getElementById('bottomtabs')._navBuilds||0)>b0){ ms=performance.now()-t0; break; } await wait(2); }
        out.push([d, Math.round(ms)]); await wait(700); }
      return out; }""")
    print(r)
    chk("a single tap starts its screen's build within 100ms of the lift (%s)" % (r,), all(0 <= x[1] <= 100 for x in r), r)
    br.close()
sys.exit(0 if g["ok"] else 1)
