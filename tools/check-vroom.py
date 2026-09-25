#!/usr/bin/env python3
"""Two devices in one Virtual Room, for real.

Everything else in tools/ drives one page. A Virtual Room is the only
part of this app whose whole job is two devices agreeing, and the two
things reported about it - ready-up not showing up on the other device,
and the host seeing the test before everybody else - are both invisible
to a one-page harness. So this runs TWO TABS.

They are two real tabs in one browser context, which means they share an
origin and therefore share localStorage and its `storage` event. That is
the whole trick: the fake Firestore below keeps the room document in
localStorage and pushes snapshots on write, so a write in tab A reaches
tab B the way a Firestore write reaches another phone - asynchronously,
through something outside the page, with a latency this harness can dial
up on purpose. The app's own code is untouched by it; fbDb is simply
pointed at the fake.

  python3 tools/check-vroom.py
  python3 tools/check-vroom.py --against /path/to/old-index.html
  python3 tools/check-vroom.py --latency 400   # a bad connection

Exits non-zero on any failure.
"""
import argparse
import functools
import json
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

# A Firestore that lives in localStorage. Only the surface the Virtual
# Room actually uses: one document per room, set/get/update/onSnapshot,
# and dotted field paths, which is how ready-up and progress are written.
FAKE_FIRESTORE = """
(() => {
  const KEY = c => "fakefs::" + c;
  const LATENCY = window.__fakeLatency || 60;
  const listeners = [];

  function read(coll, id){
    try {
      const all = JSON.parse(localStorage.getItem(KEY(coll)) || "{}");
      return all[id] || null;
    } catch(e){ return null; }
  }
  function writeAll(coll, all){
    localStorage.setItem(KEY(coll), JSON.stringify(all));
    // Same-tab listeners get no storage event, so they are told directly.
    // Other tabs get the real one, which is the point of the exercise.
    setTimeout(() => notify(coll), 0);
  }
  function write(coll, id, data){
    let all = {};
    try { all = JSON.parse(localStorage.getItem(KEY(coll)) || "{}"); } catch(e){}
    all[id] = data;
    writeAll(coll, all);
  }
  function setDeep(obj, path, value){
    const parts = path.split(".");
    let cur = obj;
    for(let i = 0; i < parts.length - 1; i++){
      if(typeof cur[parts[i]] !== "object" || cur[parts[i]] === null) cur[parts[i]] = {};
      cur = cur[parts[i]];
    }
    cur[parts[parts.length - 1]] = value;
  }
  function collSnap(coll){
    let all = {};
    try { all = JSON.parse(localStorage.getItem(KEY(coll)) || "{}"); } catch(e){}
    const ids = Object.keys(all);
    return {
      metadata: { fromCache: false },
      size: ids.length,
      forEach(fn){ ids.forEach(id => fn({
        id: id, exists: true,
        data: () => JSON.parse(JSON.stringify(all[id] || {}))
      })); }
    };
  }
  function notify(coll){
    listeners.filter(l => l.coll === coll).forEach(l => {
      /* A COLLECTION LISTENER IS A REAL THING AND THE FAKE DID NOT HAVE
         ONE. attachInviteWatcher() subscribes to the whole `leaderboard`
         collection, and without this its call threw into the try/catch
         that wraps it - silently. So every check had to hand-assign
         leaderboardRows, and the one bug that lives in that callback
         (announcing only while the screen was "home") was invisible to
         the harness by construction. */
      if(l.id === null){ l.cb(collSnap(l.coll)); return; }
      const data = read(l.coll, l.id);
      l.cb({ exists: !!data, id: l.id, data: () => JSON.parse(JSON.stringify(data || {})) });
    });
  }
  window.addEventListener("storage", e => {
    if(e && e.key && e.key.indexOf("fakefs::") === 0) notify(e.key.slice(8));
  });

  function later(fn){ return new Promise(res => setTimeout(() => res(fn()), LATENCY)); }

  window.__fakeDb = {
    collection(coll){
      return {
        onSnapshot(cb, err){
          const l = { coll: coll, id: null, cb: cb };
          listeners.push(l);
          setTimeout(() => cb(collSnap(coll)), LATENCY);
          return () => { const i = listeners.indexOf(l); if(i >= 0) listeners.splice(i, 1); };
        },
        /* A ONE-SHOT READ OF THE WHOLE COLLECTION. The app stopped
           holding a live subscription to the board and pulls it
           occasionally instead, so a fake without this reports an empty
           class and every fallback silently measures nothing. */
        get(){ return later(() => collSnap(coll)); },
        doc(id){
          return {
            set(data, opts){ return later(() => {
              /* MERGE IS NOT A DETAIL HERE. Presence is one document
                 with a field per person, written by thirty devices with
                 set(..., {merge:true}) - a fake that replaces instead of
                 merging would show exactly one person online and the
                 check would be measuring the harness, not the app. */
              if(opts && opts.merge){
                const cur = read(coll, id) || {};
                const inc = JSON.parse(JSON.stringify(data));
                const deepMerge = (a, b) => {
                  Object.keys(b).forEach(k => {
                    if(b[k] && typeof b[k] === "object" && !Array.isArray(b[k])
                       && a[k] && typeof a[k] === "object" && !Array.isArray(a[k])){
                      deepMerge(a[k], b[k]);
                    } else { a[k] = b[k]; }
                  });
                  return a;
                };
                write(coll, id, deepMerge(cur, inc));
                return;
              }
              write(coll, id, JSON.parse(JSON.stringify(data)));
            }); },
            get(){ return later(() => {
              const d = read(coll, id);
              return { exists: !!d, id: id, data: () => JSON.parse(JSON.stringify(d || {})) };
            }); },
            update(fields){ return later(() => {
              /* Read AND write inside the same tick of this callback, so an
                 update behaves the way Firestore's does: whatever is on
                 disk when it runs is what it appends to. That is what lets
                 the concurrent-chat check below mean something - two sends
                 issued at the same moment resolve one after the other
                 here, and arrayUnion has to survive that. */
              const d = read(coll, id) || {};
              Object.keys(fields).forEach(k => {
                const v = fields[k];
                if(v && typeof v === "object" && v.__arrayUnion){
                  const parts = k.split(".");
                  let cur = d;
                  for(let i = 0; i < parts.length - 1; i++){
                    if(typeof cur[parts[i]] !== "object" || cur[parts[i]] === null) cur[parts[i]] = {};
                    cur = cur[parts[i]];
                  }
                  const leaf = parts[parts.length - 1];
                  const arr = Array.isArray(cur[leaf]) ? cur[leaf].slice() : [];
                  /* Firestore de-duplicates by deep equality. */
                  const seen = JSON.stringify(v.__arrayUnion);
                  if(!arr.some(x => JSON.stringify(x) === seen)) arr.push(v.__arrayUnion);
                  cur[leaf] = arr;
                } else if(v && typeof v === "object" && v.__delete){
                  /* Firestore removes the FIELD, and an empty parent is
                     left as an empty map rather than being pruned -
                     which matters, because the app counts the keys of
                     `participants` to know how many people are in the
                     room. */
                  const parts = k.split(".");
                  let cur = d;
                  let ok = true;
                  for(let i = 0; i < parts.length - 1; i++){
                    if(typeof cur[parts[i]] !== "object" || cur[parts[i]] === null){ ok = false; break; }
                    cur = cur[parts[i]];
                  }
                  if(ok) delete cur[parts[parts.length - 1]];
                } else {
                  setDeep(d, k, v);
                }
              });
              write(coll, id, d);
            }); },
            delete(){ return later(() => {
              let all = {};
              try { all = JSON.parse(localStorage.getItem(KEY(coll)) || "{}"); } catch(e){}
              delete all[id];
              writeAll(coll, all);
            }); },
            onSnapshot(cb, err){
              const l = { coll: coll, id: id, cb: cb };
              listeners.push(l);
              setTimeout(() => {
                const d = read(coll, id);
                cb({ exists: !!d, id: id, data: () => JSON.parse(JSON.stringify(d || {})) });
              }, LATENCY);
              return () => { const i = listeners.indexOf(l); if(i >= 0) listeners.splice(i, 1); };
            }
          };
        }
      };
    }
  };
  /* The app reaches for firebase.firestore.FieldValue.arrayUnion when it
     sends a chat message. The real SDK is blocked in the sandbox, so
     without this the send path throws and the chat checks would fail for
     a reason that has nothing to do with the chat. */
  window.firebase = window.firebase || {};
  window.firebase.firestore = window.firebase.firestore || {};
  window.firebase.firestore.FieldValue = {
    arrayUnion: function(v){ return { __arrayUnion: v }; },
    /* Leaving a room deletes the participant field. Without this the
       sentinel would be STORED as an object and the person would still
       be counted - the exact bug leaving was written to fix, hidden by
       the harness rather than caught by it. */
    delete: function(){ return { __delete: true }; }
  };
  window.__useFake = function(){ fbDb = window.__fakeDb; };
})();
"""

