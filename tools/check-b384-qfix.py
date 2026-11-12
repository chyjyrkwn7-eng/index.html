#!/usr/bin/env python3
"""Build 384.73: the question-audit fixes (Fire Code). Madison (he/him) read the audit and said: "The 85 flagged and any other issues
mentioned in the attention document ... I need you to fix it now. If you need to change questions entirely then do that, or if you need
to remove questions entirely, do that." That lifts "questions are word for word the study guides" for these items only.

WHAT THIS BUILD CHANGES (tools/gen-ifc-bank.py: UNIT_REMOVALS + QUESTION_EDITS; index.html: IFC_SRC_GAPS, IFC_RETIRED_KEYS, IFC_KEY_TEXT,
IFC_KEY_CHOICES; ifc/bank.js; the full list with the reason for each is the build's RESOLUTIONS.md and docs/notes-archive.md, "384.73"):
  REMOVED (3, the weaker twin of a same-question pair): ch12-012 (twin ch4-001), ch55-702 (twin ch2-086), ch2-047 (twin ch1-071)
  STEM REWORDED (5): ch1-081 and ch1-612 (an article before the blank ruled out an option / made the key the odd one out), ch3-099, ch35-009,
    ch1-112 (each printed the figure that ANOTHER question asks: 50 percent, 30 feet, $200 to $500)
  OPTION REPLACED (1): ch1-040 (A "Compliance" -> "Completion": 105.3.4 lets the fire code official issue a conditional certificate of compliance)
  EXPLANATION (2): ch28-701 and chAppC-002 ("neighbouring" -> "neighboring"; chAppC-002's row beside 3,000 gpm is 350 feet, not 300)
  Everything else, in the bank and in the app, is main's.
  1,795 -> 1,792 questions; Chapter 2 111 -> 109, Chapter 4 40 -> 39, nothing else moves.

WHAT IT HOLDS (read off the page: the app's own KEYS, QUESTIONS and tables, for main's app + bank (BASE) and for this build):
 (1) THE BANK: exactly the three ids are gone (and their twins stay, byte-identical); exactly the eight edited questions differ, and only in the
     field the build says; every other question's record is byte-identical to main's; ifc/bank.js parses; meta and every unit's questionCount
     are the bank's own counts; no chapter is empty;
 (2) EACH FIX IS IN EFFECT, as shapes read off the bank (not typed labels): no stem holds `a|an _____` with an option the article rules out
     (main has exactly ch1-081 and ch1-612), the answer is the same option with the same text; ch1-040's wrong options name no certificate the
     cited text names; no stem prints the key of the question it was paired with; no explanation says "neighbour"; chAppC-002's rows either side;
 (3) IDENTITY: every one of the 1,792 questions keeps main's key (0 moves), all keys unique; each reworded stem / replaced option has the old
     text pinned (keyText / keyChoices = main's wording, so the key is main's); each removed question's position stays taken (IFC_SRC_GAPS), its key
     (and, for the two that moved in 384.42, the key it was stored under before) is in IFC_RETIRED_KEYS; the tables only grew;
 (4) COUNTS: each unit's size is main's less what left it; the bank's size, unitQuestionCount, a full-chapter run and the chapter cards agree;
     the class card reads the new total; a run of Chapter 2's / Chapter 4's old size is no longer the whole chapter;
 (5) NOTHING LOST: an account holding the badge, hundos, stats and stars (chapters 1, 2, 4) is booted on main and its saved state on this build:
     badges, hundos, level, rank, the published row and every stored field but stats/flagged are identical; no stored tally is lowered; stars on
     the removed come off once (tombstone), stars on every other question stay; nothing is owed; two devices merged either way lower nothing;
     a saved test holding a removed question is dropped (the existing notice), one holding an edited question is put back;
 (6) THE REST OF THE APP: Fire Code boots with no page errors; the academy's questions, keys and wording are identical to main's; the only lines
     of index.html that differ from main's are inside the Fire Code identity block and the build line; version.json and APP_BUILD agree.
Every check fails on main:  python3 tools/check-b384-qfix.py --against <main's index.html>  with OLD_BANK=<main's ifc/bank.js>."""
import os, sys, json, re, subprocess, difflib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import b384_qfix_lib as L

