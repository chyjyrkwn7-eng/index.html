"""Build 384, the Virtual Room round 3. Madison: "Say you are paused for 1 minute, then you get kicked for inactivity. That's what
the chat would say. Same would apply for the phone die, they just wouldn't know for a minute or two or whatever works best.
That's mid test."

SEVERAL DEVICES, ONE CLOUD: check-b384-vroom-review's harness (each device its own browser context and storage, one Firestore
stand-in served over HTTP). Accounts, names and codes are made up. Every section is a two-player race.
 (S) PAUSED FOR A MINUTE, THIS DEVICE: pausing arms the kick; a minute on (the pause's own stamp moved back, rather than a
     minute's wait) the paused player is out of the room, lands on Home and is told why; the room's chat carries a line that they
     were removed for inactivity, the other player's race line drops them and their toast says so;
 (W) PAUSED, PHONE ASLEEP: a racer whose pause is past the minute and whose own device says nothing (its timers stopped, as an
     iPhone stops them) is removed by the other player's device, with the same chat line; when the sleeping phone wakes, its
     race ends there too and it is told why - it does not put itself back in the room;
 (G) THE PHONE DIED: a racer with no presence beat for well over a minute and a half is removed by the other player's device,
     with the same chat line, and the race finishes without them;
 (K) NOT TOO SOON, NOT THE FINISHED: a racer paused for under a minute, or quiet for under a minute, is not removed; a racer who
     has finished is never removed, however quiet;
 (N) no sync code in any `vrooms` document; no page errors.
Run:  python3 tools/check-b384-vrkick.py     (--against OLD/index.html must FAIL)    ONLY=S,G to run some sections"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-vroom-review.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
exec(compile(_src, os.path.join(HERE, "check-b384-vroom-review.py"), "exec"), globals())

def leave2(pg):
    pg.evaluate("""()=>{ try{ document.getElementById('vroom-race-cut')?.remove(); document.getElementById('vroom-cutscene')?.remove(); document.getElementById('vroom-prep')?.remove();
      document.querySelectorAll('.vroom-leave-confirm, #roomchat-sheet, .toast').forEach(n => n.remove());
      if(typeof cancelPauseTiming === 'function') cancelPauseTiming(); paused = false;
      if(vroomCode) leaveVirtualRoom(); testInProgress = false; showHome(); }catch(e){} }""")
    pg.wait_for_timeout(700)
def race(host, others, n=5):
    code = host_room(host, unit_a, "race", n)
    for pg in others: join(pg, code)
    ready([host] + others)
    for pg in [host] + others: wait_for(pg, RACE_UP, tries=100, step=300)
    return code
def entry(code, pub): return (room(code).get("participants") or {}).get(pub)
def kick_lines(code, pub): return [m for m in (room(code).get("chatMessages") or []) if m.get("key") == pub and m.get("type") == "left"]
MARKS = "()=>[...document.querySelectorAll('.vroom-race-marker')].map(x => (x.title || '').split(' ')[0])"
TOAST_HAS = "(s)=>{ const t = [...document.querySelectorAll('.toast')].map(x => x.innerText).join(' / '); return t.toLowerCase().indexOf(s) >= 0 ? t : null; }"
HOME = "()=>!!document.querySelector('#stage [data-screen=\"home\"], #stage .screen-home-actual') && !inVirtualRoom && !vroomCode"
# a phone going quiet: its beat, its room listener and its own kick timer stop, as an iPhone stops a backgrounded page's
ASLEEP = """()=>{ try{ clearInterval(vroomBeatTimer); vroomBeatTimer = null; }catch(e){}
  try{ stopVroomRaceListener(); }catch(e){}
  try{ if(typeof vroomPauseKickTimer !== 'undefined'){ clearTimeout(vroomPauseKickTimer); vroomPauseKickTimer = null; } }catch(e){} }"""
# a field on this device's own room entry, written as the app writes it
SETF = "([f, v])=>vroomDb().collection('vrooms').doc(vroomCode).update({ ['participants.' + vroomMyKey + '.' + f]: Date.now() - v })"
OLD = OLD_BUILD is not None

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    actx, A = device(br, "alex", ALEX)
    kctx, K = device(br, "kim", KIM)
    unit_a = A.evaluate(SMALL_UNIT)

    # ===================== (S) paused a minute, this device =====================
    if want("S"):
        print("\n-- (S) paused for a minute: out of the match, told why, and the room's chat says so", flush=True)
        try:
            code = race(A, [K])
            K.evaluate(ANSWER_ALL, 1)
            before = wait_for(A, "()=>{ const m = (%s)(); return m.length >= 2 ? m : null; }" % MARKS, tries=20, step=250) or []
            K.evaluate("()=>document.getElementById('pausebtn').click()")
            wait_for(K, "()=>!!document.querySelector('#stage .pausepanel.is-pause')", tries=20, step=200)
            armed = K.evaluate("()=>typeof vroomPauseKickTimer !== 'undefined' && vroomPauseKickTimer != null")
            chk("(S) pausing a race arms the inactivity kick (%s)" % armed, armed)
            K.wait_for_timeout(1500)
            still = K.evaluate("()=>!!vroomCode && !!document.querySelector('#stage .pausepanel.is-pause')")
            chk("(S) and under the minute nothing happens (still paused, still in the room: %s)" % still, still and entry(code, KIM) is not None)
            # a minute on: the pause's stamp moved back, and the kick's own check run as its timer would
            K.evaluate("()=>{ if(typeof vroomPausedAt !== 'undefined'){ vroomPausedAt -= 61000; clearTimeout(vroomPauseKickTimer); vroomKickSelfIfIdle(); } }")
            home = wait_for(K, HOME, tries=20, step=250)
            told = wait_for(K, TOAST_HAS, "inactivity", tries=12, step=250)
            chk("(S) a minute paused: the paused player is on Home, out of the room, and told why (%s; %r)" % (bool(home), told),
                bool(home) and bool(told) and entry(code, KIM) is None, {"entry": entry(code, KIM), "screen": K.evaluate("()=>stage.firstElementChild && stage.firstElementChild.className")})
            ln = kick_lines(code, KIM)
            chk("(S) the room's chat says they were removed for inactivity (%s)" % ln[-1:], bool(ln) and "inactivity" in (ln[-1].get("text") or "") and ln[-1].get("name") == NAMES[KIM], room(code).get("chatMessages"))
            gone = wait_for(A, "(n)=>{ const m = (%s)(); return (m.length && m.indexOf(n) < 0) ? m : null; }" % MARKS, NAMES[KIM], tries=20, step=250)
            ta = wait_for(A, TOAST_HAS, "inactivity", tries=12, step=250)
            chk("(S) the other player's race line drops them and their toast says why (%s -> %s; %r)" % (before, gone, ta), bool(gone) and NAMES[KIM] in before and bool(ta) and NAMES[KIM] in ta)
            leave2(A); leave2(K)
        except Exception as ex:
            chk("(S) ran to the end", False, repr(ex)[:300]); leave2(A); leave2(K)

    # ===================== (W) paused, phone asleep =====================
    if want("W"):
        print("\n-- (W) paused with the phone asleep: the other device removes them; waking, they are out and told why", flush=True)
        try:
            code = race(A, [K])
            K.evaluate(ANSWER_ALL, 1)
            K.evaluate("()=>document.getElementById('pausebtn').click()")
            wait_for(K, "()=>!!document.querySelector('#stage .pausepanel.is-pause')", tries=20, step=200)
            K.evaluate(ASLEEP)
            K.evaluate(SETF, ["paused", 80000])
            out = None
            for _ in range(80):
                if entry(code, KIM) is None: out = True; break
                A.wait_for_timeout(250)
            ln = kick_lines(code, KIM)
            chk("(W) paused past the minute with the phone silent: the other player's device removes them (%s), the chat says why (%s)" % (bool(out), ln[-1:]),
                bool(out) and bool(ln) and "inactivity" in (ln[-1].get("text") or ""), {"entry": entry(code, KIM), "chat": room(code).get("chatMessages")})
            nw = len(CLOUD.writes)
            K.evaluate("()=>startVroomRaceListener()")
            home = wait_for(K, HOME, tries=20, step=250)
            told = wait_for(K, TOAST_HAS, "inactivity", tries=12, step=250)
            K.wait_for_timeout(1200)
            kw = [w for w in CLOUD.writes[nw:] if w["dev"] == "kim" and w["path"] == "vrooms/" + code]
            chk("(W) the phone wakes: its race ends, it is on Home and told why (%s; %r), and it writes nothing back into the room (%d writes)" % (bool(home), told, len(kw)),
                bool(home) and bool(told) and not kw and entry(code, KIM) is None, {"writes": kw, "entry": entry(code, KIM)})
            leave2(A); leave2(K)
        except Exception as ex:
            chk("(W) ran to the end", False, repr(ex)[:300]); leave2(A); leave2(K)

    # ===================== (G) the phone died =====================
    if want("G"):
        print("\n-- (G) the phone died: no beat for over a minute and a half, removed by the other device", flush=True)
        try:
            code = race(A, [K])
            K.evaluate(ANSWER_ALL, 1)
            K.evaluate(ASLEEP)
            K.evaluate(SETF, ["seen", 105000])
            out = None
            for _ in range(80):
                if entry(code, KIM) is None: out = True; break
                A.wait_for_timeout(250)
            ln = kick_lines(code, KIM)
            chk("(G) a silent phone is removed by the other player's device (%s), with the chat's line (%s)" % (bool(out), ln[-1:]),
                bool(out) and bool(ln) and "inactivity" in (ln[-1].get("text") or "") and ln[-1].get("name") == NAMES[KIM], {"entry": entry(code, KIM), "chat": room(code).get("chatMessages")})
            A.evaluate(ANSWER_ALL, None)
            allin = wait_for(A, ALL_IN if "ALL_IN" in globals() else "()=>!!document.querySelector('.vroom-waitcard.is-all-in')", tries=30, step=400)
            chk("(G) and the race finishes without them", bool(allin))
            leave2(A); leave2(K)
        except Exception as ex:
            chk("(G) ran to the end", False, repr(ex)[:300]); leave2(A); leave2(K)

    # ===================== (K) not too soon, never the finished =====================
    if want("K"):
        print("\n-- (K) not before the minute; never somebody who has finished", flush=True)
        try:
            code = race(A, [K])
            K.evaluate(ANSWER_ALL, 1)
            K.evaluate("()=>document.getElementById('pausebtn').click()")
            wait_for(K, "()=>!!document.querySelector('#stage .pausepanel.is-pause')", tries=20, step=200)
            K.evaluate(ASLEEP)
            K.evaluate(SETF, ["paused", 40000])
            K.evaluate(SETF, ["seen", 50000])
            A.evaluate(ANSWER_ALL, None)            # A finishes: their results' listener looks too
            A.wait_for_timeout(17000)
            chk("(K) paused 40s and quiet 50s: not removed (still in: %s)" % (entry(code, KIM) is not None), entry(code, KIM) is not None and not kick_lines(code, KIM), entry(code, KIM))
            # K comes back and finishes; then A, finished, goes quiet for minutes - K's device must leave A be
            K.evaluate("()=>{ startVroomRaceListener(); startVroomPresence(); }")
            K.evaluate("()=>document.getElementById('resumebtn')?.click()")
            wait_for(K, RACE_UP, tries=20, step=250)
            K.evaluate(ANSWER_ALL, None)
            wait_for(K, "()=>!!document.querySelector('.vroom-waitcard')", tries=30, step=400)
            A.evaluate(ASLEEP)
            A.evaluate(SETF, ["seen", 300000])
            K.wait_for_timeout(17000)
            ea = entry(code, ALEX)
            chk("(K) a finished racer, quiet five minutes, is never removed (still in: %s)" % (ea is not None), ea is not None and not kick_lines(code, ALEX), ea)
            leave2(A); leave2(K)
        except Exception as ex:
            chk("(K) ran to the end", False, repr(ex)[:300]); leave2(A); leave2(K)

    # ===================== (N) =====================
    print("\n-- (N) no sync code in any vrooms document; no page errors", flush=True)
    A.wait_for_timeout(800)
    leak = [k for k, v in CLOUD.data["vrooms"].items() if any(c in json.dumps(v) or c in k for c in CODE.values())]
    chk("(N) no sync code in any `vrooms` document (%d documents; %s)" % (len(CLOUD.data["vrooms"]), leak), not leak, leak)
    for dev, es in ERRS.items():
        chk("(N) no page errors on %s" % dev, not es, es[:3])
    for c in (actx, kctx):
        try: c.close()
        except Exception: pass
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
