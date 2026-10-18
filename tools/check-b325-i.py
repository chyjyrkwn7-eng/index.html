#!/usr/bin/env python3
"""Build 325, stream I - the road map's flare goes into the planet system
UNCHANGED.

Madison: "the flare bubble changes in the transition and doesn't look like
the flare.. fix that. That's a big one."

At the road map -> planet hand-off (rankCutHandoff) the road map's copy of
the new rank's circle (the "ghost": a gold rim, a 4px ring of the rank's
colour and a 30px glow) is moved INTO the scene's bubble. On 618ee2b that
bubble was overflow:hidden, so in ONE frame the copy lost its rim, its ring
and its glow - a gold, glowing flare became a plain glass ball - and the gold
came back only ~0.6s later as the bubble lit.

This measures it in pixels, on both reference devices, installed:

  K1. the last frame before the move against the first frame after it:
      same centre and size, and the same rim colour, ring and glow round
      the copy (the annuli just outside its edge);
  K2. from there, the hand-off's cross-fade (lit bubble in, copy out),
      frame by frame (Playwright's clock paused and every animation seeked
      together): no frame-to-frame jump in rim, ring or glow, and the rim
      stays gold the whole way (it never drops to the glass ball).

Traps this harness had to get past, each of which invented a defect:
  - pause_at() takes SECONDS when given a number; a millisecond Date.now()
    jumped the clock decades on and fired every timer in the journey;
  - the move re-parents the copy, which restarts its CSS animations, and
    ruClockSnap puts them back on their clock in the same instant - a seek
    that reset "new" animations to 0 restarted the "you are here" pulse
    ring and read it as the ring changing (the pulse is held still here:
    it is the same heartbeat either side of the move);
  - the rim is ~5 device px wide and the planet system rounds its place a
    third of a pixel differently from the road map, so a band average moved
    by a fifth with nothing visible changing: the circle is found in the
    pixels (the rim's peak round 180 rays), not taken from the layout box.

  python3 tools/check-b325-i.py
  python3 tools/check-b325-i.py --against /tmp/claude-0/w325final/index.html

Exits non-zero on any failure. Frames go to $B325I_OUT (if set).
"""
import importlib.util
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
from playwright.sync_api import sync_playwright
from PIL import Image

DEVICES = (("iPhone 17 Pro Max", 440, 956, 3), ("iPad Pro 11\"", 834, 1194, 2))
OUT = os.environ.get("B325I_OUT")
STEP_MS = 50
STEPS = 34          # 0 .. 1700ms: the cross-fade (copy out over 250+1300ms, bubble in on the same timing); after it the scene marks the flare with its own ring
FAILURES = []
if "--against" in sys.argv:
    print("against: %s" % cb.SRC)


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:700]) if detail else ""))
    if not ok:
        FAILURES.append(name)


STANDALONE = """(() => { try{ Object.defineProperty(navigator, 'standalone', { get: () => true, configurable: true }); }catch(e){}
  const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q) ? { matches: true, media: q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} } : mm(q); })();"""


def boot(br, w, h, dpr):
    """cb.booted(), with Playwright's clock installed BEFORE the page loads
    (time flows until the check pauses it)."""
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, is_mobile=True, device_scale_factor=dpr)
    ctx.add_init_script(STANDALONE)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');"
                        "localStorage.setItem('class26e.drill.v1', '%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');}catch(e){}" % cb.USED_ACCOUNT)
    pg = cb.open_page(ctx)
    pg.clock.install()
    pg.goto(cb.URL)
    pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    return ctx, pg


# Hold the journey at the end of rankUpHandOut (the copy drawn back, the map
# dark - the last frame before the move), and catch rankCutHandoff.
HOOK = r"""() => {
  window.__held = null; window.__hand = null;
  const out = rankUpHandOut;
  rankUpHandOut = async function(scene, stop){
    const h = await out(scene, stop);
    if(h && h.ghost){ window.__held = true; await new Promise(res => { window.__goOn = res; }); }
    return h;
  };
  const cut = rankCutHandoff;
  rankCutHandoff = function(ov, sw, hb, key, ghost){
    const r = cut(ov, sw, hb, key, ghost);
    /* frozen IN THE SAME TASK as the move: the frame the move paints. Left
       to a later call, the new planet's orbit turned on in real time while
       the check polled, and the first frame came out up to 24px off on an
       iPad - the copy turns with its bubble, so nothing had parted */
    window.__seek(0);
    window.__hand = { took: r, key };
    return r;
  };
}"""

