#!/usr/bin/env python3
"""384.99 (resultskip): the results screen's tap to skip, its buttons, and its bars, held as SHAPE (no label strings; every
number read off the page).

Madison, on his iPhone: "Ensure tap to skip works properly with the result screen, the timing is weird, I'm sitting there
having to spam it for it to register, it should just speed up/skip." / "When the results are up, the buttons under it take like
3-4 seconds to let you tap them." / "When scoring a hundred. The bar lags as it goes up. Get this right."

REAL runs (a drill through summarize(), check-results' SETUP), the page's REAL clock, REAL touch (CDP Input.dispatchTouchEvent),
an iPhone 17 Pro Max 440x956 @3x and an iPad Pro 11" 834x1194 @2x.

THE IPHONE'S CLICK RULE IS MODELLED, because Chromium sends a click for every tap and an iPhone does not. Read off WebKit
(WebPage::potentialTapAtPosition / commitPotentialTap, ancestorRespondingToClickEvents): a tap gets a click only when the touched
element, or an ancestor BELOW <body>, answers clicks itself (a click / mousedown / mouseup listener, or a control) - listeners on
document or window do not count - and only when that element is the same one when the finger lifts as when it landed. An init
script records which elements were given such listeners and drops (stopImmediatePropagation, before any of the page's own
listeners) every touch-made click that rule would never have produced (window.__iosDropped counts them).

 S1  ONE tap skips: a tap at each stage of the reveal (before the grade lands, while it counts, during a 100%'s hundo effect,
     while the XP lines come in, while the XP bar fills), in the middle of the screen, in the side gutter and on the "Tap to
     skip" words, and in Fire Code, an exam and a practice test: within 350ms everything has landed in its final state (nothing
     half-way: no card mid-landing, the grade not counting and in its place, every bar at its end and not moving, the effect's
     layers gone, the hint gone, the buttons drawn and live) and it is still that 400ms later (nothing kept counting).
 S3  The unlock queue is intact: a run that earns a badge, tapped while it counts: everything up to the badge's case lands, the
     case still plays (and a tap on it does not end it), the "Found & unlocked" box lands every row after it, the badge is held,
     its scene marked played and nothing owed; with "Skip celebrations and pop-ups" on, one tap lands the box, its note and the
     buttons with no scene.
 S4  Each button under the results (Continue to review, Re-run, Main menu - read off the page) takes a tap that lands within
     100ms of the frame it is first drawn, after a skip and after a reveal left alone; and with Reduce motion.
 S5  The builds 305 / 380 / 382 protections (pass on both builds by design: they are kept, not new): a tap where Main menu will
     be, before it is there, leaves the results alone; taps that keep coming at that spot as it arrives do not press it, and the
     first after a pause does.
 S6  The bars do not lag, at 4x CPU, 440x956 @3x, a 100% run and a run that climbs a level: while the grade counts and while the
     XP bar fills, every bar is moved by a running transform-only animation, not by script (style writes on a bar: a few, not
     one a frame); no layout or style pass forced by script; no element made by the counting numbers; the warm-ups held back
     (recordingShouldWait > 0); the XP number counts with its bar, and the level wrap reads (full, empty, filling, the level
     one higher). Frame pacing is printed, not judged (this machine's load moves it more than any build does).

  python3 tools/check-b384-resultskip.py [--against OLD_INDEX] [--only S1,S4] [--dev max|ipad]
"""
import importlib.util, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
ONLY = None
if "--only" in args:
    i = args.index("--only"); ONLY = args[i + 1].split(","); del args[i:i + 2]
DEVONLY = None
if "--dev" in args:
    i = args.index("--dev"); DEVONLY = args[i + 1]; del args[i:i + 2]
AG = []
if "--against" in args:
    i = args.index("--against"); AG = ["--against", os.path.abspath(args[i + 1])]
sys.argv = [sys.argv[0]] + AG
_spec = importlib.util.spec_from_file_location("cb", HERE + "/check-behaviour.py")
cb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cb)
_r = open(HERE + "/check-results.py").read()
_i = _r.index('SETUP = """') + len('SETUP = """'); SETUP = _r[_i:_r.index('"""', _i)]
from playwright.sync_api import sync_playwright

ok = True
FAILS = []
def ck(name, cond, detail=""):
    global ok
    print("  ", "PASS" if cond else "FAIL", name, ("-> " + str(detail)[:600]) if detail != "" else "", flush=True)
    if not cond: ok = False; FAILS.append(name)
def info(name, detail): print("   INFO", name, "->", str(detail)[:600], flush=True)
def want(k): return ONLY is None or k in ONLY

MAX = ("17 Pro Max", 440, 956, 3)
IPAD = ("iPad Pro 11", 834, 1194, 2)
DEVS = [d for d in (MAX, IPAD) if not DEVONLY or (DEVONLY == "max" and d is MAX) or (DEVONLY == "ipad" and d is IPAD)]
UNIT = "Identity Crimes"

