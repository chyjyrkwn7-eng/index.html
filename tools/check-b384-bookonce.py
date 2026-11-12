"""Build 384.58: the IFC book is asked for once per device, and never when it is already there.
Reported: a classmate joined Fire Code, had to load the IFC PDF to join, and a test then asked for it AGAIN at the bottom of a
question; and one who signed up on a phone had to load it again on the computer.
The book is kept in the device's own IndexedDB and never in the account (it is a licensed book), so a second device does need it
once. What was wrong is everything else that ended on the same "Your IFC PDF isn't on this device" card and its Load button:
  (1) a save counted as done when the browser had ACCEPTED the write, not when it had committed it - a copy of tens of megabytes
      reported "kept", the class switch reloaded the page, and the index survived without its book (measured at 120 MB: index
      there, PDF gone) - so a book that was "kept" asked for again;
  (2) the card was the same whatever had gone wrong: the PDF reader (pdf.js, from a CDN) not loading for a moment, in a classroom,
      showed "your PDF isn't on this device ... this browser let the saved copy go" over a copy that was fine, and the failed load
      was remembered for the whole visit, so loading the PDF again (the screen it sent people to) failed the same way too;
  (3) a copy whose notes (the index) were from another build, or missing, was treated as no copy at all - nobody is asked for a
      book they already gave: it is read again from the copy;
  (4) "kept on this device" was said without looking: now only when both parts are read back at full size;
  (5) on a device that never had the book (a computer, the installed app after the browser tab) the card said the browser had let
      the copy go; it now says the book stays per device, is never in the account, and loads once here.
Sections (S1, S4 need nothing; S2, S3, S5 need the owner's own copy, which never goes into the repo):
  S1  a write is resolved only after the browser has committed it (the commit event comes first);
  S2  the book loaded through the reader's own path; a test shows its code and no prompt; again after a reload; the reader
      dropping out (pdf.js unreachable) shows the try-again card, NOT a request for the PDF (no file chooser opens from it); with
      the connection back, Try again draws the code with no file picked; a stale index on a saved copy is read again, not asked for;
  S3  the reader failing while a book is being loaded, then back: the same screen loads it, the failure was not kept;
  S4  a second device (nothing saved): the card is the per-device one, with one button that opens the file chooser, 44px+;
  S5  a write that does not stick is not reported kept.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-bookonce.py
      (--against OLD/index.html must FAIL)"""
import os, sys, json, mimetypes
HERE = os.path.dirname(os.path.abspath(__file__))
srcf = os.path.join(HERE, "check-b383-signup.py")
head = open(srcf).read().split('print("check-b383-signup against"')[0]
G = {"__file__": srcf, "__name__": "b384bookonce"}
exec(head, G)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
HAVE_BOOK = os.path.exists(PDFJS + "build/pdf.min.mjs") and os.path.isfile(BOOK)
from playwright.sync_api import sync_playwright
open_page, relaunch, account, CHROME = G["open_page"], G["relaunch"], G["account"], G["CHROME"]
SEEN_ACCT = G["SEEN_ACCT"]
ok = True

CODE = "TEST-3840"
# a Fire Code account (Fire Code alone: the device opens in it), as a device holds it after sign-up
acct = account("Gate Student", "gatebook0001", 0, 0, classes=["ifc"])
ifcs = account("Gate Student", "gatebook0001", 0, 0)
INIT = SEEN_ACCT + ("localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
                    "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.ifc.drill.v1', %s);"
                    % (json.dumps(json.dumps(acct)), CODE, json.dumps(json.dumps(ifcs))))
SEED = {"progress": {CODE: acct, CODE + "__ifc": ifcs}}

STATE = {"fail": False}
OPEN = []
def pdfjs_route(route, request):
    if STATE["fail"]: return route.abort()
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})

