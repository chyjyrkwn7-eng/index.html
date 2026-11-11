#!/usr/bin/env python3
"""Build 384.47: the county permit questions move to Chapter 1; the repeats go; no one's progress on any other question moves.

The owner: "the 87 questions we are gonna take them and put them in chapter 1. However we don't want repeat questions of course ... I don't
want repeat questions and I don't want bad questions ... I want the best questions out of what we got." A test of the chapters you selected
must not show references to chapters you did not select: a question lives in the unit of the chapter whose text it cites.
The 87 are the Fire Code questions whose citation is the county's Chapter 1 (sections 101-199, source 'amendment') in a unit that is not
Chapter 1, the Finder (NAV) or Exhibit B. 72 of them move to Chapter 1 (appended after its own 88, positions 89-160, in citation order) and
15 that repeat a fact another question already asks are taken out (tools/gen-ifc-bank.py UNIT_MOVES / UNIT_REMOVALS; the reasons are in
docs/notes-archive.md, "384.47"). Wording, options, answer, explanation, citation, highlight and every id are the bank's, unchanged: only `unit`.
A question's key is chapter | position in the chapter | hash(wording + choices), so a move changes THAT question's key and must change no other.
Everything is read off the page, in Fire Code, for the app and bank on origin/main (BASE) and for this build (the app's own KEYS for both):
(1) THE QUESTIONS: each of the 72 is in unit 1 (and the unit it left no longer has it); in the bank file and as the app shows it, its question,
    options, answer, explanation, citation and every other field are byte-identical to main's (only `unit` differs); the 15 are gone from the
    bank and from the app; the ids that stay are main's;
(2) THE IDENTITY GUARANTEE: every question that STAYS keeps the key it had on main (1,725 of 1,725 here, none moves), the 72 moved ones' keys change
    (the wording hash stays), all keys are unique; IFC_MOVED_KEYS holds each moved question's old key, IFC_RETIRED_KEYS each removed one's,
    IFC_SRC_GAPS each old position;
(3) ORDER: the 72 are at the END of Chapter 1 in the table's order (89-160), Chapter 1's own 88 keep their positions, each old chapter keeps
    every other question's position (the moved/removed one's number stays taken), every other question has main's chapter and position;
(4) THE COUNTS: every unit's size is what the table says (main's size, less what left it, plus what came in); Chapter 1 160, the bank 1,797 -
    the bank's own unit sizes, unitQuestionCount (what a full-chapter run must cover, isFullUnitRun), a full-chapter question count and the "N
    questions" on the chapter cards all agree; a run of Chapter 1's old 88 is no longer the chapter;
(5) STARS: a star on a moved question goes with it (new key, same stamp, the old key gets the tombstone), a star on a removed question comes off
    once (tombstone), a star on any other question stays;
(6) CHAPTER PURITY: no question in a unit other than Chapter 1, the Finder and Exhibit B cites the county's Chapter 1 any more (87 on main),
    every moved question cites a 1xx section; and the remaining questions whose citation is outside their unit's own chapter are LISTED;
(7) no page errors.
(1)-(6) FAIL on main: run it there with  --against <main's index.html>  and  OLD_BANK=<main's ifc/bank.js>.
  python3 tools/check-b384-moveperm.py [--against OLD/index.html]   (BASE = the merge-base with origin/main by default)"""
import os, sys, json, re, ast, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def _base():   # the commit this branch was cut from (origin/main moves as other branches merge; the keys to hold are the ones THIS bank started from)
    r = subprocess.run(["git", "-C", ROOT, "merge-base", "HEAD", "origin/main"], capture_output=True, text=True).stdout.strip()
    return r or "origin/main"
