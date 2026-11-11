"""Shared helpers for the 384.23 gates (check-b384-installfirst.py, check-b384-signupshort.py) and the flow recording
(record-b384-flow.py): a served copy of index.html, a page opened as a given device (user agent, touch, installed or in a tab,
an in-memory Firestore stub), and a WALKER that signs a new account up the way a person does and counts what it took.

Counting is read off the page, never typed: a tap is a button the walker pressed, plus one per box Nova showed (the page's own
__nova.count lines, each taken once), a screen is a distinct data-screen / panel the stage held."""
import functools, http.server, io, json, os, re, socket, threading, time
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")

UA = {
    "iphone-safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1",
    "iphone-chrome": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/141.0.7390.41 Mobile/15E148 Safari/604.1",
    "iphone-firefox": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/141.0 Mobile/15E148 Safari/605.1.15",
    "iphone-edge": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 EdgiOS/141.0.3537.71 Mobile/15E148 Safari/605.1.15",
    # iPadOS asks for the desktop site and says Macintosh; the touch screen is what tells it from a Mac
    "ipad-safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
    "mac-safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
    "mac-chrome": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "mac-firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
    "win-chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "win-edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
    "win-firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "linux-chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "android-chrome": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
    "android-firefox": "Mozilla/5.0 (Android 14; Mobile; rv:141.0) Gecko/141.0 Firefox/141.0",
    "android-samsung": "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/26.0 Chrome/122.0.0.0 Mobile Safari/537.36",
    "android-tablet-chrome": "Mozilla/5.0 (Linux; Android 14; SM-X710) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    # browsers inside other apps
    "iphone-instagram": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/22A100 Instagram 380.0.0.28.104 (iPhone16,2; iOS 26_0; en_US; en-US; scale=3.00; 1290x2796; 700000000)",
    "iphone-facebook": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/22A100 [FBAN/FBIOS;FBAV/500.0.0.0.0;FBBV/1;FBDV/iPhone16,2;FBMD/iPhone;FBSN/iOS;FBSV/26.0;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5]",
    "iphone-tiktok": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/22A100 musical_ly_40.0.0 BytedanceWebview/d8a21c6",
    "iphone-webview": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/22A100",
    "android-facebook": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Build/AP1A) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/141.0.0.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/500.0.0.0.0;]",
    "android-webview": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Build/AP1A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/141.0.0.0 Mobile Safari/537.36",
}
# which user agents are touch phones/tablets (the page's own rule, restated here only to decide what the context emulates)
TOUCH = {"ipad-safari", "android-tablet-chrome"} | {k for k in UA if k.startswith(("iphone", "android"))}

STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){},
       addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""
# the Firestore stub (the CDN is blocked here): every read finds nothing, every write resolves
FAKE_FIREBASE = """
(function(){
  function docRef(){ return {
      get: function(){ return Promise.resolve({ exists:false, data:function(){ return null; } }); },
      set: function(){ return Promise.resolve(); }, update: function(){ return Promise.resolve(); }, delete: function(){ return Promise.resolve(); },
      onSnapshot: function(next){ setTimeout(function(){ next({ exists:false, data:function(){ return null; }, metadata:{fromCache:false} }); }, 40); return function(){}; } }; }
  function collRef(){ var c = { doc: function(){ return docRef(); }, where: function(){ return c; }, orderBy: function(){ return c; }, limit: function(){ return c; },
      get: function(){ return Promise.resolve({ empty:true, docs:[], forEach:function(){}, size:0 }); },
      onSnapshot: function(next){ setTimeout(function(){ next({ forEach: function(){}, docs:[], empty:true, size:0, docChanges:function(){ return []; }, metadata:{fromCache:false} }); }, 60); return function(){}; } };
    return c; }
  window.firebase = { apps: [], initializeApp: function(){ this.apps.push({}); },
    firestore: function(){ return { collection: collRef, batch: function(){ return { set(){}, update(){}, delete(){}, commit: function(){ return Promise.resolve(); } }; } }; } };
  window.firebase.firestore.FieldValue = { delete: function(){ return null; }, serverTimestamp: function(){ return Date.now(); }, arrayUnion: function(){ return []; }, increment: function(n){ return n; } };
})();"""
# an existing, finished account (the gates' usual fixture: tourRev and the seen marks so no tour or pop-up lands over it)
SEED = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,"leaderboardOptIn":true,"lastModified":1700000000000,'
        '"tourRev":99,"seenProfileTour":true,"seenModeSelectTour":true,"seenUnitSelectTour":true,"seenMainMenuTour":true,"seenClassTip":true,'
        '"seenRankingsTour":true,"seenAppearanceTour":true,"lifetime":{"points":1200,"answered":540,"correct":498,"drillPlays":6,"examPlays":2,"gamePlays":1,"perfectTests":4,"currentStreak":3,"longestStreak":5}}')
