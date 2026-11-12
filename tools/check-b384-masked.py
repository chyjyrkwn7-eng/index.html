#!/usr/bin/env python3
"""Build 384.46: the academy's Masked One (challenge `retake100`, "Retake 100 missed questions"), the Smoke Diver's academy twin.

The same hole as Fire Code's (384.40), read in the academy's own flow: in a Drill a wrong pick is followed by picking again until it is
right, and `choose()` recorded that moment as ONE miss (recordResult -> stats `m` + 1) and ONE retake (`attempts[qi] > 1` ->
retakenQuestions + 1). So `retakenQuestions` was the number of misses answered at the end of a Drill, and "Retake 100 missed questions"
was met by missing 100 answers: no question ever had to come back. (The owner's own academy account read 1,231 retakes on 1,088
misses.) The owner decided the rule must mean what it says and that anyone holding it without earning it loses it, everywhere.

The academy now counts DIFFERENT questions answered while a miss of them is on record (`retakeDistinctCount`): `store.retakenKeys` (written
in `choose()` before the answer's own miss is recorded), a question with two or more misses, and - a carry-over for what was earned before
keys existed - a question with exactly one miss and two or more answers whose miss is older than RETAKE_CARRY_BEFORE_MS (or has no stamp).
Worked out when read; the old counter is never read. The Hardcore door (10 units, retired game) is kept.

 (0) the fixture is the owner's shape: a counter far above 100, under 100 different questions retaken;
 (A) such an account (worn, queued, marked announced and seen, in the store, the account document and its floor): locked on every
     surface after the server's copy is in (card N of 100 and not Unlocked, not in the held list), not worn (the first starter, the rest
     of the look kept), not queued, not marked, the document and floor as written carry none of it; the same after another boot, after a
     second device's copy merges in (counter 3,000, worn, queued, marked) and what is written after;
 (B) the other doors: no cloud document yet; the floor alone holding it; a copy with no sync;
 (C) AN HONEST EARNER IS KEPT: 100 different questions by keys; by the record alone (two misses); by the carry-over (one miss, answered
     again, a stamp from before the cutoff or none); a mix; Hardcore on 10 units; kept = unlocked, card Unlocked, still worn, announced,
     in the document and floor, after another boot and a merge. 99 do not. One miss answered once does not count. A single miss
     stamped after the cutoff counts only through its key. Keys with no miss, or not in the bank, do not count;
 (D) THE APP'S OWN FLOW: a Drill with every question missed once and answered again counts NO retake (the old counter reads one per miss);
     a later Drill answered right counts each once; again, and a Retake run, add nothing;
 (E) NOTHING ELSE CHANGES: an academy account rich in other rewards: every challenge, rank and secret character other than the Masked One reads
     the same held / locked with and without retake evidence; no unlock pop-up, queue entry or mark appears for anyone as a result.
Run:  python3 tools/check-b384-masked.py [--against OLD/index.html]     (--against origin/main 384.45 must FAIL)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-smokediver2.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
exec(compile(_src, os.path.join(HERE, "check-b384-smokediver2.py"), "exec"), globals())

CUT_DEFAULT = 1794528000000   # 2026-11-13 00:00 UTC, RETAKE_CARRY_BEFORE_MS
OLDTS = 1790000000000         # 2026-09-21

def acad(**kw):
    """an academy account as it is after some use: its own copy of the owner's harness account, no Hardcore, nothing seeded"""
    a = json.loads(json.dumps(BASE))
    a.update({"retakenQuestions": 0, "unitGameBeat": {}, "challengeSeed289": True, "fullTestsSeeded": True, "lateHundosSeed312": True, "koiRevoked295": True,
              "hiveMoved384": True, "sheriffMoved324": True, "lastModified": now - 600000, "retakenKeys": [], "legacyChars": [],
              "pendingCharUnlocks": [], "unlocksShown": {"chars": [], "banners": [], "fx": []}, "seenUnlocks": {"chars": ["ghost"], "banners": [], "fx": []},
              "stats": {}})
    a["lifetime"] = dict(a["lifetime"], answered=5400, correct=4980, drillPlays=64, examPlays=22, fullTests=20)
    a.update(kw); return a

