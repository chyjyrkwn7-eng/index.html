"""Build 371: the Drag test's looks take BLURRED SURFACES away (backdrop-filter): A the Leaderboard as is, B the Report a bug screen, C every blur
but the bar's off, D the chat dock gone, E both, F both and the page hidden. The banner goes off 2s into each look, and each look's frame
intervals are kept (window.__dragLines) and sent. Reads the live page in each look (computed styles, which screen is up), not the labels.
Run:  python3 tools/check-b371.py   (--against: copy the old index.html and version.json over first)"""
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
    r = pg.evaluate("""async()=>{ window.__dragTick=120; const per={}; const p=runDragTest(); let done=false; p.then(()=>done=true);
      const banner=()=>[...document.body.children].find(e=>e.tagName==='DIV'&&/^(Look |Slide across)/.test(e.textContent||''));
      while(!done){ const n=banner(); const L=n&&/^Look /.test(n.textContent)?n.textContent[5]:null;
        if(L && !per[L] && n.style.visibility==='hidden'){ document.documentElement.classList.add('tab-held'); await new Promise(r=>setTimeout(r,40));
          const bf=[...document.querySelectorAll('body *')].filter(e=>{ if(e.closest('.bottomtabs')||e.tagName==='STYLE'||e===n) return false; const c=getComputedStyle(e); return c.display!=='none'&&c.backdropFilter&&c.backdropFilter!=='none'; }).length;
          const dock=document.getElementById('chatdock');
          per[L]={ board:!!document.querySelector('.screen-rankings'), bug:!!document.querySelector('.screen-bugreport'), blurs:bf, dock:dock?getComputedStyle(dock).display:'none',
            stage:getComputedStyle(document.getElementById('stage')).visibility, barBlur:getComputedStyle(document.querySelector('.bottomtabs')).backdropFilter };
          document.documentElement.classList.remove('tab-held'); }
        await new Promise(r=>setTimeout(r,15)); }
      return { per, left:!!document.getElementById('drag-look'), banner:!!banner(), lines:window.__dragLines||null }; }""")
    P = r["per"]
    chk("six looks were sampled after their banner went off (%s)" % "".join(sorted(P)), "".join(sorted(P)) == "ABCDEF", r)
    chk("A is the Leaderboard with its blurs, B the Report a bug screen", P["A"]["board"] and P["A"]["blurs"] > 0 and P["B"]["bug"] and not P["B"]["board"], P)
    chk("C has no blur but the bar's (the bar's stays), D has no chat dock, E both", P["C"]["blurs"] == 0 and P["C"]["barBlur"] == P["A"]["barBlur"] != "none" and P["D"]["dock"] == "none" and P["A"]["dock"] != "none" and P["E"]["blurs"] == 0 and P["E"]["dock"] == "none", P)
    chk("F also hides the page", P["F"]["stage"] == "hidden" and P["E"]["stage"] == "visible", P)
    chk("it is all taken off at the end and each look's frame intervals were kept (%s lines)" % (len(r["lines"] or [])), not r["left"] and not r["banner"] and r["lines"] is not None and len(r["lines"]) == 6, r)
    br.close()
sys.exit(0 if g["ok"] else 1)
