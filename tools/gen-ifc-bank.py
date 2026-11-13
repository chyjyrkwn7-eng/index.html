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
# (sections 101-199, source 'amendment') and that sat in other chapters move to Chapter 1 (UNIT_MOVES above: 70 of them); 17 are not
# moved and are not kept: 15 ask the same fact as one that stays (the same table cell or the same limit), and two the owner took out himself: ch20-508 (the
# rooftop-heliport question; its wrong options are not stated not to need a permit) and ch30-505 (industrial ovens: 'an _____ permit' -
# the article fits only 'operational', so the grammar gives the answer away; the fact itself, 105.5.26, is right). They are DELETED
# here. A removed question's position stays taken in its old chapter (IFC_SRC_GAPS), its key is un-starred once
# (IFC_RETIRED_KEYS) and its answer counts are left alone - the 5.4.2 precedent. Never reword a question to fix it: it goes or it is
# reported (384.73: the owner lifted that for the audit's items - QUESTION_EDITS below, each with its old text pinned). The table of what was kept and removed, with the reason for each, is in docs/notes-archive.md ("384.47").
# A removal is applied BEFORE the moves and is a no-op for an id that is already gone (re-running on the shipped bank).
#   (384.73) ch12-012 and ch55-702 were moved here in 384.42 and are REMOVED in 384.73 (UNIT_REMOVALS: each repeats a question that stays), so
#   they are no longer in this table; their moves are history (IFC_MOVED_KEYS keeps the entries, which nothing reads once the id is gone).
UNIT_MOVES = {"ch62-702": "2", "ch62-703": "2", "ch64-001": "2",
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
    "ch30-506": "1", "ch30-709": "1", "ch39-002": "1", "chAppC-702": "1", "ch12-319": "1", "ch10-108": "1"}

UNIT_REMOVALS = ["ch28-501", "ch37-001", "ch56-312", "ch59-711", "ch29-201", "ch50-074", "ch54-009", "ch50-075", "ch59-207",
    "ch53-601", "ch63-210", "ch63-510", "ch63-701", "ch55-501", "ch55-502", "ch20-508", "ch30-505",
    # (384.73) the three same-question pairs the audit found, the weaker twin of each (the owner: "do what is best"):
    # ch12-012 repeats ch4-001 (county 403.7.1.1, backup power within 3 hours), ch55-702 repeats ch2-086 (the IFC definition of a
    # cryogenic fluid, boiling point lower than -130 F), ch2-047 repeats ch1-071 (a special event outdoors is 100 or more people).
    "ch12-012", "ch55-702", "ch2-047"]

