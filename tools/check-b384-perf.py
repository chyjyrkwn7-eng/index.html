"""Build 384, the Safari and laptop performance pass. Madison: "Ensure safari and laptop runs well. THIS A HUGE One." and "The review
section, while scrolling down the questions are populating as you scroll and you can see it happening real time. Fix that, they
should already be loaded as you scroll so it's super smooth."
Read off the page in Chromium (WebKit cannot run here), both classes (the academy and Fire Code), a laptop (1536x864 at 1.25x, a
mouse, a Windows user agent, a browser tab) and an iPhone (440x956 at 3x, touch, Safari's user agent with no requestIdleCallback,
installed). Shapes and counts, never frame times:
(1) REVIEW IS LAID OUT AHEAD OF THE SCROLL (the biggest unit of each class: the academy's Penal Code, Fire Code's longest chapter):
    a. opened, and scrolled at a steady 3,000px/s from 300ms after it opens with the CPU slowed 4x: in no frame is a question on
       screen, or within a screen and a half below it, still unlaid-out (content-visibility skipped);
    b. opened and left alone (CPU at full speed): every question of the unit is laid out within 25s;
    c. that pass works in slices (its own log, window.__rqLog): more than one, none laying out more than 64 questions - never the
       whole unit in one task; the slowest slice's time is printed as INFO;
    d. Safari's way (no scroll anchoring, emulated: overflow-anchor off and CSS.supports saying so), the iPhone, academy: opened and
       at once jumped 30,000px down - the question in the middle of the screen moves no more than 2px over 12s while every question
       above and below it is laid out.
(2) A TRIP TO PROFILE AND BACK TO HOME (real taps on the bar): no whole-page style pass forced by the status-bar colour read
    (a style recalc over more than half the page whose stack is cssColorHexNow) - on the installed iPhone and the laptop; and on the
    laptop no write of --tabbar-half on <html> (a custom property every element inherits) while Home's width for the bar is unchanged.
(3) NO BACKDROP FILTER ON WHAT CANNOT BE SEEN: on Home, Profile, the Leaderboard (Fire Code: Stats), the Calendar (Fire Code:
    Settings) and Settings, no element carries a backdrop-filter while it, or an ancestor, is at opacity 0 / visibility hidden or it
    is under 4px a side (WebKit makes every backdrop filter a layer that reads back what is under it).
(4) no page errors.
Run:  python3 tools/check-b384-perf.py [--against REV] [--only 1,2,3]   (--against 1dca98e must FAIL (1)(2)(3))"""
import functools, http.server, json, os, re, socket, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    import glob as _g; CHROME = (sorted(_g.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
def want(n): return ONLY is None or str(n) in ONLY
if "--against" in sys.argv:
    SRC = subprocess.check_output(["git", "-C", ROOT, "show", sys.argv[sys.argv.index("--against") + 1] + ":index.html"]).decode("utf-8")
else:
    SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
BUILD = (re.search(r'const APP_BUILD = "([^"]+)"', SRC) or [None, ""])[1]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
def info(s): print("INFO " + s, flush=True)
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
def body_for(ins):
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return INSET_RE.sub(lambda m: v[m.group(1)], SRC)
def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/index.html" % port
URL = serve()
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
DEV = {"laptop": dict(viewport={"width": 1536, "height": 864}, device_scale_factor=1.25, has_touch=False, is_mobile=False, user_agent=WIN_UA),
       "phone": dict(viewport={"width": 440, "height": 956}, device_scale_factor=3, has_touch=True, is_mobile=True, user_agent=IPHONE_UA)}
INS = {"laptop": (0, 0, 0, 0), "phone": (62, 0, 34, 0)}
STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
  ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}} : mm(q); })();"""
NO_RIC = "try{ delete window.requestIdleCallback; delete window.cancelIdleCallback; window.requestIdleCallback = undefined; window.cancelIdleCallback = undefined; }catch(e){}"
FAKE = """(function(){ function snap(){ return { empty:true, size:0, docs:[], docChanges:function(){return [];}, metadata:{fromCache:false}, forEach:function(){} }; }
  function doc(){ return { get:function(){ return Promise.resolve({ exists:false, data:function(){ return null; } }); }, set:function(){ return Promise.resolve(); }, update:function(){ return Promise.resolve(); }, delete:function(){ return Promise.resolve(); },
    onSnapshot:function(){ var n=[].slice.call(arguments).filter(function(x){ return typeof x==='function'; })[0]; setTimeout(function(){ n({ exists:false, id:'x', data:function(){ return null; }, metadata:{fromCache:false, hasPendingWrites:false} }); }, 40); return function(){}; },
    collection:function(){ return coll(); } }; }
  function coll(){ var c = { doc:doc, where:function(){ return c; }, orderBy:function(){ return c; }, limit:function(){ return c; }, get:function(){ return Promise.resolve(snap()); },
    onSnapshot:function(){ var n=[].slice.call(arguments).filter(function(x){ return typeof x==='function'; })[0]; setTimeout(function(){ n(snap()); }, 60); return function(){}; } }; return c; }
  var db = { collection:coll, batch:function(){ return { set:function(){}, update:function(){}, delete:function(){}, commit:function(){ return Promise.resolve(); } }; } };
  var fs = function(){ return db; }; fs.FieldValue = { delete:function(){ return null; }, serverTimestamp:function(){ return Date.now(); }, arrayUnion:function(){ return [].slice.call(arguments); }, increment:function(n){ return n; } };
  window.firebase = { apps:[], initializeApp:function(){ this.apps.push({}); }, firestore:fs }; })();"""
def week_key_now():
    import datetime
    d = datetime.date.today(); d -= datetime.timedelta(days=d.weekday()); return d.isoformat()
SEED = {"firstName": "Casey", "avatarChar": "ninja", "onboardingComplete": True, "weekKey": week_key_now(), "weekPoints": 640, "leaderboardOptIn": True,
        "lastModified": 1700000000000, "publicId": "xph5b57jbp5a", "novaMet": 99, "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True,
        "seenModeSelectTour": True, "seenUnitSelectTour": True, "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True,
        "novaHeard": {"@recap": 99991231}, "unitPerfects": {"Penal Code": 35, "TCOLE Rules": 35, "Racial Profiling": 22},
        "lifetime": {"points": 12400, "answered": 5400, "correct": 4980, "drillPlays": 64, "examPlays": 22, "perfectTests": 141, "currentStreak": 23, "longestStreak": 57}}
SEEN = ["freshstart", "intro.seen", "unithold.tip", "daily.seen", "savecode.asked", "savecode.card", "getstarted", "penal55124.seen", "penal124256.seen", "penal256578.seen"]
def init_js(cls):
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.intro.seen','99');"   # What's New seen: its card would cover the bar
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3845');" % json.dumps(json.dumps(SEED))
    s += "localStorage.setItem('class26e.classseen', JSON.stringify(['academy','ifc'])); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
    if cls == "ifc":
        ifc = dict(SEED); ifc["unitPerfects"] = {}; ifc["lifetime"] = dict(SEED["lifetime"], points=4321, correct=777, perfectTests=30)
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc))
    return s + " }catch(e){} })()"
def open_page(br, dev, cls, extra=()):
    ctx = br.new_context(**DEV[dev])
    if dev == "phone": ctx.add_init_script(NO_RIC); ctx.add_init_script(STANDALONE)
    for e in extra: ctx.add_init_script(e)
    ctx.add_init_script(FAKE); ctx.add_init_script(init_js(cls))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = body_for(INS[dev])
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "note": "", "frameId": "", "force": True, "safariSound": True})))
    cdp = ctx.new_cdp_session(pg)
    pg.goto(URL)
    for _ in range(320):
        if pg.evaluate("()=>!!document.querySelector('#stage .screen-home-actual') && !document.getElementById('splashscreen')"): break
        pg.wait_for_timeout(250)
    # an account with nothing owed: no rank-up waiting (the Profile tab would open its journey instead)
    pg.evaluate("""()=>{ try{ store.rankUpShown = TIER_ORDER_FULL.length; store.seenUnlockedTiers = TIER_ORDER_FULL.slice(); saveStore();
      document.body.classList.remove('rankup-lock'); document.querySelectorAll('.ru-nudge').forEach(n => n.classList.remove('ru-nudge')); }catch(e){}
      /* ...and nothing waiting to be unlocked on Home (its cutscene takes the bar away) */
      try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
      try{ homeUnlocksOwed = () => false; }catch(e){} }""")
    for _ in range(40):
        if not pg.evaluate("()=>document.body.classList.contains('cutscene-focus')"): break
        pg.evaluate("()=>{ const s = document.querySelector('.rs-spot.is-up'); if(s) s.click(); }"); pg.wait_for_timeout(500)
    pg.evaluate("""()=>{ document.getElementById('splashscreen')?.remove();
      for(let i=0;i<3;i++) [...document.querySelectorAll('button')].filter(b=>/^(Got it|Not now|Later)$/i.test(b.textContent.trim()) && b.offsetParent).forEach(b=>b.click());
      document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner,.rs-spot,.unlock-card').forEach(e=>e.remove()); }""")
    return ctx, pg, cdp, errs
ALLERR = []
REVIEW_PROBE = r"""()=>{
  const rows = () => [...document.querySelectorAll('#stage .screen-answerreview .review-question')].filter(r => !r.hidden);
  const skipped = r => { const c = r.firstElementChild; return !!c && !c.checkVisibility({ contentVisibilityAuto: true }); };
  window.__rvRows = rows; window.__rvSkipped = skipped;
  window.__rvScroll = (speed, ms) => new Promise(res => {
    const R = window.__rv = { frames: 0, inView: 0, near: 0, nearest: null, y0: window.scrollY };
    const t0 = performance.now(); let last = t0; const vh = innerHeight; let y = window.scrollY;
    const step = t => {
      const dt = t - last; last = t; R.frames++;
      for(const r of rows()){
        const b = r.getBoundingClientRect();
        if(b.bottom < 0 || b.top > vh * 2.5 || !skipped(r)) continue;
        if(b.top < vh && b.bottom > 0) R.inView++; else { R.near++; R.nearest = R.nearest === null ? Math.round(b.top - vh) : Math.min(R.nearest, Math.round(b.top - vh)); }
      }
      if(t - t0 < ms){ y += speed * dt / 1000; window.scrollTo({ top: y, behavior: 'instant' }); requestAnimationFrame(step); } else { R.y = Math.round(window.scrollY - R.y0); res(R); }
    };
    requestAnimationFrame(step);
  });
  return true; }"""
BIGGEST = "()=>{ const c={}; QUESTIONS.forEach(q=>{ if(typeof inWholeUnit==='function' && !inWholeUnit(q)) return; const t=(q.topic||'').trim(); c[t]=(c[t]||0)+1; }); return Object.entries(c).sort((a,b)=>b[1]-a[1])[0]; }"
OPEN = """(u)=>new Promise(res=>{ window.scrollTo(0,0); window.__rqLog=[]; const t0=performance.now(); showAnswerReview([u], 'all', null);
  requestAnimationFrame(()=>requestAnimationFrame(()=>res(Math.round(performance.now()-t0)))); })"""
CENTRE = "(sel)=>{ const b=document.querySelector(sel); if(!b) return null; const r=b.getBoundingClientRect(); if(!r.width) return null; return [r.left+r.width/2, r.top+r.height/2]; }"
UNCOVER = r"""(sel)=>{ const t = document.querySelector(sel); if(!t) return []; const gone = [];
  for(let i = 0; i < 5; i++){ const r = t.getBoundingClientRect(); const e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if(!e || t.contains(e) || e.closest('#bottomtabs')) break;
    let top = e; while(top.parentElement && top.parentElement !== document.body) top = top.parentElement;
    if(top.classList.contains('wrap') || top.id === 'bottomtabs') break;
    gone.push((top.id ? '#' + top.id : top.tagName.toLowerCase()) + '.' + String(top.className).split(' ')[0]); top.remove(); }
  return gone; }"""
def tap(pg, cdp, dev, sel):
    # a notice or tip that came up over the bar is not what is measured: it goes first (and is reported)
    gone = pg.evaluate(UNCOVER, sel)
    if gone: info("cleared over %s before the tap: %s" % (sel, gone))
    c = pg.evaluate(CENTRE, sel)
    if not c: return False
    if dev == "phone":
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c[0], "y": c[1]}]}); time.sleep(0.07)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    else:
        pg.mouse.move(c[0], c[1], steps=4); pg.mouse.click(c[0], c[1])
    return True
