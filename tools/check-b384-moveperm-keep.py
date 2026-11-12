#!/usr/bin/env python3
"""Build 384.47: nobody loses a badge, a hundo, a star, a level, a rank or an answer to the county permit questions moving to Chapter 1.

The owner's rule for every question move: no one loses anything. 69 Fire Code questions moved into Chapter 1 and 18 were taken out (15 repeats, ch20-508, ch30-505 and, in 384.70, ch30-709, which the owner removed),
from 35 chapters (and Chapter 1 itself grew from 88 to 157). The Fire Code badge is ONE hundo per chapter, stored per chapter NAME
(store.unitPerfects), never recomputed from a chapter's size. A Fire Code account that ALREADY holds the badge in every chapter the move
touches (a hundo count beyond it in one), with answered questions in each, partly-answered chapters, the moved and the removed questions
answered and starred, and points, hundos and a rank on top, is booted on the app and bank on origin/main (BASE), its saved state is taken as
it stands, and that same state is booted on this build. Everything is read off the page:
(a) the badge is still held for each affected chapter (badgesEarnedList, badgeCountOf, unitBadgeEarned) and every one is drawn as earned in
    the badge case on Profile (#stage .badge-tile.is-earned) and counted on the Profile card;
(b) every stored field of the account except the per-question answer counts and stars (stats, flagged, unflagged) and the save time
    (lastModified, which the boot copy's save moves) is byte-identical: the hundo counters (unitPerfects), unit stars and levels, hundos total
    (lifetime.perfectTests), points / level / rank inputs, lifetime answered / correct, best times and percentages, run counts; the level, rank,
    badge count and the leaderboard row it publishes are the same;
(c) no pop-up, badge cutscene or rank-up is owed: pendingBadgeUnlocks is empty and stays empty, nothing is pending for Home (pendingHomeUnlocks),
    and no cutscene or unlock card is on the page;
(d) THE ANSWER COUNTS: every stored answer entry is still there and not one is lower (nothing is removed or lowered, the removed questions'
    entries too); each moved question's tally also sits on its new key (copied once at boot), so the answered-at-least-once and right / wrong
    totals over the chapters, and the Stats ring's "answered right once" count, change by EXACTLY what the 18 removed questions held (their
    entries stay in the store, but no chapter lists them any more) and not by one more; Chapter 1's answered count rises by the moved questions
    answered (they arrive with their history);
(e) two devices of one account, one on the old bank and one on the new, merged either way with mergeSameAccount (and added with
    mergeLeavingAccount): no hundo counter, count, best or answer count is lower afterwards than the higher of the two;
(f) a person's NEXT full run of a chapter is judged by the chapter as it stands: the sizes of the affected chapters on this page are the ones the
    move gives (Chapter 1 157), and the old 88-question run of Chapter 1 is a partial run (no hundo for it);
and the move is in effect on this page (Chapter 1 is 157) - which is what fails on main.
  python3 tools/check-b384-moveperm-keep.py [--against OLD/index.html]    (BASE = merge-base with origin/main; OLD_BANK=<its ifc/bank.js> with --against)"""
import os, sys, json, subprocess, ast
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def _base():   # the commit this branch was cut from (the keys to hold are the ones THIS bank started from)
    r = subprocess.run(["git", "-C", ROOT, "merge-base", "HEAD", "origin/main"], capture_output=True, text=True).stdout.strip()
    return r or "origin/main"
