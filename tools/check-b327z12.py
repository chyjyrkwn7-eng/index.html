#!/usr/bin/env python3
"""Build 327z12: Madison's list after 327z11, one section per report.

  python3 tools/check-b327z12.py
  python3 tools/check-b327z12.py --against /path/to/old/index.html
  B327Z12_ONLY=LN python3 tools/check-b327z12.py

  L. "fake void ... doesn't move": recording a small character's flip-book
     plays Umbra's moon phases and Void's flare turn (both used to be held
     at one frame) - the recorder is watched setting each loop's time.
  M. "When the chat is pulled up, the Liquid Glass is glitched and lags
     behind": no frame of the slide up carries a backdrop blur, and the
     sheet is glass again once it has stopped.
  N. "you can't scroll down when ... touching the actual calendar", and
     "could the calendar look better": on an iPhone no day of the month
     carries a native haptic switch (a finger on one drags the switch, not
     the page) while the month's other buttons still do; the month is one
     card holding its title, a Today pill and arrows in one row, the days,
     the key and the picked day; on a phone a day is a number, not a tile.
  O. "can [hundos] and xp be like [overall] ... the title header thing",
     then "just stuff relevant to that leaderboard tab": This Week and
     Hundos carry a header and ONE column, their own number (XP, Hundos);
     Overall keeps its three. (327z13: Find me carries NO icon - "remove that".)
  P. "The daily question button did not get better": waiting, the button is
     lit in the rank's colour with no ring drawn on it; answered, it is the
     plain glass with a slim arc.

  Round 2 (same build):
  Q. "That look you get when tapping someone's profile ... could it be like
     that? ... the friends box is hidden under the profile stuff ... Chat
     tab may make more sense": Profile is three sibling cards (you, the
     next rank, the badge case), the first in the person card's glass (the
     page's card body under its banner pools, the surface blur), with no
     Friends box; the chat's Friends tab opens with a Friends bar whose
     button opens the Friends screen, and that screen's back link returns
     to the tab it was opened over, which stays lit.
  R. "The question mark is not centered": the mark's ink is centred in the
     button within half a pixel both ways, waiting and answered. 327z13:
     "when it's complete don't make it a checkmark" - answered, it is still
     the "?" (no tick drawn).
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("z5b", os.path.join(HERE, "check-b327z5-b.py"))
z5b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(z5b)   # check-behaviour reads --against itself
cb = z5b.cb
check = cb.check
from playwright.sync_api import sync_playwright

ONLY = os.environ.get("B327Z12_ONLY", "LMNOPQR")
UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
IPHONE_INIT = "Object.defineProperty(navigator,'userAgent',{get:()=>%r});try{Object.defineProperty(navigator,'standalone',{get:()=>true});}catch(e){}" % UA_IPHONE
CLEAN = "() => document.querySelectorAll('#tour-overlay, #tour-tooltip, .daily-alert, .toast, .invite-overlay').forEach(x => x.remove())"


def chars_move(br):
    print("\nL. a small character's recording plays its slow loops")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    for cid, name in (("umbra", "cx-um-dark"), ("voidwalker", "cx-spin-back")):
        r = pg.evaluate("""async ([cid, name]) => {
          const d = Object.getOwnPropertyDescriptor(Animation.prototype, 'currentTime');
          const seen = new Set();
          Object.defineProperty(Animation.prototype, 'currentTime', { configurable: true, get: d.get,
            set(v){ if(this.animationName === name) seen.add(Math.round(Number(v) / 10)); return d.set.call(this, v); } });
          try{ await caches.keys().then(ks => Promise.all(ks.map(k => caches.delete(k)))); }catch(e){}
          let sp = null;
          try{ sp = await Promise.race([recordCharSheet(charAnimDrawing(cid), 64), new Promise(r => setTimeout(() => r('timeout'), 40000))]); }
          finally{ Object.defineProperty(Animation.prototype, 'currentTime', d); }
          return { got: !!sp && sp !== 'timeout', distinct: seen.size }; }""", [cid, name])
        check("%s: L. %s's %s plays through its recording (%d distinct times set)" % (label, cid, name, r["distinct"]),
              r["got"] and r["distinct"] >= 20, r)
    ctx.close()


def chat_open(br):
    print("\nM. the chat sheet slides up on a flat fill, then turns to glass")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    pg.evaluate(CLEAN)
    pg.evaluate("""() => { const p = document.querySelector('.chatdock-panel'); window.__tr = [];
      const L = () => { const cs = getComputedStyle(p); __tr.push({ top: p.getBoundingClientRect().top, bf: cs.backdropFilter, wbf: cs.webkitBackdropFilter || '' });
        if(__tr.length < 90) requestAnimationFrame(L); };
      requestAnimationFrame(L); openChatDock(); }""")
    time.sleep(1.6)
    tr = pg.evaluate("() => __tr")
    end = tr[-1]["top"]
    moving = [f for f in tr if f["top"] > end + 2]
    blurred = [f for f in moving if f["bf"] not in ("none", "") or f["wbf"] not in ("none", "")]
    check("%s: M. no backdrop blur on any frame of the slide up (%d of %d moving frames blurred)" % (label, len(blurred), len(moving)),
          len(moving) >= 3 and not blurred, (len(moving), blurred[:2]))
    check("%s: M. at rest it is glass again (%s)" % (label, tr[-1]["bf"]), tr[-1]["bf"] not in ("none", ""), tr[-1])
    ctx.close()


def calendar(br):
    print("\nN. the month scrolls the page, and is one card")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, touch=True, dpr=dpr, init=IPHONE_INIT)
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { document.getElementById('splashscreen')?.remove(); showCalendarTab(); }")
    pg.wait_for_timeout(2500)
    pg.evaluate(CLEAN)
    r = pg.evaluate("""() => { const t = document.querySelector('#stage .screen-calendar');
      const cells = [...t.querySelectorAll('.cal-grid .cal-cell[data-date]')];
      const card = t.querySelector('.cal-monthview'), cs = getComputedStyle(card);
      const nav = t.querySelector('.cal-grid-nav'), kids = nav ? [...nav.children].filter(e => getComputedStyle(e).display !== 'none') : [];
      const tops = kids.map(e => { const r = e.getBoundingClientRect(); return Math.round(r.top + r.height / 2); });
      const title = t.querySelector('.cal-grid-month').getBoundingClientRect();
      const cls = cells.filter(c => c.classList.contains('cal-cell-class') && !c.classList.contains('cal-cell-sel') && !c.classList.contains('cal-cell-today'));
      const bgOf = c => { const s = getComputedStyle(c); return s.backgroundImage !== 'none' || !/rgba\\(0, 0, 0, 0\\)|transparent/.test(s.backgroundColor); };
      return { cells: cells.length, cellSw: cells.filter(c => c.querySelector('.nova-hsw')).length,
        otherSw: t.querySelectorAll('.cal-grid-arrow > .nova-hsw, .nova-hsw').length,
        card: cs.backgroundImage !== 'none' && parseFloat(cs.borderTopWidth) >= 1,
        holds: ['.cal-grid-nav', '.cal-grid', '.cal-grid-legend', '.cal-daycard'].every(s => card.contains(t.querySelector(s))),
        oneRow: tops.length >= 3 && Math.max(...tops) - Math.min(...tops) <= 4,
        titleLeft: kids.every(e => e === t.querySelector('.cal-grid-month') || e.getBoundingClientRect().left >= title.right - 1),
        pill: !!t.querySelector('.cal-grid-nav .cal-action-btn'),
        tiles: cls.filter(bgOf).length, classDays: cls.length }; }""")
    check("%s: N. on an iPhone no day of the month carries a native switch (%d of %d), the page still has its switches (%d)"
          % (label, r["cellSw"], r["cells"], r["otherSw"]), r["cells"] >= 28 and r["cellSw"] == 0 and r["otherSw"] >= 1, r)
    check("%s: N. the month is one card holding its header, days, key and picked day" % label, r["card"] and r["holds"], r)
    check("%s: N. the title on the left, Today and the arrows beside it in one row" % label, r["oneRow"] and r["titleLeft"] and r["pill"], r)
    check("%s: N. a class day is a number, not a tile (%d of %d tiled)" % (label, r["tiles"], r["classDays"]),
          r["classDays"] >= 5 and r["tiles"] == 0, r)
    ctx.close()


def boards(br):
    print("\nO. This Week and Hundos in Overall's table")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    # round 2: This Week and Hundos carry ONLY their own column
    for tab, heads in (("This Week", ["XP"]), ("Hundos", ["Hundos"]), ("Overall", ["Rank", "Level", "Badges"])):
        pg.evaluate("() => showRankings()")
        pg.wait_for_timeout(700)
        pg.evaluate(CLEAN)
        pg.evaluate("t => { const b = [...document.querySelectorAll('#stage button, #stage [role=tab]')].find(b => b.textContent.trim() === t); b && b.click(); }", tab)
        pg.wait_for_timeout(900)
        r = pg.evaluate("""() => { const h = document.querySelector('#stage .rank-row-head');
          const rows = [...document.querySelectorAll('#stage .rank-row:not(.rank-row-head)')];
          return { head: h ? [...h.querySelectorAll('.rank-col-head')].map(e => e.textContent.trim()) : null,
            rows: rows.length, ncols: rows.map(r => r.querySelectorAll(':scope > .rank-cols > .rank-col').length),
            icon: !!document.querySelector('#stage .rank-me-btn svg') }; }""")
        check("%s: O. %s has the header %s and every row exactly those columns (%s)" % (label, tab, r["head"], r["ncols"]),
              r["head"] == heads and r["rows"] >= 1 and all(n == len(heads) for n in r["ncols"]), r)
    # MOVED IN 327z13: "not sure why the find me button has a blue arrow thing? Remove that"
    check("%s: O. Find me is the word alone, no icon" % label, not r["icon"], r)
    ctx.close()


def daily(br):
    print("\nP. the daily button: lit while it waits, a clock once answered")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    READ = """() => { const b = document.querySelector('.daily-question-fab'), ring = b.querySelector('.dq-ring'), cs = getComputedStyle(b);
      const prog = ring && ring.querySelector('.dq-ring-prog'), k = ring ? ring.querySelector('svg').getBoundingClientRect().width / 100 : 0;
      return { ready: b.classList.contains('is-ready'), ringOp: ring ? +getComputedStyle(ring).opacity : 0,
        progPx: prog ? parseFloat(getComputedStyle(prog).strokeWidth) * k : 0,
        lit: /radial-gradient/.test(cs.backgroundImage), img: cs.backgroundImage }; }"""
    pg.evaluate("() => { store.dailyQuestionDate = ''; showHome(); }")
    pg.wait_for_timeout(1500)
    pg.evaluate(CLEAN)
    a = pg.evaluate(READ)
    check("%s: P. waiting, the button is lit glass with no ring drawn on it" % label, a["ready"] and a["lit"] and a["ringOp"] == 0, a)
    pg.evaluate("() => { store.dailyQuestionDate = dailyPeriodKey(); showHome(); }")
    pg.wait_for_timeout(1500)
    b = pg.evaluate(READ)
    # round 2: answered is the lit orb's quieter sibling - a different, fainter
    # glass (not the waiting one), and the slim arc
    check("%s: P. answered, not the waiting orb, and a slim arc (%.1fpx)" % (label, b["progPx"]),
          b["img"] != a["img"] and b["ringOp"] > .9 and 0 < b["progPx"] <= 2.0, b)
    ctx.close()


def profile_friends(br):
    print("\nQ. Profile in three glass cards; Friends in the chat")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { showProfile('profile'); }")
    pg.wait_for_timeout(1500)
    pg.evaluate(CLEAN)
    r = pg.evaluate("""() => { const tab = document.querySelector('#stage .profile-identity-tab');
      const kids = tab ? [...tab.children].filter(e => getComputedStyle(e).display !== 'none') : [];
      const hero = document.querySelector('#stage .profile-hero'), cs = getComputedStyle(hero);
      const probe = document.createElement('div'); probe.style.cssText = 'position:fixed;background:var(--pop-bg-card);backdrop-filter:var(--surface-blur)'; document.body.appendChild(probe);
      const want = getComputedStyle(probe).backgroundImage, blur = getComputedStyle(probe).backdropFilter; probe.remove();
      const rects = kids.map(e => e.getBoundingClientRect());
      return { kinds: kids.map(e => e.classList.contains('profile-hero') ? 'hero' : e.classList.contains('pf-goal') ? 'goal' : e.classList.contains('pf-case') ? 'case' : e.className),
        nested: !!hero.querySelector('.pf-goal, .pf-case'), friendBox: !!document.querySelector('#stage .profile-friendcard'),
        glass: cs.backgroundImage.endsWith(want.slice(want.indexOf('linear-gradient'))) && cs.backdropFilter === blur,
        surface: /linear-gradient\(rgb\(20, 23, 28\) 0%, rgb\(11, 13, 17\) 100%\)$/.test(cs.backgroundImage),
        gaps: rects.slice(1).map((r, i) => Math.round(r.top - rects[i].bottom)) }; }""")
    check("%s: Q. Profile is three cards - you, the next rank, the case - none inside another (%s)" % (label, r["kinds"]),
          r["kinds"][:3] == ["hero", "goal", "case"] and not r["nested"] and all(g >= 8 for g in r["gaps"]), r)
    # SUPERSEDED LATER IN 327z (notes: "THE THREE PROFILE CARDS, ONE FAMILY: hero, next-rank card and the case's body all on the person
    # card's surface (linear #14171C -> #0B0D11 ...), each with one colour pool at the top"): the top card is that surface, under its pools
    check("%s: Q. the top card is on the person card's surface (#14171C -> #0B0D11, under its pools)" % label, r["surface"], r)
    check("%s: Q. no Friends box on Profile" % label, not r["friendBox"], r)
    hid = pg.evaluate("""async () => { showProfile('stats'); await new Promise(r => setTimeout(r, 700));
      const t = document.querySelector('#stage .profile-identity-tab'); return t ? { hidden: t.hidden, shown: getComputedStyle(t).display !== 'none' } : null; }""")
    check("%s: Q. on the Stats tab the Profile cards are not shown" % label, hid and hid["hidden"] and not hid["shown"], hid)
    pg.evaluate("() => { showCalendarTab(); }")
    pg.wait_for_timeout(1200)
    pg.evaluate(CLEAN)
    pg.evaluate("() => { chatDockTab = 'friends'; openChatDock(); }")
    pg.wait_for_timeout(900)
    a = pg.evaluate("""() => { const bar = document.querySelector('.chatdock-panel .chatdock-friendsbar'); const b = bar && bar.querySelector('button');
      const out = { bar: !!bar, h: b ? Math.round(b.getBoundingClientRect().height) : 0, first: !!(bar && bar === bar.parentElement.firstElementChild || (bar && bar.previousElementSibling && bar.previousElementSibling.classList.contains('chatdock-note'))) };
      if(b) b.click(); return out; }""")
    pg.wait_for_timeout(1200)
    b = pg.evaluate("""() => ({ friends: !!document.querySelector('#stage > .screen-friends'), back: (document.querySelector('#stage .back-link') || {}).textContent,
      open: chatDockOpen, lit: [...document.querySelectorAll('.bottomtab.active')].map(x => x.id) })""")
    check("%s: Q. the chat's Friends tab opens with a Friends bar, its button 44px+" % label, a["bar"] and a["h"] >= 44, a)
    check("%s: Q. it opens Friends over the tab it came from: back to %s, %s lit, the chat shut" % (label, b["back"], b["lit"]),
          # MOVED IN 327z15: "it says back to home but shouldn't it say back to
          # chat" - opened from the chat, Friends goes back to the chat
          b["friends"] and "Chat" in (b["back"] or "") and b["lit"] == ["bottomtab-calendar"] and not b["open"], b)
    pg.evaluate("() => document.querySelector('#stage .back-link').click()")
    pg.wait_for_timeout(1000)
    c = pg.evaluate("() => !!document.querySelector('#stage > .screen-calendar-tab') && chatDockOpen && chatDockTab === 'friends'")
    check("%s: Q. and back lands on the Calendar with the chat open on Friends (327z15)" % label, c, c)
    ctx.close()


def daily_mark(br):
    print("\nR. the daily button's mark is centred")
    import io
    from PIL import Image
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    for done in (False, True):
        pg.evaluate("d => { store.dailyQuestionDate = d ? dailyPeriodKey() : ''; showHome(); }", done)
        pg.wait_for_timeout(1500)
        pg.evaluate(CLEAN)
        box = pg.evaluate("""() => { const f = document.querySelector('.daily-question-fab');
          f.style.cssText += ';background:#000 !important;box-shadow:none !important;border-color:transparent !important;animation:none !important';
          f.classList.remove('is-ready', 'is-fresh'); f.querySelectorAll('.dq-ring').forEach(r => r.style.opacity = 0);
          const g = f.querySelector('.dq-glyph'); g.style.opacity = 1; g.style.color = '#fff';
          const r = f.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height,
            tick: [...f.querySelectorAll('.dq-mark')].some(m => !m.classList.contains('dq-mark-q') && getComputedStyle(m).display !== 'none'),
            q: !!f.querySelector('.dq-mark-q') && getComputedStyle(f.querySelector('.dq-mark-q')).display !== 'none' }; }""")
        pg.wait_for_timeout(250)
        im = Image.open(io.BytesIO(pg.screenshot(clip={"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]}))).convert("L")
        W, H = im.size
        pts = [(x, y) for y in range(H) for x in range(W) if im.getpixel((x, y)) > 140]
        if not pts:
            check("%s: R. the mark is drawn (%s)" % (label, "answered" if done else "waiting"), False, box)
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        k = W / box["w"]
        dx = ((min(xs) + max(xs)) / 2 - W / 2) / k; dy = ((min(ys) + max(ys)) / 2 - H / 2) / k
        check("%s: R. %s, the \"?\" is shown, no tick, its ink centred (%.2f, %.2f px off)" % (label, "answered" if done else "waiting", dx, dy),
              abs(dx) <= .5 and abs(dy) <= .5 and box["q"] and not box["tick"], (dx, dy, box))
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("L", chars_move), ("M", chat_open), ("N", calendar), ("O", boards), ("P", daily), ("Q", profile_friends), ("R", daily_mark)):
            if k in ONLY:
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
