#!/usr/bin/env python3
"""Build 384.77: THE TOP OF THE SCREEN AND SCROLLING AS BUILD 383 HAD THEM, with an opaque strip in the status bar's area on top.

Madison (iPhone 17 Pro Max, installed): "this was working so perfectly a week ago, the rubber banding was great, the top was great ... I don't
want to lose how great we had it." Build 383 (42bbffa) was live 11-03 to 11-09. This gate holds the build against 383 ITSELF (read out of
git), on the same screens, in Chromium (docs/notes-archive.md "384.77"):
 (1) SAME PLACE  installed iPhone 17 Pro Max (440x956, 59/34 simulated) and iPad Pro 11" (834x1194, 24/20): the test header row, Pause, the chat
                 button and the round back button (Settings) sit on the same rect as 383's on Home, a Drill question scrolled 0/120/400, the
                 Profile, Settings and the Leaderboard (1px); --sat is the raw inset;
 (2) STILL       with the visual viewport reading offset by the scroll (what 384.62's heal read on his phone mid-scroll) the header, Pause and
                 the chat button do not move (as on 383, which had no follower);
 (3) BOUNCE      (384.80, changed on purpose: the owner's "when swiping down, the bottom tab breaks") the root does NOT bounce in the
                 installed app (overscroll-behavior-y none; 383 had the rubber band);
 (4) BUTTONS     (384.78, CHANGED ON PURPOSE: the owner on 384.77, "all it did was change the color of the chat button, and now the chat
                 button doesn't match") the chat button on every screen, Pause and the round back buttons wear ONE look, 384.70/384.76's
                 unblurred glass (384 r17): no backdrop blur, and the same background, border and shadow everywhere. 384.77 (383's flat disc
                 beyond Home, 384.1's blurred glass on Home and Pause) must FAIL this;
 (5) STRIP       (384.80) ONE strip, #top-edge, over the whole safe area (6px where there is none), in the markup ahead of every script in
                 <body>, one solid opaque colour, no image, taps going through; no #top-safe; a Profile scrolled 300 shows the same status-bar
                 area as at rest; theme-color and color-scheme are not written after launch;
 (6) VARIANTS    the display test lists A (class26e.topmatch), B (topdeep), C (top383); C takes both strips away and rewrites the tags as 383;
 (7) no page errors.
Run:  python3 tools/check-b384-top383.py [--against FILE]   (main 384.70 must FAIL (1), (2), (6); main 384.77 must FAIL (4))"""
import os, sys, io, re, subprocess, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
args = sys.argv[1:]
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
REF = subprocess.run(["git", "-C", os.path.dirname(HERE), "show", "42bbffa:index.html"], capture_output=True, text=True).stdout
assert 'APP_BUILD = "2026-11-03-383"' in REF, "build 383 not readable from git"
from playwright.sync_api import sync_playwright
from PIL import Image
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');")
VVM = "window.__vvm = {follow: false}; try{ const d = Object.getOwnPropertyDescriptor(VisualViewport.prototype, 'offsetTop'); Object.defineProperty(window.visualViewport, 'offsetTop', { get(){ return window.__vvm.follow ? Math.min(500, Math.round(window.scrollY)) : d.get.call(this); }, configurable: true }); }catch(e){}"
WATCH = """(()=>{ window.__tw = { tags: 0 }; addEventListener('load', () => setTimeout(() => {
    const mo = new MutationObserver(ms => { for(const m of ms) if(m.type === 'attributes'){ if(m.target.id === 'colorscheme') window.__tw.cs = (window.__tw.cs || 0) + 1; else window.__tw.tags++; } });
    ['themecolor', 'colorscheme'].forEach(id => { const e = document.getElementById(id); if(e) mo.observe(e, { attributes: true, attributeFilter: ['content'] }); });
    window.__tw.tc0 = (document.getElementById('themecolor') || {}).content; }, 4200)); })();"""
DEVICES = [("promax", 440, 956, 59, 34, UA), ("ipad11", 834, 1194, 24, 20, UA_PAD)]
QSTART = """()=>{ showHome(); const u = 'Arrest, Search, and Seizure'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false; theme.reduceMotion=true;
  beginRun(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u), null); }"""
