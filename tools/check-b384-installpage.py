#!/usr/bin/env python3
"""Build 384.36 check: THE INSTALL PAGE, FRIENDLY, with the video above the share menu.

The owner: "Could this look better, friendly? ... shouldn't it say, open the app from your Home Screen once done ... very clear
instructions ... Remove the show me how ... When you hit the button the share menu will pop up, and right above the share menu will be the
video that plays so you can watch simultaneously. And the video won't have all those 'options' under the video, should just say I've done it
or maybe that's also where it says I can't add it ... 'I can't add it' ... open the walkthrough or give help full screen and then it
could say 'still can't add it' and then you can continue with safari."
Asserted by shape (nothing names a label or a typed pixel number; what is measured is read off the page):

 (1) THE PAGE      the app icon, three numbered steps, a primary button and a quiet way out; the old "Show me how" link is gone; the button
                   is not a share-icon circle; text is 16px or more; every control 44px or more; nothing wider than the screen.
 (2) THE TAP       the primary calls navigator.share exactly once, in the tap, with the canonical address; in the same task the page is the
                   video screen. Share resolved, cancelled, failed or missing: the same screen.
 (3) THE VIDEO     exists, is playing (or has been asked to), muted, playsinline, loops; its box and its one-line heading end inside the top
                   ~45% of the viewport on 440x956, 393x852, 375x667 and 834x1194 (measured); exactly two controls under it (a primary and a
                   quiet one), no tabs, no step list, no note. The box takes its crop from CSS custom properties (a new recording is a CSS
                   change: changing --iv-ar changes the box's shape, --iv-pos changes the object-position the video is drawn with).
 (4) I'VE ADDED IT the final state (icon, a line saying to open Nova from the Home Screen, a line saying the page can be closed), no way into
                   sign-up from it, no account made; the reminder bar is over (what the old guide's answer did).
 (5) I CAN'T ADD IT on the install page and on the video screen: a full-screen help page with exactly two buttons; Try again returns to the
                   install page; Still can't add it lands where the old skip did (Get Started) and the install page is never shown again.
 (6) THE OTHERS    Android with the install prompt keeps Install Nova; without it, the same video screen and two answers, no share call; the
                   in-app page has the icon, the friendly line, Open in Safari, the copy link and the same quiet way to the help page;
                   a computer is unchanged (Get Started).
 (7) THE SWAP      the clip's path is one constant (INSTALL_CLIP) read by the video element.

  python3 tools/check-b384-installpage.py [--against OLD/index.html]     (must FAIL on 384.34: there is no video screen)
"""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
SRC_PATH = args[args.index("--against") + 1] if "--against" in args else None
SRC = L.load_src(SRC_PATH)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

SHARE_STUB = """(()=>{ window.__shares = []; window.__shareMode = 'resolve'; window.__shareAt = [];
  navigator.share = function(d){ window.__shares.push({url:d && d.url, title:d && d.title}); window.__shareAt.push(!!document.querySelector('[data-screen=installfirst]'));
    if(window.__shareMode === 'abort') return Promise.reject(Object.assign(new Error('x'), {name:'AbortError'}));
    if(window.__shareMode === 'fail') return Promise.reject(Object.assign(new Error('x'), {name:'NotAllowedError'}));
    return Promise.resolve(); }; })();"""
