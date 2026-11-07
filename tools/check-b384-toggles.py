#!/usr/bin/env python3
"""Build 384 round 5: one toggle look. The Profile / Stats / Settings switch and the Leaderboard's tabs carry the same picked-segment
look as Stats' This week / Last week switch (an accent-tinted pill with its own ring), not a grey pill.

Madison: "the touch look and toggles ... the entire app needs to be cohesive". Reads the computed fill and ring of the picked segment on
each and compares them with the Stats week switch's; shape is read off the page, no colour is typed here.
  python3 tools/check-b384-toggles.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=2)
    pg.evaluate("document.querySelectorAll('#splashscreen').forEach(n=>n.remove())")
    pg.evaluate("showProfile('stats')"); pg.wait_for_timeout(1500)
    ref = pg.evaluate("()=>{ const b=document.querySelector('.stx-dots-switch button[aria-selected=true]'); const c=getComputedStyle(b); return {bg:c.backgroundColor, ring:c.boxShadow, fg:c.color}; }")
    got = pg.evaluate("""()=>{ const sl=document.querySelector('.screen-profile > .navsegment.profiletabs > .seg-slider'); const a=document.querySelector('.screen-profile > .navsegment.profiletabs > .iconbtn.active');
      const cs=getComputedStyle(sl), ca=getComputedStyle(a); return {bg:cs.backgroundColor, ring:cs.boxShadow, fg:ca.color, rad:cs.borderRadius}; }""")
    chk("Profile's switch: the picked pill is the Stats switch's fill", got["bg"] == ref["bg"], (got, ref))
    chk("...with the same ring", got["ring"] == ref["ring"], (got, ref))
    chk("...and the same text colour", got["fg"] == ref["fg"], (got, ref))
    pg.evaluate("showRankings('overall')"); pg.wait_for_timeout(1500)
    got2 = pg.evaluate("""()=>{ const sl=document.querySelector('.screen-rankings > .navsegment.profiletabs > .seg-slider'); const cs=getComputedStyle(sl); return {bg:cs.backgroundColor, ring:cs.boxShadow}; }""")
    chk("Leaderboard's tabs: the same fill and ring", got2["bg"] == ref["bg"] and got2["ring"] == ref["ring"], (got2, ref))
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
