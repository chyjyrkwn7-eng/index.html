"""Does re-adding to the Home Screen still lose your account?

Every check here is written against the reported failure: a person
followed the re-add notice, removed the icon, added it back and came up
at Welcome with no way into their account. Removing a Home Screen web
app destroys the whole storage jar, so this wipes localStorage AND
IndexedDB together - the same event - and then asks whether the app can
still get back in.

--against <file> runs it on another build. It has to FAIL there.
"""
import argparse, functools, http.server, io, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = "ABCD-2345"

def serve(path):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{port}/index.html"

# A fake Firestore holding one account under CODE. The real SDK is blocked
# in the sandbox, so the app's own fbDb seam is filled instead: this is the
# cloud the recovery is supposed to reach.
# The app binds `fbDb` lexically from window.firebase, so THAT is the seam,
# not window.fbDb - a stub on window.fbDb is simply never read, which is how
# the first version of this check measured nothing at all. A fake firebase
# makes the app wire its own real code path to this cloud.
CLOUD = """
window.__cloud = {
  "%s": { username:"Madison", onboardingComplete:true, lastModified: Date.now(),
          lifetime:{answered:840,correct:712,drillPlays:22,examPlays:9,gamePlays:6,
                    perfectTests:3,currentStreak:11,longestStreak:17,points:6400},
          stats:{}, testStats:{}, studyLog:{}, testHistory:[], unitPerfects:{}, unitBlackStar:{} }
};
window.__pulled = [];
window.__wrote = [];
window.firebase = {
  apps: [],
  initializeApp(){ window.firebase.apps.push({}); return {}; },
  firestore(){ return {
    collection(name){ return { doc(id){ return {
      get(){ window.__pulled.push(name + "/" + id);
        const d = name === "progress" ? window.__cloud[id] : null;
        return Promise.resolve({ exists: !!d, data: () => d,
                                 metadata: { fromCache: false } }); },
      set(v){ window.__wrote.push({ id, v }); if(name==="progress") window.__cloud[id] = v;
              return Promise.resolve(); },
      update(){ return Promise.resolve(); },
      delete(){ return Promise.resolve(); },
      onSnapshot(){ return function(){}; }
    };},
    where(){ return this; }, orderBy(){ return this; }, limit(){ return this; },
    get(){ return Promise.resolve({ docs: [], forEach(){} }); },
    onSnapshot(){ return function(){}; } };}
  };}
};
window.firebase.firestore.FieldValue = { serverTimestamp(){ return Date.now(); },
                                         delete(){ return null; } };
""" % CODE

