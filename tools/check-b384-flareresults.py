"""Build 384.59: a secret flare's find is the results' - not the main menu's - while its test can still be finished.
The owner: "Secret flare pop ups, why did it happen on the main menu? Is it because I left a test and left the app? They should be showing
up in results."

WHAT IT WAS, played in Chromium on 384.48: a flare tapped in a test, the app then closed (a reload is the stand-in for iOS putting it away
and the person coming back). The test comes back as an unfinished one (scheduleResumeOffer: "Continue your test?" is offered by Start
Studying) and Home played the find's scene and its card ~2.5s after launch, with the test still waiting. The find was in that test's save
slot (flareFound) and the test's own results would have played it. Finishing a test and staying on its results always played it there.

(A) LOST RUN: flare tapped, app closed, relaunch. For 9s on Home nothing of the find plays (no scene, no card), it is still owed, and the
    test is still offered. Continued and finished, the results play the scene and the card; afterwards nothing is owed and Home plays nothing.
(B) QUIT TEST: flare tapped, "Quit test". The test is gone, so Home plays the find once (scene, then card) and never again.
(C) A FINISHED RUN, stayed on: results play the scene and the card, Home plays nothing afterwards.
(D) "Skip celebrations and pop-ups" on: a lost run's find plays nothing, anywhere, and is no longer owed.
(E) THE HOLD ENDS: a lost run's find a day old plays on Home (never lost).
(F) THE THIRD FLARE (Void), lost run: Home plays none of its scene, card, character, banner or the "A new secret" card while the test waits.
(G) no page errors.

Run:  python3 tools/check-b384-flareresults.py   (--against OLD/index.html must FAIL (A, F); ONLY=A,B runs those)"""
import json, os, re, sys, time, functools, http.server, socket, threading, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else open(ROOT + "/index.html", encoding="utf-8").read()
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}
def want(n): return not ONLY or n in ONLY
from playwright.sync_api import sync_playwright
ok = True
buf = []
def chk(name, cond, info=""):
    """held until its scenario has finished: a browser that dies under load (a shared machine) takes that scenario's lines with it, and the scenario is run again"""
    buf.append((bool(cond), ("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:700])))
def flush():
    global ok
    for c, line in buf:
        ok = ok and c; print(line, flush=True)
    del buf[:]
so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
_m = re.search(r'const APP_BUILD = "([^"]+)"', BODY)
SERVED = _m.group(1) if _m else ""
# an existing, up-to-date account (tours seen, Nova met, everything it holds announced): nothing lands over what is measured
SEED = {"onboardingComplete": True, "firstName": "Maddog", "avatarChar": "ghost", "publicId": "xph5b57jbp5a", "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30,
                     "longestStreak": 20, "currentStreak": 3}}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted"]
def init_js():
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    return s + " }catch(e){} })()"
ARGS = ["--disable-dev-shm-usage"]
def page(br, w=440, h=956):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, has_touch=True)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js())
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    # the page's own build, whatever the repo's version.json says (under --against the update check would reload the page mid-walk)
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % SERVED))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    boot(pg)
    return ctx, pg, errs
def boot(pg):
    """past the splash, and everything the account already holds marked as announced (the seed holds a hundo effect the account has not seen)"""
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ const p = pendingHomeUnlocks(); markUnlocksShown(p.chars, p.banners, p.fx); }catch(e){} document.querySelectorAll('.rs-spot').forEach(e => e.remove()); }")
# every scene and card the find can put up, and the screen it was put up on
LOGGER = r"""()=>{ if(window.__log) return; window.__log = [];
  const scr = () => document.querySelector('#stage [data-screen="home"]') ? 'home' : document.querySelector('#stage .rs-screen') ? 'results' : document.querySelector('#stage .choice') ? 'question' : 'other';
  const seen = new WeakSet();
  const scan = () => { document.querySelectorAll('.sf-scene,.fl-scene,.ff-scene,.rs-spot').forEach(e => { if(seen.has(e)) return; seen.add(e);
     window.__log.push({ screen: scr(), kind: e.matches('.rs-spot') ? ((String(e.className).match(/rs-spot-(\w+)/) || [])[1] || 'card') : 'scene', t: Math.round(performance.now()) }); }); };
  new MutationObserver(scan).observe(document.body, { subtree: true, childList: true }); setInterval(scan, 100); }"""
ANSWER = r"""()=>{ if(!document.querySelector('.choice') || typeof order === 'undefined' || !order.length) return 'wait';
  const key = order.length + ':' + pos;
  if(window.__answered !== key){ if(performance.now() - (window.__nextAt || 0) < 700) return 'wait'; const c = document.querySelector('.choice[data-index="' + correctSlot(order[pos]) + '"]'); if(!c) return 'wait'; c.click(); window.__answered = key; window.__answeredAt = performance.now(); return 'answered'; }
  const n = document.getElementById('nextbtn'); if(n && !n.hidden && performance.now() - window.__answeredAt > 400){ n.click(); window.__nextAt = performance.now(); return 'next'; } return 'wait'; }"""
