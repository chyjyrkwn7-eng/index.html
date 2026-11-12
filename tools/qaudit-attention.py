#!/usr/bin/env python3
"""Question audit, last step: ATTENTION.md, the list of everything that needs the owner's decision, in plain words and grouped by kind.
Reads verdicts.csv (qaudit-compose.py) and the study-guide list of questions no longer in the bank. Run: python3 tools/qaudit-attention.py OUTDIR [guide_missing.json]"""
import sys, os, csv, json, collections, re
OUT = sys.argv[1]
rows = list(csv.DictReader(open(os.path.join(OUT, "verdicts.csv"), encoding="utf-8")))
by = {r["id"]: r for r in rows}
missing = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else []
SEV = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "": 0}
def line(r, n=230):
    t = re.sub(r"\s+", " ", r["reason"]).strip()
    return "- **%s** (%s, %s): %s" % (r["id"], r["unit"], r["severity"], t[:n] + ("..." if len(t) > n else ""))
def kind(r, k): return k in [x.strip() for x in r["kinds"].split(";")]
fl = [r for r in rows if r["severity"]]
cnt = collections.Counter(r["severity"] or "OK" for r in rows)
L = []
w = L.append
w("# What needs Madison's attention")
w("")
w("Audit of all %d Fire Code questions (the bank on branch claude/b384-moveperm, Chapter 1 = 158). Nothing was changed: every item below is a report." % len(rows))
w("Result: **%d OK, %d flagged** (HIGH %d, MEDIUM %d, LOW %d). The full list, one line per question, is in INDEX.md and verdicts.csv; each question's pictures are in its chapter PDF." % (cnt["OK"], len(fl), cnt["HIGH"], cnt["MEDIUM"], cnt["LOW"]))
w("")
w("How to read a flag. HIGH = the picture or the question is wrong in a way a student would notice. MEDIUM = worth fixing, nobody is misled about the answer. LOW = a note; leaving it is fine.")
w("")
w("## 1. The two open items you asked about")
w("")
w("**ch30-709** (emergency repair on an industrial oven, application due within 2 working days): **KEEP.** The cited county text for ovens (105.6.14, exception 2, booklet p.24) says \"within two working days of commencement of work\", so the stem is answerable from it. The competing rule is the general one in 105.1.4 (\"the next working business day\"), which is the wrong option \"1 working day\". County 102.10 settles it: the specific requirement applies over the general one. It is not a repeat of ch30-506 (that one asks which permit, answer: construction permit), although ch30-506's explanation already mentions the two days. Same exception also appears under 105.6.2 and 105.6.12, but the stem names the oven.")
w("")
w("**ch1-142** (fire lane fine \"$200 to $500\"): **KEEP (leave it).** It is correct and it is not a repeat: it asks about row 503.4 (obstructing a fire lane) of Table 112.4.2. The range appears in the stem of ch1-112 (working without permits) and is the key of ch1-609 (stop work order), and 9 of the table's 11 rows are $200 to $500 (not 8; the other two are $100 to $250 and a flat $500), so it is the easy guess. If you want fewer fine questions, this is the one to drop; nothing is wrong with it.")
w("")
w("**chAppC (hydrant table) and ch22-014 (dust table), highlight on the table title only.** The question and key are right in all of them; the highlight should be:")
for i in ["chAppC-004", "chAppC-005", "chAppC-009", "chAppC-003", "ch22-014"]:
    w(line(by[i], 420))
