#!/usr/bin/env python3
"""Build 384, the county code pictures: a table row's gold covers the whole row, every line of its first cell.

Found going through the Fire Code code pictures for Madison: Harris County Table 5609.4.1's last row ("Motor vehicles fuel-dispensing
station dispensers or Retail propane / dispensing station dispenser | 100 ft.") was marked on the first line and the "100 ft." beside
it, and the second line of the same cell was left outside the gold - a band cutting through a sentence. The booklet prints a cell's
value centred between the two lines of its neighbour, and the text layer lists lines top to bottom, so "100 ft." sorted BETWEEN the
two lines and the row's first cell was found as its first line alone. countyChars now reads a line that stands right of both its
neighbours and between them after them (the same fix also takes in Table 105.5.9's "... enrichment / systems" line).
For every county citation whose highlight is a row ("cell | cell"): each printed line of the booklet near the gold whose words are
part of the highlight is inside the gold's height.
  PDFJS_DIR=<pdfjs-dist 5.4.149> python3 tools/check-b384-countyrows.py [--against FILE|REV]
  --against takes an ifc-viewer.js file or a commit (its ifc/ifc-viewer.js). Against 670de9c (before this) it FAILS (Table 5609.4.1, 105.5.9)."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/")
if not os.path.exists(PDFJS + "/legacy/build/pdf.mjs"):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149"); sys.exit(0)
tmp = tempfile.mkdtemp(prefix="b384crow-")
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
const [PDFJS, PDF, KIT, BANK] = process.argv.slice(2);
const pdfjs = await import(PDFJS + "/legacy/build/pdf.mjs");
const V = await import(KIT);
const bs = fs.readFileSync(BANK, "utf8"), bank = JSON.parse(bs.slice(bs.indexOf("{"), bs.lastIndexOf("}") + 1));
const doc = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(PDF)), isEvalSupported: false, verbosity: 0, useSystemFonts: true, disableFontFace: true }).promise;
const nz = s => String(s).toLowerCase().replace(/[^a-z0-9]/g, "");
const seen = new Set(), out = [];
for (const q of bank.questions) {
  const c = q.citation;
  if (c.source !== "amendment" || !/ \| /.test(String(c.highlight))) continue;
  const key = JSON.stringify([c.section, c.pdfPage, c.highlight]); if (seen.has(key)) continue; seen.add(key);
  const clip = await V.countyClip(doc, c, { cache: new Map() });
  if (!clip.ok) { out.push({ id: q.id, section: c.section, ok: false }); continue; }
  const tc = await (await doc.getPage(c.pdfPage)).getTextContent();
  const H = nz(c.highlight);
  const count = new Map(); for (const it of tc.items) count.set(nz(it.str), (count.get(nz(it.str)) || 0) + 1);
  const items = tc.items.filter(it => nz(it.str).length >= 6 && count.get(nz(it.str)) === 1 && H.includes(nz(it.str))).map(it => ({ t: it.str, y: it.transform[5], h: it.height || 11 }));
  out.push({ id: q.id, section: c.section, ok: true, page: c.pdfPage, marks: clip.marks.filter(m => m.page === c.pdfPage).map(m => ({ i0: m.i0, i1: m.i1, fs: m.fs })), items });
}
console.log(JSON.stringify(out));
"""
runner = os.path.join(tmp, "run.mjs"); open(runner, "w").write(RUN)
res = subprocess.run(["node", runner, PDFJS, os.path.join(ROOT, "ifc", "harris-county-amendments.pdf"), kitm, os.path.join(ROOT, "ifc", "bank.js")], capture_output=True, text=True, timeout=1800)
if res.returncode != 0:
    print(res.stderr[-1500:]); print("FAIL the kit ran"); sys.exit(1)
rows = json.loads(res.stdout.strip().splitlines()[-1])
bad = []
for r in rows:
    if not r["ok"] or not r["marks"]: bad.append((r["id"], "no mark")); continue
    for m in r["marks"]:
        # the lines of the row: printed lines (of the highlight's words, each printed once on the page) that stand within the gold's span widened by one line either way
        near = [it for it in r["items"] if m["i0"] - 1.3 * m["fs"] <= it["y"] <= m["i1"] + 1.3 * m["fs"]]
        miss = [it["t"] for it in near if not (m["i0"] <= it["y"] <= m["i1"])]   # the line's baseline is inside the gold
        if miss: bad.append((r["id"], r["section"], miss[:3]))
print("%d county row citations" % len(rows))
ok = not bad
print(("PASS " if ok else "FAIL ") + "every line of a county row's first cell is inside the gold" + ("" if ok else "  -> " + str(bad)[:700]))
print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)
