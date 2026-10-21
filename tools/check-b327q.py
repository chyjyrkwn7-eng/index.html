#!/usr/bin/env python3
"""Build 327, round 6, package Q - the results screen's grade box, its soft
edges, the rank-up XP climb on Profile, the UFO's beam.

  python3 tools/check-b327q.py [--against OLD/index.html] [--only A,B,C,D]

Madison's words (Oct 21):
  A. "Why does the grade box on the result screen show how many you got
     right twice? It says 12/12 above the bar and at the top. Redundant."
     A one-unit run: the unit's row is its name and its bar, no count. A
     three-unit run: each row keeps its own count.
  B. "I feel like the borders of the result screen boxes used to be better.
     Now that the edges are like a hard stop for the borders it's kinda
     bad." Every card (and the 100% box in its effect's colours) has a soft
     rim - about a third of its colour - no full-strength 1px line inside
     it, a soft glow outside it and in off it.
  C. "The entire road map cutscene at the end when you get extra xp ... it
     should show the next level like normal and so on but as the next
     levels bar goes up the extra xp would go down to match it."
     The climb shows the ordinary "x / y XP" counting UP with the bar, and
     "N extra XP" beside it counting DOWN; in every frame their sum is the
     XP into the level shown.
  D. "when the ufos beam comes out it does it fast and not like legit."
     The hull charges before it fires, the beam leaves it slowly (eased),
     a bright head rides its tip and never lights the box ahead of it, and
     it still reaches the box's floor at its old moment.

Every section fails on e83f307."""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ONLY = None
if "--only" in sys.argv:
    ONLY = sys.argv[sys.argv.index("--only") + 1].split(",")

_src = open(os.path.join(HERE, "check-b326-a.py")).read()
_src = _src[:_src.index("SECTIONS = [")].replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = %r' % HERE)
A_ = {"__name__": "b326a_harness"}
exec(compile(_src, "check-b326-a.py", "exec"), A_)
cb, check, boot, fx_session, fx_to = A_["cb"], A_["check"], A_["boot"], A_["fx_session"], A_["fx_to"]
PHONE, TABLET, RUN3, shadows, parse_col = A_["PHONE"], A_["TABLET"], A_["RUN3"], A_["shadows"], A_["parse_col"]
from playwright.sync_api import sync_playwright

_c = open(os.path.join(HERE, "check-b326-c.py")).read()
_i = _c.index('CLIMB = """') + len('CLIMB = """')
CLIMB = _c[_i:_c.index('"""', _i)]
# the extra beside the ordinary numbers (read here whatever the build calls it)
CLIMB = CLIMB.replace("ex: num((s.querySelector('.pf-xp-extra-n') || {}).textContent) });",
                      "ex: num((s.querySelector('.pf-xp-extra-n') || {}).textContent), line: ((s.querySelector('.pf-xpnums .xpnums') || {}).textContent || '').trim() });")
if "line:" not in CLIMB:
    CLIMB = CLIMB.replace("extra: !!s.querySelector('.xpnums.is-extra') });",
                          "extra: !!s.querySelector('.pf-xp-extra'), ex: 0, line: ((s.querySelector('.pf-xpnums .xpnums') || {}).textContent || '').trim() });")
assert "line:" in CLIMB

WAITDONE = "async () => { for(let i = 0; i < 400 && !document.querySelector('.rs-rewards.rs-done'); i++) await new Promise(r => setTimeout(r, 100)); return !!document.querySelector('.rs-rewards.rs-done'); }"
ROWS = """() => [...document.querySelectorAll('#stage .rs-grade .rs-byunit .unit-breakdown-row')].map(r => ({
  name: (r.querySelector('.unit-breakdown-name') || {}).textContent || '', score: r.querySelector('.unit-breakdown-score') ? r.querySelector('.unit-breakdown-score').textContent : null,
  bar: !!r.querySelector('.unit-breakdown-fill') }))"""


def sec_dup(br):
    print("\nA. one unit: no second count on its row; several units keep theirs")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        pg.evaluate("() => { theme.reduceMotion = true; try{ applyTheme(); }catch(e){} __run('Identity Crimes', 2, 'drill'); }")
        pg.evaluate(WAITDONE)
        rows = pg.evaluate(ROWS)
        frac = pg.evaluate("() => (document.querySelector('#stage .rs-grade .rs-grade-frac') || {}).textContent || ''")
        check("%s: a one-unit run's unit row is its name and its bar, with no count beside it (the card says %s once)" % (label, frac),
              len(rows) == 1 and rows[0]["score"] is None and rows[0]["name"] and rows[0]["bar"] and re.search(r"\d", frac or ""), rows)
        lay = pg.evaluate("""() => { const t = document.querySelector('#stage .rs-byunit .unit-breakdown-top'), n = t && t.querySelector('.unit-breakdown-name');
          if(!t || !n) return null; const a = t.getBoundingClientRect(), b = n.getBoundingClientRect(); return { dl: Math.round(b.left - a.left), w: Math.round(b.width), tw: Math.round(a.width) }; }""")
        check("%s: and the name sits on the row's left edge, over its bar" % label, bool(lay) and lay["dl"] <= 1, lay)
        ctx.close()
        ctx, pg = boot(br, w, h)
        pg.evaluate(RUN3)
        rows = pg.evaluate(ROWS)
        check("%s: a three-unit run keeps each unit's own count (%s)" % (label, [r["score"] for r in rows]),
              len(rows) == 3 and all(r["score"] and re.match(r"^\d+\s*/\s*\d+$", r["score"].strip()) for r in rows), rows)
        ctx.close()


