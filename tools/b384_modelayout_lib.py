"""Shared harness for the mode-screen layout gate and its screenshots (384 r20).
Boots the app the way check-b384-modes does (a used account, installed, both classes, the in-memory Firestore) but at ANY
viewport / screen / inset, so the page-zoomed case (518 CSS px on a 440pt screen) and the laptop sizes can be read too.
`--against FILE` (anywhere in argv) serves that file instead of the worktree's index.html."""
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
# check-b383-ifcsync reads sys.argv for --against itself, so it patches its own page(); we only borrow its pieces
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ml"}
exec(_src, G)
g = G["g"]
OLD = None
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
CHROME = g["CHROME"]
# label: (viewport w, h, screen w, h, insets, installed)
DEVICES = {
    "se-375x667":          (375, 667, 375, 667, (20, 0, 0, 0), True),
    "promax-440x956":      (440, 956, 440, 956, (62, 0, 34, 0), True),
    "promax-zoom-518x1126": (518, 1126, 440, 956, (62, 0, 34, 0), True),
    "ipad11-834x1194":     (834, 1194, 834, 1194, (24, 0, 20, 0), True),
    "ipad11-land-1194x834": (1194, 834, 1194, 834, (24, 0, 20, 0), True),
    "laptop-1366x768":     (1366, 768, 1366, 768, (0, 0, 0, 0), False),
    "desktop-1920x1080":   (1920, 1080, 1920, 1080, (0, 0, 0, 0), False),
}
def body_for(ins):
    t, r, b, l = ins
    v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], OLD) if OLD is not None else g["patched"](ins)
OLD_BUILD = re.search(r'const APP_BUILD = "([^"]+)"', OLD).group(1) if OLD else None
def open_page(br, cls, dev):
    W, H, SW, SH, ins, installed = DEVICES[dev]
    init = G["init"](G["ifc"] if cls == "ifc" else G["academy"], **({} if cls == "ifc" else {"active": "academy"}))
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": SW, "height": SH}, device_scale_factor=2 if W < 1300 else 1,
                         has_touch=installed, is_mobile=False)
    ctx.add_init_script("window.__cloudSeed = {};")
    ctx.add_init_script(G["FAKE"])
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(init)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    if OLD_BUILD:
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""})))
    body = body_for(ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3200)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
CLEAR = ("()=>{ try{ homeUnlocksOwed = () => false; }catch(e){} document.querySelectorAll('.unlock-card,.rs-spot,.rs-fly,.daily-alert').forEach(n => n.remove());"
         " document.body.classList.remove('cutscene-focus'); store.seenModeSelectTour = true; }")
def show(pg, which):
    pg.evaluate(CLEAR)
    if which == "modes": pg.evaluate("()=>showModeSelect()")
    elif which == "vroom": pg.evaluate("()=>{ cfg.mode='vroom'; showVirtualRoomChoice(); }")
    else: pg.evaluate(which)
    pg.wait_for_timeout(1500)
