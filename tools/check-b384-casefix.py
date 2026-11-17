"""Build 384.133 (casefix): the badge case's corners, and the open lid's reflection.
Madison, on the academy cutscene's open case (iPhone 17 Pro Max, 16 of 24 found): "Why do the top edges look so sharp? And the
bottom edges? They can be but they just look off. Also, the color reflecting to the back of these case, why does it not match
with what's actually there in the case? Ensure that's good to go."

Read off the page, both classes (the academy's 6x4 case, Fire Code's 58), iPhone 17 Pro Max 440x956 at 2x:

(A) THE CUTSCENE CASE'S OUTER CORNERS, drawn. The open case of the still scene (Reduce motion: the open pose, nothing moving) is
    shot on a flat key colour (the scene's dim, glow and words hidden) and its silhouette read: at each of its four outer corners
    (the open lid's top two, the base's foot two) how far in from the side the outermost line starts, against the furthest-out
    the side reaches just below it (a square corner, or a square wall sticking out under a rounded top: about nothing; a round
    corner of radius r: nearly r). Asserted: (A1) every corner is rounded - at least half the corner the Badges screen's case draws, measured the
    same way off that page and scaled to this case's width; (A2) top and bottom agree (the smaller of the two at least .6 of the
    larger), so the lid's free edge and the base's foot are one case.
(B) THE FLAT CASES (the Badges screen's tray, the Profile's shut case - or, since profilerows2, option a's small shut case on the Profile's card; options b and c draw no case there): every part that paints something inside the case lies
    inside the case's own rounded outline at every corner (its used corner radii, after the browser scales a radius down to fit a
    short box) - no square or tighter corner, no seam line, poking out past the case's curve; and the outline's top corners equal
    its bottom ones.
(C) THE LID'S REFLECTION COMES FROM THE FOUND BADGES. Two different sets of found badges, one per column in a different row each
    (and none in some columns), plus the scene's own new badge, are played as the still scene; the lid is shot with its light
    layers on and off and the difference read per column of the tray (each column's slots mapped onto the lid): (C1) every
    column with a found badge in it is lit, at least .4 of the brightest (each read against its badge's own brightness over the
    cushion: a dark enamel gives less light) - wherever in the column the badge is, and including the badge seated in this scene; (C2) a column with nothing found stays dark (at most .35 of the faintest lit one); (C3) each lit
    column's light is its badge's own colour (hue within 40 degrees of badgeThemeFor(u).g, where that colour has a hue);
    (C4) the two sets light different columns - the light follows the badges, not the case; (C5) nothing found: no colour.
(D) no page errors.

Run:  python3 tools/check-b384-casefix.py   (--against OLD/index.html must FAIL A, B and C; ONLY=A,C runs those)"""
import json, os, re, sys, math, io, functools, http.server, socket, threading, glob
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else open(ROOT + "/index.html", encoding="utf-8").read()
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}
def want(n): return not ONLY or n in ONLY
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
_m = re.search(r'const APP_BUILD = "([^"]+)"', BODY)
SERVED = _m.group(1) if _m else ""
SEED = {"onboardingComplete": True, "firstName": "Maddog", "avatarChar": "ninja", "publicId": "xph5b57jbp5a", "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30,
                     "longestStreak": 20, "currentStreak": 3}}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted"]
def init_js(cls):
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    return s + " }catch(e){} })()"
# what would land over what is measured (an owed unlock card, a tour, a banner)
QUIET = ".rs-spot,.daily-alert,#tour-overlay,.update-banner,.toast{display:none!important}"
def page(br, cls, reduce=False):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2, has_touch=True, reduced_motion="reduce" if reduce else "no-preference")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js(cls))
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % SERVED))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.add_style_tag(content=QUIET)
    return ctx, pg, errs
def shot(pg, clip=None):
    return np.asarray(Image.open(io.BytesIO(pg.screenshot(clip=clip) if clip else pg.screenshot())).convert("RGB")).astype(np.int32)

