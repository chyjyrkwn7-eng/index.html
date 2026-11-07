#!/usr/bin/env python3
"""Build 384 round 5: people the board cannot tell apart share a place, and a row with nothing scored is not placed.

Six classmates on 360 XP were 1st to 6th by the alphabet. This opens the real This Week, Overall and Hundos boards on a fixture
with ties and with zeros and reads the place printed on each row.
  python3 tools/check-b384-ties.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
READ = """()=>[...document.querySelectorAll('.rank-row:not(.rank-row-head)')].map(r=>({p:(r.querySelector('.rank-place')||{}).innerText||'', n:(r.querySelector('.rank-name, .lb-name')||{}).innerText||r.innerText.split('\\n')[1]||''}))"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    pg.evaluate("document.querySelectorAll('#splashscreen').forEach(n=>n.remove())")
    pg.evaluate("""()=>{ const ids=['ninja','wizard','ghost','grizzly']; const w=weekKeyNow();
      const spec=[['Ann',300,5],['Bo',300,5],['Cy',300,5],['Di',200,3],['Ed',200,3],['Flo',100,1],['Gil',0,0],['Hal',0,0]];
      leaderboardRows = spec.map((s,i)=>Object.assign({pub:'t'+i+'0000000000', firstName:s[0], avatarChar:ids[i%4], level:10+i, badges:i%3, correct:100, lastModified:Date.now(), week:w, weekPoints:s[1], hundos:s[2]}));
      store.leaderboardOptIn = true; showRankings('week'); }""")
    pg.wait_for_timeout(1500)
    for key, tab in (("week", 0), ("hundos", 2)):
        pg.evaluate("(i)=>document.querySelectorAll('.screen-rankings .navsegment .iconbtn')[i].click()", tab); pg.wait_for_timeout(900)
        rows = [r for r in pg.evaluate(READ) if r["n"] in ("Ann","Bo","Cy","Di","Ed","Flo","Gil","Hal")]
        by = {r["n"]: r["p"].replace("#", "").strip() for r in rows}
        n = lambda k: int(by[k]) if by.get(k, "").isdigit() else None
        base = n("Ann")   # the account's own row can sit above them, so places are read relative to the first of them
        chk("%s: three people on the same number share a place" % key, base is not None and n("Bo") == base and n("Cy") == base, by)
        chk("%s: the two on the next number share the next place, three further down (not each their own)" % key, n("Di") == n("Ed") and n("Di") == base + 3, by)
        chk("%s: the one after them is two further down" % key, n("Flo") == base + 5, by)
        chk("%s: nothing scored is not placed (no medal, no number)" % key, by.get("Gil") not in ("1","2","3","7","8") and not any(ch.isdigit() for ch in by.get("Gil","1")), by)
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
