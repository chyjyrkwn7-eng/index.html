#!/usr/bin/env python3
"""Build 384 r22: a friend is shown as they are in the class they used LAST (Madison, his Friends list in Fire Code: ten friends,
eight of them the grey ghost).
  "on my friends list, maybe it will just be the character of the class they are in currently or the class they were in last?
   Same for the banner? ... in the friends list you also see their levels, and if you click their profile you also see their rank and
   stats and everything. ... some of the accounts I'm looking at have banners set from academy but have the corresponding IFC one on
   somehow? That should not be possible."
r11 drew everybody as their character OF THE CLASS YOU ARE IN and knew a friend's Fire Code character only from their own beat, which a
build from before r11 never wrote: the ghost. And a banner id is one set shared by both classes, so an academy banner showed in Fire
Code as the Fire Code twin of the same id. Now the presence beat says `lc` (the class it was written from) beside `b` / `fb` (that
class's banner id) and `lv`+`bg` / `flv`+`fbg` (its level and badges), and every screen draws a person as ONE class: that class's
character, in that class's art, its banner in its art, its level and rank.

Against an in-memory Firestore (the CDN is blocked here), one page in the academy and one in Fire Code, each a real boot. Seven friends
in every state a friend can be in:
  ACAD   academy only                      (a row; a beat that says lc academy)
  FIRE   Fire Code only                    (no row; a beat that says lc ifc)
  BOTHA  both, last class the academy      (a row; a beat with both classes' character, banner, level)
  BOTHI  both, last class Fire Code        (a row; a beat with both; the academy banner and the Fire Code one are different ids)
  BOTHI2 both, last class Fire Code, whose Fire Code banner is the default (the academy row holds a banner Fire Code never unlocked)
  NOLC   both, a beat with no `lc` (a build from before this one)
  OLD    an academy row and nothing else    (no beat at all: the oldest builds)
  NONE   a friend nothing says anything about
and, read off the DOM by shape (data-char / data-art on the avatar span and its svg, data-art and the bnr-<id> class on a banner, the
numbers in the row): no ghost where a character is known; the art drawn is the class the rule picks, on BOTH pages; the banner is the
one that class holds and in that class's art; the level and rank are that class's (Fire Code's board row once the Leaderboard has read
it, else the beat's); the beat writes once, holds no sync code, merges (the other class's fields stay) and is small.
Also: every character drawn in both classes' art on both pages (the right kind each, the page's own drawing unchanged, nothing left
lent behind), and every redrawn banner.
Run:  python3 tools/check-b384-lastclass.py   (--against OLD/index.html must FAIL)"""
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
    print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:420]), flush=True)

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port

ME = "me0000000001"
ACAD, FIRE, BOTHA, BOTHI, BOTHI2, NOLC, OLD_, NONE = ("acad0000000a", "fire0000000b", "botha000000c", "bothi000000d", "bothi200000e",
                                                        "nolc0000000f", "old00000000g", "none0000000h")
NAMES = {ACAD: "Acad", FIRE: "Fire", BOTHA: "BothA", BOTHI: "BothI", BOTHI2: "BothIb", NOLC: "NoLc", OLD_: "Old", NONE: None}
ME_ACAD, ME_IFC = "grizzly", "alien"
ACADEMY = {"firstName": "Madison", "avatarChar": ME_ACAD, "onboardingComplete": True, "tourRev": 999, "leaderboardOptIn": True,
           "publicId": ME, "classes": ["academy", "ifc"], "lastModified": 1790500000000, "novaMet": 99, "hiveMoved384": True,
           "novaHeard": {"@recap": 99991231}, "seenClassTip": True, "banner": ""}
IFCSTORE = {"firstName": "Madison", "avatarChar": ME_IFC, "onboardingComplete": True, "tourRev": 999, "leaderboardOptIn": True,
            "publicId": ME, "lastModified": 1790500000000, "novaMet": 99, "novaHeard": {"@recap": 99991231}, "seenClassTip": True, "banner": ""}
