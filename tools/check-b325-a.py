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
# The moment a set of buttons is put on screen, every animation on each
# button and on its row, as keyframes and timing - read off the page, not
# sampled, so a loaded machine cannot blur it.
RISE_LOG = r"""(sel) => { window.__rise = null;
  const snap = el => { const btns = [...el.querySelectorAll(':scope > button, :scope > .next')].filter(b => !b.hidden);
    const anim = n => n.getAnimations().map(a => { const k = a.effect.getKeyframes(), t = a.effect.getTiming();
      return { name: a.animationName || a.id || '', first: k[0] && (k[0].transform || k[0].translate || ''), firstOp: k[0] && k[0].opacity, last: k[k.length - 1] && (k[k.length - 1].transform || ''),
        dur: t.duration, delay: t.delay, ease: t.easing, kEase: k[0] && k[0].easing, ops: k.map(f => [f.offset, f.computedOffset, f.opacity]) }; });
    const ty = n => { try{ return new DOMMatrixReadOnly(getComputedStyle(n).transform).m42; }catch(e){ return 0; } };
    window.__rise = { n: btns.length, rows: btns.map(b => b.offsetTop), row: anim(el), btn: btns.map(anim), y: btns.map(ty), op: btns.map(b => +getComputedStyle(b).opacity) }; };
  const shown = el => { const v = el.closest('.vrc'); if(v) return v.classList.contains('is-done');
    return el.classList.contains('rs-in') || el.classList.contains('rs-in-now') || !el.classList.contains('rs-land'); };
  const arm = () => { const el = document.querySelector(sel); if(!el) return false;
    if(shown(el)){ snap(el); return true; }
    const mo = new MutationObserver(() => { if(shown(el)){ mo.disconnect(); snap(el); } });
    mo.observe(el.closest('.vrc') || el, { attributes: true, attributeFilter: ['class'], subtree: true }); return true; };
  if(!arm()){ const mo = new MutationObserver(() => { if(arm()) mo.disconnect(); }); mo.observe(document.body, { childList: true, subtree: true }); } }"""
# The Next question pill's own rise, read off the stylesheet.
QNEXT = r"""() => { let rule = null, kf = null;
  for(const sh of document.styleSheets){ let rules; try{ rules = sh.cssRules; }catch(e){ continue; }
    for(const r of rules){ if(r.selectorText && /\.qnext\.is-rising/.test(r.selectorText) && r.style.animationName) rule = rule || r; if(r.type === 7 && r.name === 'qnext-rise') kf = r; } }
  if(!rule) return null;
  const o35 = kf ? [...kf.cssRules].find(k => k.keyText === '35%') : null;
  return { dur: parseFloat(rule.style.animationDuration) * 1000, ease: rule.style.animationTimingFunction.replace(/\s/g, ''), opIn: o35 ? +o35.style.opacity : null }; }"""


def _ty(tf):
    """the y a keyframe's transform puts it at, as a sign: below (+), above (-), in calc() too"""
    if not tf:
        return 0
    m = re.search(r"translate(?:Y)?\(([^)]*)\)", tf)
    if not m:
        return 0
    arg = m.group(1).split(",")[-1] if "translateY" not in tf else m.group(1)
    if "calc(" in tf and "100%" in tf:
        return 1 if "-100%" not in tf and "- 100%" not in tf else -1
    n = re.search(r"(-?[\d.]+)px", arg)
    return float(n.group(1)) if n else 0


def rise_verdict(label, r, qn):
    if not r:
        check("%s: its buttons come up when they are put on screen" % label, False, "never shown")
        return
    rises = []
    for b in range(r["n"]):
        own = [a for a in r["btn"][b] if _ty(a["first"]) > 0 and (a["firstOp"] in (0, "0")) and not _ty(a["last"])]
        rises.append(own[0] if own else None)
    drop = [a for a in r["row"] if _ty(a["first"]) < 0]
    check("%s: every button starts below where it rests, unseen, and rises into it" % label,
          r["n"] >= 1 and all(rises) and not drop, [r["btn"], r["row"]][:2] if not all(rises) or drop else r["n"])
    same = qn is not None and all(a and abs(a["dur"] - qn["dur"]) < 1 and (a["ease"] or "").replace(" ", "") == qn["ease"] or
                                  a and abs(a["dur"] - qn["dur"]) < 1 and (a["ease"] or "") == "linear" and (a.get("kEase") or "").replace(" ", "") == qn["ease"] for a in rises)
    opin = all(a and any(abs((o[1] or 0) - .35) < .01 and float(o[2] or 0) == 1 for o in a["ops"]) for a in rises)
    check("%s: on the Next question pill's own move (%s ms, %s, in by 35%%)" % (label, qn and qn["dur"], qn and qn["ease"]), same and opin,
          [(a and a["dur"], a and a["ease"]) for a in rises])
    rows = sorted(set(round(v / 6) for v in r["rows"]))
    if len(rows) > 1:
        d = {}
        for b in range(r["n"]):
            if rises[b]:
                d.setdefault(round(r["rows"][b] / 6), []).append(rises[b]["delay"])
        check("%s: a row at a time" % label, all(max(d.get(rows[i], [0])) < min(d.get(rows[i + 1], [0])) for i in range(len(rows) - 1)), d)


