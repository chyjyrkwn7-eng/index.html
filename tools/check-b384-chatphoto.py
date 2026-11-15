#!/usr/bin/env python3
"""Build 384.127: A PICTURE IN A CHAT ENLARGES WHEN IT IS TAPPED, ON EVERY CHAT, AND IS SHOWN AS LARGE AS THE SCREEN ALLOWS.

Madison: "Pictures in the chat, when clicking them, ensure they enlarge."
Every picture is drawn by ONE function (buildPhoto, in buildVroomChatPanel), so the surfaces are one code path with different hosts.
Against an in-memory Firestore (the CDN is blocked here), a real boot in each class, an account with a photo message, per surface:
  friend chat (dock), group chat (dock), Nova's chat (dock, a local message), the Virtual Room lobby chat (inline on the page),
  the Virtual Room chat sheet (the panel lifted into .roomchat-overlay)
at an iPhone 17 Pro Max (440x956, installed, insets 59/34) and an iPad Pro 11" (834x1194):
  (1) TAP OPENS IT: a real touch (CDP touchStart/touchEnd) at the picture's middle opens .chat-photo-view;
  (2) AS LARGE AS IT CAN BE: the enlarged image is inside the viewport less the safe-area insets, at least FACTOR times the
      thumbnail (FACTOR read off the page: the bigger of the two the fit allows) and is the largest size that fits (one side
      touches the padding box, and its aspect is the picture's natural aspect to 1%) - a small picture is scaled UP to fit;
  (3) ON TOP: the viewer is the top-most element at the viewport's centre, and over the chat sheet;
  (4) CLOSES: a tap anywhere on it, the visible 44px button, Escape and a swipe down each close it, and the tap does not reach
      the chat underneath (no react picker, no second viewer);
  (5) STILL: the page and the chat's list do not scroll behind it (a wheel / touch move over it);
  (6) NAVIGATION CLEARS IT: a screen change (showHome) removes it;
  (7) STATES: a photo still loading opens the viewer and fills it when it arrives; a photo that is gone opens nothing and
      raises no error; a photo sent before the size fields (no w / h) opens as large; a tap that lands while the list is
      re-rendered (a snapshot between touchStart and touchEnd: the typing line, a reaction, somebody's heartbeat) still opens
      it; a photo is not rebuilt (same node, no loading shimmer) by a re-render that did not change it;
  (8) no page errors.
Run:  python3 tools/check-b384-chatphoto.py [--quick] [--probe] [--against OLD/index.html]   (384.107 must FAIL (1)(2)(4)(6)(7))
"""
import base64, functools, http.server, io, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
_VR = open(os.path.join(HERE, "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)
QUICK = "--quick" in sys.argv
PROBE = "--probe" in sys.argv
OLD = None; OLD_BUILD = None
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    OLD_BUILD = re.search(r'const APP_BUILD = "([^"]+)"', OLD).group(1)
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")

ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:500]), flush=True)

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port

