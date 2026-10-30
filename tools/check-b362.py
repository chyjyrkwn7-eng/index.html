"""Build 362: the Leaderboard is first drawn with only the rows in view - the rest are born skipped (.is-offscreen) with a row's
height held - and the tab speed test's variants are the ones that say what the first draw is spent on ([g:nobody] [g:noart]
[g:nohero] [g:bare], three rounds each, medians).
Run:  python3 tools/check-b362.py   (add --against old.html to run on another build)"""
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
    # the rows as built, before any observer has reported: a probe at the first frame after showRankings
    r = pg.evaluate("""async()=>{ showRankings(); const rs=[...document.querySelectorAll('.rank-row:not(.rank-row-head):not(.rank-row-skel)')];
      const born = rs.map(x=>x.classList.contains('is-offscreen')); const firstOff = born.indexOf(true);
      const inView = rs.filter(x=>{const b=x.getBoundingClientRect(); return b.top < innerHeight-80}).length;
      const viewSkipped = rs.filter(x=>{const b=x.getBoundingClientRect(); return b.top < innerHeight-80 && x.classList.contains('is-offscreen')}).length;
      return { rows: rs.length, firstOff, inView, viewSkipped, skipped: born.filter(Boolean).length, skippedHidden: rs.filter(x=>x.classList.contains('is-offscreen') && getComputedStyle(x).contentVisibility==='hidden').length }; }""")
    chk("rows past the view are born skipped, the ones in view are not (%s)" % (r,), r["rows"] >= 30 and r["firstOff"] >= r["inView"] and r["viewSkipped"] == 0 and r["skipped"] >= 15 and r["skippedHidden"] == r["skipped"], r)
    pg.wait_for_timeout(3000)
    r2 = pg.evaluate("()=>{ const rs=[...document.querySelectorAll('.rank-row')]; const vis=rs.filter(x=>{const b=x.getBoundingClientRect(); return b.bottom>0&&b.top<innerHeight}); return { vis: vis.length, visSkipped: vis.filter(x=>getComputedStyle(x).contentVisibility==='hidden').length, H: document.documentElement.scrollHeight }; }")
    h0 = r2["H"]
    pg.evaluate("()=>window.scrollTo(0,1500)"); pg.wait_for_timeout(900)
    r3 = pg.evaluate("()=>{ const rs=[...document.querySelectorAll('.rank-row')]; const vis=rs.filter(x=>{const b=x.getBoundingClientRect(); return b.bottom>0&&b.top<innerHeight}); return { vis: vis.length, visSkipped: vis.filter(x=>getComputedStyle(x).contentVisibility==='hidden').length, H: document.documentElement.scrollHeight }; }")
    chk("after the observer reports, nothing in view is skipped, at the top or scrolled (%s %s)" % (r2, r3), r2["visSkipped"] == 0 and r3["visSkipped"] == 0, [r2, r3])
    chk("the list is about the same length scrolled as at the top (%s vs %s)" % (r3["H"], h0), abs(r3["H"] - h0) <= 60, [h0, r3["H"]])
    text = pg.evaluate("async()=>{ const x=await runLagTest(()=>{}); return x.text; }")
    parts = [p for p in text.split(" | ") if p.startswith("[g:")]
    names = [p[3:p.index("]")] for p in parts]
    chk("the speed test's variants are base, nobody, noart, nohero, bare (%s)" % (names,), names == ["base", "nobody", "noart", "nohero", "bare"], text)
    # the platter's inline opacity goes 0 -> 1 -> "" when the glass hands over, never 0 -> "" (a dip, then a .2s ramp)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    seq = pg.evaluate("""async()=>{ const s=document.getElementById('bottomtabs-slider'); const seq=[];
      const mo=new MutationObserver(()=>{ seq.push(s.style.opacity); }); mo.observe(s,{attributes:true,attributeFilter:['style']});
      const el=document.getElementById('bottomtab-profile'); const b=el.getBoundingClientRect(); const x=b.left+b.width/2,y=b.top+b.height/2;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:52,isPrimary:true,clientX:x,clientY:y});
      el.dispatchEvent(mk('pointerdown')); await new Promise(r=>setTimeout(r,60)); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
      await new Promise(r=>setTimeout(r,1800)); mo.disconnect(); return seq; }""")
    i1 = max([i for i, v in enumerate(seq) if v == "0"] or [-1]); tail = seq[i1 + 1:]
    chk("the platter's opacity is held at 1 before it is released (%s)" % (seq,), tail[:1] == ["1"] and "" in tail[1:], seq)
    br.close()
sys.exit(0 if g["ok"] else 1)
