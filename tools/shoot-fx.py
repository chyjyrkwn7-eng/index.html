"""Stills of a Fire Code hundo effect at chosen moments, on the stand-in 100% card of check-b384-extspr's lab (every animation
paused and seeked, so a frame is exactly that time into the effect).

  python3 tools/shoot-fx.py OUTDIR FX T1,T2,... [W H] [--small] [--against FILE] [--sheet]

FX is the rung's id (fireworks = Extinguisher, underwater = Sprinklers, bubbles = Thermal Camera, ufo = Hazmat). One PNG a
time at 2x; --sheet also writes one contact sheet of them side by side. --small plays the box-alone version (a tile)."""
import os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:]]
SMALL = "--small" in args
SHEET = "--sheet" in args
for f in ("--small", "--sheet"):
    if f in args: args.remove(f)
if "--against" in args:
    i = args.index("--against"); AG = args[i + 1]; del args[i:i + 2]
    sys.argv = [sys.argv[0], "--against", AG]
else:
    sys.argv = [sys.argv[0]]
OUT, FX, TS = os.path.abspath(args[0]), args[1], [float(x) for x in args[2].split(",")]
W = int(args[3]) if len(args) > 3 else 440; H = int(args[4]) if len(args) > 4 else 956
src = open(os.path.join(HERE, "check-b384-extspr.py")).read().split("\nsrv, port = serve()")[0]
G = {"__file__": os.path.join(HERE, "check-b384-extspr.py"), "__name__": "shootfx"}
exec(src, G)
from PIL import Image
os.makedirs(OUT, exist_ok=True)
srv, port = G["serve"]()
with G["sync_playwright"]() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
    pg.add_init_script(G["INIT"])
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=G["BODY"]))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2800)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    pg.evaluate(G["LAB"])
    pg.evaluate("(id) => __G.warm(id)", FX)
    for _ in range(60):
        if pg.evaluate("(id) => __G.warmed(id)", FX): break
        pg.wait_for_timeout(150)
    pg.evaluate("([W, H]) => __G.setup(W, H)", [W, H])
    info = pg.evaluate("([id, s]) => __G.play(id, s)", [FX, SMALL])
    pg.wait_for_timeout(80)
    # the layer over the box (Hazmat's, hfx-ufo-top) is its own element: lift it into the lab and pause/seek it with the rest
    pg.evaluate("""() => { const G = __G, tops = [...document.querySelectorAll('.hfx-ufo-top')];
      tops.forEach(t => { t.style.visibility = 'visible'; t.style.zIndex = 2147480003; G.lab.appendChild(t); });
      const extra = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && tops.some(x => x.contains(t)); });
      extra.forEach(a => { try{ a.pause(); a.currentTime = 0; }catch(e){} }); G.anims = G.anims.concat(extra); }""")
    print(info.get("total"), info.get("screen"), info.get("box"), flush=True)
    ims = []
    for t in TS:
        pg.evaluate("(t) => __G.seek(t)", t)
        pg.wait_for_timeout(120)
        b = pg.screenshot()
        p = os.path.join(OUT, "%s-%s-%sx%s-%05.2f.png" % (("small-" if SMALL else "") + FX, "t", W, H, t))
        open(p, "wb").write(b); ims.append(Image.open(io.BytesIO(b)).convert("RGB"))
    if SHEET and ims:
        k = min(len(ims), 6); sc = .5
        row = [im.resize((int(im.width * sc), int(im.height * sc))) for im in ims]
        for r0 in range(0, len(row), k):
            seg = row[r0:r0 + k]; sh = Image.new("RGB", (sum(i.width for i in seg), seg[0].height))
            x = 0
            for i in seg: sh.paste(i, (x, 0)); x += i.width
            sh.save(os.path.join(OUT, "sheet-%s-%s-%d.jpg" % (FX, "small" if SMALL else "full", r0 // k)), quality=88)
    print("errors:", errs)
    br.close()