# ---- small generated pictures (palette PNGs, a few KB each); bands and a diagonal so a crop or a stretch shows
def make_png(w, h, hue):
    im = Image.new("P", (w, h)); d = ImageDraw.Draw(im)
    pal = []
    for i in range(16): pal += [min(255, 30 + i * 14 + hue * 9 % 90), min(255, 60 + (i * 7 + hue * 40) % 200), min(255, 220 - i * 10)]
    im.putpalette(pal + [0] * (768 - len(pal)))
    for i in range(0, h, max(4, h // 14)): d.rectangle([0, i, w, i + max(4, h // 14) - 1], fill=(i // max(4, h // 14)) % 16)
    d.line([0, 0, w, h], fill=15, width=max(2, w // 60)); d.rectangle([0, 0, w - 1, h - 1], outline=3, width=max(2, w // 80))
    b = io.BytesIO(); im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
PICS = {"land": (600, 400), "port": (300, 520), "small": (120, 90), "old": (640, 360), "own": (480, 480), "slow": (500, 300)}
IMG = {k: make_png(w, h, i) for i, (k, (w, h)) in enumerate(PICS.items())}

ME, ALEX, KIM = "me0000000001", "alex000000002", "kim0000000003"
ACADEMY = {"firstName": "Madison", "avatarChar": "grizzly", "onboardingComplete": True, "tourRev": 999, "leaderboardOptIn": True,
           "publicId": ME, "classes": ["academy", "ifc"], "lastModified": 1790500000000, "novaMet": 99, "hiveMoved384": True,
           "novaHeard": {"@recap": 99991231}, "seenClassTip": True}
IFCSTORE = dict(ACADEMY); IFCSTORE.pop("classes")
ROWS = [{"pub": ALEX, "firstName": "Alex", "avatarChar": "marksman"}, {"pub": KIM, "firstName": "Kim", "avatarChar": "astronaut"}]
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked',"
        "'class26e.savecode.card','class26e.getstarted','class26e.penal55124.seen','class26e.penal124256.seen','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');")
SEEN_IFC = ("['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card',"
            "'class26e.ifc.getstarted','class26e.ifc.unithold.tip','class26e.ifc.a2hs'].forEach(k=>localStorage.setItem(k,'1'));")
def init_js(cls):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(ACADEMY))
    s += "localStorage.setItem('class26e.synccode', 'SYNC-ME');"
    s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(IFCSTORE))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.greet.ifc','done');" + SEEN_IFC
    return s + " })()"

SETUP = """(cfg)=>{
  document.getElementById('splashscreen')?.remove(); __useFake();
  store.onboardingComplete = true; store.firstName = 'Madison'; store.publicId = cfg.me; store.leaderboardOptIn = true;
  store.tourRev = 999; store.savedCodeSaved = true;
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour','seenUnitOptionsTour',
   'seenUnitSelectTour','seenMainMenuTour','seenClassTip'].forEach(k => store[k] = true);
  syncCode = 'SYNC-ME'; chatRoomCode = null; chatMyKey = null;
  try{ homeUnlocksOwed = () => false; scheduleWeekRecap = () => {}; maybeShowWeekRecap = () => {}; }catch(e){}
  leaderboardRows = cfg.rows.map(r => Object.assign({ facc: [], freq: [], level: 3, badges: 0, hundos: 0 }, r));
  store.friendsIn = cfg.friends; store.chats = [];
  chatImageCache['img-own'] = cfg.imgs.own;                      /* your own picture: in this device's cache, no document yet */
  const imgs = Object.keys(cfg.imgs).filter(k => k !== 'own' && k !== 'slow');
  return Promise.all(imgs.map(k => fbDb.collection('vrooms').doc('img-' + k).set({ kind: 'chatimg', data: cfg.imgs[k], by: cfg.alex, at: Date.now() })))
    .then(() => { showHome(); return window.NOVA_CLASS; }); }"""

DEVS = [("Pro Max", 440, 956, 59, 34, "phone"), ("iPad 11", 834, 1194, 24, 20, "tablet")]
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")

def boot(br, url, cls, dev, errs, video=None):
    name, W, H, it, ib, kind = dev
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True,
                         user_agent=UA if kind == "phone" else UA_PAD,
                         **({"record_video_dir": video, "record_video_size": {"width": W, "height": H}} if video else {}))
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(FAKE); ctx.add_init_script(init_js(cls))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("%s %s: %s" % (name, cls, str(e)[:160])))
    ins = {"top": "%dpx" % it, "bottom": "%dpx" % ib, "left": "0px", "right": "0px"}
    html = INSET_RE.sub(lambda m: ins[m.group(1)], OLD if OLD is not None else open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": OLD_BUILD or "x", "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=html))
    pg.goto(url, timeout=180000); pg.wait_for_timeout(4000)
    for _ in range(60):
        if pg.evaluate("()=>typeof store === 'object' && !!store && typeof __useFake === 'function' && window.NOVA_CLASS !== undefined"): break
        pg.wait_for_timeout(500)
    got = pg.evaluate(SETUP, {"me": ME, "alex": ALEX, "rows": ROWS, "friends": [ALEX, KIM], "imgs": IMG})
    pg.wait_for_timeout(400)
    return ctx, pg, got

def msg(i, key, name, kind, ts_off=0, **kw):
    import time
    m = {"id": "m%d-%s" % (i, kind), "key": key, "name": name, "text": "\U0001F4F7 Photo", "ts": int(time.time() * 1000) - 60000 + i * 1000 + ts_off, "type": "img", "img": "img-" + kind}
    m.update(kw); return m

