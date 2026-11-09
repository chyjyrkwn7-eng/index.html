"""Build 384: Fire Code's "Show the code" opens smoothly.
Madison, with a screen recording of a Fire Code Review list: "Sometimes when doing the 'show the code' drop down, it isn't
seamless and perfectly moves, there just a super small catch/lag. Ensure that it's super smooth."
The catch was the drawing: the code opened on "Opening the code..." while pdf.js cut and painted the section on the main thread,
and the box jumped to the picture's height. With the owner's own IFC loaded (its real path, as check-b383-ifcbook), in a Fire
Code Review list, as an iPhone-sized touch screen, at 4x CPU:
(1) a code box that has sat in view for a moment (the page still) has its picture drawn already, while still shut;
(2) tapping "Show the code" on it: the picture is there in the first frame after the tap - no "Opening the code..." - and no
    task over 50ms runs in the 600ms after the tap (after one ordinary tap, as in any session: the first sound of a session
    builds the sound engine's reverb, whatever was tapped);
(3) its contents ease in (an animation on transform and opacity, nothing else);
(4) a box scrolled past quickly is not drawn while the page is scrolling;
(5) no page errors.
The book never goes into the repo; its path is given when the gate is run.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-codeopen.py
      (--against OLD/index.html must FAIL)"""

import os, sys, json, mimetypes
HERE = os.path.dirname(os.path.abspath(__file__))
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "build/pdf.min.mjs") or not os.path.isfile(BOOK):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF"); sys.exit(0)
SHOTS = os.environ.get("SHOTS", "")
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b383book"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)

def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})

def page(br, init):
    # the harness's page(), with pdf.js routed BEFORE the app loads (a failed import is kept for the visit)
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    ctx.add_init_script("window.__cloudSeed = {};")
    ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"]); ctx.add_init_script(init)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = G["g"]["patched"]((59, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs

STATE = """()=>{ const c=document.querySelector('.fc-card'); const b=c.querySelector('.fc-back'); const d=b.querySelector('details.ifc-code');
  const cr=c.getBoundingClientRect(), nav=document.querySelector('.fc-back-btn, .fc-next-btn');
  const cv=b.querySelector('.ifc-code-body .ifc-clips canvas');
  return { flipped: c.classList.contains('is-flipped'), open: d ? d.open : null, faceH: b.scrollHeight, cardH: Math.round(cr.height),
           cardBottom: Math.round(cr.bottom), navTop: nav ? Math.round(nav.getBoundingClientRect().top) : null,
           pic: cv ? [cv.width, cv.height, Math.round(cv.getBoundingClientRect().height)] : null, viewer: !!document.querySelector('.ifc-vz'),
           vpic: !!document.querySelector('.ifc-vz-pages canvas'), locked: !!b.querySelector('.ifc-locked') }; }"""
AT = """(sel)=>{ const e=document.querySelector(sel); if(!e) return null; e.scrollIntoView({block:'center'}); return true; }"""
XY = """(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2, scrollY]; }"""
def tap(pg, sel):
    if not pg.evaluate(AT, sel): return False
    pg.wait_for_timeout(400)
    xy, prev, still = None, None, 0
    for _ in range(40):
        xy = pg.evaluate(XY, sel)
        if xy and prev and all(abs(a - b) < .5 for a, b in zip(xy, prev)): still += 1
        else: still = 0
        if still >= 3: break
        prev = xy; pg.wait_for_timeout(120)
    if not xy: return False
    pg.touchscreen.tap(xy[0], xy[1]); return True
