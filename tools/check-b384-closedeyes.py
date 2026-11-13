#!/usr/bin/env python3
"""Build 384.113 (closedeyes): a character's closed eyes are DRAWN, never just gone.

  Madison, on a classmate's card opened from the Leaderboard (the Toxic Spill, asleep, with its "z"): "His eyes close just look
  missing. Fix that."

  The Toxic Spill's eyes sit in dark sockets. Asleep, its open eyes are hidden and its closed eyes (closedEyes()) shown - but the
  closed eyes were a curve in #1E0434 drawn on a socket of #24063F, so all that was left was three empty holes. Its blink squashed
  the three eyes about the middle of the eye GROUP (they sit at three heights), so the top eye's line landed on the skin above its
  socket and the two big ones' at their sockets' top edges: holes again. And every character's blink (cx-blink, a squash to a tenth
  of the eye's height) left a lit or pale eye a hairline or nothing: the closed eyes now come down for the bottom of each blink.

For EVERY character on BOTH class pages (the academy and Fire Code; every id the page keeps, not retired), drawn live:
  A. A FULL IDLE CYCLE: every animation paused on one shared clock and stepped over the longest eye loop (120 steps, plus the exact
     bottom of every blink). The frames where the eyes are closed - the eye group's height (its own transform and its eyes') under
     half, or the eyes put out altogether (a lit eye that dims or flickers is a light, not an eye closing) - are shot, the deepest of
     each closing. An eye that is still open in that frame (a wink shuts one) is left for its own closing.
  B. ASLEEP is shot (char-sleep and char-live, as setCharState makes a sleeper: the pose the person card shows with its "z").
  Each eye's region is found by what it is: the same pose and moment with the open eyes shown, against the same with the open AND
  the closed eyes hidden (the bare face); one region per connected eye (a glint under a sixth of the biggest is not an eye). Inside
  each shut eye's region, at the bottom of a blink and asleep alike, the LID LINE: pixels in the drawing's own lid colour (what its
  closed eyes' lines are stroked in) that run as a LINE - no thicker than .45 of the eye or one drawing unit, with something that is
  not lid colour right above and below, its colour standing off both by >= 40 (RGB distance) - across at least 40% of the eye's
  width, more of it than the bare face already has there. A socket left empty is one thick dark run, not a line, so it fails; a
  hairline of a squashed lit eye is not in the lid colour, so it fails. An empty eye group (Void, the Koi's painted eyes, the Drone
  Pilot's goggles) has nothing to close. A sleeping pose that covers the eyes (the Sheriff tips his hat brim over them: under 45% of
  the eyes left in view) is covered, not missing, and is reported, not asked for a lid.
  C. LEGIBLE SMALL: asleep at a 42px rankings row (126 device pixels, a 3x phone): the lid line across at least 35% of each eye,
     standing off by >= 28.
  D. THE FLIP-BOOKS RE-RECORD: CHAR_ANIM_VER is not 384.95's (c5), so a sheet recorded before this build is never played.
  F. THE FLIP-BOOK ITSELF: the app's own recorder (recordCharFrames) makes the sheet a 42px row plays, for the Toxic Spill (Fire Code)
     and Frost (the academy); its frame whose eyes differ most from the sheet's usual frame - the bottom of the blink - shows the lid
     line in every eye, as C measures it.
  E. no page error on either page.

  python3 tools/check-b384-closedeyes.py                          (both pages, every character)
  python3 tools/check-b384-closedeyes.py --only astronaut,ghost   (some ids)   --class ifc   (one page)
  python3 tools/check-b384-closedeyes.py --against OLD/index.html (must FAIL: the Toxic Spill on 384.95)
  python3 tools/check-b384-closedeyes.py --shots DIR              (also writes each character's open / blink / asleep frames)
"""
import base64, io, json, os, re, sys
from collections import deque
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np

BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
CLASSES = sys.argv[sys.argv.index("--class") + 1].split(",") if "--class" in sys.argv else ["academy", "ifc"]
PREV_VER = "c5"   # 384.95's CHAR_ANIM_VER
# F: the characters whose blink this build changed, by page - their flip-book is recorded and its blink frame read
FLIP = {"ifc": ["astronaut"], "academy": ["frost"]}
ok = True
fails = []
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    if not cond: fails.append(name)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4closedeye", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = {"ifc": ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
               "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
               "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
               "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S),
        "academy": ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                    "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S}