def sec_rise(br):
    print("\n1. the way-on buttons rise from below, like Next question")
    ctx, pg = boot(br, 440, 956)
    qn = pg.evaluate(QNEXT)
    pg.evaluate(RISE_LOG, ".rs-rewards .rs-actions")
    pg.evaluate("() => __run('Identity Crimes', 2, 'drill', false)")
    ok = wait_done(pg)
    order = pg.evaluate("() => (window.__lands || []).map(l => l.kind)")
    # (the buttons come after every card above them - the order the gate
    # reads them in; not a check of its own, it held before this build)
    if not (ok and order and order[-1] == "actions"):
        check("results (2 missed): the reveal finished with the buttons last", False, order[-6:])
    rise_verdict("results", pg.evaluate("() => window.__rise"), qn)
    pg.wait_for_timeout(1500)
    pg.evaluate(RISE_LOG, ".rs-review .actions")
    pg.evaluate("() => { const b = [...document.querySelectorAll('.rs-actions button')].find(b => /review/i.test(b.textContent)); b && b.click(); }")
    pg.wait_for_timeout(400)
    rise_verdict("the review", pg.evaluate("() => window.__rise"), qn)
    pg.wait_for_timeout(1500)
    pg.evaluate(RISE_LOG, ".rs-rewards .rs-actions")
    pg.evaluate("() => { const b = [...document.querySelectorAll('.rs-review .actions button')].find(b => /results/i.test(b.textContent)); b && b.click(); }")
    pg.wait_for_timeout(400)
    rise_verdict("back to the results", pg.evaluate("() => window.__rise"), qn)
    ctx.close()
    # the daily question: Exit comes up into Submit's spot after the outro
    ctx, pg = boot(br, 440, 956)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      store.dailyQuestionDate = null; saveStore(); document.querySelectorAll('#pushing-update,#intro-pop').forEach(n => n.remove());
      startDailyQuestion();
      for(let t = 0; t < 80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
      await wait(400);
      const sb = document.getElementById('dailyq-submitbtn'); const at = sb && sb.getBoundingClientRect();
      [...document.querySelectorAll('.qpanel .choice')].find(c => +c.dataset.index === correctSlot(order[pos])).click(); await wait(150);
      document.getElementById('dailyq-submitbtn').click();
      for(let t = 0; t < 40 && !document.getElementById('dailyq-exitbtn'); t++) await wait(25);
      const ex = document.getElementById('dailyq-exitbtn'); if(!ex) return null;
      const an = ex.getAnimations().map(a => { const k = a.effect.getKeyframes(), t = a.effect.getTiming(); return { first: k[0] && k[0].transform, firstOp: k[0] && k[0].opacity, dur: t.duration, delay: t.delay, ease: t.easing }; });
      const lines = [...document.querySelectorAll('.dailyq-outro > *')].map(e => e.getAnimations().map(a => { const t = a.effect.getTiming(); return t.delay + t.duration; })).flat();
      await wait(2900);
      const r2 = ex.getBoundingClientRect();
      return { an, lines, spot: at ? [Math.round(at.top), Math.round(r2.top)] : null }; }""")
    rise = [a for a in (r or {}).get("an", []) if a["first"] and "calc(100%" in a["first"] and str(a["firstOp"]) == "0"]
    last_line = max((r or {}).get("lines") or [0])
    check("the daily question: Exit rises (the Next pill's move) once the verdict's lines are in, into Submit's own spot",
          bool(rise) and abs(rise[0]["dur"] - qn["dur"]) < 1 and rise[0]["delay"] >= last_line - 1 and r["spot"] and abs(r["spot"][0] - r["spot"][1]) <= 1,
          [r and r.get("an"), last_line, r and r.get("spot")])
    ctx.close()
    # the race board's exits
    ctx, pg = boot(br, 440, 956)
    pg.evaluate(RISE_LOG, "#vroom-race-cut .vrc-exits")
    pg.evaluate("""() => { vroomMyKey = 'a';
      const P = (k, n, ch, xp, j) => ({ key: k, xp, p: { name: n, avatarChar: ch, joinedAt: j, finished: true, xp, xpLines: [{ key: 'correct', label: 'Correct', value: xp }] } });
      playVroomRaceCutscene([P('a', 'Madison', 'ninja', 300, 1), P('b', 'Sam', 'ghost', 200, 2), P('c', 'Lee', 'wizard', 100, 3)]); }""")
    for _ in range(120):
        if pg.evaluate("() => !!window.__rise"):
            break
        pg.wait_for_timeout(250)
    rise_verdict("the race board", pg.evaluate("() => window.__rise"), qn)
    ctx.close()


# ---------------------------------------------------------------- 2. dim
def sec_dim(br):
    print("\n2. the default hundo effect dims the screen like the others")
    ctx, pg = boot(br, 440, 956, fx="confetti")
    # (build 326: the dim is the one every effect shares, .hfx-dim, its own
    # layer put up beside the burst - looked for there too, a tick later)
    pg.evaluate("""() => { window.__dim = null; const rc = celebrate; window.celebrate = function(){ const r = rc.apply(this, arguments); setTimeout(() => {
      const lay = [...document.querySelectorAll('.confetti-layer')].pop(), g = document.querySelector('.rs-grade');
      /* every full-screen layer the burst put up, and how its opacity runs */
      const full = (lay ? [...lay.children] : []).concat([...document.querySelectorAll('.hfx-dim')]).filter(e => { const b = e.getBoundingClientRect(); return b.width >= innerWidth - 1 && b.height >= innerHeight - 1; });
      window.__dim = { full: full.map(e => e.getAnimations().map(a => { const t = a.effect.getComputedTiming(); return { dur: t.duration, delay: t.delay, k: a.effect.getKeyframes().map(f => [f.computedOffset, f.opacity == null ? null : +f.opacity]) }; })),
        bg: full.map(e => getComputedStyle(e).backgroundImage !== 'none' || getComputedStyle(e).backgroundColor !== 'rgba(0, 0, 0, 0)'),
        over: null };
      setTimeout(() => { __dim.over = g && lay ? (+getComputedStyle(g).zIndex || 0) > (+getComputedStyle(lay).zIndex || 0) : false; }, 300);
      /* the moment the way-on buttons start to come up: how dim the screen still is */
      const dimEl = lay && full.find(e => getComputedStyle(e).backgroundImage !== 'none'), acts = document.querySelector('.rs-actions'), t0 = performance.now();
      if(acts){ const mo = new MutationObserver(() => { if(acts.classList.contains('rs-in-now') || acts.classList.contains('rs-in')){ mo.disconnect();
        __dim.atButtons = { t: Math.round(performance.now() - t0), dim: dimEl && dimEl.isConnected ? +getComputedStyle(dimEl).opacity : 0 }; } });
        mo.observe(acts, { attributes: true, attributeFilter: ['class'] }); }
      }, 0); return r; }; }""")
    pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
    for _ in range(160):
        if pg.evaluate("() => !!window.__dim && window.__dim.over !== null"):
            break
        pg.wait_for_timeout(250)
    d = pg.evaluate("() => window.__dim") or {"full": [], "bg": [], "over": False}
    dims = []
    for an, bg in zip(d["full"], d["bg"]):
        for a in an:
            ks = [k for k in a["k"] if k[1] is not None]
            if bg and ks and max(k[1] for k in ks) > .2:
                dims.append(a)
    a = dims[0] if dims else None
    peak = max(k[1] for k in a["k"] if k[1] is not None) if a else 0
    t_in = next(((a["delay"] + k[0] * a["dur"]) for k in a["k"] if k[1] is not None and k[1] >= peak - .01), None) if a else None
    t_out = (a["delay"] + a["dur"]) if a else None
    end = a["k"][-1][1] if a else None
    check("Confetti: the screen dims while it plays (the Fireworks' .5 at its height)", a is not None and .4 <= peak <= .6, peak)
    check("Confetti: the dim is in within .5s and gone (0) by 3s", a is not None and t_in is not None and t_in <= 500 and t_out <= 3050 and end == 0, [t_in, t_out, end])
    check("Confetti: the 100% box is lifted over it, as the Fireworks lift theirs", d["over"], d["over"])
    # the buttons wait for it: they start to rise only once the dim has lifted
    for _ in range(80):
        if pg.evaluate("() => !!(window.__dim && window.__dim.atButtons)"):
            break
        pg.wait_for_timeout(250)
    ab = pg.evaluate("() => window.__dim && window.__dim.atButtons")
    check("Confetti: the buttons rise only once its dim has lifted (dim 0 as they start)", a is not None and peak >= .4 and bool(ab) and ab["dim"] <= .02, ab)
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
        check("%s: the 100's glow is the effect's own colour at every frame it eases in (never dark, no snap at the end)" % fx,
              len(gl) >= 10 and fin is not None and not bad, bad[:4] or (fin and [round(v) for v in fin[:3]]))
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
    ref, d0 = edge_ok(pg.evaluate(EDGE, ".rs-grade.hfx-tinted"))
    if not ref:
        check("the hundo box (Bubbles) is the recipe: a rim, a 1px line and a deep glow, one hue", False, d0)
    ok, d = edge_ok(pg.evaluate(EDGE, ".rs-xp"))
    check("the XP card has the hundo box's edge (Bubbles' here), in its blue", ok and ref, d)
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
  /* at the very moment the breath is taken or let go: where the surface is against the face */
  const at = () => { const sf = document.querySelector('.hfx-uw-surface'); if(!sf) return null; const r = sf.getBoundingClientRect(); return Math.round(r.top + r.height * .7 - face()); };
  new MutationObserver(() => { __uw.ev.push([performance.now() - t0, av.classList.contains('char-hold') ? 'hold' : av.classList.contains('char-gasp') ? 'gasp' : '-', at()]); }).observe(av, { attributes: true, attributeFilter: ['class'] });
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
    U = pg.evaluate("() => HFX_UW")
    up, down = (U["rise"] + U["riseD"]) * 1000, U["drain"] * 1000
    dry = [(round(x[0]), x[5]) for x in seen if x[1] is None or x[1] > vh * .2 or x[0] < up - 50 or x[0] > down + 50]
    check("drawn fish swim across while the sea is up - in after it has risen (%.2fs), out of frame before it drains (%.2fs)" % (up / 1000, down / 1000),
          len(seen) >= 30 and not dry and bool(art) and art["shapes"] >= 12, [len(seen), dry[:4], art])
    ctx.close()
    # the breath, frame by frame on the recorders' clock (record-hundo's: the
    # page's timers, frames and every animation stepped 1/30s together), so
    # a loaded machine cannot move it: how far below the eyes the surface is
    # (px; negative = over them) and whether the breath is held
    rh = open(os.path.join(HERE, "record-hundo.py")).read()
    j = rh.index('CLOCK = r"""') + len('CLOCK = r"""')
    clock = rh[j:rh.index('"""', j)]
    ctx, pg = boot(br, 440, 956, fx="underwater")
    pg.evaluate("() => { window.__fxAt = 0; const real = playHundoFx; window.playHundoFx = function(a, b){ window.__fxAt = performance.now(); return real(a, b); }; }")
    pg.wait_for_timeout(1200)
    pg.evaluate(clock)
    pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
    for _ in range(1500):
        if pg.evaluate("() => window.__fxAt > 0"):
            break
        pg.evaluate("() => __clk.advance(1000 / 30)")
    S = """() => { const av = document.querySelector('.rs-screen .results-level-avatar'), e = av && av.querySelector('svg .cx-eyes'), sf = document.querySelector('.hfx-uw-surface');
      if(!e || !sf) return null; const r = e.getBoundingClientRect(), q = sf.getBoundingClientRect();
      return [av.classList.contains('char-hold') ? 1 : 0, Math.round(q.top + q.height * .7 - (r.top + r.height / 2))]; }"""
    fr = []
    for k in range(int(7.0 * 30)):
        pg.evaluate("async () => { await __clk.advance(1000 / 30); }")
        v = pg.evaluate(S)
        if v:
            fr.append([round((k + 1) / 30, 2)] + v)
    early = [f for f in fr if f[1] and f[2] > 120]
    held = [f for f in fr if f[1]]
    under = [f for f in fr if f[2] <= -60]
    dry_under = [f for f in under if not f[1]]
    check("the breath is held on every frame the water is over the face, and never while it is still, or again, well below it (>120px under the eyes)",
          bool(held) and not early and bool(under) and not dry_under, [early[:3], dry_under[:3]] if (early or dry_under) else held[:1])
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