def photo_msgs(key=ALEX, name="Alex"):
    """the thread, in the order the page draws it: a text, then land, port, small, old (no w/h), own (sent by you, its image only in the
    device's cache: the document it was written to has not come back), nope (the image document is gone)"""
    return [{"id": "t0", "key": key, "name": name, "text": "look at this", "ts": 0},
            msg(1, key, name, "land", w=600, h=400), msg(2, key, name, "port", w=300, h=520), msg(3, key, name, "small", w=120, h=90),
            msg(4, key, name, "old"), msg(5, ME, "Madison", "own", w=480, h=480), msg(6, key, name, "nope", w=200, h=200)]
ORDER = ["land", "port", "small", "old", "own", "nope"]

def fix_ts(msgs):
    import time
    now = int(time.time() * 1000)
    for i, m in enumerate(msgs):
        if not m.get("ts"): m["ts"] = now - 70000
    return msgs

# ---- in-page helpers
CENTRE = """(sel)=>{ const el = document.querySelector(sel); if(!el) return null;
  el.scrollIntoView({block:'center'}); const r = el.getBoundingClientRect();
  return { x: r.left + r.width/2, y: r.top + r.height/2, w: r.width, h: r.height, top: r.top, bottom: r.bottom }; }"""
VIEW = """()=>{ const v = document.querySelector('.chat-photo-view'); if(!v) return null;
  const img = v.querySelector('img'); const r = img ? img.getBoundingClientRect() : null;
  const vr = v.getBoundingClientRect(); const cs = getComputedStyle(document.documentElement);
  const cx = innerWidth/2, cy = innerHeight/2; const top = document.elementFromPoint(cx, cy);
  const x = v.querySelector('button, [role=button]'); const xr = x ? x.getBoundingClientRect() : null;
  return { n: document.querySelectorAll('.chat-photo-view').length,
    img: r ? { l: r.left, t: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom, nw: img.naturalWidth, nh: img.naturalHeight, ok: img.complete && img.naturalWidth > 0 } : null,
    view: { l: vr.left, t: vr.top, w: vr.width, h: vr.height },
    onTop: !!(top && (top === v || v.contains(top))), topTag: top ? (top.className || top.tagName) : null,
    x: xr ? { w: xr.width, h: xr.height, t: xr.top, r: xr.right } : null, vw: innerWidth, vh: innerHeight,
    z: getComputedStyle(v).zIndex, bodyOverflow: getComputedStyle(document.body).overflow }; }"""

# ---- surfaces
def put_messages(pg, code, msgs, extra=None):
    """write the room document the chat listens to (the fake notifies the listener)"""
    pg.evaluate("""(x)=>{ const ref = fbDb.collection('vrooms').doc(x.code);
        return ref.get().then(s => { const d = s && s.exists ? s.data() : {};
          d.kind = d.kind || 'chat'; d.chatMessages = x.msgs; d.typing = d.typing || {};
          d.participants = Object.assign({ [x.me]: { name:'Madison', avatarChar:'grizzly', joinedAt: 1, seen: Date.now() },
            [x.alex]: { name:'Alex', avatarChar:'marksman', joinedAt: 2, seen: Date.now() } }, d.participants || {});
          Object.assign(d, x.extra || {}); return ref.set(d); }); }""",
                {"code": code, "msgs": msgs, "me": ME, "alex": ALEX, "extra": extra})

