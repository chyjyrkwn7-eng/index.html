"""Build 383: Fire Code's flash cards with the owner's own IFC loaded - what his phone shows.
check-b383-flashcards runs with no book (the code box is the lock card and "Load my IFC PDF") and no pdf.js (the CDN is blocked
here), so the pictures - the thing the code box is for - were never drawn there. Here the reader's real path runs: the book is
picked through "Load my IFC PDF"'s own file input, analysed (the 12-second Analyzing screen) and kept, and pdf.js is served from
a local copy. Then, in Fire Code, as an iPhone-sized touch screen, a flash card from the book and one from the county's
amendments:
(0) the book is accepted ("Verified");
(1) a tap on the card turns it to its answer side;
(2) "Show the code" opens the code and the card stays on its answer side; the code's picture is drawn (a canvas) - the book's
    section cut from his PDF, or the county's;
(3) the card holds the drawn picture: nothing of the answer side hangs out of the card, the arrows under it stay clear;
(4) a tap on the picture opens the page viewer (and draws it) - the card does not turn; Done closes it, the card still on its
    answer side;
(5) "Enlarge" opens the viewer too, the card does not turn;
(6) "Hide the code" closes it, the card stays on its answer side and shrinks back;
(7) no page errors.
The book never goes into the repo (the repo is public): its path is given when the gate is run.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149 package> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b383-ifcbook.py
      (--against OLD/index.html: on 382, before the flash cards' own-tap guard, the taps turn the card)
SHOTS=<folder> saves a picture of each card with its code open."""
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
    # (0) the book, through the reader's own path: Load my IFC PDF's file input, the Analyzing screen, kept on the device
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    got = wait_for(pg, "()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')", 150000)
    res = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? { ok: o.classList.contains('is-ok'), title: o.querySelector('.ia-title').textContent, text: o.querySelector('.ia-result').textContent } : null; }")
    chk("(0) the owner's IFC is accepted (%s)" % (res and res["title"]), got and res and res["ok"], res)
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(1200)
    for kind in ("book", "amendment"):
        unit = pg.evaluate("""async(kind)=>{ const w=ms=>new Promise(r=>setTimeout(r,ms));
          const q = QUESTIONS.find(q=>q.ifc && q.ifc.citation && !q.ifc.citation.blur && ((q.ifc.citation.source==='amendment') === (kind==='amendment')));
          if(!q) return null; showFlashcards([q.topic.trim()], 'all'); await w(1200);
          const want = QUESTIONS.indexOf(q); const at = fc.deck.indexOf(want); if(at > 0){ fc.pos = at; showFlashcards(fc.units, fc.source, fc.versions); await w(900); }
          return q.topic.trim() + ' | ' + q.ifc.citation.label; }""", kind)
        if not unit:
            chk("%s: a Fire Code card of this kind" % kind, False); continue
        print("  %s card: %s" % (kind, unit))
        tap(pg, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(900)
        s1 = pg.evaluate(STATE)
        chk("(1) %s: a tap on the card turns it to its answer" % kind, s1["flipped"] is True, s1)
        tap(pg, ".fc-card .fc-back summary.ifc-code-sum")
        drawn = wait_for(pg, "()=>{ const c=document.querySelector('.fc-card .fc-back .ifc-code-body .ifc-clips canvas'); return !!c && c.width > 0; }", 30000)
        pg.wait_for_timeout(1200)
        s2 = pg.evaluate(STATE)
        chk("(2) %s: 'Show the code' opens the code, the card stays on its answer, and the code's picture is drawn (%s)" % (kind, s2["pic"]),
            s2["flipped"] is True and s2["open"] is True and drawn and not s2["locked"], s2)
        chk("(3) %s: the card holds the drawn picture (answer side %spx in a %spx card) and the arrows are below it (%s / %s)"
            % (kind, s2["faceH"], s2["cardH"], s2["cardBottom"], s2["navTop"]),
            s2["faceH"] <= s2["cardH"] + 2 and s2["navTop"] is not None and s2["navTop"] >= s2["cardBottom"] - 1, s2)
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); pg.evaluate(AT, ".fc-card .fc-back .ifc-code-body"); pg.wait_for_timeout(500)
            pg.screenshot(path=os.path.join(SHOTS, "ifcbook-%s.png" % kind))
        tap(pg, ".fc-card .fc-back .ifc-code-body .ifc-clips")
        vz = wait_for(pg, "()=>!!document.querySelector('.ifc-vz-pages canvas')", 20000)
        pg.wait_for_timeout(600)
        s4 = pg.evaluate(STATE)
        if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "ifcbook-%s-viewer.png" % kind))
        chk("(4) %s: a tap on the picture opens the page viewer and draws it; the card does not turn" % kind, s4["viewer"] and vz and s4["flipped"] is True, s4)
        pg.evaluate("()=>document.querySelector('.ifc-vz .ifc-vz-btn.is-done')?.click()"); pg.wait_for_timeout(900)
        s4b = pg.evaluate(STATE)
        chk("(4) %s: Done closes the viewer, the card still on its answer" % kind, not s4b["viewer"] and s4b["flipped"] is True and s4b["open"] is True, s4b)
        big = pg.evaluate("()=>{ const b=[...document.querySelectorAll('.fc-card .fc-back .ifc-links .ifc-link')].find(x=>/Enlarge/.test(x.textContent)); if(!b) return false; b.id='__enlarge'; return true; }")
        if big:
            tap(pg, "#__enlarge"); wait_for(pg, "()=>!!document.querySelector('.ifc-vz')", 8000); pg.wait_for_timeout(500)
            s5 = pg.evaluate(STATE)
            chk("(5) %s: 'Enlarge' opens the viewer too; the card does not turn" % kind, s5["viewer"] and s5["flipped"] is True, s5)
            pg.evaluate("()=>document.querySelector('.ifc-vz .ifc-vz-btn.is-done')?.click()"); pg.wait_for_timeout(900)
        else:
            chk("(5) %s: an Enlarge button under the picture" % kind, False)
        tap(pg, ".fc-card .fc-back summary.ifc-code-sum"); pg.wait_for_timeout(1100)
        s6 = pg.evaluate(STATE)
        chk("(6) %s: 'Hide the code' closes it, the card stays on its answer and shrinks back (%s -> %s)" % (kind, s2["cardH"], s6["cardH"]),
            s6["flipped"] is True and s6["open"] is False and s6["cardH"] < s2["cardH"], s6)
    chk("(7) no page errors", not errs, errs[:3])
    ctx.close(); br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
