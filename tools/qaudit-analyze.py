#!/usr/bin/env python3
"""Question audit, step 2: the machine half of the verdicts. Reads the bank, the records tools/qaudit-render.py wrote, and (optionally) the text of
the study guide and the books; writes one JSON of signals per question. Nothing here changes a question: it REPORTS.

Signals per question (every one is a fact read off the data, the judgement is the reader's in the next step):
  marks      the gold marks' verdict (the 384.56 rule: do the marks cover the words that decide the keyed answer?) and what is marked
  page       the cited section / table / excerpt is printed on the cited PDF page(s); the printed page label is on that page
  gold       strong-gold pixels in the code picture and in the whole-page picture (0 = no highlight drawn)
  chapter    the citation's chapter is the unit's chapter (the chapter finder: the keyed chapter is the cited one)
  guide      the question, options and key against the study guide (words and numbers; "not in guide" = added or reworded since)
  spelling   words in the question / options / explanation that are in no dictionary, no book text and no other question
  article    "a / an _____": the article fits only some options (a cue that gives the answer, or rules a distractor out)
  options    identical options, one option inside another, "all of the above"
  repeats    another question with the same cited place and the same key, or the same wording; the key printed in another question's stem
Run: python3 tools/qaudit-analyze.py RAWDIR OUT.json --bank ifc/bank.js [--guide sg.json] [--book-text ifc.txt] [--county-text c.txt]"""
import os, sys, json, re, collections, difflib, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import qaudit_lib as L
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
RAW, OUT = sys.argv[1], sys.argv[2]
bs = open(arg("--bank"), encoding="utf-8").read(); bank = json.loads(bs[bs.index("{"): bs.rindex("}") + 1])
units = {u["id"]: u for u in bank["units"]}
Q = bank["questions"]
def nrm(x): return re.sub(r"\s+", " ", str(x).replace("’", "'").replace("—", "-").replace("–", "-").replace("“", '"').replace("”", '"')).strip()
guide = json.load(open(arg("--guide"))) if arg("--guide") else []
book_pages = open(arg("--book-text"), encoding="utf-8", errors="ignore").read().split("\f") if arg("--book-text") else []
county_pages = open(arg("--county-text"), encoding="utf-8", errors="ignore").read().split("\f") if arg("--county-text") else []
try:
    import numpy as np
    from PIL import Image
except Exception:
    np = None
# ---------------------------------------------------------------- the study guide
gi = {}
for r in guide: gi.setdefault(nrm(r["q"]), []).append(r)
def guide_cmp(q):
    m = gi.get(nrm(q["question"]))
    if not m: return {"status": "not in guide"}
    best = None
    for r in m:
        d = [l for l in "ABCD" if nrm(r["opts"][l]) != nrm(q["options"][l])]
        sc = len(d) + (r["ans"] != q["answer"])
        if best is None or sc < best[0]: best = (sc, r, d)
    sc, r, d = best
    return {"status": "same" if sc == 0 else "differs", "guide": "%s-%s" % (r["chap"], r["n"]), "optdiff": d, "ansdiff": r["ans"] != q["answer"], "explSame": nrm(r["expl"]) == nrm(q["explanation"]),
            "guideExpl": r["expl"] if nrm(r["expl"]) != nrm(q["explanation"]) else None}
# ---------------------------------------------------------------- spelling
vocab = set()
try:
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", "pylib"))
    from spellchecker import SpellChecker
    SC = SpellChecker()
except Exception:
    SC = None
for t in book_pages + county_pages:
    for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", t): vocab.add(w.lower().strip("'-"))
for r in guide:
    pass
wc = collections.Counter()
def words(s): return [w.lower().strip("'-") for w in re.findall(r"[A-Za-z][A-Za-z'’\-]*", str(s).replace("’", "'"))]
for q in Q:
    for s in [q["question"]] + list(q["options"].values()) + [q["explanation"]]:
        for w in words(s): wc[w] += 1
