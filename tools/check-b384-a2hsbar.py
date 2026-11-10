"""Build 384 r19: the Home Screen reminder bar, and the walkthrough that it opens (showHomeScreenSheet).
Madison: "maybe you can put out reminders for people who are on Safari without it as a home app? And it won't go away on the
screen till they hit the X button or something?" A page cannot add itself to the Home Screen, so the app keeps a slim glass bar
at the top of Home, for anybody using Nova in a browser tab on a phone or tablet, until they end it.
Read off the page, an existing account (signed up, has answered questions, the Home Screen walkthrough already shown once):
(1) WHERE IT SHOWS: an iPhone Safari tab, an iPad (desktop-class user agent, touch), an Android Chrome tab - yes; a Windows
    laptop, a Mac laptop, the installed app (iPhone and Android) - no, however long it is waited for; and not for an account
    whose walkthrough is still owed (a sign-up under way), nor while the one-time "Quick tip" sheet is still to come - it
    follows the tip once the tip has gone;
(2) WHAT IT IS: one plain line, an Add pill and an X, no owner's name; the X a 44px+ target; the bar one tap from the
    walkthrough; position:fixed (it holds no space), inside the screen, centred, clear of the safe area;
(3) IT STAYS: still there after a reload, on returning to Home from another screen; gone on every other screen at once;
(4) THE X ENDS IT FOR GOOD: class26e.a2hs.bar holds x and a time, the bar is gone, the planet system is back, and it does not
    return after a reload or a new day (the clock moved two days on);
(5) TAPPING IT opens the walkthrough (data-from bar): steps with the buttons' names in bold, three short lines of what the
    person gains, "I've added it" and "Not now" 44px+ side by side; Not now closes it and the bar STAYS (and after a reload);
    I've added it ends the bar for good (class26e.a2hs.bar holds d and a time) and does not return;
(6) THE UPDATE AND RE-ADD NOTICES COME FIRST: while one is up the bar is not (never two at once, no box overlap), and the bar
    comes back when it goes; a banner that arrives after the bar parks below it;
(7) NOTHING OF HOME IS COVERED OR BLOCKED: the bar's box meets none of the chat button, the planet system and its flares,
    the greeting, Start Studying, the daily question button, the tab bar; a tap at each of their centres lands on it, not on the bar;
(8) NO SHIFT ON ARRIVAL: no layout-shift entry (PerformanceObserver) from the moment it shows; the planet moves by `translate`;
(9) NEVER over a test, a tour, a cutscene or the splash (hidden while one is up, back after);
(12) A PHONE ON ITS SIDE has no room for it (Home's planet system is a few dozen pixels tall there): the bar waits for it to be turned upright; a tablet on its side has it;
(10) AT 85% PAGE ZOOM (518 CSS px across a 440pt screen, html.page-zoomed, --zc) it is the size it is at 100% on the glass:
    its height and its X in points, and its words not smaller;
(11) the key is class26e.a2hs.bar, in localStorage only (nothing of it on the account's store); no page errors.
Run:  python3 tools/check-b384-a2hsbar.py   (--against OLD/index.html must FAIL)
      ONLY=where,stay python3 tools/check-b384-a2hsbar.py      A2B_SHOTS=/some/folder  (a picture of each)"""
