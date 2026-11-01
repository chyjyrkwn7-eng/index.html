"""Build 375: (1) THE GLASS LANDS AFTER THE NEW SCREEN HAS BEEN DRAWN. A tap whose screen takes a long time to draw (a 350ms build,
as on the phone) keeps its lens up, at full height, until the frame after the one that drew the screen, and only then shrinks into
the platter - it never shrinks while the screen is being drawn. A tap on the tab already showing lands as before.
(3) a slide across the bar does not stop the page's animations; (4) a slide let go over the tab already lit leaves a scrolled screen where it
was; (5) a Leaderboard that has been left is let go (six quick visits, then 7s: none of the six boards is still in memory).
(2) THE LEADERBOARD ARRIVES WITH ITS ART. Once a board's character loops and flare loops have been made (and its row geometry seen
once), the next board - and the first board after a relaunch, once the loops have been read back - is built with every row's loop
playing and its flare's loop on, in the same task that mounts it: no bare discs, no empty rings, nothing drawn later.
Run:  python3 tools/check-b375.py   (--against: copy the old index.html and version.json over first)"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const ids=['ninja','wizard','ghost']; const rows=[]; for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%3]}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
PROBE = """()=>{ const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;});
  return { n:vis.length, loop:vis.filter(r=>r.querySelector('.rank-avatar .char-flip-play')).length, disc:vis.filter(r=>r.querySelector('.rank-avatar-wrap[data-lazy-av]:not([data-flip-pre])')).length,
   flare:vis.filter(r=>r.querySelector('.rank-mark > .cosmic-rank-anim')).length, ring:vis.filter(r=>r.querySelector('.rank-mark.is-lazy')).length }; }"""
TAP = """async()=>{
  const wait=ms=>new Promise(r=>setTimeout(r,ms));
  const real=window.showProfile; let builtAt=0;
  window.showProfile=function(){ const t=performance.now(); while(performance.now()-t<350){} const r=real.apply(this,arguments); builtAt=performance.now(); return r; };
  const body=document.querySelector('#bottomtabs-lens .tab-lens-body'), tab=document.getElementById('bottomtab-profile');
  const b=tab.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
  const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:71,isPrimary:true,clientX:x,clientY:y});
  const sy=()=>{ const m=getComputedStyle(body).transform; if(!m||m==='none') return 0; const v=m.slice(m.indexOf('(')+1,-1).split(',').map(Number); return v.length===6?v[3]:v[5]; };
  const samples=[]; let on=true, frameAfterBuild=0, framesSinceBuild=0;
  const tick=()=>{ const t=performance.now(); if(builtAt && t>builtAt){ framesSinceBuild++; if(framesSinceBuild===2) frameAfterBuild=t; } samples.push([t, sy(), getComputedStyle(document.getElementById('bottomtabs-lens')).opacity]); if(on) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  const t0=performance.now();
  tab.dispatchEvent(mk('pointerdown')); await wait(80); tab.dispatchEvent(mk('pointerup')); tab.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
  await wait(1600); on=false; window.showProfile=real;
  const up=samples.filter(s=>s[0]>t0 && s[2]>0.5 && s[1]>0);
  const top=Math.max(...up.map(s=>s[1]));
  /* the first frame the lens is clearly shorter than it was held - the shrink has begun */
  const shrinkAt=(up.find(s=>s[0]>t0+100 && s[1]<top*0.93)||[0])[0];
  return { builtAt:Math.round(builtAt-t0), frameAfterBuild:Math.round(frameAfterBuild-t0), shrinkAt:shrinkAt?Math.round(shrinkAt-t0):null, onProfile:!!document.querySelector('.screen-profile'), lensGone:getComputedStyle(document.getElementById('bottomtabs-lens')).opacity==='0' };
}"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    r = pg.evaluate(TAP)
    chk("a slow screen (built %sms after the tap, drawn by %sms): the glass starts to shrink only after that (%sms)" % (r["builtAt"], r["frameAfterBuild"], r["shrinkAt"]),
        r["onProfile"] and r["shrinkAt"] is not None and r["frameAfterBuild"] > 0 and r["shrinkAt"] >= r["frameAfterBuild"] and r["lensGone"], r)
    # (2) the board
    pg.evaluate(FILL); pg.wait_for_timeout(500)
    pg.evaluate("()=>showRankings()")
    t0 = time.time(); p = None
    while time.time() - t0 < 90:
        pg.wait_for_timeout(1000)
        p = pg.evaluate(PROBE)
        if p["loop"] >= p["n"] - 1 and p["flare"] >= p["n"] - 1: break
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1200)
    again = pg.evaluate("()=>{ showRankings(); return (" + PROBE + ")(); }")
    chk("the next board is built with its loops and flares on, in the mounting task (%s of %s rows looping, %s flares, %s discs, %s rings)" % (again["loop"], again["n"], again["flare"], again["disc"], again["ring"]),
        again["n"] >= 6 and again["loop"] >= again["n"] - 1 and again["flare"] >= again["n"] - 1 and again["disc"] <= 1 and again["ring"] <= 1, {"settled": p, "again": again})
    pg.reload(); pg.wait_for_timeout(2500)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL)
    pg.evaluate("()=>{ if(typeof lbArtPreloadSoon==='function') lbArtPreloadSoon(); }")
    pg.wait_for_timeout(9000)
    cold = pg.evaluate("()=>{ showRankings(); return (" + PROBE + ")(); }")
    chk("after a relaunch the first board is built the same way once the saved loops are read back (%s of %s looping, %s discs)" % (cold["loop"], cold["n"], cold["disc"]),
        cold["n"] >= 6 and cold["loop"] >= cold["n"] - 1 and cold["flare"] >= cold["n"] - 1 and cold["disc"] <= 1, cold)
    # (3) and (4): on a scrolled board, a slide out and back to the lit tab
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); window.scrollTo(0,500); await wait(400); const y0=window.scrollY;
      const st=document.getElementById('stage'); const run=()=>st.getAnimations({subtree:true}).filter(a=>a.playState==='running').length;
      const nav=document.querySelector('.bottomtabs-navrow'), tab=document.getElementById('bottomtab-rewards'); const b=tab.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const mk=(t,xx)=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:83,isPrimary:true,clientX:xx,clientY:y});
      const before=run(); tab.dispatchEvent(mk('pointerdown',x)); await wait(60);
      for(let i=1;i<=10;i++){ nav.dispatchEvent(mk('pointermove',x+i*6)); await wait(16); }
      const during=run();
      for(let i=9;i>=0;i--){ nav.dispatchEvent(mk('pointermove',x+i*6)); await wait(16); }
      nav.dispatchEvent(mk('pointerup',x)); await wait(1200);
      return { y0, y1: Math.round(window.scrollY), before, during, onBoard: !!document.querySelector('.screen-rankings') }; }""")
    chk("the page goes on moving while a finger slides across the bar (%s animations running, %s before)" % (r["during"], r["before"]), r["before"] > 0 and r["during"] >= 0.8 * r["before"], r)
    chk("let go over the tab already lit, the board stays scrolled where it was (%s -> %s)" % (r["y0"], r["y1"]), r["y0"] >= 400 and abs(r["y1"] - r["y0"]) < 30 and r["onBoard"], r)
    # (5) boards that have been left are let go
    pg.evaluate("()=>{ window.__wrs=[]; }")
    for k in range(6):
        pg.evaluate("()=>{ showRankings(); __wrs.push(new WeakRef(document.querySelector('.rank-rows'))); }"); pg.wait_for_timeout(1300)
        pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(1300)
    pg.wait_for_timeout(7000)
    cdp = ctx.new_cdp_session(pg); cdp.send("HeapProfiler.collectGarbage"); pg.wait_for_timeout(300); cdp.send("HeapProfiler.collectGarbage")
    alive = pg.evaluate("()=>__wrs.map(w=>!!w.deref())")
    chk("six Leaderboards visited and left: none still held 7s later (%s)" % (alive,), not any(alive), alive)
    br.close()
sys.exit(0 if g["ok"] else 1)
