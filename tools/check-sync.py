#!/usr/bin/env python3
"""Account integrity: the sync code, recovery, and who Find me blames.

The sweep asks "is anything broken on this device", check-positions asks
"did it land where I meant it to", check-fixes asks "is this fix in effect
here". None of them can see the one class of bug that costs somebody their
account rather than their layout: a sync code that goes missing, a
recovery that restores the progress and then leaves the Welcome screen up
to overwrite it, a rankings row nobody can ever delete. Every check here
is a measurement of behaviour, not a code read, and every one of them was
written against a build where it FAILED - run it with --against on that
build to see it fail, which is the only thing that makes a green run mean
anything.

  python3 tools/check-sync.py
  python3 tools/check-sync.py --against /path/to/old-index.html

Chromium has no Firestore here (the CDN is blocked in the sandbox), so
fbDb is stubbed - see HOOK. Exits non-zero on any failure.
"""
import functools, http.server, io, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")

SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv \
    else os.path.join(ROOT, "index.html")

# A Firestore stand-in. The real CDN is blocked in the sandbox, so fbDb is
# null and every cloud path is dead; these checks are about those paths, so
# the stub is the only way to exercise them at all. It records deletes,
# which is how "the old rankings row is retired" is measured.
HOOK = '''
  window.__deleted = [];
  window.__entries = [];
  window.__set = [];
  /* A DOCUMENT THE STUB CAN ACTUALLY RETURN. Without one, every get()
     is exists:false and no check can tell "the cloud has your account"
     from "the cloud has never heard of you" - which is the whole
     difference in the recovery paths below. Keyed by document id.
     __ready() drains the onFirebaseReady queue FROM INSIDE THE SCRIPT:
     fbDb is a top-level `let`, so it is not a window property and an
     assignment from a page.evaluate() silently creates a second,
     unrelated global while the app goes on seeing null. */
  window.__cloud = {};
  window.__ready = function(){ firebaseBecameReady(); };
  window.__fake = function(entries){
    window.__entries = entries || [];
    fbDb = { collection: function(name){ return { doc: function(id){ return {
      set: function(v){ window.__set.push(name + "/" + id); return Promise.resolve(); },
      get: function(){ const d = name === "progress" ? window.__cloud[id] : null;
        return Promise.resolve(d ? { exists: true, data: function(){ return d; } }
                                 : { exists: false }); },
      delete: function(){ window.__deleted.push(name + "/" + id); return Promise.resolve(); }
    }; } }; } };
    onSnapshotResilient = function(ref, onNext){
      setTimeout(function(){ onNext({ forEach: function(f){
        window.__entries.forEach(function(e){ f({ id: e.id, data: function(){ return e; } }); });
      } }); }, 20);
      return function(){};
    };
  };
'''

BODY = INSET_RE.sub(lambda m: "0px", io.open(SRC, encoding="utf-8").read()) \
    .replace("let fbDb = null;", "let fbDb = null;" + HOOK, 1)

STORE = ("{\"firstName\":\"Madison\",\"avatarChar\":\"ninja\",\"onboardingComplete\":true,"
         "\"leaderboardOptIn\":true,\"lastModified\":1700000000000,"
         "\"lifetime\":{\"points\":420,\"correct\":88,\"perfectTests\":2}}")

so = socket.socket(); so.bind(("127.0.0.1", 0)); PORT = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

fails = []
def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + detail) if detail else ""))
    if not ok: fails.append(name)

