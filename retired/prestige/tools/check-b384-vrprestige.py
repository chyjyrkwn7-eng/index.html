"""Build 384.134: FIRE CODE PRESTIGE EMBLEMS IN VIRTUAL ROOMS. Madison: Fire Code prestige emblems must show in Virtual Rooms.

Read off the page by shape and by the app's own numbers (never label strings), in a Fire Code page and in the academy's, with the room
stood up on the in-page Firestore stand-in the prestige gate uses (tools/b384_prestige_lib.py): made-up classmates at prestige 0, 1, 2, 3,
one with no `pg` (an older client), one with an unknown value (7) and one with a string ("3"), a name too long for its row.
 (A) THE DATA: joining a Fire Code room writes `pg` (this account's count) in the entry the join already writes; an academy room's entry
     has none; the presence beat that already runs carries it too, follows a change at once and a count of 0 clears it; the beat is still
     one write to the room per tick (no extra write, none per answer); no sync code anywhere in the room document;
 (B) THE LOBBY, phone and tablet: each member's emblem is their count, none for 0 / no field / 7 / "3"; yours is your own live count; it
     sits right after the name on its line, about the text's height, the numeral its count; a long name keeps its ellipsis and the emblem
     stays whole inside its row; rows stay at least 44px (the row is the tap target);
 (C) NOTHING MOVES WHEN IT IS ABSENT: the same room drawn with every `pg` removed has the same rows, the same heights and the same
     roster height; and a change of one member's `pg` redraws their row live (0 -> 1 -> 3 -> 0) with no reload;
 (D) PRESTIGE IS FIRE CODE'S: an ACADEMY room draws no emblem on anybody, whatever their entries say (the Fire Code page and the academy's
     page both), and a Fire Code room joined from the ACADEMY's page draws them, with this account's count read off Fire Code's saved copy;
 (E) EVERYWHERE A MEMBER IS NAMED: the person card opened from a row (the room's entry, not the board's), the race podium (first three
     and the list under them), the sides' podium, the race results board, the winners' cutscene and the room's chat (the sender's
     name) each carry the emblem beside the name, the same drawing as the Leaderboard's (prestigeMark), and nothing where there is none;
 (F) no page errors.
  python3 tools/check-b384-vrprestige.py [--against OLD/index.html] [--only A,B]     (must FAIL on the build before: there is no `pg` in a room)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_prestige_lib as L
from playwright.sync_api import sync_playwright

ARGS = sys.argv[1:]
def arg(n): return ARGS[ARGS.index(n) + 1] if n in ARGS else None
AGAINST = arg("--against")
ONLY = set(x.strip().upper() for x in (arg("--only") or "").split(",")) - {""}
def wanted(n): return not ONLY or n in ONLY
TEXT = open(AGAINST or os.path.join(L.ROOT, "index.html"), encoding="utf-8").read()

ok = True
def chk(name, cond, info=None):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or info is None else "  -> " + str(info)[:700]), flush=True)
class section:
    def __init__(self, name): self.name = name
    def __enter__(self): return self
    def __exit__(self, t, e, tb):
        if t is not None: chk(self.name + " runs", False, repr(e)[:500]); return True

# the beat (45 s) is run at 250 ms so a gate can see it: nothing else in the app waits exactly 45000
FAST = "window.__si = window.setInterval; window.setInterval = function(f, ms){ return window.__si.apply(window, [f, ms === 45000 ? 250 : ms].concat([].slice.call(arguments, 2))); };"
BEAT = 250
LONG = "Bartholomew Featherstonehaugh-Montgomery"
# name, character, prestige (None: an older client's entry with no `pg`; 7 and "3": values nothing may draw), level, badges
MATES = [("Alexis", "pgstate", 3, 80, 40), ("Kimber", "pgmarshal", 2, 80, 38), ("Leeland", "pgdeputy", 1, 80, 38), ("Rosa", "grizzly", 0, 52, 20),
         ("Dmitri", "alien", None, 41, 13), ("Priya", "ghost", 7, 30, 8), ("Tomas", "grizzly", "3", 80, 38), (LONG, "ninja", 3, 60, 22)]
WANT = {"Alexis": 3, "Kimber": 2, "Leeland": 1, "Rosa": 0, "Dmitri": 0, "Priya": 0, "Tomas": 0, LONG: 3}
def pub_of(i): return "pgvr%07d" % i
def room(cls, mates=MATES, finished=False, chat=None, game="race", hostile=None):
    parts = {}
    for i, (nm, ch, pgv, lv, bd) in enumerate(mates):
        e = {"name": nm, "avatarChar": ch, "level": lv, "badges": bd, "joinedAt": 10 + i, "seen": 9e15, "ready": i % 2 == 0, "progress": 100 if finished else 0,
             "finished": bool(finished), "banner": "", "accent": "ink"}
        if finished: e.update({"xp": 900 - 70 * i, "elapsedMs": 60000 + 4000 * i, "score": 900 - 70 * i})
        if pgv is not None: e["pg"] = pgv
        if hostile is not None: e["pg"] = hostile
        parts[pub_of(i)] = e
    d = {"hostCode": pub_of(0), "units": [], "versions": {}, "timeLimit": None, "count": None, "game": game, "open": False, "hostName": mates[0][0],
         "hostAvatar": mates[0][1], "status": "finished" if finished else "waiting", "startAt": (L.now_ms - 400000) if finished else None, "mode": "exam",
         "createdAt": L.now_ms - 600000, "participants": parts}
    if cls: d["cls"] = cls
    if chat:
        d["chatMessages"] = [{"id": "m%d" % i, "key": pub_of(i), "name": mates[i][0], "text": "hello %d" % i, "ts": L.now_ms - 1000 * (len(chat) - n)} for n, i in enumerate(chat)]
    return d

def boot(br, page_cls, prestige, rooms, w=440, h=956, extra_init=""):
    """A device of the account in `page_cls` ('ifc': Fire Code's page, 'academy': the academy's), Fire Code's count `prestige`."""
    fc = L.account(ifc=True, extra={"prestige": prestige} if prestige is not None else None)
    a2 = dict(L.account(), classes=["academy", "ifc"])
    seed = {"progress": {L.CODE: a2, L.CODE + "__ifc": fc}, "leaderboard": {},
            "vrooms": dict({"lb-ifc-v1": {"kind": "board", "cls": "ifc", "rows": L.mate_rows()}}, **rooms)}
    init = L.init_js(a2, fc, active=page_cls) + ";" + extra_init
    ctx, pg, errs = L.page(br, TEXT, seed, init, w=w, h=h)
    L.quiet(pg)
    return ctx, pg, errs

