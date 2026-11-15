"""384.126 prestige: the ceremony as a video, in real time (Playwright's own recorder, then H.264 with ffmpeg when it is there).

  python3 tools/record-b384-prestige.py OUTDIR [--n 1|3] [--dev pm|ipad]

Fire Code, a real-shaped account that can take Prestige n (I: Supernova + one gold rim; III: everything, II already taken): the
Prestige screen, the Take button, the confirm sheet, Take, the ceremony and its reward cards, Done, and Profile with the emblem
beside the name - about 15 seconds. Chromium's frame timing is not an iPhone's; the sound is not in the file."""
import os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_prestige_lib as L
from playwright.sync_api import sync_playwright

ARGS = sys.argv[1:]
OUT = ARGS[0] if ARGS and not ARGS[0].startswith("--") else "/dev/shm/pg-video"
def arg(n, d=None): return ARGS[ARGS.index(n) + 1] if n in ARGS else d
N = int(arg("--n", "1")); DEV = arg("--dev", "pm")
W, H = (440, 956) if DEV == "pm" else (834, 1194)
os.makedirs(OUT, exist_ok=True)
text = open(os.path.join(L.ROOT, "index.html"), encoding="utf-8").read()
tmp = os.path.join(OUT, "raw-%d-%s" % (N, DEV)); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=L.CHROME, args=["--no-sandbox"])
    fc = L.account(ifc=True)
    seed, init = L.ifc_seed(fc)
    # set the account up off camera, then record a fresh page of it
    ctx, pg, errs = L.page(br, text, seed, init, w=W, h=H)
    L.quiet(pg)
    L.build(pg, "one" if N == 1 else "all")
    if N == 3: pg.evaluate("()=>{ takePrestige(1); takePrestige(2); }")
    L.quiet(pg)   # what the fixture holds is marked as told, so no unlock card plays over the recording
    pg.evaluate("()=>{ store.avatarChar = 'ghost'; saveStore(); }")
    pg.wait_for_timeout(800)
    st = pg.evaluate("()=>localStorage.getItem('class26e.ifc.drill.v1')")
    ctx.close()
    init2 = init.replace("localStorage.setItem('class26e.ifc.drill.v1',", "localStorage.setItem('class26e.ifc.drill.v1', %s); void(" % __import__("json").dumps(st), 1)
    seed2 = dict(seed); seed2["progress"] = dict(seed["progress"]); seed2["progress"][L.CODE + "__ifc"] = __import__("json").loads(st)
    import time as _t
    t0 = _t.time()
    ctx, pg, errs = L.page(br, text, seed2, init2, w=W, h=H, video_dir=tmp)
    L.quiet(pg)
    t_show = _t.time() - t0   # the boot is cut off the video: it starts half a second before the Prestige screen
    pg.evaluate("()=>showPrestige()")
    pg.wait_for_timeout(900)
    pg.evaluate("()=>{ const b = document.querySelector('.pg-card.is-ready .pg-take'); if(b){ b.scrollIntoView({ block: 'center' }); } }")
    pg.wait_for_timeout(1300)
    pg.click(".pg-card.is-ready .pg-take")
    pg.wait_for_timeout(1900)
    pg.click(".pg-confirm-go")
    pg.wait_for_timeout(6400)
    pg.click(".pg-scene-done")
    pg.wait_for_timeout(2600)
    print("taken", pg.evaluate("()=>store.prestige"), "errors", errs, flush=True)
    vid = pg.video.path()
    ctx.close(); br.close()
out = os.path.join(OUT, "prestige-%s-%s.mp4" % (["", "I", "II", "III"][N], DEV))
ff = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
if os.path.exists(ff):
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", "%.2f" % max(0, t_show - .5), "-i", vid, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-r", "30", out], check=True)
    print("video", out)
else:
    print("video (webm)", vid)
