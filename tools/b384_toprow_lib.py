"""Shared harness for build 384.95's top-row gate (tools/check-b384-toprow.py) and its screenshots.

A used account (shoot-flow's seed: badges, hundos, the board's classmates through a fake Firestore), every one-time card and
tour marked seen, in either class, on a device with its safe-area insets substituted into the served copy (Chromium reports 0).
INK reads the top row of whatever screen is up: the smallest top of any visible text line, button, image or icon in the top
quarter of the screen that belongs to the page (not the status-bar strip, the sky, a header's backdrop or the tab bar)."""
import json, os, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(_src, g)
CHROME = g["CHROME"]
INSET_RE = g["INSET_RE"]
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_IPAD = "Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
# name, w, h, insets (top, right, bottom, left), installed, UA, notched-upright-installed (the line E applies)
DEVICES = {
    "promax":  ("iPhone 17 Pro Max", 440, 956, (62, 0, 34, 0), True, UA, True),
    "zoom85":  ("iPhone 17 Pro Max @85%", 518, 1125, (73, 0, 40, 0), True, UA, True),
    "se":      ("iPhone SE", 375, 667, (20, 0, 0, 0), True, UA, False),
    "ipadP":   ("iPad Pro 11 portrait", 834, 1194, (24, 0, 20, 0), True, UA_IPAD, False),
    "ipadL":   ("iPad Pro 11 landscape", 1194, 834, (24, 0, 20, 0), True, UA_IPAD, False),
    "safari":  ("Safari tab 440", 440, 797, (0, 0, 0, 0), False, UA, False),
    "side":    ("iPhone 17 Pro Max on its side", 956, 440, (0, 62, 21, 62), True, UA, False),
}
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',"
        "'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.freshstart',"
        "'class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal55124.seen','1'); localStorage.setItem('class26e.penal124256.seen','1');"
        "localStorage.setItem('class26e.penal256578.seen','1'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31'); localStorage.setItem('class26e.daily.seen','x');")
IFC = ("localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1')); localStorage.setItem('class26e.ifc.synccode','TEST-3843');"
       "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');")
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1') || localStorage.getItem('__fresh')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); """ + SEEN + """ %s })()"""
def seed():
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "xph5b57jbp5a"; d["firstName"] = "Casey"; d["novaMet"] = 99
    d["unlocksShown"] = {"chars": [], "banners": ["hundos100"], "fx": ["fireworks", "blackhole", "underwater", "worldtree", "bubbles", "ufo"]}
    import time as _t
    d["testHistory"] = [{"label": "Identity Crimes", "units": ["Identity Crimes"], "mode": m, "pct": 60 + 8 * j, "elapsedMs": 900000 + j * 137000,
                         "playedAt": int(_t.time() * 1000) - j * 172800000, "score": 12 + j, "total": 20, "seconds": 300 + 20 * j} for j, m in enumerate(("drill", "exam", "game"))]
    return d
_srv = None
def url():
    global _srv
    if _srv is None: _srv = g["serve"]()
    return _srv[1]