BIG = 240      # css px; the context is 2x, so 480 device px - about 14 a drawing unit
SMALL = 63     # 126 device px: a 42px rankings row on a 3x phone
SETUP = r"""() => {
  document.getElementById('splashscreen')?.remove();
  const st = document.createElement('style'); st.id = 'ce-style';
  st.textContent = '.cehost{position:fixed;background:#1E2026;z-index:2147483647;overflow:hidden;contain:strict}' +
    '.cehost > svg{width:100%;height:100%;display:block}' +
    '.cehost.ce-eyes-on .cx-eyes{opacity:1!important;visibility:visible!important}' +
    '.cehost.ce-eyes-off .cx-eyes{visibility:hidden!important}' +
    '.cehost.ce-shut-off .cx-eyes-closed{visibility:hidden!important}' +
    '.cehost.ce-eyes-still :is(.cx-eyes, .cx-eyes *){animation:none!important;transform:none!important;scale:none!important;translate:none!important}' +
    'body > :not(.cehost):not(script):not(style){visibility:hidden!important}';
  /* (visibility, not display: the drawings' depth shading is a filter in an svg in the page, and an svg filter in a display:none
     subtree draws nothing - the whole character went) */
  document.body.appendChild(st);
  const ids = AVATAR_CHARACTERS.filter(c => !c.retired).map(c => c.id);
  return { cls: window.NOVA_CLASS || 'academy', ids, ver: typeof CHAR_ANIM_VER === 'string' ? CHAR_ANIM_VER : null,
    names: Object.fromEntries(ids.map(i => [i, (AVATAR_DISPLAY_NAME[i] || i)])),
    kinds: Object.fromEntries(ids.map(i => [i, AVATAR_CHARACTERS.find(c => c.id === i).kind])) };
}"""
# mount one character several times side by side, for one screenshot: state '' | 'live' | 'sleep' (asleep is char-sleep AND
# char-live, as setCharState makes a sleeper), every animation paused at t; each copy is [extra classes, size, x, y]
MOUNT = r"""([id, state, t, copies]) => {
  document.querySelectorAll('.cehost').forEach(n => n.remove());
  let sv = null;
  copies.forEach(([extra, size, x, y]) => {
    const h = document.createElement('div');
    h.className = 'cehost ' + (state === 'sleep' ? 'char-sleep char-live' : state === 'live' ? 'char-live' : '') + ' ' + (extra || '');
    h.style.cssText = 'left:' + x + 'px;top:' + y + 'px;width:' + size + 'px;height:' + size + 'px';
    const s = buildAvatarCharSVG(id); h.appendChild(s); document.body.appendChild(h); sv = sv || s;
    h.getAnimations({ subtree: true }).forEach(a => { a.pause(); a.currentTime = t; });
  });
  /* the lid colour: what the closed eyes' LINES are stroked in (a path with no fill), the commonest */
  const cnt = {};
  sv.querySelectorAll('.cx-eyes-closed path').forEach(n => { const c = (n.getAttribute('stroke') || '').trim().toUpperCase(), f = (n.getAttribute('fill') || '').trim();
    if(/^#[0-9A-F]{6}$/.test(c) && (f === 'none' || f === '')) cnt[c] = (cnt[c] || 0) + 1; });
  if(!Object.keys(cnt).length) sv.querySelectorAll('.cx-eyes-closed *').forEach(n => { const c = (n.getAttribute('stroke') || '').trim().toUpperCase(); if(/^#[0-9A-F]{6}$/.test(c)) cnt[c] = (cnt[c] || 0) + 1; });
  return { lid: Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0] || null };
}"""
# A: the idle cycle on one clock; how closed the eyes are at each step
CYCLE = r"""([id, N]) => {
  document.querySelectorAll('.cehost').forEach(n => n.remove());
  const h = document.createElement('div'); h.className = 'cehost char-live'; h.style.cssText = 'left:0;top:0;width:100px;height:100px';
  const sv = buildAvatarCharSVG(id); h.appendChild(sv); document.body.appendChild(h);
  const anims = h.getAnimations({ subtree: true });
  const eyes = [...sv.querySelectorAll('.cx-eyes')];
  const onEyes = a => { const t = a.effect && a.effect.target; return !!t && (eyes.some(e => e === t || e.contains(t) || t.contains(e)) || !!(t.closest && t.closest('.cx-eyes-closed'))); };
  let P = 0;
  anims.filter(onEyes).forEach(a => { const tm = a.effect.getTiming(); const d = Number(tm.duration) || 0; P = Math.max(P, d * (String(tm.direction || '').indexOf('alternate') >= 0 ? 2 : 1)); });
  if(!P) P = 6000;
  P = Math.min(P, 20000);
  anims.forEach(a => a.pause());
  const sy = n => { const cs = getComputedStyle(n); let k = 1;
    if(cs.transform && cs.transform !== 'none'){ const m = new DOMMatrix(cs.transform); k *= Math.hypot(m.b, m.d); }
    if(cs.scale && cs.scale !== 'none'){ const sc = cs.scale.split(' ').map(Number); k *= sc.length > 1 ? sc[1] : sc[0]; } return k; };
  const inner = eyes.map(e => anims.map(a => a.effect && a.effect.target).filter(t => t && t !== e && e.contains(t)));
  const state = () => {
    let v = 1;
    eyes.forEach((e, i) => {
      let op = 1, k = 1, n = e;
      while(n && n !== h){ const cs = getComputedStyle(n); op *= +cs.opacity; if(cs.visibility === 'hidden' || cs.display === 'none') op = 0; if(n !== h && sv.contains(n)) k *= sy(n); n = n.parentNode; }
      /* an eye that blinks in a group of its own inside the eye group (each about its own middle) */
      if(inner[i].length) k *= Math.min(...inner[i].map(sy));
      /* closing is HEIGHT: a lit eye that dims or flickers (cx-ember, the Ronin's neon flick) is a light doing what it does, not an
         eye closing - unless it is put out altogether */
      v = Math.min(v, op < .02 ? 0 : k);
    });
    return v;
  };
  const out = [];
  for(let i = 0; i < N; i++){ const t = i * P / N; anims.forEach(a => { a.currentTime = t; }); out.push([+t.toFixed(1), +state().toFixed(3)]); }
  /* and the exact bottom of every cx-blink */
  anims.filter(a => a.animationName === 'cx-blink').forEach(a => {
    const tm = a.effect.getTiming(), d = Number(tm.duration) || 0, del = Number(tm.delay) || 0;
    for(let k = 0; k < 4; k++){ const t = .95 * d - del + k * d; if(t < 0 || t > P) continue; anims.forEach(b => { b.currentTime = t; }); out.push([+t.toFixed(1), +state().toFixed(3)]); }
  });
  h.remove();
  return { P, n: eyes.length, steps: out, names: [...new Set(anims.filter(onEyes).map(a => a.animationName))] };
}"""


