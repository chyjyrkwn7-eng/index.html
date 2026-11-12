#!/usr/bin/env python3
"""Build 384.54: THE TOP OF THE SCREEN - nothing of ours sits in the system's fade, nothing of ours fades the header, and a Safari tab's edges agree.

Madison (iPhone 17 Pro Max, iOS 26.x, the installed app, a third report): "The top of my phone screen still has the faded things that are covering the stuff."
His screenshots: Home with the status-bar zone circled; a paused Drill where "Drill", "8/8", the chat button are blurred to nothing; an answered question where
"Drill 1/11 ... Pause" is blurred. Read off them (docs/notes-archive.md "384.54"): his page is laid out 518 CSS px wide on a 440pt screen (0.85pt a CSS px), the
header row sits at 62-99pt, and the wash iOS 26 draws under `black-translucent` ends at ~100pt, level with the bottom of that row. Chromium cannot draw that wash, so what
this gate holds is what is OURS and what puts content inside it:
 (1) CLEAR   on Home, a Drill question, the answered state, the paused state, the results, Settings, Profile and the Leaderboard, in an installed iPhone held upright
             (440x956 with the 59px island inset, and his 518px-wide page-zoomed layout on a 440pt screen with the same inset in CSS px): the first control or line of
             text starts at least CLEAR_PT (40pt) below the safe-area line, measured in points on the glass; no header, title or button is inside the system's ~100pt;
             (384.77, REVERSED ON PURPOSE: the push-down is off by default - it left a band of scrolled page between the status bar and the header and did not
             remove the wash; CLEAR_PT is 0 now, i.e. nothing starts under the status bar, and the 42pt clearance is checked only with class26e.topclear = "1")
 (2) INK     the header's text and buttons are at their true colour: the brightest ink pixel of each against the colour round it, as a share of what its CSS colour says,
             is at least INK_MIN (a positive control - a 55% scrim laid over the row - must drop below it, so the check can fail);
 (3) LAYERS  the only fixed full-width layers in the top 200px are the 12px strip (inside the status bar, never lower than the inset) and the header's own fade
             (z-index below the header's content); nothing paints over a control;
 (4) STRIP   on a question the 12px strip is the colour the page is just under it (paper, under the pinned header's fade): within STEP_MAX levels (it was 10);
 (5) ELSEWHERE nothing moves outside an installed iPhone held upright with a notch: a phone on its side, an SE-sized phone, an iPad, a Safari tab and
             class26e.topclear = "0" keep --sat equal to the raw inset; the clearance is in points (x --zc), 42pt;
 (6) SAFARI TAB (iPhone Safari UA, not installed; Chromium cannot draw Safari's bars, so this is the repo's model of them: the page between the bars at 440x797, and
             the bars over a full-height page at 440x956 with a 62pt / 83pt model): the theme-color tag is the colour the page paints at its top row (it was 13 levels
             off on Home); the page's first rows on a question are the root's band colour Safari fills above them (it was 9 off); with the bars over the page, every
             pinned bottom element (tab bar, primary button, floating buttons) ends above the toolbar and the top controls start below the status bar; when the toolbar
             collapses (the viewport grows) the tab bar keeps its distance from the bottom and nothing scrolls sideways.
 (7) no page errors.
Run:  python3 tools/check-b384-topfade.py [--shots DIR]    (--against OLD/index.html must FAIL: main 384.62 fails 1, 4, 5, 6 - 30 of 96 checks; 5's failures there are
only --sat not existing, so 1, 4 and 6 are the ones that measure the build)"""
import os, sys, io, re, statistics, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
args = sys.argv[1:]
SHOTS = None
if "--shots" in args:
    i = args.index("--shots"); SHOTS = os.path.abspath(args[i + 1]); os.makedirs(SHOTS, exist_ok=True)
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
def serve_with(top, bottom):
    ins = {"top": "%gpx" % top, "bottom": "%gpx" % bottom, "left": "0px", "right": "0px"}
    cb.BODY = cb.INSET_RE.sub(lambda m: ins[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
from PIL import Image
CLEAR_PT, INK_MIN, STEP_MAX, TAB_STEP, ZONE_PT = 0, 0.75, 3, 4, 100   # (384.77) CLEAR_PT was 40: the 42pt push-down is reversed on purpose; nothing starts under the status bar
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:420], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
UA_TAB = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');")
def boot(br, W, H, scr=None, standalone=True, ua=UA, extra="", touch=True, mobile=True):
    kw = dict(viewport={"width": W, "height": H}, device_scale_factor=2, has_touch=touch, is_mobile=mobile, user_agent=ua)
    if scr: kw["screen"] = {"width": scr[0], "height": scr[1]}
    ctx = br.new_context(**kw)
    ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');%s}catch(e){}" % (SEEN, cb.USED_ACCOUNT, extra))
    if standalone: ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    pg = cb.open_page(ctx); pg.goto(cb.URL); pg.wait_for_timeout(2500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); pg.wait_for_timeout(700)
    return ctx, pg
SMALL = """()=>{ const u='Identity Crimes'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false; theme.reduceMotion=true;
  beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u)), null); }"""
RIGHT = """()=>{ const r=correctSlot(order[pos]); document.querySelector('.qpanel .choice[data-index="'+r+'"]').click(); }"""
def finish(pg):
    pg.wait_for_selector(".qpanel .choice", timeout=25000)
    for _ in range(40):
        if not pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
        p = pg.evaluate("()=>pos"); pg.evaluate(RIGHT); pg.wait_for_timeout(450)
        if pg.evaluate("()=>!!document.getElementById('nextbtn')"): pg.evaluate("()=>document.getElementById('nextbtn').click()")
        for _ in range(30):
            pg.wait_for_timeout(120)
            if pg.evaluate("()=>pos") != p or not pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
    pg.wait_for_timeout(2500)
SCREENS = ["home", "drill", "answered", "paused", "results", "settings", "profile", "leaderboard"]
def mount(pg, name):
    pg.evaluate("()=>{ try{ if(document.getElementById('pausebtn') && !document.querySelector('.pausepanel')){} }catch(e){} }")
    if name in ("drill", "answered", "paused", "results"):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
        pg.evaluate(SMALL); pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(900)
        if name == "answered": pg.evaluate(RIGHT); pg.wait_for_timeout(1200)
        if name == "paused": pg.evaluate("()=>document.getElementById('pausebtn').click()"); pg.wait_for_timeout(1200)
        if name == "results": finish(pg)
    else:
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
        pg.evaluate({"home": "()=>showHome()", "settings": "()=>showAppearance()", "profile": "()=>showProfile()", "leaderboard": "()=>showRankings()"}[name]); pg.wait_for_timeout(1700)
    pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot').forEach(n=>n.remove()); }"); pg.wait_for_timeout(250)
def shot(pg, path=None):
    b = pg.screenshot(); im = Image.open(io.BytesIO(b)).convert("RGB")
    if path: im.save(path)
    return im
# the rows in the top 220px: visible, hit-testable controls and text lines (css px), plus the top-layer scan
ROWS = """()=>{
  const k = screen.width / innerWidth, out = [];
  const vis = e => { try{ return e.checkVisibility({ checkOpacity:true, checkVisibilityCSS:true }); }catch(x){ return true; } };
  const who = a => a.tagName.toLowerCase()+(a.id?'#'+a.id:'')+(typeof a.className==='string'&&a.className?'.'+a.className.trim().split(/\\s+/).slice(0,2).join('.'):'');
  for(const e of document.body.querySelectorAll('*')){
    if(e.closest('#splashscreen,#top-edge,script,style,svg')) continue;
    if(!vis(e)) continue;
    const r = e.getBoundingClientRect(); if(r.width < 4 || r.height < 4 || r.top >= 220 || r.bottom <= 0) continue;
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const ctl = /^(BUTTON|A|INPUT)$/.test(e.tagName);
    if(!own && !ctl) continue;
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const hit = document.elementFromPoint(Math.min(innerWidth - 1, Math.max(0, cx)), Math.min(innerHeight - 1, Math.max(0, cy)));
    if(!hit || !(hit === e || e.contains(hit) || hit.contains(e))) continue;
    const cs = getComputedStyle(e);
    out.push({ w: who(e), l: r.left, t: r.top, r: r.right, b: r.bottom, color: cs.color, own, ctl, txt: (e.textContent || '').trim().slice(0, 16) });
  }
  const cs0 = getComputedStyle(document.documentElement);
  const layers = [];
  for(const e of document.body.querySelectorAll('*')){
    const cs = getComputedStyle(e); if(cs.position !== 'fixed' || !vis(e)) continue;
    const r = e.getBoundingClientRect(); if(r.top >= 200 || r.width < innerWidth * .6) continue;
    const bg = cs.backgroundColor, painted = (bg && !/rgba\\(\\s*0,\\s*0,\\s*0,\\s*0\\)|transparent/.test(bg)) || cs.backgroundImage !== 'none' || (cs.backdropFilter && cs.backdropFilter !== 'none');
    if(painted) layers.push({ w: who(e), t: r.top, b: r.bottom, z: cs.zIndex, bg });
  }
  const tops = [...document.querySelectorAll('.wrap > .top, #stage .top')].map(t => { const p = getComputedStyle(t, '::before'); return p.content !== 'none' ? { z: p.zIndex, pos: p.position, h: t.getBoundingClientRect().height } : null; }).filter(Boolean);
  const edge = document.getElementById('top-edge'); const er = edge && edge.getBoundingClientRect();
  return { k, sat: cs0.getPropertyValue('--sat').trim(), extra: cs0.getPropertyValue('--edge-extra').trim(), zc: cs0.getPropertyValue('--zc').trim(), rows: out, layers, tops,
           edge: edge ? { h: er.height, b: er.bottom, disp: getComputedStyle(edge).display } : null, inW: innerWidth, scrW: screen.width }; }"""
def med_row(im, y):
    vals = [im.getpixel((x, y)) for x in range(8, im.width - 8, 8)]
    return tuple(int(statistics.median(v[i] for v in vals)) for i in range(3))
def parse_rgb(c):
    m = re.findall(r"[\d.]+", c or ""); return tuple(float(x) for x in m[:3]) if len(m) >= 3 else None
def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def ink_ratio(im, row, scale):
    """brightest-vs-background contrast of the element's pixels as a share of its CSS colour's contrast with the same background"""
    css = parse_rgb(row["color"]); x0, y0, x1, y1 = [int(round(v * scale)) for v in (row["l"], row["t"], row["r"], row["b"])]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(im.width, x1), min(im.height, y1)
    if x1 - x0 < 4 or y1 - y0 < 4 or not css: return None
    # the background: the median of a ring 4px outside the box
    ring = [im.getpixel((x, y)) for x in range(x0, x1, 3) for y in (max(0, y0 - 4), min(im.height - 1, y1 + 4))]
    if not ring: return None
    bg = tuple(statistics.median(p[i] for p in ring) for i in range(3)); bl = lum(bg)
    want = abs(lum(css) - bl)
    if want < 40: return None   # a colour too close to its ground to read as ink (a glass button's own border etc.)
    px = [im.getpixel((x, y)) for x in range(x0, x1) for y in range(y0, y1)]
    got = max(abs(lum(p) - bl) for p in px)
    return got / want
errs = []
def retry(fn, tries=3):
    """a scenario gets a fresh browser each try: under load a page (or the browser) crashes, and that is not the build"""
    for i in range(tries):
        try:
            with sync_playwright() as pw:
                br = pw.chromium.launch(executable_path=cb.CHROME)
                try: return fn(br)
                finally:
                    try: br.close()
                    except Exception: pass
        except Exception as e:
            if "closed" in repr(e).lower() or "crashed" in repr(e).lower():
                print("  (retry %d: %s)" % (i + 1, repr(e)[:80]), flush=True); continue
            raise
    raise RuntimeError("page kept crashing")
def phone_pass(br, label, W, H, scr, inset_css):
    """every screen at one installed-iPhone geometry: clearance, ink, layers, strip"""
    serve_with(inset_css, 34)
    ctx, pg = boot(br, W, H, scr, ua=UA, mobile=(scr is None), touch=True)
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    cls = pg.evaluate("()=>document.documentElement.className")
    chk("%s: installed iPhone, upright: the still-edge class is on (%s)" % (label, cls), "top-edge-on" in cls, cls)
    worst = {}
    for name in SCREENS:
        mount(pg, name)
        d = pg.evaluate(ROWS); k = d["k"]; rows = d["rows"]
        im = shot(pg, os.path.join(SHOTS, "%s-%s.png" % (label.split()[0], name)) if SHOTS else None)
        inset_pt = inset_css * k
        first = min((r["t"] for r in rows), default=None)
        first_pt = first * k if first is not None else None
        who = [r["w"] for r in rows if r["t"] == first][:2]
        chk("%s %s: the first control or line starts %.0fpt below the safe-area line (%.1fpt, needs >= %d - 384.77: not pushed down, never under the status bar; %s)" % (label, name, (first_pt or 0) - inset_pt, first_pt or 0, CLEAR_PT, who),
            first_pt is not None and first_pt - inset_pt >= CLEAR_PT - 0.6, [first_pt, inset_pt, who])
        # (2) ink: every text/control row that is in the top ZONE_PT of the glass
        zone = [r for r in rows if r["t"] * k < ZONE_PT + 60 and r["own"]]
        ratios = [(ink_ratio(im, r, 2), r["w"]) for r in zone]; ratios = [x for x in ratios if x[0] is not None]
        low = [x for x in ratios if x[0] < INK_MIN]
        chk("%s %s: the header's text is at its true colour (%d rows, lowest %.2f >= %.2f)" % (label, name, len(ratios), min([x[0] for x in ratios], default=1), INK_MIN), not low, low)
        # (3) layers
        bad = [l for l in d["layers"] if l["w"] not in ("div#top-edge", "div#top-safe") and not (l["w"].startswith("div#splash"))]   # (384.77) #top-safe: the status bar's area, opaque, under every layer
        chk("%s %s: no fixed full-width layer in the top 200px but the strip (%s)" % (label, name, [l["w"] for l in bad]), not bad, bad)
        e = d["edge"]
        chk("%s %s: the strip is %spx, inside the status bar (its foot %spx, the inset %spx)" % (label, name, e and e["h"], e and e["b"], inset_css), e and e["b"] <= inset_css + .5 and e["disp"] == "block", e)
        for t in d["tops"]:
            chk("%s %s: the header's own fade sits BEHIND its content (z-index %s)" % (label, name, t["z"]), t["z"] != "auto" and int(t["z"]) < 0, t)
        # (4) the strip against the page just under it
        if name in ("drill", "answered"):
            s = med_row(im, 6); p = med_row(im, 2 * 14 + 2)
            step = max(abs(a - b) for a, b in zip(s, p))
            chk("%s %s: the 12px strip is the page's colour (step %d <= %d: %s vs %s)" % (label, name, step, STEP_MAX, s, p), step <= STEP_MAX, (s, p))
        if name == "answered":
            # (2) positive control: a 55% scrim over the header row must drop the ink below the floor
            pg.evaluate("""()=>{ const d = document.createElement('div'); d.id = 'scrim'; d.style.cssText = 'position:fixed;left:0;right:0;top:0;height:220px;background:rgba(17,21,27,.55);z-index:2147482000;pointer-events:none'; document.body.appendChild(d); }""")
            pg.wait_for_timeout(200); im2 = shot(pg)
            r2 = [(ink_ratio(im2, r, 2), r["w"]) for r in zone]; r2 = [x for x in r2 if x[0] is not None]
            chk("%s: positive control - a 55%% scrim over the header drops its ink below the floor (lowest %.2f < %.2f), so (2) can fail" % (label, min([x[0] for x in r2], default=1), INK_MIN), any(x[0] < INK_MIN for x in r2), r2[:4])
            pg.evaluate("()=>document.getElementById('scrim')?.remove()")
    ctx.close()
def elsewhere(br):
    def one(label, W, H, scr, inset, ua, standalone, extra="", expect_zero=True, touch=True):
        serve_with(inset, 34)
        ctx, pg = boot(br, W, H, scr, standalone=standalone, ua=ua, extra=extra, mobile=(scr is None), touch=touch)
        sat = pg.evaluate("()=>{ const px = v => { const p = document.createElement('i'); p.style.cssText = 'position:fixed;top:0;width:0;height:var(' + v + ')'; document.body.appendChild(p); const h = p.getBoundingClientRect().height; p.remove(); return h; }; return [px('--sat'), px('--edge-extra')]; }")
        chk("%s: --sat is the raw inset (%s, extra %s)" % (label, sat[0], sat[1]), abs(sat[0] - inset) < .6 and abs(sat[1]) < .1, [sat, inset])
        ctx.close()
    one("an iPhone on its side (956x440)", 956, 440, None, 0, UA, True)
    one("an SE-sized phone (375x667, 20px inset)", 375, 667, None, 20, UA, True)
    one("an iPad Pro 11 (834x1194)", 834, 1194, None, 24, UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS"), True)
    one("a Safari tab on a Pro Max (440x797)", 440, 797, None, 0, UA_TAB, False)
    one("class26e.topclear = 0 on a Pro Max", 440, 956, None, 59, UA, True, extra="localStorage.setItem('class26e.topclear','0');")
    one("a Pro Max by default (384.77: the clearance is off)", 440, 956, None, 59, UA, True)
    serve_with(59, 34)
    ctx, pg = boot(br, 440, 956, None, ua=UA, extra="localStorage.setItem('class26e.topclear','1');")   # (384.77) only when asked for
    d = pg.evaluate(ROWS)
    px = pg.evaluate("()=>{ const p = document.createElement('i'); p.style.cssText = 'position:fixed;top:0;height:var(--edge-extra);width:0'; document.body.appendChild(p); const h = p.getBoundingClientRect().height; p.remove(); return h; }")
    chk("a Pro Max at 100%% even with class26e.topclear = 1: no clearance (384.77: build 383's top; %s)" % px, abs(px) < .6, px)
    ctx.close()
    serve_with(73, 40)
    ctx, pg = boot(br, 518, 1126, (440, 956), ua=UA, mobile=False, extra="localStorage.setItem('class26e.topclear','1');")
    px = pg.evaluate("()=>{ const p = document.createElement('i'); p.style.cssText = 'position:fixed;top:0;height:var(--edge-extra);width:0'; document.body.appendChild(p); const h = p.getBoundingClientRect().height; p.remove(); return [h, innerWidth / screen.width]; }")
    chk("his 518px page on a 440pt screen: no clearance (384.77: build 383's top; %.1f CSS px)" % px[0], abs(px[0]) < .6, px)
    ctx.close()
def safari_tab(br):
    # at rest: the page between the bars (the repo's model: 440x797, no insets)
    serve_with(0, 0)
    ctx, pg = boot(br, 440, 797, None, standalone=False, ua=UA_TAB)
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    for name in ("home", "drill", "settings"):
        mount(pg, name); im = shot(pg, os.path.join(SHOTS, "tab-rest-%s.png" % name) if SHOTS else None)
        info = pg.evaluate("""()=>({ tc: document.getElementById('themecolor').content, band: getComputedStyle(document.documentElement).getPropertyValue('--band').trim(), sky: appTopEdgeColor() })""")
        # (384.77, REVERSED ON PURPOSE) a Safari tab's tag is the sky's top colour again, as build 383 had it (384.54 had made it --band)
        chk("Safari tab, %s: the theme-color tag is the sky's top colour, as build 383 (%s vs %s)" % (name, info["tc"], info["sky"]), (info["tc"] or "").lower() == (info["sky"] or "").lower(), info)
    ctx.close()
    # the bars over a full-height page: 62pt status bar, 83pt toolbar (the model), insets 62 / 34 as the sweep's
    serve_with(62, 34)
    ctx, pg = boot(br, 440, 956, None, standalone=False, ua=UA_TAB)
    over = pg.evaluate("()=>document.documentElement.classList.contains('safari-bars-over')")
    chk("Safari tab at full height with an inset: the page knows Safari's bars are over it", over)
    PIN = """(sbTop, sbBot)=>{ const vh = innerHeight, out = [];
      for(const e of document.body.querySelectorAll('*')){
        const cs = getComputedStyle(e); if(cs.position !== 'fixed') continue;
        try{ if(!e.checkVisibility({ checkOpacity:true, checkVisibilityCSS:true })) continue; }catch(x){}
        const r = e.getBoundingClientRect(); if(r.width < 20 || r.height < 20 || r.width > innerWidth * .98 && r.height > vh * .5) continue;
        if(r.top >= vh - 200 && r.bottom > vh - sbBot + .5) out.push('bottom ' + e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + '.' + (e.className || '').toString().split(' ')[0] + ' ends ' + Math.round(r.bottom) + ' > ' + (vh - sbBot));
        if(r.bottom <= 200 && r.top < sbTop - .5) out.push('top ' + e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + ' starts ' + Math.round(r.top) + ' < ' + sbTop);
      }
      const pb = document.querySelector('.playbtn, #nextbtn, .gs-bar button'); const pr = pb && pb.getBoundingClientRect();
      return { bad: out, play: pr ? Math.round(pr.bottom) : null, vh }; }"""
    for name in ("home", "drill", "answered", "settings"):
        mount(pg, name)
        r = pg.evaluate(PIN, [62, 83])
        chk("Safari bars over the page, %s: every pinned bottom element is above the toolbar (the 83pt model), every pinned top one below the status bar (%s)" % (name, r["bad"][:3]), not r["bad"], r)
        if name == "home":
            chk("Safari bars over the page, home: Start Studying ends above the toolbar (%s <= %d)" % (r["play"], r["vh"] - 83), r["play"] is not None and r["play"] <= r["vh"] - 83, r)
    ctx.close()
    # the toolbar collapses on a scroll: the viewport grows; the tab bar keeps its distance from the bottom
    TB = "()=>{ const t = document.querySelector('.bottomtabs'); if(!t) return null; const r = t.getBoundingClientRect(); return { gap: innerHeight - r.bottom, sw: document.documentElement.scrollWidth - innerWidth }; }"
    serve_with(0, 0)
    ctx, pg = boot(br, 440, 797, None, standalone=False, ua=UA_TAB)
    mount(pg, "home"); a = pg.evaluate(TB)
    pg.set_viewport_size({"width": 440, "height": 870}); pg.wait_for_timeout(700); b = pg.evaluate(TB)
    chk("Safari tab, the toolbar collapses (797 -> 870px): the tab bar keeps its distance from the bottom (%s -> %s) and nothing scrolls sideways" % (a and a["gap"], b and b["gap"]),
        a and b and abs(a["gap"] - b["gap"]) < 1.5 and b["sw"] <= 0, [a, b])
    ctx.close()
retry(lambda br: phone_pass(br, "Pro Max 440x956", 440, 956, None, 59))
retry(lambda br: phone_pass(br, "Pro Max at 85% page zoom (518x1126 on 440x956pt)", 518, 1126, (440, 956), 73))
retry(elsewhere)
retry(safari_tab)
chk("no page errors", not errs, errs)
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