# Where the copy is (its circle, in CSS px) and how much it is scaled on
# screen (its rim, ring and glow are drawn at its own size, then scaled).
WHERE = r"""() => {
  const g = document.querySelector('.rankmap-stop.ru-ghost'); if(!g) return null;
  const n = g.querySelector('.rankmap-node') || g, r = n.getBoundingClientRect();
  const b = g.closest('.cosmic-icon-badge');
  return { cx: r.left + r.width / 2, cy: r.top + r.height / 2, R: r.width / 2, sc: r.width / (n.offsetWidth || r.width),
           inBubble: !!b, op: +getComputedStyle(g).opacity,
           bubbleOverflow: b ? getComputedStyle(b).overflow : null };
}"""

# Freeze every animation at t, seeking each from where it was when first
# seen (one shared clock with Playwright's for the timers and frames).
SEEK = r"""(t) => window.__seek(t)"""
SEEK_DEF = r"""() => { window.__seek = (t) => {
  const M = window.__seekM || (window.__seekM = new Map());
  document.getAnimations().forEach(a => {
    let m = M.get(a);
    /* one already there at this instant (when the freeze began, or made
       in this same instant - the copy's emblem and its "you are here"
       pulse, restarted by the move and put back on their clock by
       ruClockSnap) keeps the time it has; one made since the last step
       (by a frame or a timer) starts from 0, half a step back - the real
       time between the step and this call must not count */
    if(!m){ m = (window.__seekT == null || window.__seekT === t) ? { c0: a.currentTime == null ? 0 : a.currentTime, t0: t } : { c0: 0, t0: (window.__seekT + t) / 2 }; M.set(a, m); }
    /* the road map's "you are here" pulse (a ring off the circle, again
       every 2.6s) is the flare's own heartbeat, the same either side of
       the move: held where it is, so its restart is not read as a jump */
    const hold = a.animationName === 'rankmap-here';
    try{ a.pause(); a.currentTime = hold ? m.c0 : m.c0 + (t - m.t0); }catch(e){}
  });
  window.__seekT = t;
  void document.body.offsetWidth;
}; }"""


