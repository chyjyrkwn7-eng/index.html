"""Build 384.20: a room code left set by a Virtual Room does not follow the device into the next test.

`vroomCode` is the one variable that says "this device is in a room", and the only thing that cleared it was leaveVirtualRoom().
A lobby (or a finished match) walked away from by any other door - the header's Home, a banner's View, a tab - left it set, with
the room's presence beat, its listener and the room's class bank still running. And a Drill or an Exam asked it twice before it
would own the one save slot (`runSaveSlot`, `runSessionSavable()`): `!vroomCode`. So the next ordinary test could not be saved
(Pause had no Save and exit, a closed app left no test to come back to), was titled "Virtual Room", and held a forced update off.

SEVERAL DEVICES, ONE CLOUD (the check-b384-vrkick arrangement, its harness exec'd): each device its own browser context, one
Firestore stand-in over HTTP. Accounts and codes are made up. Every number is read off the page.
 (L) A LOBBY WALKED AWAY FROM, three doors that are not Leave lobby (Home, Friends, Profile): the room code, the presence beat and
     the lobby listener are gone, this device is off the room's roster, and an ordinary Drill that follows can be saved
     (runSessionSavable, Save and exit writes the slot) and is not titled "Virtual Room"; the Leave lobby button does the same
     (control);
 (F) A FINISHED MATCH walked away from by Home (not Main menu): the same;
 (R) THE ROOM'S OWN SCREENS ARE NOT A WAY OUT: Match settings and back, the results and Back to lobby - each held for well over the
     watch's delay - keep the code, the beat and the roster entry (the guard against the watch being too eager);
 (K) KICKED (paused past the minute): the same (control - it already went through leaveVirtualRoom);
 (S) STALE STATE, WHATEVER PUT IT THERE: a room code planted on a device that is in no room does not stop an ordinary Drill being
     saved, and the Drill drops it; planted DURING the Drill it still does not stop the save (the save path never reads it);
 (N) no page errors.
Run:  python3 tools/check-b384-roomleft.py     (--against OLD/index.html must FAIL)    ONLY=L,S to run some sections"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-vroom-review.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
exec(compile(_src, os.path.join(HERE, "check-b384-vroom-review.py"), "exec"), globals())

OLD = OLD_BUILD is not None
def entry(code, pub): return (room(code).get("participants") or {}).get(pub)

# what this device still holds of a room
HELD = """()=>({ code: (typeof vroomCode !== 'undefined') ? vroomCode : 'n/a', key: vroomMyKey || null,
  beat: vroomBeatTimer != null, lobbyListener: typeof vroomUnsubscribe !== 'undefined' && vroomUnsubscribe != null,
  inRoom: !!inVirtualRoom, bank: BANK_CLASS })"""

# an ordinary Drill, started as Start Studying starts one (beginRun), then asked what a Drill is asked
SOLO = """async()=>{ const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
  const until = async (f, ms) => { const t0 = Date.now(); while(Date.now() - t0 < (ms || 9000)){ try{ if(f()) return true; }catch(e){} await wait(60); } return false; };
  try{
    const unit = topicsIn(QUESTIONS).map(u => [u, unitQuestionCount(u)]).filter(x => x[1] >= 6).sort((a, b) => a[1] - b[1])[0][0];
    const idx = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && inWholeUnit(QUESTIONS[i]));
    theme.autoAdvance = false; clearRunSession();
    if(__PLANT__){ vroomCode = 'STALE-0001'; vroomMyKey = 'stale-key'; }
    cfg.mode = 'drill'; cfg.units = [unit]; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'up'; cfg.flashcards = false;
    beginRun(freshOrder(idx), null, null);
    out.up = await until(() => document.querySelector('.qpanel .choice') && runStartTime != null);
    if(__PLANT_DURING__){ vroomCode = 'STALE-0002'; vroomMyKey = 'stale-key'; }
    out.savable = runSessionSavable();
    out.title = runModeTitle();
    out.codeAfterStart = vroomCode;
    pauseRun(); await wait(400);
    out.pauseHasSave = !!document.querySelector('.pausepanel.has-save');
    out.saved = saveRunSession(true);
    out.slot = !!localStorage.getItem(RUN_SESSION_KEY);
  }catch(e){ out.threw = String(e && e.stack || e).slice(0, 300); }
  try{ clearRunSession(); paused = false; testInProgress = false; try{ cancelPauseTiming(); }catch(e){} showHome(); }catch(e){}
  return out; }"""
def solo(pg, plant=False, during=False):
    return pg.evaluate(SOLO.replace("__PLANT_DURING__", "true" if during else "false").replace("__PLANT__", "true" if plant else "false"))
def tidy(pg):
    pg.evaluate("""()=>{ try{ document.getElementById('vroom-race-cut')?.remove(); document.getElementById('vroom-cutscene')?.remove(); document.getElementById('vroom-prep')?.remove();
      document.querySelectorAll('.vroom-leave-confirm, #roomchat-sheet, .toast').forEach(n => n.remove());
      if(typeof cancelPauseTiming === 'function') cancelPauseTiming(); paused = false; if(vroomCode) leaveVirtualRoom(); testInProgress = false; showHome(); }catch(e){} }""")
    pg.wait_for_timeout(700)

DOORS = {
    "the header's Home": "()=>showHome()",
    "a banner's View (Friends)": "()=>showFriends()",
    "the Profile tab": "()=>showProfile()",
    "Leave lobby (control)": "()=>{ document.querySelector('#stage .screen-vroom-lobby .back-link, #stage .screen-vroom-lobby [class*=back]').click(); }",
}

def after_leaving(tag, pg, code, pub):
    """what a device that has walked out of a room must look like, then an ordinary Drill."""
    gone = wait_for(pg, "()=>(typeof vroomCode !== 'undefined' && !vroomCode) ? true : null", tries=12, step=250)
    h = pg.evaluate(HELD)
    chk("(%s) the room code is cleared (%r)" % (tag, h["code"]), bool(gone) and not h["code"], h)
    chk("(%s) and nothing of the room is still running: no presence beat, no lobby listener (%s)" % (tag, {k: h[k] for k in ("beat", "lobbyListener", "inRoom")}),
        not h["beat"] and not h["lobbyListener"] and not h["inRoom"], h)
    chk("(%s) and the room no longer lists this device (%s)" % (tag, entry(code, pub)), entry(code, pub) is None, entry(code, pub))
    s = solo(pg)
    chk("(%s) the Drill that follows can be saved: savable, Pause offers Save and exit, the slot is written (%s)" % (tag, {k: s.get(k) for k in ("savable", "pauseHasSave", "saved", "slot")}),
        bool(s.get("up")) and s.get("savable") is True and s.get("pauseHasSave") is True and s.get("saved") is True and s.get("slot") is True and not s.get("threw"), s)
    chk("(%s) and it is titled as a Drill, not a Virtual Room (%r)" % (tag, s.get("title")), bool(s.get("title")) and "virtual" not in (s.get("title") or "").lower(), s)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    actx, A = device(br, "alex", ALEX)
    kctx, K = device(br, "kim", KIM)
    unit_a = A.evaluate(SMALL_UNIT)

    # ===================== (L) a lobby, left by a door that is not Leave lobby =====================
    if want("L"):
        print("\n-- (L) a lobby walked away from: nothing of the room is kept, and the next Drill saves", flush=True)
        for name, js in DOORS.items():
            try:
                code = host_room(A, unit_a, "race", 5)
                chk("(L) %s: a lobby, this device in it (%s)" % (name, code), bool(code) and entry(code, ALEX) is not None, code)
                A.evaluate(js)
                A.wait_for_timeout(900)
                after_leaving("L, " + name, A, code, ALEX)
            except Exception as e:
                chk("(L) %s: ran without an exception" % name, False, repr(e)[:300])
            tidy(A)

    # ===================== (R) the room's own screens =====================
    if want("R"):
        print("\n-- (R) Match settings and back: still in the room", flush=True)
        try:
            code = host_room(A, unit_a, "race", 5)
            A.click("#stage .screen-vroom-lobby .vroom-settings-btn")
            up = wait_for(A, "()=>document.querySelector('#stage .screen-vroom-setup') ? true : null", tries=15, step=300)
            A.wait_for_timeout(1200)
            h = A.evaluate(HELD)
            chk("(R) Match settings, held 1.2s, keeps the room (screen up %s; code %r, beat %s, on the roster %s)" % (bool(up), h["code"], h["beat"], entry(code, ALEX) is not None),
                bool(up) and h["code"] == code and h["beat"] and entry(code, ALEX) is not None, h)
            A.evaluate("()=>showVirtualRoomLobby()")
            A.wait_for_timeout(1200)
            h = A.evaluate(HELD)
            chk("(R) and back on the lobby it is still this device's room (code %r)" % h["code"], h["code"] == code and entry(code, ALEX) is not None, h)
        except Exception as e:
            chk("(R) ran without an exception", False, repr(e)[:300])
        tidy(A)

    # ===================== (F) a finished match, left by Home =====================
    if want("F"):
        print("\n-- (F) a finished race walked away from by Home (not Main menu)", flush=True)
        try:
            code = host_room(A, unit_a, "race", 5)
            join(K, code)
            ready([A, K])
            for pg in (A, K): wait_for(pg, RACE_UP, tries=100, step=300)
            A.evaluate(ANSWER_ALL, 1); K.evaluate(ANSWER_ALL, 1)
            A.evaluate(ANSWER_ALL); K.evaluate(ANSWER_ALL)
            res = wait_for(A, "()=>(!inVirtualRoom && vroomCode && document.querySelector('#stage .rs-screen')) ? true : null", tries=60, step=400)
            chk("(F) the match is over and this device is on its results (%s)" % bool(res), bool(res), A.evaluate("()=>({s: stage.firstElementChild && stage.firstElementChild.className, inRoom: inVirtualRoom, code: vroomCode})"))
            A.wait_for_timeout(1500)
            h = A.evaluate(HELD)
            chk("(R) the results screen, held 1.5s, keeps the room (code %r, beat %s, on the roster %s)" % (h["code"], h["beat"], entry(code, ALEX) is not None),
                h["code"] == code and h["beat"] and entry(code, ALEX) is not None, h)
            A.evaluate("()=>{ document.getElementById('vroom-prep')?.remove(); vroomReturnToLobby(); }")
            back = wait_for(A, "()=>document.querySelector('#stage .screen-vroom-lobby') ? true : null", tries=20, step=300)
            A.wait_for_timeout(1200)
            h = A.evaluate(HELD)
            chk("(R) Back to lobby: the lobby is up and, held 1.2s, still this device's room (code %r, beat %s)" % (h["code"], h["beat"]),
                bool(back) and h["code"] == code and h["beat"] and entry(code, ALEX) is not None, h)
            A.evaluate("()=>showHome()")
            A.wait_for_timeout(900)
            after_leaving("F", A, code, ALEX)
        except Exception as e:
            chk("(F) ran without an exception", False, repr(e)[:300])
        tidy(A); tidy(K)

    # ===================== (K) kicked =====================
    if want("K"):
        print("\n-- (K) removed for inactivity (control: it already goes through leaveVirtualRoom)", flush=True)
        try:
            code = host_room(A, unit_a, "race", 5)
            join(K, code)
            ready([A, K])
            for pg in (A, K): wait_for(pg, RACE_UP, tries=100, step=300)
            K.evaluate("()=>document.getElementById('pausebtn').click()")
            wait_for(K, "()=>!!document.querySelector('#stage .pausepanel.is-pause')", tries=20, step=200)
            K.evaluate("()=>{ vroomPausedAt -= 61000; clearTimeout(vroomPauseKickTimer); vroomKickSelfIfIdle(); }")
            wait_for(K, "()=>(typeof vroomCode !== 'undefined' && !vroomCode) ? true : null", tries=20, step=250)
            after_leaving("K", K, code, KIM)
        except Exception as e:
            chk("(K) ran without an exception", False, repr(e)[:300])
        tidy(A); tidy(K)

    # ===================== (S) stale state, whatever put it there =====================
    if want("S"):
        print("\n-- (S) a stale room code does not touch an ordinary test's save", flush=True)
        try:
            s = solo(A, plant=True)
            chk("(S) a code planted just before the Drill starts: the Drill still saves (%s)" % {k: s.get(k) for k in ("savable", "pauseHasSave", "saved", "slot")},
                bool(s.get("up")) and s.get("savable") is True and s.get("pauseHasSave") is True and s.get("saved") is True and s.get("slot") is True and not s.get("threw"), s)
            chk("(S) and the Drill dropped the stale code (%r)" % s.get("codeAfterStart"), not s.get("codeAfterStart"), s)
            chk("(S) and is titled as a Drill (%r)" % s.get("title"), bool(s.get("title")) and "virtual" not in (s.get("title") or "").lower(), s)
            A.wait_for_timeout(600)
            s = solo(A, during=True)
            chk("(S) a code appearing DURING the Drill does not stop its save: the save path never reads it (%s)" % {k: s.get(k) for k in ("savable", "pauseHasSave", "saved", "slot")},
                bool(s.get("up")) and s.get("savable") is True and s.get("pauseHasSave") is True and s.get("saved") is True and s.get("slot") is True and not s.get("threw"), s)
        except Exception as e:
            chk("(S) ran without an exception", False, repr(e)[:300])
        tidy(A)

    # ===================== (N) =====================
    print("\n-- (N) no page errors", flush=True)
    chk("(N) no page errors on either device (%s)" % {k: v[:2] for k, v in ERRS.items() if v}, not any(ERRS[d] for d in ERRS), ERRS)
    leak = [c for c, d in CLOUD.data.get("vrooms", {}).items() if any(code in json.dumps(d) for code in CODE.values())]
    chk("(N) no sync code in any `vrooms` document (%s)" % leak, not leak, leak)
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