def row(pub, ch, lvl, badges, banner):
    return {"pub": pub, "firstName": NAMES[pub], "avatarChar": ch, "level": lvl, "badges": badges, "banner": banner, "facc": [], "freq": [], "hundos": 3, "xp": 4000, "correct": 800}
# the academy's board rows: BOTHI's and BOTHI2's hold the academy banner "tests500", which Fire Code (their last class) never unlocked
ROWS = [row(ACAD, "marksman", 20, 2, "tests250"), row(BOTHA, "marksman", 40, 5, "tests250"), row(BOTHI, "detective", 50, 6, "tests500"),
        row(BOTHI2, "detective", 50, 6, "tests500"), row(NOLC, "marksman", 30, 3, "tests250"), row(OLD_, "alien", 11, 1, "")]
NOW = 4102444800000
PRESENCE = {"kind": "presence", "p": {k: NOW for k in (ACAD, FIRE, BOTHA, BOTHI, BOTHI2, NOLC)},
            "c": {ACAD: {"k": "academy", "n": "Acad", "v": "marksman", "lc": "academy", "b": "tests250", "lv": 20, "bg": 2},
                  FIRE: {"k": "ifc", "n": "Fire", "v": "grizzly", "fv": "alien", "lc": "ifc", "fb": "hundos100", "flv": 12, "fbg": 2},
                  BOTHA: {"k": "academy,ifc", "n": "BothA", "v": "marksman", "fv": "astronaut", "lc": "academy", "b": "tests250", "fb": "tests100",
                          "lv": 40, "bg": 5, "flv": 9, "fbg": 1},
                  BOTHI: {"k": "academy,ifc", "n": "BothI", "v": "detective", "fv": "hacker", "lc": "ifc", "b": "tests500", "fb": "tests250",
                          "lv": 50, "bg": 6, "flv": 7, "fbg": 1},
                  BOTHI2: {"k": "academy,ifc", "n": "BothIb", "v": "detective", "fv": "clown", "lc": "ifc", "b": "tests500", "fb": "", "lv": 50, "bg": 6},
                  NOLC: {"k": "academy,ifc", "n": "NoLc", "v": "marksman", "fv": "clown"}}}
FRIENDS = [ACAD, FIRE, BOTHA, BOTHI, BOTHI2, NOLC, OLD_, NONE]