# F: the app's own recorder makes the flip-book sheet of one character (the sheet a board row plays), as a data URL
SHEET = r"""async ([id, px]) => {
  const el = document.createElement('span'); el.className = 'char-flip'; el.dataset.flipSolo = '1'; document.body.appendChild(el);
  const sp = await Promise.race([recordCharFrames(id, px, el), new Promise(r => setTimeout(() => r(null), 240000))]);
  el.remove();
  if(!sp || !sp.url) return null;
  const blob = await (await fetch(sp.url)).blob();
  return await new Promise(r => { const fr = new FileReader(); fr.onload = () => r({ url: fr.result, cols: sp.cols, n: sp.n, px: sp.px }); fr.readAsDataURL(blob); });
}"""


def mount(pg, cid, state, t, copies):
    """copies: [[extra classes, css size]], laid out left to right and taken in ONE screenshot; returns (info, [image per copy])"""
    lay, x = [], 0
    for extra, size in copies:
        lay.append([extra, size, x, 0]); x += size + 8
    info = pg.evaluate(MOUNT, [cid, state, t, lay])
    H = max(size for _, size in copies)
    png = pg.screenshot(clip={"x": 0, "y": 0, "width": x - 8, "height": H})
    im = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.int16)
    return info, [im[0:size * 2, x0 * 2:(x0 + size) * 2] for _, size, x0, _ in lay]