CARDS = """() => [...document.querySelectorAll('#stage .rs-screen > .rs-card')].filter(c => getComputedStyle(c).opacity > .5).map(c => {
  const cs = getComputedStyle(c), t = c.querySelector(':scope > .hfx-tint');
  return { cls: String(c.className).split(' ').filter(x => /^rs-(grade|xp|unlocked|badges)$/.test(x)).join('.'), border: cs.borderTopColor, bs: cs.boxShadow,
    tint: t && +getComputedStyle(t).opacity > .99 ? getComputedStyle(t).boxShadow : null }; })"""


def soft(card):
    rim = parse_col(card["border"]) or [0, 0, 0, 0]
    sh = shadows(card["bs"]) + (shadows(card["tint"]) if card.get("tint") else [])
    hard = [s for s in sh if s[2] and s[0] and len(s[1]) >= 4 and s[1][2] == 0 and s[1][3] >= 1 and s[0][3] >= .3 and s[0][:3] != [255.0, 255.0, 255.0]]
    outer = [s for s in sh if not s[2] and s[0] and len(s[1]) >= 3 and s[1][2] >= 14 and abs(s[1][1]) < 4 and s[0][3] >= .2]
    inner = [s for s in sh if s[2] and s[0] and len(s[1]) >= 3 and s[1][2] >= 18 and s[0][3] >= .08]
    return {"rim": round(rim[3], 2), "hard": len(hard), "outer": len(outer), "inner": len(inner)}


def sec_edges(br):
    print("\nB. soft edges: a third-strength rim, no hard line inside it, a glow out and in")
    for label, w, h in (PHONE, TABLET):
        for kind in ("pass", "fail", "hundo"):
            ctx, pg = (fx_session(br, w, h, "fireworks") if kind == "hundo" else boot(br, w, h))
            if kind == "hundo":
                fx_to(pg, 9)
            else:
                pg.evaluate("(n) => { theme.reduceMotion = true; try{ applyTheme(); }catch(e){} __run('Identity Crimes', n, 'drill'); }", 1 if kind == "pass" else 7)
                pg.evaluate(WAITDONE)
            cards = pg.evaluate(CARDS)
            res = [(c["cls"], soft(c)) for c in cards if c["cls"] in ("rs-grade", "rs-xp")]
            ok = len(res) == 2 and all(.25 <= s["rim"] <= .7 and s["hard"] == 0 and s["outer"] >= 1 and s["inner"] >= 1 for _, s in res)
            check("%s, %s: the grade box and the XP box both have the soft edge (%s)" % (label, kind, res), ok, cards[:2])
            ctx.close()


def sec_climb(br):
    print("\nC. the climb: the next level like normal, the extra going down beside it")
    for (label, w, h), lv, plus in ((PHONE, 53, 700), (TABLET, 47, 300)):
        ctx, pg = boot(br, w, h)
        pts = pg.evaluate("(a) => xpForLevel(a[0]) + a[1]", [lv, plus])
        r = pg.evaluate(CLIMB, {"badges": 5, "points": pts})
        if r.get("errs"):
            check("%s: the climb ran" % label, False, r["errs"]); ctx.close(); continue
        s, tot = r["samples"], r["to"]["total"]
        ex = [x for x in s if x.get("extra")]
        ordinary = [x for x in ex if re.fullmatch(r"[\d,]+ / [\d,]+ XP", x.get("line") or "")]
        check("%s: while it climbs the line is the ordinary 'x / y XP' AND its own 'N extra XP' (%d of %d frames)" % (label, len(ordinary), len(s)),
              len(ex) >= 20 and len(ordinary) == len(ex), [(x["line"], x["ex"]) for x in s[:3]])
        bad = [(x["lv"], x["have"], x["ex"]) for x in ordinary if x["have"] + x["ex"] != tot - int(r["xpFor"][str(x["lv"])])]
        check("%s: in every frame shown into the level + the extra = the XP into that level (nothing made up or lost)" % label,
              len(ordinary) >= 20 and not bad, bad[:5])
        ups, downs = [], []
        for a, b in zip(ordinary, ordinary[1:]):
            if a["lv"] == b["lv"]:
                if b["have"] < a["have"]: ups.append((a["lv"], a["have"], b["have"]))
            if b["ex"] > a["ex"]: downs.append((a["ex"], b["ex"]))
        check("%s: within each level the number counts UP with the bar, and the extra only ever counts DOWN" % label,
              len(ordinary) >= 20 and not ups and not downs and ordinary[-1]["ex"] < ordinary[0]["ex"], [ups[:3], downs[:3]])
        check("%s: it lands on Level %s with the ordinary numbers and no extra left on the line" % (label, r["to"]["level"]),
              r["after"]["level"] == "Level %d" % r["to"]["level"] and r["after"]["have"] == r["to"]["into"]
              and not pg.evaluate("() => !!document.querySelector('.pf-standing .pf-xp-extra, .pf-standing .xpnums.is-extra')"), r["after"])
        ctx.close()


