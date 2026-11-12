#!/usr/bin/env python3
"""Question audit, step 1: for every Fire Code question, what the app draws for its citation.

With the owner's own IFC PDF loaded the way a reader loads it (Load my IFC PDF) and pdf.js served from a local copy, this asks the app's own
code path (V.locate + V.computeClip; V.countyClip for the county booklet; buildIfcRef for the card) for each question and writes, per id, under OUT:
    <id>.json        the record: marks (the text under each gold mark), the cited text, the pointer / page lines, the keyed answer
    <id>.crop.jpg    the card's own picture (the framed, highlighted crop), screenshotted off the page at device scale 2
    <id>.p<k>.jpg    the whole cited page(s) painted with the same marks (licence footer painted over)
It resumes: an id whose <id>.json exists is skipped. The book never goes into the repo (it is public): its path is given when this is run.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/qaudit-render.py OUT [--ids a,b] [--unit 1] [--limit N] [--page-scale 1.3]
"""
import os, sys, json, mimetypes, re, base64, io, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "build/pdf.min.mjs") or not os.path.isfile(BOOK):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF"); sys.exit(0)
from PIL import Image
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "qaudit"}
_argv = sys.argv[:]; sys.argv = [sys.argv[0]]
exec(src, G)
sys.argv = _argv
from playwright.sync_api import sync_playwright
PAGE_SCALE = float(arg("--page-scale", "1.3")); PAGE_W = int(arg("--page-width", "900"))
VIEWER = open(arg("--viewer"), encoding="utf-8").read() if arg("--viewer") else None      # another ifc-viewer.js (e.g. the unmerged build 384.56's), served instead of the tree's own
PATCH = json.load(open(arg("--patch"))) if arg("--patch") else None                        # id -> pointer keys laid over the bank's citation (the 384.56 IFC_POINTER_PATCH), as that build's app does
def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
def open_app(br, w=440, h=956, dpr=2):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=dpr)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    if VIEWER is not None: ctx.route("**/ifc/ifc-viewer.js*", lambda route, request: route.fulfill(status=200, body=VIEWER, content_type="text/javascript"))
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.route("**/index.html", lambda route, request, b=G["g"]["patched"]((59, 0, 34, 0)): route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, errs
def load_book(pg):
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    for _ in range(4800):
        if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
        pg.wait_for_timeout(250)
    acc = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? o.classList.contains('is-ok') : null; }")
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(1200)
    return acc
def main():
    t0 = time.time()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=G["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
        ctx, pg, errs = open_app(br)
        acc = load_book(pg)
        print("book accepted:", acc, "in %.0fs" % (time.time() - t0), flush=True)
        if not acc: sys.exit(2)
        pg.evaluate(open(os.path.join(HERE, "qaudit-page.js"), encoding="utf-8").read())
        if PATCH: pg.evaluate("""(P) => { for (const q of QUESTIONS) if (q.ifc && P[q.ifc.id]) q.ifc = Object.assign({}, q.ifc, { citation: Object.assign({}, q.ifc.citation, P[q.ifc.id]) }); ifcNodeCache.clear(); }""", PATCH)
        ids = pg.evaluate("()=>__qa.ids()")
        if arg("--ids"): ids = [i for i in ids if i in arg("--ids").split(",")]
        if arg("--unit"):
            bs = open(os.path.join(ROOT, "ifc", "bank.js"), encoding="utf-8").read(); bank = json.loads(bs[bs.index("{"): bs.rindex("}") + 1])
            want = {q["id"] for q in bank["questions"] if q["unit"] in arg("--unit").split(",")}; ids = [i for i in ids if i in want]
        todo = [i for i in ids if not os.path.exists(os.path.join(OUT, i + ".json"))]
        if arg("--limit"): todo = todo[: int(arg("--limit"))]
        if arg("--max"): todo = todo[: int(arg("--max"))]                  # a fresh browser every N questions (the page's caches grow)
        print("%d questions, %d to do" % (len(ids), len(todo)), flush=True)
        for n, i in enumerate(todo):
            rec = None
            for attempt in range(3):
                try:
                    rec = pg.evaluate("(id)=>__qa.rec(id)", i)
                    card = pg.evaluate("(id)=>__qa.card(id)", i); rec["card"] = card
                    if card.get("ok"):
                        el = pg.query_selector("#qa-host .ifc-clips")
                        if el:
                            el.scroll_into_view_if_needed(); png = el.screenshot(timeout=15000)
                            im = Image.open(io.BytesIO(png)).convert("RGB"); im.save(os.path.join(OUT, i + ".crop.jpg"), quality=80, optimize=True)
                            rec["crop_px"] = [im.width, im.height]
                    pgs = pg.evaluate("([id, s])=>__qa.pages(id, s)", [i, PAGE_SCALE])
                    rec["pages_meta"] = []
                    for k, im in enumerate(pgs.get("imgs", []) or []):
                        pi = Image.open(io.BytesIO(base64.b64decode(im["url"].split(",", 1)[1]))).convert("RGB")
                        pi = pi.resize((PAGE_W, round(PAGE_W * pi.height / pi.width)), Image.LANCZOS); pi.save(os.path.join(OUT, "%s.p%d.jpg" % (i, k)), quality=60, optimize=True)
                        rec["pages_meta"].append({"w": im["w"], "h": im["h"], "page": (pgs.get("pages") or [None] * (k + 1))[k]})
                    if pgs.get("err"): rec["pages_err"] = pgs["err"]
                    break
                except Exception as e:
                    rec = {"id": i, "error": str(e)[:200]}
                    print("  retry", i, str(e)[:100], flush=True)
                    if "crash" in str(e).lower() or "closed" in str(e).lower():          # the page is gone: leave this id undone and stop; the wrapper starts a new browser
                        try: br.close()
                        except Exception: pass
                        sys.exit(3)
                    try: pg.evaluate("()=>{ document.getElementById('qa-host')?.remove(); }")
                    except Exception: pass
            json.dump(rec, open(os.path.join(OUT, i + ".json"), "w"))
            if n % 25 == 24: print("  ... %d / %d  (%.0fs)" % (n + 1, len(todo), time.time() - t0), flush=True)
        br.close()
    print("done in %.0fs; page errors: %s" % (time.time() - t0, errs[:3]))
main()
