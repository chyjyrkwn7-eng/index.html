#!/usr/bin/env python3
"""Build 327 round 7 (b327y): no hard line round a circle.

Madison: "some of the circles shaped stuff across the app, especially the
Home Screen has like a hard but very hard to notice line at the bottom and
maybe the top I can tell. For example some of the flares have a line at the
bottom of the bubble that makes it look weird. The daily question button is
the same."

What the line was, measured at 3x down each one's centre column:
  1. Each of these lays a top-lit gradient over its fill and has a 1px
     see-through border. The image is sized to the padding box and REPEATS
     under the border, so the strip under the BOTTOM border showed the
     gradient's TOP - its brightest highlight: a 3-device-px bright band
     along the bottom rim (an unlit flare bubble's rim went 120 -> 162 of
     255; the daily button's 56 -> 73).
  2. The chat button and Pause wore --surface-shadow, whose catch-light is
     inset 0 1px 0 (no blur): a hairline ruled round the top of a circle,
     33-43 levels over the glass beside it.

So on an iPhone 17 Pro Max (440x956 at 3x), every animation paused and the
rank emblems hidden (they are the bubble's picture, not its shading), for
each round control on Home - the seven rank flare bubbles, each lit and
unlit; the secret flares not under a bubble; the daily question button
ready and answered; the chat button - and Pause on a test:
  a. the element is shot as it is and again with ONLY its background image
     taken away; the difference down its centre column is what the image
     itself paints. From just inside the circle's own anti-aliased outer
     edge, 8 device rows in at the top and at the bottom, that may not
     step by more than MAXJUMP = 9 levels from one row to the next. A
     repeated tile under a see-through border is exactly such a step.
     An opaque border (a lit flare's rim) hides what is under it and is
     skipped. Old build: unlit bubbles 16-40, the daily button 20, chat
     and Pause 15. Fixed: 0-7.1 (the 7 is the 24% rim's own tint over
     the top highlight - the outline, not a line).
  b. no inset shadow with a y offset and under 2px of blur (a hairline)
     on it or its ::before/::after.
Lit bubbles pass on both builds: their rim is opaque, so the repeat never
showed through it.

  python3 tools/check-b327y.py [--against FILE]

Fails on 61d9620.
"""
import importlib.util, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
from PIL import Image

check, booted, USED_ACCOUNT = cb.check, cb.booted, cb.USED_ACCOUNT
MAXJUMP = 9
PAD = 6
DPR = 3


def lum(p):
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def freeze(pg):
    # The emblem drawn inside a bubble is its picture, not its shading, and
    # it is screen-blended over the glass, so it would change what taking
    # the gradient away does: hidden, so the shots read the glass alone.
    pg.add_style_tag(content=".cosmic-icon-badge.cosmic-badge-rank > svg.cosmic-rank-emblem, .cosmic-icon-badge.cosmic-badge-rank > .cosmic-rank-anim{ visibility:hidden !important; }")
    pg.evaluate("() => { document.getAnimations().forEach(a => { try{ a.pause(); a.currentTime = 0; }catch(e){} }); }")
    pg.wait_for_timeout(250)


def bottom_light(pg, el, idx):
    r = el.bounding_box()
    if not r or r["width"] < 4:
        return None
    clip = {"x": r["x"] - PAD, "y": r["y"] - PAD, "width": r["width"] + 2 * PAD, "height": r["height"] + 2 * PAD}

    def prof():
        im = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        W, H = im.size
        cx = W // 2
        return [sum(lum(im.getpixel((x, y))) for x in range(cx - 2, cx + 3)) / 5.0 for y in range(H)], H
    a, H = prof()
    cls = "y-noimg-%d" % idx
    pg.add_style_tag(content=".%s{ background-image:none !important; }" % cls)
    el.evaluate("(e, c) => e.classList.add(c)", cls)
    pg.wait_for_timeout(80)
    b, _ = prof()
    el.evaluate("(e, c) => e.classList.remove(c)", cls)
    pg.wait_for_timeout(40)
    c = [a[y] - b[y] for y in range(H)]
    top, bot = PAD * DPR, H - PAD * DPR
    # An OPAQUE border (a lit flare's rim) hides whatever is under it, so
    # nothing there can be the gradient's line, and the step from the rim
    # into the glass is the rim, not a line: such a border is skipped. A
    # see-through one is read through, since that is where the line was.
    bw, ba = el.evaluate("""(e) => { const cs = getComputedStyle(e); const bc = cs.borderTopColor; let al = 1;
      const m = bc.match(/rgba\\(([^)]*)\\)/), sl = bc.match(/\\/\\s*([\\d.]+)\\s*\\)/);
      if(m) al = Number(m[1].split(',')[3]); else if(sl) al = Number(sl[1]);
      return [parseFloat(cs.borderTopWidth) || 0, al]; }""")
    if ba > .9:
        skip = int(round(bw * DPR)) + 1
        top, bot = top + skip, bot - skip
    # where the circle's own outer edge falls (its anti-aliased step, which
    # lands a row either way with the box's fractional position) and the
    # row after it are the outline; the window starts past them
    ts = max(range(PAD * DPR - 2, PAD * DPR + 4), key=lambda y: abs(a[y] - a[y - 1]))
    bs = max(range(H - PAD * DPR - 3, H - PAD * DPR + 3), key=lambda y: abs(a[y] - a[y - 1]))
    top, bot = max(top, ts), min(bot, bs)
    jt = max(abs(c[y] - c[y - 1]) for y in range(top + 2, top + 10))
    jb = max(abs(c[y] - c[y - 1]) for y in range(bot - 9, bot - 1))
    return round(jt, 1), round(jb, 1)


