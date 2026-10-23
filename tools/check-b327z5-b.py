#!/usr/bin/env python3
"""Build 327z5, package b: swipe a sheet down from anywhere on it.

Madison:
  "The chat box when it's up, you can't swipe down from it unless you are
   swiping down from the very top."
  "The test start menu with all the options. The swiping down function is
   broken ... The x button in the top right you can't see it cause color.
   When you do swipe down it glitches and changes colors."

Real touch input (CDP Input.dispatchTouchEvent), installed, on an iPhone 17
Pro Max (440x956 @3) and an iPad Pro 11" (834x1194 @2):

  python3 tools/check-b327z5-b.py
  python3 tools/check-b327z5-b.py --against /path/to/old/index.html
  B327Z5B_ONLY=A python3 tools/check-b327z5-b.py

  A. THE START SHEET (Drill's, and the Virtual Room's Match settings on the
     phone). A drag down from the middle of it (the bank caption, a section
     card - not a slider) follows the finger 1:1 once past its slop, and
     nothing about the sheet's look changes while it moves: its computed
     fill is the resting one, and a patch of it, read off the pixels where
     the sheet now is, is the resting colour. Let go past the line, it slides
     out and closes; a short pull springs back with the sheet left as it
     was. Scrolled down, a drag down scrolls instead; a sideways drag does
     nothing. The close X is a visible circle with an X at 4.5:1 or more.
  B. THE CHAT SHEET. With the message list scrolled to its top, a drag down
     in the list pulls the sheet and closes it; with the list scrolled down,
     the same drag scrolls the list and the sheet stays; a drag down on the
     composer row (not the field) pulls it too. The page behind never moves.
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

PHONE = ("iPhone 17 Pro Max", 440, 956, 3)
TABLET = ("iPad Pro 11\"", 834, 1194, 2)
ONLY = os.environ.get("B327Z5B_ONLY", "AB")
check = cb.check

STANDALONE = ("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});"
              "(()=>{const mm=window.matchMedia.bind(window);window.matchMedia=q=>/display-mode:\\s*standalone/.test(q)"
              "?{matches:true,media:q,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}}:mm(q);})();")


def boot(br, w, h, dpr):
    return cb.booted(br, w, h, seed=cb.USED_ACCOUNT, touch=True, dpr=dpr, init=STANDALONE)


def shot(pg):
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")


def mean(img, box):
    c = img.crop(box)
    px = list(c.getdata())
    n = len(px) or 1
    return tuple(sum(p[i] for p in px) / n for i in range(3))


def tstart(cdp, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})


def tmove(cdp, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})


def tend(cdp):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def drag_to(cdp, x, y, dx, dy, steps=14, wait=0.022):
    tstart(cdp, x, y)
    for i in range(1, steps + 1):
        time.sleep(wait)
        tmove(cdp, x + dx * i / steps, y + dy * i / steps)


OPEN_SETUP = """async (vr)=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());
  store.seenUnitSelectTour = true; store.seenUnitHoldTip = true;
  if(vr){ showVirtualRoomSetup({ units:['Identity Crimes'], count:null, game:'race' }); await wait(900);
    document.querySelector('.vroom-setup-go').click(); }
  else { cfg.mode='drill'; cfg.units=[]; showSetup(); await wait(900);
    document.querySelector('.picks .pick .pname').click(); await wait(400);
    document.getElementById('nextbtn').click(); }
  await wait(600);
  const sh=document.querySelector('#unitoptions-modal .unitoptions-modal-sheet');
  for(let i=0;i<40 && sh && sh.getAnimations().some(a=>a.playState==='running');i++) await wait(100);
  await wait(250);
  if(!sh || document.getElementById('unitoptions-modal').hidden) return null;
  sh.scrollTop = 0;
  const r=sh.getBoundingClientRect();
  /* a point on the sheet that is not a control that owns its own drag */
  const cand=[...sh.querySelectorAll('.sect-caption, .bank-caption, .ohint, .slab, .sheet-summary-units, .unitoptions-modal-title')]
    .map(e=>e.getBoundingClientRect()).filter(b=>b.height>4 && b.top>r.top+40 && b.bottom<Math.min(innerHeight,r.bottom)-80);
  const b=cand[0] || { left:r.left+40, right:r.left+120, top:r.top+120, bottom:r.top+140 };
  const x=Math.round((b.left+b.right)/2), y=Math.round((b.top+b.bottom)/2);
  const e=document.elementFromPoint(x,y);
  const cs=getComputedStyle(sh);
  return { top:r.top, left:r.left, right:r.right, bottom:r.bottom, h:r.height, x, y, at:(e&&e.className)||'',
           look: cs.backgroundColor+'|'+cs.backgroundImage, scrolls: sh.scrollHeight>sh.clientHeight+20 }; }"""

TRACE = """()=>{ const sh=document.querySelector('#unitoptions-modal .unitoptions-modal-sheet'); window.__tr=[];
  const L=()=>{ const cs=getComputedStyle(sh); const m=new DOMMatrix(cs.transform==='none'?undefined:cs.transform);
    __tr.push({ ty:m.m42, look:cs.backgroundColor+'|'+cs.backgroundImage }); if(__tr.length<600 && !window.__stop) requestAnimationFrame(L); };
  window.__stop=false; requestAnimationFrame(L); }"""

READ_SHEET = """()=>{ const sh=document.querySelector('#unitoptions-modal .unitoptions-modal-sheet'); const cs=getComputedStyle(sh);
  const m=new DOMMatrix(cs.transform==='none'?undefined:cs.transform);
  return { ty:m.m42, hidden:document.getElementById('unitoptions-modal').hidden, cls:sh.className, st:sh.scrollTop, inline:sh.style.transform,
           look:cs.backgroundColor+'|'+cs.backgroundImage }; }"""

X_READ = """()=>{ const sh=document.querySelector('#unitoptions-modal .unitoptions-modal-sheet'); const x=sh.querySelector('.unitoptions-modal-head .next');
  const r=x.getBoundingClientRect(); return { l:r.left, t:r.top, r:r.right, b:r.bottom, ink:getComputedStyle(x,'::before').backgroundColor,
   op:getComputedStyle(x,'::before').opacity, h:getComputedStyle(x,'::before').height }; }"""


def lum(c):
    def ch(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def section_a(br):
    print("\nA. the start sheet: down from anywhere, 1:1, the same colour, a close X you can see")
    for label, w, h, dpr, vr in (PHONE + (False,), TABLET + (False,), PHONE + (True,)):
        name = label + (" (Match settings)" if vr else " (Drill)")
        ctx, pg = boot(br, w, h, dpr)
        o = pg.evaluate(OPEN_SETUP, vr)
        if not o:
            check("%s: the start sheet opened" % name, False); ctx.close(); continue
        cdp = ctx.new_cdp_session(pg)
        rest_look = o["look"]
        # a patch of the sheet's own fill, near its top-left, clear of text
        px0 = int((o["left"] + 6) * dpr); py0 = int((o["top"] + 6) * dpr)
        rest = shot(pg)
        patch_rest = mean(rest, (px0, py0, px0 + 10 * dpr, py0 + 4 * dpr))
        # 1. a drag down from the middle of the sheet
        pg.evaluate(TRACE)
        # MOVED IN 327z8: "it goes away even if you barely swipe down" - a slow
        # pull now has to pass 40% of the sheet (the question swipe's rule), so
        # this pull goes 46% of its height; a short slow one is checked below.
        FD = int(o["h"] * 0.46)
        drag_to(cdp, o["x"], o["y"], 0, FD)
        time.sleep(0.12)
        held = pg.evaluate(READ_SHEET)
        mid = shot(pg)
        oy = int(round(held["ty"] * dpr))
        patch_mid = mean(mid, (px0, py0 + oy, px0 + 10 * dpr, py0 + oy + 4 * dpr))
        tend(cdp)
        time.sleep(0.9)
        pg.evaluate("()=>{window.__stop=true;}")
        tr = pg.evaluate("()=>__tr")
        after = pg.evaluate(READ_SHEET)
        looks = sorted(set(t["look"] for t in tr))
        check("%s: a drag down from the middle of the sheet (on %s) moves it with the finger - %.0fpx for a %dpx pull, within its slop"
              % (name, o["at"][:30], held["ty"], FD), FD - 18 <= held["ty"] <= FD + 1, held)
        check("%s: its fill never changes while it moves (one computed look in %d frames, the resting one)" % (name, len(tr)),
              looks == [rest_look], looks[:3])
        dpatch = max(abs(a - b) for a, b in zip(patch_rest, patch_mid))
        check("%s: and read off the pixels where the sheet is, its colour mid-drag is its colour at rest (off by %.1f)" % (name, dpatch),
              dpatch <= 3, [patch_rest, patch_mid])
        check("%s: let go past the line, it closes" % name, after["hidden"] is True, after)
        moving = [t["ty"] for t in tr]
        check("%s: it slides out on the way (it reaches past half its height before it is gone)" % name,
              max(moving or [0]) > o["h"] * 0.5, max(moving or [0]))
        # 2. a short pull springs back
        o = pg.evaluate(OPEN_SETUP, vr)
        drag_to(cdp, o["x"], o["y"], 0, 50, steps=6)
        time.sleep(0.08)
        tend(cdp)
        time.sleep(0.7)
        sp = pg.evaluate(READ_SHEET)
        check("%s: a short pull springs back - still open, back at rest, nothing left on it" % name,
              (not sp["hidden"]) and abs(sp["ty"]) < 0.5 and "is-dragging" not in sp["cls"] and not sp["inline"] and sp["look"] == rest_look, sp)
        # 3. sideways does nothing
        drag_to(cdp, o["x"] - 60, o["y"], 120, 14, steps=10)
        time.sleep(0.08)
        sw = pg.evaluate(READ_SHEET)
        tend(cdp); time.sleep(0.4)
        sw2 = pg.evaluate(READ_SHEET)
        check("%s: a sideways drag does not pull it" % name, abs(sw["ty"]) < 1 and not sw2["hidden"], [sw, sw2])
        # 4. scrolled down: a drag down scrolls
        if o["scrolls"]:
            pg.evaluate("()=>{ document.querySelector('#unitoptions-modal .unitoptions-modal-sheet').scrollTop = 120; }")
            time.sleep(0.2)
            drag_to(cdp, o["x"], o["y"], 0, 90, steps=10)
            time.sleep(0.08)
            sc = pg.evaluate(READ_SHEET)
            tend(cdp); time.sleep(0.5)
            sc2 = pg.evaluate(READ_SHEET)
            check("%s: scrolled down, a drag down scrolls the sheet's list and does not pull it" % name,
                  abs(sc["ty"]) < 1 and not sc2["hidden"], [sc, sc2])
            pg.evaluate("()=>{ document.querySelector('#unitoptions-modal .unitoptions-modal-sheet').scrollTop = 0; }")
            time.sleep(0.3)
        # 5. the close X
        xr = pg.evaluate(X_READ)
        img = shot(pg).crop((int(xr["l"] * dpr), int(xr["t"] * dpr), int(xr["r"] * dpr), int(xr["b"] * dpr)))
        cxs, cys = img.size
        # the circle's own colour: just inside its edge, off the X; the X: the brightest pixel at its centre
        circle = mean(img, (int(cxs * .22), int(cys * .45), int(cxs * .3), int(cys * .55)))
        centre = img.crop((int(cxs * .4), int(cys * .4), int(cxs * .6), int(cys * .6)))
        xs = max(centre.getdata(), key=lambda p: abs(lum(p) - lum(circle)))
        sheetc = mean(shot(pg), (px0, py0, px0 + 10 * dpr, py0 + 4 * dpr))
        cr = contrast(xs, circle)
        check("%s: the close X stands out from its circle at %.1f:1 (needs 4.5)" % (name, cr), cr >= 4.5, [xs, circle, xr])
        check("%s: and the circle is a visible glass circle on the sheet, not a white disc and not invisible (circle %s, sheet %s)"
              % (name, tuple(round(v) for v in circle), tuple(round(v) for v in sheetc)),
              lum(circle) < 0.25 and contrast(circle, sheetc) >= 1.25, [circle, sheetc])
        ctx.close()


OPEN_CHAT = """async () => { openChatDock(); enterChatRoom('GTEST1');
  for(let i = 0; i < 40 && !document.querySelector('.chatdock-panel .vroom-chat-input'); i++) await new Promise(r => setTimeout(r, 100));
  const list = document.querySelector('.chatdock-panel .vroom-chat-list');
  if(list && !list.querySelector('.z5-msg')){
    for(let i = 0; i < 40; i++){ const m = document.createElement('div'); m.className = 'vroom-chat-msg z5-msg';
      m.textContent = 'Message ' + (i + 1) + ': studying the Penal Code before Monday.'; list.appendChild(m); }
  }
  await new Promise(r => setTimeout(r, 900));
  const p = document.querySelector('.chatdock-panel').getBoundingClientRect();
  const l = list.getBoundingClientRect();
  const row = document.querySelector('.chatdock-panel .vroom-chat-row').getBoundingClientRect();
  const inp = document.querySelector('.chatdock-panel .vroom-chat-input').getBoundingClientRect();
  return { open: chatDockOpen, top: p.top, bottom: p.bottom, left: p.left, right: p.right,
           lx: Math.round((l.left + l.right) / 2), ly: Math.round(l.top + l.height * 0.45), lh: l.height,
           rx: Math.round(inp.right + 6 > row.right - 4 ? row.left + 8 : inp.right + 4), ry: Math.round((row.top + row.bottom) / 2),
           rowL: row.left, inpL: inp.left }; }"""

READ_CHAT = """() => { const p = document.querySelector('.chatdock-panel'); const cs = getComputedStyle(p);
  const m = new DOMMatrix(cs.transform === 'none' ? undefined : cs.transform);
  const l = document.querySelector('.chatdock-panel .vroom-chat-list');
  return { ty: m.m42, open: chatDockOpen, st: l ? l.scrollTop : -1, sy: scrollY, inline: p.style.transform }; }"""


def section_b(br):
    print("\nB. the chat sheet: down from anywhere, when the list is at its top")
    for label, w, h, dpr in (PHONE, TABLET):
        ctx, pg = boot(br, w, h, dpr)
        o = pg.evaluate(OPEN_CHAT)
        if not o["open"]:
            check("%s: the chat opened" % label, False, o); ctx.close(); continue
        cdp = ctx.new_cdp_session(pg)
        # 1. list at its top: a drag down in it pulls the sheet and closes it
        pg.evaluate("() => { document.querySelector('.chatdock-panel .vroom-chat-list').scrollTop = 0; }")
        time.sleep(0.3)
        PH = pg.evaluate("() => document.querySelector('.chatdock-panel').getBoundingClientRect().height")
        CD = max(180, int(PH * 0.46))  # MOVED IN 327z8: past 40% of the sheet, as the start sheet
        drag_to(cdp, o["lx"], max(40, o["ly"] - CD // 3), 0, CD)
        time.sleep(0.12)
        held = pg.evaluate(READ_CHAT)
        tend(cdp); time.sleep(0.8)
        aft = pg.evaluate(READ_CHAT)
        check("%s: with the message list at its top, a drag down in the middle of it pulls the sheet (%.0fpx for %d)" % (label, held["ty"], CD),
              held["ty"] > CD * 0.66, held)
        check("%s: and let go, it closes" % label, aft["open"] is False, aft)
        # 2. list scrolled down: the same drag scrolls the list
        o = pg.evaluate(OPEN_CHAT)
        pg.evaluate("() => { const l = document.querySelector('.chatdock-panel .vroom-chat-list'); l.scrollTop = l.scrollHeight; }")
        time.sleep(0.3)
        st0 = pg.evaluate(READ_CHAT)
        drag_to(cdp, o["lx"], o["ly"], 0, 160)
        time.sleep(0.12)
        held = pg.evaluate(READ_CHAT)
        tend(cdp); time.sleep(0.6)
        aft = pg.evaluate(READ_CHAT)
        check("%s: with the list scrolled down, the same drag scrolls the list (%d -> %d) and the sheet stays" % (label, st0["st"], aft["st"]),
              abs(held["ty"]) < 1 and aft["open"] and aft["st"] < st0["st"] - 40, [st0, held, aft])
        # 3. the composer row, off the field
        pg.evaluate("() => { const l = document.querySelector('.chatdock-panel .vroom-chat-list'); l.scrollTop = 0; }")
        time.sleep(0.3)
        sy0 = pg.evaluate("() => scrollY")
        drag_to(cdp, o["rx"], o["ry"], 0, 140)
        time.sleep(0.12)
        held = pg.evaluate(READ_CHAT)
        tend(cdp); time.sleep(0.8)
        aft = pg.evaluate(READ_CHAT)
        check("%s: a drag down from the composer row (off the field) pulls the sheet too (%.0fpx for 140)" % (label, held["ty"]),
              held["ty"] > 80, held)
        check("%s: and the page behind never moved" % label, aft["sy"] == sy0, [sy0, aft["sy"]])
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
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
