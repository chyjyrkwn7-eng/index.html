"""Build 384: the Fire Code bank 5.4.2 - every question keeps the identity it had; the wording, the count and the removed
questions as the update says. Madison: "Fix these questions (attached file for updated questions) ... This needs to be CHECKED
PERFECTLY. We can't mess up questions." The update (class26e-ifc-update-5.4.2): 43 rewordings (42 questions, 3 explanations),
36 Finder questions added, 3 removed (ch12-008, ch12-071, ch4-040), nothing else changed.
Read off the page, in Fire Code, against the 5.4.1 bank and app (git: BASE below):
(1) the class holds the 5.4.2 bank as the owner has cut it: 1,797 questions (384.47 took 15 repeats out), and each unit's size is the bank's own questionCount (Chapter 1 160,
    Chapter 2 111, Chapter 4 40, Chapter 12 41, the Finder 138; 384.42 moved five questions between chapters and 384.47 72 into Chapter 1);
(2) every question kept from 5.4.1 (1,776) has exactly the key (topic|position|wording hash) it had - so no one's answers,
    stars, badges or saved tests on them move - EXCEPT the five questions the owner moved in 384.42 (ch12-012 to Chapter 4, ch55-702, ch62-702,
    ch62-703 and ch64-001 to Chapter 2: their keys change on purpose; check-b384-moveq holds the moves: 1,771 of 1,771 others unchanged) - and the 36 new keys are new (no clash with any old key), all keys unique;
(3) the 42 reworded questions show the new wording and the 3 explanations the new explanation; every question, explanation
    and keyed answer shown is the bank's word for word; no answer changed;
(4) the 3 removed questions are gone, and a star left on one comes off once (a tombstone in `unflagged`), other stars kept;
(5) the class list says "Harris County Fire Code Amendments" and the bank's count (1,797), the analysis step the same count;
(6) WITH THE BOOK (PDFJS_DIR and IFC_BOOK as for check-b383-ifcbook - the book never goes in the repo): the owner's IFC is
    accepted, and every new Finder question's "Show the code" draws its picture from the book (an IFC chapter/appendix) or
    the county booklet (Chapter 1 / Exhibit B), with a highlight in it; no page errors.
Run:  [PDFJS_DIR=... IFC_BOOK=...] python3 tools/check-b384-ifc542.py   (--against OLD/index.html: run with the old bank too
      by setting OLD_BANK=<old ifc/bank.js> - the 5.4.1 app FAILS (1), (3)-(5))"""
import os, sys, json, subprocess, mimetypes
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
import ast
def _gen(name):   # the owner's moves and removals, read from the generator's own tables (tools/gen-ifc-bank.py)
    for n in ast.parse(open(os.path.join(HERE, "gen-ifc-bank.py"), encoding="utf-8").read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == name: return ast.literal_eval(n.value)
MOVED_BY_OWNER = sorted(_gen("UNIT_MOVES"))      # 384.42 (5) + 384.47 (72 into Chapter 1): see tools/check-b384-moveq.py, check-b384-moveperm.py
REMOVED_BY_OWNER = sorted(_gen("UNIT_REMOVALS"))   # 384.47: 15 repeats taken out of the bank
EXPECT_TOTAL = 1812 - len(REMOVED_BY_OWNER)       # 1,797
BASE = os.environ.get("BASE", "1982cbf")   # the last commit with the 5.4.1 bank
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
WITH_BOOK = os.path.exists(PDFJS + "build/pdf.min.mjs") and os.path.isfile(BOOK)
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ifc542"}
exec(src, G)
OLD_HTML = subprocess.run(["git", "-C", ROOT, "show", BASE + ":index.html"], capture_output=True, text=True).stdout
OLD_BANK = subprocess.run(["git", "-C", ROOT, "show", BASE + ":ifc/bank.js"], capture_output=True, text=True).stdout
NEW_BANK = open(os.path.join(ROOT, "ifc", "bank.js"), encoding="utf-8").read()
if "--against" in sys.argv:
    OLDX = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLDX)
    G["g"]["patched"] = _old
    if os.environ.get("OLD_BANK"): NEW_BANK = open(os.environ["OLD_BANK"], encoding="utf-8").read()
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
def bank_of(js): return json.loads(js[js.index("window.IFC_BANK = ") + 18:].rstrip().rstrip(";"))
def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
def open_class(br, html, bank, init_extra=""):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    if WITH_BOOK: ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]) + init_extra)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = html((59, 0, 34, 0)) if callable(html) else html
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/ifc/bank.js*", lambda route, request, b=bank: route.fulfill(status=200, headers={"content-type": "text/javascript; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
READ = """()=>({ cls: window.NOVA_CLASS, rows: QUESTIONS.map((q,i)=>({ id: q.ifc && q.ifc.id, key: KEYS[i], topic: q.topic, q: q.q, expl: q.explanation,
  ans: q.choices[q.answer], bq: q.ifc && q.ifc.question, be: q.ifc && q.ifc.explanation, ba: q.ifc && q.ifc.options[q.ifc.answer] })),
  units: (window.IFC_BANK.units||[]).map(u=>({ id: u.id, topic: ifcUnitTopic(u), n: u.questionCount })), meta: window.IFC_BANK.meta.questionCount })"""
