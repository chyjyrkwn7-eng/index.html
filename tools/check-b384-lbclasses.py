#!/usr/bin/env python3
"""Build 385: every class has a leaderboard of its own, and Settings says which is shown and which is hidden.

(384 review had said: "The leaderboard should not be available for Fire Code ... Maybe in leaderboard settings it shows each class."
385 reverses the first half - Madison: "fire code is gonna get the leaderboard ... every class will have their own leaderboard" - and keeps
the second: Settings lists each class.) So:
(1) in Fire Code (enrolled in both): a Leaderboard tab on the bar, a real Leaderboard & Privacy row (Shown or Hidden, its own switch) whose
    page has the switch, a hint that names Fire Code, and lists each class: Police Academy and Fire Code, each Shown or Hidden;
(2) in the academy, enrolled in both: the switch is there, its hint explains the per-class switches below it (385 r17: one switch a class, check-b384-privacy), and the page lists each class too - Fire
    Code's as it is in its own copy (Shown, or Hidden once it is hidden there);
(3) in the academy, enrolled in one: no class list, the hint is as it was.
  python3 tools/check-b384-lbclasses.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384lb"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
READ = """async (two)=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); document.getElementById('splashscreen')?.remove();
  if(two !== null){ const real = enrolledClasses; enrolledClasses = () => two ? ['academy','ifc'] : ['academy']; }
  showAppearance(); await w(900);
  const row = document.getElementById('settings-row-rankings');
  const menu = row ? { value: (row.querySelector('.settings-row-value')||{}).textContent } : null;
  let page = null;
  if(row){ row.click(); await w(900);
    page = { text: (document.querySelector('#stage')||{}).innerText, classes: [...document.querySelectorAll('#stage .settings-lb-class')].map(r => (r.querySelector('.otext').firstChild.textContent) + '=' + (r.querySelector('input').checked ? 'Shown' : 'Hidden')),
             hint: (document.querySelector('#stage .ohint')||{}).textContent || null, sw: !!document.querySelector('#stage input[type=checkbox]') }; }
  return { cls: window.NOVA_CLASS, tab: [...document.querySelectorAll('.bottomtabs .bottomtab')].filter(b => b.id === 'bottomtab-rewards').map(b => b.hidden || !b.getBoundingClientRect().width), menu, page }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"])); pg.wait_for_timeout(1200)
    r = pg.evaluate(READ, None); errs_all += errs; ctx.close()
    chk("(1) Fire Code: a Leaderboard tab on the bar (%s), a Leaderboard & Privacy row that is Shown or Hidden (%s), and its own switch" % (r["tab"], r["menu"]),
        r["cls"] == "ifc" and not any(r["tab"]) and len(r["tab"]) == 1 and r["menu"] and r["menu"]["value"] in ("Shown", "Hidden") and r["page"] and r["page"]["sw"], r)
    chk("(1) ...its page names Fire Code, and lists each class: the Police Academy and Fire Code, each shown or hidden (%s)" % (r["page"] and r["page"]["classes"]),
        r["page"] and "below" in (r["page"]["hint"] or "") and len(r["page"]["classes"]) == 2 and r["page"]["classes"][0].startswith("Police Academy=")
        and r["page"]["classes"][1].startswith("Fire Code=") and all(c.split("=")[1] in ("Shown", "Hidden") for c in r["page"]["classes"]), r)
    for two in (True, False):
        ctx, pg, errs = G["page"](br, G["init"](G["academy"], active="academy")); pg.wait_for_timeout(1200)
        r = pg.evaluate(READ, two); errs_all += errs; ctx.close()
        if two:
            chk("(2) the academy, in both classes: the switch is there, its hint names the Police Academy, and the page lists both classes (%s)" % (r["page"] and r["page"]["classes"]),
                r["page"] and r["page"]["sw"] and "below" in (r["page"]["hint"] or "") and len(r["page"]["classes"]) == 2
                and r["page"]["classes"][1].startswith("Fire Code=") and r["page"]["classes"][1].split("=")[1] in ("Shown", "Hidden"), r)
        else:
            chk("(3) the academy, in one class: no class list, the hint as it was",
                r["page"] and r["page"]["sw"] and not r["page"]["classes"] and "Police Academy" not in (r["page"]["hint"] or ""), r)
    # (2b) the academy lists Fire Code as Hidden once its own copy has the switch off
    ctx, pg, errs = G["page"](br, G["init"](G["academy"], active="academy") + ";(()=>{ try{ var c = JSON.parse(localStorage.getItem('class26e.drill.v1')); c.leaderboardOptIn = false; localStorage.setItem('class26e.ifc.drill.v1', JSON.stringify(c)); }catch(e){} })();"); pg.wait_for_timeout(1200)
    r = pg.evaluate(READ, True); errs_all += errs; ctx.close()
    chk("(2b) the academy lists Fire Code as Hidden when it is hidden in Fire Code's own copy (%s)" % (r["page"] and r["page"]["classes"]),
        r["page"] and len(r["page"]["classes"]) == 2 and r["page"]["classes"][1] == "Fire Code=Hidden", r)
    chk("no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
