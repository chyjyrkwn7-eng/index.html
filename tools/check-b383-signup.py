#!/usr/bin/env python3
"""Build 383: sign-up and sign-in, walked end to end as a person would.

Madison: "Ensure the sign up login process is perfect and good to go."

An in-memory Firestore (the CDN is blocked here) that keeps its documents across the tab's reloads, so a Sign out and a
sign-in see the same cloud. Codes are fake (TEST-38xx), names are made up. Installed app (navigator.standalone), with the
iPhone's safe areas. Every step: no page error or console error, no sideways scroll, every visible button 44px+ both ways,
text fields 16px+, no two pieces of a sign-up screen on top of each other, no owner's name in what the screen says.

  fresh    - a new install, on an iPhone 17 Pro Max (440x956) and an iPad Pro 11 (834x1194): Get Started -> Welcome ->
             Sign in and Back -> I'm new here -> New to Nova? (Back) -> Select your classes (Back; Continue only once a class
             is picked; a double tap starts ONE sign-up [fix]) -> GENERATING PROFILE -> Nova asks the name (Enter answers)
             and the partner (one account, one document) -> the save-your-code card (Continue off until ticked) -> his
             talk to its end -> the tips -> Home; a reload stays on Home.
  signin   - Welcome > Sign in: empty, typed lower case with a space, pasted with a space in front [fix], the whole message
             Save it shares pasted [fix], a wrong code, a code from before the fresh start (not "verified") [fix], Enter
             checks it; the right code: the account's name, Sync This Device -> Home with its progress, no Nova, no tips,
             no save-code card, the cloud copy not lowered, a reload stays on Home. The cloud not answering: Checking, and
             Back still works; no Firebase at all: says so.
  had      - a device that held an account: I'm new here asks first (Sign in primary), both answers go where they say.
  signout  - the owner, in both classes: Settings > Account > Sign out -> Welcome, not the first-visit page [fix]; nothing
             of the account left; I'm new here asks first; the code signs it back in with everything; Fire Code's cloud
             document untouched; Fire Code's enrolment (a device setting) kept through the sign out [fix2]: after signing
             back in the class button offers Fire Code, and tapping it opens Fire Code's Home - no enrolling, no book to
             pick - with its progress back from its cloud document [fix2].
  icon     - an installed app opened from an icon whose address carries the code (#k=, Add to Home Screen walkthrough):
             Sign out stays signed out on the reload and on the next launch from that icon [fix]; the code signs it back
             in and the icon then opens Home; a wiped device opened from that icon lands on Home, not Get Started [fix].
  settings - Settings > Sync > Enter a code (a device with sync off) takes the pasted message's code [fix]; Settings >
             Account > Name's Change pill takes a tap anywhere in 44px round its middle [fix2].

  python3 tools/check-b383-signup.py
  python3 tools/check-b383-signup.py --against /path/to/old-index.html     (the [fix] checks FAIL there; [fix2] on 18815df)
  ONLY=fresh,signin python3 tools/check-b383-signup.py
  SU_SHOTS=/some/folder python3 tools/check-b383-signup.py                 (a picture of every step)
"""
import functools, http.server, io, json, os, re, socket, sys, threading, time
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PATH = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(ROOT, "index.html")
SRC = io.open(SRC_PATH, encoding="utf-8").read()
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', SRC).group(1)
ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
SHOTS = os.environ.get("SU_SHOTS")
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
DEVICES = {"phone": (440, 956, (62, 0, 34, 0)), "ipad": (834, 1194, (24, 0, 20, 0))}
OWNER = "xph5b57jbp5a"

STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
 ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}} : mm(q); })();"""
# The cloud: documents, get/set/update/delete, live listeners; kept in the tab's sessionStorage so a reload (Sign out)
# sees the same documents. window.__offline = true makes every read and write hang, as a cloud that never answers.
FAKE = r"""(()=>{ if(location.protocol !== 'http:') return;
  let C = null; try{ C = JSON.parse(sessionStorage.getItem('__fakecloud') || 'null'); }catch(e){}
  if(!C) C = JSON.parse(JSON.stringify(window.__cloudSeed || {}));
  ['progress','leaderboard','vrooms'].forEach(k => { C[k] = C[k] || {}; });
  window.__cloud = C;
  let W = []; try{ W = JSON.parse(sessionStorage.getItem('__fakewrites') || '[]'); }catch(e){}
  window.__writes = W;
  const keep = () => { try{ sessionStorage.setItem('__fakecloud', JSON.stringify(C)); sessionStorage.setItem('__fakewrites', JSON.stringify(W)); }catch(e){} };
  const subs = {};
  const clone = v => v == null ? v : JSON.parse(JSON.stringify(v));
  const snap = (c, id) => { const d = (C[c] || {})[id]; return { id, exists: d !== undefined, data: () => clone(d), metadata: { fromCache: false, hasPendingWrites: false } }; };
  const fire = (c, id) => (subs[c + '/' + id] || []).forEach(f => setTimeout(() => f(snap(c, id)), 15));
  const hang = () => new Promise(() => {});
  const doc = (c, id) => ({ id,
    get: () => window.__offline ? hang() : Promise.resolve(snap(c, id)),
    set: (v, o) => { if(window.__offline) return hang(); C[c] = C[c] || {}; C[c][id] = (o && o.merge) ? Object.assign({}, C[c][id] || {}, clone(v)) : clone(v); W.push('set ' + c + '/' + id); keep(); fire(c, id); return Promise.resolve(); },
    update: v => { if(window.__offline) return hang(); C[c] = C[c] || {}; C[c][id] = Object.assign({}, C[c][id] || {}, clone(v)); W.push('update ' + c + '/' + id); keep(); fire(c, id); return Promise.resolve(); },
    delete: () => { if(window.__offline) return hang(); if(C[c]) delete C[c][id]; W.push('DEL ' + c + '/' + id); keep(); fire(c, id); return Promise.resolve(); },
    onSnapshot: function(){ const a = [...arguments]; const next = a.find(x => typeof x === 'function'); const k = c + '/' + id; (subs[k] = subs[k] || []).push(next); if(!window.__offline) setTimeout(() => next(snap(c, id)), 30); return () => { subs[k] = (subs[k] || []).filter(f => f !== next); }; },
    collection: n => coll(c + '/' + id + '/' + n) });
  const coll = c => { const q = { doc: id => doc(c, id), where(){ return q; }, orderBy(){ return q; }, limit(){ return q; },
    get: () => window.__offline ? hang() : Promise.resolve({ empty: true, docs: [], forEach(){}, size: 0 }),
    onSnapshot: function(){ const a = [...arguments]; const next = a.find(x => typeof x === 'function'); if(!window.__offline) setTimeout(() => next({ empty: true, docs: [], size: 0, forEach(){}, metadata: { fromCache: false }, docChanges: () => [] }), 30); return () => {}; } }; return q; };
  const db = { collection: coll, batch: () => ({ set(){}, update(){}, delete(){}, commit: () => Promise.resolve() }) };
  const fs = () => db; fs.FieldValue = { delete: () => null, serverTimestamp: () => Date.now(), arrayUnion: (...x) => x, increment: n => n }; fs.FieldPath = function(){};
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.getstarted','class26e.frame.ok']"
        ".forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));")
SEEN_ACCT = SEEN + "['class26e.daily.seen','class26e.savecode.card','class26e.savecode.asked'].forEach(k=>localStorage.setItem(k,'1'));"
def account(name, pub, pts, correct, **extra):
    d = {"firstName": name, "avatarChar": "ghost", "onboardingComplete": True, "publicId": pub, "leaderboardOptIn": False,
         "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
         "seenMainMenuTour": True, "seenClassTip": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
         "seenRankingsTour": True, "seenAppearanceTour": True,
         "lifetime": {"points": pts, "answered": correct + 100, "correct": correct}, "testStats": {"Penal Code": {"plays": 3}}}
    d.update(extra)
    return d

s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer.handle_error = lambda *a: None
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT)).serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

fails = []; fixes_failed = []
def chk(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:500]), flush=True)
    if not cond:
        fails.append(name)
        if name.startswith("[fix]"): fixes_failed.append(name)
def want(sec): return not ONLY or sec in ONLY

def body(ins):
    v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
    return INSET_RE.sub(lambda m: v[m.group(1)], SRC)

def open_page(br, dev="phone", init="", seed=None, suffix="", firebase=True, wait=3200):
    w, h, ins = DEVICES[dev]
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, has_touch=True)
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed or {}))
    if firebase: ctx.add_init_script(FAKE)
    ctx.add_init_script(STANDALONE)
    if init:
        ctx.add_init_script("(()=>{ try{ if(location.protocol !== 'http:' || sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); "
                            + init + " }catch(e){} })()")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:240]))
    pg.on("console", lambda m: errs.append("console: " + m.text[:240]) if m.type == "error"
          and "Failed to load resource" not in m.text and "net::" not in m.text else None)
    b = body(ins)
    pg.route("**/index.html", lambda r, q, b=b: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "force": False, "frameId": ""})))
    pg.goto(URL + suffix); pg.wait_for_timeout(wait)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.errs = errs; pg.dev = dev
    # (384, round 2) Get Started opens on every launch with no account now; a device that has seen it (SEEN's mark) has its
    # button up at once, and a person taps it to reach Welcome - so does this (a first visit still meets the page: sec_fresh)
    if pg.evaluate("()=>!!document.querySelector('.gs-page .gs-bar.is-ready .gs-go')"):
        pg.click(".gs-go"); pg.wait_for_timeout(1100)
    return ctx, pg

def relaunch(pg, suffix="", wait=3200):
    """the app closed and opened again (from its icon, whose address may carry #k=)"""
    pg.goto("about:blank"); pg.wait_for_timeout(200)
    pg.goto(URL + suffix); pg.wait_for_timeout(wait)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.wait_for_timeout(600)

SCREEN = """()=>{ const s=document.querySelector('#stage [data-screen]'); if(s) return s.dataset.screen;
  const p=document.querySelector('#stage > .panel, #stage > section'); return p ? (p.className||'').toString().replace(/\\s+/g,'.') : ''; }"""
def screen(pg): return pg.evaluate(SCREEN)

