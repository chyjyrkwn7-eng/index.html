#!/usr/bin/env python3
"""Build 326, package A - the results screen, the hundo effects, Stats and
Save and exit.

  python3 tools/check-b326-a.py [--against OLD/index.html] [--only NAME,...]

Madison's list (Oct 18, second), one section each:
  1. sum      "The xp box for results, in the total section under the
              amount of xp you got it has a description ... remove that."
              Nothing under the XP total; the total is the lines' sum.
  2. streak   "The answers in a row one got worse somehow." The line under
              "Answers in a row" says the marks reached, in words: no
              "in a row" said again, no "+N" jammed in, a count as a word.
  3. stats    "In stats it's calling a Hundo a perfect test ... some are in
              blue green and gold, what's going on?" Nowhere on Stats, Test
              history or a test's page says "perfect"; a test that earned a
              hundo says Hundo; and every test is in ONE colour - its
              mode's (ring, wash and chip agree), whatever its score.
  4. save     "The save and exit button is clear and see through? Thats a
              terrible idea." Save and exit is opaque, no backdrop blur,
              not Quit's colour, its words at 4.5:1 or better, 44px+, as
              wide and tall as Resume and Quit.
  5. dim      "The bubble effect ... doesn't [dim] the background like the
              others. Ensure each effect dims the same." Every effect puts
              up ONE dim (.hfx-dim) and no dim of its own: the same colour,
              the same peak, up over the same time from the effect's first
              frame and down over the same time to nothing at the moment
              the buttons rise (HUNDO_FX_TAIL_AT); the 100% box is over it
              the whole time.
  6. edges    "UFO effect, the score box border of it before the ufo arrives
              it doesn't have the same border like xp, it's not as dark."
              On every effect, at the effect's first frame, in the middle
              of it and after it, every card on the results screen carries
              the XP card's edge: an opaque rim, a 1px line inside it at
              the XP card's strength and a glow off the edge as deep and
              as strong.
  7. water    "I don't like the fish you got going on ... when the water
              goes down and away, the boxes lag/glitch." Drawn fish with no
              outline and nothing dark but an eye; four or more species at
              three depths (sizes); each swims (turns with its path) and
              its tail beats; none left once the drain starts; no
              backdrop-filter anywhere in the water; the buttons rise only
              once the water has gone; and every card is at rest by then.

Every section fails on 5869856 (build 325) - run --against. The effect
sections run on the page's own clock (record-hundo's: every animation
paused and seeked, every timer on it), so a loaded machine cannot blur
them."""
import importlib.util
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

_RES = open(os.path.join(HERE, "check-results.py")).read()
_i = _RES.index('SETUP = """') + len('SETUP = """')
SETUP = _RES[_i:_RES.index('"""', _i)]
_RH = open(os.path.join(HERE, "record-hundo.py")).read()
_i = _RH.index('CLOCK = r"""') + len('CLOCK = r"""')
CLOCK = _RH[_i:_RH.index('"""', _i)]

PHONE = ("iPhone 17 Pro Max", 440, 956)
TABLET = ("iPad Pro 11\"", 834, 1194)
CLEAN = "() => { document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); }"


def boot(br, w, h):
    ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT)
    pg.evaluate(SETUP)
    pg.evaluate(CLEAN)
    return ctx, pg


def parse_col(c):
    """[r, g, b, a] of a computed colour: rgb(), rgba() or color(srgb r g b / a)."""
    if not c:
        return None
    m = re.match(r"rgba?\(([^)]*)\)", c)
    if m:
        v = [float(x) for x in re.split(r"[ ,/]+", m.group(1).strip()) if x]
        return v[:3] + [v[3] if len(v) > 3 else 1.0]
    m = re.match(r"color\(srgb ([^)]*)\)", c)
    if m:
        v = [float(x) for x in re.split(r"[ /]+", m.group(1).strip()) if x]
        return [v[0] * 255, v[1] * 255, v[2] * 255, v[3] if len(v) > 3 else 1.0]
    return None


def shadows(bs):
    """[(colour, [lengths in px], inset)] of a computed box-shadow."""
    out = []
    if not bs or bs == "none":
        return out
    for part in re.split(r",(?![^(]*\))", bs):
        part = part.strip()
        m = re.match(r"((?:rgba?|color)\([^)]*\))\s*(.*)", part)
        if not m:
            continue
        rest = m.group(2)
        out.append((parse_col(m.group(1)), [float(x) for x in re.findall(r"(-?[\d.]+)px", rest)], "inset" in rest))
    return out


