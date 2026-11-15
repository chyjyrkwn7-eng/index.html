#!/usr/bin/env python3
"""Build 384.127 screenshots and a real-time recording for Madison: a chat with a picture, the picture enlarged, and tap-to-enlarge then close.
  python3 tools/shoot-b384-chatphoto.py OUT_DIR [--against OLD/index.html]     (the `--against` run is the 'before': files get a before- prefix)
Per device (iPhone 17 Pro Max 440x956 installed, iPad Pro 11" 834x1194), a friend's chat holding four pictures:
  <p>-chat.png (the chat), <p>-enlarged.png (after a real touch on the first picture), <p>-small.png (a 120x90 picture enlarged),
  <p>-tap.mp4 (screen recording in real time: tap, enlarged, tap to close)."""
import importlib.util, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cp", os.path.join(HERE, "check-b384-chatphoto.py"))
cp = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp)
from playwright.sync_api import sync_playwright
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
PRE = "before-" if cp.OLD is not None else ""
srv, url = cp.serve(); errs = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cp.CHROME, args=["--no-sandbox"])
    for dev in cp.DEVS:
        tag = "phone" if dev[5] == "phone" else "ipad"
        vdir = os.path.join(OUT, "vid-" + PRE + tag); shutil.rmtree(vdir, ignore_errors=True)
        ctx, pg, got = cp.boot(br, url, "academy", dev, errs, video=vdir)
        root, code = cp.open_surface(pg, "friend", cp.photo_msgs())
        pg.evaluate("(r)=>{ const l = document.querySelector(r + ' .vroom-chat-list'); l.scrollTop = 0; }", root)
        f = cp.nth_fig(pg, root, 0); pg.wait_for_timeout(500)
        pg.screenshot(path=os.path.join(OUT, "%s%s-chat.png" % (PRE, tag)))
        cp.tap(pg, f["x"], f["y"]); pg.wait_for_timeout(900)
        pg.screenshot(path=os.path.join(OUT, "%s%s-enlarged.png" % (PRE, tag)))
        v = pg.evaluate(cp.VIEW2)
        if v:
            cp.tap(pg, v["vw"] / 2, v["vh"] / 2); pg.wait_for_timeout(700)
        else:
            pg.evaluate("()=>document.querySelectorAll('.vroom-chat-picker').forEach(p=>p.remove())")
        # a small picture: on the old build, with a click the app's own handler gets (a real touch never reaches it there)
        f = cp.nth_fig(pg, root, 2); cp.close_all(pg)
        pg.evaluate("(r)=>[...document.querySelectorAll(r + ' .vroom-chat-photo')][2].click()", root); pg.wait_for_timeout(900)
        pg.screenshot(path=os.path.join(OUT, "%s%s-small.png" % (PRE, tag)))
        cp.close_all(pg)
        ctx.close()
        for fn in os.listdir(vdir):
            if fn.endswith(".webm"):
                dst = os.path.join(OUT, "%s%s-tap.mp4" % (PRE, tag))
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(vdir, fn), "-c:v", "libx264", "-pix_fmt", "yuv420p", dst])
        shutil.rmtree(vdir, ignore_errors=True)
    br.close()
srv.shutdown(); print("errors:", errs)
