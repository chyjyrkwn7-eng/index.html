"""Build 384.88: the academy's Amethyst asks 16 badges and Supernova 25, and nobody loses a rank.
Madison: "Update the badge requirements for the amethyst and supernova for academy class. 16 for amethyst. 25 for supernova."
Read off the pages, never typed (the OLD ladder is read from `git show origin/main:index.html`, loaded in a page of its own):
 (1) the academy: Amethyst (elite) and Supernova (titan) ask 16 and 25 badges at the base build's levels, every other rank is
     the base build's, each label is generated from its rule, and the Rank tab of a fresh account prints both on their cards.
     The earnable badge count (the academy's units) is reported: Supernova's 25 may sit above it, as asked;
 (2) Fire Code is untouched: its ladder (counts, levels, labels) is the base build's, and so is the academy ladder its
     one-time floor reads (TIER_UNLOCKS_ACADEMY);
 (3) NOBODY LOSES A RANK: an Amethyst at 12-15 badges and a Supernova at 14-24 badges on the base ladder, booted through the
     real launch (a stored copy without the new flag), still hold their rank - by the rank floor, the raw rank being lower - at
     the curve's own level (the wall does not hold them back), the published row says the same rank and level, the colour and
     the rank's characters stay unlocked, nothing is owed or queued, the Rank tab names the right next goal (Supernova's own
     level and badges for an Amethyst, no next rank for a Supernova) and says nothing of a rank lost;
 (4) the new ladder as asked for a fresh account (the flag already set, no floor): 15 badges at level 70 is Sapphire, 16 is
     Amethyst; every badge there is at level 80 is Amethyst while the academy has fewer units than Supernova's count;
 (5) the rank bar math uses the new numbers: the Overall board's progress for a Sapphire at 12 badges, the road map's light,
     and the next rank's challenges are the page's own formulas over the page's own 16 and 25;
 (6) no unlock is stored: booting a holder adds no store field on this build that the base build does not add, other than the
     ladder's own flag; the flag and the floor merge by max and a reset sets the flag with no floor; the floor runs once
     (a copy carrying the flag is never floored again, however many badges it has);
 (7) no page errors.
Run:  python3 tools/check-b384-academyranks.py
      python3 tools/check-b384-academyranks.py --against OLD/index.html      (must FAIL: the ladder is the previous one)
      --base REF   the git ref the old ladder is read from (default origin/main)"""
import copy, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ar"}
_argv = sys.argv; sys.argv = [sys.argv[0]]
exec(src, G)
sys.argv = _argv
g = G["g"]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
BASE_REF = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "origin/main"
BASE = subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=REPO, capture_output=True, text=True, check=True).stdout
NEW = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv \
    else open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
ACAD0 = copy.deepcopy(G["academy"])
def use(html):
    def _p(ins):
        v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], html)
    g["patched"] = _p
def launch(br, html, acad=None, active="academy"):
    use(html)
    # version.json answers with the loaded page's own build, so neither page is told to update (and reload) mid-check
    G["OLD_BUILD"] = re.search(r'const APP_BUILD = "([^"]+)"', html).group(1)
    G["academy"] = acad if acad is not None else ACAD0
    return G["page"](br, G["init"](G["ifc"] if active == "ifc" else None, active=active))
LADDER = "()=>({ cls: window.NOVA_CLASS, names: TIER_ORDER_FULL.map(k=>RANK_DISPLAY_NAME[k]), b: TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].badges), " \
         "l: TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].level), lab: TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].label), " \
         "acad: (typeof TIER_UNLOCKS_ACADEMY === 'object') ? TIER_ORDER_FULL.map(k=>[TIER_UNLOCKS_ACADEMY[k].level, TIER_UNLOCKS_ACADEMY[k].badges]) : null, " \
         "topics: classTopics(), need: classTopics().map(u=>badgeThresholdFor(u)), xp: Array.from({length: 81}, (_, i) => xpForLevel(i)) })"
