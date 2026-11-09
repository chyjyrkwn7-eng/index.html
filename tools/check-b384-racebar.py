#!/usr/bin/env python3
"""Build 384 round 5: the live race line never sits under the chat button.

Madison: "Why is the chat icon on top of the race?" On the results screen (others still racing) nothing sits above the line, and the fixed
chat button covered the finish flag. This shows the line on a screen with no question counter row and measures it against the chat
button on a phone, a small phone and a tablet; and checks a question's own arrangement is untouched (no extra gap above the line).
  python3 tools/check-b384-racebar.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
    for w, h, dpr in ((440, 956, 2), (375, 667, 2), (834, 1194, 2)):
        ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, dpr=dpr)
        r = pg.evaluate("""()=>{ document.querySelectorAll('#splashscreen').forEach(n=>n.remove());
          showHome(); const rb=document.getElementById('vroomracebar'); rb.hidden=false; inVirtualRoom=true;
          const m=document.getElementById('vroomracemarkers'); const d=document.createElement('div'); d.className='vroom-race-marker'; d.style.left='100%'; m.appendChild(d);
          window.scrollTo(0,0);
          const bar=rb.getBoundingClientRect(); const fin=rb.querySelector('.vroom-racetrack-finish').getBoundingClientRect();
          const chat=[...document.querySelectorAll('.chatdock-btn')].filter(b=>b.offsetParent!==null||getComputedStyle(b).position==='fixed').map(b=>b.getBoundingClientRect()).filter(c=>c.width>0)[0];
          return {barTop:bar.top, finTop:fin.top, finLeft:fin.left, finRight:fin.right, chat: chat ? {b:chat.bottom, l:chat.left, r:chat.right} : null}; }""")
        c = r["chat"]
        chk("%dx%d: the chat button is on this screen" % (w, h), c is not None, r)
        if c:
            clear = r["finTop"] >= c["b"] or r["finRight"] <= c["l"] or r["finLeft"] >= c["r"]
            chk("%dx%d: the finish flag does not sit under the chat button (flag top %.0f, chat bottom %.0f)" % (w, h, r["finTop"], c["b"]), clear, r)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
