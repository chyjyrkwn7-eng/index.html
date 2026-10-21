#!/usr/bin/env python3
"""Build 327, round 6, stream T - the rank-up cutscene darker and deeper, and
the road map -> planet system hand-off slow and mysterious.

Madison: "The cutscene for ranking up needs to be way cooler, darker." and
"When the road map transitions to the planet system it's so loud and fast
and bad..... shoukd be like Pokemon with a dark mysterious noise ... We
don't want creepy."

  H. the hand-off, on a real rank-up journey (iPhone 17 Pro Max, installed):
     H1 the road map's flare draws back slower (its draw-back animation
        longer than 2000ms);
     H2 the map goes dark over longer than 1300ms, ending with the draw-back;
     H3 the flare then HOLDS alone in the dark (rankUpHandOut returns well
        after the veil has finished);
     H4 the planet system pulls back slower than 2800ms;
     H5 the cutscene's attention waits for the pull-back to settle (it
        starts at least 80% of the pull-back after the cut) - not in the
        middle of it.
  D. the cutscene itself (playTierCutscene, Platinum from Gold, both
     reference devices), in the middle of the whirl:
     D1 the backdrop is darker: the mean luminance of the screen's outer
        band (the 12% next to every edge) under 3.0 (build 326: 3.8-3.9);
     D2 the corners are near black (each corner pixel's luminance under 2);
     D3 it has depth: a starfield, the new rank's colour as a low glow, and
        light rays, each showing during the whirl, and a vignette;
     D4 the flash has no white-out at its heart (its first stop is not pure
        white) and a deep bloom leads it (::before animated);
     D5 the title comes in like a film's: scaled up before it settles, with
        a hairline of light drawn under it.

  python3 tools/check-b327t.py
  python3 tools/check-b327t.py --against /tmp/base327.html
"""
import importlib.util
import io
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
from playwright.sync_api import sync_playwright
from PIL import Image

FAILURES = []
OUT = os.environ.get("B327T_OUT")
ONLY = os.environ.get("B327T_ONLY", "")
if "--against" in sys.argv:
    print("against: %s" % cb.SRC)


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:600]) if detail else ""))
    if not ok:
        FAILURES.append(name)


STANDALONE = """(() => { try{ Object.defineProperty(navigator, 'standalone', { get: () => true, configurable: true }); }catch(e){}
  const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q) ? { matches: true, media: q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} } : mm(q); })();"""


def boot(br, w, h, dpr):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, is_mobile=True, device_scale_factor=dpr)
    ctx.add_init_script(STANDALONE)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');"
                        "localStorage.setItem('class26e.drill.v1', '%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');}catch(e){}" % cb.USED_ACCOUNT)
    pg = cb.open_page(ctx)
    pg.goto(cb.URL)
    pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    return ctx, pg


HOOK = r"""() => {
  const R = window.__h = { T0: performance.now() };
  const now = () => Math.round(performance.now() - R.T0);
  const out = rankUpHandOut;
  rankUpHandOut = async function(scene, stop){
    R.start = now();
    const p = out(scene, stop);
    try{
      const g = document.querySelector('body > .ru-ghost'), v = document.querySelector('.ru-veil');
      R.draw = g && g.__ruDraw ? Math.round(g.__ruDraw.effect.getTiming().duration) : null;
      R.veil = v ? v.getAnimations().map(a => { const t = a.effect.getTiming(); return { delay: t.delay, dur: t.duration }; }) : null;
      if(v && v.getAnimations()[0]) v.getAnimations()[0].finished.then(() => { R.veilDone = now(); }, () => { R.veilDone = R.veilDone || now(); });
    }catch(e){ R.err = String(e); }
    const h = await p;
    R.ret = now();
    return h;
  };
  const cut = rankCutHandoff;
  rankCutHandoff = function(ov, sw, hb, key, ghost){
    const r = cut(ov, sw, hb, key, ghost);
    R.cut = now(); R.took = r;
    const mo = new MutationObserver(() => { if(R.attn == null && ov.querySelector('.rank-chg.is-attention, .rank-attn.is-attention')) R.attn = now(); });
    mo.observe(ov, { subtree: true, childList: true });
    const read = () => { const m = /transform\s+(\d+)ms/.exec(sw.style.transition || ''); if(m) R.zoom = +m[1]; };
    [300, 900, 1500, 2500].forEach(t => setTimeout(read, t));
    return r;
  };
}"""


def section_handoff(br):
    print("\nH. the road map -> planet system hand-off: slow, held in the dark, the planet rising out of it")
    ctx, pg = boot(br, 440, 956, 2)
    try:
        pg.evaluate(cb.B319_RU_SEED, {})
        pg.evaluate(cb.B319_RU_RUN, {})
        pg.evaluate("()=>{ showHome(); }")
        for i in range(80):
            if pg.evaluate("()=>document.body.classList.contains('rankup-lock')"):
                break
            pg.evaluate("()=>{ const sp=document.querySelector('.rs-spot.is-up'); if(sp) sp.click(); }")
            pg.wait_for_timeout(150)
        pg.evaluate(HOOK)
        pg.evaluate("()=>document.getElementById('bottomtab-profile').click()")
        r = {}
        for i in range(900):
            r = pg.evaluate("()=>window.__h")
            if r.get("attn") is not None and r.get("zoom"):
                break
            pg.wait_for_timeout(100)
        print("     %s" % r)
        draw = r.get("draw") or 0
        check("H1: the road map's flare draws back slower than build 326's 2000ms", draw > 2000, draw)
        veil = (r.get("veil") or [{}])[0]
        vd, vdel = veil.get("dur") or 0, veil.get("delay") or 0
        check("H2: the map goes dark over longer than 1300ms, ending with the draw-back", vd > 1300 and abs(vd + vdel - draw) < 30, veil)
        ret, st = r.get("ret"), r.get("start")
        held = (ret - r["veilDone"]) if (ret is not None and r.get("veilDone") is not None) else None
        check("H3: the flare holds alone in the dark after the veil (at least 450ms)", held is not None and held >= 450, held)
        zoom = r.get("zoom") or 0
        check("H4: the planet system pulls back slower than 2800ms", r.get("took") and zoom > 2800, [r.get("took"), zoom])
        a, c = r.get("attn"), r.get("cut")
        check("H5: the cutscene's attention starts once the pull-back has (nearly) settled",
              a is not None and c is not None and zoom and (a - c) >= .8 * zoom, [a, c, zoom])
    finally:
        ctx.close()


