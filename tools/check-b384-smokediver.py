#!/usr/bin/env python3
"""Build 384.20: the Smoke Diver (Fire Code's `masked`, challenge `retake100`) is not taken from an account that earned it.

384 r23 stopped a Fire Code account holding the Smoke Diver on counters that were not its own (an inherited 640 retakes, Game's
Hardcore units): `ifcChallengeClamp` holds `retakenQuestions` to what the account's own record supports. The bound it used was
"every retake follows a miss, so retakes <= misses on record". That is not so. A Drill question missed and then answered again counts a
retake AT ONCE (and one miss), and "Retake missed questions" counts that same question a SECOND time when it is retaken, with no new
miss: two retakes for one miss is ordinary play. So an account that missed 60 questions in a Drill and retook them all holds 120
retakes - the Smoke Diver, honestly - and the clamp put it back to 60, locked the character, took it off the avatar, and (because the
document and its __floor are written from the clamped copy) took the count off the cloud too.

 (A) THE INVARIANT, FROM THE APP'S OWN FLOW: a Drill whose every question is missed once and then answered, then "Retake missed
     questions" answered right, in Fire Code: the retakes read off the page are MORE than the misses on record (so "retakes <= misses"
     is not an invariant) and no more than twice them (the raw counter ticks twice for one miss, which is why the clamp holds a count to the misses, not to twice them: 384.24);
 (B) THE CLAMP'S BOUND, read off the page: a store with M misses on record keeps a count of 2M and is held to 2M above it, whatever
     the answers (it is still <= answers given); the academy's store is not touched at all;
 (C) AN HONEST EARN ABOVE ITS MISSES IS KEPT: a Fire Code account with 120 retakes on 60 misses and 400 answers (the shape (A) makes)
     keeps the Smoke Diver, wears it, has it written to the cloud document and its floor at 120, and still has it after another boot
     and after a cloud merge;
 (D) THE INHERITED COUNT IS STILL CAUGHT: 640 retakes and twelve Hardcore units on 5 misses are put at what its own record supports,
     the character is locked and not worn (r23's check B).
Run:  python3 tools/check-b384-smokediver.py [--against OLD/index.html]     (--against 384.19 must FAIL)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-fcchallenges.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
exec(compile(_src, os.path.join(HERE, "check-b384-fcchallenges.py"), "exec"), globals())

# the page's own numbers
BOUND = """()=>{ const mk = (m, a, r) => ({ stats: { x: { n: 9, m: m, r: [] } }, lifetime: { answered: a }, retakenQuestions: r, unitGameBeat: {} });
  const run = (m, a, r) => { const d = mk(m, a, r); const ch = ifcChallengeClamp(d); return { kept: d.retakenQuestions, changed: ch }; };
  return { two: run(10, 999, 10), over: run(10, 999, 11), way: run(10, 999, 640), few: run(10, 6, 20), zero: run(0, 999, 5) }; }"""

# a Drill missed once on every question then answered, finished; then Retake missed questions, answered right
FLOW = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
  const until = async (f, ms) => { const t0 = Date.now(); while(Date.now() - t0 < (ms || 12000)){ try{ if(f()) return true; }catch(e){} await W(80); } return false; };
  const sum = () => Object.keys(store.stats || {}).reduce((n, k) => n + ((store.stats[k] && store.stats[k].m) || 0), 0);
  try{
    theme.autoAdvance = false;
    const unit = topicsIn(QUESTIONS).map(u => [u, unitQuestionCount(u)]).filter(x => x[1] >= 6).sort((a, b) => a[1] - b[1])[0][0];
    const idx = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && inWholeUnit(QUESTIONS[i])).slice(0, 8);
    out.before = { r: store.retakenQuestions || 0, m: sum(), a: store.lifetime.answered };
    cfg.mode = 'drill'; cfg.units = [unit]; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'up'; cfg.flashcards = false;
    const play = async (n, miss) => { for(let k = 0; k < n; k++){
      await until(() => document.querySelector('.qpanel .choice') && !document.querySelector('.qpanel .choice[disabled]'));
      const qi = order[pos], right = correctSlot(qi), wrong = right === 0 ? 1 : 0;
      if(miss){ choose(wrong); await W(260); }
      choose(right); await W(300); advance(); await W(420); } };
    beginRun(freshOrder(idx), null, null);
    await until(() => document.querySelector('.qpanel .choice') && runStartTime != null);
    await play(idx.length, true);
    await until(() => !testInProgress || document.querySelector('.rs-screen'), 15000);
    out.afterDrill = { r: store.retakenQuestions || 0, m: sum() };
    const missed = freshOrder(idx);   // every question in the run was missed once
    beginRun(missed, 'Missed questions', null, true);
    await until(() => document.querySelector('.qpanel .choice') && runStartTime != null);
    await play(missed.length, false);
    await until(() => !testInProgress || document.querySelector('.rs-screen'), 15000);
    out.afterRetake = { r: store.retakenQuestions || 0, m: sum(), a: store.lifetime.answered };
    out.n = idx.length;
  }catch(e){ out.threw = String(e && e.stack || e).slice(0, 300); }
  return out; }"""

