#!/usr/bin/env python3
"""Find glows and backgrounds that stop in a hard straight line.

"The top of the screenshot doesn't blend - it's hard cutoff." A glow
clipped by a box shows up as a UNIFORM brightness step along that box's
edge: every column in the row jumps by the same amount, and nothing
steps back. A ring, a rule or a line of text is a +/- PAIR a pixel or
two apart. This screenshots every mountable screen on every device,
scans each row's mean brightness down the upper half of the screen, and
flags a step of >= STEP levels that is not undone within PAIR pixels.

  python3 tools/check-edges.py            # the whole matrix, portrait
  python3 tools/check-edges.py --only 17  # one device family
"""
import argparse, functools, http.server, io, os, re, socket, sys, threading
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
PAIR, RUN, PEAK = 4, 0.35, 4
VIEW_W = [1]
sw = io.open(os.path.join(ROOT, "tools/sweep-layout.py")).read()
SEED = re.search(r'SEED = """(.*?)"""', sw, re.S).group(1)
STANDALONE = re.search(r'STANDALONE = """(.*?)"""', sw, re.S).group(1)
DEVICES = eval("[" + re.search(r'DEVICES = \[(.*?)\n\]', sw, re.S).group(1) + "]")
# The two screens that carry the planet glow. Every other screen is
# made of cards whose edges are meant to be edges.
SCREENS = ["showHome", "showWelcome"]

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/index.html"

