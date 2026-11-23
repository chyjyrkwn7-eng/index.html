#!/usr/bin/env python3
"""384 festive: MP4s and stills of Home in each season, for Madison (both classes, iPhone 17 Pro Max at 3x; an iPad still a season).

  python3 tools/record-b384-festive.py OUTDIR [SCENE,...] [--class academy|ifc|both] [--stills-only] [--no-stills] [--closeups]

SCENES: thanksgiving, thanksgiving-day, christmas, nye (the last seconds of Dec 31 and midnight), newyear (Jan 1).
The season is forced with the preview key the app reads (localStorage "class26e.season", see festMount) - the device's clock is moved
to that moment and runs on from it. Frames are made on a virtual clock (the clock of tools/record-hundo.py: Date, performance.now,
timers and every CSS / Web animation advance exactly 1/30s a frame), so the video is smooth whatever the machine's load, and a tap on
the planet (a real click on the sphere) lands at a fixed moment of the clip.
Out: <scene>-<class>.mp4 (H.264, yuv420p, faststart, 1320x2868), <scene>-<class>.jpg (iPhone, ~2100px wide, quality 87),
<scene>-ipad.jpg (iPad Pro 11", academy). --closeups (alone): hat-thanksgiving|christmas|newyear.jpg (each hat on the planet at 3x,
every loop held) and sleigh-closeup.jpg (Santa's sleigh mid-flight at 3x). Each clip also leaves one frame a second in OUTDIR/frames/ for checking by eye."""
import base64, io, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "festrec"}
sys_argv = sys.argv[:]; sys.argv = [sys.argv[0]]
exec(src, G)
sys.argv = sys_argv
g = G["g"]
from playwright.sync_api import sync_playwright
from PIL import Image
args = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = os.path.abspath(args[0]); os.makedirs(OUT + "/frames", exist_ok=True)
SCENES = args[1].split(",") if len(args) > 1 else ["thanksgiving", "thanksgiving-day", "christmas", "nye", "newyear"]
CLS = "both"
if "--class" in sys.argv: CLS = sys.argv[sys.argv.index("--class") + 1]
CLASSES = ["academy", "ifc"] if CLS == "both" else [CLS]
STILLS = "--no-stills" not in sys.argv
VIDEO = "--stills-only" not in sys.argv
FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"
FPS = 30
CLOCK = open(os.path.join(HERE, "record-hundo.py")).read().split('CLOCK = r"""', 1)[1].split('"""', 1)[0]
# the fixture's account has never seen Version 11's card (intro.seen 99 above) and is owed challenge cards (.rs-spot): neither is the season
UNCOVER = "document.querySelectorAll('.rs-spot,.rs-fly,.unlock-card,.intro-popup,#intro-pop,.app-banner,.daily-alert,.nova-talk').forEach(e=>e.remove());"
CLEAN = ("try{ homeUnlocksOwed = () => false; }catch(e){} try{ maybeShowIntro = () => {}; }catch(e){} "
         "document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner,.unlock-card,.rs-spot,.rs-fly,.homecaption').forEach(e=>e.remove());")
# scene: the forced moment, seconds of clip, seconds into the clip to tap the planet (None: no tap), the still's moment
SCENE = {
    "thanksgiving":     ("thanksgiving",        9.0, 4.2, 3.0),
    "thanksgiving-day": ("thanksgiving-day",    8.0, 3.4, 2.4),
    "christmas":        ("christmas",          11.0, 2.2, 6.0),
    "nye":              ("2026-12-31T23:59:47", 15.0, None, 2.5),
    "newyear":          ("newyear",            10.0, 6.4, 2.2),
}
def open_page(br, cls, forced, w, h, dpr, ins):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=False)
    ctx.add_init_script("window.__cloudSeed = {};")
    ctx.add_init_script(G["FAKE"])
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"] if cls == "ifc" else G["academy"], active=cls))
    ctx.add_init_script("try{ localStorage.setItem('class26e.intro.seen', '99'); localStorage.setItem('class26e.season', %s); localStorage.setItem('class26e.weekrecap.v1','9999-12-31'); localStorage.setItem('class26e.ifc.weekrecap.v1','9999-12-31'); }catch(e){}" % json.dumps(forced))
    if ins[0]: ctx.add_init_script(g["STATUS_BAR"].replace("__H__", str(ins[0])))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3800)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); %s }" % CLEAN)
    return ctx, pg, errs