def open_surface(pg, surface, msgs):
    """returns (root selector, room code or None)"""
    msgs = fix_ts(msgs)
    if surface == "friend":
        pg.evaluate("(p)=>{ chatDockTab='friends'; openChatDock(); openFriendChat(p); }", ALEX); pg.wait_for_timeout(900)
        code = pg.evaluate("()=>chatRoomCode"); put_messages(pg, code, msgs); pg.wait_for_timeout(900)
        return "#chatdock .vroom-chat", code
    if surface == "group":
        code = "PHOTO-GROUP-" + str(abs(hash(str(msgs[0]["ts"]))) % 1000)
        pg.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).set({ kind:'chat', createdAt: Date.now(), chatMessages: [], typing: {},
            participants: { [x.me]: { name:'Madison', avatarChar:'grizzly', joinedAt: 1, seen: Date.now() }, [x.alex]: { name:'Alex', avatarChar:'marksman', joinedAt: 2, seen: Date.now() } } })""",
                    {"code": code, "me": ME, "alex": ALEX})
        pg.evaluate("(c)=>{ chatDockTab='chats'; openChatDock(); return joinChatRoom(c); }", code); pg.wait_for_timeout(900)
        put_messages(pg, code, msgs); pg.wait_for_timeout(900)
        return "#chatdock .vroom-chat", code
    if surface == "nova":
        pg.evaluate("""()=>{ try{ store.novaMet = 99; }catch(e){} openNovaChat(); }"""); pg.wait_for_timeout(900)
        pg.evaluate("""(ms)=>{ ms.forEach(m => { m.key = 'nova'; m.name = 'Nova'; novaAppend(m); }); novaListeners.forEach(f => f(novaPanelData())); }""", msgs)
        pg.wait_for_timeout(700)
        return "#chatdock .vroom-chat", "DM-NOVA"
    if surface in ("lobby", "sheet"):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
        pg.evaluate("()=>createVirtualRoomLobby(['Identity Crimes'], null, 'race')")
        for _ in range(40):
            if pg.evaluate("()=>!!vroomCode"): break
            pg.wait_for_timeout(250)
        code = pg.evaluate("()=>vroomCode"); pg.wait_for_timeout(600)
        put_messages(pg, code, msgs); pg.wait_for_timeout(900)
        if surface == "sheet":
            pg.evaluate("()=>openRoomChatSheet()"); pg.wait_for_timeout(600)
            return "#roomchat-sheet .vroom-chat", code
        return "#stage .vroom-chat", code
    raise ValueError(surface)

SURFACES = ["friend", "group", "nova", "lobby", "sheet"]

def nth_fig(pg, root, i):
    """the i-th photo in the list, scrolled to the middle of its list and let settle, with its centre"""
    js = """([root, i, go])=>{ const f = [...document.querySelectorAll(root + ' .vroom-chat-photo')][i]; if(!f) return null;
      if(go) f.scrollIntoView({block:'center'}); const r = f.getBoundingClientRect();
      return { x: r.left + r.width/2, y: r.top + r.height/2, w: r.width, h: r.height }; }"""
    r = pg.evaluate(js, [root, i, True]); pg.wait_for_timeout(250)
    return pg.evaluate(js, [root, i, False]) or r

def touch(pg, x, y, hold=40, between=None):
    """a real touch through the browser's input pipeline; `between` runs after the finger is down and before it lifts"""
    c = pg.context.new_cdp_session(pg)
    c.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]})
    pg.wait_for_timeout(hold)
    if between: between()
    c.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(450)
    try: c.detach()
    except Exception: pass

def tap(pg, x, y): touch(pg, x, y)

def close_all(pg):
    pg.evaluate("()=>{ document.querySelectorAll('.chat-photo-view').forEach(v=>v.remove()); }")

def drag(pg, x0, y0, x1, y1, steps=10, hold=16):
    c = pg.context.new_cdp_session(pg)
    c.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0, "id": 1}]})
    for i in range(1, steps + 1):
        pg.wait_for_timeout(hold)
        c.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * i / steps, "y": y0 + (y1 - y0) * i / steps, "id": 1}]})
    c.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(450)
    try: c.detach()
    except Exception: pass

def double_tap(pg, x, y, gap=20):
    c = pg.context.new_cdp_session(pg)
    for i in range(2):
        c.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]}); pg.wait_for_timeout(10)
        c.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        if i == 0: pg.wait_for_timeout(gap)
    pg.wait_for_timeout(450)
    try: c.detach()
    except Exception: pass

def pinch_out(pg, cx, cy, d0=40, d1=160, steps=8):
    c = pg.context.new_cdp_session(pg)
    pts = lambda d: [{"x": cx - d / 2, "y": cy, "id": 1}, {"x": cx + d / 2, "y": cy, "id": 2}]
    c.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": pts(d0)})
    for i in range(1, steps + 1):
        pg.wait_for_timeout(16)
        c.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": pts(d0 + (d1 - d0) * i / steps)})
    c.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(450)
    try: c.detach()
    except Exception: pass

