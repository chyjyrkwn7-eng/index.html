#!/usr/bin/env python3
"""Build 384 r8: the Tug of War and Battle "You're done" screens say one thing and show your result.
Madison (the Tug of War wait): "This is a confusing screenshot, says I'm almost done but it also says I'm finished, and where is the rest
of the stuff".
iPhone 17 Pro Max, a three-person room, you finished on 42 of 50 (Tug) / 31 of 50 (Battle): (1) no Pause once you are done; (2) your
own score is on it - the percentage and "N of M right"; (3) Tug: the line under the rope describes the rope (no instruction to pull,
for a lead, a lead near the line, the other side's lead and a level rope); (4) the column is centred (room above within 80px of room
below); (5) no page errors.
  python3 tools/check-b384-tugwait.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
D = open(os.path.join(HERE, "check-b384-vroomlook.py")).read().split('\nD = """')[1].split('"""')[0]
M = """(sel)=>{ const p=document.querySelector(sel); if(!p) return null; const vis=[...p.children].filter(c=>c.getBoundingClientRect().height>0);
  const top=Math.min(...vis.map(c=>c.getBoundingClientRect().top)), bot=Math.max(...vis.map(c=>c.getBoundingClientRect().bottom));
  return { pause: document.getElementById('pausebtn').hidden, txt: p.textContent, state: (p.querySelector('.tug-state')||{}).textContent || '', above: top, below: innerHeight - bot }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1, init=cb._ROOM_FAKE)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.evaluate("document.querySelectorAll('#splashscreen,#pushing-update,#intro-pop').forEach(n=>n.remove()); __useRooms();")
    pg.evaluate(D)
    states = []
    for lab, a, b, c in (("your lead, near the line", 40, 30, 0), ("your lead", 6, 6, 5), ("their lead, near the line", 0, 0, 40), ("level", 10, 10, 10)):
        pg.evaluate("""([a, b, c]) => { __d.tug.over=false; __d.tug.progress.me.pull=a; __d.tug.progress.a2.pull=b; __d.tug.progress.b1.pull=c;
          tugCount=50; tugMyCorrect=42; document.querySelector('.screen-tug-wait')?.remove(); try{ detachTug(); }catch(e){} renderTugWaiting(__d); }""", [a, b, c]); pg.wait_for_timeout(900)
        m = pg.evaluate(M, ".screen-tug-wait"); states.append((lab, m and m["state"]))
        if lab == "your lead, near the line":
            chk("(1) Tug: no Pause once you are done", m and m["pause"] is True, m and m["pause"])
            chk("(2) Tug: your score is on it (84%, 42 of 50 right)", m and "84" in m["txt"] and "42 of 50" in m["txt"], m and m["txt"][:120])
            chk("(4) Tug: centred (above %.0f, below %.0f)" % (m["above"], m["below"]), abs(m["above"] - m["below"]) <= 80, m)
    bad = [(l, t) for l, t in states if not t or re.search(r"\b(keep pulling|pull it back|pull)\b", t, re.I) and re.search(r"\b(keep|back)\b", t, re.I)]
    chk("(3) Tug: the line under the rope describes it, never tells you to pull (%s)" % states, not bad and len({t for _, t in states}) >= 3, bad or states)
    pg.evaluate("()=>{ battleCount=50; battleCorrect=31; try{ detachTug(); }catch(e){} renderBattleWaiting(__d); }"); pg.wait_for_timeout(1200)
    m = pg.evaluate(M, ".screen-battle-wait")
    chk("(1) Battle: no Pause once you are done", m and m["pause"] is True, m and m["pause"])
    chk("(2) Battle: your score is on it (62%, 31 of 50 right)", m and "62" in m["txt"] and "31 of 50" in m["txt"], m and m["txt"][:120])
    chk("(4) Battle: centred (above %.0f, below %.0f)" % (m["above"], m["below"]), abs(m["above"] - m["below"]) <= 80, m)
    chk("(5) no page errors", not errs, errs[:3])
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
