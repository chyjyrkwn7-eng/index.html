#!/usr/bin/env python3
"""Build 326, package g: the weekly recap, the starfield, Home's spacing on a
phone, and the Calendar tab.

Madison, Oct 18 (second list):
  "The weekly recap, it's good but could also talk about people's hundos, or
   impressive study time? Idk. The description at the end where it talks
   about next weeks is anyone's and stuff is bad as well."
  "I like the background with the stars, I do kinda think it's a SMIDGE tiny
   bit too much"
  "the phone is where most people use this app, and I again, think the start
   studying button is slightly too low and the good morning and text about
   the button is slightly too low too."
  "the calendar tab ... clean it all up some. Also the key is cool with the
   orange big exam but it has a diamond, should just be a normal orange.
   Include the pt finals as orange too."

Every section fails on build 325 (5869856):
  python3 tools/check-b326-g.py
  python3 tools/check-b326-g.py --against /path/to/325/index.html
  ONLY=recap|sky|home|cal python3 tools/check-b326-g.py
"""
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
check, booted, USED_ACCOUNT, FAILURES = cb.check, cb.booted, cb.USED_ACCOUNT, cb.FAILURES

# ---------------------------------------------------------------------------
# 1. THE RECAP. check-behaviour's fixture (Ada, Bo, Cy on the podium; Di, Ed
# and the viewer off it), with this week's board under way: Ada 1,240, the
# viewer 420.
RECAP_JS = r"""async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const out = { err: null };
  try{
    document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
    """ + cb.RECAP_FIXTURE_JS + r"""
    __recapMine(3000);
    const thisWeek = rows => { rows.forEach((r, i) => { r.weekPoints = [1240, 600, 900, 300, 150, 0][i] || 0; r.rawWeekPoints = r.weekPoints; }); store.weekPoints = 420; return rows; };
    const rows = thisWeek(__recapRows());
    try{ localStorage.removeItem('class26e.weekrecap.v1'); }catch(e){}
    const r = buildWeekRecap(rows);
    out.top = r.top.map(t => t.name);
    out.ments = r.mentions.map(m => ({ cat: m.cat, name: m.name }));
    out.cw = r.classWeek || null;
    out.lines = weekRecapLines(r).map(l => l.text);
    /* the expected totals, from the fixture's own blocks */
    out.wantH = rows.reduce((a, e) => a + ((e.pwk && e.pwk.h) || 0), 0);
    out.wantM = rows.reduce((a, e) => a + ((e.pwk && e.pwk.m) || 0), 0);
    /* the rotation never hands out hundos or study as a mention any more */
    const weeks = []; { const p = lw.split('-').map(Number); for(let i = 0; i < 12; i++){ const d = new Date(p[0], p[1] - 1, p[2] + 7 * i); weeks.push(dayKey(d)); } }
    out.rot = weeks.map(k => weekRecapMentions(__recapRows().map(x => { x.pwk = Object.assign({}, x.pwk, { k }); x.prevWeek = k; return x; }),
      [{ pub: 'a1', name: 'Ada' }, { pub: 'b2', name: 'Bo' }, { pub: 'c3', name: 'Cy' }], k).map(m => m.cat));
    /* fewer than three people report hundos: no hundo total, no award */
    const thin = thisWeek(__recapRows()).map((x, i) => { if(i > 1) x.pwk = Object.assign({}, x.pwk, { h: null }); return x; });
    const rt = buildWeekRecap(thin);
    out.thin = rt.classWeek ? { totals: rt.classWeek.totals, awards: rt.classWeek.awards.map(a => a.cat) } : null;
    /* the ending before anybody has scored this week: how far off the podium */
    const quiet = __recapRows().map(x => { x.weekPoints = 0; x.rawWeekPoints = 0; return x; }); store.weekPoints = 0;
    out.closeQuiet = typeof weekRecapClose === 'function' ? weekRecapClose(quiet, r.top, { inTop: -1, place: 6, pts: 3000 }) : null;
    out.closeFirst = typeof weekRecapClose === 'function' ? weekRecapClose(quiet, r.top, { inTop: 0, place: 1, pts: 9000 }) : null;
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""

# Plays the recap for real and reads the class's page at its fullest.
PLAY_JS = r"""async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const out = { err: null };
  try{
    document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
    """ + cb.RECAP_FIXTURE_JS + r"""
    __recapMine(3000);
    const rows = __recapRows();
    try{ localStorage.removeItem('class26e.weekrecap.v1'); }catch(e){}
    const el = playWeekRecap(buildWeekRecap(rows));
    out.skip = !!(el && el.querySelector('.nt-skip'));
    /* MOVED IN 327 (b327c): the two awards are honorable mentions on a page
       of their own (.wr-page-awards) before the class's totals, and the
       class's page - the last - holds three tiles: hundos, tests, study */
    const seen = { tiles: 0, awards: 0, bad: [], nums: [] };
    const measure = pg => {
      const box = el.querySelector('.wr-pages').getBoundingClientRect();
      pg.querySelectorAll('.wr-tile, .wr-award, .wr-subwrap').forEach(c => {
        const r = c.getBoundingClientRect(), cs = getComputedStyle(c);
        if(cs.display === 'none' || !r.width) return;
        if(r.left < -.5 || r.right > innerWidth + .5) seen.bad.push('x ' + c.className);
        if(r.top < box.top - 1 || r.bottom > box.bottom + 1) seen.bad.push('y ' + c.className + ' ' + Math.round(r.top) + '..' + Math.round(r.bottom) + ' in ' + Math.round(box.top) + '..' + Math.round(box.bottom));
      });
    };
    for(let k = 0; k < 40 && el && el.__nova; k++){
      const n = el.__nova;
      if(n.typing){ n.advance(); await wait(60); }
      await wait(700);
      const pa = el.querySelector('.wr-page-awards.is-on');
      if(pa && pa.querySelectorAll('.wr-award.is-in').length === pa.querySelectorAll('.wr-award').length && !seen.awards){
        seen.awards = pa.querySelectorAll('.wr-award').length; measure(pa);
      }
      const pg = el.querySelector('.wr-page-class.is-on');
      if(pg){
        seen.tiles = pg.querySelectorAll('.wr-tile').length; measure(pg);
        seen.nums = [...pg.querySelectorAll('.wr-tile-num')].map(n => n.textContent);
        break;
      }
      if(n.index >= n.count - 1) break;
      n.advance(); await wait(250);
    }
    out.page = seen;
    out.scrollX = document.documentElement.scrollWidth - innerWidth;
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""


def recap_section(br):
    print("\n1. the weekly recap: hundos and study time every week, and an ending read off the board")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    a = pg.evaluate(RECAP_JS)
    ctx.close()
    if a.get("err"):
        check("the recap could be built", False, a["err"])
        return
    cw = a.get("cw") or {}
    tot = cw.get("totals") or {}
    check("the class's week totals the hundos and the study clock off everyone's published week",
          tot.get("hundos") == a.get("wantH") and tot.get("study") == a.get("wantM"), [tot, a.get("wantH"), a.get("wantM")])
    awards = cw.get("awards") or []
    top = set(n.lower() for n in a.get("top") or [])
    ment = set(m["name"].lower() for m in a.get("ments") or [])
    names = [x["name"].lower() for x in awards]
    check("a Flawless (hundos) and a Long Shift (study time) award every week, never the top 3, "
          "never anybody already named, never one person twice",
          [x["cat"] for x in awards] == ["hundos", "study"] and not (set(names) & top) and not (set(names) & ment)
          and len(set(names)) == len(names), [awards, sorted(top), sorted(ment)])
    rot = a.get("rot") or []
    check("hundos and study time are no longer drawn as rotating mentions (twelve weeks)",
          rot and all("hundos" not in w and "study" not in w for w in rot) and all(w for w in rot), rot)
    thin = a.get("thin")
    check("fewer than three people reporting hundos: no hundo total and no hundo award",
          thin is not None and "hundos" not in (thin.get("totals") or {}) and "hundos" not in (thin.get("awards") or []), thin)
    lines = a.get("lines") or []
    joined = " | ".join(lines)
    said_totals = any(("%d hundos" % (a.get("wantH") or -1)) in t and "study clock" in t for t in lines)
    said_awards = all(any(x["name"] in t and title in t for t in lines)
                      for x, title in zip(awards, ["Flawless", "Long Shift"]))
    check("Nova says the class's hundos and hours, then names both awards", said_totals and said_awards,
          [t for t in lines if "hundo" in t or "study" in t or "Flawless" in t or "Long Shift" in t])
    # MOVED IN 327 (b327c): "it needs to end with the class time and hundos
    # and tests completed and then that's it" - no closing line read off
    # this week's board any more; the class's totals are the last line
    check("the ending is the class's totals and nothing after them - no 'anyone's', no 'this week so far'",
          "anyone" not in joined.lower() and "so far" not in joined and lines and ("%d hundos" % (a.get("wantH") or -1)) in lines[-1],
          lines[-2:])
    check("he still says goodbye until next Tuesday, in his own voice", lines and "next Tuesday" in lines[-1], lines[-1:])
    cq, cf = a.get("closeQuiet") or {}, a.get("closeFirst") or {}
    check("before anybody has scored this week: the gap off the podium, or 'the one to catch' for last week's winner",
          cq.get("kind") == "podium" and cq.get("gap") == 4000 and cf.get("kind") == "defend", [cq, cf])
    for dev, w, h in [("iPhone SE (1st gen)", 320, 568), ("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11\"", 834, 1194)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        b = pg.evaluate(PLAY_JS)
        ctx.close()
        p = b.get("page") or {}
        check("%s: the class's page shows its three tiles and the awards page both awards, inside the stage and the screen, Skip kept" % dev,
              not b.get("err") and p.get("tiles") == 3 and p.get("awards") == 2 and not p.get("bad") and b.get("skip")
              and (b.get("scrollX") or 0) <= 0, [b.get("err"), p, b.get("skip")])


# ---------------------------------------------------------------------------
# 2. THE STARFIELD. The light the stars add to Home's frame, everything else
# hidden, on a 17 Pro Max at 3x: build 325 measured 499,129. A smidge less is
# 8-18% less - not the same, and not a different sky.
SKY_REF = 499129


def sky_section(br):
    print("\n2. the starfield: a smidge less")
    from PIL import Image, ImageChops
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, dpr=3)
    pg.evaluate("() => { document.querySelectorAll('.nova-talk,.daily-alert,.toast').forEach(n => n.remove()); showHome(); }")
    pg.wait_for_timeout(1500)
    pg.add_style_tag(content="body > *:not(script){ visibility:hidden !important; }")
    pg.wait_for_timeout(900)
    a = Image.open(io.BytesIO(pg.screenshot())).convert("L")
    pg.evaluate("document.documentElement.classList.remove('sky-ready')")
    pg.wait_for_timeout(900)
    b = Image.open(io.BytesIO(pg.screenshot())).convert("L")
    ctx.close()
    hist = ImageChops.subtract(a, b).histogram()
    light = sum(i * n for i, n in enumerate(hist))
    stars = sum(hist[31:])
    ratio = light / SKY_REF
    # MOVED IN BUILD 327: "a smidge smidge less" again - 326's 86% of 325 went
    # to ~72% (check-b327-d holds 65-88% of 326). What stays from 326: less
    # than 325, and still a sky.
    check("the stars add 60-92% of build 325's light to Home (less, same sky; 327 trimmed again)",
          0.60 <= ratio <= 0.92 and stars > 2000, "light %d (%.3f of %d), %d bright pixels" % (light, ratio, SKY_REF, stars))


# ---------------------------------------------------------------------------
# 3. HOME ON A PHONE: installed, with the real insets substituted in.
STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){},
       addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""
