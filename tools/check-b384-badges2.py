#!/usr/bin/env python3
"""Build 384.121 follow-up (claude/b384-badges2): the police academy's unit badges are back to what origin/main draws, and Fire Code's
chapter badges are untouched. Madison: "Revert the badges for the police academy. I'm not a fan of these new ones."

Every badge surface is drawn on the build under test and on a reference build, in the same Chromium, and compared PIXEL FOR PIXEL
(nothing typed: the reference is the other build's own output):
 (1) THE SHEET, per unit of the class (all 24 academy units / all 58 Fire Code chapters), at 440x956 @3x and 834x1194 @2x: the found
     badge at 26, 40, the case slot's size, 88 (no slot) and the card's own size; the empty slot; the grey token; the found badge at
     every dirt stage 1-4 (the renderer still takes one); the unit card's badge found / empty / grey (cardBadgeSVG); the back at every
     dirt stage (renderBadgeBack, the badge in your hand turned round); the coin face of the earned cutscene (badgeCoinFaceURL);
 (2) THE TOKENS' OWN PIXELS: renderBadgeStrike found / grey at every dirt stage 0-4, at 132 and 84 device px, read with getImageData
     and hashed (exact, no screenshot);
 (3) THE SCREENS, on a stopped clock (every animation seeked to the same time from the step it was first seen): the Badges screen's
     case (found and empty slots), a found badge in your hand (the inspect view), the unit list's cards (Choose your units), and four
     frames of the badge-earned cutscene (the coin at rest after its spin, swaying, the case open, the badge seated). The in-hand view
     and the cutscene are compared with the glint layers (and what is inside them) hidden on both builds: the glint is the 384.108 shine
     work, which stays on purpose (the compositor glint replaced the in-SVG one, and the coin is no longer left lit at rest). That work
     also gives the coin's band its own layer from the start of the scene, which rounds the coin under it by 1-2 levels on a few hundred
     device pixels: the cutscene allows 2 levels on 0.05% of the frame and prints what it allowed. The frames as they are, glint shown,
     are printed for information only;
 (4) no page errors.
--class academy compares with 31588af (was origin/main 384.107; --acad-ref REV|FILE); --class ifc compares with 1c2758a (384.133 art3; was 31588af, before that a68976a, claude/b384-badges,
--ifc-ref REV|FILE). Default: both.
Run:  python3 tools/check-b384-badges2.py [--class academy|ifc|both] [--against REV|FILE] [--shots DIR]
      --against origin/main must PASS the academy (main against itself); --against a68976a must FAIL it (the 24 redrawn pins)."""
import hashlib, io, json, os, re, subprocess, sys, functools, http.server, socket, threading, glob, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
def body_of(a):
    if os.path.exists(a): return open(a, encoding="utf-8").read()
    return subprocess.run(["git", "-C", ROOT, "show", a + ":index.html"], capture_output=True, text=True, check=True).stdout