def planet_xy(pg):
    return pg.evaluate("""()=>{ const h=document.querySelector('#stage .cosmic-hero-wrap'); const r=h.getBoundingClientRect();
      return [r.left + r.width/2 + r.width*.06, r.top + r.height*.47368 + r.width*.07]; }""")
def save_jpeg(png, path, width=None):
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if width and im.width != width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "JPEG", quality=87, optimize=True, progressive=True)
def still(br, scene, cls, ipad=False):
    forced, _, _, at = SCENE[scene]
    if ipad: w, h, dpr, ins = 834, 1194, 2.52, (24, 0, 20, 0)
    else: w, h, dpr, ins = 440, 956, 4.8, (62, 0, 34, 0)
    ctx, pg, errs = open_page(br, cls, forced, w, h, dpr, ins)
    pg.evaluate("()=>{ festYearShown = ''; %s showHome(); }" % CLEAN)
    pg.wait_for_timeout(int(at * 1000))
    if scene == "nye": pg.wait_for_timeout(4100)   # the last seconds over the planet, before midnight
    pg.evaluate("()=>{ " + UNCOVER + " }")
    png = pg.screenshot(scale="device")
    name = "%s-%s.jpg" % (scene, "ipad" if ipad else cls)
    save_jpeg(png, os.path.join(OUT, name), 2100 if not ipad else None)
    print("still", name, "errors:", errs[:2], flush=True)
    ctx.close()