def wait_for(pg, js, ms):
    t = 0
    while t < ms:
        if pg.evaluate(js): return True
        pg.wait_for_timeout(250); t += 250
    return bool(pg.evaluate(js))

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, errs = page(br, G["init"](G["ifc"]))
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    got = wait_for(pg, "()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')", 150000)
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(1200)
    # a Review list of a chapter with book citations
    unit = pg.evaluate("""()=>{ const q = QUESTIONS.find(q=>q.ifc && q.ifc.citation && !q.ifc.citation.blur && q.ifc.citation.source !== 'amendment');
      showAnswerReview([q.topic.trim()], 'all'); return q.topic.trim(); }""")
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg); cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    # (4) scroll fast past a few boxes: nothing drawn while scrolling
    DRAWN = "()=>[...document.querySelectorAll('#stage details.ifc-code:not([open]) .ifc-code-body')].filter(b=>b.querySelector('canvas')).length"
    before = pg.evaluate(DRAWN)
    pg.evaluate("""async ()=>{ for(let i=0;i<14;i++){ window.scrollBy(0, 160); window.dispatchEvent(new Event('scroll')); await new Promise(r=>setTimeout(r,60)); } }""")
    mid = pg.evaluate(DRAWN) - before
    # (1) sit still with a box in view
    pg.evaluate("""()=>{ const s=[...document.querySelectorAll('#stage summary.ifc-code-sum')].find(x=>{ const r=x.getBoundingClientRect(); return r.top>200 && r.bottom<innerHeight-200; }) || document.querySelector('#stage summary.ifc-code-sum');
      s.id='__sum'; s.scrollIntoView({ block: 'center' }); }""")
    ahead = wait_for(pg, "()=>{ const d=document.getElementById('__sum').closest('details'); return !d.open && !!d.querySelector('.ifc-code-body .ifc-clips canvas'); }", 12000)
    chk("(1) a box sitting in view has its picture drawn while still shut", ahead)
    chk("(4) nothing drawn while the page scrolls (%d drawn mid-scroll)" % mid, mid == 0, mid)
    pg.evaluate("""()=>{ window.__lt=[]; try{ new PerformanceObserver(l=>l.getEntries().forEach(e=>window.__lt.push([Math.round(e.startTime), Math.round(e.duration)]))).observe({ type:'longtask', buffered:false }); }catch(e){} }""")
    # one ordinary tap first (on a question's words), as any session has had by now: the sound engine builds its reverb on the
    # session's first sound (sndImpulseData, ~12ms at 4x), whatever the tap - not the code box's cost
    bx = pg.evaluate("()=>{ const q=[...document.querySelectorAll('#stage p')].find(e=>{ const r=e.getBoundingClientRect(); return r.top>150 && r.bottom<innerHeight-200 && !e.closest('details'); }); const r=q.getBoundingClientRect(); return [r.left+20, r.top+r.height/2]; }")
    pg.touchscreen.tap(bx[0], bx[1]); pg.wait_for_timeout(1500)
    xy = pg.evaluate("()=>{ const r=document.getElementById('__sum').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }")
    t0 = pg.evaluate("()=>performance.now()")
    pg.touchscreen.tap(xy[0], xy[1])
    first = pg.evaluate("""()=>new Promise(r=>requestAnimationFrame(()=>{ const d=document.getElementById('__sum').closest('details');
      r({ open: d.open, pic: !!d.querySelector('.ifc-code-body .ifc-clips canvas'), busy: !!d.querySelector('.ifc-busy') }); }))""")
    pg.wait_for_timeout(700)
    lt = pg.evaluate("(t0)=>window.__lt.filter(x=>x[0]>=t0 && x[0]<=t0+600)", t0)
    chk("(2) the tap opens on the finished picture (%s) and no task over 50ms follows it (%s)" % (first, lt),
        first["open"] and first["pic"] and not first["busy"] and not [x for x in lt if x[1] > 50], [first, lt])
    an = pg.evaluate("""()=>{ const d=document.getElementById('__sum').closest('details'); const kids=[...d.children].filter(c=>c.tagName!=='SUMMARY');
      return kids.map(k=>{ const c=getComputedStyle(k); return [c.animationName, c.animationDuration]; }); }""")
    kf = pg.evaluate("""()=>{ for(const sh of document.styleSheets){ let rs; try{ rs=sh.cssRules; }catch(e){ continue; }
        for(const r of rs){ if(r.type===7 && r.name==='ifc-code-in') return [...r.cssRules].map(k=>k.style.cssText); } } return null; }""")
    props = set()
    for k in (kf or []):
        for decl in k.split(";"):
            if ":" in decl: props.add(decl.split(":")[0].strip())
    chk("(3) its contents ease in on transform and opacity alone (%s, %s)" % (an, sorted(props)),
        an and all(a[0] == "ifc-code-in" for a in an) and props and props <= {"opacity", "transform"}, [an, kf])
    chk("(5) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
