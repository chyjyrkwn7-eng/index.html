#!/usr/bin/env python3
"""Build ifc/bank.js from the Fire Code hand-off's ifc_question_bank.json (build 328).

    python3 tools/gen-ifc-bank.py path/to/ifc_question_bank.json

The question file holds no IFC wording (pointers only) and the county's public text, so it
may live in the repo. It is written out as it is (every field: the viewer reads them), as
`window.IFC_BANK = {...}`, and is loaded only in the Fire Code class (the head script) and
while someone enrols. NEVER put the IFC PDF, or any picture cut from it, in this folder.
"""
import json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
bank = json.load(open(src, encoding="utf-8"))
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
