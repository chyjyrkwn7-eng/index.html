"""Build 384.122 (boardshake2): the Leaderboard's RANK FLARES hold still at any page zoom, as its characters do (384.112 / 384.99).

384.99 took the shake out of the characters (each loop is a canvas the size of one cell of its sheet, a frame COPIED into it a step, in a
box that never moves) and reported, in its notes, that the rank flares in the same rows shivered the same way and were not changed:
his 384.99 recording at Safari's page zoom 85% (layout 518 x 1125 CSS px on a 440 x 956pt screen, devicePixelRatio still 3) showed the
flares moving +-0.2-0.57px back and forth on their 30-a-second sheet. The cause is the characters': the sheet is SLID under a window by
a cell a step (a stepped CSS animation), and under page zoom a step is not whole device pixels - the flare's cell is 29 CSS px = 73.93
device px, so each column of the sheet lands 0.07 further off the grid (0.84 by the row's end) and the phone's painting rounds it.
Madison: "this isn't optional, fix it".

Here the page is laid out as his phone lays it out (layout = screen / zoom, the screen 440 x 956, Chromium painting at 3 x zoom device px
per CSS px, devicePixelRatio reading 3, as Safari's does), the Overall board of each class with classmates on it (rank flares in the Rank
column), at page zoom 1.0, 0.85 and 0.75, and over 60 frames (a scroll in the middle) for every flare on the screen:
 (1) PLAYING: at least 3 flares are on the rows and each shows 8+ different frames of its loop;
 (2) ONE PHASE: the frame on show is on ONE sub-pixel phase in its window at every step, and its centre stays within 0.1 device px of the
     bubble's centre through every step and the scroll (a slid sheet lands on a new fraction of a pixel every column: 12+ phases);
 (3) PIXELS: with every flare's sheet a STILL picture (each of its 180 cells the same drawing under a fine grid), the flare column captured at
     the device's scale on 24 different steps is the same picture every time (sub-pixel registration, <= 0.1 device px);
 (4) the characters beside them still hold (one phase, within 0.1 device px: 384.99's own check, kept);
 (5) HOME is untouched: its bubbles' flares are still a sheet under a stepped animation (the change is the board's rows only);
 (6) no page errors.
Must FAIL on origin/main 384.107 (the flares there are an <img> slid by a stepped animation) and pass on this build.

Run:  TMPDIR=/dev/shm python3 tools/check-b384-boardshake2.py [--zooms 1,0.85,0.75] [--classes academy,ifc] [--frames 60] [--against OLD/index.html]
"""
import os, sys, time, re, io, json, base64, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
ZOOMS = [float(z) for z in arg("--zooms", "1,0.85,0.75").split(",")]
CLASSES = arg("--classes", "academy,ifc").split(",")
FRAMES = int(arg("--frames", "60"))
SRC = arg("--against", os.path.join(ROOT, "index.html"))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
RAW = io.open(SRC, encoding="utf-8").read()
SW, SH, DPR = 440, 956, 3
ok = True
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:700]), flush=True)

# ---- a board of nineteen classmates for both classes (the academy's in `leaderboard`, Fire Code's in vrooms/lb-ifc-v1), offline ----
NAMES = ["Avery", "Logan", "Sam", "Matt", "Cody", "Dana", "Rookie", "Jordan", "Riley", "Quinn", "Taylor", "Morgan", "Reese", "Parker", "Drew", "Skyler", "Rowan", "Emerson", "Hayden"]
CHARS = ["detective", "wizard", "ghost", "grizzly", "ninja", "alien", "samurai", "ninja", "queen", "alien", "wizard", "dragon", "grizzly", "ghost", "alien", "samurai", "wizard", "queen", "dragon"]
WK = g["week_key_now"]()
ME = "pubme000bs2"
ROWS = []
for i, (n, a) in enumerate(zip(NAMES, CHARS)):
    p = "pubbs2%06d" % (i + 1)
    ROWS.append({"code": p, "pub": p, "publicId": p, "firstName": n, "avatarChar": a, "level": max(1, 40 - i * 2), "badges": max(0, 10 - i),
                 "hundos": (400 - i * 10) if i < 14 else (100 - i), "correct": 3000 - i * 100, "week": WK, "weekPoints": (900 - i * 120) if i < 2 else max(10, 600 - i * 25)})
