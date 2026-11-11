#!/usr/bin/env python3
"""Build 384.20: A BANNER TILE ARRIVES MOVING, FRAME BY FRAME - Customize > Banner, flung and jumped through.
Reported (iOS): "banners misbehave as you scroll - some stop animating / flicker". Build 384 r24 could not reproduce it at five scroll stops
(every tile at least half in view ran, nothing idle or paused). Frame by frame it is not the same question: a stop is looked at after the
page has settled, a person looks at every frame of the way there.

A Customize banner tile is held still (.is-offscreen, animation-play-state:paused) outside an observer's margin (a third of a screen) and
woken by that observer - an IntersectionObserver callback, a task of its own, after the frame that draws the new place. A fling's tiles are
woken a third of a screen ahead, so they arrive moving. A JUMP (back to top, the status bar's tap, the end of a long fling) lands tiles
in view with the callback still to come: measured at 440x956 in Chromium, 4-6 frames over six jumps at 1x, and at 4x CPU, where a frame is
150ms or more, a banner standing on its pose for a third of a second after a tap on "back to top". wakeTilesOnScroll() wakes them in the
scroll event, which runs in the frame that moves the page, before it is drawn.

Judged on the page, per animation frame (a requestAnimationFrame log of every tile's class and animations), by SHAPE:
 (1) A FLING (mouse wheel, down and back, 3000px/s): in no frame is a tile that is at least half in view, drawn, and moves at all,
     .is-offscreen (paused) or .rk-idle. Phone (440x956) and tablet (834x1194), the Fire Code class and the academy.
 (2) A JUMP (an instant scrollTo to the end, the middle, the top, a quarter, three quarters, the top): the same, in EVERY frame
     after the jump - including the first one the new place is drawn in.
 (3) THE BUDGET STANDS: after a stop, a tile more than half a screen away runs nothing (it is held), so waking early did not wake the page.
 (4) no page error.
INFO: how many banner animations are alive (running + paused) at each stop - on this page (22 tiles, ~2 screens long) every tile is
always inside the idle margin (a whole screen), so all of them are alive at every stop; that is the page's budget, not this build's.

  python3 tools/check-b384-bannerscroll.py [--against OLD/index.html] [--cpu 4]
Fails on 384.19: (2) on every config (tiles frozen in the first frame(s) after a jump). (1) and (3) hold on both.
"""
import json, os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
gsrc = open(os.path.join(HERE, "check-b384-fcbanner-motion.py")).read()
ns = {"json": json, "rc": rc}; exec(gsrc[gsrc.index("def seed_for"):gsrc.index("def share")], ns); seed_for = ns["seed_for"]
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
BODY = open(args[args.index("--against") + 1], encoding="utf-8").read() if "--against" in args else None
CPU = float(args[args.index("--cpu") + 1]) if "--cpu" in args else 1
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def info(s): print("INFO " + s, flush=True)

LOGGER = """() => { window.__log = []; window.__run = true; const vh = innerHeight, tiles = Array.from(document.querySelectorAll('.banner-opt'));
  const tick = () => { if(!window.__run) return; const row = [];
    tiles.forEach((b, i) => { const r = b.getBoundingClientRect(); if(r.bottom < -vh || r.top > 2 * vh) return;
      const vis = Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0)) / Math.max(1, r.height);
      const bn = b.querySelector('.bnr'); const an = bn ? bn.getAnimations({ subtree: true }) : [];
      let run = 0; an.forEach(x => { if(x.playState === 'running' || x.playState === 'pending') run++; });
      row.push([i, +vis.toFixed(2), bn ? 1 : 0, b.classList.contains('is-offscreen') ? 1 : 0, bn && bn.classList.contains('rk-idle') ? 1 : 0, run, an.length]); });
    window.__log.push([Math.round(performance.now()), Math.round(scrollY), row]); requestAnimationFrame(tick); };
  requestAnimationFrame(tick); }"""
STOP = """() => { const vh = innerHeight; let alive = 0, far = 0, farRunning = [], tiles = 0;
  document.querySelectorAll('.banner-opt').forEach((b, i) => { const r = b.getBoundingClientRect(), bn = b.querySelector('.bnr'); if(!bn) return; tiles++;
    const an = bn.getAnimations({ subtree: true }); alive += an.length;
    const dist = r.bottom < 0 ? -r.bottom : r.top > vh ? r.top - vh : 0;
    if(dist > vh * .5){ far++; const run = an.filter(x => x.playState === 'running').length; if(run) farRunning.push([i, run]); } });
  return { tiles, alive, far, farRunning }; }"""

