"""Build 384: an account that was already here gets Add to Home Screen once too, as a "Quick tip".
Madison: "Existing accounts, they can get the pop up too on how to add to Home Screen. But for existing accounts have it
say like quick tip or something."
Read off the page, an existing account (signed up, has answered questions, the tips long done) opening Nova:
(1) iPhone, a Safari tab: on Home, once the launch has gone quiet, the Add to Home Screen sheet comes up headed "Quick tip"
    (not the sign-up's heading), with iPhone picked, "Not now" to close, and nothing of a computer in what it says;
(2) ...it waits its turn: while something else is up on Home (an unlock card) it does not come; once that is gone, it does;
(3) ...closed, the device remembers it (class26e.a2hs holds a time); opened again, no sheet - once only;
(4) Samsung, a Chrome tab: the same Quick tip, Android picked;
(5) never: in the installed app, on a computer, for an account that has answered nothing (a sign-up still under way), or
    where it has shown before (the sign-up's own showing counts);
(6) the sign-up's own showing keeps its heading ("Home Screen") - only an existing account's says Quick tip;
(7) no page errors.
Run:  python3 tools/check-b384-a2hstip.py   (--against OLD/index.html must FAIL)"""
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-a2hs.py")).read(); _src = _src[:_src.index("\nwith sync_playwright() as pw:")]
G = {"__file__": os.path.join(HERE, "check-b384-a2hs.py"), "__name__": "b384tip"}
exec(_src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
CODE = "TEST-3842"
# an account that has been here: What's new seen at its current revision (INTRO_REV; '1' would put it up, and the tip waits for it)
SEEN = ("['class26e.freshstart','class26e.unithold.tip','class26e.getstarted','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.intro.seen','99'); localStorage.setItem('class26e.frame.ok','go-live-1');")
def acct(answered):
    return {"firstName": "Gate Tester", "avatarChar": "ghost", "onboardingComplete": True, "publicId": "gatetest3842", "leaderboardOptIn": False,
            "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
            "seenMainMenuTour": True, "seenClassTip": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True, "seenRankingsTour": True,
            "seenAppearanceTour": True, "lifetime": {"points": 1200 if answered else 0, "answered": answered, "correct": int(answered * .8)}}
def init(answered, extra=""):
    return SEEN + "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(acct(answered))) + \
        "localStorage.setItem('class26e.synccode','%s');" % CODE + extra
SHEET = """()=>{ const o=document.getElementById('a2hs-sheet'); if(!o) return null;
  const seg=[...o.querySelectorAll('.a2hs-seg [role=radio]')].filter(b=>b.getAttribute('aria-checked')==='true').map(b=>b.dataset.dev);
  return { from:o.dataset.from, tag:(o.querySelector('.a2hs-tag')||{}).textContent||'', title:(o.querySelector('.a2hs-title')||{}).textContent||'',
    intro:(o.querySelector('.a2hs-intro')||{}).textContent||'', close:(o.querySelector('.a2hs-close')||{}).textContent||'', checked:seg,
    screen:(document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen }; }"""
def wait_sheet(pg, secs):
    for _ in range(int(secs * 4)):
        r = pg.evaluate(SHEET)
        if r: return r
        pg.wait_for_timeout(250)
    return None
def on_home(pg):
    for _ in range(40):
        if G["screen"](pg) == "home": return True
        pg.wait_for_timeout(250)
    return False
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch()
    # (1)-(3) iPhone, a Safari tab
    ctx, pg = G["open_page"](br, "iphone", init=init(300), seed={"progress": {CODE: acct(300)}})
    home = on_home(pg)
    # (2) something else up on Home first: an unlock card (a stand-in .rs-spot), for 14 seconds
    pg.evaluate("()=>{ const d=document.createElement('div'); d.className='rs-spot'; d.id='gate-hold'; document.body.appendChild(d); }")
    held = wait_sheet(pg, 14)
    pg.evaluate("()=>document.getElementById('gate-hold')?.remove()")
    r = wait_sheet(pg, 25)
    chk("(2) iPhone: while an unlock card is up on Home the tip waits (%s); once it is gone, it comes (%s)" % (held and held["from"], r and r["from"]), home and held is None and r is not None, [home, held, r])
    chk("(1) iPhone, a Safari tab, an existing account: the sheet on Home headed '%s', iPhone picked, '%s' to close" % (r and r["tag"], r and r["close"]),
        bool(r) and r["from"] == "tip" and re.fullmatch(r"\s*quick tip\s*", r["tag"], re.I) and r["checked"] == ["apple"] and r["screen"] == "home"
        and re.search(r"not now", r["close"], re.I) and not re.search(r"computer", r["intro"], re.I), r)
    if r:
        G["sheet_layout"](pg, "Quick tip sheet")
        gone = G["close_sheet"](pg)
        key = pg.evaluate("()=>localStorage.getItem('class26e.a2hs')")
        G["relaunch"](pg); on_home(pg)
        again = wait_sheet(pg, 16)
        chk("(3) closed (%s), the device remembers it (%s); opened again, no sheet (%s)" % (gone, key, again and again["from"]), gone and bool(re.fullmatch(r"\d+", key or "")) and again is None, [gone, key, again])
    errs_all += pg.errs; ctx.close()
    # (4) Samsung
    ctx, pg = G["open_page"](br, "samsung", init=init(120), seed={"progress": {CODE: acct(120)}})
    on_home(pg); r = wait_sheet(pg, 25)
    chk("(4) Samsung, a Chrome tab: the same Quick tip, Android picked (%s)" % (r and [r["tag"], r["checked"]]),
        bool(r) and r["from"] == "tip" and re.fullmatch(r"\s*quick tip\s*", r["tag"], re.I) and r["checked"] == ["android"], r)
    errs_all += pg.errs; ctx.close()
    # (5) never
    never = {}
    for label, dev, kw in (("installed", "iphone", {"installed": True, "init": init(300)}), ("computer", "desktop", {"init": init(300)}),
                           ("answered nothing", "iphone", {"init": init(0)}),
                           ("shown before", "iphone", {"init": init(300, "localStorage.setItem('class26e.a2hs', String(Date.now() - 864e5));")})):
        ctx, pg = G["open_page"](br, dev, seed={"progress": {CODE: acct(0 if label == "answered nothing" else 300)}}, **kw)
        h = on_home(pg); r = wait_sheet(pg, 18)
        never[label] = {"home": h, "sheet": r and r["from"]}
        errs_all += pg.errs; ctx.close()
    chk("(5) never in the installed app, on a computer, for an account with nothing answered, or where it has shown (%s)" % never,
        all(v["home"] and v["sheet"] is None for v in never.values()), never)
    # (6) the sign-up's showing keeps its own heading
    ctx, pg = G["open_page"](br, "iphone", init=init(300, "localStorage.setItem('class26e.a2hs', String(Date.now()));"), seed={"progress": {CODE: acct(300)}})
    on_home(pg)
    pg.evaluate("()=>showHomeScreenSheet({ from: 'signup' })"); pg.wait_for_timeout(800)
    s6 = pg.evaluate(SHEET)
    chk("(6) the sign-up's own showing is headed '%s', not Quick tip" % (s6 and s6["tag"]), bool(s6) and s6["from"] == "signup" and not re.search(r"tip", s6["tag"], re.I), s6)
    errs_all += pg.errs; ctx.close()
    br.close()
chk("(7) no page errors", not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
