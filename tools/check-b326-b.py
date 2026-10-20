#!/usr/bin/env python3
"""Build 326, package b: the badges and the badge case.

Madison (Oct 18, second list):
  "During the badge cutscene, the top opening part is glitched and isn't
   there, fix that. The wording on the back of the badge is not cohesive
   for all of them. Some say class 26e some don't. I also don't like the way
   the engraving looks, doesn't look legit. The badges look good but the
   edges on the side don't look good. I think they could look better still.
   I think the case could LOOK better too. We want these to look so good."

Every check here was written against build 325 (5869856), where each one
fails; run it there with --against to watch it:

  python3 tools/check-b326-b.py
  python3 tools/check-b326-b.py --against /path/to/old/index.html
  B326B_ONLY=ABC python3 tools/check-b326-b.py      (some sections)

On both reference devices where a device matters (iPhone 17 Pro Max
440x956, iPad Pro 11" 834x1194, installed):
  A. ONE WORDING RULE: every one of the sixteen backs carries the same
     lines - the unit's name and CLASS 26E, parted by a rule (on the ring,
     by the turn round it) - read off the plan the renderer cuts from.
  B. THE WORDS ARE CUT, NOT PAINTED: inside the letters, the wall that faces
     the light (the lower-right edge of a stroke) is bright and the one
     that faces away is dark - at least WALL_SPLIT levels apart, and the lit
     wall at least LIT_OVER_FLOOR over the cut's floor. A black fill laid
     edge to edge (the old back) has neither.
  C. THE SIDE IS LIT BY WHICH WAY IT FACES: round every badge's outline,
     the side's light follows the outline's normal (up-facing stretches
     brighter than down-facing ones at the same height), not a ramp down
     the shape's box - a least-squares fit of the side's light on the
     normal and on the height, the normal's term at least SIDE_NORMAL.
  D. THE CUTSCENE'S LID IS FLAT LEAVES: nothing inside the swinging lid is
     itself a 3D container, the lid's inside is not coplanar with the tray,
     and shut, each hooked hasp still shows its staple through its slot.
  E. THE LID IS THERE IN EVERY FRAME of its opening (stepped at 20 fps from
     the crack to open): its front edge is painted end to end, and every
     face of it that faces the camera is painted over its middle.
  F. THE CASE LOOKS FINISHED: the lid's cushion is plain - no quilt (moved
     in 327: the tufting was "the weird pattern of the case on the inside top
     part") - and the lid's outside carries a row of stitching, in the
     cutscene's case and the Badges tab's alike.
"""
import importlib.util
import io
import os
import sys

from playwright.sync_api import sync_playwright

_spec = importlib.util.spec_from_file_location(
    "cb", os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
check, booted, USED_ACCOUNT, FAILURES = cb.check, cb.booted, cb.USED_ACCOUNT, cb.FAILURES

DEVICES = [("17 Pro Max", 440, 956, 2), ("iPad Pro 11", 834, 1194, 2)]
ONLY = os.environ.get("B326B_ONLY", "ABCDEF")
WALL_SPLIT = 30       # levels, lit wall over shaded wall (median)
LIT_OVER_FLOOR = 25   # levels, lit wall over the cut's floor (median)
SIDE_NORMAL = 25      # levels per unit of the normal's y, the side's light

STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){},
       addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""

SEED = """() => { const units = topicsIn(QUESTIONS).filter(u => u !== 'Identity Crimes');
  store.unitPerfects = store.unitPerfects || {}; units.slice(0, 4).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
  store.unitPerfects['Identity Crimes'] = badgeThresholdFor('Identity Crimes');
  store.badgeCleanedAt = {}; Object.keys(store.unitPerfects).forEach(u => store.badgeCleanedAt[u] = Date.now());
  store.pendingBadgeUnlocks = []; theme.muteBanners = false; theme.reduceMotion = false; applyTheme();
  document.querySelectorAll('#pushing-update,#intro-pop,.app-banner,.daily-alert,.nova-talk').forEach(n => n.remove()); }"""