HERE_NAME = arg("--against", "working tree")
HERE = body_of(arg("--against")) if arg("--against") else open(ROOT + "/index.html", encoding="utf-8").read()
# (384.133 badgeart) Fire Code's reference RE-PINNED from a68976a to 31588af: Madison asked for 19 chapters redrawn ("make it great",
# "fix every one", then "do a check on all of them") - 5, 9, 22, 28, 31, 32, 33, 34, 35, 37, 40, 54, 57, 59, 60, 61, 63, Appendix H and I,
# and Chapter 3 a little wider and Appendix B's spray wider for their backs - and the badge case itself was rebuilt (384.133 casefix).
# 31588af is that art and that case. Every badge, back, card and screen is still held pixel for pixel to it, so any change not asked
# for fails as before; --against 458b3c9 fails on exactly the redrawn chapters and the case.
# The academy's reference likewise moves from origin/main (384.107) to 31588af: its badges, tokens, sheets and case there are main's
# pixel for pixel (this gate's (1) and (2), and the case in (3), passed against origin/main on 31588af), but casefix rebuilt the
# cutscene's case (rounded box, the lid's reflection of the found badges), so main's cutscene frames are no longer the academy's.
# (384.133 art3) Fire Code's reference RE-PINNED from 31588af to 1c2758a: Madison's next round asked for six of them redrawn (Chapter
# 34's tyres "got to look better", Chapter 33's star "is not it", Appendix H's pencil at the cone, Chapter 32's rack "hard to tell what
# that even is", Chapter 63's valve-to-tank connection, Chapter 61's collar). On fa11d79 against 31588af, exactly those six tokens
# differed (2), their six sheet images (1), and the case and the cutscene frames that hold them (3); every other token, back, card and
# screen was pixel-identical. 1c2758a is that art; everything is still held pixel for pixel to it, and --against fa11d79 fails on
# exactly the six. The academy's reference is unchanged (it passed against 31588af on this branch).
# (384.136) Fire Code's reference moves to round 4's art (ee8ef50: Madison's fixes to the hat, pencil, rack, cylinder and LPG tank);
# the pins are the art gates' to hold (check-b384-objbadges, check-b384-badgeart); this one holds everything else in the case
# (384.136 art6) Fire Code's reference moves again: a pin's side takes its parts' colours (badgeEdgeColourHref), so the badge in hand
# and the earned cutscene's turned coin differ there and only there (the run before this re-pin: (3) inspect 2 and cutscene 6, nothing else)
# (384.136 art6 round 3) and again: Appendix H redrawn, the rack, the cylinder, the bare faces in hand and the edge-on strip
# (384.136 art6 round 4) and again: the pencil, ticks, rack and cylinder collar redrawn
REFS = {"academy": arg("--acad-ref", "31588af"), "ifc": arg("--ifc-ref", "dfd6af1")}
CLASSES = ["academy", "ifc"] if arg("--class", "both") == "both" else [arg("--class")]
SHOTS = arg("--shots")
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}   # sheet, screens, cutscene
if SHOTS: os.makedirs(SHOTS, exist_ok=True)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
ok = True
CARD_UNREAD = []
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
# an existing, up-to-date account: nothing lands over what is measured
SEED = {"onboardingComplete": True, "firstName": "Sample", "avatarChar": "ninja", "publicId": "xph5b57jbp5a", "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30, "longestStreak": 20, "currentStreak": 3}}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted", "penal55124.seen", "penal124256.seen", "penal256578.seen"]
def init_js(cls):
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    return s + " }catch(e){} })()"
VIEWS = [(440, 956, 3, "promax"), (834, 1194, 2, "ipad11")]
def open_page(br, body, cls, w, h, dsf):
    for attempt in range(4):
        try:
            ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dsf, has_touch=True, is_mobile=w < 600)
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
            pg.add_init_script(init_js(cls))
            served = (re.search(r'const APP_BUILD = "([^"]+)"', body) or [None, ""])[1]
            pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
            pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % served))
            pg.goto("http://127.0.0.1:%d/index.html" % port, timeout=180000); pg.wait_for_timeout(3500)
            pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
            # a third of the units not yet found; nothing new, nothing pending, every badge clean as of now
            pg.evaluate("""() => { const us = unitsInTeachingOrder(); store.unitPerfects = {};
              us.forEach((u, i) => store.unitPerfects[u] = (i % 3 !== 2) ? badgeThresholdFor(u) : Math.floor(badgeThresholdFor(u) / 3));
              store.seenUnlocks = store.seenUnlocks || { chars: [], banners: [], themes: [], badges: [] }; store.seenUnlocks.badges = us.slice();
              const held = unlockedIdsNow(); ['chars', 'banners', 'themes', 'fx'].forEach(k => { store.seenUnlocks[k] = (held[k] || []).slice(); });
              store.badgeCleanedAt = {}; const now = Date.now(); us.forEach(u => { store.badgeCleanedAt[u] = now - 3600e3; });
              store.pendingBadgeUnlocks = []; saveStore(); theme.muteBanners = true; applyTheme(); showHome();
              document.querySelectorAll('.rs-spot,.daily-alert,#tour-overlay,.update-banner,.toast,.unlock-card,#pushing-update,#intro-pop,.app-banner').forEach(n => n.remove()); }""")
            pg.wait_for_timeout(1500)
            return ctx, pg, errs
        except Exception as e:
            if attempt == 3: raise
            print("page start failed (%s), retrying" % str(e).splitlines()[0][:80], flush=True)
            try: ctx.close()
            except Exception: pass
