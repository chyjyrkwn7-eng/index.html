#!/usr/bin/env python3
"""Build 384.85: UNDER AN OPAQUE ("default") STATUS BAR THE BAR IS THE COLOUR OF THE TOP OF THE SCREEN; THE TRANSLUCENT INSTALL IS AS IT WAS.

Madison's test icon (added from ?sbs=default): the system's blur is gone, and the opaque bar is a BROWN band (#271E23-ish) over Get
Started, and over Home after a relaunch, though the strip there was the sky's navy - "we just gotta make the top go with the app now".
(docs/notes-archive.md "384.85".) Default mode is simulated: an installed iPhone 17 Pro Max whose page is the screen less the 62pt bar
(440x894, screen 440x956, insets 0/34) and an iPad Pro 11" (834x1170, screen 834x1194, 0/20); 100vh/100lvh modelled as the SCREEN's
height (WebKit 316008: they are wrong without the translucent style), which is the case that makes a screen that fits scroll.
 (A) STATIC   the HTML's theme-color and the manifest's theme_color agree, and are the launch's black (#0A0A0A), not #271E23;
 (B) DETECT   html.sb-default from ?sbs=default; and from the geometry alone (no ?sbs, no stored flag: no top inset, a window shorter
              than the screen), stored for the next launch; never in a translucent install (inset 59 / 24, the whole screen);
 (C) SPLASH   while the splash is up: strip == theme-color == <html>'s colour == the splash's #0A0A0A; the word centred in what shows
              (the page's viewport) at its reveal and still there 1.2s later;
 (D) SCREENS  on every screen (Get Started, Welcome, sign-up and sign-in steps, Home, Profile, badges, Leaderboard, Calendar,
              Settings, test setup, a question, Pause, the chat, the install guide, the save-code card, the code viewer, a rank
              cutscene, the badge cutscene): ONE colour - the strip's inline background-colour == theme-color (settled) == <html>'s
              background-colour - and it is the page's: the row just under the strip within 3 levels; on a solid surface the row
              60px down within 3 too (on the sky the bar is the sky's top-colour model; Chromium paints the sky a few levels off it,
              CLAUDE.md "do not re-sample in Chromium", so 12 there); Get Started is #05060D, never #271E23;
 (E) SAME TASK the strip and the tag change in the task that mounts the screen (read after a microtask, no frame in between);
 (F) LAYOUT   the strip is a real fixed element 12px+ tall at y 0, full width, pointer-events none, solid inline colour; Home and
              Get Started fit (no scroll) with 100lvh = the screen; the header, Pause, the chat and back buttons sit on the page's
              own top floor under the bar (a browser tab's spacing: at least 12px, never the translucent inset added again) and
              Pause and the chat button as they were to each other;
 (G) TRANSLUCENT UNCHANGED  (440x956 59/34, 834x1194 24/20) no html.sb-default, the strip's colour, height and theme-color on each
              screen equal to the previous build's (--base, default origin/main), the top 120px of Profile, Settings and a question
              pixel-equal to it;
 (H) OJAPP    translucent: after the splash an invisible cover (1% white, z 2147483646) and a panel (z 2147483647) are added, take no
              touch, move nothing, and are gone within 1.5s; the display test lists "ojapp", and with it (class26e.ojappoff) and under
              html.sb-default none is made;
 (I) no page errors.
Run:  python3 tools/check-b384-sbdefault.py [--against FILE] [--base FILE]   (main 384.82 must FAIL (A)-(F), (H))"""
import os, sys, re, json, base64, subprocess, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
from PIL import Image
args = sys.argv[1:]
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
if "--base" in args: BASE = open(args[args.index("--base") + 1], encoding="utf-8").read()
else: BASE = subprocess.run(["git", "-C", os.path.dirname(HERE), "show", "origin/main:index.html"], capture_output=True, text=True).stdout
SHOTS = os.environ.get("SHOTS", "")
TMP = os.environ.get("TMPDIR", "/tmp")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');")
# name, page W, page H (default mode), bar, inset bottom, translucent inset top, UA
DEVS = [("promax", 440, 894, 62, 34, 59, UA), ("ipad11", 834, 1170, 24, 20, 24, UA_PAD)]
errs = []
OJLOG = """(()=>{ window.__oj = []; const go = () => { if(!document.body) return false; new MutationObserver(ms => { for(const m of ms) for(const n of m.addedNodes) if(n.id === 'oj-cover' || n.id === 'oj-panel'){
  const cs = getComputedStyle(n); window.__oj.push({ id: n.id, t: performance.now(), pe: cs.pointerEvents, z: cs.zIndex, bg: cs.backgroundColor, pos: cs.position }); }
  for(const m of ms) for(const n of m.removedNodes) if(n.id === 'oj-cover' || n.id === 'oj-panel') window.__oj.push({ id: n.id, gone: performance.now() }); }).observe(document.body, { childList: true }); return true; };
  if(!go()) document.addEventListener('DOMContentLoaded', go); })();"""
