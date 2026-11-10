#!/usr/bin/env python3
"""Build 384.20: NO WEEKLY NOVA POP-UP IN FIRE CODE.
Madison: "Why did nova pop up for a weekly thing in the fire code class? Remove that."
The Fire Code class has no weekly board, but maybeShowWeekRecap still played a stripped-down "Nova's weekly recap" there (and Nova's
weekly challenge message was still allowed). Read off the page, on a Wednesday (the recap's day is Tuesday to Sunday), in each class:
 (1) FIRE CODE: Home is up, the recap is asked for (maybeShowWeekRecap) and given ten seconds: no .nova-talk / #nova-intro appears, and nothing
     is marked seen (class26e.weekrecap.v1 stays empty).
 (2) FIRE CODE: Nova owes no recap today (novaRecapOwedToday on a Tuesday is false) and no week of the next twelve carries a weekly challenge
     (novaPending(...).weekly is null for every one).
 (3) THE ACADEMY is untouched: on the same week at least one of the twelve weeks does carry a weekly challenge, and the Tuesday recap is still owed.
 (4) no page errors.
Run:  python3 tools/check-b384-ifcweekly.py [--against OLD/index.html]   (must FAIL on 384.19)"""
import json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
BODY = open(args[args.index("--against") + 1], encoding="utf-8").read() if "--against" in args else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)

def seed_for(cls):
    seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4weekly01", classes=["academy", "ifc"])
    S = json.dumps(json.dumps(seed))
    base = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);") % S
    if cls == "ifc":
        return base + ("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
            "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
            "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % S
    return base + "localStorage.setItem('class26e.activeclass','academy');localStorage.setItem('class26e.enrolled',JSON.stringify(['academy']));}catch(e){}"

WED = datetime.datetime(2026, 11, 11, 10, 0, 0)     # a Wednesday: inside the recap's Tuesday to Sunday
srv, PORT = rc["serve"]()
try:
  with sync_playwright() as pw:
    for cls in ("ifc", "academy"):
        br = pw.chromium.launch(executable_path=rc["CHROME"])
        ctx = br.new_context(viewport={"width": 440, "height": 956})
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        if BODY is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.clock.install(time=WED)
        pg.add_init_script(seed_for(cls))
        pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.clock.run_for(3000); pg.wait_for_timeout(1500)
        pg.evaluate("() => document.getElementById('splashscreen')?.remove()")
        cl = pg.evaluate("() => window.NOVA_CLASS")
        chk("%s: the page is in that class (%s)" % (cls, cl), cl == cls, cl)
        if cls == "ifc":
            # a launch that is not a sign-in (the recap is for somebody already here), with no sync code to wait on, and nothing else on screen
            # (a seeded account's own Home unlocks would otherwise hold it back, and then nothing could be measured)
            pg.evaluate("() => { try{ accountArrivedThisLaunch = false; weekRecapBlocked = () => false; store.prevWeekStats = { k: lastWeekKey(), t: 4, h: 1 }; }catch(e){} showHome(); maybeShowWeekRecap(0); }")
            for _ in range(10):
                pg.clock.run_for(1000); pg.wait_for_timeout(120)
            seen = pg.evaluate("() => !!document.querySelector('.nova-talk, #nova-intro')")
            mark = pg.evaluate("() => { try{ const r = weekRecapRecord(); return r ? JSON.stringify(r) : ''; }catch(e){ return 'err:' + e.message; } }")
            chk("(1) ifc: the weekly recap does not pop up on Home (nothing .nova-talk)", not seen, seen)
            chk("(1) ifc: nothing is marked as seen (%r)" % mark, not mark, mark)
        tue = int(datetime.datetime(2026, 11, 10, 12).timestamp() * 1000)
        owed = pg.evaluate("(t) => novaRecapOwedToday(t)", tue)
        weeks = pg.evaluate("""(t0) => { const out = []; const heard = {}; for(let i = 0; i < 12; i++){ const now = t0 + i * 7 * 864e5 + 3 * 864e5;
            try{ out.push(!!novaPending(heard, now).weekly); }catch(e){ out.push('err:' + e.message); } } return out; }""", tue)
        if cls == "ifc":
            chk("(2) ifc: no recap is owed on a Tuesday (%s)" % owed, owed is False, owed)
            chk("(2) ifc: none of the next twelve weeks carries a weekly challenge (%s)" % weeks, not any(weeks), weeks)
        else:
            chk("(3) academy: the Tuesday recap is still owed when unseen (%s)" % owed, owed is True, owed)
            chk("(3) academy: some week of twelve still carries a weekly challenge (%s)" % weeks, any(w is True for w in weeks), weeks)
        chk("(4) %s: no page errors" % cls, not errs, errs[:2])
        ctx.close(); br.close()
finally:
    try: srv.shutdown()
    except Exception: pass
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