SHEET = r"""async () => {
  const us = unitsInTeachingOrder(), slot = (typeof badgeCaseSlotPx === 'function') ? badgeCaseSlotPx() : 44;
  const cardPx = (typeof badgeDefaultPx === 'function') ? badgeDefaultPx() : 44;
  document.body.innerHTML = ''; document.documentElement.style.cssText = 'background:#0B0D10'; document.body.style.cssText = 'margin:0;background:#0B0D10';
  const root = document.createElement('div'); root.id = 'sheet'; root.style.cssText = 'position:absolute;left:0;top:0;z-index:2147483647;width:' + (innerWidth - 4) + 'px;background:#0B0D10;';
  document.body.appendChild(root);
  const st = document.createElement('style'); st.textContent = 'body > *:not(#sheet):not(style), #launch-trouble { display: none !important }'; document.body.appendChild(st);   /* a toast, a banner or the launch-trouble screen the app adds later (a page with its body emptied looks like a failed start) */
  const box = (px, el) => { const w = document.createElement('div'); w.style.cssText = 'width:' + px + 'px;height:' + px + 'px;flex:none;display:flex;align-items:center;justify-content:center;';
    el.style.cssText = 'width:100%;height:100%;display:block;overflow:visible'; w.appendChild(el); return w; };
  const img = (px, url) => { const i = document.createElement('img'); i.src = url; return box(px, i); };
  const rows = [];
  for(const u of us){
    const row = document.createElement('div'); row.className = '__row'; row.style.cssText = 'display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px;border-bottom:1px solid #222;';
    [26, 40, slot, cardPx].forEach(px => row.appendChild(box(px, buildUnitBadgeSVG(u, true, { px, dirt: 0 }))));
    row.appendChild(box(88, buildUnitBadgeSVG(u, true, { px: 88, dirt: 0, slot: false })));
    row.appendChild(box(slot, buildUnitBadgeSVG(u, false, { px: slot })));
    row.appendChild(box(slot, buildUnitBadgeSVG(u, 'grey', { px: slot })));
    [1, 2, 3, 4].forEach(d => row.appendChild(box(slot, buildUnitBadgeSVG(u, true, { px: slot, dirt: d }))));
    [true, false, 'grey'].forEach(e => row.appendChild(box(28, cardBadgeSVG(u, e))));
    if(typeof renderBadgeBack === 'function') [0, 1, 2, 3, 4].forEach(d => { const c = renderBadgeBack(u, 132, 2, d); row.appendChild(img(66, c.toDataURL())); });
    if(typeof badgeCoinFaceURL === 'function'){ const f = badgeCoinFaceURL(u); if(f) row.appendChild(img(96, f)); }
    root.appendChild(row);
  }
  await new Promise(r => setTimeout(r, 2500));
  for(let i = 0; i < 150; i++){ if(typeof BADGE_STRIKE_DRAFTS === 'undefined' || !BADGE_STRIKE_DRAFTS.size) break; await new Promise(r => setTimeout(r, 400)); }
  await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
  await new Promise(r => setTimeout(r, 800));
  const fe = (x, y) => { const e = document.elementFromPoint(x, y); return e ? e.tagName + '.' + String(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className).slice(0, 40) + '#' + e.id + ' in ' + (e.closest('#sheet') ? 'sheet' : 'NOT sheet') : null; };
  return { probe: [fe(30, 30), fe(200, 200)], n: us.length, slot, cardPx, units: us, drafts: (typeof BADGE_STRIKE_DRAFTS === 'undefined') ? 0 : BADGE_STRIKE_DRAFTS.size };
}"""
TOKENS = r"""() => { const H = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s[i]; h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const out = {};
  for(const u of unitsInTeachingOrder()){ const r = [];
    [132, 84].forEach(W => [false, true].forEach(g => [0, 1, 2, 3, 4].forEach(d => { if(g && d) return;
      const c = renderBadgeStrike(u, g, W, 2, d); r.push(c.width + 'x' + c.height + ':' + H(c.getContext('2d').getImageData(0, 0, c.width, c.height).data)); })));
    out[u] = r; }
  return out; }"""
