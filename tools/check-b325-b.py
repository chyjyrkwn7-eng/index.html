#!/usr/bin/env python3
"""Build 325, stream b: the badge backs and the badge case.

Madison (Oct 18):
  1. "I like the new badges, the title of the back of them though aren't
     visible though, especially for some depending on the shape. This needs
     to be fixed badly."
  2. "the thing on the top that says 'Nova - Class 26E' does not look 3d. It
     looks like a sticker. The thing on the front that says level one badge
     case is the same way, and that one has a weird placement because it's
     sitting on top of stuff. Would it make more sense if that one was just
     combined with the other one and put on top? Made to look nice?"
  3. "some of the metal things on the corners are rounded but then the
     others connecting to it aren't? Fix that."
  4. "The clips for the case don't make sense either, because they aren't
     clipping to anything.. fix that."
  5. "The badge case that's opened in the badge tab. Ensure the case is
     better here too."

Every check here was written against 6fc16b7 (build 324, reviewed), where
each one fails; run it there with --against to watch it:

  python3 tools/check-b325-b.py
  python3 tools/check-b325-b.py --against /path/to/old/index.html

On both reference devices (iPhone 17 Pro Max 440x956 @3x, iPad Pro 11"
834x1194 @2x):
  A. THE BACKS, every unit's badge (every BADGE_SHAPE), at the size the
     badge in your hand renders its back: every pixel of the engraved words
     lies inside the outline by at least BACK_MARGIN token units (tested
     against the outline itself with the canvas's own isPointInStroke - not
     the app's field); the name's letters are at least LETTER_MIN CSS px
     tall; and the cut reads against the metal - the field round the words
     at least CONTRAST_MIN times the luminance of the words' floor (a WCAG
     contrast ratio) on a clean badge, CONTRAST_DIRTY on the dirtiest.
  B. ONE NAMEPLATE ON TOP: the shut case (the cutscene's, and the Badges
     tab's) carries exactly one plate, on the lid's outside, holding both
     the app/class line and the case's name (badgeCaseName, read off the
     page); the front walls carry no words at all; the plate has a
     thickness (an edge showing below the slab), a shadow on the leather
     and a rivet in each corner.
  C. NOTHING ON THE FRONT SITS ON ANYTHING ELSE: the front's parts (latches,
     the handle, any plate) do not overlap, projected, in either case.
  D. THE CORNERS ARE ONE GEOMETRY: under every near cap of the shut lid the
     wall's guard is the same width and flush with it (within 1.5px,
     projected), the guard is square where it meets the cap and where the
     lid meets the base, its foot takes the cap's own inner radius, and it
     is the cap's metal.
  E. THE LATCHES CLIP TO SOMETHING: shut, each hasp crosses the seam and its
     keeper's staple shows THROUGH it (the top element at the staple's
     middle is the staple, inside the hasp's box); opening, each hasp comes
     off its staple and down (it moves through several poses) BEFORE the lid
     leaves shut - in the cutscene and on the Badges tab.
  F. THE TWO CASES ARE ONE OBJECT: the Badges tab's shut case and the
     cutscene's are built from the same parts - the nameplate, its rivets,
     the keepers and their staples - with the same plate drawing.
"""
import importlib.util
import io
import math
import os
import sys

from playwright.sync_api import sync_playwright

_spec = importlib.util.spec_from_file_location(
    "cb", os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
check, booted, USED_ACCOUNT, FAILURES = cb.check, cb.booted, cb.USED_ACCOUNT, cb.FAILURES

DEVICES = [("17 Pro Max", 440, 956, 3), ("iPad Pro 11", 834, 1194, 2)]
BACK_MARGIN = 5.6     # token units inside the outline (the back's rim is 4.6)
LETTER_MIN = 9.2      # CSS px, the name's letters, smallest badge
CONTRAST_MIN = 3.0    # field round the words : the words' floor, a clean badge
CONTRAST_DIRTY = 2.5  # ...the dirtiest (stage 4: dulled on purpose)
ONLY = os.environ.get("B325B_ONLY", "ABCDEF")

STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){},
       addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""

