#!/usr/bin/env python3
"""Build 384 full check: the loading screen never fades out over an empty stage.

The splash's time is a timer and the first screen is mounted after the saved copy loads, so on a slow phone - above all
after a class switch, where only what is left of the switch's bar runs on the new page - it faded out with nothing mounted
yet and the page's bare top row showed for a second or more (seen on the video recordings under load). The splash now
waits for the first screen, for a few seconds at most.

The slow phone is made here by holding the stage's first mount back (replaceChildren on #stage, deferred).

  python3 tools/check-b384-splashstage.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
seed = dict(rc["SEED"]); seed["seenClassTip"] = True
# hold the first mount of #stage back by HOLD ms (0: not at all), and sample the splash and the stage every 50ms
HOLD_JS = """(() => { const HOLD = %d, t0 = performance.now(), q = [];
  /* every change to #stage before HOLD waits until then, in order (a screen can mount by any of these) */
  ['replaceChildren', 'appendChild', 'append', 'prepend', 'insertBefore'].forEach(m => {
    const orig = Element.prototype[m] || Node.prototype[m]; if(!orig) return;
    const proto = Element.prototype[m] ? Element.prototype : Node.prototype;
    proto[m] = function(...a){
      if(HOLD && this && this.id === 'stage' && performance.now() - t0 < HOLD){
        if(!q.length) setTimeout(() => { q.splice(0).forEach(f => f()); }, Math.max(0, HOLD - (performance.now() - t0)));
        const me = this; q.push(() => orig.apply(me, a)); return m === 'appendChild' || m === 'insertBefore' ? a[0] : undefined; }
      return orig.apply(this, a); }; });
  window.__samples = [];
  const iv = setInterval(() => { const sp = document.getElementById('splashscreen'), st = document.getElementById('stage');
    window.__samples.push({ t: Math.round(performance.now() - t0), sp: sp ? (sp.classList.contains('splash-hide') ? 'hiding' : 'up') : 'gone',
      kids: st ? st.childElementCount : -1 });
    if(performance.now() - t0 > 16000) clearInterval(iv); }, 50); })();"""
srv, port = rc["serve"]()
def run(br, hold, wait_ms):
    ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.a2hs','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','99');localStorage.setItem('class26e.drill.v1',%s)}catch(e){}" % json.dumps(json.dumps(seed)))
    pg.add_init_script(HOLD_JS % hold)
    pg.route("**/version.json", lambda r, q: r.abort())
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(wait_ms)
    s = pg.evaluate("() => window.__samples"); ctx.close()
    return s, errs
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    # 1. a slow phone: the first screen lands 4.5s in, two seconds after the splash's own time
    s, errs = run(br, 4500, 7500)
    bare = [x for x in s if x["sp"] != "up" and x["kids"] == 0]
    chk("(1) slow first screen: the splash is never off an empty stage (%d of %d samples bare, first at %s ms)" % (len(bare), len(s), bare[0]["t"] if bare else "-"), not bare, bare[:3])
    off = next((x["t"] for x in s if x["sp"] != "up"), None); mounted = next((x["t"] for x in s if x["kids"] > 0), None)
    chk("(2) ... and it goes as soon as the screen is there (mounted %s ms, splash off %s ms)" % (mounted, off),
        off is not None and mounted is not None and 0 <= off - mounted <= 400, (mounted, off))
    chk("(3) no page errors", not errs, errs)
    # 2. a launch that never mounts a screen is not held behind the splash for good
    s, errs = run(br, 15000, 11500)
    off = next((x["t"] for x in s if x["sp"] != "up"), None)
    chk("(4) nothing ever mounted: the splash still goes, within a few seconds of its time (off at %s ms)" % off, off is not None and off < 10500, off)
    # 3. an ordinary launch is not slowed: off at its own time
    s0, errs = run(br, 0, 4500)
    off0 = next((x["t"] for x in s0 if x["sp"] != "up"), None)
    chk("(5) an ordinary launch: the splash goes at its own time (off at %s ms)" % off0, off0 is not None and off0 < 3300, off0)
    br.close()
srv.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
