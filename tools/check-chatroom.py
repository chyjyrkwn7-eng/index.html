#!/usr/bin/env python3
"""TWO DEVICES, ONE CHAT, FOR REAL.

check-chat drives the dock on a single page with a stubbed Firestore,
which proves the panel builds and the writes are shaped right. It does
not prove that a chat WORKS: that one person can start one, invite
somebody, and have that somebody actually get in and talk. Reported
directly - "the join invite buttons don't work, you can't actually
click them" - and the single-page check had nothing to say about it,
because there was no second person to click anything.

So this is two real browser tabs against the shared fake Firestore that
check-vroom already uses: one localStorage-backed store both tabs read
and write, with listeners that fire across them. Every step is the
app's own path - the dock's own buttons, clicked.
"""
import argparse, functools, http.server, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The fake Firestore lives in check-vroom and is lifted rather than
# copied: two of them would drift, and the one that drifts is always
# the copy nobody is looking at.
_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)

FAILS = []
def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -> " + str(detail)) if detail else ""))
    if not ok: FAILS.append(name)

def serve(path):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port

SEED = json.dumps({"onboardingComplete": True, "tourRev": 99, "seenSettingsTour": True,
                   "avatarChar": "ninja", "points": 9000, "leaderboardOptIn": True})

def main(src):
    srv, url = serve(src)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            # ONE CONTEXT, so both tabs share the localStorage the fake
            # Firestore is built on - that sharing IS the network here.
            ctx = br.new_context(viewport={"width": 440, "height": 956})
            ctx.add_init_script(FAKE)
            ctx.add_init_script(
                "try{localStorage.setItem('class26e.frame.ok','go-live-1');"
                "localStorage.setItem('class26e.intro.seen','9');}catch(e){}")
            errs = []

            def tab(name, pub):
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: errs.append(name + ": " + str(e)[:140]))
                pg.goto(url); pg.wait_for_timeout(2600)
                pg.evaluate("""(a)=>{
                  document.getElementById('splashscreen')?.remove();
                  __useFake();
                  /* Each tab is its OWN person. publicIdOf() mints one and
                     saves it into the shared localStorage, so without this
                     the second tab boots as the SAME account - the exact
                     trap check-vroom already carries a note about. */
                  store.onboardingComplete = true;
                  store.firstName = a.name;
                  store.publicId = a.pub;
                  store.tourRev = 99;
                  syncCode = 'SYNC-' + a.pub;
                  try{ localStorage.removeItem('class26e.chatroom'); }catch(e){}
                  chatRoomCode = null; chatMyKey = null;
                  showHome();}""", {"name": name, "pub": pub})
                pg.wait_for_timeout(500)
                return pg

            a = tab("Madison", "aaa0000000001")
            b = tab("Alex", "bbb0000000002")

            # They are friends, both ways, the way the board delivers it.
            for pg, me, them, thename in ((a, "aaa0000000001", "bbb0000000002", "Alex"),
                                          (b, "bbb0000000002", "aaa0000000001", "Madison")):
                pg.evaluate("""(x)=>{
                  store.friendsIn = [x.them]; store.friendsOut = []; store.friendsDeclined = [];
                  leaderboardRows = [
                    { pub:x.me, firstName:'me', facc:[x.them], freq:[], level:1, badges:0, hundos:0 },
                    { pub:x.them, firstName:x.thename, facc:[x.me], freq:[], level:1, badges:0, hundos:0 }
                  ];}""", {"me": me, "them": them, "thename": thename})

            print("\n1. Madison starts a chat from the dock")
            started = a.evaluate("""()=>{
              document.getElementById('chatdock-btn').click();
              const s=[...document.querySelectorAll('.chatdock-act')]
                .find(x=>x.textContent==='Start a chat');
              if(!s) return {no:'no Start a chat button'};
              s.click();
              return new Promise(r=>setTimeout(()=>r({code:chatRoomCode,
                input:!!document.querySelector('.chatdock-chathost .vroom-chat-input')}),400));}""")
            check("the chat room is created", bool(started.get("code")), started)
            check("and she can type in it", started.get("input") is True, started)

            print("\n2. she invites Alex, and Alex is told")
            a.evaluate("""()=>{
              [...document.querySelectorAll('.chatdock-mini')]
                .find(x=>x.textContent==='Invite').click();}""")
            a.wait_for_timeout(400)
            # A CHECK THAT ASKS "IS IT IN THE DOM" CANNOT FAIL ON "YOU
            # CANNOT SEE IT". The sheet is built at opacity:0 and faded
            # in by a class added on the next frame; two of the three
            # sheets never added it, so this one mounted invisible at
            # z-index 340 - present, interactive, and reported as "the
            # invite button doesn't work". Opacity is the only thing
            # that differs between the two builds: hit testing does not
            # care about it, so elementFromPoint passes either way.
            vis = a.evaluate("""()=>{
              const o=document.querySelector('.invite-overlay');
              if(!o) return {no:'no sheet at all'};
              return {op:Number(getComputedStyle(o).opacity),
                      shown:o.classList.contains('invite-overlay-show')};}""")
            check("the invite sheet is actually VISIBLE",
                  not vis.get("no") and (vis.get("op") or 0) > 0.5, vis)
            inv = a.evaluate("""()=>{
              const b=[...document.querySelectorAll('.invite-sheet .friend-act')][0];
              if(!b) return {no:'nobody to invite'};
              b.click();
              return {label:b.textContent, out:JSON.parse(JSON.stringify(store.chatInvitesOut||{}))};}""")
            check("the invite sheet lists a friend", not inv.get("no"), inv)
            # And it must not survive a screen change: it is on <body>,
            # so nothing else would ever take it off.
            gone = a.evaluate("""()=>{ showProfile(); return new Promise(r=>
              setTimeout(()=>r({left:document.querySelectorAll('.invite-overlay').length}),300));}""")
            check("and it clears itself on navigation", gone.get("left") == 0, gone)
            a.evaluate("()=>{ showHome(); }")
            a.wait_for_timeout(300)
            check("and inviting records it against them",
                  "bbb0000000002" in (inv.get("out") or {}), inv.get("out"))

            # The invite rides Madison's own board row. Hand Alex the row
            # the way a snapshot would.
            code = started["code"]
            b.evaluate("""(x)=>{
              leaderboardRows = [
                { pub:x.me, firstName:'Alex', facc:[x.them], freq:[], level:1, badges:0, hundos:0 },
                { pub:x.them, firstName:'Madison', facc:[x.me], freq:[], level:1, badges:0, hundos:0,
                  cinv: { [x.me]: { code:x.code, at:Date.now() } } }
              ];}""", {"me": "bbb0000000002", "them": "aaa0000000001", "code": code})

            print("\n3. Alex sees it in Notifications and JOINS by tapping it")
            seen = b.evaluate("""()=>{
              document.getElementById('chatdock-btn').click();
              chatDockTab='notifs'; syncChatDock();
              const rows=[...document.querySelectorAll('.chatdock-notif')];
              const join=[...document.querySelectorAll('.chatdock-notif .chatdock-mini')]
                .find(x=>x.textContent==='Join');
              return {rows:rows.length, hasJoin:!!join,
                      joinH: join?Math.round(join.getBoundingClientRect().height):0,
                      text:(rows[0]||{}).textContent||''};}""")
            check("the invite is in his notifications", seen["rows"] >= 1, seen)
            check("with a Join he can actually hit", seen["hasJoin"] and seen["joinH"] >= 44, seen)

            joined = b.evaluate("""()=>{
              [...document.querySelectorAll('.chatdock-notif .chatdock-mini')]
                .find(x=>x.textContent==='Join').click();
              return new Promise(r=>setTimeout(()=>r({
                code: chatRoomCode,
                input: !!document.querySelector('.chatdock-chathost .vroom-chat-input')}), 700));}""")
            check("tapping Join puts him in the room", joined.get("code") == code, joined)
            check("and he can type in it", joined.get("input") is True, joined)

            print("\n4. they can actually talk")
            a.evaluate("""()=>{
              const i=document.querySelector('.chatdock-chathost .vroom-chat-input');
              i.value='are you studying tonight';
              document.querySelector('.chatdock-chathost .vroom-chat-send').click();}""")
            b.wait_for_timeout(900)
            got = b.evaluate("""()=>{
              const l=document.querySelector('.chatdock-chathost .vroom-chat-list');
              return {text:(l?l.textContent:''), n:document.querySelectorAll('.chatdock-chathost .vroom-chat-msg').length};}""")
            check("Alex receives what Madison sent",
                  "are you studying tonight" in got["text"], got["text"][:70])

            b.evaluate("""()=>{
              const i=document.querySelector('.chatdock-chathost .vroom-chat-input');
              i.value='yep, unit nine';
              document.querySelector('.chatdock-chathost .vroom-chat-send').click();}""")
            a.wait_for_timeout(900)
            back = a.evaluate("""()=>{
              const l=document.querySelector('.chatdock-chathost .vroom-chat-list');
              const names=[...document.querySelectorAll('.chatdock-chathost .vroom-chat-msg-name')]
                .map(n=>getComputedStyle(n).color);
              return {text:(l?l.textContent:''), colours:names,
                      distinct:new Set(names).size===names.length};}""")
            check("and Madison receives his reply", "yep, unit nine" in back["text"], back["text"][:70])
            check("with the two of them in different colours",
                  back["distinct"] is True, back["colours"])

            print("\n5. leaving takes him out of it")
            b.evaluate("""()=>{
              [...document.querySelectorAll('.chatdock-mini')]
                .find(x=>x.textContent==='Leave').click();}""")
            a.wait_for_timeout(1000)
            left = a.evaluate("""()=>{
              const w=document.getElementById('chatdock-roomwho');
              return {who:(w?w.textContent:''), mine:chatRoomCode};}""")
            check("Madison's roster drops back to one",
                  "Just you" in left["who"], left)
            check("and her own chat is untouched", left["mine"] == code, left)

            real = [e for e in errs if not any(k in e.lower() for k in
                    ("firebase", "firestore", "gstatic", "failed to fetch", "net::"))]
            check("no JS errors on either device", not real, real[:2])
            br.close()
    finally:
        srv.shutdown()

ap = argparse.ArgumentParser(); ap.add_argument("--against")
args = ap.parse_args()
main(args.against or ROOT)
print("\n%s  (%d failure(s))" %
      ("ALL PASS" if not FAILS else "FAILED: " + ", ".join(FAILS), len(FAILS)))
sys.exit(1 if FAILS else 0)
