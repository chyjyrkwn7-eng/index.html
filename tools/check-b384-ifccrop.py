"""Build 384, round 3: every code picture framed like 307.4.2; the tag pills; Enlarge.
Madison (phone screenshots): "The 307 looks a lot better because it's nicely centered in the crop ... all the cropped stuff needs to
look that good" / "a lot of that crop stuff isn't even rightly placed? ... The titles and stuff. Everything needs to be cohesive too,
because some of the cropped stuff if its code runs border to border" / "the word amendments, ifc aren't centered perfectly in the
little bubble" / "The word enlarge and magnifying glass could look better, the 'view entire page' looks amazing, it's perfect.
Ensure the enlarge one is just as great".
Everything is read off the page - the pictures' own pixels, the boxes the app lays out - with the owner's IFC loaded through the
app's own path (Load my IFC PDF, the Analyzing screen) and pdf.js served from a local copy, in Fire Code, as his iPhone draws it
(deviceScaleFactor 3):
(1) EVERY REFERENCE (all 1,812: 1,391 from the book, 421 from the county booklet - or a stratified sample with --sample N), built
    by the app (buildBankNote -> "Show the code" opened) in the answer card of a real Drill question, laid out at the card's width
    on a 440 phone and again at a 375 phone's. For each piece of the picture, its ink (every pixel that is not the paper: print,
    rules, highlight, blur) against the yellow box it shows in (the frame, or the canvas itself, cut to what can be seen):
    (1a) drawn, and nothing of the ink touches or is cut by an edge of its box (no sideways scrolling, nothing past an edge);
    (1b) the print centred: left and right margins equal within 1px (a change bar - the book's thick bar in the margin - is set
         aside: the text is what is centred, and the bar must still be inside the box);
    (1c) one padding rule: every margin at least 10px, and the top and bottom margins the same in every picture (10-16px);
    (1d) the box is the card's width (one family: every picture the same width as the card it sits in);
    (1e) WHAT is cut and marked is the kit's: the pixels inked in the app's picture are exactly the ones the kit's own paint()
         inks for that reference (same count, same colour sum), and the highlight is there wherever the kit marks one.
         (384 crops) A county picture whose running text the app sets again at a book column's width (ifcCountyColumn,
         check-b384-cropfit) holds the kit's print instead - its dark pixels within 2% - and a marker wherever the kit marks one;
         its pieces share one window, so they are centred as one.
(2) THE BLURRED PICTURES: every definition shown before the answer with its term blurred (ifcPreAnswer), and a sample of Drill
    Hints (the number blurred): the app's picture holds exactly the kit's blurred pixels (it hides what it hid - the part that
    holds on both builds), and is framed by (1a)-(1c) (the part that fails before).
(3) THE OTHER PLACES: a Fire Code flash card's answer side and the page viewer (Enlarge) show the same framed, centred picture.
(4) THE TAG PILLS "IFC", "AMENDMENTS" and the Hint's "HINT" with its bulb: the ink (glyph pixels, screenshots at dpr 3) centred in
    the pill horizontally and vertically within 0.5px - averaged over six sub-pixel placements (any one placement adds up to a
    device pixel of rounding that no style can remove), every placement within 0.75px - at 440, 375 and 440 with 125% text.
(5) ENLARGE AND THE WHOLE PAGE: the same height, padding, type, colour, fill and rounding; each 44px+; mark and word centred
    together in each (1px); stacked both the card's full width, or side by side two equal halves filling the row - at 440x956,
    375x667, an iPad Pro 11" 834x1194 and a 1536x864 laptop.
(6) PERFORMANCE: the time the framing adds to drawing a picture (reported: median and worst, and against the kit's paint).
(7) no page errors.
The book never goes into the repo (the repo is public): its path is given when the gate is run.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-ifccrop.py
          [--against REV|FILE] [--sample N | --ids id,id] [--only 1,2,3,4,5,6]
      (--against 39d5b0c, the start of this work: (1a)-(1d), (2), (3), (4) and (5) FAIL; (0), (1), (1e) and (7) are guards that
      pass on both; (6) has nothing to time there)
OUT_JSON=<file> writes every reference's measurements (margins, ink) - kept out of the repo like the book."""
import os, sys, json, io, re, subprocess, mimetypes, statistics, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "build/pdf.min.mjs") or not os.path.isfile(BOOK):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF"); sys.exit(0)
try:
    from PIL import Image
    import numpy as np
except Exception:
    print("SKIP: needs Pillow and numpy for the pill measurements"); sys.exit(0)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ifccrop"}
_argv = sys.argv[:]
if "--against" in sys.argv:   # the harness reads --against as a file of its own; this gate takes a commit too, so it is kept from it
    i = sys.argv.index("--against"); sys.argv = sys.argv[:i] + sys.argv[i + 2:]
exec(src, G)
sys.argv = _argv
AGAINST = None
if "--against" in sys.argv:
    a = sys.argv[sys.argv.index("--against") + 1]
    AGAINST = open(a, encoding="utf-8").read() if os.path.isfile(a) else subprocess.check_output(["git", "-C", ROOT, "show", a + ":index.html"]).decode("utf-8")
def body_for(ins):
    if AGAINST is None: return G["g"]["patched"](ins)
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return G["g"]["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
SAMPLE = int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0
IDS = sys.argv[sys.argv.index("--ids") + 1].split(",") if "--ids" in sys.argv else None
ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
def want(k): return ONLY is None or k in ONLY
OUT_JSON = os.environ.get("OUT_JSON", "")
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:1200], flush=True)
def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})

