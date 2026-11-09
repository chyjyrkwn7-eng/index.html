#!/usr/bin/env python3
"""Build 384: the academy's hundo effects, tightened.

Madison: "Tighten up all of them where you can to ensure they perfect, that
goes for the police ones too."

Every check runs on a REAL 100% results screen (check-behaviour's __run100,
Identity Crimes), the effect picked in the store, on an iPhone 17 Pro Max
(440x956) and an 11" iPad (834x1194); the UFO and Fireworks also on the
phone with the iPhone's real status bar (env(safe-area-inset-top) served as
59px, as tools/sim-safe-area.py does - Chromium reports 0). Positions are
read off the page with every animation of the effect paused and seeked, or
off the effect's own show, never off typed numbers:

  A. UFO - the saucer is whole on the screen (and clear of the status bar)
     from the moment it shows (1.0s) until it breaks away (8.5s): circling,
     hovering, sweeping, landed and lifted - on one unit and on two (where
     the reveal has scrolled the page 83px). It still circles over the box.
     Its beam, alone on black while it hovers, is lit right under the hull
     and as wide as itself near the box's floor (the svg had been
     letterboxed: on two units it began at the box's edge, 50px under the
     hull, and on an iPad it was a quarter too narrow).
  B. Fireworks - no burst is cut off by the top of the screen or the status
     bar: under 1% of the show's lit spark-head samples are above the sky.
  C. Bubbles - they spread over the screen: 35%+ of the bubbles end below
     the box (they all left upwards), their ends span over half the screen's
     height; the flourish's halo opens at the ring of bubbles (not in the
     middle of the box, over the number) and its bitmap is drawn at 1000px+.
  D. Confetti - the 100% box carries the burst: a box half in the grade card
     with the number lit on the burst (within 0.15s) and the nova's rings in
     it; nothing in the nova animates a filter.
  E. The tiles and stills - the UFO's beam is blue as the effect's is
     (HFX_UFO_BEAM), in the tile and the still; no Fireworks tile burst runs
     into the tile's top edge (3+ units clear); the Fireworks still's glow is
     its own magenta, not white fading to clear.
  F. No page errors.

  python3 tools/check-b384-policefx.py [--against OLD/index.html]   (must FAIL on 3b6f4ad)
  B384P_ONLY=A,C   runs those sections only."""
import importlib.util, io, os, re, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

ONLY = set((os.environ.get("B384P_ONLY") or "A,B,C,D,E,F").split(","))
FAILS = []
def ck(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)) if detail != "" else ""), flush=True)
    if not ok: FAILS.append(name)

PHONE, IPAD = (440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11")
# the page as an iPhone serves it: the status bar's 59px (and the home bar's 34px)
SRC = io.open(cb.SRC, encoding="utf-8").read()
BODY59 = cb.INSET_RE.sub(lambda m: {"top": "59px", "bottom": "34px"}.get(m.group(1), "0px"), SRC) \
    .replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
ERRS = []

def page(br, w, h, inset=False):
    ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT)
    if inset:
        pg.unroute("**/index.html")
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY59))
        pg.goto(cb.URL); pg.wait_for_timeout(2600)
        pg.evaluate("()=>{ try{ store.savedCodeSaved = true; localStorage.setItem('class26e.savecode.card','1'); }catch(e){} document.getElementById('splashscreen')?.remove(); __stub(); }")
    pg.on("pageerror", lambda e: ERRS.append(str(e)[:200]))
    pg.evaluate("() => { " + cb.RUN100 + " }")
    return ctx, pg

# a real 100% with effect `fx`, up to its first frame; `pre` runs first (a hook)
START = """async ([fx, pre]) => { const wait = ms => new Promise(r => setTimeout(r, ms));
  store.lifetime.perfectTests = 600; if(!HUNDO_FX.some(d => d.id === fx)) return { err: 'no ' + fx };
  store.hundoFx = fx; theme.reduceMotion = false; theme.muteBanners = true;
  try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){}
  saveStore(); saveTheme();
  if(pre) (0, eval)(pre);
  window.__fxAt = 0; const real = playHundoFx; window.playHundoFx = function(a, b){ window.__fxAt = performance.now(); return real(a, b); };
  const rc = celebrate; window.celebrate = function(a, b, c){ window.__fxAt = window.__fxAt || performance.now(); return rc(a, b, c); };
  showHome(); await wait(200);
  if(window.__units) __run100m(topicsIn(QUESTIONS).slice(0, window.__units)); else __run100('Identity Crimes');
  for(let i = 0; i < 900 && !window.__fxAt; i++) await wait(50);
  return { ok: !!window.__fxAt }; }"""