# ---- QUESTION_EDITS (build 384.73): wording the OWNER had changed after the audit, applied to whatever the hand-off says ----
# "The 85 flagged and any other issues mentioned in the attention document ... fix it now." {question id: {field: (old, new)}}; an
# option is addressed as "options.B". A field already holding the new text is left alone (re-running on the shipped bank is a
# no-op); one holding neither is an error (the bank is not what this table was written against). A question's key is its chapter,
# its position and a hash of its wording and choices, so every edit to a stem or an option has its old text pinned in index.html
# (IFC_KEY_TEXT / IFC_KEY_CHOICES) - an explanation is not part of the key and needs nothing. The reason for each is in
# docs/notes-archive.md ("384.73").
QUESTION_EDITS = {
    # the article "a" in the stem ruled out "operational" (and "an" in 105.7 made the key the odd one out): the stem no longer has one
    "ch1-081": {"question": ("Harris County requires a _____ permit to install or modify a gate across a fire apparatus access road.",
                             "Which type of permit does Harris County require to install or modify a gate across a fire apparatus access road?")},
    "ch1-612": {"question": ("In Harris County, an industrial facility may be approved for exemption from the fire code, including operational permits, if it has a _____.",
                             "In Harris County, an industrial facility may be approved for exemption from the fire code, including operational permits, if it has which of these?")},
    # 105.3.4 lets the fire code official issue a conditional or partial certificate of COMPLIANCE, so that wrong option was arguable
    # (the 5.4.3 precedent for chAppH-805: the option is replaced, the old one stays in the key)
    "ch1-040": {"options.A": ("Compliance", "Completion")},
    # a figure the answer to another question depends on was printed in this stem (ch3-624 asks 50 percent, ch35-016 asks 30 feet,
    # ch1-142 and ch1-609 ask $200 to $500): the stem keeps the question and drops the figure
    "ch3-099": {"question": ("In Harris County, the occupant load of a mobile food vendor vehicle park whose perimeter is enclosed more than 50 percent is calculated at _____ square feet per occupant.",
                             "In Harris County, the occupant load of a mobile food vendor vehicle park is calculated at _____ square feet per occupant.")},
    "ch35-009": {"question": ("At least one portable fire extinguisher rated not less than _____ shall be within 30 feet of hot work being performed.",
                              "At least one portable fire extinguisher provided for hot work must have a minimum rating of _____.")},
    "ch1-112": {"question": ("In Harris County, a citation for working without permits carries a $200 to $500 fine plus _____ permit fees.",
                             "In Harris County, a citation for working without permits carries a fine plus _____ permit fees.")},
    # American spelling; and the hydrant row beside the 3,000 gpm row is 350 feet (the 3,251-4,000 row), not 300 (the row after that)
    "ch28-701": {"explanation": ("The separation is one and one-half times the pile height, measured to buildings, property lines and neighbouring piles, with approved access roads in that space.",
                                 "The separation is one and one-half times the pile height, measured to buildings, property lines and neighboring piles, with approved access roads in that space.")},
    "chAppC-002": {"explanation": ("The 2,751 to 3,250 gpm row lists an average hydrant spacing of 400 feet, before any footnote adjustment. Neighbouring rows list 450 feet (lower flows) and 300 feet (higher flows).",
                                   "The 2,751 to 3,250 gpm row lists an average hydrant spacing of 400 feet, before any footnote adjustment. The rows either side list 450 feet (lower flows) and 350 feet (higher flows).")},
}

# ---- QUESTION_ADDS (build 384.104): questions the OWNER asked for, written from the book, applied to whatever the hand-off says ----
# "More occupant load questions. Chapter 10 is really good, it needs a few more occupant load questions though. There should be a question
# over almost all of them. Ensure there is a question regarding the bench/pew stuff too." Every number and every word is IFC 2021 Table 1004.5
# (book pages 10-3 / 10-4, PDF pages 200 / 201) or Section 1004.6 / 1004.8 (10-4) as printed in the owner's copy; the county amends only the
# IBC's Table 1004.5 "Assembly" rows (Exhibit B: the same five factors, plus Escape/Puzzle rooms) and nothing of IFC Section 1004. The book
# says "fixed seating without dividing arms" and (in the definition of FIXED SEATING) "bench-type seats"; it never says "pew", so no question
# does. A new question is placed after its unit's LAST question in the array (in the order listed), so it takes the next positions of that
# unit (Chapter 10: 133-158) and no existing question's position, and so no existing key, moves. Ids continue Chapter 10's numbering (the
# highest ever was ch10-338). An id already in the bank must be identical (re-running on the shipped bank is a no-op). The coverage table,
# row by row, is in docs/notes-archive.md ("384.104"); tools/check-b384-occload.py holds it against the book.
_T1004 = {"source": "ifc", "section": "Table 1004.5", "heading": "Table 1004.5 — Maximum Floor Area Allowances per Occupant",
          "label": "IFC 2021 Table 1004.5"}
def _q(qid, question, options, answer, explanation, topic, kind, citation):
    return {"id": qid, "unit": "10", "type": "content", "question": question, "options": dict(zip("ABCD", options)), "answer": answer,
            "explanation": explanation, "topic": topic, "kind": kind, "citation": citation}
def _row(qid, row, page, question, options, answer, explanation, topic):
    # a row of Table 1004.5: PDF page 200 is book page 10-3 (the table's first eight rows), 201 is 10-4 (the rest)
    return _q(qid, question, options, answer, explanation, topic, "measure",
              dict(_T1004, pdfPage=page, printedPage={200: "10-3", 201: "10-4"}[page], row=row))
