#!/usr/bin/env python3
"""Screenshots of the NEW first-run path (384.27) at the two reference sizes, for the owner to look at.

For each size (iPhone 17 Pro Max 440x956, iPad Pro 11" 834x1194):
  in a browser tab, no account:  install page (iPhone Safari), the guide opened from it, the in-app browser page (Instagram), the Android
                                 install page;
  in the Home Screen icon (installed, a fresh storage): every screen a new account meets, by walking it the way a person does
                                 (Get Started, Welcome, New to Nova?, class, confirm, Nova's boxes, the tips, Home).
Safe areas are modelled (a status-bar strip is drawn black at the top: Chromium has none); the share menu is not drawn (Chromium has none).

  python3 tools/shoot-b384-onboard.py OUTDIR
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "b384-shots"
os.makedirs(OUT, exist_ok=True)
SRC = L.load_src()
SIZES = (("phone", 440, 956, (62, 0, 34, 0), "iphone-safari"), ("ipad", 834, 1194, (24, 0, 20, 0), "ipad-safari"))
SHARE_STUB = "navigator.share = function(){ return Promise.resolve(); };"
srv, url = L.serve()
names = []


def snap(pg, tag, dev, inset_top):
    # a status-bar strip, because a screenshot with an unexplained band at the top has been misread before
    pg.evaluate("(h)=>{ let b=document.getElementById('__sb'); if(!b){ b=document.createElement('div'); b.id='__sb'; b.style.cssText='position:fixed;left:0;right:0;top:0;height:'+h+'px;background:#000;z-index:99999;pointer-events:none'; document.body.appendChild(b); } }", inset_top)
    f = os.path.join(OUT, "%s-%s.png" % (dev, tag))
    pg.screenshot(path=f); names.append(f)
    pg.evaluate("()=>{ const b=document.getElementById('__sb'); if(b) b.remove(); }")


try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME)
        for dev, w, h, ins, ua in SIZES:
            # ---- in a browser tab
            ctx, pg = L.new_page(br, SRC, url, ua=ua, w=w, h=h, insets=ins, extra_init=(SHARE_STUB,))
            L.boot(pg, url, 1800); pg.wait_for_timeout(1000)
            snap(pg, "01-install-page", dev, ins[0])
            pg.click(".if-guide"); pg.wait_for_timeout(1800); snap(pg, "02-install-guide", dev, ins[0])
            ctx.close()
            ctx, pg = L.new_page(br, SRC, url, ua="iphone-instagram", w=w, h=h, insets=ins)
            L.boot(pg, url, 1800); pg.wait_for_timeout(1000)
            snap(pg, "03-in-app-browser", dev, ins[0])
            ctx.close()
            ctx, pg = L.new_page(br, SRC, url, ua="android-chrome", w=w, h=h, insets=ins)
            L.boot(pg, url, 1800); pg.wait_for_timeout(1000)
            snap(pg, "04-android-install-page", dev, ins[0])
            ctx.close()
            # ---- in the icon
            ctx, pg = L.new_page(br, SRC, url, ua="iphone-safari", w=w, h=h, installed=True, insets=ins)
            L.boot(pg, url, 2500)
            seq = [0]
            def shot(label):
                seq[0] += 1
                pg.wait_for_timeout(900)
                snap(pg, "%02d-icon-%s" % (10 + seq[0], "".join(c if c.isalnum() else "-" for c in label)[:28]), dev, ins[0])
            def box(label):
                if label in ("nova-box-1", "nova-box-3", "nova-box-5", "nova-box-8"):
                    seq[0] += 1; snap(pg, "%02d-icon-%s" % (10 + seq[0], label), dev, ins[0])
            def tip(label):
                seq[0] += 1; snap(pg, "%02d-icon-%s" % (10 + seq[0], label), dev, ins[0])
            r = L.walk_signup(pg, "J.Smith", shot=shot, box_shot=box, tip_shot=tip)
            pg.wait_for_timeout(1500); seq[0] += 1; snap(pg, "%02d-icon-home" % (10 + seq[0]), dev, ins[0])
            print(dev, "walk:", r["taps"], "presses;", len(names), "shots so far", flush=True)
            ctx.close()
        br.close()
finally:
    srv.shutdown()
print("\n".join(names))
