#!/usr/bin/env python3
"""Build 325, stream g: Nova's weekly recap and the Calendar tab.

Madison, Oct 18:
  "The nova weekly recap, ensure the honorable mention makes sense it isn't
   one of the top 3 players for the week. Ensure the description seem game
   like and are well made."
  "The calendar is missing the key dots though, the red ones for no class.
   The yellow ones, and the others. We need some dots for the 4 big tests,
   the level 1 exam, level 2 exam, level 3 exam and the state test."

Every check here fails on the build before (6fc16b7):
  python3 tools/check-b325-g.py                         # this build
  python3 tools/check-b325-g.py --against /path/old/index.html
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
check, booted, USED_ACCOUNT, FAILURES = cb.check, cb.booted, cb.USED_ACCOUNT, cb.FAILURES

# ---------------------------------------------------------------------------
# THE RECAP. Six rows: the podium (Jordan, Alex, Riley) best at everything;
# "jordan " - the podium's Jordan under a second row (a second sign-up),
# off the podium on XP but the natural winner of every mention; Sam next;
# Chris last. The mention must be Sam every time: never a podium row and
# never a podium NAME.
RECAP_JS = r"""async (opt) => {
  const out = { err: null };
  try{
    document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
    const lw = lastWeekKey(), wk = weekKeyNow();
    const row = (pub, name, x, o) => ({ pub, firstName: name, avatarChar: 'ninja', week: wk, weekPoints: 5, rawWeekPoints: 5,
      prevWeek: lw, prevWeekPoints: x, pwk: Object.assign({ k: lw, x, p: null }, o) });
    const rows = () => [
      row('a1', 'Jordan', 9000, { t: 60, h: 20, d: 7, m: 2000, s: 7, b: 500 }),
      row('b2', 'Alex',   8000, { t: 55, h: 18, d: 7, m: 1900, s: 7, b: 400 }),
      row('c3', 'Riley',  7000, { t: 50, h: 16, d: 7, m: 1800, s: 7, b: 300 }),
      row('j9', ' jordan ', 3000, { t: 40, h: 12, d: 6, m: 1500, s: 6, b: 100 }),
      row('d4', 'Sam',    6000, opt.samLow ? { t: 1, h: 0, d: 1, m: 10, s: 1, b: 5990 } : { t: 30, h: 9, d: 5, m: 900, s: 5, b: 4000 }),
      row('e5', 'Chris',  5000, opt.samLow ? { t: 1, h: 0, d: 1, m: 10, s: 1, b: 4990 } : { t: 20, h: 3, d: 3, m: 300, s: 3, b: 4500 })
    ];
    store.weekKey = wk; store.weekPoints = 5; store.prevWeekKey = lw; store.prevWeekPoints = 0;
    try{ localStorage.removeItem('class26e.weekrecap.v1'); localStorage.removeItem('class26e.weektop.v1'); }catch(e){}
    const cats = RECAP_MENTIONS.map(d => d.cat);
    window.weekRecapMentionCount = () => 1;
    window.weekRecapPlanned = () => [];
    out.cats = cats;
    out.per = {};
    for(const cat of cats){
      window.weekRecapCatOrder = () => [cat];
      const r = buildWeekRecap(rows());
      const res = { top: r.top.map(t => t.name), ments: r.mentions.map(m => ({ cat: m.cat, name: m.name, v: m.value })) };
      if(!opt.samLow && r.mentions.length){
        const ui = buildWeekRecapStage(r);
        document.body.appendChild(ui.root);
        const card = ui.root.querySelector('.wr-mention');
        res.title = card ? (card.querySelector('.wr-mcat') || {}).textContent : null;
        res.line = card ? (card.querySelector('.wr-mval') || {}).textContent : null;
        res.strip = (() => { const b = ui.root.querySelector('.wr-page-mentions .wr-minibox');
          if(!b) return null;
          const list = ui.root.querySelector('.wr-mlist');
          return { cap: !!b.querySelector('.wr-mini-cap'), names: [...b.querySelectorAll('.wr-mini-name')].map(n => n.textContent),
                   places: [...b.querySelectorAll('.wr-mini-place')].map(n => n.textContent), apart: !!list && !b.contains(list) }; })();
        ui.root.remove();
        res.said = weekRecapLines(r).map(l => l.text);
      }
      out.per[cat] = res;
    }
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""


def recap_section(br):
    print("\n1. the weekly recap: an honorable mention is never the top 3, and reads as an award")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    a = pg.evaluate(RECAP_JS, {"samLow": False})
    b = pg.evaluate(RECAP_JS, {"samLow": True})
    ctx.close()
    if a.get("err") or b.get("err"):
        check("the recap could be built at all", False, a.get("err") or b.get("err"))
        return
    import re
    want = ["hundos", "tests", "daily", "improve", "study", "streak"]
    for cat in want:
        res = (a.get("per") or {}).get(cat) or {}
        ments = res.get("ments") or []
        check("%s: the natural winner is on the podium (or is a podium name on a second row) - the next one off it is named"
              % cat, [m["name"] for m in ments] == ["Sam"] and [m["cat"] for m in ments] == [cat],
              [res.get("top"), ments])
    # only the podium and its second row qualify: the mention is dropped
    dropped = {c: [m["name"] for m in ((b.get("per") or {}).get(c) or {}).get("ments") or []] for c in want}
    check("when only the podium (and a podium name) qualify, the mention is dropped, never given to them",
          all(v == [] for v in dropped.values()), dropped)
    # the words: an award, what was done, no claim the podium may have beaten
    SUPER = re.compile(r"\b(most|longest|best|highest|top|biggest)\b", re.I)
    bad = []
    for cat in want:
        res = (a.get("per") or {}).get(cat) or {}
        title, line, said = res.get("title") or "", res.get("line") or "", res.get("said") or []
        v = (res.get("ments") or [{}])[0].get("v")
        say = next((t for t in said if "Sam" in t), "")
        num = "{:,}".format(v) if isinstance(v, int) else str(v)
        if cat == "study" and isinstance(v, int):
            num = "%dh" % (v // 60)
        ok = (title and not SUPER.search(title) and not SUPER.search(line) and not SUPER.search(say)
              and num in line and title.lower() in say.lower() and "Sam" in say)
        if not ok:
            bad.append([cat, title, line, say])
    check("every mention is a named award: the card's title is what Nova announces, the line says the number, "
          "and nothing claims a 'most' the podium may have beaten", not bad, bad)
    st = ((a.get("per") or {}).get("tests") or {}).get("strip")
    check("the top 3 over the mentions is captioned, numbered and set apart, so it cannot read as the first three mentions",
          bool(st) and st["cap"] and st["names"] == ["Jordan", "Alex", "Riley"] and st["places"] == ["1", "2", "3"] and st["apart"], st)


# ---------------------------------------------------------------------------
# THE CALENDAR. The date is pinned, the tab built, and the grid walked.
CAL_JS = r"""async ([iso, months]) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const RealDate = window.__RealDate || Date; window.__RealDate = RealDate;
  const off = new RealDate(iso + 'T10:00:00').getTime() - RealDate.now();
  window.Date = class extends RealDate { constructor(...a){ if(a.length) super(...a); else super(RealDate.now() + off); }
                                         static now(){ return RealDate.now() + off; } };
  const out = { err: null };
  try{
    document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
    showHome(); await wait(250);
    (typeof showCalendarTab === 'function' ? showCalendarTab : showCalendar)(); await wait(700);
    document.querySelectorAll('#tour-overlay, #tour-tooltip, .daily-alert, .toast').forEach(x => x.remove());
    const tab = document.querySelector('#stage > .screen-calendar');
    const vis = el => { if(!el) return false; const cs = getComputedStyle(el), r = el.getBoundingClientRect();
      return cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > .5 && r.width >= 3 && r.height >= 3; };
    const look = el => { if(!el) return null; const cs = getComputedStyle(el);
      return { bg: cs.backgroundColor + '|' + cs.backgroundImage, tf: cs.transform, rad: cs.borderRadius, w: Math.round(el.getBoundingClientRect().width) }; };
    out.big = typeof isBigExamDay === 'function' ? CALENDAR_DATA.filter(isBigExamDay).map(e => [e.date, testNameOf(e)]) : null;
    /* walk the asked months */
    const nav = [...tab.querySelectorAll('.cal-grid-arrow')];
    const monthKey = () => { const t = tab.querySelector('.cal-grid-month').textContent; return t; };
    out.months = {};
    for(const m of months){
      for(let i = 0; i < 24 && nav[0] && !nav[0].disabled; i++){ nav[0].click(); }
      await wait(60);
      for(let i = 0; i < 24 && monthKey() !== m && !nav[1].disabled; i++){ nav[1].click(); }
      await wait(120);
      const cells = [...tab.querySelectorAll('.cal-grid .cal-cell[data-date]')].map(c => {
        const ds = c.dataset.date, e = CALENDAR_DATA.find(x => x.date === ds) || null;
        const dots = [...c.querySelectorAll('.cal-cell-dots > i')];
        return { ds, kind: !e ? 'none' : e.holiday ? 'off' : (typeof isBigExamDay === 'function' ? isBigExamDay(e) : (isExamDay(e) && !/TEST\s*#/i.test(e.text))) ? 'big' : isExamDay(e) ? 'test' : 'class',
                 cls: c.className, dots: dots.filter(vis).map(d => ({ c: d.className, l: look(d) })) };
      });
      out.months[m] = cells;
    }
    /* the key */
    const lg = tab.querySelector('.cal-grid-legend'), grid = tab.querySelector('.cal-grid'), day = tab.querySelector('.cal-daycard');
    out.key = lg ? { items: [...lg.children].map(it => { const d = it.querySelector('i'); return { t: it.textContent.trim(), vis: vis(d), l: look(d) }; }),
                     afterGrid: !!(grid && day && lg.getBoundingClientRect().top > grid.getBoundingClientRect().bottom - 1 && lg.getBoundingClientRect().bottom <= day.getBoundingClientRect().top + 1),
                     inside: [...lg.children].every(it => { const r = it.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth; }) } : null;
    /* next test, today, week */
    const nt = tab.querySelector('.cal-nexttest-card');
    out.next = nt ? { date: nt.dataset.date || null, big: nt.classList.contains('is-bigexam'), chipMark: vis(nt.querySelector('.cal-nt-big .cal-cell-dot-big')),
                      title: (nt.querySelector('.cal-nt-title') || {}).textContent || '', topics: [...nt.querySelectorAll('.cal-topics-list li')].map(li => li.textContent) } : null;
    /* the big exams card */
    const bc = tab.querySelector('.cal-big-card');
    out.bigCard = bc && vis(bc) ? { rows: [...bc.querySelectorAll('.cal-big-row')].map(r => ({ d: r.dataset.date, n: (r.querySelector('.cal-big-name') || {}).textContent,
                      c: (r.querySelector('.cal-big-count') || {}).textContent, mark: vis(r.querySelector('.cal-cell-dot-big')) })) } : null;
    if(bc){ const r = bc.querySelector('.cal-big-row[data-date="2027-06-21"]'); if(r){ r.click(); await wait(300);
      out.pick = { sel: (tab.querySelector('.cal-cell-sel') || {}).dataset ? tab.querySelector('.cal-cell-sel').dataset.date : null,
                   card: (tab.querySelector('.cal-daycard') || {}).textContent || '' }; } }
    /* Oct 26's own day card */
    const pick = async ds => { const idx = ds; for(let i = 0; i < 24 && nav[0] && !nav[0].disabled; i++) nav[0].click();
      const want = new Date(+ds.slice(0, 4), +ds.slice(5, 7) - 1, 1).toLocaleString('en-US', { month: 'long' }) + ' ' + ds.slice(0, 4);
      for(let i = 0; i < 24 && monthKey() !== want && !nav[1].disabled; i++) nav[1].click();
      const c = tab.querySelector('.cal-cell[data-date="' + ds + '"]'); if(c) c.click(); await wait(150);
      return [...tab.querySelectorAll('.cal-daycard .cal-topics-list li')].map(li => li.textContent); };
    out.oct26 = await pick('2026-10-26');
    out.scrollX = document.documentElement.scrollWidth - innerWidth;
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""

BIG = [["2027-01-19", "Level One Final"], ["2027-06-10", "Level Two Final"],
       ["2027-06-21", "Level Three Final Exam"], ["2027-07-08", "State test"]]


def calendar_section(br):
    print("\n2. the Calendar tab: the key dots on every device, the big four exams, the posted topics")
    for dev, w, h in cb.DEVICES:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        a = pg.evaluate(CAL_JS, ["2026-10-18", ["October 2026", "January 2027", "March 2027", "June 2027", "July 2027"]])
        ctx.close()
        if a.get("err"):
            check("%s: the Calendar tab could be read" % dev, False, a["err"])
            continue
        check("%s: isBigExamDay is the four big exams - Level One, Two and Three finals and the state test" % dev,
              a.get("big") == BIG, a.get("big"))
        cells = [c for m in (a.get("months") or {}).values() for c in m]
        problems = []
        looks = {}
        for c in cells:
            k, dots = c["kind"], c["dots"]
            if k == "none":
                if dots:
                    problems.append([c["ds"], "dot on a day with nothing on"])
                continue
            if not dots:
                problems.append([c["ds"], k, "no visible dot"])
                continue
            mark = dots[-1]["l"]
            looks.setdefault(k, set()).add(mark["bg"] + mark["tf"] + mark["rad"])
            if k in ("test", "big") and len(dots) != 2:
                problems.append([c["ds"], k, "wants a class dot and its own mark", len(dots)])
        # each kind has ONE look, and the four looks are all different
        one = all(len(v) == 1 for v in looks.values())
        distinct = len(set(next(iter(v)) for v in looks.values())) == len(looks) == 4
        big_l = next(iter(looks.get("big", {""})))
        test_l = next(iter(looks.get("test", {""})))
        check("%s: every class day, test, big exam and no-class day in the grid shows its dot (Oct, Jan, Mar, Jun, Jul), "
              "one look per kind and four different looks" % dev, not problems and one and distinct,
              [problems[:6], {k: len(v) for k, v in looks.items()}])
        check("%s: a big exam's mark is not the test's round amber dot (its own shape)" % dev,
              bool(big_l) and big_l != test_l and "matrix" in big_l, [big_l[-80:], test_l[-60:]])
        mar = [c for c in (a.get("months") or {}).get("March 2027", []) if "2027-03-08" <= c["ds"] <= "2027-03-12"]
        check("%s: spring break (Mar 8-12) is no class, not five class days" % dev,
              len(mar) == 5 and all(c["kind"] == "off" for c in mar), [(c["ds"], c["kind"]) for c in mar])
        key = a.get("key") or {}
        items = key.get("items") or []
        cell_look = {k: next(iter(v)) for k, v in looks.items()}
        key_looks = [i["l"]["bg"] + i["l"]["tf"] + i["l"]["rad"] if i.get("l") else None for i in items]
        check("%s: the key sits right under the grid, shows a visible mark for each of the four kinds, "
              "each mark the same as the grid's" % dev,
              len(items) == 4 and all(i["vis"] for i in items) and key.get("afterGrid") and key.get("inside")
              and sorted(key_looks) == sorted(cell_look.values()) and (a.get("scrollX") or 0) <= 0,
              [[i["t"] for i in items], [i["vis"] for i in items], key.get("afterGrid"), key.get("inside"), a.get("scrollX")])
        bc = a.get("bigCard") or {}
        rows = bc.get("rows") or []
        check("%s: a Big exams card lists the four in order, each with the key's mark and how far off it is" % dev,
              [[r["d"], r["n"]] for r in rows] == BIG and all(r["mark"] for r in rows)
              and rows and rows[0]["c"] == "93 days", rows)
        pk = a.get("pick") or {}
        check("%s: tapping a big exam picks its day in the month" % dev,
              pk.get("sel") == "2027-06-21" and "Final Exam" in (pk.get("card") or ""), pk)
        nx = a.get("next") or {}
        check("%s: Oct 18: Next test is Test #5 with the posted topic (Penal Code slides 124-256), and Oct 26 shows 256-578" % dev,
              nx.get("date") == "2026-10-19" and any("124" in t and "256" in t for t in nx.get("topics") or [])
              and not nx.get("big") and any("256" in t and "578" in t for t in a.get("oct26") or []),
              [nx, a.get("oct26")])
        # the week before the Level One Final: the Next test card says it is one of the big four
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        j = pg.evaluate(CAL_JS, ["2027-01-15", ["January 2027"]])
        ctx.close()
        nj = j.get("next") or {}
        check("%s: Jan 15: Next test is the Level One Final, marked as a big exam with the key's diamond" % dev,
              nj.get("date") == "2027-01-19" and nj.get("title") == "Level One Final" and nj.get("big") and nj.get("chipMark"),
              [j.get("err"), nj])


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME, args=["--no-sandbox"])
        only = os.environ.get("ONLY", "")
        if not only or "recap" in only:
            recap_section(br)
        if not only or "cal" in only:
            calendar_section(br)
        br.close()
    print("\n%d failure(s)" % len(FAILURES))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
