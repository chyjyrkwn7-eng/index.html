#!/usr/bin/env python3
"""Build 327, package h: the chat sheet - nothing behind it changes, nothing behind it moves.

Madison (Oct 20, his iPhone, the installed app):
  "if the chat is open I click at the bottom, the foreground behind it
   starts changing colors, fix that. I also somehow moved the screen
   behind the chat box even [though] I clicked the chat box when it was
   open. Ensure the app is lag free and works super smooth."

Both with REAL touch input (CDP Input.dispatchTouchEvent), on an iPhone 17
Pro Max (440x956 @3) and an iPad Pro 11" (834x1194 @2), installed:

  python3 tools/check-b327-h.py
  python3 tools/check-b327-h.py --against /tmp/claude-0/b327/index-7ec06e0.html
  B327H_ONLY=A python3 tools/check-b327-h.py

  A. TAPS AT THE BOTTOM OF THE OPEN SHEET CHANGE NOTHING BEHIND IT. A thumb's
     tap slides a few pixels (here 5-17 - Chromium holds back touchmoves inside its ~15px slop, so the last step must pass it); on
     7ec06e0 a tap like that anywhere on the sheet's dead space - its bottom
     padding, the gaps round the composer, the typing line - armed the
     sheet's drag: the sheet jumped and its glass swapped for the flat
     .is-dragging fill and back (.is-settling), so everything seen through it
     changed colour. Every other animation on the page is paused, then each
     tap is shot while the finger is down and again 120ms and 450ms after it
     lifts: outside the control that was touched (a pressed button, a
     focused field), not one pixel may change, and the sheet never takes
     .is-dragging / .is-flat / .is-settling.
  B. A DRAG IN THE SHEET NEVER MOVES THE PAGE BEHIND IT. A tall screen behind
     (Settings) scrolled part-way down; drags on the sheet's header, on its
     composer (field, send button, the row between), on its bottom padding,
     and on its message list past both ends: window.scrollY never moves. The
     list itself still scrolls when dragged in its middle, the field still
     takes focus on a tap, and a pull on the grip still closes the sheet
     (phone).
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
from PIL import Image, ImageChops

PHONE = ("iPhone 17 Pro Max", 440, 956, 3)
TABLET = ("iPad Pro 11\"", 834, 1194, 2)
ONLY = os.environ.get("B327H_ONLY", "AB")
check = cb.check

# the installed app: what sweep-layout does to Chromium
STANDALONE = ("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});"
              "(()=>{const mm=window.matchMedia.bind(window);window.matchMedia=q=>/display-mode:\\s*standalone/.test(q)"
              "?{matches:true,media:q,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}}:mm(q);})();")

OPEN = """async () => { openChatDock(); enterChatRoom('GTEST1');
  for(let i = 0; i < 40 && !document.querySelector('.chatdock-panel .vroom-chat-input'); i++) await new Promise(r => setTimeout(r, 100));
  /* a conversation long enough to scroll, so its ends can be dragged past */
  const list = document.querySelector('.chatdock-panel .vroom-chat-list');
  if(list && !list.querySelector('.h327-msg')){
    for(let i = 0; i < 40; i++){ const m = document.createElement('div'); m.className = 'vroom-chat-msg h327-msg';
      m.textContent = 'Message ' + (i + 1) + ': studying the Penal Code before Monday.'; list.appendChild(m); }
  }
  await new Promise(r => setTimeout(r, 900));
  const p = document.querySelector('.chatdock-panel').getBoundingClientRect();
  return { open: chatDockOpen, top: p.top, bottom: p.bottom, left: p.left, right: p.right }; }"""

RECT = """(sel) => { const el = document.querySelector(sel); if(!el) return null; const r = el.getBoundingClientRect();
  return r.width && r.height ? { l: r.left, t: r.top, r: r.right, b: r.bottom } : null; }"""


def boot(br, w, h, dpr):
    return cb.booted(br, w, h, seed=cb.USED_ACCOUNT, touch=True, dpr=dpr, init=STANDALONE)


def shot(pg):
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")


def changed(a, b, skip, dpr, thr=10):
    """Pixels (device px) that changed by more than thr, outside `skip`."""
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > thr else 0)
    if skip:
        from PIL import ImageDraw
        dr = ImageDraw.Draw(d)
        m = 8
        dr.rectangle([(skip["l"] - m) * dpr, (skip["t"] - m) * dpr, (skip["r"] + m) * dpr, (skip["b"] + m) * dpr], fill=0)
    box = d.getbbox()
    n = d.histogram()[255] if box else 0
    return n, box


def tap(cdp, x, y, path, hold=0.05):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "radiusX": 1, "radiusY": 1}]})
    for (dx, dy) in path:
        time.sleep(0.016)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + dx, "y": y + dy, "radiusX": 1, "radiusY": 1}]})
    time.sleep(hold)


def lift(cdp):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def drag(cdp, x, y, dy, steps=12):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for i in range(1, steps + 1):
        time.sleep(0.016)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + (i % 2), "y": y + dy * i / steps}]})
    time.sleep(0.03)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


JITTERS = [[(0, 5), (1, 11), (1, 17)], [(2, -6), (1, -12), (2, -17)]]


WATCH = """() => { const p = document.querySelector('.chatdock-panel');
  const read = () => { const r = p.getBoundingClientRect(); const cs = getComputedStyle(p);
    return [Math.round(r.top), Math.round(r.height), p.style.transform || '', cs.backgroundColor, cs.backdropFilter || cs.webkitBackdropFilter || '',
            /is-(dragging|flat|settling)/.test(p.className) ? 'flat' : ''].join('|'); };
  window.__rest = read(); window.__seen = [];
  const look = () => { const s = read(); if(s !== __rest && __seen.length < 20) __seen.push(s); };
  if(!window.__watching){ window.__watching = 1;
    const loop = () => { look(); requestAnimationFrame(loop); }; requestAnimationFrame(loop);
    ['touchstart','touchmove','touchend'].forEach(t => addEventListener(t, look, true));
    new MutationObserver(look).observe(p, { attributes: true }); }
  window.__rearm = () => { __rest = read(); __seen.length = 0; }; }"""


def section_a(br):
    print("\nA. taps at the bottom of the open chat change nothing behind it")
    for label, w, h, dpr in (PHONE, TABLET):
        ctx, pg = boot(br, w, h, dpr)
        if dpr == 3:
            # the iPhone's home indicator: Chromium reports every safe-area
            # inset as 0, so the sheet's bottom padding is given the 34px it
            # has on the device - the dead space a thumb taps in. (Without
            # it the padding is 16px, and Chromium's touch adjustment snaps
            # a tap there onto the field above.)
            pg.evaluate("""() => { const s = document.createElement('style');
              s.textContent = '.chatdock-panel:not(.is-kb){ padding-bottom:calc(1rem + 34px) !important; }';
              document.head.appendChild(s); }""")
        o = pg.evaluate(OPEN)
        if not o["open"]:
            check("%s: the chat opened" % label, False, o); ctx.close(); continue
        pg.evaluate(WATCH)
        cdp = ctx.new_cdp_session(pg)
        # everything that animates is held still, so the only thing a tap can
        # change is what the tap itself changes
        cdp.send("Animation.enable")
        cdp.send("Animation.setPlaybackRate", {"playbackRate": 0})
        row = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-row")
        inp = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-input")
        snd = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-send")
        typ = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-typing")
        bot, top, left, right = o["bottom"], o["top"], o["left"], o["right"]
        cx = (left + right) / 2
        # what the glass shows: the upper part of the sheet (the messages over
        # the page behind it) - never the composer the tap may focus
        glass = (int((left + 2) * dpr), int((top + 2) * dpr), int((right - 2) * dpr), int((top + 0.45 * (bot - top)) * dpr))
        pts = [("bottom padding, left", left + 24, bot - 8),
               ("bottom padding, middle", cx, bot - 8),
               ("bottom padding, right", right - 24, bot - 8)]
        if row and inp and snd:
            pts.append(("the gap between field and send", (inp["r"] + snd["l"]) / 2, (row["t"] + row["b"]) / 2))
            pts.append(("just under the composer", cx, row["b"] + 4))
            pts.append(("just over the composer", cx, row["t"] - 4))
            pts.append(("the field", (inp["l"] + inp["r"]) / 2, (inp["t"] + inp["b"]) / 2))
            pts.append(("send", (snd["l"] + snd["r"]) / 2, (snd["t"] + snd["b"]) / 2))
        if typ:
            pts.append(("the typing line", cx, (typ["t"] + typ["b"]) / 2))
        pts.append(("100px up the sheet's foot", left + 30, bot - 100))
        # a touch in the message list is the list's to scroll (section B)
        pts = [p_ for p_ in pts if not pg.evaluate(
            "([x, y]) => { const e = document.elementFromPoint(x, y); return !!(e && e.closest('.vroom-chat-list')); }", [p_[1], p_[2]])]
        worst = []
        for (name, x, y) in pts:
            for path in JITTERS:
                pg.evaluate("() => { const a = document.activeElement; if(a && a.blur && a !== document.body) a.blur(); document.querySelectorAll('.vroom-chat-tray').forEach(t => t.remove()); }")
                pg.wait_for_timeout(200)
                pg.evaluate("() => __rearm()")
                a = shot(pg).crop(glass)
                tap(cdp, x, y, path)
                down = shot(pg).crop(glass)
                lift(cdp)
                pg.wait_for_timeout(120)
                mid = shot(pg).crop(glass)
                pg.wait_for_timeout(330)
                end = shot(pg).crop(glass)
                seen = pg.evaluate("() => __seen.slice()")
                st = pg.evaluate("() => ({ open: chatDockOpen })")
                n = [changed(a, s, None, dpr)[0] for s in (down, mid, end)]
                if max(n) > 0 or seen or not st["open"]:
                    worst.append({"at": name, "jitter": path, "px": n, "sheet": seen[:2], "open": st["open"]})
                if not st["open"]:
                    pg.evaluate(OPEN); pg.evaluate(WATCH)
        check("%s: %d thumb taps (a 5-17px slide) at the bottom of the open sheet - the sheet never moves, grows or swaps its glass, and not a pixel of what it shows changes" % (label, len(pts) * len(JITTERS)),
              not worst, worst[:3] + (["...%d more" % (len(worst) - 3)] if len(worst) > 3 else []))
        ctx.close()


SCROLLER = """() => { const l = document.querySelector('.chatdock-panel .vroom-chat-list'); return l ? { top: l.scrollTop, max: l.scrollHeight - l.clientHeight } : null; }"""


def section_b(br):
    print("\nB. a drag inside the open chat never moves the page behind it")
    for label, w, h, dpr in (PHONE, TABLET):
        ctx, pg = boot(br, w, h, dpr)
        pg.evaluate("() => showAppearance()")
        pg.wait_for_timeout(1200)
        y0 = pg.evaluate("""async () => { const de = document.documentElement; de.style.scrollBehavior = 'auto';
          const max = de.scrollHeight - innerHeight; window.scrollTo(0, Math.round(max / 2)); await new Promise(r => setTimeout(r, 300));
          de.style.scrollBehavior = ''; return { y: scrollY, max }; }""")
        if y0["max"] < 200:
            check("%s: the page behind can scroll (a fair test)" % label, False, y0); ctx.close(); continue
        o = pg.evaluate(OPEN)
        if not o["open"]:
            check("%s: the chat opened" % label, False, o); ctx.close(); continue
        cdp = ctx.new_cdp_session(pg)
        head = pg.evaluate(RECT, ".chatdock-panel .chatdock-roomhead") or pg.evaluate(RECT, ".chatdock-panel .chatdock-tabs")
        inp = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-input")
        snd = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-send")
        row = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-row")
        lst = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-list")
        sy = pg.evaluate("() => scrollY")
        moved = []

        def go(name, x, y, dy):
            before = pg.evaluate("() => scrollY")
            drag(cdp, x, y, dy)
            pg.wait_for_timeout(500)
            after = pg.evaluate("() => ({ y: scrollY, open: chatDockOpen })")
            if abs(after["y"] - before) > 0.5:
                moved.append({"drag": name, "dy": dy, "from": before, "to": after["y"]})
            if not after["open"]:
                pg.evaluate(OPEN)
                pg.wait_for_timeout(300)

        cx = (o["left"] + o["right"]) / 2
        if head:
            go("the room's header, down a little", head["l"] + 12, (head["t"] + head["b"]) / 2, 50)
            go("the room's header, up", head["l"] + 12, (head["t"] + head["b"]) / 2, -60)
        if inp:
            go("the field, up", (inp["l"] + inp["r"]) / 2, (inp["t"] + inp["b"]) / 2, -160)
            go("the field, down", (inp["l"] + inp["r"]) / 2, (inp["t"] + inp["b"]) / 2, 120)
        if snd:
            go("send, up", (snd["l"] + snd["r"]) / 2, (snd["t"] + snd["b"]) / 2, -160)
        if row and inp and snd:
            go("between field and send, up", (inp["r"] + snd["l"]) / 2, (row["t"] + row["b"]) / 2, -160)
        go("the sheet's bottom padding, up", cx, o["bottom"] - 8, -180)
        go("the sheet's bottom padding, down", cx, o["bottom"] - 30, 60)
        lst_ok = None
        if lst:
            ly = (lst["t"] + lst["b"]) / 2
            pg.evaluate("() => { const l = document.querySelector('.chatdock-panel .vroom-chat-list'); l.scrollTop = 0; }")
            go("the list past its top", cx, lst["t"] + 30, 200)
            pg.evaluate("() => { const l = document.querySelector('.chatdock-panel .vroom-chat-list'); l.scrollTop = l.scrollHeight; }")
            go("the list past its bottom", cx, lst["b"] - 30, -200)
            # the list still scrolls when dragged in its middle
            pg.evaluate("() => { const l = document.querySelector('.chatdock-panel .vroom-chat-list'); l.scrollTop = Math.round((l.scrollHeight - l.clientHeight) / 2); }")
            s0 = pg.evaluate(SCROLLER)
            drag(cdp, cx, ly, -90)
            pg.wait_for_timeout(500)
            s1 = pg.evaluate(SCROLLER)
            lst_ok = s0 and s1 and s0["max"] > 40 and s1["top"] > s0["top"] + 20
            check("%s: the conversation still scrolls when dragged (%s -> %s)" % (label, s0 and s0["top"], s1 and s1["top"]), bool(lst_ok), [s0, s1])
        check("%s: page behind at y=%d - no drag on the header, field, send, the row, the padding or the list past its ends moved it" % (label, sy),
              not moved, moved[:4])
        # the field still takes a tap (measured again: a drag may have
        # closed and reopened the sheet)
        if not pg.evaluate("() => chatDockOpen"):
            pg.evaluate(OPEN)
        pg.wait_for_timeout(400)
        inp = pg.evaluate(RECT, ".chatdock-panel .vroom-chat-input")
        if inp:
            tap(cdp, (inp["l"] + inp["r"]) / 2, (inp["t"] + inp["b"]) / 2, [])
            lift(cdp)
            pg.wait_for_timeout(300)
            f = pg.evaluate("() => (document.activeElement || {}).className")
            check("%s: a tap on the field still focuses it" % label, f == "vroom-chat-input", f)
            pg.evaluate("() => document.activeElement && document.activeElement.blur()")
        # the grip still closes the sheet (phone; the tablet has none)
        if w < 640:
            g = pg.evaluate(RECT, ".chatdock-panel .chatdock-grip")
            if g:
                drag(cdp, (g["l"] + g["r"]) / 2, (g["t"] + g["b"]) / 2, 240, steps=14)
                pg.wait_for_timeout(600)
                c = pg.evaluate("() => ({ open: chatDockOpen, y: scrollY })")
                check("%s: a pull down on the grip still closes the sheet, and the page is where it was" % label,
                      c["open"] is False and abs(c["y"] - sy) <= 1, {"after": c, "was": sy})
        ctx.close()


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("A", section_a), ("B", section_b)):
            if k in ONLY:
                try:
                    fn(br)
                except Exception as e:  # a section that throws is a failure, not a crash
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
