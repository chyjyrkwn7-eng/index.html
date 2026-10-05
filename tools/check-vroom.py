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
import time, argparse
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
    /* TRANSACTIONS (build 238). The chat's reactions, votes and trim
       write through runTransaction so they build on the server's list
       rather than this tab's last snapshot. The fake runs the body
       against a real read and applies its writes afterwards - enough
       for the ORDER to be the real one: the read happens when the
       transaction runs, not when the button was pressed. */
    runTransaction(fn){
      const ops = [];
      const tx = {
        get: ref => ref.get(),
        update(ref, f){ ops.push(() => ref.update(f)); return tx; },
        set(ref, d, o){ ops.push(() => ref.set(d, o)); return tx; }
      };
      return Promise.resolve().then(() => fn(tx))
        .then(r => Promise.all(ops.map(f => f())).then(() => r));
    },
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
        '"tourRev":99,"rankMapFx244":true,"seenProfileTour":true,"seenModeSelectTour":true,"seenUnitSelectTour":true,'
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


def sections_246(ctx, open_tab, args):
    """Build 246: the race's 45-second questions, the wider race line, the
    countdown in the theme's colours, coming back to the lobby after a
    match, and a way out of a Tug of War or a Battle. Every check here was
    run against the build before it (--against) and fails there."""
    def active(pg):
        ctx.new_cdp_session(pg).send("Page.setWebLifecycleState", {"state": "active"})

    # ---- 13. every race question has 45 seconds ------------------------
    # "For the race lets not add time options, just make it where each
    # question has a 45 second timer, if you don't click in time it's
    # wrong - you'd get a thing where it shows the right answer but counts
    # it as wrong for you - and then goes to the next one."
    # A room document from an older build still carries timeLimit:10, and
    # it must neither break the run nor come back as an overall limit.
    print("\n13. a race gives every question 45 seconds")
    try:
        rq = open_tab("Rae", "ninja", 3000, "R45A-0001", badges=1)
        active(rq)
        rq.evaluate("""()=>{ const parts={
            me:{name:'Rae',avatarChar:'ninja',joinedAt:1,ready:true,finished:false,progress:0,seen:Date.now()},
            a:{name:'A',avatarChar:'ghost',joinedAt:2,ready:true,finished:false,progress:10,seen:Date.now()} };
          return fbDb.collection('vrooms').doc('RACE45').set({status:'starting',game:'race',timeLimit:10,
            units:['Identity Crimes'],startAt:Date.now()-2000,chatMessages:[],participants:parts}); }""")
        rq.wait_for_timeout(300)
        rq.evaluate("""()=>{ store.practiceTestPassed=false; store.practiceExamPerfect=false; saveStore();
          vroomCode='RACE45'; vroomMyKey='me'; vroomIsHost=true; theme.autoAdvance=false;
          beginVirtualRoomTest(['Identity Crimes'], 10, null, 0); }""")
        rq.wait_for_selector(".qpanel .choice", timeout=25000)
        rq.wait_for_timeout(400)
        first = rq.evaluate("""()=>{ const c=document.querySelector('.qpanel .race-qclock');
          return { clock: c ? c.textContent.trim() : null, overall: (typeof practiceTestMinutes!=='undefined') ? practiceTestMinutes : 'n/a',
                   timerline: !document.getElementById('timerline').hidden }; }""")
        check("a race question shows its own clock, starting at 45 seconds",
              bool(first["clock"]) and first["clock"].rstrip("s") in ("45", "44"), first)
        check("and the room's old ten-minute limit is not read", first["overall"] is None and not first["timerline"], first)

        # A CLOCK, NOT A COUNT: the number is read off a deadline, so it
        # is whatever is left, however the ticks were throttled.
        rq.evaluate("()=>{ raceQuestionDeadline = Date.now() + 20400; }")
        rq.wait_for_timeout(450)
        mid = rq.evaluate("()=>document.querySelector('.qpanel .race-qclock').textContent.trim()")
        check("the clock reads the time left off a deadline", mid.rstrip("s") in ("20", "21"), mid)

        # Pause holds it.
        rq.evaluate("()=>{ raceQuestionDeadline = Date.now() + 10000; pauseRun(); }")
        rq.wait_for_timeout(1600)
        rq.evaluate("()=>resumeRun()")
        rq.wait_for_timeout(300)
        held = rq.evaluate("()=>Math.round((raceQuestionDeadline - Date.now())/100)/10")
        check("pausing holds the question's clock", 9.2 <= held <= 10.1, held)

        # RUNNING OUT: what a phone coming back from the lock screen sees -
        # the deadline has already gone.
        before = rq.evaluate("()=>({pos:pos, qi:order[pos]})")
        rq.evaluate("()=>{ raceQuestionDeadline = Date.now() - 5; }")
        rq.wait_for_timeout(350)
        rev = rq.evaluate("""()=>{ const cs=[...document.querySelectorAll('.qpanel .choice')];
          const st=document.querySelector('.qpanel .status'); const nb=document.getElementById('nextbtn');
          const right = cs.filter(c=>c.classList.contains('is-right'));
          return { pos:pos, all:cs.length, off:cs.filter(c=>c.disabled).length, right:right.length,
                   rightIsAnswer: right.length===1 && +right[0].dataset.index===correctSlot(order[pos]),
                   bad: !!st && st.classList.contains('bad'), status: st ? st.textContent : '',
                   next: !!nb && !nb.hidden }; }""")
        check("out of time: the right answer is shown and every choice is locked",
              rev["pos"] == before["pos"] and rev["right"] == 1 and rev["rightIsAnswer"]
              and rev["off"] == rev["all"] and rev["bad"] and not rev["next"], rev)
        rq.evaluate("()=>{ const c=[...document.querySelectorAll('.qpanel .choice')][0]; c && c.click(); choose(0); }")
        check("and nothing can be picked over it",
              rq.evaluate("(qi)=>picked[qi]===undefined", before["qi"]))
        rq.wait_for_timeout(3300)
        after = rq.evaluate("""(qi)=>({pos:pos, timedOut: !!timedOutSet[qi]})""", before["qi"])
        check("then it moves on by itself, counted as a miss",
              after["pos"] == before["pos"] + 1 and after["timedOut"], {"before": before, "after": after})
        rq.wait_for_timeout(400)
        prog = rq.evaluate("""()=>fbDb.collection('vrooms').doc('RACE45').get().then(d=>((d.data().participants||{}).me||{}).progress)""")
        check("and the race line hears about it like any answer", (prog or 0) > 0, prog)

        # A pause during the reveal holds the reveal.
        b2 = rq.evaluate("()=>pos")
        rq.evaluate("()=>{ raceQuestionDeadline = Date.now() - 5; }")
        rq.wait_for_timeout(300)
        rq.evaluate("()=>pauseRun()")
        rq.wait_for_timeout(3400)
        held_pos = rq.evaluate("()=>pos")
        rq.evaluate("()=>resumeRun()")
        rq.wait_for_timeout(3300)
        check("a pause in the middle of the reveal holds it, and it carries on after",
              held_pos == b2 and rq.evaluate("()=>pos") == b2 + 1,
              {"was": b2, "while paused": held_pos, "after": rq.evaluate("()=>pos")})

        # An answer picked but not confirmed stands: you did click in time.
        b3 = rq.evaluate("()=>({pos:pos, qi:order[pos]})")
        rq.evaluate("()=>{ const r=correctSlot(order[pos]); choose(r); raceQuestionDeadline = Date.now() - 5; }")
        rq.wait_for_timeout(700)
        kept = rq.evaluate("(qi)=>({pos:pos, timedOut: !!timedOutSet[qi], picked: picked[qi]!==undefined})", b3["qi"])
        check("an answer picked before the clock ran out stands, with no reveal",
              kept["pos"] == b3["pos"] + 1 and not kept["timedOut"] and kept["picked"], kept)

        # Reduce motion, and the LAST question: it still reveals, then ends the run.
        rq.evaluate("()=>{ theme.reduceMotion=true; pos = order.length - 1; openQuestion(); }")
        rq.wait_for_timeout(300)
        lastqi = rq.evaluate("()=>order[pos]")
        rq.evaluate("()=>{ raceQuestionDeadline = Date.now() - 5; }")
        rq.wait_for_timeout(300)
        rev_last = rq.evaluate("()=>document.querySelectorAll('.qpanel .choice.is-right').length")
        rq.wait_for_timeout(3600)
        end = rq.evaluate("""(qi)=>({results: !!document.querySelector('[data-screen=results]'), done: !testInProgress,
            missed: (lastRunResult && lastRunResult.missed || []).indexOf(qi) >= 0,
            practice: !!store.practiceTestPassed || !!store.practiceExamPerfect})""", lastqi)
        check("the last question reveals too, then the run ends on the results with it missed",
              rev_last == 1 and end["results"] and end["done"] and end["missed"], {"reveal": rev_last, **end})
        check("and a race never marks the Practice Test passed", not end["practice"], end)
        rq.evaluate("()=>{ theme.reduceMotion=false; }")
        rq.close()
    except Exception as e:
        check("the 45-second section ran at all", False, repr(e)[:240])

    # ---- 14. the race line, a smidge wider ----------------------------
    # "The race stuff at the top of race. If you are able to make that a
    # smidge wider so it'd be bigger that would be great." Measured on the
    # reference phone and on a 320px one, with a crowd of eight.
    print("\n14. the race line is wider, and still fits")
    try:
        rw = open_tab("Rae", "ninja", 3000, "RWID-0001", badges=1)
        active(rw)
        rw.evaluate("""()=>{ const parts={ me:{name:'Rae',avatarChar:'ninja',joinedAt:1,ready:true,finished:false,progress:0} };
            [['a',8],['b',8],['c',10],['d',55],['e',58],['f',92],['g',100]].forEach(([k,p],i)=>parts[k]={name:k,avatarChar:'ghost',joinedAt:2+i,ready:true,finished:p===100,progress:p});
            return fbDb.collection('vrooms').doc('RWIDE').set({status:'starting',game:'race',units:['Identity Crimes'],startAt:Date.now()-2000,chatMessages:[],participants:parts}); }""")
        rw.wait_for_timeout(300)
        rw.evaluate("()=>{ vroomCode='RWIDE'; vroomMyKey='me'; vroomIsHost=true; beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }")
        rw.wait_for_selector(".qpanel .choice", timeout=25000)
        rw.wait_for_timeout(1500)
        MEAS = """()=>{ const t=document.querySelector('#vroomracebar .vroom-racetrack').getBoundingClientRect();
            const ms=[...document.querySelectorAll('#vroomracebar .vroom-race-marker')].map(m=>m.getBoundingClientRect());
            const pb=document.getElementById('pausebtn').getBoundingClientRect();
            const flag=document.querySelector('#vroomracebar .vroom-racetrack-finish').getBoundingClientRect();
            let touch=0; for(let i=0;i<ms.length;i++) for(let j=i+1;j<ms.length;j++){ const a=ms[i],b=ms[j];
              const dx=(a.left+a.width/2)-(b.left+b.width/2), dy=(a.top+a.height/2)-(b.top+b.height/2);
              if(Math.abs(dx) < 2 && Math.hypot(dx,dy) < a.width - 1) touch++; }
            return { vw:innerWidth, track:Math.round(t.width), share:+(t.width/innerWidth).toFixed(3), marker:Math.round(ms[0].width), n:ms.length,
              minLeft:Math.round(Math.min(...ms.map(m=>m.left))), maxRight:Math.round(Math.max(flag.right, ...ms.map(m=>m.right))),
              top:Math.round(t.top), pauseBottom:Math.round(pb.bottom), stackedTouch:touch,
              hscroll: document.documentElement.scrollWidth - innerWidth }; }"""
        m440 = rw.evaluate(MEAS)
        check("the track takes more of the phone's width than it did (339px of 440)",
              m440["track"] >= 355, m440)
        check("and the markers are bigger with it", m440["marker"] >= 25, m440)
        check("markers stacked on one spot still do not overlap", m440["stackedTouch"] == 0, m440)
        check("it sits clear under Pause and chat", m440["top"] >= m440["pauseBottom"], m440)
        # A TABLET PINS PAUSE AND CHAT IN THE CORNER, at a tablet's size -
        # and the track used to start right under the counter row, so on
        # an iPad both buttons sat on the finish flag and on whoever was
        # at 90-100%. Found looking at the race line on the reference
        # iPad for this change.
        rw.set_viewport_size({"width": 834, "height": 1194})
        rw.wait_for_timeout(700)
        clash = rw.evaluate("""()=>{ const t=document.querySelector('#vroomracebar .vroom-racetrack').getBoundingClientRect();
            const hits=[...document.querySelectorAll('#pausebtn:not([hidden]), .chatdock-btn, #roomchat-fab')].filter(b=>b.getClientRects().length).map(b=>{
              const r=b.getBoundingClientRect(); const ix=Math.min(r.right,t.right)-Math.max(r.left,t.left), iy=Math.min(r.bottom,t.bottom)-Math.max(r.top,t.top);
              return [b.id||b.className.split(' ')[0], Math.round(ix), Math.round(iy)]; }).filter(x=>x[1]>0&&x[2]>0);
            return {hits:hits, trackTop:Math.round(t.top)}; }""")
        check("on an iPad the track sits clear of the pinned Pause and chat buttons", not clash["hits"], clash)
        rw.set_viewport_size({"width": 320, "height": 568})
        rw.wait_for_timeout(700)
        m320 = rw.evaluate(MEAS)
        check("on a 320px phone it still fits: nothing off either edge, no sideways scroll",
              m320["minLeft"] >= 0 and m320["maxRight"] <= m320["vw"] and m320["hscroll"] <= 0, m320)
        rw.close()
    except Exception as e:
        check("the race-line section ran at all (246)", False, repr(e)[:240])

    # ---- 15. the countdown in the theme's colours ----------------------
    # "Ensure the count down numbers and start are updated for other
    # themes." The number already took the theme's gradient; the screen
    # around it was the default's - flat black, a grey label, a
    # one-colour ring and a fixed green tick.
    print("\n15. the countdown and 'Everyone's ready!' wear the theme")
    try:
        cd = open_tab("Rae", "ninja", 3000, "CDWN-0001", badges=1)
        active(cd)
        seen = {}
        for acc in ("ink", "adept", "titan"):
            seen[acc] = cd.evaluate("""(a)=>{ theme.accent=a; applyTheme(); stage.replaceChildren();
              const rd=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
              const probe=document.createElement('i'); document.body.appendChild(probe);
              const rgb=v=>{ probe.style.color=v; return getComputedStyle(probe).color; };
              const c1=rgb(rd('--theme-c1')), c2=rgb(rd('--theme-c2'));
              showVroomCountdown(Date.now()+5000, ()=>{});
              const ov=document.getElementById('vroom-reveal-overlay');
              const out={ c1:c1, c2:c2,
                bg: getComputedStyle(ov).backgroundImage,
                label: getComputedStyle(document.getElementById('vroom-reveal-label')).color,
                ring: getComputedStyle(document.getElementById('vroom-reveal-ring'),'::before').backgroundImage };
              ov.remove();
              showVroomReadyFlourish(()=>{});
              const fl=document.getElementById('vroom-flourish-overlay');
              const ck=getComputedStyle(document.getElementById('vroom-flourish-check'));
              out.flbg=getComputedStyle(fl).backgroundImage; out.check=ck.backgroundImage + ' ' + ck.backgroundColor + ' / ' + ck.color;
              fl.remove(); probe.remove(); return out; }""", acc)
        glow = all("radial-gradient" in v["bg"] and "radial-gradient" in v["flbg"] for v in seen.values())
        check("the count and the ready beat sit on the theme's glow, not flat black", glow,
              {k: v["bg"][:60] for k, v in seen.items()})
        check("'Starting in' is in the theme's colour", all(v["label"] == v["c1"] for v in seen.values()),
              {k: (v["label"], v["c1"]) for k, v in seen.items()})
        check("the ring runs through the theme's own colours",
              all(v["c1"].replace(" ", "") in v["ring"].replace(" ", "") for v in seen.values()),
              {k: v["ring"][:80] for k, v in seen.items()})
        check("and the tick is the theme's, not a fixed green",
              all("61, 214, 140" not in v["check"] for v in seen.values()) and seen["ink"]["check"] != seen["adept"]["check"],
              {k: v["check"][:90] for k, v in seen.items()})
        cd.evaluate("()=>{ theme.accent='ink'; applyTheme(); }")
        cd.close()
    except Exception as e:
        check("the countdown section ran at all", False, repr(e)[:240])

    # ---- 16. coming back to the lobby after a race -----------------------
    # Reported as the Virtual Room misbehaving on a re-run, and it did:
    # the room stays on "starting" through a race, so whoever got back to
    # the lobby before the host was dropped into a new race on their own;
    # everybody's ready flag survived the match, so one ready-up started
    # the next race with people still on their results; and somebody who
    # had closed the app between rounds (still on the room document) held
    # the finale on "2/3" for good.
    print("\n16. back to the lobby after a race, and a second race")
    try:
        ha = open_tab("Hana", "ninja", 3000, "REHA-0001", badges=1)
        gb = open_tab("Gus", "ghost", 3000, "REGB-0002", badges=1)
        for pg in (ha, gb):
            active(pg)
        ha.evaluate("()=>createVirtualRoomLobby(['Identity Crimes'], null, 'race')")
        ha.wait_for_function("() => typeof vroomCode === 'string' && vroomCode", timeout=20000)
        rcode = ha.evaluate("()=>vroomCode")
        join_lobby(gb, rcode)
        ha.wait_for_function("() => document.querySelectorAll('.vroom-row').length >= 2", timeout=25000)
        # Somebody who sat in this room and closed the app: on the
        # document, gone from presence, never coming back.
        ha.evaluate("""()=>fbDb.collection('vrooms').doc(vroomCode).update({'participants.zed':
            {name:'Zed',avatarChar:'alien',joinedAt:Date.now(),seen:Date.now()-10*60*1000,ready:false,finished:false,progress:0}})""")
        ha.wait_for_timeout(600)
        # Each device's own ready writes, recorded as it sends them. Read
        # back off the shared fake instead, two tabs writing in the same
        # instant lose one write to each other (section 7 says why) - the
        # harness, not the app, so the app is asked what it SENT.
        for pg in (ha, gb):
            pg.evaluate("""()=>{ window.__readyWrites=[]; const oc=fbDb.collection.bind(fbDb);
              fbDb.collection = name => { const c=oc(name); const od=c.doc.bind(c);
                c.doc = id => { const d=od(id); const ou=d.update.bind(d);
                  d.update = f => { Object.keys(f||{}).forEach(k=>{ if(/\\.ready$/.test(k)) window.__readyWrites.push([k, f[k], vroomTestStarted]); }); return ou(f); };
                  return d; };
                return c; }; }""")
        for pg in (ha, gb):
            tap(pg, ".vroom-readyup-btn", "ready-up")
            pg.wait_for_timeout(300)
        for pg in (ha, gb):
            pg.wait_for_function("() => typeof vroomStartAt === 'number' && vroomStartAt && !!document.querySelector('.qpanel .choice')", timeout=40000)
        ha.wait_for_timeout(800)
        doc = ha.evaluate("()=>fbDb.collection('vrooms').doc(vroomCode).get().then(d=>d.data())")
        parts = doc.get("participants", {})
        spent = {n: pg.evaluate("()=>{ const w=(window.__readyWrites||[]).filter(x=>x[0]==='participants.'+vroomMyKey+'.ready'); return w.length ? w[w.length-1] : null; }")
                 for n, pg in (("host", ha), ("guest", gb))}
        check("starting a match uses up everybody's ready",
              all(v and v[1] is False and v[2] is True for v in spent.values()), spent)
        check("and the match names who is in it - not the classmate who closed the app",
              sorted(doc.get("racers") or []) == sorted(k for k in parts if k != "zed"), doc.get("racers"))
        first_start = ha.evaluate("()=>vroomStartAt")
        for pg in (ha, gb):
            pg.evaluate("""()=>{ theme.muteBanners=true; order.forEach(qi=>{ picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
              stopQuestionTimer(); summarize(); }""")
            pg.wait_for_function("""()=>fbDb.collection('vrooms').doc(vroomCode).get()
              .then(d => !!(((d.data() || {}).participants || {})[vroomMyKey] || {}).finished)""", timeout=10000)
        ha.wait_for_timeout(1500)
        wc = ha.evaluate("()=>(document.querySelector('.vroom-wait-count')||{}).textContent")
        check("the finale counts the people racing, so it is not waiting on somebody who left",
              wc == "2/2", wc)
        # The guest comes back first.
        gb.evaluate("()=>{ document.getElementById('vroom-race-cut')?.remove(); vroomReturnToLobby(); }")
        gb.wait_for_timeout(3500)
        gstate = gb.evaluate("""()=>({question: !!document.querySelector('.qpanel .choice'), lobby: !!document.querySelector('.screen-vroom-lobby'),
            startAt: vroomStartAt, readyOff: !!(document.querySelector('.vroom-readyup-btn')||{}).disabled})""")
        check("whoever gets back before the host is not dropped into a race on their own",
              gstate["lobby"] and not gstate["question"] and gstate["startAt"] == first_start, gstate)
        ha.evaluate("()=>{ document.getElementById('vroom-race-cut')?.remove(); vroomReturnToLobby(); }")
        ha.wait_for_timeout(3500)
        st = ha.evaluate("()=>fbDb.collection('vrooms').doc(vroomCode).get().then(d=>d.data().status)")
        idle = {n: pg.evaluate("()=>({q: !!document.querySelector('.qpanel .choice'), s: vroomStartAt})") for n, pg in (("host", ha), ("guest", gb))}
        check("the host coming back opens the lobby, and nothing starts until people ready up",
              st == "waiting" and not idle["host"]["q"] and not idle["guest"]["q"], {"status": st, **idle})
        for pg in (ha, gb):
            tap(pg, ".vroom-readyup-btn", "ready-up, second race")
            pg.wait_for_timeout(300)
        ok = True
        try:
            for pg in (ha, gb):
                pg.wait_for_function("(s) => vroomStartAt && vroomStartAt !== s && !!document.querySelector('.qpanel .choice')", arg=first_start, timeout=40000)
        except Exception:
            ok = False
        check("and a second race starts for both once both are ready", ok)
        for pg in (ha, gb):
            try:
                pg.evaluate("()=>{ stopQuestionTimer(); leaveVirtualRoom(); }")
            except Exception:
                pass
            pg.close()
    except Exception as e:
        check("the back-to-the-lobby section ran at all", False, repr(e)[:240])

    # ---- 17. a way out of a Tug of War or a Battle -----------------------
    # Neither showed Pause, neither has a back link, and the tab bar is
    # forced off for both - so there was no way to leave one mid-match
    # short of closing the app.
    print("\n17. a Tug of War or a Battle can be left mid-match")
    try:
        tl = open_tab("Tam", "ninja", 3000, "TLEV-0001", badges=1)
        active(tl)
        for game in ("tug", "battle"):
            tl.evaluate("""(game)=>{ const parts={me:{name:'Tam',avatarChar:'ninja',joinedAt:1,ready:true,seen:Date.now()},
                 b:{name:'Bo',avatarChar:'robot',joinedAt:2,ready:true,seen:Date.now()}};
               const d={status:'starting', game:game, units:['Identity Crimes'], startAt:Date.now()-1000, chatMessages:[], participants:parts, racers:['me','b']};
               const teams={me:'a', b:'b'};
               if(game==='tug') d.tug={progress:{}, over:false, winner:null, finalPos:0, count:0, teams};
               else d.battle={log:[], progress:{}, over:false, winner:null, count:0, teams};
               return fbDb.collection('vrooms').doc('LEAVE'+game).set(d).then(()=>{ vroomCode='LEAVE'+game; vroomMyKey='me'; showVirtualRoomLobby(); }); }""", game)
            tl.wait_for_selector(".screen-%s .choice" % game, timeout=20000)
            tl.wait_for_timeout(500)
            vis = tl.evaluate("()=>{ const b=document.getElementById('pausebtn'); return !b.hidden && b.getBoundingClientRect().height >= 40; }")
            check("%s: Pause is on screen during the match" % game, vis)
            tl.click("#pausebtn")
            tl.wait_for_timeout(400)
            sheet = tl.evaluate("()=>!!document.querySelector('.vroom-leave-confirm')")
            tl.evaluate("()=>{ [...document.querySelectorAll('.vroom-leave-confirm button')].find(b=>/keep/i.test(b.textContent)).click(); }")
            tl.wait_for_timeout(400)
            stayed = tl.evaluate("(g)=>!document.querySelector('.vroom-leave-confirm') && !!document.querySelector('.screen-'+g)", game)
            check("%s: it asks first, and Keep playing leaves the match as it was" % game, sheet and stayed, {"asked": sheet, "stayed": stayed})
            tl.click("#pausebtn")
            tl.wait_for_timeout(400)
            tl.evaluate("()=>{ [...document.querySelectorAll('.vroom-leave-confirm button')].find(b=>/^leave$/i.test(b.textContent.trim())).click(); }")
            tl.wait_for_timeout(900)
            gone = tl.evaluate("""(g)=>fbDb.collection('vrooms').doc('LEAVE'+g).get().then(d=>({left: !((d.data().participants||{}).me),
                home: !!document.querySelector('[data-screen=home]'), code: vroomCode}))""", game)
            check("%s: Leave takes you out of the room and home" % game, gone["left"] and gone["home"] and not gone["code"], gone)
        tl.close()
    except Exception as e:
        check("the leave-a-team-match section ran at all", False, repr(e)[:240])


    # ---- 18. there is always a way back to the main menu -----------------
    # A classmate's report, from a desktop: "Can't leave back to main menu
    # after a game with multiple participants concludes." Two ways it was
    # true. Once everybody had finished, the waiting card's Leave room
    # went away and nothing replaced it until the leaderboard rolled -
    # at least twelve seconds, up to a minute - with no Pause, no tab bar
    # and no link on the screen. And the leaderboard scene is a fixed
    # layer that cannot scroll, so with a full room on a small phone its
    # Main menu button was drawn below the bottom of the screen.
    print("\n18. there is always a way back to the main menu after a race")
    try:
        lv = open_tab("Liv", "ninja", 3000, "LEAV-0001", badges=1)
        active(lv)
        lv.evaluate("""()=>{ const parts={me:{name:'Liv',avatarChar:'ninja',joinedAt:1,ready:true,finished:false,progress:0,seen:Date.now()}};
            ['a','b','c','d','e','f','g'].forEach((k,i)=>parts[k]={name:'P'+k,avatarChar:['ghost','alien','tempest','robot'][i%4],joinedAt:2+i,ready:true,seen:Date.now(),
              finished:true,progress:100,score:90,elapsedMs:200000+i,xp:150+i,totalScore:150+i,revealDone:true,
              xpLines:[{key:'correct',label:'11 correct',value:110},{key:'speed',label:'Speed',value:40+i}]});
            /* And one who closed the app mid-race: unfinished, no
               heartbeat for ten minutes, still carrying the lifetime XP
               it joined with. It must not hold the room up, and it must
               not top the board with that number either. */
            parts.gone={name:'Gone',avatarChar:'alien',joinedAt:20,ready:true,seen:Date.now()-10*60*1000,finished:false,progress:40,xp:98765};
            return fbDb.collection('vrooms').doc('LEAVEALL').set({status:'starting',game:'race',units:['Identity Crimes'],startAt:Date.now()-2000,chatMessages:[],participants:parts}); }""")
        lv.wait_for_timeout(300)
        lv.evaluate("""()=>{ vroomCode='LEAVEALL'; vroomMyKey='me'; vroomIsHost=true; beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }""")
        lv.wait_for_selector(".qpanel .choice", timeout=25000)
        lv.evaluate("""()=>{ order.forEach(qi=>{ picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); stopQuestionTimer(); summarize(); }""")
        try:
            lv.wait_for_function("()=>document.querySelector('.vroom-waitcard.is-all-in')", timeout=15000)
            allin = True
        except Exception:
            allin = False
        lv.wait_for_timeout(500)
        way = lv.evaluate("""()=>{ const b=document.querySelector('.vroom-wait-leave'); if(!b || b.hidden || !b.getClientRects().length) return {shown:false};
            b.scrollIntoView({block:'center', behavior:'instant'}); const r=b.getBoundingClientRect();
            const top=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); return {shown:true, hit: top===b || b.contains(top)}; }""")
        check("a racer who closed the app mid-race does not hold the room up", allin,
              lv.evaluate("()=>(document.querySelector('.vroom-wait-count')||{}).textContent"))
        top = lv.evaluate("()=>vroomRankedEntries(lastFinaleData||{}).map(e=>e.key)")
        check("and is ranked on what they finished (nothing), not on the XP they joined with",
              bool(top) and top[0] != "gone" and top[-1] == "gone", top)
        check("with everybody finished and the leaderboard still to come, Leave room is still there", way.get("shown") and way.get("hit"), way)
        if way.get("shown"):
            lv.click(".vroom-wait-leave")
            lv.wait_for_timeout(400)
            lv.evaluate("()=>[...document.querySelectorAll('#stage button')].find(b=>b.textContent.trim()==='Leave').click()")
            lv.wait_for_timeout(14000)
            after = lv.evaluate("()=>({home: !!document.querySelector('[data-screen=home]'), code: vroomCode, cut: !!document.getElementById('vroom-race-cut'), prep: !!document.getElementById('vroom-prep')})")
            check("and leaving there lands on Home, with no leaderboard rolling over it afterwards",
                  after["home"] and not after["code"] and not after["cut"] and not after["prep"], after)
        # The leaderboard scene, a room of eight, on a 320x568 phone.
        lv.set_viewport_size({"width": 320, "height": 568})
        lv.evaluate("""()=>{ const parts={me:{name:'Liv',avatarChar:'ninja',joinedAt:1,finished:true,xp:140,elapsedMs:1,xpLines:[]}};
            ['a','b','c','d','e','f','g'].forEach((k,i)=>parts[k]={name:'P'+k,avatarChar:'ghost',joinedAt:2+i,finished:true,xp:150+i,elapsedMs:2,xpLines:[]});
            vroomMyKey='me'; theme.reduceMotion=true; playVroomRaceCutscene(vroomRankedEntries({participants:parts})); }""")
        lv.wait_for_function("()=>document.querySelector('#vroom-race-cut.is-done')", timeout=20000)
        lv.wait_for_timeout(800)
        mm = lv.evaluate("""()=>{ const b=[...document.querySelectorAll('#vroom-race-cut .vrc-exits button')].find(x=>/main menu/i.test(x.textContent));
            const r=b.getBoundingClientRect(); const cx=r.left+r.width/2, cy=r.top+r.height/2;
            const top=(cy>0&&cy<innerHeight)?document.elementFromPoint(cx,cy):null;
            return {y:Math.round(r.top), bottom:Math.round(r.bottom), vh:innerHeight, hit: !!top && (top===b||b.contains(top))}; }""")
        check("in a room of eight on a 320px phone, the scene's Main menu is on screen and tappable",
              mm["hit"] and mm["bottom"] <= mm["vh"], mm)
        lv.click("#vroom-race-cut .vrc-exits button.ghost")
        lv.wait_for_timeout(900)
        check("and it goes home", lv.evaluate("()=>!!document.querySelector('[data-screen=home]') && !document.getElementById('vroom-race-cut')"))
        lv.evaluate("()=>{ theme.reduceMotion=false; }")
        lv.close()
    except Exception as e:
        check("the way-back section ran at all", False, repr(e)[:240])

    # ---- 19. retired characters show up as what they became ------------
    # "Make sure the Virtual Room cutscenes/end screens show the current
    # characters" - the SWAT (245) and the Robot (244) are retired and
    # drawn as the Ninja. The drawing already went through
    # RETIRED_CHARACTER_TO; the glow each row is tinted with did not, so a
    # Ninja stood in the Robot's light on the leaderboard scene.
    print("\n19. a retired character is the Ninja everywhere in a room, glow and all")
    try:
        rc = open_tab("Rae", "ninja", 3000, "RETC-0001", badges=1)
        active(rc)
        got = rc.evaluate("""()=>{ vroomMyKey='me';
            const mk=(k,a,j,x)=>({key:k, p:{name:k, avatarChar:a, joinedAt:j, xpLines:[]}, xp:x});
            playVroomRaceCutscene([mk('me','ghost',1,300), mk('r','robot',2,200), mk('s','swat',3,100)]);
            const rows=[...document.querySelectorAll('#vroom-race-cut .vrc-row')];
            /* Every drawing numbers its own gradient ids, so compare with
               the ids taken out. */
            const norm = h => h.replace(/(id="|#)[A-Za-z0-9_-]+/g, '');
            const ninjaSvg = norm(buildAvatarCharSVGSafe('ninja').outerHTML);
            const out = rows.map(x=>({pl: x.style.getPropertyValue('--pl'), ninja: norm(x.querySelector('.vrc-fig svg').outerHTML) === ninjaSvg}));
            document.getElementById('vroom-race-cut').remove();
            return { rows: out, ninjaGlow: AVATAR_GLOW.ninja }; }""")
        retired = got["rows"][1:]
        check("the Robot and the SWAT are drawn as the Ninja on the leaderboard scene", all(r["ninja"] for r in retired), got)
        check("and glow as the Ninja too", all(r["pl"] == got["ninjaGlow"] for r in retired), got)
        rc.close()
    except Exception as e:
        check("the retired-characters section ran at all", False, repr(e)[:240])



