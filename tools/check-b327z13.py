#!/usr/bin/env python3
"""Build 327z13: the tab bar's glass crosses slower, and nothing is built under it.

Madison: "The bottom tab is getting better but the pill bubble thing still
moves too fast when clicking through the bottom tab. It also lags. Please
ensure it's perfect, leave no stone unturned."

Real touch input on an iPhone 17 Pro Max (440x956 @3), installed:

  python3 tools/check-b327z13.py
  python3 tools/check-b327z13.py --against /path/to/old/index.html

  S. The glide, read off the lens's own 60fps track (so the machine's speed
     cannot move it): a quarter to two fifths of the way at 4 frames, no
     more than four fifths at 8, nine tenths by 16, and never past the tab.
  T. A quick tap (60ms): the lens does not start to shrink until it is
     95% of the way to the tapped tab, and is up 320ms or more from the
     press - a glide you can watch (the 327z12 one was down at ~260ms).
  U. The tapped tab's screen is built only once the glass has crossed: at
     the moment #stage changes, 270ms or more after the press, the lens's
     own track is 90% or more of the way. (A build is a long main-thread
     task; under the glide it held the glass's frames.)
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("z5b", os.path.join(HERE, "check-b327z5-b.py"))
z5b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(z5b)   # check-behaviour reads --against itself
cb = z5b.cb
check = cb.check
from playwright.sync_api import sync_playwright

ONLY = os.environ.get("B327Z13_ONLY", "STU")

# the lens body's centre x on each keyframe, and its height
TRACK = """() => { const body = document.querySelector('#bottomtabs-lens .tab-lens-body'); const a = body && body.getAnimations()[0];
  if(!a) return null;
  const rd = k => { const m = /translate3d\\(([-\\d.]+)px,\\s*([-\\d.]+)px[^)]*\\) scale\\(([-\\d.]+),\\s*([-\\d.]+)/.exec(k.transform || '');
    return m ? { cx: +m[1] + +m[3] * 50, h: +m[4] } : null; };
  return { t: a.currentTime, frames: a.effect.getKeyframes().map(rd).filter(Boolean) }; }"""


def centre(pg, tid):
    return pg.evaluate("id => { const r = document.getElementById(id).getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }", tid)


def glide(br):
    print("\nS. the glide's pace")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    for tid in ("bottomtab-profile", "bottomtab-calendar"):
        t = centre(pg, tid)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
        pg.wait_for_timeout(30)
        r = pg.evaluate(TRACK)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(1500)
        xs = [f["cx"] for f in (r or {}).get("frames", [])]
        p = [(x - xs[0]) / ((xs[-1] - xs[0]) or 1) for x in xs] if xs else []
        ok = len(p) > 17 and .25 <= p[4] <= .42 and p[8] <= .8 and p[16] >= .9 and max(p) <= 1.01
        check("%s: S. to %s the glass is %s of the way at frames 4 / 8 / 16, never past it (max %.3f)"
              % (label, tid.split("-")[1], p and "%.2f / %.2f / %.2f" % (p[4], p[8], p[min(16, len(p) - 1)]), max(p) if p else -1),
              ok, [round(v, 3) for v in p[:24]])
    ctx.close()


def quick_tap(br):
    print("\nT. a quick tap stays up until it has arrived")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    t = centre(pg, "bottomtab-calendar")
    x0 = pg.evaluate(TRACK)
    pg.evaluate("() => { window.__t = {}; addEventListener('pointerdown', () => { __t.down = performance.now(); }, { capture: true, once: true }); addEventListener('touchend', () => { __t.up = performance.now(); }, { capture: true, once: true }); }")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
    pg.wait_for_timeout(20)
    a = pg.evaluate(TRACK)
    time.sleep(0.04)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(30)
    r = pg.evaluate(TRACK)
    tt = pg.evaluate("() => window.__t")
    rel = (tt.get("up") or 0) - (tt.get("down") or 0)
    pg.wait_for_timeout(1500)
    start = (a or {}).get("frames", [{}])[0].get("cx")
    fr = (r or {}).get("frames", [])
    if not fr or start is None:
        check("%s: T. the release has a track" % label, False, [a, r])
        ctx.close()
        return
    end = fr[-1]["cx"]
    hmax = max(f["h"] for f in fr)
    shrink = next((i for i, f in enumerate(fr) if i > 0 and f["h"] < hmax * .97 and fr[i - 1]["h"] >= f["h"] and any(g["h"] >= hmax * .99 for g in fr[:i])), None)
    prog = (fr[shrink]["cx"] - start) / ((end - start) or 1) if shrink is not None else None
    upMs = rel + shrink * 1000 / 60 if shrink is not None else None
    check("%s: T. a 60ms tap's lens starts to shrink only once it is 95%%+ of the way (%.2f), %.0fms after the press (320+)"
          % (label, prog if prog is not None else -1, upMs or -1), prog is not None and prog >= .95 and (upMs or 0) >= 320, [prog, shrink, upMs])
    ctx.close()


def build_after(br):
    print("\nU. the screen is built once the glass has crossed")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    for tid in ("bottomtab-profile", "bottomtab-calendar", "bottomtab-home"):
        t = centre(pg, tid)
        pg.evaluate("""() => { window.__u = { mount: null, down: null, track: null, at: null };
          addEventListener('pointerdown', () => { __u.down = performance.now(); setTimeout(() => {
            const body = document.querySelector('#bottomtabs-lens .tab-lens-body'); const a = body && body.getAnimations()[0];
            if(a) __u.track = a; }, 0); }, { capture: true, once: true });
          const mo = new MutationObserver(() => { if(__u.mount !== null || __u.down === null) return;
            __u.mount = performance.now() - __u.down;
            const body = document.querySelector('#bottomtabs-lens .tab-lens-body'); const a = body && body.getAnimations()[0];
            __u.at = a ? a.currentTime : null; mo.disconnect(); });
          mo.observe(document.getElementById('stage'), { childList: true }); }""")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
        time.sleep(0.06)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(1600)
        # where the glide (the press's own track) was at the moment of the build:
        # the same spring is replayed from rest to read it at that time
        r = pg.evaluate("""() => { const m = __u.mount, a = __u.track;
          if(!a || m === null) return { mount: m, prog: null, track: !!a };
          const rd = k => { const mm = /translate3d\\(([-\\d.]+)px,\\s*([-\\d.]+)px[^)]*\\) scale\\(([-\\d.]+)/.exec(k.transform || ''); return mm ? +mm[1] + +mm[3] * 50 : null; };
          const xs = a.effect.getKeyframes().map(rd).filter(v => v !== null);
          const i = Math.min(xs.length - 1, Math.floor(m / (1000 / 60)));
          return { mount: m, prog: (xs[i] - xs[0]) / ((xs[xs.length - 1] - xs[0]) || 1),
                   lit: document.querySelector('.bottomtab.active') && document.querySelector('.bottomtab.active').id }; }""")
        check("%s: U. %s's screen goes in %.0fms after the press (270+), the glide %.0f%% of the way (90%%+), never under it"
              % (label, tid.split("-")[1], r.get("mount") or -1, 100 * (r.get("prog") or 0)),
              (r.get("prog") or 0) >= .9 and (r.get("mount") or 0) >= 270 and r.get("lit") == tid, r)
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("S", glide), ("T", quick_tap), ("U", build_after)):
            if k in ONLY:
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