SEEK = """(t) => { const M = window.__t0s = window.__t0s || new WeakMap();
  document.getAnimations().forEach(an => {
    if(!M.has(an)) M.set(an, { at: t, from: 0, done: false });   /* first seen at this step: started at it (the document timeline is real time, so its own currentTime is not the same twice) */
    const s = M.get(an); if(s.done) return;
    const want = s.from + (t - s.at) * 1000;
    let end = Infinity; try{ end = an.effect.getComputedTiming().endTime; }catch(e){}
    if(want >= end && isFinite(end)){ s.done = true; try{ an.finish(); }catch(e){} return; }
    if(an.playState !== 'paused') an.pause();
    try{ an.currentTime = want; }catch(e){} }); }"""
class Clock:
    def __init__(self, pg):
        self.pg, self.t = pg, 0.0
        pg.clock.install(); pg.clock.pause_at(pg.evaluate("() => Date.now()") + 50)
    def to(self, t):
        while self.t < t - 1e-6:
            dt = min(1 / 30, t - self.t); t0 = self.t; self.t += dt
            self.pg.clock.run_for(max(1, int(round(self.t * 1000)) - int(round(t0 * 1000))))
            self.pg.evaluate(SEEK, self.t)
# (384.133 pin) the badge in your hand now carries the pinned badge's "Pin to profile" button (Madison asked for a badge on the
# profile "to flex"); it is the pin's own work, measured by check-b384-pin.py, so it is hidden on both builds like the glint, and
# the badge, its name and its card are still compared pixel for pixel.
GLINT = ".binspect-spec, .badge-glint-band, .badge-shine-band, .badge-shine, .badge-glint, .ncase-glint, .bc-spec"
# (384.136) the pin button (Pin to profile) is taken out of the page for the compared picture on both builds (no-op on the reference),
# not hidden: it shares Close's row and Close takes a margin after it, so its space would move Close; the pin gate measures it
GLINT = ", ".join(x + ", " + x + " *" for x in GLINT.split(", "))   # and what is inside each (a visible rule on a child beats an inherited hidden)
HIDEG = "() => { let s = document.getElementById('__hideglint'); if(!s){ s = document.createElement('style'); s.id = '__hideglint'; s.textContent = '%s{visibility:hidden !important}'; document.body.appendChild(s); } }" % GLINT
SHOWG = "() => { const s = document.getElementById('__hideglint'); if(s) s.remove(); }"
def png(pg, clip=None):
    return Image.open(io.BytesIO(pg.screenshot(clip=clip) if clip else pg.screenshot())).convert("RGBA")
def rect(pg, sel):
    return pg.evaluate("(s) => { const e = document.querySelector(s); if(!e) return null; const r = e.getBoundingClientRect(); return r.width && r.height ? { x: Math.max(0, r.left), y: Math.max(0, r.top), width: Math.min(innerWidth, r.right) - Math.max(0, r.left), height: Math.min(innerHeight, r.bottom) - Math.max(0, r.top) } : null; }", sel)

