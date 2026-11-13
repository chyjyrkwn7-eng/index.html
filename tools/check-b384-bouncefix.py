#!/usr/bin/env python3
"""Build 384.80: THE INSTALLED APP DOES NOT BOUNCE, AND THE PAGE BEHIND A CARD IS LOCKED.

Madison (iPhone 17 Pro Max, installed, 384.77, a 17s recording): "when swiping down, the bottom tab breaks. Secondly, when on the pause
menu, it starts moving when swiping too?" The frames: on a Fire Code question the pull dragged the page and the pinned header area; with
the Pause card up the card rode up and down with the page (a scroll indicator on the right); on Home the pull rubber-banded the planet
system and the tab bar dropped off the foot and came back broken (docs/notes-archive.md "384.80").
Installed iPhone 17 Pro Max (440x956, 59/34 simulated) and iPad Pro 11" (834x1194, 24/20):
 (1) BOUNCE   the root's overscroll-behavior-y is none in the installed app (and still none in a Safari tab, as since 327z);
 (2) HOME     Home's document is no taller than the screen (nothing to scroll, nothing to drag), and a wheel and a touch drag leave it at 0;
 (3) TAB BAR  on Home and on a scrolled Profile the tab bar's rect does not change through a wheel and a touch drag (0.5px);
 (4) PAUSE    on a question scrolled to 200, Pause: html.page-locked, html and body overflow hidden; a wheel and a touch drag on the card
              and beside it leave scrollY and the card's rect as they were (0.5px); Resume gives the question back at scrollY 200 exactly,
              unlocked, and a wheel scrolls it again;
 (5) QUIT     Quit test's confirmation (the same card): locked, still through a wheel and a drag; Keep going brings Pause back, locked;
 (6) OVERLAY  a full-screen overlay on <body> over a scrolled Profile (the install guide): locked, scrollY and the overlay's card still
              through a wheel and a drag; closed, unlocked and scrollY exactly where it was;
 (7) SIDEWAYS an iPhone on its side (956x440): a Pause card that does not fit leaves the page scrollable (no lock), one that fits locks;
 (8) no page errors;
 (9) THE TOP STRIP (Safari 26 / iOS 26 tinting; r/PWA's production fix for the top blur): on Home, a question, Profile, Settings, the
     Leaderboard and Home again there is exactly ONE real element WebKit can sample (fixed/sticky, shown, within 4px of the top, over 4px tall,
     >= 80% wide): #top-edge - fixed, full width, at least max(inset, 6px) tall, pointer-events none, an inline OPAQUE background-colour and
     no background-image, the colour of the screen's top (the sky's top colour; the paper under a question's header) and theme-color's;
     where that colour changes (onto a question, back to Home) theme-color was danced c, c + "fe", c; z 2147483647 (the r/PWA element);
 (10) CLIP    the display test lists "clip" (class26e.topclip): the strip 11px with background-clip:text, its colour still set and opaque.
Run:  python3 tools/check-b384-bouncefix.py [--against FILE]   (main 384.77 must FAIL (1), (4), (5), (6), (9))"""
import os, sys, re, time, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
args = sys.argv[1:]
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');")
DEVICES = [("promax", 440, 956, 59, 34, UA), ("ipad11", 834, 1194, 24, 20, UA_PAD)]
QSTART = """()=>{ showHome(); const u = 'Arrest, Search, and Seizure'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false; theme.reduceMotion=true;
  beginRun(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u), null); }"""
# a question page given a length that outlives render() (Resume rebuilds the question)
LONG = "()=>{ const s = document.createElement('style'); s.id = 'gate-long'; s.textContent = '#stage > .qpanel{ padding-bottom:1400px !important; }'; document.body.appendChild(s); }"
RECT = """(sel)=>{ const e = document.querySelector(sel); if(!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom].map(v => Math.round(v * 100) / 100); }"""
STATE = """()=>{ const de = document.documentElement; return { y: scrollY, sh: de.scrollHeight, ih: innerHeight, locked: de.classList.contains('page-locked'),
  ho: getComputedStyle(de).overflowY, bo: getComputedStyle(document.body).overflowY, ob: getComputedStyle(de).overscrollBehaviorY }; }"""
# every value theme-color's content takes, from the first byte
TAGLOG = """(()=>{ window.__tc = []; const hook = () => { const m = document.getElementById('themecolor'); if(!m){ return false; } window.__tc.push(m.getAttribute('content'));
  new MutationObserver(() => window.__tc.push(m.getAttribute('content'))).observe(m, { attributes: true, attributeFilter: ['content'] }); return true; };
  if(!hook()) document.addEventListener('readystatechange', function f(){ if(hook()) document.removeEventListener('readystatechange', f); }); })();"""
