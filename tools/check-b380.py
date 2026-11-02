"""Build 380: every loop in the app is a window-sized layer.
(1) by default (html.loops-paint) every loop on Home, the Leaderboard and the tab bar steps by left/top (rk-pos-*), no loop's sheet is a
layer of its own (will-change auto on every sheet) and every window is (will-change transform);
(2) each loop shows the same frame as the old way at the same time (left/top here = the transform offset with the class taken away);
(3) the watchdog: two counts in a row with most frames slow put the loops back on layers, write that down for this build, and "Send tab
timings" says so; (4) the next launch of this build starts on layers, a launch of another build on windows;
(5) the Leaderboard speed test's looks are base, layers, noloops, norows;
(6) a screen that takes 800ms to build no longer holds the glass up for it: the landing (its turn to grey) is planned at the release,
within 400ms of it.
With the iPhone layer on (an iPhone's user agent: every control carries a native haptic switch):
(7) a tab tap that leaves its switch focused is not taken for typing - nothing focused is blurred at the next press or at the screen's mount;
(8) the switches of a new screen go in after the glass has landed (not inside the settle window) and all in one pass;
(11) a slide only starts on the lit tab: a press on another tab that slides on to a third opens neither (back home), let go on the
pressed tab it opens it, and a slide from the lit tab still lands where it is let go;
(12) on a test's results, taps that keep coming never press a button that rises under them (the guard restarts with each refused tap),
(19) nor does a tap the page gets late (held behind 900ms of work: it counts from when it happened, not when it arrived),
and a tap after a pause does; (13) a tap finishes the whole box that is coming in (the grade lands on its number at once) and the next
box comes in by itself;
(14) the grade's count does not sit on the number before the grade: on a 100 the 99 shows for under 650ms (it was ~1.2s), on an 80 the 79
the same; (15) a retake's card says what it was and how it went ("Retake of missed questions" / "All 3 answered correctly" or "2 of 4
answered correctly" with "2 still to review" under it);
(16) the badge case: once the Badges tab has been up a few seconds, a finger on a found badge costs next to nothing (its big face is already
made) and the lift shows one face from its first frame to its last; (17) the badge-unlock coin: once warmed, every one of its pictures is
decoded the moment it is built (none come in after it is up); (18) the badge put back after a rub is one finished picture from its first frame in the slot (no draft, no
second render once measured);
(20) the daily question's XP pop-up is Home's banner glass, as a message or friend request is, and what flies to Profile has no blur;
(21) Review's Starred pill has Select all's glass and rim, a plain count, and its star is the starred question's own gold; (22) with
nothing starred, a tap on it says so at the top (a banner), not in a toast at the bottom;
(23) a switch tapped sets off as the finger lifts, not when the flip arrives (on an iPhone the native switch's change comes later -
here 150ms later), and a tap whose flip never comes glides back;
(24) on a test, the chat button and Pause are the tab bar's own glass (body, rim, blur, shadow); (25) Next question comes up 2rem under
the answers when they leave room (as on a phone, no keys line), and at the bottom, where it was, when the question fills the screen;
(26) Pause is one card on the screen's middle with Resume across it and Save and exit and Quit test side by side in one black, and
Keep going lands where Resume was; (27) Home's daily question and class button are the rank bubbles' glass (their body and rim,
no blur) and the class mark is in its own colours; (28) closing the class list sends each bubble back into the class button;
(29) the Leaderboard tab's trophy is one piece; (30) a lit Silver flare is not the grey a locked flare is; (31) a secret flare has
a glint, the light pooled at its foot and a rim;
(33) the time limit runs 1 to 120 minutes and Max sets 120; (34) letting go of All or Max, the fill that lights the button carries
the word in dark, so the word reads the whole way through;
(10) at most 14 character sheets keep their decoded picture (the 14 used most lately), however many are ready;
(9) a board's flares are put on the loop clock about once each (a flare replaced when its row's art comes in counts again), not again at
every art-queue step or at the row observer's first report.
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
    # (11) a slide starts only on the lit tab
    cdp = ctx.new_cdp_session(pg); cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
    def cen(i): return pg.evaluate("(id)=>{const b=document.getElementById(id).getBoundingClientRect(); return [b.left+b.width/2,b.top+b.height/2];}", i)
    def slide(a, b, steps=20):
        x0, y = cen(a); x1, _ = cen(b)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]}); pg.wait_for_timeout(100)
        for k in range(1, steps + 1):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * k / steps, "y": y}]}); pg.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); pg.wait_for_timeout(1500)
    lit = lambda: pg.evaluate("()=>{ const a=document.querySelector('.bottomtab.active'); return a && a.id; }")
    on = lambda s: pg.evaluate("(s)=>!!document.querySelector(s)", s)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2000)
    slide("bottomtab-profile", "bottomtab-calendar")
    off_lit = [lit(), on(".screen-home-actual"), on(".screen-calendar-tab"), on(".screen-profile")]
    x, y = cen("bottomtab-profile")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); pg.wait_for_timeout(80)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + 4, "y": y}]}); pg.wait_for_timeout(30)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); pg.wait_for_timeout(1500)
    tap_other = [lit(), on(".screen-profile")]
    slide("bottomtab-profile", "bottomtab-calendar")
    from_lit = [lit(), on(".screen-calendar-tab")]
    cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": False}); cdp.detach()
    chk("a slide starts only on the lit tab: from another tab to a third %s, a press let go on it %s, from the lit tab %s" % (off_lit, tap_other, from_lit),
        off_lit == ["bottomtab-home", True, False, False] and tap_other == ["bottomtab-profile", True] and from_lit == ["bottomtab-calendar", True], [off_lit, tap_other, from_lit])
    # (12)/(13) the results
    RUN0 = g["RUN"].replace("stopQuestionTimer(); summarize(); await wait(500);", "stopQuestionTimer(); summarize(); return {};")
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
    pg.evaluate(RUN0, ["Victims of Crime", "all", 0, 0])
    pg.wait_for_timeout(700)
    g13 = pg.evaluate("""async()=>{ const p=document.querySelector('.rs-screen'); const gr=()=>{ const e=p.querySelector('.rs-grade'); return e ? e.textContent : ''; };
      const before=gr(); p.dispatchEvent(new MouseEvent('click',{bubbles:true})); await new Promise(r=>setTimeout(r,60)); const after=gr();
      await new Promise(r=>setTimeout(r,900)); const xpIn=!!p.querySelector('.rs-xp.rs-in, .rs-xp.rs-in-now, [class*=rs-xp].rs-in, [class*=rs-xp].rs-in-now');
      return { before: before.slice(0,12), after: after.slice(0,12), xpIn }; }""")
    chk("a tap finishes the grade box at once (%s -> %s) and the XP box comes in by itself (%s)" % (g13["before"], g13["after"], g13["xpIn"]),
        g13["before"] != g13["after"] and "100%" in g13["after"] and g13["xpIn"], g13)
    # keep tapping where the buttons rise (a run with misses: no pop-ups to hold it); then pause and tap a button.
    # The taps are timed in the page, 450ms apart. A tap the page itself ran late (a busy page - here the gate's own load after
    # the parts above) can come 700ms+ after the last one, and that is a pause: a press, by design. Such a run says nothing and is
    # run again (up to 3 tries); a button pressed less than 700ms after the tap before it fails.
    TAPS = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const LOG=[]; let prev=null, leftGap=null;
      for(let k=0;k<30;k++){ const p=document.querySelector('.rs-screen'); if(!p){ LOG.push('left'); break; }
        const b=[...p.querySelectorAll('.rs-final button')].find(x=>/Main menu/.test(x.textContent)); const t=(b && getComputedStyle(b).pointerEvents!=='none') ? b : p;
        const now=performance.now(); const gap = prev==null ? null : Math.round(now-prev); prev=now;
        t.dispatchEvent(new MouseEvent('click',{bubbles:true})); LOG.push(t===p ? 'panel' : 'button');
        await wait(450); if(!document.querySelector('.rs-screen') && leftGap==null) leftGap = gap; }
      return { LOG, leftGap, still: !!document.querySelector('.rs-screen') }; }"""
    tries = []
    for attempt in range(3):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
        pg.evaluate(RUN0, ["Victims of Crime", "all", 0, 3])
        tr = pg.evaluate(TAPS); tries.append(tr)
        if tr["still"] or (tr["leftGap"] is not None and tr["leftGap"] < 700): break
    LOG = tries[-1]["LOG"]; on_results = tries[-1]["still"]
    pg.wait_for_timeout(900)
    pg.evaluate("()=>{ const b=[...document.querySelectorAll('.rs-final button')].find(x=>/Main menu/.test(x.textContent)); b && b.click(); }")
    pg.wait_for_timeout(600)
    went = pg.evaluate("()=>!!document.querySelector('.screen-home-actual')")
    chk("taps that keep coming never press a results button (%s button taps of 30, still on the results: %s, tries %s); a tap after a pause does (home: %s)" % (LOG.count("button"), on_results, [(x["still"], x["leftGap"]) for x in tries], went),
        LOG.count("button") >= 5 and on_results and went, tries)
    # (19) a tap held back by a busy page
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
    pg.evaluate(RUN0, ["Victims of Crime", "all", 0, 3])
    pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); for(let k=0;k<40;k++){ const p=document.querySelector('.rs-screen'); if(!p) return;
      const b=[...p.querySelectorAll('.rs-final button')].find(x=>/Main menu/.test(x.textContent)); if(b && getComputedStyle(b).pointerEvents!=='none') break;
      p.dispatchEvent(new MouseEvent('click',{bubbles:true})); await wait(300); } }""")
    pg.wait_for_timeout(1800)
    bx = pg.evaluate("""()=>{ const b=[...document.querySelectorAll('.rs-final button')].find(x=>/Main menu/.test(x.textContent)); if(!b) return null; b.scrollIntoView({block:'center',behavior:'instant'});
      const r=b.getBoundingClientRect(), x=r.left+r.width/2, y=r.top+r.height/2; return { x, y, hit: document.elementFromPoint(x,y)===b || b.contains(document.elementFromPoint(x,y)) }; }""")
    pg.wait_for_timeout(300)
    held = None
    if bx and bx["hit"]:
        pg.evaluate("""()=>{ const p=document.querySelector('.rs-screen'); p.dispatchEvent(new MouseEvent('click',{bubbles:true}));
          setTimeout(()=>{ const t=performance.now(); while(performance.now()-t<900){} }, 30); }""")
        pg.wait_for_timeout(120)
        pg.mouse.click(bx["x"], bx["y"])
        pg.wait_for_timeout(800)
        held = pg.evaluate("()=>!!document.querySelector('.rs-screen')")
        pg.wait_for_timeout(1200)
        pg.mouse.click(bx["x"], bx["y"]); pg.wait_for_timeout(700)
    later = pg.evaluate("()=>!!document.querySelector('.screen-home-actual')")
    chk("a tap held back 900ms by a busy page, 120ms after a tap on the results, does not press Main menu (still on the results: %s); one after a pause does (home: %s)" % (held, later),
        held is True and later, [bx, held, later])
    # (14) the count's last number
    holds = []
    for wrong in (0, 3):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
        pg.evaluate(RUN0, ["Victims of Crime", "all", 0, wrong])
        r = pg.evaluate("""async()=>{ const T0=performance.now(); const seen=[]; let last=null;
          while(performance.now()-T0<9000){ const e=document.querySelector('.rs-screen .rs-pct'); const v=e?e.textContent.replace(/[^0-9]/g,''):null; if(v!==last){ seen.push([Math.round(performance.now()-T0), v]); last=v; } await new Promise(r=>requestAnimationFrame(r)); }
          return seen; }""")
        holds.append([r[-1][1], r[-2][1], r[-1][0] - r[-2][0]] if len(r) > 1 else None)
    chk("the count does not sit on the number before the grade (%s)" % (holds,), all(h and int(h[1]) == int(h[0]) - 1 and h[2] < 650 for h in holds), holds)
    # (15) the retake card
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
    pg.evaluate(g["RUN"], ["Victims of Crime", "all", 0, 3])
    rk = pg.evaluate(g["RETAKE"], 0)
    pg.wait_for_timeout(1500)
    card = pg.evaluate("()=>{ const k=document.querySelector('#stage .rs-retake-note .rs-kicker'), l=document.querySelector('#stage .rs-retake-line'); return [k && k.textContent, l && l.textContent]; }")
    chk("a retake's card says what it was and how it went (%s)" % (card,), card[0] == "Retake of missed questions" and card[1] == "All 3 answered correctly", card)
    # (16) the badge case
    pg.evaluate("()=>{ showProfile('badges'); }"); pg.wait_for_timeout(9000)
    bc = pg.evaluate("""async()=>{ const t=document.querySelector('.ncase-cell.is-earned'); if(!t) return null;
      const srcs=[]; let on=true; const obs=()=>{ const im=document.querySelector('.binspect-art.is-current'); if(im) srcs.push(im.getAttribute('src')); if(on) requestAnimationFrame(obs); }; requestAnimationFrame(obs);
      const T0=performance.now(); t.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})); const downMs=performance.now()-T0;
      await new Promise(r=>setTimeout(r,90)); t.click(); await new Promise(r=>setTimeout(r,1800)); on=false;
      try{ badgeInspectNow && badgeInspectNow.teardown(); }catch(e){}
      return { downMs: Math.round(downMs), faces: new Set(srcs).size, frames: srcs.length }; }""")
    chk("a found badge in the case: the finger costs %sms, the lift shows %s face(s) over %s frames" % (bc and bc["downMs"], bc and bc["faces"], bc and bc["frames"]),
        bc and bc["downMs"] < 80 and bc["faces"] == 1 and bc["frames"] > 20, bc)
    # (17) the unlock coin
    cr = pg.evaluate("""async()=>{ const u=unitsInTeachingOrder().find(x=>unitBadgeEarned(x)) || 'Victims of Crime'; warmBadgeCoinFaces([u]); await new Promise(r=>setTimeout(r,4000));
      const c=buildBadgeCoin(u); document.body.appendChild(c); const imgs=[...c.querySelectorAll('img')]; const ready=imgs.filter(i=>i.complete && i.naturalWidth>0).length; c.remove();
      return { imgs: imgs.length, ready }; }""")
    chk("the badge-unlock coin is complete the moment it is built (%s of %s pictures decoded)" % (cr["ready"], cr["imgs"]), cr["imgs"] >= 20 and cr["ready"] == cr["imgs"], cr)
    # (18) the slot left and the badge put back
    pg.evaluate("()=>{ showHome(); unitsInTeachingOrder().filter(u=>unitBadgeEarned(u)).forEach(u=>setBadgeDirtStage(u,4)); }"); pg.wait_for_timeout(600)
    pg.evaluate("()=>{ showProfile('badges'); }"); pg.wait_for_timeout(9000)
    ci = pg.evaluate("()=>{ const c=[...document.querySelectorAll('.ncase-cell')]; const t=c.find(x=>x.classList.contains('is-earned')); t.scrollIntoView({block:'center',behavior:'instant'}); return c.indexOf(t); }")
    WATCH = """(i)=>{ const cell=document.querySelectorAll('.ncase-cell')[i]; window.__slotLooks=[]; window.__slotOn=true;
      const obs=()=>{ const im=cell.querySelector('image.badge-raster'); if(im) window.__slotLooks.push((im.__strike&&im.__strike.draft?'draft':'final')+':'+(im.__strike&&im.__strike.grey?'grey':'found')+':'+(im.getAttribute('href')||'').length); if(window.__slotOn) requestAnimationFrame(obs); }; requestAnimationFrame(obs); }"""
    LOOKS = "()=>{ window.__slotOn=false; const s=window.__slotLooks; const out=[]; s.forEach(x=>{ if(out[out.length-1]!==x) out.push(x); }); return out; }"
    tb = pg.evaluate("(i)=>{ const r=document.querySelectorAll('.ncase-cell')[i].getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }", ci)
    pg.wait_for_timeout(300)
    pg.mouse.click(tb[0], tb[1]); pg.wait_for_timeout(1600)
    s0 = pg.evaluate("()=>badgeInspectNow && badgeInspectNow.state().stage")
    fx, fy, fw = pg.evaluate("() => { const r = document.querySelector('.binspect-float').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, r.width]; }")
    per = pg.evaluate("() => BINSPECT.rubPerStage")
    pg.mouse.move(fx, fy); pg.mouse.down()
    for k in range(per * 3 + 6):
        pos = (k % 6) if (k % 6) < 3 else 6 - (k % 6)
        pg.mouse.move(fx - fw * .08 + pos * fw * .055, fy + (k % 2)); pg.wait_for_timeout(16)
        if pg.evaluate("()=>badgeInspectNow.state().stage") != s0: break
    pg.mouse.up()
    s1 = pg.evaluate("()=>badgeInspectNow && badgeInspectNow.state().stage")
    pg.wait_for_timeout(1500)
    pg.evaluate(WATCH, ci); pg.evaluate("()=>badgeInspectNow.close()"); pg.wait_for_timeout(2500)
    back = pg.evaluate(LOOKS)
    chk("a badge put back a stage cleaner (%s -> %s) shows one finished picture in its slot (%s)" % (s0, s1, back),
        s1 is not None and s0 is not None and s1 < s0 and len(back) == 1 and back[0].startswith("final:found"), back)
    # (20) the daily question's XP on Home's banner glass
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
    GLASS = "(sel)=>{ const b=document.querySelector(sel); if(!b) return null; const cs=getComputedStyle(b), r=b.getBoundingClientRect(); return {bg:cs.backgroundImage+cs.backgroundColor, bf:cs.backdropFilter||cs.webkitBackdropFilter, rad:cs.borderTopLeftRadius, bar:cs.borderLeftWidth, rim:cs.borderTopColor, w:Math.round(r.width), l:Math.round(r.left), parts:['.app-banner-icon','.app-banner-tag','.app-banner-title'].filter(s=>b.querySelector(s)).length} }"
    pg.evaluate("()=>{ const b=buildAppBanner('gate-friend','friend','Cadet7\\nWants to be your friend.','View',()=>{},()=>{}); document.body.appendChild(b); placeTopBanner(b); b.classList.add('show'); }"); pg.wait_for_timeout(400)
    ref = pg.evaluate(GLASS, "#gate-friend"); pg.evaluate("()=>document.getElementById('gate-friend').remove()")
    pg.evaluate("()=>showPointsFlyEffect('+200 XP', 'Daily question')"); pg.wait_for_timeout(800)
    xb = pg.evaluate(GLASS, "#welcomebonus-banner")
    pg.wait_for_timeout(700)
    mover = pg.evaluate("()=>{ const m=document.querySelector('.wb-chip.welcomebonus-fly, #welcomebonus-banner.welcomebonus-fly'); return m ? (getComputedStyle(m).backdropFilter||'none') : null; }")
    pg.wait_for_timeout(1500)
    diff = [k for k in ("bg", "bf", "rad", "bar", "rim", "w", "l") if not xb or xb[k] != ref[k]]
    chk("the daily question's XP pop-up is Home's banner glass, as a friend request's (differs in: %s; icon, tag, title: %s of 3), and what flies to Profile is not blurred (%s)" % (diff or "nothing", xb and xb["parts"], mover),
        xb and not diff and xb["parts"] == 3 and mover in ("none", ""), [xb, ref, mover])
    # (21)/(22) Review's Starred pill (first the unlock pop-ups the runs above left waiting for "Got it": a notice waits behind a pop-up)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ store.seenUnitSelectTour = true; store.seenUnitOptionsTour = true; store.flagged = {}; store.unflagged = {}; const all=topicsIn(QUESTIONS); toggleFlag(QUESTIONS.findIndex(q=>(q.topic||'').trim()===all[1])); cfg.mode='review'; cfg.units=[]; cfg.source='all'; showSetup(); }")
    pg.wait_for_timeout(1500)
    sp = pg.evaluate("""()=>{ const look=e=>{ const c=getComputedStyle(e); return [c.backgroundImage, c.backgroundColor, c.borderTopColor, c.borderLeftColor, c.backdropFilter, c.boxShadow].join(' | '); };
      const p=document.querySelector('.screen-setup .starred-pill'), s=document.querySelector('.screen-setup .selall-btn'); if(!p||!s) return null;
      const st=p.querySelector('.starred-card-star.is-filled > path'); const cnt=p.querySelector('.pcount');
      const probe=document.createElement('span'); probe.style.color='#E8C770'; document.body.appendChild(probe); const gold=getComputedStyle(probe).color; probe.remove();
      const rgb=c=>(c.match(/[0-9.]+/g)||[]).slice(0,3).map(Number); const warm=c=>{ const v=rgb(c); return v.length===3 && v[0]-v[2]>40; };
      return { same: look(p)===look(s), rim: getComputedStyle(p).borderTopColor, star: st ? getComputedStyle(st).fill : null, gold, countWarm: warm(getComputedStyle(cnt).color) || warm(getComputedStyle(cnt).backgroundColor) }; }""")
    chk("Review's Starred pill has Select all's glass and rim (%s), a plain count (gold: %s), and its star is the starred question's gold (%s, %s)" % (sp and sp["same"], sp and sp["countWarm"], sp and sp["star"], sp and sp["gold"]),
        sp and sp["same"] and not sp["countWarm"] and sp["star"] == sp["gold"], sp)
    pg.evaluate("()=>{ store.flagged = {}; store.unflagged = {}; showSetup(); }"); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ document.getElementById('toast')?.remove(); document.querySelector('.screen-setup .starred-pill').click(); }"); pg.wait_for_timeout(700)
    nt = pg.evaluate("""()=>{ const t=document.getElementById('toast'); const b=[...document.querySelectorAll('.daily-alert.app-banner')].find(x=>/starred/i.test(x.textContent));
      const r=(b||t) ? (b||t).getBoundingClientRect() : null; return { banner: !!b, toast: !!t, top: r ? Math.round(r.top) : null, vh: innerHeight,
        focus: typeof cutsceneFocusActive === 'function' ? cutsceneFocusActive() : null, held: (typeof cutsceneHeld !== 'undefined' ? cutsceneHeld.map(h=>h.key).slice(0,4) : null), screen: ((document.querySelector('#stage > *')||{}).className||'').slice(0,40), starred: flaggedIndexes().length,
        scenes: [...document.body.querySelectorAll(':scope > :is(' + CUTSCENE_SCENE_SEL + ')')].map(e=>(e.id||'')+'.'+String(e.className).slice(0,40)), depth: cutsceneFocusDepth }; }""")
    chk("with nothing starred, a tap on it says so at the top (banner %s, toast %s, top %s of %s)" % (nt["banner"], nt["toast"], nt["top"], nt["vh"]),
        nt["banner"] and not nt["toast"] and nt["top"] is not None and nt["top"] < nt["vh"] / 3, nt)
    pg.evaluate("()=>{ document.querySelectorAll('.daily-alert').forEach(n=>n.remove()); showHome(); }"); pg.wait_for_timeout(800)
    # (23) a tapped switch sets off at the release
    pg.evaluate("()=>{ theme.reduceMotion=false; try{ applyTheme(); }catch(e){} showAppearance(); }"); pg.wait_for_timeout(2500)
    SW = """async([late, flip])=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
      const box=[...document.querySelectorAll('#stage .opt > .box')].find(b=>!/Reduce motion/i.test(b.closest('.opt').textContent)); if(!box) return null;
      box.scrollIntoView({block:'center'}); await wait(400);
      const b=box.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2, cb=box.parentNode.querySelector(':scope > input[type=checkbox]'), on0=cb.checked;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:57,isPrimary:true,clientX:x,clientY:y});
      const fr=[]; let on=true; const T0=performance.now();
      const f=t=>{ const L=box.querySelector('.nsw-lens'); let c=null; if(L){ try{ c=new DOMMatrixReadOnly(getComputedStyle(L).transform).m41; }catch(e){} } fr.push([t-T0, c]); if(on) requestAnimationFrame(f); }; requestAnimationFrame(f);
      box.dispatchEvent(mk('pointerdown')); await wait(90); const up=performance.now()-T0; box.dispatchEvent(mk('pointerup'));
      if(flip){ await wait(late); box.parentNode.click(); }
      await wait(1100); on=false;
      const seen=fr.filter(v=>v[1]!=null); const start=seen.length?seen[0][1]:null;
      const moved=seen.find(v=>v[0]>up && Math.abs(v[1]-start)>.6);
      return { flipped: cb.checked!==on0, startsAfterUp: moved ? Math.round(moved[0]-up) : null, last: seen.length ? Math.round(seen[seen.length-1][1]*10)/10 : null, start: start==null?null:Math.round(start*10)/10,
               far: seen.length ? Math.round(Math.max(...seen.map(v=>Math.abs(v[1]-start)))) : 0, restore: ()=>{} }; }"""
    tap = pg.evaluate(SW, [150, True])
    pg.wait_for_timeout(500)
    none = pg.evaluate(SW, [0, False])
    pg.wait_for_timeout(500)
    chk("a switch tapped sets off %sms after the finger lifts, with its flip 150ms later (flipped: %s); a tap whose flip never comes goes %spx and back (%s -> %s)" % (tap and tap["startsAfterUp"], tap and tap["flipped"], none and none["far"], none and none["start"], none and none["last"]),
        tap and tap["flipped"] and tap["startsAfterUp"] is not None and tap["startsAfterUp"] < 60 and none and not none["flipped"] and abs((none["last"] or 0) - (none["start"] or 0)) < 1.5, [tap, none])
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
    # (24) the chat button and Pause in the bar's glass
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
    LOOK = "(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const c=getComputedStyle(e); return [c.backgroundImage, c.backgroundColor, c.borderTopColor, c.backdropFilter||c.webkitBackdropFilter, c.boxShadow].join(' | '); }"
    bar = pg.evaluate(LOOK, ".bottomtabs")
    QRUN = """async([ui, right])=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const u=topicsIn(QUESTIONS)[ui]; const idx=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u && inWholeUnit(QUESTIONS[i]));
      theme.autoAdvance=false; cfg.source='all'; cfg.mode='drill'; cfg.units=[u]; beginRun(idx); for(let t=0;t<60 && !document.querySelector('.qpanel .choice');t++) await wait(100); await wait(400);
      if(!right) return true; const qi=order[pos]; const ch=[...document.querySelectorAll('.qpanel .choice')]; ch[optionOrder(qi).indexOf(QUESTIONS[qi].answer)].click(); await wait(1700); return true; }"""
    pg.evaluate(QRUN, [5, False])
    pause = pg.evaluate(LOOK, ".top #pausebtn"); chat = pg.evaluate(LOOK, ".chatdock-btn")
    chk("on a test, the chat button and Pause are the tab bar's own glass (chat: %s, Pause: %s)" % (chat == bar, pause == bar), bar and chat == bar and pause == bar, [bar, chat, pause])
    pg.evaluate("()=>{ try{ stopQuestionTimer(); }catch(e){} showHome(); }"); pg.wait_for_timeout(800)
    # (25) Next question under the answers
    pg.evaluate("()=>{ const s=document.createElement('style'); s.id='gate-phone-keys'; s.textContent='#hint{display:none !important}'; document.head.appendChild(s); }")
    NB = """()=>{ const b=document.getElementById('nextbtn'), ch=[...document.querySelectorAll('.qpanel .choice')]; if(!b||b.hidden||!ch.length) return null; const r=b.getBoundingClientRect(), l=ch[ch.length-1].getBoundingClientRect();
      const rem=parseFloat(getComputedStyle(document.documentElement).fontSize)||16; return { gapRem: +((r.top-l.bottom)/rem).toFixed(2), fromBottom: Math.round(innerHeight-r.bottom), scrolls: document.documentElement.scrollHeight>innerHeight+1 }; }"""
    pg.evaluate(QRUN, [5, True]); short = pg.evaluate(NB)
    pg.evaluate("()=>{ try{ stopQuestionTimer(); }catch(e){} showHome(); }"); pg.wait_for_timeout(800)
    # a question that fills the screen: the longest stem and choices of a unit
    pg.set_viewport_size({"width": 440, "height": 600}); pg.wait_for_timeout(500)
    pg.evaluate(QRUN, [7, True]); tall = pg.evaluate(NB)
    pg.evaluate("()=>{ try{ stopQuestionTimer(); }catch(e){} showHome(); document.getElementById('gate-phone-keys')?.remove(); }"); pg.wait_for_timeout(800)
    pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(600)
    pg.evaluate("()=>{ const s=document.createElement('style'); s.id='gate-phone-keys'; s.textContent='.foot > .floatbtn.qnext{ --qnext-raise:0px !important; }'; document.head.appendChild(s); }")
    pg.set_viewport_size({"width": 440, "height": 600}); pg.wait_for_timeout(500)
    pg.evaluate(QRUN, [7, True]); tall0 = pg.evaluate(NB)
    pg.evaluate("()=>{ try{ stopQuestionTimer(); }catch(e){} showHome(); document.getElementById('gate-phone-keys')?.remove(); }"); pg.wait_for_timeout(600)
    pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(800)
    chk("Next question comes up %s rem under a short question's answers, and where it always was when the question fills the screen (%s px from the bottom, was %s)" % (short and short["gapRem"], tall and tall["fromBottom"], tall0 and tall0["fromBottom"]),
        short and 1.6 <= short["gapRem"] <= 2.6 and tall and tall0 and tall["scrolls"] and tall["fromBottom"] == tall0["fromBottom"], [short, tall, tall0])
    # (26) the Pause card
    pc = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const u=topicsIn(QUESTIONS)[5]; const idx=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u && inWholeUnit(QUESTIONS[i]));
      cfg.source='all'; cfg.mode='drill'; cfg.units=[u]; beginRun(idx); for(let t=0;t<60 && !document.querySelector('.qpanel .choice');t++) await wait(100); await wait(400); pauseRun(); await wait(900);
      const st=document.querySelector('.pause-stack'), s=st.getBoundingClientRect(), cs=getComputedStyle(st); const bs=[...document.querySelectorAll('.pausepanel .actions button')]; const rs=bs.map(b=>b.getBoundingClientRect());
      const bg=b=>getComputedStyle(b).backgroundColor; const before=rs[0];
      const out={ card: cs.borderTopLeftRadius!=='0px' && cs.backgroundColor!=='rgba(0, 0, 0, 0)', off: Math.round(Math.abs(s.top+s.height/2-innerHeight/2)), n: bs.length,
        row: bs.length===3 && Math.abs(rs[1].top-rs[2].top)<1 && rs[1].top>rs[0].bottom-1 && Math.abs(rs[1].width-rs[2].width)<1, twoLooks: bs.length===3 && bg(bs[1])===bg(bs[2]) && bg(bs[0])!==bg(bs[1]) };
      document.getElementById('pause-quit').click(); await wait(800); const k=document.querySelector('.pausepanel .actions button').getBoundingClientRect();
      out.keep = Math.abs(k.top-before.top)<0.6 && Math.abs(k.left-before.left)<0.6; document.querySelector('.pausepanel .actions button').click(); await wait(500); try{ resumeRun(); }catch(e){} await wait(300); try{ stopQuestionTimer(); }catch(e){} showHome(); return out; }""")
    chk("Pause is one card on the screen's middle (%s px off), Resume across it, Save and exit and Quit test side by side in one look (%s), and Keep going lands where Resume was (%s)" % (pc["off"], pc["twoLooks"], pc["keep"]),
        pc["card"] and pc["off"] <= 8 and pc["row"] and pc["twoLooks"] and pc["keep"], pc)
    pg.wait_for_timeout(1200)
    # (27)/(28) Home's corner buttons and the class list
    pg.evaluate("()=>{ window.NOVA_CLASS_OWNER = (store && store.publicId) || 'me'; if(store && !store.publicId) store.publicId='me'; try{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); }catch(e){} showHome(); }")
    pg.wait_for_timeout(3000)
    cb = pg.evaluate("""async()=>{ const c=s=>document.querySelector(s); const b=c('.class-bubble'), q=c('.daily-question-fab'), rk=c('#stage .cosmic-badge-rank:not(.cosmic-badge-lit)'); if(!b||!q||!rk) return null;
      const g=e=>{ const s=getComputedStyle(e); return { body: s.backgroundColor, rim: s.borderTopColor, blur: s.backdropFilter||s.webkitBackdropFilter||'none' }; };
      const stops=[...b.querySelectorAll('svg stop')].map(s=>getComputedStyle(s).stopColor); const rgb=x=>(x.match(/[\d.]+/g)||[]).slice(0,3).map(Number); const spread=Math.max(0,...stops.map(x=>{ const v=rgb(x); return Math.max(...v)-Math.min(...v); }));
      const it=[...document.querySelectorAll('.class-stack-item .csi-bubble')]; b.click(); await new Promise(r=>setTimeout(r,800)); const open=it.map(e=>e.getBoundingClientRect().top);
      b.click(); await new Promise(r=>setTimeout(r,700)); const br=b.getBoundingClientRect(); const shut=it.map(e=>{ const r=e.getBoundingClientRect(); return Math.abs((r.top+r.height/2)-(br.top+br.height/2)); });
      return { b: g(b), q: g(q), rk: g(rk), spread, open, shut: shut.map(Math.round) }; }""")
    same = cb and cb["b"]["body"] == cb["rk"]["body"] == cb["q"]["body"] and cb["b"]["rim"] == cb["rk"]["rim"] and cb["b"]["blur"] == cb["rk"]["blur"] == cb["q"]["blur"]
    chk("Home's daily question and class button are the rank bubbles' glass (body, rim, frost: %s) and the class mark is in its own colours (spread %s)" % (bool(same), cb and cb["spread"]),
        same and cb["spread"] > 40, cb)
    chk("closing the class list sends each bubble back into the class button (%s px from its centre)" % (cb and cb["shut"],), cb and cb["shut"] and max(cb["shut"]) <= 4, cb)
    # (29) the trophy, (30) Silver, (31) a secret flare
    tr = pg.evaluate("()=>{ const s=document.querySelector('#bottomtab-rewards svg'); return s ? s.querySelectorAll('path').length : null; }")
    chk("the Leaderboard tab's trophy is one piece (%s path)" % tr, tr == 1, tr)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ window.rankUpHolds = () => false; store.rankFloor = 2; store.rankMapSeen = 1; store.mysteryColorsFound = { red:true, orange:false, yellow:false, violet:false, white:false, core:false }; homeUnlocksOwed=()=>false; showHome(); }")
    pg.wait_for_timeout(2500)
    pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    sv = pg.evaluate("""()=>{ const lit=document.querySelector('#stage .cosmic-badge-rank.cosmic-badge-lit[data-rank-tier="ranger"]'), off=document.querySelector('#stage .cosmic-badge-rank:not(.cosmic-badge-lit)'); if(!lit||!off) return { why: [rankOf(store), !!document.querySelector('.screen-home-actual'), [...document.querySelectorAll('#stage .cosmic-badge-rank')].map(b=>b.dataset.rankTier+(b.classList.contains('cosmic-badge-lit')?'*':'')).join(','), [...document.body.children].filter(e=>/cut|scene|journey|rs-spot/.test(e.id+' '+e.className)).map(e=>e.id||e.className).join('|')] };
      const rgb=x=>{ const v=(x.match(/[0-9.]+/g)||[]).map(Number); return /^color\(/.test(x) ? v.slice(0,3).map(n=>n*255) : v.slice(0,3); };
      const L=getComputedStyle(lit), O=getComputedStyle(off); const rim=rgb(L.borderTopColor), offRim=rgb(O.borderTopColor);
      return { rim: rim.map(Math.round), offRim: offRim.map(Math.round), cool: Math.round(rim[2]-rim[0]), offCool: Math.round(offRim[2]-offRim[0]) }; }""")
    if sv and "why" in sv: print("   silver not on Home:", sv["why"]); sv = None
    chk("a lit Silver flare is not a locked flare's grey: its rim is cool silver-blue (blue over red by %s, a locked one's by %s)" % (sv and sv["cool"], sv and sv["offCool"]),
        sv and sv["cool"] >= 20 and abs(sv["offCool"]) < 8, sv)
    fd = pg.evaluate("""()=>{ const d=document.querySelector('#stage .cosmic-flare-dot:not(.is-found) .cof-body'), f=document.querySelector('#stage .cosmic-flare-dot.is-found .cof-body'); if(!d) return null; const c=e=>getComputedStyle(e);
      return { unfound: (c(d).backgroundImage.match(/gradient/g)||[]).length, rim: /inset/.test(c(d).boxShadow), found: f ? (c(f).backgroundImage.match(/gradient/g)||[]).length : null }; }""")
    chk("a secret flare has a glint, the light pooled at its foot, its body and a rim (%s layers not found, %s found, rim %s)" % (fd and fd["unfound"], fd and fd["found"], fd and fd["rim"]),
        fd and fd["unfound"] >= 4 and fd["rim"] and (fd["found"] is None or fd["found"] >= 3), fd)
    pg.evaluate("()=>{ store.rankFloor = 0; showHome(); }"); pg.wait_for_timeout(800)
    # (33)/(34) the start sheet's sliders
    pg.evaluate("()=>{ store.seenUnitSelectTour=true; store.seenUnitOptionsTour=true; cfg.mode='drill'; cfg.units=[topicsIn(QUESTIONS)[5]]; cfg.timer='down'; cfg.timerMinutes=30; showSetup(); }")
    pg.wait_for_timeout(1500)
    pg.evaluate("()=>{ const m=document.getElementById('unitoptions-modal'); if(m) m.hidden=false; }"); pg.wait_for_timeout(900)
    tl = pg.evaluate("""async()=>{ const s=document.querySelector('.minutes-sect input.slider'), mb=document.querySelector('.minutes-sect .slider-maxbtn'); if(!s||!mb) return null;
      const at=v=>{ s.value=v; s.dispatchEvent(new Event('input',{bubbles:true})); return cfg.timerMinutes; };
      const low=at(0); mb.click(); await new Promise(r=>setTimeout(r,500)); return { min: Number(s.min), max: Number(s.max), low, top: cfg.timerMinutes }; }""")
    chk("the time limit runs 1 to 120 minutes and Max sets 120 (%s)" % (tl,), tl and tl["min"] == 1 and tl["max"] == 120 and tl["low"] == 1 and tl["top"] == 120, tl)
    fw = pg.evaluate("""async()=>{ const out=[]; for(const sel of ['.unitoptions-modal-sheet .slider-allbtn:not(.slider-maxbtn)', '.minutes-sect .slider-maxbtn']){
        const b=document.querySelector(sel); if(!b) { out.push(null); continue; } const s=b.closest('.sliderwrap').querySelector('input.slider');
        if(!b.classList.contains('on')){ b.click(); await new Promise(r=>setTimeout(r,500)); }
        s.value=Number(s.max)-3; s.dispatchEvent(new Event('input',{bubbles:true}));
        const a=getComputedStyle(b,'::after'); out.push({ lit: b.classList.contains('just-ready'), word: (b.textContent||'').trim(), content: a.content, color: a.color, base: getComputedStyle(b).color });
        await new Promise(r=>setTimeout(r,900)); } return out; }""")
    okw = fw and all(x and x["lit"] and x["content"].strip('"').lower() == x["word"].lower() and x["color"] != x["base"] for x in fw)
    chk("letting go of All or Max, the fill carries the word in dark over the white one (%s)" % ([x and (x["content"], x["color"]) for x in (fw or [])],), okw, fw)
    pg.evaluate("()=>{ document.getElementById('unitoptions-modal') && (document.getElementById('unitoptions-modal').hidden = true); showHome(); }"); pg.wait_for_timeout(800)
    # (10) the decoded-sheet cap
    cap = pg.evaluate("""()=>{ if(typeof charPreKeep!=='function') return null; const made=[]; for(let i=0;i<20;i++){ const sp={ url:'x'+i, pre:{ i } }; made.push(sp); charPreKeep(sp); }
      charPreKeep(made[6]); const extra={ url:'y', pre:{} }; made.push(extra); charPreKeep(extra);
      const held=made.filter(sp=>sp.pre); return { held: held.length, newest: !!extra.pre, touched: !!made[6].pre, oldest: !!made[7].pre }; }""")
    chk("at most 14 character sheets stay decoded, the ones used last (%s)" % (cap,), cap and cap["held"] == 14 and cap["newest"] and cap["touched"] and not cap["oldest"], cap)
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
    # ---- the iPhone layer ----
    IPH = """(()=>{ const ua='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148';
      Object.defineProperty(Navigator.prototype,'userAgent',{get:()=>ua,configurable:true}); try{ delete Navigator.prototype.vibrate; }catch(e){}
      window.__blurs=0; const rb=HTMLElement.prototype.blur; HTMLElement.prototype.blur=function(){ if(this === document.activeElement) __blurs++; return rb.apply(this, arguments); };
      window.__hswAt=[]; new MutationObserver(ms=>{ ms.forEach(m=>m.addedNodes.forEach(n=>{ if(n.nodeType===1 && n.classList.contains('nova-hsw')) __hswAt.push([performance.now(), Date.now() < (window.settleUntil||0)]); })); }).observe(document, {childList:true, subtree:true}); })()"""
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    w, h, ins, inst = g["DEV"]["promax"]; g["g"]["new_page"].w, g["g"]["new_page"].h = w, h
    ctx, pg = g["g"]["new_page"](br, ins, inst, False)
    ctx.add_init_script(IPH)
    pg.add_init_script(g["INIT"] % __import__("json").dumps(g["seed"]()))
    pg.goto(g["url"]); pg.wait_for_timeout(3000)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL); pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(16000)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(3000)
    nsw = pg.evaluate("()=>document.querySelectorAll('.bottomtab > .nova-hsw').length")
    cdp = ctx.new_cdp_session(pg); cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
    def cen(i): return pg.evaluate("(id)=>{const b=document.getElementById(id).getBoundingClientRect(); return [b.left+b.width/2,b.top+b.height/2];}", i)
    def tap(i):
        x, y = cen(i)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); pg.wait_for_timeout(60)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    # (7)
    pg.evaluate("()=>{ const sw=document.querySelector('#bottomtab-profile > .nova-hsw'); if(sw) sw.focus(); window.__blurs=0; }")
    focused = pg.evaluate("()=>!!(document.activeElement && document.activeElement.classList.contains('nova-hsw'))")
    tap("bottomtab-profile"); pg.wait_for_timeout(1200); tap("bottomtab-calendar"); pg.wait_for_timeout(1200)
    blurs = pg.evaluate("()=>__blurs")
    chk("a tab tap with its switch focused (%s, %s switches on the bar) is not taken for typing: %s blurs over two taps" % (focused, nsw, blurs), nsw >= 4 and focused and blurs == 0, [focused, nsw, blurs])
    # (8)
    pg.evaluate("()=>{ __hswAt.length=0; }")
    t0 = pg.evaluate("()=>performance.now()")
    tap("bottomtab-rewards"); pg.wait_for_timeout(3000)
    at = pg.evaluate("()=>__hswAt.slice()")
    inside = [a for a in at if a[1]]
    first = round(at[0][0] - t0) if at else None
    chk("a new screen's switches go in after the glass has landed (%s put in, first %sms after the tap, %s inside the settle window)" % (len(at), first, len(inside)),
        len(at) >= 5 and not inside and first is not None and first >= 300, [len(at), first, len(inside)])
    # (9)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    sy = pg.evaluate("""async()=>{ let n=0; const real=window.syncLoopClock; window.syncLoopClock=function(r){ if(r && r.classList && r.classList.contains('cosmic-rank-anim')) n++; return real.apply(this, arguments); };
      showRankings(); await new Promise(r=>setTimeout(r,3500)); window.syncLoopClock=real;
      return { syncs: n, marks: document.querySelectorAll('.screen-rankings .rank-mark > .cosmic-rank-anim').length }; }""")
    chk("a board's flares are put on the loop clock once each (%s syncs for %s flares)" % (sy["syncs"], sy["marks"]), sy["marks"] >= 8 and sy["syncs"] <= 2 * sy["marks"], sy)
    br.close()
    # (32) Test #8 (Nov 9) is posted, and the next test hands over at 8 PM on Monday Nov 2 (Chicago, CST after Nov 1)
    import datetime
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    def at(when):
        c = br.new_context(viewport={"width": 393, "height": 852}, timezone_id="America/Chicago"); p2 = c.new_page()
        p2.add_init_script("try{localStorage.setItem('class26e.intro.seen','99')}catch(e){}")
        p2.clock.install(time=datetime.datetime.fromisoformat(when)); p2.goto(g["url"]); p2.wait_for_timeout(2500)
        return c, p2
    NT = "() => { try{ const u = nextTestUnits(); const t = testTopicsFor('2026-11-09'); return { d: u && u.date, u: u ? [...u.units].sort() : null, t: t && t.topics }; }catch(e){ return { err: String(e).slice(0, 80) }; } }"
    c1, p1 = at("2026-11-02T19:59:00-06:00"); before = p1.evaluate(NT); c1.close()
    c2, p2 = at("2026-11-02T20:00:30-06:00"); after = p2.evaluate(NT); c2.close()
    br.close()
    want = sorted(["Health and Safety Code", "Multiculturalism and Human Relations", "Racial Profiling", "Professionalism and Ethics"])
    chk("Test #8 on Nov 9 is posted (%s topics); at 7:59 PM Monday the next test is still today's (%s), from 8 PM it is Nov 9's four units (%s)" % (len((after or {}).get("t") or []), before and before.get("d"), after and after.get("d")),
        before and before.get("d") == "2026-11-02" and after and after.get("d") == "2026-11-09" and after.get("u") == want and len(after.get("t") or []) == 4, [before, after])
sys.exit(0 if g["ok"] else 1)