def boot(br, raw, dev, mode, used=True, sbs=True, extra=""):
    name, W, H, bar, bot, tins, ua = dev
    if mode == "default": ins = {"top": "0px", "bottom": "%dpx" % bot, "left": "0px", "right": "0px"}; vh = H; sh = H + bar
    else: ins = {"top": "%dpx" % tins, "bottom": "%dpx" % bot, "left": "0px", "right": "0px"}; vh = H + bar; sh = H + bar
    body = cb.INSET_RE.sub(lambda m: ins[m.group(1)], raw).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
    if mode == "default": body = body.replace("100lvh", "calc(100dvh + %dpx)" % bar).replace("100vh", "calc(100dvh + %dpx)" % bar)
    b = re.search(r'const APP_BUILD = "([^"]+)"', raw).group(1)
    ctx = br.new_context(viewport={"width": W, "height": vh}, screen={"width": W, "height": sh}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    if used: ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');}catch(e){}" % (SEEN, cb.USED_ACCOUNT))
    if extra: ctx.add_init_script("try{%s}catch(e){}" % extra)
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(OJLOG)
    pg = ctx.new_page()
    pg.route("**/index.html*", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
    pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % b))
    pg.on("pageerror", lambda e: errs.append(name + " " + mode + ": " + str(e)[:160]))
    pg.goto(cb.URL + ("?sbs=default" if (mode == "default" and sbs) else ""))
    return ctx, pg
def settle(pg, used):
    pg.wait_for_timeout(2600)
    if used: pg.evaluate("()=>{ try{ store.savedCodeSaved = true; }catch(e){} document.getElementById('splashscreen')?.remove(); __stub(); }")
    pg.wait_for_timeout(1500)
QSTART = """()=>{ showHome(); const u = 'Identity Crimes'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false; theme.reduceMotion=true;
  beginRun(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u), null); }"""
CLEAR = "()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.update-banner,.daily-alert,.savecode-card,.installguide-overlay,.invite-overlay').forEach(n=>n.remove()); try{ ifcCloseViewer(); }catch(e){} try{ closeChatDock(); }catch(e){} }"
FRESH = [("Get Started", None, "solid"), ("Welcome", "()=>showWelcome()", "sky"), ("intro", "()=>{showWelcome(); showWelcomeIntro();}", "sky"),
         ("username", "()=>{showWelcome(); showWelcomeNamePrompt();}", "sky"), ("character", "()=>{showWelcome(); showWelcomeCharacterPrompt();}", "sky"),
         ("class pick", "()=>{showWelcome(); showClassSelection();}", "sky"), ("sign in", "()=>{showWelcome(); showWelcomeCodeEntry();}", "sky"),
         ("your code", "()=>{showWelcome(); showWelcomeCodeReveal();}", "sky")]
