#!/usr/bin/env python3
"""Build 327z10: the chat sheet slides down when swiped away, and smoothly.

Madison: "The chat when swiping down, it just disappears, it doesn't do the
animation that it goes downwards, and it's laggy."

Real touch input (CDP Input.dispatchTouchEvent), installed, on an iPhone 17
Pro Max (440x956 @3), the modern dark layout (the default):

  python3 tools/check-b327z10.py
  python3 tools/check-b327z10.py --against /path/to/old/index.html

  A. While a finger pulls the sheet (past the flat-fill point) and through
     the slide out, the sheet carries no backdrop blur - read off the
     computed style every frame.
  B. Let go past the line, the sheet travels from where the finger let go to
     off the bottom over at least 120ms, and at a quarter of that time it is no more
     than 58% of the way (the old .26s ease-out was about two thirds there).
  C. Closed, it rests off the bottom; opened again it comes back to rest at
     the same place it opened before. A short pull springs back and stays
     open.
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

TRACE = """() => { const p = document.querySelector('.chatdock-panel'); window.__tr = []; window.__stop = false;
  const L = () => { const cs = getComputedStyle(p);
    __tr.push({ t: performance.now(), top: p.getBoundingClientRect().top, bf: cs.backdropFilter, wbf: cs.webkitBackdropFilter || '',
                flat: p.classList.contains('is-flat'), open: chatDockOpen, rel: !!window.__released });
    if(__tr.length < 400 && !window.__stop) requestAnimationFrame(L); };
  requestAnimationFrame(L); }"""

READ = """() => { const p = document.querySelector('.chatdock-panel'); const r = p.getBoundingClientRect();
  return { top: r.top, h: r.height, open: chatDockOpen, inline: p.style.transform, vh: innerHeight }; }"""


ONLY = os.environ.get("B327Z10_ONLY", "ABCDEFG")


def chat_sheet(br):
        label, w, h, dpr = z5b.PHONE
        ctx, pg = z5b.boot(br, w, h, dpr)
        lay = pg.evaluate("() => document.documentElement.dataset.layout + '/' + document.documentElement.dataset.theme")
        check("%s: the modern dark layout is on (%s)" % (label, lay), lay == "modern/dark", lay)
        o = pg.evaluate(z5b.OPEN_CHAT)
        cdp = ctx.new_cdp_session(pg)
        pg.evaluate("() => { document.querySelector('.chatdock-panel .vroom-chat-list').scrollTop = 0; }")
        time.sleep(0.3)
        rest = pg.evaluate(READ)
        CD = max(200, int(rest["h"] * 0.5))
        pg.evaluate(TRACE)
        z5b.drag_to(cdp, o["lx"], max(40, o["ly"] - CD // 3), 0, CD, steps=16)
        time.sleep(0.08)
        pg.evaluate("() => { window.__released = true; }")
        z5b.tend(cdp)
        time.sleep(0.9)
        pg.evaluate("() => { window.__stop = true; }")
        tr = pg.evaluate("() => __tr")
        aft = pg.evaluate(READ)

        moving = [f for f in tr if f["flat"] or (f["rel"] and f["top"] > rest["top"] + 2 and f["top"] < aft["top"] - 1)]
        blurred = [f for f in moving if (f["bf"] not in ("none", "")) or (f["wbf"] not in ("none", ""))]
        check("%s: A. no backdrop blur on any frame while it is pulled or slides out (%d of %d frames blurred)"
              % (label, len(blurred), len(moving)), moving and not blurred, blurred[:3])

        check("%s: and let go past the line, it closes" % label, aft["open"] is False, aft)
        after = [f for f in tr if f["rel"]]
        start = after[0]["top"] if after else rest["top"]
        end = aft["top"]
        way = end - start
        tops = [start] + [f["top"] for f in after]
        moved = [f for f in after if f["top"] > start + 0.5]
        t0 = moved[0]["t"] - 16.7 if moved else 0
        done = next((f["t"] for f in moved if f["top"] >= end - 1), t0)
        dur = done - t0
        q = t0 + dur / 4
        # how far it is at a quarter of its slide, interpolated between frames
        prev = (t0, start)
        at_q = end
        for f in moved:
            if f["t"] >= q:
                a, b = prev, (f["t"], f["top"])
                at_q = a[1] + (b[1] - a[1]) * ((q - a[0]) / max(0.01, b[0] - a[0]))
                break
            prev = (f["t"], f["top"])
        frac = (at_q - start) / max(1, way)
        check("%s: B. it slides from where the finger let go (%.0f) to off the bottom (%.0f) over %.0fms, %.0f%% of the way at a quarter of that (an ease-out that leaps is over 58%%)"
              % (label, start, end, dur, 100 * frac),
              way > 80 and end >= aft["vh"] - 1 and dur >= 120 and frac <= 0.58,
              [round(f["top"]) for f in moved])
        check("%s: C. closed, nothing inline is left on it" % label, aft["inline"] == "", aft)

        # reopen: back where it rested
        pg.evaluate("() => { openChatDock(); }")
        time.sleep(0.6)
        re = pg.evaluate(READ)
        check("%s: C. opened again, it rests where it did (%.0f, was %.0f)" % (label, re["top"], rest["top"]),
              re["open"] and abs(re["top"] - rest["top"]) < 2, [re, rest])

        # a short pull springs back
        pg.evaluate("() => { document.querySelector('.chatdock-panel .vroom-chat-list').scrollTop = 0; }")
        time.sleep(0.3)
        z5b.drag_to(cdp, o["lx"], o["ly"], 0, 60, steps=8, wait=0.05)
        time.sleep(0.3)
        z5b.tend(cdp)
        time.sleep(0.7)
        sp = pg.evaluate(READ)
        check("%s: C. a short slow pull springs back and stays open (%.0f)" % (label, sp["top"]),
              sp["open"] and abs(sp["top"] - rest["top"]) < 2 and sp["inline"] == "", sp)
        ctx.close()


def tab_roll(br):
    print("\nD. a tapped tab's screen waits for the glass to roll over")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    t = pg.evaluate("()=>{const r=document.getElementById('bottomtab-profile').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}}")
    pg.evaluate("""() => { window.__z10 = { mount: null, lens: null, down: null };
      addEventListener('pointerdown', () => { __z10.down = performance.now(); }, true);
      new MutationObserver(() => { if(__z10.mount !== null || __z10.down === null) return;
        __z10.mount = performance.now() - __z10.down;
        const a = document.querySelector('#bottomtabs-lens .tab-lens-body');
        const an = a && a.getAnimations()[0];
        __z10.lensUp = !!document.querySelector('#bottomtabs-lens.is-up'); }).observe(document.getElementById('stage'), { childList: true }); }""")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
    time.sleep(0.06)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(1200)
    r = pg.evaluate("() => Object.assign({}, __z10, { profile: !!document.querySelector('#stage .bottomtab-profile, #stage [class*=profile]'), lit: document.getElementById('bottomtab-profile').classList.contains('active') })")
    check("%s: D. the screen goes in %.0fms after the press - after the glass has crossed (90ms or more), not on the frame after a quick tap's click"
          % (label, r.get("mount") or -1), (r.get("mount") or 0) >= 90 and r.get("lit"), r)
    ctx.close()


def planet(br):
    print("\nE. the planet answers once")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      const tap = () => { const s = document.querySelector('#stage .screen-home-actual .cosmic-sphere-hsw') || [...document.querySelectorAll('#stage .screen-home-actual circle')].find(c => c.getAttribute('fill') === 'url(#cosmicSphereGrad)');
        const b = s.getBoundingClientRect(), x = b.left + b.width / 2, y = b.top + b.height / 2;
        const o = { bubbles: true, cancelable: true, clientX: x, clientY: y, pointerId: 7, isPrimary: true, pointerType: 'touch', button: 0 };
        s.dispatchEvent(new PointerEvent('pointerdown', o)); s.dispatchEvent(new PointerEvent('pointerup', o)); s.dispatchEvent(new MouseEvent('click', o)); };
      const live = () => [...document.querySelectorAll('#stage .home-caption > .hc-item:not(.is-out)')].map(e => e.dataset.text);
      tap(); await wait(500); const a = live();
      tap(); await wait(500); const b = live();
      return { a, b, items: document.querySelectorAll('#stage .home-caption > .hc-item').length }; }""")
    a, b = r["a"], r["b"]
    one = a[0] if len(a) == 1 else ""
    check("%s: E. two taps on the planet: one caption, the same words both times, %d sentences" % (label, one.count(".")),
          len(a) == 1 and len(b) == 1 and a == b and one.count(".") >= 2, r)
    ctx.close()