IOS_CLICKS = r"""(() => {
  const S = new WeakSet(), add = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function(type, fn, o){
    if((type === 'click' || type === 'mousedown' || type === 'mouseup') && this && this.nodeType === 1) S.add(this);
    return add.call(this, type, fn, o);
  };
  const CTL = 'a[href], button, input, select, textarea, label, summary, [onclick]';
  const responder = el => { for(let a = el; a && a.nodeType === 1 && a !== document.body && a !== document.documentElement; a = a.parentElement){ if(S.has(a) || a.onclick || a.matches(CTL)) return a; } return null; };
  let downNode, downAt = -1e9;
  add.call(window, 'touchstart', e => { const p = e.touches && e.touches[0]; const el = p ? document.elementFromPoint(p.clientX, p.clientY) : null; downNode = el ? responder(el) : null; downAt = performance.now(); }, { capture: true, passive: true });
  add.call(window, 'click', e => {
    if(!e.isTrusted || downNode === undefined || performance.now() - downAt > 1500) return;
    const now = responder(e.target), drop = !downNode || now !== downNode;
    downNode = undefined;
    if(drop){ e.stopImmediatePropagation(); e.preventDefault(); window.__iosDropped = (window.__iosDropped || 0) + 1; }
  }, true);
})();"""

INSTR = r"""() => {
  window.__iosDropped = 0;
  window.__vis = el => { if(!el) return 0; let o = 1, x = el; while(x && x.nodeType === 1){ const cs = getComputedStyle(x); if(cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; x = x.parentElement; } return o; };
  /* the results as they stand: what is not yet in its final state */
  window.__rsLeft = () => {
    const p = document.querySelector('#stage .rs-rewards'); if(!p) return { gone: true };
    const bad = [];
    const finiteRunning = el => el.getAnimations().filter(a => { try{ return a.playState === 'running' && a.effect.getComputedTiming().iterations !== Infinity; }catch(e){ return false; } });
    const seq = (typeof resultsSeq !== 'undefined') ? resultsSeq : null;
    const held = !!(seq && seq.isHeld && seq.isHeld());
    /* a scene or pop-up still to come (the reveal running, past a skip, waiting on it): the box it lands in and the buttons
       after it wait for it - the caller then wants to SEE that scene come */
    const pending = !!(seq && seq.isRunning && seq.isRunning()) && !p.classList.contains('rs-done');
    if(pending) window.__scenePending = true;
    const box = p.querySelector('.rs-unlocked');
    p.querySelectorAll('.rs-land').forEach(e => {
      if(e.classList.contains('rs-in-now')) return;
      if(e.classList.contains('rs-in') && !finiteRunning(e).length) return;
      if(box && (e === box || box.contains(e)) && window.__scenePending) return;
      if(window.__scenePending && e.closest('.rs-endslot')) return;
      bad.push('not landed: ' + String(e.className).split(' ').slice(0, 3).join('.'));
    });
    const g = p.querySelector('.rs-grade');
    if(g && (g.classList.contains('is-counting') || g.classList.contains('is-running'))) bad.push('grade counting');
    if(g && g.style.translate) bad.push('grade off its place');
    if(g && g.getAnimations().some(a => a.id === 'rs-grade-rise' && a.playState === 'running')) bad.push('grade rising');
    p.querySelectorAll('.rs-byunit .unit-breakdown-fill[data-to]').forEach(f => {
      if(f.style.getPropertyValue('--fill').trim() !== f.dataset.to) bad.push('unit bar at ' + f.style.getPropertyValue('--fill') + ' of ' + f.dataset.to);
      if(finiteRunning(f).length) bad.push('unit bar moving');
    });
    p.querySelectorAll('.results-level .xpbar-fill').forEach(f => { if(finiteRunning(f).length) bad.push('xp bar moving'); });
    const lv = p.querySelector('.results-level'); if(lv && !p.querySelector('.rs-xp.is-charged')) bad.push('xp not charged');
    const layers = [...document.querySelectorAll('body > .hfx-layer, body > .stardust-layer')].filter(l => +getComputedStyle(l).opacity > .05).length;
    if(layers) bad.push(layers + ' effect layer(s) up');
    if(document.querySelector('[data-skip-hint].is-on')) bad.push('hint up');
    const a = p.querySelector('.rs-actions');
    if(a && !window.__scenePending){
      if(a.closest('.rs-unarmed') || a.classList.contains('rs-unarmed')) bad.push('buttons not live');
      const bs = [...a.querySelectorAll('button')]; if(!bs.length || bs.some(b => __vis(b) < .5)) bad.push('buttons not drawn');
    }
    if(!p.classList.contains('rs-done') && !window.__scenePending) bad.push('not done');
    return { bad, held, pending, done: p.classList.contains('rs-done') };
  };
  /* the numbers and the bars, to say whether anything is still moving */
  window.__rsSnap = () => { const p = document.querySelector('#stage .rs-rewards'); if(!p) return null;
    const T = s => [...p.querySelectorAll(s)].map(e => e.textContent).join('|');
    const B = s => [...p.querySelectorAll(s)].map(e => { const m = new DOMMatrixReadOnly(getComputedStyle(e).transform); return Math.round(m.m41); }).join('|');
    return [T('.rs-pct'), T('.rs-grade-frac'), T('.rs-xptotal-num'), T('.results-level-line'), T('.results-level-num'), B('.unit-breakdown-fill'), B('.xpbar-fill'), document.querySelectorAll('#stage .rs-rewards .rs-in').length].join(' ; '); };
  window.__scenePending = false;
}"""

