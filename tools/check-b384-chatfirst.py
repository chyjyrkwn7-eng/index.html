#!/usr/bin/env python3
"""Build 384.95: THE CHAT BUTTON IS UP IN THE FRAME HOME FIRST SHOWS, NOT 0.8s LATER.

Madison (iPhone 17 Pro Max, installed, a screen recording of a launch): "Chat takes a second to load when you load the app." The
recording (15fps) has Home up through the fading splash and the round chat button popping in nine frames (~0.6s) later. Cause:
syncChatDock() hides the dock while ANY #splashscreen is in the page - and the splash stays in the page for the whole of its fade
(.splash-hide, opacity .75s) until finishSplash's timer removes it 800ms after the fade starts (450ms on a class switch). Home's
.wrap is revealed in the frame .splash-hide goes on (#splashscreen:not(.splash-hide) ~ .wrap{visibility:hidden}), so for that
whole time Home showed without its chat button. (No Firestore is involved: the dock is built from showHome() and needs only
store.onboardingComplete; the unread dot can come later.)

This launches a used account (installed, phone and iPad) with a per-frame recorder (rAF from the first script) and finds the
first frame in which the splash has .splash-hide (the first frame Home shows through it). In that frame, and in every frame after
it, #chatdock-btn must be displayed (the dock not [hidden], the button laid out, visibility visible, opacity 1 on it and on the
dock). Also: no page errors.

  python3 tools/check-b384-chatfirst.py [--against OLD/index.html]   (384.94 must FAIL)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
seed = dict(rc["SEED"]); seed["seenClassTip"] = True
srv, port = rc["serve"]()
REC = """(() => { window.__cf = []; let n = 0;
  const vis = () => { const b = document.getElementById('chatdock-btn'); if(!b) return 'none';
    const d = b.closest('.chatdock'); if(d && d.hidden) return 'dock-hidden';
    const cs = getComputedStyle(b), r = b.getBoundingClientRect();
    if(cs.display === 'none' || cs.visibility !== 'visible' || r.width < 20) return 'not-laid-out';
    let o = 1; for(let e = b; e && e !== document.body; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity) || 0;
    return o >= .99 ? 'shown' : 'faded ' + o.toFixed(2); };
  const f = (t) => { const sp = document.getElementById('splashscreen');
    const home = !!document.querySelector('#stage .screen-home-actual, #stage [data-screen="home"]');
    window.__cf.push({ t: Math.round(t), sp: sp ? (sp.classList.contains('splash-hide') ? 'fading' : 'up') : 'gone', home, btn: vis() });
    if(++n < 900) requestAnimationFrame(f); };
  requestAnimationFrame(f); })();"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for label, w, h in (("phone 440x956", 440, 956), ("iPad 834x1194", 834, 1194)):
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
        pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.a2hs','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
                           "localStorage.setItem('class26e.intro.seen','99');localStorage.setItem('class26e.daily.seen','x');localStorage.setItem('class26e.drill.v1',%s)}catch(e){}" % json.dumps(json.dumps(seed)))
        pg.add_init_script(REC)
        pg.route("**/version.json", lambda r, q: r.abort())
        if BODY is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.goto("http://127.0.0.1:%d/index.html" % port)
        for _ in range(60):
            pg.wait_for_timeout(250)
            fr = pg.evaluate("()=>window.__cf || []")
            if any(x["sp"] == "gone" for x in fr) and len([x for x in fr if x["sp"] == "gone"]) > 10: break
        fr = pg.evaluate("()=>window.__cf || []")
        # frames before the splash is parsed read "gone" too: only a frame after one with the splash up counts
        upat = next((i for i, x in enumerate(fr) if x["sp"] == "up"), len(fr))
        fade = [i for i, x in enumerate(fr) if i > upat and x["sp"] != "up"]
        if not fade:
            chk("%s: the splash started its fade on its own (%d frames recorded)" % (label, len(fr)), False, fr[-3:]); ctx.close(); continue
        i0 = fade[0]; first = fr[i0]
        chk("%s: Home is the screen under the splash when its fade starts (frame %d, %dms)" % (label, i0, first["t"]), first["home"], first)
        after = fr[i0:]
        bad = [x for x in after if x["btn"] != "shown"]
        firstshown = next((x for x in after if x["btn"] == "shown"), None)
        late = (firstshown["t"] - first["t"]) if firstshown else None
        chk("%s: the chat button is drawn in the first frame Home shows (fade start, %dms) and every frame after - first shown %s ms later, %d of %d frames without it (%s)" % (
            label, first["t"], late, len(bad), len(after), sorted(set(x["btn"] for x in bad))), not bad, bad[:3])
        chk("%s: no page errors" % label, not errs, errs)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