TIER = ["rookie", "ranger", "veteran", "vanguard", "adept", "elite", "titan"]
STATE = """()=>{
  const row = buildLeaderboardRow(), fixed = fixBoardLevel(Object.assign({}, row));
  const lv = levelOf(store), bd = badgeCountOf(store), c = rankChallengesOf();
  return { rank: rankOf(store), raw: rankOfStats(lv, bd, 0), floor: store.rankFloor, flag: store.academyLadderRule, badges: bd, level: lv,
    curve: levelFromPoints(store.lifetime.points), shown: store.rankUpShown, owed: !!rankUpOwed(), queued: (store.pendingBadgeUnlocks || []).length,
    accents: TIER_ORDER_FULL.map(k => !isLockedAccent(k)),
    chars: AVATAR_CHARACTERS.filter(c => c.unlock && !c.retired).map(c => [c.id, TIER_ORDER_FULL.indexOf(c.unlock), !isLockedCharacter(c.id)]),
    next: c ? { key: c.key, need: c.list.map(x => [x.kind, x.need, x.now]) } : null,
    note: rankChallengeNote(c),
    keys: Object.keys(store).sort(),
    pub: { rank: rankOfEntry(row), floor: row.rankFloor, level: row.level, fixedLevel: fixed.level, badges: row.badges } };
}"""
def account(base, L, badges, level, floor=0, shown=None, flag=None):
    s = copy.deepcopy(base)
    s["unitPerfects"] = {u: n for u, n in list(zip(L["topics"], L["need"]))[:badges]}
    s["lifetime"] = dict(s.get("lifetime") or {}, points=L["xp"][level] + 5)
    s["rankFloor"] = floor; s["levelFloor"] = 0
    s["rankUpShown"] = shown
    s["theme"] = {"mode": "dark", "accent": "ink"}
    for k in ("pendingBadgeUnlocks", "pendingHomeUnlocks"): s[k] = []
    s.pop("academyLadderRule", None)
    if flag is not None: s["academyLadderRule"] = flag
    return s
def rank_tab(pg):
    pg.evaluate("()=>{ showProfile('ranks'); }"); pg.wait_for_timeout(1400)
    return pg.evaluate("()=>document.getElementById('stage').innerText")
def card(text, name):
    """the requirement line printed under a rank's name on the climb ("Level 70 · 16 badges")"""
    m = re.search(r"\n%s\n(?:[^\n]*\n){0,3}?Level (\d+) · (\d+) badges?" % re.escape(name), text)
    return (int(m.group(1)), int(m.group(2))) if m else None