def capture(br, body, cls, tag):
    """every surface of one build in one class: {(view, name): Image}, the token hashes, page errors"""
    imgs, errs_all, tokens = {}, [], None
    for (w, h, dsf, vname) in VIEWS:
        # (1)(2) the sheet and the tokens
        if ONLY and "sheet" not in ONLY:
            tokens = tokens or {}
        else:
          ctx, pg, errs = open_page(br, body, cls, w, h, dsf)
          if tokens is None: tokens = pg.evaluate(TOKENS)
          sh = pg.evaluate(SHEET)
          if not all(p and p.endswith(" in sheet") for p in sh["probe"]): errs.append("the sheet is covered: %s" % sh["probe"])   # (a cover once made every row one blank)
          n = pg.evaluate("() => document.querySelectorAll('#sheet .__row').length")
          for i in range(n):
              r = pg.evaluate("(i) => { const e = document.querySelectorAll('#sheet .__row')[i]; e.scrollIntoView({ block: 'start', behavior: 'instant' }); const b = e.getBoundingClientRect(); return { x: 0, y: b.top, width: b.width, height: Math.min(innerHeight - b.top, b.height) }; }", i)
              imgs[(vname, "sheet %02d %s" % (i, sh["units"][i][:40]))] = png(pg, r)
              if SHOTS and i in (0, 7): imgs[(vname, "sheet %02d %s" % (i, sh["units"][i][:40]))].save(os.path.join(SHOTS, "%s-%s-%s-sheet%02d.png" % (tag, cls, vname, i)))
          errs_all += errs; ctx.close()
        # (3) the screens on a stopped clock
        if not ONLY or "screens" in ONLY:
            ctx, pg, errs = open_page(br, body, cls, w, h, dsf)
            clk = Clock(pg)
            pg.evaluate("() => showRanksScreen('badges')"); clk.to(2.5)
            pg.evaluate("() => { try{ finishBadgeCaseOpen(document.querySelector('.badges-tab .ncase')); }catch(e){} }"); clk.to(4.5)
            pg.evaluate("() => { for(const s of ['.badges-tab .ncase']){ const e = document.querySelector(s); if(e) e.scrollIntoView({ block: 'start', behavior: 'instant' }); } }"); clk.to(5.0)
            for i in range(40):
                if pg.evaluate("() => typeof BADGE_STRIKE_DRAFTS === 'undefined' || !BADGE_STRIKE_DRAFTS.size"): break
                clk.to(clk.t + 0.5); pg.wait_for_timeout(200)
            clk.to(clk.t + 0.5)
            r = rect(pg, ".badges-tab .ncase")
            imgs[(vname, "case")] = png(pg, r) if r else Image.new("RGBA", (1, 1))
            if SHOTS: png(pg).save(os.path.join(SHOTS, "%s-%s-%s-case.png" % (tag, cls, vname)))
            # a found badge in your hand
            pg.evaluate("() => { const u = unitsInTeachingOrder()[0]; const c = [...document.querySelectorAll('.badges-tab .ncase-cell')][0]; openBadgeInspect(u, c); }")
            clk.to(clk.t + 2.5)
            for i in range(40):
                if pg.evaluate("() => typeof BADGE_STRIKE_DRAFTS === 'undefined' || !BADGE_STRIKE_DRAFTS.size"): break
                clk.to(clk.t + 0.5); pg.wait_for_timeout(200)
            clk.to(clk.t + 0.3)
            imgs[(vname, "inspect (as is, glint shown)")] = png(pg)
            pg.evaluate(HIDEG)
            # (384.133 combined) what is compared is the badge in your hand: the screen behind the overlay is not it. Its title row ("Badges", dimmed
            # under the overlay) is where other builds' intended changes to the title row show (tabfeel, namebox, nodiag: a few px, 13 levels), so the
            # screen is hidden for this picture on both builds; the overlay's own glow, badge, name and Close are all still compared, pixel for pixel.
            pg.evaluate("() => { document.querySelectorAll('.binspect-pin').forEach(n => n.remove()); }")
            pg.evaluate("() => { const s = document.getElementById('stage'); if(s) s.style.visibility = 'hidden'; }"); pg.wait_for_timeout(80)
            imgs[(vname, "inspect")] = png(pg)
            pg.evaluate("() => { const s = document.getElementById('stage'); if(s) s.style.visibility = ''; }")
            pg.evaluate(SHOWG)
            if SHOTS: imgs[(vname, "inspect")].save(os.path.join(SHOTS, "%s-%s-%s-inspect.png" % (tag, cls, vname)))
            pg.evaluate("() => { try{ badgeInspectNow && badgeInspectNow.close(); }catch(e){} }"); clk.to(clk.t + 2)
            # the unit list's cards
            pg.evaluate("() => { document.querySelectorAll('.binspect').forEach(n => n.remove()); cfg.mode = 'drill'; cfg.units = []; cfg.size = 0; showSetup(); }")
            clk.to(clk.t + 2.5)
            for i in range(40):
                if pg.evaluate("() => typeof BADGE_STRIKE_DRAFTS === 'undefined' || !BADGE_STRIKE_DRAFTS.size"): break
                clk.to(clk.t + 0.5); pg.wait_for_timeout(200)
            clk.to(clk.t + 0.5)
            # the picker is built once more now that every strike is finished: a card built while a strike was still a draft can hold the draft's cached
            # picture (a blob that is dropped when the finish replaces it), which is the app's own caching and not what is compared
            pg.evaluate("() => { cfg.mode = 'drill'; cfg.units = []; cfg.size = 0; showSetup(); }")
            clk.to(clk.t + 1.5); pg.wait_for_timeout(600)
            cards = pg.evaluate("() => [...document.querySelectorAll('.pick-badge')].slice(0, 9).map(e => { e.scrollIntoView({ block: 'nearest', behavior: 'instant' }); const r = e.getBoundingClientRect(); return { x: r.left - 6, y: r.top - 6, width: r.width + 12, height: r.height + 12 }; })")
            for i, c in enumerate(cards):
                pg.evaluate("(i) => document.querySelectorAll('.pick-badge')[i].scrollIntoView({ block: 'center', behavior: 'instant' })", i)
                c = pg.evaluate("(i) => { const r = document.querySelectorAll('.pick-badge')[i].getBoundingClientRect(); return { x: r.left - 6, y: r.top - 6, width: r.width + 12, height: r.height + 12 }; }", i)
                # (384.133 combined) WHAT IS COMPARED IS THE BADGE ON THE CARD, NOT A SCREENSHOT OF THE CARD. The card's picture moves by a device pixel
                # (or is a fraction of a pixel bigger) with other builds' intended changes to the list's layout, and an SVG's edges are not the same pixels
                # at another sub-pixel offset, so a screenshot at the card's box cannot be pixel-identical across builds. The card holds the badge as
                # the struck raster (an <image class="badge-raster"> with the PNG the renderer made, or the cached strike as an <img>): that picture is read
                # back at its own size and compared pixel for pixel (the art itself, whatever the layout round it). A card with no raster (an empty or grey
                # slot, drawn as vectors) is compared by its svg's markup with the ids renumbered and the shine group taken out (the 384.108 work, on purpose).
                art = pg.evaluate("""async (i) => { const h = document.querySelectorAll('.pick-badge')[i];
                    const pi = h.querySelector('img.pick-badge-img');
                    for(let k = 0; pi && k < 20 && !(pi.complete && pi.naturalWidth > 0); k++){ try{ await pi.decode(); }catch(e){ await new Promise(r => setTimeout(r, 100)); } }
                    if(pi && pi.complete && pi.naturalWidth > 0){ const cv = document.createElement('canvas'); cv.width = pi.naturalWidth; cv.height = pi.naturalHeight; cv.getContext('2d').drawImage(pi, 0, 0); return { kind: 'raster', href: cv.toDataURL('image/png') }; }
                    const im = h.querySelector('image.badge-raster');
                    if(im) return { kind: 'raster', href: im.getAttribute('href') || im.getAttribute('xlink:href') || '' };
                    const sv = h.querySelector('svg'); if(!sv) return { kind: 'none', html: (pi ? 'IMG ' + pi.src.slice(0, 40) + ' w=' + pi.naturalWidth : h.outerHTML.slice(0, 100)) };
                    const c = sv.cloneNode(true); c.querySelectorAll('.badge-shine, [class*=shine]').forEach(n => n.remove());
                    return { kind: 'markup', html: c.outerHTML }; }""", i)
                if art["kind"] == "raster" and art["href"].startswith("data:image/png;base64,"):
                    import base64
                    imgs[(vname, "card %d" % i)] = Image.open(io.BytesIO(base64.b64decode(art["href"].split(",", 1)[1]))).convert("RGBA")
                elif art["kind"] == "markup":
                    norm = re.sub(r"\b([a-zA-Z]+)\d+-", r"\1N-", art["html"]); norm = re.sub(r"(url\(#|href=\"#|id=\")[^)\"]*", r"\1X", norm)
                    d = hashlib.sha1(norm.encode("utf-8")).digest(); im = Image.new("RGBA", (len(d), 1)); im.putdata([(b, b, b, 255) for b in d])
                    imgs[(vname, "card %d" % i)] = im
                else:
                    imgs[(vname, "card %d" % i)] = Image.new("RGBA", (1, 1))
                    CARD_UNREAD.append((vname, i, art["kind"], (art.get("html") or "")[:120]))   # a card whose art could not be read fails on its own, never as an equal pair of blanks
            if SHOTS:
                pg.evaluate("() => window.scrollTo({ top: 0, behavior: 'instant' })"); clk.to(clk.t + .2)
                png(pg).save(os.path.join(SHOTS, "%s-%s-%s-cards.png" % (tag, cls, vname)))
            errs_all += errs; ctx.close()
        # the badge-earned cutscene: a found unit flies into its slot
        if ONLY and "cutscene" not in ONLY: continue
        ctx, pg, errs = open_page(br, body, cls, w, h, dsf)
        u = pg.evaluate("() => { const u = unitsInTeachingOrder()[0]; theme.muteBanners = false; applyTheme(); document.querySelectorAll('.toast,.app-banner,.unlock-card,.update-banner,.daily-alert').forEach(n => n.remove()); try{ warmBadgeCoinFaces([u]); }catch(e){} return u; }")
        pg.wait_for_timeout(4000)
        clk = Clock(pg)
        pg.evaluate("(u) => { playBadgeCaseScene([u], () => {}, [], {}); }", u)
        for t, name in ((3.6, "coin"), (5.2, "sway"), (10.8, "open"), (15.5, "seated")):
            clk.to(t)
            pg.evaluate("() => document.querySelectorAll('.toast,.app-banner,.update-banner,.daily-alert').forEach(n => n.remove())")
            if not pg.evaluate("() => !!document.querySelector('.bc-scene')"): print("     (no .bc-scene at %.1fs in %s)" % (t, vname), flush=True)
            raw = png(pg)
            pg.evaluate(HIDEG); pg.wait_for_timeout(80)
            imgs[(vname, "cutscene %s" % name)] = png(pg)
            pg.evaluate(SHOWG); pg.wait_for_timeout(40)
            imgs[(vname, "cutscene %s (as is, glint shown)" % name)] = raw
            if SHOTS: raw.save(os.path.join(SHOTS, "%s-%s-%s-cutscene-%s.png" % (tag, cls, vname, name)))
        errs_all += errs; ctx.close()
    return imgs, tokens, errs_all