BASE = os.environ.get("BASE") or _base()
def _gen(name):
    for n in ast.parse(open(os.path.join(HERE, "gen-ifc-bank.py"), encoding="utf-8").read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == name: return ast.literal_eval(n.value)
MOVES = [i for i, to in _gen("UNIT_MOVES").items() if to == "1"]
REMOVED = list(_gen("UNIT_REMOVALS"))
GONE = set(MOVES) | set(REMOVED)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384moveperm_keep"}
exec(src, G)
OLD_HTML = subprocess.run(["git", "-C", ROOT, "show", BASE + ":index.html"], capture_output=True, text=True).stdout
OLD_BANK = subprocess.run(["git", "-C", ROOT, "show", BASE + ":ifc/bank.js"], capture_output=True, text=True).stdout
assert OLD_HTML and OLD_BANK, "git show %s failed" % BASE
NEW_BANK = open(os.path.join(ROOT, "ifc", "bank.js"), encoding="utf-8").read()
if "--against" in sys.argv:
    OLDX = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLDX)
    G["g"]["patched"] = _old
    if os.environ.get("OLD_BANK"): NEW_BANK = open(os.environ["OLD_BANK"], encoding="utf-8").read()
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def bank_of(js): return json.loads(js[js.index("window.IFC_BANK = ") + 18:].rstrip().rstrip(";"))
def open_class(br, html, bank, init_extra=""):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]) + init_extra)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = html((59, 0, 34, 0)) if callable(html) else html
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/ifc/bank.js*", lambda route, request, b=bank: route.fulfill(status=200, headers={"content-type": "text/javascript; charset=utf-8"}, body=b))
    import re as _re
    _m = _re.search(r'const APP_BUILD = "([^"]+)"', body)
    if _m:   # the page's own build is the one version.json names, so an older build is not sent off to update itself mid-gate
        pg.route("**/version.json*", lambda route, request, v=_m.group(1): route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": v, "force": False, "frameId": "", "safariSound": True})))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
STORE_KEY = "class26e.ifc.drill.v1"
def seed_js(fields):
    return ";(()=>{ try{ const k='%s'; const s=JSON.parse(localStorage.getItem(k)||'{}'); Object.assign(s, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % (STORE_KEY, json.dumps(fields))
ROWS = """()=>({ rows: QUESTIONS.map((q,i)=>({ id: q.ifc && q.ifc.id, key: KEYS[i], topic: q.topic, src: q.src })),
  topics: Object.fromEntries((window.IFC_BANK.units||[]).map(u => [u.id, ifcUnitTopic(u)])) })"""
# everything derived from the account, read through the app's own functions (the chapters are named by their topics)
SNAP = """(UN)=>{ const T = UN.map(t => t);
  const per = T.map(t => ({ t, perf: unitPerfectCount(t), earned: unitBadgeEarned(t), star: unitDrillStarEarned(t), level: unitLevel(t), size: unitQuestionCount(t),
    acc: unitAccuracyOf(t), answered: QUESTIONS.filter((q, i) => (q.topic || '').trim() === t && store.stats[KEYS[i]] && (store.stats[KEYS[i]].n || 0) > 0).length,
    nm: QUESTIONS.reduce((a, q, i) => (q.topic || '').trim() === t && store.stats[KEYS[i]] ? [a[0] + (store.stats[KEYS[i]].n || 0), a[1] + (store.stats[KEYS[i]].m || 0)] : a, [0, 0]) }));
  let ring = 0; [...new Set(KEYS)].forEach(k => { const st = store.stats && store.stats[k]; if(st && (Number(st.n) || 0) > (Number(st.m) || 0)) ring++; });
  const strip = o => { const c = JSON.parse(JSON.stringify(o)); delete c.stats; delete c.flagged; delete c.unflagged; delete c.lastModified; delete c.badgeScenePlayed; delete c.badgeSceneOwed; delete c.rankFloor; return c; };   /* 384.70: 384.50 defaults the scene fields to {} (nothing owed); 384.60 raises rankFloor to the rank held on the old Fire Code ladder (the rank itself is compared below) */
  let row = null; try{ row = JSON.parse(JSON.stringify(buildLeaderboardRow())); delete row.at; delete row.updatedAt; delete row.ts; delete row.lastModified; delete row.seenAt; delete row.rankFloor; }catch(e){ row = String(e); }
  let rank = null; try{ rank = JSON.stringify(rankOf(store)); }catch(e){ rank = String(e); }
  let lvl = null; try{ lvl = JSON.stringify(levelProgress(store.lifetime.points)); }catch(e){ lvl = null; }
  let pend = null; try{ const p = pendingHomeUnlocks(); pend = { owed: homeUnlocksOwed(p), n: [p.chars.length, p.banners.length, (p.hints||[]).length, (p.fx||[]).length, (p.finds||[]).length] }; }catch(e){ pend = String(e); }
  return { rest: strip(store), per, ring, badges: badgesEarnedList(), badgeCount: badgeCountOf(store), hundos: hundosOf(store), row, rank, lvl, pend,
    pending: JSON.parse(JSON.stringify(store.pendingBadgeUnlocks || [])), classTopicsN: classTopics().length,
    overlay: !!document.querySelector('.cutscene, .tier-cutscene, .badge-cutscene, .unlock-card, .rankup, #tour-overlay'),
    stats: JSON.parse(JSON.stringify(store.stats)) }; }"""
CASE = """()=>{ showRanksScreen('badges'); return new Promise(r => setTimeout(() => r({ tiles: [...document.querySelectorAll('#stage .badge-tile')].map(c => ({ label: c.getAttribute('aria-label') || '', earned: c.classList.contains('is-earned') })),
  card: document.querySelector('#stage')?.innerText.slice(0, 600) }), 2500)); }"""
FULL = """(t)=>{ cfg.mode = 'drill'; cfg.units = [t]; const idx = []; QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === t && inWholeUnit(q)) idx.push(i); }); order = idx.slice(0, 88); const r88 = isFullUnitRun(); order = idx.slice(); return { r88, rfull: isFullUnitRun(), n: idx.length }; }"""
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    IR = G["g"]["INSET_RE"]
    old_body = IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], OLD_HTML)
    # phase A: the old app's keys
    ctx, pg, e = open_class(br, old_body, OLD_BANK)
    A = pg.evaluate(ROWS); ctx.close()
    keyof = {r["id"]: r["key"] for r in A["rows"]}
    topic_of = {r["id"]: r["topic"] for r in A["rows"]}
    UNITS = ["1"] + sorted({next(u for u, t in A["topics"].items() if t == topic_of[i]) for i in GONE} - {"1"}, key=lambda u: (len(u) > 2, int(u) if u.isdigit() else 0, u))
    topics = [A["topics"][u] for u in UNITS]
    in_unit = {u: [r for r in A["rows"] if r["topic"] == A["topics"][u] and r["id"] not in GONE] for u in UNITS}
    stats = {}
    for i in GONE: stats[keyof[i]] = {"n": 6, "m": 2, "r": [1790000000001, 1790000000002]}              # the moved AND the removed questions answered (and missed twice)
    for u in UNITS:                                                                                         # partly answered chapters: a third of each, some missed
        for j, r in enumerate(in_unit[u][: max(3, len(in_unit[u]) // 3)]): stats[r["key"]] = {"n": 2 + j % 3, "m": j % 2, "r": []}
    perf = {A["topics"][u]: (1 if u != "12" else 4) for u in UNITS}                                         # the badge in every affected chapter, a hundo count beyond it in one
    perf[A["topics"]["10"]] = 2
    fields = {"unitPerfects": perf, "stats": stats, "pendingBadgeUnlocks": [], "unitBestPct": {t: 100 for t in topics}, "unitRuns": {t: 5 for t in topics},
              "flagged": {keyof[MOVES[0]]: 1790000000100, keyof[REMOVED[0]]: 1790000000150, in_unit["12"][0]["key"]: 1790000000200}}
    fields["lifetime"] = {"points": 52000, "perfectTests": 9, "answered": 900, "correct": 700}
    # phase B: the old app with that account
    ctx, pg, e = open_class(br, old_body, OLD_BANK, seed_js(fields))
    pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
    before = pg.evaluate(SNAP, topics)
    saved = pg.evaluate("()=>JSON.parse(JSON.stringify(store))")
    errs_all += e; ctx.close()
    # phase C: this build, on exactly that saved state
    ctx, pg, e = open_class(br, G["g"]["patched"], NEW_BANK, seed_js(saved))
    pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
    after = pg.evaluate(SNAP, topics)
    case = pg.evaluate(CASE)
    full = pg.evaluate(FULL, A["topics"]["1"])
    # phase D: two devices of one account, merged either way, on this build's functions
    merged = pg.evaluate("""(args)=>{ const a = args.a, b = args.b; const C = o => JSON.parse(JSON.stringify(o));
      const nums = o => { const out = {}; const walk = (p, v) => { if(typeof v === 'number') out[p] = v; else if(v && typeof v === 'object' && !Array.isArray(v)) Object.keys(v).forEach(k => walk(p + '/' + k, v[k])); };
        walk('perf', o.unitPerfects || {}); walk('life', o.lifetime || {}); walk('best', o.unitBestPct || {}); walk('runs', o.unitRuns || {});
        Object.keys(o.stats || {}).forEach(k => { out['n:' + k] = (o.stats[k] || {}).n || 0; out['m:' + k] = (o.stats[k] || {}).m || 0; }); return out; };
      const lower = (m, x, y) => { const ex = nums(x), ey = nums(y), em = nums(m); const bad = []; Object.keys(ex).concat(Object.keys(ey)).forEach(k => { if((em[k] || 0) < Math.max(ex[k] || 0, ey[k] || 0)) bad.push(k); }); return bad; };
      const out = {};
      const d1 = C(a); mergeSameAccount(d1, C(b)); out.ab = lower(d1, a, b);
      const d2 = C(b); mergeSameAccount(d2, C(a)); out.ba = lower(d2, a, b);
      const d3 = C(d1); mergeSameAccount(d3, C(b)); mergeSameAccount(d3, C(a)); out.again = JSON.stringify(nums(d3)) === JSON.stringify(nums(d1));
      const keep = JSON.parse(JSON.stringify(store)); let add = [];
      try{ mergeLeavingAccount(C(b), ''); const na = nums(store), nk = nums(keep); Object.keys(nk).forEach(k => { if((na[k] || 0) < nk[k]) add.push(k); }); }catch(e){ add = [String(e)]; }
      out.leave = add; return out; }""", {"a": pg.evaluate("()=>JSON.parse(JSON.stringify(store))"), "b": saved})
    errs_all += e; ctx.close(); br.close()
# ---- read the results
mk = lambda s: {p["t"]: p for p in s["per"]}
B, Af = mk(before), mk(after)
held = [t for t in topics if Af[t]["earned"] and Af[t]["perf"] == before["per"][topics.index(t)]["perf"] and before["per"][topics.index(t)]["earned"]]
earned_tiles = [c["label"] for c in case["tiles"] if c["earned"]]
chk("(a) all %d affected chapters still hold the badge (%d); the badge count %s -> %s; the case on Profile draws %d earned badges, each of the %d among them" % (
    len(topics), len(held), before["badgeCount"], after["badgeCount"], len(earned_tiles), len(topics)),
    len(held) == len(topics) and set(topics) <= set(after["badges"]) and after["badgeCount"] == before["badgeCount"] >= len(topics) and
    all(any(l.startswith(t + " Badge") for l in earned_tiles) for t in topics) and len(earned_tiles) == after["badgeCount"],
    {"held": len(held), "tiles": earned_tiles[:6], "after": after["badges"][:6]})
diff = [k for k in set(before["rest"]) | set(after["rest"]) if json.dumps(before["rest"].get(k), sort_keys=True) != json.dumps(after["rest"].get(k), sort_keys=True)]
same_per = all(B[t]["perf"] == Af[t]["perf"] and B[t]["star"] == Af[t]["star"] and B[t]["level"] == Af[t]["level"] and B[t]["earned"] == Af[t]["earned"] for t in topics)
chk("(b) every stored field but the per-question answers and stars is identical (%d differ: %s); hundos %s -> %s, level %s, rank %s, the published row, unit stars and levels the same" % (
    len(diff), diff[:4], before["hundos"], after["hundos"], "same" if before["lvl"] == after["lvl"] else "CHANGED", "same" if before["rank"] == after["rank"] else "CHANGED"),
    not diff and same_per and before["hundos"] == after["hundos"] == 9 and before["lvl"] == after["lvl"] and before["rank"] == after["rank"] and before["row"] == after["row"] and before["classTopicsN"] == after["classTopicsN"],
    {"diff": diff[:5], "vals": {k: [json.dumps(before["rest"].get(k))[:200], json.dumps(after["rest"].get(k))[:200]] for k in diff[:3]}, "rowdiff": [k for k in set(before["row"]) | set(after["row"]) if before["row"].get(k) != after["row"].get(k)], "lvl": [before["lvl"], after["lvl"]], "rank": [before["rank"], after["rank"]], "ct": [before["classTopicsN"], after["classTopicsN"]], "h": [before["hundos"], after["hundos"]]})
chk("(c) nothing is owed: pendingBadgeUnlocks %s -> %s, Home's pending unlocks %s -> %s, no cutscene or unlock card on the page (%s)" % (
    before["pending"], after["pending"], before["pend"], after["pend"], after["overlay"]),
    after["pending"] == [] and before["pending"] == [] and after["pend"] == before["pend"] and not after["overlay"], {"pend": after["pend"], "overlay": after["overlay"]})
# (d) the answer counts
tot = lambda s: [sum(p["nm"][0] for p in s["per"]), sum(p["nm"][1] for p in s["per"])]
ans_b, ans_a = sum(p["answered"] for p in before["per"]), sum(p["answered"] for p in after["per"])
held_by_removed = [stats[keyof[i]] for i in REMOVED]
rem_n = sum(s["n"] for s in held_by_removed); rem_m = sum(s["m"] for s in held_by_removed)
rem_ring = sum(1 for s in held_by_removed if s["n"] > s["m"])
old_left = all(json.dumps(after["stats"].get(k), sort_keys=True) == json.dumps(v, sort_keys=True) for k, v in stats.items())
lowered = [k for k, v in stats.items() if (after["stats"].get(k) or {}).get("n", 0) < v["n"] or (after["stats"].get(k) or {}).get("m", 0) < v["m"]]
ch1b, ch1a = B[A["topics"]["1"]], Af[A["topics"]["1"]]
chk("(d) every stored tally is still there and none is lower (%d entries, %d lowered); answered-at-least-once over the %d chapters %d -> %d (the removed ones held %d); right/wrong totals %s -> %s (they held %s); the Stats ring's answered-right count %d -> %d (they held %d); Chapter 1 answered %d -> %d (+%d moved answered)" % (
    len(stats), len(lowered), len(topics), ans_b, ans_a, len(REMOVED), tot(before), tot(after), [rem_n, rem_m], before["ring"], after["ring"], rem_ring,
    ch1b["answered"], ch1a["answered"], len(MOVES)),
    old_left and not lowered and ans_a == ans_b - len(REMOVED) and tot(after) == [tot(before)[0] - rem_n, tot(before)[1] - rem_m] and after["ring"] == before["ring"] - rem_ring
    and ch1a["answered"] == ch1b["answered"] + len(MOVES) and len(after["stats"]) >= len(before["stats"]) + len(MOVES),
    {"lowered": lowered[:3], "old_left": old_left, "per": [(t[:12], B[t]["answered"], Af[t]["answered"]) for t in topics[:6]]})
chk("(e) two devices of one account (old bank, new bank), merged either way: nothing lower than the higher of the two (%s, %s), merging again changes nothing (%s); adding the other account in lowers nothing (%s)" % (
    merged["ab"][:2], merged["ba"][:2], merged["again"], merged["leave"][:2]), not merged["ab"] and not merged["ba"] and merged["again"] and not merged["leave"], merged)
chk("(f) the sizes of the affected chapters on this page are the bank's (Chapter 1 %s); a run of Chapter 1's old 88 is no longer the whole chapter (88 of %s -> full run? %s; all %s -> %s)" % (
    Af[A["topics"]["1"]]["size"], full["n"], full["r88"], full["n"], full["rfull"]),
    Af[A["topics"]["1"]]["size"] == full["n"] == 157 and full["r88"] is False and full["rfull"] is True, {"sizes": [(t[:10], Af[t]["size"]) for t in topics[:6]], "full": full})
chk("no page errors (%s)" % errs_all[:2], not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