HOME_JS = r"""async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const kill = () => document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk,.daily-alert,.toast,#tour-overlay,#tour-tooltip').forEach(n => n.remove());
  kill(); showHome(); await wait(900); kill();
  const R = s => { const e = document.querySelector(s); if(!e) return null; const r = e.getBoundingClientRect(); return r.height ? r : null; };
  const b = R('#nextbtn'), tg = R('#stage .hometagline'), g = R('#stage .homegreeting'), f = R('.daily-question-fab'), t = R('.bottomtabs:not([hidden])');
  return { btnTop: Math.round(b.top), greet: g && Math.round(g.top), tagGap: tg ? Math.round(b.top - tg.bottom) : null,
           toTabs: t ? Math.round(t.top - b.bottom) : null, fabX: f ? Math.round(f.left - b.right) : null,
           fabY: f ? Math.round(f.top - b.bottom) : null, scroll: document.documentElement.scrollHeight - innerHeight };
}"""
# (device, w, h, insets, [toTabs lo, hi], tagline->button gap, build 325's button top)
HOME_DEV = [
    ("iPhone 17 Pro Max", 440, 956, (62, 34), (50, 58), 56, 730),
    ("iPhone 14 / 15 / 16", 393, 852, (59, 34), (38, 46), 32, 651),
    ("iPad Pro 11\"", 834, 1194, (24, 20), (59, 63), 83, 945),
]


