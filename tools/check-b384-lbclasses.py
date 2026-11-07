#!/usr/bin/env python3
"""Build 384 review: the leaderboard belongs to the Police Academy; Fire Code has none, and Settings say so.

Madison: "The leaderboard should not be available for Fire Code. Ensure the settings match up with that and it makes sense how it's
described. Maybe in leaderboard settings it shows each class." So:
(1) in Fire Code (enrolled in both): no Leaderboard bottom tab, no switch anywhere - and Settings has a read-only Leaderboard & Privacy
    row ("Police Academy only") whose page lists each class: Police Academy shown/hidden, Fire Code "No leaderboard";
(2) in the academy, enrolled in both: the switch is there, its hint names the Police Academy, and the page lists each class too;
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
    page = { text: (document.querySelector('#stage')||{}).innerText, classes: [...document.querySelectorAll('#stage .settings-lb-class')].map(r => (r.querySelector('.settings-row-label')||{}).textContent + '=' + (r.querySelector('.settings-row-value')||{}).textContent),
             hint: (document.querySelector('#stage .ohint')||{}).textContent || null, sw: !!document.querySelector('#stage input[type=checkbox]') }; }
  return { cls: window.NOVA_CLASS, tab: [...document.querySelectorAll('.bottomtabs .bottomtab')].filter(b => b.id === 'bottomtab-rewards').map(b => b.hidden || !b.getBoundingClientRect().width), menu, page }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"])); pg.wait_for_timeout(1200)
    r = pg.evaluate(READ, None); errs_all += errs; ctx.close()
    chk("(1) Fire Code: no Leaderboard tab on the bar (%s), a read-only row 'Police Academy only' (%s), and no switch" % (r["tab"], r["menu"]),
        r["cls"] == "ifc" and all(r["tab"]) and r["menu"] and r["menu"]["value"] == "Police Academy only" and r["page"] and not r["page"]["sw"], r)
    chk("(1) ...its page lists each class: the Police Academy shown or hidden, Fire Code 'No leaderboard' (%s)" % (r["page"] and r["page"]["classes"]),
        r["page"] and len(r["page"]["classes"]) == 2 and r["page"]["classes"][0].startswith("Police Academy=") and r["page"]["classes"][0].split("=")[1] in ("Shown", "Hidden")
        and r["page"]["classes"][1] == "Fire Code=No leaderboard", r)
    for two in (True, False):
        ctx, pg, errs = G["page"](br, G["init"](G["academy"], active="academy")); pg.wait_for_timeout(1200)
        r = pg.evaluate(READ, two); errs_all += errs; ctx.close()
        if two:
            chk("(2) the academy, in both classes: the switch is there, its hint names the Police Academy, and the page lists both classes (%s)" % (r["page"] and r["page"]["classes"]),
                r["page"] and r["page"]["sw"] and "Police Academy" in (r["page"]["hint"] or "") and len(r["page"]["classes"]) == 2 and r["page"]["classes"][1] == "Fire Code=No leaderboard", r)
        else:
            chk("(3) the academy, in one class: no class list, the hint as it was",
                r["page"] and r["page"]["sw"] and not r["page"]["classes"] and "Police Academy" not in (r["page"]["hint"] or ""), r)
    chk("no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