def body_for(raw, ins):
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return INSET_RE.sub(lambda m: v[m.group(1)], raw)
def open_page(br, raw, devkey, cls="academy", fresh=False, settle=True):
    name, w, h, ins, installed, ua, notched = DEVICES[devkey]
    # at 85% page zoom the page is laid out 518 CSS px wide on a 440pt screen: the screen stays the phone's (syncFieldFloor's --zc reads it)
    scr = {"width": 440, "height": 956} if devkey == "zoom85" else {"width": w, "height": h}
    ctx = br.new_context(viewport={"width": w, "height": h}, screen=scr, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    if fresh: ctx.add_init_script("try{ localStorage.setItem('__fresh','1'); localStorage.setItem('class26e.freshstart','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); }catch(e){}")
    else: ctx.add_init_script(INIT % (json.dumps(json.dumps(seed())), IFC if cls == "ifc" else ""))
    pg = ctx.new_page(); body = body_for(raw, ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url())
    if settle:
        pg.wait_for_timeout(3200)
        pg.evaluate(QUIET)
        pg.wait_for_timeout(300)
    return ctx, pg, errs
QUIET = ("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} try{ store.novaMet=99; }catch(e){}"
         " try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} try{ theme.muteBanners = true; }catch(e){}"
         " document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card, .intro-pop, #intro-pop, .update-banner, .daily-alert, .savecode-card').forEach(n=>n.remove()); }")
# The page's top row. Every visible leaf in the top 40% of the screen: text (its line box), a button, an image, an svg, a progress
# dot; skipped: the status-bar strip and fixed full-width backdrops (no ink of their own), the bottom tab bar, the sky, hidden things.
INK = """()=>{
  const H = innerHeight, W = innerWidth, lim = H * .4, out = [];
  const skip = e => e.closest('#top-edge, #top-deep, #top-guard, .bottomtabs, #splashscreen, #tour-overlay, .chatdock-panel, [aria-hidden="true"].sky, #sb-probe');
  const vis = e => { for(let n = e; n && n !== document.body; n = n.parentElement){ const s = getComputedStyle(n); if(s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) < .05) return false; } return true; };
  /* (a box that starts above the screen is cut by the screen's edge - a backdrop or a page scrolled under the top - not a top-row element) */
  /* what an ancestor that clips (overflow other than visible) cuts away is not ink: the box is cut to it */
  const clipTop = (e, top, bottom) => { for(let n = e.parentElement; n && n !== document.body; n = n.parentElement){ const s = getComputedStyle(n);
      if(s.overflowY !== 'visible' || s.overflowX !== 'visible'){ const q = n.getBoundingClientRect(); top = Math.max(top, q.top); bottom = Math.min(bottom, q.bottom); } }
    return bottom - top >= 2 ? top : null; };
  const add = (e, r0, kind) => { const ct = clipTop(e, r0.top, r0.bottom); if(ct === null) return; const r = { top: ct, bottom: r0.bottom, left: r0.left, right: r0.right, width: r0.width, height: r0.bottom - ct };
    if(r.width < 2 || r.height < 2 || r.top < 0 || r.top >= lim || r.right <= 0 || r.left >= W) return;
    out.push({ top: Math.round(r.top * 10) / 10, bottom: Math.round(r.bottom * 10) / 10, kind, what: (e.id ? '#' + e.id : '') + (e.className && e.className.baseVal === undefined ? '.' + String(e.className).trim().split(/\\s+/).slice(0, 2).join('.') : '') + ' ' + (kind === 'text' ? JSON.stringify((e.textContent || '').trim().slice(0, 24)) : e.tagName.toLowerCase()) }); };
  /* a text line's INK: its box is the font's content area (ascent + descent), so the baseline is the box's top plus the font's
     ascent and the glyphs' top is the baseline less what these letters actually reach (canvas measureText, the same font) */
  const cv = document.createElement('canvas').getContext('2d');
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for(let t = walker.nextNode(); t; t = walker.nextNode()){
    if(!t.textContent.trim()) continue; const e = t.parentElement; if(!e || skip(e) || !vis(e)) continue;
    if(/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|OPTION)$/.test(e.tagName)) continue;
    const s = getComputedStyle(e); cv.font = s.fontStyle + ' ' + s.fontWeight + ' ' + s.fontSize + ' ' + s.fontFamily;
    const m = cv.measureText(t.textContent.trim()); const off = (m.fontBoundingBoxAscent || 0) - (m.actualBoundingBoxAscent || 0);
    const g = document.createRange(); g.selectNodeContents(t);
    for(const r of g.getClientRects()) add(e, { top: r.top + Math.max(0, off), bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height }, 'text'); }
  /* a control's box is ink only where it is painted (a fill, a rim, a shadow): a bare text button's box is air, its words are measured above */
  const painted = e => { const s = getComputedStyle(e); const c = s.backgroundColor.match(/[\\d.]+/g);
    return (c && (c.length < 4 || parseFloat(c[3]) > .05) && !/^rgba\\(0, 0, 0, 0\\)$/.test(s.backgroundColor)) || s.backgroundImage !== 'none' || s.boxShadow !== 'none' ||
      (parseFloat(s.borderTopWidth) > 0 && !/rgba\\([^)]*, 0\\)$/.test(s.borderTopColor) && s.borderTopStyle !== 'none'); };
  for(const e of document.querySelectorAll('body button, body a[href], body img, body svg, body [role="button"], body .qdot, body .back-link')){
    if(skip(e) || !vis(e) || (e.closest('svg') && e.closest('svg') !== e)) continue;
    if(!/^(IMG|svg)$/.test(e.tagName) && !e.classList.contains('qdot') && !painted(e)) continue;
    add(e, e.getBoundingClientRect(), e.tagName.toLowerCase()); }
  out.sort((a, b) => a.top - b.top);
  const de = document.documentElement;
  return { items: out.slice(0, 8), min: out.length ? out[0].top : null, scroll: Math.max(0, de.scrollHeight - innerHeight), sy: scrollY,
    E: (() => { const p = document.createElement('div'); p.style.cssText = 'position:fixed;left:0;width:1px;height:1px;visibility:hidden;top:var(--top-e, -1px)';
      document.body.appendChild(p); const v = p.getBoundingClientRect().top; p.remove(); return v; })(), sat: getComputedStyle(de).getPropertyValue('--sat').trim() };
}"""
CHAT = """()=>{ const b = document.getElementById('chatdock-btn'); if(!b || b.closest('[hidden]') || !b.getClientRects().length) return null; const r = b.getBoundingClientRect();
  if(getComputedStyle(b).visibility === 'hidden') return null; return [Math.round(r.left * 10) / 10, Math.round(r.top * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; }"""
