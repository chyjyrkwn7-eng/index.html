#!/usr/bin/env python3
"""The Virtual Room chat: colours, the unread count, and the announcement.

Every check here is written against the build that did not have them, and
--against <dir> runs it there: it has to FAIL on that build or it is
measuring nothing.

The room document is driven directly rather than through Firestore - the
SDK is blocked in the sandbox - so what is exercised is the app's own
snapshot handler, the same path a real message arrives on.
"""
import argparse, functools, http.server, io, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def serve(path):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{port}/index.html"

ROOM = """
window.__room = {
  participants: { me:{name:'Madison'}, ann:{name:'Ann'}, bo:{name:'Bo'}, cy:{name:'Cy'} },
  chatMessages: []
};
/* EVERY listener, not the last one. The lobby, the race and the chat all
   subscribe to the same room document, so a stub that kept one callback
   was driving whichever happened to subscribe last - which is how the
   first run of this check reported the chat rendering nothing at all. */
window.__snaps = [];
window.__updates = [];
window.firebase = { apps: [], initializeApp(){ window.firebase.apps.push({}); return {}; },
  firestore(){ return { collection(){ return { doc(__id){ return {
    get(){ return Promise.resolve({exists:true, data:()=>window.__room, metadata:{fromCache:false}}); },
    set(){ return Promise.resolve(); },
    update(d){ window.__updates.push({id: __id, d: d}); return Promise.resolve(); },
    delete(){ return Promise.resolve(); },
    onSnapshot(cb){ window.__snaps.push(cb);
      cb({exists:true, data:()=>window.__room, metadata:{fromCache:false}});
      return function(){}; }
  };}, where(){return this;}, orderBy(){return this;}, limit(){return this;},
     get(){return Promise.resolve({docs:[],forEach(){}});}, onSnapshot(){return function(){};} };}};}
};
window.firebase.firestore.FieldValue = { serverTimestamp(){return Date.now();}, delete(){return null;},
  arrayUnion(v){ return v; } };
window.__push = function(key, name, text){
  window.__room.chatMessages = window.__room.chatMessages.concat([
    {id:key+'-'+Date.now()+'-'+Math.random(), key:key, name:name, text:text, ts:Date.now()}]);
  window.__snaps.forEach(function(cb){
    try{ cb({exists:true, data:()=>window.__room, metadata:{fromCache:false}}); }catch(e){}
  });
};
"""

def run(src_dir, label):
    srv, url = serve(src_dir); fails = []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            ctx = br.new_context(viewport={"width": 440, "height": 956}, is_mobile=True, has_touch=True)
            ctx.add_init_script(ROOM)
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.goto(url); pg.wait_for_timeout(2400)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")
            # a lobby, with this device as 'me'
            ok = pg.evaluate("""()=>{
              if(typeof showVirtualRoomLobby !== 'function') return false;
              vroomCode = 'TESTROOM'; vroomMyKey = 'me'; vroomIsHost = true;
              showVirtualRoomLobby(); return true; }""")
            if not ok:
                fails.append("showVirtualRoomLobby is not available")
                return fails
            pg.wait_for_timeout(700)
            # three people speak while the sheet is closed
            for k, n, t in [("ann","Ann","are we starting"),("bo","Bo","one sec"),("cy","Cy","ready")]:
                pg.evaluate("([k,n,t])=>window.__push(k,n,t)", [k,n,t]); pg.wait_for_timeout(260)
            out = pg.evaluate("""()=>{
              const dot=document.querySelector('.vroom-chat-dot');
              const alert=document.querySelector('.vroom-chat-alert');
              const names=[...document.querySelectorAll('.vroom-chat-msg-name')]
                .map(n=>({t:n.textContent.trim(), c:getComputedStyle(n).color,
                          me:n.classList.contains('is-me')}));
              return {dotHidden:dot?dot.hidden:null, dotText:dot?dot.textContent:null,
                      alert: alert?alert.textContent:null,
                      alertShown: alert?alert.classList.contains('show'):false,
                      names};}""")
            print(f"  [{label}] {json.dumps(out)[:300]}")
            if out["dotHidden"] is not False: fails.append("the unread badge is not showing")
            if out["dotText"] != "3": fails.append(f"the unread badge reads {out['dotText']!r}, not a count of 3")
            if not out["alert"]: fails.append("nothing announced who sent the message")
            elif "sent a message" not in out["alert"]: fails.append(f"the announcement reads {out['alert']!r}")
            if not out["alertShown"]: fails.append("the announcement never animated in")
            others = [n for n in out["names"] if not n["me"]]
            cols = set(n["c"] for n in others)
            if len(others) < 3: fails.append(f"only {len(others)} messages rendered from other people")
            elif len(cols) != len(others):
                fails.append(f"names are not each their own colour: {sorted(cols)}")
            real = [e for e in errs if not any(k in e.lower() for k in
                    ("firebase","firestore","gstatic","failed to fetch","net::"))]
            if real: fails.append(f"JS error {real[0]}")
            br.close()
    finally:
        srv.shutdown()
    return fails


