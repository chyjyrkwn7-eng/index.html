#!/usr/bin/env python3
"""Build 384.27: Test #9 (Monday Nov 16, 2026) is on the calendar with its subjects, and the next test hands over to it at 8 PM on Monday Nov 9.
Madison, with the instructor's email: "Up the test stuff. Next test." The email: "Test #9 will cover the following subjects. Arrest, Search, and Seizure, CCP, and
Consular Notifications." Read off the page (Chicago time, CST):
 (1) testTopicsFor('2026-11-16') has the three subjects and the title Test #9, written as the units' own names;
 (2) at 7:59 PM on Monday Nov 9 the next test is still Nov 9's (Test #8); from 8 PM it is Nov 16's, and the units it marks are exactly Arrest, Search, and Seizure,
     Code of Criminal Procedure and Bill of Rights and Consular Notification (each a unit that exists);
 (3) the Fire Code class has no test calendar: nothing is posted there.
Run:  python3 tools/check-b384-test9.py   (--against OLD/index.html must FAIL)"""
import os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
BODY = open(args[args.index("--against") + 1], encoding="utf-8").read() if "--against" in args else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
NT = "() => { try{ const u = nextTestUnits(); const t = testTopicsFor('2026-11-16'); return { d: u && u.date, u: u ? [...u.units].sort() : null, t: t && t.topics, title: t && t.title }; }catch(e){ return { err: String(e).slice(0, 80) }; } }"
srv, PORT = rc["serve"]()
try:
  with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    def at(when, ifc=False):
        c = br.new_context(viewport={"width": 393, "height": 852}, timezone_id="America/Chicago"); p = c.new_page()
        if BODY is not None: p.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        p.add_init_script("try{localStorage.setItem('class26e.intro.seen','99');" + ("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled','[\"ifc\"]');" if ifc else "") + "}catch(e){}")
        p.clock.install(time=datetime.datetime.fromisoformat(when)); p.goto("http://127.0.0.1:%d/index.html" % PORT); p.wait_for_timeout(2500)
        return c, p
    c, p = at("2026-11-09T19:59:00-06:00"); before = p.evaluate(NT); c.close()
    c, p = at("2026-11-09T20:00:30-06:00"); after = p.evaluate(NT)
    units = p.evaluate("()=>unitsInTeachingOrder().map(u=>String(u))"); c.close()
    want = ["Arrest, Search, and Seizure", "Code of Criminal Procedure and Bill of Rights", "Consular Notification"]
    chk("(1) Test #9 is posted: title %r, topics %s" % ((after or {}).get("title"), (after or {}).get("t")), after and after.get("title") == "Test #9" and len(after.get("t") or []) == 3, after)
    chk("(2) at 7:59 PM Monday Nov 9 the next test is still Nov 9's (%s); from 8 PM it is Nov 16's, marking %s" % (before and before.get("d"), after and after.get("u")),
        before and before.get("d") == "2026-11-09" and after and after.get("d") == "2026-11-16" and after.get("u") == sorted(want), [before, after])
    chk("(2) each marked unit exists in the app", all(w in units for w in want), units[:30])
    c, p = at("2026-11-09T20:00:30-06:00", ifc=True); f = p.evaluate("()=>({cls:window.NOVA_CLASS, t:testTopicsFor('2026-11-16')})"); c.close()
    chk("(3) Fire Code has no test calendar (%s)" % f, f["cls"] != "ifc" or f["t"] is None, f)
    br.close()
finally:
    srv.shutdown()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
