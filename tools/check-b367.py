"""Build 367: Report a bug has a Drag test (for a screen recording) that puts six looks of the bar on one after another - A the bar as it is, B the bar
solid while the glass is up, C no blend or mask on the glass, D a lighter bar blur, E B and C and no rim shadow, F no glass - naming the one on in a
banner, and takes them all off at the end.
Run:  python3 tools/check-b367.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
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
    pg.evaluate("()=>showBugReport()"); pg.wait_for_timeout(500)
    btns = pg.evaluate("()=>[...document.querySelectorAll('.screen-bugreport button')].map(b=>b.textContent.trim())")
    chk("Report a bug has the Drag test button (%s)" % (btns,), any(b.startswith("Drag test") for b in btns), btns)
    r = pg.evaluate("""async()=>{ window.__dragTick=25; const seen=[]; const p=runDragTest(); let last='';
      const iv=setInterval(()=>{ const n=[...document.body.children].find(e=>e.tagName==='DIV'&&/^(Look |Slide across)/.test(e.textContent||'')); const t=n?n.textContent:''; if(t!==last){ last=t; const st=document.getElementById('drag-look'); seen.push([t.slice(0,18), st?st.textContent.length:-1]); } },5);
      await p; clearInterval(iv); return { seen, left: !!document.getElementById('drag-look'), banner: [...document.body.children].some(e=>e.tagName==='DIV'&&/^Look /.test(e.textContent||'')) }; }""")
    letters = "".join(sorted(set(x[0][5] for x in r["seen"] if x[0].startswith("Look "))))
    chk("the six looks run in turn and are all taken off at the end (%s, left %s)" % (letters, r["left"]), letters == "ABCDEF" and not r["left"] and not r["banner"], r)
    br.close()
sys.exit(0 if g["ok"] else 1)
