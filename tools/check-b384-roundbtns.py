#!/usr/bin/env python3
"""Build 384 final check: the round buttons' icons look like iOS's.

Madison, beside a screenshot of iMessage's round back and FaceTime buttons: "Those bubbles look amazing, the back arrow looks
great ... it looks so clean and white and it's a great size. Ensure our bubbles look that great ... The icons within the bubbles
need to look that great." and of ours, "The arrow isn't centered". Measured off his screenshots at one scale: the circles are
the same size; iMessage's chevron is 41% of the circle tall (ours was 27%) in pure white (ours #E7EDF1, the chat glyph at .92
too), set ~3% of the circle left of the middle (ours box-centred); its camera is 41% tall (our speech bubble 31%).
On an installed iPhone 17 Pro Max at its 3x, each round icon button - the unit screen's back, the mode screen's back, a Settings
page's back, the sign-up class step's back, and the chat button:
(1) its glyph is pure white (computed colour, full opacity, and the ink's brightest pixel), the circle still 44px;
(2) its glyph is the size iOS draws it: 38-46% of the circle tall;
(3) a chevron's ink sits 3% of the circle left of the middle (within .5px) and on the middle up and down; the chat bubble's on
    the middle both ways;
(4) no page errors.
  python3 tools/check-b384-roundbtns.py [--against OLD/index.html]   (must FAIL on the build before)"""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b381-class.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b381-class.py"), "__name__": "b384rb"}
exec(src, G)
g = G["g"]
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = g["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = _old
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
SETTINGS_PAGE = ("showAppearance(); setTimeout(()=>{ const r=[...document.querySelectorAll('#stage button, #stage [role=button]')]"
                 ".find(b=>/Account|Sound|Display|Appearance|Notifications/i.test(b.textContent)); r&&r.click(); }, 200)")
BUTTONS = [("the unit screen's back", "cfg.mode='drill'; cfg.units=[]; showSetup()", "#stage .settings-nav-back", True),
           ("the mode screen's back", "showModeSelect()", "#stage .ios-nav-back", True),
           ("a Settings page's back", SETTINGS_PAGE, "#stage .settings-nav-back", True),
           ("the sign-up class step's back", "store.onboardingComplete=false; showClassSelection()", "#stage > .classselect-panel > .back-link", True),
           ("the chat button", "store.onboardingComplete=true; showHome()", "#chatdock-btn", False)]
BOX = """(s)=>{ const b=document.querySelector(s); if(!b) return null; const r=b.getBoundingClientRect(); const v=b.querySelector('svg'); const cs=getComputedStyle(v);
  return [r.left, r.top, r.width, r.height, cs.color, +cs.opacity * +getComputedStyle(b).opacity]; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx, pg, cdp = G["page"](br, 440, 956, (62, 0, 34, 0), True)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    dpr = pg.evaluate("devicePixelRatio")
    for label, call, sel, chevron in BUTTONS:
        pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('.rs-spot,.unlock-card,#tour-overlay,#tour-tooltip,.daily-alert').forEach(n=>n.remove()); %s; }" % call)
        pg.wait_for_timeout(1800)
        pg.evaluate("()=>document.querySelectorAll('.rs-spot,.unlock-card,#tour-overlay,#tour-tooltip,.daily-alert,.toast').forEach(n=>n.remove())")
        r = pg.evaluate(BOX, sel)
        if not r:
            chk("%s: on the screen" % label, False, sel); continue
        im = np.array(Image.open(io.BytesIO(pg.screenshot(clip={"x": r[0], "y": r[1], "width": r[2], "height": r[3]}))).convert("L")).astype(int)
        H, W = im.shape; yy, xx = np.mgrid[0:H, 0:W]
        inside = (xx - W / 2 + .5) ** 2 + (yy - H / 2 + .5) ** 2 < (W / 2 - 3) ** 2
        fill = int(np.median(im[inside])); ink = inside & (im > fill + (255 - fill) * .5)
        ys, xs = np.nonzero(ink)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        hpct = 100 * (y1 - y0 + 1) / H
        dx = ((x0 + x1) / 2 - (W - 1) / 2) / dpr; dy = ((y0 + y1) / 2 - (H - 1) / 2) / dpr
        white = r[4] == "rgb(255, 255, 255)" and abs(r[5] - 1) < 1e-6 and im[ink].max() >= 250
        chk("(1) %s: its glyph is pure white (%s at %s, brightest %d) in a %dpx circle" % (label, r[4], r[5], im[ink].max(), round(r[2])),
            white and abs(r[2] - 44) < .6 and abs(r[3] - 44) < .6, r)
        chk("(2) %s: its glyph is %.0f%% of the circle tall (iOS: 41%%)" % (label, hpct), 38 <= hpct <= 46, hpct)
        want = -.03 * r[2] if chevron else 0
        chk("(3) %s: its ink sits %+.2fpx across (wanted %+.2f, %s) and %+.2fpx up and down" % (label, dx, want, "iOS's optical centre" if chevron else "the middle", dy),
            abs(dx - want) <= .5 and abs(dy) <= .5, [dx, dy])
    chk("(4) no page errors", not errs, errs[:3])
    br.close()
G["srv"].shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
