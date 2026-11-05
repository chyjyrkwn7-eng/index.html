"""Build 384: What's New for Version 10 - existing accounts only, once.
Madison: "for EXISTING accounts only, there is gonna be a 'what's new' pop up for this update as well. We are gonna be onto
version 10. Just a semi quick one, mentioning the updating interface, updated settings layout, updated layout, and of course
the biggest piece of the update, the new class ... This will talk about the ifc the option to switch between classes and
stuff. Make it great. I love how the what's new pop up has been looking, don't change that look."
Read off the page:
(1) an existing account (it saw 9.2's card) opening Nova on an iPhone 17 Pro Max: the card comes up on Home, headed "New in
    version 10", a short list (4 to 7 rows) whose first row is the new class (Fire Code) and which also covers moving between
    classes, the new look/layout and Settings - the same card as before (intro-card-compact, its heading, Got it);
(2) Got it closes it, and opened again it does not come back;
(3) a brand-new account never sees it: a sign-up from Get Started to Home's last tip never puts it up, and the device's
    mark is at the current revision;
(4) the card is inside the screen on an iPhone SE (375x667), the Pro Max and an iPad Pro 11", nothing scrolls;
(5) Settings' version history leads with Version 10; no page errors.
Run:  python3 tools/check-b384-whatsnew10.py   (--against OLD/index.html must FAIL)"""
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-a2hs.py")).read(); _src = _src[:_src.index("\nwith sync_playwright() as pw:")]
G = {"__file__": os.path.join(HERE, "check-b384-a2hs.py"), "__name__": "b384wn"}
exec(_src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
CODE = "TEST-3843"
def acct():
    return {"firstName": "Gate Tester", "avatarChar": "ghost", "onboardingComplete": True, "publicId": "gatetest3843", "leaderboardOptIn": False,
            "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
            "seenMainMenuTour": True, "seenClassTip": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True, "seenRankingsTour": True,
            "seenAppearanceTour": True, "lifetime": {"points": 1200, "answered": 300, "correct": 250}}
INIT = ("['class26e.freshstart','class26e.unithold.tip','class26e.getstarted','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.intro.seen','6'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.a2hs', String(Date.now()));"
        "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','%s');" % (json.dumps(json.dumps(acct())), CODE))
CARD = """()=>{ const el=document.getElementById('intro-pop'); if(!el) return null; const c=el.querySelector('.intro-card'), r=c.getBoundingClientRect();
  return { compact: c.classList.contains('intro-card-compact'), eyebrow: (el.querySelector('.intro-eyebrow')||{}).textContent||'', title: (el.querySelector('.intro-title')||{}).textContent||'',
    rows: [...el.querySelectorAll('.intro-row')].map(x=>x.textContent.trim()), go: (el.querySelector('.intro-go')||{}).textContent||'',
    inside: r.top >= 0 && r.bottom <= innerHeight + 0.5 && r.left >= 0 && r.right <= innerWidth + 0.5, scrolls: el.scrollHeight > el.clientHeight + 1 }; }"""
def wait_card(pg, secs=20):
    for _ in range(int(secs * 2)):
        r = pg.evaluate(CARD)
        if r: return r
        pg.wait_for_timeout(500)
    return None
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch()
    # (1) (2) existing account, Pro Max
    ctx, pg = G["open_page"](br, "iphone", init=INIT, seed={"progress": {CODE: acct()}})
    r = wait_card(pg)
    rows = (r or {}).get("rows", [])
    txt = " ".join(rows).lower()
    chk("(1) existing account: the card on Home, '%s', %d rows, first: %r" % (r and r["eyebrow"], len(rows), rows[:1]),
        bool(r) and r["compact"] and re.search(r"version 10\b", r["eyebrow"], re.I) and "new" in r["title"].lower() and 4 <= len(rows) <= 7
        and re.search(r"fire code", rows[0], re.I) and re.search(r"between (your )?classes|class button", txt) and re.search(r"settings", txt)
        and re.search(r"look|layout|design", txt) and re.search(r"got it", r["go"], re.I), r)
    if r:
        pg.click("#intro-pop .intro-go"); pg.wait_for_timeout(900)
        G["relaunch"](pg); again = wait_card(pg, 10)
        chk("(2) Got it closes it; opened again, it does not come back (%s)" % (again and again["eyebrow"]), again is None, again)
    errs_all += pg.errs; ctx.close()
    # (4) the sizes
    fits = {}
    for label, (w, h) in (("se", (375, 667)), ("promax", (440, 956)), ("ipad", (834, 1194))):
        G["DEVICES"]["wn-" + label] = (w, h, (62, 0, 34, 0) if label != "ipad" else (24, 0, 20, 0)); G["UA"]["wn-" + label] = G["UA"]["iphone"]
        ctx, pg = G["open_page"](br, "wn-" + label, init=INIT, seed={"progress": {CODE: acct()}})
        r = wait_card(pg); fits[label] = r and {"inside": r["inside"], "scrolls": r["scrolls"], "rows": len(r["rows"])}
        errs_all += pg.errs; ctx.close()
    chk("(4) inside the screen with nothing scrolling on the SE, Pro Max and iPad (%s)" % fits, all(v and v["inside"] and not v["scrolls"] for v in fits.values()), fits)
    # (5) Settings' version history
    ctx, pg = G["open_page"](br, "iphone", init=INIT.replace("'class26e.intro.seen','6'", "'class26e.intro.seen','99'"), seed={"progress": {CODE: acct()}})
    hist = pg.evaluate("()=>RELEASE_NOTES[0].version")
    chk("(5) the version history leads with Version 10 (%s)" % hist, hist == "10", hist)
    errs_all += pg.errs; ctx.close()
    # (3) a brand-new account
    ctx, pg = G["open_page"](br, "iphone")
    pg.add_init_script("")
    seen_card = []
    pg.evaluate("()=>{ new MutationObserver(()=>{ if(document.getElementById('intro-pop')) window.__wnSeen = true; }).observe(document.body, { childList: true, subtree: true }); }")
    walk = G["sign_up"](pg, "Jordan Wells")
    pg.wait_for_timeout(6000)
    st = pg.evaluate("()=>({ seen: !!window.__wnSeen || !!document.getElementById('intro-pop'), mark: Number(localStorage.getItem('class26e.intro.seen')||0), rev: INTRO_REV })")
    chk("(3) a new account never sees it - sign-up to the last tip and after (%s)" % st, not st["seen"] and st["mark"] >= st["rev"], st)
    errs_all += [e for e in pg.errs if "a2hs" not in e]; ctx.close()
    br.close()
chk("(5) no page errors (%s)" % errs_all[:2], not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