def run_class(src_dir, label):
    """The chat dock: the button on every screen, the chat lobby behind
    it, and the one place the chat is deliberately absent.

    Written against a build that had none of it, so --against fails on
    every one of these."""
    srv, url = serve(src_dir); fails = []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            ctx = br.new_context(viewport={"width": 440, "height": 956}, is_mobile=True, has_touch=True)
            # FIREBASE AVAILABLE SYNCHRONOUSLY, AND A SYNC CODE ALREADY ON
            # THE DEVICE. That pairing is what reaches the recovery path
            # from inside the top-level script, and it is how a `let`
            # declared below its caller takes the whole app down before it
            # can paint - see the note on mirroredCode. In production only
            # `defer` on the Firebase tags prevents it, which is a
            # guarantee held somewhere else entirely.
            ctx.add_init_script(ROOM)
            ctx.add_init_script(
                "try{localStorage.setItem('class26e.freshstart','1');"
                "localStorage.setItem('class26e.synccode','SECR-ETXX');"
                # The introduction card opens two seconds after Home and
                # would land on top of everything below. It has its own
                # section.
                "localStorage.setItem('class26e.intro.seen','9');}catch(e){}")
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(url); pg.wait_for_timeout(2400)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")

            booted = pg.evaluate("""()=>{
              try{ return typeof inVirtualRoom === 'boolean'; }
              catch(e){ return 'THREW: ' + e.message; }}""")
            if booted is not True:
                fails.append("the app did not finish booting with Firebase synchronous: %s" % booted)
                return fails

            seeded = pg.evaluate("""()=>{
              if(typeof showHome !== 'function') return false;
              store.onboardingComplete = true; store.firstName = 'Madison';
              store.tourRev = 99; store.publicId = 'me0000000001';
              vroomCode = null; inVirtualRoom = false;
              showHome(); return true;}""")
            if not seeded:
                fails.append("showHome is not available")
                return fails
            pg.wait_for_timeout(500)

            # 1. a real control, a circle, in the corner it was asked for
            box = pg.evaluate("""()=>{
              const b = document.getElementById('chatdock-btn');
              if(!b) return null;
              const r = b.getBoundingClientRect();
              const cs = getComputedStyle(b);
              return {x:r.x, y:r.y, w:r.width, h:r.height, radius: cs.borderRadius,
                      vw: innerWidth, vh: innerHeight};}""")
            if not box:
                fails.append("there is no chat dock button on Home")
            else:
                if box["w"] < 44 or box["h"] < 44:
                    fails.append("the chat button is %dx%d, under the 44px floor"
                                 % (round(box["w"]), round(box["h"])))
                # A CIRCLE, asked for by name - and round means square as
                # well as radiused, which is the half that quietly breaks.
                if abs(box["w"] - box["h"]) > 1 or "50%" not in (box["radius"] or ""):
                    fails.append("the chat button is not a circle: %s" % box)
                # TOP RIGHT. A quadrant rather than coordinates, which
                # would go stale the first time the inset or gap moved.
                if not (box["x"] > box["vw"] * 0.5 and box["y"] < box["vh"] * 0.2):
                    fails.append("the chat button is not in the top-right corner: %s" % box)

            # 2. a top banner parks BELOW it rather than under it
            off = pg.evaluate("""()=>{
              const b = document.getElementById('chatdock-btn');
              if(!b) return null;
              const probe = document.createElement('div');
              probe.className = 'daily-alert';
              document.body.appendChild(probe);
              const o = topNoticeOffset(probe);
              probe.remove();
              return {off: o, btnBottom: b.getBoundingClientRect().bottom};}""")
            if off and (off["off"] is None or off["off"] < off["btnBottom"]):
                fails.append("a top banner does not clear the chat button: %s" % off)

            # 3. starting a chat makes a room, and the panel binds to it
            started = pg.evaluate("""()=>{
              window.__updates.length = 0;
              document.getElementById('chatdock-btn').click();
              const start = [...document.querySelectorAll('.chatdock-act')]
                .find(b => b.textContent === 'Start a chat');
              if(!start) return {no: 'no Start a chat button'};
              start.click();
              return new Promise(r => setTimeout(() => r({
                code: chatRoomCode,
                input: !!document.querySelector('.chatdock-chathost .vroom-chat-input'),
                invite: !!([...document.querySelectorAll('.chatdock-mini')]
                  .find(b => b.textContent === 'Invite')),
                /* NO CODE ANYWHERE ON THE SCREEN. Codes were removed from
                   lobbies and chats alike - "it's all through invites
                   now" - so a room id rendered anywhere is the old flow
                   growing back. Searched as the actual string, which is
                   the only thing that catches it wherever it is put. */
                codeOnScreen: document.body.innerText.indexOf(chatRoomCode) >= 0,
                joinField: !!document.querySelector('.chatdock-joininput')}), 200));}""")
            if started.get("no"):
                fails.append(started["no"])
            else:
                if not started.get("code"):
                    fails.append("starting a chat did not put this device in a room")
                if started.get("codeOnScreen"):
                    fails.append("the chat is still showing its code on screen")
                if started.get("joinField"):
                    fails.append("there is still a join-by-code field in the chat")
                if not started.get("input"):
                    fails.append("the chat has no message field")
                # ASKED FOR BY NAME - "make sure there's an invite to chat
                # thing in there".
                if not started.get("invite"):
                    fails.append("there is no way to invite anybody to the chat")

            # 4. somebody else speaks: the dot counts it, the preview
            #    fires, and every person is a different colour
            spoke = pg.evaluate("""()=>{
              const code = chatRoomCode;
              const P = {me0000000001:{name:'Madison',joinedAt:1},
                         a2:{name:'Alex',joinedAt:2}, b3:{name:'Bo',joinedAt:3},
                         c4:{name:'Cy',joinedAt:4}};
              const cb = window.__snaps[window.__snaps.length - 1];
              const snap = (msgs) => window.__snaps.forEach(f => {
                try{ f({exists:true, metadata:{fromCache:false},
                        data:()=>({kind:'chat', participants:P, chatMessages:msgs})}); }catch(e){}});
              const t = Date.now();
              snap([]);
              closeChatDock();
              snap([{id:'m1',key:'a2',name:'Alex',text:'hey',ts:t-2},
                    {id:'m2',key:'b3',name:'Bo',text:'you coming',ts:t-1},
                    {id:'m3',key:'c4',name:'Cy',text:'ready',ts:t}]);
              const dot = document.getElementById('chatdock-dot');
              const names = [...document.querySelectorAll('.chatdock-chathost .vroom-chat-msg-name')]
                .map(n => getComputedStyle(n).color);
              const alert = document.querySelector('.vroom-chat-alert');
              return {dotHidden: dot.hidden, dotDisplay: getComputedStyle(dot).display,
                      dotText: dot.textContent, colors: names,
                      preview: alert ? alert.textContent : null};}""")
            if spoke["dotHidden"] is not False or spoke["dotDisplay"] == "none":
                fails.append("the unread dot is not showing: %s" % spoke)
            if spoke["dotText"] != "3":
                fails.append("the dot reads %r, not a count of 3" % spoke["dotText"])
            # ASKED FOR BY NAME - "make sure everyone's chat color is
            # different". A hash into eight colours collides; this is the
            # property, not the mechanism.
            if len(set(spoke["colors"])) != len(spoke["colors"]):
                fails.append("two people in the chat share a colour: %s" % spoke["colors"])
            # ASKED FOR BY NAME - "you will get message previews when
            # someone sends a chat even if you don't have the chat open".
            if not spoke["preview"] or "sent a message" not in spoke["preview"]:
                fails.append("no message preview when the chat is closed: %r" % spoke["preview"])

            # 5. a Virtual Room takes the chat away and leaves the dock
            vr = pg.evaluate("""()=>{
              vroomCode = 'ROOM-1234';
              syncChatDock(); chatDockTab = 'chat'; syncChatDock();
              const note = (document.querySelector('.chatdock-note')||{}).textContent || '';
              const r = {note: note, left: chatRoomCode,
                         dockUp: !document.getElementById('chatdock').hidden,
                         chatControls: !!document.querySelector('.chatdock-chathost')};
              vroomCode = null; syncChatDock();
              return r;}""")
            # THE VIRTUAL ROOM'S CHAT SUPERSEDES THIS ONE, and leaving the
            # room does not hand it back: "you'd have to start another chat
            # again because it won't be there".
            if vr["left"] is not None:
                fails.append("a Virtual Room did not end the chat lobby: %r" % vr["left"])
            if vr["chatControls"]:
                fails.append("the chat is still usable inside a Virtual Room")
            if not vr["dockUp"]:
                fails.append("the whole dock went away inside a Virtual Room - notifications go with it")
            if "Virtual Room" not in (vr["note"] or ""):
                fails.append("nothing says why the chat is gone: %r" % vr["note"])

            # 6. nothing published anywhere carries the sync code
            leak = pg.evaluate("()=>JSON.stringify(window.__updates).indexOf('SECR') >= 0")
            if leak:
                fails.append("THE SYNC CODE WAS PUBLISHED FROM THE CHAT")

            real = [e for e in errs if not any(k in e.lower() for k in
                    ("firebase","firestore","gstatic","failed to fetch","net::"))]
            if real: fails.append("JS error %s" % real[0])
            br.close()
    finally:
        srv.shutdown()
    return fails