# One seed for both tabs. Identity is applied PER TAB after boot instead,
# because two tabs in one context share localStorage - so a per-tab seed
# would have the second tab's name overwrite the first's on disk, and the
# two would then share a sync code, which is the participant key. Two real
# devices have two codes; the harness has to arrange that itself.
SEED = ('{"firstName":"Anonymous","avatarChar":"ninja","onboardingComplete":true,'
        '"leaderboardOptIn":true,"lastModified":1700000000000,'
        '"tourRev":99,"seenProfileTour":true,"seenModeSelectTour":true,"seenUnitSelectTour":true,'
        '"lifetime":{"points":1000,"answered":400,"correct":380,"perfectTests":9}}')

FAILURES = []



def tap(pg, selector, what):
    """A REAL tap, and a loud failure if there is nothing to tap.

    Two faults lived in `evaluate("()=>document.querySelector(s)?.click()")`
    and between them they are why this file timed out about a quarter of
    the time regardless of what was being tested.

    `element.click()` bypasses pointer-events and hit testing, which is
    the anti-pattern that let a Join button measure perfectly while being
    unpressable for a week. And `?.` turns "the button has not rendered
    yet" into a SILENT no-op - so nobody readied up, the auto-start never
    fired, and the run sat waiting twenty seconds for something that was
    never going to happen, reporting a timeout with no clue in it.

    Waiting for the element first removes the race; a hit-tested click
    tests what a finger does; and an exception here names the button
    instead of surfacing as a mystery timeout further down.
    """
    try:
        pg.wait_for_selector(selector, state="visible", timeout=15000)
    except Exception:
        raise AssertionError("%s never appeared (%s)" % (what, selector))
    pg.click(selector)

