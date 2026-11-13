#!/usr/bin/env python3
"""Build 384.103: Review test - the test you just took, every question, from its results.

Madison: "After you finish a test (you get the 100 or finish all the retakes, did them all finally), add a button for review test or
something and then you can review the test you just took ya know. Make this good."

Every run here is PLAYED: beginRun() and a tap on a choice, question by question (a wrong one first where the gate means to miss),
the results' own buttons pressed once they are armed (Continue to review, Retake missed questions, the review button) - never a run
state written by hand and handed to summarize(). Shape, not words: buttons are found by what they do and where they sit, never by
their labels; the right answers are the bank's own choice text; what was picked first is what the gate tapped.

  A. A Drill (academy, iPhone 17 Pro Max 440x956, the reveal played and tapped through): 3 missed on the test, 1 of those missed again
     on retake 1, cleared on retake 2.
     A1 the results of the test and of retake 1 (misses left) carry no review button; the results of the retake that clears the last
        miss carry exactly one, first in the row and its lead (#nextbtn, not ghost), with Re-run and Main menu still after it
     A2 it opens the whole ORIGINAL test: every question of it once, in the order it was asked - not the retake's questions
     A3 each question says how it went: right first time, or the retake it was answered right on (its round, and that number in its
        tag); the two kinds are told apart
     A4 the answers: the correct one is the bank's; a first-time question shows the answer given (the right one) and no second line;
        a retaken one shows the FIRST answer given - the one the gate tapped wrong - beside the correct one
     A5 the summary: the grade (the test's), a time, "first try" N / total and the retaken count, read off the page
     A6 the filter (the app's pill switcher, role=tab): three segments whose counts are all / retaken / first try; each shows exactly
        its questions, in test order; the segment picked says so (aria-selected)
     A7 each question has its star (a 44px target); a tap stars it and a second unstars it
     A8 back and forth: the lead goes back to the results, drawn at once (rs-done, nothing replayed), its buttons as before; the
        review opens again the same, and the filter last picked is still picked; twice over
     A9 Re-run from those results still starts the full test (not a retake)
  B. A 100% first time (academy, iPad Pro 11" 834x1194): the review button leads the results; the review lists every question as
     right first time, with no filter (nothing to split); its other button goes to Main menu (Home)
  C. A Mock with misses (academy, 375x667): Continue to review still leads and the review button comes second, quieter (ghost), then
     Re-run and Main menu; the review marks the misses with the answer tapped; Continue to review still opens just the misses
  D. Fire Code (Exhibit B, both missed and retaken): every question carries its code box (the card's own .ifc-ref); a retaken
     question's code opens and draws its picture (the county booklet ships with the app; pdf.js is served from PDFJS_DIR) inside its
     card, with no sideways page scroll
  E. A 50-question Practice test (exam, iPad Pro 11"): all 50 listed in order, the misses marked; the end of the list and its
     buttons are reached by scrolling; Back to results works from there
  F. The screen at 320x568, 375x667, 440x956, 956x440, 834x1194, 1194x834: no sideways page scroll, every segment's words inside
     its segment, every card inside the page, the buttons and stars 44px or more

  python3 tools/check-b384-reviewtest.py [--against REV|FILE] [--only A,B,...]
--against origin/main must FAIL (no review button anywhere, so A-F fail); this build ALL PASS."""
import importlib.util, json, mimetypes, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
args = sys.argv[1:]
ONLY = None
if "--only" in args:
    i = args.index("--only"); ONLY = set(args[i + 1].split(",")); del args[i:i + 2]
AG = []
if "--against" in args:
    i = args.index("--against"); a = args[i + 1]; del args[i:i + 2]
    if not os.path.isfile(a):
        tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "reviewtest-against-%d.html" % os.getpid())
        open(tmp, "wb").write(subprocess.check_output(["git", "-C", ROOT, "show", a + ":index.html"]))
        a = tmp
    AG = ["--against", os.path.abspath(a)]
sys.argv = [sys.argv[0]] + AG
_spec = importlib.util.spec_from_file_location("cb", HERE + "/check-behaviour.py")
cb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
# a 10MB page on a busy machine: the load gets three minutes, not Playwright's thirty seconds
_open_page = cb.open_page
def _open_page_patient(ctx):
    pg = _open_page(ctx); pg.set_default_navigation_timeout(180000); return pg
