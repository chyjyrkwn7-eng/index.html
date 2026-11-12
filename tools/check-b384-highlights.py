#!/usr/bin/env python3
"""Build 384.41: a highlight reaches the end of its sentence - the whole page and the card's picture, for EVERY county citation.

Madison (iPhone, "Show the whole page", Harris County amendments page 89, D103.6 Signs): "Highlights aren't connecting to the end of
their sentence properly." Circled: the darker band over "Signs shall be spaced not more than 50 feet apart." starts at the right end of
one line and goes on to the next, and on the second line it stops inside "apart" - the full stop is outside it.
The cause: the booklet is set in Calibri and a justified line is one long text run with wide spaces; pdf.js gives a run's start and
width, not its letters, and the kit spread the width over the letters by TIMES' proportions, so a letter's place came out up to four
points wrong by the middle of a line. A highlight's end was then placed inside a word and a "covers at least half of it" rule moved
it onto the nearest word, which here was the one before. The card's picture (reflowed to a book column) marks a word when the kit's mark
covers half of it, so it inherited the same error. Now every letter is placed from the page's own drawing (countyChars: glyphOrigins).

What this holds every county citation (all 421 questions, 410 distinct citations) to, read off the PIXELS of the two pictures the app draws
(the card's picture exactly as ifcFillCode makes it, and V.paintPages, which is "Show the whole page" and Enlarge), at 2 device pixels:
  (1) no word of the print is cut by the edge of a band - a band that ends inside "apart." and leaves the full stop out cuts the word;
  (2) a band starts at the first glyph of the first word it covers and ends at the last glyph of the last (no more than the marker's own
      room beyond them: no gap before a full stop or after a closing quote) - not for a table row, which runs rule to rule on purpose;
  (3) (whole page) the words the bands cover are exactly the words of the cited text found in the page's own text: none left outside, none
      marked that are not cited.
Nothing here reads the kit's marks. The county booklet ships in the repo; the owner's IFC book is not needed (the IFC pointers cannot be
read here: the book is not in the repo, and its pointers use the kit's other reader, findMarks, which this does not touch).
  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> [IFC_BOOK=<the owner's 2021 IFC PDF>] python3 tools/check-b384-highlights.py [--against REV|FILE.html [--viewer FILE.js]] [--quick] [--ids a,b] [--ifc-only]
  (384.56) With IFC_BOOK the same two readings are made for the Fire Code's own book (the IFC leg, at the end): every pointer the 384.56 patch table gives a `find`, and every
  25th Fire Code question, in the whole book page and the code box; skipped without the book (it is not in the repo). --ifc-only runs that leg alone.
  --against REV takes a commit (its index.html AND ifc/ifc-viewer.js are served); a FILE is an index.html (its viewer: --viewer, else
  origin/main's). Against 384.38 (origin/main before this) it FAILS: on the D103.6 sentence and on many more.
OUT_JSON=<file> writes every citation's measurements."""
import os, sys, json, subprocess, mimetypes, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
if not os.path.exists(PDFJS + "build/pdf.min.mjs"):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149"); sys.exit(0)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384hl"}
_argv = sys.argv[:]
for flag in ("--against", "--viewer", "--ids", "--dump"):
    if flag in sys.argv:                                      # the harness reads --against as a file of its own; these are this gate's
        i = sys.argv.index(flag); sys.argv = sys.argv[:i] + sys.argv[i + 2:]
