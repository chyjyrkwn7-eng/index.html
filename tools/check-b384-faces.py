#!/usr/bin/env python3
"""Build 384 r11: everyone is shown wearing their own character of the class you are in.
Madison: "In the friends chat, if I look at them while in one class, I'll see what they have selected as the placeholder in the
class I'm in. I guess it would be whatever class they are currently in and whatever character that is, so it may change constantly."
One account is two classes, each with its own character. Everything social carried only the academy's, and Fire Code re-skins an
academy id as its own look, so a friend in the academy's Marksman showed in Fire Code as a Hazmat they never chose or unlocked there.

Against an in-memory Firestore (the CDN is blocked here), one page in the academy and one in Fire Code, each a real boot with the
account's two copies on the device. Five people, as the class holds them:
  ALEX  academy "marksman", Fire Code "astronaut"   (a board row, and a presence beat that says both)
  KIM   academy "astronaut", no Fire Code character (a row, a beat with no `fv`: never opened Fire Code on a build that says)
  PAT   academy "alien", an OLD-format person       (a row and nothing else: no beat, no new field anywhere)
  ZED   academy "alien", Fire Code "grizzly"        (only the chat's entry says it: no row, no beat)
  DEE   a friend in Fire Code alone                 (no row; a beat with a name and both characters)
and, read off the .rank-avatar spans' data-char (avatarSpanFor sets it), in BOTH classes:
  1  the chat roster, the Members list;
  2  the chat's Friends tab, Manage friends, a friend's chat header, a person's card;
  3  the Virtual Room lobby;
  4  your own entry carries both characters (chat entry, presence beat), and only when the account is in Fire Code;
  5  your own face in your own class is your own character.
Academy: each is drawn as their academy character, as before. Fire Code: as their Fire Code character; one that is not known is the
class's starter (classDefaultCharacter), never the academy's re-skinned.
Run:  python3 tools/check-b384-faces.py   (--against OLD/index.html must FAIL)"""
import functools, http.server, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
_VR = open(os.path.join(HERE, "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)

OLD = None; OLD_BUILD = None
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    OLD_BUILD = re.search(r'const APP_BUILD = "([^"]+)"', OLD).group(1)

ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:400]), flush=True)

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port

ME, ALEX, KIM, PAT, ZED, DEE = "me0000000001", "alex000000002", "kim0000000003", "pat0000000004", "zed0000000005", "dee0000000006"
ME_ACAD, ME_IFC = "grizzly", "alien"
# what the account's own two copies say
ACADEMY = {"firstName": "Madison", "avatarChar": ME_ACAD, "onboardingComplete": True, "tourRev": 999, "leaderboardOptIn": True,
           "publicId": ME, "classes": ["academy", "ifc"], "lastModified": 1790500000000, "novaMet": 99, "hiveMoved384": True,
           "novaHeard": {"@recap": 99991231}, "seenClassTip": True}
IFCSTORE = {"firstName": "Madison", "avatarChar": ME_IFC, "onboardingComplete": True, "tourRev": 999, "leaderboardOptIn": True,
            "publicId": ME, "lastModified": 1790500000000, "novaMet": 99, "novaHeard": {"@recap": 99991231}, "seenClassTip": True}
ROWS = [{"pub": ALEX, "firstName": "Alex", "avatarChar": "marksman"},
        {"pub": KIM, "firstName": "Kim", "avatarChar": "astronaut"},
        {"pub": PAT, "firstName": "Pat", "avatarChar": "alien"}]
# the presence document: ALEX says both, KIM says only the academy's, DEE is in Fire Code alone, PAT and ZED have no beat
NOW = 4102444800000
PRESENCE = {"kind": "presence",
            "p": {ALEX: NOW, KIM: NOW, DEE: NOW},
            "c": {ALEX: {"k": "academy,ifc", "n": "Alex", "v": "marksman", "fv": "astronaut"},
                  KIM: {"k": "academy", "n": "Kim", "v": "astronaut"},
                  DEE: {"k": "ifc", "n": "Dee", "v": "grizzly", "fv": "alien"}}}
