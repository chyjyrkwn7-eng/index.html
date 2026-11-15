#!/usr/bin/env python3
"""Build 384, the code pictures: a table row's darker gold is the row asked about, all of it.

Found going through every Fire Code citation's picture for Madison ("I need 1000 percent confirmation that it's good to go"): of the
44 citations that point at a table row,
  - Table 1017.2 "row: B" put the gold on the raised note letter "b" in "250 b", a row above row B (the row finder took the first
    print that spelled the label, and a raised letter spells "b");
  - in a table of three or more columns the gold ran from the label to the one cell nearest it, so half the row was marked
    (Table 1006.3.4(1), 3206.2, 5104.3.2, 5704.4.2 ...);
  - a row of two or three lines (Table 906.3(1) "Maximum floor area / per unit of A", D103.4's three-line turnarounds) was marked on
    the label's line only, a thin stripe through the middle of a cell.
The painter now fills a row from rule to rule (ruleBand / sideRules / mergedLabel in ifc/ifc-viewer.js, read off the picture's
pixels, looked at for all 44); this gate holds the part of it that is decided from the book's text, through the app's own kit:
(1) Table 1017.2 row B: the gold is on row B - its label "B", "200" and "300" - and on nothing in the rows above or below it;
(2) every row citation: the gold runs across the whole row - every line of print in the table whose letters stand half or more
    inside the gold's height, right of the label, is inside the gold's width;
(3) every row citation: the gold carries its reach (the next row's start above and below it, or the table's edge), so the painter
    can fill a row of several lines to its rules without passing into another row;
(4) every row citation: the gold's label is print the size of the table's cells, never a raised note letter.
(5) (384.97) the answers once marked as a cell (IFC_POINTER_PATCH `rows: true`: read from index.html, the bank's pointer with the patch over it) are each one
    row mark, and the keyed answer's words are printed in that row; (0)-(4) hold for them too. Against origin/main (0) and (5) FAIL on the four.
  PDFJS_DIR=<pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-tablerows.py [--against FILE|REV]
  --against takes an ifc-viewer.js file or a commit (its ifc/ifc-viewer.js). Against 4dfd194 (before this): (1), (2), (3) and (4) FAIL.
The book never goes into the repo; it is read where it lies."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/")
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "/legacy/build/pdf.mjs") or not os.path.isfile(BOOK):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF"); sys.exit(0)
tmp = tempfile.mkdtemp(prefix="b384rows-")
kit = os.path.join(ROOT, "ifc", "ifc-viewer.js")
if "--against" in sys.argv:
    a = sys.argv[sys.argv.index("--against") + 1]
    if os.path.isfile(a): kit = a
    else:
        kit = os.path.join(tmp, "old-viewer.js")
        open(kit, "w", encoding="utf-8").write(subprocess.check_output(["git", "-C", ROOT, "show", a + ":ifc/ifc-viewer.js"], text=True))
kitm = os.path.join(tmp, "kit.mjs"); open(kitm, "w", encoding="utf-8").write(open(kit, encoding="utf-8").read())
RUN = r"""
import fs from "fs";
const [PDFJS, BOOK, KIT, BANK, APP] = process.argv.slice(2);
// (384.97) the app's pointer patches (IFC_POINTER_PATCH in index.html): a pointer with `rows: true` has its table cells marked as their rows - a row citation too
const app = fs.readFileSync(APP, "utf8"), pb = app.slice(app.indexOf("const IFC_POINTER_PATCH = {") + "const IFC_POINTER_PATCH = ".length);
const PATCH = Function("return " + pb.slice(0, pb.indexOf("\n};") + 2))();
const pdfjs = await import(PDFJS + "/legacy/build/pdf.mjs");
const V = await import(KIT);
const bs = fs.readFileSync(BANK, "utf8"), bank = JSON.parse(bs.slice(bs.indexOf("{"), bs.lastIndexOf("}") + 1));
const doc = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(BOOK)), isEvalSupported: false, verbosity: 0, useSystemFonts: true, disableFontFace: true }).promise;
const fb = new Map(), cache = new Map();
const index = await V.buildIndex(doc, { fontBold: fb, cache });
const out = [];
for (const q of bank.questions) {
  const c = Object.assign({}, q.citation, PATCH[q.id] || {}); delete c.head;
  if (!(c.row || c.rows) || c.source === "amendment") continue;
  const loc = V.locate(index, c);
  const clip = loc.ok ? await V.computeClip(doc, index, loc, c, { cache, fontBold: fb }) : { ok: false };
  const r = { id: q.id, label: c.label, row: c.row || c.rows, cells: !!c.rows, answer: q.options[q.answer], ok: !!clip.ok, marks: [] };
  if (clip.ok) {
    for (const m of clip.marks.filter(m => m.kind === "row")) {
      const model = await V.pageModel(doc, m.page, fb, cache);
      const mx = (m.x0 + m.x1) / 2, my = (m.i0 + m.i1) / 2;           // (the piece the row is in: a section's text and its table can be two pieces of one page)
      const seg = clip.segments.find(s => s.page === m.page && mx >= s.x0 && mx <= s.x1 && my >= s.y0 && my <= s.y1) || clip.segments.find(s => s.page === m.page) || {};
      const items = model.items.filter(it => it.t && it.y >= (seg.y0 ?? -1e9) && it.y <= (seg.y1 ?? 1e9) && it.x + it.w / 2 >= (seg.x0 ?? -1e9) && it.x + it.w / 2 <= (seg.x1 ?? 1e9))
        .map(it => ({ t: it.t, x: it.x, y: it.y, w: it.w, h: it.h }));
      r.marks.push({ x0: m.x0, x1: m.x1, i0: m.i0, i1: m.i1, fs: m.fs, lt: m.lt ?? null, lb: m.lb ?? null, items });
    }
  }
  out.push(r);
}
console.log(JSON.stringify(out));
"""
runner = os.path.join(tmp, "run.mjs"); open(runner, "w").write(RUN)
res = subprocess.run(["node", runner, PDFJS, BOOK, kitm, os.path.join(ROOT, "ifc", "bank.js"), os.path.join(ROOT, "index.html")], capture_output=True, text=True, timeout=1800)
if res.returncode != 0:
    print(res.stderr[-1500:]); print("FAIL the kit ran"); sys.exit(1)
rows = json.loads(res.stdout.strip().splitlines()[-1])
ASC, DSC = 0.69, 0.21   # the kit's MARK_INK for the book (tallest letters / descenders, in ems)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
def inside(m, it):
    a0, a1 = it["y"] - DSC * it["h"], it["y"] + ASC * it["h"]
    ov = min(a1, m["i1"]) - max(a0, m["i0"])
    return ov >= 0.5 * (a1 - a0)
print("%d row citations, %d drew" % (len(rows), sum(r["ok"] for r in rows)))
chk("(0) every row citation draws its picture with a row mark", all(r["ok"] and r["marks"] for r in rows), [r["id"] for r in rows if not (r["ok"] and r["marks"])])
# (1) Table 1017.2, row B
b = next((r for r in rows if r["id"] == "ch10-061"), None)
m = b["marks"][0] if b and b["marks"] else None
got = sorted({it["t"].strip() for it in (m["items"] if m else []) if inside(m, it) and it["x"] + it["w"] / 2 >= m["x0"] and it["x"] + it["w"] / 2 <= m["x1"] and it["h"] >= 0.8 * m["fs"]}) if m else []
chk("(1) Table 1017.2 row B: the gold is on row B's label, 200 and 300 (%s), nothing in another row" % got,
    m is not None and {"B", "200"} <= set(got) and any(g.startswith("300") for g in got) and not any(g in ("I-1", "Not Permitted", "250") for g in got), got)
# (2) the whole row
short = []
for r in rows:
    for m in r["marks"]:
        lab = min((it for it in m["items"] if inside(m, it) and it["x"] >= m["x0"] - 1), key=lambda it: it["x"], default=None)
        if not lab: continue
        miss = [it["t"] for it in m["items"] if it["h"] >= 0.8 * m["fs"] and inside(m, it) and it["x"] >= lab["x"] and (it["x"] < m["x0"] - 1 or it["x"] + it["w"] > m["x1"] + 1)]
        if miss: short.append((r["id"], miss[:4]))
chk("(2) every row's gold runs across the whole row (%d of %d rows short)" % (len(short), sum(len(r["marks"]) for r in rows)), not short, short[:8])
# (3) the reach
noreach = [(r["id"], m["lt"], m["lb"]) for r in rows for m in r["marks"] if m["lt"] is None or m["lb"] is None or m["lt"] < m["i1"] - 0.5 or m["lb"] > m["i0"] + 0.5]
chk("(3) every row's gold carries its reach, enclosing it (the next row's start or the table's edge)", not noreach, noreach[:8])
# (4) never a raised letter for a label
raised = []
for r in rows:
    for m in r["marks"]:
        cells = sorted(it["h"] for it in m["items"] if it["t"].strip()); med = cells[len(cells) // 2] if cells else 0
        if m["fs"] < 0.8 * med: raised.append((r["id"], round(m["fs"], 1), med))
chk("(4) every row's gold is labelled by print the size of the table's cells, never a raised note letter", not raised, raised[:8])
# (5) (384.97) the answers that were marked as one cell are marked as their row (IFC_POINTER_PATCH rows: true): one row mark, and the keyed answer's words
# are printed inside it - the row is the one that holds the answer (the rest of the row, border to border and no other row, is (2) here and check-b384-cropfix (g))
import re as _re
conv = [r for r in rows if r.get("cells")]
wrong = []
for r in conv:
    if len(r["marks"]) != 1: wrong.append((r["id"], "%d row marks" % len(r["marks"]))); continue
    m = r["marks"][0]
    txt = " ".join(it["t"] for it in m["items"] if inside(m, it) and it["x"] + it["w"] / 2 >= m["x0"] - 1 and it["x"] + it["w"] / 2 <= m["x1"] + 1).lower()
    miss = [t for t in _re.findall(r"[a-z0-9]+", r["answer"].lower()) if t not in txt]
    if miss: wrong.append((r["id"], r["answer"], "not in the row", miss, txt[:120]))
chk("(5) the %d answers once marked as a cell (%s) are each one row mark, and the keyed answer is printed in that row" % (len(conv), ", ".join(r["id"] for r in conv)), len(conv) >= 4 and not wrong, wrong)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
