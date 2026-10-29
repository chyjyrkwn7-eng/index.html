"""Build 351: Leaderboard rows are built by the clock and rows below the screen are skipped by the browser; the tab's
character is its own layer; the speed test's passes name Home's and the Leaderboard's parts.
Run:  python3 tools/check-b351.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<60;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL)
    # a slow device: every row costs ~6ms, so the tap's own task must stop early and the rest follow on later frames
    r = pg.evaluate("""async ()=>{ const real = buildAvatarCharSVGSafe; window.buildAvatarCharSVGSafe = function(){ const t=performance.now(); while(performance.now()-t < 6){} return real.apply(this, arguments); };
      showRankings(); const first = document.querySelectorAll('.rank-rows .rank-row').length;
      await new Promise(r=>setTimeout(r, 2500)); const all = document.querySelectorAll('.rank-rows .rank-row').length; window.buildAvatarCharSVGSafe = real; return { first, all }; }""")
    chk("on a slow device the tap builds only a few rows (%s)" % (r,), 3 <= r["first"] <= 9, r)
    chk("and the rest of the list follows (%s)" % (r,), r["all"] >= 60, r)
    cv = pg.evaluate("()=>{ const r=document.querySelector('.rank-rows .rank-row'); return r ? getComputedStyle(r).contentVisibility : null; }")
    chk("rows below the screen are skipped by the browser (%s)" % cv, cv == "auto", cv)
    wc = pg.evaluate("()=>{ const e=document.querySelector('#bottomtab-profile .bottomtab-icon-avatar'); return e ? getComputedStyle(e).willChange : null; }")
    chk("the tab's character is its own layer (%s)" % wc, wc and "transform" in wc, wc)
    t = pg.evaluate("async ()=>(await runLagTest()).text")
    for v in ("base", "nocols", "noavw", "nohead", "nohero"):
        chk("the speed test has a [%s] pass for Home" % v, ("[" + v + "]home") in t, t[:160])
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