JOIN = "async(code)=>{ const ok = await joinVirtualRoomLobby(code); await new Promise(r=>setTimeout(r,2200)); return [ok, vroomCode, BANK_CLASS]; }"
# every roster row: name text, the emblem (its numeral and drawing), where it sits against the text, the row's box
ROWS = """()=>[...document.querySelectorAll('.vroom-roster .vroom-row')].map(row => { const nm = row.querySelector('.lb-name'); const mk = nm.querySelector('.pg-mark');
  const txtEl = nm.querySelector('.pg-nm') || nm; const range = document.createRange(); range.setStart(txtEl.firstChild, 0); range.setEnd(txtEl.firstChild, txtEl.firstChild.length);
  const t = range.getBoundingClientRect(), r = row.getBoundingClientRect(), m = mk ? mk.getBoundingClientRect() : null;
  return { name: txtEl.firstChild.textContent.trim(), pg: mk ? +mk.dataset.pg : 0, svg: mk ? !!mk.querySelector('svg.pg-emblem-' + mk.dataset.pg) : false,
    gap: m ? Math.round(m.left - t.right) : null, dy: m ? Math.round(Math.abs((m.top + m.bottom) / 2 - (t.top + t.bottom) / 2)) : null, mh: m ? Math.round(m.height) : null,
    th: Math.round(t.height), inside: m ? (m.left >= r.left - .5 && m.right <= r.right + .5 && m.top >= r.top - .5 && m.bottom <= r.bottom + .5) : null,
    rh: Math.round(r.height * 10) / 10, rw: Math.round(r.width * 10) / 10, top: Math.round(r.top), you: !!row.querySelector('.vroom-you-tag'), label: mk ? mk.getAttribute('aria-label') : null }; })"""