w("")
w("Build 384.56 (branch b384-ifcmarks, not merged) already fixes the four Appendix C questions and ten more (below); it does NOT cover ch22-014. The PDFs show the picture the app draws today, and for the 15 questions that build fixes, a second picture under it showing what 384.56 would draw (checked: the words that decide the answer are inside the gold in every one).")
w("")
w("## 2. The highlight does not cover the words that prove the answer")
w("")
hm = sorted([r for r in fl if kind(r, "Highlight misses the proof")], key=lambda r: (-SEV[r["severity"]], r["id"]))
w("%d questions. The answer is right in all of them; what is marked is the title, a lead-in, or a neighbouring line." % len(hm))
w("")
for r in hm: w(line(r, 200))
w("")
w("Of these, 384.56 fixes: " + ", ".join(sorted(r["id"] for r in hm if re.search(r"ixed by the unmerged", r["reason"]))) + ".")
w("Not fixed by 384.56: " + ", ".join(sorted(r["id"] for r in hm if not re.search(r"ixed by the unmerged", r["reason"]))) + ".")
w("")
w("## 3. The same question twice")
w("")
for r in sorted([r for r in fl if kind(r, "Repeat or overlap") and r["severity"] != "LOW"], key=lambda r: r["id"]): w(line(r, 330))
w("")
w("Smaller overlaps (a key printed in another question's stem, or one number reused): " + ", ".join(r["id"] for r in sorted([r for r in fl if kind(r, "Repeat or overlap") and r["severity"] == "LOW"], key=lambda r: r["id"])) + ". These are all LOW; see INDEX.md.")
w("")
w("## 4. The wording gives the answer away")
w("")
for r in sorted([r for r in fl if kind(r, "Gives the answer away")], key=lambda r: (-SEV[r["severity"]], r["id"])): w(line(r, 300))
w("")
w("(The earlier Chapter 1 audit also rated ch1-040, ch1-081, ch1-612 and eight more MEDIUM. Re-read against the cited text, the \"exclusion inferred\" ones (ch22-001, ch26-001, ch61-716, ch55-503) are fine: the wrong options are simply not in the permit list, and nothing in the booklet makes them arguable. ch30-505 and ch20-508 are gone from the bank.)")
w("")
w("## 5. A wrong option is arguably right")
w("")
for r in sorted([r for r in fl if kind(r, "Another option is arguably right")], key=lambda r: r["id"]): w(line(r, 260))
w("")
w("## 6. Pictures")
w("")
pic = [r for r in fl if kind(r, "Picture problem")]
tab = [r for r in pic if "without the table" in r["reason"]]
tall = [r for r in pic if "very tall" in r["reason"] and r not in tab]
oth = [r for r in pic if r not in tab and r not in tall]
w("Every one of the 1,795 questions has a cropped picture (framed and highlighted the way the app draws it) and a whole-page picture; none is blank (checked by pixels, and about 40 looked at by eye). Notes:")
w("")
w("- **Table 1004.5 (occupant load), %d questions in Chapter 10** are drawn as the whole table, 928 points tall (about 1.2 phone screens); the cited row can be below the fold (Warehouses is the last row, at the very bottom). The highlight is correct. Ids: %s." % (len([r for r in tall if r["id"].startswith("ch10-1")]), ", ".join(r["id"] for r in tall if r["id"].startswith("ch10-1"))))
w("- **Other tall pictures (more than about 750 points)** where the cited line is a small part: " + ", ".join(r["id"] for r in tall if not r["id"].startswith("ch10-1")) + ".")
w("- **County table rows drawn without the table's title or column headings (%d)**: Table 105.5.22 / Table 1004.5 rows whose title is on the previous booklet page, so neither the crop nor the whole-page picture says what the numbers are: %s." % (len(tab), ", ".join(r["id"] for r in tab)))
for r in oth: w(line(r, 300))
w("")
w("## 7. Typos (report only)")
w("")
for r in sorted([r for r in fl if kind(r, "Typo (report only)")], key=lambda r: r["id"]): w(line(r, 260))
w("")
w("Everything else the spell check found is a real technical word (resubmittal, draftstops, as-builts, odorized, requalification, undiked...). Questions are word for word the study guide, so none of this was touched.")
w("")
w("## 8. The bank against the printed study guide")
w("")
w("The study guide PDF in the hand-off kit (1,675 questions) and the bank (1,657 content questions plus 138 Chapter-finder questions that the guide does not print) agree word for word on **1,651** content questions: same question, same four options, same key. They differ on:")
w("")
GD = {"ch1-008": "the bank adds \"Under the Harris County Fire Code Amendments,\" and rewords the rest of the stem (the guide: \"When a substantial improvement is made, ___ must be brought into compliance with the new construction requirements of the Harris County Fire Code\").",
      "ch1-303": "the bank says \"Under the Harris County Fire Code Amendments,\" where the guide says \"Under Harris County's code,\".",
      "ch1-311": "the bank says \"Under the Harris County Fire Code Amendments, how must ... be reported to the fire code official?\"; the guide says \"... to the Harris County fire code official?\".",
      "ch56-009": "the bank says \"moved into Harris County's jurisdiction\"; the guide says \"moved into the county's fire code jurisdiction\".",
      "chAppH-805": "the 5.4.3 question (Emergency Action Plan / Emergency Response Plan, one wrong option replaced at your request); the printed guide does not have it in this form.",
      "chExhB-801": "the banquet-room occupant load question (3,000 square feet, answer 200); the printed guide has the escape-room one (chExhB-205) but not this one.",
      "ch1-040": "the explanation says \"showing the fire code is met\"; the guide says \"showing the county fire code is met\" (one word). Question, options and key are the same."}
for i in sorted(GD): w("- **%s** (%s): %s" % (i, by[i]["unit"], GD[i]))
w("")
w("And %d questions printed in the guide are no longer in the bank (the county permit questions removed or moved to Chapter 1, and the three Chapter 1 and one Chapter 56 questions listed above whose text was reworded):" % len(missing))
w("")
for m in missing: w("- guide %s: %s [%s]" % (m["guide"], re.sub(r"\s+", " ", m["q"])[:120], m["ref"]))
w("")
w("## 9. Chapter placement and the citations")
w("")
w("- Every content question cites the chapter it sits in. Checked by section number for all 1,657: the only mismatches are the seven Exhibit B questions (they cite the county's IBC amendments, Table 508.4 and Table 1004.5, which is what Exhibit B is). No county permit question is left outside Chapter 1.")
w("- Every Chapter-finder question (138) has the chapter or section that is the answer: titles and numbers match the book and the county booklet, 0 disagreements.")
w("- Every cited section is printed on the cited page, with one explained exception: county table rows continued from the previous page (section 6).")
w("")
w("## 10. What was not checked, and why")
w("")
w("- Chromium drew the pictures at the iPhone's pixel ratio, but it cannot show the iPhone's own safe areas, blur or fonts; the pictures are the app's own drawing of your book, not a photograph of a phone.")
w("- I read every question, its options, its key and the words highlighted (not the whole book section behind each one). A wrong key would have shown as numbers not found in the highlight; paraphrased answers (about 120) I compared by eye to the highlighted text. Questions whose answer depends on reading a table were checked against the table page picture, not re-derived from the whole code.")
w("- The pictures of the whole page have the book's licence footer and the licence number at the top painted over; the crops are as the app draws them.")
open(os.path.join(OUT, "ATTENTION.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("wrote ATTENTION.md, %d lines" % len(L))
