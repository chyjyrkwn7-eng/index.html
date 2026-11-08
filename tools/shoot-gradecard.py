#!/usr/bin/env python3
"""The 100% results screen's grade card in every hundo effect, next to the non-hundo grades, on REAL runs (round 3).

  python3 tools/shoot-gradecard.py OUTDIR [--against FILE] [--class ifc|academy] [--dev phone|tablet]

For each class and device it writes grades-<cls>-<dev>.png, one sheet: the plain grade cards on the first row (Pass, Fail, a
retake with nothing left, a retake with some left) and under them every rung's 100% card - MIDDLE of the effect on the left,
SETTLED (the effect over) on the right, each cropped off the real screen (2x). Also measures every part of each card and writes
it to grades-<cls>-<dev>.json (the gate, check-b384-gradecard.py, reads the same numbers).
Needs ffmpeg-free Pillow only. The page's clock is the recorder's own (lib_realrun.py), so a still is a chosen moment."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
args = sys.argv[1:]
AG = []
if "--against" in args:
    i = args.index("--against"); AG = ["--against", os.path.abspath(args[i + 1])]; del args[i:i + 2]
CLS = ["ifc", "academy"]; DEVS = {"phone": (440, 956), "tablet": (834, 1194)}
if "--class" in args:
    i = args.index("--class"); CLS = [args[i + 1]]; del args[i:i + 2]
if "--dev" in args:
    i = args.index("--dev"); DEVS = {args[i + 1]: DEVS[args[i + 1]]}; del args[i:i + 2]
OUT = os.path.abspath(args[0]); os.makedirs(OUT, exist_ok=True)
sys.argv = [sys.argv[0]] + AG
import lib_realrun as L
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
READ = L.READ_GRADE
HIDE = "() => { const s = document.createElement('style'); s.id = '__hide'; s.textContent = 'body > :not(#stage):not(script):not(style){ visibility:hidden !important; }'; document.head.appendChild(s); }"
SHOW = "() => document.getElementById('__hide') && document.getElementById('__hide').remove()"
def crop(pg, path, hide=False):
    # in Fire Code the badge / rank scene is up over the card once an effect is over: hide whatever sits on <body> outside the stage for the still
    if hide: pg.evaluate(HIDE)
    r = pg.evaluate("() => { const b = document.querySelector('.rs-grade').getBoundingClientRect(); return { x: b.left, y: b.top, width: b.width, height: b.height }; }")
    pg.screenshot(path=path, clip=r)
    if hide: pg.evaluate(SHOW)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.cb.CHROME, args=["--force-device-scale-factor=2"])
    for cls in CLS:
        for dev, (W, H) in DEVS.items():
            tag = "%s-%s" % (cls, dev); data = {}; ims = {}
            plain = [("Pass", 1, "drill", False), ("Fail", 7, "drill", False), ("Retake, none left", 0, "drill", True), ("Retake, some left", 2, "drill", True)]
            for name, miss, mode, rt in plain:
                ctx, pg, errs = L.open_run(br, cls, W, H, "confetti", miss, mode, rt)
                L.advance(pg, 14)
                data[name] = pg.evaluate(READ); p = "%s/_%s-%s.png" % (OUT, tag, name.replace(" ", "").replace(",", "")); crop(pg, p); ims[name] = p
                ctx.close()
            for fx in IDS:
                ctx, pg, errs = L.open_run(br, cls, W, H, fx)
                L.wait_fx(pg)
                total = pg.evaluate("(f) => (typeof HUNDO_FX_TOTAL !== 'undefined' && HUNDO_FX_TOTAL[f]) || 5000", fx) / 1000
                L.advance(pg, max(.8, total * .45))
                data[fx + "-mid"] = pg.evaluate(READ); p = "%s/_%s-%s-mid.png" % (OUT, tag, fx); crop(pg, p); ims[fx + "-mid"] = p
                # settled = the last moment the results card is on show: in Fire Code the badge / rank scene (.bc-scene) comes up over it as the
                # effect finishes, so step on in tenths until it is about to, or the effect's total has passed
                t = total * .45; p = "%s/_%s-%s.png" % (OUT, tag, fx)
                while True:
                    data[fx] = pg.evaluate(READ); crop(pg, p)
                    if t >= total + .1: break
                    L.advance(pg, .1); t += .1
                    if pg.evaluate("() => !!document.querySelector('.bc-scene')"): break
                ims[fx] = p
                if errs: print("ERRORS", fx, errs[:2])
                ctx.close()
            json.dump(data, open("%s/grades-%s.json" % (OUT, tag), "w"), indent=1)
            # the sheet
            rows = []
            lab = lambda im, t: (ImageDraw.Draw(im).text((8, 4), t, fill=(255, 255, 255)), im)[1]
            first = [Image.open(ims[n]) for n, *_ in plain]
            rows.append(first)
            for fx in IDS: rows.append([Image.open(ims[fx + "-mid"]), Image.open(ims[fx])])
            cw = max(i.width for r in rows for i in r); ch = max(i.height for r in rows for i in r)
            ncol = max(len(r) for r in rows)
            if dev == "phone": ncol = max(ncol, 2)
            sheet = Image.new("RGB", (ncol * (cw + 14) + 14, sum(max(i.height for i in r) + 14 for r in rows) + 14), (14, 17, 24)); y = 14
            for r in rows:
                x = 14
                for im in r: sheet.paste(im, (x, y)); x += cw + 14
                y += max(i.height for i in r) + 14
            sheet.save("%s/grades-%s.png" % (OUT, tag)); print("wrote", tag, sheet.size, flush=True)
            for p in ims.values(): os.remove(p)
    br.close()
L.cb.SERVER.shutdown()
