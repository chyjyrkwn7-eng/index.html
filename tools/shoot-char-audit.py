#!/usr/bin/env python3
"""shoot-char-audit.py - the base-art characters, big, for a connection audit.

  python3 tools/shoot-char-audit.py OUTDIR [--against OLD/index.html] [--ids a,b] [--big 480] [--tag before]

For each id it writes OUTDIR/<tag>-<id>.png: the character as a big round coin (the real drawing, the real
.avatarchar-svg mask and filter), the same drawing with the mask off (so a shape that stops short or overshoots
can be seen), and an unlock-card coin (7.6rem) at device pixel ratio 3, side by side; and OUTDIR/<tag>-sheet.png
with every id at 4x. It builds each character with the app's own buildAvatarCharSVG.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright

args = list(sys.argv[1:])
def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default
OUT = args[0]
BODY = open(opt("--against"), encoding="utf-8").read() if "--against" in args else None
IDS = opt("--ids").split(",") if opt("--ids") else None
DPR = int(opt("--dpr", "2"))
BIG = int(opt("--big", "480"))
TAG = opt("--tag", "shot")
os.makedirs(OUT, exist_ok=True)

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4chaud001", classes=["academy"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S

BUILD = r"""async ([ids, big]) => {
  document.getElementById('splashscreen')?.remove();
  const list = ids || AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy).map(c => c.id);
  [...document.body.children].forEach(n => { if(n.tagName !== 'STYLE') n.remove(); });   /* not body.innerHTML = '': the 2.9MB stylesheet is a <style> in <body> (384 r17) */
  document.body.style.cssText = 'background:#12151B;margin:0;padding:14px;font:13px sans-serif;color:#cfd6e2';
  const wrap = document.createElement('div'); wrap.id = 'wrap'; document.body.appendChild(wrap);
  for(const id of list){
    const cell = document.createElement('div'); cell.className = 'cell'; cell.dataset.id = id;
    cell.style.cssText = 'display:flex;gap:16px;align-items:flex-start;padding:10px;background:#12151B;width:max-content';
    const coin = (px, mask, card) => {
      const d = document.createElement('div');
      d.style.cssText = 'width:' + px + 'px;height:' + px + 'px;border-radius:50%;overflow:hidden;position:relative;flex:none;' +
        (card ? 'background:radial-gradient(circle at 50% 38%, color-mix(in srgb,' + (AVATAR_GLOW[id] || '#fff') + ' 22%, #1C212B), #0E1117 72%);box-shadow:0 0 0 1px rgba(255,255,255,.12)' : 'background:#0b0d12');
      const sv = buildAvatarCharSVG(id); sv.style.cssText = 'width:100%;height:100%;display:block' + (mask ? '' : ';-webkit-mask-image:none;mask-image:none');
      d.appendChild(sv); return d;
    };
    cell.appendChild(coin(big, true, false));
    cell.appendChild(coin(big, false, false));
    const col = document.createElement('div'); col.style.cssText = 'display:flex;flex-direction:column;gap:10px;align-items:center';
    col.appendChild(coin(Math.round(7.6 * 16), true, true));
    const nm = document.createElement('div'); nm.textContent = id; col.appendChild(nm);
    cell.appendChild(col);
    wrap.appendChild(cell);
  }
  await new Promise(r => setTimeout(r, 600));
  return list;
}"""

srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": BIG * 2 + 400, "height": 900}, device_scale_factor=DPR)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.on("console", lambda m: errs.append("console:" + m.text[:160]) if m.type == "error" and "firebase" not in m.text.lower() and "Failed to load resource" not in m.text else None)
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    ids = pg.evaluate(BUILD, [IDS, BIG])
    for c in pg.query_selector_all(".cell"):
        i = c.get_attribute("data-id")
        c.screenshot(path=os.path.join(OUT, "%s-%s.png" % (TAG, i)))
    print("ids", len(ids), ids, "errors", errs[:5])
    ctx.close(); br.close()
srv.shutdown()