BEAM = r"""() => {
  const beam = document.querySelector('.hfx-saucer:not(.is-mini) > .hfx-ufo-beam'); if(!beam) return null;
  const op = el => { let o = 1; for(let e = el; e && e !== document.body; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
  const m = getComputedStyle(beam).transform.match(/matrix\(([^)]+)\)/); const v = m ? m[1].split(',').map(Number) : [1, 0, 0, 0];
  const tip = document.querySelector('.hfx-ufo-beamtip'), prime = document.querySelector('.hfx-ufo-prime');
  const bb = beam.getBoundingClientRect(), tb = tip && tip.getBoundingClientRect();
  return { sy: Math.hypot(v[2], v[3]), op: op(beam), head: bb.bottom, tipOp: tip ? op(tip) : 0, tipBot: tb ? tb.bottom : null, primeOp: prime ? op(prime) : 0 };
}"""


def sec_ufo(br):
    print("\nD. the UFO's beam emerges: a charge, a slow start, a bright head, the floor at its old moment")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = fx_session(br, w, h, "ufo")
        S = {}
        ts = [3.2, 3.4, 3.55] + [round(3.6 + k * .02, 2) for k in range(32)] + [4.25, 4.5, 5.2]
        for t in ts:
            fx_to(pg, t, 20)
            S[t] = pg.evaluate(BEAM)
        ctx.close()
        if not S[3.2]:
            check("%s: a real 100%% played the UFO" % label, False, S); continue
        check("%s: the hull charges before it fires - a glow under it from 3.4s, before any beam (%s)" % (label, [round(S[t]["primeOp"], 2) for t in (3.2, 3.4, 3.55)]),
              S[3.4]["primeOp"] > .2 and S[3.55]["primeOp"] > .3 and all(S[t]["op"] < .02 for t in (3.2, 3.4, 3.55)), [S[t] for t in (3.4, 3.55)])
        fire = next((t for t in ts if t >= 3.6 and S[t]["op"] > .05), None)
        reach = next((t for t in ts if t >= 3.6 and S[t]["sy"] >= .3), None)
        floor = next((t for t in ts if t >= 3.6 and S[t]["sy"] >= .995), None)
        check("%s: the beam leaves the hull slowly - 0.15s+ from firing (%s) to a third of its length (%s)" % (label, fire, reach),
              fire is not None and reach is not None and reach - fire >= .15, [(t, round(S[t]["sy"], 3), round(S[t]["op"], 2)) for t in ts if 3.6 <= t <= 4.0])
        check("%s: and still reaches the box's floor at its old moment (4.1-4.22s, here %s)" % (label, floor),
              floor is not None and 4.1 <= floor <= 4.22, floor)
        lit = [t for t in ts if 3.6 <= t <= 4.15 and S[t]["op"] > .05 and S[t]["sy"] > .05]
        tips = [(t, round(S[t]["tipBot"] - S[t]["head"], 1)) for t in lit if S[t]["tipOp"] > .3 and S[t]["tipBot"] is not None]
        check("%s: a bright head rides the beam's tip as it comes out (%d frames), never past it" % (label, len(tips)),
              len(tips) >= max(6, len(lit) // 2) and all(-6 <= d <= 1 for _, d in tips), tips[:8])
        check("%s: and it is gone once the beam is down (4.5s)" % label, S[4.5]["tipOp"] < .02 and S[4.5]["op"] > .5, S[4.5])


SECTIONS = {"A": sec_dup, "B": sec_edges, "C": sec_climb, "D": sec_ufo}
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=cb.CHROME, args=["--no-sandbox"])
    for k, fn in SECTIONS.items():
        if ONLY and k not in ONLY:
            continue
        try:
            fn(br)
        except Exception as e:
            check("section %s ran" % k, False, repr(e)[:400])
    br.close()
print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
sys.exit(1 if cb.FAILURES else 0)