cb.open_page = _open_page_patient

PDFJS = (os.environ.get("PDFJS_DIR") or "/tmp/claude-0/-home-user/920022cb-51dc-5785-b32b-503aff219f98/scratchpad/pdfjs549/package").rstrip("/") + "/"
HAVE_PDFJS = os.path.exists(PDFJS + "build/pdf.min.mjs")

ok = True
def ck(name, cond, detail=""):
    global ok
    print("  %s %s%s" % ("PASS" if cond else "FAIL", name, ("  -> " + str(detail)[:900]) if (detail != "" and not cond) else ""), flush=True)
    if not cond: ok = False
def want(k): return ONLY is None or k in ONLY

# ---- playing a test, in the page ------------------------------------------------------------------------------------------
# o: { unit | all+n, mode, practice, reduce, miss: [[positions to miss on the test], [on retake 1], ...] }
# Drill: a miss is a wrong choice tapped first, then the right one. Exam: the wrong choice. Each round's record: the order as asked,
# what was missed (and what the app counted missed), the choice tapped wrong (the bank's index), the results' buttons.
PLAY = r"""async (o) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const until = async (f, ms) => { for(let t = 0; t < ms; t += 100){ try{ const v = f(); if(v) return v; }catch(e){} await wait(100); } return null; };
  const armed = () => { const a = [...document.querySelectorAll('#stage .rs-final')]; return a.length && a.every(x => !x.classList.contains('rs-unarmed')) && Date.now() > (typeof rsTapGuardUntil === 'number' ? rsTapGuardUntil : 0); };
  const tidy = () => document.querySelectorAll('#intro-pop, .app-banner, #tour-overlay, #tour-tooltip').forEach(n => n.remove());
  theme.autoAdvance = true; theme.reduceMotion = !!o.reduce; theme.muteBanners = !!o.reduce; try{ applyTheme(); }catch(e){}
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour'].forEach(k => store[k] = true);
  saveStore();
  cfg.mode = o.mode || 'drill'; cfg.source = 'all'; cfg.size = 0; cfg.versions = {};
  let pool;
  if(o.all){ pool = freshOrder(QUESTIONS.map((q, i) => i)).slice(0, o.n); cfg.units = topicsIn(QUESTIONS); }
  else { pool = freshOrder(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === o.unit && inWholeUnit(QUESTIONS[i]))); cfg.units = [o.unit]; }
  beginRun(pool, null, o.practice ? PRACTICE_TEST_MINUTES : null);
  const rounds = [];
  const playRound = async (missPos) => {
    await until(() => document.querySelector('#stage .qpanel .choice') && !document.querySelector('#teststart-overlay'), 30000);
    const rec = { order: order.slice(), missed: [], wrongOrig: {} };
    let last = -1, guard = 0;
    while(testInProgress && guard++ < 6000){
      tidy();
      if(pos !== last && pos < order.length && document.querySelectorAll('#stage .qpanel').length === 1 && document.querySelector('#stage .qpanel .choice')){
        await wait(120);
        if(document.querySelectorAll('#stage .qpanel').length !== 1) continue;
        const k = pos, qi = order[k], right = correctSlot(qi), n = optionOrder(qi).length;
        const tap = s => { const c = document.querySelector('#stage .qpanel .choice[data-index="' + s + '"]'); if(c) c.click(); return !!c; };
        last = k;
        if(missPos.indexOf(k) >= 0){
          const wrong = (right + 1) % n;
          rec.missed.push(qi); rec.wrongOrig[qi] = optionOrder(qi)[wrong];
          tap(wrong);
          if(runMode !== 'exam'){ await wait(450); tap(right); }
        } else tap(right);
      }
      await wait(90);
    }
    await until(() => document.querySelector('#stage .rs-final button'), 90000);
    for(let i = 0; i < 600 && !document.querySelector('.rs-rewards.rs-done'); i++){
      const sp = document.querySelector('.rs-spot.is-up');
      if(sp) (sp.__nova ? sp.__nova.skip() : sp.click()); else document.querySelector('#stage .rs-screen')?.click();
      await wait(150);
    }
    await until(armed, 20000); await wait(250);
    rec.appMissed = (lastRunResult && lastRunResult.missed || []).slice();
    rec.btns = [...document.querySelectorAll('#stage .rs-final button')].map(b => ({ cls: b.className, id: b.id, review: b.classList.contains('rs-testreview-go') }));
    return rec;
  };
  rounds.push(await playRound(o.miss[0] || []));
  for(let r = 1; r < o.miss.length; r++){
    await until(armed, 20000);
    document.querySelector('#stage .rs-continue').click();
    await until(() => document.querySelector('#stage .rs-review'), 10000);
    await until(armed, 20000);
    document.querySelector('#stage .rs-final #nextbtn').click();
    rounds.push(await playRound(o.miss[r] || []));
  }
  return rounds;
}"""

