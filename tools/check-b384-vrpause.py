"""Build 384, the Virtual Room round 2. Madison: "Pausing should only pause you.. and yeah if you pause it would let you leave." /
"If someone leaves it would update real time so people know they left. For example the race, if someone leaves, it would remove
them from the top thing on the race. In the chat, it would say x player left or whatever." / "If I'm friends with someone they
should be there and stuff."

SEVERAL DEVICES, ONE CLOUD: check-b384-vroom-review's harness (each device its own browser context and storage, one Firestore
stand-in served over HTTP), with two more made-up academy accounts so Tug of War and Battle can be two against two. Accounts,
names and codes are made up.
 (P) PAUSE ONLY PAUSES YOU (a race, two players): the pause is on the paused player's room entry, their marker on the other's race
     line is dimmed, and the pause screen says who is still racing and has a way out of the match; the one who finished is not
     held - their results reach "all in" and the leaderboard rolls while the other is still paused, whose own race is still held;
 (R) RESUME PUTS YOU BACK IN THE WAIT: resumed before the leaderboard rolls, the finished player's card goes back to waiting;
 (Q) FINISHING AFTER THE OTHERS WENT BACK: the others' return to the lobby says which match it was from, and the late finisher's
     results say the race is over and offer Return to lobby, rather than waiting on people who are no longer racing;
 (L) LEAVING A RACE, LIVE: Pause > Leave match takes the player out of the room; their marker leaves the other's race line, the
     room's chat carries a line saying they left the match (in the leave's own write - no write of its own), it is not counted
     unread or raised as a chat preview, the results do not wait for them, and the Room chat sheet shows the line;
 (T) LEAVING A TUG OF WAR, LIVE (2 v 2): the leaver's figure and name leave the rope on the others' screens without them
     answering anything;
 (B) LEAVING A BATTLE, LIVE (2 v 2): the leaver's face and name leave their side, the same way;
 (F) EVERY FRIEND BY NAME: an academy-only account whose friend is in Fire Code alone (no board row) sees that friend's first
     name and character - on the chat's Friends tab (filled in live when the friend's beat lands), in the friend chat's header,
     in Manage friends (every friend listed, none dropped) and on the chat invite sheet; a friend nothing is known about yet is
     listed as "Friend" with the default character; drawing them writes nothing;
 (N) no sync code in any `vrooms` document; no page errors.
Run:  python3 tools/check-b384-vrpause.py     (--against OLD/index.html must FAIL)    ONLY=P,L to run some sections"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
# the harness: everything in check-b384-vroom-review before its run (the cloud, the client, the accounts, device(), host_room()...)
_src = open(os.path.join(HERE, "check-b384-vroom-review.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
exec(compile(_src, os.path.join(HERE, "check-b384-vroom-review.py"), "exec"), globals())

# ------------------------------------------------------------------ two more academy accounts (made up), and Devon's own face
ROW, SAS = "tst384vrrw05", "tst384vrsa06"
for pub, code, name, fc, av in ((ROW, "TEST-3865", "Rowan", "RWW-384", "queen"), (SAS, "TEST-3866", "Sasha", "SSW-384", "samurai")):
    CODE[pub] = code; NAMES[pub] = name; FCODE[pub] = fc; AVATAR[pub] = av; CLASSES[pub] = ["academy"]; FRIENDS[pub] = []
    CLOUD.data["progress"][code] = academy_store(pub)
    CLOUD.data["leaderboard"][pub] = row(pub)
AVATAR[DEV] = "wizard"   # not the default character, so "drawn from his beat" can be told from "drawn from nothing"
CLOUD.data["progress"][CODE[DEV]]["avatarChar"] = "wizard"
UNKNOWN = "tst384vrunk9"   # a friend nothing is known about: no board row, no beat, no chat
OLD = OLD_BUILD is not None

def leave2(pg):
    pg.evaluate("""()=>{ try{ document.getElementById('vroom-race-cut')?.remove(); document.getElementById('vroom-cutscene')?.remove(); document.getElementById('vroom-prep')?.remove();
      document.querySelectorAll('.vroom-leave-confirm, #roomchat-sheet').forEach(n => n.remove());
      if(typeof cancelPauseTiming === 'function') cancelPauseTiming(); paused = false;
      if(vroomCode) leaveVirtualRoom(); testInProgress = false; showHome(); }catch(e){} }""")
    pg.wait_for_timeout(700)
def race(host, others, n=5):
    code = host_room(host, unit_a, "race", n)
    for pg in others: join(pg, code)
    ready([host] + others)
    for pg in [host] + others: wait_for(pg, RACE_UP, tries=100, step=300)
    return code
def entry(code, pub): return (room(code).get("participants") or {}).get(pub) or {}
MARK = """(n)=>{ const m = [...document.querySelectorAll('.vroom-race-marker')].find(x => (x.title || '').indexOf(n) === 0); return m ? { paused: m.classList.contains('is-paused') } : null; }"""
MARKS = "()=>[...document.querySelectorAll('.vroom-race-marker')].map(x => (x.title || '').split(' ')[0])"
ALL_IN = "()=>!!document.querySelector('.vroom-waitcard.is-all-in')"
CUT = "()=>!!document.getElementById('vroom-race-cut')"
PAUSED = "()=>!!document.querySelector('#stage .pausepanel.is-pause') && paused === true && testInProgress === true"

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    actx, A = device(br, "alex", ALEX)      # academy only
    kctx, K = device(br, "kim", KIM)        # in both, on the academy's page
    unit_a = A.evaluate(SMALL_UNIT)

    # ===================== (P) + (R) + (Q): a race, one player paused =====================
    if want("P") or want("R") or want("Q"):
        print("\n-- (P) pausing a race only pauses you; (R) resuming puts you back in the wait; (Q) finishing after the others went back", flush=True)
        try:
            code = race(A, [K])
            K.evaluate(ANSWER_ALL, 1)
            K.evaluate("()=>document.getElementById('pausebtn').click()")
            pz = wait_for(K, "()=>{ const p = document.querySelector('#stage .pausepanel.is-pause'); return p ? { quit: !!p.querySelector('#pause-quit'), room: !!p.querySelector('.pause-room') } : null; }", tries=20, step=200) or {}
            e = None
            for _ in range(20):
                e = entry(code, KIM)
                if e.get("paused"): break
                K.wait_for_timeout(250)
            chk("(P) the pause is said on the paused player's own room entry (paused: %s)" % e.get("paused"), isinstance(e.get("paused"), (int, float)) and e.get("paused") > 0, e)
            mk = wait_for(A, "(n)=>{ const m = (%s)(n); return m && m.paused ? m : null; }" % MARK, NAMES[KIM], tries=20, step=250)
            chk("(P) the other player's race line dims the paused player's marker (%s)" % mk, bool(mk), A.evaluate(MARK, NAMES[KIM]))
            chk("(P) the pause screen says who is still racing and has the way out of the match (%s)" % pz, bool(pz.get("room")) and bool(pz.get("quit")), pz)
            # the one still racing finishes: their results are not held by the paused player
            t0 = time.time()
            A.evaluate(ANSWER_ALL, None)
            allin = wait_for(A, ALL_IN, tries=40, step=400)
            took = time.time() - t0
            chk("(P) the finished player's results reach 'all in' while the other is paused (%.1fs; before: held for as long as the pause)" % took, bool(allin), {"kim": entry(code, KIM)})
            line = K.evaluate("()=>{ const l = document.querySelector('#stage .pausepanel .pause-room'); return l ? { still: l.dataset.still, t: l.textContent } : null; }") or {}
            chk("(P) the paused player's screen says nobody else is still racing (still=%s)" % line.get("still"), line.get("still") == "0", line)
            # (R) a resume before the leaderboard rolls puts them back in the wait
            if want("R"):
                K.evaluate("()=>document.getElementById('resumebtn')?.click()")
                back_wait = wait_for(A, "()=>{ const w = document.querySelector('.vroom-waitcard'); return (w && !w.classList.contains('is-all-in')) ? true : null; }", tries=20, step=250)
                chk("(R) resumed before the leaderboard rolled: the finished player, who was all in, is waiting on them again (all in before: %s; after: %s)" % (bool(allin), not back_wait),
                    bool(allin) and bool(back_wait) and not A.evaluate(CUT) and not entry(code, KIM).get("paused"), {"kim": entry(code, KIM), "cut": A.evaluate(CUT)})
                K.wait_for_timeout(600)
                K.evaluate("()=>document.getElementById('pausebtn').click()")
                wait_for(K, PAUSED, tries=20, step=200)
                wait_for(A, ALL_IN, tries=40, step=400)
            # the leaderboard rolls while the other is still paused
            cut = wait_for(A, CUT, tries=120, step=500)
            still = K.evaluate(PAUSED)
            chk("(P) the leaderboard rolls for the finished player while the other is still paused (rolled: %s; still paused: %s)" % (bool(cut), still),
                bool(cut) and still, {"kim": entry(code, KIM)})
            # (Q) the finished player goes back to the lobby; then the paused one resumes and finishes
            if want("Q"):
                A.evaluate("()=>{ document.getElementById('vroom-race-cut')?.remove(); vroomReturnToLobby(); }")
                wait_for(A, "()=>!!document.querySelector('#stage .screen-vroom-lobby')", tries=25)
                ea = {}
                for _ in range(20):
                    ea = entry(code, ALEX)
                    if ea.get("back"): break
                    A.wait_for_timeout(250)
                chk("(Q) going back to the lobby says which match it was from (back %s, the match %s)" % (ea.get("back"), room(code).get("startAt")),
                    bool(ea.get("back")) and ea.get("back") == room(code).get("startAt"), ea)
                K.evaluate("()=>document.getElementById('resumebtn')?.click()")
                wait_for(K, RACE_UP, tries=20, step=250)
                K.evaluate(ANSWER_ALL, None)
                mv = wait_for(K, "()=>{ const w = document.querySelector('.vroom-waitcard'); if(!w) return null; const b = w.querySelector('.vroom-wait-tolobby'); return w.classList.contains('is-moved-on') && b ? { btn: true } : null; }", tries=30, step=400)
                chk("(Q) the late finisher is told the race is over and offered Return to lobby, not left waiting (%s; card: %r)" % (mv,
                    K.evaluate("()=>{ const w = document.querySelector('.vroom-waitcard'); return w ? w.className + ' | ' + w.innerText.slice(0, 90) : null; }")), bool(mv))
                if mv:
                    K.evaluate("()=>document.querySelector('.vroom-waitcard .vroom-wait-tolobby').click()")
                    lob = wait_for(K, "()=>!!document.querySelector('#stage .screen-vroom-lobby')", tries=25)
                    chk("(Q) and Return to lobby takes them there", bool(lob))
            leave2(A); leave2(K)
        except Exception as ex:
            chk("(P/R/Q) ran to the end", False, repr(ex)[:300]); leave2(A); leave2(K)

    # ===================== (L) leaving a race =====================
    if want("L"):
        print("\n-- (L) leaving a race: off the race line, a line in the room's chat, not waited for", flush=True)
        try:
            code = race(A, [K])
            K.evaluate(ANSWER_ALL, 1)
            K.wait_for_timeout(900)
            before = wait_for(A, "()=>{ const m = (%s)(); return m.length >= 2 ? m : null; }" % MARKS, tries=20, step=250) or []
            A.evaluate("""()=>{ window.__alerts = 0; new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => {
                if(n.classList && n.classList.contains('vroom-chat-alert')) window.__alerts++; }))).observe(document.body, { childList: true }); }""")
            nw = len(CLOUD.writes)
            K.evaluate("()=>document.getElementById('pausebtn').click()"); K.wait_for_timeout(400)
            K.evaluate("()=>document.getElementById('pause-quit').click()"); K.wait_for_timeout(300)
            conf = K.evaluate("()=>{ const b = document.getElementById('quit-confirm'); return b ? b.closest('.pausepanel') ? 'panel' : 'other' : null; }")
            K.evaluate("()=>document.getElementById('quit-confirm').click()")
            gone = wait_for(A, "(n)=>{ const m = (%s)(); return (m.length && m.indexOf(n) < 0) ? m : null; }" % MARKS, NAMES[KIM], tries=20, step=250)
            chk("(L) Pause > Leave match asks first, then takes them out of the room (%s; still an entry: %s)" % (conf, KIM in (room(code).get("participants") or {})),
                conf == "panel" and KIM not in (room(code).get("participants") or {}), room(code).get("participants"))
            chk("(L) their marker leaves the race line on the other player's screen (%s -> %s)" % (before, gone), bool(gone) and NAMES[KIM] in before, {"before": before, "after": A.evaluate(MARKS)})
            msgs = room(code).get("chatMessages") or []
            lm = [m for m in msgs if m.get("key") == KIM and m.get("type") == "left"]
            kw = [w for w in CLOUD.writes[nw:] if w["dev"] == "kim" and w["path"] == "vrooms/" + code]
            chk("(L) the room's chat carries a line that they left the match (%s)" % (lm[-1:] or msgs[-1:]),
                bool(lm) and "match" in (lm[-1].get("text") or "") and lm[-1].get("name") == NAMES[KIM], msgs[-3:])
            chk("(L) in the leave's own write - the leaver wrote the room once from Pause to gone, the pause's own note aside (%d: %s)" % (len(kw), [w["op"] for w in kw]),
                1 <= len(kw) <= 2, kw)
            A.wait_for_timeout(800)
            t0 = time.time()
            A.evaluate(ANSWER_ALL, None)
            allin = wait_for(A, ALL_IN, tries=30, step=400)
            chk("(L) the results do not wait for them (all in %.1fs after the last answer)" % (time.time() - t0), bool(allin))
            fab = wait_for(A, "()=>{ const f = document.getElementById('roomchat-fab'); if(!f) return null; const c = f.querySelector('.roomchat-fab-count'); return { unread: c && !c.hidden ? c.textContent : '' }; }", tries=20, step=250) or {}
            chk("(L) the line is not counted unread nor raised as a chat preview (unread %r, previews %s)" % (fab.get("unread"), A.evaluate("()=>window.__alerts")),
                fab.get("unread") == "" and A.evaluate("()=>window.__alerts") == 0, fab)
            A.evaluate("()=>document.getElementById('roomchat-fab')?.click()")
            sysl = wait_for(A, "()=>{ const l = [...document.querySelectorAll('#roomchat-sheet .vroom-chat-sys')].map(x => x.textContent); return l.length ? l : null; }", tries=15, step=250)
            chk("(L) the Room chat on the results shows it as a line of its own (%s)" % sysl, bool(sysl) and any(NAMES[KIM] in x for x in sysl), sysl)
            leave2(A); leave2(K)
        except Exception as ex:
            chk("(L) ran to the end", False, repr(ex)[:300]); leave2(A); leave2(K)

    # ===================== (T) + (B) team games, 2 v 2 =====================
    if want("T") or want("B"):
        rctx, R = device(br, "rowan", ROW)
        sctx, S = device(br, "sasha", SAS)
        def team_game(game):
            code = host_room(A, unit_a, game, 6)
            for pg in (K, R, S): join(pg, code)
            ready([A, K, R, S])
            sel = ".screen-tug .choice" if game == "tug" else ".screen-battle .choice"
            for pg in (A, K, R, S): wait_for(pg, "()=>!!document.querySelector('%s')" % sel, tries=100, step=300)
            return code
        if want("T"):
            print("\n-- (T) Tug of War: somebody leaving leaves the rope, live", flush=True)
            try:
                code = team_game("tug")
                FIGS = """()=>{ const s = document.querySelector('.screen-tug'); if(!s) return null;
                    return { figs: [...s.querySelectorAll('.tug-team-fig')].map(f => f.title), names: [...s.querySelectorAll('.tug-side-name')].map(x => x.textContent).join(' | '), pos: tugShownPos }; }"""
                b4 = wait_for(A, "()=>{ const f = (%s)(); return f && f.figs.length === 4 ? f : null; }" % FIGS, tries=20, step=250) or {}
                K.evaluate("()=>document.getElementById('pausebtn').click()"); K.wait_for_timeout(400)
                K.evaluate("()=>document.querySelector('.vroom-leave-confirm .next.danger')?.click()")
                af = wait_for(A, "(n)=>{ const f = (%s)(); return (f && f.figs.indexOf(n) < 0) ? f : null; }" % FIGS, NAMES[KIM], tries=16, step=250) or A.evaluate(FIGS) or {}
                chk("(T) the leaver's figure leaves the rope and their name the side's line, while the others' question stays put (%s -> %s)" % (b4.get("figs"), af.get("figs")),
                    NAMES[KIM] in (b4.get("figs") or []) and NAMES[KIM] not in (af.get("figs") or [NAMES[KIM]]) and NAMES[KIM] not in (af.get("names") or NAMES[KIM])
                    and af.get("pos") == b4.get("pos") and len(af.get("figs") or []) == 3, {"before": b4, "after": af})
                lm = [m for m in (room(code).get("chatMessages") or []) if m.get("key") == KIM and m.get("type") == "left"]
                chk("(T) and the room's chat says they left the match (%s)" % lm[-1:], bool(lm) and "match" in (lm[-1].get("text") or ""), lm)
                for pg in (A, R, S): leave2(pg)
                K.evaluate("()=>showHome()")
            except Exception as ex:
                chk("(T) ran to the end", False, repr(ex)[:300])
                for pg in (A, K, R, S): leave2(pg)
        if want("B"):
            print("\n-- (B) Battle: somebody leaving leaves their side, live", flush=True)
            try:
                code = team_game("battle")
                FACES = """()=>{ const s = document.querySelector('.screen-battle'); if(!s) return null;
                    return { faces: s.querySelectorAll('.battle-av:not(.battle-av-more)').length, names: [...s.querySelectorAll('.battle-side-names')].map(x => x.textContent).join(' | '), pos: battlePos }; }"""
                b4 = wait_for(A, "(n)=>{ const f = (%s)(); return f && f.faces === 4 && f.names.indexOf(n) >= 0 ? f : null; }" % FACES, NAMES[KIM], tries=20, step=250) or {}
                K.evaluate("()=>document.getElementById('pausebtn').click()"); K.wait_for_timeout(400)
                K.evaluate("()=>document.querySelector('.vroom-leave-confirm .next.danger')?.click()")
                af = wait_for(A, "(n)=>{ const f = (%s)(); return (f && f.names.indexOf(n) < 0) ? f : null; }" % FACES, NAMES[KIM], tries=16, step=250) or A.evaluate(FACES) or {}
                chk("(B) the leaver's face and name leave their side, while the others' question stays put (%s -> %s faces; %r)" % (b4.get("faces"), af.get("faces"), af.get("names")),
                    b4.get("faces") == 4 and af.get("faces") == 3 and NAMES[KIM] not in (af.get("names") or NAMES[KIM]) and af.get("pos") == b4.get("pos"), {"before": b4, "after": af})
                for pg in (A, R, S): leave2(pg)
                K.evaluate("()=>showHome()")
            except Exception as ex:
                chk("(B) ran to the end", False, repr(ex)[:300])
                for pg in (A, K, R, S): leave2(pg)
        for c in (rctx, sctx):
            try: c.close()
            except Exception: pass

    # ===================== (F) every friend by name =====================
    if want("F"):
        print("\n-- (F) a friend in Fire Code alone, and one nobody knows about yet, on every friends list", flush=True)
        try:
            A.evaluate("(u)=>{ if((store.friendsIn || []).indexOf(u) < 0) store.friendsIn = (store.friendsIn || []).concat([u]); }", UNKNOWN)
            ids = A.evaluate("()=>friendPublicIds()")
            nw = len(CLOUD.writes)
            # the Friends tab open BEFORE the Fire Code friend's beat has landed
            A.evaluate("()=>{ chatDockTab = 'friends'; openChatDock(); try{ syncChatDock(); }catch(e){} }")
            ROWS = """()=>[...document.querySelectorAll('.chatdock-chatrow.is-friend:not(.is-nova)')].map(r => ({ pub: r.dataset.pub || null,
                name: (r.querySelector('.chatdock-chatrow-name') || {}).textContent, ch: (r.querySelector('.rank-avatar') || { dataset: {} }).dataset.char,
                unknown: r.hasAttribute('data-unknown') }))"""
            first = wait_for(A, "()=>{ const r = (%s)(); return r.length >= 3 ? r : null; }" % ROWS, tries=20, step=250) or []
            # now the friend in Fire Code alone opens the app: their beat (name, character, classes) lands
            dctx, D = device(br, "devon", DEV, "ifc")
            D.evaluate("()=>{ try{ sendHeartbeat(true); }catch(e){} }")
            cd = None
            for _ in range(30):
                cd = ((dump()["vrooms"].get("presence-v1") or {}).get("c") or {}).get(DEV)
                if isinstance(cd, dict) and cd.get("v"): break
                A.wait_for_timeout(300)
            dctx.close()
            chk("(F) the Fire Code-only friend's beat names them (%s)" % cd, isinstance(cd, dict) and cd.get("n") == NAMES[DEV] and cd.get("v") == AVATAR[DEV], cd)
            live = wait_for(A, "(p)=>{ const r = (%s)().find(x => x.pub === p.dev || x.name === p.name); return (r && r.name === p.name) ? r : null; }" % ROWS,
                            {"dev": DEV, "name": NAMES[DEV]}, tries=24, step=250)
            rows = A.evaluate(ROWS)
            byname = {r.get("name"): r for r in rows}
            chk("(F) the chat's Friends tab names the Fire Code-only friend, with their character, as soon as their beat lands - the tab already open (%s)" % live,
                bool(live) and live.get("ch") == AVATAR[DEV] and not live.get("unknown"), {"first": first, "now": rows})
            unk = [r for r in rows if r.get("pub") == UNKNOWN] or [r for r in rows if r.get("name") not in [NAMES[p] for p in FRIENDS[ALEX]]]
            chk("(F) a friend nothing is known about yet is listed as 'Friend' with the default character (%s)" % unk,
                len(rows) == len(ids) and bool(unk) and unk[0].get("name") == "Friend" and unk[0].get("ch") == "ninja", rows)
            # Manage friends: every friend, none dropped
            A.evaluate("()=>{ closeChatDock(); showFriends(); }")
            MF = """()=>[...document.querySelectorAll('#stage .screen-friends .friend-row:not(.is-nova)')].map(r => ({ name: (r.querySelector('.friend-row-name') || {}).textContent,
                ch: (r.querySelector('.rank-avatar') || { dataset: {} }).dataset.char, cls: !!r.querySelector('.friend-row-class'), card: r.classList.contains('is-tappable') }))"""
            mf = wait_for(A, "(p)=>{ const r = (%s)(); const n = r.map(x => x.name); return (r.length >= p.n && n.indexOf(p.d) >= 0 && n.indexOf(p.k) >= 0) ? r : null; }" % MF,
                          {"n": len(ids), "d": NAMES[DEV], "k": NAMES[KIM]}, tries=24, step=250) or A.evaluate(MF)
            mby = {r.get("name"): r for r in mf}
            chk("(F) Manage friends lists every friend - %d of %d (%s)" % (len(mf), len(ids), [r.get("name") for r in mf]), len(mf) == len(ids), mf)
            chk("(F) the Fire Code-only friend there by name and character, said for what they are (no academy rank or level) (%s)" % mby.get(NAMES[DEV]),
                bool(mby.get(NAMES[DEV])) and mby[NAMES[DEV]]["ch"] == AVATAR[DEV] and mby[NAMES[DEV]]["cls"]
                and bool(mby.get(NAMES[KIM])) and not mby[NAMES[KIM]]["cls"], mf)
            # the chat invite sheet (as from a group chat)
            A.evaluate("()=>{ window.__keepRoom = chatRoomCode; chatRoomCode = 'zzgroupchat384'; openChatInviteSheet(); }")
            inv = wait_for(A, "()=>{ const r = [...document.querySelectorAll('.invite-overlay .friend-row')].map(x => (x.querySelector('.friend-row-name') || {}).textContent); return r.length ? r : null; }", tries=12, step=250) or []
            A.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); chatRoomCode = window.__keepRoom; }")
            chk("(F) the chat's invite sheet names them too (%s)" % inv, NAMES[DEV] in inv and "Student" not in inv, inv)
            # (her own board row may go out on its own clock - the app republishes it; nothing here is about friends)
            fw = [w for w in CLOUD.writes[nw:] if w["dev"] == "alex" and w["path"].startswith("vrooms/") and w["path"] != "vrooms/presence-v1"]
            chk("(F) drawing all of that wrote nothing to the room or presence documents (%d writes besides her own beat)" % len(fw), not fw, fw)
            # the friend chat's header
            A.evaluate("(p)=>{ showHome(); openFriendChat(p); }", DEV)
            hd = wait_for(A, "()=>{ const n = document.querySelector('.chatdock-friendhead-name'); const a = document.querySelector('.chatdock-friendhead-art .rank-avatar'); return n ? { name: n.textContent, ch: a ? a.dataset.char : null } : null; }", tries=20, step=250) or {}
            chk("(F) the friend chat's header names them, with their character (%s)" % hd, hd.get("name") == NAMES[DEV] and hd.get("ch") == AVATAR[DEV], hd)
            A.evaluate("()=>{ try{ closeChatRoom(); closeChatDock(); }catch(e){} showHome(); }")
        except Exception as ex:
            chk("(F) ran to the end", False, repr(ex)[:300])

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
