#!/usr/bin/env python3
"""Build 327, package r: the Virtual Room's chat buttons.

Madison:
  "Why is the room chat icon blue and not the same color as the other chat
   button? Also why is the room chat button a thing if you can just use the
   chat at the bottom of the page? Should we just remove the room chat button
   where the chat is available at the bottom? ... figure this out."
  "the room chat and the other chat button are on top of the virtual room
   stuff like the live race thing and whatever could be up there. Fix that."

  python3 tools/check-b327r.py
  python3 tools/check-b327r.py --against /tmp/base327r.html
  B327R_ONLY=A python3 tools/check-b327r.py      (A or B)

  A. ONE WAY TO THE ROOM'S CHAT, AND IT LOOKS LIKE THE CHAT BUTTON.
     - Where the room's chat panel is on the page (the lobby; the room's own
       results screen with its VIRTUAL ROOM CHAT section) there is no Room
       chat button at all.
     - Where it is not (the waiting / finale results, the race leaderboard)
       there is exactly one button carrying the room's chat, it is the dock
       button's own glass and icon colour (no blue anywhere on it), it says
       "Room" in words, the room's unread count still lands on it, and a tap
       opens the room's chat.
  B. NOTHING OF THE CHAT BUTTONS SITS OVER THE ROOM. On 320x568, 375x667,
     393x852, 440x956, 518x1125, 834x1194, 1194x834 and 1366x638, in the
     lobby, a race in progress (race line, question header), the race's
     countdown, the waiting results, the race leaderboard, a Tug of War
     match, a Battle and the room's results: the box of every visible chat
     button overlaps no visible content of the room (text, a character, the
     race track and its markers, the countdown) with the page at its top;
     a race scrolled 60/140/400px never has its race line under a chat
     button; over the leaderboard the Room button sits inside the ship's
     window, clear of its frame.

Every check about a change fails on e83f307. Guards that pass on both (they
hold what was already right): the lobby has no Room button, the race at
rest, the countdown, Tug of War and Battle overlaps, the leaderboard's one
button, a Room button's count and its tap.
"""
import argparse, functools, http.server, importlib.util, io, json, os, re, socket, sys, threading, time
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("cv", os.path.join(HERE, "check-vroom.py"))
cv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cv)

ONLY = os.environ.get("B327R_ONLY", "AB")
SIZES = [(320, 568), (375, 667), (393, 852), (440, 956), (518, 1125), (834, 1194), (1194, 834), (1366, 638)]
FAILURES = []
SHOTS = os.environ.get("B327R_SHOTS")
if SHOTS: os.makedirs(SHOTS, exist_ok=True)


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:400]) if detail else ""))
    if not ok:
        FAILURES.append(name)


