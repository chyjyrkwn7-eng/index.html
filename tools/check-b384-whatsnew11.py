"""Build 384.137: What's New for Version 11 - existing accounts only, once per device, in either class.
Madison: "Go ahead and start working on a what's new update thing. Talking about the plated badges and whatever else. We have a
pretty massive new build on our hands here."
Read off the page:
(1) an existing account that saw Version 10's card (mark 7) opening Nova in the academy on an iPhone 17 Pro Max: the card comes up
    on Home, headed "New in version 11", 4 to 8 rows (384 streak: the Daily streak row made the academy's 7 and Fire Code's 8), the first about the badges as metal pins, the others covering pinning a badge
    and All unlocks - the same card (intro-card-compact, its heading, Got it); no Fire Code-only row in the academy;
(2) Got it closes it, and opened again it does not come back;
(3) a brand-new account never sees it: a sign-up from Get Started to Home's last tip never puts it up, and the device's
    mark is at the current revision;
(4) the card is inside the screen on an iPhone SE (375x667), the Pro Max and an iPad Pro 11", nothing scrolls;
(5) Settings' version history leads with Version 11; no page errors;
(6) Fire Code: the same account opening in Fire Code gets the card there too (Version 10's was held for the academy), with the
    calculator row, 4 to 8 rows, inside the screen.
Run:  python3 tools/check-b384-whatsnew11.py   (--against OLD/index.html must FAIL)"""
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
            "seenAppearanceTour": True, "lifetime": {"points": 1200, "answered": 300, "correct": 250}, "classes": ["academy", "ifc"]}
INIT = ("['class26e.freshstart','class26e.unithold.tip','class26e.getstarted','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.intro.seen','7'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.a2hs', String(Date.now()));"
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
        bool(r) and r["compact"] and re.search(r"version 11\b", r["eyebrow"], re.I) and "new" in r["title"].lower() and 4 <= len(rows) <= 8
        and re.search(r"badge", rows[0], re.I) and re.search(r"metal|pin", rows[0], re.I) and re.search(r"pin a badge|pin one badge", txt)
        and re.search(r"all unlocks", txt) and not re.search(r"calculator", txt) and re.search(r"got it", r["go"], re.I), r)
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
    chk("(5) the version history leads with Version 11 (%s)" % hist, hist == "11", hist)
    errs_all += pg.errs; ctx.close()
    # (6) Fire Code
    IFC_ACCT = {k: v for k, v in acct().items()}
    IFC_ACCT.update({"ifcCurveRule": 38435, "rankUpShown": 0, "unitPerfects": {}, "testHistory": []})
    INIT_IFC = INIT + ("localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        "localStorage.setItem('class26e.activeclass','ifc');"
        "['class26e.ifc.freshstart','class26e.ifc.daily.seen','class26e.ifc.getstarted','class26e.ifc.savecode.asked','class26e.ifc.savecode.card'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(IFC_ACCT)))
    ctx, pg = G["open_page"](br, "iphone", init=INIT_IFC, seed={"progress": {CODE: acct()}})
    r = wait_card(pg, 30); cls = pg.evaluate("()=>window.NOVA_CLASS")
    rows = (r or {}).get("rows", []); txt = " ".join(rows).lower()
    chk("(6) Fire Code: the card there too, with its calculator row (%s, %s, %d rows)" % (cls, r and r["eyebrow"], len(rows)),
        cls == "ifc" and bool(r) and re.search(r"version 11\b", r["eyebrow"], re.I) and 4 <= len(rows) <= 8 and re.search(r"calculator", txt)
        and re.search(r"badge", rows[0], re.I) and r["inside"] and not r["scrolls"], r or cls)
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