# who is drawn how, by page: pub -> (character, class whose art, level or None (left out), banner id or "" (the theme), shown class)
# a character and a class that nothing contradicts; "DEFAULT" is the page's starter, read off the page
EXPECT = {
    "academy": {ACAD: ("marksman", "academy", 20, "tests250"), FIRE: ("alien", "ifc", 12, "hundos100"),
                BOTHA: ("marksman", "academy", 40, "tests250"), BOTHI: ("hacker", "ifc", 7, "tests250"),
                BOTHI2: ("clown", "ifc", None, ""), NOLC: ("marksman", "academy", 30, "tests250"),
                OLD_: ("alien", "academy", 11, ""), NONE: ("DEFAULT", "academy", None, "")},
    "ifc": {ACAD: ("marksman", "academy", 20, "tests250"), FIRE: ("alien", "ifc", 12, "hundos100"),
            BOTHA: ("marksman", "academy", 40, "tests250"), BOTHI: ("hacker", "ifc", 7, "tests250"),
            BOTHI2: ("clown", "ifc", None, ""), NOLC: ("clown", "ifc", None, ""),
            OLD_: ("alien", "academy", 11, ""), NONE: ("DEFAULT", "ifc", None, "")}}

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
  leaderboardRows = cfg.rows.map(r => Object.assign({}, r));
  store.friendsIn = cfg.friends; store.chats = [];
  return fbDb.collection('vrooms').doc('presence-v1').set(cfg.presence).then(() => { attachPresence(); showHome(); return window.NOVA_CLASS; }); }"""

def boot(br, url, cls, errs, vw=440, vh=956):
    ctx = br.new_context(viewport={"width": vw, "height": vh}, has_touch=True)
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
    got = pg.evaluate(SETUP, {"me": ME, "rows": ROWS, "friends": FRIENDS, "presence": PRESENCE})
    pg.wait_for_timeout(700)
    return ctx, pg, got

READ_ROWS = """()=>[...document.querySelectorAll('.screen-friends .friend-row')].map(r => {
  const a = r.querySelector('.friend-row-art .rank-avatar'), svg = a && a.querySelector('svg.avatarchar-svg');
  const lv = (r.querySelector('.friend-row-lvl')||{}).textContent || '', rk = (r.querySelector('.friend-row-rank')||{}).textContent || '';
  return { n: (r.querySelector('.friend-row-name')||{}).textContent || '', c: a ? (a.dataset.char || null) : null, art: a ? (a.dataset.art || null) : null,
           sart: svg ? svg.getAttribute('data-art') : null, lvl: lv, rank: rk, mark: (r.querySelector('.class-mark')||{}).dataset ? (r.querySelector('.class-mark').dataset.cls) : null }; })"""
READ_TAB = """()=>[...document.querySelectorAll('.chatdock-chatrow.is-friend')].map(r => {
  const a = r.querySelector('.chatdock-chatrow-avatar .rank-avatar'), svg = a && a.querySelector('svg.avatarchar-svg');
  return { n: (r.querySelector('.chatdock-chatrow-name')||{}).textContent || '', c: a ? (a.dataset.char || null) : null, art: a ? (a.dataset.art || null) : null,
           sart: svg ? svg.getAttribute('data-art') : null }; })"""

def level_of(txt):
    m = re.search(r"Level (\d+)", txt or "")
    return int(m.group(1)) if m else None

def run_class(br, url, cls, shared):
    errs = []
    ctx, pg, got = boot(br, url, cls, errs)
    try:
        print("\n== %s page (NOVA_CLASS=%s)" % (cls, got), flush=True)
        chk("%s: the page is the class under test" % cls, got == cls, got)
        default = pg.evaluate("()=>classDefaultCharacter()")
        want = {}
        for pub, (ch, art, lvl, ban) in EXPECT[cls].items():
            want[pub] = (default if ch == "DEFAULT" else ch, art, lvl, ban)

        # ---- 1. Manage friends: face, art, level, rank, class mark
        pg.evaluate("()=>showFriends()"); pg.wait_for_timeout(1500)
        mf = [x for x in pg.evaluate(READ_ROWS) if x["n"] != "Nova"]
        chk("%s: Manage friends lists every friend (%d)" % (cls, len(mf)), len(mf) == len(FRIENDS), [x["n"] for x in mf])
        for pub, (ch, art, lvl, ban) in want.items():
            nm = NAMES[pub] or "Friend"
            r = next((x for x in mf if x["n"] == nm), None)
            chk("%s: Manage friends draws %s as %s in %s art" % (cls, nm, ch, art), bool(r) and r["c"] == ch and r["art"] == art and r["sart"] == art, r)
            if pub == NONE: continue
            if lvl is None:
                chk("%s: ...no level made up for %s (the class's name instead)" % (cls, nm), bool(r) and level_of(r["lvl"]) is None and not r["rank"], r)
            else:
                chk("%s: ...%s is Level %d, the level of the class shown" % (cls, nm, lvl), bool(r) and level_of(r["lvl"]) == lvl, r)
        # the rank is the class shown's: BOTHI is Level 50 + 6 badges in the academy, Level 7 + 1 in Fire Code
        rk = pg.evaluate("""()=>({ acad: (rankOfEntry({level:50,badges:6})||''), ifc: (rankOfEntry({level:7,badges:1})||''),
          names: Object.assign({}, RANK_DISPLAY_NAME) })""")
        r = next((x for x in mf if x["n"] == "BothI"), None)
        chk("%s: the fixture's two classes rank differently (so the next check can tell)" % cls, rk["acad"] != rk["ifc"], rk)
        want_rank = rk["names"].get(rk["ifc"], "") if rk["ifc"] else ""
        chk("%s: BothI's rank word is Fire Code's (their last class), not the academy's" % cls, bool(r) and r["rank"] == want_rank, [r, rk])
        r = next((x for x in mf if x["n"] == "BothA"), None)
        chk("%s: a person in both classes carries the quiet class mark of the class shown" % cls, bool(r) and r["mark"] == "academy", r)
        r = next((x for x in mf if x["n"] == "BothI"), None)
        chk("%s: ...Fire Code's for a Fire Code last class" % cls, bool(r) and r["mark"] == "ifc", r)
        r = next((x for x in mf if x["n"] == "Acad"), None)
        chk("%s: ...and none for somebody in one class" % cls, bool(r) and r["mark"] is None, r)

        # ---- 2. no ghost where a character is known, and no placeholder starter where the academy's is
        starter_known = [x for x in mf if x["n"] != "Friend" and x["c"] == default and NAMES_BY_N.get(x["n"]) in (ACAD, BOTHA, BOTHI, NOLC)]
        chk("%s: nobody whose character is known is the placeholder" % cls, not starter_known, starter_known)

        # ---- 3. the chat's Friends tab
        pg.evaluate("()=>{ chatDockTab = 'friends'; openChatDock(); syncChatDock(); }"); pg.wait_for_timeout(1300)
        tab = pg.evaluate(READ_TAB)
        for pub, (ch, art, lvl, ban) in want.items():
            if pub == NONE: continue
            nm = NAMES[pub]
            r = next((x for x in tab if x["n"] == nm), None)
            chk("%s: the chat's Friends tab draws %s as %s in %s art" % (cls, nm, ch, art), bool(r) and r["c"] == ch and r["art"] == art and r["sart"] == art, r)
        pg.evaluate("()=>{ closeChatDock && closeChatDock(); }")

        # ---- 4. a person's card: the face, the banner and its art, the level
        for pub, (ch, art, lvl, ban) in want.items():
            if pub in (NONE,): continue
            nm = NAMES[pub]
            pg.evaluate("(p)=>{ document.querySelectorAll('.invite-overlay').forEach(o=>o.remove()); openPersonSheet(friendCardOf(p)); }", pub)
            pg.wait_for_timeout(450)
            card = pg.evaluate("""()=>{ const a = document.querySelector('.person-sheet-art .rank-avatar'); const svg = a && a.querySelector('svg.avatarchar-svg');
              const cov = document.querySelector('.person-card-cover .bnr'); const cl = cov ? [...cov.classList].find(c => /^bnr-/.test(c) && c !== 'bnr-theme') || null : null;
              return { c: a ? a.dataset.char : null, art: a ? a.dataset.art : null, sart: svg ? svg.getAttribute('data-art') : null,
                       banner: cl ? cl.slice(4) : '', bart: cov ? (cov.dataset.art || null) : null, theme: !!(cov && cov.classList.contains('bnr-theme')),
                       lvl: (document.querySelector('.person-card-level')||{}).textContent || '' }; }""")
            chk("%s: %s's card draws %s in %s art" % (cls, nm, ch, art), card["c"] == ch and card["art"] == art and card["sart"] == art, card)
            if ban:
                chk("%s: ...their banner is %s (the one that class holds), in %s art" % (cls, ban, art), card["banner"] == ban and card["bart"] == art, card)
            else:
                chk("%s: ...no banner they do not hold: their theme (not the other class's %s)" % (cls, "tests500"), card["theme"] and not card["banner"], card)
            if lvl is not None:
                chk("%s: ...Level %d" % (cls, lvl), level_of(card["lvl"]) == lvl, card)
            else:
                chk("%s: ...no level made up" % cls, level_of(card["lvl"]) is None, card)
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(o=>o.remove())")

        # ---- 5. the board of the class, once the Leaderboard has read it: its numbers win over the beat's
        if cls == "ifc":
            pg.evaluate("""(x)=>{ classBoardRows = [ { pub: x.bothi, firstName: 'BothI', avatarChar: 'hacker', level: 8, badges: 1, banner: 'tests250', hundos: 1 },
                                                      { pub: x.nolc, firstName: 'NoLc', avatarChar: 'clown', level: 15, badges: 2, banner: '' } ]; }""",
                        {"bothi": BOTHI, "nolc": NOLC})
            pg.evaluate("()=>showFriends()"); pg.wait_for_timeout(1000)
            mf2 = [x for x in pg.evaluate(READ_ROWS) if x["n"] != "Nova"]
            r = next((x for x in mf2 if x["n"] == "BothI"), None)
            chk("ifc: Fire Code's board row (once read) gives BothI's level, over the beat's", bool(r) and level_of(r["lvl"]) == 8, r)
            r = next((x for x in mf2 if x["n"] == "NoLc"), None)
            chk("ifc: ...and gives a person with no beat numbers theirs (Level 15)", bool(r) and level_of(r["lvl"]) == 15 and r["art"] == "ifc", r)
            r = next((x for x in mf2 if x["n"] == "BothA"), None)
            chk("ifc: ...while a person shown in the academy keeps the academy row's level", bool(r) and level_of(r["lvl"]) == 40, r)
            pg.evaluate("()=>{ classBoardRows = []; }")

        # ---- 6. a group chat roster
        code = "LASTCLASS-" + cls.upper()
        pg.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).set({ kind:'chat', createdAt: Date.now(), chatMessages: [], typing: {},
            participants: {
              [x.me]:    { name:'Madison', avatarChar:'grizzly', joinedAt: 1, seen: Date.now() },
              [x.bothi]: { name:'BothI', avatarChar:'detective', joinedAt: 2, seen: Date.now() },
              [x.botha]: { name:'BothA', avatarChar:'marksman', joinedAt: 3, seen: Date.now() },
              [x.old]:   { name:'Old', avatarChar:'alien', joinedAt: 4, seen: Date.now() } } })""",
                    {"code": code, "me": ME, "bothi": BOTHI, "botha": BOTHA, "old": OLD_})
        pg.evaluate("(c)=>{ openChatDock(); return joinChatRoom(c); }", code)
        pg.wait_for_timeout(1500)
        roster = pg.evaluate("""()=>[...document.querySelectorAll('#chatdock-roomwho .chatdock-who')].map(c => { const a = c.querySelector('.chatdock-who-art .rank-avatar');
            return { n: c.querySelector('.chatdock-who-name').textContent, c: a ? a.dataset.char : null, art: a ? a.dataset.art : null, me: c.classList.contains('is-me') }; })""")
        for nm, pub in (("BothI", BOTHI), ("BothA", BOTHA), ("Old", OLD_)):
            ch, art = want[pub][0], want[pub][1]
            r = next((x for x in roster if x["n"] == nm), None)
            chk("%s: the chat roster draws %s as %s in %s art" % (cls, nm, ch, art), bool(r) and r["c"] == ch and r["art"] == art, roster)
        pg.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(o=>o.remove()); try{ closeChatRoom(); }catch(e){} }")
        pg.wait_for_timeout(300)

        # ---- 7. the Virtual Room lobby: this room's class first
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
        pg.evaluate("()=>createVirtualRoomLobby(['Identity Crimes'], null, 'race')")
        for _ in range(40):
            if pg.evaluate("()=>!!vroomCode"): break
            pg.wait_for_timeout(250)
        vc = pg.evaluate("()=>vroomCode")
        if vc:
            pg.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).update({
                ['participants.'+x.botha]: { name:'BothA', avatarChar:'marksman', avatarCharIfc:'astronaut', level:3, badges:0, joinedAt: Date.now()+1, seen: Date.now(), progress:0, finished:false, ready:false },
                ['participants.'+x.old]:   { name:'Old', avatarChar:'alien', level:3, badges:0, joinedAt: Date.now()+2, seen: Date.now(), progress:0, finished:false, ready:false } })""",
                        {"code": vc, "botha": BOTHA, "old": OLD_})
            pg.wait_for_timeout(1600)
            lob = pg.evaluate("""()=>[...document.querySelectorAll('.vroom-row')].map(r => { const a = r.querySelector('.vroom-avatar .rank-avatar') || r.querySelector('.vroom-avatar');
                const svg = r.querySelector('.vroom-avatar svg.avatarchar-svg');
                return { t: r.textContent, c: a && a.dataset ? (a.dataset.char || null) : null, art: a && a.dataset ? (a.dataset.art || null) : null, sart: svg ? svg.getAttribute('data-art') : null }; })""")
            # BothA: the room's class (this page's) when their character in it is known; Old: no Fire Code character, so the academy's art
            wantlob = {"BothA": ("marksman", "academy") if cls == "academy" else ("astronaut", "ifc"), "Old": ("alien", "academy")}
            for nm, (ch, art) in wantlob.items():
                r = next((x for x in lob if nm in x["t"]), None)
                chk("%s: the lobby draws %s as %s in %s art" % (cls, nm, ch, art), bool(r) and r["c"] == ch and r["art"] == art, lob)
        else:
            chk("%s: a Virtual Room lobby opened" % cls, False, "no vroomCode")

        # ---- 8. the beat: the class it is written from, the banner and numbers of THAT class, merged, once, small, no code
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(300)
        beat = pg.evaluate("""()=>{ wornBanner = () => 'tests100'; const b = presenceClassesValue(); return b; }""")
        chk("%s: the beat says the class it is written from (lc)" % cls, beat.get("lc") == cls, beat)
        own, other = ("fb", "b") if cls == "ifc" else ("b", "fb")
        chk("%s: ...and that class's banner id under `%s`, not `%s`" % (cls, own, other), beat.get(own) == "tests100" and other not in beat, beat)
        lvk, bgk = ("flv", "fbg") if cls == "ifc" else ("lv", "bg")
        chk("%s: ...and that class's level and badges (`%s`, `%s`) as numbers" % (cls, lvk, bgk), isinstance(beat.get(lvk), int) and isinstance(beat.get(bgk), int), beat)
        chk("%s: ...which is small (%d bytes) and holds no sync code" % (cls, len(json.dumps(beat))), len(json.dumps(beat)) < 420 and "SYNC" not in json.dumps(beat), beat)
        pg.evaluate("""(x)=>{ window.__pw = []; const od = fbDb.collection.bind(fbDb);
            fbDb.collection = c => { const col = od(c); const dd = col.doc.bind(col);
              col.doc = id => { const d = dd(id); if(c === 'vrooms' && id === 'presence-v1'){ const os = d.set.bind(d); d.set = (data, o) => { window.__pw.push(JSON.parse(JSON.stringify(data))); return os(data, o); }; } return d; };
              return col; };
            const other = {}; other[x.k] = 'tests250'; return fbDb.collection('vrooms').doc('presence-v1').set({ c: { [store.publicId]: other } }, { merge: true }); }""", {"k": other})
        pg.wait_for_timeout(300)
        pg.evaluate("()=>{ window.__pw = []; sendHeartbeat(true); }")
        pg.wait_for_timeout(500)
        writes = pg.evaluate("()=>window.__pw")
        chk("%s: the beat is ONE write, as it was (%d)" % (cls, len(writes)), len(writes) == 1, writes)
        doc = pg.evaluate("()=>fbDb.collection('vrooms').doc('presence-v1').get().then(s => s.data())")
        mine = (doc.get("c") or {}).get(ME) or {}
        chk("%s: ...merged: the other class's banner (`%s`) is still there, this one's is new" % (cls, other), mine.get(other) == "tests250" and mine.get(own) == "tests100" and mine.get("lc") == cls, mine)
        chk("%s: the document holds no sync code" % cls, "SYNC-ME" not in json.dumps(doc), "")
        chk("%s: no page errors" % cls, not errs, errs[:3])
    finally:
        ctx.close()

NAMES_BY_N = {v: k for k, v in NAMES.items() if v}

# ---- the drawing of both classes' art on this page, character by character, and banner by banner
ART_JS = """()=>{
  const strip = el => { const u = el.getAttribute && el.getAttribute('data-cx-uid'); let x = new XMLSerializer().serializeToString(el); if(u) x = x.split(u).join('U');
    return x.replace(/ data-art="[a-z]+"/g, '').replace(/bn\\d+-/g, 'bn-'); };
  const kindOf = svg => { const f = svg && svg.querySelector("[class*='cx-k-']"); const m = f && /\\bcx-k-([a-z0-9_]+)/.exec(f.getAttribute('class') || ''); return m ? m[1] : null; };
  const before = { glow: JSON.stringify(AVATAR_GLOW), kinds: JSON.stringify(AVATAR_CHARACTERS.map(c => [c.id, c.kind])), cen: JSON.stringify(AVATAR_CENTRE_DY),
                   sp: Object.keys(CHAR_SPECIAL_DRAW).sort().join(','), n: AVATAR_CHARACTERS.length };
  const page = window.NOVA_CLASS === 'ifc' ? 'ifc' : 'academy';
  const ids = AVATAR_CHARACTERS.map(c => c.id).concat(['zeus']);
  const out = { chars: {}, banners: {} };
  ids.forEach(id => {
    const own = buildAvatarCharSVG(id);
    const row = { page: strip(own), pageKind: kindOf(own), looks: IFC_CHAR_LOOK[id] ? IFC_CHAR_LOOK[id][0] : null, retired: !!RETIRED_CHARACTER_TO[id] };
    ['academy', 'ifc'].forEach(a => {
      let s = null; try{ s = buildAvatarCharSVG(id, a); }catch(e){ row[a] = { err: String(e).slice(0, 100) }; return; }
      row[a] = s ? { kind: kindOf(s), art: s.getAttribute('data-art'), ser: strip(s), char: s.getAttribute('data-char'), size: s.querySelectorAll('*').length } : null;
    });
    out.chars[id] = row;
  });
  const after = { glow: JSON.stringify(AVATAR_GLOW), kinds: JSON.stringify(AVATAR_CHARACTERS.map(c => [c.id, c.kind])), cen: JSON.stringify(AVATAR_CENTRE_DY),
                  sp: Object.keys(CHAR_SPECIAL_DRAW).sort().join(','), n: AVATAR_CHARACTERS.length };
  out.restored = JSON.stringify(before) === JSON.stringify(after);
  out.glows = {}; Object.keys(IFC_CHAR_LOOK).forEach(id => { out.glows[id] = { a: avatarGlowIn(id, 'academy'), i: avatarGlowIn(id, 'ifc') }; });
  Object.keys(IFC_BANNER_ART).forEach(id => {
    const b = bannerDef(id); if(!b || b.rank) return;
    const o = buildBannerArt(id), a = buildBannerArt(id, 'academy'), i = buildBannerArt(id, 'ifc');
    out.banners[id] = { own: strip(o), a: strip(a), i: strip(i), aart: a.dataset.art, iart: i.dataset.art };
  });
  out.page = page;
  return out;
}"""

def run_art(br, url, cls, shared):
    errs = []
    ctx, pg, got = boot(br, url, cls, errs)
    try:
        print("\n== both classes' art on the %s page" % cls, flush=True)
        try:
            res = pg.evaluate(ART_JS)
        except Exception as e:
            chk("%s: the page can draw either class's art" % cls, False, str(e)[:200]); return
        chars, banners = res["chars"], res["banners"]
        redrawn = [i for i, r in chars.items() if r["looks"]]
        chk("%s: %d characters are drawn differently in Fire Code" % (cls, len(redrawn)), len(redrawn) >= 15, len(redrawn))
        bad = [i for i, r in chars.items() if not (r.get("academy") and r.get("ifc") and not r["academy"].get("err") and not r["ifc"].get("err"))]
        # a retired id that has no drawing at all (RETIRED_CHARACTER_TO says what it is) still draws as something
        chk("%s: every character draws in both classes' art without an error (%d of %d)" % (cls, len(chars) - len(bad), len(chars)), not bad, bad[:6])
        wrongart = [i for i, r in chars.items() if r.get("academy") and r.get("ifc") and (r["academy"]["art"] != "academy" or r["ifc"]["art"] != "ifc")]
        chk("%s: ...each drawing says which class's art it is" % cls, not wrongart, wrongart[:6])
        wrongifc = [i for i in redrawn if chars[i].get("ifc") and chars[i]["ifc"]["kind"] != chars[i]["looks"]]
        chk("%s: a redrawn character is Fire Code's kind in Fire Code art, on this page too" % cls, not wrongifc, wrongifc[:6])
        if cls == "academy":
            shared["kinds"] = {i: chars[i]["academy"]["kind"] for i in redrawn if chars[i].get("academy")}
        kinds = shared.get("kinds") or {}
        wrongac = [i for i in redrawn if chars[i].get("academy") and (chars[i]["academy"]["kind"] == chars[i]["looks"] or (kinds and chars[i]["academy"]["kind"] != kinds.get(i)))]
        chk("%s: ...and the academy's kind in academy art, on this page too" % cls, not wrongac and (cls == "academy" or bool(kinds)), wrongac[:6])
        same = [i for i in redrawn if chars[i].get("academy") and chars[i].get("ifc") and chars[i]["academy"]["ser"] == chars[i]["ifc"]["ser"]]
        chk("%s: the two classes' drawings of one id are different drawings" % cls, not same, same[:6])
        keep = [i for i, r in chars.items() if r.get("academy") and r.get("ifc") and not r["looks"] and not r["retired"] and r["academy"]["ser"] != r["ifc"]["ser"]]
        chk("%s: an id drawn the same in both classes is the same drawing" % cls, not keep, keep[:6])
        z = chars.get("zeus", {})
        chk("%s: Zeus (dropped from Fire Code's table) is still Zeus in the academy's art" % cls, bool(z.get("academy")) and z["academy"]["kind"] == "zeus", z.get("academy"))
        own_art = "academy" if cls == "academy" else "ifc"
        moved = [i for i, r in chars.items() if r.get(own_art) and r["page"] != r[own_art]["ser"]]
        chk("%s: the page's own art is the drawing it always was (no argument = this class)" % cls, not moved, moved[:6])
        chk("%s: nothing lent for a draw is left behind (kinds, glows, centring, specials, the table)" % cls, res["restored"], "")
        gl = [i for i, g in res["glows"].items() if g["a"] == g["i"]]
        chk("%s: a glow follows the art (%d of %d differ)" % (cls, len(res["glows"]) - len(gl), len(res["glows"])), len(gl) <= 3, gl)
        bn = [i for i, b in banners.items() if b["a"] == b["i"]]
        chk("%s: %d redrawn banners draw differently in the two classes' art" % (cls, len(banners) - len(bn)), len(banners) >= 15 and len(bn) <= 2, bn[:6])
        bw = [i for i, b in banners.items() if b["aart"] != "academy" or b["iart"] != "ifc"]
        chk("%s: ...each banner says which class's art it is" % cls, not bw, bw[:6])
        bo = [i for i, b in banners.items() if b[own_art[0]] != b["own"]]
        chk("%s: ...the page's own art of a banner is unchanged" % cls, not bo, bo[:6])
        chk("%s: no page errors" % cls, not errs, errs[:3])
    finally:
        ctx.close()

def main():
    srv, url = serve()
    shared = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            for cls in ("academy", "ifc"):
                for attempt in range(3):
                    try: run_class(br, url, cls, shared); break
                    except Exception as e:
                        if attempt == 2 or not any(w in str(e) for w in ("crashed", "Target", "closed", "Timeout")):
                            chk("%s: the run completed" % cls, False, str(e)[:300]); break
                        print("  (retry: %s)" % str(e).split("\n")[0][:80], flush=True)
            for cls in ("academy", "ifc"):
                for attempt in range(3):
                    try: run_art(br, url, cls, shared); break
                    except Exception as e:
                        if attempt == 2 or not any(w in str(e) for w in ("crashed", "Target", "closed", "Timeout")):
                            chk("%s: the art run completed" % cls, False, str(e)[:300]); break
            br.close()
    finally:
        srv.shutdown()
    print("\nALL GOOD" if ok else "\nFAILED"); sys.exit(0 if ok else 1)
main()
