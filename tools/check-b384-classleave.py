#!/usr/bin/env python3
"""Build 384 r16: leaving a class (Settings > Manage classes) - asked twice, smooth, and exactly right in both classes.

Madison: "When I hit the red leave button, it should ask again for confirmation." / "When it happens, the splash screen loaded but it
massively lagged and the screen jumped around." / "The fire code class was still in the class drop down. I didn't leave it." / "When
looking at it in settings, it says Your classes, and the one I'm in says Open now, I click it and it asks if I wanna leave. Should the
title of that section be Manage classes instead?" / "I hit the Join another class button, I hit the back button, and that took me to the
main menu for some reason."

What was wrong (build 384.13, measured here):
  (1) the red button left at once - one question;
  (2) leaving the class you are in sat on the Settings page for 0.3s (1x CPU; 1.2s at 4x on a loaded machine) with the account's write
      polled, and only then put the cover up; the page that finished a leave asked for in Fire Code built its whole Home first (the cover
      lifted over it) and then left; a leave of Fire Code's from Fire Code and the academy's from Fire Code each cost an extra page;
  (3) A LEAVE ASKED FOR IN FIRE CODE NEVER HAPPENED: it wrote its hand-off note (class26e.leaveclass) in Fire Code, where every
      "class26e." key is that class's own (class26e.ifc.leaveclass), and the academy's page read the other name - so leaving Fire
      Code from Fire Code opened the academy with Fire Code still in the class list ("the fire code class was still in the class drop
      down. I didn't leave it"), and leaving the academy from Fire Code did nothing at all;
  (4) the section was headed "Your classes" and the class you are in read "Open now" - and tapping it offers to leave;
  (5) the class list's Back always went Home, whichever way the list was opened.

  python3 tools/check-b384-classleave.py                                    (all)
  python3 tools/check-b384-classleave.py --against /path/to/old-index.html  (must FAIL on 1, 2, 3, 4, 5)
  ONLY=confirm,texts,back,lists,hop,timing,undo python3 tools/check-b384-classleave.py   (sections)

Texts are read off the page and judged by shape. The real flow is driven (Settings > Classes > the row > the red button > the red button) at an
iPhone 17 Pro Max (installed, touch) with the owner's account in both classes; the cloud is an in-memory Firestore kept in the tab so a reload
sees what the last page wrote.
"""
import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_leave_lib as V
import b384_switchfx_lib as L
from playwright.sync_api import sync_playwright

ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
def want(sec): return not ONLY or sec in ONLY
fails = []
def chk(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:600]), flush=True)
    if not cond: fails.append(name)

TITLE = {"academy": "Police Academy", "ifc": "Fire Code"}
OTHER = {"academy": "ifc", "ifc": "academy"}

def ev(X, js, arg=None): return L.ev(X.pg, js, arg)
def settle(X, cls, t0, limit=45): return X.wait_settled(t0, cls, limit)
def no_cover(X): return not ev(X, "()=>!!document.getElementById('class-switch-loader')")
def unchanged(X, before, what, extra=None):
    """nothing about the account changed: the lists, the dates, the cloud's copy, which class the page is, no cover"""
    now = X.state()
    keys = ("cls", "enrolled", "left", "joined", "cloud")
    same = all(now.get(k) == before.get(k) for k in keys) and no_cover(X)
    chk(what, same, {k: (before.get(k), now.get(k)) for k in keys if now.get(k) != before.get(k)})
    return now

def open_settings_classes(X):
    X.open_classes()

