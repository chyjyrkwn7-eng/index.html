#!/usr/bin/env python3
"""Build 327, package B - the XP box simplified, the extra that goes down,
the fish in the water.

  python3 tools/check-b327-b.py [--against OLD/index.html] [--only A,B,C]

Madison's words (Oct 20):
  A. "the xp box ... the descriptions under some of the stuff is bad, it
     looks cluttered. The hundo one has an unnecessary description. That
     would probably only need to be there or there's multiple units you got
     a hundo on? Answers in a row is terrible, it was better how it was
     before. The title 'answers in a row' could be answer streak or
     something. The whole xp box needs to be simplified."
     computeRunXp: the streak line is "Answer streak" over build 324's line
     ("10 ×2 · 25 in a row"); one hundo has no sub-line, two or more name
     their units; no sub-line restates a sum or says "on average" or
     "every answer right"; every value is what the same run paid on 326 and
     the total is the lines' sum. On a real three-unit results card: the
     same, as drawn.
  B. "The xp bar with the extra, not sure what's up with the -xp stuff in
     the bar.. it could literally just be the xp that's the extra it goes
     down as you level up.. fix that."
     The rank-up climb on Profile across several levels (both reference
     devices): no "-N XP" anywhere at any frame; the line under the bar
     reads "N extra XP" while it climbs and N only ever goes down, from the
     XP past the wall level to what is left; it ends on the ordinary
     numbers.
  C. "The underwater fish are still bad, why are they clearly visible? They
     don't look like they are in the water."
     Every fish swims in a layer at the BACK of the water (.hfx-uw-life),
     the water's light, rays and a dapple laid over it; the middle and near
     fish carry the water's haze in their pictures; none is shown at more
     than .85 strength, the school at no more than .45.

Every section fails on build 326 (--against /tmp/claude-0/b327/index-326.html)."""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ONLY = None
if "--only" in sys.argv:
    ONLY = sys.argv[sys.argv.index("--only") + 1].split(",")

# the shared harness of check-b326-a (boot, the effect's own clock, the
# water sampler), without running its sections
_src = open(os.path.join(HERE, "check-b326-a.py")).read()
_src = _src[:_src.index("SECTIONS = [")].replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = %r' % HERE)
A = {"__name__": "b326a_harness"}
exec(compile(_src, "check-b326-a.py", "exec"), A)
cb, check, boot, fx_session, fx_to = A["cb"], A["check"], A["boot"], A["fx_session"], A["fx_to"]
PHONE, TABLET, RUN3 = A["PHONE"], A["TABLET"], A["RUN3"]
from playwright.sync_api import sync_playwright

_c = open(os.path.join(HERE, "check-b326-c.py")).read()
_i = _c.index('CLIMB = """') + len('CLIMB = """')
CLIMB = _c[_i:_c.index('"""', _i)]
# every frame: is any "-N XP" on the standing card, and is the line the extra
CLIMB = CLIMB.replace("if(/saved/i.test(s.textContent)) out.saved = true;",
                      "if(/saved/i.test(s.textContent)) out.saved = true; if(/[\\u2212-]\\s?[\\d,]+\\s?XP/.test(s.textContent)) out.minus = (out.minus || 0) + 1;"
                      " (out.lines = out.lines || []).push(((s.querySelector('.pf-xpnums .pf-xp-extra') || {}).textContent || '').trim());")
assert "out.minus" in CLIMB


