#!/usr/bin/env python3
"""Build 384 r8/r9: the lobby's open switch - (6, r9) its word reads "Private lobby" off and "Open lobby" on; its line follows the switch; the game's name and icon wear its colour.
Madison (the host's lobby): "'On, anyone in 26e blah blah' wording has bad spacing and it's showing up while it's off? Also ... the word
race at the top, shouldn't the race icon and stuff be the color of the race icon?"
A four-person room you host, iPhone 17 Pro Max: (1) with the switch off the line says who can join (it does not describe ON); (2) after a
tap (switch on) it changes - the two lines differ and the on one names the class; (3) the line has air: 10px+ under the switch row and
14px+ above the first player (it was 7 / 11); (4) the game's name and icon are the game's colour (not the plain ink), for a race, a tug and a battle,
and the three differ; (5) no page errors.
  python3 tools/check-b384-lobbyopen.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
MOUNT = """(game)=>{ const me=publicIdOf(); const parts={}; parts[me]={name:'Madison',avatarChar:'ghost',level:41,badges:6,joinedAt:1,seen:9e15,ready:false};
  ['Avery','Jordan','Kim'].forEach((n,i)=>{ parts['pF'+i+'0000000000']={name:n,avatarChar:['grizzly','alien','ghost'][i],level:10+i,badges:i,joinedAt:2+i,seen:9e15,ready:i>0}; });
  __rooms['ROOM384']={hostCode:me,hostName:'Madison',units:['Identity Crimes'],versions:{},game:game,open:false,status:'waiting',mode:'exam',createdAt:1,count:null,participants:parts};
  vroomCode='ROOM384'; vroomMyKey=me; vroomIsHost=true; vroomIsOpen=false; vroomUnits=['Identity Crimes']; vroomLastDoc={code:'ROOM384',data:JSON.parse(JSON.stringify(__rooms.ROOM384))}; showVirtualRoomLobby(); }"""
LINE = """()=>{ const l=document.querySelector('.vroom-open-line'), sw=document.querySelector('.vroom-open-switch'), first=document.querySelector('.vroom-roster-list > *');
  if(!l) return null; const lr=l.getBoundingClientRect(), sr=sw.getBoundingClientRect(), fr=first?first.getBoundingClientRect():null;
  return { txt:l.textContent.trim(), on: sw.getAttribute('aria-checked'), underRow: lr.top - sr.bottom, aboveFirst: fr ? fr.top - lr.bottom : null }; }"""
TITLE = """()=>{ const t=document.querySelector('.vroom-test-summary-title'); if(!t) return null; const ic=t.querySelector('.vroom-summary-icon'), nm=[...t.children].find(c=>!c.classList.contains('vroom-summary-icon'));
  return { name:getComputedStyle(nm||t).color, icon: ic ? getComputedStyle(ic).color : null, ink:getComputedStyle(document.body).color }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1, init=cb._ROOM_FAKE)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.evaluate("document.querySelectorAll('#splashscreen,#pushing-update,#intro-pop').forEach(n=>n.remove()); __useRooms();")
    pg.evaluate(MOUNT, "race"); pg.wait_for_timeout(1500)
    off = pg.evaluate(LINE)
    chk("(1) switch off: the line says who can join, not what ON does (%r)" % (off and off["txt"]), off and off["on"] == "false" and not __import__("re").match(r"on\b", off["txt"].lower()) and "find this room" not in off["txt"], off)
    W = "()=>{ const w=document.querySelector('.vroom-open-word'); return w ? w.textContent.trim() : null; }"
    w_off = pg.evaluate(W)
    pg.evaluate("()=>{ document.querySelector('.vroom-open-switch').click(); }"); pg.wait_for_timeout(500)
    on = pg.evaluate(LINE)
    w_on = pg.evaluate(W)
    # (r9) "Shouldn't this just say private lobby/open lobby?" - the switch's word names the room it makes
    chk("(6) the switch's word follows it: %r off, %r on" % (w_off, w_on), w_off == "Private lobby" and w_on == "Open lobby", [w_off, w_on])
    chk("(2) switch on: the line changes and names the class (%r)" % (on and on["txt"]), on and on["on"] == "true" and on["txt"] != off["txt"] and ("26E" in on["txt"] or "Fire Code" in on["txt"]), on)
    chk("(3) air round the line (%.1f under the switch row, %s above the first player)" % (on["underRow"], on["aboveFirst"]), on["underRow"] >= 10 and on["aboveFirst"] is not None and on["aboveFirst"] >= 14, on)
    cols = {}
    for g in ("race", "tug", "battle"):
        pg.evaluate(MOUNT, g); pg.wait_for_timeout(1200)
        t = pg.evaluate(TITLE); cols[g] = t
        chk("(4) %s: the name and icon in the game's colour (%s / %s, ink %s)" % (g, t and t["name"], t and t["icon"], t and t["ink"]), t and t["name"] == t["icon"] and t["name"] != t["ink"] and t["name"] not in ("rgb(255, 255, 255)",), t)
    chk("(4) the three games' colours differ", len({c["name"] for c in cols.values() if c}) == 3, cols)
    chk("(5) no page errors", not errs, errs[:3])
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