# press a results / review button once its row is armed (rsArmIn) - the way a person's tap gets through
PRESS = r"""async (sel) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for(let i = 0; i < 200; i++){
    const b = document.querySelector(sel), row = b && b.closest('.rs-final');
    if(b && row && !row.classList.contains('rs-unarmed') && Date.now() > (typeof rsTapGuardUntil === 'number' ? rsTapGuardUntil : 0)){ b.click(); return true; }
    await wait(100);
  }
  return false; }"""
REVIEW_BTN = "#stage .rs-final .rs-testreview-go"
ON_REVIEW = "()=>!!document.querySelector('#stage .rs-testreview')"

# what the review screen holds, read off the page
READ = r"""() => {
  const p = document.querySelector('#stage .rs-testreview'); if(!p) return null;
  const txt = e => e ? [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim() : null;
  const items = [...p.querySelectorAll('.rs-tr-list > .rs-q')].map(li => ({
    qi: +li.dataset.qi, how: li.dataset.how, round: li.dataset.round == null ? null : +li.dataset.round, hidden: li.hidden || !li.getClientRects().length,
    tag: (li.querySelector('.rs-q-tag') || {}).textContent || '', tagCls: (li.querySelector('.rs-q-tag') || {}).className || '',
    yours: txt(li.querySelector('.rs-q-yours')), right: txt(li.querySelector('.rs-q-right')),
    yoursOk: !!(li.querySelector('.rs-q-yours') && li.querySelector('.rs-q-yours').classList.contains('is-right')),
    bankRight: String(QUESTIONS[+li.dataset.qi].choices[QUESTIONS[+li.dataset.qi].answer]),
    star: (() => { const s = li.querySelector('.flagbtn'); if(!s) return null; const r = s.getBoundingClientRect(); return { w: r.width, h: r.height }; })(),
    ifc: !!li.querySelector('.ifc-ref details.ifc-code') }));
  const tabs = [...p.querySelectorAll('.rs-tr-filter > .rs-tab')].map(t => ({ on: t.getAttribute('aria-selected') === 'true', role: t.getAttribute('role'),
    count: +(t.querySelector('.rs-tab-count') || {}).textContent.replace(/[^0-9]/g, '') }));
  const stats = {}; p.querySelectorAll('.rs-tr-stat').forEach(s => { stats[s.dataset.stat] = (s.querySelector('.rs-tr-val') || {}).textContent || ''; });
  const btns = [...p.querySelectorAll('.rs-final button')].map(b => ({ cls: b.className, id: b.id }));
  return { items, tabs, thumb: !!p.querySelector('.rs-tr-filter.has-seg-thumb'), stats, btns, screen: p.dataset.screen, top: scrollY };
}"""
nums = lambda s: [int(x) for x in re.findall(r"\d+", (s or "").replace(",", ""))]

def booted_ifc(br, w, h):
    acct = json.loads(cb.USED_ACCOUNT); acct["publicId"] = "xph5b57jbp5a"; acct["novaMet"] = 99
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
    if HAVE_PDFJS:
        def pdfjs_route(route, request):
            rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
            if not os.path.exists(p): return route.fulfill(status=404, body="")
            ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
            route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
        ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    raw = json.dumps(json.dumps(acct))
    ctx.add_init_script("try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
                        "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
                        "localStorage.setItem('class26e.ifc.drill.v1', %s);localStorage.setItem('class26e.drill.v1', %s);"
                        "localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                        "localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');}catch(e){}" % (raw, raw))
    pg = cb.open_page(ctx)
    pg.goto(cb.URL); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); __stub(); try{ store.savedCodeSaved = true; }catch(e){} document.querySelectorAll('#intro-pop, .app-banner').forEach(n=>n.remove()); }")
    return ctx, pg

