#!/usr/bin/env python3
"""Build 325 (stream F): the bottom tab bar's Liquid Glass lens, to Madison's
iOS 26 reference recording.

"the tab bar lens Liquid Glass. There is improvements but it needs to be
better ... pay very close attention to the button tab and how it functions.
We need that. You did well with updating the toggle switches, now do the
same. We need this to be identical!!! Do your best. When you have one
selected, it should kinda grey. Ensure the lens size is perfect and ensure
the selected tabs lens is perfect and matches."

Her recording (a three-tab iOS 26 bar, 1320x2868, read frame by frame at
30fps) is the spec; the numbers asserted here are its numbers, in ranges:
  - at rest the selected tab sits on a GREY platter (an ~11% white over the
    bar), 4pt inside the bar at the top, the bottom and the end
    (concentric), the same size on every tab;
  - touch: the platter lifts into a lens ~1.27x the bar's height, standing
    proud of its top and bottom, wider than it is tall, while the bar
    swells (x1.084 wide, x1.043 tall) and what is under the lens is drawn
    ~1.23x;
  - it is a true capsule at every moment (no oval ends, no seam);
  - dragged, it follows the finger across every tab, squashes with speed
    (wider and flatter, area kept), and runs a little way past the end tab;
  - let go, it turns grey while it is still shrinking and becomes the
    platter on the tab under the finger, settled in well under half a
    second; a tap does the same, short, and selects;
  - Reduce motion: no lens, no swell; the platter just moves.

Every check FAILS on build 324 (6fc16b7) and passes here:
  python3 tools/check-b325-f.py
  python3 tools/check-b325-f.py --against /tmp/claude-0/wbase325/index.html
"""
import importlib.util
import io
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright  # noqa: E402

check, booted, USED_ACCOUNT, CHROME = cb.check, cb.booted, cb.USED_ACCOUNT, cb.CHROME

CLEAN = "() => { document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk,#tour-overlay,.tour-tip').forEach(n=>n.remove()); }"

# The platter's rect is the slider's box less the ::before's insets; the
# bar's and the tabs' are their own (a transform-free moment).
GEO = """() => {
  const bar = document.getElementById('bottomtabs'), b = bar.getBoundingClientRect();
  const sl = document.getElementById('bottomtabs-slider'), s = sl.getBoundingClientRect(), pb = getComputedStyle(sl, '::before');
  const n = v => parseFloat(v) || 0;
  const p = { l: s.left + n(pb.left), r: s.right - n(pb.right), t: s.top + n(pb.top), b: s.bottom - n(pb.bottom) };
  const tabs = [...bar.querySelectorAll('.bottomtabs-navrow .bottomtab')].map(t => { const r = t.getBoundingClientRect();
    return { id: t.id, l: r.left, r: r.right, w: r.width, c: r.left + r.width / 2, active: t.classList.contains('active') }; });
  const rgba = v => (v.match(/rgba?\\([^)]*\\)/g) || []).map(x => (x.match(/[\\d.]+/g) || []).map(Number));
  const fill = rgba(pb.backgroundColor)[0] || [0, 0, 0, 0];
  const insetWhite = Math.max(0, ...((pb.boxShadow.match(/rgba?\\([^)]*\\)[^,]*inset|inset[^,]*rgba?\\([^)]*\\)/g) || []).join(' ')
      .match(/rgba?\\([^)]*\\)/g) || []).map(x => (x.match(/[\\d.]+/g) || []).map(Number))
      .filter(a => a[0] > 200 && a[1] > 200 && a[2] > 200).map(a => a.length > 3 ? a[3] : 1));
  const fillWhite = fill[0] > 200 && fill[1] > 200 && fill[2] > 200 ? (fill.length > 3 ? fill[3] : 1) : 0;
  return { bar: { l: b.left, r: b.right, t: b.top, b: b.bottom, w: b.width, h: b.height }, p, tabs,
           op: parseFloat(getComputedStyle(sl).opacity), fillWhite, insetWhite }; }"""