NO_SHARE = "try{ Object.defineProperty(navigator,'share',{get:()=>undefined,configurable:true}); }catch(e){}"
STATE = """()=>{ const st = document.getElementById('stage'); const f = st && st.firstElementChild; const q = s => document.querySelector(s);
  const vis = e => !!e && !e.hidden && e.getBoundingClientRect().width > 0;
  const r = e => { if(!e) return null; const b = e.getBoundingClientRect(); return { top:b.top, bottom:b.bottom, left:b.left, right:b.right, h:b.height, w:b.width }; };
  const ctl = f ? [...f.querySelectorAll('button, a, input:not(.nova-hsw), select, textarea, [role=button]')].filter(e => vis(e) && !e.classList.contains('iv-play')) : [];
  const kinds = ctl.map(b => b.classList.contains('next') ? 'primary' : 'quiet');
  const v = q('.iv-frame video');
  return { screen: f && f.dataset ? f.dataset.screen : '', mode: f && f.dataset ? f.dataset.mode : '', dev: f && f.dataset ? f.dataset.dev : '',
    vh: innerHeight, vw: innerWidth, sw: document.documentElement.scrollWidth - innerWidth,
    icon: !!(f && f.querySelector('.if-appicon img')), steps: f ? f.querySelectorAll('.if-steps .if-step').length : 0, nums: f ? f.querySelectorAll('.if-step .if-num').length : 0,
    guide: !!q('.if-guide'), sheet: !!q('#a2hs-sheet'), gs: !!q('.gs-page'), welcome: !!q('.cosmic-welcome'), home: !!q('[data-screen=home]'), nova: !!q('#nova-intro'),
    primary: r(q('.next.playbtn')), primaryText: (q('.next.playbtn') || {}).textContent || '', skip: r(q('.if-skip')), controls: ctl.length, kinds: kinds,
    ctlH: ctl.map(b => b.getBoundingClientRect().height), tabs: !!q('.a2hs-seg, [role=tablist], [role=radiogroup]'), lists: f ? f.querySelectorAll('.if-steps:not(.if-steps-card), .a2hs-steps').length : 0,
    notes: f ? f.querySelectorAll('.if-note:not(:empty), .if-after, .a2hs-note, .if-status:not([hidden])').length : 0,
    frame: r(q('.iv-frame')), head: r(q('.if-vhead')), headText: (q('.if-vhead') || {}).textContent || '', title: (q('.if-title') || {}).textContent || '',
    after: (q('.if-after') || {}).textContent || '', afterWeight: q('.if-after') ? parseInt(getComputedStyle(q('.if-after')).fontWeight) : 0, afterVis: vis(q('.if-after')),
    device: (q('.if-device') || {}).textContent || '', deviceVis: vis(q('.if-device')), gsDevice: (q('.gs-device') || {}).textContent || '', gsDeviceVis: vis(q('.gs-device')),
    lastStep: f && f.querySelector('.if-steps') ? [...f.querySelectorAll('.if-steps .if-step')].pop().textContent : '', line: (q('.if-line') || {}).textContent || '',
    video: v ? { paused: v.paused, muted: v.muted, pi: v.playsInline, loop: v.loop, auto: v.autoplay, src: v.getAttribute('src'), pos: getComputedStyle(v).objectPosition, t: v.currentTime } : null,
    frameAR: q('.iv-frame') ? q('.iv-frame').getBoundingClientRect().width / q('.iv-frame').getBoundingClientRect().height : 0,
    fontMin: f ? Math.min(...[...f.querySelectorAll('p, li, span, button, code, h1, h2')].filter(e => e.childElementCount === 0 && e.textContent.trim() && e.getBoundingClientRect().width > 0 && !e.closest('[hidden]')).map(e => parseFloat(getComputedStyle(e).fontSize))) : 0,
    kicker: (q('.if-kicker') || {}).textContent || '' }; }"""

srv, url = L.serve()
def open_dev(br, ua, *, extra=(), w=440, h=956, seeded=False):
    ctx, pg = L.new_page(br, SRC, url, ua=ua, seeded=seeded, extra_init=extra, w=w, h=h, insets=(62, 0, 34, 0) if w < 600 else (24, 0, 20, 0))
    L.boot(pg, url, 1800); pg.wait_for_timeout(1200)
    return ctx, pg
