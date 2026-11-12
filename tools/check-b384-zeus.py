#!/usr/bin/env python3
"""Build 384.51: Zeus, one winner a week. Academy `zeus` (challenge `weektop`: weeklyWins >= 1, "first place on the weekly board").

The finding (live data, counts only): six accounts held a weekly win, and two of the weeks they listed were each listed by TWO accounts
(a week has one first place); two of the six have a win count with no listed week (the owner's hand-set grants of 312.3).

What this holds the build to, every line written to FAIL on 384.48 (run it `--against` that build's index.html):
 (A) A WEEK LISTED BY TWO ACCOUNTS IS ONE WIN. The two weeks the live data doubled are pinned to the account with by far the most
     lifetime XP of each pair (WEEK_WIN_PINS): the other loses it on load, with the character locked on every surface (not worn - the class's
     first starter, the look kept -, not queued, not marked announced or seen), and the pinned one keeps it, worn and marked as it was.
 (B) THE REST OF THE WEEKS, BY THE BOARD: a week another account's row claims with a better claim (more points; a claim with points beats
     one with none; then more lifetime XP; then the lower public id) is taken off the account that has the worse one - and only that one:
     every claim has exactly one of two answers against every other, so exactly one of any set keeps it. A claim nobody beats is kept,
     and a board that did not come from the server, or whose row does not list the week, changes nothing.
 (C) A RULE, NOT AN EDIT: after the loss, a copy that still holds the win (newer or older, from a second device, with the floor alone
     holding it) cannot put it back, and the document and the floor about to be written come down with it (writeAccount).
 (D) HONEST WINNERS AND THE OWNER'S GRANTS KEEP THEIRS: a listed week nobody else claims, a win no listed week backs (grants), after a
     boot and after a merge - and two accounts' grants merged into one are both kept while a week both listed is one week.
 (E) A DOUBLE SETTLE CANNOT ADD A SECOND WINNER: a week this account already holds adds nothing when its other device settles it; a
     week it lost is not taken back; a tie is one winner (the lower public id); a week read only off a sighting (more than one back) is not
     a win; the claim records the points it was made with and the row publishes it.
 (F) NOTHING IS ANNOUNCED: nothing is queued or marked as a result of a loss, and a win that is real afterwards is announced as it should be.
Run:  python3 tools/check-b384-zeus.py [--against OLD/index.html]     (384.48 must FAIL)"""
import functools, http.server, io, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(ROOT, "index.html")
BODY = INSET_RE.sub(lambda m: "0px", io.open(SRC, encoding="utf-8").read())
STORE = ("{\"firstName\":\"Madison\",\"avatarChar\":\"ninja\",\"onboardingComplete\":true,"
         "\"leaderboardOptIn\":true,\"lastModified\":1700000000000,"
         "\"lifetime\":{\"points\":420,\"correct\":88,\"perfectTests\":2}}")
so = socket.socket(); so.bind(("127.0.0.1", 0)); PORT = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT
fails = []
def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + detail) if detail else ""))
    if not ok: fails.append(name)

INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');"
        "localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % STORE)

