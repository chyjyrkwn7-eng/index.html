#!/usr/bin/env python3
"""Build 384.42: one Fire Code question moved from Chapter 12 to Chapter 4, and no one's progress on any other question moves.

The owner's decision: ch12-012 ("In Harris County, a Group I-1 assisted living fire safety and evacuation plan must outline how
backup power is provided within _____ of a power loss.", C, 3 hours, county 403.7.1.1 - Chapter 4's Fire safety and evacuation plan)
moves to Chapter 4. Nothing else moves; its wording, options, answer, explanation, citation and highlight stay word for word.
A question's key is chapter | position in the chapter | hash(wording + choices), so the move changes THIS question's key and must change
no other (the questions after it in Chapter 12 would otherwise all shift up by one). Everything is read off the page, in Fire Code,
for the app and bank on origin/main (BASE) and for this build:
(1) THE QUESTION: in Chapter 4 and not in Chapter 12; in the bank file and as the app shows it, its question, options, answer,
    explanation, citation and every other field byte-identical to main's (only `unit` differs); the id is unchanged;
(2) THE IDENTITY GUARANTEE: for every other question in the 1,812-question bank, the app's own key (KEYS) is identical on main and
    here (1,811 of 1,811 - none moves), the moved question's key is the only one that changes, and every key is unique;
(3) ORDER: the moved question is the LAST in Chapter 4's order (position 41, the one after every other Chapter 4 position), and
    Chapter 12 has the gap (its positions are main's, without the first), every other question's position the same as on main;
(4) THE COUNTS: Chapter 4 reads 40 questions and Chapter 12 43 - the bank's own unit sizes, the app's unitQuestionCount (what a
    full-chapter run must cover, isFullUnitRun) and the "N questions" on the chapter cards; the bank's 1,812 unchanged; the bank
    file's other questions in the same order as main's, every other unit untouched;
(5) A STAR on the moved question goes with it (new key, same stamp; the old key gets the tombstone a Reset leaves), a star on any
    other question stays;
(6) no page errors.
(5) etc. FAIL on main: run it there with  --against <main's index.html>  and  OLD_BANK=<main's ifc/bank.js>.
  python3 tools/check-b384-moveq.py [--against OLD/index.html]   (BASE=origin/main by default)"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
BASE = os.environ.get("BASE", "origin/main")
MOVED = "ch12-012"
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
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
errs_all = []
T4, T12 = "Chapter 4: Emergency Planning and Preparedness", "Chapter 12: Energy Systems"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    IR = G["g"]["INSET_RE"]
    old_body = IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], OLD_HTML)
    ctx, pg, e0 = open_class(br, old_body, OLD_BANK)
    old = pg.evaluate(READ); ctx.close()
    O = {r["id"]: r for r in old["rows"]}
    old_key = O[MOVED]["key"]
    other = [i for i in O if i not in (MOVED, "ch1-008")]
    keep_key = O["ch1-008"]["key"]; keep2 = O["ch12-002"]["key"]
    STAMP = 1790000000123
    seed = ";(()=>{ try{ const k='class26e.ifc.drill.v1'; const s=JSON.parse(localStorage.getItem(k)||'{}'); s.flagged=Object.assign({}, s.flagged||{}, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % json.dumps(
        {old_key: STAMP, keep_key: STAMP + 1, keep2: STAMP + 2})
    ctx, pg, errs = open_class(br, G["g"]["patched"], NEW_BANK, seed)
    new = pg.evaluate(READ)
    cards = pg.evaluate(CARDS)
    flags = pg.evaluate("()=>({ flagged: JSON.parse(JSON.stringify(store.flagged||{})), unflagged: JSON.parse(JSON.stringify(store.unflagged||{})) })")
    errs_all += errs; ctx.close(); br.close()
N = {r["id"]: r for r in new["rows"]}
# (1) the question
oq = {q["id"]: q for q in ob["questions"]}; nq = {q["id"]: q for q in nb["questions"]}
same_fields = {k for k in oq[MOVED] if k != "unit" and oq[MOVED][k] == nq[MOVED].get(k)} == {k for k in oq[MOVED] if k != "unit"} and set(oq[MOVED]) == set(nq[MOVED])
shown_same = all(O[MOVED][k] == N[MOVED][k] for k in ("q", "ch", "ans", "expl")) and json.loads(N[MOVED]["ifc"]) == dict(json.loads(O[MOVED]["ifc"]), unit="4")
chk("(1) %s is in Chapter 4 (was %r), not Chapter 12; bank file: every field but `unit` identical; as shown: wording, options, answer, explanation, citation identical" % (
    MOVED, O[MOVED]["topic"]), N[MOVED]["topic"] == T4 and O[MOVED]["topic"] == T12 and nq[MOVED]["unit"] == "4" and oq[MOVED]["unit"] == "12" and same_fields and shown_same,
    {"topic": N[MOVED]["topic"], "same_fields": same_fields, "shown_same": shown_same})
# (2) the identity guarantee
moved_keys = [i for i in O if i in N and O[i]["key"] != N[i]["key"]]
allk = [r["key"] for r in new["rows"]]
chk("(2) %d questions in the bank; of the other %d every key is identical on main and here (%d moved); the moved one's key changed (%s -> %s); all keys unique" % (
    len(N), len(other) + 1, len([i for i in moved_keys if i != MOVED]), old_key, N[MOVED]["key"]),
    len(N) == len(O) == 1812 and set(N) == set(O) and moved_keys == [MOVED] and len(set(allk)) == len(allk), moved_keys[:5])
# (3) order and positions
u4 = [r for r in new["rows"] if r["topic"] == T4]; u12 = [r for r in new["rows"] if r["topic"] == T12]
o4 = [r for r in old["rows"] if r["topic"] == T4]; o12 = [r for r in old["rows"] if r["topic"] == T12]
pos_same = all(O[i]["src"] == N[i]["src"] and O[i]["topic"] == N[i]["topic"] for i in O if i != MOVED)
chk("(3) last in Chapter 4 (position %s, after %s); Chapter 12's first position is now %s (main %s); every other question has main's chapter and position (%s)" % (
    N[MOVED]["src"], max(r["src"] for r in o4), u12[0]["src"], o12[0]["src"], pos_same),
    u4[-1]["id"] == MOVED and N[MOVED]["src"] == max(r["src"] for r in o4) + 1 and N[MOVED]["src"] > max(r["src"] for r in u4 if r["id"] != MOVED)
    and [r["id"] for r in u4[:-1]] == [r["id"] for r in o4] and [r["id"] for r in u12] == [r["id"] for r in o12[1:]]
    and [r["src"] for r in u12] == [r["src"] for r in o12[1:]] and u12[0]["src"] == o12[1]["src"] and pos_same,
    {"u4_last": u4[-1]["id"], "src": N[MOVED]["src"], "pos_same": pos_same})
# (4) counts
S = {s["id"]: s for s in new["sizes"]}
card = {c["name"]: c["count"] for c in cards}
bank_same = [q["id"] for q in ob["questions"] if q["id"] != MOVED] == [q["id"] for q in nb["questions"] if q["id"] != MOVED] and \
    all(oq[i] == nq[i] for i in oq if i != MOVED) and ob["meta"] == nb["meta"] and \
    all({k: v for k, v in a.items() if k != "questionCount"} == {k: v for k, v in b.items() if k != "questionCount"} for a, b in zip(ob["units"], nb["units"])) and \
    all(a["questionCount"] == b["questionCount"] for a, b in zip(ob["units"], nb["units"]) if a["id"] not in ("4", "12")) and \
    all(u["questionCount"] == sum(1 for q in nb["questions"] if q["unit"] == u["id"]) for u in nb["units"])
chk("(4) Chapter 4 reads %s (bank %s, cache %s, full run %s, card %r), Chapter 12 %s (bank %s, cache %s, full run %s, card %r); %s questions in all; the rest of the bank is main's" % (
    len(u4), S["4"]["n"], S["4"]["cache"], S["4"]["run"], card.get(T4.split(": ", 1)[1]) or card.get(T4), len(u12), S["12"]["n"], S["12"]["cache"], S["12"]["run"], card.get(T12.split(": ", 1)[1]) or card.get(T12), new["meta"]),
    len(u4) == S["4"]["n"] == S["4"]["cache"] == S["4"]["run"] == 40 and len(u12) == S["12"]["n"] == S["12"]["cache"] == S["12"]["run"] == 43 and new["meta"] == 1812
    and "40 questions" in str(card) and "43 questions" in str(card) and bank_same, {"cards": {k: v for k, v in card.items() if "Chapter 4" in k or "Chapter 12" in k or "Energy" in k or "Emergency" in k}, "bank_same": bank_same})
# (5) the star
nk = N[MOVED]["key"]
chk("(5) a star on the moved question goes to its new key with its stamp, the old key carries the tombstone; stars on other questions stay",
    flags["flagged"].get(nk) == STAMP and old_key not in flags["flagged"] and old_key in flags["unflagged"] and nk not in flags["unflagged"]
    and flags["flagged"].get(keep_key) == STAMP + 1 and flags["flagged"].get(keep2) == STAMP + 2, {"nk": flags["flagged"].get(nk), "old_flagged": old_key in flags["flagged"], "unf": old_key in flags["unflagged"]})
chk("(6) no page errors (%s)" % errs_all[:2], not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