def sec_lines(br):
    print("\nA. the XP box: one line a kind, a sub-line only where it says something")
    ctx, pg = boot(br, *PHONE[1:])
    r = pg.evaluate("""() => { const T = n => Array(n).fill(true), F = [false];
      const run = o => computeRunXp(Object.assign({ elapsedMs: (o.answered || 12) * 9000, wholeUnits: 1, hundos: 0 }, o));
      const two = run({ good: 37, answered: 38, okList: T(12).concat(F, T(25)) });
      const one = run({ good: 12, answered: 12, okList: T(12), hundos: 1, hundoUnits: [] });
      const many = run({ good: 46, answered: 46, okList: T(46), hundos: 3, wholeUnits: 3, hundoUnits: ['Identity Crimes', 'Victims of Crime', 'TCOLE Rules'] });
      const long = run({ good: 140, answered: 150, okList: T(60).concat(F, T(89)), wholeUnits: 2,
        timePRs: [{ unit: 'A', text: 'A 1:00 (was 1:20)' }], scorePRs: [{ unit: 'B', text: 'B 100% (was 90%)' }] });
      const pay = { correct: POINTS_PER_QUESTION, hundo: PERFECT_BONUS, tier: [10, 25, 50, 75, 100].map(runStreakTierXp) };
      return { two, one, many, long, pay }; }""")
    st = [l for l in r["two"]["lines"] if l["key"] == "streak"]
    check("the streak line is called 'Answer streak' (%s)" % [l["label"] for l in st], len(st) == 1 and st[0]["label"] == "Answer streak", st)
    check("its line is build 324's: '10 ×2 · 25 in a row' (%s)" % (st and st[0].get("sub")),
          bool(st) and st[0].get("sub") == "10 ×2 · 25 in a row", st)
    h1 = [l for l in r["one"]["lines"] if l["key"] == "hundo"]
    check("one hundo is one line with no sub-line (%s)" % h1, len(h1) == 1 and not h1[0].get("sub"), h1)
    hm = [l for l in r["many"]["lines"] if l["key"] == "hundo"]
    check("three hundos name their three units, and nothing else (%s)" % (hm and hm[0].get("sub")),
          len(hm) == 1 and hm[0].get("sub") and all(u in hm[0]["sub"] for u in ("Identity Crimes", "Victims of Crime", "TCOLE Rules"))
          and not re.search(r"\d|XP|right", hm[0]["sub"]), hm)
    lines = [l for k in ("two", "one", "many", "long") for l in r[k]["lines"]]
    clutter = [(l["key"], l.get("sub")) for l in lines if re.search(r"above|% of|on average|every answer right|in all\)|for every", l.get("sub") or "")]
    check("no sub-line restates a sum or explains the arithmetic (%d lines)" % len(lines), not clutter, clutter)
    sums = [(k, r[k]["total"], sum(l["value"] for l in r[k]["lines"])) for k in ("two", "one", "many", "long")]
    check("every total is its lines' sum", all(a == b for _, a, b in sums), sums)
    v = lambda k, key: sum(l["value"] for l in r[k]["lines"] if l["key"] == key)
    P = r["pay"]
    check("and pays what build 326 paid: right answers x10, a hundo each, the marks reached",
          v("two", "correct") == 37 * P["correct"] and v("two", "streak") == 2 * P["tier"][0] + P["tier"][1]
          and v("one", "hundo") == P["hundo"] and v("many", "hundo") == 3 * P["hundo"]
          and v("many", "streak") == sum(P["tier"][:2]), [v("two", "correct"), v("two", "streak"), v("one", "hundo"), v("many", "hundo"), v("many", "streak")])
    ctx.close()
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        res = pg.evaluate(RUN3)
        card = pg.evaluate("""() => [...document.querySelectorAll('#stage .rs-xp .rs-xpline:not(.rs-xpkick)')].map(e => ({
          name: (e.querySelector('.rs-xpline-name') || {}).textContent, sub: (e.querySelector('.rs-xpline-sub') || {}).textContent || null }))""")
        hu = [c for c in card if re.match(r"Hundo", c["name"] or "")]
        st = [c for c in card if c["name"] == "Answer streak"]
        check("%s: the card draws 'Answer streak' over its marks, and the hundos of a multi-unit run name their units (%s)" % (label, card),
              len(st) == 1 and (st[0]["sub"] or "").endswith(" in a row") and len(hu) == 1 and hu[0]["sub"]
              and len([u for u in ("Identity Crimes", "Victims of Crime", "TCOLE Rules") if u in hu[0]["sub"]]) >= 2, card)
        check("%s: and its total is still the lines' sum (%s)" % (label, res and res.get("total")),
              bool(res) and res["total"] == sum(res["vals"]) == res["xpTotal"], res)
        ctx.close()


def sec_extra(br):
    print("\nB. the extra goes down as the levels fill; no '-N XP'")
    for (label, w, h), lv, plus in ((PHONE, 53, 700), (TABLET, 47, 300)):
        ctx, pg = boot(br, w, h)
        pts = pg.evaluate("(a) => xpForLevel(a[0]) + a[1]", [lv, plus])
        r = pg.evaluate(CLIMB, {"badges": 5, "points": pts})
        if r.get("errs"):
            check("%s: the climb ran" % label, False, r["errs"])
            ctx.close()
            continue
        fr, to, s = r["from"], r["to"], r["samples"]
        check("%s: no '-N XP' on the card at any frame (%d frames, %s found)" % (label, r["n"], r.get("minus") or 0),
              r["n"] >= 30 and not r.get("minus") and not r["chips"], [r.get("minus"), r["chips"][:3]])
        # MOVED IN 327 (round 6): "it should show the next level like normal
        # and so on but as the next level's bar goes up the extra xp would go
        # down to match it". The extra is its own "N extra XP" beside the
        # ordinary numbers, not in place of them.
        ex = [x for x in s if x.get("extra")]
        texts = sorted(set(t for t in (r.get("lines") or []) if "extra" in t))
        check("%s: while it climbs the extra is its own 'N extra XP', starting on the XP past the wall (%s)" % (label, texts[:2]),
              len(ex) >= 20 and ex[0]["ex"] == fr["into"] - fr["span"] and texts and all(re.fullmatch(r"[\d,]+ extra XP", t) for t in texts),
              [ex[:1], fr, texts[:3]])
        haves = [x["ex"] for x in ex]
        check("%s: and it only ever goes down (%d -> %d over %d frames)" % (label, haves[0] if haves else -1, haves[-1] if haves else -1, len(haves)),
              len(haves) >= 20 and all(haves[i] <= haves[i - 1] for i in range(1, len(haves))) and haves[-1] < haves[0],
              [(i, haves[i - 1], haves[i]) for i in range(1, len(haves)) if haves[i] > haves[i - 1]][:4])
        check("%s: it lands on the ordinary numbers - Level %s, %s / %s XP" % (label, to["level"], to["into"], to["span"]),
              r["after"]["level"] == "Level %d" % to["level"] and r["after"]["have"] == to["into"]
              and not pg.evaluate("() => !!document.querySelector('.pf-standing .pf-xp-extra')"), r["after"])
        ctx.close()