# what WebKit samples for the tint: every REAL element that is fixed or sticky, shown, within 4px of the top, over 4px tall and at least
# 80% of the width (pointer-events:none elements included, so not elementFromPoint); the screen's own top colour to compare it with
SAMPLE = """()=>{ const W = innerWidth, out = [];
  for(const e of document.body.querySelectorAll('*')){ const r = e.getBoundingClientRect(); if(r.top > 4 || r.height <= 4 || r.width < .8 * W || r.bottom <= 0) continue;
    const cs = getComputedStyle(e); if(!/^(fixed|sticky)$/.test(cs.position) || cs.display === 'none') continue;
    out.push({ id: e.id || (e.tagName + '.' + String(e.className).slice(0, 30)), pos: cs.position, w: r.width, h: r.height, top: r.top, bg: cs.backgroundColor, bi: cs.backgroundImage, inl: e.style.backgroundColor, pe: cs.pointerEvents, z: cs.zIndex }); }
  const m = document.getElementById('themecolor'), tc = m ? m.getAttribute('content') : null;
  const rgb = c => { const p = document.createElement('i'); p.style.color = c; document.body.appendChild(p); const v = getComputedStyle(p).color; p.remove(); return v; };
  const pinned = !!document.querySelector('.wrap.test-pinned');
  return { c: out, tc: tc, tcRgb: tc ? rgb(tc) : null, want: rgb(pinned ? 'var(--paper)' : appTopEdgeColor()), pinned: pinned, vw: W }; }"""
def opaque(c): return c.startswith("rgb(") or (c.startswith("rgba(") and c.rstrip(")").split(",")[-1].strip() in ("1", "1.0"))
errs = []
def boot(br, raw, dev, standalone=True, extra=""):
    name, W, H, top, bottom, ua = dev
    ins = {"top": "%dpx" % top, "bottom": "%dpx" % bottom, "left": "0px", "right": "0px"}
    m = re.search(r'const APP_BUILD = "([^"]+)"', raw); cb.SERVED_BUILD = m.group(1)
    cb.BODY = cb.INSET_RE.sub(lambda m: ins[m.group(1)], raw).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');%s}catch(e){}" % (SEEN, cb.USED_ACCOUNT, extra))
    if standalone: ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(TAGLOG)
    pg = cb.open_page(ctx)
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(cb.URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); __stub(); }"); pg.wait_for_timeout(1500)
    return ctx, pg, ctx.new_cdp_session(pg)
def tidy(pg):
    pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot,.update-banner,.daily-alert').forEach(n=>n.remove()); }")
def attempts(pg, cdp, W, H, xs=None):
    """A wheel each way and a touch drag each way, at the middle and beside it; what the page did after each."""
    seen = []
    for x in (xs or (W / 2, 14)):
        for dy in (500, -500):
            pg.mouse.move(x, H / 2); pg.mouse.wheel(0, dy); pg.wait_for_timeout(260); seen.append(("wheel", x, dy))
        for dy in (-320, 320):
            cb._swipe(cdp, x, H / 2, 0, dy, steps=10); pg.wait_for_timeout(320); seen.append(("drag", x, dy))
    return seen
def still(pg, cdp, W, H, sel, label, xs=None):
    a, ra = pg.evaluate(STATE), pg.evaluate(RECT, sel)
    worst_y, worst_r = 0, 0
    for x in (xs or (W / 2, 14)):
        for kind in ("wheel+", "wheel-", "drag-", "drag+"):
            if kind.startswith("wheel"):
                pg.mouse.move(x, H / 2); pg.mouse.wheel(0, 500 if kind.endswith("+") else -500); pg.wait_for_timeout(260)
            else:
                cb._swipe(cdp, x, H / 2, 0, -320 if kind.endswith("-") else 320, steps=10); pg.wait_for_timeout(320)
            b, rb = pg.evaluate(STATE), pg.evaluate(RECT, sel)
            worst_y = max(worst_y, abs(b["y"] - a["y"]))
            if ra and rb: worst_r = max(worst_r, max(abs(p - q) for p, q in zip(ra, rb)))
            elif ra or rb: worst_r = 999
    return a, worst_y, worst_r