READ = """()=>{ const R = s => { const e = document.querySelector(s); if(!e) return null; const cs = getComputedStyle(e); if(cs.display === 'none' || cs.visibility === 'hidden') return null; const r = e.getBoundingClientRect(); if(!r.width) return null;
    return { r: [r.left, r.top, r.right, r.bottom].map(v => Math.round(v * 10) / 10), bf: cs.backdropFilter, bg: cs.backgroundColor, bi: cs.backgroundImage.slice(0, 40), bc: cs.borderTopColor, sh: cs.boxShadow }; };
  const h = document.elementFromPoint(innerWidth / 2, 4);
  return { y: Math.round(scrollY), header: R('.wrap > .top'), pause: R('#pausebtn'), chat: R('#chatdock-btn'), back: R('#stage .settings-nav-back') || R('#stage .ios-nav > .back-link.ios-nav-back'),
    edge: R('#top-edge'), safe: R('#top-safe'), at4: h ? (h.id || h.tagName) : null, ob: getComputedStyle(document.documentElement).overscrollBehaviorY, cls: document.documentElement.className,
    sat: (() => { const q = document.createElement('i'); q.style.cssText = 'position:fixed;top:0;width:0;height:var(--sat, env(safe-area-inset-top, 0px))'; document.body.appendChild(q); const x = q.getBoundingClientRect().height; q.remove(); return x; })(),
    tw: window.__tw, tc: (document.getElementById('themecolor') || {}).content, pe: (() => { const e = document.getElementById('top-edge'); return e ? getComputedStyle(e).pointerEvents : null; })(),
    ebi: (() => { const e = document.getElementById('top-edge'); return e ? getComputedStyle(e).backgroundImage : null; })() }; }"""
SCREENS = [("home", "()=>showHome()", [0]), ("question", QSTART, [0, 120, 400]), ("profile", "()=>showProfile()", [0, 300]), ("settings", "()=>showAppearance()", [0, 300]), ("leaderboard", "()=>showRankings()", [0])]
errs = []
def boot(br, raw, dev, extra=""):
    name, W, H, top, bottom, ua = dev
    ins = {"top": "%dpx" % top, "bottom": "%dpx" % bottom, "left": "0px", "right": "0px"}
    m = re.search(r'const APP_BUILD = "([^"]+)"', raw); cb.SERVED_BUILD = m.group(1)
    cb.BODY = cb.INSET_RE.sub(lambda m: ins[m.group(1)], raw).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');%s}catch(e){}" % (SEEN, cb.USED_ACCOUNT, extra))
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(VVM); ctx.add_init_script(WATCH)
    pg = cb.open_page(ctx)
    pg.goto(cb.URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); pg.wait_for_timeout(1500)
    return ctx, pg