# ---------------------------------------------------------------------------
# BUILD 313: "please ensure all the virtual room modes work properly, test
# this over and over ... check to see it works with like 20 people or 2 and
# so on ... ensure the result screen works well for the virtual room
# especially." One real device and up to nineteen simulated classmates, who
# write to the room exactly what their own devices would: progress, a finish
# with its XP lines, a reveal done, a heartbeat, a tug row, a battle hit.
BOTS_313 = r"""
(() => {
  const B = window.__vrBots = { code: null, timers: [], gone: new Set(), parts: {} };
  const NAMES = ["Ava","Ben","Cy","Dee","Eli","Fay","Gus","Hana","Ivy","Jon","Kim","Lou","Max","Nia","Oto","Pia","Quin","Rae","Sol","Tao"];
  const AV = AVATAR_CHARACTERS.map(c => c.id);
  B.room = (code, n, extra, mine) => {
    B.stop(); B.code = code; B.gone = new Set();
    const now = Date.now(); const parts = {};
    parts.me = Object.assign({ name: store.firstName, avatarChar: store.avatarChar, joinedAt: now - 100000, ready: true,
                               finished: false, progress: 0, seen: now }, mine || {});
    for(let i = 1; i < n; i++){
      parts["b" + i] = Object.assign({ name: NAMES[(i - 1) % NAMES.length], avatarChar: AV[i % AV.length],
        joinedAt: now - 100000 + i * 10, ready: true, finished: false, progress: 0, seen: now, level: 5 + i, badges: i % 4 },
        (extra && extra(i)) || {});
    }
    B.parts = parts;
    return parts;
  };
  B.upd = f => fbDb.collection("vrooms").doc(B.code).update(f);
  B.keys = () => Object.keys(B.parts).filter(k => k !== "me");
  B.stop = () => { B.timers.forEach(t => { clearInterval(t); clearTimeout(t); }); B.timers = []; };
  B.beat = () => B.timers.push(setInterval(() => {
    const f = {}; B.keys().forEach(k => { if(!B.gone.has(k)) f["participants." + k + ".seen"] = Date.now(); });
    if(Object.keys(f).length) B.upd(f).catch(() => {});
  }, 2500));
  B.finished = (i, xp) => ({ finished: true, progress: 100, score: 80, elapsedMs: 60000 + i * 500, xp: xp, totalScore: xp,
    revealDone: true, xpLines: [{ key: "correct", label: "8 correct", value: Math.round(xp * .6) }, { key: "speed", label: "Speed", value: xp - Math.round(xp * .6) }] });
  B.tug = (k, every, right, count) => {
    let pos = 0, correct = 0, pull = 0;
    B.timers.push(setInterval(() => {
      if(B.gone.has(k) || pos >= count) return;
      const ok = Math.random() < right; pos++; if(ok){ correct++; pull += 1; } else pull -= .25;
      B.upd({ ["tug.progress." + k]: { pos, correct, pull: Math.round(pull * 1000) / 1000, done: pos >= count, at: Date.now() } }).catch(() => {});
    }, every));
  };
  B.battle = (k, every, right, count) => {
    let pos = 0, correct = 0;
    B.timers.push(setInterval(() => {
      if(B.gone.has(k) || pos >= count) return;
      const ok = Math.random() < right; pos++; if(ok) correct++;
      const f = { ["battle.progress." + k]: { pos, correct, done: pos >= count, at: Date.now() } };
      if(ok) f["battle.log"] = firebase.firestore.FieldValue.arrayUnion({ id: k + "-" + pos + "-" + Math.random().toString(36).slice(2, 6), at: Date.now(), from: k, kind: "hit", dmg: 5 });
      B.upd(f).catch(() => {});
    }, every));
  };
  B.die = k => { B.gone.add(k); return B.upd({ ["participants." + k + ".seen"]: Date.now() - 10 * 60 * 1000 }); };
})();
"""


