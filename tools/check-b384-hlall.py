#!/usr/bin/env python3
"""Build 384 (r15), THE HIGHLIGHTS, EVERY CITATION: the soft highlight of the whole page and the picture in the card, checked for every distinct
citation of the Fire Code bank - 410 county, 1,368 book - not for a sample.

Madison, over and over: "Why is the entire code not highlighted in full page?", "Why are the tables not fully highlighted in full page?",
"Should be symmetrical there", "I need you to fix every single question". The rules this holds every citation to:
  * THE WHOLE PROVISION IS TINTED on the whole page: its heading through its last sub-item and exceptions; a table from its title to its last row
    and notes; an entry; a section title with the first provision under it. It ends at the next heading, not at the line the answer is on.
  * the picture in the card never ends inside a sentence or a list item, shows no line the page does not highlight, and is never two disjoint
    pieces (a standard's organisation heading far above its entry);
  * ONE LOOK: one soft tint and one deeper gold across every highlight (county and book, card and page), the soft block running the width of its
    text column (a table: its own rules), a centred heading sitting centred in its block (equal margins left and right), the same padding on every
    block, nothing tinted outside the provision, the deeper marks inside the soft block.
Two legs:
  1. STRUCTURE (node, headless; tools/b384-hlall.mjs): every citation's clip against the lines the printed page says the provision is, read by a
     different rule than the viewer's. Counts per kind, every offender listed.
  2. PAINT (Chromium, the viewer's own painter at 2 px per point): the pixels of every whole page - the one soft tint and one deeper gold, the block
     measured against the provision's lines (top, bottom, right edge), the symmetry of a centred heading, nothing spilling.
County runs anywhere with PDFJS_DIR; the book legs run when IFC_BOOK is the owner's 2021 IFC PDF (it is only read, never copied or stored), else
they are SKIPPED (and say so).
  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> [IFC_BOOK=<the owner's 2021 IFC PDF>] python3 tools/check-b384-hlall.py [--against FILE|REV] [--quick] [--structure]
  --against takes an ifc-viewer.js file or a commit (its ifc/ifc-viewer.js). Against 54a6848 (before this) it FAILS with many offenders.
  --quick samples the paint leg (every 6th citation); --structure runs the node leg only."""
import json, os, subprocess, sys, tempfile, threading, http.server, socketserver, shutil, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/")
if not os.path.exists(PDFJS + "/legacy/build/pdf.mjs") or not os.path.exists(PDFJS + "/build/pdf.min.mjs"):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149"); sys.exit(0)
BOOK = os.environ.get("IFC_BOOK", "")
HAVE_BOOK = bool(BOOK) and os.path.isfile(BOOK)
QUICK = "--quick" in sys.argv; STRUCT_ONLY = "--structure" in sys.argv
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
tmp = tempfile.mkdtemp(prefix="b384hl-")
kit = os.path.join(ROOT, "ifc", "ifc-viewer.js")
if "--against" in sys.argv:
    a = sys.argv[sys.argv.index("--against") + 1]
    if os.path.isfile(a): kit = a
    else:
        kit = os.path.join(tmp, "old-viewer.js")
        open(kit, "w", encoding="utf-8").write(subprocess.check_output(["git", "-C", ROOT, "show", a + ":ifc/ifc-viewer.js"], text=True))
kitm = os.path.join(tmp, "kit.mjs"); shutil.copy(kit, kitm)
COUNTY = os.path.join(ROOT, "ifc", "harris-county-amendments.pdf"); BANK = os.path.join(ROOT, "ifc", "bank.js")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)

# ------------------------------------------------------------------------------------------------ 1. structure
out = os.path.join(tmp, "struct.json")
res = subprocess.run(["node", os.path.join(HERE, "b384-hlall.mjs"), PDFJS, kitm, COUNTY, BANK, BOOK if HAVE_BOOK else "-", out], capture_output=True, text=True, timeout=1800)
if res.returncode != 0:
    print(res.stderr[-1500:]); print("FAIL the structural audit ran"); sys.exit(1)
S = json.load(open(out))
def summarize(src, rows):
    kinds = collections.OrderedDict()
    for r in rows:
        k = kinds.setdefault(r["kind"], [0, 0, collections.Counter()]); k[0] += 1
        if r["bad"]: k[1] += 1
        for b in r["bad"]: k[2][b[0]] += 1
    print("\n%s: %d distinct citations" % (src, len(rows)))
    for k, (n, bad, why) in kinds.items():
        print("  %-24s %4d citations, %3d offenders%s" % (k, n, bad, ("   (" + "; ".join("%s x%d" % (w, c) for w, c in why.items()) + ")") if bad else ""))
    bad = [r for r in rows if r["bad"]]
    return bad
bad = summarize("county", S["county"])
chk("every county citation: the page highlights the whole provision / table / heading's first provision, the picture ends clean", not bad,
    "; ".join("%s %s: %s" % (r["label"], r["kind"], r["bad"][0][0] + " " + r["bad"][0][1]) for r in bad[:8]) + ((" ... +%d more" % (len(bad) - 8)) if len(bad) > 8 else ""))
