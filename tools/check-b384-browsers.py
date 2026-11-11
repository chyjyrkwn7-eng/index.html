#!/usr/bin/env python3
"""Build 384: Safari in a tab on every device, Internet Explorer, the bookmark icon, a device that keeps its account, and one
shared link for five people.

Shape, read off the page:
  safari  iPhone 17 Pro Max (at 100% and at his 85% page zoom), iPhone 16, iPhone 17, SE and iPad Pro 11 (upright and on its
          side), each two ways:
          TAB  - the page between Safari's bars, as measured off a frame of his own Safari tab (no insets, the viewport
                 short by the status bar and the toolbar's reservation);
          OVER - Safari's bars drawn over a full-screen page (real safe-area insets; the toolbar in none of them): the
                 iOS 26 model - an iPhone's status bar and 83pt of floating toolbar (60 with a Home button), an iPad's
                 74pt top bar.
          On Home, Profile, Stats, Settings, the Leaderboard, Customize, the units, a drill question (answered, Next up), Get
          Started and Welcome: the tab bar ends above the toolbar's top and starts below the top bar; nothing pinned
          (fixed/sticky) and visible starts above the top bar or ends below the toolbar's top; at rest nothing to read or tap
          starts under the top bar; scrolled to the end, the last control ends above the tab bar and the toolbar; Next (pinned,
          or in the page under the answers) ends above the toolbar; Welcome's two buttons end above it with nothing scrolled;
          Get Started's button, at the page's end, too. OVER fails on 91a1d96; TAB passes on both (the measured state needed
          no change - it is there so a change cannot break it).
  ie      An Internet Explorer 11 user agent gets one plain page - "Nova needs a current browser", a button whose address is
          microsoft-edge: + this page, the browsers that work - and none of the app; Chrome, Safari (iPhone and Mac),
          Samsung Internet and Firefox user agents get the app and no such page. The guard is the first script in the
          page and parses as ECMAScript 3 (acorn, ecmaVersion 3, when node and acorn are on this machine). Fails on 91a1d96.
  icons   Every icon the page declares is the app icon: the embedded favicon, the real-file favicons at 16, 32 and 192
          (each linked with its size), the apple-touch-icon file at 180, the manifest's 180/192/512 and its maskable 512,
          share/icon-512.png - the same art as tools/gen-app-icon.py's shipped variant; the theme-color meta agrees with the
          manifest's.
  keep    An account on a device is still there after a reload, after the tab is closed and the bookmark opened in a new
          one, and the store, the code and Home come back; storage.persist() is asked for only once the device holds an
          account (not on a first visit); a device whose site data was cleared lands on Welcome with Sign in on it.
  share   The link the Share button sends is SHARE_URL exactly, with no code, account or device in it; opened in five fresh
          browsers (iPhone Safari, Android Chrome, Samsung Internet, a Windows laptop, an iPad) it reaches the app's first
          run, with no account and nothing from any of the others.
Run:  python3 tools/check-b384-browsers.py [section ...]  [--root DIR]   (--root: a copy of another build, e.g. 91a1d96)"""
import functools, http.server, json, os, re, shutil, socket, subprocess, sys, threading, base64, io
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if "--root" in args:
    i = args.index("--root"); ROOT = os.path.abspath(args[i + 1]); del args[i:i + 2]
want = args or ["safari", "ie", "icons", "keep", "share"]
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

ok = True
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else ("-> " + str(info)[:600]))

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/" % port
srv, BASE = serve()
URL = BASE + "index.html"

UA = {
    "iphone": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1",
    "ipad": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
    "mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
    "chrome-android": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
    "samsung": "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/28.0 Chrome/130.0.0.0 Mobile Safari/537.36",
    "windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
    "firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "ie11": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "ie10": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
}
TOUCH_POINTS = "Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5,configurable:true});"
SEED = json.dumps({"firstName": "Casey", "avatarChar": "ninja", "onboardingComplete": True, "leaderboardOptIn": True,
    "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
    "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "seenHomeTour": True, "seenSettingsTour": True,
    "seenRewardsTour": True, "seenLadderTour": True, "novaMet": 99, "publicId": "pubtest00384",
    "lifetime": {"points": 12400, "answered": 5400, "correct": 4980, "drillPlays": 64, "examPlays": 22, "gamePlays": 9,
                 "perfectTests": 141, "currentStreak": 23, "longestStreak": 57}})
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked',"
        "'class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1');")
