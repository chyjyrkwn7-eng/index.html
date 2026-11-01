"""Build 380: every loop in the app is a window-sized layer.
(1) by default (html.loops-paint) every loop on Home, the Leaderboard and the tab bar steps by left/top (rk-pos-*), no loop's sheet is a
layer of its own (will-change auto on every sheet) and every window is (will-change transform);
(2) each loop shows the same frame as the old way at the same time (left/top here = the transform offset with the class taken away);
(3) the watchdog: two counts in a row with most frames slow put the loops back on layers, write that down for this build, and "Send tab
timings" says so; (4) the next launch of this build starts on layers, a launch of another build on windows;
(5) the Leaderboard speed test's looks are base, layers, noloops, norows;
(6) a screen that takes 800ms to build no longer holds the glass up for it: the landing (its turn to grey) is planned at the release,
within 400ms of it.
Run:  python3 tools/check-b380.py   (--against: copy the old index.html and version.json over first)"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const ids=['ninja','wizard','ghost']; const rows=[]; for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%3]}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
LOOPS = "'#stage .char-flip-play img, #stage .rk-frame img, .bottomtabs .char-flip-play img'"
# rows skipped by the browser (off screen) have no transform computed the old way, so the frame match reads the loops on screen
LOOPS_ON = "[...document.querySelectorAll(%s)].filter(i=>!i.closest('.is-offscreen'))" % LOOPS
STATE = """()=>{ const a=[...document.querySelectorAll(%s)]; return { n:a.length, pos:a.filter(i=>getComputedStyle(i).animationName.startsWith('rk-pos')).length,
  sheetLayers:a.filter(i=>getComputedStyle(i).willChange.includes('transform')).length, winLayers:a.filter(i=>getComputedStyle(i.parentElement).willChange.includes('transform')).length,
  paint: document.documentElement.classList.contains('loops-paint') }; }""" % LOOPS
SAME = """async(T)=>{ const a=%s; const seek=()=>document.getAnimations().forEach(x=>{ const el=x.effect&&x.effect.target; if(el && a.includes(el)){ x.pause(); x.currentTime=T; } });
  seek(); await new Promise(r=>setTimeout(r,150)); const p=a.map(i=>[parseFloat(getComputedStyle(i).left)||0, parseFloat(getComputedStyle(i).top)||0]);
  document.documentElement.classList.remove('loops-paint'); await new Promise(r=>setTimeout(r,250)); seek(); await new Promise(r=>setTimeout(r,150));
  const q=a.map(i=>{ const m=new DOMMatrixReadOnly(getComputedStyle(i).transform); return [m.e, m.f]; });
  document.documentElement.classList.add('loops-paint'); document.getAnimations().forEach(x=>{ try{ x.play(); }catch(e){} });
  return { n:a.length, off:p.map((v,k)=>Math.max(Math.abs(v[0]-q[k][0]), Math.abs(v[1]-q[k][1]))).filter(d=>d>0.6).length, moved:p.filter(v=>v[0]||v[1]).length }; }""" % LOOPS_ON
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL); pg.evaluate("()=>showRankings()")
    t0 = time.time()
    while time.time() - t0 < 120:
        pg.wait_for_timeout(1500)
        k = pg.evaluate("()=>{ const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;}); return [vis.length, vis.filter(r=>r.querySelector('.char-flip-play')).length, vis.filter(r=>r.querySelector('.rk-frame img')).length]; }")
        if k[1] >= k[0] - 1 and k[2] >= k[0] - 2: break
    pg.wait_for_timeout(1500)
    board = pg.evaluate(STATE); bsame = pg.evaluate(SAME, 2345)
    pg.evaluate("()=>showHome()")
    t0 = time.time()
    while time.time() - t0 < 60:
        pg.wait_for_timeout(1500)
        if pg.evaluate("()=>document.querySelectorAll('.screen-home-actual .rk-frame img').length") >= 3: break
    pg.wait_for_timeout(1500)
    home = pg.evaluate(STATE); hsame = pg.evaluate(SAME, 4111)
    chk("every loop is a window-sized layer: board %s, Home %s" % (board, home),
        board["paint"] and board["n"] >= 20 and board["pos"] == board["n"] and board["sheetLayers"] == 0 and board["winLayers"] == board["n"]
        and home["n"] >= 3 and home["pos"] == home["n"] and home["sheetLayers"] == 0 and home["winLayers"] == home["n"], [board, home])
    chk("each loop shows the old way's frame at the same time (board %s, Home %s: loops off by more than half a px)" % (bsame, hsame),
        bsame["n"] >= 15 and bsame["off"] == 0 and bsame["moved"] >= 10 and hsame["n"] >= 3 and hsame["off"] == 0, [bsame, hsame])
    # (3) the watchdog
    wd = pg.evaluate("""async()=>{ if(typeof loopsWatchTick!=='function') return null; const wait=ms=>new Promise(r=>setTimeout(r,ms)); let on=true;
      const jank=()=>{ const t=performance.now(); while(performance.now()-t<40){} if(on) requestAnimationFrame(jank); }; requestAnimationFrame(jank); await wait(600);
      while(loopsWatch.busy) await wait(100);
      loopsWatchTick(true); await wait(2000); while(loopsWatch.busy) await wait(100); const after1=document.documentElement.classList.contains('loops-paint');
      loopsWatchTick(true); await wait(2000); while(loopsWatch.busy) await wait(100); on=false; await wait(200);
      return { after1, after2: document.documentElement.classList.contains('loops-paint'), key: localStorage.getItem('class26e.loopmode'), report: tabPerfText().slice(0, 300) }; }""")
    chk("two slow counts put the loops back on layers for this build, and the report says so (%s)" % (wd,),
        wd and wd["after1"] is True and wd["after2"] is False and (wd["key"] or "").startswith("layers|") and (wd["key"] or "").endswith("|2026-11-01-380") and "loops layers" in wd["report"], wd)
    # (4) next launch
    pg.reload(); pg.wait_for_timeout(3500)
    same_build = pg.evaluate("()=>document.documentElement.classList.contains('loops-paint')")
    pg.evaluate("()=>localStorage.setItem('class26e.loopmode', 'layers|n90/s60|2026-01-01-000')"); pg.reload(); pg.wait_for_timeout(3500)
    other_build = pg.evaluate("()=>document.documentElement.classList.contains('loops-paint')")
    chk("this build relaunches on layers (%s), another build's note does not hold (windows: %s)" % (not same_build, other_build), same_build is False and other_build is True, [same_build, other_build])
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    # (5)
    looks = pg.evaluate("()=>typeof BOARD_TEST_LOOKS!=='undefined' ? BOARD_TEST_LOOKS.map(l=>l[0]+':'+l[2]) : null")
    chk("the speed test's looks are base, layers, noloops, norows (%s)" % (looks,), looks == ["base:", "layers:-loops-paint", "noloops:", "norows:"], looks)
    # (6) the landing is planned at the release: the glass's fade to grey is on its track the moment the finger lifts, whatever the screen
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const real=window.showProfile; let builtAt=0;
      window.showProfile=function(){ const t=performance.now(); while(performance.now()-t<800){} const r=real.apply(this,arguments); builtAt=performance.now(); return r; };
      const glass=document.querySelector('#bottomtabs-lens .tab-lens-glass'), tab=document.getElementById('bottomtab-profile');
      const b=tab.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:72,isPrimary:true,clientX:x,clientY:y});
      tab.dispatchEvent(mk('pointerdown')); await wait(80); const rel=performance.now(); tab.dispatchEvent(mk('pointerup')); tab.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
      const plan=()=>{ const a=glass.getAnimations().find(a=>{ const k=a.effect.getKeyframes(); return k.length && k.some(f=>'opacity' in f); }); if(!a) return null;
        const k=a.effect.getKeyframes(), D=a.effect.getTiming().duration; const drop=k.findIndex((f,n)=>n>0 && parseFloat(f.opacity)<0.9 && parseFloat(k[n-1].opacity)>=0.9);
        return drop<0 ? null : Math.round(k[drop].computedOffset*D - ((performance.now()-rel) - (a.currentTime||0))); };
      const atRelease=plan(); await wait(30); const soon=plan();
      await wait(2400); window.showProfile=real;
      return { greyPlannedAt: atRelease, greyPlannedSoon: soon, builtAfterRelease: Math.round(builtAt-rel), onProfile: !!document.querySelector('.screen-profile'), lensGone: getComputedStyle(document.getElementById('bottomtabs-lens')).opacity==='0' }; }""")
    chk("the landing is planned at the release (greys %sms after it), not when the 800ms screen is done (%sms)" % (r["greyPlannedAt"], r["builtAfterRelease"]),
        r["onProfile"] and r["lensGone"] and r["greyPlannedAt"] is not None and 0 <= r["greyPlannedAt"] <= 400 and r["builtAfterRelease"] >= 750, r)
    br.close()
sys.exit(0 if g["ok"] else 1)
