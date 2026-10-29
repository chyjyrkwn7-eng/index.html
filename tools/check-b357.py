"""Build 357: the Leaderboard's whole list is there in the tap's own task and cheap (no character or flare built in it),
the art follows from the queue nearest the view first.   Run:  python3 tools/check-b357.py"""
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
    pg.evaluate(FILL); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
    r = pg.evaluate("""async()=>{ const real = buildAvatarCharSVGSafe; window.buildAvatarCharSVGSafe = function(){ const t=performance.now(); while(performance.now()-t < 6){} return real.apply(this, arguments); };
      const t0 = performance.now(); showRankings(); const took = performance.now() - t0;
      const rows=()=>[...document.querySelectorAll('.rank-rows .rank-row')].filter(x=>x.querySelector('.rank-avatar'));
      const out = { took: Math.round(took), n: rows().length, svgNow: document.querySelectorAll('.rank-rows .rank-avatar svg').length };
      await new Promise(r=>setTimeout(r, 600));
      const visible = rows().filter(x=>x.getBoundingClientRect().top < innerHeight - 90);
      out.visible = visible.length; out.visibleBare = visible.filter(x=>!x.querySelector('.rank-avatar svg')).length;
      window.buildAvatarCharSVGSafe = real; return out; }""")
    chk("the tap builds the whole list in a short task, even with each character costing 6ms (%s)" % (r,), r["n"] >= 40 and r["took"] <= 70, r)
    chk("without building any character in it (%s)" % (r["svgNow"],), r["svgNow"] <= 3, r)
    chk("and the screenful has its characters by 0.6s (%s of %s bare)" % (r["visibleBare"], r["visible"]), r["visibleBare"] == 0, r)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
