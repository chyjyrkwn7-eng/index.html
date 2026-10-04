#!/usr/bin/env python3
"""GROUP CHATS, BY THE PEOPLE IN THEM (build 307).

Three classmates and a second device, against the shared fake Firestore
check-vroom carries, every step through the app's own functions and
buttons. Written from one report covering five things at once:

  1. "When starting a group chat, there's a massive box that takes over
     the entire screen ... similar thing happens when leaving a chat."
     A toast pinned top AND bottom (two rules, same specificity, the
     wrong one later in the file).
  2. "Looking at an old group chat, previous members of it randomly got
     kicked out and I don't see them." Nameless participant entries -
     written by older builds - were dropped as ghosts. The live class
     chat had Napoleon and Billyswole in it, invisible.
  3. "The list of your group chats and who's in them ... definitely not
     showing correctly" and "the characters match up". The list, the
     roster and the bubbles all read the entry, which holds whatever name
     and character the person had when they last opened that room.
  4. "Clicking the group chat stuff but not a button makes the background
     go dark." iOS's tap highlight on every non-button with a handler -
     the whole panel is one - plus a roster that opened a dimmed sheet
     with nothing on it to say it was a button.
  5. Leaving on one device while another had the chat open: the second
     one's presence beat wrote you straight back in.

Every check was run against build 306 (--against <dir>) and fails there.
"""
import argparse, functools, http.server, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)

FAILS = []
def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)) if detail else ""))
    if not ok: FAILS.append(name)

def serve(path):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port

MAD, ALEX, KIM = "aaa0000000001", "bbb0000000002", "ccc0000000003"
# The rankings say who these people are NOW. Kim's entry in the room is
# going to say something older.
ROWS = [
    {"pub": MAD, "firstName": "Madison", "avatarChar": "grizzly"},
    {"pub": ALEX, "firstName": "Alex", "avatarChar": "alien"},
    {"pub": KIM, "firstName": "Kim", "avatarChar": "wizard"},
]

