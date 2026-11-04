#!/usr/bin/env python3
"""Build 382: saving the sync code when it is given, and nobody signed out.

Madison: "We just have to ensure it's apparent that the user needs to
remember the code and write it down or something when they receive it and
we have to absolutely sure people can't be randomly logged out." And:
"People keep creating new accounts again and again instead of keeping the
same one."

  python3 tools/check-b382-savecode.py
  python3 tools/check-b382-savecode.py --against /path/to/old-index.html
  ONLY=signup,existing,test,reset,signin,heal,newhere,settings python3 tools/check-b382-savecode.py

Sections:
  signup   - a new sign-up (Nova) stops on the code card; Continue is off
             until the box is ticked or Save worked; it never shows again
  existing - an existing account with no savedCodeSaved sees it once after
             the server copy is read; a saved one never; the old banner is gone
  test     - never over a test
  reset    - a missing account document wipes nothing unless the server
             says the account AND its floor are gone
  signin   - signing in with a code: one line about keeping it, no card,
             and the device stays onboarded (old documents lack the flag)
  heal     - the boot self-heal minting a new code asks for it to be saved
  newhere  - "I'm new here" on a device that has held an account asks first,
             Sign in primary; a fresh device goes straight on
  settings - Settings > Sync has the code and a Save it row that saves

Firestore is stubbed (the CDN is blocked here). Taps are real hit-tested
clicks. The codes are fake (TEST-0000 style), never real ones.
"""
import functools, http.server, io, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(ROOT, "index.html")
ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
INSET = {"top": "59px", "bottom": "34px", "left": "0px", "right": "0px"}

HOOK = '''
  window.__cloud = {};
  window.__snap = null;
  window.__fake = function(){
    const clone = v => JSON.parse(JSON.stringify(v));
    const docRef = (name, id) => ({
      get: function(){ const d = name === "progress" ? window.__cloud[id] : null;
        return Promise.resolve(d ? { exists: true, metadata: { fromCache: false }, data: () => clone(d) }
                                 : { exists: false, metadata: { fromCache: false } }); },
      set: function(v){ if(name === "progress") window.__cloud[id] = clone(v); return Promise.resolve(); },
      update: function(){ return Promise.resolve(); },
      delete: function(){ if(name === "progress") delete window.__cloud[id]; return Promise.resolve(); },
      onSnapshot: function(){ return function(){}; },
      collection: function(n2){ return { doc: i2 => docRef(n2, i2), get: () => Promise.resolve({ forEach(){}, docs: [] }) }; }
    });
    fbDb = { collection: function(name){ return { doc: id => docRef(name, id),
               where: function(){ return this; }, limit: function(){ return this; }, orderBy: function(){ return this; },
               get: () => Promise.resolve({ forEach(){}, docs: [], empty: true }) }; },
             runTransaction: function(fn){ return Promise.reject(new Error("no transactions in the stub")); } };
    onSnapshotResilient = function(ref, onNext){
      if(ref && ref.get && !ref.where){ window.__snap = onNext; }
      setTimeout(function(){ try{ onNext({ forEach: function(){}, docs: [] }); }catch(e){} }, 20);
      return function(){};
    };
    firebaseBecameReady();
  };
'''
src = io.open(SRC, encoding="utf-8").read()
BODY = re.sub(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)", lambda m: INSET[m.group(1)], src) \
    .replace("let fbDb = null;", "let fbDb = null;" + HOOK, 1)
m = re.search(r'APP_BUILD\s*=\s*"([^"]+)"', src)
VERSION_JSON = json.dumps({"build": m.group(1) if m else "", "note": "", "frameId": "", "frameNote": "", "force": False})

SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
        "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
        "localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');"
        "localStorage.setItem('class26e.penal256578.seen','1');")
def store(**extra):
    d = {"firstName": "Gate Tester", "avatarChar": "ninja", "onboardingComplete": True, "leaderboardOptIn": False,
         "tourRev": 999, "novaMet": 99, "lastModified": 1790400000000,
         # every week's recap counted as heard: on a recap day Nova talks first and the card rightly waits
         "novaHeard": {"@recap": 99991231},
         "lifetime": {"points": 420, "correct": 88}, "testStats": {"Penal Code": {"plays": 1}}}
    d.update(extra)
    return d

