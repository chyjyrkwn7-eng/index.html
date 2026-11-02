"""Build 376: (1) while a finger slides across the tab bar, the animations BEHIND the bar are paused and those higher up the screen keep
running; all of them run again once it lets go. (2) A slide that lands on another tab tries its haptic tick again on the touch's own end.
(3) The board's saved loops are read back after launch even while the person keeps touching the screen (no wait for a quiet two seconds).
(4) The rows' art queue holds off until the glass has landed (still nothing filled 650ms after the board is opened).
Run:  python3 tools/check-b376.py   (--against: copy the old index.html and version.json over first)"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const ids=['ninja','wizard','ghost']; const rows=[]; for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%3]}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL); pg.wait_for_timeout(500)
    # (4) first: a fresh board, nothing recorded yet
    # a finger holds the bar (the glass is up) while the board comes in: nothing fills until it has landed, then it does
    q = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const tab=document.getElementById('bottomtab-rewards'); const b=tab.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:94,isPrimary:true,clientX:x,clientY:y});
      tab.dispatchEvent(mk('pointerdown')); showRankings(); await wait(900);
      const body=()=>[...document.querySelectorAll('.rank-rows > .rank-row')].filter(r=>!r.classList.contains('rank-row-head'));
      const held={ up: !!document.querySelector('#bottomtabs-lens.is-up'), rows: body().length, filled: body().filter(r=>!r.dataset.lazyArt).length };
      tab.dispatchEvent(mk('pointerup')); await wait(1400);
      return { held, after: body().filter(r=>!r.dataset.lazyArt).length }; }""")
    chk("while the glass is up the board's art queue waits (%s of %s rows filled at 900ms), and fills once it has landed (%s)" % (q["held"]["filled"], q["held"]["rows"], q["after"]),
        q["held"]["up"] and q["held"]["rows"] >= 20 and q["held"]["filled"] == 0 and q["after"] > 0, q)
    # let the board record its loops (as a visit does), so there is motion behind the bar and loops to read back after a relaunch
    PROBE = "()=>{ const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;}); return [vis.length, vis.filter(r=>r.querySelector('.char-flip-play')).length]; }"
    t0 = time.time()
    while time.time() - t0 < 90:
        pg.wait_for_timeout(1000)
        n, k = pg.evaluate(PROBE)
        if k >= n - 1: break
    pg.evaluate("()=>{ window.scrollTo(0, 260); }"); pg.wait_for_timeout(1500)
    # (1) a slide on the board. A loop is read where its WINDOW is (380: the sheet inside moves by left/top, so its own box wanders into and
    # out of the bar's band while what is seen stays put), and a row the page has marked off screen is left out (its loop is paused by CSS)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const st=document.getElementById('stage'), bar=document.querySelector('.bottomtabs');
      const br=bar.getBoundingClientRect(); const where=a=>{ const t=a.effect&&a.effect.target; if(!t||!t.getBoundingClientRect) return null; if(t.closest&&t.closest('.is-offscreen')) return null; const r=((t.closest&&t.closest('.rk-frame, .char-flip-play'))||t).getBoundingClientRect(); if(!r.width) return null; return (r.bottom>br.top-24 && r.top<br.bottom+8) ? 'under' : (r.bottom < br.top-60 ? 'above' : null); };
      const count=()=>{ const o={underRun:0, underPaused:0, aboveRun:0, abovePaused:0}; st.getAnimations({subtree:true}).forEach(a=>{ const w=where(a); if(!w) return; o[w+(a.playState==='running'?'Run':'Paused')]++; }); return o; };
      const before=count();
      const nav=document.querySelector('.bottomtabs-navrow'), tab=document.getElementById('bottomtab-rewards'); const b=tab.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const mk=(t,xx)=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:91,isPrimary:true,clientX:xx,clientY:y});
      tab.dispatchEvent(mk('pointerdown',x)); await wait(60);
      for(let i=1;i<=8;i++){ nav.dispatchEvent(mk('pointermove',x+i*6)); await wait(16); }
      const during=count();
      for(let i=7;i>=0;i--){ nav.dispatchEvent(mk('pointermove',x+i*6)); await wait(16); }
      nav.dispatchEvent(mk('pointerup',x)); await wait(900);
      return { before, during, after: count() }; }""")
    d = r["during"]
    chk("mid-slide, what is behind the bar is paused (%s paused, %s running there) and what is above it runs (%s running)" % (d["underPaused"], d["underRun"], d["aboveRun"]),
        r["before"]["underRun"] > 0 and d["underPaused"] > 0 and d["underRun"] == 0 and d["aboveRun"] > 0 and d["abovePaused"] == 0, r)
    chk("after the slide everything behind the bar runs again (%s)" % (r["after"],), r["after"]["underPaused"] == 0 and r["after"]["underRun"] > 0, r)
    # (2) a slide's landing: the haptic is tried again on touchend
    h = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); showHome(); await wait(2500); const calls=[]; const real=NovaSound.haptic; NovaSound.haptic=(k,f)=>{ calls.push([k,!!f]); };
      const nav=document.querySelector('.bottomtabs-navrow'), a=document.getElementById('bottomtab-home'), c=document.getElementById('bottomtab-calendar');
      const ra=a.getBoundingClientRect(), rc=c.getBoundingClientRect(), y=ra.top+ra.height/2, x0=ra.left+ra.width/2, x1=rc.left+rc.width/2;
      const mk=(t,xx)=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:92,isPrimary:true,clientX:xx,clientY:y});
      a.dispatchEvent(mk('pointerdown',x0)); await wait(60); for(let i=1;i<=20;i++){ nav.dispatchEvent(mk('pointermove',x0+(x1-x0)*i/20)); await wait(16); }
      nav.dispatchEvent(mk('pointerup',x1)); nav.dispatchEvent(new Event('touchend',{bubbles:true})); await wait(300); NovaSound.haptic=real;
      return { calls, onCal: !!document.querySelector('.screen-calendar-tab, .screen-calendar') }; }""")
    chk("a slide that lands on another tab tries its tick again on the touch's end (%s)" % (h,), any(c[1] for c in h["calls"]), h)
    # (3) saved loops read back while the person keeps touching
    pg.reload(); pg.wait_for_timeout(2500)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL)
    pg.evaluate("()=>{ if(typeof lbArtPreloadSoon==='function') lbArtPreloadSoon(); window.__poke=setInterval(()=>{ window.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})); }, 400); }")
    pg.wait_for_timeout(7000)
    n = pg.evaluate("()=>{ clearInterval(window.__poke); return typeof charAnimReady!=='undefined' ? charAnimReady.size : -1; }")
    chk("after a relaunch the saved loops are read back while the screen is still being touched (%s in memory)" % n, n >= 2, n)
    br.close()
sys.exit(0 if g["ok"] else 1)