def _sec(qid, section, heading, find, question, options, answer, explanation, topic, kind="measure"):
    return _q(qid, question, options, answer, explanation, topic, kind,
              {"source": "ifc", "section": section, "heading": heading, "label": "IFC 2021 " + section, "pdfPage": 201, "printedPage": "10-4", "find": [find]})
QUESTION_ADDS = [
    _row("ch10-339", "Accessory storage areas, mechanical", 200,
         "Accessory storage areas and mechanical equipment rooms are figured at one occupant per _____ gross square feet.",
         ["100", "200", "300", "500"], "C",
         "Table 1004.5 lists accessory storage areas and mechanical equipment rooms at 300 gross square feet per occupant.",
         "accessory storage occupant load"),
    _row("ch10-340", "Agricultural building", 200,
         "An agricultural building has 15,000 gross square feet. What is its occupant load?",
         ["50", "75", "150", "300"], "A",
         "Agricultural buildings are figured at 300 gross square feet per occupant: 15,000 ÷ 300 = 50.",
         "agricultural building load"),
    _row("ch10-341", "Aircraft hangars", 200,
         "Aircraft hangars are figured at one occupant per _____ gross square feet.",
         ["200", "240", "300", "500"], "D",
         "Table 1004.5 sets aircraft hangars at 500 gross square feet per occupant.",
         "aircraft hangar occupant load"),
    _row("ch10-342", "Baggage claim", 200,
         "An airport terminal's baggage claim area has 9,000 gross square feet. What is its occupant load?",
         ["30", "90", "450", "600"], "C",
         "Airport terminal baggage claim areas are figured at 20 gross square feet per occupant: 9,000 ÷ 20 = 450.",
         "baggage claim load"),
    _row("ch10-343", "Baggage handling", 200,
         "In an airport terminal, baggage handling areas are figured at one occupant per _____ gross square feet.",
         ["20", "100", "200", "300"], "D",
         "Table 1004.5 lists airport terminal baggage handling areas at 300 gross square feet per occupant.",
         "baggage handling occupant load"),
    _row("ch10-344", "Concourse", 200,
         "An airport terminal concourse has 30,000 gross square feet. What is its occupant load?",
         ["100", "300", "1,500", "2,000"], "B",
         "An airport terminal concourse is figured at 100 gross square feet per occupant: 30,000 ÷ 100 = 300.",
         "concourse load"),
    _row("ch10-345", "Waiting areas", 200,
         "Airport terminal waiting areas are figured at one occupant per _____ gross square feet.",
         ["15", "20", "50", "100"], "A",
         "Table 1004.5 lists airport terminal waiting areas at 15 gross square feet per occupant.",
         "terminal waiting area occupant load"),
    _row("ch10-346", "Gaming floors (keno, slots, etc.)", 201,
         "A casino gaming floor with slot machines and keno has 5,500 gross square feet. What is its occupant load?",
         ["110", "220", "275", "500"], "D",
         "Gaming floors (keno, slots and the like) are figured at 11 gross square feet per occupant: 5,500 ÷ 11 = 500.",
         "gaming floor load"),
    _row("ch10-347", "Exhibit gallery and museum", 201,
         "A museum's exhibit gallery has 4,500 net square feet. What is its occupant load?",
         ["90", "150", "300", "900"], "B",
         "Exhibit galleries and museums are figured at 30 net square feet per occupant: 4,500 ÷ 30 = 150.",
         "exhibit gallery load"),
    _row("ch10-348", "Concentrated (chairs only—not fixed)", 201,
         "An assembly room set up with chairs only, not fixed, has 2,100 net square feet. What is its occupant load?",
         ["70", "140", "300", "420"], "C",
         "Assembly without fixed seats, concentrated (chairs only, not fixed), is figured at 7 net square feet per occupant: 2,100 ÷ 7 = 300.",
         "concentrated assembly load"),
    _row("ch10-349", "Standing space", 201,
         "Assembly standing space is figured at one occupant per _____ net square feet.",
         ["3", "5", "7", "15"], "B",
         "Table 1004.5 lists standing space, under assembly without fixed seats, at 5 net square feet per occupant.",
         "standing space occupant load"),
    _row("ch10-350", "Unconcentrated (tables and chairs)", 201,
         "Unconcentrated assembly space, set with tables and chairs, is figured at one occupant per _____ net square feet.",
         ["5", "7", "11", "15"], "D",
         "Table 1004.5 lists unconcentrated assembly space (tables and chairs) at 15 net square feet per occupant.",
         "unconcentrated assembly occupant load"),
    _row("ch10-351", "Bowling centers, allow 5 persons for each", 201,
         "A bowling center has 12 lanes, each including 15 feet of runway, and 1,400 net square feet of additional areas. What is its occupant load?",
         ["60", "200", "260", "284"], "C",
         "Table 1004.5 allows 5 persons for each lane including 15 feet of runway (12 × 5 = 60) and 7 net square feet per occupant for additional areas (1,400 ÷ 7 = 200), for 260 in all.",
         "bowling center load"),
    _row("ch10-352", "Group H-5 fabrication and manufacturing", 201,
         "Group H-5 fabrication and manufacturing areas are figured at one occupant per _____ gross square feet.",
         ["50", "100", "150", "200"], "D",
         "Table 1004.5 sets Group H-5 fabrication and manufacturing areas at 200 gross square feet per occupant.",
         "Group H-5 occupant load"),
    _row("ch10-353", "Outpatient areas", 201,
         "A hospital's outpatient area has 6,000 gross square feet. What is its occupant load?",
         ["25", "50", "60", "120"], "C",
         "Institutional outpatient areas are figured at 100 gross square feet per occupant: 6,000 ÷ 100 = 60.",
         "outpatient area load"),
    _row("ch10-354", "Sleeping areas", 201,
         "Institutional sleeping areas are figured at one occupant per _____ gross square feet.",
         ["100", "120", "200", "240"], "B",
         "Table 1004.5 lists institutional sleeping areas at 120 gross square feet per occupant.",
         "institutional sleeping occupant load"),
    _row("ch10-355", "Stack area", 201,
         "A library's stack area has 5,000 gross square feet. What is its occupant load?",
         ["25", "50", "100", "250"], "B",
         "Library stack areas are figured at 100 gross square feet per occupant: 5,000 ÷ 100 = 50.",
         "library stack load"),
    _row("ch10-356", "Locker rooms", 201,
         "Locker rooms are figured at one occupant per _____ gross square feet.",
         ["50", "100", "150", "200"], "A",
         "Table 1004.5 sets locker rooms at 50 gross square feet per occupant.",
         "locker room occupant load"),
    _row("ch10-357", "Storage, stock, shipping areas", 201,
         "A store's storage, stock and shipping area has 9,000 gross square feet. What is the occupant load of that area?",
         ["18", "30", "90", "150"], "B",
         "Mercantile storage, stock and shipping areas are figured at 300 gross square feet per occupant: 9,000 ÷ 300 = 30.",
         "mercantile stock area load"),
    _row("ch10-358", "Rink and pool", 201,
         "For a skating rink, the rink itself is figured at one occupant per _____ gross square feet.",
         ["15", "20", "30", "50"], "D",
         "Table 1004.5 lists skating rinks with swimming pools: the rink or pool is figured at 50 gross square feet per occupant, and the decks at 15.",
         "skating rink occupant load"),
    _sec("ch10-359", "1004.8", "Concentrated business use areas", "not less than one occupant per 50 square feet",
         "Where approved, the occupant load of a telephone call center is its actual occupant load, but not less than one occupant per _____ square feet of gross occupiable floor space.",
         ["50", "100", "150", "200"], "A",
         "Concentrated business use areas, such as telephone call centers, trading floors and data processing centers, may use the actual occupant load where approved, but not less than one occupant per 50 square feet of gross occupiable floor space.",
         "concentrated business minimum"),
    _sec("ch10-360", "1004.6", "Fixed seating", "determined by the number of fixed seats installed",
         "An auditorium seating area of 4,200 net square feet has 450 fixed seats and aisles. What is the occupant load of the seating area?",
         ["280", "450", "600", "840"], "B",
         "Where an area has fixed seats and aisles, the occupant load is the number of fixed seats installed, 450, not a figure worked out from the floor area.",
         "fixed seats occupant load"),
    _sec("ch10-361", "1004.6", "Fixed seating", "added to the number of fixed seats",
         "In an area with fixed seats, the occupant load of a part where fixed seating is not installed, such as a waiting space, is _____.",
         ["not counted, because the fixed seats set the occupant load", "counted only where it holds more people than the fixed seats",
          "determined under Section 1004.5 and added to the fixed seats", "assigned by the owner from the expected number of people"], "C",
         "Where fixed seating is not installed, such as in waiting spaces, the occupant load is determined under Section 1004.5 and added to the number of fixed seats.",
         "fixed seating with waiting space", kind="other"),
    _sec("ch10-362", "1004.6", "Fixed seating", "one person for each 18 inches",
         "For fixed seating without dividing arms, such as bench-type seats, the occupant load is not less than one person for each _____ of seating length.",
         ["12 inches", "15 inches", "18 inches", "30 inches"], "C",
         "For fixed seating without dividing arms, the occupant load is at least the number of seats based on one person for each 18 inches of seating length.",
         "bench seating factor"),
    _sec("ch10-363", "1004.6", "Fixed seating", "one person for each 18 inches",
         "A chapel has 12 fixed benches without dividing arms, each 15 feet long. What is the minimum occupant load of the benches?",
         ["72", "120", "144", "180"], "B",
         "Each bench is 180 inches long, and at one person for each 18 inches of seating length that is 10 people a bench: 12 × 10 = 120.",
         "bench rows occupant load"),
    _sec("ch10-364", "1004.6", "Fixed seating", "one person for each 24 inches",
         "A restaurant seating booth has 96 inches of booth seat length, measured at the backrest. What is its occupant load?",
         ["4", "6", "8", "12"], "A",
         "Seating booths are figured at one person for each 24 inches of booth seat length measured at the backrest: 96 ÷ 24 = 4.",
         "booth seating occupant load"),
]