def new_device(br, init=INIT):
    """a device of its own: its own storage; the account is on it, the book is not (until it is loaded)"""
    for attempt in range(4):   # a page of this size can be taken down by a busy machine: open it again
        try:
            ctx, pg = open_page(br, "phone", init=init, seed=SEED, wait=3500); break
        except Exception as e:
            print("  (page did not open: %s; again)" % str(e)[:60])
            try: ctx.close()
            except Exception: pass
    else:
        raise RuntimeError("the page would not open")
    OPEN.append(ctx)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    pg.chooser = []
    pg.on("filechooser", lambda fc: pg.chooser.append(1))
    pg.wait_for_timeout(1500)
    return ctx, pg

def wait_for(pg, js, ms):
    t = 0
    while t < ms:
        try:
            if pg.evaluate(js): return True
        except Exception: pass
        pg.wait_for_timeout(250); t += 250
    return False

START = """()=>{ const ids = QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].ifc && QUESTIONS[i].ifc.citation && QUESTIONS[i].ifc.citation.source!=='amendment' && !QUESTIONS[i].ifc.citation.blur).slice(0,5);
  cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic.trim()]; beginRun(ids); return ids.length; }"""
CARD = """()=>{ const r=document.querySelector('.ifc-ref'); if(!r) return null; const b=r.querySelector('.ifc-code-body'); const lk=r.querySelector('.ifc-locked');
  const btns=[...r.querySelectorAll('.ifc-code-body button')].filter(x=>x.offsetParent);
  return { locked: !!lk, why: lk ? (lk.dataset.why || '') : null, canvases: r.querySelectorAll('canvas').length, buttons: btns.length,
           btnH: btns.map(x=>Math.round(x.getBoundingClientRect().height)), open: !!(r.querySelector('details') || {}).open }; }"""
def question_code(pg, settle_ms=90000):
    """take a one-question look: start a drill, answer, open the code; returns the code box once it holds a picture or a card"""
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.evaluate(START)
    if not wait_for(pg, "()=>document.querySelectorAll('.choice').length > 0", 40000): return None
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()"); pg.wait_for_timeout(800)
    for i in range(4):   # pick until the answer is right: the code is shown with the answer
        if pg.evaluate("()=>!!document.querySelector('.ifc-ref')"): break
        pg.evaluate("(i)=>{ const c=document.querySelectorAll('.choice')[i]; c && c.click(); }", i); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ const d=document.querySelector('.ifc-ref details'); if(d && !d.open){ const s=d.querySelector('summary'); s && s.click(); } }")
    wait_for(pg, "()=>{ const r=document.querySelector('.ifc-ref'); return !!r && (r.querySelector('canvas') || r.querySelector('.ifc-locked')); }", settle_ms)
    pg.wait_for_timeout(600)
    return pg.evaluate(CARD)
def load_book(pg, wait_ms=240000):
    pg.evaluate("()=>{ ifcPickBook({ enroll: true }); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    wait_for(pg, "()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')", wait_ms)
    return pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? { ok: o.classList.contains('is-ok'), bad: o.classList.contains('is-bad'), kept: o.dataset.kept === undefined ? null : o.dataset.kept, reason: o.dataset.reason || null } : null; }")
def stored(pg):
    return pg.evaluate("""async()=>{ const p = await ifcKv('get','pdf').catch(()=>null), i = await ifcKv('get','index').catch(()=>null);
      const V = await ifcViewer().catch(()=>null);
      return { pdf: p ? p.size : null, idxV: i ? i.v : null, now: V ? V.INDEX_VERSION : null }; }""")