# one sign-up/sign-in screen: overflow, tap targets, field sizes, overlaps, the owner's name
LAYOUT = r"""(scope)=>{ const de=document.documentElement;
  const vis=e=>{ const r=e.getBoundingClientRect(), c=getComputedStyle(e); return r.width>0 && r.height>0 && c.visibility!=='hidden' && c.display!=='none' && Number(c.opacity)>0.05 && r.bottom>0 && r.top<innerHeight && r.right>0 && r.left<innerWidth; };
  const onTop=e=>{ const r=e.getBoundingClientRect(); const x=Math.min(innerWidth-1,Math.max(0,r.left+r.width/2)), y=Math.min(innerHeight-1,Math.max(0,r.top+r.height/2)); const t=document.elementFromPoint(x,y); return !!t && (e===t || e.contains(t) || t.contains(e)); };
  const roots=[...document.querySelectorAll(scope)];
  const all=sel=>roots.flatMap(r=>[...r.querySelectorAll(sel)]);
  const btns=all('button, [role=button], [role=checkbox]').filter(vis).filter(onTop).filter(b=>!b.closest('[aria-hidden=true]'));
  const small=btns.filter(b=>{ const r=b.getBoundingClientRect(); return r.height<43.5 || r.width<43.5; })
    .map(b=>((b.className||'')+'').slice(0,40)+' "'+b.textContent.trim().slice(0,20)+'" '+Math.round(b.getBoundingClientRect().width)+'x'+Math.round(b.getBoundingClientRect().height));
  const fields=all('input:not([type=checkbox]):not([type=radio]):not([type=file])').filter(vis).map(i=>parseFloat(getComputedStyle(i).fontSize)).filter(f=>f<15.95);
  const parts=all('p, h1, h2, button, input, label, .class-card').filter(vis).filter(e=>!e.closest('[aria-hidden=true]') && !e.closest('.class-card') || e.matches('.class-card'));
  const ov=[]; for(let i=0;i<parts.length;i++) for(let j=i+1;j<parts.length;j++){ const a=parts[i], b=parts[j]; if(a.contains(b)||b.contains(a)) continue;
    const r=a.getBoundingClientRect(), s=b.getBoundingClientRect(); const ix=Math.min(r.right,s.right)-Math.max(r.left,s.left), iy=Math.min(r.bottom,s.bottom)-Math.max(r.top,s.top);
    if(ix>2 && iy>2) ov.push(((a.className||a.tagName)+'').slice(0,28)+' x '+((b.className||b.tagName)+'').slice(0,28)); }
  const text=roots.map(r=>r.innerText||'').join(' ');
  return { sideways: de.scrollWidth-de.clientWidth, small, fields, overlaps: ov.slice(0,6), owner: /madison/i.test(text) }; }"""
step_n = [0]
def step(pg, label, scope="#stage"):
    pg.wait_for_timeout(250)
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True); step_n[0] += 1
        pg.screenshot(path=os.path.join(SHOTS, "%s-%02d-%s.png" % (pg.dev, step_n[0], re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-"))))
    r = pg.evaluate(LAYOUT, scope)
    bad = {k: v for k, v in r.items() if v}
    chk("[guard] %s %s: no sideways scroll, buttons 44px+, fields 16px+, nothing overlapping, no owner's name" % (pg.dev, label), not bad, bad)
    return r

def errs_ok(pg, where):
    chk("[guard] %s %s: no page or console errors" % (pg.dev, where), not pg.errs, pg.errs[:3])

def nova(pg):
    return pg.evaluate("""()=>{ const n=document.getElementById('nova-intro'); if(!n||!n.__nova) return null;
      return { asking:n.__nova.asking, typing:n.__nova.typing, i:n.__nova.index, count:n.__nova.count,
        name: !!n.querySelector('.nt-ask-name input'), char: !!n.querySelector('.nt-ask-char .avatarchar-option'),
        card: !!document.getElementById('savecode-card') }; }""")

def to_welcome(pg):
    """from the first-visit Get Started page to Welcome, as a person would: scroll to its end, Let's get started"""
    if screen(pg) == "getstarted":
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); s && s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1400)
        pg.click(".gs-go"); pg.wait_for_timeout(1000)

def type_code(pg, sel, text, paste=False):
    pg.fill(sel, ""); pg.focus(sel)
    if paste: pg.keyboard.insert_text(text)
    else: pg.keyboard.type(text)
    pg.wait_for_timeout(120)
    return pg.input_value(sel)

def sign_in(pg, code):
    """Welcome > Sign in > the code > Continue > Sync This Device > Home"""
    to_welcome(pg)
    if screen(pg) != "welcome": return False
    pg.click(".welcome-signin"); pg.wait_for_timeout(500)
    type_code(pg, ".synccode-entry-panel input", code)
    pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(700)
    pg.click(".synccode-confirm .next.playbtn")
    pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=15000)
    pg.wait_for_timeout(1500)
    return True