def run(src_dir, label):
    srv, url = serve(src_dir)
    fails = []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            ctx = br.new_context(viewport={"width": 440, "height": 956},
                                 is_mobile=True, has_touch=True)
            ctx.add_init_script(
                "Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
            ctx.add_init_script(CLOUD)
            pg = ctx.new_page()
            boot_errs = []
            pg.on("pageerror", lambda e: boot_errs.append(str(e)[:200]))

            # --- 1. an installed app with an account on it
            pg.goto(url)
            pg.evaluate("""(code)=>{
              localStorage.setItem('class26e.synccode', code);
              localStorage.setItem('class26e.drill.v1', JSON.stringify(
                {username:'Madison', onboardingComplete:true, tourRev:999,
                 lastModified: Date.now(),
                 lifetime:{answered:840,correct:712,drillPlays:22,examPlays:9,
                           gamePlays:6,perfectTests:3,currentStreak:11,
                           longestStreak:17,points:6400}}));
            }""", CODE)
            pg.reload(); pg.wait_for_timeout(2600)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")
            real = [e for e in boot_errs if not any(k in e.lower() for k in
                    ("firebase","firestore","gstatic","failed to fetch","net::"))]
            if real:
                print(f"  [{label}] BOOT ERRORS: {real}")
                fails.append(f"the script threw at boot: {real[0]}")

            # --- 2. what the hand-off would open Safari on
            handoff = pg.evaluate(
                "()=> typeof safariHandoffTarget === 'function' ? safariHandoffTarget() : null")
            if not handoff:
                fails.append("openInSafari produced no hand-off URL at all")
            elif CODE not in (handoff or ""):
                fails.append(f"the Safari hand-off does not carry the code: {handoff!r}")

            # --- 3. REMOVE THE ICON. This is the whole event: iOS destroys
            #        the app's storage jar, localStorage and IndexedDB together.
            pg.evaluate("""async ()=>{
              localStorage.clear(); sessionStorage.clear();
              const dbs = (indexedDB.databases ? await indexedDB.databases() : [{name:'class26e-drill-backup'}]);
              await Promise.all(dbs.map(d => new Promise(res => {
                const r = indexedDB.deleteDatabase(d.name); r.onsuccess=r.onerror=r.onblocked=()=>res();
              })));
            }""")

            # --- 4. re-added: the icon launches the URL it was created from
            relaunch = (handoff or "").replace("x-safari-https://", "http://")
            if CODE not in relaunch:
                relaunch = url + "#k=" + CODE
            # about:blank first, ALWAYS. A goto to a URL that differs from
            # the current one only by its fragment is a same-document
            # navigation: nothing reloads, no boot code runs, and the
            # check silently measures the app that was already open. That
            # is what "the cloud was never asked" meant on the first run
            # of this file - the app under test had never restarted.
            pg.goto("about:blank")
            pg.goto(relaunch)
            pg.wait_for_timeout(3200)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")
            pg.wait_for_timeout(1200)

            after = pg.evaluate("""()=>({
              code: (()=>{ try{ return localStorage.getItem('class26e.synccode'); }catch(e){ return null; } })(),
              onboarded: (typeof store !== 'undefined') && !!store.onboardingComplete,
              points: (typeof store !== 'undefined' && store.lifetime && store.lifetime.points) || 0,
              name: (typeof store !== 'undefined' && store.username) || null,
              screen: (document.querySelector('[data-screen]')||{}).dataset
                        ? (document.querySelector('[data-screen]').dataset.screen) : null,
              welcome: !!document.querySelector('[data-screen="welcome"]'),
              pulled: window.__pulled || [],
              hash: location.hash
            })""")
            print(f"  [{label}] after re-add: {json.dumps(after)}")

            if after["welcome"]:
                fails.append("re-added app came up on WELCOME - the account is lost")
            if after["code"] != CODE:
                fails.append(f"the code did not come back (got {after['code']!r})")
            if not after["onboarded"]:
                fails.append("the restored store is not an onboarded account")
            if after["points"] != 6400:
                fails.append(f"progress did not come back (points {after['points']})")
            if not any(CODE in p for p in (after["pulled"] or [])):
                fails.append("the cloud was never asked for this account")
            if after["hash"]:
                fails.append(f"the code was left in the live URL: {after['hash']!r}")

            # --- 5. a SECOND wipe must heal too: the icon re-offers the code
            #        on every launch, so this is not a one-shot cache.
            pg.evaluate("""async ()=>{ localStorage.clear();
              const dbs = (indexedDB.databases ? await indexedDB.databases() : []);
              await Promise.all(dbs.map(d => new Promise(res => {
                const r = indexedDB.deleteDatabase(d.name); r.onsuccess=r.onerror=r.onblocked=()=>res(); })));
            }""")
            pg.goto("about:blank")
            pg.goto(relaunch); pg.wait_for_timeout(3200)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")
            pg.wait_for_timeout(1000)
            again = pg.evaluate("""()=>({ welcome: !!document.querySelector('[data-screen="welcome"]'),
              points:(typeof store!=='undefined'&&store.lifetime&&store.lifetime.points)||0 })""")
            print(f"  [{label}] after a SECOND wipe: {json.dumps(again)}")
            if again["welcome"] or again["points"] != 6400:
                fails.append("a second wipe was not recovered - the URL is not being re-read")

            # --- 6. a URL code must NEVER take over a device that already
            #        has an account of its own.
            pg.evaluate("""(code)=>{ localStorage.setItem('class26e.synccode', code);
              localStorage.setItem('class26e.drill.v1', JSON.stringify(
                {username:'Someone Else', onboardingComplete:true, tourRev:999,
                 lastModified: Date.now(), lifetime:{points:111}}));
            }""", "ZZZZ-9999")
            pg.goto("about:blank")
            pg.goto(url + "#k=" + CODE); pg.wait_for_timeout(3000)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")
            hijack = pg.evaluate("()=>({ code: localStorage.getItem('class26e.synccode') })")
            print(f"  [{label}] URL code against an existing account: {json.dumps(hijack)}")
            if hijack["code"] != "ZZZZ-9999":
                fails.append(f"a URL reassigned a device that already had an account "
                             f"(now {hijack['code']!r}) - that takes somebody off their own account")
            br.close()
    finally:
        srv.shutdown()
    return fails

ap = argparse.ArgumentParser()
ap.add_argument("--against", help="a directory holding another build's index.html")
a = ap.parse_args()
where = a.against or ROOT
label = os.path.basename(where.rstrip("/")) if a.against else "current"
fails = run(where, label)
if fails:
    print(f"\n{len(fails)} FAILURE(S) [{label}]")
    for f in fails: print("  *", f)
    sys.exit(1)
print(f"\nALL PASS [{label}] - re-adding keeps the account")
