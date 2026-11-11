#!/usr/bin/env python3
"""Build 384.20: A SMALL PHONE ON ITS SIDE - HOME DOES NOT SCROLL, AND THE "GREY BAR" GATE HAS NOTHING TO SEE.
check-fixes' "GREY BAR" on an iPhone SE 1st gen held sideways in a Safari tab (568x260) was the one known failure for many builds (7 levels
at the bottom edge against a limit of 6). Cause, read off the page: Home is the only screen the body of which should not scroll there, and
it was 284px tall in a 260px tab (336 in a 320px installed app). .wrap reserves 8rem under the content for the tab bar (what a phone upright
or a tablet needs); the bar's whole footprint on a 568px-wide phone is 91px, so ~40px of it was nothing, and a page that scrolls puts the
html fallback layer (anchored to the top of the document) that far off the fixed sky at the bottom edge - the gate's number - and gives
Safari's toolbar something to move on the lightest touch.

Judged on the page, by shape and never by a label or a typed figure:
 (1) HOME'S PAGE IS NO TALLER THAN THE SCREEN, on every phone-sized viewport on its side and narrower than 40rem, in a browser tab and
     installed, whatever the height: the document's scroll height does not exceed the viewport's (Home is one screen there).
 (2) NOTHING WAS MOVED TO MAKE ROOM: the Start button's bottom sits above the bar's top, the bar sits wholly on the screen, and the page's
     own reserve under the content (.wrap's padding-bottom) still covers the bar's whole footprint (its offset from the edge plus its
     height) - the reserve was cut to the bar, not below it.
 (3) THE FALLBACK AGREES WITH THE FIXED SKY AT THE BOTTOM EDGE, scrolled as far as the page goes, in a browser tab: the same measurement
     check-fixes makes (html's own background against body::before over the last 40 rows) is within its 6 levels.
 (4) A WIDER PHONE AND A TABLET ARE UNTOUCHED: at a width from 40rem up (a Pro Max on its side, an iPad) .wrap's reserve is what it was -
     it still comes from the general 8rem rule, not from this one (it is not the bar's own).

  python3 tools/check-b384-selandscape.py [--against OLD/index.html]
Fails on 384.19: (1) 568x260 browser (284 > 260) and 568x320 installed (336 > 320), (3) 7 levels at (284, 221).
"""
import io, os, re, sys, socket, threading, functools, http.server
from PIL import Image
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
args = sys.argv[1:]
SRC = os.path.abspath(args[args.index("--against") + 1]) if "--against" in args else os.path.join(ROOT, "index.html")
BODY = io.open(SRC, encoding="utf-8").read()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

def load(pat):
    s = io.open(os.path.join(HERE, "sweep-layout.py")).read()
    return re.search(pat, s, re.S).group(1)
SEED = load(r'SEED = """(.*?)"""')
STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""
def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port

# (label, width, height, installed?) - a phone's landscape viewports; the 568 ones are the SE 1st gen (a Safari tab keeps 60px of the 320)
NARROW = [("SE 1st gen tab", 568, 260, False), ("SE 1st gen installed", 568, 320, True), ("568x300 tab", 568, 300, False), ("600x280 tab", 600, 280, False)]
WIDE = [("SE 2nd gen tab", 667, 315, False), ("Pro Max tab", 932, 380, False), ("iPad mini tab", 1133, 670, False)]

PROBE = """()=>{ showHome();
  return new Promise(res => setTimeout(() => {
    const de = document.documentElement, R = s => { const e = document.querySelector(s); return e && e.getBoundingClientRect(); };
    const btn = R('.panel.home .playbtn'), bar = R('.bottomtabs'), wrap = document.querySelector('.wrap');
    const pb = wrap ? parseFloat(getComputedStyle(wrap).paddingBottom) : null;
    res({ sh: de.scrollHeight, ih: innerHeight, iw: innerWidth, rem: parseFloat(getComputedStyle(de).fontSize),
          btnBottom: btn ? btn.bottom : null, barTop: bar ? bar.top : null, barBottom: bar ? bar.bottom : null, barH: bar ? bar.height : null, pb,
          cls: document.body.className }); }, 700)); }"""

