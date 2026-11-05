"""Build 384, the code pictures: ONE picture per citation, TWO tones, the marker ON its words.
Madison (phone screenshots of Fire Code; "very very VERY VITAL ... the heart of the app"): "When showing the show code, why would there
be two cropped images? That should be one cropped image ... Like tables too. If it's going across the left side of the page and
continuing to the right side of the page, don't do two crops, just make it look like it's one cropped ... make it look like how the
code book has it ... why do some of the cropped photos or full page thing of code have 3 different tones of highlighted stuff? ...
Should really only ever be two tones ... I see some highlights where it goes slightly above the word with the dark stuff but it would
need to be nice all the way through? The edges of the highlight need to be nice as well and cohesive."
Everything is read off the pictures' own pixels, in Fire Code, with the owner's IFC loaded through the app's own path (Load my IFC
PDF) and pdf.js served from a local copy, as his iPhone 17 Pro Max draws it (440x956, deviceScaleFactor 3), for EVERY citation (all
1,812: 1,391 from the book, 421 from the county booklet - or those named with --ids, or a stratified --sample N):
(1a) ONE PICTURE: the answer card's "Show the code" shows exactly one picture.
(1b) TWO TONES IN THE PICTURE: the flat highlight colours in it (pixels whose neighbours all share their colour, the red channel at
     the top - the wash and the gold are multiplied over the paper) are at most two: the pale wash and the darker gold.
(1c) TWO TONES ON THE WHOLE PAGE ("Show the whole page", painted as the viewer paints it, every page of the citation).
(1d) NOTHING DARKER THAN THE GOLD: no flat highlight colour darker than the gold on the wash (where marks overlap, an orange mark,
     a mark over a mark), in the picture or on the page.
(1e) THE GOLD SITS ON ITS WORDS: for every shape of the darker gold, the room between its top edge and the tallest letters under it
     and the room between its bottom edge and the lowest descenders above it differ by at most 1.5px + 0.04 em (in the picture's
     own pixels - 3.4 a point in the card, 4.4 on the page). The tolerance is a device pixel of anti-aliasing at each edge (the
     edge row is part-covered) and the typefaces' own spread: the book's Times and the booklet's Calibri set their tallest letters
     at 0.68-0.69 em and their descenders at 0.18-0.21 em, measured on the rendered pages. A line with no letter above the x-height
     (or none below the baseline) is measured against its x-height's baseline and the font's descender instead - its letters do
     not reach the edge they are measured against. Before this build the gold ran from 0.95 em above the baseline to 0.3 below:
     0.26 em of room above the letters and 0.09 below.
(1f) LINES JOIN CLEANLY: no stripe of wash (thinner than 0.3 em) between two lines of the gold that overlap sideways, and no
     sliver of the gold on its own (under 0.25 em tall, 3 em long or more: a band that ran on past a table's rule). A table row's gold
     runs to its rules, so an edge of the gold that lies along a rule is the rule's and is not measured by (1e).
(1g) NOTHING CUT: in the kit's own cut (before it is framed), no letter sliced by the top or the bottom edge (a table's rule running on
     past the cut is a rule, not a letter).
(1h) ENLARGE ONE PICTURE: every citation whose cut has more than one piece, and every 20th other one, opened with Enlarge.
(2)  no page errors.
The book never goes into the repo (the repo is public): its path is given when the gate is run.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-onepicture.py
          [--against REV|FILE] [--sample N | --ids id,id] [--shots DIR]
      --against takes a commit (its index.html AND its ifc/ifc-viewer.js are served) or an index.html file (with ifc/ifc-viewer.js
      beside it). Against claude/b384 at 5bb4865 (the build before this work): (1a), (1b), (1c), (1d), (1e), (1f), (1g) and (1h)
      FAIL; (2) passes on both.
OUT_JSON=<file> writes every citation's measurements; --shots DIR saves each card (as the phone shows it) and each whole page (and a
close crop of its highlight) - book pages: keep them out of the repo, like the book."""
import os, sys, json, subprocess, mimetypes, time, base64, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "build/pdf.min.mjs") or not os.path.isfile(BOOK):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF"); sys.exit(0)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384onepicture"}
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
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLE = int(arg("--sample", 0)); IDS = arg("--ids").split(",") if arg("--ids") else None
SHOTS = arg("--shots"); OUT_JSON = os.environ.get("OUT_JSON", "")
if SHOTS: os.makedirs(SHOTS, exist_ok=True)
def body_for(ins):
    if AGAINST is None: return G["g"]["patched"](ins)
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return G["g"]["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:1600], flush=True)
def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
def new_page(ctx):
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = body_for((59, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); try{ localStorage.removeItem('class26e.codeopen'); }catch(e){} }")
    return pg, errs
def load_book(pg):
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    for _ in range(3600):
        if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
        pg.wait_for_timeout(250)
    acc = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? o.classList.contains('is-ok') : null; }")
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(1200)
    return acc