def tab_special(br):
    print("\nF. the Profile tab's character plays its special")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""async () => { const el = document.querySelector('#bottomtab-profile .bottomtab-icon-avatar');
      if(!el) return { el: false };
      const listed = el.matches(CHAR_SPECIAL_PROMINENT);
      /* the scheduler's own pick: everything due now */
      el.dataset.spNext = '1'; charSpecialBusyUntil = 0; charSpecialTick();
      await new Promise(r => setTimeout(r, 400));
      const on = el.classList.contains('char-special');
      const moving = [...el.querySelectorAll('.cx-sp *')].some(n => n.getAnimations().some(a => a.playState === 'running'));
      return { el: true, listed, on, moving }; }""")
    check("%s: F. the tab's character is one the specials scheduler plays, and its special runs" % label,
          r.get("listed") and r.get("on") and r.get("moving"), r)
    ctx.close()


def daily_ring(br):
    print("\nG. the daily question's ring is a line of light on the glass rim")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2000)
    r = pg.evaluate("""() => { store.dailyQuestionDate = dailyPeriodKey(); showHome(); return 1; }""")
    pg.wait_for_timeout(1200)
    r = pg.evaluate("""() => { const b = document.querySelector('.daily-question-fab'), ring = b && b.querySelector('.dq-ring');
      if(!ring) return null; const svg = ring.querySelector('svg'), k = svg.getBoundingClientRect().width / 100;
      const tr = getComputedStyle(ring.querySelector('.dq-ring-track')), pr = getComputedStyle(ring.querySelector('.dq-ring-prog'));
      const rgb = (tr.stroke.match(/[\d.]+/g) || []).map(Number);
      const br = b.getBoundingClientRect(), rr = ring.getBoundingClientRect();
      return { track: tr.stroke, hue: rgb.length >= 3 ? Math.max(rgb[0], rgb[1], rgb[2]) - Math.min(rgb[0], rgb[1], rgb[2]) : 99,
               progPx: parseFloat(pr.strokeWidth) * k, d: Math.max(Math.abs(br.left - rr.left), Math.abs(br.top - rr.top)) }; }""")
    check("%s: G. the unlit track is the glass rim - no colour of its own (%s)" % (label, r and r["track"]), bool(r) and r["hue"] <= 2, r)
    check("%s: G. the progress is a slim line, %.1fpx (2px at most), on the button's rim" % (label, r and r["progPx"] or -1),
          bool(r) and r["progPx"] <= 2.0 and r["d"] <= 2, r)
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("A", chat_sheet), ("D", tab_roll), ("E", planet), ("F", tab_special), ("G", daily_ring)):
            if k in ONLY or (k == "A" and any(c in ONLY for c in "ABC")):
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