# [name] -> (the character drawn in the academy, in Fire Code); the default is read off the page (classDefaultCharacter)
EXPECT = {"Alex": ("marksman", "astronaut"), "Kim": ("astronaut", "DEFAULT"), "Pat": ("alien", "DEFAULT"), "Zed": ("alien", "grizzly")}

SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked',"
        "'class26e.savecode.card','class26e.getstarted','class26e.penal55124.seen','class26e.penal124256.seen'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1');")
SEEN_IFC = ("['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card',"
            "'class26e.ifc.getstarted','class26e.ifc.unithold.tip'].forEach(k=>localStorage.setItem(k,'1'));")
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
  leaderboardRows = cfg.rows.map(r => Object.assign({ facc: [], freq: [], level: 3, badges: 0, hundos: 0 }, r));
  store.friendsIn = cfg.friends; store.chats = [];
  return fbDb.collection('vrooms').doc('presence-v1').set(cfg.presence).then(() => { attachPresence(); showHome(); return window.NOVA_CLASS; }); }"""

CHAR_OF = """const charOf = el => { const a = el && (el.querySelector('.rank-avatar') || el); return a && a.dataset ? (a.dataset.char || null) : null; };"""

def boot(br, url, cls, errs):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.add_init_script(FAKE); ctx.add_init_script(init_js(cls))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(cls + ": " + str(e)[:160]))
    if OLD is not None:
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
                 body=json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""})))
        pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=OLD))
    pg.goto(url); pg.wait_for_timeout(4000)
    for _ in range(40):
        if pg.evaluate("()=>typeof store === 'object' && !!store && typeof __useFake === 'function' && window.NOVA_CLASS !== undefined"): break
        pg.wait_for_timeout(500)
    got = pg.evaluate(SETUP, {"me": ME, "rows": ROWS, "friends": [ALEX, KIM, PAT, DEE], "presence": PRESENCE})
    pg.wait_for_timeout(500)
    return ctx, pg, got

def expect_for(cls, default):
    i = 0 if cls == "academy" else 1
    return {n: (default if v[i] == "DEFAULT" else v[i]) for n, v in EXPECT.items()}

def run_class(br, url, cls):
    errs = []
    ctx, pg, got = boot(br, url, cls, errs)
    try:
        print("\n== %s page (NOVA_CLASS=%s)" % (cls, got), flush=True)
        chk("%s: the page is the class under test" % cls, got == cls, got)
        default = pg.evaluate("()=>classDefaultCharacter()")
        want = expect_for(cls, default)
        own = ME_ACAD if cls == "academy" else ME_IFC

        # ---- 1. a group chat: the roster and the Members list
        code = "CHATFACES-" + cls.upper()
        pg.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).set({ kind:'chat', createdAt: Date.now(), chatMessages: [], typing: {},
            participants: {
              [x.me]:   { name:'Madison', avatarChar:'grizzly', joinedAt: 1, seen: Date.now() },
              [x.alex]: { name:'Alex', avatarChar:'marksman', joinedAt: 2, seen: Date.now() },
              [x.kim]:  { name:'Kim', avatarChar:'astronaut', joinedAt: 3, seen: Date.now() },
              [x.pat]:  { name:'Pat', avatarChar:'alien', joinedAt: 4, seen: Date.now() },
              [x.zed]:  { name:'Zed', avatarChar:'alien', avatarCharIfc:'grizzly', joinedAt: 5, seen: Date.now() } } })""",
                    {"code": code, "me": ME, "alex": ALEX, "kim": KIM, "pat": PAT, "zed": ZED})
        pg.evaluate("(c)=>{ openChatDock(); return joinChatRoom(c); }", code)
        pg.wait_for_timeout(1500)
        roster = pg.evaluate("""()=>{ %s
          return [...document.querySelectorAll('#chatdock-roomwho .chatdock-who')].map(c => ({ n: c.querySelector('.chatdock-who-name').textContent, c: charOf(c.querySelector('.chatdock-who-art')), me: c.classList.contains('is-me') })); }""" % CHAR_OF)
        chk("%s: the roster lists everybody (%s)" % (cls, ", ".join(r["n"] for r in roster)), len(roster) == 5, roster)
        for n, c in want.items():
            r = next((x for x in roster if x["n"] == n), None)
            chk("%s: roster draws %s as %s" % (cls, n, c), bool(r) and r["c"] == c, r)
        me = next((x for x in roster if x["me"]), None)
        chk("%s: roster draws you as your own %s character (%s)" % (cls, cls, own), bool(me) and me["c"] == own, me)
        pg.evaluate("()=>document.querySelector('#chatdock-roomwho .chatdock-who-more').click()")
        pg.wait_for_timeout(500)
        mem = pg.evaluate("""()=>{ %s
          return [...document.querySelectorAll('.chat-members .chat-member')].map(r => ({ n: (r.querySelector('.chat-member-name')||{}).textContent || '', c: charOf(r.querySelector('.chat-member-art')) })); }""" % CHAR_OF)
        for n, c in want.items():
            r = next((x for x in mem if x["n"].startswith(n)), None)
            chk("%s: Members list draws %s as %s" % (cls, n, c), bool(r) and r["c"] == c, mem)
        r = next((x for x in mem if x["n"].endswith("(you)")), None)
        chk("%s: Members list draws you as %s" % (cls, own), bool(r) and r["c"] == own, mem)
        pg.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(o=>o.remove()); closeChatRoom(); }")
        pg.wait_for_timeout(300)

        # ---- 2. the Friends tab, Manage friends, a friend's chat, a person's card
        pg.evaluate("()=>{ chatDockTab = 'friends'; openChatDock(); syncChatDock(); }")
        pg.wait_for_timeout(1200)
        tab = pg.evaluate("""()=>{ %s
          return [...document.querySelectorAll('.chatdock-chatrow.is-friend')].map(r => ({ n: (r.querySelector('.chatdock-chatrow-name')||{}).textContent || '', c: charOf(r.querySelector('.chatdock-chatrow-avatar')) })); }""" % CHAR_OF)
        fwant = dict(want); fwant.pop("Zed")
        fwant["Dee"] = "grizzly" if cls == "academy" else "alien"   # a friend in Fire Code alone: their beat's two characters
        for n, c in fwant.items():
            r = next((x for x in tab if x["n"] == n), None)
            chk("%s: the chat's Friends tab draws %s as %s" % (cls, n, c), bool(r) and r["c"] == c, tab)
        pg.evaluate("()=>{ closeChatDock && closeChatDock(); }")
        pg.evaluate("()=>showFriends()"); pg.wait_for_timeout(1200)
        mf = pg.evaluate("""()=>{ %s
          return [...document.querySelectorAll('.screen-friends .friend-row')].map(r => ({ n: (r.querySelector('.friend-row-name')||{}).textContent || '', c: charOf(r.querySelector('.friend-row-art')) })); }""" % CHAR_OF)
        for n, c in fwant.items():
            r = next((x for x in mf if x["n"].startswith(n)), None)
            chk("%s: Manage friends draws %s as %s" % (cls, n, c), bool(r) and r["c"] == c, mf)
        pg.evaluate("()=>{ chatDockTab='friends'; openChatDock(); openFriendChat(%s); }" % json.dumps(ALEX))
        pg.wait_for_timeout(1500)
        hd = pg.evaluate("""()=>{ %s const h = document.querySelector('.chatdock-friendhead-art'); return h ? charOf(h) : null; }""" % CHAR_OF)
        chk("%s: a friend's chat header draws Alex as %s" % (cls, want["Alex"]), hd == want["Alex"], hd)
        pg.evaluate("()=>{ try{ closeChatRoom(); }catch(e){} }")
        pg.evaluate("(x)=>{ openPersonSheet(Object.assign({ pub: x.pub, level: 3, badges: 0 }, x.row)); }", {"pub": ALEX, "row": ROWS[0]})
        pg.wait_for_timeout(700)
        card = pg.evaluate("""()=>{ %s const a = document.querySelector('.person-sheet-art'); return a ? charOf(a) : null; }""" % CHAR_OF)
        chk("%s: a person's card draws Alex as %s" % (cls, want["Alex"]), card == want["Alex"], card)
        pg.evaluate("()=>document.querySelectorAll('.person-sheet, .person-overlay, .invite-overlay').forEach(o=>o.remove())")

        # ---- 3. the Virtual Room lobby
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
        pg.evaluate("()=>createVirtualRoomLobby(['Identity Crimes'], null, 'race')")
        for _ in range(40):
            if pg.evaluate("()=>!!vroomCode"): break
            pg.wait_for_timeout(250)
        vc = pg.evaluate("()=>vroomCode")
        if vc:
            pg.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).update({
                ['participants.'+x.alex]: { name:'Alex', avatarChar:'marksman', avatarCharIfc:'astronaut', level:3, badges:0, joinedAt: Date.now()+1, seen: Date.now(), progress:0, finished:false, ready:false },
                ['participants.'+x.kim]:  { name:'Kim', avatarChar:'astronaut', level:3, badges:0, joinedAt: Date.now()+2, seen: Date.now(), progress:0, finished:false, ready:false } })""",
                        {"code": vc, "alex": ALEX, "kim": KIM})
            pg.wait_for_timeout(1500)
            lob = pg.evaluate("""()=>{ %s
              return [...document.querySelectorAll('.vroom-row')].map(r => ({ t: r.textContent, c: charOf(r.querySelector('.vroom-avatar')) })); }""" % CHAR_OF)
            for n in ("Alex", "Kim"):
                r = next((x for x in lob if n in x["t"]), None)
                chk("%s: the Virtual Room lobby draws %s as %s" % (cls, n, want[n]), bool(r) and r["c"] == want[n], lob)
            r = next((x for x in lob if "Madison" in x["t"] or "You" in x["t"]), None)
            chk("%s: the lobby draws you as %s" % (cls, own), bool(r) and r["c"] == own, lob)
        else:
            chk("%s: a Virtual Room lobby opened" % cls, False, "no vroomCode")

        # ---- 4. your own entry carries both, and says so only when the account is in Fire Code
        ent = pg.evaluate("()=>({ self: chatSelfEntry(), beat: presenceClassesValue(), card: socialCard() })")
        chk("%s: your chat entry carries the academy character (unchanged)" % cls, ent["self"].get("avatarChar") == ME_ACAD, ent["self"])
        chk("%s: ...and the Fire Code one (%s)" % (cls, ME_IFC), ent["self"].get("avatarCharIfc") == ME_IFC, ent["self"])
        chk("%s: the presence beat carries v (academy) and fv (Fire Code)" % cls, ent["beat"].get("v") == ME_ACAD and ent["beat"].get("fv") == ME_IFC, ent["beat"])
        chk("%s: your social card carries both" % cls, ent["card"].get("avatarChar") == ME_ACAD and ent["card"].get("avatarCharIfc") == ME_IFC, ent["card"])
        if cls == "academy":
            lone = pg.evaluate("()=>{ const k = store.classes; store.classes = ['academy']; try{ return { self: chatSelfEntry(), beat: presenceClassesValue() }; }finally{ store.classes = k; } }")
            chk("academy: an account not in Fire Code advertises no Fire Code character",
                "avatarCharIfc" not in lone["self"] and "fv" not in lone["beat"], lone)
        chk("%s: no page errors" % cls, not errs, errs[:3])
    finally:
        ctx.close()

def main():
    srv, url = serve()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            for cls in ("academy", "ifc"):
                for attempt in range(3):
                    try: run_class(br, url, cls); break
                    except Exception as e:
                        if attempt == 2 or not any(w in str(e) for w in ("crashed", "Target", "closed", "Timeout")): raise
                        print("  (retry: %s)" % str(e).split("\n")[0][:80], flush=True)
            br.close()
    finally:
        srv.shutdown()
    print("\nALL GOOD" if ok else "\nFAILED"); sys.exit(0 if ok else 1)
main()