INIT = ("(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s);"
        " localStorage.setItem('class26e.synccode','TEST-0384'); %s })()") % (json.dumps(SEED), SEEN)
CLEAR = ("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click());"
         " document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); document.body.classList.remove('cutscene-focus'); }")

def patched(ins):
    v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
    return INSET_RE.sub(lambda m: v[m.group(1)], SRC)

# ---------------------------------------------------------------------------------------------------------- (a) safari
# name, css w, css h, screen (pt), portrait insets (css), zoom, iPad?
DEVICES = [
    ("iPhone 17 Pro Max", 440, 956, (440, 956), (62, 0, 34, 0), 1.0, False),
    ("iPhone 17 Pro Max at 85%", 518, 1125, (440, 956), (73, 0, 40, 0), 0.85, False),
    ("iPhone 16", 393, 852, (393, 852), (59, 0, 34, 0), 1.0, False),
    ("iPhone 17", 402, 874, (402, 874), (62, 0, 34, 0), 1.0, False),
    ("iPhone SE", 375, 667, (375, 667), (20, 0, 0, 0), 1.0, False),
    ("iPad Pro 11", 834, 1194, (834, 1194), (24, 0, 20, 0), 1.0, True),
    ("iPad Pro 11 on its side", 1194, 834, (834, 1194), (24, 0, 20, 0), 1.0, True),
]
def model(dev, kind):
    """-> viewport (w, h), page insets, the bars (top, bottom) in CSS px that the page must keep its controls out of"""
    name, w, h, scr, ins, z, ipad = dev
    pt = lambda v: round(v / z)
    if kind == "tab":
        chrome = pt(74) if ipad else round((ins[0] * z + (97 if ins[2] else 72)) / z)
        return (w, h - chrome), (0, 0, 0, 0), (0, 0)
    if ipad:   # Safari's bar is at the top; at the bottom only the home indicator, which the tab bar may sit over as installed
        return (w, h), ins, (max(ins[0], pt(74)), 0)
    return (w, h), ins, (max(ins[0], pt(20)), max(ins[2], pt(83 if ins[2] else 60)))

SCREENS = [("Home", "showHome()"), ("Profile", "document.getElementById('bottomtab-profile').click()"),
           ("Stats", "showProfile('stats')"), ("Settings", "showProfile('settings')"),
           ("Leaderboard", "showRankings('overall')"), ("Customize", "showCustomize()"),
           ("Units", "cfg.mode='drill'; showSetup()"), ("Question", "__q()"), ("Get Started", "showGetStarted()"), ("Welcome", "showWelcome()")]
QUESTION = """window.__q = function(){ theme.reduceMotion = true; const u = 'Identity Crimes'; cfg.mode = 'drill'; cfg.source = 'all';
  cfg.units = [u]; cfg.size = 0; beginRun(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === u && inWholeUnit(QUESTIONS[i]))); };"""
AUDIT = """([bt, bb])=>{ const vw = innerWidth, vh = innerHeight, out = { over: document.documentElement.classList.contains('safari-bars-over'), hits: [] };
  const shown = e => { let p = e; while(p && p !== document.documentElement){ const s = getComputedStyle(p);
      if(s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false; p = p.parentElement; }
    const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < vh && r.right > 0 && r.left < vw; };
  const pinned = e => { let p = e; while(p && p !== document.body){ const s = getComputedStyle(p); if(s.position === 'fixed' || s.position === 'sticky') return true; p = p.parentElement; } return false; };
  const nm = e => ((e.id ? '#' + e.id : '') + ' ' + String(e.className || e.tagName)).trim().slice(0, 50);
  const tabs = document.querySelector('.bottomtabs');
  if(tabs && shown(tabs)){ const r = tabs.getBoundingClientRect(); out.tabs = [Math.round(r.top), Math.round(r.bottom)];
    if(r.bottom > vh - bb + .5) out.hits.push('the tab bar ends at ' + Math.round(r.bottom) + ', under the toolbar from ' + (vh - bb));
    if(r.top < bt - .5) out.hits.push('the tab bar starts at ' + Math.round(r.top) + ', under the top bar to ' + bt); }
  const live = [...document.querySelectorAll('button, a[href], input, select, textarea, [role=button], h1, h2, .bottomtab')].filter(shown);
  live.forEach(e => { const r = e.getBoundingClientRect(); if(!e.textContent.trim() && !e.matches('input,select,textarea') && !e.querySelector('svg')) return;
    if(r.top < bt - .5) out.hits.push(nm(e) + ' starts at ' + Math.round(r.top) + ', under the top bar to ' + bt);
    if(pinned(e) && r.bottom > vh - bb + .5) out.hits.push('pinned ' + nm(e) + ' ends at ' + Math.round(r.bottom) + ', under the toolbar from ' + (vh - bb)); });
  return out; }"""
