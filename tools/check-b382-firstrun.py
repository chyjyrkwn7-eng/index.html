#!/usr/bin/env python3
"""Build 382: the first run, end to end, and Home's two corner buttons in the tab bar's glass.

Madison: "The Home Screen is perfect, just make the daily question button and the class button match the
feel and look. Ensure the sign up process and start up screen are all good to go."

  A. A new academy account, walked from a cleared device (iPhone 440x956, installed): Get Started ->
     Welcome -> I'm new here -> New to Nova? -> Select your classes -> the loading screen -> Nova's
     talk (his name question, his character question with "Still to find") -> the tips -> Home.
  B. The same steps up to Nova on the other sizes (Pro Max at 85% 518x1125, SE 375x667, 320x568,
     iPad 834x1194, a laptop 1366x768) - Nova's dots on one line on the smallest.
  C. Returning: Welcome -> Sign in -> a code -> "This code belongs to" -> Sync This Device -> Home.
  D. The Fire Code class's first visit (the owner, enrolled, NOVA_CLASS "ifc"): Home and Nova's welcome.
  E. Home's daily question (ready and answered) and class button (and its list) wear the tab bar's
     glass: its body, rim and frost; the class button is the daily question's size on a phone and the
     chat button's on a tablet.
Every step: no page error or console error (blocked network aside), no sideways overflow, every
visible button at least 44px each way, text fields at least 16px.

Run:  python3 tools/check-b382-firstrun.py      (--against: copy the old index.html over first)"""
import io, json, os, re, sys, time, functools, http.server, threading, socket
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
HOOK = open(os.path.join(ROOT, "tools/check-sync.py")).read().split("HOOK = '''", 1)[1].split("'''", 1)[0]
SRC = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
SHOTS = os.environ.get("FR_SHOTS")   # a folder: save a picture of every step there
STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
 ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}} : mm(q); })();"""
OWNER = "xph5b57jbp5a"
SEED = {"firstName": "Casey", "avatarChar": "ninja", "onboardingComplete": True, "publicId": OWNER, "leaderboardOptIn": True,
        "lastModified": 1700000000000, "tourRev": 99, "novaMet": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True,
        "seenUnitSelectTour": True, "seenMainMenuTour": True, "seenRankingsTour": True, "seenAppearanceTour": True,
        "lifetime": {"points": 900, "answered": 300, "correct": 250}}
SEEN = ['class26e.freshstart', 'class26e.intro.seen', 'class26e.unithold.tip', 'class26e.daily.seen', 'class26e.savecode.asked', 'class26e.getstarted']

s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer.handle_error = lambda *a: None   # a page closed mid-download is not a failure
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(info)[:600]))

def body_for(w, h=0):
    # the device's own safe areas: a notched iPhone, an SE (status bar only), an iPad, a laptop (none)
    t, b = (62, 34) if w < 600 and h >= 800 else ((20, 0) if w < 600 else ((24, 20) if w < 1200 else (0, 0)))
    ins = {"top": "%dpx" % t, "bottom": "%dpx" % b, "left": "0px", "right": "0px"}
    return INSET_RE.sub(lambda m: ins[m.group(1)], SRC).replace("let fbDb = null;", "let fbDb = null;" + HOOK, 1)

def new(br, w, h, init=None, installed=True):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
    if installed: ctx.add_init_script(STANDALONE)
    if init: ctx.add_init_script(init)
    pg = ctx.new_page(); b = body_for(w, h)
    pg.route("**/index.html", lambda r, q, b=b: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:200]))
    pg.on("console", lambda m: errs.append("console.error: " + m.text[:200]) if m.type == "error" and "Failed to load resource" not in m.text and "net::" not in m.text else None)
    pg.errs = errs
    return ctx, pg

STEP = """()=>{ const de=document.documentElement; const vis=e=>{ const r=e.getBoundingClientRect(), c=getComputedStyle(e);
   return r.width>0 && r.height>0 && c.visibility!=='hidden' && c.display!=='none' && Number(c.opacity)>0.05 && r.bottom>0 && r.top<innerHeight; };
 const sel='#stage .next, #stage .back-link, #stage .cosmic-welcome-btn, .gs-go, #nova-intro .nt-go, #nova-intro .nt-ask-go, #nova-intro .nt-skip, #stage .class-card, .synccode-confirm .next';
 const onTop=e=>{ const r=e.getBoundingClientRect(); const x=Math.min(innerWidth-1, Math.max(0, r.left+r.width/2)), y=Math.min(innerHeight-1, Math.max(0, r.top+r.height/2)); const t=document.elementFromPoint(x, y); return !!t && (e===t || e.contains(t) || t.contains(e)); };
 const small=[...document.querySelectorAll(sel)].filter(vis).filter(onTop).filter(b=>{ const r=b.getBoundingClientRect(); return r.height<43.5 || r.width<43.5; })
   .map(b=>(b.className||'').toString().slice(0,40)+' '+Math.round(b.getBoundingClientRect().width)+'x'+Math.round(b.getBoundingClientRect().height));
 const fields=[...document.querySelectorAll('input[type=text], input:not([type])')].filter(vis).map(i=>parseFloat(getComputedStyle(i).fontSize)).filter(f=>f<15.95);
 const wide=[...document.querySelectorAll('#stage button, #stage input, #stage h1, #stage p, #nova-intro button')].filter(vis).filter(e=>{ const r=e.getBoundingClientRect(); return r.right>innerWidth+1 || r.left<-1; }).map(e=>(e.className||e.tagName).toString().slice(0,30));
 return { over: de.scrollWidth - de.clientWidth, small, fields, wide }; }"""

def step(pg, label, name):
    pg.wait_for_timeout(350)
    r = pg.evaluate(STEP)
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "fr-%s-%s.png" % (label, name)))
    chk("%s %s: no sideways overflow, buttons >= 44px, fields >= 16px (%s)" % (label, name, r),
        r["over"] <= 0 and not r["small"] and not r["fields"] and not r["wide"], r)
    return r

def to_welcome(pg):
    pg.goto(URL); pg.wait_for_timeout(3000)
    pg.evaluate("document.getElementById('splashscreen')?.remove()"); pg.wait_for_timeout(300)

def up_to_nova(pg, label, full):
    to_welcome(pg)
    if pg.evaluate("()=>!!document.querySelector('.gs-page')"):
        pg.wait_for_timeout(1700)
        if full: step(pg, label, "1-getstarted")
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1300)
        step(pg, label, "2-getstarted-end")
        pg.click(".gs-go"); pg.wait_for_timeout(1200)
    step(pg, label, "3-welcome")
    pg.click(".welcome-signin"); pg.wait_for_timeout(600); step(pg, label, "4-signin")
    pg.click(".synccode-entry-panel .back-link"); pg.wait_for_timeout(500)
    chk("%s: Back from Sign in is Welcome again" % label, pg.evaluate("()=>!!document.querySelector('[data-screen=welcome]')"))
    pg.click(".welcome-new"); pg.wait_for_timeout(600); step(pg, label, "5-newtonova")
    pg.click(".signupcheck-go"); pg.wait_for_timeout(700); step(pg, label, "6-classes")
    hid = pg.evaluate("()=>{ const b=document.querySelector('.classselect-panel #nextbtn'); return !b || b.hidden || b.getBoundingClientRect().height===0; }")
    chk("%s: Continue waits until a class is picked (no way past it unchosen)" % label, hid)
    pg.click(".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(300); step(pg, label, "7-classes-picked")
    pg.click(".classselect-panel #nextbtn"); pg.wait_for_timeout(300); pg.click("#classenroll-confirm .classenroll-yes")   # (384) the enroll confirm
    pg.wait_for_selector("#genprofile-overlay", timeout=8000); pg.wait_for_timeout(700)
    step(pg, label, "8-loading")
    pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=30000); pg.wait_for_timeout(2600)

def nova_dots(pg):
    return pg.evaluate("""()=>{ const p=document.querySelector('#nova-intro .nt-progress'); if(!p) return null; const ys=[...p.children].map(i=>Math.round(i.getBoundingClientRect().top));
      const r=p.getBoundingClientRect(); return { rows: new Set(ys).size, n: ys.length, right: Math.round(r.right), w: innerWidth }; }""")

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    # ---------- A. the whole first run on an iPhone ----------
    ctx, pg = new(br, 440, 956)
    up_to_nova(pg, "iphone", True)
    asked = set(); last_dots = None
    for _ in range(260):
        if not pg.evaluate("()=>!!document.getElementById('nova-intro')"): break
        if not last_dots or len(asked) < 3: d = nova_dots(pg); last_dots = d if d else last_dots
        ask = pg.evaluate("()=>{ const el=document.getElementById('nova-intro'); if(!el||!el.__nova||el.__nova.typing||!el.__nova.asking) return ''; return el.querySelector('.nt-ask-name')?'name':el.querySelector('.nt-ask-char')?'char':''; }")
        if ask == "name" and "name" not in asked:
            asked.add("name"); pg.wait_for_timeout(600); step(pg, "iphone", "9-nova-name")
            pg.fill(".nt-ask-input", "J.Smith"); pg.wait_for_timeout(250); step(pg, "iphone", "9b-nova-name-typed")
            pg.click(".nt-ask-name .nt-ask-go"); pg.wait_for_timeout(1500); continue
        if ask == "char" and "char" not in asked:
            asked.add("char"); pg.wait_for_timeout(900)
            later = pg.evaluate("()=>document.querySelectorAll('#nova-intro .nt-ask-later [role=img]').length")
            chk("iphone: his character question still shows the characters to find, greyed (%s)" % later, later > 0, later)
            pg.click(".nt-ask-char .avatarchar-option"); pg.wait_for_timeout(300); step(pg, "iphone", "10-nova-character")
            pg.click(".nt-ask-char .nt-ask-go"); pg.wait_for_timeout(800); continue
        st = pg.evaluate("""()=>{ const el=document.getElementById('nova-intro'); if(!el||!el.__nova||el.__nova.asking) return 'wait';
          if(el.__nova.index===el.__nova.count-1 && !el.__nova.typing) return 'last'; el.__nova.advance(); return 'next'; }""")
        if st == "last":
            pg.wait_for_timeout(700); d = nova_dots(pg); last_dots = d or last_dots
            step(pg, "iphone", "11-nova-last")
            chk("iphone: Nova's dots stay on one line on his last line (%s)" % (d,), d and d["rows"] == 1 and d["right"] <= d["w"], d)
            pg.click("#nova-intro .nt-go"); pg.wait_for_timeout(600); continue
        pg.wait_for_timeout(110)
    chk("iphone: he asked the name and the character", asked == {"name", "char"}, asked)
    pg.wait_for_timeout(3600)
    for _ in range(20):
        if not pg.evaluate("()=>!!document.getElementById('tour-next')"): break
        pg.evaluate("()=>document.getElementById('tour-next').click()"); pg.wait_for_timeout(320)
    pg.wait_for_timeout(1500)
    step(pg, "iphone", "12-home")
    st = pg.evaluate("()=>({ home: !!document.querySelector('.panel.home.screen-home-actual'), code: !!syncCode, done: !!store.onboardingComplete, name: store.firstName, ch: store.avatarChar, bar: !!document.querySelector('.bottomtabs:not([hidden])') })")
    chk("iphone: lands on Home with the account made (%s)" % st, st["home"] and st["code"] and st["done"] and st["name"] == "J.Smith" and st["ch"] and st["bar"], st)
    chk("iphone: no page or console errors over the whole first run (%s)" % pg.errs[:3], not pg.errs, pg.errs)
    ctx.close()
    # ---------- B. the other sizes, up to Nova ----------
    for label, w, h in (("promax85", 518, 1125), ("se", 375, 667), ("small320", 320, 568), ("ipad", 834, 1194), ("laptop", 1366, 768)):
        ctx, pg = new(br, w, h, installed=(w < 1200))
        up_to_nova(pg, label, False)
        pg.wait_for_timeout(1200)
        d = nova_dots(pg)
        step(pg, label, "9-nova")
        chk("%s: Nova's talk is up after the loading screen and his dots are one line inside the screen (%s)" % (label, d), d and d["rows"] == 1 and d["right"] <= d["w"], d)
        chk("%s: no page or console errors (%s)" % (label, pg.errs[:3]), not pg.errs, pg.errs)
        ctx.close()
    # ---------- C. returning: Sign in with a code ----------
    code = "WXYZ-7382"
    ctx, pg = new(br, 440, 956)
    to_welcome(pg)
    pg.evaluate("""(c)=>{ window.__cloud[c] = { firstName:'Riley', avatarChar:'ghost', onboardingComplete:true, leaderboardOptIn:true, tourRev:99, novaMet:99,
       lastModified: Date.now(), lifetime:{ points: 4321, correct: 310, answered: 400 } }; __fake([]); __ready(); }""", code)
    if pg.evaluate("()=>!!document.querySelector('.gs-page')"):
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1300); pg.click(".gs-go"); pg.wait_for_timeout(1000)
    pg.click(".welcome-signin"); pg.wait_for_timeout(500)
    pg.fill(".synccode-entry-panel input", code); pg.wait_for_timeout(200)
    step(pg, "signin", "1-code")
    pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(1200)
    step(pg, "signin", "2-belongs-to")
    who = pg.evaluate("()=>{ const c=document.querySelector('.synccode-confirm'); return c ? { shown: c.classList.contains('show'), name: (c.querySelector('.synccode-confirm-name')||{}).textContent } : null; }")
    chk("signin: the code names whose account it is before anything is synced (%s)" % (who,), who and who["shown"] and "Riley" in (who["name"] or ""), who)
    pg.click(".synccode-confirm .next"); pg.wait_for_timeout(2500)
    for _ in range(4):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^(Got it|Continue|Close|Done|Not now)$/.test(b.textContent.trim())).forEach(b=>b.click()); }"); pg.wait_for_timeout(300)
    step(pg, "signin", "3-home")
    st = pg.evaluate("()=>({ home: !!document.querySelector('.panel.home.screen-home-actual'), code: syncCode, name: store.firstName, pts: (store.lifetime||{}).points })")
    chk("signin: lands on Home as that account (%s)" % st, st["home"] and st["code"] == code and st["name"] == "Riley" and st["pts"] == 4321, st)
    chk("signin: no page or console errors (%s)" % pg.errs[:3], not pg.errs, pg.errs)
    # the splash a returning launch shows
    pg.reload(); pg.wait_for_timeout(500)
    sp = pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); return s ? { vis: getComputedStyle(s).visibility, w: Math.round(s.getBoundingClientRect().width) } : null; }")
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "fr-signin-4-splash.png"))
    chk("signin: a returning launch shows the start-up screen across the width (%s)" % (sp,), sp is None or (sp["w"] == 440), sp)
    ctx.close()
    # ---------- D. the Fire Code class's first visit ----------
    init = "(()=>{ if(sessionStorage.getItem('fr.d')) return; sessionStorage.setItem('fr.d','1'); localStorage.clear(); localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');" \
           " %s localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.classseen', JSON.stringify(['academy','ifc'])); localStorage.setItem('class26e.greet.ifc','pending'); localStorage.setItem('class26e.activeclass','ifc'); })()" % (
           json.dumps(json.dumps(SEED)), " ".join("localStorage.setItem('%s','99');" % k for k in SEEN))
    for label, w, h in (("ifc-iphone", 440, 956), ("ifc-ipad", 834, 1194)):
        ctx, pg = new(br, w, h, init)
        to_welcome(pg)
        cls = pg.evaluate("()=>window.NOVA_CLASS")
        chk("%s: the page is Fire Code (%s)" % (label, cls), cls == "ifc", cls)
        pg.wait_for_timeout(1500)
        greet = pg.evaluate("()=>!!document.getElementById('nova-class-greet')")
        if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "fr-%s-1-greeting.png" % label))
        chk("%s: Nova welcomes the new class" % label, greet, greet)
        for _ in range(60):
            if not pg.evaluate("()=>!!document.getElementById('nova-class-greet')"): break
            pg.evaluate("""()=>{ const el=document.getElementById('nova-class-greet'); if(!el||!el.__nova) return; if(el.__nova.index===el.__nova.count-1 && !el.__nova.typing){ const g=el.querySelector('.nt-go'); if(g) g.click(); } else el.__nova.advance(); }""")
            pg.wait_for_timeout(160)
        pg.wait_for_timeout(1800)
        step(pg, label, "2-home")
        st = pg.evaluate("()=>({ home: !!document.querySelector('.panel.home.screen-home-actual'), cls: !!document.querySelector('.class-bubble.is-ifc'), done: !!store.onboardingComplete, fresh: (store.lifetime||{}).points||0 })")
        chk("%s: lands on Fire Code's Home with the class button, nothing carried over (%s)" % (label, st), st["home"] and st["cls"] and st["done"] and st["fresh"] == 0, st)
        chk("%s: no page or console errors (%s)" % (label, pg.errs[:3]), not pg.errs, pg.errs)
        ctx.close()
    # ---------- E. Home's corner buttons are the tab bar's glass ----------
    init = "(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382'); %s" \
           " localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.classseen', JSON.stringify(['academy','ifc'])); })()" % (
           json.dumps(json.dumps(SEED)), " ".join("localStorage.setItem('%s','99');" % k for k in SEEN))
    GLASS = """()=>{ const g=e=>{ if(!e) return null; const c=getComputedStyle(e), r=e.getBoundingClientRect();
        const img=c.backgroundImage; return { body:c.backgroundColor, lift:(img.match(/linear-gradient\\([^)]*\\)[^)]*\\)/)||[''])[0], radials:(img.match(/radial-gradient/g)||[]).length,
          rim:c.borderTopColor, rimW:c.borderTopWidth, frost:c.backdropFilter||c.webkitBackdropFilter||'none', shadow:c.boxShadow.split(/,(?![^(]*\\))/)[0].trim(), w:Math.round(r.width*10)/10 }; };
      return { bar:g(document.querySelector('.bottomtabs')), chat:g(document.getElementById('chatdock-btn')), daily:g(document.querySelector('.daily-question-fab')),
        dq:(document.querySelector('.daily-question-fab')||{}).className, cls:g(document.querySelector('.class-bubble')), item:g(document.querySelector('.class-stack-item .csi-bubble')) }; }"""
    for label, w, h in (("iphone", 440, 956), ("ipad", 834, 1194)):
        for state in ("ready", "answered"):
            ctx, pg = new(br, w, h, init)
            to_welcome(pg)
            pg.evaluate("""(st)=>{ homeUnlocksOwed=()=>false; window.rankUpHolds=()=>false; if(st==='answered'){ store.dailyQuestionDate=dailyPeriodKey(); store.dailyQuestionCorrect=true; } else store.dailyQuestionDate='';
              persistLocally(); document.querySelectorAll('.rs-spot, .daily-alert').forEach(n=>n.remove()); showHome(); }""", state)
            pg.wait_for_timeout(2600)
            if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "fr-corners-%s-%s.png" % (label, state)))
            r = pg.evaluate(GLASS)
            b, q, c = r["bar"], r["daily"], r["cls"]
            same = lambda x: x and b and x["body"] == b["body"] and x["lift"] == b["lift"] and x["radials"] == 0 and x["rim"] == b["rim"] and x["rimW"] == b["rimW"] and x["frost"] == b["frost"] and x["shadow"] == b["shadow"]
            want = "is-ready" if state == "ready" else "is-done"
            chk("%s %s: the daily question is %s" % (label, state, want), want in (r["dq"] or ""), r["dq"])
            if state == "ready":
                # a waiting question keeps the rank's colour in its rim only: body, lift, frost and shadow are the bar's, no wash
                okq = q and b and q["body"] == b["body"] and q["lift"] == b["lift"] and q["radials"] == 0 and q["frost"] == b["frost"] and q["shadow"] == b["shadow"] and q["rim"] != b["rim"]
                chk("%s ready: the daily question is the tab bar's glass, the rank colour only in its rim (%s / bar %s)" % (label, q, b), okq, (q, b))
            else:
                chk("%s answered: the daily question is the tab bar's glass (%s / bar %s)" % (label, q, b), same(q), (q, b))
            chk("%s %s: the class button is the tab bar's glass, no colour wash (%s)" % (label, state, c), same(c), (c, b))
            if label == "iphone":
                chk("%s %s: the class button is the daily question's size (%s / %s)" % (label, state, c and c["w"], q and q["w"]), c and q and abs(c["w"] - q["w"]) <= 1, (c, q))
            else:
                chk("%s %s: the class button, opposite the chat button, is its size (%s / %s)" % (label, state, c and c["w"], r["chat"] and r["chat"]["w"]),
                    c and r["chat"] and abs(c["w"] - r["chat"]["w"]) <= 1, (c, r["chat"]))
            if state == "ready":
                pg.click(".class-bubble"); pg.wait_for_timeout(900)
                it = pg.evaluate(GLASS)["item"]
                if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "fr-corners-%s-classlist.png" % label))
                chk("%s: the class list's buttons wear the bar's lift and rim (%s)" % (label, it), it and it["lift"] == b["lift"] and it["rim"] == b["rim"] and it["radials"] == 0, it)
                pg.click(".class-bubble"); pg.wait_for_timeout(700)
            chk("%s %s: no page or console errors (%s)" % (label, state, pg.errs[:3]), not pg.errs, pg.errs)
            ctx.close()
    # ---------- F. another account ----------
    # (384, Madison: "everyone is gonna get the button") a different publicId HAS the class button now; it still gets no class
    # banner on Home (that is for the accounts on the invite list - check-b384-classes-open), and asking for Fire Code with only
    # the device's setting - the account is not enrolled in it - still stays in the academy
    other = dict(SEED); other["publicId"] = "pubnotowner382"
    for label, w, h in (("nonowner-iphone", 440, 956), ("nonowner-ipad", 834, 1194)):
        init = "(()=>{ if(sessionStorage.getItem('fr.f')) return; sessionStorage.setItem('fr.f','1'); localStorage.clear(); localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0383'); %s" \
               " localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.activeclass','ifc'); })()" % (
               json.dumps(json.dumps(other)), " ".join("localStorage.setItem('%s','99');" % k for k in SEEN))
        ctx, pg = new(br, w, h, init)
        to_welcome(pg)
        pg.evaluate("()=>{ homeUnlocksOwed=()=>false; if(!document.querySelector('.screen-home-actual')) showHome(); }")
        pg.wait_for_timeout(3200)   # past the 2.4s "new class" banner
        r = pg.evaluate("""()=>({ cls: window.NOVA_CLASS, active: localStorage.getItem('class26e.activeclass'), allowed: classSwitchAllowed(),
            bubble: !!document.querySelector('.class-bubble, .class-bubble-wrap'), banner: !!document.querySelector('#newclass-banner, #enrolled-banner'),
            home: !!document.querySelector('.panel.home.screen-home-actual') })""")
        if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "fr-%s-home.png" % label))
        chk("%s: activeclass 'ifc' without the owner's account stays in the academy and is cleared (%s)" % (label, r), r["cls"] == "academy" and r["active"] is None, r)
        chk("%s: another account has the class button (384) but no class banner on Home (%s)" % (label, r), r["home"] and r["allowed"] and r["bubble"] and not r["banner"], r)
        chk("%s: no page or console errors (%s)" % (label, pg.errs[:3]), not pg.errs, pg.errs)
        ctx.close()
    br.close()
srv.shutdown()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