def spelling(q):
    out = []
    for field, s in [("question", q["question"])] + [("option " + k, v) for k, v in q["options"].items()] + [("explanation", q["explanation"])]:
        for w in words(s):
            if len(w) < 4 or w in vocab: continue
            if SC is not None and not SC.unknown([w]): continue
            if SC is not None and "-" in w and not SC.unknown(w.split("-")): continue
            if wc[w] >= 3: continue                                    # a word used three times in the bank is a term, not a slip
            out.append((field, w))
    return out
# ---------------------------------------------------------------- "a / an _____"
def starts_vowel_sound(opt):
    o = nrm(opt).lower().lstrip("\"'(")
    if not o: return None
    m = re.match(r"[a-z0-9$½¼¾]+", o)
    w = m.group(0) if m else o
    if w[0].isdigit():
        n = re.match(r"\d+", w).group(0)
        return n[0] == "8" or n in ("11", "18")                       # eight, eighty, eight hundred, eleven, eighteen
    if w.startswith(("hour", "honest", "honor", "heir")): return True
    if w.startswith(("uni", "use", "usa", "eu", "one", "once", "uro", "ut")) and not w.startswith("unin"): return False
    if w.startswith(("un", "up")) and w[:3] != "uni": return True
    return w[0] in "aeiou"
def article_cue(q):
    m = re.search(r"\b(a|an)\s+_{3,}", q["question"], re.I)
    if not m: return None
    art = m.group(1).lower()
    fits = {}
    for k, v in q["options"].items():
        vs = starts_vowel_sound(v)
        if vs is None: return None
        fits[k] = (art == "an") == vs
    n = sum(fits.values())
    if n == 4: return None
    return {"article": art, "fits": [k for k, f in fits.items() if f], "keyFits": fits[q["answer"]], "n": n}
# ---------------------------------------------------------------- options
def option_issues(q):
    out = []
    o = {k: nrm(v).lower() for k, v in q["options"].items()}
    for a, b in itertools.combinations(o, 2):
        if o[a] == o[b]: out.append("options %s and %s are the same" % (a, b))
        elif len(o[a]) > 3 and len(o[b]) > 3 and (re.search(r"\b" + re.escape(o[a]) + r"\b", o[b]) or re.search(r"\b" + re.escape(o[b]) + r"\b", o[a])): out.append("one of %s / %s sits inside the other" % (a, b))
    if any(re.search(r"above|none of the|all of the|both", v) for v in o.values()): out.append("an 'above / none / all / both' option")
    nb = len(re.findall(r"_{3,}", q["question"]))
    if nb > 1: out.append("%d blanks in the stem" % nb)
    return out
# ---------------------------------------------------------------- repeats and leaks
def stem_key(q): return " ".join(L.toks(re.sub(r"_{3,}", " blank ", q["question"])))
SK = {q["id"]: stem_key(q) for q in Q}
SET = {i: set(s.split()) for i, s in SK.items()}
def cite_key(q):
    c = q["citation"]
    return (c["source"], str(c["section"]), str(c.get("exception") or ""), json.dumps(c.get("row") or c.get("entry") or ""), json.dumps(c.get("find") or c.get("highlight") or ""))
repeats = collections.defaultdict(list)
byans = collections.defaultdict(list)
for q in Q:
    if q["type"] == "chapter_finder": continue
    byans[(cite_key(q)[:3], " ".join(L.toks(q["options"][q["answer"]])))].append(q["id"])
# the same cited place, a key that is the same fact written two ways ("3" / "3 hours"), and a stem that shares its words: the same question asked twice
bycite = collections.defaultdict(list)
for q in Q:
    if q["type"] != "chapter_finder": bycite[cite_key(q)[:3]].append(q)
for k, qs_ in bycite.items():
    for qa, qb in itertools.combinations(qs_, 2):
        ta, tb = set(L.toks(qa["options"][qa["answer"]])), set(L.toks(qb["options"][qb["answer"]]))
        if not ta or not tb or not (ta <= tb or tb <= ta) or not any(w.isdigit() or len(w) > 3 for w in (ta & tb)): continue
        A, B = set(stem_key(qa).split()), set(stem_key(qb).split())
        if len(A & B) / max(1, len(A | B)) >= 0.45:
            repeats[qa["id"]].append(("same cited place, same key and similar stem:", qb["id"])); repeats[qb["id"]].append(("same cited place, same key and similar stem:", qa["id"]))