# found = {index in the case: True}; the new one (the scene's) given separately
SET_FOUND = r"""([found, fresh]) => { const all = badgeCaseUnits(badgeCaseOf(unitsInTeachingOrder()[0])); store.unitPerfects = {};
  found.forEach(i => { const u = all[i]; if(u) store.unitPerfects[u] = badgeThresholdFor(u); });
  if(fresh != null && all[fresh]) store.unitPerfects[all[fresh]] = badgeThresholdFor(all[fresh]);
  saveStore(); const g = badgeCaseGrid(all.length); return { n: all.length, cols: g.cols, rows: g.rows,
    col: all.map(u => ((badgeThemeFor(u) || {}).g) || null), fresh: fresh != null ? all[fresh] : null }; }"""
# the still scene, held up (its own end, a timer of BC_STILL_MS, is not set: a loaded machine reached it mid-measure) and shown in
# its end state at once (no fades: what is measured is where the light settles)
PLAY_STILL = r"""(u) => { document.querySelectorAll('.bc-scene').forEach(n => n.remove()); showHome(); window.__bcDone = 0;
  if(!document.getElementById('casefix-still')){ const st = document.createElement('style'); st.id = 'casefix-still'; st.textContent = '.bc-scene, .bc-scene *{ transition:none !important; }'; document.body.appendChild(st); }
  const st0 = window.setTimeout; window.setTimeout = (f, ms, ...a) => (ms >= 2500 ? 0 : st0(f, ms, ...a));
  try{ playBadgeCaseScene([u], () => { window.__bcDone++; }, [], {}); } finally { window.setTimeout = st0; }
  return !!document.querySelector('.bc-scene.bc-still'); }"""
KEY = (255, 0, 255)
KEY_CSS = (".bc-scene{ background:rgb(255,0,255) !important; } .bc-scene > :not(.bc-stage){ visibility:hidden !important; }"
           " .bc-floor{ visibility:hidden !important; }")

def corner_r(mask, side, end):
    """how far in from the case's side the outermost line of the silhouette starts at one outer corner (a square corner: none;
    a corner of radius r: nearly r) - against the furthest-out the side reaches in the next 24% of the case's width, so a slanted
    side (the camera's perspective) or a wider part just below the corner (a square wall under a rounded top) counts as square"""
    ys, xs = np.nonzero(mask)
    x0, x1 = xs.min(), xs.max(); W = x1 - x0 + 1
    S = max(6, int(.12 * W))
    band = mask[:, x0:x0 + S] if side == "l" else mask[:, x1 - S + 1:x1 + 1][:, ::-1]
    rows = np.nonzero(band.any(axis=1))[0]
    y_top, y_bot = rows.min(), rows.max()
    def xl(y):
        r = np.nonzero(band[y])[0]
        return r.min() if len(r) else S
    rr = range(y_top, min(y_top + 2 * S, band.shape[0])) if end == "top" else range(y_bot, max(y_bot - 2 * S, -1), -1)
    prof = [xl(y) for y in rr]
    return float(prof[1] - min(prof))

def badges_shell_ratio(pg):
    """the Badges screen's case: its outer corner radius as a share of its width, read off its pixels on the key colour"""
    pg.evaluate("()=>{ store.unitPerfects = {}; saveStore(); showProfile('badges'); }"); pg.wait_for_timeout(2500)
    r = pg.evaluate("""()=>{ const s = document.querySelector('.badges-tab .bcs-shell'); if(!s) return null; s.scrollIntoView({ block: s.getBoundingClientRect().height > innerHeight * .7 ? 'start' : 'center', behavior: 'instant' });
      const st = document.createElement('style'); st.textContent = 'html, body, #stage, #stage *:not(.bcs):not(.bcs *){ background:rgb(255,0,255) !important; box-shadow:none !important; } .bcs-shell{ box-shadow:none !important; }';
      document.body.appendChild(st); const b = s.getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height }; }""")
    if not r: return None
    pg.wait_for_timeout(600)
    r = pg.evaluate("()=>{ const b = document.querySelector('.badges-tab .bcs-shell').getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height }; }")
    img = shot(pg, {"x": r["x"] - 6, "y": r["y"] - 6, "width": r["w"] + 12, "height": r["h"] + 12})
    m = np.abs(img - np.array(KEY)).sum(axis=2) > 90
    # its top corners (a tall case - Fire Code's 58 - runs off the screen at the foot)
    rs = [corner_r(m, s_, "top") for s_ in "lr"]
    ys, xs = np.nonzero(m)
    return min(rs) / (xs.max() - xs.min() + 1), rs