def open_ctx(br, dev, cls="academy", reduce=False, mute=False, fx="confetti", ios=True):
    _, W, H, dpr = dev
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=dpr, has_touch=True, is_mobile=True)
    if ios: ctx.add_init_script(IOS_CLICKS)
    acct = cb.USED_ACCOUNT
    if cls == "ifc":
        a = json.loads(acct); a["publicId"] = "xph5b57jbp5a"; a["novaMet"] = 99; acct = json.dumps(a)
        ctx.add_init_script("try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
                            "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');"
                            "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
                            "if(!localStorage.getItem('class26e.ifc.drill.v1')) localStorage.setItem('class26e.ifc.drill.v1', %s);}catch(e){}" % json.dumps(acct))
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');"
                        "localStorage.setItem('class26e.drill.v1', %s);}catch(e){}" % json.dumps(cb.USED_ACCOUNT))
    pg = cb.open_page(ctx); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
    pg.on("console", lambda m: errs.append("console: " + m.text[:200]) if m.type == "error" and "ERR_TUNNEL" not in m.text and "Failed to load resource" not in m.text else None)
    pg.set_default_timeout(120000)
    pg.goto(cb.URL, timeout=180000); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.evaluate(SETUP)
    pg.evaluate("""([fx, reduce, mute]) => { store.lifetime.perfectTests = 600; store.hundoFx = fx;
      const u = pendingHomeUnlocks ? pendingHomeUnlocks() : null; if(u) markUnlocksShown(u.chars, u.banners, u.fx);
      theme.reduceMotion = !!reduce; theme.muteBanners = !!mute; try{ applyTheme(); }catch(e){} saveStore(); }""", [fx, reduce, mute])
    pg.wait_for_timeout(1500)
    pg.evaluate("() => { document.getElementById('splashscreen')?.remove(); }")
    pg.evaluate(INSTR)
    cdp = ctx.new_cdp_session(pg)
    return ctx, pg, cdp, errs

def unit_of(pg, cls):
    return pg.evaluate("() => topicsIn(QUESTIONS)[0]") if cls == "ifc" else UNIT

def go(pg, cls="academy", miss=0, mode="drill", practice=False, setup=""):
    pg.evaluate("""([u, m, mode, prac, setup]) => { try{ endResultsReveal(); }catch(e){} showHome(); window.__scenePending = false;
      if(setup) (new Function(setup))();
      __run(u, m, mode, false);
      if(prac){ /* a practice test is an exam with its minutes (summarize reads practiceTestMinutes): rebuild it so */ }
      window.__mountAt = performance.now(); }""", [unit_of(pg, cls), miss, mode, practice, setup])

def tap(cdp, x, y, hold=0.06):
    """a finger down and up `hold` seconds apart, BY THE EVENTS' OWN TIMES (as a phone stamps them): dispatchTouchEvent waits for
    the page to take each event, so on a busy page the lift would otherwise arrive - and be stamped - a second late"""
    p = [{"x": float(x), "y": float(y), "radiusX": 4, "radiusY": 4, "force": 1, "id": 1}]
    t0 = time.time()
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": p, "timestamp": t0})
    time.sleep(max(0.0, hold - (time.time() - t0)))
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": [], "timestamp": t0 + hold})

def wait_js(pg, cond, limit=30.0, step=40):
    t0 = time.time()
    while time.time() - t0 < limit:
        if pg.evaluate(cond): return True
        pg.wait_for_timeout(step)
    return False

def wait_done(pg, limit=60.0):
    return wait_js(pg, "() => { const p = document.querySelector('#stage .rs-rewards'); return !p || p.classList.contains('rs-done'); }", limit, 120)

# the moments of the reveal a tap is sent at: (name, condition to wait for, extra ms after it)
STAGES = [
    ("before the grade lands", "() => !!document.querySelector('#stage .rs-rewards')", 120),
    ("while the grade counts", "() => !!document.querySelector('#stage .rs-grade.is-running')", 700),
    ("during the hundo effect", "() => !!document.querySelector('body > .hfx-layer, body > .stardust-layer')", 500),
    ("while the XP lines come in", "() => !!document.querySelector('#stage .rs-xp.rs-in, #stage .rs-xp.rs-in-now') && !document.querySelector('#stage .rs-xptotal.rs-in-now')", 200),
    ("while the XP bar fills", "() => !!document.querySelector('#stage .rs-xp.is-charging')", 500),
]

def where(pg, dev, kind):
    _, W, H, _ = dev
    if kind == "middle": return (W / 2, H * 0.45)
    if kind == "gutter": return (6, H * 0.55)
    if kind == "hint":
        r = pg.evaluate("() => { const h = document.querySelector('[data-skip-hint]'); if(!h) return null; const b = h.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }")
        return tuple(r) if r else (W / 2, H - 30)