LENS = """() => { const bar = document.getElementById('bottomtabs').getBoundingClientRect();
  const l = document.getElementById('bottomtabs-lens'); const body = l && l.querySelector('.tab-lens-body');
  if(!body) return { lens: false, barT: bar.top, barB: bar.bottom, barH: bar.height, barW: bar.width };
  const r = body.getBoundingClientRect(), cs = getComputedStyle(l);
  const grey = l.querySelector('.tab-lens-grey');
  return { lens: true, up: l.classList.contains('is-up'), op: parseFloat(cs.opacity), vis: cs.visibility,
    cx: r.left + r.width / 2, t: r.top, b: r.bottom, w: r.width, h: r.height,
    grey: grey ? parseFloat(getComputedStyle(grey).opacity) : 0,
    barT: bar.top, barB: bar.bottom, barH: bar.height, barW: bar.width, barCx: bar.left + bar.width / 2 }; }"""

# Every layer inside the lens that draws something: its own scale must be
# the same both ways (a capsule scaled two ways is not a capsule), and
# whatever it sits in may only move it.
CAPSULE = """() => { const l = document.getElementById('bottomtabs-lens'); if(!l) return { layers: 0, bad: ['no lens'] };
  const bad = []; let layers = 0;
  const M = el => { const t = getComputedStyle(el).transform; return t && t !== 'none' ? new DOMMatrixReadOnly(t) : new DOMMatrixReadOnly(); };
  l.querySelectorAll('*').forEach(el => { const cs = getComputedStyle(el);
    if(cs.visibility === 'hidden') return;
    const draws = (cs.backgroundColor && !/rgba\\(0, 0, 0, 0\\)|transparent/.test(cs.backgroundColor)) || cs.backgroundImage !== 'none' || cs.boxShadow !== 'none';
    if(!draws) return; layers++;
    let k = el, sx = 1, sy = 1;
    while(k && k !== l){ const m = M(k); sx *= Math.hypot(m.a, m.b); sy *= Math.hypot(m.c, m.d); k = k.parentElement; }
    if(Math.abs(sx - sy) > 1e-3 * Math.max(sx, sy)) bad.push((el.className || el.tagName) + ' ' + sx.toFixed(3) + 'x' + sy.toFixed(3)); });
  return { layers, bad }; }"""

def touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})