FAKE = """(function(){ var ROWS = %s; var MAP = {}; ROWS.forEach(function(r){ MAP[r.pub] = r; });
  function docRef(id){ var has = id === 'lb-ifc-v1'; var snap = { exists: has, id: id, metadata:{fromCache:false}, data: function(){ return has ? { kind:'board', cls:'ifc', rows: MAP } : null; } };
    return { get: function(){ return Promise.resolve(snap); }, set: function(){ return Promise.resolve(); }, update: function(){ return Promise.resolve(); }, delete: function(){ return Promise.resolve(); },
      collection: function(){ return collRef('sub'); }, onSnapshot: function(a, b){ var next = typeof a === 'function' ? a : b; setTimeout(function(){ next(snap); }, 40); return function(){}; } }; }
  function collRef(name){ var rows = name === 'leaderboard' ? ROWS : [];
    var s = { forEach: function(cb){ rows.forEach(function(r){ cb({ id: r.code, data: function(){ return r; } }); }); }, size: rows.length, docs: [], metadata: { fromCache:false } };
    var c = { doc: function(id){ return docRef(id); }, where: function(){ return c; }, orderBy: function(){ return c; }, limit: function(){ return c; }, get: function(){ return Promise.resolve(s); },
      onSnapshot: function(a, b){ var next = typeof a === 'function' ? a : b; setTimeout(function(){ next(s); }, 60); return function(){}; } }; return c; }
  window.firebase = { apps: [], initializeApp: function(){ this.apps.push({}); }, firestore: Object.assign(function(){ return { collection: collRef, doc: function(p){ return docRef(String(p).split('/').pop()); } }; }, { FieldValue: { serverTimestamp: function(){ return Date.now(); }, delete: function(){ return null; }, increment: function(n){ return n; }, arrayUnion: function(){ return []; }, arrayRemove: function(){ return []; } }, FieldPath: function(){} }) };
})();""" % json.dumps(ROWS)
def seed(cls):
    d = json.loads(g["SEED"].replace("__WEEK__", WK)); d["publicId"] = ME; d["firstName"] = "Casey"
    d["classes"] = ["academy", "ifc"] if cls == "ifc" else ["academy"]
    return json.dumps(d)
DPR_AS_SAFARI = "Object.defineProperty(window, 'devicePixelRatio', { get: () => %d, configurable: true });" % DPR
srv, URL = g["serve"]()

