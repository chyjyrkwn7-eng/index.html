#!/usr/bin/env python3
"""Build 325, stream A - the end of a run: its buttons, the hundo effects,
the character's reactions, and the characters in their circles.

  python3 tools/check-b325-a.py [--against OLD/index.html] [--only NAME,...]

Madison's list (Oct 18), one section each:
  1. rise     "The continue to review button, re run button, and main menu
              button just show up really fast. Have them slide up from the
              bottom like how the next question button does during a test."
              Every way-on button on the results, the review, back to the
              results and the race board comes up from BELOW where it rests,
              on the Next question pill's own move (qnext-rise: .62s, its
              curve, opacity in by a third), a row at a time; on the results
              only once everything above it has landed.
  2. dim      "the new hundo effects the screen goes slightly dim and the
              effect happens, let's ensure the default one is the same."
              Confetti puts the Fireworks' dim up (.5 at its height), the
              grade box lifted over it, and takes it down by 3s.
  3. glow     "the number 100 lights up on a delay and it's not a smooth
              transition at the end." As the 100 crosses into its effect's
              colours its glow is that colour at every frame of the
              crossing - never the near-black a color-mix() shadow
              interpolates as - and grows smoothly (no jump on the last).
  4. chat     "The chat button disappears and comes back during hundo
              effect? Fix that, it can stay." The chat button does not move
              and does not hide for the whole of a full-page hundo effect.
  5. edges    "the edges of it have that nice hard glow, ensure all the
              other boxes on the result screen match this." The XP card,
              the Found & unlocked card and the grade of a pass carry the
              hundo box's recipe in their own colour: an opaque rim, an
              inset 1px line and an inset glow 24px+ deep.
  6. water    "The underwater one ... he holds his breath even before the
              water and holds it after it's gone ... The fish coming by and
              the random shadow black thing is bad." No manta; the fish are
              drawn (several colours, fins, an eye) and are only ever on
              screen while the sea is up; the breath is taken no more than
              .18s before the surface reaches the face and let go no more
              than .15s after it has left it (real time, every frame).
  7. tick     "What's up with the check mark for the 70 %? Don't do that."
              No character's pass reaction puts anything on the circle.
  8. centre   "almost every character and its stuff is not centered, they
              are all near the top." For EVERY character id, what you see of
              it in the results circle - its visible ink, scenery and halo
              aside - is centred in the circle (its top-to-bottom middle
              within 3% of the circle's height of the middle), and the
              drawing every other place uses is that same centred one.

Every section fails on 6fc16b7 (/tmp/claude-0/wbase325) - run --against."""
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ONLY = None
if "--only" in sys.argv:
    ONLY = sys.argv[sys.argv.index("--only") + 1].split(",")
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)
check = cb.check
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

_RES = open(os.path.join(HERE, "check-results.py")).read()
_i = _RES.index('SETUP = """') + len('SETUP = """')
SETUP = _RES[_i:_RES.index('"""', _i)]


def boot(br, w=440, h=956, dpr=1, char="ninja", fx="confetti", seed=None):
    ctx, pg = cb.booted(br, w, h, seed=seed or cb.USED_ACCOUNT, dpr=dpr)
    pg.evaluate(SETUP)
    pg.evaluate("""([fx, ch]) => { store.avatarChar = ch; store.lifetime.perfectTests = 600; store.hundoFx = fx;
      const u = typeof pendingHomeUnlocks === 'function' ? pendingHomeUnlocks() : null; if(u) markUnlocksShown(u.chars, u.banners, u.fx);
      saveStore(); try{ hfxWarm(fx); }catch(e){} }""", [fx, char])
    return ctx, pg