VIEW2 = """()=>{ const v = document.querySelector('.chat-photo-view'); if(!v) return null;
  const img = v.querySelector('img'); const cs = getComputedStyle(v); const ic = img ? getComputedStyle(img) : null;
  const pad = { t: parseFloat(cs.paddingTop), r: parseFloat(cs.paddingRight), b: parseFloat(cs.paddingBottom), l: parseFloat(cs.paddingLeft) };
  const r = img ? img.getBoundingClientRect() : null, nw = img ? img.naturalWidth : 0, nh = img ? img.naturalHeight : 0;
  let f = null;
  if(r && nw){ if(ic.objectFit === 'contain'){ const k = Math.min(r.width / nw, r.height / nh); const w = nw * k, h = nh * k;
      f = { l: r.left + (r.width - w) / 2, t: r.top + (r.height - h) / 2, w, h }; } else f = { l: r.left, t: r.top, w: r.width, h: r.height }; }
  const x = v.querySelector('button'); const xr = x ? x.getBoundingClientRect() : null;
  const top = document.elementFromPoint(innerWidth / 2, innerHeight / 2);
  const bx = v.querySelector('.chat-photo-view-box');
  return { n: document.querySelectorAll('.chat-photo-view').length, pad, vw: innerWidth, vh: innerHeight, f, nat: [nw, nh], loaded: !!(img && img.complete && nw > 0),
    wait: v.classList.contains('is-wait'), onTop: !!(top && (top === v || v.contains(top))), topCls: top ? (String(top.className) || top.tagName) : null,
    x: xr ? { w: xr.width, h: xr.height, cx: xr.left + xr.width / 2, cy: xr.top + xr.height / 2 } : null, z: cs.zIndex,
    tf: bx ? bx.style.transform : '', vr: (()=>{ const q = v.getBoundingClientRect(); return [q.left, q.top, q.width, q.height]; })() }; }"""
STILL = """(root)=>{ const l = document.querySelector(root + ' .vroom-chat-list'); const p = document.querySelector('#chatdock .chatdock-panel');
  const pr = p ? p.getBoundingClientRect() : null;
  return { sy: scrollY, sx: scrollX, list: l ? l.scrollTop : null, panel: pr ? [pr.left, pr.top, pr.width, pr.height] : null, dock: !!(p && document.querySelector('#chatdock.is-open')) }; }"""
UNDER = """([x, y])=>{ const e = document.elementFromPoint(x, y); return e ? (String(e.className) || e.tagName) : null; }"""
PICKER = "()=>({ picker: document.querySelectorAll('.vroom-chat-picker').length, picking: document.querySelectorAll('.vroom-chat-msgwrap.is-picking').length, views: document.querySelectorAll('.chat-photo-view').length })"

def fit_problems(v, thumb):
    """what is wrong with the enlarged picture, against the page's own numbers; [] when it is right"""
    bad = []
    if not v or not v["f"]: return ["no image drawn: %s" % (v and (v["nat"], v["loaded"]))]
    f, p = v["f"], v["pad"]
    availw, availh = v["vw"] - p["l"] - p["r"], v["vh"] - p["t"] - p["b"]
    if f["l"] < p["l"] - 1 or f["t"] < p["t"] - 1 or f["l"] + f["w"] > v["vw"] - p["r"] + 1 or f["t"] + f["h"] > v["vh"] - p["b"] + 1:
        bad.append("outside the safe box %s" % {k: round(f[k], 1) for k in f})
    if not (abs(f["w"] - availw) <= 1.5 or abs(f["h"] - availh) <= 1.5):
        bad.append("not the largest that fits: %.0fx%.0f in %.0fx%.0f" % (f["w"], f["h"], availw, availh))
    ar, nar = f["w"] / f["h"], v["nat"][0] / v["nat"][1]
    if abs(ar - nar) / nar > .01: bad.append("aspect %.3f vs natural %.3f" % (ar, nar))
    factor = max(1.0, min(availw / thumb["w"], availh / thumb["h"]) * .9)
    if f["w"] < thumb["w"] * factor or f["h"] < thumb["h"] * factor:
        bad.append("smaller than the thumbnail x%.2f: %.0fx%.0f vs %.0fx%.0f" % (factor, f["w"], f["h"], thumb["w"], thumb["h"]))
    return bad

def render_again(pg, code, msgs):
    """a snapshot of the room document that changes nothing the picture shows: a typing flag and somebody's heartbeat"""
    import time
    put_messages(pg, code, msgs, extra={"typing": {ALEX: int(time.time() * 1000)}})

