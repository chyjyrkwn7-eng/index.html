"""Build 384.60: Fire Code's ranks climb to EVERY chapter, and nobody loses one.
Madison: "We need to change how many you need to reach ranks. Don't change how many for Bronze, Silver, but it should be 58 to
reach Supernova and it needs to progressively get there." Fire Code has 58 chapters, a badge each (one 100% a chapter).
Read off the pages, never typed (the OLD ladder is read from `git show origin/main:index.html`, loaded in a page of its own):
 (1) Fire Code's badge counts rise rank by rank, the gaps never shrink and the last is bigger than the first; Bronze and Silver
     (rookie, ranger) are exactly the base build's; Supernova is the chapter count; the levels are the base build's; each label is generated
     from the rule ("Reach level N and M badges");
 (2) the academy's ladder is untouched (same counts as the base build) and ifcLadderFloor384bOnce does nothing there;
 (3) NOBODY LOSES A RANK: an account sitting exactly on each rank of the BASE ladder (its badges, its level), booted through
     the real launch, still holds that rank - and Gold, Platinum, Sapphire and Amethyst are held by the rank floor (the raw level-and-badges
     rank is lower on this ladder), the floor written once under class26e.ifcladder384b before the work;
 (4) everything a rank hands over is derived and still there for an account that held it: the colour, every character that rank
     unlocks, the published row's rank (rankOfEntry of the row it would publish) and its level; the level shown is the curve's
     own; no rank-up is owed and none re-fires (rankUpShown untouched, no badge cutscene queued), and no "ranked down" text;
 (5) a FRESH account (no floor) one badge short of Platinum's new count shows Gold, at the count Platinum - the new ladder as asked;
 (6) the Rank tab's meter reads the NEXT rank after the floor: for an account whose floor is above what its badges show, the next
     rank is the one after the floor, its requirement is the page's own, and progress rises with each badge and stays under 100%;
 (7) a floor only raises (a same-account merge takes the larger), is written before the work (a throwing save cannot loop it) and
     runs once per device;
 (8) no page errors.
Run:  python3 tools/check-b384-ladder58.py
      python3 tools/check-b384-ladder58.py --against OLD/index.html      (must FAIL: the ladder is the previous one)
      --base REF   the git ref the old ladder is read from (default origin/main)"""
import copy, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384l58"}
exec(src, G)
g = G["g"]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
BASE_REF = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "origin/main"
BASE = subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=REPO, capture_output=True, text=True, check=True).stdout
NEW = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv \
    else open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
def use(html):
    def _p(ins):
        v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], html)
    g["patched"] = _p
PRESET = "localStorage.setItem('class26e.ifc.ifcladder384b','1');"   # Fire Code keeps its keys under class26e.ifc.*
def launch(br, html, st, active="ifc", preset=False):
    use(html)
    init = G["init"](st, active=active) if active == "ifc" else G["init"](st, active=active)
    if preset: init = init.replace("sessionStorage.setItem('__seeded','1');", "sessionStorage.setItem('__seeded','1'); " + PRESET, 1)
    ctx, pg, errs = G["page"](br, init)
    return ctx, pg, errs
LADDER = "()=>({ cls: window.NOVA_CLASS, n: (()=>{ const s={}; QUESTIONS.forEach(q=>{ const t=(q.topic||'').trim(); if(t) s[t]=1; }); return Object.keys(s).length; })(), " \
         "names: TIER_ORDER_FULL.map(k=>RANK_DISPLAY_NAME[k]), b: TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].badges), l: TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].level), lab: TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].label), " \
         "topics: classTopics(), xp: TIER_ORDER_FULL.map(k=>xpForLevel(TIER_UNLOCKS[k].level)) })"
