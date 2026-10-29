"""Build 355: a page that comes back without ever having been told it was hidden (iOS can freeze the app first) puts the
loops back to the pose they left in, holds them until frames are steady, and notes what happened.
Run:  python3 tools/check-b355.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
      const a=document.getAnimations().filter(x=>x.effect&&x.effect.getTiming().iterations===Infinity&&String(x.animationName||'').indexOf('orbit')>=0)[0];
      if(!a) return null; const out={};
      try{ localStorage.removeItem('class26e.resumelog'); }catch(e){}
      out.p0=a.currentTime;
      /* the page was frozen: no hidden event, the loops ran on the wall clock for 7s, the alive tick went stale */
      loopAliveAt = Date.now() - 7000; a.currentTime = a.currentTime + 7000;
      document.dispatchEvent(new Event('visibilitychange'));
      await wait(30); out.soon=a.playState; out.jumpKept=a.currentTime-out.p0;
      await wait(1800); out.later=a.playState; out.total=a.currentTime-out.p0;
      out.log=localStorage.getItem('class26e.resumelog'); out.perf=(typeof tabPerfText==='function')?tabPerfText():'';
      return out; }""")
    chk("a page that was never told it was hidden is put back to the pose it left in (moved %s)" % (r and round(r["jumpKept"])), r and abs(r["jumpKept"]) < 1500, r)
    chk("and held there in the first frames back", r and r["soon"] == "paused", r)
    chk("then goes on, still within a couple of seconds of that pose (moved %s)" % (r and round(r["total"])), r and r["later"] == "running" and r["total"] < 3800, r)
    chk("the way back is noted (NOTTOLD) and reaches the report", r and "NOTTOLD" in (r["log"] or "") and "resume:" in (r["perf"] or ""), r and (r["log"], (r["perf"] or "")[:120]))
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
