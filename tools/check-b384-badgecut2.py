"""Build 384.50: an earned badge is never silent - with "Skip celebrations and pop-ups" ON it is SAID, once, plainly.
The owner (third report): "THE BADGE CUTSCENE IS NOT HAPPENING IDK WHAT ELSE TO SAY! ... I just unlocked yet another badge and it didn't happen."
THE CAUSE, read off his own account's cloud copy and played in Chromium on his real state: Settings > Motion & Effects > "Skip celebrations and
pop-ups" (theme.muteBanners) was ON on his phone. With it on every badge, character, banner, effect and flare scene and card returns at once - by
design and by his own earlier request ("unless you have the setting on") - and said nothing, so a badge was earned and no sign of why. With it OFF
every route plays (tools/trace-badge-run.py: plain, a tap a step, four taps a second, backgrounded, Reduce motion; both classes). So now, with it ON:
the results' "Found & unlocked" box ends in one line - what was earned and "Celebrations are off." - and a "Turn on" button that opens the switch's
own page with its row lit; where the scene would have played over Home, one top banner says the same (tap = the switch's page). With it OFF: nothing.

(A) Fire Code, a real full-chapter run (one hundo short of its badge, answered through the page's own buttons) with the setting ON: no case scene, and the
    results' box carries the note naming the unit's own badge title and "Celebrations are off", with a button
(B) the same in the academy
(C) the button: opens Settings > Motion & Effects with the switch's row lit, the switch reads ON, the tab bar is back; turning the switch off sticks
    (theme.muteBanners false, in the saved account's theme too)
(D) the setting OFF: the same run shows NO note and NO banner, and the badge case plays (up >= MIN_UP s with no ending begun)
(E) Home, setting ON, a character waiting to be announced: ONE banner (#celebrations-off) naming the character, tapping it opens the switch's page; no
    card; and with the setting OFF the card plays and there is no banner
(F) the switch's own words say it outright (badge and scenes named in its subtitle, read off the page) and it is a switch row on the Motion & Effects page
(G) no page errors
(H) NOTHING EARNED IS LEFT UNTOLD WITH THE SETTING OFF EITHER: a badge whose scene never reached its end on the results (the phone put the app away and it came
    back reloaded, 2.5s into the results) is owed (store.badgeSceneOwed) and Home plays the case by itself, to its end, and marks it played
(I) a scene that played on the results is marked played and Home does not play it a second time
(J) every unit of both classes: the scene builds, in motion and still, none throwing (the sweep that found no other silent case; passes on main too)

Run:  python3 tools/check-b384-badgecut2.py   (--against OLD/index.html must FAIL (A, B, C, E); ONLY=A,C runs those)"""
import importlib.util, json, os, re, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("tb", ROOT + "/tools/trace-badge-run.py"); tb = importlib.util.module_from_spec(spec); spec.loader.exec_module(tb)
from playwright.sync_api import sync_playwright
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}
def want(n): return not ONLY or n in ONLY
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
srv, port = tb.serve()
MIN_UP = 4.0
def seed_for(muted):
    s = json.loads(json.dumps(tb.BASE_SEED)); s["theme"] = {"muteBanners": bool(muted)}; return s
def fresh(br, cls, muted):
    ctx, pg, errs = tb.page(br, cls, seed_for(muted), body=tb.load_body()); tb.open_page(pg, port); return ctx, pg, errs
