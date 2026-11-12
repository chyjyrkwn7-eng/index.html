"""The audit's rule for tools/check-b384-ifcmarks.py: does what an IFC question's clipping MARKS cover the words that decide the keyed answer?

record = what tools/b384-ifcmarks-page.js hands back for one question (the marked text of every gold mark, the clipping's text, the cited pages' text).
verdict(record) -> (verdict, how)   verdicts:
  OK                    the keyed answer's decisive words are inside a gold mark (the heading counts when it is itself the answer: a standard's
                        designation, a defined term); `how` says which rule held (numbers / phrase / words / computed)
  title only            the only gold is the section / table caption, and the answer's words are printed in the clipping
  marks nothing         no gold at all
  wrong place           gold marks text, but not the answer's: the answer's words are printed on the cited page(s), outside every mark
  answer not on page    the answer's words are not printed on the cited page(s) in any form this rule can read (a paraphrase, a computed answer it
                        cannot derive, a group named by a heading line): the mark cannot be shown to cover them; each is judged by hand in
                        tools/b384-ifcmarks-judged.json (the gate's EXCEPTIONS), one reason per id
  no clipping           the reference was not found in the book / only the whole page is shown
Rule. A quantity answer (V.answerNumbers: "18 inches", "50", "1,000") is covered when every one of its numbers is printed inside a mark (digits or the
book's spelled form), or can be COMPUTED from the marked numbers and the stem's own (a worked example: 9,000 gross sq ft / the marked 150 gross = 60).
Any other answer is covered when every content word of the keyed option is inside the marked text (a plural, a spelled number, "annually" for "every
year" count as the same word), or its whole text is; a group or class named by a code ("R-1", "Class IV") must be printed as that code.
"""
import re
from itertools import combinations