for k, ids in byans.items():
    if len(ids) > 1:
        for a in ids:
            for b in ids:
                if a != b: repeats[a].append(("same place and same key as", b))
ids = [q["id"] for q in Q]
qmap0 = {q["id"]: q for q in Q}
for a, b in itertools.combinations(ids, 2):
    A, B = SET[a], SET[b]
    if len(A) < 5 or len(B) < 5: continue
    j = len(A & B) / len(A | B)
    if j >= 0.72:
        qa, qb = qmap0[a], qmap0[b]
        ka, kb = " ".join(L.toks(qa["options"][qa["answer"]])), " ".join(L.toks(qb["options"][qb["answer"]]))
        if j >= 0.85 or ka == kb:                                       # a template ("... Class I liquids ... in excess of") with another key is a sibling question, not a repeat
            tag = "near-identical wording%s to (%.0f%%)" % (" and the same key" if ka == kb else "", 100 * j)
            repeats[a].append((tag, b)); repeats[b].append((tag, a))
# the key printed in another question's stem (same unit; a quantity or a 2+ word phrase)
qmap = {q["id"]: q for q in Q}
leaks = collections.defaultdict(list)
for q in Q:
    if q["type"] == "chapter_finder": continue
    key = nrm(q["options"][q["answer"]]).lower().rstrip(".")
    if len(key) < 6 or len(key.split()) < 2 and not re.search(r"\d", key): continue
    for p in Q:
        if p["id"] == q["id"] or p["unit"] != q["unit"] or p["type"] == "chapter_finder": continue
        if p["citation"]["section"] != q["citation"]["section"] or (q["citation"]["section"] == "202" and p["citation"].get("heading") != q["citation"].get("heading")): continue
        if re.search(r"(?<![\w$])" + re.escape(key) + r"(?![\w])", nrm(p["question"]).lower()):
            leaks[q["id"]].append(p["id"])
# ---------------------------------------------------------------- chapters
def chap_of(c):
    sec = str(c["section"]).strip()
    m = re.match(r"^(chapter|appendix|exhibit)\s+(\w+)", sec, re.I)
    if m:
        k = m.group(1).lower(); v = m.group(2)
        return ("App" + v) if k == "appendix" else ("Exh" + v) if k == "exhibit" else v.lstrip("0")
    m = re.match(r"^(?:table|figure)\s+([A-Z]?)(\d+)", sec, re.I)
    if m:
        if m.group(1): return "App" + m.group(1).upper()
        n = m.group(2); return n[:-2] if len(n) >= 3 else n
    m = re.match(r"^([A-J])\d", sec)
    if m: return "App" + m.group(1)
    m = re.match(r"^(\d+)", sec)
    if m:
        n = m.group(1); return n if len(n) <= 2 else n[:-2]
    return "?"
def chapter_in_text(s):
    m = re.search(r"Chapter\s+(\d+)", s)
    if m: return m.group(1)
    m = re.search(r"Appendix\s+([A-J])", s)
    return "App" + m.group(1) if m else None
# ---------------------------------------------------------------- the pictures
def gold(path):
    if np is None or not os.path.exists(path): return None
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    return int(((a[..., 0] >= 235) & (a[..., 1] < 232) & (a[..., 2] < 95)).sum())
def cited_on_page(q, rec):
    c = q["citation"]; sec = str(c["section"]); pages = rec.get("pagesText") or []
    txt = " ".join(pages) + " " + (rec.get("clipText") or "")
    if c["source"] == "amendment":
        key = nrm(c.get("highlight") or c.get("excerpt") or "")[:60]
        t = nrm(txt)
        if key and key in t: return True
        if re.match(r"^(chapter|exhibit)", sec, re.I): return sec.split()[0].lower() in t.lower()
        return sec in t
    t = nrm(txt).lower()
    if re.match(r"^(chapter|appendix)\s", sec, re.I): return sec.split()[0].lower() in t
    if sec == "202": return True
    return sec.lower() in t or nrm(sec).lower().replace("table ", "").replace("figure ", "") in t