# ------------------------------------------------------------------------------------------------ (4) the section's words, (1) two questions, (5) Back
def sec_academy(pw, srv):
    X = V.Leave(pw, srv, "academy").boot()
    try:
        pg = X.pg
        # ---- (4) heading and rows, read off the page
        L.ev(pg, "()=>showAppearance()"); pg.wait_for_timeout(1300)
        menu = ev(X, "()=>{ const r = document.getElementById('settings-row-classes'); return r ? { label: (r.querySelector('.settings-row-label')||{}).textContent, value: (r.querySelector('.settings-row-value')||{}).textContent || '' } : null; }")
        exp = ev(X, "()=>{ const m = enrolledClasses(); return m.length === 1 ? classTitle(m[0]) : m.length + ' classes'; }")
        chk("texts Settings' main menu row says how many classes the account is in (%r)" % (menu,), bool(menu) and menu["value"] == exp, (menu, exp))
        X.S.tap("#settings-row-classes"); pg.wait_for_timeout(900)
        head = ev(X, "()=>{ const h = document.querySelector('.settings-page-classes > p.slab'); return h ? h.textContent.trim() : null; }")
        rows = ev(X, "()=>[...document.querySelectorAll('.settings-class-row')].map(r => ({ cls: r.dataset.cls, label: (r.querySelector('.settings-row-label')||{}).textContent, "
                     "value: ((r.querySelector('.settings-row-value')||{}).textContent || '').trim(), aria: r.getAttribute('aria-label') || '', chev: !!r.querySelector('.settings-row-chev') }))")
        note = ev(X, "()=>((document.querySelector('.settings-classes-note')||{}).textContent || '').trim()")
        cur = ev(X, "()=>window.NOVA_CLASS")
        chk("texts the section is headed as managing the classes, not as a list of them (%r)" % head,
            bool(head) and "manage" in head.lower() and "class" in head.lower(), head)
        chk("texts a row per class, named as the class is named (%s)" % [(r["cls"], r["label"]) for r in rows],
            [r["cls"] for r in rows] == ["academy", "ifc"] and all(r["label"] == TITLE[r["cls"]] for r in rows), rows)
        valued = [r for r in rows if r["value"]]
        chk("texts only the class you are in carries a value, and it names it as the current one - not as 'open' (%r)" % [(r["cls"], r["value"]) for r in valued],
            len(valued) == 1 and valued[0]["cls"] == cur and "current" in valued[0]["value"].lower() and "open" not in valued[0]["value"].lower(), valued)
        chk("texts every row says tapping manages that class, and still has its chevron (%s)" % [r["aria"] for r in rows],
            all("manage" in r["aria"].lower() and r["chev"] for r in rows), rows)
        chk("texts the footnote says tapping manages the class, and keeps the promise that progress is kept (%r)" % note[:90],
            "manage" in note.lower() and "kept" in note.lower(), note)

        # ---- (1) the two questions: Cancel at either changes nothing, both red buttons are needed
        for k in ("academy", "ifc"):
            before = X.state()
            X.tap_row(k)
            a = X.sheet()
            chk("confirm %s: the first sheet names the class and offers a red button and Cancel (%r)" % (k, a and a["title"]),
                bool(a) and TITLE[k] in (a["title"] or "") and a["danger"] and bool(a["back"]), a)
            if not a: continue
            X.press("back"); pg.wait_for_timeout(300)
            chk("confirm %s: Cancel on the first sheet closes it" % k, X.sheet() is None)
            unchanged(X, before, "confirm %s: Cancel on the first sheet changes nothing" % k)
            X.tap_row(k); X.press("yes"); pg.wait_for_timeout(900)
            b = X.sheet()
            chk("confirm %s: the red button asks again - a second sheet that names the class, with a red confirm and Cancel (%r)" % (k, b and b["title"]),
                bool(b) and b != a and TITLE[k] in (b["title"] or "") and (b["title"] != a["title"]) and b["danger"] and bool(b["back"]), (a, b))
            if b:
                chk("confirm %s: the second sheet says what is kept, and what goes (%r)" % (k, (b["body"] or "")[:100]),
                    "kept" in (b["body"] or "").lower() and "leaderboard" in (b["body"] or "").lower(), b)
            unchanged(X, before, "confirm %s: after the first red button nothing has changed yet (both are needed)" % k)
            if b:
                X.press("back"); pg.wait_for_timeout(1500)
                chk("confirm %s: Cancel on the second sheet closes it" % k, X.sheet() is None)
            unchanged(X, before, "confirm %s: Cancel on the second sheet changes nothing (no cover, no reload, the lists and the cloud as they were)" % k)
            chk("confirm %s: no class-left note was written and no hand-off is waiting" % k,
                not ev(X, "()=>['class26e.leaveclass','class26e.leftnote'].some(k => localStorage.getItem(k))"))

        # ---- (5) Back from the class list goes to where it was opened from
        L.ev(pg, "()=>showAppearance({page:'classes'})"); pg.wait_for_timeout(900)
        X.S.tap("#settings-join-class"); pg.wait_for_timeout(900)
        on = ev(X, "()=>!!document.querySelector('.class-catalog')")
        chk("back Join another class opens the class list", on)
        X.S.tap(".class-catalog .back-link"); pg.wait_for_timeout(900)
        where = ev(X, "()=>({ classes: !!document.querySelector('.settings-page-classes'), home: !!document.querySelector('#stage [data-screen=\"home\"]'), catalog: !!document.querySelector('.class-catalog') })")
        chk("back from the class list opened from Settings > Manage classes lands on that page, not Home (%s)" % where, where["classes"] and not where["home"] and not where["catalog"], where)
        L.ev(pg, "()=>showHome()"); pg.wait_for_timeout(1500)
        L.ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner,#classback-banner').forEach(e=>e.remove()); }")
        X.S.tap(".class-bubble"); pg.wait_for_timeout(900)
        X.S.tap(".class-stack-item.is-add"); pg.wait_for_timeout(900)
        on = ev(X, "()=>!!document.querySelector('.class-catalog')")
        X.S.tap(".class-catalog .back-link"); pg.wait_for_timeout(900)
        where = ev(X, "()=>({ home: !!document.querySelector('#stage [data-screen=\"home\"]'), catalog: !!document.querySelector('.class-catalog') })")
        chk("back from the class list opened by the class button's + lands on Home (%s)" % where, on and where["home"] and not where["catalog"], (on, where))
        errs = [e for e in X.S.errs if "Failed to load" not in e]
        chk("no page errors (academy)", not errs, errs)
    finally:
        X.close()

