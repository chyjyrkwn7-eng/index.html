#!/usr/bin/env python3
"""Build 384.24: a person's card draws the character inside its circle.
Madison, a leaderboard card with a ghost, the drop and sparks circled where they sit on and past the ring: "Why are some character effects going
outside the circles?" Read off the pixels: for every character of the page's class, open the card (openPersonSheet), photograph the token with the
character's drawing on and then with it hidden, and compare the ring of pixels just OUTSIDE the circle (1.5px to 14px past its edge): the drawing may
not have painted anything there (the token's own ring and glow are in both pictures and cancel).
Run:  python3 tools/check-b384-cardclip.py   (--against OLD/index.html must FAIL: 384.23's ghost drop, alien glyph and marksman's rifle tip are outside)"""
import io, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
DPR = 2
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=DPR)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    ids = pg.evaluate("()=>AVATAR_CHARACTERS.map(c=>c.id)")
    bad = []
    for ch in ids:
        pg.evaluate("""(ch)=>{ document.querySelectorAll('.invite-overlay,.person-sheet').forEach(n=>n.remove());
          openPersonSheet({ pub:'tstpub000001', firstName:'Cody Smart', avatarChar:ch, level:1, badges:0, points:100, correct:0, hundos:0 }); }""", ch)
        pg.wait_for_timeout(1100)
        pg.add_style_tag(content=".person-card-art *{ animation:none !important; transition:none !important; }")
        el = pg.query_selector(".person-card-art")
        if not el: bad.append((ch, "no card")); continue
        b = el.bounding_box(); R = b["width"] / 2; pad = 18
        clip = {"x": b["x"] - pad, "y": b["y"] - pad, "width": b["width"] + 2 * pad, "height": b["height"] + 2 * pad}
        pg.wait_for_timeout(250)
        a = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        pg.evaluate("()=>{ const e=document.querySelector('.person-card-art > .rank-avatar'); if(e) e.style.visibility='hidden'; }")
        pg.wait_for_timeout(150)
        c = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        d = ImageChops.difference(a, c).convert("L"); W, H = d.size; px = d.load(); cx, cy = W / 2.0, H / 2.0
        n = 0
        for y in range(H):
            for x in range(W):
                r = (((x + .5 - cx) ** 2 + (y + .5 - cy) ** 2) ** .5) / DPR
                if R + 1.5 <= r <= R + 14 and px[x, y] > 14: n += 1
        if n: bad.append((ch, n))
    chk("every character (%d) is drawn inside the token's circle: nothing of the drawing paints 1.5-14px past its edge (outside: %s)" % (len(ids), bad[:6]), not bad, bad)
    chk("no page errors", not errs, errs[:2])
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