END = """([bt, bb])=>{ const vh = innerHeight;
  const shown = e => { let p = e; while(p && p !== document.documentElement){ const s = getComputedStyle(p);
      if(s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false; p = p.parentElement; }
    const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const pinned = e => { let p = e; while(p && p !== document.body){ const s = getComputedStyle(p); if(s.position === 'fixed' || s.position === 'sticky') return true; p = p.parentElement; } return false; };
  const tabs = document.querySelector('.bottomtabs'); let floor = vh - bb;
  if(tabs && shown(tabs)) floor = Math.min(floor, tabs.getBoundingClientRect().top);
  const flow = [...document.querySelectorAll('#stage button, #stage a[href], #stage input, #stage [role=button]')].filter(e => shown(e) && !pinned(e) && e.textContent.trim());
  if(!flow.length) return { n: 0 };
  const last = flow.reduce((a, e) => e.getBoundingClientRect().bottom > a.getBoundingClientRect().bottom ? e : a);
  const r = last.getBoundingClientRect();
  return { n: flow.length, last: String(last.textContent).trim().slice(0, 30), bottom: Math.round(r.bottom), floor: Math.round(floor), clear: r.bottom <= floor + 1.5 }; }"""

def safari(pw):
    br = pw.chromium.launch(executable_path=CHROME)
    for dev in DEVICES:
        for kind in ("tab", "over"):
            (vw, vh), ins, bars = model(dev, kind)
            ctx = br.new_context(viewport={"width": vw, "height": vh}, screen={"width": dev[3][0], "height": dev[3][1]},
                                 user_agent=UA["ipad" if dev[6] else "iphone"], has_touch=True, is_mobile=True, device_scale_factor=2)
            ctx.add_init_script(INIT); ctx.add_init_script(QUESTION)
            if dev[6]: ctx.add_init_script(TOUCH_POINTS)
            pg = ctx.new_page()
            body = patched(ins)
            pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.goto(URL); pg.wait_for_timeout(3000)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")
            pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"); pg.wait_for_timeout(1200)
            for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(150)
            tag = "%s, Safari %s (%dx%d, bars %d/%d)" % (dev[0], "tab" if kind == "tab" else "bars over the page", vw, vh, bars[0], bars[1])
            if kind == "over":
                over = pg.evaluate("document.documentElement.classList.contains('safari-bars-over')")
                chk(tag + ": the app sees Safari's bars over the page", over)
            for sname, call in SCREENS:
                pg.evaluate("()=>{ %s; }" % call); pg.wait_for_timeout(900)
                if sname == "Question":
                    try:
                        pg.wait_for_function("!!document.querySelector('.qpanel .choice')", timeout=8000)
                        pg.wait_for_timeout(500)
                        pg.evaluate("""()=>{ const qi = order[pos]; const r = optionOrder(qi).indexOf(QUESTIONS[qi].answer);
                          const cs = [...document.querySelectorAll('.qpanel .choice')]; (cs[r] || cs[0]).click(); }""")
                        pg.wait_for_timeout(1800)
                    except Exception as e:
                        chk(tag + ": a drill question comes up", False, str(e)[:120]); continue
                pg.evaluate(CLEAR); pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(350)
                a = pg.evaluate(AUDIT, list(bars))
                extra = ""
                if sname == "Question":
                    NX = """()=>{ const n = document.querySelector('.foot > .floatbtn.qnext'); if(!n) return null; const r = n.getBoundingClientRect();
                      const s = getComputedStyle(n); return { b: Math.round(r.bottom), t: Math.round(r.top), pos: s.position, flow: n.classList.contains('qnext-flow'),
                        shown: s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > 0 && r.height > 0 }; }"""
                    nx = pg.evaluate(NX)
                    chk(tag + ": Question - Next is up after an answer", nx and nx["shown"], nx)
                    if nx and nx["shown"]:
                        if nx["pos"] != "fixed":
                            # no room under the answers: Next flows in the page under them - scrolled to, it ends above the toolbar
                            pg.evaluate("scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(1200)
                            nx = pg.evaluate(NX); pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(600)
                        chk(tag + ": Question - Next (%s) ends above the toolbar (%s <= %d)" % ("in the page" if nx["pos"] != "fixed" else "pinned", nx["b"], vh - bars[1]),
                            nx["b"] <= vh - bars[1] + .5, nx)
                    extra = " - tab bar %s" % a.get("tabs")
                chk(tag + ": %s - nothing to read or tap under the bars at rest%s" % (sname, extra or (" (tab bar %s)" % a.get("tabs") if a.get("tabs") else "")), not a["hits"], a["hits"][:5])
                if sname == "Welcome":
                    w = pg.evaluate("""()=>[...document.querySelectorAll('.cosmic-welcome button')].filter(b => b.getBoundingClientRect().height > 0).map(b => [b.textContent.trim(), Math.round(b.getBoundingClientRect().bottom)])""")
                    chk(tag + ": Welcome - Sign in and I'm new here end above the toolbar with nothing scrolled (%s <= %d)" % (w, vh - bars[1]),
                        len(w) >= 2 and all(b <= vh - bars[1] + .5 for _, b in w), w)
                if sname == "Get Started":
                    pg.evaluate("()=>{ const s = document.querySelector('.gs-scroll'); s && s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1600)
                    gsr = pg.evaluate("""()=>{ const b = document.querySelector('.gs-go'); if(!b) return null; const r = b.getBoundingClientRect(); return { b: Math.round(r.bottom), h: Math.round(r.height) }; }""")
                    chk(tag + ": Get Started - its button, up at the page's end, ends above the toolbar (%s <= %d)" % (gsr, vh - bars[1]),
                        gsr and gsr["h"] >= 44 and gsr["b"] <= vh - bars[1] + .5, gsr)
                if sname not in ("Question", "Welcome", "Home"):
                    # (the app scrolls smoothly: let it arrive)
                    pg.evaluate("scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(1200)
                    e = pg.evaluate(END, list(bars))
                    if e.get("n"):
                        chk(tag + ": %s - scrolled to the end, the last control (%r) ends above the bar (%s <= %s)" % (sname, e["last"], e["bottom"], e["floor"]), e["clear"], e)
                    pg.evaluate("scrollTo(0,0)")
            pg.evaluate("()=>{ try{ testInProgress = false; }catch(e){} showHome(); }")
            real = [x for x in errs if not any(k in x for k in ("firebase", "firestore", "gstatic", "Failed to fetch", "net::"))]
            chk(tag + ": no page errors", not real, real[:3])
            ctx.close()
    br.close()

# ---------------------------------------------------------------------------------------------------------- (b) ie
def ie(pw):
    head = SRC.split("<script>", 1)
    first = head[1].split("</script>", 1)[0] if len(head) > 1 else ""
    chk("the Internet Explorer guard is the first script in the page", "INTERNET EXPLORER" in first and "microsoft-edge:" in first, first[:120])
    node = shutil.which("node"); acorn = "/opt/node-tools/node_modules/acorn"
    if node and os.path.isdir(acorn) and first:
        js = ("const a=require(%s); try{ a.parse(%s, {ecmaVersion:3}); console.log('ok'); }catch(e){ console.log('ERR '+e.message); }"
              % (json.dumps(acorn), json.dumps(first)))
        out = subprocess.run([node, "-e", js], capture_output=True, text=True).stdout.strip()
        chk("...and it parses as ECMAScript 3 (acorn ecmaVersion 3)", out == "ok", out)
    else:
        print("NOTE  node/acorn not on this machine: the ES3 parse was not run")
    br = pw.chromium.launch(executable_path=CHROME)
    for key in ("ie11", "ie10"):
        ctx = br.new_context(viewport={"width": 1366, "height": 768}, user_agent=UA[key])
        # (the guard stops the page loading, as IE's execCommand("Stop") does, so there is no load event to wait for)
        pg = ctx.new_page(); pg.goto(URL, wait_until="commit"); pg.wait_for_timeout(2500)
        r = pg.evaluate("""()=>{ const box = document.getElementById('nova-old-browser'), a = document.getElementById('nova-open-edge');
          return { box: !!box, h1: box ? (box.querySelector('h1') || {}).textContent : '', text: box ? box.textContent : '', href: a ? a.getAttribute('href') : '',
            app: !!document.getElementById('stage') || !!document.querySelector('.wrap'), splash: !!document.getElementById('splashscreen'),
            shownBox: box ? box.getBoundingClientRect().height > 50 : false, title: document.title }; }""")
        chk("%s: one plain page - 'Nova needs a current browser'" % key.upper(), r["box"] and r["shownBox"] and "current browser" in (r["h1"] or ""), r)
        chk("%s: its button opens this address in Microsoft Edge (%s)" % (key.upper(), r["href"][:60]), r["href"] == "microsoft-edge:" + URL, r["href"])
        chk("%s: and names the browsers that work, with no name of anybody's in it" % key.upper(),
            all(b in r["text"] for b in ("Chrome", "Edge", "Safari", "Firefox")) and "Madison" not in r["text"] and "Davis" not in r["text"], r["text"][:200])
        chk("%s: none of the app is there (no #stage, no .wrap, no splash)" % key.upper(), not r["app"] and not r["splash"], r)
        ctx.close()
    for key in ("windows", "edge", "firefox", "mac", "iphone", "samsung", "chrome-android"):
        mobile = key in ("iphone", "samsung", "chrome-android")
        ctx = br.new_context(viewport={"width": 430 if mobile else 1366, "height": 900 if mobile else 768}, user_agent=UA[key], has_touch=mobile, is_mobile=mobile)
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.goto(URL); pg.wait_for_timeout(3000)
        r = pg.evaluate("()=>({ box: !!document.getElementById('nova-old-browser'), flag: !!window.NOVA_OLD_BROWSER, stage: !!document.getElementById('stage'), wrap: !!document.querySelector('.wrap'), screens: document.querySelectorAll('#stage > *').length })")
        real = [x for x in errs if not any(k in x for k in ("firebase", "firestore", "gstatic", "Failed to fetch", "net::"))]
        chk("%s: the app, untouched by the guard (stage up, %d screen nodes, no IE page, no page errors)" % (key, r["screens"]),
            not r["box"] and not r["flag"] and r["stage"] and r["wrap"] and r["screens"] > 0 and not real, [r, real[:2]])
        ctx.close()
    br.close()

# ---------------------------------------------------------------------------------------------------------- (c) icons
def icons(pw):
    from PIL import Image
    def img_of(href):
        if href.startswith("data:"):
            return Image.open(io.BytesIO(base64.b64decode(href.split(",", 1)[1]))).convert("RGB")
        path = href.split("?")[0]
        path = path.replace("https://chyjyrkwn7-eng.github.io/index.html/", "")
        return Image.open(os.path.join(ROOT, path)).convert("RGB")
    def diff(a, b):
        k = min(64, a.size[0], b.size[0])
        a = a.resize((k, k), Image.LANCZOS); b = b.resize((k, k), Image.LANCZOS)
        pa = list(a.getdata()); pb = list(b.getdata())
        return sum(abs(x - y) for p, q in zip(pa, pb) for x, y in zip(p, q)) / (k * k * 3)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("genicon", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen-app-icon.py"))
    gi = importlib.util.module_from_spec(spec); spec.loader.exec_module(gi)
    shipped = getattr(gi, "SHIPPED_VARIANT", "pixel")
    ref = gi.render(shipped, 512).convert("RGB")
    links = re.findall(r'<link rel="(icon|apple-touch-icon)"([^>]*?)href="([^"]+)"', SRC)
    sizes = {}
    for rel, attrs, href in links:
        m = re.search(r'sizes="(\d+)x\d+"', attrs)
        sizes.setdefault(rel, []).append(int(m.group(1)) if m else None)
        im = img_of(href)
        d = diff(ref, im)
        chk("%s %s (%dx%d) is the app icon (%s art, mean difference %.1f)" % (rel, ("sizes=%s" % m.group(1)) if m else "(no sizes, embedded)", im.size[0], im.size[1], shipped, d), d <= 3, d)
    chk("favicons for tabs and bookmarks at 16 and 32, and 192 for Android tiles, each linked with its size", all(s in sizes.get("icon", []) for s in (16, 32, 192)), sizes)
    chk("the apple-touch-icon is a real 180 file (Safari's bookmarks, Favorites and Home Screen)", 180 in sizes.get("apple-touch-icon", []), sizes)
    m = re.search(r'href="data:application/manifest\+json;base64,([^"]+)"', SRC)
    man = json.loads(base64.b64decode(m.group(1)))
    got = []
    for i in man.get("icons", []):
        im = Image.open(io.BytesIO(base64.b64decode(i["src"].split(",", 1)[1]))).convert("RGB")
        got.append((i["sizes"], i.get("purpose", "any"), round(diff(ref, im), 1)))
    chk("the manifest's icons are the app icon at 192 and 512, and a maskable 512 (%s)" % got,
        all(d <= 3 for _, _, d in got) and any(s == "192x192" for s, _, _ in got) and any(s == "512x512" and p == "maskable" for s, p, _ in got), got)
    s512 = os.path.join(ROOT, "share", "icon-512.png")
    chk("share/icon-512.png (the share page's icon) is the app icon", os.path.exists(s512) and diff(ref, Image.open(s512).convert("RGB")) <= 3)
    meta = re.search(r'<meta name="theme-color" id="themecolor" content="(#[0-9A-Fa-f]{6})"', SRC)
    chk("theme-color: the meta tag and the manifest agree (%s / %s)" % (meta and meta.group(1), man.get("theme_color")), meta and meta.group(1).lower() == str(man.get("theme_color")).lower())
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen-app-icon.py"), "--check"], capture_output=True, text=True, cwd=ROOT)
    chk("tools/gen-app-icon.py --check: %s" % (r.stdout.strip() or r.stderr.strip())[:120], r.returncode == 0)

# ---------------------------------------------------------------------------------------------------------- (d) keep
PERSIST_SPY = """(()=>{ window.__persist = []; try{ const st = navigator.storage; if(st){ const orig = st.persist ? st.persist.bind(st) : null;
  st.persist = function(){ let code = null; try{ code = localStorage.getItem('class26e.synccode'); }catch(e){}
    window.__persist.push({ code: !!code, at: Date.now() }); return orig ? orig() : Promise.resolve(false); }; } }catch(e){} })()"""
STATE = """()=>({ code: localStorage.getItem('class26e.synccode'), name: (JSON.parse(localStorage.getItem('class26e.drill.v1') || '{}')).firstName,
  points: ((JSON.parse(localStorage.getItem('class26e.drill.v1') || '{}')).lifetime || {}).points, home: !!document.querySelector('#stage [data-screen="home"]'),
  welcome: !!document.querySelector('.cosmic-welcome'), gs: !!document.querySelector('.gs-page'), persist: window.__persist || [] })"""
def keep(pw):
    br = pw.chromium.launch(executable_path=CHROME)
    # a first visit: no account, so no persist() question
    ctx = br.new_context(viewport={"width": 430, "height": 900}, user_agent=UA["firefox"])
    ctx.add_init_script(PERSIST_SPY)
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(3500)
    s = pg.evaluate(STATE)
    chk("a first visit (no account on the device) does not ask for persistent storage", s["code"] is None and not s["persist"], s)
    ctx.close()
    # an account on the device: kept over a reload, a closed tab and the bookmark opened again
    ctx = br.new_context(viewport={"width": 430, "height": 900}, user_agent=UA["iphone"], has_touch=True, is_mobile=True)
    ctx.add_init_script(INIT); ctx.add_init_script(PERSIST_SPY)
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(3500)
    s0 = pg.evaluate(STATE)
    chk("an account on the device: its store and code are there, Home is up", s0["code"] == "TEST-0384" and s0["name"] == "Casey" and s0["home"], s0)
    chk("...and storage.persist() is asked for, with the account already on the device", any(p["code"] for p in s0["persist"]) and all(p["code"] for p in s0["persist"]), s0["persist"])
    pg.evaluate("()=>{ store.lifetime.points += 5; saveStore(); }"); pg.wait_for_timeout(400)
    pg.reload(); pg.wait_for_timeout(3500)
    s1 = pg.evaluate(STATE)
    chk("a refresh keeps it (code, name, the points just earned, Home)", s1["code"] == "TEST-0384" and s1["name"] == "Casey" and s1["points"] == s0["points"] + 5 and s1["home"], s1)
    pg.close()
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(3500)   # the tab closed; the bookmark opened in a new one
    s2 = pg.evaluate(STATE)
    chk("the tab closed and the bookmark opened in a new one: still signed in, the same points", s2["code"] == "TEST-0384" and s2["points"] == s0["points"] + 5 and s2["home"], s2)
    idb = pg.evaluate("""async ()=>{ const names = indexedDB.databases ? (await indexedDB.databases()).map(d => d.name) : []; return names; }""")
    chk("the IndexedDB mirror is there too (%s)" % idb, "class26e-drill-backup" in idb, idb)
    keys = pg.evaluate("()=>Object.keys(localStorage).filter(k => /^class26e\\.(drill\\.v1|synccode)$/.test(k)).sort()")
    chk("the keys are the ones every device has always used (class26e.drill.v1, class26e.synccode)", keys == ["class26e.drill.v1", "class26e.synccode"], keys)
    # site data cleared (what "clear cookies and website data" does): the device has nothing; Sign in is the way back
    ctx.clear_cookies()
    pg.evaluate("async ()=>{ localStorage.clear(); sessionStorage.clear(); try{ indexedDB.deleteDatabase('class26e-drill-backup'); }catch(e){} }")
    pg.close()
    ctx2 = br.new_context(viewport={"width": 430, "height": 900}, user_agent=UA["iphone"], has_touch=True, is_mobile=True)
    ctx2.add_init_script("try{ localStorage.setItem('class26e.getstarted','1'); localStorage.setItem('class26e.hadaccount','1'); }catch(e){}")
    pg = ctx2.new_page(); pg.goto(URL); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    # (384, merged with Get Started for every device with no account) the device opens on Get Started; its Sign in is on
    # screen from the first frame, and one tap reaches the code entry
    gsr = pg.evaluate("""()=>{ const s=document.querySelector('.gs-page .gs-signin'); if(!s) return null; const r=s.getBoundingClientRect();
      return { h: Math.round(r.height), w: Math.round(r.width), onScreen: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth }; }""")
    if gsr is not None:
        chk("site data cleared: Get Started's Sign in is on screen from the start, 44px+ (%s)" % gsr, gsr["h"] >= 44 and gsr["w"] >= 44 and gsr["onScreen"], gsr)
        pg.click(".gs-page .gs-signin"); pg.wait_for_timeout(900)
        ent = pg.evaluate("()=>({ entry: !!document.querySelector('.synccode-entry-panel input'), gs: !!document.querySelector('.gs-page') })")
        chk("site data cleared: ...one tap reaches the sync code entry (%s)" % ent, ent["entry"] and not ent["gs"], ent)
        pg.evaluate("()=>showWelcome()"); pg.wait_for_timeout(900)
    r = pg.evaluate("""()=>{ const s = [...document.querySelectorAll('button')].find(b => /^Sign in$/.test(b.textContent.trim())); const r = s ? s.getBoundingClientRect() : null;
      return { code: localStorage.getItem('class26e.synccode'), signin: !!s, h: r ? Math.round(r.height) : 0, onScreen: r ? r.top >= 0 && r.bottom <= innerHeight : false,
               cap: (document.querySelector('.welcome-signin-cap') || {}).textContent || '' }; }""")
    chk("site data cleared: no account on the device, and Welcome's Sign in is on screen, 44px+ (%r)" % r["cap"], r["code"] is None and r["signin"] and r["h"] >= 44 and r["onScreen"], r)
    ctx2.close(); ctx.close(); br.close()

# ---------------------------------------------------------------------------------------------------------- (e) share
def share(pw):
    m = re.search(r'const SHARE_URL = "([^"]+)";', SRC)
    chk("SHARE_URL is one fixed address (%s)" % (m and m.group(1)), m and re.match(r"^https://chyjyrkwn7-eng\.github\.io/index\.html/share/(\?v=\d+)?$", m.group(1)))
    page = open(os.path.join(ROOT, "share", "index.html"), encoding="utf-8").read()
    chk("the share page carries nothing per person (no code, no k=, no name, no storage read)",
        not re.search(r"[#?&]k=|synccode|localStorage|sessionStorage|Madison", page))
    br = pw.chromium.launch(executable_path=CHROME)
    # the Share button hands over SHARE_URL itself
    ctx = br.new_context(viewport={"width": 430, "height": 900}, user_agent=UA["iphone"], has_touch=True, is_mobile=True)
    ctx.add_init_script(INIT)
    ctx.add_init_script("window.__shared = []; navigator.share = function(d){ window.__shared.push(d); return Promise.resolve(); };")
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} showProfile('settings'); }"); pg.wait_for_timeout(900)
    pg.evaluate("()=>{ const r = document.getElementById('settings-row-share'); r ? r.click() : showAppearance({ page: 'share' }); }"); pg.wait_for_timeout(900)
    pg.evaluate("()=>{ const b = [...document.querySelectorAll('#stage button')].find(x => /Share this app/.test(x.textContent)); b && b.click(); }")
    pg.wait_for_timeout(1200)
    sh = pg.evaluate("window.__shared")
    url = sh[0]["url"] if sh else None
    chk("Settings' Share sends SHARE_URL exactly, with no code or account in it (%s)" % url, url == (m and m.group(1)) and "TEST-0384" not in json.dumps(sh) and "pubtest" not in json.dumps(sh), sh)
    ctx.close()
    # five people, five devices, the same link (served here: share/ forwards to ../, the app)
    people = [("iPhone Safari", UA["iphone"], (440, 956), True), ("Android Chrome", UA["chrome-android"], (412, 915), True),
              ("Samsung Internet", UA["samsung"], (384, 832), True), ("Windows laptop", UA["windows"], (1366, 768), False),
              ("iPad Safari", UA["ipad"], (820, 1180), True)]
    link = BASE + "share/" + ("?" + m.group(1).split("?", 1)[1] if m and "?" in m.group(1) else "")
    seen = []
    for who, ua, (w, h), touch in people:
        ctx = br.new_context(viewport={"width": w, "height": h}, user_agent=ua, has_touch=touch, is_mobile=touch)
        pg = ctx.new_page(); pg.goto(link); pg.wait_for_timeout(4500)
        r = pg.evaluate("""()=>({ url: location.href, code: localStorage.getItem('class26e.synccode'), store: localStorage.getItem('class26e.drill.v1'),
          gs: !!document.querySelector('.gs-page'), welcome: !!document.querySelector('.cosmic-welcome'), home: !!document.querySelector('#stage [data-screen="home"]'),
          stage: !!document.getElementById('stage'), inst: !!document.querySelector('[data-screen="installfirst"]') })""")
        # 384.23: a phone or tablet in a tab with no account is first held on the install page (check-b384-installfirst.py); a computer is not
        first = (r["gs"] or r["welcome"] or (touch and r["inst"])) and not r["home"] and (touch or not r["inst"])
        chk("%s opens the shared link: it reaches the app (%s) at its first run, with no account" % (who, r["url"].replace(BASE, "/")),
            r["stage"] and "/share/" not in r["url"] and first and not r["code"], r)
        pid = pg.evaluate("()=>{ try{ return (JSON.parse(localStorage.getItem('class26e.drill.v1') || '{}')).publicId || null; }catch(e){ return null; } }")
        seen.append(pid)
        ctx.close()
    chk("nothing from one person's browser reaches another's: all five start with no account id of their own or anybody's (%s)" % seen,
        len(seen) == 5 and not any(seen), seen)
    br.close()
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen-share-card.py"), "--check"], capture_output=True, text=True, cwd=ROOT)
    chk("tools/gen-share-card.py --check: %s" % r.stdout.strip()[:120], r.returncode == 0, r.stdout + r.stderr)

with sync_playwright() as pw:
    for sec in want:
        print("== " + sec)
        {"safari": safari, "ie": ie, "icons": icons, "keep": keep, "share": share}[sec](pw)
srv.shutdown()
print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