# Every visible chat button, and every piece of the room's content under it.
MEASURE = r"""(only) => {
  const vis = el => { if(!el || !el.isConnected) return false;
    if(el.closest('[hidden]')) return false;
    for(let e = el; e && e.nodeType === 1; e = e.parentElement){ const cs = getComputedStyle(e);
      if(cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < .05) return false; }
    const r = el.getBoundingClientRect(); return r.width > 2 && r.height > 2; };
  const btns = ['#chatdock-btn', '#roomchat-fab'].map(q => document.querySelector(q)).filter(vis)
    .map(b => { const r = b.getBoundingClientRect(); return { id: b.id, l: r.left, t: r.top, r: r.right, b: r.bottom }; });
  const roots = (only || ['#stage', '#vroomracebar', '#vroom-race-cut', '#vroom-cutscene', '#vroom-reveal-overlay', '.wrap > .top', '#count', '#meter', '#timerline']).map(q => document.querySelector(q)).filter(Boolean)
    .filter(root => { const over = document.querySelector('#vroom-reveal-overlay, #vroom-race-cut, #vroom-cutscene');
      return !over || over === root || over.contains(root) || root.contains(over); });
  const skip = el => !!el.closest('.chatdock, #roomchat-fab, #pausebtn, .roomchat-host, .vrc-hull, .vrc-stars, .homeglow, .bottomtabs');
  const boxes = [];
  const push = (el, r, what) => { if(r.width < 2 || r.height < 2) return; boxes.push({ what, l: r.left, t: r.top, r: r.right, b: r.bottom }); };
  for(const root of roots){
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n; while((n = tw.nextNode())){
      if(!n.nodeValue.trim()) continue; const el = n.parentElement; if(!el || skip(el) || !vis(el)) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for(const r of rg.getClientRects()) push(el, r, (el.className || el.tagName) + ':' + n.nodeValue.trim().slice(0, 24));
    }
    root.querySelectorAll('svg, img, canvas, input, .vroom-racetrack, .vroom-racetrack-markers > *, .tug-rope, .battle-bar, .battle-hp, .vrc-row, .vroom-reveal-ring, #vroom-reveal-ring').forEach(el => {
      if(skip(el) || !vis(el)) return; if(el.tagName === 'svg' && el.parentElement && el.parentElement.closest('svg')) return;
      const anc = el.closest('[class]'); const tag = (typeof el.className === 'string' && el.className) ? el.className : el.tagName + (anc ? '<' + (anc.className.baseVal !== undefined ? anc.className.baseVal : anc.className) : '');
      push(el, el.getBoundingClientRect(), tag);
    });
  }
  const hits = [];
  for(const b of btns) for(const c of boxes){
    const w = Math.min(b.r, c.r) - Math.max(b.l, c.l), h = Math.min(b.b, c.b) - Math.max(b.t, c.t);
    if(w > 1 && h > 1) hits.push(b.id + ' over ' + c.what + ' (' + Math.round(w) + 'x' + Math.round(h) + ')');
  }
  return { btns: btns.map(b => b.id), hits };
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--against")
    args = ap.parse_args()
    src = args.against or os.path.join(ROOT, "index.html")
    body = cv.INSET_RE.sub(lambda m: "0px", io.open(src, encoding="utf-8").read())
    m = re.search(r'APP_BUILD\s*=\s*"([^"]+)"', body)
    vj = json.dumps({"build": m.group(1) if m else "", "note": "", "frameId": "", "frameNote": "", "force": False})
    sock = socket.socket(); sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]; sock.close()

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/index.html" % port

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cv.CHROME)
        ctx = br.new_context(viewport={"width": 440, "height": 956})
        ctx.add_init_script("window.__fakeLatency = 30;")
        ctx.add_init_script(cv.FAKE_FIRESTORE)
        ctx.add_init_script("try{['class26e.freshstart','class26e.unithold.tip','class26e.penal55124.seen','class26e.penal124256.seen','class26e.penal256578.seen'].forEach(k=>localStorage.setItem(k,'1'));"
                            "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                            "localStorage.setItem('class26e.weekrecap.v1', JSON.stringify({wk:'9999-12-31',hist:{}}));"
                            "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % cv.SEED)
        pg = ctx.new_page()
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
        pg.route("**/version.json", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"}, body=vj))
        pg.goto(url)
        pg.wait_for_function("()=>typeof showHome==='function' && typeof beginVirtualRoomTest==='function'", timeout=60000)
        pg.wait_for_timeout(2500)
        pg.evaluate("""()=>{ document.getElementById('splashscreen')?.remove(); __useFake();
          store.firstName='Rae'; store.avatarChar='ninja'; syncCode='R327-0001'; store.publicId='pub-R327-0001';
          store.novaMet = 9; theme.muteBanners = true; theme.reduceMotion = true; theme.autoAdvance = false; showHome(); }""")
        ctx.new_cdp_session(pg).send("Page.setWebLifecycleState", {"state": "active"})
        pg.evaluate(cv.BOTS_313)

        def home():
            pg.evaluate("""()=>{ try{ __vrBots.stop(); }catch(e){} ['vroom-race-cut','vroom-prep','vroom-cutscene','vroom-reveal-overlay','roomchat-sheet'].forEach(i=>document.getElementById(i)?.remove());
              try{ stopQuestionTimer(); }catch(e){} try{ leaveVirtualRoom(); }catch(e){} testInProgress=false; showHome(); }""")
            pg.wait_for_timeout(400)

        def settle():
            pg.evaluate("()=>{ window.scrollTo(0,0); try{ syncChatDock(); }catch(e){} try{ placeRoomChatFab(); }catch(e){} }")
            pg.wait_for_timeout(350)
            pg.evaluate("()=>{ window.scrollTo(0,0); try{ syncChatDock(); }catch(e){} try{ placeRoomChatFab(); }catch(e){} }")
            pg.wait_for_timeout(150)

        def sweep(state):
            bad = []
            for (w, h) in SIZES:
                pg.set_viewport_size({"width": w, "height": h})
                settle()
                r = pg.evaluate(MEASURE, None)
                if SHOTS and (w, h) in ((440, 956), (834, 1194)):
                    pg.screenshot(path=os.path.join(SHOTS, "%s-%dx%d.png" % (re.sub(r"[^a-z]+", "-", state.lower()).strip("-"), w, h)))
                if r["hits"]:
                    # a hit must persist: a character's flip-book sheet can sit for
                    # a frame where it is attached before it is placed
                    pg.wait_for_timeout(900); settle()
                    r = pg.evaluate(MEASURE, None)
                if r["hits"]:
                    bad.append("%dx%d %s" % (w, h, r["hits"][:3]))
            pg.set_viewport_size({"width": 440, "height": 956})
            settle()
            check("B %s: no chat button over the room's content at any of %d sizes" % (state, len(SIZES)), not bad, bad[:4])

        def race_room(code, n, finished=True):
            pg.evaluate("""([code, n, fin])=>{ const parts = __vrBots.room(code, n, i => fin === 'wait' ? (i === 1 ? { progress: 50 } : __vrBots.finished(i, 90 + i * 7))
                : fin ? __vrBots.finished(i, 90 + i * 7) : { progress: 20 * i });
              return fbDb.collection('vrooms').doc(code).set({ status:'starting', game:'race', units:['Identity Crimes'],
                startAt: Date.now() - 2000, chatMessages: [], participants: parts, racers: Object.keys(parts) }); }""", [code, n, finished])
            pg.wait_for_timeout(250)
            pg.evaluate("(code)=>{ vroomCode=code; vroomMyKey='me'; vroomIsHost=true; beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }", code)
            pg.wait_for_selector(".qpanel .choice", timeout=30000)

        def fab_info():
            return pg.evaluate("""()=>{ const f=document.getElementById('roomchat-fab'); const d=document.getElementById('chatdock-btn');
              const vis = el => !!el && getComputedStyle(el).visibility !== 'hidden' && getComputedStyle(el).display !== 'none' && el.getBoundingClientRect().width > 0;
              const cs = el => el ? getComputedStyle(el) : null; const fc = cs(f), dc = cs(d);
              const iconCol = el => { const s = el && el.querySelector('svg'); return s ? getComputedStyle(s).color : null; };
              const blue = c => { const m = (c||'').match(/[\\d.]+/g); if(!m) return false; const [r,g,b] = m.map(Number); return b - r > 30 && b > 120; };
              return { fab: !!f, fabVis: vis(f), dockVis: vis(d),
                fabBg: fc && fc.backgroundColor, dockBg: dc && dc.backgroundColor, fabBgImg: fc && fc.backgroundImage, dockBgImg: dc && dc.backgroundImage,
                fabBorder: fc && fc.borderTopColor, dockBorder: dc && dc.borderTopColor,
                fabColor: fc && fc.color, dockColor: dc && dc.color, fabIcon: iconCol(f), dockIcon: iconCol(d),
                anyBlue: !!f && [fc.backgroundColor, fc.borderTopColor, fc.color, iconCol(f)].some(blue),
                text: f ? f.textContent.trim() : '', label: f ? (f.getAttribute('aria-label')||'') : '',
                chatOnPage: [...document.querySelectorAll('#stage .vroom-chat')].some(c => !c.closest('[hidden], .roomchat-host'))}; }""")

        def fab_family(state):
            i = fab_info()
            check("A %s: one Room chat button" % state, i["fab"] and i["fabVis"], i)
            same = (i["fabBg"] == i["dockBg"] and i["fabBgImg"] == i["dockBgImg"] and i["fabBorder"] == i["dockBorder"]
                    and i["fabIcon"] == i["dockIcon"])
            check("A %s: it is the dock button's own glass and icon colour, no blue on it" % state, same and not i["anyBlue"], i)
            check("A %s: it says Room in words" % state, "room" in i["text"].lower(), i["text"])
            # unread count, and a tap opens the room's chat
            pg.evaluate("()=>{ roomChatUnread = 3; paintRoomChatFab(); }")
            cnt = pg.evaluate("()=>{ const c=document.querySelector('#roomchat-fab .roomchat-fab-count'); return c && !c.hidden && getComputedStyle(c).display!=='none' ? c.textContent : null; }")
            check("A %s: the room's unread count lands on it" % state, cnt == "3", cnt)
            try:
                pg.click("#roomchat-fab", timeout=5000)
                pg.wait_for_selector("#roomchat-sheet .vroom-chat", timeout=5000)
                ok = True
            except Exception as e:
                ok = False
            check("A %s: a tap opens the room's chat" % state, ok)
            pg.evaluate("()=>{ try{ closeRoomChatSheet(); }catch(e){} }")
            pg.wait_for_timeout(200)

        # ---- the lobby: the chat is on the page ---------------------------
        print("\nLobby")
        pg.evaluate("()=>createVirtualRoomLobby(['Identity Crimes'], null, 'race')")
        pg.wait_for_function("()=>typeof vroomCode==='string' && vroomCode && document.querySelector('.screen-vroom-lobby')", timeout=30000)
        pg.wait_for_timeout(1200)
        if "A" in ONLY:
            i = fab_info()
            check("A lobby: the room's chat is on the page and there is no Room chat button", i["chatOnPage"] and not i["fab"], i)
        if "B" in ONLY:
            sweep("lobby")
        home()

        # ---- a race in progress, its countdown -----------------------------
        if "B" in ONLY:
            print("\nRace in progress")
            race_room("R327RUN", 6, finished=False)
            pg.evaluate("()=>{ const bar=document.getElementById('vroomracebar'); return bar && !bar.hidden; }")
            pg.wait_for_timeout(800)
            sweep("a race in progress")
            # a long question scrolls: the race line must not slide up under the buttons
            bad = []
            for (w, h) in SIZES:
                pg.set_viewport_size({"width": w, "height": h})
                settle()
                pg.evaluate("()=>{ if(!document.getElementById('r327-spacer')){ const d=document.createElement('div'); d.id='r327-spacer'; d.style.height='2400px'; document.querySelector('#stage .qpanel').appendChild(d); } }")
                pg.wait_for_timeout(150)
                for y in (60, 140, 400):
                    pg.evaluate("(y)=>window.scrollTo(0, y)", y)
                    pg.wait_for_timeout(120)
                    r = pg.evaluate(MEASURE, ["#vroomracebar"])
                    if r["hits"]:
                        bad.append("%dx%d @%d %s" % (w, h, y, r["hits"][:2]))
                        break
                pg.evaluate("()=>{ document.getElementById('r327-spacer')?.remove(); window.scrollTo(0,0); }")
            pg.set_viewport_size({"width": 440, "height": 956}); settle()
            check("B a race in progress, scrolled: the race line never slides under a chat button", not bad, bad[:4])
            home()
            print("\nCountdown")
            pg.evaluate("()=>{ showVroomCountdown(Date.now() + 60000, ()=>{}); }")
            pg.wait_for_selector("#vroom-reveal-overlay", timeout=10000)
            pg.wait_for_timeout(600)
            sweep("the race's countdown")
            pg.evaluate("()=>document.getElementById('vroom-reveal-overlay')?.remove()")
            home()

        # ---- the waiting results, the leaderboard --------------------------
        print("\nWaiting results and the race leaderboard")
        # one racer still going, so the leaderboard does not roll by itself
        # while the waiting results are measured
        race_room("R327FIN", 4, finished="wait")
        pg.evaluate("()=>__vrBots.beat()")
        pg.evaluate("()=>{ order.forEach(qi=>{ picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); stopQuestionTimer(); summarize(); }")
        pg.wait_for_function("()=>!!document.querySelector('.vroom-waitcard')", timeout=30000)
        pg.wait_for_timeout(1500)
        if "A" in ONLY:
            fab_family("the waiting results")
            # a message from another racer: the VIRTUAL ROOM preview opens the room's chat
            pg.evaluate("()=>{ theme.muteBanners = false; }")
            pg.evaluate("""()=>fbDb.collection('vrooms').doc('R327FIN').update({ chatMessages: firebase.firestore.FieldValue.arrayUnion(
              { id:'m-r327', key:'b1', name:'Ben', text:'gg everyone', ts: Date.now() }) })""")
            try:
                pg.wait_for_selector(".vroom-chat-alert", timeout=8000)
                tag = pg.evaluate("()=>(document.querySelector('.vroom-chat-alert .vroom-chat-alert-tag')||{}).textContent")
                pg.click(".vroom-chat-alert", timeout=5000)
                pg.wait_for_selector("#roomchat-sheet .vroom-chat", timeout=5000)
                ok = True
            except Exception as e:
                ok = False; tag = repr(e)[:120]
            check("A the waiting results: the VIRTUAL ROOM preview opens the room's chat", ok, tag)
            pg.evaluate("()=>{ try{ closeRoomChatSheet(); }catch(e){} theme.muteBanners = true; }")
            pg.wait_for_timeout(200)
        if "B" in ONLY:
            sweep("the waiting results")
        pg.evaluate("()=>startVroomRaceCutscene()")
        pg.wait_for_function("()=>document.querySelector('#vroom-race-cut.is-done')", timeout=30000)
        pg.wait_for_timeout(1200)
        if "A" in ONLY:
            fab_family("the race leaderboard")
            n = pg.evaluate("""()=>['#chatdock-btn','#roomchat-fab'].map(q=>document.querySelector(q)).filter(el=>el && getComputedStyle(el).visibility!=='hidden' && getComputedStyle(el).display!=='none').length""")
            check("A the race leaderboard: one chat button on screen", n == 1, n)
        if "B" in ONLY:
            sweep("the race leaderboard")
            bad = []
            for (w, h) in SIZES:
                pg.set_viewport_size({"width": w, "height": h})
                settle()
                r = pg.evaluate("""()=>{ const f=document.getElementById('roomchat-fab'), win=document.querySelector('#vroom-race-cut .vrc-window');
                  if(!f || !win) return { ok:false, why:'missing' };
                  const a=f.getBoundingClientRect(), b=win.getBoundingClientRect(), rim=9;
                  return { ok: a.left >= b.left + rim && a.right <= b.right - rim && a.top >= b.top + rim && a.bottom <= b.bottom - rim,
                           fab:[a.left,a.top,a.right,a.bottom].map(Math.round), win:[b.left,b.top,b.right,b.bottom].map(Math.round) }; }""")
                if not r["ok"]:
                    bad.append("%dx%d %s" % (w, h, r))
            pg.set_viewport_size({"width": 440, "height": 956}); settle()
            check("B the race leaderboard: the Room button sits inside the ship's window, clear of its frame", not bad, bad[:3])
        home()

        # ---- the room's own results: the chat is on the page ---------------
        print("\nThe room's results screen")
        race_room("R327RES", 3, finished=True)
        pg.evaluate("()=>{ order.forEach(qi=>{ picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); stopQuestionTimer(); summarize(); }")
        pg.wait_for_function("()=>!!document.querySelector('.vroom-waitcard')", timeout=30000)
        pg.wait_for_timeout(600)
        pg.evaluate("()=>{ document.getElementById('vroom-race-cut')?.remove(); showVirtualRoomResults(); }")
        pg.wait_for_selector("#stage .vroom-chat", timeout=15000)
        pg.wait_for_timeout(800)
        if "A" in ONLY:
            i = fab_info()
            check("A the room's results: its chat is on the page and there is no Room chat button", i["chatOnPage"] and not i["fab"], i)
        if "B" in ONLY:
            sweep("the room's results")
        home()

        # ---- Tug of War and Battle in progress ------------------------------
        if "B" in ONLY:
            for game in ("tug", "battle"):
                print("\n%s in progress" % game)
                code = game.upper() + "327R"
                pg.evaluate("""([code, game])=>{ const parts = __vrBots.room(code, 4); const teams = tugTeamsFor(parts);
                  const d = { status:'starting', game, units:['Identity Crimes'], count: 10, startAt: Date.now() + 600,
                              chatMessages: [], participants: parts, racers: Object.keys(parts) };
                  if(game === 'tug') d.tug = { progress:{}, over:false, winner:null, finalPos:0, count:10, teams };
                  else d.battle = { log:[], progress:{}, over:false, winner:null, count:0, teams };
                  return fbDb.collection('vrooms').doc(code).set(d).then(()=>{ vroomCode=code; vroomMyKey='me';
                    game === 'tug' ? beginTugMatch(d) : beginBattleMatch(d); __vrBots.beat(); }); }""", [code, game])
                pg.wait_for_selector(".screen-%s .choice" % game, timeout=30000)
                pg.wait_for_timeout(600)
                sweep("a %s match" % ("Tug of War" if game == "tug" else "Battle"))
                home()

        ctx.close(); br.close(); srv.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILURES else "FAILED: " + "; ".join(FAILURES), len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