so = socket.socket(); so.bind(("127.0.0.1", 0)); PORT = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT)).serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

fails = []
def ck(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:220]) if detail != "" else ""))
    if not ok: fails.append(name)
def want(sec): return not ONLY or sec in ONLY

def open_page(br, init, w=440, h=956, errs=None):
    ctx = br.new_context(viewport={"width": w, "height": h})
    ctx.add_init_script("try{" + init + "}catch(e){}")
    pg = ctx.new_page()
    if errs is not None: pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"}, body=VERSION_JSON))
    pg.goto(URL); pg.wait_for_timeout(2800)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    return ctx, pg

def init_account(code, st):
    return SEEN + "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(st)) + \
        ("localStorage.setItem('class26e.synccode','%s');" % code if code else "")

def card_up(pg):
    return pg.evaluate("()=>!!document.getElementById('savecode-card')")

def wait_card(pg, ms):
    t = 0
    while t < ms:
        if card_up(pg): return True
        pg.wait_for_timeout(250); t += 250
    return card_up(pg)

def connect(pg, code, cloud_store):
    pg.evaluate("(a)=>{ window.__cloud[a[0]] = a[1]; __fake(); }", [code, cloud_store])

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)

    if want("signup"):
        print("\n1. a new sign-up stops on the code card")
        errs = []
        ctx, pg = open_page(br, SEEN, errs=errs)
        pg.evaluate("()=>{ startSignupWithNova(); }")
        pg.wait_for_timeout(11500)
        reached = False; steps = 0; last = None
        for steps in range(160):
            st = pg.evaluate("""()=>{ const n=document.getElementById('nova-intro'); if(!n||!n.__nova) return {gone:true};
              return { asking:n.__nova.asking, typing:n.__nova.typing, i:n.__nova.index, count:n.__nova.count,
                       name: !!n.querySelector('.nt-ask-name input'), char: !!n.querySelector('.nt-ask-char .avatarchar-option'),
                       card: !!document.getElementById('savecode-card'), final: !!n.querySelector('.nt-bubble.is-final') }; }""")
            last = st
            if st.get("card"): reached = True; break
            if st.get("gone"): pg.wait_for_timeout(400); continue
            if st["typing"]: pg.evaluate("()=>document.getElementById('nova-intro').__nova.advance()"); pg.wait_for_timeout(120); continue
            if st["asking"]:
                if st["name"]:
                    pg.fill("#nova-intro .nt-ask-name input", "Gate Tester"); pg.wait_for_timeout(100)
                    pg.click("#nova-intro .nt-ask-name .nt-ask-go"); pg.wait_for_timeout(1300); continue
                if st["char"]:
                    pg.click("#nova-intro .nt-ask-char .avatarchar-option"); pg.wait_for_timeout(200)
                    pg.click("#nova-intro .nt-ask-char .nt-ask-go"); pg.wait_for_timeout(900); continue
                pg.wait_for_timeout(400); continue
            if st["final"]: break
            pg.evaluate("()=>document.getElementById('nova-intro').__nova.advance()"); pg.wait_for_timeout(160)
        ck("the sign-up reaches the code card (in Nova's introduction)", reached, last)
        if not reached:
            for n in ("the code is large, monospace and is the account's code", "Continue starts disabled",
                      "a cancelled Save does not enable Continue", "ticking the box enables Continue, unticking disables it",
                      "a Save that worked enables Continue", "Nova waits while the card is up", "every control is 44px or taller",
                      "Continue closes it, records it saved and Nova goes on", "it does not show again on Home"):
                ck(n, False, "no card")
        else:
            c = pg.evaluate("""()=>{ const v=document.querySelector('#savecode-card .savecode-value'); const cs=getComputedStyle(v);
              return { text:v.textContent, code:syncCode, px:parseFloat(cs.fontSize), mono:/mono|menlo|consolas/i.test(cs.fontFamily),
                       body:(document.querySelector('#savecode-card .savecode-body')||{}).textContent||'' }; }""")
            ck("the code is large, monospace and is the account's code",
               c["text"] == c["code"] and bool(c["code"]) and c["px"] >= 24 and c["mono"], c)
            dis = lambda: pg.evaluate("()=>document.querySelector('#savecode-card .savecode-continue').disabled")
            ck("Continue starts disabled", dis() is True)
            # (384) Save it shares on a phone and copies on a computer (check-b384-glitches save); this context is Chromium's
            # desktop at a phone's size, so it is told it is a phone where the phone's share sheet is what is checked
            pg.evaluate("()=>{ a2hsDeviceGuess = () => 'apple'; }")
            pg.evaluate("""()=>{ Object.defineProperty(navigator,'share',{configurable:true,value:()=>Promise.reject(Object.assign(new Error('x'),{name:'AbortError'}))}); }""")
            pg.click("#savecode-card .savecode-save"); pg.wait_for_timeout(400)
            ck("a cancelled Save does not enable Continue", dis() is True)
            pg.click("#savecode-card .savecode-ack"); pg.wait_for_timeout(150)
            on = dis()
            pg.click("#savecode-card .savecode-ack"); pg.wait_for_timeout(150)
            ck("ticking the box enables Continue, unticking disables it", on is False and dis() is True)
            pg.evaluate("""()=>{ window.__shared=null; Object.defineProperty(navigator,'share',{configurable:true,value:d=>{window.__shared=d;return Promise.resolve();}}); }""")
            pg.click("#savecode-card .savecode-save"); pg.wait_for_timeout(400)
            shared = pg.evaluate("()=>window.__shared && window.__shared.text")
            ck("a Save that worked enables Continue", dis() is False and shared and c["code"] in shared, shared)
            ck("Nova waits while the card is up", pg.evaluate("()=>document.getElementById('nova-intro').__nova.asking") is True)
            sizes = pg.evaluate("""()=>['.savecode-save','.savecode-ack','.savecode-continue'].map(s=>Math.round(document.querySelector('#savecode-card '+s).getBoundingClientRect().height))""")
            ck("every control is 44px or taller", min(sizes) >= 44, sizes)
            i0 = pg.evaluate("()=>document.getElementById('nova-intro').__nova.index")
            pg.click("#savecode-card .savecode-continue"); pg.wait_for_timeout(700)
            after = pg.evaluate("""()=>({ card:!!document.getElementById('savecode-card'), saved:store.savedCodeSaved,
                 key:!!localStorage.getItem('class26e.savecode.card'), i:document.getElementById('nova-intro').__nova.index })""")
            ck("Continue closes it, records it saved and Nova goes on",
               not after["card"] and after["saved"] is True and after["key"] and after["i"] > i0, after)
            pg.evaluate("()=>{ const n=document.getElementById('nova-intro'); if(n) n.__nova.close(); }")
            pg.wait_for_timeout(600)
            shown = []
            for _ in range(3):
                pg.evaluate("()=>{ cloudConfirmedFor = syncCode; showHome(); setTimeout(checkSaveCodeReminder, 50); }")
                pg.wait_for_timeout(1200); shown.append(card_up(pg))
            ck("it does not show again on Home", shown == [False, False, False], shown)
        ck("no JS errors in the sign-up", not errs, errs[:2])
        ctx.close()

    if want("existing"):
        print("\n2. an existing account that never confirmed saving")
        errs = []
        st = store()
        ctx, pg = open_page(br, init_account("TEST-2222", st), errs=errs)
        connect(pg, "TEST-2222", st)
        up = wait_card(pg, 9000)
        # build 383: Madison, "The save your sync code pop up, don't do that for the existing accounts" - it never shows
        ck("(383) never sees the card on Home, even once the server copy is read", not up)
        ck("the old banner is gone", pg.evaluate("()=>!document.getElementById('save-code')"))
        if up:
            v = pg.evaluate("()=>document.querySelector('#savecode-card .savecode-value').textContent")
            ck("showing its own code", v == "TEST-2222", v)
            pg.click("#savecode-card .savecode-ack"); pg.click("#savecode-card .savecode-continue"); pg.wait_for_timeout(500)
        again = []
        for _ in range(3):
            pg.evaluate("()=>{ showHome(); setTimeout(checkSaveCodeReminder, 50); }"); pg.wait_for_timeout(1000); again.append(card_up(pg))
        ck("and only once", again == [False, False, False], again)
        pg.reload(); pg.wait_for_timeout(2800); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
        connect(pg, "TEST-2222", st)
        ck("not on the next launch either", not wait_card(pg, 7000))
        ck("no JS errors", not errs, errs[:2])
        ctx.close()

        st2 = store(savedCodeSaved=True)
        ctx, pg = open_page(br, init_account("TEST-3333", st2))
        connect(pg, "TEST-3333", st2)
        ck("an account that already saved it never sees it", not wait_card(pg, 8000))
        ctx.close()

        st3 = store(); cloud3 = store(savedCodeSaved=True, lastModified=1790400001000)
        ctx, pg = open_page(br, init_account("TEST-4444", st3))
        connect(pg, "TEST-4444", cloud3)
        ck("nor one that saved it on another device", not wait_card(pg, 8000))
        ctx.close()

        ctx, pg = open_page(br, init_account("TEST-5555", store()))
        ck("nor before the server copy has been read", not wait_card(pg, 4000))
        ctx.close()

    if want("test"):
        print("\n3. never over a test")
        st = store()
        ctx, pg = open_page(br, init_account("TEST-6666", st))
        pg.evaluate("()=>{ beginRun([0,1,2,3,4], 'Drill'); }"); pg.wait_for_timeout(2500)
        mid = pg.evaluate("()=>({ test: testInProgress, home: !!stage.querySelector('.screen-home-actual') })")
        connect(pg, "TEST-6666", st)
        ck("a test is running (%s)" % mid, mid["test"] is True and not mid["home"], mid)
        ck("the card does not land on it", not wait_card(pg, 8000))
        pg.evaluate("()=>{ try{ checkSaveCodeReminder(); }catch(e){} }"); pg.wait_for_timeout(500)
        ck("not even when asked directly mid-test", not card_up(pg))
        ctx.close()

    if want("reset"):
        print("\n4. a missing account document is checked before anything is wiped")
        st = store(savedCodeSaved=True)
        ctx, pg = open_page(br, init_account("TEST-7777", st))
        connect(pg, "TEST-7777", st)
        pg.wait_for_timeout(1500)
        pg.evaluate("()=>{ attachLiveListener(syncCode); }"); pg.wait_for_timeout(200)
        pg.evaluate("""()=>{ const s=window.__snap; s({ exists:true, metadata:{fromCache:false}, data:()=>JSON.parse(JSON.stringify(window.__cloud['TEST-7777'])) });
                         s({ exists:false, metadata:{fromCache:false} }); }""")
        pg.wait_for_timeout(4500)
        r = pg.evaluate("()=>({ code:syncCode, ls:localStorage.getItem('class26e.synccode'), welcome:!!stage.querySelector('[data-screen=\"welcome\"]') })")
        ck("a stray server 'missing' while the account is still there signs nobody out", r["code"] == "TEST-7777" and r["ls"] == "TEST-7777" and not r["welcome"], r)
        pg.evaluate("()=>{ window.__cloud['TEST-7777__floor'] = { lastModified: 1790400000000 }; delete window.__cloud['TEST-7777']; attachLiveListener(syncCode); }")
        pg.wait_for_timeout(200)
        pg.evaluate("""()=>{ const s=window.__snap; s({ exists:true, metadata:{fromCache:false}, data:()=>({ lastModified:1790400000000 }) });
                         s({ exists:false, metadata:{fromCache:false} }); }""")
        pg.wait_for_timeout(11500)
        r = pg.evaluate("()=>({ code:syncCode })")
        ck("nor does the account going while its backup (floor) stays", r["code"] == "TEST-7777", r)
        pg.evaluate("()=>{ delete window.__cloud['TEST-7777__floor']; window.__cloud['TEST-7777']={lastModified:1790400000000}; attachLiveListener(syncCode); }")
        pg.wait_for_timeout(200)
        pg.evaluate("""()=>{ const s=window.__snap; s({ exists:true, metadata:{fromCache:false}, data:()=>({ lastModified:1790400000000 }) });
                         delete window.__cloud['TEST-7777']; s({ exists:false, metadata:{fromCache:false} }); }""")
        pg.wait_for_timeout(13000)
        r = pg.evaluate("()=>({ code:syncCode, welcome:!!stage.querySelector('[data-screen=\"welcome\"]') })")
        ck("a real reset (account and floor both gone) still resets this device", r["code"] is None and r["welcome"], r)
        ctx.close()

    if want("signin"):
        print("\n5. signing in with a code")
        ctx, pg = open_page(br, SEEN)
        pg.evaluate("""()=>{ window.__cloud['TEST-0000'] = { firstName:'Gate Tester', onboardingComplete:false, lastModified:1790400000000,
                          lifetime:{ points:0, correct:0 } }; __fake(); showWelcomeCodeEntry(); }""")
        pg.wait_for_timeout(500)
        pg.fill(".synccode-entry-panel input", "TEST0000"); pg.wait_for_timeout(100)
        pg.click("#nextbtn"); pg.wait_for_timeout(900)
        note = pg.evaluate("""()=>{ const c=document.querySelector('.synccode-confirm.show'); if(!c) return null;
              const n=c.querySelector('.signin-keep-note'); return n ? n.textContent : ''; }""")
        ck("the confirmation says one line about keeping the code", bool(note) and "safe" in note.lower(), note)
        pg.click(".synccode-confirm .next"); pg.wait_for_timeout(4200)
        r = pg.evaluate("""()=>({ code:syncCode, onb:store.onboardingComplete,
              saved:JSON.parse(localStorage.getItem('class26e.drill.v1')||'{}').onboardingComplete,
              cardKey:!!localStorage.getItem('class26e.savecode.card') })""")
        ck("signed in, and onboarded on this device even though the cloud copy said not", r["code"] == "TEST-0000" and r["onb"] is True and r["saved"] is True, r)
        ck("the card is marked done on this device (they typed the code)", r["cardKey"], r)
        pg.reload(); pg.wait_for_timeout(2800); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
        r = pg.evaluate("()=>({ welcome:!!stage.querySelector('[data-screen=\"welcome\"]'), home:!!stage.querySelector('.screen-home-actual'), code:syncCode })")
        ck("the next launch is Home, not Welcome", r["home"] and not r["welcome"] and r["code"] == "TEST-0000", r)
        ctx.close()

    if want("heal"):
        print("\n6. the boot self-heal minting a new code")
        ctx, pg = open_page(br, init_account(None, store(savedCodeSaved=True)))
        r = pg.evaluate("()=>({ code:syncCode, saved:store.savedCodeSaved })")
        ck("a minted code is a code nobody has saved yet", bool(r["code"]) and r["saved"] is False, r)
        ctx.close()

    if want("newhere"):
        print("\n7. \"I'm new here\" on a device that has held an account")
        ctx, pg = open_page(br, init_account("TEST-8888", store(savedCodeSaved=True)))
        pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(600)
        mk = pg.evaluate("()=>localStorage.getItem('class26e.hadaccount')")
        ck("an account on Home leaves a marker with no code in it", bool(mk) and "TEST" not in mk, mk)
        ctx.close()
        ctx, pg = open_page(br, SEEN + "localStorage.setItem('class26e.hadaccount', JSON.stringify({at:1790400000000,name:'Gate Tester'}));")
        pg.evaluate("()=>{ welcomeTraceSkip=false; showWelcome(); }"); pg.wait_for_timeout(600)
        geo = pg.evaluate("""()=>{ const a=document.querySelector('.welcome-signin'), b=document.querySelector('.welcome-new');
            if(!a||!b) return null; const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
            return { aH:Math.round(ra.height), aW:Math.round(ra.width), bW:Math.round(rb.width), aFirst: ra.top < rb.top,
                     aPrimary: a.classList.contains('playbtn') }; }""")
        ck("Welcome: Sign in is first, primary, full size", geo and geo["aFirst"] and geo["aPrimary"] and geo["aH"] >= 44 and geo["aW"] >= geo["bW"] - 2, geo)
        pg.click(".welcome-new"); pg.wait_for_timeout(700)
        sh = pg.evaluate("""()=>{ const s=document.getElementById('newacct-confirm'); if(!s) return null;
            const b=[...s.querySelectorAll('button')]; return { n:b.length, first:b[0].className, firstText:b[0].textContent,
            h:b.map(x=>Math.round(x.getBoundingClientRect().height)), body:(s.querySelector('.savecode-body')||{}).textContent }; }""")
        ck("a confirm sheet comes first", sh is not None, sh)
        ck("its primary is Sign in", sh and "newacct-signin" in sh["first"] and sh["n"] == 2 and min(sh["h"]) >= 44, sh)
        if sh:
            pg.click("#newacct-confirm .newacct-signin"); pg.wait_for_timeout(700)
        ck("Sign in goes to the code screen", pg.evaluate("()=>!!stage.querySelector('.synccode-entry-panel') && !document.getElementById('newacct-confirm')"))
        pg.evaluate("()=>{ showWelcome(); }"); pg.wait_for_timeout(500)
        pg.click(".welcome-new"); pg.wait_for_timeout(700)
        if pg.evaluate("()=>!!document.getElementById('newacct-confirm')"):
            pg.click("#newacct-confirm .newacct-fresh"); pg.wait_for_timeout(900)
            ok = pg.evaluate("()=>!document.getElementById('newacct-confirm') && !stage.querySelector('[data-screen=\"welcome\"]')")
        else: ok = False
        ck("Start a new account goes on with sign-up", ok)
        ctx.close()
        ctx, pg = open_page(br, SEEN)
        pg.evaluate("()=>{ showWelcome(); }"); pg.wait_for_timeout(600)
        pg.click(".welcome-new"); pg.wait_for_timeout(700)
        r = pg.evaluate("()=>({ sheet:!!document.getElementById('newacct-confirm'), check:!!stage.querySelector('.signupcheck-panel') })")
        ck("a device that never held an account goes straight to the usual check", not r["sheet"] and r["check"], r)
        ctx.close()

    if want("settings"):
        print("\n8. Settings > Sync: the code and Save it")
        ctx, pg = open_page(br, init_account("TEST-9999", store()))
        pg.evaluate("()=>showAppearance({ focus:'sync' })"); pg.wait_for_timeout(1300)
        r = pg.evaluate("""()=>{ const s=document.getElementById('settings-sync-sect'); if(!s) return null;
            const row=s.querySelector('.sync-save-code-row'); const r=row?row.getBoundingClientRect():null;
            return { codeRow:!!s.querySelector('.sync-code-row'), save: r ? Math.round(r.height) : 0,
                     inView: r ? (r.top >= 0 && r.bottom <= innerHeight) : false }; }""")
        ck("the code row and a Save it row, 44px+, in view when Settings opens on Sync", r and r["codeRow"] and r["save"] >= 44 and r["inView"], r)
        if r and r["save"]:
            pg.evaluate("()=>{ a2hsDeviceGuess = () => 'apple'; }")   # (384) a phone - see section 1
            pg.evaluate("""()=>{ window.__shared=null; Object.defineProperty(navigator,'share',{configurable:true,value:d=>{window.__shared=d;return Promise.resolve();}}); }""")
            pg.click("#settings-sync-sect .sync-save-code-row"); pg.wait_for_timeout(500)
            s = pg.evaluate("()=>({ text: window.__shared && window.__shared.text, saved: store.savedCodeSaved })")
            ck("Save it hands the code to the share sheet and records it saved", s["text"] and "TEST-9999" in s["text"] and s["saved"] is True, s)
        else:
            ck("Save it hands the code to the share sheet and records it saved", False, "no row")
        ctx.close()
    br.close()

print("\n%s (%d failure(s))" % ("ALL PASS" if not fails else "FAILED: " + "; ".join(fails), len(fails)))
raise SystemExit(1 if fails else 0)