def _base():   # the commit this branch was cut from (origin/main moves as other branches merge; the keys to hold are the ones THIS bank started from)
    r = subprocess.run(["git", "-C", ROOT, "merge-base", "HEAD", "origin/main"], capture_output=True, text=True).stdout.strip()
    return r or "origin/main"
BASE = os.environ.get("BASE") or _base()
OLD_HTML = L.git_show(BASE, "index.html"); OLD_BANK = L.git_show(BASE, "ifc/bank.js"); OLD_VER = L.git_show(BASE, "version.json")
assert OLD_HTML and OLD_BANK, "git show %s failed" % BASE
NEW_HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
NEW_BANK = open(os.path.join(ROOT, "ifc", "bank.js"), encoding="utf-8").read()
NEW_VER = open(os.path.join(ROOT, "version.json"), encoding="utf-8").read()
if "--against" in sys.argv:        # "this build" is the OLD one: every check below must fail
    NEW_HTML = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    NEW_BANK = open(os.environ["OLD_BANK"], encoding="utf-8").read() if os.environ.get("OLD_BANK") else OLD_BANK
    NEW_VER = OLD_VER
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
bank_of = L.bank_of

# ---- the owner's decisions, as data (ids, not wording: the wording is read off the bank and held as shapes) ----
REMOVED = {"ch12-012": "ch4-001", "ch55-702": "ch2-086", "ch2-047": "ch1-071"}          # removed id -> the twin that stays
STEMS = ["ch1-081", "ch1-612", "ch3-099", "ch35-009", "ch1-112"]                           # stem reworded
OPT = {"ch1-040": "A"}                                                                      # one option replaced
EXPL = ["ch28-701", "chAppC-002"]                                                           # explanation only
EDITED = STEMS + list(OPT) + EXPL
LEAKS = {"ch3-099": "ch3-624", "ch35-009": "ch35-016", "ch1-112": "ch1-142"}               # the stem that printed the figure another question asks -> that question
UNIT_OF_REMOVED = {"ch12-012": "4", "ch55-702": "2", "ch2-047": "2"}
ob, nb = bank_of(OLD_BANK), bank_of(NEW_BANK)
oq = {q["id"]: q for q in ob["questions"]}; nq = {q["id"]: q for q in nb["questions"]}
KEEP_SAME = [i for i in oq if i not in REMOVED and i not in EDITED]
UNTOUCHED = [next(q["id"] for q in ob["questions"] if q["unit"] == u and q["id"] in KEEP_SAME and q["id"] not in REMOVED.values()) for u in ("1", "2", "4")]   # an ordinary question of each chapter

# ---- the page, on main's app + bank and on this build's ----
G = L.fixture(); IR = G["g"]["INSET_RE"]
def insets(h): return IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], h)
OLD_PAGE = insets(OLD_HTML); NEW_PAGE = insets(NEW_HTML)
STORE_KEY = "class26e.ifc.drill.v1"
def seed_js(fields):
    return ";(()=>{ try{ const k='%s'; const s=JSON.parse(localStorage.getItem(k)||'{}'); Object.assign(s, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % (STORE_KEY, json.dumps(fields))
CARDS = """()=>{ cfg.mode = 'drill'; cfg.units = []; showSetup(); return new Promise(r => setTimeout(() => r([...document.querySelectorAll('.picks > label.pick')].map(c => ({
  name: c.querySelector('.pname') && c.querySelector('.pname').textContent, count: c.querySelector('.pcount') && c.querySelector('.pcount').textContent }))), 1200)); }"""
FULLRUN = """(args)=>{ const t = args.t, n = args.n; cfg.mode = 'drill'; cfg.units = [t]; const idx = []; QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === t && inWholeUnit(q)) idx.push(i); });
  order = idx.slice(0, n); const part = isFullUnitRun(); order = idx.slice(); return { part, full: isFullUnitRun(), n: idx.length }; }"""
