#!/usr/bin/env python3
"""Build 384.23 check: the sign-up is shorter, and still makes a whole account.

The owner, watching classmates: "The walkthrough is a lot. The sign up process is not easy, it's kinda difficult, long, not easy and even
confusing." Measured on 384.22, in the installed app (iPhone 17 Pro Max, a new account, Police Academy): 6 presses before Nova (Get Started,
I'm new here, New to Nova?, the class and its Continue, Enroll), then Nova's 23 boxes (the story of the voyage and the storm, the flares, the
badges, the crew, the four modes, each a tap) with the name, the partner and the sync code's card among them, then 8 tips and a ninth (Start
Studying): about 40 presses. 384.23 tells the story in nine boxes and the tips in four.

Read off the page, never typed: the walker (tools/b384_flow_lib.py) presses what a person presses and counts Nova's boxes from the page's own
__nova.count and the tips from the tour overlay. Asserted by shape:

 (1) a new account, walked from the first screen of the installed app to the last tip, takes at most BUDGET presses (the old flow's count
     is the page's own on --against, and is above it);
 (2) Nova's introduction is at most 10 boxes, the tips at most 5 (the four of mainMenuTourSteps(false) and Start Studying), and the
     number of tips that RENDERED equals the number the source declares plus the last one (no dead step);
 (3) nothing a person has to DO is gone: the account ends onboarded, with a sync code, the typed name and a partner, and the sync code's
     card was met on the way (the code is still offered at sign-up and kept in Settings, Sync);
 (4) a relaunch lands on Home, with no Nova and no tip;
 (5) an account that already exists, in the installed app and in a browser tab, sees none of it (no Nova, no tip, no install page, no
     Get Started) and ends on Home.

  python3 tools/check-b384-signupshort.py [--against OLD/index.html]     (must FAIL on 384.22: its walk is about 40 presses)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
SRC_PATH = args[args.index("--against") + 1] if "--against" in args else None
SRC = L.load_src(SRC_PATH)
BUDGET = 28
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)

srv, url = L.serve()
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME)
        ins = (62, 0, 34, 0)
        # ---- (1)-(4): a new account in the installed app
        ctx, pg = L.new_page(br, SRC, url, ua="iphone-safari", installed=True, insets=ins)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        L.boot(pg, url, 2500)
        declared = pg.evaluate("()=>mainMenuTourSteps(false).length")
        r = L.walk_signup(pg, "J.Smith", log=lambda s: None)
        print("  walk: %d presses, %d Nova boxes, %d tips, %d pages: %s" % (r["taps"], r["nova_boxes"], r["tips"], len(r["pages"]), " > ".join(r["pages"])), flush=True)
        chk("(1) a new account takes at most %d presses from the first screen to the last tip (%d)" % (BUDGET, r["taps"]), r["taps"] <= BUDGET, r)
        chk("(2) Nova's introduction is at most 10 boxes (%d)" % r["nova_boxes"], r["nova_boxes"] <= 10, r)
        chk("(2) the tips are at most 5, and every declared step rendered (declared %d + the last one, rendered %d)" % (declared, r["tips"]),
            r["tips"] <= 5 and r["tips"] == declared + 1, r)
        chk("(3) the account ends onboarded, with a sync code, the typed name and a partner", r["onboarded"] and r["code"] and r["name"] == "J.Smith" and r["avatar"], r)
        chk("(3) the sync code's card was on the way", "sync code card" in r["pages"], r["pages"])
        chk("(3) Settings still holds the code (Sync page builds a code row)", pg.evaluate("()=>typeof shownSyncCode==='function' && !!shownSyncCode()"), "")
        # a relaunch
        pg.reload(); pg.wait_for_timeout(2500)
        pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); if(s) s.remove(); }"); pg.wait_for_timeout(4000)
        st = pg.evaluate("()=>({ screen: (document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen||'', nova: !!document.getElementById('nova-intro'), tour: !!document.getElementById('tour-tooltip'), gs: !!document.querySelector('.gs-page') })")
        chk("(4) a relaunch lands on Home with no Nova and no tip", st["screen"] == "home" and not st["nova"] and not st["tour"] and not st["gs"], st)
        real = [e for e in errs if not any(k in e for k in ("firebase", "firestore", "gstatic", "Failed to fetch", "net::"))]
        chk("no page errors", not real, real[:2])
        ctx.close()
        # ---- (5): an existing account sees none of it
        for lab, inst, ua in (("installed", True, "iphone-safari"), ("a browser tab", False, "iphone-safari"), ("a browser tab on a computer", False, "win-chrome")):
            ctx, pg = L.new_page(br, SRC, url, ua=ua, installed=inst, seeded=True, insets=ins)
            L.boot(pg, url, 2500); pg.wait_for_timeout(6000)
            st = pg.evaluate("()=>({ screen: (document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen||'', nova: !!document.getElementById('nova-intro'), tour: !!document.getElementById('tour-tooltip'), gs: !!document.querySelector('.gs-page'), inst: !!document.querySelector('[data-screen=installfirst]') })")
            chk("(5) an existing account, %s: Home, with no Nova, no tip, no Get Started and no install page" % lab, st["screen"] == "home" and not (st["nova"] or st["tour"] or st["gs"] or st["inst"]), st)
            ctx.close()
        br.close()
finally:
    srv.shutdown()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