# ---------------------------------------------------------------- A. backs
BACKS = r"""async (o) => {
  const units = unitsInTeachingOrder(); store.unitPerfects = {}; units.forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
  store.badgeCleanedAt = {}; units.forEach(u => store.badgeCleanedAt[u] = Date.now());
  theme.reduceMotion = true; theme.muteBanners = true; applyTheme();
  document.querySelectorAll('#pushing-update,#intro-pop,.app-banner,.daily-alert,.update-banner,.nova-talk').forEach(n => n.remove());
  /* the size the badge in your hand renders its back at, on this device */
  let W = 0;
  let shown = 0;
  try{ openBadgeInspect(units[0], null); shown = badgeInspectNow.size(); W = Math.min(864, badgeStrikeSize(shown * badgeDpr())); badgeInspectNow.teardown(); }catch(e){ return { err: String(e) }; }
  /* CSS px per pixel of the render: the render is capped (864), so not always the device's */
  const dpr = W / shown, out = { W, dpr, shown, units: {} };
  const load = src => new Promise(r => { const im = new Image(); im.onload = () => r(im); im.onerror = () => r(null); im.src = src; });
  const lin = v => { v /= 255; return v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
  for(const u of units){
    const shape = badgeShapeFor(u), d = shape.d, S = BADGE_GEOM.scale, c = shape.c;
    const g = badgeStrikeGeometry(shape);
    const M = badgeBackLayout(u, g, W);
    /* the outline as the back shows it (mirrored), with the margin as a stroke */
    const vb = badgeViewBoxFor(d).split(/\s+/).map(Number), f = W / vb[2];
    const cv = document.createElement('canvas'); cv.width = cv.height = W; const cx = cv.getContext('2d');
    cx.setTransform(-f, 0, 0, f, W + vb[0] * f, -vb[1] * f); cx.translate(c[0], c[1]); cx.scale(S, S); cx.translate(-c[0], -c[1]);
    const path = new Path2D(d); cx.lineWidth = 2 * o.margin; cx.lineJoin = 'round';
    const deep = (x, y) => cx.isPointInPath(path, x + .5, y + .5) && !cx.isPointInStroke(path, x + .5, y + .5);
    let ink = 0, out_ = 0;
    for(let y = 0; y < W; y++) for(let x = 0; x < W; x++){ if(M[y * W + x] > .25){ ink++; if(!deep(x, y)) out_++; } }
    /* letters: connected components of the words, their size */
    const lab = new Int32Array(W * W); let n = 0; const sizes = [];
    for(let i = 0; i < W * W; i++){ if(M[i] <= .5 || lab[i]) continue; n++;
      const st = [i]; lab[i] = n; let x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1, a = 0;
      while(st.length){ const q = st.pop(), qx = q % W, qy = (q / W) | 0; a++;
        if(qx < x0) x0 = qx; if(qx > x1) x1 = qx; if(qy < y0) y0 = qy; if(qy > y1) y1 = qy;
        for(const nb of [q - 1, q + 1, q - W, q + W]){ if(nb < 0 || nb >= W * W) continue; if(Math.abs((nb % W) - qx) > 1) continue; if(M[nb] > .5 && !lab[nb]){ lab[nb] = n; st.push(nb); } } }
      /* its height: letters set side by side can touch and join, which widens a component but never heightens it */
      if(a >= 6) sizes.push(y1 - y0 + 1); }
    sizes.sort((p, q) => p - q);
    /* the letters of the NAME: the larger half of the components (the class line is smaller) */
    const big = sizes.slice(Math.floor(sizes.length / 2));
    const letter = big.length ? big[Math.floor(big.length / 2)] / dpr : 0;
    /* contrast, clean and dirtiest: the words' floor against the field round them */
    const con = [];
    for(const stage of [0, 4]){
      const im = await load(badgeBackFaceURL(u, W, stage)); if(!im){ con.push(0); continue; }
      const c2 = document.createElement('canvas'); c2.width = c2.height = W; const g2 = c2.getContext('2d'); g2.drawImage(im, 0, 0);
      const px = g2.getImageData(0, 0, W, W).data;
      const L = i => .2126 * lin(px[i * 4]) + .7152 * lin(px[i * 4 + 1]) + .0722 * lin(px[i * 4 + 2]);
      const r1 = 1, r2 = Math.max(4, Math.round(W * .03)), rc = Math.max(2, Math.round(W * .006));
      const core = [], field = [];
      for(let y = r2; y < W - r2; y += 1) for(let x = r2; x < W - r2; x += 1){
        const i = y * W + x;
        if(M[i] > .95){ let ok = true; for(let v = -r1; v <= r1 && ok; v++) for(let w = -r1; w <= r1; w++) if(M[i + v * W + w] < .95){ ok = false; break; } if(ok) core.push(L(i)); }
        else if(M[i] === 0 && (x + y) % 2 === 0){
          let near = false; for(let v = -r2; v <= r2 && !near; v += 2) for(let w = -r2; w <= r2; w += 2) if(M[i + v * W + w] > .5){ near = true; break; }
          let close = false; for(let v = -rc; v <= rc && !close; v++) for(let w = -rc; w <= rc; w++) if(M[i + v * W + w] > .02){ close = true; break; }
          if(near && !close && deep(x, y)) field.push(L(i)); } }
      const med = a => { a.sort((p, q) => p - q); return a.length ? a[Math.floor(a.length / 2)] : 0; };
      con.push(core.length > 20 && field.length > 20 ? +((med(field) + .05) / (med(core) + .05)).toFixed(2) : 0);
      (out.lum = out.lum || {})[u.slice(0, 12) + stage] = [+med(field).toFixed(3), +med(core).toFixed(3), core.length, field.length];
    }
    out.units[u] = { key: Object.keys(BADGE_SHAPE).find(k => BADGE_SHAPE[k] === shape), ink, out: out_, letter: +letter.toFixed(1), con };
  }
  return out; }"""