def skip_once(pg, cdp, dev, cond, after, kind="middle", label=""):
    """one tap at a moment of the reveal; True when the results reach their final state within 350ms and stay there"""
    if not wait_js(pg, cond, 40, 20): return None, "the moment never came"
    pg.wait_for_timeout(after)
    if pg.evaluate("() => { const p = document.querySelector('#stage .rs-rewards'); return !p || p.classList.contains('rs-done'); }"):
        return None, "the reveal was over before the tap"
    x, y = where(pg, dev, kind)
    tap(cdp, x, y)
    pg.wait_for_timeout(350)
    left = pg.evaluate("() => __rsLeft()")
    s1 = pg.evaluate("() => __rsSnap()")
    pg.wait_for_timeout(400)
    s2 = pg.evaluate("() => __rsSnap()")
    left2 = pg.evaluate("() => __rsLeft()")
    good = not left.get("gone") and not left["bad"] and s1 == s2 and not left2["bad"]
    d = {"at350": left["bad"], "still": s1 == s2, "at750": left2["bad"], "dropped": pg.evaluate("() => __iosDropped")}
    if good and left.get("pending"):
        # what it is waiting on has to come: a pop-up or a scene, within its beat
        d["then"] = "a pop-up or scene" if wait_js(pg, "() => !!document.querySelector('.rs-spot, .bc-scene, .sf-scene, .fl-scene')", 4, 50) else "NOTHING came"
        good = d["then"] != "NOTHING came"
    return good, d

def s1(br):
    print("\nS1. one tap skips the reveal, at any moment of it, anywhere on the screen")
    for dev in DEVS:
        ctx, pg, cdp, errs = open_ctx(br, dev)
        for name, cond, after in STAGES:
            go(pg)
            r, d = skip_once(pg, cdp, dev, cond, after)
            ck("%s: one tap %s, in the middle of the screen: final in 350ms and still" % (dev[0], name), r is True, d)
            wait_done(pg, 40)
        for kind in ("gutter", "hint"):
            go(pg)
            r, d = skip_once(pg, cdp, dev, STAGES[1][1], STAGES[1][2], kind)
            ck("%s: one tap while it counts, %s: final in 350ms and still" % (dev[0], "in the side gutter" if kind == "gutter" else "on the 'Tap to skip' words"), r is True, d)
            wait_done(pg, 40)
        if dev is MAX:
            for mode, miss, lab in (("exam", 2, "an exam"), ("drill", 3, "a drill with misses")):
                go(pg, miss=miss, mode=mode)
                r, d = skip_once(pg, cdp, dev, STAGES[1][1], STAGES[1][2])
                ck("%s: %s, one tap while it counts: final in 350ms and still" % (dev[0], lab), r is True, d)
                wait_done(pg, 40)
            go(pg, miss=0, mode="exam", setup="const s = summarize; window.summarize = function(){ window.summarize = s; practiceTestMinutes = 60; return s.apply(this, arguments); };")
            r, d = skip_once(pg, cdp, dev, STAGES[3][1], STAGES[3][2])
            ck("%s: a practice-test result, one tap as the XP comes in: final in 350ms and still" % dev[0], r is True, d)
        ck("%s: no page errors" % dev[0], not errs, errs[:3])
        ctx.close()
    # Fire Code
    ctx, pg, cdp, errs = open_ctx(br, MAX, cls="ifc")
    for name, cond, after in (STAGES[1], STAGES[2]):
        go(pg, cls="ifc")
        r, d = skip_once(pg, cdp, MAX, cond, after)
        ck("Fire Code, %s: one tap %s: final in 350ms and still" % (MAX[0], name), r is True, d)
        wait_done(pg, 50)
    ck("Fire Code: no page errors", not errs, errs[:3])
    ctx.close()

def s3(br):
    print("\nS3. the unlock queue is intact: a badge's case still plays after a skip; muted, one tap lands the box")
    dev = MAX
    ctx, pg, cdp, errs = open_ctx(br, dev)
    setup = "store.unitPerfects = {}; store.unitPerfects['%s'] = badgeThresholdFor('%s') - 1; store.badgeSceneOwed = {}; store.badgeScenePlayed = {}; saveStore(); window.__caseAt = 0; window.__caseIv && clearInterval(window.__caseIv); window.__caseIv = setInterval(() => { if(document.querySelector('.bc-scene') && !window.__caseAt) window.__caseAt = performance.now(); }, 50);" % (UNIT, UNIT)
    go(pg, setup=setup)
    pg.evaluate("() => { window.__scenePending = true; }")
    r, d = skip_once(pg, cdp, dev, STAGES[1][1], STAGES[1][2])
    ck("a badge run, one tap while it counts: everything up to the badge's case lands at once", r is True, d)
    came = wait_js(pg, "() => !!document.querySelector('.bc-scene')", 8)
    ck("the badge's case still plays after the skip", came)
    if came:
        pg.wait_for_timeout(900)
        tap(cdp, dev[1] / 2, dev[2] * 0.5)
        pg.wait_for_timeout(500)
        ck("a tap on the case does not end it", pg.evaluate("() => !!document.querySelector('.bc-scene')"))
    wait_js(pg, "() => !document.querySelector('.bc-scene')", 40)
    pg.evaluate("() => { window.__scenePending = false; }")
    wait_js(pg, "() => !!document.querySelector('#stage .rs-unlocked.rs-in, #stage .rs-unlocked.rs-in-now')", 6)
    if not pg.evaluate("() => !!document.querySelector('#stage .rs-rewards.rs-done')"):
        tap(cdp, dev[1] / 2, dev[2] * 0.3)
        pg.wait_for_timeout(350)
    st = pg.evaluate("""(u) => ({ left: __rsLeft().bad, rows: document.querySelectorAll('#stage .rs-unlocked .rs-unlock').length,
      landed: document.querySelectorAll('#stage .rs-unlocked .rs-unlock.rs-in-now, #stage .rs-unlocked .rs-unlock.rs-in').length,
      held: unitBadgeEarned(u), owed: badgeScenesOwed(), played: Object.keys(store.badgeScenePlayed || {}) })""", UNIT)
    ck("after the case: the box with every row landed, the badge held, its scene played, nothing owed",
       not st["left"] and st["rows"] >= 1 and st["landed"] == st["rows"] and st["held"] and UNIT in st["played"] and not st["owed"], st)
    ctx.close()
    ctx, pg, cdp, errs = open_ctx(br, dev, mute=True)
    go(pg, setup=setup)
    r, d = skip_once(pg, cdp, dev, STAGES[1][1], STAGES[1][2])
    st = pg.evaluate("() => ({ rows: document.querySelectorAll('#stage .rs-unlocked .rs-unlock.rs-in-now').length, note: !!document.querySelector('#stage .rs-celebrate-off.rs-in-now'), scene: !!document.querySelector('.bc-scene') })")
    ck("celebrations off, a badge run: one tap lands everything - the box, its rows and its note, the buttons - and no scene", r is True and st["rows"] >= 1 and st["note"] and not st["scene"], [d, st])
    ck("no page errors", not errs, errs[:3])
    ctx.close()