def edge_of(card):
    """(rim alpha, inner 1px line alpha, inner glow (blur px, alpha)) of a
    card as sampled: its own shadows, and its .hfx-tint's when that is
    fully shown."""
    sh = shadows(card["bs"])
    if card.get("tint") and card["tint"]["op"] >= .99:
        sh += shadows(card["tint"]["bs"])
    line = max([s[0][3] for s in sh if s[2] and s[0] and len(s[1]) >= 4 and s[1][3] == 1 and s[1][2] == 0] or [0])
    glow = max([(s[1][2], s[0][3]) for s in sh if s[2] and s[0] and len(s[1]) >= 3 and s[1][2] >= 20] or [(0, 0)])
    rim = parse_col(card["border"])
    return (round(rim[3], 2) if rim else 0, round(line, 2), (round(glow[0]), round(glow[1], 2)))


# ------------------------------------------------------------ the effect's own clock
FX_PREP = r"""(fx) => { store.lifetime.perfectTests = 600; store.hundoFx = fx;
  const u = typeof pendingHomeUnlocks === 'function' ? pendingHomeUnlocks() : null; if(u) markUnlocksShown(u.chars, u.banners, u.fx); saveStore();
  try{ hfxWarm(fx); }catch(e){}
  window.__fxAt = 0; window.__riseAt = null;
  const real = playHundoFx; window.playHundoFx = function(a, b){ window.__fxAt = performance.now(); return real(a, b); };
  const rc = celebrate; window.celebrate = function(a, b, c){ if(!window.__fxAt) window.__fxAt = performance.now(); return rc(a, b, c); };
  new MutationObserver(() => { const a = document.querySelector('.rs-rewards .rs-actions');
    if(a && window.__riseAt == null && (a.classList.contains('rs-rising') || a.classList.contains('rs-in') || a.classList.contains('rs-in-now')) && window.__fxAt) window.__riseAt = performance.now() - window.__fxAt; })
    .observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] }); }"""


def fx_session(br, w, h, fx):
    ctx, pg = boot(br, w, h)
    pg.evaluate(FX_PREP, fx)
    pg.wait_for_timeout(1500)
    pg.evaluate(CLOCK)
    pg.evaluate("() => __run('Identity Crimes', 0, 'drill', false)")
    for _ in range(400):
        if pg.evaluate("async () => { await __clk.advance(100); return window.__fxAt > 0; }"):
            break
    return ctx, pg


def fx_to(pg, t, step=50):
    """advance the page's clock to t s after the effect started"""
    pg.evaluate("""async ([t, step]) => { for(let i = 0; i < 2000 && performance.now() - window.__fxAt < t * 1000 - .5; i++)
      await __clk.advance(Math.min(step, t * 1000 - (performance.now() - window.__fxAt))); }""", [t, step])


SAMPLE = r"""() => {
  const vis = e => { const cs = getComputedStyle(e); return e.getClientRects().length && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  const DIMS = /(^|\s)(hfx-dim|hfx-fw-dim|hfx-ufo-dim|hfx-bh-dim|stardust-dim|hfx-ufo-boxdim)(\s|$)/;
  const dims = [...document.querySelectorAll('[class]')].filter(e => DIMS.test(String(e.className)) && vis(e))
    .map(e => ({ cls: String(e.className), op: +getComputedStyle(e).opacity, z: getComputedStyle(e).zIndex,
      kf: e.getAnimations().map(a => ({ d: a.effect.getTiming().duration, k: a.effect.getKeyframes().map(f => [Math.round(f.computedOffset * 1000) / 1000, f.opacity]) })) }));
  const g = document.querySelector('.rs-screen .rs-grade');
  const cards = [...document.querySelectorAll('#stage .rs-screen > .rs-card')].filter(c => vis(c) && +getComputedStyle(c).opacity > .5).map(c => {
    const cs = getComputedStyle(c), t = c.querySelector(':scope > .hfx-tint');
    return { cls: String(c.className).split(' ').filter(x => /^rs-(grade|xp|unlocked|badges)$|^vroom-waitcard$/.test(x)).join('.'),
      border: cs.borderTopColor, bs: cs.boxShadow, tint: t ? { op: +getComputedStyle(t).opacity, bs: getComputedStyle(t).boxShadow } : null };
  });
  return { dims, cards, gz: g ? getComputedStyle(g).zIndex : null, gpos: g ? getComputedStyle(g).position : null,
    tail: (typeof HUNDO_FX_TAIL_AT === 'object' && HUNDO_FX_TAIL_AT) || {}, total: (typeof HUNDO_FX_TOTAL === 'object' && HUNDO_FX_TOTAL) || {} };
}"""