def section_a(br):
    print("\nA. the engraved name on the back of every badge: inside its shape, big enough, and dark against the metal")
    for (dev, w, h, dpr) in DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=STANDALONE, dpr=dpr)
        pg.set_default_timeout(600000)
        r = pg.evaluate(BACKS, {"margin": BACK_MARGIN})
        ctx.close()
        if r.get("err"):
            check(f"{dev}: the backs could be measured", False, r["err"])
            continue
        U = r["units"]
        shapes = sorted(set(v["key"] for v in U.values()))
        print("     (rendered at %d px for %.0f CSS px; %d units, %d shapes)" % (r["W"], r["shown"], len(U), len(shapes)))
        if os.environ.get("B325B_LUM"): print(r.get("lum"))
        outside = {u[:24]: (v["key"], v["out"], v["ink"]) for u, v in U.items() if v["ink"] == 0 or v["out"] > 0}
        check(f"{dev}: on every badge (all {len(shapes)} shapes) every pixel of the engraved words is inside the outline by {BACK_MARGIN} units",
              len(U) >= 16 and len(shapes) >= 16 and not outside, outside or "")
        small = {u[:24]: (v["key"], v["letter"]) for u, v in U.items() if v["letter"] < LETTER_MIN}
        check(f"{dev}: the name's letters are at least {LETTER_MIN} CSS px on every badge",
              len(U) >= 16 and not small, small or {"smallest": min((v["letter"], v["key"]) for v in U.values())})
        weak = {u[:24]: (v["key"], v["con"]) for u, v in U.items() if v["con"][0] < CONTRAST_MIN or v["con"][1] < CONTRAST_DIRTY}
        check(f"{dev}: the cut reads: the metal round the words is at least {CONTRAST_MIN}x the words' floor clean, {CONTRAST_DIRTY}x at its dirtiest, every badge",
              len(U) >= 16 and not weak, weak or {"lowest clean": min((v["con"][0], v["key"]) for v in U.values()), "lowest dirtiest": min((v["con"][1], v["key"]) for v in U.values())})


