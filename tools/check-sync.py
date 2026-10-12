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
        return Promise.resolve(d ? { exists: true, metadata: { fromCache: false }, data: function(){ return d; } }
                                 : { exists: false, metadata: { fromCache: false } }); },
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
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)
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
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
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
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % hidden)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    pg.evaluate("()=>showRankings('week')"); pg.wait_for_timeout(400)
    # MOVED IN 324 (builder L): "If I have it off then I shouldn't be able
    # to see it." Hidden is no longer a Find me message - there is no board
    # and no Find me at all, only the hidden card, and the reason it names
    # is the same setting, as its one button.
    res = pg.evaluate("""()=>({findMe:!!document.querySelector('.rank-me-btn'),
        rows:document.querySelectorAll('.rank-rows .rank-row').length,
        card:(document.querySelector('.lb-optout')||{}).textContent||''})""")
    check("hidden: no board and no Find me, and the card names the Settings toggle",
          not res["findMe"] and res["rows"] == 0 and "Show me in the rankings" in res["card"], str(res))
    ctx.close()

    # ---- 4. localStorage evicted: recovery must land on Home, with the code ----
    print("\n4. localStorage lost, IndexedDB mirror intact")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    pg = page(ctx)
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                       "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); saveStore();}")
    pg.wait_for_timeout(600)
    mirrored = pg.evaluate("()=>idbLoadCode? idbLoadCode() : null") \
        if pg.evaluate("()=>typeof idbLoadCode==='function'") else None
    check("the code is mirrored into IndexedDB", mirrored == "WXYZ-7777", repr(mirrored))
    pg.close()

    pg2 = page(ctx)   # same context: IndexedDB survives, localStorage does not
    pg2.add_init_script("try{localStorage.clear();localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');}catch(e){}")
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
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                       "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); saveStore();}")
    pg.wait_for_timeout(600)
    pg.close()

    pg2 = page(ctx)   # same context: the mirror survives, the code key does not
    pg2.add_init_script("try{localStorage.clear();localStorage.setItem('class26e.freshstart','1');"
                        "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');"
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
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
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
                        "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');}catch(e){}")
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
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(700)
    pg.evaluate("()=>document.querySelector('.sync-code-row').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(300)
    """THE SAVE CODE BUTTON IS GONE, ON REQUEST, AND THIS CHECK WAS
    ASSERTING IT. It drove `.sync-save-row .cal-profile-btn`, clicked it,
    and read the clipboard - and that button came off Settings two builds
    ago because the screen was reported as a pile of controls. So the
    gate has been red since then for demanding a control the app was
    asked to remove, which is the seventh time in this repo a check has
    encoded a DECISION and then failed the app for being right.

    What has NOT changed is why the check exists: removing the app
    destroys the whole storage jar, so neither recovery above can help
    and what is left is the code, from memory. That is still the
    invariant, and it is still true - the code lives on a row in
    Settings that reveals it on a tap, with a line underneath saying to
    keep it somewhere else. So the check asks for THAT, by driving it
    the way a person does rather than by calling anything.

    ONE CONSEQUENCE IS WORTH KNOWING AND IS NOT A FAILURE HERE:
    `saveSyncCodeVia()` was that button's only caller, so nothing sets
    `store.savedCodeSaved` any more and the save-code reminder now runs
    its full three prompts whether or not anybody saved anything. The
    banner still works and still lands on this section; there is simply
    no longer a moment the app can call "saved". Raised with Madison
    rather than patched around, because the fix is another button and
    the button is the thing she asked to remove."""
    row = pg.query_selector(".sync-code-row")
    check("the code still has a row in Settings", row is not None)
    hidden = pg.evaluate("()=>{const v=document.querySelector('.sync-code-value');"
                         " return v ? v.textContent : null;}")
    check("and it starts hidden", hidden is not None and "WXYZ" not in hidden, hidden)
    if row:
        row.click(); pg.wait_for_timeout(250)
    shown = pg.evaluate("()=>{const v=document.querySelector('.sync-code-value');"
                        " return v ? v.textContent : null;}")
    check("Settings hands over the code", shown == "WXYZ-7777", shown)
    # Tapping again has to put it back. A code left on screen is a code
    # on screen in a classroom, which is the reason it is hidden at all.
    if row:
        row.click(); pg.wait_for_timeout(250)
    rehidden = pg.evaluate("()=>{const v=document.querySelector('.sync-code-value');"
                           " return v ? v.textContent : null;}")
    check("and a second tap hides it again",
          rehidden is not None and "WXYZ" not in rehidden, rehidden)
    note = pg.evaluate("""()=>{
      const n = [...document.querySelectorAll('#settings-sync-sect .sync-note-plain')]
        .map(p => p.textContent).join(' ');
      return n;}""")
    check("with the sentence saying why to keep it",
          "loses its data" in note or "off this phone" in note, note[:90])
    # THE PILE IS GONE AND HAS TO STAY GONE. The sync section was
    # reported as four visual languages stacked; this is the shape it
    # was cut down to, asserted as a count rather than as a list of
    # labels so a rename cannot turn it red.
    nbtn = pg.evaluate("()=>document.querySelectorAll('#settings-sync-sect button').length")
    check("the sync section is not a pile of buttons again", nbtn <= 2, str(nbtn))

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

    # ---- 4e. a cloud document must not cost you your publicId ----
    # THE DUPLICATE-ROW BUG, and it was live on the class board. The
    # rankings row is keyed by publicId, so minting a new one means a
    # SECOND row with the same progress in it and nobody holding the id
    # to the first. applyLoadedData() used to null the local publicId
    # whenever the incoming document carried none - which is every
    # document written before publicId existed - and the next push then
    # minted a fresh one. Two people on the live board had duplicate
    # rows with identical correct-answer counts minutes apart.
    print("\n4e. applying cloud data does not mint a second rankings row")
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake([]);}")
    pg.wait_for_timeout(400)
    before = pg.evaluate("()=>publicIdOf()")
    check("this device has a public id", bool(before), before)

    # A document from an older build: newer than ours, and no publicId.
    kept = pg.evaluate("""(mine)=>{
      applyLoadedData({ firstName:"Madison", onboardingComplete:true,
        leaderboardOptIn:true, lastModified: Date.now(),
        lifetime:{points:999, correct:99} });
      return { after: store.publicId, same: store.publicId === mine };
    }""", before)
    check("an old document without one does not wipe it",
          kept["same"] is True, str(kept))
    check("and no new id is minted on the next publish",
          pg.evaluate("()=>publicIdOf()") == before, before)

    # The linking case must still work: a document that HAS an id wins,
    # because that is how this device adopts the account it linked to.
    linked = pg.evaluate("""()=>{
      applyLoadedData({ firstName:"Madison", onboardingComplete:true,
        leaderboardOptIn:true, publicId:"theirpublicid", lastModified: Date.now(),
        lifetime:{points:5, correct:5} });
      return store.publicId; }""")
    check("but a document that carries one still wins (linking)",
          linked == "theirpublicid", linked)

    # AND NOBODY GETS SIGNED OUT BY ANY OF IT. The publicId is the
    # anonymous id on a rankings row; the SYNC CODE is the account, and
    # being signed in depends on that plus onboardingComplete. Neither
    # is touched here - but "neither is touched" is a code read, and a
    # code read is exactly what this file exists not to rely on. So it
    # is measured, on the same page, after both documents have landed.
    still = pg.evaluate("""()=>({
      code: syncCode, ls: localStorage.getItem('class26e.synccode'),
      onboarded: !!store.onboardingComplete, name: store.firstName,
      screen: (document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen || null,
      welcome: !!document.querySelector('[data-screen="welcome"]')})""")
    check("the sync code is untouched", still["code"] == "WXYZ-7777"
          and still["ls"] == "WXYZ-7777", str(still))
    check("the account is still onboarded", still["onboarded"] is True, str(still))
    check("and nobody is dropped on Welcome", still["welcome"] is False, str(still))
    ctx.close()

    # ---- 4f. the board shows one row per person ----
    # 4e stops NEW duplicates; the ones already published have no owner
    # and cannot delete themselves, so the board has to collapse them.
    # Narrow on purpose: name AND character, because "usernames are not
    # unique" and collapsing on a name alone would hide a real person.
    print("\n4f. duplicate rows are collapsed on the board")
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.evaluate("""()=>{ __fake([
      /* one person, two rows, the real one richer */
      {pub:"dup-rich", firstName:"Billy", avatarChar:"fox", level:11, hundos:5, correct:333, weekPoints:3980, lastModified:2},
      {pub:"dup-poor", firstName:"Billy", avatarChar:"fox", level:4,  hundos:0, correct:81,  weekPoints:1030, lastModified:9},
      /* same name, DIFFERENT character - two real people, both stay */
      {pub:"twin-a", firstName:"Sam", avatarChar:"owl",   level:7, hundos:2, correct:150, weekPoints:400, lastModified:5},
      {pub:"twin-b", firstName:"Sam", avatarChar:"robot", level:3, hundos:1, correct:70,  weekPoints:200, lastModified:5},
      {pub:"solo",   firstName:"Dana", avatarChar:"ninja", level:9, hundos:3, correct:210, weekPoints:600, lastModified:5}
    ]); }""")
    pg.evaluate("()=>showRankings('level')"); pg.wait_for_timeout(700)
    def names():
        return pg.evaluate("()=>[...document.querySelectorAll('.rank-row')]"
                           ".map(r=>(r.textContent||'').replace(/\\s+/g,' ').trim())")
    shown = names()
    billy = [n for n in shown if "Billy" in n]
    check("the duplicate appears once", len(billy) == 1, str(billy))
    # Asserted on Hundos, where the two rows differ unambiguously (5 vs
    # 0). The level board's row text carries the week unit, so checking
    # for "11" there was reading the wrong number off the right row.
    pg.evaluate("()=>showRankings('hundos')"); pg.wait_for_timeout(500)
    rich = [n for n in names() if "Billy" in n]
    check("and it is the row with the real progress",
          bool(rich) and "5 hundos" in rich[0], str(rich))
    check("two people sharing a name both stay",
          len([n for n in shown if "Sam" in n]) == 2, str(shown))

    # The same row has to survive on every board, or somebody appears on
    # one tab and vanishes on another.
    for key in ["week", "hundos"]:
        pg.evaluate("(k)=>showRankings(k)", key); pg.wait_for_timeout(500)
        b = [n for n in names() if "Billy" in n]
        check("still one Billy on the %s board" % key, len(b) == 1, str(b))
    ctx.close()

    # ---- 5. swapping codes retires the old rankings row ----
    print("\n5. abandoning a code takes its rankings row with it")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
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
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
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

    # ---- 8. two devices, one account: merged, never overwritten ----
    # Build 284. "on his two devices, he says he synced them but each
    # account is still a different level but I only see one in the
    # leaderboard". Sync was last-write-wins by lastModified, and a boot
    # save stamps lastModified before the first pull - so a device that
    # had been away pushed its stale copy over the other device's
    # progress. Every case here fails on 283.
    print("\n8. two devices on one account: merged, never overwritten")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2601');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      let cloud = null, cb = null;
      const writes = [];
      fbDb = { collection: name => ({ doc: id => ({
        get: () => Promise.resolve(name === 'progress' && cloud ? { exists: true, metadata: { fromCache: false }, data: () => clone(cloud) } : { exists: false, metadata: { fromCache: false } }),
        set: d => { if(name === 'progress') writes.push(clone(d)); return Promise.resolve(); },
        update: d => Promise.resolve(),
        delete: () => Promise.resolve(),
        onSnapshot: next => { cb = next; return () => {}; }
      }) }) };
      syncCode = 'NOVA-2601';
      const out = {};
      const base = () => { const s = clone(store); s.stats = {}; s.testHistory = []; s.unitPerfects = {}; return s; };

      /* (a) THE REPORTED BUG. The other device studied: the cloud has 900
         points and a question this device never saw. This device is
         stale (500 points) but saved something trivial at boot, so its
         stamp is NEWER. */
      const NOW = Date.now();
      cloud = base(); cloud.lifetime.points = 900; cloud.lastModified = NOW - 60000;
      cloud.stats.qOTHER = { n: 4, m: 1, r: [10] };
      cloud.testHistory = [{ playedAt: 900, label: 'Other device', pct: 100, mode: 'drill', units: [] }];
      store.lifetime.points = 500; store.stats = { qMINE: { n: 2, m: 0, r: [] } }; store.testHistory = []; /* a stale copy, not play: build 298's tallies would read a value set by hand as this device's own new progress */ if(store.tally){ store.tally = {}; store.tallyBase = {}; }
      store.lastModified = NOW;
      writes.length = 0;
      await new Promise(res => pullFromCloud('NOVA-2601', () => res()));
      await wait(3200);
      const last = writes[writes.length - 1] || null;
      out.a = { points: store.lifetime.points, other: !!store.stats.qOTHER, mine: !!store.stats.qMINE,
                history: (store.testHistory || []).length,
                pushedPoints: last ? last.lifetime.points : null, pushedBoth: !!(last && last.stats.qOTHER && last.stats.qMINE) };

      /* (b) the other device's clock is BEHIND: its copy arrives through
         the listener stamped older, with progress this one lacks */
      attachLiveListener('NOVA-2601');
      const older = clone(store); older.lastModified = store.lastModified - 3600000; older.lifetime.points = 1200;
      older.unitPerfects = { 'Identity Crimes': 7 };
      if(cb) cb({ exists: true, metadata: { fromCache: false }, data: () => clone(older) });
      out.b = { points: store.lifetime.points, perfects: (store.unitPerfects || {})['Identity Crimes'] || 0 };

      /* (c) our own write echoing back changes nothing and pushes nothing */
      await wait(3200);
      writes.length = 0;
      const echo = clone(store);
      if(cb) cb({ exists: true, metadata: { fromCache: false }, data: () => clone(echo) });
      await wait(3200);
      out.c = { writes: writes.length, points: store.lifetime.points };

      const hasMerge = typeof mergeSameAccount === 'function';
      if(hasMerge){
      /* (d) two copies converge, and merging again adds nothing */
      const A = base(), B = base();
      A.lifetime.points = 300; A.stats = { q1: { n: 3, m: 1, r: [1] } }; A.unitPerfects = { U: 2 };
      B.lifetime.points = 450; B.stats = { q2: { n: 1, m: 0, r: [] }, q1: { n: 5, m: 0, r: [2] } }; B.unitPerfects = { U: 1, V: 4 };
      mergeSameAccount(A, clone(B)); mergeSameAccount(B, clone(A));
      const canon = v => Array.isArray(v) ? '[' + v.map(canon).join(',') + ']' : (v && typeof v === 'object') ? '{' + Object.keys(v).sort().map(k => k + ':' + canon(v[k])).join(',') + '}' : JSON.stringify(v);
      const pick = s => canon([s.lifetime.points, s.stats, s.unitPerfects]);
      const again = mergeSameAccount(A, clone(B));
      out.d = { same: pick(A) === pick(B), again: again.gained || again.otherHadLess, q1: A.stats.q1 };

      /* (e) a cleared most-missed list stays cleared */
      const C = base(), D = base();
      C.stats = { q: { n: 6, m: 3, r: [], rc: 5000 } };
      D.stats = { q: { n: 6, m: 3, r: [100, 200] } };
      mergeSameAccount(C, D);
      out.e = { r: C.stats.q.r || [] };
      } else { out.d = { same: false, again: true, q1: { n: 0, m: 0 } }; out.e = { r: ['no merge'] }; }

      /* (f) linking ADOPTS: this device's own, different progress is
         not pushed over the account it links to */
      detachLiveListener();
      cloud = base(); cloud.lifetime.points = 777; cloud.lastModified = Date.now() - 600000;
      store.lifetime.points = 50; store.lastModified = Date.now();
      writes.length = 0;
      await new Promise(res => (typeof adoptFromCloud === 'function' ? adoptFromCloud : pullFromCloud)('NOVA-2601', () => res()));
      await wait(3200);
      out.f = { points: store.lifetime.points, pushedMine: writes.some(w => w.lifetime && w.lifetime.points === 50) };
      return out; }""")
    a = r["a"]
    check("a stale device stamped newer takes the other device's progress, not the other way round",
          a["points"] == 900 and a["other"] and a["mine"] and a["history"] == 1, str(a))
    check("and pushes the merge - both devices' progress - never its stale copy",
          a["pushedPoints"] == 900 and a["pushedBoth"], str(a))
    check("progress from a device whose clock is behind still merges in",
          r["b"]["points"] == 1200 and r["b"]["perfects"] == 7, str(r["b"]))
    check("this device's own write echoing back pushes nothing",
          r["c"]["writes"] == 0, str(r["c"]))
    check("two copies converge, and merging again changes nothing",
          r["d"]["same"] and not r["d"]["again"] and r["d"]["q1"]["n"] == 5 and r["d"]["q1"]["m"] == 1, str(r["d"]))
    check("a cleared most-missed list stays cleared when the other device still has the misses",
          r["e"]["r"] == [], str(r["e"]))
    check("linking a device takes the account as it is and pushes nothing of the device's own",
          r["f"]["points"] == 777 and not r["f"]["pushedMine"], str(r["f"]))
    ctx.close()

    # ---- 8b. a credit note pays an account once ----
    # Build 284. A parallel sign-up whose device was reset left a
    # rankings row with no progress document behind it, so there is no
    # device to follow a merge note. The credit note sits beside the
    # account it is FOR and every device on that account reads it; it has
    # to pay once per ACCOUNT, not once per device. Fails on 283, which
    # has no credit note at all.
    print("\n8b. a credit note pays an account once, on whichever device sees it")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2601');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      let credit = null;
      const marked = [];
      fbDb = { collection: name => ({ doc: id => ({
        id,
        get: () => Promise.resolve(id === 'NOVA-2601__credit' && credit
          ? { exists: true, data: () => clone(credit), ref: { set: d => { marked.push(clone(d)); credit = Object.assign(credit, d); return Promise.resolve(); } } }
          : { exists: false }),
        set: d => Promise.resolve(),
        update: d => Promise.resolve(),
        delete: () => Promise.resolve(),
        onSnapshot: next => () => {}
      }) }) };
      syncCode = 'NOVA-2601';
      try{ rollWeek(); }catch(e){}
      const run = async () => { accountMoveChecked = ''; checkAccountMove('NOVA-2601'); await wait(400); };
      const snap = () => ({ points: store.lifetime.points, correct: store.lifetime.correct, week: store.weekPoints || 0 });
      const out = { before: snap() };
      credit = { id: 'row:test', extra: { points: 1000, correct: 90, weekPoints: 400, week: store.weekKey }, at: Date.now() };
      const keep = clone(credit);
      await run();
      out.first = snap(); out.marked = marked.length; out.applied = (store.creditsApplied || []).slice();
      out.held = !!store.mergeHold;
      /* the note was marked done; pretend that write never landed and
         the same note is read again */
      credit = clone(keep); await run(); out.again = snap();
      /* a second device on the same account that has already synced the
         first one's creditsApplied does not pay it again */
      if(typeof mergeSameAccount === 'function'){
        const other = clone(store);
        store.creditsApplied = []; store.lifetime.points = out.before.points; store.lifetime.correct = out.before.correct;
        mergeSameAccount(store, other);
        credit = clone(keep); await run(); out.second = snap();
      }
      /* a note somebody already followed pays nothing on a fresh account */
      store.creditsApplied = [];
      const p0 = snap();
      credit = Object.assign(clone(keep), { done: 123 }); await run(); out.done = { before: p0, after: snap() };
      return out; }""")
    b, f = r["before"], r["first"]
    check("a credit note adds its XP, right answers and this week's points",
          f["points"] == b["points"] + 1000 and f["correct"] == b["correct"] + 90 and f["week"] == b["week"] + 400, str(r))
    check("and the device marks the note followed, and holds anything it unlocks for the next test",
          r["marked"] == 1 and r["applied"] == ["row:test"] and r["held"], str(r))
    check("the same note read again pays nothing",
          r.get("again") == f, str(r.get("again")))
    check("a second device on the account, already synced, pays nothing",
          r.get("second") == f, str(r.get("second")))
    check("a note already followed pays nothing",
          r["done"]["after"] == r["done"]["before"], str(r["done"]))
    ctx.close()

    # ---- 8c. the unlock hold travels with the account ----
    # Build 286. A merge or credit sets mergeHold so what it unlocks plays
    # after the next test. A device whose own copy was newer kept its
    # copy without the hold and pushed it up, so the unlocks played on
    # Home instead. Fails on 285.
    print("\n8c. the unlock hold survives a sync, and a spent one stays spent")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2601');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""()=>{
      const clone = o => JSON.parse(JSON.stringify(o));
      const base = clone(store); base.mergeHold = null; base.mergeHoldDone = 0;
      const hold = (pts, at) => ({ points: pts, perfects: {}, chars: [], banners: [], at });
      const out = {};
      if(typeof mergeSameAccount !== 'function') return { none: true };
      /* (a) the cloud carries a hold, this device's newer copy does not */
      const A = clone(base), B = clone(base); B.mergeHold = hold(500, 1000);
      mergeSameAccount(A, B); out.a = A.mergeHold ? A.mergeHold.points : null;
      /* (b) a test on this device spent the hold after it was set */
      const C = clone(base), D = clone(base); C.mergeHoldDone = 2000; D.mergeHold = hold(500, 1000);
      mergeSameAccount(C, D); out.b = C.mergeHold;
      /* ... and the device holding the stale copy learns it was spent */
      const E = clone(base), F = clone(base); E.mergeHold = hold(500, 1000); F.mergeHoldDone = 2000;
      mergeSameAccount(E, F); out.b2 = E.mergeHold;
      /* (c) two holds: the lower baseline is kept */
      const G = clone(base), H = clone(base); G.mergeHold = hold(900, 3000); H.mergeHold = hold(400, 3100);
      mergeSameAccount(G, H); out.c = G.mergeHold && G.mergeHold.points;
      /* (d) and it survives a cloud copy coming back through the listener path */
      const cloud = clone(base); cloud.mergeHold = hold(700, Date.now()); cloud.lastModified = 1;
      store.mergeHold = null; store.mergeHoldDone = 0; store.lastModified = Date.now();
      syncSameAccount(cloud); out.d = store.mergeHold ? store.mergeHold.points : null;
      return out; }""")
    check("a hold on the other copy is kept when this device's copy is newer",
          r.get("a") == 500 and r.get("d") == 700, str(r))
    check("a hold a test has already spent is not brought back, on either side",
          r.get("b") is None and r.get("b2") is None, str(r))
    check("of two holds, the lower baseline is kept", r.get("c") == 400, str(r))
    ctx.close()

    # ---- 8d. a merge the server already did is not added twice ----
    # Build 287. Z's phone runs a build from before move notes and pushes
    # its own document over the server on every launch, so his two
    # accounts were merged on the server and the note on his old code
    # carries `base`, the account as merged. When the phone finally
    # updates and follows the note it must add only what was played
    # since. Fails on 286, which adds the whole store again.
    print("\n8d. a merge note with a base adds only what was played since")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-OLD1');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      const U = topicsIn(QUESTIONS)[0], K = KEYS[0];
      const base = clone(store);
      base.lifetime = { points: 1000, correct: 80, answered: 100, perfectTests: 2 };
      base.unitPerfects = { [U]: 2 }; base.studyLog = { '2026-09-28': 60000 };
      base.stats = { [K]: { n: 4, m: 1, r: [111] } };
      base.testHistory = [{ playedAt: 5000, pct: 100 }];
      /* the phone kept playing after the server merged it */
      const now = clone(base);
      now.lifetime = { points: 1500, correct: 120, answered: 150, perfectTests: 3 };
      now.unitPerfects = { [U]: 3 }; now.studyLog = { '2026-09-28': 60000, '2026-10-03': 30000 };
      now.stats = { [K]: { n: 6, m: 2, r: [111, 222] } };
      now.testHistory = [{ playedAt: 9000, pct: 100 }, { playedAt: 5000, pct: 100 }];
      /* the account it moves to already holds its own 3000 and the base */
      const target = clone(base);
      target.firstName = 'Target'; target.publicId = 'tgt000000000';
      target.lifetime = { points: 4000, correct: 300, answered: 400, perfectTests: 7 };
      target.unitPerfects = { [U]: 5 }; target.studyLog = { '2026-09-28': 90000 };
      target.stats = { [K]: { n: 9, m: 3, r: [111, 333] } };
      target.testHistory = [{ playedAt: 7000, pct: 90 }, { playedAt: 5000, pct: 100 }];
      fbDb = { collection: name => ({ doc: id => ({ id,
        get: () => Promise.resolve(id === 'NOVA-TGT1' ? { exists: true, metadata: { fromCache: false }, data: () => clone(target) } : { exists: false, metadata: { fromCache: false } }),
        set: d => Promise.resolve(), update: d => Promise.resolve(), delete: () => Promise.resolve(),
        onSnapshot: next => () => {} }) }) };
      Object.keys(now).forEach(k => { store[k] = clone(now[k]); });
      syncCode = 'NOVA-OLD1';
      const noteRef = { set: () => Promise.resolve() };
      followAccountMove('NOVA-OLD1', 'NOVA-TGT1', noteRef, { to: 'NOVA-TGT1', merge: true, base: clone(base) });
      await wait(500);
      return { code: syncCode, points: store.lifetime.points, correct: store.lifetime.correct, hundos: store.lifetime.perfectTests,
               unit: store.unitPerfects[U], study: store.studyLog, n: store.stats[K].n, m: store.stats[K].m,
               tests: (store.testHistory || []).map(t => t.playedAt) }; }""")
    check("the device moves to the account it was merged into", r.get("code") == "NOVA-TGT1", str(r))
    check("and adds only the XP, right answers and hundos earned since the merge",
          r.get("points") == 4500 and r.get("correct") == 340 and r.get("hundos") == 8 and r.get("unit") == 6, str(r))
    check("per question and per day, the same: only the difference",
          r.get("n") == 11 and r.get("m") == 4 and r.get("study") == {"2026-09-28": 90000, "2026-10-03": 30000}, str(r))
    check("and the test played before the merge is not listed twice",
          sorted(r.get("tests") or []) == [5000, 7000, 9000], str(r))
    ctx.close()

    # ---- 8e. a stale device opening does not overwrite the account ----
    # Build 296. Cmilledge went from level 46 to 26, Billyswole from 8
    # hundos to 3, on Oct 2-3. Boot called pushToCloud() the moment
    # Firebase was ready - a whole-document set() of this device's copy,
    # before it had read anything - so a second device holding older
    # progress wrote it over the account every time it opened. The merge
    # could not catch it: Firestore shows a device its own pending write,
    # so the newer server copy never reached it. Fails on 295.
    # Build 315: the server here is unreachable until its snapshot comes
    # - it used to answer a direct read with "no such document" while its
    # listener said otherwise, and build 313's own server read then
    # confirmed an account that did not exist. That passed on 313 only
    # because its push happened to land after the snapshot.
    print("\n8e. a stale device opening does not overwrite the account")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2601');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      const writes = []; let cb = null;
      /* the account on the server, which this device cannot reach until
         its snapshot comes through */
      let server = null, serverUp = false;
      fbDb = { collection: name => ({
        onSnapshot: () => () => {},
        doc: id => ({
          get: () => (name === 'progress' && id === 'NOVA-2601')
            ? (serverUp ? Promise.resolve({ exists: !!server, metadata: { fromCache: false }, data: () => clone(server) }) : Promise.reject(new Error('unavailable')))
            : Promise.resolve({ exists: false, metadata: { fromCache: false } }),
          set: d => { if(name === 'progress' && (id === 'NOVA-2601' || id === 'NOVA-NEW1')) writes.push(clone(d)); return Promise.resolve(); },
          update: () => Promise.resolve(), delete: () => Promise.resolve(),
          onSnapshot: next => { if(name === 'progress' && (id === 'NOVA-2601' || id === 'NOVA-NEW1')) cb = next; return () => {}; }
        }) }) };
      /* the stale device: 500 points, stamped NOW by a boot save */
      syncCode = 'NOVA-2601';
      store.lifetime.points = 500; store.unitPerfects = { U: 1 }; store.lastModified = Date.now(); /* a stale copy, not play: build 298's tallies would read a value set by hand as this device's own new progress */ if(store.tally){ store.tally = {}; store.tallyBase = {}; }
      /* the account in the cloud: the other device's 900 points, 5 hundos */
      const cloud = clone(store); cloud.lifetime.points = 900; cloud.unitPerfects = { U: 5 };
      cloud.lastModified = Date.now() - 60000;
      server = cloud;
      writes.length = 0;
      fbReadyDrained = false; firebaseBecameReady();
      await wait(3200);
      const out = { atBoot: writes.map(w => w.lifetime.points) };
      /* Firestore delivers its cached copy first: still not the server */
      if(cb) cb({ exists: true, metadata: { fromCache: true }, data: () => clone(Object.assign(clone(cloud), { lifetime: Object.assign({}, cloud.lifetime, { points: 450 }) })) });
      await wait(3200);
      out.afterCache = writes.map(w => w.lifetime.points);
      /* then the server's */
      serverUp = true;
      if(cb) cb({ exists: true, metadata: { fromCache: false }, data: () => clone(cloud) });
      await wait(3200);
      const last = writes[writes.length - 1] || null;
      out.after = { n: writes.length, points: last && last.lifetime.points, U: last && (last.unitPerfects || {}).U,
                    local: store.lifetime.points, localU: (store.unitPerfects || {}).U };
      out.anyStale = writes.some(w => w.lifetime.points < 900);
      /* a brand-new account: the server says there is no document, and
         the first push - the one creating it - goes */
      writes.length = 0; cb = null;
      syncCode = 'NOVA-NEW1'; store.lifetime.points = 10; store.lastModified = Date.now();
      attachLiveListener('NOVA-NEW1'); scheduleCloudPush();
      await wait(3200);
      out.newBefore = writes.length;
      if(cb) cb({ exists: false, metadata: { fromCache: false } });
      await wait(3200);
      out.newAfter = writes.length;
      return out; }""")
    check("a device opening does not write its copy over the account before reading the server's",
          r["atBoot"] == [] and r["afterCache"] == [], str([r["atBoot"], r["afterCache"]]))
    check("once the server's copy arrives, what goes up is the merge - the other device's 900 points and 5 hundos",
          r["after"]["n"] >= 1 and r["after"]["points"] == 900 and r["after"]["U"] == 5 and not r["anyStale"], str(r["after"]))
    check("and this device keeps the merged copy", r["after"]["local"] == 900 and r["after"]["localU"] == 5, str(r["after"]))
    check("a brand-new account's first push still goes, once the server says there is nothing there yet",
          r["newBefore"] == 0 and r["newAfter"] >= 1, str([r["newBefore"], r["newAfter"]]))
    ctx.close()

    # ---- 8f. an old build's overwrite comes back from the high-water mark ----
    # Build 298. A phone still on 295 or older set() its own copy over the
    # account at every launch - Hector went from 17,585 XP to 2,330 hours
    # after 296 shipped - and nothing in a new build can stop an old
    # build's write. progress/<code>__floor, which old builds never touch,
    # is read on launch and merged in before anything is pushed. Fails on
    # 297, which has no floor at all.
    print("\n8f. an old build's overwrite comes back from the high-water mark")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2602');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      const writes = [], deletes = []; let cb = null; let floor = null; const floorReads = [];
      fbDb = { collection: name => ({
        onSnapshot: () => () => {},
        doc: id => ({
          get: () => {
            if(name === 'progress' && /__floor$/.test(id)){
              floorReads.push(Date.now());
              /* slow on purpose: nothing may write the floor before this lands */
              return new Promise(res => setTimeout(() => res(floor ? { exists: true, data: () => clone(floor) } : { exists: false }), 1500));
            }
            return Promise.resolve({ exists: false, metadata: { fromCache: false } });
          },
          set: d => { if(name === 'progress') writes.push({ id, at: Date.now(), points: (d.lifetime || {}).points, U: (d.unitPerfects || {}).U, cred: d.creditsApplied }); return Promise.resolve(); },
          update: () => Promise.resolve(),
          delete: () => { deletes.push(name + '/' + id); return Promise.resolve(); },
          onSnapshot: next => { if(name === 'progress' && /^NOVA-/.test(id) && !/__/.test(id)) cb = next; return () => {}; }
        }) }) };
      const out = {};
      /* the old build has knocked the account down to its own copy */
      syncCode = 'NOVA-2602';
      store.lifetime.points = 2330; store.unitPerfects = {}; store.creditsApplied = []; store.lastModified = Date.now(); /* a stale copy, not play: build 298's tallies would read a value set by hand as this device's own new progress */ if(store.tally){ store.tally = {}; store.tallyBase = {}; }
      const server = clone(store);
      floor = clone(store); floor.lifetime.points = 17585; floor.unitPerfects = { U: 13 }; floor.creditsApplied = ['row:old'];
      floor.lastModified = Date.now() - 3600000;
      writes.length = 0;
      fbReadyDrained = false; firebaseBecameReady();
      await wait(600);
      if(cb) cb({ exists: true, metadata: { fromCache: false }, data: () => clone(server) });
      await wait(400);
      out.floorWritesBeforeRead = writes.filter(w => /__floor$/.test(w.id)).length;
      await wait(4200);
      const prog = writes.filter(w => w.id === 'NOVA-2602'), fl = writes.filter(w => /__floor$/.test(w.id));
      const lastP = prog[prog.length - 1] || {}, lastF = fl[fl.length - 1] || {};
      out.restored = { local: store.lifetime.points, localU: (store.unitPerfects || {}).U, cred: store.creditsApplied,
                       pushed: lastP.points, pushedU: lastP.U, floorPoints: lastF.points, floorReads: floorReads.length,
                       floorNeverLower: fl.every(w => w.points >= 17585) };

      /* a reset account: the server says there is no document. A floor
         left behind must not bring it back. */
      writes.length = 0; cb = null; floorReads.length = 0;
      syncCode = 'NOVA-2603'; cloudConfirmedFor = '';
      store.lifetime.points = 0; store.unitPerfects = {}; store.lastModified = Date.now();
      floor = clone(store); floor.lifetime.points = 9999;
      attachLiveListener('NOVA-2603'); scheduleCloudPush();
      await wait(300);
      if(cb) cb({ exists: false, metadata: { fromCache: false } });
      await wait(3200);
      out.reset = { local: store.lifetime.points, floorReads: floorReads.length,
                    floorWritten: writes.filter(w => w.id === 'NOVA-2603__floor').map(w => w.points) };

      /* and resetting deletes it */
      syncCode = 'NOVA-2602';
      try{ resetEverything(); }catch(e){ out.resetErr = String(e); }
      out.deletes = deletes;
      return out; }""")
    check("an old build's overwrite is merged back from the floor on launch",
          r["restored"]["local"] == 17585 and r["restored"]["localU"] == 13 and "row:old" in (r["restored"]["cred"] or []), str(r["restored"]))
    check("and the restored account is what goes up, to the account and the floor",
          r["restored"]["pushed"] == 17585 and r["restored"]["pushedU"] == 13 and r["restored"]["floorPoints"] == 17585, str(r["restored"]))
    check("the floor is never written before it has been read, and never lower",
          r["floorWritesBeforeRead"] == 0 and r["restored"]["floorNeverLower"] and r["restored"]["floorReads"] >= 1,
          str([r["floorWritesBeforeRead"], r["restored"]]))
    check("a floor never brings a missing (reset) account back",
          r["reset"]["local"] == 0 and r["reset"]["floorReads"] == 0 and all(p == 0 for p in r["reset"]["floorWritten"]), str(r["reset"]))
    check("resetting deletes the floor with the account",
          "progress/NOVA-2602__floor" in r.get("deletes", []), str(r.get("deletes")))
    ctx.close()

    # ---- 8g. two devices playing at once: both keep what they earned ----
    # Build 298. "Ensure this PROBLEM is permanently fixed." The merge took
    # the higher of each count, which is right for two copies of one
    # history and wrong for two devices that both moved on from it: one
    # played a 300 XP test while the other played a 200 XP one, and the
    # 200 was gone. Counts that grow by play are base + one tally per
    # device now. Fails on 297 and 298-before-this, which end on 1300.
    print("\n8g. two devices playing at once both keep what they earned")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const clone = o => JSON.parse(JSON.stringify(o));
      const out = {};
      try{
      fbDb = { collection: () => ({ doc: () => ({ set: () => Promise.resolve(), get: () => Promise.resolve({ exists: false }), update: () => Promise.resolve(), delete: () => Promise.resolve() }) }) };
      syncCode = '';
      const hasTally = typeof tallyCapture === 'function';
      const as = id => { if(hasTally) tallyDeviceIdMemo = id; };
      const save = () => { persistLocally(); return clone(store); };
      const load = d => { applyLoadedData(clone(d)); };
      const view = () => ({ points: store.lifetime.points, hundos: store.lifetime.perfectTests, U: (store.unitPerfects || {}).U, week: store.weekPoints });
      /* where both devices start: one account, in step */
      as('devA');
      store.lifetime.points = 1000; store.lifetime.perfectTests = 5; store.unitPerfects = { U: 5 };
      rollWeek(); store.weekPoints = 100; store.lastModified = 1000;
      const X = save();
      /* device A plays a test: 300 XP, two hundos */
      as('devA'); load(X); awardXp(300); store.lifetime.perfectTests += 2; store.unitPerfects.U += 2; store.lastModified = 2000;
      const A = save();
      /* device B, at the same time: 200 XP, one hundo */
      as('devB'); load(X); awardXp(200); store.lifetime.perfectTests += 1; store.unitPerfects.U += 1; store.lastModified = 3000;
      const B = save();
      /* A hears from B */
      as('devA'); load(A); syncSameAccount(clone(B)); out.onA = view(); const AM = clone(store);
      /* B hears from A (its merged copy) */
      as('devB'); load(B); syncSameAccount(clone(AM)); out.onB = view(); const BM = clone(store);
      /* and again: nothing changes, and nothing to push */
      as('devA'); load(AM); const before = JSON.stringify(view()); const g = syncSameAccount(clone(BM));
      out.echo = { same: JSON.stringify(view()) === before, gained: g };
      /* a phone on an old build: it drops the tallies and plays 50 */
      const old = clone(AM); delete old.tally; delete old.tallyBase; old.lifetime.points += 50; old.lastModified = 9000;
      as('devA'); load(AM); syncSameAccount(clone(old)); out.oldBuild = view();
      /* an old build that did not play: nothing is counted twice */
      const old2 = clone(AM); delete old2.tally; delete old2.tallyBase; old2.lastModified = 9500;
      as('devA'); load(AM); syncSameAccount(clone(old2)); out.oldNoPlay = view();
      /* a count raised by hand on the server, loaded by both devices,
         then merged between them: once, not twice */
      const srv = clone(AM); srv.lifetime.points += 18; srv.lastModified = 10000;
      as('devA'); load(srv); store.lastModified = 10001; const SA = save();
      as('devB'); load(srv); store.lastModified = 10002; const SB = save();
      as('devA'); load(SA); syncSameAccount(clone(SB)); out.server = view();
      /* a reset leaves no tallies behind */
      try{ wipeLocalProgressAndSettings(); }catch(e){ try{ resetEverything(); }catch(e2){} }
      out.afterReset = { tally: Object.keys(store.tally || {}).length, points: store.lifetime.points };
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("no error", not r.get("threw"), r.get("threw", ""))
    want = {"points": 1500, "hundos": 8, "U": 8, "week": 600}
    check("a 300 XP test on one device and a 200 XP test on the other are both kept: 1000 + 300 + 200, hundos and the week too",
          r.get("onA") == want, str(r.get("onA")))
    check("and the other device lands on exactly the same", r.get("onB") == want, str(r.get("onB")))
    check("merging again changes nothing and has nothing to push", (r.get("echo") or {}).get("same") and not (r.get("echo") or {}).get("gained"), str(r.get("echo")))
    check("an old build's copy without tallies is read the old way: its 50 counts once, nothing twice",
          (r.get("oldBuild") or {}).get("points") == 1550, str(r.get("oldBuild")))
    check("an old build's copy that did not play changes nothing", (r.get("oldNoPlay") or {}).get("points") == 1500, str(r.get("oldNoPlay")))
    check("a count raised on the server and loaded by both devices is counted once", (r.get("server") or {}).get("points") == 1518, str(r.get("server")))
    check("a reset leaves no tallies behind", (r.get("afterReset") or {}).get("tally") == 0, str(r.get("afterReset")))
    ctx.close()

    # ---- 8h. the board never runs ahead of the account ----
    # Build 313. "I saw the cap account at level 34 earlier today, now
    # it's 33." The row and the account were independent writes: the
    # account waits for this device to have read the server's copy, the
    # row never waited. Rod713's row said 11,075 XP with his account at
    # 9,070 - a phone whose listener never delivered a server snapshot,
    # publishing its numbers while holding its progress. Fails on 312:
    # the row goes out unconfirmed and the progress never does.
    print("\n8h. the board never runs ahead of the account, and a device that cannot confirm keeps asking")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2601');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      const prog = [], rows = [], order = []; let serverReads = 0;
      /* the account on the server: 900 XP, written by the other device */
      const cloud = clone(store); cloud.lifetime.points = 900; cloud.lifetime.correct = 70; cloud.lastModified = Date.now() - 60000;
      if(cloud.tally){ cloud.tally = {}; cloud.tallyBase = {}; }
      fbDb = { collection: name => ({
        onSnapshot: () => () => {},
        doc: id => ({
          /* the listener is stuck: it only ever has the cache */
          onSnapshot: next => { if(name === 'progress' && id === 'NOVA-2601') setTimeout(() => next({ exists: true, metadata: { fromCache: true }, data: () => clone(cloud) }), 50); return () => {}; },
          get: opts => { if(name === 'progress' && id === 'NOVA-2601'){ if(opts && opts.source === 'server') serverReads++;
              return Promise.resolve({ exists: true, metadata: { fromCache: false }, data: () => clone(cloud) }); }
            return Promise.resolve({ exists: false, metadata: { fromCache: false } }); },
          set: d => { if(name === 'progress' && id === 'NOVA-2601'){ prog.push(clone(d)); order.push('account'); }
            if(name === 'leaderboard'){ rows.push(clone(d)); order.push('row'); } return Promise.resolve(); },
          update: () => Promise.resolve(), delete: () => Promise.resolve()
        }) }) };
      /* the launch pull is the one other way in: it is offline here */
      const realPull = pullFromCloud; pullFromCloud = (c, done) => { done && done(false, 'error'); };
      syncCode = 'NOVA-2601'; store.leaderboardOptIn = true;
      if(store.tally){ store.tally = {}; store.tallyBase = {}; }
      store.lifetime.points = 1200; store.lifetime.correct = 95; store.lastModified = Date.now();
      cloudConfirmedFor = ''; cloudPushPending = false;
      try{ confirmRetryMs = 4000; clearTimeout(confirmRetryTimer); confirmRetryTimer = null; }catch(e){}
      attachLiveListener('NOVA-2601');
      await wait(400);
      /* this device finishes a test: it saves and publishes */
      saveStore(); try{ publishNow(); }catch(e){} try{ flushLeaderboardRow(); }catch(e){}
      await wait(600);
      const out = { rowsBefore: rows.map(r => r.xp), progBefore: prog.length };
      await wait(9000);
      const lastP = prog[prog.length - 1], lastR = rows[rows.length - 1];
      out.serverReads = serverReads;
      out.prog = lastP ? lastP.lifetime.points : null;
      out.row = lastR ? lastR.xp : null;
      out.rowLevel = lastR ? lastR.level : null;
      out.rowsUnder = rows.filter(r => (r.xp || 0) < 1200).length;
      out.accountFirst = order.indexOf('account') >= 0 && order.indexOf('account') < order.indexOf('row');
      pullFromCloud = realPull;
      return out; }""")
    check("an unconfirmed device publishes nothing to the board, however it finishes",
          r["rowsBefore"] == [] and r["progBefore"] == 0, str([r["rowsBefore"], r["progBefore"]]))
    check("with the listener stuck on its cache, the device asks the server itself, and its progress lands",
          r["serverReads"] >= 1 and r["prog"] == 1200, str([r["serverReads"], r["prog"]]))
    check("then the board gets the saved number - after the account has it, never before",
          r["row"] == 1200 and r["rowsUnder"] == 0 and r["accountFirst"], str([r["row"], r["rowLevel"], r["rowsUnder"], r["accountFirst"]]))
    ctx.close()

    # ---- 8i. answering spends a write a minute, not a write pair per question ----
    # Build 312.1. On Oct 5 the class used up Firestore's free 20,000
    # writes at 21:58 UTC and every save from every phone failed until
    # midnight Pacific. Each answer pushed the account and its
    # high-water mark 2.5s later. Fails on 312: 22 writes for ten answers.
    print("\n8i. answering spends a write a minute, not two per question; leaving saves everything at once")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2601');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      const acct = [], floor = [];
      fbDb = { collection: name => ({ onSnapshot: () => () => {},
        doc: id => ({ onSnapshot: () => () => {}, get: () => Promise.resolve({ exists: false, metadata: { fromCache: false } }),
          set: d => { if(name === 'progress' && id === 'NOVA-2601') acct.push(clone(d)); if(name === 'progress' && id === 'NOVA-2601__floor') floor.push(clone(d)); return Promise.resolve(); },
          update: () => Promise.resolve(), delete: () => Promise.resolve() }) }) };
      syncCode = 'NOVA-2601'; cloudConfirmedFor = 'NOVA-2601'; floorMergedFor = 'NOVA-2601';
      try{ clearTimeout(cloudPushTimer); cloudPushTimer = null; }catch(e){}
      /* ten answers, one every three seconds */
      for(let i = 0; i < 10; i++){ store.lifetime.correct += 1; saveStore(); await wait(3000); }
      const during = { acct: acct.length, floor: floor.length };
      /* then the app goes to the background */
      store.lifetime.correct += 1; saveStore(); publishNow();
      await wait(300);
      const want = store.lifetime.correct, la = acct[acct.length - 1], lf = floor[floor.length - 1];
      return { during, acctLast: la && la.lifetime.correct, floorLast: lf && lf.lifetime.correct, want }; }""")
    check("ten answers in thirty seconds write the account at most twice and its high-water mark at most once",
          r["during"]["acct"] <= 2 and r["during"]["floor"] <= 1, str(r["during"]))
    check("leaving the app puts the latest progress in both, at once",
          r["acctLast"] == r["want"] and r["floorLast"] == r["want"], str([r["acctLast"], r["floorLast"], r["want"]]))
    ctx.close()

    # ---- 8j. a weekly win that never happened stays gone ----
    # Build 312.3. OdinSavior's phone settled the week of 21 Sep as a win on
    # a build before 248 (it trusted the rank it last saw; Sauce passed
    # him later that night), so he held Zeus. weeklyWins merges by taking
    # the higher side, so zeroing the cloud copy alone comes straight back
    # from any copy still holding the 1. Fails on 312.2: nothing voids it.
    print("\n8j. a weekly win that never happened stays gone; a real one still counts")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""()=>{
      const clone = o => JSON.parse(JSON.stringify(o));
      const zeus = AVATAR_CHARACTERS.find(c => c.feat === 'weektop');
      const solar = AVATAR_CHARACTERS.find(c => c.id === 'solar');
      const odin = clone(store);
      odin.publicId = 'kdxnp7smgcre'; odin.weeklyWins = 1; odin.avatarChar = zeus.id;
      odin.pendingCharUnlocks = [zeus.id]; odin.weekWinWeeks = [];
      applyLoadedData(clone(odin));
      const load = { ww: store.weeklyWins, char: store.avatarChar, locked: isLockedCharacter(zeus.id),
                     pend: (store.pendingCharUnlocks || []).indexOf(zeus.id) };
      saveStore = () => {}; scheduleCloudPush = () => {}; persistLocally = () => {};
      const stale = clone(odin); stale.lastModified = Date.now() + 99999;
      syncSameAccount(stale);
      const newer = { ww: store.weeklyWins, char: store.avatarChar };
      stale.lastModified = 1; syncSameAccount(stale);
      const older = { ww: store.weeklyWins, char: store.avatarChar };
      const keep = finalRankForWeek; finalRankForWeek = () => 1;
      store.weekRankSeen = { week: lastWeekKey(), rank: 1 }; settleWeeklyWin();
      finalRankForWeek = keep;
      applyLoadedData(clone(store));
      const real = { ww: store.weeklyWins, locked: isLockedCharacter(zeus.id) };
      const sauce = clone(odin); sauce.publicId = 'ew7hyxpg5j2y';
      applyLoadedData(sauce);
      const other = { ww: store.weeklyWins, char: store.avatarChar };
      return { load, newer, older, real, other, zeus: zeus.id, solar: !!solar }; }""")
    check("the voided win is gone on load, Zeus locks, and he is put in another character he holds",
          r["load"]["ww"] == 0 and r["load"]["locked"] and r["load"]["char"] not in (r["zeus"], None) and r["load"]["pend"] < 0, str(r["load"]))
    check("a stale copy still holding the win cannot bring it back, newer or older",
          r["newer"]["ww"] == 0 and r["older"]["ww"] == 0 and r["newer"]["char"] != r["zeus"] and r["older"]["char"] != r["zeus"],
          str([r["newer"], r["older"]]))
    check("a week he really wins still counts and unlocks Zeus", r["real"]["ww"] == 1 and not r["real"]["locked"], str(r["real"]))
    check("an account the void does not name keeps its win and its Zeus", r["other"]["ww"] == 1 and r["other"]["char"] == r["zeus"], str(r["other"]))
    ctx.close()

    # ---- 8k. a device with a stale view of the account cannot write over it ----
    # Build 315. Overnight on Oct 6-7 two accounts lost progress to phones
    # on current builds. Rogelio's phone saved on the evening of Oct 5 and
    # was put away before the write left it; Firestore sent it when the app
    # woke the next night, over the 2,590 XP his other phone had played
    # since - the account and its high-water mark both. Alfred's phone had
    # last heard from the server before his Oct 6 test, played a session on
    # top of that copy and wrote it up, and the test and three hundos were
    # gone. A launch read the server once and trusted it all session; every
    # account write is a transaction now. The stand-in server here keeps
    # versions, holds writes made offline and sends them when the network
    # returns (as Firestore does), and commits a transaction only if what it
    # read is unchanged. Fails on 313 and on 315 before this.
    print("\n8k. a device with a stale view of the account cannot write over it")
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');"
                        "localStorage.setItem('class26e.synccode','NOVA-2611');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      const out = {};
      try{
      const S = {}, V = {}, queued = []; let online = true, beforeCommit = null, txRuns = 0;
      const put = (k, d) => { S[k] = clone(d); V[k] = (V[k] || 0) + 1; };
      const snapOf = k => ({ exists: k in S, metadata: { fromCache: false }, data: () => clone(S[k]) });
      const ref = k => ({ _k: k,
        get: () => online ? Promise.resolve(snapOf(k)) : Promise.reject(new Error('unavailable')),
        set: (d, o) => { const n = (o && o.merge) ? Object.assign(clone(S[k] || {}), clone(d)) : clone(d);
                         if(online) put(k, n); else queued.push([k, n]); return Promise.resolve(); },
        update: d => { const n = Object.assign(clone(S[k] || {}), clone(d)); if(online) put(k, n); else queued.push([k, n]); return Promise.resolve(); },
        delete: () => { delete S[k]; V[k] = (V[k] || 0) + 1; return Promise.resolve(); },
        /* the listener has gone quiet */
        onSnapshot: () => () => {} });
      fbDb = {
        collection: name => ({ onSnapshot: () => () => {}, doc: id => ref(name + '/' + id) }),
        runTransaction: async fn => {
          for(let i = 0; i < 5; i++){
            if(!online) throw new Error('unavailable');
            txRuns++;
            const read = {}, writes = [];
            const tx = { get: r => { read[r._k] = V[r._k] || 0; return Promise.resolve(snapOf(r._k)); },
                         set: (r, d) => { writes.push([r._k, clone(d)]); return tx; },
                         update: (r, d) => { writes.push([r._k, Object.assign(clone(S[r._k] || {}), clone(d))]); return tx; } };
            const res = await fn(tx);
            if(beforeCommit){ const f = beforeCommit; beforeCommit = null; f(); }
            if(Object.keys(read).every(k => (V[k] || 0) === read[k])){ writes.forEach(([k, d]) => put(k, d)); return res; }
          }
          throw new Error('aborted');
        } };
      /* a device id per phone (build 298's tallies), and copies built the
         way the app builds them; no account is live while they are made */
      const as = id => { tallyDeviceIdMemo = id; };
      const quiet = () => { syncCode = ''; cloudConfirmedFor = ''; try{ clearTimeout(cloudPushTimer); cloudPushTimer = null; clearTimeout(confirmRetryTimer); confirmRetryTimer = null; }catch(e){} };
      const load = d => { applyLoadedData(clone(d)); };
      const save = () => { persistLocally(); return clone(store); };
      /* each scenario is its own account: nothing carries over, tallies least of all */
      const fresh = () => { quiet(); store.tally = {}; store.tallyBase = {}; store.unitPerfects = {}; store.testHistory = []; store.studyLog = {};
        store.weeklyWins = 0; Object.keys(store.lifetime || {}).forEach(k => { store.lifetime[k] = 0; }); };
      /* this phone, confirmed against the server long ago this session */
      const confirmedLongAgo = code => {
        syncCode = code; cloudConfirmedFor = code; floorMergedFor = code; lastPushCode = code; lastCloudPushAt = 0; lastFloorPushAt = 0;
        try{ accountWriteAt = 0; accountWriteNext = null; accountWriteFails = 0; }catch(e){}
        try{ clearTimeout(cloudPushTimer); cloudPushTimer = null; clearTimeout(confirmRetryTimer); confirmRetryTimer = null; confirmRetryMs = 4000; }catch(e){}
      };
      const view = k => { const d = S[k] || {}; return { points: (d.lifetime || {}).points, full: (d.lifetime || {}).fullTests,
        tcole: (d.unitPerfects || {})['TCOLE Rules'] || 0, hist: (d.testHistory || []).length, ww: d.weeklyWins }; };
      store.leaderboardOptIn = false;

      /* A. Alfred: the listener went quiet before the other phone's test */
      fresh();
      as('phoneA'); load(store);
      store.lifetime.points = 30000; store.lifetime.correct = 2000; store.lifetime.answered = 2200; store.lifetime.fullTests = 9;
      store.unitPerfects = { 'Racial Profiling': 5, 'TCOLE Rules': 0 }; store.testHistory = []; store.weeklyWins = 0;
      store.lastModified = Date.now() - 86400000;
      const X = save();
      put('progress/NOVA-2611', X); put('progress/NOVA-2611__floor', X);
      /* the other phone plays a full test overnight: a hundo, 1,640 XP */
      as('phoneA'); load(X); awardXp(1640); store.lifetime.fullTests += 1; store.unitPerfects['TCOLE Rules'] = 1;
      store.testHistory = [{ playedAt: Date.now() - 3600000, label: 'TCOLE Rules', pct: 100 }]; store.lastModified = Date.now() - 3600000;
      const A = save(); quiet();
      put('progress/NOVA-2611', A); put('progress/NOVA-2611__floor', A);
      /* this phone still holds X, plays 2,345 XP on top of it, and leaves */
      as('phoneB'); load(X); awardXp(2345); store.lifetime.correct += 240; store.lifetime.answered += 250;
      quiet(); confirmedLongAgo('NOVA-2611');
      saveStore(); publishNow();
      await wait(900);
      out.A = { acct: view('progress/NOVA-2611'), floor: view('progress/NOVA-2611__floor'),
                local: { points: store.lifetime.points, tcole: (store.unitPerfects || {})['TCOLE Rules'] || 0, full: store.lifetime.fullTests } };

      /* B. Rogelio: a save made offline, sent when the phone wakes a day later */
      fresh();
      as('phoneR1'); store.lifetime.points = 20000; store.lifetime.correct = 1400; store.lifetime.fullTests = 8;
      store.unitPerfects = { 'Racial Profiling': 2 }; store.testHistory = []; store.lastModified = Date.now() - 172800000;
      const X2 = save();
      put('progress/NOVA-2612', X2); put('progress/NOVA-2612__floor', X2);
      as('phoneR2'); load(X2); awardXp(2590); store.lifetime.correct += 142; store.lastModified = Date.now() - 7200000;
      const R2 = save(); quiet();
      as('phoneR1'); load(X2);
      confirmedLongAgo('NOVA-2612');
      online = false;
      store.seenProfileTour = !store.seenProfileTour; saveStore(); publishNow();
      await wait(500);
      /* while it sleeps, the other phone plays 2,590 XP into the account */
      put('progress/NOVA-2612', R2); put('progress/NOVA-2612__floor', R2);
      /* and the network comes back */
      online = true; queued.splice(0).forEach(([k, d]) => put(k, d));
      window.dispatchEvent(new Event('online'));
      await wait(10000);
      out.B = { acct: view('progress/NOVA-2612'), floor: view('progress/NOVA-2612__floor'), local: store.lifetime.points };

      /* C. the other phone's write lands between this one's read and its commit */
      fresh(); txRuns = 0;
      as('phoneC1'); store.lifetime.points = 10000; store.unitPerfects = {}; store.testHistory = []; store.lastModified = Date.now() - 86400000;
      const X3 = save();
      as('phoneC2'); load(X3); awardXp(700); store.lastModified = Date.now() - 1000; const C2 = save();
      as('phoneC1'); load(X3); awardXp(500); quiet();
      put('progress/NOVA-2613', X3);
      confirmedLongAgo('NOVA-2613');
      beforeCommit = () => put('progress/NOVA-2613', C2);
      pushToCloud();
      await wait(900);
      out.C = { acct: view('progress/NOVA-2613'), txRuns, local: store.lifetime.points };

      /* D. the server holds nothing new: this phone's copy goes up as it is */
      fresh();
      as('phoneD'); store.lifetime.points = 5000; store.weeklyWins = 1; store.lastModified = Date.now() - 86400000;
      const X4 = save(); put('progress/NOVA-2614', X4);
      load(X4); store.weeklyWins = 0; quiet(); confirmedLongAgo('NOVA-2614');
      saveStore(); pushToCloud();
      await wait(900);
      out.D = view('progress/NOVA-2614');
      } catch(e){ out.threw = String(e && e.stack || e); }
      return out; }""")
    check("no error", not r.get("threw"), r.get("threw", ""))
    A = r.get("A") or {}
    check("a phone whose listener went quiet keeps what the other phone played: the test, its hundo, and both phones' XP",
          (A.get("acct") or {}).get("points") == 33985 and (A.get("acct") or {}).get("full") == 10 and (A.get("acct") or {}).get("tcole") == 1,
          str(A.get("acct")))
    check("and the high-water mark holds the same", (A.get("floor") or {}).get("points") == 33985 and (A.get("floor") or {}).get("tcole") == 1,
          str(A.get("floor")))
    check("and the phone that wrote it catches up", (A.get("local") or {}).get("points") == 33985 and (A.get("local") or {}).get("tcole") == 1,
          str(A.get("local")))
    B = r.get("B") or {}
    check("a save made offline and sent when the phone wakes cannot land over what was played since - account and high-water mark",
          (B.get("acct") or {}).get("points") == 22590 and (B.get("floor") or {}).get("points") == 22590 and B.get("local") == 22590, str(B))
    C = r.get("C") or {}
    check("a write that lands between this phone's read and its commit is kept, not written over",
          (C.get("acct") or {}).get("points") == 11200 and (C.get("txRuns") or 0) >= 2, str(C))
    check("where the server holds nothing new, this phone's copy goes up as it is", (r.get("D") or {}).get("ww") == 0, str(r.get("D")))
    ctx.close()

    # ==== BUILD 322: ACCOUNTS ====
    # "We need to really crack down on the leaderboard accuracy and crack
    # down on people's progress randomly going away or people somehow
    # using two accounts. People who are signing up, could we make it
    # where it asks you to sign in first and then you have to hit I'm new
    # here sign up or something?" Every check below fails on 6a387e2.
    FLAGS = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
             "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
             "localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');")
    def booted(extra=""):
        c = br.new_context(viewport={"width": 440, "height": 956})
        c.add_init_script("try{" + FLAGS + extra + "}catch(e){}")
        p = page(c); p.goto(URL); p.wait_for_timeout(2600)
        p.evaluate("()=>document.getElementById('splashscreen')?.remove()")
        p.wait_for_timeout(300)
        return c, p

    # ---- 9a. sign in first ----
    print("\n9a. Welcome leads with Sign in; I'm new here is the second choice")
    ctx, pg = booted()
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const out = {};
      const btns = () => [...document.querySelectorAll('[data-screen="welcome"] .cosmic-welcome-actions button')];
      const b = btns();
      out.labels = b.map(x => x.textContent);
      out.primary = !!(b[0] && b[0].classList.contains('playbtn'));
      out.ghost = !!(b[1] && b[1].classList.contains('ghost'));
      out.hint = (document.querySelector('.cosmic-welcome-hint') || {}).textContent || '';
      if(b[0]) b[0].click(); await wait(300);
      out.firstOpens = document.querySelector('.synccode-entry-panel') ? 'code' : document.querySelector('.releasenotes-panel') ? 'whatsnew' : 'other';
      showWelcome(); await wait(200);
      const b2 = btns(); if(b2[1]) b2[1].click(); await wait(300);
      out.secondOpens = document.querySelector('.signupcheck-panel') ? 'check' : document.querySelector('.releasenotes-panel') ? 'whatsnew'
                      : document.querySelector('.synccode-entry-panel') ? 'code' : 'other';
      return out; }""")
    check("the first, primary button on Welcome is Sign in, and it opens the code screen",
          r["primary"] and r["labels"] and r["labels"][0].strip().lower() == "sign in" and r["firstOpens"] == "code", str(r))
    check("the second is I'm new here, and it opens a check, not sign-up",
          r["ghost"] and len(r["labels"]) > 1 and "new here" in r["labels"][1].lower() and r["secondOpens"] == "check", str(r))
    ctx.close()

    # ---- 9b. the confirm step ----
    print("\n9b. sign-up opens with a plain check: used Nova before? sign in instead")
    ctx, pg = booted()
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const out = {};
      try{
        showSignUpCheck(); await wait(300);
        const p = document.querySelector('.signupcheck-panel');
        out.text = p ? p.innerText.replace(/\\s+/g, ' ') : '';
        const si = p && p.querySelector('.signupcheck-signin'), go = p && p.querySelector('.signupcheck-go');
        out.signin = si ? si.textContent : null; out.go = go ? go.textContent : null;
        out.goFloor = !!(go && go.classList.contains('playbtn'));
        si.click(); await wait(300);
        out.signinOpens = !!document.querySelector('.synccode-entry-panel');
        showSignUpCheck(); await wait(300);
        document.querySelector('.signupcheck-go').click(); await wait(400);
        out.goOpens = !!document.querySelector('.releasenotes-panel');
        document.querySelector('.releasenotes-panel .back-link').click(); await wait(300);
        out.backTo = !!document.querySelector('.signupcheck-panel');
        /* and a device with nothing on it signs up exactly as before */
        store.firstName = 'Newbie'; store.avatarChar = AVATAR_CHARACTERS[0].id;
        finishWelcomeStartFresh(); await wait(500);
        out.minted = !!syncCode && !!document.querySelector('.codereveal-value');
      }catch(e){ out.err = String(e); }
      return out; }""")
    check("it asks whether you have used Nova before, says a second account will not carry progress, and offers both ways",
          not r.get("err") and "Have you used Nova before" in r.get("text", "") and "second account" in r.get("text", "")
          and r.get("signin") == "Sign in instead" and r.get("go") == "I’m new, continue" and r.get("goFloor"), str(r))
    check("Sign in instead opens the code screen; I'm new, continue goes on to sign-up, whose Back returns here",
          r.get("signinOpens") and r.get("goOpens") and r.get("backTo"), str(r))
    check("a device with no account on it still signs up as before", bool(r.get("minted")), str(r))
    ctx.close()

    # ---- 9c. a name already on the board ----
    print("\n9c. a username already on the board is asked about once, with nothing else said")
    ctx, pg = booted()
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const out = {};
      try{
        leaderboardRows = [{ pub: 'mdgaaaaaaaaa', firstName: 'Mad Dog', level: 31, badges: 6, xp: 12345, hundos: 7, correct: 900 },
                           { pub: 'smbbbbbbbbbb', firstName: 'Sam', level: 4 }];
        boardFetchedAt = Date.now();
        const type = v => { const i = document.querySelector('.onboarding-shortform-panel .searchbox'); i.value = v; i.dispatchEvent(new Event('input')); };
        const go = () => [...document.querySelectorAll('.onboarding-shortform-panel > .playbtn')].pop();
        showWelcomeNamePrompt(); await wait(150);
        type(' MADdog '); go().click(); await wait(250);
        const card = document.querySelector('.namecheck-card');
        out.stopped = !document.querySelector('.charselect-panel');
        out.shown = !!(card && getComputedStyle(card).display !== 'none');
        out.text = card ? card.innerText.replace(/\\s+/g, ' ') : '';
        out.btn = go() ? go().textContent : '';
        out.signIn = !!(card && card.querySelector('.namecheck-signin'));
        go().click(); await wait(250);
        out.onAfter = !!document.querySelector('.charselect-panel'); out.name = store.firstName;
        showWelcomeNamePrompt(); await wait(150);
        type('Riley'); go().click(); await wait(250);
        out.newName = !!document.querySelector('.charselect-panel');
        showWelcomeNamePrompt(); await wait(150);
        type('mad dog'); go().click(); await wait(250);
        document.querySelector('.namecheck-signin').click(); await wait(250);
        out.signInOpens = !!document.querySelector('.synccode-entry-panel');
      }catch(e){ out.err = String(e); }
      return out; }""")
    check("a name already on the board, in any case and spacing, is stopped once with the warning and Sign in",
          not r.get("err") and r.get("stopped") and r.get("shown") and r.get("signIn")
          and "Someone named Mad Dog already has an account. If that’s you, sign in with your code." in r.get("text", "")
          and r.get("btn") == "It’s not me, continue", str(r))
    check("the warning names the name and nothing else about that account",
          r.get("shown") and not re.search(r"\d", r.get("text", "")) and "Level" not in r.get("text", ""), r.get("text", ""))
    check("It's not me, continue goes on; a name nobody has is never stopped; Sign in opens the code screen",
          r.get("onAfter") and r.get("newName") and r.get("signInOpens"), str(r))
    ctx.close()

    # ---- 9d. an account still on the device comes before sign-up ----
    print("\n9d. a device that still holds an account is offered it back, and cannot quietly make a second")
    MID = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":false,"leaderboardOptIn":true,'
           '"lastModified":1700000000000,"lifetime":{"points":0,"correct":0}}')
    # (1) a sign-up closed on the code screen: the code and the name are here, Home never came
    ctx, pg = booted("localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.synccode','NOVA-4401');" % MID)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const out = {};
      const b = [...document.querySelectorAll('[data-screen="welcome"] .cosmic-welcome-actions button')];
      out.labels = b.map(x => x.textContent);
      try{
        finishWelcomeStartFresh(); await wait(400);
        out.afterSilent = { code: syncCode, reveal: !!document.querySelector('.codereveal-value'),
                            welcome: !!document.querySelector('[data-screen="welcome"]') };
        const c = document.querySelector('[data-screen="welcome"] .cosmic-welcome-actions .playbtn');
        if(c) c.click(); await wait(600);
        out.after = { code: syncCode, home: !!document.querySelector('.panel.home.screen-home-actual'), done: store.onboardingComplete };
      }catch(e){ out.err = String(e); }
      return out; }""")
    check("a sign-up that stopped before Home is offered back: Continue as Madison",
          r["labels"] and r["labels"][0] == "Continue as Madison", str(r.get("labels")))
    check("and sign-up cannot make a second account over it without asking: no new code, back to Welcome",
          not r.get("err") and (r.get("afterSilent") or {}).get("code") == "NOVA-4401" and not (r.get("afterSilent") or {}).get("reveal")
          and (r.get("afterSilent") or {}).get("welcome"), str(r.get("afterSilent")) + str(r.get("err", "")))
    check("Continue finishes the sign-up it belongs to: Home, the same code",
          (r.get("after") or {}).get("code") == "NOVA-4401" and (r.get("after") or {}).get("home") and (r.get("after") or {}).get("done"),
          str(r.get("after")))
    ctx.close()
    # (2) localStorage gone, the mirror kept the code (offline: the boot recovery cannot pull)
    ctx, pg = booted()
    pg.evaluate("""async ()=>{ idbSaveCode('NOVA-4402');
      await new Promise(res => setTimeout(res, 300));
      await idbOpen().then(db => new Promise(res => { const tx = db.transaction(IDB_STORE, 'readwrite'); tx.objectStore(IDB_STORE).delete(IDB_KEY); tx.oncomplete = res; tx.onerror = res; }));
      localStorage.removeItem('class26e.drill.v1'); localStorage.removeItem('class26e.synccode'); }""")
    pg.reload(); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.wait_for_timeout(500)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const out = {};
      try{
        const b = [...document.querySelectorAll('[data-screen="welcome"] .cosmic-welcome-actions button')];
        out.labels = b.map(x => x.textContent);
        showSignUpCheck(); await wait(400);
        out.check = (document.querySelector('.signupcheck-panel') || {}).innerText || '';
        store.firstName = 'Second'; store.avatarChar = AVATAR_CHARACTERS[0].id;
        finishWelcomeStartFresh(); await wait(400);
        out.minted = syncCode; out.mirror = await idbLoadCode();
        /* the network comes back: Continue puts the account back */
        __fake([]);
        __cloud['NOVA-4402'] = { firstName: 'Madison', avatarChar: 'ninja', onboardingComplete: true, leaderboardOptIn: true,
                                 lastModified: Date.now(), lifetime: { points: 4200, correct: 300 } };
        showWelcome(); await wait(400);
        const c = document.querySelector('[data-screen="welcome"] .cosmic-welcome-actions .playbtn');
        out.label2 = c ? c.textContent : null;
        if(c) c.click(); await wait(600);
        out.after = { code: syncCode, home: !!document.querySelector('.panel.home.screen-home-actual'), points: store.lifetime.points, name: store.firstName };
      }catch(e){ out.err = String(e); }
      return out; }""")
    check("the code in the mirror alone is enough: Welcome offers the account first",
          r.get("labels") and "Continue" in r["labels"][0] and "This device still has" in r.get("check", ""), str([r.get("labels"), r.get("check")]))
    check("and nothing mints a second account over it", not r.get("err") and not r.get("minted") and r.get("mirror") == "NOVA-4402",
          str([r.get("minted"), r.get("mirror"), r.get("err")]))
    check("Continue brings it back under the same code, on Home",
          (r.get("after") or {}).get("code") == "NOVA-4402" and (r.get("after") or {}).get("home") and (r.get("after") or {}).get("points") == 4200,
          str(r.get("after")))
    ctx.close()
    # (3) the code survived and the store did not; the cloud has the account
    ctx, pg = booted("localStorage.setItem('class26e.synccode','NOVA-4403');")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      __fake([]);
      __cloud['NOVA-4403'] = { firstName: 'Madison', avatarChar: 'ninja', onboardingComplete: true, leaderboardOptIn: true,
                               lastModified: Date.now(), lifetime: { points: 5000, correct: 400 } };
      __ready(); await wait(900);
      return { code: syncCode, home: !!document.querySelector('.panel.home.screen-home-actual'),
               welcome: !!document.querySelector('[data-screen="welcome"]'), points: store.lifetime.points }; }""")
    check("a code with no progress beside it, whose account comes down at launch, lands on Home - not on Welcome over it",
          r["code"] == "NOVA-4403" and r["home"] and not r["welcome"] and r["points"] == 5000, str(r))
    ctx.close()
    # (4) the mirror's pull is still out when the device takes another account
    ctx, pg = booted()
    pg.evaluate("""async ()=>{ idbSaveCode('NOVA-4404');
      await new Promise(res => setTimeout(res, 300));
      await idbOpen().then(db => new Promise(res => { const tx = db.transaction(IDB_STORE, 'readwrite'); tx.objectStore(IDB_STORE).delete(IDB_KEY); tx.oncomplete = res; tx.onerror = res; }));
      localStorage.removeItem('class26e.drill.v1'); localStorage.removeItem('class26e.synccode'); }""")
    pg.reload(); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const other = { firstName: 'Other person', avatarChar: 'ninja', onboardingComplete: true, lastModified: Date.now(),
                      lifetime: { points: 7777, correct: 500 } };
      const snap = d => ({ exists: !!d, metadata: { fromCache: false }, data: () => JSON.parse(JSON.stringify(d)) });
      const ref = (name, id) => ({ get: () => new Promise(res => setTimeout(() => res(snap(name === 'progress' && id === 'NOVA-4404' ? other : null)), 400)),
                                   set: () => Promise.resolve(), update: () => Promise.resolve(), delete: () => Promise.resolve(),
                                   onSnapshot: () => () => {} });
      fbDb = { collection: name => ({ doc: id => ref(name, id), onSnapshot: () => () => {}, get: () => Promise.resolve({ forEach(){} }) }) };
      __ready();                      /* boot's mirror recovery sends its read */
      await wait(60);
      setSyncCode('NOVA-4499');       /* and a sign-in lands while it is out */
      store.firstName = 'Newbie'; store.lifetime.points = 10;
      await wait(900);
      return { code: syncCode, points: store.lifetime.points, name: store.firstName }; }""")
    check("a recovery read still out when the device takes another account neither switches the code nor pours one account into the other",
          r["code"] == "NOVA-4499" and r["points"] == 10 and r["name"] == "Newbie", str(r))
    ctx.close()

    # ---- 9e. the board's numbers are Profile's ----
    print("\n9e. your row on the board says what Profile says")
    FLOORED = STORE.replace('"onboardingComplete":true,', '"onboardingComplete":true,"rankFloor":3,"tourRev":99,')
    ctx, pg = booted("localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.synccode','NOVA-4501');" % FLOORED)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const out = {};
      try{
        const pub = publicIdOf();
        /* what this device last PUBLISHED, before the test it just finished */
        __fake([{ id: pub, firstName: 'Madison', avatarChar: 'ninja', level: 1, badges: 0, hundos: 2, xp: 100, correct: 10 }]);
        store.lifetime.points += 777; store.lifetime.correct += 50;
        const row = buildLeaderboardRow();
        out.profileRank = rankOf(store) ? RANK_DISPLAY_NAME[rankOf(store)] : null;
        out.rowRank = (typeof rankOfEntry === 'function') ? (rankOfEntry(row) ? RANK_DISPLAY_NAME[rankOfEntry(row)] : null) : 'n/a';
        out.rowNums = { level: row.level === levelOf(store), badges: row.badges === badgeCountOf(store), hundos: row.hundos === hundosOf(store),
                        xp: row.xp === store.lifetime.points, floor: row.rankFloor === store.rankFloor };
        showRankings('overall'); await wait(600);
        const me = document.querySelector('[data-me="1"]');
        out.boardRank = me ? ((me.querySelector('.rank-col-rankname') || {}).textContent || '—') : null;
        if(me) me.click(); await wait(500);
        const cells = {};
        document.querySelectorAll('.person-card-cell').forEach(c => {
          cells[(c.querySelector('.person-card-cell-label') || {}).textContent] = (c.querySelector('.person-card-cell-value') || {}).textContent; });
        out.cardRank = (document.querySelector('.person-card-rank') || {}).textContent || null;
        out.card = cells;
        out.want = { xp: store.lifetime.points.toLocaleString(), correct: store.lifetime.correct.toLocaleString() };
      }catch(e){ out.err = String(e); }
      return out; }""")
    check("the row carries Profile's rank (its floor included) and the board and your card show it",
          not r.get("err") and r.get("profileRank") and r.get("rowRank") == r.get("profileRank")
          and r.get("boardRank") == r.get("profileRank") and r.get("cardRank") == r.get("profileRank")
          and all((r.get("rowNums") or {}).values()), str(r))
    check("your own card on the board shows the XP and right answers Profile and Stats do, not the last ones published",
          (r.get("card") or {}).get("XP") == (r.get("want") or {}).get("xp")
          and (r.get("card") or {}).get("Correct answers") == (r.get("want") or {}).get("correct"), str([r.get("card"), r.get("want")]))
    ctx.close()

    # ---- 9f. a stale device cannot take the row backwards ----
    print("\n9f. a device behind the account cannot publish its older numbers over the row")
    ctx, pg = booted("localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.synccode','NOVA-4601');" % STORE)
    r = pg.evaluate("""async ()=>{
      const wait = ms => new Promise(res => setTimeout(res, ms));
      const clone = o => JSON.parse(JSON.stringify(o));
      const out = {};
      try{
        const S = {}, rows = []; let serverReads = 0;
        /* the launch's own pull must not do the catching up here: the
           Firebase retry would drain it the moment fbDb is set */
        fbReadyDrained = true; fbReadyCallbacks.length = 0;
        const snapOf = k => ({ exists: k in S, metadata: { fromCache: false }, data: () => clone(S[k]) });
        const ref = k => ({ _k: k,
          get: o => { if(o && o.source === 'server' && k.indexOf('progress/') === 0) serverReads++; return Promise.resolve(snapOf(k)); },
          set: d => { S[k] = clone(d); if(k.indexOf('leaderboard/') === 0) rows.push(clone(d)); return Promise.resolve(); },
          update: () => Promise.resolve(), delete: () => { delete S[k]; return Promise.resolve(); },
          onSnapshot: () => () => {} });
        fbDb = { collection: name => ({ onSnapshot: () => () => {}, doc: id => ref(name + '/' + id) }),
          runTransaction: async fn => { const w = [];
            const tx = { get: r => Promise.resolve(snapOf(r._k)), set: (r, d) => { w.push([r, d]); return tx; } };
            const res = await fn(tx); w.forEach(([r, d]) => r.set(d)); return res; } };
        const run = async (code, acct, row) => {
          syncCode = ''; cloudConfirmedFor = '';
          try{ clearTimeout(cloudPushTimer); cloudPushTimer = null; clearTimeout(confirmRetryTimer); confirmRetryTimer = null; clearTimeout(rowPushTimer); rowPushTimer = null; }catch(e){}
          store.tally = {}; store.tallyBase = {}; store.publicId = 'rowtest' + code.slice(-4) + 'ab';
          store.leaderboardOptIn = true; store.lifetime.points = 1200; store.lifetime.correct = 95; store.lastModified = Date.now() - 86400000;
          persistLocally();
          const cloud = clone(store); cloud.lifetime.points = acct; cloud.lifetime.correct = 95 + (acct - 1200) / 10; cloud.lastModified = Date.now() - 3600000;
          S['progress/' + code] = cloud;
          S['leaderboard/' + store.publicId] = { firstName: 'Madison', xp: row, correct: 95 + (row - 1200) / 10, hundos: 2, level: 9 };
          rows.length = 0; serverReads = 0;
          /* this phone read the server at launch, long ago; its listener has gone quiet since */
          syncCode = code; cloudConfirmedFor = code; floorMergedFor = code; lastPushCode = code; lastCloudPushAt = 0; lastFloorPushAt = 0;
          try{ accountWriteAt = 0; accountWriteNext = null; accountWriteFails = 0; lastRowSig = null; lastRowUrgentSig = null; confirmRetryMs = 200; }catch(e){}
          /* and it is put away */
          publishNow();
          await wait(4500);
          return { rows: rows.map(x => x.xp), reads: serverReads, local: store.lifetime.points };
        };
        /* A: the other phone played 300 XP into the account and its row */
        out.A = await run('NOVA-4601', 1500, 1500);
        /* B: a row ahead of its own account (an old build wrote it): one re-read, then the account's number */
        out.B = await run('NOVA-4602', 1200, 2000);
      }catch(e){ out.err = String(e && e.stack || e); }
      return out; }""")
    A = r.get("A") or {}
    check("a phone behind the account never writes its older numbers over the row; it reads the account and the row follows the merge",
          not r.get("err") and A.get("rows") and min(A["rows"]) >= 1500 and A.get("reads", 0) >= 1 and A.get("local") == 1500,
          str(r.get("err") or A))
    B = r.get("B") or {}
    check("a row ahead of its own account is not obeyed for ever: the account is read again, then its number goes up",
          B.get("reads", 0) >= 1 and B.get("rows") == [1200], str(B))
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
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)
    pg = page(ctx); pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    r = pg.evaluate("""async ()=>{
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
      /* build 296: a session pushes only once the server's copy has been
         read; this section is about WHAT is published, so it starts from
         a confirmed session */
      if(typeof markCloudConfirmed === 'function') markCloudConfirmed(false);
      pushToCloud();
      /* build 315: the row goes once the account write has landed */
      await new Promise(res => setTimeout(res, 400));
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