def sec_A(br):
    print("\nA. UFO: the saucer whole on the screen, clear of the status bar, from 1.0s to 8.5s; its beam all there")
    for (w, h, dev), inset, units in ((PHONE, False, 0), (IPAD, False, 0), (PHONE, True, 0), (PHONE, False, 2)):
        tag = dev + (" with the 59px status bar" if inset else "") + (", %d units" % units if units else "")
        ctx, pg = page(br, w, h, inset)
        if units:
            pg.evaluate("(n) => { " + cb.RUN100M + "; window.__units = n; }", units)
        st = pg.evaluate(START, ["ufo", None])
        if not st.get("ok"):
            ck("%s: a real 100%% played the UFO" % tag, False, st); ctx.close(); continue
        pg.wait_for_timeout(300)
        # everything paused; then only the saucer's own layer is painted, on black, so the
        # top rows of the sky show nothing but the saucer: any lit pixel there is the saucer
        # cut by the top of the screen (or sitting under the status bar)
        ok = pg.evaluate("""() => {
          const anims = () => document.getAnimations().filter(a => { const e = a.effect && a.effect.target; return e && e.closest && e.closest('.hfx-layer.hfx-ufo, .hfx-box.hfx-ufo, .hfx-dim'); });
          window.__ufoSeek = t => anims().forEach(a => { try{ a.pause(); a.currentTime = t * 1000; }catch(e){} });
          window.__ufoSeek(1);
          const op = el => { let o = 1; for(let e = el; e && e !== document.body; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
          const body = document.querySelector('.hfx-saucer:not(.is-mini) .hfx-ufo-body'), g = document.querySelector('.rs-screen .rs-grade'), top = document.querySelector('.hfx-ufo-top');
          if(!body || !g || !top) return false;
          window.__ufoAt = () => { const b = body.getBoundingClientRect(), gb = g.getBoundingClientRect(); return { top: b.top, cy: b.top + b.height / 2, o: op(body), boxTop: gb.top }; };
          document.documentElement.style.background = '#000'; document.body.style.background = '#000';
          document.body.style.visibility = 'hidden'; top.style.visibility = 'visible';
          return true; }""")
        top = 59 if inset else 0   # the status bar the page is served with (Chromium itself reports 0)
        if not ok:
            ck("%s: the saucer, its layer and the box are there" % tag, False); ctx.close(); continue
        from PIL import Image
        r = []
        for i in range(76):
            t = round(1.0 + i * .1, 2)
            pg.evaluate("(t) => new Promise(res => { __ufoSeek(t); requestAnimationFrame(() => requestAnimationFrame(res)); })", t)
            x = pg.evaluate("() => __ufoAt()"); x["t"] = t
            im = Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": top, "width": w, "height": 2}))).convert("RGB")
            x["lit"] = sum(1 for p in list(im.getdata()) if max(p) > 40)
            r.append(x)
        # its beam, hovering (5.6s), alone on black: lit just under the hull (12% of the way
        # down it) and, near the box's floor, as wide as the beam itself - the picture fills
        # its box (an svg kept to its own 1:2 left the ends clear, or the sides)
        pg.evaluate("(t) => new Promise(res => { __ufoSeek(t); requestAnimationFrame(() => requestAnimationFrame(res)); })", 5.6)
        bm = pg.evaluate("() => { const b = document.querySelector('.hfx-saucer:not(.is-mini) > .hfx-ufo-beam'), r = b.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }")
        def span(y):
            im = Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": y, "width": w, "height": 1}))).convert("RGB")
            xs = [i for i, p in enumerate(list(im.getdata())) if max(p) > 40]
            return (xs[-1] - xs[0]) / (im.width / w) if xs else 0
        hi = span(bm[1] + (bm[3] - bm[1]) * .12); lo = span(bm[3] - 12)
        ctx.close()
        ck("%s: the beam is lit right under the hull and, near the box's floor, as wide as itself (%.0f of %.0fpx; %.0fpx lit under the hull)" % (tag, lo, bm[2] - bm[0], hi),
           hi >= 4 and lo >= (bm[2] - bm[0]) * .85, bm)
        seen = [x for x in r if x["o"] > .3]
        cut = [(x["t"], x["lit"]) for x in seen if x["lit"]]
        ck("%s: the saucer is whole on the screen and clear of the status bar (%dpx) at every 0.1s it shows, 1.0-8.5s - none of it in the sky's top rows" % (tag, top),
           len(seen) > 60 and not cut, cut[:12])
        circ = [x for x in seen if 1.4 <= x["t"] <= 2.95]
        ck("%s: and it still circles over the box (its middle 40px+ over the box's top edge all round the circle)" % tag,
           len(circ) > 10 and all(x["cy"] < x["boxTop"] - 40 for x in circ), [(x["t"], round(x["cy"]), round(x["boxTop"])) for x in circ if x["cy"] >= x["boxTop"] - 40][:6])

