#!/usr/bin/env python3
"""Build 384.71: the chevron on each mode tile is centred in its disc, by its ink, at the device's own pixel ratio.

Madison: "Mode arrows, make them centered correctly."
The arrow at the top right of each tile (Choose your mode: Drill, Mock, Review, Virtual Room in the academy and three in Fire Code; the Virtual Room's
Host and Join) is the tile's ::after: a disc with the arrow as its background picture, 50% of the disc, centred. The picture's chevron was drawn half a
unit right of the middle of its 24-unit box (arms from x 9.5 to 15.5 where the box's middle is 12), so its ink stood 0.31px right of the disc's middle on a
phone and 0.35px on a tablet - 0.45 / 0.35 as measured, the picture's own placement on the device pixel grid included - and 15px (a phone's 50%) is 45 device
pixels at 3x in a 90-pixel disc: a picture set on a half pixel the phone rounds. The arms run from x 9 to 15 now (the ink's middle is the box's, 12), and the
picture is 16px on the 34px disc and 14px on the 30px one (whole device pixels at 1x, 2x and 3x).

What this reads, at the real ratios - an iPhone 17 Pro Max (440x956, 3x) and an iPad Pro 11" (834x1194, 2x), Chromium launched at the device's own scale -
in both classes, on Choose your mode and on the Virtual Room's two ways in:
  (1) every tile's arrow disc is found (4 / 3 / 2 / 2): its box is read from a probe set in the disc's own grid cell;
  (2) the arrow's ink - the difference between the page with and without the disc's picture, edges placed to a fraction of a device pixel, the same method
      as check-centering - sits in the middle of the disc across and up and down within 0.3 px (the 0.5 of check-centering is what let 0.45 pass);
  (3) the arrow is the same size on every tile of a screen, and wholly inside the disc.
tools/check-centering.py holds the same discs on every screen of both classes at 3x on four sizes (the arrows are candidates of its own there).
Run:  python3 tools/check-b384-modearrows.py [--against REV|FILE.html] [--shots DIR]      (--against main 384.62 FAILS (2): the phone's 0.45 and the tablet's 0.35)"""
import sys, os, json, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
args = sys.argv[1:]
def arg(n):
    return args[args.index(n) + 1] if n in args else None
SHOTS = arg("--shots")
against = arg("--against")
sys.argv = ["check-centering.py"] + (["--against", against] if against else [])
src = open(os.path.join(HERE, "check-centering.py"), encoding="utf-8").read().split('if __name__ == "__main__":')[0]
G = {"__file__": os.path.join(HERE, "check-centering.py"), "__name__": "b384modearrows"}
exec(src, G)
np, Image = G["np"], G["Image"]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
TOL = 0.3
PROBE = """()=>{ const out=[]; document.querySelectorAll('#stage .modecards > .modecard').forEach((c,i)=>{
  const ps=getComputedStyle(c,'::after'); const p=document.createElement('i');
  p.style.cssText='display:block;grid-column:'+ps.gridColumnStart+';grid-row:'+ps.gridRowStart+';justify-self:'+ps.justifySelf+';align-self:'+ps.alignSelf+';width:'+ps.width+';height:'+ps.height+';visibility:hidden;margin:0;padding:0;border:0';
  c.appendChild(p); const r=p.getBoundingClientRect(); out.push({i, l:r.left, t:r.top, r:r.right, b:r.bottom}); p.remove(); });
  return out; }"""
HIDE = "document.head.insertAdjacentHTML('beforeend','<style id=czx>#stage .modecards > .modecard::after{background-image:none!important}</style>')"
UNHIDE = "document.getElementById('czx')?.remove()"
DEVS = [G["DEVICES"][0], ("iPad Pro 11", 834, 1194, 2, (24, 0, 20, 0), True, True, G["UA_IPAD"])]
SCREENS = [("choose your mode", "showModeSelect();", {"academy": 4, "ifc": 3}), ("virtual room", "cfg.mode='vroom'; showVirtualRoomChoice();", {"academy": 2, "ifc": 2})]

