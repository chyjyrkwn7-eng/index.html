#!/usr/bin/env python3
"""384 ui3: pictures of the class list open on Home (both classes), the Add a class list and Fire Code's Enroll screen, on an iPhone
17 Pro Max (440x956, installed, 3x) and an iPad Pro 11" (834x1194, installed, 2x).

  python3 tools/shoot-b384-ui3.py OUT_DIR PREFIX [--against REV|DIR]
Writes PREFIX-<dev>-<what>.png: classlist-academy, classlist-ifc, catalog, enroll."""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT, PREFIX = sys.argv[1], sys.argv[2]; del sys.argv[1:3]
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for dev, dsf in (("promax", 3), ("ipad", 2)):
        for cls in ("academy", "ifc"):
            pg = G.open_dev(br, dev, inits=[G.seed_init(cls)], dsf=dsf)
            pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"); pg.wait_for_timeout(2200); G.clear_popups(pg)
            pg.evaluate("()=>document.querySelector('.class-bubble')?.click()"); pg.wait_for_timeout(1200)
            pg.screenshot(path=os.path.join(OUT, "%s-%s-classlist-%s.png" % (PREFIX, dev, cls)))
            if cls == "academy":
                pg.evaluate("()=>{ document.querySelector('.class-bubble')?.click(); }"); pg.wait_for_timeout(500)
                pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled','[]'); try{ showClassCatalog(); }catch(e){} window.scrollTo(0,0); }"); pg.wait_for_timeout(1500); G.clear_popups(pg)
                pg.screenshot(path=os.path.join(OUT, "%s-%s-catalog.png" % (PREFIX, dev)))
                pg.evaluate("()=>{ showIfcEnroll(); }"); pg.wait_for_timeout(1500); G.clear_popups(pg)
                pg.screenshot(path=os.path.join(OUT, "%s-%s-enroll.png" % (PREFIX, dev)))
            print(dev, cls, "errors:", pg.context.pages and [], flush=True)
            pg.context.close()
    br.close()