TRACE = os.path.join("/tmp", "b384perf-%d.json" % os.getpid())
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    # ---------------------------------------------------------------- (1) Review
    if want(1):
        for cls, dev in (("academy", "laptop"), ("ifc", "phone"), ("academy", "phone"), ("ifc", "laptop")):
            ctx, pg, cdp, errs = open_page(br, dev, cls)
            pg.wait_for_timeout(6000)
            unit, n = pg.evaluate(BIGGEST)
            pg.evaluate(REVIEW_PROBE)
            # a: 4x CPU, scroll from 300ms after the open
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            pg.evaluate(OPEN, unit); pg.wait_for_timeout(300)
            r = pg.evaluate("()=>__rvScroll(3000, 4000)")
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            chk("(1a) %s %s: Review of %s (%d), scrolled at 3,000px/s from 300ms after opening at 4x CPU (%dpx, %d frames): no question on screen unlaid-out (%d) or within 1.5 screens below (%d, nearest %s px below)" % (
                cls, dev, unit[:28], n, r["y"], r["frames"], r["inView"], r["near"], r["nearest"]), r["inView"] == 0 and r["near"] == 0 and r["y"] > 4000, r)
            # b, c: full speed, opened and left alone
            pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2000)
            t_open = [pg.evaluate(OPEN, unit)]
            left = None; t0 = time.time()
            while time.time() - t0 < 25:
                left = pg.evaluate("()=>__rvRows().filter(__rvSkipped).length")
                if left == 0: break
                pg.wait_for_timeout(500)
            took = time.time() - t0
            total = pg.evaluate("()=>__rvRows().length")
            chk("(1b) %s %s: opened and left alone, every question laid out (%d of %d still not, after %.1fs)" % (cls, dev, left, total, took), left == 0 and total >= n * .9, [left, total])
            log = pg.evaluate("()=>window.__rqLog || []")
            worst = max([x[1] for x in log] or [0]); most = max([x[0] for x in log] or [0])
            chk("(1c) %s %s: laid out in slices, never the unit in one go (%d slices for %d questions, at most %d in one)" % (cls, dev, len(log), sum(x[0] for x in log), most),
                len(log) > 1 and 0 < most <= 64, log[:12])
            info("(1c) %s %s: the slowest slice took %.1fms (wall clock, this machine's load included)" % (cls, dev, worst))
            for _ in range(2):
                pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500); t_open.append(pg.evaluate(OPEN, unit))
            info("(1) %s %s: Review open to its second frame (full CPU) %s ms" % (cls, dev, t_open))
            ALLERR.extend(errs); ctx.close()
        # d: Safari's way - no scroll anchoring. Jumped far down right after opening, the question in the middle of the screen
        # stays where it is while everything above it is laid out (the page moves by what they grew, at once)
        NOANCHOR = """(()=>{ const s = CSS.supports.bind(CSS); CSS.supports = function(a){ if(String(a).indexOf('overflow-anchor') >= 0) return false; return s.apply(CSS, arguments); };
          addEventListener('DOMContentLoaded', () => { const st = document.createElement('style'); st.textContent = 'html, body, *{ overflow-anchor:none !important; }'; document.head.appendChild(st); }); })()"""
        ctx, pg, cdp, errs = open_page(br, "phone", "academy", extra=(NOANCHOR,))
        pg.wait_for_timeout(5000)
        unit, n = pg.evaluate(BIGGEST)
        pg.evaluate(REVIEW_PROBE)
        pg.evaluate("(u)=>{ window.scrollTo(0,0); showAnswerReview([u], 'all', null); }", unit); pg.wait_for_timeout(60)
        pg.evaluate("()=>window.scrollTo({ top: 30000, behavior: 'instant' })"); pg.wait_for_timeout(200)
        pg.evaluate("""()=>{ const mid = innerHeight / 2; window.__mark = __rvRows().find(q => { const b = q.getBoundingClientRect(); return b.top < mid && b.bottom > mid; });
          window.__tops = []; const t0 = performance.now();
          const f = () => { if(window.__mark) window.__tops.push(window.__mark.getBoundingClientRect().top); if(performance.now() - t0 < 12000) requestAnimationFrame(f); }; requestAnimationFrame(f); }""")
        pg.wait_for_timeout(12500)
        tops = pg.evaluate("()=>window.__tops"); left = pg.evaluate("()=>__rvRows().filter(__rvSkipped).length")
        moved = (max(tops) - min(tops)) if tops else -1
        chk("(1d) no scroll anchoring (Safari), jumped to 30,000px just after opening: the question mid-screen moves %.1fpx while the %d above and below are laid out (%d still not)" % (moved, n, left),
            tops and moved <= 2 and left == 0, [moved, left, tops[:3], tops[-3:]])
        ALLERR.extend(errs); ctx.close()
    # ---------------------------------------------------------------- (2) a trip to Profile and back to Home
    if want(2):
        for dev in ("phone", "laptop"):
            ctx, pg, cdp, errs = open_page(br, dev, "academy")
            pg.wait_for_timeout(12000)
            pg.evaluate("""()=>{ window.__half = []; new MutationObserver(()=>{ const v = document.documentElement.style.getPropertyValue('--tabbar-half');
              if(v !== window.__lastHalf){ window.__half.push(v); window.__lastHalf = v; } }).observe(document.documentElement, { attributes: true, attributeFilter: ['style'] });
              window.__lastHalf = document.documentElement.style.getPropertyValue('--tabbar-half'); }""")
            els = pg.evaluate("()=>document.getElementsByTagName('*').length")
            br.start_tracing(page=pg, path=TRACE, categories=["devtools.timeline", "disabled-by-default-devtools.timeline", "disabled-by-default-devtools.timeline.stack"])
            landed = []
            for t, scr in (("#bottomtab-profile", ".screen-profile"), ("#bottomtab-home", ".screen-home-actual"), ("#bottomtab-profile", ".screen-profile"), ("#bottomtab-home", ".screen-home-actual")):
                tap(pg, cdp, dev, t); pg.wait_for_timeout(2600)
                landed.append(pg.evaluate("(s)=>!!document.querySelector('#stage > ' + s)", scr))
            br.stop_tracing()
            ev = json.load(open(TRACE)); ev = ev["traceEvents"] if isinstance(ev, dict) else ev
            forced = []; whole = 0
            for e in ev:
                if e.get("name") == "UpdateLayoutTree" and e.get("ph") == "X":
                    ec = (e.get("args", {}) or {}).get("elementCount") or 0
                    if ec > els * .5:
                        whole += 1
                        stk = ((e.get("args", {}) or {}).get("beginData") or {}).get("stackTrace") or []
                        if any((f.get("functionName") or "") == "cssColorHexNow" for f in stk): forced.append(ec)
            try: os.remove(TRACE)
            except Exception: pass
            chk("(2) %s: Home -> Profile -> Home twice by real taps (each landed: %s): no whole-page style pass forced by the status-bar colour read (%d of %d whole-page passes)" % (dev, landed, len(forced), whole),
                all(landed) and whole > 0 and not forced, [landed, whole, forced])
            meta = pg.evaluate("()=>({ meta: (document.getElementById('themecolor')||{}).content, want: appTopEdgeColor(), home: !!document.querySelector('#stage .screen-home-actual') })")
            info("(2) %s: back on Home %s, theme-color %s = the sky's top colour %s" % (dev, meta["home"], meta["meta"], meta["want"]))
            if dev == "laptop":
                half = pg.evaluate("()=>window.__half")
                chk("(2) laptop: no --tabbar-half written on <html> for the trips (Home's bar the same width each time; written %s)" % half, not half, half)
            ALLERR.extend(errs); ctx.close()
    # ---------------------------------------------------------------- (3) no backdrop filter on what cannot be seen
    if want(3):
        BF = r"""()=>{ const out = [];
          for(const el of document.querySelectorAll('body *')){
            const cs = getComputedStyle(el); const bf = cs.backdropFilter || cs.webkitBackdropFilter;
            if(!bf || bf === 'none' || cs.display === 'none') continue;
            const r = el.getBoundingClientRect();
            let hidden = r.width < 4 || r.height < 4, p = el;
            while(!hidden && p && p.nodeType === 1){ const s = getComputedStyle(p); if(+s.opacity === 0 || s.visibility === 'hidden') hidden = true; p = p.parentElement; }
            if(hidden && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)
              out.push((el.id ? '#' + el.id : el.tagName.toLowerCase()) + '.' + String(el.className).split(' ')[0] + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
          }
          return out; }"""
        for cls, dev in (("academy", "phone"), ("ifc", "laptop")):
            ctx, pg, cdp, errs = open_page(br, dev, cls)
            pg.wait_for_timeout(3000)
            bad = {}
            screens = (("home", "showHome()"), ("profile", "showProfile()"), ("board", "showRankings()"), ("settings", "showAppearance()")) + ((("calendar", "showCalendar()"),) if cls != "ifc" else ())
            for name, js in screens:
                pg.evaluate("()=>{ %s }" % js); pg.wait_for_timeout(2500)
                b = pg.evaluate(BF)
                if b: bad[name] = b
            chk("(3) %s %s: no backdrop-filter on an element that cannot be seen, on %s (%s)" % (cls, dev, ", ".join(s[0] for s in screens), bad), not bad, bad)
            ALLERR.extend(errs); ctx.close()
    chk("(4) no page errors", not ALLERR, ALLERR[:4])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
