#!/usr/bin/env python3
"""trace-badge-run.py - for ANY run, print what it earned and which scenes played (or why one did not).   (384.50)

The owner's report, three times: "badge cutscenes aren't showing up". This is the instrument that answers, for a real run played through the
page's own buttons in Chromium, the three questions a badge report needs answered:

    earned items: badges [...], chars [...], banners [...], effects [...], flare ...
    scenes played: [...]   (each with when it came up and how long it was up, ms from the first answer)
    scene skipped because: <guard>      (a muted setting, a sequence stopped by a screen change, a thrown error, ...)

It changes nothing in the app: it wraps the scene players (playBadgeCaseScene, playUnlockSpotlight, playFlareFoundScene, the rank-up
scenes, makeRevealSequence's stop) from outside, after the page has loaded, and reads.

Usage (as a tool):
    python3 tools/trace-badge-run.py [--class academy|ifc] [--scenario NAME ...] [--against FILE] [--seed-json FILE] [--unit NAME] [--out FILE]
Scenarios: plain (no taps), tap (a tap on the results at each step), taps (4 a second from the results on), hide (the page goes hidden for 3s
once during the results), multi (a two-unit selection), retake (retake of missed questions), early (the results left through the tab bar
at once), reduce (Reduce motion)
As a module: `from importlib ... trace-badge-run` and use page(), run(), report().

--seed-json takes a progress document (an account's real state, with no code in it) to play on top of; the unit played is then a unit it
already holds a badge for, taken back to one hundo short.
"""
import json, os, re, sys, time, functools, http.server, socket, threading, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def load_body():
    return open(arg("--against") or (ROOT + "/index.html"), encoding="utf-8").read()


def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted"]
BASE_SEED = {"onboardingComplete": True, "firstName": "Maddog", "avatarChar": "ninja", "publicId": "xph5b57jbp5a", "novaMet": 99,
             "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
             "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
             "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30,
                          "longestStreak": 20, "currentStreak": 3}}
# fields of a real progress document that are about OTHER people or are codes: never carried into a local fixture
DROP = ("friendCode", "friendsIn", "friendsOut", "friendsDeclined", "chats", "chatInvitesOut", "lobbyInvitesOut", "savedCodePrompts", "savedCodeSaved")


def init_js(cls, seed):
    s = ("(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1');"
         "localStorage.setItem('class26e.intro.seen','9'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');")
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(seed))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(seed))
    return s + " }catch(e){} })()"


INSTRUMENT = r"""()=>{
 if(window.__tr) return 'already';
 const T = window.__tr = { t0: performance.now(), log: [], runs: [], scenes: [], skipped: [], errors: [], stops: [] };
 const now = () => Math.round(performance.now() - T.t0);
 const L = (k, v) => T.log.push([now(), k, v === undefined ? null : v]);
 window.addEventListener('error', e => T.errors.push([now(), String(e.message).slice(0, 160)]));
 window.addEventListener('unhandledrejection', e => T.errors.push([now(), 'rejection ' + String(e.reason).slice(0, 120)]));
 document.addEventListener('visibilitychange', () => L('visibility', document.visibilityState));
 const guards = () => ({ muteBanners: !!theme.muteBanners, reduceMotion: !!theme.reduceMotion, motionOff: (()=>{ try{ return resultsMotionOff(); }catch(e){ return null; } })(),
                         hidden: document.hidden, screen: (document.querySelector('[data-screen]') || {dataset:{}}).dataset.screen || null });
 // what the run earned: every call of rsUnlockItems sees the run
 const _ri = window.rsUnlockItems;
 window.rsUnlockItems = function(run){
   const items = _ri.apply(this, arguments);
   T.runs.push({ at: now(), badges: (run.badges || []).slice(), retro: (run.retroBadges || []).slice(), chars: (run.characters || []).slice(), banners: (run.banners || []).slice(),
     fx: (run.fx || []).slice(), flare: run.flare || null, perfect: !!run.isPerfect, retake: !!run.retake, pct: run.pct, mode: run.mode, items: items.map(i => i.kind + ':' + (i.unit || i.character || i.banner || i.fx || i.flare || '')) , guards: guards() });
   return items;
 };
 const wrapScene = (name, sel, label) => {
   const orig = window[name]; if(typeof orig !== 'function') return;
   window[name] = function(){
     const args = Array.prototype.slice.call(arguments);
     const rec = { name: label || name, at: now(), arg: String(args[0] && (args[0].unit || args[0].kind || args[0]) || '').slice(0, 60), guards: guards(), up: null, done: null, ended: null, threw: null };
     T.scenes.push(rec);
     const di = args.findIndex(a => typeof a === 'function');
     if(di >= 0){ const d = args[di]; args[di] = function(){ rec.done = now(); return d.apply(this, arguments); }; }
     let ret;
     try{ ret = orig.apply(this, args); }catch(e){ rec.threw = String(e && e.message || e).slice(0, 160); T.errors.push([now(), name + ' threw: ' + rec.threw]); throw e; }
     rec.ret = ret ? 'handle' : String(ret);
     rec.shown = sel ? !!document.querySelector(sel) : null;
     if(sel && !rec.shown) T.skipped.push({ scene: rec.name, at: now(), why: rec.done !== null ? 'returned at once (done() before any scene: ' + JSON.stringify(rec.guards) + ')' : 'no overlay appeared' });
     if(sel && rec.shown){ rec.up = now(); const el = document.querySelector(sel); const mo = new MutationObserver(() => { if(!el.isConnected){ rec.ended = now(); mo.disconnect(); } });
       mo.observe(document.body, { childList: true }); }
     return ret;
   };
 };
 wrapScene('playBadgeCaseScene', '.bc-scene', 'badge case');
 wrapScene('playUnlockSpotlight', '.rs-spot', 'unlock card');
 wrapScene('playFlareFoundScene', '.sf-scene', 'flare found');
 wrapScene('playTierCutscene', '#supernova-cutscene', 'rank-up scene');
 wrapScene('playSupernovaCutscene', '#supernova-cutscene', 'supernova scene');
 wrapScene('playQueuedBadgeCutscenes', null, 'home badge queue');
 wrapScene('playHomeUnlocks', null, 'home unlocks');
 // a reveal sequence stopped before it ended (the results left, a new run began)
 const _mk = window.makeRevealSequence;
 window.makeRevealSequence = function(alive){
   const seq = _mk.apply(this, arguments);
   const st = seq.stop; let steps = 0; const add = seq.add;
   seq.add = function(){ steps++; return add.apply(this, arguments); };
   seq.stop = function(){ const was = seq.isRunning(); const r = st.apply(this, arguments); if(was) T.stops.push({ at: now(), steps, screen: guards().screen, stack: String(new Error().stack).split('\n').slice(2, 5).map(s => s.trim().slice(0, 90)) }); return r; };
   return seq;
 };
 return 'ok';
}"""

