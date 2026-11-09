"""Build 384: picking a class at sign-up - a second tap unpicks it, and Continue asks to confirm.
Madison: "When signing up, when you select a class to enroll, there's no way to unselect it. Ensure that if you tap it again after
you click it, you'd unenroll. After you select a class and hit continue, have it ask to confirm and stuff."
A fresh device (no account), iPhone 17 Pro Max (440x956), Select your classes, read off the page:
(1) a tap on the class picks it ("Selected", Continue shows); a second tap unpicks it (back to "Select", Continue hidden);
    a third picks it again;
(2) Continue opens a confirm sheet naming the class, with Enroll and Go back - and starts nothing yet (no loading screen);
(3) Go back closes the sheet, the class still picked, still on the class screen;
(4) Continue then Enroll starts the sign-up (its loading screen comes up);
(5) no page errors.
Run:  python3 tools/check-b384-signupclass.py   (--against OLD/index.html must FAIL)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384sc"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
STATE = """()=>{ const c=document.querySelector('.classselect-panel .class-card.is-academy'), n=document.querySelector('.classselect-panel #nextbtn');
  return { on: !!c && c.classList.contains('is-picked'), chip: c && c.querySelector('.cc-status').textContent, cont: !!n && !n.hidden,
           sheet: !!document.querySelector('#classenroll-confirm'), title: (document.querySelector('#classenroll-confirm h2')||{}).textContent || '',
           yes: !!document.querySelector('#classenroll-confirm .classenroll-yes'), back: !!document.querySelector('#classenroll-confirm .classenroll-back'),
           loading: !!document.querySelector('#genprofile-overlay'), onClasses: !!document.querySelector('#stage .classselect-panel') }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["SEEN"], errs=errs)
    pg.evaluate("()=>{ document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner').forEach(e=>e.remove()); showClassSelection(); }"); pg.wait_for_timeout(1200)
    card = ".classselect-panel .class-card.is-academy"
    pg.click(card); pg.wait_for_timeout(350); s1 = pg.evaluate(STATE)
    pg.click(card); pg.wait_for_timeout(350); s2 = pg.evaluate(STATE)
    pg.click(card); pg.wait_for_timeout(350); s3 = pg.evaluate(STATE)
    ck("(1) a tap picks (%s, Continue %s), a second unpicks (%s, Continue %s), a third picks again (%s)" % (s1["chip"], s1["cont"], s2["chip"], s2["cont"], s3["chip"]),
       s1["on"] and s1["cont"] and not s2["on"] and not s2["cont"] and s2["chip"] != s1["chip"] and s3["on"] and s3["cont"], [s1, s2, s3])
    pg.click(".classselect-panel #nextbtn"); pg.wait_for_timeout(600); s4 = pg.evaluate(STATE)
    ck("(2) Continue asks first: a sheet (%r) with Enroll and Go back, nothing started yet" % s4["title"],
       s4["sheet"] and s4["yes"] and s4["back"] and s4["title"] and not s4["loading"], s4)
    if s4["back"]:
        pg.click("#classenroll-confirm .classenroll-back"); pg.wait_for_timeout(600)
    s5 = pg.evaluate(STATE)
    ck("(3) Go back closes it, the class still picked, still here", s4["back"] and not s5["sheet"] and s5["on"] and s5["onClasses"] and not s5["loading"], s5)
    pg.click(".classselect-panel #nextbtn"); pg.wait_for_timeout(500)
    if pg.evaluate("()=>!!document.querySelector('#classenroll-confirm .classenroll-yes')"):
        pg.click("#classenroll-confirm .classenroll-yes")
    started = False
    for _ in range(20):
        if pg.evaluate("()=>!!document.querySelector('#genprofile-overlay')"): started = True; break
        pg.wait_for_timeout(150)
    ck("(4) Continue then Enroll starts the sign-up (its loading screen: %s)" % started, s4["yes"] and started)
    ck("(5) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
