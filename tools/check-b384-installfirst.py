#!/usr/bin/env python3
"""Build 384.23 check: INSTALL FIRST, and the white button that opens the share menu.

The owner, watching classmates: "Someone clicks the link, they get the start up page. They create an account, then the Nova intro, then
the tips ... When people add it to their Home Screen and click it, the first thing they see is the start up page again even though they
just went through that entire process ... Maybe when you click the link the first thing it makes you do on the phone is add it to your Home
Screen." On iPhone and iPad the icon keeps its own storage, so nothing is carried: a phone or tablet in a browser tab with no account on it
opens on ONE page (showInstallFirst) whose job is the Home Screen; the account, the intro and the tips are made in the icon, once.
Asserted by shape (nothing here names a label, a build or a typed address):

 (1) WHO IS HELD  a touch phone or tablet, in any real browser, with no account and not installed: iPhone Safari, Chrome (CriOS), Firefox
     (FxiOS), Edge (EdgiOS), an iPad (iPadOS's Mac-like user agent plus touch points), Android Chrome, Firefox, Samsung Internet and an Android
     tablet - the install page is up, Get Started is not.
 (2) WHO IS NOT   a Mac's Safari (the same user agent as the iPad, without touch), Chrome and Firefox on a Mac, Windows Chrome, Edge and
     Firefox, Linux Chrome: Get Started as before. The installed app on a phone: Get Started. A phone with an account on it
     (a finished store, or a name, a sync code, or signed out): not held.
 (3) IN-APP BROWSERS  Instagram, Facebook (iOS and Android), TikTok, an iOS web view with no Safari token and an Android web view: the
     page asks for the browser first (data-mode=inapp), has the copyable link, and is not the share-menu page.
 (4) THE WAY OUT  "I can't add it" is at least 44px tall, goes on to Get Started and Welcome as before, is remembered (a reload does not
     show the install page again), and the in-app page has it too.
 (5) THE WHITE BUTTON  on iPhone and iPad, Open Share menu calls navigator.share from the tap with the page's own canonical address
     (read from og:url, never the address this page was served at) and the title; when it resolves the page says what to do next; when it
     rejects (cancelled or not), or the browser has no navigator.share, the guide (the Home Screen sheet) opens: no dead end. The same
     white button is the sheet's primary button wherever the sheet shows (Settings), with "I've added it" beside Not now as the quiet answers.
 (6) ANDROID  with the browser's install prompt (a stubbed beforeinstallprompt), the primary button calls prompt() and says what happened;
     with none (Firefox, Samsung), it opens the browser's menu steps (the sheet on Android).
 (7) BOOT  the page is built after boot like Get Started (the splash is still the first thing in the body, and the head gained no script or
     style for it); every button on the page is at least 44px.

  python3 tools/check-b384-installfirst.py [--against OLD/index.html]     (must FAIL on 384.22: there is no install page)
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
SRC_PATH = args[args.index("--against") + 1] if "--against" in args else None
SRC = L.load_src(SRC_PATH)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)

# navigator.share, stubbed: records what it was given; MODE is read from window.__shareMode: resolve | abort | fail
SHARE_STUB = """(()=>{ window.__shares = []; window.__shareMode = 'resolve';
  navigator.share = function(d){ window.__shares.push({url:d && d.url, title:d && d.title, text:d && d.text});
    if(window.__shareMode === 'abort') return Promise.reject(Object.assign(new Error('x'), {name:'AbortError'}));
    if(window.__shareMode === 'fail') return Promise.reject(Object.assign(new Error('x'), {name:'NotAllowedError'}));
    return Promise.resolve(); }; })();"""
NO_SHARE = "try{ Object.defineProperty(navigator,'share',{get:()=>undefined,configurable:true}); }catch(e){}"
STATE = """()=>{ const st = document.getElementById('stage'); const f = st && st.firstElementChild;
  const q = s => document.querySelector(s); const bt = e => { if(!e) return null; const r = e.getBoundingClientRect(); return { h: r.height, w: r.width, text: e.textContent.trim() }; };
  return { inst: !!(f && f.dataset && f.dataset.screen === 'installfirst'), mode: f && f.dataset ? f.dataset.mode : '', dev: f && f.dataset ? f.dataset.dev : '',
    gs: !!q('.gs-page'), welcome: !!q('.cosmic-welcome'), home: !!q('[data-screen=home]'),
    go: bt(q('.if-go')), skip: bt(q('.if-out')), guide: bt(q('.if-guide')), copy: bt(q('.if-copy')), link: !!q('.if-link-addr'),
    status: (q('.if-status') || {}).textContent || '', sheet: !!q('#a2hs-sheet'), sheetDev: (q('#a2hs-sheet') || {}).dataset ? q('#a2hs-sheet').dataset.dev : '',
    title: (q('.if-title') || {}).textContent || '' }; }"""

srv, url = L.serve()
def open_dev(br, ua, *, installed=False, seeded=False, extra=(), w=440, h=956):
    ctx, pg = L.new_page(br, SRC, url, ua=ua, installed=installed, seeded=seeded, extra_init=extra, w=w, h=h, insets=(62, 0, 34, 0) if w < 600 else (24, 0, 20, 0))
    L.boot(pg, url, 1800); pg.wait_for_timeout(1200)
    return ctx, pg
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME)
        # ---- (1) who is held
        for ua in ("iphone-safari", "iphone-chrome", "iphone-firefox", "iphone-edge", "ipad-safari", "android-chrome", "android-firefox", "android-samsung", "android-tablet-chrome"):
            ipad = ua in ("ipad-safari", "android-tablet-chrome")
            ctx, pg = open_dev(br, ua, w=834 if ipad else 440, h=1194 if ipad else 956)
            s = pg.evaluate(STATE)
            chk("(1) %s, no account, in a tab: the install page, not Get Started (dev %s)" % (ua, s["dev"]), s["inst"] and s["mode"] == "install" and not s["gs"] and not s["welcome"], s)
            ctx.close()
        # ---- (2) who is not
        for ua in ("mac-safari", "mac-chrome", "mac-firefox", "win-chrome", "win-edge", "win-firefox", "linux-chrome"):
            ctx, pg = open_dev(br, ua, w=1440, h=860)
            s = pg.evaluate(STATE)
            chk("(2) %s: not held (Get Started)" % ua, (not s["inst"]) and s["gs"], s)
            ctx.close()
        ctx, pg = open_dev(br, "iphone-safari", installed=True)
        s = pg.evaluate(STATE)
        chk("(2) the installed app on an iPhone, no account: Get Started, no install page", (not s["inst"]) and s["gs"], s)
        ctx.close()
        ctx, pg = open_dev(br, "android-chrome", installed=True)
        s = pg.evaluate(STATE)
        chk("(2) the installed app on Android: no install page", not s["inst"], s)
        ctx.close()
        ctx, pg = open_dev(br, "iphone-safari", seeded=True)
        pg.wait_for_timeout(2500); s = pg.evaluate(STATE)
        chk("(2) an iPhone in Safari WITH an account: Home, not held", s["home"] and not s["inst"], s)
        ctx.close()
        for lab, sc in (("a code in localStorage and no store", "try{localStorage.setItem('class26e.synccode','MADI-0001');}catch(e){}"),
                        ("signed out here", "try{localStorage.setItem('class26e.signedout','1');}catch(e){}"),
                        ("the mark that this device once held an account (site data cleared since)", "try{localStorage.setItem('class26e.hadaccount','1');}catch(e){}"),
                        ("a name in the saved store", "try{localStorage.setItem('class26e.drill.v1', JSON.stringify({firstName:'Kim'}));}catch(e){}")):
            ctx, pg = open_dev(br, "iphone-safari", extra=(sc,))
            s = pg.evaluate(STATE)
            chk("(2) an iPhone in Safari with %s: Welcome, not the install page" % lab, (not s["inst"]) and (s["welcome"] or s["home"] or s["gs"]), s)
            ctx.close()
        # ---- (3) in-app browsers
        for ua in ("iphone-instagram", "iphone-facebook", "iphone-tiktok", "iphone-webview", "android-facebook", "android-webview"):
            ctx, pg = open_dev(br, ua)
            s = pg.evaluate(STATE)
            chk("(3) %s: the open-it-in-a-browser page, with the link to copy, and not the share-menu page" % ua,
                s["inst"] and s["mode"] == "inapp" and s["link"] and s["go"] is not None and (s["guide"] is None), s)
            if ua == "iphone-instagram":
                chk("(4) the in-app page has the way out, at least 44px tall", s["skip"] and s["skip"]["h"] >= 43.5, s)
                tgt = pg.evaluate("()=>safariHandoffTarget()")
                chk("(3) its button's hand-off is Safari's scheme with this page's own address", tgt.startswith("x-safari-https://127.0.0.1"), tgt)
            ctx.close()
        # ---- (4) the way out
        ctx, pg = open_dev(br, "iphone-safari")
        s = pg.evaluate(STATE)
        chk("(4) the way out is at least 44px tall and wide", s["skip"] and s["skip"]["h"] >= 43.5 and s["skip"]["w"] >= 43.5, s)
        pg.click(".if-out"); pg.wait_for_timeout(1500)
        s2 = pg.evaluate(STATE)
        chk("(4) it goes on as before: Get Started, not the install page", s2["gs"] and not s2["inst"], s2)
        mem = pg.evaluate("()=>{ try{ return Object.keys(localStorage).filter(k=>/^class26e\\./.test(k)&&/install/.test(k)).length; }catch(e){ return -1; } }")
        chk("(4) and it is remembered under a class26e. key", mem >= 1, mem)
        pg.reload(); pg.wait_for_timeout(2500)
        pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); if(s) s.remove(); }"); pg.wait_for_timeout(800)
        s3 = pg.evaluate(STATE)
        chk("(4) a reload does not nag again", s3["gs"] and not s3["inst"], s3)
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); if(s) s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(900)
        pg.click(".gs-go"); pg.wait_for_timeout(900)
        chk("(4) Get Started's button still leads to Welcome", pg.evaluate("()=>!!document.querySelector('.cosmic-welcome')"), "")
        ctx.close()
        # ---- (5) the white button
        og = re.search(r'<meta property="og:url" content="([^"]+)"', SRC)
        canon = og.group(1) if og else None
        chk("(5) the page declares its canonical address (og:url)", bool(canon), canon)
        for ua, w, h in (("iphone-safari", 440, 956), ("ipad-safari", 834, 1194), ("iphone-chrome", 440, 956)):
            ctx, pg = open_dev(br, ua, extra=(SHARE_STUB,), w=w, h=h)
            s = pg.evaluate(STATE)
            chk("(5) %s: the primary button is at least 44px and says it opens the share menu (not that it adds itself)" % ua,
                s["go"] and s["go"]["h"] >= 43.5 and re.search(r"share", s["go"]["text"], re.I) and not re.search(r"\badded\b|\binstalled\b", s["go"]["text"], re.I), s)
            pg.click(".if-go"); pg.wait_for_timeout(700)
            sh = pg.evaluate("()=>window.__shares"); s = pg.evaluate(STATE)
            chk("(5) %s: the tap calls navigator.share once with the canonical address and a title" % ua,
                len(sh) == 1 and sh[0]["url"] == canon and sh[0]["title"], sh)
            chk("(5) %s: shared, it says what to do next and does not open the guide over it" % ua, s["status"].strip() and not s["sheet"], s)
            for mode in ("abort", "fail"):
                pg.evaluate("(m)=>{ window.__shareMode = m; document.getElementById('a2hs-sheet') && document.getElementById('a2hs-sheet').remove(); }", mode)
                pg.click(".if-go"); pg.wait_for_timeout(900)
                s = pg.evaluate(STATE)
                chk("(5) %s: share %s -> the guide opens (no dead end)" % (ua, "cancelled" if mode == "abort" else "failed"), s["sheet"] and s["sheetDev"] == "apple", s)
            ctx.close()
        ctx, pg = open_dev(br, "iphone-safari", extra=(NO_SHARE,))
        pg.click(".if-go"); pg.wait_for_timeout(900); s = pg.evaluate(STATE)
        chk("(5) no navigator.share: the guide opens", s["sheet"] and s["sheetDev"] == "apple", s)
        ctx.close()
        # the sheet's own white button (Settings > Add to Home Screen, on an iPhone with an account)
        ctx, pg = open_dev(br, "iphone-safari", seeded=True, extra=(SHARE_STUB,))
        pg.wait_for_timeout(2500)
        pg.evaluate("()=>showHomeScreenSheet({ from: 'settings' })"); pg.wait_for_timeout(1200)
        g = pg.evaluate("""()=>{ const o=document.getElementById('a2hs-sheet'); const q=s=>o.querySelector(s); const vis=e=>!!e&&!e.hidden&&e.getBoundingClientRect().width>0;
          const sb=q('.a2hs-share'), ad=q('.a2hs-added');
          return { share: vis(sb), shareH: sb ? sb.getBoundingClientRect().height : 0, shareText: sb ? sb.textContent : '', addedGhost: !!ad && ad.classList.contains('ghost'), addedVis: vis(ad), doneVis: vis(q('.a2hs-close')),
            primaryIsShare: sb ? !sb.classList.contains('ghost') : false }; }""")
        chk("(5) the sheet's white (primary) button opens the share menu; I've added it and Not now are the quiet ones", g["share"] and g["shareH"] >= 47.5 and g["primaryIsShare"] and g["addedGhost"] and g["addedVis"] and g["doneVis"], g)
        pg.evaluate("()=>{ window.__shareMode='resolve'; document.querySelector('#a2hs-sheet .a2hs-share').click(); }"); pg.wait_for_timeout(500)
        sh = pg.evaluate("()=>window.__shares")
        chk("(5) its tap calls navigator.share with the canonical address", len(sh) == 1 and sh[0]["url"] == canon, sh)
        pg.evaluate("()=>{ window.__shareMode='fail'; document.querySelector('#a2hs-sheet .a2hs-share').click(); }"); pg.wait_for_timeout(500)
        txt = pg.evaluate("()=>{ const e=document.querySelector('#a2hs-sheet .a2hs-share-status'); return e && !e.hidden ? e.textContent : ''; }")
        chk("(5) a failed share leaves the steps on the sheet and says to use them", txt.strip() and pg.evaluate("()=>!!document.getElementById('a2hs-sheet')"), txt)
        ctx.close()
        # ---- (6) Android
        PROMPT = """(()=>{ window.__prompts = 0; window.__fire = function(outcome){ const e = new Event('beforeinstallprompt'); e.prompt = function(){ window.__prompts++; return Promise.resolve(); };
            e.userChoice = Promise.resolve({ outcome: outcome || 'accepted' }); window.dispatchEvent(e); }; })();"""
        ctx, pg = open_dev(br, "android-chrome", extra=(PROMPT,))
        before = pg.evaluate(STATE)
        pg.evaluate("()=>window.__fire('accepted')"); pg.wait_for_timeout(500)
        s = pg.evaluate(STATE)
        chk("(6) Android Chrome with the install prompt: the button changes to Install and the guide link hides (was %r, now %r)" % (before["go"] and before["go"]["text"], s["go"] and s["go"]["text"]),
            s["go"] and s["go"]["text"] != (before["go"] or {}).get("text") and pg.evaluate("()=>{ const g=document.querySelector('.if-guide'); return !g || g.hidden; }"), s)
        pg.click(".if-go"); pg.wait_for_timeout(700)
        n = pg.evaluate("()=>window.__prompts"); s = pg.evaluate(STATE)
        chk("(6) its tap calls the browser's prompt() once and says what happened", n == 1 and s["status"].strip() and not s["sheet"], [n, s])
        ctx.close()
        for ua in ("android-firefox", "android-samsung"):
            ctx, pg = open_dev(br, ua)
            pg.click(".if-go"); pg.wait_for_timeout(900); s = pg.evaluate(STATE)
            chk("(6) %s without an install prompt: the button opens the browser's menu steps (the sheet on Android)" % ua, s["sheet"] and s["sheetDev"] == "android", s)
            ctx.close()
        # ---- (7) boot
        order = re.search(r"<body>\s*<div id=\"splashscreen\">", SRC) is not None
        chk("(7) the splash is still the first thing in <body>", order, "")
        head = SRC[:SRC.index("</head>")]
        chk("(7) nothing of the install page is in the head", "installfirst" not in head and "showInstallFirst" not in head, "")
        ctx, pg = open_dev(br, "iphone-safari")
        small = pg.evaluate("()=>[...document.querySelectorAll('#stage button')].filter(b=>!b.hidden&&b.getBoundingClientRect().width>0).filter(b=>b.getBoundingClientRect().height<43.5).map(b=>b.className)")
        chk("(7) every button on the install page is at least 44px", not small, small)
        side = pg.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        chk("(7) nothing is wider than the screen", side <= 0, side)
        ctx.close()
        br.close()
finally:
    srv.shutdown()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
