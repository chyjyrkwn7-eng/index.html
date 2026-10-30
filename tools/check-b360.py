"""Build 360: a Leaderboard row that is off the screen skips its contents (content-visibility) and keeps its height, so
sitting on the Leaderboard is cheap to draw and a tap on the tab bar is not held up; the list is the same length before and
after scrolling; the screen's build runs from its timer, without waiting for a frame as well.
Run:  python3 tools/check-b360.py   (add --against old.html to run on another build)"""
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
    pg.evaluate(FILL); pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(4500)
    h0 = pg.evaluate("()=>document.documentElement.scrollHeight")
    pg.evaluate("()=>window.scrollTo(0,1500)"); pg.wait_for_timeout(900)
    r = pg.evaluate("""()=>{ const rs=[...document.querySelectorAll('.rank-row')]; const off=rs.filter(x=>x.classList.contains('is-offscreen'));
      return { total: rs.length, off: off.length, hidden: off.filter(x=>getComputedStyle(x).contentVisibility==='hidden').length, H: document.documentElement.scrollHeight,
        visBlank: rs.filter(x=>{const b=x.getBoundingClientRect(); return b.bottom>0&&b.top<innerHeight&&getComputedStyle(x).contentVisibility==='hidden'}).length }; }""")
    chk("rows off the screen skip their contents (%s)" % (r,), r["off"] >= 10 and r["hidden"] == r["off"], r)
    chk("none of the rows in view is skipped (%s)" % (r["visBlank"],), r["visBlank"] == 0, r)
    chk("the list is the same length scrolled as at the top (%s vs %s)" % (r["H"], h0), abs(r["H"] - h0) <= 2, r)
    # the build runs from the timer, not a frame: with frames held back, a tap still builds
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    b = pg.evaluate("""async()=>{ const bar=document.getElementById('bottomtabs'); const raf=window.requestAnimationFrame; window.requestAnimationFrame=()=>0;
      const el=document.getElementById('bottomtab-calendar'); const b0=bar._navBuilds||0; const t0=performance.now(); el.click(); let ms=-1;
      while(performance.now()-t0<900){ if((bar._navBuilds||0)>b0){ ms=performance.now()-t0; break; } await new Promise(r=>setTimeout(r,2)); } window.requestAnimationFrame=raf; return ms; }""")
    chk("a tab tap builds its screen from its timer within 100ms, with no frame callback (%s ms)" % (round(b),), 0 <= b <= 100, b)
    br.close()
sys.exit(0 if g["ok"] else 1)
