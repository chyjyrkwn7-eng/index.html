#!/usr/bin/env python3
"""Build 384 round 6: the results screen's new order, held as SHAPE (no label strings, no typed thresholds read off a
design - the numbers are read off the page).

Madison: "The hundo effect should probably come up before the xp ... what if the grade box was centered, then slid up or
moved up when it was done, then the xp box, and then unlock and whatever else" / "the academy firework effect where most
of it comes off screen.. and the transition is bad because it's like grade, xp, dark, hundo effect. Don't do the darkened
thing any, ensure the tap to skip thing is in place."

On REAL runs (a drill through summarize(), lib_realrun, the page's clock stepped):
 (F1) a 100% run: while the effect plays the grade card is centred in the viewport (both axes) and nothing else of the
      results is on screen
 (F2) no dim: at no sample through the effect is there a .hfx-dim, or any layer outside the results that covers the
      viewport with a dark fill (alpha > .05) - the Thermal Camera's display is the one named exception (the effect IS
      the screen turned into a camera view)
 (F3) the grade's way up: afterwards its top is its place at the top of the stack (under the header, nothing between),
      and while it moves its layout box does not (a transform: `translate`)
 (F4) the XP card is shown only once the grade has settled; (F5) the unlock card only after the XP card (a Fire Code
      chapter's badge: its case cutscene still plays, after the settled grade)
 (F6) a tap on the page while the effect plays: within 300ms the effect's layers are gone, the grade is in its place,
      nothing on the grade is still running; Enter does the same
 (F7) the skip hint (data-skip-hint) is up, legible and clear of the card while the effect plays
 (F8) every effect, both classes, keeps >= 85% of its painted PIECES inside the viewport at its peak (before its exit, the last 15% of its time) and on average
      through the middle half of it, on an iPhone SE, a 17 Pro Max, an iPad Pro 11" and a laptop - a piece is anything
      painted up to half the screen's area and narrower and shorter than 90% of it, weighted by area and opacity (a wash,
      a corner beam, a ring sweeping the whole screen or a strip spanning it is atmosphere and meant to run off the edges); fireworks: the particles themselves, which the canvas
      would clip. The app's top bar (the status bar and the title bar under it on a phone) counts as off the screen
 (F9) reduce motion: nothing is offset, no hint, everything in its place
 (F10) a run short of 100: the same order without an effect (centred, then up, then the XP card)

  python3 tools/check-b384-results-flow.py [--quick] [--against OLD_INDEX] [--only F8] [--fx fireworks,ufo]
--quick: F8 on the SE and the Pro Max only."""
import importlib.util, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
QUICK = "--quick" in args
ONLY = None
if "--only" in args:
    i = args.index("--only"); ONLY = args[i + 1].split(","); del args[i:i + 2]
FXONLY = None
if "--fx" in args:
    i = args.index("--fx"); FXONLY = args[i + 1].split(","); del args[i:i + 2]
AG = []
if "--against" in args:
    i = args.index("--against"); AG = ["--against", os.path.abspath(args[i + 1])]
sys.argv = [sys.argv[0]] + AG
spec = importlib.util.spec_from_file_location("rr", HERE + "/lib_realrun.py")
rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)
from playwright.sync_api import sync_playwright

ok = True
def ck(name, cond, detail=""):
    global ok
    print(" ", "PASS" if cond else "FAIL", name, ("-> " + str(detail)[:400]) if detail != "" else "", flush=True)
    if not cond: ok = False
def want(k): return ONLY is None or k in ONLY

SE, MAX, IPAD, LAP = (375, 667), (440, 956), (834, 1194), (1366, 638)
# each one as it is INSTALLED (the real safe-area insets put in for env(), as tools/sim-safe-area.py does): on a phone the
# status bar takes the top 20-62px and the app's own bar sits under it - the room an effect really has
INSETS = {SE: {"top": "20px", "bottom": "0px"}, MAX: {"top": "62px", "bottom": "34px"}, IPAD: {"top": "24px", "bottom": "20px"}, LAP: {}}
_SRC = open(rr.cb.SRC, encoding="utf-8").read()
def body_for(dev):
    ins = INSETS.get(dev, {})
    return rr.cb.INSET_RE.sub(lambda m: ins.get(m.group(1), "0px"), _SRC).replace("let fbDb = null;", "let fbDb = null;" + rr.cb.FIRESTORE_STUB, 1)