FW_SHOW = """() => { const P = []; (window.__fw || []).filter(f => !f.inBox).forEach(f => {
    const S = f.S;
    S.P.forEach(p => {
      for(let a = 0; a <= p.life; a += .04){
        const u = a / p.life;
        let b = p.kind === 3 ? 1 - u : p.kind === 2 ? Math.pow(1 - u, 1.5) * .75 : (u < .58 ? 1 : 1 - Math.pow((u - .58) / .42, 1.4));
        if(b < .1) continue;
        const h = S.at(p, a); P.push([p.kind, p.tr || 0, h[1], h[0]]);
      }
    }); });
  return P; }"""
FW_HOOK = "(function(){ const real = hfxFwSky; window.__fw = []; hfxFwSky = function(parent, c, S){ window.__fw.push({ S, inBox: !!(parent && parent.classList && parent.classList.contains('hfx-box')) }); return real.apply(this, arguments); }; })()"

def sec_B(br):
    print("\nB. Fireworks: no burst cut off by the top of the screen or the status bar")
    for (w, h, dev), inset in ((PHONE, False), (IPAD, False), (PHONE, True)):
        tag = dev + (" with the 59px status bar" if inset else "")
        ctx, pg = page(br, w, h, inset)
        st = pg.evaluate(START, ["fireworks", FW_HOOK])
        if not st.get("ok"):
            ck("%s: a real 100%% played the Fireworks" % tag, False, st); ctx.close(); continue
        pg.wait_for_timeout(200)
        P = pg.evaluate(FW_SHOW)
        top = 59 if inset else 0   # the status bar the page is served with (Chromium itself reports 0)
        ctx.close()
        bursts = [p for p in P if p[0] == 0 and p[1] >= .13]
        over = [p for p in bursts if p[2] < top - 1]
        share = len(over) / max(1, len(bursts))
        ck("%s: under 1%% of the bursts' lit spark samples are above the sky's top (%dpx): %.1f%% of %d" % (tag, top, share * 100, len(bursts)),
           len(bursts) > 500 and share < .01, "highest %.0fpx" % min(p[2] for p in bursts) if bursts else "no show")

