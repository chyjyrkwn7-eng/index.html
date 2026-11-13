"""Build 384.112 (boardshake): the Leaderboard's characters hold still at ANY page zoom.

Madison, a screen recording from his installed iPhone 17 Pro Max: "Other leaderboard fix, do you see how the characters are slightly
shaking randomly? I've mentioned this problem before. Fix this." (The third report: builds 313/314 and 384.20 each fixed it at 100%.)

Read off that recording frame by frame (docs/notes-archive.md, "384.112 (boardshake)"): the rows, the names and the circles never moved
(0.00px); inside every circle the drawing jumped a whole device pixel sideways (up to 0.9px down) twice a sheet row - once at the row's
wrap, once part way along it in two steps of ~0.6 and ~0.4 - every 0.500s exactly (12 steps of the 24-a-second sheet), each character on
its own phase. His phone runs Safari's page zoom at 85% (518 CSS px across 440pt, devicePixelRatio still 3) and the board's rows are
CSS-zoomed by --zc (1.177) to undo it, so a CSS px inside a row is 1.177 x 0.85 x 3 = 3.0014 device px: a step of the sheet (36 CSS px)
is 108.05 device px, not 108, and every column of the sheet lands on another fraction of a pixel, which the phone's painting rounds.
Every gate ran at 100%, where a step is 108.000.

Here the page is laid out the way his phone lays it out - the layout viewport is the screen / zoom (518 x 1125 at 85%), the screen is
440 x 956, Chromium paints at 3 x zoom device px per CSS px (2.55 at 85%), and devicePixelRatio reads 3 as Safari's does - at page zoom
1.0, 0.85 and 1.15. The Leaderboard is up with a board of classmates, every character's sheet is a STILL picture (each of its 144 cells
the same drawing, so anything that moves between steps is the flip-book moving, not the character), and over 90 frames snapshots arrive
(rows rebuilt with new numbers, same order) and the page scrolls. Asserted, for every character on the screen:
 (1) GEOMETRY: the frame it shows is put on the same sub-pixel phase at every step (one phase, in device px at the real scale), and the
     picture stays within 0.1 device px of its drawing (centre on centre) through every step, snapshot and scroll;
 (2) PIXELS: the board's avatar column, captured at the device's scale on many different steps, is the same picture every time
     (no character drawn even 0.1 device px off where it was, by sub-pixel registration);
 (3) the rows themselves: a snapshot puts every row back on exactly the device pixel it was on (within 0.01 device px), and a scroll
     moves them all by the scroll and nothing else;
 (4) no page errors;
 (5) the same on every other board and on Customize: each loop on the screen keeps one sub-pixel phase in its box through 24 frames
     and steps (every place a character loops - boards, the Virtual Room's lobby and results, friends, chat faces, pickers - is put
     on by the one path, setCharState -> charFlipAttach).
Must FAIL on 384.95 (origin/main 562b1ed) at 0.85 and pass on this build.

Run:  TMPDIR=/dev/shm python3 tools/check-b384-boardshake.py [--zooms 1,0.85,1.15] [--frames 90] [--against OLD/index.html]
"""
import os, sys, time, importlib.util, io
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image

def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
ZOOMS = [float(z) for z in arg("--zooms", "1,0.85,1.15").split(",")]
FRAMES = int(arg("--frames", "90"))
SHOTS = int(arg("--shots", "36"))
DUMP = arg("--dump", "")
SW, SH, DPR = 440, 956, 3          # iPhone 17 Pro Max, points and scale

ok = True
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:600]), flush=True)

# devicePixelRatio as Safari reports it under page zoom (his bug reports: "518x1125 ... dpr 3"): the device's, not the zoom's
DPR_AS_SAFARI = "Object.defineProperty(window, 'devicePixelRatio', { get: () => %d, configurable: true });" % DPR

