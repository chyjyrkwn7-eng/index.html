#!/usr/bin/env python3
"""Build 384.1 check: the splash's word and bar stay centred while they scale back as the splash fades out.

Build 384 added `#splashscreen.splash-hide #splash-group{ scale:1.04 }` (a little drift as Welcome comes up). The group is
centred by `left/top` + `transform:translate(-50%,-50%)`, and the `scale` property applies AFTER that transform, about the
default origin - the middle of the group's LAYOUT box, which is half a group-size down and right of the screen's middle. So
the 4% scale also moved the word 4% of that offset up and left: -5,-3 px on a 250x150 group, a small jump-and-drift on every
launch. check-fixes caught it only on a loaded machine, when the splash's own timer reached the fade while the gate measured.

This holds the splash in its hidden state (the class added by hand, the .75s transition run out) and measures the group's
painted middle against the viewport's, on a phone and a tablet, with the scale checked to really be in effect.

  python3 tools/check-b384-splashhide.py [--against OLD/index.html]   (must FAIL on the build before)
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
srv, port = rc["serve"]()
MEASURE = """async () => {
  const o = document.getElementById('splashscreen'), g = document.getElementById('splash-group');
  if(!o || !g) return null;
  const rect = () => { const r = g.getBoundingClientRect();
    return { cx: (r.left + r.right) / 2 - innerWidth / 2, cy: (r.top + r.bottom) / 2 - innerHeight / 2, w: r.width }; };
  const before = rect();
  o.classList.add('splash-hide');
  /* wait for the .75s scale transition to run out (on the clock it is 850ms; a loaded machine takes longer) */
  for(let i = 0; i < 40 && o.isConnected && parseFloat(getComputedStyle(g).scale) < 1.039; i++) await new Promise(res => setTimeout(res, 100));
  if(!o.isConnected) return { gone: true };
  const after = rect();
  return { before, after, scale: getComputedStyle(g).scale, grew: after.w / before.w };
}"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for label, w, h in (("phone 440x956", 440, 956), ("tablet 834x1194", 834, 1194)):
        ctx = br.new_context(viewport={"width": w, "height": h}); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.a2hs','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','99');localStorage.setItem('class26e.drill.v1',%s)}catch(e){}" % json.dumps(json.dumps(seed)))
        pg.route("**/version.json", lambda r, q: r.abort())
        if BODY is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(500)
        m = pg.evaluate(MEASURE)
        if not m or m.get("gone"):
            chk("%s: the splash was there to measure" % label, False, m); ctx.close(); continue
        chk("%s: before the fade the group is centred (%.1f, %.1f)" % (label, m["before"]["cx"], m["before"]["cy"]),
            abs(m["before"]["cx"]) <= 1.5 and abs(m["before"]["cy"]) <= 1.5, m["before"])
        chk("%s: the drift is really in effect (scale %s, group %.3fx wider)" % (label, m["scale"], m["grew"]),
            m["grew"] > 1.02, m)
        chk("%s: ... and it stays centred while it scales (%.1f, %.1f from the middle)" % (label, m["after"]["cx"], m["after"]["cy"]),
            abs(m["after"]["cx"]) <= 1.5 and abs(m["after"]["cy"]) <= 1.5, m["after"])
        chk("%s: no page errors" % label, not errs, errs)
        ctx.close()
    br.close()
srv.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