HARD = r"""(e) => {
  const out = [];
  for(const pseudo of [null, '::before', '::after']){
    const bs = getComputedStyle(e, pseudo).boxShadow;
    if(!bs || bs === 'none') continue;
    for(const p of bs.split(/,(?![^(]*\))/)){
      if(!/inset/.test(p)) continue;
      const m = p.match(/rgba?\(([^)]*)\)/);
      const col = m ? m[1].split(',').map(Number) : [0, 0, 0, 1];
      const al = col.length > 3 ? col[3] : 1;
      const nums = (p.replace(/[a-z-]+\([^)]*\)/g, '').match(/-?[\d.]+px/g) || []).map(parseFloat);
      const y = nums[1] || 0, blur = nums[2] || 0;
      if(Math.abs(y) >= 1 && blur < 2 && al >= .08) out.push((pseudo || '') + ' ' + p.trim());
    }
  }
  return out; }"""


def judge(pg, el, name, idx):
    if el is None:
        check(name + ": found on screen", False)
        return
    j = bottom_light(pg, el, idx)
    check(name + ": its gradient runs smoothly to the top edge", j is not None and j[0] <= MAXJUMP, "jump %s" % (j and j[0]))
    check(name + ": its gradient runs smoothly to the bottom edge", j is not None and j[1] <= MAXJUMP, "jump %s" % (j and j[1]))
    hard = el.evaluate(HARD)
    check(name + ": no hairline catch-light or lip round it", not hard, "; ".join(hard)[:160])


def home(br):
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True, dpr=DPR)
    try:
        pg.wait_for_timeout(1500)
        n = pg.evaluate("() => document.querySelectorAll('.cosmic-icon-badge.cosmic-badge-rank').length")
        check("Home has its seven flare bubbles", n == 7, n)
        for lit in (True, False):
            pg.evaluate("""(lit) => document.querySelectorAll('.cosmic-icon-badge.cosmic-badge-rank').forEach(b => b.classList.toggle('cosmic-badge-lit', lit))""", lit)
            freeze(pg)
            for i in range(n):
                el = pg.query_selector_all(".cosmic-icon-badge.cosmic-badge-rank")[i]
                tier = el.get_attribute("data-rank-tier") or str(i)
                judge(pg, el, "flare bubble %s (%s)" % (tier, "lit" if lit else "unlit"), i + (0 if lit else 10))
        for i, el in enumerate(pg.query_selector_all(".cosmic-flare-dot")):
            bb = el.bounding_box()
            # a secret flare passing under a rank bubble's glass is the
            # bubble's picture there, not the flare's
            under = el.evaluate("""(e) => { const r = e.getBoundingClientRect();
              return [...document.querySelectorAll('.cosmic-icon-badge.cosmic-badge-rank')].some(b => { const q = b.getBoundingClientRect();
                return q.left < r.right + 3 && q.right > r.left - 3 && q.top < r.bottom + 3 && q.bottom > r.top - 3; }); }""")
            if bb and bb["width"] > 4 and not under:
                judge(pg, el, "secret flare %d" % i, 20 + i)
        for k, state in enumerate(("is-ready", "is-done")):
            pg.evaluate("""(s) => { const f = document.querySelector('.daily-question-fab'); f.classList.remove('is-ready', 'is-done', 'is-charging', 'is-fresh'); f.classList.add(s); }""", state)
            freeze(pg)
            judge(pg, pg.query_selector(".daily-question-fab"), "daily question button (%s)" % state.replace("is-", ""), 30 + k)
        judge(pg, pg.query_selector("#chatdock-btn"), "chat button", 40)
    finally:
        ctx.close()


def pause(br):
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, touch=True, dpr=DPR)
    try:
        pg.evaluate("""() => { cfg.mode = 'drill'; beginRun(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic === 'Identity Crimes').slice(0, 5), null); }""")
        for _ in range(40):
            pg.wait_for_timeout(250)
            if pg.evaluate("() => !!document.querySelector('#pausebtn:not([hidden])') && !!document.querySelector('.choice')"):
                break
        freeze(pg)
        judge(pg, pg.query_selector("#pausebtn:not([hidden])"), "Pause on a test", 41)
    finally:
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            for fn in (home, pause):
                try:
                    fn(br)
                except Exception as e:
                    check("%s ran to the end" % fn.__name__, False, str(e)[:200])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