def run_surface(pg, tag, surf, errs):
    res = []
    def c(n, cond, info=""): res.append(("%s / %s: %s" % (tag, surf, n), cond, info))
    msgs = fix_ts(photo_msgs())
    root, code = open_surface(pg, surf, msgs)
    n = pg.evaluate("(r)=>document.querySelectorAll(r + ' .vroom-chat-photo').length", root)
    c("the chat draws its %d pictures" % len(ORDER), n == len(ORDER), n)
    if n != len(ORDER): return res
    # (1)-(3) each loaded picture: a real touch opens it, as large as it can be, on top
    opens, sizes, tops, unders = [], [], [], []
    for kind in ["land", "port", "small", "old", "own"]:
        f = nth_fig(pg, root, ORDER.index(kind))
        under = pg.evaluate(UNDER, [f["x"], f["y"]]); unders.append((kind, under))
        close_all(pg); tap(pg, f["x"], f["y"]); v = pg.evaluate(VIEW2)
        if not v: opens.append((kind, "no viewer; the tap landed on " + str(under))); continue
        pg.wait_for_timeout(300); v = pg.evaluate(VIEW2)
        pr = fit_problems(v, f)
        if pr: sizes.append((kind, pr))
        if not v["onTop"]: tops.append((kind, v["topCls"]))
        if v["n"] != 1: opens.append((kind, "%d viewers" % v["n"]))
        close_all(pg)
    c("(1) a touch on each picture (land, port, small, old, own) opens the viewer", not opens, opens)
    c("(1b) the touch lands on the picture, not a layer over it (under the finger: %s)" % (unders[0][1][:30] if unders else ""), all("vroom-chat-photo" in u or u == "IMG" for _, u in unders) or all(u.startswith("IMG") for _, u in unders), unders)
    c("(2) enlarged: inside the safe box, the largest that fits, true aspect, never smaller than the thumbnail", not sizes, sizes)
    c("(3) the viewer is the top-most element at the screen's middle (over the %s)" % ("chat sheet" if surf == "sheet" else "chat"), not tops, tops)
    # (4) the ways out, and nothing reaches the chat under
    way = {}
    def fresh():
        close_all(pg); f = nth_fig(pg, root, 0); tap(pg, f["x"], f["y"]); pg.wait_for_timeout(250); return f
    f = fresh(); v = pg.evaluate(VIEW2)
    if v:
        tap(pg, 12, v["vh"] - 12); pg.wait_for_timeout(250); way["tap anywhere (a corner)"] = pg.evaluate(PICKER)
        fresh(); v = pg.evaluate(VIEW2)
        way["x is 44px"] = bool(v and v["x"] and v["x"]["w"] >= 44 and v["x"]["h"] >= 44)
        if v and v["x"]: tap(pg, v["x"]["cx"], v["x"]["cy"]); pg.wait_for_timeout(100); way["button"] = pg.evaluate(PICKER)
        fresh(); pg.keyboard.press("Escape"); pg.wait_for_timeout(150); way["Escape"] = pg.evaluate(PICKER)
        fresh(); v = pg.evaluate(VIEW2)
        if v: drag(pg, v["vw"] / 2, v["vh"] / 2 - 40, v["vw"] / 2, v["vh"] / 2 + 260); way["swipe down"] = pg.evaluate(PICKER)
    bad = {k: x for k, x in way.items() if x is not True and not (isinstance(x, dict) and x["views"] == 0 and x["picker"] == 0 and x["picking"] == 0)}
    c("(4) a tap anywhere, the 44px button, Escape and a swipe down each close it, and none reaches the chat under (no picker, no 2nd viewer)",
      len(way) == 5 and not bad, {"way": way, "bad": bad})
    # (5) nothing behind it moves
    close_all(pg); f = nth_fig(pg, root, 0); before = pg.evaluate(STILL, root); tap(pg, f["x"], f["y"]); pg.wait_for_timeout(250)
    v = pg.evaluate(VIEW2)
    if v:
        drag(pg, v["vw"] / 2, v["vh"] / 2, v["vw"] / 2, v["vh"] / 2 - 160, steps=8)
        drag(pg, v["vw"] / 2 - 100, v["vh"] / 2, v["vw"] / 2 + 100, v["vh"] / 2, steps=8)
        pg.mouse.move(v["vw"] / 2, v["vh"] / 2); pg.mouse.wheel(0, 400); pg.wait_for_timeout(250)
    after = pg.evaluate(STILL, root); stillv = pg.evaluate(VIEW2)
    c("(5) a swipe up, a swipe across and a wheel over it move neither the page nor the chat's list nor the sheet, and do not close it",
      bool(v) and before == after and bool(stillv), {"before": before, "after": after, "open": bool(stillv)})
    # (6) a screen change clears it
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(500)
    c("(6) a screen change removes the viewer", pg.evaluate("()=>document.querySelectorAll('.chat-photo-view').length") == 0)
    pg.evaluate("()=>{ try{ closeRoomChatSheet(); }catch(e){} try{ closeChatDock(); }catch(e){} showHome(); }"); pg.wait_for_timeout(400)
    return res