def measure(pg, dpr, tag):
    """Rim colour, ring and glow just outside the copy's edge, from a real
    screenshot. Distances are the copy's own px (x its on-screen scale)."""
    w = pg.evaluate(WHERE)
    if not w:
        return None
    pad = (34 * w["sc"]) + 6
    x0, y0 = max(0, w["cx"] - w["R"] - pad), max(0, w["cy"] - w["R"] - pad)
    side = 2 * (w["R"] + pad)
    png = pg.screenshot(clip={"x": x0, "y": y0, "width": side, "height": side}, animations="allow")
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if OUT:
        os.makedirs(OUT, exist_ok=True)
        im.save(os.path.join(OUT, tag + ".png"))
    px = im.load()
    W, H = im.size
    sc = w["sc"]
    lum = lambda c: .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

    def rays(cx, cy, R):
        """along 180 rays, the brightest pixel from 3px inside the edge to
        1px outside it: (its distance, its colour)"""
        out = []
        for k in range(180):
            th = 2 * math.pi * k / 180
            best = None
            for q in range(0, int(4 * sc * dpr) + 1):
                d = R - 3 * sc + q / dpr
                i, j = int((cx + d * math.cos(th) - x0) * dpr), int((cy + d * math.sin(th) - y0) * dpr)
                if 0 <= i < W and 0 <= j < H:
                    c = px[i, j]
                    if best is None or lum(c) > best[0]:
                        best = (lum(c), d, c, th)
            if best:
                out.append(best[1:])
        return out
    # THE CIRCLE IS FOUND IN THE PIXELS, not taken from the layout box: the
    # rim is ~5 device px wide and a band average moves with a third of a
    # pixel of placement, which the scaled planet system rounds differently
    # from the road map. The rim's peak round 180 rays gives the centre
    # (a circle off by (ox, oy) peaks at R + ox cos + oy sin) and the radius.
    cx, cy, R = w["cx"], w["cy"], w["R"]
    pk = rays(cx, cy, R)
    if pk:
        ox = 2 * sum(d * math.cos(th) for d, c, th in pk) / len(pk)
        oy = 2 * sum(d * math.sin(th) for d, c, th in pk) / len(pk)
        cl = lambda v: max(-1.5, min(1.5, v))
        cx, cy = cx + cl(ox), cy + cl(oy)
        pk = rays(cx, cy, R)
        R = sum(d for d, c, th in pk) / len(pk) + 1.0 * sc     # the peak is mid-rim; the edge is a rim-half out
        R = max(w["R"] - 1.5, min(w["R"] + 1.5, R))
    bands = {"rim": (R - 2.0 * sc, R - .2 * sc), "ring": (R + .4 * sc, R + 4 * sc), "glow": (R + 4 * sc, R + 16 * sc)}
    acc = {k: [0, 0, 0, 0, 0.0] for k in bands}   # r, g, b, n, excess luminance
    for j in range(H):
        for i in range(W):
            x, y = x0 + (i + .5) / dpr, y0 + (j + .5) / dpr
            d = math.hypot(x - cx, y - cy)
            for k, (a, b) in bands.items():
                if a <= d < b:
                    c = px[i, j]
                    A = acc[k]
                    A[0] += c[0]; A[1] += c[1]; A[2] += c[2]; A[3] += 1
                    A[4] += max(0.0, lum(c) - 6)
    res = dict(w)
    res["fit"] = [round(cx - w["cx"], 2), round(cy - w["cy"], 2), round(R - w["R"], 2)]
    res["rimPeak"] = [round(sum(c[ch] for d, c, th in pk) / max(1, len(pk))) for ch in range(3)]
    for k, A in acc.items():
        n = max(1, A[3])
        res[k] = [round(A[0] / n), round(A[1] / n), round(A[2] / n)]
        res[k + "L"] = round(A[4] / n, 1)        # mean excess luminance in the band
    # "gold": how far the rim's colour is from neutral glass (warm minus blue)
    res["rimGold"] = round((res["rimPeak"][0] + res["rimPeak"][1]) / 2 - res["rimPeak"][2], 1)
    return res


def short(m):
    return None if not m else {k: m[k] for k in ("cx", "cy", "R", "fit", "rimPeak", "rim", "rimL", "rimGold", "ringL", "glowL", "op", "bubbleOverflow") if k in m}


