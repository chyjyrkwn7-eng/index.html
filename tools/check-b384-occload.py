#!/usr/bin/env python3
"""Build 384.104: more occupant load questions in Chapter 10 (Fire Code). Madison (he/him): "More occupant load questions. Chapter 10 is
really good, it needs a few more occupant load questions though. There should be a question over almost all of them. Ensure there is a
question regarding the bench/pew stuff too."

WHAT THIS BUILD ADDS (tools/gen-ifc-bank.py QUESTION_ADDS; ifc/bank.js regenerated; nothing else of the bank changes): 26 questions,
ch10-339 .. ch10-364, after Chapter 10's last question - 20 on rows of IFC 2021 Table 1004.5 (19 rows that had no question, and the
skating rink beside the pool question), one on 1004.8 (the table's "Concentrated business use areas - See Section 1004.8"), five on
1004.6 fixed seating (the table's "Assembly with fixed seats - See Section 1004.6": the fixed seats themselves, the waiting space added
to them, benches without dividing arms twice, booths). The book never says "pew": no question does.

WHAT IT HOLDS (this build's index.html + ifc/bank.js + ifc/ifc-viewer.js against BASE's, the commit this branch was cut from):
 (1) THE BANK: the 26 are in Chapter 10, after its last question, in order, in the bank's schema-5 shape (the fields, `kind`, the
     citation's section / heading / label / pdfPage / printedPage and its `row` or `find`); their ids continue Chapter 10's numbering past
     every ch10 id the bank or the notes have ever named; four options each, distinct, numbers ascending; every other question is
     byte-identical to BASE's and in the same order; the counts are the bank's own (Chapter 10 +26, the bank +26); the fill-ins and the
     calculations are about one to one; two bench questions besides ch10-304, a booth one and the fixed-seats rule are there.
 (2) THE BOOK (needs PDFJS_DIR + IFC_BOOK: the owner's PDF, loaded the way a reader loads it; SKIPPED without them):
   (2a) every row of Table 1004.5, read off the book (each printed factor cell), is in the gate's table, and each is either asked
        (a question of this build cites it, or the section it sends the reader to) or skipped with a reason - only the mall row is;
   (2b) each new question's answer is the book's: the factor, the gross / net and the bowling lane allowance are read from the TEXT
        UNDER THE GOLD of the question's own picture (the row the app lights, or the 1004.6 / 1004.8 sentence), and a fill-in's key is
        that factor (the stem's gross / net the same), a calculation's key is the stem's area over it, a bench / booth one the stem's
        length over the book's inches;
   (2c) each renders as ONE picture in the code box (the app's own kit paint) with exactly one lit band: a row question's gold runs from
        the table's left border to its right border (within 1.2 pt: it stops one rule's width inside) on the row asked about and nowhere else; a section question's on
        its one sentence; the row's label and its factor stand on the strong gold in the code box and on the whole page;
   (2d) the app's own check of the book (verifyCopy, every new reference) finds every one where the bank says.
 (3) IDENTITY: every one of BASE's questions keeps its exact key (chapter | position | wording), all keys unique; the new ones take
     Chapter 10's positions after its last (133-158); the identity tables (gaps, moved, retired, pinned wording / choices) are BASE's.
 (4) NOTHING LOST: an account that has MASTERED Chapter 10 (35 hundos: badge, star and "Advanced", every one of its 131 questions answered right, stars on some, three
     other badges) is booted on BASE and its saved state on this build: the badge, the star, the chapter's level, hundos, badge count,
     rank, level, the published row and every stored field are identical; no answer tally is lowered, the chapter's answered count and the
     Stats ring's count are the same (its share is reported: the bank is larger); nothing is owed or re-fired; the card still shows the
     badge earned; two devices (BASE and this build) merged either way lower nothing.
 (5) COUNTS: Chapter 10 is 157 in the bank, unitQuestionCount, a full run and its card; the class card reads the bank's total; a run of
     the old 131 is a partial run now; no page errors.
Run:  [PDFJS_DIR=<pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF>] python3 tools/check-b384-occload.py [--against REV]
      --against REV: REV's index.html, ifc/bank.js and ifc/ifc-viewer.js are "this build". Against origin/main (384.95) (1), (2a), (2b),
      (2c), (2d) and (5) FAIL (the questions are not there); (3) and (4) hold on both by design (they are what must not change).
The book never goes into the repo (it is public): its path is given when the gate is run."""
import os, sys, json, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import b384_qfix_lib as L

AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
def git_show(rev, path): return subprocess.run(["git", "-C", ROOT, "show", rev + ":" + path], capture_output=True, text=True).stdout
def _base():
    r = subprocess.run(["git", "-C", ROOT, "merge-base", "HEAD", "origin/main"], capture_output=True, text=True).stdout.strip()
    return r or "origin/main"
BASE = os.environ.get("BASE") or _base()
OLD_HTML, OLD_BANK, OLD_VIEW = git_show(BASE, "index.html"), git_show(BASE, "ifc/bank.js"), git_show(BASE, "ifc/ifc-viewer.js")
OLD_NOTES = git_show(BASE, "docs/notes-archive.md")
assert OLD_HTML and OLD_BANK and OLD_VIEW, "git show %s failed" % BASE
if AGAINST:
    NEW_HTML, NEW_BANK, NEW_VIEW = git_show(AGAINST, "index.html"), git_show(AGAINST, "ifc/bank.js"), git_show(AGAINST, "ifc/ifc-viewer.js")
    assert NEW_HTML and NEW_BANK and NEW_VIEW, "git show %s failed" % AGAINST
