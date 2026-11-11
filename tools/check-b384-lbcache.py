#!/usr/bin/env python3
"""Build 384.23: the Leaderboard is not grey boxes on the first visit of a launch.
Madison: "The leaderboard, when clicking it, sometimes doesn't load right away, it's grey boxes at first." With nothing in memory (the first visit
after a launch) the board stood on placeholder rows until the cloud's first answer (1-6 seconds on a phone). The last board the device read from
the SERVER is kept in localStorage (class26e.lbcache.<academy|ifc>) and seeds the screen like memory does. Read off the page:
 (1) a board answered by the server is kept: the key holds >= 6 rows, each with a public id and no sync code;
 (2) after a relaunch (page reloaded, the cloud never answering), opening the Leaderboard shows the real rows within half a second - no placeholder
     rows, the classmates' names there, the column header there;
 (3) with no kept board (first ever visit) the placeholders still show, so (2) is the cache and nothing else;
 (4) a kept board more than a week old is not used (placeholders);
 (5) a snapshot that only came from Firestore's CACHE is not kept (the key stays empty);
 (6) the live answer still replaces the kept rows (a later answer with different people replaces them, nobody from the old copy is left over);
 (7) no page errors.
Run:  python3 tools/check-b384-lbcache.py   (--against OLD/index.html must FAIL)"""
import os, sys, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
ANSWER = """(arg)=>{ const names=arg.names, fromCache=!!arg.fromCache;
  window.__docs = names.map((n,i)=>({ id:'tstpub'+String(arg.base+i).padStart(6,'0'), data:()=>Object.assign({}, boardNumbersOf(store), { firstName:n, avatarChar:'ninja', level:5+i, points:900-i*50, weekPoints:100-i }) }));
  onSnapshotResilient = function(ref, onNext){ setTimeout(()=>onNext({ metadata:{ fromCache }, forEach:f=>window.__docs.forEach(f) }), 120); return function(){}; }; }"""
NEVER = "()=>{ onSnapshotResilient = function(){ return function(){}; }; }"
ROWS = """()=>{ const r=document.querySelector('#stage .rank-rows'); if(!r) return null;
  return { real:r.querySelectorAll(':scope > .rank-row[data-pub]').length, skel:r.querySelectorAll(':scope > .rank-row-skel').length, head:!!r.querySelector(':scope > .rank-head, :scope > .rank-row-head, :scope > .rank-head-skel'),
           names:[...r.querySelectorAll('.rank-name')].map(e=>e.textContent.trim()).slice(0,12) }; }"""
NAMES1 = ["Avery", "Jordan", "Kim", "Lee", "Sam", "Pat", "Chris", "Dana"]
NAMES2 = ["Rowan", "Quinn", "Ellis", "Harper", "Blake", "Reese", "Skyler", "Morgan"]
def open_board(pg, mode, names=None, base=0, fromCache=False, wait=1500):
    if mode == "answer": pg.evaluate(ANSWER, {"names": names, "base": base, "fromCache": fromCache})
    else: pg.evaluate(NEVER)
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(wait)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.evaluate("()=>{ try{ store.leaderboardOptIn = true; }catch(e){} }")
    # (3) first ever visit, the cloud never answers: placeholders
    open_board(pg, "never", wait=700); r3 = pg.evaluate(ROWS)
    chk("(3) no kept board: the placeholders show (%s)" % r3, r3 and r3["skel"] > 0, r3)
    # (5) a cache-only snapshot is not kept
    open_board(pg, "answer", NAMES1, 0, fromCache=True)
    k5 = pg.evaluate("()=>localStorage.getItem('class26e.lbcache.academy')")
    chk("(5) a snapshot that came from Firestore's cache is not kept", not k5, k5 and k5[:80])
    # (1) a server answer is kept
    pg.evaluate("()=>{ lbCacheWroteAt = 0; }")
    open_board(pg, "answer", NAMES1, 0, fromCache=False)
    raw = pg.evaluate("()=>localStorage.getItem('class26e.lbcache.academy')")
    o = json.loads(raw) if raw else {}
    chk("(1) a server answer is kept: %d rows with public ids" % len(o.get("rows", [])), len(o.get("rows", [])) >= 6 and all(x.get("pub") for x in o["rows"]), raw and raw[:100])
    chk("(1) ...and carries no sync code (nothing in it is the account's code)", raw and pg.evaluate("()=>!!syncCode && localStorage.getItem('class26e.lbcache.academy').indexOf(String(syncCode)) < 0"), "")
    # (2) a relaunch: the cloud never answers, the kept rows are up at once
    pg.reload(); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub(); try{ store.leaderboardOptIn = true; }catch(e){} }")
    open_board(pg, "never", wait=500); r2 = pg.evaluate(ROWS)
    chk("(2) after a relaunch the kept rows are up within half a second, no placeholders (%s)" % (r2 and {k: r2[k] for k in ("real", "skel", "head")}),
        r2 and r2["real"] >= 6 and r2["skel"] == 0 and r2["head"] and "Avery" in " ".join(r2["names"]), r2)
    # (6) the live answer replaces them
    open_board(pg, "answer", NAMES2, 20, fromCache=False, wait=1500); r6 = pg.evaluate(ROWS)
    chk("(6) a later server answer replaces the kept rows (%s)" % (r6 and r6["names"][:4]), r6 and "Rowan" in " ".join(r6["names"]) and "Avery" not in " ".join(r6["names"]), r6)
    # (4) a kept board older than a week is not used
    pg.evaluate("()=>{ const o=JSON.parse(localStorage.getItem('class26e.lbcache.academy')); o.t=Date.now()-8*864e5; localStorage.setItem('class26e.lbcache.academy', JSON.stringify(o)); }")
    pg.reload(); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub(); try{ store.leaderboardOptIn = true; }catch(e){} }")
    open_board(pg, "never", wait=600); r4 = pg.evaluate(ROWS)
    chk("(4) a kept board a week old is not used (%s)" % (r4 and {k: r4[k] for k in ("real", "skel")}), r4 and r4["skel"] > 0, r4)
    chk("(7) no page errors", not errs, errs[:3])
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