def page(ctx):
    pg = ctx.new_page()
    pg.route("**/index.html", lambda r: r.fulfill(
        status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    return pg

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)

    # ---- 1. onboarded, no sync code: boot issues one ----
    print("\n1. onboarded account whose sync code went missing")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    got = pg.evaluate("()=>({code:syncCode, ls:localStorage.getItem('class26e.synccode')})")
    check("a code is issued at boot", bool(got["code"]) and got["ls"] == got["code"], str(got))
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    pg.evaluate("()=>showRankings('week')"); pg.wait_for_timeout(400)
    pg.evaluate("()=>document.querySelector('.rank-me-btn').click()"); pg.wait_for_timeout(300)
    res = pg.evaluate("""()=>({me:!!document.querySelector('[data-me="1"]'),
        flash:!!document.querySelector('.rank-flash'),
        msg:(document.querySelector('.daily-alert')||{}).textContent||null})""")
    check("Find me finds your row", res["me"] and res["flash"], str(res))
    ctx.close()

    # ---- 2. sync deliberately off: no code, and the message says so ----
    print("\n2. sync turned off on purpose")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.syncoff','1');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    pg.evaluate("()=>showRankings('week')"); pg.wait_for_timeout(400)
    pg.evaluate("()=>document.querySelector('.rank-me-btn').click()"); pg.wait_for_timeout(300)
    res = pg.evaluate("""()=>({code:syncCode,
        msg:(document.querySelector('.daily-alert')||{}).textContent||''})""")
    check("no code is forced on a device that opted out", not res["code"], str(res["code"]))
    check("Find me blames sync, not the rankings setting",
          "isn’t syncing" in res["msg"], repr(res["msg"]))
    ctx.close()

    # ---- 3. hidden from the rankings: the other message ----
    print("\n3. hidden from the rankings")
    hidden = STORE.replace('"leaderboardOptIn":true', '"leaderboardOptIn":false')
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % hidden)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    pg.evaluate("()=>showRankings('week')"); pg.wait_for_timeout(400)
    pg.evaluate("()=>document.querySelector('.rank-me-btn').click()"); pg.wait_for_timeout(300)
    msg = pg.evaluate("()=>(document.querySelector('.daily-alert')||{}).textContent||''")
    check("Find me names the Settings toggle", "Show me in the rankings" in msg, repr(msg))
    ctx.close()

    # ---- 4. localStorage evicted: recovery must land on Home, with the code ----
    print("\n4. localStorage lost, IndexedDB mirror intact")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    pg = page(ctx)
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                       "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); saveStore();}")
    pg.wait_for_timeout(600)
    mirrored = pg.evaluate("()=>idbLoadCode? idbLoadCode() : null") \
        if pg.evaluate("()=>typeof idbLoadCode==='function'") else None
    check("the code is mirrored into IndexedDB", mirrored == "WXYZ-7777", repr(mirrored))
    pg.close()

    pg2 = page(ctx)   # same context: IndexedDB survives, localStorage does not
    pg2.add_init_script("try{localStorage.clear();localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');}catch(e){}")
    pg2.goto(URL); pg2.wait_for_timeout(3200)
    pg2.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg2.wait_for_timeout(900)
    res = pg2.evaluate("""()=>({screen:(document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen||null,
        name:store.firstName, points:(store.lifetime||{}).points,
        code:syncCode, ls:localStorage.getItem('class26e.synccode')})""")
    check("recovery lands on Home, not Welcome", res["screen"] == "home", str(res))
    check("recovery restores the progress", res["points"] == 420 and res["name"] == "Madison", str(res))
    check("recovery restores the sync code", res["code"] == "WXYZ-7777"
          and res["ls"] == "WXYZ-7777", str(res))
    ctx.close()

    # ---- 4b. the store key survived but the code did NOT ----
    # The one case the "an onboarded account always has a code" self-heal
    # actually fires on is a device that HAS an account and has lost the
    # key to it. Minting there is a second account: the old rankings row
    # is orphaned with nobody holding the id to retire it, and the
    # progress sitting right there goes up under an id nobody has seen.
    # Both records are in the same IndexedDB object store, but the store
    # is every answer this person has ever given and the code is nine
    # bytes, so a device under storage pressure can keep one and lose
    # the other. Fails on any build that mints without asking the mirror.
    print("\n4b. the progress key survived, the sync code did not")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    pg = page(ctx)
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                       "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); saveStore();}")
    pg.wait_for_timeout(600)
    pg.close()

    pg2 = page(ctx)   # same context: the mirror survives, the code key does not
    pg2.add_init_script("try{localStorage.clear();localStorage.setItem('class26e.freshstart','1');"
                        "localStorage.setItem('class26e.frame.ok','go-live-1');"
                        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)
    pg2.goto(URL); pg2.wait_for_timeout(3200)
    pg2.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg2.wait_for_timeout(900)
    res = pg2.evaluate("""()=>({code:syncCode, ls:localStorage.getItem('class26e.synccode'),
        onboarded:!!store.onboardingComplete})""")
    check("the mirrored code is adopted, not replaced", res["code"] == "WXYZ-7777", str(res))
    check("and it is written back to localStorage", res["ls"] == "WXYZ-7777", str(res))
    ctx.close()

    # ---- 4c. the mirror kept the code and lost the store ----
    # This is the shape that READS as being signed out: Welcome, no
    # progress, nothing said, while the whole account is in the cloud
    # and the key to it is in the mirror. Recovery used to bail the
    # moment the store record came back null and throw the code away
    # with it. The code is adopted only once a real document has come
    # back for it - setting it first is how an empty store gets pushed
    # up under a live account.
    print("\n4c. the mirror kept the code and lost the progress")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    pg = page(ctx)
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                       "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); saveStore();}")
    pg.wait_for_timeout(600)
    # lose the big record, keep the nine bytes
    pg.evaluate("""async ()=>{ const db = await idbOpen();
        await new Promise(r=>{ const tx = db.transaction('kv','readwrite');
          tx.objectStore('kv').delete('store'); tx.oncomplete = r; tx.onerror = r; }); }""")
    left = pg.evaluate("async ()=>({data: await idbLoad(), code: await idbLoadCode()})")
    check("the mirror is left holding only the code",
          left["data"] is None and left["code"] == "WXYZ-7777", str(left))
    pg.close()

    pg2 = page(ctx)
    pg2.add_init_script("try{localStorage.clear();localStorage.setItem('class26e.freshstart','1');"
                        "localStorage.setItem('class26e.frame.ok','go-live-1');}catch(e){}")
    pg2.goto(URL); pg2.wait_for_timeout(3200)
    pg2.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    # Firebase arrives now, with the account still in the cloud. The boot
    # code queued its work on onFirebaseReady, so draining it is what a
    # real launch does when the SDK finally lands.
    # THE DOCUMENT HAS TO POST-DATE FRESH_START_CUTOFF or pullFromCloud
    # reports it as not-found - which is correct behaviour and would make
    # this check measure the cutoff instead of the recovery. Read off the
    # app rather than written down here, so moving the cutoff cannot
    # quietly turn this check green for the wrong reason.
    pg2.evaluate("""()=>{ const d = %s; d.lastModified = (FRESH_START_CUTOFF || 0) + 86400000;
      window.__cloud['WXYZ-7777'] = d; __fake([]); __ready(); }""" % STORE)
    pg2.wait_for_timeout(1500)
    res = pg2.evaluate("""()=>({screen:(document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen||null,
        code:syncCode, name:store.firstName, points:(store.lifetime||{}).points,
        wrote:(window.__set||[]).join(',')})""")
    check("the code alone gets the account back", res["code"] == "WXYZ-7777", str(res))
    check("the progress comes down from the cloud",
          res["points"] == 420 and res["name"] == "Madison", str(res))
    check("and it lands on Home, not Welcome", res["screen"] == "home", str(res))
    ctx.close()

    # ---- 4d. Settings hands over a way back in ----
    # Removing the app destroys the whole storage jar, so neither
    # recovery above can help and what is left is the code, from memory.
    # recoveryUrlFor() was written for exactly that and was dead code -
    # defined, commented, never called - so there was no way to save
    # either one before the phone lost it. Tapped for real rather than
    # called: a button behind something unclickable measures as present
    # and does nothing.
    print("\n4d. Settings can hand over the code")
    ctx = br.new_context(viewport={"width": 440, "height": 956},
                         permissions=["clipboard-read", "clipboard-write"])
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(700)
    pg.evaluate("()=>document.querySelector('.sync-code-row').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(300)
    btns = pg.query_selector_all(".sync-save-row .cal-profile-btn")
    got = {}
    for b in btns:
        b.click(); pg.wait_for_timeout(350)
        got[b.text_content()] = pg.evaluate("()=>navigator.clipboard.readText()")
    check("Settings copies the code", got.get("Copy code") == "WXYZ-7777", str(got))
    # ONE BUTTON, NOT TWO. Copy sign-in link came off on an explicit
    # report - "I don't even know what that is and it will confuse
    # people" - and this check went red for asserting it, which is the
    # gate failing the app for being right. Asserted as SHAPE now: one
    # copy button in the sync section, whatever it ends up called.
    check("there is exactly one copy button, not a pair",
          len(btns) == 1, str([b.text_content() for b in btns]))
    filled = pg.evaluate(
        "()=>{const b=document.querySelector('.sync-save-row .cal-profile-btn');"
        " const r=document.querySelector('.sync-save-row');"
        " return b && r ? Math.round(r.getBoundingClientRect().width - b.getBoundingClientRect().width) : -1;}")
    check("and it fills the row", filled == 0, "%dpx short" % filled)
    # The recovery URL is still LOAD-BEARING even with no button on it:
    # the re-add notice hands off to Safari with it, and that is the one
    # route back for a device whose whole storage jar is about to go. So
    # it is checked where it actually lives now, not through a control
    # that no longer exists.
    back = pg.evaluate("""()=>{ const u = recoveryUrlFor(syncCode);
        const h = u.split('#')[1] || '';
        const v = (new URLSearchParams(h).get('k')||'').toUpperCase();
        return { url: u, read: SYNC_CODE_RE.test(v) ? v : null,
                 handoff: safariHandoffTarget() }; }""")
    check("the recovery link still round-trips", back.get("read") == "WXYZ-7777", str(back))
    check("and the Safari hand-off still carries the code",
          "k=WXYZ-7777" in (back.get("handoff") or ""), back.get("handoff"))
    ctx.close()

    # ---- 5. swapping codes retires the old rankings row ----
    print("\n5. abandoning a code takes its rankings row with it")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','AAAA-1111');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    # THE ROW IS KEYED BY THE PUBLIC ID NOW, so what has to be retired
    # is the old PUBLIC id's row, not the old sync code's - the sync
    # code is not a document id anywhere any more, and retiring by it
    # would delete nothing at all. This check named the sync code and
    # went red on the build that fixed the exposure: the same
    # stale-decision trap this repo has now watched take out five
    # separate gates. It asserts the RELATIONSHIP instead - whatever id
    # this device was publishing under before the swap is the one that
    # gets deleted.
    was = pg.evaluate("()=>(typeof publicIdOf==='function'?publicIdOf():null)")
    pg.evaluate("()=>{ __deleted.length = 0; setSyncCode('BBBB-2222'); }")
    pg.wait_for_timeout(200)
    dele = pg.evaluate("()=>__deleted.slice()")
    check("linking to another code retires the row it was publishing under",
          bool(was) and ("leaderboard/" + was) in dele, str(dele) + " was=" + str(was))
    check("and does not retire it by the sync code, which keys nothing",
          "leaderboard/AAAA-1111" not in dele, str(dele))
    check("linking does NOT delete the old progress doc",
          not any(d.startswith("progress/") for d in dele), str(dele))
    pg.evaluate("()=>{ __deleted.length = 0; retireLeaderboardEntry(syncCode); clearSyncCode(true); }")
    pg.wait_for_timeout(200)
    res = pg.evaluate("()=>({del:__deleted.slice(), off:localStorage.getItem('class26e.syncoff')})")
    check("stopping sync deletes the row and records the opt-out",
          "leaderboard/BBBB-2222" in res["del"] and res["off"] == "1", str(res))
    ctx.close()

    # ---- 6. a cached snapshot is NOT a remote reset ----
    # Reported from a device: "when signing up it randomly reset my account
    # and showed the notification that the account was reset from another
    # device." exists:false means two different things depending on where
    # the snapshot came from - genuinely deleted (server) or just not known
    # here yet (cache, while reconnecting or around a fresh signup). Acting
    # on the cached one wipes a live account.
    #
    # This drives the app's own listener callback with the exact snapshots
    # Firestore delivers, rather than waiting for a real network race. It
    # fails on the build before this check existed: step 3 resets.
    print("\n6. only a server-confirmed deletion counts as a remote reset")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2601');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    seq = [
        {"label": "cache says missing, before the first push", "exists": False, "fromCache": True,  "reset": False},
        {"label": "server confirms it exists",                 "exists": True,  "fromCache": False, "reset": False},
        {"label": "cache replays missing after a drop",        "exists": False, "fromCache": True,  "reset": False},
        {"label": "server confirms it again",                  "exists": True,  "fromCache": False, "reset": False},
        {"label": "server says it is gone - a real reset",     "exists": False, "fromCache": False, "reset": True},
    ]
    got = pg.evaluate("""(seq)=>{
      let cb=null, fired=0;
      const ref={ onSnapshot:(next)=>{ cb=next; return ()=>{}; } };
      const realReset = window.handleRemoteReset;
      const origDb = fbDb;
      window.handleRemoteReset = ()=>{ fired++; };
      fbDb = { collection:()=>({ doc:()=>ref }) };
      syncCode = 'NOVA-2601';
      attachLiveListener('NOVA-2601');
      const out=[];
      seq.forEach(s=>{ const before=fired;
        cb({ exists:s.exists, metadata:{ fromCache:s.fromCache },
             data:()=>({ lastModified:1, firstName:'Madison' }) });
        out.push(fired>before); });
      window.handleRemoteReset = realReset; fbDb = origDb;
      return out;}""", seq)
    for i, s in enumerate(seq):
        check("%s -> %s" % (s["label"], "reset" if s["reset"] else "no reset"),
              got[i] == s["reset"], "fired=%s" % got[i])
    ctx.close()

    # ---- 7. the sync code never reaches a collection anyone can list ----
    # `leaderboard` and `vrooms` can both be ENUMERATED by anyone - this
    # repo's own firestore-admin.py lists them over plain REST with no
    # credentials, which is the access every classmate has - and the sync
    # code IS the account. For a long time the document id on both WAS
    # the sync code, so opening the Rankings screen handed the client
    # every classmate's account key beside their name and avatar.
    # This captures every write the app would make to a listable
    # collection and asserts the secret is in none of them, in any
    # position: not as a document id, not as a participant key, not as a
    # field value. It fails on build 136 and every build before it.
    print("\n7. the sync code never reaches a collection anyone can list")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""()=>{
      const wrote = [];
      fbDb = { collection: name => ({
          doc: id => ({
            set: d => { wrote.push({ col:name, id:id, data:d }); return Promise.resolve(); },
            update: d => { wrote.push({ col:name, id:id, data:d }); return Promise.resolve(); },
            get: () => Promise.resolve({ exists:false }),
            delete: () => Promise.resolve()
          })
        }) };
      store.leaderboardOptIn = true;
      pushToCloud();
      /* And a Virtual Room, which keys its PARTICIPANTS by the same id
         and lives in a collection that is just as listable. */
      try { createVirtualRoom(['Identity Crimes']); } catch(e){}
      const pub = store.publicId;
      const listable = wrote.filter(w => w.col === 'leaderboard' || w.col === 'vrooms');
      const flat = JSON.stringify(listable);
      return { pub: pub, n: listable.length,
               idIsSecret: listable.some(w => w.id === syncCode),
               secretAnywhere: flat.indexOf(syncCode) >= 0,
               allPublic: listable.length > 0 && listable.every(w => w.id === pub || w.col === 'vrooms'),
               derived: !!(pub && (syncCode.indexOf(pub) >= 0
                          || pub.indexOf(syncCode.replace('-','')) >= 0)) };}""")
    check("this device publishes something to check", r["n"] > 0, str(r))
    check("no document id is the sync code", r["idIsSecret"] is False, str(r))
    check("the sync code is nowhere in any of it", r["secretAnywhere"] is False, str(r))
    check("the public id is not derived from the secret", r["derived"] is False, str(r))
    ctx.close()

    br.close()

srv.shutdown()
print("\n%s  (%d failure(s))" % ("ALL PASS" if not fails else "FAILED: " + ", ".join(fails), len(fails)))
sys.exit(1 if fails else 0)