else:
    rd = lambda p: open(os.path.join(ROOT, p), encoding="utf-8").read()
    NEW_HTML, NEW_BANK, NEW_VIEW = rd("index.html"), rd("ifc/bank.js"), rd("ifc/ifc-viewer.js")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:1500], flush=True)
def nz(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())

NEW = ["ch10-%03d" % n for n in range(339, 365)]
CH10 = "10"
# ---- IFC 2021 Table 1004.5, every row that prints a factor (40), in the book's order: what this build does with it.
#      "old": a question existed before; "new": this build adds one; "sec": the row sends the reader to a section, and that section is asked;
#      "skip": no question, and why. (2a) reads the book's own cells to hold this list complete.
ROWS = [
    ("Accessory storage areas, mechanical", "new"), ("Agricultural building", "new"), ("Aircraft hangars", "new"),
    ("Baggage claim", "new"), ("Baggage handling", "new"), ("Concourse", "new"), ("Waiting areas", "new"),
    ("Gaming floors (keno, slots, etc.)", "new"), ("Exhibit gallery and museum", "new"),
    ("Assembly with fixed seats", ("sec", "1004.6")),
    ("Concentrated (chairs only—not fixed)", "new"), ("Standing space", "new"), ("Unconcentrated (tables and chairs)", "new"),
    ("Bowling centers, allow 5 persons for each", "new"),
    ("Business areas", "old"), ("Concentrated business use areas", ("sec", "1004.8")),
    ("Courtrooms—other than fixed seating areas", "old"), ("Day care", "old"), ("Dormitories", "old"),
    ("Classroom area", "old"), ("Shops and other vocational room areas", "old"), ("Exercise rooms", "old"),
    ("Group H-5 fabrication and manufacturing", "new"), ("Industrial areas", "old"),
    ("Inpatient treatment areas", "old"), ("Outpatient areas", "new"), ("Sleeping areas", "new"),
    ("Kitchens, commercial", "old"), ("Reading rooms", "old"), ("Stack area", "new"), ("Locker rooms", "new"),
    ("Mall buildings—covered and open", ("skip", "the row has no factor: it sends the reader to Section 402.8.2 of the International Building Code, which is not in the IFC book")),
    ("Mercantile", "old"), ("Storage, stock, shipping areas", "new"), ("Parking garages", "old"), ("Residential", "old"),
    ("Rink and pool", "old"), ("Decks", "old"), ("Stages and platforms", "old"), ("Warehouses", "old"),
]
SECTIONS_1004_6 = {"bench18": "one person for each 18 inches", "booth24": "one person for each 24 inches",
                   "fixed": "determined by the number of fixed seats installed", "waiting": "added to the number of fixed seats"}

ob, nb = L.bank_of(OLD_BANK), L.bank_of(NEW_BANK)
oq = {q["id"]: q for q in ob["questions"]}; nq = {q["id"]: q for q in nb["questions"]}

# =========================================================== (1) the bank
SCHEMA = ["id", "unit", "type", "question", "options", "answer", "explanation", "topic", "kind", "citation"]
T1004 = next(q["citation"] for q in ob["questions"] if q["citation"].get("section") == "Table 1004.5" and q["citation"].get("source") == "ifc")
present = [i for i in NEW if i in nq]
old10 = [q["id"] for q in ob["questions"] if q["unit"] == CH10]
new10 = [q["id"] for q in nb["questions"] if q["unit"] == CH10]
placed = new10 == old10 + NEW
seen_ids = set(re.findall(r"\bch10-(\d{3})\b", OLD_NOTES + OLD_BANK + OLD_HTML))
top_ever = max(int(n) for n in seen_ids)
fresh = all(int(i.split("-")[1]) > top_ever for i in NEW) and len(set(NEW)) == len(NEW)
shape_bad = []
def is_num(s): return re.fullmatch(r"[\d,]+(\.\d+)?", s) is not None
def num(s): return float(s.replace(",", ""))
for i in present:
    q = nq[i]; c = q["citation"]; opts = [q["options"].get(k) for k in "ABCD"]
    why = []
    if list(q) != SCHEMA: why.append("fields %s" % list(q))
    if q["unit"] != CH10 or q["type"] != "content" or q["kind"] not in ("measure", "other"): why.append("unit/type/kind")
    if sorted(q["options"]) != list("ABCD") or q["answer"] not in "ABCD" or len(set(opts)) != 4 or not all(o and o.strip() for o in opts): why.append("options")
    if all(is_num(o) for o in opts) and [num(o) for o in opts] != sorted(num(o) for o in opts): why.append("numbers not ascending")
    if q["question"].count("_____") > 1 or not q["explanation"].strip() or not q["topic"].strip(): why.append("stem/explanation/topic")
    if c.get("source") != "ifc" or c.get("label") != "IFC 2021 " + c.get("section", "") or not isinstance(c.get("pdfPage"), int): why.append("citation basics")
    if c.get("printedPage") != {200: "10-3", 201: "10-4"}.get(c.get("pdfPage")): why.append("printedPage")
    if c.get("section") == "Table 1004.5":
        if c.get("heading") != T1004["heading"] or not isinstance(c.get("row"), str) or set(c) != {"source", "section", "heading", "label", "pdfPage", "printedPage", "row"}: why.append("table pointer")
    elif c.get("section") in ("1004.6", "1004.8"):
        if not (isinstance(c.get("find"), list) and len(c["find"]) == 1 and c.get("heading")) or set(c) != {"source", "section", "heading", "label", "pdfPage", "printedPage", "find"}: why.append("section pointer")
    else: why.append("section %s" % c.get("section"))
    if why: shape_bad.append((i, why))
