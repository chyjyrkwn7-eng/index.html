#!/usr/bin/env python3
"""Connection audit of the Fire Code characters: each drawn LARGE as the raw figure (not clipped to its coin), with the
coin's circle and a 1-unit grid ticked on top, so a part that floats, a gap at a join or a spike off the axis shows.

  python3 tools/shoot-fc-audit.py OUTDIR [--ids a,b,c] [--px 680] [--against OLD/index.html] [--sheet]

Writes OUTDIR/<id>.png (px x px = 34 viewBox units, i.e. px/34 per unit; 680 = 20px a unit = 4x a 170px figure at 5 css px/unit)
and, with --sheet, OUTDIR/audit-sheet.png (all of them side by side, labelled).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
def opt(n, d=None): return args[args.index(n) + 1] if n in args else d
OUT = args[0]; os.makedirs(OUT, exist_ok=True)
BODY = open(opt("--against"), encoding="utf-8").read() if "--against" in args else None
IDS = opt("--ids").split(",") if opt("--ids") else None
PX = int(opt("--px", "680"))
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8audit1", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
BUILD = r"""async ([ids, px]) => {
  document.getElementById('splashscreen')?.remove();
  const list = ids || Object.keys(IFC_CHAR_LOOK);
  document.body.innerHTML = '';
  document.body.style.cssText = 'background:#12151B;margin:0;padding:10px;display:flex;flex-wrap:wrap;gap:14px;width:' + (px * 3 + 60) + 'px';
  const u = px / 34;
  for(const id of list){
    const cell = document.createElement('div'); cell.className = 'cell'; cell.dataset.id = id; cell.style.cssText = 'position:relative;width:' + px + 'px;height:' + px + 'px;background:#0b0d12';
    const sv = drawAvatarCharSVG(id); sv.setAttribute('width', px); sv.setAttribute('height', px); sv.style.cssText = 'display:block;overflow:visible;position:absolute;left:0;top:0';
    cell.appendChild(sv);
    const ov = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); ov.setAttribute('viewBox', '3 3 34 34'); ov.setAttribute('width', px); ov.setAttribute('height', px);
    ov.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none';
    let g = '<circle cx="20" cy="20" r="17" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width=".08" stroke-dasharray=".4 .4"/>';
    for(let i = 4; i <= 36; i += 4) g += '<path d="M' + i + ' 3 V37 M3 ' + i + ' H37" stroke="#7af" stroke-opacity=".18" stroke-width=".04"/>';
    g += '<path d="M20 3 V37" stroke="#f55" stroke-opacity=".35" stroke-width=".05"/>';
    ov.innerHTML = g; cell.appendChild(ov);
    const lb = document.createElement('div'); lb.textContent = (AVATAR_DISPLAY_NAME[id] || id) + ' (' + id + ')'; lb.style.cssText = 'position:absolute;left:6px;top:4px;font:13px sans-serif;color:#9ab';
    cell.appendChild(lb);
    document.body.appendChild(cell);
  }
  await new Promise(r => setTimeout(r, 500));
  return list;
}"""
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": PX * 3 + 80, "height": 900}, device_scale_factor=1)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    ids = pg.evaluate(BUILD, [IDS, PX])
    if "--sheet" in args: pg.screenshot(path=os.path.join(OUT, "audit-sheet.png"), full_page=True)
    for c in pg.query_selector_all(".cell"):
        c.screenshot(path=os.path.join(OUT, c.get_attribute("data-id") + ".png"))
    print("ids", len(ids), "errors", errs[:5])
    ctx.close(); br.close()
srv.shutdown()
