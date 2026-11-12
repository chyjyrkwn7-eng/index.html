#!/usr/bin/env python3
"""Contact sheet of every Fire Code badge (build 384.61, chapter badges phase 1).

Renders each of Fire Code's chapters as the app draws it - buildUnitBadgeSVG, earned and as its empty slot - at 96px and 26px,
light on dark, in a grid with the chapter's title under each, and writes one PNG.
  python3 tools/render-chapter-badges.py OUT.png [--index OLD/index.html] [--only 10,12] [--cols 6] [--dsf 2]
                                         [--phone OUT.png] [--ipad OUT.png] [--earned samples|all|none|10,12] [--shape coin]
--only takes chapter numbers (or title prefixes such as 'Appendix B'); --index renders another build's file; --phone / --ipad also
write a screenshot of Profile > Badges (440x956 / 834x1194) with the chapters that have an icon earned and the rest empty (or
--earned all / none / a comma list of chapter numbers). --shape KEY draws every chosen chapter on one outline (a what-if for the
sheet only: BADGE_SHAPE's keys, e.g. coin, shield, disc) - nothing is written.
Playwright + /opt/pw-browsers Chromium; the Firebase CDN is blocked, which changes nothing here. Never prints or writes a sync code."""
import json, os, sys, glob, functools, http.server, socket, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
INDEX = arg("--index")
BODY = open(INDEX, encoding="utf-8").read() if INDEX else open(ROOT + "/index.html", encoding="utf-8").read()
OWNER = "xph5b57jbp5a"   # the class owner's public id (not a sync code)
ALL_CHARS = ["detective", "masked", "zeus", "poseidon", "clown", "valkyrie", "marksman", "astronaut", "hacker", "timekeeper", "ronin", "hive",
             "voidwalker", "umbra", "singularity", "genesis", "lunar", "solar", "tempest", "frost", "oracle", "inferno", "astral", "celestial", "zenith"]
# a used, existing Fire Code account: onboarded, tours seen, Nova met, everything it holds announced
SEED = {"onboardingComplete": True, "firstName": "Sample", "avatarChar": "ninja", "publicId": OWNER, "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30,
                     "longestStreak": 20, "currentStreak": 3},
        "unlocksShown": {"chars": ALL_CHARS, "banners": [], "fx": ["fireworks", "underwater", "bubbles", "ufo"]},
        "flareHintsShown": ["umbra", "singularity", "genesis"]}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted", "penal55124.seen", "penal124256.seen", "penal256578.seen"]
def init_js(seed, cls="ifc"):
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(seed))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(seed))
    return s + " }catch(e){} })()"
def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port
def open_page(br, port, seed, w, h, dsf, cls="ifc", body=None):
    """The page, retried: under load (other sessions' browsers) a renderer of this 10MB page is sometimes killed at start."""
    for attempt in range(4):
        try:
            return _open_page(br, port, seed, w, h, dsf, cls, body)
        except Exception as e:
            if attempt == 3: raise
            print("page start failed (%s), retrying" % str(e).splitlines()[0][:80], flush=True)
