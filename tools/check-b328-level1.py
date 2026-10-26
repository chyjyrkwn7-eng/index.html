#!/usr/bin/env python3
"""Build 328 gate: the rest of Level 1.

1. Every question that was in the bank before is still there with the same KEY
   (topic|src|hash of keyText/keyChoices): nobody's history moves. Compared with
   the previous build loaded beside this one (--base, default `git show HEAD:index.html`).
2. 24 units, each the size of its 10-25-26 study guide; the eight new ones are there.
3. The guide's changes: Penal Code #243 counts False Alarm or Report; Arrest, Search
   and Seizure #66 has its lost choice back; Sexual Assault's fifteen dropped
   questions are out of the unit and the daily pool, and #47-51 are in.
4. Arrest, Search and Seizure #31 and #55 show the red "Being verified" note once
   answered in a Drill.
5. Badges: 10 / 8 / 6 / 3 / 2 hundos by unit size; every unit has its own shape;
   24 badges sit six by four.
6. The unit screen has Level 1-3 tabs; Level 2 answers with a "Coming soon" sheet and
   stays on Level 1; Level 1 has no "More units coming soon" tile.

Run `--against <previous index.html>`: it fails there (no new units, old bands).
"""
import sys, os, subprocess, tempfile, functools, http.server, threading, socket

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
target = os.path.join(ROOT, "index.html")
if "--against" in sys.argv:
    target = os.path.abspath(sys.argv[sys.argv.index("--against") + 1])
base = None
if "--base" in sys.argv:
    base = os.path.abspath(sys.argv[sys.argv.index("--base") + 1])
else:
    try:
        src = subprocess.run(["git", "-C", ROOT, "show", "ba173e4:index.html"], capture_output=True, check=True).stdout
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False); tmp.write(src); tmp.close(); base = tmp.name
    except Exception:
        base = None

from playwright.sync_api import sync_playwright
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("  PASS " if ok else "  FAIL ") + name + ("" if ok else "  -> " + str(detail)[:300]))
    if not ok: fails += 1

def serve(path):
    d = os.path.dirname(path)
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=d)
    h.log_message = lambda *a: None
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/%s" % (port, os.path.basename(path))

FIXTURE = """() => { try{
  const st = { tourRev: 99, onboardingComplete: true, introSeen: 99 };
  localStorage.setItem('class26e.intro.seen', '99');
}catch(e){} }"""

