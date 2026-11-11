#!/usr/bin/env python3
"""Build 384 r21: the test settings sheet - its title, and room for what is in it.
Madison, over the start sheet on 'Choose your chapters' (Fire Code, iPhone 17 Pro Max, page zoom ~85%): "The word Drill here is
redundant, should this say Test settings or something?" and "should the menu it pulls up be a little bigger? Because right now if
you hit Time limit, you can't even tell the settings are there because you'd have to scroll which is not practical."
What it was: a title that said the mode a third time (the chip on the page, the card above Begin), and ONE scroller capped at
80vh with the summary and Begin stuck to its bottom edge - covering ~200px of it, so on a 440x956 phone the whole Stopwatch &
Timer card sat under them, and the minutes picker Time limit opens arrived below the fold with nothing to say so.
Read off the page (the real sheet, both classes, Drill / Mock / Review, the default state and with every switch on):
 (1) the title is the generic settings title - not the mode's name (and Review's says Review settings);
 (2) PINNED: with every option expanded the summary and Begin are both on screen, Begin's foot clear of the home indicator, the
     foot does not move when the body is scrolled, and nothing of the body is drawn under it;
 (3) TALL: on a phone the sheet is at least 85% of the visible height - unless everything already fits (it sizes to its rows);
 (4) a control a switch has just revealed (Time limit's minutes) is inside the scroller's visible window right after the tap
     (the scroller is the body; it scrolls to it - never past the switch that asked), and the sheet is not wider than the screen;
 (5) the sheet never reaches the page's own header buttons (its top is below them on a phone), and never off the top;
 (6) every control on it is a 44px tap target (rows, buttons, the close button);
 (7) a swipe down closes it from the handle, the title row and the body at its top, and does NOT close it from a body that has
     been scrolled (that pull scrolls);
 (8) a phone on its side keeps Begin on screen and a body of at least 90px; (9) no page errors.
Run:  python3 tools/check-b384-startsheet.py [--only SUBSTR] [--shoot DIR] [--against OLD/index.html]   (must FAIL on 384.16)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
argv = sys.argv[:]; sys.argv = [argv[0]]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ss"}
exec(src, G)
g = G["g"]
if "--against" in argv:
    OLD = open(argv[argv.index("--against") + 1], encoding="utf-8").read(); IR = g["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = _old
ONLY = argv[argv.index("--only") + 1] if "--only" in argv else None
SHOOT = argv[argv.index("--shoot") + 1] if "--shoot" in argv else None
if SHOOT: os.makedirs(SHOOT, exist_ok=True)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

# label, width, height, insets (top, right, bottom, left) in CSS px, touch, screen (None = the viewport), phone?
DEVICES = [
    ("SE 375x667",        375,  667, (20, 0, 0, 0),   True,  None,       True),
    ("Pro Max 440x956",   440,  956, (62, 0, 34, 0),  True,  None,       True),
    ("Pro Max zoom 518x1126", 518, 1126, (73, 0, 40, 0), True, (440, 956), True),
    ("iPad 834x1194",     834, 1194, (24, 0, 20, 0),  True,  None,       False),
    ("laptop 1366x768",  1366,  768, (0, 0, 0, 0),    False, None,       False),
    ("desktop 1920x1080", 1920, 1080, (0, 0, 0, 0),   False, None,       False),
]
LANDSCAPE = ("Pro Max landscape 956x440", 956, 440, (0, 62, 21, 62), True, None, True)

OPEN = """async(mode)=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
  try{ homeUnlocksOwed = () => false; }catch(e){}
  document.querySelectorAll('.unlock-card,.rs-spot,.rs-fly').forEach(n => n.remove()); document.body.classList.remove('cutscene-focus');
  theme.reduceMotion=false; try{ applyTheme(); }catch(e){}
  document.getElementById('unitoptions-modal')?.remove();
  cfg.mode=mode; cfg.source='all'; cfg.timer='off'; cfg.shuffle=true; cfg.recall=false; cfg.flashcards=false; showSetup(); await wait(900);
  const c=document.querySelector('.pick input'); if(!c) return 'nounit'; c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); await wait(300);
  document.getElementById('nextbtn').click(); await wait(1400);
  return document.querySelector('.unitoptions-modal-sheet.is-setup') ? 'ok' : 'nosheet'; }"""
# everything on, in the order they are on the sheet; Time limit comes after Stopwatch and takes it off (one or the other)
ALLON = """async()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); const wait=ms=>new Promise(r=>setTimeout(r,ms));
  const done=[]; for(const row of [...sh.querySelectorAll('.opt')]){ const cb=row.querySelector(':scope > input[type=checkbox]'); if(!cb || cb.disabled || row.hidden || !row.getClientRects().length) continue;
    if(!cb.checked){ cb.click(); await wait(250); done.push(row.textContent.trim().slice(0, 18)); } }
  await wait(900); return done; }"""
# the sheet's geometry, read off the page - the scroller is the body in this build and the sheet itself in the one before
GEO = """()=>{ const m=document.getElementById('unitoptions-modal'), sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); if(!sh) return null;
  const body=sh.querySelector('.optionsmodal-body'), bar=sh.querySelector('.sheet-begin-bar'), head=sh.querySelector('.unitoptions-modal-head');
  const R=e=>{ const r=e.getBoundingClientRect(); return { l:r.left, t:r.top, r:r.right, b:r.bottom, w:r.width, h:r.height }; };
  const scroller = /auto|scroll/.test(getComputedStyle(body).overflowY) && body.scrollHeight > body.clientHeight + 1 ? body : sh;
  const begin=sh.querySelector('.sheet-begin-btn'), sum=sh.querySelector('.start-summary'), mode=sh.querySelector('.sheet-summary-mode'), title=sh.querySelector('.unitoptions-modal-title');
  const sc = scroller === body ? body : sh;
  return { open: !m.hidden, vw: innerWidth, vh: innerHeight, sheet: R(sh), bar: R(bar), begin: R(begin), sum: R(sum), head: R(head), body: R(body),
    title: title.textContent.trim(), mode: mode.textContent.trim(), modeKey: mode.dataset.mode, beginText: begin.textContent.trim(),
    scrollable: sc.scrollHeight > sc.clientHeight + 1, scrollTop: sc.scrollTop, scrollMax: sc.scrollHeight - sc.clientHeight,
    sheetSW: sh.scrollWidth, sheetCW: sh.clientWidth, bodySW: body.scrollWidth, bodyCW: body.clientWidth, docSW: document.documentElement.scrollWidth,
    bodyIsScroller: scroller === body, zoomed: document.documentElement.classList.contains('page-zoomed'), fade: getComputedStyle(body).maskImage || getComputedStyle(body).webkitMaskImage };
}"""
HEADER = """()=>{ const bs=[...document.querySelectorAll('#stage .settings-nav-back, .chatdock-btn')].filter(b=>{ const r=b.getBoundingClientRect(); return r.width>0 && r.top < 200 && r.bottom > 0 && !b.closest('.unitoptions-modal'); });
  return { n: bs.length, bottom: Math.max(0, ...bs.map(b=>b.getBoundingClientRect().bottom)) }; }"""
TARGETS = """()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); const out=[];
  for(const e of sh.querySelectorAll('button, label.opt, .bank-opt, input[type=range], .slider-allbtn')){ if(e.closest('[hidden]') || e.hidden) continue; const r=e.getBoundingClientRect(); if(!r.width || !r.height) continue;
    const cs=getComputedStyle(e); if(cs.visibility==='hidden' || cs.pointerEvents==='none') continue;
    out.push({ el:(e.className||e.tagName).toString().slice(0,34)+' '+(e.textContent||'').trim().slice(0,14), w:Math.round(r.width), h:Math.round(r.height) }); }
  return out; }"""
REVEAL = """async()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); const wait=ms=>new Promise(r=>setTimeout(r,ms));
  const body=sh.querySelector('.optionsmodal-body'); const sc = (body.scrollHeight > body.clientHeight + 1 && /auto|scroll/.test(getComputedStyle(body).overflowY)) ? body : sh;
  const row=[...sh.querySelectorAll('.opt')].find(o=>/Time limit/.test(o.textContent)); const cb=row.querySelector(':scope > input[type=checkbox]');
  if(cb.checked){ cb.click(); await wait(700); }
  /* the person scrolls to the switch first (they have to see it to tap it), as they would */
  sc.scrollTop = 0; await wait(200); row.scrollIntoView({ block:'center' }); await wait(400);
  const bar=sh.querySelector('.sheet-begin-bar'), before={ sTop: sh.getBoundingClientRect().top, row: row.getBoundingClientRect().top };
  cb.click(); await wait(1100);
  const m=sh.querySelector('.minutes-sect'); const r=m.getBoundingClientRect(), sr=sh.getBoundingClientRect(), br=bar.getBoundingClientRect(), rr=row.getBoundingClientRect();
  const lim=sh.querySelector('.minutes-sect input[type=range]').getBoundingClientRect();
  return { shown: !m.hidden && r.height > 0, top: r.top, bottom: r.bottom, winTop: sr.top, winBottom: br.top, rowTop: rr.top, rowBottom: rr.bottom,
    sliderTop: lim.top, sliderBottom: lim.bottom, scrollTop: sc.scrollTop, before }; }"""
def tap_swipe(cdp, x, y0, y1, steps=14, wait=0.016):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y0}]}); time.sleep(0.05)
    for i in range(1, steps + 1):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y0 + (y1 - y0) * i / steps}]}); time.sleep(wait)
    time.sleep(0.04)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
def page(br, cls, dev):
    label, w, h, ins, touch, screen, phone = dev
    kw = dict(viewport={"width": w, "height": h}, has_touch=touch)
    if screen: kw["screen"] = {"width": screen[0], "height": screen[1]}
    ctx = br.new_context(**kw)
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"])
    if touch: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"] if cls == "ifc" else G["academy"], **({} if cls == "ifc" else {"active": "academy"})))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
def shot(pg, tag):
    if SHOOT: pg.screenshot(path=os.path.join(SHOOT, tag + ".png"))
def slug(s): return "".join(c if c.isalnum() else "-" for c in s).strip("-").lower()

def one(pg, cdp, cls, dev, mode, full):
    label, w, h, ins, touch, screen, phone = dev
    tag = "%s / %s / %s" % (label, cls, mode)
    r = pg.evaluate(OPEN, mode)
    if r != "ok":
        chk("%s: the start sheet opens (%s)" % (tag, r), False, r); return
    d0 = pg.evaluate(GEO)
    shot(pg, "%s-%s-%s-default" % (slug(label), cls, mode))
    # (1) the title
    names = {"drill": "Drill", "exam": "Mock", "review": "Review"}
    t = d0["title"]
    chk("(1) %s: the title is the generic settings title, not the mode (%r; the card says %r)" % (tag, t, d0["mode"]),
        t.lower().endswith("settings") and t != d0["mode"] and (mode == "review" or d0["mode"].lower() not in t.lower()) and (mode != "review" or t.lower().startswith("review")), [t, d0["mode"]])
    on = pg.evaluate(ALLON)
    d = pg.evaluate(GEO)
    shot(pg, "%s-%s-%s-allon" % (slug(label), cls, mode))
    ib = ins[2]
    # (2) pinned
    s, b, bar, sm, be = d["sheet"], d["body"], d["bar"], d["sum"], d["begin"]
    inview = lambda r: r["t"] >= -0.5 and r["b"] <= d["vh"] + 0.5 and r["l"] >= -0.5 and r["r"] <= d["vw"] + 0.5
    clear = be["b"] <= d["vh"] - ib + 0.5
    chk("(2) %s, everything on (%s): the summary and Begin are both on screen, Begin clear of the home indicator (%dpx)" % (tag, ", ".join(on) or "nothing to switch", ib),
        inview(sm) and inview(be) and clear and be["b"] <= bar["b"] + 0.5 and sm["b"] <= be["t"], d)
    if d["bodyIsScroller"] and d["scrollable"]:
        # the foot holds still while the body is scrolled, and the body is not drawn under it
        pg.evaluate("()=>{ const b=document.querySelector('.unitoptions-modal-sheet.is-setup .optionsmodal-body'); b.scrollTop = b.scrollHeight; }"); pg.wait_for_timeout(300)
        d2 = pg.evaluate(GEO)
        chk("(2) %s: scrolled to the end, the foot has not moved and the body stops where it begins (foot %.1f -> %.1f, body ends %.1f)" % (tag, bar["t"], d2["bar"]["t"], d2["body"]["b"]),
            abs(d2["bar"]["t"] - bar["t"]) < .6 and d2["body"]["b"] <= d2["bar"]["t"] + .6, [d, d2])
        pg.evaluate("()=>{ document.querySelector('.unitoptions-modal-sheet.is-setup .optionsmodal-body').scrollTop = 0; }"); pg.wait_for_timeout(200)
    elif not d["bodyIsScroller"] and d["scrollable"]:
        chk("(2) %s: the sheet's rows scroll under a pinned foot (the body is its own scroller)" % tag, False, d)
    # (3) tall
    fits = not d["scrollable"]
    if phone:
        chk("(3) %s: the sheet is at least 85%% of the visible height (%.0f%% of %d) or sizes to rows that all fit" % (tag, 100 * s["h"] / d["vh"], d["vh"]),
            s["h"] >= .85 * d["vh"] - 1 or fits, [s["h"], d["vh"], d["scrollable"]])
    # (4) not wider than the screen
    chk("(4) %s: no sideways scroll (sheet %d/%d, body %d/%d, page %d/%d)" % (tag, d["sheetSW"], d["sheetCW"], d["bodySW"], d["bodyCW"], d["docSW"], d["vw"]),
        d["sheetSW"] <= d["sheetCW"] + 1 and d["bodySW"] <= d["bodyCW"] + 1 and d["docSW"] <= d["vw"] + 1 and s["l"] >= -.5 and s["r"] <= d["vw"] + .5, d)
    # (5) the page's header buttons are not cut across by its top edge
    if phone and w < 600 and h > w:
        hd = pg.evaluate(HEADER)
        chk("(5) %s: the sheet's top (%.0f) is under the page's header buttons (%.0f), and on screen" % (tag, s["t"], hd["bottom"]),
            s["t"] >= hd["bottom"] - 1 and s["t"] >= ins[0] - .5, [s, hd])
    if not full: return
    # (6) tap targets
    ts = pg.evaluate(TARGETS)
    small = [x for x in ts if min(x["w"], x["h"]) < 43.5]
    chk("(6) %s: every control on the sheet is a 44px target (%d checked; under: %s)" % (tag, len(ts), small[:5]), ts and not small, small)
    # (4) a revealed control, right after the tap
    rv = pg.evaluate(REVEAL)
    shot(pg, "%s-%s-%s-timelimit" % (slug(label), cls, mode))
    inside = rv["shown"] and rv["top"] >= rv["winTop"] - 1 and rv["bottom"] <= rv["winBottom"] + 1
    chk("(4) %s: Time limit's minutes are inside the scroller's visible window right after the tap (picker %.0f-%.0f, window %.0f-%.0f; the switch %.0f-%.0f)" % (tag, rv["top"], rv["bottom"], rv["winTop"], rv["winBottom"], rv["rowTop"], rv["rowBottom"]),
        inside and rv["rowTop"] >= rv["winTop"] - 1, rv)
    # (7) swipes
    if touch and w < 900:
        cdp = pg.context.new_cdp_session(pg)
        def reopen():
            pg.evaluate("()=>{ document.getElementById('unitoptions-modal').hidden = false; const s=document.querySelector('.unitoptions-modal-sheet.is-setup'); s.style.transform=''; s.classList.remove('is-dragging'); const b=s.querySelector('.optionsmodal-body'); b.scrollTop=0; s.scrollTop=0; }")
            pg.wait_for_timeout(900)
        def closed(): return pg.evaluate("()=>document.getElementById('unitoptions-modal').hidden")
        pg.evaluate("()=>{ for(const o of document.querySelectorAll('.unitoptions-modal-sheet.is-setup .opt')) if(/Time limit/.test(o.textContent)){ const c=o.querySelector('input'); if(c.checked) c.click(); } }"); pg.wait_for_timeout(500)
        reopen(); d = pg.evaluate(GEO); s = d["sheet"]; cx = s["l"] + s["w"] / 2
        tap_swipe(cdp, cx - 60, s["t"] + 8, s["t"] + 8 + s["h"] * .6); pg.wait_for_timeout(700)
        chk("(7) %s: a swipe down from the handle closes it" % tag, closed(), d)
        reopen(); d = pg.evaluate(GEO); s = d["sheet"]
        tap_swipe(cdp, cx - 60, d["head"]["t"] + 30, d["head"]["t"] + 30 + s["h"] * .6); pg.wait_for_timeout(700)
        chk("(7) %s: a swipe down from the title row closes it" % tag, closed(), d)
        reopen(); d = pg.evaluate(GEO); s = d["sheet"]
        y = d["body"]["t"] + 12
        tap_swipe(cdp, s["l"] + 24, y, y + s["h"] * .6); pg.wait_for_timeout(700)
        chk("(7) %s: a swipe down from the body at its top closes it" % tag, closed(), d)
        reopen(); d = pg.evaluate(GEO)
        if d["bodyIsScroller"] and d["scrollable"]:
            pg.evaluate("()=>{ document.querySelector('.unitoptions-modal-sheet.is-setup .optionsmodal-body').scrollTop = 90; }"); pg.wait_for_timeout(300)
            d = pg.evaluate(GEO); s = d["sheet"]; y = d["body"]["t"] + 40
            tap_swipe(cdp, s["l"] + 24, y, y + 70); pg.wait_for_timeout(700)
            d3 = pg.evaluate(GEO)
            chk("(7) %s: a pull down on a body that has been scrolled scrolls it, it does not close the sheet (scrollTop %d -> %d)" % (tag, d["scrollTop"], d3["scrollTop"]),
                not closed() and d3["scrollTop"] < d["scrollTop"] and abs(d3["sheet"]["t"] - s["t"]) < 1, [d, d3])
        reopen()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    devs = [d for d in DEVICES if not ONLY or ONLY.lower() in d[0].lower()]
    allerrs = []
    for dev in devs:
        label = dev[0]
        full = True
        plan = [("academy", ["drill", "exam", "review"]), ("ifc", ["drill", "review"])]
        for cls, modes in plan:
            ctx, pg, errs = page(br, cls, dev)
            cdp = ctx.new_cdp_session(pg)
            for i, mode in enumerate(modes):
                one(pg, cdp, cls, dev, mode, full=(i == 0))
            if dev[6] and dev[1] == 518:
                chk("%s: the page is zoomed (html.page-zoomed, --zc %s)" % (label, pg.evaluate("()=>getComputedStyle(document.documentElement).getPropertyValue('--zc')")),
                    pg.evaluate("()=>document.documentElement.classList.contains('page-zoomed')"))
            allerrs += errs; ctx.close()
    if not ONLY or "land" in ONLY.lower():
        ctx, pg, errs = page(br, "academy", LANDSCAPE)
        r = pg.evaluate(OPEN, "drill"); d = pg.evaluate(GEO); shot(pg, "landscape-academy-drill-default")
        pg.evaluate(ALLON); d = pg.evaluate(GEO); shot(pg, "landscape-academy-drill-allon")
        chk("(8) %s: Begin is on screen (%.0f of %d) and the body is at least 90px tall (%.0f)" % (LANDSCAPE[0], d["begin"]["b"], d["vh"], d["body"]["h"]),
            d["begin"]["b"] <= d["vh"] + .5 and d["begin"]["t"] >= 0 and d["body"]["h"] >= 90, d)
        allerrs += errs; ctx.close()
    chk("(9) no page errors", not allerrs, allerrs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