START = r"""(t) => { store.unitPerfects = {}; store.mysteryColorsFound = { red:false, orange:false, yellow:false, violet:false, white:false, core:false }; store.flareHintsShown = []; saveStore(); showHome();
  cfg.source = 'all'; cfg.mode = 'drill'; cfg.units = [t];
  setTimeout(() => beginRun(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === t)), 800); return true; }"""
OWED = "()=>localStorage.getItem('class26e.flarefinds.owed')"
HOME = "()=>!!document.querySelector('#stage [data-screen=\"home\"]')"
def until(pg, js, limit, step=200):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            if pg.evaluate(js): return True
        except Exception: pass
        pg.wait_for_timeout(step)
    return False
def log(pg): return pg.evaluate("()=>window.__log || []")
def find_in_test(pg, color="red", earlier=None):
    """a real run in the smallest unit; at its second question the flare is there and tapped (what a person does)"""
    topic = pg.evaluate("()=>unitsInTeachingOrder().filter(u=>unitQuestionCount(u)>0).sort((a,b)=>unitQuestionCount(a)-unitQuestionCount(b))[0]")
    pg.evaluate(START, topic)
    assert until(pg, "()=>!!document.querySelector('.choice')", 20), "test did not start"
    while pg.evaluate("()=>pos") < 1:
        pg.evaluate(ANSWER); pg.wait_for_timeout(100)
    pg.wait_for_timeout(600)
    if earlier: pg.evaluate("(f)=>{ f.forEach(k => store.mysteryColorsFound[k] = true); saveStore(); }", earlier)
    pg.evaluate("(c)=>{ mysteryColorThisRun = c; mysteryFoundThisSession = false; mysteryAppearsAtPos = pos; render(); }", color)
    pg.wait_for_timeout(500)
    tapped = pg.evaluate("()=>{ const s = document.querySelector('.mystery-spark'); if(!s) return false; s.click(); return true; }")
    pg.wait_for_timeout(1200)
    return tapped
def app_closed(pg):
    """the app put away and coming back: the page is hidden (the run is saved), then it is gone and loaded again"""
    pg.evaluate("()=>{ window.dispatchEvent(new Event('pagehide')); }")
    pg.reload(); pg.wait_for_timeout(3500)
    boot(pg); pg.evaluate(LOGGER)
def watch_home(pg, secs):
    """seconds of Home with the logger on: what was put up, and where"""
    t0 = time.time()
    while time.time() - t0 < secs: pg.wait_for_timeout(500)
    return log(pg)
def finish_to_results(pg, limit=120):
    t0 = time.time()
    while time.time() - t0 < limit:
        if pg.evaluate("()=>!!document.querySelector('.rs-screen')"): return True
        pg.evaluate(ANSWER); pg.wait_for_timeout(100)
    return False

def scen_A(br, errs_all):
    # (A) a lost run: the find waits for its test's results
    ctx, pg, errs = page(br)
    pg.evaluate(LOGGER)
    chk("(A) setup: the flare was there and tapped, and it is owed", find_in_test(pg) and bool(pg.evaluate(OWED)), pg.evaluate(OWED))
    app_closed(pg)
    seen = watch_home(pg, 9)
    owed = pg.evaluate(OWED)
    chk("(A) the app closed and opened again: for 9s on Home no scene and no card of the find is put up (%s)" % [e["kind"] + "@" + e["screen"] for e in seen], not seen, seen)
    chk("(A) ... the find is still owed, and the test is still there to continue", bool(owed) and pg.evaluate("()=>!!readRunSession()"), [owed, pg.evaluate("()=>!!readRunSession()")])
    pg.evaluate("()=>startStudying()"); pg.wait_for_timeout(700)
    has_offer = pg.evaluate("()=>!!document.getElementById('resume-go')")
    chk("(A) Start Studying offers the test back (Resume test)", has_offer)
    if has_offer:
        pg.evaluate("()=>document.getElementById('resume-go').click()")
        got = until(pg, "()=>!!document.querySelector('.choice') && typeof order !== 'undefined' && testInProgress", 30)
        pg.evaluate(LOGGER)
        reached = got and finish_to_results(pg)
        chk("(A) the test is continued and finished: its results come up", reached)
        if reached:
            played = until(pg, "()=>window.__log.some(e => e.kind === 'flare')", 80, 250)
            lg = log(pg)
            chk("(A) the results play the find: its scene, then its card, both on the results screen (%s)" % [e["kind"] + "@" + e["screen"] for e in lg],
                played and [e["kind"] for e in lg][:2] == ["scene", "flare"] and all(e["screen"] == "results" for e in lg), lg)
            gone = until(pg, "()=>!localStorage.getItem('class26e.flarefinds.owed')", 40)
            chk("(A) ... and once seen nothing is owed", gone, pg.evaluate(OWED))
            pg.evaluate("()=>showHome()")
            after = watch_home(pg, 8)
            chk("(A) Home afterwards plays nothing of it again (exactly once)", len(after) == len(lg), after)
    errs_all += errs; ctx.close()