def edges(path, limit=None):
    """Calibrated on the real thing (build 199, 518px Home): the clipped
    glow is ONE row in which a contiguous run of about half the screen's
    width steps the same way at once, peaking at ~7 levels in the middle
    and fading to nothing at the sides, because the glow itself is
    radial. A ring's apex or a badge's top is a short run. So: flag a row
    whose longest same-sign run covers >= RUN of the width with a peak of
    >= PEAK levels, measured over 2px to ride out anti-aliasing, and not
    undone within PAIR px below it."""
    im = Image.open(path).convert("L"); W, H = im.size
    xs = list(range(int(W * .04), int(W * .96), max(1, W // 60)))
    out = []
    scale = W / VIEW_W[0]
    stop = int((limit if limit is not None else H / scale / 4) * scale)
    for y in range(3, min(stop, H - PAIR - 1)):
        d = [im.getpixel((x, y)) - im.getpixel((x, y - 2)) for x in xs]
        for sign in (1, -1):
            best = cur = 0; peak = 0; bpk = 0
            for v in d:
                if v * sign >= 1:
                    cur += 1; peak = max(peak, v * sign)
                    if cur > best: best, bpk = cur, peak
                else:
                    cur = 0; peak = 0
            if best < RUN * len(xs) or bpk < PEAK: continue
            d2 = [im.getpixel((x, min(H - 1, y + PAIR))) - im.getpixel((x, y)) for x in xs]
            if sum(v * sign for v in d2) < -0.5 * sum(v * sign for v in d if v * sign > 0): continue
            if not out or y - out[-1][0] > 3:
                out.append((y, bpk * sign))
    return out

def side_edges(path):
    """The same cutoff turned through ninety degrees: a column near either
    side of the screen in which a contiguous stretch (>= RUN of the upper
    part of the screen) steps the same way at once, and is not undone
    within PAIR px. A card's border is a +/- pair and is skipped."""
    im = Image.open(path).convert("L"); W, H = im.size
    ys = list(range(int(H * .06), int(H * .6), max(1, H // 90)))
    out = []
    band = max(8, int(W * .12))
    for x in list(range(3, band)) + list(range(W - band, W - PAIR - 1)):
        d = [im.getpixel((x, y)) - im.getpixel((x - 2, y)) for y in ys]
        for sign in (1, -1):
            # Peak required as well as length: a wide smooth gradient on a
            # laptop bands by ONE level for hundreds of pixels and is not
            # an edge; the real cutoff peaked at 7.
            best = cur = pk = bpk = 0
            for v in d:
                if v * sign >= 1:
                    cur += 1; pk = max(pk, v * sign)
                    if cur > best: best, bpk = cur, pk
                else:
                    cur = pk = 0
            if best < RUN * len(ys) or bpk < PEAK: continue
            d2 = [im.getpixel((min(W - 1, x + PAIR), y)) - im.getpixel((x, y)) for y in ys]
            if sum(v * sign for v in d2) < -0.5 * sum(v * sign for v in d if v * sign > 0): continue
            if not out or abs(x - out[-1][0]) > 3:
                out.append((x, sign))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only"); ap.add_argument("--against"); a = ap.parse_args()
    devs = [d for d in DEVICES if not a.only or a.only.lower() in d[0].lower()]
    url = serve(); src = io.open(a.against or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    fails = []; n = 0
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        for name, w, h, plat, ins, _ in devs:
            t, r, bt, l = ins
            html = INSET_RE.sub(lambda m: {"top": f"{t}px", "right": f"{r}px", "bottom": f"{bt}px", "left": f"{l}px"}[m.group(1)], src)
            ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=w < 900, has_touch=True)
            if plat != "desktop": ctx.add_init_script(STANDALONE)
            ctx.add_init_script(SEED)
            pg = ctx.new_page()
            pg.route("**/index.html", (lambda hh: (lambda route, request=None: route.fulfill(status=200, content_type="text/html", body=hh)))(html))
            # The build under test must agree with version.json, or an
            # --against run of an older build shows "Pushing update..."
            # instead of the screen and every scan passes on a blank page.
            bld = (re.search(r'const APP_BUILD = "([^"]+)"', src) or [None, ""])[1]
            pg.route("**/version.json*", lambda route, request=None: route.fulfill(status=200, content_type="application/json", body='{"build":"%s","frameId":"","force":true}' % bld))
            pg.goto(url); pg.wait_for_timeout(1300)
            pg.evaluate("()=>{const s=document.getElementById('splashscreen'); if(s) s.remove();}")
            for sc in SCREENS:
                call = sc if sc.endswith(")") else sc + "()"
                try:
                    pg.evaluate("()=>{ %s }" % call); pg.wait_for_timeout(450)
                    pg.evaluate("()=>document.querySelectorAll('.notice-bar,.update-banner,.daily-alert,.app-banner,#tour-overlay,#tour-tooltip').forEach(e=>e.remove())")
                    pg.wait_for_timeout(150)
                except Exception:
                    continue
                shown = pg.evaluate("()=>!!document.querySelector('.cosmic-hero-wrap')")
                if not shown:
                    fails.append(f"{name} {w}x{h}: {call} did not render a planet - nothing was scanned"); continue
                # Only the band ABOVE the planet: that is where the
                # background meets the status bar and where the clip
                # showed. Inside the hero the planet's own halo is a real,
                # deliberate ring of light and must not be flagged.
                limit = pg.evaluate("()=>document.querySelector('.cosmic-hero-wrap').getBoundingClientRect().top + 12")
                VIEW_W[0] = w
                f = "/tmp/_edge.png"; pg.screenshot(path=f); n += 1
                if os.environ.get("EDGE_KEEP"): pg.screenshot(path=os.environ["EDGE_KEEP"] + "/" + re.sub(r"[^A-Za-z0-9]+", "_", name + "_" + call) + ".png")
                for x, v in side_edges(f):
                    fails.append(f"{name} {w}x{h}: {call} hard SIDE edge at x={x}")
                for y, v in edges(f, limit):
                    fails.append(f"{name} {w}x{h}: {call} hard edge at y={y} ({v:+} levels)")
            ctx.close()
        b.close()
    print(f"{n} screen/device combinations scanned")
    if fails:
        print(f"\n{len(fails)} HARD EDGES"); [print("  *", x) for x in fails]; sys.exit(1)
    print("no hard edges anywhere")

if __name__ == "__main__": main()