def open_page(br, w, h, installed, mobile=True):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=mobile, is_mobile=mobile)
    ctx.add_init_script(SEED)
    if installed: ctx.add_init_script(STANDALONE)
    pg = ctx.new_page()
    pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto(URL); pg.wait_for_timeout(1300)
    pg.evaluate("()=>{ try{ const u=pendingHomeUnlocks(); markUnlocksShown(u.chars,u.banners,u.fx); }catch(e){} try{ homeUnlocksOwed=()=>false; }catch(e){} }")
    pg.wait_for_timeout(3600)
    pg.evaluate("()=>{ document.documentElement.style.background=''; document.getElementById('splashscreen')?.remove(); }")
    return ctx, pg

def fallback_levels(pg):
    """check-fixes' measurement: body::before against html's own background over the last 40 rows, scrolled to the end"""
    pg.evaluate("""()=>{const s=document.createElement('style'); s.id='__hc';
      s.textContent='body>*{visibility:hidden!important} html{--root-sky-a:none!important;--root-sky-b:none!important}';
      document.head.appendChild(s); window.scrollTo(0, document.documentElement.scrollHeight);}""")
    pg.wait_for_timeout(260)
    a = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    pg.evaluate("""()=>{const s=document.createElement('style'); s.id='__hb'; s.textContent='body::before{display:none!important}'; document.head.appendChild(s);}""")
    pg.wait_for_timeout(220)
    b = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    SW, SH = a.size; worst, at = 0, None
    for col in (SW // 4, SW // 2, (3 * SW) // 4):
        for y in range(max(0, SH - 40), SH):
            d = max(abs(p - q) for p, q in zip(a.getpixel((col, y)), b.getpixel((col, y))))
            if d > worst: worst, at = d, (col, y)
    pg.evaluate("()=>{document.getElementById('__hc')?.remove();document.getElementById('__hb')?.remove();}")
    return worst, at

srv, URL = serve()
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for (label, w, h, inst) in NARROW:
            ctx, pg = open_page(br, w, h, inst)
            r = pg.evaluate(PROBE)
            tag = "%s (%dx%d)" % (label, w, h)
            chk("(1) %s: Home's page is no taller than the screen (%d against %d)" % (tag, r["sh"], r["ih"]), r["sh"] <= r["ih"] + 1, r)
            if r["btnBottom"] is not None and r["barTop"] is not None:
                chk("(2) %s: Start sits above the bar and the bar is wholly on the screen" % tag, r["btnBottom"] <= r["barTop"] - 4 and r["barBottom"] <= r["ih"] + .5, r)
                footprint = (r["ih"] - r["barTop"])          # the bar's top edge to the screen's bottom: its offset plus its height
                chk("(2) %s: the reserve under the content (%.0fpx) still covers the bar's footprint (%.0fpx)" % (tag, r["pb"], footprint), r["pb"] >= footprint - 1, r)
            ctx.close()
            if not inst:
                # check-fixes measures this on a plain (not touch-emulated) page; so does this
                ctx, pg = open_page(br, w, h, inst, mobile=False)
                pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
                worst, at = fallback_levels(pg)
                chk("(3) %s: html's fallback is within 6 levels of the fixed sky at the bottom edge (%d at %s)" % (tag, worst, at), worst <= 6, (worst, at))
                ctx.close()
        for (label, w, h, inst) in WIDE:
            ctx, pg = open_page(br, w, h, inst)
            r = pg.evaluate(PROBE)
            tag = "%s (%dx%d)" % (label, w, h)
            # the general reserve is 8rem less how far the bar came down; this build's own rule would be the bar's footprint plus 6px
            general = 8 * r["rem"]
            chk("(4) %s: the page's reserve is the general one, not this build's (%.0fpx; 8rem is %.0f)" % (tag, r["pb"], general), r["pb"] >= general - 1, r)
            ctx.close()
        br.close()
finally:
    srv.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