SNAP = """(UN)=>{ const T = UN.map(t => t);
  const per = T.map(t => ({ t, perf: unitPerfectCount(t), earned: unitBadgeEarned(t), star: unitDrillStarEarned(t), level: unitLevel(t), size: unitQuestionCount(t),
    answered: QUESTIONS.filter((q, i) => (q.topic || '').trim() === t && store.stats[KEYS[i]] && (store.stats[KEYS[i]].n || 0) > 0).length }));
  let ring = 0; [...new Set(KEYS)].forEach(k => { const st = store.stats && store.stats[k]; if(st && (Number(st.n) || 0) > (Number(st.m) || 0)) ring++; });
  const strip = o => { const c = JSON.parse(JSON.stringify(o)); delete c.stats; delete c.flagged; delete c.unflagged; delete c.lastModified; delete c.badgeScenePlayed; delete c.badgeSceneOwed; return c; };
  let row = null; try{ row = JSON.parse(JSON.stringify(buildLeaderboardRow())); delete row.at; delete row.updatedAt; delete row.ts; delete row.lastModified; delete row.seenAt; }catch(e){ row = String(e); }
  let rank = null; try{ rank = JSON.stringify(rankOf(store)); }catch(e){ rank = String(e); }
  let lvl = null; try{ lvl = JSON.stringify(levelProgress(store.lifetime.points)); }catch(e){ lvl = null; }
  let pend = null; try{ const p = pendingHomeUnlocks(); pend = { owed: homeUnlocksOwed(p), n: [p.chars.length, p.banners.length, (p.hints||[]).length, (p.fx||[]).length, (p.finds||[]).length] }; }catch(e){ pend = String(e); }
  return { rest: strip(store), per, ring, badges: badgesEarnedList(), badgeCount: badgeCountOf(store), hundos: hundosOf(store), row, rank, lvl, pend,
    pending: JSON.parse(JSON.stringify(store.pendingBadgeUnlocks || [])),
    flagged: JSON.parse(JSON.stringify(store.flagged || {})), unflagged: JSON.parse(JSON.stringify(store.unflagged || {})), stats: JSON.parse(JSON.stringify(store.stats)),
    overlay: !!document.querySelector('.cutscene, .tier-cutscene, .badge-cutscene, .unlock-card, .rankup, #tour-overlay') }; }"""
# a saved test, put back (or not) by the app's own function: a session holding the given keys, one shuffled layout
REMAP = """(args)=>{ const qk = {}; const order = []; args.keys.forEach((k, n) => { qk[n + 1000] = k; order.push(n + 1000); });
  const s = { v: 1, saved: true, order, qkeys: qk, pos: 0, layout: {}, attempts: {}, picked: {}, firstPick: {}, timedOutSet: {}, qTimeMs: {}, cfg: { units: [] } };
  let r = null; try{ r = remapRunSession(s); }catch(e){ return 'threw ' + e; }
  return r ? { ok: true, n: r.order.length } : { ok: false }; }"""

# =========================================================== the bank file
bad_other = [i for i in KEEP_SAME if oq[i] != nq.get(i)]
twins_same = all(oq[t] == nq.get(t) for t in REMOVED.values())
gone_ok = all(i not in nq for i in REMOVED) and set(nq) == set(oq) - set(REMOVED)
diff_fields = {i: sorted(k for k in oq[i] if oq[i][k] != nq[i][k]) for i in EDITED if i in nq}
want_fields = {**{i: ["question"] for i in STEMS}, **{i: ["options"] for i in OPT}, **{i: ["explanation"] for i in EXPL}}
opt_diff = {i: sorted(k for k in oq[i]["options"] if nq[i]["options"][k] != oq[i]["options"][k]) for i in OPT if i in nq}
ans_same = all(nq[i]["answer"] == oq[i]["answer"] and nq[i]["options"][nq[i]["answer"]] == oq[i]["options"][oq[i]["answer"]] for i in STEMS + list(OPT) if i in nq)
units_ok = all(u["questionCount"] == sum(1 for q in nb["questions"] if q["unit"] == u["id"]) for u in nb["units"]) and nb["meta"]["questionCount"] == len(nb["questions"]) \
    and all(u["questionCount"] >= 1 for u in nb["units"]) and sum(u["questionCount"] for u in nb["units"]) == len(nb["questions"])
