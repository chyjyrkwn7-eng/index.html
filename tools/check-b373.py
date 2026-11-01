"""Build 373: while a finger slides across the tab bar the animations on the page under it are paused (html.tab-dragging), for a slide only
(not a tap), and the class is gone before the release navigates, so the new screen's entrance runs.
Run:  python3 tools/check-b373.py   (--against: copy the old index.html and version.json over first)"""
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
    pg.wait_for_timeout(1500)
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const st=document.getElementById('stage');
      const run=()=>st.getAnimations({subtree:true}).filter(a=>a.playState==='running'&&a.effect&&a.effect.target&&a.effect.target.closest&&a.effect.target.closest('#stage')).length;
      const paused=()=>st.getAnimations({subtree:true}).filter(a=>a.playState==='paused').length;
      const nav=document.querySelector('.bottomtabs-navrow'), a=document.getElementById('bottomtab-rewards'), b=document.getElementById('bottomtab-calendar');
      const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect(), y=ra.top+ra.height/2, x0=ra.left+ra.width/2, x1=rb.left+rb.width/2;
      const mk=(t,x)=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:7,isPrimary:true,clientX:x,clientY:y});
      const H=()=>document.documentElement.classList.contains('tab-dragging');
      const out={ before:{running:run(),cls:H()} };
      a.dispatchEvent(mk('pointerdown',x0)); await wait(100); out.tapHold={cls:H(),running:run()};
      for(let i=1;i<=12;i++){ nav.dispatchEvent(mk('pointermove',x0+(x1-x0)*i/12)); await wait(16); }
      await wait(100); out.sliding={cls:H(),running:run(),paused:paused()};
      nav.dispatchEvent(mk('pointerup',x1)); out.afterUp={cls:H()}; await wait(1500);
      out.after={cls:H(),onCalendar:!!document.querySelector('.screen-calendar, .cal-title'),running:run()};
      return out; }""")
    chk("a press without a slide leaves the page animating (class %s, running %s)" % (r["tapHold"]["cls"], r["tapHold"]["running"]), (not r["tapHold"]["cls"]) and r["tapHold"]["running"] > 0 and r["before"]["running"] > 0, r)
    chk("sliding pauses the page's animations (class %s, running %s, paused %s)" % (r["sliding"]["cls"], r["sliding"]["running"], r["sliding"]["paused"]), r["sliding"]["cls"] and r["sliding"]["running"] == 0 and r["sliding"]["paused"] > 0, r)
    chk("the release takes it off before navigating, and the new screen is up and running (%s)" % (r["after"],), (not r["afterUp"]["cls"]) and (not r["after"]["cls"]) and r["after"]["onCalendar"], r)
    br.close()
sys.exit(0 if g["ok"] else 1)