def run_intro(src_dir, label):
    """The one-time introduction card: it opens, it says the three things
    it was asked to say, and it never opens twice."""
    srv, url = serve(src_dir); fails = []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            ctx = br.new_context(viewport={"width": 440, "height": 956}, is_mobile=True, has_touch=True)
            # NO intro.seen here - this is the one check that wants it.
            ctx.add_init_script(
                "try{localStorage.setItem('class26e.freshstart','1');"
                "localStorage.setItem('class26e.frame.ok','go-live-1');}catch(e){}")
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(url); pg.wait_for_timeout(2400)
            pg.evaluate("""()=>{document.getElementById('splashscreen')?.remove();
              fbDb = {collection:()=>({doc:()=>({set:()=>Promise.resolve(),
                       update:()=>Promise.resolve()})})};
              store.onboardingComplete = true; store.firstName = 'Madison';
              store.tourRev = 99; store.publicId = 'me0000000001';
              try{ localStorage.removeItem('class26e.intro.seen'); }catch(e){}
              showHome();}""")
            # IT IS NOT UP YET, and that is half the requirement: "give it
            # a 2 or so second delay after the Home Screen hits".
            pg.wait_for_timeout(900)
            early = pg.evaluate("()=>!!document.getElementById('intro-pop')")
            if early:
                fails.append("the introduction opened immediately, not after a pause")
            pg.wait_for_timeout(1900)
            out = pg.evaluate("""()=>{
              const el = document.getElementById('intro-pop');
              if(!el) return null;
              const card = el.querySelector('.intro-card').getBoundingClientRect();
              const btn = document.getElementById('chatdock-btn');
              const txt = el.innerText.toLowerCase();
              return {rows: el.querySelectorAll('.intro-row').length,
                      topReachable: card.top >= -1,
                      bottomReachable: card.bottom <= el.scrollHeight + 1,
                      /* A POPUP, NOT A TOOLTIP - asked for in those words.
                         A tour tooltip is ~15rem wide; this is most of the
                         column. */
                      wide: card.width > innerWidth * 0.7,
                      ringed: !!(btn && btn.classList.contains('is-introduced')),
                      saysChat: txt.indexOf('chat') >= 0,
                      saysFriends: txt.indexOf('friend') >= 0,
                      saysPrivate: txt.indexOf('only the people you invite') >= 0,
                      go: !!el.querySelector('.intro-go')};}""")
            if not out:
                fails.append("the introduction never opened")
            else:
                if out["rows"] < 3:
                    fails.append("the introduction has %d sections, not three" % out["rows"])
                if not out["wide"]:
                    fails.append("the introduction is tooltip-sized, not a popup")
                if not (out["topReachable"] and out["bottomReachable"]):
                    fails.append("part of the introduction cannot be scrolled to: %s" % out)
                # It introduces the BUTTON, so the button has to be findable
                # while it is being talked about.
                if not out["ringed"]:
                    fails.append("the chat button is not highlighted while being explained")
                for key, what in [("saysChat", "the chat"), ("saysFriends", "friends"),
                                  ("saysPrivate", "who can see a chat")]:
                    if not out[key]:
                        fails.append("the introduction never mentions %s" % what)
                if not out["go"]:
                    fails.append("there is no way to dismiss the introduction")

            # ONCE, AND ONLY ONCE. A "what's new" card that comes back every
            # launch is the single most irritating thing an update can do.
            again = pg.evaluate("""()=>{
              document.querySelector('.intro-go').click();
              return new Promise(r => setTimeout(() => {
                showHome();
                setTimeout(() => r({
                  seen: localStorage.getItem('class26e.intro.seen'),
                  back: !!document.getElementById('intro-pop')}), 2600);
              }, 400));}""")
            if not again["seen"]:
                fails.append("dismissing the introduction did not record it")
            if again["back"]:
                fails.append("the introduction came back on the next visit to Home")

            real = [e for e in errs if not any(k in e.lower() for k in
                    ("firebase","firestore","gstatic","failed to fetch","net::"))]
            if real: fails.append("JS error %s" % real[0])
            br.close()
    finally:
        srv.shutdown()
    return fails


ap = argparse.ArgumentParser(); ap.add_argument("--against")
a = ap.parse_args()
where = a.against or ROOT
label = os.path.basename(where.rstrip("/")) if a.against else "current"
fails = run(where, label) + run_class(where, label) + run_intro(where, label)
if fails:
    print(f"\n{len(fails)} FAILURE(S) [{label}]")
    for f in fails: print("  *", f)
    sys.exit(1)
print(f"\nALL PASS [{label}] - the lobby chat, the chat dock and the introduction")
