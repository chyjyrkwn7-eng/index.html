#!/usr/bin/env python3
"""Contact sheet of the Fire Code class's banners, drawn by the app itself (buildBannerArt, the animated art, a still of each).

  python3 tools/shoot-fc-banners-flares.py OUTDIR [--against OLD/index.html] [--ids a,b,c] [--w 440] [--dpr 2]

Writes OUTDIR/sheet.png (the banners one under another, each its own name) and OUTDIR/one/<id>.png (one banner each, 480x180 scaled to --w).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
def opt(n, d=None): return args[args.index(n) + 1] if n in args else d
OUT = args[0]; os.makedirs(os.path.join(OUT, "one"), exist_ok=True)
BODY = open(opt("--against"), encoding="utf-8").read() if "--against" in args else None
IDS = opt("--ids", "flare_void,flare_umbra,flare_horizon,flare_genesis").split(",")
W = int(opt("--w", "440")); DPR = float(opt("--dpr", "2"))
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8bann1", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
BUILD = r"""([ids, w]) => {
  document.getElementById('splashscreen')?.remove();
  [...document.body.children].forEach(n => { if(n.tagName !== 'STYLE') n.remove(); });   /* not body.innerHTML = '': the 2.9MB stylesheet is a <style> in <body> (384 r17) */ document.body.style.cssText = 'background:#12151B;margin:0;padding:10px;width:' + w + 'px;font:12px sans-serif;color:#cfd6e2';
  ids.forEach(id => { const c = document.createElement('div'); c.className = 'cell'; c.dataset.id = id; c.style.cssText = 'margin-bottom:10px';
    const b = document.createElement('div'); b.style.cssText = 'width:' + w + 'px;height:' + Math.round(w * 180 / 480) + 'px;overflow:hidden;position:relative;border-radius:10px';
    const art = buildBannerArt(id); art.style.cssText += ';position:absolute;inset:0;width:100%;height:100%'; b.appendChild(art);
    c.appendChild(b); const n = document.createElement('div'); n.textContent = id + ' - ' + ((BANNERS.find(x => x.id === id) || {}).name); c.appendChild(n); document.body.appendChild(c); });
  return true; }"""
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": W + 20, "height": 900}, device_scale_factor=DPR)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate(BUILD, [IDS, W]); pg.wait_for_timeout(900)
    pg.screenshot(path=os.path.join(OUT, "sheet.png"), full_page=True)
    for c in pg.query_selector_all(".cell"):
        c.query_selector("div").screenshot(path=os.path.join(OUT, "one", c.get_attribute("data-id") + ".png"))
    print("errors", errs[:5]); ctx.close(); br.close()
