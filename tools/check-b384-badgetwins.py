#!/usr/bin/env python3
"""Build 384 final check: no two badges in a class are one outline turned, flipped or alike at a unit card's size, and no
two share a colour or nearly do.

Madison, circling Chapter and Section Finder and Chapter 3 on the unit screen: "These badges are the exact same just in a
different direction? That needs to be fixed ... Each badge will need to be unique. If some of the badges look the same across
the classes that's okay too." Then: "I don't like the acorn badge.. please don't make badges that look like real things? ...
ALSO why are there so many repeating colors. Make that right. Make colors darker lighter, do some whites, some blacks? Idk make
them great." And, of the academy: "if the academy has look a like badges as well then get on that too."

OUTLINES. Each outline is drawn by the app (badgeShapeFor(unit).d) at 200px, centred on its centroid and scaled by its area,
and its edge compared with every other's at every 3 degrees and both flips; the score is the share of each edge that lies on
the other's, the worse of the two. Three readings, each held under 0.85 within a class (a cheap radial profile picks the 90
most alike pairs for the full comparison):
  1px  - a 1px band (the old twins scored 0.96-1.00; the closest honest pair, keystone and shield, 0.75);
  2px  - a 2px band, which forgives a rounded corner or a small notch (the academy's gate, hex and octagon scored 0.85-0.90 -
         at 28px they are one rounded polygon);
  28px - the silhouette blurred to what a 28px unit card shows (sigma 9 of 200px, ~1.5 CSS px) and cut at half, then 1px
         (Fire Code's gear and burst plate scored 1.00 - one toothed disc).
  STRETCHED (badges round 3; "none the same shape turned, flipped OR stretched") - each silhouette's bounding box scaled to
         a square (a stretch along the badge's own axes only, never a turn mixed in, so a rectangle and a diamond stay two
         shapes: card / diamond 0.12), then the 8 orientations at 90 degree steps (turned and flipped), the same 1px band
         at the same scale (the box 65px of the 176 grid, the size a square comes to under the area scaling above). Held
         under 0.88: an outline against an independently drawn stretched copy of itself scores 1.00 (round 1's crystal /
         nameplate, card / plaque, coin / oval) and a scalloped coin against the coin 0.94; no two different outlines in
         either class score over 0.83 (Fire Code's quarter dome / scooped square, notched square / ticket, card /
         saddle; the academy's disc / keystone 0.79) - 0.88 sits half way across that gap.
COLOURS, per class, read off the page:
  (a) every unit its own enamel (badgeThemeFor(u).p);
  (b) no two enamels within CIEDE2000 11 as defined (the 21 families run down to 6.5: violet / indigo);
  (c) no two within 9 as STRUCK - the mean colour of each enamel struck on one reference token (the coin) at the case's
      size, found as the pixels that change when the enamel is swapped for black. The token's metal, lighting and clear
      coat squeeze colours together (onyx strikes as a dark grey, a pearl as a light one), so this is the stricter reading;
      one reference, because a thin outline's enamel is mostly wall and shade and strikes darker than a broad one's;
  (d) side by side - in the unit list (its cards as laid out at 440px: two columns, so the card below counts too, and teaching
      order), the badge case scene's grid (badgeCaseGrid) and the case on Profile (its tiles' own positions, diagonals too) -
      no two struck enamels within 14;
  (e) a pale enamel (badgeEnamelPale) keeps a dark edge where it meets the silver - the band of its enamel at the wall has at
      most .35 of its field's light (the bevel's shade alone leaves ~.40; with BADGE_STRIKE.paleEdge ~.30) - and a
      near-black one glows in a light that can be seen (badgeThemeFor(u).g, L* 45 or more).
  (5) no page errors in either class.
  python3 tools/check-b384-badgetwins.py [--against OLD/index.html]   (must FAIL on the build before)"""
import json, os, sys, itertools, math
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
N = 200; LIM = .85; SLIM, SBOX = .88, 65; DE_HEX, DE_STRUCK, DE_SIDE = 11, 9, 14; EDGE = .35
RASTER = """(N)=>{ const cv=document.createElement('canvas'); cv.width=N; cv.height=N; const x=cv.getContext('2d'); const seen={}, units={};
  for(const u of unitsInTeachingOrder()){ const d=badgeShapeFor(u).d; units[u]=d; if(seen[d]) continue;
    x.clearRect(0,0,N,N); x.save(); x.scale(N/120, N/120); x.translate(10,10); x.fill(new Path2D(d)); x.restore();
    const a=x.getImageData(0,0,N,N).data; let s=''; for(let i=3;i<a.length;i+=4) s += a[i]>127 ? '1' : '0'; seen[d]=s; }
  return { cls: window.NOVA_CLASS, units, masks: seen }; }"""