PLAIN = rr.cb.BODY

READ = r"""() => {
  const g = document.querySelector('.rs-grade'); if(!g) return null;
  const r = g.getBoundingClientRect(), cs = getComputedStyle(g);
  const vis = e => { if(!e) return false; let o = 1, x = e; while(x && x !== document.body){ o *= +getComputedStyle(x).opacity; x = x.parentElement; } return o > .5 && e.getClientRects().length > 0; };
  let y = 0, e = g; while(e){ y += e.offsetTop; e = e.offsetParent; }
  const head = document.querySelector('.rs-screen > .rs-head');
  let hy = 0; e = head; while(e){ hy += e.offsetTop; e = e.offsetParent; }
  const h = document.querySelector('[data-skip-hint]');
  const hr = h ? h.getBoundingClientRect() : null, hcs = h ? getComputedStyle(h) : null;
  const others = [...document.querySelectorAll('.rs-screen > *')].filter(x => x !== g && !x.classList.contains('rs-endslot') && vis(x)).map(x => x.className.split(' ').slice(0, 2).join('.'));
  const running = g.getAnimations({ subtree: true }).filter(a => { try{ return a.playState === 'running' && a.effect.getComputedTiming().iterations !== Infinity; }catch(err){ return false; } }).length;
  return { vw: innerWidth, vh: innerHeight, cx: r.left + r.width / 2, cy: r.top + r.height / 2, top: r.top, h: r.height, layoutTop: y - scrollY, scrollY,
    headBottom: head ? hy + head.offsetHeight + parseFloat(getComputedStyle(head).marginBottom || 0) - scrollY : null, gradeMt: parseFloat(cs.marginTop) || 0,
    translate: cs.translate, transform: cs.transform, xp: vis(document.querySelector('.rs-xp')), unlocked: vis(document.querySelector('.rs-unlocked')),
    hint: h ? { op: +hcs.opacity, fs: parseFloat(hcs.fontSize), l: hr.left, r: hr.right, t: hr.top, b: hr.bottom, pe: hcs.pointerEvents } : null,
    others, running, layers: [...document.querySelectorAll('body > .hfx-layer, body > .stardust-layer')].filter(l => +getComputedStyle(l).opacity > .05).length,
    dims: document.querySelectorAll('.hfx-dim').length, fx: window.__fxAt > 0 };
}"""

# a layer outside the results covering the screen with a DARK fill (the old dim's shape): colour stops / background colour
# with alpha > .05 and every channel under 70, on an element covering >= 90% of the viewport
DIMS = r"""() => {
  const W = innerWidth, H = innerHeight, out = [];
  const panel = document.querySelector('.rs-screen');
  const eff = el => { let o = 1, x = el; while(x && x !== document.documentElement){ const cs = getComputedStyle(x); if(cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; x = x.parentElement; } return o; };
  const dark = s => { const m = (s || '').match(/rgba?\([^)]*\)/g) || []; return m.some(c => { const v = c.match(/[\d.]+/g).map(Number); const a = v.length > 3 ? v[3] : 1; return a > .05 && v[0] < 70 && v[1] < 70 && v[2] < 70; }); };
  document.querySelectorAll('body *').forEach(el => {
    if(panel && panel.contains(el)) return;
    if(el.closest('.wrap > .top')) return;
    const r = el.getBoundingClientRect(); if(r.width * r.height < .9 * W * H) return;
    const cl = Math.max(0, Math.min(r.right, W) - Math.max(r.left, 0)) * Math.max(0, Math.min(r.bottom, H) - Math.max(r.top, 0));
    if(cl < .9 * W * H) return;
    const cs = getComputedStyle(el);
    if(!(dark(cs.backgroundColor) || (cs.backgroundImage !== 'none' && dark(cs.backgroundImage)))) return;
    const o = eff(el); if(o <= .05) return;
    const thermal = !!el.closest('.hfx-bubbles') && window.NOVA_CLASS === 'ifc';
    out.push({ cls: (el.className && el.className.baseVal != null ? el.className.baseVal : el.className) + '', o: +o.toFixed(2), thermal, tag: el.tagName });
  });
  return out;
}"""

