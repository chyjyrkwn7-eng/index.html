#!/usr/bin/env python3
"""Build 384 r8: placement XP in every Virtual Room game, and one results screen for all three.

Madison, over a Tug of War result reading "+0 XP - Winner takes all": "Everybody should still get xp, you get it based on your
finishing spot x how many people are in the lobby". The rule he picked: N players, 1st = N shares, 2nd = N-1 ... last = 1; a share
is 25 XP; on top of your own answers. Team games: the winning side 1st, the losing side 2nd, a draw everybody 1st.
And over the old "Results - Ranked by total score" screen: "presented as a podium instead. The xp box isn't the same as all the
others? ... make it the same for all virtual rooms".

Drives the real result functions with room documents (the fake Firestore check-behaviour gives the room gates), iPhone 17 Pro Max:
  XP (read off store.lifetime.points, not off the screen)
   1 Tug of War, 2v2: the winners take 100 + their right answers x 10, the losers 75 + theirs
   2 a draw: 100 + your right answers x 10
   3 a 2v1 room is N = 3: winners 75 + answers, the loser 50 + answers
   4 Battle: 100 + answers for the win, 75 + answers for the loss (the flat 150 win bonus is gone - placement replaces it)
   5 a four-person Race pays 100 / 75 / 50 / 25 for its place, in the order the leaderboard cutscene ranks (XP, then time - one
     seat is a tie on XP decided by time), and the cutscene's own final order agrees
   6 paid once: the result drawn twice, and again as after a relaunch (the screen's own guard reset), and XP rises once
   7 a visitor from another class takes none, where a home player in the same seat takes 75 + answers
  THE RESULTS SCREEN (each game)
   8 the XP card carries the place as its own line ("1st of 4" ... and its +XP)
   9 the final screen has the results' grade card and the SAME XP card as a drill's (computed styles compared with a drill's results)
  10 a podium in the right order (the race: 1st/2nd/3rd by the ranking, the rest listed under; teams: the winners on the 1st step)
  11 no "pts" scoring anywhere: the old points screen is gone and no final screen says pts
  12 the room's chat is reachable from the final screen (the Room button opens it)
  13 no page errors, and every game ends on the results screen
  python3 tools/check-b384-vrplace.py [--against OLD/index.html]   (every check must FAIL on the build before)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)

SETUP = """()=>{ document.querySelectorAll('#splashscreen,#pushing-update,#intro-pop').forEach(n=>n.remove()); __useRooms(); __delay = 150;
  window.firebase = window.firebase || {}; firebase.firestore = firebase.firestore || {};
  firebase.firestore.FieldValue = { delete:()=>({_delete:true}), arrayUnion:(...a)=>({__au:a}), serverTimestamp:()=>Date.now() };
  theme.reduceMotion = true; try{ applyTheme(); }catch(e){}
  window.__seq = 0; window.__home = vroomForeign; }"""
# A team room: `teams` maps key -> side; `right` my right answers; returns the XP this result paid and what the screen shows.
TEAM = """async ([game, teams, winner, right, me, foreign]) => {
  const now = Date.now() - 400000 + (++__seq) * 1000;
  const names = { me:'Madison', a2:'Ben', b1:'Ava', b2:'Kim', x9:'Visitor' }, chars = { me:'ninja', a2:'wizard', b1:'ghost', b2:'alien', x9:'robot' };
  const parts = {}, prog = {};
  Object.keys(teams).forEach((k, i) => { parts[k] = { name:names[k] || k, avatarChar:chars[k] || 'ghost', level:10, badges:1, joinedAt:i + 1, ready:true, seen:9e15 };
    prog[k] = { pos:30, correct: k === me ? right : 12 + i, pull: 5, done:true, at: now }; });
  /* a hit per right answer, for the battle's damage board */
  const log = []; Object.keys(teams).forEach(k => { for(let j = 0; j < prog[k].correct; j++) log.push({ id: k + j, at: now + j * 1000 + log.length, from: k, kind: 'hit' }); });
  const g = { teams, progress: prog, over:true, winner: winner, finalPos: winner ? (winner === 'a' ? -9 : 9) : 0, count:30, log: [] };
  const gb = Object.assign({}, g, { log: log });
  window.__d = { status:'finished', startAt: now, units:['Identity Crimes'], game, participants: parts, tug: g, battle: JSON.parse(JSON.stringify(gb)) };
  __rooms['VRP' + __seq] = JSON.parse(JSON.stringify(__d));
  vroomCode = 'VRP' + __seq; vroomMyKey = me; vroomIsHost = true;
  vroomForeign = foreign ? (() => true) : __home;
  store.vrCounted = [];
  const p0 = store.lifetime.points;
  try{ detachTug(); }catch(e){}
  (game === 'tug' ? showTugResult : showBattleResult)(__d);
  const paid = store.lifetime.points - p0;
  vroomForeign = __home;
  await new Promise(r => setTimeout(r, 900));
  const place = document.querySelector('#stage .rs-xp .rs-xpline.is-place');
  return { paid, rewards: !!document.querySelector('#stage > .rs-rewards'), place: place ? place.textContent.replace(/\\s+/g, ' ').trim() : null,
           text: (document.getElementById('stage').textContent || '').replace(/\\s+/g, ' ') }; }"""
# Re-draw the same match: `relaunch` also resets the screen's own in-memory guard, as a relaunch would.
AGAIN = """async ([game, relaunch]) => { const p0 = store.lifetime.points;
  if(relaunch){ tugPaidFor = 0; battlePaidFor = 0; }
  try{ detachTug(); }catch(e){} (game === 'tug' ? showTugResult : showBattleResult)(__d);
  await new Promise(r => setTimeout(r, 300)); return store.lifetime.points - p0; }"""
# A four-person race: everybody else finished; my run (run XP `mine`) goes through the real finish and the finale's listener.
RACE = """async ([mine, myMs]) => {
  const now = Date.now() - 300000 + (++__seq) * 1000;
  const L = (c, s) => [{key:'correct', label:'Correct answers', value:c}, {key:'speed', label:'Speed', value:s}];
  vroomCode = 'VRR' + __seq; vroomMyKey = 'me'; vroomIsHost = true; store.vrCounted = [];
  __rooms[vroomCode] = { status:'started', startAt: now, units:['Identity Crimes'], game:'race', racers:['me','p2','p3','p4'], participants:{
    me:{ name:'Madison', avatarChar:'ninja', level:23, badges:4, joinedAt:1, ready:true, finished:false, progress:90, seen:9e15 },
    p2:{ name:'Devonte', avatarChar:'ghost', level:31, badges:6, joinedAt:2, ready:true, finished:true, progress:100, elapsedMs:200000, xp:330, xpLines:L(280,50), revealDone:true, seen:9e15 },
    p3:{ name:'Alex', avatarChar:'grizzly', level:47, badges:9, joinedAt:3, ready:true, finished:true, progress:100, elapsedMs:180000, xp:400, xpLines:L(340,60), revealDone:true, seen:9e15 },
    p4:{ name:'Kim', avatarChar:'alien', level:12, badges:2, joinedAt:4, ready:true, finished:true, progress:100, elapsedMs:260000, xp:210, xpLines:L(200,10), revealDone:true, seen:9e15 } } };
  const lines = [{ key:'correct', label:'Correct answers', sub: ((mine - 20) / 10) + ' \u00d7 10 XP', value: mine - 20 }, { key:'speed', label:'Speed', value: 20 }];
  lastRunRoomXp = { lines, total: mine };
  const b = badgeCountOf(store);
  const run = { total:30, good:28, pct:93, missed:[], isPerfect:false, elapsedMs:myMs, timedOut:false, order:[], attempts:{}, picked:{}, firstPick:{}, flare:null, flareAll:false, flareCount:0, timedOutSet:{},
    mode:'exam', retake:false, practice:false, vroom:true, vroomGame:'race', source:'all', units:['Identity Crimes'], unitsSat:['Identity Crimes'], byUnit:{ 'Identity Crimes':{ total:30, wrong:2 } },
    xpLines: lines, xpTotal: mine, pointsAfter: store.lifetime.points, badgesBefore:b, badgesAfter:b, hundosEarned:0, leveledUpTo:null, newBest:false, progUnits:[], perfectsBefore:{},
    badges:[], retroBadges:[], colors:[], characters:[], banners:[], fx:[], supernova:false };
  showRunRewards(run, { finalActions: () => document.createElement('div'), tour: () => {} });
  await new Promise(r => setTimeout(r, 200));
  const p0 = store.lifetime.points;
  finishVirtualRoomTest(93, myMs);
  for(let i = 0; i < 40 && !document.querySelector('.vroom-waitcard.is-all-in'); i++) await new Promise(r => setTimeout(r, 100));
  await new Promise(r => setTimeout(r, 200));
  const order = vroomRankedEntries(lastFinaleData || __rooms[vroomCode]).map(e => e.key);
  return { paid: store.lifetime.points - p0, place: order.indexOf('me') + 1, order }; }"""
# The cutscene and its way on, from the room as the finale last saw it.
CUT = """async () => { startVroomRaceCutscene();
  for(let i = 0; i < 60 && !document.querySelector('#vroom-race-cut.is-done'); i++) await new Promise(r => setTimeout(r, 100));
  const rows = [...document.querySelectorAll('#vroom-race-cut .vrc-row')];
  const cutOrder = rows.map(r => (r.querySelector('.vrc-name-text') || {}).textContent);
  const nums = rows.map(r => Number((r.querySelector('.vrc-num') || {}).textContent.replace(/[^\\d]/g, '')) || 0);
  const cont = document.querySelector('#vroom-race-cut .vrc-continue');
  if(cont) cont.click();
  await new Promise(r => setTimeout(r, 1200));
  const place = document.querySelector('#stage .rs-xp .rs-xpline.is-place');
  return { cutOrder, nums, cont: !!cont, rewards: !!document.querySelector('#stage > .rs-rewards'), place: place ? place.textContent.replace(/\\s+/g, ' ').trim() : null,
           text: (document.getElementById('stage').textContent || '').replace(/\\s+/g, ' ') }; }"""
# The final screen's cards against a drill's: the grade card and the XP card, by computed style.
STYLE = """() => { const pick = (sel) => { const e = document.querySelector('#stage ' + sel); if(!e) return null; const c = getComputedStyle(e);
    return [c.backgroundColor, c.borderTopLeftRadius, c.paddingTop, c.paddingLeft, c.borderTopWidth, c.boxShadow].join(' | '); };
  const fs = (sel) => { const e = document.querySelector('#stage ' + sel); return e ? getComputedStyle(e).fontSize + ' ' + getComputedStyle(e).fontWeight : null; };
  return { grade: pick('.rs-grade'), xp: pick('.rs-xp'), kick: fs('.rs-xp .rs-kicker'), line: fs('.rs-xp .rs-xpline-name'), total: fs('.rs-xp .rs-xptotal-num'),
           level: !!document.querySelector('#stage .rs-xp .results-level'), oldBox: !!document.querySelector('#stage .tug-xp') }; }"""
DRILL = """async () => { const b = badgeCountOf(store);
  const lines = [{ key:'correct', label:'Correct answers', sub:'9 x 10 XP', value:90 }, { key:'speed', label:'Speed', value:20 }];
  const run = { total:10, good:9, pct:90, missed:[], isPerfect:false, elapsedMs:60000, timedOut:false, order:[], attempts:{}, picked:{}, firstPick:{}, flare:null, flareAll:false, flareCount:0, timedOutSet:{},
    mode:'drill', retake:false, practice:false, vroom:false, source:'all', units:['Identity Crimes'], unitsSat:['Identity Crimes'], byUnit:{ 'Identity Crimes':{ total:10, wrong:1 } },
    xpLines: lines, xpTotal: 110, pointsAfter: store.lifetime.points, badgesBefore:b, badgesAfter:b, hundosEarned:0, leveledUpTo:null, newBest:false, progUnits:[], perfectsBefore:{},
    badges:[], retroBadges:[], colors:[], characters:[], banners:[], fx:[], supernova:false };
  showRunRewards(run, { finalActions: () => { const d = document.createElement('div'); d.className = 'actions'; return d; }, tour: () => {} });
  await new Promise(r => setTimeout(r, 900)); }"""
PODIUM = """() => { const c = document.querySelector('#stage .vr-podium'); if(!c) return null;
  return { spots: [...c.querySelectorAll('.lw-podium-spot')].map(s => ({ key: s.dataset.key || null, side: s.dataset.side || null, place: (s.className.match(/lw-place-(\\d)/) || [])[1] })),
           list: [...c.querySelectorAll('.vr-podium-list .vr-podium-row')].map(r => r.dataset.key) }; }"""
CHAT = """async () => { const fab = document.getElementById('roomchat-fab'); if(!fab) return { fab:false };
  fab.click(); await new Promise(r => setTimeout(r, 400)); const sheet = document.getElementById('roomchat-sheet');
  const out = { fab:true, opened: !!(sheet && sheet.querySelector('.vroom-chat')) }; try{ closeRoomChatSheet(); }catch(e){} return out; }"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1, init=cb._ROOM_FAKE)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.evaluate(SETUP)
    def ev(js, arg=None):
        try: return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        except Exception as e: errs.append("harness: " + str(e)[:1500]); return None
    T22 = {"me": "a", "a2": "a", "b1": "b", "b2": "b"}
    # 1 a 2v2 tug, won and lost
    win = ev(TEAM, ["tug", T22, "a", 24, "me", False]) or {}
    loss = ev(TEAM, ["tug", T22, "b", 24, "me", False]) or {}
    chk("1 Tug 2v2: winners 100 + 24 x 10 = 340 (paid %s), losers 75 + 240 = 315 (paid %s)" % (win.get("paid"), loss.get("paid")), win.get("paid") == 340 and loss.get("paid") == 315, (win.get("paid"), loss.get("paid")))
    # 2 a draw
    draw = ev(TEAM, ["tug", T22, None, 18, "me", False]) or {}
    chk("2 Tug draw: everybody 1st, 100 + 18 x 10 = 280 (paid %s)" % draw.get("paid"), draw.get("paid") == 280, draw.get("paid"))
    # 3 a 2v1 room
    T21 = {"me": "a", "a2": "a", "b1": "b"}
    w3 = ev(TEAM, ["tug", T21, "a", 10, "me", False]) or {}
    l3 = ev(TEAM, ["tug", {"a2": "a", "b1": "a", "me": "b"}, "a", 10, "me", False]) or {}
    chk("3 a 2v1 room is N = 3: the winners 75 + 100 = 175 (paid %s), the one loser 50 + 100 = 150 (paid %s)" % (w3.get("paid"), l3.get("paid")), w3.get("paid") == 175 and l3.get("paid") == 150, (w3.get("paid"), l3.get("paid")))
    # 4 battle
    bw = ev(TEAM, ["battle", T22, "a", 31, "me", False]) or {}
    battle_text = (bw.get("text") or "")
    bwStyle = ev(STYLE) or {}
    bwPod = ev(PODIUM)
    bwChat = ev(CHAT) or {}
    bl = ev(TEAM, ["battle", T22, "b", 31, "me", False]) or {}
    chk("4 Battle: placement replaces the flat win bonus - the win 100 + 310 = 410 (paid %s), the loss 75 + 310 = 385 (paid %s)" % (bw.get("paid"), bl.get("paid")), bw.get("paid") == 410 and bl.get("paid") == 385, (bw.get("paid"), bl.get("paid")))
    # 6 once only (the last tug: draw it twice, then as after a relaunch)
    ev(TEAM, ["tug", T22, "a", 20, "me", False])
    again = ev(AGAIN, ["tug", False]); relaunch = ev(AGAIN, ["tug", True])
    chk("6 paid once: drawn again +%s XP, again after a relaunch +%s XP (both 0)" % (again, relaunch), again == 0 and relaunch == 0, (again, relaunch))
    # 7 a visitor from another class, against a home player in the same seat
    fx = ev(TEAM, ["tug", T22, "b", 24, "me", True]) or {}
    chk("7 a visitor takes nothing (%s) where a home player on the losing side takes 75 + 240 (%s)" % (fx.get("paid"), loss.get("paid")), fx.get("paid") == 0 and loss.get("paid") == 315, (fx.get("paid"), loss.get("paid")))
    # the tug's final screen, for 8-13
    tw = ev(TEAM, ["tug", T22, "a", 24, "me", False]) or {}
    tugStyle = ev(STYLE) or {}; tugPod = ev(PODIUM); tugChat = ev(CHAT) or {}
    tl = ev(TEAM, ["tug", T22, "b", 24, "me", False]) or {}
    tlPod = ev(PODIUM)
    # 5 the race, four seats
    seats = []
    for mine, ms, want in ((420, 150000, 1), (330, 190000, 2), (330, 210000, 3), (100, 300000, 4)):
        r = ev(RACE, [mine, ms]) or {}
        seats.append((want, r.get("place"), r.get("paid"), r.get("order")))
    exp = {1: 100, 2: 75, 3: 50, 4: 25}
    chk("5 Race: places 1-4 pay 100/75/50/25 on top of the run, ranked by XP then time (a 330 tie split by time) %s" % [(w, p, x) for w, p, x, _ in seats],
        all(p == w and x == exp[w] for w, p, x, _ in seats), seats)
    # the last race (4th): its cutscene and Continue, and the cutscene's own order
    cut = ev(CUT) or {}
    raceStyle = ev(STYLE) or {}; racePod = ev(PODIUM); raceChat = ev(CHAT) or {}
    names = {"me": "Madison", "p2": "Devonte", "p3": "Alex", "p4": "Kim"}
    last_order = seats[-1][3] or []
    chk("5b the cutscene's final order is the order paid (%s vs %s), and its numbers include the place (Alex 400 + 100 = %s)" % (cut.get("cutOrder"), [names.get(k) for k in last_order], (cut.get("nums") or [0])[0]),
        cut.get("cutOrder") == [names.get(k) for k in last_order] and (cut.get("nums") or [0])[0] == 500, cut)
    # 8 the place line
    chk("8 the XP card carries the place as its own line: Tug %r, loss %r, Battle %r, Race %r" % (tw.get("place"), tl.get("place"), bw.get("place"), cut.get("place")),
        all(re.match(r"^1st of 4.*\+100$", x or "") for x in (tw.get("place"), bw.get("place"))) and re.match(r"^2nd of 4.*\+75$", tl.get("place") or "") and re.match(r"^4th of 4.*\+25$", cut.get("place") or ""),
        (tw.get("place"), tl.get("place"), bw.get("place"), cut.get("place")))
    # 9 the same cards as a drill
    ev(DRILL); drill = ev(STYLE) or {}
    same = lambda s: s.get("grade") and s.get("xp") and all(s.get(k) == drill.get(k) for k in ("grade", "xp", "kick", "line", "total")) and s.get("level") and not s.get("oldBox")
    chk("9 the final screens' grade and XP cards are a drill's (Tug %s, Battle %s, Race %s)" % (bool(same(tugStyle)), bool(same(bwStyle)), bool(same(raceStyle))),
        same(tugStyle) and same(bwStyle) and same(raceStyle), {"drill": drill, "tug": tugStyle, "race": raceStyle})
    # 10 podiums
    rp = racePod or {}
    rp_ok = [s["key"] for s in rp.get("spots", [])] == last_order[:3] and [s["place"] for s in rp.get("spots", [])] == ["1", "2", "3"] and rp.get("list") == last_order[3:]
    side_ok = lambda pod, win_side: pod and len(pod["spots"]) == 2 and [s["place"] for s in pod["spots"] if s["side"] == win_side] == ["1"] and [s["place"] for s in pod["spots"] if s["side"] != win_side] == ["2"]
    chk("10 podiums: the race 1-2-3 by the ranking with 4th listed under (%s); Tug and Battle winners on the 1st step, losers on the 2nd" % ([s.get("key") for s in rp.get("spots", [])],),
        rp_ok and side_ok(tugPod, "a") and side_ok(tlPod, "b") and side_ok(bwPod, "a"), {"race": racePod, "tug": tugPod, "tugLoss": tlPod, "battle": bwPod})
    # 11 no points
    gone = ev("() => typeof showVirtualRoomResults === 'undefined' && typeof vroomTopThree === 'undefined'")
    pts = [n for n, t in (("tug", tw.get("text")), ("battle", battle_text), ("race", cut.get("text"))) if re.search(r"\bpts\b", t or "")]
    chk("11 no points scoring: the old points screen is gone (%s) and no final screen says pts (%s)" % (gone, pts or "none"), gone is True and not pts, (gone, pts))
    # 12 chat
    chk("12 the room's chat opens from the final screen: Tug %s, Battle %s, Race %s" % (tugChat.get("opened"), bwChat.get("opened"), raceChat.get("opened")),
        tugChat.get("opened") and bwChat.get("opened") and raceChat.get("opened"), (tugChat, bwChat, raceChat))
    # 13
    ended = tw.get("rewards") and bw.get("rewards") and cut.get("rewards") and cut.get("cont")
    chk("13 no page errors, and every game ends on the results screen (%s)" % bool(ended), not errs and ended, errs[:4] or (tw.get("rewards"), bw.get("rewards"), cut))
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
