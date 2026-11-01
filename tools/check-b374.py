"""Build 374: Profile's character, rank emblem and reward art are in the screen the moment it is mounted again (build 372's fade-in is gone - "the fade in is
absolutely not it"). Right after showProfile (before any frame) they are all there, fully opaque, no inline opacity or transition.
Run:  python3 tools/check-b374.py   (--against: copy the old index.html and version.json over first)"""
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
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(800)
    r = pg.evaluate("""()=>{ showProfile(); const av=document.querySelector('.profile-hero-avatar'), emb=document.querySelector('.pf-goal-emb'), rw=[...document.querySelectorAll('.pf-rw-art')];
      const kid=av&&av.querySelector('svg.avatarchar-svg'); const span=kid&&kid.parentElement;
      return { avSvg:!!kid, embSvg:!!(emb&&emb.querySelector('svg')), rw:rw.length, rwFilled:rw.filter(a=>a.children.length).length,
        inlineOpacity:span?span.style.opacity:null, inlineTransition:span?span.style.transition:null }; }""")
    chk("the character, emblem and reward art are in as soon as the screen is mounted (%s)" % (r,), r["avSvg"] and r["embSvg"] and r["rw"] > 0 and r["rwFilled"] == r["rw"] and r["inlineOpacity"] in ("", None) and r["inlineTransition"] in ("", None), r)
    br.close()
sys.exit(0 if g["ok"] else 1)
