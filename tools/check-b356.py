"""Build 356: coming back when the page's clocks cannot be trusted (the loops did NOT run on while it was away) puts the
loops where they were seen last, and the loop clock agrees with them; the Leaderboard rows below the first screenful
are all filled within a second of the list being built (on a slow device), the screenful at once; the speed test
reports the returns.   Run:  python3 tools/check-b356.py"""
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
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(3500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const out={};
      const ref=loopRef(); if(!ref) return null;
      out.p0=ref.currentTime;
      /* away for 7s by Date.now(), but the page's animation clock did not move (a frozen page) and no hidden event ran */
      loopAliveAt = Date.now() - 7000;
      document.dispatchEvent(new Event('visibilitychange'));
      await wait(40); out.soon=ref.currentTime-out.p0; out.state=ref.playState;
      await wait(1800); out.later=ref.currentTime-out.p0; out.stateLater=ref.playState;
      syncLoopClock(document); await wait(30); out.afterSync=ref.currentTime-out.p0-out.later;
      out.log=localStorage.getItem('class26e.resumelog'); return out; }""")
    chk("loops that did not move while the page was frozen are not rewound by the time away (%s)" % (r and round(r["soon"])), r and abs(r["soon"]) < 1500, r)
    chk("they go on from there (%s)" % (r and round(r["later"])), r and r["stateLater"] == "running" and 0 < r["later"] < 3500, r)
    chk("and the loop clock agrees with them: a re-sync moves them by no more than a second (%s)" % (r and round(r["afterSync"])), r and abs(r["afterSync"]) < 1000, r)
    chk("the return is logged", r and "NOTTOLD" in (r["log"] or "") and "drift" in (r["log"] or ""), r and r["log"])
    # the speed test report carries the returns
    t = pg.evaluate("async()=>(await runLagTest()).text")
    # (the report's text is the runs; the log rides in the perf line, which is built from localStorage - check the builder)
    chk("the speed test report builder includes the returns", "resume: " in open(HERE + "/../index.html").read().split("async function runLagTest")[1].split("function showBugReport")[0])
    # a run of quick taps does not build a screen under every tap
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    sp = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const b=document.getElementById('bottomtabs'); const n0=b._navBuilds||0;
      const ids=['rewards','home','calendar','profile','home','rewards','profile','calendar','rewards','home'];
      for(const d of ids){ const el=document.getElementById('bottomtab-'+d); const r=el.getBoundingClientRect(); const x=r.left+r.width/2,y=r.top+r.height/2;
        const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:31,isPrimary:true,clientX:x,clientY:y});
        el.dispatchEvent(mk('pointerdown')); await wait(35); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y})); await wait(135); }
      const during=(b._navBuilds||0)-n0; await wait(2500);
      return { during, screen: document.querySelector('.screen-home-actual')?'home':'other', lit: document.querySelector('.bottomtab.active').id }; }""")
    chk("ten taps 170ms apart build no more than ten screens, one for each tap at most (%s)" % (sp,), sp["during"] <= 10, sp)  # build 365: every tap's screen follows (was: at most four)
    chk("and end on the last tab's screen with it lit", sp["screen"] == "home" and sp["lit"] == "bottomtab-home", sp)
    # the leaderboard fills in
    pg.evaluate(FILL)
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(600)
    res = pg.evaluate("""async()=>{ const real = buildAvatarCharSVGSafe; window.buildAvatarCharSVGSafe = function(){ const t=performance.now(); while(performance.now()-t < 6){} return real.apply(this, arguments); };
      const wait=ms=>new Promise(r=>setTimeout(r,ms)); showRankings();
      const rows=()=>[...document.querySelectorAll('.rank-rows .rank-row')];
      const bare=()=>rows().filter(x=>{const a=x.querySelector('.rank-avatar'); return a && !a.querySelector('svg');});
      const onScreen=()=>bare().filter(x=>x.getBoundingClientRect().top < innerHeight - 90).length;
      const out={}; await wait(700); out.at700={ n: rows().length, bare: bare().length, bareOnScreen: onScreen() };
      await wait(1100); out.at1800={ n: rows().length, bare: bare().length }; window.buildAvatarCharSVGSafe = real; return out; }""")
    chk("the first screenful has its characters by 0.7s (%s)" % (res["at700"],), res["at700"]["n"] >= 40 and res["at700"]["bareOnScreen"] == 0, res)
    chk("and the rows near the view have theirs by 1.8s on a slow device; the far ones wait to be scrolled toward - build 366 (%s)" % (res["at1800"],), res["at1800"]["bare"] <= res["at1800"]["n"] - 12, res)
    cv = pg.evaluate("()=>{ const r=document.querySelector('.rank-rows .rank-row'); return r ? getComputedStyle(r).contentVisibility : null; }")
    chk("rows are not hidden from the browser while off screen (%s)" % cv, cv in (None, "visible"), cv)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
