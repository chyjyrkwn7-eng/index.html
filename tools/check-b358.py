"""Build 358 (rows part reversed in 377: they keep their art; Home's sheets part reversed in 384: they stay on): while the app is
hidden Home's moving-emblem sheets came off (less to keep, so iOS is less likely to end the page), and came back when it returned; the grey platter is hidden the
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
    chk("the Leaderboard has its art before leaving (%s)" % (r["before"],), r["before"]["svgs"] >= 12, r)
    # build 377: REVERSED. The rows keep their art while hidden - stripping them made the board come back as discs and empty rings for
    # seconds ("the leaderboard not loading properly" after a return); the leak that made the page too big for iOS is fixed (375)
    chk("while hidden its rows keep their art (build 377) (%s)" % (r["hidden"],), r["hidden"]["svgs"] == r["before"]["svgs"] and r["hidden"]["marks"] == r["before"]["marks"] and r["hidden"]["bare"] <= r["before"]["bare"], r)
    chk("and the rows near the view are back a few seconds after returning (build 366: only those; the rest come as they are scrolled toward) (%s)" % (r["back"],), r["back"]["svgs"] >= 12 and r["back"]["svgs"] == r["before"]["svgs"], r)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(4500)
    # (384) a sheet on before it is measured: recording takes a while on a shared sandbox
    for _ in range(40):
        if pg.evaluate("()=>document.querySelectorAll('.cosmic-hero-wrap .cosmic-rank-anim').length") >= 1: break
        pg.wait_for_timeout(3000)
    h = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const cnt=()=>document.querySelectorAll('.cosmic-hero-wrap .cosmic-rank-anim').length; const out={ before: cnt() };
      window.__h=true; document.dispatchEvent(new Event('visibilitychange')); await wait(100); out.hidden=cnt();
      window.__h=false; document.dispatchEvent(new Event('visibilitychange')); await wait(3500); out.back=cnt(); return out; }""")
    # build 384: REVERSED, as 377 did for the rows. Taking them off and putting them back was what came back wrong ("it still kinda
    # does a weird thing"): each flare showed its still drawing, then crossfaded to its sheet, restarting. They stay on now.
    chk("Home's moving emblems stay on while hidden (build 384) and are all there after (%s)" % (h,), h["before"] >= 1 and h["hidden"] == h["before"] and h["back"] == h["before"], h)
    # the platter is hidden the instant the glass is pressed
    s = pg.evaluate("""async()=>{ const el=document.getElementById('bottomtab-rewards'); const sl=document.getElementById('bottomtabs-slider'); const r=el.getBoundingClientRect(); const x=r.left+r.width/2,y=r.top+r.height/2;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:41,isPrimary:true,clientX:x,clientY:y});
      el.dispatchEvent(mk('pointerdown')); const atPress = sl.style.opacity;
      await new Promise(r=>setTimeout(r,80)); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
      const atRelease = sl.style.opacity; await new Promise(r=>setTimeout(r,2600)); return { atPress, atRelease, end: sl.style.opacity, shown: parseFloat(getComputedStyle(sl).opacity) }; }""")
    chk("the platter is hidden at the press and the release, and clear at the end (%s)" % (s,), s["atPress"] == "0" and s["atRelease"] == "0" and s["end"] == "" and s["shown"] > .9, s)
    # a run that ended in the background is noted at the next start
    pg.evaluate("()=>{ const real=Storage.prototype.setItem; window.__realSet=real; Storage.prototype.setItem=function(k,v){ if(k==='class26e.session') return; return real.call(this,k,v); }; }")
    pg.evaluate("()=>{ window.__realSet.call(localStorage, 'class26e.session', JSON.stringify({state:'hidden', t:Date.now()-5000, screen:'board', build:'x'})); localStorage.removeItem('class26e.crashlog'); }")
    pg.reload(); pg.wait_for_timeout(3500)
    c = pg.evaluate("()=>localStorage.getItem('class26e.crashlog')")
    chk("a run that ended while hidden is noted at the next start (%s)" % (c,), c and "ENDED-hidden" in c and "board" in c, c)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
