"""Build 350: the tab speed test runs five passes and leaves no style behind.
Run:  python3 tools/check-b350.py"""
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
    r = pg.evaluate("async ()=>await runLagTest()")
    t = (r or {}).get("text", "")
    for v in ("steady",):
        chk("the speed test has a [%s] pass for the Leaderboard" % v, ("[" + v + "]rewards") in t, t[:200])
    left = pg.evaluate("()=>!!document.getElementById('lagtest-variant')")
    chk("it leaves no variant style on the page", left is False, left)
    chk("the report fits in the 1700 characters the bug report keeps (%d)" % len(t), len(t) <= 1650, len(t))
    # coming back from another app: the loops hold their pose and go on only once frames are steady
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
      const a=document.getAnimations().filter(x=>x.effect&&x.effect.getTiming().iterations===Infinity&&String(x.animationName||'').indexOf('orbit')>=0)[0];
      if(!a) return null; const out={};
      Object.defineProperty(document,'hidden',{configurable:true,get:()=>window.__h}); Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>window.__h?'hidden':'visible'});
      out.t0=a.currentTime; window.__h=true; document.dispatchEvent(new Event('visibilitychange')); await wait(2500);
      out.hiddenMove=a.currentTime-out.t0; window.__h=false; document.dispatchEvent(new Event('visibilitychange'));
      await new Promise(r=>requestAnimationFrame(r)); out.soon=a.playState; /* (build 377: two steady frames, not four - read on the first) */ await wait(1500); out.later=a.playState; out.total=a.currentTime-out.t0; return out; }""")
    chk("the planet system does not move while the app is away", r and abs(r["hiddenMove"]) < 200, r)
    chk("and stays on its pose in the first frames back", r and r["soon"] == "paused", r)
    chk("then goes on from that pose, not from where the clock has got to (%s)" % (r and r.get("total")), r and r["later"] == "running" and r["total"] < 2500, r)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