def worn_unlocked(p): return p["maskedLocked"] is False and p["avatar"] == p["maskedId"]

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])

    # ---------------- (A) the invariant, from the app's own flow ----------------
    with section("A"):
        G["academy"].clear(); G["academy"].update(heavy_academy(retakenQuestions=0, unitGameBeat={}, stats={}))
        small = fc_base(retakenQuestions=0, stats={}, lifetime={"answered": 0, "correct": 0, "drillPlays": 0, "examPlays": 0, "gamePlays": 0, "perfectTests": 0,
                        "currentStreak": 0, "longestStreak": 0, "points": 0, "fullTests": 0})
        set_ifc(small)
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
        pg.wait_for_timeout(2500)
        f = pg.evaluate(FLOW)
        chk("A the flow ran (%s questions, no exception)" % f.get("n"), not f.get("threw") and f.get("n", 0) >= 6, f)
        d, a = f["afterDrill"], f["afterRetake"]
        chk("A a Drill missed once and answered again counts one retake and one miss per question (retakes %d, misses %d, questions %d)" % (d["r"], d["m"], f["n"]),
            d["r"] == f["n"] and d["m"] == f["n"], f)
        chk("A then Retake missed questions, answered right, counts each AGAIN with no new miss: retakes %d are more than the %d misses on record" % (a["r"], a["m"]),
            a["r"] == 2 * f["n"] and a["m"] == f["n"] and a["r"] > a["m"], f)
        chk("A and no more than twice the misses, nor more than the answers given (%d <= 2 x %d, <= %d)" % (a["r"], a["m"], a["a"]), a["r"] <= 2 * a["m"] and a["r"] <= a["a"], f)
        chk("A no script error", not errs, errs)
        ctx.close()

    # ---------------- (B) the clamp's bound ----------------
    with section("B"):
        set_ifc(fc_base())
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
        pg.wait_for_timeout(2500)
        b = pg.evaluate(BOUND)
        chk("B 10 misses: a count of 10 is kept, untouched (%s)" % b["two"], b["two"]["kept"] == 10 and b["two"]["changed"] is False, b)
        chk("B 11 is held to 10, and 640 to 10 (%s / %s)" % (b["over"], b["way"]), b["over"]["kept"] == 10 and b["way"]["kept"] == 10, b)
        chk("B and never above the answers given (6 answered: %s), nor anything on no misses (%s)" % (b["few"], b["zero"]), b["few"]["kept"] == 6 and b["zero"]["kept"] == 0, b)
        chk("B no script error", not errs, errs)
        ctx.close()
        G["academy"].clear(); G["academy"].update(heavy_academy(avatarChar="masked", stats={"a": {"n": 3, "m": 1, "r": []}}))
        ctx, pg, errs = G["page"](br, G["init"]("academy"), seed=cloud_with())
        pg.wait_for_timeout(2500)
        p = probe(pg)
        chk("B the academy's 640 retakes on 1 miss are its own (rule is Fire Code's alone): %s retakes, Masked One unlocked" % p["retaken"], p["cls"] == "academy" and p["retaken"] == 640 and p["maskedLocked"] is False, p)
        ctx.close()

    # ---------------- (C) an honest earn above its misses is kept ----------------
    with section("C"):
        G["academy"].clear(); G["academy"].update(heavy_academy())
        real = fc_base(retakenQuestions=100, avatarChar="masked", lifetime={"answered": 400, "correct": 270, "drillPlays": 12, "examPlays": 3, "gamePlays": 0,
                       "perfectTests": 0, "currentStreak": 0, "longestStreak": 9, "points": 2600, "fullTests": 0},
                       unlocksShown={"chars": ["masked"], "banners": [], "fx": []})
        # (384.40) the challenge counts 100 DIFFERENT questions answered after a miss: real keys of the bank, each missed and answered again
        _c, _p, _e = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
        _rk = _p.evaluate("KEYS.slice(0, 300)"); _c.close()
        real["stats"] = {_rk[i]: {"n": 5, "m": 2, "r": []} for i in range(100)}
        cd = json.loads(json.dumps(real)); cd["lastModified"] = now - 300000
        set_ifc(real)
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with(fire=cd, floor=cd))
        pg.wait_for_timeout(2500); p = settle(pg)
        chk("C the server's copy is in (the rule waits for it)", p["confirmed"], p)
        chk("C 100 retakes on %d misses and %d answers: kept, Smoke Diver unlocked and still worn (retakes %s)" % (p["misses"], p["answered"], p["retaken"]),
            p["misses"] == 200 and p["retaken"] == 100 and worn_unlocked(p) and "masked" in p["shown"], p)
        pg.wait_for_timeout(6500); p = probe(pg)
        chk("C written to the cloud document and its floor as 100 (%s / %s)" % (p["docRetaken"], p["floorRetaken"]), p["docRetaken"] == 100 and p["floorRetaken"] == 100, p)
        pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); p = settle(pg)
        chk("C after another boot", p["retaken"] == 100 and worn_unlocked(p), p)
        back = pg.evaluate("""()=>{ const hi = JSON.parse(JSON.stringify(store)); hi.lastModified = Date.now() + 5000; syncSameAccount(hi); return { retaken: store.retakenQuestions, locked: isLockedCharacter('masked') }; }""")
        chk("C and after a cloud merge (%s)" % back, back["retaken"] == 100 and back["locked"] is False, back)
        chk("C no script error", not errs, errs)
        ctx.close()

    # ---------------- (D) the inherited count is still caught ----------------
    with section("D"):
        G["academy"].clear(); G["academy"].update(heavy_academy())
        wrong = fc_base(retakenQuestions=640, unitGameBeat={u: {"easy": True, "average": True, "hardcore": True} for u in UNITS}, avatarChar="masked",
                        pendingCharUnlocks=["masked"], unlocksShown={"chars": ["masked", "ghost"], "banners": [], "fx": []}, seenUnlocks={"chars": ["masked"], "banners": [], "fx": []})
        wrong["stats"] = {"q%d" % i: {"n": 3, "m": 1, "r": []} for i in range(5)}
        cd = json.loads(json.dumps(wrong)); cd["lastModified"] = now - 300000
        set_ifc(wrong)
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with(fire=cd, floor=cd))
        pg.wait_for_timeout(2500); p = settle(pg)
        chk("D 640 retakes on %d misses and %d answers are put at what the record supports (%s <= misses), no Hardcore, Smoke Diver locked and not worn" % (p["misses"], p["answered"], p["retaken"]),
            p["confirmed"] and p["retaken"] <= p["misses"] and p["retaken"] < 100 and p["hc"] == 0 and p["maskedLocked"] is True and p["avatar"] != p["maskedId"], p)
        chk("D no script error", not errs, errs)
        ctx.close()
    br.close()

print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