others_bad = [i for i in oq if nq.get(i) != oq[i]]
order_kept = [q["id"] for q in nb["questions"] if q["id"] in oq] == [q["id"] for q in ob["questions"]]
units_ok = all(u["questionCount"] == sum(1 for q in nb["questions"] if q["unit"] == u["id"]) for u in nb["units"]) and nb["meta"]["questionCount"] == len(nb["questions"])
sizes = {u["id"]: u["questionCount"] for u in nb["units"]}; osizes = {u["id"]: u["questionCount"] for u in ob["units"]}
size_ok = sizes.get(CH10) == osizes[CH10] + len(NEW) and all(sizes[u] == osizes[u] for u in osizes if u != CH10) and len(nb["questions"]) == len(ob["questions"]) + len(NEW)
meas = [nq[i] for i in present if nq[i]["kind"] == "measure"]
fills = sum(1 for q in meas if "_____" in q["question"]); calcs = len(meas) - fills
mix_ok = fills and calcs and min(fills, calcs) / max(fills, calcs) >= 0.6
f6 = lambda q: q["citation"].get("section") == "1004.6" and (q["citation"].get("find") or [""])[0]
bench = [i for i in present if f6(nq[i]) == SECTIONS_1004_6["bench18"]]
seat_kinds = {k: [i for i in present if f6(nq[i]) == v] for k, v in SECTIONS_1004_6.items()}
pew_ok = len(bench) >= 2 and all(seat_kinds[k] for k in SECTIONS_1004_6) and all(nq[i]["question"] != oq["ch10-304"]["question"] for i in bench)
chk("(1) the bank: %d of the %d new questions are in Chapter 10, after its last question, in order (%s); their ids continue past every ch10 id ever named (highest before: ch10-%03d); the schema-5 shape, four distinct options, numbers ascending (%d bad: %s)" % (
    len(present), len(NEW), placed, top_ever, len(shape_bad), shape_bad[:2]),
    len(present) == len(NEW) and placed and fresh and not shape_bad, {"present": len(present), "placed": placed, "fresh": fresh, "bad": shape_bad[:4]})
chk("(1) every other question (%d) is byte-identical to %s's and in the same order (%d differ); counts are the bank's own: Chapter 10 %s -> %s, the bank %d -> %d, every other chapter its size" % (
    len(oq), BASE[:7], len(others_bad), osizes[CH10], sizes.get(CH10), len(ob["questions"]), len(nb["questions"])),
    not others_bad and order_kept and units_ok and size_ok, {"others": others_bad[:4], "order": order_kept, "units": units_ok, "size": size_ok})
chk("(1) the mix: %d fill-ins and %d calculations of kind measure (about one to one); bench seating without dividing arms asked %d more times than ch10-304 (%s), booths, the fixed seats and the waiting space beside them each asked (%s)" % (
    fills, calcs, len(bench), bench, {k: v for k, v in seat_kinds.items()}), mix_ok and pew_ok, {"fills": fills, "calcs": calcs, "bench": bench, "kinds": seat_kinds})

# =========================================================== the pages
from playwright.sync_api import sync_playwright
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"; BOOK = os.environ.get("IFC_BOOK", "")
HAVE_BOOK = os.path.exists(PDFJS + "build/pdf.min.mjs") and os.path.isfile(BOOK)
if HAVE_BOOK:
    saved_argv = sys.argv; sys.argv = [saved_argv[0]]
    src = open(os.path.join(HERE, "check-b384-ifcmarks.py"), encoding="utf-8").read().split("SPAGE = 1.7")[0]
    G0 = {"__file__": os.path.join(HERE, "check-b384-ifcmarks.py"), "__name__": "b384occload"}
    exec(src, G0)                                              # the harness: the book, pdf.js, the in-memory cloud, the server
    sys.argv = saved_argv
    G = G0["G"]
else:
    G = L.fixture()
IR = G["g"]["INSET_RE"]
def insets(h): return IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], h)
OLD_PAGE, NEW_PAGE = insets(OLD_HTML), insets(NEW_HTML)
errs_all = []