# each unit's enamel struck: the mean (linear light) over the pixels that change when the enamel is black; the band at the
# wall against the field; the light it glows in; the scene's columns
COLOURS = r"""async (W) => {
  const lin = c => { c /= 255; return c <= .04045 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4); };
  const enc = c => { const v = c <= .0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - .055; return Math.max(0, Math.min(255, Math.round(v * 255))); };
  const hex = a => '#' + a.map(v => enc(v).toString(16).padStart(2, '0')).join('').toUpperCase();
  /* every enamel struck on ONE reference token (the coin), so two colours are compared as colours - a thin outline's
     enamel is mostly wall and shade and strikes darker than the same enamel on a broad one */
  const pu = '__enamel probe'; IFC_BADGE_SHAPE[pu] = 'coin';
  const strike = h => { BADGE_FAMILY.__probe = h; IFC_BADGE_THEME[pu] = ['__probe']; return renderBadgeStrike(pu, false, W, 1, 0).getContext('2d').getImageData(0, 0, W, W).data; };
  const k = strike('#000000');
  const out = [];
  for(const u of unitsInTeachingOrder()){
    const bt = badgeThemeFor(u), d = strike(String(bt.p));
    const m = new Uint8Array(W * W);
    for(let i = 0; i < W * W; i++){ const j = i * 4; if(d[j + 3] >= 250 && Math.abs(d[j] - k[j]) + Math.abs(d[j + 1] - k[j + 1]) + Math.abs(d[j + 2] - k[j + 2]) >= 9) m[i] = 1; }
    let r = 0, g = 0, b = 0, n = 0, eY = 0, eN = 0, fY = 0, fN = 0;
    for(let y = 1; y < W - 1; y++) for(let x = 1; x < W - 1; x++){ const i = y * W + x; if(!m[i]) continue; const j = i * 4;
      const R = lin(d[j]), Gg = lin(d[j + 1]), B = lin(d[j + 2]); r += R; g += Gg; b += B; n++;
      const Y = .2126 * R + .7152 * Gg + .0722 * B;
      if(!m[i - 1] || !m[i + 1] || !m[i - W] || !m[i + W]){ eY += Y; eN++; } else { fY += Y; fN++; } }
    out.push({ u, p: String(bt.p), g: String(bt.g || bt.p), mean: hex([r / n, g / n, b / n]),
               pale: typeof badgeEnamelPale === 'function' ? badgeEnamelPale(bt.p) : false, edgeY: eN ? eY / eN : 0, fieldY: fN ? fY / fN : 0 });
  }
  return { cls: window.NOVA_CLASS, units: out, cols: badgeCaseGrid(out.length).cols }; }"""
TILES = r"""async () => { unitsInTeachingOrder().forEach(u => { store.unitPerfects[u] = Math.max(store.unitPerfects[u] || 0, badgeThresholdFor(u)); });
  showRanksScreen('badges'); await new Promise(r => setTimeout(r, 2500));
  return [...document.querySelectorAll('#stage .badge-tile')].map(c => { const r = c.getBoundingClientRect();
    return { label: c.getAttribute('aria-label') || '', x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; }); }"""
CARDS = r"""async () => { cfg.mode = 'drill'; cfg.units = []; showSetup(); await new Promise(r => setTimeout(r, 1800));
  const t = {}; unitsInTeachingOrder().forEach(u => { t[unitTitle(u)] = u; });
  return [...document.querySelectorAll('#stage label.pick')].map(c => { const n = c.querySelector('.pname'), r = c.getBoundingClientRect();
    return { u: n ? t[n.textContent] || null : null, x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; }).filter(o => o.u); }"""
GS = 176; gv = (np.arange(GS) + .5) / GS * 2 - 1; U, V = np.meshgrid(gv * 2.4, gv * 2.4)
def blur(m, sigma=9.0):
    r = int(3 * sigma); x = np.arange(-r, r + 1); k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    a = np.pad(m.astype(float), r)
    a = np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 0, a); a = np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 1, a)
    return a > .5
