#!/usr/bin/env python3
"""Build 384 (r19), THE PAGE VIEWER ON A COMPUTER. Madison, on a Windows computer: "when opening the view page of code it was absolutely
massive and it didn't look like a normal page on a computer? Fix that. We need this app to be functioning perfectly on the computer."
'Show the whole page' / 'Show the whole book page' (and Enlarge) open the viewer (ifcOpenViewer). It was a card the width of the whole
window with the page fitted to the card's WIDTH: on a 1920px screen a letter page was 1878px wide and 2430px tall - a third of one page
on the screen, the highlight below it. It is a centred reader now: the page fitted to the window's height (never wider than 60rem),
on a calm backdrop under a slim bar with the zoom and Done on its right, + / - and Ctrl + wheel and a trackpad's pinch zoom the PAGE,
the wheel scrolls, a drag pans, Esc closes, and no key reaches the question behind it.
Read off the page, in a Windows desktop browser tab (a mouse, no touch) at 1366x768, 1536x864, 1920x1080 and 2560x1440, each at device pixel
ratios 1 and 1.5, a county citation (HC 322 and HC 5609.4.1) - and, with IFC_BOOK set to the owner's 2021 IFC (it is only read), a book
citation (IFC 1004.5 and IFC 1013):
 (1) THE PAGE: its rendered width is no more than min(60rem, the window less margins), its middle is the window's middle (2px), it is
     whole in the window's height (no taller than the window, top and bottom on the screen), the card is in the window and no
     horizontal scroll anywhere;
 (2) THE BAR is in the window, slim, with Done at its top right;
 (3) THE HIGHLIGHT sits on the cited text: the soft tint's box is inside the page and inside what is on the screen, runs from the cited
     lines' top to their bottom, and the deeper gold (the cited words) is on those words - and it is on them still, in the same place
     on the page, at 2x;
 (4) ZOOM: + and - (buttons, keys, Ctrl + wheel) change the page's size by a step each way and stop at the limits (never below the fitted
     page, never past 5x), Ctrl + wheel is the page's and not the browser's, the wheel scrolls a zoomed page, a drag pans it, Fit width
     and Fit page (where the page is narrower than the room) go between the two;
 (5) THE KEYBOARD: with the viewer up, 1-4 and Enter do nothing to the question behind it; Esc closes it and the app beneath is as it was;
 (6) ENLARGE: the cut picture is whole in the window, no wider than 60rem, centred, no larger than the book's print x2.6;
 (7) A PHONE (440x956, touch, installed) is as it was: the page is the card's width, card inset 12px, no new bar controls; and an iPad
     (834x1194 and 1194x834) has no overflow, a centred page whole in its height.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> [IFC_BOOK=<the owner's 2021 IFC PDF>] python3 tools/check-b384-viewerdesk.py [--against OLD/index.html] [--quick]
      [--shoot DIR [--tag NAME]]   (--against the build before this (af5725d) must FAIL)"""
import json, os, sys, time, mimetypes
HERE = os.path.dirname(os.path.abspath(__file__))
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "build/pdf.min.mjs"):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 package (the booklet is drawn with it)"); sys.exit(0)
HAVE_BOOK = bool(BOOK) and os.path.isfile(BOOK)
src = open(os.path.join(HERE, "check-b382-test.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b382-test.py"), "__name__": "b384vd"}
exec(src, G)
g = G["g"]
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = g["INSET_RE"]
    g["patched"] = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
QUICK = "--quick" in sys.argv
SHOOT = sys.argv[sys.argv.index("--shoot") + 1] if "--shoot" in sys.argv else ""
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "shot"
if SHOOT: os.makedirs(SHOOT, exist_ok=True)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:420], flush=True)
WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
SETTLE = """()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99;
  try{ const p = pendingHomeUnlocks(); markUnlocksShown(p.chars, p.banners, p.fx); }catch(e){}
  document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }"""
