#!/usr/bin/env python3
"""Build 384.42: five Fire Code questions moved to another chapter, and no one's progress on any other question moves.

The owner's decisions: ch12-012 ("In Harris County, a Group I-1 assisted living fire safety and evacuation plan must outline how
backup power is provided within _____ of a power loss.", county 403.7.1.1 - Chapter 4's Fire safety and evacuation plan) moves from
Chapter 12 to Chapter 4; and, "we aren't gonna study chapter 9 and get references to chapter 2" (a chapter's questions cite that
chapter's own), four questions that ask a fact from a definition move to Chapter 2: ch55-702 (Cryogenic Fluids), ch62-702 and
ch62-703 (Organic Peroxides), ch64-001 (Pyrophoric Materials). Nothing else moves (the county permit questions stay); each one's
wording, options, answer, explanation, citation and highlight stay word for word, and its id.
A question's key is chapter | position in the chapter | hash(wording + choices), so a move changes THAT question's key and must change
no other (the questions after it in its old chapter would otherwise all shift up). Everything is read off the page, in Fire Code, for
the app and bank on origin/main (BASE) and for this build:
(1) THE QUESTIONS: each in its new chapter and not its old; in the bank file and as the app shows it, its question, options, answer,
    explanation, citation and every other field byte-identical to main's (only `unit` differs); ids unchanged;
(2) THE IDENTITY GUARANTEE: for every other question in the 1,812-question bank, the app's own key (KEYS) is identical on main and
    here (1,807 of 1,807 - none moves), the five moved questions' keys are the only ones that change, and every key is unique;
(3) ORDER: each moved question is at the END of its new chapter, after every question that was there (Chapter 4: 41; Chapter 2:
    108-111 in the order listed), and its old chapter has the gap (the others' positions are main's), every other question's
    position the same as on main;
(4) THE COUNTS: Chapter 2 111, Chapter 4 40, Chapter 12 43, Chapter 55 16, Chapter 62 10, Chapter 64 10 - the bank's own unit sizes,
    the app's unitQuestionCount (what a full-chapter run must cover, isFullUnitRun), a full-chapter question count and the "N
    questions" on the chapter cards; the bank's 1,812 unchanged; the bank file's other questions in the same order as main's, every
    other unit and the meta untouched;
(5) A STAR on a moved question goes with it (new key, same stamp; the old key gets the tombstone a Reset leaves), a star on any other
    question stays;
(6) no page errors.
(1)-(5) FAIL on main: run it there with  --against <main's index.html>  and  OLD_BANK=<main's ifc/bank.js>.
Adding a move later: one line in MOVES here, and UNIT_MOVES / IFC_SRC_GAPS / IFC_MOVED_KEYS (see tools/gen-ifc-bank.py).
  python3 tools/check-b384-moveq.py [--against OLD/index.html]   (BASE=origin/main by default)"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
BASE = os.environ.get("BASE", "origin/main")
# id -> the unit id it moves to, in the order the generator appends them
MOVES = {"ch12-012": "4", "ch55-702": "2", "ch62-702": "2", "ch62-703": "2", "ch64-001": "2"}
EXPECT = {"2": 111, "4": 40, "12": 43, "55": 16, "62": 10, "64": 10}      # the owner's numbers
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384moveq"}
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
def bank_of(js): return json.loads(js[js.index("window.IFC_BANK = ") + 18:].rstrip().rstrip(";"))
def open_class(br, html, bank, init_extra=""):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]) + init_extra)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = html((59, 0, 34, 0)) if callable(html) else html
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/ifc/bank.js*", lambda route, request, b=bank: route.fulfill(status=200, headers={"content-type": "text/javascript; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
READ = """()=>({ cls: window.NOVA_CLASS, rows: QUESTIONS.map((q,i)=>({ id: q.ifc && q.ifc.id, key: KEYS[i], topic: q.topic, src: q.src, q: q.q, ch: q.choices,
  ans: q.answer, expl: q.explanation, ifc: JSON.stringify(q.ifc) })),
  sizes: (window.IFC_BANK.units||[]).map(u=>({ id: u.id, topic: ifcUnitTopic(u), n: u.questionCount, cache: unitQuestionCount(ifcUnitTopic(u)),
    run: QUESTIONS.filter(q => (q.topic || '').trim() === ifcUnitTopic(u) && inWholeUnit(q)).length })), meta: window.IFC_BANK.meta.questionCount })"""
CARDS = """()=>{ cfg.mode = 'drill'; cfg.units = []; showSetup(); return new Promise(r => setTimeout(() => r([...document.querySelectorAll('.picks > label.pick')].map(c => ({
  name: c.querySelector('.pname') && c.querySelector('.pname').textContent, count: c.querySelector('.pcount') && c.querySelector('.pcount').textContent }))), 1200)); }"""
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
    old_keys = {i: O[i]["key"] for i in MOVES}
    STAMP = 1790000000123
    stars = {old_keys[i]: STAMP + n for n, i in enumerate(MOVES)}                      # a star on every moved question
    keep = {O["ch1-008"]["key"]: STAMP + 50, O["ch12-002"]["key"]: STAMP + 51, O["ch2-001"]["key"] if "ch2-001" in O else O["ch1-303"]["key"]: STAMP + 52}
    seed = ";(()=>{ try{ const k='class26e.ifc.drill.v1'; const s=JSON.parse(localStorage.getItem(k)||'{}'); s.flagged=Object.assign({}, s.flagged||{}, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % json.dumps(dict(stars, **keep))
    ctx, pg, errs = open_class(br, G["g"]["patched"], NEW_BANK, seed)
    new = pg.evaluate(READ)
    cards = pg.evaluate(CARDS)
    flags = pg.evaluate("()=>({ flagged: JSON.parse(JSON.stringify(store.flagged||{})), unflagged: JSON.parse(JSON.stringify(store.unflagged||{})) })")
    errs_all += errs; ctx.close(); br.close()
N = {r["id"]: r for r in new["rows"]}
topic_of_unit = {s["id"]: s["topic"] for s in new["sizes"]}
# (1) the questions
bad1 = []
for i, to in MOVES.items():
    same_fields = set(oq[i]) == set(nq[i]) and all(oq[i][k] == nq[i][k] for k in oq[i] if k != "unit")
    shown_same = all(O[i][k] == N[i][k] for k in ("q", "ch", "ans", "expl")) and json.loads(N[i]["ifc"]) == dict(json.loads(O[i]["ifc"]), unit=to)
    if not (N[i]["topic"] == topic_of_unit[to] and O[i]["topic"] != N[i]["topic"] and nq[i]["unit"] == to and oq[i]["unit"] != to and same_fields and shown_same):
        bad1.append((i, N[i]["topic"], same_fields, shown_same))
chk("(1) %d questions each in its new chapter (%s), not its old; bank file: every field but `unit` identical; as shown: wording, options, answer, explanation, citation identical" % (
    len(MOVES), ", ".join("%s -> %s" % (i, N[i]["topic"].split(":")[0]) for i in MOVES)), not bad1, bad1)
# (2) the identity guarantee
moved_keys = sorted(i for i in O if i in N and O[i]["key"] != N[i]["key"])
allk = [r["key"] for r in new["rows"]]
chk("(2) %d questions in the bank; of the other %d every key is identical on main and here (%d moved); the %d moved ones' keys changed; all keys unique" % (
    len(N), len(N) - len(MOVES), len([i for i in moved_keys if i not in MOVES]), len(moved_keys)),
    len(N) == len(O) == 1812 and set(N) == set(O) and moved_keys == sorted(MOVES) and len(set(allk)) == len(allk), moved_keys[:8])
# (3) order and positions
def rows(R, t): return [r for r in R if r["topic"] == t]
bad3 = []
for to in sorted(set(MOVES.values())):
    t = topic_of_unit[to]; was = rows(old["rows"], t); now = rows(new["rows"], t)
    mine = [i for i in MOVES if MOVES[i] == to]
    top = max(r["src"] for r in was)
    ok3 = [r["id"] for r in now[:len(was)]] == [r["id"] for r in was] and [r["id"] for r in now[len(was):]] == mine \
        and [N[i]["src"] for i in mine] == list(range(top + 1, top + 1 + len(mine))) and all(N[r["id"]]["src"] == r["src"] for r in was)
    if not ok3: bad3.append((t, [r["id"] for r in now[len(was):]], [N[i]["src"] for i in mine], top))
for fr in sorted({O[i]["topic"] for i in MOVES}):
    was = rows(old["rows"], fr); now = rows(new["rows"], fr); gone = [r["id"] for r in was if r["id"] in MOVES]
    ok3 = [r["id"] for r in now] == [r["id"] for r in was if r["id"] not in MOVES] and all(N[r["id"]]["src"] == r["src"] for r in now)
    if not ok3: bad3.append((fr, "gap", gone))
pos_same = all(O[i]["src"] == N[i]["src"] and O[i]["topic"] == N[i]["topic"] for i in O if i not in MOVES)
chk("(3) each moved question last in its new chapter (%s); each old chapter keeps the others' positions (gaps at %s); every other question has main's chapter and position (%s)" % (
    ", ".join("%s %s" % (i, N[i]["src"]) for i in MOVES), ", ".join("%s %s" % (i, O[i]["src"]) for i in MOVES), pos_same), not bad3 and pos_same, bad3)
# (4) counts
S = {s["id"]: s for s in new["sizes"]}
card = {c["name"]: c["count"] for c in cards}
card_for = lambda t: next((v for k, v in card.items() if k and (k == t or k == t.split(": ", 1)[-1])), None)
bank_same = [q["id"] for q in ob["questions"] if q["id"] not in MOVES] == [q["id"] for q in nb["questions"] if q["id"] not in MOVES] and \
    all(oq[i] == nq[i] for i in oq if i not in MOVES) and ob["meta"] == nb["meta"] and \
    all({k: v for k, v in a.items() if k != "questionCount"} == {k: v for k, v in b.items() if k != "questionCount"} for a, b in zip(ob["units"], nb["units"])) and \
    all(a["questionCount"] == b["questionCount"] for a, b in zip(ob["units"], nb["units"]) if a["id"] not in EXPECT) and \
    all(u["questionCount"] == sum(1 for q in nb["questions"] if q["unit"] == u["id"]) for u in nb["units"])
bad4 = {u: (S[u]["n"], S[u]["cache"], S[u]["run"], len(rows(new["rows"], S[u]["topic"])), card_for(S[u]["topic"])) for u, n in EXPECT.items()
        if not (S[u]["n"] == S[u]["cache"] == S[u]["run"] == len(rows(new["rows"], S[u]["topic"])) == n and card_for(S[u]["topic"]) == "%d questions" % n)}
chk("(4) %s (bank, unitQuestionCount, a full run, the chapter card all agree); %s questions in all; the rest of the bank is main's" % (
    ", ".join("Chapter %s %d" % (u, S[u]["n"]) for u in EXPECT), new["meta"]), not bad4 and new["meta"] == 1812 and bank_same, {"bad": bad4, "bank_same": bank_same})
# (5) the stars
bad5 = []
for i in MOVES:
    nk, ok_ = N[i]["key"], old_keys[i]
    if not (nk in flags["flagged"] and flags["flagged"][nk] == stars[ok_] and ok_ not in flags["flagged"] and ok_ in flags["unflagged"] and nk not in flags["unflagged"]):
        bad5.append(i)
chk("(5) a star on each moved question goes to its new key with its stamp, the old key carries the tombstone; stars on other questions stay",
    not bad5 and all(flags["flagged"].get(k) == v for k, v in keep.items()), {"bad": bad5})
chk("(6) no page errors (%s)" % errs_all[:2], not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