# --------------------------------------------------------------------------
RUN3 = """async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  theme.reduceMotion = true; try{ applyTheme(); }catch(e){} store.seenFirstResultsTour = true;
  window.playBadgeCaseScene = (u, d) => { setTimeout(d, 30); return {}; };
  const units = ['Identity Crimes', 'Victims of Crime', 'TCOLE Rules'];
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = units; cfg.size = 0;
  order = QUESTIONS.map((q,i) => [q,i]).filter(([q]) => units.indexOf((q.topic||'').trim()) >= 0 && (typeof inWholeUnit !== 'function' || inWholeUnit(q))).map(([,i]) => i);
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false; practiceTestMinutes = null; inVirtualRoom = false;
  attempts = {}; picked = {}; timedOutSet = {};
  order.forEach((qi, k) => { const oo = optionOrder(qi), right = oo.indexOf(QUESTIONS[qi].answer), bad = k === 25;
    attempts[qi] = bad ? 2 : 1; picked[qi] = bad ? (right + 1) % oo.length : right; });
  runStartTime = Date.now() - order.length * 9000; testInProgress = true; pos = order.length - 1;
  summarize();
  for(let i = 0; i < 300 && !document.querySelector('.rs-rewards.rs-done'); i++){ const sp = document.querySelector('.rs-spot.is-up'); if(sp) sp.click(); await wait(100); }
  const x = document.querySelector('#stage .rs-xp'); if(!x) return null;
  const tot = x.querySelector('.rs-xptotal'), lvl = x.querySelector('.results-level');
  const between = []; for(let e = tot && tot.nextElementSibling; e && e !== lvl; e = e.nextElementSibling) if(e.getClientRects().length && e.textContent.trim()) between.push(e.textContent.trim());
  const vals = [...x.querySelectorAll('.rs-xpline:not(.rs-xpkick) .rs-xpline-val')].map(e => +e.textContent.replace(/[^0-9]/g, ''));
  return { between, total: +((x.querySelector('.rs-xptotal-num') || {}).textContent || '').replace(/[^0-9]/g, ''), vals, xpTotal: lastRunResult && lastRunResult.xpTotal };
}"""


def sec_sum(br):
    print("\n1. nothing under the XP total")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        r = pg.evaluate(RUN3)
        check("%s: a run with answers and bonuses has nothing between the total and the level bar (%s)" % (label, r and r["between"]),
              bool(r) and not r["between"] and r["total"] == sum(r["vals"]) == r["xpTotal"] and len(r["vals"]) >= 3, r)
        ctx.close()


def sec_streak(br):
    # MOVED IN 327: "Answers in a row is terrible, it was better how it was
    # before." The sentence this section held is gone; build 324's line is
    # back ("10 ×2 · 25 in a row", tools/check-b327-b.py). Held here: no
    # "+N" jammed into it, and it still fits one line on a phone.
    print("\n2. the answer streak line (327: build 324's form, see check-b327-b)")
    ctx, pg = boot(br, 440, 956)
    cases = pg.evaluate("""() => { const sub = ok => (computeRunXp({good: ok.filter(Boolean).length, answered: ok.length, elapsedMs: ok.length * 20000, okList: ok, hundos: 0, wholeUnits: 1}).lines.find(l => l.key === 'streak') || {}).sub || null;
      const T = n => Array(n).fill(true), F = [false];
      return { one: sub(T(12)), two: sub(T(12).concat(F, T(25))), three: sub(T(12).concat(F, T(11), F, T(10))), full: sub(T(100)) }; }""")
    bad = {k: v for k, v in cases.items() if not v or "+" in v or v.count("in a row") != 1}
    check("no line jams a '+N' into it, and each says 'in a row' once", not bad, cases)
    check("and it is build 324's line: the marks in order, a count only where one came more than once",
          cases["one"] == "10 in a row" and cases["two"] == "10 \u00d72 \u00b7 25 in a row"
          and cases["three"] == "10 \u00d73 in a row" and cases["full"] == "10 \u00b7 25 \u00b7 50 \u00b7 75 \u00b7 100 in a row", cases)
    # on the card: one line, under a 440px phone's width, never wrapped
    r = pg.evaluate(RUN3.replace("bad = k === 25", "bad = k === 25 || k === 37"))
    sub = pg.evaluate("""() => { const l = [...document.querySelectorAll('#stage .rs-xp .rs-xpline')].find(e => /in a row/i.test(e.textContent));
      const s = l && l.querySelector('.rs-xpline-sub'); if(!s) return null; const rg = document.createRange(); rg.selectNodeContents(s);
      return { text: s.textContent, lines: new Set([...rg.getClientRects()].map(q => Math.round(q.top))).size }; }""")
    check("on the results card it is one line on a phone (%s)" % (sub and sub["text"]), bool(sub) and sub["lines"] == 1, sub)
    ctx.close()