STOP = set("""a an the of or and to in on at by for with without from as is are be been was were it its this that these those than then not no any all each
every per into onto up down out over under between within when where which who whom what how may shall should must can will would could their there they them
his her also such if so either neither both more most less least only""".split())
ORGS = {"nfpa", "astm", "ul", "ansi", "asme", "awwa", "csa", "nema", "ieee", "api", "cga", "asce", "iapmo", "icc", "ufc"}
UNITW = {"zero": 0, "one": 1, "once": 1, "two": 2, "twice": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENSW = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
SYN = {"annually": "annual", "annual": "annual", "yearly": "annual", "semiannually": "semiannual", "semiannual": "semiannual", "prior": "before",
       "daily": "day", "weekly": "week", "monthly": "month", "quarterly": "quarter", "permitted": "allow", "allowed": "allow", "prohibited": "prohibit",
       "approved": "approve", "mm": "mm"}


def nz(s):
    return re.sub(r"[^a-z0-9]+", "", str(s).lower().replace("’", "'"))


def _pre(s):
    s = str(s).lower().replace("’", "'").replace("½", " 1/2 ").replace("¼", " 1/4 ").replace("¾", " 3/4 ")
    s = re.sub(r"(\d),(?=\d{3}(?!\d))", r"\1", s)
    s = re.sub(r"(\d)\s+(\d)\s*/\s*(\d)", r"\1 \2/\3", s)                  # "8 1 / 4" -> "8 1/4"
    s = re.sub(r"every\s+six\s+months|six[- ]month\s+interval", "semiannual", s)
    s = re.sub(r"every\s+(?:one\s+)?year|once\s+a\s+year|once\s+every\s+year|each\s+year|per\s+year", "annual", s)
    s = re.sub(r"every\s+(?:one\s+)?month|once\s+a\s+month|each\s+month", "month", s)
    s = re.sub(r"once\s+a\s+day|every\s+day|each\s+day", "day", s)
    return s


def toks(s):
    """canonical tokens: lower-case words, a spelled number as its digits, a few synonyms; word-final plural / -ed / -ing stripped"""
    out, raw = [], re.findall(r"\d+(?:\.\d+)?(?:/\d+)?|[a-z]+", _pre(s).replace("'", ""))
    i = 0
    while i < len(raw):
        w = raw[i]
        if w in TENSW:
            v = TENSW[w]
            if i + 1 < len(raw) and raw[i + 1] in UNITW and UNITW[raw[i + 1]] < 10: v += UNITW[raw[i + 1]]; i += 1
            out.append(str(v)); i += 1; continue
        if w in UNITW: out.append(str(UNITW[w])); i += 1; continue
        if w == "hundred" and out and out[-1].isdigit(): out[-1] = str(int(out[-1]) * 100); i += 1; continue
        out.append(SYN.get(w, _stem(w))); i += 1
    return out


def _stem(w):
    if w.isdigit() or "/" in w or "." in w: return w
    for suf in ("ies", "es", "s", "ed", "ing"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def numbers_in(s):
    t = _pre(s)
    out = []
    for m in re.finditer(r"(?<![\w.])(\d+(?:\.\d+)?)(?:\s+(\d+)/(\d+)|/(\d+))?", t):
        v = float(m.group(1))
        if m.group(2): v += int(m.group(2)) / int(m.group(3))
        elif m.group(4): v = v / int(m.group(4))
        out.append(v)
    out += [float(x) for x in re.findall(r"(?<![\w.])\d+(?![\d.])", t)] + [float(x) for x in re.findall(r"(?<=/)\d+", t)]      # the digits of a mixed number on their own ("4 1/2": 4, 1, 2)
    for w in toks(s):
        if w.isdigit(): out.append(float(w))
    return out


def has_number(text, n):
    n = float(n)
    return any(abs(v - n) < 1e-9 for v in numbers_in(text))


def computed(text, stem_text, ans):
    """can `ans` be got from numbers printed in the marked text and in the question's own stem (a worked example)? + - * / of a marked number with a stem number,
    of two stem numbers with a marked one, a percentage of it, rounded up / down"""
    A = float(ans)
    M = [v for v in numbers_in(text) if v > 0]
    S = [v for v in numbers_in(stem_text) if v > 0]
    if not M: return False
    def hit(x): return abs(x - A) < 1e-6 * max(1, A) or abs(round(x) - A) < 1e-9 or abs(int(x) - A) < 1e-9 or (x == int(x) + 0.0 and False)
    import math
    def near(x):
        return abs(x - A) < 1e-6 * max(1, abs(A)) or abs(math.ceil(x - 1e-9) - A) < 1e-9 or abs(math.floor(x + 1e-9) - A) < 1e-9
    sets = [(m, s) for m in M for s in S] + [(m, 0) for m in M]
    for m, s in sets:
        if s and any(near(x) for x in (s * m, s / m, m / s, s + m, abs(s - m), s * m / 100, s / (m / 100), m * s / 1000, s / m + 1)): return True
        if not s and any(near(x) for x in (m,)): return True
    for (s1, s2) in combinations(S, 2):
        for m in M:
            for base in (s1 + s2, abs(s1 - s2), s1 * s2):
                if any(near(x) for x in (base / m, base * m, base * m / 100)): return True
            for a, b in ((s1, s2), (s2, s1)):
                if near(a / b) or near(a / b * m) or near(a * m / b): return True
    for (m1, m2) in combinations(M, 2):
        for s in S + [1]:
            if any(near(x) for x in (s * m1 * m2, s * m1 / m2, s * m2 / m1, m1 + m2, m1 * m2, s / m1 * m2, s / m2 * m1)): return True
    return False


def covers(text, rec):
    """does `text` hold the keyed answer's decisive words? -> (bool, how)"""
    nums = rec.get("nums") or []
    if nums:
        return all(has_number(text, n) for n in nums), "numbers"
    opt = rec.get("ans") or ""
    codes = _codes(opt).split()                                     # a group or class named by its code ("R-1", "Class IV"): printed as that code
    if codes and not all(c in _codes(text).split() for c in codes): return False, "code"
    entry = rec.get("locKind") == "entry"
    ow = [w for w in toks(opt) if (w not in STOP or w.isdigit()) and not (entry and w in ORGS)]
    if codes: ow = [w for w in ow if len(w) > 1 and not w.isdigit() and not re.fullmatch(r"[ivx]+", w)]      # the code itself was checked above
    if not ow: return (True, "code") if codes else (False, "empty")
    if re.fullmatch(r"[A-Za-z0-9]{1,2}", opt.strip()):             # a short answer ("I", "H", "S") is a word of its own in the text, not letters inside other words
        return bool(re.search(r"(?<![A-Za-z0-9])" + re.escape(opt.strip()) + r"(?![A-Za-z0-9])", text)), "word"
    if nz(opt) and nz(opt) in nz(text): return True, "phrase"
    tw = set(toks(text))
    have = [w for w in ow if w in tw]
    return len(have) == len(ow), "words %d/%d" % (len(have), len(ow))


def _codes(text):
    """the group / class codes printed in a text ("R-1", "Class IV") as ' r1 ' words, so that "R-1" is found as itself and not as an "R" and a "1" far apart"""
    out = []
    for m in re.finditer(r"(?<![A-Za-z0-9])([A-Z]{1,2})[-–—]?(\d)(?![0-9])|(?<![A-Za-z0-9])(?:Class|Division|Type)\s+([IVX]{1,4}|[A-Z0-9]{1,3})(?![A-Za-z0-9])", text):
        out.append((m.group(1) + m.group(2)).lower() if m.group(1) else m.group(3).lower())
    return " " + " ".join(out) + " "


def marked_texts(rec):
    heads = [m for m in rec.get("marks", []) if m["kind"] == "heading"]
    keys = [m for m in rec.get("marks", []) if m["kind"] != "heading"]
    return heads, keys


def verdict(rec):
    if rec.get("error") or rec.get("nobook"): return "error", rec.get("error", "no book")
    if not rec.get("locOk") or rec.get("locKind") == "pages" or not rec.get("clipOk"): return "no clipping", ""
    heads, keys = marked_texts(rec)
    marked = " ".join(m["text"] for m in heads + keys)          # a heading that itself holds the answer (a standard's designation, a defined term) is a mark of it
    page = " ".join(rec.get("pagesText", [])) + " " + rec.get("clipText", "")
    ok, how = covers(marked, rec) if (keys or heads) else (False, "none")
    if ok: return "OK", how
    if rec.get("nums") and len(rec["nums"]) == 1 and keys and computed(" ".join(m["text"] for m in keys), rec.get("stem", ""), rec["nums"][0]):
        return "OK", "computed"
    onpage, how2 = covers(page, rec)
    if not onpage: return "answer not on page", ("no marks; " if not keys else "") + how2
    if not keys: return ("title only" if heads else "marks nothing"), how2
    return "wrong place", how
