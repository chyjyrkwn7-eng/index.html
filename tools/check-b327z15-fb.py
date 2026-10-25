#!/usr/bin/env python3
"""Build 327z15, Firestore: fewer reads and writes, nothing visible changed.

  A. The board refresh reads only rows that changed after the first full
     fetch of a launch; a changed row replaces its copy, a new one joins,
     nobody is taken off. A full fetch comes back after BOARD_FULL_MS, and
     after a refused delta query.
  B. A leaderboard row push does not hold back the presence beat (the
     presence document is what isOnline reads first).
  C. Hiding the app and then closing it writes "away" once, to presence and
     to the open chat, and the chat's typing dot is cleared by the hide.
  D. The Friends screen's board listener detaches when Friends leaves.
  E. Somebody signing up never gets the What's New card, even on a device
     whose older account had not seen it.
  F. The public leaderboard row no longer carries the person's chat codes.
  G. A chat beats every CHAT_BEAT_MS and counts a member here for
     CHAT_STALE_MS; a Virtual Room keeps its own shorter window.
  H. Hiding the app twice inside FLOOR_HIDE_GAP_MS writes the account
     twice and the __floor once.
  I. A test the app lost is not a pop-up on Home: it is kept, and Start
     Studying asks to continue it.
  J. What's New is shown again for 9.2 (INTRO_REV past 5), with the two
     new rows first.

  python3 tools/check-b327z15-fb.py
  python3 tools/check-b327z15-fb.py --against /path/to/old-index.html
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
SEED = ('{"firstName":"Tester","avatarChar":"ninja","onboardingComplete":true,'
        '"tourRev":99,"rankMapFx244":true,"leaderboardOptIn":true,"publicId":"me0000000001",'
        '"lifetime":{"points":14820,"answered":5400,"correct":4980,"drillPlays":64}}')
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
        "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % SEED)
    pg = ctx.new_page()
    pg.route("**/index.html", lambda r: r.fulfill(
        status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(2600)
    # One fake Firestore that logs every call: what was asked of which
    # collection, and what the board holds on the "server".
    pg.evaluate("""()=>{
      document.getElementById('splashscreen')?.remove();
      if(!window.firebase) window.firebase = { firestore: { FieldValue: { delete: () => '__del' } } };
      window.__log = []; window.__board = {}; window.__whereFails = false; window.__unsubs = 0;
      const snapOf = docs => ({ metadata:{ fromCache:false }, size: docs.length,
        forEach: f => docs.forEach(([id, d]) => f({ id, data: () => d })) });
      fbDb = { collection: c => ({
        get: () => { __log.push({ c, op:'get' });
          return Promise.resolve(snapOf(Object.entries(__board))); },
        where: (f, op, v) => ({ get: () => { __log.push({ c, op:'where', f, v });
          if(__whereFails) return Promise.reject(new Error('index'));
          return Promise.resolve(snapOf(Object.entries(__board).filter(([id, d]) => (d[f] || 0) > v))); } }),
        onSnapshot: (next) => { __log.push({ c, op:'listen' });
          setTimeout(() => next(snapOf(Object.entries(__board))), 0);
          return () => { __unsubs++; }; },
        doc: id => ({
          get: () => Promise.resolve({ exists:false, data: () => null }),
          set: (d, o) => { __log.push({ c, id, op:'set', d: JSON.parse(JSON.stringify(d)) }); return Promise.resolve(); },
          update: d => { __log.push({ c, id, op:'update', keys: Object.keys(d) }); return Promise.resolve(); },
          delete: () => Promise.resolve() }) }) };
    }""")
    return ctx, pg


def main():
    print("Build 327z15 Firestore savings  (%s)" % SRC)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME)
        ctx, pg = booted(br)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        print("\nA. the board refresh reads only what changed")
        r = pg.evaluate("""async()=>{
          const t0 = Date.now();
          __board = { a1:{ firstName:'A', level:3, lastModified:t0-3600e3 },
                      b2:{ firstName:'B', level:4, lastModified:t0-3600e3 } };
          leaderboardRows = []; boardFetchedAt = 0;
          const wait = () => new Promise(r => setTimeout(r, 60));
          __log = []; fetchBoardForInvites(true); await wait();
          const first = __log.filter(x => x.c === 'leaderboard').map(x => x.op);
          const afterFirst = leaderboardRows.map(e => e.pub).sort().join(',');
          __board.b2 = { firstName:'B', level:9, lastModified:Date.now() };
          __board.c3 = { firstName:'C', level:1, lastModified:Date.now() };
          __log = []; fetchBoardForInvites(true); await wait();
          const second = __log.filter(x => x.c === 'leaderboard');
          const rows = leaderboardRows.map(e => e.pub).sort().join(',');
          const b = leaderboardRows.find(e => e.pub === 'b2');
          let fullLater = null, afterRefuse = null;
          try{ boardFullAt = Date.now() - BOARD_FULL_MS - 1000;
               __log = []; fetchBoardForInvites(true); await wait();
               fullLater = __log.filter(x => x.c === 'leaderboard').map(x => x.op).join(',');
               __whereFails = true; __log = []; fetchBoardForInvites(true); await wait();
               __whereFails = false; __log = []; fetchBoardForInvites(true); await wait();
               afterRefuse = __log.filter(x => x.c === 'leaderboard').map(x => x.op).join(',');
          }catch(e){ fullLater = 'n/a: ' + e.message; }
          return { first: first.join(','), afterFirst, second: second.map(x => x.op).join(','),
                   since: second[0] && second[0].v, fetchedAt: boardFetchedAt,
                   rows, bLevel: b && b.level, fullLater, afterRefuse };
        }""")
        check("A1. the first fetch of a launch reads the whole board", r["first"] == "get"
              and r["afterFirst"] == "a1,b2", r)
        check("A2. the next fetch asks only for rows changed since", r["second"] == "where", r["second"])
        check("A3. it keeps everybody, updates the changed row and adds the new one",
              r["rows"] == "a1,b2,c3" and r["bLevel"] == 9, (r["rows"], r["bLevel"]))
        check("A4. a full fetch again once the full answer is old", r["fullLater"] == "get", r["fullLater"])
        check("A5. a refused delta query is followed by a full fetch", r["afterRefuse"] == "get", r["afterRefuse"])

        print("\nB. a row push does not hold back the presence beat")
        r = pg.evaluate("""async()=>{
          cloudConfirmedFor = syncCode; lastHeartbeatAt = 0;
          writeLeaderboardRow(buildLeaderboardRow());
          await new Promise(r => setTimeout(r, 60));
          const rowWritten = __log.some(x => x.c === 'leaderboard' && x.op === 'set');
          __log = [];
          sendHeartbeat(false);
          const beat = __log.filter(x => x.c === 'vrooms' && x.id === PRESENCE_DOC && x.op === 'set').length;
          return { rowWritten, beat };
        }""")
        check("B1. a beat right after a row push still reaches the presence document",
              r["rowWritten"] and r["beat"] == 1, r)

        print("\nC. hiding then closing writes away once")
        r = pg.evaluate("""async()=>{
          startHeartbeat();
          chatRoomCode = 'FRND-TEST'; chatMyKey = store.publicId;
          const friendCode = isFriendChatCode(chatRoomCode);
          if(!friendCode) chatSawMeIn = chatRoomCode;
          const may = chatMayStamp();
          __log = [];
          Object.defineProperty(document, 'visibilityState', { configurable:true, get: () => 'hidden' });
          Object.defineProperty(document, 'hidden', { configurable:true, get: () => true });
          document.dispatchEvent(new Event('visibilitychange'));
          window.dispatchEvent(new Event('pagehide'));
          await new Promise(r => setTimeout(r, 30));
          const pres = __log.filter(x => x.id === PRESENCE_DOC && x.op === 'set'
            && x.d.p && x.d.p[store.publicId] < 0).length;
          const chat = __log.filter(x => x.id === chatRoomCode && x.op === 'update');
          const typingCleared = chat.length && chat[0].keys.some(k => k.indexOf('typing.') === 0);
          Object.defineProperty(document, 'visibilityState', { configurable:true, get: () => 'visible' });
          Object.defineProperty(document, 'hidden', { configurable:true, get: () => false });
          document.dispatchEvent(new Event('visibilitychange'));
          __log = [];
          Object.defineProperty(document, 'visibilityState', { configurable:true, get: () => 'hidden' });
          document.dispatchEvent(new Event('visibilitychange'));
          const again = __log.filter(x => x.id === PRESENCE_DOC && x.op === 'set').length;
          Object.defineProperty(document, 'visibilityState', { configurable:true, get: () => 'visible' });
          chatRoomCode = null;
          return { may, pres, chat: chat.length, typingCleared: !!typingCleared, again };
        }""")
        check("C1. one away mark in the presence document", r["pres"] == 1, r)
        check("C2. one away write to the open chat", r["chat"] == 1, r)
        check("C3. the hide clears the typing dot", r["typingCleared"], r)
        check("C4. after coming back, the next hide writes away again", r["again"] == 1, r)

        print("\nD. the Friends listener goes with its screen")
        r = pg.evaluate("""async()=>{
          leaderboardRows = []; __unsubs = 0;
          showFriends();
          await new Promise(r => setTimeout(r, 80));
          const listening = __log.some(x => x.c === 'leaderboard' && x.op === 'listen');
          const before = __unsubs;
          showHome();
          await new Promise(r => setTimeout(r, 80));
          return { listening, before, after: __unsubs };
        }""")
        check("D1. leaving Friends detaches its board listener",
              r["listening"] and r["before"] == 0 and r["after"] == 1, r)

        print("\nE. no What's New for a sign-up")
        r = pg.evaluate("""async()=>{
          try{ localStorage.removeItem(INTRO_KEY); }catch(e){}
          store.onboardingComplete = true; store.novaMet = 999;
          signupInNova = true;
          showHome(); maybeShowIntro();
          await new Promise(r => setTimeout(r, 3200));
          const card = !!document.getElementById('intro-pop');
          const seen = introSeen();
          signupInNova = false;
          return { card, seen };
        }""")
        check("E1. no What's New card during a sign-up", not r["card"], r)
        check("E2. and it is marked seen for that device", r["seen"], r)

        print("\nF. no chat codes on the public row")
        r = pg.evaluate("""()=>{ store.chats = [{ code:'GRPX-TEST', name:'g' }];
          const row = buildLeaderboardRow(); return { has: 'chats' in row }; }""")
        check("F1. the leaderboard row has no `chats`", not r["has"], r)

        print("\nG. chat presence")
        r = pg.evaluate("""()=>{
          const now = Date.now();
          const m = { a:{ name:'A', seen: now - 200e3 }, b:{ name:'B', seen: now - 400e3 } };
          let chat = null, room = null, beat = null;
          try{ chat = Object.keys(presentParticipants(m, CHAT_STALE_MS)).join(','); }catch(e){ chat = 'n/a'; }
          room = Object.keys(presentParticipants(m)).join(',');
          try{ beat = CHAT_BEAT_MS; }catch(e){}
          return { chat, room, beat, stale: PRESENCE_STALE_MS };
        }""")
        check("G1. a chat member who beat 200s ago is still here, 400s ago is not", r["chat"] == "a", r)
        check("G2. a Virtual Room keeps its own window", r["room"] == "", r)
        check("G3. the chat beat stays inside an older build's window", bool(r["beat"]) and r["beat"] < r["stale"], r)

        print("\nH. the __floor on hide")
        r = pg.evaluate("""async()=>{
          cloudConfirmedFor = syncCode; floorMergedFor = syncCode; lastPushCode = syncCode;
          lastFloorPushAt = Date.now() - 20 * 60e3; accountWriteAt = 0;
          const wait = () => new Promise(r => setTimeout(r, 80));
          __log = [];
          pushToCloud(true); await wait(); accountWriteAt = 0;
          pushToCloud(true); await wait();
          const sets = __log.filter(x => x.c === 'progress' && x.op === 'set');
          return { main: sets.filter(x => x.id === syncCode).length,
                   floor: sets.filter(x => String(x.id).endsWith('__floor')).length };
        }""")
        check("H1. the account goes on every hide", r["main"] == 2, r)
        check("H2. the __floor goes once for two quick hides", r["floor"] == 1, r)

        print("\nI. a lost test waits for Start Studying")
        r = pg.evaluate("""async()=>{
          const s = { v:1, at: Date.now(), cfg:{ mode:'drill', units:[] }, runMode:'drill', order:[0,1,2,3], pos:1,
                      answers:{}, saved:false };
          try{ localStorage.setItem(RUN_SESSION_KEY, JSON.stringify(s)); }catch(e){}
          resumeOfferShown = false;
          showHome();
          await new Promise(r => setTimeout(r, 3500));
          const popup = !!document.getElementById('resume-offer');
          let kept = null; try{ kept = JSON.parse(localStorage.getItem(RUN_SESSION_KEY)); }catch(e){}
          let title = '';
          if(kept){ startStudying(); await new Promise(r => setTimeout(r, 400));
            title = (document.getElementById('resume-title') || {}).textContent || ''; }
          document.getElementById('resume-offer')?.remove();
          try{ localStorage.removeItem(RUN_SESSION_KEY); }catch(e){}
          return { popup, kept: !!kept, saved: !!(kept && kept.saved), title };
        }""")
        check("I1. no pop-up on Home", not r["popup"], r)
        check("I2. the test is kept for later", r["kept"] and r["saved"], r)
        check("I3. Start Studying offers to continue it, without 'interrupted'",
              bool(r["title"]) and "nterrupt" not in r["title"], r)

        print("\nJ. What's New for 9.2")
        r = pg.evaluate("""async()=>{
          document.getElementById('resume-offer')?.remove();
          showIntroPopup(); await new Promise(r => setTimeout(r, 300));
          const pop = document.getElementById('intro-pop');
          const rows = [...document.querySelectorAll('#intro-pop .intro-row')].map(x => x.dataset.key);
          const b = pop.querySelector('.intro-card').getBoundingClientRect();
          const go = pop.querySelector('.intro-go').getBoundingClientRect();
          const fits = b.top >= 0 && b.bottom <= innerHeight && pop.scrollHeight <= pop.clientHeight + 1
            && getComputedStyle(pop).overflowY !== 'auto';
          pop.remove();
          return { rev: INTRO_REV, rows: rows.slice(0, 3), all: rows, fits, goH: Math.round(go.height) };
        }""")
        check("J1. a device that saw Version 9's card sees it again", r["rev"] > 5, r)
        check("J2. the layout and fixes rows lead", r["rows"][:2] == ["devices92", "fixes92"], r["rows"])
        check("J3. no 'Mock, a real test' row (only the name changed)", "modes" not in r["all"], r["all"])
        check("J4. the card fits the screen with nothing to scroll, Got it still 44px+",
              r["fits"] and r["goH"] >= 44, (r["fits"], r["goH"]))

        check("Z. no page errors", not errs, errs[:3])
        ctx.close(); br.close()
    print("\n" + ("ALL PASS" if not FAILURES else "%d FAILURE(S): %s" % (len(FAILURES), FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