USED = [("Home", "()=>showHome()", "sky"), ("Profile", "()=>showProfile()", "sky"), ("badges", "()=>showProfile('badges')", "sky"), ("Leaderboard", "()=>showRankings()", "sky"),
        ("Calendar", "()=>showCalendar()", "sky"), ("Settings", "()=>showAppearance()", "sky"), ("test setup", "()=>showSetup()", "sky"), ("a question", QSTART, "header"),
        ("Pause", "()=>pauseRun()", "sky"), ("Home again", "()=>{ showHome(); }", "sky"), ("the chat", "()=>openChatDock()", "sky"),
        ("install guide", "()=>{ try{ closeChatDock(); }catch(e){} showHome(); showInstallGuide('ios'); }", "dim"), ("save-code card", "()=>{ document.querySelectorAll('.installguide-overlay').forEach(n=>n.remove()); showHome(); showSaveCodeCard(); }", "dim"),
        ("code viewer", "()=>{ document.querySelectorAll('.savecode-card').forEach(n=>n.remove()); showHome(); ifcOpenViewer({ title: 'Section 101', sub: 'Scope' }); }", "solid"),
        ("rank cutscene", "()=>{ try{ ifcCloseViewer(); }catch(e){} showHome(); playTierCutscene('vanguard'); }", "solid"),
        ("badge cutscene", "()=>{ document.querySelectorAll('#supernova-cutscene,.tier-cutscene').forEach(n=>n.remove()); showHome(); playBadgeCaseScene(['Identity Crimes'], ()=>{}); }", "solid")]
READ = """()=>{ const e = document.getElementById('top-edge'), m = document.getElementById('themecolor'), r = e ? e.getBoundingClientRect() : null, cs = e ? getComputedStyle(e) : null;
  return { strip: cs ? cs.backgroundColor : null, inl: e ? e.style.backgroundColor : null, h: r ? r.height : 0, top: r ? r.top : 99, w: r ? r.width : 0, pos: cs ? cs.position : null, pe: cs ? cs.pointerEvents : null,
    disp: cs ? cs.display : null, bi: cs ? cs.backgroundImage : null, tc: m ? m.getAttribute('content') : null, html: document.documentElement.style.backgroundColor,
    sbd: document.documentElement.classList.contains('sb-default'), sh: document.documentElement.scrollHeight, ih: innerHeight, iw: innerWidth }; }"""
RECTS = """()=>{ const R = s => { const e = document.querySelector(s); if(!e) return null; const r = e.getBoundingClientRect(); return r.width ? Math.round(r.top * 10) / 10 : null; };
  return { header: R('.wrap > .top'), pause: R('#pausebtn'), chat: R('#chatdock-btn'), back: R('#stage .settings-nav-back') || R('#stage .ios-nav > .back-link.ios-nav-back'), title: R('#stage h1, #stage .screen-title') }; }"""
def rgb(s):
    if not s: return None
    s = s.strip()
    if s.startswith("#") and len(s) == 7: return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    m = re.findall(r"[\d.]+", s)
    return tuple(int(round(float(x))) for x in m[:3]) if len(m) >= 3 else None