VIS_THEN_TAP = r"""(i) => new Promise(res => {
  const t0 = performance.now();
  const f = () => {
    /* an unlock's pop-up comes first (an account this many tests in crosses a challenge now and then): it is tapped on, as a person does */
    const sp = document.querySelector('.rs-spot');
    if(sp && __vis(sp) > .5 && !window.__spotTapped){ window.__spotTapped = 1; const r = sp.getBoundingClientRect(); res({ spot: true, x: r.left + r.width / 2, y: r.top + r.height / 2 }); return; }
    if(!sp) window.__spotTapped = 0;
    const bs = [...document.querySelectorAll('#stage .rs-rewards .rs-actions button')].filter(b => !b.hidden);
    const b = bs[i];
    if(b){
      const r = b.getBoundingClientRect();
      const on = __vis(b) >= .1 && r.bottom > 0 && r.top < innerHeight && r.width > 0;
      if(!on && __vis(b) >= .1 && (r.top >= innerHeight || r.bottom <= 0)){ window.scrollBy({ top: r.top - innerHeight / 2, behavior: 'instant' }); }
      else if(on){ window.__visAt = performance.now(); res({ n: bs.length, x: r.left + r.width / 2, y: r.top + r.height / 2 }); return; }
    }
    if(performance.now() - t0 > 60000){ res(null); return; }
    requestAnimationFrame(f);
  };
  f();
})"""
TOUCH_AT = "() => { window.__tapAt = 0; window.addEventListener('touchstart', e => { if(!window.__tapAt) window.__tapAt = performance.now(); }, { capture: true, passive: true, once: true }); }"

def press_when_drawn(pg, cdp, i):
    for _ in range(6):
        pg.evaluate(TOUCH_AT)
        p = pg.evaluate(VIS_THEN_TAP, i)
        if not p or not p.get("spot"): break
        tap(cdp, p["x"], p["y"]); pg.wait_for_timeout(700)
    if not p or p.get("spot"): return None, "never drawn"
    tap(cdp, p["x"], p["y"], 0.05)
    lag = pg.evaluate("() => Math.round(__tapAt - __visAt)")
    pg.wait_for_timeout(900)
    left = pg.evaluate("() => !document.querySelector('#stage .rs-rewards')")
    # where it went has to have arrived before the next run is set up (Re-run's test mounts after its loading screen, and would
    # land on top of the next results)
    if left: wait_js(pg, "() => !!document.querySelector('#stage .qpanel .choice, #stage [data-screen=\"home\"], #stage .rs-review')", 15, 100)
    return left, {"tap after drawn ms": lag, "buttons": p["n"], "dropped": pg.evaluate("() => __iosDropped")}