BUB = """() => { const L = document.querySelector('.hfx-layer.hfx-bubbles'), g = document.querySelector('.rs-screen .rs-grade');
  if(!L || !g) return null;
  const lr = L.getBoundingClientRect(), gb = g.getBoundingClientRect(), px = (el, k) => parseFloat(el.style.getPropertyValue(k)) || 0;
  const bs = [...L.querySelectorAll(':scope > .hfx-bb, :scope > .hfx-gb')].map(el => ({
    x: lr.left + parseFloat(el.style.left) + px(el, '--ex'), y: lr.top + parseFloat(el.style.top) + px(el, '--ey'),
    d: px(el, '--d'), dl: px(el, '--dl'), pop: el.classList.contains('is-pop') }));
  const halo = L.querySelector('.hfx-bub-halo');
  let s0 = null;
  try{ const a = halo.getAnimations()[0]; const k = a.effect.getKeyframes()[0]; const m = /scale\\(([\\d.]+)/.exec(k.transform || ''); s0 = m ? +m[1] : null; }catch(e){}
  /* which sprite the halo shows (either of its forms, compared as the page writes them back) */
  const sp = typeof hfxSprites === 'object' ? hfxSprites : {}, tmp = document.createElement('i');
  const norm = v => { tmp.style.backgroundImage = ''; tmp.style.backgroundImage = v || ''; return tmp.style.backgroundImage; };
  const hb = halo ? norm(halo.style.backgroundImage) : '';
  const haloSprite = Object.keys(sp).filter(k => hb && (hb === norm(sp[k].png) || hb === norm(sp[k].svg))).map(k => sp[k].px)[0] || null;
  return { bs, boxTop: gb.top, boxBottom: gb.bottom, cx: gb.left + gb.width / 2, cy: gb.top + gb.height / 2, vh: innerHeight,
    halo: halo ? { hr: px(halo, '--hr'), s0, px: haloSprite } : null }; }"""

def sec_C(br):
    print("\nC. Bubbles: over the whole screen; a halo that opens at the ring of bubbles, drawn sharp")
    for (w, h, dev) in (PHONE, IPAD):
        ctx, pg = page(br, w, h)
        st = pg.evaluate(START, ["bubbles", None])
        if not st.get("ok"):
            ck("%s: a real 100%% played Bubbles" % dev, False, st); ctx.close(); continue
        pg.wait_for_timeout(150)
        r = pg.evaluate(BUB)
        ctx.close()
        if not r or not r["bs"]:
            ck("%s: the bubbles are there" % dev, False, r); continue
        bs = r["bs"]
        below = [b for b in bs if b["y"] > r["boxBottom"] + 10]
        ys = [b["y"] for b in bs]
        ck("%s: 35%%+ of the bubbles end below the box (%d of %d)" % (dev, len(below), len(bs)), len(below) / len(bs) >= .35)
        ck("%s: their ends span over half the screen's height (%.0f of %dpx)" % (dev, max(ys) - min(ys), r["vh"]), max(ys) - min(ys) > r["vh"] * .5)
        fl = [b for b in bs if b["pop"] and abs(b["d"] - .9) < .01]
        R = max(abs(b["x"] - r["cx"]) for b in fl) if fl else 0
        hl = r["halo"] or {}
        birth = (hl.get("hr") or 0) / 2 * (hl.get("s0") or 0)
        ck("%s: the halo opens at the ring of bubbles (%.0fpx from the box's middle; the ring is %.0fpx out), not in over the number" % (dev, birth, R),
           R > 0 and birth >= .9 * R, hl)
        ck("%s: and its picture is drawn at 1000px or more (%s), not blown up from a 320px one" % (dev, hl.get("px")), (hl.get("px") or 0) >= 1000)

