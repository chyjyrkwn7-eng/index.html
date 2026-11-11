#!/usr/bin/env python3
"""Build ifc/bank.js from the Fire Code hand-off's ifc_question_bank.json (build 328).

    python3 tools/gen-ifc-bank.py path/to/ifc_question_bank.json
    python3 tools/gen-ifc-bank.py --from-bank-js ifc/bank.js     (re-apply UNIT_MOVES to the shipped bank, in place)

The question file holds no IFC wording (pointers only) and the county's public text, so it
may live in the repo. It is written out as it is (every field: the viewer reads them), as
`window.IFC_BANK = {...}`, and is loaded only in the Fire Code class (the head script) and
while someone enrols. NEVER put the IFC PDF, or any picture cut from it, in this folder.
"""
import json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- UNIT_MOVES (build 384.42): questions the OWNER moved to another unit, applied to whatever the hand-off says ----
# {question id: unit id it now belongs to}. The hand-off's file still has them where the study guide put them, so a
# regeneration without this table would quietly undo the move. The id never changes (ids are references: pins, highlights).
# A moved question is placed after the target unit's LAST question in the array, so it takes the LAST position in that unit
# (ifcQuestionsFrom numbers a unit's questions in array order) and nobody else's position moves. The unit it left keeps its
# number as a gap in IFC_SRC_GAPS (index.html) so the questions after it keep theirs. When you add a move here, add its old
# position to IFC_SRC_GAPS and its old key to IFC_MOVED_KEYS in index.html too, or every later question in the unit it left
# loses its progress (tools/check-b384-moveq.py holds all of it).
#   ch12-012: "Group I-1 ... backup power within 3 hours" cites county 403.7.1.1 (Chapter 4's Fire safety and evacuation
#             plan): Chapter 12 (its first question, position 1) -> Chapter 4 (position 41).
UNIT_MOVES = {"ch12-012": "4"}

def apply_moves(bank):
    qs, units = bank["questions"], bank["units"]
    ids = {u["id"] for u in units}
    for qid, to in UNIT_MOVES.items():
        assert to in ids, (qid, to)
        q = next((x for x in qs if x["id"] == qid), None)
        assert q is not None, qid
        if q["unit"] == to:
            continue                               # already moved (re-running on the shipped bank): nothing to do
        qs.remove(q); q["unit"] = to
        last = max(i for i, x in enumerate(qs) if x["unit"] == to)
        qs.insert(last + 1, q)
    for u in units:                                # the unit sizes are the bank's own counts
        u["questionCount"] = sum(1 for x in qs if x["unit"] == u["id"])

arg = sys.argv[1]
if arg == "--from-bank-js":
    js = open(sys.argv[2], encoding="utf-8").read()
    bank = json.loads(js[js.index("window.IFC_BANK = ") + len("window.IFC_BANK = "):].rstrip().rstrip(";"))
else:
    bank = json.load(open(arg, encoding="utf-8"))
apply_moves(bank)
qs, units = bank["questions"], bank["units"]
assert bank["meta"]["schemaVersion"] == 5, bank["meta"]["schemaVersion"]
assert len(qs) == bank["meta"]["questionCount"], (len(qs), bank["meta"]["questionCount"])
ids = {u["id"] for u in units}
for q in qs:
    assert q["unit"] in ids, q["id"]
    assert sorted(q["options"]) == ["A", "B", "C", "D"], q["id"]
    assert q["answer"] in q["options"], q["id"]
    assert q["citation"].get("label"), q["id"]
out = os.path.join(ROOT, "ifc", "bank.js")
body = json.dumps({"meta": bank["meta"], "units": units, "questions": qs}, ensure_ascii=False, separators=(",", ":"))
with open(out, "w", encoding="utf-8") as f:
    f.write("/* The Fire Code class's question bank (schema %d, %d questions in %d units), built by\n"
            "   tools/gen-ifc-bank.py from the hand-off's ifc_question_bank.json. Do not edit by hand. */\n"
            % (bank["meta"]["schemaVersion"], len(qs), len(units)))
    f.write("window.IFC_BANK = " + body + ";\n")
print("wrote", out, os.path.getsize(out), "bytes,", len(qs), "questions,", len(units), "units")