def _open_page(br, port, seed, w, h, dsf, cls="ifc", body=None):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dsf, has_touch=True)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js(seed, cls))
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body or BODY))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": "x", "force": False, "frameId": ""})))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
SHEET = r"""async ({ only, cols, shape, px0 }) => {
  if(shape){ for(const u of unitsInTeachingOrder()) IFC_BADGE_SHAPE[u] = shape; }
  const us = unitsInTeachingOrder();
  const pick = us.filter(u => !only.length || only.some(o => /^\d+$/.test(o) ? (u.indexOf('Chapter ' + o + ':') === 0) : u.toLowerCase().indexOf(o.toLowerCase()) === 0));
  document.body.innerHTML = ''; document.documentElement.style.cssText = 'background:#0B0D10';
  const root = document.createElement('div');
  root.id = 'sheet'; root.style.cssText = 'position:absolute;left:0;top:0;background:#0B0D10;color:#C9D1DA;font:11px/1.25 system-ui,sans-serif;padding:14px;display:grid;grid-template-columns:repeat(' + cols + ',' + (px0 > 96 ? px0 * 2 + 70 : 266) + 'px);gap:12px 10px;';
  document.body.appendChild(root);
  const iconOf = u => (typeof chapterIconFor === 'function' && chapterIconFor(u)) ? 'icon' : 'fallback';
  for(const u of pick){
    const cell = document.createElement('div'); cell.style.cssText = 'background:#12161B;border:1px solid #232A33;border-radius:10px;padding:8px 8px 7px;display:flex;flex-direction:column;gap:6px;';
    const row = document.createElement('div'); row.style.cssText = 'display:flex;align-items:center;gap:8px;';
    const mk = (earned, px) => { const w = document.createElement('div'); w.style.cssText = 'width:' + px + 'px;height:' + px + 'px;flex:none;display:flex;align-items:center;justify-content:center;';
      const s = buildUnitBadgeSVG(u, earned, { px, dirt: 0 }); s.style.cssText = 'width:100%;height:100%;display:block;overflow:visible'; w.appendChild(s); return w; };
    row.appendChild(mk(true, px0)); row.appendChild(mk(false, px0));
    const small = document.createElement('div'); small.style.cssText = 'display:flex;flex-direction:column;gap:6px;margin-left:2px;';
    small.appendChild(mk(true, 26)); small.appendChild(mk(false, 26)); row.appendChild(small);
    cell.appendChild(row);
    const t = document.createElement('div'); t.textContent = u; t.style.cssText = 'color:#DDE3EA;font-weight:600;'; cell.appendChild(t);
    const tg = document.createElement('span'); tg.textContent = '  ' + (iconOf(u) === 'icon' ? 'ICON' : 'fallback'); tg.style.cssText = 'font-size:9px;font-weight:700;letter-spacing:.06em;color:' + (iconOf(u) === 'icon' ? '#7FD6A0' : '#5C6773'); t.appendChild(tg);
    root.appendChild(cell);
  }
  await new Promise(r => setTimeout(r, 2500));
  /* let every supersampled finish land */
  for(let i = 0; i < 40; i++){ if(typeof BADGE_STRIKE_DRAFTS === 'undefined' || !BADGE_STRIKE_DRAFTS.size) break; await new Promise(r => setTimeout(r, 400)); }
  const r = root.getBoundingClientRect(); return { n: pick.length, w: Math.ceil(r.width), h: Math.ceil(r.height) };
}"""
def shoot_tiles(pg, out, w, h, dsf, tile=640):
    """The sheet in horizontal bands, stitched: one 3000x3300 capture kills the renderer under load."""
    from PIL import Image
    import io
    img = Image.new("RGB", (int(w * dsf), int(h * dsf)), (11, 13, 16))
    y = 0
    while y < h:
        hh = min(tile, h - y)
        pg.evaluate("()=>document.querySelectorAll('body > *:not(#sheet)').forEach(e=>e.remove())")
        png = pg.screenshot(clip={"x": 0, "y": y, "width": w, "height": hh}, full_page=True, timeout=120000)
        img.paste(Image.open(io.BytesIO(png)).convert("RGB"), (0, int(y * dsf)))
        y += hh
    img.save(out)
def main():
    out = next((a for i, a in enumerate(sys.argv[1:], 1) if a.endswith(".png") and not sys.argv[i - 1].startswith("--")), None)
    from playwright.sync_api import sync_playwright
    only = [x for x in (arg("--only", "") or "").split(",") if x]
    cols = int(arg("--cols", "6")); dsf = int(arg("--dsf", "2"))
    srv, port = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME, args=["--disable-dev-shm-usage"])
        if out:
            ctx, pg, errs = open_page(br, port, SEED, 440, 956, dsf)
            r = pg.evaluate(SHEET, {"only": only, "cols": cols, "shape": arg("--shape"), "px0": int(arg("--px", "96"))})

            shoot_tiles(pg, out, r["w"], r["h"], dsf)
            print("sheet:", out, r, "errors:", errs[:3]); ctx.close()
        for flag, (w, h) in (("--phone", (440, 956)), ("--ipad", (834, 1194))):
            dest = arg(flag)
            if not dest: continue
            earned = arg("--earned", "samples")
            ctx, pg, errs = open_page(br, port, SEED, w, h, int(arg("--sdsf", "3" if w < 500 else "2")))
            pg.evaluate("""(earned)=>{ const us = unitsInTeachingOrder(); const samples = (typeof CHAPTER_ICON === 'object') ? us.filter(u => chapterIconFor(u)) : [];
              const want = earned === 'all' ? us : earned === 'none' ? [] : earned === 'samples' ? samples : us.filter(u => earned.split(',').some(n => u.indexOf('Chapter ' + n + ':') === 0));
              want.forEach(u => { store.unitPerfects[u] = Math.max(store.unitPerfects[u] || 0, badgeThresholdFor(u)); });
              showRanksScreen('badges'); }""", earned)
            pg.wait_for_timeout(3500)
            for _ in range(30):
                if not pg.evaluate("()=>typeof BADGE_STRIKE_DRAFTS !== 'undefined' && BADGE_STRIKE_DRAFTS.size"): break
                pg.wait_for_timeout(400)
            pg.screenshot(path=dest, timeout=120000)
            print("screen:", dest, "errors:", errs[:3]); ctx.close()
        br.close()
if __name__ == "__main__":
    main()
