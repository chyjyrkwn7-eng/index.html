#!/usr/bin/env python3
"""Screenshots of the 384.36 install page at the two reference sizes (iPhone 17 Pro Max 440x956, iPad Pro 11" 834x1194), for the owner.

  install page, the video screen (alone, and on the phone with a MOCK of the iOS share sheet over the lower ~58% - Chromium has no share
  sheet, the mock is labelled and only shows the arrangement), the final state, the help page, the in-app page, the Android page and the
  Android video screen.  A status-bar strip is drawn black at the top (Chromium has no safe area; a band with no explanation was misread before).

  python3 tools/shoot-b384-installpage.py OUTDIR
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "b384-installpage-shots"
SUFFIX = sys.argv[2] if len(sys.argv) > 2 else ""      # e.g. -v2 (a second round of shots in the same folder)
os.makedirs(OUT, exist_ok=True)
SRC = L.load_src()
SIZES = (("phone", 440, 956, (62, 0, 34, 0), "iphone-safari"), ("ipad", 834, 1194, (24, 0, 20, 0), "ipad-safari"))
SHARE_STUB = "navigator.share = function(){ return Promise.resolve(); };"
MOCK = """(h)=>{ const d=document.createElement('div'); d.id='__mocksheet';
  d.style.cssText='position:fixed;left:0;right:0;bottom:0;height:58%;z-index:99998;background:#2c2c2ef2;border-radius:22px 22px 0 0;color:#fff;font:600 15px -apple-system,Helvetica,sans-serif;padding:14px 16px;box-sizing:border-box;box-shadow:0 -10px 40px #000a';
  d.innerHTML='<div style="text-align:center;font:700 12px Helvetica;letter-spacing:.06em;color:#ffd24a;margin-bottom:10px">MOCK OF THE iOS SHARE SHEET (the real one is the phone\\'s: its height and look differ)</div>'
   +'<div style="display:flex;gap:10px;margin-bottom:14px">'+['AirDrop','Messages','Mail','Notes'].map(n=>'<div style="flex:1;text-align:center"><div style="height:56px;border-radius:14px;background:#4a4a50;margin-bottom:6px"></div><span style="font:500 12px Helvetica">'+n+'</span></div>').join('')+'</div>'
   +['Copy','Add to Bookmarks','Add to Reading List','Add to Home Screen','Print'].map(n=>'<div style="padding:13px 12px;margin-bottom:2px;border-radius:12px;background:'+(n==='Add to Home Screen'?'#5a5a62':'#3c3c40')+'">'+n+(n==='Add to Home Screen'?'   (tap this)':'')+'</div>').join('');
  document.body.appendChild(d); }"""
srv, url = L.serve()
names = []


def snap(pg, tag, dev, top):
    pg.evaluate("(h)=>{ let b=document.getElementById('__sb'); if(!b){ b=document.createElement('div'); b.id='__sb'; b.style.cssText='position:fixed;left:0;right:0;top:0;height:'+h+'px;background:#000;z-index:99999;pointer-events:none'; document.body.appendChild(b); } }", top)
    f = os.path.join(OUT, "%s-%s%s.png" % (dev, tag, SUFFIX)); pg.screenshot(path=f); names.append(f)
    pg.evaluate("()=>{ for(const id of ['__sb']){ const b=document.getElementById(id); if(b) b.remove(); } }")


try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME)
        for dev, w, h, ins, ua in SIZES:
            ctx, pg = L.new_page(br, SRC, url, ua=ua, w=w, h=h, insets=ins, extra_init=(SHARE_STUB,))
            L.boot(pg, url, 1800); pg.wait_for_timeout(1000)
            snap(pg, "01-install-page", dev, ins[0])
            pg.click(".if-go"); pg.wait_for_timeout(1800)
            snap(pg, "02-video-screen", dev, ins[0])
            if dev == "phone":
                pg.evaluate(MOCK, h); snap(pg, "03-video-screen-with-MOCK-share-sheet", dev, ins[0])
                pg.evaluate("()=>{ const d=document.getElementById('__mocksheet'); if(d) d.remove(); }")
            pg.click(".installvideo-panel .next.playbtn"); pg.wait_for_timeout(800)
            snap(pg, "04-final-state", dev, ins[0])
            pg.click(".if-skip"); pg.wait_for_timeout(700)      # back to the install page
            pg.click(".if-out"); pg.wait_for_timeout(800)
            snap(pg, "05-help-page", dev, ins[0])
            ctx.close()
            ctx, pg = L.new_page(br, SRC, url, ua="iphone-instagram", w=w, h=h, insets=ins)
            L.boot(pg, url, 1800); pg.wait_for_timeout(1000)
            snap(pg, "06-in-app-page", dev, ins[0])
            ctx.close()
            ctx, pg = L.new_page(br, SRC, url, ua="android-chrome", w=w, h=h, insets=ins)
            L.boot(pg, url, 1800); pg.wait_for_timeout(1000)
            snap(pg, "07-android-page", dev, ins[0])
            pg.click(".if-go"); pg.wait_for_timeout(900)
            snap(pg, "08-android-video-screen", dev, ins[0])
            ctx.close()
        # the computer's Get Started page (it says Nova is made for a phone)
        ctx, pg = L.new_page(br, SRC, url, ua="win-chrome", w=1440, h=900, insets=(0, 0, 0, 0))
        L.boot(pg, url, 1800); pg.wait_for_timeout(2600)
        snap(pg, "09-computer-get-started", "computer", 0)
        ctx.close()
        br.close()
finally:
    srv.shutdown()
print("\n".join(names))