# Every sheet a STILL: the character's drawing in each of its 144 cells, with a fine crisp grid over it so a sub-pixel move cannot hide
# in a soft edge. A loop that steps through it should show the same picture at every step.
STILL_SHEETS = r"""(() => {
  window.__sheetsMade = 0;
  window.recordCharSheet = async function(drawing, px){
    const cols = CHAR_ANIM_COLS, rows = Math.ceil(CHAR_ANIM_FRAMES / cols);
    const svg = drawing.svg.cloneNode(true);
    svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); svg.setAttribute('width', px); svg.setAttribute('height', px);
    const img = new Image();
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(svg));
    try{ await img.decode(); }catch(e){}
    const one = document.createElement('canvas'); one.width = one.height = px;
    const g1 = one.getContext('2d');
    g1.fillStyle = '#20242c'; g1.fillRect(0, 0, px, px);
    try{ g1.drawImage(img, 0, 0, px, px); }catch(e){}
    g1.fillStyle = 'rgba(255,255,255,.85)';
    for(let x = 3; x < px; x += 7) g1.fillRect(x, 0, 1, px);
    for(let y = 5; y < px; y += 9) g1.fillRect(0, y, px, 1);
    g1.fillStyle = '#ff3355'; g1.fillRect(Math.round(px * .3), Math.round(px * .4), 2, 2);
    const sheet = document.createElement('canvas'); sheet.width = cols * px; sheet.height = rows * px;
    const g = sheet.getContext('2d');
    for(let f = 0; f < CHAR_ANIM_FRAMES; f++) g.drawImage(one, (f % cols) * px, Math.floor(f / cols) * px);
    const blob = await new Promise(r => sheet.toBlob(r, 'image/png'));
    window.__sheetsMade++;
    return charAnimSheetFromBlob(blob, px);
  };
})()"""

# One frame's reading of every flip-book on the screen, in DEVICE px at the real scale (dsf).
READ = r"""(dsf) => {
  const vh = innerHeight, out = [];
  document.querySelectorAll('.screen-rankings .rank-rows .rank-row .char-flip-play').forEach(play => {
    const w = play.getBoundingClientRect();
    if(!w.width || w.bottom < 0 || w.top > vh) return;
    const av = play.parentNode, row = play.closest('.rank-row');
    const svg = av.querySelector(':scope > svg.avatarchar-svg') || av.querySelector(':scope > svg');
    if(!svg) return;
    const s = svg.getBoundingClientRect();
    /* where the frame on show is: an <img> sheet stepped under its window, or a picture that does not move in its box */
    const img = play.querySelector('img'), cv = play.querySelector('canvas');
    let ox = w.left, oy = w.top, ph = '0,0', step = null;
    if(img){
      const r = img.getBoundingClientRect(), cell = w.width;
      const kx = Math.round((w.left - r.left) / cell), ky = Math.round((w.top - r.top) / cell);
      ox = r.left + kx * cell; oy = r.top + ky * cell;
      const fx = (r.left - w.left) * dsf, fy = (r.top - w.top) * dsf;
      ph = (fx - Math.round(fx)).toFixed(2) + ',' + (fy - Math.round(fy)).toFixed(2);
      step = ky * 12 + kx;
    } else if(cv){
      const r = cv.getBoundingClientRect();
      ox = r.left; oy = r.top;
      const fx = (r.left - w.left) * dsf, fy = (r.top - w.top) * dsf;
      ph = (fx - Math.round(fx)).toFixed(2) + ',' + (fy - Math.round(fy)).toFixed(2);
      step = cv.__f >= 0 ? cv.__f : null;
    }
    const cell = w.width;
    out.push({ pub: row && row.dataset.pub, ph, step,
      dx: ((ox + cell / 2) - (s.left + s.width / 2)) * dsf, dy: ((oy + cell / 2) - (s.top + s.height / 2)) * dsf,
      dw: (cell - s.width) * dsf });
  });
  return out;
}"""

ROWS = r"""(dsf) => [...document.querySelectorAll('.screen-rankings .rank-rows .rank-row:not(.rank-row-head):not(.rank-row-skel)')].slice(0, 14).map(r => {
  const b = r.getBoundingClientRect(), a = r.querySelector('.rank-avatar');
  const ab = a ? a.getBoundingClientRect() : b;
  return { pub: r.dataset.pub, y: (b.top + scrollY) * dsf, ay: (ab.top + scrollY) * dsf, ax: ab.left * dsf };
})"""