print("check-b383-signup against", SRC_PATH, "(build %s)" % BUILD)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)

    # ------------------------------------------------------------------ fresh
    def sec_fresh():
        for dev in ("phone", "ipad"):
            print("\nfresh install, %s" % dev)
            ctx, pg = open_page(br, dev, wait=3500)
            chk("[guard] %s a first visit opens on Get Started" % dev, screen(pg) == "getstarted", screen(pg))
            pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); s && s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1400)
            pg.click(".gs-go"); pg.wait_for_timeout(1000)
            chk("[guard] %s Let's get started -> Welcome, Sign in first" % dev, screen(pg) == "welcome" and pg.evaluate("()=>document.querySelector('.cosmic-welcome-btn').classList.contains('welcome-signin')"), screen(pg))
            step(pg, "Welcome")
            pg.click(".welcome-signin"); pg.wait_for_timeout(500)
            step(pg, "Sign in")
            pg.click(".synccode-entry-panel .back-link"); pg.wait_for_timeout(500)
            chk("[guard] %s Sign in's Back -> Welcome" % dev, screen(pg) == "welcome", screen(pg))
            pg.click(".welcome-new"); pg.wait_for_timeout(700)
            chk("[guard] %s I'm new here on a fresh device -> New to Nova? (no sheet)" % dev, pg.evaluate("()=>!!document.querySelector('#stage .signupcheck-panel') && !document.getElementById('newacct-confirm')"), screen(pg))
            step(pg, "New to Nova")
            pg.click(".signupcheck-panel .back-link"); pg.wait_for_timeout(500)
            chk("[guard] %s New to Nova?'s Back -> Welcome" % dev, screen(pg) == "welcome", screen(pg))
            pg.click(".welcome-new"); pg.wait_for_timeout(700)
            pg.click(".signupcheck-go"); pg.wait_for_timeout(600)
            chk("[guard] %s I'm new, continue -> Select your classes, Continue waiting for a pick" % dev,
                pg.evaluate("()=>!!document.querySelector('#stage .classselect-panel') && document.querySelector('.classselect-panel #nextbtn').hidden"), screen(pg))
            step(pg, "Select your classes")
            pg.click(".classselect-panel .back-link"); pg.wait_for_timeout(500)
            chk("[guard] %s the class step's Back -> New to Nova?" % dev, pg.evaluate("()=>!!document.querySelector('#stage .signupcheck-panel')"), screen(pg))
            pg.click(".signupcheck-go"); pg.wait_for_timeout(600)
            pg.click(".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(300)
            step(pg, "Class picked")
            t0 = time.time()
            # (384) Continue asks first (the enroll confirm); a double tap on Enroll is the double tap now
            pg.evaluate("()=>{ const b=document.querySelector('.classselect-panel #nextbtn'); b.click(); b.click(); }"); pg.wait_for_timeout(300)
            pg.evaluate("()=>{ const y=document.querySelector('#classenroll-confirm .classenroll-yes'); if(y){ y.click(); y.click(); } }")
            most = 0
            for _ in range(12):
                most = max(most, pg.evaluate("()=>document.querySelectorAll('#genprofile-overlay').length")); pg.wait_for_timeout(100)
            chk("[fix] %s a double tap on Continue starts one sign-up: one loading screen (%d)" % (dev, most), most == 1, most)
            step(pg, "Generating profile", "#genprofile-overlay")
            pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=30000)
            print("  INFO %s GENERATING PROFILE took %.1fs" % (dev, time.time() - t0))
            seen = set(); name = "Casey Rivera"; count_after = None; card_off = None
            t1 = time.time()
            while time.time() - t1 < 120:
                st = nova(pg)
                if not st:
                    if pg.evaluate("()=>!!document.getElementById('savecode-card')"): pass
                    elif "end" in seen or time.time() - t1 > 8: break
                    pg.wait_for_timeout(150); continue
                if st["card"] and "card" not in seen:
                    seen.add("card"); pg.wait_for_timeout(400)
                    card_off = pg.evaluate("()=>document.querySelector('#savecode-card .savecode-continue').disabled")
                    step(pg, "Save your sync code", "#savecode-card")
                    pg.click("#savecode-card .savecode-continue", force=True); pg.wait_for_timeout(200)
                    still = pg.evaluate("()=>!!document.getElementById('savecode-card')")
                    chk("[guard] %s the save-code card: Continue is off until the box is ticked" % dev, card_off and still, (card_off, still))
                    pg.click("#savecode-card .savecode-ack"); pg.wait_for_timeout(150)
                    pg.click("#savecode-card .savecode-continue"); pg.wait_for_timeout(500)
                    continue
                if st["asking"] and not st["typing"] and st["name"] and "name" not in seen:
                    seen.add("name")
                    step(pg, "Nova asks your name", "#nova-intro .nt-ask")
                    pg.click(".nt-ask-input"); pg.keyboard.type(name); pg.keyboard.press("Enter")
                    for _ in range(60):
                        if not pg.evaluate("()=>!!document.querySelector('#nova-intro .nt-ask-name')"): break
                        pg.wait_for_timeout(100)
                    chk("[guard] %s Enter in the name field answers it" % dev, not pg.evaluate("()=>!!document.querySelector('#nova-intro .nt-ask-name:not(.is-out)')"), "still asking")
                    continue
                if st["asking"] and not st["typing"] and st["char"] and "char" not in seen:
                    seen.add("char")
                    pg.click(".nt-ask-char .avatarchar-option"); pg.wait_for_timeout(300)
                    step(pg, "Nova asks your partner", "#nova-intro .nt-ask")
                    pg.evaluate("()=>{ const b=document.querySelector('.nt-ask-char .nt-ask-go'); b.click(); b.click(); }")
                    pg.wait_for_timeout(1500)
                    count_after = pg.evaluate("()=>({ code: syncCode, docs: Object.keys(__cloud.progress).filter(k=>!/__/.test(k)) })")
                    continue
                if not st["typing"] and not st["asking"]:
                    if st["i"] == st["count"] - 1:
                        seen.add("end"); pg.evaluate("()=>document.querySelector('#nova-intro .nt-go')?.click()")
                    else: pg.evaluate("()=>document.getElementById('nova-intro').__nova.advance()")
                pg.wait_for_timeout(120)
            chk("[guard] %s Nova asked the name, the partner and had the save-code card answered" % dev, {"name", "char", "card"} <= seen, seen)
            tip = False
            for _ in range(40):
                if pg.evaluate("()=>!!document.getElementById('tour-tooltip')"): tip = True; break
                pg.wait_for_timeout(250)
            chk("[guard] %s after Nova, the main menu's tips run over Home" % dev, tip and screen(pg) == "home", screen(pg))
            for _ in range(20):
                if not pg.evaluate("()=>!!document.getElementById('tour-next')"): break
                pg.evaluate("()=>document.getElementById('tour-next').click()"); pg.wait_for_timeout(300)
            pg.wait_for_timeout(1500)
            r = pg.evaluate("""()=>({ screen: document.querySelector('#stage [data-screen]')?.dataset.screen, name: store.firstName, char: store.avatarChar,
                onb: store.onboardingComplete, saved: store.savedCodeSaved, code: syncCode, card: !!document.getElementById('savecode-card'),
                cloudName: ((__cloud.progress[syncCode]||{}).firstName) || null, floor: !!__cloud.progress[syncCode + '__floor'] })""")
            docs = pg.evaluate("()=>Object.keys(__cloud.progress).filter(k=>!/__/.test(k))")
            chk("[guard] %s choosing the partner (twice) made one account: one code, kept to the end, one document (%s, %s)" % (dev, count_after, docs),
                bool(count_after) and bool(count_after["code"]) and count_after["code"] == r["code"] and docs == [r["code"]], (count_after, docs))
            chk("[guard] %s Home, the account named, its partner, onboarded, the code saved, in the cloud with its backup (%s)" % (dev, r),
                r["screen"] == "home" and r["name"] == name and r["char"] and r["onb"] and r["saved"] and r["cloudName"] == name and r["floor"] and not r["card"], r)
            relaunch(pg)
            chk("[guard] %s opened again: Home, still signed in" % dev, screen(pg) == "home" and pg.evaluate("()=>syncCode") == r["code"], screen(pg))
            errs_ok(pg, "fresh install")
            ctx.close()

    # ------------------------------------------------------------------ signin
    def sec_signin():
        print("\nsign in with a code")
        CODE, OLD = "TEST-3831", "OLDC-3831"
        acct = account("Gate Tester", "gatetest0001", 4321, 777)
        old = account("Older Account", "gatetest0009", 50, 9, lastModified=1780000000000)   # before the fresh start
        ctx, pg = open_page(br, "phone", init=SEEN, seed={"progress": {CODE: acct, OLD: old}})
        pg.click(".welcome-signin"); pg.wait_for_timeout(500)
        F = ".synccode-entry-panel input"
        status = lambda: pg.evaluate("()=>{ const s=document.querySelector('.synccode-status'); return { text: s.textContent, bad: s.classList.contains('bad'), shown: s.classList.contains('show'), card: document.querySelector('.synccode-confirm').classList.contains('show') }; }")
        pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(300)
        r = status(); chk("[guard] Continue with nothing typed says so", r["shown"] and r["bad"] and not r["card"], r)
        v = type_code(pg, F, "test 3831"); chk("[guard] typed in lower case with a space: %r" % v, v == CODE, v)
        v = type_code(pg, F, " " + CODE, paste=True); chk("[fix] pasted with a space in front: %r (was cut to 9 characters)" % v, v == CODE, v)
        msg = "Nova sign-in code: %s\nKeep this. It is the only way back into your account if this phone loses the app's data." % CODE
        v = type_code(pg, F, msg, paste=True); chk("[fix] the whole message Save it shares, pasted: %r" % v, v == CODE, v)
        v = type_code(pg, F, "ABCD-EFGHJK"); chk("[guard] typing past eight characters stops at the code: %r" % v, v == "ABCD-EFGH", v)
        pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(600)
        r = status(); chk("[guard] a code with no account: not verified, says so", r["shown"] and r["bad"] and not r["card"], r)
        type_code(pg, F, OLD); pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(600)
        r = status(); chk("[fix] a code from before the fresh start is not 'verified' and names nobody", r["bad"] and not r["card"], r)
        type_code(pg, F, CODE); pg.keyboard.press("Enter"); pg.wait_for_timeout(700)
        r = status(); who = pg.evaluate("()=>document.querySelector('.synccode-confirm-name').textContent")
        chk("[guard] Enter checks the code; the right one names its account (%r)" % who, r["card"] and not r["bad"] and who == "Gate Tester", r)
        step(pg, "Code verified")
        t0 = time.time()
        pg.evaluate("()=>{ const b=document.querySelector('.synccode-confirm .next.playbtn'); b.click(); b.click(); }")
        pg.wait_for_timeout(500)
        chk("[guard] Sync This Device twice: one syncing screen", pg.evaluate("()=>document.querySelectorAll('#genprofile-overlay').length") == 1)
        pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=15000)
        print("  INFO SYNCING DEVICES took %.1fs" % (time.time() - t0))
        pg.wait_for_timeout(800)
        r = pg.evaluate("()=>({ screen: document.querySelector('#stage [data-screen]')?.dataset.screen, pts: store.lifetime.points, correct: store.lifetime.correct, name: store.firstName, code: syncCode, onb: store.onboardingComplete })")
        chk("[guard] signed in: Home with the account's progress (%s)" % r, r["screen"] == "home" and r["pts"] == 4321 and r["correct"] == 777 and r["code"] == CODE and r["onb"], r)
        extra = []
        for _ in range(24):
            for k, sel in (("nova", "#nova-intro"), ("tips", "#tour-tooltip"), ("save-code card", "#savecode-card"), ("what's new", "#intro-pop"), ("new-account sheet", "#newacct-confirm")):
                if k not in extra and pg.evaluate("(s)=>!!document.querySelector(s)", sel): extra.append(k)
            pg.wait_for_timeout(250)
        chk("[guard] no new-account pieces after signing in - no Nova, tips or save-code card (%s)" % extra, not extra, extra)
        cloud = pg.evaluate("(c)=>__cloud.progress[c].lifetime", CODE)
        chk("[guard] the cloud copy was not lowered (%s)" % cloud, cloud["points"] >= 4321 and cloud["correct"] >= 777, cloud)
        relaunch(pg)
        chk("[guard] opened again: Home, still signed in", screen(pg) == "home" and pg.evaluate("()=>syncCode") == CODE, screen(pg))
        errs_ok(pg, "sign in")
        ctx.close()
        # the cloud not answering
        ctx, pg = open_page(br, "phone", init=SEEN, seed={"progress": {CODE: acct}})
        pg.evaluate("()=>{ window.__offline = true; }")
        pg.click(".welcome-signin"); pg.wait_for_timeout(400)
        type_code(pg, F, CODE); pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(1500)
        r = pg.evaluate("()=>{ const b=document.querySelector('.synccode-entry-panel #nextbtn'); return { busy: b.disabled, text: b.textContent }; }")
        chk("[guard] the cloud not answering: Continue shows it is checking and cannot be tapped again (%s)" % r, r["busy"], r)
        pg.click(".synccode-entry-panel .back-link"); pg.wait_for_timeout(500)
        chk("[guard] ... and Back still goes to Welcome", screen(pg) == "welcome", screen(pg))
        ctx.close()
        ctx, pg = open_page(br, "phone", init=SEEN, firebase=False)
        pg.click(".welcome-signin"); pg.wait_for_timeout(400)
        type_code(pg, F, CODE); pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(500)
        r = status(); chk("[guard] no Firebase at all: says sync can't be reached", r["shown"] and r["bad"] and not r["card"], r)
        ctx.close()

    # ------------------------------------------------------------------ had
    def sec_had():
        print("\na device that held an account")
        ctx, pg = open_page(br, "phone", init=SEEN + "localStorage.setItem('class26e.hadaccount', JSON.stringify({at:1,name:'Gate Tester'}));")
        pg.click(".welcome-new"); pg.wait_for_timeout(700)
        r = pg.evaluate("()=>{ const s=document.getElementById('newacct-confirm'); return s ? { first: (s.querySelector('button')||{}).className || '' } : null; }")
        chk("[guard] I'm new here asks first, Sign in with my code the first answer", r and "newacct-signin" in r["first"], r)
        step(pg, "Already have an account", "#newacct-confirm")
        pg.click("#newacct-confirm .newacct-signin"); pg.wait_for_timeout(600)
        chk("[guard] Sign in with my code -> the code screen", pg.evaluate("()=>!!document.querySelector('#stage .synccode-entry-panel') && !document.getElementById('newacct-confirm')"), screen(pg))
        pg.click(".synccode-entry-panel .back-link"); pg.wait_for_timeout(500)
        pg.click(".welcome-new"); pg.wait_for_timeout(700)
        pg.mouse.click(8, 140); pg.wait_for_timeout(500)
        chk("[guard] a tap outside the sheet is 'not now': Welcome", screen(pg) == "welcome" and not pg.evaluate("()=>!!document.getElementById('newacct-confirm')"), screen(pg))
        pg.click(".welcome-new"); pg.wait_for_timeout(700)
        pg.click("#newacct-confirm .newacct-fresh"); pg.wait_for_timeout(700)
        chk("[guard] Start a new account -> Select your classes", pg.evaluate("()=>!!document.querySelector('#stage .classselect-panel')"), screen(pg))
        errs_ok(pg, "had an account")
        ctx.close()

    # ------------------------------------------------------------------ signout
    def sec_signout():
        print("\nsign out, then sign back in (the owner, both classes)")
        CODE = "TEST-3832"
        acct = account("Gate Owner", OWNER, 4321, 777)
        ifc = account("Gate Owner", OWNER, 1234, 222)
        init = SEEN_ACCT + ("localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
                            "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.ifc.drill.v1', %s); localStorage.setItem('class26e.hadaccount', JSON.stringify({at:1,name:'Gate Owner'}));"
                            % (json.dumps(json.dumps(acct)), CODE, json.dumps(json.dumps(ifc))))
        ctx, pg = open_page(br, "phone", init=init, seed={"progress": {CODE: acct, CODE + "__ifc": ifc}})
        pg.wait_for_timeout(2000)
        pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(900)
        pg.click("#stage .signout-row"); pg.wait_for_timeout(600)
        step(pg, "Sign out sheet", "#signout-confirm")
        with pg.expect_navigation(timeout=15000):
            pg.click("#signout-confirm .signout-go")
        pg.wait_for_timeout(3600); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()"); pg.wait_for_timeout(600)
        # (384) Madison: "Signing out, signing out will just bring them to the welcome screen." (Get Started is for a device
        # with nothing on it; a signed-out one opens on Welcome, as in 383.)
        chk("[fix] after Sign out: Welcome, with Sign in on it (%s)" % screen(pg), screen(pg) == "welcome", screen(pg))
        r = pg.evaluate("()=>({ code: syncCode, name: store.firstName || '', pts: (store.lifetime||{}).points || 0, keys: Object.keys(localStorage).filter(k=>/^class26e\\.(drill\\.v1|synccode|ifc\\.drill\\.v1|activeclass)$/.test(k)), enrolled: localStorage.getItem('class26e.enrolled') })")
        chk("[guard] nothing of the account is left on the device (%s)" % r, not r["code"] and not r["name"] and not r["pts"] and not r["keys"], r)
        chk("[fix2] Fire Code's enrolment, a device setting, is kept through the sign out (%s)" % r["enrolled"], "ifc" in (r["enrolled"] or ""), r)
        to_welcome(pg)
        step(pg, "Welcome after sign out")
        pg.click(".welcome-new"); pg.wait_for_timeout(700)
        chk("[guard] I'm new here asks first after a sign out", pg.evaluate("()=>!!document.getElementById('newacct-confirm')"))
        pg.click("#newacct-confirm .newacct-signin"); pg.wait_for_timeout(600)
        pg.click(".synccode-entry-panel .back-link"); pg.wait_for_timeout(500)
        sign_in(pg, CODE.lower())
        r = pg.evaluate("""()=>({ screen: document.querySelector('#stage [data-screen]')?.dataset.screen, pts: store.lifetime.points, correct: store.lifetime.correct,
            name: store.firstName, pub: store.publicId, code: syncCode, bubble: !!document.querySelector('.class-bubble'), marker: localStorage.getItem('class26e.signedout'),
            enrolled: localStorage.getItem('class26e.enrolled') })""")
        chk("[guard] signed back in: Home, the progress, the name, the account's id and the class button (%s)" % r,
            r["screen"] == "home" and r["pts"] == 4321 and r["correct"] == 777 and r["name"] == "Gate Owner" and r["pub"] == OWNER and r["code"] == CODE and r["bubble"], r)
        chk("[guard] signed in again: no longer marked signed out", not r["marker"], r["marker"])
        fc = pg.evaluate("(c)=>(__cloud.progress[c + '__ifc'] || {}).lifetime || null", CODE)
        chk("[guard] Fire Code's cloud document is untouched by the sign out and back in (%s)" % fc, fc and fc["points"] == 1234 and fc["correct"] == 222, fc)
        offer = pg.evaluate("()=>[...document.querySelectorAll('.class-stack-item')].map(b=>b.className)")
        chk("[fix2] signed back in: the class button offers Fire Code (%s; enrolled %s)" % (offer, r["enrolled"]), any("is-ifc" in c for c in offer), offer)
        errs_ok(pg, "sign out and back in")
        if any("is-ifc" in c for c in offer):
            pg.click(".class-bubble"); pg.wait_for_timeout(700)
            with pg.expect_navigation(timeout=15000):
                pg.click(".class-stack-item.is-ifc")
            pg.wait_for_timeout(4200); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
            for _ in range(40):
                f = pg.evaluate("""()=>({ cls: window.NOVA_CLASS, screen: document.querySelector('#stage [data-screen]')?.dataset.screen || null,
                    pick: !!document.querySelector('#stage .ifc-enroll, #stage [data-screen="ifcenroll"], .ifc-analyze, #ifc-book-input'),
                    pts: ((typeof store !== 'undefined' && store || {}).lifetime || {}).points || 0, name: (typeof store !== 'undefined' && store || {}).firstName || '' })""")
                if f["screen"] == "home" and f["pts"] == 1234: break
                pg.wait_for_timeout(250)
            chk("[fix2] and tapping it opens Fire Code's Home - no enrolling, no book to pick - with its progress from the cloud (%s)" % f,
                f["cls"] == "ifc" and f["screen"] == "home" and not f["pick"] and f["pts"] == 1234 and f["name"] == "Gate Owner", f)
            errs_ok(pg, "Fire Code after signing back in")
        ctx.close()

    # ------------------------------------------------------------------ icon
    def sec_icon():
        print("\nan icon whose address carries the code (#k=)")
        CODE = "TEST-3834"
        acct = account("Gate Icon", "gatetest0004", 4321, 777)
        init = SEEN_ACCT + "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(acct)), CODE)
        ctx, pg = open_page(br, "phone", init=init, seed={"progress": {CODE: acct}}, suffix="#k=" + CODE)
        pg.wait_for_timeout(1500)
        chk("[guard] opened from the icon: Home, signed in", screen(pg) == "home" and pg.evaluate("()=>syncCode") == CODE, screen(pg))
        pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(900)
        pg.click("#stage .signout-row"); pg.wait_for_timeout(600)
        with pg.expect_navigation(timeout=15000):
            pg.click("#signout-confirm .signout-go")
        pg.wait_for_timeout(5000); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()"); pg.wait_for_timeout(800)
        r = pg.evaluate("()=>({ code: syncCode, name: store.firstName || '', href: location.href })")
        # (384) signed out, the device opens on Welcome - and is not signed back in
        chk("[fix] Sign out sticks: the reload does not sign the icon's code back in (%s, %s)" % (screen(pg), r), not r["code"] and not r["name"] and screen(pg) == "welcome", r)
        relaunch(pg, "#k=" + CODE, wait=5000)
        r = pg.evaluate("()=>({ code: syncCode, name: store.firstName || '', hash: location.hash })")
        chk("[fix] ... nor the next launch from that icon (%s, %s)" % (screen(pg), r), not r["code"] and not r["name"] and screen(pg) == "welcome" and not r["hash"], r)
        signed = sign_in(pg, CODE)
        chk("[guard] the code signs it back in", screen(pg) == "home" and pg.evaluate("()=>syncCode") == CODE, (signed, screen(pg)))
        relaunch(pg, "#k=" + CODE)
        chk("[guard] and the icon opens Home again", screen(pg) == "home" and pg.evaluate("()=>syncCode") == CODE and pg.evaluate("()=>store.lifetime.points") == 4321, screen(pg))
        errs_ok(pg, "icon sign out")
        ctx.close()
        # a device whose storage was wiped (iOS evicts it), opened from that icon
        ctx, pg = open_page(br, "phone", seed={"progress": {CODE: acct}}, suffix="#k=" + CODE, wait=4500)
        pg.wait_for_timeout(1500)
        r = pg.evaluate("()=>({ code: syncCode, pts: store.lifetime.points })")
        chk("[fix] a wiped device opened from that icon: its account back, on Home - not left on Get Started (%s, %s)" % (screen(pg), r), screen(pg) == "home" and r["code"] == CODE and r["pts"] == 4321, r)
        errs_ok(pg, "wiped device from the icon")
        ctx.close()

    # ------------------------------------------------------------------ settings
    def sec_settings():
        print("\nSettings > Sync > Enter a code")
        acct = account("Gate Nosync", "gatetest0005", 10, 2)
        init = SEEN_ACCT + "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.syncoff', '1');" % json.dumps(json.dumps(acct))
        ctx, pg = open_page(br, "phone", init=init)
        pg.evaluate("()=>showAppearance({ page: 'sync' })"); pg.wait_for_timeout(900)
        pg.click("#stage [data-row='entercode']"); pg.wait_for_timeout(400)
        F2 = "#stage .sync-enter-wrap input"
        v = type_code(pg, F2, "Nova sign-in code: TEST-3835\nKeep this.", paste=True)
        chk("[fix] the pasted message gives its code: %r" % v, v == "TEST-3835", v)
        v = type_code(pg, F2, "test 3835"); chk("[guard] typed in lower case with a space: %r" % v, v == "TEST-3835", v)
        fs = pg.evaluate("(s)=>parseFloat(getComputedStyle(document.querySelector(s)).fontSize)", F2)
        chk("[guard] the field is 16px+ (%s)" % fs, fs >= 15.95, fs)
        errs_ok(pg, "Settings > Sync")
        # Settings > Account > Name: the Change pill is small to look at, 44px to hit (its ::after) - a .next's overflow clipped that
        pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(900)
        hb = pg.evaluate("""()=>{ const b=document.querySelector('#stage .customize-namerow .profile-edit-btn'); if(!b) return null; const r=b.getBoundingClientRect();
            const cx=r.left+r.width/2, cy=r.top+r.height/2, half=Math.max(r.height, 44)/2 - 1;
            const hit=(x,y)=>{ const e=document.elementFromPoint(x,y); return !!e && (e===b || b.contains(e)); };
            return { box: [Math.round(r.width), Math.round(r.height)], above: hit(cx, cy - half), below: hit(cx, cy + half), wide: r.width >= 44 || (hit(cx - half, cy) && hit(cx + half, cy)) }; }""")
        chk("[fix2] Settings > Account > Name: the Change pill (%s) takes a tap anywhere in 44px round its middle (%s)" % (hb and hb["box"], hb),
            hb and hb["above"] and hb["below"] and hb["wide"], hb)
        ctx.close()

    for name in ("fresh", "signin", "had", "signout", "icon", "settings"):
        if not want(name): continue
        try: locals()["sec_" + name]()
        except Exception as e:
            chk("[guard] the %s walk ran to its end" % name, False, repr(e)[:300])
            for c in br.contexts:
                try: c.close()
                except Exception: pass
    br.close()

print("\n" + ("ALL PASS" if not fails else "FAILURES (%d): %s" % (len(fails), "; ".join(fails)[:1500])))
sys.exit(0 if not fails else 1)
