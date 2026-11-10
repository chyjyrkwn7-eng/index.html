#!/usr/bin/env python3
"""Build 384.21: a Virtual Room lobby row keeps its name wide and its status at the right edge.
Madison, a lobby screenshot (iPhone, Fire Code room, just him in it): the "Not ready" chip sat right after the name in the middle of the row with
the rest of the row empty, and his name was cut to "Ma...": "This looks broken, it's on the left, your username isn't visible either".
Read off the page (boxes, not words), for a room of one, of three, and of eight (crowded: two across), on a phone, an SE, his page-zoomed 518px
viewport and an iPad:
 (1) a row in an uncrowded room: the name column fills the room to the status (its right edge + the row's gap = the status's left edge, within 2px);
 (2) the status sits at the row's right edge (its right edge = the row's right edge less its padding, within 2px);
 (3) a short name is never cut (its box is not scrolled: scrollWidth <= clientWidth) and "(You)" is on the row; a very long name IS cut with an
     ellipsis but the status is still at the right edge;
 (4) a crowded room keeps its tight rows (not the grid) and nothing scrolls sideways; no page errors.
Run:  python3 tools/check-b384-lobbyrow.py   (--against OLD/index.html must FAIL: 384.20's name column is as wide as its own words)"""
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
ROOM = """(spec)=>{ const me=publicIdOf(); const parts={}; parts[me]={name:spec.me,avatarChar:'ghost',level:4,badges:0,joinedAt:1,seen:9e15,ready:false,banner:'tests500'};
  for(let i=0;i<spec.others;i++) parts['pF'+i+'0000000000']={name:['Avery','Jordan','Kim','Lee','Sam','Pat','Chris'][i%7],avatarChar:['zeus','alien','ghost'][i%3],level:10+i,badges:i%5,joinedAt:2+i,seen:9e15,ready:i%2===1};
  __rooms['ROOM384']={hostCode:me,hostName:spec.me,units:[],versions:{},game:null,open:false,status:'waiting',mode:'exam',createdAt:1,count:null,participants:parts};
  vroomCode='ROOM384'; vroomMyKey=me; vroomIsHost=true; vroomUnits=[]; vroomLastDoc={code:'ROOM384',data:JSON.parse(JSON.stringify(__rooms.ROOM384))}; showVirtualRoomLobby(); }"""
ROWS = """()=>{ const roster=document.querySelector('.vroom-roster'); const crowded=roster.classList.contains('is-crowded');
  return { crowded, sw:document.documentElement.scrollWidth-innerWidth, rows:[...document.querySelectorAll('.vroom-row')].map(r=>{ const cs=getComputedStyle(r), rb=r.getBoundingClientRect(), n=r.querySelector('.lb-name-wrap').getBoundingClientRect(),
      b=r.querySelector('.vroom-ready-badge').getBoundingClientRect(), nm=r.querySelector('.lb-name');
      return { disp:cs.display, gap:parseFloat(cs.columnGap)||0, padR:parseFloat(cs.paddingRight)+parseFloat(cs.borderRightWidth), fill: b.left-n.right, edge: rb.right-b.right, cut: nm.scrollWidth>nm.clientWidth+1,
               you: !!r.querySelector('.vroom-you-tag'), mine: r.classList.contains('is-you') }; }) }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for lab, W, H in (("iPhone 17 Pro Max", 440, 956), ("iPhone SE", 375, 667), ("page zoom 518", 518, 1126), ("iPad Pro 11in", 834, 1194)):
        ctx, pg = cb.booted(br, W, H, seed=cb.USED_ACCOUNT, dpr=1, init=cb._ROOM_FAKE)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("document.querySelectorAll('#splashscreen,#pushing-update,#intro-pop').forEach(n=>n.remove()); __useRooms();")
        for what, spec in (("a room of one", {"me": "Madison", "others": 0}), ("a room of three", {"me": "Madison", "others": 2}),
                           ("a very long name", {"me": "Madison Rodriguez-Smith the Third of Many Names", "others": 0})):
            pg.evaluate(ROOM, spec); pg.wait_for_timeout(1300); r = pg.evaluate(ROWS)
            mine = [x for x in r["rows"] if x["mine"]]
            chk("(1) %s, %s: the name column fills the room up to the status (gap left over %s)" % (lab, what, [round(x["fill"] - x["gap"], 1) for x in r["rows"]]),
                r["rows"] and not r["crowded"] and all(abs(x["fill"] - x["gap"]) <= 2 for x in r["rows"]), r)
            chk("(2) %s, %s: the status sits at the row's right edge (%s)" % (lab, what, [round(x["edge"] - x["padR"], 1) for x in r["rows"]]),
                r["rows"] and all(abs(x["edge"] - x["padR"]) <= 2 for x in r["rows"]), r)
            if spec["me"] == "Madison":
                chk("(3) %s, %s: your name is whole and carries (You)" % (lab, what), mine and not mine[0]["cut"] and mine[0]["you"], mine)
            else:
                chk("(3) %s, %s: a long name is cut with an ellipsis where it does not fit (a phone), the status stays at the edge" % (lab, what), mine and (mine[0]["cut"] or W >= 600) and abs(mine[0]["edge"] - mine[0]["padR"]) <= 2, mine)
        pg.evaluate(ROOM, {"me": "Madison", "others": 7}); pg.wait_for_timeout(1300); c = pg.evaluate(ROWS)
        chk("(4) %s: a crowded room keeps its tight rows (not the grid), nothing scrolls sideways, no page errors" % lab,
            c["crowded"] and all(x["disp"] != "grid" for x in c["rows"]) and c["sw"] <= 0 and not errs, [c["crowded"], [x["disp"] for x in c["rows"]][:2], c["sw"], errs[:2]])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