DROP = re.compile(r"ranked down|lost your rank|dropped a rank|you fell|demoted|rank (was )?taken", re.I)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    # ---- the ladders, read off two pages
    ctx, pg, e = launch(br, BASE); old = pg.evaluate(LADDER); ctx.close(); errs += e
    ctx, pg, e = launch(br, NEW); new = pg.evaluate(LADDER); errs += e
    flag = pg.evaluate("()=>typeof ACADEMY_LADDER_RULE === 'number' ? ACADEMY_LADDER_RULE : null")
    tab = rank_tab(pg); ctx.close()
    L = new; ob, nb, n = old["b"], new["b"], len(new["topics"])
    i_am, i_sn = TIER.index("elite"), TIER.index("titan")
    print("     the academy has %d units, so %d badges can be earned (badgeCountOf with every unit done is checked in (4))" % (n, n))
    chk("(1) academy: Amethyst asks 16 badges and Supernova 25 (%s %s, was %s %s)" % (new["names"][i_am], nb[i_am], ob[i_am], ob[i_sn]),
        new["cls"] == old["cls"] == "academy" and nb[i_am] == 16 and nb[i_sn] == 25, [nb, ob])
    chk("(1) every other rank and every level is the base build's (%s / %s)" % (nb[:5], new["l"]), nb[:5] == ob[:5] and new["l"] == old["l"], [nb, ob, new["l"], old["l"]])
    chk("(1) each label is generated from its rule (%s, %s)" % (new["lab"][i_am], new["lab"][i_sn]),
        all(lab == "Reach level %d and %d badge%s" % (l, b, "" if b == 1 else "s") for lab, l, b in zip(new["lab"], new["l"], nb)), new["lab"])
    ca, cs = card(tab, new["names"][i_am]), card(tab, new["names"][i_sn])
    chk("(1) the Rank tab's cards print them: %s %s, %s %s" % (new["names"][i_am], ca, new["names"][i_sn], cs),
        ca == (new["l"][i_am], nb[i_am]) and cs == (new["l"][i_sn], nb[i_sn]), tab[-900:])
    chk("(1) the account's ladder flag exists (%s)" % flag, isinstance(flag, int) and flag > 0, flag)

    # ---- (2) Fire Code untouched
    ctx, pg, e = launch(br, BASE, active="ifc"); fo = pg.evaluate(LADDER); ctx.close(); errs += e
    ctx, pg, e = launch(br, NEW, active="ifc"); fn = pg.evaluate(LADDER); ctx.close(); errs += e
    chk("(2) Fire Code's ladder is the base build's (%s, levels %s)" % (fn["b"], fn["l"]),
        fn["cls"] == fo["cls"] == "ifc" and fn["b"] == fo["b"] and fn["l"] == fo["l"] and fn["lab"] == fo["lab"], [fn["b"], fo["b"]])
    chk("(2) ...and the academy ladder its one-time floor reads is the base build's (%s)" % (fn["acad"],),
        fn["acad"] == fo["acad"] and fn["acad"] is not None, [fn["acad"], fo["acad"]])

    # ---- (3) holders on the base ladder, booted for real
    base_keys = {}
    for k, counts, lvl in (("elite", (12, 13, 14, 15), old["l"][i_am]), ("titan", (14, 18, 24), old["l"][i_sn])):
        i = TIER.index(k)
        for b in counts:
            # sit a level past the rank's own, so a wall that held them back would show
            want_lv = min(80, lvl + (2 if k == "elite" else 0))
            st = account(ACAD0, L, b, want_lv, shown=i + 1)
            ctx, pg, e = launch(br, NEW, st); errs += e
            pg.wait_for_timeout(600)
            r = pg.evaluate(STATE)
            t = rank_tab(pg); ctx.close()
            nm = new["names"][i]
            chk("(3) %s on the base ladder (%d badges, level %d) still holds %s (rank %s, floor %s, raw rank %s)" % (nm, b, want_lv, nm, r["rank"], r["floor"], r["raw"]),
                r["rank"] == k and r["floor"] == i + 1 and TIER.index(r["raw"]) < i if r["raw"] else r["rank"] == k and r["floor"] == i + 1, r)
            chk("(3) ...at the curve's own level %d (shown %d), the published row says %s at level %s, the colour and its characters are unlocked, nothing owed or queued"
                % (r["curve"], r["level"], r["pub"]["rank"], r["pub"]["level"]),
                r["level"] == r["curve"] == want_lv and r["pub"]["rank"] == k and r["pub"]["floor"] == i + 1 and r["pub"]["fixedLevel"] == r["pub"]["level"] == want_lv
                and all(r["accents"][:i + 1]) and all(c[2] for c in r["chars"] if 0 <= c[1] <= i) and not r["owed"] and r["shown"] == i + 1 and r["queued"] == 0, r)
            if k == "elite":
                nxt = r["next"]
                want = [["level", new["l"][i_sn], want_lv], ["badges", nb[i_sn], b]]
                said = re.search(r"TO REACH\s+%s" % new["names"][i_sn].upper(), t, re.I) and re.search(r"\b%d of %d\b" % (b, nb[i_sn]), t)
                chk("(3) ...and its next goal is %s's own level %d and %d badges (%s; the Rank tab says '%d of %d': %s; note %r)"
                    % (new["names"][i_sn], new["l"][i_sn], nb[i_sn], nxt, b, nb[i_sn], bool(said), r["note"]),
                    nxt and nxt["key"] == "titan" and nxt["need"] == want and said and str(nb[i_sn] - b) in r["note"], [nxt, t[:400], r["note"]])
            else:
                chk("(3) ...and there is no next rank to chase (%s)" % (r["next"],), r["next"] is None and not re.search(r"TO REACH", t, re.I), [r["next"], t[:300]])
            bad = DROP.findall(t)
            chk("(3) ...and the Rank tab says nothing of a rank lost (%s)" % bad, not bad, t[:300])
            if b == counts[0]:
                ctx, pg, e = launch(br, BASE, st); errs += e; pg.wait_for_timeout(600)
                base_keys[k] = (pg.evaluate("()=>Object.keys(store).sort()"), r["keys"]); ctx.close()

    # ---- (4) the new ladder, for a fresh account (flag set, no floor)
    for b, lv, want in ((nb[i_am] - 1, new["l"][i_am], "adept"), (nb[i_am], new["l"][i_am], "elite"), (n, new["l"][i_sn], "elite" if n < nb[i_sn] else "titan")):
        st = account(ACAD0, L, b, lv, shown=TIER.index(want) + 1, flag=flag or 1)
        ctx, pg, e = launch(br, NEW, st); errs += e
        pg.wait_for_timeout(600)
        r = pg.evaluate(STATE); ctx.close()
        chk("(4) with no floor, %d badges at level %d is %s (rank %s, floor %s, badges counted %s)" % (b, lv, want, r["rank"], r["floor"], r["badges"]),
            r["rank"] == want and not r["floor"] and r["badges"] == b, r)

    # ---- (5) the rank bar math, over the page's own numbers
    st = account(ACAD0, L, 12, new["l"][i_am], shown=5, flag=flag or 1)
    ctx, pg, e = launch(br, NEW, st); errs += e
    pg.wait_for_timeout(600)
    m = pg.evaluate("""()=>{ const p = overallProgressOf(70, 12, 0); const s = rankRoadStateNow(); const c = rankChallengesOf();
      return { p, s, frac: rankRoadFracOf(s), W: [RANK_ROAD_NEAR, RANK_ROAD_BADGE_W, RANK_ROAD_PART_W], c: c && c.list.map(x => [x.kind, x.need]),
               H: TIER_UNLOCKS.adept, N: TIER_UNLOCKS.elite }; }""")
    ctx.close()
    exp_p = (70 / m["N"]["level"] * 100 + 12 / m["N"]["badges"] * 100) / 2
    s = m["s"]; near, bw, pw_ = m["W"]
    def part(v, a, b_, met):
        if met: return 1
        return 0 if b_ - a <= 0 else max(0, min(.999, (v - a) / (b_ - a)))
    Lp = part(s["levelExact"], min(m["H"]["level"], m["N"]["level"]), m["N"]["level"], s["level"] >= m["N"]["level"])
    Bp = part(s["badges"] + pw_ * s["partials"], min(m["H"]["badges"], m["N"]["badges"]), m["N"]["badges"], s["badges"] >= m["N"]["badges"])
    exp_f = 1 if Lp >= 1 and Bp >= 1 else near * (bw * Bp + (1 - bw) * Lp)
    chk("(5) the Overall board's progress for a Sapphire at level 70 and 12 badges is %.2f%% over Amethyst's %d badges (expected %.2f%%)" % (m["p"]["progress"], m["N"]["badges"], exp_p),
        m["N"]["badges"] == 16 and abs(m["p"]["progress"] - exp_p) < 1e-9 and m["p"]["key"] == "adept", m)
    chk("(5) the road map's light is the page's formula over 9 -> 16 badges (%.4f, expected %.4f) and short of the next circle" % (m["frac"], exp_f),
        abs(m["frac"] - exp_f) < 1e-9 and 0 < m["frac"] < near, m)
    chk("(5) the next rank's challenges ask Amethyst's own level and badges (%s)" % m["c"], m["c"] == [["level", m["N"]["level"]], ["badges", 16]], m["c"])

    # ---- (6) nothing stored, merges, reset, once
    for k, (bk, nk) in base_keys.items():
        extra = sorted(set(nk) - set(bk))
        chk("(6) booting a %s holder adds no store field the base build does not, beyond the ladder's flag (%s)" % (k, extra), extra == ["academyLadderRule"], extra)
    st = account(ACAD0, L, 13, new["l"][i_am], shown=6)
    ctx, pg, e = launch(br, NEW, st); errs += e
    pg.wait_for_timeout(600)
    r = pg.evaluate("""()=>{
      const out = {}; const R = (typeof ACADEMY_LADDER_RULE === 'number') ? ACADEMY_LADDER_RULE : -1;
      const dst = { rankFloor: 0, academyLadderRule: 0 }; mergeSameAccount(dst, { rankFloor: 6, academyLadderRule: R });
      out.merged = [dst.rankFloor, dst.academyLadderRule];
      const dst2 = { rankFloor: 7, academyLadderRule: R }; mergeSameAccount(dst2, { rankFloor: 2 });
      out.kept = [dst2.rankFloor, dst2.academyLadderRule];
      /* once: a flagged copy with Supernova's OLD numbers (14 badges, level 80) is not floored - it is a Sapphire on this ladder */
      const copy = JSON.parse(JSON.stringify(store)); copy.rankFloor = 0; copy.academyLadderRule = R;
      copy.unitPerfects = {}; classTopics().slice(0, 14).forEach(u => copy.unitPerfects[u] = badgeThresholdFor(u)); copy.lifetime.points = xpForLevel(80) + 5;
      applyLoadedData(copy); out.flagged = [store.rankFloor, rankOf(store)];
      /* an unflagged copy (an older build's) is */
      const old = JSON.parse(JSON.stringify(copy)); delete old.academyLadderRule; applyLoadedData(old); out.unflagged = [store.rankFloor, rankOf(store), store.academyLadderRule];
      return out; }""")
    chk("(6) the floor and the flag merge by max and keep the larger (%s)" % r, r["merged"] == [6, flag] and r["kept"][0] == 7 and r["kept"][1] == flag, r)
    chk("(6) a copy carrying the flag is never floored (%s), one without it is, once (%s)" % (r["flagged"], r["unflagged"]),
        r["flagged"] == [0, "adept"] and r["unflagged"] == [7, "titan", flag], r)
    rs = pg.evaluate("""()=>{ store.rankFloor = 6; store.academyLadderRule = 0; try{ wipeLocalProgressAndSettings(); }catch(e){ return { err: String(e) }; }
      return { floor: store.rankFloor, flag: store.academyLadderRule }; }""")
    chk("(6) a reset starts on the new ladder with no floor (%s)" % rs, rs.get("floor") == 0 and rs.get("flag") == flag, rs)
    ctx.close()

    chk("(7) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