def scen_B(br, errs_all):
    # (B) Quit test: the test is gone, Home plays the find once
    ctx, pg, errs = page(br)
    pg.evaluate(LOGGER)
    find_in_test(pg)
    pg.evaluate("()=>confirmExitTest()"); pg.wait_for_timeout(500)
    pg.evaluate("()=>document.getElementById('quit-confirm').click()"); pg.wait_for_timeout(500)
    played = until(pg, "()=>window.__log.some(e => e.kind === 'flare')", 50, 250)
    lg = log(pg)
    chk("(B) Quit test: the test is gone, so Home plays the find - its scene, then its card (%s)" % [e["kind"] + "@" + e["screen"] for e in lg],
        played and [e["kind"] for e in lg][:2] == ["scene", "flare"] and all(e["screen"] == "home" for e in lg), lg)
    until(pg, "()=>!localStorage.getItem('class26e.flarefinds.owed')", 30)
    pg.evaluate("()=>showHome()")
    again = watch_home(pg, 6)
    chk("(B) ... once: a second Home plays nothing more", len(again) == len(lg) and not pg.evaluate(OWED), again)
    errs_all += errs; ctx.close()

def scen_C(br, errs_all):
    # (C) a finished run, stayed on: results play it, Home nothing
    ctx, pg, errs = page(br)
    pg.evaluate(LOGGER)
    find_in_test(pg)
    reached = finish_to_results(pg)
    played = reached and until(pg, "()=>window.__log.some(e => e.kind === 'flare')", 80, 250)
    lg = log(pg)
    chk("(C) a finished run: the results play the scene and the card on the results screen (%s)" % [e["kind"] + "@" + e["screen"] for e in lg],
        played and [e["kind"] for e in lg][:2] == ["scene", "flare"] and all(e["screen"] == "results" for e in lg), lg)
    until(pg, "()=>!localStorage.getItem('class26e.flarefinds.owed')", 40)
    pg.evaluate("()=>showHome()")
    after = watch_home(pg, 7)
    chk("(C) ... and Home plays nothing of it afterwards", len(after) == len(lg), after)
    errs_all += errs; ctx.close()

def scen_D(br, errs_all):
    # (D) celebrations off: nothing plays, nothing is owed
    ctx, pg, errs = page(br)
    pg.evaluate("()=>{ theme.muteBanners = true; saveTheme(); }")
    pg.evaluate(LOGGER)
    find_in_test(pg)
    app_closed(pg)
    seen = watch_home(pg, 8)
    chk("(D) 'Skip celebrations and pop-ups' on: a lost run's find plays nothing on Home", not seen, seen)
    chk("(D) ... and is not owed afterwards (nothing will ever be shown for it)", not pg.evaluate(OWED), pg.evaluate(OWED))
    errs_all += errs; ctx.close()

def scen_E(br, errs_all):
    # (E) the hold ends: a find a day old plays on Home
    ctx, pg, errs = page(br)
    pg.evaluate(LOGGER)
    find_in_test(pg)
    pg.evaluate("()=>{ const a = JSON.parse(localStorage.getItem('class26e.flarefinds.owed') || '[]'); a.forEach(o => { o.t = Date.now() - 25 * 3600 * 1000; }); localStorage.setItem('class26e.flarefinds.owed', JSON.stringify(a)); }")
    app_closed(pg)
    played = until(pg, "()=>window.__log.some(e => e.kind === 'flare')", 40, 250)
    lg = log(pg)
    chk("(E) a lost run's find that is a day old is not held: Home plays it (scene, card), so it is never lost", played and [e["kind"] for e in lg][:2] == ["scene", "flare"], lg)
    errs_all += errs; ctx.close()

def scen_F(br, errs_all):
    # (F) the third flare, lost run: nothing of Void on Home
    ctx, pg, errs = page(br)
    pg.evaluate(LOGGER)
    find_in_test(pg, "yellow", ["red", "orange"])
    app_closed(pg)
    seen = watch_home(pg, 9)
    up = pg.evaluate("()=>document.querySelectorAll('.rs-spot, .ff-scene, .sf-scene, .fl-scene').length")
    chk("(F) the third flare found, the app closed and opened: Home puts up none of Void's scene, card, character, banner or 'A new secret' (%s)" % [e["kind"] + "@" + e["screen"] for e in seen], not seen and up == 0, [seen, up])
    chk("(F) ... and the find is still owed to the test", bool(pg.evaluate(OWED)), pg.evaluate(OWED))
    errs_all += errs; ctx.close()

with sync_playwright() as pw:
    errs_all = []
    for key, fn in (("A", scen_A), ("B", scen_B), ("C", scen_C), ("D", scen_D), ("E", scen_E), ("F", scen_F)):
        if not want(key): continue
        for attempt in range(3):
            br = pw.chromium.launch(executable_path=CHROME, args=ARGS)
            try:
                fn(br, errs_all); flush(); break
            except Exception as ex:
                del buf[:]
                print("   (%s: %s - run again)" % (key, str(ex).split("\n")[0][:90]), flush=True)
            finally:
                try: br.close()
                except Exception: pass
        else:
            chk("(%s) the browser kept dying under load - not measured" % key, False); flush()
    chk("(G) no page errors", not errs_all, errs_all); flush()
print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