# ---------------------------------------------------------------- A + B
BACKS = r"""async (W) => {
  const units = unitsInTeachingOrder(), out = { units: {} };
  const load = src => new Promise(r => { const im = new Image(); im.onload = () => r(im); im.onerror = () => r(null); im.src = src; });
  /* the gate's own distance transform (a 3-4 chamfer, /3): not the app's */
  const dist = (M, W) => { const d = new Float32Array(W * W); for(let i = 0; i < d.length; i++) d[i] = M[i] > .5 ? 1e6 : 0;
    const at = (x, y) => x < 0 || y < 0 || x >= W || y >= W ? 0 : d[y * W + x];
    for(let y = 0; y < W; y++) for(let x = 0; x < W; x++){ const i = y * W + x; if(!d[i]) continue;
      d[i] = Math.min(d[i], at(x - 1, y) + 3, at(x, y - 1) + 3, at(x - 1, y - 1) + 4, at(x + 1, y - 1) + 4); }
    for(let y = W - 1; y >= 0; y--) for(let x = W - 1; x >= 0; x--){ const i = y * W + x; if(!d[i]) continue;
      d[i] = Math.min(d[i], at(x + 1, y) + 3, at(x, y + 1) + 3, at(x + 1, y + 1) + 4, at(x - 1, y + 1) + 4); }
    for(let i = 0; i < d.length; i++) d[i] /= 3; return d; };
  const med = a => { a = a.slice().sort((p, q) => p - q); return a.length ? a[Math.floor(a.length / 2)] : 0; };
  for(const u of units){
    const plan = badgeBackPlan(u);
    const strs = (plan.items || []).filter(it => it.s).map(it => String(it.s));
    const hasClass = strs.some(s => /^CLASS 26E$/.test(s)) || strs.join('').replace(/[^A-Z0-9]/g, '').endsWith('CLASS26E');
    /* a ring's two lines are parted by the turn round the ring, not a rule */
    const hasRule = plan.mode === 'arc' || (plan.items || []).some(it => it.rule);
    const nameUp = String(u).toUpperCase().replace(/[^A-Z0-9]/g, '');
    const inked = strs.join('').replace(/[^A-Z0-9]/g, '');
    const hasName = inked.includes(nameUp);
    /* the class line's ink, rendered: its own mask band */
    const g = badgeStrikeGeometry(badgeShapeFor(u));
    const M = badgeBackLayout(u, g, W);
    const im = await load(badgeBackFaceURL(u, W, 0)); if(!im){ out.units[u] = { err: 'no image' }; continue; }
    const cv = document.createElement('canvas'); cv.width = cv.height = W; const c2 = cv.getContext('2d'); c2.drawImage(im, 0, 0);
    const px = c2.getImageData(0, 0, W, W).data, L = i => .299 * px[i * 4] + .587 * px[i * 4 + 1] + .114 * px[i * 4 + 2];
    const D = dist(M, W);
    /* walls: inside the letters, within ~2px of the edge; which way the edge
       lies from here is the distance's gradient */
    const lit = [], shade = [], floor = [];
    for(let y = 2; y < W - 2; y++) for(let x = 2; x < W - 2; x++){ const i = y * W + x, d = D[i]; if(d <= 0) continue;
      const gx = D[i + 1] - D[i - 1], gy = D[i + W] - D[i - W], gl = Math.hypot(gx, gy);
      if(d >= .8 && d <= 2.2 && gl > .5){ /* inward direction */ const k = (gx * -.6 + gy * -.8) / gl;
        if(k > .55) lit.push(L(i)); else if(k < -.55) shade.push(L(i)); }
      else if(d >= 3.2) floor.push(L(i)); }
    out.units[u] = { cls: hasClass, rule: hasRule, name: hasName, mode: plan.mode,
      lit: Math.round(med(lit)), shade: Math.round(med(shade)), floor: floor.length > 20 ? Math.round(med(floor)) : null, n: [lit.length, shade.length, floor.length] };
  }
  return out; }"""