import os, sys, json, re, time
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-a2hs.py")).read(); _src = _src[:_src.index("\nwith sync_playwright() as pw:")]
G = {"__file__": os.path.join(HERE, "check-b384-a2hs.py"), "__name__": "b384bar"}
exec(_src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("  PASS " if cond else "  FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
def want(sec): return not ONLY or sec in ONLY
SHOTS = os.environ.get("A2B_SHOTS")
BUILD = G["BUILD"]; SRC = G["SRC"]; URL = G["URL"]; INSET_RE = G["INSET_RE"]
CODE = "TEST-3842"
SEEN = ("['class26e.freshstart','class26e.unithold.tip','class26e.getstarted','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.intro.seen','99'); localStorage.setItem('class26e.frame.ok','go-live-1');")
def acct(answered=300):
    return {"firstName": "Gate Tester", "avatarChar": "ghost", "onboardingComplete": True, "publicId": "gatetest3842", "leaderboardOptIn": False,
            "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
            "seenMainMenuTour": True, "seenClassTip": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True, "seenRankingsTour": True,
            "seenAppearanceTour": True, "lifetime": {"points": 1200 if answered else 0, "answered": answered, "correct": int(answered * .8)}}
def init(a2hs="yesterday", answered=300):
    """an existing account. a2hs: the one-time walkthrough's key ('yesterday' = shown a day ago, 'owed', '' = never shown)"""
    extra = {"yesterday": "localStorage.setItem('class26e.a2hs', String(Date.now() - 864e5));",
             "owed": "localStorage.setItem('class26e.a2hs', 'owed');", "": ""}[a2hs]
    return SEEN + "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(acct(answered))) + \
        "localStorage.setItem('class26e.synccode','%s');" % CODE + extra

UA = {
    "iphone": G["UA"]["iphone"],
    "ipad": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
    "android": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "windows": G["UA"]["desktop"],
    "mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
}
# name: (w, h, insets, ua, touch points, screen (w,h) or None)
DEV = {"iphone": (440, 956, (62, 0, 34, 0), "iphone", 5, None), "se": (375, 667, (20, 0, 0, 0), "iphone", 5, None),
       "ipad": (834, 1194, (24, 0, 20, 0), "ipad", 5, None), "android": (360, 800, (24, 0, 0, 0), "android", 5, None),
       "zoom": (518, 1125, (62, 0, 34, 0), "iphone", 5, (440, 956)),
       "se-land": (667, 375, (0, 44, 21, 44), "iphone", 5, None), "promax-land": (956, 440, (0, 62, 21, 62), "iphone", 5, None),
       "ipad-land": (1194, 834, (24, 0, 20, 0), "ipad", 5, None), "android-land": (800, 360, (0, 32, 0, 32), "android", 5, None),
       "windows": (1536, 864, (0, 0, 0, 0), "windows", 0, None), "mac": (1440, 900, (0, 0, 0, 0), "mac", 0, None)}
PERF = """(()=>{ window.__ls = []; try{ new PerformanceObserver(l => { for(const e of l.getEntries()) window.__ls.push({ t: e.startTime, v: e.value,
   src: (e.sources || []).map(s => s.node ? (s.node.id || s.node.className || s.node.nodeName) : '') }); }).observe({ type: 'layout-shift', buffered: true }); }catch(e){}
  const go = () => new MutationObserver(ms => { for(const m of ms){ const t = m.target;
      if(t && t.id === 'a2hsbar' && t.classList.contains('show') && !window.__barShowAt) window.__barShowAt = performance.now(); } })
      .observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'], childList: true });
  if(document.body) go(); else document.addEventListener('DOMContentLoaded', go); })()"""

def open2(br, dev, installed=False, init_js=None, seed=None, wait=3000, version=None, ctx=None, days=0):
    w, h, ins, uak, tp, scr = DEV[dev]
    if ctx is None:
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, has_touch=tp > 0, is_mobile=tp > 0, user_agent=UA[uak])
        ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed or {"progress": {CODE: acct()}}))
        ctx.add_init_script(G["FAKE"]); ctx.add_init_script(PERF)
        ctx.add_init_script("Object.defineProperty(navigator,'maxTouchPoints',{get:()=>%d,configurable:true});" % tp)
        if scr: ctx.add_init_script("Object.defineProperty(screen,'width',{get:()=>%d});Object.defineProperty(screen,'height',{get:()=>%d});" % scr)
        if installed: ctx.add_init_script(G["STANDALONE"])
        if init_js is None: init_js = init()
        if init_js:
            ctx.add_init_script("(()=>{ try{ if(location.protocol !== 'http:' || sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + init_js + " }catch(e){} })()")
    if days:
        ctx.add_init_script("(()=>{ const n = Date.now.bind(Date); const off = %d * 864e5; Date.now = () => n() + off;"
                            " const D = Date; window.Date = class extends D { constructor(...a){ if(a.length) super(...a); else super(D.now() + off); } static now(){ return n() + off; } }; })()" % days)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:240]))
    pg.on("console", lambda m: errs.append("console: " + m.text[:240]) if m.type == "error" and "Failed to load resource" not in m.text and "net::" not in m.text else None)
    b = INSET_RE.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], SRC)
    pg.route("**/index.html*", lambda r, q, b=b: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    ver = version or {"build": BUILD, "force": False, "frameId": ""}
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps(ver)))
    pg.goto(URL); pg.wait_for_timeout(wait)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.errs = errs; pg.dev = dev; pg.ctx = ctx
    return ctx, pg

def relaunch(pg, wait=3000):
    pg.goto("about:blank"); pg.wait_for_timeout(200)
    pg.goto(URL); pg.wait_for_timeout(wait)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")