STATS_SEED = """() => { const now = Date.now(), m = 60000;
  store.testHistory = [
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 100, elapsedMs: 300000, playedAt: now - 5 * m, mode: 'drill', n: 12, ok: 12, hundos: 1 },
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 92, elapsedMs: 300000, playedAt: now - 30 * m, mode: 'drill', n: 12, ok: 11 },
    { label: 'Victims of Crime', units: ['Victims of Crime'], pct: 80, elapsedMs: 300000, playedAt: now - 60 * m, mode: 'exam', n: 20, ok: 16 },
    { label: 'TCOLE Rules', units: ['TCOLE Rules'], pct: 64, elapsedMs: 300000, playedAt: now - 90 * m, mode: 'drill', n: 14, ok: 9, vr: true },
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 100, elapsedMs: 200000, playedAt: now - 120 * m, mode: 'exam', n: 12, ok: 12, hundos: 1 }];
  saveStore(); }"""
ROWS = r"""(sel) => [...document.querySelectorAll(sel)].map(r => { const ring = r.querySelector('.thx-ring-arc'), chip = r.querySelector('.thx-chip');
  return { tone: getComputedStyle(r).getPropertyValue('--tone').trim(), ring: ring ? getComputedStyle(ring).stroke : null,
    chip: chip ? getComputedStyle(chip).getPropertyValue('--mode-c').trim() : null, mode: chip ? chip.textContent : null,
    pct: (r.querySelector('.thx-ring-num') || {}).textContent, text: r.textContent, hundo: !!r.querySelector('.thx-hundo'),
    border: getComputedStyle(r).borderTopColor }; })"""


def hexrgb(h):
    h = h.strip().lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] if len(h) == 6 else None


def same_col(a, b):
    pa = parse_col(a) if a and not a.startswith("#") else (hexrgb(a) + [1] if a else None)
    pb = parse_col(b) if b and not b.startswith("#") else (hexrgb(b) + [1] if b else None)
    return bool(pa and pb) and all(abs(x - y) < 2 for x, y in zip(pa[:3], pb[:3]))


def sec_stats(br):
    print("\n3. Stats: a Hundo is a Hundo, a test is its mode's colour")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate(STATS_SEED)
        pg.evaluate("() => showProfile('stats')")
        pg.wait_for_timeout(900)
        stats_text = pg.evaluate("() => { const t = document.querySelector('.profile-stats-tab') || document.querySelector('#stage'); return t.innerText; }")
        rows = pg.evaluate(ROWS, ".profile-stats-tab .thx-row")
        pg.evaluate("() => showTestReviewList()")
        pg.wait_for_timeout(500)
        hist_text = pg.evaluate("() => document.querySelector('#stage').innerText")
        hrows = pg.evaluate(ROWS, "#stage .thx-row")
        pg.evaluate("() => { const r = document.querySelector('#stage .thx-row'); r && r.click(); }")
        pg.wait_for_timeout(500)
        det = pg.evaluate("""() => { const p = document.querySelector('#stage .screen-testdetail'); if(!p) return null;
          const ring = p.querySelector('.thx-ring-arc'), chip = p.querySelector('.thx-chip');
          return { text: p.innerText, verdict: (p.querySelector('.thx-verdict') || {}).textContent, tone: getComputedStyle(p).getPropertyValue('--tone').trim(),
            ring: ring && getComputedStyle(ring).stroke, chip: chip && getComputedStyle(chip).getPropertyValue('--mode-c').trim(),
            bars: [...p.querySelectorAll('.thx-unit-bar > span')].map(e => getComputedStyle(e).backgroundColor) }; }""")
        perfect = [t for t in (stats_text, hist_text, det and det["text"]) if t and re.search(r"\bperfect\b", t, re.I)]
        check("%s: 'perfect' appears nowhere on Stats, Test history or a test's page" % label, not perfect,
              [re.findall(r".{0,30}\bperfect\b.{0,20}", t, re.I) for t in perfect])
        hun = [r for r in rows + hrows if r["pct"] == "100%"]
        check("%s: a test that earned a hundo says Hundo on its row, and its own page says Hundo" % label,
              hun and all(r["hundo"] and "Hundo" in r["text"] for r in hun) and det and det["verdict"] and "Hundo" in det["verdict"],
              [(r["pct"], r["hundo"]) for r in hun] + [det and det["verdict"]])
        # MOVED IN 327 (b327e): "Recent test, why are the percentage rings
        # color matched to the mode? It should be color matched to hundo
        # (gold) or pass green or fail red. And then the mode would have that
        # thing as its own color." 326's rule (ring, wash and chip all the
        # mode's colour) is the decision that changed; what holds now is ONE
        # colour code per piece: the ring and its wash are the RESULT
        # (testResultTone), the chip alone is the mode. check-b327-e B holds
        # the colours themselves.
        allrows = rows + hrows
        res = lambda p: "#FFD36A" if p == "100%" else "#5FD99A" if int(p.rstrip("%")) >= 70 else "#FF7A7A"
        one = [r for r in allrows if not (same_col(r["ring"], res(r["pct"])) and same_col(r["tone"], res(r["pct"])))]
        check("%s: every row's ring and wash are its RESULT's colour (%d rows)" % (label, len(allrows)), len(allrows) >= 7 and not one,
              [(r["mode"], r["pct"], r["ring"], r["tone"], r["chip"]) for r in one])
        drills = [r for r in allrows if r["mode"] == "Drill"]
        check("%s: tests of one mode keep one chip colour, whatever their score (Drill at %s)" % (label, sorted(set(r["pct"] for r in drills))),
              len(set(r["pct"] for r in drills)) >= 2 and len(set(r["chip"] for r in drills)) == 1 and len(set(r["border"] for r in allrows)) == 1,
              [(r["pct"], r["chip"], r["border"]) for r in drills])
        check("%s: a test's own page: its ring and tone are its result's colour, its chip its mode's" % label,
              bool(det) and same_col(det["ring"], det["tone"]) and not same_col(det["ring"], det["chip"]), det)
        ctx.close()