def apply_moves(bank):
    qs, units = bank["questions"], bank["units"]
    ids = {u["id"] for u in units}
    for qid in UNIT_REMOVALS:                      # the owner's removals first (an id already gone: nothing to do)
        q = next((x for x in qs if x["id"] == qid), None)
        if q is not None:
            qs.remove(q)
    bank["meta"]["questionCount"] = len(qs)        # the bank's own count follows (the app reads it; nothing types it)
    for qid, edits in QUESTION_EDITS.items():      # (384.73) the owner's wording changes
        q = next((x for x in qs if x["id"] == qid), None)
        assert q is not None, qid
        for field, (old, new) in edits.items():
            box, key = (q["options"], field.split(".")[1]) if field.startswith("options.") else (q, field)
            assert box[key] in (old, new), (qid, field, box[key])
            box[key] = new
    for qid, to in UNIT_MOVES.items():
        assert to in ids, (qid, to)
        q = next((x for x in qs if x["id"] == qid), None)
        assert q is not None, qid
        if q["unit"] == to:
            continue                               # already moved (re-running on the shipped bank): nothing to do
        qs.remove(q); q["unit"] = to
        last = max(i for i, x in enumerate(qs) if x["unit"] == to)
        qs.insert(last + 1, q)
    for add in QUESTION_ADDS:                      # (384.104) the owner's new questions, after their unit's last question, in this order
        assert add["unit"] in ids, add["id"]
        q = next((x for x in qs if x["id"] == add["id"]), None)
        if q is not None:
            assert q == add, ("an added id is in the bank with other content", add["id"])
            continue                               # already added (re-running on the shipped bank): nothing to do
        last = max(i for i, x in enumerate(qs) if x["unit"] == add["unit"])
        qs.insert(last + 1, json.loads(json.dumps(add)))
    bank["meta"]["questionCount"] = len(qs)
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