def label_on_page(q):
    c = q["citation"]
    if c["source"] != "ifc" or not c.get("printedPage") or not book_pages: return None
    p = c["pdfPage"]
    if p - 1 >= len(book_pages): return None
    return c["printedPage"] in book_pages[p - 1]
res = {}
for q in Q:
    i = q["id"]; c = q["citation"]; u = q["unit"]; sig = {"unit": u, "section": c["section"], "source": c["source"], "type": q["type"], "flags": []}
    sig["guide"] = guide_cmp(q) if guide else None
    sig["spelling"] = spelling(q)
    sig["article"] = article_cue(q)
    sig["options"] = option_issues(q)
    sig["repeats"] = repeats.get(i, []); sig["leaks"] = leaks.get(i, [])
    sig["chapterOf"] = chap_of(c); sig["chapterFit"] = (u == "NAV") or chap_of(c) == u
    if u == "NAV":
        kopt = q["options"][q["answer"]]; kc = chapter_in_text(kopt)
        ck = chap_of(c)
        sig["nav"] = {"keyedChapter": kc, "citedChapter": ck, "agree": (kc == ck) if kc else None}
    sig["labelOnPage"] = label_on_page(q)
    rp = os.path.join(RAW, i + ".json")
    if os.path.exists(rp):
        r = json.load(open(rp)); sig["rec"] = True
        if r.get("error"): sig["error"] = r["error"]
        else:
            if r.get("source") == "amendment" and r.get("clipOk"):
                # the county booklet's marks carry no readable text (its text layer sits in another frame): the gold is the bank's own `highlight` (a verbatim part of the excerpt), found on the page
                keys = [m for m in r.get("marks", []) if m["kind"] != "heading"]; heads = [m for m in r.get("marks", []) if m["kind"] == "heading"]
                hl = c.get("highlight") or ""
                r["marks"] = ([{"kind": "cite", "text": hl}] if keys and hl else []) + heads
                if not keys: sig["flags"].append("county: nothing marked")
            v = L.verdict(r) if r.get("source") == "ifc" or r.get("clipOk") else ("no clipping", "")
            sig["marks"] = {"verdict": v[0], "how": v[1], "n": len(r.get("marks", [])), "kinds": sorted({m["kind"] for m in r.get("marks", [])}),
                            "text": [m["text"] for m in r.get("marks", [])], "whole": bool(r.get("whole")), "truncated": bool(r.get("truncated")), "clipOk": bool(r.get("clipOk")),
                            "locKind": r.get("locKind"), "pages": r.get("pages"), "cardOk": bool((r.get("card") or {}).get("ok")), "cardText": bool((r.get("card") or {}).get("text")),
                            "cardNote": (r.get("card") or {}).get("note"), "ptr": r.get("ptr"), "pageLine": r.get("pageLine"), "crop_px": r.get("crop_px")}
            sig["citedOnPage"] = cited_on_page(q, r) if r.get("clipOk") or r.get("pagesText") else None
            sig["gold"] = {"crop": gold(os.path.join(RAW, i + ".crop.jpg")), "page": [gold(os.path.join(RAW, "%s.p%d.jpg" % (i, k))) for k in range(len(r.get("pages_meta", [])))]}
    else:
        sig["rec"] = False
    if sig.get("rec") and not sig.get("error") and c["source"] == "amendment" and " | " in (c.get("excerpt") or "") and " | " in (c.get("highlight") or ""):
        try: ct = json.load(open(rp)).get("clipText") or ""
        except Exception: ct = ""
        sig["tableNoTitle"] = not re.search(r"\bTABLE\b", ct, re.I)                    # a county table row shown without the table's title / column headings
    res[i] = sig
json.dump(res, open(OUT, "w"))
c = collections.Counter(s.get("marks", {}).get("verdict", "?") for s in res.values())
print("analysed %d; marks verdicts: %s" % (len(res), dict(c)))