def s4(br):
    print("\nS4. every button under the results takes a tap within 100ms of being drawn")
    for dev in DEVS:
        ctx, pg, cdp, errs = open_ctx(br, dev)
        go(pg, miss=2)
        n = pg.evaluate("() => document.querySelectorAll('#stage .rs-rewards .rs-actions button').length")
        for i in range(n):
            for attempt in range(5):
                go(pg, miss=2)
                wait_js(pg, STAGES[1][1], 30, 20); pg.wait_for_timeout(600)
                tap(cdp, dev[1] / 2, dev[2] * 0.3)
                left, d = press_when_drawn(pg, cdp, i)
                if isinstance(d, dict) and d["tap after drawn ms"] > 100 and attempt < 4: continue   # the harness was slow, not the app
                break
            ck("%s: after a skip, button %d of %d takes a tap %sms after it is drawn" % (dev[0], i + 1, n, d.get("tap after drawn ms") if isinstance(d, dict) else "?"),
               left is True and isinstance(d, dict) and d["tap after drawn ms"] <= 100, d)
        for attempt in range(5):
            go(pg, miss=2)
            left, d = press_when_drawn(pg, cdp, n - 1)
            if isinstance(d, dict) and d["tap after drawn ms"] > 100 and attempt < 4: continue
            break
        ck("%s: a reveal left alone, the last button takes a tap %sms after it is drawn" % (dev[0], d.get("tap after drawn ms") if isinstance(d, dict) else "?"),
           left is True and isinstance(d, dict) and d["tap after drawn ms"] <= 100, d)
        ck("%s: no page errors" % dev[0], not errs, errs[:3])
        ctx.close()
    ctx, pg, cdp, errs = open_ctx(br, MAX, reduce=True)
    for attempt in range(5):
        go(pg, miss=2)
        pg.wait_for_timeout(300)
        st = pg.evaluate("() => __rsLeft()")
        left, d = press_when_drawn(pg, cdp, 0)
        if isinstance(d, dict) and d["tap after drawn ms"] > 100 and attempt < 4: continue
        break
    ck("Reduce motion: everything in place at once, no hint", not st.get("bad"), st)
    ck("Reduce motion: the first button takes a tap %sms after it is drawn" % (d.get("tap after drawn ms") if isinstance(d, dict) else "?"),
       left is True and isinstance(d, dict) and d["tap after drawn ms"] <= 100, d)
    ck("Reduce motion: no page errors", not errs, errs[:3])
    ctx.close()