def cloud_ac(doc=None, floor=None):
    c = json.loads(json.dumps(G["CLOUD0"]))
    if doc is not None: c["progress"][CODE] = doc
    if floor is not None: c["progress"][CODE + "__floor"] = floor
    return c

def booted_ac(br, local, cloud):
    ctx, pg, errs = G["page"](br, G["init"]("academy", with_ifc=False, academy_copy=local), seed=cloud)
    pg.wait_for_timeout(2500)
    return ctx, pg, errs

def probe_extra(pg):
    return pg.evaluate("""()=>({ cls: window.NOVA_CLASS, cut: (typeof RETAKE_CARRY_BEFORE_MS === 'number') ? RETAKE_CARRY_BEFORE_MS : null,
      hc: (typeof hardcoreUnitsBeaten === 'function') ? hardcoreUnitsBeaten() : null })""")

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx, pg, errs = booted_ac(br, acad(), cloud_ac(acad()))
    RK = list(dict.fromkeys(pg.evaluate("KEYS.slice()")))   # unique: a few questions share a key
    X = probe_extra(pg)
    ctx.close()
    CUT = X["cut"] or CUT_DEFAULT
    chk("0 the academy bank gives enough question keys for a fixture (%d), class %s" % (len(RK), X["cls"]), len(RK) >= 600 and X["cls"] == "academy")

    def stats_of(spec):
        """spec: [(misses, answers, stamp, how_many)] -> {key: {n, m, r}} on real keys; stamp 'old' | 'none' | 'new'"""
        st, i = {}, 0
        for m, n, stamp, cnt in spec:
            for _ in range(cnt):
                r = [] if stamp == "none" else ([OLDTS + j for j in range(m)] if stamp == "old" else [CUT + 3600000 + j for j in range(m)])
                st[RK[i]] = {"n": n, "m": m, "r": r}; i += 1
        return st
    # his shape: lots of questions missed once and answered once (a wrong pick and the right one, the same moment), 60 missed twice or more,
    # 20 missed once and answered again; a counter of 1,231 on the misses
    HIS = [(0, 1, "none", 150), (1, 1, "old", 400), (1, 3, "old", 20), (2, 4, "old", 45), (3, 5, "old", 15)]
    his_stats = stats_of(HIS)
    his_m = sum(v["m"] for v in his_stats.values())
    HIS_COUNT = 80
    chk("0 the fixture is his shape: %d questions, %d misses on record, a counter of 1,231, and only %d different questions retaken" % (len(his_stats), his_m, HIS_COUNT),
        his_m == 400 + 20 + 90 + 45 and len(his_stats) == 630)
    def his(**kw):
        d = acad(retakenQuestions=1231, avatarChar="masked", stats=json.loads(json.dumps(his_stats)),
                 pendingCharUnlocks=["masked"], unlocksShown={"chars": ["masked", "astronaut"], "banners": ["tests500"], "fx": []},
                 seenUnlocks={"chars": ["ghost", "masked"], "banners": [], "fx": ["fireworks"], "v": 2})
        d.update(kw); return d

    # ---------------- (A) his shape ----------------
    with section("A"):
        mine = his(); cd = json.loads(json.dumps(mine)); cd["lastModified"] = now - 300000
        ctx, pg, errs = booted_ac(br, mine, cloud_ac(cd, cd))
        p = settle2(pg)
        chk("A the server's copy is in", p["confirmed"], p)
        chk("A a counter of %s on the misses, but only %s DIFFERENT questions retaken (expected %d of 100)" % (p["old"], p["count"], HIS_COUNT), p["old"] == 1231 and p["count"] == HIS_COUNT, p)
        chk("A the Masked One is locked and the card reads %s of %s, not Unlocked" % (p["cardHave"], p["cardNeed"]), p["locked"] is True and p["cardUnlocked"] is False and p["cardHave"] == HIS_COUNT and p["cardNeed"] == 100, p)
        chk("A not in the challenge group's held list (%s)" % p["challengeHave"], p["maskedId"] not in p["challengeHave"], p)
        chk("A not worn (the first starter, %s), not queued, not marked announced or seen" % p["first"], p["avatar"] == p["first"] and clean(p, p["maskedId"]), p)
        chk("A what is not this character is kept: the starter stays seen, the Astronaut stays announced, the look is untouched (%s)" % p["look"],
            "ghost" in p["seen"] and "astronaut" in p["shown"] and p["look"]["accent"] == "ink" and p["look"]["theme"] == "dark", p)
        pg.wait_for_timeout(6500); p = p2(pg)
        chk("A the account document and its floor, as written, carry none of it (%s / %s)" % (p["doc"], p["floor"]),
            p["doc"] and p["floor"] and doc_clean(p["doc"], p["maskedId"]) and doc_clean(p["floor"], p["maskedId"]), p)
        pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); p = settle2(pg)
        chk("A after another boot: still locked, not worn", p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
        mid = p["maskedId"]
        back = pg.evaluate("""()=>{ const hi = JSON.parse(JSON.stringify(store)); hi.lastModified = Date.now() + 5000; hi.retakenQuestions = 3000; hi.avatarChar = AVATAR_CHARACTERS.find(c => c.feat === 'retake100').id;
          hi.pendingCharUnlocks = [hi.avatarChar]; hi.unlocksShown = { chars: [hi.avatarChar], banners: [], fx: [] }; hi.seenUnlocks = { chars: [hi.avatarChar], banners: [], fx: [] };
          syncSameAccount(hi); return { avatar: store.avatarChar, locked: isLockedCharacter(hi.avatarChar), pending: store.pendingCharUnlocks.slice(), shown: store.unlocksShown.chars.slice(), seen: store.seenUnlocks.chars.slice(), old: store.retakenQuestions }; }""")
        chk("A a second device's copy (3,000 retakes, worn, queued, marked) merges in: still locked, not worn, not queued, not marked (%s)" % back,
            back["locked"] is True and back["avatar"] != mid and mid not in back["pending"] and mid not in back["shown"] and mid not in back["seen"], back)
        pg.wait_for_timeout(5000); p = p2(pg)
        chk("A and what is written after that merge is clean too (%s / %s)" % (p["doc"], p["floor"]), doc_clean(p["doc"], mid) and doc_clean(p["floor"], mid), p)
        chk("A no script error", not errs, errs)
        ctx.close()
        # a second device on an OLDER build writes it all back into the document and the floor; this build's next launch corrects it
        worn = his(); worn["lastModified"] = now - 100000
        fl = json.loads(json.dumps(worn)); fl["lastModified"] = now - 200000
        ctx, pg, errs = booted_ac(br, acad(stats=json.loads(json.dumps(his_stats)), retakenQuestions=1231, lastModified=now - 900000), cloud_ac(worn, fl))
        p = settle2(pg)
        chk("A the cloud copy (newer, worn, queued, marked) and its floor, read on a device that held nothing of it: locked, not worn, not queued, not marked",
            p["confirmed"] and p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
        pg.wait_for_timeout(6500); p = p2(pg)
        chk("A and the document and floor are corrected (%s / %s)" % (p["doc"], p["floor"]), p["doc"] and p["floor"] and doc_clean(p["doc"], p["maskedId"]) and doc_clean(p["floor"], p["maskedId"]), p)
        ctx.close()

    # ---------------- (B) the other doors ----------------
    with section("B"):
        mine = his()
        ctx, pg, errs = booted_ac(br, mine, cloud_ac(acad()))
        p = settle2(pg)
        chk("B no cloud progress of its own yet: locked, not worn, not marked (count %s)" % p["count"], p["confirmed"] and p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
        ctx.close()
        fl = json.loads(json.dumps(mine)); fl["lastModified"] = now - 200000
        small = acad(); small["lastModified"] = now - 100000
        ctx, pg, errs = booted_ac(br, mine, cloud_ac(small, fl))
        p = settle2(pg)
        chk("B the floor alone still holding it (worn, queued, marked, 1,231): locked, not worn, not marked", p["confirmed"] and p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
        pg.wait_for_timeout(6500); p = p2(pg)
        chk("B and the floor is brought down with it (%s)" % p["floor"], p["floor"] and doc_clean(p["floor"], p["maskedId"]), p)
        chk("B no script error", not errs, errs)
        ctx.close()

    # ---------------- (C) an honest earner is kept ----------------
    with section("C"):
        def earned(spec=None, keys=0, hardcore=0, worn="masked"):
            st = stats_of(spec or [])
            d = acad(avatarChar=worn, stats=st, retakenQuestions=3, unlocksShown={"chars": ["masked"], "banners": [], "fx": []}, seenUnlocks={"chars": ["masked"], "banners": [], "fx": []})
            if keys:
                off = len(st)
                for k in RK[off:off + keys]: st[k] = {"n": 3, "m": 1, "r": [CUT + 3600000]}
                d["retakenKeys"] = RK[off:off + keys]
            if hardcore:
                d["unitGameBeat"] = {"U%d" % i: {"easy": True, "average": True, "hardcore": True} for i in range(hardcore)}
            return d
        CASES = [("two misses (the record alone)", dict(spec=[(2, 3, "old", 100)])),
                 ("one miss, answered again, an old stamp (the carry-over)", dict(spec=[(1, 3, "old", 100)])),
                 ("one miss, answered again, no stamp (an old entry)", dict(spec=[(1, 2, "none", 100)])),
                 ("keys (answered again after the cutoff)", dict(keys=100)),
                 ("a mix of all four", dict(spec=[(2, 3, "old", 30), (1, 3, "old", 30), (1, 2, "none", 20)], keys=20)),
                 ("Hardcore on 10 units and nothing else", dict(hardcore=10))]
        for label, kw in CASES:
            real = earned(**kw); cd = json.loads(json.dumps(real)); cd["lastModified"] = now - 300000
            ctx, pg, errs = booted_ac(br, real, cloud_ac(cd, cd))
            p = settle2(pg)
            want = None if kw.get("hardcore") else 100
            chk("C [%s] kept: unlocked, the card Unlocked, still worn, announced (count %s)" % (label, p["count"]),
                p["confirmed"] and (want is None or p["count"] == want) and p["locked"] is False and p["cardUnlocked"] is True and p["avatar"] == p["maskedId"] and p["maskedId"] in p["shown"], p)
            pg.wait_for_timeout(6500); p = p2(pg)
            chk("C [%s] written to the document and floor still worn and announced (%s / %s)" % (label, p["doc"], p["floor"]),
                p["doc"] and p["floor"] and p["doc"]["avatar"] == p["maskedId"] and p["floor"]["avatar"] == p["maskedId"] and p["maskedId"] in p["doc"]["shown"], p)
            pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); p = settle2(pg)
            chk("C [%s] after another boot" % label, p["locked"] is False and p["avatar"] == p["maskedId"], p)
            back = pg.evaluate("()=>{ const hi = JSON.parse(JSON.stringify(store)); hi.lastModified = Date.now() + 5000; syncSameAccount(hi); return { locked: isLockedCharacter(AVATAR_CHARACTERS.find(c => c.feat === 'retake100').id), avatar: store.avatarChar }; }")
            chk("C [%s] and after a cloud merge (%s)" % (label, back), back["locked"] is False and back["avatar"] == p["maskedId"], back)
            chk("C [%s] no script error" % label, not errs, errs)
            ctx.close()
        def lost(label, d, count):
            ctx, pg, errs = booted_ac(br, d, cloud_ac(d, d)); p = settle2(pg)
            chk("C %s (count %s): locked, not worn, not marked" % (label, p["count"]), p["confirmed"] and p["count"] == count and p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
            ctx.close()
        lost("99 different questions retaken do not", earned([(1, 3, "old", 99)]), 99)
        lost("one miss answered once does not count, however many", earned([(1, 1, "old", 300), (2, 3, "old", 99)]), 99)
        lost("a miss with no answer after it and none before does not count (m 1, n 1)", earned([(1, 1, "none", 400)]), 0)
        lost("a single miss stamped after the cutoff counts only through its key", earned([(1, 3, "new", 100)]), 0)
        fake = earned(keys=100); fake["stats"] = {}; fake["retakenKeys"] = RK[:100] + ["not a question|1|zzzzzz"] * 3
        lost("keys with no miss on record do not count", fake, 0)
        fake = earned([(2, 3, "old", 99)]); fake["stats"]["not a question|1|zzzzzz"] = {"n": 3, "m": 2, "r": [OLDTS]}
        lost("a miss on a key that is not in this bank does not count", fake, 99)
        hc9 = earned(hardcore=9); hc9["retakenQuestions"] = 5000
        lost("Hardcore on 9 units and a counter of 5,000 do not", hc9, 0)

    # ---------------- (D) the app's own flow ----------------
    with section("D"):
        # (the Fire Code gate keeps its flow inside its own section; the same flow, written against the academy)
        FLOW = """async (a)=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          const until = async (f, ms) => { const t0 = Date.now(); while(Date.now() - t0 < (ms || 12000)){ try{ if(f()) return true; }catch(e){} await W(80); } return false; };
          const sum = () => Object.keys(store.stats || {}).reduce((n, k) => n + ((store.stats[k] && store.stats[k].m) || 0), 0);
          const snap = () => ({ old: store.retakenQuestions || 0, m: sum(), count: retakeDistinctCount(), keys: (store.retakenKeys || []).length, done: !!CHARACTER_FEATS.retake100.done() });
          try{
            theme.autoAdvance = false;
            const unit = topicsIn(QUESTIONS).map(u => [u, unitQuestionCount(u)]).filter(x => x[1] >= 6).sort((x, y) => x[1] - y[1])[0][0];
            const idx = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && inWholeUnit(QUESTIONS[i])).slice(0, 8);
            cfg.mode = 'drill'; cfg.units = [unit]; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'up'; cfg.flashcards = false;
            const play = async (n, miss) => { for(let k = 0; k < n; k++){
              await until(() => document.querySelector('.qpanel .choice') && !document.querySelector('.qpanel .choice[disabled]'));
              const qi = order[pos], right = correctSlot(qi), wrong = right === 0 ? 1 : 0;
              if(miss){ choose(wrong); await W(260); }
              choose(right); await W(300); advance(); await W(420); } };
            const run = async (miss, retake) => {
              beginRun(freshOrder(idx), retake ? 'Missed questions' : null, null, !!retake);
              await until(() => document.querySelector('.qpanel .choice') && runStartTime != null);
              await play(idx.length, miss);
              await until(() => !testInProgress || document.querySelector('.rs-screen'), 15000); };
            out.n = idx.length; out.start = snap();
            await run(true, false);  out.drill1 = snap();
            await run(false, false); out.drill2 = snap();
            await run(false, false); out.drill3 = snap();
            await run(false, true);  out.retake = snap();
          }catch(e){ out.threw = String(e && e.stack || e).slice(0, 300); }
          return out; }"""
        clean_acc = acad(avatarChar="ghost", lifetime={"answered": 0, "correct": 0, "drillPlays": 0, "examPlays": 0, "gamePlays": 0, "perfectTests": 0, "currentStreak": 0,
                                                       "longestStreak": 0, "points": 0, "fullTests": 0})
        ctx, pg, errs = booted_ac(br, clean_acc, cloud_ac(clean_acc))
        f = pg.evaluate(FLOW, None)
        chk("D the flow ran (%s questions, no exception)" % f.get("n"), not f.get("threw") and f.get("n", 0) >= 6, f)
        n = f.get("n", 0)
        d1 = f.get("drill1", {})
        chk("D a Drill with every question missed once and answered again: the OLD counter reads %s (one per miss - the cause), the different questions retaken %s" % (d1.get("old"), d1.get("count")),
            d1.get("old") == n and d1.get("m") == n and d1.get("count") == 0 and d1.get("keys") == 0, f)
        d2 = f.get("drill2", {})
        chk("D the next Drill, answered right first time, retakes each of those %d questions once (count %s)" % (n, d2.get("count")), d2.get("count") == n and d2.get("keys") == n, f)
        d3, r = f.get("drill3", {}), f.get("retake", {})
        chk("D the same questions again, and a Retake run, add nothing: each counts once (%s, %s)" % (d3.get("count"), r.get("count")), d3.get("count") == n and r.get("count") == n and r.get("keys") == n, f)
        chk("D and %d questions are not 100 (done: %s)" % (n, r.get("done")), r.get("done") is False, f)
        chk("D no script error", not errs, errs)
        ctx.close()

    # ---------------- (E) nothing else changes ----------------
    with section("E"):
        ids = None
        ctx, pg, errs = booted_ac(br, acad(), cloud_ac(acad()))
        ids = pg.evaluate("AVATAR_CHARACTERS.filter(c => (c.feat || c.unlock) && !c.retired && !c.legacy).map(c => c.id)")
        ctx.close()
        today = day_key(now)
        rich = dict(weeklyWins=1, vrWins=3, vrHosted=3, novaBeaten=True, bestTestStreak=150, hundoDayBest=3, bigTest450Passed=True, dailyCorrectTotal=10,
                    studyLog={day_key(now - i * DAY): 3600000 * 5 for i in range(1, 12)}, legacyChars=["hive", "poseidon"])
        def held_of(doc):
            ctx, pg, errs = booted_ac(br, doc, cloud_ac(doc, doc))
            p = settle2(pg)
            held = pg.evaluate("(ids)=>ids.filter(id => !isLockedCharacter(id))", ids)
            st = pg.evaluate("()=>({ pending: store.pendingCharUnlocks.slice(), shown: store.unlocksShown.chars.slice(), seen: store.seenUnlocks.chars.slice(), avatar: store.avatarChar, toast: !!document.querySelector('.unlock-pop, .newchar-pop') })")
            ctx.close(); return held, st, p
        base = acad(**rich, retakenQuestions=0)
        h0, s0, p0 = held_of(base)
        # the same account holding the old counter only: the Masked One is the ONLY difference
        fat = acad(**rich, retakenQuestions=1231, stats=json.loads(json.dumps(his_stats)))
        h1, s1, p1 = held_of(fat)
        chk("E the rich account holds %d rewards besides; nothing else moves with the retake evidence (%s vs %s)" % (len(h0), h0, h1), "masked" not in h0 and "masked" not in h1 and h0 == h1 and len(h0) >= 4, [h0, h1])
        chk("E no unlock queued, announced or seen for anyone as a result (%s / %s)" % (s0, s1), "masked" not in s1["pending"] + s1["shown"] + s1["seen"] and s1["pending"] == s0["pending"] and not s1["toast"], [s0, s1])
        # and one who earned it gains nothing else
        ok100 = acad(**rich, stats=stats_of([(2, 3, "old", 100)]))
        h2, s2, p2_ = held_of(ok100)
        chk("E an honest earner holds exactly the same plus the Masked One (%s)" % h2, sorted(h2) == sorted(h0 + ["masked"]), [h0, h2])
        chk("E ...and is not announced a second time (queue %s)" % s2["pending"], "masked" not in s2["pending"] and not s2["toast"], s2)
    br.close()

print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