TIER = ["rookie", "ranger", "veteran", "vanguard", "adept", "elite", "titan"]
STATE = """()=>{
  const row = buildLeaderboardRow(), fixed = fixBoardLevel(Object.assign({}, row));
  const lv = levelOf(store), bd = badgeCountOf(store);
  const idx = TIER_ORDER_FULL.indexOf(rankOf(store));
  return { rank: rankOf(store), idx, raw: rankOfStats(lv, bd, 0), rawIdx: TIER_ORDER_FULL.indexOf(rankOfStats(lv, bd, 0)), floor: store.rankFloor, badges: bd, level: lv,
    curve: levelFromPoints(store.lifetime.points), shown: store.rankUpShown, owed: !!rankUpOwed(), queued: (store.pendingBadgeUnlocks || []).length,
    key: localStorage.getItem('class26e.ifcladder384b'),
    accents: TIER_ORDER_FULL.map(k => !isLockedAccent(k)),
    chars: AVATAR_CHARACTERS.filter(c => c.unlock && !c.retired).map(c => [c.id, TIER_ORDER_FULL.indexOf(c.unlock), !isLockedCharacter(c.id)]),
    pub: { rank: rankOfEntry(row), floor: row.rankFloor, level: row.level, fixedLevel: fixed.level, badges: row.badges } };
}"""
def account(base_store, topics, badges, level, xp, floor=0, shown=None):
    s = copy.deepcopy(base_store)
    s["unitPerfects"] = {t: 1 for t in topics[:badges]}
    s["lifetime"] = dict(s.get("lifetime") or {}, points=xp(level) + 5)
    s["rankFloor"] = floor; s["levelFloor"] = 0
    s["rankUpShown"] = shown
    s["theme"] = {"mode": "dark", "accent": "ink"}
    for k in ("pendingBadgeUnlocks", "pendingHomeUnlocks"): s[k] = []
    return s

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # ---- the two ladders, read off two pages
    ctx, pg, e0 = launch(br, BASE, G["ifc"]); old = pg.evaluate(LADDER); ctx.close()
    ctx, pg, e1 = launch(br, NEW, G["ifc"]); new = pg.evaluate(LADDER)
    topics = new["topics"]; n = new["n"]
    XPT = pg.evaluate("()=>Array.from({length: 81}, (_, i) => xpForLevel(i))")
    xp = lambda lv: XPT[lv]
    ctx.close()
    ob, nb = old["b"], new["b"]
    gaps = [b - a for a, b in zip(nb, nb[1:])]
    chk("(1) Fire Code's badge counts %s of %d chapters (was %s): rising, gaps %s never shrink and the last is bigger than the first" % (nb, n, ob, gaps),
        old["cls"] == new["cls"] == "ifc" and all(a < b for a, b in zip(nb, nb[1:])) and all(a <= b for a, b in zip(gaps, gaps[1:])) and gaps[-1] > gaps[0], [nb, gaps])
    chk("(1) Bronze and Silver are the base build's (%s %s against %s)" % (new["names"][:2], nb[:2], ob[:2]), nb[:2] == ob[:2], [nb, ob])
    chk("(1) Supernova asks for every chapter (%s of %d), and the levels are the base build's" % (nb[-1], n), nb[-1] == n and new["l"] == old["l"], [nb, n, new["l"], old["l"]])
    chk("(1) each label is generated from its rule", all(lab == "Reach level %d and %d badge%s" % (l, b, "" if b == 1 else "s") for lab, l, b in zip(new["lab"], new["l"], nb)), new["lab"])

    # ---- (2) the academy
    ctx, pg, ea = launch(br, BASE, G["academy"], active="academy"); oa = pg.evaluate(LADDER); ctx.close()
    ctx, pg, eb = launch(br, NEW, G["academy"], active="academy")
    na = pg.evaluate(LADDER)
    did = pg.evaluate("()=>{ try{ localStorage.removeItem('class26e.ifcladder384b'); const f = store.rankFloor; const r = (typeof ifcLadderFloor384bOnce === 'function') ? ifcLadderFloor384bOnce() : 'none'; return { r, same: f === store.rankFloor }; }catch(e){ return { err: String(e) }; } }")
    chk("(2) the academy's ladder is the base build's (%s) and the new floor does nothing there (%s)" % (na["b"], did), na["cls"] == "academy" and na["b"] == oa["b"] and na["l"] == oa["l"] and did.get("r") in (False, "none") and did.get("same", True), [na, oa, did])
    ctx.close()

    # ---- (3)(4) every rank of the BASE ladder, booted for real
    held_by_floor = {}
    for i, k in enumerate(TIER):
        st = account(G["ifc"], topics, ob[i], old["l"][i], xp, shown=i + 1)
        ctx, pg, er = launch(br, NEW, st)
        pg.wait_for_timeout(600)
        r = pg.evaluate(STATE)
        held_by_floor[k] = r
        chk("(3) %s on the base ladder (%d badges, level %d) still holds %s (rank %s, floor %s, raw rank %s)" % (new["names"][i], ob[i], old["l"][i], new["names"][i], r["rank"], r["floor"], r["raw"]),
            r["rank"] == k, r)
        if i in (2, 3, 4, 5):
            chk("(3) ...and %s is held by the floor, not by its badges (raw rank index %s < %d; floor %s; key written %s)" % (new["names"][i], r["rawIdx"], i, r["floor"], r["key"]),
                r["rawIdx"] < i and r["floor"] == i + 1 and r["key"] == "1", r)
        chk("(4) %s: the colour and every character up to it are unlocked, the published row says %s at its level (%s), nothing is owed or queued"
            % (k, r["pub"]["rank"], r["pub"]["level"]),
            all(r["accents"][:i + 1]) and all(c[2] for c in r["chars"] if 0 <= c[1] <= i) and r["pub"]["rank"] == k and r["pub"]["floor"] == r["floor"]
            and r["pub"]["fixedLevel"] == r["pub"]["level"] == r["level"] == r["curve"] and not r["owed"] and r["shown"] == i + 1 and r["queued"] == 0, r)
        if i == 5:
            pg.evaluate("()=>{ showProfile('ranks'); }"); pg.wait_for_timeout(1200)
            t = pg.evaluate("()=>document.getElementById('stage').innerText")
            bad = re.findall(r"ranked down|lost your rank|dropped a rank|you fell|demoted", t, re.I)
            say = pg.evaluate("()=>TIER_UNLOCKS.titan.badges")
            chk("(4) the Rank tab for Amethyst says nothing of a rank lost (%s) and names Supernova's own %s badges" % (bad, say), not bad and re.search(r"\b%d\b" % say, t), t[:300])
        ctx.close()

    # ---- (5) a fresh account, no floor
    for b, want in ((nb[3] - 1, "veteran"), (nb[3], "vanguard")):
        st = account(G["ifc"], topics, b, old["l"][3], xp, shown=3)
        ctx, pg, er = launch(br, NEW, st, preset=True)
        pg.wait_for_timeout(600)
        r = pg.evaluate(STATE); ctx.close()
        chk("(5) with no floor, %d badges and the level for Platinum shows %s (rank %s, floor %s)" % (b, new["names"][TIER.index(want)], new["names"][TIER.index(r["rank"])] if r["rank"] else None, r["floor"]), r["rank"] == want and r["floor"] in (0, None, 3), r)

    # ---- (6) the meter, for an account whose floor is above what its badges show
    METER = """()=>{ const s = rankStepProgress(), c = rankChallengesOf();
      return { held: s.held, next: s.next, pct: s.pct, lvlPart: s.lvlPart, bdgPart: s.bdgPart, ch: c && c.key, need: c && c.list.map(x => [x.kind, x.need, x.now]),
               rule: TIER_UNLOCKS[s.next] && TIER_UNLOCKS[s.next].badges, road: rankRoadProgress(), badges: badgeCountOf(store) }; }"""
    pcts = []; rows = []
    for b in (20, 25, 29, 31):
        st = account(G["ifc"], topics, b, new["l"][4], xp, floor=0, shown=4)
        st["rankFloor"] = 4                                    # Platinum, held on the previous ladder
        ctx, pg, er = launch(br, NEW, st, preset=True)
        pg.wait_for_timeout(600)
        m = pg.evaluate(METER); ctx.close(); rows.append(m); pcts.append(m["pct"])
    m0 = rows[0]
    chk("(6) floor Platinum with 20 badges: held %s, next is the rank after the floor (%s), its badges are the page's own (%s, challenge %s)" % (m0["held"], m0["next"], m0["rule"], m0["need"]),
        m0["held"] == "vanguard" and m0["next"] == "adept" and m0["ch"] == "adept" and [x for x in m0["need"] if x[0] == "badges"][0][1] == m0["rule"], m0)
    chk("(6) its progress is a real fraction that rises with every badge and stays under 100%% (%s)" % ([round(p, 3) for p in pcts]),
        all(0 <= p < 1 for p in pcts) and all(a <= b for a, b in zip(pcts, pcts[1:])) and pcts[-1] > pcts[0], rows)
    st = account(G["ifc"], topics, nb[4], new["l"][4], xp, floor=4, shown=4)
    ctx, pg, er = launch(br, NEW, st, preset=True); pg.wait_for_timeout(600)
    m = pg.evaluate(METER); ctx.close()
    chk("(6) at Sapphire's own %d badges the rank is Sapphire and the next is Amethyst (%s, %s)" % (nb[4], m["held"], m["next"]), m["held"] == "adept" and m["next"] == "elite", m)

    # ---- (7) a floor only raises, is written before the work, and runs once
    st = account(G["ifc"], topics, ob[5], old["l"][5], xp, shown=6)
    ctx, pg, er = launch(br, NEW, st)
    pg.wait_for_timeout(600)
    r = pg.evaluate("""()=>{
      if(typeof ifcLadderFloor384bOnce !== 'function') return { missing: true };
      const out = {}; out.once = ifcLadderFloor384bOnce();                       // already ran at launch: nothing again
      const dst = { rankFloor: 0 }; const had = store.rankFloor;
      try{ mergeSameAccount(dst, { rankFloor: had }); }catch(e){ out.mergeErr = String(e); }
      out.merged = dst.rankFloor;
      const dst2 = { rankFloor: 7 }; try{ mergeSameAccount(dst2, { rankFloor: 2 }); }catch(e){}
      out.kept = dst2.rankFloor;
      localStorage.removeItem('class26e.ifcladder384b'); const was = window.saveStore;
      store.rankFloor = 0; let thrown = false;
      try{ window.saveStore = function(){ throw new Error('disk'); }; out.crash = ifcLadderFloor384bOnce(); }catch(e){ thrown = true; }
      window.saveStore = was; out.thrown = thrown; out.keyAfterCrash = localStorage.getItem('class26e.ifcladder384b');
      out.again = ifcLadderFloor384bOnce();
      return out; }""")
    chk("(7) the floor merges by max, keeps the larger, and its once-key is written before the work (a throwing save cannot loop it) (%s)" % r,
        r.get("once") is False and r.get("merged") == 6 and r.get("kept") == 7 and r.get("keyAfterCrash") == "1" and r.get("again") is False, r)
    ctx.close()

    errs = e0 + e1 + ea + eb
    chk("(8) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
