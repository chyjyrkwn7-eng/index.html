#!/usr/bin/env python3
"""Build 384 (claude/b384-cameo): CHARACTER CAMEOS on a test's question.

Madison: "Maybe when you are taking a test your character can be interactive in a way, so maybe your character will randomly be
sitting on the edge of the question box with his legs swinging, or maybe he will be run across the bottom and then go away, but
when you swipe to the next question it would go away. Almost like an Easter egg, just randomly coming up at rare times."

Read off the page (Chromium; an iPhone 17 Pro Max 440x956 at 3x and an iPad Pro 11" 834x1194 at 2x, installed, touch), both
classes. The hook is the app's own: cameoForce(kind, {hold, dir}) fires one now on the question that is up; cameoInfo() says
what is planned and up; cameoPlanFor / cameoNoteFired are the dice.
 (A) EVERY KIND, WHOLE LIFE, CLEAR OF WHAT MATTERS: each of the nine kinds forced on a Drill (academy and Fire Code, phone and
     iPad), on a Mock with a time limit and a two-row meter (phone), and a Drill after a wrong pick (phone, Fire Code). Sampled
     every frame from the moment it fires until it has gone by itself (or 6s), each part's box (bust, legs, shoes, gloves, z's,
     sparks, the drop, the dust - every element of it, as clipped by the ledge where it is clipped) against the question text,
     every choice, the question's number, star and calculator, the status and reference lines, Pause, the chat button, the
     mode and count labels, the meter, the timer, the keyboard hint, Next: no overlap at all, in any frame. Every kind fits at
     least once per device (the run on the phone needs the floor free: the short questions here leave it).
 (B) NEVER TAKES A TAP: every element of it computes pointer-events none; elementFromPoint at the middle of each of its parts
     finds something that is not it; a real touch on a choice while one is up answers the question.
 (C) IT LEAVES: a swipe to the next question (a real touch drag) - gone before the slide has finished; a tap on Next; Pause -
     gone in the same task; the screen going (Save and exit / Home) - gone in the same task, the one still leaving included;
     an answer; the app hidden. Nothing of it left in <body>, no listener left behind (it is never re-shown by them).
 (D) REDUCE MOTION: with the app's switch and with the system's setting, no cameo (forced or planned), nothing built.
     Settings > Character cameos: there, on by default, off stops them and is saved on the theme.
 (E) RARITY, THE APP'S OWN DICE: 7000 simulated runs of 6-40 questions through cameoPlanFor/cameoNoteFired - about 1 in 7 runs
     (0.143 +- 0.02); never two runs in a row; the question never the first two or the last; under 6 questions never; not
     eligible never. Then the real path in a page with the dice forced to hit: the planned run shows nothing on questions 1 and
     2 (each held 5s), shows exactly one on its question by itself (no hook), then the next two runs plan none.
 (F) CHEAP: nothing of it in the page before one fires; once up, only transform / opacity / translate / rotate animate; the
     drawing has no filter.
 (G) no page errors.
Run:  python3 tools/check-b384-cameo.py [--only A,B,...] [--against REV|path]   (--against 1cb2318 must FAIL)"""
import functools, http.server, json, os, re, socket, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    import glob as _g; CHROME = (sorted(_g.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
args = sys.argv[1:]
ONLY = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
def want(n): return ONLY is None or n in ONLY
if "--against" in args:
    v = args[args.index("--against") + 1]
    SRC = open(v, encoding="utf-8").read() if os.path.isfile(v) else subprocess.check_output(["git", "-C", ROOT, "show", v + ":index.html"]).decode("utf-8")
else:
    SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
BUILD = (re.search(r'const APP_BUILD = "([^"]+)"', SRC) or [None, ""])[1]
from playwright.sync_api import sync_playwright
ok = True; FAILS = []
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    if not cond: FAILS.append(name)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
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
IPAD_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
  ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}} : mm(q); })();"""
FAKE = """(function(){
  function docRef(){ return { get(){ return Promise.resolve({ exists:false, data(){ return null; } }); }, set(){ return Promise.resolve(); }, update(){ return Promise.resolve(); }, delete(){ return Promise.resolve(); },
      onSnapshot(next){ setTimeout(function(){ next({ exists:false, data(){ return null; }, metadata:{fromCache:false} }); }, 40); return function(){}; }, collection(){ return collRef(); } }; }
  function collRef(){ var c = { doc(){ return docRef(); }, where(){ return c; }, orderBy(){ return c; }, limit(){ return c; },
      get(){ return Promise.resolve({ empty:true, docs:[], forEach(){}, size:0 }); },
      onSnapshot(next){ setTimeout(function(){ next({ forEach(){}, docs:[], empty:true, size:0, docChanges(){ return []; }, metadata:{fromCache:false} }); }, 60); return function(){}; } }; return c; }
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, app(){ return {}; },
    firestore(){ return { collection: collRef, batch(){ return { set(){}, update(){}, delete(){}, commit(){ return Promise.resolve(); } }; }, runTransaction(){ return Promise.reject(new Error('offline')); } }; } };
  window.firebase.firestore.FieldValue = { delete(){ return null; }, serverTimestamp(){ return Date.now(); }, arrayUnion(){ return []; }, arrayRemove(){ return []; }, increment(n){ return n; } };
})();"""
SEED = {"firstName": "Casey", "avatarChar": "grizzly", "onboardingComplete": True, "leaderboardOptIn": False, "lastModified": 1700000000000,
        "publicId": "tstcameo0001", "novaMet": 99, "tourRev": 99, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenRewardsTour": True, "seenAppearanceTour": True,
        "novaHeard": {"@recap": 99991231, "hello": 1}, "classes": ["academy", "ifc"],
        "lifetime": {"points": 1200, "answered": 540, "correct": 498, "drillPlays": 6, "examPlays": 2, "perfectTests": 4, "currentStreak": 3, "longestStreak": 5}}
SEEN = ["freshstart", "intro.seen", "unithold.tip", "daily.seen", "savecode.asked", "savecode.card", "getstarted", "a2hs",
        "ifc.freshstart", "ifc.intro.seen", "ifc.daily.seen", "ifc.savecode.asked", "ifc.savecode.card", "ifc.getstarted"]
def init_js(cls):
    j = json.dumps(json.dumps(SEED))
    s = "(()=>{ try{ if(sessionStorage.getItem('__s')) return; sessionStorage.setItem('__s','1');"
    s += "".join("localStorage.setItem('class26e.%s','1');" % k for k in SEEN)
    s += ("localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0001');"
          "localStorage.setItem('class26e.classseen', JSON.stringify(['academy','ifc'])); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');") % j
    if cls == "ifc": s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.ifc.drill.v1', %s);" % j
    return s + " }catch(e){} })()"
DEVS = {"phone": (440, 956, 3, IPHONE_UA, (62, 0, 34, 0)), "ipad": (834, 1194, 2, IPAD_UA, (24, 0, 20, 0))}
ERRS = []
def open_page(br, dev, cls, reduced=False, extra=()):
    w, h, d, ua, ins = DEVS[dev]
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=d, has_touch=True, is_mobile=(dev == "phone"), user_agent=ua,
                         reduced_motion="reduce" if reduced else "no-preference")
    ctx.add_init_script("Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5,configurable:true});")
    ctx.add_init_script(STANDALONE); ctx.add_init_script(FAKE); ctx.add_init_script(init_js(cls))
    for e in extra: ctx.add_init_script(e)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = body_for(ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}, body=b))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "note": "", "frameId": "", "force": True, "safariSound": True})))
    cdp = ctx.new_cdp_session(pg)
    pg.goto(URL)
    pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); if(s) s.remove(); }")
    pg.wait_for_timeout(800)
    pg.evaluate("""()=>{ try{ homeUnlocksOwed=()=>false; scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){}
      for(let i=0;i<3;i++) [...document.querySelectorAll('button')].filter(b=>/^(Got it|Not now|Later|Done)$/i.test(b.textContent.trim()) && b.offsetParent).forEach(b=>b.click()); }""")
    ERRS.append((dev + "/" + cls, errs))
    return ctx, pg, cdp
START = """async(o)=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const unit=QUESTIONS[0].topic.trim();
 const idx=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit && inWholeUnit(QUESTIONS[i]));
 cfg.source='all'; cfg.mode=o.mode||'drill'; cfg.units=[unit]; beginRun(idx.slice(0, o.n||12), null, o.minutes||undefined);
 for(let t=0;t<120&&!document.querySelector('#stage .qpanel .choice');t++) await wait(100); await wait(1400); return { n: order.length, pos }; }"""
# the things it must never cover: [name, rect] for each visible one
PROTECTED = r"""()=>{ const out=[]; const vh=innerHeight, vw=innerWidth;
  const add=(name, e)=>{ if(!e) return; const r=e.getBoundingClientRect(); if(r.width<1||r.height<1||r.bottom<0||r.top>vh) return;
    const cs=getComputedStyle(e); if(cs.visibility==='hidden'||cs.display==='none') return; if(e.closest('[hidden]')) return;
    out.push([name, [r.left, r.top, r.right, r.bottom]]); };
  document.querySelectorAll('#stage .qpanel .qtext').forEach(e=>add('question text', e));
  document.querySelectorAll('#stage .qpanel .choice').forEach((e,i)=>add('choice '+'ABCDEF'[i], e));
  document.querySelectorAll('#stage .qpanel .qnum, #stage .qpanel .qnumrow button').forEach(e=>add('number row: '+(e.className||'').split(' ')[0], e));
  document.querySelectorAll('#stage .qpanel .status .status-words, #stage .qpanel .ref:not([hidden])').forEach(e=>add('status/ref', e));
  document.querySelectorAll('#stage .qpanel button, #stage .foot button').forEach(e=>add('button '+(e.className||'').split(' ')[0], e));
  ['#pausebtn','#chatdock-btn','.test-modelabel','.test-qcounter','.wrap > .meter .tick','.race-qclock'].forEach(s=>document.querySelectorAll(s).forEach(e=>add(s, e)));
  document.querySelectorAll('.timerline').forEach(e=>{ if(e.offsetHeight) [...e.querySelectorAll('*')].concat([e]).forEach(x=>{ if([...x.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())||x.tagName.toLowerCase()==='svg') add('timer', x); }); });
  const h=document.querySelector('.wrap > .hint'); if(h && h.textContent.trim()) add('keyboard hint', h);
  const nb=document.getElementById('nextbtn'); if(nb && !nb.hidden) add('Next', nb);
  return out; }"""
# per frame: every element of the cameo (clipped by its clip box where it clips), and what it must not cover, until it is gone
SAMPLE = r"""async(ms)=>{ const frames=[]; const t0=performance.now(); const prot=(%s);
  const clipOf=e=>{ const c=e.closest('.cm-clip'); if(!c) return null; return getComputedStyle(c).overflow==='hidden' ? c.getBoundingClientRect() : null; };
  while(performance.now()-t0<ms){
    const el=document.querySelector('body > .cameo'); if(!el) break;
    const parts=[]; el.querySelectorAll('.cm-bust, .cm-leg, .cm-shoe, .cm-hand, .cm-z, .cm-spark, .cm-drop, .cm-dust').forEach(p=>{ let r=p.getBoundingClientRect(); let b=[r.left,r.top,r.right,r.bottom];
      const c=clipOf(p); if(c) b=[Math.max(b[0],c.left),Math.max(b[1],c.top),Math.min(b[2],c.right),Math.min(b[3],c.bottom)];
      if(b[2]-b[0]>.5 && b[3]-b[1]>.5) parts.push([p.className.split(' ').slice(0,2).join('.'), b]); });
    frames.push({ t: Math.round(performance.now()-t0), parts, prot: prot() });
    await new Promise(r=>requestAnimationFrame(r)); }
  return { frames, gone: !document.querySelector('body > .cameo'), t: Math.round(performance.now()-t0) }; }""" % PROTECTED
def overlaps(frames):
    bad = []
    for f in frames:
        for pn, p in f["parts"]:
            for qn, q in f["prot"]:
                ix = min(p[2], q[2]) - max(p[0], q[0]); iy = min(p[3], q[3]) - max(p[1], q[1])
                if ix > .5 and iy > .5: bad.append((f["t"], pn, qn, [round(v) for v in p], [round(v) for v in q]))
    return bad
KINDS = ["sit", "tiptoe", "dangle", "peek", "wave", "sleepy", "cheer", "oops", "run"]
def touch_drag(cdp, x0, y0, x1, y1, ms=260):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]}); time.sleep(.05)
    t0 = time.time()
    while True:
        u = min(1, (time.time() - t0) / (ms / 1000))
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * u, "y": y0 + (y1 - y0) * u}]})
        if u >= 1: break
        time.sleep(.012)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
def tap_at(cdp, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(.06)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
ANSWER = """async(right)=>{ const qi=order[pos]; const k=optionOrder(qi).indexOf(QUESTIONS[qi].answer); const ch=[...document.querySelectorAll('#stage .qpanel .choice')];
  (right ? ch[k] : ch[(k+1)%ch.length]).click(); await new Promise(r=>setTimeout(r, 1600)); }"""
HAS_HOOK = "()=>typeof cameoForce==='function' && typeof cameoInfo==='function' && typeof cameoPlanFor==='function'"

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    # ------------------------------------------------------------------ (A) (B) (F)
    if want("A") or want("B") or want("F"):
        CONFIGS = [("phone", "academy", {"mode": "drill"}, "grizzly"), ("ipad", "academy", {"mode": "drill"}, "grizzly"),
                   ("phone", "ifc", {"mode": "drill"}, "hacker"), ("ipad", "ifc", {"mode": "drill"}, "hacker"),
                   ("phone", "academy", {"mode": "exam", "n": 30, "minutes": 20}, "ghost"), ("phone", "ifc", {"mode": "drill", "wrong": True}, "masked")]
        for dev, cls, run, char in CONFIGS:
            label = "%s %s %s%s%s" % (dev, "Fire Code" if cls == "ifc" else "academy", run["mode"], ", timer, 30 questions" if run.get("minutes") else "", ", after a wrong pick" if run.get("wrong") else "")
            ctx, pg, cdp = open_page(br, dev, cls)
            if not pg.evaluate(HAS_HOOK):
                chk("(A) %s: the app has the cameo hook" % label, False, "no cameoForce / cameoInfo / cameoPlanFor"); ctx.close(); continue
            pg.evaluate("(c)=>{ store.avatarChar=c; }", char)
            pg.evaluate(START, run)
            if run.get("wrong"): pg.evaluate(ANSWER, False)
            before = pg.evaluate("()=>document.querySelectorAll('.cameo, [class*=\"cm-\"]').length")
            if want("F"): chk("(F) %s: nothing of a cameo in the page before one fires" % label, before == 0, before)
            fitted = []
            for k in KINDS:
                pg.evaluate("()=>{ cameoGone(); }")
                r = pg.evaluate("(k)=>cameoForce(k)", k)
                if not r or not r.get("ok"):
                    info("%s: %s did not fit (%s)" % (label, k, r and r.get("why"))); continue
                fitted.append(k)
                if want("F") and k in ("sit", "run", "cheer", "sleepy"):
                    a = pg.evaluate("""()=>{ const el=document.querySelector('body > .cameo'); const props=new Set(); let n=0;
                      el.getAnimations({subtree:true}).forEach(an=>{ n++; (an.effect&&an.effect.getKeyframes?an.effect.getKeyframes():[]).forEach(f=>Object.keys(f).forEach(p=>{ if(!/^(offset|easing|composite|computedOffset)$/.test(p)) props.add(p); })); });
                      const svg=el.querySelector('svg'); return { n, props:[...props], filter: svg?getComputedStyle(svg).filter:'?', svgAnimFilter: !!el.querySelector('filter') }; }""")
                    # the drawing's own parts (blink, sleep, nod) animate transform/opacity inside it: counted too
                    badp = [p for p in a["props"] if p not in ("transform", "opacity", "translate", "rotate", "scale")]
                    chk("(F) %s %s: only transform/opacity animate (%d animations: %s), the drawing unfiltered (%s)" % (label, k, a["n"], ",".join(sorted(a["props"])), a["filter"]),
                        a["n"] > 0 and not badp and a["filter"] == "none" and not a["svgAnimFilter"], a)
                if want("B"):
                    b = pg.evaluate("""()=>{ const el=document.querySelector('body > .cameo'); if(!el) return null; const all=[el,...el.querySelectorAll('*')];
                      const pe=all.filter(e=>getComputedStyle(e).pointerEvents!=='none').length; let hit=0, pts=0;
                      el.querySelectorAll('.cm-bust, .cm-hand, .cm-leg').forEach(p=>{ const r=p.getBoundingClientRect(); const x=r.left+r.width/2, y=r.top+r.height/2;
                        if(x<0||y<0||x>innerWidth||y>innerHeight) return; pts++; const e=document.elementFromPoint(x,y); if(e && e.closest('.cameo')) hit++; });
                      return { pe, hit, pts }; }""")
                    chk("(B) %s %s: no part takes a pointer (%s with pointer events), elementFromPoint at %s part middles never finds it (%s)" % (label, k, b and b["pe"], b and b["pts"], b and b["hit"]),
                        b and b["pe"] == 0 and b["hit"] == 0, b)
                if want("A"):
                    s = pg.evaluate(SAMPLE, 6000)
                    bad = overlaps(s["frames"])
                    prot_names = sorted(set(n for f in s["frames"][:1] for n, _ in f["prot"]))
                    chk("(A) %s %s (s=%spx): clear of the question, choices, controls and timer in all %d frames over %dms" % (label, k, r.get("s"), len(s["frames"]), s["t"]),
                        len(s["frames"]) > 10 and not bad, bad[:4] or ("frames", len(s["frames"])))
                    if k == KINDS[0]: info("%s: protected = %s" % (label, prot_names))
                pg.evaluate("()=>cameoGone()")
            need = set(KINDS) - {"run", "tiptoe"} if (dev == "phone") else set(KINDS)
            if run.get("minutes"): need = {"peek", "dangle"}      # the timer and two rows of meter leave little room: at least these
            chk("(A) %s: the kinds that must fit here fit (%s of %s)" % (label, len(fitted), len(KINDS)), need <= set(fitted), sorted(need - set(fitted)))
            if want("B") and dev == "phone" and not run.get("wrong") and run["mode"] == "drill":
                # a real touch on a choice while one is up answers the question
                pg.evaluate("()=>cameoGone()")
                r = pg.evaluate("()=>cameoForce('dangle', {hold:true})")
                c = pg.evaluate("()=>{ const qi=order[pos]; const k=optionOrder(qi).indexOf(QUESTIONS[qi].answer); const b=[...document.querySelectorAll('#stage .qpanel .choice')][k].getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2, qi]; }")
                tap_at(cdp, c[0], c[1]); pg.wait_for_timeout(700)
                st = pg.evaluate("(qi)=>({ cleared, att: attempts[qi], up: document.querySelectorAll('body > .cameo').length })", c[2])
                chk("(B) %s: a real touch on a choice with a cameo up answers it (attempts %s, cleared %s), and the cameo went (%s left)" % (label, st["att"], st["cleared"], st["up"]),
                    r.get("ok") and st["att"] == 1 and st["cleared"] and st["up"] == 0, (r, st))
            ctx.close()
    # ------------------------------------------------------------------ (C) it leaves
    if want("C"):
        for dev, cls in (("phone", "academy"), ("ipad", "ifc")):
            label = "%s %s" % (dev, "Fire Code" if cls == "ifc" else "academy")
            ctx, pg, cdp = open_page(br, dev, cls)
            if not pg.evaluate(HAS_HOOK):
                chk("(C) %s: the app has the cameo hook" % label, False); ctx.close(); continue
            pg.evaluate(START, {"mode": "drill"})
            W, H = DEVS[dev][0], DEVS[dev][1]
            # a swipe to the next question, after a right answer
            pg.evaluate(ANSWER, True)
            r = pg.evaluate("()=>cameoForce('sit', {hold:true})")
            p0 = pg.evaluate("()=>pos")
            pg.evaluate("""()=>{ window.__gone=null; const t0=performance.now(); const f=()=>{ if(!document.querySelector('body > .cameo')){ window.__gone=performance.now()-t0; return; } requestAnimationFrame(f); }; requestAnimationFrame(f);
              window.__slideAt=null; const q=window.qSlideDone; window.qSlideDone=function(){ if(window.__slideAt==null) window.__slideAt=performance.now()-t0; return q.apply(this, arguments); }; }""")
            touch_drag(cdp, W * .85, H * .55, W * .1, H * .55, 280)
            pg.wait_for_timeout(1200)
            g = pg.evaluate("()=>({ gone: window.__gone, slide: window.__slideAt, pos, n: document.querySelectorAll('body > .cameo').length })")
            chk("(C) %s: a swipe to the next question - it was up (%s), went in %sms, before the slide ended (%sms), next question up (pos %s -> %s), nothing left" % (label, r.get("ok"), g["gone"] and round(g["gone"]), g["slide"] and round(g["slide"]), p0, g["pos"]),
                r.get("ok") and g["gone"] is not None and g["slide"] is not None and g["gone"] <= g["slide"] + 20 and g["pos"] == p0 + 1 and g["n"] == 0, (r, g))
            # a tap on Next
            pg.wait_for_timeout(600)
            pg.evaluate(ANSWER, True)
            r = pg.evaluate("()=>cameoForce('peek', {hold:true})")
            nb = pg.evaluate("()=>{ const b=document.getElementById('nextbtn').getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }")
            p0 = pg.evaluate("()=>pos")
            tap_at(cdp, nb[0], nb[1]); pg.wait_for_timeout(700)
            g = pg.evaluate("()=>({ pos, n: document.querySelectorAll('body > .cameo').length })")
            chk("(C) %s: a tap on Next - next question (pos %s -> %s), it is gone (%s left)" % (label, p0, g["pos"], g["n"]), r.get("ok") and g["pos"] == p0 + 1 and g["n"] == 0, (r, g))
            pg.wait_for_timeout(600)
            # an answer (keyboard: no pointer at all)
            r = pg.evaluate("()=>cameoForce('wave', {hold:true})")
            pg.keyboard.press("1"); pg.wait_for_timeout(400)
            n = pg.evaluate("()=>document.querySelectorAll('body > .cameo').length")
            chk("(C) %s: an answer by key - it goes (%s left)" % (label, n), r.get("ok") and n == 0, r)
            pg.evaluate("()=>{ cameoGone(); if(cleared || attempts[order[pos]]) { advance(); } }"); pg.wait_for_timeout(800)
            # a redraw with no input at all (the question drawn again)
            r = pg.evaluate("()=>cameoForce('sit', {hold:true})")
            pg.evaluate("()=>render()"); pg.wait_for_timeout(400)
            n = pg.evaluate("()=>document.querySelectorAll('body > .cameo').length")
            chk("(C) %s: the question redrawn - it goes (%s left)" % (label, n), r.get("ok") and n == 0, r)
            # Pause: gone in the same task
            r = pg.evaluate("()=>cameoForce('dangle', {hold:true})")
            n = pg.evaluate("()=>{ pauseRun(); return document.querySelectorAll('body > .cameo').length; }")
            pg.wait_for_timeout(300)
            chk("(C) %s: Pause - gone in the same task (%s left)" % (label, n), r.get("ok") and n == 0, r)
            pg.evaluate("()=>resumeRun()"); pg.wait_for_timeout(900)
            # the app hidden
            r = pg.evaluate("()=>cameoForce('sleepy', {hold:true})")
            n = pg.evaluate("""()=>{ Object.defineProperty(document,'visibilityState',{get:()=>'hidden',configurable:true}); document.dispatchEvent(new Event('visibilitychange'));
              const n=document.querySelectorAll('body > .cameo').length; delete document.visibilityState; return n; }""")
            chk("(C) %s: the app hidden - gone in the same task (%s left)" % (label, n), r.get("ok") and n == 0, r)
            # (the app pauses a test it is hidden on): back to the question
            pg.evaluate("()=>{ if(paused) resumeRun(); }"); pg.wait_for_timeout(900)
            # the screen going, with one still leaving: Save and exit
            r = pg.evaluate("()=>cameoForce('sit', {hold:true})")
            r2 = pg.evaluate("()=>{ cameoLeave('test'); const a=document.querySelectorAll('body > .cameo').length; const r=cameoForce('peek', {hold:true}); return [a, r]; }")
            n = pg.evaluate("()=>{ saveAndExitTest(); return document.querySelectorAll('body > .cameo').length; }")
            pg.wait_for_timeout(100)
            n2 = pg.evaluate("()=>document.querySelectorAll('body > .cameo, .cameo').length")
            scr = pg.evaluate("()=>!document.querySelector('#stage .qpanel')")
            chk("(C) %s: the screen going (Save and exit) - the one up and the one still leaving gone (%s, then %s left), off the question (%s)" % (label, n, n2, scr),
                r.get("ok") and r2[1].get("ok") and n2 == 0 and scr, (r, r2, n, n2))
            # and no listener left: a touch later shows nothing, the page has no cameo
            tap_at(cdp, W / 2, H / 2); pg.wait_for_timeout(300)
            chk("(C) %s: after it all, nothing of it in the page (%s)" % (label, pg.evaluate("()=>document.querySelectorAll('.cameo').length")), pg.evaluate("()=>document.querySelectorAll('.cameo').length") == 0)
            ctx.close()
    # ------------------------------------------------------------------ (D) Reduce motion, the switch
    if want("D"):
        for how in ("app", "system"):
            ctx, pg, cdp = open_page(br, "phone", "academy", reduced=(how == "system"))
            if not pg.evaluate(HAS_HOOK):
                chk("(D) Reduce motion (%s): the app has the cameo hook" % how, False); ctx.close(); continue
            if how == "app": pg.evaluate("()=>{ theme.reduceMotion=true; applyTheme(); saveTheme(); }")
            pg.evaluate("()=>{ Math.__r=Math.random; Math.random=()=>0; }")
            pg.evaluate(START, {"mode": "drill"})
            res = [pg.evaluate("(k)=>cameoForce(k)", k) for k in KINDS]
            plan = pg.evaluate("()=>cameoInfo().plan")
            pg.evaluate("()=>{ advance(); }"); pg.wait_for_timeout(600); pg.evaluate("()=>{ advance(); }"); pg.wait_for_timeout(5000)
            n = pg.evaluate("()=>document.querySelectorAll('.cameo, [class*=\"cm-\"]').length")
            chk("(D) Reduce motion (%s): no kind can be shown (%s), no run planned (%s), nothing built after 5s on a question (%s)" % (how, sorted(set(r.get("why") for r in res)), plan, n),
                all(not r.get("ok") for r in res) and plan is None and n == 0, (res[:2], plan, n))
            ctx.close()
        ctx, pg, cdp = open_page(br, "phone", "academy")
        if pg.evaluate(HAS_HOOK):
            pg.evaluate("()=>showAppearance({page:'motion'})"); pg.wait_for_timeout(1200)
            row = pg.evaluate("""()=>{ const r=[...document.querySelectorAll('label.opt')].find(l=>/^Character cameos/.test((l.querySelector('.otext')||{}).textContent||'')); if(!r) return null;
              const cb=r.querySelector('input'); return { on: cb.checked, hint: (r.querySelector('.ohint')||{}).textContent, h: r.getBoundingClientRect().height }; }""")
            chk("(D) Settings: a Character cameos switch, on by default, a 44px+ row (%s)" % row, row and row["on"] and row["h"] >= 44, row)
            if row:
                pg.evaluate("""()=>{ const r=[...document.querySelectorAll('label.opt')].find(l=>/^Character cameos/.test((l.querySelector('.otext')||{}).textContent||'')); r.querySelector('input').click(); }""")
                pg.wait_for_timeout(300)
                st = pg.evaluate("()=>({ t: theme.cameos, saved: store.theme && store.theme.cameos })")
                pg.evaluate(START, {"mode": "drill"})
                r = pg.evaluate("()=>cameoForce('sit')")
                chk("(D) Settings: switched off it is saved on the theme (%s) and no cameo shows (%s)" % (st, r), st["t"] is False and st["saved"] is False and not r.get("ok"), (st, r))
        else:
            chk("(D) Settings: the app has the cameo hook", False)
        ctx.close()
    # ------------------------------------------------------------------ (E) rarity
    if want("E"):
        ctx, pg, cdp = open_page(br, "phone", "academy")
        if not pg.evaluate(HAS_HOOK):
            chk("(E) rarity: the app has the dice (cameoPlanFor)", False)
        else:
            sim = pg.evaluate("""()=>{ localStorage.removeItem('class26e.cameo'); let fired=0, runs=0, twice=0, last=false, badPos=0, small=0, inel=0, gaps=[], since=0;
              for(let i=0;i<7000;i++){ const n=6+Math.floor(Math.random()*35); const p=cameoPlanFor(n, true); runs++;
                if(p){ fired++; if(last) twice++; if(!(p.at>=2 && p.at<=n-2)) badPos++; cameoNoteFired(); gaps.push(since); since=0; last=true; } else { last=false; since++; } }
              for(let i=0;i<500;i++){ if(cameoPlanFor(2+Math.floor(Math.random()*4), true)) small++; if(cameoPlanFor(20, false)) inel++; }
              localStorage.removeItem('class26e.cameo');
              return { fired, runs, rate: fired/runs, twice, badPos, small, inel, minGap: Math.min(...gaps.slice(1)) }; }""")
            chk("(E) rarity: %d of %d simulated runs had one (%.3f; 1 in %.1f) - about 1 in 7 (0.143 +- 0.02)" % (sim["fired"], sim["runs"], sim["rate"], 1 / max(sim["rate"], 1e-9)),
                abs(sim["rate"] - 1 / 7) <= .02, sim)
            chk("(E) rarity: never two runs in a row (%s), at least 2 runs between (min gap %s), never question 1 or 2 or the last (%s outside)" % (sim["twice"], sim["minGap"], sim["badPos"]),
                sim["twice"] == 0 and sim["minGap"] >= 2 and sim["badPos"] == 0, sim)
            chk("(E) rarity: never under 6 questions (%s), never in a run that may not have one (%s)" % (sim["small"], sim["inel"]), sim["small"] == 0 and sim["inel"] == 0, sim)
            # the real path: the dice forced to hit, no hook
            # the dice at 0 all the way to the cameo: the run is chosen, its question is the 3rd, its kind the first (sit), its wait the shortest
            pg.evaluate("()=>{ localStorage.removeItem('class26e.cameo'); Math.__r=Math.random; Math.random=()=>0; }")
            pg.evaluate(START, {"mode": "drill"})
            plan = pg.evaluate("()=>cameoInfo().plan")
            seen = []
            for q in range(2):
                pg.wait_for_timeout(5000)
                seen.append(pg.evaluate("()=>document.querySelectorAll('body > .cameo').length"))
                pg.evaluate(ANSWER, True); pg.evaluate("()=>advanceWithSlide()"); pg.wait_for_timeout(900)
            # question 3 (pos 2): it comes by itself, once
            got = None; t0 = time.time()
            while time.time() - t0 < 8:
                if pg.evaluate("()=>!!document.querySelector('body > .cameo')"): got = round(time.time() - t0, 1); break
                pg.wait_for_timeout(100)
            pg.evaluate("()=>{ Math.random=Math.__r; }")
            kind = pg.evaluate("()=>{ const e=document.querySelector('body > .cameo'); return e ? e.dataset.kind : null; }")
            info2 = pg.evaluate("()=>cameoInfo()")
            pg.wait_for_timeout(9000)
            pg.evaluate(ANSWER, True); pg.evaluate("()=>advanceWithSlide()"); pg.wait_for_timeout(5500)
            again = pg.evaluate("()=>document.querySelectorAll('body > .cameo').length")
            chk("(E) the real path: planned for question %s; nothing on questions 1 and 2 (%s); on question 3 one came by itself after %ss (%s, pos %s); none again after it (%s)" % (
                plan and plan["at"] + 1, seen, got, kind, info2["plan"] and info2["plan"]["pos"], again),
                plan and plan["at"] == 2 and seen == [0, 0] and got is not None and kind is not None and info2["plan"]["fired"] and again == 0, (plan, seen, got, info2))
            # the next two runs plan none, even with the dice at 0; the third does
            plans = []
            pg.evaluate("()=>{ Math.random=()=>0; }")
            for i in range(3):
                pg.evaluate("()=>{ testInProgress=false; }")
                pg.evaluate(START, {"mode": "drill"})
                plans.append(pg.evaluate("()=>!!cameoInfo().plan"))
            pg.evaluate("()=>{ Math.random=Math.__r; }")
            chk("(E) after a run with one, the next two runs plan none and the third may (%s)" % plans, plans == [False, False, True], plans)
            pg.evaluate("()=>localStorage.removeItem('class26e.cameo')")
        ctx.close()
    br.close()
allerr = [(k, e) for k, e in ERRS if e]
chk("(G) no page errors (%d pages)" % len(ERRS), not allerr, allerr[:3])
print("ALL PASS" if ok else "FAILURES (%d): %s" % (len(FAILS), "; ".join(FAILS[:8])))
sys.exit(0 if ok else 1)
