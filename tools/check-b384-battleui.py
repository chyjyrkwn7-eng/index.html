#!/usr/bin/env python3
"""Build 384 round 5: Battle's VS sits dead centre in its pill, and powers are on offer from the first question.

Madison: "The letters VS isn't centered. Powers should probably unlock from the beginning and not till 10 questions."
  python3 tools/check-b384-battleui.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for w, h, dpr in ((440, 956, 3), (834, 1194, 2), (375, 667, 2)):
        ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, dpr=dpr)
        r = pg.evaluate("""()=>{
          document.querySelectorAll('#splashscreen').forEach(n=>n.remove());
          const d = {participants:{a1:{name:'You',char:'ninja'},a2:{name:'Ben',char:'wizard'},b1:{name:'Ava',char:'wizard'},b2:{name:'Cy',char:'ghost'}}, battle:{teams:{a1:'a',a2:'a',b1:'b',b2:'b'},progress:{}}};
          vroomMyKey = 'a1';
          const st = document.getElementById('stage'); st.replaceChildren();
          const host = document.createElement('section'); host.className = 'panel screen-battle'; st.appendChild(host);
          host.appendChild(buildBattleBoard(d));
          const pw_ = document.createElement('div'); pw_.className = 'battle-power'; host.appendChild(pw_);
          const vs = document.querySelector('.battle-vs'); const b = vs.getBoundingClientRect();
          const rg = document.createRange(); rg.selectNodeContents(vs); const t = rg.getBoundingClientRect();
          battleHeld = null; battlePos = 1; battleRightSinceGrant = 0; battleLastData = d;
          battlePaintPower(d);
          return {w:b.width, h:b.height, dx:(t.left+t.width/2)-(b.left+b.width/2), dy:(t.top+t.height/2)-(b.top+b.height/2), hint:(document.querySelector('.battle-power-hint')||{}).innerText||''};
        }""")
        chk("%dx%d: VS pill is round (width %.1f, height %.1f)" % (w, h, r["w"], r["h"]), abs(r["w"] - r["h"]) < 0.6, r)
        chk("%dx%d: VS letters centred horizontally (off by %.2fpx)" % (w, h, r["dx"]), abs(r["dx"]) <= 0.6, r)
        chk("%dx%d: after one question the power hint counts right answers, not a wait for question ten" % (w, h), r["hint"] and "unlock" not in r["hint"].lower(), r["hint"])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
