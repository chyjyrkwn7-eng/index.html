#!/usr/bin/env python3
"""Build 384 (art8) check: a Fire Code pin's side, turned in your hand, is its parts' own colours - not washed with grey.

Madison, of the Appendix H pencil turned: two erasers, a pale second pencil behind the first - "check every badge because I've seen
this same kinda look/problem before". The side (badgeEdgeURL's slices) was the parts' colour map laid at .72 over the silver side,
so every part's side came out its colour washed with grey (the eraser's side pink, the steel ferrule's beige, the paint faded) and
read as a second, ghostly object beside the face. Now each part's side is its own colour lit by the side's light, opaque.
For every pin (Fire Code's 58 and, since the academy's are pins too, its 24), the middle slice of its side (tone 1, clean) is drawn and compared, pixel for pixel inside the outline,
with the parts' colour map (chapterObjColourMap) in the same frame:
  (1) the side keeps the parts' colour: its mean saturation (chroma / brightness - lighting keeps it, a grey wash does not) is at
      least .7 of the map's on every badge and .85 at the class's median, over the parts that have a colour (map saturation > .25, brightness > 70) (every badge)
  (2) the side's hue follows the part under it: where the map is saturated (chroma > 40), the side's hue is within 25 degrees on at
      least 90% of those pixels (every badge with any)
  (3) no page errors
Run:  python3 tools/check-b384-sides.py [--against REV|FILE] [--class ifc|academy|both]    --against c2417de (before) FAILS (1) and (1b): saturation kept min .39, median .70 (now min .73, median .92)."""
import sys, os, io, json, base64, subprocess, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
spec = importlib.util.spec_from_file_location("rcb", ROOT + "/tools/render-chapter-badges.py"); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
from PIL import Image
import numpy as np
AG = arg("--against"); BODY = None; TH = .7
CLASSES = {"both": ["ifc", "academy"]}.get(arg("--class", "both"), [arg("--class", "both")])
if AG: BODY = open(AG, encoding="utf-8").read() if os.path.exists(AG) else subprocess.check_output(["git", "-C", ROOT, "show", AG + ":index.html"]).decode("utf-8")
JS = r"""async ({k}) => {
  const us = unitsInTeachingOrder(); if(k >= us.length) return null;
  const u = us[k], shape = badgeShapeFor(u); if(!shape.obj) return { u, skip: true };
  const vb = badgeViewBoxFor(shape.d).split(/\s+/).map(Number), R = 256;
  const url = badgeEdgeURL(u, 1, 0);
  const img = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = url; });
  const c = document.createElement('canvas'); c.width = c.height = R; const x = c.getContext('2d'); x.drawImage(img, 0, 0, R, R);
  const cm = chapterObjColourMap(shape, { vx: vb[0], vy: vb[1], vw: vb[2], cx: shape.c[0], cy: shape.c[1], S: BADGE_GEOM.scale }, R, u);
  const m = document.createElement('canvas'); m.width = m.height = R; const mx = m.getContext('2d'); const id = mx.createImageData(R, R); id.data.set(cm); mx.putImageData(id, 0, 0);
  return { u, side: c.toDataURL(), map: m.toDataURL() };
}"""
dec = lambda d: np.array(Image.open(io.BytesIO(base64.b64decode(d.split(",", 1)[1]))).convert("RGBA")).astype(float)
def hue_chroma(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; mx = np.max(a[..., :3], -1); mn = np.min(a[..., :3], -1); c = mx - mn
    h = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return h, c
fails = 0
def report(ok, label):
    global fails
    print(("PASS " if ok else "FAIL ") + label, flush=True)
    if not ok: fails += 1
from scipy import ndimage
from playwright.sync_api import sync_playwright
srv, port = R.serve()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
    allerrs = []
    for cls in CLASSES:
        ctx, pg, errs = R.open_page(br, port, dict(R.SEED), 600, 600, 1, cls, BODY)
        weak, offhue, n, ratios = [], [], 0, []; k = 0
        while True:
            r = pg.evaluate(JS, {"k": k}); k += 1
            if r is None: break
            if r.get("skip"): continue
            n += 1
            S, M = dec(r["side"]), dec(r["map"])
            inside = ndimage.binary_erosion((S[..., 3] > 250) & (M[..., 3] > 250), iterations=3)   # away from the outline (the side's mask reaches a hair past it)
            hs, cs = hue_chroma(S); hm, cmc = hue_chroma(M)
            # saturation (chroma / brightness): lighting a colour (shade to sheen) keeps it; washing it with grey does not
            satS = cs / np.maximum(1, np.max(S[..., :3], -1)); satM = cmc / np.maximum(1, np.max(M[..., :3], -1))
            col = inside & (satM > .25) & (np.max(M[..., :3], -1) > 70)   # parts with a colour to lose (a white page or a steel band has none; a near-black's 'colour' is noise)
            if col.sum() < 50: col = inside
            ratio = float(satS[col].mean() / max(1e-6, satM[col].mean()))
            ratios.append(ratio)
            if ratio < TH: weak.append((r["u"][:34], round(ratio, 2)))
            sat = inside & (cmc > 40)
            if sat.sum() > 50:
                dh = np.abs(((hs[sat] - hm[sat]) + 180) % 360 - 180)
                ok = float((dh <= 25).mean())
                if ok < .9: offhue.append((r["u"][:34], round(ok, 2)))
        allerrs += errs; ctx.close()
        name = "police academy" if cls == "academy" else "Fire Code"
        if not n: print("   %s: no pins" % name); continue
        med = sorted(ratios)[len(ratios) // 2]
        print("   %s: saturation kept, per badge: min %.2f median %.2f" % (name, min(ratios), med))
        report(not weak, "(1) %s: every pin's side keeps its parts' colour, saturation >= %.2f of the map's (%d badges; short: %d %s)" % (name, TH, n, len(weak), weak[:8]))
        report(med >= .85, "(1b) %s: across the class the side keeps it: median >= .85 (%.2f)" % (name, med))
        report(not offhue, "(2) %s: a pin's side takes the hue of the part under it, 90%% within 25 degrees (off: %d %s)" % (name, len(offhue), offhue[:8]))
    report(not allerrs, "(3) no page errors %s" % allerrs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED (%d)" % fails)
sys.exit(1 if fails else 0)