INSIDE = r"""(sel) => {
  /* every element in the case that paints something lies inside the case's rounded outline at its corners */
  const box = document.querySelector(sel); if(!box) return { missing: sel };
  const used = (el) => { const cs = getComputedStyle(el), b = el.getBoundingClientRect();
    const rad = k => { const v = cs[k].split(' ').map(parseFloat); return [v[0] || 0, (v.length > 1 ? v[1] : v[0]) || 0]; };
    let tl = rad('borderTopLeftRadius'), tr = rad('borderTopRightRadius'), br = rad('borderBottomRightRadius'), bl = rad('borderBottomLeftRadius');
    const f = Math.min(1, b.width / Math.max(1e-6, tl[0] + tr[0]), b.width / Math.max(1e-6, bl[0] + br[0]), b.height / Math.max(1e-6, tl[1] + bl[1]), b.height / Math.max(1e-6, tr[1] + br[1]));
    [tl, tr, br, bl].forEach(r => { r[0] *= f; r[1] *= f; });
    return { b, tl, tr, br, bl }; };
  const O = used(box);
  const inO = (x, y) => { const b = O.b; if(x < b.left - .5 || x > b.right + .5 || y < b.top - .5 || y > b.bottom + .5) return false;
    const c = [[O.tl, b.left + O.tl[0], b.top + O.tl[1], x < b.left + O.tl[0] && y < b.top + O.tl[1]],
               [O.tr, b.right - O.tr[0], b.top + O.tr[1], x > b.right - O.tr[0] && y < b.top + O.tr[1]],
               [O.br, b.right - O.br[0], b.bottom - O.br[1], x > b.right - O.br[0] && y > b.bottom - O.br[1]],
               [O.bl, b.left + O.bl[0], b.bottom - O.bl[1], x < b.left + O.bl[0] && y > b.bottom - O.bl[1]]];
    for(const [r, cx, cy, inC] of c){ if(inC && r[0] > 0 && r[1] > 0){ const dx = (x - cx) / r[0], dy = (y - cy) / r[1]; if(dx * dx + dy * dy > 1 + 2 / Math.min(r[0], r[1])) return false; } }
    return true; };
  const paints = el => { const cs = getComputedStyle(el); if(cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) return false;
    const bgc = cs.backgroundColor; const alpha = /rgba?\(([^)]+)\)/.exec(bgc); const a = alpha ? (alpha[1].split(',')[3] === undefined ? 1 : +alpha[1].split(',')[3]) : 0;
    const img = cs.backgroundImage && cs.backgroundImage !== 'none' && !/^linear-gradient\((rgba\(0, 0, 0, 0\)|transparent), (rgba\(0, 0, 0, 0\)|transparent)\)$/.test(cs.backgroundImage);
    const bw = ['Top', 'Right', 'Bottom', 'Left'].some(s => parseFloat(cs['border' + s + 'Width']) > 0 && !/rgba\(.*, 0\)$/.test(cs['border' + s + 'Color']) && cs['border' + s + 'Style'] !== 'none');
    return a > 0.01 || img || bw; };
  const bad = [];
  box.querySelectorAll('*').forEach(el => {
    if(!paints(el)) return;
    const U = used(el), b = U.b; if(b.width < 1 || b.height < 1) return;
    /* only parts that reach a corner region of the case */
    const R = Math.max(O.tl[0], O.tr[0], O.bl[0], O.br[0]);
    const near = (b.left < O.b.left + R || b.right > O.b.right - R) && (b.top < O.b.top + R || b.bottom > O.b.bottom - R);
    if(!near) return;
    /* points along its own outline at each corner (its own radii) */
    const pts = [];
    const arc = (cx, cy, rx, ry, a0) => { for(let k = 0; k <= 8; k++){ const a = a0 + k / 8 * Math.PI / 2; pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); } };
    arc(b.left + U.tl[0], b.top + U.tl[1], U.tl[0], U.tl[1], Math.PI);
    arc(b.right - U.tr[0], b.top + U.tr[1], U.tr[0], U.tr[1], 1.5 * Math.PI);
    arc(b.right - U.br[0], b.bottom - U.br[1], U.br[0], U.br[1], 0);
    arc(b.left + U.bl[0], b.bottom - U.bl[1], U.bl[0], U.bl[1], .5 * Math.PI);
    const out = pts.filter(p => !inO(p[0], p[1]));
    if(out.length) bad.push((el.className && el.className.baseVal === undefined ? el.className : el.tagName) + ' ' + out.length + ' pts, e.g. ' + out[0].map(v => v.toFixed(1)).join(','));
  });
  return { bad, outer: { tl: O.tl, tr: O.tr, br: O.br, bl: O.bl, w: O.b.width } };
}"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    errs_all = []
    for cls in ("academy", "ifc"):
        label = "the academy" if cls == "academy" else "Fire Code"
        # ---------------------------------------------------------------- (A) the cutscene's outer corners
        if want("A"):
            ctx, pg, errs = page(br, cls, reduce=False)
            ref = badges_shell_ratio(pg)
            ctx.close(); errs_all += errs
            ctx, pg, errs = page(br, cls, reduce=True)
            info = pg.evaluate(SET_FOUND, [[0, 1, 4, 7, 9, 12], 3])
            pg.evaluate(PLAY_STILL, info["fresh"]); pg.wait_for_timeout(1300)
            pg.add_style_tag(content=KEY_CSS); pg.wait_for_timeout(300)
            img = shot(pg)
            m = np.abs(img - np.array(KEY)).sum(axis=2) > 90
            rs = {s_ + "-" + e: corner_r(m, s_, e) for s_ in "lr" for e in ("top", "bottom")}
            ys, xs = np.nonzero(m); W = xs.max() - xs.min() + 1
            need = .5 * ref[0] * W if ref else None
            chk("(A1) %s, the cutscene's open case: all four outer corners rounded - each at least half the Badges screen's corner at this width "
                "(measured radii px@2x %s; need >= %.1f; Badges screen ratio %s)" % (label, {k: round(v, 1) for k, v in rs.items()}, need or -1, ref and round(ref[0], 4)),
                ref is not None and min(rs.values()) >= need, (rs, ref))
            top = (rs["l-top"] + rs["r-top"]) / 2; bot = (rs["l-bottom"] + rs["r-bottom"]) / 2
            chk("(A2) %s: the lid's top corners and the base's foot agree (top %.1f, bottom %.1f, ratio %.2f >= .6)" % (label, top, bot, min(top, bot) / max(top, bot, 1e-6)),
                min(top, bot) / max(top, bot, 1e-6) >= .6, rs)
            errs_all += errs; ctx.close()
        # ---------------------------------------------------------------- (B) the flat cases
        if want("B"):
            ctx, pg, errs = page(br, cls)
            pg.evaluate(SET_FOUND, [[0, 1, 4, 7, 9, 12], None])
            pg.evaluate("()=>showProfile('badges')"); pg.wait_for_timeout(2500)
            r = pg.evaluate(INSIDE, ".badges-tab .bcs-shell")
            o = r.get("outer", {})
            chk("(B) %s, the Badges screen's case: every painted part inside its rounded outline at the corners, and its top corners equal its bottom ones (%s)" % (label, o),
                not r.get("missing") and not r["bad"] and o["tl"] == o["bl"] and o["tr"] == o["br"], r)
            if cls == "academy":
                # (profilerows2) Profile's case is whatever Profile draws: the shut case (.pf-case-closed, the build-319 drawing), or since
                # profilerows2 a Delta card whose picture depends on the option (?pfbadge=, html[data-pfrow-badge]): option a draws a small
                # shut case (.pfr-mc: handle, lid, front, latches) and is measured the same way; options b (a ring) and c (a coin) draw no
                # case at all, so there is no case outline to measure on Profile and (B) is the Badges tray alone - said, not skipped quietly.
                pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(2500)
                kind = pg.evaluate("""()=>document.querySelector('#stage .pf-case-closed .pf-ccase') ? 'shut'
                    : document.querySelector('#stage .pf-case.pfr-case') ? (['a','b','c'].find(o => document.querySelector('#stage .pfr-bc-' + o)) || '?') : 'none'""")
                if kind == "shut":
                    r = pg.evaluate(INSIDE, ".pf-case-closed .pf-ccase")
                    o = r.get("outer", {})
                    chk("(B) %s, the Profile's shut case: every painted part (lid, seam, front) inside the card's rounded outline at its corners, top corners equal to bottom (%s)" % (label, o),
                        not r.get("missing") and not r["bad"] and o["tl"] == o["bl"] and o["tr"] == o["br"], r)
                else:
                    chk("(B) %s, Profile shows option %s of the case row: %s" % (label, kind, "a small shut case (measured below, as option a)" if kind == "a" else
                        "no shut case on Profile (a ring of ticks / a coin and a segment bar) - nothing case-shaped to measure there, so (B) on Profile is option a's drawing only"),
                        kind in ("a", "b", "c"), kind)
                    pg.evaluate("()=>{ document.documentElement.setAttribute('data-pfrow-badge','a'); showProfile(); }"); pg.wait_for_timeout(2500)
                    r = pg.evaluate(INSIDE, "#stage .pfr-bc-a .pfr-mc")
                    o = r.get("outer", {})
                    chk("(B) %s, Profile's option a, the small shut case: every painted part (lid, front, fill, latches) inside its rounded outline at its corners, top corners equal to bottom (%s)" % (label, o),
                        not r.get("missing") and not r["bad"] and o.get("tl") == o.get("bl") and o.get("tr") == o.get("br") and (o.get("tl") or [0])[0] > 0, r)
            errs_all += errs; ctx.close()
        # ---------------------------------------------------------------- (C) the reflection
        if want("C"):
            ctx, pg, errs = page(br, cls, reduce=True)
            g = pg.evaluate(SET_FOUND, [[], None])
            cols, rows = g["cols"], g["rows"]
            def one_set(pick, fresh_col):
                """pick: {column: row}; the scene's new badge in fresh_col (its own row)"""
                found = [r_ * cols + c for c, r_ in pick.items() if r_ * cols + c < g["n"]]
                fresh = None
                if fresh_col is not None:
                    fr = (rows - 1) if fresh_col % 2 else 1
                    while fr * cols + fresh_col >= g["n"]: fr -= 1
                    fresh = fr * cols + fresh_col
                info = pg.evaluate(SET_FOUND, [found, fresh])
                ok_play = pg.evaluate(PLAY_STILL, info["fresh"]) if info["fresh"] else pg.evaluate(PLAY_STILL, badgeless[0])
                for _ in range(20):
                    if pg.evaluate("()=>!!document.querySelector('.bc-scene .bc-case.bc-open')"): break
                    pg.wait_for_timeout(100)
                # the light comes up by opacity: wait until every light layer on the lid has settled
                last = None
                for _ in range(40):
                    pg.wait_for_timeout(200)
                    now = pg.evaluate("()=>[...document.querySelectorAll('.bc-scene .bc-lidlight')].map(e => getComputedStyle(e).opacity).join(',')")
                    if now == last: break
                    last = now
                geo = pg.evaluate("""()=>{ const q = s => document.querySelector(s); const lid = q('.bc-scene .bc-lid-in'), tray = q('.bc-scene .bc-tray');
                  const slots = [...document.querySelectorAll('.bc-scene .bc-slot')].map(s => { const b = s.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; });
                  const r = e => { const b = e.getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height }; };
                  /* where each column of the tray lands on the (foreshortened) lid, row by row: probes in the lid's own plane */
                  const tb = tray.getBoundingClientRect(), cols = %d, rows = %d, probe = [];
                  for(let c = 0; c < cols; c++){ const xs = []; for(let r = 0; r < rows; r++){ const i = r * cols + c; if(slots[i]) xs.push(slots[i][0]); }
                    const fx = (xs.reduce((a, b) => a + b, 0) / xs.length - tb.left) / tb.width; const col = [];
                    for(let k = 0; k < 12; k++){ const p = document.createElement('i'); p.style.cssText = 'position:absolute;width:0;height:0;left:' + (fx * 100) + '%%;top:' + ((k + .5) / 12 * 100) + '%%';
                      lid.appendChild(p); const b = p.getBoundingClientRect(); col.push([b.left, b.top]); p.remove(); }
                    probe.push(col); }
                  return { lid: r(lid), tray: r(tray), slots, probe }; }""" % (cols, rows))
                L = geo["lid"]; clip = {"x": L["x"], "y": L["y"], "width": L["w"], "height": L["h"]}
                HIDE = "(h)=>{ document.querySelectorAll('.bc-scene .bc-lidlight').forEach(e => h ? e.style.setProperty('visibility', 'hidden', 'important') : e.style.removeProperty('visibility')); }"
                # the lid with its light and without, and with it again: the two lit shots must agree (nothing else moved between)
                for _ in range(6):
                    on = shot(pg, clip)
                    pg.evaluate(HIDE, True); pg.wait_for_timeout(150)
                    off = shot(pg, clip)
                    pg.evaluate(HIDE, False); pg.wait_for_timeout(150)
                    on2 = shot(pg, clip)
                    if float(np.abs(on - on2).mean()) < .5: break
                    pg.wait_for_timeout(400)
                pg.evaluate("()=>{ document.querySelectorAll('.bc-scene').forEach(n => n.remove()); }")
                if os.environ.get("CASEFIX_DEBUG"):
                    Image.fromarray(np.concatenate([on, off], axis=1).astype(np.uint8)).save(os.environ["CASEFIX_DEBUG"] + "-%s-%s.png" % (cls, fresh_col))
                d = np.clip(on - off, 0, None).astype(float)
                Hh, Ww = d.shape[:2]; sc = Ww / L["w"]
                # each column of the tray, followed up the lid through the probes: a window round it on every band of the lid
                P = geo["probe"]
                per = []
                for c in range(cols):
                    tot = np.zeros(3); E = 0.0; n = 0
                    for k in range(12):
                        px, py = (P[c][k][0] - L["x"]) * sc, (P[c][k][1] - L["y"]) * sc
                        nb = [abs(P[c2][k][0] - P[c][k][0]) for c2 in (c - 1, c + 1) if 0 <= c2 < cols]
                        hw = .4 * min(nb) * sc
                        bh = Hh / 12 / 2
                        y0, y1 = int(max(0, py - bh)), int(min(Hh, py + bh)); x0, x1 = int(max(0, px - hw)), int(min(Ww, px + hw))
                        if y1 <= y0 or x1 <= x0: continue
                        seg = d[y0:y1, x0:x1, :]; e = seg.sum(axis=2)
                        E += float(e.sum()); n += e.size; tot += (seg * e[..., None]).sum(axis=(0, 1))
                    per.append((E / max(n, 1), tot / E if E > 0 else np.zeros(3)))
                lit = {c: (r_ * cols + c) for c, r_ in pick.items() if r_ * cols + c < g["n"]}
                if fresh is not None: lit[fresh_col] = fresh
                return per, lit, info, float(off.reshape(-1, 3).mean(axis=0).sum())
            def hue(rgb):
                r_, g_, b_ = [v / 255 for v in rgb]; mx, mn = max(r_, g_, b_), min(r_, g_, b_)
                if mx - mn < .06: return None
                if mx == r_: h = (g_ - b_) / (mx - mn) % 6
                elif mx == g_: h = (b_ - r_) / (mx - mn) + 2
                else: h = (r_ - g_) / (mx - mn) + 4
                return h * 60
            def hexrgb(h):
                h = h.strip()
                if h.startswith("#"): return [int(h[i:i + 2], 16) for i in (1, 3, 5)]
                return [int(float(v)) for v in re.findall(r"[\d.]+", h)[:3]]
            badgeless = [pg.evaluate("()=>badgeCaseUnits(badgeCaseOf(unitsInTeachingOrder()[0]))[0]")]
            # two sets: one badge per chosen column, each in a different row; some columns empty; the scene's new badge in another column
            setA = {c: (c * 2 + 1) % rows for c in range(cols) if c % 3 != 2 and c != 3}
            setB = {c: (c * 3) % rows for c in range(cols) if c % 3 != 0 and c != 4}
            res = {}
            for nm, pick, fc in (("first", setA, 3), ("second", setB, 4)):
                per, lit, info, bgsum = one_set(pick, fc)
                res[nm] = (per, lit)
                # a dark enamel gives less light than a bright one: each lit column's light is read against its badge's own brightness
                Es = [p[0] for p in per]
                lum = {c: max(.08, (sum(hexrgb(info["col"][i])) - bgsum) / 765) for c, i in lit.items()}
                lit_E = {c: Es[c] / lum[c] for c in lit}; mx = max(lit_E.values()) or 1
                dark_E = {c: Es[c] for c in range(cols) if c not in lit}
                chk("(C1) %s, the %s set (found in columns %s, the new one in column %d): every column with a found badge is lit, >= .4 of the brightest (%s)"
                    % (label, nm, sorted(lit), fc, {c: round(v / mx, 2) for c, v in lit_E.items()}),
                    all(v >= .4 * mx for v in lit_E.values()), lit_E)
                mn_lit = min(Es[c] for c in lit) if lit else 0
                chk("(C2) %s, the %s set: a column with nothing found stays dark, <= .35 of the faintest lit one (%s)" % (label, nm, {c: round(v / max(mn_lit, 1e-6), 2) for c, v in dark_E.items()}),
                    all(v <= .35 * mn_lit for v in dark_E.values()) and mn_lit > 0, (dark_E, mn_lit))
                bad = []
                for c, i in lit.items():
                    want_h = hue(hexrgb(info["col"][i])); got_h = hue(per[c][1] / max(per[c][1].max(), 1e-6) * 255)
                    if want_h is None: continue
                    dh = None if got_h is None else min(abs(want_h - got_h), 360 - abs(want_h - got_h))
                    if dh is None or dh > 40: bad.append((c, info["col"][i], None if got_h is None else round(got_h), dh and round(dh)))
                chk("(C3) %s, the %s set: each lit column's light is its badge's own colour (hue within 40 degrees)" % (label, nm), not bad, bad)
            la = set(res["first"][1]); lb = set(res["second"][1])
            pa = [res["first"][0][c][0] for c in range(cols)]; pb = [res["second"][0][c][0] for c in range(cols)]
            moved = [c for c in range(cols) if (c in la) != (c in lb)]
            chk("(C4) %s: the two sets light different columns - the light follows the badges (columns that change: %s)" % (label, moved),
                bool(moved) and all((pa[c] > pb[c]) == (c in la) for c in moved), (pa, pb, sorted(la), sorted(lb)))
            # nothing found but the scene's own badge is not played: an empty case, the still scene for a badge then taken back out
            info = pg.evaluate(SET_FOUND, [[], None])
            bgs = pg.evaluate("""()=>{ const all = badgeCaseUnits(badgeCaseOf(unitsInTeachingOrder()[0]));
              const C = buildBadgeCase3D(all, () => false);
              return typeof bcLidReflection === 'function' ? bcLidReflection(all, () => false, C.grid) : bcLeakLayers(all, () => false, { grid: C.grid, mode: 'back', at: 104, w: 30, h: 34 }); }""")
            cols_in = re.findall(r"#[0-9A-Fa-f]{6}|rgba?\([^)]*\)", bgs)
            def chroma(c):
                v = hexrgb(c); return max(v) - min(v)
            chk("(C5) %s: nothing found, the lid's reflection has no colour (%r)" % (label, bgs[:120]), bgs.strip() in ("none", "") or all(chroma(c) < 12 for c in cols_in), bgs[:300])
            errs_all += errs; ctx.close()
    chk("(D) no page errors", not errs_all, errs_all[:4])
    br.close()
sys.exit(0 if ok else 1)
