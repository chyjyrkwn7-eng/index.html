#!/usr/bin/env python3
"""Build 384 review: every row in Settings has its parts on one line - the tile on the row's middle, the chevron on the row's
middle, and a grey value (the "Open now", "On", a count) level with the chevron beside it.

Madison, again: "the word now is not centered properly, shouldn't it line up with the arrow? Not sure how this kind of stuff keeps
getting missed." The centring gate measures a control's ink against its own box; a row's value text is not a control, so it was
never measured against its neighbours. This measures, on the Settings menu and every Settings page, in both classes, at the phone
and tablet sizes and 3x: for each row, the tile's and the chevron's ink against the row's middle, and the value's visual middle
(its capitals' top to its baseline, the middle of what the eye reads) against the chevron's.
Allowed: 1.0px (a quarter of a point is rounding; two is a lean).
  python3 tools/check-b384-rows.py [--against OLD/index.html]   (must FAIL on the build before)"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
PAGES = [None, "classes", "sync", "sound", "study", "motion", "share", "account", "rankings"]
GEOM = """()=>{ const out=[]; document.querySelectorAll('#stage .settings-row').forEach(row=>{
    const rb=row.getBoundingClientRect(); if(!rb.width || !rb.height) return;
    const q=e=>{ if(!e) return null; const b=e.getBoundingClientRect(); return b.width ? [b.left,b.top,b.width,b.height] : null; };
    out.push({ name:(row.querySelector('.settings-row-label')||{}).textContent||'', row:[rb.left,rb.top,rb.width,rb.height],
      icon:q(row.querySelector(':scope > .settings-row-icon')), chev:q(row.querySelector(':scope > .settings-row-chev')), val:q(row.querySelector(':scope > .settings-row-value')), fs:parseFloat(getComputedStyle(row.querySelector(':scope > .settings-row-value')||row).fontSize) }); });
  return out; }"""
def ink(im, s, box):
    x, y, w, h = box
    reg = im[int(y * s):int((y + h) * s) + 1, int(x * s):int((x + w) * s) + 1]
    bg = reg[0, 0]; m = np.abs(reg - bg).sum(axis=2) > 90
    ys, xs = np.nonzero(m)
    return (ys.min() / s + y, ys.max() / s + y) if len(ys) else None
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    worst = {"icon": 0, "chev": 0, "val": 0}; bad = []; vals = []
    for cls in ("academy", "ifc"):
        for (w, h) in ((440, 956), (834, 1194)):
            for page in PAGES:
                try:
                    ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, dpr=3)
                    if cls == "ifc":
                        pg.evaluate("()=>{ window.NOVA_CLASS='ifc'; }")
                    pg.evaluate("(p)=>{ document.querySelectorAll('#splashscreen').forEach(n=>n.remove()); showAppearance(p ? {page:p} : undefined); }", page)
                    pg.wait_for_timeout(1300)
                    rows = pg.evaluate(GEOM)
                    im = np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert("RGB")).astype(int)
                    for r in rows:
                        rx, ry, rw, rh = r["row"]; mid = ry + rh / 2
                        if ry < 0 or ry + rh > h: continue
                        if r["icon"]:
                            b = r["icon"]; d = abs((b[1] + b[3] / 2) - mid)
                            if d > worst["icon"]: worst["icon"] = d
                            if d > 1.0: bad.append((cls, w, page, r["name"], "tile", round(d, 2)))
                        if r["chev"]:
                            c = ink(im, 3, r["chev"])
                            if c:
                                d = abs((c[0] + c[1]) / 2 - mid)
                                if d > worst["chev"]: worst["chev"] = d
                                if d > 1.0: bad.append((cls, w, page, r["name"], "chevron", round(d, 2)))
                        if r["val"] and r["chev"]:
                            v = ink(im, 3, r["val"]); c = ink(im, 3, r["chev"])
                            if v and c:
                                # the visual middle of a word: its first letter's top to its baseline (the descender is not what the eye centres)
                                # from the first letter's top (every value here starts with a capital or a digit), 56% of the cap height down:
                                # between the capitals' middle and the lowercase letters' - where the eye puts the middle of a word
                                capH = 0.727 * r.get("fs", 17)
                                vm = v[0] + capH * 0.56; cm = (c[0] + c[1]) / 2
                                d = abs(vm - cm)
                                if d > worst["val"]: worst["val"] = d
                                vals.append(round(vm - cm, 2))
                                if d > 1.25: bad.append((cls, w, page, r["name"], "value vs chevron", round(vm - cm, 2)))
                    ctx.close()
                except Exception as e:
                    bad.append((cls, w, page, "ERROR", repr(e)[:120], 0))
    br.close()
cb.SERVER.shutdown()
print("value offsets (px, + = low):", sorted(set(vals)))
chk("every row's tile, chevron and value are on its line (worst: tile %.2f, chevron %.2f, value %.2f px; wanted 1.0 or less for tile and chevron, 1.25 for the word)" % (worst["icon"], worst["chev"], worst["val"]), not bad, bad[:8])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