def section(pw, fn, title):
    """a section in a browser of its own, run again (its output discarded) if the machine takes the page down: a page this size,
    pdf.js and a 700-page book have a busy sandbox killing the renderer now and then"""
    global cur, ok
    for attempt in range(4):
        cur = []
        br = None
        try:
            print("\n" + title, flush=True)
            br = pw.chromium.launch(executable_path=CHROME, args=["--disable-dev-shm-usage"])
            fn(br)
        except Exception as e:
            print("  (the page was taken down: %s; again)" % str(e).splitlines()[0][:80], flush=True)
            STATE["fail"] = False
            continue
        finally:
            for c in OPEN:
                try: c.close()
                except Exception: pass
            del OPEN[:]
            try: br and br.close()
            except Exception: pass
        for name, cond, info in cur:
            ok = ok and bool(cond)
            print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
        return
    ok = False
    print("FAIL %s ran to its end  -> the page kept crashing" % title, flush=True)
cur = []
def chk(name, cond, info=""):
    cur.append((name, bool(cond), info))

def sec_s1(br):
    ctx, pg = new_device(br)
    r = pg.evaluate("""async()=>{
      let commitAt = 0; const add = IDBTransaction.prototype.addEventListener;
      const orig = IDBDatabase.prototype.transaction;
      IDBDatabase.prototype.transaction = function(){ const tx = orig.apply(this, arguments); tx.addEventListener('complete', () => { commitAt = performance.now(); }); return tx; };
      const blob = new Blob([new Uint8Array(3 * 1024 * 1024)], { type: 'application/pdf' });
      await ifcKv('put', 'probe', blob);
      const resolvedAt = performance.now();
      await new Promise(r => setTimeout(r, 1500));
      IDBDatabase.prototype.transaction = orig;
      const back = await ifcKv('get', 'probe'); await ifcKv('del', 'probe');
      return { resolvedAt, commitAt, size: back ? back.size : null }; }""")
    chk("S1 the write resolved no earlier than its commit (%s)" % r, r["commitAt"] > 0 and r["resolvedAt"] >= r["commitAt"], r)
    chk("S1 the data is there", r["size"] == 3 * 1024 * 1024, r)
    ctx.close()


def sec_s4(br):
    ctx, pg = new_device(br)
    st = stored(pg)
    chk("S4 the device holds no book (%s)" % st, st["pdf"] is None, st)
    card = question_code(pg, 60000)
    chk("S4 a question's code box shows a card, not a picture (%s)" % card, bool(card) and card["locked"] and not card["canvases"], card)
    chk("S4 it is the per-device card: it says it is this device that lacks the book (why=device), not a copy that was lost (%s)" % (card or {}).get("why"),
        bool(card) and card["why"] == "device", card)
    chk("S4 one button, 44px or more (%s)" % ((card or {}).get("btnH"),), bool(card) and card["buttons"] == 1 and min(card["btnH"] or [0]) >= 43.5, card)
    before = len(pg.chooser)
    pg.evaluate("()=>document.querySelector('.ifc-ref .ifc-code-body button.ifc-link').click()"); pg.wait_for_timeout(900)
    chk("S4 the button opens the file chooser: loading it is one tap away", len(pg.chooser) > before, len(pg.chooser))
    ctx.close()