SEED_JS = ("try{localStorage.setItem('class26e.drill.v1', %s);localStorage.setItem('class26e.synccode','MADI-0001');"
           "localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
           "localStorage.setItem('class26e.daily.seen','x');localStorage.setItem('class26e.savecode.asked','1');localStorage.setItem('class26e.savecode.card','1');"
           "localStorage.setItem('class26e.a2hs','x1');localStorage.setItem('class26e.getstarted','1');}catch(e){}") % json.dumps(SEED)


def load_src(path=None):
    return io.open(path or os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def patched(src, insets):
    t, r, b, l = insets
    v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return INSET_RE.sub(lambda m: v[m.group(1)], src)


def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port


def new_page(br, html, url, *, ua="iphone-safari", w=440, h=956, installed=False, seeded=False, extra_init=(), insets=(0, 0, 0, 0), scale=2):
    """a page as a device would arrive at it. ua is a key of UA (or a raw string). Returns (ctx, page)."""
    uas = UA.get(ua, ua)
    touch = ua in TOUCH
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=scale, user_agent=uas, has_touch=touch, is_mobile=False)
    ctx.add_init_script("Object.defineProperty(navigator,'maxTouchPoints',{get:()=>%d,configurable:true});" % (5 if touch else 0))
    if installed: ctx.add_init_script(STANDALONE)
    ctx.add_init_script(FAKE_FIREBASE)
    if seeded: ctx.add_init_script(SEED_JS)
    for sc in extra_init: ctx.add_init_script(sc)
    page = ctx.new_page()
    body = patched(html, insets)
    page.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}, body=b))
    return ctx, page


def boot(pg, url, settle=1800):
    """open it, let the splash step aside (the Firebase CDN is blocked, so it never clears itself when an account is on the device)"""
    pg.goto(url)
    pg.wait_for_timeout(settle)
    pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); if(s) s.remove(); }")
    pg.wait_for_timeout(500)


SCREEN_JS = """()=>{ const st=document.getElementById('stage'); const f=st&&st.firstElementChild; if(!f) return '';
  return f.dataset && f.dataset.screen ? f.dataset.screen : (f.className||'').split(/\\s+/).filter(c=>/panel|cosmic|gs-|page/.test(c)).join('.') || f.tagName; }"""


def screen_of(pg):
    return pg.evaluate(SCREEN_JS)


def novastate(pg):
    return pg.evaluate("""()=>{ const n=document.getElementById('nova-intro'); if(!n||!n.__nova) return null;
      return { asking:n.__nova.asking, typing:n.__nova.typing, i:n.__nova.index, count:n.__nova.count,
        name: !!n.querySelector('.nt-ask-name input'), char: !!n.querySelector('.nt-ask-char .avatarchar-option'),
        card: !!document.getElementById('savecode-card') }; }""")