meta_same = {k: v for k, v in ob["meta"].items() if k != "questionCount"} == {k: v for k, v in nb["meta"].items() if k != "questionCount"}
order_ok = [q["id"] for q in ob["questions"] if q["id"] in nq] == [q["id"] for q in nb["questions"]]
chk("(1) bank file: the three removed (%s) are gone and their twins (%s) are byte-identical; the %d edited questions differ only in the field the build says (%s) and keep their keyed answer; the other %d are byte-identical to main's; "
    "order, meta and every unit's questionCount are the bank's own (%d questions); no chapter is empty" % (", ".join(REMOVED), ", ".join(REMOVED.values()), len(EDITED), "stem 5, one option, explanation 2", len(KEEP_SAME), len(nb["questions"])),
    gone_ok and twins_same and not bad_other and diff_fields == want_fields and opt_diff == {i: [o] for i, o in OPT.items()} and ans_same and units_ok and meta_same and order_ok and len(nb["questions"]) == len(oq) - len(REMOVED),
    {"gone_ok": gone_ok, "twins": twins_same, "other": bad_other[:4], "fields": {i: f for i, f in diff_fields.items() if f != want_fields[i]}, "opt": opt_diff, "ans": ans_same, "units": units_ok, "order": order_ok})

# =========================================================== each fix, as shapes
def article_bad(bank):
    """stems with `a|an _____` where an option the article rules out exists (an option that cannot follow it)"""
    def vowel(s):
        w = re.split(r"[\s,/]", s.strip().strip("\"'("))[0]
        if re.match(r"^(hour|honest|heir)", w, re.I): return True
        if re.match(r"^(uni|use|usa|eu|one|once)", w, re.I): return False
        if re.match(r"^(OSHA|NFPA|FBI|SDS|MSDS)", w): return True
        if re.match(r"^(8|11|18|80)", w): return True
        return w[:1].lower() in "aeiou"
    out = []
    for q in bank["questions"]:
        m = re.search(r"\b(a|an) _____", q["question"])
        if m and not all(vowel(v) == (m.group(1) == "an") for v in q["options"].values()): out.append(q["id"])
    return out
art_new, art_old = article_bad(nb), article_bad(ob)
chk("(2a) no stem in the bank has `a|an _____` with an option that article rules out (main: %s)" % art_old, not art_new and sorted(art_old) == ["ch1-081", "ch1-612"], {"here": art_new, "main": art_old})
def one(i): return nq.get(i) or {"question": "", "options": {}, "answer": "A", "citation": {}, "explanation": ""}
q40 = one("ch1-040"); exc40 = (q40["citation"].get("excerpt") or "").lower()
wrong40 = [v for k, v in q40["options"].items() if k != q40["answer"]]
named40 = [v for v in wrong40 if ("certificate of " + v.lower()) in exc40]
chk("(2b) ch1-040: the key (%s) is still the certificate the fire code official issues, and none of the %d wrong options is a certificate the cited text names (%s)" % (
    q40["options"].get(q40["answer"]), len(wrong40), named40 or "none"), q40["options"].get(q40["answer"]) == "Inspection" and ("certificate of inspection" in exc40) and len(wrong40) == 3 and not named40, {"named": named40})
leak_bad = []
for stem_id, sib in LEAKS.items():
    sq = nq.get(sib)
    if not sq or stem_id not in nq: leak_bad.append((stem_id, "missing")); continue
    key = sq["options"][sq["answer"]]
    fig = {"ch3-624": key + " percent"}.get(sib, key)                 # the figure as the stem would print it
    if fig.lower() in nq[stem_id]["question"].lower(): leak_bad.append((stem_id, fig))