def video(br, scene, cls):
    forced, secs, tap, _ = SCENE[scene]
    ctx, pg, errs = open_page(br, cls, forced, 440, 956, 3, (62, 0, 34, 0))
    pg.wait_for_timeout(600)
    pg.evaluate("(" + CLOCK + ")()")
    # a fixed random, so a clip is the same every time it is made
    pg.evaluate("""()=>{ let a = 20261126; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }""")
    if scene == "nye":
        # the clock is moved again so the clip starts 12 seconds before midnight, whatever the load before it
        pg.evaluate("()=>{ localStorage.setItem('class26e.season', 'x'); festPin = null; localStorage.setItem('class26e.season', '2026-12-31T23:59:48'); }")
    pg.evaluate("()=>{ festYearShown = ''; %s showHome(); }" % CLEAN)
    for _ in range(int(FPS * .8)): pg.evaluate("async () => { await __clk.advance(1000 / 30); }")
    cdp = ctx.new_cdp_session(pg)
    path = os.path.join(OUT, "%s-%s.mp4" % (scene, cls))
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium",
        "-movflags", "+faststart", "-r", str(FPS), path], stdin=subprocess.PIPE)
    n = 0; total = int(secs * FPS); tapped = False
    while n < total:
        if tap is not None and not tapped and n >= tap * FPS:
            pg.evaluate("()=>{ " + UNCOVER + " }"); x, y = planet_xy(pg); pg.mouse.click(x, y); tapped = True
        pg.evaluate("async () => { await __clk.advance(1000 / 30); " + UNCOVER + " }")
        fr = base64.b64decode(cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 90})["data"])
        p.stdin.write(fr); n += 1
        if n % 15 == 0: open(os.path.join(OUT, "frames", "%s-%s-%03d.jpg" % (scene, cls, n // 15)), "wb").write(fr)
    p.stdin.close(); p.wait()
    print("video", os.path.basename(path), "%.1f MB" % (os.path.getsize(path) / 1e6), "errors:", errs[:2], flush=True)
    ctx.close()
def closeups(br):
    ctx, pg, errs = open_page(br, "academy", "thanksgiving", 440, 956, 3, (62, 0, 34, 0))
    for name, forced in (("thanksgiving", "thanksgiving"), ("christmas", "christmas"), ("newyear", "2026-12-31T20:00")):
        pg.evaluate("(f)=>{ localStorage.setItem('class26e.season', f); festYearShown = 'x'; %s showHome(); }" % CLEAN, forced)
        pg.wait_for_timeout(2200)
        pg.evaluate("()=>{ " + UNCOVER + " document.getAnimations().forEach(a=>{ try{ a.pause(); }catch(e){} }); }")
        # one glass orb passing in front of the hat's right shoulder (the nearest rank bubble, moved there; its own animation held)
        pg.evaluate("""()=>{ const h=document.querySelector('#stage .cosmic-hero-wrap'); const hat=h.querySelector('.fest-planet .fest-hat g > path:not(.fest-hat-shadow)');
          const hr=hat.getBoundingClientRect(); const tx=hr.right-hr.width*.26, ty=hr.top+hr.height*.42;
          let best=null, bd=1e9; h.querySelectorAll(':scope > .cosmic-icon-badge').forEach(b=>{ const r=b.getBoundingClientRect(); const d=Math.hypot(r.left+r.width/2-tx, r.top+r.height/2-ty); if(d<bd){ bd=d; best=b; } });
          if(best){ const r=best.getBoundingClientRect(); best.style.translate=(tx-(r.left+r.width/2))+'px '+(ty-(r.top+r.height/2))+'px'; } }""")
        pg.wait_for_timeout(150)
        clip = pg.evaluate("""()=>{ const h=document.querySelector('#stage .cosmic-hero-wrap').getBoundingClientRect(); const cx=h.left+h.width/2, cy=h.top+h.height*.47368, w=h.width*.5;
          return {x:cx-w/2, y:cy-w*.86, width:w, height:w*1.02}; }""")
        save_jpeg(pg.screenshot(clip=clip, scale="device"), os.path.join(OUT, "hat-%s.jpg" % name))
        print("close-up hat-%s.jpg" % name, errs[:2], flush=True)
    pg.evaluate("()=>{ localStorage.setItem('class26e.season', 'christmas'); %s showHome(); }" % CLEAN); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{ festSleighBusy = 0; festSleigh(); }"); pg.wait_for_timeout(100)
    pg.evaluate("""()=>{ const sl=document.querySelector('.fest-sleigh'); sl.getAnimations({subtree:true}).forEach(a=>{ try{ a.pause(); a.currentTime = a.effect.target === sl ? a.effect.getComputedTiming().endTime * .5 : 300; }catch(e){} }); }""")
    pg.wait_for_timeout(200)
    r = pg.evaluate("()=>{ const b=document.querySelector('.fest-sleigh').getBoundingClientRect(); return [b.left, b.top, b.width, b.height]; }")
    clip = {"x": max(0, r[0] - 16), "y": max(0, r[1] - 24), "width": min(440 - max(0, r[0] - 16), r[2] + 32), "height": r[3] + 48}
    save_jpeg(pg.screenshot(clip=clip, scale="device"), os.path.join(OUT, "sleigh-closeup.jpg"))
    print("close-up sleigh-closeup.jpg", errs[:2], flush=True)
    ctx.close()

with sync_playwright() as pw:
    # the video's frames are the screen's own pixels at 3x (CDP's screenshot is at the forced scale)
    brv = pw.chromium.launch(executable_path=g["CHROME"], args=["--force-device-scale-factor=3"])
    br = pw.chromium.launch(executable_path=g["CHROME"])
    if "--closeups" in sys.argv:
        closeups(br); br.close(); brv.close(); sys.exit(0)
    for scene in SCENES:
        for cls in CLASSES:
            if VIDEO: video(brv, scene, cls)
            if STILLS: still(br, scene, cls)
        if STILLS and "academy" in CLASSES: still(br, scene, "academy", ipad=True)
    br.close(); brv.close()
