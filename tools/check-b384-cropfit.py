"""Build 384, crops: every "Show the code" picture one family - the amendments as the book's, the heading cited alone, one tag size.
Madison (phone screenshots of Fire Code): "The cropped thing of the 'section 322 battery storage' why doesn't that look like the
rest? Why isn't the word highlighted like the others? Why is it cropped so small like that?" / "ensure that the cropped photo from the
show code drop looks good, it has the context there centered nicely and each one is cohesive so you know what to expect when you hit
the drop down" / "on the amendments one ... some of those don't have the same nice look as the ifc ones" / "sometimes when i hit the
amendment drop down, it comes up as text and not the cropped photo and stuff?" - and, circled on a Review list, the IFC tag beside the
AMENDMENTS tag (two sizes).
Read off the page and the pictures' own pixels, in Fire Code, with the owner's IFC loaded through the app's own path (Load my IFC
PDF) and pdf.js served from a local copy, as an iPhone draws it (deviceScaleFactor 3, 440x956):
(1) THE PICTURE, NEVER THE TEXT FIRST: every county reference (all 421) opened as a tap opens it, watched on every frame from the
    tap until its picture is up: the booklet's words (the text fallback) are never on the screen, and it ends on the picture. The
    first open of a visit (booklet not yet fetched) shows "Opening the code..." and then the picture, never the text.
(2) GUARD - THE FALLBACK: with the booklet unreachable the box still ends on the county's words (no error, no empty box).
(3) THE BOOK'S PRINT SIZE: each county picture's print scale (css px per pdf point) against a book column's (307.4.2 in the same
    card): running text at the column's scale (within 3%), a table kept as cut; at least 85% of all county references, and no more
    than 2% kept as cut that are not tables (the step refuses what it cannot read as plain running text - those are listed).
(4) A HEADING CITED ALONE (the 15 county headings - "SECTION 322 BATTERY STORAGE" - and the 59 IFC section banners): the heading
    carries the marker, and the picture shows lines under it (more lines of print than the heading has).
(5) ONE TAG SIZE: the IFC, AMENDMENTS and HINT pills one width and one height (0.5px), at 440, 375, 834 and at 125% text.
(6) GUARD - THE BUTTONS: Enlarge and "Show the whole (book) page" the same boxes in an IFC card and a county card (width, height,
    place in the card) at 440x956, 834x1194 and 1536x864.
(7) DRAWN AHEAD WITHOUT THE BOOK: a county box sitting in view in a Review list draws its picture while still shut, with no book
    open in memory (the booklet ships with the app).
(8) THE OTHER PLACES: a county flash card shows the picture at a book column's print size there (its card is narrower: the scale a
    column has in that frame), and Enlarge shows it larger, fitted to the viewer;
    an IFC section banner's flash card shows the lines under the banner.
(9) no page errors.
The book never goes into the repo (the repo is public): its path is given when the gate is run.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-cropfit.py [--against REV|FILE]
      [--only 1,3,...]   (--against f9694e7, the start of this work: (1), (3), (4), (5), (7) and (8) FAIL; (2), (6), (9) pass on both)
      --against takes a commit (its index.html AND its ifc/ifc-viewer.js are served) or an index.html file."""
import os, sys, json, subprocess, mimetypes, time, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "build/pdf.min.mjs") or not os.path.isfile(BOOK):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF"); sys.exit(0)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384cropfit"}
_argv = sys.argv[:]
if "--against" in sys.argv:
    i = sys.argv.index("--against"); sys.argv = sys.argv[:i] + sys.argv[i + 2:]
exec(src, G)
sys.argv = _argv
AGAINST = VIEWER = None
if "--against" in sys.argv:
    a = sys.argv[sys.argv.index("--against") + 1]
    if os.path.isfile(a):
        AGAINST = open(a, encoding="utf-8").read()
        v = os.path.join(os.path.dirname(os.path.abspath(a)), "ifc", "ifc-viewer.js")
        VIEWER = open(v, encoding="utf-8").read() if os.path.isfile(v) else None
    else:
        AGAINST = subprocess.check_output(["git", "-C", ROOT, "show", a + ":index.html"]).decode("utf-8")
        VIEWER = subprocess.check_output(["git", "-C", ROOT, "show", a + ":ifc/ifc-viewer.js"]).decode("utf-8")
ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
def want(k): return ONLY is None or k in ONLY
def body_for(ins):
    if AGAINST is None: return G["g"]["patched"](ins)
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return G["g"]["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
from playwright.sync_api import sync_playwright
S = 1.7 * 2          # picture pixels per pdf point at dpr 3 (the kit draws at min(dpr, 2))
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:1500], flush=True)
def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
def open_app(br, w=440, h=956, dpr=3):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=dpr)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    if VIEWER is not None:
        ctx.route("**/ifc/ifc-viewer.js*", lambda route, request: route.fulfill(status=200, body=VIEWER, content_type="text/javascript"))
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = body_for((59, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); try{ localStorage.removeItem('class26e.codeopen'); }catch(e){} }")
    return ctx, pg, errs
