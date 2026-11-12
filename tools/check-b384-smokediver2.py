#!/usr/bin/env python3
"""Build 384.40: the Smoke Diver, the third time. Fire Code's `masked` (challenge `retake100`, "Retake 100 missed questions").

Madison's account, read from the live data (shapes only): 216 different questions answered, 384 answers, 128 different questions
missed, and `retakenQuestions` 172 - exactly the 172 misses on record, in the account's document and in its floor. In a Drill a wrong
pick is followed by picking again until it is right: ONE miss and ONE retake were recorded for that moment. So in Fire Code the counter
WAS the number of misses, by construction, "Retake 100 missed questions" was met by missing 100 answers, and the two clamps before this
(min(misses, answers)) could never bind - they bounded the counter by itself. 67 of his 128 missed questions were never shown again.

Fire Code now counts DIFFERENT questions answered AFTER a miss of them is on record: `store.retakenKeys` (written at the moment, before
the answer's own miss is recorded) plus any question with two or more misses in stats, worked out when read from those two (keys only
count while stats still hold a miss and the key is in the bank). Nothing is granted, so nothing stale can hold the character.

 (A) HIS SHAPE: 128 questions missed, 172 misses, `retakenQuestions` 172, the Smoke Diver worn, queued, marked announced and seen, in the
     store, the account document and its floor: after boot and the server's copy, the character is locked on every surface (the card
     reads 39 of 100, not Unlocked; the count of the challenge group), not worn (the class's first starter, the rest of the look
     kept), not queued, not marked; the document and floor written carry none of it; the same after another boot, after a second
     device's copy merges in (640 retakes, worn, queued), and with the floor alone still holding it;
 (B) THE SAME FROM EACH OTHER DOOR: no cloud document yet; the floor alone holding it;
 (C) AN HONEST EARN IS KEPT: 100 different questions answered after a miss (the keys; and the record alone, m >= 2) keep the Smoke Diver, worn,
     announced, in the document and floor, after another boot and a merge; 99 do not; keys with no miss on record, or not in the bank,
     do not count;
 (D) THE APP'S OWN FLOW: a Drill whose every question is missed once and answered counts NO retake (the old counter reads one per miss - the
     cause - and is not what decides); a later Drill answered right counts each question once; again, and a Retake run, add nothing;
 (E) EVERY CHALLENGE, RANK AND SECRET CHARACTER, the same way: with all of them queued, marked and one worn on a store that has earned
     none, every one is taken off; a store that has earned exactly one keeps that one (queued, marked, worn) and loses the rest;
 (F) PERSISTENCE: `retakenKeys` defaults to nothing for an older copy, drops what is not a string, is a union on a merge between devices
     (kept from both) (the reset's line is read in the source, not run: it reloads the page);
 (G) THE ACADEMY (384.46 changed it; its own gate is check-b384-masked.py): 640 retakes on 1 miss no longer hold the Masked One, only its Hardcore units do.
Run:  python3 tools/check-b384-smokediver2.py [--against OLD/index.html]     (--against 384.38 must FAIL)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-fcchallenges.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
exec(compile(_src, os.path.join(HERE, "check-b384-fcchallenges.py"), "exec"), globals())

PROBE2 = """()=>{ const o = {}; const t = f => { try{ return f(); }catch(e){ return 'ERR ' + String(e && e.message || e).slice(0, 80); } };
  const masked = AVATAR_CHARACTERS.find(c => c.feat === 'retake100');
  o.count = t(() => retakeDistinctCount());
  o.locked = t(() => isLockedCharacter(masked.id));
  const det = t(() => characterDetail(masked.id)); o.cardUnlocked = !!(det && det.unlocked); o.cardHave = det && det.have; o.cardNeed = det && det.need;
  o.avatar = store.avatarChar; o.pending = (store.pendingCharUnlocks || []).slice(); o.shown = ((store.unlocksShown || {}).chars || []).slice(); o.seen = ((store.seenUnlocks || {}).chars || []).slice();
  o.keys = Array.isArray(store.retakenKeys) ? store.retakenKeys.length : null;
  o.old = store.retakenQuestions; o.look = { accent: theme.accent, theme: theme.mode, banner: store.banner || null };
  o.challengeHave = AVATAR_CHARACTERS.filter(c => c.feat && !c.secret && !c.retired && !c.ultimate).filter(c => !isLockedCharacter(c.id)).map(c => c.id);
  o.maskedId = masked.id; o.first = classDefaultCharacter();
  const cl = window.__cloud && window.__cloud.progress, sc = (typeof syncCode !== 'undefined') ? syncCode : null;
  const slim = d => d ? { avatar: d.avatarChar, pending: (d.pendingCharUnlocks || []).slice(), shown: ((d.unlocksShown || {}).chars || []).slice(), seen: ((d.seenUnlocks || {}).chars || []).slice(), keys: Array.isArray(d.retakenKeys) ? d.retakenKeys.length : null } : null;
  o.doc = sc && cl ? slim(cl[sc]) : null; o.floor = sc && cl ? slim(cl[sc + '__floor']) : null;
  o.confirmed = (typeof cloudConfirmedFor !== 'undefined') && !!sc && cloudConfirmedFor === sc;
  return o; }"""
def p2(pg): return pg.evaluate(PROBE2)
def settle2(pg, tries=24):
    p = None
    for _ in range(tries):
        p = p2(pg)
        if p["confirmed"]: return p
        pg.wait_for_timeout(500)
    return p
def clean(s, mid):
    return mid not in s["pending"] and mid not in s["shown"] and mid not in s["seen"]
def doc_clean(d, mid):
    return d is None or (d["avatar"] != mid and mid not in d["pending"] and mid not in d["shown"] and mid not in d["seen"])
def booted(br, ifc_copy, cloud):
    set_ifc(ifc_copy)
    ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud)
    pg.wait_for_timeout(2500)
    return ctx, pg, errs

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # the bank's own question keys (a retake is of a question of this bank)
    set_ifc(fc_base())
    ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
    RK = pg.evaluate("KEYS.slice()")
    ctx.close()
    chk("0 the Fire Code bank gives enough question keys for a fixture (%d)" % len(RK), len(RK) >= 400 and all(isinstance(k, str) for k in RK))
    G["academy"].clear(); G["academy"].update(heavy_academy())

    def stats_of(spec):
        """spec: [(misses, answers, how_many)] -> {key: {n, m, r}} on real keys, in order"""
        st, i = {}, 0
        for m, n, cnt in spec:
            for _ in range(cnt):
                st[RK[i]] = {"n": n, "m": m, "r": []}; i += 1
        return st
    HIS = [(0, 1, 88), (1, 1, 67), (1, 2, 22), (2, 3, 35), (3, 4, 3), (4, 5, 1)]     # 216 questions, 128 missed, 172 misses, 61 answered twice or more
    his_stats = stats_of(HIS)
    his_m = sum(v["m"] for v in his_stats.values())
    his_two = sum(1 for v in his_stats.values() if v["m"] >= 2)
    chk("0 the fixture is his shape: 216 questions, 128 missed, %d misses, %d missed twice or more" % (his_m, his_two), len(his_stats) == 216 and his_m == 172 and his_two == 39)
    def his(**kw):
        d = fc_base(retakenQuestions=172, avatarChar="masked", stats=json.loads(json.dumps(his_stats)),
                    lifetime={"answered": 384, "correct": 212, "drillPlays": 18, "examPlays": 0, "gamePlays": 0, "perfectTests": 4, "currentStreak": 0,
                              "longestStreak": 31, "points": 3210, "fullTests": 10},
                    pendingCharUnlocks=["masked"], unlocksShown={"chars": ["masked", "astronaut"], "banners": ["tests500"], "fx": []},
                    seenUnlocks={"chars": ["ghost", "masked"], "banners": [], "fx": ["fireworks"], "v": 2})
        d.update(kw); return d

    # ---------------- (A) his shape ----------------
    with section("A"):
        mine = his()
        cd = json.loads(json.dumps(mine)); cd["lastModified"] = now - 300000
        ctx, pg, errs = booted(br, mine, cloud_with(fire=cd, floor=cd))
        p = settle2(pg)
        chk("A the server's copy is in (the rule waits for it)", p["confirmed"], p)
        chk("A 172 misses on record and a counter of %s, but only %s DIFFERENT questions retaken (expected 39 of 100)" % (p["old"], p["count"]), p["old"] == 172 and p["count"] == 39, p)
        chk("A the Smoke Diver is locked, and the card reads %s of %s, not Unlocked" % (p["cardHave"], p["cardNeed"]), p["locked"] is True and p["cardUnlocked"] is False and p["cardHave"] == 39 and p["cardNeed"] == 100, p)
        chk("A not in the challenge group's count of held characters (%s)" % p["challengeHave"], p["maskedId"] not in p["challengeHave"], p)
        chk("A not worn (the class's first starter, %s), not queued, not marked announced or seen" % p["first"], p["avatar"] == p["first"] and clean(p, p["maskedId"]), p)
        chk("A what is not this character is kept: the starter stays seen, the look is untouched (%s)" % p["look"], "ghost" in p["seen"] and p["look"]["accent"] == "ink" and p["look"]["theme"] == "dark", p)
        pg.wait_for_timeout(6500); p = p2(pg)
        chk("A the account document and its floor, as written, carry none of it (%s / %s)" % (p["doc"], p["floor"]),
            p["doc"] and p["floor"] and doc_clean(p["doc"], p["maskedId"]) and doc_clean(p["floor"], p["maskedId"]), p)
        pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); p = settle2(pg)
        chk("A after another boot: still locked, not worn", p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
        back = pg.evaluate("""()=>{ const hi = JSON.parse(JSON.stringify(store)); hi.lastModified = Date.now() + 5000; hi.retakenQuestions = 640; hi.avatarChar = AVATAR_CHARACTERS.find(c => c.feat === 'retake100').id;
          hi.pendingCharUnlocks = [hi.avatarChar]; hi.unlocksShown = { chars: [hi.avatarChar], banners: [], fx: [] }; hi.seenUnlocks = { chars: [hi.avatarChar], banners: [], fx: [] };
          syncSameAccount(hi); return { avatar: store.avatarChar, locked: isLockedCharacter(hi.avatarChar), pending: store.pendingCharUnlocks.slice(), shown: store.unlocksShown.chars.slice(), seen: store.seenUnlocks.chars.slice(), old: store.retakenQuestions }; }""")
        mid = p["maskedId"]
        chk("A a second device's copy (640 retakes, worn, queued, marked) merges in: still locked, not worn, not queued, not marked (%s)" % back,
            back["locked"] is True and back["avatar"] != mid and mid not in back["pending"] and mid not in back["shown"] and mid not in back["seen"], back)
        pg.wait_for_timeout(5000); p = p2(pg)
        chk("A and what is written after that merge is clean too (%s / %s)" % (p["doc"], p["floor"]), doc_clean(p["doc"], mid) and doc_clean(p["floor"], mid), p)
        chk("A no script error", not errs, errs)
        ctx.close()

    # ---------------- (B) the other doors ----------------
    with section("B"):
        mine = his()
        ctx, pg, errs = booted(br, mine, cloud_with())
        p = settle2(pg)
        chk("B no cloud document yet: locked, not worn, not marked (count %s)" % p["count"], p["confirmed"] and p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
        ctx.close()
        fl = json.loads(json.dumps(mine)); fl["lastModified"] = now - 200000
        small = fc_base(); small["lastModified"] = now - 100000
        ctx, pg, errs = booted(br, mine, cloud_with(fire=small, floor=fl))
        p = settle2(pg)
        chk("B the floor alone still holding it (worn, queued, marked, 172): locked, not worn, not marked", p["confirmed"] and p["locked"] is True and p["avatar"] != p["maskedId"] and clean(p, p["maskedId"]), p)
        pg.wait_for_timeout(6500); p = p2(pg)
        chk("B and the floor is brought down with it (%s)" % p["floor"], p["floor"] and doc_clean(p["floor"], p["maskedId"]), p)
        chk("B no script error", not errs, errs)
        ctx.close()

    # ---------------- (C) an honest earn is kept ----------------
    with section("C"):
        keys100 = RK[:100]
        def earned(n_keys=100, how="keys"):
            st = {}
            for k in RK[:n_keys]:
                st[k] = {"n": 3, "m": 2 if how == "record" else 1, "r": []}
            d = fc_base(avatarChar="masked", stats=st, retakenQuestions=3,
                        lifetime={"answered": 400, "correct": 270, "drillPlays": 12, "examPlays": 3, "gamePlays": 0, "perfectTests": 0, "currentStreak": 0, "longestStreak": 9, "points": 2600, "fullTests": 0},
                        unlocksShown={"chars": ["masked"], "banners": [], "fx": []}, seenUnlocks={"chars": ["masked"], "banners": [], "fx": []})
            if how == "keys": d["retakenKeys"] = RK[:n_keys]
            return d
        for how in ("keys", "record"):
            real = earned(100, how); cd = json.loads(json.dumps(real)); cd["lastModified"] = now - 300000
            ctx, pg, errs = booted(br, real, cloud_with(fire=cd, floor=cd))
            p = settle2(pg)
            chk("C (%s) 100 different questions retaken: kept - unlocked, the card Unlocked, still worn, announced (count %s)" % (how, p["count"]),
                p["confirmed"] and p["count"] == 100 and p["locked"] is False and p["cardUnlocked"] is True and p["avatar"] == p["maskedId"] and p["maskedId"] in p["shown"], p)
            pg.wait_for_timeout(6500); p = p2(pg)
            chk("C (%s) written to the document and floor still worn and announced (%s / %s)" % (how, p["doc"], p["floor"]),
                p["doc"] and p["floor"] and p["doc"]["avatar"] == p["maskedId"] and p["floor"]["avatar"] == p["maskedId"] and p["maskedId"] in p["doc"]["shown"], p)
            pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); p = settle2(pg)
            chk("C (%s) after another boot" % how, p["locked"] is False and p["avatar"] == p["maskedId"], p)
            back = pg.evaluate("()=>{ const hi = JSON.parse(JSON.stringify(store)); hi.lastModified = Date.now() + 5000; syncSameAccount(hi); return { locked: isLockedCharacter(AVATAR_CHARACTERS.find(c => c.feat === 'retake100').id), avatar: store.avatarChar }; }")
            chk("C (%s) and after a cloud merge (%s)" % (how, back), back["locked"] is False and back["avatar"] == p["maskedId"], back)
            chk("C (%s) no script error" % how, not errs, errs)
            ctx.close()
        short = earned(99, "keys")
        ctx, pg, errs = booted(br, short, cloud_with(fire=short, floor=short)); p = settle2(pg)
        chk("C 99 do not (count %s): locked, not worn" % p["count"], p["count"] == 99 and p["locked"] is True and p["avatar"] != p["maskedId"], p)
        ctx.close()
        fake = earned(100, "keys"); fake["stats"] = {}      # keys with no miss on record
        fake["retakenKeys"] = RK[:100] + ["not a question|1|zzzzzz"] * 3
        ctx, pg, errs = booted(br, fake, cloud_with(fire=fake, floor=fake)); p = settle2(pg)
        chk("C keys with no miss on record do not count (count %s)" % p["count"], p["count"] == 0 and p["locked"] is True, p)
        ctx.close()
        fake = earned(99, "keys"); fake["stats"]["not a question|1|zzzzzz"] = {"n": 3, "m": 2, "r": []}
        ctx, pg, errs = booted(br, fake, cloud_with(fire=fake, floor=fake)); p = settle2(pg)
        chk("C a miss on a key that is not in this bank does not count (count %s)" % p["count"], p["count"] == 99 and p["locked"] is True, p)
        ctx.close()

    # ---------------- (D) the app's own flow ----------------
    with section("D"):
        FLOW2 = """async (a)=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
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
        set_ifc(fc_base(stats={}, retakenQuestions=0, retakenKeys=[], avatarChar="ghost", lifetime={"answered": 0, "correct": 0, "drillPlays": 0, "examPlays": 0, "gamePlays": 0,
                "perfectTests": 0, "currentStreak": 0, "longestStreak": 0, "points": 0, "fullTests": 0}))
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
        pg.wait_for_timeout(2500)
        f = pg.evaluate(FLOW2, None)
        chk("D the flow ran (%s questions, no exception)" % f.get("n"), not f.get("threw") and f.get("n", 0) >= 6, f)
        n = f.get("n", 0)
        d1 = f.get("drill1", {})
        chk("D a Drill with every question missed once and answered again: the OLD counter reads %s (one per miss - the cause), the different questions retaken %s" % (d1.get("old"), d1.get("count")),
            d1.get("old") == n and d1.get("m") == n and d1.get("count") == 0 and d1.get("keys") == 0, f)
        d2 = f.get("drill2", {})
        chk("D the next Drill, answered right first time, retakes each of those %d questions once (count %s)" % (n, d2.get("count")), d2.get("count") == n and d2.get("keys") == n, f)
        d3, r = f.get("drill3", {}), f.get("retake", {})
        chk("D the same questions again, and a Retake run, add nothing: each counts once (%s, %s)" % (d3.get("count"), r.get("count")), d3.get("count") == n and r.get("count") == n and r.get("keys") == n, f)
        chk("D and eight questions are not 100 (done: %s)" % r.get("done"), r.get("done") is False, f)
        chk("D no script error", not errs, errs)
        ctx.close()

    # ---------------- (E) every challenge, rank and secret character ----------------
    with section("E"):
        ALL = None
        set_ifc(fc_base())
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
        ALL = pg.evaluate("AVATAR_CHARACTERS.filter(c => (c.feat || c.unlock) && !c.retired && !c.legacy).map(c => [c.id, c.feat || null, !!c.unlock, !!c.secret, !!c.ultimate])")
        ctx.close()
        feats = [a for a in ALL if a[1] and not a[3]]
        chk("E the class has %d challenge characters, %d in all with the ranks and the secrets" % (len(feats), len(ALL)), len(feats) == 12 and len(ALL) >= 22, ALL)
        ids = [a[0] for a in ALL]
        today = day_key(now)
        studyrun = {day_key(now - i * DAY): 3600000 for i in range(1, 8)}
        SUP = {"detective": {"dailyCorrectTotal": 10}, "masked": {"retakenKeys": RK[:100], "stats": {k: {"n": 3, "m": 1, "r": []} for k in RK[:100]}},
               "zeus": {"weeklyWins": 1}, "poseidon": {"novaBeaten": True}, "clown": {"vrWins": 3}, "valkyrie": {"studyLog": studyrun},
               "marksman": {"bestTestStreak": 100}, "astronaut": {"hundoDayBest": 3}, "hacker": {"studyLog": {day_key(now - i * DAY): 3600000 * 5 for i in range(1, 6)}},
               "timekeeper": {"studyLog": {day_key(now - i * DAY): 3600000 for i in range(1, 30, 2)}}, "ronin": {"bigTest450Passed": True}, "hive": {"vrHosted": 3}}
        def stale(extra=None, wear="marksman"):
            d = fc_base(avatarChar=wear, pendingCharUnlocks=list(ids), unlocksShown={"chars": list(ids), "banners": [], "fx": []}, seenUnlocks={"chars": list(ids) + ["ghost"], "banners": [], "fx": []})
            d.update(extra or {}); return d
        # nothing earned
        mine = stale(); cd = json.loads(json.dumps(mine)); cd["lastModified"] = now - 300000
        ctx, pg, errs = booted(br, mine, cloud_with(fire=cd, floor=cd))
        pg.wait_for_timeout(1500)
        s = settle2(pg)
        held = pg.evaluate("(ids)=>ids.filter(id => !isLockedCharacter(id))", ids)
        leftover = pg.evaluate("(ids)=>({ pending: store.pendingCharUnlocks.filter(x => ids.indexOf(x) >= 0), shown: store.unlocksShown.chars.filter(x => ids.indexOf(x) >= 0), seen: store.seenUnlocks.chars.filter(x => ids.indexOf(x) >= 0), avatar: store.avatarChar })", ids)
        chk("E nothing earned: none of the %d is held (%s)" % (len(ids), held), s["confirmed"] and not held, [s["confirmed"], held])
        chk("E ...and none is queued, announced or seen, and the wearer is on the first starter (%s)" % leftover,
            not leftover["pending"] and not leftover["shown"] and not leftover["seen"] and leftover["avatar"] == s["first"], leftover)
        ctx.close()
        # each earned alone
        for cid, fid, *_ in feats:
            if cid not in SUP: continue      # the ultimates (every other reward first) cannot be earned alone
            extra = json.loads(json.dumps(SUP[cid]))
            mine = stale(extra, wear=cid); cd = json.loads(json.dumps(mine)); cd["lastModified"] = now - 300000
            ctx, pg, errs = booted(br, mine, cloud_with(fire=cd, floor=cd))
            s = settle2(pg)
            held = pg.evaluate("(ids)=>ids.filter(id => !isLockedCharacter(id))", ids)
            left = pg.evaluate("(a)=>({ pending: store.pendingCharUnlocks.filter(x => a.ids.indexOf(x) >= 0), shown: store.unlocksShown.chars.filter(x => a.ids.indexOf(x) >= 0), seen: store.seenUnlocks.chars.filter(x => a.ids.indexOf(x) >= 0), avatar: store.avatarChar })", {"ids": ids})
            chk("E %s alone: held %s; queued %s; announced %s; seen %s; worn %s" % (cid, held, left["pending"], left["shown"], left["seen"], left["avatar"]),
                s["confirmed"] and held == [cid] and left["pending"] == [cid] and left["shown"] == [cid] and left["seen"] == [cid] and left["avatar"] == cid and not errs, [held, left, errs])
            ctx.close()

    # ---------------- (F) persistence ----------------
    with section("F"):
        old = fc_base(); old.pop("retakenKeys", None)
        ctx, pg, errs = booted(br, old, cloud_with())
        v = pg.evaluate("()=>({ keys: store.retakenKeys })")
        chk("F an older copy without the field loads as none (%s)" % v["keys"], v["keys"] == [], v)
        ctx.close()
        junk = fc_base(retakenKeys=[RK[0], 5, None, {"a": 1}, RK[1]])
        ctx, pg, errs = booted(br, junk, cloud_with())
        v = pg.evaluate("()=>({ keys: store.retakenKeys })")
        chk("F anything that is not a string is dropped (%s)" % v["keys"], v["keys"] == [RK[0], RK[1]], v)
        both = pg.evaluate("""(rk)=>{ store.stats = {}; rk.slice(0, 6).forEach(k => { store.stats[k] = { n: 3, m: 1, r: [] }; }); store.retakenKeys = rk.slice(0, 3);
          const src = JSON.parse(JSON.stringify(store)); src.retakenKeys = rk.slice(2, 6); src.lastModified = Date.now() + 5000; syncSameAccount(src); return store.retakenKeys.slice(); }""", RK)
        chk("F two devices' keys are a union (%d of 6: %s)" % (len(both), both), sorted(both) == sorted(RK[:6]), both)
        ctx.close()

    # ---------------- (G) the academy ----------------
    # (384.46) the academy counts different questions too now (tools/check-b384-masked.py is its gate). Here: what is left of the old exception.
    with section("G"):
        G["academy"].clear(); G["academy"].update(heavy_academy(avatarChar="masked", stats={"a": {"n": 3, "m": 1, "r": []}}))
        ctx, pg, errs = G["page"](br, G["init"]("academy"), seed=cloud_with())
        pg.wait_for_timeout(2500)
        v = pg.evaluate("""()=>{ const m = AVATAR_CHARACTERS.find(c => c.feat === 'retake100'); return { cls: window.NOVA_CLASS, locked: isLockedCharacter(m.id), avatar: store.avatarChar, id: m.id, retaken: store.retakenQuestions,
          note: CHARACTER_FEATS.retake100.note, keys: (store.retakenKeys || []).length, hc: hardcoreUnitsBeaten(), count: retakeDistinctCount() }; }""")
        chk("G the academy's 640 retakes on 1 miss no longer hold the Masked One by the counter (count %s); its twelve Hardcore units still do (%s)" % (v["count"], v), v["cls"] == "academy" and v["count"] == 0 and v["hc"] >= 10 and v["locked"] is False and v["avatar"] == v["id"], v)
        chk("G no script error", not errs, errs)
        ctx.close()
    br.close()

print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