leak_bad += [("ch1-112", "ch1-609", nq["ch1-609"]["options"][nq["ch1-609"]["answer"]])] if "ch1-112" in nq and nq["ch1-609"]["options"][nq["ch1-609"]["answer"]].lower() in nq["ch1-112"]["question"].lower() else []
blanks = all("_____" in nq[i]["question"] for i in LEAKS if i in nq)
cited = all(nq[i]["options"][nq[i]["answer"]].lower() in (nq[i]["citation"].get("excerpt") or nq[i]["citation"].get("highlight") or "").lower() for i in ("ch3-099", "ch1-112") if i in nq) if blanks else False
chk("(2c) no stem prints the figure of the question it was paired with (ch3-099 / ch3-624, ch35-009 / ch35-016, ch1-112 / ch1-142 and ch1-609); each keeps its blank and its answer is still in the cited county text", not leak_bad and blanks and cited, {"leaks": leak_bad, "blanks": blanks, "cited": cited})
brit = [i for i, q in nq.items() if re.search(r"neighbour", q["question"] + " " + q["explanation"] + " ".join(q["options"].values()), re.I)]
c2 = one("chAppC-002")["explanation"]
chk("(2d) American spelling: no question or explanation in the bank says 'neighbour' (%s); chAppC-002's explanation names the rows either side of the 3,000 gpm row as 450 and 350 feet (Table C102.1: 2,251-2,750 is 450, 3,251-4,000 is 350; 300 is two rows on)" % (brit or "none"),
    not brit and "450 feet" in c2 and "350 feet" in c2 and "300 feet" not in c2 and "neighboring piles" in one("ch28-701")["explanation"], {"brit": brit, "c2": c2})

