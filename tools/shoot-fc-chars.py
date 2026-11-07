#!/usr/bin/env python3
"""Contact sheets of the Fire Code class's characters, drawn by the app itself.

  python3 tools/shoot-fc-chars.py OUTDIR [--against OLD/index.html] [--ids a,b,c] [--big 300]

Writes, in OUTDIR:
  sheet.png          every Fire Code character as a big coin, a 56px coin and a 26px rankings dot, with its name
  one/<id>.png       one big coin each (with its backdrop and glow, as the Customize card shows it)
It loads the page as the Fire Code class (the same fixture check-b384-ifcchars uses) and builds each character with
buildAvatarCharSVG, so it is the app's own drawing, not a copy.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:]]
def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default
OUT = args[0]
BODY = open(opt("--against"), encoding="utf-8").read() if "--against" in args else None
IDS = opt("--ids").split(",") if opt("--ids") else None
BIG = int(opt("--big", "300"))
CLASS = opt("--class", "ifc")      # "academy" draws the academy's own set (for comparing)
os.makedirs(os.path.join(OUT, "one"), exist_ok=True)

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8chars1", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
if CLASS == "academy":
    INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S

BUILD = r"""async ([ids, big]) => {
  document.getElementById('splashscreen')?.remove();
  const list = ids || AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy).map(c => c.id);
  document.body.innerHTML = '';
  document.body.style.cssText = 'background:#12151B;margin:0;padding:14px;font:12px sans-serif;color:#cfd6e2;width:' + (big * 6 + 7 * 24) + 'px';
  const grid = document.createElement('div'); grid.id = 'grid'; grid.style.cssText = 'display:grid;grid-template-columns:repeat(6,' + big + 'px);gap:22px 24px';
  document.body.appendChild(grid);
  const coin = (id, px) => {
    const d = document.createElement('div');
    d.style.cssText = 'width:' + px + 'px;height:' + px + 'px;border-radius:50%;overflow:hidden;position:relative;flex:none;background:#0b0d12;box-shadow:0 0 ' + Math.round(px / 8) + 'px ' + (AVATAR_GLOW[id] || '#888') + '66';
    const sv = buildAvatarCharSVG(id); sv.style.cssText = 'width:100%;height:100%;display:block'; d.appendChild(sv); return d;
  };
  for(const id of list){
    const cell = document.createElement('div'); cell.className = 'cell'; cell.dataset.id = id; cell.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:6px';
    cell.appendChild(coin(id, big));
    const row = document.createElement('div'); row.style.cssText = 'display:flex;align-items:center;gap:12px';
    row.appendChild(coin(id, 56)); row.appendChild(coin(id, 26));
    const nm = document.createElement('span'); nm.textContent = (AVATAR_DISPLAY_NAME[id] || id) + '  (' + id + ')'; row.appendChild(nm);
    cell.appendChild(row); grid.appendChild(cell);
  }
  await new Promise(r => setTimeout(r, 600));
  return list;
}"""

srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": BIG * 6 + 7 * 24 + 28, "height": 900}, device_scale_factor=1)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.on("console", lambda m: errs.append("console:" + m.text[:160]) if m.type == "error" and "firebase" not in m.text.lower() and "Failed to load resource" not in m.text else None)
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    cls = pg.evaluate("window.NOVA_CLASS")
    ids = pg.evaluate(BUILD, [IDS, BIG])
    pg.screenshot(path=os.path.join(OUT, "sheet.png"), full_page=True)
    for c in pg.query_selector_all(".cell"):
        i = c.get_attribute("data-id")
        c.query_selector("div").screenshot(path=os.path.join(OUT, "one", i + ".png"))
    print("class", cls, "ids", len(ids), "errors", errs[:5])
    ctx.close(); br.close()
srv.shutdown()