def main(src, size):
    vw, vh = size
    srv, url = serve(src)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            ctx = br.new_context(viewport={"width": vw, "height": vh}, has_touch=True)
            ctx.add_init_script(FAKE)
            ctx.add_init_script(
                "try{localStorage.setItem('class26e.frame.ok','go-live-1');"
                "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');}catch(e){}")
            errs = []

            def tab(name, pub, av):
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: errs.append(name + ": " + str(e)[:160]))
                pg.goto(url); pg.wait_for_timeout(2600)
                pg.evaluate("""(a)=>{
                  document.getElementById('splashscreen')?.remove(); __useFake();
                  store.onboardingComplete = true; store.firstName = a.name; store.publicId = a.pub;
                  store.avatarChar = a.av; store.tourRev = 99; store.savedCodeSaved = true;
                  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour',
                   'seenSettingsTour','seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
                  syncCode = 'SYNC-' + a.pub; chatRoomCode = null; chatMyKey = null;
                  leaderboardRows = a.rows.map(r => Object.assign({ facc: [], freq: [], level: 3, badges: 0, hundos: 0 }, r));
                  store.chats = [];
                  showHome(); }""", {"name": name, "pub": pub, "av": av, "rows": ROWS})
                pg.wait_for_timeout(300)
                return pg

            M = tab("Madison", MAD, "grizzly")
            A = tab("Alex", ALEX, "alien")
            K = tab("Kim", KIM, "wizard")

            print("\n1. starting, joining and leaving: a notice, not a wall")
            M.bring_to_front()
            M.evaluate("""()=>{ openChatDock(); document.querySelector('.chatdock-tab[data-tab="groups"]')?.click();
              [...document.querySelectorAll('.chatdock-act')].find(x=>/Start/.test(x.textContent)).click(); }""")
            M.wait_for_timeout(700)
            t = M.evaluate("""()=>{ const t=[...document.querySelectorAll('.toast')].find(x=>/started/i.test(x.textContent));
              if(!t) return null; const b=t.getBoundingClientRect(); return {h:Math.round(b.height), top:Math.round(b.top), vh:innerHeight, has:document.body.classList.contains('has-bottomtabs')}; }""")
            check("'Chat started' is drawn", t is not None, t)
            check("with the tab bar behind it", bool(t and t["has"]), t)
            check("and it is a notice-sized box, not most of the screen",
                  bool(t and t["h"] < 120), t)
            check("pinned near the top", bool(t and t["top"] < 120), t)
            code = M.evaluate("()=>chatRoomCode")
            for pg in (A, K):
                pg.bring_to_front(); pg.evaluate("(c)=>joinChatRoom(c)", code); pg.wait_for_timeout(500)

            print("\n2. a nameless member (an older build's stamp) is still a member")
            # Kim is not looking at it - her own device, on this build,
            # would put her name straight back, which is right but is not
            # the case being tested: somebody on an OLD build.
            K.evaluate("()=>closeChatRoom()")
            # Kim's entry, as an older build left it: a stamp and nothing
            # else. And the rankings say she now plays as the wizard while
            # the room never heard about it.
            M.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).update({ ['participants.'+x.kim]: { seen: Date.now() } })""",
                       {"code": code, "kim": KIM})
            M.bring_to_front(); M.wait_for_timeout(900)
            r = M.evaluate("""()=>{
              const chips=[...document.querySelectorAll('#chatdock-roomwho .chatdock-who')];
              return { names: chips.map(c=>c.querySelector('.chatdock-who-name').textContent),
                       count: (document.getElementById('chatdock-roomcount')||{}).textContent || '' }; }""")
            check("the roster still shows Kim", "Kim" in r["names"], r)
            check("and counts three members", r["count"].startswith("3 members"), r)
            mem = M.evaluate("""()=>{ document.getElementById('chatdock-roomwho').click();
              const rows=[...document.querySelectorAll('.chat-members .chat-member-name')].map(e=>e.textContent);
              const head=(document.querySelector('.chat-members .invite-sheet-title')||{}).textContent||'';
              document.querySelectorAll('.invite-overlay').forEach(o=>o.remove());
              return {rows, head}; }""")
            check("the member list has her too", any("Kim" in x for x in mem["rows"]), mem)

            print("\n3. everyone is drawn as they are now")
            # Alex's own entry still carries an old name and character -
            # what the room holds for somebody who renamed (Davis -> Maddog)
            # and changed character since they last opened it.
            M.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).update({
                ['participants.'+x.alex+'.name']: 'Davis', ['participants.'+x.alex+'.avatarChar']: 'ninja' })""",
                       {"code": code, "alex": ALEX})
            M.wait_for_timeout(900)
            look = M.evaluate("""()=>{
              const sig = el => [...el.querySelectorAll('*')].map(n=>n.tagName).join(',');
              const charOf = el => { if(!el) return null; const a = el.querySelector('.rank-avatar') || el;
                if(a.dataset && a.dataset.char) return a.dataset.char;
                const s = sig(el); const hit = AVATAR_CHARACTERS.find(c => sig(avatarSpanFor({avatarChar:c.id})) === s);
                return hit ? hit.id : null; };
              const chips=[...document.querySelectorAll('#chatdock-roomwho .chatdock-who')];
              const alex = chips.find(c=>/Alex|Davis/.test(c.querySelector('.chatdock-who-name').textContent));
              return { name: alex ? alex.querySelector('.chatdock-who-name').textContent : null,
                       char: alex ? charOf(alex.querySelector('.chatdock-who-art')) : null }; }""")
            check("the roster calls him by his name now", look["name"] == "Alex", look)
            check("with the character he has now", look["char"] == "alien", look)
            # A message he sent under the old name reads with the new one.
            M.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).update({ chatMessages: [
                { id:'m1', key:x.alex, name:'Davis', text:'see you at 7', ts: Date.now() } ] })""",
                       {"code": code, "alex": ALEX})
            M.wait_for_timeout(700)
            bub = M.evaluate("""()=>[...document.querySelectorAll('.chatdock-chathost .vroom-chat-msg-name')].map(e=>e.textContent)""")
            check("and so does a message he sent before the rename", any(x.startswith("Alex") for x in bub), bub)

            print("\n4. the list says who is in each group")
            M.evaluate("()=>document.querySelector('.chatdock-back').click()")
            M.wait_for_timeout(300)
            M.evaluate("()=>refreshChatList(true)"); M.wait_for_timeout(900)
            row = M.evaluate("""(c)=>{ const r=document.querySelector('.chatdock-chatrow[data-code="'+c+'"]'); if(!r) return null;
              const sig = el => [...el.querySelectorAll('*')].map(n=>n.tagName).join(',');
              const charOf = el => { if(!el) return null; const a = el.querySelector('.rank-avatar') || el;
                if(a.dataset && a.dataset.char) return a.dataset.char;
                const s = sig(el); const hit = AVATAR_CHARACTERS.find(c => sig(avatarSpanFor({avatarChar:c.id})) === s);
                return hit ? hit.id : null; };
              const faces=[...r.querySelectorAll('.chatdock-face:not(.chatdock-face-more)')].map(f=>charOf(f));
              return { name: r.querySelector('.chatdock-chatrow-name').textContent,
                       kind: (r.querySelector('.chatdock-chatrow-kind')||{}).textContent,
                       faces: faces.length, chars: faces }; }""", code)
            check("the row names both of them", bool(row and "Alex" in row["name"] and "Kim" in row["name"]), row)
            check("and says it is a group of three", bool(row and row["kind"] and row["kind"].endswith("3")), row)
            check("with both faces, in their own characters",
                  bool(row and sorted(str(c) for c in row["chars"]) == ["alien", "wizard"]), row)

            print("\n5. no grey flash, and the roster says it is a button")
            M.evaluate("(c)=>enterChatRoom(c)", code)
            M.wait_for_timeout(500)
            hl = M.evaluate("""()=>{ const p=document.getElementById('chatdock-panel'); const w=document.getElementById('chatdock-roomwho');
              const tr = v => /rgba\\(0, 0, 0, 0\\)|transparent/.test(v);
              return { panel: getComputedStyle(p).webkitTapHighlightColor, who: getComputedStyle(w).webkitTapHighlightColor,
                       ok: tr(getComputedStyle(p).webkitTapHighlightColor) && tr(getComputedStyle(w).webkitTapHighlightColor),
                       more: !!w.querySelector('.chatdock-who-more') }; }""")
            check("tapping blank chat does not grey the panel", hl["ok"], hl)
            check("the roster carries a Members label", hl["more"], hl)

            print("\n6. leaving on one device takes you out on the other")
            A2 = ctx.new_page()
            A2.on("pageerror", lambda e: errs.append("Alex2: " + str(e)[:160]))
            A2.goto(url); A2.wait_for_timeout(2600)
            A2.evaluate("""(a)=>{ document.getElementById('splashscreen')?.remove(); __useFake();
              store.onboardingComplete = true; store.firstName = 'Alex'; store.publicId = a.pub; store.avatarChar = 'alien';
              store.tourRev = 99; store.savedCodeSaved = true; syncCode = 'SYNC-' + a.pub;
              leaderboardRows = a.rows; showHome(); openChatDock(); enterChatRoom(a.code); }""",
                        {"pub": ALEX, "code": code, "rows": ROWS})
            A2.wait_for_timeout(900)
            A.bring_to_front()
            A.evaluate("(c)=>{ if(chatRoomCode!==c){ openChatDock(); enterChatRoom(c); } }", code); A.wait_for_timeout(500)
            A.evaluate("()=>leaveChatRoom()"); A.wait_for_timeout(500)
            A2.bring_to_front(); A2.wait_for_timeout(900)
            # Whatever his second phone would write next: a beat, coming
            # back to the app, and the app going away.
            A2.evaluate("""()=>{ document.dispatchEvent(new Event('visibilitychange'));
              window.dispatchEvent(new Event('pagehide')); }""")
            A2.wait_for_timeout(700)
            out = M.evaluate("""(x)=>fbDb.collection('vrooms').doc(x.code).get().then(s=>Object.keys((s.data()||{}).participants||{}))""",
                             {"code": code})
            a2 = A2.evaluate("(c)=>({open: chatRoomCode, listed: !!chatEntry(c)})", code)
            check("his other device does not write him back in", ALEX not in out, out)
            check("it closes the chat", a2["open"] is None, a2)
            check("and takes it off his list", a2["listed"] is False, a2)

            print("\n7. the leave question belongs to the chat")
            K.bring_to_front()
            K.evaluate("(c)=>{ openChatDock(); document.querySelector('.chatdock-tab[data-tab=\"groups\"]')?.click(); enterChatRoom(c); }", code)
            K.wait_for_timeout(500)
            K.evaluate("()=>[...document.querySelectorAll('.chatdock-mini')].find(x=>x.textContent==='Leave').click()")
            K.wait_for_timeout(400)
            box = K.evaluate("""()=>{ const s=document.querySelector('.chat-leavesheet'); const p=document.getElementById('chatdock-panel');
              if(!s||!p) return null; const a=s.getBoundingClientRect(), b=p.getBoundingClientRect();
              return { inside: a.left>=b.left-1 && a.right<=b.right+1 && a.top>=b.top-1 && a.bottom<=b.bottom+1,
                       sheet:[a.left,a.top,a.width,a.height].map(Math.round), panel:[b.left,b.top,b.width,b.height].map(Math.round) }; }""")
            check("it is drawn inside the chat panel", bool(box and box["inside"]), box)
            K.evaluate("()=>document.querySelector('.chatdock-back').click()"); K.wait_for_timeout(300)
            stay = K.evaluate("()=>document.querySelectorAll('.chat-leavesheet').length")
            check("and going back to the list takes it away", stay == 0, stay)
            K.evaluate("(c)=>enterChatRoom(c)", code); K.wait_for_timeout(400)
            K.evaluate("()=>[...document.querySelectorAll('.chatdock-mini')].find(x=>x.textContent==='Leave').click()")
            K.wait_for_timeout(300)
            K.evaluate("()=>document.querySelector('.chatdock-confirm-leave').click()"); K.wait_for_timeout(500)
            lt = K.evaluate("""()=>{ const t=[...document.querySelectorAll('.toast')].find(x=>/Left/.test(x.textContent));
              return t ? Math.round(t.getBoundingClientRect().height) : null; }""")
            check("'Left the chat' is a notice-sized box too", lt is not None and lt < 120, lt)

            check("no JS errors on any device", not errs, errs[:4])
    finally:
        srv.shutdown()

ap = argparse.ArgumentParser()
ap.add_argument("--against")
ap.add_argument("--size", default="440x956,834x1194")
args = ap.parse_args()
src = os.path.abspath(args.against) if args.against else ROOT
for sz in args.size.split(","):
    w, h = (int(v) for v in sz.split("x"))
    print("\n=== %dx%d %s" % (w, h, "[against " + src + "]" if args.against else "[current]"))
    main(src, (w, h))
if FAILS:
    print("\nFAILED: %s  (%d failure(s))" % (FAILS[0], len(FAILS)))
    sys.exit(1)
print("\nALL PASS - group chats")
