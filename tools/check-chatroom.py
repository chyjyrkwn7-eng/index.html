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

SEED = json.dumps({"onboardingComplete": True, "tourRev": 99, "rankMapFx244": True, "seenSettingsTour": True,
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
                "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');}catch(e){}")
            errs = []

            def tab(name, pub, late=False):
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
                  /* A GATE'S FIXTURE CARRIES ITS TOUR FLAGS. Without
                     them the Leaderboard's own tour starts inside the
                     check and its dim refuses every banner - which
                     fails a check that has nothing to do with tours. */
                  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour',
                   'seenRewardsTour','seenSettingsTour','seenUnitOptionsTour',
                   'seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
                  syncCode = 'SYNC-' + a.pub; cloudConfirmedFor = syncCode;  /* read done, as on a real launch (build 296 guard) */
                  try{ localStorage.removeItem('class26e.chatroom'); }catch(e){}
                  chatRoomCode = null; chatMyKey = null;
                  showHome();}""", {"name": name, "pub": pub})
                pg.wait_for_timeout(500)
                return pg

            a = tab("Madison", "aaa0000000001")
            b = tab("Alex", "bbb0000000002")

            print("\n0. the board listener attaches even though the SDK was late")
            # BOTH FIREBASE TAGS CARRY `defer`, so fbDb is guaranteed to
            # be null when the boot code runs - the file says so itself.
            # attachInviteWatcher used to be `if(!fbDb) return;` with
            # nothing trying again, so at launch it hit that return every
            # single time and the watcher only ever appeared if Home was
            # mounted a second time by hand. That is "the invites don't
            # show immediately at all, they randomly show up".
            #
            # This boots a third tab the way a real device boots - no
            # fbDb - and then lets the SDK arrive, with nothing calling
            # showHome() again afterwards.
            c = ctx.new_page()
            c.goto(url); c.wait_for_timeout(2600)
            cold = c.evaluate("""(a)=>{
              document.getElementById('splashscreen')?.remove();
              /* Deliberately NOT __useFake() yet: this is the state
                 every real launch is in. */
              store.onboardingComplete = true;
              store.firstName = a.name; store.publicId = a.pub;
              store.tourRev = 99;
              ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour',
               'seenRewardsTour','seenSettingsTour','seenUnitOptionsTour',
               'seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
              syncCode = 'SYNC-' + a.pub; cloudConfirmedFor = syncCode;  /* read done, as on a real launch (build 296 guard) */
              showHome();
              return new Promise(r=>setTimeout(()=>r({
                db: !!fbDb, watching: !!inviteWatchUnsub}), 400));}""",
              {"name": "Cold", "pub": "ccc0000000003"})
            check("it boots with no SDK, like a real launch",
                  cold.get("db") is False, cold)
            check("and the board has not been read yet", cold.get("watching") is False, cold)
            late = c.evaluate("""()=>{
              /* The SDK arriving, the way the real loader announces it. */
              __useFake();
              const pending = fbReadyCallbacks.splice(0);
              pending.forEach(cb => { try{ cb(); }catch(e){} });
              return new Promise(r=>setTimeout(()=>r({
                watching: (leaderboardRows||[]).length > 0,
                rows: (leaderboardRows||[]).length}), 900));}""")
            check("the board is fetched once the SDK arrives",
                  late.get("watching") is True, late)
            c.close()

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
              /* Build 240: group chats have their own tab. */
              const gt=document.querySelector('.chatdock-tab[data-tab="groups"]');
              if(gt) gt.click();
              const s=[...document.querySelectorAll('.chatdock-act')]
                .find(x=>/^Start a group chat$/.test(x.textContent));
              if(!s) return {no:'no Start a group chat button'};
              s.click();
              return new Promise(r=>setTimeout(()=>r({code:chatRoomCode,
                input:!!document.querySelector('.chatdock-chathost .vroom-chat-input')}),400));}""")
            check("the chat room is created", bool(started.get("code")), started)
            check("and she can type in it", started.get("input") is True, started)

            print("\n2. she invites Alex, and Alex is told")
            # A BACKGROUND TAB DOES NOT RUN CSS TRANSITIONS, so computed
            # opacity stays at the start value however correct the class
            # is - the sheet's visibility can only be measured on a page
            # that is actually being painted.
            a.bring_to_front()
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
            # A COOLDOWN, NOT A ONE-SHOT. The button used to stay
            # disabled for the whole life of the chat, so somebody who
            # missed an invite could never be asked again. Thirty
            # seconds, and it re-enables itself.
            cool = a.evaluate("""()=>{
              const b=[...document.querySelectorAll('.invite-sheet .friend-act')][0];
              const held = {label:b.textContent, off:b.disabled};
              /* Rewind the invite past the window rather than waiting
                 30 real seconds, then let the button's own tick run. */
              store.chatInvitesOut[Object.keys(store.chatInvitesOut)[0]].at =
                Date.now() - 31000;
              return new Promise(r=>setTimeout(()=>r(Object.assign(held,
                {after:b.textContent, stillOff:b.disabled})), 1400));}""")
            check("inviting starts a visible countdown",
                  cool["off"] and "s" in cool["label"] and cool["label"] != "Invited",
                  cool)
            check("and after 30s they can be invited again",
                  cool["stillOff"] is False and cool["after"] == "Invite", cool)
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

            b.bring_to_front()
            print("\n2b. and it reaches him while he is NOT on the main menu")
            # THE BUTTON IS ON EVERY SCREEN, SO WHAT IT COUNTS HAS TO BE
            # TOO. The board snapshot used to announce only while the
            # current screen was "home", and did not look at chat
            # invites at all - so one arriving on the Leaderboard, in
            # Settings or mid-test produced nothing until the next Home
            # mount. Reported exactly that way.
            #
            # Nothing here calls checkChatInvites(). The invite is
            # written into the shared fake the way a real client writes
            # it, and Alex's own board listener is what has to notice -
            # which is the whole point, because that listener is where
            # the bug was.
            away = b.evaluate("""()=>{
              closeChatDock();
              document.getElementById('chat-invite')?.remove();
              chatInviteSeen = 0;
              showRankings();
              return new Promise(r=>setTimeout(()=>r({
                screen: (stage.firstElementChild && stage.firstElementChild.dataset)
                        ? (stage.firstElementChild.dataset.screen || '') : '',
                watching: (leaderboardRows||[]).length > 0}), 700));}""")
            check("he is off the main menu", away.get("screen") != "home", away)
            check("and he has board data to fall back on", away.get("watching") is True, away)

            # A FRESH INVITE, SENT THROUGH THE APP'S OWN BUTTON, while
            # Alex is sitting on the Leaderboard. Nothing here touches
            # his board or calls a check by hand: his MAILBOX listener
            # is the only thing that can produce this banner.
            a.evaluate("""(x)=>{
              store.chatInvitesOut[x.them].at = Date.now() - 60000;
              inviteFriendToChat(x.them);}""", {"them": "bbb0000000002"})
            b.wait_for_timeout(1500)
            fired = b.evaluate("""()=>({
              banner: !!document.getElementById('chat-invite'),
              box: Object.keys(inboxMsgs || {}).length,
              rows: (leaderboardRows||[]).length,
              dot: (document.getElementById('chatdock-dot')||{}).hidden === false,
              count: (document.getElementById('chatdock-dot')||{}).textContent || ''})""")
            check("it lands in his mailbox", fired.get("box", 0) >= 1, fired)
            check("the invite banner fires off the main menu too",
                  fired.get("banner") is True, fired)
            check("and the button carries the count there", fired.get("dot") is True, fired)
            b.evaluate("()=>{ document.getElementById('chat-invite')?.remove(); showHome(); }")
            b.wait_for_timeout(700)

            print("\n2c. and it arrives through his own mailbox, not the board")
            # THE POINT OF THE MAILBOX. An invite addressed to Alex now
            # goes into vrooms/inbox-<his id>, which only his device
            # listens to - instead of into Madison's leaderboard row,
            # which every phone in the class had to watch. This proves
            # delivery with the class-wide board listener DETACHED and
            # leaderboardRows emptied: if anything still depends on the
            # board, nothing arrives.
            mail = b.evaluate("""(x)=>{
              leaderboardRows = [];
              document.getElementById('chat-invite')?.remove();
              chatInviteSeen = 0;
              /* He still knows who his friends are from his own store. */
              store.friendsIn = [x.them];
              return new Promise(r=>setTimeout(()=>r({
                box: Object.keys(inboxMsgs || {}).length,
                invites: incomingChatInvites().length,
                rows: (leaderboardRows||[]).length,
                watching: typeof inviteWatchUnsub !== "undefined" && !!inviteWatchUnsub}), 700));}""",
                {"them": "aaa0000000001"})
            check("no class-wide board listener is held at all",
                  mail.get("watching") is False, mail)
            check("and the board itself is empty", mail.get("rows") == 0, mail)
            check("his mailbox still has the invite in it", mail.get("box", 0) >= 1, mail)
            check("and the app still sees it as an invite",
                  mail.get("invites", 0) >= 1, mail)

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

            print("\n3b. they can SEE each other in it")
            # "People aren't showing in the chat if they do manage to
            # join." They had joined - the header said "2 in this chat"
            # and named nobody, so there was nothing on screen with
            # their name on it. A count is not a roster.
            who = a.evaluate("""()=>new Promise(r=>setTimeout(()=>r({
              names: [...document.querySelectorAll('.chatdock-who-name')].map(x=>x.textContent),
              arts: document.querySelectorAll('.chatdock-who-art').length}), 900))""")
            check("Madison's roster names the people in the chat",
                  "Alex" in (who.get("names") or []), who)
            check("with her own entry in it too",
                  "You" in (who.get("names") or []), who)
            check("and each one carries their character",
                  who.get("arts") == len(who.get("names") or []), who)

            print("\n3c. and somebody who vanishes stops being listed")
            # A LEAVE IS THE ONE EXIT THAT WRITES ANYTHING. Closing the
            # app, locking the phone and losing signal write nothing, so
            # the entry sat there forever and everybody waited on a
            # person who was gone. Presence gives it a shelf life: the
            # stamp is rewound past the window here rather than waiting
            # a real minute.
            stale = a.evaluate("""(x)=>{
              const ref = window.__fakeDb.collection('vrooms').doc(x.code);
              return ref.get().then(sn=>{
                const d = sn.data();
                Object.keys(d.participants).forEach(k=>{
                  if(k !== chatMyKey) d.participants[k].seen = Date.now() - 300000;
                });
                return ref.set(d);
              }).then(()=>new Promise(r=>setTimeout(()=>r({
                names: [...document.querySelectorAll('.chatdock-who-name')].map(x=>x.textContent),
                away: [...document.querySelectorAll('.chatdock-who.is-away .chatdock-who-name')].map(x=>x.textContent),
                count: (document.getElementById('chatdock-roomcount')||{}).textContent||'',
                text: (document.getElementById('chatdock-roomwho')||{}).textContent||''
              }), 900)));}""", {"code": code})
            # ---- THIS ENCODED A DECISION, AND IT CHANGED (build 240) ----
            # "Ensure it will be easy to always tell who's currently in the
            # group chat." A member whose phone slept used to vanish from
            # the roster, so a group of four read as a group of one. They
            # are still a member: shown, dimmed as away, and counted apart
            # from the people here now. Leaving (section 5) still removes.
            check("a stale classmate is shown as away, not dropped",
                  "Alex" in (stale.get("away") or []), stale)
            check("and the header says how many are here now",
                  "1 here now" in (stale.get("count") or ""), stale)
            # And put him back, so section 4 still has two people in it.
            a.evaluate("""(x)=>{
              const ref = window.__fakeDb.collection('vrooms').doc(x.code);
              return ref.get().then(sn=>{
                const d = sn.data();
                Object.keys(d.participants).forEach(k=>{ d.participants[k].seen = Date.now(); });
                return ref.set(d);
              });}""", {"code": code})
            a.wait_for_timeout(700)

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

            print("\n4a. who is typing: one row each, and accurate")
            # ---- BUILD 240, Madison: "The 'someone is typing' thing ensure
            # it works well and it's accurate, if multiple people are typing
            # at once just stack them so you can see both." Written against
            # build 239, which said "Alex and Sam are typing", kept saying it
            # after the message landed, and trusted the sender's clock.
            rows = lambda pg: pg.evaluate("""()=>[...document.querySelectorAll('.chatdock-chathost .vroom-chat-typer')].map(r=>r.textContent)""")
            b.evaluate("""()=>{ const i=document.querySelector('.chatdock-chathost .vroom-chat-input');
              i.value='hold on'; i.dispatchEvent(new Event('input', {bubbles:true})); }""")
            # A third person, typing, whose phone clock is a minute behind:
            # their stamp is old by this device's clock, but it is CHANGING.
            a.evaluate("""async (c)=>{ const ref = fbDb.collection('vrooms').doc(c);
              await ref.update({ 'typing.ccc0000000003': Date.now() - 60000 });
              await new Promise(r => setTimeout(r, 500));
              await ref.update({ 'typing.ccc0000000003': Date.now() - 59500 }); }""", code)
            # Wait on the page, not a timer: under load Alex's keystroke can
            # take longer than a fixed 1.3s to reach this device, and a
            # fixed wait then reads one row and fails a build that is fine.
            # A genuinely missing row still fails once the 5s are up.
            a.wait_for_timeout(1300)
            for _ in range(25):
                if len(rows(a)) >= 2: break
                a.wait_for_timeout(150)
            both = rows(a)
            check("two people typing at once are two rows, not one sentence",
                  len(both) == 2 and all("is typing" in r for r in both), both)
            check("a skewed clock does not hide somebody who is typing",
                  any("Alex" not in r for r in both) and len(both) == 2, both)
            b.evaluate("""()=>{ document.querySelector('.chatdock-chathost .vroom-chat-send').click(); }""")
            a.wait_for_timeout(700)
            after = rows(a)
            check("Alex's row goes the moment his message lands",
                  not any("Alex" in r for r in after), after)
            b.evaluate("""()=>{ const i=document.querySelector('.chatdock-chathost .vroom-chat-input');
              i.value='x'; i.dispatchEvent(new Event('input', {bubbles:true})); }""")
            a.wait_for_timeout(900)
            typed = rows(a)
            b.evaluate("""()=>{ const i=document.querySelector('.chatdock-chathost .vroom-chat-input');
              i.value=''; i.dispatchEvent(new Event('input', {bubbles:true})); }""")
            a.wait_for_timeout(900)
            cleared = rows(a)
            check("and when he empties the box instead of sending",
                  any("Alex" in r for r in typed) and not any("Alex" in r for r in cleared), [typed, cleared])
            a.evaluate("""(c)=>fbDb.collection('vrooms').doc(c).update({ 'typing.ccc0000000003': firebase.firestore.FieldValue.delete() })""", code)

            print("\n4b. long text wraps; it never scrolls sideways")
            a.evaluate("""()=>{
              const i=document.querySelector('.chatdock-chathost .vroom-chat-input');
              /* No spaces at all - a pasted code or a link, which is the
                 case that actually broke: a run with no break
                 opportunity sets the width of the whole list unless the
                 item is told it may break anywhere. */
              i.value='WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW';
              document.querySelector('.chatdock-chathost .vroom-chat-send').click();}""")
            a.wait_for_timeout(700)
            wrapM = a.evaluate("""()=>{
              const l=document.querySelector('.chatdock-chathost .vroom-chat-list');
              const over = [...l.querySelectorAll('.vroom-chat-msg')]
                .map(n=>Math.round(n.getBoundingClientRect().width - l.clientWidth));
              return { sideways: l.scrollWidth - l.clientWidth,
                       widest: over.length ? Math.max.apply(null, over) : 0,
                       lines: l.scrollHeight };}""")
            check("the list does not scroll sideways", wrapM["sideways"] <= 0, wrapM)
            check("and no message is wider than the list", wrapM["widest"] <= 0, wrapM)

            print("\n4c. five reactions, and a reaction bumps its message")
            react = a.evaluate("""()=>{
              const l=document.querySelector('.chatdock-chathost .vroom-chat-list');
              const wraps=[...l.querySelectorAll('.vroom-chat-msgwrap')];
              if(!wraps.length) return { none:true };
              /* The FIRST message, so the bump has somewhere to move it
                 to - reacting to the last one proves nothing. */
              const first = wraps[0];
              const textBefore = first.textContent;
              first.click();
              const pick = l.querySelector('.vroom-chat-picker');
              const glyphs = pick ? [...pick.querySelectorAll('.vroom-chat-pick')]
                .map(b=>b.getAttribute('aria-label')) : null;
              const tall = pick ? [...pick.querySelectorAll('.vroom-chat-pick')]
                .map(b=>Math.round(b.getBoundingClientRect().height)) : [];
              if(pick) pick.querySelectorAll('.vroom-chat-pick')[1].click();
              return { glyphs, tall, textBefore,
                       stillOpen: !!l.querySelector('.vroom-chat-picker') };}""")
            check("tapping a message offers five reactions",
                  react.get("glyphs") and len(react["glyphs"]) == 5, react.get("glyphs"))
            check("each one is a 44px target",
                  react.get("tall") and min(react["tall"]) >= 44, react.get("tall"))
            check("and the picker closes once you pick",
                  react.get("stillOpen") is False)
            a.wait_for_timeout(800); b.wait_for_timeout(800)
            after = b.evaluate("""(before)=>{
              const l=document.querySelector('.chatdock-chathost .vroom-chat-list');
              const wraps=[...l.querySelectorAll('.vroom-chat-msgwrap')];
              const chips=[...l.querySelectorAll('.vroom-chat-react')].map(c=>c.textContent);
              return { last: wraps.length ? wraps[wraps.length-1].textContent : '',
                       first: wraps.length ? wraps[0].textContent : '',
                       chips, n: wraps.length };}""", react.get("textBefore"))
            check("the other person sees the reaction", len(after["chips"]) == 1, after["chips"])
            """The bump is the whole ask - "it bumps the message to the
            bottom, Snapchat style" - so what matters is that the
            message that WAS first is now last, on the other device."""
            check("and the message it was left on has moved to the bottom",
                  "are you studying tonight" in (after["last"] or ""), after["last"][:60])
            undo = a.evaluate("""()=>{
              const l=document.querySelector('.chatdock-chathost .vroom-chat-list');
              const wraps=[...l.querySelectorAll('.vroom-chat-msgwrap')];
              const mine = wraps.filter(w=>w.querySelector('.vroom-chat-react.is-mine'))[0];
              if(!mine) return { noMine:true };
              mine.click();
              const pick = l.querySelector('.vroom-chat-picker');
              if(pick) pick.querySelectorAll('.vroom-chat-pick')[1].click();
              return { ok:true };}""")
            a.wait_for_timeout(800)
            gone = a.evaluate("""()=>document.querySelectorAll(
              '.chatdock-chathost .vroom-chat-react').length""")
            """A CHECK THAT CANNOT FAIL IS WORSE THAN NO CHECK. `gone ==
            0` passed against the build with no reactions at all, where
            there was nothing to take back - so it has to assert the
            TRANSITION: one chip before, none after, and a reaction
            actually found to undo."""
            check("your own reaction is yours to take back",
                  not undo.get("noMine") and len(after["chips"]) == 1 and gone == 0,
                  {"before": after["chips"], "after": gone, "found": not undo.get("noMine")})

            print("\n4d. notifications say what is true")
            """WRAPPED, SO THE BUILD THAT LACKS THESE FAILS RATHER THAN
            THROWS. A gate that dies on the build it was written against
            never reaches the checks that matter - it just reports one
            stack trace where there should be six red lines."""
            notif = a.evaluate("""()=>{
              try{
              if(typeof timeAgo !== 'function') throw new Error('no timeAgo');
              if(typeof withMeInChat !== 'function') throw new Error('no withMeInChat');
              const out = {};
              /* ---- an age on every row that has a timestamp ---- */
              out.ago = {
                now:   timeAgo(Date.now() - 5000),
                mins:  timeAgo(Date.now() - 12 * 60000),
                hours: timeAgo(Date.now() - 3 * 3600000),
                days:  timeAgo(Date.now() - 4 * 86400000),
                none:  timeAgo(0)
              };
              /* ---- already in this chat with me ---- */
              const them = 'them-01';
              out.withBefore = withMeInChat(them);
              liveChatParticipants = {};
              liveChatParticipants[chatMyKey] = { name:'Madison' };
              liveChatParticipants[them] = { name:'Alex' };
              out.withAfter = withMeInChat(them);
              out.notMe = withMeInChat(chatMyKey);
              /* ---- their stale invite drops out of the list ---- */
              const stamp = Date.now() - 9 * 60000;
              /* SHAPED THE WAY sendToInbox() WRITES IT, including `pub`:
                 incomingChatInvites() filters on m.pub, so a fixture
                 without it lists nothing and every check below passes
                 against zero. A first draft did exactly that. */
              inboxMsgs = { [them]: { pub: them, type:'chat', code:'ZZZZ-9999',
                                      at: stamp, firstName:'Alex', avatarChar:'ninja' } };
              /* AN INVITE IS ONLY LISTED IF IT IS FROM A FRIEND -
                 incomingChatInvites() filters on friendPublicIds(), so a
                 fixture that skips this lists nothing and the "it
                 disappeared" check below passes against zero. Caught by
                 the listedWhenApart guard rather than by reading the
                 code, which is the point of having it. */
              store.friendsIn = [them];
              leaderboardRows = [{ pub: them, firstName:'Alex', avatarChar:'ninja',
                                   level:9, badges:1, seenAt: Date.now() }];
              liveChatParticipants = null;   /* not with me yet */
              const before = notificationItems().filter(i => i.kind === 'chat');
              out.listedWhenApart = before.length;
              out.listedAt = before.length ? before[0].at : 0;
              liveChatParticipants = {};
              liveChatParticipants[chatMyKey] = { name:'Madison' };
              liveChatParticipants[them] = { name:'Alex' };
              /* Build 240, Madison: "if I'm in a group chat with a
                 person, they invite me to another, the notification will
                 be there". So an invite to a DIFFERENT chat stays... */
              out.listedWhenTogether =
                notificationItems().filter(i => i.kind === 'chat').length;
              /* ...and one for the chat you are already in goes. */
              inboxMsgs = { [them]: { pub: them, type:'chat', code: chatRoomCode,
                                      at: stamp, firstName:'Alex', avatarChar:'ninja' } };
              out.listedForThisChat =
                notificationItems().filter(i => i.kind === 'chat').length;
              return out;
              } catch(e){ return { threw: String(e) }; }}""")
            print("     ", json.dumps(notif))
            if notif.get("threw"):
                for n in ("an age reads in minutes, hours and days",
                          "somebody in the chat with me is recognised as such",
                          "and I am never 'with' myself",
                          "their invite is listed while we are apart",
                          "and carries the time it arrived",
                          "an invite to a DIFFERENT chat stays while we are in one together",
                          "and drops out the moment we are in the chat it is for"):
                    check(n, False, notif["threw"])
                notif = None
            if notif:
                check("an age reads in minutes, hours and days",
                      notif["ago"]["now"] == "just now" and notif["ago"]["mins"] == "12m ago"
                      and notif["ago"]["hours"] == "3h ago" and notif["ago"]["days"] == "4d ago"
                      and notif["ago"]["none"] == "", notif["ago"])
                check("somebody in the chat with me is recognised as such",
                      notif["withBefore"] is False and notif["withAfter"] is True,
                      [notif["withBefore"], notif["withAfter"]])
                check("and I am never 'with' myself", notif["notMe"] is False)
                """The row has to be there to begin with, or 'it disappeared'
                is a check that cannot fail - which this file has already
                been caught by once."""
                check("their invite is listed while we are apart",
                      notif["listedWhenApart"] == 1, notif["listedWhenApart"])
                check("and carries the time it arrived", notif["listedAt"] > 0, notif["listedAt"])
                check("an invite to a DIFFERENT chat stays while we are in one together",
                      notif["listedWhenTogether"] == 1, notif["listedWhenTogether"])
                check("and drops out the moment we are in the chat it is for",
                      notif.get("listedForThisChat") == 0, notif.get("listedForThisChat"))

            print("\n4e. a join that fails keeps its invitation")
            failed = a.evaluate("""async ()=>{
              /* A code that is not there at all: joinChatRoom must say
                 so AND report it, rather than leaving the caller to
                 assume it worked. */
              const bad = await Promise.resolve(joinChatRoom('QQQQ-0000'));
              /* And a Virtual Room code handed to the chat joiner. */
              const wrongKind = await Promise.resolve(joinChatRoom(''));
              return { bad, wrongKind };}""")
            check("joining a chat that is not there resolves false",
                  failed["bad"] is False, failed)
            check("and so does joining nothing at all",
                  failed["wrongKind"] is False, failed)
            inv = a.evaluate("""()=>{
              try{
              if(typeof withMeInChat !== 'function') throw new Error('no withMeInChat');
              const them = 'them-02';
              liveChatParticipants = {};
              liveChatParticipants[chatMyKey] = { name:'Madison' };
              liveChatParticipants[them] = { name:'Alex' };
              let said = null;
              const realToast = window.showToast;
              window.showToast = (m) => { said = m; };
              store.chatInvitesOut = {};
              inviteFriendToChat(them);
              window.showToast = realToast;
              return { said, sent: !!(store.chatInvitesOut || {})[them] };
              } catch(e){ return { threw: String(e) }; }}""")
            check("inviting somebody already in the chat is refused",
                  not inv.get("threw") and inv.get("sent") is False
                  and "already" in (inv.get("said") or "").lower(), inv)

            print("\n5. leaving takes him out of it")
            # Build 240: Leave asks first. Tapping it must only ask, Stay
            # must keep him in, and only the card's own Leave leaves.
            asked = b.evaluate("""async ()=>{
              const leave = () => [...document.querySelectorAll('.chatdock-mini')].find(x=>x.textContent==='Leave');
              leave().click();
              const card = document.querySelector('.chatdock-confirm');
              const out = { asked: !!card, title: card ? (card.querySelector('#chatdock-confirm-title') || {}).textContent || '' : '',
                            stillIn: !!chatRoomCode };
              document.querySelector('.chatdock-confirm-stay')?.click();
              await new Promise(r => setTimeout(r, 200));
              out.stayKept = !!chatRoomCode && !document.querySelector('.chatdock-confirm');
              leave().click();
              document.querySelector('.chatdock-confirm-leave')?.click();
              return out; }""")
            check("Leave asks before it leaves", asked.get("asked") is True and asked.get("stillIn") is True, asked)
            check("and Stay keeps him in the chat", asked.get("stayKept") is True, asked)
            a.wait_for_timeout(1000)
            left = a.evaluate("""()=>{
              const w=document.getElementById('chatdock-roomwho');
              return {who:(w?w.textContent:''), mine:chatRoomCode};}""")
            check("Madison's roster drops back to one",
                  "Just you" in left["who"], left)
            check("and her own chat is untouched", left["mine"] == code, left)

            print("\n6. more than one chat, and a list to get back into them")
            # ---- WRITTEN AGAINST THE BUILD WITH ONE CHAT AND ONE WAY OUT ----
            # Before this the only exit from a chat was Leave, which
            # deleted your participation - so "go back to the other one"
            # meant burning the one you were in. Every assertion here is
            # false on that build, and the evaluate is wrapped because
            # the helpers it calls do not exist there at all: a gate that
            # THROWS on the old build reports one failure about a
            # ReferenceError instead of six about the feature.
            multi = a.evaluate("""async ()=>{
              try{
              if(typeof chatList !== 'function') throw new Error('no chatList');
              if(typeof closeChatRoom !== 'function') throw new Error('no closeChatRoom');
              const out = {};
              const first = chatRoomCode;
              out.first = first;
              /* A MEMBER OF IT, which is not the same as having it open. */
              out.listed = chatList().map(c => c.code);
              out.named = (chatList()[0] || {}).name || '';
              /* The way back to the list, by the app's own button. */
              const back = [...document.querySelectorAll('.chatdock-back')][0];
              out.hasBack = !!back;
              if(back) back.click();
              out.openAfterBack = chatRoomCode;
              out.rows = document.querySelectorAll('.chatdock-chatrow').length;
              /* And back in, by the row. */
              const row = document.querySelector('.chatdock-chatrow-open');
              if(row) row.click();
              out.reopened = chatRoomCode;
              out.panelBack = !!document.querySelector('.chatdock-chathost .vroom-chat-list');
              return out;
              } catch(e){ return { threw: String(e) }; }}""")
            print("     ", json.dumps(multi))
            names6 = ("a chat you are in is a chat you are a member of",
                      "it is named after who is in it, not by its code",
                      "there is a way back to the list that is not Leave",
                      "closing a chat does not leave it",
                      "the list has a row for it",
                      "and the row opens it again")
            if multi.get("threw"):
                for n in names6: check(n, False, multi["threw"])
            else:
                check(names6[0], multi["listed"] == [multi["first"]], multi["listed"])
                check(names6[1], multi["named"] and multi["named"] != multi["first"], multi["named"])
                check(names6[2], multi["hasBack"] is True)
                check(names6[3], multi["openAfterBack"] is None and multi["rows"] == 1,
                      [multi["openAfterBack"], multi["rows"]])
                check(names6[4], multi["rows"] == 1, multi["rows"])
                check(names6[5], multi["reopened"] == multi["first"] and multi["panelBack"] is True,
                      [multi["reopened"], multi["panelBack"]])

            second = a.evaluate("""async ()=>{
              try{
              if(typeof closeChatRoom !== 'function') throw new Error('no closeChatRoom');
              const out = {}; const first = chatRoomCode;
              closeChatRoom();
              /* STARTING ANOTHER MUST NOT END THE FIRST. That is the
                 whole request - "a list you can revisit". */
              createChatRoom();
              await new Promise(r => setTimeout(r, 500));
              out.second = chatRoomCode;
              out.both = chatList().map(c => c.code);
              closeChatRoom();
              out.rows = document.querySelectorAll('.chatdock-chatrow').length;
              /* THE DELETE ARMS BEFORE IT FIRES. One tap on a x beside a
                 row must not take somebody out of a conversation. */
              const rows = [...document.querySelectorAll('.chatdock-chatrow')];
              const target = rows.find(r => r.querySelector('.chatdock-chatrow-open'));
              const del = target.querySelector('.chatdock-chatrow-del');
              del.click();
              out.armed = !!document.querySelector('.chatdock-confirm');
              out.rowsAfterOneTap = document.querySelectorAll('.chatdock-chatrow').length;
              const goneCode = target.dataset.code;
              document.querySelector('.chatdock-confirm-leave')?.click();
              await new Promise(r => setTimeout(r, 400));
              out.gone = goneCode;
              out.left = chatList().map(c => c.code);
              const snap = await fbDb.collection('vrooms').doc(goneCode).get();
              const p = (snap.data() || {}).participants || {};
              out.stillIn = Object.keys(p).indexOf(publicIdOf()) >= 0;
              return out;
              } catch(e){ return { threw: String(e) }; }}""")
            print("     ", json.dumps(second))
            names7 = ("starting a second chat does not end the first",
                      "both are in the list",
                      "one tap on the x asks rather than leaving",
                      "confirming takes the row off the list",
                      "and leaves the chat for real, not just locally")
            if second.get("threw"):
                for n in names7: check(n, False, second["threw"])
            else:
                check(names7[0], second["second"] != multi.get("first")
                      and second["second"] is not None, second["second"])
                check(names7[1], len(second["both"]) == 2, second["both"])
                check(names7[2], second["armed"] is True and second["rowsAfterOneTap"] == 2,
                      [second["armed"], second["rowsAfterOneTap"]])
                check(names7[3], len(second["left"]) == 1
                      and second["gone"] not in second["left"], second["left"])
                check(names7[4], second["stillIn"] is False, second["stillIn"])

            print("\n8. four invites to one chat, one accept answers them all")
            # ---- BUILD 240, Madison: "ensure the notification disappear
            # if like 4 people invite me to the same chat and I accept one
            # of them". Being in the chat hid the other three, but only
            # while it stayed on the list: leave it and all three came
            # back. Written against build 239, where they do.
            four = a.evaluate("""async ()=>{ try{
              const wait = ms => new Promise(r => setTimeout(r, ms));
              if(chatRoomCode) closeChatRoom();
              createChatRoom(); await wait(500);
              const C = chatRoomCode;
              leaveChatRoom(true); await wait(200);
              const pubs = ['P4A','P4B','P4C','P4D'];
              store.friendsIn = pubs.slice();
              leaderboardRows = pubs.map((p, i) => ({ pub: p, firstName: 'F' + i, avatarChar: 'ninja', level: 3, seenAt: Date.now() }));
              /* INTO THE REAL MAILBOX, not into inboxMsgs. The inbox
                 listener replaces that variable on every snapshot, so a
                 fixture written straight into it is wiped by the join's
                 own writes - and "they came back" then passes on every
                 build, which is how the first draft of this passed on
                 the build it was written against. */
              const msgs = {};
              pubs.forEach((p, i) => { msgs[p] = { pub: p, type: 'chat', code: C, at: Date.now() - 1000 * (i + 1),
                                                   firstName: 'F' + i, avatarChar: 'ninja' }; });
              attachInbox();
              await inboxDocFor(publicIdOf()).set({ kind: 'inbox', msgs });
              await wait(600);
              const listed = () => notificationItems().filter(i => i.kind === 'chat').length;
              const out = { before: listed() };
              const item = notificationItems().find(i => i.kind === 'chat');
              item.act(); await wait(700);
              out.joined = chatRoomCode === C;
              out.afterAccept = listed();
              leaveChatRoom(true); await wait(200);
              out.afterLeaving = listed();
              return out; } catch(e){ return { threw: String(e) }; }}""")
            print("     ", json.dumps(four))
            check("four invites to one chat are all listed", four.get("before") == 4, four)
            check("accepting one joins the chat", four.get("joined") is True, four)
            check("and the other three go with it", four.get("afterAccept") == 0, four)
            check("and stay gone after leaving that chat later", four.get("afterLeaving") == 0, four)

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
