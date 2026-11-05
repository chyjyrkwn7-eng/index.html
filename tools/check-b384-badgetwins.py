#!/usr/bin/env python3
"""Build 384 final check: no two Fire Code badges are one outline turned or flipped.

Madison, circling Chapter and Section Finder and Chapter 3 on the unit screen: "These badges are the exact same just in a
different direction? That needs to be fixed ... Each badge will need to be unique. If some of the badges look the same across
the classes that's okay too." check-b384-ifcbadges compared every pair of outlines in ONE orientation, so a hexagon stood on end
(the crystal) and laid on its side (the nameplate) passed as two shapes; so did the diamond and the tile (a square turned 45
degrees), the card and the plaque, and - at a unit card's 28px, where rounded corners and small scallops vanish - the coin, the
octagon and the seal.
Each outline is drawn by the app (badgeShapeFor(unit).d) at 200px, centred on its centroid and scaled by its area, and its edge
is compared with every other's at every 3 degrees and both flips (a 1px band); the score is the share of each edge that lies on
the other's, the worse of the two. A cheap radial profile picks the 80 most alike pairs for the full comparison.
(1) Fire Code: every chapter has its own outline, and no two outlines score 0.9 or more (the old twins scored 0.96-1.00;
    the closest honest pair, the academy's keystone and shield, 0.75);
(2) the academy's own 24 are unchanged by this (listed for reference, not held to it - they are another class);
(3) no page errors.
  python3 tools/check-b384-badgetwins.py [--against OLD/index.html]   (must FAIL on the build before)"""
import json, os, sys, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384bt"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
N = 200
RASTER = """(N)=>{ const cv=document.createElement('canvas'); cv.width=N; cv.height=N; const x=cv.getContext('2d'); const seen={}, units={};
  for(const u of unitsInTeachingOrder()){ const d=badgeShapeFor(u).d; units[u]=d; if(seen[d]) continue;
    x.clearRect(0,0,N,N); x.save(); x.scale(N/120, N/120); x.translate(10,10); x.fill(new Path2D(d)); x.restore();
    const a=x.getImageData(0,0,N,N).data; let s=''; for(let i=3;i<a.length;i+=4) s += a[i]>127 ? '1' : '0'; seen[d]=s; }
  return { cls: window.NOVA_CLASS, units, masks: seen }; }"""
GS = 176; gv = (np.arange(GS) + .5) / GS * 2 - 1; U, V = np.meshgrid(gv * 2.4, gv * 2.4)
def frame(m):
    ys, xs = np.nonzero(m); P = np.stack([xs, ys], 1).astype(float); c = P.mean(0)
    return m, c, np.eye(2) * np.sqrt(len(P) / np.pi)
def render(f, ang, flip):
    m, c, Wi = f; ca, sa = np.cos(ang), np.sin(ang); u = U * (-1 if flip else 1)
    S = np.stack([(ca * u - sa * V).ravel(), (sa * u + ca * V).ravel()], 0); src_ = (Wi @ S).T + c
    xi = np.round(src_[:, 0]).astype(int); yi = np.round(src_[:, 1]).astype(int); n = m.shape[0]
    okk = (xi >= 0) & (xi < n) & (yi >= 0) & (yi < n); o = np.zeros(len(xi), bool); o[okk] = m[yi[okk], xi[okk]]; return o.reshape(GS, GS)
def edge(a): return a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
def dil1(a): return a | np.roll(a, 1, 0) | np.roll(a, -1, 0) | np.roll(a, 1, 1) | np.roll(a, -1, 1)
def radial(m):
    ys, xs = np.nonzero(m); c = np.array([xs.mean(), ys.mean()]); r = np.sqrt(len(xs) / np.pi); out = []
    for t in np.radians(np.arange(0, 360, 2)):
        d = np.arange(0, 3 * r, .5); px = np.round(c[0] + d * np.cos(t)).astype(int); py = np.round(c[1] + d * np.sin(t)).astype(int)
        okk = (px >= 0) & (px < N) & (py >= 0) & (py < N); hit = d[okk][m[py[okk], px[okk]]]
        out.append(hit.max() / r if len(hit) else 0)
    return np.array(out)
def rdist(a, b):
    best = 9
    for bb in (b, b[::-1]):
        for k in range(len(a)): best = min(best, np.abs(a - np.roll(bb, k)).mean())
    return best
def compare(masks, label, hold):
    keys = list(masks); F = {k: frame(masks[k]) for k in keys}; R = {k: radial(masks[k]) for k in keys}
    pairs = sorted(itertools.combinations(keys, 2), key=lambda p: rdist(R[p[0]], R[p[1]]))[:80]
    E = {}
    def edges(k):
        if k not in E: E[k] = [(edge(render(F[k], np.radians(t), fl))) for fl in (False, True) for t in range(0, 360, 3)]
        return E[k]
    rows = []
    for a, b in pairs:
        A = edge(render(F[a], 0, False)); Ad = dil1(A); best = 0
        for B in edges(b):
            s = min((A & dil1(B)).sum() / A.sum(), (B & Ad).sum() / B.sum())
            if s > best: best = s
        rows.append((round(float(best), 2), a, b))
    rows.sort(reverse=True)
    return rows
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
    pg.wait_for_timeout(800)
    r = pg.evaluate(RASTER, N)
    ctx.close()
    ctx, pg, errs2 = G["page"](br, G["init"](G["academy"], active="academy"))
    pg.wait_for_timeout(800)
    ra = pg.evaluate(RASTER, N)
    ctx.close(); br.close()
names = {}
def masks_of(res):
    out = {}
    for i, (d, s) in enumerate(res["masks"].items()):
        k = "o%d" % i; out[k] = np.array([c == "1" for c in s], bool).reshape(N, N)
        names[k] = [u.split(":")[0] for u, dd in res["units"].items() if dd == d]
    return out
mi = masks_of(r)
chk("(1a) Fire Code (%s): every chapter has its own outline (%d chapters, %d outlines)" % (r["cls"], len(r["units"]), len(mi)),
    r["cls"] == "ifc" and len(mi) == len(r["units"]), [len(r["units"]), len(mi)])
rows = compare(mi, "ifc", True)
twins = [(s, names[a], names[b]) for s, a, b in rows if s >= .9]
chk("(1b) Fire Code: no two outlines are one turned or flipped (closest: %s)" % ", ".join("%s/%s %.2f" % (names[a][0], names[b][0], s) for s, a, b in rows[:4]),
    not twins, twins)
names_a = {}
ma = masks_of(ra)
rows_a = compare(ma, "academy", False)
print("     (2) the academy's own %d, for reference: closest %s" % (len(ma), ", ".join("%s/%s %.2f" % (names[a][0], names[b][0], s) for s, a, b in rows_a[:4])))
chk("(3) no page errors", not errs and not errs2, (errs + errs2)[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