# ---------------------------------------------------------------- the case
HELD = ["Fitness, Wellness, and Stress Management", "Professionalism and Ethics", "Professional Policing",
        "US and Texas Constitution and Rights", "Victims of Crime"]
NEW = "Identity Crimes"
SEED = """([held, nu]) => { store.unitPerfects = {}; held.forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
  if(nu) store.unitPerfects[nu] = badgeThresholdFor(nu); store.pendingBadgeUnlocks = []; store.retroBadgePending = [];
  store.seenUnlocks = store.seenUnlocks || {}; store.seenUnlocks.badges = unitsInTeachingOrder();
  store.badgeCleanedAt = {}; unitsInTeachingOrder().forEach(u => store.badgeCleanedAt[u] = Date.now());
  store.rankMapFx244 = true; store.rankMapSeen = TIER_ORDER_FULL.indexOf(rankOf(store));
  theme.muteBanners = false; theme.reduceMotion = false; applyTheme(); saveStore();
  document.querySelectorAll('#pushing-update,#intro-pop,.app-banner,.daily-alert,#toast,.vroom-chat-alert,.nova-talk').forEach(n => n.remove());
  showHome(); }"""

# what a shut case shows: its plate(s), the words on its front, its front's parts,
# the corners at the fold, the latches. `root` is the case, `out` its lid's outside,
# `front` the base's front wall, `lidFront` the lid's (the cutscene's only).
SHUT = r"""(sel) => {
  const k = document.querySelector(sel.root); if(!k) return null;
  const B = e => { const r = e.getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height }; };
  const out = k.querySelector(sel.out), front = k.querySelector(sel.front), lidFront = sel.lidFront ? k.querySelector(sel.lidFront) : null;
  const res = { root: !!k, out: !!out, front: !!front };
  const caseName = (() => { try{ return badgeCaseName(BADGE_CASES[0]); }catch(e){ return ''; } })();
  res.caseName = caseName;
  /* B. the plates: anything on the case that carries words, outside the lid's cushion */
  const texty = el => [...el.querySelectorAll('*')].filter(e => !e.closest('.nova-case-cushion, .nova-case-lidlabel, .sr-only, .ncase-cell, .bc-slot') &&
    [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden');
  const plates = [...k.querySelectorAll('.nova-case-plate, .nova-case-sideplate, .nova-case-nameplate')].filter(p => p.getClientRects().length && !p.parentElement.closest('.nova-case-plate'));
  res.plates = plates.map(p => ({ inLidOut: !!(out && out.contains(p)), onFront: !!((front && front.contains(p)) || (lidFront && lidFront.contains(p))),
    text: p.textContent.replace(/\s+/g, ' ').trim(),
    lines: [...p.querySelectorAll('*')].filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())).length,
    rivets: p.querySelectorAll('.nova-case-screw').length }));
  res.frontWords = [front, lidFront].filter(Boolean).flatMap(f => texty(f).map(e => e.textContent.trim()));
  /* the plate's thickness and shadow: an edge showing below its slab, a shadow wider than it on the leather */
  const np = k.querySelector('.nova-case-nameplate');
  if(np){ const slab = np.querySelector('.nova-case-np-slab'), edge = np.querySelector('.nova-case-np-edge'), sh = np.querySelector('.nova-case-np-shadow');
    res.depth = { slab: slab ? B(slab) : null, edge: edge ? B(edge) : null, shadow: sh ? B(sh) : null }; }
  /* C. the front's parts, projected */
  const parts = [];
  [front, lidFront].filter(Boolean).forEach(f => [...f.children].forEach(c => { if(c.getClientRects().length) parts.push({ cls: c.className, box: B(c) }); }));
  res.parts = parts;
  /* D. corners: each near cap of the lid's outside, and the guard under it */
  const caps = out ? [...out.querySelectorAll(':scope > .nova-case-cap')] : [];
  const nearCaps = caps.filter(c => /is-b[lr]/.test(c.className)).map(c => ({ side: /is-bl/.test(c.className) ? 'l' : 'r', box: B(c), cs: getComputedStyle(c) }));
  /* a point in an element's own box, projected: a 0x0 probe placed there */
  const at = (el, x, y) => { const q = document.createElement('i'); q.style.cssText = 'position:absolute;width:0;height:0;margin:0;padding:0;left:' + x + 'px;top:' + y + 'px';
    el.appendChild(q); const r = q.getBoundingClientRect(); q.remove(); return [r.left, r.top]; };
  const wall = lidFront || front;
  res.corners = nearCaps.map(c => {
    const capEl = caps.find(e => (c.side === 'l' ? /is-bl/ : /is-br/).test(e.className));
    const gcs = getComputedStyle(wall, c.side === 'l' ? '::before' : '::after');
    const px = v => parseFloat(v) || 0, gw = px(gcs.width);
    const gx = c.side === 'l' ? px(gcs.left) : wall.clientWidth - px(gcs.right) - gw;
    /* the cap's edge along the fold, and the guard's top edge, both projected */
    const cw = capEl.offsetWidth, ch = capEl.offsetHeight;
    const cap = [at(capEl, 0, ch)[0], at(capEl, cw, ch)[0]], guard = [at(wall, gx, 0)[0], at(wall, gx + gw, 0)[0]];
    const capR = c.side === 'l' ? [c.cs.borderTopLeftRadius, c.cs.borderTopRightRadius, c.cs.borderBottomRightRadius, c.cs.borderBottomLeftRadius]
                                : [c.cs.borderTopRightRadius, c.cs.borderTopLeftRadius, c.cs.borderBottomLeftRadius, c.cs.borderBottomRightRadius];
    /* the left guard's own corners; the right one is the left mirrored (scaleX(-1)) */
    const gR = [gcs.borderTopLeftRadius, gcs.borderTopRightRadius, gcs.borderBottomRightRadius, gcs.borderBottomLeftRadius];
    const baseG = lidFront ? getComputedStyle(front, c.side === 'l' ? '::before' : '::after') : null;
    return { side: c.side, cap, guard, capR, guardR: gR,
      baseGuardR: baseG ? [baseG.borderTopLeftRadius, baseG.borderTopRightRadius, baseG.borderBottomRightRadius, baseG.borderBottomLeftRadius] : null,
      capBg: c.cs.backgroundImage.replace(/\d+(\.\d+)?px/g, 'N'), guardBg: gcs.backgroundImage.replace(/\d+(\.\d+)?px/g, 'N') };
  });
  /* hit tests below need the case's parts to take a hit (they are pointer-events:none) */
  const hitOn = document.createElement('style'); hitOn.textContent = sel.root + ', ' + sel.root + ' *, .bc-stage{ pointer-events:auto !important; }'; document.head.appendChild(hitOn);
  /* E. the latches: each hasp, the keeper's staple it is hooked on, and what is on top there */
  res.latches = [...(front ? front.querySelectorAll('.nova-case-latch') : [])].map((l, i) => {
    const hp = l.querySelector('.nova-case-hasp'); if(!hp) return { hasp: false };
    const hb = B(hp);
    const keepers = [...k.querySelectorAll('.nova-case-keeper')];
    const kp = keepers.sort((a, b) => Math.abs((B(a).l + B(a).r) / 2 - (hb.l + hb.r) / 2) - Math.abs((B(b).l + B(b).r) / 2 - (hb.l + hb.r) / 2))[0];
    const st = kp ? kp.querySelector('.nova-case-staple') : null, sb = st ? B(st) : null;
    const sx = sb ? (sb.l + sb.r) / 2 : 0, sy = sb ? (sb.t + sb.b) / 2 : 0;
    const top = sb ? document.elementFromPoint(sx, sy) : null;
    const fb = front.getBoundingClientRect();
    return { hasp: true, hb, seam: fb.top, keeper: !!kp, staple: sb,
      through: !!(top && top.closest && top.closest('.nova-case-staple, .ncase-staple-over')),
      inHasp: !!(sb && sx > hb.l && sx < hb.r && sy > hb.t && sy < hb.b),
      crosses: hb.t < fb.top - 2 && hb.b > fb.top + 2 };
  });
  hitOn.remove();
  return res; }"""