# ---- (2) the book: this build's page, viewer and bank, with the owner's PDF loaded
PIX = r"""async (id) => {
  const V = await ifcViewer(); const book = await ifcEnsureBook(); const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), c = q.ifc.citation;
  const loc = V.locate(book.index, c); if (!loc.ok) return { id, err: 'not located' };
  const clip = await V.computeClip(book.doc, book.index, loc, c, book.opts); if (!clip || !clip.ok) return { id, err: 'no clip' };
  const box = document.createElement('div'); document.body.appendChild(box);
  await V.paint(book.doc, clip, box, { scale: 1.7 });
  const cvs = box.querySelectorAll('canvas'), cv = cvs[0], W = cv.width, H = cv.height, s = 1.7 * Math.min(window.devicePixelRatio || 1, 2);
  const D = cv.getContext('2d').getImageData(0, 0, W, H).data;
  const ink = (x, y) => D[(y * W + x) * 4] < 200, gold = (x, y) => { const i = (y * W + x) * 4; return D[i] > 200 && D[i + 1] > 150 && D[i + 2] < 120; };
  // the table's frame: the extent of its long horizontal rules (30 pt or more of ink in a row)
  let a = W, b = -1; const MIN = 30 * s;
  for (let y = 0; y < H; y++) { let run = 0; for (let x = 0; x <= W; x++) { if (x < W && ink(x, y)) { run++; continue; } if (run >= MIN) { a = Math.min(a, x - run); b = Math.max(b, x - 1); } run = 0; } }
  // the lit bands: rows of the picture holding strong gold, a gap of 4 pt or less inside one band
  const rows = []; for (let y = 0; y < H; y++) { let n = 0; for (let x = 0; x < W; x++) if (gold(x, y)) n++; rows.push(n); }
  const bands = []; let cur = null;
  for (let y = 0; y < H; y++) { if (!rows[y]) continue; if (cur && y - cur.y1 <= 4 * s) cur.y1 = y; else { cur = { y0: y, y1: y }; bands.push(cur); } }
  for (const bd of bands) {
    let best = bd.y0; for (let y = bd.y0; y <= bd.y1; y++) if (rows[y] > rows[best]) best = y;
    let gx0 = -1, gx1 = -1; for (let x = 0; x < W; x++) if (gold(x, best)) { if (gx0 < 0) gx0 = x; gx1 = x; }
    let mx0 = W, mx1 = -1; for (let y = bd.y0; y <= bd.y1; y++) for (let x = 0; x < W; x++) if (gold(x, y)) { mx0 = Math.min(mx0, x); mx1 = Math.max(mx1, x); }
    Object.assign(bd, { y: best, gx0, gx1, mx0, mx1, px: rows[best] });
  }
  box.remove();
  return { id, n: cvs.length, W, H, s, frame: b >= 0 ? [a, b] : null, bands };
}"""
VERIFY = r"""async (ids) => { const V = await ifcViewer(); const book = await ifcEnsureBook();
  const qs = ids.map(id => (QUESTIONS.find(x => x.ifc && x.ifc.id === id) || {}).ifc).filter(Boolean);
  const r = await V.verifyCopy(book.doc, book.index, qs, { sample: Infinity, cache: book.opts.cache, fontBold: book.opts.fontBold });
  return { level: r.level, n: qs.length, differences: r.differences, summary: r.summary }; }"""
def open_book(br, html, viewer, bank):
    """the app on `html` with `viewer` and `bank`, and the owner's book loaded (the ifcmarks harness, with the bank and the viewer of the build under test)"""
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, device_scale_factor=2)
    ctx.route("**/pdfjs-dist@5.4.149/**", G0["pdfjs_route"])
    ctx.route("**/ifc/ifc-viewer.js*", lambda route, request, b=viewer: route.fulfill(status=200, body=b, content_type="text/javascript"))
    ctx.route("**/ifc/bank.js*", lambda route, request, b=bank: route.fulfill(status=200, body=b, content_type="text/javascript; charset=utf-8"))
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"]); ctx.add_init_script(G["init"](G["ifc"]))
    pg = ctx.new_page(); errs = []
    pg.set_default_timeout(180000)                             # (a loaded machine: choosing the 7.5 MB book took over 30 s)
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    v = re.search(r'const APP_BUILD = "([^"]+)"', html).group(1)
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": v, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=html: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, errs

if not HAVE_BOOK:
    print("SKIP (2): set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF to read the book and the pictures", flush=True)
