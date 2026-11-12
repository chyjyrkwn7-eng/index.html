#!/usr/bin/env python3
"""Question audit, step 3: put the machine's facts (qaudit-analyze.py) and the reader's flags (flags.jsonl) together into one verdict per question.

Writes verdicts.json (for qaudit-pdf.py), verdicts.csv and INDEX.md (every verdict) and ATTENTION.md (what needs the owner's decision, in plain words).
A question with no flag is OK. A flag has a severity (HIGH / MEDIUM / LOW), kinds (the groups used in ATTENTION.md), a reason and a recommendation.
Machine flags (added here, not by hand): a picture problem (no cropped picture, no highlight drawn, a tall picture, a table row without its title), a
difference from the study guide, a citation whose section is not on the cited page, a chapter finder whose keyed chapter is not the cited one.
Run: python3 tools/qaudit-compose.py --bank ifc/bank.js --mech mech.json --flags flags.jsonl --out DIR [--read read.txt] [--guide sg.json]"""
import os, sys, json, csv, re, collections
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
bs = open(arg("--bank"), encoding="utf-8").read(); bank = json.loads(bs[bs.index("{"): bs.rindex("}") + 1])
mech = json.load(open(arg("--mech"))); OUT = arg("--out"); os.makedirs(OUT, exist_ok=True)
units = {u["id"]: u for u in bank["units"]}
SEV = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
flags = collections.defaultdict(list)
for ln in open(arg("--flags")):
    ln = ln.strip()
    if ln: d = json.loads(ln); flags[d["id"]].append(d)
silence = set()                                    # ids whose automatic picture flags were looked at and cleared by the reader
if arg("--silence") and os.path.exists(arg("--silence")): silence = {l.split()[0] for l in open(arg("--silence")) if l.strip() and not l.startswith("#")}
readrng = collections.defaultdict(list)
if arg("--read") and os.path.exists(arg("--read")):
    for l in open(arg("--read")):
        p = l.split()
        if len(p) >= 3: readrng[p[0]].append((int(p[1]), int(p[2])))
order = {u["id"]: i for i, u in enumerate(sorted(bank["units"], key=lambda u: u.get("order", 0)))}
byunit = collections.defaultdict(list)
for q in bank["questions"]: byunit[q["unit"]].append(q)
def was_read(q):
    qs = byunit[q["unit"]]; k = qs.index(q)
    return any(a <= k < b for a, b in readrng[q["unit"]])