def diff(a, b): return max(abs(p - q) for p, q in zip(a, b)) if a and b else 999
def rows(pg, W, ys, tag):
    f = os.path.join(SHOTS or TMP, "sbd-%s.png" % re.sub(r"\W+", "_", tag)); pg.screenshot(path=f)
    im = Image.open(f).convert("RGB"); w = im.size[0]; d = w / W; out = {}
    for y in ys:
        px = sorted(im.getpixel((x, int(y * d))) for x in range(int(w * .1), int(w * .9), 5)); out[y] = px[len(px) // 2]
    if not SHOTS: os.remove(f)
    return out
def screens_default(br, dev):
    name, W, H = dev[0], dev[1], dev[2]
    for used, lst in ((False, FRESH), (True, USED)):
        ctx, pg = boot(br, RAW, dev, "default", used=used)
        settle(pg, used)
        for scr, js, kind in lst:
            try:
                if js: pg.evaluate(js)
                if scr == "a question": pg.wait_for_selector(".qpanel .choice", timeout=25000)
                pg.wait_for_timeout(2200)
                pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.update-banner,.daily-alert').forEach(n=>n.remove()); }"); pg.wait_for_timeout(300)
                s = pg.evaluate(READ); rw = rows(pg, W, (13, 60), name + "_default_" + scr)
                st, tc, ht = rgb(s["strip"]), rgb(s["tc"]), rgb(s["html"])
                one = st and st == tc and st == ht and s["inl"]
                # 60px down: a solid surface is still itself; the sky is Chromium's paint of it (a few levels off the hardware model);
                # a question's header is paper to 70% of its height and then fades (on an iPad 60px is in the fade)
                near = diff(rw[13], st) <= 3 and (kind in ("sky", "header") and diff(rw[60], st) <= 12 or kind not in ("sky", "header") and diff(rw[60], st) <= 3)
                extra = ""
                if scr == "Get Started": extra = " (#05060D)"; one = one and s["tc"].lower() == "#05060d"
                chk("%s default %s: the bar's colour is ONE - strip %s, theme-color %s, <html> %s - and the page's top: under the strip %s, 60px down %s%s" % (
                    name, scr, st, s["tc"], ht, rw[13], rw[60], extra), one and near and (st != (39, 30, 35)), s)
                if scr in ("Home", "Get Started"):
                    chk("%s default %s fits: document %d of %d (100lvh = the screen)" % (name, scr, s["sh"], s["ih"]), s["sh"] <= s["ih"], s)
            except Exception as e:
                chk("%s default %s: mounted" % (name, scr), False, str(e)[:300])
        if used:
            # (E) the same task: from Home, Get Started's page and back
            pg.evaluate(CLEAR); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
            r = pg.evaluate("""async ()=>{ const e = document.getElementById('top-edge'), m = document.getElementById('themecolor'); const a = e.style.backgroundColor;
              showGetStarted(); await Promise.resolve(); await Promise.resolve(); const b = { strip: e.style.backgroundColor, tc: m.getAttribute('content'), html: document.documentElement.style.backgroundColor };
              return { a, b }; }""")
            chk("%s default: the strip, the tag and <html> change in the task that mounts the screen (Home -> Get Started: %s -> %s, tag %s)" % (name, r["a"], r["b"]["strip"], r["b"]["tc"]),
                rgb(r["b"]["strip"]) == (5, 6, 13) and (r["b"]["tc"] or "").lower() == "#05060d" and rgb(r["b"]["html"]) == (5, 6, 13), r)
            oj = pg.evaluate("()=>window.__oj")
            chk("%s default: no ojapp cover or panel is ever made under the opaque bar" % name, not oj, oj)
        ctx.close()
def layout(br, dev):
    """(F) the strip, and the top furniture: default rect top == translucent rect top - inset"""
    name, W, H, bar, bot, tins = dev[:6]
    got = {}
    for mode in ("default", "translucent"):
        ctx, pg = boot(br, RAW, dev, mode)
        settle(pg, True)
        if mode == "default":
            s = pg.evaluate(READ)
            chk("%s default: the strip is a real fixed element at y 0, full width, %.0fpx (>= 12), taps through, solid inline colour, no image" % (name, s["h"]),
                s["pos"] == "fixed" and s["top"] == 0 and s["w"] >= W - .5 and s["h"] >= 12 and s["pe"] == "none" and s["inl"] and s["bi"] == "none" and s["disp"] == "block", s)
        for scr, js in (("Home", "()=>showHome()"), ("Profile", "()=>showProfile()"), ("Settings", "()=>showAppearance()"), ("a question", QSTART)):
            pg.evaluate(CLEAR); pg.evaluate(js)
            if scr == "a question": pg.wait_for_selector(".qpanel .choice", timeout=25000)
            pg.wait_for_timeout(1600)
            got[(mode, scr)] = pg.evaluate(RECTS)
        ctx.close()
    for scr in ("Home", "Profile", "Settings", "a question"):
        d, t = got[("default", scr)], got[("translucent", scr)]
        # under the opaque bar the page has no inset: what was on the inset line sits on the page's own floor (.wrap's 1.25rem / 1.5rem,
        # a browser tab's spacing) - never the inset added again, never under the strip, and in the same places relative to each other
        bad = {k: (d[k], t[k]) for k in d if (d[k] is None) != (t[k] is None) or (d[k] is not None and not (11.5 <= d[k] <= t[k] - tins + 24.5))}
        if d["pause"] is not None and d["chat"] is not None and abs((d["pause"] - d["chat"]) - (t["pause"] - t["chat"])) > 1: bad["pause-chat"] = (d["pause"] - d["chat"], t["pause"] - t["chat"])
        chk("%s %s: the header, Pause, chat and back buttons sit under the bar on the page's own floor - clear of the strip, no inset added twice, Pause and chat as they were to each other (default %s, translucent %s, inset %d)" % (name, scr, d, t, tins), not bad, bad)
def detect(br, dev):
    name = dev[0]
    ctx, pg = boot(br, RAW, dev, "default", sbs=False)
    pg.wait_for_timeout(3000)
    s = pg.evaluate("()=>({ c: document.documentElement.classList.contains('sb-default'), f: localStorage.getItem('class26e.sbdefault') })")
    chk("%s: with no ?sbs and nothing stored, the geometry (no inset, the window short of the screen) finds the opaque bar, and stores it" % name, s["c"] and s["f"] == "1", s)
    ctx.close()
    ctx, pg = boot(br, RAW, dev, "translucent")
    pg.wait_for_timeout(3000)
    s = pg.evaluate("()=>({ c: document.documentElement.classList.contains('sb-default'), f: localStorage.getItem('class26e.sbdefault') })")
    chk("%s: a translucent install (inset %d, the whole screen) never takes it" % (name, dev[5]), not s["c"] and s["f"] != "1", s)
    ctx.close()
def splash(br, dev):
    name, W, H = dev[0], dev[1], dev[2]
    ctx, pg = boot(br, RAW, dev, "default", used=True, extra="localStorage.setItem('class26e.synccode','TESTCODE1');")
    seen = []
    for i in range(14):
        pg.wait_for_timeout(150)
        s = pg.evaluate("""()=>{ const sp = document.getElementById('splashscreen'), g = document.getElementById('splash-group'); if(!sp || sp.classList.contains('splash-hide')) return null;
          const e = document.getElementById('top-edge'), m = document.getElementById('themecolor'), r = g ? g.getBoundingClientRect() : null;
          return { strip: e.style.backgroundColor, tc: m.getAttribute('content'), html: getComputedStyle(document.documentElement).backgroundColor, ready: g ? g.classList.contains('splash-ready') : false,
            cy: r ? r.top + r.height / 2 : null, ih: innerHeight }; }""")
        if s: seen.append(s)
    up = [s for s in seen if s["ready"]]
    chk("%s default: under the splash the strip, the tag and <html> are the splash's #0A0A0A (%d readings)" % (name, len(seen)),
        seen and all(rgb(s["strip"]) == (10, 10, 10) and (s["tc"] or "").lower() == "#0a0a0a" and rgb(s["html"]) == (10, 10, 10) for s in seen), seen[:3])
    chk("%s default: the word is centred in what shows (the page's viewport) and does not move (%s)" % (name, [round(s["cy"] - s["ih"] / 2, 1) for s in up]),
        up and all(abs(s["cy"] - s["ih"] / 2) <= 2 for s in up) and max(s["cy"] for s in up) - min(s["cy"] for s in up) <= .5, up[:3])
    ctx.close()
def translucent(br, dev):
    name, W, H, bar = dev[0], dev[1], dev[2], dev[3]
    seq = {}
    for tag, raw in (("this", RAW), ("base", BASE)):
        ctx, pg = boot(br, raw, dev, "translucent", extra="localStorage.setItem('class26e.ojappoff','1');" if tag == "this" else "")
        settle(pg, True); pg.wait_for_timeout(1200)
        out = []
        for scr, js in (("Home", "()=>showHome()"), ("Profile", "()=>showProfile()"), ("Settings", "()=>showAppearance()"), ("a question", QSTART), ("Home again", "()=>showHome()")):
            pg.evaluate(CLEAR); pg.evaluate(js)
            if scr == "a question": pg.wait_for_selector(".qpanel .choice", timeout=25000)
            pg.wait_for_timeout(1900)
            s = pg.evaluate(READ)
            r = rows(pg, W, range(0, 120, 6), name + "_tr_" + tag + "_" + scr) if scr in ("Profile", "Settings", "a question") else None
            out.append((scr, s["strip"], s["h"], s["tc"], s["html"], s["sbd"], r))
        seq[tag] = out
        ctx.close()
    for a, b in zip(seq["this"], seq["base"]):
        same = a[1:6] == b[1:6]
        chk("%s translucent %s: strip %s %dpx, theme-color %s, <html> '%s', no sb-default - as the previous build" % (name, a[0], a[1], a[2], a[3], a[4]), same and not a[5], (a[:6], b[:6]))
        if a[6] is not None:
            d = max(diff(a[6][y], b[6][y]) for y in a[6])
            chk("%s translucent %s: the top 120px are the previous build's (worst %d levels)" % (name, a[0], d), d <= 2, d)
def ojapp(br, dev):
    name, W = dev[0], dev[1]
    ctx, pg = boot(br, RAW, dev, "translucent")
    settle(pg, True)
    before = pg.evaluate(RECTS)
    pg.wait_for_timeout(2600)
    oj = pg.evaluate("()=>window.__oj"); after = pg.evaluate(RECTS)
    made = [o for o in oj if "pe" in o]; gone = {o["id"]: o["gone"] for o in oj if "gone" in o}
    t0 = {o["id"]: o["t"] for o in made}
    good = {o["id"] for o in made} == {"oj-cover", "oj-panel"} and all(o["pe"] == "none" and o["pos"] == "fixed" for o in made) \
        and all(i in gone and gone[i] - t0[i] <= 1500 for i in t0) and not pg.evaluate("()=>!!document.getElementById('oj-cover') || !!document.getElementById('oj-panel')")
    z = {o["id"]: o["z"] for o in made}; bg = {o["id"]: o["bg"] for o in made}
    chk("%s translucent: after the splash the ojapp cover (z %s, %s) and panel (z %s) were made, take no touch, and are gone within 1.5s (%s ms)" % (
        name, z.get("oj-cover"), bg.get("oj-cover"), z.get("oj-panel"), {i: round(gone.get(i, 0) - t0[i]) for i in t0}), good and z.get("oj-cover") == "2147483646" and z.get("oj-panel") == "2147483647"
        and all(re.search(r"0\.01\)$", b) for b in bg.values()), oj)
    chk("%s translucent: nothing on the screen moved while they were up (%s)" % (name, before), before == after, (before, after))
    pg.evaluate("()=>{ document.dispatchEvent(new Event('visibilitychange')); }"); pg.wait_for_timeout(1800)
    n2 = len([o for o in pg.evaluate("()=>window.__oj") if "pe" in o])
    chk("%s translucent: coming back to the screen runs it again (%d made in all)" % (name, n2), n2 >= 4, n2)
    ctx.close()
    ctx, pg = boot(br, RAW, dev, "translucent", extra="localStorage.setItem('class26e.ojappoff','1');")
    settle(pg, True); pg.wait_for_timeout(2600)
    oj = pg.evaluate("()=>window.__oj")
    lst = pg.evaluate("()=>{ try{ return typeof showDisplayTest === 'function' || true; }catch(e){ return false; } }")
    chk("%s translucent with class26e.ojappoff: none made" % name, not oj, oj)
    ctx.close()
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=cb.CHROME)
    # (A)
    m = re.search(r'<meta name="theme-color" id="themecolor" content="([^"]+)">', RAW)
    mf = re.search(r'<link rel="manifest" href="data:application/manifest\+json;base64,([^"]+)"', RAW)
    man = json.loads(base64.b64decode(mf.group(1)).decode()) if mf else {}
    chk("the HTML's theme-color (%s) and the manifest's theme_color (%s) agree and are the launch's black" % (m and m.group(1), man.get("theme_color")),
        m and man.get("theme_color") and m.group(1).lower() == man["theme_color"].lower() == "#0a0a0a")
    chk("the display test lists the ojapp switch (class26e.ojappoff)", 'flagTrial("ojapp"' in RAW and "class26e.ojappoff" in RAW)
    for dev in DEVS:
        detect(br, dev)
        splash(br, dev)
        screens_default(br, dev)
        layout(br, dev)
        translucent(br, dev)
        ojapp(br, dev)
    chk("no page errors", not errs, errs[:6])
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