def open_app(br, w=440, h=956):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=3)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = body_for((59, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, errs
def load_book(pg):
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    for _ in range(1200):
        if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
        pg.wait_for_timeout(250)
    acc = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? o.classList.contains('is-ok') : null; }")
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(1200)
    return acc
HINTS_JS = r"""async (n)=>{ const V = await ifcViewer(); const doc = await ifcCountyDoc(); const book = await ifcEnsureBook(); const out = [];
  const qs = QUESTIONS.filter(q => q.ifc && !q.ifc.citation.blur && V.answerNumbers(q.ifc).length);
  const book1 = qs.filter(q => q.ifc.citation.source !== 'amendment'), county = qs.filter(q => q.ifc.citation.source === 'amendment');
  for(const q of [].concat(...book1.map((b, i) => [b, county[i]]).flat()).filter(Boolean)){            /* book and county in turn */
    const c = q.ifc.citation; let clip = null, d = doc;
    if(c.source === 'amendment') clip = await V.countyClip(doc, c, ifcCountyOpts);
    else { const l = V.locate(book.index, c); if(!l.ok || ['figure','entry','table','pages'].includes(l.kind)) continue; d = book.doc; clip = await V.computeClip(book.doc, book.index, l, c, book.opts); }
    if(clip && clip.ok && await V.hideAnswer(d, clip, V.answerNumbers(q.ifc))) out.push(q.ifc.id);
    if(out.length >= n) break; }
  return out; }"""
def find_hints(n): return pg.evaluate(HINTS_JS, n)
TAPC = """(sel)=>{ const el=document.querySelector(sel); if(!el) return null; el.scrollIntoView({block:'center',behavior:'instant'}); const b=el.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }"""
def drill(pg, qid, answer=True):
    """a real Drill on one Fire Code question; answered right by a touch unless answer is False"""
    pg.evaluate("""(id)=>{ const i = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[i].topic]; beginRun([i]); }""", qid)
    pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(900)
    if not answer: return True
    for _ in range(6):
        c = pg.evaluate("""()=>{ const r=correctSlot(order[pos]); const el=document.querySelector('.qpanel .choice[data-index="'+r+'"]'); if(!el) return null; el.scrollIntoView({block:'center',behavior:'instant'}); const b=el.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }""")
        if c: pg.touchscreen.tap(c[0], c[1])
        pg.wait_for_timeout(1300)
        if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-ref')"): return True
    return False

# ---- the picture's ink, read off its pixels (the gate's own reading: paper = the colour the edges share; a change bar = a solid
#      upright bar a few points wide alone at one side, clear of the text) and laid against the box it shows in ----
INK_JS = r"""
window.__inkSeen = new WeakMap();
window.__inkOf = function(cv, s){
  if(__inkSeen.has(cv)) return __inkSeen.get(cv);
  const k = __inkRead(cv, s); __inkSeen.set(cv, k); return k;
};
window.__inkRead = function(cv, s){
  const W = cv.width, H = cv.height; if(!W || !H) return null;
  let D; try{ D = cv.getContext('2d').getImageData(0, 0, W, H).data; }catch(e){ return null; }
  const at = (x, y) => (y * W + x) * 4, samp = [at(0,0), at(W-1,0), at(0,H-1), at(W-1,H-1), at(W>>1,0), at(W>>1,H-1), at(0,H>>1), at(W-1,H>>1)];
  const votes = {}; let paper = null, best = 0;
  for(const i of samp){ const k = D[i]+','+D[i+1]+','+D[i+2]; votes[k] = (votes[k]||0) + 1; if(votes[k] > best){ best = votes[k]; paper = [D[i], D[i+1], D[i+2]]; } }
  const colN = new Uint32Array(W); let y0 = -1, y1 = -1, n = 0, sum = 0, marks = 0, dk = 0;
  for(let y = 0; y < H; y++){ const o = y * W * 4; for(let x = 0; x < W; x++){ const i = o + x * 4;
    if(299 * D[i] + 587 * D[i+1] + 114 * D[i+2] < 150000) dk++;
    const d = Math.abs(D[i]-paper[0]) + Math.abs(D[i+1]-paper[1]) + Math.abs(D[i+2]-paper[2]);
    if(d > 40){ colN[x]++; if(y0 < 0) y0 = y; y1 = y; n++; sum += D[i] + D[i+1] + D[i+2]; if(D[i] > 200 && D[i+2] < 120) marks++; } } }
  if(y0 < 0) return { W, H, paper, n: 0, dk };
  let x0 = 0; while(!colN[x0]) x0++; let x1 = W - 1; while(!colN[x1]) x1--;
  const bar = (side) => {                              /* the text's edge on this side, a margin bar set aside */
    const step = side < 0 ? 1 : -1, e = side < 0 ? x0 : x1; let x = e, w = 0;
    while(x >= 0 && x < W && colN[x]){ w++; x += step; }
    let gap = 0; while(x >= 0 && x < W && !colN[x]){ gap++; x += step; }
    if(w < 1.5 * s || w > 6.5 * s || gap < 3.5 * s || x < 0 || x >= W) return [e, false];
    const a = Math.min(e, e + step * (w - 1)), b = Math.max(e, e + step * (w - 1)); let rows = 0, solid = 0;
    for(let y = y0; y <= y1; y++){ let c = 0; for(let xx = a; xx <= b; xx++){ const i = at(xx, y); if(Math.abs(D[i]-paper[0]) + Math.abs(D[i+1]-paper[1]) + Math.abs(D[i+2]-paper[2]) > 40) c++; }
      if(c){ rows++; if(c >= .8 * w) solid++; } }
    return rows >= 6 * s && solid >= .9 * rows ? [x, true] : [e, false];
  };
  const [tx0, bl] = bar(-1), [tx1, br] = bar(1);
  return { W, H, paper, n, sum, marks, dk, x0, x1, y0, y1, tx0, tx1, bars: (bl ? 1 : 0) + (br ? 1 : 0) };
};
window.__measure = function(root, s){
  const holder = root.querySelector('.ifc-code-body .ifc-clips') || root.querySelector('.ifc-clips') || root;
  const hr = holder.getBoundingClientRect(), hs = getComputedStyle(holder);
  const clipX = (hs.overflowX !== 'visible') ? [hr.left, hr.right] : null;
  const card = holder.parentElement.getBoundingClientRect();
  const out = [];
  holder.querySelectorAll('canvas').forEach(cv => {
    if(cv.classList.contains('ifc-page')){ out.push({ page: true }); return; }
    const k = __inkOf(cv, s); if(!k || !k.n){ out.push({ blank: true }); return; }
    const box = cv.closest('.ifc-frame') || cv; const b = box.getBoundingClientRect(), r = cv.getBoundingClientRect();
    let bl = b.left, brt = b.right; if(clipX){ bl = Math.max(bl, clipX[0]); brt = Math.min(brt, clipX[1]); }
    const fx = r.width / k.W, fy = r.height / k.H;
    const X = x => r.left + x * fx, Y = y => r.top + y * fy, q = v => Math.round(v * 100) / 100;
    out.push({ framed: box !== cv, W: k.W, H: k.H, n: k.n, sum: k.sum, marks: k.marks, dk: k.dk, bars: k.bars,
      L: q(X(k.tx0) - bl), R: q(brt - X(k.tx1 + 1)), aL: q(X(k.x0) - bl), aR: q(brt - X(k.x1 + 1)), T: q(Y(k.y0) - b.top), B: q(b.bottom - Y(k.y1 + 1)),
      boxW: q(brt - bl), cardW: q(card.width), cssW: q(r.width) });
  });
  return out;
};
/* the kit's own paint of a reference, measured the same way: what the picture must hold */
window.__kitInk = async function(item, s, opts){
  const V = await ifcViewer(), c = item.ifc.citation; let doc, clip;
  if(c.source === 'amendment'){ doc = await ifcCountyDoc(); clip = await V.countyClip(doc, c, ifcCountyOpts); }
  else { const book = await ifcEnsureBook(); doc = book.doc; const loc = V.locate(book.index, c); if(!loc.ok || loc.kind === 'pages') return null; clip = await V.computeClip(book.doc, book.index, loc, c, book.opts); }
  if(!clip || !clip.ok) return null;
  const tmp = document.createElement('div'); const t0 = performance.now();
  await V.paint(doc, opts && opts.hide ? { ...clip, hide: opts.hide.hide, hiddenText: opts.hide.hiddenText } : clip, tmp, { scale: (opts && opts.scale) || 1.7, ...(opts && opts.blur ? { blur: true } : {}) });
  const ms = performance.now() - t0;
  const keyed = clip.marks.some(m => m.kind === 'cite' || m.kind === 'row');
  const painted = !(opts && opts.blur) && clip.marks.some(m => m.kind === 'cite' || m.kind === 'row' || m.kind === 'exception' || m.kind === 'exceptionNumber' || (m.kind === 'heading' && !keyed));
  let n = 0, sum = 0, marks = 0, dk = 0, kW = 0;
  tmp.querySelectorAll('canvas').forEach(cv => { const k = __inkOf(cv, s); kW = Math.max(kW, cv.width); if(k && k.n){ n += k.n; sum += k.sum; marks += k.marks; dk += k.dk; } });
  /* pieces cut from one window of one page belong together (a table's caption, rows and notes): they are centred as one */
  const keys = clip.segments.filter(sg => !sg.whole).map(sg => sg.page + ':' + sg.x0 + ':' + sg.x1);
  return { n, sum, marks, dk, kW, painted, ms, segs: clip.segments.length, keys };
};
true;
"""
SWEEP = r"""async ([ids, s, w375])=>{
  const wt = ms => new Promise(r => setTimeout(r, ms));
  const panel = document.querySelector('.qpanel'); const real = panel.querySelector('.ifc-ref');
  let h1 = document.getElementById('__h440'), h2 = document.getElementById('__h375');
  if(!h1){ h1 = document.createElement('div'); h1.id = '__h440'; h2 = document.createElement('div'); h2.id = '__h375'; h2.style.width = w375 + 'px';
    real.after(h1, h2); real.style.display = 'none'; }
  const out = [];
  for(const id of ids){
    const i = QUESTIONS.findIndex(q => q.ifc && q.ifc.id === id); const item = QUESTIONS[i];
    const rec = { id, src: item.ifc.citation.source, label: item.ifc.citation.label };
    try{
      ifcNodeCache.clear();
      const node = buildBankNote(item); h1.replaceChildren(node); h2.replaceChildren();
      const d = node.querySelector('details.ifc-code'); d.open = true;
      const t0 = performance.now(); let done = false;
      for(let k = 0; k < 400 && !done; k++){ await wt(50); done = !!node.querySelector('.ifc-code-body > .ifc-links, .ifc-code-body > .ifc-note, .ifc-code-body > .ifc-locked'); }
      rec.fillMs = Math.round(performance.now() - t0);
      rec.locked = !!node.querySelector('.ifc-locked'); rec.note = (node.querySelector('.ifc-code-body > .ifc-note') || {}).textContent || '';
      await wt(30);
      rec.m440 = __measure(node, s);
      h2.appendChild(node); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
      rec.m375 = __measure(node, s);
      rec.kit = await __kitInk(item, s);
      h2.replaceChildren();
    }catch(e){ rec.err = String(e && e.message || e); }
    out.push(rec);
  }
  return out;
}"""

def reset_to_column(m, kit, src):
    """(384 crops) a county picture whose running text the app set again at a book column's width (ifcCountyColumn): its pieces are
    narrower than the kit's cut and share one window"""
    pieces = [x for x in m if not x.get("page") and not x.get("blank")]
    return src == "amendment" and bool(kit) and bool(pieces) and all(x["W"] < 0.8 * kit.get("kW", 0) for x in pieces)
def groups_of(m, kit, src=None):
    pieces = [x for x in m if not x.get("page") and not x.get("blank")]
    if reset_to_column(m, kit, src): return [pieces]
    keys = (kit or {}).get("keys") or []
    if len(keys) != len(pieces): keys = ["piece%d" % k for k in range(len(pieces))]
    groups = {}
    for key, x in zip(keys, pieces): groups.setdefault(key, []).append(x)
    return list(groups.values())
def pic_problems(m, kit, src=None):
    """what is wrong with one reference's picture at one width (an empty list: framed like 307.4.2). Pieces the kit cut from the
    same window of one page (kit["keys"]) are centred as one group: the group's narrowest left and right margins must match."""
    p = []
    pieces = [x for x in m if not x.get("page") and not x.get("blank")]
    if not pieces: return ["no picture drawn"]
    for gi, xs in enumerate(groups_of(m, kit, src)):
        L, R = min(x["L"] for x in xs), min(x["R"] for x in xs)
        if abs(L - R) > 1.0: p.append("%s: off centre (left %s, right %s)" % ("group %d of %d pieces" % (gi + 1, len(xs)) if len(xs) > 1 else "piece %d" % (gi + 1), L, R))
        if len(xs) > 1 and len({round(x["cssW"], 1) for x in xs}) > 1: p.append("group %d: its pieces not one width %s" % (gi + 1, [x["cssW"] for x in xs]))
    for k, x in enumerate(pieces):
        tag = "piece %d" % (k + 1)
        if min(x["aL"], x["aR"], x["T"], x["B"]) < 1: p.append("%s: ink touches or is cut by an edge (L %s R %s T %s B %s)" % (tag, x["aL"], x["aR"], x["T"], x["B"]))
        if min(x["L"], x["R"], x["T"], x["B"]) < 10: p.append("%s: a margin under 10px (L %s R %s T %s B %s)" % (tag, x["L"], x["R"], x["T"], x["B"]))
        if not (10 <= x["T"] <= 16 and 10 <= x["B"] <= 16): p.append("%s: top/bottom not the common padding (T %s B %s)" % (tag, x["T"], x["B"]))
        if abs(x["boxW"] - x["cardW"]) > 1.5: p.append("%s: box %spx in a %spx card" % (tag, x["boxW"], x["cardW"]))
    return p

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, errs = open_app(br)
    t = time.time(); acc = load_book(pg)
    chk("(0) the owner's IFC is accepted through Load my IFC PDF (%ds)" % (time.time() - t), acc is True, acc)
    pg.evaluate(INK_JS)
    S = 1.7 * 2   # the kit draws at scale x min(dpr, 2): picture pixels per pdf point at dpr 3
    ids_all = pg.evaluate("()=>QUESTIONS.filter(q=>q.ifc).map(q=>q.ifc.id)")
    # a real Drill question answered: the card the pictures are laid out in (and its width on a 375 phone)
    drill(pg, "ch3-053")
    w440 = pg.evaluate("()=>document.querySelector('.qpanel .ifc-ref').getBoundingClientRect().width")
    pg.set_viewport_size({"width": 375, "height": 667}); pg.wait_for_timeout(1500)
    w375 = pg.evaluate("()=>document.querySelector('.qpanel .ifc-ref').getBoundingClientRect().width")
    pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(1500)
    print("  the answer card: %.1fpx wide on a 440 phone, %.1fpx on a 375 phone" % (w440, w375), flush=True)
    results = []
    if want("1"):
        ids = [q for q in ids_all if q in IDS] if IDS else ids_all
        if SAMPLE and not IDS:
            # stratified: every unit, both sources, every citation kind, all the new Finder questions
            kinds = pg.evaluate("""async ()=>{ const V = await ifcViewer(); const book = await ifcEnsureBook();
              return QUESTIONS.filter(q=>q.ifc).map(q=>{ const c=q.ifc.citation; let k='county'; if(c.source!=='amendment'){ const l=V.locate(book.index, c); k = l.ok ? l.kind : 'none'; }
                return [q.ifc.id, q.ifc.unit || q.topic, k]; }); }""")
            pick, seen = [], set()
            for qid, unit, kind in kinds:
                key = (unit, kind)
                if key not in seen or qid.startswith("nav-") and qid.split("-")[-1] >= "801": seen.add(key); pick.append(qid)
            rest = [q for q, _, _ in kinds if q not in pick]
            step = max(1, len(rest) // max(1, SAMPLE - len(pick)))
            pick += rest[::step][:max(0, SAMPLE - len(pick))]
            ids = [q for q in ids_all if q in set(pick)]
        print("  (1) %d references%s" % (len(ids), " (those named)" if IDS else " (a stratified sample)" if SAMPLE else " (every one)"), flush=True)
        t = time.time()
        for k in range(0, len(ids), 20):
            res = pg.evaluate(SWEEP, [ids[k:k + 20], S, w375])
            results += res
            if (k // 20) % 10 == 0: print("    %d / %d (%ds)" % (k + len(res), len(ids), time.time() - t), flush=True)
        if OUT_JSON:
            with open(OUT_JSON, "w") as f: json.dump(results, f)
        bad = {"1a": [], "1b": [], "1c": [], "1d": [], "1e": [], "draw": []}
        worst = {"lr": 0, "minm": 99, "tb": [99, 0]}; marked = 0; recol = 0
        for r in results:
            if r.get("err") or r.get("locked") or not r.get("m440"):
                bad["draw"].append((r["id"], r.get("err") or r.get("note") or "locked")); continue
            for wk in ("m440", "m375"):
                for pr in pic_problems(r[wk], r.get("kit"), r.get("src")):
                    key = "1a" if "edge" in pr or "no picture" in pr else "1b" if "off centre" in pr or "one width" in pr else "1d" if "card" in pr else "1c"
                    bad[key].append("%s @%s %s: %s" % (r["id"], wk[1:], r["label"], pr))
                for xs in groups_of(r[wk], r.get("kit"), r.get("src")):
                    worst["lr"] = max(worst["lr"], abs(min(x["L"] for x in xs) - min(x["R"] for x in xs)))
                for x in r[wk]:
                    if x.get("page") or x.get("blank"): continue
                    worst["minm"] = min(worst["minm"], x["L"], x["R"], x["T"], x["B"], x["aL"], x["aR"])
                    worst["tb"] = [min(worst["tb"][0], x["T"], x["B"]), max(worst["tb"][1], x["T"], x["B"])]
            kit = r.get("kit")
            shown = [x for x in r["m440"] if not x.get("page") and not x.get("blank")]
            n = sum(x["n"] for x in shown); sm = sum(x["sum"] for x in shown); mk = sum(x["marks"] for x in shown)
            if kit and kit["marks"]: marked += 1
            if reset_to_column(r["m440"], kit, r.get("src")):
                # the same print (its dark pixels, within 2%: a letter's edge under the marker can cross the threshold) and a marker
                # wherever the kit marks one - laid on whole words now (check-b384-cropfit)
                dk = sum(x.get("dk", 0) for x in shown); recol += 1
                if abs(dk - kit["dk"]) > 0.02 * max(1, kit["dk"]) or (mk > 0) != (kit["marks"] > 0):
                    bad["1e"].append("%s %s (set to a column): kit dark %s marks %s, shown dark %s marks %s" % (r["id"], r["label"], kit["dk"], kit["marks"], dk, mk))
            elif not kit or kit["n"] != n or kit["sum"] != sm or kit["marks"] != mk:
                bad["1e"].append("%s %s: kit %s, shown n %s sum %s marks %s" % (r["id"], r["label"], kit and {k: kit[k] for k in ("n", "sum", "marks", "painted")}, n, sm, mk))
        nb = sum(1 for r in results if r.get("src") != "amendment"); nc = len(results) - nb
        print("  measured %d references (%d book, %d county) at two widths; worst |left-right| %.2fpx, smallest margin %.2fpx, top/bottom %.2f-%.2fpx"
              % (len(results), nb, nc, worst["lr"], worst["minm"], worst["tb"][0], worst["tb"][1]), flush=True)
        chk("(1) every reference's picture is drawn (%d of %d)" % (len(results) - len(bad["draw"]), len(results)), not bad["draw"], bad["draw"][:5])
        chk("(1a) nothing touches or is cut by an edge of its box, at 440 and 375 (%d pictures not so)" % len(bad["1a"]), not bad["1a"], bad["1a"][:6])
        chk("(1b) the print centred, left and right margins within 1px (%d not)" % len(bad["1b"]), not bad["1b"], bad["1b"][:6])
        chk("(1c) one padding rule: every margin 10px+, top and bottom 10-16px in every picture (%d not)" % len(bad["1c"]), not bad["1c"], bad["1c"][:6])
        chk("(1d) every picture's box is the card's width (%d not)" % len(bad["1d"]), not bad["1d"], bad["1d"][:6])
        chk("(1e) GUARD: each picture holds exactly the kit's inked pixels, its highlight included (%d carry one; %d county pictures set to a column hold the kit's print; %d differ)" % (marked, recol, len(bad["1e"])), not bad["1e"], bad["1e"][:6])
        fills = sorted(r["fillMs"] for r in results if r.get("fillMs")); kitms = sorted(r["kit"]["ms"] for r in results if r.get("kit"))
        if fills: print("  draw time per reference (opened -> picture and buttons in place): median %dms, 90th %dms; the kit's paint alone median %dms"
                        % (fills[len(fills) // 2], fills[int(len(fills) * .9)], kitms[len(kitms) // 2] if kitms else -1), flush=True)
    if want("2"):
        # (2) the blurred definitions (ifcPreAnswer, before the answer) and a sample of Drill Hints
        blur = pg.evaluate(r"""async (s)=>{ const wt = ms => new Promise(r => setTimeout(r, ms)); const out = [];
          const items = QUESTIONS.filter(q => q.ifc && q.ifc.citation.blur && q.ifc.blurStem && q.ifc.citation.source !== 'amendment');
          const host = document.createElement('div'); host.style.cssText = 'width:' + document.querySelector('.qpanel').clientWidth + 'px'; document.querySelector('.qpanel').appendChild(host);
          for(const item of items){
            ifcNodeCache.clear(); host.replaceChildren(); const qt = document.createElement('p'); qt.className = 'qtext'; host.appendChild(qt);
            ifcPreAnswer(item, qt, host);
            let pic = null; for(let k = 0; k < 300 && !pic; k++){ await wt(50); pic = host.querySelector('.ifc-blurpic canvas'); }
            await wt(80);
            const m = pic ? __measure(host.querySelector('.ifc-blurpic'), s * 1.5 / 1.7) : null;
            const kit = await __kitInk(item, s * 1.5 / 1.7, { blur: true, scale: 1.5 });
            out.push({ id: item.ifc.id, m, kit });
          }
          host.remove(); return out; }""", S)
        bb = []
        for r in blur:
            m = r["m"]; kit = r["kit"]
            if not m: bb.append((r["id"], "no picture")); continue
            n = sum(x.get("n", 0) for x in m); sm = sum(x.get("sum", 0) for x in m)
            pr = pic_problems(m, kit)
            if not kit or kit["n"] != n or kit["sum"] != sm: pr.append("pixels differ from the kit's blurred paint (%s vs %s)" % (kit and (kit["n"], kit["sum"]), (n, sm)))
            if pr: bb.append((r["id"], pr))
        chk("(2) the %d definitions shown before the answer with the term blurred: the kit's blurred pixels exactly, framed and centred" % len(blur), len(blur) >= 40 and not bb, bb[:5])
        # Drill hints: a Drill on hint questions, the app's own button, against the kit's paint with the answer hidden
        hints = find_hints(8)
        hb = []
        for qid in hints:
            drill(pg, qid, answer=False)
            pg.wait_for_selector(".qpanel .ifc-hint-btn", timeout=25000); pg.wait_for_timeout(500)
            c = pg.evaluate(TAPC, ".qpanel .ifc-hint-btn"); pg.touchscreen.tap(c[0], c[1])
            r = pg.evaluate(r"""async ([id, s])=>{ const wt = ms => new Promise(r => setTimeout(r, ms)); let pic = null;
              for(let k = 0; k < 300 && !pic; k++){ await wt(50); pic = document.querySelector('.qpanel .ifc-hintpic canvas'); }
              /* (384 review) the Hint's picture drops in (ifcSlideHeight): measured once the slide has let go of its height */
              for(let k = 0; k < 80; k++){ const h = document.querySelector('.qpanel .ifc-hintpic'); if(!h || !h.style.height) break; await wt(50); }
              await wt(80); if(!pic) return { id, m: null };
              const item = QUESTIONS.find(q => q.ifc && q.ifc.id === id); const V = await ifcViewer(); const c = item.ifc.citation;
              let doc, clip; if(c.source === 'amendment'){ doc = await ifcCountyDoc(); clip = await V.countyClip(doc, c, ifcCountyOpts); }
              else { const b = await ifcEnsureBook(); doc = b.doc; clip = await V.computeClip(b.doc, b.index, V.locate(b.index, c), c, b.opts); }
              const h = await V.hideAnswer(doc, clip, V.answerNumbers(item.ifc));
              const m = __measure(document.querySelector('.qpanel .ifc-hintpic'), s * 1.5 / 1.7);
              const kit = await __kitInk(item, s * 1.5 / 1.7, { blur: true, scale: 1.5, hide: h });
              return { id, m, kit, unanswered: typeof cleared !== 'undefined' ? !cleared : null }; }""", [qid, S])
            m, kit = r["m"], r.get("kit")
            if not m: hb.append((qid, "no picture")); continue
            n = sum(x.get("n", 0) for x in m); sm = sum(x.get("sum", 0) for x in m)
            pr = pic_problems(m, kit)
            if not kit or kit["n"] != n or kit["sum"] != sm: pr.append("pixels differ from the kit's paint with the answer hidden (%s vs %s)" % (kit and (kit["n"], kit["sum"]), (n, sm)))
            if r.get("unanswered") is False: pr.append("the question was answered by the hint")
            if pr: hb.append((qid, pr))
        chk("(2) %d Drill Hints: the kit's pixels with the answer hidden exactly, framed and centred, the question still unanswered" % len(hints), len(hints) >= 6 and not hb, hb[:4])
    if want("3"):
        # (3a) a flash card's answer side
        fc = []
        for qid in ("ch9-316", "nav-NAVC-031"):
            pg.evaluate("""(id)=>{ const q = QUESTIONS.find(q=>q.ifc && q.ifc.id===id); showFlashcards([q.topic.trim()], 'all'); }""", qid); pg.wait_for_timeout(1200)
            pg.evaluate("""(id)=>{ const want = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); const at = fc.deck.indexOf(want); if(at >= 0 && fc.pos !== at){ fc.pos = at; showFlashcards(fc.units, fc.source, fc.versions); } }""", qid); pg.wait_for_timeout(1000)
            c = pg.evaluate(TAPC, ".fc-card .fc-front .fc-fliphint") or pg.evaluate(TAPC, ".fc-card"); pg.touchscreen.tap(c[0], c[1]); pg.wait_for_timeout(900)
            c = pg.evaluate(TAPC, ".fc-card .fc-back summary.ifc-code-sum")
            if c: pg.touchscreen.tap(c[0], c[1])
            for _ in range(120):
                if pg.evaluate("()=>!!document.querySelector('.fc-card .fc-back .ifc-code-body .ifc-links')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(600)
            m = pg.evaluate("(s)=>{ const b = document.querySelector('.fc-card .fc-back .ifc-ref'); return b ? __measure(b, s) : null; }", S)
            fc.append((qid, m and pic_problems(m, None), m))
        chk("(3) a Fire Code flash card's answer side shows the picture framed and centred (%s)" % [(a, b) for a, b, _ in fc], all(m and not p for _, p, m in fc), fc)
        # (3b) the page viewer: Enlarge on a section and on a chapter title
        vz = []
        for qid in ("ch9-316", "nav-NAVC-035"):
            drill(pg, qid)
            pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code'); if(d && !d.open) d.open = true; }")
            for _ in range(160):
                if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-code-body .ifc-links')"): break
                pg.wait_for_timeout(250)
            pg.evaluate("()=>{ const b=[...document.querySelectorAll('.qpanel .ifc-links .ifc-link')].find(x=>/Enlarge/.test(x.textContent)); b && b.click(); }")
            for _ in range(80):
                if pg.evaluate("()=>!!document.querySelector('.ifc-vz-pages canvas')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(900)
            m = pg.evaluate("""(s)=>{ const p = document.querySelector('.ifc-vz-pages'); if(!p) return null; const sc = document.querySelector('.ifc-vz-scroll').getBoundingClientRect();
              const ms = __measure(p, s); return { ms, fit: Math.round(document.querySelector('.ifc-vz-pages canvas').getBoundingClientRect().width / sc.width * 100) / 100 }; }""", 2.6 * 2)
            pg.evaluate("()=>document.querySelector('.ifc-vz .ifc-vz-btn.is-done')?.click()"); pg.wait_for_timeout(700)
            probs = []
            if not m or not m["ms"]: probs.append("nothing drawn")
            else:
                for x in m["ms"]:
                    if x.get("page") or x.get("blank"): continue
                    if not x["framed"]: probs.append("not framed")
                    if min(x["aL"], x["aR"], x["T"], x["B"]) < 1: probs.append("ink on an edge %s" % [x["aL"], x["aR"], x["T"], x["B"]])
                    if abs(x["L"] - x["R"]) > 1.5: probs.append("off centre %s / %s" % (x["L"], x["R"]))
                if m["fit"] < 0.9: probs.append("not fitted to the width (%s)" % m["fit"])
            vz.append((qid, probs, m and m["fit"]))
        chk("(3) Enlarge shows the same picture framed, centred and fitted to the viewer (%s)" % vz, all(not p for _, p, _ in vz), vz)
    if want("4"):
        # (4) the tag pills, their glyph pixels: as shown (dpr 3) and moved by a sixth of a pixel at a time
        def pill(sel):
            tag = pg.evaluate("(sel)=>{ const t=document.querySelector(sel); if(!t) return null; t.scrollIntoView({block:'center',behavior:'instant'}); t.id='__pill'; return t.textContent.trim(); }", sel)
            if not tag: return None
            pg.wait_for_timeout(250)
            res = []
            for fx, fy in ((0, 0), (1 / 6, 2 / 6), (2 / 6, 4 / 6), (3 / 6, 1 / 6), (4 / 6, 3 / 6), (5 / 6, 5 / 6)):
                pg.evaluate("([x,y])=>{ document.getElementById('__pill').style.transform = (x||y) ? 'translate(' + x + 'px,' + y + 'px)' : ''; }", [fx, fy])
                bb = pg.evaluate("()=>{ const r=document.getElementById('__pill').getBoundingClientRect(); return [r.left,r.top,r.width,r.height]; }")
                pad = 4; clip = {"x": bb[0] - pad, "y": bb[1] - pad, "width": bb[2] + 2 * pad, "height": bb[3] + 2 * pad}
                a = np.asarray(Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")).astype(float)
                pg.evaluate("()=>document.getElementById('__pill').style.setProperty('color','transparent','important')")
                b = np.asarray(Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")).astype(float)
                pg.evaluate("()=>document.getElementById('__pill').style.removeProperty('color')")
                d = np.abs(a - b).sum(axis=2); mx = d.max()
                if mx <= 30: res.append(None); continue
                def edges(prof):
                    idx = np.nonzero(prof > 30)[0]; i0, i1 = idx[0], idx[-1]
                    return (i0 + 1 - min(1, prof[i0] / mx)), (i1 + min(1, prof[i1] / mx))
                x0, x1 = edges(d.max(axis=0)); y0, y1 = edges(d.max(axis=1))
                sc = 3.0
                res.append(((x0 + x1) / 2 / sc - pad - bb[2] / 2, (y0 + y1) / 2 / sc - pad - bb[3] / 2))
            pg.evaluate("()=>{ const t=document.getElementById('__pill'); t.style.transform=''; t.removeAttribute('id'); }")
            if any(r is None for r in res): return {"word": tag, "err": "no ink"}
            mdx = sum(r[0] for r in res) / len(res); mdy = sum(r[1] for r in res) / len(res)
            return {"word": tag, "dx": round(mdx, 2), "dy": round(mdy, 2), "worst": round(max(max(abs(r[0]), abs(r[1])) for r in res), 2)}
        rows = []; hint1 = find_hints(1)[0]
        for label, w, h, fs in (("440", 440, 956, 1), ("375", 375, 667, 1), ("440 @125%", 440, 956, 1.25)):
            pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(900)
            pg.evaluate("(z)=>{ const r=document.documentElement; r.style.fontSize = z === 1 ? '' : (16 * z) + 'px'; }", fs); pg.wait_for_timeout(400)
            for qid, sel in (("ch3-053", ".qpanel .ifc-code-sum .ifc-tag"), ("nav-NAVC-031", ".qpanel .ifc-code-sum .ifc-tag")):
                drill(pg, qid); rows.append((label, pill(sel)))
            drill(pg, hint1, answer=False)
            try: pg.wait_for_selector(".qpanel .ifc-hint-btn .ifc-tag", timeout=20000)
            except Exception: pass
            rows.append((label, pill(".qpanel .ifc-hint-btn .ifc-tag")))
            pg.evaluate("()=>{ document.documentElement.style.fontSize=''; }")
        pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(600)
        bad = [(l, r) for l, r in rows if not r or r.get("err") or abs(r["dx"]) > 0.5 or abs(r["dy"]) > 0.5 or r["worst"] > 0.75]
        words = sorted({r["word"].upper() for _, r in rows if r})
        chk("(4) the tag pills %s: the ink centred within 0.5px (mean of six placements), each placement within 0.75px - %s"
            % (words, "; ".join("%s %s %s/%s (%s)" % (l, r and r["word"], r and r.get("dx"), r and r.get("dy"), r and r.get("worst")) for l, r in rows)),
            len(words) >= 3 and not bad, bad)
    if want("5"):
        # (5) Enlarge and the whole page
        LINKS = r"""()=>{ const box = document.querySelector('.qpanel .ifc-code[open] .ifc-links'); if(!box) return null;
          const bs = [...box.querySelectorAll('.ifc-link')].filter(x => x.offsetWidth); const lb = box.getBoundingClientRect();
          const st = b => { const c = getComputedStyle(b); return [c.fontSize, c.fontWeight, c.color, c.paddingLeft, c.paddingRight, c.borderTopLeftRadius, c.backgroundColor, c.borderTopColor, c.borderTopWidth, c.lineHeight].join('|'); };
          return { row: [lb.left, lb.right], btns: bs.map(b => { const r = b.getBoundingClientRect(); const kids = [...b.children].map(k => k.getBoundingClientRect());
            const cl = Math.min(...kids.map(k => k.left)), cr = Math.max(...kids.map(k => k.right)), ct = Math.min(...kids.map(k => k.top)), cb = Math.max(...kids.map(k => k.bottom));
            const lab = b.querySelector('span'); return { t: b.textContent.trim(), l: r.left, r: r.right, top: r.top, w: r.width, h: r.height, st: st(b),
              cdx: (cl + cr) / 2 - (r.left + r.right) / 2, cdy: (ct + cb) / 2 - (r.top + r.bottom) / 2, cut: lab ? lab.scrollWidth > lab.clientWidth + 1 : false }; }) }; }"""
        out = []
        for label, w, h in (("440x956", 440, 956), ("375x667", 375, 667), ("iPad 834x1194", 834, 1194), ("laptop 1536x864", 1536, 864)):
            pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(1000)
            drill(pg, "ch3-053")
            pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code'); if(d && !d.open) d.open = true; }")
            for _ in range(160):
                if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-code[open] .ifc-links .ifc-link')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(500)
            L = pg.evaluate(LINKS); probs = []
            if not L or len(L["btns"]) != 2: probs.append("not two buttons: %s" % L)
            else:
                a, b = L["btns"]; rw = L["row"][1] - L["row"][0]
                if a["st"] != b["st"]: probs.append("not the same style: %s / %s" % (a["st"], b["st"]))
                if abs(a["h"] - b["h"]) > 0.5: probs.append("heights %s / %s" % (a["h"], b["h"]))
                if min(a["h"], b["h"], a["w"], b["w"]) < 44: probs.append("under 44px")
                for x in (a, b):
                    if abs(x["cdx"]) > 1 or abs(x["cdy"]) > 1: probs.append("%s: mark and word off centre by %.1f/%.1f" % (x["t"], x["cdx"], x["cdy"]))
                    if x["cut"]: probs.append("%s: its word cut short" % x["t"])
                same_row = abs(a["top"] - b["top"]) < 2
                if same_row:
                    if abs(a["w"] - b["w"]) > 1 or abs(a["l"] - L["row"][0]) > 1 or abs(b["r"] - L["row"][1]) > 1: probs.append("side by side but not two equal halves: %.1f / %.1f in %.1f" % (a["w"], b["w"], rw))
                else:
                    if abs(a["w"] - rw) > 1 or abs(b["w"] - rw) > 1: probs.append("stacked but not both full width: %.1f / %.1f in %.1f" % (a["w"], b["w"], rw))
                out.append((label, "side by side" if same_row else "stacked", round(a["w"]), round(b["w"]), probs))
            if probs and not out or (out and out[-1][0] != label): out.append((label, None, None, None, probs))
        pg.set_viewport_size({"width": 440, "height": 956})
        chk("(5) Enlarge and Show the whole book page: one family, both 44px+, mark and word centred, stacked full width or equal halves (%s)"
            % "; ".join("%s %s %s/%s" % (l, k, a, b) for l, k, a, b, _ in out), out and all(not p for *_, p in out), [(l, p) for l, *_, p in out if p])
    if want("6"):
        # (6) what the framing costs: the app's ifcFrameClips timed around each call while pictures are drawn
        perf = pg.evaluate(r"""async ()=>{ const wt = ms => new Promise(r => setTimeout(r, ms));
          if(typeof ifcFrameClips !== 'function') return { none: true };
          const orig = ifcFrameClips; const times = []; ifcFrameClips = function(){ const t0 = performance.now(); const r = orig.apply(this, arguments); times.push(performance.now() - t0); return r; };
          const ids = ['ch3-053','ch9-316','nav-NAVC-001','nav-NAVC-035','nav-NAVC-031','ch3-062','ch2-057','ch2-610'];
          const host = document.getElementById('__h440') || document.querySelector('.qpanel'); const fills = [];
          for(const id of ids){ ifcNodeCache.clear(); const item = QUESTIONS.find(q => q.ifc && q.ifc.id === id); const n = buildBankNote(item); host.replaceChildren ? host.replaceChildren(n) : host.appendChild(n);
            const t0 = performance.now(); n.querySelector('details').open = true; for(let k = 0; k < 400 && !n.querySelector('.ifc-code-body .ifc-links'); k++) await wt(20); fills.push(performance.now() - t0); }
          ifcFrameClips = orig; return { times, fills }; }""")
        if perf.get("none"): print("  (6) this build has no framing step (nothing added to the draw)", flush=True)
        else:
            ft = sorted(perf["times"]); fl = sorted(perf["fills"])
            print("  (6) framing: median %.1fms, worst %.1fms per picture; the whole draw (opened -> shown) median %dms, worst %dms"
                  % (ft[len(ft) // 2], ft[-1], fl[len(fl) // 2], fl[-1]), flush=True)
            chk("(6) the framing adds little to a picture's draw (median %.1fms, worst %.1fms, against a median draw of %dms)" % (ft[len(ft) // 2], ft[-1], fl[len(fl) // 2]),
                ft[len(ft) // 2] <= max(25, 0.15 * fl[len(fl) // 2]) and ft[-1] <= 120, perf)
    chk("(7) no page errors", not errs, errs[:3])
    ctx.close(); br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
