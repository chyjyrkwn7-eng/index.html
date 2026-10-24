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
  O. "can [hundos] and xp be like [overall] ... the title header thing":
     This Week and Hundos carry Overall's header and three columns, the
     third being the board's own number; Find me carries an icon.
  P. "The daily question button did not get better": waiting, the button is
     lit in the rank's colour with no ring drawn on it; answered, it is the
     plain glass with a slim arc.
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

ONLY = os.environ.get("B327Z12_ONLY", "LMNOP")
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
    for tab, third in (("This Week", "XP"), ("Hundos", "Hundos"), ("Overall", "Badges")):
        pg.evaluate("() => showRankings()")
        pg.wait_for_timeout(700)
        pg.evaluate(CLEAN)
        pg.evaluate("t => { const b = [...document.querySelectorAll('#stage button, #stage [role=tab]')].find(b => b.textContent.trim() === t); b && b.click(); }", tab)
        pg.wait_for_timeout(900)
        r = pg.evaluate("""() => { const h = document.querySelector('#stage .rank-row-head');
          const rows = [...document.querySelectorAll('#stage .rank-row:not(.rank-row-head)')];
          return { head: h ? [...h.querySelectorAll('.rank-col-head')].map(e => e.textContent.trim()) : null,
            rows: rows.length, cols: rows.filter(r => r.querySelectorAll(':scope > .rank-cols > .rank-col').length === 3).length,
            icon: !!document.querySelector('#stage .rank-me-btn svg') }; }""")
        check("%s: O. %s has the header %s and every row three columns (%d of %d)" % (label, tab, r["head"], r["cols"], r["rows"]),
              r["head"] and len(r["head"]) == 3 and r["head"][2].lower() == third.lower() and r["rows"] >= 1 and r["cols"] == r["rows"], r)
    check("%s: O. Find me carries an icon" % label, r["icon"], r)
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
        lit: /radial-gradient/.test(cs.backgroundImage), img: cs.backgroundImage.slice(0, 80) }; }"""
    pg.evaluate("() => { store.dailyQuestionDate = ''; showHome(); }")
    pg.wait_for_timeout(1500)
    pg.evaluate(CLEAN)
    a = pg.evaluate(READ)
    check("%s: P. waiting, the button is lit glass with no ring drawn on it" % label, a["ready"] and a["lit"] and a["ringOp"] == 0, a)
    pg.evaluate("() => { store.dailyQuestionDate = dailyPeriodKey(); showHome(); }")
    pg.wait_for_timeout(1500)
    b = pg.evaluate(READ)
    check("%s: P. answered, the plain glass and a slim arc (%.1fpx)" % (label, b["progPx"]),
          not b["lit"] and b["ringOp"] > .9 and 0 < b["progPx"] <= 2.0, b)
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("L", chars_move), ("M", chat_open), ("N", calendar), ("O", boards), ("P", daily)):
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