def booted(br, w, h):
    ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT)
    pg.evaluate("()=>{ try{ store.savedCodeSaved = true; }catch(e){} document.querySelectorAll('#intro-pop, .app-banner').forEach(n=>n.remove()); }")
    return ctx, pg

def open_review(pg):
    if not pg.evaluate("(s)=>!!document.querySelector(s)", REVIEW_BTN): return False
    pg.evaluate(PRESS, REVIEW_BTN)
    try:
        pg.wait_for_function(ON_REVIEW, timeout=8000); pg.wait_for_timeout(500); return True
    except Exception:
        return False

def first_try_and_rounds(rounds):
    """from the gate's own record: each question of the test -> 0 (right first time) or the retake round it was right on"""
    test = rounds[0]["order"]; out = {}
    for qi in test:
        if qi not in rounds[0]["missed"]: out[qi] = 0; continue
        for r in range(1, len(rounds)):
            if qi in rounds[r]["order"] and qi not in rounds[r]["missed"]: out[qi] = r; break
    return out

def played_as_meant(label, rounds):
    ck("%s: the app counted exactly the misses the gate played, every round" % label,
       all(sorted(r["missed"]) == sorted(r["appMissed"]) for r in rounds), [(sorted(r["missed"]), sorted(r["appMissed"])) for r in rounds])

def check_review_items(label, rv, rounds, exam=False):
    test = rounds[0]["order"]; how = first_try_and_rounds(rounds)
    items = rv["items"] if rv else []
    ck("%s: the review lists every question of the test once, in the order it was asked" % label,
       [i["qi"] for i in items] == test, ([i["qi"] for i in items][:20], test[:20]))
    bad = []
    for it in items:
        r = how.get(it["qi"])
        if exam:
            want_how = "first" if it["qi"] not in rounds[0]["missed"] else "other"
            if it["how"] != want_how: bad.append(("how", it["qi"], it["how"], want_how))
        else:
            if r is None: bad.append(("not cleared?", it["qi"])); continue
            if it["how"] != ("first" if r == 0 else "other") or it["round"] != r: bad.append(("round", it["qi"], it["how"], it["round"], r))
            if r > 0 and nums(it["tag"]) != [r]: bad.append(("tag number", it["qi"], it["tag"], r))
            if r == 0 and nums(it["tag"]): bad.append(("tag carries a number", it["qi"], it["tag"]))
    ck("%s: each question is marked as it went - right first time, or the retake it was answered right on (and its tag says which)" % label
       if not exam else "%s: each question is marked right or missed as it was answered" % label, not bad and bool(items), bad[:6])
    firsts = [it for it in items if it["how"] == "first"]; others = [it for it in items if it["how"] == "other"]
    ck("%s: the two kinds are told apart (their tags differ in class)" % label,
       bool(items) and (not firsts or not others or ({i["tagCls"] for i in firsts}.isdisjoint({i["tagCls"] for i in others}))), ({i["tagCls"] for i in firsts}, {i["tagCls"] for i in others}))
    bad = []
    for it in items:
        if it["how"] == "first":
            if it["yours"] != it["bankRight"] or not it["yoursOk"] or it["right"] is not None: bad.append(("first", it["qi"], it["yours"], it["right"], it["bankRight"]))
        else:
            if it["right"] != it["bankRight"]: bad.append(("correct", it["qi"], it["right"], it["bankRight"]))
            if it.get("tappedText") is None or it["yours"] != it["tappedText"]: bad.append(("first answer", it["qi"], it["yours"], it.get("tappedText")))
            if it["yours"] == it["bankRight"] or it["yoursOk"]: bad.append(("first answer shown as right", it["qi"], it["yours"]))
    ck("%s: the correct answer is the bank's; a first-time question shows the answer given (right) alone; a missed one shows the first answer tapped beside the correct one" % label,
       not bad and bool(items), bad[:6])

def attach_tapped(pg, rv, rounds):
    """the bank's text of the choice the gate tapped wrong first, per question"""
    if not rv: return
    tapped = {str(k): v for k, v in rounds[0]["wrongOrig"].items()}
    texts = pg.evaluate("(m)=>{ const o = {}; Object.keys(m).forEach(k => { o[k] = String(QUESTIONS[+k].choices[m[k]]); }); return o; }", tapped)
    for it in rv["items"]:
        if str(it["qi"]) in texts: it["tappedText"] = texts[str(it["qi"])]