def load_book(pg):
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    for _ in range(3600):           # the analysis takes 15s to a few minutes; under heavy load, longer
        if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
        pg.wait_for_timeout(250)
    acc = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? o.classList.contains('is-ok') : null; }")
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(1200)
    return acc
def drill(pg, qid, answer=True):
    pg.evaluate("""(id)=>{ const i = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[i].topic]; beginRun([i]); }""", qid)
    pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(900)
    if not answer: return True
    for _ in range(6):
        c = pg.evaluate("""()=>{ const r=correctSlot(order[pos]); const el=document.querySelector('.qpanel .choice[data-index="'+r+'"]'); if(!el) return null; el.scrollIntoView({block:'center',behavior:'instant'}); const b=el.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }""")
        if c: pg.touchscreen.tap(c[0], c[1])
        pg.wait_for_timeout(1300)
        if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-ref')"): return True
    return False

# a picture read off its pixels: lines of print (bands of rows with dark ink), marker pixels, and its print scale
PIC_JS = r"""
window.__S = 1.7 * Math.min(devicePixelRatio || 1, 2);
window.__pic = function(root){
  const out = { pieces: [], lines: 0, marker: 0, scale: [] };
  root.querySelectorAll('.ifc-clips canvas').forEach(cv => {
    if(cv.classList.contains('ifc-page')){ out.pieces.push({ page: true }); return; }
    const W = cv.width, H = cv.height; if(!W || !H) return;
    const D = cv.getContext('2d').getImageData(0, 0, W, H).data; const rowDark = new Uint8Array(H); let marker = 0;
    for(let y = 0; y < H; y++) for(let x = 0; x < W; x++){ const i = (y * W + x) * 4, r = D[i], g = D[i + 1], b = D[i + 2];
      if(0.299 * r + 0.587 * g + 0.114 * b < 150) rowDark[y] = 1; else if(r > 240 && g > 200 && g < 236 && b < 80) marker++; }
    let lines = 0, gap = 99; for(let y = 0; y < H; y++){ if(rowDark[y]){ if(gap >= 2) lines++; gap = 0; } else gap++; }
    const r = cv.getBoundingClientRect(), scale = r.width / (W / __S);
    /* a column's scale in this frame: the frame's room (less its padding) for a book column's 250pt, at most 1.7 */
    const fr = cv.closest('.ifc-frame'), fs = fr ? getComputedStyle(fr) : null;
    const inner = fr ? fr.clientWidth - parseFloat(fs.paddingLeft) - parseFloat(fs.paddingRight) : r.width;
    out.pieces.push({ W, H, lines, marker, scale: Math.round(scale * 1000) / 1000, col: Math.round(Math.min(1.7, inner / 250) * 1000) / 1000, cssW: Math.round(r.width * 10) / 10 });
    out.lines += lines; out.marker += marker; out.scale.push(scale);
  });
  return out;
};
window.__openWatch = async function(id, host){
  const wt = ms => new Promise(r => setTimeout(r, ms));
  ifcNodeCache.clear();
  const item = QUESTIONS.find(q => q.ifc && q.ifc.id === id);
  const node = buildBankNote(item); host.replaceChildren(node);
  const d = node.querySelector('details.ifc-code'), sum = d.querySelector(':scope > summary');
  const rec = { id, textFrames: 0, busyFrames: 0, frames: 0 }; let done = false;
  const watch = () => { rec.frames++; const t = node.querySelector('.ifc-county-text'); if(t && !t.hidden && t.getBoundingClientRect().height > 0) rec.textFrames++;
    if(node.querySelector('.ifc-code-body .ifc-busy')) rec.busyFrames++; if(!done) requestAnimationFrame(watch); };
  requestAnimationFrame(watch);
  const t0 = performance.now();
  sum.click();
  for(let k = 0; k < 500; k++){ await wt(25); if(node.querySelector('.ifc-code-body > .ifc-links, .ifc-code-body > .ifc-note, .ifc-code-body > .ifc-locked') || (node.querySelector('.ifc-code-body > .ifc-county-text') && !node.querySelector('.ifc-code-body .ifc-busy') && performance.now() - t0 > 4000)) break; }
  await wt(60); done = true;
  rec.ms = Math.round(performance.now() - t0);
  const t = node.querySelector('.ifc-county-text'); rec.textEnd = !!(t && !t.hidden && t.getBoundingClientRect().height > 0);
  rec.pic = __pic(node);
  rec.excerpt = (item.ifc.citation.excerpt || '').slice(0, 2000);
  try{ localStorage.removeItem('class26e.codeopen'); }catch(e){}
  return rec;
};
true;
"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, errs = open_app(br)
    pg.evaluate(PIC_JS)
    county = pg.evaluate("()=>QUESTIONS.filter(q=>q.ifc && q.ifc.citation.source==='amendment').map(q=>q.ifc.id)")
    heads_c = pg.evaluate("()=>QUESTIONS.filter(q=>q.ifc && q.ifc.citation.source==='amendment' && !q.ifc.citation.highlight && !q.ifc.citation.exceptionText).map(q=>q.ifc.id)")
    heads_b = pg.evaluate("()=>QUESTIONS.filter(q=>q.ifc && q.ifc.citation.source!=='amendment' && /^\\d{2,4}$/.test(q.ifc.citation.section) && !['80','202'].includes(q.ifc.citation.section)).map(q=>q.ifc.id)")
    print("  %d county references (%d a heading alone), %d IFC section banners cited alone" % (len(county), len(heads_c), len(heads_b)), flush=True)
    # a county question drilled before anything has fetched the booklet: its first open, as the first of a visit
    first = None
    if want("1"):
        # a county question drilled before anything has fetched the booklet; then its code opened as the first of a visit
        drill(pg, "nav-NAVB-303")
        pg.evaluate("()=>{ const real=document.querySelector('.qpanel .ifc-ref'); const h=document.createElement('div'); h.id='__host'; real.after(h); real.style.display='none'; }")
        first = pg.evaluate("async ()=>{ ifcCountyP = null; try{ ifcCountyLineCache.clear(); }catch(e){} return __openWatch('nav-NAVB-303', document.getElementById('__host')); }")
        print("  first open of a visit: %s" % {k: first[k] for k in ("textFrames", "busyFrames", "frames", "ms", "textEnd")}, flush=True)
    if want("7"):
        # (7) a Review list of a county unit, no book open in memory (none loaded yet): a box in view draws while shut
        pg.evaluate("""()=>{ const q = QUESTIONS.find(q=>q.ifc && q.ifc.id==='nav-NAVB-303'); showAnswerReview([q.topic.trim()], 'all'); }""")
        pg.wait_for_timeout(2500)
        pg.evaluate("""()=>{ const s=[...document.querySelectorAll('#stage .ifc-ref')].find(b=>b.querySelector('.ifc-tag.is-county')); if(s){ s.id='__cbox'; s.scrollIntoView({block:'center'}); } }""")
        drawn = None
        for _ in range(60):
            drawn = pg.evaluate("()=>{ const b=document.getElementById('__cbox'); if(!b) return null; const d=b.querySelector('details'); return !d.open && !!b.querySelector('.ifc-code-body .ifc-clips canvas'); }")
            if drawn: break
            pg.wait_for_timeout(250)
        chk("(7) a county box sitting in view in a Review list draws its picture while still shut, with no book open in memory (%s)" % pg.evaluate("()=>typeof ifcBook === 'undefined' ? 'n/a' : !!ifcBook"), drawn is True, drawn)
    t = time.time(); acc = load_book(pg)
    print("  the owner's IFC loaded through Load my IFC PDF: %s (%ds)" % (acc, time.time() - t), flush=True)
    drill(pg, "ch3-053")
    pg.evaluate("()=>{ const real=document.querySelector('.qpanel .ifc-ref'); const h=document.createElement('div'); h.id='__host'; real.after(h); real.style.display='none'; }")
    pg.evaluate(PIC_JS)
    res = []
    if want("1") or want("3") or want("4"):
        t = time.time()
        for k in range(0, len(county), 25):
            res += pg.evaluate("async (ids)=>{ const out=[]; for(const id of ids) out.push(await __openWatch(id, document.getElementById('__host'))); return out; }", county[k:k + 25])
        print("  opened every county reference (%ds)" % (time.time() - t), flush=True)
    if want("1"):
        texty = [(r["id"], r["textFrames"]) for r in res if r["textFrames"]]
        nopic = [r["id"] for r in res if r["textEnd"] or not r["pic"]["pieces"]]
        chk("(1) every county reference opens on its picture, never its text (text on screen in %d of %d opens; first open of a visit: text %d frames, 'Opening the code' %d frames)"
            % (len(texty), len(res), first["textFrames"], first["busyFrames"]),
            res and not texty and not nopic and first and first["textFrames"] == 0 and not first["textEnd"] and first["busyFrames"] > 0, {"text": texty[:8], "noPicture": nopic[:8]})
    if want("2"):
        ctx2, pg2, errs2 = open_app(br)
        pg2.route("**/harris-county-amendments.pdf*", lambda route, request: route.fulfill(status=404, body=""))
        pg2.evaluate(PIC_JS)
        drill(pg2, "nav-NAVC-031")
        pg2.evaluate("()=>{ const real=document.querySelector('.qpanel .ifc-ref'); const h=document.createElement('div'); h.id='__host'; real.after(h); real.style.display='none'; }")
        fb = pg2.evaluate("async ()=>{ ifcCountyP = null; return __openWatch('nav-NAVC-031', document.getElementById('__host')); }")
        words = pg2.evaluate("()=>{ const t=document.querySelector('#__host .ifc-county-text'); return t ? t.textContent.slice(0, 60) : null; }")
        chk("(2) GUARD: the booklet unreachable, the box ends on the county's words (%r), no error" % words, fb["textEnd"] and words and not errs2, [fb, errs2[:2]])
        ctx2.close()
    col = None
    if want("3") or want("8"):
        # a book column's scale in the same card: 307.4.2
        pg.evaluate("async ()=>{ await __openWatch('ch3-053', document.getElementById('__host')); }")
        col = pg.evaluate("()=>__pic(document.getElementById('__host')).scale[0]")
        print("  a book column in this card: %.3f css px a point" % col, flush=True)
    if want("3"):
        at, cut, bad = [], [], []
        for r in res:
            sc = r["pic"]["scale"]
            if not sc: bad.append((r["id"], "no picture")); continue
            if all(abs(x / col - 1) <= 0.03 for x in sc): at.append(r["id"])
            elif "TABLE" in r["excerpt"].upper() or " | " in r["excerpt"]: cut.append(r["id"])
            else: bad.append((r["id"], [round(x, 3) for x in sc]))
        med = statistics.median([min(r["pic"]["scale"]) for r in res if r["pic"]["scale"]])
        chk("(3) county pictures at a book column's print size: %d of %d (median %.3f against the column's %.3f px a point); %d tables kept as cut; %d other kept as cut (the set-to-a-column step refuses a piece it cannot read as plain running text: %s)"
            % (len(at), len(res), med, col, len(cut), len(bad), [b[0] for b in bad][:6]), len(at) >= 0.85 * len(res) and len(bad) <= 0.02 * len(res), bad[:10])
    if want("4"):
        hb = []
        for k in range(0, len(heads_b), 20):
            hb += pg.evaluate("async (ids)=>{ const out=[]; for(const id of ids) out.push(await __openWatch(id, document.getElementById('__host'))); return out; }", heads_b[k:k + 20])
        # the heading's own height: the kit's heading marks (points); the picture's print must reach a line of text below it
        hl = pg.evaluate("""async (ids)=>{ const V = await ifcViewer(); const out = {}; const book = await ifcEnsureBook(); const doc = await ifcCountyDoc();
          for(const id of ids){ const c = QUESTIONS.find(q=>q.ifc && q.ifc.id===id).ifc.citation; let clip;
            if(c.source === 'amendment') clip = await V.countyClip(doc, c, ifcCountyOpts); else clip = await V.computeClip(book.doc, book.index, V.locate(book.index, c), c, book.opts);
            const hm = (clip.marks || []).filter(m => m.kind === 'heading');
            out[id] = hm.length ? Math.max(...hm.map(m => m.y1)) - Math.min(...hm.map(m => m.y0)) : 0; }
          return out; }""", heads_b + heads_c)
        byid = {r["id"]: r for r in res}
        probs = []
        for r in [byid[i] for i in heads_c if i in byid] + hb:
            p = r["pic"]; tall = sum(x.get("H", 0) for x in p["pieces"]) / S - 1
            if not p["marker"]: probs.append((r["id"], "the heading is not marked"))
            if tall < hl.get(r["id"], 0) + 9: probs.append((r["id"], "%.0fpt of print, the heading alone %.0fpt" % (tall, hl.get(r["id"], 0))))
        nb = len(heads_c) + len(hb)
        chk("(4) a heading cited alone (%d county, %d IFC banners): the heading marked and lines under it in every picture (%d not)" % (len(heads_c), len(hb), len(probs)),
            nb >= 70 and not probs, probs[:10])
    if want("5"):
        rows = []
        hint = pg.evaluate("""async ()=>{ const V = await ifcViewer(); const doc = await ifcCountyDoc();
          for(const q of QUESTIONS.filter(q => q.ifc && q.ifc.citation.source === 'amendment' && !q.ifc.citation.blur && V.answerNumbers(q.ifc).length)){
            const clip = await V.countyClip(doc, q.ifc.citation, ifcCountyOpts); if(clip.ok && await V.hideAnswer(doc, clip, V.answerNumbers(q.ifc))) return q.ifc.id; } return null; }""")
        for label, w, h, fs in (("440", 440, 956, 1), ("375", 375, 667, 1), ("834", 834, 1194, 1), ("440 @125%", 440, 956, 1.25)):
            pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(700)
            pg.evaluate("(z)=>{ document.documentElement.style.fontSize = z === 1 ? '' : (16 * z) + 'px'; }", fs); pg.wait_for_timeout(300)
            box = {}
            for qid, sel in (("ch3-053", ".qpanel .ifc-code-sum .ifc-tag"), ("nav-NAVC-031", ".qpanel .ifc-code-sum .ifc-tag"), (hint, ".qpanel .ifc-hint-btn .ifc-tag")):
                drill(pg, qid, answer=sel.find("hint") < 0)
                try: pg.wait_for_selector(sel, timeout=20000)
                except Exception: pass
                box[qid] = pg.evaluate("(sel)=>{ const t=document.querySelector(sel); if(!t) return null; const r=t.getBoundingClientRect(); return [Math.round(r.width*100)/100, Math.round(r.height*100)/100, t.textContent.trim()]; }", sel)
            pg.evaluate("()=>{ document.documentElement.style.fontSize=''; }")
            vals = [v for v in box.values() if v]
            same = len(vals) == 3 and max(v[0] for v in vals) - min(v[0] for v in vals) <= 0.5 and max(v[1] for v in vals) - min(v[1] for v in vals) <= 0.5
            rows.append((label, same, [(v[2], v[0], v[1]) for v in vals]))
        pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(500)
        chk("(5) the IFC, AMENDMENTS and HINT tags one width and one height: %s" % "; ".join("%s %s" % (l, v) for l, _, v in rows), all(s for _, s, _ in rows), rows)
    if want("6"):
        LINKS = """()=>{ const card = document.querySelector('.qpanel .ifc-ref'); const c = card.getBoundingClientRect();
          return [...card.querySelectorAll('.ifc-links .ifc-link')].filter(b => b.offsetWidth).map(b => { const r = b.getBoundingClientRect();
            return [Math.round((r.left - c.left) * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; }); }"""
        out = []
        for label, w, h in (("440x956", 440, 956), ("834x1194", 834, 1194), ("1536x864", 1536, 864)):
            pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(800)
            got = {}
            for qid in ("ch3-053", "nav-NAVC-031"):
                drill(pg, qid)
                pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code'); if(d && !d.open) d.open = true; }")
                for _ in range(120):
                    if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-code[open] .ifc-links .ifc-link')"): break
                    pg.wait_for_timeout(250)
                pg.wait_for_timeout(300)
                got[qid] = pg.evaluate(LINKS)
            a, b = got["ch3-053"], got["nav-NAVC-031"]
            same = len(a) == 2 and len(b) == 2 and all(abs(x - y) <= 0.5 for p, q in zip(a, b) for x, y in zip(p, q))
            out.append((label, same, a, b))
        pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(500)
        chk("(6) GUARD: Enlarge and the whole page the same boxes in an IFC card and a county card (%s)" % "; ".join("%s %s" % (l, a) for l, _, a, _ in out),
            all(s for _, s, _, _ in out), out)
    if want("8"):
        if col is None: col = 302 / 250.0
        probs = []
        # a county flash card, and an IFC section banner's
        for qid, kind in (("nav-NAVC-031", "county"), ("nav-NAVB-027", "banner")):
            pg.evaluate("""(id)=>{ const q = QUESTIONS.find(q=>q.ifc && q.ifc.id===id); showFlashcards([q.topic.trim()], 'all'); }""", qid); pg.wait_for_timeout(1200)
            # that card itself (showFlashcards deals a new deck from its first card; renderFlashcard shows the one at fc.pos)
            at = pg.evaluate("""(id)=>{ const want = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); const at = fc.deck.indexOf(want); if(at >= 0){ fc.pos = at; renderFlashcard(); } return at; }""", qid); pg.wait_for_timeout(900)
            if at < 0: probs.append((qid, "not in its unit's flash cards")); continue
            pg.evaluate("()=>{ const c=document.querySelector('.fc-card'); c && c.click(); }"); pg.wait_for_timeout(800)
            pg.evaluate("()=>{ const d=document.querySelector('.fc-card .fc-back details.ifc-code'); if(d && !d.open) d.open = true; }")
            for _ in range(120):
                if pg.evaluate("()=>!!document.querySelector('.fc-card .fc-back .ifc-code-body .ifc-links')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(400)
            p = pg.evaluate("(id)=>{ const b=document.querySelector('.fc-card .fc-back .ifc-ref'); const ok = QUESTIONS[fc.deck[fc.pos]].ifc.id === id; return b && ok ? __pic(b) : null; }", qid)
            if not p or not p["pieces"]: probs.append((qid, "no picture on the flash card")); continue
            if kind == "county" and not all(abs(x["scale"] / x["col"] - 1) <= 0.03 for x in p["pieces"] if not x.get("page")):
                probs.append((qid, "flash card print scale %s against its column's %s" % ([x["scale"] for x in p["pieces"]], [x["col"] for x in p["pieces"]])))
            if kind == "banner" and p["lines"] < 4: probs.append((qid, "flash card banner picture: %d lines" % p["lines"]))
        # Enlarge on a county picture: the same column picture, fitted to the viewer
        drill(pg, "nav-NAVC-031")
        pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code'); if(d && !d.open) d.open = true; }")
        for _ in range(120):
            if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-code-body .ifc-links')"): break
            pg.wait_for_timeout(250)
        pg.evaluate("()=>{ const b=[...document.querySelectorAll('.qpanel .ifc-links .ifc-link')].find(x=>/Enlarge/.test(x.textContent)); b && b.click(); }")
        for _ in range(80):
            if pg.evaluate("()=>!!document.querySelector('.ifc-vz-pages canvas')"): break
            pg.wait_for_timeout(250)
        pg.wait_for_timeout(700)
        vz = pg.evaluate("""()=>{ const cv = document.querySelector('.ifc-vz-pages canvas'); if(!cv) return null; const sc = document.querySelector('.ifc-vz-scroll').getBoundingClientRect();
          const r = cv.getBoundingClientRect(); return { W: cv.width, fit: Math.round(r.width / sc.width * 100) / 100, perPt: r.width / (cv.width / (2.6 * Math.min(devicePixelRatio, 2))) }; }""")
        pg.evaluate("()=>document.querySelector('.ifc-vz .ifc-vz-btn.is-done')?.click()"); pg.wait_for_timeout(600)
        if not vz: probs.append(("Enlarge", "nothing drawn"))
        else:
            if vz["fit"] < 0.85: probs.append(("Enlarge", "not fitted to the viewer: %s" % vz["fit"]))
            if vz["perPt"] < col * 1.05: probs.append(("Enlarge", "the county print no larger than the card's: %.3f px a point" % vz["perPt"]))
        chk("(8) the county picture at the book's print size on a flash card and larger in Enlarge; a banner's flash card shows the lines under it (%s)" % (vz,), not probs, probs)
    chk("(9) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
