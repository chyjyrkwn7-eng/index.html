"""Build 384.101: a badge's glint is smooth - it moves on the compositor, inside the badge, and it hands over without a pop.
Madison, on his installed iPhone: "When the badge comes up, the part where it shines comes up laggy, it's not a smooth transition.
It's smooth, needs to be smoother, it like glistens but needs to do it smoother."

THE CAUSE, traced in Chromium (440x956 at 3x, CPU x4) on the build before: the glint that crosses a badge as it goes into its slot
was a rect INSIDE the badge's SVG behind an SVG mask, moved by a CSS transform. An SVG child's transform is not run by the
compositor (WebKit's or Chromium's), so the whole masked drawing was painted again on every frame of the glint (25 paints of the
badge's svg in its 1.3s). On the coin, the turning light was sampled 37 degrees apart in the first turns (its passes flashed at .65
on one turn and 1 the next), it was left lit at .74 when the coin came to rest, and the glint snapped it off and began again.

Read off the page (nothing typed as a label; the numbers are the page's own or a pixel's):
 (1) THE SLOT'S GLINT, TRACED (the whole badge-earned scene, one new badge into a case of four): during the glint (its active phase,
     read off its own animations) no Paint event names the badge's drawing (its svg) or anything in its slot.
 (2) ONLY TRANSFORM AND OPACITY, ON AN HTML LAYER: every animation of a glint or a turning light (the slot's, the coin's glint at
     rest, the spin's two lights) animates nothing but transform and opacity, and its target is an HTML element (not inside an SVG).
 (3) PROMOTED BEFORE IT RUNS: at the seat, before its glint starts, the glint's band exists and is already promoted (will-change
     transform), so its first frame is not a new layer.
 (4) INSIDE THE BADGE: at the band's peak (the most-lit of 35/50/65% of its run, every animation paused there), the pixels the glint
     changes are all inside the badge's silhouette (the footprint drawn by the same mask filled solid, dilated 2 device px; a fringe of 0.05% of it at most) - the
     slot and the coin, in the academy and Fire Code; nothing outside the badge changes. And the coin's light mask itself reaches
     no further than the badge's own drawing (its face picture and edge, dilated 2 device px; 2% of the mask at most): a raised pin has no keyline rim,
     and a mask with one lights the dark round its edge (claude/b384-objbadges' pins, on that branch alone).
 (5) AND IT VISIBLY RUNS: at that peak it lights part of the badge (a brightest change of at least 40 levels over at least 2% of the
     silhouette), and it travels left to right (the lit pixels' middle moves right from 35% to 65%).
 (6) THE COIN HANDS OVER WITHOUT A POP: across the moment its glint begins (40ms either side; the spin is over and the sway not
     begun), nothing on the coin's face (its silhouette, eroded 2 device px) changes by more than 16 levels (0.2% of it at most).
 (7) EVERY TURN'S SHIMMER IS THE SAME: in the spin's own keyframes, each pass of the light over a face peaks at at least .9 of the
     brightest pass, and no two neighbouring samples are more than 6 degrees of turn apart.
 (8) THE BADGES SCREEN: no found badge's drawing carries a glint inside it (a displayed .badge-shine mask group: the old band, a mask
     every repaint of every badge paid for); its case has no lid to glint (the tray has had none since round 10, so the lid glint in
     openBadgeCaseLid cannot run) and its count medal no sheen (::after content none since build 270); anything moving on a badge
     there is transform/opacity on HTML.
 (9) REDUCE MOTION: the still scene runs no glint.     (10) no page errors.

Run:  python3 tools/check-b384-shine.py [--against FILE|REV] [--shots DIR]   (ONLY=1,4 runs those; --against origin/main must FAIL:
      (1), (2), (3), (6), (7), (8))"""
import io, json, os, re, subprocess, sys, time, functools, http.server, socket, threading, glob, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
def body_of(arg):
    if os.path.exists(arg): return open(arg, encoding="utf-8").read()
    return subprocess.run(["git", "-C", ROOT, "show", arg + ":index.html"], capture_output=True, text=True, check=True).stdout