def drill(pg, qid):
    pg.evaluate("""(id)=>{ const i = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[i].topic]; beginRun([i]); }""", qid)
    pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(900)
    for _ in range(6):
        c = pg.evaluate("""()=>{ const r=correctSlot(order[pos]); const el=document.querySelector('.qpanel .choice[data-index="'+r+'"]'); if(!el) return null; el.scrollIntoView({block:'center',behavior:'instant'}); const b=el.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }""")
        if c: pg.touchscreen.tap(c[0], c[1])
        pg.wait_for_timeout(1300)
        if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-ref')"): return True
    return False

MEASURE_JS = r"""
window.__S = 1.7 * Math.min(devicePixelRatio || 1, 2);
{ const st = document.createElement('style'); st.textContent = '.ifc-code *, .ifc-code{ animation:none !important; transition:none !important; }'; document.head.appendChild(st); }
/* the flat highlight colours of a picture: a pixel whose 8 neighbours share its colour (within 2 levels), red at the top (both tones
   are multiplied over the paper, which leaves red at 255), not the white paper - grouped within 6 levels */
window.__tones = function(D, W, H, step){
  const cl = []; let n = 0;
  const same = (i, j) => Math.abs(D[i] - D[j]) <= 2 && Math.abs(D[i + 1] - D[j + 1]) <= 2 && Math.abs(D[i + 2] - D[j + 2]) <= 2;
  const R = 4 * W;
  for(let y = 1; y < H - 1; y += step) for(let x = 1; x < W - 1; x += step){
    const i = (y * W + x) * 4, r = D[i], g = D[i + 1], b = D[i + 2];
    if(r < 245 || (g >= 248 && b >= 235)) continue;
    if(!(same(i, i - 4) && same(i, i + 4) && same(i, i - R) && same(i, i + R) && same(i, i - R - 4) && same(i, i + R + 4) && same(i, i - R + 4) && same(i, i + R - 4))) continue;
    n++;
    let c = cl.find(c => Math.abs(c.g - g) <= 6 && Math.abs(c.b - b) <= 6);
    if(!c) cl.push(c = { r, g, b, n: 0 }); c.n++;
  }
  const min = Math.max(25, 0.002 * n);
  const tones = cl.filter(c => c.n >= min).sort((a, b) => b.n - a.n).map(c => [c.r, c.g, c.b, c.n * step * step]);
  const darker = cl.filter(c => c.n >= 12 && (c.g < 207 || c.b < 17)).map(c => [c.r, c.g, c.b, c.n * step * step]);
  return { tones, darker };
};
/* the darker gold's shapes and how they sit on their words. em: estimated from the x-height of the line under the edge (x-height
   0.46 em in both typefaces) */
window.__gold = function(D, W, H, s){
  const isG = (i) => D[i] >= 245 && Math.abs(D[i + 1] - 215) <= 9 && D[i + 2] <= 48;
  const ink = (i) => D[i] + D[i + 1] + D[i + 2] < 300;
  const lab = new Int32Array(W * H); const comps = [];
  for(let p = 0; p < W * H; p++){
    if(lab[p] || !isG(p * 4)) continue;
    const id = comps.length + 1, st = [p]; lab[p] = id; let n = 0, x0 = W, x1 = -1, y0 = H, y1 = -1;
    while(st.length){ const q = st.pop(), x = q % W, y = (q - x) / W; n++; if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y;
      for(const r of [q - 1, q + 1, q - W, q + W]){ if(r < 0 || r >= W * H || lab[r]) continue; if((r === q - 1 && x === 0) || (r === q + 1 && x === W - 1)) continue; if(isG(r * 4)){ lab[r] = id; st.push(r); } } }
    comps.push({ id, n, x0, x1, y0, y1 });
  }
  const big = comps.filter(c => c.n >= 150 && c.y1 - c.y0 >= 4 * s);
  const out = [];
  for(const c of big){
    const rec = { x0: c.x0, x1: c.x1, y0: c.y0, y1: c.y1 };
    const w = c.x1 - c.x0 + 1, h = c.y1 - c.y0 + 1;
    /* a table's rules are not letters: a column inked down most of the shape (an upright rule), a row inked across most of it */
    const colN = new Uint16Array(w), rowN = new Uint32Array(h);
    for(let y = c.y0; y <= c.y1; y++) for(let x = c.x0; x <= c.x1; x++) if(ink((y * W + x) * 4)) colN[x - c.x0]++;
    const rcol = (x) => colN[x - c.x0] >= 0.8 * h;
    for(let y = c.y0; y <= c.y1; y++){ let m = 0; for(let x = c.x0; x <= c.x1; x++) if(!rcol(x) && ink((y * W + x) * 4)) m++; rowN[y - c.y0] = m; }
    const prow = (y) => rowN[y - c.y0] >= 0.6 * w;
    /* the lines of print inside the shape: runs of rows with letters, a blank row or more between two lines */
    const lines = []; let cur = null;
    for(let y = c.y0; y <= c.y1; y++){
      const m = prow(y) ? 0 : rowN[y - c.y0];
      if(m){ if(cur && y - cur.b <= 2){ cur.b = y; cur.rows.push([y, m]); } else { cur = { a: y, b: y, rows: [[y, m]] }; lines.push(cur); } }
    }
    if(!lines.length){ rec.skip = 'no letters inside'; out.push(rec); continue; }
    /* each line: its x-height block (the rows most letters cover: 0.45-0.47 em in both typefaces), baseline at its foot */
    for(const L of lines){
      const mx = Math.max(...L.rows.map(r => r[1]));
      const dense = L.rows.filter(r => r[1] >= 0.45 * mx).map(r => r[0]);
      L.base = Math.max(...dense); L.xt = Math.min(...dense);
      L.em = Math.max(4, (L.base - L.xt + 1) / 0.46);
      L.tall = (L.base + 1 - L.a) / L.em >= 0.6;            /* a capital, a figure or an ascender in the line */
      L.desc = (L.b - L.base) / L.em >= 0.1;                /* a descender in the line */
    }
    /* a table row's gold fills its row up to the rules: an edge that runs along a rule is the rule's, not measured */
    const ruledAt = (y) => { if(y < 0 || y >= H) return false; let run = 0, best = 0; for(let x = c.x0; x <= c.x1; x++){ if(ink((y * W + x) * 4)){ run++; if(run > best) best = run; } else run = 0; } return best >= 0.5 * w; };
    rec.ruled = [ruledAt(c.y0 - 1) || ruledAt(c.y0 - 2), ruledAt(c.y1 + 1) || ruledAt(c.y1 + 2)];
    if(rec.ruled[0] || rec.ruled[1]){ rec.skip = 'a table row: its gold runs to the rule'; out.push(rec); continue; }
    const T = lines[0], B = lines[lines.length - 1];
    const above = T.a - c.y0;
    const inkBot = B.desc ? B.b + 1 : B.base + 1 + 0.205 * B.em;
    const below = c.y1 + 1 - inkBot;
    rec.above = +above.toFixed(2); rec.below = +below.toFixed(2); rec.em = +T.em.toFixed(1); rec.viaFont = !B.desc; rec.lines = lines.length;
    if(!T.tall){ rec.skip = 'no tall letter in the top line'; out.push(rec); continue; }
    rec.diff = +(below - above).toFixed(2);
    rec.tol = +(1.5 + 0.04 * T.em).toFixed(2);
    rec.ok = Math.abs(rec.diff) <= rec.tol;
    out.push(rec);
  }
  /* stripes: two shapes one above the other, overlapping sideways, with a thin band of something else between */
  const stripes = [];
  for(const a of big) for(const b of big){ if(a === b) continue;
    const ov = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0), gap = b.y0 - a.y1 - 1;
    if(ov > 4 * s && gap >= 1 && gap <= 0.3 * 10 * s) stripes.push([a.y1, b.y0, gap]); }
  /* slivers: a long thin strip of the gold on its own (under 0.25 em tall, over 3 em long) - a band that ran past a table's rule */
  const slivers = comps.filter(c => c.n >= 20 && c.y1 - c.y0 + 1 <= 0.25 * 10 * s && c.x1 - c.x0 + 1 >= 3 * 10 * s).map(c => [c.x0, c.y0, c.x1, c.y1]);
  return { shapes: out, stripes, slivers, n: big.length };
};
/* the kit's own cut (before it is framed): ink on its edges. Top / bottom: a letter sliced ('text') or a rule running on ('rule');
   left / right: any ink on the side edge ('ink'), a table's rule running on ('rule') */
window.__edges = function(D, W, H){
  const ink = (x, y) => { const i = (y * W + x) * 4; return D[i] + D[i + 1] + D[i + 2] < 300; };
  const res = {};
  for(const [side, ys] of [['top', [0, 1]], ['bottom', [H - 1, H - 2]]]){
    let kind = null, x = 0;
    while(x < W){
      if(!ys.some(y => y >= 0 && y < H && ink(x, y))){ x++; continue; }
      let e = x; while(e < W && ys.some(y => y >= 0 && y < H && ink(e, y))) e++;
      const w = e - x;
      /* a rule or a change bar: every column of it inked straight on from the edge for 26px or more (a letter, 0.9 em tall at
         most, is not; a sliced letter's stroke stops sooner); a rule along the edge: a third of the width or more */
      let solid = Infinity;
      for(let xx = x; xx < e; xx++){ let run = 0; for(let k = 0; k < Math.min(H, 26); k++){ const y = side === 'top' ? k : H - 1 - k; if(ink(xx, y)) run++; else break; } solid = Math.min(solid, run); }
      /* or a thin level line along the edge (a table's rule cut through): its columns empty 3 rows in */
      let deep = 0; for(let xx = x; xx < e; xx++){ const y = side === 'top' ? 4 : H - 5; if(y >= 0 && y < H && ink(xx, y)) deep++; }
      const isRule = solid >= Math.min(26, H - 2) || w >= 0.3 * W || (w >= 12 && deep <= 0.3 * w);
      kind = isRule ? (kind || 'rule') : 'text';
      x = e;
    }
    res[side] = kind;
  }
  for(const [side, xs] of [['left', [0, 1]], ['right', [W - 1, W - 2]]]){
    let kind = null, y = 0;
    while(y < H){
      if(!xs.some(x => x >= 0 && x < W && ink(x, y))){ y++; continue; }
      let e = y; while(e < H && xs.some(x => x >= 0 && x < W && ink(x, e))) e++;
      let solid = Infinity;
      for(let yy = y; yy < e; yy++){ let run = 0; for(let k = 0; k < Math.min(W, 26); k++){ const x = side === 'left' ? k : W - 1 - k; if(ink(x, yy)) run++; else break; } solid = Math.min(solid, run); }
      kind = solid >= Math.min(26, W - 2) ? (kind || 'rule') : 'ink';
      y = e;
    }
    res[side] = kind;
  }
  return res;
};
window.__readCanvas = function(cv){ const W = cv.width, H = cv.height; if(!W || !H) return null; try{ return { W, H, D: cv.getContext('2d').getImageData(0, 0, W, H).data }; }catch(e){ return null; } };
window.__jpeg = function(cv, maxW, crop){
  const sx = crop ? crop[0] : 0, sy = crop ? crop[1] : 0, sw = crop ? crop[2] : cv.width, sh = crop ? crop[3] : cv.height;
  const k = Math.min(1, maxW / sw), o = document.createElement('canvas'); o.width = Math.max(1, Math.round(sw * k)); o.height = Math.max(1, Math.round(sh * k));
  const g = o.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(cv, sx, sy, sw, sh, 0, 0, o.width, o.height);
  const u = o.toDataURL('image/jpeg', 0.86); o.width = 0; return u;
};
window.__one = async function(id, opts){
  const wt = ms => new Promise(r => setTimeout(r, ms));
  const item = QUESTIONS.find(q => q.ifc && q.ifc.id === id), c = item.ifc.citation;
  const rec = { id, src: c.source === 'amendment' ? 'county' : 'book', label: c.label, section: c.section };
  let host = document.getElementById('__host');
  if(!host){ const real = document.querySelector('.qpanel .ifc-ref'); host = document.createElement('div'); host.id = '__host'; real.after(host); real.style.display = 'none'; }
  ifcNodeCache.clear();
  const node = buildBankNote(item); host.replaceChildren(node);
  const d = node.querySelector('details.ifc-code'); d.open = true;
  for(let k = 0; k < 800; k++){ await wt(25); if(node.querySelector('.ifc-code-body > .ifc-links, .ifc-code-body > .ifc-note, .ifc-code-body > .ifc-locked')) break; }
  await wt(80);
  d.querySelectorAll('[style*="height"]').forEach(e => { if(e.style.height && !e.matches('canvas')) e.style.height = ''; });
  const cvs = [...node.querySelectorAll('.ifc-code-body .ifc-clips canvas')];
  rec.pictures = cvs.length; rec.pages = cvs.filter(cv => cv.classList.contains('ifc-page')).length;
  rec.text = !!node.querySelector('.ifc-code-body > .ifc-county-text');
  rec.card = [];
  for(const cv of cvs){
    const p = __readCanvas(cv); if(!p) continue;
    const r = cv.getBoundingClientRect();
    const t = __tones(p.D, p.W, p.H, 1), g = __gold(p.D, p.W, p.H, __S);
    rec.card.push({ W: p.W, H: p.H, cssW: +r.width.toFixed(1), cssH: +r.height.toFixed(1), pxPerPt: +(r.width / (p.W / __S)).toFixed(3), tones: t.tones, darker: t.darker,
      gold: g.shapes, stripes: g.stripes, slivers: g.slivers });
  }
  /* the kit's own cut and the whole page, painted as the app paints them */
  const V = await ifcViewer(); let doc, clip, popts;
  try{
    if(c.source === 'amendment'){ doc = await ifcCountyDoc(); clip = await V.countyClip(doc, c, ifcCountyOpts); popts = ifcCountyOpts; }
    else { const b = await ifcEnsureBook(); doc = b.doc; popts = b.opts; const loc = V.locate(b.index, c); clip = loc.ok && loc.kind !== 'pages' ? await V.computeClip(b.doc, b.index, loc, c, b.opts) : null; rec.kind = loc.kind; }
  }catch(e){ rec.clipErr = String(e && e.message || e); }
  if(clip && clip.ok){
    rec.segs = clip.segments.length; rec.sheet = !!clip.sheet;
    const tmp = document.createElement('div');
    await V.paint(doc, clip, tmp, { scale: 1.7 });
    rec.cut = [...tmp.querySelectorAll('canvas')].map(cv => { const p = __readCanvas(cv); const e = p ? __edges(p.D, p.W, p.H) : null; const o = { W: cv.width, H: cv.height, ...e }; cv.width = 0; return o; });
    const pg = document.createElement('div');
    await V.paintPages(doc, clip.pages, pg, { scale: 2.2, ...popts, clip });
    rec.page = []; const shots = [];
    for(const cv of pg.querySelectorAll('canvas')){
      const p = __readCanvas(cv); if(!p) continue;
      const t = __tones(p.D, p.W, p.H, 2), g = __gold(p.D, p.W, p.H, 2.2 * Math.min(devicePixelRatio || 1, 2));
      rec.page.push({ W: p.W, H: p.H, tones: t.tones, darker: t.darker, gold: g.shapes, stripes: g.stripes, slivers: g.slivers });
      if(opts && opts.shots){
        /* the page as the viewer shows it, and a close crop of what is highlighted on it */
        let x0 = p.W, x1 = -1, y0 = p.H, y1 = -1;
        for(let y = 0; y < p.H; y += 2) for(let x = 0; x < p.W; x += 2){ const i = (y * p.W + x) * 4; if(p.D[i] >= 245 && (p.D[i + 1] < 248 || p.D[i + 2] < 230) && p.D[i + 2] < 200){ if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y; } }
        const full = __jpeg(cv, 760);
        let crop = null;
        if(x1 > x0){ const m = 70; const cx0 = Math.max(0, x0 - m), cy0 = Math.max(0, y0 - m), cw = Math.min(p.W, x1 + m) - cx0, ch = Math.min(p.H, y1 + m) - cy0; crop = __jpeg(cv, 1100, [cx0, cy0, cw, ch]); }
        shots.push({ full, crop });
      }
      cv.width = 0;
    }
    if(shots.length) rec.shots = shots;
  }
  d.scrollIntoView({ block: 'start', behavior: 'instant' }); window.scrollBy(0, -70);
  return rec;
};
window.__enlarge = async function(){
  const wt = ms => new Promise(r => setTimeout(r, ms));
  const b = [...document.querySelectorAll('#__host .ifc-links .ifc-link')].find(x => /Enlarge/.test(x.textContent)); if(!b) return null;
  b.click(); let n = 0;
  for(let k = 0; k < 200; k++){ await wt(50); if(document.querySelector('.ifc-vz-pages canvas')) break; }
  await wt(200);
  n = document.querySelectorAll('.ifc-vz-pages canvas').length;
  document.querySelector('.ifc-vz .ifc-vz-btn.is-done')?.click(); await wt(300);
  return n;
};
true;
"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, device_scale_factor=3)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    if VIEWER is not None:
        ctx.route("**/ifc/ifc-viewer.js*", lambda route, request: route.fulfill(status=200, body=VIEWER, content_type="text/javascript"))
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]))
    pg, errs = new_page(ctx)
    t = time.time(); acc = load_book(pg)
    chk("(0) the owner's IFC is accepted through Load my IFC PDF (%ds)" % (time.time() - t), acc is True, acc)
    ids_all = pg.evaluate("()=>QUESTIONS.filter(q=>q.ifc).map(q=>q.ifc.id)")
    ids = [q for q in ids_all if q in IDS] if IDS else ids_all
    if SAMPLE and not IDS:
        step = max(1, len(ids_all) // SAMPLE); ids = ids_all[::step][:SAMPLE]
    def fresh():
        global pg, errs
        e0 = errs
        try: pg.close()
        except Exception: pass
        pg, errs = new_page(ctx); errs[:0] = e0
        drill(pg, "ch3-053"); pg.evaluate(MEASURE_JS)
    drill(pg, "ch3-053"); pg.evaluate(MEASURE_JS)
    print("  %d citations%s" % (len(ids), " (those named)" if IDS else " (a sample)" if SAMPLE else " (every one)"), flush=True)
    res = []; t = time.time()
    for k, qid in enumerate(ids):
        if k and k % 250 == 0: fresh()
        try:
            r = pg.evaluate("([id, sh])=>__one(id, { shots: sh })", [qid, bool(SHOTS)])
        except Exception as e:
            r = {"id": qid, "err": str(e)[:300]}; fresh()
        if SHOTS and not r.get("err"):
            try:
                pg.query_selector("#__host details.ifc-code").screenshot(path=os.path.join(SHOTS, qid + "-card.jpg"), type="jpeg", quality=85)
            except Exception as e: r["shotErr"] = str(e)[:120]
            for j, sh in enumerate(r.pop("shots", []) or []):
                for nm in ("full", "crop"):
                    if sh.get(nm): open(os.path.join(SHOTS, "%s-page%d-%s.jpg" % (qid, j + 1, nm)), "wb").write(base64.b64decode(sh[nm].split(",", 1)[1]))
        if not r.get("err") and (r.get("segs", 1) > 1 or k % 20 == 0):
            try: r["enlarge"] = pg.evaluate("()=>__enlarge()")
            except Exception as e: r["enlarge"] = None
        res.append(r)
        if k % 100 == 0: print("    %d / %d (%ds)" % (k + 1, len(ids), time.time() - t), flush=True)
    if OUT_JSON:
        with open(OUT_JSON, "w") as f: json.dump(res, f)
    # ---- the verdicts
    bad = {k: [] for k in ("draw", "1a", "1b", "1c", "1d", "1e", "1f", "1g", "1h")}
    n_shapes = [0, 0]; n_eval = [0, 0]; worst = [0.0, 0.0]; offs = [[], []]
    for r in res:
        tag = "%s (%s)" % (r["id"], r.get("label"))
        if r.get("err") or r.get("text") or not r.get("card"):
            bad["draw"].append((tag, r.get("err") or ("the county's words, not a picture" if r.get("text") else "no picture"))); continue
        if r["pictures"] != 1: bad["1a"].append((tag, "%d pictures" % r["pictures"]))
        for x in r["card"]:
            if len(x["tones"]) > 2: bad["1b"].append((tag, x["tones"]))
            if x["darker"]: bad["1d"].append((tag, "picture", x["darker"]))
        for x in r.get("page", []):
            if len(x["tones"]) > 2: bad["1c"].append((tag, x["tones"]))
            if x["darker"]: bad["1d"].append((tag, "page", x["darker"]))
        for w, part in ((0, r["card"]), (1, r.get("page", []))):
            for x in part:
                for sh in x["gold"]:
                    n_shapes[w] += 1
                    if "diff" not in sh: continue
                    n_eval[w] += 1; offs[w].append(sh["diff"] / sh["em"])
                    worst[w] = max(worst[w], abs(sh["diff"]) / sh["em"])
                    if not sh["ok"]: bad["1e"].append((tag, "picture" if w == 0 else "page", "above %s below %s em %s" % (sh["above"], sh["below"], sh["em"])))
                if x["stripes"]: bad["1f"].append((tag, "picture" if w == 0 else "page", x["stripes"][:3]))
                if x.get("slivers"): bad["1f"].append((tag, "picture" if w == 0 else "page", "a sliver of the gold on its own", x["slivers"][:3]))
        for cu in r.get("cut", []):
            if cu.get("top") == "text" or cu.get("bottom") == "text": bad["1g"].append((tag, {k: cu.get(k) for k in ("top", "bottom")}))
        if r.get("enlarge") not in (None, 1): bad["1h"].append((tag, "%s pictures" % r.get("enlarge")))
    nb = sum(1 for r in res if r.get("src") == "book"); nc = len(res) - nb
    med = lambda v: statistics.median(v) if v else 0
    print("  measured %d citations (%d book, %d county); gold shapes %d in the pictures (%d measured), %d on the pages (%d measured)"
          % (len(res), nb, nc, n_shapes[0], n_eval[0], n_shapes[1], n_eval[1]), flush=True)
    print("  the gold's (room below - room above), in ems: pictures median %.3f, worst %.3f; pages median %.3f, worst %.3f"
          % (med(offs[0]), worst[0], med(offs[1]), worst[1]), flush=True)
    chk("(1) every citation drew its picture (%d of %d)" % (len(res) - len(bad["draw"]), len(res)), not bad["draw"], bad["draw"][:5])
    chk("(1a) one picture per citation in the answer card (%d not)" % len(bad["1a"]), not bad["1a"], bad["1a"][:8])
    chk("(1b) at most two highlight tones in every picture (%d not)" % len(bad["1b"]), not bad["1b"], bad["1b"][:6])
    chk("(1c) at most two highlight tones on every whole page (%d not)" % len(bad["1c"]), not bad["1c"], bad["1c"][:6])
    chk("(1d) nothing darker than the gold, in the pictures and on the pages (%d not)" % len(bad["1d"]), not bad["1d"], bad["1d"][:6])
    chk("(1e) the gold centred on its words' ink, within 1.5px + 0.04 em (%d shapes not)" % len(bad["1e"]), not bad["1e"], bad["1e"][:8])
    chk("(1f) lines of the gold join with no stripe between them, and no sliver of it runs on past a table's rule (%d not)" % len(bad["1f"]), not bad["1f"], bad["1f"][:6])
    chk("(1g) no letter cut by a picture's top or bottom edge (%d not)" % len(bad["1g"]), not bad["1g"], bad["1g"][:8])
    ne = sum(1 for r in res if r.get("enlarge") is not None)
    chk("(1h) Enlarge shows one picture (%d opened, %d not)" % (ne, len(bad["1h"])), ne and not bad["1h"], bad["1h"][:6])
    chk("(2) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