for r in bad[:40]: print("    OFFENDER %s [%s] %s" % (r["label"], r["kind"], "; ".join(b[0] + " (" + b[1] + ")" for b in r["bad"])))
if len(bad) > 40: print("    ... and %d more offenders" % (len(bad) - 40))
if HAVE_BOOK:
    badb = summarize("book (the owner's copy)", S["book"])
    chk("every book citation: the page highlights the whole provision / entry / section, the picture ends clean", not badb,
        "; ".join("%s %s: %s" % (r["label"], r["kind"], r["bad"][0][0] + " " + r["bad"][0][1]) for r in badb[:8]) + ((" ... +%d more" % (len(badb) - 8)) if len(badb) > 8 else ""))
    for r in badb[:40]: print("    OFFENDER %s [%s] %s" % (r["label"], r["kind"], "; ".join(b[0] + " (" + b[1] + ")" for b in r["bad"])))
    if len(badb) > 40: print("    ... and %d more offenders" % (len(badb) - 40))
else:
    print("\nSKIP the book legs: IFC_BOOK is not set to the owner's 2021 IFC PDF (county legs ran)")
if STRUCT_ONLY:
    print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)

# ------------------------------------------------------------------------------------------------ 2. paint
from playwright.sync_api import sync_playwright
serve = os.path.join(tmp, "www"); os.makedirs(serve)
os.symlink(PDFJS, os.path.join(serve, "pdfjs")); shutil.copy(kitm, os.path.join(serve, "viewer.js")); shutil.copy(COUNTY, os.path.join(serve, "county.pdf"))
if HAVE_BOOK: os.symlink(BOOK, os.path.join(serve, "book.pdf"))
bs = open(BANK, encoding="utf-8").read(); bank = json.loads(bs[bs.index("{"): bs.rindex("}") + 1])
json.dump(bank, open(os.path.join(serve, "bank.json"), "w"))
PAGE = open(os.path.join(HERE, "b384-hlall-page.js"), encoding="utf-8").read()
open(os.path.join(serve, "index.html"), "w").write("<!doctype html><meta charset=utf-8><body style='margin:0'><script type='module'>\nconst HAVE_BOOK = %s;\n%s\n</script>" % ("true" if HAVE_BOOK else "false", PAGE))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=serve, **k)
    def log_message(self, *a): pass
    def end_headers(self): self.send_header("Access-Control-Allow-Origin", "*"); super().end_headers()
H.extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript", ".js": "text/javascript", ".wasm": "application/wasm"}
class TS(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
srv = TS(("127.0.0.1", 0), H); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
ids = []
seen = set()
for q in bank["questions"]:
    c = q["citation"]
    if c.get("source") != "amendment" and not HAVE_BOOK: continue
    k = json.dumps(c, sort_keys=True)
    if k in seen: continue
    seen.add(k); ids.append((q["id"], "county" if c.get("source") == "amendment" else "book"))
if QUICK: ids = ids[::6]
if "--only" in sys.argv:                                                          # (debug) --only ID,ID: just these citations' paint leg
    want = sys.argv[sys.argv.index("--only") + 1].split(","); ids = [x for x in ids if x[0] in want]
found = collections.defaultdict(list); stats = collections.Counter(); metrics = collections.defaultdict(list)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    pg = br.new_page(viewport={"width": 900, "height": 1000}, device_scale_factor=1)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto("http://127.0.0.1:%d/index.html" % port)
    pg.wait_for_function("window.__ready === true || window.__failed", timeout=240000)
    if pg.evaluate("window.__failed"): print("FAIL the page did not start:", pg.evaluate("window.__failed")); sys.exit(1)
    if "--shot" in sys.argv:                                                      # (debug) python3 tools/check-b384-hlall.py --shot ID [--shot ID]  -> /tmp/hl-ID-N.png
        import base64
        for i, a in enumerate(sys.argv):
            if a == "--shot":
                for k, u in enumerate(pg.evaluate("(id) => window.shot(id)", sys.argv[i + 1])):
                    open("/tmp/hl-%s-%d.png" % (sys.argv[i + 1], k), "wb").write(base64.b64decode(u.split(",", 1)[1])); print("wrote /tmp/hl-%s-%d.png" % (sys.argv[i + 1], k))
        sys.exit(0)
    for n, (cid, src) in enumerate(ids):
        for attempt in range(2):
            try:
                r = pg.evaluate("(id) => window.measure(id)", cid); break
            except Exception as e:
                r = {"error": str(e)[:200]}
        stats[src + (" skipped" if r.get("skip") else " measured")] += 1
        if r.get("error"): found[(src, "painter error")].append((cid, r["error"])); continue
        for f in r.get("bad", []): found[(src, f[0])].append((cid, f[1]))
        for k, v in r.get("metrics", {}).items(): metrics[(src, k)].extend(v)
        if n % 100 == 99: print("  ... %d / %d painted" % (n + 1, len(ids)), flush=True)
    br.close()
print("\npaint leg:", dict(stats), "page errors:", errs[:3])
for (src, k), v in sorted(metrics.items()):
    v = sorted(v); print("  %-7s %-30s n=%d  min %.1f  median %.1f  max %.1f" % (src, k, len(v), v[0], v[len(v) // 2], v[-1]))
chk("no page errors while painting", not errs, errs[:2])
for src in ("county", "book"):
    if src == "book" and not HAVE_BOOK: continue
    rows = {w: l for (s, w), l in found.items() if s == src}
    chk("every %s whole page: one soft tint, one deeper gold, the block as wide as its column, centred headings centred, nothing outside the provision" % src, not rows,
        "; ".join("%s x%d (%s)" % (w, len(l), l[0][0] + " " + str(l[0][1])) for w, l in rows.items()))
    for w, l in rows.items():
        for cid, d in l[:12]: print("    OFFENDER %s: %s  %s" % (cid, w, d))
        if len(l) > 12: print("    ... and %d more: %s" % (len(l) - 12, w))
print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)