BODY = body_of(sys.argv[sys.argv.index("--against") + 1]) if "--against" in sys.argv else open(ROOT + "/index.html", encoding="utf-8").read()
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
if SHOTS: os.makedirs(SHOTS, exist_ok=True)
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}
def want(n): return not ONLY or str(n) in ONLY
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageFilter
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
_m = re.search(r'const APP_BUILD = "([^"]+)"', BODY); SERVED = _m.group(1) if _m else ""
# an existing, up-to-date account: nothing lands over what is measured
SEED = {"onboardingComplete": True, "firstName": "Maddog", "avatarChar": "ninja", "publicId": "xph5b57jbp5a", "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30, "longestStreak": 20, "currentStreak": 3}}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted"]
def init_js(cls):
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    return s + " }catch(e){} })()"
def page(br, cls="academy", reduce=False, clock=False):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=3, has_touch=True, is_mobile=True,
                         reduced_motion="reduce" if reduce else "no-preference")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js(cls))
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % SERVED))
    pg.goto("http://127.0.0.1:%d/index.html" % port, timeout=180000); pg.wait_for_timeout(3500)   # (a 10MB page on a busy machine)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    # four badges in the case and the fifth the new one; the case's renders warmed as a results screen warms them
    unit = pg.evaluate("""(reduce)=>{ const us = unitsInTeachingOrder(); store.unitPerfects = store.unitPerfects || {};
      us.slice(0, 5).forEach(u => { store.unitPerfects[u] = badgeThresholdFor(u); }); saveStore();
      theme.muteBanners = false; theme.reduceMotion = !!reduce; applyTheme(); showHome();
      document.querySelectorAll('.rs-spot,.daily-alert,#tour-overlay,.update-banner,.toast,.unlock-card,#pushing-update,#intro-pop,.app-banner').forEach(n => n.remove());
      try{ warmBadgeCoinFaces([us[4]]); }catch(e){} return us[4]; }""", reduce)
    pg.wait_for_timeout(6000)
    return ctx, pg, errs, unit

# ---- what is a glint, on any build: the band (HTML or the old SVG rect) and the spin's turning light ----
FIND = r"""(where) => {
  const scene = document.querySelector('.bc-scene');
  const shine = el => !!(el && el.matches && el.matches('.badge-glint-band, .badge-shine-band, .badge-shine, .ncase-glint, .ncase-glint *, .bc-spec i'));
  const root = where === 'slot' ? document.querySelector('.bc-slot.is-new') : where === 'coin' ? document.querySelector('.bc-flyer .bc-face.is-front')
             : where === 'tab' ? document.querySelector('.badges-tab .nova-case') : scene;
  if(!root) return null;
  const L = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && root.contains(t) && shine(t); });
  return L.map(a => { const t = a.effect.target, tm = a.effect.getTiming(), kf = a.effect.getKeyframes();
    const props = [...new Set(kf.flatMap(k => Object.keys(k)))].filter(p => !['offset', 'computedOffset', 'easing', 'composite'].includes(p));
    return { cls: (t.getAttribute('class') || t.tagName), html: t instanceof HTMLElement && !t.closest('svg'), props,
             delay: tm.delay || 0, dur: Number(tm.duration) || 0, start: a.startTime, name: a.animationName || '', n: kf.length,
             peaks: kf.map(k => k.opacity === undefined ? null : +k.opacity), offs: kf.map(k => k.computedOffset) }; }); }"""