CUT_LEVELS, CUT_SHARE = 2, 0.0005
def diff(a, b):
    if a.size != b.size: return ("size", a.size, b.size)
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))   # RGB: an RGBA difference's alpha is 0 everywhere and getbbox reads alpha
    if d.getbbox() is None: return None
    px = sum(1 for p in d.getdata() if max(p) > 0)
    return ("pixels", px, max(max(p) for p in d.getdata()))

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--disable-dev-shm-usage"])
    for cls in CLASSES:
        ref = REFS[cls]
        print("\n== %s: %s against %s ==" % ("police academy" if cls == "academy" else "Fire Code", HERE_NAME, ref), flush=True)
        A, tA, eA = capture(br, HERE, cls, "here")
        B, tB, eB = capture(br, body_of(ref), cls, "ref")
        # (384.133 combined) THE CUTSCENE'S FRAMES ARE RE-TAKEN (at most twice) WHEN THEY DIFFER. The first seconds of the scene (the coin at rest, swaying)
        # carry a backdrop that fades in on the page's own clock, so on a loaded machine a whole frame can read a few levels (up to 16, every pixel of it,
        # a different frame on a different run, on either build) off the other build's. A real change to the badge, the coin or the scene is the same on
        # every take; the LAST take is the one asserted. The sheet, case, in-hand and card pictures are not re-taken.
        _cutkeys = lambda D: sorted(k for k in D if k[1].startswith("cutscene") and "(" not in k[1])
        _cutok = lambda A_, B_: all((k not in A_) or (not diff(A_[k], B_[k])) or (diff(A_[k], B_[k])[0] == "pixels" and diff(A_[k], B_[k])[2] <= CUT_LEVELS and diff(A_[k], B_[k])[1] <= CUT_SHARE * A_[k].width * A_[k].height) for k in _cutkeys(B_))
        for _take in range(2):
            if _cutok(A, B): break
            print("     (the cutscene's frames differ: taken again, %d of 2)" % (_take + 1), flush=True)
            _keep = set(ONLY); ONLY.clear(); ONLY.add("cutscene")
            A2, _, _ = capture(br, HERE, cls, "here"); B2, _, _ = capture(br, body_of(ref), cls, "ref")
            ONLY.clear(); ONLY.update(_keep)
            for k in _cutkeys(B2):
                if k in A2: A[k] = A2[k]; B[k] = B2[k]
        units = list(tB.keys())
        chk("(1) %s: the unit list is the reference's (%d units)" % (cls, len(units)), list(tA.keys()) == units, [len(tA), len(units)])
        tdif = [u for u in units if tA.get(u) != tB[u]]
        chk("(2) %s: every token's own pixels (found and grey, dirt 0-4, 132 and 84 px) equal the reference's: %d of %d units differ %s" % (cls, len(tdif), len(units), tdif[:4]), not tdif, tdif[:8])
        for group, keyf in (("(1) the sheet", lambda k: k[1].startswith("sheet")), ("(3) the case", lambda k: k[1] == "case"),
                            ("(3) a badge in your hand (glint layers hidden on both)", lambda k: k[1] == "inspect"), ("(3) the unit cards", lambda k: k[1].startswith("card")),
                            ("(3) the earned cutscene (glint layers hidden on both; the shine's layer allowance, %d levels on %.2f%% of the frame)" % (CUT_LEVELS, CUT_SHARE * 100), lambda k: k[1].startswith("cutscene") and "(" not in k[1])):
            keys = sorted(k for k in B if keyf(k))
            if not keys and ONLY: continue
            miss = [k for k in keys if k not in A]
            bad = [(k, diff(A[k], B[k])) for k in keys if k in A]
            if "cutscene" in group:
                # (384.108, kept) the coin's glint band now waits on its own compositor layer from the start of the scene, and a promoted
                # layer rounds the coin under it by a level or two: at most CUT_LEVELS on at most CUT_SHARE of the frame is that
                bad = [x for x in bad if x[1] and not (x[1][0] == "pixels" and x[1][2] <= CUT_LEVELS and x[1][1] <= CUT_SHARE * A[x[0]].width * A[x[0]].height)]
                if [x for x in [(k, diff(A[k], B[k])) for k in keys if k in A] if x[1]]: print("     (within the shine's layer allowance) %s" % [(k, diff(A[k], B[k])) for k in keys if k in A and diff(A[k], B[k])], flush=True)
            bad = [x for x in bad if x[1]]
            chk("%s, %s: %d images at 440x956@3 and 834x1194@2 pixel-identical with the reference: %s" % (group, cls, len(keys), "all identical" if not bad and not miss else "%d differ" % (len(bad) + len(miss))),
                keys and not bad and not miss, (miss[:3], bad[:6]))
        info = [(k, diff(A[k], B[k])) for k in sorted(B) if "(" in k[1] and k in A]
        print("     (info, not asserted) the in-hand view and the cutscene's frames as they are, glint shown (the 384.108 shine differs from main on purpose): %s" % [(k[0], k[1], d) for k, d in info], flush=True)
        chk("(3) %s: the art of every one of the nine unit cards was read (a raster or markup, never a blank): unread %s" % (cls, CARD_UNREAD[:4]), not CARD_UNREAD, CARD_UNREAD[:6])
        chk("(4) %s: no page errors" % cls, not eA and not eB, (eA + eB)[:4])
        if SHOTS:
            for k in sorted(B):
                if k in A and (k[1] in ("case", "inspect") or k[1].startswith("cutscene") or k[1] == "card 0"):
                    a, b = A[k], B[k]; s = Image.new("RGBA", (a.width + b.width + 10, max(a.height, b.height)), (40, 40, 40, 255)); s.paste(a, (0, 0)); s.paste(b, (a.width + 10, 0))
                    s.save(os.path.join(SHOTS, "pair-%s-%s-%s.png" % (cls, k[0], re.sub(r"[^a-z0-9]+", "-", k[1].lower()).strip("-"))))
    br.close()
srv.shutdown()
print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