def sections_313(ctx, open_tab, args):
    """Build 313. Every check here was run against build 312 (--against
    /tmp/claude-0/b313/old312.html) and fails there."""
    def active(pg):
        ctx.new_cdp_session(pg).send("Page.setWebLifecycleState", {"state": "active"})

    def home(pg):
        pg.evaluate("""()=>{ try{ __vrBots.stop(); }catch(e){} document.getElementById('vroom-race-cut')?.remove();
          document.getElementById('vroom-prep')?.remove(); document.getElementById('vroom-cutscene')?.remove();
          try{ stopQuestionTimer(); }catch(e){} try{ leaveVirtualRoom(); }catch(e){} testInProgress=false; showHome(); }""")
        pg.wait_for_timeout(300)

    # ---- 20. a race, at every size ----------------------------------------
    print("\n20. (313) a race of 2, 3, 4, 8 and 20: it counts, it ranks, the screen fits")
    try:
        pg = open_tab("Rae", "ninja", 3000, "R313-0001", badges=1)
        active(pg)
        pg.evaluate(BOTS_313)
        pg.evaluate("()=>{ theme.reduceMotion = true; }")
        for n in (2, 3, 4, 8, 20):
            code = "R313N%d" % n
            before = pg.evaluate("()=>store.vrMatches || 0")
            pg.evaluate("""([code, n])=>{ const parts = __vrBots.room(code, n, i => __vrBots.finished(i, 90 + i * 7));
              return fbDb.collection('vrooms').doc(code).set({ status:'starting', game:'race', units:['Identity Crimes'],
                startAt: Date.now() - 2000, chatMessages: [], participants: parts, racers: Object.keys(parts) }); }""", [code, n])
            pg.wait_for_timeout(250)
            pg.evaluate("""(code)=>{ vroomCode=code; vroomMyKey='me'; vroomIsHost=true; theme.autoAdvance=false;
              beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }""", code)
            pg.wait_for_selector(".qpanel .choice", timeout=25000)
            pg.evaluate("()=>{ order.forEach(qi=>{ picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); stopQuestionTimer(); summarize(); }")
            try:
                pg.wait_for_function("()=>!!document.querySelector('.vroom-waitcard.is-all-in')", timeout=20000)
                allin = True
            except Exception:
                allin = False
            pg.wait_for_timeout(300)
            card = pg.evaluate("""(before)=>{ const w=document.querySelector('.vroom-waitcard');
              return { inXp: !!(w && w.closest('.rs-xp')), matches: (store.vrMatches || 0) - before,
                       count: (document.querySelector('.vroom-wait-count')||{}).textContent }; }""", before)
            check("%d people: everyone in is seen" % n, allin and card["count"] == "%d/%d" % (n, n), card)
            check("%d people: the waiting card is its own card, not inside the XP card" % n, not card["inXp"], card)
            check("%d people: the match counts towards Matches played, once" % n, card["matches"] == 1, card)
            pg.evaluate("()=>startVroomRaceCutscene()")
            pg.wait_for_function("()=>document.querySelector('#vroom-race-cut.is-done')", timeout=20000)
            pg.wait_for_timeout(1200)
            b = pg.evaluate("""()=>{ const c=document.getElementById('vroom-race-cut');
              const rows=[...c.querySelectorAll('.vrc-row')];
              const btns=[...c.querySelectorAll('.vrc-exits button')].map(x=>{ const r=x.getBoundingClientRect();
                const t=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
                return { ok: r.bottom <= innerHeight && r.right <= innerWidth && r.left >= 0 && (t===x || x.contains(t)) }; });
              return { rows: rows.length, places: rows.map(r=>r.querySelector('.vrc-place').textContent).filter(Boolean),
                       exits: btns, hs: document.documentElement.scrollWidth - innerWidth }; }""")
            want = ["Winner"] if n < 4 else ["1st", "2nd", "3rd"]
            check("%d people: everybody is on the leaderboard" % n, b["rows"] == n, b)
            check("%d people: %s" % (n, "one winner, nobody else placed" if n < 4 else "a podium of three"),
                  sorted(b["places"]) == sorted(want), b["places"])
            check("%d people: both ways out are on screen and tappable" % n,
                  len(b["exits"]) == 2 and all(e["ok"] for e in b["exits"]) and b["hs"] <= 0, b)
            home(pg)
        # The same room, played again from its lobby: a second match.
        before = pg.evaluate("()=>store.vrMatches || 0")
        pg.evaluate("""()=>{ const parts = __vrBots.room('R313N4', 4, i => __vrBots.finished(i, 90 + i * 7));
          return fbDb.collection('vrooms').doc('R313N4').set({ status:'starting', game:'race', units:['Identity Crimes'],
            startAt: Date.now() - 1000, chatMessages: [], participants: parts, racers: Object.keys(parts) }); }""")
        pg.wait_for_timeout(250)
        pg.evaluate("()=>{ vroomCode='R313N4'; vroomMyKey='me'; vroomIsHost=true; beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }")
        pg.wait_for_selector(".qpanel .choice", timeout=25000)
        pg.evaluate("()=>{ order.forEach(qi=>{ picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); stopQuestionTimer(); summarize(); }")
        pg.wait_for_function("()=>!!document.querySelector('.vroom-waitcard.is-all-in')", timeout=20000)
        pg.wait_for_timeout(300)
        check("a second match in the same room counts too", pg.evaluate("(b)=>(store.vrMatches||0) - b", before) == 1)
        home(pg)

        # A racer whose phone died mid-race must not hold the leaderboard.
        pg.evaluate("""()=>{ const parts = __vrBots.room('R313DEAD', 5, i => i === 1
              ? { seen: Date.now() - 10 * 60 * 1000, progress: 40 } : __vrBots.finished(i, 90 + i * 7));
          return fbDb.collection('vrooms').doc('R313DEAD').set({ status:'starting', game:'race', units:['Identity Crimes'],
            startAt: Date.now() - 2000, chatMessages: [], participants: parts, racers: Object.keys(parts) }); }""")
        pg.wait_for_timeout(250)
        pg.evaluate("()=>{ vroomCode='R313DEAD'; vroomMyKey='me'; vroomIsHost=true; beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }")
        pg.wait_for_selector(".qpanel .choice", timeout=25000)
        pg.evaluate("()=>{ order.forEach(qi=>{ picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); stopQuestionTimer(); summarize(); }")
        pg.wait_for_function("()=>!!document.querySelector('.vroom-waitcard.is-all-in')", timeout=20000)
        t0 = time.time()
        try:
            pg.wait_for_function("()=>!!document.getElementById('vroom-race-cut')", timeout=30000)
            took = round(time.time() - t0, 1)
        except Exception:
            took = None
        check("a racer whose phone died does not hold the leaderboard back (rolls within 30s of everyone in)",
              took is not None, took)
        if took is not None:
            last = pg.evaluate("()=>[...document.querySelectorAll('#vroom-race-cut .vrc-row')].length")
            check("and is still on it, last", last == 5, last)
        home(pg)
        pg.close()
    except Exception as e:
        check("the 313 race section ran at all", False, repr(e)[:300])

    # ---- 21. Tug of War and Battle, at every size ---------------------------
    print("\n21. (313) Tug of War and Battle of 2, 4 and 20: they end, they count, the result fits")
    try:
        pg = open_tab("Tam", "ninja", 3000, "T313-0001", badges=1)
        active(pg)
        pg.evaluate(BOTS_313)
        pg.evaluate("()=>{ theme.muteBanners = true; theme.reduceMotion = true; }")
        for game in ("tug", "battle"):
            for n in (2, 4, 20):
                code = ("TUG" if game == "tug" else "BAT") + "313N%d" % n
                before = pg.evaluate("()=>store.vrMatches || 0")
                pg.evaluate("""([code, n, game])=>{ const parts = __vrBots.room(code, n); const teams = tugTeamsFor(parts);
                  const d = { status:'starting', game, units:['Identity Crimes'], count: 10, startAt: Date.now() + 1200,
                              chatMessages: [], participants: parts, racers: Object.keys(parts) };
                  if(game === 'tug') d.tug = { progress:{}, over:false, winner:null, finalPos:0, count:10, teams };
                  else d.battle = { log:[], progress:{}, over:false, winner:null, count:0, teams };
                  return fbDb.collection('vrooms').doc(code).set(d).then(()=>{ vroomCode=code; vroomMyKey='me';
                    game === 'tug' ? beginTugMatch(d) : beginBattleMatch(d); __vrBots.beat(); }); }""", [code, n, game])
                pg.wait_for_selector(".screen-%s .choice" % game, timeout=25000)
                pg.wait_for_timeout(400)
                if game == "battle":
                    hdr = pg.evaluate("""()=>{ const sides=[...document.querySelectorAll('.screen-battle .battle-side')];
                      return { faces: sides.map(s=>s.querySelectorAll('.battle-faces > *').length),
                               out: sides.some(s=>{ const r=s.getBoundingClientRect(); return r.left < -1 || r.right > innerWidth + 1; }),
                               hs: document.documentElement.scrollWidth - innerWidth }; }""")
                    check("battle, %d people: each side's header fits on screen" % n,
                          max(hdr["faces"]) <= 4 and not hdr["out"] and hdr["hs"] <= 0, hdr)
                pg.evaluate("""([game, n])=>{ const d = game === 'tug' ? tugLastData : battleLastData; const teams = d[game].teams; const mine = teams.me;
                  const cnt = game === 'tug' ? tugCount : battleCount;
                  Object.keys(teams).filter(k => k !== 'me').forEach(k => { const ours = teams[k] === mine;
                    const fast = n === 2 || ours;
                    if(game === 'tug') __vrBots.tug(k, fast ? 300 : 900, fast ? 1 : .3, cnt);
                    else __vrBots.battle(k, fast ? 250 : 900, fast ? 1 : .3, cnt); }); }""", [game, n])
                try:
                    pg.wait_for_selector(".screen-%s-result" % game, timeout=40000)
                    ended = True
                except Exception:
                    ended = False
                check("%s, %d people: the match ends on the result screen" % (game, n), ended)
                if ended:
                    pg.wait_for_timeout(600)
                    r = pg.evaluate("""(before)=>{ const sub=document.querySelector('#stage .cal-sub');
                      const bar=document.querySelector('.bottomtabs');
                      const ex=[...document.querySelectorAll('#stage .vroom-exit-row button')].map(b=>b.getBoundingClientRect()).map(q=>q.right<=innerWidth+1&&q.left>=-1);
                      return { sub: sub ? sub.textContent : '', hs: document.documentElement.scrollWidth - innerWidth,
                               tabbar: !bar || bar.hidden || getComputedStyle(bar).display === 'none',
                               exits: ex, rows: document.querySelectorAll('#stage .tug-board-row').length,
                               matches: (store.vrMatches || 0) - before }; }""", before)
                    check("%s, %d people: no sideways scroll and a one-line summary" % (game, n),
                          r["hs"] <= 0 and len(r["sub"]) <= 70 and r["sub"].count("&") <= 1, r)
                    check("%s, %d people: everybody is on the board" % (game, n), r["rows"] == n, r)
                    check("%s, %d people: no tab bar, two ways out on screen" % (game, n),
                          r["tabbar"] and len(r["exits"]) == 2 and all(r["exits"]), r)
                    check("%s, %d people: the match counts towards Matches played" % (game, n), r["matches"] == 1, r)
                home(pg)
        # The same room twice: two matches.
        before = pg.evaluate("()=>store.vrMatches || 0")
        for _ in range(2):
            pg.evaluate("""()=>{ const parts = __vrBots.room('BAT313TWICE', 2); const teams = tugTeamsFor(parts);
              const d = { status:'starting', game:'battle', units:['Identity Crimes'], startAt: Date.now() + 800, chatMessages: [],
                participants: parts, racers: Object.keys(parts), battle: { log:[], progress:{}, over:false, winner:null, count:0, teams } };
              return fbDb.collection('vrooms').doc('BAT313TWICE').set(d).then(()=>{ vroomCode='BAT313TWICE'; vroomMyKey='me'; beginBattleMatch(d);
                __vrBots.battle('b1', 200, 1, battleCount); }); }""")
            pg.wait_for_selector(".screen-battle-result", timeout=40000)
            pg.wait_for_timeout(400)
            home(pg)
        check("two matches in the same room are two matches", pg.evaluate("(b)=>(store.vrMatches||0) - b", before) == 2)
        pg.close()
    except Exception as e:
        check("the 313 team-match section ran at all", False, repr(e)[:300])

    # ---- 22. nobody can strand a team match ---------------------------------
    print("\n22. (313) a team match cannot be held up by a phone that died")
    try:
        pg = open_tab("Gil", "ninja", 3000, "G313-0001", badges=1)
        active(pg)
        pg.evaluate(BOTS_313)
        pg.evaluate("()=>{ theme.muteBanners = true; theme.reduceMotion = true; }")
        # The HOST's phone dies: the one device that calls the match over.
        pg.evaluate("""()=>{ const parts = __vrBots.room('TUG313HOST', 4, i => i === 1 ? { joinedAt: Date.now() - 999999 } : {});
          const teams = tugTeamsFor(parts);
          const d = { status:'starting', game:'tug', units:['Identity Crimes'], count: 3, startAt: Date.now() + 800, chatMessages: [],
                      participants: parts, racers: Object.keys(parts), tug: { progress:{}, over:false, winner:null, finalPos:0, count:3, teams } };
          return fbDb.collection('vrooms').doc('TUG313HOST').set(d).then(()=>{ vroomCode='TUG313HOST'; vroomMyKey='me'; beginTugMatch(d); __vrBots.beat(); }); }""")
        pg.wait_for_selector(".screen-tug .choice", timeout=25000)
        pg.evaluate("""()=>{ __vrBots.die('b1');
          ['b2','b3'].forEach(k => __vrBots.upd({ ['tug.progress.' + k]: { pos: 3, correct: 0, pull: -.75, done: true, at: Date.now() } }));
          tugMyPos = tugCount; tugMyDone = true; tugMyPull = -.75; tugPublishProgress(); }""")
        try:
            pg.wait_for_selector(".screen-tug-result", timeout=20000)
            ok = True
        except Exception:
            ok = False
        check("the host's phone dies: the next player calls the match, and it ends", ok,
              pg.evaluate("()=>({host: vroomIsHost, over: tugLastData && tugLastData.tug && tugLastData.tug.over})"))
        home(pg)
        # A whole side goes quiet: the other side has won.
        pg.evaluate("""()=>{ const parts = __vrBots.room('BAT313GONE', 2); const teams = tugTeamsFor(parts);
          const d = { status:'starting', game:'battle', units:['Identity Crimes'], startAt: Date.now() + 800, chatMessages: [],
            participants: parts, racers: Object.keys(parts), battle: { log:[], progress:{}, over:false, winner:null, count:0, teams } };
          return fbDb.collection('vrooms').doc('BAT313GONE').set(d).then(()=>{ vroomCode='BAT313GONE'; vroomMyKey='me'; beginBattleMatch(d); }); }""")
        pg.wait_for_selector(".screen-battle .choice", timeout=25000)
        pg.evaluate("()=>__vrBots.die('b1')")
        try:
            pg.wait_for_selector(".screen-battle-result", timeout=20000)
            won = pg.evaluate("()=>(document.querySelector('#stage h1')||{}).textContent")
        except Exception:
            won = None
        check("the only player on the other side goes quiet: the match ends, and you have won",
              won is not None and "won" in won.lower(), won)
        home(pg)
        # A side of ten, on the winner scene: three figures and a count, on the phone.
        pg.evaluate("()=>{ theme.muteBanners = false; theme.reduceMotion = false; }")
        fit = pg.evaluate("""()=>new Promise(res=>{ const es=[...Array(10)].map((_, i)=>({ name: 'P' + i, avatar: 'ninja' }));
          playVroomWinnerCutscene({ kind:'team', entries: es }, ()=>{});
          setTimeout(()=>{ const t=document.querySelector('#vroom-cutscene .vroom-cut-team'); const r=t.getBoundingClientRect();
            const out={ figs: t.querySelectorAll('.vroom-cut-figure').length, more: (t.querySelector('.vroom-cut-morenum')||{}).textContent || '',
                        left: Math.round(r.left), right: Math.round(r.right), vw: innerWidth };
            document.getElementById('vroom-cutscene')?.remove(); res(out); }, 4200); })""")
        check("a winning side of ten fits the phone: three figures and '+7'",
              fit["figs"] == 3 and fit["more"] == "+7" and fit["left"] >= 0 and fit["right"] <= fit["vw"], fit)
        pg.close()
    except Exception as e:
        check("the 313 stranding section ran at all", False, repr(e)[:300])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--against", help="run against a different index.html")
    ap.add_argument("--latency", type=int, default=60,
                    help="simulated one-way write latency, ms")
    ap.add_argument("--only-246", action="store_true",
                    help="run only the build-246 sections (13-19)")
    ap.add_argument("--only-313", action="store_true",
                    help="run only the build-313 sections (20-22)")
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

        ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
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

        if args.only_313:
            sections_313(ctx, open_tab, args)
            ctx.close(); br.close(); srv.shutdown()
            print("\n%s  (%d failure(s))"
                  % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
            return 1 if FAILURES else 0
        if args.only_246:
            sections_246(ctx, open_tab, args)
            ctx.close(); br.close(); srv.shutdown()
            print("\n%s  (%d failure(s))"
                  % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
            return 1 if FAILURES else 0

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
          /* build 266: a room has no game until the host picks one, so
             the harness picks the race it has always tested */
          createVirtualRoomLobby(units, null, "race");
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
            .map(r=>{const m=r.querySelector('.vroom-row-rank'); return m ? m.textContent : null;}),
          coins: document.querySelectorAll('.vroom-row .lb-rankmark').length,
          want: [RANK_DISPLAY_NAME.rookie, RANK_DISPLAY_NAME.veteran] })""")
        # In words under the name, never as a coin on the character
        # (build 241: "the ranking with the words is enough").
        check("every row carries its person's rank",
              sorted(r for r in ranks["seen"] if r) == sorted(ranks["want"]), ranks)
        check("and no rank coin on anyone's character", ranks.get("coins") == 0, ranks)
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

        # ---- 5b. a reaction at the moment somebody sends -------------
        # A send is an atomic append; a reaction rewrites the whole list.
        # Built from this tab's last snapshot, that rewrite erased any
        # message sent in between (build 237). Made deterministic in one
        # tab: another person's message goes into the room in the same
        # tick as the tap, so this tab's copy cannot have seen it yet.
        print("\n5b. a reaction while somebody sends")
        host.evaluate("""()=>{
          const wrap=[...document.querySelectorAll('#chatprobe .vroom-chat-msgwrap')]
            .find(w=>w.textContent.indexOf('from the host')>=0);
          wrap.click();
          const pick=document.querySelector('#chatprobe .vroom-chat-pick');
          fbDb.collection('vrooms').doc(vroomCode).update({ chatMessages:
            firebase.firestore.FieldValue.arrayUnion({ id:'race-1', key:'KKKK-4444',
              name:'Kim', text:'sent during a reaction', ts:Date.now() }) });
          pick.click(); }""")
        host.wait_for_timeout(1200 + args.latency * 4)
        raced = host.evaluate("""()=>({
          texts: [...document.querySelectorAll('#chatprobe .vroom-chat-msg')].map(e=>e.textContent).join(' | '),
          reacts: document.querySelectorAll('#chatprobe .vroom-chat-react').length })""")
        check("a message sent during a reaction survives it",
              "sent during a reaction" in raced["texts"], raced["texts"])
        check("and the reaction lands too", raced["reacts"] >= 1, raced)

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
        # The guest will hold back its "my results have finished landing"
        # report until told to, so the host's wait on the LAST reveal can
        # be seen (build 214).
        guest.evaluate("""()=>{ window.__holdReveal = true;
          const oc = fbDb.collection.bind(fbDb);
          fbDb.collection = name => { const c = oc(name); const od = c.doc.bind(c);
            c.doc = id => { const d = od(id); const ou = d.update.bind(d);
              d.update = f => (window.__holdReveal && f && Object.keys(f).some(k => /\\.revealDone$/.test(k) && f[k] === true))
                ? Promise.resolve() : ou(f);
              return d; };
            return c; }; }""")
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
            # ONE AFTER THE OTHER, and waited on. The fake room lives in
            # localStorage shared by both tabs, and Chromium syncs that
            # between renderers asynchronously - so two finishes in the
            # same instant can each read the room, and the later write
            # puts back a copy without the earlier one's finish in it.
            # Measured: the host's record reverted to its join-time
            # values (finished:false, xp = lifetime points) and every
            # "is the room all in" check after it went red. Real
            # Firestore applies field-path updates on the server and has
            # no such race, so this is the harness, not the app; waiting
            # for each finish to land is what a real room gets for free.
            pg.wait_for_function("""()=>fbDb.collection('vrooms').doc(vroomCode).get()
              .then(d => !!(((d.data() || {}).participants || {})[vroomMyKey] || {}).finished)""",
              timeout=8000)
        host.wait_for_timeout(600)
        # THE NORMAL RESULTS SCREEN STAYS (build 207). Finishing used to
        # show it and then replace it outright with the finale's own
        # screen - "the result screen comes up and then disappears right
        # after". What must hold now is that the screen summarize() built
        # is still the one up, carrying the Virtual Room part on it.
        stays = host.evaluate("""()=>{
          const top = document.getElementById('stage').firstElementChild;
          return { screen: top && top.dataset ? top.dataset.screen : null,
                   /* Build 213: the room's part is the live "waiting on other
                      players" card at the TOP of the results, not a section
                      in the middle of them. */
                   inline: !!(top && top.querySelector('.vroom-waitcard')),
                   level: !!(top && top.querySelector('.results-level, .xp-block, .level-block, [class*=level]')),
                   /* Build 213: the race line is down on the results
                      screen too - the waiting card replaced it, and left
                      up it sat under the chat button. */
                   race: (() => { const r = document.getElementById('vroomracebar');
                                  return !r || r.hidden; })() };}""")
        check("finishing keeps the normal results screen up", stays.get("screen") == "results", stays)
        check("with the Virtual Room part on it, not instead of it", stays.get("inline") is True, stays)
        check("and the race line is down on it", stays.get("race") is True, stays)

        # ---- BUILD 214: the wait, and what fills it ----
        # "the virtual room doesn't need the review button, the missed
        # questions need to be displayed beneath there ... that review
        # section at the bottom needs to be a tab". Then "preparing
        # leaderboard" about five seconds after everyone is in, and the
        # cutscene held until the LAST player's results have finished
        # landing.
        rv = host.evaluate("""()=>{ const top = document.getElementById('stage').firstElementChild;
          return { tabs: [...top.querySelectorAll('.rs-roomreview .rs-tab')].map(b=>b.dataset.tab),
                   on: (top.querySelector('.rs-roomreview .rs-tab.is-on')||{dataset:{}}).dataset.tab,
                   reviewBtn: [...top.querySelectorAll('button')].some(b=>/Review your answers/.test(b.textContent)) }; }""")
        check("the review is on the screen in two tabs, missed first",
              rv["tabs"] == ["missed", "all"] and rv["on"] == "missed", rv)
        check("with no Review button to open it", not rv["reviewBtn"], rv)
        # ---- BUILD 240: the room's chat on the screen a real race ends on ----
        # The Room chat button was only ever mounted by
        # showVirtualRoomResults(), which a real race no longer reaches, so
        # it never appeared outside a harness that mounted that screen by
        # hand. This is the real finish. Written against build 240's first
        # draft, where every one of these was false.
        # Read what is there first - earlier messages this harness never
        # scrolled to are honestly unread - so the count below is the one
        # message that arrives while the sheet is closed.
        host.evaluate("""()=>{ document.getElementById('roomchat-fab')?.click(); closeRoomChatSheet(); }""")
        host.wait_for_timeout(300)
        guest.evaluate("""()=>fbDb.collection('vrooms').doc(vroomCode).update({ chatMessages:
          firebase.firestore.FieldValue.arrayUnion({ id: 'g-' + Date.now(), key: vroomMyKey, name: 'Guest',
                                                     text: 'gg everyone', ts: Date.now() }) })""")
        host.wait_for_timeout(1200 + args.latency * 2)
        rc = host.evaluate("""()=>{ const fab = document.getElementById('roomchat-fab');
          const c = fab && fab.querySelector('.roomchat-fab-count');
          const out = { fab: !!fab, count: c && !c.hidden ? c.textContent : '' };
          if(fab){ fab.click(); }
          const sheet = document.getElementById('roomchat-sheet');
          out.lifted = !!(sheet && sheet.querySelector('.vroom-chat'));
          out.text = sheet ? (sheet.querySelector('.vroom-chat-list') || {}).textContent || '' : '';
          closeRoomChatSheet();
          return out; }""")
        check("the Room chat button is up on the results a real race ends on", rc.get("fab") is True, rc)
        check("and counts a message that arrived while it was closed", rc.get("count") == "1", rc)
        check("and opens the room's chat with that message in it",
              rc.get("lifted") is True and "gg everyone" in rc.get("text", ""), rc)
        t_in = None
        for _ in range(100):
            if host.evaluate("()=>!!document.querySelector('.vroom-waitcard.is-all-in')"):
                t_in = time.time(); break
            host.wait_for_timeout(200)
        check("everyone in is seen", t_in is not None)
        if t_in:
            host.wait_for_timeout(max(0, int((t_in + 6.5 - time.time()) * 1000)))
            check("'Preparing leaderboard' is up five seconds after",
                  host.evaluate("()=>!!document.getElementById('vroom-prep')"))
            host.wait_for_timeout(max(0, int((t_in + 14.5 - time.time()) * 1000)))
            held = host.evaluate("()=>!document.getElementById('vroom-race-cut') && !!document.getElementById('vroom-prep')")
            check("the cutscene waits while a player's results are still landing", held, held)
            # BUILD 279: "the leaderboard just wouldn't load till that
            # person's stuff is done there". A rank-up still playing on THIS
            # screen holds the roll however ready the room is; written
            # against 278, where the board cut in over it.
            host.evaluate("()=>{ const d = document.createElement('div'); d.id = 'supernova-cutscene'; document.body.appendChild(d); }")
            guest.evaluate("""()=>{ window.__holdReveal = false;
              fbDb.collection('vrooms').doc(vroomCode).update({ ['participants.' + vroomMyKey + '.revealDone']: true }); }""")
            host.wait_for_timeout(10500)
            check("and never rolls over a cutscene still playing on this screen",
                  host.evaluate("()=>!document.getElementById('vroom-race-cut')"))
            host.evaluate("()=>document.getElementById('supernova-cutscene')?.remove()")
            rolled = False
            for _ in range(80):
                if host.evaluate("()=>!!document.getElementById('vroom-race-cut')"):
                    rolled = True; break
                host.wait_for_timeout(250)
            check("and rolls once they are done", rolled)
            check("taking the banner down with it", not host.evaluate("()=>!!document.getElementById('vroom-prep')"))
        for pg in (host, guest):
            pg.evaluate("()=>{ document.getElementById('vroom-race-cut')?.remove(); document.getElementById('vroom-prep')?.remove(); }")
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
            /* ---- ONE CHAT BUTTON IN THE APP ----
               This asserted that the Virtual Room's own chat TOGGLE sat
               in the top-right corner. That toggle is gone: the room's
               chat is a named section at the foot of the lobby and the
               round dock button means DMs, asked for directly - "I don't
               want there to be two chat buttons ... the button is still
               just strictly DMs."
               So the check is the decision one level up, which is the
               one that cannot go stale: exactly one chat BUTTON on the
               screen, and it is the dock's. */
            /* COUNTED BY WHAT IS ON SCREEN, not by what is in the DOM.
               `:not([hidden])` counted three: a display:none toggle is
               still un-hidden as far as the attribute goes, and a panel
               is mounted per screen. A button nobody can see is not a
               second chat button. */
            chatButtons: [...document.querySelectorAll(
              '.vroom-chat-toggle, .chatdock-btn')]
              .filter(b => b.getBoundingClientRect().width > 0
                        && getComputedStyle(b).display !== 'none'
                        && getComputedStyle(b).visibility !== 'hidden').length,
            roomChatNamed: (() => {
              const t = document.querySelector('.vroom-chat-title');
              return t ? (t.textContent || '').trim() : null;
            })(),
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
        check("there is exactly one chat button on the screen",
              got["chatButtons"] == 1, got["chatButtons"])
        check("and the room's own chat says which chat it is",
              (got["roomChatNamed"] or "").lower().startswith("virtual room"),
              got["roomChatNamed"])

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
        # Section 7's results screen rolls its leaderboard on its own
        # clock; on a loaded machine it can still be up here. It belongs
        # to section 7 and is not what this section mounts.
        pg.evaluate("()=>{ document.getElementById('vroom-race-cut')?.remove(); document.getElementById('vroom-prep')?.remove(); }")
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

        # The options sheet: the questions slider and NO time limit
        # (build 246 - "for the race lets not add time options"; every
        # question has its own 45 seconds), and Save rather than Create
        # lobby. This asserted both sliders until the decision changed.
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
        check("the questions slider is there, and no time limit",
              sheet["sliders"] == 1 and not any("time" in l for l in sheet["labs"]),
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
            pulled_d = tugB.evaluate("""()=>{
              const k = document.querySelector('.tug-knot');
              return { left: k ? parseFloat(k.style.left) : null,
                       progress: tugLastData && tugLastData.tug && tugLastData.tug.progress,
                       screen: !!document.querySelector('.screen-tug') };}""")
            pulled = pulled_d["left"]
            check("the rope has moved on the device that answered nothing",
                  pulled is not None and abs(pulled - 50) > 1, pulled_d)
            mine_side = tugB.evaluate("()=>!!document.querySelector('.tug-knot.is-theirs')")
            check("and it has moved the wrong way for them", mine_side is True)
            # AND TOWARDS THE SIDE THAT IS PULLING. Alex's side got three
            # right, so the knot belongs on Alex's end. Since build 241
            # every device draws ITS OWN side on the left ("you should be
            # able to just look only at the rope to see how well your
            # side is doing"), so on Bo's phone Alex's end is the right.
            # For a while every lead was drawn backwards and the check
            # above could not tell, because it only asked for a colour.
            toward = tugB.evaluate("""()=>{
              const side = tugTeamOf(tugLastData, (Object.keys(tugLastData.participants||{})
                .find(k => (tugLastData.participants[k]||{}).name === 'Alex')));
              const k = document.querySelector('.tug-knot');
              return { side: side, mine: tugTeamOf(tugLastData, vroomMyKey),
                       left: k ? parseFloat(k.style.left) : null };}""")
            check("and it has moved towards the side that is pulling, drawn from this device's end",
                  toward["left"] is not None and
                  ((toward["side"] == toward["mine"] and toward["left"] < 50) or
                   (toward["side"] != toward["mine"] and toward["left"] > 50)), toward)

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
            # ---- THESE THREE ENCODED A PACING DECISION, AND IT CHANGED ----
            # They asserted a 7-second floor, a 5-10 minute window and a
            # ten-minute cap, which is what was asked for when tug of war
            # was built. Asked for again since: "increase the amount of
            # time - the amount of time for tug of war should change
            # depending on how many questions." The old numbers did the
            # opposite at the top end: every match flattened out at the
            # ten-minute cap, so picking 40 questions or 200 made no
            # difference to how long it ran.
            # Re-read rather than deleted, because the SHAPE is still what
            # matters and is still checkable: a floor that nothing goes
            # under, a length that rises with the bank, and a ceiling.
            check("the floor is nine seconds and nothing goes under it",
                  pace["floorSmall"] == 9000 and pace["floorBig"] >= 9000,
                  {"29q at the end": pace["floorSmall"], "a huge bank": pace["floorBig"]})
            # A SHORT MATCH IS STILL SHORT. Ten questions must not become a
            # twenty-minute sitting because the target went up.
            check("ten questions is still a short match",
                  3 <= pace["m10"] <= 12, pace["m10"])
            # AND LONGER MEANS LONGER, which is the whole of the request.
            check("more questions means a longer match, not a faster one",
                  pace["m29"] >= pace["m10"] and pace["m80"] >= pace["m29"]
                  and pace["m80"] > pace["m10"],
                  {k: pace[k] for k in ("m10", "m29", "m80")})
            # The bank is not capped - "All units" is several hundred
            # questions - so past a point the rope settles it rather than
            # the questions running out. The ceiling moved with the target.
            check("and a whole-bank match is still capped, at twenty minutes",
                  pace["mAll"] <= 20, pace["mAll"])

            # ---- THE END OF A MATCH. Nothing here looked past the rope
            # moving, and the two screens after it had both been deleted
            # by accident in build 170 - finishing your questions and the
            # end of every match threw a ReferenceError and left the
            # screen where it was. Played to the end, on both devices.
            tug_errs = []
            for tag, pg in (("A", tugA), ("B", tugB)):
                pg.on("pageerror", lambda e, t=tag: tug_errs.append(t + ": " + str(e)))
            for _ in range(80):
                if tugA.evaluate("()=>tugMyDone || !document.querySelector('.screen-tug .choices .choice:not([disabled])')"):
                    if tugA.evaluate("()=>tugMyDone"):
                        break
                    tugA.wait_for_timeout(300)
                    continue
                tug_answer(tugA, True)
            tugA.wait_for_timeout(600)
            wait = tugA.evaluate("""()=>({ done: tugMyDone,
              wait: !!document.querySelector('.screen-tug-wait'),
              rope: !!document.querySelector('.screen-tug-wait .tug-rope'),
              over: !!(tugLastData && tugLastData.tug && tugLastData.tug.over) })""")
            check("finishing your questions shows the rope, not a frozen question",
                  wait["wait"] or wait["over"], wait)
            for _ in range(80):
                if tugB.evaluate("()=>tugMyDone || !document.querySelector('.screen-tug')"):
                    break
                if tugB.evaluate("()=>!!document.querySelector('.screen-tug .choices .choice:not([disabled])')"):
                    tug_answer(tugB, False)
                else:
                    tugB.wait_for_timeout(300)
            for pg in (tugA, tugB):
                try:
                    pg.wait_for_selector(".screen-tug-result", timeout=20000)
                except Exception:
                    pass
            ends = [pg.evaluate("""()=>({ result: !!document.querySelector('.screen-tug-result'),
              title: (document.querySelector('.screen-tug-result h1')||{}).textContent || null,
              exits: [...document.querySelectorAll('.screen-tug-result .vroom-exit-btn')].map(b=>b.textContent) })""")
                    for pg in (tugA, tugB)]
            check("the match ends on a result screen on both devices",
                  all(e["result"] for e in ends), ends)
            check("the side that answered everything right won it",
                  ends[0]["title"] == "Your side won" and ends[1]["title"] == "Your side lost",
                  [e["title"] for e in ends])
            check("with a way back to the lobby and a way home",
                  all(len(e["exits"]) == 2 for e in ends), [e["exits"] for e in ends])
            check("and nothing threw on the way there", not tug_errs, tug_errs[:3])

            # NO GAME HAS A TIME LIMIT CONTROL NOW. It went from tug first
            # ("when I hit tug of war, the timer option shouldn't be there")
            # and from the race in build 246 ("for the race lets not add
            # time options, just make it where each question has a 45
            # second timer"). This asserted race 2 / tug 1 until then - a
            # gate that encodes a decision is re-read when the decision
            # changes. Still a SHAPE (how many sliders), never a label.
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
            check("no game offers a time limit: race and tug both have just the questions slider",
                  race_n == 1 and tug_n == 1, {"race": race_n, "tug": tug_n})
            check("and switching back to race does not bring one back", back_n == 1, back_n)

            # The game cards read as a choice: all the same size, all
            # with a surface of their own. The unselected one was reported
            # as looking like it was not there.
            cards = tugA.evaluate("""()=>[...document.querySelectorAll('.vroom-host-mode')].map(b=>{
              const r=b.getBoundingClientRect(), cs=getComputedStyle(b);
              return { w:Math.round(r.width), h:Math.round(r.height),
                       on:b.classList.contains('on'),
                       bg:cs.backgroundColor, art:!!b.querySelector('.vroom-host-mode-art') };})""")
            check("every game card is the same size and has art",
                  len(cards) >= 2 and len({c["w"] for c in cards}) == 1
                  and len({c["h"] for c in cards}) == 1 and all(c["art"] for c in cards),
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
                  { name: "Cy", avatar: "ninja", sub: "88%" },
                  /* Four people: a podium needs a room of four since
                     build 236 (VROOM_PODIUM_MIN). */
                  { name: "Dee", avatar: "alien", sub: "80%" }] },
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
            # Under four people there is no podium - "if the lobby is less
            # than 4 people ... just who finished first" (build 236).
            small = cut.evaluate("""()=>{
              playVroomWinnerCutscene({ kind: "podium", entries: [
                  { name: "Rosa", avatar: "queen", sub: "96%" },
                  { name: "Ben", avatar: "ghost", sub: "92%" },
                  { name: "Cy", avatar: "ninja", sub: "88%" }] }, () => {});
              const el = document.getElementById("vroom-cutscene");
              const r = [...el.querySelectorAll('.vroom-cut-plinth')].map(p => p.dataset.place);
              el.remove(); return r; }""")
            check("a room of three has a winner and no podium", small == ["1"], small)
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

        # ---- 12. everybody on the line, whatever they are wearing ----
        # Written against build 215, where it fails. The race line built
        # each marker with buildAvatarCharSVG(), which returns null for an
        # avatar id this build does not know - an older build's character,
        # a renamed one - and appendChild(null) threw inside the loop, so
        # everybody after that person was simply missing from the line.
        # Found recording a four-person room for Madison. And the "Everyone's
        # ready!" beat drew the lobby's tab bar over itself.
        print("\n12. the race line draws everyone, and the ready beat is clean")
        try:
            rl = open_tab("Rae", "ninja", 3000, "RACE-0001", badges=1)
            ctx.new_cdp_session(rl).send("Page.setWebLifecycleState", {"state": "active"})
            rl.evaluate("""()=>{ const parts={
                me:{name:'Rae',avatarChar:'ninja',joinedAt:1,ready:true,finished:false,progress:0},
                a:{name:'A',avatarChar:'cadet-from-an-older-build',joinedAt:2,ready:true,finished:false,progress:30},
                b:{name:'B',avatarChar:'ghost',joinedAt:3,ready:true,finished:false,progress:50},
                c:{name:'C',avatarChar:'queen',joinedAt:4,ready:true,finished:false,progress:70} };
              return fbDb.collection('vrooms').doc('RACELINE').set({host:'me',status:'started',game:'race',
                units:['Identity Crimes'],startAt:Date.now()-2000,chatMessages:[],participants:parts}); }""")
            rl.wait_for_timeout(300)
            rl.evaluate("""()=>{ window.__errs=[]; window.addEventListener('error',e=>__errs.push(String(e.message)));
              vroomCode='RACELINE'; vroomMyKey='me'; vroomIsHost=true;
              beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }""")
            rl.wait_for_selector(".choice", timeout=25000)
            rl.wait_for_timeout(1500 + args.latency * 4)
            line = rl.evaluate("""()=>({markers: document.querySelectorAll('.vroom-race-marker').length,
                                       errs: window.__errs})""")
            check("all four people are on the race line, one of them in a character this build does not know",
                  line["markers"] == 4 and not line["errs"], line)
            rl.evaluate("()=>{ inVirtualRoom=false; testInProgress=false; stopVroomRaceListener(); showHome(); }")
            rl.wait_for_timeout(600)
            beat = rl.evaluate("""()=>{ const bar=document.querySelector('.bottomtabs');
              const before = !!bar && !bar.hidden;
              showVroomReadyFlourish(()=>{});
              return new Promise(r=>setTimeout(()=>r({before: before,
                during: !!bar && !bar.hidden && getComputedStyle(bar).display!=='none',
                overlay: !!document.getElementById('vroom-flourish-overlay')}), 400)); }""")
            check("the tab bar is not drawn over \"Everyone's ready!\"",
                  beat["before"] and beat["overlay"] and not beat["during"], beat)
        except Exception as e:
            check("the race-line section ran at all", False, repr(e)[:200])

        sections_246(ctx, open_tab, args)
        sections_313(ctx, open_tab, args)

        ctx.close()
        br.close()
    srv.shutdown()
    print("\n%s  (%d failure(s))"
          % ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES),
             len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
