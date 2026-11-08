#!/usr/bin/env python3
"""The Fire Code banners drawn as the strip they are shown in (1050x348, the 480x180 scene cropped to its centre), so a part that
floats, a letter that is cut off or a scene that does not read at that size can be looked at.

  python3 tools/shoot-fc-banners.py OUTDIR [--ids a,b,c] [--against OLD/index.html] [--w 1050] [--h 348] [--t 1.2] [--sheet]

Writes OUTDIR/<id>.png (the live, animated banner at --t seconds). With --sheet also OUTDIR/sheet.png: every banner asked for in
two columns, labelled with its name. --scene also writes OUTDIR/<id>-scene.png, the whole 480x180 scene (nothing cropped).
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
    ctx = br.new_context(viewport={"width": 1100, "height": 760}, device_scale_factor=1)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3000)
    ids = IDS or pg.evaluate("() => BANNERS.filter(b => typeof IFC_BANNER_ART !== 'undefined' && IFC_BANNER_ART[b.id]).map(b => b.id)")
    names = {}
    for i in ids:
        for scene in ([False, True] if "--scene" in args else [False]):
            names[i] = pg.evaluate(MOUNT, [i, W, H, scene]); pg.wait_for_timeout(int(T * 1000))
            pg.query_selector("#strip").screenshot(path=os.path.join(OUT, i + ("-scene" if scene else "") + ".png"))
    if "--sheet" in args:
        ims = [(i, Image.open(os.path.join(OUT, i + ".png")).convert("RGB")) for i in ids]
        tw = 700; th = round(tw * H / W); cols = 2; pad = 8; lab = 22
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
