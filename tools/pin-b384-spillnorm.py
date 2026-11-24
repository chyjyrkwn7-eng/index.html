#!/usr/bin/env python3
"""Build 384.133: writes the "spillNorm" pin (see tools/b384_spill_lib.py) into the three character gates' .prev.json files, read off the build each gate
pins its characters to, in Fire Code:
  check-b384-r5-chars.prev.json   <- c1d224b          check-b384-r8-eyes.prev.json   <- cd34de2          check-b384-r9-chars.prev.json  <- cd82880
Only the key "spillNorm" is added or replaced; nothing else in a file is touched. Each reference build's APP_BUILD is set to this tree's version.json build so the
page does not reload mid-read.
  python3 tools/pin-b384-spillnorm.py"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from b384_spill_lib import SPILL_NORM
src = open(os.path.join(HERE, "check-b384-r5-chars.py")).read().split("# ---- what the page measures")[0]
G = {"__file__": os.path.join(HERE, "check-b384-r5-chars.py"), "__name__": "r5pin"}; sys.argv = [sys.argv[0]]; exec(src, G)
rc, INIT_IFC = G["rc"], G["INIT_IFC"]
BUILD = json.load(open(os.path.join(ROOT, "version.json")))["build"]
from playwright.sync_api import sync_playwright
def read(rev):
    body = subprocess.run(["git", "show", rev + ":index.html"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    body = re.sub(r'const APP_BUILD = "[^"]*"', 'const APP_BUILD = "%s"' % BUILD, body, count=1)
    srv, port = rc["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=rc["CHROME"]); ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
        pg.add_init_script(INIT_IFC); pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
        cls = pg.evaluate("()=>window.NOVA_CLASS"); h = pg.evaluate(SPILL_NORM); ctx.close(); br.close()
    srv.shutdown(); assert cls == "ifc" and not errs and re.fullmatch(r"[0-9a-f]+", h), (cls, errs, h)
    return h
for name, rev in (("check-b384-r5-chars.prev.json", "c1d224b"), ("check-b384-r8-eyes.prev.json", "cd34de2"), ("check-b384-r9-chars.prev.json", "cd82880")):
    p = os.path.join(HERE, name); d = json.load(open(p)); d["spillNorm"] = read(rev)
    json.dump(d, open(p, "w"), indent=0, sort_keys=True); print(name, rev, d["spillNorm"])
