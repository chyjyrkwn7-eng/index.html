#!/usr/bin/env python3
#!/usr/bin/env python3
"""Build 384.48, the 5.4.3 bank: ONE wrong option of ONE Fire Code question changed, and nobody's progress moves.

Madison sent class26e-ifc-update-5.4.3 ("should just be a change to a single question"): chAppH-805 (Appendix H, IFC H103.1, "Where
OSHA or state rules require a facility to have an Emergency Action Plan or Emergency Response Plan, that plan must be included as
part of the _____.") - the wrong option "operational permit application" is now "construction documents" (under IFC 5001.5.1 a permit
application can include the hazardous materials management plan, so the old one could be argued as partly right). Nothing else in
the bank changed.
A question's key includes its choices, so the change is pinned (IFC_KEY_CHOICES keeps the choices it was first stored under).
Read off the page, in Fire Code, for the app and bank on origin/main (BASE) and for this build:
(1) THE QUESTION: as the app shows it, chAppH-805 has the four options hazardous materials inventory statement / construction
    documents / site plan / hazardous materials management plan, the keyed answer is still "hazardous materials management plan", its
    wording, explanation and citation are byte-identical to main's, and "operational permit application" is gone from it;
(2) THE BANK FILE: exactly that one option differs from main's file (every other field of every question, the units and the meta);
(3) THE IDENTITY GUARANTEE: the app's own key (KEYS) of every one of the 1,812 questions, chAppH-805 included, is identical on main
    and here, and all keys are unique;
(4) A STAR on chAppH-805 (and on any other question) is kept;
(5) no page errors.
(1) and (3) FAIL on main: run it there with  --against <main's index.html>  and  OLD_BANK=<main's ifc/bank.js>.
  python3 tools/check-b384-ifc543.py [--against OLD/index.html]   (BASE = the merge-base with origin/main by default)"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
# (384.47) main holds the 5.4.3 change now, so the commit to compare with is the last one BEFORE it (efe84b3, main 384.45). What 384.47 did to the bank
# besides (70 questions into Chapter 1, 17 removed: tools/gen-ifc-bank.py UNIT_MOVES / UNIT_REMOVALS) is read from the generator and left out of
# the comparisons here; tools/check-b384-moveperm.py holds that move.
BASE = os.environ.get("BASE") or "efe84b3"
import ast
def _gen(name):
    for n in ast.parse(open(os.path.join(HERE, "gen-ifc-bank.py"), encoding="utf-8").read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == name: return ast.literal_eval(n.value)
MOVED47 = sorted(i for i, to in _gen("UNIT_MOVES").items() if to == "1"); REMOVED47 = sorted(_gen("UNIT_REMOVALS")); GONE47 = set(MOVED47) | set(REMOVED47)   # (384.73) REMOVED47 is every removal (17 of 384.47, ch12-012 / ch55-702 / ch2-047 of 384.73)
EDIT73 = set(_gen("QUESTION_EDITS"))   # (384.73) the eight questions whose wording the audit fixes changed (tools/check-b384-qfix.py holds them)
# id -> the unit id it moves to, in the order the generator appends them


src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ifc543"}
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

ID = "chAppH-805"
NEWOPTS = ["hazardous materials inventory statement", "construction documents", "site plan", "hazardous materials management plan"]
READ = """()=>({ rows: QUESTIONS.map((q,i)=>({ id: q.ifc && q.ifc.id, key: KEYS[i], topic: q.topic, src: q.src, q: q.q, ch: q.choices, ans: q.answer, expl: q.explanation,
  cit: q.ifc && JSON.stringify(q.ifc.citation) })) })"""
ob, nb = bank_of(OLD_BANK), bank_of(NEW_BANK)
oq = {q["id"]: q for q in ob["questions"]}; nq = {q["id"]: q for q in nb["questions"]}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    IR = G["g"]["INSET_RE"]
    old_body = IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], OLD_HTML)
    ctx, pg, e0 = open_class(br, old_body, OLD_BANK)
    old = pg.evaluate(READ); ctx.close()
    O = {r["id"]: r for r in old["rows"]}
    STAMP = 1790000000321
    seed = ";(()=>{ try{ const k='class26e.ifc.drill.v1'; const s=JSON.parse(localStorage.getItem(k)||'{}'); s.flagged=Object.assign({}, s.flagged||{}, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % json.dumps({O[ID]["key"]: STAMP, O["ch1-008"]["key"]: STAMP + 1})
    ctx, pg, errs = open_class(br, G["g"]["patched"], NEW_BANK, seed)
    new = pg.evaluate(READ)
    flags = pg.evaluate("()=>JSON.parse(JSON.stringify(store.flagged||{}))")
    ctx.close(); br.close()
N = {r["id"]: r for r in new["rows"]}
# (1)
n = N[ID]; o = O[ID]
ans_text = n["ch"][n["ans"]] if isinstance(n["ans"], int) and 0 <= n["ans"] < len(n["ch"]) else None
chk("(1) %s as shown: options %s; keyed answer %r; wording, explanation and citation identical to main's; no 'operational permit application'" % (ID, n["ch"], ans_text),
    n["ch"] == NEWOPTS and ans_text == "hazardous materials management plan" and n["q"] == o["q"] and n["expl"] == o["expl"] and n["cit"] == o["cit"] and "operational permit application" not in n["ch"],
    (n["ch"], ans_text))
# (2)
diffs = [(i, sorted(k for k in set(oq[i]) | set(nq[i]) if oq[i].get(k) != nq[i].get(k))) for i in oq if i in nq and i not in GONE47 and i not in EDIT73 and oq[i] != nq[i]]
moved_fields = [i for i in MOVED47 if sorted(k for k in set(oq[i]) | set(nq[i]) if oq[i].get(k) != nq[i].get(k)) != ["unit"]]   # a 384.47 move changes `unit` and nothing else
chk("(2) the bank file: only %s differs from main's, in `options` alone (every other question, the units and the meta identical)" % ID,
    diffs == [(ID, ["options"])] and not moved_fields and [{k: v for k, v in u.items() if k != "questionCount"} for u in ob["units"]] == [{k: v for k, v in u.items() if k != "questionCount"} for u in nb["units"]]
    and {k: v for k, v in ob["meta"].items() if k != "questionCount"} == {k: v for k, v in nb["meta"].items() if k != "questionCount"} and set(nq) == set(oq) - set(REMOVED47) and len(nq) == 1812 - len(REMOVED47)
    and [k for k in nq[ID]["options"] if nq[ID]["options"][k] != oq[ID]["options"][k]] == ["B"], diffs[:4])
# (3)
moved = sorted(i for i in O if i not in REMOVED47 and O[i]["key"] != N.get(i, {}).get("key"))
allk = [r["key"] for r in new["rows"]]
chk("(3) all %d questions' keys identical on main and here but the %d the owner moved into Chapter 1 in 384.47 (%d differ), chAppH-805 included; all unique" % (len(N), len(MOVED47), len(moved)),
    len(N) == len(O) - len(REMOVED47) and moved == MOVED47 and len(set(allk)) == len(allk), moved[:6])
# (4)
chk("(4) the stars on %s and on ch1-008 are kept" % ID, flags.get(O[ID]["key"]) == STAMP and flags.get(O["ch1-008"]["key"]) == STAMP + 1, flags)
chk("(5) no page errors", not errs and not e0, (errs + e0)[:3])
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