NOTE = r"""()=>{ const n = document.querySelector('.rs-celebrate-off'); return n ? { text: n.textContent, btn: !!n.querySelector('button'), shown: n.classList.contains('rs-in-now') || n.classList.contains('rs-in') } : null; }"""
def scene_up(tr):
    s = [x for x in tr["scenes"] if x["name"] == "badge case" and x.get("shown")]
    return s, [round((x["ended"] - x["up"]) / 1000, 1) for x in s if x.get("ended") and x.get("up")]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=tb.CHROME)
    errs_all = []
    # ---------------------------------------------------------------- (A)(B)(C) setting ON, a real badge run
    for key, cls in (("A", "ifc"), ("B", "academy")):
        if not want(key) and not (key == "A" and want("C")): continue
        ctx, pg, errs = fresh(br, cls, True)
        tr = tb.run(pg, "plain", limit=150)
        title = pg.evaluate("(u)=>badgeTitle(u).replace(/ badge$/i,'')", tr["unitsPlayed"][0])
        note = pg.evaluate(NOTE)
        s, ups = scene_up(tr)
        errs_all += errs
        if want(key):
            chk("(%s) %s, setting ON, a real full-unit run: no case scene, and the results' box says '%s' was earned and that celebrations are off, with a button (%s)"
                % (key, "Fire Code" if cls == "ifc" else "the academy", title[:30], note),
                not s and bool(note) and title.lower() in note["text"].lower() and "celebrations are off" in note["text"].lower() and note["btn"] and note["shown"], (note, tr["skipped"][:1]))
        if key == "A" and want("C") and not note:
            chk("(C) the note's button opens Motion & Effects ... (there is no note to press)", False, note)
        elif key == "A" and want("C"):
            pg.evaluate("()=>document.querySelector('.rs-celebrate-off').scrollIntoView({block:'center'})"); pg.wait_for_timeout(600)
            pg.click(".rs-celebrate-off-btn"); pg.wait_for_timeout(1200)
            st = pg.evaluate("""()=>({ page: !!document.querySelector('.settings-page-motion'), row: !!document.getElementById('settings-celebrations'),
              lit: !!document.querySelector('#settings-celebrations.settings-flash'), on: (document.querySelector('#settings-celebrations input')||{}).checked,
              tabs: !!document.querySelector('.bottomtabs:not([hidden])') })""")
            chk("(C) the note's button opens Motion & Effects with the switch's row lit, the switch ON, and the tab bar back (%s)" % st, st["page"] and st["row"] and st["lit"] and st["on"] and st["tabs"], st)
            pg.click("#settings-celebrations .box"); pg.wait_for_timeout(500)
            saved = pg.evaluate("()=>[theme.muteBanners, !!(store.theme && store.theme.muteBanners)]")
            chk("(C) turning it off sticks (theme and the saved account's theme): %s" % saved, saved == [False, False], saved)
        ctx.close()
    # ---------------------------------------------------------------- (D) setting OFF: the case plays, nothing is said
    if want("D"):
        ctx, pg, errs = fresh(br, "ifc", False)
        tr = tb.run(pg, "taps", limit=150)
        s, ups = scene_up(tr)
        note = pg.evaluate(NOTE); banner = pg.evaluate("()=>!!document.getElementById('celebrations-off')")
        chk("(D) Fire Code, setting OFF, tapped through: the badge case plays (up %s s, at least %.0f) and there is no note and no banner" % (ups, MIN_UP),
            bool(ups) and min(ups) >= MIN_UP and note is None and not banner, (ups, note, banner))
        errs_all += errs; ctx.close()
    # ---------------------------------------------------------------- (E) Home: a character waiting, setting ON then OFF
    if want("E"):
        for muted in (True, False):
            ctx, pg, errs = fresh(br, "academy", muted)
            names = pg.evaluate("""()=>{ const c = AVATAR_CHARACTERS.find(c => c.id !== 'ninja' && !c.unlock && !c.feat && !c.legacy && !c.retired && !isLockedCharacter(c.id));
              store.pendingCharUnlocks = [c.id]; store.unlocksShown = { chars: [], banners: [], fx: [] }; saveStore();
              const p = pendingHomeUnlocks(); const items = [].concat(p.chars.map(characterUnlockItem), p.banners.map(bannerUnlockItem), (p.fx || []).map(hundoFxUnlockItem)).filter(Boolean);
              showHome(); return items.map(i => i.name); }""")
            name = names[0] if names else ""
            got = None
            for _ in range(60):
                got = pg.evaluate("()=>{ const b = document.getElementById('celebrations-off'); return { banner: b ? b.textContent : null, card: !!document.querySelector('.rs-spot') }; }")
                if got["banner"] or got["card"]: break
                pg.wait_for_timeout(250)
            if muted:
                chk("(E) Home, setting ON, something waiting to be announced: ONE banner names it and says celebrations are off, and no card plays (%s)" % got,
                    bool(names) and bool(got["banner"]) and name.lower() in got["banner"].lower() and "celebrations are off" in got["banner"].lower() and not got["card"], got)
                pg.evaluate("()=>document.getElementById('celebrations-off').click()"); pg.wait_for_timeout(1000)
                chk("(E) ... and tapping it opens the switch's page", pg.evaluate("()=>!!document.querySelector('.settings-page-motion #settings-celebrations')"))
            else:
                chk("(E) Home, setting OFF: the card plays and there is no banner (%s)" % got, got["card"] and not got["banner"], got)
            errs_all += errs; ctx.close()
    # ---------------------------------------------------------------- (F) the switch says it outright
    if want("F"):
        ctx, pg, errs = fresh(br, "academy", False)
        pg.evaluate("()=>{ setActiveNav('settings'); showAppearance({ page: 'motion' }); }"); pg.wait_for_timeout(800)
        r = pg.evaluate("""()=>{ const row = document.getElementById('settings-celebrations'); if(!row) return null; const h = row.querySelector('.ohint'), cs = h ? getComputedStyle(h) : null;
          const rc = row.getBoundingClientRect();
          return { hint: h ? h.textContent : '', shown: !!h && cs.display !== 'none' && cs.visibility !== 'hidden' && h.getBoundingClientRect().height > 8, input: row.querySelector('input').type,
                   inView: rc.left >= 0 && rc.right <= innerWidth, page: !!document.querySelector('.settings-page-motion') }; }""")
        chk("(F) Motion & Effects holds the switch as a checkbox row whose subtitle is visible, inside the screen, and names badge and scenes (%s)" % r,
            bool(r) and r["page"] and r["input"] == "checkbox" and r["shown"] and r["inView"] and re.search(r"badge", r["hint"], re.I) and re.search(r"scene", r["hint"], re.I), r)
        errs_all += errs; ctx.close()
    # ---------------------------------------------------------------- (H) a scene the results never reached is owed, and Home plays it
    if want("H"):
        ctx, pg, errs = fresh(br, "ifc", False)
        unit = pg.evaluate("()=>unitsInTeachingOrder().filter(u=>unitQuestionCount(u)>0).sort((a,b)=>unitQuestionCount(a)-unitQuestionCount(b))[0]")
        pg.evaluate(r"""(t) => { store.unitPerfects = {}; saveStore(); showHome(); cfg.source = 'all'; cfg.mode = 'drill'; cfg.units = [t];
          setTimeout(() => beginRun(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === t)), 1200); return true; }""", unit)
        t0 = time.time()
        while time.time() - t0 < 120 and not pg.evaluate("()=>!!document.querySelector('.rs-screen')"):
            pg.evaluate(tb.ANSWER); pg.wait_for_timeout(120)
        pg.wait_for_timeout(2500)
        owed = pg.evaluate("(u)=>[!!(store.badgeSceneOwed||{})[u], !!(store.badgeScenePlayed||{})[u], badgeScenesOwed().length]", unit)
        # the phone puts the app away and brings it back: the results (and their scene) are gone, the account is not
        pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
        up = None; t1 = time.time()
        while time.time() - t1 < 25:
            if pg.evaluate("()=>!!document.querySelector('.bc-scene')"): up = time.time(); break
            pg.wait_for_timeout(250)
        chk("(H) the results are lost 2.5s in (the app reloaded): the badge is owed (%s), and Home plays its case scene by itself (up after %s)" % (owed, None if up is None else round(up - t1, 1)),
            owed[0] and not owed[1] and up is not None, (owed, up))
        if up is not None:
            end = None
            while time.time() - up < 30:
                if not pg.evaluate("()=>!!document.querySelector('.bc-scene')"): end = time.time(); break
                pg.wait_for_timeout(300)
            pg.wait_for_timeout(1500)
            st = pg.evaluate("(u)=>[!!(store.badgeScenePlayed||{})[u], badgeScenesOwed().length, !!document.querySelector('.bc-scene')]", unit)
            chk("(H) ... it plays to its end (%s s), is then marked played, nothing is owed, and it does not come round again (%s)" % (None if end is None else round(end - up, 1), st),
                end is not None and end - up >= MIN_UP and st == [True, 0, False], (end, st))
            pg.reload(); pg.wait_for_timeout(3500); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()"); pg.wait_for_timeout(5000)
            chk("(H) ... and a later launch plays nothing", not pg.evaluate("()=>!!document.querySelector('.bc-scene')"))
        errs_all += errs; ctx.close()
    # ---------------------------------------------------------------- (I) a scene that played on the results is not owed again
    if want("I"):
        ctx, pg, errs = fresh(br, "academy", False)
        tr = tb.run(pg, "plain", limit=150)
        s, ups = scene_up(tr)
        u = tr["unitsPlayed"][0]
        st = pg.evaluate("(u)=>[!!(store.badgeScenePlayed||{})[u], badgeScenesOwed().length]", u)
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(6000)
        again = pg.evaluate("()=>!!document.querySelector('.bc-scene')")
        chk("(I) a full run's scene played on the results (up %s s) is marked played, nothing owed (%s), and Home does not play it again (%s)" % (ups, st, again),
            bool(ups) and st == [True, 0] and not again, (ups, st, again))
        errs_all += errs; ctx.close()
    # ---------------------------------------------------------------- (J) every unit's scene builds (a scene that throws is a silent badge). Passes on main too: it is the sweep that found nothing.
    if want("J"):
        for cls in ("academy", "ifc"):
            ctx, pg, errs = fresh(br, cls, False)
            r = pg.evaluate(r"""()=>{ const bad = []; let n = 0;
              unitsInTeachingOrder().filter(u => unitQuestionCount(u) > 0).forEach(u => {
                [false, true].forEach(still => { n++;
                  try{ theme.reduceMotion = still; const h = playBadgeCaseScene([u], () => {}, [], {}); const o = document.querySelector('.bc-scene');
                    if(!o) bad.push([u.slice(0, 30), still, 'no overlay']); else { (o.__nova || {}).skip && o.__nova.skip(); o.remove(); }
                    document.body.classList.remove('bc-covering'); }
                  catch(e){ bad.push([u.slice(0, 30), still, String(e && e.message || e).slice(0, 60)]); }
                  document.querySelectorAll('.bc-scene').forEach(x => x.remove()); }); });
              theme.reduceMotion = false; return { n, bad }; }""")
            chk("(J) %s: the badge scene builds for every unit, in motion and still (%d scenes), none throwing and none without its overlay %s" % (cls, r["n"], r["bad"][:3]), r["n"] > 0 and not r["bad"], r)
            errs_all += errs; ctx.close()
    chk("(G) no page errors on any of it", not errs_all, errs_all[:4])
    br.close()
sys.exit(0 if ok else 1)
