"""Build 384 r12: the display test panel has an auto test (one tap, screen-record the phone, each suspect alone for 5 seconds).
Madison's phone shows a soft band across the top of every screen that Chromium cannot reproduce; he will not tick switches one at a time.
With ?diag / class26e.displaytest on: the panel has a button; tapping it steps through "nothing off", "everything off at once" and each
suspect alone (one style element at a time, named in the panel), then clears every switch and says Done; no page errors.
Run:  python3 tools/check-b384-autotest.py   (--against OLD/index.html must FAIL)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, init="try{localStorage.setItem('class26e.displaytest','1')}catch(e){}")
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
    pg.reload(); pg.wait_for_timeout(3000)
    n_switch = pg.evaluate("()=>document.querySelectorAll('#diagpanel input[type=checkbox]').length")
    has = pg.evaluate("()=>!!document.querySelector('#diagpanel button')")
    chk("the panel has an auto-test button (%d switches)" % n_switch, has and n_switch > 5, [has, n_switch])
    if has:
        pg.evaluate("()=>document.querySelector('#diagpanel button').click()")
        steps = []
        for _ in range(45):
            pg.wait_for_timeout(2000)
            r = pg.evaluate("()=>[document.querySelector('#diagpanel div').textContent, [...document.querySelectorAll('style[id^=diag-]')].length]")
            if not steps or steps[-1] != r: steps.append(r)
            if r[0].startswith("Done"): break
        alone = [s for s in steps if s[0].startswith("Step") and s[1] == 1]
        chk("steps: nothing off, then everything off at once (%d styles), then each suspect alone (%d steps)" % (max([s[1] for s in steps] or [0]), len(alone)),
            any(s[1] == 0 and s[0].startswith("Step 1") for s in steps) and any(s[1] == n_switch for s in steps) and len(alone) == n_switch, steps)
        chk("it ends by clearing every switch and saying Done", steps and steps[-1][0].startswith("Done") and steps[-1][1] == 0, steps[-1:])
    chk("no page errors", not errs, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
