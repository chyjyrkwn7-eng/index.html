#!/usr/bin/env python3
"""Friends: a real request, a real accept, and a real decline.

NOBODY EVER WRITES ANYBODY ELSE'S DOCUMENT. That is the whole design and
it is the thing most worth asserting, because it is what lets this work
under the rules the project actually has - a `friendreqs` collection was
the obvious shape and returns 403 against the live database. A request
lives in the SENDER's own leaderboard row and an acceptance in the
ACCEPTER's own row, so this check drives two simulated people by handing
each one the other's row and watching what each one writes.

  python3 tools/check-friends.py
  python3 tools/check-friends.py --against /path/to/old-index.html

It fails on build 137 and every build before it, where none of this
exists. Device-independent - none of it is layout - so it runs once.
"""
import functools
import http.server
import io
import os
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
SRC = (sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv
       else os.path.join(ROOT, "index.html"))

SEED = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,'
        '"tourRev":99,"leaderboardOptIn":true,"publicId":"me0000000001",'
        '"lifetime":{"points":14820,"answered":5400,"correct":4980,"drillPlays":64,'
        '"examPlays":22,"gamePlays":9,"perfectTests":141,"currentStreak":23,'
        '"longestStreak":57}}')

BODY = INSET_RE.sub(lambda m: "0px", io.open(SRC, encoding="utf-8").read())

_s = socket.socket(); _s.bind(("127.0.0.1", 0))
PORT = _s.getsockname()[1]; _s.close()


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


SERVER = http.server.ThreadingHTTPServer(
    ("127.0.0.1", PORT), functools.partial(_Quiet, directory=ROOT))