BASE = os.environ.get("BASE") or _base()
def _gen(name):   # the owner's table, read from the generator's own file
    for n in ast.parse(open(os.path.join(HERE, "gen-ifc-bank.py"), encoding="utf-8").read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == name: return ast.literal_eval(n.value)
FIVE = ["ch12-012", "ch55-702", "ch62-702", "ch62-703", "ch64-001"]                 # 384.42: already on main
MOVES = [i for i, to in _gen("UNIT_MOVES").items() if to == "1"]                    # the 72, in the order the generator appends them
REMOVED = list(_gen("UNIT_REMOVALS"))                                               # the 15
assert len(MOVES) == 72 and len(REMOVED) == 15
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384moveperm"}
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
READ = """()=>({ cls: window.NOVA_CLASS, rows: QUESTIONS.map((q,i)=>({ id: q.ifc && q.ifc.id, key: KEYS[i], topic: q.topic, src: q.src, q: q.q, ch: q.choices,
  ans: q.answer, expl: q.explanation, ifc: JSON.stringify(q.ifc) })),
  sizes: (window.IFC_BANK.units||[]).map(u=>({ id: u.id, topic: ifcUnitTopic(u), n: u.questionCount, cache: unitQuestionCount(ifcUnitTopic(u)),
    run: QUESTIONS.filter(q => (q.topic || '').trim() === ifcUnitTopic(u) && inWholeUnit(q)).length })), meta: window.IFC_BANK.meta.questionCount,
  tables: { moved: typeof IFC_MOVED_KEYS !== 'undefined' ? IFC_MOVED_KEYS : null, retired: typeof IFC_RETIRED_KEYS !== 'undefined' ? IFC_RETIRED_KEYS : null, gaps: typeof IFC_SRC_GAPS !== 'undefined' ? IFC_SRC_GAPS : null } })"""
CARDS = """()=>{ cfg.mode = 'drill'; cfg.units = []; showSetup(); return new Promise(r => setTimeout(() => r([...document.querySelectorAll('.picks > label.pick')].map(c => ({
  name: c.querySelector('.pname') && c.querySelector('.pname').textContent, count: c.querySelector('.pcount') && c.querySelector('.pcount').textContent }))), 1200)); }"""
OLDRUN = """(args)=>{ const t = args.t, n = args.n; cfg.mode = 'drill'; cfg.units = [t]; const idx = []; QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === t && inWholeUnit(q)) idx.push(i); });
  order = idx.slice(0, n); const part = isFullUnitRun(); order = idx.slice(); return { part, full: isFullUnitRun(), n: idx.length }; }"""
ob, nb = bank_of(OLD_BANK), bank_of(NEW_BANK)
oq = {q["id"]: q for q in ob["questions"]}; nq = {q["id"]: q for q in nb["questions"]}
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    IR = G["g"]["INSET_RE"]
    old_body = IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], OLD_HTML)
    ctx, pg, e0 = open_class(br, old_body, OLD_BANK)
    old = pg.evaluate(READ); ctx.close()
    O = {r["id"]: r for r in old["rows"]}
    STAMP = 1790000000123
    stars = {O[i]["key"]: STAMP + n for n, i in enumerate(MOVES + REMOVED)}               # a star on every moved and every removed question
    keep = {O["ch1-008"]["key"]: STAMP + 500, O["ch12-002"]["key"]: STAMP + 501, O["ch57-007"]["key"]: STAMP + 502, O["ch53-001"]["key"]: STAMP + 503}
    seed = ";(()=>{ try{ const k='class26e.ifc.drill.v1'; const s=JSON.parse(localStorage.getItem(k)||'{}'); s.flagged=Object.assign({}, s.flagged||{}, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % json.dumps(dict(stars, **keep))
    ctx, pg, errs = open_class(br, G["g"]["patched"], NEW_BANK, seed)
    new = pg.evaluate(READ)
    cards = pg.evaluate(CARDS)
    flags = pg.evaluate("()=>({ flagged: JSON.parse(JSON.stringify(store.flagged||{})), unflagged: JSON.parse(JSON.stringify(store.unflagged||{})) })")
    ch1_topic = next(s["topic"] for s in new["sizes"] if s["id"] == "1")
    oldrun = pg.evaluate(OLDRUN, {"t": ch1_topic, "n": len(oq) and sum(1 for q in ob["questions"] if q["unit"] == "1")})
    errs_all += errs; ctx.close(); br.close()
N = {r["id"]: r for r in new["rows"]}
topic_of_unit = {s["id"]: s["topic"] for s in new["sizes"]}
# (1) the questions
bad1 = []
for i in MOVES:
    same_fields = i in nq and set(oq[i]) == set(nq[i]) and all(oq[i][k] == nq[i][k] for k in oq[i] if k != "unit")
    shown_same = i in N and all(O[i][k] == N[i][k] for k in ("q", "ch", "ans", "expl")) and json.loads(N[i]["ifc"]) == dict(json.loads(O[i]["ifc"]), unit="1")
    if not (i in N and N[i]["topic"] == topic_of_unit["1"] and O[i]["topic"] != N[i]["topic"] and nq[i]["unit"] == "1" and oq[i]["unit"] != "1" and same_fields and shown_same):
        bad1.append((i, N.get(i, {}).get("topic"), same_fields, shown_same))