SCENE = r"""() => { document.querySelectorAll('#intro-pop, .nova-talk').forEach(n => n.remove());
  window.__sc = playTierCutscene('vanguard', { from: 'veteran', onDone(){} }); }"""

LAYERS = r"""() => { const o = document.getElementById('supernova-cutscene'); if(!o) return null;
  const op = sel => { const e = o.querySelector(sel); return e ? +getComputedStyle(e).opacity : null; };
  const fl = o.querySelector('.supernova-flash');
  const ti = o.querySelector('.supernova-title');
  const tm = ti ? new DOMMatrix(getComputedStyle(ti).transform) : null;
  const ta = ti ? getComputedStyle(ti, '::after') : null;
  const fb = fl ? getComputedStyle(fl, '::before') : null;
  return { c: o.className, sky: op('.rank-sky'), neb: op('.rank-nebula'), rays: op('.rank-rays'), vig: op('.rank-vignette'),
    flashBg: fl ? getComputedStyle(fl).backgroundImage.slice(0, 80) : null,
    deep: fb ? (fb.content !== 'none' && fb.content !== 'normal' && /rank-flash-deep/.test(fb.animationName || '') || /rank-flash-deep/.test([...document.styleSheets].map(s => { try{ return [...s.cssRules].map(r => r.cssText).join(' '); }catch(e){ return ''; } }).join(' '))) : false,
    titleScale: tm ? tm.a : null, titleRule: ta ? (ta.content !== 'none' && ta.content !== 'normal') : false }; }"""


def lum(p):
    return .2126 * p[0] + .7152 * p[1] + .0722 * p[2]


def section_dark(br):
    print("\nD. the cutscene: darker, deeper, a cooler flash, a cinematic title")
    for label, w, h, dpr in (("iPhone 17 Pro Max", 440, 956, 2), ("iPad Pro 11\"", 834, 1194, 2)):
        ctx, pg = boot(br, w, h, dpr)
        try:
            pg.evaluate("()=>{ showHome(); }")
            pg.wait_for_timeout(1200)
            pg.evaluate(SCENE)
            early = pg.evaluate(LAYERS)
            ok = False
            for i in range(400):
                c = pg.evaluate("()=>{ const o = document.getElementById('supernova-cutscene'); return o ? o.className : ''; }")
                if "is-cutspin" in c:
                    ok = True
                    break
                pg.wait_for_timeout(100)
            if not ok:
                check("%s: the whirl started" % label, False)
                continue
            pg.wait_for_timeout(4200)
            L = pg.evaluate(LAYERS)
            img = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            if OUT:
                os.makedirs(OUT, exist_ok=True)
                img.save(os.path.join(OUT, "whirl_%s_%s.png" % (label[:4].strip(), "against" if "--against" in sys.argv else "this")))
            W, H = img.size
            px = img.load()
            bw, bh = int(W * .12), int(H * .12)
            tot = n = 0
            for y in range(0, H, 3):
                for x in range(0, W, 3):
                    if x < bw or x >= W - bw or y < bh or y >= H - bh:
                        tot += lum(px[x, y]); n += 1
            band = tot / max(1, n)
            corners = [round(lum(px[x, y]), 2) for x, y in ((2, 2), (W - 3, 2), (2, H - 3), (W - 3, H - 3))]
            print("     %s: band %.2f corners %s layers %s" % (label, band, corners, L))
            check("%s D1: the backdrop's outer band is darker (mean luminance under 3.0; build 326 measures 3.8-3.9)" % label, band < 3.0, round(band, 2))
            check("%s D2: the corners are near black (each under 2)" % label, max(corners) < 2, corners)
            check("%s D3: a starfield, the rank's low glow and light rays show during the whirl, over a vignette" % label,
                  bool(L) and (L.get("sky") or 0) > .2 and (L.get("neb") or 0) > .3 and (L.get("rays") or 0) > .1 and L.get("vig") is not None,
                  L and {k: L.get(k) for k in ("sky", "neb", "rays", "vig")})
            fb = (L or {}).get("flashBg") or ""
            check("%s D4: the flash has no white-out at its heart, and a deep bloom leads it" % label,
                  fb and not fb.startswith("radial-gradient(circle, rgb(255, 255, 255)") and L.get("deep"), [fb, L and L.get("deep")])
            ts = (early or {}).get("titleScale")
            check("%s D5: the title comes in scaled and settles, a hairline of light drawn under it" % label,
                  ts is not None and ts > 1.05 and (early or {}).get("titleRule"), [ts, early and early.get("titleRule")])
        finally:
            ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            for name, fn in (("H", section_handoff), ("D", section_dark)):
                if ONLY and name not in ONLY:
                    continue
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % name, False, repr(e)[:400])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
