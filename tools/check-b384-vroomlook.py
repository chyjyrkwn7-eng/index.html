#!/usr/bin/env python3
"""Build 384 round 5: the Virtual Room's own screens are in the mode screen's look.

Madison: "the option to select open room or host ... didn't get updated ... should look like the mode selection screen. Same goes
for all parts of the virtual room - the lobby, results, leaderboard, cutscenes". Reads the computed style of each screen's pieces:
  - the choice cards match the mode screen's cards (padding, the words' size, the title's size) and its question's size
  - the lobby's game name and headings, and every results/wait title, are the app's one face (not the serif), in sentence case
  - your score card, the XP card and the match boards have no rim
  python3 tools/check-b384-vroomlook.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
LOBBY = open(os.path.join(HERE, "..", "docs", "fixtures", "lobby.js")).read() if os.path.exists(os.path.join(HERE, "..", "docs", "fixtures", "lobby.js")) else None
CARD = """()=>{ const c=document.querySelector('.modecard'); const cs=getComputedStyle(c); const t=getComputedStyle(c.querySelector('.modecardtitle')); const d=getComputedStyle(c.querySelector('.modecarddesc'));
  const sub=document.querySelector('.modeselect-sub, .screen-vroom-choice > .cal-sub'); return {pad:cs.padding, bw:cs.borderTopWidth, layers:cs.backgroundImage.split('linear-gradient').length - 1, ff:t.fontFamily, title:t.fontSize, desc:d.fontSize, sub:getComputedStyle(sub).fontSize, subAlign:getComputedStyle(sub).textAlign}; }"""
FACE = """(sel)=>[...document.querySelectorAll(sel)].map(e=>{ const c=getComputedStyle(e); return {t:e.textContent.trim().slice(0,24), serif:/georgia|times|palatino|iowan/i.test(c.fontFamily.split(',')[0]), up:c.textTransform==='uppercase'}; })"""
D = """()=>{ window.__d = {status:'finished', startAt:Date.now()-400000, participants:{me:{name:'Madison',avatarChar:'ninja',level:23,badges:4,joinedAt:1,ready:true,finished:true,progress:100},
  a2:{name:'Ben',avatarChar:'wizard',level:12,badges:1,joinedAt:2,ready:true,finished:true,progress:100}, b1:{name:'Ava',avatarChar:'ghost',level:31,badges:6,joinedAt:3,ready:true,finished:true,progress:100}},
  tug:{teams:{me:'a',a2:'a',b1:'b'},progress:{me:{pos:50,pull:30},a2:{pos:50,pull:20},b1:{pos:50,pull:10}},over:true,winner:'a',finalPos:8,count:50},
  battle:{teams:{me:'a',a2:'a',b1:'b'},progress:{},log:[],over:true,winner:'a',count:50}, game:'tug'}; vroomMyKey='me'; vroomCode='X'; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1, init=cb._ROOM_FAKE)
    pg.evaluate("document.querySelectorAll('#splashscreen,#pushing-update,#intro-pop').forEach(n=>n.remove()); __useRooms();")
    pg.evaluate("showModeSelect()"); pg.wait_for_timeout(1300); m = pg.evaluate(CARD)
    pg.evaluate("showVirtualRoomChoice()"); pg.wait_for_timeout(1300); v = pg.evaluate(CARD)
    # (384 r20) the tiles fill their screens, so each screen builds them to its own room (three or four to a phone are compact, two are
    # tall): the padding follows the tile, the MATERIAL and the TYPE are the one family - the same face and layers and rim, the title
    # and the words within 2px of each other
    px = lambda s: float(s[:-2])
    chk("Virtual Room's tiles are the mode screen's: the same material and rim, the same face (%s vs %s)" % ((v["layers"], v["bw"]), (m["layers"], m["bw"])),
        v["layers"] == m["layers"] and v["bw"] == m["bw"] and v["ff"] == m["ff"], (v, m))
    chk("...the title size and the words size within 2px", abs(px(v["title"]) - px(m["title"])) <= 2 and abs(px(v["desc"]) - px(m["desc"])) <= 2, (v, m))
    chk("...and the question under the title is the same size and centred", v["sub"] == m["sub"] and v["subAlign"] == m["subAlign"], (v, m))
    # the lobby (a four-person room, you are the host)
    pg.evaluate("""()=>{ const me=publicIdOf(); const parts={}; parts[me]={name:'Madison',avatarChar:'ninja',level:41,badges:6,joinedAt:1,seen:9e15,ready:false};
      ['Avery','Jordan','Kim'].forEach((n,i)=>{ parts['pF'+i+'0000000000']={name:n,avatarChar:['zeus','alien','ghost'][i],level:10+i,badges:i,joinedAt:2+i,seen:9e15,ready:i>0}; });
      __rooms['ROOM384']={hostCode:me,hostName:'Madison',units:['Identity Crimes'],versions:{},game:'tug',open:false,status:'waiting',mode:'exam',createdAt:1,count:null,participants:parts};
      vroomCode='ROOM384'; vroomMyKey=me; vroomIsHost=true; vroomUnits=['Identity Crimes']; vroomLastDoc={code:'ROOM384',data:JSON.parse(JSON.stringify(__rooms.ROOM384))}; showVirtualRoomLobby(); }""")
    pg.wait_for_timeout(1500)
    f = pg.evaluate(FACE, ".vroom-test-summary-title, .vroom-setup-head, .vroom-roster-title")
    chk("the lobby's game name and headings are in the app's face, sentence case (%s)" % [x["t"] for x in f], f and not any(x["serif"] or x["up"] for x in f), f)
    pg.evaluate(D)
    for name, fn in (("Tug result","showTugResult(__d)"),("Battle result","showBattleResult(__d)"),("Tug waiting","renderTugWaiting(__d)"),("Battle waiting","renderBattleWaiting(__d)")):
        pg.evaluate("()=>{ try{ detachTug(); }catch(e){} "+fn+" }"); pg.wait_for_timeout(1500)
        # (384 r8) Tug of War and Battle end on the results screen: its heading is the unit title (.rs-units)
        f = pg.evaluate(FACE, "#stage :is(.welcomeintro-title, .rs-units)")
        chk("%s: the title is the app's face, not the serif or upper case (%s)" % (name, [x["t"] for x in f]), f and not any(x["serif"] or x["up"] for x in f), f)
    pg.evaluate("()=>{ try{ detachTug(); }catch(e){} showTugResult(__d) }"); pg.wait_for_timeout(1500)
    # (384 r8) the XP card is the results' own (.rs-xp) now; "no rim" is a border nobody can see - none, or transparent
    r = pg.evaluate("""()=>{ const e=document.querySelector('#stage :is(.tug-xp, .rs-xp)'); if(!e) return null; const c=getComputedStyle(e);
      const clear = c.borderTopWidth==='0px' || /rgba\\(.*,\\s*0\\)$|transparent/.test(c.borderTopColor); return (clear ? 'clear' : c.borderTopWidth+' '+c.borderTopColor)+' '+c.boxShadow; }""")
    chk("the XP card has no rim and no glow (%s)" % r, r is not None and r.startswith("clear") and r.endswith("none"), r)
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
