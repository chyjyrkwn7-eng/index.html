"""Build 372: Profile's character and emblems are drawn AFTER the screen is up (artLater), not inside the tap - on his phone Profile's first
frame took 120-400ms, about 120ms of it this art. Right after showProfile the boxes are there (same size) but empty; once the screen has
settled the art is in, fully opaque, the character is live, and nothing moved.
Run:  python3 tools/check-b372.py   (--against: copy the old index.html and version.json over first)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
PROBE = """()=>{ const q=s=>document.querySelector(s); const av=q('.profile-hero-avatar'); const emb=q('.pf-goal-emb'); const rw=[...document.querySelectorAll('.pf-rw-art')];
  const r=av&&av.getBoundingClientRect(); return { av:!!av, avSvg:!!(av&&av.querySelector('svg.avatarchar-svg')), box:r?[Math.round(r.width),Math.round(r.height)]:null,
   emb:!!emb, embSvg:!!(emb&&emb.querySelector('svg')), rw:rw.length, rwFilled:rw.filter(a=>a.children.length).length,
   opacity:av&&av.firstElementChild?getComputedStyle(av.firstElementChild).opacity:null, plate:!!(av&&av.querySelector('.has-plate, svg.avatarchar-svg')) }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.wait_for_timeout(1500)
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(800)
    now = pg.evaluate("()=>{ showProfile(); return (" + PROBE + ")(); }")
    pg.wait_for_timeout(2200)
    late = pg.evaluate(PROBE)
    chk("right after the tap the boxes are in place but the art is not (character %s, emblem %s, reward art %s of %s)" % (now["avSvg"], now["embSvg"], now["rwFilled"], now["rw"]),
        now["av"] and now["box"][0] > 40 and not now["avSvg"] and (not now["emb"] or not now["embSvg"]) and now["rwFilled"] == 0, now)
    chk("once the screen has settled the art is all in and opaque (character %s, emblem %s, reward art %s of %s, opacity %s)" % (late["avSvg"], late["embSvg"], late["rwFilled"], late["rw"], late["opacity"]),
        late["avSvg"] and (not late["emb"] or late["embSvg"]) and late["rwFilled"] == late["rw"] and late["opacity"] == "1" and late["box"] == now["box"], {"now": now, "late": late})
    br.close()
sys.exit(0 if g["ok"] else 1)