def read(pg, cdp, dev, shot):
    d = dev[3]
    for _ in range(12):
        if not pg.evaluate(G["SETTLED"]): break
        pg.wait_for_timeout(150)
    cdp.send("Animation.setPlaybackRate", {"playbackRate": 0})
    G["VIEW"]["x"], G["VIEW"]["y"] = pg.evaluate("()=>[visualViewport.pageLeft, visualViewport.pageTop]")
    boxes = pg.evaluate(PROBE)
    full = (0, 0, int(dev[1] * d), int(dev[2] * d))
    A = G["grab"](cdp, full)
    pg.evaluate(HIDE); pg.wait_for_timeout(200)
    C = G["grab"](cdp, full)
    pg.evaluate(UNHIDE)
    if shot: Image.fromarray(A.astype(np.uint8)).save(shot)
    rows = []
    for b in boxes:
        l, t, r, bt = b["l"], b["t"], b["r"], b["b"]
        if l < 0 or r > dev[1] or t < 0 or bt > dev[2]: rows.append(dict(b, off=True)); continue
        x0, y0, x1, y1 = int(math.floor(l * d)) - 2, int(math.floor(t * d)) - 2, int(math.ceil(r * d)) + 2, int(math.ceil(bt * d)) + 2
        diff = G["diffmap"](A[y0:y1, x0:x1], C[y0:y1, x0:x1]); v = diff[diff > 10]
        if v.size < 6: rows.append(dict(b, empty=True)); continue
        top = float(np.partition(v, -min(5, v.size))[-min(5, v.size)]); bb = G["bbox"](diff, max(18, .35 * top))
        cm, rm = diff.max(axis=0).astype(float), diff.max(axis=1).astype(float)
        L, T = G["edge"](cm, bb[0], 1), G["edge"](rm, bb[1], 1); R, B = G["edge"](cm, bb[2] - 1, -1), G["edge"](rm, bb[3] - 1, -1)
        ink = [(x0 + L) / d, (y0 + T) / d, (x0 + R) / d, (y0 + B) / d]
        q = lambda x: math.floor(x * d + .5) / d                      # (the disc is drawn on the device's pixel grid)
        gl, gr, gt, gb = ink[0] - q(l), q(r) - ink[2], ink[1] - q(t), q(bt) - ink[3]
        rows.append(dict(b, dx=float((gl - gr) / 2), dy=float((gt - gb) / 2), w=float(ink[2] - ink[0]), h=float(ink[3] - ink[1]), size=float(r - l), gaps=[float(x) for x in (gl, gr, gt, gb)]))
    return rows

srv, url = G["g"]["serve"](); G["URL"] = url
allrows = []
with sync_playwright() as pw:
    for dev in DEVS:
        br = pw.chromium.launch(executable_path=G["g"]["CHROME"], args=["--force-device-scale-factor=%s" % dev[3]])
        G["VIEW"]["cscale"] = 1
        for cls in ("academy", "ifc"):
            ctx, pg, cdp, errs = G["open_page"](br, dev, cls)
            pg.evaluate(G["HELPERS"]); pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(2200)
            for sname, js, want in SCREENS:
                pg.evaluate("()=>{" + js + "}"); pg.wait_for_timeout(2500)
                shot = os.path.join(SHOTS, "%s-%s-%s.png" % (dev[0].replace(" ", ""), cls, sname.replace(" ", ""))) if SHOTS else None
                if SHOTS: os.makedirs(SHOTS, exist_ok=True)
                rows = read(pg, cdp, dev, shot)
                tag = "%s (%dx), %s, %s" % (dev[0], dev[3], cls, sname)
                allrows.append((tag, want[cls], rows))
                try: pg.evaluate("()=>__czs.clear()")
                except Exception: pass
            ctx.close()
        br.close()
srv.shutdown()
for tag, want, rows in allrows:
    good = [r for r in rows if "dx" in r]
    chk("%s: all %d arrow discs found and read" % (tag, want), len(good) == want, "%d of %d (%s)" % (len(good), want, [k for r in rows for k in ("off", "empty") if k in r]))
    if not good: continue
    worst = max(max(abs(r["dx"]), abs(r["dy"])) for r in good)
    chk("%s: the arrow's ink is centred in its disc within %.1fpx, across and down (worst %.2f; across %s)" % (tag, TOL, worst, sorted({round(r["dx"], 2) for r in good})),
        worst <= TOL, [(r["i"], round(r["dx"], 2), round(r["dy"], 2)) for r in good if max(abs(r["dx"]), abs(r["dy"])) > TOL])
    sizes = {(round(r["w"], 1), round(r["h"], 1)) for r in good}
    inside = all(min(r["gaps"]) > 0.15 * r["size"] for r in good)
    chk("%s: one size of arrow on every tile (%s), wholly inside its disc" % (tag, sorted(sizes)), len(sizes) <= 2 and inside, good[0]["gaps"])
print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)