GUIDE = {"Professionalism and Ethics": 29, "Professional Policing": 19, "Fitness, Wellness, and Stress Management": 28,
  "TCOLE Rules": 20, "Multiculturalism and Human Relations": 35, "Racial Profiling": 13, "US and Texas Constitution and Rights": 77,
  "Penal Code": 340, "Code of Criminal Procedure and Bill of Rights": 35, "Arrest, Search, and Seizure": 120, "Victims of Crime": 15,
  "Missing and Exploited Children": 55, "Identity Crimes": 12, "Sexual Assault and Family Violence": 36, "Verbal Communication": 29,
  "Civil Process and Liability": 22, "Consular Notification": 9, "Crisis Intervention Training": 67, "De-Escalation": 22,
  "Health and Safety Code": 26, "Interacting with Deaf or Hard-of-Hearing": 11, "Radio Communications, Alerts, and TCIC-TLETS": 15,
  "Traumatic Brain Injury": 12, "Phonetic Alphabet and Military Time": 39}

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    def open_page(path, w=393, h=852):
        srv, url = serve(path)
        ctx = b.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        pg.add_init_script("try{localStorage.setItem('class26e.intro.seen','99')}catch(e){}")
        pg.goto(url); pg.wait_for_timeout(2500)
        return srv, ctx, pg

    srv, ctx, pg = open_page(target)

    print("\n328a. no existing question moved")
    keys = pg.evaluate("() => KEYS.slice()")
    if base:
        bsrv, bctx, bpg = open_page(base)
        old = bpg.evaluate("() => KEYS.slice()")
        bctx.close(); bsrv.shutdown()
        check("every key of the previous bank is at the same index", keys[:len(old)] == old,
              [i for i in range(min(len(old), len(keys))) if keys[i] != old[i]][:8])
        check("the bank only grew (new questions are appended)", len(keys) > len(old), [len(old), len(keys)])
    else:
        check("previous build available to compare", False, "no base")
    check("no two questions share a key, apart from TCOLE's three #12s", len(keys) - len(set(keys)) <= 2, len(keys) - len(set(keys)))

    print("\n328b. 24 units, each its guide's size")
    sizes = pg.evaluate("() => { const o = {}; topicsIn(QUESTIONS).forEach(u => o[u] = unitQuestionCount(u)); return o; }")
    check("24 units", len(sizes) == 24, list(sizes))
    bad = {u: [sizes.get(u), n] for u, n in GUIDE.items() if sizes.get(u) != n}
    check("every unit is the size of its study guide", not bad, bad)

    print("\n328c. the guides' changes")
    r = pg.evaluate("""() => {
      const f = (t, s) => QUESTIONS.find(q => q.topic === t && q.src === s && !q.versionOnly);
      const p = f('Penal Code', 243), a66 = f('Arrest, Search, and Seizure', 66);
      const sa = QUESTIONS.filter(q => q.topic === 'Sexual Assault and Family Violence' && inWholeUnit(q)).map(q => q.src);
      return { penal: p && p.choices[p.answer], a66: a66 && a66.choices.slice(), a66ans: a66 && a66.choices[a66.answer],
        saIn: sa, sa30: !!f('Sexual Assault and Family Violence', 30) };
    }""")
    check("Penal Code #243 counts False Alarm or Report", r["penal"] == "False Alarm or Report", r["penal"])
    check("Arrest #66 has four choices, 12 hours first, 48 hours right", r["a66"] and len(r["a66"]) == 4 and r["a66"][0] == "12 hours" and r["a66ans"] == "48 hours", r["a66"])
    dropped = [4, 5, 6, 8, 10, 11, 19, 23, 25, 30, 31, 36, 38, 43, 45]
    check("Sexual Assault's dropped fifteen are out of the unit", not set(dropped) & set(r["saIn"]), sorted(set(dropped) & set(r["saIn"])))
    check("Sexual Assault #47-51 are in", set([47, 48, 49, 50, 51]) <= set(r["saIn"]), r["saIn"])
    daily = pg.evaluate("""() => { const out = []; const d0 = new Date(2026, 9, 26, 12);
      for(let k = 0; k < 500; k++){ const d = new Date(d0.getTime() + k * 86400000);
        const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        const q = QUESTIONS[dailyQuestionIndexFor(key)]; if(q.versionOnly) out.push(key + ':' + q.topic + ' ' + q.src); }
      return out; }""")
    check("500 days of daily questions, none retired", daily == [], daily[:4])

    print("\n328d. the answer being verified says so in red")
    note = pg.evaluate("""() => { const f = s => QUESTIONS.find(q => q.topic === 'Arrest, Search, and Seizure' && q.src === s);
      return [31, 55].map(s => { const n = buildBankNote(f(s)); return n ? n.textContent : null; }); }""")
    check("#31 and #55 each draw a red note naming the instructor", all(n and "instructor" in n and "verif" in n.lower() for n in note), note)
    check("a plain question draws none", pg.evaluate("() => buildBankNote(QUESTIONS[0]) === null"))
    color = pg.evaluate("""() => { const n = buildBankNote(QUESTIONS.find(q => q.verifyNote)); document.body.appendChild(n);
      const c = getComputedStyle(n.querySelector('.bank-note-text')).color; n.remove(); return c; }""")
    rgb = [int(x) for x in color.strip("rgba() ").split(",")[:3]] if color else [0, 0, 0]
    check("the note is the red bank-note (a red cast: R well above G and B)", rgb[0] > rgb[1] + 20 and rgb[0] > rgb[2] + 10, color)

    print("\n328e. badges")
    th = pg.evaluate("() => ['Identity Crimes','Fitness, Wellness, and Stress Management','US and Texas Constitution and Rights','Arrest, Search, and Seizure','Penal Code'].map(badgeThresholdFor)")
    check("10 / 8 / 6 / 3 / 2 hundos by unit size", th == [10, 8, 6, 3, 2], th)
    shapes = pg.evaluate("() => { const o = {}; topicsIn(QUESTIONS).forEach(u => { const s = badgeShapeFor(u); o[u] = s && s.d; }); return o; }")
    check("every unit has its own outline", len(set(shapes.values())) == len(shapes), len(set(shapes.values())))
    g = pg.evaluate("() => badgeCaseGrid(badgeCaseUnits(BADGE_CASES[0]).length)")
    check("24 badges sit six by four", g == {"cols": 6, "rows": 4}, g)
    retro = pg.evaluate("""() => { store.badgeBandsVersion = 3; store.unitPerfects = { 'Identity Crimes': 10, 'Penal Code': 1 }; store.retroBadgePending = [];
      grantRetroBadgesOnce(); return store.retroBadgePending.slice(); }""")
    check("an account at 10 hundos in a 12-question unit is owed that badge's celebration", retro == ["Identity Crimes"], retro)

    print("\n328f. levels on the unit screen")
    pg.evaluate("() => { store.seenUnitSelectTour = true; saveStore(); try{ localStorage.setItem(penalVersionNoteKey(), '1'); }catch(e){} showSetup(); }"); pg.wait_for_timeout(1500)   # the first-time unit tour is not what is measured
    lv = pg.evaluate("""() => ({ tabs: [...document.querySelectorAll('.screen-setup .setup-levels .iconbtn')].map(b => b.textContent.trim()),
      active: (document.querySelector('.screen-setup .setup-levels .iconbtn.active') || {}).textContent,
      shown: [...document.querySelectorAll('.picks > label.pick')].filter(r => getComputedStyle(r).display !== 'none').length,
      more: [...document.querySelectorAll('.pick-more-coming')].filter(r => getComputedStyle(r).display !== 'none' && !r.hidden).length })""")
    check("three level tabs, Level 1 active", lv["tabs"][:3] == ["Level 1", "Level 2", "Level 3"] and (lv["active"] or "").startswith("Level 1"), lv)
    check("Level 1 shows all 24 units and no 'More units coming soon' tile", lv["shown"] == 24 and lv["more"] == 0, lv)
    pg.click(".setup-levels .iconbtn[data-level='2']"); pg.wait_for_timeout(700)
    sh = pg.evaluate("""() => ({ sheet: !!document.querySelector('.level-coming-sheet'), txt: (document.querySelector('.level-coming-sheet') || {}).textContent || '',
      active: (document.querySelector('.screen-setup .setup-levels .iconbtn.active') || {}).textContent })""")
    check("Level 2 opens a 'Coming soon' sheet and the tab stays on Level 1", sh["sheet"] and "Level 2" in sh["txt"] and (sh["active"] or "").startswith("Level 1"), sh)
    pg.evaluate("() => document.querySelector('.level-coming-sheet .next').click()"); pg.wait_for_timeout(300)
    pg.evaluate("() => { const cb = document.querySelector('.picks > label.pick input'); cb.click(); }"); pg.wait_for_timeout(300)
    cnt = pg.evaluate("() => (document.querySelector('.setup-levels .iconbtn[data-level=\"1\"] .setup-level-count') || {}).textContent")
    check("a picked unit shows on its level's tab as a count", cnt == "1", cnt)
    ctx.close(); srv.shutdown()