def section_ab(br):
    print("\nA-B. the backs: one wording rule on all sixteen, and words cut into the metal")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=STANDALONE, dpr=1)
    pg.evaluate(SEED)
    r = pg.evaluate(BACKS, 600)
    us = r["units"]
    if "A" in ONLY:
        missing = [u for u, v in us.items() if not (v.get("cls") and v.get("rule") and v.get("name"))]
        check("every one of the %d backs carries the unit's name, a rule and CLASS 26E" % len(us),
              len(us) >= 16 and not missing, {"missing": missing[:8]})
    if "B" in ONLY:
        bad = []
        for u, v in us.items():
            if v.get("err") or v["lit"] - v["shade"] < WALL_SPLIT or (v["floor"] is not None and v["lit"] - v["floor"] < LIT_OVER_FLOOR):
                bad.append((u[:22], v.get("lit"), v.get("shade"), v.get("floor")))
        worst = min(((v["lit"] - v["shade"]), u[:22]) for u, v in us.items() if not v.get("err"))
        check("every back's words are cut: the wall facing the light bright, the one facing away dark (%d+ apart), the lit wall %d+ over the floor"
              % (WALL_SPLIT, LIT_OVER_FLOOR), not bad, {"failing": bad[:6], "smallest split": worst})
    ctx.close()


# ---------------------------------------------------------------- C
SIDE = r"""async () => {
  const units = unitsInTeachingOrder(), W = 256, rows = [];
  const load = src => new Promise(r => { const im = new Image(); im.onload = () => r(im); im.onerror = () => r(null); im.src = src; });
  for(const u of units){
    const im = await load(badgeEdgeURL(u, 1, 0)); if(!im) continue;
    const cv = document.createElement('canvas'); cv.width = cv.height = W; const c = cv.getContext('2d'); c.drawImage(im, 0, 0, W, W);
    const p = c.getImageData(0, 0, W, W).data, A = i => p[i * 4 + 3] / 255, L = i => .299 * p[i * 4] + .587 * p[i * 4 + 1] + .114 * p[i * 4 + 2];
    /* the outline: a band just inside the silhouette; its outward normal from the alpha's gradient, a few pixels across */
    for(let y = 4; y < W - 4; y++) for(let x = 4; x < W - 4; x++){ const i = y * W + x; if(A(i) < .98) continue;
      const gx = A(i - 3) - A(i + 3), gy = A(i - 3 * W) - A(i + 3 * W), gl = Math.hypot(gx, gy);
      if(gl < .5) continue;
      rows.push([L(i), gy / gl, y / W]); } }
  /* least squares: lum = a * ny + b * y + c (ny < 0 faces up) */
  let S = [[0,0,0],[0,0,0],[0,0,0]], T = [0,0,0];
  rows.forEach(([l, n, y]) => { const v = [n, y, 1]; for(let r = 0; r < 3; r++){ T[r] += v[r] * l; for(let q = 0; q < 3; q++) S[r][q] += v[r] * v[q]; } });
  const solve = (M, b) => { M = M.map((r, i) => r.concat([b[i]])); for(let i = 0; i < 3; i++){ let m = i; for(let r = i + 1; r < 3; r++) if(Math.abs(M[r][i]) > Math.abs(M[m][i])) m = r; [M[i], M[m]] = [M[m], M[i]];
    for(let r = 0; r < 3; r++){ if(r === i) continue; const f = M[r][i] / M[i][i]; for(let q = i; q < 4; q++) M[r][q] -= f * M[i][q]; } } return M.map((r, i) => r[3] / r[i]); };
  const [a, b] = solve(S, T);
  return { n: rows.length, normal: +(-a).toFixed(1), height: +b.toFixed(1) }; }"""


def section_c(br):
    print("\nC. the badge's side: lit by which way each stretch of it faces")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=STANDALONE, dpr=1)
    pg.evaluate(SEED)
    r = pg.evaluate(SIDE)
    check("round all sixteen outlines the side's light follows its normal (up-facing brighter), not a ramp down the box: %d+ levels per unit of normal"
          % SIDE_NORMAL, r["n"] > 2000 and r["normal"] >= SIDE_NORMAL, r)
    ctx.close()