def analyse(log, label, from_t=None):
    everran = set(i for (t, sy, row) in log for (i, vis, dr, off, idle, run, tot) in row if run and dr)
    bad = {}
    seen = set()
    for (t, sy, row) in log:
        if from_t is not None and t < from_t: continue
        for (i, vis, dr, off, idle, run, tot) in row:
            if vis >= .5 and dr and i in everran:
                seen.add(i)
                why = [n for n, c in (("is-offscreen", off), ("rk-idle", idle)) if c]
                if why: bad.setdefault((i, "+".join(why)), []).append((t, sy))
    return seen, bad

srv, PORT = rc["serve"]()
try:
  with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for cls in ("ifc", "academy"):
        for (W, H, dev) in ((440, 956, "phone"), (834, 1194, "tablet")):
            tag = "%s %s %dx%d%s" % (cls, dev, W, H, (" @%gx CPU" % CPU) if CPU != 1 else "")
            ctx = br.new_context(viewport={"width": W, "height": H})
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            if BODY is not None:
                pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
            pg.add_init_script(seed_for(cls))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.wait_for_timeout(2500)
            pg.evaluate("() => document.getElementById('splashscreen')?.remove()")
            if CPU != 1: ctx.new_cdp_session(pg).send("Emulation.setCPUThrottlingRate", {"rate": CPU})
            pg.evaluate("() => { window.bannerEarned = () => true; showCustomize('banner'); }"); pg.wait_for_timeout(3500 if CPU == 1 else 7000)
            maxy = pg.evaluate("() => document.scrollingElement.scrollHeight - innerHeight")
            chk("%s: the Customize banner page is taller than the screen (%d)" % (tag, maxy), maxy > 400, maxy)
            # ---- (1) a fling, down and back
            pg.evaluate(LOGGER)
            step = 48; dist = int(maxy * .95)
            pg.mouse.move(W // 2, H // 2)
            for d in (1, -1):
                done = 0
                while done < dist:
                    pg.mouse.wheel(0, d * step); done += step; pg.wait_for_timeout(16)
                pg.wait_for_timeout(700)
            pg.evaluate("() => { window.__run = false; }")
            log = pg.evaluate("() => window.__log")
            seen, bad = analyse(log, tag)
            chk("%s (1): through a fling of %d frames, %d moving tiles looked at, none was ever held still or idle while at least half in view" % (tag, len(log), len(seen)),
                len(seen) >= 8 and not bad, (len(seen), {k: len(v) for k, v in list(bad.items())[:6]}))
            # ---- (2) jumps
            pg.evaluate(LOGGER)
            marks = []
            for frac in (1.0, .5, 0, .25, .75, 0):
                marks.append(pg.evaluate("() => performance.now()"))
                pg.evaluate("(y) => document.scrollingElement.scrollTo({ top: y, behavior: 'instant' })", int(maxy * frac))
                pg.wait_for_timeout(900 if CPU == 1 else 2500)
            pg.evaluate("() => { window.__run = false; }")
            log = pg.evaluate("() => window.__log")
            seen, bad = analyse(log, tag, from_t=marks[0])
            nframes = sum(1 for (t, sy, row) in log if t >= marks[0])
            nbad = len(set(t for v in bad.values() for (t, sy) in v))
            chk("%s (2): across 6 jumps (%d frames), no moving tile at least half in view is held still or idle in any frame (%d frames had one)" % (tag, nframes, nbad),
                len(seen) >= 8 and not bad, (len(seen), {k: len(v) for k, v in list(bad.items())[:6]}))
            # ---- (3) the budget stands, and INFO
            alive_at = []
            far_bad = []
            for frac in (0, .5, 1.0):
                pg.evaluate("(y) => document.scrollingElement.scrollTo({ top: y, behavior: 'instant' })", int(maxy * frac)); pg.wait_for_timeout(1500 if CPU == 1 else 4000)
                s = pg.evaluate(STOP); alive_at.append(s["alive"])
                if s["farRunning"]: far_bad.append((frac, s["farRunning"][:4]))
            chk("%s (3): after a stop, a tile more than half a screen away runs nothing" % tag, not far_bad, far_bad)
            info("%s: banner animations alive at the top / middle / end: %s" % (tag, alive_at))
            chk("%s (4): no page error" % tag, not errs, errs[:2])
            ctx.close()
    br.close()
finally:
    srv.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
