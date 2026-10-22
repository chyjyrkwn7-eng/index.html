#!/usr/bin/env python3
"""Build 327, package c: Nova's story, the weekly recap's words and ending,
the podium's repeat finishers, the calendar's words and colours, and two
known issues from HANDOFF-326.

Madison (Oct 20):
  "In the weekly recap, why are we are calling it to the this week board?
   Fix that. ... it needs to end with the class time and hundos and tests
   completed and then that's it. If someone manages to get top 3 more than
   once or back to back mention that during the podium presentation part
   too."
  "Calendar ... where it says the date of when the test got posted, don't
   include that? The orange dot, it says big exam, and pt final ... Final
   Exams is probably what the name should be for it ... 'on the test',
   ensure that part is only there if we have the information ... some of
   the colors in 'the course' box look confusing because it's so many."
  "Meeting nova, he starts to explain the cracking, 'every flare you light
   pours its light into your planet, it can't hold it all..' ... I don't
   like this one at all."
  "The badge explanation is bad at the end, it says something about
   finding them so I can teach you that unit? That's terrible"
  "we need to understand why your planet blew up, what the badges and stuff
   are, and why we should avoid cracking ours kinda thing"

Every section fails on build 326 (5ce026a):
  python3 tools/check-b327-c.py
  python3 tools/check-b327-c.py --against /path/to/326/index.html
  ONLY=recap,cal,story,issues python3 tools/check-b327-c.py
"""
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
from playwright.sync_api import sync_playwright

check, booted, USED_ACCOUNT, FAILURES = cb.check, cb.booted, cb.USED_ACCOUNT, cb.FAILURES
DEVS = ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11"))

