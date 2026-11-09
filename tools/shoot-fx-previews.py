#!/usr/bin/env python3
"""Every place a hundo effect is PREVIEWED, both classes, on one sheet (build 384 round 6: "ensure all the hundo effect
previews when clicking on them are updated" / "The picture preview for the ifc hundo effects aren't that great, the academy
ones are better").

  python3 tools/shoot-fx-previews.py OUTDIR [--against FILE] [--size W H]

Per class, per effect, on the page's own clock (every animation seeked, so a still is a chosen moment):
  tile     Customize's Hundo effect page: its tile (the poster)
  stage    the small 100% box playing its box-only version, a moment in (Customize's Your look row, the pop-up's box)
  mock-a   the detail card's miniature results screen, the effect playing on the centred grade
  mock-b   the same miniature once it has settled (the grade up, the XP card under it)
  still    the effect's still (the Unlocked row, reduce motion)
Writes each crop and sheet-previews.png (rows: class x effect; columns: the five)."""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
AG = None
if "--against" in a:
    i = a.index("--against"); AG = os.path.abspath(a[i + 1]); del a[i:i + 2]
W, H = 440, 956
if "--size" in a:
    i = a.index("--size"); W, H = int(a[i + 1]), int(a[i + 2]); del a[i:i + 3]
OUT = os.path.abspath(a[0]); os.makedirs(OUT, exist_ok=True)
sys.argv = [sys.argv[0]] + (["--against", AG] if AG else [])
spec = importlib.util.spec_from_file_location("rr", HERE + "/lib_realrun.py")
rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
COLS = ["tile", "stage", "mock-a", "mock-b", "still"]
shots = {}
def grab(pg, sel, path):
    loc = pg.locator(sel).first
    try:
        loc.screenshot(path=path, timeout=6000); return path
    except Exception as e:
        print("  miss", sel, str(e).split("\n")[0][:120]); return None
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rr.cb.CHROME)
    for cls in ("academy", "ifc"):
        ctx, pg, errs = rr.open_run(br, cls, W, H, "confetti", run=False, dpr=3)
        names = pg.evaluate("() => Object.fromEntries(HUNDO_FX.map(d => [d.id, d.name]))")
        # tiles: the effects page, every tile at once
        pg.evaluate("() => { document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove()); showCustomize('fx'); }")
        rr.advance(pg, 1.2)
        for fx in IDS:
            shots[(cls, fx, "tile")] = grab(pg, ".hfx-opt[data-fx='%s'] .hfx-opt-art" % fx, os.path.join(OUT, "tile-%s-%s.png" % (cls, fx)))
            # the small box, playing its box-only version
            pg.evaluate("""(fx) => { const old = document.getElementById('shoot-stage'); if(old) old.remove();
              const w = document.createElement('div'); w.id = 'shoot-stage'; w.style.cssText = 'position:fixed;left:20px;top:120px;width:300px;z-index:9999;padding:0';
              w.appendChild(buildHundoFxStage(fx, { live: true, delay: 0 })); document.body.appendChild(w); }""", fx)
            rr.advance(pg, .3)
            tot = pg.evaluate("(fx) => (HUNDO_FX_BOX_TOTAL[fx] || 3000) / 1000", fx)
            rr.advance(pg, tot * .55)
            shots[(cls, fx, "stage")] = grab(pg, "#shoot-stage", os.path.join(OUT, "stage-%s-%s.png" % (cls, fx)))
            pg.evaluate("() => { const w = document.getElementById('shoot-stage'); if(w){ w.querySelectorAll('.hfx-stage').forEach(s => s.stopFx && s.stopFx()); w.remove(); } }")
            # the still
            pg.evaluate("""(fx) => { const w = document.createElement('div'); w.id = 'shoot-still'; w.style.cssText = 'position:fixed;left:20px;top:120px;width:96px;height:96px;z-index:9999;background:#1c2027;border-radius:14px;padding:10px;box-sizing:border-box';
              w.appendChild(buildHundoFxStill(fx)); document.body.appendChild(w); }""", fx)
            rr.advance(pg, .1)
            shots[(cls, fx, "still")] = grab(pg, "#shoot-still", os.path.join(OUT, "still-%s-%s.png" % (cls, fx)))
            pg.evaluate("() => document.getElementById('shoot-still')?.remove()")
        # the detail card's miniature
        for fx in IDS:
            pg.evaluate("(fx) => { document.querySelectorAll('.invite-overlay,.rs-spot,.unlock-card-overlay').forEach(e => e.remove()); showUnlockDetail(hundoFxDetail(fx)); }", fx)
            tot = pg.evaluate("(fx) => (HUNDO_FX_TOTAL[fx] || 3000) / 1000", fx)
            tail = pg.evaluate("(fx) => (HUNDO_FX_TAIL_AT[fx] || 1500) / 1000", fx)
            rr.advance(pg, .9 + min(tail * .5, 2.6))
            shots[(cls, fx, "mock-a")] = grab(pg, ".hfx-mock", os.path.join(OUT, "mock-a-%s-%s.png" % (cls, fx)))
            rr.advance(pg, tail * .5 + 1.6)
            shots[(cls, fx, "mock-b")] = grab(pg, ".hfx-mock", os.path.join(OUT, "mock-b-%s-%s.png" % (cls, fx)))
            pg.evaluate("() => { document.querySelectorAll('.hfx-mock').forEach(m => m.stopFx && m.stopFx()); showCustomize('fx'); }")
            rr.advance(pg, .4)
        if errs: print(cls, "ERRORS", errs[:3])
        ctx.close()
    br.close()
rr.cb.SERVER.shutdown()
# the sheet
CW = {"tile": 300, "stage": 300, "mock-a": 200, "mock-b": 200, "still": 96}
rows = []
for cls in ("academy", "ifc"):
    for fx in IDS:
        cells = []
        for col in COLS:
            p = shots.get((cls, fx, col))
            im = Image.open(p).convert("RGB") if p else Image.new("RGB", (CW[col], 60), (60, 0, 0))
            w = CW[col]; im = im.resize((w, max(1, int(im.height * w / im.width))))
            cells.append(im)
        rows.append(((cls, fx), cells))
pad = 12; lab = 150
rh = [max(c.height for c in cells) for _, cells in rows]
SW = lab + sum(CW[c] for c in COLS) + pad * (len(COLS) + 1); SH = sum(rh) + pad * (len(rows) + 1) + 24
S = Image.new("RGB", (SW, SH), (24, 26, 30)); d = ImageDraw.Draw(S)
x = lab + pad
for c in COLS: d.text((x, 6), c, fill=(230, 230, 230)); x += CW[c] + pad
y = 24 + pad
for ((cls, fx), cells), h in zip(rows, rh):
    d.text((8, y + 4), "%s\n%s" % (cls, fx), fill=(255, 220, 120))
    x = lab + pad
    for c, im in zip(COLS, cells): S.paste(im, (x, y)); x += CW[c] + pad
    y += h + pad
S.save(os.path.join(OUT, "sheet-previews.png")); print(os.path.join(OUT, "sheet-previews.png"), S.size)