# how much of what the effect paints is on the screen
AREA = r"""() => {
  const W = innerWidth, H = innerHeight;
  /* what the app's own top bar covers is not on the screen either (on a phone it is the status bar and the bar under it) */
  const tb = document.querySelector('.wrap > .top'), Y0 = tb && tb.offsetHeight && tb.getBoundingClientRect().top < 90 ? Math.max(0, tb.getBoundingClientRect().bottom) : 0;
  const clip = r => Math.max(0, Math.min(r.right, W) - Math.max(r.left, 0)) * Math.max(0, Math.min(r.bottom, H) - Math.max(r.top, Y0));
  let tot = 0, inn = 0, pieces = 0, fwTot = 0, fwIn = 0;
  const cache = new Map();
  const op = (el, root) => { if(el === root || !el) return +getComputedStyle(root).opacity; if(cache.has(el)) return cache.get(el);
    const cs = getComputedStyle(el); const v = (cs.display === 'none' || cs.visibility === 'hidden') ? 0 : +cs.opacity * op(el.parentElement, root); cache.set(el, v); return v; };
  const painted = (el, cs) => el.tagName === 'svg' || el.tagName === 'IMG' || el.tagName === 'CANVAS' || cs.backgroundImage !== 'none' ||
    (/rgba?\(/.test(cs.backgroundColor) && !/rgba\([^)]*,\s*0\)$/.test(cs.backgroundColor) && cs.backgroundColor !== 'rgba(0, 0, 0, 0)') || cs.boxShadow !== 'none' || parseFloat(cs.borderTopWidth) > 0;
  document.querySelectorAll('body > .hfx-layer, body > .stardust-layer').forEach(L => {
    if(+getComputedStyle(L).opacity < .05) return;
    const lr = L.getBoundingClientRect();
    L.querySelectorAll('*').forEach(el => {
      if(el.ownerSVGElement) return;
      if(el.tagName === 'CANVAS' && el.classList.contains('hfx-fw-sky') && window.__fwShows && window.__fwShows.length){
        /* the show's own particles (the sky canvas clips what it cannot hold, so its pixels cannot say what was thrown off
           the screen): captured from hfxFwShow as the effect built it, on the clock it started on */
        /* and only what the sky can show: it stops (and fades out over 10px) at the box's top edge, the box lifted over it */
        const f = window.__fwShows[window.__fwShows.length - 1], t = (performance.now() - f.at) / 1000, cr = el.getBoundingClientRect();
        f.S.P.forEach(p => { const a = t - p.t0; if(a < 0 || a > p.life) return; const h = f.S.at(p, a); const s = Math.max(1, p.hs || 1) * 2, w = s * s;
          fwTot += w; const x = h[0] + lr.left, y = h[1] + lr.top; if(x >= 0 && x <= W && y >= Y0 && y <= Math.min(H, cr.bottom - 10)) fwIn += w; });
        return;
      }
      const cs = getComputedStyle(el); if(!painted(el, cs)) return;
      const o = op(el, L); if(o < .05) return;
      const r = el.getBoundingClientRect(); const a = r.width * r.height; if(a < 1) return;
      /* the PIECES - bursts, particles, sprites, clouds, the responder: anything up to half the screen. A wash, a beam
         from a corner, a ring sweeping the whole screen or a strip spanning it (a wave, a band of light that drifts) is
         atmosphere: it is meant to run off the edges */
      if(a > .5 * W * H || r.width >= .9 * W || r.height >= .9 * H) return;
      tot += a * o; inn += clip(r) * o; pieces++;
    });
  });
  const T = tot + fwTot * 6, I = inn + fwIn * 6;
  return { tot: Math.round(T), frac: T ? +(I / T).toFixed(3) : 1, pieces, fw: fwTot ? +(fwIn / fwTot).toFixed(3) : null };
}"""