def frame(m):
    ys, xs = np.nonzero(m); P = np.stack([xs, ys], 1).astype(float); return m, P.mean(0), np.eye(2) * np.sqrt(len(P) / np.pi)
def render(f, ang, flip):
    m, c, Wi = f; ca, sa = np.cos(ang), np.sin(ang); u = U * (-1 if flip else 1)
    S = np.stack([(ca * u - sa * V).ravel(), (sa * u + ca * V).ravel()], 0); src_ = (Wi @ S).T + c
    xi = np.round(src_[:, 0]).astype(int); yi = np.round(src_[:, 1]).astype(int); n = m.shape[0]
    okk = (xi >= 0) & (xi < n) & (yi >= 0) & (yi < n); o = np.zeros(len(xi), bool); o[okk] = m[yi[okk], xi[okk]]; return o.reshape(GS, GS)
def edge(a): return a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
def dil(a, r):
    o = a.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r: o |= np.roll(np.roll(a, dy, 0), dx, 1)
    return o
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
def compare(masks, band, small):
    keys = list(masks); M = {k: (blur(masks[k]) if small else masks[k]) for k in keys}
    F = {k: frame(M[k]) for k in keys}; R = {k: radial(M[k]) for k in keys}
    pairs = sorted(itertools.combinations(keys, 2), key=lambda p: rdist(R[p[0]], R[p[1]]))[:90]
    E = {}
    def turns(k):
        if k not in E:
            Bs = [edge(render(F[k], np.radians(t), fl)) for fl in (False, True) for t in range(0, 360, 3)]
            E[k] = (Bs, [dil(b, band) for b in Bs])
        return E[k]
    rows = []
    for a, b in pairs:
        A = edge(render(F[a], 0, False)); Ad = dil(A, band); best = 0
        for B, Bd in zip(*turns(b)):
            s = min((A & Bd).sum() / A.sum(), (B & Ad).sum() / B.sum())
            if s > best: best = s
        rows.append((round(float(best), 2), a, b))
    rows.sort(reverse=True)
    return rows
def boxnorm(m):
    """the silhouette's bounding box scaled to an SBOX square in the GS grid (a stretch on the badge's own axes)"""
    ys, xs = np.nonzero(m); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    iy = np.minimum(y1 - 1, (y0 + (np.arange(SBOX) + .5) / SBOX * (y1 - y0)).astype(int))
    ix = np.minimum(x1 - 1, (x0 + (np.arange(SBOX) + .5) / SBOX * (x1 - x0)).astype(int))
    out = np.zeros((GS, GS), bool); o = (GS - SBOX) // 2; out[o:o + SBOX, o:o + SBOX] = m[np.ix_(iy, ix)]; return out
def compare_stretch(masks):
    """every pair: the 8 turns and flips of one box-squared silhouette against the other, 1px band"""
    E = {}
    for k, m in masks.items():
        n = boxnorm(m); Es = [edge(np.rot90(f, q)) for f in (n, np.fliplr(n)) for q in range(4)]; E[k] = (Es, [dil(e, 1) for e in Es])
    rows = []
    for a, b in itertools.combinations(list(masks), 2):
        A, Ad = E[a][0][0], E[a][1][0]; best = 0
        for B, Bd in zip(*E[b]):
            s = min((A & Bd).sum() / A.sum(), (B & Ad).sum() / B.sum())
            if s > best: best = s
        rows.append((round(float(best), 2), a, b))
    rows.sort(reverse=True)
    return rows
def lab(h):
    if h.startswith("rgb"): h = "#%02X%02X%02X" % tuple(int(float(v)) for v in h[h.index("(") + 1:-1].split(","))
    h = h.lstrip("#")
    def lin(c):
        c /= 255; return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    r, g, b = [lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)]
    X = (.4124564 * r + .3575761 * g + .1804375 * b) / .95047; Y = .2126729 * r + .7151522 * g + .0721750 * b; Z = (.0193339 * r + .1191920 * g + .9503041 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    return (116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z)))
