"""Build 339: a sync code never rides in a browser tab's address, and Share hands out the real site.
The installed app still adopting its launch code is covered by check-readd.py.
Run:  python3 tools/check-b339.py"""
import io, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
g["DEV"]["tab"] = (440, 956, (0, 0, 0, 0), False)
CODE = "TEST-0330"
STRANGER = "ABCD-EFGH"
FAKE = """window.firebase = { apps: [], initializeApp(){ window.firebase.apps.push({}); return {}; },
  firestore(){ return { collection(name){ return { doc(id){ return {
    get(){ const d = (name === "progress" && id === "%s") ? { firstName:"Casey", username:"Casey", onboardingComplete:true, lastModified:Date.now(), lifetime:{points:900}, stats:{}, testStats:{}, studyLog:{}, testHistory:[] } : null;
      return Promise.resolve({ exists: !!d, data: () => d, metadata: { fromCache:false } }); },
    set(){ return Promise.resolve(); }, update(){ return Promise.resolve(); }, delete(){ return Promise.resolve(); }, onSnapshot(){ return function(){}; } }; },
    where(){ return this; }, orderBy(){ return this; }, limit(){ return this; },
    get(){ return Promise.resolve({ docs: [], forEach(){} }); }, onSnapshot(){ return function(){}; } }; } }; } };
window.firebase.firestore.FieldValue = { serverTimestamp(){ return Date.now(); }, delete(){ return null; } };""" % STRANGER
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    # a signed-in browser tab
    ctx, page = g["page_for"](br, "tab")
    page.evaluate("()=>{ showHome(); }"); page.wait_for_timeout(800)
    h = page.evaluate("location.hash + '|' + location.search")
    g["chk"]("a signed-in browser tab's address carries no sync code after Home", "k=" not in h and CODE not in h, h)
    shared = page.evaluate("()=>{ window.__shared = null; navigator.share = async d => { window.__shared = d; }; return typeof SHARE_URL === 'string' ? SHARE_URL : null; }")
    g["chk"]("the Share link is the real site, a plain address", bool(shared) and shared.startswith("https://") and "#" not in shared and "?" not in shared and not shared.endswith("/Nova/"), shared)
    page.evaluate("()=>{ showAppearance(); }"); page.wait_for_timeout(600)
    page.evaluate("()=>{ const b=[...document.querySelectorAll('button')].find(x=>/Share this app/.test(x.textContent)); b && b.click(); }"); page.wait_for_timeout(800)
    sd = page.evaluate("window.__shared")
    g["chk"]("tapping Share this app shares exactly that address", bool(sd) and sd.get("url") == shared, sd)
    page.evaluate("()=>showInstallGuide('ios')"); page.wait_for_timeout(300)
    h = page.evaluate("location.hash")
    g["chk"]("while the Add to Home Screen steps are open the icon can carry the code", CODE in h, h)
    page.evaluate("()=>{ [...document.querySelectorAll('.installguide-card button')].find(x=>/Got it/.test(x.textContent)).click(); }"); page.wait_for_timeout(300)
    h = page.evaluate("location.hash")
    g["chk"]("...and closing them takes it off the address again", "k=" not in h, h)
    ctx.close()
    # a stranger opens a link that still has a code in it (links already sent)
    g["g"]["new_page"].w, g["g"]["new_page"].h = 440, 956
    ctx, page = g["g"]["new_page"](br, (62, 0, 34, 0), False, False)
    page.add_init_script(FAKE)
    page.goto(g["url"] + "#k=" + STRANGER); page.wait_for_timeout(3500)
    page.evaluate("document.getElementById('splashscreen')?.remove()"); page.wait_for_timeout(500)
    r = page.evaluate("()=>({ hash: location.hash, sc: localStorage.getItem('class26e.synccode'), txt: document.body.innerText, link: browserLinkCode })")
    g["chk"]("an old link with a code in a browser tab is stripped from the address", "k=" not in r["hash"], r["hash"])
    g["chk"]("...is not adopted", not r["sc"], r["sc"])
    g["chk"]("...and is not held to offer as an account to continue", not r["link"], r["link"])
    g["chk"]("...and Welcome does not offer to continue as anyone", "Continue as" not in r["txt"] and "Continue to your account" not in r["txt"], r["txt"][:200])
    ctx.close()
    br.close()
sys.exit(0 if g["ok"] else 1)
