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
#   "we ARENT gonna study chapter 9 and get references to chapter 2": a unit's questions cite that unit's own chapter. Four
#   questions that ask a fact from a definition (they cite IFC 2021 202, Definitions) go to Chapter 2, after its 107 (108..111):
#   ch55-702 (Cryogenic Fluids, position 12), ch62-702 and ch62-703 (Organic Peroxides, 8 and 9), ch64-001 (Pyrophoric, 1).
#   Several moves into one unit append in the order listed here.
#
# ---- UNIT_REMOVALS (build 384.47): questions the OWNER took OUT of the bank ----
# "the 87 questions we are gonna take them and put them in chapter 1 ... I don't want repeat questions and I don't want bad
# questions ... I want the best questions out of what we got." The 87 Fire Code questions whose citation is the county's Chapter 1
# (sections 101-199, source 'amendment') and that sat in other chapters move to Chapter 1 (UNIT_MOVES above: 69 of them after 384.70; 70 in 384.47); 18 are not
# moved and are not kept: 15 ask the same fact as one that stays (the same table cell or the same limit), and two the owner took out himself: ch20-508 (the
# rooftop-heliport question; its wrong options are not stated not to need a permit) and ch30-505 (industrial ovens: 'an _____ permit' -
# the article fits only 'operational', so the grammar gives the answer away; the fact itself, 105.5.26, is right), and (384.70) ch30-709
# (industrial ovens: emergency repair work, application due within 2 working days - it asks the fact ch30-506 already asks; it was on the move list and comes off it). They are DELETED
# here. A removed question's position stays taken in its old chapter (IFC_SRC_GAPS), its key is un-starred once
# (IFC_RETIRED_KEYS) and its answer counts are left alone - the 5.4.2 precedent. Never reword a question to fix it: it goes or it is
# reported. The table of what was kept and removed, with the reason for each, is in docs/notes-archive.md ("384.47").
# A removal is applied BEFORE the moves and is a no-op for an id that is already gone (re-running on the shipped bank).
UNIT_MOVES = {"ch12-012": "4", "ch55-702": "2", "ch62-702": "2", "ch62-703": "2", "ch64-001": "2",
    # (384.47) the county permit questions: Chapter 1 (sections 101-199), in citation order, after its own 88 (positions 89-158)
    "ch51-020": "1", "ch20-003": "1", "ch22-001": "1", "ch37-710": "1", "ch53-024": "1", "ch53-025": "1",
    "ch53-602": "1", "ch53-603": "1", "ch54-010": "1", "ch58-501": "1", "ch60-514": "1", "ch64-204": "1",
    "ch55-019": "1", "ch55-020": "1", "ch55-021": "1", "ch55-022": "1", "ch55-717": "1", "ch58-502": "1",
    "ch58-503": "1", "ch21-012": "1", "chAppC-704": "1", "ch57-001": "1", "ch57-002": "1", "ch57-003": "1",
    "ch57-004": "1", "ch57-005": "1", "ch25-001": "1", "ch26-001": "1", "ch26-712": "1", "ch50-076": "1",
    "ch54-011": "1", "ch60-511": "1", "ch60-701": "1", "ch60-702": "1", "ch62-205": "1", "ch62-206": "1",
    "ch62-506": "1", "ch62-507": "1", "ch62-701": "1", "ch63-702": "1", "ch63-703": "1", "ch63-704": "1",
    "ch66-701": "1", "ch66-702": "1", "ch66-703": "1", "ch66-704": "1", "ch67-711": "1", "ch67-712": "1",
    "ch67-713": "1", "ch27-518": "1", "ch35-001": "1", "ch35-002": "1", "ch61-716": "1",
    "ch39-001": "1", "chAppC-701": "1", "chAppC-703": "1", "ch65-006": "1", "ch34-007": "1",
    "ch31-031": "1", "ch61-715": "1", "ch34-008": "1", "ch55-503": "1", "ch12-320": "1", "ch32-612": "1",
    "ch30-506": "1", "ch39-002": "1", "chAppC-702": "1", "ch12-319": "1", "ch10-108": "1"}

UNIT_REMOVALS = ["ch28-501", "ch37-001", "ch56-312", "ch59-711", "ch29-201", "ch50-074", "ch54-009", "ch50-075", "ch59-207",
    "ch53-601", "ch63-210", "ch63-510", "ch63-701", "ch55-501", "ch55-502", "ch20-508", "ch30-505", "ch30-709"]

def apply_moves(bank):
    qs, units = bank["questions"], bank["units"]
    ids = {u["id"] for u in units}
    for qid in UNIT_REMOVALS:                      # the owner's removals first (an id already gone: nothing to do)
        q = next((x for x in qs if x["id"] == qid), None)
        if q is not None:
            qs.remove(q)
    bank["meta"]["questionCount"] = len(qs)        # the bank's own count follows (the app reads it; nothing types it)
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