def traced(br):
    """(1)(2)(3): the whole scene on the real clock, traced; the glint's window read off its own animations"""
    ctx, pg, errs, unit = page(br)
    cdp = ctx.new_cdp_session(pg)
    evs, done = [], []
    cdp.on("Tracing.dataCollected", lambda p: evs.extend(p["value"]))
    cdp.on("Tracing.tracingComplete", lambda p: done.append(1))
    cdp.send("Tracing.start", {"categories": "devtools.timeline,disabled-by-default-devtools.timeline,blink.animations", "transferMode": "ReportEvents"})
    pg.wait_for_timeout(600)    # the renderer takes the categories up a beat after Tracing.start returns
    pg.evaluate(r"""(u) => { window.__sh = { seat: null, pre: null };
      new MutationObserver(ms => { for(const m of ms){ const t = m.target;
        if(t.classList && t.classList.contains('bc-slot') && t.classList.contains('is-new') && !window.__sh.seat){
          window.__sh.seat = performance.now();
          const b = t.querySelector('.badge-glint-band, .badge-shine-band');
          window.__sh.pre = b ? { has: true, wc: getComputedStyle(b).willChange, html: b instanceof HTMLElement } : { has: false }; } } })
        .observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] });
      window.__sh.scene = performance.now();
      window.__done = 0; playBadgeCaseScene([u], () => { window.__done = 1; }, [], {}); }""", unit)
    slot = coin = None; t0 = time.time()
    while time.time() - t0 < 120:
        if coin is None and pg.evaluate("()=>!!document.querySelector('.bc-flyer .bc-face.is-front') && document.getAnimations().some(a => a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest('.bc-face.is-front') && a.playState === 'running')"):
            pg.wait_for_timeout(200); coin = pg.evaluate(FIND, "coin")
        if slot is None and pg.evaluate("()=>!!window.__sh.seat"):
            pg.wait_for_timeout(120); slot = pg.evaluate(FIND, "slot")
        if pg.evaluate("()=>window.__done"): break
        pg.wait_for_timeout(100)
    sh = pg.evaluate("()=>window.__sh")
    cdp.send("Tracing.end")
    for _ in range(1200):
        if done: break
        pg.wait_for_timeout(100)   # (a sleep would not pump the session: the trace arrives only while Playwright is called)
    ctx.close()
    return {"unit": unit, "slot": slot or [], "coin": coin or [], "sh": sh, "evs": evs, "errs": errs}

def traced_coin_glint(br):
    """the coin's glint at rest, as the page makes it (BC_T.glint), read on the real clock"""
    ctx, pg, errs, unit = page(br)
    pg.evaluate("(u) => { playBadgeCaseScene([u], () => {}, [], {}); }", unit)
    gl = pg.evaluate("()=>BC_T.glint")
    pg.wait_for_timeout(gl)
    g = []; t0 = time.time()
    while time.time() - t0 < 30:     # the scene's own timer, however late a busy machine runs it
        g = pg.evaluate(FIND, "coin") or []
        if any(x["n"] <= 60 for x in g): break
        pg.wait_for_timeout(150)
    ctx.close()
    return g, errs