def walk(br, raw, dev, mine):
    ctx, pg = boot(br, raw, dev)
    if mine: pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    out = {}
    for scr, js, ys in SCREENS:
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500); pg.evaluate(js)
        if scr == "question": pg.wait_for_selector(".qpanel .choice", timeout=25000)
        pg.wait_for_timeout(1700)
        pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot').forEach(n=>n.remove()); const d = document.createElement('div'); d.style.cssText = 'height:1400px;pointer-events:none'; (document.querySelector('#stage .qpanel') || document.getElementById('stage')).appendChild(d); }")
        pg.wait_for_timeout(300)
        for y in ys:
            pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(450)
            out[(scr, y)] = pg.evaluate(READ)
            if mine and scr == "profile":
                # the status bar's area scrolled must be what it is at rest: nothing of the page runs up under the clock
                im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB"); top = dev[3]
                if y == 0: out["strip0"] = im
                else:
                    im0 = out.pop("strip0")
                    bad = [(x // 2, yy // 2) for yy in range(0, top * 2 - 1, 3) for x in range(4, im.width - 4, 6) if max(abs(a - b) for a, b in zip(im.getpixel((x, yy))[:3], im0.getpixel((x, yy))[:3])) > 3]
                    out["strip_px"] = (len(bad), bad[:5])
        if scr == "question":
            pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(400)
            a = pg.evaluate(READ); pg.evaluate("()=>{ window.__vvm.follow = true; }"); seen = []
            for y in (150, 350, 250):
                pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(420)
                b = pg.evaluate(READ); seen.append({k: (round(b[k]["r"][1] - a[k]["r"][1], 1) if b.get(k) and a.get(k) else None) for k in ("header", "pause", "chat")})
            pg.evaluate("()=>{ window.__vvm.follow = false; }")
            out["follow"] = seen
    out["final"] = pg.evaluate(READ)
    ctx.close()
    return out
def same(a, b, tol=1.0):
    if a is None or b is None: return a is None and b is None
    return max(abs(x - y) for x, y in zip(a["r"], b["r"])) <= tol
def run(br):
    for dev in DEVICES:
        ref = walk(br, REF, dev, False); got = walk(br, RAW, dev, True)
        name, top = dev[0], dev[3]
        for key in [k for k in ref if isinstance(k, tuple)]:
            r, g = ref[key], got.get(key)
            if not g: chk("%s %s y%d: read" % (name, *key), False, g); continue
            # Pause on a question is 384 r5's (16px, 5.4rem; on an iPad the 384 text trim makes it 40px tall), and the chat button stands beside it:
            # kept on purpose, so on a question those two are compared for staying put (below), not against 383
            kept = ("pause", "chat") if key[0] == "question" else ()
            diff = {k: [r[k] and r[k]["r"], g[k] and g[k]["r"]] for k in ("header", "pause", "chat", "back") if k not in kept and not same(r[k], g[k])}
            chk("%s %s scrolled %d: header%s and back button on 383's rects (%s)" % (name, key[0], key[1], "" if kept else ", Pause, chat", "same" if not diff else diff), not diff, diff)
            if kept and (key[0], 0) in got and key[1]:
                g0 = got[(key[0], 0)]
                moved = {k: [g0[k] and g0[k]["r"], g[k] and g[k]["r"]] for k in kept if not same(g0[k], g[k], .5)}
                chk("%s %s scrolled %d: Pause and the chat button where they were at 0 (%s)" % (name, key[0], key[1], "same" if not moved else moved), not moved, moved)
        # (4) (384.78) ONE LOOK for the top band's buttons, on every screen read here: the chat button (Home included), Pause and the round back buttons
        LOOK = ("bf", "bg", "bi", "bc", "sh")
        looks = {}
        for key in [k for k in got if isinstance(k, tuple)]:
            for el in ("chat", "pause", "back"):
                v = got[key].get(el)
                if v: looks.setdefault(tuple(v[f] for f in LOOK), []).append("%s %s y%d" % (el, key[0], key[1]))
        chk("%s: the chat button, Pause and the round back buttons wear one look on every screen (%d look%s: %s)" % (name, len(looks), "" if len(looks) == 1 else "s",
            "; ".join("%s <- %s" % (k[:2], v[:3]) for k, v in looks.items())[:400]), len(looks) == 1, looks)
        chk("%s: ... and it is 384.76's unblurred glass (no backdrop blur)" % name, all(k[0] in ("none", "") for k in looks), list(looks)[:3])
        chk("%s: ... read on Home, a question (with Pause) and beyond Home" % name,
            any(x.startswith("chat home") for v in looks.values() for x in v) and any(x.startswith("pause question") for v in looks.values() for x in v)
            and any(x.startswith("chat profile") for v in looks.values() for x in v), list(looks.values())[:1])
        worst = max(abs(v) for s in got["follow"] for v in s.values() if v is not None)
        chk("%s: with the visual viewport reading offset by the scroll the header, Pause and chat do not move (worst %.1f; 383 %s)" % (name, worst, ref["follow"]), worst <= .5, got["follow"])
        f = got["final"]
        chk("%s: --sat is the raw inset (%.1f vs %d)" % (name, f["sat"], top), abs(f["sat"] - top) < .6, f["sat"])
        chk("%s: (384.80) the root does not bounce (overscroll-behavior-y %s; 383 %s)" % (name, f["ob"], ref["final"]["ob"]), f["ob"] == "none", f["ob"])
        e, s = f["edge"], f["safe"]
        # (384.80, changed on purpose: the owner's Safari 26 / r/PWA reports) ONE strip: #top-edge over the whole safe area (6px where there is none),
        # a solid opaque colour with no image, taps going through; #top-safe is folded into it
        chk("%s: #top-edge is the one opaque strip over the status bar's area, solid, taps through (%s, %s, %s, %s)" % (name, e and e["r"], e and e["bg"], f["ebi"], f["pe"]),
            e and e["r"][1] == 0 and abs(e["r"][3] - max(top, 6)) < .6 and "rgba" not in e["bg"] and f["ebi"] == "none" and f["pe"] == "none", f)
        chk("%s: no second strip (#top-safe %s)" % (name, s), s is None, s)
        px = got.get("strip_px")
        chk("%s: a Profile scrolled 300 shows the same status-bar area as at rest - nothing of the page under the clock (%s pixels off)" % (name, px and px[0]), px and px[0] == 0, px)
        tw = f["tw"] or {}
        # (384.80, changed on purpose) theme-color follows the sampled strip with the "fe" dance; color-scheme is still never written
        tch = (f["tc"] or "").lstrip("#"); tcr = "rgb(%d, %d, %d)" % tuple(int(tch[i:i + 2], 16) for i in (0, 2, 4)) if len(tch) == 6 else None
        chk("%s: color-scheme not written after launch (%s writes); theme-color is #top-edge's colour (%s / %s)" % (name, tw.get("cs", 0), f["tc"], e and e["bg"]), not tw.get("cs") and e and tcr == e["bg"], tw)
    # markup ahead of every script
    serve = RAW; bi = serve.find("\n<body>\n"); ie, ib = serve.find('id="top-edge"', bi), serve.find("<script", bi)
    chk("the strip is in the markup ahead of every script in <body>, with an inline colour (%d < %d)" % (ie, ib), 0 < ie < ib and 'id="top-edge" aria-hidden="true" style="background-color:' in serve, [ie, ib])
    # (6) the variants
    dev = DEVICES[0]
    ctx, pg = boot(br, RAW, dev, "localStorage.setItem('class26e.displaytest','1');")
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    r = pg.evaluate("""()=>{ const T = window.__diagTrials; if(!T) return null; return ['tvmatch', 'tvdeep', 'tv383'].map(i => !!T.byId[i]); }""")
    chk("the display test lists A, B and C (%s)" % r, r and all(r), r)
    ctx.close()
    for flag, cls in (("topmatch", "top-match"), ("topdeep", "top-deep"), ("top383", "top-383")):
        ctx, pg = boot(br, RAW, dev, "localStorage.setItem('class26e.%s','1');" % flag)
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1200); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1200)
        f = pg.evaluate(READ)
        d = pg.evaluate("()=>{ const e = document.getElementById('top-deep'); if(!e) return null; const cs = getComputedStyle(e), r = e.getBoundingClientRect(); return [cs.display, Math.round(r.bottom), cs.zIndex]; }")
        chk("variant %s: the head script put .%s on (%s)" % (flag, cls, cls in f["cls"].split()), cls in f["cls"].split(), f["cls"])
        if flag == "topdeep": chk("variant B: the flat backdrop lies under the wash's depth, behind the content (%s)" % d, d and d[0] == "block" and d[1] == dev[3] + 62 and d[2] == "-1", d)
        if flag == "top383":
            chk("variant C: no strip of any kind (edge %s, safe %s, guard)" % (f["edge"], f["safe"]), f["edge"] is None and f["safe"] is None and not pg.evaluate("()=>!!document.getElementById('top-guard')"), f)
            chk("variant C: the tags are the app's again (theme-color written after launch: %s)" % (f["tw"] or {}).get("tags"), (f["tw"] or {}).get("tags", 0) >= 1, f["tw"])
        ctx.close()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    try: run(br)
    finally: br.close()
chk("no page errors (%d)" % len(errs), not errs, errs[:4])
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
