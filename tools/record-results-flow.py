#!/usr/bin/env python3
"""An MP4 of a WHOLE results screen, from the moment it mounts to its settled end (the buttons in, .rs-done), on the
recorder's own clock (record-hundo's: every animation seeked, a fresh frame per step, so the clip is smooth by
construction). Build 384 round 6: the grade centred on its own, the 100%'s effect on it, the move up, then the XP box,
the unlocks and the rest - a still cannot show a choreography.

  python3 tools/record-results-flow.py OUT.mp4 [--ifc] [--fx ID] [--miss N] [--mode drill|exam] [--size W H]
                                       [--tap SECONDS] [--max SECONDS] [--against FILE]

--fx      the hundo effect worn (confetti default); a 100% run unless --miss
--tap S   a tap on the page S seconds in (to film a skip)
Writes OUT.mp4 and prints when each card landed (clip seconds)."""
import importlib.util, os, sys, subprocess, base64
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
def opt(name, default=None, n=1):
    if name in a:
        i = a.index(name); v = a[i + 1:i + 1 + n]; del a[i:i + 1 + n]; return v if n > 1 else v[0]
    return default
IFC = "--ifc" in a
if IFC: a.remove("--ifc")
FX = opt("--fx", "confetti"); MISS = int(opt("--miss", "0")); MODE = opt("--mode", "drill")
SIZE = opt("--size", None, 2); W, H = (int(SIZE[0]), int(SIZE[1])) if SIZE else (440, 956)
TAP = opt("--tap", None); TAP = float(TAP) if TAP else None
MAXS = float(opt("--max", "40")); AG = opt("--against", None)
OUT = os.path.abspath(a[0])
sys.argv = [sys.argv[0]] + (["--against", os.path.abspath(AG)] if AG else [])
spec = importlib.util.spec_from_file_location("rr", HERE + "/lib_realrun.py")
rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)
import imageio_ffmpeg
from playwright.sync_api import sync_playwright
FF = imageio_ffmpeg.get_ffmpeg_exe(); FPS = 30
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rr.cb.CHROME)
    ctx, pg, errs = rr.open_run(br, "ifc" if IFC else "academy", W, H, FX, missN=MISS, mode=MODE, run=False)
    cdp = ctx.new_cdp_session(pg)
    pg.evaluate("""() => { window.__landAt = {}; const t0 = performance.now();
      new MutationObserver(ms => ms.forEach(m => { const el = m.target; if(!el.classList || el.__la) return;
        if(!(el.classList.contains('rs-in') || el.classList.contains('rs-in-now'))) return; el.__la = 1;
        const k = ['rs-grade','rs-head','rs-xp','rs-xptotal','rs-unlocked','rs-actions'].find(c => el.classList.contains(c)); if(k) __landAt[k] = (performance.now() - t0) / 1000; }))
        .observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] }); }""")
    u = pg.evaluate("() => topicsIn(QUESTIONS)[0]") if IFC else "Identity Crimes"
    pg.evaluate("([u, m, mode]) => __run(u, m, mode, false)", [u, MISS, MODE])
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-preset", "medium",
        "-movflags", "+faststart", "-r", str(FPS), OUT], stdin=subprocess.PIPE)
    n = 0; done_at = None; tapped = False
    while n < MAXS * FPS:
        pg.evaluate("async () => { await __clk.advance(1000 / 30); }")
        if TAP is not None and not tapped and n >= TAP * FPS:
            pg.mouse.click(W / 2, H - 40); tapped = True
        p.stdin.write(base64.b64decode(cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 85})["data"])); n += 1
        if done_at is None and pg.evaluate("() => !!document.querySelector('.rs-rewards.rs-done')"): done_at = n
        if done_at is not None and n > done_at + 1.2 * FPS: break
    p.stdin.close(); p.wait()
    print(os.path.basename(OUT), "%.1fs" % (n / FPS), "landed:", {k: round(v, 2) for k, v in pg.evaluate("() => __landAt").items()}, "ERR" if errs else "", errs[:3])
    ctx.close(); br.close()
rr.cb.SERVER.shutdown()