def join_lobby(pg, code, tries=3, timeout=12000):
    """Join a room and WAIT FOR THE LOBBY, retrying.

    Joining is a write, a snapshot and a screen mount. The fake
    Firestore wakes every listener in the context on every write, so
    with several tabs alive any of the three can miss its window - and
    a fixed wait then fails the whole run for a reason that has nothing
    to do with the app. Retried rather than waited longer: a second
    attempt lands immediately where a longer wait just fails later.
    Every section joins through this, so the flakiness is fixed in one
    place rather than three."""
    for attempt in range(tries):
        pg.evaluate("(c)=>joinVirtualRoomLobby(c)", code)
        try:
            pg.wait_for_selector(".vroom-readyup-btn", state="visible", timeout=timeout)
            return
        except Exception:
            if attempt == tries - 1:
                raise
            pg.wait_for_timeout(1200)


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -> " + str(detail)) if detail else ""))
    if not ok:
        FAILURES.append(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--against", help="run against a different index.html")
    ap.add_argument("--latency", type=int, default=60,
                    help="simulated one-way write latency, ms")
    args = ap.parse_args()
    src = args.against or os.path.join(ROOT, "index.html")
    body = INSET_RE.sub(lambda m: "0px", io.open(src, encoding="utf-8").read())
    # THE HARNESS MUST ECHO BACK THE BUILD IT IS SERVING. version.json
    # on disk names the CURRENT build; served alongside an --against
    # copy it does not match its APP_BUILD, the update check fires, and
    # with "force" set the page reloads out from under the run. That is
    # not a finding about the old build, it is the harness breaking
    # itself, and it cost a whole --against run before it was spotted.
    m = re.search(r'APP_BUILD\s*=\s*"([^"]+)"', body)
    version_json = json.dumps({"build": m.group(1) if m else "", "note": "",
                               "frameId": "", "frameNote": "", "force": False})

    sock = socket.socket(); sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]; sock.close()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/index.html" % port

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        # ONE context, so the two tabs share an origin and therefore share
        # localStorage and its storage event.
        ctx = br.new_context(viewport={"width": 440, "height": 956})
        ctx.add_init_script("window.__fakeLatency = %d;" % args.latency)
        ctx.add_init_script(FAKE_FIRESTORE)

        ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                            "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % SEED)

        def open_tab(name, avatar, points, code, badges=0, rank_key=None):
            pg = ctx.new_page()
            pg.route("**/index.html", lambda r: r.fulfill(
                status=200, headers={"content-type": "text/html; charset=utf-8"},
                body=body))
            pg.route("**/version.json", lambda r: r.fulfill(
                status=200, headers={"content-type": "application/json"},
                body=version_json))
            pg.goto(url)
            pg.wait_for_timeout(2600)
            pg.evaluate("""(a)=>{
              document.getElementById('splashscreen')?.remove();
              __useFake();
              store.firstName = a.name;
              store.avatarChar = a.avatar;
              /* A RANK FIXTURE ASKS THE TABLE, IT DOES NOT TYPE NUMBERS.
                 These used to be literal XP totals chosen to clear a
                 tier - 14,820 for Silver, 3,100 for Iron - and they
                 stopped clearing anything the day the ladder was
                 rescaled, which failed the app for being right. Given a
                 rankKey this now derives the smallest XP total that
                 reaches that rank's level, plus exactly its badge count,
                 so the fixture follows TIER_UNLOCKS wherever it goes. */
              let wantBadges = a.badges;
              if(a.rankKey){
                const R = TIER_UNLOCKS[a.rankKey];
                let xp = 0;
                while(levelProgress(xp).level < R.level) xp += 25;
                store.lifetime.points = xp;
                wantBadges = R.badges;
              } else {
                store.lifetime.points = a.points;
              }
              /* Badges as well as points, because a rank needs both and
                 the lobby shows the rank. Mastering the first N units
                 is the cheapest way to hold a given one. */
              store.unitPerfects = {};
              topicsIn(QUESTIONS).slice(0, wantBadges).forEach(u => {
                store.unitPerfects[u] = BADGE_THRESHOLD;
              });
              syncCode = a.code;
              /* A DISTINCT PUBLIC ID PER TAB, and this is not cosmetic.
                 publicIdOf() mints one on demand and saveStore()s it -
                 into localStorage, which every tab in this context
                 SHARES. So whichever tab minted first wrote its id to
                 disk, and a tab booting after that read the same id and
                 became the same account: joining then came back "this
                 account is already in the lobby" and the join silently
                 did nothing. It presented as a flaky harness and it was
                 the harness being dishonest - two devices are two
                 accounts, so the fixture has to say so. */
              store.publicId = "pub-" + a.code;
            }""", {"name": name, "avatar": avatar, "points": points, "code": code,
                   "badges": badges, "rankKey": rank_key})
            return pg

        # Different ranks on purpose - Madison holds veteran and Devonte
        # only rookie - so a row showing the wrong emblem cannot pass by
        # showing the same one twice. Named by TIER_UNLOCKS key rather
        # than by an XP total, so the pair stays two different ranks
        # however the ladder is rescaled.
        host = open_tab("Madison", "ninja", None, "HOST-0001", rank_key="veteran")
        guest = open_tab("Devonte", "ghost", None, "GUES-0002", rank_key="rookie")
        # Only one tab can be in front, and a background tab has its rAF
        # throttled - which showed up as the host "starting a second late"
        # when it was simply not being given frames. Two phones are both
        # foreground, so the harness has to say so. This is about the
        # HARNESS being honest, not about the app.
        for pg in (host, guest):
            cdp = ctx.new_cdp_session(pg)
            cdp.send("Page.setWebLifecycleState", {"state": "active"})

        print("\n1. a lobby, and a second device joining it")
        code = host.evaluate("""()=>{
          const units = topicsIn(QUESTIONS).slice(0, 1);
          createVirtualRoomLobby(units, null);
          return null;}""")
        # WAIT FOR THE LOBBY, DO NOT SLEEP AT IT. These were fixed waits
        # and the whole run failed about one time in three - not on
        # anything the app did, but on a write, a snapshot and a screen
        # mount taking longer than the number somebody typed. A gate
        # that fails at random is a gate nobody believes, which makes
        # every question about this screen unanswerable.
        host.wait_for_function("() => typeof vroomCode === 'string' && vroomCode",
                               timeout=20000)
        code = host.evaluate("()=>vroomCode")
        check("the host lands in a lobby with a code", bool(code), code)

        join_lobby(guest, code)
        try:
            host.wait_for_function(
                "() => document.querySelectorAll('.vroom-row').length >= 2",
                timeout=20000)
        except Exception:
            pass
        if os.environ.get("VROOM_DEBUG"):
            print("   guest:", guest.evaluate("""()=>({code:vroomCode, key:vroomMyKey,
              screen:(document.querySelector('#stage .panel')||{}).className,
              rows:document.querySelectorAll('.vroom-row').length,
              doc: JSON.parse(localStorage.getItem('fakefs::vrooms')||'{}')})"""))
            print("   host :", host.evaluate("""()=>({code:vroomCode, key:vroomMyKey,
              rows:document.querySelectorAll('.vroom-row').length})"""))
        rows = host.evaluate("()=>document.querySelectorAll('.vroom-row').length")
        check("the host sees the guest arrive", rows == 2, "%d row(s)" % rows)

        print("\n2. ready-up reaches the other device")
        # The guest readies up; the HOST's screen has to change without
        # anybody touching it. This is the reported bug.
        tap(guest, ".vroom-readyup-btn", "the guest's ready-up button")
        host.wait_for_timeout(600)
        seen = host.evaluate("""()=>{
          const rows=[...document.querySelectorAll('.vroom-row')];
          return { ready: rows.filter(r=>r.classList.contains('is-ready')).length,
                   count:(document.querySelector('.vroom-readycount')||{}).textContent||"" };}""")
        check("the host sees the guest's ready without reloading",
              seen["ready"] >= 1, seen)

        print("\n3. the lobby says who you are up against")
        # The small blue level number that used to sit here is gone -
        # that used to sit here is gone - asked for, built, and then
        # asked against. The rank emblem is what stayed.
        ranks = host.evaluate("""()=>({
          seen: [...document.querySelectorAll('.vroom-row')]
            .map(r=>{const m=r.querySelector('.lb-rankmark'); return m ? m.title : null;}),
          want: [RANK_DISPLAY_NAME.rookie, RANK_DISPLAY_NAME.veteran] })""")
        check("every row carries its person's rank",
              sorted(r for r in ranks["seen"] if r) == sorted(ranks["want"]), ranks)
        check("no level number beside the character",
              host.evaluate("()=>!document.querySelector('.vroom-level')"), "none")

        print("\n4. everybody starts at the same instant")
        tap(host, ".vroom-readyup-btn", "the host's ready-up button")
        # Both devices install a per-frame recorder BEFORE the countdown, so
        # the moment each one uncovers its question is measured rather than
        # polled for. Polling from here cannot resolve the difference this
        # is about: the report was that the host saw the test first.
        for pg in (host, guest):
            pg.evaluate("""()=>{
              window.__revealSeen = null; window.__revealGone = null;
              (function watch(){
                const up = !!document.getElementById('vroom-reveal-overlay');
                if(up && window.__revealSeen === null) window.__revealSeen = Date.now();
                if(!up && window.__revealSeen !== null && window.__revealGone === null){
                  window.__revealGone = Date.now(); return;
                }
                requestAnimationFrame(watch);
              })();
            }""")
        starts = {}
        for label, pg in [("host", host), ("guest", guest)]:
            pg.wait_for_function("() => typeof vroomStartAt === 'number' && vroomStartAt",
                                 timeout=20000)
            starts[label] = pg.evaluate("()=>vroomStartAt")
        check("both devices share one start instant",
              starts["host"] and starts["host"] == starts["guest"], starts)

        # Wait past the shared instant, then compare what each recorded.
        host.wait_for_timeout(1000)
        for pg in (host, guest):
            pg.wait_for_function("() => window.__revealGone !== null", timeout=25000)
        seen = {k: pg.evaluate("()=>({up:window.__revealSeen, gone:window.__revealGone})")
                for k, pg in [("host", host), ("guest", guest)]}
        check("the question was covered on both while the countdown ran",
              all(v["up"] for v in seen.values()), seen)
        # EARLY is the bug. The report was the host seeing the test first
        # while everybody else was still loading, and the fix for it is
        # that every device computes the same instant from the same
        # shared startAt - so the assertion is that nobody uncovers
        # before it, not that the two land on the same millisecond.
        #
        # Late is measured too, but only on the tab that is in front.
        # Chromium throttles requestAnimationFrame in a background tab
        # and the app's own countdown runs on rAF, so a backgrounded tab
        # genuinely does hold its overlay a beat longer - an artefact of
        # two tabs in one browser, not of two phones. Asserting a tight
        # skew across both would be asserting something the harness
        # cannot honestly measure.
        early = {k: starts["host"] - v["gone"] for k, v in seen.items()}
        check("neither device uncovers the question early",
              all(v <= 50 for v in early.values()),
              {k: "%dms early" % v for k, v in early.items()})
        front = seen["guest"]["gone"] - starts["host"]
        check("the foreground device uncovers on the shared instant",
              -50 <= front <= 250, "%dms after startAt" % front)

        # ---- 5. the chat cannot lose a message -----------------------
        # The bug this is written against: send() used to .get() the whole
        # document, push onto the array it found, and .update() the result.
        # Two people typing at once each read the array BEFORE the other's
        # message existed, so whoever wrote second erased the first. In a
        # lobby whose whole purpose is agreeing on units, that is the one
        # failure that matters.
        print("\n5. two people typing at once")
        for pg in (host, guest):
            pg.evaluate("()=>{ if(window.__chatKill) window.__chatKill(); "
                        "const box=document.createElement('div');"
                        "box.id='chatprobe';document.body.appendChild(box);"
                        "window.__chatKill = buildVroomChatPanel(box); }")
        host.wait_for_timeout(400)
        # Fired without awaiting each other, which is the whole point.
        host.evaluate("()=>{ const i=document.querySelector('#chatprobe .vroom-chat-input');"
                      "i.value='from the host'; "
                      "document.querySelector('#chatprobe .vroom-chat-send').click(); }")
        guest.evaluate("()=>{ const i=document.querySelector('#chatprobe .vroom-chat-input');"
                       "i.value='from the guest'; "
                       "document.querySelector('#chatprobe .vroom-chat-send').click(); }")
        host.wait_for_timeout(1200 + args.latency * 4)
        texts = host.evaluate("()=>[...document.querySelectorAll('#chatprobe .vroom-chat-msg')]"
                              ".map(e=>e.textContent)")
        joined = " | ".join(texts)
        check("both messages survive a simultaneous send",
              ("from the host" in joined) and ("from the guest" in joined), joined)
        seen_on_guest = guest.evaluate(
            "()=>[...document.querySelectorAll('#chatprobe .vroom-chat-msg')]"
            ".map(e=>e.textContent).join(' | ')")
        check("and both reach the other device",
              ("from the host" in seen_on_guest) and ("from the guest" in seen_on_guest),
              seen_on_guest)

        # ---- 6. two lobbies at once ----------------------------------
        # Each lobby is its own document keyed by its join code, so they
        # should never see each other - but "should" is not a check, and
        # ~40 classmates can easily have two rooms open at the same time.
        print("\n6. two lobbies at the same time")
        second = open_tab("Rosa", "queen", 4000, "CCCC-3333", badges=2)
        second.evaluate("()=>{ vroomCode='ZZZZ-9999'; vroomMyKey='CCCC-3333';"
                        " vroomIsHost=true;"
                        " fbDb.collection('vrooms').doc('ZZZZ-9999')"
                        "   .set({ host:'CCCC-3333', participants:{}, chatMessages:[] }); }")
        second.wait_for_timeout(300 + args.latency * 2)
        second.evaluate("()=>{ const box=document.createElement('div');"
                        "box.id='chatprobe';document.body.appendChild(box);"
                        "window.__chatKill = buildVroomChatPanel(box); }")
        second.wait_for_timeout(300 + args.latency * 2)
        second.evaluate("()=>{ const i=document.querySelector('#chatprobe .vroom-chat-input');"
                        "i.value='other room only'; "
                        "document.querySelector('#chatprobe .vroom-chat-send').click(); }")
        second.wait_for_timeout(800 + args.latency * 4)
        bleed = host.evaluate("()=>[...document.querySelectorAll('#chatprobe .vroom-chat-msg')]"
                              ".map(e=>e.textContent).join(' | ')")
        check("the second lobby's chat does not reach the first",
              "other room only" not in bleed, bleed)
        own = second.evaluate("()=>[...document.querySelectorAll('#chatprobe .vroom-chat-msg')]"
                              ".map(e=>e.textContent).join(' | ')")
        check("and the second lobby sees only its own",
              ("other room only" in own) and ("from the host" not in own), own)
        codes = host.evaluate("()=>vroomCode") , second.evaluate("()=>vroomCode")
        check("the two lobbies are two different documents",
              codes[0] != codes[1], codes)

        # ---- 7. the results screen -----------------------------------
        # THE ONE SCREEN WITH NO OTHER COVERAGE. It needs run state, so it
        # cannot be mounted cold and is therefore not in sweep-layout's
        # SCREENS - which is exactly why five separate things were wrong
        # on it at once: the tab bar was showing inside a test, the race
        # line stayed up with the results out, the two exits were
        # different sizes with an arrow on one, "Review your answers"
        # opened an empty box on a clean run, and there was no sign of
        # the XP the run had earned.
        #
        # Driven here rather than mounted: both tabs finish for real, so
        # the screen is reached the way a person reaches it.
        print("\n7. the results screen, reached by finishing")
        for pg in (host, guest):
            pg.evaluate("""()=>{
              /* EVERY ANSWER RIGHT, on purpose. The bug in "Review your
                 answers" was only ever on the clean-run path: the list
                 was built when something had been missed, so the one
                 case where the button said "all correct" was the case
                 where it expanded nothing. A run with misses in it takes
                 the other branch and cannot see that at all. */
              order.forEach(qi => {
                const oo = optionOrder(qi);
                picked[qi] = oo.indexOf(QUESTIONS[qi].answer);
              });
              /* A real finish writes the score and hands over to the
                 finale, which hands over to the results screen. */
              summarize();
            }""")
        host.wait_for_timeout(600)
        # Both are finished as far as the room document is concerned, so
        # the results screen can be asked for directly - what is under
        # test is the screen, not the route to it.
        for pg in (host, guest):
            pg.evaluate("()=>{ showVirtualRoomResults(); }")
        host.wait_for_timeout(900 + args.latency * 4)

        # THE RACE LINE, on the path that was actually broken. Hiding it
        # on the FIRST render always worked; what did not was every
        # render after it, because the hide sat past an early return that
        # fires once the standings are up. So: put the bar back, poke the
        # room document to force another snapshot, and see whether the
        # screen takes it down again.
        host.evaluate("()=>{ document.getElementById('vroomracebar').hidden = false; }")
        host.evaluate("()=>{ fbDb.collection('vrooms').doc(vroomCode)"
                      "  .update({ nudge: Date.now() }); }")
        host.wait_for_timeout(700 + args.latency * 4)
        race_again = host.evaluate("()=>document.getElementById('vroomracebar').hidden")

        got = host.evaluate("""()=>{
          const R = e => e ? e.getBoundingClientRect() : null;
          const btns = [...document.querySelectorAll('.vroom-exit-row .vroom-exit-btn')];
          const bar = document.querySelector('.bottomtabs');
          const race = document.getElementById('vroomracebar');
          const lvl = document.querySelector('.results-level');
          const toggle = [...document.querySelectorAll('button')]
            .find(b => /Review your answers/.test(b.textContent));
          if(toggle) toggle.click();
          const list = toggle ? toggle.nextElementSibling : null;
          const chat = document.querySelector('.vroom-chat-toggle');
          const panel = document.querySelector('#stage .panel');
          return {
            exits: btns.map(b => Math.round(R(b).width)),
            exitLabels: btns.map(b => b.textContent),
            arrow: btns.some(b => b.classList.contains('back-link')),
            tabbar: !bar || bar.hidden,
            forced: !!window.forceHideBottomTabs,
            raceHidden: !race || race.hidden,
            levelBlock: !!lvl,
            levelGain: lvl ? (lvl.querySelector('.results-level-gain') || {}).textContent : null,
            reviewItems: list ? list.querySelectorAll('li').length : -1,
            chatCorner: chat ? (R(chat).right > R(panel).right - 4) : null
          };}""")
        check("no bottom tab bar on the results screen",
              got["tabbar"] and got["forced"], {k: got[k] for k in ("tabbar", "forced")})
        check("the race line is down once the results are out",
              got["raceHidden"], got["raceHidden"])
        check("and stays down on every snapshot after, not just the first",
              race_again, race_again)
        check("both exits are the same width",
              len(got["exits"]) == 2 and got["exits"][0] == got["exits"][1], got["exits"])
        # ASSERT THE SHAPE, NOT THE STRING. This named "Back to Home"
        # and went red the day that button was renamed to "Main menu"
        # for consistency with every other results screen - a gate that
        # encodes a decision fails the app for being right. What matters
        # is that there are two of them, that one goes to the lobby and
        # one leaves the room, and that neither is a back link (a back
        # link draws an arrow, which was asked against).
        labels = [x.strip().lower() for x in got["exitLabels"]]
        check("and neither is a back link, so neither carries an arrow",
              not got["arrow"], got["exitLabels"])
        check("one goes back to the lobby and one leaves the room",
              len(labels) == 2 and any("lobby" in x for x in labels)
              and any(("menu" in x or "home" in x) for x in labels), got["exitLabels"])
        check("the XP and level block is on the screen",
              got["levelBlock"], got["levelGain"])
        # -1 means the toggle was not found at all; 0 means it was found
        # and opened nothing, which is the bug this is written against.
        check("Review your answers opens a real list, even on a clean run",
              got["reviewItems"] > 0, got["reviewItems"])
        if got["chatCorner"] is not None:
            check("the chat button is in the top right", got["chatCorner"], got["chatCorner"])

        # -------------------------------------------------------------
        # 8. MATCH SETTINGS IS A SCREEN, NOT A SHEET OVER HOME.
        # Asked for in those words: a button in the lobby opens "the
        # normal unit selection screen", with the tab bar replaced by
        # the options button and a way back to the lobby. It is
        # showVirtualRoomSetup() in edit mode rather than a second
        # screen, because setting a room up and changing it afterwards
        # are the same question and two builders for one idea is what
        # this file keeps paying for.
        print("\n8. match settings")
        pg.evaluate("""()=>{
          fbDb = { collection:()=>({ doc:()=>({ update:()=>Promise.resolve() }) }) };
          vroomCode = 'ROOM42'; vroomIsHost = true;
          const all = topicsIn(QUESTIONS);
          showVirtualRoomSetup({units:[all[0]], timeLimit:20, count:null, status:'waiting'});
        }""")
        pg.wait_for_timeout(900)
        got = pg.evaluate("""()=>{
          const cards = [...document.querySelectorAll('.picks .pick')];
          const tabs = document.querySelector('.bottomtabs');
          const back = document.querySelector('.back-link');
          return {
            units: cards.length, allUnits: topicsIn(QUESTIONS).length,
            checked: cards.filter(c => c.querySelector('input').checked).length,
            // .pick is opacity:0 until revealed - sixteen rows, right
            // size, right contents, painting nothing measures fine.
            painted: cards.slice(0, 2).every(c => +getComputedStyle(c).opacity > 0.9),
            badges: cards.filter(c => !!c.querySelector('.pick-badge')).length,
            search: !!document.querySelector('.searchwrap input'),
            tabsGone: !tabs || tabs.hidden || tabs.getBoundingClientRect().height === 0,
            back: back ? back.textContent : null,
            title: (document.querySelector('.welcomeintro-title')||{}).textContent,
            over: document.documentElement.scrollWidth - window.innerWidth
          };}""")
        check("every unit is offered", got["units"] == got["allUnits"],
              {"rows": got["units"], "units": got["allUnits"]})
        # A settings screen that opens on defaults is a reset button.
        check("it opens on what the room is already set to", got["checked"] == 1, got["checked"])
        check("the unit cards are actually painted", got["painted"] is True, got["painted"])
        check("they are the real unit cards, badge and search and all",
              got["badges"] == got["units"] and got["search"] is True,
              {"badges": got["badges"], "search": got["search"]})
        # You are inside a match: Home, Leaderboard, Ranks and Settings
        # are not places to be from here.
        check("no bottom tab bar on it", got["tabsGone"] is True, got["tabsGone"])
        check("and a way back to the lobby",
              "lobby" in (got["back"] or "").lower(), got["back"])
        check("titled as what it is", got["title"] == "Match settings", got["title"])
        check("no sideways scroll", got["over"] <= 0, got["over"])

        # The options sheet: questions AND time limit, both the drill
        # sliders, and Save rather than Create lobby.
        tap(pg, "#nextbtn", "the next button")
        pg.wait_for_timeout(600)
        sheet = pg.evaluate("""()=>{
          const m = document.getElementById('unitoptions-modal');
          const labs = [...document.querySelectorAll('#unitoptions-modal .slab')]
                        .map(x => x.textContent.trim().toLowerCase());
          return { open: !!m && !m.hidden,
                   sliders: document.querySelectorAll('#unitoptions-modal .slider').length,
                   labs: labs,
                   dupes: labs.length !== new Set(labs).size,
                   begin: (document.querySelector('.sheet-begin-btn')||{}).textContent,
                   title: (document.querySelector('.unitoptions-modal-title')||{}).textContent };}""")
        check("the options sheet opens", sheet["open"] is True, sheet["open"])
        check("questions and time limit are both there", sheet["sliders"] == 2,
              {"n": sheet["sliders"], "labels": sheet["labs"]})
        # plainSlider draws its own heading, so a second one above it
        # printed TIME LIMIT twice.
        check("and neither heading is printed twice", sheet["dupes"] is False, sheet["labs"])
        check("it saves rather than creating a second lobby",
              sheet["begin"] == "Save settings", sheet["begin"])
        check("and says what it is", sheet["title"] == "Match settings", sheet["title"])

        # ---- 9. tug of war, two devices, self-paced -----------------
        # WRITTEN AGAINST THE BUILD IT FAILS ON. Tug shipped as lockstep
        # rounds: everyone on the same question, the host resolving each
        # one, nobody moving until everybody had answered. It was
        # replaced whole - "it's not turn based, the teams will work
        # through the questions, and whoever is getting through them
        # faster will start to pull the rope, so each question you get
        # one chance" - so the assertion that matters is the one the old
        # build cannot satisfy: ONE DEVICE GETS THROUGH SEVERAL
        # QUESTIONS WHILE THE OTHER ANSWERS NOTHING, and the rope moves
        # for it. Under rounds that is impossible by construction.
        try:
            print("\n9. tug of war: one side can pull ahead on its own")
            # THE EARLIER TABS GO FIRST. Sections 1-8 leave five live
            # pages, each holding a listener onto the same fake Firestore
            # in the same localStorage, and every write in this section
            # wakes all of them. That is not two phones, it is one
            # browser doing eight tabs' work, and it was enough to make
            # a fresh lobby miss its 20-second window.
            for stale in (host, guest, second):
                try:
                    stale.close()
                except Exception:
                    pass
            tugA = open_tab("Alex", "cadet", 2000, "TUGA-0001", badges=1)
            tugB = open_tab("Bo", "ghost", 2000, "TUGB-0002", badges=1)
            for pg in (tugA, tugB):
                cdp = ctx.new_cdp_session(pg)
                cdp.send("Page.setWebLifecycleState", {"state": "active"})

            tugA.evaluate("""()=>{
              const units = topicsIn(QUESTIONS).slice(0, 1);
              createVirtualRoomLobby(units, null, "tug");
            }""")
            tugA.wait_for_function("() => typeof vroomCode === 'string' && vroomCode",
                                   timeout=20000)
            tcode = tugA.evaluate("()=>vroomCode")
            try:
                tugA.wait_for_selector(".vroom-readyup-btn", state="visible", timeout=25000)
                join_lobby(tugB, tcode)
            except Exception:
                # Say WHERE it got stuck. "the button never appeared" on
                # its own sends the next person looking at the button.
                for tag, pg in (("A", tugA), ("B", tugB)):
                    print("   %s: %s" % (tag, pg.evaluate("""()=>({
                      code: vroomCode, key: vroomMyKey, host: vroomIsHost,
                      panel: (document.querySelector('#stage .panel')||{}).className,
                      rows: document.querySelectorAll('.vroom-row').length })""")))
                raise
            check("a tug lobby takes a second device", bool(tcode), tcode)

            tap(tugB, ".vroom-readyup-btn", "Bo's ready-up")
            tugA.wait_for_timeout(400 + args.latency * 2)
            tap(tugA, ".vroom-readyup-btn", "Alex's ready-up")
            for pg in (tugA, tugB):
                pg.wait_for_selector(".screen-tug", timeout=25000)
            check("both devices land in the match",
                  tugA.evaluate("()=>!!document.querySelector('.screen-tug')")
                  and tugB.evaluate("()=>!!document.querySelector('.screen-tug')"))

            # THE ROPE ITSELF. A knot, a centre line, and a rope with the
            # twist on it - the twist is a repeating gradient rather than
            # elements, so what is checked is that the background carries
            # one, not that some strand div exists.
            rope = tugA.evaluate("""()=>{
              const r = document.querySelector('.screen-tug .tug-rope');
              if(!r) return null;
              const cs = getComputedStyle(r);
              return { h: Math.round(r.getBoundingClientRect().height),
                       twist: /repeating-linear-gradient/.test(cs.backgroundImage),
                       knot: !!document.querySelector('.tug-knot'),
                       centre: !!document.querySelector('.tug-centre') };}""")
            check("the rope is drawn as a rope, not a hairline",
                  bool(rope) and rope["twist"] and rope["h"] >= 24, rope)
            check("with a knot on it and a line to pull it past",
                  bool(rope) and rope["knot"] and rope["centre"], rope)

            def tug_answer(pg, right=True):
                """One real, hit-tested tap on a choice, then wait out the
                settle and the advance."""
                idx = pg.evaluate("""(want)=>{
                  const item = QUESTIONS[tugPool[tugMyPos % tugPool.length]];
                  const n = item.choices.length;
                  return want ? item.answer : (item.answer + 1) % n;
                }""", right)
                pg.click(".screen-tug .choices .choice:nth-child(%d)" % (idx + 1))
                pg.wait_for_timeout(1400)

            before = tugA.evaluate("()=>({pos:tugMyPos, correct:tugMyCorrect})")
            for _ in range(3):
                tug_answer(tugA, True)
            after = tugA.evaluate("()=>({pos:tugMyPos, correct:tugMyCorrect})")
            stuck = tugB.evaluate("()=>({pos:tugMyPos, correct:tugMyCorrect})")
            # THE WHOLE POINT. Three questions answered on one device while
            # the other has not touched anything.
            check("one device works through three questions on its own",
                  after["pos"] == before["pos"] + 3 and after["correct"] == 3,
                  {"before": before, "after": after})
            check("and the other device is untouched by that",
                  stuck["pos"] == 0, stuck)

            # The rope has to have MOVED on the device that did nothing -
            # that is the published-progress half, and it is what "whoever
            # is getting through them faster will start to pull" means.
            tugB.wait_for_timeout(600 + args.latency * 4)
            pulled = tugB.evaluate("""()=>{
              const k = document.querySelector('.tug-knot');
              return k ? parseFloat(k.style.left) : null;}""")
            check("the rope has moved on the device that answered nothing",
                  pulled is not None and abs(pulled - 50) > 1, pulled)
            mine_side = tugB.evaluate("()=>!!document.querySelector('.tug-knot.is-theirs')")
            check("and it has moved the wrong way for them", mine_side is True)

            # ONE CHANCE. The tap locks every choice; a second tap on
            # another one must change nothing.
            pos_before = tugA.evaluate("()=>tugMyPos")
            idx = tugA.evaluate("""()=>{
              const item = QUESTIONS[tugPool[tugMyPos % tugPool.length]];
              return (item.answer + 1) % item.choices.length; }""")
            tugA.click(".screen-tug .choices .choice:nth-child(%d)" % (idx + 1))
            tugA.wait_for_timeout(120)
            locked = tugA.evaluate("""()=>{
              const cs=[...document.querySelectorAll('.screen-tug .choice')];
              return { all: cs.length, off: cs.filter(c=>c.disabled).length,
                       shown: cs.filter(c=>c.classList.contains('is-right')).length };}""")
            check("one chance: the tap locks every choice",
                  locked["all"] > 0 and locked["off"] == locked["all"], locked)
            # A wrong answer still says what the right one was - this mode is
            # fast, and it is worth nothing as study if it never tells you.
            check("and a wrong answer still shows the right one",
                  locked["shown"] >= 1, locked)
            tugA.wait_for_timeout(1400)
            check("a miss still moves you on",
                  tugA.evaluate("()=>tugMyPos") == pos_before + 1,
                  {"was": pos_before, "now": tugA.evaluate("()=>tugMyPos")})

            # THE PACE. The clock is a function of elapsed match time, not
            # of anybody's own index, and it tightens.
            pace = tugA.evaluate("""()=>{
              const n = tugCount;
              const p = tugPace(n);
              const at = f => tugQuestionMs(p.total * f, n);
              return { n: n, start: p.start, end: p.end, total: p.total,
                       q0: at(0), q25: at(.25), q55: at(.55), q80: at(.8), q100: at(1),
                       mins: tugPaceMinutes(n),
                       m10: tugPaceMinutes(10), m29: tugPaceMinutes(29), m80: tugPaceMinutes(80),
                       mAll: tugPaceMinutes(400),
                       floorSmall: tugQuestionMs(tugPace(29).total, 29),
                       floorBig: tugQuestionMs(1e9, 500) };}""")
            # THE SPEED-UP IS A LATE EVENT, NOT A GRADIENT YOU ARE INSIDE
            # FROM QUESTION ONE - "towards the end if there's no winner
            # questions speed up". A straight ramp from the first question
            # was the first draft and it is not this.
            check("the opening pace holds through the first half",
                  pace["q0"] == pace["q25"] == pace["q55"] == pace["start"],
                  {k: pace[k] for k in ("start", "q0", "q25", "q55")})
            check("and it tightens towards the end",
                  pace["q80"] < pace["q55"] and pace["q100"] == pace["end"],
                  {k: pace[k] for k in ("q55", "q80", "q100", "end")})
            # SEVEN SECONDS, AND ONLY AT THE END - "lowest time will be 7
            # seconds but that's ONLY if it takes that long to decide a
            # winner." A floor the match REACHES, not a speed it runs at.
            check("the floor is seven seconds and nothing goes under it",
                  pace["floorSmall"] == 7000 and pace["floorBig"] >= 7000,
                  {"29q at the end": pace["floorSmall"], "a huge bank": pace["floorBig"]})
            # 5-10 minutes, whatever was picked - "if I select 80 questions
            # though, make it so that it does last about that long".
            check("10, 29 and 80 questions all land in the 5-10 minute window",
                  all(5 <= pace[k] <= 10 for k in ("m10", "m29", "m80")),
                  {k: pace[k] for k in ("m10", "m29", "m80")})
            # The bank is not capped - "All units" is several hundred
            # questions - so past a point the rope settles it rather than
            # the questions running out.
            check("and a whole-bank match is still capped at ten minutes",
                  pace["mAll"] <= 10, pace["mAll"])

            # THE TIME LIMIT CONTROL IS GONE for tug, and still there for
            # race - "when I hit tug of war, the timer option shouldn't be
            # there". Asserted as a SHAPE (one slider vs two) rather than by
            # naming the label, which is the trap this file has already been
            # caught by twice.
            tugA.evaluate("""()=>{
              fbDb = { collection:()=>({ doc:()=>({ update:()=>Promise.resolve() }) }) };
              vroomCode='ROOM43'; vroomIsHost=true;
              showVirtualRoomSetup({units:[topicsIn(QUESTIONS)[0]], timeLimit:20,
                                    count:null, game:'race', status:'waiting'});
            }""")
            tugA.wait_for_timeout(700)
            tap(tugA, "#nextbtn", "the next button")
            tugA.wait_for_timeout(500)
            def visible_sliders(pg):
                # The SLIDERS themselves, not their sections: plainSlider
                # builds its own .sect inside the one it is appended to, so
                # counting sections counts each slider twice and the numbers
                # stop meaning what they say.
                return pg.evaluate("""()=>[...document.querySelectorAll('#unitoptions-modal .slider')]
                  .filter(s => s.offsetParent !== null).length""")
            race_n = visible_sliders(tugA)
            tugA.click(".vroom-host-mode[data-mode='tug']")
            tugA.wait_for_timeout(350)
            tug_n = visible_sliders(tugA)
            tugA.click(".vroom-host-mode[data-mode='race']")
            tugA.wait_for_timeout(350)
            back_n = visible_sliders(tugA)
            check("race offers a time limit, tug does not",
                  race_n == 2 and tug_n == 1, {"race": race_n, "tug": tug_n})
            check("and switching back restores it", back_n == 2, back_n)

            # The two game cards read as a choice: both the same size, both
            # with a surface of their own. The unselected one was reported
            # as looking like it was not there.
            cards = tugA.evaluate("""()=>[...document.querySelectorAll('.vroom-host-mode')].map(b=>{
              const r=b.getBoundingClientRect(), cs=getComputedStyle(b);
              return { w:Math.round(r.width), h:Math.round(r.height),
                       on:b.classList.contains('on'),
                       bg:cs.backgroundColor, art:!!b.querySelector('.vroom-host-mode-art') };})""")
            check("both game cards are the same size and both have art",
                  len(cards) == 2 and cards[0]["w"] == cards[1]["w"]
                  and cards[0]["h"] == cards[1]["h"] and all(c["art"] for c in cards),
                  cards)
            off = [c for c in cards if not c["on"]]
            check("and the unselected one still has a surface",
                  bool(off) and off[0]["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"),
                  off[0]["bg"] if off else None)
        except Exception as e:
            # A SECTION THAT THROWS IS A SECTION THAT FAILED, and it must
            # not take the other eight down with it. --against an older
            # build this one is EXPECTED to go red, and an exception there
            # aborts the run before it can say so.
            check("the tug section ran at all", False, repr(e)[:200])
        finally:
            # EVERY SECTION CLOSES ITS OWN TABS. The fake Firestore wakes
            # every listener in the context on every write, so a tab left
            # open goes on doing work for the rest of the run - and with
            # eight of them alive a fresh join stopped landing inside its
            # 25 seconds. The symptom was whichever heavy section happened
            # to run last, which is the giveaway that it was load and not
            # the app.
            for done in ("tugA", "tugB"):
                pg2 = locals().get(done)
                if pg2 is not None:
                    try:
                        pg2.close()
                    except Exception:
                        pass

        # ---- 10. somebody leaves ------------------------------------
        # NOTHING EVER REMOVED A PARTICIPANT FROM A ROOM. "Leave lobby"
        # detached a listener and walked away; pause -> Exit test did
        # not touch the room at all. Both gates in this app wait for
        # EVERYONE with no timeout - the lobby before it starts, the
        # finale before it reveals - so one person walking out stranded
        # the rest for good, and a host walking out bricked the room
        # outright, because only a host fires the auto-start.
        print("\n10. a room survives somebody walking out")
        try:
            for stale in (tugA, tugB):
                try:
                    stale.close()
                except Exception:
                    pass
            lobA = open_tab("Ana", "cadet", 2000, "LOBA-0001", badges=1)
            lobB = open_tab("Ben", "ghost", 2000, "LOBB-0002", badges=1)
            lobC = open_tab("Cy", "queen", 2000, "LOBC-0003", badges=1)
            for pg in (lobA, lobB, lobC):
                ctx.new_cdp_session(pg).send("Page.setWebLifecycleState", {"state": "active"})

            lobA.evaluate("()=>createVirtualRoomLobby(topicsIn(QUESTIONS).slice(0,1), 10, 'race')")
            lobA.wait_for_function("() => typeof vroomCode === 'string' && vroomCode", timeout=20000)
            lcode = lobA.evaluate("()=>vroomCode")
            for pg in (lobB, lobC):
                join_lobby(pg, lcode)
            lobA.wait_for_function(
                "() => document.querySelectorAll('.vroom-row').length >= 3", timeout=25000)
            check("three people are in the lobby",
                  lobA.evaluate("()=>document.querySelectorAll('.vroom-row').length") == 3)

            # THE HOST LEAVES. Under the old code this was terminal:
            # vroomIsHost was a local flag set when you created the room,
            # so nobody was host afterwards and the auto-start could
            # never fire however ready everybody was.
            lobA.evaluate("()=>{ window.__toasts=[]; }")
            lobB.evaluate("""()=>{ window.__toasts=[]; const o=window.showToast;
              window.showToast=function(m){ window.__toasts.push(m); return o.apply(this,arguments); }; }""")
            lobA.click(".back-link")
            lobB.wait_for_function(
                "() => document.querySelectorAll('.vroom-row').length === 2", timeout=25000)
            left = lobB.evaluate("()=>document.querySelectorAll('.vroom-row').length")
            check("the host's row disappears for everyone else", left == 2, left)
            toasts = lobB.evaluate("()=>window.__toasts||[]")
            check("and they are told who left",
                  any("Ana" in t and "left" in t.lower() for t in toasts), toasts)

            # THE ROOM STILL HAS A HOST. Derived from join order, so the
            # earliest remaining person is host from the next snapshot -
            # no handoff write to race against.
            hosts = {n: pg.evaluate("()=>vroomIsHost") for n, pg in (("Ben", lobB), ("Cy", lobC))}
            check("exactly one of the two left is now host",
                  sum(1 for v in hosts.values() if v) == 1, hosts)
            check("and it is the earlier joiner", hosts.get("Ben") is True, hosts)

            # AND THE MATCH CAN ACTUALLY START. This is the assertion the
            # old build cannot satisfy: two people ready, nobody host,
            # nothing happens, forever.
            for pg in (lobB, lobC):
                tap(pg, ".vroom-readyup-btn", "ready-up")
                pg.wait_for_timeout(300)
            started = True
            try:
                for pg in (lobB, lobC):
                    pg.wait_for_function(
                        "() => typeof vroomStartAt === 'number' && vroomStartAt", timeout=25000)
            except Exception:
                started = False
            check("the match still starts without the person who made it", started)
        except Exception as e:
            check("the leave section ran at all", False, repr(e)[:200])
        finally:
            for done in ("lobA", "lobB", "lobC"):
                pg2 = locals().get(done)
                if pg2 is not None:
                    try:
                        pg2.close()
                    except Exception:
                        pass

        # ---- 11. the end-of-match cutscene --------------------------
        # "A 5 second cutscene at the end of these virtual room matches
        # with some anticipation to see who wins." The standings already
        # staggered in last-place-first and its own comment called that
        # "a beat of suspense, not a cutscene", which was the gap.
        print("\n11. the end-of-match cutscene")
        try:
            cut = open_tab("Del", "cadet", 3000, "CUTA-0001", badges=1)
            ctx.new_cdp_session(cut).send("Page.setWebLifecycleState", {"state": "active"})
            # A SCENE, NOT A PORTRAIT. One big character centred on black
            # is the character-unlock screen, and it was read as one -
            # "it looks too much like the void character unlock". So a
            # race ends on a PODIUM with the top three and a tug ends on
            # the whole winning SIDE. Asserted as shape: how many
            # figures, and that the blocks are ordered tallest in the
            # middle, not by what any of them is called.
            shape = cut.evaluate("""()=>{
              window.__done = false;
              theme.muteBanners = false; theme.reduceMotion = false;
              playVroomWinnerCutscene({ kind: "podium", entries: [
                  { name: "Rosa", avatar: "queen", sub: "96%" },
                  { name: "Ben", avatar: "ghost", sub: "92%" },
                  { name: "Cy", avatar: "ninja", sub: "88%" }] },
                () => { window.__done = true; });
              const el = document.getElementById("vroom-cutscene");
              return { up: !!el,
                       plinths: el.querySelectorAll('.vroom-cut-plinth').length,
                       order: [...el.querySelectorAll('.vroom-cut-plinth')].map(p=>p.dataset.place),
                       names: [...el.querySelectorAll('.vroom-cut-pname')].map(n=>n.textContent),
                       art: el.querySelectorAll('.vroom-cut-figure svg').length,
                       floor: !!el.querySelector('.vroom-cut-floor'),
                       skip: !!el.querySelector('.vroom-cut-skip'),
                       z: el ? +getComputedStyle(el).zIndex : 0 };}""")
            check("it puts a full-screen cutscene up", shape.get("up") is True, shape)
            check("a race ends on a podium of three, each with a character",
                  shape.get("plinths") == 3 and shape.get("art") == 3, shape)
            # Second, first, third in DOM order, so the tallest block is
            # in the middle where a podium puts it.
            check("with first in the middle, not first on the left",
                  shape.get("order") == ["2", "1", "3"], shape.get("order"))
            check("and everyone on it is named",
                  shape.get("names") == ["Ben", "Rosa", "Cy"], shape.get("names"))
            # Over the bottom tab bar (200) and the tour overlay (205),
            # or it is a cutscene with a tab bar across it.
            check("above every other layer", shape.get("z", 0) >= 400, shape.get("z"))

            # THE WINNER IS NOT REVEALED IMMEDIATELY - that is the whole
            # point of the word "anticipation". Before the wind-up ends
            # the card is still hidden.
            cut.wait_for_timeout(900)
            early = cut.evaluate("()=>[...document.getElementById('vroom-cutscene').querySelectorAll('.vroom-cut-plinth')].filter(p=>p.classList.contains('is-on')).length")
            check("the podium is held back at first", early == 0, early)
            cut.wait_for_timeout(3400)
            late = cut.evaluate("()=>[...document.getElementById('vroom-cutscene').querySelectorAll('.vroom-cut-plinth')].filter(p=>p.classList.contains('is-on')).length")
            check("and all three are up before it ends", late == 3, late)

            # FIVE SECONDS, and done() always fires - the thing after it
            # is the results screen, so a cutscene that can swallow its
            # own callback is a match that never ends.
            cut.wait_for_function("()=>window.__done === true", timeout=8000)
            check("it finishes and hands over", True)
            check("and clears itself off the screen",
                  cut.evaluate("()=>!document.getElementById('vroom-cutscene')") is True)

            # SKIPPABLE. It is played with the same people over and over.
            cut.evaluate("""()=>{ window.__done2 = false;
              playVroomWinnerCutscene({ kind: "podium",
                entries: [{ name: "Sam", avatar: "ninja" }] },
                () => { window.__done2 = true; }); }""")
            cut.wait_for_timeout(400)
            cut.click("#vroom-cutscene")
            cut.wait_for_timeout(300)
            check("a tap skips it", cut.evaluate("()=>window.__done2 === true") is True)

            # muteBanners skips it outright, the same switch that mutes
            # the badge cutscene; reduceMotion keeps the reveal but not
            # the wind-up, rather than leaving a screen that sits still
            # for five seconds because the global animation:none rule
            # stripped the keyframes.
            muted = cut.evaluate("""()=>{ window.__done3 = false; theme.muteBanners = true;
              playVroomWinnerCutscene({ kind: "podium", entries: [{ name: "Kit", avatar: "ghost" }] },
                () => { window.__done3 = true; });
              return { done: window.__done3, up: !!document.getElementById("vroom-cutscene") }; }""")
            check("muteBanners skips it and still hands over",
                  muted.get("done") is True and muted.get("up") is False, muted)
            cut.evaluate("()=>{ theme.muteBanners = false; theme.reduceMotion = true; }")
            cut.evaluate("""()=>{ window.__done4 = false;
              playVroomWinnerCutscene({ kind: "podium", entries: [{ name: "Ola", avatar: "wizard" }] },
                () => { window.__done4 = true; }); }""")
            cut.wait_for_function("()=>window.__done4 === true", timeout=6000)
            check("reduceMotion still reveals, just faster", True)
            cut.evaluate("()=>{ theme.reduceMotion = false; }")

            # A TEAM WIN SHOWS THE WHOLE SIDE. Two people won it together
            # and showing one of them would be wrong - asked for in those
            # words. The rope comes with them, so it is the thing they
            # were actually pulling rather than a generic banner.
            # SCOPED TO THE LIVE OVERLAY, not the document. A finished
            # cutscene keeps its element for the 400ms it spends fading
            # out - it only drops its ID at handover - so a bare
            # document query finds the PREVIOUS one and reports a podium
            # inside a team win. The id is what identifies the live one;
            # that is the whole reason it is taken off first.
            team = cut.evaluate("""()=>{ window.__done5 = false;
              playVroomWinnerCutscene({ kind: "team", reveal: "Your side took it",
                entries: [{ name: "Ana", avatar: "cadet" }, { name: "Bo", avatar: "queen" }] },
                () => { window.__done5 = true; });
              const el = document.getElementById('vroom-cutscene');
              return { mates: el.querySelectorAll('.vroom-cut-mate').length,
                       art: el.querySelectorAll('.vroom-cut-mate .vroom-cut-figure svg').length,
                       rope: !!el.querySelector('.vroom-cut-rope'),
                       podium: !!el.querySelector('.vroom-cut-podium') }; }""")
            check("a team win shows every member of the side",
                  team.get("mates") == 2 and team.get("art") == 2, team)
            check("with the rope, and no podium", 
                  team.get("rope") is True and team.get("podium") is False, team)
            cut.wait_for_function("()=>window.__done5 === true", timeout=8000)

            # The winner it names has to be the one the standings put
            # first, or the cutscene crowns somebody the list then
            # places second.
            agree = cut.evaluate("""()=>{
              const d = { participants: {
                a: { name:"A", totalScore: 120 }, b: { name:"B", totalScore: 700 },
                c: { name:"C", totalScore: 450 } } };
              return vroomWinnerOf(d).name; }""")
            check("the winner matches the standings' own ranking", agree == "B", agree)
            podium3 = cut.evaluate("""()=>{
              const d = { participants: {
                a: { name:"A", avatarChar:"ninja", totalScore: 120 },
                b: { name:"B", avatarChar:"ghost", totalScore: 700 },
                c: { name:"C", avatarChar:"queen", totalScore: 450 },
                e: { name:"E", avatarChar:"cadet", totalScore: 300 } } };
              return vroomTopThree(d).map(p=>p.name); }""")
            check("and the podium is the top three in order, not four",
                  podium3 == ["B", "C", "E"], podium3)
        except Exception as e:
            check("the cutscene section ran at all", False, repr(e)[:200])
        finally:
            pg2 = locals().get("cut")
            if pg2 is not None:
                try:
                    pg2.close()
                except Exception:
                    pass

        ctx.close()
        br.close()
    srv.shutdown()
    print("\n%s  (%d failure(s))"
          % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES),
             len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
