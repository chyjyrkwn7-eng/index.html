"""Build 366: visiting the Leaderboard does not leave its whole list in memory. (a) No document "visibilitychange" listener is added per
visit (each held the visit's list: ~35MB a visit - the white screen and splash after a few dozen visits, e.g. in the speed test);
(b) the recorders' and the flip-book watcher's sets do not keep tiles that have left the page, after a few seconds.
Run:  python3 tools/check-b366.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
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
    pg.evaluate(FILL)
    pg.evaluate("()=>{ window.__vis=0; const o=document.addEventListener.bind(document); document.addEventListener=function(t,f,c){ if(t==='visibilitychange') window.__vis++; return o(t,f,c); }; }")
    pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); for(let i=0;i<6;i++){ showRankings(); await wait(700); showHome(); await wait(500); } }""")
    pg.wait_for_timeout(6000)
    r = pg.evaluate("""()=>{ let stale=0, held=0; charRecWaiters.forEach(s=>s.forEach(t=>{ held++; if(!t.isConnected) stale++; })); orbitRecWaiters.forEach(s=>s.forEach(t=>{ if(t!==true){ held++; if(!t.isConnected) stale++; } })); let ws=0; charFlipWatched.forEach(t=>{ if(!t.isConnected) ws++; });
      return { vis: window.__vis, stale, held, watchedStale: ws }; }""")
    chk("six Leaderboard visits add no document visibilitychange listener (%s)" % (r["vis"],), r["vis"] == 0, r)
    chk("the recorders' and watcher's sets keep no tile that has left the page (%s)" % (r,), r["stale"] == 0 and r["watchedStale"] == 0, r)
    # the rows far down are drawn when they are scrolled toward
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(3500)
    far0 = pg.evaluate("()=>[...document.querySelectorAll('.rank-rows .rank-row')].filter(r=>r.dataset.lazyArt).length")
    pg.evaluate("()=>window.scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(3000)
    last = pg.evaluate("()=>{ const rs=[...document.querySelectorAll('.rank-rows .rank-row')]; const v=rs.filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight&&b.bottom>0}); return { vis: v.length, bare: v.filter(r=>r.dataset.lazyArt).length }; }")
    chk("some far rows start bare (%s), and scrolled to they have their characters (%s)" % (far0, last), far0 >= 10 and last["vis"] >= 5 and last["bare"] == 0, [far0, last])
    br.close()
sys.exit(0 if g["ok"] else 1)