# =========================================================== the page
from playwright.sync_api import sync_playwright
errs_all = []
with sync_playwright() as pw:
    rig = L.Rig(G, pw)
    try:
        old, e0 = rig.read(OLD_PAGE, OLD_BANK)
        new, e1 = rig.read(NEW_PAGE, NEW_BANK)
        errs_all += e0 + e1
        O = {r["id"]: r for r in old["rows"]}; N = {r["id"]: r for r in new["rows"]}
        # ---- (3) identity
        allk = [r["key"] for r in new["rows"]]
        moved = [i for i in N if i in O and O[i]["key"] != N[i]["key"]]
        pins_text = {i: new["tables"]["keyText"].get(i) for i in STEMS}
        pins_ok = all(pins_text[i] == oq[i]["question"] and N.get(i, {}).get("keyText") == oq[i]["question"] for i in STEMS) and \
            all(new["tables"]["keyChoices"].get(i) == [oq[i]["options"][k] for k in "ABCD"] and N.get(i, {}).get("keyChoices") == [oq[i]["options"][k] for k in "ABCD"] for i in OPT)
        shown_new = all(N[i]["q"] == nq[i]["question"] for i in STEMS if i in N) and all(N[i]["ch"] == [nq[i]["options"][k] for k in "ABCD"] for i in OPT if i in N)
        tab, otab = new["tables"], old["tables"]
        gaps_ok = all(O[i]["src"] in (tab["gaps"].get(UNIT_OF_REMOVED[i]) or []) for i in REMOVED) and all(set(v) <= set(tab["gaps"].get(u) or []) for u, v in otab["gaps"].items())
        prev_moved = {m[1]: m[0] for m in otab["moved"]}
        ret_need = [O[i]["key"] for i in REMOVED] + [prev_moved[i] for i in REMOVED if i in prev_moved]
        ret_ok = all(k in tab["retired"] for k in ret_need) and all(k in tab["retired"] for k in otab["retired"]) and len(ret_need) == 5
        tables_grew = all(m in tab["moved"] for m in otab["moved"]) and set(otab["keyText"]) <= set(tab["keyText"]) and set(otab["keyChoices"]) <= set(tab["keyChoices"])
        chk("(3) identity: %d questions here; all %d that stay keep main's exact key (%d moved: %s); all keys unique; the %d reworded stems and %d replaced option are pinned to main's wording (so the key is main's) while the page shows the new text; "
            "each removed question's position stays taken (IFC_SRC_GAPS), its key and the key it was stored under before 384.42 are retired (%d keys); the tables only grew" % (
            len(N), len(N), len(moved), moved[:3], len(STEMS), len(OPT), len(ret_need)),
            len(N) == len(O) - len(REMOVED) and not moved and len(set(allk)) == len(allk) and pins_ok and shown_new and gaps_ok and ret_ok and tables_grew and set(N) == set(O) - set(REMOVED),
            {"moved": moved[:5], "pins": pins_ok, "shown": shown_new, "gaps": gaps_ok, "retired": ret_ok, "grew": tables_grew, "n": len(N), "uniq": len(set(allk))})
        # ---- (4) counts
        S = {s["id"]: s for s in new["sizes"]}; T = {s["id"]: s for s in old["sizes"]}
        cards = {}
        ctx, pg, errs = rig.open(NEW_PAGE, NEW_BANK)
        cards = {c["name"]: c["count"] for c in pg.evaluate(CARDS)}
        t2, t4, t1 = S["2"]["topic"], S["4"]["topic"], S["1"]["topic"]
        run2 = pg.evaluate(FULLRUN, {"t": t2, "n": S["2"]["n"] - 1})      # one question short of the chapter as it stands is not the chapter
        run4 = pg.evaluate(FULLRUN, {"t": t4, "n": S["4"]["n"] - 1})
        errs_all += errs; ctx.close()
        card_for = lambda t: next((v for k, v in cards.items() if k and (k == t or k == t.split(": ", 1)[-1])), None)
        EXPECT = {u["id"]: sum(1 for q in ob["questions"] if q["unit"] == u["id"] and q["id"] not in REMOVED) for u in ob["units"]}
        bad4 = {u: (S[u]["n"], S[u]["cache"], S[u]["run"], card_for(S[u]["topic"])) for u, n in EXPECT.items()
                if not (S[u]["n"] == S[u]["cache"] == S[u]["run"] == n and card_for(S[u]["topic"]) in (None, "%d questions" % n))}
        chk("(4) counts: Chapter 2 %s -> %s, Chapter 4 %s -> %s, Chapter 1 %s unchanged, every other chapter main's size; each is its bank count, unitQuestionCount, a full run and its card; %s questions in all (main %s; the class card reads %s); "
            "a run one short of Chapter 2 / Chapter 4 is a partial run (%s / %s); every question of each (%s / %s) is the whole chapter, so the next full run is the new size" % (
            T["2"]["n"], S["2"]["n"], T["4"]["n"], S["4"]["n"], S["1"]["n"], new["meta"], old["meta"], new["tables"]["countText"], run2["part"], run4["part"], run2["n"], run4["n"]),
            not bad4 and S["2"]["n"] == T["2"]["n"] - 2 and S["4"]["n"] == T["4"]["n"] - 1 and S["1"]["n"] == T["1"]["n"] and new["meta"] == old["meta"] - 3 and new["tables"]["countText"] == "{:,}".format(new["meta"])
            and run2["part"] is False and run2["full"] is True and run4["part"] is False and run4["full"] is True and run2["n"] == S["2"]["n"] and run4["n"] == S["4"]["n"] and min(s["n"] for s in new["sizes"]) >= 1, {"bad": bad4, "run2": run2, "run4": run4})
        # ---- (5) nothing lost
        topics = [S[u]["topic"] for u in ("1", "2", "4")]
        stats = {}
        for i in list(REMOVED) + list(REMOVED.values()) + EDITED + UNTOUCHED:
            stats[O[i]["key"]] = {"n": 5, "m": 2, "r": [1790000000001, 1790000000002]}
        for i, k in prev_moved.items():
            if i in REMOVED: stats[k] = {"n": 3, "m": 1, "r": []}              # the history still sitting under the key a 384.42-moved question had before
        STAMP = 1790000000123
        flagged = {O[i]["key"]: STAMP + n for n, i in enumerate(list(REMOVED) + list(REMOVED.values()) + EDITED + UNTOUCHED[:2])}
        for i, k in prev_moved.items():
            if i in REMOVED: flagged[k] = STAMP + 900
        perf = {t: n for t, n in zip(topics, (3, 1, 2))}
        fields = {"unitPerfects": perf, "stats": stats, "pendingBadgeUnlocks": [], "flagged": flagged, "unitBestPct": {t: 100 for t in topics}, "unitRuns": {t: 5 for t in topics},
                  "lifetime": {"points": 52000, "perfectTests": 9, "answered": 900, "correct": 700}}
        ctx, pg, e = rig.open(OLD_PAGE, OLD_BANK, seed_js(fields))
        pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
        before = pg.evaluate(SNAP, topics); saved = pg.evaluate("()=>JSON.parse(JSON.stringify(store))"); errs_all += e; ctx.close()
        ctx, pg, e = rig.open(NEW_PAGE, NEW_BANK, seed_js(saved))
        pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
        after = pg.evaluate(SNAP, topics)
        keep_keys = [N[i]["key"] for i in EDITED] + [N[i]["key"] for i in REMOVED.values()]      # edited questions and kept twins: same key, so the same history
        remap_removed = pg.evaluate(REMAP, {"keys": [O[next(iter(REMOVED))]["key"]]})
        remap_removed_mix = pg.evaluate(REMAP, {"keys": [N[UNTOUCHED[0]]["key"], O["ch2-047"]["key"]]}) if "ch2-047" in O else None
        remap_edited = pg.evaluate(REMAP, {"keys": [N[i]["key"] for i in EDITED if i in N]})
        merged = pg.evaluate("""(args)=>{ const a = args.a, b = args.b; const C = o => JSON.parse(JSON.stringify(o));
          const nums = o => { const out = {}; const walk = (p, v) => { if(typeof v === 'number') out[p] = v; else if(v && typeof v === 'object' && !Array.isArray(v)) Object.keys(v).forEach(k => walk(p + '/' + k, v[k])); };
            walk('perf', o.unitPerfects || {}); walk('life', o.lifetime || {}); walk('best', o.unitBestPct || {}); walk('runs', o.unitRuns || {});
            Object.keys(o.stats || {}).forEach(k => { out['n:' + k] = (o.stats[k] || {}).n || 0; out['m:' + k] = (o.stats[k] || {}).m || 0; }); return out; };
          const lower = (m, x, y) => { const ex = nums(x), ey = nums(y), em = nums(m); const bad = []; Object.keys(ex).concat(Object.keys(ey)).forEach(k => { if((em[k] || 0) < Math.max(ex[k] || 0, ey[k] || 0)) bad.push(k); }); return bad; };
          const d1 = C(a); mergeSameAccount(d1, C(b)); const d2 = C(b); mergeSameAccount(d2, C(a)); return { ab: lower(d1, a, b), ba: lower(d2, a, b) }; }""",
                           {"a": pg.evaluate("()=>JSON.parse(JSON.stringify(store))"), "b": saved})
        errs_all += e; ctx.close()
        Bp, Ap = {p["t"]: p for p in before["per"]}, {p["t"]: p for p in after["per"]}
        held = all(Ap[t]["perf"] == Bp[t]["perf"] and Ap[t]["earned"] == Bp[t]["earned"] and Ap[t]["star"] == Bp[t]["star"] and Ap[t]["level"] == Bp[t]["level"] for t in topics)
        rest_diff = [k for k in set(before["rest"]) | set(after["rest"]) if json.dumps(before["rest"].get(k), sort_keys=True) != json.dumps(after["rest"].get(k), sort_keys=True)]
        chk("(5a) the badge, hundos, star and level of Chapters 1, 2 and 4 are held (hundos %s -> %s, badges %s -> %s, rank and the published row the same); every stored field but the per-question answers and stars is identical (%d differ: %s); nothing is owed or re-fired" % (
            before["hundos"], after["hundos"], before["badgeCount"], after["badgeCount"], len(rest_diff), rest_diff[:4]),
            held and not rest_diff and before["hundos"] == after["hundos"] and before["badgeCount"] == after["badgeCount"] and before["rank"] == after["rank"] and before["lvl"] == after["lvl"]
            and json.dumps(before["row"], sort_keys=True) == json.dumps(after["row"], sort_keys=True) and after["pending"] == [] and before["pend"] == after["pend"] and not after["overlay"],
            {"held": held, "rest": rest_diff[:5], "hundos": [before["hundos"], after["hundos"]], "pend": [before["pend"], after["pend"]]})
        lowered = [k for k, v in before["stats"].items() if after["stats"].get(k, {}).get("n", 0) < v.get("n", 0) or after["stats"].get(k, {}).get("m", 0) < v.get("m", 0)]
        gone_ans = {t: Bp[t]["answered"] - Ap[t]["answered"] for t in topics}
        chk("(5b) no stored answer tally is lowered (%d entries, %d lowered; the removed questions' tallies stay where they are and nothing reads them); a person who had answered a removed question sees their chapter's answered figure drop by it (Chapter 1/2/4: %s) and the Stats ring by %d" % (
            len(before["stats"]), len(lowered), [gone_ans[t] for t in topics], before["ring"] - after["ring"]),
            not lowered and gone_ans[topics[0]] == 0 and gone_ans[topics[1]] == 2 and gone_ans[topics[2]] == 1 and before["ring"] - after["ring"] == 3, {"lowered": lowered[:4], "gone": gone_ans, "ring": [before["ring"], after["ring"]]})
        off = [O[i]["key"] for i in REMOVED] + [k for i, k in prev_moved.items() if i in REMOVED]
        stay = [k for k in flagged if k not in off]
        stars_ok = all(k not in after["flagged"] and k in after["unflagged"] for k in off) and all(after["flagged"].get(k) == flagged[k] for k in stay)
        chk("(5c) a star on each removed question (and on the key a moved one held before) comes off once, with the tombstone (%d keys); a star on every edited question, every kept twin and every other question stays with its stamp (%d)" % (len(off), len(stay)), stars_ok,
            {"off": [k for k in off if k in after["flagged"] or k not in after["unflagged"]][:3], "stay": [k for k in stay if after["flagged"].get(k) != flagged[k]][:3]})
        chk("(5d) two devices of one account (this bank and main's), merged either way, lower nothing (%s / %s); a saved test holding a removed question is dropped (the existing 'a question is gone' path: %s; with another question beside it: %s), "
            "one holding every edited question is put back (%s)" % (merged["ab"][:2] or "ok", merged["ba"][:2] or "ok", remap_removed, remap_removed_mix, remap_edited),
            not merged["ab"] and not merged["ba"] and remap_removed == {"ok": False} and remap_removed_mix == {"ok": False} and remap_edited == {"ok": True, "n": len(EDITED)}, {"m": merged, "r": [remap_removed, remap_removed_mix, remap_edited]})
        # ---- (6) the rest of the app
        oa, ea = rig.read(OLD_PAGE, OLD_BANK, "", "academy"); na, eb = rig.read(NEW_PAGE, NEW_BANK, "", "academy")
        errs_all += ea + eb
        same_academy = json.dumps(oa["rows"], sort_keys=True) == json.dumps(na["rows"], sort_keys=True) and len(na["rows"]) > 1000 and na["cls"] == "academy" and oa["cls"] == "academy"
        chk("(6a) the academy's %d questions, keys, wording, choices, answers and explanations are identical to main's (the class is untouched)" % len(na["rows"]), same_academy, {"n": [len(oa["rows"]), len(na["rows"])]})
    finally:
        rig.close()