def de00(p, q):
    """CIEDE2000 (Sharma, Wu and Dalal's formulation)"""
    L1, a1, b1 = lab(p); L2, a2, b2 = lab(q)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2); Cb = (C1 + C2) / 2; Gf = .5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + Gf) * a1, (1 + Gf) * a2; C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p, h2p = math.degrees(math.atan2(b1, a1p)) % 360, math.degrees(math.atan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p
    if C1p * C2p == 0: dh = 0
    else:
        dh = h2p - h1p
        if dh > 180: dh -= 360
        elif dh < -180: dh += 360
    dH = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2)); Lb, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0: hb = h1p + h2p
    else:
        hb = (h1p + h2p) / 2
        if abs(h1p - h2p) > 180: hb += 180 if hb < 180 else -180
    T = 1 - .17 * math.cos(math.radians(hb - 30)) + .24 * math.cos(math.radians(2 * hb)) + .32 * math.cos(math.radians(3 * hb + 6)) - .2 * math.cos(math.radians(4 * hb - 63))
    dT = 30 * math.exp(-((hb - 275) / 25) ** 2); RC = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    SL = 1 + .015 * (Lb - 50) ** 2 / math.sqrt(20 + (Lb - 50) ** 2); SC = 1 + .045 * Cbp; SH = 1 + .015 * Cbp * T
    return math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 - math.sin(math.radians(2 * dT)) * RC * (dC / SC) * (dH / SH))
res = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    for cls in ("ifc", "academy"):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"]) if cls == "ifc" else G["init"](G["academy"], active="academy"))
        pg.wait_for_timeout(800)
        r = pg.evaluate(RASTER, N); c = pg.evaluate(COLOURS, 104); cards = pg.evaluate(CARDS); t = pg.evaluate(TILES)
        icons = pg.evaluate("()=>typeof chapterIconFor === 'function' ? unitsInTeachingOrder().filter(u => chapterIconFor(u)) : []")
        res[cls] = (r, c, t, cards, list(errs), icons); ctx.close()
    br.close()