def run(br):
    for dev in DEVICES:
        name, W, H = dev[0], dev[1], dev[2]
        ctx, pg, cdp = boot(br, RAW, dev)
        # (1) the root
        s = pg.evaluate(STATE)
        chk("%s installed: the root does not bounce (overscroll-behavior-y %s)" % (name, s["ob"]), s["ob"] == "none", s)
        # (9) THE TINT: the sampled element at the top edge on five screens, and the fe dance
        for scr, js in (("Home", "()=>showHome()"), ("a question", QSTART), ("Profile", "()=>showProfile()"), ("Settings", "()=>showAppearance()"), ("Leaderboard", "()=>showRankings()"), ("Home again", "()=>showHome()")):
            n0 = pg.evaluate("()=>window.__tc.length")
            pg.evaluate(js)
            if scr == "a question": pg.wait_for_selector(".qpanel .choice", timeout=25000)
            pg.wait_for_timeout(1700); tidy(pg)
            s = pg.evaluate(SAMPLE); c = s["c"]; e = c[0] if len(c) == 1 else None; inset = dev[3]
            good = e and e["id"] == "top-edge" and e["pos"] == "fixed" and e["w"] >= .8 * s["vw"] and e["h"] >= max(inset, 6) - .5 and e["top"] <= 4 and opaque(e["bg"]) and e["bi"] == "none" and e["inl"] \
                and e["pe"] == "none" and str(e["z"]) == "2147483647" and e["bg"] == s["want"] and e["bg"] == s["tcRgb"]
            chk("%s %s: ONE sampled element at the top - #top-edge, fixed, full width, %.0fpx (inset %d), solid %s, no image, taps through - the screen's top colour %s%s, and theme-color's (%s)" % (
                name, scr, (e or {}).get("h", 0), inset, (e or {}).get("bg"), s["want"], " (paper, under the header)" if s["pinned"] else " (the sky's)", s["tc"]), good, s)
            seq = pg.evaluate("(n)=>window.__tc.slice(n)", n0)
            if scr in ("a question", "Home again"):   # the colour changes here (paper under a question's header; the sky back on Home)
                c = s["tc"]
                danced = bool(c) and any(seq[i:i + 3] == [c, c + "fe", c] for i in range(len(seq) - 2))
                chk("%s %s: theme-color danced to the new colour (c, c+'fe', c): %s" % (name, scr, seq[-4:]), danced and seq[-1] == c, seq)
        # (2) Home, (3) the tab bar
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500); tidy(pg)
        s = pg.evaluate(STATE)
        chk("%s Home: the document is no taller than the screen (%d of %d)" % (name, s["sh"], s["ih"]), s["sh"] <= s["ih"], s)
        a, wy, wr = still(pg, cdp, W, H, ".bottomtabs", "home")
        chk("%s Home: a wheel and a touch drag leave it at the top (moved %.1f) and the tab bar where it was (%.2f px)" % (name, wy, wr), wy == 0 and a["y"] == 0 and wr <= .5, [a, wy, wr])
        pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500); tidy(pg)
        pg.evaluate("()=>window.scrollTo({top:300, behavior:'instant'})"); pg.wait_for_timeout(400)
        r0 = pg.evaluate(RECT, ".bottomtabs"); attempts(pg, cdp, W, H); pg.wait_for_timeout(900); r1 = pg.evaluate(RECT, ".bottomtabs")
        d = max(abs(p - q) for p, q in zip(r0, r1)) if r0 and r1 else 999
        chk("%s Profile: the tab bar's rect does not change through scrolling (%.2f px)" % (name, d), d <= .5, [r0, r1])
        # (6) a full-screen overlay on <body> over the scrolled Profile
        pg.evaluate("()=>window.scrollTo({top:300, behavior:'instant'})"); pg.wait_for_timeout(400)
        y0 = pg.evaluate("()=>scrollY")
        pg.evaluate("()=>showInstallGuide('ios')"); pg.wait_for_timeout(900)
        s = pg.evaluate(STATE)
        chk("%s install guide over the Profile: the page is locked (%s, html %s, body %s)" % (name, s["locked"], s["ho"], s["bo"]), s["locked"] and s["ho"] == "hidden" and s["bo"] == "hidden", s)
        a, wy, wr = still(pg, cdp, W, H, ".installguide-card", "guide", xs=(14,))
        chk("%s install guide: the page behind it and its card stay still through a wheel and a drag (page %.1f, card %.2f px)" % (name, wy, wr), wy == 0 and wr <= .5, [a, wy, wr])
        pg.evaluate("()=>{ const b = [...document.querySelectorAll('.installguide-overlay button')].pop(); b && b.click(); }"); pg.wait_for_timeout(700)
        s = pg.evaluate(STATE)
        chk("%s install guide closed: unlocked and the Profile where it was (%s of %s)" % (name, s["y"], y0), not s["locked"] and s["y"] == y0, s)
        # (4) Pause over a scrolled question
        pg.evaluate(QSTART); pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(1500); tidy(pg)
        pg.evaluate(LONG); pg.wait_for_timeout(200)
        pg.evaluate("()=>window.scrollTo({top:200, behavior:'instant'})"); pg.wait_for_timeout(500)
        yq = pg.evaluate("()=>scrollY")
        pg.evaluate("()=>pauseRun()"); pg.wait_for_timeout(1100)
        s = pg.evaluate(STATE)
        chk("%s Pause: the page behind the card is locked (%s, html %s, body %s; document %d of %d)" % (name, s["locked"], s["ho"], s["bo"], s["sh"], s["ih"]), s["locked"] and s["ho"] == "hidden" and s["bo"] == "hidden", s)
        a, wy, wr = still(pg, cdp, W, H, ".pause-stack", "pause")
        chk("%s Pause: a wheel and a touch drag on the card and beside it move neither the page (%.1f) nor the card (%.2f px)" % (name, wy, wr), wy == 0 and wr <= .5, [a, wy, wr])
        # (5) Quit's confirmation, then Keep going
        pg.evaluate("()=>document.getElementById('pause-quit').click()"); pg.wait_for_timeout(1100)
        s = pg.evaluate(STATE)
        a, wy, wr = still(pg, cdp, W, H, ".pause-stack", "quit")
        chk("%s Quit test's confirmation: locked (%s) and still through a wheel and a drag (page %.1f, card %.2f px)" % (name, s["locked"], wy, wr), s["locked"] and wy == 0 and wr <= .5, [s, wy, wr])
        pg.evaluate("()=>{ const b = [...document.querySelectorAll('#stage .pausepanel .actions button')][0]; b && b.click(); }"); pg.wait_for_timeout(1100)
        s = pg.evaluate(STATE); back = pg.evaluate("()=>!!document.getElementById('resumebtn')")
        chk("%s Keep going: Pause again, locked (%s, %s)" % (name, back, s["locked"]), back and s["locked"], s)
        pg.evaluate("()=>document.getElementById('resumebtn').click()"); pg.wait_for_timeout(1200)
        s = pg.evaluate(STATE)
        chk("%s Resume: the question back at scrollY %s exactly (%s), unlocked" % (name, yq, s["y"]), not s["locked"] and s["y"] == yq and s["ho"] != "hidden", s)
        pg.mouse.move(W / 2, H / 2); pg.mouse.wheel(0, 300); pg.wait_for_timeout(700)
        s2 = pg.evaluate(STATE)
        chk("%s Resume: the question scrolls again (%s -> %s)" % (name, s["y"], s2["y"]), s2["y"] > s["y"], [s, s2])
        ctx.close()
    # (1) a Safari tab: unchanged (none since 327z)
    ctx, pg, cdp = boot(br, RAW, DEVICES[0], standalone=False)
    s = pg.evaluate(STATE)
    chk("Safari tab: the root's overscroll-behavior-y is none as before (%s)" % s["ob"], s["ob"] == "none" and "is-browser" in pg.evaluate("()=>document.documentElement.className"), s)
    ctx.close()
    # (10) the display test's "clip": the strip 11px, background-clip:text (paints nothing), its background-colour still set and opaque
    ctx, pg, cdp = boot(br, RAW, DEVICES[0], extra="localStorage.setItem('class26e.topclip','1');")
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500)
    k = pg.evaluate("""()=>{ const e = document.getElementById('top-edge'); const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      return { cls: document.documentElement.classList.contains('top-clip'), h: r.height, clip: cs.webkitBackgroundClip || cs.backgroundClip, bg: cs.backgroundColor }; }""")
    chk("clip: the strip is 11px, background-clip:text, its colour still set and opaque (%s)" % k, k["cls"] and abs(k["h"] - 11) < .5 and k["clip"] == "text" and opaque(k["bg"]), k)
    ctx.close()
    ctx, pg, cdp = boot(br, RAW, DEVICES[0], extra="localStorage.setItem('class26e.displaytest','1');")
    listed = pg.evaluate("()=>{ const T = window.__diagTrials; return !!(T && T.byId && T.byId.clip); }")
    chk("clip: the display test lists it (%s)" % listed, listed, listed)
    ctx.close()
    # (7) on its side
    dev = ("promax-land", 956, 440, 0, 21, UA)
    ctx, pg, cdp = boot(br, RAW, dev)
    pg.evaluate(QSTART); pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(1500); tidy(pg)
    pg.evaluate("()=>pauseRun()"); pg.wait_for_timeout(1100)
    r = pg.evaluate(RECT, ".pause-stack"); s = pg.evaluate(STATE)
    fits = r and r[1] >= -1 and r[3] <= 441
    chk("on its side: a card that %s the screen %s the page (card %s, locked %s)" % ("fits" if fits else "does not fit", "locks" if fits else "leaves scrollable", r, s["locked"]), s["locked"] == bool(fits), [r, s])
    ctx.close()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    try: run(br)
    finally: br.close()
chk("no page errors (%d)" % len(errs), not errs, errs[:4])
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