def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME, args=["--disable-gpu", "--disable-dev-shm-usage"])
        errs_all = []
        if want("A"):
            print("A. a Drill: 3 missed, 1 missed again on retake 1, cleared on retake 2 (iPhone 17 Pro Max, the reveal played)")
            ctx, pg = booted(br, 440, 956); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            rounds = pg.evaluate(PLAY, {"unit": "Identity Crimes", "miss": [[1, 4, 7], [0], []], "reduce": False})
            played_as_meant("A", rounds)
            rb = [[b["review"] for b in r["btns"]] for r in rounds]
            ck("A1: no review button while misses are left (the test, retake 1) - Continue to review leads there",
               not any(rb[0]) and not any(rb[1]) and all(r["btns"] and "rs-continue" in r["btns"][0]["cls"] for r in rounds[:2]), rb)
            last = rounds[-1]["btns"]
            ck("A1: on the results of the retake that clears the last miss, exactly one review button, first in the row and its lead, Re-run and Main menu after it",
               sum(rb[-1]) == 1 and last[0]["review"] and last[0]["id"] == "nextbtn" and "ghost" not in last[0]["cls"].split()
               and len(last) == 3 and all("ghost" in b["cls"].split() and not b["id"] for b in last[1:]), last)
            opened = open_review(pg)
            ck("A2: it opens the review", opened)
            rv = pg.evaluate(READ) if opened else None
            attach_tapped(pg, rv, rounds)
            check_review_items("A", rv, rounds)
            how = first_try_and_rounds(rounds); n = len(rounds[0]["order"]); nf = sum(1 for v in how.values() if v == 0)
            st = (rv or {}).get("stats", {})
            pct = round(nf / n * 100)
            ck("A5: the summary - the test's grade, a time, first try N / total, and how many were retaken",
               nums(st.get("grade")) == [pct] and re.match(r"^\d+:\d\d(:\d\d)?$", st.get("time", "")) and nums(st.get("first")) == [nf, n]
               and nums(st.get("other")) == [n - nf], (st, pct, nf, n))
            tabs = (rv or {}).get("tabs", [])
            ck("A6: the filter is the app's pill switcher with three segments, counting all / retaken / first try, the first picked",
               len(tabs) == 3 and all(t["role"] == "tab" for t in tabs) and [t["count"] for t in tabs] == [n, n - nf, nf]
               and tabs[0]["on"] and rv.get("thumb"), tabs)
            seen = {}
            for k in (1, 2, 0):
                if rv: pg.evaluate("(k)=>document.querySelectorAll('#stage .rs-tr-filter > .rs-tab')[k].click()", k); pg.wait_for_timeout(250)
                r2 = pg.evaluate(READ) if rv else None
                seen[k] = ([i["qi"] for i in r2["items"] if not i["hidden"]], [t["on"] for t in r2["tabs"]]) if r2 else None
            test = rounds[0]["order"]
            ck("A6: each segment shows exactly its questions, in test order, and is the one marked picked",
               bool(rv) and seen[1][0] == [q for q in test if how[q] > 0] and seen[2][0] == [q for q in test if how[q] == 0] and seen[0][0] == test
               and seen[1][1] == [False, True, False] and seen[2][1] == [False, False, True] and seen[0][1] == [True, False, False], seen)
            stars = [i["star"] for i in (rv or {}).get("items", [])]
            ck("A7: every question has its star, a 44px target", bool(stars) and all(s and s["w"] >= 44 and s["h"] >= 44 for s in stars), stars[:3])
            if rv:
                q0 = rv["items"][0]["qi"]
                was = pg.evaluate("(q)=>isFlagged(q)", q0)
                pg.evaluate("()=>document.querySelector('#stage .rs-tr-list > .rs-q .flagbtn').click()"); pg.wait_for_timeout(200)
                mid = pg.evaluate("(q)=>({ f: isFlagged(q), on: document.querySelector('#stage .rs-tr-list > .rs-q .flagbtn').classList.contains('on') })", q0)
                pg.evaluate("()=>document.querySelector('#stage .rs-tr-list > .rs-q .flagbtn').click()"); pg.wait_for_timeout(200)
                end = pg.evaluate("(q)=>isFlagged(q)", q0)
                ck("A7: a tap on a star stars that question, and a second tap takes it off", mid["f"] == (not was) and mid["on"] == (not was) and end == was, (was, mid, end))
            else:
                ck("A7: a tap on a star stars that question", False, "no review")
            # A8 back and forth
            res_btns = [b["cls"].replace(" is-quietfocus", "") for b in last]
            loops = []
            for lap in range(2):
                if not rv: break
                pg.evaluate("()=>document.querySelectorAll('#stage .rs-tr-filter > .rs-tab')[1].click()"); pg.wait_for_timeout(200)
                back_btns = pg.evaluate(READ)["btns"]
                pg.evaluate(PRESS, "#stage .rs-testreview .rs-final #nextbtn")
                try: pg.wait_for_function("()=>!!document.querySelector('#stage .rs-rewards.rs-done')", timeout=3000); back = True
                except Exception: back = False
                st2 = pg.evaluate("()=>({ spots: document.querySelectorAll('.rs-spot, .bc-scene, .fl-scene, .hfx-stage').length, landing: document.querySelectorAll('#stage .rs-land:not(.rs-in-now)').length,"
                                  " btns: [...document.querySelectorAll('#stage .rs-final button')].map(b => b.className.replace(' is-quietfocus', '')) })")
                again = open_review(pg)
                r3 = pg.evaluate(READ) if again else None
                loops.append({ "backBtns": len(back_btns), "back": back, "st": st2, "again": again,
                               "same": bool(r3) and [i["qi"] for i in r3["items"]] == test,
                               "kept": bool(r3) and [t["on"] for t in r3["tabs"]] == [False, True, False] and [i["qi"] for i in r3["items"] if not i["hidden"]] == [q for q in test if how[q] > 0] })
            ck("A8: back and forth twice - the review's lead goes back to the results drawn at once (nothing lands or plays again, the same buttons), the review opens again the same, its filter still picked",
               len(loops) == 2 and all(l["backBtns"] == 2 and l["back"] and l["st"]["spots"] == 0 and l["st"]["landing"] == 0 and l["st"]["btns"] == res_btns
                                       and l["again"] and l["same"] and l["kept"] for l in loops), (loops, res_btns))
            # A9: Re-run from the results starts the whole test again
            if rv:
                pg.evaluate(PRESS, "#stage .rs-testreview .rs-final #nextbtn"); pg.wait_for_timeout(600)
                pg.evaluate(PRESS, "#stage .rs-final button:nth-child(2)")
                pg.wait_for_timeout(1500)
                rr = pg.evaluate("()=>({ on: testInProgress, retake: isMissedRetake, set: order.slice().sort((a,b)=>a-b) })")
                ck("A9: Re-run from those results starts the full test again (every question of it, not a retake)",
                   rr["on"] and not rr["retake"] and rr["set"] == sorted(test), rr)
            else:
                ck("A9: Re-run from those results starts the full test again", False, "no review")
            errs_all += errs; ctx.close()

        if want("B"):
            print("B. a 100% first time (iPad Pro 11\", reduce motion)")
            ctx, pg = booted(br, 834, 1194); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            rounds = pg.evaluate(PLAY, {"unit": "Identity Crimes", "miss": [[]], "reduce": True})
            played_as_meant("B", rounds)
            b = rounds[0]["btns"]
            ck("B: the review button leads a 100%'s results (first, #nextbtn, not ghost), Re-run and Main menu after it",
               len(b) == 3 and b[0]["review"] and b[0]["id"] == "nextbtn" and "ghost" not in b[0]["cls"].split() and all("ghost" in x["cls"].split() for x in b[1:]), b)
            opened = open_review(pg); rv = pg.evaluate(READ) if opened else None
            attach_tapped(pg, rv, rounds)
            check_review_items("B", rv, rounds)
            ck("B: every question right first time, and no filter - nothing to split", bool(rv) and all(i["how"] == "first" for i in rv["items"]) and not rv["tabs"]
               and nums(rv["stats"].get("grade")) == [100] and nums(rv["stats"].get("other")) == [0], (rv or {}).get("tabs"))
            if rv:
                pg.evaluate(PRESS, "#stage .rs-testreview .rs-final button:not(#nextbtn)")
                try: pg.wait_for_function("()=>!!document.querySelector('#stage [data-screen=\"home\"]')", timeout=5000); home = True
                except Exception: home = False
                ck("B: the review's other button goes to Main menu (Home)", home)
            else:
                ck("B: the review's other button goes to Main menu (Home)", False, "no review")
            errs_all += errs; ctx.close()

        if want("C"):
            print("C. a Mock with three missed (375x667, reduce motion)")
            ctx, pg = booted(br, 375, 667); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            rounds = pg.evaluate(PLAY, {"unit": "Identity Crimes", "mode": "exam", "miss": [[2, 5, 9]], "reduce": True})
            played_as_meant("C", rounds)
            b = rounds[0]["btns"]
            ck("C: Continue to review still leads; the review button second and quieter (ghost, full width); Re-run and Main menu after",
               len(b) == 4 and "rs-continue" in b[0]["cls"] and b[0]["id"] == "nextbtn" and b[1]["review"] and "ghost" in b[1]["cls"].split()
               and "rs-wide" in b[1]["cls"].split() and not b[1]["id"] and all("ghost" in x["cls"].split() for x in b[2:]), b)
            opened = open_review(pg); rv = pg.evaluate(READ) if opened else None
            attach_tapped(pg, rv, rounds)
            check_review_items("C", rv, rounds, exam=True)
            ck("C: the filter counts all / missed / right", bool(rv) and [t["count"] for t in rv["tabs"]] == [len(rounds[0]["order"]), 3, len(rounds[0]["order"]) - 3], (rv or {}).get("tabs"))
            if rv:
                pg.evaluate(PRESS, "#stage .rs-testreview .rs-final #nextbtn"); pg.wait_for_timeout(500)
                pg.evaluate(PRESS, "#stage .rs-final .rs-continue")
                try: pg.wait_for_function("()=>!!document.querySelector('#stage .rs-review:not(.rs-testreview)')", timeout=5000); cont = True
                except Exception: cont = False
                n = pg.evaluate("()=>document.querySelectorAll('#stage .rs-review:not(.rs-testreview) .rs-q').length") if cont else 0
                ck("C: Continue to review still opens just the misses", cont and n == 3, n)
            else:
                ck("C: Continue to review still opens just the misses", False, "no review")
            errs_all += errs; ctx.close()

        if want("D"):
            print("D. Fire Code, Exhibit B: missed and retaken, the code pictures (pdf.js %s)" % ("served locally" if HAVE_PDFJS else "NOT available: the picture is not checked"))
            ctx, pg = booted_ifc(br, 440, 956); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            cls = pg.evaluate("()=>BANK_CLASS")
            ck("D: the page is in the Fire Code class", cls == "ifc", cls)
            unit = "Exhibit B: Amendments to the International Building Code"
            rounds = pg.evaluate(PLAY, {"unit": unit, "miss": [[0, 3, 5], []], "reduce": True})
            played_as_meant("D", rounds)
            opened = open_review(pg); rv = pg.evaluate(READ) if opened else None
            attach_tapped(pg, rv, rounds)
            check_review_items("D", rv, rounds)
            ck("D: every question carries its code box", bool(rv) and all(i["ifc"] for i in rv["items"]), [i["ifc"] for i in (rv or {}).get("items", [])])
            if rv and HAVE_PDFJS:
                pg.evaluate("()=>{ const li = document.querySelector('#stage .rs-tr-list > .rs-q[data-how=other]'); li.querySelector('.ifc-code-sum').click(); li.scrollIntoView(); }")
                pic = None
                for _ in range(80):
                    pg.wait_for_timeout(250)
                    pic = pg.evaluate("""()=>{ const li = document.querySelector('#stage .rs-tr-list > .rs-q[data-how=other]'); const c = li.querySelector('.ifc-code-body canvas, .ifc-code-body img');
                      if(!c) return null; const r = c.getBoundingClientRect(), l = li.getBoundingClientRect();
                      return { w: r.width, h: r.height, inCard: r.left >= l.left - .5 && r.right <= l.right + .5, sw: document.documentElement.scrollWidth, vw: innerWidth, open: li.querySelector('details.ifc-code').open }; }""")
                    if pic and pic["h"] > 20: break
                ck("D: a retaken question's code opens and draws its picture inside its card, no sideways page scroll",
                   bool(pic) and pic["open"] and pic["h"] > 20 and pic["inCard"] and pic["sw"] <= pic["vw"], pic)
            elif rv:
                print("  SKIP the code picture: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149")
            errs_all += errs; ctx.close()

        if want("E"):
            print("E. a 50-question Practice test (iPad Pro 11\", reduce motion)")
            ctx, pg = booted(br, 834, 1194); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            rounds = pg.evaluate(PLAY, {"all": True, "n": 50, "mode": "exam", "practice": True, "miss": [[3, 10, 11, 20, 33, 47]], "reduce": True})
            played_as_meant("E", rounds)
            opened = open_review(pg); rv = pg.evaluate(READ) if opened else None
            attach_tapped(pg, rv, rounds)
            check_review_items("E", rv, rounds, exam=True)
            if rv:
                pg.evaluate("()=>window.scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(500)
                end = pg.evaluate("""()=>{ const li = [...document.querySelectorAll('#stage .rs-tr-list > .rs-q')].pop(), a = document.querySelector('#stage .rs-testreview .rs-final');
                  const r = li.getBoundingClientRect(), b = a.getBoundingClientRect(); return { y: scrollY, last: r.bottom <= innerHeight + 1 && r.bottom > 0, btns: b.bottom <= innerHeight && b.top >= 0 }; }""")
                pg.evaluate(PRESS, "#stage .rs-testreview .rs-final #nextbtn")
                try: pg.wait_for_function("()=>!!document.querySelector('#stage .rs-rewards.rs-done')", timeout=4000); back = True
                except Exception: back = False
                ck("E: the end of the list and its buttons are reached by scrolling, and Back to results works from there", end["y"] > 0 and end["last"] and end["btns"] and back, (end, back))
            else:
                ck("E: the end of the list and its buttons are reached by scrolling", False, "no review")
            errs_all += errs; ctx.close()

        if want("F"):
            print("F. the screen on six sizes (a Drill with one retaken, reduce motion)")
            LAY = r"""() => {
              const p = document.querySelector('#stage .rs-testreview'); if(!p) return null;
              const vw = innerWidth, bad = [];
              if(document.documentElement.scrollWidth > vw + 1) bad.push(['page scrolls sideways', document.documentElement.scrollWidth, vw]);
              p.querySelectorAll('.rs-tr-filter > .rs-tab').forEach(t => { const cs = getComputedStyle(t), inner = t.getBoundingClientRect();
                const l = inner.left + parseFloat(cs.paddingLeft) - 1, r = inner.right - parseFloat(cs.paddingRight) + 1;
                [...t.querySelectorAll('.tab-label, .rs-tab-count')].forEach(e => { const q = e.getBoundingClientRect(); if(q.width && (q.left < l || q.right > r)) bad.push(['segment words outside it', e.textContent, Math.round(q.left), Math.round(q.right), Math.round(l), Math.round(r)]); });
                if(inner.height < 44) bad.push(['segment under 44px', inner.height]); });
              p.querySelectorAll('.rs-card, .rs-q').forEach(c => { const r = c.getBoundingClientRect(); if(r.left < -.5 || r.right > vw + .5) bad.push(['card outside the page', c.className, r.left, r.right]); });
              p.querySelectorAll('.rs-final button, .flagbtn').forEach(b => { const r = b.getBoundingClientRect(); if(r.height < 44 || r.width < 44) bad.push(['under 44px', b.className, r.width, r.height]); });
              p.querySelectorAll('.rs-tr-stat').forEach(s => { const v = s.querySelector('.rs-tr-val'); if(v.scrollWidth > v.clientWidth + 1) bad.push(['a stat clipped', v.textContent]); });
              return bad; }"""
            for (w, h) in ((320, 568), (375, 667), (440, 956), (956, 440), (834, 1194), (1194, 834)):
                ctx, pg = booted(br, w, h); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                rounds = pg.evaluate(PLAY, {"unit": "Identity Crimes", "miss": [[2], []], "reduce": True})
                opened = open_review(pg)
                lay = pg.evaluate(LAY) if opened else None
                ck("F %dx%d: no sideways scroll, segment words inside their segments, cards inside the page, 44px targets" % (w, h), opened and lay == [], lay)
                errs_all += errs; ctx.close()

        ck("no page errors", not errs_all, errs_all[:4])
        br.close()
    cb.SERVER.shutdown()
    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
