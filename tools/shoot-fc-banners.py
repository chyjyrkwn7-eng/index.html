#!/usr/bin/env python3
"""The Fire Code banners drawn as the strip they are shown in (1050x348, the 480x180 scene cropped to its centre), so a part that
floats, a letter that is cut off or a scene that does not read at that size can be looked at.

  python3 tools/shoot-fc-banners.py OUTDIR [--ids a,b,c] [--against OLD/index.html] [--w 1050] [--h 348] [--t 1.2] [--sheet] [--dpr 1] [--cols 2]
                                    [--frames 0.2,1.2,2.4]

Writes OUTDIR/<id>.png (the live, animated banner at --t seconds). With --sheet also OUTDIR/sheet.png: every banner asked for in
two columns, labelled with its name. --scene also writes OUTDIR/<id>-scene.png, the whole 480x180 scene (nothing cropped).
--frames t1,t2,t3 (build 384 r24) writes OUTDIR/<id>-frames.png instead: the banner at each of those seconds into its life, one under the other. The
animations are PAUSED and set to that time (not waited for), so a frame is the same on any machine however slow its paint is.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
args = sys.argv[1:]
def opt(n, d=None): return args[args.index(n) + 1] if n in args else d
OUT = args[0]; os.makedirs(OUT, exist_ok=True)
BODY = open(opt("--against"), encoding="utf-8").read() if opt("--against") else None
IDS = opt("--ids").split(",") if opt("--ids") else None
W, H, T = int(opt("--w", "1050")), int(opt("--h", "348")), float(opt("--t", "1.2"))
DPR = float(opt("--dpr", "1"))
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8banr1", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
MOUNT = r"""([id, w, h, scene]) => {
  document.getElementById('splashscreen')?.remove();
  document.body.innerHTML = '';
  document.body.style.cssText = 'background:#000;margin:0';
  const box = document.createElement('div'); box.id = 'strip';
  const sw = scene ? 960 : w, sh = scene ? 360 : h;
  box.style.cssText = 'position:fixed;left:0;top:0;width:' + sw + 'px;height:' + sh + 'px;overflow:hidden;z-index:99999;background:#000';
  const el = buildBannerArt(id);
  if(scene) el.querySelector('svg').setAttribute('preserveAspectRatio', 'xMidYMid meet');
  box.appendChild(el); document.body.appendChild(box);
  return BANNERS.find(b => b.id === id).name;
}"""
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": 1100, "height": 760}, device_scale_factor=DPR)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3000)
    ids = IDS or pg.evaluate("() => BANNERS.filter(b => typeof IFC_BANNER_ART !== 'undefined' && IFC_BANNER_ART[b.id]).map(b => b.id)")
    names = {}
    FR = [float(x) for x in opt("--frames").split(",")] if opt("--frames") else None
    for i in ids:
        if FR:
            names[i] = pg.evaluate(MOUNT, [i, W, H, False]); pg.wait_for_timeout(300)
            ims = []
            for t in FR:
                pg.evaluate("(t) => document.getAnimations().forEach(a => { try{ a.pause(); a.currentTime = t * 1000; }catch(e){} })", t); pg.wait_for_timeout(120)
                pg.query_selector("#strip").screenshot(path=os.path.join(OUT, "_f.png")); ims.append(Image.open(os.path.join(OUT, "_f.png")).convert("RGB").copy())
            sh = Image.new("RGB", (W, (H + 4) * len(ims)), (18, 20, 26)); d = ImageDraw.Draw(sh)
            for n, im in enumerate(ims):
                sh.paste(im, (0, n * (H + 4))); d.text((6, n * (H + 4) + 4), "%s  t=%.1fs" % (names[i], FR[n]), fill=(255, 255, 255))
            sh.save(os.path.join(OUT, i + "-frames.png")); os.remove(os.path.join(OUT, "_f.png"))
            continue
    for i in ids if not FR else []:
        for scene in ([False, True] if "--scene" in args else [False]):
            names[i] = pg.evaluate(MOUNT, [i, W, H, scene]); pg.wait_for_timeout(int(T * 1000))
            pg.query_selector("#strip").screenshot(path=os.path.join(OUT, i + ("-scene" if scene else "") + ".png"))
    if "--sheet" in args:
        ims = [(i, Image.open(os.path.join(OUT, i + ".png")).convert("RGB")) for i in ids]
        cols = int(opt("--cols", "2")); tw = 1400 // cols; th = round(tw * H / W); pad = 8; lab = 22
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad), (18, 20, 26)); d = ImageDraw.Draw(sh)
        for n, (i, im) in enumerate(ims):
            x = pad + (n % cols) * (tw + pad); y = pad + (n // cols) * (th + lab + pad)
            d.text((x, y + 4), "%s  (%s)" % (names[i], i), fill=(190, 200, 215))
            sh.paste(im.resize((tw, th), Image.LANCZOS), (x, y + lab))
        sh.save(os.path.join(OUT, "sheet.png"))
    print("banners", len(ids), "errors", errs[:5])
    ctx.close(); br.close()
srv.shutdown()