ANSWER = r"""()=>{ if(!document.querySelector('.choice') || typeof order === 'undefined' || !order.length) return 'wait';
  const key = order.length + ':' + pos;
  if(window.__answered !== key){ if(performance.now() - (window.__nextAt || 0) < 700) return 'wait'; const c = document.querySelector('.choice[data-index="' + correctSlot(order[pos]) + '"]'); if(!c) return 'wait'; c.click(); window.__answered = key; window.__answeredAt = performance.now(); return 'answered'; }
  const n = document.getElementById('nextbtn'); if(n && !n.hidden && performance.now() - window.__answeredAt > 400){ n.click(); window.__nextAt = performance.now(); return 'next'; } return 'wait'; }"""

PROBE = r"""()=>{ const bc = document.querySelector('.bc-scene'), sp = document.querySelector('.rs-spot'), rs = !!document.querySelector('.rs-screen'),
  acts = !!document.querySelector('.rs-actions.rs-rising, .rs-actions.rs-in-now, .rs-actions .rs-rise-in, .rs-endslot button');
  return { bc: bc ? (bc.classList.contains('bc-out') ? 'out' : 'up') : null, spot: sp ? ((sp.className.match(/rs-spot-(\w+)/) || [])[1] || 'x') + (sp.classList.contains('is-leaving') ? '/leaving' : '/up') : null,
           rs, done: !!document.querySelector('.rs-screen.rs-done'), screen: (document.querySelector('[data-screen]') || {dataset: {}}).dataset.screen || null, tabbar: !!document.querySelector('.bottomtabs:not([hidden])') }; }"""


def page(br, cls, seed, reduce=False, w=440, h=956, dpr=3, body=None, mobile=True):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=mobile,
                         reduced_motion="reduce" if reduce else "no-preference")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js(cls, seed))
    body = body or load_body()
    served = (re.search(r'const APP_BUILD = "([^"]+)"', body) or [None, ""])[1]
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % served))
    return ctx, pg, errs


def open_page(pg, port):
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.evaluate(INSTRUMENT)