def walk_signup(pg, name="J.Smith", log=None, shot=None):
    """Sign a new account up from the first screen the app shows, as a person does, until the last tip has been tapped.
    Returns {taps, pages, nova_boxes, tips, onboarded, code, name, avatar}. `taps` is what a person presses: each button, one per Nova box
    (a box is a tap; the name, the partner and the code card are each their own presses), one per tip. `shot(label)` is called at each
    new screen when given."""
    taps = 0
    pages = []
    def see(label):
        if not pages or pages[-1] != label:
            pages.append(label)
            if log: log("  screen: " + label)
            if shot: shot(label)
    def press(label, sel=None, js=None):
        nonlocal taps
        taps += 1
        if log: log("  tap %d: %s" % (taps, label))
        if sel: pg.click(sel)
        else: pg.evaluate(js)
    # an install page (a phone in a tab) is not part of the sign-up: this walk starts in whatever the app opens on
    see(screen_of(pg) or "start")
    if pg.evaluate("()=>!!document.querySelector('.gs-page')"):
        pg.wait_for_timeout(2400)
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); if(s) s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1000)
        press("Get Started: Let's get started", ".gs-go"); pg.wait_for_timeout(1000)
    see(screen_of(pg))
    press("Welcome: I'm new here", ".welcome-new"); pg.wait_for_timeout(700); see(screen_of(pg))
    press("New to Nova?: I'm new, continue", ".signupcheck-go"); pg.wait_for_timeout(600); see(screen_of(pg))
    press("Class: pick Police Academy", ".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(300)
    press("Class: Continue", ".classselect-panel #nextbtn")
    try:
        pg.wait_for_selector("#classenroll-confirm .classenroll-yes", timeout=4000); pg.wait_for_timeout(400); see("class confirm")
        press("Class confirm: Enroll", "#classenroll-confirm .classenroll-yes")
    except Exception:
        pass
    try: pg.wait_for_selector("#genprofile-overlay", state="attached", timeout=5000)
    except Exception: pass
    see("generating profile")
    pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=30000)
    pg.wait_for_selector("#nova-intro", state="attached", timeout=15000)
    see("nova")
    seen_lines = set(); seen_ask = set(); t1 = time.time(); nova_boxes = 0
    while time.time() - t1 < 300:
        st = novastate(pg)
        if not st:
            if pg.evaluate("()=>!!document.getElementById('savecode-card')"): pg.wait_for_timeout(150); continue
            if time.time() - t1 > 8 or "end" in seen_ask: break
            pg.wait_for_timeout(150); continue
        if st["card"] and "card" not in seen_ask:
            seen_ask.add("card"); see("sync code card"); pg.wait_for_timeout(300)
            press("Code card: tick I've saved it", "#savecode-card .savecode-ack"); pg.wait_for_timeout(150)
            press("Code card: Continue", "#savecode-card .savecode-continue"); pg.wait_for_timeout(500); continue
        if st["asking"] and not st["typing"] and st["name"] and "name" not in seen_ask:
            seen_ask.add("name"); pg.click(".nt-ask-input"); pg.keyboard.type(name)
            press("Nova: send the name", js="()=>{ const e=document.querySelector('.nt-ask-name .nt-ask-go'); if(e) e.click(); }")
            for _ in range(80):
                if not pg.evaluate("()=>!!document.querySelector('#nova-intro .nt-ask-name')"): break
                pg.wait_for_timeout(100)
            continue
        if st["asking"] and not st["typing"] and st["char"] and "char" not in seen_ask:
            seen_ask.add("char")
            press("Nova: pick a partner", ".nt-ask-char .avatarchar-option"); pg.wait_for_timeout(300)
            press("Nova: confirm the partner", ".nt-ask-char .nt-ask-go"); pg.wait_for_timeout(1200); continue
        if st["typing"]:
            pg.evaluate("()=>document.getElementById('nova-intro').__nova.advance()")   # a tap while he types finishes the line (not counted: a person waits)
        elif not st["asking"]:
            if st["i"] not in seen_lines:
                seen_lines.add(st["i"]); nova_boxes += 1; taps += 1
                if log: log("  tap %d: Nova box %d of %d" % (taps, st["i"] + 1, st["count"]))
            if st["i"] == st["count"] - 1:
                seen_ask.add("end"); pg.evaluate("()=>document.querySelector('#nova-intro .nt-go')?.click()")
            else: pg.evaluate("()=>document.getElementById('nova-intro').__nova.advance()")
        pg.wait_for_timeout(120)
    # the tips: the tour, then the last tip (Start Studying) once the page has gone quiet
    tips = 0
    for rnd in range(2):
        up = False
        for _ in range(60 if rnd == 0 else 70):
            if pg.evaluate("()=>!!document.getElementById('tour-tooltip')"): up = True; break
            if nova_boxes and novastate(pg) and "end" in seen_ask: pg.evaluate("()=>document.querySelector('#nova-intro .nt-go')?.click()")
            pg.wait_for_timeout(250)
        if not up: break
        see("tips")
        for _ in range(20):
            if not pg.evaluate("()=>!!document.getElementById('tour-next')"): break
            pg.wait_for_timeout(500)
            press("Tip %d" % (tips + 1), js="()=>document.getElementById('tour-next').click()"); tips += 1
            pg.wait_for_timeout(450)
    see(screen_of(pg))
    info = pg.evaluate("()=>({ onboarded: !!store.onboardingComplete, code: !!syncCode, name: store.firstName || '', avatar: store.avatarChar || '' })")
    return {"taps": taps, "pages": pages, "nova_boxes": nova_boxes, "tips": tips, **info}