def run_states(pg, tag, surf, errs):
    """the states a picture can be in, on one surface (the code is one function; the surfaces differ in host only)"""
    res = []
    def c(n, cond, info=""): res.append(("%s / %s: %s" % (tag, surf, n), cond, info))
    msgs = fix_ts(photo_msgs())
    root, code = open_surface(pg, surf, msgs)
    # a picture still loading: the viewer opens and fills when the picture lands
    import time
    pg.evaluate("(d)=>{ if(!window.__lci) window.__lci = loadChatImage; window.loadChatImage = id => id === 'img-slow' ? new Promise(r => setTimeout(() => r(d), 6000)) : window.__lci(id); }", IMG["slow"])
    slow = fix_ts(photo_msgs()) + [msg(7, ALEX, "Alex", "slow", w=500, h=300)]
    if surf == "nova": slow[-1]["key"] = "nova"
    put_messages(pg, code, slow)
    if surf == "nova": pg.evaluate("(ms)=>{ ms.forEach(m => { m.key = 'nova'; m.name = 'Nova'; novaAppend(m); }); novaListeners.forEach(f => f(novaPanelData())); }", slow[-1:]);
    pg.wait_for_timeout(500)
    n = pg.evaluate("(r)=>document.querySelectorAll(r + ' .vroom-chat-photo').length", root)
    f = nth_fig(pg, root, n - 1)
    close_all(pg); tap(pg, f["x"], f["y"]); pg.wait_for_timeout(150); v = pg.evaluate(VIEW2)
    c("(7a) a picture still loading: the viewer opens at once, waiting", bool(v) and v["wait"] and not v["loaded"], v and (v["wait"], v["loaded"]))
    pg.wait_for_timeout(6500); v = pg.evaluate(VIEW2)
    c("(7a) ...and shows the picture when it lands, the largest that fits", bool(v) and v["loaded"] and not v["wait"] and not fit_problems(v, f), v and fit_problems(v, f))
    close_all(pg)
    # a picture that is gone: nothing opens, nothing throws
    e0 = len(errs); f = nth_fig(pg, root, ORDER.index("nope")); close_all(pg); tap(pg, f["x"], f["y"])
    c("(7b) a picture that is gone (\"no longer available\") opens nothing and raises nothing",
      pg.evaluate("()=>document.querySelectorAll('.chat-photo-view').length") == 0 and len(errs) == e0)
    # a tap that lands while the list is re-rendered
    f = nth_fig(pg, root, 0)
    pg.evaluate("(r)=>{ window.__fig0 = document.querySelector(r + ' .vroom-chat-photo'); window.__top0 = document.querySelector(r + ' .vroom-chat-list').scrollTop; }", root)
    close_all(pg)
    touch(pg, f["x"], f["y"], hold=60, between=lambda: (render_again(pg, code, slow) if surf != "nova" else pg.evaluate("()=>novaListeners.forEach(f => f(novaPanelData()))"), pg.wait_for_timeout(350)))
    v = pg.evaluate(VIEW2)
    c("(7c) a touch that lands before a re-render of the list and lifts after it still opens the viewer", bool(v), None)
    close_all(pg)
    st = pg.evaluate("""(r)=>{ const f = document.querySelector(r + ' .vroom-chat-photo'); return { same: f === window.__fig0, loading: f.classList.contains('is-loading'),
      top: document.querySelector(r + ' .vroom-chat-list').scrollTop, top0: window.__top0 }; }""", root)
    c("(7d) a re-render that changes nothing leaves the picture's own node (no new node, no loading shimmer) and the scroll place", st["same"] and not st["loading"] and abs(st["top"] - st["top0"]) <= 2, st)
    # the keyboard's state: the box focused (its soft keyboard is phone-only; the focus and the tap are real)
    pg.evaluate("(r)=>{ const i = document.querySelector(r + ' .vroom-chat-input'); if(i) i.focus(); }", root)
    f = nth_fig(pg, root, 1); close_all(pg); tap(pg, f["x"], f["y"]); v = pg.evaluate(VIEW2)
    c("(7e) with the message box focused a touch still opens it, and it fits", bool(v) and not fit_problems(pg.evaluate(VIEW2), f), v and fit_problems(v, f))
    close_all(pg); pg.evaluate("()=>document.activeElement && document.activeElement.blur()")
    pg.evaluate("()=>{ if(window.__lci) window.loadChatImage = window.__lci; try{ closeChatDock(); }catch(e){} try{ closeRoomChatSheet(); }catch(e){} showHome(); }"); pg.wait_for_timeout(400)
    return res

