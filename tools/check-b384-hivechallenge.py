"""Build 384 r14: the Hive (academy) / Sprinkler Head (Fire Code) challenge is hosting three Virtual Room matches to the end.
Madison: "host 3 virtual room matches ... They would need to fully finish each match. Doesn't need to be back to back."
(It was a hundo on the class's biggest unit, 384 r13.) In both classes, driving the real end of a match (the race's finale
listener, showTugResult, showBattleResult) with room documents in the fake Firestore the room gates use:
 (1) the label is "Host N Virtual Room matches", N its own need, and the unlock card's note says to play the match to the end;
 (2) a new account is locked at 0; two hosted, finished matches (a Tug of War, a Battle) count 2 and it is still locked;
     a third (a Race, through the finale's own listener) opens it;
 (3) only a match this account STARTED as host counts: one it joined (started by somebody else) does not, nor one it hosted
     with only Nova (no classmate), nor one it hosted and left before the end (abandoned);
 (4) no double count: the same result drawn again, and again as after a relaunch (the screen's own guard reset), adds nothing;
 (5) the counter is a persisted field: defaulted to 0 when missing and kept through applyLoadedData; no page errors;
 (6) it merges as a progress counter: the larger of one account's copies (mergeSameAccount), the sum when an account is folded in.
Run:  python3 tools/check-b384-hivechallenge.py   (--against OLD/index.html must FAIL)"""
import os, sys, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
a = json.loads(cb.USED_ACCOUNT); a["publicId"] = "xph5b57jbp5a"; a["novaMet"] = 99; IACCT = json.dumps(a)
IINIT = ("try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
         "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
         "localStorage.setItem('class26e.ifc.drill.v1', %s);}catch(e){}" % json.dumps(IACCT))
SETUP = """()=>{ document.querySelectorAll('#splashscreen,#pushing-update,#intro-pop').forEach(n=>n.remove()); __useRooms(); __delay = 150;
  window.firebase = window.firebase || {}; firebase.firestore = firebase.firestore || {};
  firebase.firestore.FieldValue = { delete:()=>({_delete:true}), arrayUnion:(...x)=>({__au:x}), serverTimestamp:()=>Date.now() };
  theme.reduceMotion = true; theme.muteBanners = true; window.__seq = 0;
  store.vrHosted = 0; store.vrCounted = []; window.__me = publicIdOf(); }"""
# The challenge, read off the app; and the counter
STATE = """()=>{ const f = CHARACTER_FEATS.busyday300 || {}; let note = ''; try{ note = unlockNoteFor({kind:'character', id:'hive'}); }catch(e){ note = 'ERR ' + e; }
  return { label: String(f.label), need: f.need, have: f.have ? f.have() : null, locked: isLockedCharacter('hive'), note, hosted: store.vrHosted, name: AVATAR_DISPLAY_NAME.hive }; }"""
# A Tug of War or Battle result. `startedBy` is 'me' (this account), another key, or null; `others` the other keys in the match.
TEAM = """async ([game, startedBy, others]) => {
  const me = __me, now = Date.now() - 400000 + (++__seq) * 1000;
  const keys = [me].concat(others), teams = {}, prog = {}, parts = {};
  keys.forEach((k, i) => { teams[k] = i % 2 ? 'b' : 'a'; prog[k] = { pos: 20, correct: 10 + i, pull: 3, done: true, at: now };
    parts[k] = { name: k === me ? 'Madison' : k === 'nova' ? 'Nova' : 'P' + i, avatarChar: 'ghost', level: 10, badges: 1, joinedAt: i + 1, ready: true, seen: 9e15 }; });
  const g = { teams, progress: prog, over: true, winner: 'a', finalPos: -9, count: 20, log: [] };
  const d = { status: 'finished', startAt: now, units: ['x'], game, participants: parts, racers: keys.slice(), tug: g, battle: JSON.parse(JSON.stringify(g)),
              hostCode: me, startedBy: startedBy === 'me' ? me : startedBy };
  window.__d = d; vroomCode = 'HIV' + __seq; __rooms[vroomCode] = JSON.parse(JSON.stringify(d)); vroomMyKey = me; vroomIsHost = true;
  try{ detachTug(); }catch(e){}
  (game === 'tug' ? showTugResult : showBattleResult)(d);
  await new Promise(r => setTimeout(r, 400));
  return store.vrHosted; }"""
AGAIN = """async () => { tugPaidFor = 0; battlePaidFor = 0; try{ detachTug(); }catch(e){} (__d.game === 'tug' ? showTugResult : showBattleResult)(__d);
  await new Promise(r => setTimeout(r, 300)); try{ detachTug(); }catch(e){} showTugResult(__d); await new Promise(r => setTimeout(r, 300)); return store.vrHosted; }"""