threading.Thread(target=SERVER.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT
FAILURES = []


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -> " + str(detail)) if detail else ""))
    if not ok:
        FAILURES.append(name)


def booted(br, width=440, height=956):
    ctx = br.new_context(viewport={"width": width, "height": height})
    ctx.add_init_script(
        "try{localStorage.setItem('class26e.freshstart','1');"
        "localStorage.setItem('class26e.synccode','SECR-ETXX');"
        # The introduction card opens two seconds after Home on a device
        # that has not seen it - which is every harness device. Seeded
        # like frame.ok and tourRev, or it drops a dimmed overlay over
        # whatever is being measured.
        "localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % SEED)
    pg = ctx.new_page()
    pg.route("**/index.html", lambda r: r.fulfill(
        status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove();"
                " fbDb = { collection:()=>({ doc:()=>({ set:()=>Promise.resolve(),"
                " update:()=>Promise.resolve(), delete:()=>Promise.resolve() }) }) };}")
    return ctx, pg


# The other person's row, as the board would deliver it.
ALEX = """(opts)=>{
  leaderboardRows = [
    { pub:'me0000000001', firstName:'Madison', fcode: friendCodeOf(),
      freq: store.friendsOut||[], facc: store.friendsIn||[], level:50, badges:9, hundos:141 },
    Object.assign({ pub:'alex000000002', firstName:'Alex', fcode:'ABC-234',
      level:40, badges:8, hundos:90, freq:[], facc:[] }, opts||{})
  ];
  return true;}"""


def main():
    print("checking %s" % SRC)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        ctx, pg = booted(br)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        print("\n1. the friend code is a handle, not a secret")
        r = pg.evaluate("""()=>({ code: friendCodeOf(), sync: syncCode, pub: store.publicId })""")
        check("it exists and is ABC-123 shaped",
              bool(re.match(r"^[A-Z0-9]{3}-[A-Z0-9]{3}$", r["code"])), r["code"])
        # A DIFFERENT SHAPE FROM THE SYNC CODE ON PURPOSE, so the two can
        # never be confused for one another in a message.
        check("a different shape from the sync code",
              len(r["code"]) != len(r["sync"]), [r["code"], r["sync"]])
        check("not derived from the sync code or the public id",
              r["code"].replace("-", "") not in (r["sync"] + r["pub"]).replace("-", ""), r)

        print("\n2. asking writes MY row and nobody else's")
        pg.evaluate(ALEX, None)
        r = pg.evaluate("""()=>{
          const res = sendFriendRequest('abc-234');
          return { res: res, out: store.friendsOut, inn: store.friendsIn,
                   alexUntouched: leaderboardRows[1].facc.length === 0
                                && leaderboardRows[1].freq.length === 0 };}""")
        check("the request is accepted", r["res"]["ok"] is True, r["res"])
        check("lowercase input still finds them", "alex000000002" in r["out"], r["out"])
        check("it went in MY row, not theirs", r["alexUntouched"] is True, r)
        check("we are not friends yet", pg.evaluate("()=>friendPublicIds().length") == 0)
        bad = pg.evaluate("()=>sendFriendRequest('ZZZ-999')")
        check("an unknown code says so rather than failing silently",
              bad["ok"] is False and "code" in bad["why"], bad)
        own = pg.evaluate("()=>sendFriendRequest(friendCodeOf())")
        check("your own code is refused", own["ok"] is False, own)

        print("\n3. they see it, and accepting is THEIR write")
        # Alex's client: his row is the one that changes.
        r = pg.evaluate("""()=>{
          /* Stand in Alex's shoes: his public id, and Madison's row now
             carries the request. */
          store.publicId = 'alex000000002';
          store.friendsOut = []; store.friendsIn = []; store.friendsDeclined = [];
          leaderboardRows = [
            { pub:'me0000000001', firstName:'Madison', fcode:'MAD-111',
              freq:['alex000000002'], facc:[], level:50, badges:9, hundos:141 }
          ];
          const seen = incomingFriendRequests().map(e=>e.pub);
          acceptFriendRequest('me0000000001');
          return { seen: seen, mine: store.friendsIn,
                   friends: friendPublicIds(),
                   madisonUntouched: leaderboardRows[0].facc.length === 0 };}""")
        check("Alex sees the request", r["seen"] == ["me0000000001"], r["seen"])
        check("accepting writes ALEX's own list", r["mine"] == ["me0000000001"], r["mine"])
        check("and never touches Madison's row", r["madisonUntouched"] is True)
        check("they are friends now", r["friends"] == ["me0000000001"], r["friends"])

        print("\n4. and Madison sees it from the other side")
        r = pg.evaluate("""()=>{
          store.publicId = 'me0000000001';
          store.friendsOut = ['alex000000002']; store.friendsIn = []; store.friendsDeclined = [];
          /* Alex's row now accepts her - which is the only signal she
             gets, and it has to be enough. */
          leaderboardRows = [
            { pub:'alex000000002', firstName:'Alex', fcode:'ABC-234',
              freq:[], facc:['me0000000001'], level:40, badges:8, hundos:90 }
          ];
          return { friends: friendPublicIds(), pending: outgoingFriendRequests() };}""")
        check("one accept from either side is enough", r["friends"] == ["alex000000002"], r["friends"])
        check("and it stops showing as waiting", r["pending"] == [], r["pending"])

        print("\n5. declining is quiet and local")
        r = pg.evaluate("""()=>{
          store.publicId = 'alex000000002';
          store.friendsIn = []; store.friendsDeclined = []; store.friendsOut = [];
          leaderboardRows = [
            { pub:'me0000000001', firstName:'Madison', fcode:'MAD-111',
              freq:['alex000000002'], facc:[], level:50, badges:9, hundos:141 }
          ];
          declineFriendRequest('me0000000001');
          return { pending: incomingFriendRequests().length,
                   friends: friendPublicIds().length,
                   declined: store.friendsDeclined,
                   /* Nothing about a decline may be published - it would
                      mean writing "no" into a document the other person
                      reads. */
                   notPublished: (store.friendsOut||[]).indexOf('me0000000001') < 0
                              && (store.friendsIn||[]).indexOf('me0000000001') < 0 };}""")
        check("the request stops showing", r["pending"] == 0, r["pending"])
        check("they do not become a friend", r["friends"] == 0, r["friends"])
        check("and the decline is never published", r["notPublished"] is True, r)

        print("\n6. a lobby invite rides the same rails")
        r = pg.evaluate("""()=>{
          store.publicId = 'me0000000001';
          store.friendsIn = ['alex000000002']; store.friendsDeclined = [];
          inviteFriendToLobby('alex000000002', 'ROOM42');
          const mine = store.lobbyInvitesOut;
          /* Now stand in Alex's shoes and read it off HER row. */
          store.publicId = 'alex000000002';
          store.friendsIn = ['me0000000001'];
          leaderboardRows = [
            { pub:'me0000000001', firstName:'Madison', facc:['alex000000002'],
              freq:[], inv:{ 'alex000000002': { code:'ROOM42', at: Date.now() } } }
          ];
          const live = incomingLobbyInvites();
          leaderboardRows[0].inv['alex000000002'].at = Date.now() - (LOBBY_INVITE_TTL_MS + 5000);
          const stale = incomingLobbyInvites();
          return { mine: mine, live: live.map(x=>x.code), stale: stale.length };}""")
        check("the invite is written into MY row", r["mine"]["alex000000002"]["code"] == "ROOM42", r["mine"])
        check("a friend sees it", r["live"] == ["ROOM42"], r["live"])
        # A room that finished an hour ago is not an invitation.
        check("and an old one expires rather than lingering", r["stale"] == 0, r["stale"])

        print("\n7. what gets published, and what must not be")
        r = pg.evaluate("""()=>{
          store.publicId = 'me0000000001';
          const wrote = [];
          fbDb = { collection: n => ({ doc: id => ({
            set: d => { wrote.push({n:n, id:id, d:d}); return Promise.resolve(); },
            update: ()=>Promise.resolve(), delete: ()=>Promise.resolve() }) }) };
          store.leaderboardOptIn = true;
          pushToCloud();
          const lb = wrote.filter(w=>w.n==='leaderboard');
          const flat = JSON.stringify(lb);
          return { n: lb.length,
                   hasCode: !!(lb[0] && lb[0].d.fcode),
                   hasFreq: !!(lb[0] && lb[0].d.freq),
                   hasFacc: !!(lb[0] && lb[0].d.facc),
                   onlyMyId: lb.every(w => w.id === store.publicId),
                   secret: flat.indexOf(syncCode) >= 0 };}""")
        check("my row carries the friend code and both lists",
              r["hasCode"] and r["hasFreq"] and r["hasFacc"], r)
        check("every write is to MY OWN document", r["onlyMyId"] is True, r)
        check("and the sync code is still nowhere in it", r["secret"] is False, r)

        # ---------------------------------------------------------------
        # A SCREEN CHECKED ONLY WHILE IT IS EMPTY IS NOT CHECKED.
        # Everything above drives the functions, and all of it passed on
        # a build where showFriends() threw on its very first row:
        # decorateAvatar() takes the ELEMENT the rank coin hangs off and
        # it was handed a character id, which type-checks fine, draws
        # nothing, and throws the moment there is anybody to draw. So
        # the screen was blank for exactly the people who have friends.
        # The sweep mounts it cold, with no rows, and saw nothing.
        # This runs it at 320px, the width where the row squashed.
        print("\n8. the screen itself, with people on it")
        ctx2, pg2 = booted(br, 320, 568)
        errs2 = []
        pg2.on("pageerror", lambda e: errs2.append(str(e)))
        # A throw here is the failure, not a crash of the harness -
        # `--against` an older build has to REPORT it, not stop.
        try:
            r = pg2.evaluate("""()=>{
          store.publicId = 'me0000000001';
          store.friendsIn = ['kim000000003'];
          store.friendsOut = ['zoe000000004','dee000000005'];
          store.friendsDeclined = [];
          const now = Date.now();
          leaderboardRows = [
            { pub:'alex000000002', firstName:'Alexandra', avatarChar:'officer',
              level:40, badges:8, hundos:90, fcode:'ABC-234',
              freq:['me0000000001'], facc:[], lastModified: now - 9000 },
            { pub:'ray000000006', firstName:'Ray', avatarChar:'robot',
              level:14, badges:3, hundos:12, fcode:'MND-234',
              freq:['me0000000001'], facc:[], lastModified: now - 99999999 },
            { pub:'kim000000003', firstName:'Kim', avatarChar:'astronaut',
              level:18, badges:5, hundos:23, fcode:'LPQ-234',
              freq:['me0000000001'], facc:[], lastModified: now - 9000 },
            { pub:'zoe000000004', firstName:'Zoe', avatarChar:'clown',
              level:31, badges:9, hundos:88, fcode:'HJK-234',
              freq:[], facc:['me0000000001'], lastModified: now - 99999999 },
            { pub:'dee000000005', firstName:'Dee', avatarChar:'grizzly',
              level:9, badges:1, hundos:4, fcode:'TVW-234',
              freq:[], facc:[], lastModified: now - 9000 }
          ];
          showFriends();
          const rows = [...document.querySelectorAll('.friend-row')];
          const texts = rows.map(x => x.querySelector('.friend-row-text'));
          return {
            rows: rows.length,
            pending: document.querySelectorAll('.friend-sect-pending .friend-row').length,
            drawn: rows.every(x => !!x.querySelector('.rank-avatar svg')),
            names: rows.map(x => (x.querySelector('.friend-row-name')||{}).textContent),
            narrowest: texts.length ? Math.round(Math.min.apply(null,
              texts.map(t => t.getBoundingClientRect().width))) : 0,
            dots: document.querySelectorAll('.friend-online-dot').length,
            overflow: document.documentElement.scrollWidth - window.innerWidth
          };}""")
        except Exception as exc:
            check("the screen builds at all", False, str(exc).splitlines()[0])
            r = {"rows": 0, "pending": 0, "drawn": False, "names": [""],
                 "narrowest": 0, "dots": 0, "overflow": 0}
        # 2 waiting on me, 2 friends, 1 I have asked and not heard back from.
        check("every person has a row", r["rows"] == 5, r["rows"])
        check("the two requests are in the pending section", r["pending"] == 2, r["pending"])
        # The bug: the row built, the character did not.
        check("each row draws its character", r["drawn"] is True, r["names"])
        check("and names its person", r["names"][0] == "Alexandra", r["names"])
        # THE SQUASH: two nowrap buttons took 150px of a 280px column and
        # left the name at 66px - "Alexandra" clipped to one letter. It
        # never overflowed, which is why a green sweep said nothing.
        check("the name column is not squashed by the buttons",
              r["narrowest"] >= 110, r["narrowest"])
        check("no sideways scroll at 320px", r["overflow"] <= 0, r["overflow"])
        # Read off lastModified, which the row already publishes.
        check("the green dot marks exactly who is online", r["dots"] == 3, r["dots"])
        check("and the screen threw nothing", not errs2, errs2[:3])
        ctx2.close()

        # ---------------------------------------------------------------
        # 9. THE SCREEN MUST NOT REBUILD UNDER SOMEBODY'S FINGERS.
        # A leaderboard snapshot arrives every time anybody in the class
        # pushes - on a board of forty, constantly - and the first
        # version of the live listener called showFriends() on each one.
        # That threw away the add-a-friend field mid-typing and blanked
        # the lists for a frame: "it's glitched and won't even let you
        # type in a code". Measured on the build it was written for: the
        # field came back EMPTY and unfocused after 15 rebuilds.
        print("\n9. typing a code while the class board is busy")
        ctx3, pg3 = booted(br)
        errs3 = []
        pg3.on("pageerror", lambda e: errs3.append(str(e)))
        pg3.evaluate("""()=>{
          window.__cbs=[]; window.__renders=0;
          const now=Date.now();
          window.__rows=[
            {pub:'me0000000001',firstName:'Madison',fcode:'AAA-234',freq:[],facc:[],level:20,badges:5,hundos:9,lastModified:now},
            {pub:'ray000000006',firstName:'Ray',avatarChar:'robot',fcode:'MND-234',freq:[],facc:[],level:14,badges:3,hundos:12,lastModified:now}];
          window.__mkSnap=(rows,cache)=>({metadata:{fromCache:!!cache},
            forEach:f=>rows.forEach(r=>f({id:r.pub,data:()=>r}))});
          fbDb={collection:()=>({doc:()=>({set:()=>Promise.resolve(),update:()=>Promise.resolve()}),
            onSnapshot:(cb)=>{window.__cbs.push(cb); cb(window.__mkSnap(window.__rows,false)); return ()=>{};}})};
          store.publicId='me0000000001'; store.friendsOut=[]; store.friendsIn=[];
          const _sf=showFriends;
          showFriends=function(){ window.__renders++; return _sf.apply(this,arguments); };
          leaderboardRows=[]; showFriends();}""")
        pg3.wait_for_timeout(400)
        pg3.click(".friend-add-input")
        pg3.type(".friend-add-input", "MND-2", delay=30)
        live = pg3.evaluate("""()=>{
          for(let i=0;i<12;i++){
            window.__rows[1].lastModified=Date.now()+i;
            window.__cbs.forEach(cb=>cb(window.__mkSnap(window.__rows,false)));
          }
          /* Firestore answers from cache first; an empty cached snapshot
             is not an empty class. */
          window.__cbs.forEach(cb=>cb(window.__mkSnap([],true)));
          const f=document.querySelector('.friend-add-input');
          return {value:f?f.value:null, focused:document.activeElement===f,
                  renders:window.__renders, rowsKept:(leaderboardRows||[]).length};}""")
        check("what was typed is still in the field", live["value"] == "MND-2", live)
        check("and the field still has focus", live["focused"] is True, live["focused"])
        check("the screen did not rebuild itself", live["renders"] == 1, live["renders"])
        # An empty cached snapshot must not empty the board.
        check("a cached empty snapshot does not wipe the class",
              live["rowsKept"] == 2, live["rowsKept"])
        pg3.type(".friend-add-input", "34", delay=30)
        done = pg3.evaluate("""()=>{
          const f=document.querySelector('.friend-add-input');
          const typed=f.value;
          [...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Send').click();
          return {typed, out:store.friendsOut.slice()};}""")
        check("so the whole code can be typed and sent",
              done["typed"] == "MND-234" and done["out"] == ["ray000000006"], done)
        check("and nothing threw", not errs3, errs3[:3])
        ctx3.close()

        # ---- 10. online means the app is open ------------------------
        # It was derived from `lastModified`, which only moves when
        # somebody PUSHES - so a classmate sitting on Home for ten
        # minutes read as offline and somebody who answered four minutes
        # ago and closed the app read as online. "Who is online" was
        # really "who answered something recently".
        print("\n10. online means the app is open, not that they answered recently")
        ctx4, pg4 = booted(br)
        errs4 = []
        pg4.on("pageerror", lambda e: errs4.append(str(e)))

        seen = pg4.evaluate("""()=>{
          const now = Date.now();
          return {
            /* seenAt alone is enough - the whole point. */
            beat: isOnline({ seenAt: now - 60000 }),
            /* and stale seenAt is offline however recent the push. */
            staleBeat: isOnline({ seenAt: now - 9 * 60 * 1000 }),
            /* THE FALLBACK IS LOAD-BEARING: everybody is on an older
               build for the first day after this ships, and without it
               the whole class reads offline until each phone updates. */
            oldBuild: isOnline({ lastModified: now - 60000 }),
            oldStale: isOnline({ lastModified: now - 9 * 60 * 1000 }),
            /* A row with neither is not online, not crashed. */
            empty: isOnline({}), nul: isOnline(null) };}""")
        check("a heartbeat alone makes somebody online", seen["beat"] is True, seen)
        check("and a stale one does not", seen["staleBeat"] is False, seen)
        check("an older build still reads online from its push",
              seen["oldBuild"] is True and seen["oldStale"] is False, seen)
        check("a row with neither is simply offline",
              seen["empty"] is False and seen["nul"] is False, seen)

        try:
            # EVERY GUARD ON THE HEARTBEAT IS A FIRESTORE BILL. It is the
            # only periodic write in the app; forty phones on a four-minute
            # timer is ~14k writes a day against a 20k free-tier ceiling the
            # ordinary pushes also draw on. A guard that silently stopped
            # working would not break anything visible - it would just spend
            # the quota - so each one is checked rather than trusted.
            guards = pg4.evaluate("""()=>{
              const calls = [];
              /* THE COLLECTION IS RECORDED, NOT JUST THE PAYLOAD. The
                 beat used to be stamped into this person's LEADERBOARD
                 row - the one document all ~30 classmates hold a live
                 listener on - so one green dot cost a read on every
                 phone in the class every four minutes. It goes to a
                 presence document only the Friends screen reads now.
                 Asserting WHERE it lands is the whole check; the
                 payload alone would pass either way. */
              fbDb = { collection: (c) => ({ doc: () => ({
                update: (d) => { calls.push({ coll: c, d: d }); return Promise.resolve(); },
                set: (d) => { calls.push({ coll: c, d: d });
                              return { catch: () => {} }; } }) }) };
              syncCode = "AAAA-1111"; store.publicId = "me01";
              const hidden = (v) => Object.defineProperty(document, "visibilityState",
                { get: () => v, configurable: true });

              store.leaderboardOptIn = true; hidden("visible");
              lastHeartbeatAt = 0; sendHeartbeat(true);
              const beats = calls.length;

              /* Not sharing: there is no row to write to. */
              store.leaderboardOptIn = false; lastHeartbeatAt = 0; sendHeartbeat(true);
              const optedOut = calls.length;

              /* Backgrounded: not somebody you can play with, and an app
                 left open on a desk all day is what spends the quota. */
              store.leaderboardOptIn = true; hidden("hidden");
              lastHeartbeatAt = 0; sendHeartbeat(true);
              const background = calls.length;

              /* Not syncing at all. */
              hidden("visible"); syncCode = null; lastHeartbeatAt = 0; sendHeartbeat(true);
              const noCode = calls.length;

              /* And it does not fire faster than its interval when it is
                 not forced - otherwise every screen change is a write. */
              syncCode = "AAAA-1111"; lastHeartbeatAt = Date.now(); sendHeartbeat(false);
              const throttled = calls.length;

              hidden("visible");
              return { beats, optedOut, background, noCode, throttled,
                       coll: (calls[0] || {}).coll || "",
                       field: Object.keys((calls[0] || {}).d || {}) };}""")
            check("a visible, sharing, synced device sends one",
                  guards["beats"] == 1, guards)
            # THE POINT OF THE WHOLE CHANGE.
            check("the beat does NOT touch the leaderboard row",
                  guards["coll"] != "leaderboard", guards)
            check("it goes to the presence document instead",
                  guards["coll"] == "vrooms", guards)
            check("nothing is sent when class sharing is off",
                  guards["optedOut"] == guards["beats"], guards)
            check("nothing is sent while the app is in the background",
                  guards["background"] == guards["beats"], guards)
            check("nothing is sent by a device that is not syncing",
                  guards["noCode"] == guards["beats"], guards)
            check("and it will not fire again inside its own interval",
                  guards["throttled"] == guards["beats"], guards)

            # set() REPLACES THE DOCUMENT, so a stats push landing a second
            # after a heartbeat would delete seenAt and drop the person
            # offline mid-session. Pushing is activity, so it publishes one.
            pushes = pg4.evaluate("""()=>{
              let payload = null;
              fbDb = { collection: () => ({ doc: () => ({
                set: (d) => { payload = d; return { catch: () => {} }; },
                update: () => ({ catch: () => {} }) }) }) };
              syncCode = "AAAA-1111"; store.leaderboardOptIn = true; store.publicId = "me01";
              store.firstName = "Madison";
              pushToCloud();
              return { has: !!(payload && payload.seenAt), keys: payload ? 1 : 0 };}""")
            check("a stats push republishes seenAt rather than wiping it",
                  pushes["has"] is True, pushes)
        except Exception as e:
            # --against an older build there is no heartbeat to guard,
            # and a section that throws must report that rather than
            # abort the run before it can.
            check("the heartbeat exists at all", False, repr(e)[:160])


        check("nothing threw in the heartbeat section", not errs4, errs4[:3])

        # ---- 11. the list, drawn for real ------------------------------
        # isOnline() being right is section 10; this is the screen
        # built by the app actually SAYING so - online first, the dot
        # on exactly those rows. It also pins the count of actions per
        # row: an Invite button was added here and asked against
        # directly ("why would the invite option be there?"), so every
        # row carries the same one action, online or not.
        print("\n11. the list says who is online, and offers no invite")
        errs5 = []
        pg4.on("pageerror", lambda e: errs5.append(str(e)))
        shape = pg4.evaluate("""()=>{
          store.publicId = "me0000000001";
          store.friendsIn = ["alex000000002", "sam00000000003"];
          store.friendsOut = []; store.friendsDeclined = [];
          store.leaderboardOptIn = true;
          store.lobbyInvitesOut = {};
          const now = Date.now();
          leaderboardRows = [
            { pub:"alex000000002", firstName:"Alex", fcode:"ABC-234", level:40,
              badges:8, hundos:90, freq:[], facc:["me0000000001"], seenAt: now - 30000 },
            { pub:"sam00000000003", firstName:"Sam", fcode:"SAM-234", level:12,
              badges:1, hundos:4, freq:[], facc:["me0000000001"], seenAt: now - 9*60*1000 }
          ];
          showFriends();
          const rows = [...document.querySelectorAll(".friend-row")].map(r => ({
            name: (r.querySelector(".friend-row-name") || {}).textContent,
            dot: !!r.querySelector(".friend-online-dot"),
            acts: r.querySelectorAll(".friend-act").length }));
          return rows;}""")
        byname = {r["name"]: r for r in shape}
        check("both friends are listed", set(byname) == {"Alex", "Sam"}, shape)
        check("the online one is first", shape and shape[0]["name"] == "Alex", shape)
        check("only the online one carries the dot",
              byname.get("Alex", {}).get("dot") is True
              and byname.get("Sam", {}).get("dot") is False, shape)
        check("every row carries the same one action, online or not",
              [r["acts"] for r in shape] == [1, 1], shape)

        check("nothing threw drawing the list", not errs5, errs5[:3])

        # ---- 12. adding somebody from the Leaderboard -------------------
        # Asked for directly, and it is also what keeps the class
        # reachable now that codes are gone: invites go to friends, so
        # without a way in from the board the only route to a classmate
        # is having already swapped friend codes with them.
        print("\n12. a classmate can be added from the Leaderboard")
        lb = pg4.evaluate("""()=>{
          store.publicId = "me0000000001";
          store.friendsIn = []; store.friendsOut = []; store.friendsDeclined = [];
          store.leaderboardOptIn = true;
          /* The default board is This Week, ranked on weekPoints against
             the CURRENT week key - a row without both is filtered out
             and the board draws nothing. Seeded from the app's own
             weekKeyNow() rather than a literal, so this cannot go stale
             on a Monday. */
          const wk = weekKeyNow();
          leaderboardRows = [
            { pub:"me0000000001", firstName:"Madison", level:50, badges:9, correct:900, hundos:141, week:wk, weekPoints:900, freq:[], facc:[] },
            { pub:"alex000000002", firstName:"Alex", level:40, badges:8, correct:800, hundos:90, week:wk, weekPoints:800, freq:[], facc:[] },
            { pub:"sam00000000003", firstName:"Sam", level:12, badges:1, correct:400, hundos:4, week:wk, weekPoints:400, freq:[], facc:[] }
          ];
          /* THE BOARD READS ITS OWN SNAPSHOT, not the shared
             leaderboardRows: `entries` is a local inside showRankings()
             and is only ever filled by the listener. So the listener is
             what has to be driven, with the shape Firestore actually
             delivers - a forEach over {id, data()} - which is also the
             path a real message arrives on. */
          const docs = [
            { id:"me0000000001", d:{ firstName:"Madison", level:50, badges:9, hundos:141, week:wk, weekPoints:900 } },
            { id:"alex000000002", d:{ firstName:"Alex", level:40, badges:8, hundos:90, week:wk, weekPoints:800 } },
            { id:"sam00000000003", d:{ firstName:"Sam", level:12, badges:1, hundos:4, week:wk, weekPoints:400 } }
          ];
          let boardCb = null;
          const realOnSnap = onSnapshotResilient;
          onSnapshotResilient = (ref, cb) => { boardCb = cb; return () => {}; };
          fbDb = { collection: () => ({ doc: () => ({
            set: () => ({ catch: () => {} }), update: () => ({ catch: () => {} }) }) }) };
          syncCode = "AAAA-1111";
          showRankings();
          onSnapshotResilient = realOnSnap;
          if(boardCb) boardCb({ forEach: (f) => docs.forEach(x => f({ id:x.id, data:()=>x.d })) });
          const tab = [...document.querySelectorAll(".screen-rankings .iconbtn")]
            .find(b => b.textContent === "Level");
          if(tab) tab.click();
          const rows = [...document.querySelectorAll(".rank-row")];
          const mine = rows.filter(r => r.dataset.me === "1");
          const others = rows.filter(r => r.dataset.me !== "1");
          return { rows: rows.length,
                   mineTappable: mine.some(r => r.classList.contains("is-tappable")),
                   othersTappable: others.length > 0 && others.every(r => r.classList.contains("is-tappable")) };}""")
        check("the board drew its rows", lb["rows"] >= 2, lb)
        check("somebody else's row is tappable", lb["othersTappable"] is True, lb)
        # NOTHING TO DO WITH YOURSELF, so your own row is not a button.
        check("and your own row is not", lb["mineTappable"] is False, lb)

        sent = pg4.evaluate("""()=>{
          let pushed = 0;
          fbDb = { collection: () => ({ doc: () => ({
            set: () => { pushed++; return { catch: () => {} }; },
            update: () => ({ catch: () => {} }) }) }) };
          syncCode = "AAAA-1111";
          const row = [...document.querySelectorAll(".rank-row")]
            .find(r => r.textContent.indexOf("Alex") >= 0 && r.dataset.me !== "1");
          row.click();
          const sheet = document.querySelector(".person-sheet");
          if(!sheet) return { no: "tapping a classmate opened nothing" };
          /* THE SHEET IS BUILT AT opacity:0 AND FADED IN ON THE NEXT
             FRAME, so asking the DOM whether it is there cannot fail on
             "you cannot see it" - which is exactly how the chat's own
             invite sheet shipped invisible. Wait a frame and measure. */
          return new Promise(res => setTimeout(() => {
            const o = document.querySelector(".invite-overlay");
            const op = o ? Number(getComputedStyle(o).opacity) : 0;
            const act = sheet.querySelector(".person-sheet-act");
            const label = act.textContent;
            act.click();
            res({ label: label, out: (store.friendsOut || []).slice(),
                  pushed: pushed, op: op,
                  closed: !document.querySelector(".person-sheet") });
          }, 350));}""")
        if sent.get("no"):
            check("tapping a classmate opens their card", False, sent["no"])
        else:
            check("tapping a classmate opens their card", True)
            check("and the card is actually visible", (sent.get("op") or 0) > 0.5, sent.get("op"))
            check("the action offers to add them", "Add friend" in sent["label"], sent["label"])
            # ADDRESSED BY publicId. The friend-code path searches the
            # board for a typed code; there is nothing to look up here,
            # and nothing that could become a name-to-code lookup - which
            # this app deliberately does not have.
            check("the request is written against their public id",
                  sent["out"] == ["alex000000002"], sent["out"])
            # It lives in MY row, so it does not exist for them until it
            # is published.
            check("and published straight away", sent["pushed"] >= 1, sent)
            check("the card closes once it is sent", sent["closed"] is True, sent)

        repeat = pg4.evaluate("""()=>{
          const row = [...document.querySelectorAll(".rank-row")]
            .find(r => r.textContent.indexOf("Alex") >= 0 && r.dataset.me !== "1");
          row.click();
          const act = document.querySelector(".person-sheet-act");
          const r = { label: act.textContent, disabled: act.disabled };
          document.querySelector(".invite-overlay").remove();
          return r;}""")
        # A BUTTON THAT STILL SAYS "ADD FRIEND" IS HOW SOMEBODY SENDS THE
        # SAME REQUEST SIX TIMES AND WONDERS WHY NOTHING HAPPENS.
        check("a second look says the request is already sent",
              repeat["disabled"] is True and "sent" in repeat["label"].lower(), repeat)

        # THE HUNDO COUNT CAME OFF THE FRIENDS LIST, on request.
        gone = pg4.evaluate("""()=>{
          store.friendsIn = ["alex000000002"];
          showFriends();
          const sub = document.querySelector(".friend-row-sub");
          return { text: sub ? sub.textContent : null };}""")
        check("a friend's row no longer counts their hundos",
              bool(gone["text"]) and "hundo" not in gone["text"].lower(), gone)
        check("but it still says who they are",
              bool(gone["text"]) and "Level" in gone["text"], gone)


        # ---- 13. the row is a scoreboard, not a log ---------------------
        print("\n13. what actually writes the leaderboard row")
        # The project ran out of its daily Firestore read quota because
        # every saveStore() wrote this document, and every write of it is
        # charged again as a read to all ~30 classmates listening. Two
        # changes, and the SECOND one is the dangerous one: score fields
        # may wait, but an invite in the same row must not. This asserts
        # both the saving and the safety property, because getting the
        # saving without the safety would silently break invites - the
        # thing three builds today were spent fixing.
        quota = pg4.evaluate("""()=>{
          /* On a build without the split this whole section does not
             exist. Say so rather than throwing - a gate that crashes
             takes the rest of the run with it and reports nothing. */
          if(typeof flushLeaderboardRow !== "function")
            return { missing: "the leaderboard row is written on every save" };
          let writes = 0;
          fbDb = { collection: (c) => ({ doc: () => ({
            set: () => { if(c === 'leaderboard') writes++; return { catch: () => {} }; },
            update: () => ({ catch: () => {} }),
            delete: () => ({ catch: () => {} }) }) }) };
          syncCode = "AAAA-1111";
          store.leaderboardOptIn = true;
          store.lifetime = store.lifetime || { correct: 0 };

          /* A first push establishes the baseline. */
          flushLeaderboardRow();
          const base = writes;

          /* (1) A save that changes nothing on the row - a theme toggle,
             a tour flag, a dismissed notification all look like this. */
          saveStore(); pushToCloud(); pushToCloud();
          const afterNoChange = writes;

          /* (2) Only the numbers moved: answering a question. */
          store.lifetime.correct = (store.lifetime.correct || 0) + 1;
          pushToCloud();
          store.lifetime.correct += 1;
          pushToCloud();
          const afterScore = writes;

          /* (3) An invite lands in this same row and cannot wait. */
          store.chatInvitesOut = { zzz999: { code: 'ABCD-1234', at: Date.now() } };
          pushToCloud();
          const afterInvite = writes;

          /* (4) And the end of a run publishes the numbers held back. */
          flushLeaderboardRow();
          return { base: base,
                   noChange: afterNoChange - base,
                   score: afterScore - afterNoChange,
                   invite: afterInvite - afterScore,
                   flush: writes - afterInvite };}""")
        check("a save that changes nothing on the row writes nothing",
              quota.get("noChange") == 0, quota)
        check("answering questions does not write it every time",
              quota.get("score") == 0, quota)
        # THE ONE THAT MUST NOT REGRESS.
        check("but an invite still goes out immediately",
              quota.get("invite") == 1, quota)
        check("and the end of a run publishes the held-back numbers",
              quota.get("flush") == 1, quota)

        # A DELETED ROW STILL MATCHES ITS OWN SIGNATURE, which is how
        # "skip an identical write" quietly breaks the Settings toggle:
        # turning it off deletes the document, turning it back on builds
        # a row identical to the cached one, compares equal, and writes
        # nothing - so the person stays OFF the board while the toggle
        # says they are on it. Driven through the real control.
        toggled = pg4.evaluate("""()=>{
          let writes = 0, deletes = 0;
          fbDb = { collection: (c) => ({ doc: () => ({
            set: () => { if(c === 'leaderboard') writes++; return { catch: () => {} }; },
            update: () => ({ catch: () => {} }),
            delete: () => { if(c === 'leaderboard') deletes++;
                            return { catch: () => {} }; } }) }) };
          syncCode = "AAAA-1111";
          store.leaderboardOptIn = true;
          flushLeaderboardRow();
          const before = writes;
          showAppearance();
          const box = [...document.querySelectorAll('input[type=checkbox]')]
            .find(b => b.checked && b.closest('label,div,section'));
          return new Promise(r => setTimeout(() => {
            /* Off, then on, through the store the control writes to. */
            store.leaderboardOptIn = false; store.leaderboardOptInChanged = true;
            pushToCloud();
            const afterOff = { w: writes, d: deletes };
            store.leaderboardOptIn = true; store.leaderboardOptInChanged = true;
            pushToCloud();
            r({ before: before, offDeletes: afterOff.d,
                backOn: writes - afterOff.w, hadBox: !!box });
          }, 200));}""")
        check("turning the leaderboard off removes the row",
              toggled.get("offDeletes", 0) >= 1, toggled)
        check("and turning it back on puts it back",
              toggled.get("backOn") == 1, toggled)

        ctx4.close()

        check("no uncaught JS along the way", not errs, errs[:3])
        ctx.close()
        br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))" %
          ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


main()