SIZES = ((440, 956, "iphone-safari"), (393, 852, "iphone-safari"), (375, 667, "iphone-safari"), (834, 1194, "ipad-safari"))
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME)
        og = re.search(r'<meta property="og:url" content="([^"]+)"', SRC); canon = og.group(1) if og else None
        # ---- (1) the page
        for w, h, ua in SIZES:
            ctx, pg = open_dev(br, ua, extra=(SHARE_STUB,), w=w, h=h)
            s = pg.evaluate(STATE)
            chk("(1) %dx%d the install page has the app icon, numbered steps, a primary button and a quiet way out" % (w, h),
                s["screen"] == "installfirst" and s["icon"] and s["steps"] >= 3 and s["nums"] == s["steps"] and s["primary"] and s["skip"], s)
            chk("(1) %dx%d the old 'Show me how' link is gone, and it is the only quiet control" % (w, h), (not s["guide"]) and s["kinds"].count("quiet") == 1 and s["kinds"].count("primary") == 1, s)
            chk("(1) %dx%d it says to open Nova from the Home Screen once it is added (a line of its own, apart from the steps)" % (w, h), len(s["after"].strip()) > 20 and len(s["kicker"].strip()) > 3 and len(s["line"].strip()) > 20, s)
            chk("(1) %dx%d it says plainly that this is the phone version and that there is a computer version (its own visible line), and the last line (to open Nova from its icon every time, not from the browser) is bold and visible" % (w, h),
                len(s["device"].strip()) > 40 and s["deviceVis"] and len(s["after"].strip()) > 80 and s["afterWeight"] >= 600 and s["afterVis"] and len(s["lastStep"].strip()) > 25, [s["device"], s["after"], s["afterWeight"], s["lastStep"]])
            chk("(1) %dx%d text is 16px or more, controls 44px or more, nothing wider than the screen" % (w, h), s["fontMin"] >= 15.9 and min(s["ctlH"]) >= 43.5 and s["sw"] <= 0, [s["fontMin"], s["ctlH"], s["sw"]])
            chk("(1) %dx%d the button is inside the screen without scrolling (except a 320px phone, not run here)" % (w, h), s["primary"]["bottom"] <= s["vh"] + 0.5, [s["primary"], s["vh"]])
            ctx.close()
        # ---- (2) the tap, and (3) the video
        for w, h, ua in SIZES:
            for mode in ("resolve", "abort", "fail", "none"):
                ctx, pg = open_dev(br, ua, extra=(NO_SHARE if mode == "none" else SHARE_STUB,), w=w, h=h)
                if mode != "none": pg.evaluate("(m)=>{ window.__shareMode = m; }", mode)
                pg.click(".next.playbtn"); pg.wait_for_timeout(1500)
                s = pg.evaluate(STATE)
                if mode != "none":
                    sh = pg.evaluate("()=>window.__shares"); at = pg.evaluate("()=>window.__shareAt")
                    chk("(2) %dx%d share %s: the tap calls navigator.share once, with the canonical address, while the install page is still the screen" % (w, h, mode),
                        len(sh) == 1 and sh[0]["url"] == canon and sh[0]["title"] and at == [True], [sh, at])
                chk("(2) %dx%d share %s: the page is the video screen" % (w, h, mode), s["screen"] == "installvideo" and s["video"] is not None and not s["sheet"], s)
                if mode == "resolve":
                    v = s["video"]
                    chk("(3) %dx%d the video is playing, muted, playsinline and loops" % (w, h), v and (not v["paused"]) and v["muted"] and v["pi"] and v["loop"] and v["t"] > 0, v)
                    lim = 0.45 * s["vh"]
                    chk("(3) %dx%d the video's bottom edge is in the top 45%% of the viewport (%.0f <= %.0f, %.1f%%)" % (w, h, s["frame"]["bottom"], lim, 100.0 * s["frame"]["bottom"] / s["vh"]),
                        s["frame"]["bottom"] <= lim, [s["frame"], s["vh"]])
                    chk("(3) %dx%d and the one-line heading is above it, inside too, on one line" % (w, h), s["head"] and s["head"]["bottom"] <= s["frame"]["top"] + 1 and s["head"]["h"] < 2 * 1.6 * 24 and s["headText"].strip(), [s["head"], s["headText"]])
                    chk("(3) %dx%d the video's box is wider than the heading is tall, and the screen has no sideways scroll" % (w, h), s["frame"]["w"] > 100 and s["sw"] <= 0, s)
                    chk("(3) %dx%d under the video: exactly two controls, one primary and one quiet, 44px or more; no tabs, no step list, no note" % (w, h),
                        s["controls"] == 2 and sorted(s["kinds"]) == ["primary", "quiet"] and min(s["ctlH"]) >= 43.5 and not s["tabs"] and s["lists"] == 0 and s["notes"] == 0, s)
                    chk("(3) %dx%d both answers are below the video (not over it)" % (w, h), s["primary"]["top"] >= s["frame"]["bottom"] and s["skip"]["top"] >= s["frame"]["bottom"], [s["primary"], s["skip"], s["frame"]])
                ctx.close()
        # the crop is CSS: change the custom properties and the box and the picture change
        ctx, pg = open_dev(br, "iphone-safari", extra=(SHARE_STUB,))
        pg.click(".next.playbtn"); pg.wait_for_timeout(900)
        a = pg.evaluate(STATE)
        pg.evaluate("()=>{ const p = document.querySelector('.installvideo-panel'); p.style.setProperty('--iv-ar', '0.8'); p.style.setProperty('--iv-pos', '10% 20%'); }"); pg.wait_for_timeout(300)
        b = pg.evaluate(STATE)
        chk("(7) the box's shape follows --iv-ar and the picture's crop follows --iv-pos (a new recording is tuned in CSS)", a["frameAR"] > 1.2 and b["frameAR"] < 1.0 and a["video"]["pos"] != b["video"]["pos"], [a["frameAR"], b["frameAR"], a["video"]["pos"], b["video"]["pos"]])
        chk("(7) the video element reads the clip's path from one constant (INSTALL_CLIP)", pg.evaluate("()=>document.querySelector('.iv-frame video').getAttribute('src') === INSTALL_CLIP.src") is True, "")
        ctx.close()
        # ---- (4) I've added it
        ctx, pg = open_dev(br, "iphone-safari", extra=(SHARE_STUB,))
        pg.click(".next.playbtn"); pg.wait_for_timeout(800)
        pg.click(".installvideo-panel .next.playbtn"); pg.wait_for_timeout(900)
        s = pg.evaluate(STATE)
        chk("(4) I've added it: the final state (the icon, a line to open Nova from the Home Screen, a line to close the page)", s["screen"] == "installdone" and s["icon"] and len(s["title"]) > 10 and len(s["line"]) > 8, s)
        chk("(4) the final state says Nova is an app on the phone and to use that icon every time (a bold line of its own), and has the phone/computer-version line",
            len(s["after"].strip()) > 80 and s["afterWeight"] >= 600 and s["afterVis"] and len(s["device"].strip()) > 40 and s["deviceVis"], [s["after"], s["afterWeight"], s["device"]])
        chk("(4) it does not lead into sign-up: no primary button, no Get Started, Welcome or Nova; no account was made", s["primary"] is None and not (s["gs"] or s["welcome"] or s["nova"] or s["home"]) and
            pg.evaluate("()=>!(store.firstName||store.onboardingComplete) && !syncCode"), s)
        chk("(4) the reminder bar's mark: the one-time showing counts as made and the bar is over (what the old answer did)",
            pg.evaluate("()=>{ try{ return /^\\d+$/.test(localStorage.getItem('class26e.a2hs')||'') && /^d\\d+$/.test(localStorage.getItem('class26e.a2hs.bar')||''); }catch(e){ return false; } }"), "")
        chk("(4) its one quiet control goes back to the install page, not on", s["controls"] == 1, s)
        pg.click(".if-skip"); pg.wait_for_timeout(700)
        chk("(4) ... which is the install page", pg.evaluate(STATE)["screen"] == "installfirst", "")
        ctx.close()
        # ---- (5) I can't add it, from both places
        for where in ("the install page", "the video screen"):
            ctx, pg = open_dev(br, "iphone-safari", extra=(SHARE_STUB,))
            if where == "the video screen": pg.click(".next.playbtn"); pg.wait_for_timeout(800)
            pg.click(".if-skip"); pg.wait_for_timeout(900)
            s = pg.evaluate(STATE)
            chk("(5) %s: I can't add it opens the full-screen help page with exactly two buttons (a primary and a quiet one)" % where,
                s["screen"] == "installhelp" and s["controls"] == 2 and sorted(s["kinds"]) == ["primary", "quiet"] and s["steps"] >= 3 and s["sw"] <= 0 and min(s["ctlH"]) >= 43.5 and len(s["title"]) > 8, s)
            pg.click(".next.playbtn"); pg.wait_for_timeout(800)
            s = pg.evaluate(STATE)
            chk("(5) %s: Try again returns to the install page" % where, s["screen"] == "installfirst" and s["primary"], s)
            pg.click(".if-skip"); pg.wait_for_timeout(600); pg.click(".if-skip"); pg.wait_for_timeout(1500)
            s = pg.evaluate(STATE)
            chk("(5) %s: Still can't add it lands where the old skip did (Get Started), and the install page is not up" % where, s["gs"] and s["screen"] != "installfirst", s)
            mem = pg.evaluate("()=>{ try{ return Object.keys(localStorage).filter(k=>/^class26e\\./.test(k)&&/install/.test(k)).length; }catch(e){ return -1; } }")
            pg.reload(); pg.wait_for_timeout(2500)
            pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); if(s) s.remove(); }"); pg.wait_for_timeout(800)
            s = pg.evaluate(STATE)
            chk("(5) %s: remembered (a class26e. key), and a reload does not show the install page again" % where, mem >= 1 and s["gs"] and s["screen"] != "installfirst", [mem, s])
            ctx.close()
        # ---- (6) the others
        PROMPT = """(()=>{ window.__prompts = 0; window.__fire = function(){ const e = new Event('beforeinstallprompt'); e.prompt = function(){ window.__prompts++; return Promise.resolve(); };
            e.userChoice = Promise.resolve({ outcome: 'accepted' }); window.dispatchEvent(e); }; })();"""
        ctx, pg = open_dev(br, "android-chrome", extra=(PROMPT, SHARE_STUB))
        a = pg.evaluate(STATE)
        pg.evaluate("()=>window.__fire()"); pg.wait_for_timeout(500)
        b = pg.evaluate(STATE)
        chk("(6) Android Chrome: the same friendly page (icon, steps); with the install prompt the button becomes Install and calls prompt()", a["icon"] and a["steps"] >= 3 and b["primaryText"] != a["primaryText"], [a["primaryText"], b["primaryText"]])
        pg.click(".next.playbtn"); pg.wait_for_timeout(600)
        s = pg.evaluate(STATE)
        chk("(6) ... once, and it stays on the page and says what happened", pg.evaluate("()=>window.__prompts") == 1 and s["screen"] == "installfirst" and not pg.evaluate("()=>window.__shares.length"), s)
        pg.click(".if-skip"); pg.wait_for_timeout(700)
        chk("(6) ... and its quiet way out is the help page (Android steps)", pg.evaluate(STATE)["screen"] == "installhelp", "")
        ctx.close()
        for ua in ("android-firefox", "android-samsung"):
            ctx, pg = open_dev(br, ua, extra=(SHARE_STUB,))
            pg.click(".next.playbtn"); pg.wait_for_timeout(900); s = pg.evaluate(STATE)
            chk("(6) %s with no install prompt: the video screen with the two answers, no share menu" % ua, s["screen"] == "installvideo" and s["controls"] == 2 and not pg.evaluate("()=>window.__shares.length") and s["dev"] == "android", s)
            ctx.close()
        for ua in ("iphone-instagram", "android-facebook"):
            ctx, pg = open_dev(br, ua)
            s = pg.evaluate(STATE)
            chk("(6) %s: the in-app page, friendly (icon, a welcome, the reason), with Open in Safari / Copy link and the quiet way out" % ua,
                s["screen"] == "installfirst" and s["mode"] == "inapp" and s["icon"] and len(s["kicker"]) > 3 and s["primary"] and s["skip"] and s["steps"] == 0, s)
            pg.click(".if-skip"); pg.wait_for_timeout(800)
            s = pg.evaluate(STATE)
            chk("(6) %s: its way out opens the same help page, and Try again returns to the in-app page (not the share page)" % ua, s["screen"] == "installhelp" and s["controls"] == 2, s)
            pg.click(".next.playbtn"); pg.wait_for_timeout(700)
            chk("(6) %s: ... in-app mode kept" % ua, pg.evaluate(STATE)["mode"] == "inapp", "")
            ctx.close()
        ctx, pg = open_dev(br, "win-chrome", w=1440, h=900)
        s = pg.evaluate(STATE)
        chk("(6) a computer is unchanged: Get Started, no install page", s["gs"] and s["screen"] != "installfirst", s)
        pg.wait_for_timeout(1800); s = pg.evaluate(STATE)
        chk("(8) the computer's Get Started page says the other way round: Nova is made for a phone (its own visible line)", len(s["gsDevice"].strip()) > 60 and s["gsDeviceVis"], [s["gsDevice"], s["gsDeviceVis"]])
        g = pg.evaluate("""()=>{ showHomeScreenSheet({from:'settings',device:'computer'}); const l=document.querySelector('#a2hs-sheet .a2hs-computer .a2hs-lead'); return l ? l.textContent : ''; }""")
        chk("(8) and so does the computer branch of the Home Screen guide", len(g.strip()) > 60, g)
        ctx.close()
        for lab, ua, inst in (("an iPhone with the install page skipped (Get Started on a phone)", "iphone-safari", False), ("the installed app", "iphone-safari", True)):
            ctx, pg = L.new_page(br, SRC, url, ua=ua, installed=inst, w=440, h=956, insets=(62, 0, 34, 0), extra_init=("try{localStorage.setItem('class26e.installskip','1');}catch(e){}",))
            L.boot(pg, url, 1800); pg.wait_for_timeout(1500)
            s = pg.evaluate(STATE)
            chk("(8) %s does not get the computer line" % lab, s["gs"] and not s["gsDevice"], s)
            ctx.close()
        br.close()
finally:
    srv.shutdown()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