# ---------------------------------------------------------------- D + E
STRUCT = r"""() => {
  const lid = document.querySelector('.bc-scene .bc-lid'); if(!lid) return null;
  const nested = [...lid.querySelectorAll('*')].filter(e => getComputedStyle(e).transformStyle === 'preserve-3d').map(e => e.className.split(' ')[0]);
  const li = document.querySelector('.bc-scene .bc-lid-in'), m = new DOMMatrix(getComputedStyle(li).transform);
  const hitOn = document.createElement('style'); hitOn.textContent = '.bc-stage, .bc-stage *{ pointer-events:auto !important; }'; document.head.appendChild(hitOn);
  const over = [...document.querySelectorAll('.bc-scene .bc-latch')].map(l => {
    const h = l.querySelector('.nova-case-hasp'); if(!h) return false; const hb = h.getBoundingClientRect();
    const st = l.querySelector('.ncase-staple-over') || (document.querySelector('.bc-keeper-' + (l.classList.contains('bc-latch-l') ? 'l' : 'r') + ' .nova-case-staple'));
    if(!st) return false; const sb = st.getBoundingClientRect(), x = (sb.left + sb.right) / 2, y = (sb.top + sb.bottom) / 2;
    const top = document.elementFromPoint(x, y);
    return !!(top && top.closest && top.closest('.nova-case-staple, .ncase-staple-over')) && x > hb.left && x < hb.right && y > hb.top && y < hb.bottom; });
  hitOn.remove();
  return { nested, lidInZ: +m.m43.toFixed(2), hooked: over }; }"""

FACES = r"""() => {
  const q = s => document.querySelector('.bc-scene ' + s);
  const R = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  /* which face is turned to the camera: the lid's angle on its hinge plus
     the camera's tilt (the case's rotateX) - the outside's normal is
     cos(lid + tilt) towards you; the inside's the opposite */
  const ang = e => { const m = new DOMMatrix(getComputedStyle(e).transform); return Math.atan2(m.m23, m.m22); };
  const c = Math.cos(ang(q('.bc-lid')) + ang(q('.bc-case')));
  return { front: R(q('.bc-lid-front')), lin: R(q('.bc-lid-in')), lout: R(q('.bc-lid-out')), vis: [c < -.3, c > .3], c: +c.toFixed(2) }; }"""


def section_de(br):
    print("\nD-E. the cutscene's lid: flat leaves, and there in every frame of its opening")
    from PIL import Image
    for (dev, w, h, dpr) in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=STANDALONE, dpr=dpr)
        pg.evaluate(SEED)
        clk = cb._StepperS(pg)
        pg.evaluate("() => { playBadgeCaseScene(['Identity Crimes'], () => {}); }")
        T = pg.evaluate("() => BC_T")
        while clk.t < 7.6:
            clk.step(0.1)
        if "D" in ONLY:
            s = pg.evaluate(STRUCT)
            check(f"{dev}: the lid is flat leaves - nothing inside it is a 3D container, its inside is off the tray's plane, and shut each hasp shows its staple through its slot",
                  bool(s) and not s["nested"] and abs(s["lidInZ"]) >= .3 and len(s["hooked"]) == 2 and all(s["hooked"]), s)
        if "E" in ONLY:
            while clk.t < T["crack"] / 1000:
                clk.step(0.1)
            broken, seen, faces = [], 0, 0
            while clk.t < T["open"] / 1000 + 2.6:
                clk.step(1 / 20)
                f = pg.evaluate(FACES)
                im = Image.open(io.BytesIO(pg.screenshot())).convert("L")
                fr = f["front"]
                if fr[3] - fr[1] >= 3:
                    seen += 1
                    y = int((fr[1] + fr[3]) / 2 * dpr)
                    xs = range(int((fr[0] + (fr[2] - fr[0]) * .1) * dpr), int((fr[0] + (fr[2] - fr[0]) * .9) * dpr))
                    row = [im.getpixel((x, y)) for x in xs if 0 <= x < im.width and 0 <= y < im.height]
                    dark = sum(1 for v in row if v < 13) / max(1, len(row))
                    if dark > .06:
                        broken.append(("front", round(clk.t, 2), round(dark, 2)))
                for name, vis in (("lin", f["vis"][0]), ("lout", f["vis"][1])):
                    r = f[name]
                    if not vis or r[3] - r[1] < 24:
                        continue
                    faces += 1
                    x0, y0, x1, y1 = [int(v * dpr) for v in (r[0] + (r[2] - r[0]) * .25, r[1] + (r[3] - r[1]) * .3, r[2] - (r[2] - r[0]) * .25, r[3] - (r[3] - r[1]) * .3)]
                    crop = im.crop((max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1)))
                    hist = crop.histogram(); tot = max(1, sum(hist))
                    hole = sum(hist[:12]) / tot
                    if hole > .1:
                        broken.append((name, round(clk.t, 2), round(hole, 2)))
            check(f"{dev}: from the crack to open (20 fps) the lid's front edge is painted end to end and every face of the lid turned to the camera is painted over its middle",
                  seen >= 10 and faces >= 10 and not broken, {"front frames": seen, "face frames": faces, "broken": broken[:6]})
        ctx.close()


