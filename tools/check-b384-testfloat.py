#!/usr/bin/env python3
"""384.153 (testfloat): ON A QUESTION ONLY CHAT AND PAUSE FLOAT - NO BAR THE QUESTION DISAPPEARS INTO.

Madison (a Drill question scrolled up on his iPhone, 384.152): "What's up with the bar thing in tests? I thought you fixed this?"
384.152 painted the pinned header's backing as the sky, but the row (Drill, the count, Pause) stayed pinned with that backing behind
it, so the question vanished into a strip under it. Asked, he chose "Only chat + Pause float": the two buttons stay where they rest,
as glass over the page; the row scrolls away with the question; nothing is painted behind anything.

Per device (installed Pro Max, the Pro Max at 85%, an SE, an installed iPad, a Pro Max Safari tab) and class (academy, Fire Code), on a
drill question with the page made long enough to scroll, scrolled so the question's first line sits level with where the row rested:
 (1) ROW     the mode label and the count moved up with the page by the scroll (+-1.5px);
 (2) FLOAT   Pause and the chat button did not move (+-1px) and are still on screen;
 (3) SEEN    in the band where the row rested (its top to 1.5rem under its foot), away from Pause and the chat button, the question is
             SEEN: the screenshot there differs from the same screen with the question hidden (>= 150 pixels by > 30 levels). With a
             backing over that band, hiding the question changes nothing there;
 (4) no page errors.
Run:  TMPDIR=/dev/shm python3 tools/check-b384-testfloat.py [--against REV]      --against 384.152 must FAIL (1) and (3).
"""
import importlib.util, io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

DEVICES = ["promax", "pm85", "se", "ipad", "promax-tab"]
results = []
def chk(ok, msg):
    results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + msg, flush=True)

GEO = """()=>{ const R = e => { if(!e || !e.getClientRects().length) return null; const q = e.getBoundingClientRect(); return [q.left, q.top, q.right, q.bottom]; };
  const top = document.querySelector('.wrap > .top'), lab = document.getElementById('testmodelabel'), cnt = document.getElementById('testqcounter');
  const q = document.querySelector('#stage .qpanel .qtext');
  return { top: R(top), lab: R(lab) || R(cnt), pause: R(document.querySelector('#pausebtn:not([hidden])')), chat: R(document.getElementById('chatdock-btn')),
           q: R(q), sy: window.scrollY, pinned: !!document.querySelector('.wrap.test-pinned') }; }"""
LONG = """()=>{ if(!document.getElementById('__long')){ const d = document.createElement('div'); d.id = '__long'; d.style.height = '1400px';
  const p = document.querySelector('#stage .qpanel') || document.getElementById('stage'); p.appendChild(d); } }"""
HIDEQ = """(on)=>{ let s = document.getElementById('__hq'); if(!s){ s = document.createElement('style'); s.id = '__hq'; document.body.appendChild(s); }
  s.textContent = on ? '#stage{visibility:hidden !important}' : ''; }"""
QUIET = """()=>{ let s = document.getElementById('__q'); if(!s){ s = document.createElement('style'); s.id = '__q'; document.body.appendChild(s); }
  s.textContent = '*,*::before,*::after{animation-play-state:paused !important; transition:none !important; caret-color:transparent !important}'; }"""

def shot(pg):
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for dev in DEVICES:
        for cls in ("academy", "ifc"):
            pg = G.open_dev(br, dev, inits=[G.seed_init(cls), "try{localStorage.setItem('class26e.intro.seen','99');}catch(e){}"], dsf=1)
            pg.evaluate("()=>{ try{ theme.muteBanners = true; }catch(e){} }")
            G.clear_popups(pg)
            pg.evaluate(G.START_DRILL)
            # the test's start card is up for ~2.5s first: wait for the question itself
            for _ in range(40):
                pg.wait_for_timeout(250)
                if pg.evaluate("()=>!!document.querySelector('#stage .qpanel .qtext') && !document.getElementById('teststart-overlay')"): break
            pg.wait_for_timeout(500); G.clear_popups(pg)
            pg.evaluate("()=>document.querySelectorAll('.app-banner,.daily-alert,.toast').forEach(n=>n.remove())")
            pg.evaluate(LONG); pg.evaluate(QUIET); pg.evaluate("()=>{ document.documentElement.style.scrollBehavior='auto'; window.scrollTo(0,0); }"); pg.wait_for_timeout(400)
            a = pg.evaluate(GEO)
            name = "%s %s" % (dev, cls)
            if not (a["pinned"] and a["top"] and a["lab"] and a["pause"] and a["q"]):
                chk(False, "%s: a drill question is up (%s)" % (name, {k: bool(v) for k, v in a.items()})); pg.ctx.close(); continue
            foot = a["top"][3]
            s = max(60, int(a["q"][1] - a["top"][1] + 4))   # the question's first line level with the row's top
            pg.evaluate("(y)=>window.scrollTo(0, y)", s); pg.wait_for_timeout(500)
            b = pg.evaluate(GEO)
            moved = b["sy"] - a["sy"]
            dl = b["lab"][1] - a["lab"][1]
            chk(abs(dl + moved) <= 1.5, "%s (1) ROW: scrolled %d, the mode label moved %.1f" % (name, moved, dl))
            dp = max(abs(b["pause"][i] - a["pause"][i]) for i in range(4)) if b["pause"] else 99
            dc = max(abs(b["chat"][i] - a["chat"][i]) for i in range(4)) if (b["chat"] and a["chat"]) else 0
            chk(dp <= 1 and dc <= 1 and b["pause"][1] >= 0, "%s (2) FLOAT: Pause moved %.1f, chat %.1f" % (name, dp, dc))
            img = shot(pg); pg.evaluate(HIDEQ, True); pg.wait_for_timeout(150); bare = shot(pg); pg.evaluate(HIDEQ, False)
            W = img.width; y0 = max(0, int(a["top"][1])); y1 = int(foot + 24)
            def out(x, y):
                for r in (a["pause"], a["chat"]):
                    if r and r[0] - 8 <= x <= r[2] + 8 and r[1] - 8 <= y <= r[3] + 8: return True
                return False
            n = 0
            for y in range(y0, min(y1, img.height)):
                for x in range(0, W, 2):
                    if out(x, y): continue
                    p, q = img.getpixel((x, y)), bare.getpixel((x, y))
                    if max(abs(p[i] - q[i]) for i in range(3)) > 30: n += 1
            chk(n >= 150, "%s (3) SEEN: in the row's band (y %d-%d) the question shows in %d pixels (>= 150)" % (name, y0, y1, n))
            chk(not pg.errs, "%s (4) no page errors %s" % (name, pg.errs[:2]))
            pg.ctx.close()
    br.close()
bad = results.count(False)
print("\n%d checks, %d failed" % (len(results), bad))
print("ALL PASS" if not bad else "FAILED")
sys.exit(1 if bad else 0)
