#!/usr/bin/env python3
"""Build 384 r23: a Fire Code account only counts its own challenges.

Madison, on his phone in Fire Code (Customize > Challenges): the Smoke Diver, "Retake 100 missed questions" (CHARACTER_FEATS.retake100:
store.retakenQuestions >= 100, or Game's Hardcore beaten on 10 units - store.unitGameBeat), read Unlocked, with a full bar, on an
account days old: "There's no chance I completed this, why do I have this unlocked already". Both counters are the academy's kind of
history (a Fire Code store has no Game mode; and seedChallenges289 backfilled retakenQuestions from the store's own misses x drill
share whenever its "seeded" flag read false). With an in-memory Firestore (the CDN is blocked here; check-b384-friends' stand-in) and
a heavily used academy copy (hundreds of retakes, twelve Hardcore units, a long study log, every flare, weekly wins, Virtual Room
wins and hosted matches, a 300-run, a passed 450-question test, 5,400 answers):

 (A) A FRESH FIRE CODE STORE HOLDS NOTHING: read off the page, every `CHARACTER_FEATS[*].done()`, every banner, every challenge or
     rank character - none is unlocked in Fire Code after boot, after the first drill start (beginRun), after a cloud pull of its
     own (near-empty) document, and after the academy's copy changes underneath (a reload with a heavier one).
 (B) THE REPAIR: a Fire Code store (and its cloud document and its __floor) carrying the inherited count (640 retakes on 5 misses
     and 40 answers, twelve Hardcore units), the Smoke Diver worn, queued and marked announced - corrected once the server's copy is
     in: the count within what its own record supports, no Hardcore, the character locked, not worn (the class's first starter),
     not queued, not marked; and it STAYS so after another boot and after a cloud merge that brings the high count back (max-merged
     counters), and the document written is clamped too.
 (C) A REAL EARN IS KEPT: a Fire Code account whose own record supports its 120 retakes (130 misses on record, 400 answers) keeps
     the Smoke Diver, wears it, and a live Drill - a question missed then answered again - counts one more retake and is not undone.
 (D) THE ACADEMY IS UNAFFECTED: its own retakes and Hardcore units still count and still unlock the Masked One, however few misses
     its stats hold (the rule is Fire Code's alone), and nothing is lowered in its saved copy.
 (E) THE BACKFILL: a Fire Code store whose "seeded" flag reads false (a cloud document without it, an academy copy without it) and
     which holds 150 misses on record does NOT come out of its first drill start with 150 retakes; the flag is set; the first visit
     never copies the academy's flag.

Shapes are asserted, not labels: the tables are read off the page.
Run:  python3 tools/check-b384-fcchallenges.py [--against OLD/index.html]     (--against must FAIL)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-friends.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b384-friends.py"), "__name__": "b384fcch"}
exec(src, G)
g = G["g"]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
class section:
    def __init__(self, name): self.name = name
    def __enter__(self): return self
    def __exit__(self, t, v, tb):
        if v is not None: chk(self.name + ": raised %s: %s" % (t.__name__, v), False)
        return True

CODE, OWNER, now = G["CODE"], G["OWNER"], G["now_ms"]
BASE = json.loads(json.dumps(G["academy"]))   # the harness's academy account, before any of this gate's changes
UNITS = ["Professionalism and Ethics", "Professional Policing", "TCOLE Rules", "Penal Code", "Racial Profiling", "Victims of Crime",
         "Verbal Communication", "Identity Crimes", "Civil Process and Liability", "Arrest, Search and Seizure", "Use of Force", "Traffic"]
DAY = 86400000
def day_key(ms):
    import datetime
    return datetime.date.fromtimestamp(ms / 1000).isoformat()
def heavy_academy(**kw):
    a = json.loads(json.dumps(BASE))
    a.update({"retakenQuestions": 640, "unitGameBeat": {u: {"easy": True, "average": True, "hardcore": True} for u in UNITS},
              "challengeSeed289": True, "weeklyWins": 3, "weeklyTop3": 5, "weekWinWeeks": ["2026-09-28"], "vrWins": 9, "vrMatches": 30, "vrHosted": 5,
              "novaBeaten": True, "dailyCorrectBest": 20, "dailyCorrectStreak": 12, "dailyCorrectTotal": 30, "bestTestStreak": 300,
              "bigTest450Passed": True, "bigTest500Passed": True, "unitHundoStreakBest": 9, "hundoDayBest": 8, "fullTestsSeeded": True,
              "lateHundosSeed312": True, "lateHundos": 9, "hiveMoved384": True, "sheriffMoved324": True, "koiRevoked295": True,
              "mysteryColorsFound": {"red": True, "orange": True, "yellow": True, "violet": True, "white": True, "core": True},
              "studyLog": {day_key(now - i * DAY): 3600000 for i in range(60)},
              "stats": {"k%d" % i: {"n": 6, "m": 4, "r": []} for i in range(200)}})
    a["lifetime"] = dict(a["lifetime"], answered=5400, correct=4980, drillPlays=64, examPlays=22, fullTests=120)
    a.update(kw); return a
def fc_base(**kw):
    """what a Fire Code copy looks like once it has been used a little: its own (small) progress"""
    f = {k: BASE[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey"] if k in BASE}
    f.update({k: v for k, v in BASE.items() if k.startswith("seen") and k != "seenUnlocks"})
    f.update({"avatarChar": "ghost", "lifetime": {"answered": 40, "correct": 30, "drillPlays": 3, "examPlays": 1, "gamePlays": 0, "perfectTests": 0,
              "currentStreak": 0, "longestStreak": 4, "points": 380, "fullTests": 0}, "challengeSeed289": True, "fullTestsSeeded": True,
              "lateHundosSeed312": True, "leaderboardOptIn": True, "leaderboardOptInChanged": False, "lastModified": now - 600000,
              "stats": {"q%d" % i: {"n": 4, "m": 1, "r": []} for i in range(5)}})
    f.update(kw); return f
def set_ifc(d):
    G["ifc"].clear(); G["ifc"].update(d)
def cloud_with(fire=None, floor=None):
    c = json.loads(json.dumps(G["CLOUD0"]))
    c["progress"][CODE] = G["academy"]
    if fire is not None: c["progress"][CODE + "__ifc"] = fire
    if floor is not None: c["progress"][CODE + "__ifc__floor"] = floor
    return c

PROBE = """()=>{ const feats = {}; const table = Object.keys(CHARACTER_FEATS);
  table.forEach(k => { let v; try{ v = !!CHARACTER_FEATS[k].done(); }catch(e){ v = 'ERR'; } feats[k] = v; });
  const banners = {}; BANNERS.forEach(b => { let v; try{ v = !!bannerEarned(b.id); }catch(e){ v = 'ERR'; } banners[b.id] = v; });
  const held = AVATAR_CHARACTERS.filter(c => !c.retired && (c.feat || c.unlock) && !isLockedCharacter(c.id)).map(c => c.id);
  const masked = AVATAR_CHARACTERS.find(c => c.feat === 'retake100');
  return { cls: window.NOVA_CLASS, retaken: store.retakenQuestions, hc: hardcoreUnitsBeaten(), seed: store.challengeSeed289,
    misses: Object.keys(store.stats || {}).reduce((n, k) => n + ((store.stats[k] && store.stats[k].m) || 0), 0), answered: store.lifetime.answered,
    featsDone: Object.keys(feats).filter(k => feats[k]), featsN: table.length, banners: Object.keys(banners).filter(k => banners[k]), bannersN: Object.keys(banners).length,
    held, maskedId: masked && masked.id, maskedLocked: masked ? isLockedCharacter(masked.id) : null, avatar: store.avatarChar,
    pending: (store.pendingCharUnlocks || []).slice(), shown: ((store.unlocksShown || {}).chars || []).slice(), seen: ((store.seenUnlocks || {}).chars || []).slice(),
    confirmed: (typeof cloudConfirmedFor !== 'undefined') && !!syncCode && cloudConfirmedFor === syncCode,
    docRetaken: (window.__cloud && window.__cloud.progress && window.__cloud.progress[syncCode]) ? window.__cloud.progress[syncCode].retakenQuestions : null,
    docHc: (window.__cloud && window.__cloud.progress && window.__cloud.progress[syncCode]) ? Object.keys(window.__cloud.progress[syncCode].unitGameBeat || {}).length : null,
    floorRetaken: (window.__cloud && window.__cloud.progress && window.__cloud.progress[syncCode + '__floor']) ? window.__cloud.progress[syncCode + '__floor'].retakenQuestions : null }; }"""
BEGIN = "()=>{ try{ beginRun([0,1,2,3,4,5,6,7,8,9], null); }catch(e){ return 'ERR ' + e.message; } return 'ok'; }"
def probe(pg): return pg.evaluate(PROBE)
def settle(pg, tries=24):
    p = None
    for _ in range(tries):
        p = probe(pg)
        if p["confirmed"]: return p
        pg.wait_for_timeout(500)
    return p
def nothing_held(p):
    return not p["featsDone"] and not p["banners"] and not p["held"]
def table_ok(p): return p["featsN"] >= 12 and p["bannersN"] >= 5

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])

    # ---------------- (A) a fresh Fire Code store, seeded from a heavy academy copy ----------------
    with section("A"):
        HA = heavy_academy()
        G["academy"].clear(); G["academy"].update(HA)
        own_small = {"firstName": "Maddox", "onboardingComplete": True, "publicId": OWNER, "lastModified": now - 1000, "tourRev": 99,
                     "lifetime": {"answered": 12, "correct": 9, "points": 90}, "stats": {"x": {"n": 3, "m": 1}}}
        for label, cloud in (("no cloud document", cloud_with()), ("its own near-empty cloud document", cloud_with(fire=own_small))):
            set_ifc({})
            ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=False), seed=cloud)
            pg.wait_for_timeout(2500); settle(pg)
            p = probe(pg)
            chk("A [%s] Fire Code, the challenge table read off the page (%d challenges, %d banners)" % (label, p["featsN"], p["bannersN"]), p["cls"] == "ifc" and table_ok(p), p)
            chk("A [%s] after boot: no challenge done, no banner earned, no challenge or rank character unlocked" % label, nothing_held(p), (p["featsDone"], p["banners"], p["held"]))
            chk("A [%s] its own counters are its own: no retakes, no Hardcore, nothing of the academy's" % label, p["retaken"] <= p["misses"] and p["hc"] == 0 and p["retaken"] < 100, p)
            r = pg.evaluate(BEGIN); pg.wait_for_timeout(1800); settle(pg)
            p = probe(pg)
            chk("A [%s] after the first drill start (beginRun runs every seed)" % label, r == "ok" and nothing_held(p) and p["hc"] == 0 and p["seed"] is True, (r, p))
            pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); settle(pg)
            p = probe(pg)
            chk("A [%s] after another boot" % label, nothing_held(p) and p["hc"] == 0, p)
            state = ctx.storage_state(); ctx.close()
            # the academy's copy changes underneath (heavier still), the Fire Code copy on the device is what the last run left
            HB = heavy_academy(retakenQuestions=9000, vrWins=40, weeklyWins=9)
            ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=False, academy_copy=HB), seed=cloud, state=state)
            pg.wait_for_timeout(2500); settle(pg)
            p = probe(pg)
            chk("A [%s] after the academy's copy changed underneath" % label, nothing_held(p) and p["retaken"] < 100 and p["hc"] == 0, p)
            chk("A [%s] no script error" % label, not errs, errs)
            ctx.close()
    # a brand-new Fire Code account (signed up there): same table
    with section("A2"):
        set_ifc({})
        G["academy"].clear(); G["academy"].update(heavy_academy())
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=False, academy_copy=heavy_academy(challengeSeed289=False, fullTestsSeeded=False, lateHundosSeed312=False)), seed=cloud_with())
        pg.wait_for_timeout(2500); p = probe(pg)
        chk("A2 an academy copy whose seed flags read false is not copied across: the Fire Code copy is seeded (it has no earlier history)", p["seed"] is True and nothing_held(p), p)
        ctx.close()

    # ---------------- (B) the repair ----------------
    with section("B"):
        G["academy"].clear(); G["academy"].update(heavy_academy())
        wrong = fc_base(retakenQuestions=640, unitGameBeat={u: {"easy": True, "average": True, "hardcore": True} for u in UNITS}, avatarChar="masked",
                        pendingCharUnlocks=["masked"], unlocksShown={"chars": ["masked", "ghost"], "banners": [], "fx": []},
                        seenUnlocks={"chars": ["masked"], "banners": [], "fx": []})
        wrong["stats"] = {"q%d" % i: {"n": 3, "m": 1, "r": []} for i in range(5)}
        cloud_doc = json.loads(json.dumps(wrong)); cloud_doc["lastModified"] = now - 300000
        floor_doc = json.loads(json.dumps(wrong))
        cap = 5   # (384.24) the misses on record: 5
        set_ifc(wrong)
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with(fire=cloud_doc, floor=floor_doc))
        pg.wait_for_timeout(2500); p = settle(pg)
        chk("B the server's copy is in (the repair waits for it)", p["confirmed"], p)
        chk("B the count is within what Fire Code's own record supports (%d misses, %d answers) - was 640" % (p["misses"], p["answered"]), p["retaken"] <= min(p["misses"], p["answered"]) and p["retaken"] < 100, p)
        chk("B no Hardcore units", p["hc"] == 0, p)
        chk("B the Smoke Diver is locked, not worn (the first starter instead), not queued, not marked announced or seen", p["maskedLocked"] is True and p["avatar"] != p["maskedId"] and p["maskedId"] not in p["pending"] and p["maskedId"] not in p["shown"] and p["maskedId"] not in p["seen"], p)
        chk("B what is not the Smoke Diver's is left alone (another mark stays)", "ghost" in p["shown"], p)
        chk("B nothing else came unlocked", nothing_held(p), (p["featsDone"], p["banners"], p["held"]))
        pg.wait_for_timeout(6500); p = probe(pg)
        chk("B the document written is clamped too (cloud document: %s retakes, %s Hardcore units)" % (p["docRetaken"], p["docHc"]), p["docRetaken"] is not None and p["docRetaken"] <= cap and p["docHc"] == 0, p)
        pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); p = settle(pg)
        chk("B after another boot it stays corrected (the floor and the cloud hold the high count no more)", p["retaken"] <= cap and p["hc"] == 0 and p["maskedLocked"] is True and p["avatar"] != p["maskedId"], p)
        # a merge that brings the high count back (another device, the floor backup): max-merged counters
        back = pg.evaluate("""()=>{ const hi = JSON.parse(JSON.stringify(store)); hi.retakenQuestions = 640; hi.unitGameBeat = { 'Traffic': { easy: true, average: true, hardcore: true }, 'Penal Code': { hardcore: true } };
          hi.lastModified = Date.now() + 5000; hi.pendingCharUnlocks = ['masked']; syncSameAccount(hi); return { retaken: store.retakenQuestions, hc: hardcoreUnitsBeaten() }; }""")
        chk("B and after a cloud merge that brings it back (a newer copy with 640 retakes and Hardcore units)", back["retaken"] <= cap and back["hc"] == 0, back)
        back2 = pg.evaluate("""()=>{ const hi = JSON.parse(JSON.stringify(store)); hi.retakenQuestions = 640; hi.lastModified = 1; syncSameAccount(hi); return { retaken: store.retakenQuestions, locked: isLockedCharacter('masked') }; }""")
        chk("B and after an OLDER copy with 640 is merged (the max side)", back2["retaken"] <= cap and back2["locked"] is True, back2)
        chk("B no script error", not errs, errs)
        ctx.close()
    with section("B2"):
        # a copy with no sync at all (nothing still to arrive): repaired at launch
        set_ifc(wrong)
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
        pg.wait_for_timeout(2500); p = settle(pg)
        chk("B2 the same repair where the account's Fire Code document does not exist yet (a copy nothing has been pulled for)", p["confirmed"] and p["retaken"] <= 10 and p["hc"] == 0 and p["maskedLocked"] is True, p)
        ctx.close()

    # ---------------- (C) a real earn is kept ----------------
    with section("C"):
        G["academy"].clear(); G["academy"].update(heavy_academy())
        real = fc_base(retakenQuestions=120, avatarChar="masked", lifetime={"answered": 400, "correct": 270, "drillPlays": 12, "examPlays": 3, "gamePlays": 0,
                       "perfectTests": 0, "currentStreak": 0, "longestStreak": 9, "points": 2600, "fullTests": 0},
                       unlocksShown={"chars": ["masked"], "banners": [], "fx": []})
        real["stats"] = {"q%d" % i: {"n": 5, "m": 1 + (i % 3 == 0), "r": []} for i in range(100)}
        real["stats"].update({"z%d" % i: {"n": 5, "m": 1, "r": []} for i in range(26)})
        cd = json.loads(json.dumps(real)); cd["lastModified"] = now - 300000
        set_ifc(real)
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with(fire=cd, floor=cd))
        pg.wait_for_timeout(2500); p = settle(pg)
        chk("C own record supports the count (%d misses, %d answers): 120 retakes kept, Smoke Diver unlocked and still worn" % (p["misses"], p["answered"]),
            p["misses"] >= 120 and p["retaken"] == 120 and p["maskedLocked"] is False and p["avatar"] == p["maskedId"] and "masked" in p["shown"], p)
        pg.wait_for_timeout(4000); p = probe(pg)
        chk("C and after the document is written and another boot", p["retaken"] == 120 and p["maskedLocked"] is False, p)
        pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()"); p = settle(pg)
        chk("C after another boot", p["retaken"] == 120 and p["maskedLocked"] is False and p["avatar"] == p["maskedId"], p)
        # live: a question missed then answered again counts one retake, and a merge afterwards does not undo it
        live = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
          const before = { r: store.retakenQuestions, m: Object.keys(store.stats).reduce((n, k) => n + store.stats[k].m, 0) };
          beginRun([0,1,2], null);
          for(let i = 0; i < 60 && !document.querySelector('#stage .choice'); i++) await W(200);
          const first = document.querySelector('#stage .choice'); if(!first) return { err: 'no question' };
          const qi = order[pos]; const right = correctSlot(qi); const wrong = right === 0 ? 1 : 0;
          choose(wrong); await W(700); choose(right); await W(700);
          const after = { r: store.retakenQuestions, m: Object.keys(store.stats).reduce((n, k) => n + store.stats[k].m, 0) };
          const hi = JSON.parse(JSON.stringify(store)); hi.lastModified = Date.now() + 5000; syncSameAccount(hi);
          return { before, after, merged: store.retakenQuestions }; }""")
        chk("C live: a Drill question missed then answered again counts one retake (and one miss on record) and a merge keeps it",
            "err" not in live and live["after"]["r"] == live["before"]["r"] + 1 and live["after"]["m"] == live["before"]["m"] + 1 and live["merged"] == live["after"]["r"], live)
        chk("C no script error", not errs, errs)
        ctx.close()

    # ---------------- (D) the academy is unaffected ----------------
    with section("D"):
        ac = heavy_academy(avatarChar="masked", stats={"a": {"n": 3, "m": 1, "r": []}})
        ac["lifetime"] = dict(ac["lifetime"], answered=50)
        G["academy"].clear(); G["academy"].update(ac)
        ctx, pg, errs = G["page"](br, G["init"]("academy"), seed=cloud_with())
        pg.wait_for_timeout(2500); p = probe(pg)
        chk("D academy: its 640 retakes and 12 Hardcore units count, the Masked One is its own", p["cls"] == "academy" and p["retaken"] == 640 and p["hc"] == 12 and p["maskedLocked"] is False, p)
        pg.wait_for_timeout(2500)
        saved = pg.evaluate("()=>JSON.parse(localStorage.getItem('class26e.drill.v1') || 'null')")
        chk("D academy: its saved copy lowered nothing", saved and saved.get("retakenQuestions") == 640 and len(saved.get("unitGameBeat") or {}) == 12 and saved.get("avatarChar") == "masked", saved and {k: saved.get(k) for k in ("retakenQuestions", "avatarChar")})
        ctx.close()

    # ---------------- (E) the backfill ----------------
    with section("E"):
        G["academy"].clear(); G["academy"].update(heavy_academy())
        unseeded = fc_base(challengeSeed289=False, retakenQuestions=0,
                           lifetime={"answered": 400, "correct": 250, "drillPlays": 20, "examPlays": 0, "gamePlays": 0, "perfectTests": 0, "currentStreak": 0, "longestStreak": 5, "points": 1800, "fullTests": 0})
        unseeded["stats"] = {"q%d" % i: {"n": 4, "m": 1, "r": []} for i in range(150)}
        set_ifc(unseeded)
        ctx, pg, errs = G["page"](br, G["init"]("ifc", with_ifc=True), seed=cloud_with())
        pg.wait_for_timeout(3000)
        r = pg.evaluate(BEGIN); pg.wait_for_timeout(1800); p = probe(pg)
        chk("E a Fire Code store with 150 misses on record and its seeded flag false: its first drill start backfills nothing (retakes %s, was misses x drill share = 150 in a store that never made them) and sets the flag" % p["retaken"],
            r == "ok" and p["retaken"] == 0 and p["seed"] is True and p["maskedLocked"] is True and not p["featsDone"], (r, p))
        ctx.close()
    br.close()

print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