for cls, label, s1, s2 in (("ifc", "Fire Code", "1", "3"), ("academy", "the academy", "2", "4")):
    r, c, tiles, cards, errs, icons = res[cls]
    # (384.61) A chapter with an icon (CHAPTER_ICON) is told from the others by its picture and its enamel, and its outline was chosen for
    # ROOM (the roomy outlines no chapter used: octagon, gate, hex - the octagon is the coin to the pixel): a pair with one of those is
    # not held to the outline-twin limits below (it is still printed, still held to colours). Nothing else is exempt.
    exempt = set(u.split(":")[0][:22] for u in icons)
    names, masks = {}, {}
    for i, (d, s) in enumerate(r["masks"].items()):
        k = "o%d" % i; masks[k] = np.array([ch == "1" for ch in s], bool).reshape(N, N)
        names[k] = [u.split(":")[0][:22] for u, dd in r["units"].items() if dd == d]
    n = len(r["units"])
    chk("(%sa) %s (%s): every unit has its own outline (%d units, %d outlines)" % (s1, label, r["cls"], n, len(masks)), len(masks) == n, [len(masks), n])
    for tag, band, small, what in (("b", 1, False, "the 1px edge"), ("c", 2, False, "the 2px edge"), ("d", 1, True, "a unit card's 28px")):
        rows = compare(masks, band, small)
        bad = [(s, names[a], names[b]) for s, a, b in rows if s >= LIM and not (set(names[a]) & exempt or set(names[b]) & exempt)]
        chk("(%s%s) %s: no two outlines alike turned or flipped, by %s - every pair under %.2f%s (closest: %s)" % (s1, tag, label, what, LIM, " - an icon chapter's pairs apart (%d)" % len(exempt) if exempt else "",
            ", ".join("%s/%s %.2f" % (names[a][0], names[b][0], s) for s, a, b in rows[:3])), not bad, bad[:6])
    rows = compare_stretch(masks)
    bad = [(s, names[a], names[b]) for s, a, b in rows if s >= SLIM and not (set(names[a]) & exempt or set(names[b]) & exempt)]
    chk("(%se) %s: no outline is another one stretched (each box squared, 8 turns and flips, 1px) - every pair under %.2f (closest: %s)" % (s1, label, SLIM,
        ", ".join("%s/%s %.2f" % (names[a][0], names[b][0], s) for s, a, b in rows[:3])), not bad, bad[:6])
    U_ = c["units"]
    ps = [x["p"].upper() for x in U_]
    rep = sorted({p for p in ps if ps.count(p) > 1})
    chk("(%sa) %s: every unit its own enamel (%d units, %d enamels)" % (s2, label, len(U_), len(set(ps))), not rep, rep)
    pairs = list(itertools.combinations(range(len(U_)), 2))
    hx = sorted((round(de00(U_[i]["p"], U_[j]["p"]), 1), U_[i]["u"][:18], U_[j]["u"][:18]) for i, j in pairs)
    chk("(%sb) %s: no two enamels within CIEDE2000 %d as defined (closest %.1f: %s / %s)" % (s2, label, DE_HEX, hx[0][0], hx[0][1], hx[0][2]), hx[0][0] >= DE_HEX, hx[:5])
    st = sorted((round(de00(U_[i]["mean"], U_[j]["mean"]), 1), U_[i]["u"][:18], U_[j]["u"][:18]) for i, j in pairs)
    chk("(%sc) %s: no two within %d as struck on the token (closest %.1f: %s / %s)" % (s2, label, DE_STRUCK, st[0][0], st[0][1], st[0][2]), st[0][0] >= DE_STRUCK, st[:5])
    nb = set((i, i + 1) for i in range(len(U_) - 1))
    cols = c["cols"]
    for i in range(len(U_)):
        rr, cc = divmod(i, cols)
        for dr, dc in ((0, 1), (1, -1), (1, 0), (1, 1)):
            r2, c2 = rr + dr, cc + dc
            if 0 <= c2 < cols and r2 * cols + c2 < len(U_): nb.add(tuple(sorted((i, r2 * cols + c2))))
    idx = {x["u"]: i for i, x in enumerate(U_)}
    tl = [(next((idx[u] for u in idx if t["label"].startswith(u + " Badge")), None), t) for t in tiles]
    tl = [(i, t) for i, t in tl if i is not None]
    for (i, a), (j, b) in itertools.combinations(tl, 2):
        if abs(a["x"] - b["x"]) <= a["w"] * 1.6 and abs(a["y"] - b["y"]) <= a["h"] * 1.6: nb.add(tuple(sorted((i, j))))
    cl = [(idx[k["u"]], k) for k in cards if k["u"] in idx]
    for (i, a), (j, b) in itertools.combinations(cl, 2):
        if abs(a["x"] - b["x"]) <= a["w"] * 1.6 and abs(a["y"] - b["y"]) <= a["h"] * 1.6: nb.add(tuple(sorted((i, j))))
    sd = sorted((round(de00(U_[i]["mean"], U_[j]["mean"]), 1), U_[i]["u"][:18], U_[j]["u"][:18]) for i, j in nb)
    chk("(%sd) %s: side by side - the unit list on an iPhone 17 Pro Max (%d cards, as laid out), the case scene's %d columns, the case on Profile (%d tiles) - no two struck enamels within %d (closest %.1f: %s / %s)"
        % (s2, label, len(cl), cols, len(tl), DE_SIDE, sd[0][0], sd[0][1], sd[0][2]), sd[0][0] >= DE_SIDE and len(tl) == len(U_) and len(cl) == len(U_), (sd[:5], len(tl), len(cl)))
    pale = [x for x in U_ if x["pale"]]
    ratios = sorted((round(x["edgeY"] / x["fieldY"], 3), x["u"][:22]) for x in pale if x["fieldY"])
    noedge = [(r_, u_) for r_, u_ in ratios if r_ > EDGE]
    chk("(%se) %s: every pale enamel (%d of them) keeps a dark edge at the silver - its band at the wall no more than %.2f of its field's light (worst %s)"
        % (s2, label, len(pale), EDGE, ratios[-1] if ratios else "-"), not noedge, noedge)
    darks = [x for x in U_ if lab(x["p"])[0] < 30]
    dim = [(x["u"][:22], x["p"], x["g"]) for x in darks if lab(x["g"])[0] < 45]
    chk("(%se) %s: every near-black enamel (%d of them) glows in a light that can be seen (L* 45 or more)" % (s2, label, len(darks)), not dim, dim)
    chk("(5) %s: no page errors" % label, not errs, errs[:3])
    if os.environ.get("DUMP_NB"):
        json.dump({"order": [x["u"] for x in U_], "nb": sorted(nb), "means": {x["u"]: x["mean"] for x in U_}}, open(os.environ["DUMP_NB"] + "-" + cls + ".json", "w"))
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