BAR_UP = "()=>{ const b=document.getElementById('a2hsbar'); return !!b && b.classList.contains('show') && !b.classList.contains('is-leaving'); }"
def wait_bar(pg, secs=30):
    for _ in range(int(secs * 4)):
        if pg.evaluate(BAR_UP): return True
        pg.wait_for_timeout(250)
    return False
def never_bar(pg, secs):
    """true if the bar never comes up in secs"""
    for _ in range(int(secs * 4)):
        if pg.evaluate("()=>!!document.getElementById('a2hsbar')"): return False
        pg.wait_for_timeout(250)
    return True
def gone_bar(pg, secs=4):
    for _ in range(int(secs * 4)):
        if not pg.evaluate("()=>!!document.getElementById('a2hsbar')"): return True
        pg.wait_for_timeout(250)
    return False
def on_home(pg):
    for _ in range(60):
        if G["screen"](pg) == "home": return True
        pg.wait_for_timeout(250)
    return False
def bar_key(pg): return pg.evaluate("()=>localStorage.getItem('class26e.a2hs.bar')")
def shot(pg, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, "%s-%s.png" % (pg.dev, name)))

BAR = """()=>{ const b=document.getElementById('a2hsbar'); if(!b) return null; const r=b.getBoundingClientRect(), cs=getComputedStyle(b);
  const x=b.querySelector('.a2hs-bar-x'), m=b.querySelector('.a2hs-bar-main'), xr=x.getBoundingClientRect(), mr=m.getBoundingClientRect();
  const tx=b.querySelector('.a2hs-bar-text'), de=document.documentElement;
  const zc=parseFloat(getComputedStyle(de).getPropertyValue('--zc'))||1, k=innerWidth/Math.max(1,Math.min(screen.width, screen.height) > 0 ? (innerWidth>innerHeight?Math.max(screen.width,screen.height):Math.min(screen.width,screen.height)) : innerWidth);
  return { rect:[r.left,r.top,r.right,r.bottom], w:r.width, h:r.height, pos:cs.position, text:(tx||{}).textContent||'', all:b.innerText, fs:parseFloat(getComputedStyle(tx).fontSize),
    x:[xr.width,xr.height], main:[mr.width,mr.height], hasPill:!!b.querySelector('.a2hs-bar-pill'), zc, k, page:de.classList.contains('page-zoomed'),
    mid:Math.abs((r.left+r.right)/2-innerWidth/2), insideX:r.left>=0&&r.right<=innerWidth, sideways:de.scrollWidth-de.clientWidth,
    topOk:r.top>=0, owner:/madison/i.test(b.innerText), role:b.getAttribute('role'), hidden:b.closest('[hidden]')!==null,
    xLabel:x.getAttribute('aria-label')||'', mainLabel:m.getAttribute('aria-label')||'' }; }"""
errs_all = []