CUT_SEL = {"root": ".bc-scene .bc-case", "out": ".bc-lid-out", "front": ".bc-front", "lidFront": ".bc-lid-front"}
TAB_SEL = {"root": ".badges-tab .ncase", "out": ".ncase-lid-out", "front": ".ncase-front", "lidFront": None}

# the latch poses and the lid's, through the opening
POSE = r"""(sel) => { const k = document.querySelector(sel.root); if(!k) return null;
  const lid = k.querySelector(sel.lid);
  const hasps = [...k.querySelectorAll((sel.front || '') + ' .nova-case-hasp')].map(h => { const r = h.getBoundingClientRect(); return [Math.round(r.top * 2) / 2, Math.round(r.bottom * 2) / 2, getComputedStyle(h).transform.slice(0, 60)]; });
  const staples = [...k.querySelectorAll('.nova-case-keeper .nova-case-staple')].map(s => { const r = s.getBoundingClientRect(); return [(r.left + r.right) / 2, (r.top + r.bottom) / 2]; });
  const hooked = [...k.querySelectorAll((sel.front || '') + ' .nova-case-hasp')].map(h => { const r = h.getBoundingClientRect();
    return staples.some(([x, y]) => x > r.left && x < r.right && y > r.top && y < r.bottom); });
  return { lid: lid ? getComputedStyle(lid).transform : '', hasps, hooked }; }"""