gone_bad = [i for i in REMOVED if i in nq or i in N]
others_same = all(oq[i] == nq[i] for i in oq if i not in MOVES and i not in REMOVED and i in nq) and set(nq) == set(oq) - set(REMOVED)
chk("(1) %d questions each in Chapter 1 and not their old chapter; bank file: every field but `unit` identical; as shown: wording, options, answer, explanation, citation identical; %d removed ones gone from bank and app; every other question is main's word for word" % (len(MOVES), len(REMOVED)),
    not bad1 and not gone_bad and others_same, {"bad1": bad1[:4], "gone": gone_bad[:4], "others_same": others_same})
# (2) the identity guarantee
moved_keys = sorted(i for i in O if i in N and O[i]["key"] != N[i]["key"])
allk = [r["key"] for r in new["rows"]]
stay = [i for i in N if i in O and i not in MOVES]
same_wording_hash = all(O[i]["key"].split("|")[-1] == N[i]["key"].split("|")[-1] for i in MOVES if i in N)
tab = new["tables"]
mk = {m[1]: m[0] for m in (tab["moved"] or [])}
moved_tab_ok = all(mk.get(i) == O[i]["key"] for i in MOVES)
ret_ok = all(O[i]["key"] in (tab["retired"] or []) for i in REMOVED)
gaps_ok = all(O[i]["src"] in ((tab["gaps"] or {}).get(O[i]["topic"] and next(u for u, t in topic_of_unit.items() if t == O[i]["topic"]), [])) for i in MOVES + REMOVED)
chk("(2) %d questions here; of the %d that stay every key is identical on main and here (%d of %d); the %d moved keys changed (wording hash kept: %s); all keys unique; IFC_MOVED_KEYS (%s), IFC_RETIRED_KEYS (%s), IFC_SRC_GAPS (%s) hold the old keys and positions" % (
    len(N), len(stay), sum(1 for i in stay if O[i]["key"] == N[i]["key"]), len(stay), len(moved_keys), same_wording_hash, moved_tab_ok, ret_ok, gaps_ok),
    len(stay) == 1725 and all(O[i]["key"] == N[i]["key"] for i in stay) and moved_keys == sorted(MOVES) and same_wording_hash and len(set(allk)) == len(allk) and moved_tab_ok and ret_ok and gaps_ok,
    {"moved_keys": len(moved_keys), "stay": len(stay), "tab": [moved_tab_ok, ret_ok, gaps_ok]})
# (3) order and positions
def rows(R, t): return [r for r in R if r["topic"] == t]
t1 = topic_of_unit["1"]
was1 = rows(old["rows"], t1); now1 = rows(new["rows"], t1)
ok3a = [r["id"] for r in now1[:len(was1)]] == [r["id"] for r in was1] and [r["id"] for r in now1[len(was1):]] == MOVES \
    and [N[i]["src"] for i in MOVES] == list(range(len(was1) + 1, len(was1) + 1 + len(MOVES))) and all(N[r["id"]]["src"] == r["src"] for r in was1)
GONE = set(MOVES) | set(REMOVED)
bad3 = []
for fr in sorted({O[i]["topic"] for i in GONE}):
    was = rows(old["rows"], fr); now = rows(new["rows"], fr)
    if not ([r["id"] for r in now] == [r["id"] for r in was if r["id"] not in GONE] and all(N[r["id"]]["src"] == r["src"] for r in now)): bad3.append(fr)
pos_same = all(O[i]["src"] == N[i]["src"] and O[i]["topic"] == N[i]["topic"] for i in O if i not in GONE)
chk("(3) the %d are last in Chapter 1 in the table's order (%d..%d), Chapter 1's own %d keep their positions; the %d chapters they left keep every other question's position (%s); every other question has main's chapter and position (%s)" % (
    len(MOVES), len(was1) + 1, len(was1) + len(MOVES), len(was1), len({O[i]['topic'] for i in GONE}) , bad3 or "yes", pos_same), ok3a and not bad3 and pos_same, {"ok3a": ok3a, "bad3": bad3})
# (4) counts
S = {s["id"]: s for s in new["sizes"]}
card = {c["name"]: c["count"] for c in cards}
card_for = lambda t: next((v for k, v in card.items() if k and (k == t or k == t.split(": ", 1)[-1])), None)
EXPECT = {}
for u in ob["units"]:
    EXPECT[u["id"]] = sum(1 for q in ob["questions"] if q["unit"] == u["id"] and q["id"] not in GONE)