def lum(a):
    return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r: continue
            sh = np.zeros_like(m)
            ys = slice(max(0, dy), m.shape[0] + min(0, dy)); yd = slice(max(0, -dy), m.shape[0] + min(0, -dy))
            xs = slice(max(0, dx), m.shape[1] + min(0, dx)); xd = slice(max(0, -dx), m.shape[1] + min(0, -dx))
            sh[yd, xd] = m[ys, xs]
            out |= sh
    return out


def components(m):
    H, W = m.shape; seen = np.zeros_like(m); comps = []
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]: continue
        q = deque([(y0, x0)]); seen[y0, x0] = True; pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; q.append((yy, xx))
        comps.append(pts)
    return comps


def eye_regions(E, B, px):
    """The eyes, by what they are: where showing the open eyes changes the bare face. One region per connected eye."""
    d = np.abs(E - B).max(axis=2) > 30
    if d.sum() == 0: return []
    md = dilate(d, max(2, px // 160))
    regs = []
    for pts in components(md):
        a = np.array(pts)
        y0, x0 = a.min(axis=0); y1, x1 = a.max(axis=0)
        sub = d[y0:y1 + 1, x0:x1 + 1]
        core = sub.sum()
        if core < (px / 480.0) ** 2 * 40: continue          # a stray antialiased speck
        # the box of the eye itself (what changed), not of the dilation that joined its pieces
        ys_, xs_ = np.nonzero(sub)
        regs.append([int(x0 + xs_.min()), int(y0 + ys_.min()), int(x0 + xs_.max()), int(y0 + ys_.max()), int(core)])
    # merge regions whose boxes overlap (an eye and its own catchlight)
    merged = True
    while merged:
        merged = False
        for i in range(len(regs)):
            for j in range(i + 1, len(regs)):
                a, b = regs[i], regs[j]
                if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                    regs[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]]
                    regs.pop(j); merged = True; break
            if merged: break
    # far smaller than the biggest is a glint, not an eye (an eye is kept down to a sixth of the biggest: the Toxic Spill's third)
    if regs:
        big = max(r[4] for r in regs)
        regs = [r for r in regs if r[4] >= big / 6.0]
    return regs


def hexrgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.int32)


def line_cols(ink, A, h, unit, T):
    """Columns crossed by a LINE: a run of ink no thicker than max(.45 of the eye's height, one drawing unit), with something that is
    not ink right above and right below it, its colour standing off both by >= T (RGB distance: a gold line on a pale face is a line
    though their luminance is close). Returns (columns, mean standing-off)."""
    thick = max(.45 * h, unit)
    A = A.astype(np.float64)
    n, cons = 0, []
    for x in range(ink.shape[1]):
        col = ink[:, x]; best = 0.0; y = 0
        while y < len(col):
            if not col[y]: y += 1; continue
            y2 = y
            while y2 < len(col) and col[y2]: y2 += 1
            if y > 0 and y2 < len(col) and (y2 - y) <= thick:
                run = A[y:y2, x].mean(axis=0); up = A[max(0, y - 3):y, x].mean(axis=0); dn = A[y2:y2 + 3, x].mean(axis=0)
                best = max(best, min(float(np.sqrt(((run - up) ** 2).sum())), float(np.sqrt(((run - dn) ** 2).sum()))))
            y = y2
        if best >= T: n += 1; cons.append(best)
    return n, (float(np.mean(cons)) if cons else 0.0)


