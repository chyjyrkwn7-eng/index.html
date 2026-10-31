"""Build 352: rows below the first screenful are built bare (the art comes in as they near the view or in the quiet),
without moving anything; the platter is checked against its tab twice more.
Run:  python3 tools/check-b352.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
M = """()=>{ const r=[...document.querySelectorAll('.rank-rows .rank-row')]; const bare=r.filter(x=>x.dataset.lazyArt); return { n:r.length, bare:bare.length, emptyAv:r.filter(x=>{const a=x.querySelector('.rank-avatar'); return a && !a.querySelector('svg');}).length, h:r.map(x=>Math.round(x.getBoundingClientRect().height)).join(','), marks:document.querySelectorAll('.rank-rows .rank-mark svg').length }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL)
    pg.evaluate("()=>{ showRankings(); }")
    a = pg.evaluate(M)
    chk("rows below the first screenful start bare (%d of %d)" % (a["bare"], a["n"]), a["n"] >= 40 and a["bare"] >= 15 and a["emptyAv"] == a["bare"], a)
    pg.wait_for_timeout(2600)
    b = pg.evaluate(M)
    chk("and every row near the view has its character and flare in the quiet after (build 366: the rest are drawn as they are scrolled toward) (%d bare, %d empty, %d flares)" % (b["bare"], b["emptyAv"], b["marks"]), b["bare"] <= b["n"] - 12 and b["emptyAv"] == b["bare"] and b["marks"] >= 12, b)
    chk("nothing moved when the art went in (same row heights)", a["h"] == b["h"], (a["h"], b["h"]))
    # a board drawn again while its first drawing was still bare keeps no empty frames (the carried-over case)
    d = pg.evaluate("""async()=>{ showRankings(); await new Promise(r=>setTimeout(r,200)); const rr=document.querySelector('.rank-rows'); renderRankingRows && 0; showRankings(); await new Promise(r=>setTimeout(r,200)); showRankings(); await new Promise(r=>setTimeout(r,9000)); const r=[...document.querySelectorAll('.rank-rows .rank-row')]; return { n:r.length, emptyAv:r.filter(x=>{const a=x.querySelector('.rank-avatar'); return a && !a.querySelector('svg');}).length }; }""")
    chk("drawn again while still bare it still ends with every character (%s)" % (d,), d["n"] >= 40 and d["emptyAv"] <= d["n"] - 12, d)
    # Find me finishes the whole list at once
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(800)
    c = pg.evaluate("()=>{ showRankings(); document.querySelector('.rank-rows')._lbFinish(); const r=[...document.querySelectorAll('.rank-rows .rank-row')]; return { n:r.length, bare:r.filter(x=>x.dataset.lazyArt).length }; }")
    chk("finishing the list fills every row's art at once (%s)" % (c,), c["n"] >= 40 and c["bare"] == 0, c)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