def rects_overlap(a, b, slack=1.0):
    return min(a["r"], b["r"]) - max(a["l"], b["l"]) > slack and min(a["b"], b["b"]) - max(a["t"], b["t"]) > slack


def judge_shut(dev, where, s):
    """B, C, D, E (shut) for one case."""
    if not s:
        check(f"{dev}, {where}: the case is there", False, s)
        return
    name = s["caseName"]
    pl = s["plates"]
    one = [p for p in pl if p["inLidOut"]]
    if "B" in ONLY:
        check(f"{dev}, {where}: ONE plate, on the lid's top, with the app and class AND the case's name ('{name}') on it; no other plate anywhere",
              len(pl) == 1 and len(one) == 1 and name and name.upper() in one[0]["text"].upper() and "26E" in one[0]["text"].upper() and one[0]["lines"] >= 2,
              pl)
        check(f"{dev}, {where}: the front carries no words at all", not s["frontWords"], s["frontWords"])
        d = s.get("depth") or {}
        sl, ed, sh = d.get("slab"), d.get("edge"), d.get("shadow")
        solid = bool(sl and ed and sh) and ed["b"] - sl["b"] >= 1.0 and sh["b"] > sl["b"] + 1 and sh["w"] > sl["w"] and (one[0]["rivets"] if one else 0) >= 4
        check(f"{dev}, {where}: the plate is a raised piece of metal: its thickness shows below the slab, its shadow lies on the leather past it, a rivet in each corner",
              solid, {"depth": d, "rivets": one[0]["rivets"] if one else None})
    if "C" in ONLY:
        parts = s["parts"]
        bad = [(a["cls"][:30], b["cls"][:30]) for i, a in enumerate(parts) for b in parts[i + 1:] if rects_overlap(a["box"], b["box"])]
        check(f"{dev}, {where}: nothing on the front sits on top of another part (latches, handle, plates, keepers: no overlaps)",
              len(parts) >= 3 and not bad, bad or len(parts))
    if "D" in ONLY:
        cs = s["corners"]
        misfit = []
        for c in cs:
            if abs(c["cap"][0] - c["guard"][0]) > 1.5 or abs(c["cap"][1] - c["guard"][1]) > 1.5:
                misfit.append(("width", c["side"], [round(v, 1) for v in c["cap"]], [round(v, 1) for v in c["guard"]]))
            # the cap's free (inner) corner: its largest radius
            capInner = max(c["capR"], key=lambda v: float(v.replace("px", "") or 0))
            g = c["guardR"]
            # at the fold (its top) square; its foot: the cap's inner radius on the inside
            if not g or g[0] != "0px" or g[1] != "0px":
                misfit.append(("guard not square at the fold", c["side"], g))
            if c["baseGuardR"] is not None:
                # the lid's front meets the base's at the seam: both square there, the base's foot the cap's curve
                if g[2] != "0px" or g[3] != "0px":
                    misfit.append(("lid guard not square at the seam", c["side"], g))
                bg = c["baseGuardR"]
                if bg[0] != "0px" or bg[1] != "0px" or bg[2] != capInner:
                    misfit.append(("base guard", c["side"], bg, capInner))
            elif g and g[2] != capInner:
                misfit.append(("guard's foot is not the cap's curve", c["side"], g, capInner))
            if c["capBg"].split("linear-gradient")[-1] != c["guardBg"].split("linear-gradient")[-1].replace("225deg", "135deg"):
                misfit.append(("not the cap's metal", c["side"]))
        check(f"{dev}, {where}: every near corner is one geometry: the guard under the cap is its width and flush with it, square at the fold and the seam, its foot the cap's own curve, the cap's metal",
              len(cs) == 2 and not misfit, misfit or len(cs))
    if "E" in ONLY:
        L = s["latches"]
        good = [l for l in L if l.get("hasp") and l.get("keeper") and l.get("crosses") and l.get("inHasp") and l.get("through")]
        check(f"{dev}, {where}: shut, both hasps cross the seam and are hooked on a keeper - its staple shows through each hasp's slot, on top",
              len(L) == 2 and len(good) == 2, L)