EXPECT["1"] += len(MOVES)
bad4 = {u: (S[u]["n"], S[u]["cache"], S[u]["run"], len(rows(new["rows"], S[u]["topic"])), card_for(S[u]["topic"])) for u, n in EXPECT.items()
        if not (S[u]["n"] == S[u]["cache"] == S[u]["run"] == len(rows(new["rows"], S[u]["topic"])) == n and (card_for(S[u]["topic"]) in (None, "%d questions" % n)))}
bank_same = {k: v for k, v in ob["meta"].items() if k != "questionCount"} == {k: v for k, v in nb["meta"].items() if k != "questionCount"} and \
    all({k: v for k, v in a.items() if k != "questionCount"} == {k: v for k, v in b.items() if k != "questionCount"} for a, b in zip(ob["units"], nb["units"])) and \
    all(u["questionCount"] == sum(1 for q in nb["questions"] if q["unit"] == u["id"]) for u in nb["units"])
chk("(4) Chapter 1 %d (bank, unitQuestionCount, a full run, its card %s); every unit = main's size less what left it plus what came in; %s questions in all (the bank's own count; main %d); a run of Chapter 1's old 88 is no longer the whole chapter (isFullUnitRun on 88 of 160 -> %s)" % (
    S["1"]["n"], card_for(t1), new["meta"], old["meta"], oldrun), not bad4 and S["1"]["n"] == 160 and new["meta"] == 1797 and bank_same and oldrun["part"] is False and oldrun["full"] is True,
    {"bad": bad4, "bank_same": bank_same, "oldrun": oldrun})
# (5) the stars
bad5 = []
for i in MOVES:
    nk, ok_ = N[i]["key"], O[i]["key"]
    if not (nk in flags["flagged"] and flags["flagged"][nk] == stars[ok_] and ok_ not in flags["flagged"] and ok_ in flags["unflagged"] and nk not in flags["unflagged"]): bad5.append(i)
bad5r = [i for i in REMOVED if not (O[i]["key"] not in flags["flagged"] and O[i]["key"] in flags["unflagged"])]
chk("(5) a star on each of the %d moved questions goes to its new key with its stamp (old key tombstoned); a star on each of the %d removed comes off once; stars on other questions stay" % (len(MOVES), len(REMOVED)),
    not bad5 and not bad5r and all(flags["flagged"].get(k) == v for k, v in keep.items()), {"moved": bad5[:4], "removed": bad5r[:4]})
# (6) chapter purity
def chapter_of(sec):
    s = re.sub(r"^(Table|Figure)\s+", "", str(sec or "").strip())
    m = re.match(r"^([A-I])\d", s)
    if m: return "App" + m.group(1)
    m = re.match(r"^(\d+)", s)
    if not m: return None
    n = int(m.group(1)); return str(n if n < 100 else n // 100)
def county_ch1(q): c = q["citation"]; return c.get("source") == "amendment" and re.match(r"^1\d\d(\.|$)", str(c.get("section") or "")) is not None
outside = [q["id"] for q in nb["questions"] if q["unit"] not in ("1", "NAV", "ExhB") and county_ch1(q)]
was_outside = [q["id"] for q in ob["questions"] if q["unit"] not in ("1", "NAV", "ExhB") and county_ch1(q)]
mis = [(q["id"], q["unit"], q["citation"].get("section"), chapter_of(q["citation"].get("section"))) for q in nb["questions"] if q["unit"] not in ("NAV", "ExhB") and chapter_of(q["citation"].get("section")) not in (None, q["unit"])]
mov_ok = all(i in nq and nq[i]["unit"] == "1" and county_ch1(nq[i]) for i in MOVES)
nav_exb = {u: sum(1 for q in nb["questions"] if q["unit"] == u) for u in ("NAV", "ExhB")}
chk("(6) no question outside Chapter 1, the Finder and Exhibit B cites the county's Chapter 1 any more (%d here, %d on main); the %d moved ones all cite 1xx; every other question's unit is its citation's chapter (%d exceptions: %s); left out by design: the Finder (%d) and Exhibit B (%d)" % (
    len(outside), len(was_outside), len(MOVES), len(mis), mis[:6], nav_exb["NAV"], nav_exb["ExhB"]), not outside and mov_ok and len(was_outside) == 87 and not mis, {"outside": outside[:5], "mis": mis[:5]})
chk("(7) no page errors (%s)" % errs_all[:2], not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
