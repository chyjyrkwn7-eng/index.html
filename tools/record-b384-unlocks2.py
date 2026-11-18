"""A short screen recording of browsing the Unlocks screen on a phone (iPhone 17 Pro Max, 440x956), academy, the rich fixture of
check-b384-unlocks.py: Customize, All unlocks, the ladders, the Characters / Banners / Effects filters, a card opened and closed.
Chromium's own recorder (Playwright video), converted to mp4 with ffmpeg. Touch scrolling is driven by script, so the motion is even.

  python3 tools/record-b384-unlocks2.py OUT.mp4 [--src index.html] [--cls academy|ifc]"""
import os, subprocess, sys, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
_argv = sys.argv[:]
sys.argv = [G]
h = {"__file__": G, "__name__": "rec"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = _argv
from playwright.sync_api import sync_playwright
import json, re

OUT = os.path.abspath(sys.argv[1])
def arg(n): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
SRC = arg("--src") or os.path.join(h["ROOT"], "index.html"); CLS = arg("--cls") or "academy"
text = open(SRC, encoding="utf-8").read()
seed, init = h["fixtures"]()["rich_" + CLS]
GLIDE = """async ([to, ms]) => { const y0 = scrollY, t0 = performance.now(); await new Promise(res => { const f = t => { const u = Math.min(1, (t - t0) / ms);
  const e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; window.scrollTo(0, y0 + (to - y0) * e); if(u < 1) requestAnimationFrame(f); else res(); }; requestAnimationFrame(f); }); }"""
vid = tempfile.mkdtemp(dir="/dev/shm")
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    # set up on a plain page first (the fixture, the board), then record on a fresh context with the same seed
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, device_scale_factor=2,
                         record_video_dir=vid, record_video_size={"width": 440, "height": 956})
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed))
    ctx.add_init_script(h["FAKE"]); ctx.add_init_script(h["g"]["STANDALONE"]); ctx.add_init_script(init)
    pg = ctx.new_page()
    body = h["make_patched"](text)((59, 0, 34, 0))
    build = re.search(r'const APP_BUILD = "([^"]+)"', text).group(1)
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": build, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda r, q, b=body: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(h["SERVE_URL"], timeout=180000); pg.wait_for_timeout(3800)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    h["quiet"](pg)
    pg.evaluate("()=>showCustomize()"); pg.wait_for_timeout(1800)
    pg.tap(".trk-all"); pg.wait_for_timeout(1800)
    pg.evaluate(GLIDE, [1400, 2600]); pg.wait_for_timeout(500)
    pg.evaluate(GLIDE, [3600, 2800]); pg.wait_for_timeout(600)
    pg.evaluate(GLIDE, [0, 1600]); pg.wait_for_timeout(500)
    for k, dy in (("char", 1500), ("banner", 1100), ("fx", 400)):
        pg.tap('.ulk-chip[data-filter="%s"]' % k); pg.wait_for_timeout(1600)
        pg.evaluate(GLIDE, [dy, 2200]); pg.wait_for_timeout(900)
        pg.evaluate(GLIDE, [0, 900]); pg.wait_for_timeout(400)
    pg.tap('.ulk-chip[data-filter="char"]'); pg.wait_for_timeout(1200)
    pg.evaluate(GLIDE, [700, 900]); pg.wait_for_timeout(500)
    pg.tap('.ulk-item.is-locked'); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{ const b = [...document.querySelectorAll('.invite-overlay button')].find(x => /close/i.test(x.textContent)); if(b) b.click(); }")
    pg.wait_for_timeout(1200)
    path = pg.video.path()
    ctx.close(); br.close()
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart", OUT], check=True)
shutil.rmtree(vid, ignore_errors=True)
print("wrote", OUT)