def lid_test(C, B, reg, lid, kind, unit, T):
    """In the eye's region (and a quarter of its height above and below). Returns (share of the eye's width crossed, standing-off).
    The LID LINE: the closed frame's pixels in the lid colour make a line across the eye that the bare face does not already have
    there (a socket left empty is one thick dark run, not a line; a ring round an empty socket is on the bare face too). The same
    for a blink and for sleep: at the bottom of a blink the eye is shut, and a shut eye is its lid line."""
    x0, y0, x1, y1, _ = reg
    w = x1 - x0 + 1; h = y1 - y0 + 1
    pad = max(2, int(h * .25))
    ya, yb = max(0, y0 - pad), min(C.shape[0], y1 + pad + 1)
    c = C[ya:yb, x0:x1 + 1]; b = B[ya:yb, x0:x1 + 1]
    best = (0.0, 0.0)
    if lid is not None:
        dist = lambda a: np.sqrt(((a.astype(np.int32) - hexrgb(lid)) ** 2).sum(axis=2))
        dc, db = dist(c), dist(b)
        # in the lid colour, or (a thin line's antialiased edge, which at a 42px row is most of it) changed from the bare face and
        # moved at least 40% of the way towards the lid colour
        ink_c = (dc <= 75) | ((np.abs(c - b).max(axis=2) > 20) & (dc < .6 * db))
        nc, kc = line_cols(ink_c, c, h, unit, T)
        nb, _ = line_cols(db <= 75, b, h, unit, T)
        if nc - nb > 0: best = ((nc - nb) / float(w), kc)
    return float(best[0]), best[1]