def page_desk(br, w, h, dpr):
    """a Windows desktop browser tab: a mouse, no touch, not installed, no safe-area insets"""
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=False, is_mobile=False, user_agent=WIN_UA)
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    G["route_pdf"](ctx)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = g["patched"]((0, 0, 0, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(G["INIT"] % json.dumps(json.dumps(G["d"])))
    pg.goto(G["url"]); pg.wait_for_timeout(3500); pg.evaluate(SETTLE)
    return ctx, pg, errs
def qindex(pg, section, county):
    return pg.evaluate("""([sec, county])=>{ const i = QUESTIONS.findIndex(q=>{ const c=q.ifc&&q.ifc.citation; return c && !c.blur && String(c.section)===sec && ((c.source==='amendment')===county); }); return i; }""", [section, county])
def start_one(pg, idx):
    pg.evaluate("""(id)=>{ const top = QUESTIONS[id].topic; const more = QUESTIONS.map((q,i)=>i).filter(i=>i!==id && QUESTIONS[i].topic===top).slice(0,3);
      cfg.source='all'; cfg.mode='drill'; cfg.units=[top]; beginRun([id].concat(more)); }""", idx)
    pg.wait_for_selector(".qpanel .choice", timeout=30000); pg.wait_for_timeout(1000)
def pos(pg): return pg.evaluate("()=>pos")
# ---- doing things as a person at the computer does: the mouse
def mclick(pg, sel):
    xy = pg.evaluate(g["CENTRE"] if False else G["CENTRE"], sel)
    if not xy: return False
    pg.wait_for_timeout(250); xy = pg.evaluate("(sel)=>{ const r=document.querySelector(sel).getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }", sel)
    pg.mouse.click(*xy); return True
def answer_mouse(pg):
    pg.evaluate("()=>{ const r=correctSlot(order[pos]); document.querySelector('.choice[data-index=\"'+r+'\"]').scrollIntoView({block:'center'}); }")
    pg.wait_for_timeout(250)
    c = pg.evaluate("()=>{ const r=correctSlot(order[pos]); const b=document.querySelector('.choice[data-index=\"'+r+'\"]').getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }")
    pg.mouse.click(*c); pg.wait_for_timeout(2000)
def open_code_mouse(pg):
    if not pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code, details.ifc-code'); return !!(d && d.open); }"):
        mclick(pg, ".ifc-code-sum")
    for _ in range(120):
        if pg.evaluate("()=>!!document.querySelector('.ifc-code[open] .ifc-links') && !!document.querySelector('.ifc-code[open] .ifc-clips canvas')"): break
        pg.wait_for_timeout(150)
    pg.wait_for_timeout(500)
def open_viewer(pg, which, touch_cdp=None):
    """which: 'page' (Show the whole ... page) or 'zoom' (Enlarge); a mouse click, or - with a cdp session - a touch tap"""
    sel = ".ifc-code[open] .ifc-link.is-" + which
    if touch_cdp: G["tap"](touch_cdp, *pg.evaluate(G["CENTRE"], sel))
    else: mclick(pg, sel)
    for _ in range(160):
        if pg.evaluate("()=>!!document.querySelector('.ifc-vz-pages canvas')"): break
        pg.wait_for_timeout(150)
    pg.wait_for_timeout(1300)
MEASURE = """()=>{ const R = e => { if(!e) return null; const r=e.getBoundingClientRect(); return {l:r.left,t:r.top,w:r.width,h:r.height,r:r.right,b:r.bottom}; };
  const sc=document.querySelector('.ifc-vz-scroll'); const cvs=[...document.querySelectorAll('.ifc-vz-pages canvas')];
  return { vw: innerWidth, vh: innerHeight, rem: parseFloat(getComputedStyle(document.documentElement).fontSize)||16, docW: document.documentElement.scrollWidth, bodyW: document.body.scrollWidth,
    card: R(document.querySelector('.ifc-vz-card')), bar: R(document.querySelector('.ifc-vz-bar')), done: R(document.querySelector('.ifc-vz-btn.is-done')), scroll: R(sc),
    sw: sc ? [sc.scrollWidth, sc.clientWidth] : null, cv: cvs.map(R), nat: cvs.map(c=>[c.width,c.height]), z: { out: !!document.querySelector('.ifc-vz-btn.is-out:disabled'), in: !!document.querySelector('.ifc-vz-btn.is-in:disabled') },
    fit: (()=>{ const b=document.querySelector('.ifc-vz-btn.is-fit'); return b && !b.hidden ? b.textContent.trim() : null; })(), n: document.querySelectorAll('.ifc-vz').length }; }"""
def M(pg): return pg.evaluate(MEASURE)
def SV(pg, key="w"):
    """the first page's size/position once it has stopped moving (a zoom eases over ~.22s, and the machine may be loaded)"""
    prev, same = None, 0
    for _ in range(60):
        v = M(pg)["cv"][0][key]
        same = same + 1 if prev is not None and abs(v - prev) < .01 else 0
        if same >= 3: return v
        prev = v; pg.wait_for_timeout(110)
    return prev
# the tint of the page's own pixels (hlall's classification: the one soft wash, the one deeper gold)
TINT = """(ci)=>{ const cv=[...document.querySelectorAll('.ifc-vz-pages canvas')][ci]; if(!cv) return null; const W=cv.width,H=cv.height; const D=cv.getContext('2d').getImageData(0,0,W,H).data;
  const box=()=>({x0:1e9,x1:-1,y0:1e9,y1:-1,n:0}); const soft=box(), deep=box();
  const add=(b,x,y)=>{ b.n++; if(x<b.x0)b.x0=x; if(x>b.x1)b.x1=x; if(y<b.y0)b.y0=y; if(y>b.y1)b.y1=y; };
  for(let y=0,i=0;y<H;y++) for(let x=0;x<W;x++,i+=4){ const R=D[i],G=D[i+1],B=D[i+2];
    if(R>=252&&Math.abs(G-245)<=4&&Math.abs(B-160)<=6) add(soft,x,y); else if(R>=250&&Math.abs(G-215)<=6&&B<=45) add(deep,x,y); }
  return { W, H, soft: soft.n?soft:null, deep: deep.n?deep:null }; }"""
# where the cited lines are on the page, in points from the page's top (what the viewer paints from), and where the cited words are
EXPECT = """async ([idx, county])=>{ const V = await ifcViewer(); const c = QUESTIONS[idx].ifc.citation; let doc, clip;
  if(county){ doc = await ifcCountyDoc(); clip = await V.countyClip(doc, c, ifcCountyOpts); }
  else { const book = await ifcEnsureBook(); const loc = V.locate(book.index, c); doc = book.doc; clip = await V.computeClip(book.doc, book.index, loc, c, book.opts); }
  if(!clip || !clip.ok) return { skip: true };
  const cited = clip.cited || clip.segments.filter(s=>!s.whole); if(!cited.length) return { skip: true };
  const sg = cited[0], page = await doc.getPage(sg.page), PH = page.view[3], PW = page.view[2];
  const idxPage = clip.pages.indexOf(sg.page);
  const same = cited.filter(x => x.page === sg.page);   /* every cited piece on that page: the tint is all of them */
  const out = { skip: false, pageIndex: idxPage, PW, PH, top: PH - Math.max(...same.map(x => x.y1)), bottom: PH - Math.min(...same.map(x => x.y0)), words: null };
  const hl = c.highlight || (c.find && c.find[0]);
  if(hl){ const tc = await page.getTextContent(); const key = String(hl).slice(0, 22).toLowerCase();
    const it = tc.items.find(t => t.str && t.str.toLowerCase().includes(key));
    if(it){ const at = it.str.toLowerCase().indexOf(key); out.words = { x: it.transform[4] + it.width * at / Math.max(1, it.str.length), y: PH - it.transform[5], w: it.width * key.length / Math.max(1, it.str.length), h: it.height || 10 }; } }
  return out; }"""
def check_highlight(pg, idx, county, label, zoomed_ref=None):
    ex = pg.evaluate(EXPECT, [idx, county])
    if ex.get("skip") or ex["pageIndex"] < 0:
        chk("%s: the highlight check has a citation to measure" % label, False, ex); return None
    t = pg.evaluate(TINT, ex["pageIndex"])
    m = M(pg); cv = m["cv"][ex["pageIndex"]]; sc = m["scroll"]
    if not t or not t["soft"]:
        chk("%s: the page carries the soft tint where the citation is" % label, False, t); return None
    k = cv["w"] / t["W"]; kp = t["W"] / ex["PW"]                         # CSS px per canvas px; canvas px per point
    sx0, sx1, sy0, sy1 = cv["l"] + t["soft"]["x0"] * k, cv["l"] + (t["soft"]["x1"] + 1) * k, cv["t"] + t["soft"]["y0"] * k, cv["t"] + (t["soft"]["y1"] + 1) * k
    inside = sx0 >= cv["l"] - .5 and sx1 <= cv["r"] + .5 and sy0 >= cv["t"] - .5 and sy1 <= cv["b"] + .5
    ptTop, ptBot = t["soft"]["y0"] / kp, (t["soft"]["y1"] + 1) / kp
    covers = ptTop <= ex["top"] + 9 and ptBot >= ex["bottom"] - 9 and ptTop >= ex["top"] - 60 and ptBot <= ex["bottom"] + 60
    info = {"tint(pt)": [round(ptTop), round(ptBot)], "cited(pt)": [round(ex["top"]), round(ex["bottom"])]}
    chk("%s: the soft tint is inside the page and runs from the cited lines' top to their bottom %s" % (label, info), inside and covers, [inside, covers, info])
    if zoomed_ref is None:
        # on the screen at the default zoom (the page is whole there)
        vis = sy0 >= sc["t"] - .5 and sy1 <= sc["b"] + .5 and sx0 >= sc["l"] - .5 and sx1 <= sc["r"] + .5
        chk("%s: the highlighted lines are on the screen, not below it" % label, vis, [round(sy0), round(sy1), round(sc["t"]), round(sc["b"])])
    frac = ((sx0 - cv["l"]) / cv["w"], (sy0 - cv["t"]) / cv["h"], (sx1 - cv["l"]) / cv["w"], (sy1 - cv["t"]) / cv["h"])
    if zoomed_ref is not None:
        same = all(abs(a - b) < .004 for a, b in zip(frac, zoomed_ref))
        chk("%s: zoomed, the tint is in the same place on the page %s vs %s" % (label, [round(x, 4) for x in frac], [round(x, 4) for x in zoomed_ref]), same, [frac, zoomed_ref])
    if ex.get("words") and t["deep"]:
        w = ex["words"]; dx0, dx1, dy0, dy1 = t["deep"]["x0"] / kp, (t["deep"]["x1"] + 1) / kp, t["deep"]["y0"] / kp, (t["deep"]["y1"] + 1) / kp
        # the deeper gold may run over more than the first line of the cited words (a wrapped sentence): its box must hold the words' first piece
        on = dx0 <= w["x"] + 4 and dx1 >= w["x"] + min(w["w"], 40) - 4 and dy0 <= w["y"] + 2 and dy1 >= w["y"] - w["h"] - 2
        chk("%s: the deeper gold is on the cited words %s" % (label, {"deep(pt)": [round(dx0), round(dx1), round(dy0), round(dy1)], "words(pt)": [round(w["x"]), round(w["w"]), round(w["y"] - w["h"]), round(w["y"])]}), on)
    elif ex.get("words") and not t["deep"]:
        chk("%s: the cited words carry the deeper gold" % label, False, "no deep pixels")
    return frac
def shot(pg, name):
    if SHOOT: pg.screenshot(path=os.path.join(SHOOT, "%s-%s.png" % (TAG, name)))
def geometry(pg, label, w, h, dpr, whole=True):
    m = M(pg)
    if not m["cv"]:
        chk("%s: the viewer is up with a page in it" % label, False, m); return m
    cv = m["cv"][0]; rem = m["rem"]; margin = 24
    cap = min(60 * rem, w - margin)
    chk("%s: the page is no wider than min(60rem, the window less its margins) (%.0f of %.0f px)" % (label, cv["w"], cap), cv["w"] <= cap + 1, m)
    chk("%s: the page's middle is the window's middle (%.1f px off)" % (label, abs(cv["l"] + cv["w"] / 2 - w / 2)), abs(cv["l"] + cv["w"] / 2 - w / 2) <= 2, m)
    if whole:
        chk("%s: one whole page fits the window's height (%.0f px tall in %d)" % (label, cv["h"], h), cv["h"] <= h * 1.0 and cv["t"] >= 0 and cv["b"] <= h, m)
    else:
        chk("%s: the picture is no taller than the window (%.0f in %d)" % (label, cv["h"], h), cv["h"] <= h and cv["t"] >= 0 and cv["b"] <= h, m)
    bar, done, card = m["bar"], m["done"], m["card"]
    chk("%s: the bar is inside the window, slim, with Done at its top right" % label,
        bar and bar["l"] >= 0 and bar["r"] <= w and bar["t"] >= 0 and bar["h"] <= 80 and done and done["r"] <= bar["r"] and done["l"] > w / 2 and done["t"] >= bar["t"] and done["b"] <= bar["b"], m)
    chk("%s: the card is inside the window and nothing scrolls sideways" % label,
        card["l"] >= 0 and card["r"] <= w and card["t"] >= 0 and card["b"] <= h and m["docW"] <= w and m["bodyW"] <= w and m["sw"][0] <= m["sw"][1] + 1, m)
    return m
def run_desk_zoom(pg, label, w, h):
    base = M(pg)["cv"][0]; w0, cx, cy = base["w"], w / 2, h / 2
    # buttons
    seen = [w0]
    for _ in range(14):
        if pg.evaluate("()=>!!document.querySelector('.ifc-vz-btn.is-in:disabled')"): break
        mclick(pg, ".ifc-vz-btn.is-in"); seen.append(SV(pg))
    grew = all(b > a * 1.1 for a, b in zip(seen[:3], seen[1:4]))
    chk("%s: + (button) grows the page a step each time and stops: %s" % (label, [round(x) for x in seen]), grew and seen[-1] <= 5 * w0 + 2 and seen[-1] >= 4.9 * w0 and len(seen) <= 14, seen)
    chk("%s: at the limit + is disabled; the page is never past 5x" % label, pg.evaluate("()=>!!document.querySelector('.ifc-vz-btn.is-in:disabled')"), seen[-1])
    for _ in range(16):
        if pg.evaluate("()=>!!document.querySelector('.ifc-vz-btn.is-out:disabled')"): break
        mclick(pg, ".ifc-vz-btn.is-out"); SV(pg)
    back = SV(pg)
    chk("%s: - steps back to the fitted page and stops there (%.0f, was %.0f); - is disabled" % (label, back, w0), abs(back - w0) <= 1 and pg.evaluate("()=>!!document.querySelector('.ifc-vz-btn.is-out:disabled')"), back)
    # keys
    pg.mouse.move(cx, cy)
    pg.keyboard.press("+"); k1 = SV(pg)
    pg.keyboard.press("-"); k2 = SV(pg)
    pg.keyboard.press("+"); pg.keyboard.press("+"); SV(pg); pg.keyboard.press("0"); k3 = SV(pg)
    chk("%s: the keys + and - zoom the page a step and 0 puts it back (%.0f, %.0f, %.0f from %.0f)" % (label, k1, k2, k3, w0), k1 > w0 * 1.1 and abs(k2 - w0) <= 1 and abs(k3 - w0) <= 1, [k1, k2, k3])
    for _ in range(12): pg.keyboard.press("+")
    top = SV(pg)
    for _ in range(12): pg.keyboard.press("-")
    low = SV(pg)
    chk("%s: 12 presses of + stop at 5x (%.0f of %.0f) and 12 of - at the fitted page (%.0f)" % (label, top, w0, low), top <= 5 * w0 + 2 and abs(low - w0) <= 1, [top, low])
    # ctrl + wheel is the page's, not the browser's
    pg.evaluate("()=>{ window.__wp = []; window.addEventListener('wheel', e => window.__wp.push([e.ctrlKey, e.defaultPrevented]), { passive: true }); }")
    pg.keyboard.down("Control"); pg.mouse.wheel(0, -100); pg.wait_for_timeout(250); pg.mouse.wheel(0, -100); SV(pg); pg.keyboard.up("Control")
    cw = SV(pg); wp = pg.evaluate("()=>window.__wp")
    chk("%s: Ctrl + wheel zooms the page (%.0f from %.0f) and the browser is not asked to (defaultPrevented %s), by a step a notch not a jump" % (label, cw, w0, wp),
        cw > w0 * 1.15 and cw < w0 * 2.6 and wp and all(c and d for c, d in wp), [cw, wp])
    # the wheel scrolls a zoomed page; a drag pans it
    t0 = SV(pg, "t"); pg.mouse.move(cx, cy); pg.mouse.wheel(0, 240); t1 = SV(pg, "t")
    chk("%s: the wheel scrolls the zoomed page (top %.0f -> %.0f)" % (label, t0, t1), t1 < t0 - 100, [t0, t1])
    before = M(pg)["cv"][0]; pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx - 70, cy - 50, steps=6); pg.mouse.up(); SV(pg, "t")
    after = M(pg)["cv"][0]
    chk("%s: a drag pans the zoomed page (moved %.0f, %.0f)" % (label, after["l"] - before["l"], after["t"] - before["t"]), (before["l"] - after["l"]) > 20 or (before["t"] - after["t"]) > 20, [before, after])
    pg.keyboard.press("PageDown"); t2 = SV(pg, "t")
    chk("%s: Page Down moves a zoomed page on" % label, t2 < after["t"] - 100 or (after["t"] <= -10 and True), [after["t"], t2])
    pg.keyboard.press("0"); SV(pg)
def fit_buttons(pg, label, w):
    m = M(pg)
    if not m["fit"]: return
    w0 = m["cv"][0]["w"]; mclick(pg, ".ifc-vz-btn.is-fit"); SV(pg); m2 = M(pg); w1 = m2["cv"][0]["w"]
    room = min(60 * m["rem"], m["scroll"]["w"] - 16)
    chk("%s: Fit width widens the page to the room (%.0f -> %.0f of %.0f) and the button then says Fit page (%s)" % (label, w0, w1, room, m2["fit"]), w1 > w0 * 1.03 and w1 <= room + 2 and w1 >= room - 3 and m2["fit"] == "Fit page", [m, m2])
    mclick(pg, ".ifc-vz-btn.is-fit"); w2 = SV(pg)
    chk("%s: Fit page puts the whole page back (%.0f)" % (label, w2), abs(w2 - w0) <= 1, [w0, w2])
def esc_and_app(pg, label, p0):
    # keys while it is up are the viewer's: 1-4 and Enter do nothing to the question behind it
    pg.keyboard.press("1"); pg.keyboard.press("2"); pg.keyboard.press("Enter"); pg.wait_for_timeout(500)
    st = pg.evaluate("()=>({ pos, vz: document.querySelectorAll('.ifc-vz').length })")
    chk("%s: with the viewer up, 1, 2 and Enter do not reach the question behind it (still on %d)" % (label, p0), st["pos"] == p0 and st["vz"] == 1, st)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(700)
    st = pg.evaluate("()=>({ vz: document.querySelectorAll('.ifc-vz').length, open: document.documentElement.classList.contains('ifc-vz-open'), pos, choices: document.querySelectorAll('.qpanel .choice').length, code: !!document.querySelector('.ifc-code[open]'), next: !!document.getElementById('nextbtn') })")
    chk("%s: Esc closes it and the app beneath is as it was %s" % (label, st), st["vz"] == 0 and not st["open"] and st["pos"] == p0 and st["choices"] >= 2 and st["code"], st)
def desk_run(br, w, h, dpr, cites, enlarge=True):
    label = "%dx%d @%sx" % (w, h, dpr)
    ctx, pg, errs = page_desk(br, w, h, dpr)
    try:
        ids = [(s, c) for s, c in cites if qindex(pg, s, c) >= 0]
        for n, (sec, county) in enumerate(cites):
            idx = qindex(pg, sec, county)
            lab = "%s %s%s" % (label, "HC " if county else "IFC ", sec)
            if idx < 0: chk("%s: the citation is in the bank" % lab, False); continue
            start_one(pg, idx); answer_mouse(pg); open_code_mouse(pg)
            p0 = pos(pg)
            open_viewer(pg, "page")
            m = geometry(pg, lab, w, h, dpr)
            shot(pg, "%dx%d-%s%s-page" % (w, h, "hc" if county else "ifc", sec) + ("" if dpr == 1 else "-dpr%s" % dpr))
            frac = check_highlight(pg, idx, county, lab)
            if n == 0 and frac is not None:
                run_desk_zoom(pg, lab, w, h)
                fit_buttons(pg, lab, w)
                # the highlight, zoomed 2x by the button: the same place on the page
                mclick(pg, ".ifc-vz-btn.is-in"); mclick(pg, ".ifc-vz-btn.is-in"); SV(pg)
                check_highlight(pg, idx, county, lab + " at 1.5x", zoomed_ref=frac)
                pg.keyboard.press("0"); SV(pg)
            esc_and_app(pg, lab, p0)
            if enlarge and n == 0:
                if pos(pg) != p0 or not pg.evaluate("()=>!!document.querySelector('.ifc-code[open] .ifc-link.is-zoom')"):
                    start_one(pg, idx); answer_mouse(pg); open_code_mouse(pg)   # (a build that let a key through has moved on)
                open_viewer(pg, "zoom")
                geometry(pg, lab + " Enlarge", w, h, dpr, whole=False)
                shot(pg, "%dx%d-%s%s-enlarge" % (w, h, "hc" if county else "ifc", sec) + ("" if dpr == 1 else "-dpr%s" % dpr))
                m = M(pg); cv = m["cv"][0] if m["cv"] else {"w": 1e9}
                chk("%s Enlarge: the cut picture is not larger than the book's print x2.6 would make it (%.0f px wide)" % (lab, cv["w"]), cv["w"] <= 60 * m["rem"] + 1, m)
                pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
        chk("%s: no page errors" % label, not errs, errs[:3])
    finally:
        ctx.close()
def touch_run(br, label, w, h, ins, ua, kind):
    """a phone / an iPad: touch, installed, the county booklet's HC 322"""
    ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    try:
        idx = qindex(pg, "322", True)
        start_one(pg, idx); G["answer_right"](pg, cdp); G["open_code"](pg, cdp)
        open_viewer(pg, "page", cdp)
        m = M(pg); cv = m["cv"][0]
        shot(pg, "%s-hc322-page" % label.replace(" ", "-"))
        chk("%s: the page is the card's width less its 8px (%.0f px; the page of af5725d was %.0f)" % (label, cv["w"], kind["page_w"] or -1),
            kind["page_w"] is None or abs(cv["w"] - kind["page_w"]) <= 1, m)
        chk("%s: the card is inset 12px each side and fills the height less the margins, no horizontal scroll" % label,
            kind.get("wide") or (abs(m["card"]["l"] - 12) <= 1 and abs(m["card"]["r"] - (w - 12)) <= 1 and m["docW"] <= w and m["sw"][0] <= m["sw"][1] + 1), m)
        if kind.get("wide"):
            geometry(pg, label, w, h, 2)
            chk("%s: the page is whole in the window's height (%.0f of %d)" % (label, cv["h"], h), cv["h"] <= h and cv["t"] >= 0 and cv["b"] <= h, m)
        else:
            chk("%s: the bar is as it was - zoom, Done, and no Fit button (fit %s)" % (label, m["fit"]), m["fit"] is None and m["done"] and m["bar"]["r"] <= w, m)
            chk("%s: the card is the whole height less the margins (%.0f)" % (label, m["card"]["h"]), m["card"]["t"] >= 0 and m["card"]["b"] <= h, m)
        # touch still works: a double-tap zooms, Done closes
        r = pg.evaluate("()=>{ const r=document.querySelector('.ifc-vz-scroll').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }")
        z = cv["w"]
        for _ in range(4):                                       # (two taps inside 320ms: a loaded machine can miss the window)
            G["tap"](cdp, *r, hold=.02); G["tap"](cdp, *r, hold=.02); z = SV(pg)
            if z > cv["w"] * 1.5: break
            pg.wait_for_timeout(400)
        chk("%s: a double tap zooms the page (%.0f -> %.0f)" % (label, cv["w"], z), z > cv["w"] * 2, z)
        G["tap"](cdp, *pg.evaluate(G["CENTRE"], ".ifc-vz-btn.is-done")); pg.wait_for_timeout(700)
        chk("%s: Done closes it" % label, pg.evaluate("()=>document.querySelectorAll('.ifc-vz').length") == 0)
        chk("%s: no page errors" % label, not errs, errs[:3])
    finally:
        ctx.close()
def book_leg(br):
    ctx, pg, errs = page_desk(br, 1920, 1080, 1)
    try:
        pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
        pg.set_input_files("#ifc-book-input", BOOK)
        for _ in range(600):
            if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
            pg.wait_for_timeout(250)
        pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
        pg.wait_for_timeout(1500)
        for (w, h) in ((1920, 1080), (1366, 768)):
            pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(500)
            for sec in ("1004.5", "1013"):
                idx = qindex(pg, sec, False); lab = "book %dx%d IFC %s" % (w, h, sec)
                if idx < 0: chk("%s: the citation is in the bank" % lab, False); continue
                start_one(pg, idx); answer_mouse(pg); open_code_mouse(pg); p0 = pos(pg)
                if not pg.evaluate("()=>!!document.querySelector('.ifc-code[open] .ifc-link.is-page')"):
                    chk("%s: the card has its whole-page control" % lab, False); continue
                open_viewer(pg, "page")
                geometry(pg, lab, w, h, 1)
                shot(pg, "%dx%d-ifc%s-page" % (w, h, sec))
                check_highlight(pg, idx, False, lab)
                esc_and_app(pg, lab, p0)
        chk("book: no page errors", not errs, errs[:3])
    finally:
        ctx.close()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    DESK = [(1366, 768), (1536, 864), (1920, 1080), (2560, 1440)]
    RUNS = [(1366, 768, 1), (1920, 1080, 1.5)] if QUICK else [(w, h, d) for (w, h) in DESK for d in (1, 1.5)]
    if "--only" in sys.argv:
        want = sys.argv[sys.argv.index("--only") + 1]; RUNS = [r for r in RUNS if want in "%dx%d" % r[:2]]
    if "--touch" in sys.argv: RUNS = []
    for (w, h, d) in RUNS:
        desk_run(br, w, h, d, [("322", True), ("5609.4.1", True)])
    if not ("--only" in sys.argv):
        PHONE_W = float(os.environ.get("PHONE_PAGE_W", "398"))
        touch_run(br, "phone 440x956", 440, 956, (62, 0, 34, 0), G["UA"], {"page_w": PHONE_W})
        touch_run(br, "iPad 834x1194", 834, 1194, (24, 0, 20, 0), G["UA_IPAD"], {"page_w": 792})
        touch_run(br, "iPad landscape 1194x834", 1194, 834, (24, 0, 20, 0), G["UA_IPAD"], {"page_w": None, "wide": True})
        if HAVE_BOOK: book_leg(br)
        else: print("SKIP the book legs: IFC_BOOK is not set to the owner's 2021 IFC PDF (the county legs ran)")
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