# ------------------------------------------------------------------------------------------------ (3) exact lists after each direction, with rejoin
def lists_after(X, final, left, label):
    """what every list says once the page has settled on `final` after `left` was left"""
    keep = OTHER[left]
    st = X.state()
    chk("lists %s: the page is %s, and the account is in %s only (%s)" % (label, TITLE[final], TITLE[keep], st["enrolled"]),
        st["cls"] == final and st["enrolled"] == [keep], st)
    cl = V.cloud_now(X.pg) or {}
    if st["cls"] == "academy":
        chk("lists %s: only %s is dated as left on the account, and nothing of the other class's is (%s)" % (label, TITLE[left], st["left"]),
            list((st["left"] or {}).keys()) == [left], st)
    chk("lists %s: the account's copy in the cloud lists %s only, and dates only %s as left (%s)" % (label, TITLE[keep], TITLE[left], cl),
        cl.get("classes") == [keep] and list((cl.get("left") or {}).keys()) == [left], cl)
    chk("lists %s: the class button has no other class to list (%s)" % (label, st["bubble"]), st["bubble"] == [], st)
    chk("lists %s: no hand-off key or note is left behind" % label,
        not ev(X, "()=>['class26e.leaveclass','class26e.leftnote'].some(k => localStorage.getItem(k))"))

def catalog_marks(X, enrolled, label):
    ev(X, "()=>{ showClassCatalog('settings'); }"); X.pg.wait_for_timeout(700)
    cards = ev(X, "()=>[...document.querySelectorAll('.class-card.is-academy, .class-card.is-ifc')].map(c => ({ cls: c.classList.contains('is-academy') ? 'academy' : 'ifc', enrolled: c.classList.contains('is-enrolled'), status: (c.querySelector('.cc-status')||{}).textContent }))")
    got = sorted(c["cls"] for c in cards if c["enrolled"])
    chk("lists %s: the class list marks exactly %s as enrolled (%s)" % (label, enrolled, cards), got == sorted(enrolled) and all((c["status"] == "Enrolled") == c["enrolled"] for c in cards), cards)