ROSTER_H = "()=>Math.round(document.querySelector('.vroom-roster').getBoundingClientRect().height * 10) / 10"
SET_PG = """async ([k, v])=>{ const ref = firebase.firestore().collection('vrooms').doc(vroomCode); const o = {}; o['participants.' + k + '.pg'] = v; await ref.update(o);
  await new Promise(r=>setTimeout(r,900)); }"""

def by_name(rows): return {r["name"]: r for r in rows}

def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=L.CHROME, args=["--no-sandbox"])
        errs_all = []

        # ------------------------------------------------------------------------------------------------------------ (A) the data
        if wanted("A"):
            with section("(A)"):
                ctx, pg, errs = boot(br, "ifc", 2, {"FCROOM": room("ifc"), "ACROOM": room(None)}, extra_init=FAST); errs_all += errs
                me = pg.evaluate("()=>publicIdOf()")
                j = pg.evaluate(JOIN, "FCROOM")
                ent = pg.evaluate("(m)=>__cloud.vrooms.FCROOM.participants[m]", me) or {}
                chk("(A) joining a Fire Code room writes this account's prestige in its entry (II) %s" % ent.get("pg"), j[0] is True and ent.get("pg") == 2, [j, ent])
                pg.wait_for_timeout(BEAT * 4)
                chk("(A) and the beat that was already running carries it too", pg.evaluate("(m)=>__cloud.vrooms.FCROOM.participants[m].pg", me) == 2)
                # the beat is one write per tick: count the room's writes over a window, then again while the count changes
                def writes(ms):
                    pg.evaluate("()=>{ window.__w0 = __writes.filter(x => x === 'vrooms/FCROOM').length; }")
                    pg.wait_for_timeout(ms)
                    return pg.evaluate("()=>__writes.filter(x => x === 'vrooms/FCROOM').length - window.__w0")
                a = writes(2000)
                pg.evaluate("()=>{ store.prestige = 3; saveStore(); }")
                b = writes(2000)
                cap = 2000 // BEAT + 3
                chk("(A) the beat is still one write to the room per tick: %d, then %d while the count changed (a tick every %dms)" % (a, b, BEAT),
                    0 < a <= cap and 0 < b <= cap, [a, b, cap])
                chk("(A) a change of the count reaches the room by the next beat (III)", pg.evaluate("(m)=>__cloud.vrooms.FCROOM.participants[m].pg", me) == 3)
                pg.evaluate("()=>{ store.prestige = 0; saveStore(); }"); pg.wait_for_timeout(BEAT * 4)
                chk("(A) and a count of 0 clears it (a reset account) %s" % pg.evaluate("(m)=>__cloud.vrooms.FCROOM.participants[m].pg", me),
                    pg.evaluate("(m)=>__cloud.vrooms.FCROOM.participants[m].pg", me) == 0)
                dump = pg.evaluate("()=>JSON.stringify(__cloud.vrooms)")
                chk("(A) no sync code or friend code in any room document", L.CODE not in dump and L.MYCODE not in dump and L.CODE.replace("-", "") not in dump)
                pg.evaluate("()=>{ leaveVirtualRoom(); }"); pg.wait_for_timeout(500)
                pg.evaluate("()=>{ store.prestige = 2; saveStore(); }")
                j = pg.evaluate(JOIN, "ACROOM")
                ent = pg.evaluate("(m)=>__cloud.vrooms.ACROOM.participants[m]", me) or {}
                pg.wait_for_timeout(BEAT * 4)
                ent2 = pg.evaluate("(m)=>__cloud.vrooms.ACROOM.participants[m]", me) or {}
                chk("(A) an academy room's entry has no `pg`, at the join or on a beat (the document is as it was) %s %s" % (ent.get("pg"), ent2.get("pg")),
                    j[0] is True and j[2] == "academy" and "pg" not in ent and "pg" not in ent2, [j, ent, ent2])
                ctx.close()
                # the academy's page, Fire Code room: the count is read off Fire Code's saved copy
                ctx, pg, errs = boot(br, "academy", 3, {"FCROOM": room("ifc")}, extra_init=FAST); errs_all += errs
                me = pg.evaluate("()=>publicIdOf()")
                j = pg.evaluate(JOIN, "FCROOM")
                ent = pg.evaluate("(m)=>__cloud.vrooms.FCROOM.participants[m]", me) or {}
                chk("(A) from the academy's page a Fire Code room's entry carries Fire Code's count (III) %s" % ent.get("pg"), j[2] == "ifc" and ent.get("pg") == 3, [j, ent])
                ctx.close()

        # ------------------------------------------------------------------------------------------------------------ (B) (C) the lobby
        for tag, (w, h) in (("phone", (440, 956)), ("tablet", (834, 1194))):
            if not (wanted("B") or wanted("C")): break
            with section("(B)/(C) " + tag):
                ctx, pg, errs = boot(br, "ifc", 2, {"FCROOM": room("ifc")}, w=w, h=h); errs_all += errs
                j = pg.evaluate(JOIN, "FCROOM")
                rows = pg.evaluate(ROWS); by = by_name(rows)
                got = {k: by.get(k, {}).get("pg") for k in WANT}
                chk("(B) %s: each member's emblem is their count, none for 0 / no field / 7 / \"3\" %s" % (tag, got), j[0] is True and got == WANT, rows)
                mine = [r for r in rows if r["you"] or r["name"] == "Maddox"]
                chk("(B) %s: your own row is your own count (II), not a stored one %s" % (tag, [(r["name"], r["pg"]) for r in mine]), mine and mine[0]["pg"] == 2, rows)
                lit = [r for r in rows if r["pg"]]
                chk("(B) %s: the emblem is the real drawing, labelled, right after the name, on its line, about the text's height %s" % (tag, [(r["name"][:6], r["gap"], r["dy"], r["mh"], r["th"]) for r in lit]),
                    len(lit) >= 4 and all(r["svg"] and r["label"] and 0 <= r["gap"] <= 12 and r["dy"] <= 4 and .8 * r["th"] <= r["mh"] <= 2.2 * r["th"] for r in lit if r["name"] != LONG), lit)
                lg = by.get(LONG, {})
                chk("(B) %s: a long name keeps its ellipsis and the emblem is whole inside the row %s" % (tag, (lg.get("inside"), lg.get("gap"))), lg.get("pg") == 3 and lg.get("inside") is True, lg)
                ell = pg.evaluate("()=>{ const n = [...document.querySelectorAll('.vroom-row .lb-name .pg-nm')].find(e => /Bartholomew/.test(e.textContent)); return n ? [n.scrollWidth > n.clientWidth + 1, getComputedStyle(n).textOverflow] : null; }")
                chk("(B) %s: it is the NAME that is shortened (ellipsis), never the emblem %s" % (tag, ell), ell and ell[0] and ell[1] == "ellipsis", ell)
                chk("(B) %s: every row is at least 44px tall (the row is the tap target) %s" % (tag, sorted(set(r["rh"] for r in rows))), all(r["rh"] >= 44 for r in rows), rows)
                # (C) nothing moves when it is absent
                if wanted("C"):
                    H1 = pg.evaluate(ROSTER_H)
                    for i in range(len(MATES)):
                        pg.evaluate("""async (k)=>{ const o = {}; o['participants.' + k + '.pg'] = firebase.firestore.FieldValue.delete(); await firebase.firestore().collection('vrooms').doc(vroomCode).update(o); }""", pub_of(i))
                    pg.evaluate("""async ()=>{ const o = {}; o['participants.' + publicIdOf() + '.pg'] = firebase.firestore.FieldValue.delete(); await firebase.firestore().collection('vrooms').doc(vroomCode).update(o); }""")
                    pg.evaluate("()=>{ store.prestige = 0; }"); pg.wait_for_timeout(1300)
                    rows0 = pg.evaluate(ROWS); H0 = pg.evaluate(ROSTER_H)
                    chk("(C) %s: with every `pg` gone no emblem is drawn at all %s" % (tag, [r["pg"] for r in rows0]), not any(r["pg"] for r in rows0), rows0)
                    same = len(rows0) == len(rows) and all(abs(a["rh"] - b["rh"]) <= .6 and abs(a["rw"] - b["rw"]) <= .6 and abs(a["top"] - b["top"]) <= 1 for a, b in zip(rows, rows0))
                    chk("(C) %s: and the rows are the same boxes, in the same places, as with them (roster %s against %s)" % (tag, H1, H0), same and abs(H1 - H0) <= 1, [rows, rows0])
                    # live: one member's `pg` moves 0 -> 1 -> 3 -> 0 with no reload
                    seen = []
                    for v in (1, 3, 0):
                        pg.evaluate(SET_PG, [pub_of(3), v])
                        seen.append(by_name(pg.evaluate(ROWS)).get("Rosa", {}).get("pg"))
                    chk("(C) %s: a member's emblem follows their count live, 0 -> 1 -> 3 -> 0 %s" % (tag, seen), seen == [1, 3, 0], seen)
                    pg.evaluate("()=>{ store.prestige = 3; }")
                    pg.evaluate(SET_PG, [pub_of(3), 0])
                    chk("(C) %s: and yours follows a wear at once (this device's count) %s" % (tag, [r["pg"] for r in pg.evaluate(ROWS) if r["name"] == "Maddox"]),
                        [r["pg"] for r in pg.evaluate(ROWS) if r["name"] == "Maddox"] == [3])
                ctx.close()

        # ------------------------------------------------------------------------------------------------------------ (D) Fire Code only
        if wanted("D"):
            with section("(D)"):
                # an academy room, joined from Fire Code's page: every entry says III and nobody is drawn with anything
                ctx, pg, errs = boot(br, "ifc", 3, {"ACROOM": room(None, hostile=3)}); errs_all += errs
                j = pg.evaluate(JOIN, "ACROOM")
                rows = pg.evaluate(ROWS)
                chk("(D) an academy room (joined from Fire Code's page) draws no emblem on anybody, though every entry says III, nor on you %s" % [(r["name"][:5], r["pg"]) for r in rows],
                    j[2] == "academy" and len(rows) >= 8 and not any(r["pg"] for r in rows), [j, rows])
                pg.evaluate("""()=>{ document.querySelector('.vroom-roster .vroom-row').click(); }"""); pg.wait_for_timeout(600)
                card = pg.evaluate("()=>[!!document.querySelector('.person-card'), !!document.querySelector('.person-card .pg-mark')]")
                chk("(D) and its person card shows none either %s" % card, card == [True, False], card)
                ctx.close()
                # the academy's page, an academy room
                ctx, pg, errs = boot(br, "academy", 3, {"ACROOM": room(None, hostile=3)}); errs_all += errs
                j = pg.evaluate(JOIN, "ACROOM")
                rows = pg.evaluate(ROWS)
                chk("(D) the academy's page in an academy room: none %s" % [(r["name"][:5], r["pg"]) for r in rows], j[2] == "academy" and len(rows) >= 8 and not any(r["pg"] for r in rows), rows)
                ctx.close()
                # the academy's page in a Fire Code room: the emblems are drawn, yours from Fire Code's saved copy
                ctx, pg, errs = boot(br, "academy", 3, {"FCROOM": room("ifc")}); errs_all += errs
                j = pg.evaluate(JOIN, "FCROOM")
                rows = pg.evaluate(ROWS); by = by_name(rows)
                got = {k: by.get(k, {}).get("pg") for k in WANT}
                chk("(D) a Fire Code room joined from the ACADEMY's page draws them as Fire Code's page does %s" % got, j[2] == "ifc" and got == WANT, rows)
                chk("(D) ...and yours is Fire Code's count (III), read off its saved copy %s" % [r["pg"] for r in rows if r["name"] == "Maddox"], [r["pg"] for r in rows if r["name"] == "Maddox"] == [3])
                ctx.close()

        # ------------------------------------------------------------------------------------------------------------ (E) everywhere a member is named
        if wanted("E"):
            with section("(E)"):
                names = ["Alexis", "Kimber", "Leeland", "Rosa", "Dmitri"]
                M5 = [m for m in MATES if m[0] in names]
                chat = [0, 1, 2, 3, 4]
                for tag, (w, h) in (("phone", (440, 956)), ("tablet", (834, 1194))):
                    ctx, pg, errs = boot(br, "ifc", 2, {"FCROOM": room("ifc", M5, finished=True, chat=chat), "ACROOM": room(None, M5, finished=True, chat=chat, hostile=3)}, w=w, h=h); errs_all += errs
                    pg.evaluate(JOIN, "FCROOM")
                    # --- the person card from a row: the room's entry, not the board's (Kimber is on the board at II as well: use a count only the room says)
                    pg.evaluate(SET_PG, [pub_of(4), 1])        # Dmitri, who is not on the board with a count: the room says I
                    pg.evaluate("""()=>{ const rows = [...document.querySelectorAll('.vroom-roster .vroom-row')]; rows.find(r => /Dmitri/.test(r.textContent)).click(); }"""); pg.wait_for_timeout(700)
                    card = pg.evaluate("()=>{ const m = document.querySelector('.person-card .person-sheet-name .pg-mark'); return m ? [+m.dataset.pg, !!m.querySelector('svg')] : null; }")
                    chk("(E) %s: a row's person card shows the emblem from the ROOM's entry (Dmitri, I) %s" % (tag, card), card == [1, True], card)
                    pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(o => o.remove())")
                    pg.evaluate("""async (k)=>{ const o = {}; o['participants.' + k + '.pg'] = firebase.firestore.FieldValue.delete(); await firebase.firestore().collection('vrooms').doc(vroomCode).update(o); await new Promise(r=>setTimeout(r,500)); }""", pub_of(4))
                    # --- the chat: the sender's name, between the name and its colon
                    ch = pg.evaluate("""()=>[...document.querySelectorAll('.vroom-chat-msg-name')].map(n => { const mk = n.querySelector('.pg-mark'); const tn = [...n.childNodes].find(x => x.nodeType === 3);
                      const range = document.createRange(); range.setStart(tn, 0); range.setEnd(tn, tn.length); const t = range.getBoundingClientRect(), m = mk ? mk.getBoundingClientRect() : null;
                      return { name: tn.textContent.replace(/[: ]+$/, ''), pg: mk ? +mk.dataset.pg : 0, gap: m ? Math.round(m.left - t.right) : null, dy: m ? Math.round(Math.abs((m.top + m.bottom) / 2 - (t.top + t.bottom) / 2)) : null,
                               line: Math.round(n.parentElement.getBoundingClientRect().height) }; })""")
                    want = {"Alexis": 3, "Kimber": 2, "Leeland": 1, "Rosa": 0, "Dmitri": 0}
                    got = {r["name"]: r["pg"] for r in ch}
                    chk("(E) %s: the room's chat carries the sender's emblem after the name %s" % (tag, got), got == want, ch)
                    lit = [r for r in ch if r["pg"]]
                    chk("(E) %s: ...on the name's line, close %s" % (tag, [(r["name"][:5], r["gap"], r["dy"]) for r in lit]), lit and all(0 <= r["gap"] <= 14 and r["dy"] <= 5 for r in lit), ch)
                    lines = sorted(set(r["line"] for r in ch))
                    chk("(E) %s: ...and a message line is no taller with an emblem than without %s" % (tag, lines), lines[-1] - lines[0] <= 2, ch)
                    # --- the podiums, the results board and the cutscene, from the room's document as it stands
                    NEAR = """(sel)=>[...document.querySelectorAll(sel)].map(nm => { const mk = nm.querySelector('.pg-mark'); const txt = nm.querySelector('.pg-nm') || nm;
                      const tn = [...txt.childNodes].find(x => x.nodeType === 3); const range = document.createRange(); range.setStart(tn, 0); range.setEnd(tn, tn.length);
                      const t = range.getBoundingClientRect(), m = mk ? mk.getBoundingClientRect() : null; const p = nm.getBoundingClientRect();
                      return { name: tn.textContent.replace(/[\\s★]+$/, ''), pg: mk ? +mk.dataset.pg : 0, gap: m ? Math.round(m.left - t.right) : null, dy: m ? Math.round(Math.abs((m.top + m.bottom) / 2 - (t.top + t.bottom) / 2)) : null,
                        inside: m ? (m.right <= p.right + 1 && m.left >= p.left - 1) : null, th: Math.round(t.height), mh: m ? Math.round(m.height) : null }; })"""
                    pg.evaluate("""()=>{ const d = __cloud.vrooms.FCROOM; vroomMyKey = publicIdOf(); window.__podium = buildVroomRacePodium(JSON.parse(JSON.stringify(d))); stage.replaceChildren(window.__podium); }""")
                    pg.wait_for_timeout(500)
                    pod = pg.evaluate(NEAR, ".vr-podium-race .lw-podium-name, .vr-podium-race .vr-podium-name")
                    # you are not in the finished list (the join came after it): the five are the fixtures'
                    got = {r["name"]: r["pg"] for r in pod}
                    chk("(E) %s: the race podium (the first three and the list under them) %s" % (tag, got), got == want or (got.get("Alexis") == 3 and got.get("Kimber") == 2 and got.get("Leeland") == 1 and not got.get("Rosa") and not got.get("Dmitri") and len(got) >= 5), pod)
                    chk("(E) %s: ...beside the name, on its line, inside its box %s" % (tag, [(r["name"][:5], r["gap"], r["dy"]) for r in pod if r["pg"]]),
                        all(0 <= r["gap"] <= 14 and r["dy"] <= 5 and r["inside"] for r in pod if r["pg"]) and any(r["pg"] for r in pod), pod)
                    pg.evaluate("""()=>{ const d = JSON.parse(JSON.stringify(__cloud.vrooms.FCROOM)); const ks = Object.keys(d.participants);
                      const o = { mine: 'a', winner: 'a', membersOf: s => s === 'a' ? ks.slice(0, 3) : ks.slice(3), numOf: k => 10 + ks.indexOf(k), unit: 'pts', short: 'pts' };
                      stage.replaceChildren(buildVroomTeamPodium(d, o)); }""")
                    pg.wait_for_timeout(400)
                    tp = pg.evaluate(NEAR, ".vr-podium-team .vr-podium-name")
                    got = {r["name"]: r["pg"] for r in tp}
                    chk("(E) %s: the sides' podium: each member listed under a side %s" % (tag, got), got.get("Alexis") == 3 and got.get("Kimber") == 2 and got.get("Leeland") == 1 and not got.get("Rosa") and len(got) == 5, tp)
                    pg.evaluate("""()=>{ const d = JSON.parse(JSON.stringify(__cloud.vrooms.FCROOM)); vroomMyKey = publicIdOf(); stage.replaceChildren(); playVroomRaceCutscene(vroomRankedEntries(d), roomClassOf(d)); }""")
                    pg.wait_for_timeout(1500)
                    cut = pg.evaluate(NEAR, "#vroom-race-cut .vrc-name-text")
                    got = {r["name"]: r["pg"] for r in cut}
                    chk("(E) %s: the race results board %s" % (tag, got), got.get("Alexis") == 3 and got.get("Kimber") == 2 and got.get("Leeland") == 1 and not got.get("Rosa") and len(got) == 5, cut)
                    chk("(E) %s: ...beside the name, inside its box %s" % (tag, [(r["name"][:5], r["gap"], r["dy"]) for r in cut if r["pg"]]),
                        all(0 <= r["gap"] <= 14 and r["dy"] <= 5 and r["inside"] for r in cut if r["pg"]) and any(r["pg"] for r in cut), cut)
                    pg.evaluate("()=>{ document.getElementById('vroom-race-cut')?.remove(); }")
                    pg.evaluate("""()=>{ const d = JSON.parse(JSON.stringify(__cloud.vrooms.FCROOM)); const e = Object.keys(d.participants).slice(0, 4).map(k => ({ name: d.participants[k].name, avatar: d.participants[k].avatarChar,
                       sub: 'x', pg: vroomPrestigeFor(d.participants[k], k, roomClassOf(d)) }));
                       playVroomWinnerCutscene({ kind: 'race', entries: e, opening: 'a', title: 'b', floor: 'line' }, () => {});
                       window.__e2 = e; }""")
                    pg.wait_for_timeout(1500)
                    wc = pg.evaluate(NEAR, "#vroom-cutscene .vroom-cut-pname")
                    got = {r["name"]: r["pg"] for r in wc}
                    chk("(E) %s: the winners' cutscene (a podium: the first three) %s" % (tag, got), got.get("Alexis") == 3 and got.get("Kimber") == 2 and got.get("Leeland") == 1 and len(got) == 3, wc)
                    chk("(E) %s: ...centred with the name, inside its box %s" % (tag, [(r["name"][:5], r["gap"], r["dy"]) for r in wc if r["pg"]]),
                        all(0 <= r["gap"] <= 14 and r["dy"] <= 5 and r["inside"] for r in wc if r["pg"]) and any(r["pg"] for r in wc), wc)
                    pg.evaluate("()=>{ document.getElementById('vroom-cutscene')?.remove(); }")
                    # an academy room: the same surfaces, none
                    pg.evaluate("()=>{ leaveVirtualRoom(); }"); pg.wait_for_timeout(500)
                    j = pg.evaluate(JOIN, "ACROOM")
                    ch = pg.evaluate("()=>[...document.querySelectorAll('.vroom-chat-msg-name .pg-mark')].length")
                    pg.evaluate("""()=>{ const d = JSON.parse(JSON.stringify(__cloud.vrooms.ACROOM)); vroomMyKey = publicIdOf(); stage.replaceChildren(buildVroomRacePodium(d)); }""")
                    pod = pg.evaluate("()=>document.querySelectorAll('.vr-podium-race .pg-mark').length")
                    pg.evaluate("""()=>{ const d = JSON.parse(JSON.stringify(__cloud.vrooms.ACROOM)); stage.replaceChildren(); playVroomRaceCutscene(vroomRankedEntries(d), roomClassOf(d)); }""")
                    pg.wait_for_timeout(900)
                    cut = pg.evaluate("()=>document.querySelectorAll('#vroom-race-cut .pg-mark').length")
                    chk("(E) %s: an academy room's chat, podium and results board carry no emblem (every entry says III) %s" % (tag, [ch, pod, cut]), j[2] == "academy" and ch == 0 and pod == 0 and cut == 0, [j, ch, pod, cut])
                    ctx.close()

        # ------------------------------------------------------------------------------------------------------------ (F)
        chk("(F) no page errors %s" % errs_all[:3], not errs_all, errs_all)
        br.close()

main()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
