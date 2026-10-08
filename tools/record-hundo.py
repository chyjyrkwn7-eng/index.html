#!/usr/bin/env python3
"""MP4s of each hundo effect on a real 100% results screen, smooth.

  python3 tools/record-hundo.py OUTDIR [fx,fx,...] [W H]

Build 317: "all the others came through super laggy in the videos". The
lag was the RECORDER. Under virtual time (Emulation.setVirtualTimePolicy,
paused between steps) the compositor makes no frame between steps, so a
capture can return the previous one: a frozen frame and then a jump -
5 to 12 of them in every clip, measured. Here real time runs normally and
only the PAGE'S clock is replaced: performance.now, Date.now,
setTimeout/setInterval, requestAnimationFrame and smooth scrolls read a
clock this script advances exactly 1/30s per frame, and every CSS/Web
animation and transition is paused and seeked to it. Each capture waits
for two real frames first, so it is always a fresh one. Every clip is then
checked for frozen-between-moving frames and jumps, and the count printed.
Also writes box-<fx>-WxH.png, the settled grade box, box-<fx>-WxH-first.png
(the first frame the box is half shown) and box-<fx>-WxH-mid.png (MID[fx]
seconds into the effect), cropped out of the clip's own frames, and
f-<fx>-NN.jpg, one frame a second. Needs ffmpeg from imageio_ffmpeg."""
import importlib.util, sys, os, json
OUT = os.path.abspath(sys.argv[1])
FXS = (sys.argv[2] if len(sys.argv) > 2 else "confetti,fireworks,worldtree,bubbles,ufo").split(",")
W = int(sys.argv[3]) if len(sys.argv) > 3 else 440; H = int(sys.argv[4]) if len(sys.argv) > 4 else 956
sys.argv = [sys.argv[0]]
WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("cb", WT + "/tools/check-behaviour.py")
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
import subprocess, base64, io
from playwright.sync_api import sync_playwright
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs(OUT, exist_ok=True)
SRC = open(WT + "/tools/check-results.py").read()
i = SRC.index('SETUP = """') + len('SETUP = """'); SETUP = SRC[i:SRC.index('"""', i)]
FPS = 30
LEN = {"confetti": 6.0, "fireworks": 7.6, "worldtree": 6.2, "bubbles": 7.6, "ufo": 11.7, "blackhole": 6.4, "underwater": 8.0}
# a moment well into each, for the mid-effect crop (s after it starts)
MID = {"confetti": .8, "fireworks": 2.6, "worldtree": 1.2, "bubbles": 2.4, "ufo": 6.6, "blackhole": 2.0, "underwater": 2.6}
def smoothness(path, W2=220, H2=478):
    """(frozen frames between moving ones, sudden jumps) in an MP4."""
    from PIL import Image, ImageChops, ImageStat
    raw = subprocess.run([FF, "-loglevel", "error", "-i", path, "-vf", "scale=%d:%d" % (W2, H2), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    n = W2 * H2
    ims = [Image.frombytes("L", (W2, H2), raw[k * n:(k + 1) * n]) for k in range(len(raw) // n)]
    d = [ImageStat.Stat(ImageChops.difference(a, b)).mean[0] for a, b in zip(ims, ims[1:])]
    frozen = sum(1 for i in range(1, len(d) - 1) if d[i - 1] > .4 and d[i + 1] > .4 and d[i] < .1 * (d[i - 1] + d[i + 1]))
    jumps = sum(1 for i in range(1, len(d) - 1) if d[i] > 3 * max(.3, (d[i - 1] + d[i + 1]) / 2))
    return frozen, jumps


CLOCK = r"""() => {
  const C = window.__clk = { t: performance.now(), q: [], id: 9e6, raf: [], seen: new Map() };
  const nraf = window.__nraf = window.requestAnimationFrame.bind(window);
  const d0 = Date.now() - C.t;
  performance.now = () => C.t; Date.now = () => Math.round(d0 + C.t);
  window.setTimeout = (f, ms, ...a) => { const id = C.id++; if(typeof f === 'function') C.q.push({ id, at: C.t + Math.max(0, +ms || 0), f, a }); return id; };
  window.setInterval = (f, ms, ...a) => { const id = C.id++; const p = Math.max(1, +ms || 0); C.q.push({ id, at: C.t + p, f, a, every: p }); return id; };
  window.clearTimeout = window.clearInterval = id => { C.q = C.q.filter(x => x.id !== id); };
  window.requestAnimationFrame = f => { const id = C.id++; C.raf.push({ id, f }); return id; };
  window.cancelAnimationFrame = id => { C.raf = C.raf.filter(x => x.id !== id); };
  /* smooth scrolls run on this clock too, or they jump between frames */
  const nScrollTo = window.scrollTo.bind(window);
  window.scrollTo = function(a, b){
    if(a && typeof a === 'object' && a.behavior === 'smooth'){
      const y0 = scrollY, y1 = Math.max(0, Math.min(a.top != null ? a.top : y0, document.documentElement.scrollHeight - innerHeight)), t0 = C.t, D = 420;
      const step = () => { const u = Math.min(1, (C.t - t0) / D), e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
        nScrollTo({ top: y0 + (y1 - y0) * e, left: 0, behavior: 'instant' }); if(u < 1) window.requestAnimationFrame(step); };
      window.requestAnimationFrame(step); return;
    }
    return nScrollTo(a, b);
  };
  window.scrollBy = function(a){ if(a && typeof a === 'object') return window.scrollTo(Object.assign({}, a, { top: scrollY + (a.top || 0) })); return nScrollTo(scrollX + arguments[0], scrollY + arguments[1]); };
  const seek = () => {
    for(const an of document.getAnimations()){
      let base = C.seen.get(an);
      if(base === undefined){ base = C.t - (an.currentTime || 0); C.seen.set(an, base); try{ an.pause(); }catch(e){} }
      if(an.playState === 'finished') continue;
      let end = Infinity; try{ end = an.effect.getComputedTiming().endTime; }catch(e){}
      const t = (C.t - base) * (an.playbackRate || 1);
      if(isFinite(end) && t >= end){ try{ an.finish(); }catch(e){} continue; }
      try{ an.currentTime = t; }catch(e){}
    }
  };
  C.advance = async dt => {
    const end = C.t + dt;
    for(let guard = 0; guard < 2000; guard++){
      C.q.sort((x, y) => x.at - y.at);
      const n = C.q[0]; if(!n || n.at > end) break;
      C.t = Math.max(C.t, n.at);
      if(n.every) n.at += n.every; else C.q.shift();
      try{ n.f(...n.a); }catch(e){ console.error(e); }
      await null; seek();
    }
    C.t = end; seek();
    const r = C.raf; C.raf = [];
    r.forEach(x => { try{ x.f(C.t); }catch(e){ console.error(e); } });
    await null; seek();
    await new Promise(res => nraf(() => nraf(res)));
  };
  seek();
}"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME, args=["--force-device-scale-factor=2"])
    for fx in FXS:
        ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2)
        ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');"
                            "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % cb.USED_ACCOUNT)
        pg = cb.open_page(ctx); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.goto(cb.URL); pg.wait_for_timeout(2600)
        pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
        pg.evaluate(SETUP)
        pg.evaluate("""(fx) => { store.lifetime.perfectTests = 600; if(!HUNDO_FX.some(d => d.id === fx)) HUNDO_FX[1].id = fx; store.hundoFx = fx;
          const u = pendingHomeUnlocks ? pendingHomeUnlocks() : null; if(u) markUnlocksShown(u.chars, u.banners, u.fx); saveStore();
          try{ hfxWarm(fx); }catch(e){}
          window.__fxAt = 0; const real = playHundoFx; window.playHundoFx = function(a, b){ window.__fxAt = performance.now(); return real(a, b); };
          const rc = celebrate; window.celebrate = function(a, b){ window.__fxAt = performance.now(); return rc(a, b); }; }""", fx)
        pg.wait_for_timeout(1800)
        pg.evaluate(CLOCK)
        cdp = ctx.new_cdp_session(pg)
        pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
        k = 0
        while k < 30 * FPS and not pg.evaluate("() => !!document.querySelector('.rs-grade.rs-in, .rs-grade.rs-in-now')"):
            pg.evaluate("() => __clk.advance(1000 / 30)"); k += 1
        path = OUT + "/hundo-%s-%dx%d.mp4" % (fx, W, H)
        p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
            "-movflags", "+faststart", "-r", str(FPS), path], stdin=subprocess.PIPE)
        n = 0; t0 = None; ts = []; got_first = False
        while n < LEN[fx] * FPS:
            ts.append(pg.evaluate("async () => { await __clk.advance(1000 / 30); return performance.now(); }"))
            fr = base64.b64decode(cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 92})["data"])
            p.stdin.write(fr); n += 1
            if t0 is None and pg.evaluate("() => window.__fxAt > 0"): t0 = n
            # the grade box cropped out of this very frame: the first frame
            # it is half visible ("first"), and well into the effect ("mid")
            tag = None
            if not got_first and pg.evaluate("() => { const g = document.querySelector('.rs-grade'); return !!g && +getComputedStyle(g).opacity >= .5; }"):
                tag = "first"; got_first = True
            elif t0 is not None and n == t0 + int(MID.get(fx, 2) * FPS):
                tag = "mid"
            if tag:
                rr = pg.evaluate("() => { const b = document.querySelector('.rs-grade').getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; }")
                from PIL import Image
                im = Image.open(io.BytesIO(fr)); k = im.width / W
                im.crop(tuple(int(round(v * k)) for v in rr)).save(OUT + "/box-%s-%dx%d-%s.png" % (fx, W, H, tag))
            if n % 30 == 0: open(OUT + "/f-%s-%02d.jpg" % (fx, n // 30), "wb").write(fr)
        p.stdin.close(); p.wait()
        for _ in range(int(1.5 * FPS)): pg.evaluate("async () => { await __clk.advance(1000 / 30); }")
        pg.locator(".rs-grade").screenshot(path=OUT + "/box-%s-%dx%d.png" % (fx, W, H))
        gaps = [round(b - a, 2) for a, b in zip(ts, ts[1:])]
        sm = smoothness(path)
        print(fx, "frozen-between-moving", sm[0], "jumps", sm[1], ";", "reveal", round(k / FPS, 1), "s; fx at frame", t0, ";", n, "frames; clock steps", min(gaps), "-", max(gaps), "ms;", "ERR" if errs else "", errs[:3], flush=True)
        ctx.close()
    br.close()
cb.SERVER.shutdown()