with sync_playwright() as p:
    import datetime
    b = p.chromium.launch(executable_path=CHROME)
    print("\n328g. the Penal Code slides version ends at 9 PM Mon Oct 26; Nov 2's topics")
    srv, url = serve(target)
    def at(when):
        ctx = b.new_context(viewport={"width": 393, "height": 852}, timezone_id="America/Chicago"); pg = ctx.new_page()
        pg.add_init_script("try{localStorage.setItem('class26e.intro.seen','99')}catch(e){}")
        pg.clock.install(time=datetime.datetime.fromisoformat(when)); pg.goto(url); pg.wait_for_timeout(2000)
        return ctx, pg
    ctx, pg = at("2026-10-26T20:59:00-05:00")
    pre = pg.evaluate("() => ({ has: unitHasTestVersion('Penal Code'), n: unitVersionCount('Penal Code', 'test') })")
    pg.evaluate("() => showSetup()"); pg.wait_for_timeout(1200)
    marks0 = pg.evaluate("() => { const u = nextTestUnits(); return { u: u ? [...u.units] : null, cards: document.querySelectorAll('.picks .pick .pick-nexttest, .picks .pick [class*=nexttest]').length }; }")
    ctx.close()
    check("before 9 PM Monday only today's test is next (Penal Code)", marks0["u"] == ["Penal Code"], marks0)
    ctx, pg = at("2026-10-26T21:00:30-05:00")
    post = pg.evaluate("""() => { const i = QUESTIONS.findIndex(q => q.topic === 'Penal Code');
      return { has: unitHasTestVersion('Penal Code'), whole: unitVersionCount('Penal Code', null),
        chosen: QUESTIONS.reduce((k, q, j) => k + (q.topic === 'Penal Code' && inChosenVersion(j, {'Penal Code': 'test'}) ? 1 : 0), 0) }; }""")
    check("at 8:59 PM the slides 256-578 version is still offered", pre["has"] and pre["n"] == 132, pre)
    check("at 9:00 PM there is no short version, and a saved 'test' choice is the whole unit (340)", (not post["has"]) and post["chosen"] == 340 and post["whole"] == 340, post)
    pg.evaluate("() => showSetup()"); pg.wait_for_timeout(1200)
    tag = pg.evaluate("() => { const r = [...document.querySelectorAll('.picks > label.pick')].find(r => r.querySelector('input').value === 'Penal Code'); return r ? r.textContent : null; }")
    check("the Penal Code card no longer mentions a slides version", tag is not None and "Slides" not in tag and "version" not in tag.lower(), tag)
    nt = pg.evaluate("() => { const t = testTopicsFor('2026-11-02'); const u = nextTestUnits(); return { t: t && t.topics, u: u ? [...u.units] : null, d: u && u.date }; }")
    marks1 = pg.evaluate("() => [...document.querySelectorAll('.picks > label.pick')].filter(r => /next test/i.test(r.textContent)).map(r => r.querySelector('input').value)")
    check("from 9 PM only Nov 2's units carry the next-test mark", sorted(marks1) == sorted(["Code of Criminal Procedure and Bill of Rights", "Arrest, Search, and Seizure"]), marks1)
    check("Nov 2's test is CCP and Arrest, Search, and Seizure, and both units carry the next-test mark",
          nt["t"] == ["CCP and Bill of Rights", "Arrest, Search, and Seizure"] and sorted(nt["u"] or []) == sorted(["Code of Criminal Procedure and Bill of Rights", "Arrest, Search, and Seizure"]), nt)
    shown = pg.evaluate("() => { const r = [...document.querySelectorAll('.picks > label.pick')].find(r => r.querySelector('input').value === 'Code of Criminal Procedure and Bill of Rights'); return r && r.querySelector('.pname').textContent; }")
    check("CCP is shown as CCP and Bill of Rights", shown == "CCP and Bill of Rights", shown)
    ctx.close(); srv.shutdown()

print("\n" + ("ALL PASS" if not fails else "%d FAILED" % fails))
sys.exit(1 if fails else 0)