def boot(br, cls, port, errs):
    ctx = br.new_context(viewport={"width": 1200, "height": 700}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.set_default_timeout(120000)   # a loaded machine: a screenshot can take a while
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    # the update check answers with the page's own build, so no update reloads the page under the run
    build = re.search(r'const APP_BUILD = "([^"]+)"', BODY if BODY is not None else open(os.path.join(os.path.dirname(HERE), "index.html"), encoding="utf-8").read()).group(1)
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": build, "force": False, "frameId": ""})))
    pg.add_init_script(INIT[cls])
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(4000)
    for _ in range(30):
        if pg.evaluate("()=>typeof buildAvatarCharSVG === 'function' && typeof AVATAR_CHARACTERS === 'object'"): break
        pg.wait_for_timeout(500)
    return ctx, pg, pg.evaluate(SETUP)


def run_class(br, cls, port, shots_out):
    errs = []
    ctx, pg, info = boot(br, cls, port, errs)
    chk("%s: the page is that class (%s)" % (cls, info["cls"]), (info["cls"] or "academy") == cls, info["cls"])
    ids = [i for i in info["ids"] if not ONLY or i in ONLY]
    print("== %s: %d characters" % (cls, len(ids)), flush=True)
    px = BIG * 2; spx = SMALL * 2
    results = {}
    queue = list(ids); tries = {}
    while queue:
        cid = queue.pop(0)
        try:
            one(pg, cls, cid, info, results, shots_out, px, spx)
        except Exception as e:
            # a busy machine can take the renderer down (out of memory): a fresh page, and that character once more
            tries[cid] = tries.get(cid, 0) + 1
            print("  !! %s %s: %s - a fresh page%s" % (cls, cid, str(e).split("\n")[0][:120], "" if tries[cid] < 3 else ", giving up"), flush=True)
            try: ctx.close()
            except Exception: pass
            ctx, pg, info = boot(br, cls, port, errs)
            if tries[cid] < 3: queue.insert(0, cid)
            else: chk("%s %s: drawn and measured" % (cls, cid), False, str(e)[:200])
    flip(pg, cls, info, shots_out, spx)
    pg.evaluate("()=>document.querySelectorAll('.cehost').forEach(n => n.remove())")
    chk("%s: no page error (%s)" % (cls, errs[:2]), not errs, errs)
    ver = info["ver"]
    ctx.close()
    return results, ver


def one(pg, cls, cid, info, results, shots_out, px, spx):
    if True:
        name = "%s %s (%s, %s)" % (cls, cid, info["names"][cid], info["kinds"][cid])
        # the still drawing: its eyes, open
        _, (O, Eo, Bo) = mount(pg, cid, "", 0, [["", BIG], ["ce-eyes-on ce-shut-off", BIG], ["ce-eyes-off ce-shut-off", BIG]])
        if shots_out: Image.fromarray(O.astype(np.uint8)).save(os.path.join(shots_out, "%s-%s-open.png" % (cls, cid)))
        still = eye_regions(Eo, Bo, px)
        cyc = pg.evaluate(CYCLE, [cid, 120])
        if cyc["n"] == 0 or not still:
            print("  .. %s draws no eyes that close (an empty eye group: a visor, a fish's painted eyes): nothing to close" % name, flush=True)
            results[cid] = {"noeyes": True}
            return
        still_area = sum(r[4] for r in still)
        # each closing: a run of steps under .5, shot at its deepest; the deepest closing, and a second if the cycle closes the eyes
        # again some other way (a flicker, a squint) - not the same blink a cycle later
        closed, run = [], []
        for t, v in sorted(cyc["steps"]):
            if v < .5: run.append((v, t))
            elif run: closed.append(min(run)); run = []
        if run: closed.append(min(run))
        keep, P = [], cyc["P"]
        for v, t in sorted(closed):
            if all(min(abs(t - t2) % P, P - abs(t - t2) % P) > 150 for _, t2 in keep): keep.append((v, t))
        rec = {"cycle_P": P, "anims": cyc["names"], "closings": [[t, v] for v, t in keep[:2]], "frames": []}
        frames = [("blink", t, v) for v, t in keep[:2]] + [("sleep", 0, 0)]
        for kind, t, v in frames:
            state = "live" if kind == "blink" else "sleep"
            copies = [["", BIG], ["ce-eyes-on ce-shut-off" + (" ce-eyes-still" if kind == "blink" else ""), BIG], ["ce-eyes-off ce-shut-off", BIG]]
            if kind == "sleep":
                copies += [["", SMALL], ["ce-eyes-on ce-shut-off", SMALL], ["ce-eyes-off ce-shut-off", SMALL]]
            m, ims = mount(pg, cid, state, t, copies)
            C, E, Bf = ims[0], ims[1], ims[2]
            regs = eye_regions(E, Bf, px)
            if shots_out and (kind == "sleep" or len([f for f in rec["frames"] if f["kind"] == "blink"]) == 0):
                Image.fromarray(C.astype(np.uint8)).save(os.path.join(shots_out, "%s-%s-%s.png" % (cls, cid, kind)))
            # a sleeping pose that pulls something down over the eyes (the Sheriff tips his hat brim over them) leaves little of the
            # eyes in view: covered, not missing, and not asked for a lid
            seen = sum(r[4] for r in regs) / float(still_area)
            if kind == "sleep" and seen < .45:
                print("  .. %s, asleep: its sleeping pose covers its eyes (%.0f%% of them in view): not asked for a lid" % (name, seen * 100), flush=True)
                rec["frames"].append({"kind": kind, "covered": round(seen, 2)})
                continue
            per = []
            for reg in regs:
                x0, y0, x1, y1, _ = reg
                # an eye still open at this moment (a wink closes one; the other is tested at its own closing) is not a closed eye
                if kind == "blink" and (np.abs(C[y0:y1 + 1, x0:x1 + 1] - E[y0:y1 + 1, x0:x1 + 1]).max(axis=2) > 30).mean() < .1:
                    per.append({"box": reg[:4], "open": True}); continue
                cover, contrast = lid_test(C, Bf, reg, m["lid"], kind, px / 34.0, 40)
                per.append({"box": reg[:4], "cover": round(cover, 2), "contrast": round(contrast, 1)})
            shut = [p for p in per if not p.get("open")]
            good = bool(shut) and all(p["cover"] >= .4 and p["contrast"] >= 40 for p in shut)
            rec["frames"].append({"kind": kind, "t": t, "v": v, "lid": m["lid"], "eyes": per, "ok": good})
            label = "%s at %.0fms (eyes at %.2f)" % (kind, t, v) if kind == "blink" else "asleep"
            chk("%s, %s: every shut eye (%d of %d) shows its lid line, in its lid colour %s" % (name, label, len(shut), len(regs), m["lid"]), good, per)
            if kind == "sleep":
                # C: asleep at a rankings row
                Cs, Es, Bs = ims[3], ims[4], ims[5]
                if shots_out: Image.fromarray(Cs.astype(np.uint8)).save(os.path.join(shots_out, "%s-%s-sleep42.png" % (cls, cid)))
                regs = eye_regions(Es, Bs, spx)
                per = []
                for reg in regs:
                    cover, contrast = lid_test(Cs, Bs, reg, m["lid"], "sleep", spx / 34.0, 28)
                    per.append({"box": reg[:4], "cover": round(cover, 2), "contrast": round(contrast, 1)})
                good = bool(regs) and all(p["cover"] >= .35 and p["contrast"] >= 28 for p in per)
                chk("%s, asleep at a 42px row: every eye (%d) still shows its lid line" % (name, len(regs)), good, per)
                rec["small"] = per
        results[cid] = rec


def flip(pg, cls, info, shots_out, spx):
    # F: the flip-book a board row plays, recorded by the app's own recorder at a 42px row's size: its frame at the bottom of the blink
    # (the frame whose eyes differ most from the sheet's usual frame) shows the lid line in every eye
    for cid in FLIP.get(cls, []):
        if ONLY and cid not in ONLY: continue
        name = "%s %s (%s)" % (cls, cid, info["names"].get(cid, cid))
        m, (Es, Bs) = mount(pg, cid, "live", 0, [["ce-eyes-on ce-shut-off ce-eyes-still", SMALL], ["ce-eyes-off ce-shut-off", SMALL]])
        regs = eye_regions(Es, Bs, spx)
        pg.evaluate("()=>document.querySelectorAll('.cehost').forEach(n => n.remove())")
        sh = pg.evaluate(SHEET, [cid, spx])
        if not sh:
            chk("F. %s: the app records its flip-book" % name, False, "no sheet"); continue
        im = Image.open(io.BytesIO(base64.b64decode(sh["url"].split(",", 1)[1]))).convert("RGBA")
        bg = Image.new("RGBA", im.size, (0x1E, 0x20, 0x26, 255)); bg.alpha_composite(im)
        A = np.asarray(bg.convert("RGB")).astype(np.int16)
        p, cols = sh["px"], sh["cols"]
        frames = [A[(f // cols) * p:(f // cols + 1) * p, (f % cols) * p:(f % cols + 1) * p] for f in range(sh["n"])]
        usual = np.median(np.stack(frames), axis=0).astype(np.int16)
        def eyediff(fr):
            return max(float(np.abs(fr[r[1]:r[3] + 1, r[0]:r[2] + 1] - usual[r[1]:r[3] + 1, r[0]:r[2] + 1]).mean()) for r in regs) if regs else 0.0
        scores = [eyediff(fr) for fr in frames]
        fb = int(np.argmax(scores))
        per = []
        for reg in regs:
            cover, contrast = lid_test(frames[fb], Bs, reg, m["lid"], "sleep", p / 34.0, 28)
            per.append({"box": reg[:4], "cover": round(cover, 2), "contrast": round(contrast, 1)})
        if SHOTS:
            Image.fromarray(np.concatenate([usual, frames[fb]], axis=1).astype(np.uint8)).save(os.path.join(SHOTS, "%s-%s-flipbook-blink.png" % (cls, cid)))
        chk("F. %s: its flip-book (%dpx, recorded by the app) closes its eyes (frame %d, change %.1f) and shows the lid line in every eye (%d) there"
            % (name, p, fb, scores[fb], len(regs)), bool(regs) and scores[fb] > 8 and all(q["cover"] >= .35 and q["contrast"] >= 28 for q in per), per)


if __name__ == "__main__":
    if SHOTS: os.makedirs(SHOTS, exist_ok=True)
    srv, port = rc["serve"]()
    allres, vers = {}, set()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=rc["CHROME"])
        try:
            for cls in CLASSES:
                allres[cls], ver = run_class(br, cls, port, SHOTS)
                vers.add(ver)
        finally:
            br.close()
    srv.shutdown()
    chk("D. the flip-books re-record: CHAR_ANIM_VER is %s, not %s (384.95's)" % (sorted(map(str, vers)), PREV_VER), PREV_VER not in vers and None not in vers, sorted(map(str, vers)))
    if "--json" in sys.argv:
        with open(sys.argv[sys.argv.index("--json") + 1], "w") as f: json.dump(allres, f, indent=1)
    print("\n%s  (%d failure(s))" % ("ALL PASS" if ok else "FAILED", len(fails)))
    for f in fails[:60]: print("   - " + f)
    sys.exit(0 if ok else 1)