PRE = """()=>{
  /* a build without the rule has no such functions: the checks then fail on what they measure, not by throwing */
  ['arbitrateWeekWins', 'weekWinsRepair'].forEach(n => { if(typeof window[n] !== 'function') window[n] = () => false; });
  if(typeof window.weekClaimBeats !== 'function') window.weekClaimBeats = () => false;
  if(typeof window.applyWeekWinVoids !== 'function') window.applyWeekWinVoids = () => false;
  window.CL = o => JSON.parse(JSON.stringify(o));
  window.Z = AVATAR_CHARACTERS.find(c => c.feat === 'weektop').id;
  window.BASE = CL(store);
  saveStore = () => {}; scheduleCloudPush = () => {}; persistLocally = () => {};
  /* an account of that shape: wearing Zeus, queued, marked announced and seen */
  window.mk = o => Object.assign(CL(BASE), { avatarChar: Z, pendingCharUnlocks: [Z], unlocksShown: { chars: [Z], banners: [], fx: [] },
    seenUnlocks: { chars: [Z], banners: [], fx: [] }, weekWinBase: null }, o || {});
  window.look = () => ({ ww: store.weeklyWins, char: store.avatarChar, locked: isLockedCharacter(Z),
    pend: (store.pendingCharUnlocks || []).indexOf(Z) >= 0, shown: ((store.unlocksShown || {}).chars || []).indexOf(Z) >= 0,
    seen: ((store.seenUnlocks || {}).chars || []).indexOf(Z) >= 0, banner: store.banner, weeks: (store.weekWinWeeks || []).slice() });
  window.docLook = d => d ? ({ ww: d.weeklyWins, char: d.avatarChar, pend: (d.pendingCharUnlocks || []).indexOf(Z) >= 0,
    shown: ((d.unlocksShown || {}).chars || []).indexOf(Z) >= 0, seen: ((d.seenUnlocks || {}).chars || []).indexOf(Z) >= 0 }) : null;
  window.first = classDefaultCharacter();
  window.row = (pub, xp, wins) => ({ pub, firstName: pub, xp, wins, week: weekKeyNow(), weekPoints: 0 });
  window.board = rows => { leaderboardRows = rows; leaderboardRowsFromServer = true; };
  return true; }"""