CONF = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  await wait(60);
  const g = document.querySelector('.rs-screen .rs-grade'), bx = g && g.querySelector('.hfx-box.is-grade');
  const lit = bx && bx.querySelector('.hfx-lit.is-flash');
  let litDelay = null; try{ litDelay = parseFloat(getComputedStyle(lit).animationDelay); }catch(e){}
  const rings = bx ? bx.querySelectorAll('.stardust-ring').length : 0;
  const filt = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; if(!t || !t.closest || !t.closest('.stardust-layer')) return false;
    try{ return a.effect.getKeyframes().some(k => 'filter' in k); }catch(e){ return false; } }).map(a => a.animationName || a.id || '?');
  return { box: !!bx, lit: !!lit, litDelay, rings, filt: [...new Set(filt)] }; }"""

def sec_D(br):
    print("\nD. Confetti: the 100% box carries the burst; no filter in the nova")
    for (w, h, dev) in (PHONE, IPAD):
        ctx, pg = page(br, w, h)
        st = pg.evaluate(START, ["confetti", None])
        if not st.get("ok"):
            ck("%s: a real 100%% played Confetti" % dev, False, st); ctx.close(); continue
        r = pg.evaluate(CONF)
        ctx.close()
        ck("%s: a half of the burst in the 100%% box, with the nova's rings in it (%s)" % (dev, r), r["box"] and r["rings"] >= 1)
        ck("%s: the number lit on the burst, within 0.15s of it (%s)" % (dev, r["litDelay"]), r["lit"] and r["litDelay"] is not None and r["litDelay"] <= .15)
        ck("%s: nothing in the nova animates a filter (%s)" % (dev, r["filt"]), not r["filt"])

TILES = """() => {
  const beam = (typeof hfxUfoBeam === 'function') ? hfxUfoBeam() : null;
  const ufoP = hundoFxPosterSVG('ufo'), ufoS = buildHundoFxStill('ufo').outerHTML;
  const green = (typeof HFX_UFO_BEAMS === 'object') ? HFX_UFO_BEAMS.green : { hi: '#C8FFD4', c: '#6BFF8F' };
  const fwP = hundoFxPosterSVG('fireworks'), fwS = buildHundoFxStill('fireworks').outerHTML;
  const d = new DOMParser().parseFromString(fwP.replace('class="hfx-poster"', 'xmlns="http://www.w3.org/2000/svg"'), 'image/svg+xml');
  /* the bursts' tips (white dots) and the climbing shell's head */
  const tops = [...d.querySelectorAll('circle')].filter(c => /#FFFFFF/i.test(c.getAttribute('fill') || '')).map(c => +c.getAttribute('cy') - +c.getAttribute('r'));
  const s = new DOMParser().parseFromString(fwS, 'image/svg+xml');
  const gr = s.querySelector('radialGradient');
  const stops = gr ? [...gr.querySelectorAll('stop')].map(x => [x.getAttribute('offset'), x.getAttribute('stop-color'), +(x.getAttribute('stop-opacity') || 1)]) : [];
  return { beam: beam && { hi: beam.hi, c: beam.c, name: typeof HFX_UFO_BEAM === 'string' ? HFX_UFO_BEAM : '' },
    posterBlue: !!beam && ufoP.indexOf(beam.c) >= 0, posterGreen: ufoP.indexOf(green.hi) >= 0 || ufoP.indexOf('"' + green.c + '" stop-opacity=".28"') >= 0,
    stillBlue: !!beam && ufoS.indexOf(beam.c) >= 0, stillGreenBeam: ufoS.indexOf(green.hi) >= 0,
    fwTop: tops.length ? Math.min(...tops) : null, glow: stops }; }"""

def sec_E(br):
    print("\nE. The tiles and the stills")
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT)
    pg.on("pageerror", lambda e: ERRS.append(str(e)[:200]))
    r = pg.evaluate(TILES)
    ctx.close()
    blue = r["beam"] and r["beam"]["name"] == "blue"
    ck("the UFO tile's beam is the effect's own blue (%s), with none of the old green beam" % (r["beam"],), blue and r["posterBlue"] and not r["posterGreen"])
    ck("the UFO still's beam is blue too", blue and r["stillBlue"] and not r["stillGreenBeam"])
    ck("no Fireworks tile burst runs into the tile's top edge (highest tip %.1f units down; 3+ wanted)" % (r["fwTop"] or -1), r["fwTop"] is not None and r["fwTop"] >= 3)
    mid = [x for x in r["glow"] if x[1] and x[1].upper() == "#FF5CD6" and float(x[0] or 0) < .5 and x[2] >= .3]
    ck("the Fireworks still's glow is its own magenta round a hot core, not white fading to clear (%s)" % r["glow"], len(r["glow"]) >= 3 and bool(mid))

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for k, f in (("A", sec_A), ("B", sec_B), ("C", sec_C), ("D", sec_D), ("E", sec_E)):
        if k in ONLY:
            f(br)
    if "F" in ONLY:
        print("\nF. Errors")
        ck("no page errors", not ERRS, ERRS[:3])
    br.close()
cb.SERVER.shutdown()
print("\n" + ("ALL PASS" if not FAILS else "%d FAILED" % len(FAILS)))
sys.exit(1 if FAILS else 0)