def home_section(br):
    print("\n3. Home on a phone: Start Studying and the greeting a little higher, the iPad untouched")
    body0 = io.open(cb.SRC, encoding="utf-8").read()
    for dev, w, h, (it, ib), (lo, hi), gap, top325 in HOME_DEV:
        body = cb.INSET_RE.sub(lambda m: {"top": "%dpx" % it, "bottom": "%dpx" % ib}.get(m.group(1), "0px"), body0) \
            .replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
        ctx = br.new_context(viewport={"width": w, "height": h})
        ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
                            "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
                            "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % USED_ACCOUNT)
        ctx.add_init_script(STANDALONE)
        pg = ctx.new_page()
        pg.route("**/index.html", lambda r, req=None, b=body: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"},
                                                          body='{"build":"%s","frameId":"","note":""}' % cb.SERVED_BUILD))
        pg.goto(cb.URL)
        pg.wait_for_timeout(2600)
        pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
        m = pg.evaluate(HOME_JS)
        ctx.close()
        tablet = w >= 640
        moved = top325 - m["btnTop"]
        ok = lo <= (m["toTabs"] or -99) <= hi and abs((m["tagGap"] or -99) - gap) <= 1 and m["scroll"] <= 0
        if tablet:
            ok = ok and abs(moved) <= 1
        else:
            ok = ok and 9 <= moved <= 16 and ((m["fabX"] or 0) >= 12 or (m["fabY"] or 0) >= 8)
        check("%s: button %d px above the tab bar (%d-%d), tagline->button still %dpx, %s" %
              (dev, m["toTabs"] or -1, lo, hi, gap, "unmoved" if tablet else "raised 9-16px, clear of the daily circle"),
              ok, m)


