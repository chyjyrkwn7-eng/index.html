"""Build 384: Fire Code's XP curve and its secret flares.
Madison: "the ifc version, the xp curve and xp amount needed to level up. Ensure this is made right. A person probably won't be
grinding these nearly as hard as the police one. And remember that each unit 1 one hundred is a badge. So the xp curve is gonna need
to be easier, it's gonna have to be easier to reach the max rank." / "ensure for the ifc version, the secret flares are more spread
out and come through earlier on ... There's 6 of them, so every 15 levels or so I'd think you can get one for the ifc?"
Read off the app (the academy in one page, Fire Code in another), XP from computeRunXp itself:
(1) every Fire Code level costs a fifth of the academy's, level by level (within 1%); the academy's curve is its own (unscaled);
(2) taking every Fire Code chapter to 100% - an imperfect first go (about 70%, 9s a question) and a perfect second (8s a question),
    as computeRunXp pays them - reaches level 80: the top rank's level is there by the time its badges are;
(3) each Fire Code rank's level is there by its badges: its badge count of average chapters (the same two goes each) reaches the
    rank's level, and even the cheapest chapters reach half of it - the level never stands far past the badges;
(4) Fire Code's six flares are drawn about every 13-15 levels from about 13 (the first at 16 or below, each next 10-18 levels on,
    the last by 80); the academy's first is still where it was (20);
(5) no page errors.
Run:  python3 tools/check-b384-ifccurve.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ic"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
LEVELS = list(range(5, 81, 5))
CURVE = "(ls)=>ls.map(l => xpForLevel(l))"
CHAPTERS = """()=>{ const units = {}; QUESTIONS.forEach(q => { const t=(q.topic||'').trim(); if(t) units[t] = (units[t]||0) + 1; });
  const pay = (n, good, sec, hundo, u) => computeRunXp({ good, answered: n, elapsedMs: n * sec * 1000,
      okList: Array.from({ length: n }, (_, i) => i < good ? !(i % 4 === 3 && good < n) : false), hundos: hundo ? 1 : 0, hundoUnits: hundo ? [u] : [],
      wholeUnits: 1, scorePRs: [], timePRs: [], badgesPaid: 0 }).total;
  return Object.keys(units).map(u => { const n = units[u]; return { u, n, xp: pay(n, Math.round(n * .7), 9, false, u) + pay(n, n, 8, true, u) }; }).sort((a, b) => a.xp - b.xp); }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    # the academy
    ctx, pg, errsA = G["page"](br, G["init"](G["academy"], active="academy"))
    acad = pg.evaluate("()=>({ cls: window.NOVA_CLASS, first: (FLARE_WINDOWS.red || [])[0] })"); acurve = pg.evaluate(CURVE, LEVELS)
    ctx.close()
    # Fire Code
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
    info = pg.evaluate("()=>({ cls: window.NOVA_CLASS, tiers: TIER_ORDER_FULL.map(k => [k, TIER_UNLOCKS[k].level, TIER_UNLOCKS[k].badges]) })")
    icurve = pg.evaluate(CURVE, LEVELS)
    ch = pg.evaluate(CHAPTERS)
    flares = pg.evaluate("()=>{ store.flareLevels = {}; return MYSTERY_ORDER.map(c => mysteryLevelGate(c)); }")
    ratios = [round(i / a, 4) for i, a in zip(icurve, acurve)]
    chk("(1) every Fire Code level costs a fifth of the academy's (ratios %s ... %s), the academy's unscaled (%s XP to 80, %s)" % (ratios[0], ratios[-1], acurve[-1], acad["cls"]),
        info["cls"] == "ifc" and acad["cls"] == "academy" and all(abs(r - .2) <= .2 * .01 + 1 / max(1, a) for r, a in zip(ratios, acurve)), list(zip(LEVELS, acurve, icurve)))
    total = sum(c["xp"] for c in ch)
    chk("(2) every chapter taken to 100%% (%d chapters, %d XP) reaches level 80 (%d XP)" % (len(ch), total, icurve[-1]), total >= icurve[-1], [total, icurve[-1]])
    far = []
    mean = total / max(1, len(ch))
    for k, lvl, b in info["tiers"]:
        need = pg.evaluate("(l)=>xpForLevel(l)", lvl)
        typical, cheapest = mean * b, sum(c["xp"] for c in ch[:b])
        if typical < need or cheapest < .5 * need: far.append((k, lvl, b, round(typical), cheapest, need))
    chk("(3) each rank's level is there by its badges: its badge count of average chapters reaches it, and even the cheapest chapters reach half of it (%s)" % ([(k, l, b) for k, l, b in info["tiers"]],), not far, far)
    gaps = [b - a for a, b in zip(flares, flares[1:])]
    chk("(4) Fire Code's flares about every 15 levels from ~15 (%s, gaps %s); the academy's first still %s" % (flares, gaps, acad["first"]),
        flares[0] <= 16 and all(10 <= g <= 18 for g in gaps) and flares[-1] <= 80 and acad["first"] == 20, [flares, gaps, acad])
    chk("(5) no page errors", not errs and not errsA, (errs + errsA)[:3])
    ctx.close(); br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