def section_move(br):
    print("\nK. the road map's flare goes into the planet system UNCHANGED - the same gold ring, the same glow, the same size and centre - and fades into the lit bubble with no jump")
    for label, w, h, dpr in DEVICES:
        ctx, pg = boot(br, w, h, dpr)
        pg.evaluate(cb.B319_RU_SEED, {})
        pg.evaluate(cb.B319_RU_RUN, {})
        pg.evaluate("()=>{ showHome(); }")
        for i in range(80):
            if pg.evaluate("()=>document.body.classList.contains('rankup-lock')"):
                break
            pg.evaluate("()=>{ const sp=document.querySelector('.rs-spot.is-up'); if(sp) sp.click(); }")
            pg.wait_for_timeout(150)
        pg.evaluate(SEEK_DEF)
        pg.evaluate(HOOK)
        pg.evaluate("()=>document.getElementById('bottomtab-profile').click()")
        for i in range(1500):
            if pg.evaluate("()=>!!window.__held"):
                break
            pg.wait_for_timeout(50)
        if not pg.evaluate("()=>!!window.__held"):
            check("%s: the journey reached the hand-off" % label, False)
            ctx.close()
            continue
        pg.wait_for_timeout(200)
        # the last frame before the move: freeze the timers, then the animations
        # (still held: nothing moves in the next quarter second but the
        # emblem's own loop; a number is SECONDS to pause_at)
        now = pg.evaluate("()=>Date.now()")
        pg.clock.pause_at((now + 250) / 1000.0)
        pg.evaluate(SEEK, 0)
        before = measure(pg, dpr, "%s_before" % label[:4])
        # the move, in this same task: rankCutHandoff runs from the cutscene
        pg.evaluate("async ()=>{ window.__goOn(); for(let i = 0; i < 20 && !window.__hand; i++) await Promise.resolve(); }")
        for i in range(20):
            if pg.evaluate("()=>!!window.__hand"):
                break
            pg.wait_for_timeout(20)
        hand = pg.evaluate("()=>window.__hand")
        if not (hand and hand["took"]):
            check("%s: the hand-off took" % label, False, hand)
            ctx.close()
            continue
        pg.evaluate(SEEK, 0)
        after = measure(pg, dpr, "%s_after" % label[:4])
        print("     before: %s" % short(before))
        print("     after:  %s" % short(after))
        ok_geo = bool(before and after) and abs(before["cx"] - after["cx"]) <= 1.5 and abs(before["cy"] - after["cy"]) <= 1.5 and abs(before["R"] - after["R"]) <= 1.5
        check("%s: the copy keeps its centre and size across the move (within 1.5px)" % label, ok_geo,
              before and after and [round(after[k] - before[k], 2) for k in ("cx", "cy", "R")])
        rim_d = before and after and max(abs(a - b) for a, b in zip(before["rimPeak"], after["rimPeak"]))
        check("%s: its gold rim is the same colour in the first frame after the move (each channel within 12 levels)" % label,
              bool(before and after) and after["inBubble"] and rim_d <= 12, {"before": before and before["rimPeak"], "after": after and after["rimPeak"]})
        rel = lambda a, b: abs(a - b) / max(1.0, b)
        check("%s: its ring and its glow are the same in the first frame after the move (within 15%%)" % label,
              bool(before and after) and rel(after["ringL"], before["ringL"]) <= .15 and rel(after["glowL"], before["glowL"]) <= .15,
              {"ring": [before and before["ringL"], after and after["ringL"]], "glow": [before and before["glowL"], after and after["glowL"]]})
        # the cross-fade, frame by frame
        seq = [after]
        for s in range(1, STEPS + 1):
            pg.clock.run_for(STEP_MS)
            pg.evaluate(SEEK, s * STEP_MS)
            m = measure(pg, dpr, "%s_t%04d" % (label[:4], s * STEP_MS))
            if not m:
                break
            seq.append(m)
        print("     frames (t: rim gold / ring / glow): " + " ".join("%d:%s/%s/%s" % (i * STEP_MS, m["rimGold"], m["ringL"], m["glowL"]) for i, m in enumerate(seq) if i % 2 == 0))
        jumps = {}
        for k in ("rimL", "ringL", "glowL"):
            base = max(1.0, before[k], max(m[k] for m in seq))
            worst = max((abs(seq[i][k] - (before if i == 0 else seq[i - 1])[k]) / base, i * STEP_MS) for i in range(len(seq)))
            jumps[k] = (round(worst[0], 3), worst[1])
        check("%s: from the last frame before the move through %dms of the cross-fade, no %dms step changes the rim, ring or glow by more than 12%% of the most it has" % (label, STEPS * STEP_MS, STEP_MS),
              len(seq) > STEPS // 2 and all(v[0] <= .12 for v in jumps.values()), jumps)
        low = min(m["rimGold"] for m in seq)
        check("%s: the rim stays gold through the whole hand-off (never the colourless glass ball: warm-minus-blue at least half the flare's own)" % label,
              low >= .5 * before["rimGold"], {"flare": before["rimGold"], "lowest": low,
                                               "at": [i * STEP_MS for i, m in enumerate(seq) if m["rimGold"] == low][:3]})
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            try:
                section_move(br)
            except Exception as e:
                check("section_move ran", False, repr(e)[:400])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
