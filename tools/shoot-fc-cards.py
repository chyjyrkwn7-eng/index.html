#!/usr/bin/env python3
"""The unlock card of each Fire Code character, locked and unlocked, as the app opens it on an iPhone (440x956, dpr 2).

  python3 tools/shoot-fc-cards.py OUTDIR [--ids a,b,c]

The card is the app's own (showUnlockDetail(characterDetail(id))), the one a press-and-hold opens. 'locked' is the
card a new account sees (every non-starter is a silhouette); 'unlocked' is the card of someone who holds it.
Writes OUTDIR/NN-name-unlocked.png and NN-name-locked.png (starters have no locked card).
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
OUT = args[0]; os.makedirs(OUT, exist_ok=True)
IDS = args[args.index("--ids") + 1].split(",") if "--ids" in args else None
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8cards1", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    ids = pg.evaluate("() => AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy).map(c => [c.id, !!(c.unlock || c.feat)])")
    for n, (cid, earned) in enumerate(ids, 1):
        if IDS and cid not in IDS: continue
        for state in (["unlocked", "locked"] if earned else ["unlocked"]):
            pg.evaluate("""([id, locked]) => {
              window.__orig = window.__orig || { isLockedCharacter };
              isLockedCharacter = locked ? (x => x === id) : (() => false);
              document.querySelectorAll('.invite-overlay').forEach(n => n.remove());
              showUnlockDetail(characterDetail(id));
            }""", [cid, state == "locked"])
            pg.wait_for_timeout(1400)
            name = pg.evaluate("(id) => AVATAR_DISPLAY_NAME[id] || id", cid)
            fn = "%02d-%s-%s.png" % (n, re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), state)
            pg.screenshot(path=os.path.join(OUT, fn))
    print("cards written", len(os.listdir(OUT)), "errors", errs[:3])
    ctx.close(); br.close()
srv.shutdown()
