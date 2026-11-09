"""Shared harness for the Customize pages (build 384 round 4): a served copy of index.html (optionally an older one, with the
device's safe-area insets substituted in), a used account in either class, standalone, no Firebase (the CDN is blocked here).
  open_page(br, cls, W, H, insets=(t,r,b,l), body=None, dpr=1)  ->  ctx, pg, errs      cls: 'ifc' (Fire Code) or 'academy'
"""
import functools, http.server, json, os, re, socket, threading
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
SEED = {"onboardingComplete": True, "firstName": "Madison", "avatarChar": "alien", "tourRev": 99, "rankMapFx244": True,
        "publicId": "xph5b57jbp5a", "novaMet": 99, "seenProfileTour": True, "leaderboardOptIn": True,
        "lifetime": {"points": 14820, "answered": 5400, "correct": 4980, "drillPlays": 64, "examPlays": 22, "gamePlays": 9,
                     "perfectTests": 60, "longestStreak": 57, "currentStreak": 23},
        "unlocksShown": {"chars": [], "banners": ["hundos100"], "fx": ["fireworks", "blackhole", "underwater", "worldtree", "bubbles", "ufo"]}}
def init_script(cls, seed=None):
    s = json.dumps(json.dumps(dict(SEED, **(seed or {}))))
    base = ("Object.defineProperty(navigator,'standalone',{get:()=>true});try{localStorage.setItem('class26e.freshstart','1');"
            "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.daily.seen','x');"
            "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');"
            "localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');"
            "localStorage.setItem('class26e.drill.v1',%s);" % s)
    if cls == "ifc":
        base += ("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
                 "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
                 "if(!localStorage.getItem('class26e.ifc.drill.v1')) localStorage.setItem('class26e.ifc.drill.v1',%s);" % s)
    return base + "}catch(e){}"
_srv = {}
def serve():
    if "port" in _srv: return _srv["port"]
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    _srv["port"] = port
    return port
def body_for(path=None, insets=(0, 0, 0, 0)):
    src = open(path or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    v = {"top": "%dpx" % insets[0], "right": "%dpx" % insets[1], "bottom": "%dpx" % insets[2], "left": "%dpx" % insets[3]}
    return INSET_RE.sub(lambda m: v[m.group(1)], src)
def open_page(br, cls, W, H, insets=(0, 0, 0, 0), body=None, dpr=1, touch=False, seed=None):
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=dpr, has_touch=touch, is_mobile=touch)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
    pg.add_init_script(init_script(cls, seed))
    b = body if body is not None else body_for(None, insets)
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto("http://127.0.0.1:%d/index.html" % serve()); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{ document.querySelectorAll('#splashscreen,#intro-pop,.app-banner,.daily-alert,.update-banner,#pushing-update,.unlock-card,.rs-spot,#tour-overlay,#tour-tooltip').forEach(n=>n.remove()); }")
    return ctx, pg, errs