SEED = r"""(s) => { let a = s >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a;
  t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }"""

# the Fireworks' particle list, caught as hfxFwShow hands it to the effect (the screen show's is the first one built)
FWHOOK = r"""() => { window.__fwShows = []; if(typeof hfxFwShow !== 'function') return;
  const real = hfxFwShow; window.hfxFwShow = function(k){ const S = real(k); if(!window.__fwShows.length) window.__fwShows.push({ S, at: performance.now() }); return S; }; }"""

def to_fx(pg, limit=40):
    k = 0
    while k < limit * 2 and not pg.evaluate("() => window.__fxAt > 0"):
        rr.advance(pg, .5); k += 1
    return pg.evaluate("() => window.__fxAt > 0")

def unit_for(pg, cls):
    return pg.evaluate("() => topicsIn(QUESTIONS)[0]") if cls == "ifc" else "Identity Crimes"

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rr.cb.CHROME)
    ACAD = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
    TOT = {}
    # ---- F1-F5, F7 on a 100% run, both classes, phone and iPad ----
    if want("F1") or want("F2") or want("F3") or want("F4") or want("F5") or want("F7"):
        for cls, fx in (("academy", "fireworks"), ("ifc", "ufo"), ("academy", "ufo"), ("ifc", "bubbles")):
            for dev in ((MAX, IPAD) if fx in ("fireworks",) else (MAX,)):
                W, H = dev
                print("%s %s %dx%d" % (cls, fx, W, H), flush=True)
                ctx, pg, errs = rr.open_run(br, cls, W, H, fx, run=False)
                tail = pg.evaluate("(f) => HUNDO_FX_TAIL_AT[f] || 1500", fx) / 1000
                pg.evaluate("(u) => __run(u, 0, 'drill', false)", unit_for(pg, cls))
                started = to_fx(pg)
                ck("%s %s %dx%d: the effect plays on a 100%% run" % (cls, fx, W, H), started)
                if not started: ctx.close(); continue
                samples, dims, cents = [], [], []
                t = 0
                while t < tail - .3:
                    rr.advance(pg, .25); t += .25
                    s = pg.evaluate(READ); samples.append(s)
                    d = pg.evaluate(DIMS); dims.extend([x for x in d if not x["thermal"]])
                mid = samples[len(samples) // 3]
                ck("(F1) the grade card is centred in the viewport while the effect plays (%s %dx%d)" % (fx, W, H),
                   all(abs(s["cy"] - s["vh"] / 2) <= max(6, .01 * s["vh"]) and abs(s["cx"] - s["vw"] / 2) <= 4 for s in samples[1:-2]),
                   [(round(s["cx"] - s["vw"] / 2, 1), round(s["cy"] - s["vh"] / 2, 1)) for s in samples[::4]])
                ck("(F1) and nothing else of the results is on the screen with it", all(not s["others"] for s in samples[1:-2]), [s["others"] for s in samples[::4]])
                ck("(F2) no dim: no .hfx-dim and no dark layer over the whole screen at any of %d samples" % len(samples),
                   all(s["dims"] == 0 for s in samples) and not dims, dims[:3])
                if want("F7"):
                    h = mid["hint"]
                    ck("(F7) a skip hint is up while the effect plays: shown, >= 12px, on the screen, clear of the card, takes no pointer",
                       bool(h) and h["op"] > .5 and h["fs"] >= 12 and h["t"] >= 0 and h["b"] <= mid["vh"] and h["l"] >= 0 and h["r"] <= mid["vw"]
                       and (h["t"] > mid["top"] + mid["h"] or h["b"] < mid["top"]) and h["pe"] == "none", h)
                # through the move up to the XP card
                trace = []
                for _ in range(60):
                    rr.advance(pg, .1); s = pg.evaluate(READ); trace.append(s)
                    if s["xp"] and s["translate"] in ("none", "0px", "0px 0px"): break
                moving = [s for s in trace if s["translate"] not in ("none", "0px", "0px 0px")]
                fin = trace[-1]
                ck("(F3) afterwards the grade's top is its place at the top of the stack, under the header",
                   abs(fin["top"] - fin["layoutTop"]) < 1.5 and fin["headBottom"] is not None and abs(fin["layoutTop"] - fin["gradeMt"] - fin["headBottom"]) < 2.5,
                   {k: fin[k] for k in ("top", "layoutTop", "headBottom", "gradeMt")})
                ck("(F3) its move is a transform: the box is drawn between centre and its place while its layout box stays put",
                   len(moving) >= 2 and all(abs(m["layoutTop"] - fin["layoutTop"]) < 1 for m in moving) and any(fin["top"] + 8 < m["top"] < mid["top"] - 8 for m in moving),
                   [(round(m["top"]), m["translate"]) for m in moving][:6])
                xp_at = next((i for i, s in enumerate(trace) if s["xp"]), None)
                settled_at = next((i for i, s in enumerate(trace) if s["translate"] in ("none", "0px", "0px 0px") and abs(s["top"] - s["layoutTop"]) < 1.5), None)
                ck("(F4) the XP card is shown only once the grade has settled", xp_at is not None and settled_at is not None and xp_at >= settled_at
                   and all(not s["xp"] for s in samples), (settled_at, xp_at))
                if cls == "ifc" and fx == "ufo" and want("F5"):
                    # the chapter's badge: its case plays after the settled grade, the unlock card after the XP card
                    seen_case = False; xp_vis_t = None; un_t = None; tt = 0
                    while tt < 60:
                        rr.advance(pg, .5); tt += .5
                        st = pg.evaluate("() => ({ c: !!document.querySelector('.bc-scene'), x: (() => { const e = document.querySelector('.rs-xp'); return !!e && +getComputedStyle(e).opacity > .5; })(), u: (() => { const e = document.querySelector('.rs-unlocked'); return !!e && +getComputedStyle(e).opacity > .5; })(), d: !!document.querySelector('.rs-done') })")
                        seen_case = seen_case or st["c"]
                        if st["x"] and xp_vis_t is None: xp_vis_t = tt
                        if st["u"] and un_t is None: un_t = tt
                        if st["d"]: break
                    ck("(F5) a Fire Code 100% chapter: its badge case still plays, after the settled grade", seen_case)
                    ck("(F5) the unlock card comes after the XP card", un_t is not None and xp_vis_t is not None and un_t > xp_vis_t, (xp_vis_t, un_t))
                if errs: ck("no page errors", False, errs[:3])
                ctx.close()

    # ---- F6: a tap, and Enter, skip it ----
    if want("F6"):
        for how in ("tap", "enter"):
            for cls, fx in (("academy", "fireworks"), ("ifc", "ufo")) if how == "tap" else (("academy", "underwater"),):
                W, H = MAX
                ctx, pg, errs = rr.open_run(br, cls, W, H, fx, run=False)
                pg.evaluate("(u) => __run(u, 0, 'drill', false)", unit_for(pg, cls))
                to_fx(pg); rr.advance(pg, 1.2)
                before = pg.evaluate(READ)
                if how == "tap": pg.mouse.click(W / 2, H - 30)
                else: pg.keyboard.press("Enter")
                rr.advance(pg, .3)
                s = pg.evaluate(READ)
                ck("(F6) %s %s: a %s while the effect plays - within 300ms its layers are gone, the grade is in its place, nothing on it still running" % (cls, fx, how),
                   before["layers"] > 0 and s["layers"] == 0 and s["translate"] in ("none", "0px", "0px 0px") and abs(s["top"] - s["layoutTop"]) < 1.5 and s["running"] == 0,
                   {"before": before["layers"], "layers": s["layers"], "translate": s["translate"], "top": s["top"], "layoutTop": s["layoutTop"], "running": s["running"]})
                ctx.close()

    # ---- F8: on the screen ----
    if want("F8"):
        devs = (SE, MAX) if QUICK else (SE, MAX, IPAD, LAP)
        for cls in ("academy", "ifc"):
            for fx in ACAD:
                if cls == "ifc" and fx == "confetti": continue
                if FXONLY and fx not in FXONLY: continue
                res = []
                for (W, H) in devs:
                    rr.cb.BODY = body_for((W, H))
                    ctx, pg, errs = rr.open_run(br, cls, W, H, fx, run=False)
                    rr.cb.BODY = PLAIN
                    pg.evaluate(SEED, 3840 + W)   # the same show every run (Math.random seeded), a different one per size
                    pg.evaluate(FWHOOK)
                    tail = pg.evaluate("(f) => HUNDO_FX_TAIL_AT[f] || 1500", fx) / 1000
                    pg.evaluate("(u) => __run(u, 0, 'drill', false)", unit_for(pg, cls))
                    if not to_fx(pg): res.append((W, H, None)); ctx.close(); continue
                    best = None; t = 0; worst = 1
                    rows = []
                    while t < tail:
                        rr.advance(pg, .25); t += .25
                        a = pg.evaluate(AREA); rows.append(a)
                    # the busiest moment before its exit (the last 15% of its time is it leaving - the UFO's warp streaks off the
                    # top of the screen on purpose)
                    peak = max(rows[:max(1, int(len(rows) * .85))], key=lambda r: r["tot"])
                    if os.environ.get("F8DEBUG"): print("   ", W, H, "peak at", (rows.index(peak) + 1) * .25, "s", peak, "worst", min((r["frac"], i) for i, r in enumerate(rows)))
                    # the middle half of it (its entrance and exit may come in or go out over an edge)
                    midr = [r for r in rows[len(rows) // 4: max(len(rows) // 4 + 1, 3 * len(rows) // 4)] if r["tot"] > 0]
                    avg = sum(r["frac"] * r["tot"] for r in midr) / max(1, sum(r["tot"] for r in midr))
                    res.append((W, H, peak["frac"], round(avg, 3), peak["fw"]))
                    ctx.close()
                ck("(F8) %s %s keeps >= 85%% of its painted pieces on the screen at its peak and through the middle of it, every size" % (cls, fx),
                   all(r[2] is not None and r[2] >= .85 and r[3] >= .85 and (r[4] is None or r[4] >= .85) for r in res)
                   and (fx != "fireworks" or cls == "ifc" or all(r[4] is not None for r in res)), res)

    # ---- F9 reduce motion, F10 a run short of 100 ----
    if want("F9"):
        W, H = MAX
        ctx, pg, errs = rr.open_run(br, "academy", W, H, "fireworks", run=False)
        pg.evaluate("() => { theme.reduceMotion = true; }")
        pg.evaluate("(u) => __run(u, 0, 'drill', false)", "Identity Crimes")
        rr.advance(pg, .6)
        s = pg.evaluate(READ)
        ck("(F9) reduce motion: the grade in its place at once, the XP card with it, no hint, no effect layer",
           s["translate"] in ("none", "0px", "0px 0px") and abs(s["top"] - s["layoutTop"]) < 1.5 and s["xp"] and not s["hint"] and s["layers"] == 0, s)
        ctx.close()
    if want("F10"):
        W, H = MAX
        ctx, pg, errs = rr.open_run(br, "academy", W, H, "fireworks", run=False)
        pg.evaluate("(u) => __run(u, 3, 'drill', false)", "Identity Crimes")
        trace = []
        for _ in range(140):
            rr.advance(pg, .1); s = pg.evaluate(READ); trace.append(s)
            if s and s["xp"]: break
        cen = [s for s in trace if s and abs(s["cy"] - s["vh"] / 2) < 8]
        ck("(F10) a run short of 100: centred first, no effect, then up, then the XP card",
           len(cen) >= 10 and not any(s["fx"] for s in trace) and trace[-1]["xp"] and abs(trace[-1]["top"] - trace[-1]["layoutTop"]) < 1.5,
           (len(cen), trace[-1]["top"] if trace else None))
        ctx.close()
    br.close()
rr.cb.SERVER.shutdown()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