def check_geometry(br):
    print("\nF1. at rest: a grey platter, concentric with the bar, the same on every tab, centred on it")
    for (w, h) in [(320, 568), (375, 667), (393, 852), (440, 956), (744, 1133), (834, 1194), (1366, 638)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate(CLEAN)
        rows = []
        for tid in ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar"]:
            pg.evaluate("(id) => { document.querySelectorAll('#tour-overlay,.tour-tip').forEach(n=>n.remove()); document.getElementById(id).click(); }", tid)
            # a screen that is slow to build re-lights its tab when it lands;
            # measure once the platter has stopped
            # (a screen can hold the main thread for seconds here, software
            # rendered: wait until the platter's slide has finished and it
            # has stayed put)
            g = None
            for _ in range(30):
                pg.wait_for_timeout(300)
                pg.evaluate(CLEAN)
                busy = pg.evaluate("() => document.getElementById('bottomtabs-slider').getAnimations().length")
                g2 = pg.evaluate(GEO)
                if not busy and g and abs(g2["p"]["l"] - g["p"]["l"]) < .05 and any(x["active"] and x["id"] == tid for x in g2["tabs"]):
                    break
                g = g2
            g = g2
            t = next(x for x in g["tabs"] if x["id"] == tid)
            p, bar = g["p"], g["bar"]
            rows.append({"id": tid, "lit": t["active"], "pcx": (p["l"] + p["r"]) / 2, "tcx": t["c"], "pw": p["r"] - p["l"], "ph": p["b"] - p["t"],
                         "top": p["t"] - bar["t"], "bot": bar["b"] - p["b"], "lend": p["l"] - bar["l"], "rend": bar["r"] - p["r"],
                         "tw": t["w"], "fill": g["fillWhite"], "rim": g["insetWhite"], "op": g["op"]})
        ws = [r["tw"] for r in rows]; pws = [r["pw"] for r in rows]
        check("%dx%d: every platter centred on its tab (<=.5px), lit, and 4-8px inside the bar above and below it alike (<=.5px; the reference: 4pt)" % (w, h),
              all(r["lit"] and r["op"] > .95 and abs(r["pcx"] - r["tcx"]) <= .5 and abs(r["top"] - r["bot"]) <= .5 and 4 <= r["top"] <= 8 for r in rows),
              [(r["id"][10:], round(r["pcx"] - r["tcx"], 2), round(r["top"], 1), round(r["bot"], 1)) for r in rows])
        if w >= 360:   # a 320px phone cannot fit "Leaderboard" in a quarter of the bar
            check("%dx%d: four even tabs, and the platter the same size on each (within 10%%; it was 72 to 115 wide)" % (w, h),
                  max(ws) <= min(ws) * 1.1 and max(pws) <= min(pws) * 1.1, [round(x) for x in pws])
        first, last = rows[0], rows[-1]
        check("%dx%d: concentric with the bar - on the end tabs the platter is as far from the bar's end as from its top (+-1px), 4-8px" % (w, h),
              abs(first["lend"] - first["top"]) <= 1 and abs(last["rend"] - last["top"]) <= 1 and 4 <= first["top"] <= 8,
              {"home": [round(first["lend"], 1), round(first["top"], 1)], "calendar": [round(last["rend"], 1), round(last["top"], 1)]})
        check("%dx%d: \"it should kinda grey\": a flat white fill of 8-16%% (the reference: 11%%), no bright rim (<=20%%), never taller than wide" % (w, h),
              all(.08 <= r["fill"] <= .16 and r["rim"] <= .2 and r["ph"] <= r["pw"] + .5 for r in rows), {"fill": rows[0]["fill"], "rim": rows[0]["rim"], "size": [round(rows[0]["pw"]), round(rows[0]["ph"])]})
        ctx.close()


# ---- a frame-exact clock -------------------------------------------------
# This machine renders the page in software and its frames come when they
# come (a 450ms first frame after a touch was measured), so a gate that
# samples in real time misses the lens's peak and times its landing against
# the machine. The page clock is faked and every animation is paused and
# seeked to it, one 60th of a second a step (the review recordings' method,
# pack317), so each frame the page would draw is sampled, at its real time.
SEEK = """(t) => { const M = window.__t0s = window.__t0s || new WeakMap();
  document.getAnimations().forEach(an => {
    if(!M.has(an)) M.set(an, { at: t, from: an.currentTime || 0, done: false });
    const s = M.get(an); if(s.gone || s.done) return;
    if(an.animationName && an.effect && an.effect.target){ try{
      const cs = getComputedStyle(an.effect.target, an.effect.pseudoElement || null);
      if(cs.animationName.split(',').map(x => x.trim()).indexOf(an.animationName) < 0){ s.gone = true; an.cancel(); return; }
    }catch(e){} }
    const want = s.from + (t - s.at) * 1000;
    let end = Infinity; try{ end = an.effect.getComputedTiming().endTime; }catch(e){}
    if(want >= end && isFinite(end)){ s.done = true; try{ an.finish(); }catch(e){} return; }
    if(an.playState !== 'paused') an.pause();
    try{ an.currentTime = want; }catch(e){} }); return true; }"""


class Frames:
    def __init__(self, ctx, pg):
        self.pg, self.t, self.ms = pg, 0.0, 0
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Animation.enable")
        cdp.send("Animation.setPlaybackRate", {"playbackRate": 0})
        self._cdp = cdp
        pg.clock.install()
        pg.clock.pause_at((pg.evaluate("() => Date.now()") + 1500) / 1000.0)

    def step(self, n=1):
        for _ in range(n):
            self.t += 1 / 60.0
            ms = int(round(self.t * 1000))
            self.pg.clock.run_for(ms - self.ms)
            self.ms = ms
            self.pg.evaluate(SEEK, self.t)


SAMPLE = """() => { const bar = document.getElementById('bottomtabs').getBoundingClientRect();
  const l = document.getElementById('bottomtabs-lens'); const body = l && l.querySelector('.tab-lens-body');
  const r = body ? body.getBoundingClientRect() : null; const cs = l ? getComputedStyle(l) : null;
  const grey = l && l.querySelector('.tab-lens-grey'); const sl = document.getElementById('bottomtabs-slider');
  return { up: !!(l && l.classList.contains('is-up')), op: cs ? parseFloat(cs.opacity) : 0, vis: cs ? cs.visibility : 'hidden',
    cx: r ? r.left + r.width / 2 : null, t: r ? r.top : null, b: r ? r.bottom : null, w: r ? r.width : 0, h: r ? r.height : 0,
    grey: grey ? parseFloat(getComputedStyle(grey).opacity) : 0, slOp: parseFloat(getComputedStyle(sl).opacity),
    barT: bar.top, barB: bar.bottom, barW: bar.width, barH: bar.height, barCx: bar.left + bar.width / 2 }; }"""


def shown(f):
    return f["up"] and f["op"] > .5 and f["vis"] != "hidden"


def check_press(br):
    print("\nF2. a press: the platter lifts into a lens - its size, the bar's swell, what is under it, a true capsule")
    for label, w, h in [("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11\"", 834, 1194), ("375 phone", 375, 667)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        pg.evaluate(CLEAN); pg.evaluate("() => showHome()"); pg.wait_for_timeout(1100); pg.evaluate(CLEAN)
        g0 = pg.evaluate(GEO)
        T = {t["id"]: t for t in g0["tabs"]}
        cdp = ctx.new_cdp_session(pg)
        y = (g0["bar"]["t"] + g0["bar"]["b"]) / 2
        hx = T["bottomtab-home"]["c"]
        icon0 = pg.evaluate("() => document.querySelector('#bottomtabs .bottomtab.active .bottomtab-icon').getBoundingClientRect().width")
        F = Frames(ctx, pg)
        touch(cdp, "touchStart", hx, y)
        caps = []
        for i in range(36):
            F.step()
            if i % 3 == 0:
                caps.append(pg.evaluate(CAPSULE))
        d = pg.evaluate(SAMPLE)
        icon = pg.evaluate("() => document.querySelector('#bottomtabs .bottomtab.active .bottomtab-icon').getBoundingClientRect().width")
        touch(cdp, "touchEnd")
        for i in range(30):
            F.step()
            if i % 3 == 0:
                caps.append(pg.evaluate(CAPSULE))
        bar0 = g0["bar"]
        bc0 = (bar0["l"] + bar0["r"]) / 2
        hx1 = d["barCx"] + (hx - bc0) * d["barW"] / bar0["w"]
        check("%s: held, the lens stands proud of the swollen bar's top and bottom by 4-16px each (the reference: 7pt), centred on the tab where the swell has carried it (<=2px)" % label,
              shown(d) and d["barH"] >= bar0["h"] * 1.02 and 4 <= d["barT"] - d["t"] <= 16 and 4 <= d["b"] - d["barB"] <= 16 and abs(d["cx"] - hx1) <= 2,
              {k: round(d[k], 1) for k in ("t", "b", "h", "w", "cx", "barT", "barB") if d.get(k) is not None})
        check("%s: the lens is a capsule wider than it is tall (1.12-1.6 : 1; the reference's 1.4), ~1.27x the bar's height (1.15-1.4)" % label,
              shown(d) and 1.12 <= d["w"] / d["h"] <= 1.6 and 1.15 <= d["h"] / bar0["h"] <= 1.4,
              {"w/h": round(d["w"] / max(1, d["h"]), 3), "h/bar": round(d["h"] / bar0["h"], 3)})
        check("%s: the bar swells while it is held (x1.06-1.11 wide, x1.02-1.07 tall; the reference: 1.084 x 1.043), about its centre" % label,
              1.06 <= d["barW"] / bar0["w"] <= 1.11 and 1.02 <= d["barH"] / bar0["h"] <= 1.07 and abs(d["barCx"] - bc0) <= 1,
              {"w": round(d["barW"] / bar0["w"], 4), "h": round(d["barH"] / bar0["h"], 4)})
        check("%s: what is under the lens is drawn 1.18-1.3x (the reference: 1.23)" % label,
              1.18 <= icon / icon0 <= 1.3, round(icon / icon0, 3))
        drawn = [c for c in caps if c["layers"]]
        check("%s: a true capsule in every frame of the lift and the landing - every layer that draws it is scaled the same both ways (no oval ends)" % label,
              len(drawn) >= 10 and all(not c["bad"] for c in drawn), {"frames": len(drawn), "bad": [c["bad"] for c in drawn if c["bad"]][:2]})
        ctx.close()


def check_seam(br):
    print("\nF3. no seam: the lens is drawn as one piece of glass (3x, held)")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True, dpr=3)
    pg.evaluate(CLEAN); pg.evaluate("() => showHome()"); pg.wait_for_timeout(1500); pg.evaluate(CLEAN)
    g0 = pg.evaluate(GEO); T = {t["id"]: t for t in g0["tabs"]}
    cdp = ctx.new_cdp_session(pg)
    y = (g0["bar"]["t"] + g0["bar"]["b"]) / 2
    F = Frames(ctx, pg)
    touch(cdp, "touchStart", T["bottomtab-rewards"]["c"], y)
    F.step(50)
    d = pg.evaluate(SAMPLE)
    cap = pg.evaluate(CAPSULE)
    from PIL import Image
    shot = Image.open(io.BytesIO(pg.screenshot())).convert("L")
    touch(cdp, "touchEnd"); F.step(40)
    worst = 99
    if shown(d):
        cx = int(round(d["cx"] * 3))
        # rows through the lens's top rim, its highlight and the band below
        # it (clear of the label): the centre column against its neighbours
        worst = 0
        for k in (1, 2, 3, 5, 8, 11):
            yy = int(round((d["t"] + k) * 3))
            row = [shot.getpixel((x, yy)) for x in range(cx - 8, cx + 9)]
            for i in range(2, len(row) - 2):
                worst = max(worst, abs(row[i] - (row[i - 2] + row[i + 2]) / 2))
    check("held over Leaderboard, a capsule of halves (%d layers) with no line down its middle (<=4 levels against its neighbours)" % cap["layers"],
          shown(d) and cap["layers"] >= 2 and not cap["bad"] and worst <= 4, {"worst": worst, "bad": cap["bad"]})
    ctx.close()


def check_drag(br):
    print("\nF4. a drag: follows the finger across every tab, squashes with speed, runs past the end, lands grey on the tab")
    for label, w, h in [("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11\"", 834, 1194)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        pg.evaluate(CLEAN); pg.evaluate("() => showHome()"); pg.wait_for_timeout(1100); pg.evaluate(CLEAN)
        g0 = pg.evaluate(GEO); T = {t["id"]: t for t in g0["tabs"]}
        cdp = ctx.new_cdp_session(pg)
        y = (g0["bar"]["t"] + g0["bar"]["b"]) / 2
        ids = ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar"]
        xs = [T[i]["c"] for i in ids]
        F = Frames(ctx, pg)
        touch(cdp, "touchStart", xs[0], y); F.step(20)
        follow, held, lag = [], None, []
        x = xs[0]
        for nx in xs[1:]:
            for k in range(1, 9):
                fx = x + (nx - x) * k / 8
                touch(cdp, "touchMove", fx, y); F.step(2)
                lf = pg.evaluate(SAMPLE)
                # the finger in screen space, against the lens
                lag.append(fx - (lf["cx"] or fx))
            x = nx
            F.step(18)
            dd = pg.evaluate(SAMPLE)
            follow.append((round(nx), round(dd["cx"] or -1), round(dd["h"])))
            held = dd
        check("%s: dragged, the lens trails the moving finger a touch (3px+, a spring) and comes to rest under it on every tab (<=6px), still up" % label,
              len(follow) == 3 and all(abs(a - b) <= 6 and hh > g0["bar"]["h"] for a, b, hh in follow) and max(lag) >= 3,
              {"rest": follow, "most lag": round(max(lag), 1)})
        # fast back towards Profile: wider and flatter while it moves, about the same area
        fr = []
        for k in range(1, 7):
            touch(cdp, "touchMove", xs[3] + (xs[1] - xs[3]) * k / 6, y); F.step(); fr.append(pg.evaluate(SAMPLE))
        for _ in range(30):
            F.step(); fr.append(pg.evaluate(SAMPLE))
        mw = max(fr, key=lambda r: r["w"])
        tall = max(fr, key=lambda r: r["h"] / max(1, r["w"]))
        check("%s: moving fast it squashes - wider (>=6%%) and flatter (>=4%%), its area kept (+-15%%) - and wobbles taller as it stops (the reference's b0159)" % label,
              mw["w"] >= held["w"] * 1.06 and mw["h"] <= held["h"] * .96 and abs(mw["w"] * mw["h"] / (held["w"] * held["h"]) - 1) <= .15
              and tall["h"] / tall["w"] > held["h"] / held["w"] * 1.01,
              {"held": [round(held["w"]), round(held["h"])], "widest": [round(mw["w"]), round(mw["h"])], "tallest": [round(tall["w"]), round(tall["h"])]})
        # past the end tab
        for k in range(1, 9):
            touch(cdp, "touchMove", xs[1] + (xs[3] + 90 - xs[1]) * k / 8, y); F.step(2)
        F.step(30)
        past = pg.evaluate(SAMPLE)
        endc = past["barCx"] + (xs[3] - (g0["bar"]["l"] + g0["bar"]["r"]) / 2) * past["barW"] / g0["bar"]["w"]
        check("%s: dragged past the last tab, the lens runs a little way past it (10-30px; the reference's 16pt) and no further" % label,
              10 <= past["cx"] - endc <= 30, round(past["cx"] - endc, 1))
        # back to Leaderboard and let go
        for k in range(1, 9):
            touch(cdp, "touchMove", xs[3] + 90 + (xs[2] - xs[3] - 90) * k / 8, y); F.step(2)
        F.step(20)
        before = pg.evaluate(SAMPLE)
        touch(cdp, "touchEnd")
        rel = []
        for i in range(48):
            F.step(); f = pg.evaluate(SAMPLE); f["ms"] = (i + 1) * 1000 / 60; rel.append(f)
        F.step(30)
        s = pg.evaluate(GEO)
        pill = (s["p"]["l"] + s["p"]["r"]) / 2
        lit = [t["id"] for t in s["tabs"] if t["active"]]
        scr = pg.evaluate("() => !!document.querySelector('#stage .screen-rankings')")
        mags = pg.evaluate("() => [...document.querySelectorAll('#bottomtabs .bottomtab')].map(t => t.style.transform || '')")
        pillH = s["p"]["b"] - s["p"]["t"]
        check("%s: let go over Leaderboard: it lands there - lit, the board up, the grey platter centred under it (<=1px), nothing magnified" % label,
              lit == ["bottomtab-rewards"] and scr and abs(pill - T["bottomtab-rewards"]["c"]) <= 1 and s["op"] > .95
              and .08 <= s["fillWhite"] <= .16 and not any(mags), {"lit": lit, "pill": round(pill - T["bottomtab-rewards"]["c"], 2), "fill": s["fillWhite"], "mags": mags})
        greyBig = [round(f["ms"]) for f in rel if shown(f) and f["grey"] > .5 and f["h"] > pillH * f["barH"] / g0["bar"]["h"] + 4]
        check("%s: it turns grey while it is still shrinking (the grey coat over half while the lens is 4px+ taller than the platter), as the reference does (b0166-b0169)" % label,
              len(greyBig) >= 2, {"frames": greyBig, "held h": round(before["h"])})
        gone = next((f["ms"] for f in rel if not shown(f) and f["slOp"] > .95), None)
        check("%s: and, let go at rest over its tab, it is the platter again within 250ms (the reference, at rest over Settings: 133ms, b0328-b0332)" % label,
              gone is not None and gone <= 250, gone)
        ctx.close()


def check_tap(br):
    print("\nF5. a tap: swells, glides, settles grey on the tapped tab, and selects it")
    for label, w, h in [("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11\"", 834, 1194)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, touch=True)
        pg.evaluate(CLEAN); pg.evaluate("() => { store.seenRewardsTour = true; showRankings(); }"); pg.wait_for_timeout(1300); pg.evaluate(CLEAN)
        g0 = pg.evaluate(GEO); T = {t["id"]: t for t in g0["tabs"]}
        cdp = ctx.new_cdp_session(pg)
        y = (g0["bar"]["t"] + g0["bar"]["b"]) / 2
        bc0 = (g0["bar"]["l"] + g0["bar"]["r"]) / 2
        lb, cal = T["bottomtab-rewards"]["c"], T["bottomtab-calendar"]["c"]
        F = Frames(ctx, pg)
        touch(cdp, "touchStart", cal, y); F.step(); touch(cdp, "touchEnd")
        rec = []
        for i in range(42):
            F.step(); f = pg.evaluate(SAMPLE); f["ms"] = (i + 2) * 1000 / 60; rec.append(f)
        F.step(30)
        s = pg.evaluate(GEO)
        lit = [t["id"] for t in s["tabs"] if t["active"]]
        shownCal = pg.evaluate("() => [...document.querySelectorAll('#stage .screen-calendar')].some(e => !e.closest('[hidden]'))")
        up = [f for f in rec if shown(f)]
        # the tab centres in the swollen bar's frame
        sc = lambda f, x: f["barCx"] + (x - bc0) * f["barW"] / g0["bar"]["w"]
        swell = max([f["barW"] for f in rec] or [0]) / g0["bar"]["w"]
        check("%s: the tap lifts the lens over the bar's edges and glides it from Leaderboard to Calendar, the bar swelling under it (>=3%%)" % label,
              bool(up) and max(f["h"] for f in up) > g0["bar"]["h"] + 8 and abs(up[0]["cx"] - sc(up[0], lb)) < 8
              and any(sc(f, lb) + 10 < f["cx"] < sc(f, cal) - 10 for f in up) and swell >= 1.03,
              {"n": len(up), "maxH": round(max([f["h"] for f in up] or [0])), "xs": [round(f["cx"]) for f in up][:12], "swell": round(swell, 3)})
        gone = next((f["ms"] for f in rec if f["ms"] > 40 and not shown(f) and f["slOp"] > .95), None)
        check("%s: Calendar selected and showing, the grey platter centred under it, and settled within 520ms of the tap (the reference: ~400ms, b0324-b0336)" % label,
              lit == ["bottomtab-calendar"] and shownCal and abs((s["p"]["l"] + s["p"]["r"]) / 2 - cal) <= 1 and .08 <= s["fillWhite"] <= .16
              and gone is not None and gone <= 520, {"lit": lit, "shown": shownCal, "gone": gone})
        ctx.close()


def check_calm(br):
    print("\nF6. Reduce motion: no lens and no swell; a tap still lands the grey platter")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True)
    pg.evaluate(CLEAN); pg.evaluate("() => { theme.reduceMotion = true; applyTheme(); showHome(); }"); pg.wait_for_timeout(1100); pg.evaluate(CLEAN)
    g0 = pg.evaluate(GEO); T = {t["id"]: t for t in g0["tabs"]}
    cdp = ctx.new_cdp_session(pg)
    y = (g0["bar"]["t"] + g0["bar"]["b"]) / 2
    touch(cdp, "touchStart", T["bottomtab-profile"]["c"], y); pg.wait_for_timeout(400)
    d = pg.evaluate(LENS)
    touch(cdp, "touchEnd"); pg.wait_for_timeout(1200)
    s = pg.evaluate(GEO)
    lit = [t["id"] for t in s["tabs"] if t["active"]]
    shown_lens = d["lens"] and d.get("up") and d.get("op", 0) > .05 and d.get("vis") != "hidden"
    check("pressed with Reduce motion: no lens shows and the bar does not swell",
          not shown_lens and abs(d["barW"] - g0["bar"]["w"]) < .5, {"lens": shown_lens, "barW": [round(g0["bar"]["w"], 1), round(d["barW"], 1)]})
    check("and the tap lands Profile with the grey platter under it",
          lit == ["bottomtab-profile"] and abs((s["p"]["l"] + s["p"]["r"]) / 2 - T["bottomtab-profile"]["c"]) <= 1 and .08 <= s["fillWhite"] <= .16,
          {"lit": lit, "fill": s["fillWhite"]})
    pg.evaluate("() => { theme.reduceMotion = false; applyTheme(); }")
    ctx.close()


def main():
    fns = os.environ.get("ONLY_FN")
    order = [check_geometry, check_press, check_seam, check_drag, check_tap, check_calm]
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        try:
            for f in order:
                if fns and f.__name__ not in fns.split(","):
                    continue
                f(br)
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