def wait_done(pg, ms=45000):
    for _ in range(ms // 250):
        if pg.evaluate("()=>!!document.querySelector('.rs-rewards.rs-done')"):
            return True
        pg.wait_for_timeout(250)
    return False


# ---------------------------------------------------------------- 1. rise
# Every frame from the moment a set of buttons is put on screen: each one's
# offset from where it RESTS (its transform's y) and its opacity.
RISE_LOG = r"""(sel) => { window.__rise = null;
  const go = el => { if(window.__rise) return; const t0 = performance.now(), log = [];
    const btns = [...el.querySelectorAll(':scope > button, :scope > .next')].filter(b => !b.hidden);
    window.__rise = { log, n: btns.length, rows: btns.map(b => b.offsetTop) };
    const tick = () => { const t = performance.now() - t0;
      log.push([t, btns.map(b => { const cs = getComputedStyle(b); let y = 0; try{ y = new DOMMatrixReadOnly(cs.transform).m42; }catch(e){}
        return [+y.toFixed(1), +(+cs.opacity).toFixed(2)]; })]);
      if(t < 1500) requestAnimationFrame(tick); };
    tick(); };
  const watch = () => { const el = document.querySelector(sel); if(!el) return false;
    const shown = () => { const cs = getComputedStyle(el); return cs.opacity > .01 && cs.visibility !== 'hidden' && (el.classList.contains('rs-in') || el.classList.contains('rs-in-now') || el.classList.contains('is-done') || el.closest('.vrc.is-done') || !el.classList.contains('rs-land')); };
    if(shown()){ go(el); return true; }
    new MutationObserver((m, o) => { if(shown()){ o.disconnect(); go(el); } }).observe(el, { attributes: true, attributeFilter: ['class'] });
    const p = el.closest('.vrc'); if(p) new MutationObserver((m, o) => { if(shown()){ o.disconnect(); go(el); } }).observe(p, { attributes: true, attributeFilter: ['class'] });
    return true; };
  if(!watch()){ const mo = new MutationObserver(() => { if(watch()) mo.disconnect(); }); mo.observe(document.body, { childList: true, subtree: true }); } }"""
# The Next question pill's own rise, read off the stylesheet.
QNEXT = r"""() => { for(const sh of document.styleSheets){ let rules; try{ rules = sh.cssRules; }catch(e){ continue; }
  for(const r of rules){ if(r.selectorText && /\.qnext\.is-rising/.test(r.selectorText) && r.style.animationName){ return { dur: r.style.animationDuration, ease: r.style.animationTimingFunction }; } } } return null; }"""


def rise_verdict(label, r, qn):
    if not r or not r.get("log"):
        check("%s: its buttons come up when they are put on screen" % label, False, "never shown")
        return
    log = r["log"]
    first = log[0][1]
    below = all(y > 20 and o < .5 for (y, o) in first)
    end = log[-1][1]
    rested = all(abs(y) < .5 and o > .99 for (y, o) in end)
    # how long each took to come within 1px of rest
    took = []
    for b in range(r["n"]):
        t_in = next((t for (t, ys) in log if abs(ys[b][0]) <= 1 and ys[b][1] > .99), None)
        took.append(t_in)
    rows = sorted(set(round(v / 6) for v in r["rows"]))
    stag = True
    if len(rows) > 1:
        # the first row's buttons start before the next row's
        start = []
        for b in range(r["n"]):
            t_mv = next((t for (t, ys) in log if ys[b][0] < first[b][0] - 2), None)
            start.append((round(r["rows"][b] / 6), t_mv))
        firsts = [t for (rw, t) in start if rw == rows[0] and t is not None]
        lasts = [t for (rw, t) in start if rw == rows[-1] and t is not None]
        stag = bool(firsts and lasts and min(lasts) > min(firsts) + 40)
    check("%s: every button starts below where it rests, unseen" % label, below, first)
    check("%s: ... and rises into place (no drop from above)" % label,
          rested and all(t is not None for t in took) and all(
              all(ys[b][0] >= -0.5 for (t, ys) in log) for b in range(r["n"])), [took, end])
    # the Next pill's .62s: each button is home in .45-.9s of starting
    dur_ok = all(t is not None and 380 <= t - (0 if len(rows) < 2 else 0) <= 1100 for t in took)
    check("%s: on the Next question pill's move (%s, %s)" % (label, qn and qn.get("dur"), qn and qn.get("ease")), dur_ok and qn is not None, took)
    check("%s: a row at a time" % label, stag, r["rows"])


def sec_rise(br):
    print("\n1. the way-on buttons rise from below, like Next question")
    ctx, pg = boot(br, 440, 956)
    qn = pg.evaluate(QNEXT)
    pg.evaluate(RISE_LOG, ".rs-rewards .rs-actions")
    pg.evaluate("() => __run('Identity Crimes', 2, 'drill', false)")
    ok = wait_done(pg)
    pg.wait_for_timeout(1700)
    r = pg.evaluate("() => window.__rise")
    # nothing landing after them: every card above had landed when they came
    order = pg.evaluate("() => (window.__lands || []).map(l => l.kind)")
    check("results (2 missed): the reveal finished", ok)
    check("results: the buttons come after every card above them", bool(order) and order[-1] == "actions", order[-6:])
    rise_verdict("results", r, qn)
    # the review
    pg.evaluate(RISE_LOG, ".rs-review .actions")
    pg.evaluate("() => { const b = [...document.querySelectorAll('.rs-actions button')].find(b => /review/i.test(b.textContent)); b && b.click(); }")
    pg.wait_for_timeout(1900)
    rise_verdict("the review", pg.evaluate("() => window.__rise"), qn)
    # back to the results
    pg.evaluate(RISE_LOG, ".rs-rewards .rs-actions")
    pg.evaluate("() => { const b = [...document.querySelectorAll('.rs-review .actions button')].find(b => /results/i.test(b.textContent)); b && b.click(); }")
    pg.wait_for_timeout(1900)
    rise_verdict("back to the results", pg.evaluate("() => window.__rise"), qn)
    ctx.close()
    # the race board's exits
    ctx, pg = boot(br, 440, 956)
    pg.evaluate(RISE_LOG, "#vroom-race-cut .vrc-exits")
    pg.evaluate("""() => { vroomMyKey = 'a';
      const P = (k, n, ch, xp, j) => ({ key: k, xp, p: { name: n, avatarChar: ch, joinedAt: j, finished: true, xp, xpLines: [{ key: 'correct', label: 'Correct', value: xp }] } });
      playVroomRaceCutscene([P('a', 'Madison', 'ninja', 300, 1), P('b', 'Sam', 'ghost', 200, 2), P('c', 'Lee', 'wizard', 100, 3)]); }""")
    for _ in range(80):
        if pg.evaluate("() => !!(window.__rise && window.__rise.log.length > 50)"):
            break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(1700)
    rise_verdict("the race board", pg.evaluate("() => window.__rise"), qn)
    ctx.close()


# ---------------------------------------------------------------- 2. dim
def sec_dim(br):
    print("\n2. the default hundo effect dims the screen like the others")
    ctx, pg = boot(br, 440, 956, fx="confetti")
    pg.evaluate("""() => { window.__dim = []; const rc = celebrate; window.celebrate = function(){ const r = rc.apply(this, arguments);
      const t0 = performance.now(); const tick = () => { const t = performance.now() - t0;
        /* the darkest full-screen layer the effect has put up, and the box */
        let dim = 0; document.querySelectorAll('.confetti-layer > *').forEach(e => { const cs = getComputedStyle(e), b = e.getBoundingClientRect();
          if(b.width >= innerWidth - 1 && b.height >= innerHeight - 1 && /gradient|rgb/.test(cs.backgroundImage + cs.backgroundColor) && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' || (b.width >= innerWidth - 1 && b.height >= innerHeight - 1 && cs.backgroundImage !== 'none')) dim = Math.max(dim, +cs.opacity); });
        const g = document.querySelector('.rs-grade'); const lay = document.querySelector('.confetti-layer');
        const over = g && lay ? (+getComputedStyle(g).zIndex || 0) > (+getComputedStyle(lay).zIndex || 0) : false;
        __dim.push([t, dim, over]); if(t < 3600) requestAnimationFrame(tick); }; requestAnimationFrame(tick); return r; }; }""")
    pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
    for _ in range(160):
        if pg.evaluate("() => window.__dim.length && window.__dim[window.__dim.length - 1][0] > 3500"):
            break
        pg.wait_for_timeout(250)
    d = pg.evaluate("() => window.__dim")
    peak = max([x[1] for x in d] or [0])
    at1 = [x[1] for x in d if 700 <= x[0] <= 1300]
    late = [x[1] for x in d if x[0] >= 3050]
    over = [x[2] for x in d if 300 <= x[0] <= 1500]
    check("Confetti: the screen dims while it plays (the Fireworks' .5 at its height)", .4 <= peak <= .6 and at1 and min(at1) >= .4, "peak %.2f" % peak)
    check("Confetti: the dim is in within .5s and gone by 3s", bool(d) and next((x[0] for x in d if x[1] >= .4), 9999) <= 550 and (not late or max(late) < .02),
          [next((round(x[0]) for x in d if x[1] >= .4), None), late[:3]])
    check("Confetti: the 100% box is lifted over it, as the Fireworks lift theirs", bool(over) and all(over), over[:3])
    ctx.close()


# ---------------------------------------------------------------- 3. glow
def _rgba(s):
    m = re.search(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)", s or "")
    if m:
        return [float(m.group(i)) for i in (1, 2, 3)] + [float(m.group(4) or 1)]
    m = re.search(r"color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)(?: / ([\d.]+))?\)", s or "")
    if m:
        return [float(m.group(i)) * 255 for i in (1, 2, 3)] + [float(m.group(4) or 1)]
    return None


def sec_glow(br):
    print("\n3. the 100 lights into its effect's glow smoothly, in that glow's colour")
    for fx in ("fireworks", "underwater", "bubbles", "ufo"):
        ctx, pg = boot(br, 440, 956, fx=fx)
        pg.evaluate("""() => { window.__gl = []; const g0 = () => document.querySelector('.rs-grade');
          const mo = new MutationObserver(() => { const g = g0(); if(!g || !g.classList.contains('rs-graded') || window.__glOn) return; window.__glOn = 1;
            const t0 = performance.now(); const tick = () => { const t = performance.now() - t0, p = g.querySelector('.rs-pct');
              __gl.push([t, getComputedStyle(p).filter]); if(t < 1400) requestAnimationFrame(tick); }; tick(); });
          mo.observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] }); }""")
        pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
        for _ in range(120):
            if pg.evaluate("() => window.__gl.length && window.__gl[window.__gl.length - 1][0] > 1300"):
                break
            pg.wait_for_timeout(250)
        gl = pg.evaluate("() => window.__gl")
        fin = _rgba(gl[-1][1]) if gl else None
        bad, blur = [], []
        for t, f in gl:
            c = _rgba(f)
            if not c or not fin:
                continue
            m = re.search(r"([\d.]+)px\)?\s*$", f.replace(")", ") ").strip())
            if c[3] > .05 and max(abs(c[j] - fin[j]) for j in range(3)) > 40:
                bad.append((round(t), [round(v) for v in c[:3]]))
        rad = []
        for t, f in gl:
            m = re.findall(r"([\d.]+)px", f)
            if m:
                rad.append((t, float(m[-1])))
        jumps = [(round(rad[i][0]), round(rad[i][1] - rad[i - 1][1], 1)) for i in range(1, len(rad)) if rad[i][1] - rad[i - 1][1] > 4.5]
        check("%s: the 100's glow is the effect's own colour at every frame it eases in (never dark)" % fx, bool(gl) and fin is not None and not bad,
              bad[:4] or (fin and [round(v) for v in fin[:3]]))
        check("%s: ... and grows without a jump" % fx, bool(rad) and not jumps, jumps[:3])
        ctx.close()


# ---------------------------------------------------------------- 4. chat
def sec_chat(br):
    print("\n4. the chat button stays where it is through a hundo effect")
    for fx in ("fireworks", "underwater", "ufo"):
        ctx, pg = boot(br, 440, 956, fx=fx)
        pg.evaluate("""() => { window.__ch = []; const real = playHundoFx; window.playHundoFx = function(a, b){ const h = real(a, b); const t0 = performance.now();
          const tick = () => { const t = performance.now() - t0, c = document.querySelector('.chatdock-btn');
            if(c){ const r = c.getBoundingClientRect(), cs = getComputedStyle(c); __ch.push([t, Math.round(r.top), Math.round(r.left), cs.visibility, +cs.opacity, cs.pointerEvents]); }
            if(t < (HUNDO_FX_TOTAL[a] || 7000) + 900) requestAnimationFrame(tick); }; tick(); return h; }; }""")
        pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
        for _ in range(200):
            if pg.evaluate("() => window.__ch.length && window.__ch[window.__ch.length - 1][0] > (HUNDO_FX_TOTAL[store.hundoFx] || 7000) + 800"):
                break
            pg.wait_for_timeout(250)
        ch = pg.evaluate("() => window.__ch")
        tops = [x[1] for x in ch]
        hidden = [x for x in ch if x[3] == "hidden" or x[4] < .9 or x[1] < -1]
        check("%s: the chat button is there, unmoved, for the whole effect" % fx, bool(ch) and max(tops) - min(tops) <= 1 and not hidden,
              (min(tops) if tops else None, max(tops) if tops else None, hidden[:2]))
        check("%s: ... and takes a tap" % fx, bool(ch) and all(x[5] != "none" for x in ch), [x[5] for x in ch if x[5] == "none"][:1])
        ctx.close()


# ---------------------------------------------------------------- 5. edges
EDGE = r"""(sel) => { const e = document.querySelector(sel); if(!e) return null; const cs = getComputedStyle(e);
  const tint = e.querySelector(':scope > .hfx-tint'); const ts = tint ? getComputedStyle(tint) : null;
  return { border: cs.borderTopColor, shadow: cs.boxShadow, tint: ts && +ts.opacity > .5 ? ts.boxShadow : '' }; }"""


def edge_ok(e):
    """an opaque rim, an inset 1px line, and an inset glow 24px+ deep, all one hue"""
    if not e:
        return False, "missing"
    b = _rgba(e["border"])
    sh = (e["shadow"] or "") + "," + (e["tint"] or "")
    insets = re.findall(r"(rgba?\([^)]*\)|color\([^)]*\))\s+0px\s+0px\s+([\d.]+)px\s+([\d.]+)px\s+inset", sh)
    insets += [(m[0], m[1], "0") for m in re.findall(r"(rgba?\([^)]*\)|color\([^)]*\))\s+0px\s+0px\s+([\d.]+)px\s+inset", sh)]
    line = [c for (c, bl, sp) in insets if float(bl) == 0 and float(sp) >= 1]
    glow = [c for (c, bl, sp) in insets if float(bl) >= 24]
    same = lambda c: b and _rgba(c) and max(abs(_rgba(c)[j] - b[j]) for j in range(3)) <= 12
    ok = bool(b) and b[3] >= .9 and any(same(c) for c in line) and any(same(c) for c in glow)
    return ok, {"border": e["border"], "line": line[:1], "glow": glow[:1]}


def sec_edges(br):
    print("\n5. every card on the results has the hundo box's hard edge, in its own colour")
    ctx, pg = boot(br, 440, 956, fx="bubbles")
    pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
    wait_done(pg)
    pg.wait_for_timeout(1200)
    ok, d = edge_ok(pg.evaluate(EDGE, ".rs-grade.hfx-tinted"))
    check("the hundo box (Bubbles) is the recipe: a rim, a 1px line and a deep glow, one hue", ok, d)
    ok, d = edge_ok(pg.evaluate(EDGE, ".rs-xp"))
    check("the XP card has it, in its blue", ok, d)
    ctx.close()
    # a pass, and a run that unlocks something
    ctx, pg = boot(br, 440, 956, fx="confetti")
    pg.evaluate("() => __run('Identity Crimes', 2, 'drill', false)")
    wait_done(pg)
    ok, d = edge_ok(pg.evaluate(EDGE, ".rs-grade"))
    check("the grade of a pass has it, in its green", ok, d)
    ctx.close()
    ctx, pg = boot(br, 440, 956, fx="confetti")
    pg.evaluate("() => { store.lifetime.perfectTests = 49; theme.muteBanners = true; store.unlocksShown.fx = []; saveStore(); }")
    pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
    wait_done(pg, 70000)
    pg.wait_for_timeout(800)
    ok, d = edge_ok(pg.evaluate(EDGE, ".rs-unlocked"))
    check("the Found & unlocked card has it, in its violet", ok, d)
    ctx.close()


# ---------------------------------------------------------------- 6. water
WATER_LOG = r"""() => { window.__uw = { log: [], ev: [] }; const real = playHundoFx; window.playHundoFx = function(a, b){ const h = real(a, b); const t0 = performance.now();
  const av = document.querySelector('.rs-screen .results-level-avatar');
  new MutationObserver(() => { __uw.ev.push([performance.now() - t0, av.classList.contains('char-hold') ? 'hold' : av.classList.contains('char-gasp') ? 'gasp' : '-']); }).observe(av, { attributes: true, attributeFilter: ['class'] });
  const face = () => { const m = av.querySelector('svg .cx-mouth'); const r = m && m.getBoundingClientRect(); if(r && r.height) return r.top + r.height / 2;
    const e = av.querySelector('svg .cx-eyes'); const q = e && e.getBoundingClientRect(); return q ? q.top + q.height / 2 : 0; };
  const tick = () => { const t = performance.now() - t0, sf = document.querySelector('.hfx-uw-sea > .hfx-uw-surface, .hfx-uw-surface'), sea = document.querySelector('.hfx-uw-sea');
    let line = null; if(sf){ const r = sf.getBoundingClientRect(); line = r.top + r.height * .7; }
    const fish = [...document.querySelectorAll('.hfx-layer [class*="fish"], .hfx-layer .hfx-uw-f')].filter(f => { const r = f.getBoundingClientRect(); return r.width > 4 && r.right > 0 && r.left < innerWidth && r.bottom > 0 && r.top < innerHeight && +getComputedStyle(f).opacity > .05; }).length;
    const manta = document.querySelectorAll('.hfx-layer [class*="manta"]').length;
    __uw.log.push([t, line, face(), fish, manta, sea ? Math.round(sea.getBoundingClientRect().top) : null]);
    if(t < 7600) requestAnimationFrame(tick); }; tick(); return h; }; }"""


def sec_water(br):
    print("\n6. Underwater: no shadow, drawn fish while the sea is up, the breath held only under it")
    ctx, pg = boot(br, 440, 956, fx="underwater")
    pg.evaluate(WATER_LOG)
    pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
    for _ in range(200):
        if pg.evaluate("() => window.__uw.log.length && window.__uw.log[window.__uw.log.length - 1][0] > 7500"):
            break
        pg.wait_for_timeout(250)
    r = pg.evaluate("() => window.__uw")
    log, ev = r["log"], r["ev"]
    vh = 956
    check("no manta (the dark shape) at any frame", bool(log) and all(x[4] == 0 for x in log), max([x[4] for x in log] or [0]))
    # the fish: drawn, and only ever on screen while the water is up (its
    # surface in the top fifth of the screen)
    art = pg.evaluate("""() => { try{ const u = hfxFishURL(1); const sp = Object.values(hfxSprites).find(s => s && (s.png === u || s.svg === u)) || null;
      const t = sp ? sp.text : decodeURIComponent((u.match(/data:image\\/svg\\+xml,(.*)"\\)$/) || [])[1] || '');
      return { shapes: (t.match(/<(path|circle|ellipse|rect|polygon)\\b/g) || []).length, colours: new Set(t.match(/#[0-9a-fA-F]{6}/g) || []).size }; }catch(e){ return null; } }""")
    check("the fish are drawn: a body, fins, markings and an eye (12+ shapes, 5+ colours)", bool(art) and art["shapes"] >= 12 and art["colours"] >= 5, art)
    seen = [x for x in log if x[3] > 0]
    dry = [(round(x[0]), x[5]) for x in seen if x[1] is None or x[1] > vh * .2]
    check("fish swim across while the sea is up", len(seen) >= 30, len(seen))
    check("... and never while it is rising or draining (nothing left in the air)", bool(seen) and not dry, dry[:4])
    # the breath, against the face, on every frame
    under = [x for x in log if x[1] is not None and x[2] and x[1] <= x[2]]
    t_cover = under[0][0] if under else None
    t_clear = next((x[0] for x in log if t_cover is not None and x[0] > t_cover + 500 and x[1] is not None and x[1] > x[2]), None)
    t_hold = next((t for (t, s) in ev if s == "hold"), None)
    t_rel = next((t for (t, s) in ev if s != "hold" and t_hold is not None and t > t_hold), None)
    lead = (t_cover - t_hold) / 1000 if (t_cover is not None and t_hold is not None) else None
    lag = (t_rel - t_clear) / 1000 if (t_clear is not None and t_rel is not None) else None
    check("the breath is taken as the water reaches the face, not before it (<= .18s ahead)", lead is not None and -0.05 <= lead <= .18, lead)
    check("... and let go as the water leaves the face, not after (<= .15s)", lag is not None and lag <= .15, lag)
    ctx.close()


# ---------------------------------------------------------------- 7. tick
def sec_tick(br):
    print("\n7. no check mark on a pass")
    ctx, pg = boot(br, 440, 956)
    r = pg.evaluate("""() => { const ids = AVATAR_CHARACTERS.filter(c => !RETIRED_CHARACTER_TO[c.id]).map(c => c.id).concat(['__generic__']); const out = [];
      ids.forEach(id => { const av = document.createElement('span'); av.className = 'results-level-avatar';
        av.appendChild(id === '__generic__' ? (() => { const s = buildAvatarCharSVGSafe('ninja'); s.setAttribute('data-char', 'zz-unknown'); return s; })() : buildAvatarCharSVGSafe(id));
        document.body.appendChild(av); reactCharacter(av, 'pass');
        /* anything drawn ON the circle for a pass: the sign layers' pieces */
        const marks = [...av.querySelectorAll(':scope > .char-emote > *')].filter(i => { const cs = getComputedStyle(i); return cs.display !== 'none' && (cs.backgroundImage !== 'none' || cs.backgroundColor !== 'rgba(0, 0, 0, 0)'); });
        out.push([id, marks.length]); av.remove(); });
      return out; }""")
    bad = [x for x in r if x[1]]
    check("every character's pass (%d, and one the table does not know) puts nothing on its circle" % len(r), bool(r) and not bad, bad[:6])
    ctx.close()


# ---------------------------------------------------------------- 8. centre
CENTRE = r"""() => { document.getElementById('b325c')?.remove();
  const ids = AVATAR_CHARACTERS.filter(c => !RETIRED_CHARACTER_TO[c.id]).map(c => c.id);
  const host = document.createElement('div'); host.id = 'b325c';
  host.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#181d25;display:grid;grid-template-columns:repeat(6,100px);gap:10px;padding:10px';
  document.body.appendChild(host);
  ids.forEach(id => { const c = document.createElement('span'); c.className = 'results-level-avatar'; const sv = buildAvatarCharSVGSafe(id);
    sv.querySelectorAll(':scope > g.cx-bg, :scope g.cx-bg').forEach(n => n.style.display = 'none');
    sv.querySelectorAll('circle').forEach(n => { if(/url\(#(aura|halo)-/.test(n.getAttribute('fill') || '')) n.style.display = 'none'; });
    c.appendChild(sv); host.appendChild(c); });
  return ids; }"""
TH = 64


def sec_centre(br):
    print("\n8. every character is centred in its circle")
    ctx, pg = cb.booted(br, 1000, 1000, seed=cb.USED_ACCOUNT, dpr=2)
    ids = pg.evaluate(CENTRE)
    pg.wait_for_timeout(500)
    boxes = pg.evaluate("()=>[...document.querySelectorAll('#b325c .results-level-avatar')].map(e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.width]})")
    a = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    pg.evaluate("()=>document.querySelectorAll('#b325c svg').forEach(s=>s.style.visibility='hidden')")
    b = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > TH else 0)
    off = []
    for cid, (x, y, w) in zip(ids, boxes):
        c = d.crop((int(x * 2), int(y * 2), int((x + w) * 2), int((y + w) * 2)))
        W = c.width
        # a row counts when 2+ of its pixels are ink
        rows = [yy for yy in range(W) if c.crop((0, yy, W, yy + 1)).histogram()[255] >= 2]
        if not rows:
            off.append((cid, "no ink"))
            continue
        mid = (rows[0] + rows[-1]) / 2 / W * 100
        if abs(mid - 50) > 3:
            off.append((cid, round(mid, 1)))
    check("all %d characters: what you see of each is centred in the results circle (within 3%%)" % len(ids), len(ids) >= 30 and not off, off)
    # the same centred drawing everywhere: the figure is moved inside the
    # drawing, so the boards, Profile, the tab bar and Customize carry it
    r = pg.evaluate("""() => { const out = {}; const probe = sv => { const g = sv && sv.querySelector('.cx-centre'); return g ? (g.getAttribute('transform') || 'none') : null; };
      out.row = probe(avatarSpanFor({ avatarChar: 'clown' }).querySelector('svg'));
      out.plate = probe(platePortrait(avatarSpanFor({ avatarChar: 'clown' })).querySelector('svg'));
      out.pick = probe(pickerCharSVG('clown'));
      out.sil = probe(charSilhouetteSVG('clown'));
      const w = buildAvatarCharSVGSafe('clown'); w.setAttribute('viewBox', AVATAR_WIDE_VIEWBOX); out.wide = probe(w);
      return out; }""")
    check("the boards, the plate (Profile, person card), Customize, the silhouette and the tab all draw the centred figure",
          all(v and "translate" in v for v in r.values()), r)
    ctx.close()


SECTIONS = [("rise", sec_rise), ("dim", sec_dim), ("glow", sec_glow), ("chat", sec_chat), ("edges", sec_edges),
            ("water", sec_water), ("tick", sec_tick), ("centre", sec_centre)]

if __name__ == "__main__":
    print("check-b325-a against", cb.SRC)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for name, fn in SECTIONS:
            if ONLY and name not in ONLY:
                continue
            try:
                fn(br)
            except Exception as e:
                check("%s ran" % name, False, str(e)[:300])
        br.close()
    cb.SERVER.shutdown()
    print("\n%d failure(s)" % len(cb.FAILURES))
    for f in cb.FAILURES:
        print("  - " + f)
    sys.exit(1 if cb.FAILURES else 0)