rows = []; verd = {}
for q in bank["questions"]:
    i = q["id"]; m = mech[i]; mk = m.get("marks") or {}; auto = []
    if m.get("rec"):
        if m.get("error") or not mk: auto.append(("HIGH", "Picture problem", "The app's picture could not be drawn for this question in the audit run (%s)." % (m.get("error") or "no record")))
        else:
            if not mk.get("cardOk"):
                auto.append(("HIGH" if not mk.get("clipOk") else "MEDIUM", "Picture problem", "No cropped picture is drawn for this citation: the app falls back to %s." % ("the whole page with no highlight" if not mk.get("clipOk") else (mk.get("cardNote") or "text"))))
            g = m.get("gold") or {}
            if mk.get("cardOk") and not g.get("crop") and i not in silence and m["type"] != "chapter_finder":
                auto.append(("MEDIUM", "Highlight misses the proof", "The cropped picture has no highlight at all (no gold anywhere in it)."))
            if g.get("page") and not any(g["page"]) and i not in silence and m["type"] != "chapter_finder":
                auto.append(("MEDIUM", "Highlight misses the proof", "The whole-page picture has no highlight at all."))
            px = mk.get("crop_px") or [0, 0]
            if px[1] and px[1] > 1500 and i not in silence: auto.append(("LOW", "Picture problem", "The cropped picture is very tall (%d points, about %.1f phone screens), so the cited line is small inside a long picture." % (px[1] // 2, px[1] / 2 / 800)))
            if m.get("tableNoTitle") and i not in silence: auto.append(("LOW", "Picture problem", "A table row is shown without the table's title or column headings%s, so the picture alone does not say what the numbers are." % (" (they are on the previous page of the booklet, so the whole-page picture does not show them either)" if m.get("citedOnPage") is False else "")))
            if m.get("citedOnPage") is False and i not in silence and not m.get("tableNoTitle") and not q["citation"]["section"].lower().startswith(("table", "figure")): auto.append(("MEDIUM", "Wrong page or citation", "The cited section number is not found in the text of the cited page."))
    nav = m.get("nav")
    if nav and nav.get("agree") is False: auto.append(("HIGH", "Wrong chapter", "The chapter named in the keyed answer (%s) is not the chapter the citation points to (%s)." % (nav["keyedChapter"], nav["citedChapter"])))
    g = m.get("guide")
    if g and g["status"] != "same" and q["type"] != "chapter_finder":
        what = "is not in the study guide PDF word for word (the bank's wording was changed after that guide was printed)" if g["status"] == "not in guide" else "differs from the study guide in %s" % ("option(s) %s" % ", ".join(g["optdiff"]) if g.get("optdiff") else "the key letter")
        auto.append(("LOW", "Differs from the study guide", "The question %s. Report only; nothing was changed." % what))
    man = flags.get(i, [])
    sev = max([SEV[x["severity"]] for x in man] + [SEV[a[0]] for a in auto] + [0])
    kinds = []; reasons = []; recs = []
    for x in man:
        for k in x["kinds"]:
            if k not in kinds: kinds.append(k)
        if x["reason"]: reasons.append(x["reason"])
        if x["recommendation"]: recs.append(x["recommendation"])
    for s, k, r in auto:
        if k not in kinds: kinds.append(k)
        reasons.append(r)
    sevname = {3: "HIGH", 2: "MEDIUM", 1: "LOW", 0: ""}[sev]
    c = q["citation"]
    v = {"verdict": "FLAG" if sev else "OK", "severity": sevname, "kinds": kinds, "reason": " ".join(reasons), "recommendation": " ".join(recs),
         "basis": "read" if (was_read(q) or man) else "mech"}
    verd[i] = v
    unit = units[q["unit"]]
    rows.append({"id": i, "unit": unit["label"], "unit_title": unit["title"], "position": byunit[q["unit"]].index(q) + 1, "type": q["type"], "kind": q.get("kind", ""), "source": "county amendments" if c["source"] == "amendment" else "IFC 2021",
                 "citation": (mk.get("ptr") or c.get("label", "")), "cited_pages": (mk.get("pageLine") or ""), "question": q["question"], "A": q["options"]["A"], "B": q["options"]["B"], "C": q["options"]["C"], "D": q["options"]["D"], "key": q["answer"], "key_text": q["options"][q["answer"]],
                 "verdict": v["verdict"], "severity": sevname, "kinds": "; ".join(kinds), "reason": v["reason"], "recommendation": v["recommendation"], "checked_by": v["basis"],
                 "marks_rule": (mk.get("verdict", "") + (" (%s)" % mk.get("how") if mk.get("how") not in (None, "", "numbers") else "")) if mk else "", "highlight_text": " / ".join((mk.get("text") or [])[:4])[:300] if mk else "",
                 "crop_px": "x".join(map(str, mk.get("crop_px") or [])) if mk else "", "guide": (g or {}).get("status", "")})
json.dump(verd, open(os.path.join(OUT, "verdicts.json"), "w"))
cols = list(rows[0].keys())
with open(os.path.join(OUT, "verdicts.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
# ---------------------------------------------------------------- INDEX.md
cnt = collections.Counter((r["severity"] or "OK") for r in rows)
lines = ["# Question audit: every verdict", "", "Counts: **OK %d**, FLAG HIGH %d, MEDIUM %d, LOW %d (total %d)." % (cnt["OK"], cnt["HIGH"], cnt["MEDIUM"], cnt["LOW"], len(rows)), ""]
perunit = []
for uid in sorted(byunit, key=lambda u: order[u]):
    rs = [r for r in rows if units[uid]["label"] == r["unit"]]
    c2 = collections.Counter((r["severity"] or "OK") for r in rs)
    perunit.append((units[uid], len(rs), c2))
lines += ["| Unit | Title | Questions | OK | HIGH | MEDIUM | LOW |", "|---|---|---|---|---|---|---|"]
for u, n, c2 in perunit: lines.append("| %s | %s | %d | %d | %d | %d | %d |" % (u["label"], u["title"], n, c2["OK"], c2["HIGH"], c2["MEDIUM"], c2["LOW"]))
lines += ["", "## Every flagged question (all severities)", "", "| id | unit | severity | kinds | reason (short) |", "|---|---|---|---|---|"]
for r in sorted([r for r in rows if r["severity"]], key=lambda r: (-SEV[r["severity"]], order[next(u for u in units if units[u]["label"] == r["unit"])], r["position"])):
    lines.append("| %s | %s | %s | %s | %s |" % (r["id"], r["unit"], r["severity"], r["kinds"], re.sub(r"\s+", " ", r["reason"])[:220].replace("|", "/")))
open(os.path.join(OUT, "INDEX.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("OK %d  HIGH %d  MEDIUM %d  LOW %d" % (cnt["OK"], cnt["HIGH"], cnt["MEDIUM"], cnt["LOW"]))