def s5(br):
    print("\nS5. kept: a tap meant for the screen never presses a button that came up under it (305/380/382; pass on both builds)")
    for dev in DEVS:
        ctx, pg, cdp, errs = open_ctx(br, dev)
        go(pg)
        wait_js(pg, "() => !!document.querySelector('#stage .rs-rewards .rs-actions button')", 10, 20)
        spot = pg.evaluate("() => { const bs = [...document.querySelectorAll('#stage .rs-rewards .rs-actions button')]; const b = bs[bs.length - 1]; const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
        tap(cdp, spot[0], spot[1])
        wait_done(pg, 40); pg.wait_for_timeout(1200)
        ck("%s: a tap where the last button will be, before it is there: still on the results" % dev[0],
           pg.evaluate("() => !!document.querySelector('#stage .rs-rewards')"))
        # taps that keep coming at that spot, from the start until well after the buttons are up
        go(pg)
        wait_js(pg, "() => !!document.querySelector('#stage .rs-rewards .rs-actions button')", 10, 20)
        spot = pg.evaluate("() => { const bs = [...document.querySelectorAll('#stage .rs-rewards .rs-actions button')]; const b = bs[bs.length - 1]; const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
        up_at = None; t0 = time.time(); stayed = True
        while time.time() - t0 < 25:
            tap(cdp, spot[0], spot[1], 0.04); pg.wait_for_timeout(250)
            if not pg.evaluate("() => !!document.querySelector('#stage .rs-rewards')"): stayed = False; break
            if up_at is None and pg.evaluate("() => { const p = document.querySelector('#stage .rs-rewards'); return !!(p && p.classList.contains('rs-done')); }"): up_at = time.time()
            if up_at and time.time() - up_at > 1.6: break
            # the last button may have been carried: follow it (its spot is what is being tapped at)
            sp = pg.evaluate("() => { const bs = [...document.querySelectorAll('#stage .rs-rewards .rs-actions button')]; const b = bs[bs.length - 1]; if(!b) return null; const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
            if sp: spot = sp
        ck("%s: taps every 250ms at that spot, through the buttons' arrival and 1.6s past it: none pressed" % dev[0], stayed and up_at is not None, {"stayed": stayed, "done": up_at is not None})
        pg.wait_for_timeout(900)
        tap(cdp, spot[0], spot[1]); pg.wait_for_timeout(900)
        ck("%s: and the first tap there after a pause presses it" % dev[0], pg.evaluate("() => !document.querySelector('#stage .rs-rewards')"))
        ck("%s: no page errors" % dev[0], not errs, errs[:3])
        ctx.close()

# ---------------------------------------------------------------- S6: the bars, at 4x CPU
LAGI = r"""() => {
  window.__ph = {}; window.__bw = { count: 0, fill: 0 }; window.__cl = { count: 0, fill: 0 }; window.__rw = { count: [], fill: [] };
  window.__frames = []; const fr = t => { __frames.push(t); requestAnimationFrame(fr); }; requestAnimationFrame(fr);
  window.__sync = []; window.__barTrace = [];
  const phase = () => __ph.count && !__ph.countEnd ? 'count' : __ph.fill && !__ph.fillEnd ? 'fill' : null;
  const mk = n => { try{ performance.mark('rs:' + n); }catch(e){} };
  new MutationObserver(ms => ms.forEach(m => {
    const el = m.target, c = el.classList;
    if(m.type === 'attributes' && m.attributeName === 'class' && c){
      if(c.contains('rs-grade') && c.contains('is-running') && !__ph.count){ __ph.count = performance.now(); mk('count'); }
      if(c.contains('rs-grade') && c.contains('rs-graded') && !__ph.countEnd){ __ph.countEnd = performance.now(); mk('countEnd'); }
      if(c.contains('rs-xp') && c.contains('is-charging') && !__ph.fill){ __ph.fill = performance.now(); mk('fill'); }
      if(c.contains('rs-xp') && c.contains('is-charged') && !__ph.fillEnd && __ph.fill){ __ph.fillEnd = performance.now(); mk('fillEnd'); }
    }
    const ph = phase(); if(!ph) return;
    if(m.type === 'attributes' && m.attributeName === 'style' && c && (c.contains('unit-breakdown-fill') || c.contains('xpbar-fill'))) __bw[ph]++;
    if(m.type === 'childList' && (m.addedNodes.length || m.removedNodes.length)) __cl[ph]++;
  })).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class', 'style'], childList: true });
  /* (pass B only: reading a bar's place each frame forces a style pass and a layout, so it is never on in the traced pass)
     each frame of the count and the fill: a bar that moved since the last frame - was it moved by a running transform-only
     animation; the warm-ups' wait; the XP number against its bar */
  if(!window.__look) return;
  const last = new Map();
  const look = () => {
    const ph = phase();
    if(ph){
      const bars = ph === 'count' ? [...document.querySelectorAll('#stage .rs-byunit .unit-breakdown-fill')] : [...document.querySelectorAll('#stage .results-level .xpbar-fill')];
      bars.forEach(b => {
        const an = b.getAnimations().filter(a => a.playState === 'running' && (() => { try{ const ks = a.effect.getKeyframes(); return ks.every(k => Object.keys(k).filter(x => !['offset','easing','composite','computedOffset'].includes(x)).every(x => x === 'transform')); }catch(e){ return false; } })() && a.effect.getComputedTiming().iterations !== Infinity);
        const m = new DOMMatrixReadOnly(getComputedStyle(b).transform), w = b.offsetWidth || 1, f = Math.max(0, Math.min(1, 1 + m.m41 / w));
        if(last.has(b) && Math.abs(f - last.get(b)) > .0005) __rw[ph].push(an.length > 0 ? 1 : 0);
        last.set(b, f);
        if(ph === 'fill') __barTrace.push([performance.now(), f, (document.querySelector('#stage .results-level-num') || {}).textContent || '', (document.querySelector('#stage .results-level-line') || {}).textContent || '']);
      });
      try{ __rw[ph + 'Wait'] = Math.min(__rw[ph + 'Wait'] == null ? 1e9 : __rw[ph + 'Wait'], recordingShouldWait()); }catch(e){}
    }
    requestAnimationFrame(look);
  };
  requestAnimationFrame(look);
}"""

def lag_pass(br, setup, look):
    """one 100% run at 4x CPU; look=False is the traced pass (nothing of the gate's own reads the layout), look=True the pass that
    reads each bar's place every frame"""
    dev = MAX
    ctx, pg, cdp, errs = open_ctx(br, dev, ios=False)
    events = []; done = {"v": False}
    cdp.on("Tracing.dataCollected", lambda p: events.extend(p["value"]))
    cdp.on("Tracing.tracingComplete", lambda p: done.update(v=True))
    pg.evaluate("(l) => { window.__look = l; }", look)
    pg.evaluate(LAGI)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    if not look: cdp.send("Tracing.start", {"categories": "devtools.timeline,disabled-by-default-devtools.timeline,blink.user_timing,v8.execute", "transferMode": "ReportEvents"})
    go(pg, setup=setup)
    t0 = time.time()
    while time.time() - t0 < 90 and not pg.evaluate("() => !!(__ph.fillEnd || document.querySelector('#stage .rs-rewards.rs-done'))"): pg.wait_for_timeout(250)
    pg.wait_for_timeout(300)
    if not look:
        cdp.send("Tracing.end")
        while not done["v"]: pg.wait_for_timeout(100)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    st = pg.evaluate("() => ({ ph: __ph, bw: __bw, cl: __cl, rw: { count: __rw.count.length ? __rw.count.reduce((a, b) => a + b, 0) / __rw.count.length : null, fill: __rw.fill.length ? __rw.fill.reduce((a, b) => a + b, 0) / __rw.fill.length : null, countWait: __rw.countWait, fillWait: __rw.fillWait }, frames: __frames, bar: __barTrace })")
    ctx.close()
    return events, st, errs

def lag_run(br, label, setup):
    events, st, errs = lag_pass(br, setup, False)
    _, stB, errsB = lag_pass(br, setup, True)
    errs = errs + errsB
    st["rw"] = stB["rw"]; st["bar"] = stB["bar"]
    marks = {e["name"][3:]: e["ts"] for e in events if e.get("name", "").startswith("rs:") and e.get("cat") == "blink.user_timing"}
    rend = [e for e in events if e.get("name") == "thread_name" and e["args"]["name"] == "CrRendererMain"]
    pid, tid = rend[0]["pid"], rend[0]["tid"]
    main = sorted([e for e in events if e.get("pid") == pid and e.get("tid") == tid and e.get("ph") == "X"], key=lambda e: e["ts"])
    JS = ("FunctionCall", "FireAnimationFrame", "TimerFire", "FireIdleCallback", "EventDispatch", "RunMicrotasks", "EvaluateScript", "v8.callFunction")
    def forced(a, b):
        js = [(e["ts"], e["ts"] + e.get("dur", 0)) for e in main if e["name"] in JS and a <= e["ts"] <= b]
        n = 0
        for e in main:
            if e["name"] in ("Layout", "UpdateLayoutTree") and a <= e["ts"] <= b and any(s <= e["ts"] <= t for s, t in js): n += 1
        return n
    res = {}
    for ph, a, b in (("count", "count", "countEnd"), ("fill", "fill", "fillEnd")):
        if a in marks and b in marks:
            A, B = marks[a], marks[b]
            fs = [f for f in st["frames"] if st["ph"].get(a) and st["ph"][a] <= f <= st["ph"][b]] if st["ph"].get(b) else []
            gaps = [fs[i + 1] - fs[i] for i in range(len(fs) - 1)]
            gaps.sort()
            res[ph] = {"ms": round((B - A) / 1000), "forced": forced(A, B), "barWrites": st["bw"][ph], "nodes": st["cl"][ph], "animated": st["rw"][ph],
                       "warmupWait": st["rw"].get(ph + "Wait"), "frames": len(fs),
                       "p50": round(gaps[len(gaps) // 2]) if gaps else None, "p95": round(gaps[int(len(gaps) * .95)]) if gaps else None, "max": round(gaps[-1]) if gaps else None}
    return res, st, errs

def s6(br):
    print("\nS6. the bars do not lag (4x CPU, %s %dx%d @%dx)" % MAX)
    climb = ("const p = (() => { for(let q = 0; q < 200000; q += 25){ const a = levelStateOf(q, 0, 0, 0), b = levelStateOf(q + 420, 0, 0, 0); if(b.level === a.level + 1 && !levelBarOf(b).over && !levelBarOf(a).over) return q; } return 0; })();"
             " store.lifetime.points = p; store.levelFloor = 0; store.rankFloor = 0; saveStore();")
    for label, setup in (("a 100% run", ""), ("a 100% run that climbs a level", climb)):
        res, st, errs = lag_run(br, label, setup)
        for ph in ("count", "fill"):
            r = res.get(ph)
            if not r: ck("%s: the %s was reached" % (label, ph), False, res); continue
            info("%s, %s (frame pacing, printed not judged)" % (label, ph), {k: r[k] for k in ("ms", "frames", "p50", "p95", "max")})
            ck("%s, while the %s: every bar moved by a running transform animation (share of bar-frames)" % (label, "grade counts" if ph == "count" else "XP bar fills"),
               r["animated"] is not None and r["animated"] >= .95, r["animated"])
            ck("%s, %s: style writes on the bars - a few, not one a frame" % (label, ph), r["barWrites"] <= 8, r["barWrites"])
            ck("%s, %s: no layout or style pass forced by script" % (label, ph), r["forced"] <= 3, r["forced"])
            ck("%s, %s: the counting numbers make no elements" % (label, ph), r["nodes"] <= 4, r["nodes"])
            ck("%s, %s: the warm-ups wait it out" % (label, ph), (r["warmupWait"] or 0) > 0, r["warmupWait"])
        bar = st["bar"]
        if bar:
            # the number with its bar: the "have" figure over the span against the bar's place (a wall: the number may run on past a full bar)
            off = []
            for t, f, lvl, line in bar:
                try:
                    have, span = [int(x.replace(",", "")) for x in line.replace("XP", "").split("/")]
                    if span > 0 and have <= span: off.append(abs(have / span - f))
                except Exception: pass
            worst = max(off) if off else None
            ck("%s: the XP number counts with its bar (worst gap, as a share of the bar)" % label, worst is not None and worst <= .1, round(worst, 3) if worst is not None else bar[:3])
            if "climbs" in label:
                fs = [f for _, f, _, _ in bar]; lv = [l for _, _, l, _ in bar]
                top = max(range(len(fs)), key=lambda i: fs[i]) if fs else 0
                full_then_empty = any(fs[i] > .97 and any(x < .08 for x in fs[i:]) for i in range(len(fs)))
                after = [x for x in fs[[i for i in range(len(fs)) if fs[i] < .08][-1]:]] if any(x < .08 for x in fs) else []
                nums = sorted({''.join(ch for ch in l if ch.isdigit()) for l in lv if any(ch.isdigit() for ch in l)})
                ck("%s: the wrap reads - full, empty, filling again, the level one higher" % label,
                   full_then_empty and after and after[-1] > .05 and len(nums) >= 2, {"full then empty": full_then_empty, "refill end": round(after[-1], 3) if after else None, "levels shown": nums})
        ck("%s: no page errors" % label, not errs, errs[:3])

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    try:
        if want("S1"): s1(br)
        if want("S3"): s3(br)
        if want("S4"): s4(br)
        if want("S5"): s5(br)
        if want("S6"): s6(br)
    finally:
        br.close()
cb.SERVER.shutdown()
print("\n" + ("ALL PASS" if ok else "FAILED: " + "; ".join(FAILS)))
sys.exit(0 if ok else 1)
