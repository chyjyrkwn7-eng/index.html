#!/usr/bin/env python3
"""Build 384 r8: a pop-up is frosted glass on every screen; the person card's numbers have room under them.
Madison, a classmate's card from the Leaderboard beside one from Home: "do you see how the stuff isn't frosted glass like the bo
screenshot? I like the frosted look, ensure it's there. Secondly, the letters 'xp' are pretty dang close to the number."
iPhone 17 Pro Max: (1) the person card opened on Home, the Leaderboard, Profile and the Virtual Room choice screen is see-through
(its fill's alpha under .7) with a backdrop blur; (2) the clean look still holds inside the page - Profile's own card beyond Home
is the solid card colour (no blur); (3) the big XP label sits at least 6px under its number, the small ones at least 4px;
(4) no page errors.
  python3 tools/check-b384-popfrost.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
ENTRY = "{ name:'Levni', pub:'abcxyz123456', level:60, badges:7, points:144000, hundos:78, correct:10563, avatarChar:'hacker', accent:'adept' }"
M = """()=>{ const s=document.querySelector('.invite-sheet.person-card'); if(!s) return null; const cs=getComputedStyle(s);
  const a = (c => { const m = /rgba?\\(([^)]+)\\)/.exec(c); if(m){ const p=m[1].split(',').map(Number); return p.length>3 ? p[3] : 1; } const n=/\\/\\s*([\\d.]+)\\s*\\)/.exec(c); return n ? +n[1] : 1; })(cs.backgroundColor);
  const cells=[...s.querySelectorAll('.person-card-cell')].map(c=>{ const v=c.querySelector('.person-card-cell-value'), l=c.querySelector('.person-card-cell-label'); return l.getBoundingClientRect().top - v.getBoundingClientRect().bottom; });
  return { alpha:a, blur:/blur\\(/.test(cs.backdropFilter||cs.webkitBackdropFilter||''), cells }; }"""
SCREENS = [("Home", "showHome()"), ("Leaderboard", "showRankings()"), ("Profile", "showProfile('profile')"), ("Virtual Room", "window.vroomDb = window.vroomDb || (()=>({})); showVirtualRoomChoice()")]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    for lab, go in SCREENS:
        pg.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(n=>n.remove()); %s; }" % go); pg.wait_for_timeout(1100)
        pg.evaluate("()=>{ openPersonSheet(%s); }" % ENTRY); pg.wait_for_timeout(900)
        m = pg.evaluate(M)
        chk("(1) %s: the person card is frosted glass (fill alpha %s, blur %s)" % (lab, m and round(m["alpha"], 2), m and m["blur"]), m and m["alpha"] < .7 and m["blur"], m)
        if lab == "Leaderboard":
            chk("(3) the big XP label sits 6px+ under its number, the others 4px+ (%s)" % [round(x, 1) for x in m["cells"]],
                m["cells"] and m["cells"][0] >= 6 and all(x >= 4 for x in m["cells"][1:]), m["cells"])
    pg.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(n=>n.remove()); showProfile('profile'); }"); pg.wait_for_timeout(1200)
    p = pg.evaluate("""()=>{ const c=document.querySelector('#stage .profile-identity-tab > .pf-goal, #stage .pf-standing, #stage .profile-card'); if(!c) return null; const cs=getComputedStyle(c);
      return { bg: cs.backgroundColor, bf: cs.backdropFilter||'none', sky: document.body.classList.contains('sky-home') }; }""")
    chk("(2) the clean look holds in the page: Profile's own card is solid, no blur (%s)" % p, p and not p["sky"] and "blur" not in p["bf"], p)
    chk("(4) no page errors", not errs, errs[:3])
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