else:
    rec, pix, shares, cited, ver = {}, {}, {}, "", None
    def book_pass(pw):
        """one browser: the book loaded, then every new question read; a renderer crash ("Target crashed", seen on this machine under load)
           is raised to the caller, which starts again in a fresh browser (the readings are the same each time: nothing here is timing)"""
        global cited, ver, acc
        br = pw.chromium.launch(executable_path=G["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
        try:
            ctx, pg, errs = open_book(br, NEW_PAGE, NEW_VIEW, NEW_BANK)
            acc = G0["load_book"](pg)
            pg.evaluate(open(os.path.join(HERE, "b384-ifcmarks-page.js"), encoding="utf-8").read())
            have = pg.evaluate("(ids)=>ids.filter(id => QUESTIONS.some(x => x.ifc && x.ifc.id === id))", NEW)
            # the whole table as the book prints it (the cited extent of an existing row question: both pages)
            cited = (pg.evaluate("(id)=>__im.rec(id)", "ch10-142") or {}).get("citedText") or ""
            for i in have:
                if i in rec and "error" not in rec[i] and i in pix and "err" not in pix[i] and (i in shares or not (nq.get(i) or {}).get("citation", {}).get("row")): continue
                rec[i] = pg.evaluate("(id)=>__im.rec(id)", i); pix[i] = pg.evaluate(PIX, i)
                q = nq.get(i) or {}
                if (q.get("citation") or {}).get("row"):
                    lab = q["citation"]["row"]
                    m = next((mk for mk in (rec[i].get("marks") or []) if mk["kind"] == "row"), None)
                    val = re.search(r"(\d+ (?:gross|net))\s*$", m["text"]).group(1) if m and re.search(r"(\d+ (?:gross|net))\s*$", m["text"]) else "@@none"
                    words = [{"re": "^" + re.escape(lab), "label": "label", "comp": False}, {"re": "^" + re.escape(val) + "$", "label": "value", "comp": False}]
                    shares[i] = {v: pg.evaluate("([id, w, s, v]) => __im.pixels(id, w, s, v)", [i, words, {"page": 2.5, "clip": 6.0}[v], v]) for v in ("clip", "page")}
            ver = pg.evaluate(VERIFY, have) if have else {"level": None, "n": 0, "differences": [], "summary": ""}
            return errs
        finally:
            try: br.close()
            except Exception: pass
    acc = None
    with sync_playwright() as pw:
        import time
        def mem_free_mb():
            try: return int(next(l for l in open("/proc/meminfo") if l.startswith("MemAvailable")).split()[1]) // 1024
            except Exception: return 1 << 20
        for attempt in range(8):
            # (reading the 697-page book takes the renderer about 1 GB; on a machine shared with other sessions' browsers the kernel's
            # memory-cgroup OOM killer took it mid-read: wait, up to 20 minutes, for room before each try)
            for _ in range(120):
                if mem_free_mb() >= 2500: break
                time.sleep(10)
            try:
                errs_all += book_pass(pw); break
            except Exception as e:
                if not any(w in str(e).lower() for w in ("crash", "closed", "timeout")) or attempt == 7: raise
                print("    (the renderer crashed reading the book: %s - again, in a fresh browser)" % str(e).splitlines()[0][:90], flush=True)
                time.sleep(30)
    chk("the owner's IFC PDF is accepted by the app", acc, acc)
    # ---- (2a) every row of the table, from the book
    vals = re.findall(r"\b\d+ (?:gross|net)\b|See Section", cited)
    labels_missing = [l for l, st in ROWS if nz(l) not in nz(cited)]
    asked = {}
    for l, st in ROWS:
        if isinstance(st, tuple) and st[0] == "skip": continue
        if isinstance(st, tuple) and st[0] == "sec":
            asked[l] = [q["id"] for q in nb["questions"] if q["unit"] == CH10 and q["citation"].get("section") == st[1]]
        else:
            asked[l] = [q["id"] for q in nb["questions"] if q["unit"] == CH10 and q["citation"].get("section") == "Table 1004.5" and l in ([q["citation"]["row"]] if isinstance(q["citation"].get("row"), str) else q["citation"].get("row") or [])]
    unasked = [l for l, ids in asked.items() if not ids]
    new_rows = sorted(l for l, st in ROWS if st == "new"); new_cited = sorted(set(nq[i]["citation"]["row"] for i in NEW if i in nq and isinstance(nq[i]["citation"].get("row"), str)) - set(l for l, st in ROWS if st == "old"))
    skipped = [l for l, st in ROWS if isinstance(st, tuple) and st[0] == "skip"]
    chk("(2a) the book's Table 1004.5 prints %d factor cells and the gate's table has %d rows, every label found in the book (%s missing); every row is asked (%d unasked: %s) but %s (skipped: the reason is in the gate); the rows this build adds questions for are exactly the %d with none before" % (
        len(vals), len(ROWS), labels_missing or "none", len(unasked), unasked[:4], skipped, len(new_rows)),
        len(vals) == len(ROWS) == 40 and not labels_missing and not unasked and new_cited == new_rows, {"vals": len(vals), "missing": labels_missing, "unasked": unasked, "new_cited": new_cited, "new_rows": new_rows})
    # ---- (2b) the answer is the book's, read from the text under the gold
    def keyed(q): return q["options"][q["answer"]]
    def stem_area(stem): m = re.search(r"([\d,]+) (gross|net) square feet", stem); return (num(m.group(1)), m.group(2)) if m else (None, None)
    wrong, read = [], {}
    for i in NEW:
        q, r = nq.get(i), rec.get(i) or {}
        if not q or not r.get("marks"): wrong.append((i, "no picture")); continue
        stem, key = q["question"], keyed(q)
        if q["citation"].get("row"):
            rm = [m for m in r["marks"] if m["kind"] == "row"]
            if len(rm) != 1: wrong.append((i, "%d row marks" % len(rm))); continue
            t = rm[0]["text"]; m = re.search(r"(\d+) (gross|net)\s*$", t)
            if not m or not nz(t).startswith(nz(q["citation"]["row"])): wrong.append((i, "the lit row is not the cited one", t[:60])); continue
            fac, basis = int(m.group(1)), m.group(2); read[i] = "%d %s" % (fac, basis)
            if "_____" in stem:
                good = re.search(r"_____ (gross|net) square feet", stem) and re.search(r"_____ (gross|net)", stem).group(1) == basis and is_num(key) and num(key) == fac
            elif re.search(r"(\d+) lanes", stem):
                lanes = int(re.search(r"(\d+) lanes", stem).group(1)); per = re.search(r"allow (\d+) persons for each lane including (\d+) feet of runway", t)
                area, b2 = stem_area(stem)
                good = per and ("%s feet of runway" % per.group(2)) in stem and b2 == basis and num(key) == lanes * int(per.group(1)) + area / fac
                read[i] += ", %s persons a lane" % (per.group(1) if per else "?")
            else:
                area, b2 = stem_area(stem)
                good = area is not None and b2 == basis and area % fac == 0 and num(key) == area / fac
        else:
            t = " ".join(m["text"] for m in r["marks"] if m["kind"] == "cite"); t = re.sub(r"\s+([,.;])", r"\1", re.sub(r"\s+", " ", t)).strip()
            read[i] = t[:70]
            one = t.endswith(".") and not re.search(r"\.\s+[A-Z]", t) and nz(q["citation"]["find"][0]) in nz(t)
            n18 = re.search(r"one person for each (\d+) inches", t); n50 = re.search(r"not less than one occupant per (\d+) square feet", t)
            if not one: good = False
            elif n18 and "_____" in stem: good = key.endswith("inches") and num(key.split()[0]) == int(n18.group(1))
            elif n18 and re.search(r"(\d+) fixed benches", stem):
                nb_, ft = int(re.search(r"(\d+) fixed benches", stem).group(1)), int(re.search(r"each (\d+) feet long", stem).group(1))
                good = (ft * 12) % int(n18.group(1)) == 0 and num(key) == nb_ * ft * 12 / int(n18.group(1))
            elif n18 and "booth" in t and re.search(r"(\d+) inches of booth seat length", stem):
                good = num(key) == int(re.search(r"(\d+) inches of booth seat length", stem).group(1)) / int(n18.group(1))
            elif n50: good = num(key) == int(n50.group(1)) and "gross occupiable floor space" in stem and "gross occupiable floor space" in t
            elif "number of fixed seats installed" in t: good = num(key) == int(re.search(r"(\d+) fixed seats", stem).group(1))
            elif "added to the number of fixed seats" in t:
                good = "1004.5" in key and "added" in key and "1004.5" in t and not any("added" in v for k, v in q["options"].items() if k != q["answer"])
            else: good = False
        if not good: wrong.append((i, read.get(i), stem[:70], key))
    chk("(2b) every new question's key is the book's, read from the text under the gold of its own picture (%d of %d; e.g. %s)" % (
        len(NEW) - len(wrong), len(NEW), "; ".join("%s %s" % (i, read.get(i)) for i in ("ch10-339", "ch10-351", "ch10-363") if i in read)), not wrong, wrong[:5])
    # ---- (2c) one picture, one lit band, the whole row
    badpic, rows_read = [], []
    for i in NEW:
        p = pix.get(i) or {}; q = nq.get(i)
        if not q or p.get("err") or p.get("n") != 1: badpic.append((i, p.get("err") or "%s canvases" % p.get("n"))); continue
        if len(p["bands"]) != 1: badpic.append((i, "%d lit bands" % len(p["bands"]), [(bd["y0"], bd["y1"]) for bd in p["bands"]][:4])); continue
        bd = p["bands"][0]
        if q["citation"].get("row"):
            fr = p["frame"]
            off = max(abs(bd["gx0"] - fr[0]), abs(bd["gx1"] - fr[1])) / p["s"] if fr else 99      # in points: the gold stops one rule's width inside the border
            if off > 1.2: badpic.append((i, "the row's gold %s..%s px, the table %s (%.1f pt off)" % (bd["gx0"], bd["gx1"], fr, off))); continue
            rows_read.append(round(off, 2))
            sh = shares.get(i) or {}
            for v in ("clip", "page"):
                ws = (sh.get(v) or {}).get("words") or []
                for lab in ("label", "value"):
                    best = max([w["share"] for w in ws if w["label"] == lab] or [0])
                    if best < 0.6: badpic.append((i, v, lab, round(best, 2)))
    chk("(2c) each new question is ONE picture in the code box with ONE lit band: a row question's gold runs from the table's left border to its right (%d rows, worst %s pt inside the border, one rule's width), its label and factor on the strong gold in the code box and on the whole page; a section question's on its one sentence" % (
        len(rows_read), max(rows_read or [None])), not badpic and len(rows_read) == sum(1 for i in NEW if i in nq and nq[i]["citation"].get("row")), badpic[:6])
    chk("(2d) the app's own check of the book (verifyCopy, all %d new references): %s, none differs (%s)" % (ver["n"], ver["level"], ver["differences"][:4] or "none"),
        ver["n"] == len(NEW) and ver["level"] == "exact" and not ver["differences"], ver)

# ---- (3)-(5): BASE's app + bank against this build's
STORE_KEY = "class26e.ifc.drill.v1"
def seed_js(fields):
    return ";(()=>{ try{ const k='%s'; const s=JSON.parse(localStorage.getItem(k)||'{}'); Object.assign(s, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % (STORE_KEY, json.dumps(fields))
SNAP = """(T)=>{
  const answered = QUESTIONS.filter((q, i) => (q.topic || '').trim() === T && store.stats[KEYS[i]] && (store.stats[KEYS[i]].n || 0) > 0).length;
  const right = QUESTIONS.filter((q, i) => (q.topic || '').trim() === T && store.stats[KEYS[i]] && (store.stats[KEYS[i]].n || 0) > (store.stats[KEYS[i]].m || 0)).length;
  let ring = 0; const bk = [...new Set(KEYS)]; bk.forEach(k => { const st = store.stats && store.stats[k]; if(st && (Number(st.n) || 0) > (Number(st.m) || 0)) ring++; });
  const strip = o => { const c = JSON.parse(JSON.stringify(o)); delete c.lastModified; delete c.badgeScenePlayed; delete c.badgeSceneOwed; return c; };
  let row = null; try{ row = JSON.parse(JSON.stringify(buildLeaderboardRow())); ['at','updatedAt','ts','lastModified','seenAt'].forEach(k => delete row[k]); }catch(e){ row = String(e); }
  let rank = null; try{ rank = JSON.stringify(rankOf(store)); }catch(e){ rank = String(e); }
  let lvl = null; try{ lvl = JSON.stringify(levelProgress(store.lifetime.points)); }catch(e){ lvl = null; }
  let pend = null; try{ const p = pendingHomeUnlocks(); pend = { owed: homeUnlocksOwed(p), n: [p.chars.length, p.banners.length, (p.hints||[]).length, (p.fx||[]).length, (p.finds||[]).length] }; }catch(e){ pend = String(e); }
  return { rest: strip(store), perf: unitPerfectCount(T), earned: unitBadgeEarned(T), star: unitDrillStarEarned(T), level: unitLevel(T), size: unitQuestionCount(T), answered, right,
    ring, ringOf: bk.length, ringPct: Math.floor(ring / bk.length * 100), badges: badgesEarnedList(), badgeCount: badgeCountOf(store), hundos: hundosOf(store), row, rank, lvl, pend,
    pending: JSON.parse(JSON.stringify(store.pendingBadgeUnlocks || [])), stats: JSON.parse(JSON.stringify(store.stats)),
    overlay: !!document.querySelector('.cutscene, .tier-cutscene, .badge-cutscene, .unlock-card, .rankup, #tour-overlay') }; }"""
CARDS = """()=>{ cfg.mode = 'drill'; cfg.units = []; showSetup(); return new Promise(r => setTimeout(() => r([...document.querySelectorAll('.picks > label.pick')].map(c => ({
  name: c.querySelector('.pname') && c.querySelector('.pname').textContent, count: c.querySelector('.pcount') && c.querySelector('.pcount').textContent,
  earned: !!c.querySelector('.pick-badge.earned') }))), 1200)); }"""
FULLRUN = """(args)=>{ const t = args.t, n = args.n; cfg.mode = 'drill'; cfg.units = [t]; const idx = []; QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === t && inWholeUnit(q)) idx.push(i); });
  order = idx.slice(0, n); const part = isFullUnitRun(); order = idx.slice(); return { part, full: isFullUnitRun(), n: idx.length }; }"""
MERGE = """(args)=>{ const a = args.a, b = args.b; const C = o => JSON.parse(JSON.stringify(o));
  const nums = o => { const out = {}; const walk = (p, v) => { if(typeof v === 'number') out[p] = v; else if(v && typeof v === 'object' && !Array.isArray(v)) Object.keys(v).forEach(k => walk(p + '/' + k, v[k])); };
    walk('perf', o.unitPerfects || {}); walk('life', o.lifetime || {}); walk('best', o.unitBestPct || {}); walk('runs', o.unitRuns || {});
    Object.keys(o.stats || {}).forEach(k => { out['n:' + k] = (o.stats[k] || {}).n || 0; out['m:' + k] = (o.stats[k] || {}).m || 0; }); return out; };
  const lower = (m, x, y) => { const ex = nums(x), ey = nums(y), em = nums(m); const bad = []; Object.keys(ex).concat(Object.keys(ey)).forEach(k => { if((em[k] || 0) < Math.max(ex[k] || 0, ey[k] || 0)) bad.push(k); }); return bad; };
  const d1 = C(a); mergeSameAccount(d1, C(b)); const d2 = C(b); mergeSameAccount(d2, C(a)); return { ab: lower(d1, a, b), ba: lower(d2, a, b) }; }"""
with sync_playwright() as pw:
    rig = L.Rig(G, pw)
    _nc = rig.br.new_context
    def _patient(**kw):                                        # (a loaded machine: a page load over 30 s is slow, not wrong)
        c = _nc(**kw); c.set_default_timeout(180000); c.set_default_navigation_timeout(180000); return c
    rig.br.new_context = _patient
    try:
        old, e0 = rig.read(OLD_PAGE, OLD_BANK); new, e1 = rig.read(NEW_PAGE, NEW_BANK)
        errs_all += e0 + e1
        O = {r["id"]: r for r in old["rows"] if r["id"]}; N = {r["id"]: r for r in new["rows"] if r["id"]}
        # ---- (3) identity
        moved = [i for i in O if i in N and O[i]["key"] != N[i]["key"]]
        allk = [r["key"] for r in new["rows"]]
        T10 = next(s["topic"] for s in new["sizes"] if s["id"] == CH10)
        last_old = max(O[i]["src"] for i in O if O[i]["topic"] == T10)
        new_src = [N[i]["src"] for i in NEW if i in N]
        tabs_same = json.dumps(old["tables"], sort_keys=True) == json.dumps(dict(new["tables"], countText=old["tables"]["countText"]), sort_keys=True)
        chk("(3) identity: all %d of %s's questions keep their exact key (%d moved: %s); all %d keys unique; the new ones take Chapter 10's positions after its last (%s, its last was %d); the identity tables are %s's" % (
            len(O), BASE[:7], len(moved), moved[:3], len(allk), (str(new_src[0]) + "-" + str(new_src[-1])) if new_src else "none", last_old, BASE[:7]),
            not moved and set(O) <= set(N) and len(set(allk)) == len(allk) and tabs_same and new_src == list(range(last_old + 1, last_old + 1 + len(new_src))),
            {"moved": moved[:5], "missing": [i for i in O if i not in N][:4], "tables": tabs_same, "src": new_src[:4]})
        # ---- (4) nothing lost: an account that has mastered Chapter 10
        ch10_keys = [O[i]["key"] for i in O if O[i]["topic"] == T10]
        others = [s["topic"] for s in old["sizes"] if s["id"] in ("1", "2", "3")]
        stats = {k: {"n": 2, "m": 0, "r": [1790000000001, 1790000000002]} for k in ch10_keys}
        for t in others:
            for r in [x for x in old["rows"] if x["topic"] == t][:20]: stats[r["key"]] = {"n": 3, "m": 1, "r": []}
        flagged = {k: 1790000000123 + n for n, k in enumerate(ch10_keys[:5])}
        perf = dict({T10: 35}, **{t: 1 for t in others})                  # 35 hundos: Chapter 10 reads "Advanced" (unitLevel mastery) as well as badged and starred
        fields = {"unitPerfects": perf, "stats": stats, "pendingBadgeUnlocks": [], "flagged": flagged, "unitBestPct": {t: 100 for t in perf}, "unitRuns": {t: 4 for t in perf},
                  "lifetime": {"points": 61000, "perfectTests": 38, "answered": 6000, "correct": 5800}}
        ctx, pg, e = rig.open(OLD_PAGE, OLD_BANK, seed_js(fields))
        pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
        before = pg.evaluate(SNAP, T10); saved = pg.evaluate("()=>JSON.parse(JSON.stringify(store))"); errs_all += e; ctx.close()
        ctx, pg, e = rig.open(NEW_PAGE, NEW_BANK, seed_js(saved))
        pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
        after = pg.evaluate(SNAP, T10)
        merged = pg.evaluate(MERGE, {"a": pg.evaluate("()=>JSON.parse(JSON.stringify(store))"), "b": saved})
        cards = {c["name"]: c for c in pg.evaluate(CARDS)}
        run_old = pg.evaluate(FULLRUN, {"t": T10, "n": len(ch10_keys)})
        cls_text = pg.evaluate("()=>ifcQuestionCountText()")
        errs_all += e; ctx.close()
        rest_diff = [k for k in set(before["rest"]) | set(after["rest"]) if json.dumps(before["rest"].get(k), sort_keys=True) != json.dumps(after["rest"].get(k), sort_keys=True)]
        held = all(before[k] == after[k] for k in ("perf", "earned", "star", "level", "badges", "badgeCount", "hundos", "rank", "lvl", "pend")) and \
            json.dumps(before["row"], sort_keys=True) == json.dumps(after["row"], sort_keys=True)
        chk("(4a) an account that has MASTERED Chapter 10 (badge, star, '%s', %d hundos there) keeps all of it on this build: the badge, the star, the level, hundos %s -> %s, badges %s -> %s, rank, level and the published row the same; every stored field identical (%d differ: %s); nothing owed or re-fired" % (
            before["level"], before["perf"], before["hundos"], after["hundos"], before["badgeCount"], after["badgeCount"], len(rest_diff), rest_diff[:4]),
            held and before["earned"] and before["star"] and before["level"] == "mastery" and not rest_diff and after["pending"] == [] and not after["overlay"],
            {"held": held, "rest": rest_diff[:5], "b": {k: before[k] for k in ("perf", "earned", "star", "level", "badgeCount", "hundos")}, "a": {k: after[k] for k in ("perf", "earned", "star", "level", "badgeCount", "hundos")}})
        lowered = [k for k, v in before["stats"].items() if after["stats"].get(k, {}).get("n", 0) < v.get("n", 0) or after["stats"].get(k, {}).get("m", 0) < v.get("m", 0)]
        card = next((c for n, c in cards.items() if n and (n == T10 or n == T10.split(": ", 1)[-1])), None)
        chk("(4b) no answer tally lowered (%d entries, %d lowered); Chapter 10 answered right %d -> %d of %d -> %d questions; the Stats ring's count %d -> %d (its share %d%% -> %d%%: %d more questions in the bank, nothing taken); the chapter card still shows the badge earned (%s)" % (
            len(before["stats"]), len(lowered), before["right"], after["right"], before["size"], after["size"], before["ring"], after["ring"], before["ringPct"], after["ringPct"], after["ringOf"] - before["ringOf"], card and card["earned"]),
            not lowered and after["right"] == before["right"] == len(ch10_keys) and after["ring"] == before["ring"] and card and card["earned"], {"lowered": lowered[:4], "card": card})
        chk("(4c) two devices of one account (%s's bank and this one), merged either way, lower nothing (%s / %s)" % (BASE[:7], merged["ab"][:2] or "ok", merged["ba"][:2] or "ok"),
            not merged["ab"] and not merged["ba"], merged)
        # ---- (5) counts
        S = {s["id"]: s for s in new["sizes"]}; Sb = {s["id"]: s for s in old["sizes"]}
        want10 = Sb[CH10]["n"] + len(NEW)
        chk("(5) Chapter 10 is %d in the bank, unitQuestionCount, a full run and its card (%s) (%s: %d); the class card reads %s; a run of the old %d is a partial run now (%s), a hundo already held is kept (4a)" % (
            S[CH10]["n"], card and card["count"], BASE[:7], Sb[CH10]["n"], cls_text, len(ch10_keys), not run_old["part"]),
            S[CH10]["n"] == S[CH10]["cache"] == S[CH10]["run"] == run_old["n"] == want10 and card and card["count"] == "%d questions" % want10
            and cls_text == "{:,}".format(len(nb["questions"])) and new["meta"] == len(nb["questions"]) == len(ob["questions"]) + len(NEW) and run_old["part"] is False and run_old["full"] is True,
            {"sizes": S[CH10], "card": card, "cls": cls_text, "run": run_old})
    finally:
        rig.close()
chk("no page errors (%s)" % (errs_all[:2] or "none"), not errs_all, errs_all[:4])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