def sec_lists_academy(pw, srv):
    """in the academy: leave Fire Code (the other class), rejoin it; then in Fire Code: leave Fire Code (the class you are in), rejoin it"""
    X = V.Leave(pw, srv, "academy").boot()
    try:
        pg = X.pg
        before = X.state()
        t, sheets = X.leave("ifc")
        pg.wait_for_timeout(1800)
        chk("lists academy>leave Fire Code: asked twice (%s)" % [s["title"] for s in sheets], len(sheets) == 2, sheets)
        st = X.state()
        chk("lists academy>leave Fire Code: still the academy's page, no reload - the other class was left, not the one you are in (%s)" % st["cls"],
            st["cls"] == "academy" and not (X.log() and any(e["k"] == "load" for e in X.log())), st)
        lists_after(X, "academy", "ifc", "academy>Fire Code")
        rowsnow = ev(X, "()=>[...document.querySelectorAll('.settings-class-row')].map(r => r.dataset.cls)")
        chk("lists academy>leave Fire Code: Settings' Manage classes page lists the academy only, in place (%s)" % rowsnow, rowsnow == ["academy"], rowsnow)
        chk("lists academy>leave Fire Code: nothing from Home (the class button) was put on the Settings page",
            not ev(X, "()=>!!document.querySelector('#stage .class-bubble-wrap')"))
        sm = V.summarise(X.log(), t)
        chk("lists academy>leave Fire Code: 'You left Fire Code.' is said (%s)" % sm["toasts"], any("Fire Code" in x and "left" in x.lower() for x in sm["toasts"]), sm)
        catalog_marks(X, ["academy"], "academy>Fire Code")
        # the only class now: its row says so and offers the class list; Back from that goes to Manage classes
        L.ev(pg, "()=>showAppearance({page:'classes'})"); pg.wait_for_timeout(900)
        X.tap_row("academy")
        sh = X.sheet()
        chk("lists academy>leave Fire Code: the only class says it cannot be left (%r)" % (sh and sh["title"]), bool(sh) and "only" in (sh["title"] or "").lower(), sh)
        X.press("yes"); pg.wait_for_timeout(900)
        X.S.tap(".class-catalog .back-link"); pg.wait_for_timeout(900)
        where = ev(X, "()=>({ classes: !!document.querySelector('.settings-page-classes'), home: !!document.querySelector('#stage [data-screen=\"home\"]') })")
        chk("back the only-class sheet's Join another class, then Back, lands on Manage classes (%s)" % where, where["classes"] and not where["home"], where)
        # Back out of Fire Code's own enrol screen goes to the list, and from there to where the list was opened from
        ev(X, "()=>showClassCatalog('settings')"); pg.wait_for_timeout(700)
        X.S.tap(".class-card.is-ifc"); pg.wait_for_timeout(900)
        enroll = ev(X, "()=>!!document.querySelector('.class-enroll')")
        X.S.tap(".class-enroll .back-link"); pg.wait_for_timeout(800)
        cat = ev(X, "()=>!!document.querySelector('.class-catalog')")
        X.S.tap(".class-catalog .back-link"); pg.wait_for_timeout(900)
        where = ev(X, "()=>({ classes: !!document.querySelector('.settings-page-classes'), home: !!document.querySelector('#stage [data-screen=\"home\"]') })")
        chk("back Fire Code's enrol screen > Back > the class list > Back lands on Manage classes (%s, %s, %s)" % (enroll, cat, where), enroll and cat and where["classes"] and not where["home"], (enroll, cat, where))
        # rejoin: what the Enroll and get started button does (the book itself is a PDF only a person can choose)
        t0 = time.time()
        ev(X, "()=>{ setEnrolled('ifc', true); localStorage.setItem('class26e.greet.ifc', 'done'); switchClass('ifc'); }")
        s = settle(X, "ifc", t0)
        chk("lists rejoin Fire Code: it opens (%s)" % s, s is not None)
        X.quiet()
        st = X.state()
        pts = ev(X, "()=>store.lifetime && store.lifetime.points")
        chk("lists rejoin Fire Code: both classes are back, Fire Code's progress is as it was (%s points) and the academy is in its list (%s)" % (pts, st["bubble"]),
            st["enrolled"] == ["academy", "ifc"] and pts == 50 and st["bubble"] == ["academy"], st)
        cl = V.cloud_now(X.pg) or {}
        chk("lists rejoin Fire Code: the cloud's copy lists both again (%s)" % cl, cl.get("classes") == ["academy", "ifc"], cl)

        # ---- in Fire Code: Cancel at either sheet changes nothing, for both classes
        L.ev(pg, "()=>showAppearance({page:'classes'})"); pg.wait_for_timeout(1100)
        before = X.state()
        for k in ("ifc", "academy"):
            X.tap_row(k); a = X.sheet()
            chk("confirm fc %s: the first sheet names the class (%r)" % (k, a and a["title"]), bool(a) and TITLE[k] in (a["title"] or "") and a["danger"], a)
            if a:
                X.press("yes"); pg.wait_for_timeout(900)
                b = X.sheet()
                chk("confirm fc %s: the red button asks again (%r)" % (k, b and b["title"]), bool(b) and b["title"] != a["title"] and TITLE[k] in (b["title"] or "") and b["danger"], (a, b))
                unchanged(X, before, "confirm fc %s: nothing has changed after the first red button" % k)
                if b: X.press("back"); pg.wait_for_timeout(1500)
            unchanged(X, before, "confirm fc %s: Cancel changes nothing, and no hand-off is waiting" % k)
            chk("confirm fc %s: no hand-off key is waiting" % k, not ev(X, "()=>['class26e.leaveclass'].some(k => localStorage.getItem(k))"))
        # ---- in Fire Code: leave Fire Code, the class you are in -> the academy's page
        t, sheets = X.leave("ifc")
        s = settle(X, "academy", t)
        chk("lists fc>leave Fire Code: asked twice, and the academy opens (%s, %s)" % ([x["title"] for x in sheets], s), len(sheets) == 2 and s is not None, (sheets, s))
        pg.wait_for_timeout(900)
        lists_after(X, "academy", "ifc", "Fire Code>Fire Code")
        sm = V.summarise(X.log(), t)
        chk("lists fc>leave Fire Code: one page load, Home built once, one cover (%s loads, %s homes, %s covers)" % (sm["loads"], sm["homes"], sm["covers"]),
            sm["loads"] == 1 and sm["homes"] == 1 and sm["covers"] == 1, sm)
        chk("lists fc>leave Fire Code: 'You left Fire Code.' is said on the academy (%s)" % sm["toasts"], any("Fire Code" in x and "left" in x.lower() for x in sm["toasts"]), sm)
        errs = [e for e in X.S.errs if "Failed to load" not in e]
        chk("no page errors (lists)", not errs, errs)
    finally:
        X.close()

