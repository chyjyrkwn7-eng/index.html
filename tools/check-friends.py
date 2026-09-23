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


def booted(br):
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script(
        "try{localStorage.setItem('class26e.freshstart','1');"
        "localStorage.setItem('class26e.synccode','SECR-ETXX');"
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

        check("no uncaught JS along the way", not errs, errs[:3])
        ctx.close()
        br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))" %
          ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


main()