# A race: everybody else finished; this account's run goes through the real finish and the finale's listener. `leave` leaves the
# room before the others are in (an abandoned match), and the others then finish.
RACE = """async ([startedBy, leave]) => {
  const me = __me, now = Date.now() - 300000 + (++__seq) * 1000;
  vroomCode = 'HVR' + __seq; vroomMyKey = me; vroomIsHost = true;
  const P = (n, fin) => ({ name: n, avatarChar: 'ghost', level: 9, badges: 1, joinedAt: 2, ready: true, finished: fin, progress: fin ? 100 : 40, elapsedMs: 200000, xp: 300, xpLines: [], revealDone: true, seen: 9e15 });
  const parts = { p2: P('Devonte', !leave), p3: P('Alex', !leave) };
  parts[me] = { name: 'Madison', avatarChar: 'ninja', level: 20, badges: 3, joinedAt: 1, ready: true, finished: false, progress: 90, seen: 9e15 };
  __rooms[vroomCode] = { status: 'started', startAt: now, units: ['x'], game: 'race', racers: [me, 'p2', 'p3'], participants: parts, hostCode: me, startedBy: startedBy === 'me' ? me : startedBy };
  lastRunRoomXp = { lines: [], total: 250 };
  finishVirtualRoomTest(90, 190000);
  for(let i = 0; i < 30 && !document.querySelector('.vroom-waitcard'); i++) await new Promise(r => setTimeout(r, 100));
  if(leave){
    await new Promise(r => setTimeout(r, 400));
    try{ leaveVirtualRoom(); }catch(e){}
    const code = 'HVR' + __seq; if(__rooms[code]){ ['p2','p3'].forEach(k => { __rooms[code].participants[k].finished = true; __rooms[code].participants[k].progress = 100; }); }
    await new Promise(r => setTimeout(r, 1500));
  } else {
    for(let i = 0; i < 40 && !document.querySelector('.vroom-waitcard.is-all-in'); i++) await new Promise(r => setTimeout(r, 100));
    await new Promise(r => setTimeout(r, 300));
  }
  return store.vrHosted; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for cls in ("academy", "ifc"):
        init = (IINIT + cb._ROOM_FAKE) if cls == "ifc" else cb._ROOM_FAKE
        ctx, pg = cb.booted(br, 440, 956, seed=IACCT if cls == "ifc" else cb.USED_ACCOUNT, dpr=1, init=init)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        def ev(js, arg=None):
            try: return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
            except Exception as e: errs.append("harness: " + str(e)[:200]); return None
        ev(SETUP)
        s0 = ev(STATE) or {}
        tag = "%s (%s)" % (cls, s0.get("name"))
        import re as _re
        m = _re.match(r"^Host (\d+) Virtual Room matches$", s0.get("label") or "")
        chk("(1) %s: %r, its number its own need (%s), the note says play it to the end (%r)" % (tag, s0.get("label"), s0.get("need"), s0.get("note")),
            m and int(m.group(1)) == s0.get("need") == 3 and "end" in (s0.get("note") or "") and "Host" in (s0.get("note") or ""), s0)
        h1 = ev(TEAM, ["tug", "me", ["c1", "c2", "c3"]])
        h2 = ev(TEAM, ["battle", "me", ["c1"]])
        s2 = ev(STATE) or {}
        joined = ev(TEAM, ["tug", "c1", ["c1", "c2", "c3"]])
        nova = ev(TEAM, ["battle", "me", ["nova"]])
        left = ev(RACE, ["me", True])
        again = ev(AGAIN)
        s2b = ev(STATE) or {}
        h3 = ev(RACE, ["me", False])
        s3 = ev(STATE) or {}
        chk("(2) %s: locked at 0 (%s); a hosted Tug of War and Battle count %s, %s and it is still locked at 2 (%s, %s/%s); a hosted Race opens it (%s, %s)" % (
            tag, s0.get("locked"), h1, h2, s2.get("locked"), s2.get("have"), s2.get("need"), h3, not s3.get("locked")),
            s0.get("locked") is True and s0.get("hosted") == 0 and h1 == 1 and h2 == 2 and s2.get("locked") is True and s2.get("have") == 2 and h3 == 3 and s3.get("locked") is False and s3.get("have") == 3,
            {"s0": s0, "h": [h1, h2, h3], "s2": s2, "s3": s3})
        chk("(3) %s: a joined match (%s), one hosted with only Nova (%s) and one hosted then left before the end (%s) add nothing" % (tag, joined, nova, left),
            joined == 2 and nova == 2 and left == 2, [joined, nova, left])
        chk("(4) %s: the same result drawn again and after a relaunch adds nothing (%s, have %s)" % (tag, again, s2b.get("have")), again == 2 and s2b.get("have") == 2, [again, s2b])
        dflt = ev("""()=>{ const keep = store.vrHosted; const d = JSON.parse(JSON.stringify(store)); delete d.vrHosted; applyLoadedData(d); const missing = store.vrHosted;
          const d2 = JSON.parse(JSON.stringify(store)); d2.vrHosted = 2; applyLoadedData(d2); const kept = store.vrHosted; store.vrHosted = keep; return [missing, kept]; }""")
        chk("(5) %s: a copy without the field loads as 0, one with it keeps it (%s), and no page errors" % (tag, dflt), dflt == [0, 2] and not errs, [dflt, errs[:3]])
        # (6) a progress counter: the same account's two copies merge to the larger (never lowered); a folded-in account adds
        mg = ev("""()=>{ const a = { vrHosted: 1 }, b = { vrHosted: 3 }; mergeSameAccount(a, b); const up = a.vrHosted;
          const c = { vrHosted: 3 }; mergeSameAccount(c, { vrHosted: 1 }); const down = c.vrHosted;
          const keep = JSON.parse(JSON.stringify(store)); store.vrHosted = 2; let sum = null;
          try{ mergeLeavingAccount(JSON.parse(JSON.stringify(Object.assign({}, keep, { vrHosted: 1 })))); sum = store.vrHosted; }catch(e){ sum = 'ERR ' + e; }
          applyLoadedData(keep); return [up, down, sum]; }""")
        chk("(6) %s: two copies of one account merge to the larger, either way round (%s), and a folded-in account adds (2 + 1 = %s)" % (tag, (mg or [None])[:2], (mg or [None] * 3)[2]),
            mg and mg[0] == 3 and mg[1] == 3 and mg[2] == 3, mg)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