# the lines of index.html that differ from main's
ol, nl = OLD_HTML.split("\n"), NEW_HTML.split("\n")
sm = difflib.SequenceMatcher(None, ol, nl, autojunk=False)
start = next(i for i, l in enumerate(nl) if l.startswith("/* ---- THE 5.4.2 BANK (build 384)"))
end = next(i for i, l in enumerate(nl) if l.startswith("const IFC_QUESTIONS = ifcQuestionsFrom"))
ostart = next(i for i, l in enumerate(ol) if l.startswith("/* ---- THE 5.4.2 BANK (build 384)"))
oend = next(i for i, l in enumerate(ol) if l.startswith("const IFC_QUESTIONS = ifcQuestionsFrom"))
outside = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal": continue
    inblock = ostart <= i1 and i2 <= oend and start <= j1 and j2 <= end
    build_line = all("APP_BUILD" in l for l in ol[i1:i2] + nl[j1:j2]) and (i2 - i1) == 1 and (j2 - j1) == 1
    if not (inblock or build_line): outside.append((i1 + 1, ol[i1:i2][:1], nl[j1:j2][:1]))
def build_of(t): return re.search(r'const APP_BUILD = "([^"]+)"', t).group(1)
vb = json.loads(NEW_VER)["build"]
chk("(6b) index.html differs from main's only inside the Fire Code identity block (the tables, lines %d-%d) and the APP_BUILD line (%d stray hunks%s); APP_BUILD %s is version.json's build %s (main: %s)" % (
    start + 1, end + 1, len(outside), (": " + str(outside[:2])[:160]) if outside else "", build_of(NEW_HTML), vb, build_of(OLD_HTML)),
    not outside and build_of(NEW_HTML) == vb and build_of(OLD_HTML) != build_of(NEW_HTML), {"outside": outside[:3]})
chk("(6c) Fire Code and the academy both boot: no page errors (%s)" % errs_all[:2], not errs_all, errs_all[:4])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