# ---------------------------------------------------------------------------
# 4. THE CALENDAR, on Jan 12 2027 (a PT finals day) and Oct 18 2026.
CAL_JS = r"""async (iso) => {
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
      return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width >= 3 && r.height >= 3; };
    const look = el => { const cs = getComputedStyle(el); return { bg: cs.backgroundColor, tf: cs.transform, rad: parseFloat(cs.borderRadius) || 0, w: +el.getBoundingClientRect().width.toFixed(1) }; };
    /* every mark on the screen: grid, week strip, key, chips, the card */
    const marks = [...tab.querySelectorAll('.cal-cell-dot, .cal-week-dot, .cal-legend-dot')].filter(vis).map(d => Object.assign({ c: d.className }, look(d)));
    out.rotated = marks.filter(m => m.tf !== 'none').map(m => m.c);
    out.square = marks.filter(m => m.rad < m.w / 2 - .5).map(m => m.c);
    out.gridSizes = [...new Set([...tab.querySelectorAll('.cal-grid .cal-cell-dot')].filter(vis).map(d => look(d).w))];
    out.keySizes = [...new Set([...tab.querySelectorAll('.cal-grid-legend .cal-legend-dot')].filter(vis).map(d => look(d).w))];
    const cellMark = ds => { const c = tab.querySelector('.cal-grid .cal-cell[data-date="' + ds + '"]'); if(!c) return null;
      const d = [...c.querySelectorAll('.cal-cell-dots > i')].filter(vis); return d.length ? d.map(x => look(x).bg) : []; };
    out.pt = ['2027-01-11', '2027-01-12', '2027-01-13'].map(cellMark);
    out.big = cellMark('2027-01-19');
    out.test = cellMark('2027-01-04');
    const items = [...tab.querySelectorAll('.cal-grid-legend > *')];
    out.key = items.map(it => ({ t: it.textContent.trim(), bg: (it.querySelector('i') && look(it.querySelector('i')).bg) || null }));
    out.bigRows = [...tab.querySelectorAll('.cal-big-row')].map(r => ({ n: (r.querySelector('.cal-big-name') || {}).textContent,
      w: (r.querySelector('.cal-big-when') || {}).textContent,
      /* MOVED IN 327z15: a page of the Countdowns card - its count box */
      c: (r.querySelector('.cal-big-count') || r.querySelector('.cal-count-num b') || {}).textContent }));
    out.today = (tab.querySelector('.cal-today-status') || {}).textContent || '';
    out.ptIsExam = typeof isPtFinalDay === 'function' ? CALENDAR_DATA.filter(isPtFinalDay).map(e => isExamDay(e)) : null;
    /* calm cells: an ordinary class day has no outline */
    const plain = [...tab.querySelectorAll('.cal-grid .cal-cell-class:not(.cal-cell-today):not(.cal-cell-sel):not(.cal-cell-last):not(.cal-cell-holiday)')];
    out.outlined = plain.filter(c => { const cs = getComputedStyle(c); const a = (cs.borderTopColor.match(/[\d.]+/g) || []);
      return parseFloat(cs.borderTopWidth) > 0 && !(a.length === 4 && +a[3] === 0) && cs.borderTopColor !== 'transparent'; }).length;
    out.plain = plain.length;
    out.scrollX = document.documentElement.scrollWidth - innerWidth;
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""


def cal_section(br):
    print("\n4. the Calendar: plain orange dots for the big exams and the PT finals, a calmer grid")
    for dev, w, h in [("iPhone SE (1st gen)", 320, 568), ("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11\"", 834, 1194)]:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        a = pg.evaluate(CAL_JS, "2027-01-12")
        ctx.close()
        if a.get("err"):
            check("%s: the Calendar could be read" % dev, False, a["err"])
            continue
        check("%s: no diamond anywhere - every mark is a round dot, none rotated" % dev,
              not a.get("rotated") and not a.get("square"), [a.get("rotated"), a.get("square")])
        check("%s: one dot size across the whole grid, and the key's dots the same" % dev,
              len(a.get("gridSizes") or []) == 1 and a.get("keySizes") == a.get("gridSizes"), [a.get("gridSizes"), a.get("keySizes")])
        big = a.get("big") or []
        orange = big[-1] if big else None
        pt = a.get("pt") or []
        check("%s: Jan 11-13 (PT finals) carry the big exam's orange dot beside the class dot; a test's amber is different" % dev,
              orange and all(p and len(p) == 2 and p[-1] == orange for p in pt) and (a.get("test") or [None])[-1] != orange,
              [pt, big, a.get("test")])
        key = a.get("key") or []
        # MOVED IN 327 (b327c): "Final Exams is probably what the name should be for it"
        ok_key = any(k["t"] == "Final Exams" and k["bg"] == orange for k in key) and len(key) == 4
        check("%s: the key has one orange entry for big exams and PT finals" % dev, ok_key, key)
        rows = a.get("bigRows") or []
        check("%s: the big exams card lists the PT finals as one row, in date order, and says Today on Jan 12" % dev,
              rows and rows[0]["n"] == "PT finals" and "11" in rows[0]["w"] and "13" in rows[0]["w"] and rows[0]["c"] == "Today"
              and [r["n"] for r in rows[1:]] == ["Level One Final", "Level Two Final", "Level Three Final Exam", "State test"], rows)
        check("%s: Today says PT finals; a PT final is never counted as a test" % dev,
              a.get("today") == "PT finals" and a.get("ptIsExam") == [False, False, False], [a.get("today"), a.get("ptIsExam")])
        check("%s: an ordinary class day has no outline, and nothing scrolls sideways" % dev,
              a.get("plain", 0) > 10 and a.get("outlined") == 0 and (a.get("scrollX") or 0) <= 0,
              [a.get("plain"), a.get("outlined"), a.get("scrollX")])


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME, args=["--no-sandbox"])
        only = os.environ.get("ONLY", "")
        if not only or "recap" in only:
            recap_section(br)
        if not only or "sky" in only:
            sky_section(br)
        if not only or "home" in only:
            home_section(br)
        if not only or "cal" in only:
            cal_section(br)
        br.close()
    print("\n%d failure(s)" % len(FAILURES))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
