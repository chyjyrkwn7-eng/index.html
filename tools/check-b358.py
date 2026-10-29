"""Build 358: while the app is hidden the Leaderboard's rows go back to bare frames and Home's moving-emblem sheets come
off (less to keep, so iOS is less likely to end the page), and come back when it returns; the grey platter is hidden the
instant the glass is pressed (it cannot snap across with no glass); a run that ended in the background is noted.
Run:  python3 tools/check-b358.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
HID = "()=>{ Object.defineProperty(document,'hidden',{configurable:true,get:()=>window.__h}); Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>window.__h?'hidden':'visible'}); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(HID); pg.evaluate("()=>{ window.__h=false; }")
    pg.evaluate(FILL); pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(4000)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
      const cnt=()=>({ svgs: document.querySelectorAll('.rank-rows .rank-avatar svg').length, marks: document.querySelectorAll('.rank-rows .rank-mark svg').length, bare: document.querySelectorAll('.rank-rows .rank-row[data-lazy-art]').length, flip: document.querySelectorAll('.rank-rows .char-flip-play').length });
      const out={ before: cnt() };
      window.__h=true; document.dispatchEvent(new Event('visibilitychange')); await wait(100); out.hidden=cnt();
      window.__h=false; document.dispatchEvent(new Event('visibilitychange')); await wait(3500); out.back=cnt(); return out; }""")
    chk("the Leaderboard has its art before leaving (%s)" % (r["before"],), r["before"]["svgs"] >= 30, r)
    chk("while hidden its rows are bare frames: no drawing, no flare, no moving sheet (%s)" % (r["hidden"],), r["hidden"]["svgs"] == 0 and r["hidden"]["marks"] == 0 and r["hidden"]["flip"] == 0 and r["hidden"]["bare"] >= 30, r)
    chk("and it is all back a few seconds after returning (%s)" % (r["back"],), r["back"]["svgs"] >= 30 and r["back"]["bare"] == 0, r)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(4500)
    h = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const cnt=()=>document.querySelectorAll('.cosmic-hero-wrap .cosmic-rank-anim').length; const out={ before: cnt() };
      window.__h=true; document.dispatchEvent(new Event('visibilitychange')); await wait(100); out.hidden=cnt();
      window.__h=false; document.dispatchEvent(new Event('visibilitychange')); await wait(3500); out.back=cnt(); return out; }""")
    chk("Home's moving emblems come off while hidden and are back after (%s)" % (h,), h["before"] >= 1 and h["hidden"] == 0 and h["back"] >= h["before"], h)
    # the platter is hidden the instant the glass is pressed
    s = pg.evaluate("""async()=>{ const el=document.getElementById('bottomtab-rewards'); const sl=document.getElementById('bottomtabs-slider'); const r=el.getBoundingClientRect(); const x=r.left+r.width/2,y=r.top+r.height/2;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:41,isPrimary:true,clientX:x,clientY:y});
      el.dispatchEvent(mk('pointerdown')); const atPress = sl.style.opacity;
      await new Promise(r=>setTimeout(r,80)); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
      const atRelease = sl.style.opacity; await new Promise(r=>setTimeout(r,2600)); return { atPress, atRelease, end: sl.style.opacity, shown: parseFloat(getComputedStyle(sl).opacity) }; }""")
    chk("the platter is hidden at the press and the release, and clear at the end (%s)" % (s,), s["atPress"] == "0" and s["atRelease"] == "0" and s["end"] == "" and s["shown"] > .9, s)
    # a run that ended in the background is noted at the next start
    pg.evaluate("()=>{ const real=Storage.prototype.setItem; Storage.prototype.setItem=function(k,v){ if(k==='class26e.session' && /closed/.test(v)) return; return real.call(this,k,v); }; }")
    pg.evaluate("()=>{ localStorage.setItem('class26e.session', JSON.stringify({state:'hidden', t:Date.now()-5000, screen:'board', build:'x'})); localStorage.removeItem('class26e.crashlog'); }")
    pg.reload(); pg.wait_for_timeout(3500)
    c = pg.evaluate("()=>localStorage.getItem('class26e.crashlog')")
    chk("a run that ended while hidden is noted at the next start (%s)" % (c,), c and "ENDED-hidden" in c and "board" in c, c)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