def sec_s2(br):
    ctx, pg = new_device(br)
    res = load_book(pg)
    chk("S2 the book is accepted (%s)" % res, res and res["ok"], res)
    st = stored(pg)
    chk("S2 it is saved on this device, the PDF at its size and the index at this build's version (%s)" % st, bool(st["pdf"]) and st["idxV"] == st["now"], st)
    chk("S2 the screen says it is kept only because it read it back (data-kept=%s)" % (res or {}).get("kept"), (res or {}).get("kept") == "1", res)
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(800)
    card = question_code(pg)
    chk("S2 first test after loading it: the code is drawn and nothing asks for the PDF (%s)" % card, bool(card) and card["canvases"] > 0 and not card["locked"], card)
    relaunch(pg)
    card = question_code(pg)
    chk("S2 after a reload (a new page, the class's own way in): drawn again, no prompt (%s)" % card, bool(card) and card["canvases"] > 0 and not card["locked"], card)
    n0 = len(pg.chooser)
    # the reader (pdf.js) does not load this time: a classroom, a phone asleep
    STATE["fail"] = True
    relaunch(pg)
    card = question_code(pg)
    st = stored(pg)
    chk("S2 the reader out of reach, the copy still saved (%s): the box is the try-again card, not the one that asks for the PDF (%s)" % (st["pdf"], card),
        bool(st["pdf"]) and bool(card) and card["locked"] and card["why"] == "unreadable", card)
    pg.evaluate("()=>document.querySelector('.ifc-ref .ifc-code-body button.ifc-link')?.click()"); pg.wait_for_timeout(1200)
    chk("S2 and its button did not open the file chooser: nobody was asked for the PDF (%d choosers)" % (len(pg.chooser) - n0), len(pg.chooser) == n0, len(pg.chooser) - n0)
    STATE["fail"] = False
    pg.evaluate("()=>document.querySelector('.ifc-ref .ifc-code-body button.ifc-link')?.click()")
    drawn = wait_for(pg, "()=>!!document.querySelector('.ifc-ref canvas')", 60000)
    chk("S2 the connection back, Try again draws the code - no file picked, the failed load was not kept for the visit", drawn and len(pg.chooser) == n0, (drawn, len(pg.chooser) - n0))
    # a saved copy whose notes are from another build: read again from the copy, not asked for
    pg.evaluate("()=>ifcKv('put', 'index', { v: 1, numPages: 697 })"); pg.wait_for_timeout(300)
    relaunch(pg)
    card = question_code(pg, 150000)
    st = stored(pg)
    chk("S2 a saved copy with an out-of-date index is read again, not asked for: the code is drawn (%s) and the index is current again (%s)" % (card, st),
        bool(card) and card["canvases"] > 0 and not card["locked"] and st["idxV"] == st["now"] and len(pg.chooser) == n0, (card, st))
    ctx.close()


def sec_s3(br):
    ctx, pg = new_device(br)
    STATE["fail"] = True
    res = load_book(pg, 40000)
    chk("S3 with the reader out of reach the screen says the reader did not load, not that the file was refused (%s)" % res, bool(res) and res["bad"] and res["reason"] == "reader", res)
    STATE["fail"] = False
    pg.evaluate("()=>{ document.querySelector('.ifc-analyze')?.remove(); }")
    res = load_book(pg)
    chk("S3 the connection back, the same screen loads the book: the failure was not kept for the visit (%s)" % res, bool(res) and res["ok"], res)
    ctx.close()


def sec_s5(br):
    ctx, pg = new_device(br)
    pg.evaluate("""()=>{ const put = IDBObjectStore.prototype.put;
      IDBObjectStore.prototype.put = function(v, k){ if(k === 'pdf') return put.call(this, 0, 'dropped'); return put.apply(this, arguments); }; }""")
    res = load_book(pg)
    st = stored(pg)
    chk("S5 the device holds no PDF (%s) and the screen does not say it kept one (data-kept=%s)" % (st["pdf"], (res or {}).get("kept")), st["pdf"] is None and (res or {}).get("kept") == "0", (res, st))
    ctx.close()


ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
def want(k): return not ONLY or k in ONLY
with sync_playwright() as pw:
    if want("S1"): section(pw, sec_s1, "S1 a save resolves after the browser has committed it")
    if want("S4"): section(pw, sec_s4, "S4 a second device: nothing saved on it")
    if not HAVE_BOOK:
        print("SKIP S2, S3, S5: set PDFJS_DIR (unpacked pdfjs-dist@5.4.149) and IFC_BOOK (the owner's 2021 IFC PDF)")
    else:
        if want("S2"): section(pw, sec_s2, "S2 the book loaded once; a test; a reload; the reader dropping out; a stale index")
        if want("S3"): section(pw, sec_s3, "S3 the reader fails while loading the book, then is back")
        if want("S5"): section(pw, sec_s5, "S5 a copy the device did not keep is not reported kept")
print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