def run(pg, scenario="plain", units=None, tap_every=0.25, limit=120, one_short=True, hide=False, retake_from=None, setup=""):
    """Play one run to the end of its results through the page's own buttons. Returns the trace."""
    if units is None:
        units = [pg.evaluate("()=>unitsInTeachingOrder().filter(u=>unitQuestionCount(u)>0).sort((a,b)=>unitQuestionCount(a)-unitQuestionCount(b))[0]")]
    if setup: pg.evaluate(setup)
    pg.evaluate(r"""(units) => { units.forEach(t => { if(!store.unitPerfects) store.unitPerfects = {}; store.unitPerfects[t] = Math.max(0, badgeThresholdFor(t) - 1);
        try{ if(store.badgeCleanedAt) delete store.badgeCleanedAt[t]; }catch(e){} });
      saveStore(); showHome(); cfg.source = 'all'; cfg.mode = 'drill'; cfg.units = units.slice();
      setTimeout(() => beginRun(QUESTIONS.map((q, i) => i).filter(i => units.indexOf((QUESTIONS[i].topic || '').trim()) >= 0)), 1200); return true; }""", units)
    t0 = time.time(); rs_at = None; nxt = 0; taps = 0; frames = []; hid = False; early = False
    while time.time() - t0 < limit:
        try:
            on_rs = pg.evaluate("()=>!!document.querySelector('.rs-screen')")
            if on_rs:
                if rs_at is None: rs_at = time.time()
                if scenario in ("taps", "tap") and time.time() >= nxt:
                    pg.mouse.click(220, 300); taps += 1; nxt = time.time() + (tap_every if scenario == "taps" else 1.5)
                if scenario == "hide" and not hid and time.time() - rs_at > 6:
                    hid = True
                    pg.evaluate("()=>{ Object.defineProperty(document,'hidden',{get:()=>true,configurable:true}); Object.defineProperty(document,'visibilityState',{get:()=>'hidden',configurable:true}); document.dispatchEvent(new Event('visibilitychange')); }")
                    pg.wait_for_timeout(3000)
                    pg.evaluate("()=>{ Object.defineProperty(document,'hidden',{get:()=>false,configurable:true}); Object.defineProperty(document,'visibilityState',{get:()=>'visible',configurable:true}); document.dispatchEvent(new Event('visibilitychange')); }")
            else:
                pg.evaluate(ANSWER)
            p = pg.evaluate(PROBE)
            frames.append([round(time.time() - t0, 2), p["bc"], p["spot"], p["rs"], p["done"]])
            if rs_at and p["done"] and time.time() - rs_at > 2: break
            if rs_at and scenario == "early" and not early and time.time() - rs_at > 1.5:
                early = True
                pg.evaluate("()=>{ const b = document.getElementById('bottomtab-home') || document.getElementById('homeBtn'); if(b) b.click(); }")
            if rs_at and not p["rs"] and time.time() - rs_at > 3: break
        except Exception as ex:
            print("   (run: %s)" % str(ex)[:100])
        pg.wait_for_timeout(120)
    # let a scene still up play out (the results can be "done" under a still scene in Reduce motion)
    for _ in range(160):
        try:
            if not pg.evaluate("()=>!!document.querySelector('.bc-scene, .rs-spot')"): break
        except Exception: break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(600)
    tr = pg.evaluate("()=>window.__tr")
    tr["resultsAt"] = None if rs_at is None else round(rs_at - t0, 1); tr["taps"] = taps; tr["frames"] = frames
    tr["unitsPlayed"] = units
    return tr


def report(tr, label=""):
    """The three lines the owner's report needs."""
    badges = sorted({b for r in tr["runs"] for b in r["badges"]}); chars = sorted({c for r in tr["runs"] for c in r["chars"]})
    banners = sorted({c for r in tr["runs"] for c in r["banners"]}); fx = sorted({c for r in tr["runs"] for c in r["fx"]}); flares = sorted({r["flare"] for r in tr["runs"] if r["flare"]})
    print("== %s (results at %ss, %d taps)" % (label, tr.get("resultsAt"), tr.get("taps", 0)))
    short = lambda xs: [x[:34] for x in xs]
    print("earned items: badges %s, chars %s, banners %s, effects %s, flares %s" % (short(badges), chars, banners, fx, flares))
    played = []
    for s in tr["scenes"]:
        if s.get("shown"):
            played.append("%s%s @%dms up %s" % (s["name"], " [" + s["arg"][:28] + "]" if s["arg"] else "", s["at"],
                          ("%dms" % (s["ended"] - s["up"])) if s.get("ended") and s.get("up") else "still up/never ended"))
    print("scenes played: %s" % (played or []))
    for s in tr["skipped"]:
        print("scene skipped because: %s: %s" % (s["scene"], s["why"]))
    for st in tr["stops"]:
        print("a reveal sequence was stopped early at %dms on screen %s (%d steps), by %s" % (st["at"], st["screen"], st["steps"], " < ".join(st["stack"][:2])))
    if tr["errors"]: print("page errors: %s" % tr["errors"][:3])
    want_scene = bool(badges)
    got_scene = any(s["name"] == "badge case" and s.get("shown") and s.get("ended") and s.get("up") for s in tr["scenes"])
    verdict = "n/a (no badge earned)" if not want_scene else ("badge case played" if got_scene else "BADGE EARNED, NO BADGE CASE PLAYED")
    print("verdict: " + verdict)
    return got_scene if want_scene else None


def main():
    from playwright.sync_api import sync_playwright
    cls = arg("--class", "academy")
    scen = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--scenario"] or ["plain"]
    seed = dict(BASE_SEED)
    sj = arg("--seed-json")
    if sj:
        seed = {k: v for k, v in json.load(open(sj)).items() if k not in DROP}
        seed["onboardingComplete"] = True
    if "--mute" in sys.argv:
        seed["theme"] = dict(seed.get("theme") or {}, muteBanners=True)
    srv, port = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for sc in scen:
            ctx, pg, errs = page(br, cls, seed, reduce=(sc == "reduce"), body=load_body())
            open_page(pg, port)
            units = [arg("--unit")] if arg("--unit") else None
            tr = run(pg, sc, units=units)
            report(tr, "%s / %s" % (cls, sc))
            ctx.close()
        br.close()


if __name__ == "__main__":
    main()