ob, nb = bank_of(OLD_BANK), bank_of(NEW_BANK)
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    # the 5.4.1 app and bank: the keys everyone's progress is stored under
    IR = G["g"]["INSET_RE"]
    old_body = IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], OLD_HTML)
    ctx, pg, e0 = open_class(br, old_body, OLD_BANK)
    old = pg.evaluate(READ); ctx.close()
    # this build; a star seeded on a removed question and on a kept one
    O = {r["id"]: r for r in old["rows"]}
    gone_keys = [O[i]["key"] for i in ("ch12-008", "ch12-071", "ch4-040") if i in O]
    keep_key = O.get("ch1-008", {}).get("key")
    seed_flags = ";(()=>{ try{ const k='class26e.ifc.drill.v1'; const s=JSON.parse(localStorage.getItem(k)||'{}'); s.flagged=Object.assign({}, s.flagged||{}, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % json.dumps({k: 1790000000000 for k in gone_keys + ([keep_key] if keep_key else [])})
    ctx, pg, errs = open_class(br, G["g"]["patched"], NEW_BANK, seed_flags)
    new = pg.evaluate(READ)
    flags = pg.evaluate("()=>({ flagged: Object.keys(store.flagged||{}), unflagged: Object.keys(store.unflagged||{}) })")
    errs_all += errs
    N = {r["id"]: r for r in new["rows"]}
    # (1)
    sizes = {}
    for u in new["units"]: sizes[u["id"]] = (u["n"], sum(1 for r in new["rows"] if r["topic"] == u["topic"]))
    wrong = {k: v for k, v in sizes.items() if v[0] != v[1]}
    chk("(1) the 5.4.2 bank: %d questions (bank says %s); Chapter 2 %s, Chapter 4 %s, Chapter 12 %s, the Finder %s; every unit its bank size" % (
        len(new["rows"]), new["meta"], sizes.get("2"), sizes.get("4"), sizes.get("12"), sizes.get("NAV")),
        len(new["rows"]) == new["meta"] == EXPECT_TOTAL and sizes.get("1") == (160, 160) and sizes.get("2") == (111, 111) and sizes.get("4") == (40, 40) and sizes.get("12") == (41, 41) and sizes.get("NAV") == (138, 138) and not wrong, wrong)
    # (2)
    kept = sorted(set(O) & set(N)); moved = [i for i in kept if O[i]["key"] != N[i]["key"]]
    added = sorted(set(N) - set(O)); oldkeys = {r["key"] for r in old["rows"]}
    clash = [i for i in added if N[i]["key"] in oldkeys]
    allk = [r["key"] for r in new["rows"]]
    chk("(2) %d kept questions, every one's key unchanged but the %d the owner moved (384.42: 5, 384.47: 72 into Chapter 1) (%d moved); %d new, none clashing (%s); all keys unique" % (len(kept), len(MOVED_BY_OWNER), len(moved), len(added), clash[:3]),
        len(kept) == 1776 - len(REMOVED_BY_OWNER) and moved == sorted(MOVED_BY_OWNER) and len(added) == 36 and not clash and len(set(allk)) == len(allk), moved[:5])
    # (3)
    oq = {q["id"]: q for q in ob["questions"]}; nq = {q["id"]: q for q in nb["questions"]}
    reworded = [i for i in kept if oq[i]["question"] != nq[i]["question"]]; reexp = [i for i in kept if oq[i]["explanation"] != nq[i]["explanation"]]
    shows = [i for i in N if N[i]["q"] != N[i]["bq"] or N[i]["expl"] != N[i]["be"] or N[i]["ans"] != N[i]["ba"]]
    newtext = [i for i in reworded if N[i]["q"] != nq[i]["question"]] + [i for i in reexp if N[i]["expl"] != nq[i]["explanation"]]
    answers = [i for i in kept if O[i]["ans"] != N[i]["ans"]]
    chk("(3) %d reworded questions and %d explanations show the new text; everything shown is the bank's word for word; no answer changed" % (len(reworded), len(reexp)),
        len(reworded) == 42 and len(reexp) == 3 and not shows and not newtext and not answers, {"shows": shows[:3], "newtext": newtext[:3], "answers": answers[:3]})
    # (4)
    gone = [i for i in ("ch12-008", "ch12-071", "ch4-040") if i in N]
    chk("(4) the 3 removed questions are gone (%s); a star on one comes off with a tombstone, a kept star stays" % (gone or "none left"),
        not gone and len(gone_keys) == 3 and all(k not in flags["flagged"] and k in flags["unflagged"] for k in gone_keys) and keep_key in flags["flagged"], flags)
    # (5)
    txt = pg.evaluate("()=>({ desc: NOVA_CLASS_INFO.ifc && NOVA_CLASS_INFO.ifc.desc, count: typeof ifcQuestionCountText === 'function' ? ifcQuestionCountText() : null })")
    chk("(5) the class list: %r" % txt["desc"], "Harris County Fire Code Amendments" in (txt["desc"] or "") and "1,797 questions" in (txt["desc"] or "") and txt["count"] == "1,797", txt)
    # (6) with the book
    if not WITH_BOOK:
        print("(6) skipped: set PDFJS_DIR and IFC_BOOK to run every new Finder question's code with the book")
    else:
        pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
        pg.set_input_files("#ifc-book-input", BOOK)
        for _ in range(600):
            if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
            pg.wait_for_timeout(250)
        acc = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? o.classList.contains('is-ok') : null; }")
        chk("(6) the owner's IFC is accepted against the 5.4.2 bank", acc is True, acc)
        pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }"); pg.wait_for_timeout(1200)
        SHOTS = os.environ.get("SHOTS", "")
        res = []
        for qid in added:
            r = pg.evaluate("""async(id)=>{ const w=ms=>new Promise(r=>setTimeout(r,ms));
              const i = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); if(i<0) return { id, err: 'missing' };
              document.querySelectorAll('.ifc-ref-probe').forEach(e=>e.remove());
              const box = document.createElement('div'); box.className='ifc-ref-probe'; box.style.cssText='position:fixed;left:0;top:0;width:420px;z-index:99999;background:#111';
              let node = null; try{ node = buildBankNote(QUESTIONS[i]); }catch(e){ return { id, err: String(e) }; }
              box.appendChild(node); document.body.appendChild(box);
              const d = box.querySelector('details.ifc-code'); if(d){ d.open = true; d.dispatchEvent(new Event('toggle')); }
              let cv = null; for(let k=0;k<120;k++){ cv = box.querySelector('.ifc-clips canvas'); if(cv && cv.width > 0) break; await w(250); }
              await w(600);
              const src = QUESTIONS[i].ifc.citation.source, label = QUESTIONS[i].ifc.citation.label;
              let yellow = 0, px = 0;
              box.querySelectorAll('.ifc-clips canvas').forEach(c => { try{ const g=c.getContext('2d'); const D=g.getImageData(0,0,c.width,c.height).data;
                for(let p=0;p<D.length;p+=16){ px++; const R=D[p],G=D[p+1],B=D[p+2]; if(R>200 && G>180 && B<150 && R-B>80) yellow++; } }catch(e){} });
              const locked = !!box.querySelector('.ifc-locked'); const ok = !!(cv && cv.width > 0) && !locked;
              return { id, label, src, ok, locked, yellow, px }; }""", qid)
            res.append(r)
            if SHOTS and r.get("ok"):
                os.makedirs(SHOTS, exist_ok=True); pg.locator(".ifc-ref-probe").screenshot(path=os.path.join(SHOTS, "%s.png" % qid))
        pg.evaluate("()=>document.querySelectorAll('.ifc-ref-probe').forEach(e=>e.remove())")
        bad = [r for r in res if not r.get("ok") or not r.get("yellow")]
        kinds = {"book": sum(1 for r in res if r.get("src") != "amendment"), "county": sum(1 for r in res if r.get("src") == "amendment")}
        chk("(6) all %d new Finder questions draw their code (%s), each with a highlight in it" % (len(res), kinds), len(res) == 36 and not bad, bad[:4])
    ctx.close(); br.close()
chk("(6) no page errors (%s)" % errs_all[:2], not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