def new_phone(br, dev="iphone", **kw):
    ctx, pg = open2(br, dev, **kw)
    return ctx, pg

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"], args=["--autoplay-policy=no-user-gesture-required"])

    # ---------------------------------------------------------------- (1) where it shows
    if want("where"):
        print("\n(1) where it shows")
        res = {}
        for dev in ("iphone", "ipad", "android"):
            ctx, pg = open2(br, dev)
            h = on_home(pg); up = wait_bar(pg, 30); info = pg.evaluate(BAR) if up else None
            res[dev] = (h, up)
            if dev == "iphone" and info:
                chk("(2) iphone the bar is one plain line, an Add pill and an X; fixed, centred, inside the screen, no owner's name: '%s'" % info["text"],
                    bool(re.search(r"home screen", info["text"], re.I)) and info["hasPill"] and info["pos"] == "fixed" and info["mid"] < 2 and info["insideX"]
                    and info["sideways"] <= 0 and info["topOk"] and not info["owner"] and info["role"] == "region" and 20 < len(info["text"]) < 70, info)
                chk("(2) iphone the X is a 44px+ target (%dx%d) and the bar's body is one 44px+ button (%dx%d); both named for a screen reader"
                    % (info["x"][0], info["x"][1], info["main"][0], info["main"][1]),
                    info["x"][0] >= 43.5 and info["x"][1] >= 43.5 and info["main"][1] >= 43.5 and info["main"][0] > 150 and info["xLabel"] and info["mainLabel"], info)
                chk("(2) iphone the bar is slim (%dpx) and its words are 14px+ (%s)" % (info["h"], info["fs"]), 44 <= info["h"] <= 72 and info["fs"] >= 13.9, info)
                shot(pg, "bar")
            errs_all.extend(pg.errs); ctx.close()
        chk("(1) shows in an iPhone Safari tab, an iPad (desktop-class UA + touch) and an Android Chrome tab (%s)" % res, all(v[0] and v[1] for v in res.values()), res)
        neg = {}
        for label, dev, kw in (("windows laptop", "windows", {}), ("mac laptop", "mac", {}), ("installed iPhone", "iphone", {"installed": True}),
                               ("installed Android", "android", {"installed": True}), ("walkthrough owed (sign-up under way)", "iphone", {"init_js": init("owed")})):
            ctx, pg = open2(br, dev, **kw)
            h = on_home(pg); n = never_bar(pg, 9); neg[label] = (h, n)
            errs_all.extend(pg.errs); ctx.close()
        chk("(1) never on a computer, in the installed app, or while a sign-up's walkthrough is still owed, however long it waits (%s)" % neg,
            all(v[0] and v[1] for v in neg.values()), neg)
        # the one-time Quick tip first; the bar after it
        ctx, pg = open2(br, "iphone", init_js=init(""))
        on_home(pg)
        sheet = False; barWith = False
        for _ in range(100):
            sh = pg.evaluate("()=>!!document.getElementById('a2hs-sheet')")
            if pg.evaluate("()=>!!document.getElementById('a2hsbar')"): barWith = barWith or sh
            if sh: sheet = True; break
            pg.wait_for_timeout(250)
        early = pg.evaluate("()=>!!document.getElementById('a2hsbar')")
        if sheet: pg.wait_for_timeout(1200); pg.evaluate("()=>document.querySelector('#a2hs-sheet .a2hs-close').click()")
        after = wait_bar(pg, 30) if sheet else False
        chk("(1) an existing account's first Home: the Quick tip comes, with no bar before or under it; the bar follows once it is closed (%s)" % [sheet, early, barWith, after],
            sheet and not early and not barWith and after, [sheet, early, barWith, after])
        errs_all.extend(pg.errs); ctx.close()

    # ---------------------------------------------------------------- (3)(4) it stays; the X ends it
    if want("stay"):
        print("\n(3)(4) it stays, and the X ends it")
        ctx, pg = open2(br, "iphone")
        on_home(pg); up = wait_bar(pg, 30)
        chk("(3) iPhone: the bar is up on Home with nothing stored yet (%s)" % bar_key(pg), up and bar_key(pg) is None, [up, bar_key(pg)])
        relaunch(pg); on_home(pg); again = wait_bar(pg, 30)
        chk("(3) it is still there after a reload (the next launch)", again, again)
        pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(300)
        away = pg.evaluate("()=>!document.getElementById('a2hsbar')")
        chk("(3) on another screen (Profile) it is not there, at once", away and G["screen"](pg) != "home", [away, G["screen"](pg)])
        pg.evaluate("()=>showHome()"); back = wait_bar(pg, 20)
        chk("(3) back on Home it is there again", back, back)
        pg.evaluate("()=>document.querySelector('#a2hsbar .a2hs-bar-x').click()"); pg.wait_for_timeout(700)
        key = bar_key(pg); gone = gone_bar(pg)
        push = pg.evaluate("()=>{ const h=document.querySelector('.cosmic-hero-wrap'); return h ? h.style.getPropertyValue('--notice-push') : null; }")
        chk("(4) the X: the bar is gone, class26e.a2hs.bar is x and a time (%s), the planet system is back (push %s)" % (key, push),
            gone and bool(re.fullmatch(r"x\d+", key or "")) and push in ("0px", "", None), [gone, key, push])
        chk("(11) the key is in localStorage and not on the account's store", pg.evaluate("()=>!JSON.stringify(store).includes('a2hs')"), "")
        relaunch(pg, 3500); on_home(pg); n1 = never_bar(pg, 10)
        chk("(4) after a reload it does not come back", n1, n1)
        ctx2, pg2 = open2(br, "iphone", ctx=ctx, days=2)
        on_home(pg2); n2 = never_bar(pg2, 10)
        chk("(4) two days later (the clock moved on) it does not come back (%s)" % bar_key(pg2), n2 and re.fullmatch(r"x\d+", bar_key(pg2) or ""), [n2, bar_key(pg2)])
        errs_all.extend(pg.errs + pg2.errs); ctx.close()

    # ---------------------------------------------------------------- (5) tapping it: the walkthrough
    if want("sheet"):
        print("\n(5) the bar opens the walkthrough")
        ctx, pg = open2(br, "iphone")
        on_home(pg); wait_bar(pg, 30)
        pg.click("#a2hsbar .a2hs-bar-main"); pg.wait_for_timeout(1200)
        S = pg.evaluate("""()=>{ const o=document.getElementById('a2hs-sheet'); if(!o) return null; const vis=e=>{ const r=e.getBoundingClientRect(); return r.width>0&&r.height>0&&!e.closest('[hidden]'); };
          const foot=[...o.querySelectorAll('.a2hs-foot button')].filter(vis).map(b=>({ cls:b.className, t:b.textContent.trim(), w:b.getBoundingClientRect().width, h:b.getBoundingClientRect().height, top:Math.round(b.getBoundingClientRect().top) }));
          const steps=[...o.querySelectorAll('.a2hs-apple .a2hs-step')];
          return { from:o.dataset.from, tag:(o.querySelector('.a2hs-tag')||{}).textContent, foot, dev:o.dataset.dev,
            gains:[...o.querySelectorAll('.a2hs-gain')].map(g=>g.textContent.trim()), gainsShown:!!o.querySelector('.a2hs-gains') && vis(o.querySelector('.a2hs-gains')),
            bold:steps.map(s=>[...s.querySelectorAll('.a2hs-step-main strong')].map(b=>b.textContent)), n:steps.length,
            ios26:/toolbar/i.test(o.querySelector('.a2hs-apple').textContent) && /View More/.test(o.querySelector('.a2hs-apple').textContent) && /Open as Web App/.test(o.querySelector('.a2hs-apple').textContent),
            owner:/madison/i.test(o.innerText) }; }""")
        chk("(5) tapping the bar opens the walkthrough (from the bar), iPhone picked, headed Home Screen (%s)" % (S and [S["from"], S["tag"], S["dev"]]),
            bool(S) and S["from"] == "bar" and S["dev"] == "apple" and re.fullmatch(r"\s*home screen\s*", S["tag"] or "", re.I), S)
        if S:
            chk("(5) the foot has two answers side by side, 44px+: I've added it, and Not now (%s)" % S["foot"],
                len(S["foot"]) == 2 and re.search(r"added", S["foot"][0]["t"], re.I) and re.fullmatch(r"Not now", S["foot"][1]["t"]) and "a2hs-close" in S["foot"][1]["cls"]
                and all(f["w"] >= 43.5 and f["h"] >= 43.5 for f in S["foot"]) and S["foot"][0]["top"] == S["foot"][1]["top"], S["foot"])
            chk("(5) what the person gains: three short lines; every step names its button in bold (%s); the iOS 26 variants are there (toolbar Share, View More, Open as Web App)" % S["bold"],
                len(S["gains"]) == 3 and all(len(g) < 60 for g in S["gains"]) and S["n"] == 6 and all(len(b) >= 1 for b in S["bold"][:5]) and S["ios26"] and not S["owner"], S)
            lay = pg.evaluate(G["LAYOUT"])
            chk("(5) the sheet is inside the screen, nothing sideways, every button 44px+, one choice of three", bool(lay) and lay["inside"] and lay["sideways"] <= 0 and not lay["small"] and lay["radios"] == 3, lay)
            shot(pg, "sheet")
        pg.evaluate("()=>document.querySelector('#a2hs-sheet .a2hs-close').click()"); pg.wait_for_timeout(900)
        stays = pg.evaluate(BAR_UP)
        chk("(5) Not now closes the walkthrough and the bar STAYS (nothing stored: %s)" % bar_key(pg), stays and not pg.evaluate("()=>!!document.getElementById('a2hs-sheet')") and bar_key(pg) is None, [stays, bar_key(pg)])
        relaunch(pg); on_home(pg); still = wait_bar(pg, 30)
        chk("(5) and after a reload it is still there", still, still)
        pg.click("#a2hsbar .a2hs-bar-main"); pg.wait_for_timeout(1000)
        pg.evaluate("()=>document.querySelector('#a2hs-sheet .a2hs-added').click()"); pg.wait_for_timeout(900)
        key = bar_key(pg); gone = gone_bar(pg)
        chk("(5) I've added it: the walkthrough closes, the bar is gone, class26e.a2hs.bar is d and a time (%s)" % key,
            gone and bool(re.fullmatch(r"d\d+", key or "")) and not pg.evaluate("()=>!!document.getElementById('a2hs-sheet')"), [gone, key])
        relaunch(pg, 3500); on_home(pg); n = never_bar(pg, 10)
        chk("(5) and it does not come back after a reload", n, n)
        errs_all.extend(pg.errs); ctx.close()
        # Android: the same bar, the Android choice, Samsung/Chrome steps with their buttons in bold
        ctx, pg = open2(br, "android")
        on_home(pg); wait_bar(pg, 30)
        pg.click("#a2hsbar .a2hs-bar-main"); pg.wait_for_timeout(1000)
        A = pg.evaluate("""()=>{ const o=document.getElementById('a2hs-sheet'); if(!o) return null; return { dev:o.dataset.dev, bold:o.querySelectorAll('.a2hs-android .a2hs-step-main strong').length,
          added:!!o.querySelector('.a2hs-added') && !o.querySelector('.a2hs-added').hidden }; }""")
        chk("(5) Android: the bar opens the Android choice, its steps name their buttons in bold, I've added it is offered (%s)" % A, bool(A) and A["dev"] == "android" and A["bold"] >= 6 and A["added"], A)
        errs_all.extend(pg.errs); ctx.close()

    # ---------------------------------------------------------------- (6)(7)(8) notices, furniture, taps, shifts
    if want("notices"):
        print("\n(6) the update and re-add notices come first")
        stale = {"build": BUILD + "-newer", "force": False, "frameId": ""}
        ctx, pg = open2(br, "iphone", version=stale, wait=2500)
        on_home(pg)
        both = 0; seenUpd = False; overlap = 0
        for _ in range(60):
            r = pg.evaluate("""()=>{ const u=document.getElementById('updatebanner'), b=document.getElementById('a2hsbar'); const ur=u&&u.getBoundingClientRect(), br=b&&b.getBoundingClientRect();
              return { u: !!u && u.classList.contains('show'), b: !!b && b.classList.contains('show') && !b.classList.contains('is-leaving'),
                ov: !!(ur && br && br.width>0 && ur.width>0 && !(br.bottom<=ur.top || br.top>=ur.bottom)) }; }""")
            seenUpd = seenUpd or r["u"]; both += 1 if (r["u"] and r["b"]) else 0; overlap += 1 if r["ov"] else 0
            pg.wait_for_timeout(250)
        chk("(6) while the update notice is up the bar is not (never both on screen at once, no box overlap) - the notice was shown: %s" % seenUpd, seenUpd and both == 0 and overlap == 0, [seenUpd, both, overlap])
        pg.evaluate("()=>document.querySelector('#updatebanner .update-banner-close').click()"); pg.wait_for_timeout(600)
        back = wait_bar(pg, 25)
        chk("(6) when the update notice is dismissed the bar comes back", back, back)
        errs_all.extend(pg.errs); ctx.close()
        ctx, pg = open2(br, "iphone")
        on_home(pg); wait_bar(pg, 30)
        pg.evaluate("()=>{ pendingNotice = { kind: 'frame', info: { frameId: 'gate-1', frameNote: 'Gate notice.' } }; syncNoticeVisibility(); }"); pg.wait_for_timeout(900)
        r = pg.evaluate("""()=>{ const u=document.getElementById('updatebanner'), b=document.getElementById('a2hsbar'); const ur=u&&u.getBoundingClientRect(), br=b&&b.getBoundingClientRect();
          return { u: !!u, b: !!b && b.classList.contains('show') && !b.classList.contains('is-leaving'), ov: !!(ur && br && !(br.bottom<=ur.top || br.top>=ur.bottom)) }; }""")
        chk("(6) the re-add notice takes the top: the bar steps aside (%s)" % r, r["u"] and not r["b"] and not r["ov"], r)
        pg.evaluate("()=>{ pendingNotice = null; hideBanner(); }"); back = wait_bar(pg, 20)
        chk("(6) and returns when it goes", back, back)
        # a banner arriving after the bar parks below it
        pg.evaluate("()=>showDailyAlert && showDailyAlert('Gate banner: nothing to see here.')"); pg.wait_for_timeout(900)
        r = pg.evaluate("""()=>{ const a=document.querySelector('.daily-alert.show'), b=document.getElementById('a2hsbar'); if(!a||!b) return { a:!!a, b:!!b };
          /* layout boxes (offsetTop), not painted ones: a banner is still sliding in with a transform here */
          const aT=a.offsetTop, bB=b.offsetTop+b.offsetHeight; return { a:true, b:true, gap: aT - bB, ovl: aT < bB }; }""")
        chk("(6) a banner that arrives after the bar parks below it, not over it (%s)" % r, bool(r.get("a")) and bool(r.get("b")) and not r["ovl"] and r["gap"] >= 0, r)
        errs_all.extend(pg.errs); ctx.close()

        print("\n(7)(8) Home is neither covered nor blocked, and nothing shifts")
        for dev in ("iphone", "se", "ipad"):
            ctx, pg = open2(br, dev)
            on_home(pg); up = wait_bar(pg, 30); top_a = pg.evaluate("()=>{ const b=document.getElementById('a2hsbar'); return b ? b.offsetTop : null; }"); pg.wait_for_timeout(2500)
            pg.evaluate("()=>document.querySelectorAll('.daily-alert').forEach(a=>a.remove())"); pg.wait_for_timeout(600)
            R = pg.evaluate("""()=>{ const b=document.getElementById('a2hsbar'); if(!b) return null; const br=b.getBoundingClientRect();
              const sels=['.chatdock-btn','.cosmic-hero-wrap','.cosmic-badge','.hometitle-wrap','.playbtn','.daily-question-fab','.bottomtabs','.bottomtab','.class-bubble'];
              const hit=[]; const taps=[];
              sels.forEach(s => document.querySelectorAll(s).forEach(e => { const r=e.getBoundingClientRect(), cs=getComputedStyle(e); if(r.width<=0||r.height<=0||cs.visibility==='hidden'||cs.display==='none'||parseFloat(cs.opacity)<.05) return;
                if(e.closest('[hidden]')) return;
                if(!(r.right<=br.left||r.left>=br.right||r.bottom<=br.top||r.top>=br.bottom)) hit.push(s + ' ' + Math.round(r.left)+','+Math.round(r.top)+','+Math.round(r.right)+','+Math.round(r.bottom));
                if(s!=='.cosmic-hero-wrap'){ const cx=(r.left+r.right)/2, cy=(r.top+r.bottom)/2; if(cx>=0&&cy>=0&&cx<innerWidth&&cy<innerHeight){ const t=document.elementFromPoint(cx,cy);
                  if(t && (t===b||b.contains(t))) taps.push(s + ' blocked'); } } }));
              return { hit, taps, bar:[Math.round(br.left),Math.round(br.top),Math.round(br.right),Math.round(br.bottom)] }; }""")
            chk("(7) %s the bar's box meets none of the chat button, the planet system, its flares, the greeting, Start Studying, the daily button, the tab bar; a tap at each of their centres is not the bar's (%s)" % (dev, R and R["bar"]),
                up and bool(R) and not R["hit"] and not R["taps"], R)
            below = pg.evaluate("()=>{ const b=document.getElementById('a2hsbar').getBoundingClientRect(); const y=Math.min(innerHeight-2, b.bottom+3); const t=document.elementFromPoint(innerWidth/2, y); return !t || !document.getElementById('a2hsbar').contains(t); }")
            chk("(7) %s a point just under the bar is not the bar's" % dev, below, below)
            shot(pg, "home")
            top_b = pg.evaluate("()=>{ const b=document.getElementById('a2hsbar'); return b ? b.offsetTop : null; }")
            chk("(8) %s the bar's layout position does not change after it has arrived (its slide in is a transform) (%s then %s)" % (dev, top_a, top_b), top_a is not None and top_b is not None and abs(top_a - top_b) <= 1, [top_a, top_b])
            if True:   # every device
                L = pg.evaluate("()=>({ ls: window.__ls || [], at: window.__barShowAt || 0, hero: (()=>{ const h=document.querySelector('.cosmic-hero-wrap'); return h ? getComputedStyle(h).translate : null; })() })")
                later = [e for e in L["ls"] if e["t"] >= L["at"] - 120]
                chk("(8) %s no layout shift from the moment the bar shows (%d entries in all, %d from then; %s); the planet moves by translate (%s)"
                    % (dev, len(L["ls"]), len(later), [(round(e["v"], 4), e["src"]) for e in later][:3], L["hero"]), L["at"] > 0 and not later, L)
            errs_all.extend(pg.errs); ctx.close()

    # ---------------------------------------------------------------- (9) never over a test, a tour, a cutscene, the splash
    if want("never"):
        print("\n(9) never over a test, a tour, a cutscene or the splash")
        ctx, pg = open2(br, "iphone")
        on_home(pg); wait_bar(pg, 30)
        pg.evaluate("()=>{ const d=document.createElement('div'); d.id='tour-overlay'; document.body.appendChild(d); syncNoticeVisibility(); }")
        t1 = gone_bar(pg, 4)
        pg.evaluate("()=>{ document.getElementById('tour-overlay').remove(); holdNoticesAfterTour(); }"); pg.wait_for_timeout(5200)
        t2 = wait_bar(pg, 20)
        chk("(9) a tour on screen: the bar is gone (%s); it is back after the tour's quiet (%s)" % (t1, t2), t1 and t2, [t1, t2])
        pg.evaluate("()=>{ cutsceneFocusDepth = 1; syncNoticeVisibility(); }")
        c1 = gone_bar(pg, 4)
        pg.evaluate("()=>{ cutsceneFocusDepth = 0; syncNoticeVisibility(); }"); c2 = wait_bar(pg, 20)
        chk("(9) a cutscene: the bar is gone (%s); it is back after (%s)" % (c1, c2), c1 and c2, [c1, c2])
        pg.evaluate("()=>{ const d=document.createElement('div'); d.id='splashscreen'; document.body.appendChild(d); document.getElementById('a2hsbar')?.remove(); syncNoticeVisibility(); }")
        s1 = never_bar(pg, 5)
        pg.evaluate("()=>{ document.getElementById('splashscreen').remove(); }"); s2 = wait_bar(pg, 25)
        chk("(9) the splash up: the bar does not come (%s); it comes once it has gone (%s)" % (s1, s2), s1 and s2, [s1, s2])
        pg.evaluate("()=>beginRun([0], 'Gate run')"); pg.wait_for_timeout(5000)
        run = pg.evaluate("()=>({ q: !!document.querySelector('.choice'), bar: !!document.getElementById('a2hsbar') })")
        chk("(9) in a test (a question on screen) there is no bar (%s)" % run, run["q"] and not run["bar"], run)
        errs_all.extend(pg.errs); ctx.close()

    # ---------------------------------------------------------------- (12) a phone on its side
    if want("land"):
        print("\n(12) a phone on its side has no room for it; a tablet does")
        res = {}
        for dev in ("se-land", "promax-land", "android-land"):
            ctx, pg = open2(br, dev); on_home(pg); res[dev] = never_bar(pg, 8); errs_all.extend(pg.errs); ctx.close()
        chk("(12) never on an iPhone or Android phone held sideways, however long it waits (%s)" % res, all(res.values()), res)
        ctx, pg = open2(br, "ipad-land"); on_home(pg); up = wait_bar(pg, 30); info = pg.evaluate(BAR) if up else None
        chk("(12) an iPad on its side has it, clear of the chat button (%s)" % (info and [round(v) for v in info["rect"]]), bool(info) and info["insideX"] and info["x"][0] >= 43.5, info)
        shot(pg, "land")
        errs_all.extend(pg.errs); ctx.close()
        # turned upright, it comes; turned on its side, it goes
        ctx, pg = open2(br, "iphone"); on_home(pg); up = wait_bar(pg, 30)
        pg.set_viewport_size({"width": 956, "height": 440}); pg.wait_for_timeout(500)
        g = gone_bar(pg, 5)
        pg.set_viewport_size({"width": 440, "height": 956}); back = wait_bar(pg, 20)
        chk("(12) turned on its side the bar goes, turned upright it comes back (%s, %s, %s)" % (up, g, back), up and g and back, [up, g, back])
        errs_all.extend(pg.errs); ctx.close()

    # ---------------------------------------------------------------- (10) 85% page zoom
    if want("zoom"):
        print("\n(10) at 85% page zoom")
        ctx, pg = open2(br, "iphone"); on_home(pg); b100 = wait_bar(pg, 30); i100 = pg.evaluate(BAR); ctx.close()
        ctx, pg = open2(br, "zoom")
        on_home(pg); up = wait_bar(pg, 30); i = pg.evaluate(BAR) if up else None
        if i:
            k = 440.0 / 518.0   # CSS px -> points on the glass
            chk("(10) zoomed (--zc %.3f, html.page-zoomed %s): the bar's height is %.1fpt against %.1fpt at 100%%; the X %.1fpt (44+); its words %.1fpt against %.1fpt"
                % (i["zc"], i["page"], i["h"] * k, i100["h"], i["x"][0] * k, i["fs"] * k, i100["fs"]),
                i["page"] and i["zc"] > 1.1 and abs(i["h"] * k - i100["h"]) <= 3 and i["x"][0] * k >= 43.5 and i["x"][1] * k >= 43.5 and i["fs"] * k >= i100["fs"] - .6
                and i["insideX"] and i["sideways"] <= 0, [i, i100])
            shot(pg, "zoomed")
        else: chk("(10) zoomed: the bar came up", False, up)
        errs_all.extend(pg.errs); ctx.close()
    br.close()

chk("(11) no page or console errors", not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