exec(src, G)
sys.argv = _argv
def arg(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None
AGAINST = VIEWER = None
a = arg("--against")
if a:
    if os.path.isfile(a):
        AGAINST = open(a, encoding="utf-8").read()
        v = arg("--viewer")
        VIEWER = open(v, encoding="utf-8").read() if v else subprocess.check_output(["git", "-C", ROOT, "show", "origin/main:ifc/ifc-viewer.js"]).decode("utf-8")
    else:
        AGAINST = subprocess.check_output(["git", "-C", ROOT, "show", a + ":index.html"]).decode("utf-8")
        VIEWER = subprocess.check_output(["git", "-C", ROOT, "show", a + ":ifc/ifc-viewer.js"]).decode("utf-8")
IDS = arg("--ids").split(",") if arg("--ids") else None
DUMP = arg("--dump")                                          # (debug) a folder: every citation's two pictures are written there as PNGs
QUICK = "--quick" in sys.argv
def body_for(ins):
    if AGAINST is None: return G["g"]["patched"](ins)
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return G["g"]["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
def open_app(br, w=440, h=956, dpr=2):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=dpr)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    if VIEWER is not None:
        ctx.route("**/ifc/ifc-viewer.js*", lambda route, request: route.fulfill(status=200, body=VIEWER, content_type="text/javascript"))
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = body_for((59, 0, 34, 0))
    if AGAINST is not None:                                       # (the old build is told it is the newest, so it does not reload itself into the current one)
        import re as _re
        ob = _re.search(r'const APP_BUILD = "([^"]+)"', AGAINST).group(1)
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": ob, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, errs

bs = open(os.path.join(ROOT, "ifc", "bank.js"), encoding="utf-8").read(); bank = json.loads(bs[bs.index("{"): bs.rindex("}") + 1])
cites = []; seen = set()
for q in bank["questions"]:
    c = q["citation"]
    if c.get("source") != "amendment": continue
    k = json.dumps(c, sort_keys=True)
    if k in seen: continue
    seen.add(k); cites.append(q["id"])
nq = sum(1 for q in bank["questions"] if q["citation"].get("source") == "amendment")
if IDS: cites = [c for c in cites if c in IDS]
elif QUICK: cites = cites[::7] + [c for c in ("chAppD-012", "chAppD-011") if c not in cites[::7]]
if "chAppD-012" not in cites and not IDS: cites.append("chAppD-012")
if "--ifc-only" in sys.argv: cites = []          # (only the IFC leg, below)
SPAGE = 1.7
print("%d county questions, %d distinct citations; checking %d (%s)" % (nq, len(seen), len(cites), "the build under test" if AGAINST is None else "AGAINST " + a), flush=True)
rows = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, errs = open_app(br)
    pg.evaluate(open(os.path.join(HERE, "b384-highlights-page.js"), encoding="utf-8").read())
    for n, cid in enumerate(cites):
        r = {}
        for view in ("page", "card"):
            for attempt in range(3):
                try:
                    r[view] = pg.evaluate("([id, s, d]) => window.__hl.%s(id, s, d)" % view, [cid, SPAGE, bool(DUMP)]); break
                except Exception as e:
                    r[view] = {"id": cid, "bad": [["harness error", str(e)[:160]]]}
                    if "closed" in str(e).lower(): break
        rows[cid] = r
        if DUMP:
            import base64
            os.makedirs(DUMP, exist_ok=True)
            for view in ("page", "card"):
                for k, u in enumerate(r[view].pop("img", None) or []): open("%s/%s-%s-%d.png" % (DUMP, cid, view, k), "wb").write(base64.b64decode(u.split(",", 1)[1]))
                if r[view].get("dbg"): json.dump(r[view]["dbg"], open("%s/%s-%s.json" % (DUMP, cid, view), "w"))
        if n % 60 == 59: print("  ... %d / %d" % (n + 1, len(cites)), flush=True)
    br.close()
if os.environ.get("OUT_JSON"): json.dump(rows, open(os.environ["OUT_JSON"], "w"))

def summary(view):
    fails = {cid: r[view] for cid, r in rows.items() if r[view].get("bad")}
    kinds = collections.Counter(b[0] for r in fails.values() for b in r["bad"])
    return fails, kinds
print("\nLines read: whole page %d lines, %d bands; card %d lines, %d bands" % (
    sum(r["page"].get("lines", 0) for r in rows.values()), sum(r["page"].get("bands", 0) for r in rows.values()),
    sum(r["card"].get("lines", 0) for r in rows.values()), sum(r["card"].get("bands", 0) for r in rows.values())))
unver = sum(1 for r in rows.values() if r["page"].get("unverifiable")); noloc = [cid for cid, r in rows.items() if r["page"].get("located") is False]
print("whole page: %d citations with a line whose words could not be told from its print (the band's edges are still checked there); %d whose text was not found" % (unver, len(noloc)))
sample = rows.get("chAppD-012")
if sample:
    for view in ("page", "card"):
        print("D103.6 'Signs shall be spaced not more than 50 feet apart.' %s: %d bands, %s" % (view, sample[view].get("bands", 0), "clean" if not sample[view].get("bad") else sample[view]["bad"][:3]))
for view, label in (("page", "the whole page (Show the whole page / Enlarge)"), ("card", "the card's picture")):
    fails, kinds = summary(view)
    chk("%s: all %d county citations - no word cut by a band's edge, each band from its first glyph to its last, and (page) the cited words and no others" % (label, len(cites)),
        not fails, "%d citations fail: %s; first: %s" % (len(fails), dict(kinds), "; ".join("%s %s" % (cid, f["bad"][0]) for cid, f in list(fails.items())[:5])))
    for cid, f in list(fails.items())[:25]: print("    OFFENDER %s [%s]: %s" % (cid, view, "; ".join("%s (%s)" % (b[0], b[1]) for b in f["bad"][:3])))
    if len(fails) > 25: print("    ... and %d more" % (len(fails) - 25))
if sample:
    chk("D103.6 (chAppD-012), the circled sentence: both views clean, and its band is found", not sample["page"].get("bad") and not sample["card"].get("bad") and sample["page"].get("bands", 0) >= 2 and sample["card"].get("bands", 0) >= 2, sample["page"].get("bad", [])[:2] + sample["card"].get("bad", [])[:2])
# ---- (384.56) the IFC leg: the same two readings off the pixels, for the Fire Code's own book. Needs the owner's PDF (IFC_BOOK), which is not in the repo: skipped without it.
# Every pointer the 384.56 patch table gives a `find` (the footnotes and cells that were never marked) plus every 25th Fire Code question, in both pictures (the whole book
# page and the code box): no word of a marked line cut by a band's edge, each sentence's band from its first glyph to its last (the full stop is inside it), and for the patched
# pointers a band that is there at all (a build before the patch marks only the table's caption, and fails that).
BOOK = os.environ.get("IFC_BOOK", "")
ifc_fails = {}
if os.path.isfile(BOOK):
    import re as _re
    tree = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    blk = tree[tree.index("const IFC_POINTER_PATCH = {"):] if "const IFC_POINTER_PATCH = {" in tree else ""
    blk = blk[: blk.index("\n};")] if blk else ""
    patched = _re.findall(r'^\s*"([A-Za-z0-9-]+)":\s*\{', blk, _re.M)
    ibank = [q["id"] for q in bank["questions"] if q["citation"].get("source") == "ifc" and q.get("type") == "content"]
    patched = [i for i in patched if i in ibank]                # (384.72) the county pointers of the patch table (a `head` / an excerpt) are cut from the booklet: this leg reads the book's
    every = 60 if QUICK else 25
    ifc_ids = patched + [i for i in ibank[::every] if i not in patched]
    if IDS: ifc_ids = [i for i in ifc_ids if i in IDS]
    print("\nIFC leg: %d pointers (%d patched, the rest every %dth), both views" % (len(ifc_ids), len(patched), every), flush=True)
    def load_book(pg):
        pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
        pg.set_input_files("#ifc-book-input", BOOK)
        for _ in range(2400):
            if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
            pg.wait_for_timeout(250)
        acc = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? o.classList.contains('is-ok') : null; }")
        pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
        pg.wait_for_timeout(1200)
        return acc
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=G["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
        ctx, ipg, ierrs = open_app(br)
        accepted = load_book(ipg)
        chk("the owner's IFC PDF is accepted by the app (the leg reads his book)", accepted, accepted)
        ipg.evaluate(open(os.path.join(HERE, "b384-highlights-page.js"), encoding="utf-8").read())
        res_ifc = {}
        for n, iid in enumerate(ifc_ids):
            for view in ("page", "box"):
                for attempt in range(3):
                    try:
                        res_ifc[(iid, view)] = ipg.evaluate("([id, s, v]) => window.__hl.ifcEnds(id, s, v, false)", [iid, SPAGE, view]); break
                    except Exception as e:
                        res_ifc[(iid, view)] = {"id": iid, "bad": [["harness error", str(e)[:160]]]}
                        if "closed" in str(e).lower(): break
            if n % 40 == 39: print("  ... IFC %d / %d" % (n + 1, len(ifc_ids)), flush=True)
        br.close()
    for (iid, view), r in res_ifc.items():
        if r.get("bad"): ifc_fails[(iid, view)] = r
    nread = sum(r.get("checked", 0) for r in res_ifc.values())
    print("IFC leg: %d marked lines read in %d pictures" % (nread, len(res_ifc)))
    chk("IFC (his book), %d pointers x both views: no word of a marked line cut by a band's edge, each sentence's band from its first glyph to its last" % len(ifc_ids), not ifc_fails,
        "%d pictures fail; first: %s" % (len(ifc_fails), "; ".join("%s %s %s" % (k[0], k[1], f["bad"][0]) for k, f in list(ifc_fails.items())[:4])))
    for (iid, view), f in list(ifc_fails.items())[:20]: print("    OFFENDER %s [%s]: %s" % (iid, view, "; ".join("%s (%s)" % (b[0], b[1]) for b in f["bad"][:2])))
    nomark = [(i, v) for i in patched for v in ("page", "box") if i in ifc_ids and res_ifc.get((i, v), {}).get("checked", 0) < 1]
    chk("IFC: every patched pointer (%d) has a gold band on the text that decides its answer, in both pictures (a build before the patch marks the table's caption only)" % len(patched), not nomark, nomark[:6])
    chk("IFC leg: no page errors", not ierrs, ierrs[:2])
else:
    print("\nSKIP the IFC leg: set IFC_BOOK to the owner's 2021 IFC PDF (it is not in the repo)")
chk("no page errors", not errs, errs[:2])
nf = len({cid for cid, r in rows.items() if r["page"].get("bad") or r["card"].get("bad")})
print("\n%d of %d citations fail in at least one view" % (nf, len(cites)))
print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)