PAUSE = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  theme.autoAdvance = false;
  cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.source = 'all'; cfg.size = 0; cfg.versions = {};
  beginRun(poolNow(), null, null);
  for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(100);
  document.querySelectorAll('.unlock-overlay,.hu-overlay').forEach(n => n.remove());
  pauseRun(); await wait(700);
  const s = document.getElementById('pause-save'), q = document.getElementById('pause-quit'), r = document.getElementById('resumebtn');
  if(!s) return null;
  const cs = getComputedStyle(s), R = e => e.getBoundingClientRect();
  return { bg: cs.backgroundColor, img: cs.backgroundImage, color: cs.color, bf: cs.backdropFilter || cs.webkitBackdropFilter || 'none', op: +cs.opacity,
           qbg: getComputedStyle(q).backgroundColor, h: R(s).height, hq: R(q).height, w: R(s).width, wr: R(r).width,
           outer: cs.boxShadow.split(/,(?![^(]*\\))/).filter(x => !/inset/.test(x)).length }; }"""


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    return .2126 * ch(c[0]) + .7152 * ch(c[1]) + .0722 * ch(c[2])


def sec_save(br):
    print("\n4. Save and exit: solid, readable, its own colour, the size of its neighbours")
    for label, w, h in (PHONE, TABLET):
        for accent in ("ink", "titan", "adept"):
            ctx, pg = boot(br, w, h)
            pg.evaluate("(a) => { theme.accent = a; try{ applyTheme(); }catch(e){} }", accent)
            r = pg.evaluate(PAUSE)
            if not r:
                check("%s (%s): the pause sheet has Save and exit" % (label, accent), False, r)
                ctx.close(); continue
            bg, fg, qbg = parse_col(r["bg"]), parse_col(r["color"]), parse_col(r["qbg"])
            con = (max(lum(bg), lum(fg)) + .05) / (min(lum(bg), lum(fg)) + .05) if bg and fg else 0
            check("%s (%s): opaque (%s), no backdrop blur, not Quit's colour, words at %.1f:1, %.0fpx tall, as wide as Resume, with a lift" % (label, accent, r["bg"], con, r["h"]),
                  bg and bg[3] == 1 and r["op"] == 1 and r["bf"] == "none" and qbg and any(abs(a - b) > 20 for a, b in zip(bg[:3], qbg[:3]))
                  and con >= 4.5 and r["h"] >= 44 and abs(r["h"] - r["hq"]) <= 1 and abs(r["w"] - r["wr"]) <= 1 and r["outer"] >= 2, r)
            ctx.close()


FXS = ("confetti", "fireworks", "underwater", "bubbles", "ufo")


def sec_dim_edges(br, do_dim=True, do_edges=True):
    if do_dim:
        print("\n5. one dim, the same for every effect")
    if do_edges:
        print("\n6. every card's edge is the XP card's, before, during and after every effect")
    shapes = {}
    for label, w, h in (PHONE, TABLET):
        for fx in FXS:
            ctx, pg = fx_session(br, w, h, fx)
            tail = pg.evaluate("() => (typeof HUNDO_FX_TAIL_AT === 'object' && HUNDO_FX_TAIL_AT['%s']) || 0" % fx) / 1000
            tot = pg.evaluate("() => (typeof HUNDO_FX_TOTAL === 'object' && HUNDO_FX_TOTAL['%s']) || 3000" % fx) / 1000
            times = [.02, .5, max(.55, tail - 1.45), max(.7, tail - .5), tail + .1, tot + .6]
            S = {}
            for t in times:
                fx_to(pg, t)
                S[t] = pg.evaluate(SAMPLE)
            tag = "%s, %s" % (label, fx)
            if do_dim:
                s0 = S[times[1]]
                d = s0["dims"]
                kinds = sorted(set(x["cls"] for x in d))
                one = len(d) == 1 and d[0]["cls"].split()[0] == "hfx-dim"
                kf = one and d[0]["kf"] and d[0]["kf"][0]
                shape = None
                if kf:
                    D = kf["d"]
                    shape = [(round(o * D), op if op is None else round(float(op), 3)) for o, op in kf["k"]]
                shapes[(label, fx)] = (shape, round(tail * 1000))
                gz = s0["gz"]
                over = gz not in (None, "auto") and d and d[0]["z"] not in ("auto",) and int(gz) > int(d[0]["z"])
                peak = [round(S[t]["dims"][0]["op"], 2) if S[t]["dims"] else 0 for t in times]
                check("%s: one dim, the shared one (%s), up at its peak through the effect and gone when the buttons rise (opacity %s), the box over it" % (tag, kinds, peak),
                      one and over and abs(peak[1] - .5) < .02 and abs(peak[2] - .5) < .02 and 0 < peak[3] < .45 and peak[4] < .02 and not S[times[5]]["dims"],
                      {"dims": [(x["cls"], x["op"], x["z"]) for x in d], "gz": gz, "peak": peak})
            if do_edges:
                xp = None
                bad = []
                for t in times:
                    for card in S[t]["cards"]:
                        e = edge_of(card)
                        if card["cls"] == "rs-xp":
                            xp = xp or e
                        # MOVED IN 327 (round 6): "I feel like the borders of the result
                        # screen boxes used to be better. Now that the edges are like a
                        # hard stop for the borders it's kinda bad." One SOFT recipe now:
                        # the rim at about a third, no full-strength 1px line, a glow in
                        # off the edge (and one outside it) - still on every card.
                        if not (.25 <= e[0] <= .5 and e[1] < .2 and e[2][0] >= 20 and e[2][1] >= .1):
                            bad.append((round(t, 2), card["cls"], e))
                grade = [edge_of(c) for t in times for c in S[t]["cards"] if c["cls"] == "rs-grade"]
                same = bool(xp) and grade and all(g[0] == xp[0] and g[1] == xp[1] and g[2] == xp[2] for g in grade)
                check("%s: every card has the edge (a soft rim, no hard 1px line, the glow) at every moment sampled, and the 100%%'s is the XP card's %s at its first frame and after" % (tag, xp),
                      not bad and same, {"bad": bad[:6], "grade": grade, "xp": xp})
            ctx.close()
    if do_dim:
        # the same shape for every effect: the same peak, the same time up, the
        # same time down, and the end at that effect's own button moment
        norm = {}
        for k, (shape, end) in shapes.items():
            if not shape:
                norm[k] = None; continue
            ups = [o for o, op in shape if op and op > .49]
            r10 = lambda v: int(round(v / 10.0)) * 10 if v is not None else None
            norm[k] = (r10(ups[0] if ups else None), r10(shape[-1][0] - (ups[-1] if ups else 0)), max(op or 0 for _, op in shape), abs(shape[-1][0] - end) <= 2)
        vals = set(v for v in norm.values())
        check("every effect's dim has the same peak, comes up over the same time and lifts over the same time, ending at its own buttons (%s)" % sorted(map(str, vals)),
              len(vals) == 1 and None not in vals and all(v and v[3] for v in vals), norm)


WATER = r"""(phase) => {
  const L = document.querySelector('.hfx-layer.hfx-underwater'); if(!L) return null;
  const vis = e => { let o = 1; for(let x = e; x && x !== document.body; x = x.parentElement){ const cs = getComputedStyle(x); if(cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; } return o; };
  const fish = [...L.querySelectorAll('.hfx-uw-f, .hfx-uw-sf, .hfx-uw-fish')].map(e => { const r = e.getBoundingClientRect();
    const urls = [e, ...e.children].map(x => getComputedStyle(x).backgroundImage).filter(u => u && u !== 'none');
    const key = urls.length ? (Object.keys(hfxSprites).find(k => urls.some(u => u === hfxSprites[k].svg || u === hfxSprites[k].png)) || '?') : '?';
    const mover = e.closest('.hfx-uw-school, .hfx-uw-fish3, .hfx-uw-school.is-big') || e;
    const rot = mover.getAnimations().map(a => a.effect.getKeyframes().map(f => parseFloat(f.rotate) || 0)).flat();
    const tail = [...e.querySelectorAll('.hfx-uw-ft')].some(t => t.getAnimations().some(a => a.playState === 'running' || a.playState === 'paused'));
    return { key, w: r.width, op: vis(e), in: r.right > 0 && r.left < innerWidth && r.bottom > 0 && r.top < innerHeight,
      turns: rot.length ? Math.max(...rot) - Math.min(...rot) : 0, tail, school: !!e.closest('.hfx-uw-school') && !e.closest('.hfx-uw-school.is-big') && e.classList.contains('hfx-uw-sf') }; });
  const bf = [...L.querySelectorAll('*')].filter(e => { const cs = getComputedStyle(e); return (cs.backdropFilter && cs.backdropFilter !== 'none') || (cs.webkitBackdropFilter && cs.webkitBackdropFilter !== 'none'); }).map(e => String(e.className));
  const cards = [...document.querySelectorAll('#stage .rs-screen > .rs-card')].map(c => getComputedStyle(c).translate);
  return { fish, bf, cards };
}"""
SPRITES = r"""() => Object.keys(hfxSprites).filter(k => /^fish/.test(k)).map(k => ({ k, t: hfxSprites[k].text }))"""


def dark_marks(svg):
    """outlines and dark fills in a fish's svg: strokes 1.5 units or wider
    in a colour under 25% luminance, and fills under 15% that are not an
    eye's (url(#ey)) - what read as 'random dark shapes'"""
    out = []
    for m in re.finditer(r"<(path|circle|ellipse|rect|g)\b([^>]*)>", svg):
        a = m.group(2)
        st = re.search(r'stroke="(#[0-9A-Fa-f]{6})"', a)
        sw = re.search(r'stroke-width="([\d.]+)"', a)
        so = re.search(r'stroke-opacity="([\d.]+)"', a)
        if st and sw and float(sw.group(1)) >= 1.5 and lum(hexrgb(st.group(1))) < .25 and (not so or float(so.group(1)) > .3):
            out.append(("outline", st.group(1), sw.group(1)))
        fl = re.search(r'fill="(#[0-9A-Fa-f]{6})"', a)
        fo = re.search(r'fill-opacity="([\d.]+)"', a)
        if fl and lum(hexrgb(fl.group(1))) < .03 and (not fo or float(fo.group(1)) > .3):
            r = re.search(r'\br="([\d.]+)"', a)
            if not (m.group(1) == "circle" and r and float(r.group(1)) <= 5):
                out.append(("dark fill", fl.group(1)))
    return out


def sec_water(br):
    print("\n7. underwater: drawn fish that swim, and a drain that does not stutter")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = fx_session(br, w, h, "underwater")
        U = pg.evaluate("() => ({ rise: HFX_UW.rise + HFX_UW.riseD, drain: HFX_UW.drain, gone: HFX_UW.drain + HFX_UW.drainD })")
        # what forces the page's style and layout up to date, counted while
        # the water is up and draining (the drain's hitch, profiled, was
        # three of these every 150ms and a getComputedStyle as each card
        # left the water)
        pg.evaluate("""() => { const n = window.__flush = { gbcr: 0, gcs: 0, ga: 0, on: false };
          n.who = {}; const wrap = (o, k, key) => { const f = o[k]; o[k] = function(){ if(n.on){ n[key]++; const st = (new Error().stack || '').split('\\n')[2] || ''; const w = (st.match(/at ([\\w.$]+)/) || [])[1] || '?'; n.who[w] = (n.who[w] || 0) + 1; } return f.apply(this, arguments); }; };
          wrap(Element.prototype, 'getBoundingClientRect', 'gbcr'); wrap(window, 'getComputedStyle', 'gcs'); wrap(Element.prototype, 'getAnimations', 'ga'); }""")
        fx_to(pg, U["rise"])
        pg.evaluate("() => { window.__flush.on = true; }")
        seen, during = [], []
        t = U["rise"] + .2
        while t < U["drain"] - .1:
            fx_to(pg, t)
            pg.evaluate("() => { window.__flush.on = false; }")
            r = pg.evaluate(WATER, "in")
            pg.evaluate("() => { window.__flush.on = true; }")
            during.append(r)
            seen += [f for f in r["fish"] if f["in"] and f["op"] > .05]
            t += .35
        sprites = pg.evaluate(SPRITES)
        fx_to(pg, U["drain"] + .02)
        pg.evaluate("() => { window.__flush.on = false; }")
        after = pg.evaluate(WATER, "drain")
        pg.evaluate("() => { window.__flush.on = true; }")
        species = sorted(set(re.sub(r"-(all|body|tail|null|undefined)?(-far)?$", "", f["key"]) for f in seen))
        sizes = sorted(set(round(f["w"] / 8) * 8 for f in seen))
        marks = {s["k"]: dark_marks(s["t"]) for s in sprites}
        marks = {k: v for k, v in marks.items() if v}
        check("%s: the fish are drawn without outlines and with nothing dark but an eye (%d fish pictures)" % (label, len(sprites)),
              sprites and not marks, marks)
        check("%s: four or more species in the water (%s), at three depths or more (widths %s)" % (label, species, sizes),
              len(species) >= 4 and len(sizes) >= 3 and max(sizes) >= 2.5 * max(8, min(sizes)), {"species": species, "sizes": sizes})
        movers = [f for f in seen if not f["school"]]
        check("%s: every fish that is not in the school turns with its path and beats its tail (%d seen)" % (label, len(movers)),
              movers and all(f["turns"] >= 2 and f["tail"] for f in movers), [(f["key"], round(f["turns"], 1), f["tail"]) for f in movers if not (f["turns"] >= 2 and f["tail"])][:6])
        left = [f["key"] for f in after["fish"] if f["in"] and f["op"] > .05]
        check("%s: no fish left in sight once the water starts to drain (%s)" % (label, left), not left, left)
        bfs = set(x for r in during + [after] for x in r["bf"])
        check("%s: no backdrop-filter anywhere in the water (%s)" % (label, sorted(bfs)), not bfs, sorted(bfs))
        fx_to(pg, U["gone"])
        fl = pg.evaluate("() => { window.__flush.on = false; return window.__flush; }")
        per = (fl["gbcr"] + fl["gcs"] + fl["ga"]) / (U["gone"] - U["rise"])
        check("%s: while the water is up and draining, the page is made to work out its style and layout no more than 12 times a second (%.1f: %s)" % (label, per, fl),
              per <= 12, fl)
        fx_to(pg, U["gone"] + .9, 30)
        rise = pg.evaluate("() => window.__riseAt")
        check("%s: the buttons rise only once the water has gone (%.2fs; drained by %.2fs)" % (label, (rise or 0) / 1000, U["gone"]),
              rise is not None and rise / 1000 >= U["gone"] - .001, rise)
        # every card at rest when the buttons come up: read at that moment
        ctx.close()
        ctx, pg = fx_session(br, w, h, "underwater")
        tail = pg.evaluate("() => HUNDO_FX_TAIL_AT.underwater") / 1000
        fx_to(pg, tail, 20)
        cards = pg.evaluate(WATER, "rest")["cards"]
        moved = [c for c in cards if c not in ("none", "0px", "0px 0px") and any(abs(float(v)) > .5 for v in re.findall(r"-?[\d.]+", c))]
        check("%s: every card is back at rest by the time the buttons rise (%s)" % (label, cards), not moved, cards)
        ctx.close()


SECTIONS = ["sum", "streak", "stats", "save", "dim", "edges", "water"]
FNS = {"sum": sec_sum, "streak": sec_streak, "stats": sec_stats, "save": sec_save, "water": sec_water}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME, args=["--no-sandbox"])
    want = [n for n in SECTIONS if ONLY is None or n in ONLY]
    for name in want:
        if name in FNS:
            FNS[name](br)
        elif name == "dim":
            sec_dim_edges(br, True, "edges" in want)
        elif name == "edges" and "dim" not in want:
            sec_dim_edges(br, False, True)
    br.close()
cb.SERVER.shutdown()
print("\n%d failure(s)" % len(cb.FAILURES))
for f in cb.FAILURES:
    print("  -", f)
sys.exit(1 if cb.FAILURES else 0)