# ------------------------------------------------------------------------------------------------ (3) leaving the academy, both ways in, and the way back
def sec_academy_leaves(pw, srv, start, label):
    X = V.Leave(pw, srv, start).boot()
    try:
        pg = X.pg
        t, sheets = X.leave("academy")
        s = settle(X, "ifc", t)
        chk("lists %s>leave the academy: asked twice, and Fire Code opens (%s, %s)" % (label, [x["title"] for x in sheets], s), len(sheets) == 2 and s is not None, (sheets, s))
        pg.wait_for_timeout(1000)
        lists_after(X, "ifc", "academy", label + ">academy")
        cl = V.cloud_now(X.pg) or {}
        chk("lists %s>leave the academy: its row is off the leaderboard (%s)" % (label, cl.get("lb")), "xph5b57jbp5a" not in (cl.get("lb") or []), cl)
        sm = V.summarise(X.log(), t)
        chk("lists %s>leave the academy: 'You left Police Academy.' is said (%s)" % (label, sm["toasts"]), any("Police Academy" in x and "left" in x.lower() for x in sm["toasts"]), sm)
        chk("lists %s>leave the academy: Fire Code's page is the only Home built, once, under one cover (%s loads, homes %s, covers %s, splashes removed %s)" % (label, sm["loads"], sm["home_classes"], sm["covers"], sm["splash_gones"]),
            sm["home_classes"] == ["ifc"] and sm["splash_gones"] == 1 and sm["covers"] == 1, sm)
        # Settings > Manage classes in Fire Code lists only Fire Code, then the class list marks it; joining the academy again is the real flow
        L.ev(pg, "()=>showAppearance({page:'classes'})"); pg.wait_for_timeout(1000)
        rows = ev(X, "()=>[...document.querySelectorAll('.settings-class-row')].map(r => r.dataset.cls)")
        chk("lists %s>leave the academy: Manage classes lists Fire Code only (%s)" % (label, rows), rows == ["ifc"], rows)
        catalog_marks(X, ["ifc"], label + ">academy")
        X.S.tap(".class-card.is-academy"); pg.wait_for_timeout(900)
        sh = X.sheet()
        chk("lists rejoin the academy: the class list asks (%r)" % (sh and sh["title"]), bool(sh), sh)
        t0 = time.time()
        X.press("yes")
        s = settle(X, "academy", t0)
        chk("lists rejoin the academy: it opens (%s)" % s, s is not None)
        X.quiet()
        st = X.state()
        pts = ev(X, "()=>store.lifetime && store.lifetime.points")
        chk("lists rejoin the academy: both classes are back and the academy's progress is as it was (%s points) (%s)" % (pts, st["enrolled"]),
            st["enrolled"] == ["academy", "ifc"] and pts == 900, st)
        cl = V.cloud_now(X.pg) or {}
        chk("lists rejoin the academy: the cloud lists both (%s), the join dated after the leave (%s)" % (cl.get("classes"), cl),
            cl.get("classes") == ["academy", "ifc"] and (cl.get("joined") or {}).get("academy", 0) > (cl.get("left") or {}).get("academy", 1e18), cl)
        errs = [e for e in X.S.errs if "Failed to load" not in e]
        chk("no page errors (%s)" % label, not errs, errs)
    finally:
        X.close()