def ev(pg, js):
    try: return pg.evaluate(js)
    except Exception as e: return {"__err": str(e)[:200]}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    ctx = br.new_context(viewport={"width": 834, "height": 1194})
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto(URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.evaluate(PRE)

    # ---- A. the two doubled weeks ----
    print("\nA. a week two accounts listed is one win")
    r = ev(pg, """()=>{
      const o = {};
      /* 5 Oct: the account with less XP of the pair, and the pinned one */
      applyLoadedData(mk({ publicId: 'zwxdcbzmzasn', weeklyWins: 1, weekWinWeeks: ['2026-10-05'], lifetime: Object.assign(CL(BASE.lifetime), { points: 154259 }) }));
      o.lowA = look();
      applyLoadedData(mk({ publicId: '3gkuv79t4vzd', weeklyWins: 4, weekWinWeeks: ['2026-10-05', '2026-10-12', '2026-10-26', '2026-11-02'], lifetime: Object.assign(CL(BASE.lifetime), { points: 342160 }) }));
      o.keepA = look();
      /* 19 Oct */
      applyLoadedData(mk({ publicId: 'tupi8gt8cajh', weeklyWins: 1, weekWinWeeks: ['2026-10-19'] }));
      o.lowB = look();
      applyLoadedData(mk({ publicId: 'hhx364dust79', weeklyWins: 1, weekWinWeeks: ['2026-10-19'] }));
      o.keepB = look();
      o.first = first;
      return o; }""")
    ok = lambda s, ww: s.get("ww") == ww
    check("5 Oct: the account that lost it has no win and Zeus is locked", ok(r.get("lowA", {}), 0) and r["lowA"]["locked"], str(r.get("lowA", r)))
    check("...not worn (the class's first starter), not queued, not marked announced or seen",
          r["lowA"]["char"] == r["first"] and not r["lowA"]["pend"] and not r["lowA"]["shown"] and not r["lowA"]["seen"], str(r.get("lowA", r)))
    check("5 Oct: the pinned account keeps all four wins, worn, announced and seen",
          ok(r.get("keepA", {}), 4) and not r["keepA"]["locked"] and r["keepA"]["char"] == "zeus" or (ok(r.get("keepA", {}), 4) and not r["keepA"]["locked"] and r["keepA"]["char"] != r["first"]), str(r.get("keepA", r)))
    check("...and keeps its marks (nothing is taken from an account the record supports)", r["keepA"]["shown"] and r["keepA"]["pend"], str(r.get("keepA", r)))
    check("19 Oct: the other account loses it, the pinned one keeps it",
          ok(r.get("lowB", {}), 0) and r["lowB"]["locked"] and ok(r.get("keepB", {}), 1) and not r["keepB"]["locked"], str([r.get("lowB"), r.get("keepB")]))

    # ---- B. the board decides the weeks nobody pinned ----
    print("\nB. a better claim on the board takes the week from the worse one")
    W = "2026-10-26"
    JS_B = """(W)=>{
      const o = {}; const me = 'mmmm00000001';
      const base = (xp, pts) => mk({ publicId: me, weeklyWins: 1, weekWinWeeks: [W], weekWinPts: pts ? { [W]: pts } : {}, lifetime: Object.assign(CL(BASE.lifetime), { points: xp }) });
      const run = (xp, pts, rows) => { applyLoadedData(base(xp, pts)); board(rows); const c = arbitrateWeekWins(); return Object.assign({ changed: c, lost: (store.weekWinLost || []).slice() }, look()); };
      o.moreXp  = run(300000, 0, [row('other0000001', 200000, { [W]: 0 })]);
      o.lessXp  = run(100000, 0, [row('other0000001', 200000, { [W]: 0 })]);
      o.morePts = run(100000, 41000, [row('other0000001', 900000, { [W]: 40000 })]);
      o.lessPts = run(900000, 39000, [row('other0000001', 100000, { [W]: 40000 })]);
      o.ptsVsNone = run(900000, 0, [row('other0000001', 100000, { [W]: 40000 })]);
      o.noneVsPts = run(100000, 40000, [row('other0000001', 900000, { [W]: 0 })]);
      o.tiePub  = run(100000, 40000, [row('zzzz00000001', 100000, { [W]: 40000 })]);
      o.tieLow  = run(100000, 40000, [row('aaaa00000001', 100000, { [W]: 40000 })]);
      o.noRow   = run(100000, 0, [row('other0000001', 900000, {})]);
      o.otherWk = run(100000, 0, [row('other0000001', 900000, { '2026-11-02': 0 })]);
      applyLoadedData(base(100000, 0)); leaderboardRows = [row('other0000001', 900000, { [W]: 0 })]; leaderboardRowsFromServer = false;
      o.cached = Object.assign({ changed: arbitrateWeekWins() }, look());
      /* a total order: three claimants on one week, each one judging itself against the other two - exactly one keeps it */
      const claims = [{ pub: 'c1', xp: 50, pts: 0 }, { pub: 'c2', xp: 70, pts: 0 }, { pub: 'c3', xp: 10, pts: 5000 }, { pub: 'c4', xp: 90, pts: 5000 }, { pub: 'c5', xp: 90, pts: 5000 }];
      o.keepers = claims.filter(a => claims.every(b => b === a || !weekClaimBeats(b, a))).map(c => c.pub);
      o.first = first;
      return o; }"""
    r = pg.evaluate(JS_B, W)
    check("more lifetime XP than the other claim (neither has points): keeps it", r["moreXp"]["ww"] == 1 and not r["moreXp"]["changed"] and not r["moreXp"]["locked"], str(r["moreXp"]))
    check("less lifetime XP: loses it - the count, Zeus locked, not worn, not queued, not marked",
          r["lessXp"]["ww"] == 0 and r["lessXp"]["locked"] and r["lessXp"]["changed"] and W in r["lessXp"]["lost"] and r["lessXp"]["char"] == r["first"]
          and not r["lessXp"]["pend"] and not r["lessXp"]["shown"] and not r["lessXp"]["seen"], str(r["lessXp"]))
    check("fewer points than the other claim loses it even with more XP; more points keeps it even with less XP (the first is lessPts)",
          r["lessPts"]["ww"] == 0 and r["morePts"]["ww"] == 1 and r["lessPts"]["locked"] is True, str([r["lessPts"], r["morePts"]]))
    check("a claim with points beats one without (either way round)", r["ptsVsNone"]["ww"] == 0 and r["noneVsPts"]["ww"] == 1, str([r["ptsVsNone"]["ww"], r["noneVsPts"]["ww"]]))
    check("equal points and XP: the lower public id keeps it", r["tiePub"]["ww"] == 1 and r["tieLow"]["ww"] == 0, str([r["tiePub"]["ww"], r["tieLow"]["ww"]]))
    check("exactly one of any set of claimants is never beaten", len(r["keepers"]) == 1, str(r["keepers"]))
    check("a board row that does not list the week, or lists another, changes nothing", r["noRow"]["ww"] == 1 and r["otherWk"]["ww"] == 1, str([r["noRow"]["ww"], r["otherWk"]["ww"]]))
    check("a board that did not come from the server changes nothing", r["cached"]["ww"] == 1 and not r["cached"]["changed"], str(r["cached"]))

    # ---- C. a rule, not an edit ----
    print("\nC. a copy that still holds the win cannot put it back")
    r = pg.evaluate("""async (W)=>{
      const o = {}; const me = 'mmmm00000001'; const wait = ms => new Promise(res => setTimeout(res, ms));
      const lostCopy = () => { applyLoadedData(mk({ publicId: me, weeklyWins: 1, weekWinWeeks: [W], lifetime: Object.assign(CL(BASE.lifetime), { points: 100000 }) }));
        board([row('other0000001', 200000, { [W]: 0 })]); arbitrateWeekWins(); return look(); };
      o.start = lostCopy();
      const holder = Object.assign(mk({ publicId: me, weeklyWins: 1, weekWinWeeks: [W] }), { lifetime: CL(store.lifetime) });
      holder.weekWinLost = []; delete holder.weekWinBase;
      const newer = CL(holder); newer.lastModified = Date.now() + 99999;
      syncSameAccount(newer); o.newer = look();
      const older = CL(holder); older.lastModified = 1;
      syncSameAccount(older); o.older = look();
      /* the floor alone holds it: merged in the way markCloudConfirmed merges it */
      mergeSameAccount(store, CL(holder)); applyWeekWinVoids(); o.floor = look();
      /* a second device on the old copy, booted fresh, then merged with the server's lowered copy */
      const lowered = CL(store);
      applyLoadedData(CL(holder)); const dev2 = look();
      mergeSameAccount(store, lowered); applyWeekWinVoids(); o.dev2after = look();
      o.dev2before = dev2;
      /* the account and its floor about to be written */
      lostCopy();
      const docs = {};
      const cloudDoc = Object.assign(CL(holder), { lastModified: Date.now() + 5000 });
      const cl = { 'progress/NOVA-2601': cloudDoc, 'progress/NOVA-2601__floor': CL(cloudDoc) };
      fbDb = { collection: name => ({ onSnapshot: () => () => {}, doc: id => ({ onSnapshot: () => () => {},
        get: () => Promise.resolve(cl[name + '/' + id] ? { exists: true, metadata: { fromCache: false }, data: () => CL(cl[name + '/' + id]) } : { exists: false, metadata: { fromCache: false } }),
        set: d => { docs[name + '/' + id] = CL(d); return Promise.resolve(); }, update: () => Promise.resolve(), delete: () => Promise.resolve() }) }) };
      syncCode = 'NOVA-2601'; cloudConfirmedFor = 'NOVA-2601'; floorMergedFor = 'NOVA-2601';
      writeAccount('NOVA-2601', true, true);
      await wait(600);
      o.doc = docLook(docs['progress/NOVA-2601']); o.floorDoc = docLook(docs['progress/NOVA-2601__floor']);
      o.first = first;
      return o; }""", W)
    cl = lambda s: s["ww"] == 0 and s["locked"] and s["char"] != "zeus" and not s["pend"] and not s["shown"] and not s["seen"]
    check("the loss is in effect (start)", cl(r["start"]), str(r["start"]))
    check("a newer and an older copy that still hold the win do not bring it back", cl(r["newer"]) and cl(r["older"]), str([r["newer"], r["older"]]))
    check("the floor alone holding it does not bring it back", cl(r["floor"]), str(r["floor"]))
    check("a second device on the old copy is corrected on its next merge", r["dev2after"]["ww"] == 0 and r["dev2after"]["locked"] and r["dev2after"]["char"] != "zeus", str([r["dev2before"], r["dev2after"]]))
    check("the account document about to be written carries none of it (count, worn, queued, marked)",
          r["doc"] is not None and r["doc"]["ww"] == 0 and r["doc"]["char"] != "zeus" and not r["doc"]["pend"] and not r["doc"]["shown"] and not r["doc"]["seen"], str(r["doc"]))
    check("...and so does its floor", r["floorDoc"] is not None and r["floorDoc"]["ww"] == 0 and r["floorDoc"]["char"] != "zeus" and not r["floorDoc"]["pend"] and not r["floorDoc"]["shown"], str(r["floorDoc"]))

    # ---- D. honest winners and grants ----
    print("\nD. honest winners and the owner's grants keep theirs")
    r = pg.evaluate("""()=>{
      const o = {}; const me = 'honest000001';
      applyLoadedData(mk({ publicId: me, weeklyWins: 1, weekWinWeeks: ['2026-10-12'] })); o.listed = look();
      board([row('other0000001', 900000, { '2026-11-02': 0 })]); arbitrateWeekWins(); o.listedBoard = look();
      applyLoadedData(mk({ publicId: 'xph5b57jbp5a', weeklyWins: 1, weekWinWeeks: [] })); o.grant = look(); o.grantBase = store.weekWinBase;
      applyLoadedData(CL(store)); o.grantBoot = look();
      const older = mk({ publicId: 'xph5b57jbp5a', weeklyWins: 1, weekWinWeeks: [] }); older.lastModified = 1;
      syncSameAccount(older); o.grantMerge = look();
      const newer = mk({ publicId: 'xph5b57jbp5a', weeklyWins: 1, weekWinWeeks: [] }); newer.lastModified = Date.now() + 99999;
      syncSameAccount(newer); o.grantMergeNewer = look();
      /* a grant AND a listed week, and a grant whose own week was lost */
      applyLoadedData(mk({ publicId: 'both00000001', weeklyWins: 2, weekWinWeeks: ['2026-10-12'] })); o.both = look(); o.bothBase = store.weekWinBase;
      applyLoadedData(mk({ publicId: 'grantlost001', weeklyWins: 2, weekWinWeeks: ['2026-10-05'] })); o.grantLost = look(); o.grantLostBase = store.weekWinBase;
      /* two accounts merged into one: both grants stay; a week both listed is one week */
      applyLoadedData(mk({ publicId: 'merge0000001', weeklyWins: 2, weekWinWeeks: ['2026-10-12'] }));   /* a grant and a week */
      const src = CL(store); src.publicId = 'merge0000002'; src.weeklyWins = 3; src.weekWinWeeks = ['2026-10-12', '2026-11-23']; delete src.weekWinBase;
      const dst = CL(store); const keepStore = store;
      try{ mergeLeavingAccount(src, { merge: true }); }catch(e){ o.mergeErr = String(e && e.message || e).slice(0, 100); }
      weekWinsRepair(store);
      o.merged = { ww: store.weeklyWins, weeks: store.weekWinWeeks.slice(), base: store.weekWinBase };
      return o; }""")
    check("a week nobody else claims is kept, with the board in", r["listed"]["ww"] == 1 and not r["listed"]["locked"] and r["listedBoard"]["ww"] == 1 and not r["listedBoard"]["locked"], str([r["listed"], r["listedBoard"]]))
    check("a hand-set grant (a win with no listed week) is kept on load, after a boot and after a merge from an older and a newer copy",
          r["grant"]["ww"] == 1 and not r["grant"]["locked"] and r["grantBase"] == 1 and r["grantBoot"]["ww"] == 1 and r["grantMerge"]["ww"] == 1 and r["grantMergeNewer"]["ww"] == 1 and not r["grantMergeNewer"]["locked"],
          str([r["grant"], r["grantMerge"], r["grantMergeNewer"]]))
    check("a grant plus a listed week is two wins; a grant whose neighbouring week was lost keeps the grant only",
          r["both"]["ww"] == 2 and r["bothBase"] == 1 and r["grantLost"]["ww"] == 1 and r["grantLostBase"] == 1 and not r["grantLost"]["locked"], str([r["both"], r["grantLost"]]))
    check("two accounts merged into one: both grants stay, a week both listed is one week",
          r["merged"]["ww"] == 4 and sorted(r["merged"]["weeks"]) == ["2026-10-12", "2026-11-23"] and r["merged"]["base"] == 2 and "mergeErr" not in r, str(r["merged"]) + " " + str(r.get("mergeErr")))

    # ---- E. the settle ----
    print("\nE. a double settle cannot add a second winner")
    r = pg.evaluate("""()=>{
      const o = {}; const lw = lastWeekKey(); const two = weekKeyBefore(lw); const me = 'mmmm00000001';
      const fresh = (extra) => { applyLoadedData(mk(Object.assign({ publicId: me, weeklyWins: 0, weekWinWeeks: [], avatarChar: 'ninja', pendingCharUnlocks: [], unlocksShown: { chars: [], banners: [], fx: [] }, seenUnlocks: { chars: [], banners: [], fx: [] } }, extra || {}))); };
      /* (1) the standings: a tie is one winner */
      const standing = (pub, mine, rows) => { fresh({ publicId: pub, prevWeekKey: lw, prevWeekPoints: mine, weekKey: weekKeyNow(), weekPoints: 0 }); board(rows); return finalRankForWeek(lw); };
      const rowsT = [{ pub: 'aaaa00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }, { pub: 'zzzz00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }];
      o.tieLow = standing('aaaa00000001', 5000, rowsT.slice(1)); o.tieHigh = standing('zzzz00000001', 5000, rowsT.slice(0, 1));
      o.tieBoth = [standing('aaaa00000001', 5000, rowsT), standing('zzzz00000001', 5000, rowsT)];
      o.clear = standing('mmmm00000001', 5100, [{ pub: 'aaaa00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }]);
      o.behind = standing('mmmm00000001', 4900, [{ pub: 'aaaa00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }]);
      /* (2) a win is counted once, with its points */
      fresh({ prevWeekKey: lw, prevWeekPoints: 5100, weekKey: weekKeyNow(), weekPoints: 0 }); board([{ pub: 'aaaa00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }]);
      store.weekRankSeen = { week: lw, rank: 1 };
      o.first = settleWeeklyWinQueued(); o.afterFirst = look(); o.pts = (store.weekWinPts || {})[lw]; o.pend = (store.pendingCharUnlocks || []).indexOf(Z) >= 0;
      const pubd = buildLeaderboardRow().wins; o.row = pubd;
      store.weekRankSeen = { week: lw, rank: 1 };       /* its other device settles the same week */
      o.second = settleWeeklyWin(); o.afterSecond = look();
      /* (3) a week this account lost is not taken back */
      fresh({ publicId: me, weeklyWins: 0, weekWinWeeks: [lw], weekWinLost: [lw], prevWeekKey: lw, prevWeekPoints: 5100 }); board([{ pub: 'aaaa00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }]);
      store.weekRankSeen = { week: lw, rank: 1 };
      o.lostSettle = settleWeeklyWin(); o.afterLost = look();
      /* (4) a week more than one back, read only off a sighting, is not a win */
      fresh({ prevWeekKey: lw, prevWeekPoints: 5100 }); board([{ pub: 'aaaa00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }]);
      store.weekRankSeen = { week: two, rank: 1 };
      o.old = settleWeeklyWin(); o.afterOld = look(); o.top3 = store.weeklyTop3;
      /* (5) the board not heard yet: wait, count nothing */
      fresh({ prevWeekKey: lw, prevWeekPoints: 5100 }); leaderboardRows = []; leaderboardRowsFromServer = false;
      store.weekRankSeen = { week: lw, rank: 1 };
      o.wait = settleWeeklyWin(); o.afterWait = look(); o.seenKept = !!store.weekRankSeen;
      return o; }""")
    check("a tie is one winner: the lower public id is first, the other second, and with both rows in exactly one is first",
          r["tieLow"] == 1 and r["tieHigh"] == 2 and sorted(r["tieBoth"]) == [1, 2], str([r["tieLow"], r["tieHigh"], r["tieBoth"]]))
    check("clearly ahead is first, clearly behind is second", r["clear"] == 1 and r["behind"] == 2, str([r["clear"], r["behind"]]))
    check("a real win counts once, lists the week, queues Zeus, records the points and publishes the claim",
          r["first"] is True and r["afterFirst"]["ww"] == 1 and len(r["afterFirst"]["weeks"]) == 1 and r["pend"] and r["pts"] == 5100 and list((r["row"] or {}).values()) == [5100],
          str([r["first"], r["afterFirst"], r["pts"], r["row"]]))
    check("the same week settled again (its other device) adds nothing", r["second"] is False and r["afterSecond"]["ww"] == 1 and len(r["afterSecond"]["weeks"]) == 1, str([r["second"], r["afterSecond"]]))
    check("a week it has lost is not taken back by a settle", r["lostSettle"] is False and r["afterLost"]["ww"] == 0 and r["afterLost"]["locked"], str([r["lostSettle"], r["afterLost"]]))
    check("a week more than one back, read only off a sighting, is not a win (the podium still counts)", r["old"] is False and r["afterOld"]["ww"] == 0 and r["top3"] >= 1, str([r["old"], r["afterOld"], r["top3"]]))
    check("with the board not heard from the server the settle waits and counts nothing", r["wait"] is False and r["afterWait"]["ww"] == 0 and r["seenKept"], str([r["wait"], r["afterWait"], r["seenKept"]]))

    # ---- F. nothing is announced by a loss; a later real win is ----
    print("\nF. no pop-up from a loss, and a real win afterwards is announced")
    r = pg.evaluate("""()=>{
      const o = {}; const lw = lastWeekKey(); const W = '2026-10-26';
      applyLoadedData(mk({ publicId: 'mmmm00000001', weeklyWins: 1, weekWinWeeks: [W], lifetime: Object.assign(CL(BASE.lifetime), { points: 100000 }) }));
      board([row('other0000001', 200000, { [W]: 0 })]); arbitrateWeekWins();
      o.afterLoss = look(); o.pendingAll = (store.pendingCharUnlocks || []).slice(); o.homePend = (store.pendingHomeUnlocks || []).slice();
      /* a real win next week */
      store.prevWeekKey = lw; store.prevWeekPoints = 6000; store.weekKey = weekKeyNow(); store.weekPoints = 0;
      board([{ pub: 'aaaa00000001', week: lw, rawWeekPoints: 5000, weekPoints: 0 }]);
      store.weekRankSeen = { week: lw, rank: 1 };
      o.won = settleWeeklyWinQueued(); o.afterWin = look(); o.pending = (store.pendingCharUnlocks || []).indexOf(Z) >= 0;
      return o; }""")
    check("a loss leaves nothing queued", r["afterLoss"]["pend"] is False and r["pendingAll"].count("zeus") == 0 and r["homePend"].count("zeus") == 0, str([r["pendingAll"], r["homePend"]]))
    check("a real win afterwards counts and is queued to be announced (it was un-marked by the loss)",
          r["won"] is True and r["afterWin"]["ww"] == 1 and not r["afterWin"]["locked"] and r["pending"] and not r["afterWin"]["shown"], str([r["won"], r["afterWin"], r["pending"]]))

    check("no page errors", not errs, str(errs[:3]))
    br.close()

print("\n%s" % ("ALL PASS" if not fails else "%d FAILED: %s" % (len(fails), fails)))
sys.exit(1 if fails else 0)