# ---- the clock stopped: every animation seeked to t (as check-behaviour's _Stepper) ----
SEEK = """(t) => { const M = window.__t0s = window.__t0s || new WeakMap();
  document.getAnimations().forEach(an => {
    if(!M.has(an)) M.set(an, { at: t, from: an.currentTime || 0, done: false });
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
# the band(s) of a glint, hidden or filled solid (the footprint of its own mask), on any build
BANDS = r"""(where) => { const root = where === 'slot' ? document.querySelector('.bc-slot.is-new') : document.querySelector('.bc-flyer .bc-face.is-front');
  return root ? [...root.querySelectorAll('.badge-glint-band, .badge-shine-band, .bc-spec i')] : []; }"""
HIDE = "(where) => { (" + BANDS + ")(where).forEach(b => { b.__vis = b.style.visibility; b.style.visibility = 'hidden'; }); }"
SHOW = "(where) => { (" + BANDS + ")(where).forEach(b => { b.style.visibility = b.__vis || ''; }); }"
# the footprint: a solid fill put INSIDE the glint's own masked box (the HTML mask, or the old SVG mask group), so it is cut by the
# very mask the glint is cut by - and nothing of the glint itself is touched (its animations keep their place)
SOLID = r"""([where, col]) => { const root = where === 'slot' ? document.querySelector('.bc-slot.is-new') : document.querySelector('.bc-flyer .bc-face.is-front');
  if(!root) return 0; let n = 0;
  root.querySelectorAll('.__fp').forEach(e => e.remove());
  if(col === null) return 0;
  [...root.querySelectorAll('.badge-glint, .bc-spec, g.badge-shine')].forEach(c => {
    if(c instanceof SVGElement){ const r = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      r.setAttribute('class', '__fp'); r.setAttribute('x', '-300'); r.setAttribute('y', '-300'); r.setAttribute('width', '800'); r.setAttribute('height', '800');
      r.setAttribute('fill', col); c.appendChild(r); }
    else { const d = document.createElement('div'); d.className = '__fp'; d.style.cssText = 'position:absolute;left:-60%;top:-60%;width:220%;height:220%;background:' + col; c.appendChild(d); }
    n++; });
  return n; }"""
BOX = r"""(where) => { const e = where === 'slot' ? document.querySelector('.bc-slot.is-new') : document.querySelector('.bc-flyer');
  if(!e) return null; const r = e.getBoundingClientRect(), m = where === 'slot' ? .35 : .12;
  return { x: Math.max(0, r.left - r.width * m), y: Math.max(0, r.top - r.height * m), width: r.width * (1 + 2 * m), height: r.height * (1 + 2 * m) }; }"""
def shot(pg, box):
    return Image.open(io.BytesIO(pg.screenshot(clip=box))).convert("RGB")
def chdiff(a, b):
    d = ImageChops.difference(a, b).split()
    return ImageChops.lighter(ImageChops.lighter(d[0], d[1]), d[2])    # the largest channel change, per pixel
def footprint(pg, where, box, base):
    """the badge's silhouette on screen: the glint's own mask filled solid (green, then magenta), against the hidden shot"""
    fp = None
    for col in ("#00FF00", "#FF00FF"):
        pg.evaluate(SOLID, [where, col]); pg.wait_for_timeout(120)
        m = chdiff(shot(pg, box), base).point(lambda v: 255 if v > 60 else 0)
        fp = m if fp is None else ImageChops.lighter(fp, m)
    pg.evaluate(SOLID, [where, None]); pg.wait_for_timeout(60)
    return fp

def pixel_run(br, cls, label, shots_tag):
    """(4)(5)(6) on the stopped clock: the coin's glint at rest, the hand-over into it, and the slot's glint"""
    ctx, pg, errs, unit = page(br, cls)
    clk = Clock(pg)
    pg.evaluate("(u) => { playBadgeCaseScene([u], () => {}, [], {}); }", unit)
    T = pg.evaluate("()=>({ glint: BC_T.glint, seat: BC_T.fly + BC_T.flyMs })")
    out = {"unit": unit, "label": label}
    # the coin: its face just before and just after its glint begins (nothing else on the face moves then: the spin is over and
    # the sway not begun), compared inside the face's silhouette, eroded 2 device px
    clk.to(T["glint"] / 1000 - 0.04)
    cbox = pg.evaluate(BOX, "coin")
    A = shot(pg, cbox)
    pg.evaluate(HIDE, "coin"); pg.wait_for_timeout(60); A0 = shot(pg, cbox); pg.evaluate(SHOW, "coin")
    fpRaw = footprint(pg, "coin", cbox, A0)
    fpA = fpRaw.filter(ImageFilter.MinFilter(5))
    # the light's mask against the badge's own drawing (the face's picture and its edge, hidden): the mask may not reach past it -
    # a raised pin has no keyline rim, and a mask with one lights the dark round its edge
    ART = "(v) => document.querySelectorAll('.bc-flyer .bc-face-art, .bc-flyer .bc-edge').forEach(e => e.style.visibility = v)"
    pg.evaluate(ART, "hidden"); pg.wait_for_timeout(60); noart = shot(pg, cbox); pg.evaluate(ART, "")
    art = chdiff(A0, noart).point(lambda v: 255 if v > 10 else 0).filter(ImageFilter.MaxFilter(5))
    mk = list(fpRaw.getdata()); ar = list(art.getdata())
    out["spill"] = {"outside_drawing": sum(1 for m, a in zip(mk, ar) if m and not a), "mask": max(1, sum(1 for m in mk if m))}
    if SHOTS: art.save(os.path.join(SHOTS, "%s-coin-drawing.png" % shots_tag)); fpRaw.save(os.path.join(SHOTS, "%s-coin-mask.png" % shots_tag))
    clk.to(T["glint"] / 1000 + 0.04)
    B = shot(pg, cbox)
    dd = list(chdiff(A, B).getdata()); fa = list(fpA.getdata())
    n_fp = max(1, sum(1 for v in fa if v))
    out["handover"] = {"changed": sum(1 for v, i in zip(dd, fa) if i and v > 16), "of": n_fp,
                       "max": max([v for v, i in zip(dd, fa) if i] or [0])}
    if SHOTS:
        A.save(os.path.join(SHOTS, "%s-coin-handover-before.png" % shots_tag)); B.save(os.path.join(SHOTS, "%s-coin-handover-after.png" % shots_tag))
    def run_glint(where, t_start, dur, tag):
        stats = []; fp_n = 0
        for f in (.35, .5, .65):
            clk.to(t_start + f * dur)
            box = pg.evaluate(BOX, where)
            if not box: continue
            lit = shot(pg, box)
            pg.evaluate(HIDE, where); pg.wait_for_timeout(60); base = shot(pg, box); pg.evaluate(SHOW, where)
            d = chdiff(lit, base)
            # the silhouette at this very moment (the coin sways between samples)
            fp = footprint(pg, where, box, base)
            inside = fp.filter(ImageFilter.MaxFilter(5))     # dilated 2 device px
            n_in = sum(1 for v in fp.getdata() if v); fp_n = max(fp_n, n_in)
            dl = list(d.getdata()); ins = list(inside.getdata()); fpd = list(fp.getdata()); W = d.width
            out_px = sum(1 for v, i in zip(dl, ins) if v > 10 and not i)
            in_max = max([v for v, i in zip(dl, fpd) if i] or [0])
            lit_px = [(k % W) for k, (v, i) in enumerate(zip(dl, fpd)) if i and v >= 16]
            stats.append({"f": f, "outside_changed": out_px, "inside_max": in_max, "lit_share": round(len(lit_px) / max(1, n_in), 3),
                          "lit_mid_x": round(sum(lit_px) / len(lit_px), 1) if lit_px else None, "fp_px": n_in})
            if SHOTS:
                lit.save(os.path.join(SHOTS, "%s-%s-%02d-lit.png" % (shots_tag, where, int(f * 100))))
                d.point(lambda v: min(255, v * 4)).save(os.path.join(SHOTS, "%s-%s-%02d-diff.png" % (shots_tag, where, int(f * 100))))
                fp.save(os.path.join(SHOTS, "%s-%s-%02d-footprint.png" % (shots_tag, where, int(f * 100))))
        return {"stats": stats, "fp_px": fp_n}
    # the coin's glint at rest: its window read off its own animations
    clk.to(T["glint"] / 1000 + 0.1)
    cg = pg.evaluate(FIND, "coin") or []
    cg = [a for a in cg if a["dur"] and a["dur"] < 3000 and not a["n"] > 60]   # the glint, not the spin's turning light
    if cg:
        dur = max(a["dur"] for a in cg) / 1000; dl = max(a["delay"] for a in cg) / 1000
        out["coin"] = run_glint("coin", T["glint"] / 1000 + dl, dur, shots_tag)
    # the slot's glint, after the seat
    clk.to(T["seat"] / 1000 + 0.05)
    sg = pg.evaluate(FIND, "slot") or []
    if sg:
        dur = max(a["dur"] for a in sg) / 1000; dl = max(a["delay"] for a in sg) / 1000
        out["slot"] = run_glint("slot", T["seat"] / 1000 + dl, dur, shots_tag)
    out["errs"] = errs
    ctx.close()
    return out

def judge_glint(label, where, r):
    st = (r or {}).get("stats") or []
    if not st:
        chk("(4) %s, the %s's glint: found and sampled" % (label, where), False, r); return
    outside = max(s["outside_changed"] for s in st)
    peak = max(st, key=lambda s: (s["inside_max"], s["lit_share"]))
    # a fringe of a few pixels where the mask's own soft edge is wider than the 2px allowance (a rimless pin turned in 3D) is the edge,
    # not light past it; a band across the square slot would be thousands
    fp_n = max(s["fp_px"] for s in st)
    chk("(4) %s, the %s's glint at its peak (and either side of it) changes nothing outside the badge's silhouette (pixels changed >10 outside it: %s, of a %d-pixel silhouette)"
        % (label, where, [s["outside_changed"] for s in st], fp_n), outside <= fp_n * .0005, st)
    chk("(5) %s, the %s's glint visibly runs: at its peak it lights the badge (brightest change %d levels over %.1f%% of the silhouette)"
        % (label, where, peak["inside_max"], 100 * peak["lit_share"]), peak["inside_max"] >= 40 and peak["lit_share"] >= .02, st)
    xs = [s["lit_mid_x"] for s in st if s["lit_mid_x"] is not None]
    chk("(5) %s, the %s's glint travels left to right across it (the lit pixels' middle, where lit: %s)" % (label, where, xs),
        len(xs) >= 2 and all(b > a for a, b in zip(xs, xs[1:])), st)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    errs_all = []
    if want(1) or want(2) or want(3):
        r = traced(br); errs_all += r["errs"]
        evs = r["evs"]
        slot = r["slot"]
        if want(1):
            # the window on the trace's own clock: the slot's glint is the last glint of the scene to begin (its Animation event,
            # blink.animations); its active phase from there + its delay, for its duration (both read off the page's animation)
            begins = sorted(e["ts"] / 1000.0 for e in evs if e.get("name") == "Animation" and e.get("ph") == "b"
                            and re.search(r"badge-(glint|shine)-band", (e.get("args", {}).get("data", {}) or {}).get("nodeName", "")))
            if begins and slot:
                a = begins[-1] + max(x["delay"] for x in slot); b = a + max(x["dur"] for x in slot)
                P = [e for e in evs if e.get("name") == "Paint" and a <= e["ts"] / 1000.0 <= b]
                nodes = [e["args"]["data"].get("nodeName", "") for e in P]
                bad = [n for n in nodes if re.search(r"badge-art|badge-shine|badge-glint|bc-slot", n)]
                when = [(round(e["ts"] / 1000.0 - a), e["args"]["data"].get("nodeName", "")[:40]) for e in P if re.search(r"badge-art|badge-shine|badge-glint|bc-slot", e["args"]["data"].get("nodeName", ""))]
                near = [(round(e["ts"] / 1000.0 - a), e["args"]["data"].get("nodeName", "")[:40]) for e in evs if e.get("name") == "Paint" and a - 900 <= e["ts"] / 1000.0 <= a + 200]
                chk("(1) during the slot's glint (%.0fms, read off its animations) no paint names the badge's drawing or its slot (%d such paints of %d in the window)"
                    % (b - a, len(bad), len(P)), len(bad) == 0, {"at_ms": when[:8], "paints_around_start": near[:20]})
            else:
                chk("(1) the slot's glint was found and traced", False, {"slot": slot, "begins": len(begins)})
        if want(2):
            g2, e2 = traced_coin_glint(br); errs_all += e2
            spin = [x for x in (r["coin"] or g2) if x["n"] > 60] or [x for x in g2 if x["n"] > 60]   # (filled forwards, still on the face at rest)
            glint_coin = [x for x in g2 if x["n"] <= 60]
            every = [("the slot's glint", slot), ("the coin's glint at rest", glint_coin), ("the spin's turning light", spin)]
            for nm, L in every:
                props = sorted(set(p for x in L for p in x["props"]))
                chk("(2) %s: %d animations, all on HTML elements (none inside an SVG) and animating only transform/opacity (%s; on %s)"
                    % (nm, len(L), props, sorted(set(x["cls"] for x in L))),
                    bool(L) and all(x["html"] for x in L) and set(props) <= {"transform", "opacity", "translate"}, L)
        if want(3):
            pre = r["sh"].get("pre") or {}
            chk("(3) at the seat, before its glint runs, the glint's band exists on an HTML layer and is already promoted (will-change: %s)" % pre.get("wc"),
                pre.get("has") and pre.get("html") and "transform" in str(pre.get("wc")), pre)
    if want(4) or want(5) or want(6):
        for cls, label in (("academy", "the academy"), ("ifc", "Fire Code")):
            for attempt in range(3):     # a renderer killed by a busy machine (out of memory) is the machine's, not the page's: again
                try:
                    o = pixel_run(br, cls, label, cls); break
                except Exception as ex:
                    if "crash" not in str(ex).lower() and "closed" not in str(ex).lower() or attempt == 2: raise
                    print("   (%s: the page's renderer was killed - running it again)" % label, flush=True)
                    for c in list(br.contexts):
                        try: c.close()
                        except Exception: pass
            errs_all += o["errs"]
            if want(4) or want(5):
                judge_glint(label + " (" + o["unit"][:28] + ")", "coin", o.get("coin"))
                judge_glint(label + " (" + o["unit"][:28] + ")", "slot", o.get("slot"))
            if want(4):
                sp = o["spill"]
                chk("(4) %s: the coin's light is cut to the badge's own drawing - its mask reaches past the drawing (dilated 2px) at %d of %d pixels"
                    % (label, sp["outside_drawing"], sp["mask"]), sp["outside_drawing"] <= sp["mask"] * .02, sp)   # a dark keyline on the dark backdrop reads faintly; a rim a pin lacks was 10% of it
            if want(6):
                h = o["handover"]
                chk("(6) %s: across the moment the coin's glint begins (80ms), nothing on its face changes by more than 16 levels (%d of %d face pixels do; largest %d)"
                    % (label, h["changed"], h["of"], h["max"]), h["changed"] <= h["of"] * .002, h)
    if want(7):
        ctx, pg, errs, unit = page(br)
        res = pg.evaluate(r"""(u) => { playBadgeCaseScene([u], () => {}, [], {}); const t0 = performance.now(); return new Promise(res => { const look = () => {
          const sp = document.querySelector('.bc-flyer .bc-spin'), out = {};
          const spinA = sp && sp.getAnimations()[0];
          if(!spinA && performance.now() - t0 < 30000){ setTimeout(look, 150); return; }   /* the scene's own timer, however late */
          const th = spinA ? spinA.effect.getKeyframes().map(k => parseFloat(/rotateY\(([-\d.]+)deg\)/.exec(k.transform)[1])) : [];
          out.maxStep = th.reduce((m, v, i) => i ? Math.max(m, Math.abs(v - th[i - 1])) : m, 0);
          out.passes = {};
          ['is-front', 'is-back'].forEach(side => { const i = document.querySelector('.bc-flyer .bc-face.' + side + ' .bc-spec i');
            const a = i && i.getAnimations().find(a => a.effect.getKeyframes().length > 20);
            const o = a ? a.effect.getKeyframes().map(k => +k.opacity) : [];
            const pk = []; for(let k = 1; k < o.length - 1; k++) if(o[k] >= o[k - 1] && o[k] > o[k + 1] && o[k] > .05) pk.push(+o[k].toFixed(2));
            out.passes[side] = pk; });
          res(out); }; setTimeout(look, BC_T.coin + 200); }); }""", unit)
        errs_all += errs; ctx.close()
        allp = res["passes"].get("is-front", []) + res["passes"].get("is-back", [])
        chk("(7) every pass of the spin's light over a face peaks at >= .9 of the brightest (front %s, back %s)" % (res["passes"].get("is-front"), res["passes"].get("is-back")),
            len(allp) >= 4 and min(allp) >= .9 * max(allp), res)
        chk("(7) ... and no two neighbouring samples of the spin are more than 6 degrees of turn apart (largest step %.1f deg)" % res["maxStep"], res["maxStep"] <= 6, res)
    if want(8):
        ctx, pg, errs, unit = page(br)
        r8 = pg.evaluate(r"""() => new Promise(res => { try{ showRanksScreen('badges'); }catch(e){ res({ err: String(e) }); return; }
          setTimeout(() => { const tab = document.querySelector('.badges-tab'); if(!tab){ res({ err: 'no badges screen' }); return; }
            const arts = [...tab.querySelectorAll('svg.badge-art.is-earned')];
            const inSvg = arts.filter(s => [...s.querySelectorAll('.badge-shine, .badge-shine-band')].some(g => getComputedStyle(g).display !== 'none')).length;
            const masks = arts.reduce((n, s) => n + s.querySelectorAll('mask').length, 0);
            const medal = tab.querySelector('.badges-medal');
            const sheen = medal ? getComputedStyle(medal, '::after').content : 'none';
            const moving = tab.getAnimations({ subtree: true }).filter(a => { const t = a.effect && a.effect.target; return t && t.closest && t.closest('.ncase-cell, .badges-medal'); });
            const props = [...new Set(moving.flatMap(a => a.effect.getKeyframes().flatMap(k => Object.keys(k))))].filter(p => !['offset', 'computedOffset', 'easing', 'composite'].includes(p));
            res({ earned: arts.length, inSvg, masks, lids: tab.querySelectorAll('.ncase-lid').length, sheen, moving: moving.length, props,
                  html: moving.every(a => a.effect.target instanceof HTMLElement && !a.effect.target.closest('svg')) }); }, 2500); })""")
        errs_all += errs; ctx.close()
        r8 = r8 or {}
        chk("(8) the Badges screen: no found badge's drawing carries a glint inside it (%s of %s do; %s masks in them) - nothing there repaints a drawing to shine"
            % (r8.get("inSvg"), r8.get("earned"), r8.get("masks")), r8.get("earned") and r8.get("inSvg") == 0, r8)
        chk("(8) ... its case has no lid to glint as it opens (%s) and its count medal no sheen (::after %s); anything moving on a badge there is transform/opacity on HTML (%d: %s)"
            % (r8.get("lids"), r8.get("sheen"), r8.get("moving") or 0, r8.get("props")),
            r8.get("lids") == 0 and r8.get("sheen") in ("none", "normal") and r8.get("html") and set(r8.get("props") or []) <= {"transform", "opacity", "translate", "scale"}, r8)
    if want(9):
        ctx, pg, errs, unit = page(br, reduce=True)
        r9 = pg.evaluate(r"""(u) => new Promise(res => { playBadgeCaseScene([u], () => {}, [], {}); setTimeout(() => {
          const s = document.querySelector('.bc-scene');
          const n = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && s && s.contains(t) && t.matches('.badge-glint-band, .badge-shine-band, .badge-glint, .ncase-glint *') && a.playState !== 'finished'; }).length;
          res({ still: !!(s && s.classList.contains('bc-still')), glints: n }); }, 1200); })""", unit)
        errs_all += errs; ctx.close()
        chk("(9) Reduce motion: the still scene (%s) runs no glint (%d)" % (r9.get("still"), r9.get("glints")), r9.get("still") and r9.get("glints") == 0, r9)
    chk("(10) no page errors", not errs_all, errs_all[:5])
    br.close()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