# ------------------------------------------------------------------------------------------------ a leave that cannot finish changes nothing
def sec_undo(pw, srv):
    for start, k in (("academy", "academy"), ("ifc", "academy")):
        X = V.Leave(pw, srv, start).boot()
        try:
            pg = X.pg
            before = X.state()
            # offline: the second red button says why it could not, and changes nothing
            X.S.ctx.set_offline(True)
            X.open_classes(); X.tap_row(k); X.press("yes"); pg.wait_for_timeout(700); X.press("yes"); pg.wait_for_timeout(1500)
            sh = X.sheet()
            chk("undo %s>leave %s offline: a sheet says it could not (%r)" % (start, k, sh and sh["title"]), bool(sh) and "couldn" in (sh["title"] or "").lower(), sh)
            unchanged(X, before, "undo %s>leave %s offline: nothing changed, no cover, the same page" % (start, k))
            chk("undo %s>leave %s offline: no hand-off is left" % (start, k), not ev(X, "()=>['class26e.leaveclass','class26e.leftnote'].some(k => localStorage.getItem(k))"))
            X.press("back"); pg.wait_for_timeout(300)
            X.S.ctx.set_offline(False)
            if start == "academy":
                # online, but the account will not take the write: the cover comes up, the write fails under it, the class is put back and the screen given back
                ev(X, "()=>{ const o = fbDb.collection.bind(fbDb); fbDb.collection = c => { const q = o(c); const d = q.doc.bind(q); q.doc = id => { const r = d(id); r.set = () => Promise.reject(new Error('down')); return r; }; return q; }; return true; }")
                t, sheets = X.leave(k)
                t_end = time.time() + 22; gone = False; seen_cover = False
                while time.time() < t_end:
                    c = ev(X, "()=>!!document.getElementById('class-switch-loader')")
                    seen_cover = seen_cover or bool(c)
                    if seen_cover and not c: gone = True; break
                    pg.wait_for_timeout(250)
                pg.wait_for_timeout(1500)
                st = X.state()
                sh = X.sheet()
                chk("undo %s>leave %s with the account unwritable: the cover came up, then the screen was given back (%s, %s)" % (start, k, seen_cover, gone), seen_cover and gone, (seen_cover, gone))
                chk("undo %s>leave %s with the account unwritable: the class is not left - both classes listed, this device still opens in %s (%s)" % (start, k, TITLE[start], st["enrolled"]),
                    st["cls"] == start and st["enrolled"] == ["academy", "ifc"] and not ev(X, "()=>localStorage.getItem('class26e.activeclass')"), st)
                chk("undo %s>leave %s with the account unwritable: the cloud's copy is as it was (%s)" % (start, k, st["cloud"]), st["cloud"] == before["cloud"], st["cloud"])
                chk("undo %s>leave %s with the account unwritable: a sheet says nothing was changed (%r)" % (start, k, sh and sh["body"]), bool(sh) and "nothing was changed" in (sh["body"] or "").lower(), sh)
                chk("undo %s>leave %s with the account unwritable: no left-note is waiting to be said on the next page" % (start, k), not ev(X, "()=>localStorage.getItem('class26e.leftnote')"))
        finally:
            X.close()