FISH = r"""() => {
  const L = document.querySelector('.hfx-layer.hfx-underwater'); if(!L) return null;
  const body = L.querySelector('.hfx-uw-ocean:not(.is-box):not(.is-drops) .hfx-uw-body'); if(!body) return null;
  const kids = [...body.children];
  const at = sel => kids.findIndex(e => e.matches(sel));
  const vis = e => { let o = 1; for(let x = e; x && x !== document.body; x = x.parentElement){ const cs = getComputedStyle(x); if(cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; } return o; };
  const keyOf = e => { const u = getComputedStyle(e).backgroundImage; return Object.keys(hfxSprites).find(k => u === hfxSprites[k].svg || u === hfxSprites[k].png) || '?'; };
  const fish = [...body.querySelectorAll('.hfx-uw-f, .hfx-uw-sf')].map(e => { const r = e.getBoundingClientRect();
    return { school: e.classList.contains('hfx-uw-sf'), inLife: !!e.closest('.hfx-uw-life'), op: vis(e),
      keys: (e.classList.contains('hfx-uw-sf') ? [e] : [...e.children]).map(keyOf), in: r.right > 0 && r.left < innerWidth && r.bottom > 0 && r.top < innerHeight }; });
  return { life: at('.hfx-uw-life'), light: at('.hfx-uw-light'), ray: at('.hfx-uw-ray'), dapple: at('.hfx-uw-dapple'), sheen: at('.hfx-uw-sheen'), fish };
}"""


def sec_fish(br):
    print("\nC. the fish are in the water, not on it")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = fx_session(br, w, h, "underwater")
        U = pg.evaluate("() => ({ up: HFX_UW.rise + HFX_UW.riseD, drain: HFX_UW.drain })")
        seen, lay = [], None
        t = U["up"] + .3
        while t < U["drain"] - .1:
            fx_to(pg, t)
            r = pg.evaluate(FISH)
            if r:
                lay = lay or r
                seen += [f for f in r["fish"] if f["in"] and f["op"] > .02]
            t += .3
        ok_order = bool(lay) and lay["life"] >= 0 and all(lay[k] > lay["life"] for k in ("light", "ray", "sheen", "dapple"))
        check("%s: the fish swim at the back of the water - its sheen, light, rays and a dapple are laid over them (%s)" % (label, lay and {k: lay[k] for k in ('life', 'sheen', 'light', 'ray', 'dapple')}),
              ok_order, lay and {k: lay[k] for k in ('life', 'sheen', 'light', 'ray', 'dapple')})
        check("%s: every fish seen is in that layer (%d seen)" % (label, len(seen)), len(seen) >= 4 and all(f["inLife"] for f in seen),
              [f for f in seen if not f["inLife"]][:3])
        movers = [f for f in seen if not f["school"]]
        check("%s: the middle and near fish carry the water's haze in their pictures" % label,
              movers and all(all(re.search(r"-h\d+$", k) for k in f["keys"]) for f in movers), [f["keys"] for f in movers if not all(re.search(r"-h\d+$", k) for k in f["keys"])][:3])
        mo = max([f["op"] for f in movers] or [1]); so = max([f["op"] for f in seen if f["school"]] or [1])
        check("%s: none at full strength - the nearest at most .85 (%.2f), the school at most .45 (%.2f)" % (label, mo, so),
              mo <= .85 and so <= .45, [mo, so])
        ctx.close()


SECTIONS = {"A": sec_lines, "B": sec_extra, "C": sec_fish}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME, args=["--no-sandbox"])
    for k, fn in SECTIONS.items():
        if ONLY is None or k in ONLY:
            try:
                fn(br)
            except Exception as e:
                check("section %s ran" % k, False, repr(e)[:600])
    br.close()
cb.SERVER.shutdown()
print("\n%d failure(s)" % len(cb.FAILURES))
for f in cb.FAILURES:
    print("  -", f)
sys.exit(1 if cb.FAILURES else 0)