def section_case(br):
    print("\nB-F. the badge case: one nameplate on top, a clear front, one corner geometry, latches that clip, one case")
    for (dev, w, h, dpr) in DEVICES:
        # ---- the cutscene: shut at 7.6s (risen, latches done up), then its opening
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=STANDALONE, dpr=dpr)
        pg.evaluate(SEED, [HELD, NEW]); pg.wait_for_timeout(600)
        clk = cb._Stepper320(pg)
        pg.evaluate("([nu]) => { playBadgeCaseScene([nu], () => {}); }", [NEW])
        T = pg.evaluate("() => BC_T")
        while clk.t < 7.6:
            clk.step(1 / 10)
        cut = pg.evaluate(SHUT, CUT_SEL)
        cut_parts = pg.evaluate("() => { try{ return caseHardwareOf(document.querySelector('.bc-scene .bc-case')); }catch(e){ return null; } }")
        cut_plate = pg.evaluate("""() => { const s = document.querySelector('.bc-scene .nova-case-nameplate .nova-case-np-slab'); if(!s) return null;
          const c = getComputedStyle(s); return { bg: c.backgroundImage.replace(/[\\d.]+px/g, 'N'), lines: s.children.length }; }""")
        judge_shut(dev, "the cutscene's case", cut)
        if "E" in ONLY:
            # from the first latch to the crack, a frame every 1/30s
            poses = []
            while clk.t < T["crack"] / 1000 - 1e-6:
                clk.step(1 / 30)
                poses.append((clk.t, pg.evaluate(POSE, {"root": ".bc-scene .bc-case", "lid": ".bc-lid", "front": ".bc-front"})))
            lid0 = poses[0][1]["lid"] if poses else ""
            lid_still = all(p["lid"] == lid0 for _, p in poses)
            free = poses[-1][1]["hooked"] if poses else [True]
            hooked0 = poses[0][1]["hooked"] if poses else []
            moved = [len(set(tuple(p["hasps"][i][:2]) for _, p in poses)) for i in range(2)] if poses else [0, 0]
            check(f"{dev}, the cutscene: both hasps start hooked on their staples, come off them and swing down (each through 6+ poses) before the lid moves at all",
                  lid_still and poses and len(hooked0) == 2 and all(hooked0) and not any(free) and min(moved) >= 6,
                  {"hooked at the first latch": hooked0, "lid still": lid_still, "hooked at the crack": free, "poses": moved})
        ctx.close()

        # ---- the Badges tab: its first frame (shut), then its opening
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, init=STANDALONE, dpr=dpr)
        pg.evaluate(SEED, [HELD + [NEW], None]); pg.wait_for_timeout(500)
        clk = cb._StepperS(pg)
        pg.evaluate("() => { try{ settleUntil = 0; }catch(e){} showRanksScreen('badges'); }")
        clk.step(1 / 30)
        pg.evaluate("() => { const k = document.querySelector('.badges-tab .ncase'); if(k) k.scrollIntoView({ block: 'end', behavior: 'instant' }); }")
        clk.step(1 / 30)
        tab = pg.evaluate(SHUT, TAB_SEL)
        tab_parts = pg.evaluate("() => { try{ return caseHardwareOf(document.querySelector('.badges-tab .ncase')); }catch(e){ return null; } }")
        tab_plate = pg.evaluate("""() => { const s = document.querySelector('.badges-tab .nova-case-nameplate .nova-case-np-slab'); if(!s) return null;
          const c = getComputedStyle(s); return { bg: c.backgroundImage.replace(/[\\d.]+px/g, 'N'), lines: s.children.length }; }""")
        judge_shut(dev, "the Badges tab's case", tab)
        if "E" in ONLY:
            poses = []
            shut_lid = pg.evaluate("() => { const l = document.querySelector('.badges-tab .ncase-lid'); return l ? getComputedStyle(l).transform : ''; }")
            for _ in range(60):
                clk.step(1 / 60)
                p = pg.evaluate(POSE, {"root": ".badges-tab .ncase", "lid": ".ncase-lid", "front": ".ncase-front"})
                if not p:
                    break
                poses.append(p)
                if p["lid"] != shut_lid:
                    break
            moved_at = poses[-1] if poses else None
            before = poses[:-1]
            distinct = [len(set(tuple(p["hasps"][i]) for p in before if len(p["hasps"]) > i)) for i in range(2)]
            ok = bool(moved_at) and moved_at["lid"] != shut_lid and len(moved_at["hasps"]) == 2 and not any(moved_at["hooked"]) and min(distinct) >= 4
            check(f"{dev}, the Badges tab: both hasps come off their staples and swing down (4+ poses each) before the lid leaves shut",
                  ok, {"frames": len(poses), "hooked when the lid moved": moved_at and moved_at["hooked"], "poses": distinct})
        ctx.close()

        if "F" in ONLY:
            keys = ["nova-case-nameplate", "nova-case-keeper", "nova-case-staple", "nova-case-cap", "nova-case-screw", "nova-case-latch", "nova-case-hasp", "nova-case-handle"]
            a = {k: (tab_parts or {}).get(k) for k in keys}
            b = {k: (cut_parts or {}).get(k) for k in keys}
            same = bool(tab_parts and cut_parts) and a == b and (a.get("nova-case-nameplate") or 0) == 1 and (a.get("nova-case-keeper") or 0) == 2 \
                and (a.get("nova-case-staple") or 0) == 2 and bool(tab_plate and cut_plate) and tab_plate == cut_plate
            check(f"{dev}: the Badges tab's case and the cutscene's are one object - the same nameplate (same drawing), keepers, staples, caps, screws, latches",
                  same, {"tab": a, "cutscene": b, "plate same": tab_plate == cut_plate})


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME)
        if "A" in ONLY:
            section_a(br)
        if any(x in ONLY for x in "BCDEF"):
            section_case(br)
        br.close()
    print("\n%s" % ("ALL PASS" if not FAILURES else "%d FAILED:\n  - " % len(FAILURES) + "\n  - ".join(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