# ------------------------------------------------------------------------------------------------ (2) the lag and the jump
def sec_timing(pw, srv):
    # the cover is up at the tap: no sitting on Settings while the account's write is polled (1x CPU: the page's own time, not the machine's)
    for start, k, final, hop in (("academy", "academy", "ifc", False), ("ifc", "ifc", "academy", False), ("ifc", "academy", "ifc", True)):
        X = V.Leave(pw, srv, start, cpu=1).boot()
        try:
            t, sheets = X.leave(k)
            s = settle(X, final, t)
            X.pg.wait_for_timeout(1200)
            sm = V.summarise(X.log(), t)
            tag = "timing %s>leave %s" % (start, k)
            chk("%s: reaches %s's Home (%s s)" % (tag, TITLE[final], None if s is None else round(s, 1)), s is not None, sm)
            chk("%s: the cover is up within 250ms of the tap, not after the account is polled (%s ms)" % (tag, sm["cover_at"]), sm["cover_at"] is not None and sm["cover_at"] <= 250, sm)
            chk("%s: %s reloads at most - never a third (%s)" % (tag, "two page loads" if hop else "one page load", sm["loads"]), 1 <= sm["loads"] <= (2 if hop else 1), sm)
            chk("%s: Home is built once, and only the class you end in (%s)" % (tag, sm["home_classes"]), sm["home_classes"] == [final], sm)
            chk("%s: one cover, one splash handed over (%s covers, %s splashes removed)" % (tag, sm["covers"], sm["splash_gones"]), sm["splash_gones"] == 1 and sm["covers"] <= 1, sm)
            chk("%s: no layout shift is seen once the cover lifts (%s over %s shifts %s)" % (tag, sm["shift_seen"], sm["shift_seen_n"], sm["shift_seen_src"]), sm["shift_seen"] <= .02, sm)
        finally:
            X.close()
    # at 4x CPU (a phone next to this machine): the work the leave itself does on the main thread is small, and the cover covers the rest
    X = V.Leave(pw, srv, "ifc", cpu=4).boot()
    try:
        t, sheets = X.leave("academy")
        s = settle(X, "ifc", t, 70)
        X.pg.wait_for_timeout(1500)
        sm = V.summarise(X.log(), t)
        chk("timing 4x ifc>leave academy: Fire Code's Home, two loads, one Home built, one splash removed (%s s, %s)" % (None if s is None else round(s, 1), (sm["loads"], sm["home_classes"], sm["splash_gones"])),
            s is not None and sm["loads"] == 2 and sm["home_classes"] == ["ifc"] and sm["splash_gones"] == 1, sm)
        chk("timing 4x ifc>leave academy: no layout shift is seen once the cover lifts (%s)" % sm["shift_seen"], sm["shift_seen"] <= .02, sm)
    finally:
        X.close()
    X = V.Leave(pw, srv, "academy", cpu=4).boot()
    try:
        X.open_classes(); X.S.throttle(4)
        cost = ev(X, """()=>{ const t0 = performance.now(); finishLeaveClass('ifc'); const a = performance.now() - t0; const t1 = performance.now();
          (typeof refreshClassesPage === 'function' ? refreshClassesPage : () => showAppearance({ page: 'classes' }))(); return { left: enrolledClasses().length === 1, leave: Math.round(a), refresh: Math.round(performance.now() - t1) }; }""")
        chk("timing 4x academy: the leave's own work on the main thread (the list, the board row, the account's push, the page's refresh) is under 60ms (%s)" % cost,
            cost["left"] and cost["leave"] + cost["refresh"] < 60, cost)
    finally:
        X.close()

print("check-b384-classleave against", L.SRC_PATH, "(build %s)" % L.BUILD, flush=True)
with sync_playwright() as pw:
    srv = L.Server()
    try:
        for name, fn in (("texts,confirm,back", lambda: sec_academy(pw, srv)),
                         ("lists", lambda: sec_lists_academy(pw, srv)),
                         ("hop", lambda: (sec_academy_leaves(pw, srv, "academy", "academy"), sec_academy_leaves(pw, srv, "ifc", "fc"))),
                         ("undo", lambda: sec_undo(pw, srv)),
                         ("timing", lambda: sec_timing(pw, srv))):
            if ONLY and not (set(name.split(",")) & ONLY): continue
            print("== " + name, flush=True)
            try: fn()
            except Exception as e:
                import traceback; traceback.print_exc()
                chk("section %s ran" % name, False, repr(e)[:300])
    finally:
        srv.close()
print("\nRESULT:", "FAIL (%d): %s" % (len(fails), "; ".join(fails)[:1200]) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