def run_zoom(pg, tag, surf):
    res = []
    def c(n, cond, info=""): res.append(("%s / %s: %s" % (tag, surf, n), cond, info))
    root, code = open_surface(pg, surf, photo_msgs())
    f = nth_fig(pg, root, 0); close_all(pg); tap(pg, f["x"], f["y"]); pg.wait_for_timeout(250)
    v = pg.evaluate(VIEW2)
    if not v: c("(8) opened for the zoom checks", False); return res
    scale = lambda: float(re.search(r"scale\(([\d.]+)\)", pg.evaluate("()=>{ const b = document.querySelector('.chat-photo-view-box'); return b ? b.style.transform : 'scale(1)'; }") or "scale(1)").group(1))
    cx, cy = v["vw"] / 2, v["vh"] / 2
    for attempt in range(3):   # a double tap is two CDP calls apart; on a machine loaded past the 300ms window a try is a single tap and closes: try again
        double_tap(pg, cx + 30, cy + 10)
        s1 = scale(); open1 = bool(pg.evaluate(VIEW2))
        if open1 and s1 > 1.5: break
        close_all(pg); f = nth_fig(pg, root, 0); tap(pg, f["x"], f["y"]); pg.wait_for_timeout(250)
    c("(8a) a double tap zooms in (and does not close)", open1 and s1 > 1.5, {"scale": s1, "open": open1})
    double_tap(pg, cx, cy)
    c("(8b) a second double tap zooms back out", bool(pg.evaluate(VIEW2)) and scale() == 1.0, scale())
    pinch_out(pg, cx, cy)
    s2 = scale()
    c("(8c) a pinch out zooms in", bool(pg.evaluate(VIEW2)) and s2 > 1.5, s2)
    close_all(pg)
    pg.evaluate("()=>{ try{ closeChatDock(); }catch(e){} try{ closeRoomChatSheet(); }catch(e){} showHome(); }"); pg.wait_for_timeout(400)
    return res

def run_dev(br, url, cls, dev, errs):
    tag = "%s, %s" % (dev[0], "Fire Code" if cls == "ifc" else "academy")
    out = []
    ctx, pg, got = boot(br, url, cls, dev, errs)
    flushed = [0]
    def flush():
        for r in out[flushed[0]:]: chk(*r)
        flushed[0] = len(out)
    out.append(("%s: the page is the class under test" % tag, got == cls, got))
    surfaces = ["friend", "lobby", "sheet"] if QUICK else SURFACES
    try:
        for surf in surfaces:
            print("  ...", tag, surf, flush=True)
            out += run_surface(pg, tag, surf, errs); flush()
        for surf in (["friend", "sheet"] if not QUICK else ["friend"]):
            out += run_states(pg, tag, surf, errs); flush()
        out += run_zoom(pg, tag, "friend"); flush()
    finally:
        ctx.close()
    return out

def main():
    srv, url = serve()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            errs = []
            combos = [(cls, dev) for dev in DEVS for cls in (["academy"] if QUICK else ["academy", "ifc"])]
            for cls, dev in combos:
                for attempt in range(3):
                    try:
                        n0 = len(errs); run_dev(br, url, cls, dev, errs); break
                    except Exception as e:
                        if attempt == 2 or not any(w in str(e) for w in ("crashed", "Target", "closed", "Timeout")): raise
                        print("  (retry: %s)" % str(e).split("\n")[0][:80], flush=True); del errs[n0:]
            chk("(9) no page errors", not errs, errs[:6])
            br.close()
    finally:
        srv.shutdown()
    print("\nALL PASS" if ok else "\nSOME FAILED"); sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