# ---------------------------------------------------------------------------
# 1. THE RECAP. check-behaviour's fixture (Ada, Bo, Cy on the podium), plus
# this device's own record of the two weeks before: Bo was on the podium the
# week before last week (back to back), Cy the week before that (once
# before), Ada never. The live top-three cache names Ada for the week before
# as well - it must NOT count (it is the board mid-week, not where it ended).
RECAP_JS = r"""async (mode) => {
  const out = { err: null };
  try{
    document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
    """ + cb.RECAP_FIXTURE_JS + r"""
    __recapMine(3000);
    const wb = weekKeyBefore(lw), wbb = weekKeyBefore(wb);
    const hist = {};
    if(mode === 'full'){
      hist[wb] = { win: 'd4', top: ['d4', 'b2', 'e5'], cats: [] };
      hist[wbb] = { win: 'c3', top: ['c3', 'x9', 'y8'], cats: [] };
    } else if(mode === 'winonly'){
      hist[wb] = { win: 'c3', cats: [] };
    }
    localStorage.setItem('class26e.weekrecap.v1', JSON.stringify({ wk: wbb, hist }));
    try{ const c = JSON.parse(localStorage.getItem('class26e.weektop.v1') || '{}');
         c[wb] = [{ pub: 'a1', name: 'Ada', avatar: 'ghost', pts: 4000 }]; localStorage.setItem('class26e.weektop.v1', JSON.stringify(c)); }catch(e){}
    const rows = __recapRows();
    const r = buildWeekRecap(rows);
    out.top = r.top.map(t => t.name);
    out.story = r.story.kind;
    const L = weekRecapLines(r);
    out.lines = L.map(l => l.text);
    out.finals = L.map(l => !!l.final);
    out.wantH = rows.reduce((a, e) => a + ((e.pwk && e.pwk.h) || 0), 0);
    out.wantT = rows.reduce((a, e) => a + ((e.pwk && e.pwk.t) || 0), 0);
    out.awards = r.classWeek ? r.classWeek.awards.map(a => ({ cat: a.cat, name: a.name })) : [];
    const ui = buildWeekRecapStage(r);
    out.pages = ui.pages.map(p => p.dataset.page);
    out.chips = [...ui.root.querySelectorAll('.wr-col')].map(c => ({ n: (c.querySelector('.wr-name') || {}).textContent || '', a: (c.querySelector('.wr-again') || {}).textContent || '' }));
    out.tiles = [...ui.root.querySelectorAll('.wr-page-class .wr-tile')].map(t => t.dataset.cat);
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""

PLAY_JS = r"""async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const out = { err: null, pages: {} };
  try{
    document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
    """ + cb.RECAP_FIXTURE_JS + r"""
    __recapMine(3000);
    try{ localStorage.removeItem('class26e.weekrecap.v1'); }catch(e){}
    const el = playWeekRecap(buildWeekRecap(__recapRows()));
    for(let k = 0; k < 40 && el && el.__nova; k++){
      const n = el.__nova;
      if(n.typing){ n.advance(); await wait(60); }
      await wait(700);
      const on = el.querySelector('.wr-page.is-on');
      if(on){
        const box = el.querySelector('.wr-pages').getBoundingClientRect();
        const bad = [];
        on.querySelectorAll('.wr-tile, .wr-award, .wr-mention, .wr-subwrap').forEach(c => {
          const r = c.getBoundingClientRect(), cs = getComputedStyle(c);
          if(cs.display === 'none' || !r.width) return;
          if(r.left < -.5 || r.right > innerWidth + .5) bad.push('x ' + c.className);
          if(r.top < box.top - 1 || r.bottom > box.bottom + 1) bad.push('y ' + c.className);
        });
        out.pages[on.dataset.page] = { bad, tiles: on.querySelectorAll('.wr-tile').length };
      }
      out.last = on ? on.dataset.page : null;
      if(n.index >= n.count - 1) break;
      n.advance(); await wait(250);
    }
    out.scrollX = document.documentElement.scrollWidth - innerWidth;
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""


def recap_section(br):
    print("\nc1. the weekly recap: last week's board, repeat finishers named, and it ends on the class")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    a = pg.evaluate(RECAP_JS, "full")
    b = pg.evaluate(RECAP_JS, "winonly")
    n = pg.evaluate(RECAP_JS, "none")
    ctx.close()
    if a.get("err"):
        check("the recap could be built", False, a["err"])
        return
    lines = a.get("lines") or []
    joined = " | ".join(lines)
    check("never 'the This Week board' - he calls it last week's board",
          "This Week board" not in joined and lines and re.search(r"last week.s board", lines[0]), lines[:1])
    last = lines[-1] if lines else ""
    check("the last line is the class's week - hundos, tests finished and study time - and the goodbye, and nothing after it",
          ("%d hundos" % a["wantH"]) in last and ("%d tests finished" % a["wantT"]) in last and "study clock" in last
          and "next Tuesday" in last and (a.get("finals") or [])[-1:] == [True] and sum(a.get("finals") or []) == 1, last)
    i_aw = [i for i, t in enumerate(lines) if "Flawless" in t or "Long Shift" in t]
    check("the two awards (Flawless, Long Shift) are said with the honorable mentions, before the class's totals",
          len(i_aw) == 2 and all(i < len(lines) - 1 for i in i_aw) and len(a.get("awards") or []) == 2,
          [lines[i][:50] for i in i_aw])
    check("no closing 'this week so far' board and no closing page; the class's page is last and has three tiles",
          "so far" not in joined and "board reset" not in joined.lower() and (a.get("pages") or [])[-1:] == ["class"]
          and "close" not in (a.get("pages") or []) and a.get("tiles") == ["hundos", "tests", "study"],
          [a.get("pages"), a.get("tiles")])
    pod = {t: next((x for x in lines[1:4] if t in x), "") for t in ("Ada", "Bo", "Cy")}
    check("Bo (on the podium the week before, by this device's own recap) is named back to back on the podium",
          re.search(r"back to back", pod["Bo"]), pod["Bo"])
    check("Cy (on it two weeks before, every week known) is told it is his second time on the podium",
          re.search(r"second time on the podium", pod["Cy"]), pod["Cy"])
    check("Ada is in the live cache for the week before but not in a recap's record: nothing is claimed for her",
          not re.search(r"podium (the week before|before)|back to back|time on the podium", pod["Ada"]), pod["Ada"])
    chips = {c["n"]: c["a"] for c in a.get("chips") or []}
    check("the podium tags them too: 'Back to back' on Bo, 'Again' on Cy, none on Ada",
          chips.get("Bo") == "Back to back" and chips.get("Cy") == "Again" and chips.get("Ada") == "", chips)
    bl = " | ".join(b.get("lines") or [])
    bpod = {t: next((x for x in (b.get("lines") or [])[1:4] if t in x), "") for t in ("Bo", "Cy")}
    check("an old record with only a winner: Cy (that winner) is back to back; nobody else gets a claim",
          re.search(r"back to back", bpod["Cy"]) and not re.search(r"podium (the week before|before)|back to back|time on the podium", bpod["Bo"]),
          bpod)
    npod = " | ".join((n.get("lines") or [])[1:4])
    check("with no record at all, no repeat is claimed for anybody",
          not re.search(r"back to back|time on the podium|on the podium before", npod), npod[:200])
    for (w, h, dev) in ((320, 568, "iPhone SE (1st gen)"),) + DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        p = pg.evaluate(PLAY_JS)
        ctx.close()
        pages = p.get("pages") or {}
        bad = {k: v["bad"] for k, v in pages.items() if v.get("bad")}
        check("%s: played for real it ends on the class's page, three tiles, every page inside the stage and the screen" % dev,
              not p.get("err") and p.get("last") == "class" and (pages.get("class") or {}).get("tiles") == 3
              and "awards" in pages and not bad and (p.get("scrollX") or 0) <= 0, [p.get("err"), p.get("last"), bad, list(pages)])


# ---------------------------------------------------------------------------
# 2. THE CALENDAR, on Tue Oct 20 2026: Test #6 (Oct 26) has its topics; then
# the same with the topics taken away.
CAL_JS = r"""async (o) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const RealDate = window.__RealDate || Date; window.__RealDate = RealDate;
  const off = new RealDate(o.iso + 'T10:00:00').getTime() - RealDate.now();
  window.Date = class extends RealDate { constructor(...a){ if(a.length) super(...a); else super(RealDate.now() + off); }
                                         static now(){ return RealDate.now() + off; } };
  const out = { err: null };
  try{
    if(o.noTopics) Object.keys(TEST_TOPICS).forEach(k => delete TEST_TOPICS[k]);
    document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
    showHome(); await wait(250);
    (typeof showCalendarTab === 'function' ? showCalendarTab : showCalendar)(); await wait(700);
    const tab = document.querySelector('#stage > .screen-calendar');
    out.text = tab.innerText.replace(/\s+/g, ' ');
    out.key = [...tab.querySelectorAll('.cal-grid-legend > *')].map(it => it.textContent.trim());
    out.bigHead = ((tab.querySelector('.cal-big-card .cal-card-head, .cal-big-card h3, .cal-big-card [class*="head"]') || {}).textContent || '').trim();
    const nt = tab.querySelector('.cal-nexttest-card');
    out.topics = nt ? [...nt.querySelectorAll('.cal-topics')].map(x => x.innerText.replace(/\s+/g, ' ')) : null;
    const rgb = s => (String(s).match(/\d+/g) || []).slice(0, 3).join(',');
    const ring = tab.querySelector('.cal-course-ring');
    out.ring = ring ? rgb((() => { const d = document.createElement('i'); d.style.color = getComputedStyle(ring).getPropertyValue('--tone').trim(); document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })()) : null;
    const td = document.createElement('i'); td.className = 'cal-cell-dot cal-cell-dot-test'; tab.appendChild(td);
    out.testDot = rgb(getComputedStyle(td).backgroundColor); td.remove();
    out.nums = [...tab.querySelectorAll('.cal-course-grid .stat-num')].map(n => ({ c: n.parentNode.className, rgb: rgb(getComputedStyle(n).color) }));
  }catch(e){ out.err = String(e && e.stack || e); }
  return out;
}"""


def cal_section(br):
    print("\nc2. the Calendar: no posted date, Final Exams, 'On the test' only when known, a calmer course card")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        a = pg.evaluate(CAL_JS, {"iso": "2026-10-20"})
        ctx.close()
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        z = pg.evaluate(CAL_JS, {"iso": "2026-10-20", "noTopics": True})
        ctx.close()
        if a.get("err") or z.get("err"):
            check("%s: the Calendar could be read" % dev, False, [a.get("err"), z.get("err")])
            continue
        txt = a.get("text") or ""
        check("%s: no 'Posted <date>' anywhere on the tab" % dev, not re.search(r"\bPosted\b", txt), re.findall(r".{20}Posted.{20}", txt)[:2])
        key = a.get("key") or []
        check("%s: the orange key reads 'Final Exams', and 'Big exam' is nowhere on the tab" % dev,
              "Final Exams" in key and len(key) == 4 and "Big exam" not in txt and "big exam" not in txt.lower(), key)
        check("%s: the orange card is 'Final Exams'" % dev, "Final Exams" in txt and "Final Exams" in (a.get("bigHead") or txt), a.get("bigHead"))
        tp = a.get("topics") or []
        check("%s: a test whose topics are known says what is on it" % dev,
              len(tp) == 1 and "on the test" in tp[0].lower() and "Penal Code" in tp[0], tp)
        check("%s: a test whose topics are NOT known has no 'On the test' part and no 'Not posted' line" % dev,
              z.get("topics") == [] and "Not posted" not in (z.get("text") or "") and "on the test" not in (z.get("text") or "").lower(), z.get("topics"))
        nums = a.get("nums") or []
        allowed = {a.get("ring"), a.get("testDot"), "243,245,247"}
        # round 10: "Let's just have class days" - the three tiles went; the ring and one line say it
        check("%s: The course has no number tiles, only its ring and the class days" % dev,
              len(nums) == 0, [nums, a.get("ring"), a.get("testDot")])


# ---------------------------------------------------------------------------
# 3. THE STORY, in every place he tells it.
STORY_JS = r"""() => {
  const out = {};
  const txt = ls => ls.map(l => l.text);
  out.fresh = txt(novaIntroLines({}));
  try{ out.existing = txt(novaIntroLines({ existing: true })); }catch(e){ out.existing = []; out.err = String(e); }
  out.slides = novaIntroLines({}).map(l => !!(l.enter || l.prep));
  out.ranks = TIER_ORDER_FULL.map((k, i) => { try{ return novaRankLine(i); }catch(e){ return ''; } });
  out.chats = ['what are badges', 'why is my planet cracking', 'what do i get', 'flares'].map(q => novaReplyFor(q));
  out.progress = [novaProgressLine({ badges: ['Penal Code'] }), novaProgressLine({ badges: ['Penal Code', 'Identity Crimes'] })];
  out.note = ((RELEASE_NOTES[0].groups || []).flatMap(g => g.items || []).find(i => /Your Instructor/.test(i.title)) || {}).body || '';
  out.tips = NOVA_NEW_TIPS_321.map(t => t.text).join(' | ');
  out.lore = RANK_LORE.veteran;
  try{ const p = typeof novaStrainPlanet === 'function' ? novaStrainPlanet() : null;
       out.strain = !!(p && p.querySelector('.cosmic-hero-wrap') && p.querySelector('.cosmic-scar')); }catch(e){ out.strain = false; }
  return out;
}"""


def story_section(br):
    print("\nc3. Nova's story: why his planet went, what a badge is, why yours must not go the same way")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate(STORY_JS)
    fresh, existing = r.get("fresh") or [], r.get("existing") or []
    everything = " | ".join(fresh + existing + (r.get("ranks") or []) + (r.get("chats") or []) + (r.get("progress") or [])
                            + [r.get("note") or "", r.get("tips") or "", r.get("lore") or ""])
    check("the 'pours its light into your planet ... can't hold it all' line is gone, from everywhere he speaks",
          not re.search(r"pours (its|more of it|its light)|can.t hold it all|isn.t breaking|becoming a star", everything),
          re.findall(r".{30}(?:pours|can.t hold it all|isn.t breaking|becoming a star).{30}", everything)[:3])
    check("no badge 'so I can teach you that unit', and no instructor's log pages",
          not re.search(r"teach (you )?(that|this|\w+ properly)|instructor.s log|page of (my|his) log|pages of my log|from it\.", everything, re.I),
          re.findall(r".{30}(?:teach|log).{30}", everything)[:3])
    i_crack = next((i for i, t in enumerate(fresh) if re.search(r"more light than it could hold", t)), -1)
    i_boom = next((i for i, t in enumerate(fresh) if re.search(r"explod", t)), -1)
    i_badge = next((i for i, t in enumerate(fresh) if re.search(r"badge", t) and re.search(r"mastered", t) and re.search(r"hundo", t)), -1)
    i_wall = next((i for i, t in enumerate(fresh) if re.search(r"level waits", t) and re.search(r"badges", t)), -1)
    # build 327 round 9: the strain slide ("your planet is a lot like that one ... cracks") was removed on
    # request - the cracks story did not make sense beside "badges hold a planet together"
    check("in order: his planet took in more light than it could hold, it exploded; then a badge is a unit mastered (hundos)",
          0 <= i_crack < i_boom < i_badge, {"crack": i_crack, "boom": i_boom, "badge": i_badge})
    check("the strain slide is gone: no intro line says your planet cracks",
          not any(re.search(r"crack", t) and re.search(r"\byour planet\b|\byours\b", t) for t in fresh + existing),
          [t for t in fresh + existing if re.search(r"crack", t) and re.search(r"\byour planet\b|\byours\b", t)][:2])
    check("both flows say what a badge is (the existing account too)",
          any(re.search(r"mastered", t) for t in existing), existing[3:10])
    check("line counts stay sensible: a new account at most 16 lines, an existing one at most 21",
          0 < len(fresh) <= 16 and 0 < len(existing) <= 21, [len(fresh), len(existing)])
    ranks = r.get("ranks") or []
    check("Gold's rank-up says the crack is strain and the badges hold it; Supernova's: it held, a star",
          len(ranks) == 7 and re.search(r"crack", ranks[2]) and re.search(r"badges", ranks[2]) and re.search(r"held", ranks[6]) and re.search(r"star", ranks[6]),
          [ranks[2:3], ranks[6:7]])
    check("his badge messages say the unit is mastered", all(re.search(r"mastered", x) for x in r.get("progress") or []), r.get("progress"))
    ctx.close()


# ---------------------------------------------------------------------------
# 4. HANDOFF-326's known issues 1 and 2.
def issues_section(br):
    print("\nc4. HANDOFF-326: a badge found with a rank-up is named; the returning tip no longer leans on the badge case")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => {
      const who = AVATAR_DISPLAY_NAME.detective || 'detective';
      const p = { crew: ['detective'], badges: ['Penal Code'], sflares: [] };
      const rank = novaRankLine(2, p);
      const both = novaProgressLine({ crew: ['detective'], badges: ['Penal Code'], sflares: ['red'] });
      const two = novaRankLine(1, { crew: [], badges: ['Penal Code', 'Identity Crimes'], sflares: [] });
      return { who, rank, both, two, flare: (MYSTERY_NAME && MYSTERY_NAME.red) || '',
               tips: NOVA_NEW_TIPS_321.map(t => t.text) };
    }""")
    ctx.close()
    check("a rank-up with a crewman AND a badge waiting names both - the crewman and the badge's unit",
          r["who"] in r["rank"] and "Penal Code" in r["rank"], r["rank"])
    check("one of his crew, a badge and a secret flare on one day: all three named in the one message",
          r["who"] in r["both"] and "Penal Code" in r["both"] and (r["flare"] in r["both"]), r["both"])
    check("two badges with a rank-up: both units named", "Penal Code" in r["two"] and "Identity Crimes" in r["two"], r["two"])
    check("no returning tip says the badge case opens from Profile", not any("badge case" in t for t in r["tips"]), r["tips"])


def main():
    only = os.environ.get("ONLY")
    secs = [("recap", recap_section), ("cal", cal_section), ("story", story_section), ("issues", issues_section)]
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME)
        for name, fn in secs:
            if only and name not in only.split(","):
                continue
            try:
                fn(br)
            except Exception as ex:
                check("section %s ran" % name, False, str(ex)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not FAILURES else "%d FAILED" % len(FAILURES)))
    raise SystemExit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