def boot(br, cls, zoom, errs):
    LW, LH = round(SW / zoom), round(SH / zoom)
    ctx = br.new_context(viewport={"width": LW, "height": LH}, screen={"width": SW, "height": SH}, device_scale_factor=DPR * zoom, has_touch=True, is_mobile=False)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(FAKE)
    if zoom != 1.0: ctx.add_init_script(DPR_AS_SAFARI)
    ctx.add_init_script("try{ if(!localStorage.getItem('class26e.drill.v1')){ localStorage.setItem('class26e.freshstart','1'); localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-BS2');"
                        "['class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted','class26e.penal256578.seen','class26e.penal55124.seen','class26e.penal124256.seen'].forEach(k=>localStorage.setItem(k,'1'));"
                        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31'); localStorage.setItem('class26e.a2hs','1790500000000'); %s } }catch(e){}"
                        % (json.dumps(seed(cls)), "localStorage.setItem('class26e.activeclass','ifc');" if cls == "ifc" else ""))
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append("%s @%.2f: %s" % (cls, zoom, str(e)[:200])))
    body = g["INSET_RE"].sub(lambda m: "0px", RAW)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    bm = re.search(r'const APP_BUILD = "([^"]+)"', RAW); vj = json.dumps({"build": bm.group(1) if bm else "", "note": "", "frameId": "", "force": True})
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=vj))
    pg.goto(URL, timeout=180000, wait_until="domcontentloaded"); pg.wait_for_timeout(4500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"); pg.wait_for_timeout(900)
    pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.daily-alert,.toast,#tour-overlay,#tour-tooltip,#nova-intro,.nova-talk,.unlock-card,.rs-spot').forEach(n=>n.remove()); }")
    return ctx, pg

# every character's and every flare's sheet a STILL: its drawing in each cell under a fine crisp grid, so any move between steps is the loop moving
STILL = r"""(() => {
  const mk = async (svgEl, px, cols, frames) => {
    const rows = Math.ceil(frames / cols);
    const svg = svgEl.cloneNode(true); svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); svg.setAttribute('width', px); svg.setAttribute('height', px);
    const img = new Image(); img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(svg));
    try{ await img.decode(); }catch(e){}
    const one = document.createElement('canvas'); one.width = one.height = px; const g1 = one.getContext('2d');
    g1.fillStyle = '#20242c'; g1.fillRect(0, 0, px, px);
    try{ g1.drawImage(img, 0, 0, px, px); }catch(e){}
    g1.fillStyle = 'rgba(255,255,255,.85)';
    for(let x = 3; x < px; x += 7) g1.fillRect(x, 0, 1, px);
    for(let y = 5; y < px; y += 9) g1.fillRect(0, y, px, 1);
    g1.fillStyle = '#ff3355'; g1.fillRect(Math.round(px * .3), Math.round(px * .4), 2, 2);
    const sheet = document.createElement('canvas'); sheet.width = cols * px; sheet.height = rows * px; const g = sheet.getContext('2d');
    for(let f = 0; f < frames; f++) g.drawImage(one, (f % cols) * px, Math.floor(f / cols) * px);
    return await new Promise(r => sheet.toBlob(r, 'image/png'));
  };
  window.recordCharSheet = async function(drawing, px){ return charAnimSheetFromBlob(await mk(drawing.svg, px, CHAR_ANIM_COLS, CHAR_ANIM_FRAMES), px); };
  window.recordRankSheet = async function(drawing, px, key){ return orbitAnimSheetFromBlob(await mk(drawing.svg, px, ORBIT_ANIM_COLS, ORBIT_ANIM_FRAMES), px); };
})()"""

# one frame's reading of every flare and every character on the board, in DEVICE px at the real scale (dsf)
READ = r"""(dsf) => {
  const vh = innerHeight, out = { flares: [], chars: [] };
  document.querySelectorAll('.screen-rankings .rank-rows .rank-row').forEach(row => {
    const pub = row.dataset.pub || '';
    row.querySelectorAll('.cosmic-rank-anim').forEach((wrap, i) => {
      const fr = wrap.querySelector('.rk-frame'), badge = wrap.parentNode; if(!fr) return;
      const w = fr.getBoundingClientRect(); if(!w.width || w.bottom < 0 || w.top > vh) return;
      const bb = badge.getBoundingClientRect(); const cell = w.width;
      const cv = fr.querySelector('canvas'), img = fr.querySelector('img');
      let ox = w.left, oy = w.top, ph = '0,0', step = null, kind = 'none';
      if(cv){ const r = cv.getBoundingClientRect(); ox = r.left; oy = r.top; const fx = (r.left - w.left) * dsf, fy = (r.top - w.top) * dsf; ph = (fx - Math.round(fx)).toFixed(2) + ',' + (fy - Math.round(fy)).toFixed(2); step = cv.__f >= 0 ? cv.__f : null; kind = 'canvas'; }
      else if(img){ const r = img.getBoundingClientRect(); const kx = Math.round((w.left - r.left) / cell), ky = Math.round((w.top - r.top) / cell);
        ox = r.left + kx * cell; oy = r.top + ky * cell; const fx = (r.left - w.left) * dsf, fy = (r.top - w.top) * dsf; ph = (fx - Math.round(fx)).toFixed(2) + ',' + (fy - Math.round(fy)).toFixed(2); step = ky * 12 + kx; kind = 'img'; }
      else return;
      out.flares.push({ k: pub + '#' + i, kind, ph, step, dx: ((ox + cell / 2) - (bb.left + bb.width / 2)) * dsf, dy: ((oy + cell / 2) - (bb.top + bb.height / 2)) * dsf });
    });
    const play = row.querySelector('.char-flip-play');
    if(play){ const w = play.getBoundingClientRect(); const av = play.parentNode; if(!(w.width && w.bottom > 0 && w.top < vh)) return;
      const svg = av.querySelector(':scope > svg.avatarchar-svg') || av.querySelector(':scope > svg'); const cv = play.querySelector('canvas'), img = play.querySelector('img'); if(!svg || !(cv || img)) return;
      const s = svg.getBoundingClientRect(), e = (cv || img).getBoundingClientRect(), cell = w.width; let ox = e.left, oy = e.top, ph, step = null;
      const fx = (e.left - w.left) * dsf, fy = (e.top - w.top) * dsf; ph = (fx - Math.round(fx)).toFixed(2) + ',' + (fy - Math.round(fy)).toFixed(2);
      if(img){ const kx = Math.round((w.left - e.left) / cell), ky = Math.round((w.top - e.top) / cell); ox = e.left + kx * cell; oy = e.top + ky * cell; step = ky * 12 + kx; } else step = cv.__f;
      out.chars.push({ k: pub, ph, step, dx: ((ox + cell / 2) - (s.left + s.width / 2)) * dsf, dy: ((oy + cell / 2) - (s.top + s.height / 2)) * dsf }); }
  });
  return out; }"""

def reg_shift(a, b):
    """Sub-pixel displacement of b against a (phase correlation + parabolic peak)."""
    a = a.astype(np.float64); b = b.astype(np.float64); a = a - a.mean(); b = b - b.mean()
    w = np.hanning(a.shape[0])[:, None] * np.hanning(a.shape[1])[None, :]
    A = np.fft.fft2(a * w); B = np.fft.fft2(b * w); R = B * A.conj(); R /= np.abs(R) + 1e-12
    ky = np.fft.fftfreq(a.shape[0])[:, None]; kx = np.fft.fftfreq(a.shape[1])[None, :]
    R *= np.exp(-(ky ** 2 + kx ** 2) / (2 * 0.15 ** 2)); cc = np.real(np.fft.ifft2(R))
    iy, ix = np.unravel_index(np.argmax(cc), cc.shape); H, W = cc.shape; at = lambda y, x: cc[y % H, x % W]; c0 = at(iy, ix)
    def par(m, p):
        d = m - 2 * c0 + p
        return 0.5 * (m - p) / d if d else 0.0
    return (iy if iy <= H // 2 else iy - H) + par(at(iy - 1, ix), at(iy + 1, ix)), (ix if ix <= W // 2 else ix - W) + par(at(iy, ix - 1), at(iy, ix + 1))

def stats(samples):
    per = {}
    for s in samples:
        d = per.setdefault(s["k"], {"ph": set(), "steps": set(), "dx": [], "dy": [], "kind": s.get("kind")})
        d["ph"].add(s["ph"]); d["steps"].add(s["step"]); d["dx"].append(s["dx"]); d["dy"].append(s["dy"])
    return per
def worst(per):
    if not per: return (0, 0, 0, 0)
    return (max(len(d["ph"]) for d in per.values()), max(max(max(abs(v) for v in d["dx"]), max(abs(v) for v in d["dy"])) for d in per.values()),
            max(max(max(d["dx"]) - min(d["dx"]), max(d["dy"]) - min(d["dy"])) for d in per.values()), min(len(d["steps"]) for d in per.values()))

def run(br, cls, zoom):
    errs = []
    dsf = DPR * zoom
    print("\n== %s at page zoom %.2f: layout %dx%d on a %dx%d screen, %.2f device px per CSS px, devicePixelRatio reads %d" % (cls, zoom, round(SW / zoom), round(SH / zoom), SW, SH, dsf, DPR), flush=True)
    ctx, pg = boot(br, cls, zoom, errs)
    pg.evaluate(STILL)
    pg.evaluate("() => { store.seenRewardsTour = true; showRankings('overall'); }")
    t0 = time.time(); nfl = nch = 0
    while time.time() - t0 < 180:
        nch = pg.evaluate("() => document.querySelectorAll('.screen-rankings .rank-rows .char-flip-play').length")
        nfl = pg.evaluate("() => document.querySelectorAll('.screen-rankings .rank-rows .cosmic-rank-anim .rk-frame img, .screen-rankings .rank-rows .cosmic-rank-anim .rk-frame canvas').length")
        busy = pg.evaluate("() => !!document.querySelector('.rank-rows.lb-still')")
        if nch >= 4 and nfl >= 3 and not busy: break
        time.sleep(1)
    pg.wait_for_timeout(1500)
    info = pg.evaluate("() => ({ iw: innerWidth, dpr: devicePixelRatio, zc: getComputedStyle(document.documentElement).getPropertyValue('--zc').trim(), loops: document.documentElement.classList.contains('loops-paint') ? 'paint' : 'layers' })")
    print("   innerWidth %s, devicePixelRatio %s, --zc %s, loops %s; %d characters, %d flares playing" % (info["iw"], info["dpr"], info["zc"], info["loops"], nch, nfl), flush=True)
    chk("@%s %.2f (1) the board has characters and rank flares playing (%d, %d)" % (cls, zoom, nch, nfl), nch >= 4 and nfl >= 3, errs)
    if nch < 4 or nfl < 3:
        ctx.close(); return
    fl, ch = [], []
    for f in range(FRAMES):
        if f == FRAMES // 2:
            pg.evaluate("() => { (document.scrollingElement || document.documentElement).scrollBy({ top: 41, behavior: 'instant' }); }"); pg.wait_for_timeout(300)
        r = pg.evaluate("(d) => new Promise(res => requestAnimationFrame(() => requestAnimationFrame(() => res((%s)(d)))))" % READ.strip(), dsf)
        fl += r["flares"]; ch += r["chars"]
    pf, pc = stats(fl), stats(ch)
    kinds = sorted({d["kind"] for d in pf.values()})
    w1 = worst(pf); w2 = worst(pc)
    chk("@%s %.2f (1) %d flares each show 8+ frames of their loop (%s; fewest %d)" % (cls, zoom, len(pf), "/".join(kinds), w1[3]), len(pf) >= 3 and w1[3] >= 8, {k[-8:]: len(d["steps"]) for k, d in pf.items()})
    chk("@%s %.2f (2) every flare's frame is put on ONE sub-pixel phase at every step (worst %d phases)" % (cls, zoom, w1[0]), w1[0] == 1, {k[-8:]: len(d["ph"]) for k, d in pf.items()})
    chk("@%s %.2f (2) ...and stays within 0.1 device px of its bubble's centre through steps and a scroll (offset up to %.3f, varying %.3f)" % (cls, zoom, w1[1], w1[2]), w1[1] <= 0.1 and w1[2] <= 0.1, {k[-8:]: (round(max(d['dx']) - min(d['dx']), 3), round(max(d['dy']) - min(d['dy']), 3)) for k, d in pf.items()})
    chk("@%s %.2f (4) the characters beside them still hold: one phase, within 0.1 device px (%d phases, offset %.3f, varying %.3f)" % (cls, zoom, w2[0], w2[1], w2[2]), pc and w2[0] == 1 and w2[1] <= 0.1 and w2[2] <= 0.1, {k[-4:]: len(d["ph"]) for k, d in pc.items()})
    # (3) pixels: the flare column at the device's scale, many steps
    pg.evaluate("() => (document.scrollingElement || document.documentElement).scrollTo({ top: 0, behavior: 'instant' })"); pg.wait_for_timeout(400)
    col = pg.evaluate("""() => { const vh = innerHeight; const as = [...document.querySelectorAll('.screen-rankings .rank-rows .rank-row .cosmic-rank-anim')].map(a => a.parentNode.getBoundingClientRect()).filter(b => b.width && b.top > 4 && b.bottom < vh - 4).slice(0, 8);
        if(!as.length) return null; const x0 = Math.min(...as.map(b => b.left)) - 2, x1 = Math.max(...as.map(b => b.right)) + 2, y0 = Math.min(...as.map(b => b.top)) - 2, y1 = Math.max(...as.map(b => b.bottom)) + 2;
        return { x: x0, y: y0, w: x1 - x0, h: y1 - y0, boxes: as.map(b => [b.left, b.top, b.width, b.height]) }; }""")
    shots = []; steps = set()
    cdp = ctx.new_cdp_session(pg)
    for s in range(24):
        buf = base64.b64decode(cdp.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False,
                                                                   "clip": {"x": col["x"], "y": col["y"], "width": col["w"], "height": col["h"], "scale": dsf}})["data"])
        shots.append(np.asarray(Image.open(io.BytesIO(buf)).convert("L"), dtype=np.float64))
        steps.add(pg.evaluate("() => [...document.querySelectorAll('.screen-rankings .rank-rows .cosmic-rank-anim .rk-frame')].slice(0, 3).map(fr => { const c = fr.querySelector('canvas'), i = fr.querySelector('img'); if(c) return String(c.__f); if(!i) return ''; const r = i.getBoundingClientRect(), w = fr.getBoundingClientRect(); return Math.round((w.left - r.left) / w.width) + ':' + Math.round((w.top - r.top) / w.width); }).join('|')"))
        pg.wait_for_timeout(37)
    h = min(s.shape[0] for s in shots); wd = min(s.shape[1] for s in shots); shots = [s[:h, :wd] for s in shots]
    worst_px = 0.0; per_fl = []
    for (bx, by, bw, bh) in col["boxes"]:
        x0 = int(round((bx - col["x"]) * dsf)) + 3; y0 = int(round((by - col["y"]) * dsf)) + 3; x1 = int(round((bx - col["x"] + bw) * dsf)) - 3; y1 = int(round((by - col["y"] + bh) * dsf)) - 3
        if x1 - x0 < 14 or y1 - y0 < 14 or y1 > h or x1 > wd: continue
        ref = shots[0][y0:y1, x0:x1]; mx = 0.0
        for s in shots[1:]:
            cur = s[y0:y1, x0:x1]
            if float(np.abs(cur - ref).max()) > 0:
                sy, sx = reg_shift(ref, cur); mx = max(mx, abs(sy), abs(sx))
        per_fl.append(round(float(mx), 3)); worst_px = max(worst_px, mx)
    print("   pixels: %d captures over %d different steps of the first three flares; largest shift per flare %s" % (len(shots), len(steps), per_fl), flush=True)
    chk("@%s %.2f (3) the flare column, captured on %d different steps, is the same picture every time: no flare drawn 0.1 device px off (worst %.3f px)" % (cls, zoom, len(steps), worst_px),
        len(steps) >= 6 and per_fl and worst_px <= 0.1, per_fl)
    # (5) Home's bubbles are as they were (only on the first run of each class: it is the same code)
    if zoom == 1.0:
        pg.evaluate("() => showHome()")
        t1 = time.time(); n = 0
        while time.time() - t1 < 150:
            n = pg.evaluate("() => document.querySelectorAll('.screen-home-actual .cosmic-rank-anim .rk-frame img').length")
            if n >= 2: break
            time.sleep(1)
        home = pg.evaluate("() => ({ img: document.querySelectorAll('.screen-home-actual .cosmic-rank-anim .rk-frame img').length, cv: document.querySelectorAll('.screen-home-actual .cosmic-rank-anim .rk-frame canvas').length, anim: [...document.querySelectorAll('.screen-home-actual .cosmic-rank-anim .rk-frame img')].slice(0, 2).map(i => getComputedStyle(i).animationName.slice(0, 7)) })")
        chk("@%s %.2f (5) Home's bubbles are untouched: their flares are still a sheet under a stepped animation (%s)" % (cls, zoom, home), home["img"] >= 2 and home["cv"] == 0, home)
    chk("@%s %.2f (6) no page errors" % (cls, zoom), not errs, errs)
    ctx.close()

with sync_playwright() as pw:
    for cls in CLASSES:
        for z in ZOOMS:
            for attempt in (1, 2, 3):
                br = pw.chromium.launch(executable_path=g["CHROME"])
                try:
                    run(br, cls, z); break
                except Exception as e:
                    msg = str(e).splitlines()[0][:160]
                    if attempt == 3 or not any(w in msg for w in ("crashed", "Target closed", "closed", "Timeout")):
                        chk("@%s %.2f ran to the end" % (cls, z), False, msg); break
                    print("   (the browser was lost: %s - once more)" % msg, flush=True)
                finally:
                    try: br.close()
                    except Exception: pass
print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
