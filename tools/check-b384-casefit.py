#!/usr/bin/env python3
"""Build 384 (art8) check: every badge sits in its slot in the case with an even gap all the way round.

Madison: "ensure the case fitting ... looks good and matches up and stuff... for all of them". A Fire Code pin is drawn as its face
plus its thickness (OBJ_PIN.wall, down and to the right); the slot was cut round the face alone, so the gap was the full clearance at
the top and left and nothing at the bottom and right, where the pin ran over the slot's lip. For every badge in both classes this
draws, off-screen, the token's own render (badgeStrikeURL) and the slot the app draws (the "-wall" path of buildUnitBadgeSVG, at its
stroke width), and reads the gap from every point of the slot's rim to the nearest pixel of the pin:
  (1) nothing of the pin lies past its slot
  (2) the gap is even: its 5th percentile is at least .6 of its median, its 95th at most 1.5 of it
  (3) no page errors
Run:  python3 tools/check-b384-casefit.py [--against REV|FILE] [--class ifc|academy|both]
      --against 21a1a45 (before art8) FAILS (1) and (2) on every Fire Code badge. Needs numpy, scipy, Pillow."""
import sys, os, io, json, base64, subprocess, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
spec = importlib.util.spec_from_file_location("rcb", ROOT + "/tools/render-chapter-badges.py"); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
from PIL import Image
import numpy as np
from scipy import ndimage
AG = arg("--against")
BODY = None
if AG: BODY = open(AG, encoding="utf-8").read() if os.path.exists(AG) else subprocess.check_output(["git", "-C", ROOT, "show", AG + ":index.html"]).decode("utf-8")
CLASSES = {"both": ["ifc", "academy"]}.get(arg("--class", "both"), [arg("--class", "both")])
JS = r"""async ({k, W}) => {
  const us = unitsInTeachingOrder(); if(k >= us.length) return null;
  const u = us[k], shape = badgeFaceShapeFor(u), G = BADGE_GEOM;
  const hole = shape.obj ? OBJ_PIN.slotGap : (G.key + G.gap), lip = shape.obj ? OBJ_PIN.slotLip : G.lip;
  const vb = badgeViewBoxFor(shape.d).split(/\s+/).map(Number);
  const url = badgeStrikeURL(u, false, W, 0);
  const img = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = url; });
  const w = img.naturalWidth, h = img.naturalHeight;
  const ct = document.createElement('canvas'); ct.width = w; ct.height = h; ct.getContext('2d').drawImage(img, 0, 0);
  const ch = document.createElement('canvas'); ch.width = w; ch.height = h; const x = ch.getContext('2d');
  x.setTransform(w / vb[2], 0, 0, h / vb[3], -vb[0] * w / vb[2], -vb[1] * h / vb[3]);
  const cx = shape.c[0], cy = shape.c[1]; x.translate(cx, cy); x.scale(G.scale, G.scale); x.translate(-cx, -cy);
  const built = buildUnitBadgeSVG(u, true, { px: 100, dirt: 0 });
  const wallEl = [...built.querySelectorAll('path')].find(e => /-wall\)/.test(e.getAttribute('fill') || ''));
  const hp = new Path2D(wallEl.getAttribute('d')), hr = parseFloat(wallEl.getAttribute('stroke-width')) / 2;
  const p = new Path2D(shape.d); x.fillStyle = '#fff'; x.strokeStyle = '#fff'; x.lineJoin = 'round'; x.lineWidth = 2 * hr; x.fill(hp); x.stroke(hp);
  const co = document.createElement('canvas'); co.width = w; co.height = h; const y = co.getContext('2d');
  y.setTransform(x.getTransform()); y.fillStyle = '#fff'; y.fill(p);
  return { u, obj: !!shape.obj, hole, lip, scale: G.scale, upx: w / vb[2], t: ct.toDataURL(), h: ch.toDataURL(), o: co.toDataURL() };
}"""
dec = lambda d: Image.open(io.BytesIO(base64.b64decode(d.split(",", 1)[1]))).convert("RGBA")
fails = 0
def report(ok, label):
    global fails
    print(("PASS " if ok else "FAIL ") + label, flush=True)
    if not ok: fails += 1
from playwright.sync_api import sync_playwright
srv, port = R.serve()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
    allerrs = []
    for cls in CLASSES:
        ctx, pg, errs = R.open_page(br, port, dict(R.SEED), 800, 800, 1, cls, BODY)
        past_bad, uneven = [], []; k = 0
        while True:
            r = pg.evaluate(JS, {"k": k, "W": 900})
            if r is None: break
            T = np.array(dec(r["t"]))[..., 3] > 160; H = np.array(dec(r["h"]))[..., 3] > 128
            upx = r["upx"]
            rim = H & ~ndimage.binary_erosion(H)
            gaps = ndimage.distance_transform_edt(~T)[rim] / upx
            past = float((T & ~H).sum()) / upx ** 2
            med = float(np.median(gaps)); p5 = float(np.percentile(gaps, 5)); p95 = float(np.percentile(gaps, 95))
            if past > .5: past_bad.append((r["u"][:40], round(past, 1)))
            if not (med > 0 and p5 >= .6 * med and p95 <= 1.5 * med): uneven.append((r["u"][:40], round(p5, 2), round(med, 2), round(p95, 2)))
            k += 1
        name = "police academy" if cls == "academy" else "Fire Code"
        report(not past_bad, "(1) %s: no badge reaches past its slot (%d badges; past, units^2: %s)" % (name, k, past_bad[:6]))
        report(not uneven, "(2) %s: every badge's gap is even all the way round (p5 >= .6 and p95 <= 1.5 of the median; uneven: %d %s)" % (name, len(uneven), uneven[:6]))
        allerrs += errs; ctx.close()
    br.close()
report(not allerrs, "(3) no page errors %s" % allerrs[:3])
print("\nALL PASS" if not fails else "\nFAILED (%d)" % fails)
sys.exit(1 if fails else 0)