# ---------------------------------------------------------------- F
LOOK = r"""() => {
  const cush = [...document.querySelectorAll('.nova-case-cushion')].map(e => { const bg = getComputedStyle(e).backgroundImage;
    return { diag: (bg.match(/linear-gradient\((to (right|left) bottom|to bottom (right|left))/g) || []).length, radial: (bg.match(/radial-gradient/g) || []).length }; });
  const stitch = ['.bc-scene .bc-lid-out', '.badges-tab .ncase-lid-out'].map(s => { const o = document.querySelector(s); if(!o) return null;
    return [...o.querySelectorAll('*')].some(e => { const c = getComputedStyle(e); return c.borderTopStyle === 'dashed' && parseFloat(c.borderTopWidth) > 0 && !e.closest('.nova-case-nameplate'); }); });
  return { cush, stitch }; }"""


def section_f(br):
    print("\nF. the case looks finished: a plain padded lid, a stitched outside, in both cases")
    for (dev, w, h, dpr) in DEVICES:
        # the Badges tab, on its first (shut) frame
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=STANDALONE, dpr=1)
        pg.evaluate(SEED)
        clk = cb._StepperS(pg)
        pg.evaluate("() => { try{ settleUntil = 0; }catch(e){} showRanksScreen('badges'); }")
        clk.step(1 / 30); clk.step(1 / 30)
        tab = pg.evaluate(LOOK)
        ctx.close()
        # the cutscene's case, shut and risen
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=STANDALONE, dpr=1)
        pg.evaluate(SEED)
        clk = cb._StepperS(pg)
        pg.evaluate("() => { playBadgeCaseScene(['Identity Crimes'], () => {}); }")
        while clk.t < 7.6:
            clk.step(0.2)
        cut = pg.evaluate(LOOK)
        ctx.close()
        cush = tab["cush"] + cut["cush"]
        # MOVED IN 327 (b327e): "I also don't like the weird pattern of the
        # case on the inside top part." The tufting 326 added is the pattern;
        # the lid's inside is one plain padded cushion now (no diagonal seams,
        # a soft dome of light - at most three radial layers). The stitching
        # round the outside stays.
        ok = len(cush) >= 2 and all(c["diag"] == 0 and 1 <= c["radial"] <= 3 for c in cush) and tab["stitch"][1] is True and cut["stitch"][0] is True
        check(f"{dev}: both cases' lids are a plain padded cushion (no quilt) and stitched round the outside", ok,
              {"cushions": cush, "tab stitched": tab["stitch"][1], "cutscene stitched": cut["stitch"][0]})


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME)
        if "A" in ONLY or "B" in ONLY:
            section_ab(br)
        if "C" in ONLY:
            section_c(br)
        if "D" in ONLY or "E" in ONLY:
            section_de(br)
        if "F" in ONLY:
            section_f(br)
        br.close()
    print("\n%s" % ("ALL PASS" if not FAILURES else "%d FAILED:\n  - " % len(FAILURES) + "\n  - ".join(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
