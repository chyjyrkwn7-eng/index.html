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
PICS = {"land": (600, 400), "port": (300, 520), "small": (120, 90), "old": (640, 360), "gone": (200, 200), "slow": (500, 300)}
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
  const imgs = Object.keys(cfg.imgs);
  return Promise.all(imgs.map(k => fbDb.collection('vrooms').doc('img-' + k).set({ kind: 'chatimg', data: cfg.imgs[k], by: cfg.alex, at: Date.now() })))
    .then(() => { showHome(); return window.NOVA_CLASS; }); }"""

DEVS = [("Pro Max", 440, 956, 59, 34, "phone"), ("iPad 11", 834, 1194, 24, 20, "tablet")]
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")

def boot(br, url, cls, dev, errs):
    name, W, H, it, ib, kind = dev
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True,
                         user_agent=UA if kind == "phone" else UA_PAD)
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
    return [{"id": "t0", "key": key, "name": name, "text": "look at this", "ts": 0},
            msg(1, key, name, "land", w=600, h=400), msg(2, key, name, "port", w=300, h=520), msg(3, key, name, "small", w=120, h=90),
            msg(4, key, name, "old"), msg(5, key, name, "gone", w=200, h=200)]

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
    """the i-th photo in the list, scrolled to the middle of its list, with its centre"""
    return pg.evaluate("""([root, i])=>{ const f = [...document.querySelectorAll(root + ' .vroom-chat-photo')][i]; if(!f) return null;
      f.scrollIntoView({block:'center'}); const r = f.getBoundingClientRect();
      return { x: r.left + r.width/2, y: r.top + r.height/2, w: r.width, h: r.height }; }""", [root, i])

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