def reg_shift(a, b):
    """Sub-pixel displacement of b against a (phase correlation + parabolic peak)."""
    a = a.astype(np.float64); b = b.astype(np.float64)
    a = a - a.mean(); b = b - b.mean()
    w = np.hanning(a.shape[0])[:, None] * np.hanning(a.shape[1])[None, :]
    A = np.fft.fft2(a * w); B = np.fft.fft2(b * w)
    R = B * A.conj(); R /= np.abs(R) + 1e-12
    ky = np.fft.fftfreq(a.shape[0])[:, None]; kx = np.fft.fftfreq(a.shape[1])[None, :]
    R *= np.exp(-(ky ** 2 + kx ** 2) / (2 * 0.15 ** 2))
    cc = np.real(np.fft.ifft2(R))
    iy, ix = np.unravel_index(np.argmax(cc), cc.shape)
    H, W = cc.shape
    at = lambda y, x: cc[y % H, x % W]
    c0 = at(iy, ix)
    def par(m, p):
        d = m - 2 * c0 + p
        return 0.5 * (m - p) / d if d else 0.0
    sy = (iy if iy <= H // 2 else iy - H) + par(at(iy - 1, ix), at(iy + 1, ix))
    sx = (ix if ix <= W // 2 else ix - W) + par(at(iy, ix - 1), at(iy, ix + 1))
    return sy, sx

def run_zoom(br, zoom):
    W, H = round(SW / zoom), round(SH / zoom)
    dsf = DPR * zoom
    print("\n== page zoom %.2f: layout %dx%d on a %dx%d screen, %.2f device px per CSS px, devicePixelRatio reads %d" % (zoom, W, H, SW, SH, dsf, DPR), flush=True)
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": SW, "height": SH}, device_scale_factor=dsf, has_touch=True, is_mobile=False)
    ctx.add_init_script(DPR_AS_SAFARI)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
                        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.drill.v1','%s');}catch(e){}" % cb.USED_ACCOUNT)
    pg = cb.open_page(ctx)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(cb.URL, timeout=180000, wait_until="domcontentloaded"); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ try{ store.savedCodeSaved = true; }catch(e){} document.getElementById('splashscreen')?.remove(); __stub(); }")
    pg.evaluate(STILL_SHEETS)
    pg.evaluate(cb._LB_FAKE)
    pg.evaluate("() => showRankings('overall')")
    zc = pg.evaluate("() => ({ zc: getComputedStyle(document.documentElement).getPropertyValue('--zc').trim(), zoomed: document.documentElement.classList.contains('page-zoomed'), dpr: devicePixelRatio, iw: innerWidth })")
    # every character on the screen playing its (still) sheet, and the board moving (lb-go)
    t0 = time.time(); n = 0
    while time.time() - t0 < 180:
        n = pg.evaluate("""() => { const vh = innerHeight; return [...document.querySelectorAll('.screen-rankings .rank-rows .rank-row')].filter(r => {
            const b = r.getBoundingClientRect(); return b.top < vh - 10 && b.bottom > 0 && r.querySelector('.rank-avatar'); }).every(r => r.querySelector('.char-flip-play')) &&
            !document.querySelector('.rank-rows.lb-still') ? document.querySelectorAll('.screen-rankings .rank-rows .char-flip-play').length : 0; }""")
        if n >= 6:
            break
        time.sleep(1)
    geo = pg.evaluate("""() => { const p = document.querySelector('.screen-rankings .rank-row .char-flip-play'); const s = p && p.parentNode.querySelector('svg.avatarchar-svg');
        return p ? { cell: p.getBoundingClientRect().width, cellCss: parseFloat(p.style.width), svgW: s && s.clientWidth, mode: p.querySelector('canvas') ? 'canvas' : 'img',
          loops: document.documentElement.classList.contains('loops-paint') ? 'paint' : 'layers' } : null; }""")
    print("   --zc %s (page-zoomed %s), devicePixelRatio %s, innerWidth %s; %d flip-books playing; %s" % (zc["zc"], zc["zoomed"], zc["dpr"], zc["iw"], n, geo), flush=True)
    if n < 6:
        chk("@%.2f: the board's characters are playing their loops (%d)" % (zoom, n), False, errs)
        ctx.close(); return
    # ---- (1) geometry over FRAMES frames, with snapshots and a scroll ----
    per = {}
    rows_before = pg.evaluate(ROWS, dsf)
    row_moves = []
    scroll_at = FRAMES // 2
    for f in range(FRAMES):
        if f in (15, 35, 60, 80):
            # a snapshot: every number changes, nobody changes place (rows rebuilt, characters carried over)
            pg.evaluate("() => { __rows.forEach(r => { r.correct += 3; r.hundos += 1; r.lastModified = Date.now(); }); __push(); }")
            pg.wait_for_timeout(250)
            after = pg.evaluate(ROWS, dsf)
            for a, b in zip(rows_before, after):
                if a["pub"] == b["pub"]:
                    row_moves.append(max(abs(a["y"] - b["y"]), abs(a["ay"] - b["ay"]), abs(a["ax"] - b["ax"])))
            rows_before = after
        if f == scroll_at:
            pg.evaluate("() => { (document.scrollingElement || document.documentElement).scrollBy({ top: 41, behavior: 'instant' }); }")
            pg.wait_for_timeout(300)
            after = pg.evaluate(ROWS, dsf)
            for a, b in zip(rows_before, after):
                if a["pub"] == b["pub"]:
                    row_moves.append(max(abs(a["y"] - b["y"]), abs(a["ay"] - b["ay"]), abs(a["ax"] - b["ax"])))
            rows_before = after
        r = pg.evaluate("(dsf) => new Promise(res => requestAnimationFrame(() => requestAnimationFrame(() => res((%s)(dsf)))))" % READ.strip(), dsf)
        for t in r:
            d = per.setdefault(t["pub"], {"ph": set(), "steps": set(), "dx": [], "dy": [], "dw": []})
            d["ph"].add(t["ph"]); d["steps"].add(t["step"]); d["dx"].append(t["dx"]); d["dy"].append(t["dy"]); d["dw"].append(t["dw"])
    worst_ph = max(len(d["ph"]) for d in per.values())
    worst_off = max(max(max(abs(v) for v in d["dx"]), max(abs(v) for v in d["dy"])) for d in per.values())
    worst_rng = max(max(max(d["dx"]) - min(d["dx"]), max(d["dy"]) - min(d["dy"])) for d in per.values())
    steps_seen = min(len(d["steps"]) for d in per.values())
    table = {k[-4:]: (len(d["ph"]), round(max(d["dx"]) - min(d["dx"]), 3), round(max(abs(v) for v in d["dx"] + d["dy"]), 3), len(d["steps"])) for k, d in per.items()}
    print("   per character (pub: phases, x range, |offset| max, steps seen):", table, flush=True)
    chk("@%.2f (1) every character's frame is put on ONE sub-pixel phase at every step (worst %d phases; %d characters, >= %d steps each)" % (zoom, worst_ph, len(per), steps_seen),
        worst_ph == 1 and steps_seen >= 8, table)
    chk("@%.2f (1) ...and stays within 0.1 device px of its drawing through steps, snapshots and a scroll (offset up to %.3f, varying %.3f)" % (zoom, worst_off, worst_rng),
        worst_off <= 0.1 and worst_rng <= 0.1, table)
    # ---- (3) rows ----
    chk("@%.2f (3) a snapshot or a scroll puts every row back on the device pixel it was on (worst %.4f device px over %d readings)" % (zoom, max(row_moves) if row_moves else -1, len(row_moves)),
        row_moves and max(row_moves) <= 0.01, row_moves[:20])
    # ---- (2) pixels: the avatar column at device scale, many steps, compared with the first ----
    col = pg.evaluate("""() => { const vh = innerHeight; const as = [...document.querySelectorAll('.screen-rankings .rank-rows .rank-row .rank-avatar')].map(a => a.getBoundingClientRect()).filter(b => b.top > 4 && b.bottom < vh - 4);
        if(!as.length) return null; const x0 = Math.min(...as.map(b => b.left)) - 2, x1 = Math.max(...as.map(b => b.right)) + 2;
        return { x: x0, y: as[0].top - 2, w: x1 - x0, h: as[as.length - 1].bottom - as[0].top + 4, boxes: as.map(b => [b.left, b.top, b.width, b.height]) }; }""")
    shots, frames_seen = [], set()
    for s in range(SHOTS):
        buf = pg.screenshot(clip={"x": col["x"], "y": col["y"], "width": col["w"], "height": col["h"]}, scale="device", animations="allow")
        im = np.asarray(Image.open(io.BytesIO(buf)).convert("L"), dtype=np.float64)
        st = pg.evaluate("""() => [...document.querySelectorAll('.screen-rankings .rank-rows .rank-row .char-flip-play')].slice(0, 3).map(p => {
            const i = p.querySelector('img'), c = p.querySelector('canvas');
            if(c) return String(c.__f); if(!i) return '';
            const r = i.getBoundingClientRect(), w = p.getBoundingClientRect(); return Math.round((w.left - r.left) / w.width) + ':' + Math.round((w.top - r.top) / w.width); }).join('|')""")
        frames_seen.add(st)
        shots.append(im)
        pg.wait_for_timeout(37)
    h = min(s.shape[0] for s in shots); w = min(s.shape[1] for s in shots)
    shots = [s[:h, :w] for s in shots]
    # each avatar on its own: its box in the capture, registered against the first capture
    worst = 0.0; worst_diff = 0.0; per_av = []
    for (bx, by, bw, bh) in col["boxes"]:
        x0 = int(round((bx - col["x"]) * dsf)) + 4; y0 = int(round((by - col["y"]) * dsf)) + 4
        x1 = int(round((bx - col["x"] + bw) * dsf)) - 4; y1 = int(round((by - col["y"] + bh) * dsf)) - 4
        if x1 - x0 < 16 or y1 - y0 < 16 or y1 > h or x1 > w:
            continue
        ref = shots[0][y0:y1, x0:x1]
        mx = 0.0; md = 0.0
        for s in shots[1:]:
            cur = s[y0:y1, x0:x1]
            d = float(np.abs(cur - ref).max())
            md = max(md, d)
            if d > 0:
                sy, sx = reg_shift(ref, cur)
                mx = max(mx, abs(sy), abs(sx))
        per_av.append((round(mx, 3), round(md, 1)))
        worst = max(worst, mx); worst_diff = max(worst_diff, md)
    print("   pixels: %d captures over %d different steps of the first three loops; per avatar (largest shift, largest grey-level difference): %s" % (len(shots), len(frames_seen), per_av), flush=True)
    if DUMP:
        os.makedirs(DUMP, exist_ok=True)
        for i, s in enumerate(shots[:12]):
            Image.fromarray(s.astype(np.uint8)).save(os.path.join(DUMP, "z%.2f-%02d.png" % (zoom, i)))
    chk("@%.2f (2) the avatar column, captured on %d different steps, is the same picture every time: no character drawn 0.1 device px off (worst %.3f px, %.0f grey levels)" % (zoom, len(frames_seen), worst, worst_diff),
        len(frames_seen) >= 6 and worst <= 0.1, per_av)
    # ---- (5) every other place a character loops: the Leaderboard's other boards, and Customize (every builder - the boards, the
    # Virtual Room's lobby and results, friends, chat faces, pickers - goes through setCharState -> charFlipAttach, one path) ----
    ANY = r"""async (dsf) => { const wait = ms => new Promise(r => setTimeout(r, ms));
      const on = () => [...document.querySelectorAll('#stage .char-flip-play')].filter(p => { const b = p.getBoundingClientRect(); return b.width && b.bottom > 0 && b.top < innerHeight; });
      const ph = new Map(), st = new Map();
      for(let f = 0; f < 24; f++){ await new Promise(r => requestAnimationFrame(r));
        on().forEach(p => { const k = p.querySelector('img, canvas'); if(!k) return; const r = k.getBoundingClientRect(), w = p.getBoundingClientRect();
          const fx = (r.left - w.left) * dsf, fy = (r.top - w.top) * dsf;
          if(!ph.has(p)){ ph.set(p, new Set()); st.set(p, new Set()); }
          ph.get(p).add((fx - Math.round(fx)).toFixed(2) + ',' + (fy - Math.round(fy)).toFixed(2));
          st.get(p).add(k.tagName === 'CANVAS' ? k.__f : Math.round((w.left - r.left) / w.width) + ':' + Math.round((w.top - r.top) / w.width)); });
        if(f % 6 === 5) await wait(60); }
      const tiles = on();
      return { n: tiles.length, img: tiles.filter(p => p.querySelector('img')).length, cv: tiles.filter(p => p.querySelector('canvas.char-flip-cv')).length,
               worstPh: Math.max(0, ...[...ph.values()].map(s => s.size)), minSteps: Math.min(99, ...[...st.values()].map(s => s.size)) }; }"""
    places = []
    keys = pg.evaluate("() => RANKING_BOARDS.map(b => b.key)")
    pg.evaluate("() => (document.scrollingElement || document.documentElement).scrollTo({ top: 0, behavior: 'instant' })")
    for i, k in enumerate(keys):
        pg.evaluate("i => { const b = document.querySelectorAll('.screen-rankings .navsegment .iconbtn')[i]; if(b) b.click(); }", i)
        pg.wait_for_timeout(1800)
        places.append(("board " + k, pg.evaluate(ANY, dsf)))
    pg.evaluate("() => showCustomize()")
    t0 = time.time()
    while time.time() - t0 < 120 and pg.evaluate("""() => [...document.querySelectorAll('#stage .avatarchar-option.char-flip')].filter(o => { const b = o.getBoundingClientRect(); return b.bottom > 0 && b.top < innerHeight; }).some(o => !o.querySelector('.char-flip-play'))"""):
        time.sleep(1)
    places.append(("customize", pg.evaluate(ANY, dsf)))
    print("   other places:", places, flush=True)
    bad = [p for p in places if p[1]["n"] and (p[1]["worstPh"] != 1 or p[1]["minSteps"] < 3)]
    chk("@%.2f (5) every other board and Customize: each loop on the screen holds still in its box at every step (%d places, %d loops)" % (zoom, len(places), sum(p[1]["n"] for p in places)),
        not bad and sum(p[1]["n"] for p in places) >= 10, bad)
    chk("@%.2f (4) no page errors" % zoom, not errs, errs)
    ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for z in ZOOMS:
        run_zoom(br, z)
    br.close()
print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
